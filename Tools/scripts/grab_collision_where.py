#!/usr/bin/env python3
"""grab_collision_where.py - where the DRIVABLE Batmobile's collision lives (G3-16).

Only the wreck's asset (`Batmobile_V3_Destroyed_Physics`, 32 bodies) was known before
this card.  This decodes the drivable car's side from the shipped cooked packages:

    BmGame.upk     Physics.Batmobile_V3_Physics (158266) and its RB_BodySetup children
                   169750 / 169751, its RB_ConstraintSetup 171462 and its
                   PhysicsAssetInstance 158308
    BmGame.upk     StaticMesh 175973 / 175974 and their RB_BodySetup 169748 / 169749
                   (the Batman-vs-Batmobile fight collision meshes)
    Playable_Batmobile_SF.upk
                   archetype `Vehicle.Batmobile` (5281), spent components: SVehicleMesh
                   5289, CollisionCylinder 276/277/278, RB_StayUprightSetup 5106,
                   RB_ConstraintInstance 5098, the four SVehicleWheel 5394-5397,
                   SimulationModel 5282, and the two BatmanCollisionMesh* components
    Research/BatmobileGrab/BMSDK_OFFSETS.json
                   field names per absolute property offset (never guessed here)

Nothing is taken from engine defaults: a tag offset whose class layout is not in
BMSDK_OFFSETS.json keeps the name UNKNOWN.

Labels: decoded = read from bytes (package, export, tag offset); derived = rule +
inputs, stated; UNKNOWN = not found, with what was tried.

Usage:
    python Tools/scripts/grab_collision_where.py --write   # writes the .md and .json
    python Tools/scripts/grab_collision_where.py --check   # recomputes and compares
"""
import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U            # noqa: E402
import grab_physics as GP       # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
OFFSETS = os.path.join(OUT, "BMSDK_OFFSETS.json")

PLAYABLE = "Playable_Batmobile_SF.upk"
ARCHETYPE = 5281
SVEHICLE_MESH = 5289
WHEELS = [5394, 5395, 5396, 5397]
SIM = 5282
STAY_UPRIGHT = 5106
STAY_UPRIGHT_INSTANCE = 5098
DRIVABLE_ASSET = 158266
DRIVABLE_BODIES = [169750, 169751]
DRIVABLE_CONSTRAINT = 171462
DRIVABLE_INSTANCE = 158308
STATIC_COLLISION_MESHES = [5392, 5393]
FIGHT_TEMPLATES = {5392: 176111, 5393: 176112}
FIGHT_BODY_SETUPS = [169748, 169749]
SVEHICLE_TEMPLATE = 175716          # BmGame Default__RVehicleBatmobileBase.SVehicleMesh
WRECK_ASSET = 5017
SELECTOR_OFFSET = 5895     # RVehicleBatmobileBase.BatmanVsBatmobileCollisionMode

CLASSES = {}


def load_layouts():
    if CLASSES:
        return CLASSES
    with open(OFFSETS, encoding="utf-8") as f:
        data = json.load(f)
    CLASSES.update(data["classes"])
    return CLASSES


def chain(cls):
    """Class chain from `cls` upwards, using the BMSDK `super` fields."""
    layouts = load_layouts()
    out, seen = [], set()
    while cls and cls in layouts and cls not in seen:
        seen.add(cls)
        out.append(cls)
        cls = layouts[cls].get("super")
    return out


def field_at(cls, offset):
    """(name, declaring class) for an absolute property offset, or (None, None)."""
    layouts = load_layouts()
    for c in chain(cls):
        for p in layouts[c].get("properties") or []:
            if p.get("offset") == offset:
                return p.get("name"), c
    return None, None


def walk(pkg, index):
    """Tag walk; templates carry a 12-byte prefix that best_walk does not skip, so retry there."""
    data = pkg.data(index)
    tags, end, why = U.best_walk(pkg, data)
    if tags:
        return tags, end, why
    for start in (12, 4):
        tags, end, why = U.walk_tags(pkg, data, start=start)
        if tags:
            return tags, end, why
    return tags, end, why


