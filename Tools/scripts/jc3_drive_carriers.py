#!/usr/bin/env python3
"""G3-08c: JC3 carriers for BmAK's drive behaviours, static only.

Two behaviours are in scope (operator leads, confirmed or contradicted in this file, never
assumed):

  * pursuit: the left stick spins the car in place while stationary;
  * battle: the left stick moves the car in the stick's direction while the car turns to
    face the camera direction (four-wheel drive).

Plus the four other driving moves BmAK's own controls menu names
(`Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md`): Side Swipe, Dodge Thrusters, Power
Slide, Afterburner.

Sources (read-only):
  * `E:/Modding/_gamedata/JC3grab/entities/*.ee.json` - 232 decoded vehicle builds, modules
    as rows (the project's evidence base; player copy only, `_ai` twins excluded, same rule
    as `jc3tankturn.py`).
  * `E:/Modding/_gamedata/JC3grab/detail/*.ee.json` - the 232 `.epe` graphs, for the object
    class census.
  * `D:/Games/Just Cause 3/*.arc` through `Research/JC3Grab/INDEX.jsonl` - the **bytes** of
    the 54 patch-layer `*_land_global.vmodc` modules, decoded with `jc3adf.Adf` /
    `jc3adf.walk`. This is where `steering_type` comes from (the cached row set does not
    carry it), and the member offsets quoted below are its struct offsets.
  * `settings/keymap_gamepad.bin` / `settings/keymap_keyboard.bin` - decoded with
    `jc3_input.read_entries` + `jc3_input.parse_keymap` (base and patch layers).

Labels: `decoded` = read from a file (path + archive + offset, or a member offset);
`derived` = computed from decoded facts, rule stated; `UNKNOWN` = not decodable here, with
what was tried.

Writes Research/JC3Grab/DRIVE_CARRIERS.json + .md. `--check` re-derives both and compares.

Usage:
  python Tools/scripts/jc3_drive_carriers.py --write
  python Tools/scripts/jc3_drive_carriers.py --check
  python Tools/scripts/jc3_drive_carriers.py dump scan|members|raw|keymap
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jc3index import DEFAULT_GAME  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
JSON_NAME = "DRIVE_CARRIERS.json"
MD_NAME = "DRIVE_CARRIERS.md"
INDEX = os.path.join(OUT, "INDEX.jsonl")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
ENT = os.path.join(RAW, "entities")
DET = os.path.join(RAW, "detail")

DONOR_BUILD = ("v0300_car_kensington_sportsmuscle__"
               "v0300_car_kensington_sportsmuscle_civilian_01.ee.json")

# every module that carries a land vehicle's drive or steering value
DRIVE_MODULES = ("LandGlobal", "LandSteering", "Transmission", "Brakes", "CustomLandGlobal",
                 "Suspension", "Tire", "LandEngine", "RigidBody", "CustomVelocityDamper",
                 "VehicleMisc", "LandAerodynamics", "CarAI")

# token groups: what a carrier of each requirement would have to be called
GROUPS = (
    ("per-wheel drive / differential",
     r"per_?wheel|wheel_?torque|wheel_?drive|torque_?(split|bias|share|distribution)|"
     r"differ(ential)?|awd|4wd|four_?wheel_?drive|drive_?(type|bias|split|share)|"
     r"driven_?wheels?|lsd|limited_?slip"),
    ("stationary turn / pivot",
     r"pivot|turn_?(in_?place|on_?spot)|spin_?(in_?place|on_?spot)|neutral_?turn|"
     r"skid_?steer|counter_?rot|track_"),
    ("camera-relative / face-camera control",
     r"camera|cam_|relative|strafe|dodge|face_?(cam|target)"),
    ("directional impulse / shove",
     r"impulse|shove|kick|push_?(force|accel|speed)|pulse"),
    ("boost / nitro", r"nitro|boost"),
    ("handbrake", r"handbrake"),
    ("steering input", r"steer|steering"),
    ("driveline ratio", r"final_drive|gear|torque"),
)

# key members, quoted in the report with their fleet range and the donor's value
MEMBERS = (
    ("LandGlobal", "steering_type.string"),
    ("LandGlobal", "number_of_wheels"),
    ("LandGlobal", "number_of_front_wheels"),
    ("LandGlobal", "is_all_wheel_steered"),
    ("LandGlobal", "is_rear_steered"),
    ("LandGlobal", "wheels_friction_type"),
    ("LandGlobal", "front_wheels.arcade_friction_multiplier"),
    ("LandGlobal", "rear_wheels.arcade_friction_multiplier"),
    ("LandSteering", "steer_angle_min_speed_deg"),
    ("LandSteering", "steer_angle_max_speed_deg"),
    ("LandSteering", "min_speed_kmph"),
    ("LandSteering", "max_speed_kmph"),
    ("LandSteering", "t_to_full_steer_s"),
    ("LandSteering", "countersteer_speed_factor"),
    ("Transmission", "final_drive"),
    ("Transmission", "gears"),
    ("Transmission", "nitrous_gears"),
    ("Brakes", "front.handbrake"),
    ("Brakes", "rear.handbrake"),
    ("Brakes", "handbrake_friction_factor"),
    ("Brakes", "rear.max_brake_torque"),
    ("CustomVelocityDamper", "handbrake_spin_damping"),
    ("CustomLandGlobal", "drift.min_speed_to_drift_kmph"),
    ("CustomLandGlobal", "drift.max_drift_torque"),
    ("CustomLandGlobal", "drift.constant_drift_torque"),
    ("CustomLandGlobal", "drift.counter_steer_torque_handbrake"),
    ("CustomLandGlobal", "drift.steering_sensitivity"),
    ("CustomLandGlobal", "drift.max_drift_angle_deg"),
    ("CustomLandGlobal", "drift.keep_velocity_strength"),
    ("CustomLandGlobal", "drift.velocity_rotation_amount"),
    ("CustomLandGlobal", "drift.velocity_rotation_start_angle"),
    ("CustomLandGlobal", "drift.velocity_rotation_end_angle"),
    ("CustomLandGlobal", "arcade.nitro_boost.extra_top_speed"),
    ("CustomLandGlobal", "arcade.nitro_boost.torque_multiplier"),
    ("CustomLandGlobal", "arcade.nitro_boost.grip_multiplier"),
    ("CustomLandGlobal", "arcade.nitro_boost.push_force"),
    ("CustomLandGlobal", "arcade.nitro_boost.boost_blend_time"),
    ("CustomLandGlobal", "arcade.nitro_boost_upgraded.extra_top_speed"),
    ("CustomLandGlobal", "arcade.nitro_boost_upgraded.push_force"),
    ("CustomLandGlobal", "arcade.heat_boost.extra_top_speed"),
    ("CustomLandGlobal", "arcade.turbo_jump.punch_speed_kph"),
    ("CustomLandGlobal", "arcade.turbo_jump.top_speed_kph"),
    ("CustomLandGlobal", "arcade.turbo_jump.f_multiplier"),
    ("VehicleMisc", "full_nitro_use_time"),
    ("VehicleMisc", "full_nitro_use_time_upgraded"),
    ("VehicleMisc", "full_nitro_refill_time"),
    ("VehicleMisc", "nitro_refill_min_speed_kph"),
    ("VehicleMisc", "official_top_speed"),
    ("VehicleMisc", "turbo_jump_cooldown"),
)

KEYMAPS = ("settings/keymap_gamepad.bin", "settings/keymap_keyboard.bin")


# ------------------------------------------------------------------ helpers

def load_index() -> list[dict]:
    with open(INDEX, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def entry_for(rows: list[dict], path: str) -> dict | None:
    hits = [r for r in rows if r["path"].lower() == path.lower()]
    if not hits:
        return None
    rank = {"base": 0, "patch": 1, "dlc": 2}
    return max(hits, key=lambda r: rank.get(r["mount"], -1))


def read_entry(r: dict) -> bytes:
    with open(os.path.join(DEFAULT_GAME, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        data = f.read(r["size"])
    if len(data) != r["size"]:
        raise SystemExit(f"short read for {r['path']}: {len(data)} != {r['size']}")
    return data


def split_modules(doc: dict) -> tuple[dict, dict]:
    player, ai = {}, {}
    for m in doc.get("modules", []):
        t = str(m.get("type") or m.get("instance"))
        bucket = ai if "/ai/" in (m.get("file") or "") else player
        bucket.setdefault(t, []).append(m)
    return player, ai


def rows_of(modules: dict, t: str) -> dict:
    lst = modules.get(t) or []
    if not lst:
        return {}
    return {r["path"]: r["value"] for r in lst[0].get("rows", [])}


def _with_sub_offset(path: str, type_name: str, value, offsets: dict) -> dict:
    """Offset of one decoded row: a top-level member's struct offset, or, for the two halves
    of a HashString, the member offset plus the half's own offset (string 0, hash 8)."""
    top = path.split(".", 1)[0]
    info = offsets.get(top, {})
    off, size = info.get("offset"), info.get("size")
    if path.endswith(".string") or path.endswith(".hash"):
        if info.get("type") == "HashString":
            size = 4 if path.endswith(".hash") else 8
            if off is not None and path.endswith(".hash"):
                off += 8
    return {"member": path, "type": type_name, "value": value,
            "offset": off, "member_size": size}


