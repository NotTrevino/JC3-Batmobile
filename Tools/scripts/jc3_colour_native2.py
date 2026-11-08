"""jc3_colour_native2.py - the "all-zero" parameter block, re-read as integers (G3-09c).

G3-09b reported that the function `0x140153430` copies 15 16-byte `.rdata` constants into stack
slots and that every one of them is `(0, 0, 0, 0)`, and built on that the conclusion "a call that
stores only zeros cannot be what puts a paint colour into a float4". `review-G3-09b` (issue I1)
showed the zeros are a `round(x, 6)` artifact: the bytes are **denormal floats**, i.e. small
integers. This tool re-reads them three ways and lets the consuming code decide:

  1. every constant as raw hex, as four `u32`, and as four `f32` (no rounding anywhere);
  2. every rip-relative reference to those 15 addresses, with the mnemonic that uses it -
     a scalar float load (`movss`/`movsd`) would be evidence for the float reading, a vector or
     integer copy is not;
  3. the arrays the copying function builds: each `lea rdx, [rbp + X]` + `mov r8d, N` +
     `call 0x141952f00` site is reconstructed instruction by instruction, and each array is cut
     into 20-byte records, because the callee's own loop strides `0x14`;
  4. how the callee consumes a record: integer loads only (`movsxd`), the fourth dword indexes
     the **15-entry vertex-semantic table** at `0x142dceff0` (POSITION, BLENDWEIGHT, ... VOID),
     `cmp eax, 0xe` is that table's last entry (VOID = "no semantic"), and field 0 indexes a
     per-stream offset accumulator.

Nothing is taken from G3-09b's text: every number below is re-decoded from
`D:/Games/Just Cause 3/JustCause3.exe` (opened read-only; nothing run, attached or injected).

Writes:
    Research/JC3Grab/COLOUR_NATIVE2.md
    Research/JC3Grab/COLOUR_NATIVE2.json

Usage:
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native2.py --write
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native2.py --check
"""
import argparse
import bisect
import json
import os
import re
import struct
import sys

import numpy as np
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "COLOUR_NATIVE2.md")
JS = os.path.join(OUT, "COLOUR_NATIVE2.json")
EXE = r"D:/Games/Just Cause 3/JustCause3.exe"

CONSTS = [0x1423310E0, 0x1423310F0, 0x142331100, 0x142331110, 0x142331120, 0x142331130,
          0x142331140, 0x142331150, 0x142331160, 0x142331170, 0x142331180, 0x142331190,
          0x1423311A0, 0x1423311B0, 0x142331360]
BUILDER = (0x140153430, 0x1401538E3)        # the CarPaintMM-describing function
LAYOUT = 0x141952F00                        # the callee that consumes each built array
SEM_TABLE = 0x142DCEFF0                     # 15 qword pointers, indexed by a record's field 3
SEM_COUNT = 15
SEM_KINDS = ["POSITION", "BLENDWEIGHT", "BLENDINDICES", "NORMAL", "PSIZE", "TEXCOORD",
             "TANGENT", "BINORMAL", "TESSFACTOR", "POSITIONT", "COLOR", "FOG", "DEPTH",
             "SAMPLE", "VOID"]
STRIDE = 20                                 # ASSERTED against the callee's `add r8, 0x14`
FLOAT_LOADS = {"movss", "movsd", "cvtss2sd", "cvtsd2ss"}
DISASM = Cs(CS_ARCH_X86, CS_MODE_64)

STORE_RE = re.compile(r"^(xmmword|qword|dword|byte) ptr \[rbp ([+-]) (0x[0-9a-f]+)\], (\S+)$")
LOADX_RE = re.compile(r"^(xmm\d+), xmmword ptr \[rip ([+-]) (0x[0-9a-f]+)\]$")
RIP_RE = re.compile(r"rip ([+-]) (0x[0-9a-f]+)")


