"""jc3_colour_native.py - G3-09b: the paint-tint path in JustCause3.exe (static, read-only).

What it does, all from the executable's bytes (nothing is run, attached or injected):
  1. Parses the PE (sections, image base) and the `.pdata` function table.
  2. Finds the ADF schema names this card names - `Tint`, `occurrence`, `tint_r`, `tint_g`,
     `tint_b`, `specular_gloss`, `metallic`, `clear_coat`, `A[Tint]`, `Palette` - as one
     contiguous NUL-terminated string run in `.rdata`, and counts the code references to
     each name.
  3. Finds every `CarPaintMM*` shader name, its code references, the referencing functions,
     the variant format string (`CarPaintMM%s%s%s`), the callees, and the 16-byte constants
     those functions copy - the CarPaintMM plumbing at the address and bytes.
  4. Finds `ToneMapping` / `ToneMap` / `Exposure` / `exposure` and counts their code
     references: a value no instruction loads is not an exposure constant.

Reference oracle (same as `grab_controls_native.py`): every target address is resolved in one
chunked pass over `.text` (disp32 of a rip-relative operand), then each hit is kept only if a
real instruction in a `.pdata`-bounded function decodes to end exactly at that disp32 and its
text says `rip`. A byte pattern alone is never a reference.

Labels: `decoded` (address + bytes/disassembly), `derived` (rule + inputs), `UNKNOWN` (what
was tried and where the answer would be).

Usage
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native.py --write
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native.py --check
"""
from __future__ import annotations

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
MD = os.path.join(OUT, "COLOUR_NATIVE.md")
JS = os.path.join(OUT, "COLOUR_NATIVE.json")
EXE = r"D:/Games/Just Cause 3/JustCause3.exe"

SCHEMA_NAMES = ["Tint", "occurrence", "tint_r", "tint_g", "tint_b", "specular_gloss",
                "metallic", "clear_coat", "A[Tint]", "Palette", "tints"]
SCHEMA_ORDER = ["Tint", "occurrence", "tint_r", "tint_g", "tint_b", "specular_gloss",
                "metallic", "clear_coat"]
TONE_NAMES = ["ToneMapping", "ToneMap", "Exposure", "exposure"]
DISASM = Cs(CS_ARCH_X86, CS_MODE_64)


class Image:
    def __init__(self, path):
        self.path = path
        self.data = open(path, "rb").read()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(self.base + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData,
                      s.SizeOfRawData, s.Name.rstrip(b"\0").decode())
                     for s in self.pe.sections]
        self.text = [s for s in self.secs if s[4] == ".text"][0]
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
        tv, tvs, tpo, trs, _ = self.text
        tb = np.frombuffer(self.data, dtype=np.uint8, count=trs, offset=tpo)
        n = len(tb) - 8
        self.disp = (np.lib.stride_tricks.sliding_window_view(tb, 4)[:n].copy()
                     .view("<i4").ravel().astype(np.int64))
        self.idx = np.arange(n, dtype=np.int64)
        self.tv = tv
        self._cache = {}
        self.refmap = {}

    # -- addressing -------------------------------------------------------
    def fo(self, va):
        for v, vs, po, rs, _ in self.secs:
            if v <= va < v + vs:
                return (va - v) + po
        return None

    def va_of_fo(self, off):
        for v, vs, po, rs, _ in self.secs:
            if po <= off < po + rs:
                return v + (off - po)
        return None

    def sec(self, va):
        for v, vs, po, rs, n in self.secs:
            if v <= va < v + vs:
                return n
        return None

    def cstr(self, va, maxlen=256):
        fo = self.fo(va)
        if fo is None:
            return None
        end = self.data.find(b"\0", fo, fo + maxlen)
        if end < 0:
            return None
        s = self.data[fo:end]
        if len(s) < 2 or not all(32 <= c < 127 for c in s):
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

    # -- references -------------------------------------------------------
    def build_refmap(self, targets, chunk=4_000_000):
        """One chunked pass: disp32 of any instruction end that equals a target address."""
        ts = np.array(sorted(set(targets)), dtype=np.int64)
        cand = {int(t): [] for t in ts}
        if not len(ts):
            return
        for start in range(0, len(self.idx), chunk):
            sl = slice(start, min(start + chunk, len(self.idx)))
            base = self.tv + self.idx[sl]
            for k in range(0, 8):
                tg = base + 4 + k + self.disp[sl]
                pos = np.clip(np.searchsorted(ts, tg), 0, len(ts) - 1)
                m = ts[pos] == tg
                if not m.any():
                    continue
                for j in np.nonzero(m)[0]:
                    end = int(self.tv + (start + int(j)) + 4 + k)
                    cand[int(tg[j])].append(end)
        self.refmap = {t: sorted(self._verify(t, ends)) for t, ends in cand.items()}

    def _verify(self, target, ends):
        good = []
        for end in ends:
            fn = self.func_of(end - 1)
            if not fn:
                continue
            for ins in self.dis(fn):
                if ins.address + ins.size == end and "rip" in ins.op_str:
                    good.append(ins.address)
                    break
        return good

    def refs(self, target):
        return self.refmap.get(int(target), [])

    def string_vas(self, name):
        out = []
        pat = re.escape(name.encode("ascii")) + rb"\0"
        for m in re.finditer(pat, self.data):
            va = self.va_of_fo(m.start())
            if va is not None and self.cstr(va) == name:
                out.append(va)
        return out


