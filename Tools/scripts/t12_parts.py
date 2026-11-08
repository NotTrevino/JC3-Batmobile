#!/usr/bin/env python
"""t12_parts.py - T-12: one behaviour row per moving part of the Batmobile (doc T-8).

Reads the grab evidence and regenerates `Working/Translation/T8_PARTS.{md,json}`:

    BmAK  Research/BatmobileGrab/ANIMATIONS.json   G1-10  253 sequences: mechanism, frames, length,
                                                          moved bones with per-bone degrees
          Research/BatmobileGrab/BONES.json        G1-11  bind pose + `pivot_jc3_m` per bone
          Research/BatmobileGrab/POSES.json        G1-12  pursuit -> battle deltas
          E:/Modding/_shared/gamedata/BmAKgrab/anims/keys/*.json   G1-10  per-bone key frames (game data, outside repo)
    JC3   Research/JC3Grab/MOVING_PARTS.json       G2-14  behaviour -> channel, variable, proof
          Research/JC3Grab/TURRET.json             G2-13  carrier hinge: axis, min/max deg, damage type
          Research/JC3Grab/DOORS.json              G2-15  door answers, per-part hinges
          Research/JC3Grab/PARTS_TABLE.jsonl       P0-2   per-part damage type `dt` of every fleet part
    this repo  Working/Translation/T8_PARTS.json           the part cut (B-02) this doc extends
               Working/Appearance/build_parts/parts_manifest.json   faces per LOD, pivot, offset
               Tools/scripts/bat_assemble.py               the ONE transform (R2), imported

Per part it derives, never types:

    pivot      = bat_assemble.pivot_point(bind world_position_cm, scale, offset)   (R2)
    axis       the bone-local Euler component with the largest span over the part's sequences
    limits     min/max of that component, degrees, over the animation's extreme frames
    rate       max |delta angle| / delta time between adjacent key frames, deg/s
    carrier    the JC3 behaviour name, its driving variable and the fleet hinge (axis/min/max/
               damage type) from the medium tank / monorail / donor as the behaviour's closest
               shipped carrier
    LOD        from parts_manifest.json (the part exists in LOD1..5 at the same pivot)

Usage
    python Tools/scripts/t12_parts.py --write
    python Tools/scripts/t12_parts.py --check
    python Tools/scripts/t12_parts.py dump rows|parts
"""
from __future__ import annotations

import argparse
import difflib
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bat_assemble  # noqa: E402  (pivot_point / to_jc3_rot - the one transform, R2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab")
JC3 = os.path.join(ROOT, "Research", "JC3Grab")
TRANS = os.path.join(ROOT, "Working", "Translation")
KEYS = os.environ.get("BMAK_KEYS", r"E:/Modding/_shared/gamedata/BmAKgrab/anims/keys")
MANIFEST = os.path.join(ROOT, "Working", "Appearance", "build_parts", "parts_manifest.json")
SPEC = os.path.join(TRANS, "T8_PARTS.json")
MD = os.path.join(TRANS, "T8_PARTS.md")
BASE_PKG = "Playable_Batmobile_SF"