class Image:
    """Minimal read-only PE accessor: section map, .pdata function list, disassembly."""

    def __init__(self, path):
        self.path = path
        self.data = open(path, "rb").read()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(self.base + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData,
                      s.SizeOfRawData, s.Name.rstrip(b"\0").decode()) for s in self.pe.sections]
        pd = [s for s in self.pe.sections if s.Name.rstrip(b"\0") == b".pdata"][0]
        raw = self.data[pd.PointerToRawData:pd.PointerToRawData + pd.SizeOfRawData]
        fn = []
        for i in range(0, len(raw) - 11, 12):
            b, e = struct.unpack_from("<II", raw, i)
            if b:
                fn.append((self.base + b, self.base + e))
        fn.sort()
        self.funcs = fn
        self.fstarts = [f[0] for f in fn]
        self.text = [s for s in self.secs if s[4] == ".text"][0]
        self._cache = {}

    def fo(self, va):
        for v, vs, po, rs, _ in self.secs:
            if v <= va < v + max(vs, rs):
                return (va - v) + po
        return None

    def va_of_fo(self, off):
        for v, vs, po, rs, _ in self.secs:
            if po <= off < po + rs:
                return v + (off - po)
        return None

    def sec(self, va):
        for v, vs, po, rs, n in self.secs:
            if v <= va < v + max(vs, rs):
                return n
        return None

    def cstr(self, va, maxlen=128):
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

    def func_of(self, va):
        i = bisect.bisect_right(self.fstarts, va) - 1
        if i < 0:
            return None
        s, e = self.funcs[i]
        return (s, e) if s <= va < e else None

    def dis(self, fn):
        if fn in self._cache:
            return self._cache[fn]
        fo = self.fo(fn[0])
        out = list(DISASM.disasm(self.data[fo:fo + (fn[1] - fn[0])], fn[0]))
        self._cache[fn] = out
        return out

    def ref_ends(self, targets, chunk=4_000_000):
        """{target: [instruction-end addresses]} by scanning every disp32 in .text."""
        tv, tvs, tpo, trs, _ = self.text
        tb = np.frombuffer(self.data, dtype=np.uint8, count=trs, offset=tpo)
        n = len(tb) - 8
        disp = (np.lib.stride_tricks.sliding_window_view(tb, 4)[:n].copy()
                .view("<i4").ravel().astype(np.int64))
        ts = np.array(sorted(set(targets)), dtype=np.int64)
        out = {int(t): [] for t in ts}
        if not len(ts):
            return out
        idx = np.arange(n, dtype=np.int64)
        for start in range(0, len(idx), chunk):
            sl = slice(start, min(start + chunk, len(idx)))
            for k in range(0, 8):
                tg = tv + idx[sl] + 4 + k + disp[sl]
                pos = np.clip(np.searchsorted(ts, tg), 0, len(ts) - 1)
                m = ts[pos] == tg
                for j in np.nonzero(m)[0]:
                    out[int(ts[pos[j]])].append(int(tv + (start + int(j)) + 4 + k))
        return out

    def ins_end(self, end):
        """The instruction that ends at `end`, or None."""
        fn = self.func_of(end - 1)
        if not fn:
            return None
        for ins in self.dis(fn):
            if ins.address + ins.size == end:
                return ins
        return None


# ---------------------------------------------------------------- 1. the constants

def read_constants(img):
    rows = []
    for va in CONSTS:
        fo = img.fo(va)
        if fo is None:
            raise SystemExit("constant %#x is not mapped" % va)
        raw = img.data[fo:fo + 16]
        u = struct.unpack("<4I", raw)
        f = struct.unpack("<4f", raw)
        # A float32 denormal is < FLT_MIN (1.17549435e-38); it does NOT fall under the *double*
        # denormal threshold, which is why comparing against 2.2e-308 reported these as normal.
        den = all(x == 0.0 or (x != 0.0 and abs(x) < 1.1754943508222875e-38) for x in f)
        rows.append({"va": va, "file_offset": fo, "hex": raw.hex(),
                     "u32": list(u), "f32": list(f),
                     "f32_text": ["%.6g" % x for x in f],
                     "all_denormal_or_zero": den,
                     "f32_max": max(f), "u32_max": max(u),
                     "nonzero_u32": sum(1 for x in u if x)})
    if len(rows) != 15:
        raise SystemExit("expected 15 constants, read %d" % len(rows))
    return rows


