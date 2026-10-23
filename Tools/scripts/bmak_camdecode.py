"""Decode the R3rdPersonCamera boom: how a FreeCameraConfig's sit offset and distance compose.

The composition was read out of BatmanAK.exe (x64) and is reproduced here arithmetically, so the
next camera build can be generated from numbers instead of a guess.  Three natives matter:

  `SetFreeCameraConfig`        0x140113480   config struct -> State* fields
  `UpdateDrivingCamSettings`   0x14010ad00   State* -> Current* (blend, per-frame)
  `UpdateCameraPosition`       0x140111660   Current* -> camera location

`SetFreeCameraConfig(camera, cfg)` (camera in rcx, cfg in rdx) does, field by field:

    cfg+0x00  -> 0xF40 StateFreeCameraSitOffsetMin
    cfg+0x0C  -> 0xF58 StateFreeCameraSitOffsetDown     <- the struct field named "SitOffsetMax"
    cfg+0x1C  -> 0xF4C StateFreeCameraSitOffsetUp       (only if cfg+0x18 & 1, else cfg+0x0C again)
    cfg+0x28  -> 0xF64 StateFreeCameraPullOffset
    cfg+0x34  -> 0x6F0 CameraPivotOffset
    cfg+0x40  -> 0x4F30 ZoomOffset
    cfg+0x68  -> 0xF70 StateSitOffsetPower
    cfg+0x6C  -> 0xF74 StateSitOffsetMin
    cfg+0x70  -> 0xF78 StateSitOffsetMax
    cfg+0x54  -> 0xD74 MinFreeCameraDistance
    cfg+0x58  -> 0xD78 MaxFreeCameraDistance
    cfg+0x5C  -> 0xD7C ShortCamSpringConst
    cfg+0x60  -> 0xD80 LongCamSpringConst
    cfg+0x4C  -> 0x804 MaxFreeCameraPitch
    cfg+0x50  -> 0x808 MinFreeCameraPitch
    all 168 bytes -> 0x4730 CurrentCameraConfig

`UpdateDrivingCamSettings` copies State* into Current* (`0xF40.. -> 0xF04..`, `0xF70.. -> 0xF34..`,
`0xD74/0xD78 -> 0xEF0/0xEF4`) and then smooths Current* toward State* every frame.

`UpdateCameraPosition` composes the boom.  With `pitch` in UE3 rotator units (65536 = 360 deg):

    t      = clamp(|pitch| / (pitch > 0 ? CurrentSitOffsetMax : CurrentSitOffsetMin), 0, 1)
    t      = t ** CurrentSitOffsetPower                    (skipped when t == 0 or power == 1)
    Sit    = lerp(FreeCameraSitOffsetMin,                  (1-t)*Min + t*Other
                  pitch > 0 ? FreeCameraSitOffsetUp
                            : FreeCameraSitOffsetDown, t)
    Loc    = anchor - RotToVector(Rotator) * distance + RotateVector(Rotator, Sit)

The distance is the spring value between `CurrentMinFreeCameraDistance` and
`CurrentMaxFreeCameraDistance` (`0xEF0/0xEF4`), smoothed with `CurrentShort/LongCamSpringConst`
(`0xD90/0xD94`) when collision shortens it; the `UpdateCameraPosition` block at 0x140111BE2 loads
those two currents, and 0x140111C75 does `candidate = base + unit_dir * distance`.
So the sit offset is **ADDITIVE** to the distant boom, not an alternative to it: the camera hangs
`distance` behind the anchor along the view axis, and the sit offset (rotated by the same rotation)
is added on top.  The old page's open question ("additive, alternatives, or collision limits") is
answered: additive, with the distance as an independent spring whose bounds collapse to 400/400 for
the Batmobile's `DrivingCamConfig1/2`.

Also decoded: `StateFreeCameraSitOffsetDown` is fed from the config field the class header calls
`StateFreeCameraSitOffsetMax`; there is no separate down vector in the 168-byte struct — the "max"
vector is the look-down offset.  And `CameraSitOffsetMin/Max` (16384 / 8192) are **pitch angles in
rotator units** (90 deg / 45 deg), not distances; they are the pitch at which the sit offset reaches
the down/up vector.

Usage
    python Tools/scripts/bmak_camdecode.py            # print the composition table
    python Tools/scripts/bmak_camdecode.py --check    # assert the authored values + arithmetic
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CAM = ROOT / "Research" / "BatmobileGrab" / "CAMERA.json"

# Constants the native code hard-codes (read from BatmanAK.exe; see the module docstring).
ROT_FULL = 65536.0          # one full turn in UE3 rotator units
SPRING_DEFAULT = 10000.0    # cfg+0x5C / cfg+0x60 for DrivingCamConfig1/2


def config(name: str) -> dict:
    table = json.loads(CAM.read_text(encoding="utf-8"))
    c = table["configs"][name]
    return dict(zip(c["fields"], c["values"]))


def native_offset(cfg_name: str, pitch: float, distance: float | None = None) -> dict:
    """Return the camera offset from the anchor, exactly as `UpdateCameraPosition` composes it.

    pitch is in UE3 rotator units (positive = look up).  The returned vector is in the same
    (unrotated) frame as the config's sit offsets: x forward, z up.
    """
    c = config(cfg_name)
    dist = c["MinFreeCameraDistance"] if distance is None else distance
    # UpdateCameraPosition uses the current bounds, which for these configs are min == max.
    assert c["MinFreeCameraDistance"] == c["MaxFreeCameraDistance"] == dist, \
        "config carries a distance range; pass an explicit distance"
    up = c["UseStateFreeCameraSitOffsetUp"]
    down = c["StateFreeCameraSitOffsetMax"]      # cfg+0x0C -> StateFreeCameraSitOffsetDown
    upv = c["StateFreeCameraSitOffsetUp"] if up else down
    threshold = c["CameraSitOffsetMax"] if pitch > 0 else c["CameraSitOffsetMin"]
    t = min(max(abs(pitch) / threshold, 0.0), 1.0) if threshold else 0.0
    if t and c["CameraSitOffsetPower"] != 1.0:
        t = t ** c["CameraSitOffsetPower"]
    other = upv if pitch > 0 else down
    lo = c["StateFreeCameraSitOffsetMin"]
    sit = [lo[i] * (1.0 - t) + other[i] * t for i in range(3)]
    total = [sit[0] - dist, sit[1], sit[2]]      # -forward * distance, then + sit
    return {
        "t": t,
        "sit": sit,
        "distance": dist,
        "total": total,
        "anchor_z": c["CameraPivotOffset"][2],
        "camera_z": c["CameraPivotOffset"][2] + total[2],
    }


def check() -> int:
    c = config("DrivingCamConfig1")
    bad = 0

    def same(a, b):
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            return len(a) == len(b) and all(abs(x - y) < 1e-6 for x, y in zip(a, b))
        return a == b

    def want(label, got, exp):
        nonlocal bad
        ok = same(got, exp)
        print(f"{'PASS' if ok else 'FAIL'} {label:44s} {got!r}")
        bad += not ok

    # The authored values the disassembly depends on.
    want("sit min (cfg+0x00)", c["StateFreeCameraSitOffsetMin"], [-300.0, 0.0, -25.0])
    want("sit max = look-down (cfg+0x0C)", c["StateFreeCameraSitOffsetMax"], [-400.0, 0.0, -25.0])
    want("sit up (cfg+0x1C)", c["StateFreeCameraSitOffsetUp"], [-500.0, 0.0, 500.0])
    want("pull (cfg+0x28)", c["StateFreeCameraPullOffset"], [0.0, 0.0, 0.0])
    want("pivot (cfg+0x34)", c["CameraPivotOffset"], [0.0, 0.0, 155.0])
    want("distance (cfg+0x54/0x58)", (c["MinFreeCameraDistance"], c["MaxFreeCameraDistance"]),
         (400.0, 400.0))
    want("springs (cfg+0x5C/0x60)", (c["ShortCamSpringConst"], c["LongCamSpringConst"]),
         (SPRING_DEFAULT, SPRING_DEFAULT))
    want("sit power (cfg+0x68)", c["CameraSitOffsetPower"], 1.5)
    want("pitch at full look-down (cfg+0x6C)", c["CameraSitOffsetMin"], 16384.0)
    want("pitch at full look-up (cfg+0x70)", c["CameraSitOffsetMax"], 8192.0)

    # The arithmetic, at the three landmarks.
    rest = native_offset("DrivingCamConfig1", 0.0)
    want("rest: t", rest["t"], 0.0)
    want("rest: offset (x, y, z cm)", rest["total"], [-700.0, 0.0, -25.0])
    want("rest: camera height above car (cm)", rest["camera_z"], 130.0)
    lvl = native_offset("DrivingCamConfig1", -1000.0)          # DefaultCameraPitch
    want("default pitch (-5.49 deg): boom cm", round(-lvl["total"][0], 3), 701.508)
    up = native_offset("DrivingCamConfig1", 8192.0)
    want("look up 45 deg: offset", up["total"], [-900.0, 0.0, 500.0])
    down = native_offset("DrivingCamConfig1", -16384.0)
    want("look down 90 deg: offset", down["total"], [-800.0, 0.0, -25.0])
    # DrivingCamConfig2 is the same distance with a flat sit offset (no downward pitch pull).
    c2 = native_offset("DrivingCamConfig2", 0.0)
    want("config2 rest: offset", c2["total"], [-900.0, 0.0, 0.0])
    print(f"{'PASS' if not bad else 'FAIL'}: boom composition")
    return 1 if bad else 0


def report() -> None:
    print(f"{'config':18s} {'pitch':>8s} {'t':>6s} {'sit':>26s} {'boom':>6s} {'camera offset from pivot (cm)':>32s}")
    for name in ("DrivingCamConfig1", "DrivingCamConfig2"):
        for label, pitch in (("rest", 0.0), ("default", -1000.0),
                             ("look-up 45", 8192.0), ("look-down 90", -16384.0)):
            r = native_offset(name, pitch)
            print(f"{name:18s} {label:>8s} {r['t']:6.3f} "
                  f"{'[' + ', '.join(f'{v:.1f}' for v in r['sit']) + ']':>26s} "
                  f"{r['distance']:6.0f} "
                  f"{'[' + ', '.join(f'{v:.1f}' for v in r['total']) + ']':>32s}")
    print()
    print("The distance is the spring boom; the sit offset is rotated and added. "
          "At rest the Batmobile camera therefore sits 700 cm behind the pivot "
          "(400 boom + 300 sit) and 25 cm below it.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        raise SystemExit(check())
    report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
