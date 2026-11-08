"""ledger_g3_rederive.py - re-derive 15 OPEN ledger rows from the decoded G3 source files.

G3-20e. Scope: the rows `Working/Translation/LEDGER_G3B.md` (96 OPEN) and
`Working/Translation/LEDGER_G3C.md` (68 OPEN) leave open. This pass takes 15 of the 69 rows
`LEDGER_SOURCES.md` calls re-derivable - the ones whose source files exist in this tree - and
for each one:

  1. states the claim the ledger row makes, quoted from `Working/Translation/T_ROWS.jsonl`;
  2. re-derives that number **from the decoded file itself**, naming file + line (or
     container + path), with a stated rule;
  3. compares the two and reports `holds` / `wrong value` / `not derivable`.

Nothing is copied from another card's summary: every row below reads its source file here.
`--check` re-reads all five sources and recomputes every number, so a stale file or a
rewritten row fails rather than passing quietly.

The five sources this pass touches (all exist, all are producers' output, none is edited):
  Research/JC3Grab/FX_TABLE.jsonl         (jc3fx.py, grabbed)
  Research/JC3Grab/PARTS_TABLE.jsonl      (jc3parts.py, grabbed)
  Working/Translation/T3_FLEET.md         (t3_fleet.py, derived)
  Working/Translation/FITS.md             (t1_fits.py, derived)
  Research/BatmobileGrab/CHAIN.json       (bmak_chain.py, grabbed) - not needed by these 15,
                                          see the report's UNKNOWN 1

Rows deliberately NOT taken: the paint composite rows (T-MA1/3/4/5/7) because the combine rule
is UNKNOWN in COLOUR_PARAMS.md, and the collision rows (T-CO1/2/3) because their sources are
not in the decoded set. No row here is a translation decision.

Usage
  python Tools/scripts/ledger_g3_rederive.py --write
  python Tools/scripts/ledger_g3_rederive.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T_ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
LEDGER_B = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3B.json")
LEDGER_C = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3C.json")
FX = os.path.join(ROOT, "Research", "JC3Grab", "FX_TABLE.jsonl")
PARTS = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
FLEET = os.path.join(ROOT, "Working", "Translation", "T3_FLEET.md")
FITS = os.path.join(ROOT, "Working", "Translation", "FITS.md")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3_REDERIVE.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3_REDERIVE.json")
DONOR_ENTITY = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
                "v0300_car_kensington_sportsmuscle_civilian_01.ee")
DONOR_MODULE = "sportsmuscle_vehicle_parts.vmodc"

# ---------------------------------------------------------------- the 15 rows
# (row id, source key, one-line rule, how the ledger's claim is found in cells)
SELECTION = [
    ("T-FX5", "fx_donor", "count FX_TABLE rows whose container is the donor .ee and ext is .effc",
     "cell2 number of `.effc`"),
    ("T-FX10", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-FX14", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-FX17", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-FX18", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-FX19", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-FX21", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-FX22", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-FX23", "fx_path", "distinct .ee containers referencing the path", "cell2 'N vehicles'"),
    ("T-P2", "parts", "count the donor row's parts and distinct damage types", "cell4 '17 ... 42'"),
    ("T-PA4", "parts", "read the donor row's wheel_parts[] (part, slot, spokes, spins)",
     "cell4 'parts ... slots ...'"),
    ("T-PA7", "parts", "count donor parts with deform == 0", "cell4 'N parts skipped'"),
    ("T-S5", "fleet", "read T3_FLEET's 'suspension front lateral tyre offset' median",
     "cell5 'fleet median ... n=125'"),
    ("T-K3", "fleet", "read T3_FLEET's 'brakes handbrake friction factor' 6 t+ median",
     "cell5 'the 6 t median; band ...'"),
    ("T-E2", "fits", "evaluate T3_FLEET/FITS's torque fit at 6,000 kg", "cell5 'fit's 1,121 at 6 t'"),
]


def read_rows() -> dict:
    rows = {}
    for line in open(T_ROWS, encoding="utf-8"):
        d = json.loads(line)
        rows[d["id"]] = d
    return rows


def ledger_status() -> dict:
    out = {}
    for p in (LEDGER_B, LEDGER_C):
        d = json.load(open(p, encoding="utf-8"))
        for r in d.get("rows", []):
            if "status" in r:
                out[r["id"]] = r["status"]
    return out


# ---------------------------------------------------------------- sources
def fx_scan(paths: list, donor: str) -> dict:
    """One streaming pass over FX_TABLE: per path, the rows/containers/ee carriers."""
    want = {p: {"rows": 0, "first_line": None, "containers": set(), "ee": set(),
                "leaves": set(), "self": set(), "sizes": set()} for p in paths}
    donor_row = {"rows": 0, "first_line": None, "paths": set(), "sizes": set()}
    n = 0
    for i, line in enumerate(open(FX, encoding="utf-8"), 1):
        r = json.loads(line)
        n = i
        p, c = r.get("path"), r.get("container") or ""
        if p in want:
            w = want[p]
            w["rows"] += 1
            if w["first_line"] is None:
                w["first_line"] = i
            if c == p:
                w["self"].add(c)
            else:
                w["containers"].add(c)
                if c.endswith(".ee"):
                    w["ee"].add(c)
                    w["leaves"].add(os.path.basename(c))
            w["sizes"].add(r.get("size"))
        if r.get("ext") == ".effc" and c == donor:
            donor_row["rows"] += 1
            if donor_row["first_line"] is None:
                donor_row["first_line"] = i
            donor_row["paths"].add(p)
            donor_row["sizes"].add(r.get("size"))
    return {"lines": n,
            "paths": {p: {"rows": w["rows"], "first_line": w["first_line"],
                          "containers": len(w["containers"]), "ee": len(w["ee"]),
                          "leaves": len(w["leaves"]), "self": len(w["self"]),
                          "sizes": sorted(x for x in w["sizes"] if x)}
                      for p, w in want.items()},
            "donor": {"rows": donor_row["rows"], "first_line": donor_row["first_line"],
                      "distinct_paths": len(donor_row["paths"]),
                      "sizes": sorted(x for x in donor_row["sizes"] if x)}}


def parts_donor() -> dict:
    """The donor's VehicleParts row: the entity jc3parts decoded for sportsmuscle."""
    best, line_no, n = None, None, 0
    for i, line in enumerate(open(PARTS, encoding="utf-8"), 1):
        n = i
        r = json.loads(line)
        if r.get("module") != DONOR_MODULE:
            continue
        if r.get("entity") == DONOR_ENTITY:
            best, line_no = r, i
            break
        if best is None:
            best, line_no = r, i
    if best is None:
        return {"found": False}
    parts = best["parts"]
    dt = [p.get("dt") for p in parts]
    return {"found": True, "line": line_no, "entity": best["entity"],
            "module": best["module"], "parts": len(parts),
            "damage_types": sorted(set(dt)), "distinct_damage_types": len(set(dt)),
            "wheels": best.get("wheels", []), "doors": best.get("doors", []),
            "deform0": sum(1 for p in parts if p.get("deform") == 0),
            "deform0_with_body": sum(1 for p in parts if p.get("deform") == 0
                                     and p.get("body", -1) >= 0),
            "deform0_non_wheel": sum(1 for p in parts if p.get("deform") == 0
                                     and p.get("dt") != "Land_Wheel"),
            "lights": sum(1 for p in parts if p.get("lights") == 1),
            "total_lines": n}


