"""grab_modes.py - modes and transformation values, with units (G1-21).

The mode families live in three places at once:

  `BMSDK_OFFSETS.json`  the *declared* inventory - every field the BmSDK-AK dump names on the
                        class, with its absolute offset and type (the same number space as the
                        cooked `FPropertyTagBat2.Offset`).
  `objects.jsonl`      the *cooked* values - each package's archetype tags, so a field is either
                        serialized in a package or it is not, per package.
  `OFFSETS.json`       GRB-11's naming evidence, and the row class each declaring class actually
                        cooked under (`RVehicleBatmobileBase` fields arrive on `RVehicleBatmobile`
                        rows), which is what makes the offset lookup class-scoped: the same
                        offset means different members in different classes.

Units are read from the field's name under UE3 conventions (time in seconds, length in cm, speed
in cm/s, a plain float angle in degrees); torque/force/impulse/power magnitudes are engine
quantities with no documented conversion and are carried as shipped; anything the name does not
say is `undocumented` rather than guessed. Nothing is rescaled.

The ledger rows that this card serves (T-BM1, T-AC1, T-RA1, T-SR1 in `T_ROWS.jsonl`) are parsed
out of the ledger itself, and `--check` fails unless every field they name - including the quoted
numbers - appears in the generated record.

Usage:
    python Tools/scripts/grab_modes.py --write
    python Tools/scripts/grab_modes.py --check
"""
import argparse
import collections
import json
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
LEDGER = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")

SCHEMA = 1
GENERATOR = "grab_modes.py"

# The families the card asks for, as prefix matches on the declared field name.
FAMILIES = [
    "BattleMode", "TurnOnSpot", "Strafe", "Transformation", "TurningModeMaxSpeed",
    "ArmourModeDamageReduction", "AirControl", "JumpRamp", "JumpNoRamp", "KillFlip",
    "KillKeepyUp", "PMDodge", "BattleDodgeImpulse", "StayUpright", "VehicleShovingTorque",
    "ImpactRoadAssist", "ImpactShake",
]

# Package -> the short name used in every table.
PACKAGES = [
    ("Playable_Batmobile_SF", "V2"),
    ("Playable_BatmobileMK2_SF", "MK2"),
    ("Playable_BatmobileJoker_SF", "Joker"),
    ("Playable_BatmobileFunhouse_SF", "Funhouse"),
]

# Where a field's scope sits, by declaring class.
SCOPE = {
    "RVehicleBatmobileBase": "vehicle",
    "SVehicle": "vehicle (engine base class)",
    "RVehicleBatmobile": "vehicle",
    "RVehicleSimBatmobile": "simulation",
    "SVehicleSimBase": "simulation (engine base class)",
    "SVehicleSimCar": "simulation (engine base class)",
    "RVehicleSimCar": "simulation (engine base class)",
    "SVehicleWheel": "wheel (engine base class)",
    "R3rdPersonCamera": "camera",
    "Pawn": "engine base class",
    "RVehicle": "vehicle (engine base class)",
}

# Declared type -> the cooked tag types that can hold it. An unmapped declared type is accepted
# only as an object/struct tag, never as a number, so an offset collision cannot fake a value.
TAG_TYPES = {
    "float": {"FloatProperty"},
    "int": {"IntProperty"},
    "bool": {"BoolProperty"},
    "FName": {"NameProperty"},
    "FString": {"StrProperty"},
    "Vector3": {"VectorProperty"},
    "Rotator": {"RotatorProperty"},
    "FInterpCurveFloat": {"StructProperty"},
    "FBMScreenShakeStruct": {"StructProperty"},
    "FFreeCameraConfig": {"StructProperty"},
}
OBJECT_TAG_TYPES = {"ObjectProperty", "ObjectNCRProperty", "ClassProperty"}
STRUCT_TAG_TYPES = {"StructProperty"}

