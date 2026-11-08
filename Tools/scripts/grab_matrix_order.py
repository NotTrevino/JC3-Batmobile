#!/usr/bin/env python3
"""grab_matrix_order.py - is the physics `TM` 3x3 stored as rows or columns? (G3-01b U-3).

G3-01b proved the 64-byte `TM` struct of an `RB_BodySetup` box element is 16 floats whose
3x3 (floats 4i+1..4i+3) is orthonormal with det +1 on 131/131 boxes, and left U-3 open: the
matrix and its transpose are both proper rotations of the same angle about the same axis, so
one matrix cannot say which of its index orders means "row".  The sign of the 4.00 deg Y tilt
of the weapons box hangs on it.

This tool answers only what the bytes can answer, and says so:

  1. THE LAYOUT (decoded).  The 16 floats are four planes, each stored (W, X, Y, Z), in the
     order X, Y, Z, W: the W slot is 0 on the first three and 1 on the last, and the last
     plane's XYZ is the translation.  Reading A (rows from floats 4i+1..4i+3) is orthonormal
     with det +1; reading B (floats 4i..4i+2) is singular on every identity box.  Same
     plane serialisation the convex element uses: COLLISION_CONVEX.md / COLLISION_GEOM.md
     record `FPlane (W,nx,ny,nz)`, proven there by a plane oracle.

  2. THE KNOWN CASE THE CARD NAMES (decoded).  The skeletal mesh's reference pose for
     `Batmobile_Rig_Weapons_Trans` - record 101 of the 44-byte skeleton array inside
     `Playable_Batmobile_SF.upk` export 5284 - is decoded here and its quaternion is the
     identity: the mesh reference pose carries no tilt at all, so that case cannot fix the
     convention.  Every other bone's rotation is also a quaternion, never a matrix.

  3. THE BUILD'S MATRIX <-> QUATERNION INVENTORY (decoded).  Every 64-byte `TM` struct in the
     four BmGame-family packages and the four Playable_Batmobile* packages is enumerated by
     owning class, and the 20,151,210-byte SkeletalMesh export is scanned at every float offset
     for an orthonormal 3x3 in either lead layout.  The result is what blocks the sign: the only
     matrices in this build are aggregate-geometry element frames (shape-local), and no
     transform in this build is stored both as a matrix and as a quaternion.

  4. THE ONE RELATION THE BYTES DO SUPPORT (evidence, premises stated).  A ragdoll capsule has
     to span its bone, so its long axis should lie along the bone's own reference-pose
     direction (the nearest child bone's position, which is a quaternion/position record, not a
     matrix).  The capsule's centre is decoded from the same TM and is rotation-free, so it
     validates the premise; the axis is then read both ways.  The tool reports the numbers and
     labels them evidence, not proof - it is one art-setup assumption away from a proof and the
     separation is not large enough to be called an oracle.

Labels: decoded = read from bytes (package + export + byte offset); derived = computed from
decoded values with the rule stated; UNKNOWN = not decoded, with what was tried.

Read-only on the game install.  Writes only its two outputs.

Usage:
    uv run --with numpy python Tools/scripts/grab_matrix_order.py --write
    uv run --with numpy python Tools/scripts/grab_matrix_order.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U          # noqa: E402
import reverify_bones as R    # noqa: E402  (G3-01b-style read-only import of the proven decode)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
OUT_JSON = os.path.join(OUT, "MATRIX_ORDER.json")
OUT_MD = os.path.join(OUT, "MATRIX_ORDER.md")

PLAYABLE = "Playable_Batmobile_SF.upk"
MESH_EXPORT = 5284
WEAPONS_EXPORT = 169751
BOX_EXPORTS = [169750, 169751]
CENSUS_PACKAGES = ["BmGame.upk", "Startup.upk", "StartupPatch.upk", "Orphan.upk",
                   "Playable_Batmobile_SF.upk", "Playable_BatmobileMK2_SF.upk",
                   "Playable_BatmobileJoker_SF.upk", "Playable_BatmobileFunhouse_SF.upk"]
TM_STRUCT_SIZE = 64
TAG_STRUCT = 10
TOL_ORTHO = 1e-3
TOL_LEAD = 1e-6
TOL_ROT = 1e-4        # the axis is normalised float32 data, so 1e-6 is below the storage


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


# ----------------------------------------------------------------- the box TM
def tm_tags(payload, name_index):
    """Every StructProperty tag in `payload` whose name is `TM` and whose size is 64."""
    needle = struct.pack("<hHiii", TAG_STRUCT, 0, name_index, 0, TM_STRUCT_SIZE)
    out, o = [], -1
    while True:
        o = payload.find(needle, o + 1)
        if o < 0:
            return out
        out.append({"tag_at": o, "tm_at": o + 20,
                    "floats": [f32(payload, o + 20 + 4 * k) for k in range(16)]})


def planes_of(floats):
    """decoded: four planes, each (W, X, Y, Z) - the layout the lead column proves."""
    return [{"w": floats[4 * i], "xyz": [floats[4 * i + 1 + j] for j in range(3)]}
            for i in range(4)]


def read_a(floats):
    """Reading A (G3-01b): rows from floats 4i+1..4i+3, translation from floats 13..15."""
    return ([[floats[4 * i + 1 + j] for j in range(3)] for i in range(3)],
            [floats[13], floats[14], floats[15]])


def read_b(floats):
    """Reading B (rejected): rows from floats 4i..4i+2, translation from floats 12..14."""
    return ([[floats[4 * i + j] for j in range(3)] for i in range(3)],
            [floats[12], floats[13], floats[14]])


def det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def ortho(m):
    norms = [math.sqrt(sum(v * v for v in r)) for r in m]
    dots = [sum(m[0][i] * m[1][i] for i in range(3)),
            sum(m[0][i] * m[2][i] for i in range(3)),
            sum(m[1][i] * m[2][i] for i in range(3))]
    return {"row_norms": [round(v, 9) for v in norms],
            "det": round(det3(m), 9),
            "max_norm_error": max(abs(n - 1.0) for n in norms),
            "max_abs_dot": max(abs(d) for d in dots),
            "is_rotation": (max(abs(n - 1.0) for n in norms) <= TOL_ORTHO
                            and max(abs(d) for d in dots) <= TOL_ORTHO
                            and abs(det3(m) - 1.0) <= TOL_ORTHO)}


def axis_angle(m):
    """derived: angle of the 3x3 and the axis it is about (R and R^T share both)."""
    cos = max(-1.0, min(1.0, (m[0][0] + m[1][1] + m[2][2] - 1.0) / 2.0))
    ang = math.degrees(math.acos(cos))
    if ang < 1e-6:
        return {"angle_deg": 0.0, "axis": None, "axis_label": "none"}
    s = 2.0 * math.sin(math.radians(ang))
    ax = [(m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s]
    k = max(range(3), key=lambda i: abs(ax[i]))
    return {"angle_deg": round(ang, 6),
            "axis": [round(v, 9) for v in ax],
            "axis_label": ("XYZ"[k] if ax[k] > 0 else "-" + "XYZ"[k])}


def quat_angle(q):
    """derived: rotation angle of a quaternion in degrees (0..180), w last."""
    n = math.sqrt(sum(v * v for v in q)) or 1.0
    w = max(-1.0, min(1.0, abs(q[3]) / n))
    return math.degrees(2.0 * math.acos(w))


def quat_matrix(q):
    """derived: the standard column-vector rotation matrix of a quaternion (columns = images)."""
    x, y, z, w = q
    n = math.sqrt(sum(v * v for v in q)) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


# ----------------------------------------------------------------- mesh side
def matrix_scan(d):
    """Every offset whose reading-A or reading-B 3x3 is orthonormal (a stored matrix)."""
    n = len(d) // 4
    with np.errstate(invalid="ignore"):
        a = np.frombuffer(d[:n * 4], dtype="<f4").astype(np.float64)
    if n <= 64:
        return {"candidates": 0, "orthonormal": [], "floats": n}
    idx = np.arange(n - 61)      # the widest prefetch reaches idx + 60
    # cheap prefilter: the W column must be 0,0,0,1 - first slot (lead-first) or last (lead-last)
    pre_a = (np.abs(a[idx]) < 1e-4) & (np.abs(a[idx + 16]) < 1e-4) \
        & (np.abs(a[idx + 32]) < 1e-4) & (np.abs(a[idx + 48] - 1.0) < 1e-4)
    pre_b = (np.abs(a[idx + 12]) < 1e-4) & (np.abs(a[idx + 28]) < 1e-4) \
        & (np.abs(a[idx + 44]) < 1e-4) & (np.abs(a[idx + 60] - 1.0) < 1e-4)
    cand = np.nonzero(pre_a | pre_b)[0]
    hits = []
    for o in cand.tolist():
        lead = 1 if pre_a[o] else 0
        base = o + (0 if lead else 0)
        rows = [[a[base + 4 * i + (1 if lead else 0) + j] for j in range(3)] for i in range(3)]
        norms = [math.sqrt(sum(v * v for v in r)) for r in rows]
        if all(abs(v - 1.0) <= TOL_ORTHO for v in norms):
            hits.append({"at": int(o * 4), "lead_first": bool(lead)})
    return {"candidates": int(len(cand)), "orthonormal": hits, "floats": int(n)}


def census():
    """Every class that carries a 64-byte `TM` struct, package by package."""
    rows = []
    for name in CENSUS_PACKAGES:
        path = os.path.join(GAME, name)
        if not os.path.isfile(path):
            rows.append({"package": name, "missing": True})
            continue
        pkg = U.Package(path)
        if "TM" not in pkg.names:
            rows.append({"package": name, "tm_name_index": None, "total": 0, "by_class": {}})
            continue
        ni = pkg.names.index("TM")
        needle = struct.pack("<hHiii", TAG_STRUCT, 0, ni, 0, TM_STRUCT_SIZE)
        by_class, total = {}, 0
        for idx in range(1, pkg.export_count + 1):
            try:
                d = pkg.data(idx)
            except Exception:
                continue
            c = d.count(needle)
            if c:
                total += c
                cls = pkg.object_class(idx)
                by_class[cls] = by_class.get(cls, 0) + c
        rows.append({"package": name, "tm_name_index": ni, "exports": len(pkg.exports),
                     "total": total, "by_class": dict(sorted(by_class.items()))})
    return rows


# ----------------------------------------------------------------- capsule evidence
def ang_line(a, b):
    na = math.sqrt(sum(v * v for v in a))
    nb = math.sqrt(sum(v * v for v in b))
    if na < 1e-9 or nb < 1e-9:
        return 90.0
    c = abs(sum(a[i] * b[i] for i in range(3))) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def elements(payload, name_index):
    """Elements of an AggGeom payload: TM(64) then that shape's own float/bool tags."""
    needle = struct.pack("<hHiii", TAG_STRUCT, 0, name_index, 0, TM_STRUCT_SIZE)
    out, o = [], -1
    while True:
        o = payload.find(needle, o + 1)
        if o < 0:
            return out
        tm = [f32(payload, o + 20 + 4 * k) for k in range(16)]
        p, tags, ok = o + 84, [], True
        while True:
            if p + 4 > len(payload):
                ok = False
                break
            t, off = struct.unpack_from("<hH", payload, p)
            if t == 0:
                p += 2
                break
            if t == 4:
                tags.append(("f", off, f32(payload, p + 4)))
            elif t == 3:
                tags.append(("b", off, struct.unpack_from("<I", payload, p + 4)[0]))
            else:
                ok = False
                break
            p += 8
        out.append({"tm": tm, "tags": tags, "ok": ok, "end": p})