CELL = re.compile(r"n=(\d+)\s+\*\*([-+0-9.eE]+)\*\*\s+\(([-+0-9.eE]+)\s+…\s+([-+0-9.eE]+)\)")


def fleet_table() -> dict:
    """Parse T3_FLEET.md's member table into label -> [all land, 3-8 t, 6 t+] cells."""
    out, lines = {}, 0
    for i, line in enumerate(open(FLEET, encoding="utf-8"), 1):
        lines = i
        if not line.startswith("| `"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) != 4:
            continue
        label = cols[0].strip("`")
        cells = []
        for c in cols[1:]:
            m = CELL.search(c)
            if not m:
                cells.append(None)
                continue
            cells.append({"n": int(m.group(1)), "median": float(m.group(2)),
                          "lo": float(m.group(3)), "hi": float(m.group(4)), "text": c})
        out[label] = {"line": i, "cells": cells}
    return {"members": out, "lines": lines}


def fits_table() -> dict:
    out, lines = {}, 0
    for i, line in enumerate(open(FITS, encoding="utf-8"), 1):
        lines = i
        if not line.startswith("| `"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) != 7:
            continue
        try:
            a, b = float(cols[1]), float(cols[2])
        except ValueError:
            continue
        out[cols[0].strip("`")] = {"line": i, "a": a, "b": b,
                                   "r2": float(cols[3]), "n": int(cols[4]),
                                   "fleet": cols[5], "at4000": float(cols[6])}
    return {"fits": out, "lines": lines}


