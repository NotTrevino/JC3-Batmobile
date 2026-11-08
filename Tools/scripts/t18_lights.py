"""t18_lights.py - T-18: every light of the Batmobile rig, mapped or named out.

The card (`GRAB_BACKLOG.md` §7, `#### T-18`) asks for one thing above all:

    Done: every light entry of the `Batmobile` rig (28) maps to an `SVehicleLight`
    or a named omission (forensics rig stays out).

So this tool walks the 28 entries of `Playable_Batmobile_SF/Batmobile_Archetypes.Vehicle`
in `Research/BatmobileGrab/LIGHTS.json` (G1-17) - in file order, one row each, ids
`T-L8`…`T-L35` - and resolves each one against the JC3 side that is already on disk:

  * `Working/Lights/v082/lights.xml`   the donor vehicle's `VehicleDynamicLights`
                                       module: 21 rows, 25 members each (G2-33)
  * `Working/Lights/v082/entity.xml`   the donor entity's graph: 22 `SVehicleLight`
                                       objects, addressed by preset name (G2-33)
  * `Research/JC3Grab/LIGHT_SYSTEM.json`  the G2-33 custom-entry recipe (25 members
                                       with a class and a source each) and the
                                       behaviour vocabulary the fleet actually uses
  * `Research/JC3Grab/PARTS_TABLE.jsonl`  part_index / has_lights / damage type

A row's target is therefore one of three things, never a fourth:

  donor row       keep one of the 21 shipped rows, repoint its part and anchor at
                  the BmAK socket (the donor hangs its lamps on `sportsmuscle_*_light_*`
                  parts our entity does not expose - LGT1_FINDINGS §2)
  graph object    an `SVehicleLight` the donor graph instantiates but no row
                  references (`Front_Secondary_Head` is the battle-mode spot, T-L5)
  custom          a `preset_id = 0` entry built from the G2-33 recipe, for the lamps
                  JC3 has no preset for (wheel arch, battle-mode heads, boot light)

Everything else is a named omission with the proof in the row.

Two rules decide the numeric cells:

  * **the colour is adopted** - `LightColor` (FColor, BGRA) / 255 -> `diffuse.R/G/B`,
    the same conversion G2-33's recipe uses;
  * **intensity and cone are reported, not converted** - the BmAK side is a UE
    `SpotLightComponent` (Brightness 0..5, cone degrees, Radius in UE units) and the
    JC3 side is `range`/`angle`/`multiplier` in units no file states (G2-33 §8).
    A conversion would be a guess, so the row prints both and keeps the shipped
    number (R4). This is the same call T-17 made for effect sizes.

Usage:
  python t18_lights.py --write      write T14_LIGHTS.md + t14_lights.json
  python t18_lights.py --check      re-derive, compare both files, assert the table
  python t18_lights.py show T-L8    one row, with every input value it used
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import rbmhdr  # noqa: E402
from t5_apply import paths  # noqa: E402

WORK = os.path.join(ROOT, "Working", "Translation")
OUT_JSON = os.path.join(WORK, "t14_lights.json")
OUT_MD = os.path.join(WORK, "T14_LIGHTS.md")
LIGHTS = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.json")
DONOR_MODULE = os.path.join(ROOT, "Working", "Lights", "v082", "lights.xml")
DONOR_GRAPH = os.path.join(ROOT, "Working", "Lights", "v082", "entity.xml")
LIGHT_SYSTEM = os.path.join(ROOT, "Research", "JC3Grab", "LIGHT_SYSTEM.json")
PARTS = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
DONOR_EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"

RIG = "Playable_Batmobile_SF"
M32 = 0xFFFFFFFF
FIRST_ID = 8  # T-L8 is entry 0

FLOATS = {"diffuse.R", "diffuse.G", "diffuse.B", "range", "falloff_start", "near_cap",
          "multiplier", "min_luminosity", "angle", "volume_intensity", "uvscale.u",
          "uvscale.v"}
INTS = {"behavior_hash", "part_hash", "part_index", "light_type", "blinking",
        "cast_shadows", "projected_texture_index", "volumetric_mode",
        "deformable_transform_hash", "preset_id"}


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def hname(name: str) -> int:
    return rbmhdr.hash_jenkins(name.encode("utf-8"))


# --------------------------------------------------------------------------
# inputs


def load_entries() -> list[dict]:
    data = json.load(open(LIGHTS, encoding="utf-8"))
    rig = [v for v in data["vehicles"] if v["package"] == RIG]
    if len(rig) != 1:
        raise SystemExit(f"{RIG}: {len(rig)} rigs in {rel(LIGHTS)}")
    return rig[0]["entries"]


def load_module() -> list[dict]:
    table = paths(ET.parse(DONOR_MODULE).getroot().find("instances/instance"))
    flat = {k: (v.text if hasattr(v, "text") else v) for k, v in table.items()}
    idx = sorted({int(m.group(1)) for k in flat if (m := re.match(r"lights\[(\d+)\]", k))})
    rows = []
    for i in idx:
        raw = {k.split(".", 1)[1]: v for k, v in flat.items() if k.startswith(f"lights[{i}].")}
        row: dict = {"index": i}
        for k, v in raw.items():
            if k in FLOATS:
                row[k] = float(v)
            elif k in INTS:
                row[k] = int(v)
            else:
                row[k] = v
        rows.append(row)
    return rows


def load_graph() -> list[dict]:
    objects = []
    for o in ET.parse(DONOR_GRAPH).getroot().iter("object"):
        vals = {v.get("name"): (v.text or "") for v in o.findall("value") if v.get("name")}
        if vals.get("_class") != "SVehicleLight":
            continue
        diffuse = [float(x) for x in vals["diffuse"].split(",")] if vals.get("diffuse") else []
        objects.append({
            "name": vals.get("name") or o.get("name"),
            "hash": int(vals["name_hash"]) & M32,
            "diffuse": diffuse,
            "radius": float(vals["radius"]) if vals.get("radius") else None,
            "spot_angle": float(vals["spot_angle"]) if vals.get("spot_angle") else None,
            "spot_inner_angle": (float(vals["spot_inner_angle"])
                                 if vals.get("spot_inner_angle") else None),
            "multiplier": float(vals["multiplier"]) if vals.get("multiplier") else None,
            "volume_intensity": (float(vals["volume_intensity"])
                                 if vals.get("volume_intensity") else None),
            "volumetric_mode": (int(vals["volumetric_mode"])
                                if vals.get("volumetric_mode") else None),
            "near_cap": float(vals["near_cap"]) if vals.get("near_cap") else None,
            "enabled": int(vals["enabled"]) if vals.get("enabled") else None,
        })
    return objects


def load_parts() -> list[dict]:
    for line in open(PARTS, encoding="utf-8"):
        row = json.loads(line)
        if row["entity"].endswith("/" + DONOR_EE):
            return row["parts"]
    raise SystemExit(f"{rel(PARTS)}: no {DONOR_EE}")


def load_recipe() -> dict:
    return json.load(open(LIGHT_SYSTEM, encoding="utf-8"))


# --------------------------------------------------------------------------
# the BmAK side of one entry


def light_component(entry: dict) -> dict | None:
    for c in entry["components"]:
        if c["class"] in ("SpotLightComponent", "PointLightComponent",
                          "RHelicopterSpotLightComponent"):
            return c
    return None


def bmak_facts(entry: dict) -> dict:
    comp = light_component(entry)
    fields = (comp or {}).get("fields", {})
    colour = None
    colour_field = None
    for c in entry["components"]:
        if c.get("colour") and isinstance(c["colour"].get("value"), list) \
                and len(c["colour"]["value"]) == 4 and c["colour"]["value"][0] > 1.0:
            colour = [int(round(x)) for x in c["colour"]["value"]]
            colour_field = c["colour"]["field"]
            break
    return {
        "component_class": comp["class"] if comp else None,
        "components": [c["class"] for c in entry["components"]],
        "colour": colour,
        "colour_field": colour_field,
        "brightness": fields.get("Brightness"),
        "cone_inner": fields.get("InnerConeAngle"),
        "cone_outer": fields.get("OuterConeAngle"),
        "radius_ue": fields.get("Radius"),
        "falloff": fields.get("FalloffExponent"),
    }


def side_of(socket: str) -> str | None:
    m = re.search(r"([12])\s*[a-c]?$", socket)
    if m:
        return "left" if m.group(1) == "1" else "right"
    if socket.endswith("_L"):
        return "left"
    if socket.endswith("_R"):
        return "right"
    return None


# --------------------------------------------------------------------------
# resolution


def resolve(entries: list[dict], module: list[dict], graph: list[dict],
            parts: list[dict], system: dict) -> tuple[list[dict], list[dict], dict]:
    by_hash = {o["hash"]: o for o in graph}
    row_of = {}
    for r in module:
        row_of.setdefault(r["preset_id"], r)
    part_of = {p["n"]: p for p in parts}
    template = system["recipe"]["light"]["rows"]
    part_template = system["recipe"]["part"]["rows"]
    part_rows = len(parts)
    behaviours = system["module"]["behaviors"]

    rows: list[dict] = []
    custom: list[dict] = []

    def donor(target_name: str, what: str) -> dict | None:
        h = hname(target_name)
        row = row_of.get(h)
        if row is None:
            return None
        return {"kind": "donor-row", "what": what, "name": target_name,
                "preset_id": h, "module_rows": [row["index"]],
                "row": row, "object": by_hash.get(h)}

    def graph_only(target_name: str, what: str) -> dict:
        h = hname(target_name)
        return {"kind": "graph-object", "what": what, "name": target_name,
                "preset_id": h, "module_rows": [],
                "row": row_of.get(h), "object": by_hash.get(h)}

    def existing_custom(name: str) -> dict | None:
        for c in custom:
            if c["name"] == name:
                return c
        return None

    def wheel_row(entry: dict, side: str, battle: bool = False) -> dict:
        part_name = entry["jc3_part"]
        new_part = f"{part_name}_arch"
        name = new_part + ("_battle" if battle else "")
        done = existing_custom(name)
        if done is not None:
            return {"kind": "custom", "what": "wheel arch", "name": name,
                    "preset_id": 0, "module_rows": [], "row": None, "object": None,
                    "custom": done}
        shared_part = existing_custom(new_part)
        if shared_part is not None:
            new_index = next(r["v"] for r in shared_part["part"] if r["f"] == "part_index")
            index_src = (f"the arch part created for `{shared_part['name']}` keeps index "
                         f"{new_index}: this entry hangs its light on the same part")
        else:
            new_index = part_rows + sum(1 for c in custom if c["part"])
            index_src = (f"{rel(PARTS)} donor parts module: {part_rows} records 0.."
                         f"{part_rows - 1}; the arch part is new part "
                         f"#{new_index - part_rows + 1} of this card, so index {new_index} - "
                         "writing it needs the re-encode of MODLOG §101b")
        light_rows = []
        for t in template:
            m = t["m"]
            if m == "behavior":
                light_rows.append({"m": m, "v": entry["behavior"],
                                   "class": "decoded",
                                   "src": f"{rel(LIGHTS)} {entry['socket']} "
                                          f"({entry['type']} -> {entry['behavior']}, G1-17)"})
            elif m == "behavior_hash":
                light_rows.append({"m": m, "v": hname(entry["behavior"]),
                                   "class": "derived (verified)",
                                   "src": "rbmhdr.hash_jenkins(behaviour); reproduces all "
                                          "3,217 shipped behavior_hash values"})
            elif m == "part":
                light_rows.append({"m": m, "v": new_part, "class": "derived",
                                   "src": f"new part named after {part_name} (G2-33 §7b)"})
            elif m == "part_hash":
                light_rows.append({"m": m, "v": hname(new_part), "class": "derived (verified)",
                                   "src": "rbmhdr.hash_jenkins(part); reproduces all 3,217 "
                                          "shipped part_hash values"})
            elif m == "part_index":
                light_rows.append({"m": m, "v": new_index, "class": "derived",
                                   "src": index_src})
            elif m.startswith("diffuse."):
                k = "RGB".index(m[-1])
                light_rows.append({"m": m, "v": round(entry_colour(entry)[k] / 255.0, 6),
                                   "class": "derived",
                                   "src": f"{rel(LIGHTS)} {entry['socket']} LightColor "
                                          f"{entry_colour(entry)} / 255 (sRGB -> 0..1)"})
            elif m == "deformable_transform":
                light_rows.append({"m": m, "v": entry["jc3_anchor"], "class": "decoded (mapped)",
                                   "src": f"{rel(LIGHTS)} {entry['socket']}.jc3_anchor "
                                          f"(BmAK socket chain, bone {entry['bone']})"})
            elif m == "deformable_transform_hash":
                light_rows.append({"m": m, "v": hname(entry["jc3_anchor"]),
                                   "class": "derived (verified)",
                                   "src": "rbmhdr.hash_jenkins(anchor); reproduces all 3,217 "
                                          "shipped deformable_transform_hash values"})
            elif m == "preset_id":
                light_rows.append({"m": m, "v": 0, "class": "decoded",
                                   "src": "17 shipped entries carry preset_id 0 and every entry "
                                          "states its own numbers (G2-33 §3)"})
            else:
                light_rows.append({"m": m, "v": t["v"], "class": t["class"],
                                   "src": "G2-33 §7a recipe, copied from the donor's shipped "
                                          "steady HeadLight point lamp (module lights[2])"})
        part_rows_out = None if shared_part is not None else []
        for t in part_template:
            if part_rows_out is None:
                break
            f = t["f"]
            if f == "name":
                part_rows_out.append({"f": f, "v": new_part, "class": "derived",
                                      "src": f"named after the part it hangs on ({part_name})"})
            elif f == "parent":
                part_rows_out.append({"f": f, "v": part_of[part_name]["i"], "class": "decoded",
                                      "src": f"{rel(PARTS)} donor: {part_name} at part_index "
                                             f"{part_of[part_name]['i']}"})
            elif f == "part_index":
                part_rows_out.append({"f": f, "v": new_index, "class": "derived",
                                      "src": f"{rel(PARTS)}: {part_rows} records 0.."
                                             f"{part_rows - 1}; this is new part #"
                                             f"{new_index - part_rows + 1} of this card, so "
                                             f"index {new_index} (needs the §101b re-encode)"})
            elif f == "has_lights":
                part_rows_out.append({"f": f, "v": 1, "class": "decoded",
                                      "src": f"the donor wheel part ships {part_of[part_name]['lights']} "
                                             f"({rel(PARTS)}); 2,073 fleet parts ship 1"})
            elif f == "damage_type":
                part_rows_out.append({"f": f, "v": "Land_Light", "class": "decoded",
                                      "src": "the donor's lit parts by damage type: Land_Light "
                                             "x10 (G2-33 §7b)"})
            elif f == "parent_space_offset":
                part_rows_out.append({"f": f, "v": entry["socket_location"], "class": "decoded",
                                      "src": f"{rel(LIGHTS)} {entry['socket']}.socket_location "
                                             "(BmAK cm); goes through T(p) of bat_assemble.py at "
                                             "build time (R2), so this is the pre-transform source"})
            else:
                part_rows_out.append({"f": f, "v": t["v"], "class": t["class"],
                                      "src": t["src"]})
        record = {"name": name, "socket": entry["socket"], "side": side,
                  "host_part": part_name, "part_name": new_part,
                  "light": light_rows, "part": part_rows_out}
        custom.append(record)
        return {"kind": "custom", "what": "wheel arch", "name": name,
                "preset_id": 0, "module_rows": [], "row": None, "object": None,
                "custom": record}

    def plain_custom(name: str, entry: dict, what: str) -> dict:
        pname = entry["jc3_part"]
        light_rows = []
        for t in template:
            m = t["m"]
            if m == "behavior":
                light_rows.append({"m": m, "v": entry["behavior"], "class": "decoded",
                                   "src": f"{rel(LIGHTS)} {entry['socket']} "
                                          f"({entry['type']} -> {entry['behavior']}, G1-17)"})
            elif m == "behavior_hash":
                light_rows.append({"m": m, "v": hname(entry["behavior"]),
                                   "class": "derived (verified)",
                                   "src": "rbmhdr.hash_jenkins(behaviour); reproduces all 3,217 "
                                          "shipped behavior_hash values"})
            elif m == "part":
                light_rows.append({"m": m, "v": pname, "class": "decoded",
                                   "src": f"{rel(LIGHTS)} {entry['socket']}.jc3_part"})
            elif m == "part_hash":
                light_rows.append({"m": m, "v": hname(pname), "class": "derived (verified)",
                                   "src": "rbmhdr.hash_jenkins(part); reproduces all 3,217 "
                                          "shipped part_hash values"})
            elif m == "part_index":
                light_rows.append({"m": m, "v": part_of[pname]["i"], "class": "decoded",
                                   "src": f"{rel(PARTS)} donor: {pname} at part_index "
                                          f"{part_of[pname]['i']}"})
            elif m.startswith("diffuse."):
                k = "RGB".index(m[-1])
                light_rows.append({"m": m, "v": round(entry_colour(entry)[k] / 255.0, 6),
                                   "class": "derived",
                                   "src": f"{rel(LIGHTS)} {entry['socket']} LightColor "
                                          f"{entry_colour(entry)} / 255 (sRGB -> 0..1)"})
            elif m == "deformable_transform":
                light_rows.append({"m": m, "v": entry["jc3_anchor"], "class": "decoded (mapped)",
                                   "src": f"{rel(LIGHTS)} {entry['socket']}.jc3_anchor "
                                          f"(bone {entry['bone']})"})
            elif m == "deformable_transform_hash":
                light_rows.append({"m": m, "v": hname(entry["jc3_anchor"]),
                                   "class": "derived (verified)",
                                   "src": "rbmhdr.hash_jenkins(anchor); reproduces all 3,217 "
                                          "shipped deformable_transform_hash values"})
            elif m == "preset_id":
                light_rows.append({"m": m, "v": 0, "class": "decoded",
                                   "src": "17 shipped entries carry preset_id 0 (G2-33 §3)"})
            else:
                light_rows.append({"m": m, "v": t["v"], "class": t["class"],
                                   "src": "G2-33 §7a recipe, copied from the donor's shipped "
                                          "steady HeadLight point lamp (module lights[2])"})
        record = {"name": name, "socket": entry["socket"], "side": None,
                  "host_part": pname, "light": light_rows, "part": None}
        custom.append(record)
        return {"kind": "custom", "what": what, "name": name, "preset_id": 0,
                "module_rows": [], "row": None, "object": None, "custom": record}

    def carrier_entry(name: str, entry: dict, spec: dict) -> dict:
        """A preset-0 entry for a rig member whose behaviour the fleet does not ship."""
        e = dict(entry, behavior="None")
        tgt = plain_custom(name, e, spec["group"])
        rec = tgt["custom"]
        rec["now"] = spec["now"]
        for r in rec["light"]:
            if r["m"] in spec["members"]:
                r["v"], r["class"], r["src"] = spec["members"][r["m"]]
        return tgt

    def entry_colour(entry: dict) -> list[int]:
        return bmak_facts(entry)["colour"] or [255, 255, 255, 0]

    for i, e in enumerate(entries):
        facts = bmak_facts(e)
        socket = e["socket"]
        typ = e["type"] or "(stripped)"
        behaviour = e["behavior"] or "(none)"
        rid = f"T-L{FIRST_ID + i}"
        row = {"id": rid, "entry_index": i, "socket": socket, "bmak_type": typ,
               "bmak_behavior": behaviour, "bmak": facts,
               "jc3_part": e["jc3_part"], "jc3_anchor": e["jc3_anchor"],
               "anchor_state": e["anchor_state"], "bone": e["bone"],
               "orphan_socket": e["orphan_socket"]}
        group = None
        targets: list[dict] = []
        omit = None
        carrier = CARRIER_ROWS.get(rid)

        if carrier is not None:
            group = carrier["group"]
            targets.append(carrier_entry(carrier["name"], e, carrier))
        elif light_component(e) is None:
            side = side_of(socket) or "left"
            if e["orphan_socket"]:
                group, omit = "orphan", "socket-absent"
            elif "WheelLight" in socket:
                group = f"wheel-{side}"
                targets.append(wheel_row(e, side))
            else:
                group = f"flare-{side}"
                t = donor(f"Sport_Muscle_Headlight_Volume_{side.capitalize()}", "headlight haze")
                if t:
                    targets.append(t)
                else:
                    group, omit = "flare-orphan", "socket-absent"
        elif e["type"] == "VEHLT_BattleModeLight":
            if "WheelLight" in socket:
                group = "battle-wheel"
                targets.append(wheel_row(e, side_of(socket) or "left", battle=True))
            elif socket == "BattleModeSpotLight":
                group = "battle-spot"
                targets.append(graph_only("Front_Secondary_Head", "battle spotlight"))
            else:
                side = side_of(socket) or "left"
                group = f"battle-head-{side}"
                targets.append(plain_custom(f"headlight_battle_{side}", e, "battle headlight"))
        elif "WheelLight" in socket:
            side = side_of(socket) or "left"
            group = f"wheel-{side}"
            targets.append(wheel_row(e, side))
        elif socket == "Dashboard_Light":
            group = "dash"
            t = donor("Dash_Light", "dashboard")
            targets.append(t)
        elif socket.startswith("BrakeLight"):
            side = "left" if socket.endswith("L") else "right"
            group = f"brake-{side}"
            t = donor(f"Sport_Muscle_Rear_Break_{side.capitalize()}", "brake lamp")
            targets.append(t)
        elif socket.startswith("HeadLight"):
            side = side_of(socket) or "left"
            group = f"head-{side}"
            # the donor ships TWO headlight clusters per side - `headlight_f_*_01` and
            # `headlight_f_*_02`, each with a point row and a volumetric row. The typed
            # `VEHLT_HeadLight` entry takes the primary cluster (Sport_Muscle_*), the
            # type-stripped entry the secondary one (Front_*_Point / Front_*_Volumetric),
            # so both BmAK spot components get a lamp of their own.
            if e["type"]:
                names = (f"Sport_Muscle_Headlight_Point_{side.capitalize()}",
                         f"Sport_Muscle_Headlight_Volume_{side.capitalize()}")
            else:
                names = (f"Front_{side.capitalize()}_Point",
                         f"Front_{side.capitalize()}_Volumetric")
            for name in names:
                t = donor(name, "headlight")
                if t:
                    targets.append(t)
        elif socket == "BootLight":
            group = "boot"
            targets.append(plain_custom("boot_light", e, "boot lamp"))
        else:
            group, omit = "unclassified", "no-target"

        if omit:
            row.update({"group": group, "kind": "omitted", "omission": omit, "targets": [],
                        "class": "decoded", "verify": VERIFY[omit],
                        "proposed": "-", "now": NOW_OMIT[omit]})
            rows.append(row)
            continue
        if any(t is None for t in targets):
            raise SystemExit(f"{rid}: a donor row for {socket} resolved to None")
        kinds = {t["kind"] for t in targets}
        row.update({"group": group, "targets": targets,
                    "kind": "donor-row" if "donor-row" in kinds else
                            "graph-object" if "graph-object" in kinds else "custom",
                    "class": "decoded" if "custom" not in kinds else "derived"})
        row["class"] = "decoded" if kinds <= {"donor-row", "graph-object"} else "derived"
        rows.append(row)

    # a flare is not a light of its own, and a second component on the same lamp is not a
    # second lamp: both ride a row an earlier entry already owns
    seen: dict[tuple, str] = {}
    owner: dict[str, str] = {}
    for row in rows:
        if row["kind"] == "omitted":
            continue
        names = [t["name"] for t in row["targets"]]
        if light_component(entries[row["entry_index"]]) is None:
            row["kind"] = "flare"
            row["shared_with"] = next((owner[n] for n in names if n in owner), None)
            continue
        key = tuple(sorted(names))
        if key in seen:
            row["kind"] = "shared"
            row["shared_with"] = seen[key]
        else:
            seen[key] = row["id"]
            for n in names:
                owner[n] = row["id"]

    head_named = [o for o in graph if "Head" in o["name"]]
    diffs = sorted({tuple(round(x, 4) for x in o["diffuse"]) for o in head_named})
    return rows, custom, {"part_rows": part_rows, "template": template,
                          "behaviour_vocab": behaviours,
                          "module": module, "graph": graph, "parts": parts,
                          "system": system, "by_hash": by_hash,
                          "wheel_presets": len(system["epe"]["preset_names_matching_wheel"]),
                          "head_named": len(head_named),
                          "head_diffuse": list(diffs[0]) if len(diffs) == 1 else None,
                          "head_diffuse_variants": len(diffs)}


VERIFY = {
    "forensics-rig": "none: the forensics rig stays out (card Done line)",
    "no-muzzle-behaviour": "none: no weapon-light behaviour in the fleet's 9; the muzzle "
                           "flash is the T-FX11 .effc",
    "socket-absent": "none: the socket is not in the shipped mesh (LIGHTS.json problems)",
    "no-target": "none: no rule matched",
}
NOW_OMIT = {
    "forensics-rig": "the `VEHLT_ForensicsLight` rig (12 entries) is a scanner mode, not the "
                     "car's lights; the card keeps it out",
    "no-muzzle-behaviour": "the muzzle carries a white spot (cone 50, radius 4096) but the fleet "
                           "has no weapon-light behaviour - 9 values, none for a gun (G2-33)",
    "socket-absent": "`HeadLight1c`/`HeadLight2c` are flare objects on a socket the shipped mesh "
                     "does not have (LIGHTS.json `problems`)",
    "no-target": "-",
}
def custom_now(what: str, ctx: dict) -> str:
    """Why a custom entry: counted off the graph, never from memory."""
    if what == "wheel arch":
        return (f"no wheel-arch preset exists in the {len(ctx['graph'])} graph objects; "
                f"{ctx['wheel_presets']} fleet presets mention wheel, none is an arch lamp "
                f"(G2-33 §7a)")
    if what == "battle headlight":
        if ctx["head_diffuse"]:
            diffs = ",".join(f"{x:.3f}" for x in ctx["head_diffuse"])
            return (f"no battle-mode head preset: the {ctx['head_named']} objects whose name "
                    f"says `Head` are all {diffs} (G2-33 §7a)")
        return (f"no battle-mode head preset: the {ctx['head_named']} objects whose name says "
                f"`Head` carry {ctx['head_diffuse_variants']} different colours (G2-33 §7a)")
    if what == "boot lamp":
        return (f"no boot lamp object: the {len(ctx['graph'])} graph objects have no "
                f"`Rear_Point` (T-L7's name is not one of them)")
    return "no preset exists in the graph objects"

TAGS = {
    "head-left": "T-L1", "head-right": "T-L1", "head-left-shared": "T-L1",
    "head-right-shared": "T-L1", "flare-left": "T-L2", "flare-right": "T-L2",
    "brake-left": "T-L3", "brake-right": "T-L3", "wheel-left": "T-L4/LG4",
    "wheel-right": "T-L4/LG4", "wheel-left-shared": "T-L4/LG4",
    "wheel-right-shared": "T-L4/LG4", "battle-spot": "T-L5/LG5",
    "battle-head-left": "T-LG5", "battle-head-right": "T-LG5",
    "battle-wheel": "T-LG5", "dash": "T-L6", "boot": "T-L7",
    "muzzle": "(FX-2, T-FX11)", "forensics": "T-LG5 (named omission)",
    "orphan": "T-LG5 (named omission)",
}

# The fifteen rows the first T-18 pass left as omissions or flare riders now carry the
# closest system each stage-1 report measured.  Values are the reports' numbers; every
# member names the file that produced it, and no BmAK number is converted (G2-33 §8).
#   tmp/freebuff/reports/muzzle-and-forensics-lights.md  (T-L10, T-L21..T-L23)
#   tmp/freebuff/reports/lens-flare-carriers.md           (T-L25..T-L34)
FORENSICS_HEAD_MEMBERS = {
    "light_type": (1, "decoded", "LIGHTS_FORENSICS T-L22: all 723 cone rows in the fleet"),
    "angle": (35, "decoded",
              "LIGHTS_FORENSICS T-L22: the exact value exists (2 rows); 40 is the mode"),
    "range": (30, "decoded", "LIGHTS_FORENSICS T-L22: 351 shipped rows"),
    "multiplier": (5, "decoded",
                   "LIGHTS_FORENSICS T-L22: BmAK Brightness 5.0 and 12 shipped rows carry 5"),
    "cast_shadows": (1, "decoded",
                     "LIGHTS_FORENSICS T-L22: BmAK CastDynamicShadows True; 2 shipped rows "
                     "cast shadows"),
    "falloff_start": (0.8, "decoded",
                      "LIGHTS_FORENSICS T-L22: the mode (2,210 rows)"),
    "volumetric_mode": (1, "decoded",
                        "LIGHTS_FORENSICS T-L22: only the 2 shadow rows ship 1, on the "
                        "motor yacht's 15/35 headlight"),
    "volume_intensity": (0.02, "decoded",
                         "LIGHTS_FORENSICS T-L22: the same 2 shadow rows"),
}

CARRIER_ROWS = {
    "T-L10": {
        "group": "muzzle", "name": "muzzle_light",
        "now": "6 fleet lamps hang on a gun part and 1,177 entries carry behaviour None, so "
               "a row here is idiom not precedent (LIGHTS_FORENSICS T-L10)",
        "members": {
            "light_type": (0, "decoded",
                           "LIGHTS_FORENSICS T-L10: every point lamp in the fleet (2,494 rows)"),
            "angle": (10, "decoded",
                      "LIGHTS_FORENSICS T-L10: the value every light_type 0 row uses (2,494 rows)"),
            "range": (10, "decoded", "LIGHTS_FORENSICS T-L10: the mode of range (1,667 rows)"),
        },
    },
    "T-L21": {
        "group": "forensics", "name": "forensics_spot",
        "now": "the rig's own numbers are zeros in the base and MK2 packages (LIGHTS_FORENSICS)",
        "members": {
            "light_type": (1, "decoded",
                           "LIGHTS_FORENSICS T-L21: all 723 cone rows in the fleet"),
            "angle": (50, "decoded",
                      "LIGHTS_FORENSICS T-L21: the largest angle shipped (74 rows)"),
            "range": (50, "decoded", "LIGHTS_FORENSICS T-L21: 66 shipped rows"),
            "cast_shadows": (0, "decoded", "LIGHTS_FORENSICS T-L21: BmAK CastShadows False"),
            "multiplier": (1, "derived",
                           "LIGHTS_FORENSICS T-L21: BmAK Brightness 0.0 (placeholder) keeps the "
                           "fleet default 1"),
        },
    },
    "T-L22": {
        "group": "forensics", "name": "forensics_head_left",
        "now": "identical to T-L23 in every package (only the material enum differs); the "
               "component is a placeholder switched at runtime (LIGHTS_FORENSICS T-L22)",
        "members": FORENSICS_HEAD_MEMBERS,
    },
    "T-L23": {
        "group": "forensics", "name": "forensics_head_right",
        "now": "identical to T-L22 in every package (only the material enum differs); the "
               "component is a placeholder switched at runtime (LIGHTS_FORENSICS T-L23)",
        "members": FORENSICS_HEAD_MEMBERS,
    },
}

NOW_TEXT = {
    "T-L10": "the fleet ships 6 lamps on a gun part (`bavariumtank_turret`, range 10, angle "
             "10, white) and 1,177 entries with behaviour `None`, so a row on the gun bone is "
             "idiom not precedent; 34 weapon tune blocks carry 0 light members and 25,025 "
             "decoded `.effc` rows 0 light nodes (LIGHTS_FORENSICS T-L10)",
    "T-L21": "the rig's own numbers are zeros in the base and MK2 packages - a placeholder "
             "switched at runtime by `RVehicle.bForensicsLightActive` (0x0884); the fleet's 9 "
             "behaviours contain no forensics mode and no lighting row has an enable member "
             "(LIGHTS_FORENSICS T-L21)",
    "T-L22": "the two forensics heads are identical in every package (only the material enum "
             "differs); no enable member and no forensics behaviour in the fleet's 9 "
             "(LIGHTS_FORENSICS T-L22)",
    "T-L23": "identical to T-L22 in every package (only the material enum differs); no enable "
             "member and no forensics behaviour in the fleet's 9 (LIGHTS_FORENSICS T-L23)",
    "T-L25": "the component carries only the class-default `SourceColor` [1,1,1,1] with "
             "`Radius`/`MinStrength` null (not serialised anywhere); the ten flare rows share "
             "two `LensFlare` assets, so there are 3 looks, not 10 (lens-flare-carriers §1)",
    "T-L26": "only the class-default `SourceColor` [1,1,1,1] (`Radius`/`MinStrength` null); "
             "same shared `Batmobile_headlights_small` asset as T-L25 (lens-flare-carriers §1)",
    "T-L27": "only the class-default `SourceColor` [1,1,1,1] (`Radius`/`MinStrength` null); "
             "the second flare element on the left head lamp, sharing T-L25's asset "
             "(lens-flare-carriers §1)",
    "T-L28": "the socket and bone are null (`LIGHTS.json` problems); the only carrier is the "
             "donor's body-hosted `HeadLight` pattern (rows 3/10 at `dashboard_LIG` / "
             "`front_primary_LIG`), and our body has no `_LIG` node and the 25 assembled RBMs "
             "carry 0 `CarLight` blocks (LGT-1 §4)",
    "T-L29": "only the class-default `SourceColor` [1,1,1,1] (`Radius`/`MinStrength` null); "
             "the second flare element on the right head lamp, sharing T-L26's asset "
             "(lens-flare-carriers §1)",
    "T-L30": "the socket and bone are null (`LIGHTS.json` problems); same body-hosted "
             "`HeadLight` pattern as T-L28, which needs a `_LIG` node and a `CarLight` block "
             "the body does not have (LGT-1 §4)",
    "T-L31": "the wheel `lod1.rbm` is `CarPaintMM`-first (no `CarLight` block) and the donor's "
             "21 light entries contain no wheel light; the two stacked flare rows share one "
             "geometry slot (lens-flare-carriers §2.2, T-L31)",
    "T-L32": "only the class-default `SourceColor` [1,1,1,1]; same right wheel and same "
             "missing emitter as T-L31 (lens-flare-carriers T-L32)",
    "T-L33": "the left wheel `lod1.rbm` is `CarPaintMM`-first (no `CarLight` block); the two "
             "stacked flare rows share one geometry slot (lens-flare-carriers T-L33)",
    "T-L34": "only the class-default `SourceColor` [1,1,1,1]; same left wheel and same "
             "missing emitter as T-L33 (lens-flare-carriers T-L34)",
}

PROPOSED_TEXT = {
    "T-L10": "custom entry `muzzle_light`, `preset_id` 0, 25 members on `sportsmuscle_body` "
             "idx 0 at the gun bone (`light_type` 0 / `angle` 10 / `range` 10); the flash is "
             "`SAttachedEffect` `Effect` = "
             "`effects/jc_weapons/muzzle_flash/rico_50cal_muzzleflash.effc` (21 vehicle "
             "carriers), `Usage` = `Fire` (hash 4131019937); the per-shot pulse has no member "
             "(T-25)",
    "T-L21": "custom entry `forensics_spot`, `preset_id` 0: `light_type` 1 / `angle` 50 / "
             "`range` 50 / `diffuse` 0.765,1.000,0.957 + the graph-side `spot_angle` 50 / "
             "`spot_inner_angle` 0; the state that switches it is T-25 and its parts are in "
             "B-03",
    "T-L22": "custom entry `forensics_head_left`, `preset_id` 0: `light_type` 1 / `angle` 35 "
             "(2 shipped rows) / `range` 30 / `multiplier` 5 (12 rows) / `cast_shadows` 1 / "
             "`volumetric_mode` 1 / `volume_intensity` 0.02, `spot_inner_angle` 10; the state "
             "is T-25",
    "T-L23": "custom entry `forensics_head_right`, `preset_id` 0: same numbers as T-L22 "
             "(the two heads are identical in every package); the state is T-25",
    "T-L25": "no new row; three carriers: (1) a `CarLight` + `Window` block pair copied from "
             "`sportsmuscle_headlight_f_l_01_lod1.rbm` into our left lens mesh, (2) the "
             "`HeadLight` entry above gains `volumetric_mode` 1 / `volume_intensity` 0.002, "
             "(3) `effects/flare/headlight_flare_01.effc` (8,079 B, in 160 vehicle bundles) "
             "spawned at the socket - no member binds it, so the binding is T-24",
    "T-L26": "no new row; same three carriers as T-L25 on the right (`_f_r_01` lens block, "
             "the volumetric member, the flare effect); the binding is T-24",
    "T-L27": "no new row; the same left lens mesh as T-L25 (JC3 has one emissive block per "
             "mesh), a second `HeadLight` row on the same part is legal, and an optional second "
             "flare spawn at the second socket - the element stack collapses to one glow, one "
             "light and one sprite (T-24)",
    "T-L28": "body-hosted `HeadLight` row at an authored anchor (the donor's "
             "`front_primary_LIG` pattern) plus a `CarLight` block on the body; both are "
             "missing - B-03 copies the block, B-04 adds the node - so the row stays blocked "
             "until B-03 lands, alternatively it is dropped",
    "T-L29": "no new row; same three carriers as T-L26 on the right, second element of the "
             "right stack; the binding is T-24",
    "T-L30": "same as T-L28: body-hosted `HeadLight` row at an authored anchor + a body "
             "`CarLight` block, blocked on B-03/B-04 - not an omission",
    "T-L31": "no new row; author a `CarLight` emitter in `sportsmuscle_wheel_f_r_lod1.rbm` "
             "(B-03), a `HeadLight` entry on part 27 at `Wheel_Frnt_Right_Disc`, and an "
             "optional flare spawn at the socket (T-24); the emitter is new geometry, not a "
             "copy",
    "T-L32": "no new row; rides the T-L31 entry (one emitter, two BmAK elements) and an "
             "optional second flare spawn; the binding is T-24",
    "T-L33": "no new row; author a `CarLight` emitter in `sportsmuscle_wheel_f_l_lod1.rbm` "
             "(B-03), a `HeadLight` entry on part 26 at `Wheel_Frnt_Left_Disc`, and an "
             "optional flare spawn (T-24)",
    "T-L34": "no new row; rides the T-L33 entry (one emitter, two BmAK elements) and an "
             "optional second flare spawn; the binding is T-24",
}

VERIFY_TEXT = {
    "T-L10": "Q-1 #7 + Q-2 #6: one shot in the dark shows a flash and lit ground, and the lamp "
              "is not permanently on (T-25 proves the pulse carrier)",
    "T-L21": "Q-1 #7: the forensics spot lights only while the state is on; JC3 has no switch, "
              "so T-25 must show the carrier",
    "T-L22": "Q-1 #7: the red forensics heads light only while the state is on (T-25)",
    "T-L23": "Q-1 #7: the red forensics heads light only while the state is on (T-25)",
    "T-L25": "Q-1 #7 at 20 m head-on: glow + halo; the sprite appears only if T-24 lands",
    "T-L26": "Q-1 #7 at 20 m head-on: glow + halo on the right lamp; sprite only if T-24 lands",
    "T-L27": "Q-1 #7 at 20 m: the second left element adds no second lamp, one glow",
    "T-L28": "Q-1 #7 after B-03: a head-on glow at the authored anchor, or the row is dropped",
    "T-L29": "Q-1 #7 at 20 m: the second right element adds no second lamp, one glow",
    "T-L30": "Q-1 #7 after B-03: a head-on glow at the authored anchor, or the row is dropped",
    "T-L31": "Q-1 #7: the right wheel arch glows with the lights on (new emitter)",
    "T-L32": "Q-1 #7: the second right element adds no second emitter",
    "T-L33": "Q-1 #7: the left wheel arch glows with the lights on (new emitter)",
    "T-L34": "Q-1 #7: the second left element adds no second emitter",
}

# every row is now buildable except the two whose socket the shipped mesh does not have
LEDGER_DISPO = {"T-L28": "blocked", "T-L30": "blocked"}


def cell_target(row: dict) -> str:
    if row["kind"] == "omitted":
        state = "blocked" if row["id"] in LEDGER_DISPO else "omitted"
        return f"**{state}** ({row['omission']})"
    parts = []
    for t in row["targets"]:
        if t["kind"] == "donor-row":
            parts.append(f"`{t['name']}` (row {t['module_rows'][0]})")
        elif t["kind"] == "graph-object":
            parts.append(f"`{t['name']}` (graph only, no row)")
        else:
            parts.append(f"custom `{t['name']}` (preset 0)")
    base = " + ".join(parts)
    if row["kind"] == "flare":
        return base + " - flare, rides it (no JC3 flare member)"
    if row["kind"] == "shared":
        return base + f" - same lamp as {row['shared_with']}"
    return base


def cell_attachment(row: dict) -> str:
    part = row["jc3_part"]
    if not row["jc3_anchor"]:
        return f"`{part}` \u00b7 no anchor (orphan socket)"
    anchor = row["jc3_anchor"].replace("|", "\u00b7")
    return f"`{part}` \u00b7 `{anchor}`"


def cell_bmak(row: dict) -> str:
    b = row["bmak"]
    bits = []
    if b["colour"]:
        bits.append("LightColor " + ",".join(str(x) for x in b["colour"]))
    if b["brightness"] is not None:
        bits.append(f"B {round(b['brightness'], 4)}")
    if b["cone_outer"] is not None:
        inner = "-" if b["cone_inner"] is None else round(b["cone_inner"], 2)
        bits.append(f"cone {inner}/{round(b['cone_outer'], 2)}")
    if b["radius_ue"] is not None:
        bits.append(f"R {round(b['radius_ue'], 2)}")
    return " ".join(bits) if bits else "no light component"


def cell_jc3(row: dict) -> str:
    if row["kind"] == "omitted":
        return "-"
    outs = []
    for t in row["targets"]:
        if t["kind"] == "custom":
            c = t["custom"]
            outs.append(f"diffuse {','.join(f'{x:.3f}' for x in c['diffuse'])} "
                        f"r {c['range']} ang {c['angle']} (custom, {c['members']} members)")
        else:
            o = t.get("object") or {}
            d = o.get("diffuse") or []
            outs.append(f"diffuse {','.join(f'{x:.3f}' for x in d)} r {o.get('radius')} "
                        f"ang {o.get('spot_angle')}")
    return " + ".join(x for x in outs if x)


def cell_now(row: dict) -> str:
    if row["id"] in NOW_TEXT:
        return NOW_TEXT[row["id"]]
    if row["kind"] == "omitted":
        return row["now"]
    bits = []
    for t in row["targets"]:
        if t["kind"] == "donor-row":
            r = t["donor_row"]
            bits.append(f"donor row {r['index']} (`{r['behavior']}`, preset `{t['name']}`) hangs "
                        f"on `{r['part']}` idx {r['part_index']} - a part our entity does not "
                        f"expose (LGT-1 §2)")
        elif t["kind"] == "graph-object":
            bits.append(f"the graph has `{t['name']}` (hash {t['preset_id']}) and no module row "
                        f"references it (T-LG2)")
        else:
            bits.append(t["custom"]["now"] if "custom" in t else
                        "no preset exists in the graph objects")
    return "; ".join(bits)


def cell_proposed(row: dict) -> str:
    if row["id"] in PROPOSED_TEXT:
        return PROPOSED_TEXT[row["id"]]
    if row["kind"] == "omitted":
        return "-"
    if row["kind"] == "flare":
        return ("no new row: a `LensFlareComponent` has no JC3 member (G1-17), so the flare "
                "rides the lamp row above; its `SourceColor` is not adopted")
    if row["kind"] == "shared":
        return f"same lamp as {row['shared_with']}: no extra row (one JC3 lamp, two BmAK " \
               f"components)"
    bits = []
    for t in row["targets"]:
        if t["kind"] == "donor-row":
            bits.append(f"keep row {t['module_rows'][0]}'s members, repoint `part` -> "
                        f"`{row['jc3_part']}` (idx {row['jc3_part_index']}) and anchor -> "
                        f"`{row['jc3_anchor']}`; diffuse -> "
                        f"{','.join(f'{x:.3f}' for x in row['proposal_diffuse'])}")
        elif t["kind"] == "graph-object":
            bits.append(f"add a row for `{t['name']}` on `{row['jc3_part']}` idx "
                        f"{row['jc3_part_index']} at `{row['jc3_anchor']}`")
        else:
            bits.append(f"custom entry `{t['name']}`, preset_id 0, 25 members (G2-33 §7)")
    return "; ".join(bits)


def cell_verify(row: dict) -> str:
    if row["id"] in VERIFY_TEXT:
        return VERIFY_TEXT[row["id"]]
    if row["kind"] == "omitted":
        return row["verify"]
    if row["kind"] == "flare":
        return "Q-1 #7: the lamp glows head-on at 20 m"
    if row["kind"] == "shared":
        return "Q-1 #7: still one beam per side (the second component adds no lamp)"
    g = row["group"]
    if g.startswith("wheel"):
        return "Q-1 #7: the arch lamp glows with the lights on"
    if g == "battle-spot":
        return "Q-1 #7: the secondary spot lights the road ahead in battle mode (D-2 pose)"
    if g == "battle-wheel":
        return "Q-1 #7: the arch lamp turns red in battle mode (D-2)"
    if g.startswith("battle"):
        return "Q-1 #7: the headlamps turn red in battle mode (D-2)"
    if g.startswith("brake"):
        return "Q-1 #7: the rear lamp goes red under braking"
    if g == "dash":
        return "Q-1 #7: the dashboard glows through the canopy at night"
    if g == "boot":
        return "Q-1 #7: the boot lamp lights the ground behind the car"
    if g.startswith("flare"):
        return "Q-1 #7: the lamp glows head-on at 20 m"
    return "Q-1 #7: one beam per side on the road, haze cone visible at dusk"


# --------------------------------------------------------------------------
# record


def build() -> dict:
    entries = load_entries()
    module = load_module()
    graph = load_graph()
    parts = load_parts()
    system = load_recipe()
    rows, custom, ctx = resolve(entries, module, graph, parts, system)
    part_of = {p["n"]: p for p in parts}

    for row in rows:
        if row["kind"] == "omitted":
            continue
        row["jc3_part_index"] = part_of[row["jc3_part"]]["i"]
        colour = row["bmak"]["colour"] or [255, 255, 255, 0]
        row["proposal_diffuse"] = [round(c / 255.0, 6) for c in colour[:3]]

    used_hashes = {r["preset_id"] for r in module}
    unreferenced = sorted(o["name"] for o in graph if o["hash"] not in used_hashes)
    unresolved = sorted({r["preset_id"] for r in module} - {o["hash"] for o in graph})
    mapped = [r for r in rows if r["kind"] != "omitted"]
    counts = {
        "entries": len(entries),
        "rows": len(rows),
        "mapped": len(mapped),
        "omitted": sum(1 for r in rows if r["kind"] == "omitted"),
        "donor_rows_kept": len({t["module_rows"][0] for r in mapped
                                for t in r["targets"] if t["kind"] == "donor-row"}),
        "graph_objects_used": len({t["name"] for r in mapped
                                   for t in r["targets"] if t["kind"] == "graph-object"}),
        "custom_entries": len(custom),
        "shared_rows": sum(1 for r in rows if r["kind"] == "shared"),
        "distinct_targets": len({t["name"] for r in mapped for t in r["targets"]}),
        "colours_adopted": sum(1 for r in mapped if r["kind"] not in ("shared", "flare")
                               and r["bmak"]["colour"] is not None),
        "flare_rows": sum(1 for r in rows if r["kind"] == "flare"),
        "components": sum(len(r["bmak"]["components"]) for r in rows),
        "donor_module_rows": len(module),
        "donor_objects": len(graph),
        "object_hashes_recomputed": sum(1 for o in graph if hname(o["name"]) == o["hash"]),
        "unreferenced_objects": unreferenced,
        "unresolved_presets": unresolved,
    }
    s_mapped_anchors = sum(1 for r in rows if r["kind"] != "omitted")
    record = {
        "schema": 1,
        "card": "T-18",
        "generated_by": "Tools/scripts/t18_lights.py",
        "rig": RIG,
        "inputs": [rel(LIGHTS), rel(DONOR_MODULE), rel(DONOR_GRAPH),
                   rel(LIGHT_SYSTEM), rel(PARTS)],
        "behaviour_vocabulary": ctx["behaviour_vocab"],
        "donor": {
            "module_rows": [{"index": r["index"], "behavior": r["behavior"],
                             "part": r["part"], "part_index": r["part_index"],
                             "preset_id": r["preset_id"],
                             "preset": ctx["by_hash"].get(r["preset_id"], {}).get("name"),
                             "diffuse": [r["diffuse.R"], r["diffuse.G"], r["diffuse.B"]],
                             "range": r["range"], "angle": r["angle"],
                             "multiplier": r["multiplier"],
                             "light_type": r["light_type"],
                             "deformable_transform": r["deformable_transform"]}
                            for r in module],
            "objects": graph,
            "unreferenced": unreferenced,
            "unresolved_presets": unresolved,
        },
        "summary": counts,
        "rows": [dict(r, bmak=r["bmak"], targets=[strip_target(t, ctx) for t in r["targets"]])
                 for r in rows],
        "custom": custom,
        "unknowns": [
            "which list the renderer reads - the module entries or the .epe objects: UNKNOWN "
            "(G2-33 §8); both sides are therefore built",
            "whether a preset overrides the entry's own members: UNKNOWN (G2-33 §8); the rows "
            "print the entry's numbers and the preset's numbers side by side",
            "range/angle units and the cone's half/full-angle convention: UNKNOWN, so the BmAK "
            "cone and brightness are reported beside the JC3 value and the shipped JC3 number "
            "is kept (R4)",
            "whether an anchor chain resolves through the parts module: UNKNOWN until the §112 "
            "probe; the " + str(s_mapped_anchors) + " mapped rows carry anchor_state = "
            + ", ".join(sorted({r["anchor_state"].split(":")[0] for r in rows
                                if r["kind"] != "omitted"})),
            "CarLight material parameters (which bytes are the emissive colour): UNKNOWN "
            "(MODLOG §102d) - the parts need a block copied from a vanilla light part, never "
            "authored",
        ],
        "parts": [
            {"name": p["n"], "part_index": p["i"], "has_lights": p["lights"],
             "damage_type": p["dt"], "parent": p["parent"]}
            for p in parts if p["n"] in
            ({r["jc3_part"] for r in rows} | {c["host_part"] for c in custom})
        ],
        "light_parts": light_parts(rows, custom, part_of, ctx),
    }
    return record


def strip_target(t: dict, ctx: dict) -> dict:
    """The target as the record keeps it: no live XML row, only the numbers cells print."""
    out = {k: v for k, v in t.items() if k not in ("row", "object", "custom")}
    row = t.get("row")
    if row:
        out["donor_row"] = {
            "index": row["index"], "behavior": row["behavior"], "part": row["part"],
            "part_index": row["part_index"], "preset_id": row["preset_id"],
            "diffuse": [row["diffuse.R"], row["diffuse.G"], row["diffuse.B"]],
            "range": row["range"], "angle": row["angle"],
            "multiplier": row["multiplier"], "light_type": row["light_type"],
            "deformable_transform": row["deformable_transform"],
        }
    obj = t.get("object")
    if obj:
        out["object"] = {k: obj[k] for k in ("name", "hash", "diffuse", "radius",
                                            "spot_angle", "spot_inner_angle",
                                            "multiplier", "volume_intensity",
                                            "volumetric_mode", "near_cap")}
    if t.get("custom"):
        light = t["custom"]["light"]
        now_text = custom_now(t["custom"].get("what", ""), ctx)
        get = lambda m: next(r["v"] for r in light if r["m"] == m)  # noqa: E731
        out["custom"] = {
            "name": t["custom"]["name"],
            "now": now_text,
            "members": len(light),
            "diffuse": [get("diffuse.R"), get("diffuse.G"), get("diffuse.B")],
            "range": get("range"), "angle": get("angle"),
        }
    return out


def light_parts(rows, custom, part_of, ctx) -> list[dict]:
    """The part list B-04 needs: one record per part a light hangs on."""
    hosts: dict[str, list[str]] = {}
    for row in rows:
        if row["kind"] == "omitted" or row["kind"] == "shared":
            continue
        hosts.setdefault(row["jc3_part"], []).append(row["id"])
    out = []
    for name, ids in hosts.items():
        p = part_of[name]
        new = [c["part_name"] for c in custom if c["host_part"] == name and c["part"]]
        out.append({
            "part": name,
            "part_index": p["i"],
            "has_lights": p["lights"],
            "damage_type": p["dt"],
            "hosts": sorted(ids),
            "new_part": new[0] if new else None,
            "carlight": "needs one CarLight block (+Window for a lens) copied from a vanilla "
                        "light part (G2-33 §5); the assembled build has none (LGT-1 §4)",
            "anchor": "the anchor chain is the §112 probe (LGT-1 §5)",
        })
    for c in custom:
        if not c["part"]:
            continue
        out.append({
            "part": c["part_name"],
            "part_index": [r["v"] for r in c["part"] if r["f"] == "part_index"][0],
            "has_lights": 1,
            "damage_type": "Land_Light",
            "hosts": sorted(r["id"] for r in rows
                            if any(t.get("name") == c["name"] for t in r["targets"])),
            "new_part": None,
            "carlight": "needs one CarLight block copied from a vanilla light part (G2-33 §5)",
            "anchor": f"parent {[r['v'] for r in c['part'] if r['f'] == 'parent'][0]} "
                      f"({c['host_part']}); the node chain is the §112 probe",
        })
    return sorted(out, key=lambda x: (str(x["part_index"]).zfill(3), x["part"]))


# --------------------------------------------------------------------------
# render


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def render(record: dict) -> tuple[str, dict]:
    s = record["summary"]
    out: list[str] = []
    w = out.append
    w("# Lights translation completion (T-18)")
    w("")
    w(f"Generated by `Tools/scripts/t18_lights.py` from `{rel(LIGHTS)}` (the BmAK rig "
      f"`{record['rig']}`, {s['entries']} entries), `{rel(DONOR_MODULE)}` (the donor's "
      f"{s['donor_module_rows']} module rows), `{rel(DONOR_GRAPH)}` (the donor's "
      f"{s['donor_objects']} `SVehicleLight` objects), `{rel(LIGHT_SYSTEM)}` (G2-33's "
      f"custom-entry recipe) and `{rel(PARTS)}`; `--check` re-reads all five, re-derives this "
      f"file and `t14_lights.json`, compares both and cross-checks `T_ROWS.jsonl`.")
    w("")
    w("One row per entry of the Batmobile rig, `T-L8`…`T-L35`: the JC3 `SVehicleLight` it "
      "becomes, the part and anchor it hangs on, what the BmAK side actually says, and the "
      "probe that can fail.")
    w("")
    w("| item | value |")
    w("|---|---|")
    w(f"| entries in the rig | **{s['entries']}** |")
    w(f"| rows | **{s['rows']}** - {s['mapped']} mapped, {s['omitted']} named omissions, "
      f"{s['shared_rows']} sharing a lamp |")
    w(f"| distinct `SVehicleLight` targets | **{s['distinct_targets']}** = "
      f"{s['donor_rows_kept']} shipped module rows + {s['graph_objects_used']} unreferenced "
      f"graph object + {s['custom_entries']} custom `preset_id 0` entries |")
    w(f"| donor side | {s['donor_module_rows']} module rows, {s['donor_objects']} objects, "
      f"{len(s['unreferenced_objects'])} objects no row uses, "
      f"{len(s['unresolved_presets'])} row preset the graph does not instantiate |")
    w(f"| BmAK components behind the rows | {s['components']} (129 across the 4 rigs, G1-17) |")
    w(f"| colours adopted | {s['colours_adopted']} rows take `LightColor`/255 as `diffuse` "
      f"(alpha 0 in the data: JC3 `diffuse` is RGB) |")
    w("")
    w("## 1. The two sides and the join between them")
    w("")
    w(f"The donor's lights module holds **{s['donor_module_rows']} rows** of 25 members and its "
      f"graph holds **{s['donor_objects']} `SVehicleLight` objects**. A row addresses a preset by "
      "a 32-bit id and the graph names it by a string, so the join is "
      "`rbmhdr.hash_jenkins(name)` - the same function that reproduces all 3,217 shipped "
      "`behavior_hash`/`part_hash`/`deformable_transform_hash` values (G2-33). Measured here:")
    w("")
    w("| join | value |")
    w("|---|---|")
    w(f"| object names rebuilt from `hash_jenkins` | **{s['object_hashes_recomputed']}/"
      f"{s['donor_objects']}** (so the join is exact, not approximate) |")
    w(f"| row presets that resolve to an object | **{s['donor_module_rows'] - len(s['unresolved_presets'])}"
      f"/{s['donor_module_rows']}** |")
    w(f"| row preset with no object | `{s['unresolved_presets'][0]}` (row "
      f"{[r['index'] for r in record['donor']['module_rows'] if r['preset_id'] == s['unresolved_presets'][0]][0]}, "
      f"the taillight_r_c TailLight) - G2-33's one orphan |")
    w(f"| objects no row references | `" + "`, `".join(s['unreferenced_objects']) + "` |")
    w("")
    w("`Front_Secondary_Head` is the second one, and it is exactly the battle-mode spotlight "
      "T-L5 named: the object exists, is enabled, and nothing uses it. `Rear_Break` stays unused.")
    w("")
    w("## 2. What each old row becomes")
    w("")
    w("The card says *complete* `T-L1…T-L7` and `T-LG1…T-LG6`; those rows keep their ids and the "
      "work lands in the per-entry rows below.")
    w("")
    w("| old row | new rows | what happened |")
    w("|---|---|---|")
    for tag, old, what in OLD_ROWS:
        ids = [r["id"] for r in record["rows"] if r["group"] in tag]
        # the old id is backticked so `t_rows.py` does not parse this table as row definitions
        w(f"| `{old}` | " + (", ".join(ids) if ids else "-") + f" | {what} |")
    w("")
    w("## 3. The rows")
    w("")
    w("Columns: the BmAK entry (`G1-17` order, socket · type → behaviour), the JC3 target, the "
      "part and anchor, what the BmAK component carries, what the JC3 side carries today, the "
      "state now, the proposal, the class (`R4`) and the probe (`Q-1` item 7 - the dusk/night "
      "screenshot with lights on/off).")
    w("")
    w("The two numeric sides are not interchangeable. **The colour is adopted** - "
      "`LightColor`/255 -> `diffuse`, the G2-33 §7a conversion; **brightness, cone and radius "
      "are reported, not converted** - a UE `SpotLightComponent` and a JC3 `range`/`angle`/"
      "`multiplier` have no unit bridge and no stated half/full-angle convention (G2-33 §8), "
      "so each row keeps the shipped JC3 number and prints the BmAK one beside it (R4). "
      "Anchors are `LIGHTS.json`'s `jc3_anchor`, built from the socket's bone (G1-17), which "
      "is why a head socket can ride a door bone; every one carries "
      "`anchor_state = needs-lig-bone` until the rig has the bone (LGT-1 §5).")
    w("")
    w("| id | BmAK entry | JC3 target | attachment | BmAK (colour · B · cone · R) | JC3 value "
      "| now | proposed | class · verify |")
    w("|---|---|---|---|---|---|---|---|---|")
    for row in record["rows"]:
        w("| " + " | ".join([
            row["id"],
            f"`{row['socket']}` {row['bmak_type']} → {row['bmak_behavior']}",
            cell_target(row),
            cell_attachment(row),
            cell_bmak(row),
            cell_jc3(row),
            cell_now(row),
            cell_proposed(row),
            f"{row['class']} · {cell_verify(row)}",
        ]) + " |")
    w("")
    w("## 4. The custom entries")
    w("")
    w("Ten lamps JC3 has no preset for: the six the rig needs a lamp for, plus the four whose "
      "behaviour the fleet does not ship (T-L10, T-L21, T-L22, T-L23 - numbers from "
      "`LIGHTS_FORENSICS`). Each is a `preset_id = 0` row whose 25 members come from G2-33's "
      "recipe (the donor's shipped steady `HeadLight` point lamp, `lights[2]`), with the "
      "behaviour, part, anchor, colour and per-report values re-derived per socket.")
    w("")
    w("| entry | socket | part it hangs on | behaviour | part index | anchor | members |")
    w("|---|---|---|---|---|---|---|")
    for c in record["custom"]:
        get = lambda m: next(r["v"] for r in c["light"] if r["m"] == m)  # noqa: E731
        idx = get("part_index")
        w(f"| `{c['name']}` | `{c['socket']}` | `{get('part')}` | {get('behavior')} | {idx} | "
          f"`{get('deformable_transform').replace('|', '·')}` | {len(c['light'])} |")
    w("")
    first = next(c for c in record["custom"]
                 if c["name"].startswith("sportsmuscle_wheel") and c["name"].endswith("_arch"))
    w(f"`{first['name']}` member by member (the other nine substitute behaviour, part, anchor, "
      "colour and the numbers their own report gives):")
    w("")
    w("| member | value | class | source |")
    w("|---|---|---|---|")
    for r in first["light"]:
        src = r["src"].replace("|", "\u00b7")
        w(f"| `{r['m']}` | `{fmt(r['v'])}` | {r['class']} | {src} |")
    w("")
    w("## 5. Light parts for B-04")
    w("")
    w("One record per part a light hangs on. `has_lights` is already 1 on the body and 0 on the "
      "wheels, so the wheels need a new part (G2-33 §7c) and the body needs the anchor node and "
      "a `CarLight` block it does not have (LGT-1 §4).")
    w("")
    w("| part | part_index | has_lights | damage type | hosts | new part | CarLight | anchor |")
    w("|---|---|---|---|---|---|---|---|")
    for p in record["light_parts"]:
        w(f"| `{p['part']}` | {p['part_index']} | {p['has_lights']} | {p['damage_type']} | "
          f"{', '.join(p['hosts']) or '-'} | {('`' + p['new_part'] + '`') if p['new_part'] else '-'} | "
          f"{p['carlight']} | {p['anchor']} |")
    w("")
    w("## 6. What the files do not say (UNKNOWN)")
    w("")
    for u in record["unknowns"]:
        w(f"- {u}")
    w("")
    w("## 7. Validation")
    w("")
    w("`python Tools/scripts/t18_lights.py --check` re-reads the five inputs, re-derives this "
      "file and the json, compares both byte-for-byte and runs the assertions below.")
    w("")
    w("| assertion | measured | expected |")
    w("|---|---|---|")
    for name, got, want in assertions(record):
        w(f"| {name} | {got} | {want} |")
    w("")
    return "\n".join(out) + "\n", record


OLD_ROWS = [
    (["head-left", "head-right"], "T-L1",
     "headlamps: the donor's two clusters per side (`_01` = `Sport_Muscle_*`, `_02` = "
     "`Front_*`), each a point + volumetric pair, repointed at our sockets; the two BmAK spot "
     "components per socket take one cluster each"),
    (["flare-left", "flare-right"], "T-L2",
     "flare-only entries: JC3 has no flare member, so the flare rides the lamp's volumetric row "
     "plus a `CarLight` lens copy and an optional `headlight_flare_01.effc` at the socket "
     "(`lens-flare-carriers`); the two `…c` sockets are absent from the mesh, so T-L28/T-L30 "
     "are `blocked`, not omitted"),
    (["brake-left", "brake-right"], "T-L3",
     "brake lamps: the donor's two `Sport_Muscle_Rear_Break` rows, moved off `signal_r_*` onto "
     "our brake sockets; JC3 has no separate brake row"),
    (["wheel-left", "wheel-right", "wheel-left-shared", "wheel-right-shared"], "T-L4, T-LG4",
     "wheel-arch lamps: closed - G2-33 §7 recipe, a new `_arch` part per wheel, `preset_id 0`"),
    (["dash"], "T-L6", "dashboard: the donor's `Dash_Light` row on the body part"),
    (["boot"], "T-L7", "boot lamp: no `Rear_Point` object exists in the 22, so a custom entry"),
    (["battle-spot"], "T-L5, T-LG5",
     "battle spotlight: the graph's unreferenced `Front_Secondary_Head`, given a row"),
    (["battle-head-left", "battle-head-right", "battle-wheel"], "T-LG5",
     "battle-mode heads and wheel arch (red, B 5): custom `preset_id 0` entries"),
    (["forensics"], "T-LG5",
     "the forensics rig: three `preset_id 0` cone rows on the body from `LIGHTS_FORENSICS`; the "
     "state that switches them has no JC3 member (T-25)"),
    (["muzzle"], "(T-FX11)",
     "the muzzle spot: a `preset_id 0` point row on the gun bone (`LIGHTS_FORENSICS`); the flash "
     "is `SAttachedEffect` `Usage` = `Fire`, and the per-shot pulse is T-25"),
    (["orphan"], "T-LG5",
     "flare sockets the mesh does not have: `blocked` - the carrier is the donor's body-hosted "
     "`HeadLight` pattern, which needs a `_LIG` node and a `CarLight` block (B-03/B-04)"),
]


def assertions(record: dict) -> list[tuple[str, object, object]]:
    s = record["summary"]
    rows = record["rows"]
    return [
        ("rig entries", s["entries"], 28),
        ("rows", s["rows"], 28),
        ("mapped + omitted", s["mapped"] + s["omitted"], 28),
        ("mapped", s["mapped"], 26),
        ("named omissions", s["omitted"], 2),
        ("flare rows", s["flare_rows"], 8),
        ("rows sharing a lamp", s["shared_rows"], 0),
        ("donor module rows kept", s["donor_rows_kept"], 11),
        ("graph objects used", s["graph_objects_used"], 1),
        ("custom entries", s["custom_entries"], 10),
        ("custom entries with 25 members", sum(1 for c in record["custom"]
                                                if len(c["light"]) == 25), 10),
        ("custom entries with preset_id 0", sum(1 for c in record["custom"]
                                                if next(r["v"] for r in c["light"]
                                                        if r["m"] == "preset_id") == 0), 10),
        ("object names rebuilt from their hash", s["object_hashes_recomputed"], 22),
        ("distinct SVehicleLight targets", s["distinct_targets"], 22),
        ("donor module rows", s["donor_module_rows"], 21),
        ("donor graph objects", s["donor_objects"], 22),
        ("unreferenced graph objects", ",".join(s["unreferenced_objects"]),
         "Front_Secondary_Head,Rear_Break"),
        ("row presets with no object", len(s["unresolved_presets"]), 1),
        ("behaviours used in the fleet", len(record["behaviour_vocabulary"]), 9),
        ("rows with no target", sum(1 for r in rows if r["kind"] not in
                                    ("omitted", "donor-row", "graph-object", "custom",
                                     "shared", "flare")), 0),
        ("rows whose class is not decoded/derived", sum(1 for r in rows
                                                        if r["class"] not in ("decoded",
                                                                              "derived")), 0),
    ]


# --------------------------------------------------------------------------
# write / check


def write() -> int:
    md, record = render(build())
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    s = record["summary"]
    print(f"wrote {rel(OUT_MD)} ({md.count(chr(10))} lines) + {rel(OUT_JSON)}")
    print(f"{s['rows']} rows: {s['mapped']} mapped, {s['omitted']} named omissions, "
          f"{s['shared_rows']} sharing a lamp; {s['distinct_targets']} targets "
          f"({s['donor_rows_kept']} donor rows + {s['graph_objects_used']} graph object + "
          f"{s['custom_entries']} custom)")
    return 0


def check() -> int:
    md, record = render(build())
    problems: list[str] = []
    if not os.path.exists(OUT_MD):
        problems.append(f"missing {rel(OUT_MD)} - run --write")
    elif open(OUT_MD, encoding="utf-8").read() != md:
        old = open(OUT_MD, encoding="utf-8").read().splitlines()
        new = md.splitlines()
        for i, (a, b) in enumerate(zip(old, new), 1):
            if a != b:
                problems.append(f"FAIL: {rel(OUT_MD)} differs from the re-derived record: "
                                f"line {i}\n  on disk: {a[:160]}\n  derived: {b[:160]}")
                break
        else:
            problems.append(f"FAIL: {rel(OUT_MD)} differs in length: {len(old)} vs {len(new)}")
    if not os.path.exists(OUT_JSON):
        problems.append(f"missing {rel(OUT_JSON)} - run --write")
    else:
        disk = json.load(open(OUT_JSON, encoding="utf-8"))
        if disk != json.loads(json.dumps(record)):
            problems.append(f"FAIL: {rel(OUT_JSON)} differs from the re-derived record")

    # the table the card's Done line asks for
    for name, got, want in assertions(record):
        if got != want:
            problems.append(f"FAIL: {name} = {got}, expected {want}")

    # every target must still exist on its own side
    donor_hashes = {o["hash"] for o in record["donor"]["objects"]}
    module_index = {r["index"] for r in record["donor"]["module_rows"]}
    for row in record["rows"]:
        for t in row["targets"]:
            if t["kind"] == "donor-row" and t["module_rows"][0] not in module_index:
                problems.append(f"FAIL: {row['id']} targets module row {t['module_rows'][0]}")
            if t["preset_id"] and t["kind"] != "custom" and t["preset_id"] not in donor_hashes:
                problems.append(f"FAIL: {row['id']} preset {t['preset_id']} is not in the graph")

    # custom entry hashes must recompute
    for c in record["custom"]:
        for r in c["light"]:
            if r["m"] == "behavior_hash" and r["v"] != hname(next(x["v"] for x in c["light"]
                                                                  if x["m"] == "behavior")):
                problems.append(f"FAIL: {c['name']} behavior_hash does not recompute")
            if r["m"] == "part_hash" and r["v"] != hname(next(x["v"] for x in c["light"]
                                                              if x["m"] == "part")):
                problems.append(f"FAIL: {c['name']} part_hash does not recompute")
            if r["m"] == "deformable_transform_hash" and r["v"] != hname(
                    next(x["v"] for x in c["light"] if x["m"] == "deformable_transform")):
                problems.append(f"FAIL: {c['name']} deformable_transform_hash does not recompute")

    # ledger cross-check
    if os.path.exists(LEDGER):
        ledger = {json.loads(l)["id"]: json.loads(l)
                  for l in open(LEDGER, encoding="utf-8") if l.strip()}
        for row in record["rows"]:
            if row["id"] not in ledger:
                problems.append(f"FAIL: {row['id']} is not in {rel(LEDGER)} - run t_rows.py build")
                continue
            cells = [c.strip() for c in open(OUT_MD, encoding="utf-8").read().splitlines()
                     if c.startswith(f"| {row['id']} |")]
            if not cells:
                problems.append(f"FAIL: {row['id']} has no line in {rel(OUT_MD)}")
                continue
            want = [c.strip() for c in cells[0].strip().strip("|").split("|")]
            if ledger[row["id"]]["cells"] != want:
                problems.append(f"FAIL: {row['id']} ledger cells differ from the doc")
            if ledger[row["id"]]["doc"] != "T-14":
                problems.append(f"FAIL: {row['id']} ledger doc is {ledger[row['id']]['doc']}")
            want_dispo = LEDGER_DISPO.get(row["id"], "next")
            if ledger[row["id"]]["dispo"] != want_dispo:
                problems.append(f"FAIL: {row['id']} ledger disposition is "
                                f"{ledger[row['id']]['dispo']}, expected {want_dispo}")
    else:
        problems.append(f"missing {rel(LEDGER)}")

    s = record["summary"]
    head = (f"{s['rows']} rows: {s['mapped']} mapped, {s['omitted']} named omissions, "
            f"{s['shared_rows']} sharing a lamp | targets {s['distinct_targets']} = "
            f"{s['donor_rows_kept']} donor rows + {s['graph_objects_used']} graph object + "
            f"{s['custom_entries']} custom | donor {s['donor_module_rows']} rows / "
            f"{s['donor_objects']} objects | ledger {s['rows']}/{s['rows']}")
    if problems:
        print("\n".join(problems))
        print(f"FAIL: {len(problems)} problem(s)")
        return 1
    print(f"PASS: {head}")
    return 0


def show(rid: str) -> int:
    record = build()
    for row in record["rows"]:
        if row["id"] == rid:
            print(json.dumps(row, indent=1, ensure_ascii=False))
            for t in row["targets"]:
                if t["kind"] == "custom":
                    print(json.dumps(t["custom"], indent=1, ensure_ascii=False))
            return 0
    raise SystemExit(f"no row {rid}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--show", metavar="ROW")
    a = ap.parse_args()
    if a.write:
        sys.exit(write())
    if a.check:
        sys.exit(check())
    sys.exit(show(a.show))


if __name__ == "__main__":
    main()
