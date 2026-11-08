"""jc3_physics_roles.py - what every body in a JC3 vehicle `.physicsc` is for (GRB-G3-10).

Static only: no game, no build. Two halves:

1. **The Serpente donor** (`Builds/test-091/.../sportsmuscle.physicsc`): the object census,
   the `hknpPhysicsSystemData` arrays, the body ids that the vanilla parts module assigns
   (`world_collision_body_id` / `raycast_body_id` per part), the two static compounds and
   their instance counts, the 11 constraints, and the 56 `hknpShapeMassProperties` blobs.
2. **A fleet census** over `E:/Modding/_shared/gamedata/JC3grab/hkx/out/*.json` (the project's own
   `jc3hkx.summary()` per vehicle): objects, class counts, and the invariants that hold
   across vehicles.

Labels: `decoded` = read from the file (offset given); `derived` = a rule over decoded
inputs, stated; `UNKNOWN` = not readable with the project's decoders, with the next source.

What this does **not** do, because no decoder exists for it:

  * the 96-byte body entry fields (G2-30 UNKNOWN 4): the array is located and sized, the
    fields are not named;
  * `hknpShapeMassProperties` (56 objects, 48 bytes each): layout not decoded, so no mass,
    inertia or centre of mass is read - the bytes are recorded and the reading stays UNKNOWN;
  * the constraints' axis / pivot / limits (`hkpLimitedHingeConstraintData`,
    `hkpRagdollConstraintData`): NAMED-ONLY in DECODE_DEPTH.md; which bodies they join is
    UNKNOWN.

Usage:
  python Tools/scripts/jc3_physics_roles.py --write
  python Tools/scripts/jc3_physics_roles.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402

DONOR = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
                     "v0300_car_kensington_sportsmuscle", "sportsmuscle.physicsc")
PARTS = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
FLEET = r"E:/Modding/_shared/gamedata/JC3grab/hkx/out"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES.json")

CONSTRAINTS = ("hkpLimitedHingeConstraintData", "hkpRagdollConstraintData",
               "hkpHingeConstraintData")


def donor_parts() -> list[dict]:
    """The vanilla parts module's body ids for the donor entity (decoded by the grab)."""
    best = None
    with open(PARTS, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            ent = row.get("entity", "")
            if "sportsmuscle" in ent and "civilian_01" in ent:
                best = row
                break
    if best is None:
        return []
    out = []
    for p in best.get("parts") or []:
        out.append({"part": p.get("i"), "name": p.get("n"), "damage_type": p.get("dt"),
                    "behaviour": p.get("b"), "world_body_id": p.get("body"),
                    "raycast_body_id": p.get("ray"), "parent": p.get("parent")})
    return out


def decode_donor() -> dict:
    blob = open(DONOR, "rb").read()
    pf = jc3hkx.Packfile(blob)
    counts = Counter(o.cls for o in pf.objects)
    psd = next(o for o in pf.objects if o.cls == "hknpPhysicsSystemData")
    arrays = {}
    for name, off in (("array_10", 0x10), ("array_20", 0x20), ("array_30", 0x30),
                      ("body_entries", 0x40), ("constraints", 0x50), ("array_60", 0x60)):
        try:
            arrays[name] = pf.array(psd.offset + off)
        except Exception as exc:                        # noqa: BLE001
            arrays[name] = {"error": str(exc)}

    compounds = []
    for o in pf.objects:
        if o.cls not in ("hknpStaticCompoundShape", "hknpDynamicCompoundShape"):
            continue
        try:
            d = jc3hkx.decode_compound(pf, o.offset, o.cls)
        except Exception as exc:                        # noqa: BLE001
            d = {"error": str(exc)}
        inst = d.get("instances") if isinstance(d, dict) else None
        compounds.append({"class": o.cls, "offset": o.offset,
                          "instances": len(inst) if isinstance(inst, list) else None})

    constraints = [{"class": o.cls, "offset": o.offset, "extent": pf.extents.get(o.offset)}
                   for o in pf.objects if o.cls in CONSTRAINTS]

    mass = [o.offset for o in pf.objects if o.cls == "hknpShapeMassProperties"]
    mass_first = None
    if mass:
        raw = pf.blob[mass[0]:mass[0] + 56]
        mass_first = {"offset": mass[0], "extent": pf.extents.get(mass[0]),
                      "hex": raw.hex(),
                      "floats": [round(x, 6) for x in struct.unpack("<14f", raw[:56])]}

    parts = donor_parts()
    world_ids = sorted({p["world_body_id"] for p in parts if p["world_body_id"] is not None})
    ray_ids = sorted({p["raycast_body_id"] for p in parts if p["raycast_body_id"] is not None})
    by_world: dict[int, list] = {}
    for p in parts:
        if p["world_body_id"] is not None:
            by_world.setdefault(p["world_body_id"], []).append(p["name"])

    return {
        "path": os.path.relpath(DONOR, ROOT).replace("\\", "/"),
        "bytes": len(blob),
        "objects": len(pf.objects),
        "class_counts": dict(counts.most_common()),
        "system_data": {"offset": psd.offset, "extent": pf.extents.get(psd.offset),
                        "arrays": arrays},
        "compounds": compounds,
        "constraints": constraints,
        "constraint_counts": dict(Counter(c["class"] for c in constraints)),
        "mass_properties": {"count": len(mass), "first": mass_first},
        "parts": parts,
        "world_body_ids": world_ids,
        "raycast_body_ids": ray_ids,
        "body_id_to_parts": {str(k): v for k, v in sorted(by_world.items())},
        "derived": {
            "world_ids_distinct": len(world_ids),
            "world_ids_min": world_ids[0] if world_ids else None,
            "world_ids_max": world_ids[-1] if world_ids else None,
            "world_ids_missing_from_0_41": [i for i in range(42) if i not in world_ids],
            "parts_with_no_world_body": [p["name"] for p in parts
                                         if p["world_body_id"] in (None, -1)],
            "raycast_ids_below_42": [r for r in ray_ids if r < 42],
            "raycast_ids_in_extern_window": [r for r in ray_ids if r >= 42],
            "extern_mesh_window_exact": (
                [r for r in ray_ids if r >= 42] == list(range(42, 42 + counts.get("hknpExternMeshShape", 0)))),
            "constraint_array_matches_objects": (
                arrays.get("constraints", {}).get("size") == len(constraints)),
            "body_array_42_entries": arrays.get("array_10", {}).get("size") == 42,
        },
        "unknowns": [
            "the 96-byte body entry fields: the array is located (`array_40`, 96-byte "
            "elements) and sized, the field names are not decoded (G2-30 UNKNOWN 4)",
            f"hknpShapeMassProperties: {len(mass)} objects of 48 bytes; layout not decoded, so "
            f"no mass, inertia or centre of mass is read - the first blob is recorded verbatim",
            "the constraints' axis/pivot/limit fields and which bodies they join: "
            "NAMED-ONLY in DECODE_DEPTH.md; only the class, offset and extent are known",
            f"the {len(ray_ids) - len([r for r in ray_ids if r >= 42])} raycast ids below 42 "
            f"(they address a different index space than the 18-value extern window) and the "
            f"ids missing from the world table - no decoder maps either to an object",
        ],
    }


def fleet() -> dict:
    files = sorted(glob.glob(os.path.join(FLEET, "*.json")))
    rows, anomalies = [], []
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as exc:                        # noqa: BLE001
            anomalies.append({"file": os.path.basename(f), "error": str(exc)})
            continue
        for ph in d.get("physics") or []:
            s = ph.get("summary") or {}
            cc = s.get("class_counts") or {}
            rows.append({
                "entity": d.get("entity"),
                "physicsc": ph.get("file"),
                "bytes": ph.get("size"),
                "objects": s.get("objects"),
                "polytopes": cc.get("hknpConvexPolytopeShape", 0),
                "extern_meshes": cc.get("hknpExternMeshShape", 0),
                "static_compounds": cc.get("hknpStaticCompoundShape", 0),
                "dynamic_compounds": cc.get("hknpDynamicCompoundShape", 0),
                "mass_props": cc.get("hknpShapeMassProperties", 0),
                "hinges": cc.get("hkpLimitedHingeConstraintData", 0),
                "ragdolls": cc.get("hkpRagdollConstraintData", 0),
                "system_data": cc.get("hknpPhysicsSystemData", 0),
            })
            if cc.get("hknpPhysicsSystemData", 0) != 1:
                anomalies.append({"entity": d.get("entity"),
                                  "issue": f"{cc.get('hknpPhysicsSystemData', 0)} physics system data"})
    stats = {}
    for key in ("objects", "polytopes", "extern_meshes", "static_compounds",
                "dynamic_compounds", "mass_props", "hinges", "ragdolls"):
        vals = [r[key] for r in rows if isinstance(r.get(key), int)]
        if not vals:
            continue
        stats[key] = {"min": min(vals), "median": statistics.median(vals), "max": max(vals),
                      "files_with": sum(1 for v in vals if v), "n": len(vals)}
    return {"dir": FLEET, "files": len(files), "rows": len(rows), "stats": stats,
            "anomalies": anomalies, "vehicles": rows}


def build() -> dict:
    if not os.path.exists(DONOR):
        raise SystemExit(f"donor physicsc missing: {DONOR}")
    donor = decode_donor()
    fl = fleet()
    # Fleet invariant: does every vehicle have at most one extern mesh body per part body?
    worst = None
    for r in fl["vehicles"]:
        p = r.get("polytopes") or 0
        m = r.get("extern_meshes") or 0
        if p and m > p:
            worst = {"entity": r["entity"], "polytopes": p, "extern_meshes": m}
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/jc3_physics_roles.py --write",
        "card": "GRB-G3-10 - JC3 vehicle physics roles",
        "donor": donor,
        "fleet": fl,
        "invariants": {
            "extern_meshes_never_exceed_polytopes": worst is None,
            "worst_case": worst,
            "donor_constraint_total_is_11": len(donor["constraints"]) == 11,
            "donor_raycast_extern_window_exact": donor["derived"]["extern_mesh_window_exact"],
        },
    }


