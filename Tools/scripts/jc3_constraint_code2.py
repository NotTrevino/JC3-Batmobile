"""G3-10i - what the runtime does with a constraint whose second body is absent.

G3-10h decoded the shipped 24-byte `hknpConstraintCinfo` record: `bodyA` at +0x08 (always a
real body index) and `bodyB` at +0x0c, which is `0x7fffffff` in 494 of 494 fleet records.
This card follows the code: from the loop that walks the cinfo list to the world call that
adds a constraint, and asks what - if anything - the engine substitutes for an invalid body.

Decoded here (static only, read-only, nothing executed):

  * `hknpPhysicsSystemData` -> `hknpPhysicsSystem` construction loop `0x141569d00`, which
    walks the 24-byte cinfo array at `[data+0x140]` (`[data+0x148]` records) and calls the
    world's add at `0x1414e7200` - and its guard chain, whose invalid-body branches all jump
    to the loop increment, i.e. the record is *dropped*, not repaired;
  * `hknpWorld::addConstraint` `0x1414e7200` (identified by its own strings `hknpworld.cpp`
    and "Unsupported constraint type. Disabling the constraint.") and the copy helper
    `0x141557a30`, which moves the record's +0x08/+0x0c into the runtime constraint's
    `bodyIdA`/`bodyIdB` verbatim;
  * every call site of `0x1414e7200` in the image (9), so nothing else can feed a cinfo in;
  * a game-side caller `0x140280530` that assembles a cinfo from two *live* body ids - the
    only way a second body appears: supplied by the caller, never by the record;
  * the same field map applied to all 494 records to derive how many survive the guard (0).

Labels: decoded (file + offset / VA), derived (rule + inputs), UNKNOWN (what was tried).

Usage:
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_constraint_code2.py --write
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_constraint_code2.py --check
"""

from __future__ import annotations

import glob
import json
import os
import re
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3_colour_native2 as C          # noqa: E402  (Image: PE map, .pdata, capstone)
import jc3_constraint_code as K        # noqa: E402  (G3-10h: registry record parser)
import jc3_physics_roles6 as R6        # noqa: E402  (fleet .physicsc -> cinfo records)

OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "CONSTRAINT_CODE2.md")
JS = os.path.join(OUT, "CONSTRAINT_CODE2.json")

SENTINEL = 0x7FFFFFFF
WALKER = 0x141569D00                   # hknpPhysicsSystem(data): bodies, then cinfos
WALKER_END = 0x141569FF0
ADD = 0x1414E7200                      # hknpWorld::addConstraint
ADD_END = 0x1414E735E
COPY = 0x141557A30                     # cinfo -> hknpConstraint::bodyIdA/bodyIdB
COPY_END = 0x141557B40
GAME_SITE = 0x140280530                # a caller that builds a two-body cinfo itself
GAME_CALL = 0x140280A1C
DATA_REF = 0x142C16158                 # the one non-.pdata slot holding WALKER

# The guard chain of the cinfo loop, instruction by instruction.  Each entry is asserted
# against the bytes; a change in any line fails --check.
GUARD = [
    (0x141569F34, "mov edi, dword ptr [r15 + 0x148]"),      # cinfo count
    (0x141569F60, "mov rax, qword ptr [r15 + 0x140]"),      # cinfo array
    (0x141569F67, "lea r8, [rbx + rax]"),                   # &cinfo[i]
    (0x141569F6B, "movsxd rax, dword ptr [r8 + 8]"),        # bodyA
    (0x141569F6F, "cmp eax, 0x7fffffff"),                   # bodyA invalid?
    (0x141569F74, "je 0x141569fc1"),                        # -> loop increment
    (0x141569F76, "mov edx, dword ptr [rsi + 0x2c]"),       # body capacity
    (0x141569F79, "and edx, 0x3fffffff"),
    (0x141569F7F, "cmp eax, edx"),                          # bodyA out of range?
    (0x141569F81, "jae 0x141569fc1"),                       # -> loop increment
    (0x141569F83, "mov r9, qword ptr [rsi + 0x20]"),        # hknpBody array
    (0x141569F87, "lea rax, [rax + rax*8]"),                # bodyA * 9
    (0x141569F8B, "add rax, rax"),                          # ... * 0x12
    (0x141569F8E, "test byte ptr [r9 + rax*8 + 0x40], 3"),  # ... * 8 = 0x90 stride
    (0x141569F94, "je 0x141569fc1"),                        # body not live -> skip
    (0x141569F96, "movsxd rax, dword ptr [r8 + 0xc]"),      # bodyB
    (0x141569F9A, "cmp eax, 0x7fffffff"),                   # bodyB invalid?
    (0x141569F9F, "je 0x141569fc1"),                        # -> loop increment
    (0x141569FA1, "cmp eax, edx"),
    (0x141569FA3, "jae 0x141569fc1"),
    (0x141569FA5, "lea rax, [rax + rax*8]"),                # bodyB * 0x90
    (0x141569FA9, "add rax, rax"),
    (0x141569FAC, "test byte ptr [r9 + rax*8 + 0x40], 3"),
    (0x141569FB2, "je 0x141569fc1"),
    (0x141569FB4, "lea rdx, [rsp + 0x38]"),
    (0x141569FB9, "mov rcx, rsi"),                          # rcx = system
    (0x141569FBC, "call 0x1414e7200"),                      # only with both bodies valid
    (0x141569FC1, "add rbx, 0x18"),                         # loop increment (skip target)
    (0x141569FC5, "dec rdi"),
    (0x141569FC8, "jne 0x141569f60"),
]

