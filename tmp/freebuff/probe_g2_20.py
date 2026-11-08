"""probe for G2-20: the exit vocabulary across the fleet + any launch/parachute member.

Read-only. Prints:
  * every distinct object name starting with `exit` with its count, classes and value keys
  * every object name anywhere in a graph mentioning eject/launch/parachute/wingsuit/glide/boost-exit
  * the exit objects of the donor with their full values
  * which root classes carry which exit
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import sys

RAW = os.environ.get("JC3_RAW", r"E:/Modding/JustCause3/_grab")
DETAIL = os.path.join(RAW, "detail")
ROOTS = ("CCar", "CBoat", "CHelicopter", "CMotorBike", "CAirPlane", "CTrain")
KEY = re.compile(r"eject|launch|parachute|wingsuit|glide|bail|jump", re.I)


def root_of(objs: list[dict]) -> str | None:
    for o in objs:
        if o.get("class") in ROOTS:
            return o["class"]
    return None


def main() -> int:
    files = sorted(glob.glob(os.path.join(DETAIL, "*.ee.json")))
    names: dict[str, dict] = {}
    keyed: dict[str, dict] = {}
    roots_by_exit: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    donor_dump = None
    for path in files:
        doc = json.load(open(path, encoding="utf-8"))
        objs = doc["epe"]["objects"]
        root = root_of(objs)
        for o in objs:
            nm = o.get("name") or ""
            if nm.startswith("exit"):
                rec = names.setdefault(nm, {"count": 0, "classes": set(), "keys": set(),
                                            "files": 0})
                rec["count"] += 1
                rec["classes"].add(o.get("class"))
                rec["keys"].update(o.get("values", {}))
                roots_by_exit[nm][root or "?"] += 1
            if nm and KEY.search(nm):
                rec = keyed.setdefault(nm, {"count": 0, "classes": set(), "keys": set()})
                rec["count"] += 1
                rec["classes"].add(o.get("class"))
                rec["keys"].update(o.get("values", {}))
            if (os.path.basename(path).startswith("v0300_car_kensington_sportsmuscle__")
                    and "civilian_01" in path and nm.startswith(("exit", "entry"))):
                donor_dump = donor_dump or []
                donor_dump.append({"node": o["node"], "name": nm, "class": o.get("class"),
                                   "values": o.get("values")})
    print(f"== {len(files)} graphs")
    print("== exit names")
    for nm in sorted(names, key=lambda k: -names[k]["count"]):
        r = names[nm]
        print(f"{r['count']:5} {nm:52} {sorted(x for x in r['classes'] if x)} "
              f"roots={dict(roots_by_exit[nm])} keys={sorted(r['keys'])[:8]}")
    print("== names mentioning eject/launch/parachute/wingsuit/glide")
    for nm in sorted(keyed, key=lambda k: -keyed[k]["count"]):
        r = keyed[nm]
        print(f"{r['count']:5} {nm:52} {sorted(x for x in r['classes'] if x)} "
              f"keys={sorted(r['keys'])[:8]}")
    print("== donor exit/entry objects")
    for o in donor_dump or []:
        print(json.dumps(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