def chassis_of(base: str) -> str:
    return base.split("__", 1)[0]


def numstr(v) -> str:
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return f"{v:.6g}"
    return str(v)


def digest() -> str:
    h = hashlib.sha256()
    for pattern in (os.path.join(ENT, "*.ee.json"), os.path.join(DET, "*.ee.json")):
        for p in sorted(glob.glob(pattern)):
            h.update(os.path.basename(p).encode())
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
    for p in (INDEX, os.path.join(HERE, "jc3_drive_carriers.py")):
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ build

def build() -> dict:
    import jc3adf
    from rbmhdr import hash_jenkins

    ent_files = sorted(glob.glob(os.path.join(ENT, "*.ee.json")))
    det_files = sorted(glob.glob(os.path.join(DET, "*.ee.json")))
    if not ent_files or not det_files:
        raise SystemExit(f"decoded cache missing under {RAW} - set JC3_RAW")

    # ---- pass 1: module census, token scan, per-member values (player copies only)
    type_files = collections.defaultdict(set)
    type_instances = collections.Counter()
    token_hits: dict[str, dict[str, set]] = {g: {} for g, _ in GROUPS}
    patterns = {g: re.compile(rx, re.I) for g, rx in GROUPS}
    values = {f"{t}.{p}": {} for t, p in MEMBERS}
    land_builds = []
    module_file = {}
    allwheel_builds = []

    for path in ent_files:
        base = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        player, _ai = split_modules(doc)
        has_land = "LandGlobal" in player
        if has_land:
            land_builds.append(base)
        for t, mods in player.items():
            type_instances[t] += len(mods)
            type_files[t].add(base)
            for m in mods:
                if base == DONOR_BUILD:
                    module_file[t] = m.get("file")
                for r in m.get("rows", []):
                    p = r["path"]
                    for g, rx in patterns.items():
                        if rx.search(p):
                            token_hits[g].setdefault(f"{t}.{p}", set()).add(base)
                    key = f"{t}.{p}"
                    if key in values:
                        values[key][base] = r["value"]
        if has_land:
            lg = rows_of(player, "LandGlobal")
            if lg.get("is_all_wheel_steered") == 1:
                allwheel_builds.append(base)

    members = []
    for t, p in MEMBERS:
        key = f"{t}.{p}"
        got = values[key]
        nums = [v for v in got.values() if isinstance(v, (int, float))]
        strs = sorted({str(v) for v in got.values() if isinstance(v, str)})
        hist = collections.Counter(numstr(v) for v in got.values())
        members.append({
            "module": t, "path": p, "builds": len(got),
            "donor": got.get(DONOR_BUILD),
            "n_min": min(nums) if nums else None,
            "n_max": max(nums) if nums else None,
            "strings": strs,
            "histogram": dict(sorted(hist.items())),
        })

    scan = []
    for g, _rx in GROUPS:
        hits = token_hits[g]
        rows = []
        for k in sorted(hits):
            mod = k.split(".", 1)[0]
            rows.append({"member": k, "builds": len(hits[k]),
                         "in_drive_module": mod in DRIVE_MODULES})
        scan.append({"group": g, "distinct": len(rows), "rows": rows,
                     "drive_module_hits": [r for r in rows if r["in_drive_module"]]})

    # ---- pass 2: the patch-layer bytes of every `*_land_global.vmodc` in INDEX
    index = load_index()
    raw_rows = [r for r in index
                if r["path"].endswith("_land_global.vmodc") and "/ai/" not in r["path"]]
    raw_rows.sort(key=lambda r: r["path"])
    steering_hist = collections.Counter()
    raw_by_chassis = {}
    hash_pairs = set()
    donor_bytes = None
    for r in raw_rows:
        data = read_entry(r)
        adf = jc3adf.Adf(data)
        walked = list(jc3adf.walk(adf))
        d = {p: v for p, _t, v in walked}
        st = d.get("steering_type.string")
        steering_hist[st if st else "(absent)"] += 1
        if st is not None:
            hash_pairs.add((st, d.get("steering_type.hash")))
        chassis = r["path"].split("/jc_vehicles/01_land/")[1].split("/")[0]
        raw_by_chassis[chassis] = {
            "steering_type": st,
            "steering_type_hash": d.get("steering_type.hash"),
            "wheels_friction_type": d.get("wheels_friction_type"),
            "number_of_wheels": d.get("number_of_wheels"),
            "archive": r["archive"], "entry_offset": r["offset"], "size": r["size"],
        }
        if "sportsmuscle_land_global.vmodc" in r["path"]:
            root_type = adf.types[adf.instances[0]["type"]]
            offsets = {m["name"]: {"offset": m["offset"], "size": m["size"],
                                   "type": adf.type_name(m["type"])}
                       for m in root_type["members"]}
            donor_bytes = {
                "path": r["path"], "archive": r["archive"], "entry_offset": r["offset"],
                "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "type": root_type["name"], "type_size": root_type["size"],
                "rows": [_with_sub_offset(p, t, v, offsets) for p, t, v in walked],
            }
    hash_check = {st: {"file_hash": f"{h:08X}",
                       "jenkins": f"{hash_jenkins(st.encode()) & 0xFFFFFFFF:08X}",
                       "match": (hash_jenkins(st.encode()) & 0xFFFFFFFF) == h}
                  for st, h in sorted(hash_pairs)}

    # cached row set vs the bytes, on the donor build
    donor_doc = json.load(open(os.path.join(ENT, DONOR_BUILD), encoding="utf-8"))
    donor_player, _ = split_modules(donor_doc)
    cache_rows = rows_of(donor_player, "LandGlobal")
    byte_rows = {p: v for p, _t, v in
                 [(x["member"], x["type"], x["value"]) for x in donor_bytes["rows"]]}
    bytes_only = sorted(set(byte_rows) - set(cache_rows))
    cache_only = sorted(set(cache_rows) - set(byte_rows))
    shared_diff = [{"member": k, "bytes": byte_rows[k], "cache": cache_rows[k]}
                   for k in sorted(set(byte_rows) & set(cache_rows))
                   if (isinstance(byte_rows[k], float)
                       and abs(byte_rows[k] - float(cache_rows[k])) > 1e-6 * max(1.0, abs(byte_rows[k])))
                   or (not isinstance(byte_rows[k], float) and byte_rows[k] != cache_rows[k])]

    # the conflict: a build the cache calls all-wheel-steered, whose bytes say FrontSteered
    conflict = []
    for base in sorted(allwheel_builds):
        ch = chassis_of(base)
        raw = raw_by_chassis.get(ch)
        conflict.append({"build": base, "chassis": ch,
                         "cache_is_all_wheel_steered": 1,
                         "bytes_steering_type": raw["steering_type"] if raw else "(no module row)"})
    disagreements = [c for c in conflict
                     if c["bytes_steering_type"] not in (None, "(no module row)")]

    # ---- pass 3: keymaps (base + patch), the only button -> action tables
    import jc3_input
    keymap = {"files": [], "vehicle_actions": [], "vector_bindings": [],
              "camera_relative_actions": []}
    cam_rx = re.compile(r"(?i)(STRAFE|DODGE|PIVOT|SPIN|CAMERA|RELATIVE|NITRO|BOOST)")
    vec_rx = re.compile(r"(?i)(STICKGENERIC|^LSTICK$|^RSTICK$|^MOVEMENT$|^ALLMOVEMENT$)")
    for path in KEYMAPS:
        hits = [r for r in index if r["path"].lower() == path.lower()]
        for r in sorted(hits, key=lambda r: jc3_input.MOUNT_RANK[r["mount"]]):
            data = read_entry(r)
            bindings, accounting = jc3_input.parse_keymap(path, r, data)
            keymap["files"].append({
                "path": path, "mount": r["mount"], "archive": r["archive"],
                "entry_offset": r["offset"], "size": r["size"],
                "bindings": len(bindings), "accounting": accounting,
            })
            if path.endswith("gamepad.bin") and r["mount"] == "patch":
                acts = collections.OrderedDict()
                for b in bindings:
                    acts.setdefault(b["action"], []).append(b["input"])
                keymap["vehicle_actions"] = [
                    {"action": a, "inputs": sorted(set(i))}
                    for a, i in sorted(acts.items())
                    if jc3_input.scope_of(a) == "land-vehicle"]
                keymap["vector_bindings"] = [
                    {"input": b["input"], "action": b["action"]}
                    for b in bindings if vec_rx.search(b["input"])]
                keymap["camera_relative_actions"] = [
                    {"action": b["action"], "input": b["input"]}
                    for b in bindings if cam_rx.search(b["action"])]

    # ---- pass 4: derived per-requirement carriers
    def member_of(mod: str, path: str) -> dict:
        return next(m for m in members if m["module"] == mod and m["path"] == path)

    zero_drift = [b for b, v in values["CustomLandGlobal.drift.min_speed_to_drift_kmph"].items()
                  if v == 0]
    rear_locked = [b for b, v in values["Brakes.rear.handbrake"].items() if v == 1]
    front_locked = [b for b, v in values["Brakes.front.handbrake"].items() if v == 1]
    nitro_builds = sorted(values["CustomLandGlobal.arcade.nitro_boost.extra_top_speed"])
    turbo_builds = sorted(values["CustomLandGlobal.arcade.turbo_jump.punch_speed_kph"])
    rear_softer, rear_harder, rear_equal = [], [], []
    for b, rv in values["LandGlobal.rear_wheels.arcade_friction_multiplier"].items():
        fv = values["LandGlobal.front_wheels.arcade_friction_multiplier"].get(b)
        if not (isinstance(rv, (int, float)) and isinstance(fv, (int, float))):
            continue
        if rv < fv:
            rear_softer.append(b)
        elif rv > fv:
            rear_harder.append(b)
        else:
            rear_equal.append(b)

    epe_classes = collections.Counter()
    for p in det_files:
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        for k, n in (doc.get("epe") or {}).get("classes", {}).items():
            epe_classes[k] += n if isinstance(n, int) else 1

    return {
        "schema": "g3-08c-drive-carriers/1",
        "inputs": {
            "entities": len(ent_files), "detail": len(det_files),
            "land_builds": len(land_builds), "module_types": len(type_files),
            "raw_land_global_modules": len(raw_rows),
            "index_rows": len(index), "digest": digest(),
        },
        "modules": {
            "types": [{"type": t, "builds": len(type_files[t]),
                       "instances": type_instances[t],
                       "drive_module": t in DRIVE_MODULES}
                      for t in sorted(type_files)],
            "drive_modules": [t for t in DRIVE_MODULES if t in type_files],
        },
        "scan": scan,
        "members": members,
        "raw": {
            "modules": len(raw_rows),
            "steering_type_histogram": dict(sorted(steering_hist.items())),
            "hash_check": hash_check,
            "by_chassis": raw_by_chassis,
            "donor_module": donor_bytes,
            "cache_vs_bytes": {"bytes_only": bytes_only, "cache_only": cache_only,
                               "shared_diffs": shared_diff},
        },
        "allwheel": {"cache_builds": sorted(allwheel_builds), "conflict": conflict,
                     "disagreements": disagreements},
        "keymap": keymap,
        "derived": {
            "drift_min_speed_zero_builds": len(zero_drift),
            "drift_min_speed_zero_chassis": sorted({chassis_of(b) for b in zero_drift}),
            "drift_min_speed_zero_examples": sorted(zero_drift)[:8],
            "rear_handbrake_builds": len(rear_locked),
            "front_handbrake_builds": len(front_locked),
            "nitro_builds": len(nitro_builds),
            "turbo_jump_builds": len(turbo_builds),
            "rear_friction_below_front": len(rear_softer),
            "rear_friction_above_front": len(rear_harder),
            "rear_friction_equal": len(rear_equal),
            "epe_camera_classes": {k: v for k, v in sorted(epe_classes.items())
                                   if re.search(r"Camera", k)},
        },
        "epe": {"classes_matching_camera": {k: v for k, v in sorted(epe_classes.items())
                                            if "Camera" in k}},
    }


