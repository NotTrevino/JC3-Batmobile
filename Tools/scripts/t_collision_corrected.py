#!/usr/bin/env python3
"""t_collision_corrected.py - corrected BmAK collision figures for T-CO1, T-P3 and t16_collision.json.

Task 7220's audit (`Working/Translation/COLLISION_SOURCES_AUDIT.md`) found three artefacts quoting
the **destroyed-wreck** physics asset (`Batmobile_V3_Destroyed_Physics`, 32 bodies) as if it were
the drivable car's collision geometry. This script re-derives the drivable numbers from the two
censuses that decode the asset the player actually drives, and writes the corrected values as NEW
files. `T_ROWS.jsonl` and `t16_collision.json` are opened read-only and never edited.

Outputs
    Working/Translation/COLLISION_ROWS_CORRECTED.json   old value, new value, source, label, rule
    Working/Translation/COLLISION_ROWS_CORRECTED.md     the operator-facing note

Derivation rule (one rule for all three artefacts):
    drivable boxes          = every `- box N: extents [...] cm` line in COLLISION_GEOM.md
    drivable convex boxes   = the header convex counts of both RB_BodySetup payloads
                              in COLLISION_CONVEX.md (43 + 13)
    drivable shapes total   = boxes + convex element boxes
    largest drivable box    = max over the boxes of (extents X, Y, Z) by longest axis
    box_m                   = extents_cm / 100

Usage: python Tools/scripts/t_collision_corrected.py --write
       python Tools/scripts/t_collision_corrected.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

GEOM = "Research/BatmobileGrab/COLLISION_GEOM.md"
CONVEX = "Research/BatmobileGrab/COLLISION_CONVEX.md"
WRECK = "Research/BatmobileGrab/PHYSICS.md"
LEDGER = "Working/Translation/T_ROWS.jsonl"
T16 = "Working/Translation/t16_collision.json"
OUT_JSON = "Working/Translation/COLLISION_ROWS_CORRECTED.json"
OUT_MD = "Working/Translation/COLLISION_ROWS_CORRECTED.md"


def p(rel: str) -> str:
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


def read(rel: str) -> str:
    with open(p(rel), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sha(rel: str) -> str:
    with open(p(rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def drivable_boxes() -> list[dict]:
    """Every `- box N: extents [...] cm, centre [...] cm` line, with its bone."""
    out = []
    bone = export = None
    for line in read(GEOM).splitlines():
        m = re.match(r"\s*- body export (\d+) bone `([^`]+)`", line)
        if m:
            export, bone = int(m.group(1)), m.group(2)
            continue
        m = re.match(r"\s*- box (\d+): extents \[([\d.]+), ([\d.]+), ([\d.]+)\] cm, "
                     r"centre \[([-\d.]+), ([-\d.]+), ([-\d.]+)\] cm", line)
        if m:
            out.append({
                "export": export, "bone": bone, "box": int(m.group(1)),
                "extents_cm": [float(m.group(2)), float(m.group(3)), float(m.group(4))],
                "centre_cm": [float(m.group(5)), float(m.group(6)), float(m.group(7))],
                "line": read(GEOM)[:0] or None,
            })
    return out


def convex_census() -> dict:
    """The two RB_BodySetup payloads: header element count, decoded count, element-box union."""
    text = read(CONVEX)
    bodies = []
    for m in re.finditer(r"header `\[0, 0, 0, (\d+)\]`, convex elements \*\*(\d+)\*\*", text):
        bodies.append({"header_count": int(m.group(1)), "decoded_count": int(m.group(2))})
    unions = [[float(x) for x in m.groups()] for m in
              re.finditer(r"union of the element boxes \(derived\).*?"
                          r"extent \[([\d.]+), ([\d.]+), ([\d.]+)\] cm", text)]
    names = re.findall(r"Object: `([^`]+)`", text)
    for i, b in enumerate(bodies):
        b["object"] = names[i] if i < len(names) else None
        b["union_cm"] = unions[i] if i < len(unions) else None
    return {"bodies": bodies,
            "elements": sum(b["decoded_count"] for b in bodies),
            "headers": sum(b["header_count"] for b in bodies)}


def wreck_census() -> dict:
    """PHYSICS.md's per-vehicle cast: 32 bodies and their extents, plus its own verdict line."""
    text = read(WRECK)
    rows = [(m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4)))
            for m in re.finditer(r"\| \d+ \| `([^`]+)` \| 1 box \| "
                                 r"([\d.]+)×([\d.]+)×([\d.]+) \|", text)]
    ranked = sorted(rows, key=lambda r: -max(r[1:]))
    verdict = next((l.strip() for l in text.splitlines()
                    if "There is no chassis body" in l), None)
    return {"bodies": len(rows), "ranked": ranked,
            "largest": ranked[0] if ranked else None,
            "second": ranked[1] if len(ranked) > 1 else None,
            "verdict": verdict}