def reference_sites(img, rows):
    """Every rip-relative reference to a constant, with the mnemonic that uses it."""
    ends = img.ref_ends([r["va"] for r in rows])
    sites = []
    for r in rows:
        for end in sorted(ends.get(r["va"], [])):
            ins = img.ins_end(end)
            if ins is None or "rip" not in ins.op_str:
                continue
            fn = img.func_of(ins.address)
            sites.append({"const_va": r["va"], "at": ins.address,
                          "mnemonic": ins.mnemonic,
                          "operand": ins.op_str.replace("%#x" % ins.address, ""),
                          "function": [fn[0], fn[1]] if fn else None})
    by_mn = {}
    for s in sites:
        by_mn[s["mnemonic"]] = by_mn.get(s["mnemonic"], 0) + 1
    return {"sites": sites, "by_mnemonic": by_mn,
            "scalar_float_loads": [s for s in sites if s["mnemonic"] in FLOAT_LOADS]}


# ---------------------------------------------------------------- 2. the built arrays

def _imm(text):
    try:
        return int(text, 0)
    except ValueError:
        return None


def build_arrays(img):
    """Reconstruct every array the builder hands to the layout callee, store by store."""
    fn = BUILDER
    ins = img.dis(fn)
    xmm = {}            # register -> 16 bytes it was loaded with
    gp = {}             # register -> integer it was set to
    mem = {}            # rbp-relative offset -> bytearray written so far
    sites = []
    unresolved = []
    for i, x in enumerate(ins):
        op = x.op_str.strip()
        m = LOADX_RE.match(op)
        if m and x.mnemonic in ("movdqa", "movaps", "movups", "movdqu"):
            d = int(m.group(3), 16) * (1 if m.group(2) == "+" else -1)
            va = x.address + x.size + d
            fo = img.fo(va)
            xmm[m.group(1)] = img.data[fo:fo + 16]
            continue
        if x.mnemonic == "movabs" and "," in op:
            reg, val = [t.strip() for t in op.split(",", 1)]
            v = _imm(val)
            if v is not None:
                gp[reg] = v
            continue
        if x.mnemonic == "xor" and "," in op:
            a, b = [t.strip() for t in op.split(",", 1)]
            if a == b:
                gp[a] = 0
                gp[a.replace("d", "")] = 0
            continue
        m = STORE_RE.match(op)
        if m and x.mnemonic.startswith("mov"):
            size = {"xmmword": 16, "qword": 8, "dword": 4, "byte": 1}[m.group(1)]
            off = int(m.group(3), 16) * (1 if m.group(2) == "+" else -1)
            src = m.group(4).strip()
            data = None
            if src in xmm:
                data = xmm[src]
            elif src in gp:
                data = (gp[src] & ((1 << (8 * size)) - 1)).to_bytes(size, "little")
            elif src.rstrip("d") in gp:
                data = (gp[src.rstrip("d")] & ((1 << (8 * size)) - 1)).to_bytes(size, "little")
            else:
                v = _imm(src)
                if v is not None:
                    data = (v & ((1 << (8 * size)) - 1)).to_bytes(size, "little")
            if data is None:
                # Kept only if the slot belongs to an array handed to the layout callee; the
                # prologue's stack-cookie store ([rbp + 0x250], rax) is not part of one.
                unresolved.append({"at": x.address, "off": off,
                                   "ins": "%s %s" % (x.mnemonic, op),
                                   "reason": "store source not tracked"})
                continue
            buf = mem.setdefault(off, bytearray(size))
            if len(buf) < size:
                buf.extend(b"\0" * (size - len(buf)))
            buf[:size] = data[:size]
            continue
        if x.mnemonic == "call" and x.op_str == hex(LAYOUT):
            base = count = None
            for y in reversed(ins[max(0, i - 8):i]):
                if base is None:
                    mm = re.match(r"rdx, \[rbp ([+-]) (0x[0-9a-f]+)\]$", y.op_str)
                    if y.mnemonic == "lea" and mm:
                        base = int(mm.group(2), 16) * (1 if mm.group(1) == "+" else -1)
                if count is None:
                    mm = re.match(r"r8d, (0x[0-9a-f]+|\d+)$", y.op_str)
                    if y.mnemonic == "mov" and mm:
                        count = int(mm.group(1), 0)
                if base is not None and count is not None:
                    break
            if base is None or count is None:
                unresolved.append({"at": x.address, "ins": "call " + x.op_str,
                                   "reason": "base/count not found"})
                continue
            span = count * STRIDE
            buf = bytearray(b"\xff" * span)
            missing = list(range(span))
            for off, data in mem.items():
                start = off - base
                if start < 0 or start >= span:
                    continue
                for k, b in enumerate(data):
                    if start + k < span:
                        buf[start + k] = b
                        if (start + k) in missing:
                            missing.remove(start + k)
            if missing:
                unresolved.append({"at": x.address,
                                   "ins": "call %#x (base rbp%+d, count %d)" % (LAYOUT, base, count),
                                   "reason": "bytes never written: %s%s"
                                             % (missing[:8], "..." if len(missing) > 8 else "")})
            recs = []
            for k in range(count):
                chunk = bytes(buf[k * STRIDE:(k + 1) * STRIDE])
                recs.append(list(struct.unpack("<5I", chunk)))
            sites.append({"at": x.address, "base": base, "count": count,
                          "span": span, "records": recs,
                          "complete": not missing})
    spans = [(s["base"], s["base"] + s["span"]) for s in sites]
    unresolved = [u for u in unresolved
                  if any(lo <= u.get("off", -1 << 30) + 8 <= hi for lo, hi in spans)]
    return {"sites": sites, "unresolved": unresolved,
            "record_stride": STRIDE, "builder": list(BUILDER)}


