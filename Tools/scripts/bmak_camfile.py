"""bmak_camfile.py - emit the CAM-1 per-entity camera tune (no install).

The missing piece for CAM-1 was a *per-entity* camera reference.  It exists:
the vehicle `.epe` carries a `SharedCarCamera` (CCameraObject) whose
`CCameraModifier` names `editor/entities/jc_cameras/vehicle_cameras/car_base.ctune`.
That path is an ordinary NUL-terminated string in the binary `.epe`, so a
same-length rename points one vehicle at its own tune without touching the
shared `car_base.ctunec` every other car uses.

`car_base.ctune` and `bat_base.ctune` are the same 14 bytes, so the epe patch
changes only the two characters that differ (`c`->`b`, `r`->`t`): no offsets,
lengths or hashes move.

This tool only writes candidates outside the repo.  It does not pack an `.ee`,
edit a `.toc` or install anything.

**WITHDRAWN (2026-10-22).** The emitted values are not the authored BmAK camera:
`DrivingCamConfig1/2` carry `Min/MaxFreeCameraDistance = 400` cm (not 0), the sit offsets are
-3.0…-4.0 m, and JC3's FOV is vertical while UE3's 85/95 are horizontal. The old `7.0 m` /
`85°` were hand-derived and the test-086 drive rejected them. `build` and `check` now fail closed;
use `source` to print the authored configs and the open composition question. No candidate is
emitted until the sit-offset/distance composition is decoded.

Usage:
    python Tools/scripts/bmak_camfile.py source
    python Tools/scripts/bmak_camfile.py build      # refuses: CAM-1 withdrawn
    python Tools/scripts/bmak_camfile.py check      # refuses: CAM-1 withdrawn

Outputs (default):
    E:/Modding/_JC3cam_out/bat_base.ctunec
    E:/Modding/_JC3cam_out/v0300_..._civilian_01.epe
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf  # noqa: E402

SRC_CTUNEC = os.path.join(
    ROOT, "Working/Audio/jc3cam/editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec")
DONOR_EPE = os.path.join(
    ROOT, "Builds/test-085/aaf/editor/entities/jc_vehicles/01_land/"
          "v0300_car_kensington_sportsmuscle/"
          "v0300_car_kensington_sportsmuscle_civilian_01.epe")
OUT_DIR = r"E:/Modding/_JC3cam_out"
REPORT = os.path.join(ROOT, "Working/Camera/CAM_TUNE.json")

OLD_REF = b"car_base.ctune"
NEW_REF = b"bat_base.ctune"
OUT_CTUNEC = "bat_base.ctunec"

# T-CAM2..T-CAM6 from Working/Translation/T6_HUD_CAMERA.md.  `old` is asserted,
# never assumed: a different source file fails loudly instead of shifting data.
EDITS = [
    dict(member="CameraPosition", index=1, row="T-CAM5", old=2.0, new=2.4),
    dict(member="CameraPosition", index=2, row="T-CAM5", old=5.0, new=7.0),
    dict(member="LookAtPoint", index=1, row="T-CAM5", old=1.25, new=1.7),
    dict(member="FOV", index=0, row="T-CAM2", old=30.0, new=55.0),
    dict(member="FOV", index=1, row="T-CAM2", old=55.0, new=85.0),
    dict(member="FOVVelocityRange", index=1, row="T-CAM3", old=50.0, new=108.0),
    dict(member="RollWithVehicleAmount", index=None, row="T-CAM6", old=0.3, new=0.38),
    # T-CAM13: the occlusion ray starts 1.0 m up on a 1.41 m donor; the Batmobile
    # body is 2.271 m, so 1.0 * 1.61 = 1.6 m keeps it inside the upper body.
    dict(member="CollisionStartPoint", index=1, row="T-CAM13", old=1.0, new=1.6),
]


CAMERA_JSON = os.path.join(ROOT, "Research/BatmobileGrab/CAMERA.json")


def source_configs() -> dict:
    return json.load(open(CAMERA_JSON))["configs"]


def guard() -> None:
    """Fail closed: the old hand-derived candidate is not a translation."""
    c1 = source_configs()["DrivingCamConfig1"]["values"]
    if (c1[9], c1[10]) != (400.0, 400.0):
        raise SystemExit("CAM-1: CAMERA.json no longer matches the 400/400 cm chase config")
    raise SystemExit(
        "CAM-1 is WITHDRAWN. The authored chase config is DrivingCamConfig1: "
        "sit [-300,0,-25]..[-400,0,-25] cm, Min/MaxFreeCameraDistance 400/400 cm, "
        "pivot 155 cm, FOV 85/95 horizontal. The old 7.0 m / 85 deg values were "
        "hand-derived and test-086 rejected them. Decode the sit-offset+distance "
        "composition before emitting anything; see Research/BatmobileGrab/CAMERA.md.")


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def member_offset(adf: jc3adf.Adf, name: str, index: int | None) -> int:
    inst = adf.instances[0]
    members = {m["name"]: m for m in adf.types[inst["type"]]["members"]}
    if name not in members:
        raise KeyError(f"{name} not in {adf.type_name(inst['type'])}")
    off = inst["offset"] + members[name]["offset"]
    return off if index is None else off + 4 * index


def edit_path(e: dict) -> str:
    return e["member"] if e["index"] is None else f'{e["member"]}[{e["index"]}]'


def build_ctunec(src: str, dst: str) -> list[dict]:
    blob = bytearray(open(src, "rb").read())
    if bytes(blob[:4]) != b" FDA" or len(blob) != 5968:
        raise SystemExit(f"{src}: not the expected 5,968-byte ADF v4 camera tune")
    adf = jc3adf.Adf(bytes(blob))
    rows = []

    for e in EDITS:
        off = member_offset(adf, e["member"], e["index"])
        actual = struct.unpack_from("<f", blob, off)[0]
        if abs(actual - e["old"]) > 1e-6:
            raise SystemExit(
                f'{edit_path(e)} at 0x{off:x}: expected {e["old"]}, found {actual}')
        struct.pack_into("<f", blob, off, e["new"])
        rows.append({**e, "path": edit_path(e), "offset": off})

    # Semantic diff through the same reader the grab uses: every row except the
    # eight edited floats must be identical.
    before = list(jc3adf.walk(adf))
    after = list(jc3adf.walk(jc3adf.Adf(bytes(blob))))
    expect = {r["path"]: r["new"] for r in rows}
    if len(before) != len(after):
        raise SystemExit("ADF row count changed")
    for (p1, _t1, v1), (p2, _t2, v2) in zip(before, after):
        if p1 != p2:
            raise SystemExit(f"ADF row order changed: {p1} != {p2}")
        if p1 in expect:
            if abs(v2 - expect[p1]) > 1e-6:
                raise SystemExit(f"{p1}: wrote {v2}, expected {expect[p1]}")
        elif v1 != v2:
            raise SystemExit(f"collateral change at {p1}: {v1} -> {v2}")

    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    open(dst, "wb").write(blob)
    for r in rows:
        r["readback"] = struct.unpack_from("<f", blob, r["offset"])[0]
    return rows


def patch_epe(src: str, dst: str) -> dict:
    blob = bytearray(open(src, "rb").read())
    count = blob.count(OLD_REF)
    if count != 1:
        raise SystemExit(f"{src}: expected one {OLD_REF!r}, found {count}")
    if len(OLD_REF) != len(NEW_REF):
        raise SystemExit("refs differ in length; in-place patch would move offsets")
    off = blob.find(OLD_REF)
    before = bytes(blob)
    blob[off:off + len(OLD_REF)] = NEW_REF
    if blob.count(NEW_REF) != 1 or blob.count(OLD_REF) != 0:
        raise SystemExit("replacement did not land exactly")
    diff = sum(1 for a, b in zip(before, blob) if a != b)
    # `car_` -> `bat_` is a 2-byte change (c->b, r->t); the two names are the
    # same length, so nothing after the string may move.
    if diff > len(OLD_REF):
        raise SystemExit(f"{diff} bytes changed, expected at most {len(OLD_REF)}")

    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    open(dst, "wb").write(blob)
    return {
        "source": src, "output": dst,
        "old_ref": OLD_REF.decode(), "new_ref": NEW_REF.decode(),
        "offset": off, "occurrences": count, "bytes_changed": diff,
        "size": len(before), "size_same": len(before) == len(blob),
        "sha256_before": sha(before), "sha256_after": sha(bytes(blob)),
    }


def run(src: str, epe: str, out: str, report: str | None) -> dict:
    guard()
    os.makedirs(out, exist_ok=True)
    ct_out = os.path.join(out, OUT_CTUNEC)
    epe_out = os.path.join(out, os.path.basename(epe))
    rows = build_ctunec(src, ct_out)
    epe_row = patch_epe(epe, epe_out)
    data = {
        "tool": "bmak_camfile.py",
        "build": "CAM-1 candidate: bat_base.ctunec + donor .epe ref rename (not packed, not installed)",
        "source": {"ctunec": src, "size": os.path.getsize(src), "sha256": sha(open(src, "rb").read())},
        "output": {"ctunec": ct_out, "size": os.path.getsize(ct_out),
                   "sha256": sha(open(ct_out, "rb").read())},
        "edits": rows,
        "readback": {"ok": len(rows), "expected": len(EDITS)},
        "epe": epe_row,
        "checks": [
            "8/8 old values asserted before write",
            "8/8 new values re-read from the written file",
            "every other ADF row unchanged (full walk)",
            "epe: one occurrence, same length, 2 bytes differ (c->b, r->t), size unchanged",
        ],
    }
    if report:
        os.makedirs(os.path.dirname(report) or ".", exist_ok=True)
        json.dump(data, open(report, "w"), indent=1)
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("source", help="print the authored chase configs and the open question")
    for name, helptext in (("build", "write the candidate files (withdrawn)"),
                           ("check", "rebuild to a temp dir and verify (withdrawn)")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--src", default=SRC_CTUNEC)
        p.add_argument("--epe", default=DONOR_EPE)
        p.add_argument("--out", default=OUT_DIR)
        p.add_argument("--report", default=REPORT if name == "build" else None)
    a = ap.parse_args()

    if a.cmd == "source":
        for name in ("DrivingCamConfig1", "DrivingCamConfig2"):
            c = source_configs()[name]
            v = dict(zip(c["fields"], c["values"]))
            print(f"{name}:")
            for k in ("StateFreeCameraSitOffsetMin", "StateFreeCameraSitOffsetMax",
                      "MinFreeCameraDistance", "MaxFreeCameraDistance", "CameraPivotOffset"):
                print(f"  {k:30} {v[k]}")
        print("open: how the sit offset and the 400 cm distance compose into the boom")
        print("JC3 FOV is vertical: 85/95 horizontal -> 54.5/63.1 vertical at 16:9")
        return 0

    if a.cmd == "check":
        tmp = tempfile.mkdtemp(prefix="camfile_")
        try:
            data = run(a.src, a.epe, tmp, None)
            fresh = os.path.join(a.out, OUT_CTUNEC)
            if os.path.exists(fresh):
                if open(fresh, "rb").read() != open(data["output"]["ctunec"], "rb").read():
                    raise SystemExit("existing output differs from a fresh build")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(f'check: 8/8 edits, 0 collateral rows, epe {data["epe"]["bytes_changed"]} bytes / '
              f'{data["epe"]["occurrences"]} ref')
        return 0

    data = run(a.src, a.epe, a.out, a.report)
    print(f'ctunec: {data["output"]["ctunec"]}  {data["output"]["size"]} B  {data["output"]["sha256"][:12]}')
    for r in data["edits"]:
        print(f'  {r["path"]:<26} {r["old"]:>8g} -> {r["new"]:<8g} @ 0x{r["offset"]:x} = {r["readback"]:g}')
    e = data["epe"]
    print(f'epe:    {e["output"]}  {e["old_ref"]} -> {e["new_ref"]} @ 0x{e["offset"]:x}, '
          f'{e["bytes_changed"]} bytes, size same={e["size_same"]}')
    if a.report:
        print(f'report: {a.report}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
