"""chase08_cdo.py - route 1 for F-57..F-64: does the CLASS DEFAULT object carry the value?

Same gap chase-02/04/06/07 closed for other classes: G1-21 (`grab_modes.py`) compared the declared
BmSDK inventory with `objects.jsonl`, which only holds the 15 `Playable_Batmobile*` packages. A
property no archetype writes can still be serialised in the class's own default object
(`Default__<Class>`), which lives in `BmGame.upk`.

This script covers the three classes the eight rows name:

  * `RVehicleSimBatmobile` - AirControlYawTorqueFactorMin / AirControlPitchTorqueFactorMin /
    AirControlInterpTime / AirControlTimeInAir / BattleModeSlopeFactor;
  * `RVehicleSimCar`      - AirControlTurnTorque;
  * `SVehicle`            - StayUprightRollResistAngle / StayUprightPitchResistAngle.

It dumps each class's default object tag stream, reports whether the card's offsets appear, and
with `--scan` checks every other `Default__*Vehicle*` / `Default__*Batmobile*` / `Default__S*`
object for the same offsets, so a subclass default cannot hide a value.

Read-only: opens the shipped package, writes nothing under the game folder.

Usage:
  python Tools/scripts/chase/chase08_cdo.py --dump
  python Tools/scripts/chase/chase08_cdo.py --scan
  python Tools/scripts/chase/chase08_cdo.py --dump --json E:/Modding/_gamedata/BmAKgrab/chase/value_cdo_08.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk, TYPE_NAMES  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

# F-57..F-64, BmSDK absolute offsets (MODES.md, G1-21; BMSDK_OFFSETS.json).
ROWS = {
    "RVehicleSimBatmobile": {
        "AirControlYawTorqueFactorMin": 0x4b0,
        "AirControlPitchTorqueFactorMin": 0x4b4,
        "AirControlInterpTime": 0x4b8,
        "AirControlTimeInAir": 0x4bc,
        "BattleModeSlopeFactor": 0x4c0,
    },
    "RVehicleSimCar": {
        "AirControlTurnTorque": 0x17c,
    },
    "SVehicle": {
        "StayUprightRollResistAngle": 0x6d4,
        "StayUprightPitchResistAngle": 0x6d8,
    },
}


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
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--json", help="write the decoded default objects here")
    a = ap.parse_args()

    pkg = Package(a.package)
    print(f"package {os.path.basename(pkg.path)}: version {pkg.version}, "
          f"licensee {pkg.licensee}, {len(pkg.names)} names, {len(pkg.imports)} imports, "
          f"{len(pkg.exports)} exports")

    if a.scan:
        want = {off for m in ROWS.values() for off in m.values()}
        cand = [i for i, e in enumerate(pkg.exports, 1)
                if (e["name"] or "").startswith("Default__") and
                any(k in (e["name"] or "") for k in ("Vehicle", "Batmobile", "Sim", "SVehicle"))]
        print(f"\n-- scanning {len(cand)} Default__*Vehicle*/Batmobile/Sim objects for "
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
        out = {"package": pkg.path, "rows": ROWS, "objects": []}
        for cls, targets in ROWS.items():
            hits = [i for i, e in enumerate(pkg.exports, 1)
                    if (e["name"] or "") in (cls, "Default__" + cls)]
            if not hits:
                print(f"\nno export named {cls} or Default__{cls}")
                continue
            for i in hits:
                d = dump(pkg, i)
                d["name"] = pkg.exports[i - 1]["name"]
                out["objects"].append(d)
                print(f"\n=== {d['name']} (export {i}, class {d['class']}, {d['bytes']} B)")
                print(f"    walked {len(d['tags'])} tags, stop={d['stop']}")
                if not d["name"].startswith("Default__"):
                    continue
                print(f"    -- F-57..F-64 offsets on {cls}:")
                for field, off in sorted(targets.items(), key=lambda kv: kv[1]):
                    got = [t for t in d["tags"] if t["offset"] == off]
                    if got:
                        print(f"       {field:<34} @0x{off:04x}  SERIALISED "
                              f"{got[0]['value']!r} ({got[0]['type']})")
                    else:
                        print(f"       {field:<34} @0x{off:04x}  absent")
        if a.json:
            os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
            with open(a.json, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=1, sort_keys=True)
            print(f"wrote {a.json}")
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
