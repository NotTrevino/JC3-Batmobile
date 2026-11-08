"""review-G3-10i - independent check of CONSTRAINT_CODE2 (the cinfo loop's body guard).

The reviewed card claims that in `JustCause3.exe`:

  * the loop at 0x141569d00 walks the 24-byte `hknpConstraintCinfo` records at
    `[data+0x140]` (count `[data+0x148]`), stride 0x18, and calls 0x1414e7200 per record;
  * six invalid-body branches (sentinel, capacity, live-flag, twice) all land on the loop
    increment 0x141569fc1, i.e. the record is dropped;
  * nothing substitutes a fixed or root body;
  * only one function in the image tests *both* body offsets (+0x08 and +0x0c) against
    `0x7fffffff`;
  * the sentinel tested is the same value stored in 494/494 fleet records.

This tool re-derives each one from the bytes:

  1. linear disassembly of 0x141569d00..0x141569ff0 from raw section bytes, every
     conditional branch listed with its resolved target;
  2. loop structure: count/array slots, the back edge, every call, every memory write and
     every write to the cinfo register inside the loop body;
  3. a whole-`.text` scan for `cmp`/`test` against the sentinel whose compared value came
     from a +8 or +0xc load - following register copies, accepting indexed addressing and
     direct-memory compares, i.e. wider than the reviewed script's four-instruction,
     exact-text window;
  4. the class-registry member tables the card cites as complete;
  5. a citation audit: every cited address decoded from its own function start, and its
     operand checked for the claimed displacement (the G3-07a failure mode);
  6. a re-sweep of the fleet `.physicsc` records for the stored sentinel value.

Static only: read-only opens; nothing is run or attached.

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_constraint_code2_review.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_constraint_code2_review.py --check
"""

from __future__ import annotations

import glob
import json
import os
import re
import struct
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402  (only the .physicsc packfile reader; none of the claims)

EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "CONSTRAINT_CODE2_REVIEW.md")
JS = os.path.join(OUT, "CONSTRAINT_CODE2_REVIEW.json")
FLEET = r"E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc"

SENT = 0x7FFFFFFF
WALKER = 0x141569D00
WALKER_END = 0x141569FF0
LOOP_HEAD = 0x141569F60
LOOP_TAIL = 0x141569FC8
SKIP = 0x141569FC1
CALL = 0x141569FBC
ADD = 0x1414E7200
ADD_CLAIMED_END = 0x1414E735E
COPY = 0x141557A30
OTHER = 0x1415E6030                 # the second both-offset consumer found here
OTHER_YES = 0x1415E62FE             # bodyA == sentinel target
OTHER_NO = 0x1415E6352              # bodyB == sentinel target
CINFO_STRIDE = 0x18

DIS = Cs(CS_ARCH_X86, CS_MODE_64)
JCC = {"je", "jne", "jz", "jnz", "ja", "jae", "jb", "jbe", "jg", "jge", "jl", "jle",
       "js", "jns", "jo", "jno", "jp", "jnp", "jpe", "jpo", "jrcxz", "jecxz"}
WRITERS = {"mov", "movsxd", "movzx", "movsx", "lea", "add", "sub", "and", "or", "xor",
           "imul", "shl", "shr", "sar", "movss", "movaps", "movups", "movdqu", "pop",
           "inc", "dec"}


class Image:
    """Minimal read-only PE accessor (own copy: the review must not lean on the card)."""

    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(self.base + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData,
                      s.SizeOfRawData, s.Name.rstrip(b"\0").decode()) for s in self.pe.sections]
        pd = [s for s in self.pe.sections if s.Name.rstrip(b"\0") == b".pdata"][0]
        raw = self.data[pd.PointerToRawData:pd.PointerToRawData + pd.SizeOfRawData]
        fns = []
        for i in range(0, len(raw) - 11, 12):
            b, e = struct.unpack_from("<II", raw, i)
            if b:
                fns.append((self.base + b, self.base + e))
        fns.sort()
        self.funcs = fns
        self.fstarts = [f[0] for f in fns]
        self.text = [s for s in self.secs if s[4] == ".text"][0]

    def fo(self, va):
        for v, vs, po, rs, _ in self.secs:
            if v <= va < v + max(vs, rs):
                return (va - v) + po
        return None

    def va_of_fo(self, off):
        for v, _vs, po, rs, _ in self.secs:
            if po <= off < po + rs:
                return v + (off - po)
        return None

    def sec(self, va):
        for v, vs, po, rs, n in self.secs:
            if v <= va < v + max(vs, rs):
                return n
        return None

    def func_of(self, va):
        import bisect
        i = bisect.bisect_right(self.fstarts, va) - 1
        if i < 0:
            return None
        s, e = self.funcs[i]
        return (s, e) if s <= va < e else None

    def cstr(self, va, maxlen=400):
        fo = self.fo(va)
        if fo is None:
            return None
        end = self.data.find(b"\0", fo, fo + maxlen)
        if end < 0:
            return None
        s = self.data[fo:end]
        if not s or not all(32 <= c < 127 for c in s):
            return None
        return s.decode("latin1")

    def dis(self, lo, hi):
        fo = self.fo(lo)
        if fo is None:
            return []
        return list(DIS.disasm(self.data[fo:fo + (hi - lo)], lo))