ADD_BLOCK = [
    (0x1414E7220, "mov rbp, r8"),                           # rbp = cinfo record
    (0x1414E7223, "mov rdi, rdx"),                          # rdi = slot out-param
    (0x1414E7226, "mov rbx, rcx"),                          # rbx = world
    (0x1414E7229, "cmp dword ptr [rcx + 0x13c], 0x7fffffff"),  # free-list head (lazy init)
    (0x1414E7267, "lea rcx, [rbx + 0x120]"),
    (0x1414E7271, "call 0x141520e80"),                      # allocate a constraint slot
    (0x1414E7276, "mov esi, dword ptr [rdi]"),
    (0x1414E7278, "imul rsi, rsi, 0x38"),                   # hknpConstraint stride 0x38
    (0x1414E728C, "call 0x141557a30"),                      # copy ids into the constraint
    (0x1414E72DC, "lea rdx, [rip + 0x107c8d5]"),            # 'Unsupported constraint type...'
    (0x1414E7314, "or byte ptr [rsi + 0x16], 4"),           # disable flag
    (0x1414E731A, "mov eax, dword ptr [rbp + 0xc]"),        # bodyB
    (0x1414E731D, "cmp dword ptr [rbp + 8], eax"),          # bodyA == bodyB?
    (0x1414E7320, "je 0x1414e7314"),                        # then just disable
]

# The slot-release loop that follows addConstraint; its 0x7fffffff is the free-list marker.
RELEASE = 0x1414E7370
RELEASE_BLOCK = [
    (0x1414E73F7, "mov dword ptr [rdi], 0x7fffffff"),       # free-list push marker
]

COPY_BLOCK = [
    (0x141557A47, "mov r12, qword ptr [rdx]"),              # constraintData
    (0x141557A4A, "movzx esi, byte ptr [rdx + 0x10]"),      # flags
    (0x141557A4E, "mov ebx, dword ptr [rdx + 0xc]"),        # bodyB
    (0x141557A51, "mov edi, dword ptr [rdx + 8]"),          # bodyA
    (0x141557ACA, "mov dword ptr [rbp], edi"),              # hknpConstraint::bodyIdA (+0)
    (0x141557ACD, "mov dword ptr [rbp + 4], ebx"),          # hknpConstraint::bodyIdB (+4)
]

GAME_BLOCK = [
    (0x140280983, "mov rax, qword ptr [rsi]"),
    (0x140280989, "call qword ptr [rax + 0x120]"),          # body id 1: own vtable slot
    (0x14028098F, "mov ecx, dword ptr [rax]"),
    (0x140280991, "mov dword ptr [rsp + 0x48], ecx"),       # cinfo + 0x08 = bodyA
    (0x140280595, "mov r12, qword ptr [rsp + 0x58]"),
    (0x14028059A, "mov rax, qword ptr [r12]"),
    (0x1402805A1, "call qword ptr [rax + 0x120]"),          # body id 2: other object
    (0x1402805A7, "mov ebx, dword ptr [rax]"),
    (0x140280995, "mov dword ptr [rsp + 0x4c], ebx"),       # cinfo + 0x0c = bodyB
    (0x140280A15, "mov rcx, qword ptr [rsi + 0x310]"),      # world
    (0x140280A1C, "call 0x1414e7200"),
]


# ---------------------------------------------------------------- helpers
def text_at(img, va):
    """The single instruction at `va` as 'mnemonic op_str', or None."""
    fo = img.fo(va)
    if fo is None:
        return None
    it = next(iter(C.DISASM.disasm(img.data[fo:fo + 16], va)), None)
    return None if it is None else "%s %s" % (it.mnemonic, it.op_str)


def block(img, spec, label):
    """Assert an instruction table against the bytes and return it rendered."""
    rows = []
    for va, want in spec:
        got = text_at(img, va)
        if got != want:
            raise SystemExit("%s: %#x is %r, expected %r" % (label, va, got, want))
        rows.append({"at": va, "text": got})
    return rows


def sentinel_sites(img, lo, hi):
    """Every instruction in [lo,hi) whose text contains 0x7fffffff."""
    out = []
    for ins in C.DISASM.disasm(img.data[img.fo(lo):img.fo(hi)], lo):
        if "0x7fffffff" in ins.op_str:
            out.append({"at": ins.address, "text": "%s %s" % (ins.mnemonic, ins.op_str)})
    return out


