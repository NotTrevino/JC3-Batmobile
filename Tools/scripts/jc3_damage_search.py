"""jc3_damage_search.py - where JC3 keeps damage, health and immunity.

The damage translation failed because the module vocabulary (`VehicleDamage`) has no
immunity member: `impact_damage_factor` can switch collision damage off, but nothing in
a `.vmodc` can say "bullets do not hurt this car". `Reports/JC3Grab/DAMAGE_MECHANISMS.md`
records the hypothesis; this tool is the search that answers it.

It walks every decoded `.epe` graph (232 vehicle entities, ~91k objects) and reports:

  * the root vehicle object's own `health` / `invulnerable` / `damage` properties;
  * every class and property whose name names damage, health, immunity or destruction;
  * value histograms, so a flag that ships on every vehicle is distinguishable from one
    that no vehicle uses (a candidate switch) and from a per-instance number.

The graphs are decoded by `jc3detail.py` into `_JC3grab/detail/*.ee.json`; this tool only
reads them. `--check` re-scans and compares against `DAMAGE_MECHANISMS.json`.

Usage:
  python jc3_damage_search.py --detail E:/Modding/_gamedata/JC3grab/detail --write
  python jc3_damage_search.py --detail E:/Modding/_gamedata/JC3grab/detail --check
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab", "DAMAGE_MECHANISMS.json")

DEFAULT_DETAIL = os.path.join(os.path.dirname(ROOT), "_gamedata", "JC3grab", "detail")   # moved 2026-11-02

TOKEN = re.compile(r"invuln|indestruct|immune|godmode|killable|damageable|destruct|breakable|"
                   r"wreck|health|damage|shield|armou?r|protect", re.I)
ROOT_CLASSES = ("CCar", "CBoat", "CHelicopter", "CMotorBike", "CAirPlane", "CTrain")
ROOT_PROPS = ("health", "invulnerable", "damage")


def hist(values: collections.Counter, limit: int = 8) -> dict:
    total = sum(values.values())
    return {"n": total,
            "distinct": len(values),
            "values": dict(sorted(values.items(), key=lambda kv: -kv[1])[:limit])}


def scan(detail_dir: str) -> dict:
    files = sorted(glob.glob(os.path.join(detail_dir, "*.ee.json")))
    if not files:
        raise SystemExit(f"no decoded entity graphs in {detail_dir}")
    roots: dict[str, dict] = {}
    token_classes: dict[str, dict] = {}
    token_props: dict[str, dict] = {}
    objects = 0
    entities = 0
    for path in files:
        entities += 1
        doc = json.load(open(path, encoding="utf-8"))
        ent = os.path.basename(doc.get("entity", path)).replace(".ee", "")
        objs = doc.get("epe", {}).get("objects", [])
        objects += len(objs)
        for o in objs:
            cls = o.get("class") or ""
            vals = o.get("values") or {}
            if cls in ROOT_CLASSES:
                r = roots.setdefault(cls, {"objects": 0, "entities": set(),
                                           "props": {p: collections.Counter() for p in ROOT_PROPS}})
                r["objects"] += 1
                r["entities"].add(ent)
                for p in ROOT_PROPS:
                    if p in vals:
                        r["props"][p][str(vals[p])] += 1
            if TOKEN.search(cls):
                c = token_classes.setdefault(cls, {"objects": 0, "entities": set(),
                                                   "props": collections.Counter()})
                c["objects"] += 1
                c["entities"].add(ent)
                for p in vals:
                    if TOKEN.search(p):
                        c["props"][p] += 1
            for p, v in vals.items():
                if not TOKEN.search(p):
                    continue
                key = f"{cls}.{p}"
                t = token_props.setdefault(key, {"class": cls, "property": p, "objects": 0,
                                                 "entities": set(), "values": collections.Counter()})
                t["objects"] += 1
                t["entities"].add(ent)
                t["values"][str(v)] += 1

    out_roots = {}
    for cls in ROOT_CLASSES:
        if cls not in roots:
            continue
        r = roots[cls]
        out_roots[cls] = {"objects": r["objects"], "entities": len(r["entities"]),
                          "props": {p: hist(c) for p, c in r["props"].items() if c}}
    out_classes = [{"class": k, "objects": v["objects"], "entities": len(v["entities"]),
                    "properties": dict(v["props"])}
                   for k, v in sorted(token_classes.items(), key=lambda kv: -kv[1]["objects"])]
    out_props = [{"property": k, "class": v["class"], "name": v["property"],
                  "objects": v["objects"], "entities": len(v["entities"]),
                  "values": hist(v["values"])}
                 for k, v in sorted(token_props.items(), key=lambda kv: -kv[1]["objects"])]
    return {"detail_dir": detail_dir, "entities": entities, "objects": objects,
            "root_classes": out_roots, "classes": out_classes, "properties": out_props}


def epe_fields(path: str, names=ROOT_PROPS) -> list[dict]:
    """Locate a root property in a compiled `.epe`: type byte, name hash, value bytes.

    An `.epe` serialises each property as `type byte, uint32 Jenkins hash, value`. The
    hash of the property name is therefore the address of the field, and a known value
    type says how many bytes follow (0x09 float32, 0x0e int32 - read off `health` and
    `damage`, which the graph dump gives as 100 and 670155287).
    """
    sys.path.insert(0, HERE)
    from rbmhdr import hash_jenkins  # noqa: E402
    blob = open(path, "rb").read()
    found = []
    for name in names:
        h = hash_jenkins(name.encode()) & 0xFFFFFFFF
        pat = h.to_bytes(4, "little")
        hits = [i for i in range(len(blob) - 4) if blob.startswith(pat, i)]
        for off in hits:
            value = blob[off + 4:off + 8]
            found.append({"name": name, "hash": f"{h:08x}", "type": f"0x{blob[off - 1]:02x}",
                          "type_at": off - 1, "hash_at": off, "value_at": off + 4,
                          "value": value.hex(" "),
                          "int": int.from_bytes(value, "little"),
                          "float": round(__import__("struct").unpack("<f", value)[0], 6)})
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--detail", default=DEFAULT_DETAIL)
    ap.add_argument("--epe", help="locate health/invulnerable/damage in a compiled .epe")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.epe:
        for f in epe_fields(a.epe):
            print(f"{f['name']:13} type {f['type']} @{f['type_at']:6}  hash {f['hash']} "
                  f"@{f['hash_at']:6}  value {f['value']} (int {f['int']}, float {f['float']}) "
                  f"@{f['value_at']}")
        return 0
    doc = scan(a.detail)
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"wrote {OUT}")
    if a.check:
        old = json.load(open(OUT, encoding="utf-8"))
        if old != doc:
            print("FAIL damage mechanisms: the decoded graphs no longer match the record")
            return 1
        print("PASS damage mechanisms")
    total = sum(r["objects"] for r in doc["root_classes"].values())
    print(f"{doc['entities']} entities, {doc['objects']} objects, "
          f"{total} vehicle roots, {len(doc['classes'])} token classes, "
          f"{len(doc['properties'])} token properties")
    for cls, r in doc["root_classes"].items():
        inv = r["props"].get("invulnerable", {})
        print(f"  {cls:14} {r['objects']:4} roots | invulnerable {inv.get('values', {})} | "
              f"health {r['props'].get('health', {}).get('values', {})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