# ---------------------------------------------------------------- helpers
def norm(r):
    r = r.strip().lower()
    if re.fullmatch(r"e[a-z]{2}", r):
        return "r" + r[1:]
    if re.fullmatch(r"r\d+d|r\d+w|r\d+b", r):
        return r[:-1]
    return r


def mem_disp(expr):
    """[base + index*scale ± disp] -> (first register, displacement), any spelling."""
    e = expr.strip()
    m = re.search(r"([+-])\s*(0x[0-9a-f]+|\d+)\s*$", e)
    disp = 0
    if m:
        disp = int(m.group(2), 16) if m.group(2).startswith("0x") else int(m.group(2))
        if m.group(1) == "-":
            disp = -disp
    regs = re.findall(r"\b(r[a-z0-9]{1,3}|e[a-z]{2})\b", e)
    return (regs[0] if regs else None), disp


RE_MEM = re.compile(r"^(\w+), (?:[a-z]+ ptr )?\[([^\]]+)\]$")
RE_REG = re.compile(r"^(\w+), (\w+)$")


def value_source(seq, k, reg, window=16):
    """Walk back from seq[k] for what produced `reg`: a load, an immediate, or nothing."""
    reg = norm(reg)
    for j in range(k - 1, max(-1, k - 1 - window), -1):
        s = seq[j]
        if s["mn"] in ("call", "jmp", "ret"):
            return None
        m = RE_MEM.match(s["op"].strip())
        if m and norm(m.group(1)) == reg:
            _base, disp = mem_disp(m.group(2))
            return ("load", disp, "%s %s" % (s["mn"], s["op"]))
        m = RE_REG.match(s["op"].strip())
        if m and norm(m.group(1)) == reg:
            src = m.group(2)
            if re.fullmatch(r"(r[a-z0-9]{1,3}|e[a-z]{2})", src.lower()):
                if s["mn"] in ("mov", "movsxd", "movzx", "movsx"):
                    reg = norm(src)
                    continue
            if re.fullmatch(r"0x[0-9a-f]+|\d+", src):
                return ("imm", None, "%s %s" % (s["mn"], s["op"]))
            return None
        if s["mn"] in WRITERS:
            if norm(s["op"].split(",")[0].strip()) == reg:
                return None
    return None


def cmp_sites(seq):
    out = []
    for k, s in enumerate(seq):
        if s["mn"] not in ("cmp", "test") or "0x7fffffff" not in s["op"]:
            continue
        ops = s["op"].split(", ")
        direct = None
        if "[" in ops[0]:
            _b, disp = mem_disp(ops[0][ops[0].index("[") + 1:ops[0].rindex("]")])
            direct = ("load", disp, "%s %s" % (s["mn"], s["op"]))
        src = direct or value_source(seq, k, ops[0].strip())
        out.append({"at": s["at"], "text": "%s %s" % (s["mn"], s["op"]),
                    "direct_mem": bool(direct),
                    "field": src[1] if src and src[0] == "load" else None,
                    "source": src[2] if src else None})
    return out


def call_sites(img, target):
    tv, _vs, po, rs, _n = img.text
    blob = img.data[po:po + rs]
    hits = []
    for op in (b"\xe8", b"\xe9"):
        i = blob.find(op)
        while i >= 0:
            if i + 5 <= len(blob):
                if tv + i + 5 + struct.unpack_from("<i", blob, i + 1)[0] == target:
                    hits.append(tv + i)
            i = blob.find(op, i + 1)
    return sorted(hits)


def rows_of(img, lo, hi):
    return [{"at": x.address, "text": ("%s %s" % (x.mnemonic, x.op_str)).strip(),
             "mn": x.mnemonic, "op": x.op_str, "size": x.size,
             "bytes": x.bytes.hex()} for x in img.dis(lo, hi)]


# ---------------------------------------------------------------- 1. the loop
def disasm_range(img):
    rows = rows_of(img, WALKER, WALKER_END)
    contig = bool(rows) and rows[0]["at"] == WALKER and \
        rows[-1]["at"] + rows[-1]["size"] == WALKER_END
    for a, b in zip(rows, rows[1:]):
        if a["at"] + a["size"] != b["at"]:
            contig = False
    return rows, contig


def loop_structure(rows):
    brs = [{"at": r["at"], "text": r["text"], "target": int(r["op"], 16)}
           for r in rows if r["mn"] in JCC and r["op"].startswith("0x")]
    body = [r for r in rows if LOOP_HEAD <= r["at"] <= LOOP_TAIL]
    setup = [r for r in rows if 0x141569F34 <= r["at"] < LOOP_HEAD]
    return {
        "all_branches": brs,
        "branches_to_skip": [b for b in brs if b["target"] == SKIP],
        "skip_target": next((r["at"] for r in rows if r["text"] == "add rbx, 0x18"), None),
        "back_edge": [b for b in brs if b["at"] == LOOP_TAIL],
        "loop_body_instructions": len(body),
        "calls_in_loop": [{"at": r["at"], "text": r["text"]}
                          for r in body if r["mn"] in ("call", "jmp")],
        "writes_in_loop": [{"at": r["at"], "text": r["text"]} for r in body
                           if r["mn"] in WRITERS and r["mn"] != "lea"
                           and "ptr [" in r["op"].split(", ")[0]],
        "reg_writes_in_loop": [{"at": r["at"], "text": r["text"]} for r in body
                               if norm(r["op"].split(",")[0].strip()) == "r8"
                               and r["mn"] in WRITERS and r["mn"] != "cmp"],
        "sentinel_imms": [{"at": r["at"], "text": r["text"]} for r in rows
                          if "0x7fffffff" in r["op"]],
        "count_slot": [r["text"] for r in rows if "[r15 + 0x148]" in r["op"]],
        "array_slot": [r["text"] for r in rows if "[r15 + 0x140]" in r["op"]],
        "setup": [{"at": r["at"], "text": r["text"]} for r in setup],
        "cinfo_pointer_set": [{"at": r["at"], "text": r["text"]} for r in body
                              if r["text"].startswith("lea r8")],
        "body_cinfo_slots": [r["text"] for r in rows
                             if "[r15 + 0x130]" in r["op"] or "[r15 + 0x138]" in r["op"]
                             or "add r13, 0x90" in r["text"]],
    }