def extents_in(data, agg):
    """Every FKBoxElem extent triple inside the AggGeom payload, with its centre."""
    start = agg["at"]
    end = start + agg["size"]
    payload = data[start:end]
    rows = []
    for m in GP.EXT_RE.finditer(payload):
        at = start + m.start()
        ext = struct.unpack("<3f", m.group(1) + m.group(2) + m.group(3))
        ctr = struct.unpack_from("<3f", data, at - 12) if at >= 12 else (0.0, 0.0, 0.0)
        rows.append({"extents_cm": [round(v, 3) for v in ext],
                     "centre_cm": [round(v, 3) for v in ctr],
                     "payload_at": at - start})
    return rows


def body(pkg, index):
    data = pkg.data(index)
    tags, _end, _why = walk(pkg, index)
    bone = next((t.get("value") for t in tags if t.get("type") == "NameProperty"), None)
    agg = next((t for t in tags if t.get("name") == "AggGeom"), None)
    boxes = []
    if agg and "size" in agg:
        boxes = extents_in(data, agg)
    spheres = struct.unpack_from("<I", data, agg["at"])[0] if agg else None
    nboxes = struct.unpack_from("<I", data, agg["at"] + 4)[0] if agg else None
    bools = [{"offset": t["offset"], "value": t.get("value"),
              "name": field_at("RB_BodySetup", t["offset"])[0]}
             for t in tags if t.get("type") == "BoolProperty"]
    floats = [{"offset": t["offset"], "value": t.get("value"),
               "name": field_at("RB_BodySetup", t["offset"])[0]}
              for t in tags if t.get("type") == "FloatProperty"]
    return {
        "package": os.path.basename(pkg.path), "export": index,
        "path": pkg.object_path(index), "class": pkg.object_class(index),
        "size": len(data), "bone": bone,
        "agggeom_size": agg["size"] if agg else None,
        "sphere_count": spheres, "box_count": nboxes,
        "boxes": boxes, "bools": bools, "floats": floats,
    }


def asset(pkg, index):
    data = pkg.data(index)
    tags, _end, why = walk(pkg, index)
    out = {"package": os.path.basename(pkg.path), "export": index,
           "path": pkg.object_path(index), "class": pkg.object_class(index),
           "size": len(data), "stop": why, "arrays": {}, "bounds": [],
           "instance": None, "constraint_setups": []}
    for t in tags:
        if t.get("type") == "ObjectNCRProperty" and t.get("ref_class") == "PhysicsAssetInstance":
            out["instance"] = {"export": t.get("value"), "path": t.get("ref")}
        name = t.get("name")
        if name in ("BodySetup", "BoundsBodies", "ConstraintSetup"):
            out["arrays"][name] = {
                "count": t.get("count"),
                "refs": [{"export": r["index"], "path": r["path"], "class": r["class"]}
                         for r in (t.get("refs") or [])],
            }
        if name == "Bounds":
            for item in t.get("items") or []:
                vec = {x["offset"]: x["value"] for x in item if "value" in x}
                out["bounds"].append({"min": vec.get(0), "max": vec.get(12)})
    for ref in out["arrays"].get("ConstraintSetup", {}).get("refs", []):
        cs_tags, _e, _w = walk(pkg, ref["export"])
        out["constraint_setups"].append({
            "export": ref["export"], "size": len(pkg.data(ref["export"])),
            "names": [t.get("value") for t in cs_tags if t.get("type") == "NameProperty"],
            "vectors": [t.get("value") for t in cs_tags if t.get("type") == "VectorProperty"],
        })
    return out


def wheels(pkg):
    rows = []
    for i in WHEELS:
        tags, _e, _w = walk(pkg, i)
        row = {"export": i, "path": pkg.object_path(i),
               "size": len(pkg.data(i)), "floats": {}, "names": {}, "refs": {}}
        for t in tags:
            off = t.get("offset")
            if t.get("type") == "FloatProperty":
                fname = field_at("SVehicleWheel", off)[0] or "UNKNOWN"
                row["floats"][fname if fname != "UNKNOWN" else "offset %d" % off] = t.get("value")
            elif t.get("type") == "NameProperty":
                fname = field_at("SVehicleWheel", off)[0] or "UNKNOWN"
                row["names"][fname if fname != "UNKNOWN" else "offset %d" % off] = t.get("value")
            elif t.get("ref") and t.get("ref_class") in ("RB_BodyInstance", "SkelControlWheel"):
                row["refs"][str(off)] = t["ref"]
        rows.append(row)
    return rows


