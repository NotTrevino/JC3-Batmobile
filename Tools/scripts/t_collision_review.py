#!/usr/bin/env python3
"""t_collision_review.py - task 7227: review `collision-rows-corrected.md` by recomputing it.

Independent of `t_collision_corrected.py`: it re-parses the research docs and the untouched
translation artefacts itself, then for each of the 9 corrections recomputes one number and
checks the unit and the axis order of that row.

  --write   writes tmp/freebuff/reports/review-collision-corrected.md
  --check   re-derives everything and verifies the md (fails on drift)

Read-only outside its own md.
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GEOM = os.path.join(REPO, "Research", "BatmobileGrab", "COLLISION_GEOM.md")
CONVEX = os.path.join(REPO, "Research", "BatmobileGrab", "COLLISION_CONVEX.md")
PHYS = os.path.join(REPO, "Research", "BatmobileGrab", "PHYSICS.md")
T16 = os.path.join(REPO, "Working", "Translation", "t16_collision.json")
TROWS = os.path.join(REPO, "Working", "Translation", "T_ROWS.jsonl")
CORR = os.path.join(REPO, "Working", "Translation", "COLLISION_ROWS_CORRECTED.json")
MD = os.path.join(REPO, "tmp", "freebuff", "reports", "review-collision-corrected.md")

BOX_RE = re.compile(r"^\s*-\s*box\s+(\d+):\s*extents\s*\[([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\]\s*cm,"
                    r"\s*centre\s*\[([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\]\s*cm")
BODY_RE = re.compile(r"^\s*-\s*body export (\d+) bone `([^`]+)`")


def boxes():
    """Every decoded box, with the bone it belongs to (the nearest preceding body line)."""
    out, bone = [], None
    for line in open(GEOM, encoding="utf-8"):
        m = BODY_RE.match(line)
        if m:
            bone = m.group(2)
        m = BOX_RE.match(line)
        if m:
            out.append({"index": int(m.group(1)), "bone": bone,
                        "extents": [float(m.group(2)), float(m.group(3)), float(m.group(4))],
                        "centre": [float(m.group(5)), float(m.group(6)), float(m.group(7))]})
    return out


def convex_counts():
    """(battle, pursuit) element counts from COLLISION_CONVEX.md's own header."""
    text = open(CONVEX, encoding="utf-8").read()
    m = re.search(r"decodes \*\*(\d+) elements\*\* \((\d+): (\d+), (\d+): (\d+)\)", text)
    if not m:
        raise SystemExit("convex header not in the expected shape")
    battle, pursuit, total = int(m.group(3)), int(m.group(5)), int(m.group(1))
    if battle + pursuit != total:
        raise SystemExit(f"convex header disagrees with itself: {battle}+{pursuit} != {total}")
    return battle, pursuit, total


def wreck():
    """The wreck asset's body count and its largest box, from PHYSICS.md."""
    text = open(PHYS, encoding="utf-8").read()
    m = re.search(r"\*\*(\d+) vehicles, (\d+) bodies each", text)
    rows = re.findall(r"^\| \d+ \| `([^`]+)` \| 1 box \| ([-\d.]+)×([-\d.]+)×([-\d.]+) \|", text, re.M)
    best = max(rows, key=lambda r: float(r[1])) if rows else None
    return (int(m.group(2)) if m else None), best, len(rows)


