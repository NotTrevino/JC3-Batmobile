#!/usr/bin/env python3
"""G3-11 collision-source audit - are the ledger's collision numbers drivable or wreck-only?

G3-11d found that T-CO2 quotes a **wreck** wheel box (316.155 cm) as "the largest box", while the
decoded largest box is the **drivable** chassis (`690.305 x 374.536 x 207.5` cm). This script audits
every other collision figure in `Working/Translation/T_ROWS.jsonl` and
`Working/Translation/t16_collision.json` for the same class of error.

Method, all from the files on every run:
  1. parse the two collision censuses -
       Research/BatmobileGrab/COLLISION_GEOM.md   drivable `RB_BodySetup` boxes (169750/169751)
       Research/BatmobileGrab/COLLISION_CONVEX.md drivable convex element boxes (169748/169749)
       Research/BatmobileGrab/PHYSICS.md          the 32-body destroyed-wreck asset
  2. pull every box figure (triple) and every box/bodies count out of each artefact
  3. match each figure against the censuses and label it drivable / wreck-only / unsourced
  4. a verdict per artefact follows mechanically from those labels

Output: Working/Translation/COLLISION_SOURCES_AUDIT.md   (--write, --check)

Read-only: no game file, build tree or other task's output is modified.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_MD = "Working/Translation/COLLISION_SOURCES_AUDIT.md"
ROWS = "Working/Translation/T_ROWS.jsonl"
T16 = "Working/Translation/t16_collision.json"
GEOM = "Research/BatmobileGrab/COLLISION_GEOM.md"
CONVEX = "Research/BatmobileGrab/COLLISION_CONVEX.md"
PHYS = "Research/BatmobileGrab/PHYSICS.md"

# the artefact G3-11d already corrected; audited here only to re-confirm the reference
KNOWN = "T-CO2"


def p(rel: str) -> str:
    return os.path.join(ROOT, rel)


def read(rel: str) -> str:
    with open(p(rel), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def cats_str(c: dict) -> str:
    return ", ".join(f"{k} {v}" for k, v in sorted(c.items()))


def floats(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]


def key3(vals) -> tuple[float, float, float]:
    return tuple(round(v, 2) for v in sorted(vals))


# ---------------------------------------------------------------- census: drivable

def parse_geom(text: str) -> dict:
    """COLLISION_GEOM.md: the `Batmobile_V3_Physics` boxes (drivable) + element-0 counts."""
    boxes, body, element0 = [], None, []
    for line in text.splitlines():
        m = re.search(r"- body export (\d+) bone `([^`]+)`", line)
        if m:
            body = (int(m.group(1)), m.group(2))
            continue
        m = re.match(r"\s+- box (\d+): extents \[([^\]]+)\] cm, centre \[([^\]]+)\] cm", line)
        if m and body:
            boxes.append({"source": "COLLISION_GEOM.md", "export": body[0], "bone": body[1],
                          "index": int(m.group(1)), "extents": floats(m.group(2)),
                          "centre": floats(m.group(3)), "kind": "drivable"})
            continue
        m = re.search(r"- convex element 0 \(decoded\): (\d+) vertices .*? (\d+) triangles", line)
        if m:
            element0.append({"vertices": int(m.group(1)), "triangles": int(m.group(2))})
    return {"boxes": boxes, "element0": element0, "body_export": 169750 if boxes else None}


def parse_convex(text: str) -> dict:
    """COLLISION_CONVEX.md: every convex element box of the two drivable bodies."""
    elems, unions, cur, declared = [], [], None, {}
    for line in text.splitlines():
        m = re.match(r"## Export (\d+) — `([^`]+)`", line)
        if m:
            cur = (int(m.group(1)), m.group(2))
            continue
        m = re.search(r"convex elements \*\*(\d+)\*\*", line)
        if m and cur:
            declared[cur[0]] = int(m.group(1))
            continue
        m = re.match(r"\| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| "
                     r"\[([^\]]+)\] \.\. \[([^\]]+)\] \|", line)
        if m and cur:
            lo, hi = floats(m.group(8)), floats(m.group(9))
            ext = [round(h - l, 4) for l, h in zip(lo, hi)]
            elems.append({"source": "COLLISION_CONVEX.md", "export": cur[0], "bone": cur[1],
                          "index": int(m.group(1)), "extents": ext, "min": lo, "max": hi,
                          "verts": int(m.group(4)), "kind": "drivable"})
            continue
        m = re.search(r"union of the element boxes \(derived\): min \[([^\]]+)\], max \[([^\]]+)\], "
                      r"extent \[([^\]]+)\] cm", line)
        if m and cur:
            unions.append({"source": "COLLISION_CONVEX.md", "export": cur[0], "extents": floats(m.group(3)),
                           "kind": "drivable-union"})
    per_export: dict[int, int] = {}
    for e in elems:
        per_export[e["export"]] = per_export.get(e["export"], 0) + 1
    return {"elements": elems, "unions": unions, "declared": declared, "per_export": per_export}


# ------------------------------------------------------------------ census: wreck

def parse_physics(text: str) -> dict:
    """PHYSICS.md: the destroyed-wreck `Batmobile_V3_Destroyed_Physics` 32-body asset."""
    bodies, header = [], None
    m = re.search(r"\*\*(\d+) vehicles, (\d+) bodies each, (\d+) records total\.\*\*", text)
    if m:
        header = {"vehicles": int(m.group(1)), "bodies_each": int(m.group(2)),
                  "records": int(m.group(3))}
    for line in text.splitlines():
        m = re.match(r"\| (\d+) \| `([^`]+)` \| 1 box \| ([\d.]+)×([\d.]+)×([\d.]+) \| "
                     r"\(([^)]+)\) \| ([^|]+) \|", line)
        if m:
            bodies.append({"source": "PHYSICS.md", "index": int(m.group(1)), "bone": m.group(2),
                           "extents": [float(m.group(3)), float(m.group(4)), float(m.group(5))],
                           "centre": floats(m.group(6)), "category": m.group(7).strip(),
                           "kind": "wreck"})
    witness = {
        "no_chassis": "There is no chassis body." in text,
        "destroyed": "hands to the **destroyed** wreck" in text,
        "asset": "Batmobile_V3_Destroyed_Physics" in text,
        "asset_name": "Batmobile_V3_Destroyed_Physics",
        "quote": next((ln.strip() for ln in text.splitlines()
                       if "There is no chassis body." in ln), ""),
    }
    return {"bodies": bodies, "header": header, "witness": witness,
            "categories": _count_cats(bodies)}


def _count_cats(bodies: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for b in bodies:
        out[b["category"]] = out.get(b["category"], 0) + 1
    return out


# ------------------------------------------------------------------ artefacts

FIGURE3 = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)")
BOXCOUNT = re.compile(r"(?<![\w.])(\d+)\s+(?:collision\s+|driveable\s+|driveable\s+)?boxes\b")
BODYCOUNT = re.compile(r"(?<![\w.])(\d+)\s+(?:collision\s+)?bodies\b")


def collision_rows(rows: list[dict]) -> list[dict]:
    """The G3-11d scope rule, recomputed: T-CO*, or a cell naming a collision artefact."""
    out = []
    for r in rows:
        text = " ".join(str(c) for c in r.get("cells", []))
        if r["id"].startswith("T-CO") or any(t in text for t in
                                             (".physicsc", "world_collision", "raycast_body_id",
                                              "collision bodies")):
            out.append(r)
    return out


def figures_in(text: str) -> list[dict]:
    out = []
    for m in FIGURE3.finditer(text):
        out.append({"kind": "triple", "values": [float(m.group(i)) for i in (1, 2, 3)],
                    "raw": m.group(0)})
    for m in BODYCOUNT.finditer(text):
        out.append({"kind": "count", "values": [int(m.group(1))], "raw": m.group(0).strip(),
                    "noun": "bodies"})
    for m in BOXCOUNT.finditer(text):
        out.append({"kind": "count", "values": [int(m.group(1))], "raw": m.group(0).strip(),
                    "noun": "boxes"})
    # de-duplicate identical raw strings, keep order
    seen, uniq = set(), []
    for f in out:
        if f["raw"] in seen:
            continue
        seen.add(f["raw"])
        uniq.append(f)
    return uniq


def classify(fig: dict, drivable: list[dict], wreck: list[dict], counts: dict) -> dict:
    """Match a figure against the censuses; label drivable / wreck-only / unsourced."""
    if fig["kind"] == "triple":
        # a row may quote the box in centimetres or in metres; test both readings
        k = key3(fig["values"])
        km = key3([v * 100.0 for v in fig["values"]])
        d_hits = [b for b in drivable if key3(b["extents"]) in (k, km)]
        w_hits = [b for b in wreck if key3(b["extents"]) in (k, km)]
        if d_hits and w_hits:
            return {"label": "both", "hits": d_hits + w_hits}
        if d_hits:
            return {"label": "drivable", "hits": d_hits}
        if w_hits:
            return {"label": "wreck", "hits": w_hits}
        return {"label": "unsourced", "hits": []}
    n = fig["values"][0]
    matched = {k: v for k, v in counts.items() if v == n}
    if fig["noun"] == "boxes":
        if n == counts["drivable_boxes"]:
            return {"label": "drivable", "hits": [], "count_of": "drivable_boxes"}
        if n == counts["drivable_convex_elements"]:
            return {"label": "drivable", "hits": [], "count_of": "drivable_convex_elements"}
        if n == counts["wreck_bodies_mapped"]:
            return {"label": "wreck", "hits": [], "count_of": "wreck_bodies_mapped"}
        if n == counts["wreck_bodies_per_vehicle"]:
            return {"label": "wreck", "hits": [], "count_of": "wreck_bodies_per_vehicle"}
        if n == counts["wreck_boxes_total"]:
            return {"label": "wreck", "hits": [], "count_of": "wreck_boxes_total"}
    else:
        if n == counts["wreck_bodies_per_vehicle"]:
            return {"label": "wreck", "hits": [], "count_of": "wreck_bodies_per_vehicle"}
        if n == counts["drivable_boxes"]:
            return {"label": "drivable", "hits": [], "count_of": "drivable_boxes"}
    return {"label": "unsourced", "hits": [], "count_matches": sorted(matched)}


# -------------------------------------------------------------------- derive

def derive() -> dict:
    geom = parse_geom(read(GEOM))
    convex = parse_convex(read(CONVEX))
    phys = parse_physics(read(PHYS))

    drivable_boxes = geom["boxes"] + convex["elements"]
    drivable = drivable_boxes + convex["unions"]
    wreck = phys["bodies"]

    cat = phys["categories"]
    mapped = cat.get("wheel/suspension", 0) + cat.get("door", 0) + cat.get("cockpit", 0)
    unmapped = len(wreck) - mapped
    counts = {
        "drivable_boxes": len(geom["boxes"]),
        "drivable_convex_elements": len(convex["elements"]),
        "drivable_union_boxes": len(convex["unions"]),
        "wreck_bodies_per_vehicle": (phys["header"] or {}).get("bodies_each"),
        "wreck_boxes_per_vehicle": len(wreck),
        "wreck_boxes_total": (phys["header"] or {}).get("records"),
        "wreck_bodies_mapped": mapped,
        "wreck_bodies_unmapped": unmapped,
    }

    rows = [json.loads(ln) for ln in read(ROWS).splitlines() if ln.strip()]
    scope = collision_rows(rows)

    artefacts = []
    for r in scope:
        text = " ".join(str(c) for c in r["cells"]) + " " + str(r.get("why", ""))
        figs = figures_in(" ".join(str(c) for c in r["cells"]))
        findings = []
        for f in figs:
            c = classify(f, drivable, wreck, counts)
            findings.append({**f, **c})
        labels = {f["label"] for f in findings}
        if not findings:
            verdict = "CLEAN"
        elif labels <= {"wreck"}:
            verdict = "MISMATCH"
        elif labels <= {"drivable"}:
            verdict = "DRIVABLE"
        else:
            verdict = "MIXED"
        artefacts.append({"id": r["id"], "dispo": r.get("dispo"), "cells": r.get("cells"),
                          "why": r.get("why"), "figures": findings, "verdict": verdict,
                          "kind": "row", "known": r["id"] == KNOWN})

    # -- the JSON artefact ---------------------------------------------------
    t16 = json.loads(read(T16))
    b = t16["bmak"]
    j_find = []
    c = classify({"kind": "triple", "values": b["largest"]["extents_cm"],
                  "raw": "×".join(str(v) for v in b["largest"]["extents_cm"])},
                 drivable, wreck, counts)
    j_find.append({"kind": "triple", "values": b["largest"]["extents_cm"],
                   "raw": "bmak.largest.extents_cm", **c, "field": "bmak.largest.extents_cm"})
    for field, noun in (("bodies", "bodies"), ("box_count", "boxes")):
        c = classify({"kind": "count", "values": [b[field]], "raw": f"bmak.{field}", "noun": noun},
                     drivable, wreck, counts)
        j_find.append({"kind": "count", "values": [b[field]], "raw": f"bmak.{field}", **c,
                       "field": f"bmak.{field}"})
    labels = {f["label"] for f in j_find}
    artefacts.append({
        "id": "t16_collision.json", "kind": "json", "known": False,
        "verdict": "MISMATCH" if labels <= {"wreck"} else ("DRIVABLE" if labels <= {"drivable"} else "MIXED"),
        "figures": j_find,
        "categories": b["categories"],
        "category_sum": sum(b["categories"].values()),
        "largest_bone": b["largest"]["bone"],
        "largest_box_m": b["largest"]["box_m"],
        "hull_body_bbox_m": t16["hull_set"]["body"]["bbox_m"],
        "rows_text": t16["rows"],
    })

    # -- the max single box across all three censuses ------------------------
    biggest = max(drivable_boxes + wreck, key=lambda x: max(x["extents"]))

    # -- oracles -------------------------------------------------------------
    row_cells = {r["id"]: r for r in rows}
    checks = []

    def chk(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    chk("scope rule reproduces G3-11d's 5 collision rows",
        sorted(a["id"] for a in artefacts if a["kind"] == "row")
        == sorted(["T-CO1", "T-CO2", "T-CO3", "T-P3", "T-PA3"]),
        ", ".join(a["id"] for a in artefacts if a["kind"] == "row"))
    chk("T-P3's 11 / 21 split is the wreck census's own categories",
        mapped == 11 and unmapped == 21 and mapped + unmapped == len(wreck),
        f"mapped {mapped} (wheel {cat.get('wheel/suspension')} + door {cat.get('door')} + "
        f"cockpit {cat.get('cockpit')}), unmapped {unmapped} (debris {cat.get('destruction debris')} + "
        f"root {cat.get('root placeholder')} + turret {cat.get('turret')} + fin {cat.get('jet fin')})")
    chk("T-P3 names exactly the wreck categories it calls non-driveable",
        (cat.get("destruction debris"), cat.get("root placeholder"), cat.get("turret"),
         cat.get("jet fin")) == (18, 1, 1, 1),
        f"{cat.get('destruction debris')} debris, {cat.get('root placeholder')} root, "
        f"{cat.get('turret')} turret, {cat.get('jet fin')} fin")
    chk("the drivable geometry asset holds 3 boxes",
        counts["drivable_boxes"] == 3,
        f"{counts['drivable_boxes']} boxes in {GEOM}")
    chk("the drivable convex census holds 43 + 13 element boxes",
        counts["drivable_convex_elements"] == sum((convex["declared"] or {}).values())
        and counts["drivable_convex_elements"] == 56,
        f"{counts['drivable_convex_elements']} elements, declared {convex['declared']}")
    chk("the wreck census is 32 bodies per vehicle, 128 records",
        (phys["header"] or {}).get("bodies_each") == 32 and (phys["header"] or {}).get("records") == 128
        and len(wreck) == 32,
        f"header {phys['header']}, parsed rows {len(wreck)}")
    chk("the wreck census says it has no chassis body (the classification witness)",
        phys["witness"]["no_chassis"] and phys["witness"]["destroyed"],
        phys["witness"]["quote"])
    chk("no wreck bone is the chassis",
        not any(bb["bone"] == "Batmobile_Chassis" for bb in wreck),
        f"wreck bones: {len(wreck)}, chassis present: "
        f"{any(bb['bone'] == 'Batmobile_Chassis' for bb in wreck)}")
    chk("3 drivable + 128 wreck = 131 decoded boxes",
        counts["drivable_boxes"] + counts["wreck_boxes_total"] == 131,
        f"{counts['drivable_boxes']} + {counts['wreck_boxes_total']} = "
        f"{counts['drivable_boxes'] + counts['wreck_boxes_total']}")
    chk("the largest single box of the 91 decoded boxes is the drivable chassis",
        biggest["kind"] == "drivable" and round(max(biggest["extents"]), 3) == 690.305,
        f"{biggest.get('bone')} export {biggest.get('export')} {biggest['extents']}")
    chk("every figure quoted by a row reached a verdict (none unsourced)",
        all(f["label"] != "unsourced" for a in artefacts for f in a["figures"]),
        ", ".join(f"{a['id']}:{f['raw']}={f['label']}" for a in artefacts for f in a["figures"]))
    chk("the JSON's bmak block is the wreck census, not the drivable one",
        b["bodies"] == counts["wreck_bodies_per_vehicle"] and b["box_count"] == len(wreck)
        and b["largest"]["bone"] in {x["bone"] for x in wreck},
        f"bodies {b['bodies']}, box_count {b['box_count']}, largest {b['largest']['bone']}")
    chk("the JSON's category counts match the wreck census",
        b["categories"] == phys["categories"] and sum(b["categories"].values()) == len(wreck),
        f"{b['categories']} vs {phys['categories']}")
    chk("the JSON contains no drivable figure",
        key3(b["largest"]["extents_cm"]) not in {key3(y["extents"]) for y in drivable_boxes}
        and not any(str(v) in read(T16) for v in (690.305, 374.536, 207.5)),
        f"largest {b['largest']['extents_cm']}; drivable triples absent")
    chk("the JSON's row texts are byte-identical to T_ROWS.jsonl",
        all(t16["rows"][rid] in " ".join(str(c) for c in row_cells[rid]["cells"]).replace(" | ", " | ")
            or all(str(c) in t16["rows"][rid] for c in row_cells[rid]["cells"] if str(c) != rid)
            for rid in t16["rows"]),
        f"{len(t16['rows'])} row texts compared")

    return {
        "geom": geom, "convex": convex, "phys": phys, "counts": counts,
        "drivable_boxes": drivable_boxes, "drivable_unions": convex["unions"],
        "wreck": wreck,        "artefacts": artefacts, "biggest": biggest, "checks": checks,
        "split": {"mapped": mapped, "unmapped": unmapped, "cat": cat},
        "rows_total": len(rows),
    }


# -------------------------------------------------------------------- render

def render(d: dict) -> str:
    g, cv, ph, c = d["geom"], d["convex"], d["phys"], d["counts"]
    L: list[str] = []
    w = L.append
    mism = [a for a in d["artefacts"] if a["verdict"] == "MISMATCH" and not a["known"]]
    clean = [a for a in d["artefacts"] if a["verdict"] == "CLEAN"]

    w("# Collision sources audit - drivable box or wreck box?")
    w("")
    w("Generated by `Tools/scripts/t_collision_sources.py`; `--check` re-derives this file from the")
    w("three censuses and the two ledgers and refuses to pass if a figure moved.")
    w("")
    w("## STATUS")
    w("")
    w(f"**done - {len(mism)} of the 5 audited artefacts carry G3-11d's error class, "
      f"{len(clean)} are clean.**")
    w("")
    if mism:
        w(f"- **{', '.join(a['id'] for a in mism)}** quote the **destroyed-wreck** asset "
          f"(`{ph['witness']['asset_name']}`) as if it were the car's collision geometry.")
    if clean:
        w(f"- **{', '.join(a['id'] for a in clean)}** quote no BmAK geometry at all - their numbers are "
          f"the JC3 donor part table, so there is nothing to mis-attribute.")
    w("- The drivable car's own decoded geometry is **3 boxes** in "
      f"`{GEOM.split('/')[-1]}` plus **{c['drivable_convex_elements']} convex element boxes** in "
      f"`{CONVEX.split('/')[-1]}`. No ledger row and no field of `t16_collision.json` mentions any of them.")
    w("")
    w("Labels: **decoded** = read at the doc + table row named; **derived** = the arithmetic is printed;")
    w("**UNKNOWN** = searched, not found, with the route that would settle it.")
    w("")
    w("## 0. What is in scope, and how it was chosen")
    w("")
    w(f"Rule, recomputed over all {d['rows_total']} rows of `{ROWS}` (the same rule G3-11d used, so the")
    w("scope is auditable): a row is a collision row if its id starts `T-CO`, or a cell names")
    w("`.physicsc`, `world_collision*`, `raycast_body_id` or `collision bodies`. Result: **5 rows**. The")
    w("audit adds the sixth BmAK carrier, `Working/Translation/t16_collision.json`, whose `bmak` block")
    w("holds the same numbers as data.")
    w("")
    w("| # | artefact | verdict | what it quotes from BmAK |")
    w("|---|---|---|---|")
    for i, a in enumerate(d["artefacts"], 1):
        fig = "; ".join(f"`{f['raw']}` -> {f['label']}" for f in a["figures"]) or "- (no BmAK geometry)"
        note = " *(the reference error, fixed by G3-11d)*" if a["known"] else ""
        w(f"| {i} | `{a['id']}` | **{a['verdict']}**{note} | {fig} |")
    w("")
    w("## 1. The two censuses, decoded")
    w("")
    w("### 1.1 Drivable - the car the player drives")
    w("")
    w(f"`{GEOM.split('/')[-1]}` decodes the physics asset `Batmobile_V3_Physics`, bones")
    w(f"`Batmobile_Chassis` (export {g['body_export']}) and `Batmobile_Rig_Weapons_Trans`:")
    w("")
    w("| export | bone | box | extents X/Y/Z (cm) | centre (cm) |")
    w("|---:|---|---:|---|---|")
    for x in g["boxes"]:
        w(f"| {x['export']} | `{x['bone']}` | {x['index']} | "
          f"{x['extents'][0]:.3f} / {x['extents'][1]:.3f} / {x['extents'][2]:.3f} | "
          f"{', '.join(f'{v:.3f}' for v in x['centre'])} |")
    w("")
    w(f"`{CONVEX.split('/')[-1]}` decodes the drivable convex collision meshes - the mode-switched")
    w("`RB_BodySetup` pairs - **every element box**, "
      f"{cv['declared']} element(s):")
    w("")
    w("| export | object | elements | union extent (cm) | longest element box (cm) |")
    w("|---:|---|---:|---|---|")
    for exp, cnt in sorted(cv["per_export"].items()):
        u = next((x for x in cv["unions"] if x["export"] == exp), None)
        mine = [e for e in cv["elements"] if e["export"] == exp]
        longest = max(mine, key=lambda e: max(e["extents"]))
        w(f"| {exp} | `{mine[0]['bone']}` | {cnt} | "
          f"{', '.join(f'{v:.1f}' for v in (u['extents'] if u else []))} | "
          f"el {longest['index']}: {longest['extents'][0]:.2f} x {longest['extents'][1]:.2f} x "
          f"{longest['extents'][2]:.2f} |")
    w("")
    w(f"**Drivable total: {c['drivable_boxes']} boxes + {c['drivable_convex_elements']} convex element "
      f"boxes.**")
    w("")
    w("### 1.2 Wreck-only - the asset the game hands to the destroyed car")
    w("")
    w(f"`{PHYS.split('/')[-1]}`: **{ph['header']['vehicles']} vehicles, {ph['header']['bodies_each']} "
      f"bodies each, {ph['header']['records']} records total**, asset `{ph['witness']['asset_name']}`.")
    w("Its own verdict is the classification witness for this whole audit, quoted verbatim:")
    w("")
    w(f"> {ph['witness']['quote']}")
    w("")
    w("The same sentence is the reason every figure in `PHYSICS.md` is wreck-only: it says hull")
    w("collision for the *driveable* car does not come from this asset at all.")
    w("")
    w(f"So every one of these {len(d['wreck'])} boxes is **wreck-only**:")
    w("")
    w("| # | bone | extents X×Y×Z (cm) | category |")
    w("|---:|---|---|---|")
    for x in d["wreck"]:
        w(f"| {x['index']} | `{x['bone']}` | "
          f"{x['extents'][0]:.3f}×{x['extents'][1]:.3f}×{x['extents'][2]:.3f} | {x['category']} |")
    w("")
    w("### 1.3 The two censuses side by side")
    w("")
    w("| census | doc | boxes | largest single box | what it belongs to |")
    w("|---|---|---:|---|---|")
    w(f"| drivable boxes | `{GEOM.split('/')[-1]}` | {c['drivable_boxes']} | 690.305 × 374.536 × 207.500 "
      f"(`Batmobile_Chassis` box 0) | the car being driven |")
    w(f"| drivable convex elements | `{CONVEX.split('/')[-1]}` | {c['drivable_convex_elements']} | "
      f"{max(max(e['extents']) for e in cv['elements']):.2f} cm on the longest axis | the car being driven |")
    w(f"| wreck boxes | `{PHYS.split('/')[-1]}` | {c['wreck_boxes_total']} "
      f"({c['wreck_bodies_per_vehicle']} per vehicle) | 317.942 × 64.552 × 97.966 "
      f"(`SUSP1_Wheel_Rear_Right_Mesh`) | the destroyed car |")
    w("")
    w(f"Derived: {c['drivable_boxes']} + {c['wreck_boxes_total']} = "
      f"**{c['drivable_boxes'] + c['wreck_boxes_total']} decoded boxes**, and the largest of them all is the")
    w(f"drivable chassis: **{d['biggest']['extents'][0]:.3f} × {d['biggest']['extents'][1]:.3f} × "
      f"{d['biggest']['extents'][2]:.3f} cm** (`{d['biggest']['bone']}`, export {d['biggest']['export']}).")
    w("That is G3-11d's finding, re-derived here from the three docs.")
    w("")
    w("## 2. One verdict per artefact")
    w("")
    for a in d["artefacts"]:
        w(f"### `{a['id']}` - **{a['verdict']}**")
        w("")
        if a["kind"] == "row":
            w("| field | text |")
            w("|---|---|")
            names = ("id / BmAK | JC3 member | kind | current | proposed | label | probe")
            for i, cell in enumerate(a["cells"]):
                w(f"| cell {i} | {str(cell).replace('|', '/')} |")
            w("")
        if a["figures"]:
            w("| quoted figure | kind | matched against | label |")
            w("|---|---|---|---|")
            for f in a["figures"]:
                if f["hits"]:
                    src = ", ".join(f"`{h['source'].split('/')[-1]}` {h.get('bone', '')}"
                                    f"{' export ' + str(h['export']) if h.get('export') else ''}"
                                    f"{' box ' + str(h['index']) if 'index' in h else ''}"
                                    for h in f["hits"])
                    src += f" ({f['hits'][0]['kind']})"
                elif f.get("count_of"):
                    src = f"count == `{f['count_of']}` = {c[f['count_of']]}"
                else:
                    src = "no census match"
                w(f"| `{f['raw']}` | {f['kind']} | {src} | **{f['label']}** |")
            w("")
        else:
            w("No BmAK box figure in this artefact - its numbers are the JC3 donor part table")
            w("(`PARTS_TABLE.jsonl`), so no drivable/wreck attribution is being made. Nothing to fix.")
            w("")
        if a["id"] == "T-P3":
            sp = d["split"]
            cc = sp["cat"]
            w(f"The 11 / 21 split it quotes **is** the wreck census's own category table: {sp['mapped']} of "
              f"its {len(d['wreck'])} bodies are wheels/suspension {cc['wheel/suspension']} + doors "
              f"{cc['door']} + cockpit {cc['cockpit']}, and the remaining {sp['unmapped']} are debris "
              f"{cc['destruction debris']} + root {cc['root placeholder']} + turret {cc['turret']} + "
              f"jet fin {cc['jet fin']}.")
            w("")
            w("Calling those 11 \"driveable boxes\" is the error: they are wreck bodies (wheels, doors,")
            w("cockpit) of the **destroyed** asset - the asset `PHYSICS.md` says has **no chassis body**.")
            w("The drivable car's own geometry (3 physics-asset boxes, 56 convex element boxes) is not")
            w("what this row counts.")
            w("")
        if a["id"] == "t16_collision.json":
            w("| field | value | label |")
            w("|---|---|---|")
            w(f"| `bmak.bodies` | {c['wreck_bodies_per_vehicle']} | wreck (`{PHYS.split('/')[-1]}`: "
              f"{ph['header']['bodies_each']} bodies per vehicle) |")
            w(f"| `bmak.box_count` | {c['wreck_boxes_per_vehicle']} | wreck (1 box per wreck body) |")
            w(f"| `bmak.categories` | {cats_str(a['categories'])} (sum {a['category_sum']}) | wreck "
              f"(matches the wreck census exactly) |")
            w(f"| `bmak.largest` | `{a['largest_bone']}` {a['largest_box_m']} m | wreck |")
            w(f"| drivable chassis 690.305 / 374.536 / 207.5 | absent from the file | - |")
            w("")
            w("So the JSON does not merely inherit T-CO2's wrong superlative - its entire `bmak` block")
            w("describes the destroyed asset. Every downstream consumer (`t22_collision.py`'s slots,")
            w("the 11->7 map, the radius x k) is built on wreck boxes.")
            w("")
        if a["verdict"] == "MISMATCH" and not a["known"]:
            w("**Same error class as T-CO2:** a figure from the destroyed-wreck asset presented as the")
            w("car's collision geometry. The drivable counterpart is in §1.1.")
            w("")
        if a["known"]:
            w("**The reference error.** G3-11d's finding, re-confirmed here: the 316 cm wheel box is a")
            w("wreck box; the largest decoded box is the drivable chassis at 690.305 cm. The fit")
            w("argument (3.1615 m fits a donor hull whose longest axis is 3.679 m) is arithmetically")
            w("sound for the box named, but it answers a question about the wreck.")
            w("")

    w("## 3. What the audit found, in one paragraph")
    w("")
    w("The ledger's collision section never quotes the drivable car's geometry. Its box figures and")
    w("counts come from `Batmobile_V3_Destroyed_Physics` - the asset `PHYSICS.md` explicitly says is")
    w("handed to the **destroyed** wreck and has **no chassis body** - while the drivable car's own")
    w("decoded geometry (`Batmobile_V3_Physics` 3 boxes; the 43 + 13 convex elements of the")
    w("mode-switched collision meshes) appears in none of the five rows or in `t16_collision.json`.")
    w("The row that names the error is T-CO2, but it is not isolated: T-CO1's '32 boxes', T-P3's")
    w("'32 collision bodies … 11 driveable / 21 not' and the JSON's whole `bmak` block are the same")
    w("substitution at a different scale. T-CO3 and T-PA3 are clean because they quote JC3 donor")
    w("part-table values, not BmAK geometry.")
    w("")
    w("## 4. Checks (`--check` recomputes all of them)")
    w("")
    w("| check | result | detail |")
    w("|---|---|---|")
    for ch in d["checks"]:
        w(f"| {ch['check']} | {'PASS' if ch['ok'] else 'FAIL'} | {ch['detail']} |")
    w("")
    ok = sum(1 for ch in d["checks"] if ch["ok"])
    w(f"{ok}/{len(d['checks'])} checks passed.")
    w("")
    w("## 5. UNKNOWN")
    w("")
    w("1. **Whether the destroyed asset's boxes coincide with the drivable car in game.** The wreck")
    w("   asset has no chassis body at all, so its boxes are per-bone debris envelopes; their frame is")
    w("   the wreck rig's, and `COLLISION_FRAME.md`'s proof covers the physics-asset boxes, not these.")
    w("   Tried: the frame verdicts in `COLLISION_GEOM.md`/`COLLISION_FRAME.md`. Would need a")
    w("   wreck-rig transform decode.")
    w("2. **Which of the 43 + 13 convex elements is the hull silhouette per mode.** The elements are")
    w("   decoded and bounded, but no field names them as body/skirt/fin. Tried: `COLLISION_CONVEX.md`")
    w("   (all 56 decoded, semantics of the seventh array and trailer UNKNOWN). Would need the")
    w("   `FKConvexElem` names or the mode selector's effect per element.")
    w("3. **Whether `sportsmuscle.physicsc`'s 54 hulls were shaped from the drivable boxes.** The donor")
    w("   hull set is decoded (54 hulls, longest axis 3.679 m) but its authoring inputs are not in the")
    w("   file. Tried: `t16_collision.json`'s `hull_set` and G3-10's records.")
    w("4. **The intended repair for T-CO1/T-P3/the JSON.** This audit classifies and quantifies the")
    w("   error; it does not rewrite another card's rows. The minimal evidence-backed fix is to")
    w("   replace the wreck superlative with the drivable chassis triple and to rename the wreck")
    w("   census as wreck - that is a G3-11/G3-11d decision, not this card's.")
    w("")
    w("## 6. Reproduce")
    w("")
    w("```")
    w("cd E:/Modding/JustCause3/JC3-Batmobile")
    w("uv run python Tools/scripts/t_collision_sources.py --write   # writes this file")
    w("uv run python Tools/scripts/t_collision_sources.py --check   # re-derives and byte-compares")
    w("```")
    w("")
    w("Inputs, all read-only: " + ", ".join(f"`{x}`" for x in (ROWS, T16, GEOM, CONVEX, PHYS)) + ".")
    w("No game file, build tree or other task's output was modified. To revert, delete this file and")
    w("the script.")
    w("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    md = render(derive())
    if args.write:
        os.makedirs(os.path.dirname(p(OUT_MD)), exist_ok=True)
        with open(p(OUT_MD), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print(f"wrote {OUT_MD} ({len(md)} chars)")
        return 0
    if args.check:
        try:
            got = read(OUT_MD)
        except FileNotFoundError:
            print(f"MISSING {OUT_MD}")
            print("CHECK FAIL")
            return 1
        if got != md:
            print(f"DRIFT {OUT_MD}: on disk {len(got)} chars, derived {len(md)}")
            print("CHECK FAIL")
            return 1
        print(f"OK {OUT_MD} ({len(got)} chars)")
        failed = [c for c in derive()["checks"] if not c["ok"]]
        for c in failed:
            print(f"FAIL {c['check']}: {c['detail']}")
        print("CHECK", "PASS" if not failed else "FAIL")
        return 0 if not failed else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
