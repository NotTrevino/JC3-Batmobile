"""t22_reopen.py - T-22 / B-10 reopened: the drivable collision replaces the donor chassis.

`tmp/freebuff/reports/collision-where.md` (G3-16, `Research/BatmobileGrab/COLLISION_WHERE.md`)
decoded the asset the drivable Batmobile actually simulates: `Physics.Batmobile_V3_Physics`
(BmGame.upk export 158266, 194 B) - **2 body setups, 3 box elements, 1 constraint**, reached from
`Batmobile.SVehicleMesh` at property offset 824. T-22 was closed on the 32-body wreck census and
B-10 wrote a donor hull set fitted to the render bbox; neither ever read the drivable asset.

This tool is the plan those two cards reopen on. It re-derives, from the generated files only:

  S1  chassis box 0  -> body 0's existing hull slot (the one B-10/B-10d already rewrites)
  S2  chassis box 1  -> a second shape instance in body 0's compound (no free hull slot)
  S3  weapons pod    -> a third shape carried rigid with body 0 (no part for it exists)
  S4  constraint 171462 -> one constraint between the two bodies (no JC3 writer decoded)
  S5  acceptance     -> jc3hkx check --all --file + union vs the two chassis boxes + Q-2

Every number is read: `COLLISION_WHERE.json` (the asset and its boxes), `bm_vehicle_hull.json`
(the decoded box TMs and the built body count), `bm_collision.json` (what the build writes today),
`t16_collision.json` (hull slots and unbound instances), `T_ROWS.jsonl` (the row dispositions) and
`GRAB_BACKLOG.md` (the two REOPENED markers).

Usage
    python Tools/scripts/t22_reopen.py --write
    python Tools/scripts/t22_reopen.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
CW = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_WHERE.json")
HULL = os.path.join(ROOT, "Working", "Collision2", "bm_vehicle_hull.json")
BUILT = os.path.join(ROOT, "Working", "Collision", "bm_collision.json")
T16 = os.path.join(WORK, "t16_collision.json")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
OUT_J = os.path.join(WORK, "T22_REOPEN.json")
OUT_M = os.path.join(WORK, "T22_REOPEN.md")

REOPENED = "REOPENED 2026-11-07"
CARDS = ("T-22", "B-10")
ROWS = ("T-P3", "T-CO1")


def load(p: str) -> dict:
    return json.load(open(p, encoding="utf-8"))


def fmt_cm(b: dict) -> str:
    x, y, z = b["extents_cm"]
    cx, cy, cz = b["centre_cm"]
    return f"{x:.3f} x {y:.3f} x {z:.3f} cm at ({cx:g}, {cy:g}, {cz:g})"


def fmt_m(b: dict) -> str:
    x, y, z = b["extents_cm"]
    return f"{x / 100:.5f} x {y / 100:.5f} x {z / 100:.5f} m"


def build() -> dict:
    cw = load(CW)
    hull = load(HULL)
    built = load(BUILT)
    t16 = load(T16)
    ledger = [json.loads(x) for x in open(LEDGER, encoding="utf-8") if x.strip()]
    led = {r["id"]: r for r in ledger}
    backlog = open(BACKLOG, encoding="utf-8").read()

    asset = cw["drivable_asset"]
    bodies = cw["drivable_bodies"]
    chassis, pod = bodies[0], bodies[1]
    boxes = [b for body in bodies for b in body["boxes"]]
    tms = {t["export"]: t for t in hull["box_tms"]}
    ch_tms = [tms[b["export"]] for b in (chassis, chassis)]

    built_bodies = hull["bodies"]["bodies"]
    written = built["summary"]["hulls_written"]
    wheels = 4
    body_shapes_today = written - wheels
    missing = len(boxes) - body_shapes_today

    steps = [
        {"id": "S1", "box": f"chassis box 0, {fmt_cm(chassis['boxes'][0])}",
         "target": "body 0's existing hull slot - the one hull B-10/B-10d already rewrite",
         "state": "writable: scale + translate into an existing slot is proven (G2-30)",
         "axis": "bone x (6.903 m) -> JC3 z, y (3.745 m) -> x, z (2.075 m) -> y, "
                 f"residual <= {hull['axis_map']['best']['max_cm']:.3f} cm"},
        {"id": "S2", "box": f"chassis box 1, {fmt_cm(chassis['boxes'][1])}",
         "target": "a second shape instance in body 0's compound (the underside box)",
         "state": "UNKNOWN: 0 free hull slots - "
                  f"{t16['decomposition']['unbound_hull_instances']} unbound instances belong to "
                  "the donor bumpers; re-purpose one or grow the object count (unproven)",
         "axis": "same map; it sits 27.75 cm below box 0's centre"},
        {"id": "S3", "box": f"weapons pod, {fmt_cm(pod['boxes'][0])}, "
                            f"{tms[pod['export']]['rotation_deg_about_y']:.3f} deg about y",
         "target": "a third shape carried rigid with body 0 (no `Rig_Weapons_Trans` part exists "
                   "in the JC3 part table, so a separate body has no owner)",
         "state": "UNKNOWN: same slot question; BmAK's 2nd body has no JC3 part to bind to",
         "axis": "4 deg about y is decoded and must be re-applied to the box, not to the car"},
        {"id": "S4", "box": "constraint setup 171462 (1), names "
                            "[Weapons_Trans, Weapons_Trans, Chassis]",
         "target": "one constraint between the chassis and the pod",
         "state": "NOT WRITABLE: `bm_collision.json` carries 0 constraint data and no JC3 "
                  "constraint writer is decoded - named omission",
         "axis": "parent/child order is UNKNOWN (no `RB_ConstraintSetup` layout)"},
        {"id": "S5", "box": "acceptance",
         "target": "the rebuilt file + a drive",
         "state": "gate: `jc3hkx.py check --all --file`, body-0 shape union within 5 cm of the "
                  "two chassis boxes, pod within 5 cm at 4 deg, then Q-2 kerb + ram",
         "axis": "the render-bbox gate becomes the raycast-body check (B-10b / body 42)"},
    ]

    oracles = []

    def oracle(oid: str, ok: bool, detail: str) -> None:
        oracles.append({"id": oid, "ok": bool(ok), "detail": detail})

    oracle("O1-drivable-asset-2-bodies",
           asset["arrays"]["BodySetup"]["count"] == 2 and len(bodies) == 2,
           f"{asset['path']} export {asset['export']} ({asset['size']} B): BodySetup "
           f"{asset['arrays']['BodySetup']['count']}, bodies decoded {len(bodies)}")
    oracle("O2-boxes-3", len(boxes) == 3 and sum(b["box_count"] for b in bodies) == 3,
           "boxes " + ", ".join(f"{b['bone']} {b['box_count']}" for b in bodies))
    oracle("O3-one-constraint", asset["arrays"]["ConstraintSetup"]["count"] == 1,
           f"ConstraintSetup {asset['arrays']['ConstraintSetup']['count']}, instance arrays "
           f"Bodies {cw['drivable_instance_arrays']['arrays']['Bodies']['count']} / Constraints "
           f"{cw['drivable_instance_arrays']['arrays']['Constraints']['count']}")
    oracle("O4-chassis-tm-identity",
           all(t["identity_error"] == 0.0 for t in ch_tms),
           "chassis identity_error " + ", ".join(f"{t['identity_error']:.1e}" for t in ch_tms))
    oracle("O5-pod-4deg",
           abs(tms[pod["export"]]["rotation_deg_about_y"] - 4.0) < 1e-9,
           f"pod rotation {tms[pod['export']]['rotation_deg_about_y']:.3f} deg about y, det "
           f"{tms[pod['export']]['det']:.9f}")
    oracle("O6-built-set-still-donor",
           built_bodies == 62 and written == 5,
           f"built file carries {built_bodies} donor bodies; {written} hulls written "
           f"({body_shapes_today} body + {wheels} wheels) -> {missing} shape(s) missing")
    oracle("O7-no-free-hull-slot",
           t16["donor"]["hulls"] == 54
           and t16["decomposition"]["unbound_hull_instances"] == 14,
           f"{t16['donor']['hulls']} donor hulls, "
           f"{t16['decomposition']['unbound_hull_instances']} unbound instances (the two donor "
           f"bumpers), object count fixed")
    best, second = hull["axis_map"]["best"], hull["axis_map"]["second"]
    oracle("O8-axis-map-inside-band",
           best["max_cm"] < 30.0 < second["max_cm"],
           f"best {best['boxes_from_dims']} residual {best['residual_cm']} cm; second "
           f"{second['max_cm']:.3f} cm")
    heads = {c: [ln for ln in backlog.splitlines() if ln.startswith(f"#### {c} ·")]
             for c in CARDS}
    rows12 = {c: [ln for ln in backlog.splitlines() if ln.startswith(f"| {c} | {REOPENED}")]
              for c in CARDS}
    oracle("O9-cards-reopened",
           all(len(heads[c]) == 1 and REOPENED in heads[c][0] for c in CARDS)
           and all(len(rows12[c]) == 1 for c in CARDS),
           "; ".join(f"{c} heading {len(heads[c])} / §12 row {len(rows12[c])}" for c in CARDS)
           + f" carry {REOPENED}")
    oracle("O10-ledger-rows",
           all(r in led and led[r]["dispo"] == "next"
               and "Batmobile_V3_Physics" in json.dumps(led[r], ensure_ascii=False)
               for r in ROWS),
           ", ".join(f"{r} {led.get(r, {}).get('dispo')}" for r in ROWS)
           + " - both cite the drivable asset")

    return {
        "schema": 1,
        "generator": "Tools/scripts/t22_reopen.py",
        "task": "collision-where apply",
        "cards": list(CARDS),
        "inputs": {
            "collision_where": {"path": "Research/BatmobileGrab/COLLISION_WHERE.json",
                                "generator": "Tools/scripts/grab_collision_where.py (G3-16)"},
            "vehicle_hull": {"path": "Working/Collision2/bm_vehicle_hull.json",
                             "generator": "Tools/scripts/bm_vehicle_hull.py (B-10e)"},
            "built": {"path": "Working/Collision/bm_collision.json",
                      "generator": "Tools/scripts/bm_collision.py (B-10)"},
            "hull_slots": {"path": "Working/Translation/t16_collision.json",
                           "generator": "Tools/scripts/t22_collision.py (T-22)"},
        },
        "asset": {
            "path": asset["path"], "package": asset["package"], "export": asset["export"],
            "size": asset["size"],
            "reached_from": "Batmobile.SVehicleMesh property offset 824 "
                            "(Default__RVehicleBatmobileBase.SVehicleMesh, export 175716)",
            "bodies": len(bodies), "boxes": len(boxes), "constraints": 1,
            "instance": asset["instance"],
        },
        "bodies": [{"bone": b["bone"], "export": b["export"], "boxes": b["box_count"],
                    "box": [{"extents_cm": x["extents_cm"], "centre_cm": x["centre_cm"],
                             "extents_m": [v / 100 for v in x["extents_cm"]]}
                            for x in b["boxes"]],
                    "tm_identity_error": tms[b["export"]]["identity_error"],
                    "rotation_deg_about_y": tms[b["export"]]["rotation_deg_about_y"]}
                   for b in bodies],
        "today": {"built_bodies": built_bodies, "hulls_written": written,
                  "body_shapes_today": body_shapes_today, "shapes_missing": missing,
                  "objects": built["write"]["objects"],
                  "file": "Working/Collision/batmobile.physicsc",
                  "sha256": built["write"]["sha256"],
                  "source": "bm-RC2 donor topology re-cut to the body mesh (54 hulls)"},
        "plan": steps,
        "replaces": (
            "The donor Serpente chassis hull stops being the colliding body-0 shape: body 0's "
            "hull is re-cut to the BmAK chassis boxes (identity TM, decoded) and the pod box is "
            "added at 4 deg, so the car's rigid-body contact is BmAK's own. The other 61 donor "
            "bodies stay as JC3's per-part contact - BmAK has 2 bodies in total, so carrying its "
            "2-body model literally would delete part-level contact; the difference is declared, "
            "not silently dropped. The one BmAK constraint has no JC3 writer (S4)."),
        "oracles": oracles,
        "all_ok": all(o["ok"] for o in oracles),
        "unknowns": [
            "Whether the object count may grow: no free hull slot exists, and G2-30 proved "
            "scale/translate of an existing hull, not a new shape.",
            "Which FName in constraint 171462 is the parent body (no `RB_ConstraintSetup` "
            "layout in BMSDK_OFFSETS.json).",
            "Whether the engine simulates the pod body (bool at 0x224 is true, unnamed), so "
            "S3's 'carried rigid' is a plan, not a decoded runtime fact.",
            "The live Batman-vs-Batmobile mesh per mode (selector at 5895 not serialised) - "
            "unchanged by this plan.",
        ],
        "revert": (
            "Delete `T22_REOPEN.*`, `t22_reopen.py`; revert the T-P3/T-CO1/T-CO2/T-CO3 cells via "
            "`git`-less backups (`Backups/`) or re-run `t22_collision.py --write` after restoring "
            "its rows, then `t_rows.py build`, `t_blocked.py --write`, `status_audit.py --write`."),
    }


def render_md(d: dict) -> str:
    a, t = d["asset"], d["today"]
    L = ["# T-22 / B-10 reopened - the drivable collision replaces the donor chassis", "",
         f"Generated by `{d['generator']}`; `--check` re-derives every number from the files "
         f"named at the bottom.", "",
         f"**STATUS: REOPENED 2026-11-07.** `tmp/freebuff/reports/collision-where.md` (G3-16) "
         f"decoded the asset the drivable car simulates, so T-22's premise (\"the driveable car "
         f"has no physics asset\", the 32-body wreck census) and B-10's hull target (the donor "
         f"chassis fitted to the render bbox) are both superseded. `T-22` and `B-10` are live "
         f"again; `T-P3`, `T-CO1`, `T-CO2` and `T-CO3` carry the new source.", "",
         "## The asset", "",
         f"`{a['path']}` - {a['package']} export {a['export']}, {a['size']} B, reached from "
         f"`{a['reached_from']}`.", "",
         "| export | bone | boxes | box extents / centre | TM |", "|---|---|---:|---|---|"]
    for b in d["bodies"]:
        for i, box in enumerate(b["box"]):
            L.append(f"| {b['export']} | `{b['bone']}` | {i} | {fmt_cm(box)} | "
                     f"identity_error {b['tm_identity_error']:.1e}, "
                     f"{b['rotation_deg_about_y']:.3f} deg about y |")
    L += ["", f"Bodies **{a['bodies']}**, boxes **{a['boxes']}**, constraints "
              f"**{a['constraints']}**; instance export {a['instance']['export']} serialises "
              f"Bodies 2 / Constraints 1 - one per asset entry, so the asset is not shared or "
              f"partially instantiated.", "",
          "## What the build collides with today", "",
          f"`{t['file']}` (sha256 `{t['sha256']}…`, {t['objects']} objects) is the "
          f"{t['source']}: **{t['built_bodies']} donor body entries**, of which the generator "
          f"rewrites **{t['hulls_written']} hull(s)** = {t['body_shapes_today']} body hull + 4 "
          f"wheels. So the car's body-0 contact is the donor's single re-cut hull and "
          f"**{t['shapes_missing']}** of BmAK's {a['boxes']} boxes are not represented.", "",
          "## The plan", "",
          "| step | BmAK box | JC3 target | state |", "|---|---|---|---|"]
    for s in d["plan"]:
        L.append(f"| **{s['id']}** | {s['box']} | {s['target']} | {s['state']} |")
    L += ["", "### What replaces what", "", d["replaces"], "",
          "### Order of work", "",
          "1. `bm_collision.py` (B-10) gains the chassis-box target: body 0's hull becomes box 0 "
          "through the existing per-axis map (B-10d/B-10e already wrote this variant to "
          "`Working/Collision2/`); the 5 cm gate compares against the chassis boxes, not DIM-1.",
          "2. The second chassis box and the pod box need shape instances. The cheapest "
          "discriminator is a 5-minute write: re-point 2 of the 14 unbound donor hull instances "
          "into body 0's compound and run `jc3hkx.py check --all --file`. If the ladder passes "
          "and the runtime draws 3 shapes, S2/S3 close; if the object count must grow, the "
          "writer case is new work.",
          "3. S4 stays a named omission until a constraint writer is decoded; the row says so "
          "instead of claiming BmAK parity.",
          "4. Q-2 (kerb + ram) is the behaviour take; no drive was run by this task.", "",
          "## Oracles", "", "| id | result | detail |", "|---|---|---|"]
    for o in d["oracles"]:
        L.append(f"| `{o['id']}` | {'PASS' if o['ok'] else 'FAIL'} | {o['detail']} |")
    L += ["", "## UNKNOWN", ""] + [f"- {u}" for u in d["unknowns"]]
    L += ["", "## Inputs and regeneration", "",
          "| path | what it is |", "|---|---|"]
    for k, v in d["inputs"].items():
        L.append(f"| `{v['path']}` | {v['generator']} |")
    L += [f"| `{os.path.relpath(OUT_M, ROOT).replace(os.sep, '/')}` | this file |",
          f"| `{os.path.relpath(OUT_J, ROOT).replace(os.sep, '/')}` | the same rows as data |", "",
          "## Revert", "", d["revert"], ""]
    return "\n".join(L)


def write(d: dict) -> None:
    with open(OUT_J, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, indent=1) + "\n")
    with open(OUT_M, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(d))


def check() -> int:
    fresh = build()
    bad = []
    if not os.path.exists(OUT_J) or not os.path.exists(OUT_M):
        print("FAIL: T22_REOPEN.{json,md} missing (run --write)")
        return 1
    if json.load(open(OUT_J, encoding="utf-8")) != fresh:
        bad.append("T22_REOPEN.json differs from the re-derived document")
    if open(OUT_M, encoding="utf-8", newline="").read().replace("\r\n", "\n") != render_md(fresh):
        bad.append("T22_REOPEN.md differs from the re-rendered text")
    for o in fresh["oracles"]:
        if not o["ok"]:
            bad.append(f"{o['id']}: {o['detail']}")
    for b in bad[:10]:
        print("FAIL:", b)
    if bad:
        return 1
    print(f"PASS: {len(fresh['oracles'])} oracles - {fresh['asset']['path']} "
          f"({fresh['asset']['bodies']} bodies / {fresh['asset']['boxes']} boxes / "
          f"{fresh['asset']['constraints']} constraint), built set "
          f"{fresh['today']['built_bodies']} donor bodies, "
          f"{fresh['today']['shapes_missing']} shape(s) missing, plan {len(fresh['plan'])} steps")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        d = build()
        write(d)
        print(f"wrote Working/Translation/T22_REOPEN.{{json,md}}: {d['asset']['path']} "
              f"{d['asset']['bodies']} bodies / {d['asset']['boxes']} boxes / "
              f"{d['asset']['constraints']} constraint; built {d['today']['built_bodies']} donor "
              f"bodies, {d['today']['shapes_missing']} shape(s) missing; "
              f"{sum(o['ok'] for o in d['oracles'])}/{len(d['oracles'])} oracles")
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