# Unit per field, plus where the unit comes from:
#   conv   the field's name under UE3 conventions (s / cm / cm/s / deg / factor)
#   engine an engine torque/force/impulse/power magnitude, no documented conversion
#   type   the slot type says what it is (ref, name, bool, struct, curve)
#   none   the name does not say what the number counts - reported raw, never guessed
UNITS = {
    # --- vehicle class -------------------------------------------------------
    "StayUprightConstraintSetup": ("object ref", "type"),
    "StayUprightConstraintInstance": ("object ref", "type"),
    "TransformationReverseDirectionIntoPursuitModeSound": ("AkEvent ref", "type"),
    "TransformationReverseDirectionIntoBattleModeSound": ("AkEvent ref", "type"),
    "BattleModePrimaryWeapon": ("object ref", "type"),
    "BattleModeYawOffset": ("undocumented", "none"),
    "BattleModeTransformationAnimName": ("name", "type"),
    "BattleModeWidth": ("cm", "conv"),
    "BattleModeLength": ("cm", "conv"),
    "BattleModeHeight": ("cm", "conv"),
    "BattleModeSpeedDelta": ("cm/s", "conv"),
    "BattleModeImpactMaxDamageSpeed": ("cm/s", "conv"),
    "BattleModeImpactMinDamageSpeed": ("cm/s", "conv"),
    "BattleModeImpactMaxDamagePow": ("factor", "conv"),
    "BattleDodgeImpulse": ("engine impulse", "engine"),
    "ArmourModeDamageReduction": ("int, undocumented scale", "none"),
    "JumpRampUpwardForce": ("engine force", "engine"),
    "JumpRampRightingTorque": ("engine torque", "engine"),
    "JumpNoRampRightingTorque": ("engine torque", "engine"),
    "KillFlipTorque": ("engine torque", "engine"),
    "KillFlipTorqueDuration": ("s", "conv"),
    "KillKeepyUpFactor": ("factor", "conv"),
    "KillKeepyUpFactorDuration": ("s", "conv"),
    "ImpactShake": ("struct", "type"),
    "ImpactShakeForceFactor": ("factor", "conv"),
    "ImpactShakeVehicleFactor": ("factor", "conv"),
    "ImpactShakeAbandonedVehicleFactor": ("factor", "conv"),
    "ImpactShakeDestructiblesFactor": ("factor", "conv"),
    "ImpactShakeCoolDown": ("s", "conv"),
    "VehicleShovingTorque": ("engine torque", "engine"),
    "PMDodgeTorque": ("engine torque", "engine"),
    "PMDodgeForce": ("engine force", "engine"),
    "PMDodgeDuration": ("s", "conv"),
    "ImpactRoadAssistTimer": ("s", "conv"),
    "ImpactRoadAssistSceneryDuration": ("s", "conv"),
    "ImpactRoadAssistEnemyDuration": ("s", "conv"),
    "ImpactRoadAssistFactor": ("engine gain", "engine"),
    "ImpactRoadAssistMaxTorque": ("engine torque", "engine"),
    "ImpactRoadAssistMaxAngle": ("deg", "conv"),
    "ImpactRoadAssistAngVelocityTime": ("s", "conv"),
    "ImpactRoadAssistSteeringFactor": ("factor", "conv"),
    "ImpactRoadAssistLookAheadTime": ("s", "conv"),
    "ImpactRoadAssistAngleStrength": ("engine gain", "engine"),
    # --- simulation class ----------------------------------------------------
    "TurnOnSpotFrontTorqueFactor": ("factor", "conv"),
    "TurnOnSpotRearTorqueFactor": ("factor", "conv"),
    "TurnOnSpotModeEngineBrakingFactor": ("factor", "conv"),
    "TurnOnSpotSteeringSpeedCurve": ("curve (cm/s -> factor)", "type"),
    "BattleModeVSpeedCurve": ("curve (cm/s -> factor)", "type"),
    "BattleModeMoving": ("bool", "type"),
    "TurningModeMaxSpeed": ("cm/s", "conv"),
    "BattleModeMaxSteering": ("deg", "conv"),
    "BattleModeRearWheelTorquePower": ("engine torque", "engine"),
    "BattleModeLatSlipScale": ("factor", "conv"),
    "BattleModeLongSlipScale": ("factor", "conv"),
    "BattleModeEngineBrakingFactor": ("factor", "conv"),
    "BattleModeTurnOnSpotTorqueFactor": ("factor", "conv"),
    "BattleModeFrontThrottle": ("factor", "conv"),
    "BattleModeRearThrottle": ("factor", "conv"),
    "BattleModeThrottleSpeed": ("undocumented (rate-sized)", "none"),
    "BattleModeMaxSpeed": ("cm/s", "conv"),
    "BattleModeDriveForceFactor": ("engine gain", "engine"),
    "BattleModeStopAndTurnAngleStationary": ("deg", "conv"),
    "BattleModeStopAndTurnAngleMoving": ("deg", "conv"),
    "BattleModeSteerAngleFactor": ("factor", "conv"),
    "BattleModeTrailingSteerFactorTurnOnSpot": ("factor", "conv"),
    "BattleModeTrailingSteerFactorMoving": ("factor", "conv"),
    "BattleModeDrivingForceZOffset": ("cm", "conv"),
    "BattleModeUprightTorqueFactor": ("factor", "conv"),
    "BattleModeUprightMaxTorque": ("engine torque", "engine"),
    "BattleModeSteerBiasRate": ("undocumented", "none"),
    "TransformationRotation": ("deg (rotator)", "conv"),
    "TransformationTurnTorqueFactor": ("engine gain", "engine"),
    "TransformationTurnDecelTorqueFactor": ("engine gain", "engine"),
    "TransformationTurnOnSpotSpeed": ("cm/s", "conv"),
    "TransformationTurnFactor": ("factor", "conv"),
    "AirControlYawTorqueFactorMax": ("engine torque gain", "engine"),
    "AirControlPitchTorqueFactorMax": ("engine torque gain", "engine"),
    "AirControlYawTorqueFactorMin": ("engine torque gain", "engine"),
    "AirControlPitchTorqueFactorMin": ("engine torque gain", "engine"),
    "AirControlInterpTime": ("s", "conv"),
    "AirControlTimeInAir": ("s", "conv"),
    "BattleModeSlopeFactor": ("factor", "conv"),
    # --- other declaring classes --------------------------------------------
    "AirControl": ("engine value", "none"),
    "AirControlTurnTorque": ("engine torque", "engine"),
    "BattleModeSteerBias": ("factor", "conv"),
    "StrafeCooldown": ("s", "conv"),
    "StrafeRight": ("cm (vector)", "conv"),
    "StrafeForce": ("engine force", "engine"),
    "StrafeTorque": ("engine torque", "engine"),
    "StrafeDuration": ("s", "conv"),
    "StrafeTime": ("s", "conv"),
    "StrafeFwdCorrectionForce": ("engine force", "engine"),
    "StrafeTarget": ("object ref", "type"),
    "TransformationAnimNode": ("object ref", "type"),
    "StayUprightRollResistAngle": ("deg", "conv"),
    "StayUprightPitchResistAngle": ("deg", "conv"),
    "StayUprightStiffness": ("engine stiffness", "engine"),
    "StayUprightDamping": ("engine damping", "engine"),
    "BattleModeCamConfig": ("struct", "type"),
    "BattleModeWinchCamConfig": ("struct", "type"),
    "BattleModeAbseilingCamConfig": ("struct", "type"),
    "BattleModeCamFOV": ("deg", "conv"),
    "BattleModeWinchCamFOV": ("deg", "conv"),
    "BattleModeHeadOffset": ("cm (vector)", "conv"),
    "BattleModeWinchHeadOffset": ("cm (vector)", "conv"),
    "BattleModeAbseilingExtraCameraRot": ("deg (rotator)", "conv"),
}

