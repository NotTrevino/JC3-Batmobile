"""t22_collision.py - T-22: collision translation (the hull set for the Batmobile).

The card asks for three things in one row set (`T-P3`, `T-CO2`, `T-CO3`) that G2-30
unblocked: a hull set derived from the Batmobile body, the convex-decomposition
parameters that exist (max hulls, convex radius), and the part hull bindings
(`parts[].has_world_collision_shape`), with the wheel stations unchanged (R3).

What the files say, and how this tool reads it:

  BmAK     `Research/BatmobileGrab/PHYSICS.json` - 4 packages, 32 `RB_BodySetup`
           bodies each, byte-identical layouts, every body one box.  PHYSICS.md
           states the two facts this card turns on: there is no chassis body, and
           the asset is the *destroyed* wreck (18 of the 32 bodies are debris).
  JC3      the donor `sportsmuscle.physicsc` decoded with `jc3hkx` (G2-8): 54
           convex-hull objects, 22 compounds, one hull per part, `convex_radius`
           per hull; the compound instances carry `CPfxPartIndexProperty`, so each
           hull has a part.
  flags    the donor `sportsmuscle_vehicle_parts.vmodc` through `jc3adf` (G2-7):
           `parts[].has_world_collision_shape` and `world_collision_body_id`.
  stations `Working/TrueScale/stations.json` - the assembled car's four corners;
           the donor physicsc carries no station quad at all (`jc3hkx.stations`).

The hull set is therefore *not* a decomposition of the Batmobile mesh: authoring a
brand-new hull needs the face table's unnamed prefix block (G2-30 §6), which is
UNKNOWN, and the object count is fixed at 54.  What is writable is the proven
case - an existing hull slot, uniformly scaled and translated.  So the card's
"convex decomposition parameters" resolve to: max hulls 54, one hull per part,
convex radius = the donor hull's radius x k.  That is recorded as it is, not
dressed up as a decomposition the writer cannot do.

Usage:
  python t22_collision.py --write   # t16_collision.json + the three row lines
  python t22_collision.py --check   # re-derive and compare json, rows and ledger
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf                                   # noqa: E402
import jc3hkx as H                              # noqa: E402

WORK = os.path.join(ROOT, "Working", "Translation")
OUT_JSON = os.path.join(WORK, "t16_collision.json")
T1 = os.path.join(WORK, "T1_TRANSLATION.md")
T2 = os.path.join(WORK, "T2_TRANSLATION.md")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
PHYSICS = os.path.join(ROOT, "Research", "BatmobileGrab", "PHYSICS.json")
PARTS = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
STATIONS = os.path.join(ROOT, "Working", "TrueScale", "stations.json")
MANIFEST = os.path.join(ROOT, "Working", "Appearance", "build_parts", "parts_manifest.json")
PARTS_MODULE = os.path.join(
    ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
    "v0300_car_kensington_sportsmuscle", "sportsmuscle_vehicle_parts.vmodc")
# G3-16: the asset the *drivable* car simulates (2 bodies / 3 boxes / 1 constraint).
# T-22 was closed on the 32-body wreck census; the card is reopened on this file.
COLLISION_WHERE = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_WHERE.json")


def fmt_cm(b: dict) -> str:
    """A BmAK box element as one cell: extents and centre, both cm."""
    x, y, z = b["extents_cm"]
    cx, cy, cz = b["centre_cm"]
    return f"{x:.3f}x{y:.3f}x{z:.3f} cm at ({cx:g}, {cy:g}, {cz:g})"

# BmAK bone -> donor part.  A wheel is two bodies (the suspension arm and the wheel
# mesh); the donor has one hull per wheel, so the larger box is the envelope and the
# other one is recorded as folded into it.  `None` targets are explained per bone.
BONE_PART = {
    "SUSP2_Wheel_Front_Left_Mesh": "sportsmuscle_wheel_f_l",
    "Wheel_Front_Left_Vis_Mesh": "sportsmuscle_wheel_f_l",
    "SUSP2_Wheel_Front_Right_Mesh": "sportsmuscle_wheel_f_r",
    "Wheel_Front_Right_Vis_Mesh": "sportsmuscle_wheel_f_r",
    "SUSP1_Wheel_Rear_Left_Mesh": "sportsmuscle_wheel_r_l",
    "Wheel_Back_Left_Vis_Mesh": "sportsmuscle_wheel_r_l",
    "SUSP1_Wheel_Rear_Right_Mesh": "sportsmuscle_wheel_r_r",
    "Wheel_Rear_Right_Vis_Mesh": "sportsmuscle_wheel_r_r",
    "CockPit_Mesh": "sportsmuscle_body",
    "Rear_Door_BOTTOM": "sportsmuscle_door_f_l",
    "Rear_Door_MIDDLE": "sportsmuscle_door_f_r",
    "Main_Turret_00": None,
    "Jet_Fins001": None,
    "Root": None,
}

WHY_NONE = {
    "Main_Turret_00": "the turret is a T-8 part (`batmobile_turret`); the donor has no "
                      "turret part and no free hull slot, so a new hull is needed",
    "Jet_Fins001": "the fin is cut into the T-8 aero-flap / jet parts; same missing slot",
    "Root": "the 30.3 cm origin cube is the wreck's root placeholder, not a part",
}

WHEEL = "wheel/suspension"
DEBRIS = "destruction debris"


def _round(v: float, n: int = 4) -> float:
    return round(float(v), n)


def _box_m(extents_cm: list) -> dict:
    """A BmAK box in metres: `extents` is the full extent, so half is the radius."""
    return {"full": [_round(e / 100.0) for e in extents_cm]}


def load_bmak() -> dict:
    d = json.load(open(PHYSICS, encoding="utf-8"))
    packages = sorted(d)
    first = d[packages[0]]["bodies"]
    signature = json.dumps([(b["bone"], b["extents"], b["centre"]) for b in first])
    identical = all(
        json.dumps([(b["bone"], b["extents"], b["centre"]) for b in d[p]["bodies"]]) == signature
        for p in packages)
    cats: dict[str, int] = {}
    for b in first:
        bone = b["bone"]
        cat = ("root placeholder" if bone == "Root" else
               WHEEL if ("Wheel" in bone or "SUSP" in bone) else
               "cockpit" if bone == "CockPit_Mesh" else
               "door" if bone.startswith("Rear_Door") else
               "turret" if bone == "Main_Turret_00" else
               "jet fin" if bone == "Jet_Fins001" else
               DEBRIS)
        b["category"] = cat
        cats[cat] = cats.get(cat, 0) + 1
    largest = max(first, key=lambda b: b["extents"][0] * b["extents"][1] * b["extents"][2])
    return {
        "packages": len(packages),
        "bodies": len(first),
        "layouts_identical": identical,
        "categories": cats,
        "bodies_all": first,
        "largest": {"bone": largest["bone"],
                    "extents_cm": largest["extents"],
                    "box_m": _box_m(largest["extents"])["full"]},
        "spheres": sum(b["spheres"] for b in first),
        "box_count": sum(b["boxes"] for b in first),
    }


def load_donor() -> dict:
    blob = open(H.DONOR, "rb").read()
    pf = H.Packfile(blob)
    names = H.load_part_names()
    ee = H.DONOR_EE
    hulls: dict[int, dict] = {}
    bound: dict[int, int] = {}
    compounds = 0
    for o in pf.objects:
        if o.cls not in H.COMPOUND_CLASSES:
            continue
        compounds += 1
        d = H.decode_compound(pf, o.offset, o.cls)
        for inst in d["instances"]:
            sh = inst["shape"]
            if not sh or inst["shape_class"] != H.POLYTOPE:
                continue
            if sh not in hulls:
                h = H.decode_polytope(pf, sh)
                idx = inst["part_index"]
                hulls[sh] = {
                    "part_index": idx,
                    "part": names.get((ee, idx)) if idx is not None else None,
                    "vertices": h["vertex_count"],
                    "planes": h["plane_count"],
                    "extent": h["extent"],
                    "radius": h["convex_radius"],
                    "box": [_round(h["bounds"]["max"][k] - h["bounds"]["min"][k]) for k in range(3)],
                    "box_precise": [h["bounds"]["max"][k] - h["bounds"]["min"][k]
                                    for k in range(3)],
                    "bounds_min": [_round(x) for x in h["bounds"]["min"]],
                    "bounds_max": [_round(x) for x in h["bounds"]["max"]],
                }
            if inst["part_index"] is not None:
                bound[hulls[sh]["part_index"]] = bound.get(hulls[sh]["part_index"], 0) + 1

    # parts module flags (G2-7)
    adf = jc3adf.Adf(open(PARTS_MODULE, "rb").read())
    flags = jc3adf.parts(adf)
    rows = [json.loads(l) for l in open(PARTS, encoding="utf-8") if l.strip()]
    rec = next(r for r in rows if r["entity"] == ee)
    part_rows = []
    for i, p in enumerate(rec["parts"]):
        f = flags[i]
        part_rows.append({
            "part_index": i,
            "part": p["n"],
            "damage_type": p["dt"],
            "has_world_collision_shape": int(f["has_world_collision_shape"]),
            "world_collision_body_id": int(f["world_collision_body_id"]),
            "hulls": sum(1 for h in hulls.values() if h["part_index"] == i),
        })
    per_part = sorted((h for h in hulls.values()), key=lambda h: (h["part"] or ""))
    radii = sorted(h["radius"] for h in hulls.values())
    return {
        "physicsc": os.path.relpath(H.DONOR, ROOT).replace(os.sep, "/"),
        "bytes": len(blob),
        "objects": len(pf.objects),
        "compounds": compounds,
        "hulls": len(hulls),
        "hulls_bound_to_a_part": sum(1 for h in hulls.values() if h["part"] is not None),
        "hulls_unbound": sum(1 for h in hulls.values() if h["part"] is None),
        "parts": len(part_rows),
        "parts_with_world_collision": sum(p["has_world_collision_shape"] for p in part_rows),
        "parts_without": [p["part"] for p in part_rows if not p["has_world_collision_shape"]],
        "hull_extent_range": [min(h["extent"] for h in hulls.values()),
                              max(h["extent"] for h in hulls.values())],
        "hull_vertex_range": [min(h["vertices"] for h in hulls.values()),
                              max(h["vertices"] for h in hulls.values())],
        "hull_plane_range": [min(h["planes"] for h in hulls.values()),
                             max(h["planes"] for h in hulls.values())],
        "hull_radius_median": _round(radii[len(radii) // 2], 6),
        "hull_radius_min": _round(radii[0], 6),
        "hull_radius_max": _round(radii[-1], 6),
        "part_rows": part_rows,
        "hulls_by_part": per_part,
        "stations_in_file": len(H.stations(pf)),
    }


def build() -> dict:
    bmak = load_bmak()
    donor = load_donor()
    st = json.load(open(STATIONS, encoding="utf-8"))
    man = json.load(open(MANIFEST, encoding="utf-8"))
    body_lo, body_hi = man["body_bbox_m"]
    body_box = [_round(body_hi[k] - body_lo[k]) for k in range(3)]

    by_bone = {b["bone"]: b for b in bmak["bodies_all"]}
    hull_by_part = {h["part"]: h for h in donor["hulls_by_part"] if h["part"]}

    # The tyre diameter is the Batmobile's own measured number, not the suspension
    # arm's box: 2 x the station radius, which is the contact radius by design
    # (`TYRES.md` §1: 1.3652-1.3657 = 2 x 0.6826-0.6829).  G2-30 scaled the donor
    # wheel hull by exactly tyre_d / 0.8225 and the file re-read clean.
    tyre_d = 2 * sum(v["radius"] for v in st["corners"].values()) / len(st["corners"])

    # one donor slot per target part.  The body hull is the chassis envelope (the
    # assembled body bbox), so the cockpit box is folded into it; a wheel is two
    # BmAK bodies (the tyre and the suspension arm) and the donor's slot is the tyre.
    groups: dict[str, list] = {}
    for bone, part in BONE_PART.items():
        if part:
            groups.setdefault(part, []).append(bone)
    envelope: dict[str, str | None] = {}
    folded: dict[str, list] = {}
    for part, bones in groups.items():
        if part == "sportsmuscle_body":
            envelope[part] = None
            folded[part] = bones
        elif "_wheel_" in part:
            vis = [b for b in bones if b.startswith("Wheel_")]
            envelope[part] = vis[0] if vis else bones[0]
            folded[part] = [b for b in bones if b != envelope[part]]
        else:
            ranked = sorted(bones, key=lambda b: -(lambda e: e[0] * e[1] * e[2])(
                by_bone[b]["extents"]))
            envelope[part] = ranked[0]
            folded[part] = ranked[1:]

    mapped = []
    for part, bone in sorted(envelope.items()):
        if bone is None:
            continue
        h = hull_by_part[part]
        box = [e / 100.0 for e in by_bone[bone]["extents"]]
        if "_wheel_" in part:
            k = k_out = tyre_d / max(h["box_precise"])
            basis = "tyre diameter / donor wheel hull's longest axis"
        else:
            ratios = [box[j] / h["box_precise"][j] for j in range(3)
                      if h["box_precise"][j] > 1e-6]
            k, k_out = min(ratios), max(ratios)
            basis = ("min(box axis / donor hull axis): k_in fits inside the box, "
                     "k_out covers it - one uniform factor cannot match both")
        mapped.append({
            "bone": bone,
            "category": by_bone[bone]["category"],
            "box_m": [_round(x) for x in box],
            "centre_cm": by_bone[bone]["centre"],
            "target_part": part,
            "target_part_index": h["part_index"],
            "donor_hull": {"vertices": h["vertices"], "planes": h["planes"],
                           "extent": h["extent"], "box_m": h["box"],
                           "radius": _round(h["radius"], 6)},
            "scale_basis": basis,
            "scale_k": _round(k, 6),
            "scale_k_out": _round(k_out, 6),
            "radius_after": _round(h["radius"] * k, 6),
            "box_after_m": [_round(h["box_precise"][j] * k) for j in range(3)],
            "folded_bones": folded[part],
        })

    # the body: no BmAK body box exists, so the donor body hull is scaled to the
    # assembled body bbox (one donor hull slot, uniform k = the binding axis)
    body_hull = hull_by_part["sportsmuscle_body"]
    body_k = min(body_box[j] / body_hull["box"][j] for j in range(3))
    body = {
        "bbox_m": body_box,
        "target_part": "sportsmuscle_body",
        "donor_hull": {"vertices": body_hull["vertices"], "planes": body_hull["planes"],
                       "extent": body_hull["extent"], "box_m": body_hull["box"],
                       "radius": _round(body_hull["radius"], 6)},
        "scale_k": _round(body_k, 6),
        "scale_k_out": _round(max(body_box[j] / body_hull["box_precise"][j] for j in range(3)), 6),
        "radius_after": _round(body_hull["radius"] * body_k, 6),
        "box_after_m": [_round(body_hull["box"][j] * body_k) for j in range(3)],
        "folded_bones": folded.get("sportsmuscle_body", []),
        "note": "one hull (the donor's) covers the chassis; the fine shell is the "
                "hknpExternMeshShape, whose quantization frame is UNKNOWN (G2-30)",
    }

    unmapped = []
    for b in bmak["bodies_all"]:
        if b["bone"] in envelope.values():
            continue
        if b["bone"] in [x for v in folded.values() for x in v]:
            continue
        part = BONE_PART.get(b["bone"])
        unmapped.append({
            "bone": b["bone"],
            "category": b["category"],
            "box_m": _box_m(b["extents"])["full"],
            "reason": WHY_NONE.get(b["bone"],
                                   "a wreck debris fragment: RB_BodySetup of the destroyed asset, "
                                   "not a part of the driveable car"),
        })

    flags = donor["part_rows"]
    mapped_bones = (sum(1 for m in mapped for _ in [m["bone"]] + m["folded_bones"])
                    + len(body["folded_bones"]))
    cols = [f"{p['part_index']}" for p in flags if p["has_world_collision_shape"]]
    no = [p for p in flags if not p["has_world_collision_shape"]]

    dec = {
        "max_hulls": donor["hulls"],
        "hulls_per_part": 1,
        "unbound_hull_instances": donor["hulls"] - donor["hulls_bound_to_a_part"],
        "new_hull": "UNKNOWN - a hull authored from a mesh needs the face table's unnamed "
                    "0/16/32/48-byte prefix (G2-30 §6, UNKNOWN 1), so only an existing "
                    "slot can be written; the object count (54) is fixed",
        "parameters": {"scale_k": "one uniform scale per hull - the only factor G2-30 proved. "
                                "For a wheel it is the tyre diameter / the hull's longest axis; "
                                "for any other part k_in (fits inside the box) and k_out "
                                "(covers it) differ, and B-10 has to choose per part",
                       "translation": "the part's pivot (bat_assemble T(p), R2)",
                       "convex_radius": "donor radius x k (G2-30's scaled-hull case)"},
        "unbound_note": "the 14 unbound hull instances belong to the donor's two bumpers "
                        "(no part index), so they are not free slots; the object count is "
                        "fixed at 54 either way",
        "tyre_diameter_m": _round(tyre_d, 4),
        "tyre_basis": "2 x stations.json radius (TYRES.md §1: the tread diameter is 2 x the "
                      "contact radius by design)",
    }

    t8 = len(json.load(open(os.path.join(WORK, "T8_PARTS.json"), encoding="utf-8"))["parts"])
    cw = json.load(open(COLLISION_WHERE, encoding="utf-8"))
    rows = render_rows(bmak, donor, mapped, body, st, unmapped, t8, cw)
    old_prose, new_prose = prose_fix(bmak)
    return {
        "schema": 1,
        "generator": "Tools/scripts/t22_collision.py",
        "card": "T-22",
        "inputs": {
            "bmak_physics": "Research/BatmobileGrab/PHYSICS.json (G1-13)",
            "jc3_physicsc": donor["physicsc"] + " (G2-8)",
            "jc3_parts_module": "Builds/test-091/aaf/models/jc_vehicles/01_land/"
                                "v0300_car_kensington_sportsmuscle/"
                                "sportsmuscle_vehicle_parts.vmodc (G2-7)",
            "parts_table": "Research/JC3Grab/PARTS_TABLE.jsonl (G2-7)",
            "stations": "Working/TrueScale/stations.json",
            "t8_parts": "Working/Translation/T8_PARTS.json (T-12, the new moving parts)",
            "body_bbox": "Working/Appearance/build_parts/parts_manifest.json",
            "drivable_asset": "Research/BatmobileGrab/COLLISION_WHERE.json (G3-16)",
        },
        "drivable_asset": {
            "path": cw["drivable_asset"]["path"],
            "export": cw["drivable_asset"]["export"],
            "size": cw["drivable_asset"]["size"],
            "bodies": len(cw["drivable_bodies"]),
            "boxes": sum(b["box_count"] for b in cw["drivable_bodies"]),
            "constraints": cw["drivable_asset"]["arrays"]["ConstraintSetup"]["count"],
            "reached_from": "Batmobile.SVehicleMesh property offset 824",
            "note": "the drivable car's rigid body, superseding the 32-body wreck census this "
                    "card was closed on; plan in T22_REOPEN.md",
        },
        "bmak": {k: bmak[k] for k in
                 ("packages", "bodies", "layouts_identical", "categories", "largest",
                  "spheres", "box_count")},
        "donor": {k: donor[k] for k in
                  ("bytes", "objects", "compounds", "hulls", "hulls_bound_to_a_part",
                   "hulls_unbound", "parts", "parts_with_world_collision", "parts_without",
                   "hull_extent_range", "hull_vertex_range", "hull_plane_range",
                   "hull_radius_median", "hull_radius_min", "hull_radius_max",
                   "stations_in_file")},
        "donor_parts": donor["part_rows"],
        "decomposition": dec,
        "hull_set": {"body": body, "parts": mapped, "unmapped": unmapped,
                     "mapped_bodies": mapped_bones,
                     "mapped_slots": len(mapped) + 1,
                     "unmapped_bodies": len(unmapped)},
        "bindings": {
            "with_world_collision": len(cols),
            "without": [{"part": p["part"], "part_index": p["part_index"],
                         "world_collision_body_id": p["world_collision_body_id"]} for p in no],
            "wheels": "both sides are sim-only: the donor's four wheels are the only parts "
                      "with has_world_collision_shape 0 / world_collision_body_id -1",
        },
        "stations": {
            "source": "Working/TrueScale/stations.json",
            "corners": {c: {"hub_true": v["hub_true"], "radius": v["radius"],
                            "tyre_width": v["tyre_width"]} for c, v in st["corners"].items()},
            "in_physicsc": donor["stations_in_file"],
            "unchanged": "R3: no wheel/station row is touched; the quads live in the "
                         "vmodc's base_wheel_hardpoint_positions + land_global, not in the "
                         "physicsc (0 sets there)",
        },
        "rows": rows,
        "prose_fix": {"file": "Working/Translation/T2_TRANSLATION.md",
                      "old": old_prose, "new": new_prose},
        "summary": {
            "bodies": bmak["bodies"],
            "mapped_to_a_slot": len(mapped) + 1,
            "mapped_bodies": mapped_bones,
            "unmapped": len(unmapped),
            "hull_slots": donor["hulls"],
            "parts_colliding": donor["parts_with_world_collision"],
            "rows": len(rows),
            "drivable_bodies": len(cw["drivable_bodies"]),
            "drivable_boxes": sum(b["box_count"] for b in cw["drivable_bodies"]),
            "dispositions": {"T-P3": "next", "T-CO2": "next", "T-CO3": "next"},
        },
    }


def render_rows(bmak: dict, donor: dict, mapped: list, body: dict, st: dict,
                doc_unmapped: list, doc_t8_parts: int, cw: dict) -> dict:
    """The three row lines, as text: the tables are the card's `Out`.

    Reopened 2026-11-07 on `COLLISION_WHERE.md` (G3-16): the rows name the *drivable* asset
    (`Physics.Batmobile_V3_Physics`: 2 bodies / 3 boxes / 1 constraint) as the hull target, and
    say that the built set still carries the donor's 62 bodies.
    """
    mapped_bones = (sum(1 for m in mapped for _ in [m["bone"]] + m["folded_bones"])
                    + len(body["folded_bones"]))
    slots = len(mapped) + 1                       # + the body slot
    largest = bmak["largest"]["box_m"]
    drv = cw["drivable_asset"]
    ch_body, pod_body = cw["drivable_bodies"][0], cw["drivable_bodies"][1]
    c0, c1 = ch_body["boxes"][0], ch_body["boxes"][1]
    pb = pod_body["boxes"][0]
    n_boxes = sum(b["box_count"] for b in cw["drivable_bodies"])
    unmapped = bmak["bodies"] - mapped_bones
    cats: dict[str, int] = {}
    for u in doc_unmapped:
        cats[u["category"]] = cats.get(u["category"], 0) + 1
    wreck = ", ".join(f"{n} {c}" for c, n in sorted(cats.items(), key=lambda kv: -kv[1]))
    t8_parts = doc_t8_parts
    t_p3 = [
        "T-P3",
        f"{bmak['bodies']} wreck bodies (boxes) + the **drivable asset {len(cw['drivable_bodies'])} "
        f"bodies / {n_boxes} boxes** (`COLLISION_WHERE.md`: chassis {fmt_cm(c0)}, chassis "
        f"{fmt_cm(c1)}; weapons pod {fmt_cm(pb)})",
        "`.physicsc` shapes",
        "existing hull slots, uniform k per hull (G2-30)",
        f"**decoded (asset, 2026-11-07)**: the drivable rigid body is `{drv['path']}` "
        f"({drv['package']} export {drv['export']}: 2 bodies, {n_boxes} boxes, 1 constraint, "
        f"reached from `Batmobile.SVehicleMesh` property offset 824) - the hull set must be "
        f"those 2 bodies, not the {mapped_bones} of {bmak['bodies']} wreck boxes G2-30 could "
        f"reach; the built set still carries 62 donor bodies with body 0's single hull rewritten "
        f"(bm-009/bm-RC2, B-10e), so 2 shapes are missing (T-22 reopened)",
        "`T22_REOPEN.md` (plan) + `t22_reopen.py --check`",
    ]
    t_co2 = [
        "T-CO2",
        f"largest **wreck** box {bmak['largest']['extents_cm'][0]:.2f}x"
        f"{bmak['largest']['extents_cm'][1]:.2f}x{bmak['largest']['extents_cm'][2]:.2f} cm; "
        f"the drivable car's largest is the chassis box {c0['extents_cm'][0]:.3f}x"
        f"{c0['extents_cm'][1]:.3f}x{c0['extents_cm'][2]:.3f} cm",
        "—",
        "1 cm = 0.01 m; JC3 hull space is metres",
        f"{largest[0]:.4f}x{largest[1]:.4f}x{largest[2]:.4f} m fits one donor hull "
        f"(longest hull axis {max(max(h['box_precise']) for h in donor['hulls_by_part']):.3f} m) "
        f"- a wreck wheel, not the car's collision",
        "next: keep the wreck-set maximum and do not author it as the car; the car's target is "
        f"T-P3's chassis body ({c0['extents_cm'][0]:.3f}x{c0['extents_cm'][1]:.3f}x"
        f"{c0['extents_cm'][2]:.3f} cm)",
        "decoded (COLLISION_WHERE) / measured (T-22)",
        "`t22_reopen.py --check`",
    ]
    flags = donor["parts_with_world_collision"]
    t_co3 = [
        "T-CO3",
        "**no per-part world-collision flag**: the drivable asset is **2 bodies / 3 boxes + 1 "
        "constraint** (`COLLISION_WHERE.md`): one `Batmobile_Chassis` body and one "
        "`Batmobile_Rig_Weapons_Trans` body; the two Batman-vs-Batmobile meshes are separate "
        "components and the wreck has 32 bodies",
        "`parts[].has_world_collision_shape`",
        "donor carry (restated)",
        f"donor's: {flags}/{donor['parts']} = 1, the 4 wheels = 0 "
        f"(`world_collision_body_id` -1); bm-RC2 has 61 parts, so the "
        f"{donor['parts']}-part denominator is stale",
        "next: keep the donor's flags and restate the reason - BmAK's 2 bodies prove the car "
        "has no per-part world bodies while the donor gives 38 parts their own, a declared "
        "difference; the chassis hull covers the wheels, so a player should not notice",
        "decoded (asset) / measured (T-22)",
        "`t22_collision.py --check` re-read at the RC2 part count",
    ]
    return {
        "T-P3": "| " + " | ".join(t_p3) + " |",
        "T-CO2": "| " + " | ".join(t_co2) + " |",
        "T-CO3": "| " + " | ".join(t_co3) + " |",
    }


PROSE_RE = r"largest box extents `\[[^\]]*\]` cm(?: \(`[^`]*`\))?"


def prose_fix(bmak: dict) -> tuple[str, str]:
    """T-2b §7's 'largest box' sentence named the front-left suspension box; the
    largest by volume is the rear-left one.  The row carries the true maximum, so
    the sentence is regenerated too rather than left contradicting it."""
    x, y, z = bmak["largest"]["extents_cm"]
    new = f"largest box extents `[{x:.1f}, {y:.1f}, {z:.1f}]` cm"
    return PROSE_RE, new


def write_docs(doc: dict) -> None:
    rows = doc["rows"]
    for path, ids in ((T1, ["T-P3"]), (T2, ["T-CO2", "T-CO3"])):
        raw = open(path, "rb").read()
        crlf = b"\r\n" in raw
        lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
        for rid in ids:
            hit = [i for i, l in enumerate(lines) if l.startswith(f"| {rid} |")]
            if len(hit) != 1:
                raise SystemExit(f"{path}: {rid} found {len(hit)} times")
            lines[hit[0]] = rows[rid]
        text = "\n".join(lines)
        pf = doc["prose_fix"]
        if path == T2:
            hits = len(re.findall(pf["old"], text))
            if hits != 1:
                raise SystemExit(f"{path}: the §7 'largest box' sentence occurs {hits} times")
            text = re.sub(pf["old"], pf["new"], text)
        if crlf:
            text = text.replace("\n", "\r\n")
        with open(path, "wb") as f:
            f.write(text.encode("utf-8"))


def check(doc: dict) -> int:
    fresh = build()
    problems: list[str] = []
    if json.dumps(doc, indent=1) != json.dumps(fresh, indent=1):
        a, b = json.dumps(doc, indent=1), json.dumps(fresh, indent=1)
        at = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        problems.append(f"{os.path.basename(OUT_JSON)} differs from the re-derived record "
                        f"at char {at}")
    t2_text = open(T2, encoding="utf-8").read().replace("\r\n", "\n")
    pf = fresh["prose_fix"]
    hits = re.findall(pf["old"], t2_text)
    if hits != [pf["new"]]:
        problems.append(f"T2_TRANSLATION.md: the §7 'largest box' sentence reads {hits}")
    for path, ids in ((T1, ["T-P3"]), (T2, ["T-CO2", "T-CO3"])):
        lines = open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
        for rid in ids:
            hit = [l for l in lines if l.startswith(f"| {rid} |")]
            if len(hit) != 1:
                problems.append(f"{os.path.basename(path)}: {rid} found {len(hit)} times")
            elif hit[0] != fresh["rows"][rid]:
                problems.append(f"{os.path.basename(path)}: {rid} row differs from the "
                                f"re-derived line")
    if os.path.exists(LEDGER):
        led = {r["id"]: r for r in
               (json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip())}
        for rid, dispo in fresh["summary"]["dispositions"].items():
            if rid not in led:
                problems.append(f"ledger: {rid} missing")
            elif led[rid]["dispo"] != dispo:
                problems.append(f"ledger: {rid} disposition {led[rid]['dispo']} != {dispo}")
    else:
        problems.append("no T_ROWS.jsonl - run `t_rows.py build`")
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    s = fresh["summary"]
    print(f"PASS: {s['bodies']} BmAK wreck bodies | drivable {s['drivable_bodies']} bodies / "
          f"{s['drivable_boxes']} boxes | {s['mapped_to_a_slot']} mapped / "
          f"{s['unmapped']} unmapped | {s['hull_slots']} donor hull slots, one per part | "
          f"{s['parts_colliding']}/42 parts collide | rows {s['rows']} "
          f"(next 3) | stations unchanged")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write the json and the row lines")
    g.add_argument("--check", action="store_true", help="re-derive and compare")
    g.add_argument("--show", action="store_true", help="print the derived rows")
    a = ap.parse_args()
    if a.show:
        doc = build()
        for line in doc["rows"].values():
            print(line)
        print(json.dumps(doc["summary"], indent=1))
        return
    if a.write:
        doc = build()
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, indent=1) + "\n")
        write_docs(doc)
        s = doc["summary"]
        print(f"wrote {os.path.relpath(OUT_JSON, ROOT)}: {s['bodies']} bodies, "
              f"{s['hull_slots']} hull slots, {s['mapped_to_a_slot']} mapped, "
              f"{s['unmapped']} unmapped; 3 rows regenerated")
        return
    if not os.path.exists(OUT_JSON):
        raise SystemExit(f"no {os.path.relpath(OUT_JSON, ROOT)} - run --write")
    doc = json.load(open(OUT_JSON, encoding="utf-8"))
    sys.exit(check(doc))


if __name__ == "__main__":
    main()