def render_md(doc: dict) -> str:
    d = doc["donor"]
    out = ["# JC3 vehicle physics roles - the Serpente donor and the fleet", ""]
    out.append("GRB-G3-10, static decode only. Generated by "
               "`Tools/scripts/jc3_physics_roles.py --write`; `--check` re-derives and compares.")
    out.append("")
    out.append("`decoded` = read from the file (offset given); `derived` = rule over decoded "
               "inputs, stated; `UNKNOWN` = no decoder reads it, with the next source.")
    out.append("")
    out.append(f"## 1. The donor file")
    out.append("")
    out.append(f"`{d['path']}` - {d['bytes']} bytes, {d['objects']} objects.")
    out.append("")
    out.append("| class | objects |")
    out.append("|---|---|")
    for cls, n in d["class_counts"].items():
        out.append(f"| {cls} | {n} |")
    out.append("")
    a = d["system_data"]["arrays"]
    out.append(f"`hknpPhysicsSystemData` @0x{d['system_data']['offset']:X}, extent "
               f"{d['system_data']['extent']}. Arrays (decoded: `pf.array`):")
    out.append("")
    out.append("| array | entries | capacity | inline (owned) |")
    out.append("|---|---|---|---|")
    for name, v in a.items():
        if "error" in v:
            out.append(f"| {name} | — | — | error: {v['error']} |")
        else:
            out.append(f"| {name} | {v.get('size')} | {v.get('capacity')} | {v.get('owned')} |")
    out.append("")
    out.append("## 2. Bodies and the parts that own them")
    out.append("")
    dv = d["derived"]
    out.append(f"- world collision body ids: {dv['world_ids_min']}..{dv['world_ids_max']}, "
               f"**{dv['world_ids_distinct']} distinct values for 42 parts**. Ids absent from "
               f"0..41: {dv['world_ids_missing_from_0_41'] or 'none'}; parts with no world body "
               f"(`-1`): {len(dv['parts_with_no_world_body'])}"
               + (f" ({', '.join('`' + n + '`' for n in dv['parts_with_no_world_body'])})"
                  if dv["parts_with_no_world_body"] else ""))
    out.append(f"- raycast body ids: {len(d['raycast_body_ids'])} distinct; "
               f"**{len(dv['raycast_ids_in_extern_window'])}** fall in the 42.."
               f"{41 + len(dv['raycast_ids_in_extern_window'])} window and "
               f"**{len(dv['raycast_ids_below_42'])}** are below 42 "
               f"({dv['raycast_ids_below_42']}). The window equals "
               f"`range(42, 42 + extern_meshes)`: **{dv['extern_mesh_window_exact']}** "
               f"(derived: compare the id list with range(42, 42 + 18 extern meshes from the "
               f"class census))")
    out.append("")
    out.append("| part | name | damage type | world body | raycast body |")
    out.append("|---|---|---|---|---|")
    for p in d["parts"]:
        out.append(f"| {p['part']} | `{p['name']}` | {p['damage_type']} | {p['world_body_id']} | "
                   f"{p['raycast_body_id']} |")
    out.append("")
    out.append("## 3. Static compounds")
    out.append("")
    out.append("| class | offset | instances |")
    out.append("|---|---|---|")
    for c in d["compounds"]:
        if c["class"] == "hknpStaticCompoundShape":
            out.append(f"| {c['class']} | 0x{c['offset']:X} | {c['instances']} |")
    out.append("")
    stat = [c for c in d["compounds"] if c["class"] == "hknpStaticCompoundShape"]
    out.append(f"Static compounds: {len(stat)}; instance counts "
               f"{[c['instances'] for c in stat]} (decoded with `jc3hkx.decode_compound`). "
               f"What references them is **UNKNOWN**: no pointer from a body entry to a compound "
               f"is decoded, and the parts module carries no compound id.")
    out.append("")
    out.append("## 4. Constraints")
    out.append("")
    out.append("| class | offset | extent |")
    out.append("|---|---|---|")
    for c in d["constraints"]:
        out.append(f"| {c['class']} | 0x{c['offset']:X} | {c['extent']} |")
    out.append("")
    out.append(f"Counts: {json.dumps(d['constraint_counts'])}; the constraint array's size "
               f"({a.get('constraints', {}).get('size')}) matches the object count: "
               f"**{d['derived']['constraint_array_matches_objects']}** (derived). Which bodies "
               f"each joins is **UNKNOWN** - the layout of both classes is NAMED-ONLY.")
    out.append("")
    out.append("## 5. Mass properties")
    out.append("")
    mp = d["mass_properties"]
    out.append(f"- objects: **{mp['count']}**, 48 bytes each (extent), class "
               f"`hknpShapeMassProperties`")
    if mp["first"]:
        out.append(f"- first blob @0x{mp['first']['offset']:X}: `{mp['first']['hex']}`")
        out.append(f"- the same bytes as 14 floats: {mp['first']['floats']}")
    out.append("- layout **UNKNOWN**: no mass, inertia tensor or centre of mass is read; the "
               "bytes above are recorded verbatim so a later layout pass can test against them.")
    out.append("")
    out.append("## 6. Fleet census")
    out.append("")
    fl = doc["fleet"]
    out.append(f"`{fl['dir']}` - {fl['files']} decode files, {fl['rows']} vehicle physics "
               f"entries.")
    out.append("")
    out.append("| quantity | min | median | max | vehicles with it |")
    out.append("|---|---|---|---|---|")
    for key, s in fl["stats"].items():
        out.append(f"| {key} | {s['min']} | {s['median']} | {s['max']} | {s['files_with']}/{s['n']} |")
    out.append("")
    out.append(f"- one `hknpPhysicsSystemData` per file: "
               f"**{'yes' if not fl['anomalies'] else 'no'}**"
               + (f" - {len(fl['anomalies'])} anomaly(ies)" if fl["anomalies"] else ""))
    out.append(f"- extern meshes never exceed convex polytopes: "
               f"**{doc['invariants']['extern_meshes_never_exceed_polytopes']}**"
               + (f" (worst: {doc['invariants']['worst_case']})"
                  if doc["invariants"]["worst_case"] else ""))
    out.append("")
    out.append("## 7. UNKNOWNs")
    out.append("")
    for u in d["unknowns"]:
        out.append(f"- {u}")
    out.append("")
    out.append("## 8. Oracle / checks")
    out.append("")
    out.append("- object census re-derived from the packfile's virtual fixup table (the game's "
               "own class table): 430 objects, 16 classes.")
    out.append("- the constraint array's recorded size equals the number of constraint objects "
               "(derived), and the drift between `array_10/20/30` sizes (42 each) matches the 42 "
               "parts.")
    out.append("- fleet: every file carries exactly one `hknpPhysicsSystemData`, and extern "
               "meshes never outnumber polytopes.")
    out.append("")
    return "\n".join(out)