def call_sites(img, target):
    """Every E8/E9 rel32 in .text that resolves to `target` (vectorised, exact)."""
    tv, vs, po, rs, _n = img.text
    n = min(vs, rs)
    arr = np.frombuffer(img.data, dtype=np.uint8, count=n, offset=po)
    hits = []
    for op in (0xE8, 0xE9):
        idx = np.nonzero(arr == op)[0]
        idx = idx[idx + 5 < n]
        disp = (arr[idx + 1].astype(np.int64)
                | (arr[idx + 2].astype(np.int64) << 8)
                | (arr[idx + 3].astype(np.int64) << 16)
                | (arr[idx + 4].astype(np.int64) << 24))
        disp = np.where(disp >= 2 ** 31, disp - 2 ** 32, disp)
        tgt = tv + idx + 5 + disp
        for i in np.nonzero(tgt == target)[0]:
            hits.append(tv + int(idx[i]))
    return sorted(hits)


def data_slots(img, target):
    """8-byte slots and 4-byte image-base-relative slots that hold `target`."""
    q, r = [], []
    rva = struct.pack("<I", target - img.base)
    qb = struct.pack("<Q", target)
    for _v, _vs, po, rs, _n in img.secs:
        blob = img.data[po:po + rs]
        i = blob.find(qb)
        while i >= 0:
            if i % 8 == 0 or True:
                va = img.va_of_fo(po + i)
                if va is not None:
                    q.append(va)
            i = blob.find(qb, i + 1)
        i = blob.find(rva)
        while i >= 0:
            va = img.va_of_fo(po + i)
            if va is not None:
                r.append(va)
            i = blob.find(rva, i + 1)
    return sorted(q), sorted(r)


def _reg(r):
    """Normalise capstone's 32/64-bit spellings so `eax` and `rax` compare equal."""
    if re.fullmatch(r"e[a-z]{2}", r):
        return "r" + r[1:]
    if re.fullmatch(r"r\d+d", r):
        return r[:-1]
    return r


def sentinel_inventory(img):
    """Whole-image: which functions compare a value loaded from +8 or +0xc to the sentinel.

    Candidate functions are found by byte search for the constant (1407 in this image),
    then each is decoded from its `.pdata` start, so no instruction is missed by a linear
    sweep's data islands.  The point of the scan is completeness: is any *other* function
    reading a record's two body fields?
    """
    tv, _vs, po, rs, _n = img.text
    pat = b"\xff\xff\xff\x7f"
    i = img.data.find(pat, po, po + rs)
    fns = set()
    while i >= 0:
        va = img.va_of_fo(i)
        f = img.func_of(va) if va is not None else None
        if f:
            fns.add(f)
        i = img.data.find(pat, i + 1)
    load = re.compile(r"^([re][a-z0-9]+), (?:dword ptr )?\[([a-z0-9]+) \+ (0x8|0xc|8|c)\]$")
    sites, total = [], 0
    for f in sorted(fns):
        seq = list(C.DISASM.disasm(img.data[img.fo(f[0]):img.fo(f[1])], f[0]))
        for k, s in enumerate(seq):
            if s.mnemonic != "cmp" or "0x7fffffff" not in s.op_str:
                continue
            total += 1
            reg = _reg(s.op_str.split(",")[0].strip())
            for j in range(max(0, k - 4), k):
                m = load.match(seq[j].op_str)
                if m and _reg(m.group(1)) == reg:
                    off = 8 if m.group(3) in ("8", "0x8") else 12
                    sites.append({"at": s.address, "offset": off,
                                  "load": "%s %s" % (seq[j].mnemonic, seq[j].op_str),
                                  "function": "%#x-%#x" % f})
                    break
    per = {}
    for s in sites:
        per.setdefault(s["function"], set()).add(s["offset"])
    both = sorted(k for k, v in per.items() if v == {8, 12})
    return {"functions_with_constant": len(fns), "sentinel_cmp_sites": total,
            "sites_fed_from_body_fields": sites, "functions_testing_both": both}


def fleet_rows():
    rows = []
    for p in sorted(glob.glob(R6.FLEET, recursive=True)):
        rec = R6.scan(p)
        if not rec or "error" in rec or not rec.get("n_cinfos"):
            continue
        for c in rec["cinfos"]:
            w = c["words"]
            rows.append({"file": p, "k": c["k"],
                         "bodyA": w[2], "bodyB": w[3], "n_bodies": rec["n_bodies"]})
    return rows