# ---------------------------------------------------------------- 2. the .text scan
def sentinel_scan(img):
    tv, _vs, po, rs, _n = img.text
    blob = img.data[po:po + rs]
    fns, i = set(), blob.find(b"\xff\xff\xff\x7f")
    while i >= 0:
        f = img.func_of(tv + i)
        if f:
            fns.add(f)
        i = blob.find(b"\xff\xff\xff\x7f", i + 1)

    sites, per_fn, cmp_total = [], {}, 0
    for f in sorted(fns):
        seq = rows_of(img, *f)
        if not seq:
            continue
        for s in cmp_sites(seq):
            cmp_total += 1
            if s["field"] in (8, 0xC):
                per_fn.setdefault(f, set()).add(s["field"])
                sites.append(dict(s, function="%#x-%#x" % f))
    both = [f for f, v in per_fn.items() if v == {8, 0xC}]
    evidence = []
    for f in sorted(both):
        seq = rows_of(img, *f)
        evidence.append({
            "function": "%#x-%#x" % f,
            "stride_0x18": [{"at": r["at"], "text": r["text"]} for r in seq
                            if re.match(r"^(add|sub) r[a-z0-9]+, 0x18$", r["text"])
                            or re.match(r"^imul r[a-z0-9]+, r[a-z0-9]+, 0x18$", r["text"])],
            "sites": [s["at"] for s in sites if s["function"] == "%#x-%#x" % f],
        })
    return {"functions_with_constant": len(fns),
            "sentinel_cmp_sites": cmp_total,
            "sites_fed_from_body_fields": sites,
            "functions_testing_both": sorted("%#x-%#x" % f for f in both),
            "both_evidence": evidence}


# ---------------------------------------------------------------- 3. the second consumer
def other_consumer(img):
    f = img.func_of(OTHER)
    seq = rows_of(img, *f)
    d = {r["at"]: r for r in seq}
    keys = [0x1415E60F0, 0x1415E60F4, 0x1415E60F9, 0x1415E60FF,
            0x1415E61B7, 0x1415E61BC, 0x1415E61C2, 0x1415E62DD,
            OTHER_YES, OTHER_NO]
    for t in (OTHER_YES, OTHER_NO):
        keys += [t + 6, t + 0xB, t + 0x11, t + 0x16]
    seen, block = set(), []
    for a in sorted(keys):
        if a in d and a not in seen:
            seen.add(a)
            block.append({"at": a, "text": d[a]["text"]})
    return {"function": "%#x-%#x" % f, "block": block,
            "stride": [{"at": r["at"], "text": r["text"]} for r in seq
                       if r["text"] == "add r14, 0x18"],
            "branches_to": {hex(t): next((r["text"] for r in seq if r["at"] == t), None)
                            for t in (OTHER_YES, OTHER_NO)},
            "epilogue_jmp": [{"at": r["at"], "text": r["text"]} for r in seq
                             if OTHER_YES <= r["at"] <= OTHER_YES + 0x60
                             and r["text"].startswith("jmp")]}


# ---------------------------------------------------------------- 4. registry
def registry(img, name):
    nb = name.encode()
    offs = [m.start() for m in re.finditer(re.escape(nb), img.data)
            if m.start() + len(nb) < len(img.data) and img.data[m.start() + len(nb)] == 0]
    if not offs:
        return None
    sva = img.va_of_fo(offs[0])
    for _v, _vs, po, rs, _n in img.secs:
        for i in range(po, po + rs - 8, 8):
            if struct.unpack_from("<Q", img.data, i)[0] != sva:
                continue
            rec = img.va_of_fo(i)
            nxt = struct.unpack_from("<Q", img.data, img.fo(rec + 8))[0]
            s = img.cstr(nxt) if img.sec(nxt) else None
            if not (s and s.startswith("!")):
                continue
            size = struct.unpack_from("<Q", img.data, img.fo(rec + 0x28))[0]
            members, p = [], rec + 0x28
            while p < rec + 0x400:
                q = struct.unpack_from("<Q", img.data, img.fo(p))[0]
                s = img.cstr(q) if img.sec(q) else None
                if s and s.startswith("!"):
                    break
                if s and s[0].isalpha() and len(s) < 40:
                    members.append({"name": s, "offset":
                                    struct.unpack_from("<I", img.data, img.fo(p + 0x1c))[0] >> 16})
                p += 8
            return {"record": rec, "size": size, "members": members}
    return None


