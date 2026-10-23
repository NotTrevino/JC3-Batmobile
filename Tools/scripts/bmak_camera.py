"""Read Batman: Arkham Knight's Batmobile camera rules out of `R3rdPersonCamera`.

The vehicle classes only expose two helpers (`GetCameraTrackingOffset`,
`ShouldCameraZFollowVehicleUp`).  The actual chase camera is `R3rdPersonCamera`, whose class default
object in `BmGame.upk` carries the values: **741 properties**, of which **447 tags** are serialized.

The cook writes simple tags as `type + class offset + value` with no name, and the class layout has
to be reconstructed from the `UProperty` children (as `bmak_layout.py` does).  The camera layout is
not a perfect fit - it drifts by a constant in regions because some native struct sizes are not in
`ScriptStruct` form - so this tool anchors on the **named struct/array tags** (which do carry their
name), interpolates the local offset delta from the nearest anchor, and only reports a scalar when
the corrected offset lands on a property of the matching type.  A value that cannot be bound is
omitted rather than guessed.

Usage:
    python Tools/scripts/bmak_camera.py --write      # -> Research/BatmobileGrab/CAMERA.json
    python Tools/scripts/bmak_camera.py --check      # re-read the game, compare every expected value
    python Tools/scripts/bmak_camera.py --report     # print the rules

The camera class is global: the Batmobile selects one of its three states
(`EBDC_BonnetCamera`, `EBDC_Camera1`, `EBDC_Camera2`).  Camera 1 and camera 2 are the two chase
presets; `DrivingCam*1/2` and `BoostingCam*1/2` are their parameters, not per-vehicle values.
"""
from __future__ import annotations

import argparse
import bisect
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import bmak_layout as L  # noqa: E402
import upk_read as U     # noqa: E402

OUT = ROOT / "Research" / "BatmobileGrab" / "CAMERA.json"

# The fields the translation needs, mapped from the corrected tag offset.  Names are the class's
# own UProperty names; the value is what the default object serializes for that slot.
WANTED = [
    # the three states
    "EBatmobileDriveCamera",
    # camera 1 / camera 2, driving and boosting
    "DrivingCamFOVInterpMaxSpeed1", "DrivingCamFOV1", "BoostingCamFOV1",
    "DrivingCamMaxExtraFOV1", "DrivingCamMaxExtraTranslation1",
    "BoostingCamSmoothingStrength1", "DrivingCamSmoothingStrength1",
    "AirborneCamSmoothingStrength1",
    "DrivingCameraLeanFactor1", "DrivingCameraPitchFactor1", "DrivingHeadImpulseFactor1",
    "DrivingCamDriftOrientationFactor1",
    "DrivingCamFOVInterpMaxSpeed2", "DrivingCamFOV2", "BoostingCamFOV2",
    "DrivingCamMaxExtraFOV2", "DrivingCamMaxExtraTranslation2",
    "BoostingCamSmoothingStrength2", "DrivingCamSmoothingStrength2",
    "AirborneCamSmoothingStrength2",
    "DrivingCameraLeanFactor2", "DrivingCameraPitchFactor2", "DrivingHeadImpulseFactor2",
    "DrivingCamDriftOrientationFactor2",
    # shared / other Batmobile states
    "BattleModeCamFOV", "BattleModeWinchCamFOV", "AntiPersonelBattleModeCamFOV",
    "ChasingCamFOV", "JumpSmoothingStrength", "BatmobileConversationCamFOV",
    "RidingCarCamFOV", "DrivingCamAccelFOVFactor", "HelicopterCameraFOVAngle",
    # the class default distances. The configs override them (DrivingCamConfig1/2 = 400/400),
    # but the defaults are needed to know what the field means and to catch a zeroed template.
    "MinFreeCameraDistance", "MaxFreeCameraDistance",
]

# CameraConfig (FreeCameraConfig) fields, in struct order.  The struct is 168 bytes and its layout
# is proven by its own ScriptStruct; values are positional because the nested tags drop the names.
CONFIG_FIELDS = [
    ("StateFreeCameraSitOffsetMin", 12), ("StateFreeCameraSitOffsetMax", 12),
    ("UseStateFreeCameraSitOffsetUp", 4), ("StateFreeCameraSitOffsetUp", 12),
    ("StateFreeCameraPullOffset", 12), ("CameraPivotOffset", 12),
    ("ZoomedOffset", 12), ("maxPitch", 4), ("MinPitch", 4),
    ("MinFreeCameraDistance", 4), ("MaxFreeCameraDistance", 4),
    ("ShortCamSpringConst", 4), ("LongCamSpringConst", 4),
    ("DefaultCameraPitch", 4), ("CameraSitOffsetPower", 4),
    ("CameraSitOffsetMin", 4), ("CameraSitOffsetMax", 4),
    ("bUseSeparate43Settings", 4), ("StateFreeCamera43SitOffsetMax", 12),
    ("StateFreeCamera43SitOffsetMin", 12), ("StateFreeCamera43SitOffsetLookUp", 12),
    ("bDontModifySitOffsetWhenLookingUp", 4),
    ("MinCameraSmoothingAngle", 4), ("MaxCameraSmoothingAngle", 4),
]
CONFIG_NAMES = [
    "DrivingCamConfig", "BoostingCamConfig", "BattleModeCamConfig", "BattleModeWinchCamConfig",
    "BattleModeAbseilingCamConfig", "ChasingCamConfig", "GlideInBatmobileCamConfig",
    "DiveToBatmobilePickupCamConfig", "BatmobileConversationCamConfig",
    "DrivingCamConfig1", "BoostingCamConfig1", "DrivingCamConfig2", "BoostingCamConfig2",
]