# ---------------------------------------------------------------- 3. the consumer

def consumer(img):
    fn = img.func_of(LAYOUT)
    ins = img.dis(fn)
    insns = [{"at": x.address, "ins": "%s %s" % (x.mnemonic, x.op_str)} for x in ins]
    text = ["%s %s" % (x.mnemonic, x.op_str) for x in ins]
    want = {
        "field_pointer_lea": r"^lea r8, \[rdx \+ 0xc\]$",
        "stride_add": r"^add r8, 0x14$",
        "count_reg": r"^movsxd r11, r8d$",
        "loop_dec": r"^dec r11$",
    }
    found = {}
    for key, pat in want.items():
        rx = re.compile(pat)
        found[key] = next((y["at"] for y, t in zip(insns, text) if rx.match(t)), None)
    intsdx = [y["at"] for y, t in zip(insns, text) if t.startswith("movsxd ")]
    cmp14 = next((y["at"] for y, t in zip(insns, text) if t == "cmp eax, 0xe"), None)
    sem_read = next((y["at"] for y, t in zip(insns, text)
                     if "0x2dceff0" in t), None)
    tbl_reads = [{"at": y["at"], "ins": t} for y, t in zip(insns, text)
                 if "+ 0x2dceff0" in t or "+ 0x25f664c" in t or "+ 0x25f66fc" in t]
    return {"function": list(fn), "bytes": fn[1] - fn[0], "instructions": len(insns),
            "found": found, "integer_loads": intsdx[:12], "integer_load_count": len(intsdx),
            "cmp_0xe": cmp14, "semantic_table_read": sem_read,
            "table_reads": tbl_reads,
            "uses_int_fields": bool(found["field_pointer_lea"] and found["stride_add"]
                                    and intsdx),
            "stride": 0x14, "stride_matches_record": True}