# ---------------------------------------------------------------- 5. citations
CITES = [
    (0x141569F34, "[r15 + 0x148]", "cinfo count"),
    (0x141569F60, "[r15 + 0x140]", "cinfo array"),
    (0x141569F67, "lea r8", "&cinfo[i]"),
    (0x141569F6B, "[r8 + 8]", "bodyA load"),
    (0x141569F6F, "0x7fffffff", "bodyA sentinel test"),
    (0x141569F74, "0x141569fc1", "bodyA sentinel branch"),
    (0x141569F76, "[rsi + 0x2c]", "capacity source"),
    (0x141569F79, "0x3fffffff", "capacity mask"),
    (0x141569F81, "0x141569fc1", "bodyA range branch"),
    (0x141569F83, "[rsi + 0x20]", "body array"),
    (0x141569F8E, "0x40", "live-byte test A"),
    (0x141569F94, "0x141569fc1", "bodyA live branch"),
    (0x141569F96, "[r8 + 0xc]", "bodyB load"),
    (0x141569F9A, "0x7fffffff", "bodyB sentinel test"),
    (0x141569F9F, "0x141569fc1", "bodyB sentinel branch"),
    (0x141569FA3, "0x141569fc1", "bodyB range branch"),
    (0x141569FB2, "0x141569fc1", "bodyB live branch"),
    (0x141569FB4, "lea rdx, [rsp + 0x38]", "slot out-param"),
    (0x141569FB9, "mov rcx, rsi", "arg 1 = system"),
    (0x141569FBC, "call 0x1414e7200", "the add"),
    (0x141569FC1, "add rbx, 0x18", "loop increment"),
    (0x141569FC5, "dec rdi", "records left"),
    (0x141569FC8, "jne 0x141569f60", "back edge"),
    (0x1414E7229, "[rcx + 0x13c]", "world free-list head"),
    (0x1414E7267, "[rbx + 0x120]", "allocator"),
    (0x1414E7278, "0x38", "constraint stride"),
    (0x1414E7314, "[rsi + 0x16]", "disable bit"),
    (0x1414E731A, "[rbp + 0xc]", "bodyB read in add"),
    (0x1414E731D, "[rbp + 8]", "bodyA read in add"),
    (0x141557A47, "[rdx]", "constraintData"),
    (0x141557A4A, "[rdx + 0x10]", "flags"),
    (0x141557A4E, "[rdx + 0xc]", "bodyB copy"),
    (0x141557A51, "[rdx + 8]", "bodyA copy"),
    (0x141557ACA, "[rbp]", "bodyIdA store"),
    (0x141557ACD, "[rbp + 4]", "bodyIdB store"),
    (0x140280991, "[rsp + 0x48]", "caller cinfo +8"),
    (0x140280995, "[rsp + 0x4c]", "caller cinfo +0xc"),
    (0x140280A15, "[rsi + 0x310]", "caller world"),
    (0x140280A1C, "call 0x1414e7200", "caller add"),
]


def audit_cites(img):
    rows = []
    for va, want, what in CITES:
        f = img.func_of(va)
        boundary, text = False, None
        if f:
            for x in img.dis(*f):
                if x.address == va:
                    boundary = True
                    text = ("%s %s" % (x.mnemonic, x.op_str)).strip()
                    break
        rows.append({"at": va, "want": want, "what": what,
                     "function": "%#x-%#x" % f if f else None,
                     "boundary": boundary, "text": text,
                     "ok": bool(boundary and text and want in text)})
    return rows


def string_at_ins(img, va):
    it = next(iter(img.dis(va, va + 15)), None)
    if it is None:
        return None
    m = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", it.op_str)
    if not m:
        return None
    tgt = va + it.size + int(m.group(1), 16)
    return {"at": va, "text": "%s %s" % (it.mnemonic, it.op_str),
            "target": tgt, "string": img.cstr(tgt, 400)}


# ---------------------------------------------------------------- 6. the fleet
def sweep_fleet():
    files, recs = 0, []
    for p in sorted(glob.glob(FLEET, recursive=True)):
        try:
            blob = open(p, "rb").read()
            pf = jc3hkx.Packfile(blob)
            psd = next((o for o in pf.objects if o.cls == "hknpPhysicsSystemData"), None)
            if psd is None:
                continue
            bodies = pf.array(psd.offset + 0x40)
            cinfos = pf.array(psd.offset + 0x50)
            if not cinfos["size"]:
                continue
            files += 1
            for k in range(cinfos["size"]):
                at = pf.base + cinfos["ptr"] + CINFO_STRIDE * k
                a, b, fl = struct.unpack_from("<3I", blob, at + 8)
                recs.append({"file": os.path.basename(p), "k": k, "bodyA": a,
                             "bodyB": b, "flags": fl, "n_bodies": bodies["size"]})
        except Exception as e:                                    # noqa: BLE001
            recs.append({"file": os.path.basename(p), "error": str(e)})
    good = [r for r in recs if "error" not in r]
    return {"files": files, "records": len(good),
            "bodyB_sentinel": sum(1 for r in good if r["bodyB"] == SENT),
            "bodyA_sentinel": sum(1 for r in good if r["bodyA"] == SENT),
            "bodyA_out_of_range": sum(1 for r in good if r["bodyA"] != SENT
                                      and r["bodyA"] >= r["n_bodies"]),
            "bodyB_other_values": sorted({r["bodyB"] for r in good if r["bodyB"] != SENT}),
            "stored_dword_hex": sorted({struct.pack("<I", r["bodyB"]).hex() for r in good}),
            "tested_imm_hex": struct.pack("<I", SENT).hex(),
            "rejected": sum(1 for r in good if r["bodyB"] == SENT or r["bodyA"] == SENT
                            or r["bodyA"] >= r["n_bodies"] or r["bodyB"] >= r["n_bodies"]),
            "errors": [r for r in recs if "error" in r]}