# ---------------------------------------------------------------- build
def build():
    img = C.Image(C.EXE)
    schema = K.class_record(img, "hknpConstraintCinfo")
    cons = K.class_record(img, "hknpConstraint")
    world = K.class_record(img, "hknpWorldCinfo")
    if not (schema and schema.get("record") and cons and cons.get("record")):
        raise SystemExit("registry records missing")

    off = {m["name"]: m["offset"] for m in schema["members"]}
    if off.get("bodyA") != 8 or off.get("bodyB") != 0x0C or schema["object_size"] != 0x18:
        raise SystemExit("cinfo schema drifted: %r" % off)
    if {m["name"] for m in cons["members"]} & {"bodyIdA", "bodyIdB"} != {"bodyIdA", "bodyIdB"}:
        raise SystemExit("hknpConstraint schema drifted")

    guard = block(img, GUARD, "walker guard")
    add = block(img, ADD_BLOCK, "addConstraint")
    rel = block(img, RELEASE_BLOCK, "release")
    copy = block(img, COPY_BLOCK, "cinfo copy")
    game = block(img, GAME_BLOCK, "game caller")

    # (1) every invalid-body branch of the guard lands on the loop increment, i.e. the
    #     record is skipped.  The skip target is the `add rbx, 0x18` instruction itself.
    loop_tail = next(r["at"] for r in guard if r["text"] == "add rbx, 0x18")
    skips = [r for r in guard if r["text"].split()[-1] == hex(loop_tail)
             and r["text"].split()[0] in ("je", "jae", "jb")]
    for r in skips:
        if r["text"].split()[-1] != hex(loop_tail):
            raise SystemExit("guard branch %#x does not skip to the loop tail" % r["at"])
    if len(skips) != 6:
        raise SystemExit("expected 6 guard branches to the loop tail, got %d" % len(skips))
    if not any(r["text"] == "call 0x1414e7200" for r in guard):
        raise SystemExit("walker does not call addConstraint")

    # (2) addConstraint never tests the record's two body fields against the sentinel.
    wsites = sentinel_sites(img, ADD, ADD_END)
    if [s["at"] for s in wsites] != [0x1414E7229]:
        raise SystemExit("addConstraint sentinel constants moved: %r" % wsites)
    if any(0x1414E7267 <= s["at"] <= 0x1414E72A6 for s in wsites):
        raise SystemExit("addConstraint tests a sentinel in the copy path")

    # (3) the copy helper moves both ids verbatim, with no sentinel constant at all.
    csites = sentinel_sites(img, COPY, COPY_END)
    if csites:
        raise SystemExit("copy helper contains a sentinel: %r" % csites)

    # (4) constraints can only enter a world through ADD; enumerate its callers.
    callers = []
    for a in call_sites(img, ADD):
        if text_at(img, a) != "call 0x1414e7200":
            raise SystemExit("bad call decode at %#x" % a)
        f = img.func_of(a)
        callers.append({"at": a, "function": "%#x-%#x" % f if f else None,
                        "is_walker": bool(f and f[0] == WALKER)})
    walker_callers = call_sites(img, WALKER)

    # (4b) whole-image completeness: no other function tests both body fields.
    inv = sentinel_inventory(img)
    if inv["functions_testing_both"] != ["0x141569d00-0x141569ff0"]:
        raise SystemExit("another function tests both body fields: %r"
                         % inv["functions_testing_both"])

    # (5) how the walker is reached: no direct call; one data slot.
    q, r = data_slots(img, WALKER)
    qadd, radd = data_slots(img, ADD)
    refs = {"walker": {"direct_calls": len(walker_callers), "qword_slots": q,
                       "rva_slots": r,
                       "sections": sorted({img.sec(v) for v in q + r if img.sec(v)}),
                       "rdata_rva_slots": [v for v in r if img.sec(v) == ".rdata"]},
            "add": {"direct_calls": len(callers), "qword_slots": qadd,
                    "rva_slots": radd,
                    "sections": sorted({img.sec(v) for v in qadd + radd if img.sec(v)}),
                    "rdata_rva_slots": [v for v in radd if img.sec(v) == ".rdata"]}}

    # (6) the fleet: how many records survive the guard at all.
    rows = fleet_rows()
    n = len(rows)
    b_sent = sum(1 for x in rows if x["bodyB"] == SENTINEL)
    a_sent = sum(1 for x in rows if x["bodyA"] == SENTINEL)
    a_oob = sum(1 for x in rows if x["bodyA"] != SENTINEL and x["bodyA"] >= x["n_bodies"])
    b_oob = sum(1 for x in rows if x["bodyB"] != SENTINEL and x["bodyB"] >= x["n_bodies"])
    rejected = sum(1 for x in rows if x["bodyB"] == SENTINEL or x["bodyA"] == SENTINEL
                   or x["bodyA"] >= x["n_bodies"] or x["bodyB"] >= x["n_bodies"])
    files = len({x["file"] for x in rows})
    if n != 494 or b_sent != 494 or files != 50:
        raise SystemExit("fleet drifted: %d records over %d files, %d sentinel"
                         % (n, files, b_sent))

    d = {
        "executable": {"path": C.EXE, "bytes": len(img.data), "base": img.base,
                       "pdata_functions": len(img.funcs)},
        "schema": {"cinfo_record": schema["record"], "cinfo_size": schema["object_size"],
                   "members": {k: v for k, v in off.items()},
                   "constraint_size": cons["object_size"],
                   "constraint_members": {m["name"]: m["offset"] for m in cons["members"]},
                   "worldcinfo_size": world["object_size"] if world and world.get("record") else None,
                   "worldcinfo_members": {m["name"]: m["offset"]
                                          for m in (world["members"] if world else [])}},
        "walker": {"va": WALKER, "end": WALKER_END, "guard": guard,
                   "sentinel_sites": sentinel_sites(img, WALKER, WALKER_END),
                   "skip_target": loop_tail,
                   "body_stride": 0x90, "cinfo_stride": 0x18,
                   "data_constraint_array": 0x140, "data_constraint_count": 0x148,
                   "data_body_array": 0x130, "data_body_count": 0x138,
                   "system_body_array": 0x20, "system_body_capacity": 0x2C},
        "add": {"va": ADD, "end": ADD_END, "block": add,
                "sentinel_sites": wsites,
                "strings": _add_strings(img)},
        "release": {"va": RELEASE, "block": rel, "sentinel_sites":
                    sentinel_sites(img, RELEASE, 0x1414E743D)},
        "copy": {"va": COPY, "end": COPY_END, "block": copy,
                 "sentinel_sites": csites},
        "callers": callers,
        "inventory": inv,
        "refs": refs,
        "game_site": {"function": GAME_SITE, "call": GAME_CALL, "block": game},
        "fleet": {"files": files, "records": n, "bodyB_sentinel": b_sent,
                  "bodyA_sentinel": a_sent, "bodyA_out_of_range": a_oob,
                  "bodyB_out_of_range": b_oob, "rejected_by_guard": rejected,
                  "surviving": n - rejected,
                  "distinct_bodyA": len({x["bodyA"] for x in rows})},
    }
    # the two strings that name the add function
    if not d["add"]["strings"]:
        raise SystemExit("addConstraint identity strings not found")
    return d