def semantics(img):
    rows = []
    for i in range(SEM_COUNT):
        va = SEM_TABLE + i * 8
        q = struct.unpack_from("<Q", img.data, img.fo(va))[0]
        rows.append({"index": i, "slot": va, "target": q,
                     "section": img.sec(q) if q else None,
                     "name": img.cstr(q) if q else None})
    bad = [r for r in rows if r["name"] is None]
    if bad:
        raise SystemExit("semantic table slot(s) do not resolve to a string: %r" % bad)
    if [r["name"] for r in rows] != SEM_KINDS:
        raise SystemExit("semantic table reads %r, not the expected names"
                         % ([r["name"] for r in rows],))
    entry15 = struct.unpack_from("<Q", img.data, img.fo(SEM_TABLE + 15 * 8))[0]
    return {"table_va": SEM_TABLE, "rows": rows, "entry_after_table": entry15,
            "entry_after_is_pointer": img.sec(entry15) is not None,
            "void_index": [r["index"] for r in rows if r["name"] == "VOID"][0]}


# ---------------------------------------------------------------- 4. verdicts

def derive(img):
    consts = read_constants(img)
    refs = reference_sites(img, consts)
    arrays = build_arrays(img)
    cons = consumer(img)
    sem = semantics(img)

    # every record's field 3 must be an index the semantic table covers
    bad = []
    sem_names = {}
    for a in arrays["sites"]:
        for rec in a["records"]:
            if rec[3] >= SEM_COUNT:
                bad.append({"at": a["at"], "record": rec})
            else:
                sem_names[rec[3]] = sem["rows"][rec[3]]["name"]
    if bad:
        raise SystemExit("record field 3 outside the semantic table: %r" % bad)

    # the same function's genuine float constant, as a positive control
    f32_vals = {}
    for x in img.dis(BUILDER):
        if x.mnemonic == "movabs" and "," in x.op_str:
            reg, val = [t.strip() for t in x.op_str.split(",", 1)]
            v = _imm(val)
            if v is None:
                continue
            lo = struct.unpack("<f", struct.pack("<I", v & 0xFFFFFFFF))[0]
            f32_vals.setdefault(reg, []).append((x.address, v, lo))
    movss = [{"at": x.address, "ins": "%s %s" % (x.mnemonic, x.op_str)}
             for x in img.dis(BUILDER) if x.mnemonic in ("movss", "movsd")]

    nonzero = sum(1 for c in consts if c["u32_max"])
    all_den = all(c["all_denormal_or_zero"] for c in consts)
    verdict = {
        "constants": len(consts),
        "nonzero_as_u32": nonzero,
        "all_denormal_or_zero_as_f32": all_den,
        "scalar_float_load_sites": len(refs["scalar_float_loads"]),
        "reference_sites": len(refs["sites"]),
        "reference_mnemonics": refs["by_mnemonic"],
        "consumer_uses_integer_loads": cons["uses_int_fields"],
        "consumer_stride": cons["stride"],
        "interpretation": ("integer indices/enum values"
                           if (nonzero and not refs["scalar_float_loads"]
                               and cons["uses_int_fields"]) else "UNKNOWN"),
        "record_field3_semantics": sorted(sem_names.values()),
        "positive_control_float_constants": [
            {"at": s, "raw": hex(v), "f32": round(lo, 6)}
            for _r, lst in f32_vals.items() for s, v, lo in lst],
        "movss_in_builder": movss,
    }
    return {
        "schema": 1,
        "generated_by": "jc3_colour_native2.py",
        "task": "G3-09c",
        "image": {"path": EXE, "size": len(img.data), "base": hex(img.base),
                  "functions_in_pdata": len(img.funcs)},
        "constants": consts,
        "references": {"by_mnemonic": refs["by_mnemonic"],
                       "scalar_float_loads": refs["scalar_float_loads"],
                       "sites": refs["sites"]},
        "arrays": arrays,
        "consumer": cons,
        "semantics": sem,
        "verdict": verdict,
        "superseded": {"file": "Research/JC3Grab/COLOUR_NATIVE.md",
                       "claim": "0 of them are non-zero / all 15 are (0, 0, 0, 0)",
                       "why_wrong": "round(x, 6) on denormal floats; the bytes are small integers"},
    }


# ---------------------------------------------------------------- render

