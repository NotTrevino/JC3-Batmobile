#!/usr/bin/env python
"""jc3turret.py - G2-13: how a JC3 vehicle turret and cannon actually move.

A turret in Just Cause 3 is not a special object. It is two ordinary parts - one
`Turret` behaviour part (yaw) and one `Cannon` behaviour part (pitch) - joined by
`hkpLimitedHingeConstraintData` objects in the vehicle's `.physicsc`. The weapon's
`SWeaponPoint` names both parts, and the part's `constraint_index` selects the hinge.

This script reads, for each sampled vehicle:

  parts       the `*_vehicle_parts.vmodc` (behaviour, parent, constraint_index, centroid)
  constraints the `.physicsc` packfile: every constraint object in file order, with the
              limited-hinge pivot, axis and angle limits
  weapon      the `SWeaponPoint` props `id:80201E4D` (yaw part) and `id:5C19E7E0`
              (pitch part), the weapon binding and the fire-point translation
  aim         `STargetPoint` objects and the weapon's autoaim tune values

It also censuses the two point properties across all 53 armed entities, and decodes
`aim_part_constraints` from every parts module in the local cache - that array is a
suspension linkage (source part aims at wheel/brake drum/chassis), not a turret.

Usage:
  python jc3turret.py --write     # decode and write TURRET.json + TURRET.md
  python jc3turret.py --check     # re-read the archives, rebuild, compare both files
  python jc3turret.py dump samples|census|tune

Limits: the limited-hinge layout is decoded from the object bytes (+0x30 basis, +0x60
pivot, +0xFC min and +0x100 max angle in radians). Ragdoll constraints are counted but
not decoded. Nothing here writes a game file; all reads are read-only.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3hkx  # noqa: E402
import jc3index  # noqa: E402
import jc3wiring  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
JSON_NAME = "TURRET.json"
MD_NAME = "TURRET.md"
WIRING = os.path.join(OUT, "WEAPON_WIRING.jsonl")
PARTS = os.path.join(OUT, "PARTS_TABLE.jsonl")
SHARED = os.path.join(OUT, "WEAPONS_SHARED.json")

V = "editor/entities/jc_vehicles/01_land"
SAMPLES = (
    ("mediumtank", "v0201 medium tank",
     f"{V}/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee"),
    ("bavariumtank", "v0202 Bavarium tank",
     f"{V}/v0202_car_capstone_bavariumtank/v0202_car_capstone_bavariumtank_military_01.ee"),
    ("smalltank", "v0603 small tank",
     f"{V}/v0603_car_urga_smalltank/v0603_car_urga_smalltank_military_01.ee"),
    ("apc", "v0200 APC",
     f"{V}/v0200_car_capstone_apc/v0200_car_capstone_apc_military_01.ee"),
    ("armoredjeep", "v0600 armoured jeep",
     f"{V}/v0600_car_urga_armoredjeep/v0600_car_urga_armoredjeep_military_01.ee"),
    ("technicaljeep", "v0504 technical",
     f"{V}/v0504_car_solar_technicaljeep/v0504_car_solar_technicaljeep_rebel_machinegun.ee"),
    ("sportsmuscle", "v0300 Serpente (donor)",
     f"{V}/v0300_car_kensington_sportsmuscle/"
     "v0300_car_kensington_sportsmuscle_signature_preorder.ee"),
    ("buggy", "v0604 buggy",
     f"{V}/v0604_car_urga_buggy/v0604_car_urga_buggy_signature_preorder.ee"),
)
BEHAVIOURS = ("Turret", "Cannon", "GatlingGun", "MissileHatch")
POINT_YAW = "id:80201E4D"
POINT_PITCH = "id:5C19E7E0"
LIMITED = "hkpLimitedHingeConstraintData"


# ------------------------------------------------------------------ readers
def load(rows_path: str, name: str) -> list[dict]:
    rows = []
    with open(os.path.join(OUT, rows_path), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def entity_parts(ee: str, rows: list[dict]) -> tuple[list[dict], str]:
    r = jc3detail.pick(rows, ee)
    blob = jc3grab.read_entry(r, GAME)
    stream, entries = jc3detail.inner_files(blob)
    hit = next((e for e in entries if e[0].endswith("_vehicle_parts.vmodc")), None)
    if hit is None:
        raise ValueError(f"no parts module in {ee}")
    return jc3adf.parts(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]])), os.path.basename(hit[0])


def constraints_of(ee: str, rows: list[dict]) -> list[dict]:
    phys = jc3hkx.physicsc_of(ee, rows, GAME)
    if not phys:
        return []
    pf = jc3hkx.Packfile(phys[0][1])
    objs = sorted((o for o in pf.objects if "Constraint" in o.cls), key=lambda o: o.offset)
    out = []
    for i, o in enumerate(objs):
        rec = {"i": i, "class": o.cls, "size": pf.extents[o.offset]}
        if o.cls == LIMITED:
            raw = pf.raw(o.offset, pf.extents[o.offset])
            axis = struct.unpack_from("<4f", raw, 0x30)
            pivot = struct.unpack_from("<4f", raw, 0x60)
            lo, hi = struct.unpack_from("<2f", raw, 0xFC)
            rec.update({
                "pivot": [round(pivot[0], 4), round(pivot[1], 4), round(pivot[2], 4)],
                "axis": [round(axis[0], 4), round(axis[1], 4), round(axis[2], 4)],
                "min_rad": round(lo, 6), "max_rad": round(hi, 6),
                "min_deg": round(lo * 57.29577951308232, 3),
                "max_deg": round(hi * 57.29577951308232, 3),
            })
        out.append(rec)
    return out


def aim_objects(ee: str, rows: list[dict]) -> list[dict]:
    """`STargetPoint` / `CAimPOIWeaponComponent` with the translation of their `world` matrix."""
    objs, _doc = jc3wiring.decode_epe(ee, rows, GAME)
    out = []
    for o in objs:
        if o.cls not in ("STargetPoint", "CAimPOIWeaponComponent"):
            continue
        w = o.get("world")
        xyz = None
        if w:
            vals = [v.strip() for v in w.replace(",", " ").split()]
            if len(vals) == 16:
                xyz = [round(float(v), 4) for v in vals[12:15]]
        out.append({"class": o.cls, "name": o.name, "node": o.node,
                    "min_aim_distance": o.get("min_aim_distance") or None, "xyz": xyz,
                    "unnamed": {k: v for k, v in o.props.items() if k.startswith("id:")}})
    return out


def is_identity(m: list) -> bool:
    want = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    return [float(x) for x in m] == [float(x) for x in want]


def mount_path(parts: dict[int, dict], p: dict) -> list[dict]:
    """A turret part's ancestors up to the body: e.g. body -> mount base -> turret."""
    chain, cur, seen = [], p, set()
    while cur is not None and cur["part_index"] not in seen:
        seen.add(cur["part_index"])
        chain.append({"part": cur["name"], "index": cur["part_index"],
                      "behavior": cur["behavior"] or None})
        parent = cur.get("parent_part_index")
        cur = parts.get(parent) if isinstance(parent, int) and parent >= 0 else None
    return list(reversed(chain))


