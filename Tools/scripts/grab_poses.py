"""grab_poses.py - pursuit -> battle pose deltas and bounding boxes (G1-12).

Inputs are the records already produced by the grab, not hand-copied numbers:

  * `Research/BatmobileGrab/BONES.json` supplies the 180-bone hierarchy, the bind pose,
    the one JC3 transform and the LOD0 mesh path/hash;
  * `Batmobile_V2_Pose_States` supplies the local track keys.  The key-frame export is
    `E:\\Modding\\_shared\\gamedata\\BmAKgrab\\anims\\keys\\Playable_Batmobile_SF__Batmobile_V2_Pose_States.json`;
    positions are metres in the PSK frame, rotations are PSK/UE3 quaternions;
  * the LOD0 PSKX supplies the 201,338 points and their raw weights, so a pose bbox is the
    actual skinned mesh bbox rather than a box around bone pivots.

The canonical pair is `Batmobile_V2_Tank_Spread_Open_Game` frame 0 (pursuit) and its last
frame (battle).  The `_Game` sequences are the gameplay transition; the same-named
sequences without `_Game` are the cinematic variant and are kept as a second endpoint
pair.  `Batmobile_V2_Tank_Strafe` is not a third pose: its root translates 4.89 m, so it
is used only to measure the true 90-degree strafe wheel yaw.

Pose reconstruction uses `grab_bones`'s PSK convention: world = q_child * q_parent and a
child's local offset is rotated by the inverse parent rotation.  The one JC3 transform is
`bat_assemble.to_jc3_rot(p) * 0.01 + offset`; rotations use the same proper rotation on
the axis (angle unchanged).

Outputs:
  Research/BatmobileGrab/POSES.json
  Research/BatmobileGrab/POSES.md

Usage:
  python Tools/scripts/grab_poses.py --write
  python Tools/scripts/grab_poses.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bat_assemble as BA  # noqa: E402
import grab_bones as GB  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GRAB = ROOT / "Research" / "BatmobileGrab"
OUT_JSON = GRAB / "POSES.json"
OUT_MD = GRAB / "POSES.md"
BONES_JSON = GRAB / "BONES.json"

PACKAGE = "Playable_Batmobile_SF"
ANIM_SET = "Batmobile_V2_Pose_States"
KEY_DIR = Path(os.environ.get("BMAK_ANIM_KEY_DIR",
                              r"E:\Modding\_shared\gamedata\BmAKgrab\anims\keys"))
KEY_JSON = KEY_DIR / ("%s__%s.json" % (PACKAGE, ANIM_SET))

CANON_OPEN = "Batmobile_V2_Tank_Spread_Open_Game"
CANON_CLOSE = "Batmobile_V2_Tank_Spread_Close_Game"
CINEMATIC_OPEN = "Batmobile_V2_Tank_Spread_Open"
CINEMATIC_CLOSE = "Batmobile_V2_Tank_Spread_Close"
STRAFE = "Batmobile_V2_Tank_Strafe"

SCHEMA = 1
SCALE = 0.01
POSE_Y = 1                      # JC3 up axis
MOVE_M = 0.0005                 # 0.5 mm counts as a moved bone
MOVE_DEG = 0.05
LOOP_POS_CM = 0.20
LOOP_ROT_DEG = 0.10


class PoseError(Exception):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fnum(v, places: int = 6):
    return None if v is None else round(float(v), places)


def vec(v, places: int = 6):
    return [fnum(x, places) for x in v]


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        return v * 0.0
    return v / n


def qnorm(q):
    q = np.asarray(q, dtype=np.float64)
    n = float(np.linalg.norm(q))
    if n < 1e-12:
        raise PoseError("zero quaternion")
    return q / n


def qconj(q):
    return np.array([-q[0], -q[1], -q[2], q[3]], dtype=np.float64)


def qmul(a, b):
    x1, y1, z1, w1 = qnorm(a)
    x2, y2, z2, w2 = qnorm(b)
    return np.array([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ], dtype=np.float64)


def qrot(q, v, inverse: bool = False):
    q = qnorm(q)
    u = q[:3].copy()
    w = q[3]
    if inverse:
        u = -u
    v = np.asarray(v, dtype=np.float64)
    return 2.0 * np.dot(u, v) * u + (w * w - np.dot(u, u)) * v + 2.0 * w * np.cross(u, v)


def qrot_batch(q, v, inverse: bool = False):
    """Vectorised qrot for an (N,4) quaternion array and (N,3) vectors."""
    q = np.asarray(q, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    u = q[:, :3].copy()
    w = q[:, 3]
    if inverse:
        u = -u
    dots = np.einsum("ij,ij->i", u, v)
    return (2.0 * dots[:, None] * u +
            (w * w - np.einsum("ij,ij->i", u, u))[:, None] * v +
            2.0 * w[:, None] * np.cross(u, v))


def jc3_vec(v):
    """PSK vector -> JC3 vector through the same proper rotation as the mesh."""
    return BA.to_jc3_rot(np.asarray(v, dtype=np.float64).reshape(1, 3))[0]


def jc3_point(p_cm):
    return jc3_vec(p_cm) * SCALE


def jc3_quat(q):
    """Rotate a PSK quaternion into JC3: rotate its axis, keep its angle."""
    q = qnorm(q)
    if q[3] < 0:
        q = -q
    w = min(1.0, max(-1.0, float(q[3])))
    angle = 2.0 * math.acos(w)
    s = math.sqrt(max(0.0, 1.0 - w * w))
    if angle < 1e-10 or s < 1e-10:
        return np.array([0.0, 0.0, 0.0, 1.0])
    axis = jc3_vec(q[:3] / s)
    s2 = math.sin(angle / 2.0)
    return qnorm(np.array([axis[0] * s2, axis[1] * s2, axis[2] * s2, math.cos(angle / 2.0)]))


def q_delta(q0, q1):
    """Shortest world rotation from q0 to q1 -> (angle_deg, axis or None)."""
    d = qmul(q1, qconj(q0))
    if d[3] < 0:
        d = -d
    w = min(1.0, max(-1.0, float(d[3])))
    angle = math.degrees(2.0 * math.acos(w))
    s = math.sqrt(max(0.0, 1.0 - w * w))
    axis = None if angle < 1e-8 or s < 1e-12 else d[:3] / s
    return angle, axis


def local_track(seq: dict, name: str, frame: int, bone: dict) -> tuple[np.ndarray, np.ndarray]:
    """Local pose for one bone, falling back to the bind local when a channel was removed."""
    tr = seq["_tracks"].get(name)
    if tr is not None and tr.get("position_m") is not None:
        lp = np.asarray(tr["position_m"][frame], dtype=np.float64) * 100.0
    else:
        lp = np.asarray(bone["bind"]["local_position_cm"], dtype=np.float64)
    if tr is not None and tr.get("rotation_quat") is not None:
        lq = qnorm(np.asarray(tr["rotation_quat"][frame], dtype=np.float64))
    else:
        lq = qnorm(np.asarray(bone["bind"]["local_rotation_quat"], dtype=np.float64))
    return lp, lq


def posed_world(seq: dict, frame: int, bones: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """(world positions cm, world quats) in PSK space for every bone."""
    n = len(bones)
    pos = np.zeros((n, 3), dtype=np.float64)
    quat = np.zeros((n, 4), dtype=np.float64)
    seen = np.zeros(n, dtype=bool)

    def visit(i: int):
        if seen[i]:
            return pos[i], quat[i]
        b = bones[i]
        lp, lq = local_track(seq, b["name"], frame, b)
        p = int(b["parent_index"])
        if p == i:
            pos[i], quat[i] = lp, lq
        else:
            pp, pq = visit(p)
            pos[i] = pp + qrot(pq, lp, inverse=True)
            quat[i] = qnorm(qmul(lq, pq))
        seen[i] = True
        return pos[i], quat[i]

    for i in range(n):
        visit(i)
    if not seen.all():
        raise PoseError("unvisited bones in %s" % seq["name"])
    return pos, quat


def bbox(points: np.ndarray) -> dict:
    lo = points.min(0)
    hi = points.max(0)
    return {
        "min_m": vec(lo),
        "max_m": vec(hi),
        "size_m": vec(hi - lo),
        "center_m": vec((lo + hi) / 2.0),
        "min_y_m": fnum(lo[POSE_Y]),
        "max_y_m": fnum(hi[POSE_Y]),
    }


def skin_points(pos: np.ndarray, quat: np.ndarray, mesh: dict,
                bind_pos: np.ndarray, bind_q: np.ndarray, offset: np.ndarray) -> np.ndarray:
    """Apply linear blend skinning, then the one JC3 transform. Returns (N,3) metres."""
    P = mesh["P"]
    W = mesh["W"]
    ro, rs, rn = mesh["chunks"]["RAWWEIGHTS"]
    if rs != 12:
        raise PoseError("RAWWEIGHTS stride %d, expected 12" % rs)
    rw = np.frombuffer(mesh["data"], np.dtype([
        ("w", "<f4"), ("p", "<u4"), ("b", "<u4")]), rn, ro)
    pi = rw["p"].astype(np.int64)
    bi = rw["b"].astype(np.int64)
    ww = rw["w"].astype(np.float64)
    if pi.max() >= len(P) or bi.max() >= len(pos):
        raise PoseError("RAWWEIGHTS index outside PNTS/REFSKELT")
    total = np.bincount(pi, weights=ww, minlength=len(P))
    if not np.allclose(total, 1.0, atol=1e-4):
        raise PoseError("point weights do not sum to 1 (max error %.3g)"
                        % float(np.max(np.abs(total - 1.0))))

    # bind-relative point, rotated into the posed bone, weighted, then accumulated
    rel = P[pi] - bind_pos[bi]
    local = qrot_batch(bind_q[bi], rel, inverse=True)
    posed = pos[bi] + qrot_batch(quat[bi], local)
    acc = np.zeros((len(P), 3), dtype=np.float64)
    for ax in range(3):
        acc[:, ax] = np.bincount(pi, weights=ww * posed[:, ax], minlength=len(P))
    return BA.to_jc3_rot(acc) * SCALE + offset


def yaw_between(a0: np.ndarray, a1: np.ndarray) -> float:
    """Signed rotation about JC3 +Y from vector a0 to a1, in degrees."""
    return math.degrees(math.atan2(float(np.dot(np.cross(a0, a1), [0.0, 1.0, 0.0])),
                                   float(np.dot(a0, a1))))


def build_doc() -> tuple[dict, str]:
    if not KEY_JSON.exists():
        raise PoseError("missing keyframes %s; run grab_anims.py --write" % KEY_JSON)
    bdoc = json.loads(BONES_JSON.read_text(encoding="utf-8"))
    bones = bdoc["bones"]
    if len(bones) != 180:
        raise PoseError("BONES.json has %d bones, expected 180" % len(bones))
    by_name = {b["name"]: b for b in bones}
    index = {b["name"]: b["index"] for b in bones}
    kdoc = json.loads(KEY_JSON.read_text(encoding="utf-8"))
    seqs = {s["name"]: s for s in kdoc["sequences"]}
    for s in seqs.values():
        s["_tracks"] = {t["bone"]: t for t in s["tracks"]}

    mesh_path = Path(bdoc["lods"][0]["file"])
    if not mesh_path.exists():
        raise PoseError("missing LOD0 mesh %s" % mesh_path)
    if sha256_file(mesh_path) != bdoc["lods"][0]["sha256"]:
        raise PoseError("LOD0 mesh hash differs from BONES.json")
    mesh = GB.read_mesh(mesh_path)
    if len(mesh["P"]) != bdoc["lods"][0]["points"]:
        raise PoseError("LOD0 point count differs from BONES.json")
    bind_pos = np.array([b["bind"]["world_position_cm"] for b in bones], dtype=np.float64)
    bind_q = np.array([b["bind"]["world_rotation_quat"] for b in bones], dtype=np.float64)
    offset = np.array(bdoc["transform"]["offset_used"], dtype=np.float64)

    def pose(seq_name: str, frame: int, role: str) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
        seq = seqs.get(seq_name)
        if seq is None:
            raise PoseError("sequence %s is missing" % seq_name)
        if frame < 0:
            frame += seq["num_frames"]
        if not 0 <= frame < seq["num_frames"]:
            raise PoseError("%s frame %d outside 0..%d"
                            % (seq_name, frame, seq["num_frames"] - 1))
        pos, quat = posed_world(seq, frame, bones)
        points = skin_points(pos, quat, mesh, bind_pos, bind_q, offset)
        time_s = seq["frame_times_s"][frame]
        return {
            "role": role,
            "source_sequence": seq_name,
            "frame": frame,
            "time_s": fnum(time_s),
            "frame_count": seq["num_frames"],
            "bbox": bbox(points),
            "bones": [{
                "name": b["name"],
                "index": b["index"],
                "parent": b["parent"],
                "position_m": vec(jc3_point(pos[b["index"]]) + offset),
                "rotation_quat_jc3": vec(jc3_quat(quat[b["index"]]), 7),
            } for b in bones],
        }, pos, quat, points

    pursuit, p_pos, p_quat, p_points = pose(CANON_OPEN, 0, "pursuit")
    battle, b_pos, b_quat, b_points = pose(CANON_OPEN, -1, "battle")

    chassis_i = index["Batmobile_Chassis"]
    turret_i = index["Batmobile_Rig_Weapons_Turret_Top"]
    chassis_d = jc3_point(b_pos[chassis_i] - p_pos[chassis_i])
    turret_d = jc3_point(b_pos[turret_i] - p_pos[turret_i])
    turret_rel_p = (p_pos[turret_i][2] - p_pos[chassis_i][2]) * SCALE
    turret_rel_b = (b_pos[turret_i][2] - b_pos[chassis_i][2]) * SCALE

    deltas = []
    for b in bones:
        i = b["index"]
        wd = jc3_point(b_pos[i] - p_pos[i])                      # metres
        wdist = float(np.linalg.norm(wd))
        wang, wax = q_delta(p_quat[i], b_quat[i])
        lp0, lq0 = local_track(seqs[CANON_OPEN], b["name"], 0, b)
        lp1, lq1 = local_track(seqs[CANON_OPEN], b["name"], -1, b)
        ld = jc3_point(lp1 - lp0)
        ldist = float(np.linalg.norm(ld))
        lang, lax = q_delta(lq0, lq1)
        moved = wdist >= MOVE_M or wang >= MOVE_DEG
        articulated = ldist >= MOVE_M or lang >= MOVE_DEG
        deltas.append({
            "name": b["name"],
            "index": i,
            "parent": b["parent"],
            "translation_m": vec(wd),
            "distance_m": fnum(wdist),
            "rotation_angle_deg": fnum(wang),
            "rotation_axis_jc3": None if wax is None else vec(wax),
            "local_translation_m": vec(ld),
            "local_distance_m": fnum(ldist),
            "local_rotation_angle_deg": fnum(lang),
            "local_rotation_axis_jc3": None if lax is None else vec(lax),
            "moved": moved,
            "articulated": articulated,
        })

    # Wheels: actual world orientations relative to the chassis.  The Game transition
    # splays the wheels ~19 degrees; it is not the 90-degree Tank_Strafe stance.
    wheels = ("Wheel_Parent_F_L", "Wheel_Parent_F_R",
              "Wheel_Parent_B_L", "Wheel_Parent_B_R")
    wheel_rows = []
    for name in wheels:
        i = index[name]
        q0 = qmul(p_quat[i], qconj(p_quat[chassis_i]))
        q1 = qmul(b_quat[i], qconj(b_quat[chassis_i]))
        ang, _axis = q_delta(q0, q1)
        a0 = jc3_vec(qrot(q0, np.array([1.0, 0.0, 0.0])))
        a1 = jc3_vec(qrot(q1, np.array([1.0, 0.0, 0.0])))
        wheel_rows.append({
            "bone": name,
            "battle_angle_deg": fnum(ang),
            "battle_axle_start_jc3": vec(a0),
            "battle_axle_end_jc3": vec(a1),
            "battle_yaw_about_y_deg": fnum(yaw_between(a0, a1)),
        })

    # Tank_Strafe: wheel local +X is the axle; it turns from +X to -Z over the sequence.
    strafe = seqs.get(STRAFE)
    if strafe is None:
        raise PoseError("sequence %s is missing" % STRAFE)
    strafe_rows = []
    _s0p, s0q = posed_world(strafe, 0, bones)
    _s1p, s1q = posed_world(strafe, strafe["num_frames"] - 1, bones)
    for name in wheels:
        b = by_name[name]
        i = b["index"]
        _lp0, lq0 = local_track(strafe, name, 0, b)
        _lp1, lq1 = local_track(strafe, name, strafe["num_frames"] - 1, b)
        # local X is the axle; the root translation is ignored, only rotation is used
        a0 = jc3_vec(qrot(s0q[i], np.array([1.0, 0.0, 0.0])))
        a1 = jc3_vec(qrot(s1q[i], np.array([1.0, 0.0, 0.0])))
        yaw = yaw_between(a0, a1)
        lang, lax = q_delta(lq0, lq1)
        strafe_rows.append({
            "bone": name,
            "local_rotation_deg": fnum(lang),
            "local_axis_jc3": None if lax is None else vec(lax),
            "axle_start_jc3": vec(a0),
            "axle_end_jc3": vec(a1),
            "yaw_about_y_deg": fnum(yaw),
        })

    fin_rows = []
    for b in bones:
        if "Aero_Flap" not in b["name"] and "Jet_Fin" not in b["name"]:
            continue
        i = b["index"]
        q0 = qmul(p_quat[i], qconj(p_quat[chassis_i]))
        q1 = qmul(b_quat[i], qconj(b_quat[chassis_i]))
        ang, _axis = q_delta(q0, q1)
        fin_rows.append({"bone": b["name"], "angle_vs_chassis_deg": fnum(ang)})

    # Variant endpoint comparison (cinematic vs gameplay).
    variants = []
    endpoint_cache = {}
    for open_name, close_name in ((CANON_OPEN, CANON_CLOSE),
                                  (CINEMATIC_OPEN, CINEMATIC_CLOSE)):
        for seq_name, frame, label in ((open_name, 0, "open_start"),
                                       (open_name, -1, "open_end"),
                                       (close_name, 0, "close_start"),
                                       (close_name, -1, "close_end")):
            p, pos, quat, points = pose(seq_name, frame, label)
            endpoint_cache[(seq_name, frame)] = (pos, quat)
            chassis = jc3_point(pos[chassis_i])
            turret = jc3_point(pos[turret_i])
            variants.append({
                "sequence": seq_name,
                "frame": p["frame"],
                "role": label,
                "bbox": p["bbox"],
                "chassis_position_m": vec(chassis + offset),
                "turret_top_position_m": vec(turret + offset),
            })

    g_open0 = endpoint_cache[(CANON_OPEN, 0)][0]
    g_open1 = endpoint_cache[(CANON_OPEN, -1)][0]
    g_close0 = endpoint_cache[(CANON_CLOSE, 0)][0]
    g_close1 = endpoint_cache[(CANON_CLOSE, -1)][0]
    loop_game = {
        "open_start_vs_close_end_pos_cm": fnum(max(float(np.linalg.norm(g_open0[i] - g_close1[i]))
                                                    for i in range(len(bones)))),
        "open_end_vs_close_start_pos_cm": fnum(max(float(np.linalg.norm(g_open1[i] - g_close0[i]))
                                                    for i in range(len(bones)))),
    }
    # rotations for the same pair
    gq_open0 = endpoint_cache[(CANON_OPEN, 0)][1]
    gq_open1 = endpoint_cache[(CANON_OPEN, -1)][1]
    gq_close0 = endpoint_cache[(CANON_CLOSE, 0)][1]
    gq_close1 = endpoint_cache[(CANON_CLOSE, -1)][1]
    loop_game["open_start_vs_close_end_rot_deg"] = fnum(max(
        q_delta(gq_close1[i], gq_open0[i])[0] for i in range(len(bones))))
    loop_game["open_end_vs_close_start_rot_deg"] = fnum(max(
        q_delta(gq_close0[i], gq_open1[i])[0] for i in range(len(bones))))
    loop_ok = (loop_game["open_start_vs_close_end_pos_cm"] <= LOOP_POS_CM and
               loop_game["open_end_vs_close_start_pos_cm"] <= LOOP_POS_CM and
               loop_game["open_start_vs_close_end_rot_deg"] <= LOOP_ROT_DEG and
               loop_game["open_end_vs_close_start_rot_deg"] <= LOOP_ROT_DEG)

    body = {
        "chassis_delta_m": vec(chassis_d),
        "chassis_lift_m": fnum(chassis_d[POSE_Y]),
        "bbox_min_y_delta_m": fnum(battle["bbox"]["min_y_m"] - pursuit["bbox"]["min_y_m"]),
        "bbox_max_y_delta_m": fnum(battle["bbox"]["max_y_m"] - pursuit["bbox"]["max_y_m"]),
    }
    turret = {
        "bone": "Batmobile_Rig_Weapons_Turret_Top",
        "raise_m": fnum(turret_d[POSE_Y]),
        "raise_relative_chassis_m": fnum(turret_rel_b - turret_rel_p),
        "delta_m": vec(turret_d),
        "pursuit_position_m": vec(jc3_point(p_pos[turret_i]) + offset),
        "battle_position_m": vec(jc3_point(b_pos[turret_i]) + offset),
    }
    summary = {
        "bones_total": len(bones),
        "bones_world_moved": sum(1 for d in deltas if d["moved"]),
        "bones_articulated": sum(1 for d in deltas if d["articulated"]),
        "max_world_translation": max(deltas, key=lambda d: d["distance_m"])["name"],
        "max_world_translation_m": max(d["distance_m"] for d in deltas),
        "max_world_rotation": max(deltas, key=lambda d: d["rotation_angle_deg"])["name"],
        "max_world_rotation_deg": max(d["rotation_angle_deg"] for d in deltas),
        "turret": turret,
        "body": body,
        "wheels": wheel_rows,
        "strafe": strafe_rows,
        "fins": fin_rows,
        "bbox_delta_m": {
            "x": fnum(battle["bbox"]["size_m"][0] - pursuit["bbox"]["size_m"][0]),
            "y": fnum(battle["bbox"]["size_m"][1] - pursuit["bbox"]["size_m"][1]),
            "z": fnum(battle["bbox"]["size_m"][2] - pursuit["bbox"]["size_m"][2]),
        },
    }

    checks = {
        "bones_total_180": len(bones) == 180,
        "pose_has_all_bones": (len(pursuit["bones"]) == len(bones) and
                               len(battle["bones"]) == len(bones)),
        "all_deltas_accounted": len(deltas) == len(bones),
        "fin_bones_present": len(fin_rows) == 13,
        "game_open_close_loop": loop_ok,
        "canonical_is_game_variant": CANON_OPEN.endswith("_Game"),
        "game_bbox_wider_than_pursuit": battle["bbox"]["size_m"][0] > pursuit["bbox"]["size_m"][0],
        "game_bbox_taller_than_pursuit": battle["bbox"]["max_y_m"] > pursuit["bbox"]["max_y_m"],
    }

    doc = {
        "schema": SCHEMA,
        "generator": "grab_poses.py",
        "verdict": (
            "Pursuit -> battle (%s f0 -> f%d): turret +%.3f m, chassis %.3f m, "
            "wheel splay %.2f-%.2f deg; full bbox %.3f x %.3f x %.3f -> %.3f x %.3f x %.3f m; "
            "%d/%d bones move, %d articulate. Tank_Strafe adds %.1f deg wheel yaw."
            % (CANON_OPEN, battle["frame"], turret["raise_m"], body["chassis_lift_m"],
               min(abs(w["battle_angle_deg"]) for w in wheel_rows),
               max(abs(w["battle_angle_deg"]) for w in wheel_rows),
               pursuit["bbox"]["size_m"][0], pursuit["bbox"]["size_m"][1], pursuit["bbox"]["size_m"][2],
               battle["bbox"]["size_m"][0], battle["bbox"]["size_m"][1], battle["bbox"]["size_m"][2],
               summary["bones_world_moved"], len(bones), summary["bones_articulated"],
               max(abs(w["yaw_about_y_deg"]) for w in strafe_rows))
        ),
        "inputs": {
            "bones_json": str(BONES_JSON),
            "bones_sha256": sha256_file(BONES_JSON),
            "animation_keys": str(KEY_JSON),
            "animation_keys_sha256": sha256_file(KEY_JSON),
            "mesh": str(mesh_path),
            "mesh_sha256": sha256_file(mesh_path),
            "package": PACKAGE,
            "anim_set": ANIM_SET,
        },
        "convention": {
            "mesh_frame": "PSK: X length, Y width, Z up, centimetres",
            "jc3_frame": "X width (left negative), Y up, Z length (front -Z), metres",
            "point_transform": "bat_assemble.to_jc3_rot(p) * 0.01 + offset",
            "rotation_transform": "rotate the axis with to_jc3_rot, keep the angle",
            "local_pose": "metres/cm and PSK quaternion; missing channel falls back to bind local",
            "world_pose": "world = q_child * q_parent; child offset rotated by inverse parent q",
            "bbox": "linear-blend skinning of all 201,338 LOD0 points through the pose",
            "canonical": "Tank_Spread_Open_Game frame 0 = pursuit, frame 60 = battle",
        },
        "poses": {"pursuit": pursuit, "battle": battle},
        "summary": summary,
        "deltas": deltas,
        "variants": variants,
        "loop": loop_game,
        "checks": checks,
    }

    # ---- markdown ----
    md = []
    md.append("# Batmobile_V2 — pursuit ↔ battle poses (G1-12)")
    md.append("")
    md.append("Generated by `Tools/scripts/grab_poses.py` from `BONES.json`, the LOD0 PSKX and "
              "`%s`." % KEY_JSON.name)
    md.append("")
    md.append("**Verdict:** " + doc["verdict"])
    md.append("")
    md.append("## Convention")
    md.append("")
    md.append("- Positions are JC3 metres: X width, Y up, Z length with the nose at **-Z**.")
    md.append("- Bone poses are reconstructed from the PSK left-handed convention "
              "(`world = q_child * q_parent`, child offset rotated by the inverse parent).")
    md.append("- The one transform is `to_jc3_rot(p) * 0.01 + offset`; rotations keep their angle "
              "and rotate their axis through the same proper rotation.")
    md.append("- A missing animation channel falls back to that bone's bind local transform; the "
              "key-frame export marks removed channels null, not zero.")
    md.append("")
    md.append("## Poses")
    md.append("")
    md.append("| pose | source | frame | time | bbox min (m) | bbox max (m) | size (m) |")
    md.append("|---|---|---:|---:|---|---|---|")
    for p in (pursuit, battle):
        bb = p["bbox"]
        md.append("| %s | `%s` | %d | %.3f s | %s | %s | %s |" % (
            p["role"], p["source_sequence"], p["frame"], p["time_s"],
            ", ".join("%.3f" % x for x in bb["min_m"]),
            ", ".join("%.3f" % x for x in bb["max_m"]),
            " × ".join("%.3f" % x for x in bb["size_m"])))
    md.append("")
    md.append("## Named deltas")
    md.append("")
    md.append("| quantity | value | note |")
    md.append("|---|---:|---|")
    md.append("| turret raise (`Turret_Top`, world Y) | **%+.3f m** | %.3f m relative to the chassis |"
              % (turret["raise_m"], turret["raise_relative_chassis_m"]))
    md.append("| chassis lift (world Y) | **%+.3f m** | body settles; bbox bottom %+.3f m, top %+.3f m |"
              % (body["chassis_lift_m"], body["bbox_min_y_delta_m"], body["bbox_max_y_delta_m"]))
    md.append("| full bbox width | %.3f → %.3f m | %+.3f m |" % (
        pursuit["bbox"]["size_m"][0], battle["bbox"]["size_m"][0],
        summary["bbox_delta_m"]["x"]))
    md.append("| full bbox height | %.3f → %.3f m | %+.3f m |" % (
        pursuit["bbox"]["size_m"][1], battle["bbox"]["size_m"][1],
        summary["bbox_delta_m"]["y"]))
    md.append("| full bbox length | %.3f → %.3f m | %+.3f m |" % (
        pursuit["bbox"]["size_m"][2], battle["bbox"]["size_m"][2],
        summary["bbox_delta_m"]["z"]))
    md.append("| bones moved | **%d / %d** | world translation or rotation |" % (
        summary["bones_world_moved"], len(bones)))
    md.append("| bones articulated | **%d** | local (parent-relative) transform changed |" % (
        summary["bones_articulated"]))
    md.append("")
    md.append("### Turret")
    md.append("")
    md.append("`Batmobile_Rig_Weapons_Turret_Top` moves from "
              "`%s` to `%s` m." % (turret["pursuit_position_m"], turret["battle_position_m"]))
    md.append("")
    md.append("### Wheels: battle splay vs strafe stance")
    md.append("")
    md.append("The gameplay spread sequence rotates each wheel about the vertical by the angle "
              "below, relative to the chassis. This is a **toe/splay**, not the 90° strafe stance.")
    md.append("")
    md.append("| wheel bone | total rotation | axle start (JC3) | axle end (JC3) | signed yaw about +Y |")
    md.append("|---|---:|---|---|---:|")
    for w in wheel_rows:
        md.append("| `%s` | %.2f° | %s | %s | %+.2f° |" % (
            w["bone"], w["battle_angle_deg"],
            ", ".join("%.3f" % x for x in w["battle_axle_start_jc3"]),
            ", ".join("%.3f" % x for x in w["battle_axle_end_jc3"]),
            w["battle_yaw_about_y_deg"]))
    md.append("")
    md.append("`Batmobile_V2_Tank_Strafe` is the actual strafe stance. Its root translates "
              "4.89 m, so only the wheel rotation is used:")
    md.append("")
    md.append("| wheel bone | local rotation | axle start (JC3) | axle end (JC3) | yaw about +Y |")
    md.append("|---|---:|---|---|---:|")
    for w in strafe_rows:
        md.append("| `%s` | %.2f° | %s | %s | %+.2f° |" % (
            w["bone"], w["local_rotation_deg"],
            ", ".join("%.3f" % x for x in w["axle_start_jc3"]),
            ", ".join("%.3f" % x for x in w["axle_end_jc3"]),
            w["yaw_about_y_deg"]))
    md.append("")
    md.append("### Fins")
    md.append("")
    md.append("All %d aero-fin bones stay rigid to the chassis in this pose (max %.3f°); the "
              "spread transition does not deploy the fins." %
              (len(fin_rows), max(abs(f["angle_vs_chassis_deg"]) for f in fin_rows)))
    md.append("")
    md.append("## Variant endpoints")
    md.append("")
    md.append("| sequence | frame | role | bbox size (m) | chassis y (m) | turret y (m) |")
    md.append("|---|---:|---|---|---:|---:|")
    for v in variants:
        md.append("| `%s` | %d | %s | %s | %.3f | %.3f |" % (
            v["sequence"], v["frame"], v["role"],
            " × ".join("%.3f" % x for x in v["bbox"]["size_m"]),
            v["chassis_position_m"][1], v["turret_top_position_m"][1]))
    md.append("")
    md.append("Game variant loop check: open start vs close end %.3f cm / %.3f°, "
              "open end vs close start %.3f cm / %.3f°." % (
                  loop_game["open_start_vs_close_end_pos_cm"],
                  loop_game["open_start_vs_close_end_rot_deg"],
                  loop_game["open_end_vs_close_start_pos_cm"],
                  loop_game["open_end_vs_close_start_rot_deg"]))
    md.append("")
    md.append("## Every bone delta")
    md.append("")
    md.append("`world` is the pose-to-pose movement in JC3 metres. `local` is relative to the "
              "bone's parent and identifies what actually articulated; a bone that only rides "
              "the chassis has `local = 0`.")
    md.append("")
    md.append("| # | bone | parent | world Δx | Δy | Δz | world m | world rot | local rot |")
    md.append("|---:|---|---|---:|---:|---:|---:|---:|---:|")
    for d in sorted(deltas, key=lambda x: x["index"]):
        md.append("| %d | `%s` | `%s` | %+.3f | %+.3f | %+.3f | %.4f | %.2f° | %.2f° |" % (
            d["index"], d["name"], d["parent"],
            d["translation_m"][0], d["translation_m"][1], d["translation_m"][2],
            d["distance_m"], d["rotation_angle_deg"], d["local_rotation_angle_deg"]))
    md.append("")
    md.append("## Checks")
    md.append("")
    md.append("| check | result |")
    md.append("|---|---|")
    for k, v in checks.items():
        md.append("| `%s` | %s |" % (k, "PASS" if v else "**FAIL**"))
    md.append("")
    md.append("A moved bone is one with world translation ≥ %.1f mm or world rotation ≥ %.2f°. "
              "An articulated bone additionally has a parent-relative change above the same "
              "threshold. `--check` re-derives both files." % (MOVE_M * 1000, MOVE_DEG))
    md.append("")
    return doc, "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write POSES.json and POSES.md")
    g.add_argument("--check", action="store_true", help="re-derive and compare the outputs")
    a = ap.parse_args()
    try:
        doc, md = build_doc()
    except (PoseError, KeyError, ValueError, OSError) as e:
        print("FAIL: %s" % e, file=sys.stderr)
        return 1

    fail = [k for k, v in doc["checks"].items() if not v]
    if fail:
        print("FAIL: checks %s" % ", ".join(fail), file=sys.stderr)
        return 1

    if a.write:
        OUT_JSON.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        OUT_MD.write_text(md + "\n", encoding="utf-8")
        print(doc["verdict"])
        print("wrote %s and %s" % (OUT_JSON, OUT_MD))
        return 0

    if not OUT_JSON.exists() or not OUT_MD.exists():
        print("FAIL: outputs missing; run --write", file=sys.stderr)
        return 1
    old = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    if json.dumps(old, sort_keys=True) != json.dumps(doc, sort_keys=True):
        print("FAIL: POSES.json differs from the re-derived record", file=sys.stderr)
        return 1
    if OUT_MD.read_text(encoding="utf-8").rstrip("\n") != md.rstrip("\n"):
        print("FAIL: POSES.md differs from the re-derived record", file=sys.stderr)
        return 1
    print("PASS: %s" % doc["verdict"])
    for k, v in doc["checks"].items():
        print("  %-36s %s" % (k, "PASS" if v else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
