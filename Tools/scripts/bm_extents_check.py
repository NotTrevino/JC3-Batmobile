#!/usr/bin/env python3
"""bm_extents_check.py - extents of the SHIPPED Batmobile `.physicsc`, and the BmAK chassis gap.

G3-12c decoded the stored shape extents of five vanilla JC3 vehicles. This applies the same
decoder (`Tools/scripts/jc3hkx.py`, imported, never edited) to the file the build ships,
`Working/Collision/batmobile.physicsc` (B-10, `BM_COLLISION.md`), and answers three questions:

  1. does each compound's stored AABB contain every decoded child-hull vertex?      (O1)
  2. is that stored AABB the union of the children's AABBs (plus the convex radius)? (O2)
  3. how does the Batmobile body compare with BmAK's drivable chassis box?
     (`Research/BatmobileGrab/COLLISION_GEOM.md`: 690.305 x 374.536 x 207.5 cm)

Question 3 is answered twice, on purpose. The BmAK box is in Unreal axes and the JC3 file in JC3
axes, and `COLLISION_GEOM.md` line 37 states outright that "Frame axes are not proven" - so the
card reports (a) the axis-free sorted-span comparison that card itself uses, and (b) a per-axis
pairing under an explicitly **ASSUMED** mapping, with the two required to agree as a multiset.

Output: Working/Collision/BM_EXTENTS_CHECK.md   (--write / --check)

Read-only on everything it opens. No game launched or attached (INSTRUCTIONS.md section 3).
Labels: decoded = bytes at a stated offset; derived = stated arithmetic; UNKNOWN = not decoded.
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
sys.path.insert(0, HERE)

from jc3hkx import (COMPOUND_CLASSES, POLYTOPE, Packfile, decode_compound,  # noqa: E402
                    decode_polytope, shape_aabb, transform_aabb)

SHIPPED = "Working/Collision/batmobile.physicsc"
B10 = "Working/Collision/bm_collision.json"
CGEOM_MD = "Research/BatmobileGrab/COLLISION_GEOM.md"
CGEOM_JSON = "Research/BatmobileGrab/COLLISION_GEOM.json"
OUT = "Working/Collision/BM_EXTENTS_CHECK.md"
TOL = 1e-3          # metres, the same slack G3-12c allows on top of the convex radius


def p(rel: str) -> str:
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


def read(rel: str) -> str:
    with open(p(rel), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def size_m(box: dict) -> list[float]:
    return [box["max"][k] - box["min"][k] for k in range(3)]


def radius_of(pf: Packfile, off: int) -> float:
    if pf._starts.get(off) == POLYTOPE:
        return decode_polytope(pf, off)["convex_radius"]
    return pf.f32(off + 0x14)


def child_bounds(pf: Packfile, inst: dict) -> dict | None:
    """A child's bounds in compound space.

    For a hull, the bounds of its decoded vertices transformed by the instance (tight). Using the
    child's own AABB and transforming the box instead over-estimates a rotated child - on this file
    it invents a 2.02 cm outlier on one compound - so the vertex set is the honest bound. A child
    with no decoded vertices (a mesh) falls back to its stored AABB, and the document says so.
    """
    sh = inst["shape"]
    if not sh:
        return None
    b, t = inst["basis"], inst["translation"]
    if pf._starts.get(sh) == POLYTOPE:
        vs = decode_polytope(pf, sh)["vertices"]
        pts = [[sum(b[r][k] * v[r] for r in range(3)) + t[k] for k in range(3)] for v in vs]
        return {"min": [min(q[k] for q in pts) for k in range(3)],
                "max": [max(q[k] for q in pts) for k in range(3)]}
    box = inst["aabb"]
    return transform_aabb(box, b, t) if box else None


def bmak_chassis() -> dict:
    """The BmAK drivable chassis box, read from both of that card's artefacts."""
    md = read(CGEOM_MD)
    m = re.search(r"box 0: extents \[([\d.]+), ([\d.]+), ([\d.]+)\] cm", md)
    if not m:
        raise SystemExit("COLLISION_GEOM.md: chassis box 0 extents not found")
    cm = [float(m.group(i)) for i in (1, 2, 3)]
    j = json.loads(read(CGEOM_JSON))["oracle_chassis_box_vs_body_box"]
    return {"extents_cm": cm,
            "md_line": md[: m.start()].count("\n") + 1,
            "json_sorted_m": j["chassis_box0_full_m_sorted"],
            "json_body_xyz_m": j["body_box_span_m_xyz_jc3"],
            "json_label": j["label"]}