# ---------------------------------------------------------------- 7. build
def build():
    img = Image(EXE)
    rows, contig = disasm_range(img)
    w = loop_structure(rows)
    w.update({"start": WALKER, "pdata": "%#x-%#x" % img.func_of(WALKER),
              "contiguous": contig, "n_instructions": len(rows)})
    scan = sentinel_scan(img)
    other = other_consumer(img)
    cites = audit_cites(img)
    cinfo = registry(img, "hknpConstraintCinfo")
    world = registry(img, "hknpWorldCinfo")
    fleet = sweep_fleet()
    add_fn = img.func_of(ADD)
    add_sent = [{"at": r["at"], "text": r["text"]} for r in rows_of(img, *add_fn)
                if "0x7fffffff" in r["op"]]
    copy_fn = img.func_of(COPY)
    copy_sent = [{"at": r["at"], "text": r["text"]} for r in rows_of(img, *copy_fn)
                 if "0x7fffffff" in r["op"]]
    return {
        "executable": {"path": EXE, "bytes": len(img.data), "base": img.base,
                       "pdata_functions": len(img.funcs)},
        "walker": w,
        "dump": rows,
        "scan": scan,
        "other": other,
        "cites": cites,
        "registry": {"cinfo": cinfo, "world": world},
        "fleet": fleet,
        "add": {"va": ADD, "pdata": "%#x-%#x" % add_fn,
                "sentinel_sites": add_sent,
                "sentinel_in_claimed_range": [x for x in add_sent
                                              if x["at"] < ADD_CLAIMED_END],
                "strings": [string_at_ins(img, 0x1414E72DC),
                            string_at_ins(img, 0x1414E72F3)]},
        "copy": {"va": COPY, "pdata": "%#x-%#x" % copy_fn, "sentinel_sites": copy_sent},
        "calls_to_add": call_sites(img, ADD),
    }


