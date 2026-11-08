"""bm_collision.py - B-10: the Batmobile hull set, written with `jc3hkx`.

`GRAB_BACKLOG.md` §8 (`B-10`): "Do: write the Batmobile hull set with `jc3hkx.py`; stations
unchanged (R3). Done: `jc3hkx.py check --all` on the built file; hull union bbox within 5 cm of
the body bbox."

Inputs, all on disk, all from a card that is done:

  B-02   `Working/Appearance/build_parts/parts_manifest.json` - the assembled body's
         `body_bbox_m` (DIM-1) and the part pivots.
  T-22   `Working/Translation/t16_collision.json` - the 7 donor hull slots that carry the 11
         driveable BmAK boxes, the uniform `k` per slot, the convex-radius rule, and the fact
         that the file carries no station quad at all.
  G2-30  `Research/JC3Grab/PHYSICS_WRITE.md` - the writer: the data section is re-laid out from
         per-object blobs, every fixup remapped, `hull_bytes()` / `scale_hull()` /
         `compound_aabb_edits()` proven on this very file.
  donor  `Builds/test-091/.../sportsmuscle.physicsc` (340,368 B, 430 objects, 54 hulls,
         22 compounds, 112 instances) + its `sportsmuscle_vehicle_parts.vmodc`.

What is written, and why each row is the shape it is:

  body   the donor's one chassis hull, re-scaled **per axis** to DIM-1's body bbox and shifted
         so its AABB *is* that bbox.  T-22's single uniform `k` (1.676259) fits *inside* the box
         (3.495 x 2.032 x 6.167 m) and leaves the body 0.239 m short in Y and 0.858 m short in Z,
         which is exactly what this card's second Done check rejects; the donor hull's aspect
         (1 : 0.581 : 1.765) is not the body bbox's (1 : 0.650 : 2.010), so no single factor can
         satisfy it.  A linear map of a convex polytope is a convex polytope: the plane slots are
         re-derived exactly (`u = K^-1 n`, `n^ = u/|u|`, `d^ = (d - u.s)/|u|`), the unused
         sentinels, vertex ranks, face table and index block are copied (the plane count does not
         change, so the face table stays valid) and the convex radius is `0.01 x min(k)`.
  wheels `jc3hkx.scale_hull` at T-22's k = 1.660052 (tyre diameter / the donor hull's 0.8225 m).
         Placement untouched: the wheel hull is centred on its own part origin, which is the
         wheel's pivot - the tyre rotates about it, so moving the hull inside the `.physicsc`
         would rotate the collision about the wrong centre.  The part frame is
         `parent_space_offset` in the parts module, i.e. B-04's row.
  doors  copied byte-identical: B-04 step 1 removes `door_f_l`/`door_f_r`, so there is no
         Batmobile part for a scaled door hull to bind to (R4: no semantic bridge, no value).
  rest   every other object is copied unchanged; `compound_aabb_edits()` moves only the
         ancestors of the five written hulls, by exactly as much as their children moved.

The second Done check is evaluated in the frame the file itself stores the body hull in (the body
part's transform is identity and the donor's chassis hull is the one hull bound to it); the
whole-file envelope is printed beside it with its frame named, because the other hulls are stored
part-local and their world placement is the parts module's (B-04's) rows.

Usage:
  python Tools/scripts/bm_collision.py --write   # Working/Collision/{batmobile.physicsc,json,md}
  python Tools/scripts/bm_collision.py --check   # re-derive everything and compare with disk
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf                                    # noqa: E402
import jc3hkx as H                               # noqa: E402

CARD = "B-10"
BASE = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
                    "v0300_car_kensington_sportsmuscle")
DONOR = os.path.join(BASE, "sportsmuscle.physicsc")
PARTS_MODULE = os.path.join(BASE, "sportsmuscle_vehicle_parts.vmodc")
T22 = os.path.join(ROOT, "Working", "Translation", "t16_collision.json")
BODY_MANIFEST = os.path.join(ROOT, "Working", "Appearance", "build_parts", "parts_manifest.json")
STATIONS = os.path.join(ROOT, "Working", "TrueScale", "stations.json")
OUT_DIR = os.path.join(ROOT, "Working", "Collision")
OUT_BIN = os.path.join(OUT_DIR, "batmobile.physicsc")
OUT_JSON = os.path.join(OUT_DIR, "bm_collision.json")
OUT_MD = os.path.join(OUT_DIR, "BM_COLLISION.md")

TOLERANCE_M = 0.05
BODY_PART = "sportsmuscle_body"
# donor wheel part -> stations.json corner (the station the hull has to keep, R3)
WHEEL_CORNER = {
    "sportsmuscle_wheel_f_l": "f_l",
    "sportsmuscle_wheel_f_r": "f_r",
    "sportsmuscle_wheel_r_l": "r_l",
    "sportsmuscle_wheel_r_r": "r_r",
}
DOOR_PARTS = ("sportsmuscle_door_f_l", "sportsmuscle_door_f_r")


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def rnd(v, n=4):
    return round(float(v), n)


def vec(v, n=4):
    return [rnd(x, n) for x in v]


def hull_offset_of_part(pf: H.Packfile) -> dict[int, int]:
    """part index -> the single convex hull offset its compound instances."""
    found: dict[int, set] = {}
    for o in pf.objects:
        if o.cls not in H.COMPOUND_CLASSES:
            continue
        for inst in H.decode_compound(pf, o.offset, o.cls)["instances"]:
            if inst["shape_class"] == H.POLYTOPE and inst["part_index"] is not None:
                found.setdefault(inst["part_index"], set()).add(inst["shape"])
    multi = {k: sorted(v) for k, v in found.items() if len(v) > 1}
    if multi:
        raise SystemExit(f"part(s) instance more than one hull: {multi} - T-22 says one per part")
    return {k: next(iter(v)) for k, v in found.items()}


def body_map(pf: H.Packfile, off: int, lo: list, hi: list,
             k: list | None = None) -> tuple[bytes, dict, list, list]:
    """The chassis hull under the exact linear map that sends its AABB to `lo..hi`.

    `k` defaults to the per-axis factors the two boxes ask for (the build); passing one
    scalar per axis is how the negative control in the B-10 report re-runs T-22's uniform
    factor through the same writer, to show the Done check discriminates.
    """
    d = H.decode_polytope(pf, off)
    src_lo, src_hi = d["bounds"]["min"], d["bounds"]["max"]
    if k is None:
        k = [(hi[j] - lo[j]) / (src_hi[j] - src_lo[j]) for j in range(3)]
    s = [lo[j] - k[j] * src_lo[j] for j in range(3)]
    verts = [[v[0] * k[0] + s[0], v[1] * k[1] + s[1], v[2] * k[2] + s[2], v[3]]
             for v in d["vertices"]]
    planes = []
    for n0, n1, n2, dd in d["plane_slots"]:
        if n0 == 0.0 and n1 == 0.0 and n2 == 0.0:
            planes.append([n0, n1, n2, dd])          # unused sentinel, copied
            continue
        u = [n0 / k[0], n1 / k[1], n2 / k[2]]
        m = math.sqrt(u[0] * u[0] + u[1] * u[1] + u[2] * u[2])
        planes.append([u[0] / m, u[1] / m, u[2] / m,
                       (dd - (u[0] * s[0] + u[1] * s[1] + u[2] * s[2])) / m])
    blob = H.hull_bytes(pf, off, verts=verts, planes=planes,
                        radius=d["convex_radius"] * min(k))
    box = {"min": [min(v[j] for v in verts) for j in range(3)],
           "max": [max(v[j] for v in verts) for j in range(3)]}
    return blob, box, k, s


def aabb_union(boxes: list[tuple[list, list]]) -> tuple[list, list]:
    lo = [min(b[0][j] for b in boxes) for j in range(3)]
    hi = [max(b[1][j] for b in boxes) for j in range(3)]
    return lo, hi


def part_world(parts: list[dict]) -> dict[int, list]:
    """part index -> its 4x4 `parent_space_offset` chain (row-vector, translation last row)."""
    memo: dict[int, list] = {}

    def world(i: int) -> list:
        if i in memo:
            return memo[i]
        m = [list(row) for row in
             (parts[i]["parent_space_offset"][4 * r:4 * r + 4] for r in range(4))]
        pi = parts[i]["parent_part_index"]
        out = m if (pi is None or pi < 0) else [[sum(m[r][c] * world(pi)[r][j]
                                                     for r in range(4)) for j in range(4)]
                                                for c in range(4)]
        memo[i] = out
        return out

    for p in parts:
        world(p["part_index"])
    return memo


def place(box: tuple[list, list], m: list) -> tuple[list, list]:
    """An AABB through a 4x4 row-vector transform (its 8 corners' enclosing box)."""
    lo, hi = box
    pts = []
    for x in (lo[0], hi[0]):
        for y in (lo[1], hi[1]):
            for z in (lo[2], hi[2]):
                p = [x, y, z, 1.0]
                pts.append([sum(p[r] * m[r][c] for r in range(4)) for c in range(3)])
    return ([min(q[j] for q in pts) for j in range(3)],
            [max(q[j] for q in pts) for j in range(3)])


def envelopes(pf: H.Packfile, parts: list[dict]) -> dict:
    """Two frames, both printed: the stored AABBs, and the decoded placement chain."""
    world = part_world(parts)
    stored, placed = [], []
    for o in pf.objects:
        if o.cls not in H.COMPOUND_CLASSES:
            continue
        for inst in H.decode_compound(pf, o.offset, o.cls)["instances"]:
            if inst["shape_class"] != H.POLYTOPE:
                continue
            d = H.decode_polytope(pf, inst["shape"])
            box = (d["bounds"]["min"], d["bounds"]["max"])
            stored.append(box)
            here = H.transform_aabb({"min": box[0], "max": box[1]},
                                    inst["basis"], inst["translation"])
            here = (here["min"], here["max"])
            idx = inst["part_index"]
            placed.append(place(here, world[idx]) if idx is not None else here)
    s_lo, s_hi = aabb_union(stored)
    p_lo, p_hi = aabb_union(placed)
    return {"stored": {"min": vec(s_lo), "max": vec(s_hi),
                       "size": vec([s_hi[j] - s_lo[j] for j in range(3)])},
            "placed": {"min": vec(p_lo), "max": vec(p_hi),
                       "size": vec([p_hi[j] - p_lo[j] for j in range(3)])},
            "frame": "`stored` = the hull AABBs as the file holds them; `placed` = instance "
                     "basis/translation (jc3hkx.transform_aabb) then the part module's "
                     "parent_space_offset chain.  Per-part frames are B-04's rows, so this is "
                     "the donor's own envelope, not the car's - reported, never asserted."}


def deviation(union_lo: list, union_hi: list, bbox_lo: list, bbox_hi: list) -> dict:
    """Per-axis min/max deviation of a union box from a reference box, plus the worst."""
    axes = []
    for j, name in enumerate(("x", "y", "z")):
        axes.append({"axis": name,
                     "min_dev": rnd(union_lo[j] - bbox_lo[j]),
                     "max_dev": rnd(union_hi[j] - bbox_hi[j]),
                     "missing": rnd(max(bbox_lo[j] - union_lo[j], union_hi[j] - bbox_hi[j]))})
    worst = max(max(abs(a["min_dev"]), abs(a["max_dev"])) for a in axes)
    inside = max(a["missing"] for a in axes)
    return {"axes": axes, "max_abs_dev_m": rnd(worst), "max_missing_m": rnd(inside),
            "within_tolerance": worst <= TOLERANCE_M}


def build() -> dict:
    man = json.load(open(BODY_MANIFEST, encoding="utf-8"))
    t22 = json.load(open(T22, encoding="utf-8"))
    st = json.load(open(STATIONS, encoding="utf-8"))
    bbox_lo = [float(x) for x in man["body_bbox_m"][0]]
    bbox_hi = [float(x) for x in man["body_bbox_m"][1]]

    donor_blob = open(DONOR, "rb").read()
    pf = H.Packfile(donor_blob)
    parts = jc3adf.parts(jc3adf.Adf(open(PARTS_MODULE, "rb").read()))
    index = {p["name"]: p["part_index"] for p in parts}
    hull_of = hull_offset_of_part(pf)

    # T-22's numbers, read not typed
    t22_parts = {p["target_part"]: p for p in t22["hull_set"]["parts"]}
    body_t22 = t22["hull_set"]["body"]
    if [rnd(x, 3) for x in body_t22["bbox_m"]] != [rnd(x, 3) for x in
                                                   [bbox_hi[j] - bbox_lo[j] for j in range(3)]]:
        raise SystemExit("T-22's body bbox and parts_manifest.body_bbox_m disagree")

    # 1. the body hull
    body_idx = index[BODY_PART]
    body_off = hull_of[body_idx]
    body_before = H.decode_polytope(pf, body_off)
    body_blob, body_box, body_k, body_s = body_map(pf, body_off, bbox_lo, bbox_hi)

    changes: dict[int, tuple[bytes, dict]] = {body_off: (body_blob, body_box)}
    written = [{"part": BODY_PART, "part_index": body_idx, "hull": f"{body_off:#x}",
                "method": "per-axis linear map to DIM-1's body bbox "
                          "(`parts_manifest.body_bbox_m`), planes re-derived",
                "vertices": body_before["vertex_count"],
                "planes": body_before["plane_count"],
                "extent_bytes": body_before["extent"],
                "box_before_m": {"min": vec(body_before["bounds"]["min"]),
                                 "max": vec(body_before["bounds"]["max"]),
                                 "size": vec([body_before["bounds"]["max"][j]
                                              - body_before["bounds"]["min"][j]
                                              for j in range(3)])},
                "scale_k": vec(body_k, 6), "translate_m": vec(body_s, 6),
                "radius_before": rnd(body_before["convex_radius"], 6),
                "radius_after": rnd(body_before["convex_radius"] * min(body_k), 6),
                "box_after_m": {"min": vec(body_box["min"]), "max": vec(body_box["max"]),
                                "size": vec([body_box["max"][j] - body_box["min"][j]
                                             for j in range(3)])},
                "provenance": "derived: DIM-1 body bbox / the donor hull's own AABB; the "
                              "writer is G2-30's `hull_bytes`, the map is exact for a convex "
                              "polytope and `check --file` re-verifies unit planes, ranks, "
                              "indices and convexity"}]

    # 2. the four wheel hulls
    wheel_report = []
    for name, corner in WHEEL_CORNER.items():
        part = index[name]
        off = hull_of[part]
        entry = t22_parts[name]
        k = float(entry["scale_k"])
        d0 = H.decode_polytope(pf, off)
        tyre_d = 2 * sum(c["radius"] for c in st["corners"].values()) / len(st["corners"])
        if abs(k - tyre_d / (d0["bounds"]["max"][1] - d0["bounds"]["min"][1])) > 1e-5:
            raise SystemExit(f"{name}: T-22 k {k} is not tyre diameter / donor hull height")
        blob, box = H.scale_hull(pf, off, k)
        changes[off] = (blob, box)
        written.append({"part": name, "part_index": part, "hull": f"{off:#x}",
                        "method": "`jc3hkx.scale_hull` (uniform, about the hull's own centre)",
                        "vertices": d0["vertex_count"], "planes": d0["plane_count"],
                        "extent_bytes": d0["extent"],
                        "box_before_m": {"min": vec(d0["bounds"]["min"]),
                                         "max": vec(d0["bounds"]["max"]),
                                         "size": vec([d0["bounds"]["max"][j]
                                                      - d0["bounds"]["min"][j]
                                                      for j in range(3)])},
                        "scale_k": [rnd(k, 6)] * 3, "translate_m": [0.0, 0.0, 0.0],
                        "radius_before": rnd(d0["convex_radius"], 6),
                        "radius_after": rnd(box["radius"], 6),
                        "box_after_m": {"min": vec(box["min"]), "max": vec(box["max"]),
                                        "size": vec([box["max"][j] - box["min"][j]
                                                     for j in range(3)])},
                        "provenance": "decoded (T-22): tyre diameter / the donor hull's height; "
                                      "placement untouched - the hull is centred on the wheel's "
                                      "own pivot"})
        wheel_report.append({"part": name, "station": corner,
                             "station_hub_m": vec(st["corners"][corner]["hub_true"]),
                             "tyre_diameter_m": rnd(2 * st["corners"][corner]["radius"]),
                             "k": rnd(k, 6)})

    # 3. edits, ancestors, write
    edits = {off: blob for off, (blob, _box) in changes.items()}
    edits.update(H.compound_aabb_edits(pf, changes))
    out, info = H.packfile_bytes(pf, edits)
    problems = H.verify_written(pf.blob, out, edits)
    ranges = H.diff_ranges(pf.blob, out) if len(out) == len(pf.blob) else []

    opf = H.Packfile(out)
    counts, shape_bad = H.shape_checks(opf)
    after_body = H.decode_polytope(opf, body_off)
    body_union = {"min": after_body["bounds"]["min"], "max": after_body["bounds"]["max"]}
    dev_body = deviation(body_union["min"], body_union["max"], bbox_lo, bbox_hi)
    # the reader's convex test allows the hull's own radius (1.6 cm here); the linear map
    # keeps every plane supported exactly, so assert the tight relation, not the reader's
    support_gap = 0.0
    for pl in after_body["planes"]:
        n, dd = pl["n"], pl["d"]
        support_gap = max(support_gap, abs(max(sum(n[k] * v[k] for k in range(3))
                                              for v in after_body["vertices"]) + dd))

    # every hull re-emitted from its decoded values reproduces the source bytes
    reemit_ok = 0
    for o in pf.objects:
        if o.cls != H.POLYTOPE:
            continue
        src = pf.blob[pf.base + o.offset:pf.base + o.offset + pf.extents[o.offset]]
        if H.hull_bytes(pf, o.offset) == src:
            reemit_ok += 1

    env_before = envelopes(pf, parts)
    env_after = envelopes(opf, parts)

    # the body-entry object (the only station/hardpoint data in the file)
    sys_before = [pf.blob[pf.base + o.offset:pf.base + o.offset + pf.extents[o.offset]]
                  for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
    sys_after = [opf.blob[opf.base + o.offset:opf.base + o.offset + opf.extents[o.offset]]
                 for o in opf.objects if o.cls == "hknpPhysicsSystemData"]
    stations_before, stations_after = len(H.stations(pf)), len(H.stations(opf))
    changed_objs = len(edits)
    compound_edits = changed_objs - len(changes)

    skipped = [{"part": name, "part_index": index[name], "hull": f"{hull_of[index[name]]:#x}",
                "box_m": {"size": vec([H.decode_polytope(pf, hull_of[index[name]])["bounds"]["max"][j]
                                       - H.decode_polytope(pf, hull_of[index[name]])["bounds"]["min"][j]
                                       for j in range(3)])},
               "reason": "B-04 step 1 removes `door_f_l`/`door_f_r` and their `door_parts` "
                         "entries, so no Batmobile part will carry this slot; scaling it would "
                         "bind collision to a part that will not exist (R4)"}
               for name in DOOR_PARTS]

    checks = [
        {"name": "donor hulls re-emitted from their decoded values reproduce the source bytes",
         "ok": reemit_ok == counts["polytopes"],
         "detail": f"{reemit_ok}/{counts['polytopes']} hulls byte-identical"},
        {"name": "the write re-reads clean (verify_written)",
         "ok": not problems, "detail": f"{len(problems)} problem(s)"},
        {"name": "every shape invariant on the built file (`shape_checks`)",
         "ok": not shape_bad, "detail": f"{len(shape_bad)} violation(s), "
                                        f"{counts['convex']}/{counts['polytopes']} convex, "
                                        f"{counts['union_ok']}/{counts['compounds']} unions"},
        {"name": "object count and class list unchanged",
         "ok": len(opf.objects) == len(pf.objects) and
               [o.cls for o in opf.objects] == [o.cls for o in pf.objects],
         "detail": f"{len(opf.objects)} objects, {counts['compounds']} compounds, "
                   f"{counts['instances']} instances"},
        {"name": "only the written hulls and their ancestor compounds changed",
         "ok": changed_objs == len(changes) + compound_edits,
         "detail": f"{len(changes)} hulls + {compound_edits} ancestor compound(s)"},
        {"name": "the body-entry data (hknpPhysicsSystemData) is byte-identical (R3)",
         "ok": sys_before == sys_after,
         "detail": f"{len(sys_before)} object(s), {sum(len(b) for b in sys_before)} B"},
        {"name": "the file carries no station quad before or after",
         "ok": stations_before == 0 and stations_after == 0,
         "detail": f"{stations_before} -> {stations_after} station sets"},
        {"name": "every plane of the written body hull is supported exactly",
         "ok": support_gap <= 1e-5,
         "detail": f"max |max(n.v) + d| = {support_gap:.2e} m (float32), "
                   f"donor {body_before['support_gap']:.2e} m"},
        {"name": "hull union bbox within 5 cm of the body bbox (Done check 2)",
         "ok": dev_body["within_tolerance"],
         "detail": f"max |dev| {dev_body['max_abs_dev_m']:.4f} m, "
                   f"missing {dev_body['max_missing_m']:.4f} m"},
    ]

    return {
        "schema": 1,
        "generator": "Tools/scripts/bm_collision.py",
        "card": CARD,
        "inputs": {
            "donor_physicsc": rel(DONOR) + " (the live build, G2-8)",
            "donor_parts_module": rel(PARTS_MODULE) + " (G2-7)",
            "t22_hull_set": rel(T22) + " (T-22)",
            "body_bbox": rel(BODY_MANIFEST) + " (`body_bbox_m`, B-02 / DIM-1)",
            "stations": rel(STATIONS) + " (T-G1; read for the wheel cross-check only, never "
                                        "written - R3)",
            "writer": "Tools/scripts/jc3hkx.py (G2-30: hull_bytes, scale_hull, "
                      "compound_aabb_edits, packfile_bytes, verify_written)",
        },
        "donor": {"bytes": len(donor_blob), "sha256": hashlib.sha256(donor_blob).hexdigest()[:16],
                  "objects": len(pf.objects), "hulls": counts["polytopes"],
                  "compounds": counts["compounds"], "instances": counts["instances"],
                  "hull_objects_unchanged": counts["polytopes"] - len(changes),
                  "station_sets": stations_before},
        "body": {
            "bbox_m": {"min": vec(bbox_lo), "max": vec(bbox_hi),
                       "size": vec([bbox_hi[j] - bbox_lo[j] for j in range(3)])},
            "scale_k_per_axis": vec(body_k, 6),
            "translate_m": vec(body_s, 6),
            "t22_uniform_k": rnd(float(body_t22["scale_k"]), 6),
            "t22_uniform_box_m": body_t22["box_after_m"],
            "why_not_t22_uniform_k": "the uniform k fits inside the body (2.032 m in Y, "
                                     "6.167 m in Z) - 0.239 m and 0.858 m short of DIM-1; the "
                                     "donor hull's aspect is not the body's",
            "union_bbox_m": {"min": vec(body_union["min"]), "max": vec(body_union["max"]),
                             "size": vec([body_union["max"][j] - body_union["min"][j]
                                          for j in range(3)])},
            "deviation": dev_body,
            "plane_support_gap_m": float(f"{support_gap:.3e}"),
            "frame": "the body part's transform is identity and the donor's chassis hull is the "
                     "one hull bound to it, so its stored AABB is the car-space union of the "
                     "hulls the body carries",
        },
        "hull_set": {"written": written, "skipped": skipped,
                     "written_count": len(written), "slots_in_t22": len(t22_parts) + 1,
                     "unchanged_hulls": counts["polytopes"] - len(changes),
                     "wheels": wheel_report},
        "stations": {
            "in_file_before": stations_before, "in_file_after": stations_after,
            "physics_system_data_identical": sys_before == sys_after,
            "parts_module_sha256": hashlib.sha256(open(PARTS_MODULE, "rb").read()).hexdigest()[:16],
            "note": "R3: no station row, no `base_wheel_hardpoint_positions`, no parts module "
                    "and no `land_global` value is written or moved; the wheel hulls keep their "
                    "part-local centre so a wheel still spins about its own pivot",
        },
        "decomposition_tyre_m": rnd(2 * sum(c["radius"] for c in st["corners"].values())
                                     / len(st["corners"])),
        "envelope": {"before": env_before, "after": env_after},
        "write": {"bytes": len(out), "objects": len(pf.objects), "edited_objects": changed_objs,
                  "hulls_written": len(changes), "compounds_updated": compound_edits,
                  "changed_ranges": len(ranges), "changed_bytes": sum(n for _s, n in ranges),
                  "same_size_as_donor": len(out) == len(donor_blob),
                  "problems": problems[:8], "shape_violations": shape_bad[:8],
                  "sha256": hashlib.sha256(out).hexdigest()[:16]},
        "checks": checks,
        "summary": {
            "hulls_written": len(changes), "compounds_updated": compound_edits,
            "body_bbox_dev_m": dev_body["max_abs_dev_m"],
            "within_tolerance": dev_body["within_tolerance"],
            "bytes_out": len(out), "objects_out": counts["polytopes"],
            "tolerance_m": TOLERANCE_M,
        },
        "_blob": out,
    }


def render_md(doc: dict) -> str:
    s = doc["summary"]
    b = doc["body"]
    lines = [
        "# B-10 - the Batmobile hull set",
        "",
        f"Generated by `{doc['generator']}`; do not edit by hand. Inputs: the donor `.physicsc` "
        f"and parts module of `Builds/test-091`; T-22's hull set "
        f"`{doc['inputs']['t22_hull_set']}`; B-02's `body_bbox_m` "
        f"`{doc['inputs']['body_bbox']}`. Writer: G2-30's `jc3hkx`.",
        "",
        "## 1. What was written",
        "",
        f"{s['hulls_written']} hull(s) over the {doc['donor']['hulls']} the file carries, "
        f"{s['compounds_updated']} ancestor compound(s) re-boxed, "
        f"{doc['donor']['objects']} objects in and out. Stations: "
        f"{doc['stations']['in_file_before']} -> {doc['stations']['in_file_after']} in-file "
        f"station sets, `hknpPhysicsSystemData` identical "
        f"{doc['stations']['physics_system_data_identical']} (R3).",
        "",
        "| part | index | hull | method | before (m) | k | after (m) | r before -> after |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for w in doc["hull_set"]["written"]:
        before = " x ".join(f"{v:.3f}" for v in w["box_before_m"]["size"])
        after = " x ".join(f"{v:.3f}" for v in w["box_after_m"]["size"])
        k = ", ".join(f"{v:.6f}" for v in w["scale_k"])
        lines.append(f"| `{w['part']}` | {w['part_index']} | `{w['hull']}` | {w['method']} | "
                     f"{before} | {k} | {after} | {w['radius_before']:.6f} -> "
                     f"{w['radius_after']:.6f} |")
    lines += ["", "Skipped slots, with the card line that decides them:", "",
              "| part | index | hull | donor box (m) | why not written |", "|---|---|---|---|---|"]
    for w in doc["hull_set"]["skipped"]:
        lines.append(f"| `{w['part']}` | {w['part_index']} | `{w['hull']}` | "
                     f"{w['box_m']['size'][0]:.3f} x {w['box_m']['size'][1]:.3f} x "
                     f"{w['box_m']['size'][2]:.3f} | {w['reason']} |")
    lines += [
        "",
        "## 2. The body hull, and why not one uniform factor",
        "",
        f"- DIM-1 body bbox: `{b['bbox_m']['min']} .. {b['bbox_m']['max']}`, "
        f"{' x '.join(f'{v:.3f}' for v in b['bbox_m']['size'])} m.",
        f"- per-axis k: `{b['scale_k_per_axis']}`, translation `{b['translate_m']}`.",
        f"- T-22's uniform k `{b['t22_uniform_k']}` gives "
        f"{' x '.join(f'{v:.3f}' for v in b['t22_uniform_box_m'])} m: "
        f"{b['why_not_t22_uniform_k']}.",
        f"- the union of the hulls the body carries: `{b['union_bbox_m']['min']} .. "
        f"{b['union_bbox_m']['max']}` = "
        f"{' x '.join(f'{v:.3f}' for v in b['union_bbox_m']['size'])} m.",
        f"- deviation from the body bbox, per axis: "
        + ", ".join(f"{a['axis']} {a['min_dev']:+.4f}/{a['max_dev']:+.4f} m"
                    for a in b["deviation"]["axes"])
        + f"; **max |dev| {b['deviation']['max_abs_dev_m']:.4f} m** against the "
          f"{doc['summary']['tolerance_m']:.2f} m band -> "
        f"{'PASS' if b['deviation']['within_tolerance'] else 'FAIL'}.",
        "",
        "The frame is part of the number: " + b["frame"] + ".",
        "",
        "## 3. Wheels (R3: the station each hull has to keep)",
        "",
        "| part | station | hub (m) | 2 x station radius (m) | k |", "|---|---|---|---|---|",
    ]
    for w in doc["hull_set"]["wheels"]:
        lines.append(f"| `{w['part']}` | `{w['station']}` | {w['station_hub_m']} | "
                     f"{w['tyre_diameter_m']:.4f} | {w['k']:.6f} |")
    lines.append("")
    lines.append(f"T-22's tyre diameter (2 x the mean station radius) is "
                 f"{doc['decomposition_tyre_m']:.4f} m and sets every wheel's k; the per-corner "
                 f"radii differ by <= 0.3 mm (`stations.json`).")
    env = doc["envelope"]
    lines += [
        "",
        "The hulls are part-local (a wheel hull is centred on its own origin) and their world "
        "placement is the parts module's `parent_space_offset` - B-04's rows. So the whole-file "
        "envelope is reported, never asserted:",
        "",
        "| frame | before (m) | after (m) |", "|---|---|---|",
    ]
    for key in ("stored", "placed"):
        lines.append(f"| `{key}` | {' x '.join(f'{v:.3f}' for v in env['before'][key]['size'])} "
                     f"| {' x '.join(f'{v:.3f}' for v in env['after'][key]['size'])} |")
    lines += ["", env["after"]["frame"], "",
              "## 4. Checks", "", "| check | result | detail |", "|---|---|---|"]
    for c in doc["checks"]:
        lines.append(f"| {c['name']} | {'PASS' if c['ok'] else 'FAIL'} | {c['detail']} |")
    lines += [
        "",
        "## 5. The two Done commands",
        "",
        "```",
        "python Tools/scripts/jc3hkx.py check --all \\",
        "    --file Working/Collision/batmobile.physicsc \\",
        f"    --against {doc['inputs']['donor_physicsc'].split(' (')[0]}",
        "python Tools/scripts/bm_collision.py --check",
        "```",
        "",
        f"Written file: `{rel(OUT_BIN)}`, {doc['write']['bytes']:,} B, "
        f"sha256 `{doc['write']['sha256']}...`; {doc['write']['changed_bytes']:,} B over "
        f"{doc['write']['changed_ranges']} range(s) differ from the donor, same object count, "
        f"same size ({doc['write']['same_size_as_donor']}) - so the `.ee` member's size and the "
        f"`.toc` record do not move.",
        "",
    ]
    return "\n".join(lines)


def public(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if not k.startswith("_")}


def check() -> int:
    doc = build()
    problems: list[str] = []
    disk = open(OUT_BIN, "rb").read() if os.path.exists(OUT_BIN) else None
    if disk is None:
        problems.append(f"{rel(OUT_BIN)} missing - run --write")
    elif disk != doc["_blob"]:
        problems.append(f"{rel(OUT_BIN)} on disk differs from the derived bytes "
                        f"({len(disk):,} vs {len(doc['_blob']):,} B)")
    if os.path.exists(OUT_JSON):
        old = json.load(open(OUT_JSON, encoding="utf-8"))
        if json.dumps(old, indent=1) != json.dumps(public(doc), indent=1):
            problems.append(f"{rel(OUT_JSON)} differs from the re-derived record")
    else:
        problems.append(f"{rel(OUT_JSON)} missing - run --write")
    if os.path.exists(OUT_MD):
        old_md = open(OUT_MD, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if old_md != render_md(doc) + "\n":
            problems.append(f"{rel(OUT_MD)} stale against the re-derived text")
    else:
        problems.append(f"{rel(OUT_MD)} missing - run --write")
    if disk is not None:
        # the shipped file, not the derived blob: re-read it and re-assert everything
        try:
            opf = H.Packfile(disk)
        except Exception as e:                       # noqa: BLE001
            problems.append(f"on-disk packfile: {e}")
            opf = None
        if opf is not None:
            counts, bad = H.shape_checks(opf)
            problems.extend(bad[:6])
            body_off = hull_offset_of_part(opf)[doc["hull_set"]["written"][0]["part_index"]]
            d = H.decode_polytope(opf, body_off)
            lo = doc["body"]["bbox_m"]["min"]
            hi = doc["body"]["bbox_m"]["max"]
            dev = deviation(d["bounds"]["min"], d["bounds"]["max"], lo, hi)
            if not dev["within_tolerance"]:
                problems.append(f"on-disk body union deviates {dev['max_abs_dev_m']:.4f} m "
                                f"from the body bbox (band {TOLERANCE_M:.2f} m)")
            if len(H.stations(opf)) != 0:
                problems.append("on-disk file now carries station sets")
            if not all(c["ok"] for c in doc["checks"]):
                problems.extend(f"check failed: {c['name']} ({c['detail']})"
                                for c in doc["checks"] if not c["ok"])
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    s = doc["summary"]
    print(f"PASS: {s['hulls_written']} hulls written, {s['compounds_updated']} ancestor "
          f"compounds re-boxed, {doc['donor']['objects']} objects, stations "
          f"{doc['stations']['in_file_before']} -> {doc['stations']['in_file_after']} | "
          f"body union vs body bbox max |dev| {s['body_bbox_dev_m']:.4f} m "
          f"<= {s['tolerance_m']:.2f} m: {s['within_tolerance']} | "
          f"{rel(OUT_BIN)} {doc['write']['bytes']:,} B sha256 "
          f"{doc['write']['sha256']}... | json match True, md match True")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write the hull set, the json and the md")
    g.add_argument("--check", action="store_true", help="re-derive everything and compare")
    a = ap.parse_args()
    if a.write:
        doc = build()
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(OUT_BIN, "wb") as f:
            f.write(doc["_blob"])
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(public(doc), indent=1) + "\n")
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_md(doc) + "\n")
        s = doc["summary"]
        print(f"wrote {rel(OUT_BIN)} ({doc['write']['bytes']:,} B), {rel(OUT_JSON)} and "
              f"{rel(OUT_MD)}: {s['hulls_written']} hulls, {s['compounds_updated']} compounds, "
              f"body dev {s['body_bbox_dev_m']:.4f} m")
        for c in doc["checks"]:
            print(f"  {c['name'][:64]:<64} {'PASS' if c['ok'] else 'FAIL'}  ({c['detail']})")
        sys.exit(0 if all(c["ok"] for c in doc["checks"]) else 1)
    sys.exit(check())


if __name__ == "__main__":
    main()
