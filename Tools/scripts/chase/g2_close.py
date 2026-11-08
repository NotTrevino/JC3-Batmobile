#!/usr/bin/env python
"""g2_close.py - attempts to close the 'Limits'/'UNKNOWN' statements of the G2 cards from data.

Read-only. Three routes, one per subcommand:

  tanks   G2-21: is there a module member that only the tracked vehicles carry (the "no data
          member distinguishes a pivot-capable tank" claim)?  Also: what does
          `wheels_friction_type` actually track, and what is `number_of_front_wheels` = -1?
  refs    G2-16: does any object in the EMP truck's `.epe` point at the EMP pulse?  (The card
          says no trigger/entry link exists; this scans every string property of every object.)
  index   G2-16/G2-17: does a dangling `<hash>=<oid>` reference name a path in the JC3 index?

Usage:
  python Tools/scripts/chase/g2_close.py tanks
  python Tools/scripts/chase/g2_close.py refs
  python Tools/scripts/chase/g2_close.py index 5FED74E7
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

TANKS = ("v0200_car_capstone_apc", "v0201_car_capstone_mediumtank",
         "v0202_car_capstone_bavariumtank", "v0603_car_urga_smalltank")


def members_by_chassis() -> tuple[dict, dict]:
    """chassis -> {member path: value}, and chassis -> {module type}."""
    mem = collections.defaultdict(dict)
    mods = collections.defaultdict(set)
    for p in glob.glob(os.path.join(RAW, "entities", "*.json")):
        doc = json.load(open(p, encoding="utf-8"))
        ent = doc.get("entity", "")
        if "/01_land/" not in ent:
            continue
        parts = ent.split("/")
        chassis = parts[parts.index("jc_vehicles") + 2] if "jc_vehicles" in parts else ent
        for m in doc.get("modules", {}).values() if isinstance(doc.get("modules"), dict) \
                else doc.get("modules", []):
            if not isinstance(m, dict):
                continue
            mods[chassis].add(m.get("type"))
            for r in m.get("rows", []):
                mem[chassis][f"{m.get('type')}.{r.get('path')}"] = r.get("value")
    return mem, mods


def cmd_tanks() -> int:
    mem, mods = members_by_chassis()
    land = {c: v for c, v in mem.items() if not c.startswith("v5603")}
    tanks = {c: v for c, v in land.items() if c in TANKS}
    others = {c: v for c, v in land.items() if c not in TANKS}
    print(f"land chassis {len(land)}, of which tanks {len(tanks)}: {sorted(tanks)}")

    only = collections.Counter()
    for c, rows in tanks.items():
        for k in rows:
            if all(k not in o for o in others.values()):
                only[k] += 1
    print(f"\n-- member paths carried only by tanks ({len(only)}), with how many tanks carry it")
    for k, n in only.most_common(40):
        vals = sorted({json.dumps(tanks[c][k]) for c in tanks if k in tanks[c]})
        print(f"   {n}/4  {k:<55} values {vals[:4]}")

    # the card's three named candidates
    print("\n-- the members TANKTURN.md names")
    for key in ("LandGlobal.wheels_friction_type", "LandGlobal.number_of_front_wheels",
                "LandGlobal.front_wheels.use_shape_cast"):
        print(f"   {key}")
        dist = collections.Counter()
        for c, rows in sorted(land.items()):
            if key in rows:
                dist[(rows[key], c in TANKS)] += 1
        for (v, istank), n in sorted(dist.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
            print(f"      value {v!r:<8} tank={istank}  x{n}")

    # what friction_type groups
    print("\n-- wheels_friction_type by chassis (land)")
    per = collections.defaultdict(list)
    for c, rows in land.items():
        if "LandGlobal.wheels_friction_type" in rows:
            per[rows["LandGlobal.wheels_friction_type"]].append(c)
    for v, cs in sorted(per.items(), key=lambda kv: str(kv[0])):
        print(f"   type {v}: {len(cs)} chassis; tanks in it: "
              f"{[c for c in cs if c in TANKS]}; sample {sorted(cs)[:6]}")
    return 0


def cmd_refs() -> int:
    import jc3index
    import jc3wiring
    ee = ("editor/entities/jc_vehicles/01_land/v0505_car_solar_oldtruck/"
          "v0505_car_solar_oldtruck_rebel_emp_01.ee")
    rows = jc3index.load_index(os.path.join(ROOT, "Research", "JC3Grab"))
    objs, _doc = jc3wiring.decode_epe(ee, rows, jc3index.DEFAULT_GAME)
    print(f"{len(objs)} objects in {ee.rsplit('/', 1)[-1]}")
    for pulse in (o for o in objs if o.cls == "CForcePulse"):
        hits = [(o.cls, o.name, k) for o in objs for k, v in o.props.items()
                if isinstance(v, str) and pulse.oid and pulse.oid in v]
        print(f"\npulse {pulse.name} oid {pulse.oid}: {len(hits)} object(s) carry that id")
        for h in hits:
            print(f"   {h[0]:<24} {h[1]:<28} {h[2]}")
    for entry in (o for o in objs if o.cls in ("CInteractionGraphEntry", "CInteractionTrigger")):
        print(f"\n{entry.cls} {entry.name}:")
        for k, v in sorted(entry.props.items()):
            if k.startswith("id:") and isinstance(v, str) and v:
                print(f"   {k} -> {v}")
    return 0


def cmd_index(want: str) -> int:
    want = want.upper()
    hits, n = [], 0
    for line in open(os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl"), encoding="utf-8"):
        if not line.strip():
            continue
        n += 1
        r = json.loads(line)
        if str(r.get("hash", "")).upper() == want:
            hits.append((r.get("path"), r.get("archive"), r.get("size")))
    print(f"index rows {n}; hash {want}: {len(hits)} path(s)")
    for h in hits:
        print("  ", h)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=("tanks", "refs", "index"))
    ap.add_argument("hash", nargs="?")
    a = ap.parse_args()
    if a.what == "tanks":
        return cmd_tanks()
    if a.what == "refs":
        return cmd_refs()
    if not a.hash:
        sys.exit("index needs a hash, e.g. 5FED74E7")
    return cmd_index(a.hash)


if __name__ == "__main__":
    raise SystemExit(main())
