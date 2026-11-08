"""chase2_verify.py - second pass over F-8..F-16: re-derive from bytes, and close F-8.

First pass (`Research/BatmobileGrab/chase/chase-02.md`) closed F-9..F-16 from the class default
objects in `BmGame.upk` and left three things open:
  * F-8 `BattleModeCamConfig` - "in the same default object and now likewise decodable ... noted,
    not chased";
  * the *unit* of `maxPitch` / `MinPitch` inside `FFreeCameraConfig`;
  * whether anything writes a FOV at runtime.

This script answers the first two as far as the files allow. It does **not** reuse the first pass's
numbers: for every field it finds the tag, prints the payload bytes at
`export_image_offset + tag.at`, and decodes them here with `struct` only (the walker's own decode in
`upk_read` is not consulted). The expected value is written down from chase-02's table, so a MATCH
proves the first pass reproduced byte for byte and a DIFF is visible.

Addresses are offsets into the *decompressed package image* (`Package.image`), not into the 214 MB
file on disk: `BmGame.upk` is chunk-compressed, so `export.offset` is image-relative. The first pass
labelled them file offsets; this script prints `image+0x...` so the label is exact.

`--check` re-runs every comparison and exits non-zero on any DIFF (R11: numbers are generated).

Read-only: opens the shipped package, writes only the `--json` path. No game launched.

Usage:
    python Tools/scripts/chase/chase2_verify.py
    python Tools/scripts/chase/chase2_verify.py --json E:/Modding/_gamedata/BmAKgrab/chase/chase2_verify.json
    python Tools/scripts/chase/chase2_verify.py --check
"""
import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk, walk_tags, TYPE_NAMES  # noqa: E402

PKG = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk"
DEFAULT_JSON = r"E:\Modding\_gamedata\BmAKgrab\chase\chase2_verify.json"

CDO_CAM = "Default__R3rdPersonCamera"
CDO_VEH = "Default__RVehicleBatmobileBase"

# field, owner object, class-layout offset, expected value as chase-02 recorded it.
# `None` = chase-02 recorded no value (it did not chase F-8); this pass fills it in.
ROWS = [
    ("F-8", "BattleModeCamConfig", CDO_CAM, 0x3DF4, "struct", None),
    ("F-9", "BattleModeWinchCamConfig", CDO_CAM, 0x3E9C, "struct", "struct"),
    ("F-10", "BattleModeAbseilingCamConfig", CDO_CAM, 0x3F44, "struct", "struct"),
    ("F-11", "BattleModeCamFOV", CDO_CAM, 0x4FD0, "float", 60.0),
    ("F-12", "BattleModeWinchCamFOV", CDO_CAM, 0x4FD4, "float", 60.0),
    ("F-13", "BattleModeHeadOffset", CDO_CAM, 0x4FDC, "vector", [0.0, 0.0, 150.0]),
    ("F-14", "BattleModeWinchHeadOffset", CDO_CAM, 0x4FF8, "vector", [0.0, 0.0, 300.0]),
    ("F-15", "BattleModeAbseilingExtraCameraRot", CDO_CAM, 0x5034, "rotator", [1500, 0, 0]),
    ("F-16", "StrafeCooldown", CDO_VEH, 0x11E4, "float", 0.75),
]

# FFreeCameraConfig member layout (BMSDK_OFFSETS.json classes.R3rdPersonCamera.structs.*):
# relative offset -> (name, kind).  Used only to name the sub-tags this pass re-walks.
FFCC = {
    0: ("StateFreeCameraSitOffsetMin", "vector"),
    12: ("StateFreeCameraSitOffsetMax", "vector"),
    24: ("UseStateFreeCameraSitOffsetUp", "bool"),
    28: ("StateFreeCameraSitOffsetUp", "vector"),
    40: ("StateFreeCameraPullOffset", "vector"),
    52: ("CameraPivotOffset", "vector"),
    64: ("ZoomedOffset", "vector"),
    76: ("maxPitch", "float"),
    80: ("MinPitch", "float"),
    84: ("MinFreeCameraDistance", "float"),
    88: ("MaxFreeCameraDistance", "float"),
    92: ("ShortCamSpringConst", "float"),
    96: ("LongCamSpringConst", "float"),
    100: ("DefaultCameraPitch", "float"),
    104: ("CameraSitOffsetPower", "float"),
    108: ("CameraSitOffsetMin", "float"),
    112: ("CameraSitOffsetMax", "float"),
    116: ("bUseSeparate43Settings", "bool"),
    120: ("StateFreeCamera43SitOffsetMax", "vector"),
    132: ("StateFreeCamera43SitOffsetMin", "vector"),
    144: ("StateFreeCamera43SitOffsetLookUp", "vector"),
    156: ("bDontModifySitOffsetWhenLookingUp", "bool"),
    160: ("MinCameraSmoothingAngle", "float"),
    164: ("MaxCameraSmoothingAngle", "float"),
}

SIMPLE_LEN = {2: 4, 3: 4, 4: 4, 6: 8, 11: 12, 12: 12, 16: 4, 17: 32}


def hexs(b, width=32):
    return " ".join("%02x" % c for c in b[:width])


def decode(t, raw):
    """Independent decode: struct module only, no upk_read helpers."""
    if t == 4:
        return struct.unpack("<f", raw[:4])[0]
    if t == 2:
        return struct.unpack("<i", raw[:4])[0]
    if t == 3:
        return bool(struct.unpack("<i", raw[:4])[0])
    if t == 11:
        return list(struct.unpack("<3f", raw[:12]))
    if t == 12:
        return list(struct.unpack("<3i", raw[:12]))
    return None