def _add_strings(img):
    """The hknpworld.cpp path and the unsupported-type message, by VA of the lea targets."""
    out = []
    for ins_va in (0x1414E72DC, 0x1414E72F3):
        fo = img.fo(ins_va)
        it = next(iter(C.DISASM.disasm(img.data[fo:fo + 15], ins_va)), None)
        if it is None:
            continue
        m = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", it.op_str)
        if not m:
            continue
        s = img.cstr(ins_va + it.size + int(m.group(1), 16), 200)
        if s:
            out.append(s)
    return out


# ---------------------------------------------------------------- render
def H(va):
    return "`%#x`" % va


def render(d):
    s = d["schema"]
    w = d["walker"]
    a = d["add"]
    c = d["copy"]
    g = d["game_site"]
    f = d["fleet"]
    L = []
    L.append("# What the runtime does with a constraint whose second body is absent (G3-10i)")
    L.append("")
    L.append("Generated by `Tools/scripts/jc3_constraint_code2.py --write`; `--check` re-decodes")
    L.append("every instruction quoted below from `JustCause3.exe` and re-sweeps the 494 records,")
    L.append("failing on any drift.  Static only: the executable was opened read-only and nothing")
    L.append("was run or attached.")
    L.append("")
    L.append("- executable: `JustCause3.exe` (%d bytes, base %#x, %d `.pdata` functions)"
             % (d["executable"]["bytes"], d["executable"]["base"],
                d["executable"]["pdata_functions"]))
    L.append("- fleet: %d `.physicsc` files, %d cinfo records" % (f["files"], f["records"]))
    L.append("")
    L.append("## VERDICT")
    L.append("")
    L.append("**None of the three.  The engine substitutes nothing: a constraint record whose")
    L.append("second body is `0x7fffffff` is validated and *dropped before the add call*.**")
    L.append("")
    L.append("The choice is made at %s, in the loop that builds an `hknpPhysicsSystem` from an"
             % H(w["va"]))
    L.append("`hknpPhysicsSystemData`.  Both body ids are checked - sentinel, then range, then")
    L.append("the body's own live-flag - and every failing branch jumps to the loop increment at")
    L.append("%s, which is the *next record*, not the call." % H(w["skip_target"]))
    L.append("")
    L.append("So the three candidates in the brief are all refuted as *substitutions*:")
    L.append("")
    L.append("| candidate | verdict | why |")
    L.append("|---|---|---|")
    L.append("| the world's fixed body | **not substituted** | the guard branches away before the "
             "call; and `hknpWorldCinfo` has no body field at all (below) |")
    L.append("| the system's root body | **not substituted** | same branch; there is no "
             "`rootBody` member in either class schema |")
    L.append("| a body supplied by the vehicle at spawn | **not substituted for an invalid id** - "
             "but this is the only way a second body does appear | game code assembles a cinfo "
             "from two live ids and adds *that*, e.g. %s (below) |" % H(g["call"]))
    L.append("")
    L.append("Decoded consequence for the modding question: the 494 shipped records with")
    L.append("`bodyB = 0x7fffffff` do not become world constraints through this path.  A vehicle")
    L.append("joint that must exist at runtime is created by game code calling the same add with a")
    L.append("cinfo it filled with two live body ids - the second body is supplied by the caller,")
    L.append("never read out of the record.")
    L.append("")
    L.append("## 1. The record, as this code reads it")
    L.append("")
    L.append("Field map from G3-10h's registry decode, re-checked here:")
    L.append("`hknpConstraintCinfo` objectSize `%#x`, `constraintData` `+0x%x`, `bodyA` `+0x%x`,"
             % (s["cinfo_size"], s["members"]["constraintData"], s["members"]["bodyA"]))
    L.append("`bodyB` `+0x%x`, `flags` `+0x%x`; the runtime `hknpConstraint` is `%#x` bytes with"
             % (s["members"]["bodyB"], s["members"]["flags"], s["constraint_size"]))
    L.append("`bodyIdA` `+0x%x` and `bodyIdB` `+0x%x` at the same offsets."
             % (s["constraint_members"]["bodyIdA"], s["constraint_members"]["bodyIdB"]))
    L.append("")
    L.append("`hknpWorldCinfo` (%s, `%#x` bytes) has exactly these members:"
             % (H(0x142DBB758), s["worldcinfo_size"] or 0))
    L.append("")
    L.append("| member | offset |")
    L.append("|---|---:|")
    for k, v in s["worldcinfo_members"].items():
        L.append("| `%s` | `%#x` |" % (k, v))
    L.append("")
    L.append("There is no fixed-body, static-body or root-body member, so \"the world's fixed")
    L.append("body\" is not a value the world data even holds; any such substitution would have")
    L.append("to invent an id, and the code below does not.")
    L.append("")
    L.append("## 2. The cinfo loop and its guard chain")
    L.append("")
    L.append("%s is the `hknpPhysicsSystemData` -> `hknpPhysicsSystem` builder: it allocates the"
             % H(w["va"]))
    L.append("system (`0x690` bytes) and first copies the `0x80`-byte body cinfos at")
    L.append("`[data+0x%x]` (count `[data+0x%x]`) into `0x90`-byte runtime bodies, then walks the"
             % (w["data_body_array"], w["data_body_count"]))
    L.append("`0x18`-byte constraint cinfos at `[data+0x%x]` (count `[data+0x%x]`)."
             % (w["data_constraint_array"], w["data_constraint_count"]))
    L.append("")
    L.append("The constraint part of the loop, verbatim (one line per instruction, all decoded")
    L.append("from the bytes; the comment column is the reading, not the disassembly).  The class")
    L.append("name is the string the fleet files carry for this object (`hknpPhysicsSystemData`,")
    L.append("decoded by `jc3_physics_roles6.scan`), and the strides agree with the file writer:")
    L.append("`0x80` body cinfos, `0x18` constraint cinfos.")
    L.append("")
    L.append("```")
    notes = {
        0x141569F34: "cinfo count",
        0x141569F60: "cinfo array",
        0x141569F67: "&cinfo[i]",
        0x141569F6B: "bodyA",
        0x141569F6F: "bodyA == invalid?",
        0x141569F74: "yes -> next record",
        0x141569F76: "body capacity from the system",
        0x141569F79: "mask low 30 bits",
        0x141569F7F: "bodyA >= capacity?",
        0x141569F81: "yes -> next record",
        0x141569F83: "hknpBody array",
        0x141569F87: "index * 9",
        0x141569F8B: "* 2",
        0x141569F8E: "[9*2*8] = 0x90 stride, live bits 0..1",
        0x141569F94: "not live -> next record",
        0x141569F96: "bodyB",
        0x141569F9A: "bodyB == invalid?",
        0x141569F9F: "yes -> next record",
        0x141569FA1: "bodyB >= capacity?",
        0x141569FA3: "yes -> next record",
        0x141569FA5: "bodyB * 9",
        0x141569FA9: "* 2",
        0x141569FAC: "live bits",
        0x141569FB2: "not live -> next record",
        0x141569FB4: "slot out-param",
        0x141569FB9: "system",
        0x141569FBC: "add - reached only if both bodies are valid",
        0x141569FC1: "loop increment: the skip target",
        0x141569FC5: "records left",
        0x141569FC8: "loop",
    }
    for r in w["guard"]:
        L.append("%#x  %-40s ; %s" % (r["at"], r["text"], notes.get(r["at"], "")))
    L.append("```")
    L.append("")
    L.append("Both invalid-body tests (`+0x08` and `+0x0c`) and both range tests jump to")
    L.append("%s, which is the instruction that advances `rbx` by `0x18`.  No path from an"
             % H(w["skip_target"]))
    L.append("invalid id reaches the `call`: there is no write-back to the record, no copy from a")
    L.append("world/root body, and the record is simply not turned into a constraint.")
    L.append("")
    L.append("## 3. The add call itself")
    L.append("")
    L.append("%s is `hknpWorld`'s add: its own strings name it - `%s` and"
             % (H(a["va"]), a["strings"][-1] if a["strings"] else "?"))
    L.append("`%s`." % (a["strings"][0] if a["strings"] else "?"))
    L.append("")
    L.append("```")
    for r in a["block"]:
        L.append("%#x  %s" % (r["at"], r["text"]))
    L.append("```")
    L.append("")
    L.append("Its only `0x7fffffff` constant is the world's constraint free-list head at")
    L.append("`[world+0x13c]` (%s); the matching push marker is in the separate slot-release"
             % H(0x1414E7229))
    L.append("loop %s (%s) - the same \"invalid index\" meaning G3-10h decoded, here applied"
             % (H(d["release"]["va"]), H(0x1414E73F7)))
    L.append("to a *slot* list, not to a body.  The two body")
    L.append("fields are never compared to it: the function reads `[record+0xc]` and `[record+8]`")
    L.append("only to test them *against each other* (%s), and when they are equal it merely sets"
             % H(0x1414E731A))
    L.append("the constraint's disable bit (`or byte ptr [rsi+0x16], 4`), it does not pick a")
    L.append("replacement body.")
    L.append("")
    L.append("The copy helper %s is where the ids land in the runtime object:" % H(c["va"]))
    L.append("")
    L.append("```")
    for r in c["block"]:
        L.append("%#x  %s" % (r["at"], r["text"]))
    L.append("```")
    L.append("")
    L.append("`bodyA` -> `hknpConstraint::bodyIdA` (+0) and `bodyB` -> `bodyIdB` (+4), verbatim,")
    L.append("including `0x7fffffff` if that is what the caller passed, and the helper contains no")
    L.append("`0x7fffffff` constant at all.  Nothing between the record and the constraint")
    L.append("rewrites a body id.")
    L.append("")
    L.append("## 4. There is no other way in")
    L.append("")
    L.append("Every `E8`/`E9` in `.text` was decoded and resolved: %s has exactly **%d** call"
             % (H(a["va"]), len(d["callers"])))
    L.append("sites in the image, so a cinfo can reach a world only through them.")
    L.append("")
    L.append("| call site | containing function | reads the file layout? |")
    L.append("|---|---|---|")
    for x in d["callers"]:
        L.append("| %s | `%s` | %s |" % (H(x["at"]), x["function"],
                                         "**yes** - the cinfo loop" if x["is_walker"] else "no"))
    L.append("")
    L.append("Only %s feeds a 24-byte record straight out of the data object; the other %d"
             % (H(0x141569FBC), len(d["callers"]) - 1))
    L.append("assemble a cinfo themselves.  %s shows how a second body is really supplied -"
             % H(g["function"]))
    L.append("two live body ids fetched from two different objects, stored into the stack cinfo at")
    L.append("`+0x08` and `+0x0c`, then added:")
    L.append("")
    L.append("```")
    for r in sorted(g["block"], key=lambda x: x["at"]):
        L.append("%#x  %s" % (r["at"], r["text"]))
    L.append("```")
    L.append("")
    L.append("That is the answer to the third candidate: a second body (the chassis, if that is")
    L.append("what the caller passes) reaches a constraint because the *caller* supplies it, not")
    L.append("because a loader fills in a sentinel.")
    L.append("")
    L.append("### No other function reads both body fields")
    L.append("")
    L.append("A whole-image scan answers the completeness question directly: of the %d functions"
             % d["inventory"]["functions_with_constant"])
    L.append("that contain the constant `0x7fffffff` (%d comparisons against it in total), only %d"
             % (d["inventory"]["sentinel_cmp_sites"],
                len(d["inventory"]["sites_fed_from_body_fields"])))
    L.append("comparisons are fed by a load from `+0x08` or `+0x0c`, and only **one function tests")
    L.append("both offsets** - the loop above.")
    L.append("")
    L.append("| comparison site | field | load | function |")
    L.append("|---|---|---|---|")
    for s in d["inventory"]["sites_fed_from_body_fields"]:
        L.append("| %s | `+0x%x` | `%s` | %s |"
                 % (H(s["at"]), s["offset"], s["load"], s["function"]))
    L.append("")
    L.append("So there is exactly one place in `JustCause3.exe` where a record's two body ids are")
    L.append("both read and checked against the invalid marker, and it is the one quoted in")
    L.append("section 2.")
    L.append("")

    L.append("### How the loop is reached")
    L.append("")
    L.append("The cinfo loop has **%d** direct callers; its address occurs in **%d** data"
             % (d["refs"]["walker"]["direct_calls"],
                len(d["refs"]["walker"]["rva_slots"]) + len(d["refs"]["walker"]["qword_slots"])))
    L.append("slot(s) (sections: %s) - i.e. `.pdata`'s unwind entry plus one `.rdata` slot."
             % ", ".join("`%s`" % s for s in d["refs"]["walker"]["sections"]))
    L.append("That non-`.pdata` slot, %s, is an `(RVA, int)` pair `(0x141569d00, -1)` inside a"
             % H(DATA_REF))
    L.append("`.rdata` table of such pairs.  So the function's address is taken by data and its")
    L.append("caller is not a direct `call`; the table that dispatches it is **UNKNOWN** (section 6).")
    add_rdata = d["refs"]["add"]["rdata_rva_slots"]
    L.append("The add function is likewise address-taken (`%s`), but its %d decoded `call` sites"
             % (", ".join(H(v) for v in add_rdata) or "no .rdata slot", len(d["callers"])))
    L.append("are the entry points into it.")
    L.append("")
    L.append("## 5. The 494 shipped records through this guard")
    L.append("")
    L.append("| measure | value |")
    L.append("|---|---:|")
    L.append("| files | %d |" % f["files"])
    L.append("| records | %d |" % f["records"])
    L.append("| `bodyB == 0x7fffffff` | %d/%d |" % (f["bodyB_sentinel"], f["records"]))
    L.append("| `bodyA == 0x7fffffff` | %d |" % f["bodyA_sentinel"])
    L.append("| `bodyA` out of range | %d |" % f["bodyA_out_of_range"])
    L.append("| `bodyB` out of range (excluding the sentinel) | %d |" % f["bodyB_out_of_range"])
    L.append("| distinct `bodyA` ids | %d |" % f["distinct_bodyA"])
    L.append("| records the guard rejects (**derived**: sentinel or out-of-range on either id) | %d/%d |"
             % (f["rejected_by_guard"], f["records"]))
    L.append("| records that reach the add (**derived**) | **%d** |" % f["surviving"])
    L.append("")
    L.append("The derivation is the guard above applied to the stored ids; the only assumption is")
    L.append("that the array at `[data+0x140]` is the file's `0x18`-byte cinfo block, which the")
    L.append("matching `0x18` stride and the `+8`/`+0c` field use support, and that the in-memory")
    L.append("body capacity (`[system+0x2c] & 0x3fffffff`) is at least the file's body count.")
    L.append("")
    L.append("## 6. UNKNOWN")
    L.append("")
    L.append("- **Who dispatches the cinfo loop.** No `call`/`jmp` in `.text` targets %s and no"
             % H(w["va"]))
    L.append("  qword slot holds it; the single `.rdata` slot (%s) is an `(RVA, int)` pair"
             % H(DATA_REF))
    L.append("  `(0x141569d00, -1)` inside a table whose owner is not identified.  Where to look:")
    L.append("  the packfile/resource loader that instantiates `hknpPhysicsSystemData` objects.")
    L.append("- **Whether the guard is the only consumer in practice.** The derivation \"%d of %d"
             % (f["rejected_by_guard"], f["records"]))
    L.append("  records rejected, %d surviving\" assumes the data object really carries the file's ids."
             % f["surviving"])
    L.append("  If a loader rewrote `+0x0c` on the way in, this loop would see something else - but")
    L.append("  no such rewrite was found: %s copies the record, and %s copies its ids verbatim."
             % (H(w["va"]), H(c["va"])))
    L.append("- **What the vehicle actually wants.** Whether the 494 sentinel records are inert by")
    L.append("  design (game code builds the joints, as at %s) or the fleet files are templates"
             % H(g["call"]))
    L.append("  that the game never instantiates through this path is not decided here; that needs")
    L.append("  a live-world test, which is out of scope for a static card.")
    L.append("")
    L.append("STATUS: DONE for the question asked - the runtime substitutes nothing, and the")
    L.append("instructions that make that choice are quoted above; the dispatch of the loop and")
    L.append("the vehicle-side intent are UNKNOWN, with the attempted anchors listed.")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- checks
