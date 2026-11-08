"""chase2_defaults.py - second pass for F-33..F-40: does any class default object TAG carry them?

`chase-05.md` proved its negative three ways, but none of them walked the CDO's *tag stream*:
it counted archetype tags in `objects.jsonl`, counted CDO-qualified **name strings** in
`GlobalPersistentCookerData.upk`, and scanned the executable for **immediate** stores. The name-string
test is the weak one, and chase-05 says so itself: `ImpactShakeVehicleFactor` is serialised 1.5 in
four archetypes yet has 0 CDO-qualified records, so "0 records" is not the same as "no tag".

This tool does the direct test. It opens `BmGame.upk`, walks every `Default__*` export's property tags
and reports any tag at one of the card offsets, with the object it belongs to. Offsets are exact
class-layout offsets, so a hit on the *owning* class is the value; a hit on a different class is a
layout coincidence (0x0268/0x0294 are low offsets thousands of structs share) and is printed as such.

The **positive control** is built in: `BattleModeWidth` 0x1994 and `BattleModeLength` 0x1998 are
serialised in the same default object (265.0 / 430.0, chase-04), so they must appear for a walk to be
trustworthy - and `BattleModeHeight` 0x199C sits between them. If 0x1994/0x1998 appear and 0x199C
does not, the absence of the height is a fact about the file, not about the walker.

Read-only: opens the package, writes only the `--json` path. No game launched.

Usage:
    python Tools/scripts/chase/chase2_defaults.py
    python Tools/scripts/chase/chase2_defaults.py --offsets 0x199c 0x1a60 --json OUT.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk  # noqa: E402

PKG = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk"
DEFAULT_JSON = r"E:\Modding\_shared\gamedata\BmAKgrab\chase\chase2_defaults.json"

# F-33 .. F-40, plus the two serialised class-mates that make the positive control.
ROWS = {
    0x1990: ("control BattleModeWidth", "RVehicleBatmobileBase"),
    0x1994: ("control BattleModeLength", "RVehicleBatmobileBase"),
    0x1998: ("control (unlabelled width/length neighbour F-32 class)", "RVehicleBatmobileBase"),
    0x199C: ("F-33 BattleModeHeight", "RVehicleBatmobileBase"),
    0x1A60: ("F-34 JumpRampUpwardForce", "RVehicleBatmobileBase"),
    0x1CC8: ("control ImpactShakeVehicleFactor", "RVehicleBatmobileBase"),
    0x1CCC: ("F-35 ImpactShakeAbandonedVehicleFactor", "RVehicleBatmobileBase"),
    0x1CD0: ("F-36 ImpactShakeDestructiblesFactor", "RVehicleBatmobileBase"),
    0x1CD4: ("F-37 ImpactShakeCoolDown", "RVehicleBatmobileBase"),
    0x1EB4: ("F-38 BattleModeSpeedDelta", "RVehicleBatmobileBase"),
    0x0268: ("F-39 TurnOnSpotSteeringSpeedCurve", "RVehicleSimBatmobile"),
    0x0294: ("F-40 BattleModeMoving", "RVehicleSimBatmobile"),
}
OWNED = {"RVehicleBatmobileBase", "RVehicleSimBatmobile"}


def walk_all(pkg):
    out = {}
    for i, e in enumerate(pkg.exports, 1):
        name = e["name"] or ""
        if not name.startswith("Default__"):
            continue
        try:
            tags, _end, why = best_walk(pkg, pkg.data(i))
        except Exception as exc:                                # noqa: BLE001 - never crash the sweep
            out[name] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        out[name] = {"export": i, "tags": tags, "stop": why,
                     "cls": pkg.class_name(e.get("class_index"))}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", default=PKG)
    ap.add_argument("--offsets", nargs="*", help="override the card offsets (hex)")
    ap.add_argument("--json", default=DEFAULT_JSON)
    a = ap.parse_args()

    want = {int(o, 0): ("(asked)", "") for o in a.offsets} if a.offsets else dict(ROWS)
    pkg = Package(a.package)
    print(f"{os.path.basename(pkg.path)}: {len(pkg.exports)} exports, image {len(pkg.image):,} B")
    objs = walk_all(pkg)
    print(f"walked {len(objs)} Default__ objects, "
          f"{sum(1 for v in objs.values() if 'tags' in v)} with a tag stream")

    hits = []
    for name, row in sorted(objs.items()):
        if "tags" not in row:
            if "error" in row:
                print(f"  ! {name}: {row['error']}")
            continue
        for t in row["tags"]:
            if t.get("offset") in want:
                hits.append({"object": name, "class": row["cls"], "export": row["export"],
                             "offset": t.get("offset"), "field": want[t["offset"]][0],
                             "owner_expected": want[t["offset"]][1],
                             "type": t.get("type"), "value": t.get("value"),
                             "bits": t.get("bits")})
    print(f"\n-- {len(hits)} tag(s) at the card offsets")
    for h in hits:
        owned = "OWNING CLASS" if (h["owner_expected"] and
                                   h["owner_expected"] in (h["class"] or "")) else "other class"
        print(f"   {h['field']:<46} {h['object']} ({h['class']}, export {h['export']}) "
              f"@0x{h['offset']:04x} {h['type']} = {h['value']!r}"
              + (f" bits=0x{h['bits']:08x}" if h.get("bits") is not None else "")
              + f"   [{owned}]")

    print("\n-- per row")
    for off, (label, owner) in sorted(want.items()):
        mine = [h for h in hits if h["offset"] == off]
        own = [h for h in mine if owner and owner in (h["class"] or "")]
        print(f"   0x{off:04x} {label:<46} hits {len(mine):>2}  "
              f"on {owner or '?':<24} {len(own)}  "
              f"{[(h['object'], h['value']) for h in own] or 'ABSENT'}")

    # neighbours, so an absence can be read against what the walker does see
    print("\n-- RVehicleBatmobileBase default object, tags between 0x1980 and 0x1CE0")
    for name in ("Default__RVehicleBatmobileBase",):
        row = objs.get(name, {})
        for t in row.get("tags", []):
            if 0x1980 <= (t.get("offset") or 0) <= 0x1CE0:
                print(f"   @0x{t['offset']:04x} {t.get('type'):<16} {t.get('name') or '':<34} "
                      f"{t.get('value')!r}")
    print("\n-- RVehicleSimBatmobile default object, tags between 0x200 and 0x400")
    for name in ("Default__RVehicleSimBatmobile",):
        row = objs.get(name, {})
        for t in row.get("tags", []):
            if 0x200 <= (t.get("offset") or 0) <= 0x400:
                print(f"   @0x{t['offset']:04x} {t.get('type'):<16} {t.get('name') or '':<34} "
                      f"{t.get('value')!r}")

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"package": pkg.path, "default_objects": len(objs), "hits": hits},
                      fh, indent=1, sort_keys=True)
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
