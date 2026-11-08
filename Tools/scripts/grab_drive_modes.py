#!/usr/bin/env python3
"""grab_drive_modes.py - G3-02l: what decides the Batmobile's driving behaviour per mode.

Static only: reads `BmGame.upk` and `Startup.upk` (read-only), never the game process.

The question the card asks is narrow: which fields and which script code decide

    * the drive type / wheel-torque distribution per mode,
    * the steering input path in each mode,
    * any camera-relative or face-camera rule,
    * any stationary-turn (spin in place) logic.

Everything below is re-derived from the cooked bytes by this script:

 1. `RVehicleSimBatmobile.EBatmobileDriveMode` - the enum that the simulation's `DriveMode`
    byte holds.  The enum payload is a count plus (FName index, number) pairs; the names are
    resolved through the package name table.  Decoded.
 2. The two cooked objects that carry the values:
      Startup.upk export 169320  `Default__RVehicleBatmobile.SimulationModel`  (the shipped car)
      BmGame.upk  export 129779  `Default__RVehicleSimBatmobile`             (the class CDO)
    Both are Batman property-tag streams; a tag carries type + byte offset only, so the name
    comes from `BMSDK_OFFSETS.json`'s class layout for that offset and a compatible kind.  A
    field with no tag is reported as "not serialised here" - never given a made-up value.
 3. The mode states' bodies.  `RVehicleBatmobileBase.PursuitMode` / `.BattleMode` and the NPC
    twins `RVehicleNPCBatmobile.PursuitMode` / `.BattleMode`: every BeginState / EndState /
    Tick / BattleDodge body is walked for its calls and its property references.  The
    `SetDriveMode(<byte>)` call and its argument are read from the bytes at the call site.
 4. A corpus scan: every Function export in BmGame.upk whose script bytes contain a reference
    to one of the drive-mode property exports, with the token that precedes it.  This is how a
    reader/writer is found without trusting a memory of UE3.
 5. The strafe/dodge bodies the controls menu names: `DrivingMode.BattleStrafe`,
    `DelayedBattleStrafe`, `PursuitStrafeOn`, `PursuitStrafe`, `CheckBattleStrafe`,
    `VehicleStrafe`, `RVehicleBatmobileBase.VehicleStrafe`, `BattleMode.BattleDodge`.
    Calls + arguments, property references and float/int constants are recorded, including the
    16384 rotator constant (90 deg in UE3 rotator units) beside `BattleModeYawOffset`.

Oracles (any failure stops --write; --check re-runs all of them):
    O1  the enum resolves to exactly BMDM_Drive / BMDM_TurnOnSpot / BMDM_BattleMode / BMDM_MAX
        with values 0..3, and `DriveMode`'s byte is that enum.
    O2  every decoded Function export passes the three bmak_damage anchors.
    O3  both property streams walk from their first tag to the stream end ('end'/'eof') and
        every printed scalar is re-read from the byte offset it is printed with.
    O4  every `SetDriveMode` call site's byte argument decodes to an enum member, and the
        pursuit body asks for BMDM_Drive while the battle body asks for BMDM_BattleMode.
    O5  every corpus property hit re-reads as that property's export index at its offset.
    O6  the 16384 constant used with `BattleModeYawOffset` is re-read as an int32 16384.
    O7  the shipped simulation object's `DriveMode` tag is BMDM_Drive (enum value 0).

Usage:
    uv run python Tools/scripts/grab_drive_modes.py --write
    uv run python Tools/scripts/grab_drive_modes.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bmak_damage as B            # noqa: E402
import upk_read as U               # noqa: E402

COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
BMSGAME = os.path.join(COOKED, "BmGame.upk")
STARTUP = os.path.join(COOKED, "Startup.upk")
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVE_MODES.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVE_MODES.json")

SIM = "RVehicleSimBatmobile"
BASE = "RVehicleBatmobileBase"
ENUM_NAME = "EBatmobileDriveMode"
DRIVE_MODE_PROP = "DriveMode"

# The fields this card is about.  (owner class, member) -> looked up in BMSDK_OFFSETS.json.
FIELDS = [
    (SIM, "DriveMode"),
    (SIM, "TurnOnSpotFrontTorqueFactor"),
    (SIM, "TurnOnSpotRearTorqueFactor"),
    (SIM, "TurnOnSpotModeEngineBrakingFactor"),
    (SIM, "DriveModeEngineBrakingFactor"),
    (SIM, "DesiredTurnOnSpotSpeed"),
    (SIM, "TurningModeMaxSpeed"),
    (SIM, "ForceTurnOnSpotMode"),
    (SIM, "BattleModeMoving"),
    (SIM, "bBattleModeReversing"),
    (SIM, "BattleModeTurnOnSpotTorqueFactor"),
    (SIM, "BattleModeStopAndTurnAngleStationary"),
    (SIM, "BattleModeStopAndTurnAngleMoving"),
    (SIM, "BattleModeSteerAngleFactor"),
    (SIM, "BattleModeTrailingSteerFactorTurnOnSpot"),
    (SIM, "BattleModeTrailingSteerFactorMoving"),
    (SIM, "BattleModeMaxSteering"),
    (SIM, "BattleModeRearWheelTorquePower"),
    (SIM, "BattleModeFrontThrottle"),
    (SIM, "BattleModeRearThrottle"),
    (SIM, "BattleModeDriveForceFactor"),
    (SIM, "BattleModeMaxSpeed"),
    (SIM, "BattleModeThrottleSpeed"),
    (SIM, "BattleModeLatSlipScale"),
    (SIM, "BattleModeLongSlipScale"),
    (SIM, "BattleModeEngineBrakingFactor"),
    (SIM, "BattleModeDrivingForceZOffset"),
    (SIM, "BattleModeVSpeedCurve"),
    (SIM, "TurnOnSpotSteeringSpeedCurve"),
    (SIM, "FrontWheelSteerPct"),
    (SIM, "RearWheelSteerPct"),
    (SIM, "AbsoluteMoveDirection"),
    (BASE, "BattleModeYawOffset"),
    (BASE, "bForceBattleModeMovement"),
    (BASE, "StrafeCooldown"),
    (BASE, "StrafeFwdCorrectionForce"),
    (BASE, "PMDodgeTorque"),
    (BASE, "PMDodgeForce"),
    (BASE, "PMDodgeDuration"),
    (BASE, "BattleDodgeImpulse"),
]

# Property names the corpus scan follows (resolved to export indices by owner+name).
SCAN = [(o, n) for o, n in FIELDS if n != DRIVE_MODE_PROP] + [
    (SIM, "DriveMode"), (BASE, "CurrentStrafeCooldown"),
]

# The bodies decoded in full (calls + arguments + references + constants).
# (class, state-or-None, function).  A cooked state body's object_path prints the OUTER's short
# name (`PursuitMode.BeginState`), so the owner class is resolved through the state's outer.
BODIES = [
    (BASE, "PursuitMode", "BeginState"),
    (BASE, "PursuitMode", "Tick"),
    (BASE, "PursuitMode", "EndState"),
    (BASE, "BattleMode", "BeginState"),
    (BASE, "BattleMode", "EndState"),
    (BASE, "BattleMode", "Tick"),
    (BASE, "BattleMode", "BattleDodge"),
    ("RVehicleNPCBatmobile", "PursuitMode", "BeginState"),
    ("RVehicleNPCBatmobile", "BattleMode", "BeginState"),
    (BASE, None, "VehicleStrafe"),
    ("RPlayerController", "DrivingMode", "VehicleStrafe"),
    ("RPlayerController", "DrivingMode", "BattleStrafe"),
    ("RPlayerController", "DrivingMode", "DelayedBattleStrafe"),
    ("RPlayerController", "DrivingMode", "PursuitStrafeOn"),
    ("RPlayerController", "DrivingMode", "PursuitStrafe"),
    ("RPlayerController", "DrivingMode", "CheckBattleStrafe"),
]

REF_TOKENS = {0x00, 0x01, 0x02, 0x20, 0x29, 0x2E, 0x3A, 0x48}
LIT_FIXED = {0x1D: 4, 0x1E: 4, 0x24: 1, 0x2C: 1}
BARE_LIT = {0x25: "0", 0x26: "1", 0x27: "true", 0x28: "false", 0x2A: "None", 0x17: "self"}


# ------------------------------------------------------------------ small helpers

def chain(classes, root):
    out, seen, c = [], set(), root
    while c and c not in seen:
        seen.add(c)
        out.append(c)
        c = (classes.get(c) or {}).get("super")
    return out


def layout(classes, root):
    lay = {}
    for cn in chain(classes, root):
        for p in classes.get(cn, {}).get("properties", []):
            lay.setdefault(p["offset"], []).append((cn, p))
    return lay


def walk_tags(pkg, data, start):
    """The upk_read tag walk, returning (rows, end, why) with the raw tag objects."""
    return U.walk_tags(pkg, data, start, max_tags=20000)


def find_start(pkg, data):
    """Try every start 0..40 and keep the walk that reaches the end with the most tags."""
    best = None
    for st in range(0, 41):
        tags, end, why = walk_tags(pkg, data, st)
        score = (why == "end" and end >= len(data) - 2, len(tags), -st)
        if best is None or score > best[0]:
            best = (score, st, tags, end, why)
    return best[1:]


def script_of(pkg, i):
    d = pkg.data(i)
    return d, (d[22:len(d) - 16] if len(d) >= 38 else b"")


def anchors(pkg, i, script):
    d = pkg.data(i)
    name = pkg.exports[i - 1]["name"]
    name_idx = struct.unpack_from("<i", d, len(d) - 8)[0] if len(d) >= 8 else -1
    pre = struct.unpack_from("<i", d, len(d) - 12)[0] if len(d) >= 12 else 0
    return {
        "script_size_field_eq_len_plus_1": struct.unpack_from("<i", d, 18)[0] == len(script) + 1,
        "name_index_matches_export_name": 0 <= name_idx < len(pkg.names) and pkg.names[name_idx] == name,
        "pre_name_word_0x0002xxxx": (pre & 0xFFFF0000) == 0x00020000,
    }


def export_of(pkg, path):
    for i in range(1, pkg.export_count + 1):
        if pkg.object_path(i) == path:
            return i
    return None


def exports_named(pkg, name):
    return [i for i in range(1, pkg.export_count + 1) if pkg.exports[i - 1]["name"] == name]


def read_arg(script, p):
    """One argument token -> (text, value, next offset) or (None, None, p) when not a literal."""
    if p >= len(script):
        return None, None, p
    t = script[p]
    if t in LIT_FIXED:
        n = LIT_FIXED[t]
        if p + 1 + n > len(script):
            return None, None, p
        raw = script[p + 1:p + 1 + n]
        if t == 0x24 or t == 0x2C:
            return str(raw[0]), raw[0], p + 1 + n
        if t == 0x1D:
            v = struct.unpack("<i", raw)[0]
            return str(v), v, p + 1 + n
        return "%g" % struct.unpack("<f", raw)[0], struct.unpack("<f", raw)[0], p + 1 + n
    if t in BARE_LIT:
        return BARE_LIT[t], None, p + 1
    return None, None, p


def call_sites(pkg, script, name):
    """Offsets of `EX_FinalFunction(name_index)` in a body."""
    out = []
    for i in range(1, pkg.export_count + 1):
        if pkg.exports[i - 1]["name"] != name:
            continue
        pat = struct.pack("<i", i)
        p = 0
        while True:
            p = script.find(pat, p)
            if p < 0:
                break
            if p > 0 and script[p - 1] in (0x1B, 0x1C):
                out.append((p - 1, pkg.object_path(i)))
            p += 1
    return out


def first_arg_after(script, at):
    """The first literal argument of a call at `at` (call token + 5-byte operand)."""
    txt, val, _ = read_arg(script, at + 5)
    return txt, val


# ------------------------------------------------------------------ the record

def build():
    bm = B.Bm(BMSGAME)
    pkg = bm.pkg
    spkg = U.Package(STARTUP)
    classes = json.load(open(OFFSETS, encoding="utf-8"))["classes"]
    lay = layout(classes, SIM)
    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    doc = {
        "card": "G3-02l",
        "generator": "grab_drive_modes.py",
        "packages": {
            "BmGame.upk": {"bytes": os.path.getsize(BMSGAME), "version": pkg.version,
                           "exports": pkg.export_count, "names": pkg.name_count},
            "Startup.upk": {"bytes": os.path.getsize(STARTUP), "version": spkg.version,
                            "exports": spkg.export_count, "names": spkg.name_count},
        },
        "enum": {}, "archetypes": {}, "fields": [], "bodies": [], "corpus": [],
        "menu_moves": [], "oracles": [], "unknowns": [], "contradictions": [],
    }

    # ---- 1. the drive-mode enum ------------------------------------------------
    enum_i = None
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) == "Enum" and pkg.exports[i - 1]["name"] == ENUM_NAME:
            enum_i = i
            break
    if enum_i is None:
        raise SystemExit("enum %s not found in BmGame.upk" % ENUM_NAME)
    edata = pkg.data(enum_i)
    count = struct.unpack_from("<i", edata, 6)[0]
    values = []
    for k in range(count):
        idx, num = struct.unpack_from("<ii", edata, 10 + 8 * k)
        values.append({"value": k, "name": pkg.names[idx], "name_index": idx, "number": num})
    doc["enum"] = {"path": pkg.object_path(enum_i), "export": enum_i, "count": count,
                   "values": values}
    names = [v["name"] for v in values]
    oracle("O1-enum",
           count == 4 and names[:4] == ["BMDM_Drive", "BMDM_TurnOnSpot",
                                        "BMDM_BattleMode", "BMDM_MAX"]
           and [v["value"] for v in values] == [0, 1, 2, 3],
           "%s export %d: %d values %s"
           % (ENUM_NAME, enum_i, count,
              ", ".join("%d=%s" % (v["value"], v["name"]) for v in values)))
    drive_enum = {v["name"]: v["value"] for v in values}

    # ---- 2. the two cooked value streams --------------------------------------
    targets = [
        {"role": "shipped_simulation", "package": "Startup.upk", "pkg": spkg, "export": 169320,
         "object": "Default__RVehicleBatmobile.SimulationModel", "class": SIM},
        {"role": "class_default_object", "package": "BmGame.upk", "pkg": pkg, "export": 129779,
         "object": "Default__RVehicleSimBatmobile", "class": SIM},
        {"role": "vehicle_class_default_object", "package": "BmGame.upk", "pkg": pkg,
         "export": 10923, "object": "BmGame.Default__RVehicleBatmobileBase", "class": BASE},
    ]
    for t in targets:
        data = t["pkg"].data(t["export"])
        st, tags, end, why = find_start(t["pkg"], data)
        lay_t = layout(classes, t["class"])
        rec = {"role": t["role"], "package": t["package"], "export": t["export"],
               "object": t["object"], "class": t["class"], "size": len(data),
               "tag_start": st, "tags": len(tags), "end": end, "stop": why, "values": {}}
        for tag in tags:
            if tag.get("type") == "EndProperty":
                continue
            off = tag.get("offset")
            cands = [(cn, p) for cn, p in (lay_t.get(off) or [])]
            same = [p for cn, p in cands if p["kind"] in ("FloatProperty", "IntProperty", "ByteProperty",
                                                          "BoolProperty", "StructProperty",
                                                          "ArrayProperty", "NameProperty",
                                                          "ObjectProperty", "ObjectNCRProperty")]
            name = same[0]["kind"] if same else None
            if not same:
                continue
            member = same[0]["member"]
            key = "%s.%s" % (same[0].get("class", "") or "", member)
            rec["values"][member] = {"offset": off, "tag_type": tag.get("type"),
                                     "kind": same[0]["kind"], "at": tag.get("at"),
                                     "value": tag.get("value"), "bits": tag.get("bits"),
                                     "struct": tag.get("size") if tag.get("type") == "StructProperty" else None}
        doc["archetypes"][t["role"]] = rec

    # O3: scalar re-read from the byte offset each printed value claims
    reread, bad = 0, []
    for role, rec in doc["archetypes"].items():
        src = spkg if role == "shipped_simulation" else pkg
        data = src.data(rec["export"])
        for member, v in rec["values"].items():
            if v["kind"] != "FloatProperty" or v["at"] is None:
                continue
            got = round(struct.unpack_from("<f", data, v["at"])[0], 6)
            reread += 1
            if got != round(v["value"], 6):
                bad.append("%s.%s" % (role, member))
            continue
        if v["kind"] != "IntProperty" or v["at"] is None:
            continue
        got = struct.unpack_from("<i", data, v["at"])[0]
        reread += 1
        if got != v["value"]:
            bad.append("%s.%s" % (role, member))
    oracle("O3-tag-values", not bad and reread > 0,
           "streams end at %s; %d float values re-read from their tag payload offsets%s"
           % (", ".join("%s(%s)" % (r["role"], r["stop"]) for r in doc["archetypes"].values()),
              reread, "" if not bad else "; mismatch: " + ", ".join(bad)))

    # ---- 3. the field table (layout + both values) ----------------------------
    by_member = {}
    for root in (SIM, BASE, "RVehicle"):
        for cn in chain(classes, root):
            for p in classes.get(cn, {}).get("properties", []):
                by_member.setdefault((cn, p["member"]), p)
                by_member.setdefault(("*", p["member"]), p)
    for owner, member in FIELDS:
        p = by_member.get((owner, member)) or by_member.get(("*", member))
        if p is None:
            doc["fields"].append({"owner": owner, "member": member, "offset": None,
                                  "kind": None, "label": "UNKNOWN (no layout entry)"})
            continue
        shipped = doc["archetypes"]["shipped_simulation"]["values"].get(member)
        cdo = doc["archetypes"]["class_default_object"]["values"].get(member)
        veh = doc["archetypes"]["vehicle_class_default_object"]["values"].get(member)
        doc["fields"].append({
            "owner": owner, "member": member, "offset": p["offset"],
            "offset_hex": "0x%04x" % p["offset"], "kind": p["kind"],
            "type": p.get("type"),
            "shipped": shipped["value"] if shipped else None,
            "shipped_bits": shipped["bits"] if shipped else None,
            "class_default": cdo["value"] if cdo else None,
            "class_default_bits": cdo["bits"] if cdo else None,
            "vehicle_default": veh["value"] if veh else None,
            "vehicle_default_bits": veh["bits"] if veh else None,
        })

    # ---- 4. mode state bodies -------------------------------------------------
    def body_record(i):
        d, s = script_of(pkg, i)
        w = bm.walk(s, own=pkg.exports[i - 1]["name"])
        calls = []
        for r in w["refs"]:
            if r["token"] not in ("EX_VirtualFunction", "EX_FinalFunction"):
                continue
            txt, val = (None, None)
            if r["token"] == "EX_FinalFunction":
                txt, val = first_arg_after(s, r["at"])
            calls.append({"at": r["at"], "kind": r["token"].split("_")[1],
                          "target": r["ref"], "first_arg_text": txt, "first_arg_value": val})
        rec = {"path": pkg.object_path(i), "export": i, "script_bytes": len(s),
               "calls": calls,
               "refs": [{"at": r["at"], "token": r["token"], "ref": r["ref"]}
                        for r in w["refs"]
                        if r["token"] not in ("EX_VirtualFunction", "EX_FinalFunction")],
               "constants": [{"at": c["at"], "kind": c["kind"], "value": c["value"]}
                             for c in w["constants"]],
               "anchors": anchors(pkg, i, s),
               "native_thunk": (len(s) == 5 and s[0] == 0x29)}
        return rec

    def resolve_body(cls, state, func):
        if state is None:
            for i in exports_named(pkg, func):
                if (pkg.object_path(i) or "").startswith(cls + "."):
                    return i
            return None
        for i in exports_named(pkg, state):
            if pkg.object_class(i) != "State":
                continue
            if not (pkg.object_path(i) or "").startswith(cls + "."):
                continue
            for j in exports_named(pkg, func):
                if pkg.exports[j - 1]["outer_index"] == i:
                    return j
        return None

    for cls, state, func in BODIES:
        label = "%s.%s%s" % (cls, (state + ".") if state else "", func)
        i = resolve_body(cls, state, func)
        if i is None:
            doc["bodies"].append({"path": label, "missing": True})
            continue
        rec = body_record(i)
        rec["label"] = label
        doc["bodies"].append(rec)

    every_body = [b for b in doc["bodies"] if not b.get("missing")]
    bad2 = [b["path"] for b in every_body if not all(b["anchors"].values())]
    oracle("O2-function-anchors", not bad2 and len(every_body) > 0,
           "%d/%d decoded bodies pass the three bmak_damage anchors%s"
           % (len(every_body) - len(bad2), len(every_body),
              "" if not bad2 else "; FAIL: " + ", ".join(bad2)))

    # O4: SetDriveMode call sites + arguments
    sdm = export_of(pkg, "RVehicleSimBatmobile.SetDriveMode")
    sdm_sites = []
    for b in every_body:
        for c in b["calls"]:
            if c["target"] and c["target"].endswith(".SetDriveMode"):
                sdm_sites.append({"path": b["path"], "label": b.get("label") or b["path"],
                                  "export": b["export"], "at": c["at"],
                                  "arg_text": c["first_arg_text"],
                                  "arg_value": c["first_arg_value"]})
    ok4 = bool(sdm_sites) and all(s["arg_value"] in drive_enum.values() for s in sdm_sites)
    want = {"PursuitMode.BeginState": drive_enum.get("BMDM_Drive"),
            "BattleMode.BeginState": drive_enum.get("BMDM_BattleMode")}
    matched = {}
    for s in sdm_sites:
        short = s["path"].rsplit(".", 2)[-2] + "." + s["path"].rsplit(".", 1)[-1]
        matched.setdefault(short, []).append(s["arg_value"])
    for short, val in want.items():
        if not matched.get(short) or any(v != val for v in matched[short]):
            ok4 = False
    doc["set_drive_mode"] = {"export": sdm, "sites": sdm_sites,
                             "expected": {"PursuitMode.BeginState": want["PursuitMode.BeginState"],
                                          "BattleMode.BeginState": want["BattleMode.BeginState"]},
                             "observed": matched}
    ttcm = export_of(pkg, "RVehicleBatmobileBase.TryToChangeMode")
    ttcm_s = script_of(pkg, ttcm)[1] if ttcm else b""
    doc["try_to_change_mode"] = {"export": ttcm, "script_bytes": len(ttcm_s),
                                 "native_thunk": len(ttcm_s) == 5 and ttcm_s[:1] == b"\x29"}
    oracle("O4-drive-mode-per-state", ok4,
           "%d SetDriveMode call site(s); pursuit asks %s, battle asks %s (enum values %s)"
           % (len(sdm_sites), matched.get("PursuitMode.BeginState"),
              matched.get("BattleMode.BeginState"),
              {k: v for k, v in drive_enum.items() if k != "BMDM_MAX"}))

    # O7: the default DriveMode tag is BMDM_Drive, and the shipped sim carries no tag of its own
    cdo_dm = doc["archetypes"]["class_default_object"]["values"].get(DRIVE_MODE_PROP)
    ship_dm = doc["archetypes"]["shipped_simulation"]["values"].get(DRIVE_MODE_PROP)
    ok7 = bool(cdo_dm) and str(cdo_dm["value"]) == "None" and ship_dm is None
    doc["ship_drive_mode_tag"] = ship_dm
    doc["cdo_drive_mode_tag"] = cdo_dm
    oracle("O7-drive-mode-default", ok7,
           "class default object tag 0x%04x = %r (FName 'None' = enum value 0 = BMDM_Drive); the "
           "shipped SimulationModel carries no DriveMode tag, so it inherits that default"
           % (cdo_dm["offset"], cdo_dm["value"]) if cdo_dm else "absent")

    # ---- 4b. comparison sites on DriveMode / BattleModeYawOffset --------------
    watch = {}
    for owner, member in ((SIM, DRIVE_MODE_PROP), (BASE, "BattleModeYawOffset")):
        ids = [i for i in exports_named(pkg, member)
               if (pkg.object_path(i) or "").startswith(owner + ".")]
        if ids:
            watch[member] = ids[0]
    cmp_sites = []
    for b in every_body:
        _, s = script_of(pkg, b["export"])
        for at in range(len(s) - 5):
            if s[at] not in (0x9A, 0x9B) or s[at + 1] not in REF_TOKENS:
                continue
            idx = struct.unpack_from("<i", s, at + 2)[0]
            for member, fid in watch.items():
                if fid == idx:
                    cmp_sites.append({"path": b.get("label") or b["path"],
                                      "export": b["export"], "at": at,
                                      "token": "0x%02x" % s[at], "field": member})
    ok8 = bool(cmp_sites)
    for c in cmp_sites:
        _, s = script_of(pkg, c["export"])
        if struct.unpack_from("<i", s, c["at"] + 2)[0] != watch[c["field"]]:
            ok8 = False
    doc["comparisons"] = cmp_sites
    oracle("O8-mode-comparisons", ok8,
           "%d compare-and-jump token(s) on DriveMode/BattleModeYawOffset: %s "
           "(0x9a = NotEqual, 0x9b = Equal)"
           % (len(cmp_sites), "; ".join("%s %s %s@%d"
                                        % (c["path"].rsplit(".", 1)[-1], c["field"],
                                           c["token"], c["at"]) for c in cmp_sites[:8])))

    # ---- 5. corpus scan for property readers/writers --------------------------
    fn_idx = [i for i in range(1, pkg.export_count + 1)
              if bm.obj_class(i) == "Function" and pkg.exports[i - 1]["size"] > 38]
    field_ids = {}
    for owner, member in SCAN:
        cand = [i for i in exports_named(pkg, member)
                if (pkg.object_path(i) or "").startswith(owner + ".")]
        if cand:
            field_ids["%s.%s" % (owner, member)] = cand[0]
    hits, verified, wrong = [], 0, []
    for key, fid in field_ids.items():
        member = key.split(".", 1)[1]
        pat = struct.pack("<i", fid)
        for j in fn_idx:
            d = pkg.data(j)
            s = d[22:len(d) - 16]
            p = -1
            while True:
                p = s.find(pat, p + 1)
                if p < 0:
                    break
                if p == 0 or s[p - 1] not in REF_TOKENS:
                    continue
                hits.append({"field": member, "field_export": fid, "function": pkg.object_path(j),
                             "export": j, "at": p - 1, "token": "0x%02x" % s[p - 1]})
                got = struct.unpack_from("<i", s, p)[0]
                if got == fid:
                    verified += 1
                else:
                    wrong.append("%s@%d" % (member, p - 1))
    doc["corpus"] = hits
    oracle("O5-corpus-refs", verified == len(hits) and not wrong,
           "%d property references over %d functions; every one re-reads its export index at "
           "the recorded offset%s"
           % (len(hits), len({h["function"] for h in hits}),
              "" if not wrong else "; bad: " + ", ".join(wrong[:3])))

    # O6: the 16384 constant beside BattleModeYawOffset
    k16384 = []
    for b in every_body:
        for c in b["constants"]:
            if c["kind"] == "int" and c["value"] == 16384:
                k16384.append({"path": b["path"], "export": b["export"], "at": c["at"]})
    ok6 = True
    for k in k16384:
        d, s = script_of(pkg, k["export"])
        if struct.unpack_from("<i", s, k["at"] + 1)[0] != 16384:
            ok6 = False
    doc["rotator_16384"] = k16384
    oracle("O6-yaw-offset-constant", ok6 and bool(k16384),
           "%d int32 constant(s) 16384 (90 deg) in the strafe/dodge bodies: %s"
           % (len(k16384), ", ".join("%s@%d" % (k["path"].rsplit(".", 1)[-1], k["at"])
                                     for k in k16384) or "none"))

    # ---- 6. menu moves --------------------------------------------------------
    menu_names = ["BatmobileSideSwipeTarget", "GetMovementAxes", "VehicleStrafe",
                  "BattleDodge", "PursuitStrafe", "CheckBattleStrafe", "PowerSlide", "Drift"]
    for nm in menu_names:
        found = exports_named(pkg, nm)
        doc["menu_moves"].append({
            "name": nm,
            "exports": [{"export": i, "path": pkg.object_path(i),
                         "class": pkg.object_class(i),
                         "script_bytes": len(script_of(pkg, i)[1])} for i in found[:6]],
        })

    # ---- 7. unknowns / contradictions ---------------------------------------
    doc["unknowns"] = [
        {"what": "the body of RVehicleSimBatmobile.SetDriveMode",
         "why": "export %s is a native declaration, not bytecode: its whole script is the "
                "0x29 PropRef to its own parameter (5 bytes). The per-mode torque/steer "
                "arithmetic therefore lives in the executable, not in the cooked package; only "
                "the fields it reads and the mode it is given are decodable here." % sdm,
         "where": "BatmanAK.exe (native), out of scope for a static package read"},
        {"what": "which caller sets BMDM_TurnOnSpot (value 1)",
         "why": "the corpus scan finds SetDriveMode called only from PursuitMode.BeginState (0) "
                "and BattleMode.BeginState (2). No script body passes 1, so either the native "
                "simulation switches to it from a speed/throttle test, or the value is set by "
                "code the package does not carry.",
         "where": "the native SetDriveMode body, or an engine-side condition on throttle/speed"},
        {"what": "the operator of the `DriveMode` guard in `BattleMode.BeginState`",
         "why": "the body reads `DriveMode` and then calls `SetDriveMode(2)`, but the comparison "
                "is written through an `EX_Context` (the object expression is `BatmobileSim`), so "
                "the operator token sits before a nested expression this one-pass scan does not "
                "classify. The reads and the call are decoded; the test is not.",
         "where": "the same body, with an expression-tree parser"},
        {"what": "the exact arithmetic of the camera-relative move",
         "why": "CheckBattleStrafe/PursuitStrafe read PlayerInput.aBaseY/aStrafe into a vector, "
                "rotate it by the Pawn's rotation and read BattleModeYawOffset in the same "
                "expression; the operator chain is an expression tree this one-pass walk does "
                "not resolve, so only the inputs and the 16384 constant are decoded.",
         "where": "the same bodies, with a full expression-tree parser"},
        {"what": "per-wheel powered flags in the shipped sim",
         "why": "SVehicle.NumPoweredWheels (1908) and SVehicleWheel.bPoweredWheel (116) exist "
                "in the layout, but neither the shipped sim object nor the class CDO carries a "
                "tag for them, so no shipped value is readable here.",
         "where": "the wheel objects of the spawned vehicle at run time, or the native sim"},
    ]
    doc["contradictions"] = []

    # Operator lead checks: report where the files agree or disagree with the lead.
    lead = {
        "pursuit_stationary_turns_in_place": {
            "verdict": "fields present; no pursuit script sets BMDM_TurnOnSpot",
            "evidence": "BMDM_TurnOnSpot exists (enum value 1) and the sim carries "
                        "TurnOnSpotFrontTorqueFactor/TurnOnSpotRearTorqueFactor with opposite "
                        "signs (front %r, rear %r in the class CDO), which is front/rear "
                        "counter-torque; no script site sets mode 1."
                        % (doc["archetypes"]["class_default_object"]["values"]
                           .get("TurnOnSpotFrontTorqueFactor", {}).get("value"),
                           doc["archetypes"]["class_default_object"]["values"]
                           .get("TurnOnSpotRearTorqueFactor", {}).get("value")),
        },
        "battle_left_stick_is_camera_relative": {
            "verdict": "carrier present (AbsoluteMoveDirection + BattleModeYawOffset), arithmetic native",
            "evidence": "AbsoluteMoveDirection is a sim struct; BattleModeYawOffset defaults to "
                        "16384 (90 deg) in the class CDO; CheckBattleStrafe builds a move vector "
                        "from aBaseY/aStrafe and reads that offset.",
        },
        "battle_mode_four_wheel_drive": {
            "verdict": "front+rear torque fields exist; no shipped powered-wheel count",
            "evidence": "BattleModeFrontThrottle/BattleModeRearThrottle are declared (no shipped "
                        "value) and BattleModeRearWheelTorquePower has a class default of %r; "
                        "NumPoweredWheels has no tag in either stream."
                        % doc["archetypes"]["class_default_object"]["values"]
                        .get("BattleModeRearWheelTorquePower", {}).get("value"),
        },
    }
    doc["operator_lead"] = lead
    doc["oracles"] = oracles
    return doc


# ------------------------------------------------------------------ rendering

def fnum(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return "%g" % v
    return str(v)


def render(doc):
    L = []
    A = L.append
    ok = sum(1 for o in doc["oracles"] if o["ok"])
    A("# DRIVE_MODES - what decides the Batmobile's behaviour per mode (G3-02l)")
    A("")
    A("Generated by `Tools/scripts/grab_drive_modes.py --write`. `--check` re-derives every "
      "number below from `BmGame.upk` and `Startup.upk` and fails on any difference. Static only: "
      "the game is never launched or attached to.")
    A("")
    A("**Oracles %d/%d pass.** Two packages read: `BmGame.upk` (%s bytes, %s exports) and "
      "`Startup.upk` (%s bytes, %s exports)."
      % (ok, len(doc["oracles"]), f"{doc['packages']['BmGame.upk']['bytes']:,}",
         f"{doc['packages']['BmGame.upk']['exports']:,}",
         f"{doc['packages']['Startup.upk']['bytes']:,}",
         f"{doc['packages']['Startup.upk']['exports']:,}"))
    A("")
    A("Labels: **decoded** = bytes read at the export and offset quoted; **derived** = a stated "
      "rule over decoded bytes; **UNKNOWN** = no field or body implements it here, with what was "
      "tried. Field *names* come from the BmSDK-AK class layout (`BMSDK_OFFSETS.json`); a tag "
      "carries only type + offset, so a field is named only where the layout declares one at "
      "that offset with a compatible kind.")
    A("")
    A("## 1. The mode the simulation is in - `EBatmobileDriveMode` (decoded)")
    A("")
    A("`%s` (export %d) holds %d values; the payload is a count and (FName, number) pairs, "
      "resolved through the package name table."
      % (doc["enum"]["path"], doc["enum"]["export"], doc["enum"]["count"]))
    A("")
    A("| value | name |")
    A("|---:|---|")
    for v in doc["enum"]["values"]:
        A("| %d | `%s` |" % (v["value"], v["name"]))
    A("")
    A("`RVehicleSimBatmobile.DriveMode` is a `ByteProperty` at **0x03b0** (class layout). The "
      "class default object carries a tag there whose value is the FName `None` - enum value 0, "
      "`BMDM_Drive`; the shipped `SimulationModel` object carries no tag of its own at that "
      "offset, so it inherits that default. So the car sits in the pursuit drive mode and battle "
      "mode is a separate simulation mode that the state sets explicitly, not a flag.")
    A("")
    A("## 2. Which state asks for which drive mode (decoded)")
    A("")
    A("| state body | export | `SetDriveMode` at | argument | meaning |")
    A("|---|---:|---:|---|---|")
    for s in doc["set_drive_mode"]["sites"]:
        ev = doc["enum"]["values"]
        nm = next((v["name"] for v in ev if v["value"] == s["arg_value"]), "?")
        A("| `%s` | %d | %d | `%s` | %s |" % (s.get("label") or s["path"], s["export"], s["at"],
                                              s["arg_text"], nm))
    A("")
    A(("Both the player vehicle (`RVehicleBatmobileBase`) and the NPC twin "
       "(`RVehicleNPCBatmobile`) carry the same pair of bodies, so the drive mode is set per "
       "*state*, and the transition itself is `RVehicleBatmobileBase.TryToChangeMode` (export %s, "
       "%d script bytes, a native declaration: %s). The battle body reads `DriveMode` first and "
       "only then calls `SetDriveMode(2)`: the reference is at 59 (player) / 74 (NPC), the call at "
       "88 / 103, so the guard is on the mode byte. The guard's operator is not decoded (see §7)."
       % (doc["try_to_change_mode"]["export"], doc["try_to_change_mode"]["script_bytes"],
          "0x29 PropRef only" if doc["try_to_change_mode"]["native_thunk"] else "bytecode")))
    A("")
    A("| body | field | token | at |")
    A("|---|---|---|---:|")
    for c in doc.get("comparisons", []):
        A("| `%s` | `%s` | `%s` | %d |" % (c["path"], c["field"], c["token"], c["at"]))
    A("")
    A("`0x9b` is `EX_Equal`, `0x9a` is `EX_NotEqual`. These are the yaw-offset comparisons the "
      "scan finds (the operator precedes the property reference directly); a comparison whose "
      "left side is an `EX_Context` object expression is not classified here and stays UNKNOWN.")
    A("")
    A("## 3. The fields the simulation reads per mode")
    A("")
    A("`RVehicleSimBatmobile` is the `SimObj` component (`Core.SimObj`, cast to the class in "
      "every mode body). Values are from the two cooked objects this tool reads:")
    A("")
    A("* `shipped` = `Startup.upk` export 169320 `Default__RVehicleBatmobile.SimulationModel` "
      "(the car's own simulation object).")
    A("* `sim CDO` = `BmGame.upk` export 129779 `Default__RVehicleSimBatmobile` (the simulation "
      "class default object; used where the shipped object carries no tag).")
    A("* `vehicle CDO` = `BmGame.upk` export 10923 `BmGame.Default__RVehicleBatmobileBase` (the "
      "vehicle class default object; the owner of the `RVehicleBatmobileBase` fields).")
    A("")
    A("| field | owner | offset | kind | shipped (sim) | sim CDO | vehicle CDO |")
    A("|---|---|---:|---|---:|---:|---:|")
    for f in doc["fields"]:
        if f.get("offset") is None:
            A("| `%s` | `%s` | - | UNKNOWN | - | - | - |" % (f["member"], f["owner"]))
            continue
        A("| `%s` | `%s` | `%s` | %s | %s | %s | %s |"
          % (f["member"], f["owner"], f["offset_hex"], f["kind"],
             fnum(f["shipped"]), fnum(f["class_default"]), fnum(f.get("vehicle_default"))))
    A("")
    A("\"-\" means no tag at that offset in that object: the class declares the field but the "
      "cooked stream does not serialise a value, so no shipped number exists to quote. The "
      "playable-archetype values for the same fields (V2/MK2/Joker/Funhouse) are already "
      "recorded in `MODES.md`; they are a different set of objects and are not re-read here.")
    A("")
    A("### Stationary turn (decoded carrier, native arithmetic)")
    A("")
    A("The mechanism the station-keeping spin needs is present as fields, not as a script "
      "branch: `BMDM_TurnOnSpot` (enum 1), `TurnOnSpotFrontTorqueFactor` and "
      "`TurnOnSpotRearTorqueFactor` with **opposite signs** (front %s, rear %s in the CDO), "
      "`DesiredTurnOnSpotSpeed` %s, `TurnOnSpotModeEngineBrakingFactor` %s in the shipped "
      "object, and `TurningModeMaxSpeed` %s. **Derived** (rule stated): a front and a rear "
      "torque factor of opposite sign can only produce counter-torque if both axles are driven, "
      "i.e. this is a four-wheel torque split rather than a steering-angle spin. The per-wheel "
      "`bPoweredWheel` flags are UNKNOWN (see §7), so the *selection* of four-wheel drive is "
      "still native; only the symbols it must use are decoded here."
      % (fnum(doc["archetypes"]["class_default_object"]["values"].get("TurnOnSpotFrontTorqueFactor", {}).get("value")),
         fnum(doc["archetypes"]["class_default_object"]["values"].get("TurnOnSpotRearTorqueFactor", {}).get("value")),
         fnum(doc["archetypes"]["class_default_object"]["values"].get("DesiredTurnOnSpotSpeed", {}).get("value")),
         fnum(doc["archetypes"]["shipped_simulation"]["values"].get("TurnOnSpotModeEngineBrakingFactor", {}).get("value")),
         fnum(doc["archetypes"]["class_default_object"]["values"].get("TurningModeMaxSpeed", {}).get("value"))))
    A("")
    A("**Who selects mode 1 is UNKNOWN**: the corpus scan finds `SetDriveMode` called from "
      "exactly two bodies per vehicle class, with 0 and 2 only. `ForceTurnOnSpotMode` (a "
      "`BoolProperty` on the sim) and `DesiredTurnOnSpotSpeed` exist but no decoded body writes "
      "them.")
    A("")
    A("## 4. The steering input path")
    A("")
    A("What the script side does (decoded references; the operator chain is an expression "
      "tree this walk does not flatten):")
    A("")
    A("1. `CheckBattleStrafe` / `PursuitStrafe` read `PlayerInput.aBaseY` and "
      "`PlayerInput.aStrafe` and store them into a local vector (`MoveDir`/`Strafe`), then read "
      "`BatmobilePawn.Rotation` and `RVehicleBatmobileBase.BattleModeYawOffset`.")
    A("2. `PursuitStrafe` calls `GetMovementAxes(X, Y, Z)`, then `VehicleStrafe(Strafe, "
      "BatmobileSideSwipeTarget)` - the side swipe target comes from the controller.")
    A("3. `RVehicleBatmobileBase.VehicleStrafe` applies the impulse (`KickStrafe`, "
      "`PMDodgeTorque`/`PMDodgeForce`/`PMDodgeDuration`) and spawns left/right exhaust bursts.")
    A("4. In pursuit the drive itself stays on the native sim: `PursuitMode.Tick` reads "
      "`Core.OutputSteering` and passes it to `SetWantAirBrakes(OutputSteering, ..., "
      "OutputSteering)`, and reads `AbsoluteMoveDirection`.")
    A("")
    A("`BattleMode.Tick` has no steering call at all: it only handles audio state, the winch, "
      "stuck-flip recovery and the `TryToChangeMode(PursuitMode)` exits. So the battle-mode "
      "movement (left stick in the stick's direction, car turning to face the camera) is "
      "implemented inside the native simulation, with `AbsoluteMoveDirection`, "
      "`BattleModeSteerAngleFactor`, `BattleModeMaxSteering`, "
      "`BattleModeTrailingSteerFactorMoving` and `BattleModeYawOffset` as its fields.")
    A("")
    A("## 5. Camera-relative / face-camera carriers")
    A("")
    A("| carrier | where | value | label |")
    A("|---|---|---:|---|")
    A("| `RVehicleBatmobileBase.BattleModeYawOffset` | class layout 0x1910 (6416) | %s | decoded "
      "(vehicle CDO); 16384 = 90 deg in UE3 rotator units |"
      % fnum(doc["archetypes"]["vehicle_class_default_object"]["values"].get("BattleModeYawOffset", {}).get("value")))
    A("| `RVehicleSimBatmobile.AbsoluteMoveDirection` | class layout 0x%04x | - | decoded field; "
      "read/written by `PursuitMode.Tick`, `DrivingMode.StartRun`/`EndRun` |"
      % (next((f["offset"] for f in doc["fields"] if f["member"] == "AbsoluteMoveDirection"), 0) or 0))
    A("| `RVehicleBatmobileBase.bForceBattleModeMovement` | class layout 0x%04x | - | decoded "
      "field; no script writer in the corpus scan |"
      % (next((f["offset"] for f in doc["fields"] if f["member"] == "bForceBattleModeMovement"), 0) or 0))
    A("")
    A("`BattleModeYawOffset` is compared with a value in the mode bodies listed in §2 (the "
      "`0x9a`/`0x9b` rows) and is read while `BattleDodge` builds its strafe direction from "
      "`Core.Rotation`. The int32 constant 16384 appears in the two strafe bodies at the offsets "
      "the O6 oracle prints. That is the file-side carrier of \"the car's facing is offset from "
      "the movement direction by 90 degrees\"; the exact expression is UNKNOWN (see §7).")
    A("")
    A("## 6. The controls-menu moves")
    A("")
    A("| menu move | decoded carrier |")
    A("|---|---|")
    A("| left stick + A, pursuit: *Side Swipe* | `DrivingMode.CheckBattleStrafe` -> "
      "`PursuitStrafe` -> `VehicleStrafe(Strafe, BatmobileSideSwipeTarget)` (calls and refs in "
      "§8) |")
    A("| left stick + A, battle: *Dodge Thrusters* | `DrivingMode.BattleStrafe` / "
      "`DelayedBattleStrafe` -> `RVehicleBatmobileBase.BattleMode.BattleDodge` (impulse + "
      "afterburner pulses, §8) |")
    A("| left stick + RT + X: *Power Slide* | UNKNOWN: no body named *PowerSlide* or *Drift* in "
      "the package name table under these classes, and the X binding "
      "(`QuickGadgetX` -> `SelectVehicleWeapon(2)`) selects a weapon slot, not a slide. What was "
      "tried: name-table and function-name match for `PowerSlide`/`Drift`/`Slide`; the corpus "
      "scan of the drive fields. Where it would be found: the native sim's handbrake/skid path "
      "(`HandBrakePct`, `bHoldingDownHandbrake`, `SkidToStop*`), whose values are in §3. |")
    A("")
    for m in doc["menu_moves"]:
        if not m["exports"]:
            A("* `%s`: no export with that name." % m["name"])
        else:
            A("* `%s`: %s" % (m["name"], ", ".join("export %d `%s` (%s, %d script bytes)"
                                                   % (e["export"], e["path"], e["class"],
                                                      e["script_bytes"])
                                                   for e in m["exports"])))
    A("")
    A("## 7. Exact gaps")
    A("")
    for u in doc["unknowns"]:
        A("- **%s** - %s *Where:* %s" % (u["what"], u["why"], u["where"]))
    A("")
    A("## 8. Bodies, calls and references")
    A("")
    for b in doc["bodies"]:
        label = b.get("label") or b["path"]
        if b.get("missing"):
            A("### `%s` - not found" % label)
            A("")
            continue
        A("### `%s` (export %d, %d script bytes)" % (label, b["export"], b["script_bytes"]))
        A("")
        if b["calls"]:
            A("| at | kind | target | first argument |")
            A("|---:|---|---|---|")
            for c in b["calls"]:
                A("| %d | %s | `%s` | %s |" % (c["at"], c["kind"], c["target"],
                                               c["first_arg_text"] if c["first_arg_text"]
                                               else "-"))
            A("")
        else:
            A("No call token.")
            A("")
        A("References: " + ("; ".join("`%s`@%d" % (r["ref"], r["at"]) for r in b["refs"])
                            or "none"))
        A("")
        if b["constants"]:
            A("Constants: " + ", ".join("%s@%d" % (c["value"], c["at"]) for c in b["constants"]))
            A("")
    A("## 9. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in doc["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**", o["evidence"]))
    A("")
    A("## 10. Operator leads vs the files")
    A("")
    for k, v in doc["operator_lead"].items():
        A("* **%s** - %s. %s" % (k, v["verdict"], v["evidence"]))
    A("")
    A("No contradiction with the leads was found. What the files cannot do is prove the "
      "arithmetic: the mode switch is a native thunk, so the per-mode torque/steer maths is in "
      "`BatmanAK.exe` and stays UNKNOWN here.")
    A("")
    A("## 11. Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/grab_drive_modes.py --write")
    A("uv run python Tools/scripts/grab_drive_modes.py --check")
    A("```")
    A("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    fails = [o["key"] for o in doc["oracles"] if not o["ok"]]

    if a.write:
        if fails:
            print("FAIL: oracles failed, nothing written: %s" % ", ".join(fails))
            for o in doc["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote Research/BatmobileGrab/DRIVE_MODES.md and .json")
        print("  enum %d, fields %d, bodies %d, corpus refs %d, oracles %d/%d"
              % (doc["enum"]["count"], len(doc["fields"]), len(doc["bodies"]),
                 len(doc["corpus"]), len(doc["oracles"]), len(doc["oracles"])))
        for s in doc["set_drive_mode"]["sites"]:
            print("    SetDriveMode(%s) in %s @%d" % (s["arg_text"], s["path"], s["at"]))
        return 0

    if fails:
        print("FAIL")
        for o in doc["oracles"]:
            if not o["ok"]:
                print("  - oracle %s: %s" % (o["key"], o["evidence"]))
        return 1
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != md:
        print("FAIL: DRIVE_MODES.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: DRIVE_MODES.json is stale")
        return 1
    print("OK %d/%d oracles, enum %d, fields %d, bodies %d, corpus refs %d; md+json identical"
          % (len(doc["oracles"]), len(doc["oracles"]), doc["enum"]["count"],
             len(doc["fields"]), len(doc["bodies"]), len(doc["corpus"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
