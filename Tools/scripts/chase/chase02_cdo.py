"""chase02_cdo.py - route 1 for F-9..F-16: does the CLASS DEFAULT object carry the value?

G1-21 (`grab_modes.py`) compared the declared BmSDK inventory with `objects.jsonl`, which only
holds the 15 `Playable_Batmobile*` packages. A property that is not serialised in a vehicle
archetype can still be serialised in the class's own default object (`Default__<Class>`), which
lives in the package that *defines* the class - `BmGame.upk`, not the Batmobile packages. This
script opens that package, finds the class (and its default object) and dumps the property-tag
stream, then reports whether the exact offsets the card names appear.

Read-only: opens the shipped package, writes nothing under the game folder.

Usage:
    python Tools/scripts/chase/chase02_cdo.py --list
    python Tools/scripts/chase/chase02_cdo.py --class R3rdPersonCamera
    python Tools/scripts/chase/chase02_cdo.py --class RVehicleBatmobileBase --json OUT.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk, TYPE_NAMES  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

# The offsets F-9..F-16 name, as ints (BmSDK absolute field offsets).
TARGETS = {
    "R3rdPersonCamera": {
        "BattleModeCamConfig": 0x3df4, "BattleModeWinchCamConfig": 0x3e9c,
        "BattleModeAbseilingCamConfig": 0x3f44, "BattleModeCamFOV": 0x4fd0,
        "BattleModeWinchCamFOV": 0x4fd4, "BattleModeHeadOffset": 0x4fdc,
        "BattleModeWinchHeadOffset": 0x4ff8, "BattleModeAbseilingExtraCameraRot": 0x5034,
    },
    "RVehicleBatmobileBase": {
        "StrafeCooldown": 0x11e4,
    },
    # chase-04 (F-25..F-32) and chase-06 (F-41..F-48) add the sim class below.
    "RVehicleSimBatmobile": {
        "BattleModeMaxSteering": 0x2cc, "BattleModeRearWheelTorquePower": 0x2d0,
        "BattleModeEngineBrakingFactor": 0x2dc, "BattleModeFrontThrottle": 0x2e4,
        "BattleModeRearThrottle": 0x2e8, "BattleModeMaxSpeed": 0x2f0,
        "BattleModeStopAndTurnAngleMoving": 0x2fc,
        "BattleModeTrailingSteerFactorTurnOnSpot": 0x31c,
    },
}


def open_pkg(path):
    pkg = Package(path)
    return pkg


def find_exports(pkg, needle):
    out = []
    for i, e in enumerate(pkg.exports, 1):
        name = e["name"] or ""
        if needle.lower() in name.lower():
            out.append({
                "index": i, "name": name,
                "class": pkg.class_name(e.get("class_index")),
                "outer": pkg.object_name(e.get("outer_index")),
                "size": e.get("size"),
            })
    return out


def dump_object(pkg, index):
    data = pkg.data(index)
    tags, end, stop = best_walk(pkg, data)
    rows = []
    for t in tags:
        row = {k: t.get(k) for k in ("type", "type_id", "offset", "name", "size",
                                     "array_index", "value")}
        if row["type_id"] is not None:
            row["type_name"] = TYPE_NAMES.get(row["type_id"])
        if "props" in t:
            row["props"] = [{k: p.get(k) for k in ("type_id", "name", "offset", "value")}
                            for p in t["props"]]
        if "items" in t:
            row["items"] = t["items"][:16]
        rows.append(row)
    return {"export_index": index, "class": pkg.class_name(pkg.exports[index - 1].get("class_index")),
            "bytes": len(data), "parsed": end, "stop": stop, "tags": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", default=os.path.join(GAME, "BmGame.upk"))
    ap.add_argument("--list", action="store_true", help="list matching exports for the card's classes")
    ap.add_argument("--class", dest="cls", help="class base name, e.g. R3rdPersonCamera")
    ap.add_argument("--json", help="write the decoded default object here")
    ap.add_argument("--scan", action="store_true",
                    help="check every Default__*Camera*/Batmobile*/Vehicle* object for a tag at the "
                         "card offsets (subclass overrides)")
    ap.add_argument("--offsets",
                    help="comma-separated hex field offsets for --scan (default: the F-9..F-16 set)")
    a = ap.parse_args()

    pkg = open_pkg(a.package)
    print(f"package {os.path.basename(pkg.path)}: version {pkg.version}, licensee {pkg.licensee}, "
          f"{len(pkg.names)} names, {len(pkg.imports)} imports, {len(pkg.exports)} exports")

    if a.list:
        for c in TARGETS:
            rows = find_exports(pkg, c)
            print(f"\n-- exports matching {c}: {len(rows)}")
            for r in rows[:40]:
                print("  ", r)
        return 0

    if a.scan:
        if a.offsets:
            want = sorted(int(x, 0) for x in a.offsets.split(",") if x.strip())
        else:
            want = sorted({o for d in TARGETS.values() for o in d.values()})
        cand = [i for i, e in enumerate(pkg.exports, 1)
                if (e["name"] or "").startswith("Default__") and
                any(k in (e["name"] or "") for k in ("Camera", "Batmobile", "Vehicle"))]
        print(f"\n-- scanning {len(cand)} Default__*Camera/Batmobile/Vehicle objects for offsets "
              f"{['0x%x' % w for w in want]}")
        found = 0
        for i in cand:
            data = pkg.data(i)
            tags, _end, _why = best_walk(pkg, data)
            hit = [(t.get("offset"), t.get("type_name"), t.get("value")) for t in tags
                   if t.get("offset") in want]
            if hit:
                found += 1
                print(f"   {pkg.exports[i - 1]['name']} (export {i}): {hit}")
        print(f"   -> {found} object(s) carry any of the card offsets")
        return 0

    if not a.cls:
        ap.print_help()
        return 2

    want = TARGETS.get(a.cls, {})
    hits = [r for r in find_exports(pkg, a.cls) if r["name"] in
            (a.cls, "Default__" + a.cls)]
    if not hits:
        print(f"no export named {a.cls} or Default__{a.cls} in {os.path.basename(pkg.path)}")
        return 1
    dumped = []
    for h in hits:
        print(f"\n=== {h['name']} (export {h['index']}, class {h['class']}, {h['size']} B)")
        d = dump_object(pkg, h["index"])
        d["name"] = h["name"]
        dumped.append(d)
        print(f"    walked {len(d['tags'])} tags, stop={d['stop']}")
        seen = {}
        for t in d["tags"]:
            off = t.get("offset")
            nm = t.get("name") or f"id_{t.get('offset')}"
            seen[off] = nm
            print(f"    {nm:<34} {t.get('type_name') or t.get('type')!s:<16} "
                  f"@0x{(off or 0):04x}  {t.get('value')!r}")
        if want:
            print(f"    -- card offsets on {a.cls}:")
            for field, off in sorted(want.items(), key=lambda kv: kv[1]):
                got = [t for t in d["tags"] if t.get("offset") == off]
                print(f"       {field:<34} @0x{off:04x}  "
                      f"{'SERIALISED ' + repr(got[0].get('value')) if got else 'absent'}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"package": pkg.path, "class": a.cls, "objects": dumped}, fh,
                      indent=1, sort_keys=True)
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