def checks(d, md, js):
    """Re-derive the load-bearing numbers from scratch and compare with the files."""
    f = d["fleet"]
    assert f["records"] == 494 and f["bodyB_sentinel"] == 494, f
    assert f["surviving"] == 0, f
    assert f["rejected_by_guard"] == 494, f
    assert len(d["callers"]) == 13, d["callers"]
    assert d["inventory"]["functions_testing_both"] == ["0x141569d00-0x141569ff0"]
    assert len(d["inventory"]["sites_fed_from_body_fields"]) == 8
    assert sum(1 for c in d["callers"] if c["is_walker"]) == 1, d["callers"]
    assert d["walker"]["skip_target"] == 0x141569FC1
    assert [s["at"] for s in d["add"]["sentinel_sites"]] == [0x1414E7229]
    assert [s["at"] for s in d["release"]["sentinel_sites"]] == [0x1414E73F7]
    assert d["copy"]["sentinel_sites"] == []
    if os.path.exists(MD):
        have = open(MD, encoding="utf-8").read()
        if have != md:
            raise SystemExit("CONSTRAINT_CODE2.md is stale; re-run --write")
    if os.path.exists(JS):
        have = json.load(open(JS, encoding="utf-8"))
        if have != json.loads(json.dumps(d)):
            raise SystemExit("CONSTRAINT_CODE2.json is stale; re-run --write")
    return True


def main(argv):
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: jc3_constraint_code2.py --write|--check")
    d = build()
    md = render(d)
    if argv[1] == "--write":
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        open(JS, "w", encoding="utf-8", newline="\n").write(
            json.dumps(d, indent=1, sort_keys=False) + "\n")
        print("wrote %s (%d lines) and %s" % (MD, md.count("\n"), JS))
        print("records 494, sentinel 494, rejected 494, surviving %d" % d["fleet"]["surviving"])
        print("add call sites %d (walker among them: %s)"
              % (len(d["callers"]),
                 any(c["is_walker"] for c in d["callers"])))
        return 0
    checks(d, md, open(MD, encoding="utf-8").read() if os.path.exists(MD) else md)
    print("CHECK OK: %d records, %d sentinel, %d rejected, %d surviving; %d add sites"
          % (d["fleet"]["records"], d["fleet"]["bodyB_sentinel"],
             d["fleet"]["rejected_by_guard"], d["fleet"]["surviving"], len(d["callers"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