# The card's eight mechanisms -> (row id, part name or None, BmAK bones, JC3 behaviour, extents)
# `bones` is explicit only where the T-8 cut has no part (canopy / hatches / yoke); otherwise the
# part's own bone list from T8_PARTS.json is used.
ROWS = [
    dict(id="P-01", part="batmobile_turret", mechanism="turret", behaviour="Turret",
         part_bones="prefix:Batmobile_Rig_Weapons_Turret_", carrier="v0201_car_capstone_mediumtank",
         carrier_behavior="Turret", verify="Q-1 #4: turret follows the camera aim. Pass = yaw "
         "sweeps the measured span without clipping the body, 3/3 targets"),
    dict(id="P-02", part="batmobile_cannon", mechanism="cannon", behaviour="Cannon",
         part_bones="prefix:Batmobile_Rig_Weapons_Heavy_Cannon_",
         carrier="v0201_car_capstone_mediumtank", carrier_behavior="Cannon",
         verify="Q-1 #4: cannon pitch limits. Pass = the barrel stops at the carrier's own "
         "-5..20 deg and does not enter the hull, 3/3"),
    dict(id="P-03", part="batmobile_machine_gun", mechanism="Vulcan", behaviour="GatlingGun",
         part_bones="prefix:Batmobile_Rig_Weapons_Machine_Gun_", carrier=None,
         carrier_behavior=None,
         verify="Q-1 #4 / Q-3 #3: barrels spin while firing (ANI-3). Pass = spin starts on the "
         "first round and stops with the burst, 3/3"),
    dict(id="P-04", part="batmobile_riot_suppressor", mechanism="cannon",
         behaviour="Cannon", part_bones="prefix:Batmobile_Rig_Weapons_Riot_",
         carrier="v0201_car_capstone_mediumtank", carrier_behavior="Cannon",
         verify="Q-1 #4: the suppressor elevator swings to its stored angle and back. Pass = "
         "return to 0 within 1 frame after release"),
    dict(id="P-05", part="batmobile_jet", mechanism="transformation", behaviour="EngineRotatingPart",
         part_bones="prefix:JetSMove", carrier="v0506_car_generic_oldtractor",
         carrier_behavior="EngineRotatingPart",
         verify="Q-1 #4: turbine spins with engine rpm (ANI-4). Pass = the fan turns at idle and "
         "speeds up with the rev sweep, 3/3"),
    dict(id="P-06", part=None, mechanism="canopy", behaviour="Hood",
         part_bones=["CockPit_Mesh"], carrier="v0300_car_kensington_sportsmuscle",
         carrier_behavior="Hood",
         verify="Q-1 #3: canopy opens on entry (MOD-4/ANI-8). Pass = it moves 0.71 m and 11 deg "
         "without intersecting the roof, and closes on exit, 3/3"),
    dict(id="P-07", part=None, mechanism="missile bays", behaviour="MissileHatch",
         part_bones=["Batmobile_Rig_Weapons_Missiles_L_T", "Batmobile_Rig_Weapons_Missiles_L_B",
                     "Batmobile_Rig_Weapons_Missiles_L_Mid"],
         carrier="v7800_train_monorailmissilecar", carrier_behavior="MissileHatch",
         verify="Q-1 #4: left bay opens when its missiles fire (ANI-6). Pass = the cover lifts "
         "14.99 deg, missiles leave, cover closes, 3/3 salvos"),
    dict(id="P-08", part=None, mechanism="missile bays", behaviour="MissileHatch",
         part_bones=["Batmobile_Rig_Weapons_Missiles_R_T", "Batmobile_Rig_Weapons_Missiles_R_B",
                     "Batmobile_Rig_Weapons_Missiles_R_Mid"],
         carrier="v7800_train_monorailmissilecar", carrier_behavior="MissileHatch",
         verify="Q-1 #4: right bay opens when its missiles fire (ANI-6), same pass as P-07"),
    dict(id="P-09", part="batmobile_aero_flap_l_f", mechanism="fins/air-brakes",
         behaviour="AirBrake", part_bones="prefix:Batmobile_Rig_Aero_Flap_L_F",
         carrier="v1000_plane_aurora", carrier_behavior="AirBrake",
         verify="Q-1 #4 air-brake probe: brake hard from 40 km/h. Pass = the flap moves; if it "
         "does not, ANI-5 becomes a static part with this row as the reason"),
    dict(id="P-10", part="batmobile_aero_flap_r_f", mechanism="fins/air-brakes",
         behaviour="AirBrake", part_bones="prefix:Batmobile_Rig_Aero_Flap_R_F",
         carrier="v1000_plane_aurora", carrier_behavior="AirBrake",
         verify="Q-1 #4 air-brake probe (right front), same pass as P-09"),
    dict(id="P-11", part="batmobile_aero_flap_l_b", mechanism="fins/air-brakes",
         behaviour="AirBrake", part_bones="prefix:Batmobile_Rig_Aero_Flap_L_B",
         carrier="v1000_plane_aurora", carrier_behavior="AirBrake",
         verify="Q-1 #4 air-brake probe (left rear), same pass as P-09"),
    dict(id="P-12", part="batmobile_aero_flap_r_b", mechanism="fins/air-brakes",
         behaviour="AirBrake", part_bones="prefix:Batmobile_Rig_Aero_Flap_R_B",
         carrier="v1000_plane_aurora", carrier_behavior="AirBrake",
         verify="Q-1 #4 air-brake probe (right rear), same pass as P-09"),
    dict(id="P-13", part=None, mechanism=None, behaviour="SteeringWheel",
         part_bones=[], carrier=None, carrier_behavior="SteeringWheel",
         verify="Q-1 #4: yoke turns with steering (ANI-7). STATIC: no bone and no geometry "
         "(G1-19), so the row records why nothing moves"),
    dict(id="P-14", part="batmobile_missile_pod_l", mechanism="missile bays",
         behaviour=None, moves_with="P-07",
         part_bones="prefix:Batmobile_Rig_Weapons_Missiles_L_", carrier=None,
         carrier_behavior=None,
         verify="V-04 file check: the pod shell is a static part; its cover is P-07"),
    dict(id="P-15", part="batmobile_missile_pod_r", mechanism="missile bays",
         behaviour=None, moves_with="P-08",
         part_bones="prefix:Batmobile_Rig_Weapons_Missiles_R_", carrier=None,
         carrier_behavior=None,
         verify="V-04 file check: the pod shell is a static part; its cover is P-08"),
]


# ---------------------------------------------------------------------------------------------
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def bone_tracks(seq: dict, bones: list[str]) -> dict:
    return {t["bone"]: t for t in seq["tracks"] if t["bone"] in bones}


def euler_extents(frames: list, tdp: float) -> dict:
    """Per-axis (min, max, max rate) of one bone's local Euler key frames, degrees / deg per s."""
    rows = [f for f in frames if f is not None]
    out = {}
    for axis in range(3):
        vals = [math.degrees(r[axis]) for r in rows]
        if not vals:
            out[axis] = None
            continue
        rate = 0.0
        steps = []
        for a, b in zip(rows, rows[1:]):
            if a is None or b is None or not tdp:
                continue
            # Euler wraps at +/-180: take the short way round or a spin reads as 10,000 deg/s
            d = (b[axis] - a[axis] + math.pi) % (2 * math.pi) - math.pi
            steps.append(math.degrees(d))
            rate = max(rate, abs(math.degrees(d)) / tdp)
        # A continuous spin comes back to where it started, so max-min is one wrap and not the
        # motion.  Sum the short-way steps: that is the travel, and a monotonic sign means the
        # channel is spinning rather than oscillating between two limits.
        travel = sum(abs(s) for s in steps)
        moving = [s for s in steps if abs(s) > 1e-9]
        monotonic = bool(moving) and (all(s > 0 for s in moving) or all(s < 0 for s in moving))
        out[axis] = {"min_deg": round(min(vals), 3), "max_deg": round(max(vals), 3),
                     "span_deg": round(max(vals) - min(vals), 3), "max_rate_deg_s": round(rate, 2),
                     "travel_deg": round(travel, 3), "turns": round(travel / 360.0, 3),
                     "monotonic": monotonic,
                     "duration_s": round(max(0.0, (len(rows) - 1) * (tdp or 0.0)), 3)}
    return out


def dominant_axis(ext: dict) -> int | None:
    spans = [(v["span_deg"], i) for i, v in ext.items() if v]
    return max(spans)[1] if spans else None


AXIS_NAME = {0: "+X", 1: "+Y", 2: "+Z"}


def quat_rotate(q: list, v: list) -> list:
    """Rotate a vector by a (x,y,z,w) quaternion."""
    x, y, z, w = q
    vx, vy, vz = v
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return [vx + w * tx + (y * tz - z * ty),
            vy + w * ty + (z * tx - x * tz),
            vz + w * tz + (x * ty - y * tx)]


def _same_axis(a: list, b: list) -> bool:
    """Do two axes describe the same joint line (parallel or antiparallel, 1e-3 tolerance)?"""
    if not a or not b:
        return False
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return abs(abs(dot) / (na * nb) - 1.0) < 1e-3