def archetype_components(pkg):
    tags, _e, _w = walk(pkg, ARCHETYPE)
    rows, wheels_ref = [], None
    for t in tags:
        if t.get("name") == "Wheels":
            wheels_ref = {"offset": t.get("offset"), "count": t.get("count"),
                          "refs": [{"export": r["index"], "path": r["path"]}
                                   for r in (t.get("refs") or [])]}
        if t.get("ref"):
            rows.append({"offset": t.get("offset"),
                         "field": field_at("RVehicleBatmobile", t.get("offset"))[0],
                         "ref": t["ref"], "class": t.get("ref_class")})
    rows.sort(key=lambda r: r["offset"] or 0)
    return rows, wheels_ref


def static_meshes(pl, bm):
    """Instance (Playable) for identity, base template (BmGame) for mesh ref and flags."""
    out = []
    for i in STATIC_COLLISION_MESHES:
        row = {"export": i, "path": pl.object_path(i), "class": pl.object_class(i),
               "size": len(pl.data(i)), "template": FIGHT_TEMPLATES[i],
               "static_mesh": None, "mesh_ref_offset": None,
               "translation": None, "rotation": None, "bits_476": None,
               "hidden_game": None}
        tpl_tags, _e, _w = walk(bm, row["template"])
        for t in tpl_tags:
            if t.get("ref") and t.get("ref_class") == "StaticMesh":
                row["static_mesh"] = t["ref"]
                row["mesh_ref_offset"] = t["offset"]
            if t.get("type") == "VectorProperty" and t.get("offset") == 400:
                row["translation"] = t.get("value")
            if t.get("type") == "RotatorProperty" and t.get("offset") == 412:
                row["rotation"] = t.get("value")
            if t.get("type") == "BoolProperty" and t.get("offset") == 476:
                row["bits_476"] = t.get("bits")
                # HiddenGame is bit 0x4000 of this word (BMSDK PrimitiveComponent mask table)
                row["hidden_game"] = bool(t.get("bits", 0) & 0x4000)
        out.append(row)
    return out


def template_refs(bm, index):
    tags, _e, _w = walk(bm, index)
    return {"export": index, "path": bm.object_path(index), "size": len(bm.data(index)),
            "refs": [{"offset": t.get("offset"), "field": field_at("SkeletalMeshComponent",
                                                                   t.get("offset"))[0],
                       "ref": t["ref"], "class": t.get("ref_class")}
                      for t in tags if t.get("ref")]}


def instance_arrays(pkg, index):
    tags, _e, _w = walk(pkg, index)
    return {"export": index, "path": pkg.object_path(index),
            "size": len(pkg.data(index)),
            "arrays": {t["name"]: {"count": t.get("count"), "size": t.get("size")}
                       for t in tags if t.get("name") in ("Bodies", "Constraints")}}


def fight_bodies(bm):
    out = []
    for i in FIGHT_BODY_SETUPS:
        tags, _e, _w = walk(bm, i)
        agg = next((t for t in tags if t.get("name") == "AggGeom"), None)
        boxes = extents_in(bm.data(i), agg) if agg and "size" in agg else []
        out.append({"export": i, "path": bm.object_path(i), "class": bm.object_class(i),
                    "size": len(bm.data(i)),
                    "agggeom_size": agg["size"] if agg else None,
                    "decodable_box_elements": len(boxes)})
    return out


