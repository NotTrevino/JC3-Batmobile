#!/usr/bin/env python
"""jc3forcepulse.py - G2-17: every `CForcePulse` in the fleet - members, ranges, trigger.

The card asks two things of the decoded graphs:

  1. dump every `CForcePulse` property per entity;
  2. find what triggers it (collision, horn, explosion) by comparing values across
     vehicles that differ in behaviour.

Everything here is derived from three inputs:

  * `E:\\Modding\\_shared\\gamedata\\JC3grab\\detail\\*.ee.json`  - the 232 vehicle graphs (the card's In
    list), used to enumerate the entities and to agree with `FEATURE_CENSUS.json`;
  * the archives themselves, re-decoded per entity with `jc3wiring.decode_epe`, because
    `jc3detail.parse_epe` skips unnamed `<value id=...>` rows - and 35 of a pulse's ~40
    members, including every pointer, live exactly there;
  * the same entity's `.ee` container, whose embedded `<tune>.ftunec` carries the eight
    `ForcePulseSettings` numbers behind `SettingsFile` (read with `jc3adf`).

The trigger question has both a data answer and a data hole:

  * a Jenkins-hashed pointer `id:B5AE7986` (name not in any shipped name table -> the
    name is UNKNOWN, the id is what the file gives) is set by exactly one owner object on
    293 of the 307 pulses: the vehicle root class for the vehicle's own blast, the weapon
    component for that weapon's blast;
  * the other 14 stay unowned: the ten barrel blasts carry an *outgoing* `id:73D4D940`
    pointer to a `CEntityObject` and nest under their `CRigidObject`, the two loose-cargo
    blasts point at ids that do not resolve in the graph, and the EMP pulse has no owner
    at all (G2-16 found the `entry.use_item` action but no pointer) -> trigger UNKNOWN
    -> Q-1 probe;
  * no tune path in the fleet mentions horn or collision; all 23 are explosion tunes: 22
    under `jc_explosions/` and one bossfight prototype (`prototype_missile_explosion_sam`).

Usage:
  python jc3forcepulse.py --write
  python jc3forcepulse.py --check
  python jc3forcepulse.py dump <substring>
"""
from __future__ import annotations

import argparse
import collections
import difflib
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
import jc3wiring  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
JSON_NAME = "FORCEPULSE.json"
MD_NAME = "FORCEPULSE.md"
CENSUS = os.path.join(OUT, "FEATURE_CENSUS.json")

# The pointer every owner carries. Its property name is a Jenkins hash with no hit in
# the shipped dictionaries (G2-11 recovered six names the same way, this one did not
# match), so it stays an id - never a guessed name (R4).
OWNER_POINTER = "id:B5AE7986"
NULL_OID = "00000000"
NAMED_MEMBERS = ("SettingsFile", "name", "name_hash", "world", "_object_id")
ROOT_CLASSES = ("CCar", "CAirPlane", "CBoat", "CHelicopter", "CTrain")
EXAMPLES = (
    ("donor, civilian", "v0300_car_kensington_sportsmuscle_civilian_01.ee"),
    ("donor, armed", "v0300_car_kensington_sportsmuscle_signature_preorder.ee"),
    ("medium tank", "v0201_car_capstone_mediumtank_military_01.ee"),
    ("corvette", "v1202_boat_capstone_corvette_military_01.ee"),
    ("plain oldtruck", "v0505_car_solar_oldtruck_rebel_01.ee"),
    ("oldtruck, barrels", "v0505_car_solar_oldtruck_commercial_cargo_barrel.ee"),
    ("oldtruck, loose cargo", "v0505_car_solar_oldtruck_commercial_cargo_random.ee"),
    ("oldtruck, EMP", "v0505_car_solar_oldtruck_rebel_emp_01.ee"),
    ("assault helicopter", "v2200_helicopter_capstone_assault_military_01.ee"),
)


# ----------------------------------------------------------------- reading
def graph_entities() -> list[str]:
    files = sorted(p for p in glob.glob(os.path.join(RAW, "detail", "*.ee.json"))
                   if not p.endswith("detail_index.json"))
    if not files:
        sys.exit("no detail graphs under %s/detail - run jc3detail.py build --all" % RAW)
    out = []
    for p in files:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        out.append(d.get("entity") or os.path.basename(p))
    return sorted(out)


def container(ee: str, rows: list[dict]) -> tuple[bytes, list[tuple[str, int, int]]]:
    return jc3detail.inner_files(jc3grab.read_entry(jc3detail.pick(rows, ee), GAME))


