#!/usr/bin/env python
"""jc3moving.py - G2-14: who drives each moving-part behaviour in JC3.

Every vehicle part carries a `behavior` string (`Turret`, `Hood`, `MainRotor`, `Wheel`...).
This script answers, for each one:

  * which channel moves it: a `vehicle_common` behaviour table (`all_hinged_part_properties`
    names a `target_position_variable`; `all_rotating_part_properties` names an `rpm_variable`),
    a name-only table (doors, fins, springs), or no table at all;
  * which vehicles use it - parts, entities, chassis, from `FEATURE_CENSUS.json`;
  * the chassis' root class (`CCar`, `CBoat`, `CHelicopter`, `CMotorBike`, `CAirPlane`), so the
    row can say proven-on-CCar or unproven-on-CCar;
  * which per-part arrays in the parts modules carry it (`door_parts[]`, `hinged_parts[]`,
    `rotating_parts[]`) and what those arrays actually store.

Sources: the `vehicle_common.vmodc` module inside the Serpente civilian `.ee` (the only copy in
the fleet), `FEATURE_CENSUS.json`, the decoded detail JSONs for the root classes, and the parts
modules in the local cache for the arrays.

Usage:
  python jc3moving.py --write    # MOVING_PARTS.md + MOVING_PARTS.json
  python jc3moving.py --check    # rebuild and compare, plus invariants
  python jc3moving.py dump tables|behaviours|arrays
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
CENSUS = os.path.join(OUT, "FEATURE_CENSUS.json")
JSON_NAME = "MOVING_PARTS.json"
MD_NAME = "MOVING_PARTS.md"
COMMON = "vehicle_common.vmodc"
CONTAINER = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
             "v0300_car_kensington_sportsmuscle_civilian_01.ee")
TABLES = ("all_fin_part_properties", "all_spring_part_properties",
          "all_door_part_properties", "all_hinged_part_properties",
          "all_rotating_part_properties")
ARRAYS = ("door_parts", "hinged_parts", "rotating_parts")
ROOT_CLASSES = ("CCar", "CBoat", "CHelicopter", "CMotorBike", "CAirPlane", "CTrain")
DONOR_MODULE = "sportsmuscle_vehicle_parts.vmodc"
APC_MODULE = "apc_vehicle_parts.vmodc"
# G2-13's six turreted samples: `TURRET.md` §3 names the vehicles and `TURRET.json` carries the
# same entity -> parts_module pairs. Identifiers only; every row count is read from the cache.
G2_13_TURRETED = (
    ("apc_vehicle_parts.vmodc", "v0200 APC"),
    ("mediumtank_vehicle_parts.vmodc", "v0201 medium tank"),
    ("bavariumtank_vehicle_parts.vmodc", "v0202 Bavarium tank"),
    ("technicaljeep_vehicle_parts.vmodc", "v0504 technical"),
    ("armoredjeep_vehicle_parts.vmodc", "v0600 armoured jeep"),
    ("smalltank_vehicle_parts.vmodc", "v0603 small tank"),
)
# Grouping of the no-row behaviours. This is *this record's reading*: none of them has a row in
# `vehicle_common`, so the grouping cannot be a decoded field. The residual is computed.
NO_ROW_GROUPS = (
    ("a Havok constraint or physics body (G2-13/G2-8)", ("Turret", "Cannon", "Axle")),
    ("the deform and wheel system", ("Wheel", "Body", "BrakeDrum", "BrakeDisc", "Engine")),
    ("windows and couplings", ("Windshield", "FrontLeftWindow", "FrontRightWindow",
                              "RearLeftWindow", "RearRightWindow", "RearWindow",
                              "CenterLeftWindow", "CenterRightWindow", "FrontWagonCoupling",
                              "FrontWagonCouplingLinked", "RearWagonCoupling")),
)


def common_module() -> bytes:
    """The one `vehicle_common.vmodc` copy: an inner file of the Serpente civilian `.ee`."""
    cached = os.path.join(RAW, "tmp", COMMON)
    if os.path.exists(cached):
        return open(cached, "rb").read()
    rows = jc3index.load_index(OUT)
    r = jc3detail.pick(rows, CONTAINER)
    stream, entries = jc3detail.inner_files(jc3grab.read_entry(r, GAME))
    hit = next((e for e in entries if e[0].endswith(COMMON)), None)
    if hit is None:
        raise SystemExit(f"no {COMMON} inside {CONTAINER}")
    blob = stream[hit[1]:hit[1] + hit[2]]
    os.makedirs(os.path.dirname(cached), exist_ok=True)
    open(cached, "wb").write(blob)
    return blob


def decode_tables() -> list[dict]:
    rows = {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(common_module()))}
    out = []
    for table in TABLES:
        n = 0
        while f"{table}[{n}].name.string" in rows:
            n += 1
        recs = []
        for i in range(n):
            members: dict[str, object] = {}
            name_hash = None
            for k, v in rows.items():
                if not k.startswith(f"{table}[{i}]."):
                    continue
                key = k.split("]", 1)[1].lstrip(".")
                if key.endswith(".hash"):
                    if key == "name.hash":
                        name_hash = v
                    continue
                if key.endswith(".string"):
                    key = key[:-7]
                members[key] = v
            recs.append({"name": members.pop("name"),
                         "name_hash": name_hash,
                         "members": members})
        out.append({"table": table, "rows": recs,
                    "member_names": sorted({m for r in recs for m in r["members"]})})
    return out


def root_classes() -> dict[str, str]:
    """entity -> root class, from the decoded `.epe` class histogram (exactly one root per file)."""
    out = {}
    for path in glob.glob(os.path.join(RAW, "detail", "*.json")):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        classes = d.get("epe", {}).get("classes", {})
        found = [c for c in ROOT_CLASSES if classes.get(c) == 1]
        if len(found) == 1:
            out[d["entity"]] = found[0]
    return out


def fleet_records() -> int | None:
    """Vehicle records in `PARTS_TABLE.jsonl` - the fleet count the other G2 docs quote."""
    path = os.path.join(OUT, "PARTS_TABLE.jsonl")
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return None


def turreted(mods: list[dict]) -> list[dict]:
    """The six G2-13 turreted samples with the array rows the cache holds for each."""
    by_name = {m["module"]: m for m in mods}
    return [{"module": module, "label": label,
             "rows": (by_name[module]["rows"] if module in by_name else None)}
            for module, label in G2_13_TURRETED]


def arrays() -> list[dict]:
    """Per-module `door_parts` / `hinged_parts` / `rotating_parts` rows and their member names."""
    mods = []
    for path in sorted(glob.glob(os.path.join(RAW, "tmp", "*_vehicle_parts.vmodc"))):
        rows = {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(open(path, "rb").read()))}
        rec = {"module": os.path.basename(path), "rows": {}, "members": {}}
        for arr in ARRAYS:
            n = 0
            members: set[str] = set()
            while f"{arr}[{n}].part_index" in rows:
                members |= {k.split("]", 1)[1].lstrip(".") for k in rows
                            if k.startswith(f"{arr}[{n}].")}
                n += 1
            rec["rows"][arr] = n
            rec["members"][arr] = sorted(members)
        mods.append(rec)
    return mods


def build() -> dict:
    tables = decode_tables()
    census = json.load(open(CENSUS, encoding="utf-8"))
    classes = root_classes()
    behaviour_entity = {b["behaviour"]: b for b in census["part_behaviours"]}
    used = {}
    for b in census["part_behaviours"]:
        for ch in b["chassis_list"]:
            used.setdefault(ch, set()).add(b["behaviour"])
    chassis_class = {}
    for ent, cls in classes.items():
        parts = ent.split("/")
        if "jc_vehicles" in parts:
            idx = parts.index("jc_vehicles")
            if idx + 2 < len(parts):
                chassis_class.setdefault(parts[idx + 2], set()).add(cls)

    by_table = {}
    for t in tables:
        for r in t["rows"]:
            by_table[r["name"]] = t["table"]

    behaviours = []
    for name, b in behaviour_entity.items():
        table = by_table.get(name)
        channel, variable = "none", None
        if table == "all_hinged_part_properties":
            channel = "hinged"
        elif table == "all_rotating_part_properties":
            channel = "rotating"
        elif table == "all_door_part_properties":
            channel = "door"
        elif table == "all_fin_part_properties":
            channel = "fin"
        elif table == "all_spring_part_properties":
            channel = "spring"
        if table:
            row = next(r for t in tables if t["table"] == table for r in t["rows"]
                       if r["name"] == name)
            variable = (row["members"].get("target_position_variable")
                        or row["members"].get("rpm_variable"))
        ch_classes = sorted({c for ch in b["chassis_list"] for c in chassis_class.get(ch, [])})
        behaviours.append({
            "behaviour": name, "parts": b["parts"], "entities": b["entities"],
            "chassis": b["chassis"], "chassis_list": b["chassis_list"],
            "table": table, "channel": channel, "variable": variable,
            "classes": ch_classes,
            "proof": "proven-on-CCar" if "CCar" in ch_classes else "unproven-on-CCar",
        })
    behaviours.sort(key=lambda r: (-r["parts"], r["behaviour"]))

    table_names = {r["name"] for t in tables for r in t["rows"]}
    mods = arrays()
    out = {
        "source": {"module": COMMON, "container": CONTAINER,
                   "rows": sum(len(t["rows"]) for t in tables),
                   "declared_not_used": sorted(table_names - set(behaviour_entity))},
        "census": {"entities": census["totals"]["entities"],
                   "part_behaviours": census["totals"]["part_behaviours"],
                   "fleet_records": fleet_records(),
                   "classified": len(classes)},
        "tables": tables,
        "behaviours": behaviours,
        "arrays": {"modules": mods, "turreted": turreted(mods)},
    }
    out["arrays"]["counts"] = {
        arr: {"modules": sum(1 for m in out["arrays"]["modules"] if m["rows"][arr]),
              "rows": sum(m["rows"][arr] for m in out["arrays"]["modules"])}
        for arr in ARRAYS}
    out["digest"] = hashlib.sha1(json.dumps(out, sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()[:16]
    return out


# ---------------------------------------------------------------------- md
def render_md(d: dict) -> str:
    beh = d["behaviours"]
    tables = {t["table"]: t for t in d["tables"]}
    used_names = {b["behaviour"] for b in beh}
    counts = d["arrays"]["counts"]
    no_table = [b for b in beh if not b["table"]]
    unproven = [b for b in beh if b["proof"] == "unproven-on-CCar"]
    modules = d["arrays"]["modules"]
    by_module = {m["module"]: m for m in modules}
    census = d["census"]
    fleet = census["fleet_records"] if census["fleet_records"] is not None else "unknown"
    table_rows = {t["table"]: len(t["rows"]) for t in d["tables"]}
    unused = d["source"]["declared_not_used"]
    legs = [n for n in unused if n.endswith(("Coxa", "Femur", "Tibia"))]
    elevons = [n for n in unused if n.endswith("Elevon")]
    rest_unused = [n for n in unused if n not in legs and n not in elevons]
    donor_doors = by_module.get(DONOR_MODULE, {}).get("rows", {}).get("door_parts")
    apc_doors = by_module.get(APC_MODULE, {}).get("rows", {}).get("door_parts")
    chassis = {c for b in beh for c in b["chassis_list"]}
    empty_class = sum(1 for b in beh if not b["classes"])

    grouped: set[str] = set()
    group_rows: list[tuple[str, list[str]]] = []
    for label, names in NO_ROW_GROUPS:
        present = [n for n in names if any(b["behaviour"] == n for b in no_table)]
        grouped |= set(present)
        if present:
            group_rows.append((label, present))
    residual = [b["behaviour"] for b in no_table if b["behaviour"] not in grouped]

    ab = next((b for b in beh if b["behaviour"] == "AirBrake"), None)
    if ab:
        ab_note = (f"`AirBrake` is the only behaviour the card names as a Q-1 probe: "
                   f"{ab['parts']} parts on {ab['chassis']} chassis "
                   f"({', '.join(ab['chassis_list'])}; {'/'.join(ab['classes']) or '-'}) and "
                   "nothing on land.")
    else:
        ab_note = "`AirBrake` is absent from the census - the card's Q-1 probe has no sample."

    tur = d["arrays"]["turreted"]
    tur_rows = [f"{t['label']} {t['rows']['door_parts']}" if t["rows"]
                else f"{t['label']} (module not in the cache)" for t in tur]
    tur_hinged = max((t["rows"]["hinged_parts"] for t in tur if t["rows"]), default=0)
    tur_rotating = max((t["rows"]["rotating_parts"] for t in tur if t["rows"]), default=0)
    turret_note = ("The six G2-13 turreted samples (`TURRET.md` \u00a73) fill `door_parts[]` - "
                   + ", ".join(tur_rows)
                   + f" - and none fills `hinged_parts[]` or `rotating_parts[]` "
                     f"(max {tur_hinged} / {tur_rotating}); their aim is the `.physicsc` hinge "
                     "(G2-13), not these arrays.")

    roto: dict[object, list[str]] = {}
    rot_rows = next(t for t in d["tables"]
                    if t["table"] == "all_rotating_part_properties")["rows"]
    for r in rot_rows:
        roto.setdefault(r["members"].get("rotoscope_rpm_per_cycle"), []).append(r["name"])
    roto_note = "; ".join(f"{v} on {len(names)} ({', '.join(names)})"
                          for v, names in sorted(roto.items(), key=lambda kv: str(kv[0])))
    lines = [
        "# Moving parts - who drives each behaviour",
        "",
        "G2-14. Every part carries one `behavior` string. That string is the key into the shared",
        "`vehicle_common.vmodc` module, which holds five behaviour tables: `all_hinged_`,",
        "`all_rotating_`, `all_door_`, `all_fin_` and `all_spring_part_properties`. Only the first",
        f"two name a driving variable; the other three are name-only, and {len(no_table)} "
        "behaviours used by shipped vehicles have no row at all.",
        "",
        "## 1. The five tables",
        "",
        "| table | rows | used by a part | members |",
        "|---|---|---|---|",
    ]
    for t in d["tables"]:
        used = sum(1 for r in t["rows"] if r["name"] in used_names)
        lines.append(f"| `{t['table']}` | {len(t['rows'])} | {used} | "
                     f"{', '.join('`' + m + '`' for m in t['member_names']) or '`name` only'} |")
    lines += ["",
              "Source: `" + d["source"]["module"] + "`, the only copy in the fleet, carried as an",
              "inner file of the Serpente civilian `.ee`.",
              "",
              "### Hinged parts - a variable, a LOD flag and an angle flag",
              "",
              "| behaviour | `target_position_variable` | `lod` | `use_target_position_as_angle` |",
              "|---|---|---|---|",
              ]
    for r in tables["all_hinged_part_properties"]["rows"]:
        m = r["members"]
        lines.append(f"| `{r['name']}` | `{m.get('target_position_variable', '-')}` | "
                     f"{m.get('lod', '-')} | {m.get('use_target_position_as_angle', '-')} |")
    angle = [r["name"] for r in tables["all_hinged_part_properties"]["rows"]
             if r["members"].get("use_target_position_as_angle") == 1]
    if len(angle) == 1:
        angle_note = (f"`{angle[0]}` is the only row that sets `use_target_position_as_angle`; "
                      "every other row takes the variable as a 0..1 position.")
    else:
        angle_note = (f"{len(angle)} rows set `use_target_position_as_angle` ("
                      + ", ".join(angle) + "); the rest take the variable as a 0..1 position.")
    lines += ["",
              "The variable is a float in the vehicle's own state: the animation system writes it,",
              "the behaviour reads it. " + angle_note,
              "",
              "### Rotating parts - an rpm variable and rotoscope flags",
              "",
              "| behaviour | `rpm_variable` | rotoscope | inverted | special collision | "
              "water sensors | rpm/cycle |",
              "|---|---|---|---|---|---|---|",
              ]
    for r in tables["all_rotating_part_properties"]["rows"]:
        m = r["members"]
        lines.append(f"| `{r['name']}` | `{m.get('rpm_variable', '-')}` | "
                     f"{m.get('rotoscope_enabled', '-')} | {m.get('inverted', '-')} | "
                     f"{m.get('special_collision_enabled', '-')} | "
                     f"{m.get('number_of_water_collision_sensors', '-')} | "
                     f"{m.get('rotoscope_rpm_per_cycle', '-')} |")
    lines += ["",
              "`rpm_variable` names the vehicle's rpm state. `rotoscope_rpm_per_cycle` holds "
              + roto_note
              + ". What the field drives is not defined in any file read here: the name suggests "
                "a per-cycle strobe rate, which is this record's inference, not a decoded "
                "definition - the value itself is decoded, the meaning is UNKNOWN.",
              "",
              "### Doors, fins and springs - name only",
              "",
              "| table | names |",
              "|---|---|"]
    for key in ("all_door_part_properties", "all_fin_part_properties",
                "all_spring_part_properties"):
        names = ", ".join(f"`{r['name']}`" for r in tables[key]["rows"])
        lines.append(f"| `{key}` | {names} |")
    lines += ["",
              "These rows carry nothing but the name and its hash. A door's angle is the part's",
              "Havok hinge (G2-13: `mediumtank_hatch` is a `FrontLeftDoor` on a 0..130 deg",
              "limited hinge), and the parts module's `door_parts[]` only lists the part index -",
              "so the door's travel is in `.physicsc`, not in `vehicle_common`.",
              "",
              "## 2. Behaviour -> vehicles -> proof",
              "",
              f"`parts`/`entities`/`chassis` come from `FEATURE_CENSUS.json` ({census['entities']} "
              f"entities, of the {fleet} records in `PARTS_TABLE.jsonl`);",
              "the root class comes from each entity's `.epe` class histogram. `proven-on-CCar`",
              "means at least one `CCar` chassis ships a part with that behaviour.",
              "",
              "| behaviour | channel / variable | parts | entities | chassis | classes | proof |",
              "|---|---|---|---|---|---|---|"]
    for b in beh:
        if b["channel"] == "hinged":
            ch = f"hinged, `{b['variable']}`"
        elif b["channel"] == "rotating":
            ch = f"rotating, `{b['variable']}`"
        elif b["table"]:
            ch = b["channel"] + " (name only)"
        else:
            ch = "no vehicle_common row"
        lines.append(f"| `{b['behaviour']}` | {ch} | {b['parts']} | {b['entities']} | "
                     f"{b['chassis']} | {', '.join('`' + c + '`' for c in b['classes']) or '-'} | "
                     f"{b['proof']} |")
    lines += ["",
              f"**{len(beh)} behaviours** in use, "
              f"**{len(used_names & {r['name'] for t in d['tables'] for r in t['rows']})}** of them "
              f"with a `vehicle_common` row. The **{len(no_table)}** without one group like "
              "this in this record's reading - an inference, because none of them has a row to "
              "prove it:",
              "",
              ] + [f"* {label}: " + ", ".join(f"`{n}`" for n in names)
                   for label, names in group_rows] + [
              "",
              f"The remaining **{len(residual)}** are named by shipped parts but no G2 record read "
              "here names what moves them - " + ", ".join(f"`{n}`" for n in residual)
              + " - so their mechanism is UNKNOWN. None of the 29 is evidence for a writer.",
              "",
              f"**Unproven on a car ({len(unproven)}):** "
              + ", ".join(f"`{b['behaviour']}`" for b in unproven) + ".",
              "",
              "Those are the behaviours a B-05 port cannot copy from another `CCar`: every user is",
              "an aircraft, boat, helicopter, bike or train. " + ab_note,
              "",
              "## 3. The per-part arrays",
              "",
              "| array | modules with rows (of " + str(len(d["arrays"]["modules"])) + ") | rows | "
              "what a row stores |",
              "|---|---|---|---|"]
    for arr in ARRAYS:
        members = sorted({m for mod in d["arrays"]["modules"] for m in mod["members"][arr]})
        lines.append(f"| `{arr}[]` | {counts[arr]['modules']} | {counts[arr]['rows']} | "
                     f"{', '.join('`' + m + '`' for m in members) or '`part_index` only'} |")
    rot = next((m["members"]["rotating_parts"] for m in d["arrays"]["modules"]
                if m["rows"]["rotating_parts"]), [])
    lines += ["",
              f"`door_parts[]` and `hinged_parts[]` store **only** a part index: the Serpente's",
              f"{donor_doors} doors and the APC's {apc_doors} are indices, nothing else, and the "
              f"{counts['hinged_parts']['rows']} hinged rows",
              f"across {counts['hinged_parts']['modules']} modules carry no axis or limit either - "
              "those come from `.physicsc`",
              "(G2-13). `rotating_parts[]` is the one array with its own geometry: a part index",
              "plus " + (", ".join('`' + m + '`' for m in rot if m != "part_index")
                        if rot else "nothing") + ".",
              turret_note,
              "",
              "## 4. Validation and limits",
              "",
              "`jc3moving.py --check` re-reads the module and the census, rebuilds both files and",
              f"compares them: table row counts are {table_rows['all_door_part_properties']} doors / "
              f"{table_rows['all_hinged_part_properties']} hinged / "
              f"{table_rows['all_rotating_part_properties']} rotating / "
              f"{table_rows['all_fin_part_properties']} fin / "
              f"{table_rows['all_spring_part_properties']} spring; every hinged row has a "
              "non-empty `target_position_variable` and every",
              "rotating row an `rpm_variable`; every name in the door/fin/spring tables has no",
              "members besides `name`; `Turret` and `Cannon` have no `vehicle_common` row; every",
              "behaviour's proof follows from its chassis classes and every behaviour has a class;",
              "the six turreted samples have no `hinged_parts[]`/`rotating_parts[]` rows; `AirBrake`",
              "is on one `CAirPlane` chassis and unproven on a car.",
              "",
              "**Limits.** The `vehicle_common` copy is read from one entity's container (the",
              f"Serpente civilian); no second copy exists in the index to diff against. The "
              f"{len(unused)} declared-but-unused names ({len(legs)} spider-leg parts, "
              f"{len(elevons)} elevons, "
              + ", ".join(f"`{n}`" for n in rest_unused) + ")",
              "have no user in the fleet, so their variables are declared, not exercised. The",
              f"array census covers the {len(modules)} parts modules in the local cache, not all "
              f"{fleet} vehicle records.",
              f"The class map resolves {census['classified']} of the {fleet} records: "
              f"{census['entities']} entities have a detail JSON and one of them",
              "(`v4603_plane_urga_cargotransport_military_cargo_tank.ee`) declares both `CCar` and",
              "`CAirPlane`, so it is dropped; every chassis that carries a behaviour still resolves",
              f"to one class ({len(chassis)} chassis, {empty_class} with an empty list). Which",
              "*code* writes a given variable (`steering_roll`, `hood_angle`) is not in any file",
              "read here - the table proves the binding, not the writer.",
              ""]
    return "\n".join(lines).rstrip() + "\n"


def invariants(d: dict) -> list[str]:
    bad = []
    tables = {t["table"]: t for t in d["tables"]}
    want = {"all_door_part_properties": 14, "all_hinged_part_properties": 25,
            "all_rotating_part_properties": 12, "all_fin_part_properties": 1,
            "all_spring_part_properties": 1}
    for k, n in want.items():
        if len(tables[k]["rows"]) != n:
            bad.append(f"{k} has {len(tables[k]['rows'])} rows, expected {n}")
    for r in tables["all_hinged_part_properties"]["rows"]:
        if not r["members"].get("target_position_variable"):
            bad.append(f"hinged row {r['name']} has no target_position_variable")
    for r in tables["all_rotating_part_properties"]["rows"]:
        if not r["members"].get("rpm_variable"):
            bad.append(f"rotating row {r['name']} has no rpm_variable")
    for key in ("all_door_part_properties", "all_fin_part_properties",
                "all_spring_part_properties"):
        for r in tables[key]["rows"]:
            if r["members"]:
                bad.append(f"{key} row {r['name']} has members {sorted(r['members'])}")
    names = {b["behaviour"] for b in d["behaviours"]}
    for must in ("Turret", "Cannon", "Wheel", "Body"):
        if must not in names:
            bad.append(f"behaviour {must} missing from the census")
        if must in {r["name"] for t in d["tables"] for r in t["rows"]}:
            bad.append(f"behaviour {must} unexpectedly has a vehicle_common row")
    for b in d["behaviours"]:
        if (b["proof"] == "proven-on-CCar") != ("CCar" in b["classes"]):
            bad.append(f"{b['behaviour']} proof does not follow from its classes")
        if b["channel"] == "hinged" and not b["variable"]:
            bad.append(f"{b['behaviour']} is hinged without a variable")
    if not d["arrays"]["counts"]["door_parts"]["rows"]:
        bad.append("door_parts is empty in every cached module")
    for t in d["arrays"].get("turreted", []):
        if t["rows"] is None:
            bad.append(f"turreted module {t['module']} is missing from the parts cache")
        elif t["rows"]["hinged_parts"] or t["rows"]["rotating_parts"]:
            bad.append(f"turreted module {t['module']} has hinged/rotating rows: {t['rows']}")
    ab = next((b for b in d["behaviours"] if b["behaviour"] == "AirBrake"), None)
    if ab is None:
        bad.append("AirBrake is missing from the census; the card's Q-1 probe has no sample")
    else:
        if ab["classes"] != ["CAirPlane"]:
            bad.append(f"AirBrake classes are {ab['classes']}, expected ['CAirPlane']")
        if ab["chassis"] != 1:
            bad.append(f"AirBrake is on {ab['chassis']} chassis, expected 1")
        if ab["proof"] != "unproven-on-CCar":
            bad.append("AirBrake is proven on a car; the Q-1 probe claim no longer holds")
    for b in d["behaviours"]:
        if not b["classes"]:
            bad.append(f"{b['behaviour']} has no chassis class")
    return bad


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(d))
    print(f"{JSON_NAME}: {len(d['behaviours'])} behaviours, "
          f"{d['source']['rows']} table rows, {len(d['arrays']['modules'])} modules")
    print(f"{MD_NAME}: {len(open(os.path.join(OUT, MD_NAME), encoding='utf-8').read().splitlines())} lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing")
        return 1
    old = json.load(open(jp, encoding="utf-8"))
    if old != d:
        for k in sorted(set(old) | set(d)):
            if old.get(k) != d.get(k):
                bad.append(f"json section changed: {k}")
                break
    md = render_md(d)
    if md != open(mp, encoding="utf-8").read():
        import difflib
        diff = list(difflib.unified_diff(open(mp, encoding="utf-8").read().splitlines(),
                                         md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {len(d['behaviours'])} behaviours, "
          f"{d['source']['rows']} table rows "
          f"({sum(1 for b in d['behaviours'] if b['proof'] == 'proven-on-CCar')} proven on CCar), "
          f"{d['arrays']['counts']['door_parts']['rows']} door rows")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    if what == "tables":
        print(json.dumps(d["tables"], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
    elif what == "behaviours":
        print(json.dumps(d["behaviours"], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
    elif what == "arrays":
        print(json.dumps(d["arrays"]["counts"], indent=1, sort_keys=True)[:4000])
    else:
        print("one of: tables, behaviours, arrays")
        return 2
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("what", nargs="?", default="tables")
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
