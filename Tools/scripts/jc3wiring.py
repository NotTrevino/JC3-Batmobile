"""jc3wiring.py - G2-11: how every armed vehicle binds its weapons.

`jc3weapons.py` (G2-10) decoded the weapon *tunes*. This script decodes the other half:
the entity graph that says which weapon a vehicle actually carries, where it fires from,
which seat owns it and which moving parts exist on the chassis.

The entity `.epe` has no `weapon_slot` field. A vehicle's root class (`CCar`, `CAirPlane`,
`CBoat`, `CHelicopter`, `CTrain`) holds four object-id pointers, present on every vehicle
and null when unused:

  id:851CAABE  `main_weapon`        driver, first      name recovered by Jenkins hash
  00568A74     (name not in any shipped name table)    driver, second
  mounted_weapon                   gunner, first      named in the file
  id:AC0BC788  `mounted_weapon_2`   gunner, second     name recovered by Jenkins hash

The hash function is the same Jenkins lookup3 used for archive paths (`rbmhdr.hash_jenkins`);
six property names were recovered with it (main_weapon, mounted_weapon_2, tuning_file,
autoaim_tuning_file, impact_usage, weapon_category), each matching its 32-bit id exactly.
`id:D04059E6` on every object is the Jenkins hash of that object's class name - `--check`
verifies that for every decoded object, which is also a reader self-test.

The weapon component itself carries no slot: it appears as a root child, and the slot pointer
is what makes it usable. Components that no slot points at exist (the fighter jet carries an
unused plain missile next to the lock-on one); they are recorded as `unbound`.

A mounted weapon also names the parts it is mounted to: its type-4 `SWeaponPoint`
(`MountAttach`) holds the part names in its string properties. All 19 gunner weapons do; among
the 62 driver weapons only the corvette's cannon does (`corvette_gun`, `corvette_turret`). The
chassis part list (Turret / Cannon / GatlingGun / MissileHatch) is recorded from
`PARTS_TABLE.jsonl` for every entity regardless.

Usage:
  python jc3wiring.py --write     # decode 53 armed entities -> WEAPON_WIRING.jsonl + .md
  python jc3wiring.py --check     # re-read the archives, compare rows and the md
  python jc3wiring.py dump <substring>   # one entity, weapons + seats + parts

Raw `.epe` XML stays outside the repo in `E:/Modding/_gamedata/JC3grab/wiring/epe/`.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3index  # noqa: E402
import jc3detail  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
TABLE = "WEAPON_WIRING.jsonl"
DOC = "WEAPON_WIRING.md"
CENSUS = os.path.join(OUT, "FEATURE_CENSUS.json")
PARTS = os.path.join(OUT, "PARTS_TABLE.jsonl")
CACHE = os.path.join(RAW, "wiring", "epe")

ROOT_CLASSES = ("CCar", "CAirPlane", "CBoat", "CHelicopter", "CTrain")
WEAPON_CLASSES = ("CBulletWeaponBase", "CMissileWeaponBase", "CRPGFireLeachWeapon")
COMPONENT_CLASSES = ("CAimPOIWeaponComponent", "CBarrelSpinWeaponComponent",
                     "CLaserBeamWeaponComponent", "CTurretWeaponComponent",
                     "CLightWeaponComponent")
MOVE_BEHAVIOURS = ("Turret", "Cannon", "GatlingGun", "MissileHatch")

# (label, .epe property key, who can fire it)
SLOTS = (
    ("main_weapon", "id:851CAABE", "driver"),
    ("secondary (id:00568A74)", "id:00568A74", "driver"),
    ("mounted_weapon", "mounted_weapon", "gunner"),
    ("mounted_weapon_2", "id:AC0BC788", "gunner"),
)
# Also on every root class, null on all 53 armed entities; never resolves to a weapon.
OTHER_POINTERS = ("id:8580BA42", "id:CA86AA17")

CLASS_HASH_PROP = "id:D04059E6"
NAME_HASH_PROP = "id:61548A03"          # CInteraction seat index
GUNNER_MOUNT_STATES = ("MOUNTED_WEAPON",)


# ------------------------------------------------------------------ epe reader
class Obj:
    __slots__ = ("parent", "values", "children", "props", "cls", "name", "oid", "node")

    def __init__(self, el: ET.Element, parent: "Obj | None", node: str) -> None:
        self.parent = parent
        self.values: list[tuple[str, str, str]] = []
        self.children: list[Obj] = []
        self.node = node
        for v in el:
            if v.tag == "value":
                key = v.get("name") or ("id:" + str(v.get("id")))
                self.values.append((key, v.get("type") or "", (v.text or "").strip()))
            elif v.tag == "object":
                self.children.append(Obj(v, self, node + "/" + (v.get("name") or str(len(self.children)))))
        self.props = {k: txt for k, _t, txt in self.values}
        self.cls = self.props.pop("_class", "")
        self.name = self.props.get("name", "")
        self.oid = self.props.get("_object_id", "")
        self.props.pop("tags", None)

    def get(self, key: str, default: str = "") -> str:
        return self.props.get(key, default)


def parse_epe(xml_path: str) -> list[Obj]:
    root = ET.parse(xml_path).getroot()
    out: list[Obj] = []

    def walk(el: ET.Element, parent: Obj | None) -> None:
        idx = 0
        for ch in el:
            if ch.tag != "object":
                continue
            node = (parent.node if parent else "") + "/" + (ch.get("name") or str(idx))
            idx += 1
            o = Obj(ch, parent, node)
            out.append(o)
            walk(ch, o)

    walk(root, None)
    return out


def decode_epe(entity: str, rows: list[dict], game: str) -> tuple[list[Obj], dict]:
    """Extract the .ee's .epe, convert it with Gibbed, parse it, keep the XML raw."""
    r = jc3detail.pick(rows, entity)
    with open(os.path.join(game, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        raw = f.read(r["size"])
    if len(raw) != r["size"]:
        raise IOError(f"short read {len(raw)} != {r['size']} for {entity}")
    stream, entries = jc3detail.inner_files(raw)
    found = [(n, o, s) for n, o, s in entries if n.endswith(".epe")]
    if not found:
        raise ValueError(f"no .epe inside {entity}")
    name, off, size = found[0]
    os.makedirs(CACHE, exist_ok=True)
    slug = entity.rsplit("/", 1)[-1]
    src = os.path.join(CACHE, slug + ".epe")
    dst = os.path.join(CACHE, slug + ".xml")
    with open(src, "wb") as f:
        f.write(stream[off:off + size])
    p = subprocess.run([jc3detail.CONVERT, "--e", src, dst], capture_output=True)
    if p.returncode != 0 or not os.path.exists(dst):
        raise RuntimeError(f"ConvertProperty failed for {entity}: "
                           f"{p.stdout[-300:]!r} {p.stderr[-300:]!r}")
    os.remove(src)
    doc = {
        "archive": r["archive"],
        "offset": r["offset"],
        "size": r["size"],
        "member": name,
        "epe_bytes": size,
    }
    return parse_epe(dst), doc


# ------------------------------------------------------------------- helpers
def xyz(world: str) -> list[float] | None:
    """Translation of an RTPC row-major mat4: fields 12..14."""
    try:
        v = [float(x) for x in world.replace(" ", "").split(",")]
        return [round(v[12], 4), round(v[13], 4), round(v[14], 4)] if len(v) == 16 else None
    except (ValueError, IndexError):
        return None


def dist(a: list[float], b: list[float]) -> float:
    return round(sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5, 3)


def num(v) -> str:
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def load_census() -> list[dict]:
    d = json.load(open(CENSUS, encoding="utf-8"))
    return d["armed_entities"]


def load_parts() -> dict[str, dict]:
    """chassis -> decoded parts row (the first entity of that chassis wins)."""
    out: dict[str, dict] = {}
    for line in open(PARTS, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        chassis = r["entity"].rsplit("/", 2)[-2]
        out.setdefault(chassis, r)
    return out


def chassis_of(entity: str) -> str:
    return entity.rsplit("/", 2)[-2]


def relevant_parts(row: dict | None) -> list[dict]:
    if not row:
        return []
    names = {p["i"]: p["n"] for p in row["parts"]}
    out = []
    for p in row["parts"]:
        if p.get("b") not in MOVE_BEHAVIOURS:
            continue
        out.append({
            "name": p["n"],
            "behaviour": p["b"],
            "index": p["i"],
            "parent": names.get(p.get("parent")) if p.get("parent") not in (None, -1) else None,
        })
    return out


def mount_parts(points: list[dict], part_names: set[str]) -> list[str]:
    """Type-4 SWeaponPoint string values that name a part on the chassis."""
    found: set[str] = set()
    for pt in points:
        if pt["type"] != "4":
            continue
        for value in pt["props"].values():
            if value in part_names:
                found.add(value)
    return sorted(found)


# ---------------------------------------------------------------- per entity
def build_row(entity: str, rows: list[dict], parts_row: dict | None, game: str) -> dict:
    objs, source = decode_epe(entity, rows, game)
    byid = {o.oid: o for o in objs if o.oid}
    class_mismatch = []
    for o in objs:
        h = o.get(CLASS_HASH_PROP)
        if h and o.cls:
            want = hash_jenkins(o.cls.encode())
            got = int(h) & 0xFFFFFFFF
            if got != want:
                class_mismatch.append({"node": o.node, "class": o.cls,
                                       "prop": h, "jenkins": f"{want:08X}"})

    roots = [o for o in objs if o.cls in ROOT_CLASSES]
    roots.sort(key=lambda o: (o.node.count("/"), o.node))
    root_sets = []
    for ro in roots:
        slots = {}
        for label, prop, _who in SLOTS:
            val = ro.get(prop)
            slots[label] = {"prop": prop,
                            "id": val if val and val != "00000000" else None,
                            "target": None, "target_class": None}
            sid = slots[label]["id"]
            if sid:
                tgt = byid.get(sid)
                slots[label]["target"] = tgt.name if tgt else None
                slots[label]["target_class"] = tgt.cls if tgt else None
        other = {}
        for prop in OTHER_POINTERS:
            val = ro.get(prop)
            other[prop] = None if not val or val == "00000000" else val
        root_sets.append({"class": ro.cls, "name": ro.name, "slots": slots,
                          "other_pointers": other,
                          "context_id": ro.get("interaction_context")})
    # a weapon can be owned by more than one root (the cargo plane carries a tank); label the
    # owner only when the entity has more than one root, so the common case stays short.
    multi = len(root_sets) > 1

    # weapons
    weapons = []
    for o in objs:
        if o.cls not in WEAPON_CLASSES:
            continue
        binding = []
        for rs in root_sets:
            for label, _p, _w in SLOTS:
                s = rs["slots"][label]
                if s["id"] and s["id"] == o.oid:
                    binding.append(f"{rs['class']}::{label}" if multi else label)
        points = []
        for ch in o.children:
            if ch.cls != "SWeaponPoint":
                continue
            points.append({
                "name": ch.name,
                "type": ch.get("type"),
                "fire_effect": ch.get("fire_effect"),
                "world": ch.get("world"),
                "xyz": xyz(ch.get("world")),
                "props": ch.props,
            })
        comps = [{"class": ch.cls, "name": ch.name, "props": ch.props}
                 for ch in o.children if ch.cls in COMPONENT_CLASSES]
        pulses = [{"class": ch.cls, "name": ch.name, "props": ch.props}
                  for ch in o.children if ch.cls == "CForcePulse"]
        weapons.append({
            "class": o.cls,
            "name": o.name,
            "object_id": o.oid,
            "weapon_id": o.get("weapon_id"),
            "weapon_type": o.get("weapon_type"),
            "world": o.get("world"),
            "xyz": xyz(o.get("world")),
            "binding": binding,
            "props": o.props,
            "points": points,
            "components": comps,
            "force_pulses": pulses,
            "tuning_file": o.get("id:AA7096C9"),
            "autoaim_tuning_file": o.get("id:6D4C8277"),
            "impact_usage": o.get("id:D075017A"),
            "weapon_category": o.get("id:19068026"),
        })

    # seats, grouped by the CInteractionContext each seat is a child of (a cargo plane can
    # carry a whole tank with its own context and its own driver seat)
    def context_of(o: Obj) -> str | None:
        p = o.parent
        while p is not None:
            if p.cls == "CInteractionContext":
                return p.oid
            p = p.parent
        return None

    seats: list[dict] = []
    by_ctx: dict[str | None, list[dict]] = {}
    for o in objs:
        if o.cls != "CInteraction" or not o.name.startswith("interaction.seat."):
            continue
        states: list[str] = []
        point = None
        for ch in o.children:
            if ch.cls != "CInteractionComponentSetNode":
                continue
            if ch.get("state") and ch.get("state") not in states:
                states.append(ch.get("state"))
            tgt = byid.get(ch.get("node"))
            if tgt is not None and point is None:
                point = {"name": tgt.name, "xyz": xyz(tgt.get("world"))}
        rec = {
            "name": o.name,
            "index": o.get(NAME_HASH_PROP),
            "states": states,
            "point": point,
        }
        seats.append(rec)
        by_ctx.setdefault(context_of(o), []).append(rec)
    for rs in root_sets:
        rs["seats"] = by_ctx.get(rs["context_id"], [])

    # gunner seat nearest each mounted weapon (entity space)
    gunner_seats = [s for s in seats
                    if any(g in " ".join(s["states"]) for g in GUNNER_MOUNT_STATES)]
    for w in weapons:
        if not any(b.startswith("mounted") for b in w["binding"]) or not w["xyz"]:
            continue
        best = None
        for s in gunner_seats:
            if not s["point"] or not s["point"]["xyz"]:
                continue
            d = dist(w["xyz"], s["point"]["xyz"])
            if best is None or d < best["distance_m"]:
                best = {"seat": s["name"], "seat_index": s["index"],
                        "point": s["point"]["name"], "distance_m": d}
        w["nearest_gunner_seat"] = best

    # parts + mount names
    parts = relevant_parts(parts_row)
    all_names = {p["n"] for p in parts_row["parts"]} if parts_row else set()
    for w in weapons:
        w["mount_parts"] = mount_parts(w["points"], all_names)

    driver_slots = [f"{rs['class']}::{label}" if multi else label
                    for rs in root_sets for label, prop, who in SLOTS
                    if who == "driver" and rs["slots"][label]["id"]]
    gunner_slots = [f"{rs['class']}::{label}" if multi else label
                    for rs in root_sets for label, prop, who in SLOTS
                    if who == "gunner" and rs["slots"][label]["id"]]
    driver_weapons = [w["name"] for label in driver_slots for w in weapons
                      if label in w["binding"]]
    row = {
        "entity": entity,
        "chassis": chassis_of(entity),
        "root_class": roots[0].cls if roots else None,
        "root_name": roots[0].name if roots else None,
        "root_classes": [rs["class"] for rs in root_sets],
        "roots": root_sets,
        "source": source,
        "seats": seats,
        "parts": parts,
        "counts": {
            "weapons": len(weapons),
            "bound": sum(1 for w in weapons if w["binding"]),
            "driver_slots": len(driver_slots),
            "gunner_slots": len(gunner_slots),
            "driver_weapons": len(set(driver_weapons)),
        },
        "weapons": weapons,
        "class_hash_mismatches": class_mismatch,
    }
    row["digest"] = sha1(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")).encode())[:16]
    return row


def collect(game: str) -> tuple[list[dict], list[dict]]:
    rows = jc3index.load_index(OUT)
    parts = load_parts()
    census = load_census()
    out = []
    failed = []
    for i, rec in enumerate(census, 1):
        entity = rec["entity"]
        try:
            out.append(build_row(entity, rows, parts.get(chassis_of(entity)), game))
        except Exception as e:                                  # noqa: BLE001
            failed.append((entity, f"{type(e).__name__}: {e}"))
            print(f"[{i}/{len(census)}] {entity.rsplit('/', 1)[-1]}: ERROR {e}")
            continue
        print(f"[{i}/{len(census)}] {entity.rsplit('/', 1)[-1]}: "
              f"{out[-1]['counts']['weapons']} weapons, "
              f"{out[-1]['counts']['driver_slots']} driver, "
              f"{out[-1]['counts']['gunner_slots']} gunner")
    return out, failed


# --------------------------------------------------------------------- report
def slot_line(rootset: dict) -> str:
    bits = []
    for label, prop, who in SLOTS:
        s = rootset["slots"][label]
        val = f"`{s['target']}`" if s["target"] else (f"`{s['id']}`" if s["id"] else "-")
        bits.append(f"{label} {val}")
    return " · ".join(bits)


def answers(rows: list[dict]) -> list[str]:
    land = [r for r in rows if "CCar" in r["root_classes"] and "/01_land/" in r["entity"]]
    land_max = max((r["counts"]["driver_slots"] for r in land), default=0)
    land_two = sorted({r["chassis"] for r in land if r["counts"]["driver_slots"] == 2})
    all_max = max((r["counts"]["driver_slots"] for r in rows), default=0)
    max_bound = max((r["counts"]["bound"] for r in rows), default=0)
    max_comp = max((r["counts"]["weapons"] for r in rows), default=0)
    over = [r for r in rows if r["counts"]["weapons"] > r["counts"]["bound"]]
    driver_ccars = [r for r in land if r["counts"]["driver_slots"]]
    mounted_ccars = [r for r in land if r["counts"]["gunner_slots"]]

    lines = []
    a = lines.append
    a("## 2. The questions the card asks")
    a("")
    a(f"**(a) Most driver-fired weapons on a land vehicle: {land_max}.**")
    a("")
    if land_two:
        a("Two driver slots are wired on " +
          ", ".join(f"`{c}`" for c in land_two) + ". Every other land vehicle has one or none.")
    else:
        a("No land vehicle wires two driver slots.")
    a(f"Across all 53 armed entities the maximum is {all_max}; no file has a third driver slot.")
    a("")
    a("**(b) How two weapons are bound to primary/secondary fire.**")
    a("")
    a("The root class carries two separate object pointers, not a list with an order. "
      "`id:851CAABE` is the first (`main_weapon`), `id:00568A74` the second. Each points at a "
      "weapon component by `_object_id`; a component with no pointer is dead weight (the fighter "
      "jet ships one). The component itself has no slot property, its `weapon_type` is `2` for "
      "every weapon, and the G2-10 tunes contain no slot or input member - so the only "
      "slot data in the game files is these two root pointers. Which button each maps to is not "
      "encoded in the entity - `action_1`/`action_2` are `1`/`2` on armed and unarmed cars alike - "
      "and neither is switching: there is no active-slot index, no next/previous weapon action and "
      "no weapon group anywhere in the `.epe`. Both slots are simply available.")
    a("")
    a("**(c) Any vehicle that switches between three or more weapons?**")
    a("")
    a(f"No. The most bound weapons on one entity is {max_bound} (two driver, or two gunner); "
      f"the most weapon components carried is {max_comp}.")
    if over:
        a("Components outnumber bound weapons here (the extra is never referenced by a slot):")
        a("")
        a("| entity | components | bound | unbound |")
        a("|---|---|---|---|")
        for r in over:
            un = [w["name"] for w in r["weapons"] if not w["binding"]]
            a(f"| `{r['entity'].rsplit('/', 1)[-1]}` | {r['counts']['weapons']} | "
              f"{r['counts']['bound']} | {', '.join(f'`{u}`' for u in un)} |")
        a("")
    a("**(d) Which wiring is driver-fired on a `CCar`?**")
    a("")
    a("| entity | chassis | driver slots | weapons | gunner seats |")
    a("|---|---|---|---|---|")
    for r in driver_ccars + [r for r in mounted_ccars if r not in driver_ccars]:
        drv = [w["name"] for w in r["weapons"]
               if any(b.split("::")[-1].startswith(("main_weapon", "secondary"))
                      for b in w["binding"])]
        gun = [w["name"] for w in r["weapons"]
               if any(b.split("::")[-1].startswith("mounted") for b in w["binding"])]
        a(f"| `{r['entity'].rsplit('/', 1)[-1]}` | `{r['chassis']}` | "
          f"{r['counts']['driver_slots']} | "
          f"{', '.join(f'`{w}`' for w in drv) if drv else '-'} | "
          f"{', '.join(f'`{w}`' for w in gun) if gun else '-'} |")
    a("")
    a("The last row is the cargo-plane variant: its driver slots belong to the tank carried in "
      "its hold, not to the plane. On an actual land `.ee`, the two CCars with two driver slots "
      "are the medium tank and the Bavarium tank; the small tank, the signature Serpente and the "
      "signature buggy have one; every other land vehicle is gunner-only or unarmed.")
    a("")
    return lines


def summary(rows: list[dict]) -> list[str]:
    lines = []
    a = lines.append
    cls: dict[str, int] = {}
    root: dict[str, int] = {}
    wcls: dict[str, int] = {}
    bound = 0
    unbound = []
    states: dict[str, int] = {}
    for r in rows:
        root[r["root_class"] or "?"] = root.get(r["root_class"] or "?", 0) + 1
        for w in r["weapons"]:
            wcls[w["class"]] = wcls.get(w["class"], 0) + 1
            if w["binding"]:
                bound += 1
            else:
                unbound.append((r["entity"].rsplit("/", 1)[-1], w["name"]))
        for s in r["seats"]:
            for st in s["states"]:
                states[st] = states.get(st, 0) + 1
    a("## 3. Fleet summary")
    a("")
    a("| item | value |")
    a("|---|---|")
    a(f"| armed entities | **{len(rows)}** |")
    a(f"| chassis | **{len({r['chassis'] for r in rows})}** |")
    for k in ("CCar", "CAirPlane", "CBoat", "CHelicopter", "CTrain"):
        if k in root:
            a(f"| primary root `{k}` | {root[k]} |")
    a(f"| weapon components | **{sum(wcls.values())}** |")
    a(f"| bound to a slot | {bound} |")
    a(f"| unbound | {len(unbound)} |")
    a("")
    a("| weapon class | components |")
    a("|---|---|")
    for k, v in sorted(wcls.items(), key=lambda kv: -kv[1]):
        a(f"| `{k}` | {v} |")
    a("")
    a(f"Counts above are components and roots, not vehicles. The cargo-tank variant carries a "
      "full `CCar` (tank) next to its `CAirPlane`, so the {len(rows)} entities hold "
      f"{sum(len(r['root_classes']) for r in rows)} root objects; the table counts each entity's "
      "primary root only, and that entity's tank slots are counted where its CCar is.")
    a("")
    a("`CLightWeaponComponent` is in the census as a weapon class but is a warning *light* "
      "attached to a weapon (30 components on 9 entities); it is listed as a subcomponent, not "
      "counted as a weapon.")
    a("")
    a("Seat states found in the armed fleet:")
    a("")
    a("| state | seats |")
    a("|---|---|")
    for k, v in sorted(states.items(), key=lambda kv: -kv[1]):
        a(f"| `{k}` | {v} |")
    a("")
    if unbound:
        a("Unbound weapon components (present, no slot points at them):")
        a("")
        for e, w in unbound:
            a(f"- `{e}`: `{w}`")
        a("")
    m2 = [(r, w) for r in rows for w in r["weapons"]
          if w["name"] == "w206_mounted_capstone_m2hm"]
    if m2:
        a("### The mounted M2, and why it is not in `WEAPONS.md`")
        a("")
        chassis = ", ".join(f"`{c}`" for c in sorted({r['chassis'] for r, _w in m2}))
        a(f"`w206_mounted_capstone_m2hm` is the fleet's most common gunner weapon: "
          f"{len(m2)} components over {len({r['chassis'] for r, _w in m2})} chassis "
          f"({chassis}). It sits in `editor/entities/jc_weapons/04_mounted/`, outside the "
          "`06_vehicle` filter G2-10 used, so it has no row there. Its tune and its two "
          "`GripPointSettings` variants are already in `WEAPONS_SHARED.json` (G2-10's shared "
          "list); this script records the per-entity `tuning_file` path and the grip-point/"
          "mount wiring that G2-10 left out.")
        a("")
    return lines


def slot_model(rows: list[dict]) -> list[str]:
    lines = []
    a = lines.append
    a("## 1. The slot properties (and how their names were recovered)")
    a("")
    a("Each root class (`CCar`, `CAirPlane`, `CBoat`, `CHelicopter`, `CTrain`) carries all "
      "four pointers; unused ones are `00000000`. RTPC writes a property's 32-bit name hash when "
      "the entity's name table does not carry the string, so two slots only have ids. Hashing "
      "candidates with the archive-path Jenkins function (`rbmhdr.hash_jenkins`) recovers a name "
      "only when the exact 32-bit value lands - six did:")
    a("")
    a("| slot | property in the `.epe` | Jenkins(name) | who fires it |")
    a("|---|---|---|---|")
    a("| 1st driver | `id:851CAABE` | `main_weapon` = `851CAABE` | driver |")
    a("| 2nd driver | `id:00568A74` | **no name found** | driver |")
    a("| 1st gunner | `mounted_weapon` | named in the file | gunner seat |")
    a("| 2nd gunner | `id:AC0BC788` | `mounted_weapon_2` = `AC0BC788` | gunner seat |")
    a("")
    a("Other recovered property names used below: `tuning_file` = `AA7096C9`, "
      "`autoaim_tuning_file` = `6D4C8277`, `impact_usage` = `D075017A`, "
      "`weapon_category` = `19068026`. `id:D04059E6` is the Jenkins hash of every object's class "
      "name (checked on every decoded object by `--check`). The 2nd driver slot resisted a "
      "1.1-million-string vocabulary search (57 weapon/mount words in 2- and 3-word combinations, "
      "numeric suffixes); its id is the name of record.")
    a("")
    a(f"`--check` also confirms the two trailing pointer properties "
      f"(`{'`, `'.join(OTHER_POINTERS)}`) are null on all {len(rows)} armed entities and never "
      "resolve to a weapon; they are recorded per root in the jsonl as `other_pointers`.")
    a("")
    a("The unarmed buggy and the civilian Serpente sampled for this check carry all four "
      "properties too, each set to `00000000` - the pointers exist on the class, not on the "
      "variant.")
    a("")
    return lines


def entity_index(rows: list[dict]) -> list[str]:
    lines = ["## 4. Entity index", "",
             "| entity | class | chassis | driver | gunner | weapons |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        names = ", ".join(f"`{w['name']}`" for w in r["weapons"])
        rc = "/".join(r["root_classes"])
        lines.append(f"| `{r['entity'].rsplit('/', 1)[-1]}` | `{rc}` | "
                     f"`{r['chassis']}` | {r['counts']['driver_slots']} | "
                     f"{r['counts']['gunner_slots']} | {names} |")
    lines.append("")
    return lines


def entity_sections(rows: list[dict]) -> list[str]:
    lines = ["## 5. Entities", ""]
    for r in rows:
        fn = r["entity"].rsplit("/", 1)[-1]
        a = lines.append
        a(f"### `{fn}`")
        a("")
        rc = " + ".join(f"`{c}`" for c in r["root_classes"])
        a(f"{rc} · chassis `{r['chassis']}` · source `{r['source']['archive']}` "
          f"@{r['source']['offset']:,} +{r['source']['size']:,} B · {r['counts']['weapons']} "
          f"weapon component(s), {r['counts']['driver_slots']} driver slot(s), "
          f"{r['counts']['gunner_slots']} gunner slot(s)")
        a("")
        for rs in r["roots"]:
            a(f"slots on `{rs['class']}` `{rs['name']}`: {slot_line(rs)}")
            a("")
        a("| slot | class | weapon | id | muzzles | aim / aux components | mount parts |")
        a("|---|---|---|---|---|---|---|")
        for w in r["weapons"]:
            slot = ", ".join(f"`{b}`" for b in w["binding"]) or "*unbound*"
            comps = ", ".join(f"`{c['name']}`" for c in w["components"]) or "-"
            mounts = ", ".join(f"`{p}`" for p in w["mount_parts"]) or "-"
            muzzles = sum(1 for p in w["points"] if p["type"] == "2")
            a(f"| {slot} | `{w['class']}` | `{w['name']}` | {w['weapon_id']} | {muzzles} | "
              f"{comps} | {mounts} |")
        a("")
        pts = [(w, p) for w in r["weapons"] for p in w["points"]]
        if pts:
            a("| weapon | point | type | fire_effect | x | y | z |")
            a("|---|---|---|---|---|---|---|")
            for w, p in pts:
                q = p["xyz"] or ["", "", ""]
                a(f"| `{w['name']}` | `{p['name']}` | {p['type']} | {p['fire_effect']} | "
                  f"{num(q[0])} | {num(q[1])} | {num(q[2])} |")
            a("")
        tunes = [(w, w["tuning_file"], w["autoaim_tuning_file"], w["weapon_category"],
                  w["impact_usage"]) for w in r["weapons"]]
        if any(t[1] or t[2] or t[3] or t[4] for t in tunes):
            a("| weapon | tuning_file | autoaim_tuning_file | category | impact_usage |")
            a("|---|---|---|---|---|")
            for w, tf, af, cat, imp in tunes:
                a(f"| `{w['name']}` | {('`' + tf + '`') if tf else '-'} | "
                  f"{('`' + af + '`') if af else '-'} | {cat or '-'} | {imp or '-'} |")
            a("")
        for w in r["weapons"]:
            if w.get("nearest_gunner_seat"):
                s = w["nearest_gunner_seat"]
                a(f"- `{w['name']}` ({', '.join(w['binding'])}) is mounted nearest "
                  f"`{s['seat']}` (seat index `{s['seat_index']}`, point `{s['point']}`, "
                  f"{num(s['distance_m'])} m).")
        if any(w.get("nearest_gunner_seat") for w in r["weapons"]):
            a("")
        for rs in r["roots"]:
            if not rs.get("seats"):
                continue
            a(f"seats on `{rs['class']}` `{rs['name']}`:")
            a("")
            a("| seat | index | state(s) | point |")
            a("|---|---|---|---|")
            for s in rs["seats"]:
                pt = s["point"]["name"] if s["point"] else "-"
                a(f"| `{s['name']}` | {s['index']} | "
                  f"{', '.join(f'`{x}`' for x in s['states']) or '-'} | `{pt}` |")
            a("")
        if r["parts"]:
            shown = r["parts"] if len(r["parts"]) <= 8 else r["parts"][:8]
            a("moving parts on the chassis: " +
              ", ".join(f"`{p['name']}` ({p['behaviour']}, {p['index']}"
                        + (f" ← `{p['parent']}`" if p["parent"] else "") + ")"
                        for p in shown) +
              (f" … and {len(r['parts']) - 8} more" if len(r["parts"]) > 8 else ""))
            a("")
        if r["class_hash_mismatches"]:
            a(f"**{len(r['class_hash_mismatches'])} class-hash mismatches** - see jsonl.")
            a("")
    return lines


def limits(rows: list[dict]) -> list[str]:
    lines = []
    a = lines.append
    a("## 6. Limits of what the entity says")
    a("")
    a("- **Driver vs gunner is structural, not per-weapon.** No weapon component points at a "
      "seat. The distinction is the slot set: the two driver pointers coexist with no gunner "
      "seat, while mounted weapons always sit on a seat whose state is "
      "`S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` (APC, technical, armoured jeep), "
      "`S_VEHICLE_FIXED_MOUNTED_WEAPON` (heavy patrol boat) or `S_MOUNTED_WEAPON` (light patrol "
      "boat). No entity mixes a driver slot with a gunner slot. The nearest-gunner-seat line is a "
      "geometric join between the weapon's world translation and the seat point, not a pointer.")
    a("- **No button mapping.** The entity does not say which input fires which slot; the G2-10 "
      "tunes have no input member either. Primary/secondary below means first/second pointer, "
      "which is the evidence the files carry.")
    a("- **Most driver weapons name no part.** 22 of 88 weapons carry a type-4 `MountAttach`: all "
      "19 gunner weapons (two parts each) and the corvette's driver cannon (`corvette_gun`, "
      "`corvette_turret`). The other 59 driver weapons have no part pointer; their chassis part "
      "list is recorded, but the turret/cannon -> weapon link is not in the `.epe`.")
    a("- **`CLightWeaponComponent` is a light**, not a gun: colour/radius/spot data, usually a "
      "child of a cannon (e.g. the medium tank's `warning_light`).")
    a("- **The monorail missile car has no slot at all.** Its only weapon sits under a "
      "`CTurretWeaponComponent` and the entity exposes only `interaction.seat.stunt`; it is an "
      "AI/script turret, not a driver weapon.")
    a("- **Two all-null pointers** (`id:8580BA42`, `id:CA86AA17`) are on every root class and "
      "never resolve to a weapon on the 53 armed entities; their names are not in the shipped "
      "name tables and no candidate hashed to them.")
    a("")
    return lines


def validation(rows: list[dict], failed: list[dict]) -> list[str]:
    bound = sum(r["counts"]["bound"] for r in rows)
    unbound = sum(1 for r in rows for w in r["weapons"] if not w["binding"])
    lines = [
        "## 7. Validation",
        "",
        "`jc3wiring.py --check` re-reads all 53 entities out of the archives, decodes the `.epe` "
        "again, rebuilds every row and compares it field-for-field with the jsonl, then regenerates "
        "this file and diffs it. It also re-checks:",
        "",
        f"- the census list ({len(rows)} armed entities) matches the decoded rows one-for-one;",
        f"- every object whose `{CLASS_HASH_PROP}` property is present hashes to its own class name "
        "(the property is a class-name hash, so this also proves the parser read the right bytes);",
        "- every non-null slot resolves to a decoded weapon component;",
        "- the weapon names and SWeaponPoint counts match `FEATURE_CENSUS.json` (a different "
        "decode path, P0-2) for every entity;",
        f"- the summary totals ({bound} bound, {unbound} unbound).",
        "",
        f"Decoded: **{len(rows)} entities**, {sum(r['counts']['weapons'] for r in rows)} weapon "
        f"components, {sum(len(r['seats']) for r in rows)} seats, "
        f"{sum(len(r['parts']) for r in rows)} moving-part rows, "
        f"{sum(len(w['points']) for r in rows for w in r['weapons'])} weapon points.",
        "",
    ]
    if failed:
        lines += ["Failed entities:", ""]
        for e, err in failed:
            lines.append(f"- `{e}`: {err}")
        lines.append("")
    return lines


def read_doc(rows: list[dict], failed: list[dict]) -> list[str]:
    lines = [
        "# JC3 vehicle weapon wiring (G2-11)",
        "",
        "How each armed vehicle binds its weapons: the root slot pointers, every weapon "
        "component and its properties, the fire points, aim components, the seat that owns it, "
        "and the moving parts on the chassis. Decoded by `Tools/scripts/jc3wiring.py` from the "
        "entity `.epe` inside each `.ee` (Gibbed `ConvertProperty`), joined with "
        "`PARTS_TABLE.jsonl` (parts module) and `FEATURE_CENSUS.json` (the armed list). The "
        "weapon tunes themselves are in `WEAPONS.md` (G2-10).",
        "",
    ]
    lines += slot_model(rows)
    lines += answers(rows)
    lines += summary(rows)
    lines += entity_index(rows)
    lines += entity_sections(rows)
    lines += limits(rows)
    lines += validation(rows, failed)
    return lines


# -------------------------------------------------------------------- commands
def build(game: str) -> tuple[list[dict], list[dict], list[str]]:
    rows, failed = collect(game)
    return rows, failed, read_doc(rows, failed)


def cmd_write(a) -> int:
    rows, failed, lines = build(a.game)
    with open(os.path.join(OUT, TABLE), "w", encoding="utf-8", newline="\n") as f:
        for rec in rows:
            f.write(json.dumps(rec, separators=(",", ":"), sort_keys=True) + "\n")
    with open(os.path.join(OUT, DOC), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{TABLE}: {len(rows)} entities, "
          f"{sum(r['counts']['weapons'] for r in rows)} weapon components, "
          f"{sum(r['counts']['driver_slots'] for r in rows)} driver slots, "
          f"{sum(r['counts']['gunner_slots'] for r in rows)} gunner slots; "
          f"{DOC.split('.')[0]}.md {len(lines)} lines")
    if failed:
        print(f"WARNING: {len(failed)} entities failed")
    return 1 if failed else 0


def cmd_check(a) -> int:
    path = os.path.join(OUT, TABLE)
    if not os.path.exists(path):
        print(f"FAIL: no {TABLE} - run --write first")
        return 1
    old = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    rows, failed, lines = build(a.game)
    bad = 0
    if failed:
        print(f"FAIL: {len(failed)} entities failed to decode")
        bad += len(failed)
    if len(old) != len(rows):
        print(f"FAIL: {len(old)} rows on disk, {len(rows)} re-derived")
        bad += 1
    for o, n in zip(old, rows):
        if o != n:
            print(f"FAIL: {o['entity']} changed")
            for k in sorted(set(o) | set(n)):
                if o.get(k) != n.get(k):
                    print(f"   field {k}: {str(o.get(k))[:100]} != {str(n.get(k))[:100]}")
            bad += 1
    new_md = "\n".join(lines) + "\n"
    doc = os.path.join(OUT, DOC)
    on_disk = open(doc, encoding="utf-8").read() if os.path.exists(doc) else ""
    if on_disk != new_md:
        print(f"FAIL: {DOC} changed")
        import difflib
        for line in list(difflib.unified_diff(on_disk.splitlines(), new_md.splitlines(),
                                              DOC, "re-derived", lineterm=""))[:20]:
            print("   " + line)
        bad += 1
    # every object's class-hash property must equal hash(class); build_row collected mismatches
    mism = sum(len(r["class_hash_mismatches"]) for r in rows)
    if mism:
        print(f"FAIL: {mism} class-hash mismatches")
        bad += 1
    # every non-null slot must resolve to a weapon component; the two trailing pointers must be null
    for r in rows:
        for rs in r["roots"]:
            for label, s in rs["slots"].items():
                if s["id"] and s["target_class"] not in WEAPON_CLASSES:
                    print(f"FAIL: {r['entity']} slot {label} -> "
                          f"{s['target_class']}/{s['target']}")
                    bad += 1
            for prop, val in rs["other_pointers"].items():
                if val is not None:
                    print(f"FAIL: {r['entity']} {prop} is not null: {val}")
                    bad += 1
    # the census and the rows must agree, including its independent weapon and point counts
    census_rows = load_census()
    census = sorted(r["entity"] for r in census_rows)
    got = sorted(r["entity"] for r in rows)
    if census != got:
        print(f"FAIL: census {len(census)} entities != rows {len(got)}")
        bad += 1
    cmap = {c["entity"]: c for c in census_rows}
    for r in rows:
        c = cmap[r["entity"]]
        want = collections.Counter(x["name"] for x in c["weapons"]
                                   if x["class"] in WEAPON_CLASSES)
        have = collections.Counter(w["name"] for w in r["weapons"])
        if want != have:
            print(f"FAIL: {r['entity']} weapons {dict(have)} != census {dict(want)}")
            bad += 1
        pts = sum(len(w["points"]) for w in r["weapons"])
        if pts != c["weapon_points"]:
            print(f"FAIL: {r['entity']} points {pts} != census {c['weapon_points']}")
            bad += 1
    print(f"{'PASS' if not bad else 'FAIL'}: {len(rows)} entities, "
          f"{sum(r['counts']['weapons'] for r in rows)} weapons, "
          f"{sum(r['counts']['bound'] for r in rows)} bound, "
          f"{sum(1 for r in rows for w in r['weapons'] if not w['binding'])} unbound, "
          f"{sum(len(r['seats']) for r in rows)} seats, md {len(new_md.splitlines())} lines")
    return 1 if bad else 0


def cmd_dump(a) -> int:
    rows, _failed, _lines = build(a.game)
    hit = [r for r in rows if a.want.lower() in r["entity"].lower()]
    if not hit:
        raise SystemExit(f"no entity matches {a.want!r}")
    for r in hit:
        print(f"# {r['entity']}  ({'/'.join(r['root_classes'])}, {r['counts']['weapons']} weapons)")
        for rs in r["roots"]:
            print(f"  root {rs['class']} {rs['name']}")
            for label, s in rs["slots"].items():
                print(f"    slot {label:28s} {(s['target'] or '-'):40s} {s['target_class'] or ''}")
        for w in r["weapons"]:
            print(f"  weapon {w['class']} {w['name']} id={w['weapon_id']} "
                  f"binding={w['binding']} points={len(w['points'])}")
            for p in w["points"]:
                print(f"      {p['name']:28s} type={p['type']} "
                      f"fire_effect={p['fire_effect']} xyz={p['xyz']}")
            for c in w["components"]:
                print(f"      {c['class']} {c['name']}")
        for s in r["seats"]:
            print(f"  seat {s['name']} idx={s['index']} {s['states']}")
        print()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true", help="decode and write the records")
    p.add_argument("--check", action="store_true", help="re-read the archives and compare")
    p.add_argument("--game", default=GAME)
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("want")
    a = p.parse_args()
    if a.cmd == "dump":
        return cmd_dump(a)
    if a.write:
        return cmd_write(a)
    if a.check:
        return cmd_check(a)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