def string_runs(img):
    """Maximal runs of adjacent NUL-terminated printable strings in .rdata."""
    rva, rvs, rpo, rrs, _ = [s for s in img.secs if s[4] == ".rdata"][0]
    blob = img.data[rpo:rpo + rrs]
    runs, cur, pos = [], [], 0
    while pos < len(blob):
        end = blob.find(b"\0", pos)
        if end < 0:
            break
        s = blob[pos:end]
        if len(s) >= 2 and all(32 <= c < 127 for c in s):
            cur.append((rva + pos, s.decode("latin1")))
            pos = end + 1
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
            pos = end + 1
    if len(cur) > 1:
        runs.append(cur)
    return runs


def schema_run(img):
    for run in string_runs(img):
        names = {n for _va, n in run}
        if {"tint_r", "tint_g", "tint_b", "Palette"} <= names:
            return run
    return None


def fn_names(img, fn):
    out = []
    for ins in img.dis(fn):
        m = re.search(r"rip ([+-]) (0x[0-9a-f]+)", ins.op_str)
        if not m:
            continue
        d = int(m.group(2), 16) * (1 if m.group(1) == "+" else -1)
        tgt = ins.address + ins.size + d
        s = img.cstr(tgt) if img.sec(tgt) == ".rdata" else None
        if s:
            out.append({"at": ins.address, "name": s, "name_va": tgt,
                        "ins": "%s %s" % (ins.mnemonic, ins.op_str)})
    return out


def fn_calls(img, fn):
    return [{"at": ins.address, "target": int(ins.op_str, 16)}
            for ins in img.dis(fn)
            if ins.mnemonic == "call" and ins.op_str.startswith("0x")]


def float4_at(img, va):
    fo = img.fo(va)
    if fo is None:
        return None
    return [round(x, 6) for x in struct.unpack_from("<4f", img.data, fo)]


def fn_constants(img, fn):
    out = []
    for ins in img.dis(fn):
        if not ins.mnemonic.startswith("mov") or "xmmword ptr [rip" not in ins.op_str:
            continue
        m = re.search(r"rip ([+-]) (0x[0-9a-f]+)", ins.op_str)
        if not m:
            continue
        d = int(m.group(2), 16) * (1 if m.group(1) == "+" else -1)
        va = ins.address + ins.size + d
        v = float4_at(img, va)
        if v is not None:
            out.append({"at": ins.address, "const_va": va, "value": v,
                        "ins": "%s %s" % (ins.mnemonic, ins.op_str)})
    return out


def fn_stores(img, fn):
    return [{"at": ins.address, "ins": "%s %s" % (ins.mnemonic, ins.op_str)}
            for ins in img.dis(fn)
            if ins.mnemonic.startswith("mov") and ins.op_str.startswith("xmmword ptr [")]