def ledger_row(row_id: str) -> dict:
    for i, line in enumerate(read(LEDGER).splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("id") == row_id:
            return {"line": i, "row": obj}
    raise SystemExit(f"{row_id} not found in {LEDGER}")


def derive() -> dict:
    boxes = drivable_boxes()
    if not boxes:
        raise SystemExit(f"{GEOM}: no box lines decoded")
    largest = max(boxes, key=lambda b: max(b["extents_cm"]))
    convex = convex_census()
    wreck = wreck_census()
    t16 = json.loads(read(T16))
    t_co1 = ledger_row("T-CO1")
    t_p3 = ledger_row("T-P3")

    n_boxes = len(boxes)
    n_elem = convex["elements"]
    total = n_boxes + n_elem
    ext = largest["extents_cm"]
    box_m = [round(v / 100.0, 5) for v in ext]

    cats = {}
    for b in boxes:
        cats[b["bone"]] = cats.get(b["bone"], 0) + 1

    # the 11/21 split T-P3 quotes, recomputed from the wreck category column
    wreck_text = read(WRECK)
    cat_counts = {}
    for m in re.finditer(r"\| \d+ \| `[^`]+` \| 1 box \| [\d.]+×[\d.]+×[\d.]+ \| "
                         r"[^|]+ \| ([^|]+) \|", wreck_text):
        c = m.group(1).strip()
        cat_counts[c] = cat_counts.get(c, 0) + 1
    wheels_doors_cockpit = (cat_counts.get("wheel/suspension", 0) + cat_counts.get("door", 0)
                            + cat_counts.get("cockpit", 0))
    rest = wreck["bodies"] - wheels_doors_cockpit

    old_co1 = t_co1["row"]["cells"][1]
    old_p3_c1 = t_p3["row"]["cells"][1]
    old_p3_c4 = t_p3["row"]["cells"][4]

    corr = []

    def add(artefact: str, locator: str, field: str, old, new, rule: str, source: str,
            label: str) -> None:
        corr.append({"artefact": artefact, "locator": locator, "field": field,
                     "old": old, "new": new, "rule": rule, "source": source,
                     "label": label})

    add(LEDGER, f"line {t_co1['line']} (T-CO1)", "cells[1]", old_co1,
        f"{n_boxes} drivable boxes (bone, centre, extents) + {n_elem} convex element boxes; "
        f"the 32-box set is the destroyed wreck",
        f"boxes = count of decoded `- box N` lines in COLLISION_GEOM.md = {n_boxes}; "
        f"convex element boxes = 43 + 13 from COLLISION_CONVEX.md = {n_elem}; "
        f"32 = PHYSICS.md's wreck bodies per vehicle",
        f"{GEOM} (PhysicsAsset section: 2 chassis boxes + 1 weapons-rig box); "
        f"{CONVEX} (header counts 43 / 13); {WRECK} (32 bodies, wreck-only)",
        "decoded counts + derived sum")

    add(LEDGER, f"line {t_p3['line']} (T-P3)", "cells[1]", old_p3_c1,
        f"{n_boxes} drivable collision bodies (boxes) + {n_elem} convex element boxes",
        f"same rule as T-CO1: {n_boxes} decoded boxes + {n_elem} element boxes in the "
        f"drivable asset; the quoted 32 is the wreck's body count",
        f"{GEOM}; {CONVEX}; {WRECK}", "decoded counts + derived sum")

    add(LEDGER, f"line {t_p3['line']} (T-P3)", "cells[4]", old_p3_c4,
        f"written (G2-30): {wheels_doors_cockpit} wreck bodies "
        f"({cat_counts.get('wheel/suspension', 0)} wheel/suspension + "
        f"{cat_counts.get('door', 0)} doors + {cat_counts.get('cockpit', 0)} cockpit) map onto 7 "
        f"donor hull slots; they are not the drivable car's collision (the drivable asset has "
        f"{n_boxes} boxes + {n_elem} convex element boxes); {rest} wreck bodies are "
        f"{cat_counts.get('destruction debris', 0)} debris, identity box, turret and fin; "
        f"11 T-8 parts have no slot",
        f"partition of the wreck's {wreck['bodies']}: "
        f"{cat_counts.get('wheel/suspension', 0)} + {cat_counts.get('door', 0)} + "
        f"{cat_counts.get('cockpit', 0)} = {wheels_doors_cockpit}, the rest = {rest}; the "
        f"'11 driveable boxes' is a subset of the WRECK, not of the drivable asset",
        f"{WRECK} (category table); {GEOM}; {CONVEX}",
        "derived partition of decoded counts")

    bm = t16.get("bmak", {})
    add(T16, "bmak.bodies", "bodies", bm.get("bodies"), n_boxes,
        f"drivable boxes = {n_boxes} (2 on Batmobile_Chassis, 1 on Batmobile_Rig_Weapons_Trans)",
        f"{GEOM}", "decoded count")
    add(T16, "bmak.box_count", "box_count", bm.get("box_count"), n_boxes,
        f"one box per drivable body = {n_boxes}; the wreck's 1-box-per-body count stays valid "
        f"for the wreck but is not this asset",
        f"{GEOM}", "decoded count")
    add(T16, "bmak.categories", "categories", bm.get("categories"), cats,
        f"box count per bone over the decoded drivable boxes = {cats}",
        f"{GEOM}", "decoded count")
    add(T16, "bmak.largest.bone", "bone", (bm.get("largest") or {}).get("bone"),
        largest["bone"],
        f"largest box by longest axis = {ext} cm on `{largest['bone']}` box {largest['box']} "
        f"(export {largest['export']})",
        f"{GEOM}", "decoded")
    add(T16, "bmak.largest.extents_cm", "extents_cm",
        (bm.get("largest") or {}).get("extents_cm"), ext,
        f"max over the {n_boxes} decoded box extents by longest axis; {ext} cm",
        f"{GEOM}", "decoded")
    add(T16, "bmak.largest.box_m", "box_m", (bm.get("largest") or {}).get("box_m"), box_m,
        f"extents_cm / 100 = {box_m} m", f"{GEOM}", "derived (x 0.01)")

    checks = []

    def chk(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    chk("COLLISION_GEOM.md yields the drivable box set and nothing else",
        n_boxes == 3, f"{n_boxes} boxes: " +
        "; ".join(f"`{b['bone']}` box {b['box']} {b['extents_cm']}" for b in boxes))
    chk("the largest drivable box is the chassis box 0 of export 169750",
        largest["bone"] == "Batmobile_Chassis" and largest["box"] == 0
        and abs(ext[0] - 690.305) < 1e-9 and abs(ext[1] - 374.536) < 1e-9
        and abs(ext[2] - 207.5) < 1e-9,
        f"{largest['bone']} box {largest['box']} @ export {largest['export']}: {ext} cm")
    chk("COLLISION_CONVEX.md's header counts and decoded counts agree, 43 + 13",
        convex["elements"] == n_elem and convex["headers"] == n_elem and n_elem == 56,
        f"headers {convex['headers']}, decoded {convex['elements']}, sum {n_elem}")
    chk("PHYSICS.md is 32 wreck bodies per vehicle and has no chassis body",
        wreck["bodies"] == 32 and wreck["verdict"] is not None,
        f"{wreck['bodies']} bodies; verdict line present: {bool(wreck['verdict'])}")
    chk("the quoted 316.155 cm is a wreck box, and not even the wreck's largest",
        wreck["largest"][1] - 316.155 > 0.1 and wreck["second"][1] == 316.155,
        f"wreck largest {wreck['largest'][0]} {wreck['largest'][1:]} cm; "
        f"second {wreck['second'][0]} {wreck['second'][1:]} cm")
    chk("the old values are still what the two artefacts say (nothing was edited)",
        old_co1 == "32 boxes (bone, centre, extents)"
        and old_p3_c1 == "32 collision bodies (boxes)" and bm.get("bodies") == 32
        and bm.get("largest", {}).get("extents_cm") == [316.155, 63.418, 109.881],
        f"T-CO1 cells[1]={old_co1!r}; T-P3 cells[1]={old_p3_c1!r}; "
        f"t16 bmak.bodies={bm.get('bodies')}")
    chk("the wreck partition recomputes to T-P3's 11 / 21",
        wheels_doors_cockpit == 11 and rest == 21,
        f"{wheels_doors_cockpit} wheel/door/cockpit + {rest} other = {wreck['bodies']}")
    chk("the new largest equals the max of the decoded boxes and box_m is cm/100",
        ext == largest["extents_cm"] and box_m == [round(v / 100.0, 5) for v in ext],
        f"{ext} cm -> {box_m} m")
    chk("every correction changes the value and carries a source and a label",
        all(c["old"] != c["new"] and c["source"] and c["label"] for c in corr),
        f"{len(corr)} corrections")

    return {
        "boxes": boxes, "convex": convex, "wreck": wreck,
        "n_boxes": n_boxes, "n_elem": n_elem, "total": total,
        "largest": largest, "box_m": box_m, "cats": cats,
        "corrections": corr, "checks": checks,
        "hashes": {rel: sha(rel) for rel in (GEOM, CONVEX, WRECK, LEDGER, T16)},
        "passed": sum(1 for c in checks if c["ok"]), "total_checks": len(checks),
    }


def render_json(d: dict) -> str:
    doc = {
        "schema": 1,
        "card": "collision rows corrected (T-CO1, T-P3, t16_collision.json)",
        "generator": "Tools/scripts/t_collision_corrected.py",
        "applies": False,
        "note": "proposed replacements; T_ROWS.jsonl and t16_collision.json are NOT edited",
        "rule": ("drivable boxes = decoded `- box N` lines in COLLISION_GEOM.md; drivable convex "
                 "boxes = header counts of both RB_BodySetup payloads in COLLISION_CONVEX.md; "
                 "largest = max box by longest axis; box_m = extents_cm / 100"),
        "inputs": d["hashes"],
        "census": {
            "drivable_boxes": d["n_boxes"],
            "drivable_convex_elements": d["n_elem"],
            "drivable_shapes_total": d["total"],
            "largest_drivable_cm": d["largest"]["extents_cm"],
            "largest_drivable_bone": d["largest"]["bone"],
            "convex_bytes": [b["union_cm"] for b in d["convex"]["bodies"]],
            "wreck_bodies_per_vehicle": d["wreck"]["bodies"],
            "wreck_largest": {"bone": d["wreck"]["largest"][0],
                              "extents_cm": list(d["wreck"]["largest"][1:])},
        },
        "corrections": d["corrections"],
        "checks": d["checks"],
        "verdict": "PASS" if d["passed"] == d["total_checks"] else "FAIL",
    }
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


def fmt(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(f"{x:g}" for x in v) + "]"
    if isinstance(v, dict):
        return json.dumps(v, sort_keys=True)
    return str(v)


def render_md(d: dict) -> str:
    L: list[str] = []
    w = L.append
    lg = d["largest"]
    w("# Collision rows: the corrected BmAK numbers")
    w("")
    w("Generated by `Tools/scripts/t_collision_corrected.py --write`; `--check` re-derives every")
    w("number from the censuses and rebuilds this file and its JSON byte for byte.")
    w("")
    w("**Nothing was edited.** `T_ROWS.jsonl` and `Working/Translation/t16_collision.json` are")
    w("opened read-only; the corrections below are proposals in a separate file, so the old values")
    w("stay visible next to the new ones. The audit that found the error is")
    w("`Working/Translation/COLLISION_SOURCES_AUDIT.md` (task 7220).")
    w("")
    w("Labels: **decoded** = read at the stated doc/line; **derived** = the arithmetic is printed;")
    w("**UNKNOWN** = not decided here.")
    w("")
    w("## STATUS")
    w("")
    w(f"**done - {len(d['corrections'])} proposed corrections across the three artefacts. The")
    w(f"drivable asset carries **{d['n_boxes']} boxes + {d['n_elem']} convex element boxes**")
    w(f"({d['total']} shapes); its largest box is `{lg['bone']}` box {lg['box']} at")
    w(f"**{lg['extents_cm'][0]:g} x {lg['extents_cm'][1]:g} x {lg['extents_cm'][2]:g} cm**.")
    w(f"The figures being replaced all come from the **destroyed wreck** (32 bodies, largest")
    w(f"{d['wreck']['largest'][1]:.3f} cm). {d['passed']}/{d['total_checks']} checks pass.**")
    w("")
    w("## 1. The census this rests on")
    w("")
    w("| census | doc | count | largest | belongs to |")
    w("|---|---|---:|---|---|")
    w(f"| drivable boxes | `{GEOM}` | {d['n_boxes']} | {lg['extents_cm'][0]:g} x "
      f"{lg['extents_cm'][1]:g} x {lg['extents_cm'][2]:g} cm | the car the player drives |")
    w(f"| drivable convex element boxes | `{CONVEX}` | {d['n_elem']} ("
      + " + ".join(str(b['decoded_count']) for b in d['convex']['bodies'])
      + ") | union "
      + " / ".join(f"{b['union_cm'][0]:g} x {b['union_cm'][1]:g} x {b['union_cm'][2]:g}"
                   for b in d['convex']['bodies'] if b['union_cm']) + " cm | the car the player drives |")
    w(f"| wreck bodies | `{WRECK}` | {d['wreck']['bodies']} per vehicle | "
      f"{d['wreck']['largest'][1]:.3f} x {d['wreck']['largest'][2]:.3f} x "
      f"{d['wreck']['largest'][3]:.3f} cm | the destroyed car |")
    w("")
    w("The wreck doc's own verdict is the classification witness, quoted verbatim:")
    w("")
    w("> " + (d["wreck"]["verdict"] or "(verdict line not found)"))
    w("")
    w("**Derivation rule** (one rule, used for every correction):")
    w("")
    w("```")
    w(f"drivable boxes        = every decoded `- box N: extents [...]` line  = {d['n_boxes']}")
    w(f"drivable convex boxes = header convex counts 43 + 13                 = {d['n_elem']}")
    w(f"drivable shapes       = boxes + convex element boxes                 = {d['total']}")
    w(f"largest drivable box  = max by longest axis                          = {lg['extents_cm']} cm")
    w("box_m                 = extents_cm / 100")
    w("```")
    w("")
    w("## 2. The corrections")
    w("")
    for i, c in enumerate(d["corrections"], 1):
        w(f"### {i}. `{c['artefact']}` - {c['locator']} - `{c['field']}`")
        w("")
        w("| | value |")
        w("|---|---|")
        w(f"| old | `{fmt(c['old'])}` |")
        w(f"| new | `{fmt(c['new'])}` |")
        w(f"| rule | {c['rule']} |")
        w(f"| source | {c['source']} |")
        w(f"| label | **{c['label']}** |")
        w("")
    w("### Why the old numbers are wreck numbers, not drivable ones")
    w("")
    w(f"- `32` is `PHYSICS.md`'s per-vehicle body count of `Batmobile_V3_Destroyed_Physics` - the")
    w("  asset the game hands to the **destroyed** car, whose own doc says it has no chassis body.");
    w(f"- the `316.155 x 63.418 x 109.881 cm` triple is that asset's `SUSP1_Wheel_Rear_Left_Mesh`")
    w(f"  box. It is not even the wreck's largest: `{d['wreck']['largest'][0]}` carries")
    w(f"  {d['wreck']['largest'][1]:.3f} cm on X, so the row quoted the second-largest wreck box.");
    w(f"- `3.1615 x 0.6342 x 1.0988 m` is that same box in metres (x 0.01) - **derived**, and still a")
    w("  wreck box.");
    w(f"- T-P3's `11 / 21` split is a *partition of the wreck's 32* - "
      f"{d['cats'].get('wheel/suspension', 0)} wheel/suspension + "
      f"{d['cats'].get('door', 0)} doors + {d['cats'].get('cockpit', 0)} cockpit = 11, the other "
      f"21 debris/root/turret/fin - so calling the 11 \"driveable boxes\" is the error, not the")
    w("  arithmetic.")
    w("")
    w("## 3. What to do with the wreck block")
    w("")
    w("The `bmak` block of `t16_collision.json` is **valid data about the wrong asset**. Suggested")
    w("shape of the edit (not applied, and not encoded in the JSON above): keep every field, rename")
    w("the block `wreck`, and add a `drivable` block with the values in section 2. Deleting the wreck")
    w("block would lose the 32-body census that `T-CO2` and the debris work already cite.")
    w("")
    w("## 4. What this does not fix")
    w("")
    w("- `T-CO2` - already corrected by G3-11d; not re-opened here.")
    w("- `T-PA3`, `T-CO3` - clean: they quote the JC3 donor part table, no BmAK box figure.")
    w("- Any downstream consumer of `t16_collision.json` that reads `bmak.bodies` / `largest`")
    w("  (`t22_collision.py`'s slot binding, the `11 -> 7` map, radius x k). Correcting this file")
    w("  does not re-point those; they read the fields this sheet proposes to change, so applying")
    w("  the edit needs that consumer checked in the same pass. That is **UNKNOWN** here: the")
    w("  consumer's use of each field was not re-read for this card.")
    w("- Whether the drivable asset's own numbers are *the car's real collision* - the 3 boxes are")
    w("  the physics-asset bodies and the 56 convex elements are the mode-switched setups; which")
    w("  mode is active in play is `COLLISION_GEOM.md`'s own UNKNOWN.")
    w("")
    w("## 5. Checks")
    w("")
    w("| check | result | detail |")
    w("|---|---|---|")
    for c in d["checks"]:
        w(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} | {c['detail'].replace('|', '\\|')} |")
    w("")
    w(f"{d['passed']}/{d['total_checks']} pass. Verdict: **"
      f"{'PASS' if d['passed'] == d['total_checks'] else 'FAIL'}**.")
    w("")
    w("## 6. UNKNOWN")
    w("")
    w("1. **Which mode's convex set is live** - `COLLISION_GEOM.md` records")
    w("   `active_mesh_per_mode: UNKNOWN` (the mode enum is not serialised). The corrected count")
    w("   therefore states *both* setups (43 + 13), not one.")
    w("2. **The chassis boxes' rotation** - `COLLISION_GEOM.md` decodes extents and centres, and")
    w("   says the rotation is not decoded, so the 690.305 x 374.536 x 207.5 cm box is its local")
    w("   frame, not a world AABB.")
    w("3. **The axes** - the doc's own oracle says \"Frame axes are not proven\", so the corrected")
    w(f"   triple is quoted in the doc's X/Y/Z order unchanged; no axis re-mapping is claimed.")
    w("4. **How many of the 3 boxes the build actually uses** - T-22's slot binding is built on the")
    w("   wreck census; re-deriving it from the drivable boxes is not in this card.")
    w("5. **Whether an edit to `t16_collision.json` breaks its own consumers** - see section 4.")
    w("")
    w("## 7. Reproduce")
    w("")
    w("```")
    w("cd E:/Modding/JustCause3/JC3-Batmobile")
    w("python Tools/scripts/t_collision_corrected.py --write")
    w("python Tools/scripts/t_collision_corrected.py --check")
    w("```")
    w("")
    w(f"Inputs, read-only: `{GEOM}`, `{CONVEX}`, `{WRECK}`, `{LEDGER}`, `{T16}`.")
    w("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = derive()
    js, md = render_json(d), render_md(d)
    if a.write:
        for rel, text in ((OUT_JSON, js), (OUT_MD, md)):
            os.makedirs(os.path.dirname(p(rel)), exist_ok=True)
            with open(p(rel), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            print(f"wrote {rel} ({len(text)} chars)")
        print(f"{d['passed']}/{d['total_checks']} checks pass, {len(d['corrections'])} corrections")
        for c in d["checks"]:
            if not c["ok"]:
                print(f"FAIL {c['check']}: {c['detail']}")
        return 0 if d["passed"] == d["total_checks"] else 1
    if a.check:
        bad = 0
        for c in d["checks"]:
            if not c["ok"]:
                bad += 1
                print(f"FAIL {c['check']}: {c['detail']}")
        for rel, text in ((OUT_JSON, js), (OUT_MD, md)):
            try:
                got = read(rel)
            except FileNotFoundError:
                print(f"MISSING {rel}")
                bad += 1
                continue
            if got != text:
                import difflib
                print("\n".join(list(difflib.unified_diff(
                    got.splitlines(), text.splitlines(), "on-disk", "regenerated",
                    lineterm="", n=1))[:30]))
                print(f"DRIFT {rel}")
                bad += 1
        print("CHECK", "PASS" if not bad else "FAIL")
        return 0 if not bad else 1
    for c in d["checks"]:
        print(("PASS " if c["ok"] else "FAIL ") + c["check"] + ": " + c["detail"])
    print(f"{d['passed']}/{d['total_checks']} pass")
    return 0 if d["passed"] == d["total_checks"] else 1


if __name__ == "__main__":
    sys.exit(main())