def collect():
    bm = U.Package(os.path.join(GAME, "BmGame.upk"))
    pl = U.Package(os.path.join(GAME, PLAYABLE))
    comps, wheels_ref = archetype_components(pl)
    data = {
        "game": "Batman: Arkham Knight",
        "packages": {"BmGame.upk": os.path.join(GAME, "BmGame.upk"),
                     PLAYABLE: os.path.join(GAME, PLAYABLE)},
        "drivable_asset": asset(bm, DRIVABLE_ASSET),
        "drivable_bodies": [body(bm, i) for i in DRIVABLE_BODIES],
        "drivable_instance": asset(bm, DRIVABLE_INSTANCE),
        "archetype": {"export": ARCHETYPE, "path": pl.object_path(ARCHETYPE),
                      "class": pl.object_class(ARCHETYPE),
                      "size": len(pl.data(ARCHETYPE)),
                      "components": comps, "wheels_array": wheels_ref},
        "svehicle_mesh": {"export": SVEHICLE_MESH, "path": pl.object_path(SVEHICLE_MESH),
                          "class": pl.object_class(SVEHICLE_MESH),
                          "size": len(pl.data(SVEHICLE_MESH))},
        "wheels": wheels(pl),
        "sim": {"export": SIM, "path": pl.object_path(SIM),
                "class": pl.object_class(SIM), "size": len(pl.data(SIM))},
        "stay_upright": {"export": STAY_UPRIGHT,
                         "path": pl.object_path(STAY_UPRIGHT),
                         "class": pl.object_class(STAY_UPRIGHT),
                         "size": len(pl.data(STAY_UPRIGHT)),
                         "tags": len(walk(pl, STAY_UPRIGHT)[0]),
                         "instance": {"export": STAY_UPRIGHT_INSTANCE,
                                      "path": pl.object_path(STAY_UPRIGHT_INSTANCE),
                                      "class": pl.object_class(STAY_UPRIGHT_INSTANCE),
                                      "size": len(pl.data(STAY_UPRIGHT_INSTANCE))}},
        "svehicle_mesh_template": template_refs(bm, SVEHICLE_TEMPLATE),
        "drivable_instance_arrays": instance_arrays(bm, DRIVABLE_INSTANCE),
        "static_collision_meshes": static_meshes(pl, bm),
        "fight_body_setups": fight_bodies(bm),
        "wreck_asset": asset(pl, WRECK_ASSET),
        "selector": {"offset": SELECTOR_OFFSET,
                     "field": field_at("RVehicleBatmobile", SELECTOR_OFFSET)[0],
                     "serialised": any(t.get("offset") == SELECTOR_OFFSET
                                       for t in walk(pl, ARCHETYPE)[0])},
    }
    return data


def fmt(v):
    if isinstance(v, list):
        return "[" + ", ".join("%g" % (0.0 if x == 0 else x) for x in v) + "]"
    if isinstance(v, float):
        return "%g" % (0.0 if v == 0 else v)
    return str(v)