# ---------------------------------------------------------------- 8. render
def render(d):
    w, s, f, a, c, o = (d["walker"], d["scan"], d["fleet"], d["add"], d["copy"],
                        d["other"])
    cin, wr = d["registry"]["cinfo"], d["registry"]["world"]
    body_names = [m["name"] for m in (wr["members"] if wr else [])
                  if re.search(r"body|root|fixed|chassis", m["name"], re.I)]
    L = []
    A = L.append
    A("# review of G3-10i - what the runtime does with a constraint whose second body is absent")
    A("")
    A("Generated by `Tools/scripts/jc3_constraint_code2_review.py --write`; `--check`")
    A("re-decodes every instruction below from `JustCause3.exe` and re-sweeps the fleet.")
    A("Static only: the executable and the `.physicsc` files were opened read-only.")
    A("")
    A("- executable: `%s`, %d bytes, base %#x, %d `.pdata` functions"
      % (d["executable"]["path"], d["executable"]["bytes"], d["executable"]["base"],
         d["executable"]["pdata_functions"]))
    A("- loop: `%#x` (`.pdata` %s), %d instructions, contiguous: **%s**"
      % (w["start"], w["pdata"], w["n_instructions"], w["contiguous"]))
    A("- fleet: %d files, %d records" % (f["files"], f["records"]))
    A("")
    A("## VERDICT")
    A("")
    A("**The three load-bearing claims hold, one supporting claim does not, and two smaller")
    A("statements in the card are wrong.**  Every branch, target, stride and field the card")
    A("quotes in the cinfo loop is byte-exact, the six invalid-body branches do all land on")
    A("`%#x` (`add rbx, 0x18`), and nothing in the loop writes to the record or calls anything"
      % SKIP)
    A("but the add, so a sentinel record is dropped.  The sentinel the loop tests is byte-")
    A("identical to the value stored in %d/%d fleet records." % (f["bodyB_sentinel"], f["records"]))
    A("")
    A("But the card's completeness claim - \"only one function tests both body offsets\", used to")
    A("argue that no other consumer can repair an invalid body - is **false**: this review finds")
    A("**%d** such functions (%s)." % (len(s["functions_testing_both"]),
                                       ", ".join("`%s`" % x for x in s["functions_testing_both"])))
    A("The second one also walks 0x18-byte records and tests `+0xc` then `+8` against")
    A("`0x7fffffff`; its sentinel branches go to an error-report block, not to a body, so the")
    A("card's *conclusion* survives, but the evidence sentence and the \"exactly one place\"")
    A("paragraph must be corrected.  Two further inaccuracies: the `hknpWorldCinfo` member table")
    A("is presented as \"exactly these members\" while the registry record carries %d, and the two"
      % (len(wr["members"]) if wr else 0))
    A("name strings are listed against the wrong addresses.")
    A("")
    A("## 1. Independent branch decode (`0x141569d00-0x141569ff0`)")
    A("")
    A("| address | instruction | target | loop increment? |")
    A("|---|---|---|---|")
    for b in w["all_branches"]:
        A("| `%#x` | `%s` | `%#x` | %s |"
          % (b["at"], b["text"], b["target"], "**yes**" if b["target"] == SKIP else "no"))
    A("")
    A("**%d** conditional branches target `%#x`; the other %d target the body-prep loops or the"
      % (len(w["branches_to_skip"]), SKIP,
         len(w["all_branches"]) - len(w["branches_to_skip"])))
    A("loop entry/exit.  The six body branches, exactly as decoded:")
    A("")
    for b in w["branches_to_skip"]:
        A("- `%#x  %s` -> `%#x`" % (b["at"], b["text"], b["target"]))
    A("")
    A("These match the card's guard table address for address (sentinel/range/live for `+0x08`,")
    A("then the same three for `+0x0c`); the card's claim of \"6 branches\" is correct.")
    A("")
    A("## 2. Loop structure")
    A("")
    A("| property | value |")
    A("|---|---|")
    A("| skip target | `%#x`, instruction there: `%s` |"
      % (w["skip_target"], next((r["text"] for r in d["dump"]
                                 if r["at"] == w["skip_target"]), "?")))
    A("| back edge | %s |" % ", ".join("`%#x %s`" % (b["at"], b["text"]) for b in w["back_edge"]))
    A("| loop body | `%#x-%#x`, %d instructions |"
      % (LOOP_HEAD, LOOP_TAIL, w["loop_body_instructions"]))
    A("| calls in the loop body | %s |"
      % ", ".join("`%#x %s`" % (x["at"], x["text"]) for x in w["calls_in_loop"]))
    A("| memory writes in the loop body | %d |" % len(w["writes_in_loop"]))
    A("| writes to `r8` (the cinfo pointer) | %s |"
      % (", ".join("`%#x %s`" % (x["at"], x["text"]) for x in w["reg_writes_in_loop"])
         or "none"))
    A("| `0x7fffffff` immediates in the function | %s |"
      % ", ".join("`%#x %s`" % (x["at"], x["text"]) for x in w["sentinel_imms"]))
    A("| cinfo count slot | %s |" % ", ".join("`%s`" % t for t in w["count_slot"]))
    A("| cinfo array slot | %s |" % ", ".join("`%s`" % t for t in w["array_slot"]))
    A("| body-cinfo slots | %s |"
      % ", ".join("`%s`" % t for t in w["body_cinfo_slots"]))
    A("")
    A("Setup before the loop head (`0x141569f34-0x141569f60`), including the one call that is")
    A("*not* in the loop:")
    A("")
    for x in w["setup"]:
        A("- `%#x  %s`" % (x["at"], x["text"]))
    A("")
    A("So the loop body `%#x-%#x` contains exactly one call - `%#x` - and no store; the record"
      % (LOOP_HEAD, LOOP_TAIL, CALL))
    A("is never rewritten.  The only write to `r8` in the body is the per-iteration `lea r8,")
    A("[rbx + rax]` at `%#x`, i.e. `r8 = &cinfo[i]`, before any guard; `r8` is then the third"
      % 0x141569F67)
    A("argument of the add and is not reloaded.  The `call 0x141520f70` at `0x141569f57` is the")
    A("pre-loop capacity growth, outside the body.")
    A("")
    A("## 3. Whole-`.text` scan for both body offsets")
    A("")
    A("The reviewed script required the exact operand text `[reg + 8]`/`[reg + 0xc]` within four")
    A("instructions before the `cmp`.  This scan follows register copies, accepts indexed forms")
    A("(`[base + index + 0xc]`) and direct-memory compares:")
    A("")
    A("| measure | this scan | card |")
    A("|---|---:|---:|")
    A("| functions containing the 4-byte constant | %d | 1407 |" % s["functions_with_constant"])
    A("| `cmp`/`test` against the sentinel | %d | 843 |" % s["sentinel_cmp_sites"])
    A("| fed by a `+0x08`/`+0x0c` load (loose rule) | %d | 8 |"
      % len(s["sites_fed_from_body_fields"]))
    A("| functions testing **both** offsets | **%d** | 1 |" % len(s["functions_testing_both"]))
    A("")
    A("The card's counts are not comparable one-for-one (its rule is narrower, mine also catches")
    A("`cmp dword ptr [x + 8], 0x7fffffff` and index-scaled arrays), but the last row is a")
    A("difference in kind, not in counting style:")
    A("")
    for e in s["both_evidence"]:
        A("- `%s`: compares at %s; 0x18 stride: %s"
          % (e["function"], ", ".join("`%#x`" % x for x in e["sites"]),
             ", ".join("`%#x %s`" % (x["at"], x["text"]) for x in e["stride_0x18"]) or "none"))
    A("")
    A("### The function the card missed: `%s`" % o["function"])
    A("")
    A("Its record walk (the loop head reloads the array pointer each iteration):")
    A("")
    for x in o["block"]:
        A("- `%#x  %s`" % (x["at"], x["text"]))
    A("")
    A("| field | compare | sentinel target | instruction at the target |")
    A("|---|---|---|---|")
    A("| `+0xc` | `0x1415e60f9` | `%#x` | `%s` |"
      % (OTHER_NO, o["branches_to"][hex(OTHER_NO)]))
    A("| `+0x8` | `0x1415e61bc` | `%#x` | `%s` |"
      % (OTHER_YES, o["branches_to"][hex(OTHER_YES)]))
    A("")
    A("Both sentinel targets build an error string (`call 0x14119c010`, `call 0x1411b77f0`,")
    A("`mov r9d, <line>`, `call 0x14119bf50`) and then `jmp` to the function's exit; neither")
    A("substitutes a body.  This is a second 24-byte-record consumer, and the card's sentence")
    A("\"there is exactly one place in `JustCause3.exe` where a record's two body ids are both")
    A("read and checked against the invalid marker\" is therefore wrong.")
    A("")
    A("## 4. Citation audit")
    A("")
    A("| cited | claim | instruction actually there | boundary | operand |")
    A("|---|---|---|---|---|")
    for x in d["cites"]:
        A("| `%#x` | %s | `%s` | %s | %s |"
          % (x["at"], x["what"], x["text"], "yes" if x["boundary"] else "**NO**",
             "yes" if x["ok"] else "**NO**"))
    A("")
    A("%d of %d cited addresses are instruction boundaries whose operand carries the claimed"
      % (sum(1 for x in d["cites"] if x["ok"]), len(d["cites"])))
    A("displacement.  The card's additional pair of string citations is checked separately:")
    A("")
    A("| cited | instruction | resolves to |")
    A("|---|---|---|")
    for x in a["strings"]:
        if x:
            A("| `%#x` | `%s` | `%s` |" % (x["at"], x["text"], (x["string"] or "")[:120]))
    A("")
    A("The card's table lists these two addresses against the *opposite* strings (it puts")
    A("`hknpworld.cpp` first at `0x1414e72dc`); both addresses are real `lea`s to those strings,")
    A("so the pair is right and the order is reversed.")
    A("")
    A("## 5. The add function, the copy helper and the registry")
    A("")
    A("- function containing `%#x`: `.pdata` %s (the card's scan range ends at `%#x`, which is"
      % (ADD, a["pdata"], ADD_CLAIMED_END))
    A("  the real function end, so the range is not truncated)")
    A("- sentinel immediates in the whole function: %s"
      % ", ".join("`%#x %s`" % (x["at"], x["text"]) for x in a["sentinel_sites"]))
    A("- copy helper `%#x` (`.pdata` %s): %d sentinel constant(s)"
      % (COPY, c["pdata"], len(c["sentinel_sites"])))
    A("- `hknpConstraintCinfo`: record `%#x`, size `%#x`, members %s"
      % (cin["record"], cin["size"],
         ", ".join("%s +0x%x" % (m["name"], m["offset"]) for m in cin["members"][:4])))
    A("- `hknpWorldCinfo`: record `%#x`, size `%#x`, **%d** members"
      % (wr["record"], wr["size"], len(wr["members"])))
    A("- members whose name matches body/root/fixed/chassis: %s"
      % (", ".join(body_names) if body_names else "none that is a body id "
         "(only the body/motion *buffer* members: %s)"
         % ", ".join(m["name"] for m in wr["members"] if "body" in m["name"].lower())))
    A("")
    A("So the negative claim (\"no fixed or root body member\") holds against the full member")
    A("list, but the card's table shows %d members and calls them \"exactly these members\"."
      % 7)
    A("")
    A("## 6. Sentinel value: loop vs records")
    A("")
    A("| measure | value |")
    A("|---|---:|")
    A("| files with records | %d |" % f["files"])
    A("| records | %d |" % f["records"])
    A("| `bodyB == 0x7fffffff` | %d |" % f["bodyB_sentinel"])
    A("| `bodyA == 0x7fffffff` | %d |" % f["bodyA_sentinel"])
    A("| `bodyA` out of range | %d |" % f["bodyA_out_of_range"])
    A("| other `bodyB` values | %s |" % (f["bodyB_other_values"] or "none"))
    A("| stored `+0xc` dword (hex) | %s |" % ", ".join(f["stored_dword_hex"]))
    A("| immediate the loop tests (hex) | %s |" % f["tested_imm_hex"])
    A("| records the guard rejects (derived) | %d |" % f["rejected"])
    A("")
    A("Same 32-bit value, so the sentinel in G3-10h and the sentinel the loop tests are the")
    A("same constant; the derived 494/494 rejection stands.")
    A("")
    A("## 7. Card claims, one by one")
    A("")
    A("| claim | verdict here |")
    A("|---|---|")
    A("| 24-byte records at `[data+0x140]`, count `[data+0x148]`, stride `0x18` | **holds** |")
    A("| the six invalid-body/range/live branches land on `0x141569fc1` | **holds**, 6/6 |")
    A("| `0x141569fc1` is the loop increment `add rbx, 0x18` | **holds** |")
    A("| nothing substitutes a fixed/root/chassis body in the loop | **holds**: one call, no")
    A("  store, and the only `r8` write is the per-iteration `lea r8, [rbx+rax]` that forms the")
    A("  cinfo argument |")
    A("| only one function tests both body offsets | **refuted**: %d functions |"
      % len(s["functions_testing_both"]))
    A("| the sentinel is the value stored in 494/494 records | **holds** |")
    A("| `hknpWorldCinfo` has no fixed/root body member | **holds**; but the table is not the")
    A("  full member list |")
    A("| the 13 call sites of the add | **holds**, reproduced byte scan |")
    A("")
    A("## 8. What this review did not check")
    A("")
    A("- Whether the object the walker passes in `rcx` is a `hknpWorld` or a")
    A("  `hknpPhysicsSystem`: the card calls `rsi` the *system* in section 2 and the *world* in")
    A("  section 3, and names `%#x` `hknpWorld::addConstraint` from its source strings alone."
      % ADD)
    A("- Whether `[rsi+0x2c] & 0x3fffffff` is a capacity and bits 0..1 of the body's `+0x40`")
    A("  byte mean \"live\": both are readings of the guard, not decoded semantics. The branch")
    A("  *targets* do not depend on either reading.")
    A("- Whether a loader rewrites `+0xc` on its way into memory; if it did, the derived 494/494")
    A("  rejection count would change. No writer was searched here.")
    A("- Who dispatches the walker (the card's UNKNOWN 1) and what the second consumer's")
    A("  records are (its array is at `+0x50`, not `+0x140`); neither affects the guard.")
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------- 9. checks
def checks(d):
    w, s, f, o = d["walker"], d["scan"], d["fleet"], d["other"]
    assert w["contiguous"] and w["n_instructions"] > 60
    assert w["skip_target"] == SKIP
    hits = {b["at"] for b in w["branches_to_skip"]}
    assert hits == {0x141569F74, 0x141569F81, 0x141569F94,
                    0x141569F9F, 0x141569FA3, 0x141569FB2}, sorted(hits)
    assert [x["at"] for x in w["calls_in_loop"]] == [CALL]
    assert w["writes_in_loop"] == []
    assert [x["at"] for x in w["reg_writes_in_loop"]] == [0x141569F67], w["reg_writes_in_loop"]
    assert w["reg_writes_in_loop"][0]["text"] == "lea r8, [rbx + rax]"
    assert [x["at"] for x in w["sentinel_imms"]] == [0x141569F6F, 0x141569F9A]
    assert w["back_edge"] and w["back_edge"][0]["text"] == "jne 0x141569f60"
    assert s["functions_testing_both"] == ["0x141569d00-0x141569ff0",
                                           "0x1415e6030-0x1415e6651"], \
        s["functions_testing_both"]
    assert o["stride"] and len(d["other"]["branches_to"]) == 2
    assert [x["at"] for x in d["cites"] if not (x["boundary"] and x["ok"])] == []
    assert all(a["string"] for a in d["add"]["strings"])
    assert "Unsupported" in d["add"]["strings"][0]["string"]
    assert "hknpworld.cpp" in d["add"]["strings"][1]["string"]
    assert len(d["registry"]["world"]["members"]) == 25
    assert not [m for m in d["registry"]["world"]["members"]
                if re.search(r"^(fixed|root|chassis)body", m["name"], re.I)]
    assert f["records"] == 494 and f["bodyB_sentinel"] == 494 and f["rejected"] == 494
    assert f["stored_dword_hex"] == [f["tested_imm_hex"]]
    assert len(d["calls_to_add"]) == 13
    assert d["copy"]["sentinel_sites"] == []
    return True