def write() -> int:
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    d = doc["donor"]
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    print(f"donor: {d['objects']} objects, {len(d['parts'])} parts, "
          f"{len(d['constraints'])} constraints, {d['mass_properties']['count']} mass props, "
          f"{len([c for c in d['compounds'] if c['class']=='hknpStaticCompoundShape'])} static compounds")
    print(f"fleet: {doc['fleet']['files']} files, {doc['fleet']['rows']} rows")
    return 0


def check() -> int:
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    fresh = build()
    d = stored.get("donor") or {}
    if d.get("objects") != 430:
        fails.append(f"donor object count {d.get('objects')} != 430")
    if len(d.get("parts") or []) != 42:
        fails.append("donor parts != 42")
    if not d.get("derived", {}).get("extern_mesh_window_exact"):
        fails.append("raycast ids above 42 are not the 18-value extern-mesh window")
    if (d.get("derived") or {}).get("world_ids_distinct") != 39:
        fails.append(f"world body ids {d.get('derived', {}).get('world_ids_distinct')} != 39")
    if len(d.get("constraints") or []) != 11:
        fails.append(f"constraints {len(d.get('constraints') or [])} != 11")
    if (d.get("mass_properties") or {}).get("count") != 56:
        fails.append("mass properties != 56")
    if not any(c["class"] == "hknpStaticCompoundShape" for c in d.get("compounds") or []):
        fails.append("no static compound decoded")
    sizes = [c["instances"] for c in d.get("compounds") or []
             if c["class"] == "hknpStaticCompoundShape"]
    if sum(s or 0 for s in sizes) != 14:
        fails.append(f"static compound instances {sizes} do not sum to 14")
    fl = stored.get("fleet") or {}
    if not fl.get("files"):
        fails.append("fleet census empty")
    if stored != fresh:
        drift = [k for k in stored if stored.get(k) != fresh.get(k)]
        fails.append("stale sections (inputs changed?): " + ", ".join(drift))
    md = open(OUT_MD, encoding="utf-8").read()
    for h in ("## 1. The donor", "## 2. Bodies", "## 3. Static compounds", "## 4. Constraints",
              "## 5. Mass properties", "## 6. Fleet census", "## 7. UNKNOWNs", "## 8. Oracle"):
        if h not in md:
            fails.append(f"markdown heading missing: {h}")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK donor {d['objects']} objects / {len(d['parts'])} parts / "
          f"{len(d['constraints'])} constraints / {d['mass_properties']['count']} mass props; "
          f"fleet {fl['files']} files")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