LEDGER_ROWS = ["T-BM1", "T-AC1", "T-RA1", "T-SR1"]


def family(name):
    for f in FAMILIES:
        if name.startswith(f):
            return f
    return None


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def sdk_inventory(doc):
    """[(declaring class, field name, offset, declared type)] for every family field."""
    out = []
    for cls, entry in sorted(doc.get("classes", {}).items()):
        for p in entry.get("properties") or []:
            name = p.get("name") or ""
            if family(name):
                out.append({"declaring_class": cls, "field": name,
                            "offset": p.get("offset"), "declared_type": p.get("type")})
    return out


def row_classes(inventory, offsets_doc):
    """declaring class -> the object classes its fields were cooked on (GRB-11's own evidence)."""
    by_name = {}
    for row in inventory:
        by_name.setdefault(row["field"], set()).add(row["declaring_class"])
    out = collections.defaultdict(set)
    for e in offsets_doc.get("fields", []):
        name = e.get("field_name")
        if not name:
            continue
        for decl in by_name.get(name, ()):
            out[decl].add(e.get("class"))
    for row in inventory:
        out[row["declaring_class"]].add(row["declaring_class"])
    return {k: sorted(v) for k, v in out.items()}


def tag_types_for(declared):
    if declared in TAG_TYPES:
        return TAG_TYPES[declared]
    if declared in ("FInterpCurveFloat",) or (declared or "").startswith("F"):
        return STRUCT_TAG_TYPES | OBJECT_TAG_TYPES
    return OBJECT_TAG_TYPES | STRUCT_TAG_TYPES


def curve_points(tag):
    """[(InVal, OutVal)] out of a cooked InterpCurve float's Points array."""
    points = []
    for prop in tag.get("props") or []:
        if not prop.get("items"):
            continue
        for item in prop["items"]:
            vals = {p.get("offset"): p.get("value") for p in item if "offset" in p}
            if 0 in vals and 4 in vals:
                points.append([vals[0], vals[4]])
    return points


def struct_props(tag):
    """The decoded members of a struct tag, as (offset, type, value) rows."""
    out = []
    for prop in tag.get("props") or []:
        if "items" in prop:
            out.append({"offset": prop.get("offset"), "type": "array",
                        "count": prop.get("count"), "value": None})
        elif "nested" in prop:
            out.append({"offset": prop.get("offset"), "type": "nested",
                        "value": (prop.get("name") or "nested")})
        else:
            out.append({"offset": prop.get("offset"), "type": prop.get("type"),
                        "value": prop.get("value")})
    return out