def collect(seqs: list, keys: dict, bones: list[str]) -> dict:
    """Union of per-bone Euler extents over every sequence of one mechanism."""
    per_bone = {}
    trans = {}
    used = []
    for seq in seqs:
        kf = keys.get((seq["package"], seq["set"], seq["name"]))
        if not kf:
            continue
        hit = False
        for name, track in bone_tracks(kf["seq"], bones).items():
            eul = track.get("rotation_euler_xyz_rad")
            if track.get("removed") == "rot" or not eul:
                continue
            times = kf["frames"]
            tdp = (times[1] - times[0]) if len(times) > 1 else 0.0
            ext = euler_extents(eul, tdp)
            slot = per_bone.setdefault(name, {"seqs": [], "ext": {}, "spans": {}})
            slot["seqs"].append(seq["name"])
            for a, v in ext.items():
                if not v:
                    continue
                slot["spans"].setdefault(a, []).append(
                    {"sequence": seq["name"], "span_deg": v["span_deg"],
                     "travel_deg": v["travel_deg"], "turns": v["turns"],
                     "monotonic": v["monotonic"]})
                cur = slot["ext"].get(a)
                if cur is None:
                    slot["ext"][a] = dict(v, travel_sequence=seq["name"])
                else:
                    cur["min_deg"] = min(cur["min_deg"], v["min_deg"])
                    cur["max_deg"] = max(cur["max_deg"], v["max_deg"])
                    cur["span_deg"] = round(cur["max_deg"] - cur["min_deg"], 3)
                    cur["max_rate_deg_s"] = max(cur["max_rate_deg_s"], v["max_rate_deg_s"])
                    # the travel of the longest single sequence, not a sum over sequences
                    if v["travel_deg"] > cur.get("travel_deg", 0):
                        cur["travel_deg"] = v["travel_deg"]
                        cur["turns"] = v["turns"]
                        cur["duration_s"] = v["duration_s"]
                        cur["travel_sequence"] = seq["name"]
                    cur["monotonic"] = cur.get("monotonic", True) and v["monotonic"]
            hit = True
        for mb in seq.get("moved_bones") or []:
            if mb.get("bone") in bones and (mb.get("dpos_cm") or 0) > 0:
                slot = trans.setdefault(mb["bone"], {"max_cm": 0.0, "sequence": None})
                if mb["dpos_cm"] > slot["max_cm"]:
                    slot["max_cm"] = round(float(mb["dpos_cm"]), 3)
                    slot["sequence"] = seq["name"]
        if hit:
            used.append(seq["name"])
    return {"bones": per_bone, "translation": trans, "sequences": sorted(set(used))}


def key_files() -> dict:
    """(package, set, name) -> {seq, frames} for every exported AnimSet key file."""
    out = {}
    for path in sorted(glob.glob(os.path.join(KEYS, "*.json"))):
        d = load_json(path)
        if "sequences" not in d:
            continue
        for seq in d["sequences"]:
            times = seq.get("frame_times_s") or []
            out[(d["package"], d["set"], seq["name"])] = {"seq": seq, "frames": times}
    return out


def carrier_hinge(turret: dict, chassis: str, behavior: str) -> dict | None:
    """The shipped hinge for one behaviour: pick the named carrier, else the first entity that has it."""
    def rows(ent):
        for cp in ent.get("constrained_parts") or []:
            if cp.get("behavior") == behavior and cp.get("hinge"):
                return {"entity": ent.get("entity"), "part": cp.get("part"),
                        "axis": cp["hinge"]["axis"], "min_deg": cp["hinge"].get("min_deg"),
                        "max_deg": cp["hinge"].get("max_deg"),
                        "pivot": cp["hinge"].get("pivot"),
                        "damage_type": cp.get("damage_type"),
                        "class": cp["hinge"].get("class")}
        return None
    for ent in turret["samples"]:
        if chassis and chassis in (ent.get("entity") or ""):
            hit = rows(ent)
            if hit:
                return hit
    for ent in turret["samples"]:
        hit = rows(ent)
        if hit:
            return hit
    return None


def part_table_dt(rows: list) -> dict:
    """behaviour -> damage types the fleet gives parts with that behaviour, land values first
    (decoded (fleet): PARTS_TABLE's `dt` per part, `01_land/` preferred over sea/air)."""
    out: dict[str, dict] = {}
    for r in rows:
        land = "/01_land/" in (r.get("entity") or "")
        for p in r.get("parts") or []:
            b, dt = p.get("b"), p.get("dt")
            if b and dt and b != "None":
                slot = out.setdefault(b, {"land": set(), "all": set()})
                slot["all"].add(dt)
                if land:
                    slot["land"].add(dt)
    return {k: {"chosen": sorted(v["land"] or v["all"])[0], "fleet": sorted(v["all"]),
                "land": sorted(v["land"])}
            for k, v in sorted(out.items())}


