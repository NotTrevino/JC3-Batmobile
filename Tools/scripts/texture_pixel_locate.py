"""texture_pixel_locate.py - do the 8 refused pixel sets exist anywhere in BmAK's cooked packages?

Read-only. Scans **every** `.upk` under BmGame/CookedPCConsole with the project's own reader
(`Tools/scripts/upk_read.py`): the package name table is decompressed (first chunk only, which is
where `upk_read` puts it), so an FName that matches a refused texture is found even when the package
was never grabbed. Packages with a hit are then opened fully to resolve export index, class and the
serialized (mip-stream) size, and to list the materials/parameters that reference the name.

Outputs
  Working/Appearance/PIXEL_LOCATE.md    per-row table: found (package + export index) or not found
  Working/Appearance/pixel_locate.json  the same numbers, with the census of every package scanned

Usage
  python Tools/scripts/texture_pixel_locate.py --write
  python Tools/scripts/texture_pixel_locate.py --check   # recomputes and compares
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read  # noqa: E402
from _lzo1x import lzo1x_decompress  # noqa: E402

PKG_DIR = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT_JSON = os.path.join(ROOT, "Working", "Appearance", "pixel_locate.json")
OUT_MD = os.path.join(ROOT, "Working", "Appearance", "PIXEL_LOCATE.md")

# The rows the appearance ledger refuses for missing pixels (correction 8392 §2.2). One row
# (`Batman_BM3_V2_Lacquered_Underlayer_Ramp`) has pixels in the grab's Startup package and is included
# so its "wrong batch" note can be checked against the game as well.
TARGETS = [
    ("P1", "Batmobile_Micropattern_A", ["micropattern_a", "micropattern"]),
    ("P1", "Batmobile_Micropattern_A_Normal", ["micropattern_a_normal", "micropattern"]),
    ("P1", "Batmobile_Micropattern_B", ["micropattern_b", "micropattern"]),
    ("P1", "Batmobile_Micropattern_C", ["micropattern_c", "micropattern"]),
    ("R2", "Batmobile_V3_Wheel_E", ["wheel_e", "wheel_emissive"]),
    ("D10", "Batman_BM3_V2_Lacquered_Underlayer_Ramp", ["underlayer_ramp", "lacquered_underlayer"]),
    ("D10", "Batmobile_V3_Body_ColourRamp", ["body_colourramp", "colourramp", "colorramp"]),
    ("D5", "Aniso_ramp_Lacquered", ["aniso_ramp", "anisoi_ramp", "aniso"]),
]
TEX_CLASSES = {"Texture2D", "Texture2DMovie", "TextureCube", "TextureRenderTarget2D"}


def _fstr(buf, o):
    n = struct.unpack_from("<i", buf, o)[0]
    if n == 0:
        return "", o + 4
    if n > 0:
        return buf[o + 4:o + 4 + n].rstrip(b"\0").decode("latin-1"), o + 4 + n
    m = -n
    return buf[o + 4:o + 4 + 2 * m].decode("utf-16-le").rstrip("\0"), o + 4 + 2 * m


def header_fields(raw):
    version, licensee = struct.unpack_from("<HH", raw, 4)
    header_size = struct.unpack_from("<i", raw, 8)[0]
    _, o = _fstr(raw, 12)
    o += 4
    (name_count, name_offset, export_count, export_offset,
     import_count, import_offset) = struct.unpack_from("<6i", raw, o)
    return {"version": version, "licensee": licensee, "header_size": header_size,
            "name_count": name_count, "name_offset": name_offset,
            "export_count": export_count, "import_count": import_count}


def first_chunk(raw, start):
    """Decompress chunk 1 only: the logical image starts at name_offset and the names live there."""
    q = raw.find(upk_read.PKG_TAG, start)
    if q < 0:
        raise upk_read.UpkError("no chunk tag")
    block, csize, usize = struct.unpack_from("<III", raw, q + 4)
    p = q + 16
    out = bytearray()
    total = 0
    while total < usize:
        bc, bu = struct.unpack_from("<II", raw, p)
        p += 8
        blob = raw[p:p + bc]
        try:
            part = zlib.decompress(blob)
        except zlib.error:
            part = lzo1x_decompress(blob)
        if len(part) != bu:
            raise upk_read.UpkError("chunk sub-block mismatch")
        out += part
        p += bc
        total += bu
    return bytes(out)


def scan_names(path):
    """[(name, index)] from the package name table, or raise."""
    raw = open(path, "rb").read()
    h = header_fields(raw)
    body = first_chunk(raw, h["name_offset"])
    names, o = [], 0
    for _ in range(h["name_count"]):
        s, o = _fstr(body, o)
        o += 8
        names.append(s)
    return names, h


def deep(pkg_path, needles):
    """Resolve export hits and the referring materials/parameters in a package that matched."""
    p = upk_read.Package(pkg_path)
    rows = []
    for i, e in enumerate(p.exports, 1):
        cls = p.class_name(e["class_index"])
        low = e["name"].lower()
        if any(n in low for n in needles):
            rows.append({"export": i, "name": e["name"], "class": cls, "bytes": e["size"]})
    for e in p.exports:
        cls = p.class_name(e["class_index"])
        if cls and ("Material" in cls or "Texture" in cls):
            low = e["name"].lower()
            if any(n in low for n in needles) and not any(r["export"] and r["name"] == e["name"] for r in rows):
                rows.append({"export": p.exports.index(e) + 1, "name": e["name"], "class": cls,
                             "bytes": e["size"]})
    return rows


def census():
    files = []
    for dirpath, _dirs, fns in os.walk(PKG_DIR):
        for fn in fns:
            if fn.lower().endswith(".upk"):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    return files


def build():
    files = census()
    per_row = {t[1]: {"rule": t[0], "needles": t[2], "packages": [], "errors": 0} for t in TARGETS}
    scanned = 0
    for path in files:
        try:
            names, _h = scan_names(path)
        except Exception:
            for r in per_row.values():
                r["errors"] += 1
            continue
        scanned += 1
        if scanned % 100 == 0:
            print(f"[scan] {scanned}/{len(files)} packages", flush=True)
        low = [n.lower() for n in names]
        for tex, row in per_row.items():
            hit = next((n for n in low if any(nd in n for nd in row["needles"])), None)
            if hit is None:
                continue
            rel = os.path.relpath(path, PKG_DIR).replace("\\", "/")
            if any(p["package"] == rel for p in row["packages"]):
                continue
            entry = {"package": rel, "matched_name": hit, "exports": [], "deep_error": None}
            try:
                entry["exports"] = deep(path, row["needles"])
            except Exception as exc:
                entry["deep_error"] = f"{type(exc).__name__}: {exc}"
            row["packages"].append(entry)
    return {
        "schema": 1,
        "tool": "Tools/scripts/texture_pixel_locate.py",
        "package_dir": PKG_DIR,
        "packages_total": len(files),
        "packages_scanned": scanned,
        "rows": per_row,
        "found": {k: bool(v["packages"]) for k, v in per_row.items()},
        "found_texture2d": {k: any(e["class"] in TEX_CLASSES
                                    for p in v["packages"] for e in p["exports"])
                            for k, v in per_row.items()},
    }


def md(m):
    out = ["# PIXEL_LOCATE - do the refused pixel sets exist in BmAK?", "",
           f"Package root: `{m['package_dir']}`  ",
           f"Packages: **{m['packages_total']}** `.upk`, name table read on **{m['packages_scanned']}** "
           f"({m['type_descriptors_total'] if 'type_descriptors_total' in m else m['packages_total'] - 0}) "
           "after the first-chunk decompress.", "",
           "| rule | texture | found? | package | export | class | bytes |",
           "|---|---|---|---|---|---|---|"]
    for tex, row in m["rows"].items():
        if not row["packages"]:
            out.append(f"| {row['rule']} | `{tex}` | **not found** | - | - | - | - |")
            continue
        first = True
        for p in row["packages"]:
            exps = p["exports"] or [{"export": "-", "class": p.get("deep_error") or "-",
                                     "bytes": "-"}]
            for e in exps:
                out.append(f"| {row['rule'] if first else ''} | {('`'+tex+'`') if first else ''} | "
                           f"{'**found**' if first else ''} | `{p['package']}` | {e.get('export','-')} | "
                           f"{e.get('class') or '-'} | {e.get('bytes','-')} |")
                first = False
    out += ["", "## Not found - every pattern tried", ""]
    for tex, row in m["rows"].items():
        if row["packages"]:
            continue
        pats = ", ".join(f"`{p}`" for p in row["needles"])
        out.append(f"- `{tex}` ({row['rule']}): patterns {pats} - 0 packages of {m['packages_scanned']} "
                   f"carry a matching FName ({row['errors']} packages unreadable).")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("pass --write or --check")
    m = build()
    if a.write:
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(m, f, indent=1)
            f.write("\n")
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md(m))
        print(f"wrote {OUT_MD}")
        print(f"packages {m['packages_scanned']}/{m['packages_total']}; "
              f"found {sum(m['found'].values())}/{len(m['rows'])} rows")
        for k, v in m["found"].items():
            print(f"  {'FOUND' if v else 'absent'} {k}")
        return 0
    old = json.load(open(OUT_JSON, encoding="utf-8"))
    bad = []
    if old["packages_total"] != m["packages_total"]:
        bad.append("package count changed")
    if old["found"] != m["found"]:
        bad.append(f"found map changed: {old['found']} -> {m['found']}")
    for k in old["rows"]:
        if [p["package"] for p in old["rows"][k]["packages"]] != [p["package"] for p in m["rows"][k]["packages"]]:
            bad.append(f"package list changed for {k}")
    if bad:
        print("FAIL")
        for b in bad:
            print(" -", b)
        return 1
    print(f"PASS: {m['packages_scanned']}/{m['packages_total']} packages re-read, "
          f"{sum(m['found'].values())}/{len(m['rows'])} rows reproduce identically")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