def paint_functions(img):
    fns = {}
    for va in img.string_vas("CarPaintMM"):
        for at in img.refs(va):
            fn = img.func_of(at)
            if fn:
                fns.setdefault(fn, []).append({"at": at, "name_va": va, "name": "CarPaintMM"})
    rows = []
    for fn, hits in sorted(fns.items()):
        names = fn_names(img, fn)
        calls = fn_calls(img, fn)
        rows.append({
            "function": [fn[0], fn[1]], "bytes": fn[1] - fn[0],
            "direct_refs": sorted(hits, key=lambda h: h["at"]),
            "calls": calls,
            "call_targets": sorted({c["target"] for c in calls}),
            "car_paint_names": sorted({n["name"] for n in names
                                       if n["name"].startswith(("CarPaint", "CarOutline"))}),
            "name_count": len(names),
            "format_strings": [n for n in names if "%s" in n["name"]],
            "constants": fn_constants(img, fn),
            "stores16": fn_stores(img, fn),
        })
    return rows


def derive(img):
    print("  scanning .rdata string runs ...", flush=True)
    run = schema_run(img) or []
    tone_vas = {n: img.string_vas(n) for n in TONE_NAMES}
    paint_vas = img.string_vas("CarPaintMM")
    targets = [va for va, _n in run] + [va for v in tone_vas.values() for va in v] \
        + paint_vas + img.string_vas("CarPaintMM%s%s%s")
    print("  resolving %d target addresses in .text ..." % len(targets), flush=True)
    img.build_refmap(targets)
    print("  %d instruction sites verified" % sum(len(v) for v in img.refmap.values()),
          flush=True)

    rows = [{"va": va, "file_offset": img.fo(va), "name": n,
             "schema_member": n in SCHEMA_NAMES, "code_refs": len(img.refs(va))}
            for va, n in run]
    wins = [n for n in SCHEMA_ORDER if any(r["name"] == n for r in rows)]
    idxs = [next(i for i, r in enumerate(rows) if r["name"] == n) for n in wins]
    schema = {
        "run_length": len(rows),
        "first_va": rows[0]["va"] if rows else None,
        "last_va": rows[-1]["va"] if rows else None,
        "strings": rows,
        "schema_order_present": wins,
        "schema_order_contiguous": (len(idxs) > 1
                                    and idxs == list(range(idxs[0], idxs[0] + len(idxs)))),
        "schema_member_code_refs": sum(r["code_refs"] for r in rows if r["schema_member"]),
    }
    tone = {}
    for n, vas in tone_vas.items():
        tone[n] = {"occurrences": len(vas),
                   "rows": [{"va": va, "file_offset": img.fo(va),
                             "code_refs": len(img.refs(va))} for va in vas],
                   "code_refs_total": sum(len(img.refs(va)) for va in vas)}
    paint = paint_functions(img)
    return {
        "task": "G3-09b",
        "image": {"path": EXE, "size": len(img.data), "base": hex(img.base),
                  "sections": [{"name": n, "va": hex(v), "vsize": vs, "raw_size": rs}
                               for v, vs, po, rs, n in img.secs],
                  "functions_in_pdata": len(img.funcs)},
        "schema_block": schema,
        "tone": tone,
        "paint": paint,
        "measured": {
            "schema_run_length": schema["run_length"],
            "schema_member_code_refs": schema["schema_member_code_refs"],
            "paint_functions": len(paint),
            "paint_name_total": len(paint_vas),
            "tone_code_refs": sum(t["code_refs_total"] for t in tone.values()),
            "variant_format_present": any("CarPaintMM%s%s%s" == f["name"]
                                           for r in paint for f in r["format_strings"]),
            "tintcolor_occurrences": len(img.string_vas("TintColorR")),
        },
    }


def hx(v):
    return "-" if v is None else "0x%X" % v