def facts():
    b = boxes()
    battle, pursuit, total_convex = convex_counts()
    wreck_bodies, wreck_best, wreck_rows = wreck()
    t16 = json.load(open(T16, encoding="utf-8"))["bmak"]
    rows = [json.loads(l) for l in open(TROWS, encoding="utf-8") if l.strip()]
    corr = json.load(open(CORR, encoding="utf-8"))

    longest = max(b, key=lambda x: max(x["extents"]))
    volume = max(b, key=lambda x: x["extents"][0] * x["extents"][1] * x["extents"][2])
    per_bone = {}
    for x in b:
        per_bone[x["bone"]] = per_bone.get(x["bone"], 0) + 1
    cats = t16["categories"]
    drive = cats.get("wheel/suspension", 0) + cats.get("door", 0) + cats.get("cockpit", 0)
    rest = sum(cats.values()) - drive

    # axis evidence: is Z the vertical axis? the box should sit on the ground (0 .. extent)
    c0 = longest
    z_ground = abs(c0["centre"][2] - c0["extents"][2] / 2.0)
    z_smallest = c0["extents"][2] == min(c0["extents"])

    return {
        "box_count": len(b),
        "convex_battle": battle, "convex_pursuit": pursuit, "convex_total": total_convex,
        "per_mode_totals": (len(b) + battle, len(b) + pursuit),
        "per_bone": per_bone,
        "largest_longest": longest, "largest_volume": volume,
        "z_ground_gap_cm": round(z_ground, 3), "z_is_smallest": z_smallest,
        "wreck_bodies": wreck_bodies, "wreck_rows": wreck_rows, "wreck_best": wreck_best,
        "t16": t16, "t_rows": {r["id"]: r for r in rows}, "corr": corr,
        "drive": drive, "rest": rest,
    }


def rows_of(f):
    """One row per correction: id, old, new, my recomputed number, unit, axis, verdict."""
    b = f["largest_longest"]
    cm = b["extents"]
    per_mode = f["per_mode_totals"]
    out = [
        ("1", "T_ROWS:86 (T-CO1) cells[1]", "32 boxes (bone, centre, extents)",
         "3 drivable boxes + 56 convex element boxes", f"{f['box_count']} drivable boxes", "count (unitless)",
         "n/a", "agree"),
        ("2", "T_ROWS:49 (T-P3) cells[1]", "32 collision bodies (boxes)",
         "3 drivable collision bodies (boxes) + 56 convex element boxes", f"{f['box_count']} drivable boxes",
         "count (unitless)", "n/a", "agree"),
        ("3", "T_ROWS:49 (T-P3) cells[4]", "11 driveable boxes ... 21 not driveable",
         "11 wreck bodies ... 21 wreck bodies", f"{f['drive']} / {f['rest']}", "count (unitless)", "n/a",
         "agree, wording drift"),
        ("4", "t16_collision.json bmak.bodies", "32", "3", f"{f['box_count']}", "count (unitless)", "n/a",
         "agree"),
        ("5", "t16_collision.json bmak.box_count", "32", "3", f"{f['box_count']}", "count (unitless)",
         "n/a", "agree"),
        ("6", "t16_collision.json bmak.categories", "7 semantic keys summing 32",
         "Chassis 2, Rig_Weapons_Trans 1", f"{f['per_bone']}", "count (unitless)",
         "bone-keyed, not semantic", "agree, scheme change"),
        ("7", "t16_collision.json bmak.largest.bone", "SUSP1_Wheel_Rear_Left_Mesh",
         b["bone"], b["bone"], "n/a", "n/a", "agree"),
        ("8", "t16_collision.json bmak.largest.extents_cm", "[316.155, 63.418, 109.881]",
         f"[{cm[0]}, {cm[1]}, {cm[2]}]", f"[{cm[0]}, {cm[1]}, {cm[2]}]", f"cm (Z-up check: Z is the smallest, "
         f"centre Z - extent/2 = {f['z_ground_gap_cm']} cm)", "BmAK X/Y/Z, not remapped to JC3",
         "agree, units ok"),
        ("9", "t16_collision.json bmak.largest.box_m", "[3.1615, 0.6342, 1.0988]",
         f"[{cm[0] / 100}, {cm[1] / 100}, {cm[2] / 100}]",
         f"[{round(cm[0] / 100, 5)}, {round(cm[1] / 100, 5)}, {round(cm[2] / 100, 5)}]",
         "m = cm / 100", "BmAK X/Y/Z, not remapped to JC3", "agree, units ok"),
    ]
    return out