def abs_of(pkg, index, tag):
    """Image offset of the tag payload: export image offset + payload position in the object."""
    return pkg.exports[index - 1]["offset"] + tag["at"]


def walk_one(pkg, name):
    idx = pkg.find(name)
    if not idx or idx < 0:
        raise SystemExit(f"{name} not found in {os.path.basename(pkg.path)}")
    data = pkg.data(idx)
    tags, end, why = best_walk(pkg, data)
    return idx, data, tags, end, why


def struct_rows(pkg, idx, tag):
    """Re-walk the struct payload; return one row per sub-tag with its own raw bytes."""
    payload = pkg.image[abs_of(pkg, idx, tag):abs_of(pkg, idx, tag) + tag["size"]]
    sub, end, why = walk_tags(pkg, payload)
    out = []
    base = tag["offset"]
    for s in sub:
        # sub-tag offsets inside a struct payload are relative to the struct (0, 12, 24, ...), which
        # is why they line up with the BmSDK FFreeCameraConfig member offsets one to one.
        rel = s["offset"]
        n = SIMPLE_LEN.get(s["type_id"])
        if n is None:
            n = s.get("size", 0)
        raw = payload[s["at"]:s["at"] + n]
        name = FFCC.get(rel, (s.get("name"), None))[0] or s.get("name")
        out.append({
            "rel_offset": rel,
            "class_offset": base + rel,
            "field": name,
            "type": TYPE_NAMES.get(s["type_id"]),
            "at": hexs(raw),
            "value": decode(s["type_id"], raw),
            "walker_value": s.get("value"),
        })
    return out, end, why, len(payload)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", default=PKG)
    ap.add_argument("--json", nargs="?", const=DEFAULT_JSON, default=DEFAULT_JSON)
    ap.add_argument("--check", action="store_true", help="exit 1 on any DIFF")
    a = ap.parse_args()

    pkg = Package(a.package)
    print(f"package {os.path.basename(pkg.path)}: version {pkg.version}, {len(pkg.exports)} exports, "
          f"image {len(pkg.image):,} B")
    # one walk per default object, reused for every row on it
    objs = {}
    for name in (CDO_CAM, CDO_VEH):
        idx, data, tags, end, why = walk_one(pkg, name)
        objs[name] = (idx, tags)
        print(f"  {name}: export {idx}, image+0x{pkg.exports[idx - 1]['offset']:x}, "
              f"{len(data)} B, {len(tags)} tags, stop={why}")

    diffs, rows_out = 0, []
    for card, field, obj, off, kind, expected in ROWS:
        idx, tags = objs[obj]
        hits = [t for t in tags if t.get("offset") == off]
        if not hits:
            print(f"\n{card} {field} @0x{off:04x}: ABSENT")
            rows_out.append({"card": card, "field": field, "offset": off, "status": "absent"})
            diffs += 1
            continue
        # ambiguity guard: a second tag at the same offset would make the value unreachable
        dup = len(hits) > 1
        t = hits[0]
        n = SIMPLE_LEN.get(t["type_id"], t.get("size", 0))
        raw = pkg.image[abs_of(pkg, idx, t):abs_of(pkg, idx, t) + n]
        value = decode(t["type_id"], raw)
        row = {"card": card, "field": field, "object": obj, "offset": off,
               "image_offset": abs_of(pkg, idx, t), "type": TYPE_NAMES.get(t["type_id"]),
               "bytes": hexs(raw, 24), "value": value, "duplicate_tags_at_offset": dup}
        print(f"\n{card} {field}  @0x{off:04x}  {TYPE_NAMES.get(t['type_id'])}  "
              f"image+0x{abs_of(pkg, idx, t):x}  payload {n} B")
        print(f"   bytes {hexs(raw, 24)}")
        if kind == "struct":
            sub, end, why, plen = struct_rows(pkg, idx, t)
            print(f"   struct payload {plen} B: {len(sub)} sub-tags, consumed {end} B "
                  f"stop={why} (the last 2 B are the 0-type list terminator)")
            print("     rel   class-off  field                                type            bytes                          value")
            for s in sub:
                print(f"   {s['rel_offset']:>6}  0x{s['class_offset']:04x}    {str(s['field']):<36} "
                      f"{str(s['type']):<15} {s['at']:<30} {s['value']!r}")
            row["sub_tags"] = sub
            row["struct_bytes"] = plen
            got = sub
            ok = (plen - end) <= 2 and len(sub) == len(FFCC)
            print(f"   -- struct ran to its terminator: {ok} ({plen - end} B unread); "
                  f"{len(sub)} sub-tags ({len(FFCC)} members expected); "
                  f"every member name resolved: {all(s['field'] for s in sub)}")
        else:
            got = value
            print(f"   decoded {got!r}  (chase-02 expected {expected!r})")
            ok = False
            if expected is None:
                ok = True
            elif isinstance(expected, list) and isinstance(got, list):
                ok = len(expected) == len(got) and all(
                    (abs(x - y) <= 1e-6 if isinstance(x, float) else x == y)
                    for x, y in zip(expected, got))
            elif isinstance(expected, float) and isinstance(got, float):
                ok = abs(expected - got) <= 1e-6
            else:
                ok = expected == got
            print(f"   {'MATCH' if ok else 'DIFF'}")
            if not ok:
                diffs += 1
        if dup:
            print("   WARNING: >1 tag at this offset (ambiguous)")
            diffs += 1
        row["status"] = "ok" if ok else "diff"
        rows_out.append(row)

    out = {"package": pkg.path, "rows": rows_out, "diffs": diffs}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        print(f"\nwrote {a.json}")
    print(f"\nrows {len(rows_out)}, diffs {diffs}")
    if a.check and diffs:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