def load():
    lay = L.Layout()
    cls = lay.find_class("R3rdPersonCamera")
    if not cls:
        raise SystemExit("R3rdPersonCamera not in BmGame.upk")
    rows, extent = lay.layout(cls)
    tags, why = lay.top_level_offsets(cls)
    by_name = {r["name"]: r for r in rows}
    anchors = []
    for t in tags:
        nm = t.get("name")
        if nm in by_name and t["type"] in ("StructProperty", "ArrayProperty"):
            anchors.append((t["offset"], t["offset"] - by_name[nm]["offset"]))
    anchors.sort()
    return {
        "class": cls, "rows": rows, "tags": tags, "extent": extent, "stop": why,
        "by_name": by_name, "anchors": anchors,
    }


def bindings(ctx):
    """Map serialized simple tags to property names with the local anchor delta."""
    anchors = ctx["anchors"]
    keys = [a[0] for a in anchors]
    by_off = {}
    for r in ctx["rows"]:
        by_off.setdefault(r["offset"], []).append(r)
    out = {}
    for t in ctx["tags"]:
        if t.get("name"):
            continue
        i = bisect.bisect_right(keys, t["offset"]) - 1
        delta = anchors[max(0, i)][1]
        target = t["offset"] - delta
        cand = []
        for off in (target, target - 4, target + 4):
            cand = [r for r in by_off.get(off, ()) if L.same_kind(t["type"], r["kind"])]
            if cand:
                break
        if not cand:
            continue
        r = cand[0]
        value = t.get("value", t.get("floats", t.get("ref")))
        if value is None:
            continue
        out.setdefault(r["name"], value)
    return out


def config_values(ctx):
    """Positional values inside a CameraConfig tag, mapped to the struct's field list."""
    out = {}
    for t in ctx["tags"]:
        nm = t.get("name")
        if nm not in CONFIG_NAMES or "props" not in t:
            continue
        vals = []
        for child in t["props"]:
            v = child.get("value", child.get("floats", child.get("ref")))
            if v is not None:
                vals.append(v)
        # The serialized struct has 23-24 slots; match by cumulative size where the count allows,
        # otherwise keep the sequence and let the field list label what it can.
        row = []
        off = 0
        for name, size in CONFIG_FIELDS:
            if off >= 168:
                break
            row.append(name)
            off += size
        out[nm] = {"fields": row, "values": vals}
    return out


def build():
    ctx = load()
    bound = bindings(ctx)
    sco = {k: bound[k] for k in WANTED if k in bound}
    enum = {}
    # The enum is a UEnum export with four FName entries; read them from the package directly.
    pkg = U.Package(L.PKG)
    idx = pkg.find("EBatmobileDriveCamera")
    if idx:
        data = pkg.data(idx)
        names = []
        for off in range(len(data) - 7):
            a, b = struct.unpack_from("<ii", data, off)
            if 0 <= a < len(pkg.names) and b == 0 and pkg.names[a].startswith("EBDC_"):
                if not names or names[-1] != pkg.names[a]:
                    names.append(pkg.names[a])
        enum["EBatmobileDriveCamera"] = names
    return {
        "source": L.PKG,
        "class": "R3rdPersonCamera",
        "properties": len(ctx["rows"]),
        "tags": len(ctx["tags"]),
        "layout_extent": ctx["extent"],
        "values": sco,
        "enum": enum,
        "configs": config_values(ctx),
    }


def check():
    table = json.loads(OUT.read_text(encoding="utf-8"))
    got = build()
    bad = 0
    for k, want in table["values"].items():
        have = got["values"].get(k)
        ok = have == want
        print(f"{'PASS' if ok else 'FAIL'} {k:38s} {have!r}")
        bad += not ok
    # The exact miss that produced the withdrawn test-086: the active chase configs carry
    # 400/400, while the zeroed `DrivingCamConfig` template does not. Bind the active ones.
    for name in ("DrivingCamConfig1", "DrivingCamConfig2"):
        vals = got["configs"][name]["values"]
        ok = (vals[9], vals[10]) == (400.0, 400.0)
        print(f"{'PASS' if ok else 'FAIL'} {name+' distance':38s} {vals[9]!r} / {vals[10]!r}")
        bad += not ok
    print(f"{'PASS' if not bad else 'FAIL'}: {len(table['values'])} camera values")
    raise SystemExit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.check:
        check()
        return
    table = build()
    if a.write:
        OUT.write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {OUT} ({len(table['values'])} values, {len(table['configs'])} configs)")
        return
    print(f"{table['class']}: {table['properties']} props, {table['tags']} tags")
    for k, v in table["values"].items():
        print(f"  {k:38s} {v}")
    print("  enum:", table["enum"])


if __name__ == "__main__":
    main()