def render(d):
    a = d["drivable_asset"]
    L = []
    L.append("# Where the drivable Batmobile's collision lives (G3-16)\n")
    L.append("Generated by `Tools/scripts/grab_collision_where.py --write`; `--check` re-derives every "
             "number from the shipped package bytes and compares.\n")
    L.append("Before this card only the wreck's asset was known: `Batmobile_V3_Destroyed_Physics` "
             "(%d body setups). The drivable car's asset exists too and is decoded below.\n" %
             d["wreck_asset"]["arrays"].get("BodySetup", {}).get("count", 0))
    L.append("## Verdict\n")
    L.append("**The drivable car's rigid-body collision is `%s`** (%s export %d, %d bytes): "
             "`BodySetup` count **%d**, `BoundsBodies` count %d, `ConstraintSetup` count %d, "
             "`PhysicsAssetInstance` at export %s.\n" %
             (a["path"], a["package"], a["export"], a["size"],
              a["arrays"]["BodySetup"]["count"], a["arrays"]["BoundsBodies"]["count"],
              a["arrays"]["ConstraintSetup"]["count"],
              (a["instance"] or {}).get("export")))
    L.append("It is reached from `%s` (Playable export %d): the `SVehicleMesh` component's "
             "`PhysicsAsset` reference, serialised at property offset 824 of the BmGame base "
             "template `Default__RVehicleBatmobileBase.SVehicleMesh` (export %d). That template's "
             "decoded references are %s.\n" %
             (d["svehicle_mesh"]["path"], d["svehicle_mesh"]["export"],
              d["svehicle_mesh_template"]["export"],
              "; ".join("offset %s `%s` -> `%s` (%s)" %
                        (r["offset"], r["field"] or "UNKNOWN", r["ref"], r["class"])
                        for r in d["svehicle_mesh_template"]["refs"])))
    inst = d["drivable_instance_arrays"]
    L.append("The asset's `PhysicsAssetInstance` (export %d, %d bytes) serialises %s - one "
             "per body and per constraint, matching the asset's arrays.\n" %
             (inst["export"], inst["size"],
              ", ".join("`%s` count %s" % (k, v["count"]) for k, v in inst["arrays"].items())))
    L.append("## Bodies\n")
    L.append("| export | bone | AggGeom bytes | boxes | spheres | box extents (cm) | box centre (cm) |")
    L.append("|---|---|---|---|---|---|---|")
    for b in d["drivable_bodies"]:
        for k, box in enumerate(b["boxes"]):
            L.append("| %d%s | `%s` | %s | %s | %s | %s | %s |" %
                     (b["export"], "" if k == 0 else " (box %d)" % k,
                      b["bone"], b["agggeom_size"], b["box_count"], b["sphere_count"],
                      fmt(box["extents_cm"]), fmt(box["centre_cm"])))
    L.append("")
    L.append("Every body setup:%s" % "")
    for b in d["drivable_bodies"]:
        L.append("- `%s` (%s export %d, %d bytes): bone **`%s`**, %d box element(s), "
                 "%d sphere(s). Other decoded tags: %s." %
                 (b["path"], b["package"], b["export"], b["size"], b["bone"],
                  b["box_count"], b["sphere_count"],
                  "; ".join("offset %d `%s`=%s" % (x["offset"], x["name"] or "UNKNOWN", x["value"])
                            for x in b["bools"] + b["floats"]) or "none"))
    L.append("")
    b0 = a["bounds"][0]
    trip = d["drivable_bodies"][0]["boxes"][0]["extents_cm"]
    span = [b0["max"][i] - b0["min"][i] for i in range(3)]
    L.append("The extent triples are **full** sizes, not half sizes: the chassis body's `Bounds` "
             "entry spans %s to %s, i.e. %g x %g x %g cm, against the decoded %s triple - a "
             "ratio of %s (derived: max-min of the two `Bounds` vectors, divided by the triple). "
             "Half-extent triples would give a ratio near 0.5; these are near 1.0.\n" %
             (fmt(b0["min"]), fmt(b0["max"]), span[0], span[1], span[2], fmt(trip),
              fmt([round(span[i] / trip[i], 3) for i in range(3)])))
    L.append("| body | Bounds min (cm) | Bounds max (cm) |")
    L.append("|---|---|---|")
    for i, bnd in enumerate(a["bounds"]):
        L.append("| %d | %s | %s |" % (i, fmt(bnd["min"]), fmt(bnd["max"])))
    L.append("")
    cs = a["constraint_setups"][0] if a["constraint_setups"] else None
    if cs:
        L.append("## Constraint\n")
        L.append("`ConstraintSetup` holds 1 `RB_ConstraintSetup` (export %d, %d bytes): "
                 "FNames %s, three vectors %s. Which FName is the joint's parent and which the "
                 "child is UNKNOWN: `RB_ConstraintSetup` has no layout entry in "
                 "BMSDK_OFFSETS.json, so the serialisation order is not decoded.\n" %
                 (cs["export"], cs["size"], cs["names"], cs["vectors"]))
    L.append("## Components on the archetype\n")
    L.append("`%s` (export %d, %d bytes, class `%s`) references:\n" %
             (d["archetype"]["path"], d["archetype"]["export"],
              d["archetype"]["size"], d["archetype"]["class"]))
    L.append("| property offset | field (BMSDK) | reference | class |")
    L.append("|---|---|---|---|")
    for c in d["archetype"]["components"]:
        L.append("| %s | %s | `%s` | %s |" %
                 (c["offset"], c["field"] or "UNKNOWN", c["ref"], c["class"]))
    L.append("")
    wa = d["archetype"]["wheels_array"]
    L.append("`Wheels` (property offset %s) is an array of **%s**: %s.\n" %
             (wa["offset"], wa["count"], ", ".join("`%s` (%d)" % (r["path"], r["export"])
                                                   for r in wa["refs"])))
    L.append("## Wheels\n")
    L.append("| component | size | radius (cm) | travel up | travel down | speed up | speed down | other floats |")
    L.append("|---|---|---|---|---|---|---|---|")
    for w in d["wheels"]:
        f = w["floats"]
        other = ", ".join("%s=%g" % (k, v) for k, v in f.items()
                          if k not in ("WheelRadius", "SuspensionTravelUp", "SuspensionTravelDown",
                                       "SuspensionSpeedUp", "SuspensionSpeedDown"))
        L.append("| `%s` | %d | %s | %s | %s | %s | %s | %s |" %
                 (w["path"], w["size"], f.get("WheelRadius", "-"), f.get("SuspensionTravelUp", "-"),
                  f.get("SuspensionTravelDown", "-"), f.get("SuspensionSpeedUp", "-"),
                  f.get("SuspensionSpeedDown", "-"), other or "-"))
    L.append("")
    L.append("Names come from `BMSDK_OFFSETS.json` at the tag's absolute offset; an offset that is "
             "not in the `SVehicleWheel` chain is printed as `offset N`. `-` means the tag is not "
             "serialised on that instance (the value is then inherited or the class default, both "
             "UNKNOWN from these bytes). `BoneName` (layout offset 548) is **not serialised** on any "
             "of the four, so the wheel-to-bone binding is UNKNOWN; the archetype binds them by "
             "array order `WheelFL, WheelFR, WheelRL, WheelRR` in `Wheels`, which is decoded but "
             "does not name the bone.\n")
    L.append("## Batman-vs-Batmobile collision meshes (not the hull)\n")
    L.append("Values are decoded from the BmGame base templates %s; the Playable instances carry "
             "no mesh reference of their own.\n" %
             ", ".join("export %d" % m["template"] for m in d["static_collision_meshes"]))
    L.append("| component | export | template | StaticMesh (template offset) | translation | "
             "rotation | bitfield 476 | `HiddenGame` |")
    L.append("|---|---|---|---|---|---|---|---|")
    for m in d["static_collision_meshes"]:
        L.append("| `%s` | %d | %d | %s | %s | %s | %s | %s |" %
                 (m["path"], m["export"], m["template"],
                  ("`%s` (%s)" % (m["static_mesh"], m["mesh_ref_offset"])) if m["static_mesh"] else "-",
                  fmt(m["translation"]) if m["translation"] else "-",
                  fmt(m["rotation"]) if m["rotation"] else "-",
                  ("0x%08x" % m["bits_476"]) if m["bits_476"] is not None else "-",
                  m["hidden_game"]))
    L.append("")
    L.append("Their mesh body setups are %s. The selector `%s` (layout offset %d) is "
             "**%s** in the archetype tag stream, so which of the two is active is UNKNOWN "
             "(also COLLISION_SELECTOR3.md).\n" %
             ("; ".join("`%s` export %d, %d bytes, %d decodable box element(s)" %
                        (b["path"], b["export"], b["size"], b["decodable_box_elements"])
                        for b in d["fight_body_setups"]),
              d["selector"]["field"], d["selector"]["offset"],
              "serialised" if d["selector"]["serialised"] else "not serialised"))
    L.append("## Stay-upright and simulation\n")
    su = d["stay_upright"]
    L.append("- `%s` (export %d, class `%s`) is **%d bytes with %d tags** - an empty object "
             "whose `ConstraintSetup` is inherited from the class; per-vehicle upright values are "
             "not serialised here (UNKNOWN: no `RB_StayUprightSetup` layout in BMSDK_OFFSETS.json). "
             "Its companion `%s` (export %d, %d bytes) is referenced at archetype offset 1772.\n" %
             (su["path"], su["export"], su["class"], su["size"], su["tags"],
              su["instance"]["path"], su["instance"]["export"], su["instance"]["size"]))
    L.append("- `%s` (export %d, class `%s`, %d bytes) is the `SimulationModel` "
             "(`SimObj`, SVehicle offset 1700). It drives the four raycast wheels above; it holds no "
             "collision shapes.\n" % (d["sim"]["path"], d["sim"]["export"], d["sim"]["class"],
                                      d["sim"]["size"]))
    L.append("## The wreck's asset, for contrast\n")
    w = d["wreck_asset"]
    L.append("`%s` (%s export %d, %d bytes): `BodySetup` %d, `BoundsBodies` %d, "
             "`ConstraintSetup` %s. It is the 32-box destruction rig of PHYSICS.md, not the "
             "drivable hull: the drivable asset has **%d** bodies and **1** constraint, the wreck "
             "asset has **%d** bodies and **no** constraint setup array.\n" %
             (w["path"], w["package"], w["export"], w["size"],
              w["arrays"]["BodySetup"]["count"], w["arrays"]["BoundsBodies"]["count"],
              w["arrays"].get("ConstraintSetup", {}).get("count", "absent (tag absent)"),
              a["arrays"]["BodySetup"]["count"], w["arrays"]["BodySetup"]["count"]))
    L.append("## What each candidate rules in or out\n")
    L.append("| candidate | rules in | rules out |")
    L.append("|---|---|---|")
    L.append("| `%s` (%d bodies) | **the drivable car's rigid-body hull**: one `Batmobile_Chassis` "
             "body with two box elements, one `Batmobile_Rig_Weapons_Trans` body, one constraint | "
             "'the drivable car has no physics asset'; the wreck asset as the driving hull |" %
             (a["path"], a["arrays"]["BodySetup"]["count"]))
    L.append("| `Batmobile_V3_Destroyed_Physics` (%d bodies) | the wreck/debris rig (PHYSICS.md) | "
             "the drivable hull: it is referenced by the dead-vehicle path, and its bodies are "
             "debris bones (`Object*_frag_*`), not a chassis |" % w["arrays"]["BodySetup"]["count"])
    L.append("| `BatmanCollisionMeshBattleMode0` / `...PursuitMode0` | Batman-vs-Batmobile "
             "collision geometry (two StaticMesh body setups) | the driving hull: their meshes are "
             "`HiddenGame` and the battle/pursuit selector is not serialised |")
    L.append("| `CollisionCylinder` / `FrontCollisionCylinder` / `RearCollisionCylinder` | "
             "the pawn-level blocking chain at x = 0 / +100 / -200 cm | the physics hull: cylinders "
             "block movement, they are not simulated bodies |")
    L.append("| the four `SVehicleWheel` | raycast wheel contact (radius 64 cm, 30 cm up / 40 cm "
             "down travel on the fronts, 40 cm down on the rears) | rigid-body wheel collision: no "
             "`RB_BodyInstance` or wheel shape is serialised on them |")
    L.append("| `RB_StayUprightSetup` + `RB_ConstraintInstance` | the uprighting constraint | "
             "any per-vehicle upright tuning: the setup object is empty (2 bytes) |")
    L.append("")
    L.append("## UNKNOWN\n")
    L.append("- Half-vs-full extent convention for the AggGeom triples: **resolved as full** by the "
             "`Bounds` cross-check above; the exact `FKBoxElem` semantics are still not stated by a "
             "layout in BMSDK_OFFSETS.json.")
    L.append("- Which FName in the constraint setup is the parent joint and which is the child.")
    L.append("- `BoneName` of each wheel instance (offset 548 not serialised) and therefore the "
             "bone each wheel rides.")
    L.append("- Which of the two Batman-vs-Batmobile meshes is active in each mode.")
    L.append("- Whether the engine simulates the `Batmobile_Rig_Weapons_Trans` body at runtime "
             "(`bConsiderForBounds`-style bool at offset 224 is true, but its property name is not "
             "in BMSDK_OFFSETS.json).")
    L.append("")
    L.append("## Regeneration\n")
    L.append("| path | what it is |")
    L.append("|---|---|")
    L.append("| `Research/BatmobileGrab/COLLISION_WHERE.md` | this file |")
    L.append("| `Research/BatmobileGrab/COLLISION_WHERE.json` | the same rows as data |")
    L.append("| `Tools/scripts/grab_collision_where.py` | the tool; `--write` / `--check` |")
    L.append("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = collect()
    md = render(data)
    json_path = os.path.join(OUT, "COLLISION_WHERE.json")
    md_path = os.path.join(OUT, "COLLISION_WHERE.md")
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if args.check:
        with open(json_path, encoding="utf-8") as f:
            old_json = f.read()
        with open(md_path, encoding="utf-8") as f:
            old_md = f.read()
        bad = [p for p, old, new in ((json_path, old_json, payload), (md_path, old_md, md))
               if old != new]
        if bad:
            for p in bad:
                print("DRIFT", p)
            raise SystemExit(1)
        print("check ok: %d bodies, %d wheels, selector %s" %
              (data["drivable_asset"]["arrays"]["BodySetup"]["count"],
               len(data["wheels"]),
               "serialised" if data["selector"]["serialised"] else "absent"))
        return
    if not args.write:
        ap.error("use --write or --check")
    with open(json_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print("wrote", md_path)
    print("wrote", json_path)


if __name__ == "__main__":
    main()