def weapon_points(row: dict) -> list[dict]:
    """Every fire point that names a yaw or pitch part."""
    out = []
    for w in row.get("weapons", []):
        for p in w.get("points", []):
            props = p.get("props", {})
            yaw, pitch = props.get(POINT_YAW), props.get(POINT_PITCH)
            if not yaw and not pitch:
                continue
            out.append({
                "weapon": w.get("name"), "class": w.get("class"),
                "binding": w.get("binding") or [],
                "point": p.get("name"), "yaw": yaw, "pitch": pitch,
                "xyz": p.get("xyz"),
                "autoaim": w.get("autoaim_tuning_file"),
            })
    return out


# ------------------------------------------------------------------- build
def build() -> dict:
    rows = jc3index.load_index(OUT)
    wiring = {r["entity"]: r for r in load("WEAPON_WIRING.jsonl", "")}
    table = {r["entity"]: r for r in load("PARTS_TABLE.jsonl", "")}
    if not wiring or not table:
        raise SystemExit("run jc3wiring.py --write and jc3parts.py build first")
    samples = []
    for tag, label, ee in SAMPLES:
        parts, module = entity_parts(ee, rows)
        cons = constraints_of(ee, rows)
        parts_by_index = {p["part_index"]: p for p in parts}
        by_idx = {}
        for p in parts:
            ci = p.get("constraint_index")
            if isinstance(ci, int) and ci >= 0:
                by_idx.setdefault(ci, []).append(p)
        chain = []
        for i, c in sorted(by_idx.items()):
            for p in sorted(by_idx[i], key=lambda x: x["part_index"]):
                rec = {
                    "part": p["name"], "index": p["part_index"],
                    "behavior": p["behavior"], "damage_type": p["damage_type"],
                    "parent": p["parent_part_index"],
                    "centroid": [round(x, 4) for x in p["centroid"][:3]],
                    "constraint": i,
                    "identity_offset": is_identity(p["parent_space_offset"]),
                }
                if 0 <= i < len(cons):
                    rec["hinge"] = cons[i]
                chain.append(rec)
        sample = {
            "tag": tag, "label": label, "entity": ee,
            "parts": len(parts), "parts_module": module,
            "constraint_classes": {k: sum(1 for c in cons if c["class"] == k)
                                   for k in sorted({c["class"] for c in cons})},
            "constraints": cons,
            "constrained_parts": sorted(chain, key=lambda x: (x["behavior"] or "", x["index"])),
            "weapons": weapon_points(wiring[ee]),
            "mount_paths": [{"of": p["name"], "path": mount_path(parts_by_index, p)}
                            for p in sorted(parts, key=lambda x: x["part_index"])
                            if p["behavior"] in ("Turret", "Cannon")],
            "autoaim_tunes": sorted({w["autoaim"] for w in weapon_points(wiring[ee])
                                     if w.get("autoaim")}),
            "aim_objects": aim_objects(ee, rows),
        }
        samples.append(sample)

    # fleet census of the two point properties
    point_census = {"points": 0, "weapons": 0, "yaw": {}, "pitch": {},
                    "unresolved": [], "bad_behaviour": [], "vehicles": 0,
                    "cross_entity": []}
    owner = {}
    for ent, rec in table.items():
        for p in rec["parts"]:
            owner.setdefault(p["n"], set()).add(ent)
    for ee, row in sorted(wiring.items()):
        pts = weapon_points(row)
        if not pts:
            continue
        point_census["vehicles"] += 1
        names = {p["n"]: p for p in table.get(ee, {}).get("parts", [])}
        point_census["points"] += len(pts)
        point_census["weapons"] += len({p["weapon"] for p in pts})
        for p in pts:
            for role in ("yaw", "pitch"):
                name = p[role]
                if not name:
                    continue
                hit = names.get(name)
                if hit is None:
                    owners = sorted(owner.get(name) or [])
                    if owners:
                        point_census["cross_entity"].append({
                            "host": ee.rsplit("/", 1)[-1], "weapon": p["weapon"],
                            "role": role, "part": name,
                            "owner": owners[0].rsplit("/", 1)[-1],
                            "owners": len(owners)})
                    else:
                        point_census["unresolved"].append(
                            {"weapon": p["weapon"], "role": role, "part": name})
                    continue
                b = hit["b"] or "None"
                point_census[role][b] = point_census[role].get(b, 0) + 1
                ok = (b == "Cannon") if role == "pitch" else (b in ("Turret", "Cannon", "None"))
                if not ok:
                    point_census["bad_behaviour"].append(
                        {"weapon": p["weapon"], "role": role, "part": name, "behaviour": b})

    # aim_part_constraints census over the local parts-module cache.
    # One walk per module: behaviour comes from the same rows dict, no second decode.
    aim = {"modules": 0, "with_constraints": 0, "rows": 0, "behaviours": {},
           "examples": [], "modules_list": [], "aim_by_module": {},
           "hinged_modules": 0, "hinged_rows": 0, "rotating_modules": 0,
           "rotating_rows": 0, "hinged_by_module": {}, "rotating_by_module": {}}
    for path in sorted(glob.glob(os.path.join(RAW, "tmp", "*_vehicle_parts.vmodc"))):
        adf = jc3adf.Adf(open(path, "rb").read())
        rows_m = {p: v for p, _t, v in jc3adf.walk(adf)}
        aim["modules"] += 1
        base = os.path.basename(path)
        for arr, key in (("hinged_parts", "hinged"), ("rotating_parts", "rotating")):
            n_rows = 0
            while f"{arr}[{n_rows}].part_index" in rows_m:
                n_rows += 1
            if n_rows:
                aim[f"{key}_modules"] += 1
                aim[f"{key}_rows"] += n_rows
                aim[f"{key}_by_module"][base] = n_rows
        if "aim_part_constraints[0].source_part_index" not in rows_m:
            continue
        aim["with_constraints"] += 1
        aim["modules_list"].append(os.path.basename(path))
        by_index = {}
        for i in range(256):
            if f"parts[{i}].name.string" not in rows_m:
                continue
            by_index[rows_m.get(f"parts[{i}].part_index")] = (
                rows_m.get(f"parts[{i}].name.string"),
                rows_m.get(f"parts[{i}].behavior.string") or "None")
        n = 0
        while f"aim_part_constraints[{n}].source_part_index" in rows_m:
            aim["rows"] += 1
            for side in ("source", "target"):
                idx = rows_m.get(f"aim_part_constraints[{n}].{side}_part_index")
                part, b = by_index.get(idx, (None, "None"))
                aim["behaviours"][f"{side}:{b}"] = aim["behaviours"].get(f"{side}:{b}", 0) + 1
                if len(aim["examples"]) < 8:
                    aim["examples"].append({
                        "module": os.path.basename(path), "index": n, "side": side,
                        "part": part, "behaviour": b})
            n += 1
        aim["aim_by_module"][os.path.basename(path)] = n

    cached = {os.path.basename(p) for p in
              glob.glob(os.path.join(RAW, "tmp", "*_vehicle_parts.vmodc"))}
    for s in samples:
        mod = s["parts_module"]
        for key, field in (("aim", "aim_rows"), ("hinged", "hinged_rows"),
                           ("rotating", "rotating_rows")):
            if mod in cached:
                s[field] = aim[f"{key}_by_module"].get(mod, 0)
            else:
                s[field] = None

    # the autoaim tunes the sampled weapons name (what picks the target)
    keep = ("Stunting.MaxAimDistance", "Stunting.MinAimDistance",
            "Stunting.AngleThresholdNewTarget", "Stunting.AngleThresholdCurrentTarget",
            "Stunting.StickyAimAngleNewTarget", "Stunting.StickyAimAngleCurrentTarget",
            "Stunting.StickyAimStrength", "Stunting.CanTargetCharacters",
            "Stunting.CanTargetVehicles", "Stunting.CanTargetRigidObjects",
            "Stunting.UseWeaponDirection", "Stunting.AlwaysTargetDistance")
    shared = json.load(open(SHARED, encoding="utf-8"))
    tunes = {}
    named = sorted({t for s in samples for t in s["autoaim_tunes"]})
    for name in named:
        entry = next((e for e in shared if e.get("path") == name), None)
        if entry is None:
            stem = os.path.basename(name).split(".")[0]
            entry = next((e for e in shared if e.get("name") == stem), None)
        if not entry:
            tunes[name] = {"path": None, "values": {}}
            continue
        inst = entry["tunes"][0]["instances"][0]
        tunes[name] = {"path": entry["path"],
                       "values": {k: round(v, 4) for k, _t, v in inst["rows"] if k in keep}}

    out = {
        "samples": samples,
        "point_census": point_census,
        "aim_constraint_census": aim,
        "autoaim": tunes,
    }
    out["digest"] = hashlib.sha1(json.dumps(out, sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()[:16]
    return out


# ---------------------------------------------------------------------- md
def fnum(v: float) -> str:
    return f"{v:g}"


def md_sample(s: dict) -> list[str]:
    lines = [f"### {s['label']}", "",
             f"`{s['entity'].rsplit('/', 1)[-1]}` - {s['parts']} parts, "
             f"{len(s['constraints'])} constraint objects "
             f"({', '.join(f'{k} {v}' for k, v in s['constraint_classes'].items())}); "
             f"`aim_part_constraints` rows {s.get('aim_rows')}, `hinged_parts` rows "
             f"{s.get('hinged_rows')}, `rotating_parts` rows {s.get('rotating_rows')}.", ""]
    for m in s.get("mount_paths", []):
        arrow = " -> ".join(f"`{c['part']}`" + (f" ({c['behavior']})" if c["behavior"] else "")
                             for c in m["path"])
        lines.append(f"- mount path for `{m['of']}`: {arrow}")
    if s.get("mount_paths"):
        lines.append("")
    lines += ["| part | i | behaviour | parent | constraint | class | pivot (x, y, z) | "
              "axis | min..max (deg) |", "|---|---|---|---|---|---|---|---|---|"]
    for c in s["constrained_parts"]:
        h = c.get("hinge") or {}
        if h.get("pivot"):
            lim = f"{fnum(h['min_deg'])} .. {fnum(h['max_deg'])}"
            pivot = ", ".join(fnum(x) for x in h["pivot"])
            axis = ", ".join(fnum(x) for x in h["axis"])
        else:
            lim = pivot = axis = "-"
        lines.append(f"| `{c['part']}` | {c['index']} | {c['behavior'] or '-'} | "
                     f"{c['parent']} | {c['constraint']} | `{h.get('class', '-')}` | "
                     f"{pivot} | {axis} | {lim} |")
    if s["weapons"]:
        lines += ["", "Weapon points that name the moving parts:", "",
                  "| weapon | binding | point | yaw part | pitch part | point xyz |",
                  "|---|---|---|---|---|---|"]
        for w in s["weapons"]:
            lines.append(f"| `{w['weapon']}` | {', '.join(w['binding']) or '-'} | "
                         f"`{w['point']}` | `{w['yaw'] or '-'}` | `{w['pitch'] or '-'}` | "
                         f"{', '.join(fnum(x) for x in (w['xyz'] or [])) or '-'} |")
    if s["aim_objects"]:
        lines += ["", "Aim objects:", "",
                  "| class | name | min_aim_distance | xyz |", "|---|---|---|---|"]
        for a in s["aim_objects"]:
            lines.append(f"| `{a['class']}` | `{a['name']}` | {a['min_aim_distance'] or '-'} | "
                         f"{', '.join(fnum(x) for x in (a['xyz'] or [])) or '-'} |")
    lines.append("")
    return lines


def render_md(d: dict) -> str:
    pc, ac = d["point_census"], d["aim_constraint_census"]
    lines = [
        "# Turrets and cannons - how JC3 moves and aims them",
        "",
        "G2-13. The short answer: a turret is **two parts and two Havok hinges**, not a special "
        "object. The yaw part carries behaviour `Turret`, the pitch part carries `Cannon`, each "
        "is one `hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`, and the weapon's "
        "fire point names both parts in two unnamed string properties. The parts module's "
        "`aim_part_constraints` array is **not** turret aim - it is the suspension linkage.",
        "",
        "## 1. The medium tank (v0201) - the full chain",
        "",
        "| | |",
        "|---|---|",
        "| yaw part | `mediumtank_turret`, index 26, behaviour `Turret`, parent 0 (body) |",
        "| yaw hinge | constraint 2, pivot (0, 2.2812, 1.1382), axis +Y, **-179 .. +179 deg** |",
        "| pitch part | `mediumtank_cannon`, index 38, behaviour `Cannon`, parent 26 |",
        "| pitch hinge | constraint 0, pivot (0, 2.5347, 0), axis +X, **-5 .. +20 deg** |",
        "| hatch | `mediumtank_hatch`, index 39, `FrontLeftDoor`, parent 26, constraint 1, "
        "pivot (-0.4848, 2.921, 1.4785), axis +X, **0 .. 130 deg** |",
        "| weapon | `w602_mediumtank_canon`, binding `main_weapon` |",
        "| fire point | `fire_position_0` at local (0, 0.3739, -5.8174); names yaw "
        "`mediumtank_turret` and pitch `mediumtank_cannon` |",
        "| counts | 42 parts, 3 constraints, all `hkpLimitedHingeConstraintData`, no ragdoll |",
        "",
        "The cannon pivots on X 0.25 m above the turret ring and its fire point sits 5.82 m "
        "forward, so the muzzle swings with the pitch hinge. `parent_space_offset` is identity "
        "on both parts, and the pivots are printed as the packfile stores them: on this vehicle "
        "they land exactly where the art puts the ring and the trunnion. Neither part names a "
        "rotation speed.",
        "",
        "## 2. The sampled vehicles",
        "",
    ]
    for s in d["samples"]:
        lines += md_sample(s)
    lines += [
        "## 3. The point properties (fleet census)",
        "",
        f"Across {pc['vehicles']} armed entities, **{pc['points']} fire points** on "
        f"**{pc['weapons']} weapons** name a yaw part (`id:80201E4D`) or a pitch part "
        f"(`id:5C19E7E0`). The values are part-name strings, not hashes.",
        "",
        "| role | part behaviour | count |",
        "|---|---|---|",
    ]
    for role in ("yaw", "pitch"):
        for b, n in sorted(pc[role].items()):
            lines.append(f"| {role} | `{b}` | {n} |")
    lines += ["",
              f"Every pitch part is a `Cannon` part. Yaw parts are `Turret` (true turrets), "
              f"`Cannon` (boat/jeep mounts that yaw and pitch as two Cannon-behaviour parts) or "
              f"plain parts on aircraft pods. Unresolved names: {len(pc['unresolved'])}; "
              f"unexpected behaviours: {len(pc['bad_behaviour'])}.",
              ""]
    if pc["cross_entity"]:
        hosts = sorted({c["host"] for c in pc["cross_entity"]})
        owners = sorted({c["owner"] for c in pc["cross_entity"]})
        lines += [f"{len(pc['cross_entity'])} entries name a part that is not in the host's "
                  f"parts module but in another entity's "
                  f"({', '.join('`' + w + '`' for w in hosts)} -> "
                  f"{', '.join('`' + w + '`' for w in owners)}): the cargo plane carries the "
                  "medium tank and mounts its whole weapon, so the weapon's point still names "
                  "the tank's own turret and cannon parts. Counted here, not unresolved.",
                  ""]
    if pc["unresolved"]:
        lines += ["Unresolved:", ""]
        for u in pc["unresolved"][:10]:
            lines.append(f"- `{u['weapon']}` {u['role']} `{u['part']}`")
        lines.append("")

    lines += [
        "## 4. `aim_part_constraints` is suspension, not a turret",
        "",
        f"Decoded from {ac['modules']} parts modules in the local cache: every one declares the "
        f"array, but only **{ac['with_constraints']}** have rows (**{ac['rows']}** in total). "
        f"Parts named by behaviour:",
        "",
        "| side:behaviour | count |",
        "|---|---|",
    ]
    for k, n in sorted(ac["behaviours"].items()):
        lines.append(f"| `{k}` | {n} |")
    lines += ["", "Examples:", ""]
    for e in ac["examples"]:
        lines.append(f"- `{e['module']}` row {e['index']} {e['side']} "
                     f"`{e['part']}` ({e['behaviour']})")
    lines += ["",
              "No row has a `Turret` or `Cannon` behaviour, and the six turreted vehicles in "
              "this sample (medium tank, Bavarium tank, small tank, APC, armoured jeep, "
              "technical) have **0** aim constraints each. The array is a part-to-part aim "
              "constraint used by suspension and steering links: a U-bar/axle/coilspring "
              "source aims at a brake drum, disc, caliper or wheel target.",
              "",
              f"The module's two other moving-part arrays are empty on all eight samples: "
              f"`hinged_parts[]` and `rotating_parts[]` carry 0 rows for each (fleet: "
              f"{ac['hinged_modules']} of {ac['modules']} modules have `hinged_parts` rows, "
              f"{ac['rotating_modules']} have `rotating_parts` rows). So for a tank the hinge "
              f"is not declared in the parts module at all - the part's `constraint_index` "
              f"points into `.physicsc`, and that is the whole link.",
              ""]

    lines += [
        "## 5. How the aim target is chosen",
        "",
        "Each sampled entity carries exactly one `STargetPoint` named `AutoAimTargetPoint` "
        "(`min_aim_distance` -1, so no minimum) plus two unnamed values (a float 2 and an int "
        "1). Its `world` matrix translation is (0, 1, 0) on every sample: the target point is "
        "the vehicle origin one metre up at the body centre, not the muzzle and not the turret.",
        "",
        "The weapons name autoaim tunes. Both tanks' `w602_mediumtank_canon` and "
        "`w603_mediumtank_mgun` and the small tank's `w605_smalltank_canon` use "
        "`autoaim_vehicle_mgun`; the mounted M2 (`w206_mounted_capstone_m2hm`) on the APC, "
        "armoured jeep and technical uses `autoaim_assault_rifle`.",
        "",
    ]
    for name, t in sorted(d["autoaim"].items()):
        lines += [f"`{os.path.basename(name)}` - `{name}`:", "",
                  "| tune member | value |", "|---|---|"]
        for k, v in sorted(t["values"].items()):
            lines.append(f"| `{k}` | {v} |")
        lines.append("")
    lines += [
              "`Stunting` is the in-vehicle set. Candidates are considered out to 70 m and "
              "never closer than 5 m; a candidate within 0.03 rad (1.7 deg) of the aim line is "
              "accepted, or 0.04 rad (2.3 deg) on the rifle tune, and the current target is "
              "held until it leaves 0.05 rad (2.9 deg) / 0.06 rad (3.4 deg). Sticky aim then "
              "allows 6 deg for a new target and 16 deg for the current one, strength 0.4. "
              "`CanTargetCharacters` is 1 while `CanTargetVehicles` and "
              "`CanTargetRigidObjects` are 0: the soft aim assist on the tank cannon is for "
              "characters, not vehicles.",
              "",
              "So no file holds an aim ray or a turret target. The aim system picks a point "
              "(the entity's `STargetPoint`, or a soft-aim candidate), and the two hinges are "
              "driven to put the cannon on it. The pitch limit stops the cannon elevating "
              "further; that is a constraint, not a target check.",
              "",
              "## 6. Validation and limits",
              "",
              "`jc3turret.py --check` re-reads the eight entities' parts modules and `.physicsc` "
              "files, rebuilds every table and compares the json field-for-field and the md "
              "byte-for-byte. It asserts: the medium tank's three constraints are the cannon "
              "(-5 .. 20 deg), hatch (0 .. 130 deg) and turret (-179 .. 179 deg); every "
              "constrained part's `constraint_index` resolves to an object; every Turret and "
              "Cannon part sits on a limited hinge with an identity `parent_space_offset`; "
              "every pitch part in the fleet is a `Cannon` part; no `aim_part_constraints` row "
              "names a Turret or Cannon part; the samples name exactly one "
              "`AutoAimTargetPoint` at (0, 1, 0); the six turreted samples have 0 "
              "`aim_part_constraints` rows.",
              "",
              "**Limits.** Rotation speeds and accelerations are not in the decoded data - a "
              "limited hinge carries an axis and two angles, and the turn rate is code-side "
              "(UNKNOWN). The hinge transform's frame (body-A local vs vehicle space) is not "
              "proven: the medium tank's numbers agree with vehicle space, and on the wheeled "
              "mounts the pitch pivot sits above an unconstrained adapter part, so a port "
              "should read them the way they are printed. `hkpRagdollConstraintData` objects "
              "are counted but not "
              "decoded (the armoured jeep and small tank carry them). The two point properties "
              "`id:80201E4D`/`id:5C19E7E0` still have no recovered names; their meaning is proven "
              "by the part names and behaviours they carry. The `aim_part_constraints` census "
              "covers the modules in the local cache, not all 233.",
              "",
              "**Not in the files:** a per-vehicle turret turn rate, a turret ring bone, or any "
              "aim limit on the weapon itself. A B-05 port must copy the parts, the hinge "
              "constraints and the two point strings; there is no single \"turret\" field to set.",
              ""]
    return "\n".join(lines).rstrip() + "\n"


# -------------------------------------------------------------------- check
def invariant_checks(d: dict) -> list[str]:
    bad = []
    by_tag = {s["tag"]: s for s in d["samples"]}
    medium = by_tag["mediumtank"]
    want = {"mediumtank_cannon": (-5.0, 20.0), "mediumtank_turret": (-179.0, 179.0),
            "mediumtank_hatch": (0.0, 130.0)}
    for c in medium["constrained_parts"]:
        if c["part"] not in want:
            continue
        h = c.get("hinge")
        if not h or "min_deg" not in h:
            bad.append(f"mediumtank {c['part']} has no decoded hinge")
            continue
        lo, hi = want[c["part"]]
        if abs(h["min_deg"] - lo) > 0.01 or abs(h["max_deg"] - hi) > 0.01:
            bad.append(f"mediumtank {c['part']} limits {h['min_deg']}..{h['max_deg']} "
                       f"!= {lo}..{hi}")
    for s in d["samples"]:
        n = len(s["constraints"])
        for c in s["constrained_parts"]:
            if not (0 <= c["constraint"] < n):
                bad.append(f"{s['tag']} part {c['part']} constraint {c['constraint']} "
                           f"out of {n} constraint objects")
            if c["behavior"] in ("Turret", "Cannon"):
                if not c.get("identity_offset"):
                    bad.append(f"{s['tag']} {c['behavior']} part {c['part']} has a "
                               f"non-identity parent_space_offset")
                if "hinge" not in c:
                    bad.append(f"{s['tag']} {c['behavior']} part {c['part']} has no hinge")
                elif c["hinge"]["class"] != LIMITED:
                    bad.append(f"{s['tag']} {c['behavior']} part {c['part']} is on a "
                               f"{c['hinge']['class']}, not a limited hinge")
        points = [a for a in s["aim_objects"] if a["class"] == "STargetPoint"]
        if len(points) != 1 or points[0]["name"] != "AutoAimTargetPoint":
            bad.append(f"{s['tag']} STargetPoint set: {[a['name'] for a in points]}")
        elif points[0]["xyz"] != [0.0, 1.0, 0.0]:
            bad.append(f"{s['tag']} aim target moved to {points[0]['xyz']}")
    for tag in ("mediumtank", "bavariumtank", "smalltank", "apc", "armoredjeep",
                "technicaljeep"):
        if by_tag[tag].get("aim_rows") != 0:
            bad.append(f"{tag} has {by_tag[tag].get('aim_rows')} aim_part_constraints rows, "
                       f"expected 0")
    pc = d["point_census"]
    if pc["bad_behaviour"]:
        bad.append(f"point behaviours unexpected: {pc['bad_behaviour'][:3]}")
    if pc["unresolved"]:
        bad.append(f"point parts unresolved: {pc['unresolved'][:3]}")
    for k in pc["pitch"]:
        if k != "Cannon":
            bad.append(f"a pitch part is {k}, not Cannon")
    ac = d["aim_constraint_census"]
    for k in ac["behaviours"]:
        if k.endswith(":Turret") or k.endswith(":Cannon"):
            bad.append(f"aim_part_constraints names a turret/cannon part: {k}")
    if "turret" not in " ".join(c["part"] for c in medium["constrained_parts"]):
        bad.append("mediumtank turret part missing")
    return bad


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(d))
    print(f"{JSON_NAME}: {len(d['samples'])} samples, "
          f"{d['point_census']['points']} point rows, "
          f"{d['aim_constraint_census']['with_constraints']} aim-constraint modules")
    print(f"{MD_NAME}: {len(open(os.path.join(OUT, MD_NAME), encoding='utf-8').read().splitlines())} lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = []
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not os.path.exists(jp) or not os.path.exists(mp):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing")
        return 1
    old = json.load(open(jp, encoding="utf-8"))
    if old != d:
        for k in sorted(set(old) | set(d)):
            if old.get(k) != d.get(k):
                bad.append(f"json section changed: {k}")
                break
    md = render_md(d)
    current = open(mp, encoding="utf-8").read()
    if md != current:
        import difflib
        diff = list(difflib.unified_diff(current.splitlines(), md.splitlines(),
                                         "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    bad += invariant_checks(d)
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {len(d['samples'])} samples, "
          f"{d['point_census']['points']} points on {d['point_census']['weapons']} weapons, "
          f"{d['aim_constraint_census']['rows']} aim-constraint rows, "
          f"{len(d['samples'][0]['constraints'])} mediumtank constraints")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    if what == "samples":
        print(json.dumps([{k: v for k, v in s.items() if k != "constraints"}
                          for s in d["samples"]], indent=1, sort_keys=True, ensure_ascii=False))
    elif what == "census":
        print(json.dumps({"points": d["point_census"],
                          "aim": d["aim_constraint_census"]}, indent=1, sort_keys=True,
                         ensure_ascii=False)[:12000])
    elif what == "tune":
        print(json.dumps(d["autoaim"], indent=1, sort_keys=True, ensure_ascii=False))
    else:
        print("one of: samples, census, tune")
        return 2
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("what", nargs="?", default="samples")
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
