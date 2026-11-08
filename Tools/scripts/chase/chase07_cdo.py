"""chase07_cdo.py - route 1 for F-49..F-56: does the CLASS DEFAULT object carry the value?

Same gap chase-02/04/06 closed for other classes: G1-21 (`grab_modes.py`) only looked at
`objects.jsonl`, which covers the 15 `Playable_Batmobile*` packages.  A property that no
archetype writes can still be serialised in the class's own default object
(`Default__RVehicleSimBatmobile`), which lives in `BmGame.upk`.

This script dumps the default object's whole property-tag stream, reports whether the eight
F-49..F-56 offsets appear, and (with `--scan`) checks every other `Default__*Vehicle*` /
`Default__*Batmobile*` object for the same offsets, so a subclass default cannot hide a value.

Read-only: opens the shipped package, writes nothing under the game folder.

Usage:
  python Tools/scripts/chase/chase07_cdo.py --dump
  python Tools/scripts/chase/chase07_cdo.py --scan
  python Tools/scripts/chase/chase07_cdo.py --dump --json E:/Modding/_gamedata/BmAKgrab/chase/sim_cdo_07.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk, TYPE_NAMES  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

# F-49..F-56, BmSDK absolute offsets on RVehicleSimBatmobile (MODES.md, G1-21).
TARGETS = {
    "TransformationAnimNode": 0x354,
    "BattleModeUprightTorqueFactor": 0x370,
    "BattleModeUprightMaxTorque": 0x374,
    "TransformationRotation": 0x384,
    "TransformationTurnOnSpotSpeed": 0x398,
    "TransformationTurnFactor": 0x39c,
    "BattleModeSteerBiasRate": 0x3c4,
    "AirControlPitchTorqueFactorMax": 0x4ac,
}
CLS = "RVehicleSimBatmobile"


def dump(pkg, index):
    tags, end, stop = best_walk(pkg, pkg.data(index))
    rows = []
    for t in tags:
        rows.append({"offset": t.get("offset"), "name": t.get("name"),
                     "type": TYPE_NAMES.get(t.get("type_id")) or t.get("type"),
                     "type_id": t.get("type_id"), "size": t.get("size"),
                     "value": t.get("value")})
    return {"export_index": index,
            "class": pkg.class_name(pkg.exports[index - 1].get("class_index")),
            "bytes": len(pkg.data(index)), "parsed": end, "stop": stop, "tags": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", default=os.path.join(GAME, "BmGame.upk"))
    ap.add_argument("--dump", action="store_true", help="dump Default__RVehicleSimBatmobile")
    ap.add_argument("--scan", action="store_true",
                    help="look for the eight offsets on every Default__*Vehicle*/Batmobile object")
    ap.add_argument("--json", help="write the decoded default object here")
    a = ap.parse_args()

    pkg = Package(a.package)
    print(f"package {os.path.basename(pkg.path)}: version {pkg.version}, licensee {pkg.licensee}, "
          f"{len(pkg.names)} names, {len(pkg.imports)} imports, {len(pkg.exports)} exports")

    if a.scan:
        want = set(TARGETS.values())
        cand = [i for i, e in enumerate(pkg.exports, 1)
                if (e["name"] or "").startswith("Default__") and
                any(k in (e["name"] or "") for k in ("Vehicle", "Batmobile"))]
        print(f"\n-- scanning {len(cand)} Default__*Vehicle*/Batmobile objects for "
              f"{['0x%x' % w for w in sorted(want)]}")
        found = 0
        for i in cand:
            tags, _e, _s = best_walk(pkg, pkg.data(i))
            hit = [(hex(t["offset"]), t.get("name"), t.get("value")) for t in tags
                   if t.get("offset") in want]
            if hit:
                found += 1
                print(f"   {pkg.exports[i - 1]['name']} (export {i}): {hit}")
        print(f"   -> {found} object(s) carry any of the eight offsets")
        return 0

    if a.dump:
        hits = [i for i, e in enumerate(pkg.exports, 1)
                if (e["name"] or "") in (CLS, "Default__" + CLS)]
        if not hits:
            print(f"no export named {CLS} or Default__{CLS}")
            return 1
        dumped = []
        for i in hits:
            d = dump(pkg, i)
            d["name"] = pkg.exports[i - 1]["name"]
            dumped.append(d)
            print(f"\n=== {d['name']} (export {i}, class {d['class']}, {d['bytes']} B)")
            print(f"    walked {len(d['tags'])} tags, stop={d['stop']}")
            for t in d["tags"]:
                print(f"    {(t['name'] or 'id'):<44} {str(t['type']):<18} "
                      f"@0x{(t['offset'] or 0):04x}  {t['value']!r}")
            print(f"    -- F-49..F-56 offsets on {CLS}:")
            for field, off in sorted(TARGETS.items(), key=lambda kv: kv[1]):
                got = [t for t in d["tags"] if t["offset"] == off]
                if got:
                    print(f"       {field:<34} @0x{off:04x}  SERIALISED {got[0]['value']!r} "
                          f"({got[0]['type']})")
                else:
                    print(f"       {field:<34} @0x{off:04x}  absent")
        if a.json:
            os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
            with open(a.json, "w", encoding="utf-8") as fh:
                json.dump({"package": pkg.path, "class": CLS, "targets": TARGETS,
                           "objects": dumped}, fh, indent=1, sort_keys=True)
            print(f"wrote {a.json}")
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
