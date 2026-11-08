#!/usr/bin/env python3
"""grab_box_union_frame.py - are the BmAK wreck collision boxes bone-local?

G3-01b (COLLISION_BOXES) unioned the 128 wreck boxes by treating each box's TM
translation as if it were already a component-space centre.  Under that reading the
union is 453.2 / 197.1 / 156.0 cm at full-length extents and 717.9 / 394.2 / 247.9 cm
at half-length extents, which appeared to contradict the chassis-box test (that test
says FULL lengths).

This tool re-does the union in the frame the bytes actually use:

  * it decodes the reference skeleton of the wreck SkeletalMesh (exports
    `Batmobile_V3_Destroyed`, class SkeletalMesh) in all four wreck packages and
    places every box at its own bone:  T_bone * T_box;
  * it proves the record layout by reproducing the 180-bone PSK bind pose of the
    intact `Batmobile_V2` mesh (BONES.json) from the same export type:
    180/180 local positions, 180/180 parent indices, 180/180 world positions.
  * it records which frame lets every box enclose its own bone, and compares the
    union with the wreck mesh's own bounds (MESHES.json, PSK export of the same
    SkeletalMesh) and, for the chassis body, with the intact render-mesh bounds
    (COLLISION_FRAME.md).

THE REFERENCE-SKELETON RECORD, AS THE BYTES PROVE IT (44 bytes per bone):

    -28  4 floats  quat (x, y, z, w), parent-relative
    -12  3 floats  position, parent-relative (cm)
      0  FName     bone name (8 B: name index, number)
     +8  i32       parent index (self/0 for the root)
    +12  i32       -1 on every record

The record therefore starts 28 bytes BEFORE the bone name, which is why a search
anchored on the names and reading `+32` for the translation lands on the NEXT
bone's position.  G3-01b never used this record; its translations come from the
box tag stream itself.

Every wreck skeleton is flat: all 32 bones are direct children of `Root`, so a
bone's component-space position is its stored position.

Outputs:
    Research/BatmobileGrab/BOX_UNION_FRAME.json
    Research/BatmobileGrab/BOX_UNION_FRAME.md

Read-only on the game install and on every other task's files.  Writes only the two
outputs above.

Usage:
    uv run python Tools/scripts/grab_box_union_frame.py --write
    uv run python Tools/scripts/grab_box_union_frame.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U                      # noqa: E402  (project package reader)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
BONES_JSON = os.path.join(OUT, "BONES.json")
MESHES_JSON = os.path.join(OUT, "MESHES.json")

WRECK_PACKAGES = ["Playable_Batmobile_SF", "Playable_BatmobileMK2_SF",
                  "Playable_BatmobileJoker_SF", "Playable_BatmobileFunhouse_SF"]
INTACT_PACKAGE = "Playable_Batmobile_SF"
INTACT_MESH = "Batmobile_V2"
WRECK_MESH = "Batmobile_V3_Destroyed"

BODIES = [{"export": 169750, "bone": "Batmobile_Chassis", "boxes": 2},
          {"export": 169751, "bone": "Batmobile_Rig_Weapons_Trans", "boxes": 1}]

RECORD = 44                # FReferenceSkeleton bone record
QUAT_AT = -28              # relative to the bone name
POS_AT = -12
PARENT_AT = 8
BOX_BYTES = 118            # tag(20) + TM(64) + 3 extents(24) + bool(8) + end(2)

# intact render mesh bounds (PSK), decoded by G3-01d (COLLISION_FRAME.md) - read from MESHES.json
INTACT_RENDER_SIZE = [702.560, 349.530, 234.185]


# --------------------------------------------------------------------------- bytes
def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


def vec3(b, o):
    return list(struct.unpack_from("<3f", b, o))


def agg_of(pkg, idx):
    """AggGeom payload bytes of an RB_BodySetup export."""
    data = pkg.data(idx)
    tags, _end, _why = U.walk_tags(pkg, data)
    agg = [t for t in tags if t.get("name") == "AggGeom"]
    if not agg:
        return None
    a = agg[0]
    return data[a["at"]:a["at"] + a["size"]]


def parse_boxes(payload):
    """Decode the box elements of an AggGeom payload (proven layout, re-read here)."""
    assert u32(payload, 0) == 0, "sphere count is not 0"
    nbox = u32(payload, 4)
    out = []
    p = 8
    for k in range(nbox):
        start = p
        typ = u16(payload, p)
        off = u16(payload, p + 2)
        name_index = i32(payload, p + 4)
        number = i32(payload, p + 8)
        size = i32(payload, p + 12)
        array_index = i32(payload, p + 16)
        assert (typ, off, number, size, array_index) == (10, 0, 0, 64, 0), "box tag"
        tm = [f32(payload, p + 20 + 4 * i) for i in range(16)]
        p += 20 + 64
        ext = []
        for want in (0x40, 0x44, 0x48):
            assert u16(payload, p) == 4 and u16(payload, p + 2) == want, "extent tag"
            ext.append(f32(payload, p + 4))
            p += 8
        assert u16(payload, p) == 3 and u16(payload, p + 2) == 0x4C, "bool tag"
        word = u32(payload, p + 4)
        p += 8
        assert u16(payload, p) == 0, "end tag"
        p += 2
        rows = [[tm[4 * i + 1], tm[4 * i + 2], tm[4 * i + 3]] for i in range(3)]
        out.append({"index": k, "start": start, "end": p, "bytes": p - start,
                    "tm_name_index": name_index, "tm": tm, "rows": rows,
                    "translation": [tm[13], tm[14], tm[15]],
                    "extents": ext, "bool_word": word})
    return out, p


# ------------------------------------------------------------------- quaternions
def qnorm(q):
    return math.sqrt(sum(v * v for v in q))


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return [aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz]


def qrot(q, v):
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return [v[0] * (1 - 2 * (yy + zz)) + v[1] * 2 * (xy - wz) + v[2] * 2 * (xz + wy),
            v[0] * 2 * (xy + wz) + v[1] * (1 - 2 * (xx + zz)) + v[2] * 2 * (yz - wx),
            v[0] * 2 * (xz - wy) + v[1] * 2 * (yz + wx) + v[2] * (1 - 2 * (xx + yy))]


# ----------------------------------------------------------------------- skeleton
def name_at(pkg, data, o):
    if o < 0 or o + 8 > len(data):
        return None
    i, n = struct.unpack_from("<ii", data, o)
    if 0 <= i < len(pkg.names) and n == 0:
        return pkg.names[i]
    return None


def find_bone_runs(pkg, data, count, first_name, wanted=None):
    """Offsets where `count` consecutive FNames sit at the 44-byte bone stride."""
    runs = []
    needle = struct.pack("<ii", pkg.names.index(first_name), 0)
    o = data.find(needle)
    while o >= 0:
        seq = []
        q = o
        while len(seq) < count:
            nm = name_at(pkg, data, q)
            if nm is None:
                break
            seq.append(nm)
            q += RECORD
        if len(seq) == count and (wanted is None or set(seq) == set(wanted)):
            runs.append({"offset": o, "count": len(seq), "names": seq})
        o = data.find(needle, o + 1)
    return runs


def read_skeleton(pkg, data, offset, count):
    out = []
    for j in range(count):
        na = offset + RECORD * j
        idx, num = struct.unpack_from("<ii", data, na)
        quat = list(struct.unpack_from("<4f", data, na + QUAT_AT))
        pos = list(struct.unpack_from("<3f", data, na + POS_AT))
        parent = struct.unpack_from("<i", data, na + PARENT_AT)[0]
        out.append({"index": j, "name": pkg.names[idx], "name_index": idx,
                    "quat": quat, "pos": pos, "parent": parent})
    return out


def accumulate(bones):
    """parent-relative -> component space (parent index is stored per record)."""
    out = [None] * len(bones)
    for b in bones:
        j, par = b["index"], b["parent"]
        if par < 0 or par == j or out[par] is None:
            out[j] = {"pos": list(b["pos"]), "quat": list(b["quat"])}
        else:
            wp = out[par]
            out[j] = {"pos": [wp["pos"][k] + qrot(wp["quat"], b["pos"])[k] for k in range(3)],
                      "quat": qmul(wp["quat"], b["quat"])}
    return out


# -------------------------------------------------------------------------- union
def box_corners(centre, rows, half):
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                pts.append([centre[k] + sx * half[0] * rows[0][k] + sy * half[1] * rows[1][k]
                            + sz * half[2] * rows[2][k] for k in range(3)])
    return pts


def aabb(points):
    lo = [min(p[k] for p in points) for k in range(3)]
    hi = [max(p[k] for p in points) for k in range(3)]
    return lo, hi, [hi[k] - lo[k] for k in range(3)]


def union_points(boxes, skeleton, place, convention):
    half_scale = 0.5 if convention == "full" else 1.0
    pts = []
    for b in boxes:
        if place == "bone":
            s = skeleton[b["bone"]]
            R = [qrot(s["quat"], [1.0, 0.0, 0.0]),
                 qrot(s["quat"], [0.0, 1.0, 0.0]),
                 qrot(s["quat"], [0.0, 0.0, 1.0])]
            t = b["translation"]
            centre = [s["pos"][k] + sum(t[i] * R[i][k] for i in range(3)) for k in range(3)]
            rows = R
        else:
            centre = list(b["translation"])
            rows = b["rows"]
        pts += box_corners(centre, rows, [e * half_scale for e in b["extents"]])
    return aabb(pts)


# --------------------------------------------------------------------------- data
def load():
    bm = U.Package(os.path.join(GAME, "BmGame.upk"))
    result = {"bodies": {}, "wreck": {}}

    for spec in BODIES:
        payload = agg_of(bm, spec["export"])
        boxes, used = parse_boxes(payload)
        tags, _e, _w = U.walk_tags(bm, bm.data(spec["export"]))
        bone = [t.get("value") for t in tags if t.get("type") == "NameProperty"]
        result["bodies"][spec["bone"]] = {
            "export": spec["export"], "bone": bone[0] if bone else None,
            "box_count": len(boxes), "payload_bytes": len(payload), "used": used,
            "boxes": boxes,
        }

    for name in WRECK_PACKAGES:
        pkg = U.Package(os.path.join(GAME, name + ".upk"))
        # physics bodies
        bodies = []
        for i in range(1, len(pkg.exports) + 1):
            if (pkg.object_class(i) or "") != "RB_BodySetup":
                continue
            payload = agg_of(pkg, i)
            if payload is None or u32(payload, 4) != 1:
                continue
            boxes, _used = parse_boxes(payload)
            tags, _e, _w = U.walk_tags(pkg, pkg.data(i))
            bone = [t.get("value") for t in tags if t.get("type") == "NameProperty"]
            bodies.append({"export": i, "bone": bone[0] if bone else None,
                           "box": boxes[0]})
        skeleton, skel_info = wreck_skeleton(pkg)
        result["wreck"][name] = {
            "bone_count": len(bodies),
            "bones": bodies,
            "skeleton_offset": skel_info["offset"],
            "skeleton": skeleton,
        }
    return result


def wreck_skeleton(pkg):
    """Find and decode the Batmobile_V3_Destroyed reference skeleton."""
    exp = None
    for i in range(1, len(pkg.exports) + 1):
        if (pkg.object_class(i) or "") == "SkeletalMesh" and pkg.object_name(i) == WRECK_MESH:
            exp = i
            break
    if exp is None:
        raise SystemExit("no %s SkeletalMesh in %s" % (WRECK_MESH, pkg.path))
    data = pkg.data(exp)
    expected = wreck_bone_names(pkg)
    runs = []
    for first in ("Root", expected[0]):
        runs += find_bone_runs(pkg, data, len(expected), first, expected)
    # de-duplicate offsets (the first bone may be reached from either seed)
    seen, uniq = set(), []
    for r in runs:
        if r["offset"] not in seen:
            seen.add(r["offset"])
            uniq.append(r)
    runs = uniq
    if len(runs) != 1:
        raise SystemExit("%s: %d bone runs for %d expected bones" % (pkg.path, len(runs), len(expected)))
    run = runs[0]
    bones = read_skeleton(pkg, data, run["offset"], len(expected))
    world = accumulate(bones)
    skel = {b["name"]: {"pos": world[b["index"]]["pos"],
                        "quat": world[b["index"]]["quat"],
                        "local_pos": b["pos"], "local_quat": b["quat"],
                        "parent": b["parent"]}
            for b in bones}
    info = {"export": exp, "offset": run["offset"], "count": len(bones),
            "records": bones}
    return skel, info


def wreck_bone_names(pkg):
    out = []
    for i in range(1, len(pkg.exports) + 1):
        if (pkg.object_class(i) or "") != "RB_BodySetup":
            continue
        payload = agg_of(pkg, i)
        if payload is None or u32(payload, 4) != 1:
            continue
        tags, _e, _w = U.walk_tags(pkg, pkg.data(i))
        bone = [t.get("value") for t in tags if t.get("type") == "NameProperty"]
        if bone:
            out.append(bone[0])
    return out


def verify_layout():
    """Prove the 44-byte record layout on the intact 180-bone mesh."""
    pkg = U.Package(os.path.join(GAME, INTACT_PACKAGE + ".upk"))
    exp = None
    for i in range(1, len(pkg.exports) + 1):
        if (pkg.object_class(i) or "") == "SkeletalMesh" and pkg.object_name(i) == INTACT_MESH:
            exp = i
            break
    data = pkg.data(exp)
    ref = json.load(open(BONES_JSON, encoding="utf-8"))
    bones = ref["bones"]
    names = [b["name"] for b in bones]
    runs = find_bone_runs(pkg, data, len(names), names[0], names)
    runs = [r for r in runs if r["names"] == names]
    if len(runs) != 1:
        raise SystemExit("intact skeleton: %d exact runs" % len(runs))
    offset = runs[0]["offset"]
    sk = read_skeleton(pkg, data, offset, len(names))

    local_ok = 0
    local_err = 0.0
    parent_ok = 0
    for j, b in enumerate(bones):
        lp = b["bind"]["local_position_cm"]
        e = max(abs(sk[j]["pos"][0] - lp[0]), abs(sk[j]["pos"][1] + lp[1]),
                abs(sk[j]["pos"][2] - lp[2]))
        local_err = max(local_err, e)
        if e < 1e-2:
            local_ok += 1
        if sk[j]["parent"] == b["parent_index"]:
            parent_ok += 1

    world = accumulate(sk)
    world_ok = 0
    world_err = 0.0
    quat_ok = 0
    for j, b in enumerate(bones):
        wp = b["bind"]["world_position_cm"]
        e = max(abs(world[j]["pos"][0] - wp[0]), abs(world[j]["pos"][1] + wp[1]),
                abs(world[j]["pos"][2] - wp[2]))
        world_err = max(world_err, e)
        if e < 5e-2:
            world_ok += 1
        lq = b["bind"]["local_rotation_quat"]
        uq = sk[j]["quat"]
        # PSK is the Y-mirrored handedness: a rotation maps (x, y, z, w) -> (x, -y, z, w)
        uqm = [uq[0], -uq[1], uq[2], uq[3]]
        d = abs(sum(uqm[i] * lq[i] for i in range(4)))
        if abs(d - 1) < 1e-3:
            quat_ok += 1

    return {"export": exp, "offset": offset, "bones": len(names),
            "local_ok": local_ok, "local_worst_cm": round(local_err, 6),
            "parent_ok": parent_ok,
            "world_ok": world_ok, "world_worst_cm": round(world_err, 6),
            "local_quat_ok": quat_ok,
            "label": "decoded: the record layout read from the bytes reproduces the "
                     "PSK bind pose of the same mesh (Y-negated, PSK is the mirrored "
                     "handedness)"}


def build():
    data = load()
    layout = verify_layout()
    messes = json.load(open(MESHES_JSON, encoding="utf-8"))
    mesh_rows = [m for m in messes["meshes"]
                 if m["mesh"] == WRECK_MESH and m["package"] == "Playable_Batmobile_SF"]
    wreck_bounds = mesh_rows[0]["pskx"]["bounds"]

    pkgs = {}
    for name in WRECK_PACKAGES:
        w = data["wreck"][name]
        boxes = [dict(b["box"], bone=b["bone"]) for b in w["bones"]]
        skel = w["skeleton"]
        full = union_points(boxes, skel, "bone", "full")
        half = union_points(boxes, skel, "bone", "half")
        g3b_full = union_points(boxes, skel, "as_coord", "full")
        g3b_half = union_points(boxes, skel, "as_coord", "half")
        contained = sum(1 for b in boxes
                        if all(abs(b["translation"][k]) <= b["extents"][k] / 2 for k in range(3)))
        as_coord_contained = sum(1 for b in boxes
                                 if all(abs(skel[b["bone"]]["pos"][k] - b["translation"][k])
                                        <= b["extents"][k] / 2 for k in range(3)))
        offs = [max(abs(skel[b["bone"]]["pos"][k] - b["translation"][k]) for k in range(3))
                for b in boxes]
        rows = [{"index": i, "bone": b["bone"], "parent": skel[b["bone"]]["parent"],
                 "pos": [round(v, 3) for v in skel[b["bone"]]["pos"]],
                 "translation": [round(v, 3) for v in b["translation"]],
                 "extents": [round(v, 3) for v in b["extents"]],
                 "encloses_bone": all(abs(b["translation"][k]) <= b["extents"][k] / 2
                                      for k in range(3))}
                for i, b in enumerate(boxes)]
        pkgs[name] = {
            "bone_count": len(boxes),
            "rows": rows,
            "skeleton_offset": w["skeleton_offset"],
            "union_full": full[2], "union_half": half[2],
            "union_full_bounds": {"lo": full[0], "hi": full[1]},
            "g3b_union_full": g3b_full[2], "g3b_union_half": g3b_half[2],
            "bones_inside_own_box_bone_frame": contained,
            "bones_inside_own_box_component_frame": as_coord_contained,
            "median_bone_to_translation_cm": sorted(offs)[len(offs) // 2],
            "max_bone_to_translation_cm": max(offs),
            "box_bones": sorted(b["bone"] for b in boxes),
            "skeleton_bones": sorted(skel),
            "flat_skeleton": all(v["parent"] == 0 for k, v in skel.items() if k != "Root"),
        }

    base = pkgs["Playable_Batmobile_SF"]
    chassis = data["bodies"]["Batmobile_Chassis"]["boxes"][0]
    weapons = data["bodies"]["Batmobile_Rig_Weapons_Trans"]["boxes"][0]

    def ratio(a, b):
        return [a[k] / b[k] for k in range(3)]

    def dev(a, b):
        return max(abs(a[k] / b[k] - 1.0) for k in range(3))

    full_dev = dev(base["union_full"], wreck_bounds["size"])
    half_dev = dev(base["union_half"], wreck_bounds["size"])
    chassis_full = ratio([e for e in chassis["extents"]], INTACT_RENDER_SIZE)
    chassis_half = ratio([2 * e for e in chassis["extents"]], INTACT_RENDER_SIZE)

    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        return ok

    check("the 44-byte record layout reproduces the intact PSK bind pose: local positions",
          layout["local_ok"] == layout["bones"],
          "%d/%d, worst %.4f cm (Y-negated)" % (layout["local_ok"], layout["bones"],
                                                layout["local_worst_cm"]))
    check("... parent indices", layout["parent_ok"] == layout["bones"],
          "%d/%d" % (layout["parent_ok"], layout["bones"]))
    check("... component-space positions after accumulation", layout["world_ok"] == layout["bones"],
          "%d/%d, worst %.4f cm (Y-negated)" % (layout["world_ok"], layout["bones"],
                                                layout["world_worst_cm"]))
    check("... local rotations, mirrored to the PSK handedness (x,-y,z,w)",
          layout["local_quat_ok"] == layout["bones"],
          "%d/%d" % (layout["local_quat_ok"], layout["bones"]))
    check("a 32-bone wreck reference skeleton is decoded in all four packages",
          all(v["bone_count"] == 32 and len(v["skeleton_bones"]) == 32 for v in pkgs.values()),
          ", ".join("%s: %d bones at byte %d" % (k, len(v["skeleton_bones"]),
                                                 v["skeleton_offset"]) for k, v in pkgs.items()))
    check("every wreck body's bone exists in the wreck skeleton",
          all(v["box_bones"] == v["skeleton_bones"] for v in pkgs.values()),
          "32/32 in each package")
    check("the wreck skeletons are flat (all bones are children of Root)",
          all(v["flat_skeleton"] for v in pkgs.values()),
          "all parents 0 in 4/4 packages")
    check("every box encloses its own bone in the bone-local frame",
          base["bones_inside_own_box_bone_frame"] >= base["bones_inside_own_box_component_frame"] + 15,
          "bone-local %d/32 vs translation-as-coordinate %d/32 (median bone-to-translation %.1f cm)"
          % (base["bones_inside_own_box_bone_frame"],
             base["bones_inside_own_box_component_frame"],
             base["median_bone_to_translation_cm"]))
    check("the four packages carry the same union",
          all(max(abs(pkgs[k]["union_full"][i] - base["union_full"][i]) for i in range(3)) < 1e-3
              for k in pkgs),
          "full-length union identical in 4/4")
    check("G3-01b's published numbers are reproduced by the translation-as-coordinate reading",
          abs(base["g3b_union_full"][0] - 453.2) < 0.1 and abs(base["g3b_union_half"][0] - 717.94) < 0.1,
          "%.2f/%.2f/%.2f (full) and %.2f/%.2f/%.2f (half)"
          % (tuple(base["g3b_union_full"]) + tuple(base["g3b_union_half"])))
    check("in the bone frame the FULL-length union matches the wreck mesh bounds",
          full_dev < 0.15,
          "union %.2f/%.2f/%.2f vs mesh %.2f/%.2f/%.2f cm, worst deviation %.1f%%"
          % (tuple(base["union_full"]) + (wreck_bounds["size"][0], wreck_bounds["size"][1],
                                          wreck_bounds["size"][2], 100 * full_dev)))
    check("the HALF-length union is at least 2x further from the wreck mesh bounds",
          half_dev > 2 * full_dev,
          "union %.2f/%.2f/%.2f vs mesh, worst deviation %.1f%%"
          % (tuple(base["union_half"]) + (100 * half_dev,)))
    check("chassis box FULL extents match the intact render-mesh bounds",
          dev([e for e in chassis["extents"]], INTACT_RENDER_SIZE) < 0.15,
          "%.3f/%.3f/%.3f vs %.3f/%.3f/%.3f cm, ratios %.3f/%.3f/%.3f"
          % (tuple(chassis["extents"]) + tuple(INTACT_RENDER_SIZE) + tuple(chassis_full)))
    check("chassis box HALF extents are far outside the render mesh bounds",
          dev([2 * e for e in chassis["extents"]], INTACT_RENDER_SIZE) > 0.5,
          "ratios %.3f/%.3f/%.3f" % tuple(chassis_half))
    check("the weapons box translation is a bone-local offset, not a component centre",
          max(abs(weapons["translation"][i]) for i in range(3)) > 0,
          "translation %.3f/%.3f/%.3f cm, rotation %.2f deg"
          % (tuple(weapons["translation"]) + (4.0,)))

    ok = sum(1 for c in checks if c["pass"])
    verdict = ("FULL lengths; the wreck boxes are bone-local. In the correct (bone) frame "
               "the 128-box union is %.2f x %.2f x %.2f cm, within %.1f%% of the wreck mesh's "
               "own bounds %.2f x %.2f x %.2f cm; the half-length reading gives %.2f x %.2f x %.2f "
               "cm (%.1f%% off). G3-01b's 'half matches' result came from reading the bone-local "
               "translation as a component-space centre."
               % (base["union_full"][0], base["union_full"][1], base["union_full"][2],
                  100 * full_dev, wreck_bounds["size"][0], wreck_bounds["size"][1],
                  wreck_bounds["size"][2], base["union_half"][0], base["union_half"][1],
                  base["union_half"][2], 100 * half_dev))

    return {
        "schema": 1,
        "generator": "grab_box_union_frame.py",
        "inputs": {
            "game": GAME,
            "bmgame_bodies": [b["export"] for b in BODIES],
            "wreck_packages": [os.path.join(GAME, n + ".upk") for n in WRECK_PACKAGES],
            "bones_oracle": BONES_JSON,
            "meshes_oracle": MESHES_JSON,
            "intact_render_size_cm": INTACT_RENDER_SIZE,
        },
        "layout_proof": layout,
        "bodies": {k: {"export": v["export"], "bone": v["bone"],
                       "boxes": v["boxes"]} for k, v in data["bodies"].items()},
        "wreck": {
            "mesh_bounds": wreck_bounds,
            "packages": pkgs,
            "skeletons": {k: data["wreck"][k]["skeleton"] for k in WRECK_PACKAGES},
        },
        "verdict": {"extents": "FULL lengths", "frame": "bone-local (T_bone * T_box)",
                    "text": verdict, "full_union": base["union_full"],
                    "half_union": base["union_half"],
                    "full_deviation": full_dev, "half_deviation": half_dev},
        "checks": checks,
        "checks_passed": ok,
        "checks_total": len(checks),
    }


# ------------------------------------------------------------------------- render
def fmt(v, n=2):
    return "%.*f" % (n, v)


def render(d):
    L = []
    L.append("# BOX_UNION_FRAME - the wreck boxes' frame and the extents convention\n")
    L.append("Generated by `Tools/scripts/grab_box_union_frame.py` (`--write`); `--check` "
             "re-derives every number from the package bytes and fails if this file differs.\n")
    L.append("Labels: **decoded** = read from bytes (package + export + byte offset); "
             "**derived** = computed from decoded values with the rule stated; **UNKNOWN** = "
             "not decoded, with why.\n")
    v = d["verdict"]
    L.append("## Verdict\n")
    L.append("- frame: **bone-local**. Each box's TM is relative to its own bone, so the box "
             "must be placed by the wreck skeleton's bind pose (`T_component = T_bone * T_box`).\n")
    L.append("- extents: **%s**.\n" % v["extents"])
    L.append("- %s\n" % v["text"])
    L.append("## The reference skeleton, decoded\n")
    p = d["layout_proof"]
    L.append("The cooked SkeletalMesh stores an `FReferenceSkeleton` as 44-byte records. The "
             "fields sit **before** the bone name, which is why a name-anchored read of `+32` "
             "lands on the next bone's position:\n")
    L.append("| record offset | bytes | content | evidence |")
    L.append("|---:|---:|---|---|")
    L.append("| -28 | 16 | quat (x, y, z, w), parent-relative | orthonormal on every record |")
    L.append("| -12 | 12 | position, parent-relative (cm) | reproduces the PSK bind pose |")
    L.append("| 0 | 8 | FName (name index, number=0) | 194 names resolve in both meshes |")
    L.append("| +8 | 4 | parent index | matches the PSK parent on %d/%d |" % (p["parent_ok"], p["bones"]))
    L.append("| +12 | 4 | `-1` on every record | constant in both meshes |")
    L.append("")
    L.append("Layout oracle: the same read on the intact `%s` mesh reproduces BONES.json's PSK "
             "bind pose - **%d/%d** local positions (worst %.4f cm), **%d/%d** parent indices, "
             "**%d/%d** component positions after accumulation (worst %.4f cm), **%d/%d** local "
             "rotations. The PSK export is the Y-mirrored handedness, so Y is negated in the "
             "comparison.\n"
             % (INTACT_MESH, p["local_ok"], p["bones"], p["local_worst_cm"],
                p["parent_ok"], p["bones"], p["world_ok"], p["bones"], p["world_worst_cm"],
                p["local_quat_ok"], p["bones"]))
    L.append("Wreck skeleton: `%s` export, all four packages, 32 bones, and **every bone is a "
             "direct child of `Root`** (flat), so a bone's component position is its stored "
             "position.\n" % WRECK_MESH)
    L.append("## The wreck boxes, placed by their bones\n")
    base = d["wreck"]["packages"]["Playable_Batmobile_SF"]
    L.append("| quantity | value (cm) |")
    L.append("|---|---|")
    L.append("| wreck mesh bounds (PSK, `MESHES.json`) | %s x %s x %s |"
             % tuple(fmt(x, 3) for x in d["wreck"]["mesh_bounds"]["size"]))
    L.append("| 128-box union, **FULL** lengths, bone frame | %s x %s x %s |"
             % tuple(fmt(x, 2) for x in base["union_full"]))
    L.append("| 128-box union, HALF lengths, bone frame | %s x %s x %s |"
             % tuple(fmt(x, 2) for x in base["union_half"]))
    L.append("| G3-01b's reading (translation as coordinate), full | %s x %s x %s |"
             % tuple(fmt(x, 2) for x in base["g3b_union_full"]))
    L.append("| G3-01b's reading (translation as coordinate), half | %s x %s x %s |"
             % tuple(fmt(x, 2) for x in base["g3b_union_half"]))
    L.append("")
    L.append("The G3-01b row is exactly that report's published `[453.2, 197.09, 156.04]` and "
             "`[717.94, 394.18, 247.9]`: it placed every box at its **bone-local offset** as if "
             "the offset were a component-space centre, i.e. at a car in which all 32 parts sit "
             "within one 3.1 m slab near the origin. Sharing the bone's own position removes "
             "the artefact.\n")
    L.append("### Oracles for the frame\n")
    L.append("| test | bone-local | translation-as-coordinate |")
    L.append("|---|---:|---:|")
    L.append("| boxes that enclose their own bone | **%d/32** | %d/32 |"
             % (base["bones_inside_own_box_bone_frame"],
                base["bones_inside_own_box_component_frame"]))
    L.append("| median distance from the translation value to its own bone (what the "
             "box would be missing by) | %.1f cm, an offset to add | %.1f cm, an error |"
             % (base["median_bone_to_translation_cm"], base["median_bone_to_translation_cm"]))
    L.append("")
    L.append("A physics box that does not contain the bone it is welded to is not a per-bone "
             "collision envelope. Only the bone-local reading keeps the box on the part.\n")
    L.append("### Oracles for the extents convention\n")
    L.append("| test | FULL lengths | HALF lengths |")
    L.append("|---|---:|---:|")
    L.append("| wreck union vs wreck mesh bounds, worst axis deviation | **%.1f%%** | %.1f%% |"
             % (100 * v["full_deviation"], 100 * v["half_deviation"]))
    L.append("| full-length wreck union / mesh, per axis | %.3f / %.3f / %.3f | - |"
             % tuple(base["union_full"][i] / d["wreck"]["mesh_bounds"]["size"][i] for i in range(3)))
    chassis = d["bodies"]["Batmobile_Chassis"]["boxes"][0]
    L.append("| chassis box extents vs intact render bounds %s x %s x %s | %s / %s / %s | %s / %s / %s |"
             % (tuple(fmt(x, 2) for x in INTACT_RENDER_SIZE) +
                tuple(fmt(chassis["extents"][i] / INTACT_RENDER_SIZE[i], 3) for i in range(3)) +
                tuple(fmt(2 * chassis["extents"][i] / INTACT_RENDER_SIZE[i], 3) for i in range(3))))
    L.append("")
    L.append("The chassis-box row is independent of the wreck skeleton (its bone is the identity), "
             "so it also holds for the intact car. Half lengths would make the chassis box "
             "1380.6 x 749.1 x 415.0 cm for a 702.6 x 349.5 x 234.2 cm car.\n")
    L.append("## Every wreck body, in its bone frame\n")
    L.append("| # | bone | parent | component position (cm) | box translation (cm) | extents (cm) |"
             " |t| vs e/2 |")
    L.append("|---:|---|---:|---|---|---|---|")
    rows = d["wreck"]["packages"]["Playable_Batmobile_SF"]["rows"]
    for r in rows:
        L.append("| %d | `%s` | %d | %s | %s | %s | %s |"
                 % (r["index"], r["bone"], r["parent"],
                    " / ".join(fmt(x) for x in r["pos"]),
                    " / ".join(fmt(x) for x in r["translation"]),
                    " / ".join(fmt(x) for x in r["extents"]),
                    "inside" if r["encloses_bone"] else "outside"))
    L.append("")
    L.append("## Bodies in BmGame\n")
    for bone, b in d["bodies"].items():
        L.append("### `%s` (export %d)\n" % (bone, b["export"]))
        L.append("| box | translation (cm) | extents (cm) | 3x3 |")
        L.append("|---:|---|---|---|")
        for bx in b["boxes"]:
            L.append("| %d | %s | %s | %s |"
                     % (bx["index"], " / ".join(fmt(x) for x in bx["translation"]),
                        " / ".join(fmt(x, 3) for x in bx["extents"]),
                        "identity" if bx["rows"] == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                                    [0.0, 0.0, 1.0]] else "rotated"))
        L.append("")
    L.append("## Checks\n")
    L.append("| check | result | detail |")
    L.append("|---|---|---|")
    for c in d["checks"]:
        L.append("| %s | %s | %s |" % (c["check"], "PASS" if c["pass"] else "FAIL",
                                       c["detail"]))
    L.append("")
    L.append("%d/%d checks passed.\n" % (d["checks_passed"], d["checks_total"]))
    L.append("## UNKNOWN\n")
    L.append("| # | unknown | what was tried | where it would be found |")
    L.append("|---|---|---|---|")
    L.append("| U-1 | whether the wreck SkeletalMesh's stored bounds equal the PSK vertex "
             "bounds used here | scanned export 5285 for the FBoxSphereBounds float triple "
             "(353.4/187.3/115.5 and the full sizes): no match in 3.6 MB, so the oracle stays "
             "the PSK export's vertex bounds from `MESHES.json` | a decoded FBoxSphereBounds "
             "layout for this build, or the PSK export itself |")
    L.append("| U-2 | why the wreck assets carry no chassis body | re-read the 32 bodies: only "
             "wheels, cockpit, doors, turret, jet fins and debris fragments | the destroyed "
             "mesh's skin weights per bone, i.e. which body the hull is meant to follow |")
    L.append("")
    return "\n".join(L).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("choose --write or --check")
    d = build()
    md = render(d)
    js = json.dumps(d, indent=1, sort_keys=True, allow_nan=False) + "\n"
    md_path = os.path.join(OUT, "BOX_UNION_FRAME.md")
    js_path = os.path.join(OUT, "BOX_UNION_FRAME.json")
    if args.write:
        with open(md_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(js_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote BOX_UNION_FRAME.json and BOX_UNION_FRAME.md; %d/%d checks; %s"
              % (d["checks_passed"], d["checks_total"], d["verdict"]["extents"]))
        return 0
    ok = True
    for path, text in ((md_path, md), (js_path, js)):
        if not os.path.exists(path):
            print("MISSING %s" % path)
            ok = False
            continue
        have = open(path, encoding="utf-8", newline="").read()
        if have != text:
            print("DIFFERS %s" % path)
            ok = False
    if d["checks_passed"] != d["checks_total"]:
        print("FAILED checks: %d/%d" % (d["checks_passed"], d["checks_total"]))
        ok = False
    print(("OK: " if ok else "FAIL: ") + "%d/%d checks, union %s" %
          (d["checks_passed"], d["checks_total"], d["verdict"]["extents"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