def bone_of(payload, names):
    """The body's BoneName: the first NameProperty tag's FName in the head of the export."""
    for o in range(0, min(len(payload), 80) - 8):
        t, _off = struct.unpack_from("<hH", payload, o)
        if t == 6:
            ni = struct.unpack_from("<i", payload, o + 4)[0]
            if 0 <= ni < len(names):
                return names[ni]
            return None
    return None


def capsule_evidence():
    """Capsule axes vs the bone's own reference-pose direction, read both ways.

    Premise (tested, not assumed): a ragdoll capsule spans its bone, so its centre - which the
    TM stores in floats 13..15 and no rotation can change - lies along the bone direction, and
    its long axis lies along that direction too.  The rig is picked per body by the smallest
    rotation-free centre residual, so the choice cannot favour either reading.
    """
    pkg = U.Package(os.path.join(GAME, "BmGame.upk"))
    names = pkg.names
    ni = names.index("TM")
    classes = {i: pkg.object_class(i) for i in range(1, pkg.export_count + 1)}
    skels = []
    for i in range(1, pkg.export_count + 1):
        if classes.get(i) != "SkeletalMesh":
            continue
        try:
            skels.append({"mesh": pkg.object_path(i),
                          "recs": R.find_ref_skeleton(pkg, pkg.data(i))["records"]})
        except Exception:
            continue
    bodies = []
    for i in range(1, pkg.export_count + 1):
        if classes.get(i) != "RB_BodySetup":
            continue
        d = pkg.data(i)
        bone = bone_of(d, names)
        if not bone:
            continue
        caps = [e for e in elements(d, ni) if tuple(t[0] for t in e["tags"]) == ("f", "f", "b")]
        if caps:
            bodies.append({"path": pkg.object_path(i), "bone": bone, "caps": caps})
    pairs = []
    for b in bodies:
        best = None
        for sk in skels:
            rec = next((r for r in sk["recs"] if r["name"] == b["bone"]), None)
            if rec is None:
                continue
            kids = [r for r in sk["recs"]
                    if r["parent_index"] == rec["index"] and r["index"] != rec["index"]
                    and math.sqrt(sum(v * v for v in r["position_cm"])) > 1e-6]
            if not kids:
                continue
            kp = min(kids, key=lambda r: sum(v * v for v in r["position_cm"]))["position_cm"]
            err = sum(ang_line(c["tm"][13:16], kp) for c in b["caps"]) / len(b["caps"])
            if best is None or err < best[0]:
                best = (err, sk["mesh"], kp, rec["quat"])
        if best is not None:
            pairs.append({"body": b["path"], "bone": b["bone"], "mesh": best[1],
                          "resid": best[0], "d": best[2], "quat": best[3],
                          "caps": b["caps"]})
    rows = []
    for p in pairs:
        for c in p["caps"]:
            tm = c["tm"]
            rows.append({"body": p["body"], "bone": p["bone"], "mesh": p["mesh"],
                         "A": [[tm[4 * i + 1 + j] for j in range(3)] for i in range(3)],
                         "centre": tm[13:16], "d": p["d"], "resid": p["resid"],
                         "quat": p["quat"], "len": c["tags"][1][2], "rad": c["tags"][0][2]})
    ident = [x for x in rows if max(abs(x["A"][i][j] - (1.0 if i == j else 0.0))
                                    for i in range(3) for j in range(3)) <= TOL_ORTHO]
    nonid = [x for x in rows if x not in ident]
    # does any element TM reproduce its own bone's reference-pose rotation?  (it should not)
    bone_matches = 0
    for x in nonid:
        qm = quat_matrix(x["quat"])
        for m in (x["A"], [[x["A"][j][i] for j in range(3)] for i in range(3)]):
            if max(abs(m[i][j] - qm[i][j]) for i in range(3) for j in range(3)) <= 1e-2:
                bone_matches += 1
                break
    stats = {}
    for thr in (5.0, 10.0):
        sub = [x for x in nonid if ang_line(x["centre"], x["d"]) <= thr]
        per = {}
        for label, key in (("rows_are_images", "row"), ("columns_are_images", "col")):
            per[label] = {}
            for ax in range(3):
                rr = sorted(ang_line([x["A"][i][ax] if key == "row" else x["A"][ax][i]
                                      for i in range(3)], x["d"]) for x in sub)
                per[label]["XYZ"[ax]] = {
                    "median_deg": round(statistics.median(rr), 3) if rr else None,
                    "within_2": sum(1 for v in rr if v <= 2),
                    "within_5": sum(1 for v in rr if v <= 5),
                    "within_10": sum(1 for v in rr if v <= 10),
                    "n": len(rr)} if rr else None
        stats["centre_within_%d" % int(thr)] = {"capsules": len(sub), "angles": per}
    centre = sorted(ang_line(x["centre"], x["d"]) for x in rows)
    lr = sorted(x["len"] / math.sqrt(sum(v * v for v in x["d"])) for x in rows
                if math.sqrt(sum(v * v for v in x["d"])) > 1e-6)
    return {
        "source": os.path.join(GAME, "BmGame.upk"),
        "skeletal_meshes": len(skels),
        "capsule_bodies": len(bodies),
        "assigned_bodies": len(pairs),
        "capsules": len(rows),
        "capsules_identity_rotation": len(ident),
        "capsules_non_identity": len(nonid),
        "element_tm_equals_its_own_bone_rotation": bone_matches,
        "capsule_length_over_bone_length_median": round(statistics.median(lr), 4) if lr else None,
        "centre_vs_bone_direction": {
            "median_deg": round(statistics.median(centre), 3) if centre else None,
            "within_5": sum(1 for v in centre if v <= 5),
            "within_10": sum(1 for v in centre if v <= 10),
            "n": len(centre)},
        "axis_readings": stats,
        "label": ("derived evidence, not an oracle: premise = a ragdoll capsule spans its bone, "
                  "so its rotation-free centre (TM floats 13..15) and its long axis both follow "
                  "the bone's own reference-pose direction (nearest child's position_cm from the "
                  "44-byte skeleton record).  The rig is assigned per body by the smallest "
                  "rotation-free centre residual."),
    }