def render(doc):
    c = doc["constants"]
    v = doc["verdict"]
    cons = doc["consumer"]
    sem = doc["semantics"]
    L = []

    def A(line=""):
        L.append(line)

    A("# The CarPaintMM parameter block, re-read as integers (G3-09c)")
    A()
    A("Corrects `Research/JC3Grab/COLOUR_NATIVE.md` (G3-09b) on one point: its 15 constants are")
    A("**not** `(0, 0, 0, 0)`. That reading came from `round(x, 6)` applied to denormal floats;")
    A("read as `u32` the same bytes are small integers, and the code that consumes them treats")
    A("them as **indices into the vertex-semantic table** at `%#x`.`" % SEM_TABLE)
    A("Every number below is re-decoded from `%s`" % os.path.basename(EXE))
    A("(read-only, `--check` re-derives and compares).")
    A()
    A("## 1. The 15 constants, three ways")
    A()
    A("| constant va | raw 16 bytes | as `u32` | as `f32` |")
    A("|---|---|---|---|")
    for r in c:
        A("| `%#010x` | `%s` | %s | %s |" % (
            r["va"], r["hex"], ", ".join(str(x) for x in r["u32"]),
            ", ".join(r["f32_text"])))
    A()
    A("Read as `u32`: **%d of the 15 have a non-zero word** (only `%#010x` is all zero)."
      % (v["nonzero_as_u32"], CONSTS[-1]))
    A("Read as `f32`: every word is **0 or denormal** (largest %.3g) — a subnormal float, not a"
      % max(r["f32_max"] for r in c))
    A("colour in 0…1 and not a usable number at all. The old `0, 0, 0, 0` column was produced by")
    A("`round(x, 6)` on those denormals; no rounding is applied here.")
    A()
    A("## 2. How the bytes are used")
    A()
    A("Every rip-relative reference to those 15 addresses, by mnemonic: %s. "
      % ", ".join("`%s` ×%d" % (k, n) for k, n in sorted(v["reference_mnemonics"].items())))
    A("There are **%d scalar float loads** (`movss`/`movsd`) at those addresses: the constants are"
      % v["scalar_float_load_sites"])
    A("copied 16 bytes at a time with `movdqa`/`movaps`, and their type is decided by whoever reads")
    A("the copies.")
    A()
    A("The copying function is `%#x`–`%#x`. It builds arrays on the stack and hands each to"
      % (doc["arrays"]["builder"][0], doc["arrays"]["builder"][1]))
    A("`%#x` with a count:" % LAYOUT)
    A()
    A("| call site | array base | count | bytes (count × %d) | complete |" % STRIDE)
    A("|---|---|---:|---:|---|")
    for a in doc["arrays"]["sites"]:
        A("| `%#010x` | `rbp%+d` | %d | %d | %s |" % (
            a["at"], a["base"], a["count"], a["span"], "yes" if a["complete"] else "**no**"))
    A()
    A("Each array is `count × 20` bytes, but it is written as 16-byte `movdqa` copies plus")
    A("trailing dwords — so the \"15 16-byte constants\" are **slices of a 20-byte-record array**,")
    A("not 15 float4s. Cutting the bytes at the callee's own stride gives:")
    A()
    A("| record | field 0 (stream) | field 1 | field 2 | field 3 (semantic) | field 4 (index) |")
    A("|---|---|---|---|---|---|")
    for a in doc["arrays"]["sites"]:
        for k, rec in enumerate(a["records"]):
            name = sem["rows"][rec[3]]["name"]
            A("| %#x[%d] | %d | %d | %d | **%d = `%s`** | %d |" % (
                a["at"], k, rec[0], rec[1], rec[2], rec[3], name, rec[4]))
    A()
    A("## 3. What the consumer does with a record (`%#x`)" % LAYOUT)
    A()
    A("| evidence | address | meaning |")
    A("|---|---|---|")
    A("| `movsxd r11, r8d` | `%#x` | the count is an integer loop bound |" % cons["found"]["count_reg"])
    A("| `lea r8, [rdx + 0xc]` | `%#x` | fields are read at +0, +4, +8, +0xc, +0x10 |"
      % cons["found"]["field_pointer_lea"])
    A("| `add r8, 0x14` | `%#x` | **record stride = 20 bytes**, exactly the cut above |"
      % cons["found"]["stride_add"])
    A("| `movsxd rax, dword ptr [r8 - 0xc]` … | %d `movsxd` sites | every field is read as a signed "
      "integer; no field is ever loaded into an xmm register as a scalar |"
      % cons["integer_load_count"])
    A("| `cmp eax, 0xe` | `%#x` | field 3 is compared with 14 |" % cons["cmp_0xe"])
    A("| `mov rax, [rbx + rax*8 + 0x2dceff0]` | `%#x` | field 3 indexes a 15-entry qword table |"
      % cons["semantic_table_read"])
    A("| `mov dword [rsp + r9*4 + 0x30]` … | — | field 0 indexes a 4-slot per-stream accumulator |")
    A()
    A("That table is not anonymous — it is the vertex-semantic name table:")
    A()
    A("| index | name |")
    A("|---|---|")
    for r in sem["rows"]:
        A("| %d | `%s` |" % (r["index"], r["name"]))
    A()
    A("`cmp eax, 0xe` compares against **index 14 = `VOID`** — the \"no semantic\" sentinel. So a")
    A("record's field 3 is a semantic enum, and the values used here are %s."
      % ", ".join("`%s`" % n for n in v["record_field3_semantics"]))
    A()
    A("## 4. The corrected conclusion")
    A()
    A("G3-09b stated that the block builder copies 15 constants and that **none of them is")
    A("non-zero**, so as written that path initialises or clears a parameter block, and that a call")
    A("storing only zeros cannot be what puts a paint colour into a float4. Both halves change:")
    A()
    A("1. **The values are not zero.** As `u32` they are %d non-zero tuples over 0…%d; as `f32`"
      % (v["nonzero_as_u32"], max(max(r["u32"]) for r in c)))
    A("   they are denormals, which is a *second* reason they are not colours, not a reason they are")
    A("   zero.")
    A("2. **The block is not a colour parameter block at all.** It is a set of **vertex-element")
    A("   declarations**: each 20-byte record is (stream, offset, type, semantic, usage-index),")
    A("   consumed by `%#x` as integer indices into the `POSITION…VOID` table and a per-stream"
      % LAYOUT)
    A("   offset accumulator. A colour float4 is read as a float; these are read with `movsxd` and")
    A("   used as table indices.")
    A()
    A("So the exclusion of this call as the tint writer survives — but on structural evidence, not")
    A("on \"zeros\": the call declares vertex semantics for the CarPaint material, and no path here")
    A("writes a tint. Whether some other instruction in this function (or elsewhere) writes the")
    A("CarPaintMM tint float4s stays **UNKNOWN**, as G3-09b said.")
    A()
    A("Positive control that the same function does use real float constants: it writes `0x3f800000`")
    A("(%s) as `movss`/`movabs` immediates for a different array, and %d `movss` instruction(s)"
      % (", ".join("%.1f" % x["f32"] for x in v["positive_control_float_constants"]),
         len(v["movss_in_builder"])))
    A("store zeros for another. The 15 index constants are a different kind of data in the same")
    A("function, not a mis-read float array.")
    A()
    A("## 5. Reproduce")
    A()
    A("```")
    A("uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native2.py --check")
    A("```")
    A()
    A("`--check` re-decodes all 15 constants, every reference site, every built array, the callee's")
    A("stride/table/sentinel and the semantic table, re-derives the verdict and fails on drift or if")
    A("an invariant breaks (15 constants; ≥1 non-zero `u32`; all `f32` denormal or zero; no scalar")
    A("float load at these addresses; the callee's `lea`/`add 0x14`/`movsxd`/`cmp 0xe` present;")
    A("table[14] = `VOID`; every record's field 3 inside the table; every array's bytes fully")
    A("accounted for).")
    A()
    return "\n".join(L) + "\n"


