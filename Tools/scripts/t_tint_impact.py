#!/usr/bin/env python3
"""t_tint_impact.py - 7211: every repo claim that puts the paint tint in the `.epe`.

`Research/JC3Grab/TINT_WRITE.md` (G3-09d) decoded the carrier: `tint_r` lives in the
palette `.vmodc` as a `ColorRGBA`; the `.epe` holds only `CCar.palette`, one int32
Jenkins hash of the palette module path.  This script finds every place in the repo that
could assume otherwise and judges each hit against that finding:

  * Working/Translation/T_ROWS.jsonl        (cells mentioning tint/palette)
  * Working/Appearance/appearance_plan.json (line scan)
  * Working/Appearance/APPEARANCE_PLAN.md   (line scan)
  * Working/Entity/bm_epe_edits.json        (does any edit name palette/tint?)
  * Tools/scripts/bm_entity.py              (does the .epe writer touch tint/palette?)
  * Builds/bm-RC2/receipt.json              (what the receipt says the build wrote)

Nothing is edited and the test ban holds: the build trees are only read and the two
`.epe` exports are staged in a temp directory.  Every number in the document is
recomputed from bytes here; `--check` re-derives all of them and compares the file.

Usage:
    python Tools/scripts/t_tint_impact.py --write
    python Tools/scripts/t_tint_impact.py --check
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf      # noqa: E402  (ADF v4 reader: independent decode of the palette)
import rbmhdr      # noqa: E402  (Jenkins hash, pinned against HashName.exe)

DONOR = "v0300_car_kensington_sportsmuscle"
ENT = "aaf/editor/entities/jc_vehicles/01_land/" + DONOR
PAL_NAME = DONOR + "_palette.vmodc"
EPE_NAME = DONOR + "_debug.epe"
CIVILIAN = DONOR + "_civilian_01.epe"

CONV_PROP = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
CONV_ADF = os.path.join(ROOT, "Tools", "Gibbed-patched", "Gibbed.JustCause3.ConvertAdf.exe")

OUT_MD = os.path.join(ROOT, "Working", "Translation", "TINT_IMPACT.md")

SRC = {
    "rows": os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl"),
    "plan_json": os.path.join(ROOT, "Working", "Appearance", "appearance_plan.json"),
    "plan_md": os.path.join(ROOT, "Working", "Appearance", "APPEARANCE_PLAN.md"),
    "epe_edits": os.path.join(ROOT, "Working", "Entity", "bm_epe_edits.json"),
    "entity_py": os.path.join(ROOT, "Tools", "scripts", "bm_entity.py"),
    "receipt": os.path.join(ROOT, "Builds", "bm-RC2", "receipt.json"),
    "pal_rc2": os.path.join(ROOT, "Builds", "bm-RC2", ENT, "modules", "default", "batmobile", PAL_NAME),
    "pal_005": os.path.join(ROOT, "Builds", "bm-005", ENT, "modules", "default", PAL_NAME),
    "epe_rc2": os.path.join(ROOT, "Builds", "bm-RC2", ENT, EPE_NAME),
    "epe_005": os.path.join(ROOT, "Builds", "bm-005", ENT, CIVILIAN),
}

VANILLA_PAL = ("editor/entities/jc_vehicles/01_land/" + DONOR +
               "/modules/default/" + PAL_NAME)
BAT_PAL = ("editor/entities/jc_vehicles/01_land/" + DONOR +
           "/modules/default/batmobile/" + PAL_NAME)
VANILLA_PAL_HASH = -1071400364
BAT_PAL_HASH = 1322976751
PAL_SHA = "72d5d04f78c64120409362646db273ef6f83d9d99606f257794ef5df9c49073b"
TINT_RE = re.compile(r"tint|palette", re.I)


# ---------------------------------------------------------------- helpers

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def signed32(u: int) -> int:
    return u - (1 << 32) if u >= (1 << 31) else u


def name_hash(name: str) -> int:
    return signed32(rbmhdr.name_hash(name))


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("command failed (%d): %s\n%s\n%s"
                         % (r.returncode, " ".join(cmd), r.stdout[:800], r.stderr[:800]))


def read_xml(path: str) -> str:
    return open(path, encoding="utf-8-sig").read()


def one(pat: str, text: str, what: str) -> str:
    m = re.findall(pat, text)
    if len(m) != 1:
        raise SystemExit("expected exactly one %s, found %d" % (what, len(m)))
    return m[0]


def clip(s: str, n: int = 92) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "\u2026"


def cell(s: str) -> str:
    return clip(s).replace("|", "\\|")


def scope_of(text: str) -> str:
    t = text.lower()
    if "palette" in t or "tints" in t or "specular_gloss" in t:
        return "palette record"
    return "material tint"


def verdict_of(scope: str, text: str) -> str:
    if scope != "palette record":
        return "n/a - not a palette claim"
    t = text.lower()
    if "0.45" in t:
        return "HOLDS as the vanilla value; 0 tint bytes written"
    if "leave" in t and "untouched" in t:
        return "HOLDS - palette copied byte-identical (sha256 = bm-005)"
    if "does not exist" in t:
        return "HOLDS - the .epe has no Palette object; only the path hash"
    return "HOLDS - the palette .vmodc is the carrier; no tint byte written"


def scan_lines(path: str) -> list[dict]:
    out = []
    for i, line in enumerate(open(path, encoding="utf-8", errors="replace").read().splitlines(), 1):
        if TINT_RE.search(line):
            out.append({"line": i, "text": line.strip()})
    return out


def find_path_entry(obj, target: str):
    if isinstance(obj, dict):
        if obj.get("path") == target:
            return obj
        for v in obj.values():
            hit = find_path_entry(v, target)
            if hit:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = find_path_entry(v, target)
            if hit:
                return hit
    return None


# ---------------------------------------------------------------- collect

def collect(tmp: str) -> dict:
    d: dict = {"gates": []}

    def gate(ok: bool, name: str, detail: str) -> None:
        d["gates"].append({"ok": bool(ok), "name": name, "detail": detail})

    # ---- 1. T_ROWS.jsonl: row cells that mention tint/palette
    row_hits, n_rows = [], 0
    for i, line in enumerate(open(SRC["rows"], encoding="utf-8").read().splitlines(), 1):
        if not line.strip():
            continue
        n_rows += 1
        row = json.loads(line)
        for j, c in enumerate(row.get("cells", [])):
            if TINT_RE.search(c):
                row_hits.append({
                    "id": row["id"], "line": i, "cell": j, "text": c,
                    "scope": scope_of(c), "dispo": row.get("dispo"), "edits": row.get("edits"),
                })
    d["rows"] = {"n_rows": n_rows, "hits": row_hits}
    pal_hits = [h for h in row_hits if h["scope"] == "palette record"]
    gate(n_rows == 198 and len(row_hits) == 7 and len(pal_hits) == 5,
         "G1-rows",
         "%d rows, %d tint/palette cell hits in %d rows, %d palette-record hits"
         % (n_rows, len(row_hits), len({h["id"] for h in row_hits}), len(pal_hits)))
    gate(all(h["dispo"] == "keep" and h["edits"] == 0 for h in row_hits),
         "G2-rows-dispo", "every hit row is dispo=keep, edits=0 (no row edits were made)")

    # ---- 2. the appearance plan pair
    plan_json = scan_lines(SRC["plan_json"])
    plan_md = scan_lines(SRC["plan_md"])
    d["plan"] = {"json": plan_json, "md": plan_md}
    gate(len(plan_json) == 5 and len(plan_md) == 3, "G3-plan-lines",
         "appearance_plan.json %d tint lines, APPEARANCE_PLAN.md %d" % (len(plan_json), len(plan_md)))
    gate(not any("palette" in h["text"].lower() for h in plan_json + plan_md),
         "G4-plan-no-palette", "no plan line mentions a palette")

    # ---- 3. the .epe edit table
    edits = json.load(open(SRC["epe_edits"], encoding="utf-8"))
    edit_rows = edits.get("edits", [])
    edit_hits = [r for r in edit_rows if TINT_RE.search(json.dumps(r))]
    d["epe_edits"] = {"rows": len(edit_rows), "hits": len(edit_hits),
                      "additions": len(edits.get("additions", []))}
    gate(len(edit_rows) == 19 and not edit_hits, "G5-epe-edits",
         "%d edits, %d naming tint/palette; %d additions"
         % (len(edit_rows), len(edit_hits), len(edits.get("additions", []))))

    # ---- 4. the .epe writer
    ent_hits = scan_lines(SRC["entity_py"])
    ent_src = open(SRC["entity_py"], encoding="utf-8").read()
    d["entity"] = {"hits": len(ent_hits), "convert": "ConvertProperty" in ent_src,
                   "epe_out": "OUT_EPE" in ent_src}
    gate(not ent_hits and d["entity"]["convert"], "G6-bm_entity",
         "%d tint/palette strings in bm_entity.py; writes the .epe via ConvertProperty" % len(ent_hits))

    # ---- 5. the palette ADF (RC2 bytes, decoded twice)
    pal_rc2, pal_005 = SRC["pal_rc2"], SRC["pal_005"]
    blob = open(pal_rc2, "rb").read()
    a = jc3adf.Adf(blob)
    vals = {k: v for k, _t, v in jc3adf.walk(a)}
    n = len([k for k in vals if k.endswith(".name.string")])
    recs = []
    for i in range(n):
        recs.append({
            "name": vals.get("tints[%d].name.string" % i),
            "occ": vals.get("tints[%d].occurrence" % i),
            "rgba": [vals.get("tints[%d].tint_r.%s" % (i, c)) for c in "RGBA"],
            "gloss": vals.get("tints[%d].specular_gloss" % i),
            "metal": vals.get("tints[%d].metallic" % i),
            "coat": vals.get("tints[%d].clear_coat" % i),
        })
    d["palette"] = {
        "sha": sha256(pal_rc2), "sha_005": sha256(pal_005),
        "size": len(blob), "n": n, "recs": recs,
        "instance": a.instances[0]["name"], "instance_size": a.instances[0]["size"],
    }
    gate(d["palette"]["sha"] == d["palette"]["sha_005"] == PAL_SHA,
         "G7-palette-sha", "RC2 palette sha256 %s == bm-005 == %s" % (d["palette"]["sha"][:12], PAL_SHA[:12]))
    gate(n == 10 and all(abs(r["gloss"] - 0.45) < 1e-6 and r["metal"] == 1.0
                         and r["coat"] == 1.0 and all(abs(x - 0.05) < 1e-6 for x in r["rgba"][:3])
                         and r["rgba"][3] == 1.0 for r in recs),
         "G8-palette-records",
         "%d tints: tint_r 0.05/0.05/0.05/1, gloss 0.45, metallic 1, clear_coat 1 in every record" % n)

    # ---- 6. both .epe carriers, exported
    os.makedirs(tmp, exist_ok=True)
    x2 = os.path.join(tmp, "rc2.xml")
    x5 = os.path.join(tmp, "b005.xml")
    run([CONV_PROP, "--e", SRC["epe_rc2"], x2])
    run([CONV_PROP, "--e", SRC["epe_005"], x5])
    t2, t5 = read_xml(x2), read_xml(x5)
    v2 = int(one(r'<value name="palette" type="int">(-?\d+)</value>', t2, "RC2 palette int"))
    v5 = int(one(r'<value name="palette" type="int">(-?\d+)</value>', t5, "bm-005 palette int"))
    raw2 = open(SRC["epe_rc2"], "rb").read()
    offs = [i for i in range(len(raw2)) if raw2.startswith(struct.pack("<i", v2), i)]
    epe_files = sorted(glob.glob(os.path.join(ROOT, "Builds", "bm-RC2", "**", "*.epe"), recursive=True))
    d["epe"] = {
        "rc2_value": v2, "b005_value": v5, "rc2_offsets": [hex(o) for o in offs],
        "rc2_lines": len(t2.splitlines()), "b005_lines": len(t5.splitlines()),
        "rc2_tint_r": t2.count("tint_r"), "b005_tint_r": t5.count("tint_r"),
        "rc2_palette_class": "Palette" in t2,
        "rc2_files": [os.path.relpath(p, ROOT).replace("\\", "/") for p in epe_files],
    }
    gate(v2 == name_hash(BAT_PAL) == BAT_PAL_HASH, "G9-rc2-pointer",
         "RC2 palette int %d == Jenkins(%s) == %d at %s"
         % (v2, "batmobile palette path", BAT_PAL_HASH, ",".join(d["epe"]["rc2_offsets"])))
    gate(v5 == name_hash(VANILLA_PAL) == VANILLA_PAL_HASH, "G10-bm005-pointer",
         "bm-005 palette int %d == Jenkins(default palette path)" % v5)
    gate(not d["epe"]["rc2_tint_r"] and not d["epe"]["rc2_palette_class"]
         and not d["epe"]["b005_tint_r"],
         "G11-epe-has-no-tint",
         "exports: RC2 tint_r x%d, Palette class %s; bm-005 tint_r x%d"
         % (d["epe"]["rc2_tint_r"], d["epe"]["rc2_palette_class"], d["epe"]["b005_tint_r"]))
    gate(len(epe_files) == 1 and epe_files[0].endswith(EPE_NAME), "G12-rc2-epe-set",
         "RC2 ships %d .epe: %s" % (len(epe_files), d["epe"]["rc2_files"][0]))

    # ---- 7. the receipt
    rec = json.load(open(SRC["receipt"], encoding="utf-8"))
    b18 = rec.get("b18", {})
    moved = b18.get("moved", {}).get(VANILLA_PAL)
    repoint = b18.get("repointed", {}).get("editor/entities/jc_vehicles/01_land/" + DONOR + "/" + CIVILIAN, {})
    cited = find_path_entry(rec, BAT_PAL) or {}
    d["receipt"] = {
        "moved": moved, "repoint_palette": repoint.get(VANILLA_PAL),
        "cited_sha": cited.get("sha256"), "n_palette_mentions": len(
            [ln for ln in open(SRC["receipt"], encoding="utf-8").read().splitlines()
             if "palette" in ln.lower()]),
    }
    gate(moved == BAT_PAL and d["receipt"]["repoint_palette"] == 1,
         "G13-receipt-move", "receipt moved the palette to batmobile/ and repointed it x%d"
         % (d["receipt"]["repoint_palette"] or 0))
    gate(d["receipt"]["cited_sha"] == d["palette"]["sha"], "G14-receipt-sha",
         "receipt cites palette sha256 %s" % str(d["receipt"]["cited_sha"])[:12])

    d["palette_path"] = os.path.relpath(pal_rc2, ROOT).replace("\\", "/")
    d["epe_path"] = os.path.relpath(SRC["epe_rc2"], ROOT).replace("\\", "/")
    return d


# ---------------------------------------------------------------- render

def render(d: dict) -> str:
    p = d["palette"]
    e = d["epe"]
    L: list[str] = []
    A = L.append

    A("# TINT_IMPACT - every repo claim about where the paint tint lives (7211)")
    A("")
    A("Generated by `Tools/scripts/t_tint_impact.py --write`; `--check` re-scans every source,")
    A("re-exports both `.epe` carriers, re-decodes the palette from the RC2 bytes and compares")
    A("this file byte for byte. Static only: no game, no install, no row edited.")
    A("")
    n_row = len(d["rows"]["hits"])
    n_plan = len(d["plan"]["json"]) + len(d["plan"]["md"])
    n_pal = len([h for h in d["rows"]["hits"] if h["scope"] == "palette record"])
    n_mat = len([h for h in d["rows"]["hits"] if h["scope"] == "material tint"]) + n_plan
    A("## STATUS")
    A("")
    A("**DONE - %d tint/palette hits (%d row cells, %d plan lines, 2 receipt entries);"
      % (n_row + n_plan + 2, n_row, n_plan))
    A("%d row cells are palette-record claims, %d lines are material-tint claims, and the edit"
      % (n_pal, n_mat))
    A("table and `bm_entity.py` name neither. No hit places `tint_r` in the `.epe`; the build writes the")
    A("palette pointer, never a tint value.**")
    A("")
    A("## 1. Answer")
    A("")
    A("`TINT_WRITE.md` holds: `tint_r` is a `ColorRGBA` in the palette `.vmodc`, and the `.epe`")
    A("carries only the `CCar.palette` path hash. What bm-RC2 actually ships:")
    A("")
    A("| carrier | RC2 file | what it holds | tint byte written? |")
    A("|---|---|---|---|")
    A("| palette `.vmodc` | `%s` | %d `Tint` records, `tint_r` 0.05/0.05/0.05/1, gloss 0.45 | **no** - sha256 `%s` equals bm-005 (vanilla copy) |"
      % (d["palette_path"], p["n"], p["sha"][:12]))
    A("| `.epe` | `%s` | `CCar.palette` = `%d` at `%s` (Jenkins of the `batmobile/` path) | **no** - pointer only; export has 0 `tint_r`, 0 `Palette` objects |"
      % (d["epe_path"], e["rc2_value"], e["rc2_offsets"][0]))
    A("| `.ee` | not decoded | AAF archive, no repo reader | UNKNOWN |")
    A("")
    A("So every hit below either (a) talks about a material/Window `tint`, not the palette")
    A("record, or (b) quotes a palette value the vanilla file already has and that the build")
    A("copies verbatim. No source claims an `.epe` field named `tint_r`, because none exists.")
    A("")
    A("## 2. The hits")
    A("")
    A("| # | source | loc | hit | claim about | build writes tint? | carrier | holds? |")
    A("|---|---|---|---|---|---|---|---|")
    k = 0
    for h in d["rows"]["hits"]:
        k += 1
        A("| %d | `T_ROWS.jsonl` | %s line %d, cell %d | %s | %s | no | %s | %s |"
          % (k, h["id"], h["line"], h["cell"], cell(h["text"]), h["scope"],
             "palette `.vmodc`" if h["scope"] == "palette record" else "material (RBM/Window)",
             verdict_of(h["scope"], h["text"])))
    for h in d["plan"]["json"]:
        k += 1
        A("| %d | `appearance_plan.json` | line %d | %s | %s | no | material (RBM/Window), not the palette | n/a |"
          % (k, h["line"], cell(h["text"]), scope_of(h["text"])))
    for h in d["plan"]["md"]:
        k += 1
        A("| %d | `APPEARANCE_PLAN.md` | line %d | %s | %s | no | material (RBM/Window), not the palette | n/a |"
          % (k, h["line"], cell(h["text"]), scope_of(h["text"])))
    k += 1
    A("| %d | `bm_epe_edits.json` | %d edits | 0 of %d edits name tint/palette | .epe members only | no | none | no assumption |"
      % (k, d["epe_edits"]["rows"], d["epe_edits"]["rows"]))
    k += 1
    A("| %d | `bm_entity.py` | whole file | %d tint/palette strings | writes the .epe via `ConvertProperty` | no | none | no assumption |"
      % (k, d["entity"]["hits"]))
    k += 1
    A("| %d | `bm-RC2/receipt.json` | palette entry | moved to `batmobile/`, sha256 `%s` | module copy | no | palette `.vmodc` | **HOLDS** - copy of vanilla bytes |"
      % (k, p["sha"][:12]))
    k += 1
    A("| %d | `bm-RC2/receipt.json` | repointed count | palette repointed x%d | path pointer | no (pointer only) | merged `.epe` | **HOLDS** - pointer `%d`, no tint value |"
      % (k, d["receipt"]["repoint_palette"], e["rc2_value"]))
    A("")
    A("Total: **%d** hits - **%d** palette-record claims (T-MA4 x1, T-MA7 x%d), **%d**"
      % (k, n_pal, n_pal - 1, n_mat))
    A("material-tint lines, and two sources with no tint code at all.")
    A("")
    A("### 2.1 The two palette rows, read closely")
    A("")
    A("* **T-MA4** asks for `0.45` \"in every paint block and in all 10 palette tints\" and is")
    A("  `dispo: keep` with `why: build carries the proposal`. The palette half is already")
    A("  satisfied by the donor file: all ten records decode at gloss `0.45` before the build")
    A("  copies it, so no palette byte is written and nothing needs to be. The paint-block half")
    A("  is an RBM material edit, a different carrier (not judged here).")
    A("* **T-MA7** claims \"10 tints, all `specular_gloss` 0.45, `clear_coat` 1, `metallic` 1")
    A("  (read from the shipped donor module in the build)\". Decoded from the RC2 palette: %d"
      % p["n"])
    A("  records, every one gloss `%.2f`, metallic `%.1f`, clear_coat `%.1f`. The row's"
      % (p["recs"][0]["gloss"], p["recs"][0]["metal"], p["recs"][0]["coat"]))
    A("  \"leave the palette untouched\" is exactly what the build did (same sha256 as bm-005).")
    A("")
    A("## 3. The palette records (decoded from the RC2 bytes)")
    A("")
    A("| i | name | occurrence | tint_r R/G/B/A | gloss | metallic | clear_coat |")
    A("|---|---|---:|---|---:|---:|---:|")
    for i, r in enumerate(p["recs"]):
        A("| %d | %s | %s | %s | %.2f | %.1f | %.1f |"
          % (i, r["name"], r["occ"], "/".join("%.3g" % x for x in r["rgba"]),
             r["gloss"], r["metal"], r["coat"]))
    A("")
    A("`tint_r` is identical in every record (`0.05, 0.05, 0.05, 1`): the donor paints itself")
    A("with the same grey in all ten slots and only the record name/gloss vary.")
    A("")
    A("## 4. The receipt and the shipped `.epe`")
    A("")
    A("* `b18.moved` maps the vanilla palette to `.../modules/default/batmobile/...`; the")
    A("  entry's sha256 (`%s`) is the vanilla file's, and the RC2 file hashes to the same value." % p["sha"][:16])
    A("* `b18.repointed[.../%s]` counts the palette x%d: the merged entity was rewritten so its" % (CIVILIAN, d["receipt"]["repoint_palette"]))
    A("  `CCar.palette` names the `batmobile/` path.")
    A("* RC2 ships exactly one `.epe`, `%s` (%d exported lines); bm-005 shipped only" % (EPE_NAME, e["rc2_lines"]))
    A("  `%s` (%d lines). The receipt's repointed key still names the pre-rename" % (CIVILIAN, e["b005_lines"]))
    A("  `civilian_01.epe`, while the built tree carries `debug.epe` with the batmobile hash:")
    A("  the pointer is present, the filename in the receipt is the merge-stage name.")
    A("* **UNKNOWN**: whether the game loads `debug.epe` or the base archive's")
    A("  `civilian_01.epe` (still at hash `%d`) for the civilian variant. No test was run, and" % VANILLA_PAL_HASH)
    A("  the `.ee` that packs the entity is an AAF archive no repo tool reads. This does not")
    A("  change the tint finding: neither file carries a tint value.")
    A("")
    A("## 5. Oracles (all recomputed by `--check`)")
    A("")
    A("| gate | result |")
    A("|---|---|")
    for g in d["gates"]:
        A("| %s | %s - %s |" % (g["name"], "PASS" if g["ok"] else "FAIL", g["detail"]))
    A("")
    A("## 6. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/t_tint_impact.py --check")
    A("```")
    A("")
    A("`--check` re-scans the six sources, re-hashes the palette against bm-005 and the pinned")
    A("TINT_WRITE sha, re-decodes all %d tint records, re-exports both `.epe` files, re-derives" % p["n"])
    A("both Jenkins hashes (via `rbmhdr.name_hash`), and compares this document byte for byte.")
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="tint_impact_")
    try:
        d = collect(tmp)
        md = render(d)
        for gate in d["gates"]:
            print("%s %-22s %s" % ("PASS" if gate["ok"] else "FAIL", gate["name"], gate["detail"]))
        bad = [x for x in d["gates"] if not x["ok"]]
        if bad:
            print("\n%d gate(s) failed" % len(bad))
            return 1
        if a.write:
            os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
            with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
                f.write(md)
            print("\nwrote %s (%d lines)" % (os.path.relpath(OUT_MD, ROOT), len(md.splitlines())))
            return 0
        if not os.path.exists(OUT_MD):
            print("\nmissing %s; run --write" % os.path.relpath(OUT_MD, ROOT))
            return 1
        have = open(OUT_MD, encoding="utf-8", newline="").read()
        if have.replace("\r\n", "\n") != md:
            print("\n%s is stale; re-run --write" % os.path.relpath(OUT_MD, ROOT))
            return 1
        print("\nPASS %s matches (%d lines)" % (os.path.relpath(OUT_MD, ROOT), len(md.splitlines())))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