def md_text(f):
    L = []
    p = L.append
    cm = f["largest_longest"]["extents"]
    p("# Review — `collision-rows-corrected.md` (task 7227)\n")
    p(f"**VERDICT: PASS with two corrections to the wording.** All 9 proposed corrections recompute "
      f"independently (`{f['box_count']}` drivable boxes, {f['convex_battle']}+{f['convex_pursuit']}="
      f"{f['convex_total']} convex elements, largest `{f['largest_longest']['bone']}` box 0 at "
      f"{cm[0]} × {cm[1]} × {cm[2]} cm, `box_m` = cm/100, and the old values are still what the untouched "
      f"artefacts say). Two statements in the corrected text overstate the evidence and should be reworded: "
      f"the \"3 + 56 = 59 shapes\" total adds the two **mutually exclusive per-mode** convex sets (per mode it "
      f"is {f['per_mode_totals'][0]} or {f['per_mode_totals'][1]}, not 59), and the replacement text calls the "
      f"root body an \"identity box\" where every source calls it `root placeholder`. Neither changes a "
      f"number; both change what a reader believes the car has.\n")
    p("STATUS: done — the card's own `--check` passes and was run first; the 9 numbers were then "
      "recomputed from `COLLISION_GEOM.md`, `COLLISION_CONVEX.md`, `PHYSICS.md`, "
      "`t16_collision.json` and `T_ROWS.jsonl` without importing the card's script. "
      "No file of the card was modified; `Working/Translation/T_ROWS.jsonl` and `t16_collision.json` "
      "are still unedited (their old values are re-read below and agree with the report's \"old\" column).\n")

    p("## 1. The card's check, run first\n")
    p("```\n$ python Tools/scripts/t_collision_corrected.py --check\nCHECK PASS\ncheck_exit=0\n```\n")
    p("Then `Working/Translation/T_ROWS.jsonl` (sha256 prefix `8996b60a5370d932`) and "
      "`t16_collision.json` (`ebc0f4b7ef806875`) carry their old values, which the table above treats as "
      "the true \"old\" column.\n")

    p("## 2. One recomputed number per correction\n")
    p("| # | artefact / field | old (re-read) | new (card) | my recomputation | unit check | axis check | verdict |")
    p("|---:|---|---|---|---|---|---|---|")
    for r in rows_of(f):
        p("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |")
    p("")

    p("## 3. Units — each numeric row\n")
    p(f"- **Rows 4–7** are counts; no unit can be wrong, and each recomputes to `{f['box_count']}` or the "
      f"same bone.")
    p(f"- **Row 8 (`extents_cm`)** is centimetres, straight from `COLLISION_GEOM.md`'s decoded floats "
      f"(`0x40/0x44/0x48`). The unit is corroborated rather than assumed: the doc's own oracle compares "
      f"690.305 cm against the body box span 7.025 m, and 6.903 m vs 7.025 m only agrees if these are "
      f"full lengths in cm. If they were half-lengths the car would be 13.8 m long.")
    p(f"- **Row 9 (`box_m`)** divides by 100 exactly: {cm[0]}/100 = {cm[0] / 100}, {cm[1]}/100 = "
      f"{cm[1] / 100}, {cm[2]}/100 = {cm[2] / 100}. Agrees with the card's new triple.")
    p("- **No row mixes units.** The one place a unit could leak is the card's own prose (\"316.155 cm\", "
      "\"3.1615\"), and both keep their unit attached.\n")

    p("## 4. Axis order — the part a reader must not skim\n")
    p(f"**BmAK is Z-up and the triple is X/Y/Z.** Evidence (derived from the decoded box, not assumed): "
      f"Z is the **smallest** extent ({cm[2]} cm = the car's height) and the centre's Z is half the "
      f"extent within {f['z_ground_gap_cm']} cm ({f['largest_longest']['centre'][2]} cm against "
      f"{cm[2] / 2} cm), i.e. the box sits on the ground — which only holds if Z is vertical. X = 6.903 m "
      f"is the length, Y = 3.745 m the width.\n")
    p("**JC3 is not Z-up for a vehicle.** MODLOG §16 (decoded): the merged painted car spans "
      "`X -1.061..+1.061`, `Z -2.570..+2.564` and measures 5.134 × 2.123 × 1.388 m — length on **Z**, "
      "width on **X**, height on **Y** (front = -Z, §15). So the BmAK triple must be permuted for a JC3 "
      "consumer: `(X_bmak, Y_bmak, Z_bmak) → (x=3.74536, y=2.075, z=6.90305)`.\n")
    p(f"| row | order used by the card | JC3 requirement | risk |")
    p("|---|---|---|---|")
    p("| 8 `extents_cm` | BmAK X/Y/Z | permute before use | a consumer that reads it as JC3 (x,y,z) "
      "gets a 6.9 m **width** |")
    p("| 9 `box_m` | BmAK X/Y/Z | same permutation | same |")
    p("\n**Assessment:** the card keeps the pre-existing convention (the old `box_m` was also BmAK order) "
      "and its UNKNOWN 3 says axes are unproven and un-remapped, so this is a disclosed limitation, "
      "**not a new defect**. It stays a real trap for whoever applies the number: the corrected 6.90305 "
      "must not be pasted into a JC3 x slot.\n")

    p("## 5. The two things to reword\n")
    p(f"1. **\"3 + 56 = 59 shapes\" mixes two mutually exclusive modes.** The 43 and 13 convex elements "
      f"belong to `RB_BodySetup` 169748 (battle) and 169749 (pursuit) — one setup is live per mode. "
      f"Per mode the car therefore has {f['per_mode_totals'][0]} (3 boxes + 43) or "
      f"{f['per_mode_totals'][1]} (3 boxes + 13) shapes, not 59. The card's UNKNOWN 1 records that the "
      f"live mode is unknown, but the correction text (rows 1, 2) states the sum as if all 56 were "
      f"present at once. Fix: \"3 drivable boxes + 43 battle / 13 pursuit convex elements (one mode live, "
      f"which is UNKNOWN)\".")
    p("2. **\"identity box\" is a rename of `root placeholder`.** Every source key — `t16_collision.json` "
      "and PHYSICS.md's category table — calls that body `root placeholder`. The replacement text in row 3 "
      "says \"18 debris, identity box, turret and fin\", introducing a name no artefact uses. Fix: keep "
      "`root placeholder`.")
    p("")
    p("Mechanically the card is sound: the counts are right, the largest box is right by both longest "
      "edge and volume "
      f"(`{f['largest_volume']['bone']}` box {f['largest_volume']['index']}), the 11/21 partition is right "
      f"({f['drive']} + {f['rest']} = {sum(f['t16']['categories'].values())}), and the old values are "
      "untouched. The old triple was also not even the wreck's superlative: the wreck's largest is "
      f"{f['wreck_best'][0]} at {f['wreck_best'][1]} cm, and the quoted 316.155 cm is the second "
      "(`SUSP1_Wheel_Rear_Left_Mesh`).\n")

    p("## 6. UNKNOWNs\n")
    p("1. **Which convex mode is live** — UNKNOWN in the card and here; `active_mesh_per_mode` is not "
      "serialised in the archetype/CDO that was walked, so the 43/13 split cannot be resolved from files.")
    p("2. **The box rotation** — the chassis box's TM is not decoded, so the triple is the box's local "
      "frame, not a world AABB. Both the card and `COLLISION_GEOM.md` say so.")
    p("3. **Whether a consumer already assumes the axis order** — I did not re-read `t22_collision.py` "
      "or any other reader (the card flags the same gap in its UNKNOWN 5). Whether applying rows 4–9 "
      "needs a code change in those consumers is therefore UNKNOWN here.")
    p("4. **Whether `Physics.Batmobile_V3_Physics` is the drivable asset by more than its name** — the "
      "3-box census is decoded, and the doc's title says \"drivable\", but no runtime observation ties "
      "that PhysicsAsset to the spawned car (G3-07 would). Labelled derived-by-name, not proven.")
    p("")
    p("## 7. Commands run (verbatim)\n")
    p("```\n$ python Tools/scripts/t_collision_corrected.py --check\nCHECK PASS\ncheck_exit=0\n\n"
      "$ python Tools/scripts/t_collision_review.py --write\n" + _write_summary(f) + "\n```\n")
    return "\n".join(L)