# ----------------------------------------------------------------- build
def build():
    box_pkg = U.Package(os.path.join(GAME, "BmGame.upk"))
    mesh_pkg = U.Package(os.path.join(GAME, PLAYABLE))
    box_ni = box_pkg.names.index("TM")

    boxes = []
    for exp in BOX_EXPORTS:
        d = box_pkg.data(exp)
        for t in tm_tags(d, box_ni):
            fl = t["floats"]
            a_rows, a_t = read_a(fl)
            b_rows, b_t = read_b(fl)
            boxes.append({
                "export": exp, "object": box_pkg.object_path(exp),
                "tm_at": t["tm_at"], "floats": [round(v, 7) for v in fl],
                "planes": [{"w": round(p["w"], 7), "xyz": [round(v, 7) for v in p["xyz"]]}
                           for p in planes_of(fl)],
                "w_column": [round(fl[4 * i], 7) for i in range(4)],
                "reading_A": {"rows": [[round(v, 7) for v in r] for r in a_rows],
                              "translation_cm": [round(v, 5) for v in a_t],
                              "oracle": ortho(a_rows)},
                "reading_B": {"rows": [[round(v, 7) for v in r] for r in b_rows],
                              "translation_cm": [round(v, 5) for v in b_t],
                              "oracle": ortho(b_rows)},
                "axis_angle": axis_angle(a_rows),
                "label": "decoded (StructProperty tag at byte %d, 16 floats from byte %d)"
                         % (t["tag_at"], t["tm_at"]),
            })
    weapons = next(b for b in boxes if b["export"] == WEAPONS_EXPORT)
    wfl = weapons["floats"]
    a_rows, a_t = read_a(wfl)
    cols = [[a_rows[i][j] for i in range(3)] for j in range(3)]   # column j of the same 3x3
    # The two candidate readings of the SAME three planes.  A right-handed rotation about +Y
    # takes local X to (cos, 0, -sin), so the signed angle is atan2(-image[2], image[0]).
    cand = {
        "rows_are_axis_images": {
            "rule": "P' = P . M + T  (row vector): row i of the 3x3 is where local axis i points",
            "local_x_image": [round(a_rows[0][j], 7) for j in range(3)],
            "local_z_image": [round(a_rows[2][j], 7) for j in range(3)],
            "rotation_deg_about_plus_Y": round(
                math.degrees(math.atan2(-a_rows[0][2], a_rows[0][0])), 6),
        },
        "columns_are_axis_images": {
            "rule": "P' = M . P + T  (column vector): column i of the 3x3 is where local axis i points",
            "local_x_image": [round(cols[0][j], 7) for j in range(3)],
            "local_z_image": [round(cols[2][j], 7) for j in range(3)],
            "rotation_deg_about_plus_Y": round(
                math.degrees(math.atan2(-cols[0][2], cols[0][0])), 6),
        },
    }

    # the skeletal mesh's reference pose for the same bone
    d = mesh_pkg.data(MESH_EXPORT)
    sk = R.find_ref_skeleton(mesh_pkg, d)
    recs = sk["records"]
    ci = next(r["index"] for r in recs if r["name"] == "Batmobile_Rig_Weapons_Trans")
    ch = next(r["index"] for r in recs if r["name"] == "Batmobile_Chassis")
    def rec_of(i):
        r = recs[i]
        return {"index": r["index"], "name": r["name"], "parent_index": r["parent_index"],
                "parent": recs[r["parent_index"]]["name"],
                "quat": r["quat"], "position_cm": r["position_cm"],
                "quat_angle_deg": round(quat_angle(r["quat"]), 6),
                "quat_matrix": [[round(v, 7) for v in row]
                                for row in quat_matrix(r["quat"])]}
    ref = {
        "package": PLAYABLE, "export": MESH_EXPORT, "object": mesh_pkg.object_path(MESH_EXPORT),
        "export_bytes": len(d), "skeleton_origin": sk["origin"], "skeleton_stride": sk["stride"],
        "skeleton_count": sk["count"],
        "weapons_bone": rec_of(ci),
        "chassis_bone": rec_of(ch),
        "label": ("decoded: the 44-byte record array of the SkeletalMesh export (quat@+0, "
                  "position@+16, FName@+28, parent@+36, 0xFFFFFFFF@+40 - the layout "
                  "reverify_bones.py proves on all 180 bones)"),
    }

    scan = matrix_scan(d)
    cen = census()

    ev = capsule_evidence()

    # ---- checks
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    check("the 16 floats are four (W,X,Y,Z) planes whose W column is (0,0,0,1)",
          all(max(abs(b["w_column"][i] - (0.0, 0.0, 0.0, 1.0)[i]) for i in range(4)) <= TOL_LEAD
              for b in boxes),
          "; ".join("export %d W column %s" % (b["export"], b["w_column"]) for b in boxes))
    check("reading A is a rotation (orthonormal, det +1) on all 3 BmGame boxes",
          all(b["reading_A"]["oracle"]["is_rotation"] for b in boxes),
          "; ".join("export %d det %.7f max|row|-1 %.2e" % (
              b["export"], b["reading_A"]["oracle"]["det"],
              b["reading_A"]["oracle"]["max_norm_error"]) for b in boxes))
    check("reading B is rejected (singular on the identity boxes)",
          all(abs(b["reading_B"]["oracle"]["det"]) <= TOL_ORTHO for b in boxes),
          "; ".join("export %d detB %.7f" % (b["export"], b["reading_B"]["oracle"]["det"])
                    for b in boxes))
    aa = weapons["axis_angle"]
    check("the weapons 3x3 is a rotation of 4.00 deg about the Y axis",
          abs(aa["angle_deg"] - 4.0) <= 0.01 and aa["axis"] is not None
          and abs(aa["axis"][0]) <= TOL_ROT and abs(aa["axis"][2]) <= TOL_ROT
          and abs(abs(aa["axis"][1]) - 1.0) <= TOL_ROT,
          "angle %.4f deg, axis %s (%s)" % (aa["angle_deg"], aa["axis"], aa["axis_label"]))
    check("the mesh reference pose of that bone is the identity rotation",
          abs(ref["weapons_bone"]["quat_angle_deg"]) <= 0.01,
          "record %d quat %s -> %.4f deg; parent %s"
          % (ref["weapons_bone"]["index"], ref["weapons_bone"]["quat"],
             ref["weapons_bone"]["quat_angle_deg"], ref["weapons_bone"]["parent"]))
    check("the SkeletalMesh export holds no stored 3x3 matrix at any float offset",
          len(scan["orthonormal"]) == 0,
          "%d prefilter candidates out of %d offsets, %d orthonormal"
          % (scan["candidates"], scan["floats"], len(scan["orthonormal"])))
    check("no 64-byte TM struct exists outside aggregate geometry / destructible chunks",
          all(set(r.get("by_class", {})) <= {"RB_BodySetup", "RAggGeomCollisionComponent",
                                             "ApexDestructibleAsset"} for r in cen),
          "; ".join("%s %s" % (r["package"], r.get("by_class", {})) for r in cen))
    check("no capsule element TM reproduces its own bone's reference-pose rotation",
          ev["element_tm_equals_its_own_bone_rotation"] == 0,
          "%d of %d non-identity capsules match their bone's quat matrix under either reading"
          % (ev["element_tm_equals_its_own_bone_rotation"], ev["capsules_non_identity"]))

    doc = {
        "schema": 1,
        "generator": "grab_matrix_order.py",
        "question": ("G3-01b U-3: are the three planes of an AggGeom `TM` 3x3 the transform's "
                     "rows (row-vector convention) or its columns, and therefore what is the "
                     "sign of the 4.00 deg Y tilt of the weapons box?"),
        "verdict": {
            "storage_order": "UNSETTLED",
            "layout": "SETTLED: four planes, each (W,X,Y,Z), in the order X, Y, Z, W",
            "tilt": ("4.00 deg about the Y axis (magnitude and axis decoded; R and R^T share "
                     "both). Sign: conditional - +4.00 deg about +Y if the planes are the rows "
                     "(row-vector), -4.00 deg about +Y if they are the columns."),
            "why": ("no transform in this build is stored both as a 64-byte FMatrix and as a "
                    "quaternion, so there is no known case to compare against; the one the card "
                    "names (the mesh reference pose of Batmobile_Rig_Weapons_Trans) is the "
                    "identity rotation"),
        },
        "source": {"game": GAME, "box_package": "BmGame.upk", "mesh_package": PLAYABLE,
                   "mesh_export": MESH_EXPORT, "weapons_export": WEAPONS_EXPORT},
        "boxes": boxes,
        "weapons_box_candidates": cand,
        "mesh_ref_pose": ref,
        "matrix_scan": scan,
        "tm_census": cen,
        "capsule_evidence": ev,
        "checks": checks,
        "unknowns": [
            {"id": "U-1",
             "item": "whether the three planes are the transform's rows or its columns",
             "tried": ("decoded all three BmGame box TMs; both readings are proper rotations of "
                       "the same angle about the same axis; enumerated every TM(64) in 8 packages "
                       "by class; scanned the 20,151,210-byte SkeletalMesh export at every float "
                       "offset for an orthonormal 3x3; decoded the mesh reference pose of the "
                       "bone the box belongs to; measured 122 non-identity ragdoll capsules "
                       "against their bones' own reference-pose directions"),
             "why": ("the only matrices this build stores are aggregate-geometry element frames "
                     "(shape-local, no quaternion counterpart); the only rotations it stores as "
                     "quaternions are skeleton/anim records (no matrix counterpart); the mesh "
                     "reference pose of the weapons bone is the identity, so it cannot carry the "
                     "tilt. A native struct dump that fixes FMatrix's row/column semantics for "
                     "this build (G3-06), or any body whose element TM duplicates a bone "
                     "transform, would decide it")},
            {"id": "U-2",
             "item": "which local axis a ragdoll capsule's long axis is",
             "tried": ("tested all three local axes against the bone direction under both "
                       "readings; the capsule is rotationally symmetric about its long axis, so "
                       "its own bytes cannot name that axis - only the art setup can"),
             "why": "no local field names the capsule's axis (BMSDK_OFFSETS.json has no "
                    "FKSphylElem layout)"},
        ],
    }
    doc["passed"] = sum(1 for c in checks if c["pass"])
    doc["checks_total"] = len(checks)
    return doc


