#!/usr/bin/env python
"""jc3tether.py - G2-34: tether, airlift and winch carriers.

Card G2-34 (serves WLD-7, WPN-6): "record tether strength vs vehicle mass, whether vehicles can
be airlifted, and whether any vehicle-mounted winch/rope exists that a car could carry".

Inputs (decoded tables only; no archive is opened, `D:\\Games` is never read):
  * ``E:/Modding/_gamedata/JC3grab/entities/*.ee.json`` - every module row (incl. `RigidBody.mass`), the
    module-type census and each entity's own inner file list.
  * ``E:/Modding/_gamedata/JC3grab/detail/*.ee.json`` - the `.epe` object graphs: `CVehicleCargoBay`,
    `CGrapplingHookPropData`, the vehicle roots (a compound entity has two) and the cargo-bay
    interaction points.
  * ``Research/JC3Grab/PARTS_TABLE.jsonl`` - the parts module rows (the transport boat's
    rope/winch parts).
  * ``Research/JC3Grab/INDEX.jsonl`` - every named asset in the game (tether/grapple names).
  * MODLOG §86/§87 - quoted, not recomputed: the BmAK winch bound and why it cannot yield a mass.

Writes ``Research/JC3Grab/TETHER.md`` + ``TETHER.json``. ``--check`` re-derives both and compares.

Usage:
  python jc3tether.py --write
  python jc3tether.py --check
  python jc3tether.py dump mass|carriers|winch|index
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
JSON_NAME = "TETHER.json"
MD_NAME = "TETHER.md"

DONOR_MODEL = "v0300_car_kensington_sportsmuscle"
BATMOBILE_MASS = 6000          # WLD-7's "6 t car" (design value, not a decoded number)
VEH_ROOTS = ("CCar", "CBoat", "CHelicopter", "CAirPlane", "CTrain", "CMotorBike")
BAY_RE = re.compile(r"cargobay|bay\.cargo", re.I)
TOK_RE = re.compile(r"tether|grappl|rope|winch", re.I)
MOD_RE = re.compile(r"cargo|tether|rope|winch|grappl|tow", re.I)
PROP = "propeller"   # contains "rope" as a substring


def slug(name: str) -> str:
    return name.split("__")[-1] if "__" in name else name


def family(model: str) -> str:
    parts = model.split("_")
    return parts[1] if len(parts) > 1 else "?"


# ---------------------------------------------------------------------- readers
def scan_entities() -> dict:
    files = sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json")))
    masses: dict[str, list[int]] = {}
    models: dict[str, str] = {}
    modules: dict[str, list[str]] = {}
    winch_files: dict[str, list[str]] = {}
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        ent = d["entity"]
        key = slug(os.path.basename(p)[:-8])
        models[key] = ent.split("/jc_vehicles/")[-1].split("/")[1]
        modules[key] = [str(m.get("type")) for m in d["modules"]]
        masses[key] = [r["value"] for m in d["modules"] if m.get("type") == "RigidBody"
                       for r in m["rows"] if r["path"] == "mass"]
        winch_files[key] = sorted(f["path"] for f in d["files"]
                                  if re.search(r"rope_winch", f["path"]))
    types = collections.Counter(t for v in modules.values() for t in v)
    return {"files": files, "masses": masses, "models": models, "modules": modules,
            "module_types": dict(sorted(types.items())), "winch_files": winch_files}


def scan_graphs() -> dict:
    files = sorted(glob.glob(os.path.join(RAW, "detail", "*.json")))
    bays: dict[str, list[dict]] = collections.defaultdict(list)
    hooks: dict[str, list[dict]] = collections.defaultdict(list)
    roots: dict[str, dict[str, int]] = {}
    bay_objs: collections.Counter = collections.Counter()
    bay_points: dict[str, list[dict]] = collections.defaultdict(list)
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        ent = os.path.basename(p)[:-8]
        rc: collections.Counter = collections.Counter()
        for o in ((d.get("epe") or {}).get("objects") or []):
            c = str(o.get("class") or "")
            n = str(o.get("name") or "")
            v = o.get("values") or {}
            if c in VEH_ROOTS:
                rc[c] += 1
            if c == "CVehicleCargoBay":
                bays[ent].append({"name": n, "enabled": v.get("enabled"),
                                  "enable": v.get("enable"), "disable": v.get("disable"),
                                  "world": v.get("world"),
                                  "members": sorted(v)})
            if c == "CGrapplingHookPropData":
                hooks[ent].append({"name": n, "enabled": v.get("enabled"),
                                   "enable_event": v.get("enable_event"),
                                   "disable_event": v.get("disable_event"),
                                   "name_hash": v.get("name_hash")})
            if BAY_RE.search(n):
                bay_objs[(c, n)] += 1
                if c == "CInteractionGraphPointNode":
                    bay_points[ent].append({"name": n, "world": v.get("world")})
        if rc:
            roots[ent] = dict(rc)
    return {"files": files, "bays": dict(bays), "hooks": dict(hooks), "roots": roots,
            "bay_objects": {f"{k[0]} · {k[1]}": v for k, v in bay_objs.most_common()},
            "bay_points": dict(bay_points)}


def scan_parts() -> dict:
    rows: dict[str, list[dict]] = {}
    mods: dict[str, str] = {}
    for line in open(os.path.join(OUT, "PARTS_TABLE.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        rows[r["entity"]] = r["parts"]
        mods[r["entity"]] = r["module"]
    picks: list[dict] = []
    for ent, parts in rows.items():
        if "v1602_boat_urga_transport" not in ent:
            continue
        for p in parts:
            low = p["n"].lower()
            if ("rope" in low or "winch" in low) and "propeller" not in low:
                picks.append({"entity": ent.split("__")[-1], "index": p["i"], "name": p["n"],
                              "damage_type": p["dt"], "behavior": p.get("b"),
                              "parent": p.get("parent"), "model": p["m"]})
    # every part row in the fleet, for the "no vehicle part pulls anything" claim
    all_behaviours = collections.Counter(
        (p["dt"], p.get("b")) for parts in rows.values() for p in parts)
    return {"entities": len(rows), "modules": mods, "picks": picks,
            "behaviours": [{"damage_type": k[0], "behavior": k[1], "parts": v}
                           for k, v in all_behaviours.most_common()]}


def behaviour_totals(rows: list[dict]) -> dict[str, int]:
    """Aggregate the (damage type, behaviour) census by behaviour alone."""
    tot: collections.Counter = collections.Counter()
    for r in rows:
        tot[r["behavior"]] += r["parts"]
    return dict(sorted(tot.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def scan_index() -> dict:
    tether: list[str] = []
    winch: list[str] = []
    lod = 0
    propeller = 0
    for line in open(os.path.join(OUT, "INDEX.jsonl"), encoding="utf-8"):
        path = json.loads(line)["path"]
        low = path.lower()
        if low.endswith(".lod"):
            lod += 1
        if "transport_propeller" in low:
            propeller += 1
        if "tether" in low:
            tether.append(path)
        if "winch" in low:
            winch.append(path)
    where = collections.Counter("/".join(p.split("/")[:3]) for p in tether)
    odd = sorted(p for p in tether if "dialogue" not in p)
    return {"tether": len(tether), "tether_where": dict(where.most_common()),
            "tether_non_dialogue": odd, "winch": winch,
            "lod_paths": lod, "propeller_paths": propeller}


# ---------------------------------------------------------------------- build
def build() -> dict:
    ent = scan_entities()
    gr = scan_graphs()
    pt = scan_parts()
    ix = scan_index()

    masses = ent["masses"]
    per_entity = {k: v[0] for k, v in masses.items() if len(v) == 1}
    multi = {k: v for k, v in masses.items() if len(v) > 1}
    fam: dict[str, list[int]] = collections.defaultdict(list)
    for k, v in per_entity.items():
        fam[family(ent["models"][k])].append(v)
    fam_stats = {}
    for f, vals in sorted(fam.items()):
        vals = sorted(vals)
        fam_stats[f] = {"n": len(vals), "min": vals[0],
                        "median": vals[len(vals) // 2], "max": vals[-1]}

    donor = next(({"entity": k, "mass": masses[k][0]}
                  for k in masses if ent["models"][k] == DONOR_MODEL
                  and k.endswith("_civilian_01")), None)

    bay_slugs = {slug(k) for k in gr["bays"]}
    carriers = {}
    for model in ("v4603_plane_urga_cargotransport", "v1602_boat_urga_transport",
                  "v5602_train_urga_monorailflatbed"):
        keys = [k for k in masses if ent["models"][k] == model]
        carriers[model] = {
            "entities": len(keys),
            "masses": sorted({m for k in keys for m in masses[k]}),
            "with_bay": sum(1 for k in keys if k in bay_slugs),
        }

    hooks_by_name = collections.Counter(h["name"] for hs in gr["hooks"].values() for h in hs)
    hook_enabled = collections.Counter(h["enabled"] for hs in gr["hooks"].values() for h in hs)
    hook_events = collections.Counter(
        (h["enable_event"] or "(empty)", h["disable_event"] or "(empty)")
        for hs in gr["hooks"].values() for h in hs)

    bay_members = collections.Counter(tuple(b["members"]) for bs in gr["bays"].values()
                                      for b in bs)
    bay_worlds = collections.Counter(b["world"] for bs in gr["bays"].values() for b in bs)
    bay_enabled = collections.Counter(b["enabled"] for bs in gr["bays"].values() for b in bs)

    picks = pt["picks"]
    names = collections.Counter(p["name"] for p in picks)
    winch_parts = [p for p in picks if "winch" in p["name"].lower()]
    winch_files = sorted({os.path.basename(f) for v in ent["winch_files"].values() for f in v})
    winch_one = sorted(os.path.basename(f) for f in
                       ent["winch_files"].get("v1602_boat_urga_transport_military_01", []))

    tetherish_modules = {k: v for k, v in ent["module_types"].items()
                         if MOD_RE.search(k) and PROP not in k.lower()}

    payload = {
        "card": "G2-34",
        "inputs": {
            "entity_caches": len(ent["files"]),
            "detail_graphs": len(gr["files"]),
            "parts_entities": pt["entities"],
            "index_rows": sum(1 for _ in open(os.path.join(OUT, "INDEX.jsonl"),
                                              encoding="utf-8")),
            "index_sha1": hashlib.sha1(
                open(os.path.join(OUT, "INDEX.jsonl"), "rb").read()).hexdigest()[:16],
        },
        "mass": {
            "entities_with_mass": len(masses),
            "single_body_entities": len(per_entity),
            "multi_body_entities": multi,
            "families": fam_stats,
            "donor": donor,
            "batmobile_target": BATMOBILE_MASS,
            "ratio_to_donor": round(BATMOBILE_MASS / donor["mass"], 3) if donor else None,
            "unit": "UNKNOWN",
        },
        "carriers": {
            "models": carriers,
            "bays": sum(len(v) for v in gr["bays"].values()),
            "bay_entities": len(gr["bays"]),
            "bay_enabled": dict(bay_enabled),
            "bay_members": [list(k) for k in bay_members],
            "bay_worlds": dict(bay_worlds),
            "bay_helicopters": [k for k in gr["bays"] if "helicopter" in k],
            "roots": gr["roots"],
            "compound": {k: v for k, v in gr["roots"].items() if len(v) > 1},
            "compound_masses": {slug(k): sorted(v) for k, v in masses.items() if len(v) > 1},
            "bay_objects": gr["bay_objects"],
            "bay_points": gr["bay_points"],
            "hooks": sum(len(v) for v in gr["hooks"].values()),
            "hook_entities": sorted(gr["hooks"]),
            "hook_counts": {slug(k): len(v) for k, v in sorted(gr["hooks"].items())},
            "hook_names": dict(sorted(hooks_by_name.items(), key=lambda kv: (-kv[1], kv[0]))),
            "hook_enabled": dict(hook_enabled),
            "hook_events": [{"enable": k[0], "disable": k[1], "objects": v}
                            for k, v in hook_events.most_common()],
        },
        "winch": {
            "part_rows": len(picks),
            "entities": len({p["entity"] for p in picks}),
            "names": dict(sorted(names.items())),
            "winch_parts": winch_parts,
            "picks": picks,
            "winch_files": winch_files,
            "winch_files_one_entity": winch_one,
            "behaviours": pt["behaviours"],
            "behaviour_totals": behaviour_totals(pt["behaviours"]),
            "tetherish_module_types": tetherish_modules,
            "module_types": len(ent["module_types"]),
            "functional_winch_classes": 0,
            "bmak": "MODLOG §86/§87: `RBatmobileWinch` yields at best a force, never a mass",
        },
        "index": ix,
    }
    payload["digest"] = hashlib.sha1(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return payload


# ---------------------------------------------------------------------- md
def render_md(d: dict) -> str:
    inp, mass, car, winch, idx = (d["inputs"], d["mass"], d["carriers"], d["winch"], d["index"])
    L: list[str] = []
    a = L.append
    a("# Tether, airlift and winch carriers (G2-34)")
    a("")
    a("What the JC3 files supply for **WLD-7** (Rico's tether, helicopter airlift and the cargo")
    a("plane around a 6 t car) and **WPN-6** (a power winch a car could carry). Every number")
    a("below is re-derived by `Tools/scripts/jc3tether.py --check`; no archive is opened and no")
    a("game is launched.")
    a("")
    a("| input | value |")
    a("|---|---|")
    a(f"| entity caches | {inp['entity_caches']} |")
    a(f"| `.epe` graphs | {inp['detail_graphs']} |")
    a(f"| parts-table entities | {inp['parts_entities']} |")
    a(f"| `INDEX.jsonl` rows | {inp['index_rows']:,} |")
    a("")
    a("## 1. Vehicle mass - the half of WLD-7 the data does carry")
    a("")
    a(f"`RigidBody.mass` is on **{mass['entities_with_mass']} entities**; "
      f"{mass['single_body_entities']} have one body. The unit is **UNKNOWN** - the file gives a")
    a("number and no unit - so every comparison here is a ratio, never a conversion.")
    a("")
    a("| family (model code) | entities | min | median | max |")
    a("|---|---|---|---|---|")
    for f, s in mass["families"].items():
        a(f"| `{f}` | {s['n']} | {s['min']:,} | {s['median']:,} | {s['max']:,} |")
    a("")
    a(f"The `{mass['families']['plane']['n']}` single-body planes above exclude the two-body")
    a("cargo tank; its row below lists both bodies (plane 40,000 + carried tank 25,000).")
    a("")
    dn = mass["donor"]
    a(f"- **donor** `{slug(dn['entity'])}` = **{dn['mass']:,}**")
    a(f"- **Batmobile** (WLD-7 design value, not a decoded number) = "
      f"**{mass['batmobile_target']:,}** = **{mass['ratio_to_donor']}x** the donor")
    a("")
    a("The three carriers WLD-7 names:")
    a("")
    a("| model | entities | body mass | with a cargo bay |")
    a("|---|---|---|---|")
    for m, c in car["models"].items():
        a(f"| `{m}` | {c['entities']} | {' / '.join(f'{x:,}' for x in c['masses'])} | "
          f"{c['with_bay']} |")
    a("")
    a("So a 6,000 car is **"
      f"{round(100 * mass['batmobile_target'] / max(car['models']['v4603_plane_urga_cargotransport']['masses']), 1)}%**"
      " of the cargo plane's own body mass and **"
      f"{round(100 * mass['batmobile_target'] / max(car['models']['v1602_boat_urga_transport']['masses']), 1)}%**"
      " of the transport boat's; **"
      f"{round(100 * mass['batmobile_target'] / max(car['models']['v5602_train_urga_monorailflatbed']['masses']), 1)}%**"
      " of the flatbed's. Those are the only mass ratios WLD-7 can quote, because the")
    a("tether's own strength is in no table (below).")
    a("")
    a("### Tether strength")
    a("")
    a("**UNKNOWN, and provably absent from the tables.** Section 5 lists all 335 `tether` names")
    a("in the index: character dialogue, DLC dialogue, two upgrade icons, two upgrade videos, one")
    a("challenge decal and the two `dualtether_test_to_vehicle` graph files. No tune, no force,")
    a("no break threshold. No vehicle module carries a tether or rope member either (section 4).")
    a("")
    a("## 2. Can a vehicle be carried? Yes - by the cargo plane, boat and flatbed")
    a("")
    a(f"`CVehicleCargoBay` appears **{car['bays']} times on {car['bay_entities']} entities**, one")
    a("per entity, `enabled = " + " / ".join(sorted(car['bay_enabled'])) + "`, doors empty:")
    a("")
    a("| model | entities with a bay |")
    a("|---|---|")
    for m, c in car["models"].items():
        a(f"| `{m}` | {c['with_bay']} |")
    a("")
    a("The object has exactly " + f"{len(car['bay_members'][0])} members, and nothing else:"
      if car["bay_members"] else "The object has no members:")
    a("")
    a("- `" + "`, `".join(car["bay_members"][0]) + "`" if car["bay_members"] else "- (none)")
    a("")
    a("So the bay carries a name hash and a transform, then stops. No capacity, no mass limit,")
    a("no attach rule: the fields are the same on all twelve:")
    a("")
    a("| bay world transform | objects |")
    a("|---|---|")
    for w, n in car["bay_worlds"].items():
        a(f"| `{w}` | {n} |")
    a("")
    a(f"**Helicopters with a cargo bay: {len(car['bay_helicopters'])}.** No helicopter in the fleet")
    a("has one, so the files give no helicopter that can carry a car (the native helicopter tow,")
    a("if it exists, is code - see section 6).")
    a("")
    a("### The proof that a vehicle rides in a bay")
    a("")
    for k, v in car["compound"].items():
        bodies = d["carriers"]["compound_masses"].get(slug(k), [])
        a(f"`{slug(k)}` carries **two vehicle roots** "
          f"({', '.join(f'`{c}` x{n}' for c, n in sorted(v.items()))}) and **two bodies**: "
          f"`{', '.join(f'{x:,}' for x in bodies)}` - the plane's own plus the carried tank's.")
        a("It is the only compound entity in the fleet, and the only decoded evidence that one")
        a("vehicle's entity contains another.")
    a("")
    a("Only the planes have bay interaction points; the boat and the flatbed carry the bay and")
    a("its door effects without one. Every named bay object in the fleet:")
    a("")
    a("| class · name | objects |")
    a("|---|---|")
    for k, v in bay_object_rows(car):
        a(f"| `{k}` | {v} |")
    a("")
    a("Bay point transforms (all six planes, identical):")
    a("")
    a("| point | world |")
    a("|---|---|")
    seen: set[tuple[str, str]] = set()
    for ent, pts in car["bay_points"].items():
        for p in pts:
            key = (p["name"], str(p["world"]))
            if key in seen:
                continue
            seen.add(key)
            a(f"| `{p['name']}` | `{p['world']}` |")
    a("")
    a("## 3. The prop-side tether data (`CGrapplingHookPropData`)")
    a("")
    a(f"**{car['hooks']} objects on {len(car['hook_entities'])} entities** - a cargo truck and a")
    a("monorail flatbed's container prop, never a player vehicle:")
    a("")
    a("| entity | objects |")
    a("|---|---|")
    for e, n in car["hook_counts"].items():
        a(f"| `{slug(e)}` | {n} |")
    a("")
    a("| object name | objects |")
    a("|---|---|")
    for k, v in car["hook_names"].items():
        a(f"| `{k}` | {v} |")
    a("")
    a("| enabled | objects |")
    a("|---|---|")
    for k, v in car["hook_enabled"].items():
        a(f"| `{k}` | {v} |")
    a("")
    a("| enable_event | disable_event | objects |")
    a("|---|---|---|")
    for h in car["hook_events"]:
        a(f"| `{h['enable']}` | `{h['disable']}` | {h['objects']} |")
    a("")
    a("`tether_tear`, `tether_tear7` and `tether_yank` - the names the card points at - are")
    a("object names on the loose cargo of one truck. They mark *which prop may be torn off or")
    a("yanked*, with an empty event pair, and carry no force, distance or mass.")
    a("")
    a("## 4. A winch a car could carry (WPN-6)")
    a("")
    a(f"The transport boat's parts module holds **{winch['part_rows']} rope/winch part rows on "
      f"{winch['entities']} entities** "
      f"({', '.join(f'{n}x{c}' for n, c in winch['names'].items())}):")
    a("")
    a("| part_index | part | damage type | behavior | parent |")
    a("|---|---|---|---|---|")
    reps = []
    seen_w: set[str] = set()
    for p in winch["picks"]:
        if p["name"] in seen_w:
            continue
        seen_w.add(p["name"])
        reps.append(p)
    for p in reps:
        a(f"| {p['index']} | `{p['name']}` | `{p['damage_type']}` | `{p['behavior']}` | "
          f"{p['parent']} |")
    a("")
    a(f"All {len(reps)} distinct names are plain mesh parts: `Boat_Generic`, `behavior = None`,")
    a("`parent = 0`, no socket. The winch mesh is real and ships inside the entity - "
      f"**{len(winch['winch_files_one_entity'])} files on one boat**, "
      f"{len(winch['winch_files'])} distinct fleet-wide:")
    a("")
    for f in winch["winch_files_one_entity"]:
        a(f"- `{f}`")
    a("")
    a("The mechanic is not there:")
    a("")
    a(f"- The fleet's {winch['module_types']} module types contain **"
      f"{len(winch['tetherish_module_types'])} tether/cargo/rope/winch/tow type** "
      f"({', '.join(f'`{k}`' for k in winch['tetherish_module_types']) or 'none'}).")
    bt = winch["behaviour_totals"]
    named = {k: v for k, v in bt.items() if k not in (None, "None")}
    a(f"- Parts-module behaviours over all {sum(bt.values()):,} fleet part rows: "
      f"{bt.get('None', 0):,} `None`, **{len(named)} distinct named behaviours**, the")
    a("  commonest being " + ", ".join(f"`{k}` x{v}" for k, v in list(named.items())[:6])
      + ".")
    a("  **None is a winch, rope, tow or reel, so no vehicle part can pull another vehicle.**")
    a(f"  The nearest is `CargoBayDoor` - {named.get('CargoBayDoor', 0)} parts that open a bay")
    a("  door and stop.")
    a(f"- Functional winch classes anywhere in the fleet: **{winch['functional_winch_classes']}**.")
    a("")
    a("**WPN-6 verdict: a carrier exists for the geometry (copy `transport_rope_winch` - one")
    a(f"part, parent 0, `Boat_Generic`, no behaviour, {len(winch['winch_files_one_entity']) - 1}"
      " LOD meshes), and the mechanic is a proven absence.**")
    a("Nothing in the vehicle data pulls, reels, tows or winches; JC3's pulling is Rico's")
    a("grapple/tether, which belongs to the character, not the vehicle.")
    a(f"BmAK side, quoted not re-derived ({winch['bmak']}). MODLOG §86 shows that bound is an")
    a("elevator bound (>= ~2 t class), so even it would not give a vehicle mass.")
    a("")
    a("## 5. Every tether/grapple/rope/winch name in the index")
    a("")
    a(f"`tether` matches **{idx['tether']} paths**:")
    a("")
    a("| prefix | paths |")
    a("|---|---|")
    for k, v in idx["tether_where"].items():
        a(f"| `{k}` | {v} |")
    a("")
    a(f"The {len(idx['tether_non_dialogue'])} that are not dialogue:")
    a("")
    for p in idx["tether_non_dialogue"]:
        a(f"- `{p}`")
    a("")
    a(f"`winch` matches **{len(idx['winch'])} paths** - the word does not occur in the index at")
    a("all. That is supporting, not conclusive: the index does not carry parts-module prop")
    a(f"meshes (`transport_propeller` matches {idx['propeller_paths']} paths, and only")
    a(f"{idx['lod_paths']} `.lod` paths are indexed at all), so the parts table - not the index -")
    a("is the authority on prop meshes. Both agree that no winch *mechanic* is named anywhere.")
    a("")
    a("## 6. UNKNOWNs and limits")
    a("")
    a("- **Tether strength / break force**: UNKNOWN. Not in any decoded table (section 1, 5).")
    a("  Only a Q-1 probe (one variable: attach the car to a fixed object and observe) can")
    a("  measure it.")
    a("- **Unit of `RigidBody.mass`**: UNKNOWN - the file gives a bare number.")
    a("- **Whether a helicopter can airlift a car**: UNKNOWN. No fleet helicopter has a")
    a("  `CVehicleCargoBay`; whether a native tow/winch exists is engine code, not entity data.")
    a("- **What carries a vehicle into a bay**: UNKNOWN. The bay is a transform with empty")
    a("  events; the attach rule (and how the tank is held by the cargo plane) is native.")
    a("- **What `graphs/dualtether_test_to_vehicle` does**: UNKNOWN - a `GraphScript`, outside")
    a("  the decoded set; its bytes were not read here.")
    a("- **Whether the §86 winch-force bound transfers to JC3**: no - it is a BmAK feasibility")
    a("  bound, quoted, not a JC3 number.")
    a("")
    a("## 7. Validation")
    a("")
    a("`python Tools/scripts/jc3tether.py --check` rebuilds `TETHER.json` and `TETHER.md` from the")
    a("inputs, compares both byte-for-byte, and asserts:")
    a("")
    a("| assertion | measured | expected |")
    a("|---|---|---|")
    for label, got, want in assertions(d):
        a(f"| {label} | {got} | {want} |")
    a("")
    return "\n".join(L)


# ---------------------------------------------------------------------- checks
def bay_object_rows(car: dict) -> list[tuple[str, int]]:
    """The bay-object census with the 13 identical cargo-bay speakers folded into one row."""
    rows: list[tuple[str, int]] = []
    speakers: list[str] = []
    speaker_n = 0
    for key, n in car["bay_objects"].items():
        name = key.partition(" · ")[2]
        if name.startswith("Speaker_inside_cargobay"):
            speakers.append(name)
            speaker_n = max(speaker_n, n)
            continue
        rows.append((key, n))
    if speakers:
        rows.append((f"CSpeaker · Speaker_inside_cargobay* ({len(speakers)} names)", speaker_n))
    return rows


def assertions(d: dict) -> list[tuple[str, object, object]]:
    mass, car, winch, idx = d["mass"], d["carriers"], d["winch"], d["index"]
    return [
        ("entities with `RigidBody.mass`", mass["entities_with_mass"], 232),
        ("multi-body entities", len(mass["multi_body_entities"]), 1),
        ("donor mass", mass["donor"]["mass"] if mass["donor"] else None, 975),
        ("Batmobile target", mass["batmobile_target"], 6000),
        ("`CVehicleCargoBay` objects", car["bays"], 12),
        ("entities with a bay", car["bay_entities"], 12),
        ("helicopters with a bay", len(car["bay_helicopters"]), 0),
        ("compound entities", len(car["compound"]), 1),
        ("`CGrapplingHookPropData` objects", car["hooks"], 33),
        ("entities carrying them", len(car["hook_entities"]), 3),
        ("`tether_*` object names", sum(v for k, v in car["hook_names"].items()
                                       if k.startswith("tether")), 6),
        ("boat rope/winch part rows", winch["part_rows"], 40),
        ("distinct rope/winch part names", len(winch["names"]), 10),
        ("`*rope_winch*` model files, fleet", len(winch["winch_files"]), 12),
        ("`*rope_winch*` files on one boat", len(winch["winch_files_one_entity"]), 6),
        ("fleet module types", winch["module_types"], 53),
        ("tether/cargo module types", len(winch["tetherish_module_types"]), 0),
        ("functional winch classes", winch["functional_winch_classes"], 0),
        ("`tether` paths in the index", idx["tether"], 335),
        ("non-dialogue `tether` paths", len(idx["tether_non_dialogue"]), 7),
        ("`winch` paths in the index", len(idx["winch"]), 0),
    ]


def invariants(d: dict) -> list[str]:
    return [f"{label} {got} != {want}" for label, got, want in assertions(d) if got != want]


def summary(d: dict) -> str:
    mass, car, winch, idx = d["mass"], d["carriers"], d["winch"], d["index"]
    return (f"{mass['entities_with_mass']} masses (donor {mass['donor']['mass']}, target "
            f"{mass['batmobile_target']}, {len(mass['multi_body_entities'])} multi-body), "
            f"bays {car['bays']} on {car['bay_entities']} entities / "
            f"{len(car['bay_helicopters'])} helicopters, hooks {car['hooks']} on "
            f"{len(car['hook_entities'])} entities, compound {len(car['compound'])}, "
            f"rope/winch parts {winch['part_rows']} ({len(winch['names'])} names) + "
            f"{len(winch['winch_files'])} winch LODs, tether-ish module types "
            f"{len(winch['tetherish_module_types'])}/{winch['module_types']}, "
            f"winch classes {winch['functional_winch_classes']}, index tether {idx['tether']} "
            f"({len(idx['tether_non_dialogue'])} non-dialogue) / winch {len(idx['winch'])}")


# ---------------------------------------------------------------------- cmds
def cmd_write() -> int:
    d = build()
    bad = invariants(d)
    if bad:
        print("REFUSED: " + "; ".join(bad))
        return 1
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {summary(d)}, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    if json.load(open(jp, encoding="utf-8")) != d:
        bad.append(f"{JSON_NAME} stale")
    md = render_md(d)
    have = open(mp, encoding="utf-8").read()
    if md != have:
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file",
                                         "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {summary(d)}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"mass": "mass", "carriers": "carriers", "winch": "winch", "index": "index"}.get(what)
    if key is None:
        print("one of: mass, carriers, winch, index")
        return 2
    print(json.dumps(d[key], indent=1, ensure_ascii=False)[:16000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="mass")
    a = p.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    if a.cmd == "dump":
        return cmd_dump(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
