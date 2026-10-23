"""t_rows.py - one disposition for every translation row (T-1 and T-2b).

`T1_TRANSLATION.md` and `T2_TRANSLATION.md` are prose tables: 88 numbered rows,
each a falsifiable property.  Prose cannot fail a build, so this tool turns every
row into a ledger line with a **disposition** and then checks the ledger against
the documents and against the build's edit list:

  edit    the proposed value is a module member and is in `t1_edits.json`
  keep    the build already carries the proposal (no edit needed)
  epe     the value lives in the entity graph, not a module (parts, lights)
  re-read verified by decoding the built entity, not by an edit
  blocked the value cannot be written with this toolkit (write side missing)
  out     no JC3 expression exists (feature gap, not a translation row)

Usage:
  python t_rows.py build      # parse both tables -> T_ROWS.jsonl
  python t_rows.py check      # ledger vs documents vs t1_edits.json
  python t_rows.py summary    # counts by disposition and by family
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
DOCS = [("T-1", os.path.join(WORK, "T1_TRANSLATION.md")),
        ("T-2b", os.path.join(WORK, "T2_TRANSLATION.md")),
        ("T-3", os.path.join(WORK, "T3_COVERAGE.md"))]
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
EDITS = os.path.join(WORK, "t1_edits.json")

ROW_RE = re.compile(r"^\|\s*(T-[A-Z]{1,3}\d+)\s*\|")
HEAD_RE = re.compile(r"^##\s+(.*)$")
# a verification table's first column is a row *family*, not a definition
SKIP_SECTION = re.compile(r"^\d+\.\s+(Verification|Blocked rows)")

# Rows whose disposition is not "keep".  A row absent from this table is a keep:
# the build already carries the proposal, which is what test-084 measured.
DISPO: dict[str, tuple[str, str]] = {
    # --- T-1, motion --------------------------------------------------------
    "T-G5": ("edit", "probe: friction_type 0 -> 2, carried and read back"),
    "T-M1": ("edit", "mass 4000 -> 6000 (armored class)"),
    "T-M2": ("edit", "yaw/pitch/roll 1.8/1.5/0.5 -> 4.0/2.6/1.2"),
    "T-M4": ("edit", "wheel mass 25/75 -> 75/150"),
    "T-S1": ("edit", "suspension strength 80/80 -> 45/45"),
    "T-S2": ("edit", "compression 2.5 -> 3.0"),
    "T-R1": ("edit", "arcade friction 1.0 -> 3.0 (the understeer row)"),
    "T-ST1": ("edit", "steer 55 deg at 20 km/h -> 20 deg at 72, falloff 1.5"),
    "T-E1": ("edit", "rpm band 1000/5000/7300 -> 800/2800/4500"),
    "T-E2": ("keep", "absolute torque stays 1393.5: +30% over the class fit, inside the fleet"),
    "T-E3": ("edit", "torque factors at min/max rpm 0.86/0.84 -> 1.0/0.65"),
    "T-E4": ("edit", "6 gears at 7000 -> 5 gears at 4200"),
    "T-A2": ("edit", "drag 0.139 -> 0.55"),
    "T-A4": ("edit", "lift -1.95 -> -0.3"),
    "T-K1": ("edit", "brake torque 10000 -> 5000"),
    "T-L1": ("epe", "light rig is SVehicleLight presets in the entity graph"),
    "T-L2": ("epe", "flare entries map onto the same two headlight presets"),
    "T-L3": ("epe", "brake rows are presets in the entity graph"),
    "T-L4": ("blocked", "JC3 has no wheel-light preset to map onto"),
    "T-L5": ("epe", "secondary spot preset in the entity graph"),
    "T-L6": ("epe", "dashboard preset in the entity graph"),
    "T-L7": ("epe", "boot preset in the entity graph"),
    "T-P1": ("epe", "part names live in the entity graph, carried from test-083"),
    "T-P2": ("keep", "damage types are in VehicleDamage, carried"),
    "T-P3": ("blocked", "no .physicsc writer: reading is solved, writing is not"),
    # --- T-2b, the other half ----------------------------------------------
    "T-PA1": ("epe", "wheel parts in the built graph"),
    "T-PA2": ("epe", "light points -> parts in the built graph"),
    "T-PA3": ("epe", "part -> collision body ids in the built graph"),
    "T-PA4": ("epe", "wheel_parts slots in the built graph"),
    "T-PA5": ("epe", "door parts in the built graph"),
    "T-PA6": ("epe", "constraint points in the built graph"),
    "T-PA7": ("epe", "non-deformable part list in the built graph"),
    "T-PA8": ("epe", "6 orphan sockets dropped, they cannot be driven"),
    "T-LG2": ("keep", "closed by t2_lg2.py: 21 rows / 22 objects, row-for-row the donor's"),
    "T-LG4": ("blocked", "no wheel-light preset exists in JC3"),
    "T-LG5": ("out", "battle-mode and forensics rigs have no JC3 system"),
    "T-AU1": ("keep", "LandAudio keeps its two members; the mapping is a bank task"),
    "T-AU2": ("keep", "engine bank already swapped (test-060)"),
    "T-AU3": ("blocked", "10 banks are absent from the install"),
    "T-AU4": ("edit", "LandAudio.max_rpm 10000 -> 4500, follows T-E1"),
    "T-FX1": ("keep", "break effects carried"),
    "T-FX2": ("keep", "burn effects carried"),
    "T-FX3": ("blocked", "no usage slot for an exhaust flame"),
    "T-FX4": ("out", "EMP/seismic/sonar are features JC3 does not have"),
    "T-FX5": ("keep", "23 unreferenced .effc belong to donor parts"),
    "T-DM1": ("keep", "max_health 2000 carried"),
    "T-DM2": ("edit", "bullet armour 100 -> 99, the fleet maximum"),
    "T-DM3": ("keep", "heavy armour 20 carried"),
    "T-DM4": ("keep", "4000/1050/250 thresholds carried, at the fleet maximum"),
    "T-DM5": ("keep", "24 damage types and the part join carried"),
    "T-DM6": ("keep", "deform_scale 1 carried"),
    "T-CO1": ("keep", "donor chassis by decision"),
    "T-CO2": ("blocked", "no .physicsc writer"),
    "T-CO3": ("blocked", "has_world_collision_shape needs a .physicsc write"),
    # --- T-3, the factors the first table never named ----------------------
    "T-G6": ("keep", "BmAK sim radius 0.64 m vs the mesh 0.683: the mesh is the contact radius"),
    "T-S6": ("blocked", "JC3 has no suspension bias/droop member or unit bridge for stiffness"),
    "T-ST7": ("blocked", "BmAK 220 deg/s is 0.25 s to lock; the JC3 family floor is 0.5 s"),
    "T-K4": ("keep", "rear-only handbrake, factor 1 = the 6 t median; e-brake force has no member"),
    "T-DR1": ("keep", "the donor drift block already equals the 6 t median"),
    "T-EF1": ("keep", "tire effects are fleet-invariant"),
    "T-DM7": ("next", "test-086: impact_damage_factor 0 -> 1, like all 156 land vehicles"),
    "T-FX6": ("epe", "vehicle effects are carried in the entity graph"),
    "T-AU5": ("blocked", "transformation/taser banks are absent from the install"),
    "T-W1": ("out", "JC3 gives a car no player-fired weapons"),
    "T-BM1": ("out", "no transformation, tank turn or battle-mode armour in JC3"),
    "T-AC1": ("out", "JC3 cars have no mid-air yaw authority"),
    "T-RA1": ("out", "no ram/dodge/shove assist system for cars"),
    "T-SR1": ("out", "JC3 has no upright constraint"),
    "T-PA9": ("keep", "actor plumbing carried by the entity graph"),
}

VOCAB = ("edit", "next", "keep", "epe", "re-read", "blocked", "out")


def parse_docs() -> list[dict]:
    rows: list[dict] = []
    seen: dict[str, str] = {}
    for tag, path in DOCS:
        if not os.path.exists(path):
            raise SystemExit(f"missing {path}")
        section = ""
        for line in open(path, encoding="utf-8"):
            h = HEAD_RE.match(line)
            if h:
                section = h.group(1).strip()
                continue
            if SKIP_SECTION.match(section):
                continue
            m = ROW_RE.match(line)
            if not m:
                continue
            rid = m.group(1)
            if rid in seen:
                raise SystemExit(f"{rid} appears twice ({seen[rid]} and {path})")
            seen[rid] = path
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append({"id": rid, "doc": tag, "section": section, "cells": cells})
    return rows


def load_edits() -> dict[str, int]:
    data = json.load(open(EDITS, encoding="utf-8"))
    counts: dict[str, int] = {}
    for e in data["edits"]:
        counts[e["row"]] = counts.get(e["row"], 0) + 1
    return counts


def build() -> int:
    rows = parse_docs()
    edits = load_edits()
    out = []
    problems = []
    for r in rows:
        dispo, why = DISPO.get(r["id"], ("keep", "build carries the proposal; nothing to edit"))
        if dispo not in VOCAB:
            problems.append(f"{r['id']}: bad disposition {dispo!r}")
        if dispo == "edit" and r["id"] not in edits:
            problems.append(f"{r['id']}: disposition edit but no row in {os.path.basename(EDITS)}")
        if dispo == "next" and r["id"] in edits:
            problems.append(f"{r['id']}: marked next but already in {os.path.basename(EDITS)}")
        out.append({**r, "dispo": dispo, "why": why, "edits": edits.get(r["id"], 0)})
    for rid in edits:
        if rid not in {r["id"] for r in rows}:
            problems.append(f"{rid}: in {os.path.basename(EDITS)} but not in the tables")
    for rid in DISPO:
        if rid not in {r["id"] for r in rows}:
            problems.append(f"{rid}: disposition for a row the tables do not have")
    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"{LEDGER}: {len(out)} rows, {sum(r['edits'] for r in out)} edits over "
          f"{sum(1 for r in out if r['edits'])} rows")
    for p in problems:
        print("FAIL", p)
    return 1 if problems else 0


def load_ledger() -> list[dict]:
    if not os.path.exists(LEDGER):
        raise SystemExit("no T_ROWS.jsonl - run `t_rows.py build`")
    return [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]


def check() -> int:
    rows = parse_docs()
    ledger = load_ledger()
    edits = load_edits()
    problems: list[str] = []
    doc_ids = [r["id"] for r in rows]
    led_ids = [r["id"] for r in ledger]
    for rid in doc_ids:
        if rid not in led_ids:
            problems.append(f"{rid}: in the tables, missing from the ledger")
    for rid in led_ids:
        if rid not in doc_ids:
            problems.append(f"{rid}: in the ledger, not in the tables (stale)")
    if len(led_ids) != len(set(led_ids)):
        problems.append("ledger has duplicate ids")
    for r in ledger:
        if r["dispo"] not in VOCAB:
            problems.append(f"{r['id']}: disposition {r['dispo']!r}")
        if r["dispo"] == "edit" and r["id"] not in edits:
            problems.append(f"{r['id']}: edit disposition, no entry in the edit list")
        if r["dispo"] == "next" and r["id"] in edits:
            problems.append(f"{r['id']}: marked next but already in the edit list")
        if r["dispo"] not in ("edit", "next") and r["id"] in edits:
            problems.append(f"{r['id']}: in the edit list but disposition is {r['dispo']}")
        if not r.get("why"):
            problems.append(f"{r['id']}: no reason")
    for rid in edits:
        if rid not in led_ids:
            problems.append(f"{rid}: edit row absent from the ledger")
    counts = {}
    for r in ledger:
        counts[r["dispo"]] = counts.get(r["dispo"], 0) + 1
    print(f"ledger {len(ledger)} rows | " + " ".join(f"{k} {counts.get(k,0)}" for k in VOCAB)
          + f" | edits {sum(edits.values())} over {len(edits)} rows")
    if problems:
        for p in problems:
            print("FAIL", p)
        print(f"{len(problems)} problem(s)")
        return 1
    print("check ok")
    return 0


def summary() -> int:
    ledger = load_ledger()
    by_doc: dict[str, dict[str, int]] = {}
    for r in ledger:
        d = by_doc.setdefault(r["doc"], {})
        d[r["dispo"]] = d.get(r["dispo"], 0) + 1
    for doc in sorted(by_doc):
        print(doc, dict(sorted(by_doc[doc].items())))
    fam: dict[str, set[str]] = {}
    for r in ledger:
        family = re.match(r"T-([A-Z]{1,3})", r["id"]).group(1)
        fam.setdefault(family, set()).add(r["dispo"])
    for family in sorted(fam):
        print(f"  {family:3} {' '.join(sorted(fam[family]))}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="parse both tables and write T_ROWS.jsonl").set_defaults(func=build)
    sub.add_parser("check", help="ledger vs tables vs the edit list").set_defaults(func=check)
    sub.add_parser("summary", help="counts by disposition").set_defaults(func=summary)
    a = ap.parse_args()
    sys.exit(a.func())


if __name__ == "__main__":
    main()