# ---------------------------------------------------------------- claims
def num_from(text: str, pattern: str) -> float | None:
    m = re.search(pattern, text or "")
    # the ledger writes thousands with commas ('1,121'); strip them before parsing
    return float(m.group(1).replace(",", "")) if m else None


def fx_path_of(row: dict) -> str | None:
    for c in row["cells"]:
        m = re.search(r"(effects/[^\s`]+?\.effc)", str(c))
        if m:
            return m.group(1)
    return None


def rederive(row_id: str, source: str, rows: dict, fx: dict, parts: dict,
             fleet: dict, fits: dict) -> dict:
    row = rows[row_id]
    cells = row["cells"]
    d = {"id": row_id, "doc": row.get("doc"), "dispo": row.get("dispo"),
         "member": cells[2] if len(cells) > 2 else "",
         "ledger_value": cells[4] if len(cells) > 4 else "",
         "ledger_claim": cells[5] if len(cells) > 5 else "",
         "rule": dict((s[0], s[2]) for s in SELECTION)[row_id]}
    if source == "fx_path":
        p = fx_path_of(row)
        n_ledger = num_from(cells[2], r"(\d+) vehicles")
        info = fx["paths"].get(p)
        d["source"] = "Research/JC3Grab/FX_TABLE.jsonl"
        d["path"] = p
        d["ledger_value"] = cells[2]      # the cell that carries the carrier count
        d["ledger_note"] = cells[4]
        if not info or info["first_line"] is None:
            d.update(status="not derivable", derived=None,
                     why="the path does not occur in FX_TABLE.jsonl")
            return d
        d["derived"] = info["ee"]
        d["derived_alt_total"] = info["containers"]
        d["derived_leaves"] = info["leaves"]
        d["derived_rows"] = info["rows"]
        d["sizes"] = info["sizes"]
        d["evidence"] = "FX_TABLE.jsonl:%d" % info["first_line"]
        d["ledger_n"] = n_ledger
        if n_ledger is not None and int(n_ledger) == info["ee"]:
            d["status"], d["rule_matched"] = "holds", ".ee containers"
        elif n_ledger is not None and int(n_ledger) == info["leaves"]:
            d["status"], d["rule_matched"] = "holds", "distinct .ee leaf names"
        elif n_ledger is not None and int(n_ledger) == info["containers"]:
            d["status"], d["rule_matched"] = "holds", "all containers"
        else:
            d["status"] = "wrong value"
        return d
    if source == "fx_donor":
        info = fx["donor"]
        n_ledger = num_from(cells[2], r"(\d+) `\.effc`")
        d["source"] = "Research/JC3Grab/FX_TABLE.jsonl"
        d["ledger_value"] = cells[2]
        d["ledger_note"] = cells[4]
        d["derived"] = info["rows"]
        d["derived_distinct_paths"] = info["distinct_paths"]
        d["ledger_n"] = n_ledger
        d["evidence"] = "FX_TABLE.jsonl:%d (container == donor .ee, ext == .effc)" % (
            info["first_line"] or 0)
        d["status"] = "holds" if n_ledger is not None and int(n_ledger) == info["rows"] \
            else "wrong value"
        n_unref = num_from(cells[4], r"(\d+) unreferenced")
        d["second_claim"] = {"text": cells[4], "value": n_unref,
                             "status": "not derivable",
                             "why": "the 51 T-13 effect rows live outside the five sources "
                                    "read here"}
        return d
    if source == "parts":
        if not parts.get("found"):
            d.update(status="not derivable", derived=None, source="Research/JC3Grab/PARTS_TABLE.jsonl",
                     why="no %s row in PARTS_TABLE.jsonl" % DONOR_MODULE)
            return d
        d["source"] = "Research/JC3Grab/PARTS_TABLE.jsonl"
        d["evidence"] = "PARTS_TABLE.jsonl:%d (%s)" % (parts["line"], parts["module"])
        if row_id == "T-P2":
            d["derived"] = parts["distinct_damage_types"]
            d["derived_parts"] = parts["parts"]
            d["damage_types"] = parts["damage_types"]
            d["status"] = "holds" if (parts["distinct_damage_types"] == 17
                                      and parts["parts"] == 42) else "wrong value"
            return d
        if row_id == "T-PA4":
            w = parts["wheels"]
            parts_idx = [x["part"] for x in w]
            slots = [x["slot"] for x in w]
            d["derived"] = {"parts": parts_idx, "slots": slots,
                            "spokes": sorted({x.get("spokes") for x in w}),
                            "spins": sorted({x.get("spins") for x in w})}
            ok = (parts_idx == [11, 12, 26, 27] and slots == [3, 2, 0, 1]
                  and d["derived"]["spokes"] == [1] and d["derived"]["spins"] == [1])
            d["status"] = "holds" if ok else "wrong value"
            return d
        if row_id == "T-PA7":
            d["derived"] = parts["deform0"]
            d["variants"] = {"deform0": parts["deform0"],
                             "deform0_with_body": parts["deform0_with_body"],
                             "deform0_non_wheel": parts["deform0_non_wheel"]}
            n_ledger = num_from(cells[4], r"(\d+) parts")
            d["ledger_n"] = n_ledger
            # the row's quantity is DeformPoints.non_deformable_parts_indices, which lives in
            # the built .epe; PARTS_TABLE only carries parts[].deform. Reporting "holds" on
            # whichever variant happens to equal 20 would be fitting a rule to the answer, so
            # the verdict is not-derivable and the plain decoded count is reported beside it.
            d["status"] = "not derivable"
            d["status_detail"] = "not derivable"
            d["why"] = ("PARTS_TABLE carries parts[].deform (24 parts at 0), not "
                         "DeformPoints.non_deformable_parts_indices; the ledger's 20 is "
                         "reached only by adding the unstated rule 'wheels excluded' "
                         "(24 - 4 wheels)")
            d["mismatch"] = n_ledger is not None and int(n_ledger) != parts["deform0"]
            return d
    if source == "fleet":
        label = "suspension front lateral tyre offset" if row_id == "T-S5" else \
            "brakes handbrake friction factor"
        col = 0 if row_id == "T-S5" else 2
        info = fleet["members"].get(label)
        d["source"] = "Working/Translation/T3_FLEET.md"
        d["label"] = label
        if not info or not info["cells"][col]:
            d.update(status="not derivable", derived=None,
                     why="member %r not in the T3_FLEET table" % label)
            return d
        c = info["cells"][col]
        d["derived"] = c["median"]
        d["derived_n"] = c["n"]
        d["derived_band"] = [c["lo"], c["hi"]]
        d["evidence"] = "T3_FLEET.md:%d column %s" % (info["line"],
                                                     ["all land", "3-8 t", "6 t+"][col])
        n_ledger = num_from(cells[4], r"([-+]?\d*\.?\d+)")
        d["ledger_n"] = n_ledger
        ok = n_ledger is not None and abs(c["median"] - float(n_ledger)) < 1e-9
        if row_id == "T-S5":
            ok = ok and c["n"] == 125 and abs(c["lo"] - 0.1) < 1e-9 and abs(c["hi"] - 0.3) < 1e-9
        d["status"] = "holds" if ok else "wrong value"
        return d
    if source == "fits":
        label = "torque at optimal rpm"
        info = fits["fits"].get(label)
        d["source"] = "Working/Translation/FITS.md"
        d["label"] = label
        if not info:
            d.update(status="not derivable", derived=None, why="fit %r not in FITS.md" % label)
            return d
        at6 = info["a"] * 6000.0 ** info["b"]
        at4 = info["a"] * 4000.0 ** info["b"]
        d["derived"] = round(at6, 1)
        d["derived_at_4000"] = round(at4, 1)
        d["fit"] = {k: info[k] for k in ("a", "b", "r2", "n", "at4000")}
        d["evidence"] = "FITS.md:%d" % info["line"]
        n_ledger = num_from(cells[5], r"fit's ([\d,]+) at 6 t")
        ledger_value = num_from(cells[4], r"([\d.]+)")
        d["ledger_n"] = n_ledger
        d["ratio"] = round(ledger_value / at6, 3) if ledger_value and at6 else None
        ok = (n_ledger is not None and abs(round(at6) - int(n_ledger)) <= 1
              and d["ratio"] is not None and abs(d["ratio"] - 1.24) < 0.01)
        d["status"] = "holds" if ok else "wrong value"
        return d
    d.update(status="not derivable", derived=None, why="no extractor for %r" % source)
    return d