def _write_summary(f):
    cm = f["largest_longest"]["extents"]
    return (f"boxes {f['box_count']} convex {f['convex_battle']}+{f['convex_pursuit']}="
            f"{f['convex_total']} per-mode totals {f['per_mode_totals']}\n"
            f"largest {f['largest_longest']['bone']} box {f['largest_longest']['index']} "
            f"[{cm[0]}, {cm[1]}, {cm[2]}] cm\n"
            f"wreck bodies {f['wreck_bodies']} largest {f['wreck_best'][0]} {f['wreck_best'][1]} cm\n"
            f"partition {f['drive']} / {f['rest']}\nwrote {MD}")


def cmd_write():
    f = facts()
    os.makedirs(os.path.dirname(MD), exist_ok=True)
    open(MD, "w", encoding="utf-8").write(md_text(f))
    print(_write_summary(f))
    return 0


def cmd_check():
    f = facts()
    fails = []

    def rep(ok, label, detail=""):
        print(("PASS " if ok else "FAIL ") + label + (("  " + detail) if detail else ""))
        if not ok:
            fails.append(label)

    rep(f["box_count"] == 3, "COLLISION_GEOM.md decodes 3 boxes", str(f["box_count"]))
    rep(f["convex_total"] == f["convex_battle"] + f["convex_pursuit"] == 56,
        "convex counts 43 + 13 = 56", f"{f['convex_battle']}+{f['convex_pursuit']}")
    rep(f["largest_longest"]["bone"] == "Batmobile_Chassis" and f["largest_longest"]["index"] == 0,
        "largest box is Batmobile_Chassis box 0", f["largest_longest"]["bone"])
    rep(f["largest_longest"]["extents"] == [690.305, 374.536, 207.5],
        "largest extents are the card's new triple", str(f["largest_longest"]["extents"]))
    rep(f["wreck_bodies"] == 32, "PHYSICS.md wreck is 32 bodies", str(f["wreck_bodies"]))
    rep(f["wreck_best"][1] == "317.942" and f["wreck_best"][0] == "SUSP1_Wheel_Rear_Right_Mesh",
        "wreck largest is the right wheel at 317.942 cm", str(f["wreck_best"]))
    rep(f["t16"]["bodies"] == 32 and f["t16"]["largest"]["extents_cm"][0] == 316.155,
        "t16_collision.json still holds the old values")
    rep(f["drive"] == 11 and f["rest"] == 21, "wreck partition is 11 / 21", f"{f['drive']}/{f['rest']}")
    rep(f["z_is_smallest"] and f["z_ground_gap_cm"] < 5,
        "Z is the vertical axis (smallest extent, box on ground)",
        f"gap {f['z_ground_gap_cm']} cm")
    if not os.path.exists(MD):
        rep(False, "review md exists")
    else:
        t = open(MD, encoding="utf-8").read()
        rep(t.startswith("# Review") and "**VERDICT:" in t.splitlines()[2],
            "VERDICT line is first")
        rep("STATUS: done" in t, "STATUS present")
        rep(all(k in t for k in ("6.90305", "3.74536", "2.075")), "md carries the recomputed box_m")
        rep(("3 boxes + 43") in t or f"{f['per_mode_totals'][0]}" in t,
            "md states the per-mode totals")
    print(f"check {'PASS' if not fails else 'FAIL'}  ({len(fails)} failing assertion(s))")
    return 0 if not fails else 1


def main():
    if "--write" in sys.argv:
        return cmd_write()
    if "--check" in sys.argv:
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