def build():
    inv = sdk_inventory(read_json(os.path.join(OUT, "BMSDK_OFFSETS.json")))
    offsets_doc = read_json(os.path.join(OUT, "OFFSETS.json"))
    scope = row_classes(inv, offsets_doc)

    # GRB-11's named offsets, so the cooked values it already published can be cross-checked.
    named = {}
    for e in offsets_doc.get("fields", []):
        if e.get("field_name"):
            named.setdefault(e["field_name"], []).append(e)

    rows_by_class = collections.defaultdict(list)
    with open(os.path.join(OUT, "objects.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            rows_by_class[r.get("class")].append(r)

    fields = []
    for row in inv:
        classes = scope.get(row["declaring_class"], [row["declaring_class"]])
        want_types = tag_types_for(row["declared_type"])
        per_pkg = collections.OrderedDict()
        struct = None
        hits = []
        for cls in classes:
            for r in rows_by_class.get(cls, []):
                for t in r.get("tags") or []:
                    named_seg = (t.get("name") or "").split(".")[-1]
                    same_name = named_seg == row["field"]
                    if not same_name and t.get("offset") != row["offset"]:
                        continue
                    if t.get("type") not in want_types:
                        continue
                    if not same_name and t.get("type") in ("VectorProperty", "RotatorProperty") \
                            and row["declared_type"] not in ("Vector3", "Rotator"):
                        continue
                    hits.append((r, t))
                    if r.get("package") in dict(PACKAGES):
                        per_pkg[r["package"]] = t.get("value")
                    if t.get("type") == "StructProperty" and struct is None:
                        struct = {"declared_type": row["declared_type"],
                                  "points": curve_points(t),
                                  "props": struct_props(t)}
        unit, basis = UNITS.get(row["field"], ("undocumented", "none"))
        cooked = [(pkg, per_pkg.get(pkg)) for pkg, _short in PACKAGES if pkg in per_pkg]
        entry = {
            "family": family(row["field"]),
            "field": row["field"],
            "declaring_class": row["declaring_class"],
            "scope": SCOPE.get(row["declaring_class"], "unknown"),
            "offset": row["offset"],
            "declared_type": row["declared_type"],
            "unit": unit,
            "unit_basis": basis,
            "serialized": bool(hits),
            "occurrences": len(hits),
            "packages": [p for p, _v in cooked],
            "values": {p: v for p, v in cooked},
            "same_in_all_four": len(cooked) == 4 and len({json.dumps(v) for _p, v in cooked}) == 1,
            "struct": struct,
            "named_by_sdk": bool(named.get(row["field"])),
        }
        fields.append(entry)

    fields.sort(key=lambda e: (e["declaring_class"], e["offset"], e["field"]))

    # ---- cross-check against GRB-11 -------------------------------------
    cross = []
    for e in fields:
        ref = named.get(e["field"]) or []
        if not ref:
            continue
        want = {json.dumps(v) for r in ref for v in r.get("values", [])}
        got = {json.dumps(v) for v in e["values"].values()}
        cross.append((e["field"], sorted(want - got) == [], len(want), len(got)))

    # ---- the ledger rows this card serves -------------------------------
    ledger = []
    if os.path.isfile(LEDGER):
        with open(LEDGER, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        for r in rows:
            if r.get("id") not in LEDGER_ROWS:
                continue
            # Only the requirement cell names BmAK fields; the dispo/why cells quote the JC3
            # carrier ("the fleet's only air member is `takeoff_pitch_damping`") and are not
            # fields of this grab. The row's disposition is another card's decision record, so
            # it is not stored here: a later change to it must not stale this artifact.
            cells = r.get("cells", [])
            text = str(cells[1]) if len(cells) > 1 else ""
            tokens = re.findall(r"`([^`]+)`", text)
            numbers = [float(x) for x in re.findall(r"(?<![\w.])(\d{3,})(?![\w.])", text)]
            counts = dict(zip(tokens, [int(x) for x in
                                       re.findall(r"`[^`]+`\s*\((\d+)\)", text)]))
            ledger.append({"id": r["id"], "tokens": tokens, "numbers": numbers,
                           "counts": counts})

    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    for item in ledger:
        for token in item["tokens"]:
            # `StayUprightConstraintSetup/Instance` names two fields in one token, and the
            # second half is shorthand for the rest of the field name
            parts = token.split("/") if "/" in token else [token]
            for core in parts:
                if core.endswith("*"):
                    prefix = core[:-1]
                    hits = [f for f in fields if f["field"].startswith(prefix)]
                    ser = [h for h in hits if h["serialized"]]
                    check("%s: %s*" % (item["id"], prefix), bool(ser),
                          "%d fields, %d serialized" % (len(hits), len(ser)))
                else:
                    hits = ([f for f in fields if f["field"] == core] or
                            [f for f in fields if f["field"].endswith(core)])
                    ser = [h for h in hits if h["serialized"]]
                    name = hits[0]["field"] if hits else core
                    check("%s: %s" % (item["id"], name), bool(ser),
                          "serialized=%s%s" % (bool(ser), "" if ser else
                                               " (declared only, no value in the files)"))
        # The Done line says "appears with its value": the parenthetical counts the ledger
        # writes are the serialised *scalar* members on the simulation class (a curve member is
        # not one of them), so assert the two agree instead of only printing them.
        for tok, n in item["counts"].items():
            prefix = tok[:-1] if tok.endswith("*") else tok
            hits = [f for f in fields if f["field"].startswith(prefix)]
            ser = [f for f in hits if f["serialized"] and f["scope"].startswith("simulation")
                   and f["declared_type"] != "FInterpCurveFloat"]
            check("%s: count %s = %d" % (item["id"], tok, n), len(ser) == n,
                  "%d serialised simulation scalars" % len(ser))
        # quoted numbers (T-AC1's 8000, T-RA1's 90000/30000/2000, ...)
        for num in item["numbers"]:
            found = False
            for f in fields:
                for v in f["values"].values():
                    if isinstance(v, (int, float)) and abs(float(v) - num) < 1e-6:
                        found = True
            check("%s: value %g" % (item["id"], num), found)

    check("GRB-11 cross-check", all(ok for _n, ok, _a, _b in cross),
          "%d/%d named fields agree" % (sum(1 for _n, ok, _a, _b in cross if ok), len(cross)))
    check("units assigned", all(f["unit"] for f in fields),
          "%d undocumented" % sum(1 for f in fields if f["unit_basis"] == "none"))

    doc = {
        "schema": SCHEMA,
        "generated_by": GENERATOR,
        "families": FAMILIES,
        "packages": [{"package": p, "short": s} for p, s in PACKAGES],
        "fields": fields,
        "summary": {
            "declared": len(fields),
            "serialized": sum(1 for f in fields if f["serialized"]),
            "not_serialized": sum(1 for f in fields if not f["serialized"]),
            "by_family": {fam: sum(1 for f in fields if f["family"] == fam) for fam in FAMILIES},
            "serialized_by_family": {fam: sum(1 for f in fields
                                              if f["family"] == fam and f["serialized"])
                                      for fam in FAMILIES},
            "same_in_all_four": sum(1 for f in fields if f["same_in_all_four"]),
            "undocumented_unit": sum(1 for f in fields if f["unit_basis"] == "none"),
        },
        "ledger_rows": ledger,
        "checks": checks,
    }
    return doc


def fmt_value(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return ("%.6g" % v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(fmt_value(x) for x in v) + "]"
    return str(v)


def write_markdown(doc):
    s = doc["summary"]
    shorts = [p["short"] for p in doc["packages"]]
    lines = []
    a = lines.append
    a("# Modes and transformation values - G1-21")
    a("")
    a("Generated by `Tools/scripts/grab_modes.py` from `BMSDK_OFFSETS.json` (what the classes")
    a("*declare*), `objects.jsonl` (what each package's archetype actually *serialises*) and")
    a("`OFFSETS.json` (GRB-11's naming evidence and the row class each declaring class cooked")
    a("under).")
    # An offset two declaring classes share is the reason the lookup is class-scoped; take the
    # pair from the record itself rather than naming one from memory.
    by_offset = collections.defaultdict(list)
    for f in doc["fields"]:
        by_offset[f["offset"]].append(f)
    pair = next(((off, es) for off, es in sorted(by_offset.items())
                 if len({e["declaring_class"] for e in es}) > 1), None)
    if pair:
        off, es = pair
        es = sorted(es, key=lambda e: (not e["serialized"], e["declaring_class"]))
        named = ["`%s` on `%s`" % (e["field"], e["declaring_class"]) for e in es]
        a(textwrap.fill(
            "The lookup is class-scoped on purpose: offset %#x is %s - one offset, %d members"
            " - so a bare offset match would read one field's number as another's."
            % (off, ", ".join(named[:-1]) + " and " + named[-1] if len(named) > 2
               else " and ".join(named), len(named)), 96))
    else:
        a("The lookup is class-scoped on purpose: this record shows no offset two declaring")
        a("classes share, but the same offset means different members across classes in general,")
        a("so a bare offset match could read one field's number as another's.")
    a("")
    a("| fact | value |")
    a("|---|---|")
    a("| declared family fields | **%d** |" % s["declared"])
    a("| serialised in the shipped archetypes | **%d** |" % s["serialized"])
    a("| declared but not serialised anywhere | **%d** |" % s["not_serialized"])
    a("| identical in all four packages | %d of the serialised |" % s["same_in_all_four"])
    a("| unit not documented by the field's name | %d |" % s["undocumented_unit"])
    a("")
    a("## Units")
    a("")
    a("| basis | meaning |")
    a("|---|---|")
    a("| `conv` | the field's name under UE3 conventions: seconds, centimetres, cm/s, plain-float")
    a("| | degrees, and `factor` for a value the name calls a factor/scale |")
    a("| `engine` | an engine torque / force / impulse / power magnitude - UE3 documents no")
    a("| | conversion, so the shipped number is carried as-is |")
    a("| `type` | the slot type says what it is: object ref, name, bool, struct, curve |")
    a("| `none` | the name does not say what the number counts: reported raw, **never guessed** |")
    a("")
    def one_value(name):
        for f in doc["fields"]:
            if f["field"] == name and f["values"]:
                return fmt_value(next(iter(f["values"].values())))
        return "—"

    a("Nothing here is rescaled. `BattleModeThrottleSpeed` (%s) and `BattleModeYawOffset` (%s) are"
      % (one_value("BattleModeThrottleSpeed"), one_value("BattleModeYawOffset")))
    a("`undocumented` for that reason.")
    a("")
    a("## Coverage by family")
    a("")
    a("| family | declared | serialised | not serialised |")
    a("|---|---|---|---|")
    for fam in FAMILIES:
        d = s["by_family"].get(fam, 0)
        if not d:
            continue
        ser = s["serialized_by_family"].get(fam, 0)
        a("| `%s*` | %d | %d | %d |" % (fam, d, ser, d - ser))
    a("")

    # ---- the counts T-BM1 writes in parentheses ---------------------------
    counted = [(i["id"], tok, i["counts"][tok])
               for i in doc["ledger_rows"] for tok in i["tokens"] if tok in i["counts"]]
    if counted:
        a("## The ledger's parenthetical counts")
        a("")
        rows_named = list(dict.fromkeys(rid for rid, _t, _n in counted))
        a(textwrap.fill(
            "%s writes %s. Those are **serialised** counts, and in each case the simulation"
            " class is what is being counted:"
            % (", ".join("`%s`" % r for r in rows_named),
               ", ".join("`%s` (%d)" % (tok, n) for _r, tok, n in counted)), 96))
        a("")
        a("| row | token | ledger | declared | serialised (sim) | serialised (vehicle) |")
        a("|---|---|---|---|---|---|")
        for rid, tok, n in counted:
            prefix = tok[:-1] if tok.endswith("*") else tok
            hits = [f for f in doc["fields"] if f["field"].startswith(prefix)]
            sim = [f for f in hits if f["scope"].startswith("simulation") and f["serialized"]]
            veh = [f for f in hits if f["scope"].startswith("vehicle") and f["serialized"]]
            a("| `%s` | `%s` | %d | %d | %d | %d |" % (rid, tok, n, len(hits), len(sim),
                                                        len(veh)))
        a("")
        bm_count = next((n for _r, tok, n in counted if tok == "BattleMode*"), None)
        bm_sim = [f for f in doc["fields"]
                  if f["field"].startswith("BattleMode") and f["scope"].startswith("simulation")
                  and f["serialized"]]
        curves = [f for f in bm_sim if f["declared_type"] == "FInterpCurveFloat"]
        scalars = [f for f in bm_sim if f["declared_type"] != "FInterpCurveFloat"]
        if bm_count is not None and curves and len(bm_sim) != bm_count:
            a(textwrap.fill(
                "The ledger's (%d) counts the scalars; the record carries %d of them plus %d curve"
                " member (`%s`, `%s`), so the serialised total on the simulation class is %d."
                % (bm_count, len(scalars), len(curves), curves[0]["field"],
                   curves[0]["declared_type"], len(bm_sim)), 96))
        a("")
        battle_veh = [f for f in doc["fields"]
                      if f["field"].startswith("BattleMode") and f["scope"].startswith("vehicle")
                      and f["serialized"]]
        a("The vehicle class carries the rest of the `BattleMode*` family (%d serialised fields"
          % len(battle_veh))
        a("on `RVehicleBatmobile`: the battle-mode primary weapon, the yaw offset and the")
        a("three-value impact-speed band), which is why this record counts more than the")
        a("ledger's (%s). `ArmourModeDamageReduction` carries its own prefix, so it is not part"
          % (bm_count if bm_count is not None else "scalar"))
        a("of that count - the row names it singly and the check above confirms its value.")
        a("")

    # ---- per class tables -------------------------------------------------
    order = ["RVehicleSimBatmobile", "RVehicleBatmobileBase", "RVehicleBatmobile", "SVehicle",
             "SVehicleWheel", "RVehicleSimCar", "SVehicleSimCar", "SVehicleSimBase",
             "R3rdPersonCamera", "Pawn"]
    titles = {
        "RVehicleSimBatmobile": "Simulation (`RVehicleSimBatmobile` -> `SimulationModel`)",
        "RVehicleBatmobileBase": "Vehicle class (`RVehicleBatmobileBase`, cooked on `RVehicleBatmobile`)",
        "RVehicleBatmobile": "Vehicle class (`RVehicleBatmobile`)",
        "SVehicle": "Engine base (`SVehicle`, cooked on `RVehicleBatmobile`)",
        "SVehicleWheel": "Wheel (`SVehicleWheel`)",
        "RVehicleSimCar": "Engine car sim (`RVehicleSimCar`)",
        "SVehicleSimCar": "Engine car sim (`SVehicleSimCar`)",
        "SVehicleSimBase": "Engine sim base (`SVehicleSimBase`)",
        "R3rdPersonCamera": "Camera (`R3rdPersonCamera` - served by the camera cards, not this one)",
        "Pawn": "Engine (`Pawn`)",
    }
    seen = set()
    for cls in order:
        rows = [f for f in doc["fields"] if f["declaring_class"] == cls]
        if not rows:
            continue
        seen.add(cls)
        a("## %s" % titles.get(cls, cls))
        a("")
        a("| field | offset | declared | unit | %s | serialised |" % " | ".join(shorts))
        a("|" + "---|" * (4 + len(shorts) + 1))
        for f in rows:
            cells = []
            for pkg_info in doc["packages"]:
                pkg = pkg_info["package"]
                cells.append(fmt_value(f["values"][pkg]) if pkg in f["values"] else "—")
            a("| `%s` | %#x | `%s` | %s | %s | %s |" % (
                f["field"], f["offset"], f["declared_type"], f["unit"],
                " | ".join(cells),
                "yes" if f["serialized"] else "no"))
        a("")
        missing = [f["field"] for f in rows if not f["serialized"]]
        if missing:
            a("Not serialised in any shipped archetype (%d): `%s`. The class declares them, the"
              % (len(missing), "` `".join(missing)))
            a("packages do not carry a tag at that offset, so **no value exists in the files** -")
            a("only the engine's or BmScript's default would be running.")
            a("")

    extra = [f for f in doc["fields"] if f["declaring_class"] not in seen]
    if extra:
        a("## Other declaring classes")
        a("")
        a("| field | declaring class | offset | unit | serialised |")
        a("|---|---|---|---|---|")
        for f in extra:
            a("| `%s` | `%s` | %#x | %s | %s |" % (
                f["field"], f["declaring_class"], f["offset"], f["unit"],
                "yes" if f["serialized"] else "no"))
        a("")

    # ---- structs and curves ------------------------------------------------
    structed = [f for f in doc["fields"] if f.get("struct") and f["struct"]["points"]]
    if structed:
        a("## Curves")
        a("")
        for f in structed:
            a("`%s` (%s, %d points, unit: %s)" % (f["field"], f["declaring_class"],
                                                   len(f["struct"]["points"]), f["unit"]))
            a("")
            a("| InVal | OutVal |")
            a("|---|---|")
            for p in f["struct"]["points"]:
                a("| %s | %s |" % (fmt_value(p[0]), fmt_value(p[1])))
            a("")
    shaken = [f for f in doc["fields"] if f["field"] == "ImpactShake" and f.get("struct")]
    for f in shaken:
        a("## `ImpactShake` (struct, declared `%s`, cooked on `RVehicleBatmobile`)"
          % f["declaring_class"])
        a("")
        a("The struct tag ships with its members unnamed in this build; the offsets below are")
        a("relative to the struct, and the five sibling `ImpactShake*` floats above are the")
        a("class-level members the SDK names.")
        a("")
        a("| struct offset | type | value |")
        a("|---|---|---|")
        for p in f["struct"]["props"]:
            a("| %#x | `%s` | %s |" % (p["offset"] or 0, p["type"], fmt_value(p["value"])))
        a("")

    # ---- ledger coverage ---------------------------------------------------
    a("## Ledger coverage (the card's Done line)")
    a("")
    a("Every field named by rows %s in `T_ROWS.jsonl`, with what this record says about it:" %
      ", ".join("`%s`" % r["id"] for r in doc["ledger_rows"]))
    a("")
    a("| row | token | in this record |")
    a("|---|---|---|")
    by_field = {f["field"]: f for f in doc["fields"]}

    def find(name):
        return ([f for f in doc["fields"] if f["field"] == name] or
                [f for f in doc["fields"] if f["field"].endswith(name)])

    def describe(name):
        hits = find(name)
        if not hits:
            return "**MISSING**"
        f = hits[0]
        if not f["values"]:
            return "declared, not serialised"
        per_pkg = [p for p in doc["packages"] if p["package"] in f["values"]]
        vals = [fmt_value(f["values"][p["package"]]) for p in per_pkg]
        absent = [p["short"] for p in doc["packages"] if p["package"] not in f["values"]]
        if len(set(vals)) == 1:
            core = "value %s (%s)" % (vals[0], f["unit"])
        else:
            core = "%s (%s)" % (", ".join("%s %s" % (p["short"], v)
                                          for p, v in zip(per_pkg, vals)), f["unit"])
        if not absent:
            return "%s, all %d packages" % (core, len(per_pkg))
        return ("%s in %d of %d packages; no tag in %s, so the class default runs, **UNKNOWN**"
                % (core, len(per_pkg), len(doc["packages"]), ", ".join(absent)))

    for item in doc["ledger_rows"]:
        for token in item["tokens"]:
            # `StayUprightConstraintSetup/Instance` names two fields in one token, and the
            # second half is shorthand for the rest of the field name
            parts = token.split("/") if "/" in token else [token]
            for i, part in enumerate(parts):
                if part.endswith("*"):
                    hits = [f for f in doc["fields"] if f["field"].startswith(part[:-1])]
                    label = token if i == 0 else part
                    a("| `%s` | `%s` | %d fields, %d serialised |" % (
                        item["id"], label, len(hits),
                        sum(1 for h in hits if h["serialized"])))
                else:
                    label = token if i == 0 else (find(part)[0]["field"] if find(part) else part)
                    a("| `%s` | `%s` | %s |" % (item["id"], label, describe(part)))
    a("")
    a("### Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for c in doc["checks"]:
        a("| %s | %s | %s |" % (c["name"], "PASS" if c["pass"] else "FAIL", c["detail"]))
    a("")
    a("%d/%d checks passed." % (sum(1 for c in doc["checks"] if c["pass"]),
                                len(doc["checks"])))
    a("")
    a("## Gaps")
    a("")
    a("- **%d of %d declared fields carry no value in the files.** They are declared by the class"
      % (s["not_serialized"], s["declared"]))
    a("  and absent from every archetype's tag stream, so the number that actually runs comes from")
    a("  the engine or BmScript defaults, which are not in this grab (`BMSDK_OFFSETS.json` has the")
    a("  declaration only).")
    partial = [f for f in doc["fields"]
               if f["values"] and len(f["values"]) < len(doc["packages"])]
    if partial:
        a(textwrap.fill(
            "- **%d serialised fields are missing from at least one archetype**: %s. A missing"
            " tag is not a zero: a cooked archetype omits a property that equals its class"
            " default, so the value that runs in those packages is a `Default__*`/CDO number the"
            " grab does not hold - **UNKNOWN** from the files, never 0 and never \"no such"
            " behaviour\"."
            % (len(partial), ", ".join("`%s` (%s)" % (f["field"], ", ".join(
                p["short"] for p in doc["packages"] if p["package"] not in f["values"]))
                for f in partial)), 96, subsequent_indent="  "))
    cam = sum(1 for f in doc["fields"] if f["declaring_class"] == "R3rdPersonCamera")
    a("- The camera family (`BattleModeCam*`, %d fields) belongs to the camera cards; it is listed"
      % cam)
    a("  here only so the `BattleMode*` prefix is complete.")
    armour = next((f for f in doc["fields"]
                   if f["field"] == "ArmourModeDamageReduction" and f["values"]), None)
    if armour:
        vals = sorted({fmt_value(v) for v in armour["values"].values()})
        absent = [p["short"] for p in doc["packages"] if p["package"] not in armour["values"]]
        a(textwrap.fill(
            "- `ArmourModeDamageReduction` ships **%s** in the %d packages that carry the tag and"
            " is read only by `TakeDamage` (`DAMAGE_RULES.md`)%s"
            % (" / ".join(vals), len(armour["values"]),
               ": armoured mode reduces incoming damage by nothing in those packages."
               if vals == ["0"] else "."), 96, subsequent_indent="  "))
        if absent:
            a("  The %s archetype has no tag there, so its running value is the class default -"
              % ", ".join(absent))
            a("  **UNKNOWN** from the files, not 0.")
    a("- `StayUprightConstraintSetup` / `...Instance` are object references; the objects they point")
    a("  at are native (`RB_StayUprightSetup`, size 2, no tags), so the constraint's own numbers")
    a("  are not in the grab.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write MODES.json and MODES.md")
    ap.add_argument("--check", action="store_true",
                    help="fail if MODES.json is stale or a ledger row is unserved")
    args = ap.parse_args()
    if not args.write and not args.check:
        args.check = True

    doc = build()
    md_path = os.path.join(OUT, "MODES.md")
    json_path = os.path.join(OUT, "MODES.json")

    if args.write:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(write_markdown(doc))
        print("wrote MODES.json (%d fields) and MODES.md" % len(doc["fields"]))
        return 0

    problems = [c for c in doc["checks"] if not c["pass"]]
    if not os.path.isfile(json_path) or not os.path.isfile(md_path):
        print("MISSING: run --write")
        return 1
    disk = read_json(json_path)
    if disk != doc:
        print("STALE: MODES.json does not match a fresh build (run --write)")
        return 1
    if open(md_path, encoding="utf-8").read() != write_markdown(doc):
        print("STALE: MODES.md does not match a fresh render (run --write)")
        return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    s = doc["summary"]
    print("OK: %d declared, %d serialised, %d not serialised; %d/%d checks; md byte-identical"
          % (s["declared"], s["serialized"], s["not_serialized"],
             len(doc["checks"]) - len(problems), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