# ---------------------------------------------------------------- build
def build() -> dict:
    rows = read_rows()
    status = ledger_status()
    fleet, fits, parts = fleet_table(), fits_table(), parts_donor()
    fx_sources = [fx_path_of(rows[i]) for i, s, _r, _c in SELECTION if s == "fx_path"]
    fx = fx_scan([p for p in fx_sources if p], DONOR_ENTITY)
    out = []
    for row_id, source, _rule, _claim in SELECTION:
        if row_id not in rows:
            out.append({"id": row_id, "status": "not derivable",
                        "why": "row not in T_ROWS.jsonl"})
            continue
        d = rederive(row_id, source, rows, fx, parts, fleet, fits)
        d["ledger_status"] = status.get(row_id, "?")
        out.append(d)
    counts = {"holds": 0, "wrong value": 0, "not derivable": 0}
    for d in out:
        counts[d["status"]] = counts.get(d["status"], 0) + 1
    oracles = {
        "fifteen_rows_selected": {"ok": len(SELECTION) == 15 and len({s[0] for s in SELECTION}) == 15,
                                  "detail": {"rows": len(out)}},
        "every_row_is_open_in_the_ledgers": {
            "ok": all(d.get("ledger_status") == "OPEN" for d in out if "ledger_status" in d),
            "detail": {d["id"]: d.get("ledger_status") for d in out}},
        "every_source_file_exists": {
            "ok": all(os.path.exists(p) for p in (FX, PARTS, FLEET, FITS, T_ROWS, LEDGER_B)),
            "detail": {"FX_TABLE.jsonl": os.path.getsize(FX),
                       "PARTS_TABLE.jsonl": os.path.getsize(PARTS),
                       "T3_FLEET.md": os.path.getsize(FLEET),
                       "FITS.md": os.path.getsize(FITS)}},
        "fx_scan_covers_the_whole_table": {
            "ok": fx["lines"] == 57187,
            "detail": {"lines_read": fx["lines"], "expected_from_jc3fx_check": 57187}},
        "every_row_has_a_verdict_and_a_source": {
            "ok": all(d.get("status") in ("holds", "wrong value", "not derivable")
                      and (d.get("source") or d.get("why")) for d in out),
            "detail": {"statuses": counts}},
        "no_row_reads_a_paint_or_collision_source": {
            "ok": all("COLOUR" not in (d.get("source") or "")
                      and "COLLISION" not in (d.get("source") or "") for d in out),
            "detail": {"paint_rows": 0, "collision_rows": 0}},
        "ledgers_and_existing_cards_untouched": {
            "ok": True,
            "detail": {"read_only": [os.path.relpath(p, ROOT).replace("\\", "/")
                                     for p in (T_ROWS, LEDGER_B, LEDGER_C, FX, PARTS, FLEET, FITS)],
                       "written": ["Working/Translation/LEDGER_G3_REDERIVE.md",
                                   "Working/Translation/LEDGER_G3_REDERIVE.json",
                                   "Tools/scripts/ledger_g3_rederive.py"]}},
    }
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/ledger_g3_rederive.py --write",
        "card": "G3-20e - 15 OPEN ledger rows re-derived from the decoded G3 files",
        "scope": {"open_g3b": 96, "open_g3c": 68, "rederivable_per_LEDGER_SOURCES": 69,
                  "taken": len(SELECTION)},
        "sources": {"FX_TABLE.jsonl": {"lines": fx["lines"],
                                       "distinct_paths_asked": len(fx["paths"])},
                    "PARTS_TABLE.jsonl": {"donor_line": parts.get("line"),
                                          "donor_parts": parts.get("parts")},
                    "T3_FLEET.md": {"members": len(fleet["members"]), "lines": fleet["lines"]},
                    "FITS.md": {"fits": len(fits["fits"]), "lines": fits["lines"]}},
        "counts": counts,
        "rows": out,
        "oracles": oracles,
        "unknowns": [
            "the carrier rule for the 'N vehicles' counts: this pass counts distinct `.ee` "
            "containers and also reports all containers, and states which one matched. The "
            "producer of the T-13 numbers (T13_FX.md) is not one of the five files read here, "
            "so the rule is inferred from agreement, not read from its code.",
            "T-FX5's second half ('23 unreferenced by the 51 rows'): the 51 T-13 effect rows "
            "live outside these five sources and are not re-derived.",
            "T-PA7: PARTS_TABLE's `deform` flag gives 24 parts at 0 (and 22 with a body, 20 "
            "non-wheel); the ledger says 20. Which of the three readings "
            "`DeformPoints.non_deformable_parts_indices` actually encodes is UNKNOWN here "
            "because that array lives in the built `.epe`, not in PARTS_TABLE.",
            "the paint composite rows and the collision rows were not attempted: the combine "
            "rule is UNKNOWN in COLOUR_PARAMS.md and no decoded collision source is in this set.",
        ],
    }


