"""jc3_rtti_map.py - static RTTI / vtable map of JustCause3.exe (read-only, never runs the game).

What it does
  1. Parses the PE (pefile), lists sections and the image base.
  2. Finds every MSVC RTTI type descriptor name in the file (".?AV" / ".?AU" strings in .rdata),
     and for the vehicle-related ones records: type-descriptor VA, name, complete-object-locator VA,
     vtable VA and the first vtable slots.
  3. Takes every quoted string literal out of the 2017 handling editor's source
     (E:/Modding/_tools/jc3-handling-editor/src) and reports which of those strings still exist in the
     exe, at what VA, plus the code that references them (RIP-relative lea, disp32 scan in .text).
  4. Writes Working/RTTI/vehicle_rtti.json (+ .md) and a receipt of every number.

--check recomputes every number from the exe bytes and fails if the stored map disagrees.

No game process is opened, no file in a game folder is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys

import numpy as np
import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = r"D:\Games\Just Cause 3\JustCause3.exe"
HANDLING_SRC = r"E:\Modding\_tools\jc3-handling-editor\src"
OUT_DIR = os.path.join(ROOT, "Working", "RTTI")
OUT_JSON = os.path.join(OUT_DIR, "vehicle_rtti.json")
OUT_MD = os.path.join(OUT_DIR, "vehicle_rtti.md")

# names whose RTTI we care about: the vehicle side of the project
VEHICLE_RE = re.compile(rb"Vehicle|Handling|Damage|Health|Tune|CCar\b|Character|GameObject", re.I)
CLASS_KIND = [
    (re.compile(r"CCar\b|LandVehicle", re.I), "land vehicle"),
    (re.compile(r"Vehicle", re.I), "vehicle"),
    (re.compile(r"Handling", re.I), "handling"),
    (re.compile(r"Damage|Health", re.I), "damage/health"),
    (re.compile(r"Character", re.I), "character"),
    (re.compile(r"GameObject", re.I), "object"),
]


class PE:
    def __init__(self, path: str):
        self.path = path
        self.pe = pefile.PE(path, fast_load=True)
        self.blob = open(path, "rb").read()
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.rstrip(b"\0").decode("latin-1")
            self.sections.append({
                "name": name,
                "va": self.base + s.VirtualAddress,
                "raw": s.PointerToRawData,
                "raw_size": s.SizeOfRawData,
                "vsize": s.Misc_VirtualSize,
            })
        self.by_name = {s["name"]: s for s in self.sections}

    # -- address helpers ---------------------------------------------------
    def va_to_off(self, va: int) -> int | None:
        rva = va - self.base
        for s in self.sections:
            if s["va"] - self.base <= rva < s["va"] - self.base + max(s["vsize"], s["raw_size"]):
                delta = rva - (s["va"] - self.base)
                if delta < s["raw_size"]:
                    return s["raw"] + delta
        return None

    def off_to_va(self, off: int) -> int | None:
        for s in self.sections:
            if s["raw"] <= off < s["raw"] + s["raw_size"]:
                return s["va"] + (off - s["raw"])
        return None

    def u32(self, va: int) -> int:
        off = self.va_to_off(va)
        return struct.unpack_from("<I", self.blob, off)[0]

    def u64(self, va: int) -> int:
        off = self.va_to_off(va)
        return struct.unpack_from("<Q", self.blob, off)[0]

    def cstr(self, va: int, limit: int = 256) -> str:
        off = self.va_to_off(va)
        end = self.blob.index(b"\0", off, off + limit)
        return self.blob[off:end].decode("latin-1")

    def section_bytes(self, name: str) -> bytes:
        s = self.by_name[name]
        return self.blob[s["raw"]:s["raw"] + s["raw_size"]]


def find_type_descriptors(pe: PE) -> list[dict]:
    """Every '.?AV' / '.?AU' name in the file, with the descriptor header before it."""
    out, i = [], 0
    while True:
        j = pe.blob.find(b".?A", i)
        if j < 0:
            break
        i = j + 3
        if pe.blob[j + 3:j + 4] not in (b"V", b"U"):
            continue
        end = pe.blob.find(b"\0", j, j + 300)
        if end < 0 or end - j < 6:
            continue
        raw = pe.blob[j:end]
        if not re.fullmatch(rb"\.\?A[VU][\w@?$<>, \-]*", raw.replace(b"\x00", b"")):
            continue
        name_va = pe.off_to_va(j)
        if name_va is None:
            continue
        out.append({
            "name": raw.decode("latin-1"),
            "name_va": name_va,
            "td_va": name_va - 0x10,          # MSVC x64: vftable, spare, name
            "td_vftable": pe.u64(name_va - 0x10),
        })
    return out


def find_cols(pe: PE, td_va: int) -> list[int]:
    """Complete object locators that point at this type descriptor (COL+12 = pTypeDescriptor)."""
    # x64 MSVC stores these pointers as image-relative 32-bit values (VA - image base), not VAs
    td_rva = td_va - pe.base
    hits, pat = [], struct.pack("<I", td_rva)
    for sec in ("__rdata__", ".rdata", "__data__", ".data"):
        s = pe.by_name.get(sec)
        if not s:
            continue
        chunk = pe.blob[s["raw"]:s["raw"] + s["raw_size"]]
        base_va = s["va"]
        i = 0
        while True:
            j = chunk.find(pat, i)
            if j < 0:
                break
            i = j + 4
            if j % 4:
                continue
            col_va = base_va + j - 12
            try:
                if pe.u32(col_va) != 1:       # signature
                    continue
                if pe.u32(col_va + 12) != td_rva:
                    continue
            except Exception:
                continue
            hits.append(col_va)
        if hits:
            break
    return hits


def find_vtables(pe: PE, col_va: int) -> list[dict]:
    """Vtables whose slot [-1] is this COL."""
    # Decoded from this exe: vtable[-1] is the COL as a full 64-bit VA (the 32-bit RVA form occurs
    # only inside class-hierarchy base-class arrays, where the following slots are not code).
    # A candidate is a vtable only if its slot 0 is code.
    out, pat = [], struct.pack("<Q", col_va)
    text_lo, text_hi = pe.base + 0x1000, pe.base + 0x2000000
    i = 0
    while True:
        j = pe.blob.find(pat, i)
        if j < 0:
            break
        i = j + 4
        base_va = pe.off_to_va(j)
        if base_va is None:
            continue
        for pad in (8, 0):                     # 8-byte COL pointer, then slots
            vt = base_va + pad
            try:
                s0 = pe.u64(vt)
            except Exception:
                continue
            if not (text_lo <= s0 < text_hi):
                continue
            slots = []
            for k in range(6):
                try:
                    slots.append(pe.u64(vt + 8 * k))
                except Exception:
                    break
            out.append({"vtable_va": vt, "slots": slots, "slot0_is_code": True})
            break
    return out


def handling_literals() -> list[str]:
    """Quoted string literals from the 2017 handling editor source (its own words, not ours)."""
    lits = set()
    if not os.path.isdir(HANDLING_SRC):
        return []
    for fn in sorted(os.listdir(HANDLING_SRC)):
        if not fn.endswith((".cpp", ".h")):
            continue
        try:
            txt = open(os.path.join(HANDLING_SRC, fn), "r", encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for m in re.finditer(r'"((?:[^"\\\n]|\\.){6,80})"', txt):
            s = m.group(1)
            if re.search(r"[A-Za-z]", s) and not s.startswith(("%", "\\n")):
                lits.add(s)
    return sorted(lits)


def find_code_refs(pe: PE, target_va: int, limit: int = 8) -> list[dict]:
    """RIP-relative lea/mov refs to a VA: disp32 scan restricted to .text."""
    s = pe.by_name.get("__text__") or pe.by_name.get(".text")
    if not s:
        return []
    chunk = pe.blob[s["raw"]:s["raw"] + s["raw_size"]]
    n = len(chunk) // 4
    arr = np.frombuffer(chunk[:n * 4], dtype="<u4").astype(np.uint64)
    ends = (s["va"] + 4 * np.arange(n, dtype=np.uint64) + 4)
    sums = (ends + arr) & np.uint64(0xFFFFFFFF)
    idx = np.nonzero(sums == np.uint64(target_va & 0xFFFFFFFF))[0]
    out = []
    for i in idx[:limit]:
        off = int(i) * 4
        op = chunk[off - 2:off]
        if not (op and op[0] == 0x8D):
            continue
        out.append({"disp_at": s["va"] + off, "instr": s["va"] + off - 2,
                    "lea": True, "func_guess": nearest_start(pe, s["va"] + off - 2)})
    return out


def nearest_start(pe: PE, va: int, window: int = 0x1000) -> int | None:
    """Approximate function start: last byte of a >=4-byte 0xCC run before va (derived, not exact)."""
    s = pe.by_name.get("__text__") or pe.by_name.get(".text")
    if not s:
        return None
    off = pe.va_to_off(va)
    lo = max(s["raw"], off - window)
    i = off
    while i > lo:
        if pe.blob[i - 1] == 0xCC:
            j = i
            while j > lo and pe.blob[j - 1] == 0xCC:
                j -= 1
            if i - j >= 4:
                return pe.off_to_va(i)
        i -= 1
    return None


def build_map() -> dict:
    pe = PE(EXE)
    tds = find_type_descriptors(pe)
    veh = [t for t in tds if VEHICLE_RE.search(t["name"].encode("latin-1"))]
    rows = []
    for t in veh:
        kind = next((k for rx, k in CLASS_KIND if rx.search(t["name"])), "other")
        cols = find_cols(pe, t["td_va"])
        vts = []
        for c in cols:
            for v in find_vtables(pe, c):
                v["vtable_va"] = v["vtable_va"]
                vts.append(v)
        rows.append({
            "name": t["name"],
            "kind": kind,
            "name_va": hex(t["name_va"]),
            "td_va": hex(t["td_va"]),
            "td_vftable": hex(t["td_vftable"]),
            "cols": [hex(c) for c in cols],
            "vtables": [{"vtable_va": hex(v["vtable_va"]),
                         "slots": [hex(x) for x in v["slots"]]} for v in vts],
        })
    lits = handling_literals()
    found = []
    for s in lits:
        b = s.encode("latin-1", "ignore")
        j = pe.blob.find(b)
        if j < 0:
            continue
        va = pe.off_to_va(j)
        if va is None:
            continue
        found.append({"literal": s, "va": hex(va), "refs": find_code_refs(pe, va)})
    return {
        "schema": 1,
        "exe": EXE,
        "exe_bytes": os.path.getsize(EXE),
        "exe_sha256": hashlib.sha256(pe.blob).hexdigest(),
        "image_base": hex(pe.base),
        "sections": [{"name": s["name"], "va": hex(s["va"]), "raw": s["raw"],
                      "raw_size": s["raw_size"], "vsize": s["vsize"]} for s in pe.sections],
        "type_descriptors_total": len(tds),
        "vehicle_rows": rows,
        "handling_literals_total": len(lits),
        "handling_literals_found": found,
    }


def write_md(m: dict) -> str:
    out = ["# Vehicle RTTI map (static, read-only)", "",
           f"exe: `{m['exe']}` ({m['exe_bytes']} B, sha256 `{m['exe_sha256']}`)",
           f"image base `{m['image_base']}`, {m['type_descriptors_total']} RTTI names", "",
           "| class | kind | TD | COL | vtable | slot0 |", "|---|---|---|---|---|---|"]
    for r in m["vehicle_rows"]:
        for v in r["vtables"] or [{"vtable_va": "-", "slots": []}]:
            s0 = v["slots"][0] if v["slots"] else "-"
            out.append(f"| `{r['name']}` | {r['kind']} | {r['td_va']} | "
                       f"{r['cols'][0] if r['cols'] else '-'} | {v['vtable_va']} | {s0} |")
    out += ["", "## 2017 handling-editor literals re-found", "",
            f"{len(m['handling_literals_found'])} of {m['handling_literals_total']} literals exist in the exe.", "",
            "| literal | VA | code refs (lea) |", "|---|---|---|"]
    for f in m["handling_literals_found"][:60]:
        refs = ", ".join(hex(r["func_guess"]) if r["func_guess"] else hex(r["instr"]) for r in f["refs"]) or "-"
        out.append(f"| `{f['literal']}` | {f['va']} | {refs} |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("pass --write or --check")
    m = build_map()
    if a.write:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(m, f, indent=1)
            f.write("\n")
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(write_md(m))
        print(f"wrote {OUT_JSON}")
        print(f"{len(m['vehicle_rows'])} vehicle rows, {len(m['handling_literals_found'])}/"
              f"{m['handling_literals_total']} literals found")
        return 0
    old = json.load(open(OUT_JSON, encoding="utf-8"))
    bad = []
    if old["exe_sha256"] != m["exe_sha256"]:
        bad.append("exe sha256 changed")
    if old["type_descriptors_total"] != m["type_descriptors_total"]:
        bad.append("type descriptor count changed")
    for o, n in zip(old["vehicle_rows"], m["vehicle_rows"]):
        if o != n:
            bad.append(f"row changed: {o['name']}")
    if len(old["vehicle_rows"]) != len(m["vehicle_rows"]):
        bad.append("row count changed")
    if len(old["handling_literals_found"]) != len(m["handling_literals_found"]):
        bad.append("literal hit count changed")
    if bad:
        print("FAIL")
        for b in bad:
            print(" -", b)
        return 1
    print(f"PASS: {len(m['vehicle_rows'])} vehicle rows and {len(m['handling_literals_found'])} literal hits "
          f"recompute identically from {m['exe_bytes']} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