def tune_of(stream: bytes, entries, settings: str) -> dict:
    """Decode the `<stem>.ftunec` member this pulse's SettingsFile names."""
    stem = settings.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    hit = next((e for e in entries if e[0].endswith(stem + ".ftunec")), None)
    if hit is None:
        return {"file": None, "values": None}
    vals = {n: v for n, _t, v in jc3adf.walk(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]]))}
    return {"file": hit[0], "values": vals}


def num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def resolve_oids(value: str, oid_cls: dict) -> list[dict]:
    """Resolve the oid tokens in a pointer/vec_events value against this graph."""
    out = []
    for tok in value.replace(",", " ").split():
        if "=" not in tok:
            continue
        cls, name = oid_cls.get(tok, ("(unresolved)", ""))
        out.append({"oid": tok, "class": cls, "name": name})
    return out


def tune_group(path: str) -> str:
    if "/jc_explosions/vehicles/" in path:
        return "vehicles"
    if "/jc_explosions/weapons/" in path:
        return "weapons"
    if "/jc_explosions/structures/" in path:
        return "structures"
    if "/jc_explosions/" in path:
        return "explosions"
    return "other"


# ------------------------------------------------------------------- build
def build() -> dict:
    rows = jc3index.load_index(OUT)
    entities = []
    names = collections.Counter()
    settings = collections.Counter()
    positions = collections.Counter()
    member_values: dict[str, list] = collections.defaultdict(list)
    owner_classes = collections.Counter()
    pointer_classes: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    unowned = []
    other_ref_count = 0
    other_ref_list = []
    horn_entities = 0

    for ee in graph_entities():
        objs, _doc = jc3wiring.decode_epe(ee, rows, GAME)
        stream, entries = container(ee, rows)
        oid_cls = {o.oid: (o.cls, o.name) for o in objs if o.oid}
        oids = {o.oid for o in objs if o.cls == "CForcePulse" and o.oid}
        horn = any(o.cls == "SAttachedEffect" and o.name == "horn" for o in objs)
        horn_entities += 1 if horn else 0

        pulses = []
        for o in (o for o in objs if o.cls == "CForcePulse"):
            oid = o.oid
            owners = [q for q in objs if q is not o and oid and q.get(OWNER_POINTER) == oid]
            others = []
            for q in objs:
                if q is o:
                    continue
                for k, v in q.props.items():
                    if k in ("_object_id", OWNER_POINTER) or not isinstance(v, str):
                        continue
                    if oid and oid in v:
                        others.append({"class": q.cls, "name": q.name, "member": k})
                        other_ref_list.append({"entity": ee, "class": q.cls,
                                               "object": q.name, "member": k, "oid": oid})
            other_ref_count += len(others)
            out = {}
            for k, v in o.props.items():
                if not k.startswith("id:") or "=" not in v:
                    continue
                hits = resolve_oids(v, oid_cls)
                out[k] = hits
                for h in hits:
                    pointer_classes[k][h["class"]] += 1
            parent = o.parent
            if parent is not None and not parent.props:
                parent = None                      # the document wrapper, not an owner
            xyz = jc3wiring.xyz(o.get("world"))
            names[o.name] += 1
            settings[o.get("SettingsFile")] += 1
            positions[tuple(xyz) if xyz else None] += 1
            for k, v in o.props.items():
                member_values[k].append(v)
            if owners:
                for q in owners:
                    owner_classes[q.cls] += 1
            else:
                owner_classes["(none)"] += 1
                unowned.append({"entity": ee, "name": o.name,
                                "settings": o.get("SettingsFile"),
                                "parent": parent.cls if parent else None,
                                "parent_name": parent.name if parent else None,
                                "xyz": xyz,
                                "out_refs": out})
            pulses.append({
                "name": o.name,
                "settings": o.get("SettingsFile"),
                "xyz": xyz,
                "oid": oid,
                "parent": {"class": parent.cls, "name": parent.name} if parent else None,
                "owners": [{"class": q.cls, "name": q.name, "member": OWNER_POINTER}
                           for q in owners],
                "other_refs": others,
                "out_refs": out,
                "tune": tune_of(stream, entries, o.get("SettingsFile")),
                "props": dict(sorted(o.props.items())),
            })

        weapon_components = []
        for o in objs:
            if "Weapon" not in o.cls:
                continue
            target = o.get(OWNER_POINTER)
            hit = next((p["name"] for p in pulses
                        if target not in ("", NULL_OID) and p["oid"] == target), None)
            weapon_components.append({
                "class": o.cls, "name": o.name, "weapon_id": o.get("weapon_id") or None,
                "blast_pointer": None if target in ("", NULL_OID) else target,
                "blast_pulse": hit,
            })

        entities.append({
            "entity": ee,
            "chassis": ee.split("/")[-2],
            "scheme": ee.split("/")[3] if ee.count("/") >= 4 else "",
            "root_class": next((o.cls for o in objs if o.cls in ROOT_CLASSES), None),
            "horn_effect": horn,
            "weapon_components": weapon_components,
            "pulses": pulses,
        })

    # ---- aggregates
    by_tune: dict[str, dict] = {}
    for e in entities:
        for p in e["pulses"]:
            t = by_tune.setdefault(p["settings"], {
                "path": p["settings"], "group": tune_group(p["settings"]),
                "objects": 0, "entities": set(), "chassis": set(),
                "names": collections.Counter(), "files": set(), "value_sets": set(),
            })
            t["objects"] += 1
            t["entities"].add(e["entity"])
            t["chassis"].add(e["chassis"])
            t["names"][p["name"]] += 1
            if p["tune"]["file"]:
                t["files"].add(p["tune"]["file"])
            if p["tune"]["values"] is not None:
                t["value_sets"].add(tuple(sorted(p["tune"]["values"].items())))
    tunes = []
    for path in sorted(by_tune):
        t = by_tune[path]
        values = None
        if len(t["value_sets"]) == 1:
            values = dict(sorted(next(iter(t["value_sets"]))))
        tunes.append({
            "path": path, "group": t["group"], "objects": t["objects"],
            "entities": len(t["entities"]), "chassis": len(t["chassis"]),
            "names": dict(sorted(t["names"].items())),
            "files": sorted(t["files"]), "consistent": len(t["value_sets"]) == 1,
            "values": values,
        })

    members = []
    for key in sorted(member_values):
        vals = member_values[key]
        present = [v for v in vals if v != ""]
        numbers = [float(v) for v in present if num(v) is not None]
        rec = {
            "member": key,
            "kind": "hashed" if key.startswith("id:") else "named",
            "present": len(present), "distinct": len(set(vals)),
        }
        if len(present) == len(numbers) and present:
            rec["min"], rec["max"] = min(numbers), max(numbers)
        elif rec["distinct"] <= 6:
            rec["values"] = sorted(set(vals))[:6]
        members.append(rec)

    ranges = {}
    for t in tunes:
        for k, v in (t["values"] or {}).items():
            n = num(v)
            if n is None:
                continue
            r = ranges.setdefault(k, {"min": n, "max": n, "tunes": 0})
            r["min"], r["max"] = min(r["min"], n), max(r["max"], n)
    for k, r in ranges.items():
        r["tunes"] = sum(1 for t in tunes if t["values"] and k in t["values"])

    totals = {
        "graphs": len(entities),
        "entities_with_pulses": sum(1 for e in entities if e["pulses"]),
        "objects": sum(len(e["pulses"]) for e in entities),
        "chassis": len({e["chassis"] for e in entities}),
        "root_classes": dict(sorted(collections.Counter(
            e["root_class"] or "(none)" for e in entities).items())),
        "multi_pulse_entities": sum(1 for e in entities if len(e["pulses"]) > 1),
        "horn_entities": horn_entities,
        "other_refs": other_ref_count,
        "other_ref_list": other_ref_list,
        "pointer_classes": {k: dict(sorted(v.items()))
                            for k, v in sorted(pointer_classes.items())},
        "world_missing": sum(1 for e in entities for p in e["pulses"]
                             if "world" not in p["props"]),
    }
    census = None
    if os.path.exists(CENSUS):
        rows_c = json.load(open(CENSUS, encoding="utf-8"))["weapon_classes"]
        c = next((r for r in rows_c if r.get("class") == "CForcePulse"), None)
        if c:
            census = {"objects": c["objects"], "entities": c["entities"],
                      "chassis": c["chassis"]}

    out = {
        "totals": totals,
        "census": census,
        "names": dict(sorted(names.items())),
        "positions": {str(k): v for k, v in sorted(positions.items(),
                                                   key=lambda kv: str(kv[0]))},
        "members": members,
        "tunes": tunes,
        "ranges": dict(sorted(ranges.items())),
        "owners": dict(sorted(owner_classes.items())),
        "unowned": sorted(unowned, key=lambda u: (u["entity"], u["name"])),
        "entities": entities,
    }
    out["digest"] = hashlib.sha1(json.dumps(out, sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()[:16]
    return out


# --------------------------------------------------------------------- md
def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return jc3wiring.num(v)
    return str(v)


def tune_cell(t: dict, key: str) -> str:
    if not t.get("values"):
        return "UNKNOWN"
    return fmt(num(t["values"].get(key)))


def render_md(d: dict) -> str:
    tot = d["totals"]
    owners = d["owners"]
    owned = sum(v for k, v in owners.items() if k != "(none)")
    unowned = d["unowned"]
    weapon_pulses = sum(v for k, v in owners.items()
                        if k in ("CBulletWeaponBase", "CMissileWeaponBase"))
    root_pulses = sum(v for k, v in owners.items() if k in ROOT_CLASSES)
    by_name_tune = collections.Counter()
    for e in d["entities"]:
        for p in e["pulses"]:
            by_name_tune[(p["name"], p["settings"].rsplit("/", 1)[-1])] += 1

    L = [
        "# `CForcePulse` - the fleet's blast component",
        "",
        "G2-17. **Trigger: explosion, and the owner says which explosion.** Every one of the",
        f"{tot['objects']} pulses in {tot['entities_with_pulses']} vehicle `.ee` files is a",
        "blast: its `SettingsFile` names one of "
        f"{len(d['tunes'])} explosion tunes, and no tune path or pulse name in the whole",
        "fleet mentions a horn or a collision. What the card really needs is *which* event",
        f"fires it, and that is written as a pointer: {owned} of {tot['objects']} pulses are",
        f"pointed at by exactly one owner object through `{OWNER_POINTER}` - the vehicle root",
        "for the vehicle's own blast, the weapon component for that weapon's blast. The",
        f"{len(unowned)} without an owner are recorded as **UNKNOWN**, not explained: the",
        "barrel blasts nest under their `CRigidObject` and point out at their own entity,",
        "but nothing points at them, and the EMP pulse has no owner",
        "at all, so \"the use-item action fires it\" stays an inference from G2-16 and becomes",
        "a Q-1 probe.",
        "",
        "## 1. Members - every property of every pulse",
        "",
        f"A pulse carries {len(d['members'])} distinct members: the "
        f"{sum(1 for m in d['members'] if m['kind'] == 'named')} named ones below plus "
        f"{sum(1 for m in d['members'] if m['kind'] == 'hashed')} Jenkins-hashed `id:*` keys",
        "whose names are in no shipped name table (UNKNOWN; G2-11 recovered six such names,",
        "this hash family matched none). `world` is on every pulse. The members that are not",
        "universal: " + ", ".join(
            f"`{m['member']}` on {m['present']}" for m in d["members"]
            if 0 < m["present"] < tot["objects"])
        + ", and " + ", ".join(
            f"`{m['member']}`" for m in d["members"] if m["present"] == 0)
        + " declared empty on all " + str(tot["objects"]) + ". Values are counted over all",
        "pulses in `FORCEPULSE.json` `entities[].pulses[].props`.",
        "",
        "| member | kind | set on | distinct | values / range |",
        "|---|---|---:|---:|---|",
    ]
    for m in d["members"]:
        if "min" in m:
            vals = f"{fmt(m['min'])} .. {fmt(m['max'])}"
        elif "values" in m:
            vals = ", ".join(f"`{v}`" if v else "`(empty)`" for v in m["values"])
        else:
            vals = f"{m['distinct']} distinct"
        L.append(f"| `{m['member']}` | {m['kind']} | {m['present']} | "
                 f"{m['distinct']} | {vals} |")

    L += [
        "",
        "`_object_id` is of course unique per object; `name` holds 9 spellings; `SettingsFile`",
        f"holds {len(d['tunes'])} tunes; the hashed members are the interesting ones - three",
        "flags (`id:4912FC04`, `id:AE6F7EFF`, `id:CF4F7880`), one object reference to a",
        "`CMaterialEffectTable` (`id:D3DDD766`), and `id:B5AE7986`, which is the *incoming*",
        "pointer from the owner, not a member of the pulse itself (see §4).",
        "",
        "Pointers that leave the pulse, resolved against the same graph (empty values such as",
        f"`{NULL_OID}` are not counted):",
        "",
        "| member | resolved target class (values) |",
        "|---|---|",
    ]
    for member, targets in d["totals"]["pointer_classes"].items():
        L.append(f"| `{member}` | " + ", ".join(f"`{c}` {n}"
                                               for c, n in targets.items()) + " |")
    p73 = tot["pointer_classes"].get("id:73D4D940", {})
    L += [
        "",
        "`id:73D4D940` is the only pointer that leads anywhere: "
        f"{sum(p73.values())} values naming "
        + (", ".join(f"`{c}`" for c in p73 if c != "(unresolved)") or "nothing resolvable")
        + " - a root-level `CEntityObject` next to the barrel `CRigidObject`, not its parent.",
        "The `vec_events` members hold",
        "event ids whose names are not in the files.",
        "",
        "## 2. The fleet",
        "",
        "| quantity | count |",
        "|---|---:|",
        f"| detail graphs read | {tot['graphs']} |",
        f"| entities carrying a pulse | {tot['entities_with_pulses']} |",
        f"| `CForcePulse` objects | {tot['objects']} |",
        f"| chassis | {tot['chassis']} |",
        f"| entities with more than one pulse | {tot['multi_pulse_entities']} |",
        f"| entities with an `SAttachedEffect horn` | {tot['horn_entities']} |",
        f"| references to a pulse from any other member (besides `{OWNER_POINTER}`) "
        f"| {tot['other_refs']} |",
    ]
    if d["census"]:
        L.append(f"| `FEATURE_CENSUS.json` agrees | objects {d['census']['objects']}, "
                 f"`.ee` {d['census']['entities']}, chassis {d['census']['chassis']} |")
    L += [
        "",
        "By root class: " + ", ".join(f"`{k}` {v}" for k, v in tot["root_classes"].items())
        + ".",
        "",
        "| pulse name | tune | objects |",
        "|---|---|---:|",
    ]
    for (name, tune), n in sorted(by_name_tune.items()):
        L.append(f"| `{name}` | `{tune}` | {n} |")
    L += [
        "",
        "Positions: " + ", ".join(f"`{k}` x{v}" for k, v in d["positions"].items()) + ".",
        "Everything sits at the entity origin except the EMP pulse (over the flatbed device)",
        "and the barrel/cargo pulses (on the cargo).",
        "",
        "## 3. Tunes and fleet ranges",
        "",
        "Every `SettingsFile` resolves to an embedded `<tune>.ftunec` in the same `.ee`, eight",
        "`ForcePulseSettings` numbers each, and the same tune decodes identically in every",
        "entity that carries it:",
        "",
        "| tune | group | objects | `.ee` | chassis | Player dmg / r | AI dmg / r |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for t in d["tunes"]:
        stem = t["path"].rsplit("/", 1)[-1]
        L.append(f"| `{stem}` | {t['group']} | {t['objects']} | {t['entities']} | "
                 f"{t['chassis']} | {tune_cell(t, 'PlayerDamage')} / "
                 f"{tune_cell(t, 'PlayerDamageRadius')} | {tune_cell(t, 'AIDamage')} / "
                 f"{tune_cell(t, 'AIDamageRadius')} |")
    L += [
        "",
        "Fleet ranges over those tunes (the card's \"fleet ranges\"):",
        "",
        "| tune member | min | max | tunes |",
        "|---|---:|---:|---:|",
    ]
    for k, r in d["ranges"].items():
        L.append(f"| `{k}` | {fmt(r['min'])} | {fmt(r['max'])} | {r['tunes']} |")
    L += [
        "",
        "The spread is the point: the same class runs from `gen_explosion_5m_nodamage`",
        "(0 damage, push only) through the stock car blast (500/5 m) to `w704_m488`",
        "(3000/50 m) and the fuel-tank blast (1000/50 m). `*RadiusPercentageMax`/`*RadiusMin`",
        "say how much of the radius keeps full damage - 0.0/0.0 on the stock vehicle blasts",
        "(damage falls off at once), 1.0/1.0 on the EMP and the bomb.",
        "",
        "## 4. What fires a pulse",
        "",
        "### 4.1 The card's three candidates, by the files",
        "",
        "| candidate | evidence | verdict |",
        "|---|---|---|",
        f"| horn | {tot['horn_entities']} entities carry an `SAttachedEffect` named `horn`; "
        f"0 of {len(d['tunes'])} tune paths and 0 of {len(d['names'])} pulse names mention a "
        "horn | horn does not trigger a pulse |",
        f"| collision | 0 of {len(d['tunes'])} tune paths mention collision; no pulse owner is "
        "a collision object | collision does not trigger a pulse |",
        f"| explosion | {sum(1 for t in d['tunes'] if t['group'] != 'other')} of "
        f"{len(d['tunes'])} tunes live under `jc_explosions/` and the remaining one is named "
        "`prototype_missile_explosion_sam` | every pulse is an explosion blast |",
        "",
        "### 4.2 The owner pointer",
        "",
        f"`{OWNER_POINTER}` is set on the owner object and holds the pulse's `_object_id`.",
        "Owners, counted per pulse:",
        "",
        "| owner class | pulses |",
        "|---|---:|",
    ]
    for k, v in sorted(owners.items()):
        L.append(f"| `{k}` | {v} |")
    L += [
        "",
        f"- **{root_pulses} pulses are owned by the vehicle root class** "
        f"({', '.join(k for k in owners if k in ROOT_CLASSES)}) and every one of them uses the",
        "  explosion tune for that vehicle's own type - so the vehicle carries *its* blast,",
        "  which is what a destroyed vehicle sets off. The event that reads the pointer is",
        "  code: the files prove the owner and the tune, not the moment (that part of the",
        "  trigger is UNKNOWN and belongs to Q-1).",
        f"- **{weapon_pulses} pulses are owned by a weapon component** "
        f"({', '.join(k for k in owners if 'Weapon' in k)}) and each uses that weapon's own",
        "  blast tune (`jc_explosions/weapons/<id>.ftune`) - so the weapon's projectile",
        "  carries the blast. Which instant (fire or impact) is code, but the pairing is",
        "  exact: the pulse only exists on entities that are wired for that weapon id.",
        "",
        "Exactly one other reference to a pulse exists in the fleet, and it is a script, not",
        "an owner: " + "; ".join(
            f"`{r['entity'].rsplit('/', 1)[-1]}` `{r['class']}` `{r['object']}` -> "
            f"`{r['member']}` -> `{r['oid']}`" for r in tot["other_ref_list"])
        + ". The target is that build's `BOMB_JEEP` vehicle-rule pulse (tune `w704_m488`), so",
        "the rule's graph is part of how that pulse is used - the graph's bytecode is not",
        "decoded here, so what it does with the pulse is UNKNOWN.",
        "",
        "### 4.3 Pulses with no owner",
        "",
        "| entity | pulse | tune | nested under |",
        "|---|---|---|---|",
    ]
    for u in d["unowned"]:
        L.append(f"| `{u['entity'].rsplit('/', 1)[-1]}` | `{u['name']}` | "
                 f"`{u['settings'].rsplit('/', 1)[-1]}` | "
                 f"`{u['parent']}` `{u['parent_name']}` |")
    L += [
        "",
        "The barrel blasts are children of their own `CRigidObject barrel` and each carries",
        f"an outgoing `id:73D4D940` pointer to a `CEntityObject` "
        f"({sum(1 for u in unowned if 'id:73D4D940' in u['out_refs'])} of {len(unowned)} "
        "unowned pulses), so an `EntityObject` of the cargo build is named in the data - but no",
        "member points *at* the pulse, so the link is nesting plus an outgoing pointer, not",
        "an owner. The **EMP pulse has no owner and no parent but the vehicle",
        "root**: G2-16 showed `entry.use_item` -> `S_STUNT_USE_ITEM_VEHICLE` with prompt",
        "`ui_activate_emp` and no pointer to the pulse, so \"use item fires the EMP\" remains",
        "an inference and is **UNKNOWN in data -> Q-1 probe**.",
        "",
        "## 5. Vehicles that differ in behaviour",
        "",
        "| | pulses (name -> tune, owner) |",
        "|---|---|",
    ]
    by_entity = {e["entity"].rsplit("/", 1)[-1]: e for e in d["entities"]}
    for label, leaf in EXAMPLES:
        e = by_entity.get(leaf)
        if e is None:
            L.append(f"| {label} | **missing: {leaf}** |")
            continue
        cells = []
        for p in e["pulses"]:
            owner = p["owners"][0]["class"] if p["owners"] else "**none**"
            cells.append(f"`{p['name']}` -> `{p['settings'].rsplit('/', 1)[-1]}` ({owner})")
        L.append(f"| {label} | " + "<br>".join(cells) + " |")
    L += [
        "",
        "- **same chassis, armed or not**: the donor's civilian build has one pulse, its own",
        "  car blast; the signature build adds the `w618_sportsmuscle_missile` blast owned by",
        "  its `CMissileWeaponBase`. The weapon is the only difference.",
        "- **two weapons, one blast**: on the medium tank the cannon's `w602` pulse is owned",
        "  by `CBulletWeaponBase w602_mediumtank_canon` while the coax `w603` component's",
        f"  `{OWNER_POINTER}` is `{NULL_OID}` - the machine gun has no force pulse at all.",
        "- **same class, different blast**: the corvette uses `boat_explosion_large` (500/15 m)",
        "  where every other boat uses `boat_explosion_medium` (500/10 m).",
        "- **one chassis, four behaviours**: the oldtruck's plain build has only the car blast;",
        "  the barrel build nests ten `barrel_explosion` pulses under its cargo; the loose-cargo",
        "  build carries two `gen_explosion_5m_nodamage` pulses (0 damage - push only); the",
        "  EMP build adds the unowned EMP pulse (100/25 m at full radius).",
        "- **helicopter**: the assault helicopter's root owns `helicopter_explosion_medium`,",
        "  `CMissileWeaponBase w601_helicopter_missile` owns `rpg_assault_helicopter`",
        "  (1200/10 m) and `CMissileWeaponBase w615_helicopter_heavy_missile` owns its own",
        "  2200/20 m blast - one pulse per wired weapon, plus the vehicle's own.",
        "",
        "## 6. Validation and limits",
        "",
        "`jc3forcepulse.py --check` re-decodes all 232 entities from the archives, rebuilds",
        f"`FORCEPULSE.json` and `FORCEPULSE.md` byte for byte and asserts the invariants:",
        f"{tot['objects']} objects over {tot['entities_with_pulses']} `.ee` and "
        f"{tot['chassis']} chassis (the numbers P0-2's census printed); the "
        f"{len(d['members'])} members with exactly the 5 named ones (`world` on all "
        f"{tot['objects']}); "
        f"{len(d['tunes'])} tunes all resolving to a decoded `.ftunec`, grouped "
        + ", ".join(f"{k} {v}" for k, v in sorted(collections.Counter(
            t["group"] for t in d["tunes"]).items()))
        + "; `car_explosion_medium` 500/5/0/0; the EMP pulse at (0, 2.0356, 0.6992) with",
        "100/25/1/1 (G2-16's numbers); the owner census "
        f"{dict(owners)}; exactly {tot['other_refs']} reference that is not the owner",
        "pointer, and it is the mm340 `GraphScript`; 0 horn and 0 collision tunes; and the",
        "census file agreeing object for object. Tamper test: change one pulse member in the json",
        "and `--check` must fail, rebuild and it passes again.",
        "",
        "**Limits.** The pointer's *name* is UNKNOWN (a Jenkins hash with no dictionary hit),",
        "so what the engine calls it cannot be stated. The owner pointer proves who carries",
        "the blast, not the code path that fires it - the firing moment for the vehicle blast",
        "and the exact weapon instant are not in any file. Which code runs after",
        "`S_STUNT_USE_ITEM_VEHICLE` is likewise not in the files, so the EMP trigger stays",
        "UNKNOWN (Q-1). The outgoing pointers on the unowned pulses resolve to an object id",
        "only when the target is in the same graph; the mm340 graph's bytecode is not decoded,",
        "so what it does with its pulse is UNKNOWN. The census covers the 232",
        "decoded vehicle graphs, not every `.ee` in the index.",
        "",
    ]
    return "\n".join(L).rstrip() + "\n"


# -------------------------------------------------------------- invariants
def invariants(d: dict) -> list[str]:
    bad = []
    tot = d["totals"]
    if tot["objects"] != 307:
        bad.append(f"objects {tot['objects']}")
    if tot["entities_with_pulses"] != 232 or tot["graphs"] != 232:
        bad.append(f"graphs/entities {tot['graphs']}/{tot['entities_with_pulses']}")
    if tot["chassis"] != 79:
        bad.append(f"chassis {tot['chassis']}")
    if d["census"] and (d["census"]["objects"], d["census"]["entities"],
                        d["census"]["chassis"]) != (307, 232, 79):
        bad.append(f"census {d['census']}")
    named = sorted(m["member"] for m in d["members"] if m["kind"] == "named")
    if named != sorted(NAMED_MEMBERS):
        bad.append(f"named members {named}")
    # 26 hashed + 5 named, counted independently from the cached Gibbed XML
    # (tmp/freebuff/probe_g2_17.py: the same union, 30 values on 297 pulses, 31 on 10).
    if len(d["members"]) != 31 or \
            sum(1 for m in d["members"] if m["kind"] == "hashed") != 26:
        bad.append(f"member count {len(d['members'])}")
    present = {m["member"]: m["present"] for m in d["members"]}
    if present.get("world") != tot["objects"] or tot["world_missing"] != 0:
        bad.append(f"world present {present.get('world')} / missing {tot['world_missing']}")
    if present.get("id:73D4D940") != 10 or present.get("id:7FD59340") != 1 or \
            present.get("id:06A05F33") != 14:
        bad.append(f"partial members {present}")
    if len(d["tunes"]) != 23:
        bad.append(f"tunes {len(d['tunes'])}")
    if any(not t["consistent"] or not t["values"] for t in d["tunes"]):
        bad.append("a tune failed to decode or differs between entities")
    groups = collections.Counter(t["group"] for t in d["tunes"])
    if dict(groups) != {"vehicles": 8, "weapons": 11, "structures": 2,
                        "explosions": 1, "other": 1}:
        bad.append(f"tune groups {dict(groups)}")
    car = next((t for t in d["tunes"] if t["path"].endswith("car_explosion_medium.ftune")), None)
    if not car or car["objects"] != 115 or \
            num(car["values"].get("PlayerDamage")) != 500 or \
            num(car["values"].get("PlayerDamageRadius")) != 5.0:
        bad.append(f"car_explosion_medium {car and (car['objects'], car['values'])}")
    if d["names"].get("CForcePulse") != 263:
        bad.append(f"pulse names {d['names']}")
    emp = next((p for e in d["entities"] for p in e["pulses"]
                if p["settings"].endswith("truck_emp.ftune")), None)
    if not emp or emp["xyz"] != [0, 2.0356, 0.6992] or emp["owners"]:
        bad.append(f"EMP pulse {emp and (emp['xyz'], emp['owners'])}")
    else:
        v = emp["tune"]["values"] or {}
        if (num(v.get("PlayerDamage")), num(v.get("PlayerDamageRadius"))) != (100, 25.0):
            bad.append(f"EMP tune {v}")
    if d["owners"].get("(none)") != len(d["unowned"]):
        bad.append("unowned list disagrees with owner census")
    if sum(d["owners"].values()) != tot["objects"] or len(d["unowned"]) != 14:
        bad.append(f"owner census does not cover the fleet: {d['owners']}")
    # Exactly one reference that is not the owner pointer: the mm340 GraphScript.
    refs = tot["other_ref_list"]
    if len(refs) != 1 or refs[0]["class"] != "CGraphScriptGameObject" or \
            refs[0]["member"] != "id:65424AC6" or \
            not refs[0]["entity"].endswith("v4603_plane_urga_cargotransport_mm340.ee"):
        bad.append(f"unexpected pulse refs {refs}")
    if tot["other_refs"] != len(refs):
        bad.append(f"{tot['other_refs']} refs to a pulse besides the owner pointer")
    if sum(1 for u in d["unowned"] if "id:73D4D940" in u["out_refs"]) != 10:
        bad.append("barrel pulses do not carry the outgoing entity pointer")
    if not any(u["entity"].endswith("rebel_emp_01.ee") for u in d["unowned"]):
        bad.append("the EMP pulse is not in the unowned list")
    horn_tunes = [t for t in d["tunes"] if "horn" in t["path"].lower()]
    coll_tunes = [t for t in d["tunes"] if "collis" in t["path"].lower()]
    if horn_tunes or coll_tunes:
        bad.append(f"horn/collision tunes {horn_tunes} {coll_tunes}")
    if not any("EMP" == n for n in d["names"]):
        bad.append("no pulse named EMP")
    return bad


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    bad = invariants(d)
    print(f"{JSON_NAME}/{MD_NAME}: {d['totals']['objects']} pulses, "
          f"{d['totals']['entities_with_pulses']} entities, "
          f"{d['totals']['chassis']} chassis, {len(d['tunes'])} tunes, "
          f"{len(d['members'])} members, {len(md.splitlines())} md lines"
          + (f", INVARIANTS: {'; '.join(bad)}" if bad else ""))
    return 1 if bad else 0


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
    tot = d["totals"]
    print(f"PASS: {tot['objects']} pulses / {tot['entities_with_pulses']} entities / "
          f"{tot['chassis']} chassis, {len(d['members'])} members, {len(d['tunes'])} tunes, "
          f"owners {dict(d['owners'])}, unowned {len(d['unowned'])}, "
          f"horn tunes 0, collision tunes 0")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    if what in ("members", "tunes", "owners", "unowned", "positions", "totals"):
        print(json.dumps(d[what], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
        return 0
    hits = [e for e in d["entities"] if what in e["entity"]]
    for e in hits:
        print(json.dumps(e, indent=1, sort_keys=True, ensure_ascii=False)[:12000])
    return 0 if hits else 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="totals")
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