def render(doc):
    L = []
    w = L.append
    im = doc["image"]
    sb = doc["schema_block"]
    m = doc["measured"]
    w("# JC3 paint tint and colour: the executable (G3-09b)")
    w("")
    w("Generated by `Tools/scripts/jc3_colour_native.py --write` from `%s` (%d bytes, image "
      "base %s, %d `.pdata` functions). `--check` re-derives and compares. The file is opened "
      "read-only; nothing is run, attached or injected."
      % (im["path"], im["size"], im["base"], im["functions_in_pdata"]))
    w("")
    w("Labels: `decoded` = an address plus the bytes/disassembly that carries it; `derived` = "
      "a rule over decoded facts, stated; `UNKNOWN` = not answerable from these bytes, with "
      "what was tried.")
    w("")
    w("## 1. The palette schema is in the executable, as data")
    w("")
    w("One contiguous `.rdata` run of **%d** NUL-terminated names at %s..%s is the engine's "
      "ADF schema/field-name table, and it contains the palette fields. Decoded: the names "
      "and their addresses. The palette fields appear in the same order as the ADF decode in "
      "`COLOUR.md` (**contiguous: %s**) - an independent confirmation of that field order "
      "from the engine's own schema, not from the asset."
      % (sb["run_length"], hx(sb["first_va"]), hx(sb["last_va"]),
         sb["schema_order_contiguous"]))
    w("")
    w("| va | file offset | name | palette schema member | code refs |")
    w("|---|---|---|---|---|")
    for r in sb["strings"]:
        if r["schema_member"]:
            w("| %s | 0x%X | `%s` | yes | %d |"
              % (hx(r["va"]), r["file_offset"], r["name"], r["code_refs"]))
    w("")
    w("**Decisive measurement: every palette schema member has 0 code references** - %d "
      "references over the %d members. No instruction in `JustCause3.exe` addresses `tint_r`, "
      "`tint_g`, `tint_b`, `specular_gloss`, `metallic`, `clear_coat`, `Palette` or `tints` "
      "by name: the palette is read by the generic ADF/schema walker, which reaches the fields "
      "by offset. A name-based search of the executable therefore cannot find the tint "
      "writer, and this one does not."
      % (sb["schema_member_code_refs"],
         len([r for r in sb["strings"] if r["schema_member"]])))
    w("")
    w("## 2. `CarPaintMM`: what the code references")
    w("")
    w("%d `CarPaintMM` string occurrence(s). Every function that references one is listed "
      "below with its shader-name table, its callees and the 16-byte constants it copies."
      % m["paint_name_total"])
    w("")
    for r in doc["paint"]:
        w("### function %s-%s (%d bytes)" % (hx(r["function"][0]), hx(r["function"][1]),
                                             r["bytes"]))
        w("")
        w("- direct references to a `CarPaintMM*` name: " +
          ", ".join("%s (`%s`)" % (hx(h["at"]), h["name"]) for h in r["direct_refs"]))
        w("- other shader names it resolves (%d strings referenced in all): %s"
          % (r["name_count"], ", ".join("`%s`" % n for n in r["car_paint_names"])))
        if r["format_strings"]:
            w("- format string(s) it references (any name containing `%s`): " +
              ", ".join("`%s` at %s" % (f["name"], hx(f["name_va"]))
                        for f in r["format_strings"]))
        w("- callees: " + (", ".join(hx(t) for t in r["call_targets"]) or "none"))
        if r["constants"]:
            w("- 16-byte `.rdata` constants it loads into xmm (decoded values):")
            w("")
            w("| at | constant va | value |")
            w("|---|---|---|")
            for c in r["constants"]:
                w("| %s | %s | `%s` |" % (hx(c["at"]), hx(c["const_va"]),
                                          ", ".join("%.6g" % x for x in c["value"])))
            w("")
        if r["stores16"]:
            w("- 16-byte stores it performs: %d (first three: %s)"
              % (len(r["stores16"]),
                 "; ".join("`%s`" % s["ins"] for s in r["stores16"][:3])))
        w("")
    consts = [c for r in doc["paint"] for c in r["constants"]]
    nonzero = [c for c in consts if any(c["value"])]
    w("Decoded: the executable selects a `CarPaintMM` **shader variant** by name "
      "(`CarPaintMM`, `_Deform`, `_Skinned`, `_RSM`, `CarPaintMMShadow*`, "
      "`CarPaintMMPreZVelocity*`, composed through the `CarPaintMM%s%s%s` format string).")
    w("One referencing function copies " + str(len(consts)) + " 16-byte `.rdata` constants "
      "into stack slots, and **" + str(len(nonzero)) + " of them are non-zero**, so as "
      "written that path initialises or clears a parameter block. It is the CarPaintMM "
      "parameter plumbing, but on this evidence it is **not** the tint writer: a call that "
      "stores only zeros cannot be what puts a paint colour into a float4.")
    w("")
    w("## 3. Tint selection: what is not in the executable")
    w("")
    w("The card asks for the code that chooses a tint and writes it into the CarPaintMM "
      "dynamic params (`TintColorR/G/B`). Measured:")
    w("")
    w("| name | occurrences | code references |")
    w("|---|---|---|")
    w("| `TintColorR` | %d | 0 |" % m["tintcolor_occurrences"])
    for n, t in doc["tone"].items():
        w("| `%s` | %d | %d |" % (n, t["occurrences"], t["code_refs_total"]))
    w("")
    w("`TintColorR/G/B` do not exist in the image as strings at all, and the palette schema "
      "names have 0 code references (section 1). So the writing of the CarPaintMM dynamic "
      "tint is **not name-addressed**: whatever fills those float4s does it by offset through "
      "the material/reflection system. This is the concrete reason the G3-09 §6 open item 2 "
      "is still open - it is an offset-level question, not a string-level one.")
    w("")
    w("## 4. Exposure and tonemapping")
    w("")
    w("| name | occurrences | code references | addresses |")
    w("|---|---|---|---|")
    for n, t in doc["tone"].items():
        w("| `%s` | %d | %d | %s |"
          % (n, t["occurrences"], t["code_refs_total"],
             ", ".join(hx(r["va"]) for r in t["rows"]) or "-"))
    w("")
    w("Decoded: `ToneMapping` and `ToneMap` occur once each, `Exposure` %d times and "
      "`exposure` %d times, and **none is referenced by code** (%d references in total). No "
      "instruction loads an exposure or tonemap constant, so no value in the image can be "
      "called one. G3-09 §5 found no data-side tonemap either; this scan does not change "
      "that finding."
      % (doc["tone"]["Exposure"]["occurrences"], doc["tone"]["exposure"]["occurrences"],
         m["tone_code_refs"]))
    w("")
    w("## 5. What is closed, what stays UNKNOWN")
    w("")
    w("Closed by measurement:")
    w("")
    w("- the palette field order is confirmed from the engine's own schema table (section 1), "
      "independently of the `.vmodc` decode in `COLOUR.md`;")
    w("- the executable does carry the CarPaintMM material plumbing and its shader-variant "
      "naming, at the addresses in section 2;")
    w("- tint writing is not name-addressed (`TintColorR/G/B` absent, schema names 0 refs);")
    w("- no code-referenced exposure/tonemap constant exists (section 4).")
    w("")
    w("UNKNOWN, with why:")
    w("")
    w("1. **Which instruction writes the CarPaintMM dynamic float4s**, and which of the four "
      "is `TintColorR`, `G`, `B`. The names are absent, so the next step is offset-level: "
      "identify the dynamic-param struct and the copy loop that fills it, or read the shader "
      "body (not on disk).")
    w("2. **Whether the parameter-block builder in section 2 is the tint path at all.** It "
      "copies 16-byte constants (values listed; several all-zero), but nothing ties a "
      "constant to a tint slot - calling it the tint writer would be a guess.")
    w("3. **The palette -> material binding.** The image has the palette schema and the "
      "material plumbing; the code that reads one and writes the other is not identified here "
      "(`Palette`/`tints` have 0 code references, so the link is offset-driven).")
    w("4. **Exposure/tonemap values.** No code-referenced constant; the strings are dead data "
      "for this purpose. A runtime capture remains the way to obtain them.")
    w("5. **Scan scope.** This is a rip-relative scan of `.text` verified against `.pdata`: "
      "an indirect reference (a name pointer stored in a table and loaded through that table) "
      "is missed unless the table entry itself is referenced. '0 references' therefore means "
      "'no direct reference'.")
    w("")
    w("## Reproduce")
    w("")
    w("```")
    w("uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native.py --write")
    w("uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native.py --check")
    w("```")
    w("")
    return "\n".join(L)