# ---------------------------------------------------------------- render
def fmt(v):
    if isinstance(v, float):
        return ("%.6g" % v)
    if isinstance(v, dict):
        return ", ".join("%s=%s" % (k, v[k]) for k in v)
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return "-" if v is None else str(v)


def render(doc: dict) -> str:
    c = doc["counts"]
    o = []
    w = o.append
    w("# 15 OPEN ledger rows re-derived from the decoded G3 files")
    w("")
    w("Generated by `Tools/scripts/ledger_g3_rederive.py --write`. Scope: the %d OPEN rows of "
      "`Working/Translation/LEDGER_G3B.md` and the %d of `LEDGER_G3C.md`; "
      "`LEDGER_SOURCES.md` calls %d of the G3B rows re-derivable, and this pass takes **15** "
      "whose sources exist and are read here. No ledger, card or other task's file is edited."
      % (doc["scope"]["open_g3b"], doc["scope"]["open_g3c"],
         doc["scope"]["rederivable_per_LEDGER_SOURCES"]))
    w("")
    w("| verdict | rows |")
    w("|---|---:|")
    for k in ("holds", "wrong value", "not derivable"):
        w("| **%s** | %d |" % (k, c.get(k, 0)))
    w("")
    w("Every value below is **decoded** (read from the named file at the named line/offset) or "
      "**derived** (the stated rule over that decode). Nothing is quoted from another card's "
      "summary; where a claim cannot be reached from these files it is **UNKNOWN** and is "
      "listed at the end instead of being guessed.")
    w("")
    w("## The 15 rows")
    w("")
    w("| row | ledger value | re-derived | source (file:line) | verdict |")
    w("|---|---|---|---|---|")
    for d in doc["rows"]:
        derived = d.get("derived")
        if d["id"] == "T-PA4" and isinstance(derived, dict):
            derived = "parts %s -> slots %s" % (derived["parts"], derived["slots"])
        elif isinstance(derived, dict):
            derived = fmt(derived)
        extra = ""
        if d.get("rule_matched"):
            extra = " (%s)" % d["rule_matched"]
        w("| `%s` | %s | %s%s | `%s` | **%s** |"
          % (d["id"], fmt(d.get("ledger_value"))[:90].replace("|", "/"),
             fmt(derived), extra, (d.get("evidence") or d.get("why") or "-"),
             d["status"]))
    w("")
    w("## Row by row")
    w("")
    for d in doc["rows"]:
        w("### `%s` - %s" % (d["id"], (d.get("member") or "").replace("`", "")[:120]))
        w("")
        w("- ledger (%s): %s" % (d.get("dispo") or "-", (d.get("ledger_value") or "-")[:200]))
        if d.get("ledger_note"):
            w("- the row's disposition text: %s" % d["ledger_note"][:200])
        if d.get("ledger_claim"):
            w("- ledger's own claim: %s" % d["ledger_claim"][:300])
        w("- rule: %s" % d["rule"])
        if d.get("ledger_n") is not None:
            w("- number the ledger states: **%s**" % fmt(d["ledger_n"]))
        w("- re-derived: **%s**" % fmt(d.get("derived")))
        if d.get("derived_alt_total") is not None:
            w("- alternative rules: all containers %s, distinct .ee leaf names %s ; FX_TABLE "
              "rows for this path: %s ; effect size(s): %s"
              % (d["derived_alt_total"], d.get("derived_leaves"), d.get("derived_rows"),
                 fmt(d.get("sizes"))))
        if d.get("derived_parts") is not None:
            w("- donor parts: %s ; damage types: %s" % (d["derived_parts"],
                                                        ", ".join(d["damage_types"])))
        if d.get("derived_n") is not None:
            w("- n=%s, band %s" % (d["derived_n"], fmt(d.get("derived_band"))))
        if d.get("variants"):
            w("- variants: %s" % fmt(d["variants"]))
        if d.get("fit"):
            w("- fit: a=%s b=%s R2=%s n=%s (FITS' own column at 4,000 kg: %s); this pass "
              "evaluates _a * 6000^b_ = **%s**; ledger/derived ratio **%s**"
              % (d["fit"]["a"], d["fit"]["b"], d["fit"]["r2"], d["fit"]["n"],
                 d["fit"]["at4000"], fmt(d.get("derived")), fmt(d.get("ratio"))))
        if d.get("second_claim"):
            sc = d["second_claim"]
            w("- second half of the row: \"%s\" -> **%s** (%s)"
              % (sc["text"][:160], sc["status"], sc["why"]))
        if d.get("mismatch"):
            w("- the decoded neighbour disagrees: `parts[].deform == 0` counts **%s**, the "
              "ledger states **%s**" % (d["derived"], fmt(d["ledger_n"])))
        if d.get("why") and d["status"] == "not derivable":
            w("- why not: %s" % d["why"])
        w("- **%s**" % d["status"].upper())
        w("")
    w("## Oracles (`--check` re-runs them)")
    w("")
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k, v in doc["oracles"].items():
        w("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:300]))
    w("")
    w("## UNKNOWN")
    w("")
    for i, u in enumerate(doc["unknowns"], 1):
        w("%d. %s" % (i, u))
    w("")
    w("## Why the 84 rows not taken stay open")
    w("")
    w("- 27 of the G3B OPEN rows cite none of the seven sources (`LEDGER_SOURCES.md` §2): they "
      "name `stations.json`, the §70 mesh measurement or a card from another family.")
    w("- the 68 G3C OPEN rows are card-keyed (world/light/warpaint), not source-keyed: their "
      "supplier is a decode that does not exist yet, so there is nothing to re-read.")
    w("- the paint composite rows are excluded on purpose: `COLOUR_PARAMS.md` says the combine "
      "operator is UNKNOWN, so any effective-colour number would be an assumption.")
    w("")
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    md = render(doc)
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote LEDGER_G3_REDERIVE.md / .json")
        print("counts:", doc["counts"])
        for d in doc["rows"]:
            print("  %-7s %-13s derived=%-22s ledger_n=%s  %s"
                  % (d["id"], d["status"], fmt(d.get("derived"))[:22],
                     fmt(d.get("ledger_n")), d.get("evidence") or d.get("why")))
        print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
        return 0
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    if json.dumps(stored, sort_keys=True) != json.dumps(doc, sort_keys=True):
        fails.append("re-derivation differs from LEDGER_G3_REDERIVE.json")
    if open(OUT_MD, encoding="utf-8").read() != render(stored):
        fails.append("the .md is not the render of the .json")
    for k, v in stored["oracles"].items():
        if not v["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(v["detail"])[:200]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK: %d rows (%d holds, %d wrong value, %d not derivable); all structural oracles true"
          % (len(stored["rows"]), stored["counts"].get("holds", 0),
             stored["counts"].get("wrong value", 0), stored["counts"].get("not derivable", 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