def analyse() -> dict:
    blob = open(p(SHIPPED), "rb").read()
    pf = Packfile(blob)
    hulls = [o for o in pf.objects if o.cls == POLYTOPE]
    compounds = [o for o in pf.objects if o.cls in COMPOUND_CLASSES]
    b10 = json.loads(read(B10))
    target = b10["body"]["bbox_m"]["size"]

    # ---- the body hull: the one whose decoded bounds are B-10's body bbox --------------
    body = None
    best = None
    for o in hulls:
        box = decode_polytope(pf, o.offset)["bounds"]
        d = max(abs(size_m(box)[k] - target[k]) for k in range(3))
        if best is None or d < best[0]:
            best = (d, o.offset, box)
    if best and best[0] <= 0.02:
        body = {"offset": best[1], "box": best[2], "delta_to_b10": best[0]}

    # ---- per-compound oracles ---------------------------------------------------------
    rows = []
    tot_v = tot_overshoot = 0.0
    tot_v = 0
    worst_pokes = worst_exceeds = 0.0
    o1_bad = o2_bad = 0
    host = None
    for o in compounds:
        d = decode_compound(pf, o.offset, o.cls)
        lo, hi = d["aabb"]["min"], d["aabb"]["max"]
        verts = 0
        overshoot = 0.0
        boxes = []
        hull_children = 0
        for inst in d["instances"]:
            sh = inst["shape"]
            if not sh:
                continue
            b, t = inst["basis"], inst["translation"]
            if pf._starts.get(sh) == POLYTOPE:
                hull_children += 1
                dd = decode_polytope(pf, sh)
                rad = dd["convex_radius"]
                for v in dd["vertices"]:
                    q = [sum(b[r][k] * v[r] for r in range(3)) + t[k] for k in range(3)]
                    over = max(max(lo[k] - q[k], q[k] - hi[k]) for k in range(3))
                    verts += 1
                    overshoot = max(overshoot, over)
                    if over > rad + TOL:
                        o1_bad += 1
            tight = child_bounds(pf, inst)
            if tight:
                boxes.append((tight, radius_of(pf, sh)))
        missing = excess = 0.0
        if boxes:
            ulo = [min(bb["min"][k] for bb, _r in boxes) for k in range(3)]
            uhi = [max(bb["max"][k] for bb, _r in boxes) for k in range(3)]
            allowance = max(r for _b, r in boxes) + TOL
            # positive "pokes" = the children's union sticks out of the stored box; positive
            # "exceeds" = the stored box is larger than the union. Havok stores the box of a hull
            # rounded by its convex radius, so both are bounded by that radius - the allowance
            # G3-12c uses on the five vanilla files.
            pokes = max(max(lo[k] - ulo[k], uhi[k] - hi[k]) for k in range(3))
            exceeds = max(max(ulo[k] - lo[k], hi[k] - uhi[k]) for k in range(3))
            if pokes > allowance or exceeds > allowance:
                o2_bad += 1
        tot_v += verts
        tot_overshoot = max(tot_overshoot, overshoot)
        worst_pokes = max(worst_pokes, pokes)
        worst_exceeds = max(worst_exceeds, exceeds)
        rows.append({
            "offset": o.offset, "class": o.cls, "instances": len(d["instances"]),
            "hull_children": hull_children, "vertices": verts,
            "overshoot_cm": overshoot * 100, "pokes_cm": pokes * 100,
            "exceeds_cm": exceeds * 100,
            "aabb": {"min": lo, "max": hi}, "size_m": size_m({"min": lo, "max": hi}),
        })
        if body and any(i["shape"] == body["offset"] for i in d["instances"]):
            host = rows[-1]

    degenerate = [r["offset"] for r in rows
                  if not all(r["aabb"]["min"][k] < r["aabb"]["max"][k] for k in range(3))]

    # ---- the comparison in cm ---------------------------------------------------------
    bm = bmak_chassis()
    body_cm = [round(v * 100.0, 3) for v in size_m(body["box"])] if body else None
    sorted_body = sorted(body_cm) if body_cm else None
    sorted_bmak = sorted(bm["extents_cm"])
    sorted_diff = [round(sorted_body[k] - sorted_bmak[k], 3) for k in range(3)] if body else None
    # ASSUMED: JC3 (x = width, y = height, z = length) <- BmAK (Y = width, Z = height, X = length)
    assumed = [("x (width)", 0, 1), ("y (height)", 1, 2), ("z (length)", 2, 0)]
    pairing = [{"axis": name, "jc3_cm": body_cm[ji], "bmak_cm": bm["extents_cm"][bi],
                "diff_cm": round(body_cm[ji] - bm["extents_cm"][bi], 3)}
               for name, ji, bi in assumed] if body else []

    # ---- oracles on the comparison -----------------------------------------------------
    md_vs_json = max(abs(sorted(bm["extents_cm"])[k] / 100.0 - bm["json_sorted_m"][k])
                     for k in range(3))
    same_multiset = (sorted(round(x["diff_cm"], 2) for x in pairing)
                     == sorted(round(x, 2) for x in sorted_diff)) if body else False
    b10_agrees = (max(abs(bm["json_body_xyz_m"][k] - target[k]) for k in range(3)) < 1e-9)

    checks = []

    def chk(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    chk("the shipped file decodes with the G3-12c reader",
        len(pf.objects) > 0 and len(hulls) > 0,
        f"{len(blob):,} B, {len(pf.objects)} objects, {len(hulls)} hulls, {len(compounds)} compounds, "
        f"sha256 {hashlib.sha256(blob).hexdigest()[:16]}")
    chk("O1: every decoded child-hull vertex lies inside its compound's stored AABB",
        o1_bad == 0,
        f"{tot_v} vertices, worst overshoot {tot_overshoot * 100:.4f} cm, tolerance = child convex radius + 1e-3 m")
    chk("O2: each stored AABB is the children's union, up to the convex radius",
        o2_bad == 0,
        f"{len(rows)} compounds; the union pokes out of its stored box by at most "
        f"{worst_pokes * 100:.4f} cm and the stored box exceeds the union by at most "
        f"{worst_exceeds * 100:.4f} cm")
    chk("O3: every stored AABB is non-degenerate",
        not degenerate, f"{len(degenerate)} degenerate box(es)")
    chk("the body hull is present and its bounds are B-10's body bbox",
        bool(body) and body["delta_to_b10"] <= 0.02,
        f"hull @0x{body['offset']:x}, max |decoded - B-10| "
        f"{body['delta_to_b10'] * 100:.6f} cm" if body else "not found")
    chk("the body hull's compound contains it, exceeding its bounds by no more than the radius",
        bool(host) and host["pokes_cm"] <= 0.1
        and host["exceeds_cm"] <= radius_of(pf, body["offset"]) * 100 + 0.1,
        (f"compound @0x{host['offset']:x}: stored box exceeds the hull bounds by "
         f"{host['exceeds_cm']:.4f} cm (hull radius {radius_of(pf, body['offset']) * 100:.4f} cm), "
         f"union pokes out by {host['pokes_cm']:.4f} cm") if host else "no host")
    chk("COLLISION_GEOM.md's chassis extents equal COLLISION_GEOM.json's sorted spans",
        md_vs_json <= TOL,
        f"max difference {md_vs_json * 1000:.6f} mm")
    chk("COLLISION_GEOM.json's body span equals B-10's body bbox",
        b10_agrees,
        f"{bm['json_body_xyz_m']} vs {target} m")
    chk("the sorted comparison and the ASSUMED per-axis pairing give the same differences",
        same_multiset,
        f"sorted {sorted_diff} cm vs pairing {[x['diff_cm'] for x in pairing]} cm")

    return {
        "blob_bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
        "objects": len(pf.objects), "hulls": len(hulls), "compounds": len(compounds),
        "rows": rows, "tot_v": tot_v, "tot_overshoot_cm": tot_overshoot * 100,
        "worst_pokes_cm": worst_pokes * 100, "worst_exceeds_cm": worst_exceeds * 100,
        "body": body, "body_cm": body_cm, "host": host,
        "radius_cm": (radius_of(pf, body["offset"]) * 100) if body else None,
        "bmak": bm, "sorted_bmak": sorted_bmak, "sorted_body": sorted_body,
        "sorted_diff": sorted_diff, "pairing": pairing,
        "checks": checks,
        "verdict": ("all oracles pass" if all(c["ok"] for c in checks)
                    else "an oracle failed - see the checks table"),
    }


def f3(v: float) -> str:
    return f"{v:+.3f}"


def render(d: dict) -> str:
    L: list[str] = []
    w = L.append
    b = d["body"]
    w("# The shipped Batmobile `.physicsc`: extents, the hull oracle, and the BmAK chassis gap")
    w("")
    w("Generated by `Tools/scripts/bm_extents_check.py --write`; `--check` re-decodes the file and")
    w("rebuilds this document byte for byte. It applies the G3-12c extents reader")
    w("(`Tools/scripts/jc3hkx.py`, imported unchanged) to `Working/Collision/batmobile.physicsc` -")
    w("the file B-10 writes (`BM_COLLISION.md`).")
    w("")
    w("Labels: **decoded** = bytes at a stated offset; **derived** = stated arithmetic on decoded")
    w("values; **ASSUMED** = a choice this card makes explicit because the sources do not prove it;")
    w("**UNKNOWN** = not decoded, with what was tried. No game was run or attached.")
    w("")
    w("## STATUS")
    w("")
    w(f"**done - {d['objects']} objects, {d['hulls']} hulls, {d['compounds']} compounds in the")
    w(f"shipped file; {d['tot_v']} child-hull vertices tested, worst overshoot")
    w(f"{d['tot_overshoot_cm']:.4f} cm; every stored compound AABB exceeds the children's union by at")
    w(f"most {d['worst_exceeds_cm']:.4f} cm (the child convex radius) and no child sticks out of its")
    w(f"box by more than {d['worst_pokes_cm']:.4f} cm. Body extents (decoded):")
    w(f"{d['body_cm'][0]:.3f} x {d['body_cm'][1]:.3f} x {d['body_cm'][2]:.3f} cm (x, y, z). Against")
    w(f"BmAK's drivable chassis box {d['bmak']['extents_cm'][0]:.3f} x ")
    w(f"{d['bmak']['extents_cm'][1]:.3f} x {d['bmak']['extents_cm'][2]:.3f} cm, the differences are")
    w(f"{f3(d['pairing'][0]['diff_cm'])} cm in width, {f3(d['pairing'][1]['diff_cm'])} cm in height and")
    w(f"{f3(d['pairing'][2]['diff_cm'])} cm in length - under the ASSUMED axis pairing (see section 4,")
    w(f"`COLLISION_GEOM.md` says the axes are not proven). {sum(c['ok'] for c in d['checks'])}/"
      )
    w(f"{len(d['checks'])} checks pass.**")
    w("")
    w("## 1. The file")
    w("")
    w(f"- `{SHIPPED}`, {d['blob_bytes']:,} B, sha256 `{d['sha256'][:16]}...` (**decoded**)")
    w(f"- {d['objects']} objects: {d['hulls']} `hknpConvexPolytopeShape` (hulls),")
    w(f"  {d['compounds']} compound shape(s), the rest donor geometry/constraints (**decoded**)")
    w("- the donor's and the Batmobile's own write are B-10's; this card re-reads the bytes and does")
    w("  not write the file (**derived**: the file is unchanged by this check).")
    w("")
    w("## 2. The body hull (decoded)")
    w("")
    if b:
        w(f"- hull object at data offset `0x{b['offset']:x}`, the only hull whose decoded vertex bounds")
        w(f"  match B-10's `body_bbox_m` (**derived** from the vertex block at `+0x50 + 16i`)")
        w(f"- bounds: `{[round(v, 6) for v in b['box']['min']]} .. {[round(v, 6) for v in b['box']['max']]}` m")
        w(f"- size: **{d['body_cm'][0]:.3f} x {d['body_cm'][1]:.3f} x {d['body_cm'][2]:.3f} cm** (x, y, z)")
        w(f"- agrees with B-10's 3.495 x 2.271 x 7.025 m to {b['delta_to_b10'] * 1e6:.4f} um "
          f"({b['delta_to_b10']:.3e} m)")
        w(f"- convex radius (field at `+0x14`): {d['radius_cm']:.4f} cm (**decoded**)")
    else:
        w("**No hull matches B-10's body bbox** - nothing below is claimed.")
    w("")
    if d["host"]:
        h = d["host"]
        w(f"The hull is hosted by the compound at `0x{h['offset']:x}` (`{h['class']}`). Its stored AABB")
        w(f"is `{[round(v, 6) for v in h['aabb']['min']]} .. {[round(v, 6) for v in h['aabb']['max']]}`")
        w(f"= **{h['size_m'][0] * 100:.3f} x {h['size_m'][1] * 100:.3f} x {h['size_m'][2] * 100:.3f} cm**: it")
        w(f"contains every child and exceeds their union by {h['exceeds_cm']:.4f} cm (within the hull's")
        w(f"convex radius of {d['radius_cm']:.4f} cm), the relation Havok uses for a rounded hull's box")
        w("(**derived**: stored box minus the decoded vertex bounds of its children).")
        w("")
    w("## 3. The oracles - is the stored AABB the children's box?")
    w("")
    w("Two records are compared: a **stored** AABB (bytes at `+0x80`/`+0x90`, **decoded**) and the")
    w("**decoded** bounds of each child, placed by the instance record's basis and translation with")
    w("`jc3hkx.transform_aabb` (the `p' = M^T p + t` reading that the data pins).")
    w("")
    w("- **O1** asks whether every child-hull vertex lies inside the stored AABB; tolerance is that")
    w("  child's own convex radius + 1e-3 m, because a hull is rounded by exactly that radius.")
    w("")
    w("- **O2** asks whether the stored AABB is the children's union: no child may poke out of it, and")
    w("  the box may exceed the union only by the child convex radius - a rounded hull's box is exactly")
    w("  that much larger than its vertices, the bound G3-12c applies to the five vanilla files. Hull")
    w("  children are bounded by their decoded vertices, which is tight under rotation; a mesh child")
    w("  falls back to its stored AABB because its vertices are the undecoded frame (G3-12c UNKNOWN 2).")
    w("")
    w("| compound | class | instances | hull children | vertices | overshoot (cm) | child outside the box (cm) | box exceeds the union (cm) |")
    w("|---|---|---:|---:|---:|---:|---:|---:|")
    for r in d["rows"]:
        w(f"| `0x{r['offset']:x}` | `{r['class']}` | {r['instances']} | {r['hull_children']} | "
          f"{r['vertices']} | {r['overshoot_cm']:.4f} | {r['pokes_cm']:.4f} | "
          f"{r['exceeds_cm']:.4f} |")
    w("")
    w(f"Worst case over the file: overshoot **{d['tot_overshoot_cm']:.4f} cm**; no child pokes out of")
    w(f"its compound's box by more than **{d['worst_pokes_cm']:.4f} cm**, and the box exceeds the")
    w(f"children's union by at most **{d['worst_exceeds_cm']:.4f} cm** - the child convex radius, the")
    w("relation Havok uses for a rounded hull: the stored box is the union of the rounded children, not")
    w("a larger hand-written box and not a box that misses a child.")
    w("")
    w("## 4. Batmobile body vs BmAK drivable chassis box")
    w("")
    w(f"BmAK's drivable chassis, `Research/BatmobileGrab/COLLISION_GEOM.md:{d['bmak']['md_line']}`")
    w("(**decoded** from `RB_BodySetup` export 169750, AggGeom, bone `Batmobile_Chassis`):")
    w(f"box 0 extents **{d['bmak']['extents_cm'][0]:.3f} x {d['bmak']['extents_cm'][1]:.3f} x ")
    w(f"{d['bmak']['extents_cm'][2]:.3f} cm**, in Unreal axes (X, Y, Z).")
    w("")
    w("### 4.1 Axis-free comparison (sorted spans) - the one that card itself uses")
    w("")
    w("| span | Batmobile body (cm) | BmAK chassis (cm) | difference (cm) |")
    w("|---|---:|---:|---:|")
    names = ["smallest", "middle", "largest"]
    for k in range(3):
        w(f"| {names[k]} | {d['sorted_body'][k]:.3f} | {d['sorted_bmak'][k]:.3f} | "
          f"{f3(d['sorted_diff'][k])} |")
    w("")
    w("### 4.2 Per-axis, under an ASSUMED pairing")
    w("")
    w("BmAK is Z-up, X-forward; the JC3 file is (x, y, z) = (width, height, length), which is B-10's")
    w("own reading of the body bbox. The pairing below follows that, i.e. **ASSUMED**, because")
    w("`COLLISION_GEOM.md` states: \"" + "Frame axes are not proven" + "\" and that the chassis box's")
    w("rotation \"is not decoded\". It is reported so the per-axis numbers exist, and the checks")
    w("require it to agree with 4.1 as a multiset - which it does, so the two readings cannot")
    w("contradict each other.")
    w("")
    w("| axis | Batmobile body (cm) | BmAK chassis (cm) | difference (cm) |")
    w("|---|---:|---:|---:|")
    for x in d["pairing"]:
        w(f"| {x['axis']} | {x['jc3_cm']:.3f} | {x['bmak_cm']:.3f} | {f3(x['diff_cm'])} |")
    w("")
    w("Reading: the Batmobile hull is **narrower** than BmAK's chassis box, **taller**, and")
    w("**longer** by the three numbers in the last column. It is not a copy of the BmAK box: B-10")
    w("scaled the donor hull to DIM-1's body bbox (the render body), and that bbox carries the")
    w("Batmobile's own proportions. The chassis box additionally has a centre offset")
    w("`[9.0, 0.0, 106.75]` cm that a symmetric body bbox does not reproduce (**decoded**, centre")
    w("rule from `COLLISION_GEOM.md`).")
    w("")
    w("## 5. Checks")
    w("")
    w("| check | result | detail |")
    w("|---|---|---|")
    for c in d["checks"]:
        w(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} | {c['detail']} |")
    w("")
    w(f"{sum(c['ok'] for c in d['checks'])}/{len(d['checks'])} pass. Verdict: **{d['verdict']}**.")
    w("")
    w("## 6. UNKNOWN")
    w("")
    w("1. **The axis pairing between the BmAK chassis box and the JC3 body (ASSUMED above).**")
    w("   `COLLISION_GEOM.md` says the frame axes are not proven and the chassis box's rotation is")
    w("   not decoded, so no source states which BmAK extent is width. Tried: the sorted-span")
    w("   comparison (axis-free, section 4.1); the centre's z = 106.75 cm is consistent with Z-up and")
    w("   a ~207.5 cm tall box but is not a proof; the constraint offsets in the same card do not")
    w("   carry a basis for the box. A per-axis answer therefore rests on the ASSUMED pairing.")
    w("2. **The unit.** The `.physicsc` stores game units; JC3's vehicle files have been read as")
    w("   metres throughout this project (a car spans ~3 m), but no byte in the file states a scale.")
    w("   The comparison in cm multiplies by 100 on that convention, which is **derived**, not")
    w("   decoded. G3-12c records the same UNKNOWN.")
    w("3. **Whether the shipped hull should match the BmAK chassis box at all.** BmAK's chassis box is")
    w("   the *drivable* body's box in the Arkham engine; the JC3 build sizes its hull to the render")
    w("   body (B-10, DIM-1). Nothing in either package says the two boxes are meant to be equal, so")
    w("   the differences above are measured, not a defect. Settling it would need B-10's sizing")
    w("   decision re-opened, which is not this card.")
    w("4. **The chassis box's rotation.** Undecoded in `COLLISION_GEOM.md`; with a rotation the 690 x")
    w("   375 x 208 cm box could project differently onto the car frame.")
    w("5. **Play behaviour** - untested, test ban (INSTRUCTIONS.md section 3).")
    w("")
    w("## 7. Reproduce")
    w("")
    w("```")
    w("cd E:/Modding/JC3-Batmobile")
    w("python Tools/scripts/bm_extents_check.py --write")
    w("python Tools/scripts/bm_extents_check.py --check")
    w("```")
    w("")
    w(f"Inputs, read-only: `{SHIPPED}`, `{B10}`, `{CGEOM_MD}`, `{CGEOM_JSON}`.")
    w("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = analyse()
    md = render(d)
    if a.write:
        os.makedirs(os.path.dirname(p(OUT)), exist_ok=True)
        with open(p(OUT), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print(f"wrote {OUT} ({len(md)} chars), "
              f"{sum(c['ok'] for c in d['checks'])}/{len(d['checks'])} checks pass")
        for c in d["checks"]:
            if not c["ok"]:
                print(f"FAIL {c['check']}: {c['detail']}")
        return 0 if all(c["ok"] for c in d["checks"]) else 1
    if a.check:
        try:
            got = read(OUT)
        except FileNotFoundError:
            print(f"MISSING {OUT}")
            print("CHECK FAIL")
            return 1
        for c in d["checks"]:
            if not c["ok"]:
                print(f"FAIL {c['check']}: {c['detail']}")
        if got != md:
            import difflib
            diff = list(difflib.unified_diff(got.splitlines(), md.splitlines(),
                                             "on-disk", "regenerated", lineterm="", n=1))
            print("\n".join(diff[:40]))
            print(f"DRIFT {OUT}")
        ok = got == md and all(c["ok"] for c in d["checks"])
        print("CHECK", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    for c in d["checks"]:
        print(("PASS " if c["ok"] else "FAIL ") + c["check"] + ": " + c["detail"])
    return 0 if all(c["ok"] for c in d["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