def build() -> dict:
    anims = load_json(os.path.join(BMAK, "ANIMATIONS.json"))
    bones = load_json(os.path.join(BMAK, "BONES.json"))
    poses = load_json(os.path.join(BMAK, "POSES.json"))
    moving = load_json(os.path.join(JC3, "MOVING_PARTS.json"))
    turret = load_json(os.path.join(JC3, "TURRET.json"))
    keys = key_files()
    manifest = load_json(MANIFEST)
    spec = load_json(SPEC)
    scale = manifest["scale"]
    offset = manifest["offset"]
    bone_by_name = {b["name"]: b for b in bones["bones"]}
    offset_delta = float(bones["transform"]["offset_delta_m"])
    bhv = {b["behaviour"]: b for b in moving["behaviours"]}
    parts_by_name = {p["name"]: p for p in spec["parts"]}
    entries = {e["name"]: e for e in manifest["entries"]}
    with open(os.path.join(JC3, "PARTS_TABLE.jsonl"), encoding="utf-8") as f:
        ptable_rows = [json.loads(line) for line in f if line.strip()]
    dt_by_behaviour = part_table_dt(ptable_rows)
    seqs_by_mech = {}
    for s in anims["sequences"]:
        if s["package"] == BASE_PKG:
            seqs_by_mech.setdefault(s["mechanism"], []).append(s)

    out = []
    for row in ROWS:
        part = parts_by_name.get(row["part"]) if row["part"] else None
        if isinstance(row["part_bones"], str) and row["part_bones"].startswith("prefix:"):
            pref = row["part_bones"][len("prefix:"):]
            bl = [b for b in bone_by_name if b.startswith(pref)] if not part else \
                [b for b in bone_by_name if b.startswith(pref)]
        elif isinstance(row["part_bones"], list):
            bl = row["part_bones"]
        else:
            bl = []
        seqs = seqs_by_mech.get(row["mechanism"], []) if row["mechanism"] else []
        got = collect(seqs, keys, set(bl))
        # pivots through the ONE transform (R2): BONES.json keeps the bind world position in cm
        pivots = {}
        for name in bl:
            b = bone_by_name.get(name)
            if not b:
                continue
            derived = bat_assemble.pivot_point(b["bind"]["world_position_cm"], scale, offset)
            stored = b.get("pivot_jc3_m") or [0, 0, 0]
            pivots[name] = {
                "pivot_jc3_m": [round(float(x), 6) for x in derived],
                "stored_pivot_jc3_m": [round(float(x), 6) for x in stored],
                "delta_m": round(float(max(abs(a - c) for a, c in zip(derived, stored))), 9),
                "parent": b.get("parent"),
            }
        pivot_bone = (part["pivot_bone"] if part else (row["part_bones"][0] if isinstance(
            row["part_bones"], list) and row["part_bones"] else None))
        joint = None
        # the joint is the animated bone with the largest span (often a child of the part pivot)
        best = None
        candidates = []
        for name, slot in got["bones"].items():
            ext = slot.get("ext") or {}
            axis = dominant_axis(ext)
            if axis is None:
                continue
            candidates.append({"bone": name, "axis_local": AXIS_NAME[axis],
                               "span_deg": ext[axis]["span_deg"],
                               "min_deg": ext[axis]["min_deg"],
                               "max_deg": ext[axis]["max_deg"],
                               "max_rate_deg_s": ext[axis]["max_rate_deg_s"],
                               "travel_deg": ext[axis].get("travel_deg"),
                               "turns": ext[axis].get("turns"),
                               "monotonic": ext[axis].get("monotonic"),
                               "is_pivot_bone": name == pivot_bone})
            cand = (ext[axis]["span_deg"], name, axis, ext[axis])
            if best is None or cand[0] > best[0]:
                best = cand
        candidates.sort(key=lambda c: -c["span_deg"])
        if best:
            _, name, axis, ext = best
            seq_spans = (got["bones"].get(name) or {}).get("spans", {}).get(axis) or []
            part_bone_ext = next((c for c in candidates if c["is_pivot_bone"]), None)
            joint = {"bone": name, "part_pivot_bone": pivot_bone,
                     "is_pivot_bone": name == pivot_bone, "axis_index": axis,
                     "axis_local": AXIS_NAME[axis], "candidates": candidates, **ext,
                     # the same frame count for every track of a sequence, so the travel is
                     # over one clip length
                     "per_sequence_spans": seq_spans,
                     "part_bone_extent": part_bone_ext,
                     # a monotonic channel with several turns is a spin: its max-min is one wrap
                     "is_spin": bool(ext.get("monotonic") and (ext.get("turns") or 0) >= 1.0),
                     "axis_jc3": [round(float(x), 4) for x in bat_assemble.to_jc3_rot(
                         np.array([[1.0 if i == axis else 0.0 for i in range(3)]]))[0]],
                     # vehicle space: the bone-local axis through the bone's bind rotation, so
                     # it can be compared with a shipped hinge axis at all
                     "axis_world_jc3": [round(float(x), 4) for x in bat_assemble.to_jc3_rot(
                         np.array([quat_rotate(bone_by_name[name]["bind"]["world_rotation_quat"],
                                               [1.0 if i == axis else 0.0 for i in range(3)])]))[0]]}
        hinge = carrier_hinge(turret, row["carrier"], row["carrier_behavior"]) \
            if row["carrier_behavior"] else None
        m = bhv.get(row["behaviour"]) if row["behaviour"] else None
        ent = entries.get(row["part"]) if row["part"] else None
        dt = (dt_by_behaviour.get(row["behaviour"] or "") or {}).get("chosen")
        # The Done clause allows a row to stay static only with a reason.  Store it, derived from
        # the measured translation / bones / driving variable, instead of leaving it to prose.
        static_reason = None
        if not joint:
            trans = got["translation"] or {}
            top = max(trans.items(), key=lambda kv: kv[1]["max_cm"]) if trans else None
            if row.get("moves_with"):
                static_reason = ("no joint of its own; it is the shell that moves with "
                                 f"{row['moves_with']}")
            elif not bl:
                static_reason = "no bone carries this part, so nothing can be animated"
            elif top:
                static_reason = (f"no rotation is animated; the bones translate (`{top[0]}` "
                                 f"{num(top[1]['max_cm'], 3)} cm in `{top[1]['sequence']}`) and a "
                                 "hinge cannot reproduce translation")
                if m and m.get("variable"):
                    static_reason += (f"; the spin itself is driven by `{m['variable']}` (code, "
                                      "not an animation)")
            elif m and m.get("variable"):
                static_reason = (f"no animation moves it; `{row['behaviour']}` is driven by "
                                 f"`{m['variable']}` (code)")
            else:
                static_reason = "no sequence in the base package rotates a bone of this part"
        out.append({
            "id": row["id"], "part": row["part"], "mechanism": row["mechanism"],
            "bones": bl, "pivots": pivots,
            "joint": joint,
            "static_reason": static_reason,
            "behaviour": row["behaviour"],
            "moves_with": row.get("moves_with"),
            "behaviour_channel": (m or {}).get("channel"),
            "variable": (m or {}).get("variable"),
            "proof": (m or {}).get("proof"),
            "carrier_chassis": ((m or {}).get("chassis_list") or [None])[0],
            "hinge": hinge,
            "animation_sequences": got["sequences"],
            "animation_sequence_count": len(got["sequences"]),
            "faces_lod0": (ent or {}).get("faces_lod0"),
            "faces_per_lod": (ent or {}).get("faces_per_lod"),
            "lod_policy": ("one RBM per LOD at the same pivot; the part is cut in every LOD the "
                           "build writes (LOD1..5)" if ent else
                           "not a separate part - geometry stays in the body/pod shell"),
            "damage_type": (hinge or {}).get("damage_type") or dt,
            "damage_type_fleet": (dt_by_behaviour.get(row["behaviour"] or "") or {}).get(
                "fleet", []),
            "damage_type_land": (dt_by_behaviour.get(row["behaviour"] or "") or {}).get(
                "land", []),
            "axis_agrees": (None if not (joint and hinge) else
                            _same_axis(joint["axis_world_jc3"], hinge["axis"])),
            "translation": {b: t for b, t in got["translation"].items() if b in set(bl)},
            "parent": (parts_by_name.get(row["part"]) or {}).get("parent") or "body",
            "verify": row["verify"],
        })

    # pose deltas (G1-12) for the parts whose pose moves them: turret raise, flaps, wheels
    pose_rows = {}
    for d in poses["deltas"]:
        if d.get("moved"):
            pose_rows.setdefault(d["name"], []).append(
                {"pose": "pursuit->battle", "translation_m": d.get("translation_m"),
                 "rotation_deg": d.get("rotation_angle_deg"),
                 "axis_jc3": d.get("rotation_axis_jc3")})
    for r in out:
        r["pose_delta"] = {b: pose_rows[b] for b in r["bones"] if b in pose_rows}
    # a static shell inherits the damage type of the part that moves it (e.g. pod <- hatch)
    for r in out:
        if r["damage_type"] is None:
            same = [x for x in out if x["mechanism"] == r["mechanism"] and x["damage_type"]]
            if same:
                r["damage_type"] = same[0]["damage_type"]
                r["damage_type_inherited_from"] = same[0]["id"]

    doc = {
        # `schema` stays 1: this file is still the `bat_assemble.py --parts` spec (same
        # `parts`/`left_in_body`), and `load_part_spec()` refuses anything else.  The T-12
        # additions live under `rows` and are versioned separately.
        "schema": 1,
        "rows_schema": 2,
        "generator": "Tools/scripts/t12_parts.py",
        "card": "T-12",
        "scope": "B-02 geometry split (unchanged `parts`, `schema` 1) + T-12 behaviour rows "
                 "(`rows_schema` 2)",
        "inputs": {
            "animations": "Research/BatmobileGrab/ANIMATIONS.json (G1-10)",
            "bones": "Research/BatmobileGrab/BONES.json (G1-11)",
            "poses": "Research/BatmobileGrab/POSES.json (G1-12)",
            "keys": KEYS,
            "moving_parts": "Research/JC3Grab/MOVING_PARTS.json (G2-14)",
            "turret": "Research/JC3Grab/TURRET.json (G2-13)",
            "parts_table": "Research/JC3Grab/PARTS_TABLE.jsonl (P0-2)",
            "parts_manifest": "Working/Appearance/build_parts/parts_manifest.json (bat_assemble --parts)",
            "transform": "Tools/scripts/bat_assemble.py pivot_point (scale %.3f, offset %s)"
                         % (scale, [round(x, 6) for x in offset]),
        },
        "pivot_tolerance_m": round(offset_delta + 1e-6, 12),
        "parts": spec["parts"],
        "left_in_body": spec["left_in_body"],
        "rows": out,
    }
    doc["summary"] = summarise(doc)
    return doc