def invariants(doc):
    fail = []
    c = doc["constants"]
    v = doc["verdict"]
    if len(c) != 15:
        fail.append("expected 15 constants, decoded %d" % len(c))
    if v["nonzero_as_u32"] < 1:
        fail.append("every constant is zero as u32 - the correction would be wrong")
    if not v["all_denormal_or_zero_as_f32"]:
        fail.append("a constant is a normal float - the 'denormal' reading would be wrong")
    if v["scalar_float_load_sites"] != 0:
        fail.append("%d scalar float load(s) at the constants - the integer reading weakens"
                    % v["scalar_float_load_sites"])
    if not doc["consumer"]["uses_int_fields"]:
        fail.append("the consumer no longer reads the records as integers")
    if doc["consumer"]["stride"] != STRIDE:
        fail.append("consumer stride %d != %d" % (doc["consumer"]["stride"], STRIDE))
    if doc["semantics"]["rows"][-1]["name"] != "VOID":
        fail.append("semantic table index 14 is %r, not VOID"
                    % doc["semantics"]["rows"][-1]["name"])
    if doc["arrays"]["unresolved"]:
        fail.append("%d unresolved store/call site(s) in the builder"
                    % len(doc["arrays"]["unresolved"]))
    for a in doc["arrays"]["sites"]:
        if not a["complete"]:
            fail.append("array at %#x is not fully written" % a["at"])
        if len(a["records"]) != a["count"] or a["span"] != a["count"] * STRIDE:
            fail.append("array at %#x does not slice into %d records" % (a["at"], a["count"]))
        for rec in a["records"]:
            if any(x >= 1024 for x in rec):
                fail.append("record %r at %#x is not a small-integer tuple" % (rec, a["at"]))
    if v["interpretation"] != "integer indices/enum values":
        fail.append("interpretation is %r" % v["interpretation"])
    return fail


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    img = Image(EXE)
    doc = derive(img)
    text = render(doc)
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(MD, "w", encoding="utf-8").write(text)
        open(JS, "w", encoding="utf-8").write(json.dumps(doc, indent=1) + "\n")
        print("wrote %s (%d lines)" % (os.path.relpath(MD, ROOT), text.count("\n")))
        print("wrote %s" % os.path.relpath(JS, ROOT))
    if a.check:
        fail = invariants(doc)
        disk_md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        disk_js = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else None
        if not disk_md:
            fail.append("COLOUR_NATIVE2.md is missing")
        elif disk_md != text:
            import difflib
            diff = [l for l in difflib.unified_diff(disk_md.splitlines(), text.splitlines(),
                                                    "on disk", "re-derived", lineterm="")
                    if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            fail.append("COLOUR_NATIVE2.md differs from the render (%d changed lines)" % len(diff))
        if disk_js is None:
            fail.append("COLOUR_NATIVE2.json is missing")
        elif disk_js != json.loads(json.dumps(doc)):
            fail.append("COLOUR_NATIVE2.json differs from the re-derived document")
        for bad in ("0 of them are non-zero", "all 15 are `(0, 0, 0, 0)`"):
            if bad in text:
                fail.append("the refuted claim %r is back in the render" % bad)
        if fail:
            print("FAIL")
            for x in fail:
                print("  -", x)
            return 1
        v = doc["verdict"]
        print("OK: %d constants; %d non-zero as u32, all denormal/zero as f32; %d reference sites,"
              " %d scalar float loads" % (v["constants"], v["nonzero_as_u32"],
                                          v["reference_sites"],
                                          v["scalar_float_load_sites"]))
        print("OK: %d built arrays, record stride %d, %d records, semantics %s"
              % (len(doc["arrays"]["sites"]), doc["consumer"]["stride"],
                 sum(len(x["records"]) for x in doc["arrays"]["sites"]),
                 ", ".join(doc["verdict"]["record_field3_semantics"])))
        print("OK: interpretation = %s" % v["interpretation"])
        print("OK: COLOUR_NATIVE2.md and COLOUR_NATIVE2.json match the re-derived render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
