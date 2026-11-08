"""Independent re-derivation for G2-31 (does not import jc3water).

Reads the donor / APC / duck straight out of the archives with jc3grab + jc3detail + jc3adf,
reads the shared `vehicle_common.vmodc` the same way, and re-counts the fleet from the decoded
cache by hand.
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, "Tools/scripts")
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402

rows = [json.loads(l) for l in open("Research/JC3Grab/INDEX.jsonl", encoding="utf-8")]
EES = {
    "donor": "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
             "v0300_car_kensington_sportsmuscle_civilian_01.ee",
    "apc": "editor/entities/jc_vehicles/01_land/v0200_car_capstone_apc/"
           "v0200_car_capstone_apc_military_01.ee",
    "duck": "editor/entities/jc_vehicles/03_sea/v1717_boat_na_duck/"
            "v1717_boat_na_duck_civilian_01.ee",
    "common": "editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc",
}


def files(ee):
    entry = jc3grab.resolve(ee, rows)
    stream, inner = jc3detail.inner_files(jc3grab.read_entry(entry, jc3grab.DEFAULT_GAME))
    return stream, inner


def walk(stream, inner, suffix):
    hit = next((e for e in inner if e[0].endswith(suffix)), None)
    if hit is None:
        return None
    return {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]]))}


out = {}
for key in ("donor", "apc", "duck"):
    stream, inner = files(EES[key])
    out[key + "_inner_files"] = len(inner)
    wi = walk(stream, inner, "water_interaction.vmodc") or {}
    bu = walk(stream, inner, "buoyancy.vmodc") or {}
    bb = walk(stream, inner, "boat_buoyancy.vmodc") or {}
    parts = {p.split("[")[1].split("]")[0] for p in wi if p.startswith("part_elements[")}
    out[key] = {
        "will_sink": wi.get("will_sink"),
        "buoyancy": bu.get("buoyancy"),
        "drag": bu.get("drag"),
        "radius": round(bu.get("radius"), 6) if bu.get("radius") is not None else None,
        "bottom_area": bu.get("bottom_area"),
        "hull_parts": len(parts),
        "from_part": (wi.get("part_elements[0].from_part.string")
                      if "part_elements[0].from_part.string" in wi else None),
        "boat_buoyancy": bool(bb),
        "base_buoyancy": bb.get("base_buoyancy"),
        "pontoon_modules": len({p.split("[")[1].split("]")[0] for p in bb
                                if p.startswith("buoyancy_modules[")}) if bb else None,
    }

# vehicle_common.vmodc is embedded in every EE, not a standalone archive entry
stream, inner = files(EES["donor"])
vc = walk(stream, inner, "/modules/vehicle_common.vmodc") or {}
out["constants"] = {k: vc.get(k) for k in (
    "vehicle_damage.min_water_entry_ms", "vehicle_damage.fatal_water_entry_ms",
    "vehicle_damage.min_water_entry_floating_ms",
    "vehicle_damage.fatal_water_entry_floating_ms",
    "car_common.engine_shut_down_delay_s", "boat_common.engine_shut_down_delay_s",
    "plane_common.engine_shut_down_delay_s")}

cache = [json.load(open(p, encoding="utf-8"))
         for p in sorted(glob.glob("E:/Modding/_JC3grab/entities/*.ee.json"))]
groups = collections.Counter()
common_files = set()
for d in cache:
    mods = {}
    for m in d["modules"]:
        mods.setdefault(m.get("type"), []).append(m)
    ws = None
    for m in mods.get("WaterInteraction", []):
        for r in m["rows"]:
            if r["path"] == "will_sink":
                ws = r["value"]
    groups["boat" if "BoatBuoyancy" in mods else
           ("sink" if ws == 1 else "floating")] += 1
    for m in mods.get("VehicleCommon", []):
        common_files.add(m.get("file"))
out["cache_entities"] = len(cache)
out["cache_groups"] = dict(groups)
out["vehicle_common_files"] = sorted(common_files)
print(json.dumps(out, indent=1, sort_keys=True))
