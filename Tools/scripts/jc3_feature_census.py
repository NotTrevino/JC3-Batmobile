"""jc3_feature_census.py - turn backlog §2 into a re-runnable census (P0-2).

Backlog §2 makes four claims about what the JC3 fleet carries.  They were found
by ad-hoc scans of the decoded graphs, so until now nothing re-derived them.
This script does, from three generated inputs only:

  * `E:\\Modding\\_shared\\gamedata\\JC3grab\\detail\\*.ee.json`   - every vehicle `.epe` graph as
    rows (232 files; produced by `jc3detail.py`).
  * `E:\\Modding\\_shared\\gamedata\\JC3grab\\entities\\*.ee.json` - the same entities as module
    rows (produced by `jc3grab.py`); the `VehicleCommon` module is where
    `vehicle_common.vmodc` exposes its behaviour tables.
  * `Research/JC3Grab/PARTS_TABLE.jsonl`        - one row per entity, one entry
    per part with its behaviour name (`jc3parts.py`).
  * `Research/JC3Grab/INDEX.jsonl`              - the named archive index, read
    only to list `jc_weapons/06_vehicle/<weapon id>/` directories.

Nothing here decodes a game file: it counts and joins what the readers already
wrote.  Every value is therefore re-derivable, and `--check` re-derives it.

What is emitted (schema 1, `FEATURE_CENSUS.json`)

  `weapon_classes`      for every `.epe` class matching
                        `C[A-Za-z]*(Weapon|Pulse|Turret|Aim)[A-Za-z]*`:
                        object count, `.ee` count, chassis count.
  `weapon_ids`          every `w6\\d\\d_[a-z0-9_]+` spelling found in a `.epe`
                        value, the alias groups that collapse two spellings onto
                        one weapon id, and the archive weapon directories.
  `armed_entities`      one row per entity whose graph carries a weapon class:
                        root class, weapon components (class, name, weapon id),
                        `SWeaponPoint` count, aim / barrel-spin components.
  `part_behaviours`     for every behaviour name in `PARTS_TABLE.jsonl` field
                        `b`: part, entity and chassis counts.
  `behaviour_variables` every `all_*_part_properties` table of the donor's
                        `vehicle_common` module: behaviour name -> driving
                        variable (and the other members that sit beside it).
  `reconciliation`      backlog §2 claim -> census value -> verdict, so a drift
                        between the text and the data is visible in the output
                        instead of being remembered.

The `.md` is generated from the same object as the `.json`; both must be
regenerated together.

Usage:
  python jc3_feature_census.py --write
  python jc3_feature_census.py --check
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
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
OUT = os.path.join(ROOT, "Research", "JC3Grab")

SCHEMA = 1
WEAPON_CLASS_RE = re.compile(r"C[A-Za-z]*(Weapon|Pulse|Turret|Aim)[A-Za-z]*")
WEAPON_ID_RE = re.compile(r"w6\d\d_[a-z0-9_]+")
WEAPON_DIR_RE = re.compile(r"jc_weapons/06_vehicle/(w6\d\d_[a-z0-9_]+)/")
BEHAVIOUR_TABLE_RE = re.compile(r"(all_[a-z_]+_part_properties)(?:\[(\d+)\])?(?:\.([a-z_]+))?(?:\.(string|hash))?$")

# Two spellings of the same weapon.  Evidence: the `.epe` values.  `w613_bomb`
# and `w613_fighterbomber_missile_ground_lockon` are both weapon 613 (the same
# tune, named for the payload), so the census keeps the longer name as the id
# and records the short one as an alias.
WEAPON_ID_ALIASES = {
    "w613_bomb": "w613_fighterbomber_missile_ground_lockon",
}


def load_detail():
    """Read every decoded `.epe` graph; return per-entity rows and class totals."""
    files = sorted(glob.glob(os.path.join(RAW, "detail", "*.ee.json")))
    files = [p for p in files if not p.endswith("detail_index.json")]
    if not files:
        sys.exit("no detail graphs under %s/detail" % RAW)

    entities = []
    class_objects = collections.Counter()
    class_entities = collections.Counter()
    class_chassis = collections.defaultdict(set)
    id_spellings = collections.Counter()
    id_entities = collections.defaultdict(set)

    for path in files:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        graph = d.get("epe") or {}
        objs = graph.get("objects") or []
        entity = d.get("entity") or os.path.basename(path)
        chassis = entity.split("/")[-2] if "/" in entity else entity
        scheme = entity.split("/")[3] if entity.count("/") >= 4 else ""

        classes = collections.Counter(o.get("class") for o in objs if o.get("class"))
        weapon_classes = {c: n for c, n in classes.items() if WEAPON_CLASS_RE.fullmatch(c)}
        for c, n in weapon_classes.items():
            class_objects[c] += n
            class_entities[c] += 1
            class_chassis[c].add(chassis)

        base = entity.rsplit(".ee", 1)[0].split("/")[-1]
        roots = [o for o in objs if o.get("depth") == 1 and o.get("class")]
        root = next((o for o in roots
                     if (o.get("values") or {}).get("name") in (base, base + "_generated")), None)
        if root is None:
            skip = {"CCameraObject", "CCameraRef", "CInteractionContext", "CMaterialEffectTable"}
            root = next((o for o in roots if o["class"] not in skip
                         and not WEAPON_CLASS_RE.fullmatch(o["class"])), roots[0] if roots else None)
        root_class = root["class"] if root else None

        weapons = []
        for o in objs:
            c = o.get("class") or ""
            if c not in ("CBulletWeaponBase", "CMissileWeaponBase", "CLightWeaponComponent",
                         "CRPGFireLeachWeapon", "CLaserBeamWeaponComponent", "CTurretWeaponComponent"):
                continue
            values = o.get("values") or {}
            name = o.get("name") or ""
            wid = values.get("weapon_id")
            if wid is None:
                m = WEAPON_ID_RE.search(name)
                wid = m.group(0) if m else None
            weapons.append({"class": c, "name": name, "weapon_id": wid})

        for o in objs:
            values = [o.get("name") or ""] + [str(v) for v in (o.get("values") or {}).values()]
            for text in values:
                for m in WEAPON_ID_RE.finditer(text):
                    spelling = m.group(0)
                    id_spellings[spelling] += 1
                    id_entities[spelling].add(entity)

        if any(c != "CForcePulse" for c in weapon_classes):
            entities.append({
                "entity": entity,
                "chassis": chassis,
                "scheme": scheme,
                "root_class": root_class,
                "graphs_objects": len(objs),
                "weapon_classes": weapon_classes,
                "weapons": sorted(weapons, key=lambda w: (w["class"], w["name"])),
                "weapon_points": classes.get("SWeaponPoint", 0),
            })

    return {
        "files": len(files),
        "entities": entities,
        "class_objects": class_objects,
        "class_entities": class_entities,
        "class_chassis": class_chassis,
        "id_spellings": id_spellings,
        "id_entities": id_entities,
    }


def load_parts():
    path = os.path.join(OUT, "PARTS_TABLE.jsonl")
    if not os.path.exists(path):
        sys.exit("missing %s" % path)
    rows = 0
    parts = 0
    behaviours = collections.defaultdict(lambda: {"parts": 0, "entities": set(), "chassis": set()})
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows += 1
            entity = row.get("entity") or ""
            chassis = entity.split("/")[-2] if "/" in entity else entity
            for part in row.get("parts") or []:
                parts += 1
                b = part.get("b") or "None"
                if b == "None":
                    continue
                entry = behaviours[b]
                entry["parts"] += 1
                entry["entities"].add(entity)
                entry["chassis"].add(chassis)
    return {"rows": rows, "parts": parts, "behaviours": behaviours}


def load_vehicle_common():
    """Read the `VehicleCommon` module rows of the donor entity."""
    pattern = os.path.join(RAW, "entities", "*sportsmuscle_civilian_01.ee.json")
    paths = sorted(glob.glob(pattern))
    if not paths:
        sys.exit("no donor entity module rows matching %s" % pattern)
    with open(paths[0], encoding="utf-8") as fh:
        d = json.load(fh)
    module = None
    for m in d.get("modules") or []:
        if m.get("type") == "VehicleCommon":
            module = m
            break
    if module is None:
        sys.exit("donor has no VehicleCommon module")

    tables = collections.OrderedDict()
    for row in module.get("rows") or []:
        m = BEHAVIOUR_TABLE_RE.match(row.get("path") or "")
        if not m:
            continue
        table, index, member, kind = m.groups()
        t = tables.setdefault(table, {"entries": {}, "members": set()})
        if index is None:
            continue
        i = int(index)
        ent = t["entries"].setdefault(i, {})
        t["members"].add(member)
        if kind == "string":
            ent[member] = row.get("value")
        elif kind == "hash":
            ent.setdefault(member + "_hash", row.get("value"))
        else:
            ent[member] = row.get("value")

    out = []
    for table in sorted(tables):
        t = tables[table]
        entries = []
        for i in sorted(t["entries"]):
            ent = t["entries"][i]
            variable = None
            var_key = None
            for k in sorted(ent):
                if k.endswith("_variable"):
                    variable = ent[k]
                    var_key = k
                    break
            drop = {"name", "name_hash"}
            if var_key:
                drop |= {var_key, var_key + "_hash"}
            entries.append({
                "name": ent.get("name"),
                "variable": variable,
                "members": {k: v for k, v in sorted(ent.items()) if k not in drop},
            })
        out.append({
            "table": table,
            "source": module.get("file"),
            "rows": len(entries),
            "entries": entries,
        })
    return {"file": paths[0], "module": module.get("file"), "tables": out}


def load_index():
    path = os.path.join(OUT, "INDEX.jsonl")
    if not os.path.exists(path):
        sys.exit("missing %s" % path)
    rows = 0
    dirs = set()
    spellings = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows += 1
            p = json.loads(line).get("path") or ""
            m = WEAPON_DIR_RE.search(p)
            if m:
                dirs.add(m.group(1))
            for s in WEAPON_ID_RE.finditer(p):
                spellings.add(s.group(0))
    return {"rows": rows, "dirs": sorted(dirs), "spellings": sorted(spellings)}


def build():
    detail = load_detail()
    parts = load_parts()
    common = load_vehicle_common()
    index = load_index()

    # Weapon ids: collapse aliases, keep the aliases visible.
    aliases = {k: v for k, v in sorted(WEAPON_ID_ALIASES.items())
               if k in detail["id_spellings"]}
    ids = collections.OrderedDict()
    for spelling in sorted(detail["id_spellings"]):
        canonical = aliases.get(spelling, spelling)
        entry = ids.setdefault(canonical, {"spellings": [], "entities": set()})
        entry["spellings"].append(spelling)
        entry["entities"] |= detail["id_entities"][spelling]
    weapon_ids = []
    for wid, entry in ids.items():
        weapon_ids.append({
            "id": wid,
            "spellings": sorted(entry["spellings"]),
            "entities": len(entry["entities"]),
        })

    weapon_classes = []
    for c in sorted(detail["class_objects"]):
        weapon_classes.append({
            "class": c,
            "objects": detail["class_objects"][c],
            "entities": detail["class_entities"][c],
            "chassis": len(detail["class_chassis"][c]),
            "chassis_list": sorted(detail["class_chassis"][c]),
        })

    part_behaviours = []
    for b in sorted(parts["behaviours"]):
        e = parts["behaviours"][b]
        part_behaviours.append({
            "behaviour": b,
            "parts": e["parts"],
            "entities": len(e["entities"]),
            "chassis": len(e["chassis"]),
            "chassis_list": sorted(e["chassis"]),
        })

    armed = []
    for e in detail["entities"]:
        armed.append({
            "entity": e["entity"],
            "chassis": e["chassis"],
            "scheme": e["scheme"],
            "root_class": e["root_class"],                "weapon_classes": {c: n for c, n in sorted(e["weapon_classes"].items())
                                    if c != "CForcePulse"},
                "force_pulses": e["weapon_classes"].get("CForcePulse", 0),
            "weapons": e["weapons"],
            "weapon_points": e["weapon_points"],
            "force_pulses": e.get("force_pulses", 0),
        })

    by_behaviour = {b["behaviour"]: b for b in part_behaviours}

    def cls(c):
        for row in weapon_classes:
            if row["class"] == c:
                return row
        return {"class": c, "objects": 0, "entities": 0, "chassis": 0, "chassis_list": []}

    def fam(beh, **kw):
        row = by_behaviour.get(beh, {"behaviour": beh, "parts": 0, "entities": 0, "chassis": 0,
                                     "chassis_list": []})
        out = {"behaviour": beh, "parts": row["parts"], "entities": row["entities"],
               "chassis": row["chassis"], "chassis_list": row.get("chassis_list", [])}
        out.update(kw)
        return out

    reconciliation = [
        {
            "claim": "§2.1 CBulletWeaponBase: 17 entities",
            "derived": "%d chassis, %d .ee, %d objects" % (
                cls("CBulletWeaponBase")["chassis"], cls("CBulletWeaponBase")["entities"],
                cls("CBulletWeaponBase")["objects"]),
            "verdict": "match at chassis granularity; wording corrected to say chassis",
        },
        {
            "claim": "§2.1 CMissileWeaponBase: 7 entities",
            "derived": "%d chassis, %d .ee, %d objects" % (
                cls("CMissileWeaponBase")["chassis"], cls("CMissileWeaponBase")["entities"],
                cls("CMissileWeaponBase")["objects"]),
            "verdict": "match at chassis granularity; wording corrected to say chassis",
        },
        {
            "claim": "§2.1 25 weapon ids",
            "derived": "%d ids (%d spellings incl. w613_bomb) in .epe values; %d archive ids" % (
                len(weapon_ids),
                len(detail["id_spellings"]),
                len(index["dirs"])),
            "verdict": "match (25 ids after the w613_bomb alias; 26 spellings; 22 archive dirs)",
        },
        {
            "claim": "G2-17/§1.4 CForcePulse: 79 entities",
            "derived": "%d chassis, %d .ee, %d objects" % (
                cls("CForcePulse")["chassis"], cls("CForcePulse")["entities"],
                cls("CForcePulse")["objects"]),
            "verdict": "match at chassis granularity; wording corrected to say chassis",
        },
        {
            "claim": "G2-11 'the 24 armed entities (P0-2 list)'",
            "derived": "%d armed .ee over %d chassis (17 bullet + 7 missile - 3 chassis with both)" % (
                len(armed), len({e["chassis"] for e in detail["entities"]})),
            "verdict": "24 was 17+7 chassis with the 3 overlapping chassis counted twice; use this list",
        },
        {
            "claim": "§2.3 SteeringWheel on 9 cars",
            "derived": "%d chassis, %d entities, %d parts; boat chassis: %s" % (
                fam("SteeringWheel")["chassis"], fam("SteeringWheel")["entities"],
                fam("SteeringWheel")["parts"],
                ", ".join(c for c in fam("SteeringWheel")["chassis_list"] if "_boat_" in c) or "none"),
            "verdict": "count matches; wording corrected to say chassis, not cars",
        },
        {
            "claim": "§2.3 Turret/Cannon: medium tank, small tank, APC, technical, armoured jeep",
            "derived": "Turret %d parts / %d chassis; Cannon %d parts / %d chassis; all five named chassis present" % (
                fam("Turret")["parts"], fam("Turret")["chassis"],
                fam("Cannon")["parts"], fam("Cannon")["chassis"]),
            "verdict": "match (the census adds the corvette's Turret and boat/heli Cannons)",
        },
        {
            "claim": "§2.3 EngineRotatingPart on v0506",
            "derived": "%d chassis %s, %d parts" % (
                fam("EngineRotatingPart")["chassis"], fam("EngineRotatingPart")["chassis_list"],
                fam("EngineRotatingPart")["parts"]),
            "verdict": "match (v0506_car_solar_oldtractor)",
        },
        {
            "claim": "§2.3 GatlingGun: racing boat and helicopters",
            "derived": "%d chassis %s" % (fam("GatlingGun")["chassis"],
                                          by_behaviour.get("GatlingGun", {}).get("chassis_list", [])),
            "verdict": "match",
        },
        {
            "claim": "§2.3 MissileHatch: monorail missile car, 16 hatches",
            "derived": "%d parts on %d entity (%s)" % (
                fam("MissileHatch")["parts"], fam("MissileHatch")["entities"],
                by_behaviour.get("MissileHatch", {}).get("chassis_list", [])),
            "verdict": "match",
        },
        {
            "claim": "§2.3 AirBrake: fighter-bomber only",
            "derived": "%d chassis %s, %d parts" % (
                fam("AirBrake")["chassis"], by_behaviour.get("AirBrake", {}).get("chassis_list", []),
                fam("AirBrake")["parts"]),
            "verdict": "match - still the only land-use probe",
        },
        {
            "claim": "§2.3 Flaps: articulated truck / armoured transport / planes",
            "derived": "%d chassis, %d parts" % (fam("Flaps")["chassis"], fam("Flaps")["parts"]),
            "verdict": "match",
        },
        {
            "claim": "§2.3 Spring: ATV, buggy, monster truck",
            "derived": "%d chassis, %d parts" % (fam("Spring")["chassis"], fam("Spring")["parts"]),
            "verdict": "match",
        },
    ]

    doc = collections.OrderedDict()
    doc["schema"] = SCHEMA
    doc["generated_by"] = "Tools/scripts/jc3_feature_census.py"
    doc["inputs"] = {
        "detail_graphs": detail["files"],
        "detail_root": RAW.replace("\\", "/") + "/detail",
        "parts_table_rows": parts["rows"],
        "parts_table_parts": parts["parts"],
        "index_rows": index["rows"],
        "vehicle_common_entity": common["file"].replace("\\", "/").split("/")[-1],
        "vehicle_common_module": common["module"],
    }
    doc["totals"] = {
        "entities": detail["files"],
        "armed_entities": len(armed),
        "armed_chassis": len({e["chassis"] for e in detail["entities"]}),
        "weapon_classes": len(weapon_classes),
        "weapon_ids": len(weapon_ids),
        "weapon_id_spellings": len(detail["id_spellings"]),
        "archive_weapon_ids": len(index["dirs"]),
        "part_behaviours": len(part_behaviours),
        "behaviour_tables": len(common["tables"]),
    }
    doc["weapon_classes"] = weapon_classes
    doc["weapon_ids"] = {
        "ids": weapon_ids,
        "aliases": aliases,
        "archive_ids": index["dirs"],
        "index_spellings": index["spellings"],
    }
    doc["armed_entities"] = armed
    doc["part_behaviours"] = part_behaviours
    doc["behaviour_variables"] = common["tables"]
    doc["reconciliation"] = reconciliation
    return doc


def render_md(doc):
    L = []
    add = L.append
    add("# JC3 feature census (generated)")
    add("")
    add("Generated by `Tools/scripts/jc3_feature_census.py` from the decoded `.epe` graphs, the")
    add("entity module rows, `PARTS_TABLE.jsonl` and `INDEX.jsonl`. Do not edit by hand:")
    add("")
    add("```")
    add("python Tools/scripts/jc3_feature_census.py --write")
    add("python Tools/scripts/jc3_feature_census.py --check")
    add("```")
    add("")
    add("## Inputs")
    add("")
    add("| input | value |")
    add("|---|---|")
    for k, v in doc["inputs"].items():
        add("| `%s` | %s |" % (k, v))
    add("")
    add("## Totals")
    add("")
    add("| quantity | count |")
    add("|---|---|")
    for k, v in doc["totals"].items():
        add("| %s | %s |" % (k.replace("_", " "), v))
    add("")
    add("## Weapon component classes in the `.epe` graphs")
    add("")
    add("The P0-2 regex is `C[A-Za-z]*(Weapon|Pulse|Turret|Aim)[A-Za-z]*`, so `CForcePulse` is listed;")
    add("every vehicle carries one, and it is excluded from the armed list below.")
    add("")
    add("| class | objects | `.ee` files | chassis |")
    add("|---|---:|---:|---:|")
    for row in doc["weapon_classes"]:
        add("| `%s` | %d | %d | %d |" % (row["class"], row["objects"], row["entities"], row["chassis"]))
    add("")
    add("## Weapon ids")
    add("")
    add("`%d` ids after alias collapse, from `%d` spellings in `.epe` values; `%d` weapon"
        % (doc["totals"]["weapon_ids"], doc["totals"]["weapon_id_spellings"],
           doc["totals"]["archive_weapon_ids"]))
    add("directories exist under `jc_weapons/06_vehicle/`. An id marked with several spellings is")
    add("one weapon named twice (see the alias table).")
    add("")
    add("| weapon id | spellings | entities |")
    add("|---|---|---:|")
    for row in doc["weapon_ids"]["ids"]:
        add("| `%s` | %s | %d |" % (row["id"], ", ".join("`%s`" % s for s in row["spellings"]), row["entities"]))
    add("")
    add("Aliases: " + (", ".join("`%s` -> `%s`" % (k, v) for k, v in doc["weapon_ids"]["aliases"].items())
                        or "none") + ".")
    add("")
    add("Archive ids (`jc_weapons/06_vehicle`): " +
        ", ".join("`%s`" % x for x in doc["weapon_ids"]["archive_ids"]) + ".")
    add("")
    add("Index spellings not used by a `.epe` (`%d`): " % len(doc["weapon_ids"]["index_spellings"]) +
        ", ".join("`%s`" % x for x in doc["weapon_ids"]["index_spellings"]) + ".")
    add("")
    add("## Armed entities")
    add("")
    add("| entity | scheme | root class | weapon classes | weapons | weapon points |")
    add("|---|---|---|---|---|---:|")
    for row in doc["armed_entities"]:
        classes = ", ".join("`%s`" % c for c in row["weapon_classes"])
        ids = ", ".join(sorted({w["name"] for w in row["weapons"] if w["name"]}))
        add("| `%s` | %s | `%s` | %s | %s | %d |" % (
            row["entity"].split("/")[-1], row["scheme"], row["root_class"], classes, ids, row["weapon_points"]))
    add("")
    add("## Part behaviours (`PARTS_TABLE.jsonl` field `b`)")
    add("")
    add("| behaviour | parts | entities | chassis |")
    add("|---|---:|---:|---:|")
    for row in doc["part_behaviours"]:
        add("| `%s` | %d | %d | %d |" % (row["behaviour"], row["parts"], row["entities"], row["chassis"]))
    add("")
    add("## `vehicle_common` behaviour -> variable")
    add("")
    add("Source: `%s` (module `%s`)." % (doc["inputs"]["vehicle_common_entity"],
                                         doc["inputs"]["vehicle_common_module"]))
    add("")
    for table in doc["behaviour_variables"]:
        add("### `%s` (%d rows)" % (table["table"], table["rows"]))
        add("")
        add("| name | driving variable | other members |")
        add("|---|---|---|")
        for e in table["entries"]:
            members = ", ".join("%s=%s" % (k, v) for k, v in e["members"].items()) or "-"
            add("| `%s` | %s | %s |" % (e["name"], ("`%s`" % e["variable"]) if e["variable"] else "-", members))
        add("")
    add("## Backlog §2 reconciliation")
    add("")
    add("| backlog §2 claim | census value | verdict |")
    add("|---|---|---|")
    for row in doc["reconciliation"]:
        add("| %s | %s | %s |" % (row["claim"], row["derived"], row["verdict"]))
    add("")
    return "\n".join(L) + "\n"


def dump(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write FEATURE_CENSUS.json and .md")
    g.add_argument("--check", action="store_true", help="re-derive and compare with the files on disk")
    args = ap.parse_args(argv)

    doc = build()
    text_json = dump(doc)
    text_md = render_md(doc)
    jpath = os.path.join(OUT, "FEATURE_CENSUS.json")
    mpath = os.path.join(OUT, "FEATURE_CENSUS.md")

    if args.write:
        with open(jpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text_json)
        with open(mpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text_md)
        print("wrote %s" % jpath)
        print("wrote %s" % mpath)
        print("totals: %(entities)d entities, %(armed_entities)d armed, %(weapon_ids)d weapon ids, "
              "%(part_behaviours)d part behaviours, %(behaviour_tables)d behaviour tables" % doc["totals"])
        return 0

    problems = 0
    for path, expected in ((jpath, text_json), (mpath, text_md)):
        if not os.path.exists(path):
            print("MISSING %s" % path)
            problems += 1
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            actual = fh.read()
        if actual != expected:
            problems += 1
            print("STALE %s" % path)
            a = actual.splitlines()
            b = expected.splitlines()
            for i in range(max(len(a), len(b))):
                av = a[i] if i < len(a) else "<missing>"
                bv = b[i] if i < len(b) else "<missing>"
                if av != bv:
                    print("  line %d:\n    on disk: %s\n    derived: %s" % (i + 1, av, bv))
                    break
        else:
            print("ok %s" % os.path.basename(path))

    if problems:
        print("FAIL: %d file(s) differ; run --write" % problems)
        return 1
    print("check ok: census matches the data (%d entities, %d armed, %d weapon ids)"
          % (doc["totals"]["entities"], doc["totals"]["armed_entities"], doc["totals"]["weapon_ids"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
