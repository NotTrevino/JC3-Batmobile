"""chase09_cdo.py - route 1 for F-65..F-72: class default objects for SVehicle, SVehicleWheel,
Pawn and RVehicleBatmobileBase.

F-65..F-67 are `VALUE-NATIVE` because no *archetype* carries the field; F-68..F-72 ask what a
number counts, which no archetype can answer either.  Both questions start at the class default
object (`Default__<Class>`), which G1-21 never read: `objects.jsonl` covers only the 15
`Playable_Batmobile*` packages, and the native base classes' CDOs live in `Engine.upk` /
`BmGame.upk`.  The script opens a package, finds the CDO of one class, dumps its tag stream and
reports the card offsets (value AND type, which is the first thing a unit question needs).

Read-only: opens the shipped packages, writes nothing under the game folder.

Usage:
  python Tools/scripts/chase/chase09_cdo.py --find                       # which package holds which CDO
  python Tools/scripts/chase/chase09_cdo.py --class SVehicle --dump
  python Tools/scripts/chase/chase09_cdo.py --class SVehicleWheel --dump --json OUT.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk, TYPE_NAMES  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
PACKAGES = ["Engine.upk", "BmGame.upk", "Core.upk"]

# class -> {field: offset} from Research/BatmobileGrab/MODES.md (G1-21) / BMSDK_OFFSETS.json
TARGETS = {
    "SVehicle": {
        "StayUprightRollResistAngle": 0x6d4,
        "StayUprightPitchResistAngle": 0x6d8,
        "StayUprightStiffness": 0x6dc,
        "StayUprightDamping": 0x6e0,
    },
    "SVehicleWheel": {
        "BattleModeSteerBias": 0x320,
    },
    "Pawn": {
        "AirControl": 0x448,
    },
    "RVehicleBatmobileBase": {
        "StrafeCooldown": 0x11e4,
        "BattleModeYawOffset": 0x1910,
        "ArmourModeDamageReduction": 0x1918,
    },
}


def dump_object(pkg, index):
    data = pkg.data(index)
    tags, end, stop = best_walk(pkg, data)
    rows = []
    for t in tags:
        rows.append({"offset": t.get("offset"), "name": t.get("name"),
                     "type": TYPE_NAMES.get(t.get("type_id")) or t.get("type"),
                     "size": t.get("size"), "value": t.get("value"),
                     "ref": t.get("ref"), "ref_class": t.get("ref_class")})
    return {"export_index": index,
            "class": pkg.class_name(pkg.exports[index - 1].get("class_index")),
            "bytes": len(data), "parsed": end, "stop": stop, "tags": rows}


def find_cdo(name):
    """(package path, export index) of Default__<name> in the packages we opened first."""
    for base in PACKAGES:
        path = os.path.join(GAME, base)
        if not os.path.exists(path):
            continue
        pkg = Package(path)
        for i, e in enumerate(pkg.exports, 1):
            if (e["name"] or "") == "Default__" + name:
                yield path, pkg, i
                break


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--find", action="store_true", help="locate every target CDO")
    ap.add_argument("--class", dest="cls", choices=sorted(TARGETS), help="class to dump")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--json", help="write the decoded default object here")
    a = ap.parse_args()

    if a.find:
        for cls in sorted(TARGETS):
            got = list(find_cdo(cls))
            print(f"{cls:<24} " + (", ".join(f"{os.path.basename(p)} export {i}" for p, _p, i in got)
                                   or "NOT FOUND in " + ", ".join(PACKAGES)))
        return 0

    if not (a.cls and a.dump):
        ap.print_help()
        return 2

    hits = list(find_cdo(a.cls))
    if not hits:
        print(f"no Default__{a.cls} in {', '.join(PACKAGES)}")
        return 1
    dumped = []
    for path, pkg, i in hits:
        d = dump_object(pkg, i)
        d["package"] = path
        d["name"] = pkg.exports[i - 1]["name"]
        dumped.append(d)
        print(f"\n=== {d['name']} ({os.path.basename(path)}, export {i}, class {d['class']}, "
              f"{d['bytes']} B)  tags {len(d['tags'])}, stop={d['stop']}")
        for t in d["tags"]:
            print(f"    {str(t['name'] or 'id'):<44} {str(t['type']):<18} "
                  f"@0x{(t['offset'] or 0):04x}  {t['value']!r}"
                  + (f" -> {t['ref']}" if t.get("ref") else ""))
        print(f"    -- card offsets on {a.cls}:")
        for field, off in sorted(TARGETS[a.cls].items(), key=lambda kv: kv[1]):
            got = [t for t in d["tags"] if t["offset"] == off]
            if got:
                print(f"       {field:<34} @0x{off:04x}  SERIALISED {got[0]['value']!r} "
                      f"({got[0]['type']}, {got[0]['size']} B)")
            else:
                print(f"       {field:<34} @0x{off:04x}  absent")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"class": a.cls, "targets": TARGETS[a.cls], "objects": dumped},
                      fh, indent=1, sort_keys=True)
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