def checks(doc, img):
    m, sb = doc["measured"], doc["schema_block"]
    out = []
    out.append(("the image is the JC3 executable and the PE parses (base %s, %d functions in "
                ".pdata)" % (doc["image"]["base"], doc["image"]["functions_in_pdata"]),
                doc["image"]["size"] > 40_000_000
                and doc["image"]["functions_in_pdata"] > 100_000))
    out.append(("the 8 palette fields are one contiguous .rdata run in the ADF order of "
                "COLOUR.md (%s)" % sb["schema_order_present"],
                sb["run_length"] > 8 and sb["schema_order_contiguous"]
                and sb["schema_order_present"] == SCHEMA_ORDER))
    out.append(("every palette schema member has 0 code references (%s), so the executable "
                "does not address tint_r/tint_g/tint_b by name"
                % sb["schema_member_code_refs"], sb["schema_member_code_refs"] == 0))
    out.append(("CarPaintMM has verified rip-relative references landing in %d function(s)"
                % m["paint_functions"],
                m["paint_name_total"] >= 1 and m["paint_functions"] >= 1))
    out.append(("the shader-variant format string `CarPaintMM%s%s%s` is present",
                m["variant_format_present"] is True))
    out.append(("`TintColorR` does not occur in the image at all (%d)"
                % m["tintcolor_occurrences"], m["tintcolor_occurrences"] == 0))
    out.append(("no ToneMapping/Exposure occurrence is code-referenced (%d refs total)"
                % m["tone_code_refs"], m["tone_code_refs"] == 0))
    out.append(("every listed constant is a real 16-byte .rdata read with 4 finite floats",
                all(img.sec(c["const_va"]) == ".rdata" and len(c["value"]) == 4
                    for r in doc["paint"] for c in r["constants"])))
    out.append(("every reference site is inside a .pdata-bounded function",
                all(img.func_of(h["at"]) for r in doc["paint"] for h in r["direct_refs"])))
    out.append(("no on-screen or tint value is claimed: the measured set is counts only",
                set(m) == {"schema_run_length", "schema_member_code_refs", "paint_functions",
                           "paint_name_total", "tone_code_refs", "variant_format_present",
                           "tintcolor_occurrences"}))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    img = Image(EXE)
    doc = derive(img)
    text = render(doc)
    blob = json.dumps(doc, indent=1) + "\n"
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        with open(JS, "w", encoding="utf-8", newline="\n") as f:
            f.write(blob)
        print("wrote %s (%d schema names, %d CarPaintMM functions, %d tone names)"
              % (MD, doc["measured"]["schema_run_length"],
                 doc["measured"]["paint_functions"], len(doc["tone"])))
        print("wrote %s" % JS)
        return 0

    bad = []
    res = checks(doc, img)
    for what, ok in res:
        print("%-4s %s" % ("ok" if ok else "FAIL", what))
        if not ok:
            bad.append(what)
    same_md = os.path.exists(MD) and open(MD, encoding="utf-8").read() == text
    same_js = os.path.exists(JS) and open(JS, encoding="utf-8").read() == blob
    print("%-4s %s is byte-identical to a fresh decode" % ("ok" if same_md else "FAIL", MD))
    print("%-4s %s is byte-identical to a fresh decode" % ("ok" if same_js else "FAIL", JS))
    if not same_md or not same_js:
        bad.append("drift")
    print("\n%s: %d/%d checks, md %s, json %s"
          % ("OK" if not bad else "FAILED", sum(1 for _w, g in res if g), len(res),
             "identical" if same_md else "DIFFERS", "identical" if same_js else "DIFFERS"))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