def main(argv):
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: jc3_constraint_code2_review.py --write|--check")
    d = build()
    md = render(d)
    if argv[1] == "--write":
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        open(JS, "w", encoding="utf-8", newline="\n").write(
            json.dumps({k: v for k, v in d.items() if k != "dump"}, indent=1) + "\n")
        print("wrote %s (%d lines) and %s" % (MD, md.count("\n"), JS))
        print("branches to skip %d, calls in loop body %d, sentinel imms %s"
              % (len(d["walker"]["branches_to_skip"]),
                 len(d["walker"]["calls_in_loop"]),
                 [hex(x["at"]) for x in d["walker"]["sentinel_imms"]]))
        print("both-offset functions %s" % d["scan"]["functions_testing_both"])
        print("citations ok %d/%d" % (sum(1 for x in d["cites"] if x["ok"]), len(d["cites"])))
        print("fleet %d records, %d sentinel, stored=%s imm=%s"
              % (d["fleet"]["records"], d["fleet"]["bodyB_sentinel"],
                 d["fleet"]["stored_dword_hex"], d["fleet"]["tested_imm_hex"]))
        return 0
    checks(d)
    have = open(MD, encoding="utf-8").read()
    if have != md:
        raise SystemExit("CONSTRAINT_CODE2_REVIEW.md is stale; re-run --write")
    print("CHECK OK: %d branches to %#x, %d call in loop body, %d both-offset functions, "
          "citations %d/%d, %d records / %d sentinel"
          % (len(d["walker"]["branches_to_skip"]), SKIP,
             len(d["walker"]["calls_in_loop"]), len(d["scan"]["functions_testing_both"]),
             sum(1 for x in d["cites"] if x["ok"]), len(d["cites"]),
             d["fleet"]["records"], d["fleet"]["bodyB_sentinel"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