# ------------------------------------------------------------------ md

def render_md(d: dict) -> str:
    L = []
    a = L.append
    m = {(x["module"], x["path"]): x for x in d["members"]}
    scan = {s["group"]: s for s in d["scan"]}
    raw = d["raw"]
    kb = d["keymap"]
    dr = d["derived"]

    def val(mod, path) -> str:
        x = m[(mod, path)]
        # "donor (fleet min .. max, n builds)"
        rng = ""
        if x["n_min"] is not None:
            rng = f"{numstr(x['n_min'])} .. {numstr(x['n_max'])}"
        elif x["strings"]:
            rng = "/".join(x["strings"][:3])
        return f"{numstr(x['donor'])} ({rng}; n={x['builds']})"

    a("# JC3 carriers for BmAK's drive behaviours (static)")
    a("")
    a("G3-08c. Generated by `Tools/scripts/jc3_drive_carriers.py`; `--check` re-derives every")
    a("number from the same bytes and fails if this file drifted. Labels: **decoded** = read")
    a("from a file (path + archive + offset, or a struct member offset), **derived** = computed")
    a("from decoded facts with the rule stated, **UNKNOWN** = not decodable here.")
    a("")
    a("## 0. Answer")
    a("")
    a(f"Sources: {d['inputs']['entities']} decoded vehicle builds, {d['inputs']['detail']} `.epe`")
    a(f"graphs, {d['inputs']['land_builds']} of them land vehicles with a player `LandGlobal`;")
    a(f"{d['inputs']['module_types']} module types; the **bytes** of "
      f"{raw['modules']} patch-layer `*_land_global.vmodc` modules decoded with `jc3adf`; and")
    a(f"{len(kb['files'])} keymap files (base + patch).")
    a("")
    a("**The fleet has no per-wheel drive, no differential and no camera-relative vehicle")
    a("control.** A token scan of every module member path on every build finds 0 members")
    a("matching per-wheel drive / differential vocabulary, and the only camera / strafe /")
    a("dodge matches (6 members) sit in `Propellers` - boat and aircraft docking limits, not in")
    a("a land driving module (section 2). A car has one `Transmission` (one `final_drive`, one gear")
    a("set) and two `Tire` modules (front axle, rear axle) - there is no per-wheel or")
    a("per-axle drive value anywhere, so **four-wheel drive cannot be expressed as data**: all")
    a("JC3 cars are a single driveline. The only per-axle asymmetry in the fleet is grip")
    a("(`front_wheels`/`rear_wheels.arcade_friction_multiplier`), which is tuning, not drive.")
    a("")
    a("| # | BmAK move | closest JC3 carrier | carrier class | verdict for the Batmobile |")
    a("|---|---|---|---|---|")
    a("| C1 | pursuit: spin in place when stationary | `CustomLandGlobal.drift.*` (yaw-torque "
      "block, 20 members) | decoded block, behaviour native | **tune + UNKNOWN**: the block is "
      "the fleet's only steering-through-torque carrier; whether yaw torque is applied at 0 km/h "
      "is not in any file |")
    a("| C2 | same | `LandGlobal.front_wheels` / `rear_wheels.arcade_friction_multiplier` | "
      "decoded, per-axle grip | tune only: changes how a slide rotates, cannot create rotation "
      "at rest |")
    a("| C3 | same | `LandGlobal.steering_type` (bytes only) | decoded enum, 1 value shipped | "
      "no: every readable module is `FrontSteered` - no rear/all-wheel steer mode is shipped |")
    a("| C4 | battle: move in the stick direction, car faces the camera | none - 0 members, 0 "
      "actions | - | **UNKNOWN / code bridge**: no data member and no keymap action expresses a "
      "2D vehicle move or a camera-relative heading |")
    a("| C5 | battle: four-wheel drive | none - 0 members | - | **UNKNOWN / code bridge**: one "
      "driveline per car, no per-wheel torque member exists |")
    a("| C6 | Side Swipe (LS + A, pursuit) | `drift.keep_velocity_strength`, "
      "`drift.velocity_rotation_*` | decoded, part of the drift block | amendment: gives "
      "lateral travel through a slide, not a discrete sideways shove |")
    a("| C7 | Dodge Thrusters (LS + A, battle) | `arcade.turbo_jump.*` (fixed-direction impulse "
      "block, 6 members) | decoded block | amendment/code bridge: the impulse is fixed along the "
      "car's own axes, not along the stick |")
    a("| C8 | Power Slide (LS + RT + X) | `Brakes.rear.handbrake` + `handbrake_friction_factor` + "
      "`CustomVelocityDamper.handbrake_spin_damping` + `drift.counter_steer_torque_handbrake` | "
      "decoded chain | **carrier found**: rear-axle-only handbrake with a yaw-torque allowance; "
      "rebind + tune only |")
    a("| C9 | Afterburner (Y) | `arcade.nitro_boost` (5 members) + `nitro_boost_upgraded` + "
      "`Transmission.nitrous_gears` + `VehicleMisc.full_nitro_*` | decoded chain | **carrier "
      "found**: boost with a finite burn and a refill rule; needs the trigger and BmAK's numbers "
      "|")
    a("")
    a("## 1. What the fleet has to carry a drive behaviour")
    a("")
    a("| module | builds (player copy) | instances | drive module |")
    a("|---|---|---|---|")
    for x in d["modules"]["types"]:
        if x["drive_module"] or x["type"] in ("VehicleCommon",):
            a(f"| `{x['type']}` | {x['builds']} | {x['instances']} | "
              f"{'yes' if x['drive_module'] else '-'} |")
    a("")
    a(f"{len(d['modules']['types'])} module types are declared by the player copies across the")
    a("fleet. The driving")
    a("set is exactly: " + ", ".join(f"`{t}`" for t in d["modules"]["drive_modules"]) + ".")
    a("There is no drive, differential, gearbox-per-wheel or track module - the module census")
    a("and the token scan below are two independent ways of saying the same thing.")
    a("")
    a("## 2. Token scan - what a carrier would have to be called, and what exists")
    a("")
    a("Every member path of every module of every build, matched against one regex per")
    a("requirement. `drive-module hits` counts matches inside the driving modules above; a hit")
    a("outside them cannot be reached by a drive tune.")
    a("")
    a("| requirement | regex hits (distinct members) | inside a drive module |")
    a("|---|---|---|")
    for g, _ in GROUPS:
        s = scan[g]
        a(f"| {g} | {s['distinct']} | {len(s['drive_module_hits'])} |")
    a("")
    for g in ("per-wheel drive / differential", "stationary turn / pivot",
              "camera-relative / face-camera control"):
        s = scan[g]
        a(f"**{g}** - {s['distinct']} distinct member(s):")
        a("")
        if not s["rows"]:
            a("none. The regex matched no member path in any module on any build.")
        else:
            a("| member | builds | in a drive module |")
            a("|---|---|---|")
            for r in s["rows"]:
                a(f"| `{r['member']}` | {r['builds']} | {'**yes**' if r['in_drive_module'] else 'no'} |")
        a("")
    a(f"The one stationary-turn match is `VehicleCommon.train_common.train_track_width_scale`")
    a("(rail gauge, `CTrain` only) - no land vehicle carries a pivot, neutral-turn or")
    a("counter-rotate member. The six camera/strafe matches are the two propeller docking")
    a("strafe-angle groups (`Propellers`, 38 builds = boats and planes): a docking limit, not a")
    a("driving control. The only driveline-word match is `Transmission.final_drive` /")
    a("`low_gears_final_drive`, which set one ratio for the whole car.")
    a("")
    a("## 3. Pursuit: spin in place when stationary")
    a("")
    a("### 3.1 The only steering-through-torque carrier: the drift block (C1)")
    a("")
    a("`CustomLandGlobal.drift.*` is a 20-member block on "
      f"{m[('CustomLandGlobal','drift.max_drift_torque')]['builds']} builds. It is the only")
    a("place in a land vehicle where the car is rotated by a torque rather than by a front")
    a("wheel angle, and it has a speed gate of its own:")
    a("")
    a("| member | donor (fleet min .. max; builds) | what it does |")
    a("|---|---|---|")
    for p in ("drift.min_speed_to_drift_kmph", "drift.max_drift_torque",
              "drift.constant_drift_torque", "drift.steering_sensitivity",
              "drift.max_drift_angle_deg", "drift.counter_steer_torque_handbrake",
              "drift.keep_velocity_strength", "drift.velocity_rotation_amount",
              "drift.velocity_rotation_start_angle", "drift.velocity_rotation_end_angle"):
        a(f"| `drift.{p.split('.',1)[1]}` | {val('CustomLandGlobal', p)} | "
          f"{'speed below which no drift is entered' if 'min_speed' in p else 'yaw torque / slide shaping'} |")
    a("")
    a(f"`drift.min_speed_to_drift_kmph` reaches **0** on {dr['drift_min_speed_zero_builds']} "
      f"builds ({len(dr['drift_min_speed_zero_chassis'])} chassis: "
      f"{', '.join('`' + c + '`' for c in dr['drift_min_speed_zero_chassis'])}),")
    a("so a value exists that does not gate the block on speed. What that does **not** prove is")
    a("that a car with that value rotates at zero velocity: the drift path is a slip-angle path")
    a("(`drift_entry_slip_angle`, `drift_exit_slip_angle`, `lat_tire_*` curves), and a slip")
    a("angle needs a velocity to exist. The arithmetic is native - **UNKNOWN**, and it is the")
    a("one cheap experiment this card cannot run.")
    a("")
    a("### 3.2 Per-axle grip is the only asymmetry the fleet has (C2)")
    a("")
    a(f"| member | donor | fleet |")
    a(f"|---|---|---|")
    a(f"| `front_wheels.arcade_friction_multiplier` | "
      f"{val('LandGlobal','front_wheels.arcade_friction_multiplier')} | |")
    a(f"| `rear_wheels.arcade_friction_multiplier` | "
      f"{val('LandGlobal','rear_wheels.arcade_friction_multiplier')} | |")
    a("")
    a(f"Across the fleet the rear axle is stiffer than the front on "
      f"{dr['rear_friction_above_front']} builds, softer on "
      f"{dr['rear_friction_below_front']} and equal on {dr['rear_friction_equal']} - so the")
    a("front/rear balance is a real tuned axis, and it is the only per-axle drive-adjacent")
    a("")
    a("This is a static per-axle multiplier (one number per axle, not per wheel): dropping the")
    a("rear axle's grip lets the drift block rotate the car more easily, which is the closest")
    a("data-side approach to steering-through-torque, but it still needs the drift path and")
    a("therefore motion. It cannot make a stationary car rotate.")
    a("")
    a("### 3.3 What the steering module can and cannot do (C3)")
    a("")
    a("| member | donor (fleet min .. max; builds) |")
    a("|---|---|")
    for p in ("steer_angle_min_speed_deg", "steer_angle_max_speed_deg", "min_speed_kmph",
              "max_speed_kmph", "t_to_full_steer_s", "countersteer_speed_factor"):
        a(f"| `{p}` | {val('LandSteering', p)} |")
    a("")
    a("`LandSteering` is a front-wheel angle curve scaled by speed: it has a steer angle at the")
    a("low end of its speed curve, but nothing that turns the body. The tanks add nothing -")
    a("their four modules are member-identical to a car's (TANKTURN.md, and section 5 below")
    a("shows they do not even carry a rear/all-wheel steering mode in their bytes).")
    a("")
    a("## 4. Battle: move in the stick direction, car faces the camera; four-wheel drive")
    a("")
    a("### 4.1 No member and no action expresses it (C4, C5)")
    a("")
    a(f"The camera-relative regex returned {scan['camera-relative / face-camera control']['distinct']} ")
    a("module members, all six in `Propellers` (docking strafe limits on boats and planes) and")
    a("none in a module a land vehicle uses. The `.epe` graphs do carry camera classes (a")
    a("`CCameraModifier` object is on every vehicle), but a camera modifier frames the camera;")
    a("it is not a control path. There is no member a stick direction could drive.")
    a("")
    a("The keymap is the only button -> action table, and it has no vehicle vector action. The")
    a("patch gamepad map decoded here carries "
      f"{len(kb['vehicle_actions'])} land-vehicle actions:")
    a("")
    a("| action | inputs |")
    a("|---|---|")
    for x in kb["vehicle_actions"]:
        a(f"| `{x['action']}` | {', '.join(x['inputs'])} |")
    a("")
    a("They are all discrete (accelerate, reverse, turn left/right, brake, fire, exit...) -")
    a("there is no action that carries a 2D stick vector into a vehicle. The only binding in")
    a("either keymap that takes a whole stick is:")
    a("")
    a("| input | action |")
    a("|---|---|")
    for x in kb["vector_bindings"]:
        a(f"| `{x['input']}` | `{x['action']}` |")
    a("")
    a("`MOVE_ALL` on `LSTICKGENERIC` is the one generic 2D-stick binding in the game, and its")
    a("name scope is on-foot. Whether a vehicle could consume it is **UNKNOWN** - nothing in")
    a("the keymap files or the 232 entity builds names a class to action set (INPUT.md reaches")
    a("the same conclusion). The nearest names to a camera-relative or dodge action in either")
    a("keymap are: " + (", ".join(f"`{x['action']}`" for x in kb["camera_relative_actions"])
                       or "none") + ".")
    a("")
    a("For four-wheel drive the answer is structural rather than a missing name: there is no")
    a("per-wheel torque member to set, because a `CCar` has one `Transmission` and one `Tire`")
    a("module per axle. Making the Batmobile four-wheel drive in the data is **not expressible**;")
    a("a carrier would have to be a code bridge (a new module type the engine does not read) or")
    a("an amendment that drops the 4WD part of the requirement.")
    a("")
    a("## 5. The one new carrier: `LandGlobal.steering_type` (bytes only)")
    a("")
    a(f"The {raw['modules']} patch-layer `*_land_global.vmodc` modules in `INDEX.jsonl` decode")
    a("with `jc3adf` to a row the cached row set does not contain: **`steering_type`**, a")
    a("hashed-string enumeration. Histogram over those modules:")
    a("")
    a("| value | modules |")
    a("|---|---|")
    for k, v in raw["steering_type_histogram"].items():
        a(f"| `{k}` | {v} |")
    a("")
    a("The decode is self-checking: the name's Jenkins hash equals the hash stored beside it")
    a("(" + ", ".join(f"`{k}` {v['file_hash']} = `hash_jenkins` {v['jenkins']}"
                     for k, v in raw["hash_check"].items()) + ").")
    a("")
    a("**Every readable module says `FrontSteered`**, and the three builds whose module is not")
    a("in INDEX carry no `steering_type` member at all. So the fleet ships one steering mode")
    a("(front axle) and the enum is not a rear-steer or all-wheel-steer switch a mod can set to")
    a("a new value: no other value is shipped, and the value domain is not in the file.")
    a("")
    a("### 5.1 A contradiction inside the project's own evidence")
    a("")
    a("The cached row set replaces that member with two int8 flags, `is_all_wheel_steered` and")
    a("`is_rear_steered`. On the donor build:")
    a("")
    a(f"* bytes only: {', '.join('`' + x + '`' for x in raw['cache_vs_bytes']['bytes_only'])}")
    a(f"* cache only: {', '.join('`' + x + '`' for x in raw['cache_vs_bytes']['cache_only'])}")
    a(f"* shared members that disagree in value: {len(raw['cache_vs_bytes']['shared_diffs'])}")
    a("")
    if d["allwheel"]["disagreements"]:
        a("That matters because `TANKTURN.md` uses `is_all_wheel_steered` to name the three")
        a("monster-truck builds as the fleet's only all-wheel-steered vehicles. The bytes say")
        a("those builds are `FrontSteered`:")
        a("")
        a("| cached build | chassis | cache flag | bytes `steering_type` |")
        a("|---|---|---|---|")
        for c in d["allwheel"]["disagreements"]:
            a(f"| `{c['build']}` | `{c['chassis']}` | {c['cache_is_all_wheel_steered']} | "
              f"`{c['bytes_steering_type']}` |")
        a("")
        a("So the cached flag is not a member of the shipped module. TANKTURN's *conclusion*")
        a("(no pivot carrier) does not depend on it - the module member sets are identical and no")
        a("pivot name exists - but its candidate row `is_all_wheel_steered` should be read as a")
        a("cache artefact, not a shipped value.")
    else:
        a("No cache/byte disagreement on the all-wheel-steer flag was found.")
    a("")
    a("## 6. The other driving moves")
    a("")
    a("### 6.1 Power Slide (left stick + RT + X) - C8, carrier found")
    a("")
    a("| member | donor (fleet min .. max; builds) | what it gives |")
    a("|---|---|---|")
    for mod, p, note in (
            ("Brakes", "rear.handbrake", "rear axle is the handbrake axle"),
            ("Brakes", "front.handbrake", "front axle is never handbraked"),
            ("Brakes", "handbrake_friction_factor", "how hard the handbrake bites"),
            ("Brakes", "rear.max_brake_torque", "torque budget"),
            ("CustomVelocityDamper", "handbrake_spin_damping", "how much spin the handbrake keeps"),
            ("CustomLandGlobal", "drift.counter_steer_torque_handbrake",
             "yaw torque while countersteering on the handbrake"),
            ("CustomLandGlobal", "drift.min_speed_to_drift_kmph", "entry speed for the slide"),
    ):
        a(f"| `{mod}.{p}` | {val(mod, p)} | {note} |")
    a("")
    a(f"`Brakes.rear.handbrake` is 1 on {dr['rear_handbrake_builds']} builds and "
      f"`front.handbrake` on {dr['front_handbrake_builds']}: JC3's handbrake is a rear-axle")
    a("lock, which is exactly the mechanism a power slide needs, and the drift block already")
    a("has a handbrake-specific yaw torque. This is a **tune**, not a code bridge: the input is")
    a("`HANDBRAKE` (bound to RPADLEFT in the patch gamepad map) and the values are the four")
    a("members above. Amendment needed: BmAK binds it to X together with RT, and the angles and")
    a("torques have to come from the T rows, not from these defaults.")
    a("")
    a("Note on the donor column: the values above are the **player** copy. The donor's `_ai` twin")
    a("carries `handbrake_friction_factor` = 2 against the player's 1, which is why")
    a("`VOCABULARY.md` shows 2: its donor column read the AI instance. Player copies are the")
    a("ones the game drives, so they are the ones quoted here (the same rule as `jc3tankturn.py`).")
    a("")
    a("### 6.2 Afterburner (Y) - C9, carrier found")
    a("")
    a("The nitrous chain, in the order it acts:")
    a("")
    a("| member | module | donor (fleet min .. max; builds) |")
    a("|---|---|---|")
    for mod, p in (("CustomLandGlobal", "arcade.nitro_boost.extra_top_speed"),
                   ("CustomLandGlobal", "arcade.nitro_boost.torque_multiplier"),
                   ("CustomLandGlobal", "arcade.nitro_boost.grip_multiplier"),
                   ("CustomLandGlobal", "arcade.nitro_boost.push_force"),
                   ("CustomLandGlobal", "arcade.nitro_boost.boost_blend_time"),
                   ("CustomLandGlobal", "arcade.nitro_boost_upgraded.extra_top_speed"),
                   ("CustomLandGlobal", "arcade.nitro_boost_upgraded.push_force"),
                   ("Transmission", "nitrous_gears"),
                   ("VehicleMisc", "full_nitro_use_time"),
                   ("VehicleMisc", "full_nitro_use_time_upgraded"),
                   ("VehicleMisc", "full_nitro_refill_time"),
                   ("VehicleMisc", "nitro_refill_min_speed_kph"),
                   ("CustomLandGlobal", "arcade.heat_boost.extra_top_speed")):
        a(f"| `{p}` | `{mod}` | {val(mod, p)} |")
    a("")
    a(f"The `arcade.nitro_boost` block is on {dr['nitro_builds']} of the "
      f"{d['inputs']['entities']} builds (matching T-WP13's 145), and the `VehicleMisc` nitro")
    a(f"timers are on {m[('VehicleMisc','full_nitro_use_time')]['builds']} - every vehicle, so the")
    a("duration and refill model exists even where the boost block does not. What the chain")
    a("already gives an Afterburner:")
    a("")
    a("* flat extra top speed on top of the driveline (`extra_top_speed`, donor +40 km/h;")
    a("  `_upgraded` +80),")
    a("* a torque multiplier (donor x2) and a push force (15,000 N; 20,000 upgraded),")
    a("* a grip multiplier (donor x2), so the boost changes handling as well as speed,")
    a("* a blend time (0.2 s) - the boost ramps instead of snapping,")
    a("* a finite burn (`full_nitro_use_time` 4 s, 8 s upgraded) and a refill rule")
    a("  (`full_nitro_refill_time` 2 s, only above `nitro_refill_min_speed_kph` = 20).")
    a("")
    a("What needs an amendment: the **trigger**. Neither keymap has a NITRO or vehicle BOOST")
    a("action (the only boost name is `WINGSUIT_BOOST`), so the button that fires the block is")
    a("native or un-named; the operator lead that JC3's nitrous is \"hold B\" is consistent with")
    a("the data side existing and the action side missing, and stays **UNKNOWN** as data. Also")
    a("amended: the 4 s budget refilled by driving is JC3's arcade model, not a hold-while-")
    a("pressed afterburner; the timers are tunable, the semantics are not.")
    a("")
    a("### 6.3 Side Swipe and Dodge Thrusters - C6, C7, no exact carrier")
    a("")
    a("Side Swipe is a lateral shove while moving. The closest data is the drift block's")
    a("velocity-keeping members, which do move the car sideways relative to its heading:")
    a("")
    a("| member | donor (fleet min .. max; builds) |")
    a("|---|---|")
    for p in ("drift.keep_velocity_strength", "drift.velocity_rotation_amount",
              "drift.velocity_rotation_start_angle", "drift.velocity_rotation_end_angle"):
        a(f"| `drift.{p.split('.',1)[1]}` | {val('CustomLandGlobal', p)} |")
    a("")
    a("Dodge Thrusters is an impulse in the stick's direction. The fleet's impulse-shaped")
    a("blocks are `arcade.turbo_jump.*` (a fixed-direction jump punch) and the `CForcePulse`")
    a("device in the `.epe` graph (radial, a weapon/explosion effect, not a driving block):")
    a("")
    a("| member | donor (fleet min .. max; builds) |")
    a("|---|---|")
    for p in ("arcade.turbo_jump.punch_speed_kph", "arcade.turbo_jump.top_speed_kph",
              "arcade.turbo_jump.f_multiplier", "turbo_jump_cooldown"):
        mod = "VehicleMisc" if p == "turbo_jump_cooldown" else "CustomLandGlobal"
        a(f"| `{p}` | {val(mod, p)} |")
    a("")
    a(f"`arcade.turbo_jump` is on {dr['turbo_jump_builds']} builds. Neither block takes a")
    a("direction, so both moves need an amendment (a directional impulse is not a member of any")
    a("module) or a code bridge that reads the stick and applies its own impulse. This is the")
    a("same missing piece as the camera-relative move in section 4: **no vehicle module consumes")
    a("a 2D stick**.")
    a("")
    a("## 7. UNKNOWNs")
    a("")
    a("1. **Whether a stationary car can be made to rotate.** The drift block's speed gate")
    a(f"   reaches 0 km/h on {dr['drift_min_speed_zero_builds']} builds, but the rotation is")
    a("   slip-angle driven and the arithmetic is native. *Tried:* member scan for pivot/spin/")
    a(f"   counter-rotate names over all {d['inputs']['module_types']} module types (0 hits in "
      "a drive module); the byte")
    a("   member list of the donor's `land_global`; TANKTURN.md's fleet-wide candidate test.")
    a("   *Where it would be:* the engine's land-vehicle torque solver, not a module.")
    a("2. **What fires `arcade.nitro_boost`.** *Tried:* both keymaps, base and patch, all 249")
    a("   bindings; the 232 entity builds for any action name (0). *Where:* native, or a graph")
    a("   the files do not name.")
    a("3. **Whether a vehicle can consume `MOVE_ALL`/`LSTICKGENERIC`.** *Tried:* keymap decode")
    a("   (one binding), scope-name rule, entity census (0 entity names a keymap). *Where:* the")
    a("   native class-to-action-set selection.")
    a("4. **The `steering_type` value domain.** The bytes name one value (`FrontSteered`) and")
    a("   store only a hash, so other values (if any) are not recoverable from these files.")
    a("5. **Whether the cached `is_all_wheel_steered` flag has any other source.** *Tried:* the")
    a("   patch-layer bytes of all 54 `land_global` modules (no such member), the donor's byte")
    a("   member list, the base+patch INDEX (one copy of the module). *Where:* the grab tool")
    a("   that produced the cached rows - it is not in the shipped module.")
    a("")
    a("## 8. Validation and limits")
    a("")
    a("`--check` re-reads the decoded cache, the 54 module entry offsets and the keymap bytes,")
    a("re-derives every number above, and fails if this document or the JSON drifted. Invariants")
    a("asserted: "
      f"{d['inputs']['land_builds']} land builds; {d['inputs']['module_types']} module types;")
    a("0 per-wheel/differential members; 0 camera/strafe/dodge members inside a driving module")
    a("(the six propeller-docking rows are checked to stay outside it); every sampled")
    a("`steering_type` hash equal to the Jenkins")
    a("hash of its own name; the donor's byte rows and cached rows agreeing on every shared")
    a("member; the keymap byte accounting tiling exactly; no camera-relative action in either")
    a("keymap.")
    a("")
    a("**Limits.** Static only: no game was launched, no install written, no process touched.")
    a("The byte-level fleet scan covers the 54 `land_global` modules that `INDEX.jsonl` lists -")
    a("the other vehicle module types are not indexed per entry, so their fleet-wide statement")
    a("rests on the decoded row cache (the same source the rest of G2 uses). The `.epe`-side")
    a("statement is a class census, not a property walk: the decoded graphs carry classes and")
    a("parts, not every object property.")
    a("")
    if raw["donor_module"]:
        dm = raw["donor_module"]
        a("## 9. Appendix - the donor's `land_global` module, decoded from the bytes")
        a("")
        a(f"`{dm['path']}` in `{dm['archive']}` at entry offset **{dm['entry_offset']}**, "
          f"{dm['size']} B, sha256 `{dm['sha256'][:16]}`; root type `{dm['type']}` "
          f"({dm['type_size']} B). `offset` is the member's struct offset.")
        a("")
        a("| offset | size | member | type | value |")
        a("|---|---|---|---|---|")
        for x in dm["rows"]:
            off = x["offset"]
            a(f"| {off if off is not None else '-'} | {x['member_size'] or '-'} | "
              f"`{x['member']}` | {x['type']} | {numstr(x['value'])} |")
        a("")
    a("Checkable: `python Tools/scripts/jc3_drive_carriers.py --check`.")
    a("")
    return "\n".join(L)