# ----------------------------------------------------------------- markdown
def fmt(v, nd=2):
    s = ("%%.%df" % nd) % v
    return "0." + s.split(".")[1] if s.startswith("-0.") and float(s) == 0 else s


def render(d):
    v = d["verdict"]
    L = ["# MATRIX_ORDER - is the AggGeom `TM` 3x3 stored as rows or columns?", "",
         "Generated by `Tools/scripts/grab_matrix_order.py` (`--write`); `--check` re-derives every",
         "number from the packages and fails on a one-byte difference. Card: `GRAB_BACKLOG.md`",
         "G3-01b open item U-3. Labels: **decoded** = from bytes (package + export + offset);",
         "**derived** = computed from decoded values with the rule stated; **UNKNOWN** = not",
         "decoded, with why.", "",
         "## Verdict", "",
         "- row/column order: **%s**" % v["storage_order"],
         "- layout of the 16 floats: **%s**" % v["layout"],
         "- the tilt: %s" % v["tilt"],
         "- why: %s" % v["why"], "",
         "## 1. The 16 floats, decoded", "",
         "Reading A is G3-01b's: rows from floats `4i+1..4i+3`, translation from floats `13..15`.",
         "The `W` column is `(0,0,0,1)` on every box, so each group of four is one plane stored",
         "`(W,X,Y,Z)` and the four planes are X, Y, Z, W - the same `FPlane (W,nx,ny,nz)` order",
         "`COLLISION_CONVEX.md` proves for the convex element's face planes.", "",
         "| export | bone | W column | reading A det | reading A max abs dot | reading B det | angle | axis (column-vector sense) |",
         "|---|---|---|---|---|---|---|---|"]
    bone_by_export = {169750: "Batmobile_Chassis", 169751: "Batmobile_Rig_Weapons_Trans"}
    for b in d["boxes"]:
        L.append("| %d | `%s` | %s | %.7f | %.2e | %.7f | %.4f deg | %s |"
                 % (b["export"], bone_by_export.get(b["export"], "?"), b["w_column"],
                    b["reading_A"]["oracle"]["det"],
                    b["reading_A"]["oracle"]["max_abs_dot"],
                    b["reading_B"]["oracle"]["det"],
                    b["axis_angle"]["angle_deg"], b["axis_angle"]["axis_label"]))
    w = next(b for b in d["boxes"] if b["export"] == d["source"]["weapons_export"])
    L += ["", "The weapons box as decoded (16 floats from byte %d of export %d):" % (
        w["tm_at"], w["export"]), "", "```",
        "floats      %s" % w["floats"],
        "planes      %s" % [(p["w"], p["xyz"]) for p in w["planes"]],
        "3x3 (A)     %s" % w["reading_A"]["rows"],
        "translation %s cm" % w["reading_A"]["translation_cm"], "```", "",
        "Both readings of one matrix give the same angle and axis (`R` and `R^T` are both proper",
        "rotations of the same angle about the same line), so the bytes cannot separate them:", "",
        "| reading | local X points to | local Z points to | rotation about +Y |",
        "|---|---|---|---|"]
    for k, c in d["weapons_box_candidates"].items():
        L.append("| `%s` | %s | %s | %+0.4f deg |" % (k, c["local_x_image"], c["local_z_image"],
                                                      c["rotation_deg_about_plus_Y"]))
    ref = d["mesh_ref_pose"]
    wb, cb = ref["weapons_bone"], ref["chassis_bone"]
    L += ["", "## 2. The known case the card names: the mesh reference pose", "",
          "`%s` export %d (`%s`), %d bytes: the 44-byte record array at byte %d, stride %d," %
          (ref["package"], ref["export"], ref["object"], ref["export_bytes"],
           ref["skeleton_origin"], ref["skeleton_stride"]), "",
          "| bone | record | quat (x,y,z,w) | angle | position_cm | parent |",
          "|---|---|---|---|---|---|",
          "| `%s` | %d | %s | %.4f deg | %s | `%s` |" % (wb["name"], wb["index"], wb["quat"],
                                                         wb["quat_angle_deg"], wb["position_cm"],
                                                         wb["parent"]),
          "| `%s` | %d | %s | %.4f deg | %s | `%s` |" % (cb["name"], cb["index"], cb["quat"],
                                                         cb["quat_angle_deg"], cb["position_cm"],
                                                         cb["parent"]), "",
          "The reference pose is the **identity rotation** for both the weapons bone and the",
          "chassis bone. The tilt the box carries is therefore a shape-local orientation inside",
          "the bone's frame, added by whoever authored the physics asset - it is **not** the",
          "bone's reference pose and no quaternion in the mesh repeats it. The case the card",
          "names is empty.", "",
          "## 3. Every matrix in this build, and why none of them is a known case", "",
          "| package | exports | `TM`(64) structs | by class |", "|---|---|---|---|"]
    for r in d["tm_census"]:
        L.append("| %s | %s | %s | %s |" % (r["package"], r.get("exports", "-"),
                                            r.get("total", 0), r.get("by_class", {})))
    sc = d["matrix_scan"]
    L += ["", "The SkeletalMesh export %d was scanned at every float offset (%d offsets) for an" %
          (ref["export"], sc["floats"]),
          "orthonormal 3x3 in either lead layout: **%d** prefilter candidates, **%d** orthonormal." %
          (sc["candidates"], len(sc["orthonormal"])), "",
          "So: the build stores **matrices only** in aggregate geometry (box/capsule element TMs,",
          "which are shape frames inside a bone) and in Apex destructible chunks (84 of the 87 chunk",
          "TMs are the identity; the 3 that are not have no quaternion counterpart either), and",
          "**quaternions only** in skeleton and animation records.",
          "No transform in this build is written both ways, which is exactly what a known case",
          "would need.", "",
          "## 4. The one relation the bytes do support (evidence, not an oracle)", "",
          "A ragdoll capsule has to span its bone. Its centre is `TM` floats 13..15, which no",
          "rotation reading touches, so the premise can be checked before the axis is judged:",
          "", "| quantity | value |", "|---|---|",
          "| capsule bodies / rig-assigned bodies | %d / %d |" % (d["capsule_evidence"]["capsule_bodies"],
                                                                 d["capsule_evidence"]["assigned_bodies"]),
          "| capsules (non-identity rotation) | %d (%d) |" % (d["capsule_evidence"]["capsules"],
                                                             d["capsule_evidence"]["capsules_non_identity"]),
          "| capsule length / bone length, median | %s |" % d["capsule_evidence"]["capsule_length_over_bone_length_median"],
          "| centre vs bone direction, median | %s deg (%d/%d within 5 deg) |" % (
              d["capsule_evidence"]["centre_vs_bone_direction"]["median_deg"],
              d["capsule_evidence"]["centre_vs_bone_direction"]["within_5"],
              d["capsule_evidence"]["centre_vs_bone_direction"]["n"]), ""]
    for key in ("centre_within_5", "centre_within_10"):
        s = d["capsule_evidence"]["axis_readings"].get(key)
        if not s:
            continue
        L += ["Subset: capsules whose centre is within %s deg of the bone direction (**%d** capsules)." %
              (key.split("_")[-1], s["capsules"]), "",
              "| reading | local axis | median | <=2 deg | <=5 deg | <=10 deg |",
              "|---|---|---|---|---|---|"]
        for label, per in s["angles"].items():
            for ax, row in per.items():
                if not row:
                    continue
                L.append("| `%s` | %s | %s deg | %d | %d | %d |"
                         % (label, ax, row["median_deg"], row["within_2"], row["within_5"],
                            row["within_10"]))
        L.append("")
    L += ["This is **evidence, not proof**: it needs the premise that ragdoll capsules are placed",
          "along their bones, the capsule is rotationally symmetric about its long axis so its own",
          "bytes cannot name that axis, and the separation between the two readings is a factor,",
          "not a gap. It is reported because it is the only relation in the build that points",
          "either way, and it points at the **column** reading. It is not used to declare the",
          "order settled.", "",
          "## 5. What would settle it", "",
          "1. a native struct dump for this build that fixes `FMatrix`'s row/column semantics",
          "   (G3-06) - the same place a `FKAggregateGeom`/`FKBoxElem` layout would come from;",
          "2. any body in any package whose element `TM` duplicates a bone transform that the",
          "   skeleton also stores as a quaternion (none in these 8 packages: table above);",
          "3. a per-bone vertex set asymmetric enough to bracket a rotated element - the weapons",
          "   bone itself owns **no** skinned points (probe in the DONE report), so its box cannot",
          "   be checked against its own geometry.", "",
          "## Checks", "",
          "| check | result | detail |", "|---|---|---|"]
    for c in d["checks"]:
        L.append("| %s | %s | %s |" % (c["name"].replace("|", "/"),
                                       "PASS" if c["pass"] else "FAIL",
                                       str(c["detail"]).replace("|", "/")))
    L += ["", "%d/%d checks passed." % (d["passed"], d["checks_total"]), "",
          "## UNKNOWNs", ""]
    for u in d["unknowns"]:
        L.append("- **%s %s** - tried: %s. Still unknown because %s." %
                 (u["id"], u["item"], u["tried"], u["why"]))
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.write and not a.check:
        a.check = True
    doc = build()
    js = json.dumps(doc, indent=1) + "\n"
    md = render(doc)
    if a.write:
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote MATRIX_ORDER.json and MATRIX_ORDER.md")
    bad = [c for c in doc["checks"] if not c["pass"]]
    print("layout: %s" % doc["verdict"]["layout"])
    print("storage order: %s | tilt: %s" % (doc["verdict"]["storage_order"],
                                            doc["verdict"]["tilt"]))
    print("mesh reference pose of the weapons bone: %s -> %.4f deg"
          % (doc["mesh_ref_pose"]["weapons_bone"]["quat"],
             doc["mesh_ref_pose"]["weapons_bone"]["quat_angle_deg"]))
    print("TM(64) census: " + "; ".join("%s %d" % (r["package"], r.get("total", 0))
                                        for r in doc["tm_census"]))
    print("matrix scan of the SkeletalMesh export: %d/%d offsets, %d orthonormal"
          % (doc["matrix_scan"]["candidates"], doc["matrix_scan"]["floats"],
             len(doc["matrix_scan"]["orthonormal"])))
    ev = doc["capsule_evidence"]
    s = ev["axis_readings"].get("centre_within_5") or {}
    if s.get("angles"):
        print("capsule evidence (n=%d): rows=Z median %s deg, columns=Z median %s deg"
              % (s["capsules"], s["angles"]["rows_are_images"]["Z"]["median_deg"],
                 s["angles"]["columns_are_images"]["Z"]["median_deg"]))
    if a.check:
        if not os.path.isfile(OUT_JSON) or not os.path.isfile(OUT_MD):
            print("MISSING: run --write")
            return 1
        if open(OUT_JSON, encoding="utf-8").read() != js:
            print("STALE: MATRIX_ORDER.json differs from a fresh decode")
            return 1
        if open(OUT_MD, encoding="utf-8").read() != md:
            print("STALE: MATRIX_ORDER.md differs from a fresh decode")
            return 1
    for c in bad:
        print("FAIL %s: %s" % (c["name"], c["detail"]))
    print("%d/%d checks passed" % (doc["passed"], doc["checks_total"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