def summarise(d: dict) -> dict:
    rows = d["rows"]
    with_joint = [r for r in rows if r["joint"]]
    with_hinge = [r for r in rows if r["hinge"]]
    return {
        "rows": len(rows),
        "parts": sum(1 for r in rows if r["part"]),
        "static_rows": [r["id"] for r in rows if not r["joint"]],
        "rows_with_joint": len(with_joint),
        "rows_with_hinge": len(with_hinge),
        "sequences_scanned": sum(r["animation_sequence_count"] for r in rows),
        "distinct_sequences": len({s for r in rows for s in r["animation_sequences"]}),
        "spin_rows": [r["id"] for r in with_joint if r["joint"].get("is_spin")],
        "max_rate_deg_s": max((r["joint"]["max_rate_deg_s"] for r in with_joint), default=None),
        "pivot_max_delta_m": max((p["delta_m"] for r in rows for p in r["pivots"].values()),
                                 default=None),
        "pivot_tolerance_m": d.get("pivot_tolerance_m"),
        "damage_types": sorted({r["damage_type"] for r in rows if r["damage_type"]}),
        "behaviours": sorted({r["behaviour"] for r in rows if r["behaviour"]}),
    }


# ---------------------------------------------------------------------------------------------
def num(v, n=2):
    if v is None:
        return "UNKNOWN"
    if isinstance(v, float):
        return f"{v:.{n}f}"
    return str(v)


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def motion_cell(j: dict) -> str:
    """What the joint actually does: a wrapped extent, or a spin's turns and travel."""
    if j.get("is_spin"):
        return (f"{num(j.get('turns'), 2)} turns / {num(j.get('travel_deg'), 1)}° in "
                f"{num(j.get('duration_s'), 2)} s")
    return f"{num(j.get('min_deg'), 3)}…{num(j.get('max_deg'), 3)}°"