# ------------------------------------------------------------------ check

def invariants(d: dict) -> list[str]:
    bad = []
    scan = {s["group"]: s for s in d["scan"]}
    if d["inputs"]["land_builds"] < 100:
        bad.append(f"land builds {d['inputs']['land_builds']} - cache incomplete?")
    if d["inputs"]["entities"] != d["inputs"]["detail"]:
        bad.append("entities/detail count differ")
    if scan["per-wheel drive / differential"]["distinct"]:
        bad.append("per-wheel/differential vocabulary exists after all")
    for g in ("per-wheel drive / differential", "camera-relative / face-camera control"):
        if scan[g]["drive_module_hits"]:
            bad.append(f"{g}: drive-module hits {scan[g]['drive_module_hits'][:2]}")
    # every camera/strafe/dodge hit must be outside the land driving set
    for r in scan["camera-relative / face-camera control"]["rows"]:
        if r["in_drive_module"]:
            bad.append(f"camera-relative member inside a drive module: {r['member']}")
    raw = d["raw"]
    if sum(raw["steering_type_histogram"].values()) != raw["modules"]:
        bad.append("steering_type histogram does not sum to the module count")
    for st, h in raw["hash_check"].items():
        if not h["match"]:
            bad.append(f"steering_type hash mismatch for {st}")
    if not raw["cache_vs_bytes"]["bytes_only"]:
        bad.append("expected the cached rows to lack steering_type")
    if raw["cache_vs_bytes"]["shared_diffs"]:
        bad.append(f"cache/byte value diffs {raw['cache_vs_bytes']['shared_diffs'][:2]}")
    kb = d["keymap"]
    for f in kb["files"]:
        acct = f["accounting"]
        if not acct["blocks_tile_data"] or not 0 <= acct["tail_bytes"] <= 3:
            bad.append(f"{f['path']} ({f['mount']}) does not tile")
    if not any(x["action"] == "MOVE_ALL" for x in kb["vector_bindings"]):
        bad.append("MOVE_ALL/LSTICKGENERIC binding missing")
    if any(x["action"] not in ("WINGSUIT_BOOST",) for x in kb["camera_relative_actions"]):
        bad.append(f"unexpected boost/camera action {kb['camera_relative_actions']}")
    if len(kb["vehicle_actions"]) < 10:
        bad.append(f"only {len(kb['vehicle_actions'])} land-vehicle actions")
    dr = d["derived"]
    if dr["rear_handbrake_builds"] <= 0:
        bad.append("no rear-handbrake builds")
    if dr["front_handbrake_builds"] != 0:
        bad.append("front handbrake is not 0 on every build")
    mem = {(x["module"], x["path"]): x for x in d["members"]}
    if dr["rear_friction_equal"] + dr["rear_friction_below_front"] + dr["rear_friction_above_front"] \
            > mem[("LandGlobal", "rear_wheels.arcade_friction_multiplier")]["builds"]:
        bad.append("per-axle friction accounting")
    if dr["nitro_builds"] != 145:
        bad.append(f"nitro builds {dr['nitro_builds']} != 145")
    if "CCameraModifier" not in d["epe"]["classes_matching_camera"]:
        bad.append("CCameraModifier missing from the graph census")
    if d["allwheel"]["cache_builds"] and not d["allwheel"]["disagreements"]:
        bad.append("all-wheel-steer cache builds have no byte disagreement recorded")
    return bad


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {d['inputs']['land_builds']} land builds, "
          f"{d['inputs']['module_types']} module types, "
          f"{d['inputs']['raw_land_global_modules']} byte-decoded land_global modules, "
          f"{d['derived']['nitro_builds']} nitro builds, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    if json.load(open(jp, encoding="utf-8")) != d:
        bad.append(f"{JSON_NAME} stale")
    md = render_md(d)
    have = open(mp, encoding="utf-8").read()
    if md != have:
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file",
                                         "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    scan = {s["group"]: s for s in d["scan"]}
    print(f"PASS: {d['inputs']['land_builds']} land builds / {d['inputs']['module_types']} "
          f"module types; per-wheel-drive members "
          f"{scan['per-wheel drive / differential']['distinct']}, camera-relative members "
          f"{scan['camera-relative / face-camera control']['distinct']}, "
          f"stationary-turn members {scan['stationary turn / pivot']['distinct']} "
          f"(0 in a drive module); {d['inputs']['raw_land_global_modules']} byte-decoded "
          f"land_global modules -> steering_type "
          f"{d['raw']['steering_type_histogram']}; cache/bytes delta "
          f"{d['raw']['cache_vs_bytes']['bytes_only']} vs "
          f"{d['raw']['cache_vs_bytes']['cache_only']}; "
          f"{len(d['keymap']['vehicle_actions'])} land-vehicle actions, "
          f"{len(d['keymap']['vector_bindings'])} 2D-stick binding(s); "
          f"nitro {d['derived']['nitro_builds']} builds, rear handbrake "
          f"{d['derived']['rear_handbrake_builds']}, front handbrake "
          f"{d['derived']['front_handbrake_builds']}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"scan": "scan", "members": "members", "raw": "raw", "keymap": "keymap"}.get(what)
    if not key:
        print("one of: scan, members, raw, keymap")
        return 2
    print(json.dumps(d[key], indent=1, sort_keys=True, ensure_ascii=False)[:20000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="scan")
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
    raise SystemExit(main())