def render_md(d: dict) -> str:
    s = d["summary"]
    # the canopy's two statistics, taken from its own row (union span vs per-clip spans)
    p6 = next((r for r in d["rows"] if r["id"] == "P-06"), None) or {}
    p7 = next((r for r in d["rows"] if r["id"] == "P-07"), None) or {}
    p7 = p7.get("joint") or {}
    j6 = p6.get("joint") or {}
    canopy = {
        "cm": max((t["max_cm"] for t in (p6.get("translation") or {}).values()), default=None),
        "cm_seq": (max((p6.get("translation") or {}).items(),
                       key=lambda kv: kv[1]["max_cm"])[1]["sequence"]
                   if p6.get("translation") else None),
        "span": j6.get("span_deg"),
        "spans": [x["span_deg"] for x in (j6.get("per_sequence_spans") or [])],
        "n": len(j6.get("per_sequence_spans") or []),
    }
    L = ["# T-8 parts — geometry cut (B-02) and behaviour rows (T-12)", "",
         "Generated by `Tools/scripts/t12_parts.py`. The geometry half is the cut that",
         "`bat_assemble.py --parts` wrote (`parts_manifest.json`); the behaviour half is T-12:",
         "one row per moving part with its BmAK bone(s), JC3 behaviour, pivot through the one",
         "transform, axis, limits from the animation's extreme frames, rate in deg/s, parent,",
         "LOD policy and damage type. A monotonic multi-turn channel (the Vulcan) is reported as",
         "turns and travel: its ±180°-wrapped extent is one wrap, not a limit.", "",
         "## Summary", "",
         "| fact | value |", "|---|---|",
         f"| rows | **{s['rows']}** ({s['parts']} cut parts + {s['rows'] - s['parts']} items with no part) |",
         f"| rows with an animated joint | {s['rows_with_joint']} |",
         f"| rows with a shipped hinge (axis/limits/damage type) | {s['rows_with_hinge']} |",
         f"| BmAK row-sequence pairs | {s['sequences_scanned']} ({s['distinct_sequences']} distinct clips) |",
         f"| joints that are a continuous spin | {', '.join(s['spin_rows']) or 'none'} |",
         f"| fastest joint | {num(s['max_rate_deg_s'])} deg/s |",
         f"| max pivot disagreement vs `BONES.json` | {num(s['pivot_max_delta_m'], 9)} m |",
         f"| damage types used | {', '.join(f'`{x}`' for x in s['damage_types'])} |",
         f"| internal rows (no joint, reason given) | {', '.join(s['static_rows'])} |",
         "", "## Geometry cut (unchanged, B-02)", "",
         "| part | parent | pivot bone | LOD0 faces | faces per LOD | pivot (m, JC3) |",
         "|---|---|---|---|---|---|"]
    for r in d["rows"]:
        if not r["part"]:
            continue
        pv = r["pivots"].get((r["joint"] or {}).get("bone") or "") or next(
            iter(r["pivots"].values()), None)
        piv = ", ".join(f"{x:.3f}" for x in pv["pivot_jc3_m"]) if pv else "n/a"
        bp = next((x for x in d["parts"] if x["name"] == r["part"]), {})
        L.append(f"| `{r['part']}` | {bp.get('parent')} | `{bp.get('pivot_bone')}` |"
                 f" {r['faces_lod0'] if r['faces_lod0'] is not None else 'n/a'} |"
                 f" {r['faces_per_lod']} | {piv} |")
    L += ["", "## Behaviour rows (T-12)", "",
          "`axis (bone-local)` is the animated bone's own axis; `axis (JC3 space)` is the same "
          "axis through the bone's bind rotation, which is what a JC3 hinge axis can be compared "
          "with. `part bone` gives the part pivot bone's own span/rate when the headline joint is "
          "a child bone.",
          "",
          "| id | part | behaviour | BmAK joint bone | pivot (m) | axis (bone-local) | "
          "axis (JC3 space) | BmAK motion | rate | part bone (own span / rate) | "
          "carrier limits | damage |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        j = r["joint"] or {}
        pv = (r["pivots"].get(j.get("bone")) or r["pivots"].get(j.get("part_pivot_bone"))
              or next(iter(r["pivots"].values()), {}))
        hinge = r["hinge"] or {}
        lim = (motion_cell(j) if j else "static")
        rate = f"{num(j.get('max_rate_deg_s'))} °/s" if j else "—"
        axj = ("[" + ", ".join(num(x, 3) for x in j["axis_world_jc3"]) + "]") if j else "—"
        pbe = j.get("part_bone_extent")
        if not j:
            pb = "—"
        elif j.get("is_pivot_bone"):
            pb = "the joint bone"
        elif pbe:
            pb = (f"`{pbe['bone']}` span {num(pbe['span_deg'], 3)}° / "
                  f"{num(pbe['max_rate_deg_s'])} °/s")
        else:
            pb = "part bone not animated"
        cl = (f"{num(hinge.get('min_deg'), 1)}…{num(hinge.get('max_deg'), 1)}° "
              f"({cell(hinge.get('entity', '')).split('/')[-1][:28]})" if hinge else "no hinge")
        bhv_txt = r["behaviour"] or ("moves with P-07/P-08" if r["joint"] else "static")
        L.append(f"| {r['id']} | `{r['part'] or '—'}` | {bhv_txt} |"
                 f" {('`' + j['bone'] + '`') if j else '—'} |"
                 f" {', '.join(f'{x:.3f}' for x in pv.get('pivot_jc3_m', [])) or 'n/a'} |"
                 f" {j.get('axis_local') if j else '—'} | {axj} | {lim} | {rate} |"
                 f" {pb} | {cl} | `{r['damage_type']}` |")
    L += ["", "## Per-part detail", ""]
    for r in d["rows"]:
        L.append(f"### {r['id']} — `{r['part'] or 'no part'}`"
                 f"{'' if r['behaviour'] else ' (static)'}")
        L.append("")
        L.append(f"- **behaviour**: {r['behaviour'] or 'none - no behaviour of its own'}"
                 f"{' (' + str(r['behaviour_channel']) + ' channel)' if r['behaviour_channel'] else ''}")
        if r["bones"]:
            L.append("- **BmAK bones**: " + ", ".join(f"`{b}`" for b in r["bones"]))
        if r["variable"]:
            L.append(f"- **driving variable**: `{r['variable']}`")
        if r["proof"]:
            L.append(f"- **proven on**: {cell(r['proof'])}")
        if r["hinge"]:
            h = r["hinge"]
            L.append(f"- **shipped hinge**: `{cell(h.get('part'))}` on "
                     f"`{cell(h.get('entity'))}` — axis {h['axis']}, "
                     f"{num(h['min_deg'], 1)}…{num(h['max_deg'], 1)}°, "
                     f"pivot {h.get('pivot')}, `{h.get('class')}`, damage `{h.get('damage_type')}`")
        if r["joint"]:
            j = r["joint"]
            if j.get("is_spin"):
                move = (f"travels **{num(j['travel_deg'], 1)}° = {num(j['turns'], 2)} turns** "
                        f"over {num(j.get('duration_s'), 2)} s at up to "
                        f"{num(j['max_rate_deg_s'])} °/s. The sampled channel's extent "
                        f"({num(j['min_deg'], 3)}…{num(j['max_deg'], 3)}°) is one ±180° wrap, "
                        "not a limit")
            else:
                move = (f"{num(j['min_deg'], 3)}…{num(j['max_deg'], 3)}° at up to "
                        f"{num(j['max_rate_deg_s'])} °/s")
            L.append(f"- **animation**: {r['animation_sequence_count']} sequences "
                     f"({', '.join('`%s`' % x for x in r['animation_sequences'][:6])}"
                     f"{'…' if len(r['animation_sequences']) > 6 else ''}); bone "
                     f"`{j['bone']}` turns about its local {j['axis_local']} "
                     f"({j['axis_jc3']} in JC3 space) and {move}"
                     + ("" if j["is_pivot_bone"] else
                        f"; note the joint bone is not the part pivot (`{j['part_pivot_bone']}`)"))
            if j.get("is_spin") and len(j.get("per_sequence_spans") or []) > 1:
                L.append("- **per-sequence travel**: " + "; ".join(
                    f"`{x['sequence']}` {num(x['travel_deg'], 1)}°"
                    for x in j["per_sequence_spans"]))
            pbe = j.get("part_bone_extent")
            if not j["is_pivot_bone"]:
                if pbe:
                    L.append(f"- **part bone itself** (`{pbe['bone']}`): "
                             f"{num(pbe['min_deg'], 3)}…{num(pbe['max_deg'], 3)}° at up to "
                             f"{num(pbe['max_rate_deg_s'])} °/s - the headline joint above is a "
                             "child bone, so these are the numbers for the part's own pivot")
                else:
                    L.append(f"- **part bone itself** (`{j['part_pivot_bone']}`): not animated; "
                             "the motion above is carried by its child bone")
            others = [c for c in j.get("candidates") or [] if c["bone"] != j["bone"]]
            if others:
                L.append("- **other bones of this part that move**: " + "; ".join(
                    f"`{c['bone']}` {num(c['min_deg'], 3)}…{num(c['max_deg'], 3)}° about "
                    f"{c['axis_local']} at {num(c['max_rate_deg_s'])} °/s" for c in others[:6]))
            if r.get("translation"):
                top = max(r["translation"].items(), key=lambda kv: kv[1]["max_cm"])
                L.append(f"- **translation**: `{top[0]}` moves {num(top[1]['max_cm'], 3)} cm in "
                         f"`{top[1]['sequence']}` (a hinge cannot reproduce translation - B-02)")
            if r["axis_agrees"] is not None:
                L.append(f"- **axis vs the shipped hinge**: "
                         f"{'agrees' if r['axis_agrees'] else 'DISAGREES - the BmAK joint and the ' + str(r['behaviour']) + ' hinge are not the same line, so B-02 must choose which one the part turns about'}")
        else:
            L.append(f"- **stays static**: {r['static_reason']}")
            if r.get("translation"):
                for bone, t in sorted(r["translation"].items(),
                                      key=lambda kv: -kv[1]["max_cm"]):
                    L.append(f"- **translation**: `{bone}` moves {num(t['max_cm'], 3)} cm in "
                             f"`{t['sequence']}` (a hinge cannot reproduce translation - B-02)")
        L.append(f"- **parent**: {r['parent']}; **LOD**: {r['lod_policy']}")
        L.append(f"- **damage type**: `{r['damage_type']}`"
                 f"{' (fleet values for this behaviour: ' + ', '.join('`%s`' % x for x in r['damage_type_fleet']) + ')' if len(r['damage_type_fleet']) > 1 else ''}")
        if r["pose_delta"]:
            one = next(iter(r["pose_delta"].items()))[1][0]
            L.append(f"- **pose delta (G1-12)**: pursuit→battle moves this bone "
                     f"{', '.join(num(x, 4) for x in one['translation_m'])} m / "
                     f"{num(one['rotation_deg'])}° about {one['axis_jc3']}")
        L.append(f"- **verify**: {cell(r['verify'])}")
        L.append("")
    L += ["## What the files do not give (UNKNOWN)", "",
          "1. **No sequence in the base package rotates the turbine or the yoke.** P-05's",
          "   `EngineRotatingPart` and P-13's `SteeringWheel` are driven by a variable",
          "   (`engine_rpm`, `steering_turn`), not by an animation, so their rate is the vehicle's",
          "   rpm / steering rate (code) and stays UNKNOWN here - the shipped `rotating_parts[]`",
          "   row carries `rpm_per_cycle` 20 instead, which is the number a build uses.",
          "2. **Hinge rate.** `vehicle_common.all_hinged_part_properties` carries",
          "   `target_position_variable`, `lod` and `use_target_position_as_angle` but **no rate**",
          "   (G2-14), so a door/turret has no deg/s member on the JC3 side; the animation rate",
          "   below is BmAK's, and how fast JC3 drives the variable is code.",
          "3. **The canopy opens by translation, not by hinge.** The canopy clips move",
          f"   `CockPit_Mesh` {num(canopy['cm'], 3)} cm (max, in `{canopy['cm_seq']}`) and turn "
          f"it {num(canopy['span'], 3)}° "
          f"(union over its {canopy['n']} clips; the per-clip spans are "
          + ", ".join(num(x, 2) for x in canopy["spans"])
          + "); JC3 door parts only rotate about a hinge",
          "   (G2-15), so a Batmobile canopy driven by `Hood` (donor: +X 0..70°) can reproduce the",
          "   rotation but not the lift. Recorded, not resolved (B-02 decision).",
          f"4. **The missile covers have no bone of their own.** The {num(p7['span_deg'], 3)}° lift "
          "is carried by the",
          "   pod bones (`Missiles_L/R_T/B`), whose faces are inside the two pod parts; a separate",
          "   hatch part needs a face-level re-cut in B-02 before `MissileHatch` can move it.",
          "5. **No yoke geometry exists** (G1-19: nothing in the hand box) and no steering-wheel",
          "   bone, so `SteeringWheel` has no part to turn.",
          "", "## Reproduce", "",
          "```",
          "python Tools/scripts/t12_parts.py --write   # regenerate T8_PARTS.md + T8_PARTS.json",
          "python Tools/scripts/t12_parts.py --check   # Done-when gate",
          "python Tools/scripts/t12_parts.py dump rows|parts",
          "```", "",
          "Key frames are read from `E:/Modding/_shared/gamedata/BmAKgrab/anims/keys/` (game data, outside the",
          "repo, R10). `T8_PARTS.json` stays a valid `bat_assemble.py --parts` spec: `parts` is",
          "unchanged, the behaviour rows are added beside it.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------
def invariants(d: dict) -> list[str]:
    bad = []
    s = d["summary"]
    if d.get("schema") != 1 or d.get("rows_schema") != 2:
        bad.append(f"spec schema {d.get('schema')} / rows_schema {d.get('rows_schema')} "
                   "(bat_assemble.load_part_spec reads only `schema` 1)")
    if s["rows"] != len(ROWS):
        bad.append(f"{s['rows']} rows, expected {len(ROWS)}")
    for r in d["rows"]:
        if r["part"] and r["faces_lod0"] is None:
            bad.append(f"{r['id']} part {r['part']} has no geometry entry")
        if r["part"] and not r["pivots"]:
            bad.append(f"{r['id']} has no pivot")
        tol = d.get("pivot_tolerance_m") or 1e-6
        for name, p in r["pivots"].items():
            if p["delta_m"] > tol:
                bad.append(f"{r['id']} pivot {name} disagrees with BONES.json by {p['delta_m']} m "
                           f"(tolerance {tol} m: BONES' own offset delta)")
        if r["joint"] and (r["joint"]["span_deg"] <= 0 or r["joint"]["max_rate_deg_s"] <= 0):
            bad.append(f"{r['id']} joint has no span or no rate")
        if r["joint"] and not r["animation_sequences"]:
            bad.append(f"{r['id']} joint without a sequence")
        if r["joint"]:
            j = r["joint"]
            if j.get("axis_index") is None or not j.get("axis_local") or not j.get("axis_jc3"):
                bad.append(f"{r['id']} joint has no axis")
            if j.get("min_deg") is None or j.get("max_deg") is None or \
                    j["min_deg"] > j["max_deg"]:
                bad.append(f"{r['id']} joint limits are not ordered")
            if j.get("is_spin"):
                if (j.get("turns") or 0) < 1 or (j.get("travel_deg") or 0) <= j["span_deg"]:
                    bad.append(f"{r['id']} is flagged a spin without travel beyond one extent")
                if not j.get("duration_s"):
                    bad.append(f"{r['id']} spin without a clip duration")
        else:
            reason = r.get("static_reason") or ""
            if not reason:
                bad.append(f"{r['id']} is static without a reason")
            elif r.get("translation") and "translat" not in reason.lower():
                bad.append(f"{r['id']} translates but its static reason does not say so")
        if r["behaviour"] is None and r["joint"] and not r.get("moves_with"):
            bad.append(f"{r['id']} moves but has no behaviour and no `moves_with`")
        if not r["verify"]:
            bad.append(f"{r['id']} has no verify cell")
        if not r["damage_type"]:
            bad.append(f"{r['id']} has no damage type")
    for mech in ("turret", "cannon", "Vulcan", "canopy", "missile bays", "fins/air-brakes"):
        if not any(r["mechanism"] == mech for r in d["rows"]):
            bad.append(f"card mechanism {mech} has no row")
    missing_parts = {x["name"] for x in d["parts"]} - {r["part"] for r in d["rows"]}
    if missing_parts:
        bad.append(f"cut parts without a row: {sorted(missing_parts)}")
    return bad


def cmd_write() -> int:
    d = build()
    with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=False, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    try:
        bat_assemble.load_part_spec(SPEC)
    except SystemExit as e:
        print(f"FAIL: bat_assemble.load_part_spec refused the written spec: {e}")
        return 1
    s = d["summary"]
    print(f"T8_PARTS.md/json: {s['rows']} rows ({s['parts']} parts), {s['rows_with_joint']} "
          f"joints, {s['rows_with_hinge']} shipped hinges, {s['sequences_scanned']} sequences, "
          f"fastest {s['max_rate_deg_s']} deg/s, pivot delta {s['pivot_max_delta_m']} m, "
          f"{len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    if not (os.path.exists(SPEC) and os.path.exists(MD)):
        print("FAIL: T8_PARTS.md/json missing - run --write")
        return 1
    have = load_json(SPEC)
    d = build()
    bad = invariants(d)
    if have != d:
        diff = [k for k in sorted(set(have) | set(d)) if have.get(k) != d.get(k)]
        bad.append("T8_PARTS.json stale: " + ",".join(diff))
    md = render_md(d)
    got = open(MD, encoding="utf-8").read()
    if md != got:
        ud = list(difflib.unified_diff(got.splitlines(), md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(ud[2:8]))
    # the delivered file must still be a `bat_assemble.py --parts` spec (the consumer)
    try:
        bat_assemble.load_part_spec(SPEC)
    except SystemExit as e:
        bad.append(f"bat_assemble.load_part_spec refused {SPEC}: {e}")
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    s = d["summary"]
    print(f"PASS: {s['rows']} rows ({s['parts']} cut parts, {s['rows_with_joint']} with an animated "
          f"joint, {s['rows_with_hinge']} with a shipped hinge, spins {s['spin_rows']}) | "
          f"{s['sequences_scanned']} BmAK row-sequence pairs ({s['distinct_sequences']} distinct "
          f"clips) | fastest joint {s['max_rate_deg_s']} deg/s | pivots re-derived through "
          f"bat_assemble (max delta {s['pivot_max_delta_m']} m) | damage types "
          f"{s['damage_types']} | internal rows {s['static_rows']} | json match True, md match True")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"rows": "rows", "parts": "parts"}.get(what)
    if key is None:
        print("one of: rows, parts")
        return 2
    print(json.dumps(d[key], indent=1)[:30000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="rows")
    a = p.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    if a.cmd == "dump":
        return cmd_dump(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
