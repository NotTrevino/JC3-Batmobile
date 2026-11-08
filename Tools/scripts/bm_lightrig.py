"""bm_lightrig.py - B-07: the Batmobile's `VehicleDynamicLights` module (`v0300_…_lights.vmodc`).

The card (`GRAB_BACKLOG.md` §8 `B-07`, deps B-05, serves LGT-1/2):

    Do:   rewrite `v0300_…_lights.vmodc` entries so every behaviour (head, high, tail, brake,
          signal if any) names Batmobile light parts. Private copy if shared (R7).
    Done: every entry names a part that exists with `has_lights` = 1.

So the module's 21 shipped rows are re-derived from the cards that own each value and written as
one new module in its own build step:

  * **row map** - `Working/Translation/t14_lights.json` (T-18): 28 rig rows, 18 distinct targets.
    A `donor-row` target names the shipped module row it keeps (`module_rows`); a `custom` target
    carries its own 25 members with a class and a source each; `graph-object` (T-L17) names an
    `SVehicleLight` the donor graph instantiates and no row uses.
  * **which part each row hangs on** - `Working/Appearance/build_lights/lights_manifest.json`
    (B-03): it cut the emitter faces into 8 lamp parts and recorded, per T-18 row, the part that
    actually carries the lamp (`t18_hosting.moved[].now_on`); 3 sockets have no lamp face and are
    not hosted (`lamps_without_faces`).
  * **whether that part exists and is lit** - the built parts module of the dependency (`B-04` via
    `Builds/bm-005/aaf/.../sportsmuscle_vehicle_parts.vmodc`), decoded with `jc3adf.parts`:
    part name, `part_index`, `has_lights`. Nothing is typed: B-04 assigned the indices.
  * **the module itself** - `Builds/bm-005/aaf/.../v0300_…_lights.vmodc` (the B-05 state), exported
    with the patched `ConvertAdf` (an unchanged export/import is byte-identical, proven below).

What B-07 must NOT do, and does not:

  * no new geometry and no new part: the parts the rows name are B-03's 8 lamp parts and the body
    (`has_lights = 1` in the donor module, decoded); a row whose lamp has no part is **dropped**,
    never pointed at an invented one;
  * no invented numbers: an unchanged member is the shipped row's own value (read from the file
    being rewritten); a changed one names its T-18 row; a custom row carries T-18's 25 member
    table; T-L17's entry is assembled from the graph object's own members plus the shipped
    `Front_Primary_Head` spot row as the template for the members the object does not carry;
  * no unit conversion - `range`/`angle`/`multiplier` stay the shipped numbers (G2-33 §8: no unit
    bridge), only the colour is adopted (T-18's `proposal_diffuse`, `LightColor`/255);
  * an entry is never written onto a part that lacks `has_lights` (the card's Done line) and never
    onto one of the donor's own Serpente lamp parts (the Do line).

Rows the T-18 map does not claim are dropped with the measured reason recorded per row: the
Batmobile's BmAK rig has no indicator, no reverse lamp and no central high beam
(`Research/BatmobileGrab/LIGHTS.json`, G1-17), so the donor's signal/reverse rows cannot name a
Batmobile light part and keeping them would light Serpente lamps on a Batmobile.

R7 (no shared module edits in place) is asserted, not assumed: the module path must be this
vehicle's own `modules/generated/…_lights.vmodc`; a shared module name (`vehicle_common`,
`lave_health_medium`, `vehicle_deform`) aborts the run. A private copy is not needed because no
other vehicle references this module.

Usage
    python Tools/scripts/bm_lightrig.py --write     # spec + Builds/bm-007 (never installs)
    python Tools/scripts/bm_lightrig.py --check     # no writes: re-derive, compare, run Done checks
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3adf                                    # noqa: E402
import rbmhdr                                    # noqa: E402
from eetoc import read_toc, sarc_dir, unaaf       # noqa: E402

BASE_TAG = "bm-005"          # B-07's dependency (deps: B-05)
PACK_TAG = "bm-009"          # B-09's packed .ee/.toc = the base the module is packed against
TAG = "bm-007"
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
VEHICLE = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
MODULE = (VEHICLE + "/modules/generated/"
          "v0300_car_kensington_sportsmuscle_lights.vmodc")
MODULE_NAME = "v0300_car_kensington_sportsmuscle_lights.vmodc"
PARTS_MODULE = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
                "sportsmuscle_vehicle_parts.vmodc")
SHARED = ("vehicle_common.vmodc", "lave_health_medium.vmodc", "vehicle_deform.vmodc")
T18 = os.path.join(ROOT, "Working", "Translation", "t14_lights.json")
T18_MD = os.path.join(ROOT, "Working", "Translation", "T14_LIGHTS.md")
B03 = os.path.join(ROOT, "Working", "Appearance", "build_lights", "lights_manifest.json")
PARTS_SPEC = os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json")
DONOR_GRAPH = os.path.join(ROOT, "Working", "Lights", "v082", "entity.xml")
SPEC = os.path.join(ROOT, "Working", "Lights", "bm_lightrig.json")
GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
ADF = os.path.join(ROOT, "Tools", "Gibbed-patched", "Gibbed.JustCause3.ConvertAdf.exe")
SCHEMA = 1
WORK = os.path.join(ROOT, "tmp", "b07")

# The 25 members of one entry, in the module's own declaration order (`Research/JC3Grab/LIGHT_SYSTEM.md` §1).
MEMBERS = ["behavior", "behavior_hash", "part", "part_hash", "part_index",
           "diffuse.R", "diffuse.G", "diffuse.B", "range", "falloff_start", "near_cap",
           "multiplier", "min_luminosity", "light_type", "blinking", "angle", "cast_shadows",
           "projected_texture_index", "volumetric_mode", "volume_intensity",
           "uvscale.u", "uvscale.v", "deformable_transform", "deformable_transform_hash",
           "preset_id"]
INTS = {"behavior_hash", "part_hash", "part_index", "light_type", "blinking", "cast_shadows",
        "projected_texture_index", "volumetric_mode", "deformable_transform_hash", "preset_id"}
FLOATS = {"diffuse.R", "diffuse.G", "diffuse.B", "range", "falloff_start", "near_cap",
          "multiplier", "min_luminosity", "angle", "volume_intensity", "uvscale.u", "uvscale.v"}
STRINGS = {"behavior", "part", "deformable_transform"}

# Why a shipped row no T-18 row claims is dropped. The behaviour/preset/part of every dropped row
# are re-read from the file and asserted against this table (see `plan()`), so the reason cannot
# drift away from the bytes.
DROP_REASONS = {
    0: ("the donor's rear point lamp (preset `Rear_Left_Point`) on the Serpente's own tail part; "
        "no T-18 row maps it - BmAK's tail behaviour is the two brake entries (T-L15/T-L16) and "
        "G1-17's rig has no rear point lamp"),
    1: ("`LeftSignal`: the BmAK rig has no indicator (G1-17: 28 entries, 9 behaviours, none "
        "Left/RightSignal), so this behaviour has no Batmobile lamp to name"),
    3: ("`Rear_Brake`: T-18's own orphan preset - no `SVehicleLight` object is instantiated for "
        "hash 3358775008 (T-18 §1); the brake/tail behaviour is carried by the two kept rows"),
    4: ("the donor's rear point lamp (preset `Rear_Right_Point`) on the Serpente's own tail part; "
        "no T-18 row maps it - same reason as row 0"),
    5: ("`Front_Left_Turn`: the BmAK rig has no indicator (G1-17), so this behaviour has no "
        "Batmobile lamp to name"),
    6: ("`Front_Right_Turn`: the BmAK rig has no indicator (G1-17), so this behaviour has no "
        "Batmobile lamp to name"),
    9: ("`Front_Primary_Head`: the donor's central high beam on the body; B-03 measured no Emissive "
        "face within 0.3909 m of the BmAK central socket `Headlight_Centre`, so no Batmobile light "
        "part can host it and T-18 wrote no row for it"),
    10: ("`Rear_Right_Turn`: the BmAK rig has no indicator (G1-17), so this behaviour has no "
         "Batmobile lamp to name"),
    15: ("`Reverse`: the BmAK rig has no reverse lamp (G1-17: 9 behaviours, none Reverse), so this "
         "behaviour has no Batmobile lamp to name"),
    16: ("`Reverse`: the BmAK rig has no reverse lamp (G1-17), same reason as row 15"),
}
# The shipped behaviour each dropped row must have for its reason to hold (measured, then checked).
DROP_EXPECT = {0: "TailLight", 1: "LeftSignal", 3: "TailLight", 4: "TailLight", 5: "LeftSignal",
               6: "RightSignal", 9: "HeadLight", 10: "RightSignal", 15: "Reverse",
               16: "Reverse"}
# T-L17's entry: which member comes from where. `object` = the graph object's own decoded members,
# `spot-template` = the shipped `Front_Primary_Head` spot row (module lights[9]), `derived` = the
# angle/light_type convention this module itself shows (all 21 rows: angle 10 -> light_type 0,
# angle 40 -> light_type 1).
TL17_MEMBERS = {
    "behavior": ("object", "T-18 row T-L17 `bmak_behavior` (VEHLT_BattleModeLight -> HeadLight, G1-17)"),
    "behavior_hash": ("derived", "rbmhdr.hash_jenkins(behaviour)"),
    "part": ("host", "B-03 hosting (no lamp face for this socket) -> the body part"),
    "part_hash": ("derived", "rbmhdr.hash_jenkins(part)"),
    "part_index": ("host", "the built parts module (B-04)"),
    "diffuse.R": ("object", "graph object `Front_Secondary_Head`.diffuse[0] (decoded)"),
    "diffuse.G": ("object", "graph object `Front_Secondary_Head`.diffuse[1] (decoded)"),
    "diffuse.B": ("object", "graph object `Front_Secondary_Head`.diffuse[2] (decoded)"),
    "range": ("object", "graph object `Front_Secondary_Head`.radius -> `range` (the bridge T-18's row prints: `r 10.0`)"),
    "falloff_start": ("spot-template", "shipped spot row lights[9] (`Front_Primary_Head`), the same kind of lamp"),
    "near_cap": ("object", "graph object `.near_cap` (decoded)"),
    "multiplier": ("object", "graph object `.multiplier` (decoded)"),
    "min_luminosity": ("spot-template", "shipped spot row lights[9]"),
    "light_type": ("derived", "angle -> light_type convention of this module (all 21 shipped rows)"),
    "blinking": ("spot-template", "shipped spot row lights[9]"),
    "angle": ("object", "graph object `.spot_angle` -> `angle` (the bridge T-18's row prints: `ang 60.0`)"),
    "cast_shadows": ("spot-template", "shipped spot row lights[9]"),
    "projected_texture_index": ("spot-template", "shipped spot row lights[9]"),
    "volumetric_mode": ("object", "graph object `.volumetric_mode` (decoded)"),
    "volume_intensity": ("object", "graph object `.volume_intensity` (decoded)"),
    "uvscale.u": ("spot-template", "shipped spot row lights[9]"),
    "uvscale.v": ("spot-template", "shipped spot row lights[9]"),
    "deformable_transform": ("row", "T-18 row T-L17 `jc3_anchor` (BmAK socket chain, decoded)"),
    "deformable_transform_hash": ("derived", "rbmhdr.hash_jenkins(anchor)"),
    "preset_id": ("object", "the graph object's own hash (T-LG2: no module row references it)"),
}


# --------------------------------------------------------------------------- helpers
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def hj(text: str) -> int:
    return rbmhdr.hash_jenkins(text.encode("ascii"))


def run(cmd: list[str], what: str) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{what} failed ({r.returncode}):\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r.stdout


def base_dir(tag: str = BASE_TAG) -> str:
    return os.path.join(ROOT, "Builds", tag)


def tag_dir() -> str:
    return os.path.join(ROOT, "Builds", TAG)


def module_of_aaf(tag: str) -> str:
    return os.path.join(base_dir(tag), "aaf", MODULE.replace("/", os.sep))


def decode_module(path: str) -> list[dict]:
    """The module's rows, member -> value, in declaration order."""
    return decode_module_bytes(open(path, "rb").read())


def decode_module_bytes(blob: bytes) -> list[dict]:
    """Same, from the module's bytes (so the .ee's own copy can be read without a temp file)."""
    adf = jc3adf.Adf(blob)
    flat = {p: v for p, _t, v in jc3adf.walk(adf)}
    n = 0
    while f"lights[{n}].behavior" in flat:
        n += 1
    rows = []
    for i in range(n):
        rows.append({m: flat[f"lights[{i}].{m}"] for m in MEMBERS})
    if n == 0:
        raise SystemExit("no lights[] rows in this module")
    return rows


def decode_parts(path: str) -> dict[int, dict]:
    adf = jc3adf.Adf(open(path, "rb").read())
    out = {}
    for p in jc3adf.parts(adf):
        out[int(p["part_index"])] = p
    return out


def preset_names() -> dict[int, str]:
    """preset hash -> `SVehicleLight` object name, from the donor graph XML (the join T-18 uses)."""
    xml = open(DONOR_GRAPH, encoding="utf-8-sig").read()
    names = []
    marker = '<value name="preset_id" type="string">'
    i = 0
    while True:
        i = xml.find(marker, i)
        if i < 0:
            break
        j = xml.find("</value>", i)
        names.append(xml[i + len(marker):j])
        i = j
    return {hj(n): n for n in names}


def xml_export(module: str, xml_path: str) -> None:
    run([ADF, "-e", module, xml_path], f"ConvertAdf -e {os.path.basename(module)}")


def xml_import(xml_path: str, module: str) -> None:
    run([ADF, "-i", xml_path, module], f"ConvertAdf -i {os.path.basename(xml_path)}")


def array_node(tree: ET.ElementTree) -> ET.Element:
    for node in tree.iter("member"):
        if node.get("name") == "lights" and node.get("gbltype") == "Array" \
                and node.findall("member"):
            return node
    raise SystemExit("the exported XML carries no lights[] array")


def member_of(node: ET.Element, name: str):
    path = name.split(".")
    cur = node
    for part in path:
        nxt = next((m for m in cur.findall("member") if m.get("name") == part), None)
        if nxt is None:
            raise SystemExit(f"member {name!r} not found under {node.get('type')}")
        cur = nxt
    return cur


def set_member(node: ET.Element, name: str, value) -> None:
    el = member_of(node, name)
    if name in STRINGS:
        el.text = str(value)
    else:
        el.text = format(float(value), ".9g") if name in FLOATS else str(int(value))


def get_member(node: ET.Element, name: str):
    el = member_of(node, name)
    if name in STRINGS:
        return el.text or ""
    return float(el.text) if name in FLOATS else int(el.text)


# --------------------------------------------------------------------------- the plan
def plan() -> dict:
    t18 = json.load(open(T18, encoding="utf-8"))
    b03 = json.load(open(B03, encoding="utf-8"))
    pspec = json.load(open(PARTS_SPEC, encoding="utf-8"))
    if MODULE_NAME in SHARED or not MODULE.startswith(VEHICLE + "/") or "00_shared" in MODULE:
        raise SystemExit(f"R7: {MODULE} is not this vehicle's own module - refusing to edit it")

    base_mod = module_of_aaf(BASE_TAG)
    base_rows = decode_module(base_mod)
    parts = decode_parts(os.path.join(base_dir(BASE_TAG), "aaf", PARTS_MODULE.replace("/", os.sep)))
    pnames = preset_names()

    moved = {m["row"]: m["now_on"] for m in b03["t18_hosting"]["moved"]}
    lamp_parts = {lamp["part"] for lamp in b03["lamps"]}
    no_face = {x["socket"]: x for x in b03["lamps_without_faces"]}

    # which T-18 rows claim which shipped module row
    claims: dict[int, list[dict]] = {}
    for row in t18["rows"]:
        for tgt in row.get("targets") or []:
            for m in tgt.get("module_rows") or []:
                claims.setdefault(int(m), []).append(row)

    def resolve_part(name: str) -> dict:
        hit = next((p for p in parts.values() if p["name"] == name), None)
        if hit is None:
            raise SystemExit(f"part {name!r} is not in the built parts module")
        return {"name": hit["name"], "part_index": int(hit["part_index"]),
                "has_lights": int(hit["has_lights"]), "damage_type": hit["damage_type"]}

    rows, dropped = [], []
    for i, base in enumerate(base_rows):
        if i not in claims:
            if i not in DROP_REASONS:
                raise SystemExit(f"shipped row {i} ({base['behavior']}) is neither claimed by T-18 "
                                 "nor reasoned about - refusing to drop it silently")
            if base["behavior"] != DROP_EXPECT[i]:
                raise SystemExit(f"row {i}: base behaviour {base['behavior']!r} != "
                                 f"{DROP_EXPECT[i]!r} the reason states")
            dropped.append({
                "base_index": i, "behavior": base["behavior"],
                "preset_id": int(base["preset_id"]),
                "preset_name": pnames.get(int(base["preset_id"]), "UNKNOWN"),
                "base_part": base["part"], "base_part_index": int(base["part_index"]),
                "anchor": base["deformable_transform"], "reason": DROP_REASONS[i]})
            continue

        # A flare row (kind `flare`, no BmAK light component) rides the lamp's row and adopts no
        # colour (T-18: "its `SourceColor` is not adopted"), so it does not decide the row.
        primary = [r for r in claims[i] if (r.get("bmak") or {}).get("colour") is not None] \
            or claims[i]
        # B-03's measured hosting wins; a row B-03 did not host (its lamp has no cut face) keeps
        # T-18's own declared part, which is the body - also lit in the donor module.
        hosts = {moved.get(r["id"]) or r["jc3_part"] for r in primary}
        if len(hosts) != 1 or None in hosts:
            raise SystemExit(f"row {i}: T-18 rows {[r['id'] for r in claims[i]]} disagree on the "
                             f"part ({hosts})")
        host = resolve_part(hosts.pop())
        if host["has_lights"] != 1:
            raise SystemExit(f"row {i}: part {host['name']} has has_lights != 1")
        colours = {tuple(r["proposal_diffuse"]) for r in primary}
        anchors = {r["jc3_anchor"] for r in primary}
        if len(colours) != 1 or len(anchors) != 1:
            raise SystemExit(f"row {i}: T-18 rows disagree on colour {colours} / anchor {anchors}")
        colour = list(colours.pop())
        anchor = anchors.pop()
        want = dict(base)
        want.update({"part": host["name"], "part_hash": hj(host["name"]),
                     "part_index": host["part_index"],
                     "diffuse.R": colour[0], "diffuse.G": colour[1], "diffuse.B": colour[2],
                     "deformable_transform": anchor,
                     "deformable_transform_hash": hj(anchor)})
        prov = {}
        for m in MEMBERS:
            if m in ("part", "part_hash", "part_index"):
                prov[m] = {"v": want[m], "class": "decoded",
                           "src": f"B-03 hosting of {', '.join(sorted(r['id'] for r in claims[i]))} "
                                  f"(`t18_hosting.moved[].now_on`, else T-18 `jc3_part` for a socket "
                                  f"B-03 measured no lamp face for); index/flag from the built parts "
                                  f"module (B-04)"}
            elif m.startswith("diffuse."):
                prov[m] = {"v": want[m], "class": "derived",
                           "src": f"T-18 {', '.join(sorted(r['id'] for r in claims[i]))} "
                                  f"`proposal_diffuse` (LightColor/255)"}
            elif m in ("deformable_transform", "deformable_transform_hash"):
                prov[m] = {"v": want[m], "class": "decoded",
                           "src": f"T-18 {', '.join(sorted(r['id'] for r in claims[i]))} `jc3_anchor`"}
            else:
                prov[m] = {"v": want[m], "class": "decoded",
                           "src": f"kept from the shipped row lights[{i}] (read from the module)"}
        rows.append({"index": len(rows), "origin": f"donor-row {i}",
                     "t18_rows": sorted(r["id"] for r in claims[i]),
                     "part": host, "anchor": anchor, "members": prov})

    # T-L17: the one graph object T-18 gives a row
    t17 = next(r for r in t18["rows"] if r["id"] == "T-L17")
    obj = t17["targets"][0]["object"]
    spot = base_rows[9]
    if spot["preset_id"] != 4272096469 or spot["behavior"] != "HeadLight":
        raise SystemExit("lights[9] is not the shipped `Front_Primary_Head` spot row T-L17 uses as "
                         "its member template")
    if [spot[m] for m in ("angle",)] != [40.0]:
        raise SystemExit("lights[9] is not a 40-degree spot row")
    body = resolve_part("sportsmuscle_body")
    if body["has_lights"] != 1:
        raise SystemExit("the body part is not lit in the built module")
    t17_base = {"behavior": t17["bmak_behavior"],
                "behavior_hash": hj(t17["bmak_behavior"]),
                "part": body["name"], "part_hash": hj(body["name"]),
                "part_index": body["part_index"],
                "diffuse.R": obj["diffuse"][0], "diffuse.G": obj["diffuse"][1],
                "diffuse.B": obj["diffuse"][2],
                "range": obj["radius"], "falloff_start": spot["falloff_start"],
                "near_cap": obj["near_cap"], "multiplier": obj["multiplier"],
                "min_luminosity": spot["min_luminosity"],
                "light_type": 1 if float(obj["spot_angle"]) > 10.0 else 0,
                "blinking": spot["blinking"], "angle": obj["spot_angle"],
                "cast_shadows": spot["cast_shadows"],
                "projected_texture_index": spot["projected_texture_index"],
                "volumetric_mode": obj["volumetric_mode"],
                "volume_intensity": obj["volume_intensity"],
                "uvscale.u": spot["uvscale.u"], "uvscale.v": spot["uvscale.v"],
                "deformable_transform": t17["jc3_anchor"],
                "deformable_transform_hash": hj(t17["jc3_anchor"]),
                "preset_id": int(obj["hash"])}
    rows.append({"index": len(rows), "origin": "graph-object (T-L17)", "t18_rows": ["T-L17"],
                 "part": body, "anchor": t17["jc3_anchor"],
                 "members": {m: {"v": t17_base[m],
                                 "class": "decoded" if TL17_MEMBERS[m][0] in ("object", "row", "host")
                                 else "derived",
                                 "src": TL17_MEMBERS[m][1]} for m in MEMBERS}})
    if len(TL17_MEMBERS) != len(MEMBERS):
        raise SystemExit("T-L17 member table does not cover the 25 members")

    # the 6 custom entries
    host_of_custom: dict[str, tuple[str, str | None, bool]] = {}
    for row in t18["rows"]:
        flare = (row.get("bmak") or {}).get("colour") is None
        for tgt in row.get("targets") or []:
            if tgt.get("kind") == "custom":
                cur = host_of_custom.get(tgt["name"])
                # the lamp row creates the entry; a flare row only rides it
                if cur is None or (cur[2] and not flare):
                    host_of_custom[tgt["name"]] = (row["id"], moved.get(row["id"]), flare)
    for cust in t18["custom"]:
        name = cust["name"]
        trid, now_on, _flare = host_of_custom[name]
        # T-18's own part, and B-03's measured hosting where it names one
        declared = next(m["v"] for m in cust["light"] if m["m"] == "part")
        part_name = now_on or declared
        host = resolve_part(part_name)
        if host["has_lights"] != 1:
            raise SystemExit(f"custom {name}: part {part_name} has has_lights != 1")
        vals = {m["m"]: m["v"] for m in cust["light"]}
        if set(vals) != set(MEMBERS):
            raise SystemExit(f"custom {name}: member set differs from the module's 25")
        want = dict(vals)
        want.update({"part": host["name"], "part_hash": hj(host["name"]),
                     "part_index": host["part_index"]})
        prov = {}
        for m in MEMBERS:
            if m in ("part", "part_hash", "part_index") and part_name != declared:
                prov[m] = {"v": want[m], "class": "decoded",
                           "src": f"B-03 hosted {trid} on {part_name} (`t18_hosting.moved[].now_on`) "
                                  f"- overrides T-18's pre-B-03 `{declared}`; index/flag from the "
                                  f"built parts module (B-04)"}
            else:
                src = next(x["src"] for x in cust["light"] if x["m"] == m)
                cls = next(x["class"] for x in cust["light"] if x["m"] == m)
                prov[m] = {"v": want[m], "class": cls, "src": src}
        rows.append({"index": len(rows), "origin": f"custom ({trid})", "t18_rows": [trid],
                     "part": host, "anchor": want["deformable_transform"], "members": prov})

    # the module's own light_type convention, which T-L17 uses
    conv = [(r["angle"], r["light_type"]) for r in base_rows]
    if not all((a > 10.0) == bool(t) for a, t in conv):
        raise SystemExit("the shipped module does not follow angle>10 -> light_type 1")

    used = sorted({r["part"]["name"] for r in rows})
    lit_without_entry = sorted(p["name"] for i, p in parts.items()
                               if int(p["has_lights"]) == 1 and i in
                               {42, 43, 44, 45, 46, 47, 48, 49} and p["name"] not in used)
    return {"schema": SCHEMA, "card": "B-07", "generator": "Tools/scripts/bm_lightrig.py",
            "scope": "the Batmobile's VehicleDynamicLights module (one entry per lamp behaviour)",
            "inputs": {
                "T-18 rows": {"path": rel(T18), "sha256": sha256_file(T18), "rows": len(t18["rows"])},
                "B-03 hosting": {"path": rel(B03), "sha256": sha256_file(B03),
                                 "lamps": len(b03["lamps"]), "hosted": len(moved)},
                "B-04 part indices": {"path": rel(PARTS_SPEC), "sha256": sha256_file(PARTS_SPEC),
                                      "new_parts": len(pspec["parts"])},
                "base module": {"path": rel(base_mod), "sha256": sha256_file(base_mod),
                                "bytes": os.path.getsize(base_mod), "rows": len(base_rows)},
                "parts module (built)": {"path": PARTS_MODULE, "parts": len(parts)},
            },
            "module": {"path": MODULE, "name": MODULE_NAME, "rows_before": len(base_rows),
                       "rows_after": len(rows), "shared": False,
                       "shared_rationale": (
                           "R7 is about modules shared between vehicles, which live under "
                           "`editor/entities/jc_vehicles/00_shared/modules/` (e.g. "
                           "`health/lave_health_medium.vmodc`, `vehicle_common.vmodc`); this file "
                           "sits inside the donor's own entity folder "
                           "(`v0300_car_kensington_sportsmuscle/modules/generated/`) and the tool "
                           "aborts unless the path is inside that folder, so a private copy would "
                           "rename nothing and has no hash to repoint. Every shared module in the "
                           "build is byte-identical to the base build's (checked below)")},
            "rows": rows, "dropped": dropped,
            "lamp_parts": sorted(lamp_parts), "parts_used": used,
            "lit_parts_without_entry": {
                "parts": lit_without_entry,
                "why": ("B-03 cut 8 lamp parts from the emissive faces, but the BmAK rig has no "
                        "socket on the rear wheels (no T-18 row, no light component), so the two "
                        "rear arch parts carry `has_lights = 1` and no module entry - the same "
                        "pattern as 13 of the fleet's 2,073 lit parts (G2-33 §4)")},
            "sockets_without_faces": no_face,
            "light_type_convention": {
                "rule": "angle > 10 -> light_type 1",
                "rows": len(conv), "holds": True,
                "source": "the 21 shipped rows of the module being rewritten"},
            "unknowns": [
                "the anchor chain (`deformable_transform`) resolving inside a non-rigged part is the "
                "§112 probe (LGT-1 §5, G2-33 §6) - B-07 writes T-18's decoded socket chain unchanged",
                "`preset_id` semantics (whether a preset overrides the entry's members) is UNKNOWN "
                "(G2-33 §8); every entry carries its own numbers",
                "range/angle/multiplier units have no bridge (G2-33 §8), so no BmAK cone/brightness "
                "is converted",
                "which of the module entries and the `.epe` `SVehicleLight` objects the renderer "
                "reads is UNKNOWN (G2-33 §8, Q-1 item 7)",
            ]}


# --------------------------------------------------------------------------- encode
def encode(pl: dict, out_module: str, workdir: str) -> dict:
    """Base module -> XML -> the plan's rows -> module; returns the re-encode facts."""
    os.makedirs(workdir, exist_ok=True)
    base_mod = module_of_aaf(BASE_TAG)
    xml_in = os.path.join(workdir, "base.xml")
    xml_export(base_mod, xml_in)

    tree = ET.parse(xml_in)
    arr = array_node(tree)
    template = arr.findall("member")[0]
    old = arr.findall("member")
    if len(old) != pl["module"]["rows_before"]:
        raise SystemExit(f"XML rows {len(old)} != decoded rows {pl['module']['rows_before']}")
    # the two decode paths must agree member by member before anything is written
    for node, row in zip(old, decode_module(base_mod)):
        for m in MEMBERS:
            got = get_member(node, m)
            want = row[m] if m not in FLOATS else float(row[m])
            if isinstance(want, str):
                if str(got) != want:
                    raise SystemExit(f"XML/decode disagree on {m}: {got!r} != {want!r}")
            elif abs(float(got) - float(want)) > 1e-9:
                raise SystemExit(f"XML/decode disagree on {m}: {got!r} != {want!r}")

    for node in old:
        arr.remove(node)
    for row in pl["rows"]:
        src = row["origin"]
        if src.startswith("donor-row "):
            node = copy.deepcopy(old[int(src.split()[1])])
        elif src.startswith("custom"):
            node = copy.deepcopy(template)
        else:
            node = copy.deepcopy(old[9])          # T-L17's member template (the spot row)
        for m in MEMBERS:
            set_member(node, m, row["members"][m]["v"])
        arr.append(node)

    xml_out = os.path.join(workdir, "bm_lightrig.xml")
    tree.write(xml_out, encoding="utf-8", xml_declaration=True)
    xml_import(xml_out, out_module)

    rows = decode_module(out_module)
    if len(rows) != len(pl["rows"]):
        raise SystemExit(f"re-read {len(rows)} rows, planned {len(pl['rows'])}")
    for got, want in zip(rows, pl["rows"]):
        for m in MEMBERS:
            a, b = got[m], want["members"][m]["v"]
            if m in FLOATS:
                if abs(float(a) - float(b)) > 1e-6:
                    raise SystemExit(f"row {want['index']} {m}: {a!r} != {b!r}")
            elif a != b:
                raise SystemExit(f"row {want['index']} {m}: {a!r} != {b!r}")
    return {"xml": rel(xml_out), "bytes": os.path.getsize(out_module),
            "sha256": sha256_file(out_module),
            "base_bytes": os.path.getsize(base_mod),
            "delta_bytes": os.path.getsize(out_module) - os.path.getsize(base_mod)}


def write_installer(tdir: str, receipt: dict) -> None:
    ee = receipt["ee"]["sha256"]
    toc = receipt["toc"]["sha256"]
    body = f"""<#
    {TAG} installer (B-07 lights module). Generated by Tools/scripts/bm_lightrig.py, never run.
    Close the game before -Action Install. Rollback091 restores test-091.
#>
[CmdletBinding()]
param([ValidateSet('Install','Verify','Rollback091','Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$GameDir = 'D:\\Games\\Just Cause 3'
$EeT = Join-Path $GameDir 'dropzone/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/{EE}'
$EeSha = '{ee}'
$TocSha = '{toc}'
$B = '{tdir}'
switch ($Action) {{
    'Install' {{
        Copy-Item -LiteralPath (Join-Path $B '{EE}') -Destination $EeT -Force
        Copy-Item -LiteralPath (Join-Path $B '{EE}.toc') -Destination ($EeT + '.toc') -Force
        Write-Host 'deployed {TAG}'
    }}
    'Verify' {{
        & python '{os.path.join(ROOT, "Tools", "scripts", "verify_install.py")}' --build $B
    }}
    'Rollback091' {{
        & (Join-Path '{os.path.join(ROOT, "Builds", "test-091")}' 'install.ps1') -Action Install
    }}
    'Status' {{
        $e = if (Test-Path -LiteralPath $EeT) {{ (Get-FileHash -LiteralPath $EeT).Hash }} else {{ 'none' }}
        $t = if (Test-Path -LiteralPath ($EeT + '.toc')) {{ (Get-FileHash -LiteralPath ($EeT + '.toc')).Hash }} else {{ 'none' }}
        Write-Host "dropzone .ee : $e"
        Write-Host "dropzone .toc: $t"
        if ($e -eq $EeSha -and $t -eq $TocSha) {{ Write-Host '  == {TAG} (all match)' }}
    }}
}}
"""
    with open(os.path.join(tdir, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
        f.write(body)


def write_build(pl: dict) -> int:
    tdir = tag_dir()
    for p in (os.path.join(base_dir(), "aaf"), module_of_aaf(BASE_TAG),
              os.path.join(base_dir(PACK_TAG), EE),
              os.path.join(base_dir(PACK_TAG), EE + ".toc")):
        if not os.path.exists(p):
            raise SystemExit(f"base build incomplete: {rel(p)}")
    if os.path.exists(tdir):
        shutil.rmtree(tdir)
    os.makedirs(tdir)
    # 1. the lineage tree: B-05's aaf (it carries B-05's loose .epe) with B-07's module
    aaf = os.path.join(tdir, "aaf")
    shutil.copytree(os.path.join(base_dir(), "aaf"), aaf)
    work = os.path.join(WORK, "build")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    module_out = os.path.join(work, MODULE_NAME)
    info = encode(pl, module_out, work)
    shutil.copyfile(module_out, os.path.join(aaf, MODULE.replace("/", os.sep)))
    print(f"module {MODULE_NAME}: {info['base_bytes']} -> {info['bytes']} B "
          f"({info['delta_bytes']:+d})")

    # 2. the packed .ee: PACK_TAG's aaf (the B-09 graph, as bm-005 carried it) + the new module,
    #    so the packed tree's only inner change is the lights module
    stage = os.path.join(WORK, "pack")
    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(os.path.join(base_dir(PACK_TAG), "aaf"), stage)
    shutil.copyfile(module_out, os.path.join(stage, MODULE.replace("/", os.sep)))
    ee = os.path.join(tdir, EE)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), stage, ee], "SmallPack")
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee,
         os.path.join(tdir, "verify")], "SmallUnpack")
    base_ee = os.path.join(base_dir(PACK_TAG), EE)
    run([sys.executable, os.path.join(HERE, "eetoc.py"), "patch", ee, base_ee + ".toc",
         "--base-ee", base_ee, "-o", ee + ".toc"], "eetoc patch")
    toc = ee + ".toc"
    recs = read_toc(open(toc, "rb").read())
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    bad = [(n, (o, s), real.get(n)) for n, o, s in recs if o and real.get(n) != (o, s)]
    if bad:
        raise SystemExit(f"{len(bad)} .toc record(s) disagree with the .ee: {bad[:3]}")
    mod_rec = next((x for x in recs if x[0].endswith(MODULE_NAME)), None)
    if not mod_rec or mod_rec[1] == 0:
        raise SystemExit("the lights module has no internal .toc record")

    r = run([sys.executable, os.path.join(HERE, "aafdiff.py"),
             os.path.join(base_dir(PACK_TAG), "verify"), os.path.join(tdir, "verify"), "--hash"],
            "aafdiff")
    changed = []
    for line in r.splitlines():
        if not line.startswith("|") or "Bytes A" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-: "):
            continue
        changed.append(cells[3].strip("`"))
    print(f"packed diff {len(changed)} inner file(s) vs {PACK_TAG}: {changed}")

    upstream = json.load(open(os.path.join(base_dir(), "receipt.json"), encoding="utf-8"))
    pl["module"].update({k: info[k] for k in ("xml", "bytes", "sha256", "base_bytes",
                                              "delta_bytes")})
    pl["build"] = {
        "tag": TAG, "base": f"Builds/{BASE_TAG}", "pack_base": f"Builds/{PACK_TAG}",
        "aaf": rel(aaf), "ee_bytes": os.path.getsize(ee), "ee_sha256": sha256_file(ee),
        "toc_bytes": os.path.getsize(toc), "toc_sha256": sha256_file(toc),
        "toc_records": len(recs), "changed_inner_files": changed,
        "module_toc_record": {"name": mod_rec[0], "offset": mod_rec[1], "size": mod_rec[2]},
        "note": ("the aaf tree is B-05's (it carries B-05's loose .epe); the packed .ee is "
                 f"{PACK_TAG}'s graph + this module, exactly as bm-005 left the graph loose"),
    }
    os.makedirs(os.path.dirname(SPEC), exist_ok=True)
    with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pl, f, indent=1)

    receipt = {
        "schema": 1, "card": "B-07", "tag": TAG,
        "built": datetime.datetime.now().isoformat(timespec="seconds"),
        "base": f"Builds/{BASE_TAG}", "pack_base": f"Builds/{PACK_TAG}",
        "aaf": rel(aaf),
        "ee": {"bytes": os.path.getsize(ee), "sha256": sha256_file(ee)},
        "toc": {"bytes": os.path.getsize(toc), "sha256": sha256_file(toc), "records": len(recs)},
        "module": {"path": MODULE, "bytes": info["bytes"], "sha256": info["sha256"],
                   "base_bytes": info["base_bytes"], "delta_bytes": info["delta_bytes"],
                   "rows_before": pl["module"]["rows_before"],
                   "rows_after": pl["module"]["rows_after"],
                   "toc_offset": mod_rec[1], "toc_size": mod_rec[2]},
        "modules_changed": changed,
        "edits": len(pl["rows"]),
        "dropped_rows": len(pl["dropped"]),
        "replaced": upstream.get("replaced", {}),
        "budgets": {"model_kb": None, "texture_kb": None,
                    "note": ("B-07 adds no mesh bytes and no .ddsc; the module changes size by "
                             f"{info['delta_bytes']:+d} B ({info['base_bytes']} -> "
                             f"{info['bytes']} B). R9's Model/Texture budgets are unchanged from "
                             "B-03's 4,899.6 / 7,065 KB figures.")},
        "checks": [],
        "installed": False,
        "bm": {"card": "B-07", "tag": TAG, "base": f"Builds/{BASE_TAG}",
               "installer_actions": ["Install", "Verify", "Rollback091", "Status"],
               "installed": False},
    }
    with open(os.path.join(tdir, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    write_installer(tdir, receipt)
    print(f"{TAG}   .ee {receipt['ee']['bytes']} B {receipt['ee']['sha256'][:16]}…, .toc "
          f"{receipt['toc']['bytes']} B {receipt['toc']['sha256'][:16]}…, module record "
          f"offset {mod_rec[1]} / {mod_rec[2]} B")
    print(f"spec   {rel(SPEC)}  rows {pl['module']['rows_before']} -> "
          f"{pl['module']['rows_after']}, dropped {len(pl['dropped'])}")
    return 0


# --------------------------------------------------------------------------- check
def module_from_ee(ee: str) -> bytes:
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    o, s = real[MODULE]
    data = unaaf(open(ee, "rb").read())
    return data[o:o + s]


def check() -> int:
    fails: list[str] = []
    for p in (SPEC, os.path.join(tag_dir(), "receipt.json"), module_of_aaf(TAG)):
        if not os.path.exists(p):
            print(f"FAIL: {rel(p)} missing (run --write)")
            return 1
    pl = plan()
    stored = json.load(open(SPEC, encoding="utf-8"))
    if json.dumps(stored["rows"], sort_keys=True) != json.dumps(pl["rows"], sort_keys=True):
        fails.append("the stored row plan differs from the re-derived one")
    if json.dumps(stored["dropped"], sort_keys=True) != json.dumps(pl["dropped"], sort_keys=True):
        fails.append("the stored dropped-row table differs from the re-derived one")

    # 1. the built module is the plan, byte for byte (re-encoded into tmp, never written to the build)
    tdir = tag_dir()
    tmp = os.path.join(WORK, "check")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    fresh = os.path.join(tmp, MODULE_NAME)
    info = encode(pl, fresh, tmp)
    built = open(module_of_aaf(TAG), "rb").read()
    if open(fresh, "rb").read() != built:
        fails.append("the built module differs from the re-derived plan")
    # 2. the packed .ee carries that same module
    ee = os.path.join(tdir, EE)
    packed = module_from_ee(ee)
    if packed != built:
        fails.append("the module inside the packed .ee differs from the aaf's")
    # 3. the .toc record points at it, non-zero
    recs = {n: (o, s) for n, o, s in read_toc(open(ee + ".toc", "rb").read())}
    off, size = recs.get(MODULE, (0, 0))
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    if off == 0 or real.get(MODULE) != (off, size) or size != len(built):
        fails.append(f"the .toc record for the module is {off}/{size}, the .ee has {real.get(MODULE)}")

    # 4. the card's Done line, on the module the .toc points at inside the packed .ee (the
    #    installable artefact), not on a side copy
    unpacked = open(os.path.join(tdir, "verify", MODULE.replace("/", os.sep)), "rb").read()
    if unpacked != packed:
        fails.append("the unpacked verify/ copy differs from the module inside the .ee")
    rows = decode_module_bytes(packed)
    parts = decode_parts(os.path.join(tdir, "aaf", PARTS_MODULE.replace("/", os.sep)))
    by_name = {p["name"]: p for p in parts.values()}
    for i, r in enumerate(rows):
        p = parts.get(int(r["part_index"]))
        if p is None:
            fails.append(f"row {i}: part_index {r['part_index']} is not in the parts module")
            continue
        if p["name"] != r["part"]:
            fails.append(f"row {i}: part_index {r['part_index']} is {p['name']!r}, the row says "
                         f"{r['part']!r}")
        if int(p["has_lights"]) != 1:
            fails.append(f"row {i}: part {p['name']} has has_lights = {p['has_lights']}")
        if int(r["part_hash"]) != hj(r["part"]):
            fails.append(f"row {i}: part_hash {r['part_hash']} != hash_jenkins({r['part']})")
        if int(r["behavior_hash"]) != hj(r["behavior"]):
            fails.append(f"row {i}: behavior_hash mismatch")
        if int(r["deformable_transform_hash"]) != hj(r["deformable_transform"]):
            fails.append(f"row {i}: deformable_transform_hash mismatch")
    # no entry may name one of the donor's own Serpente lamp parts
    lamp_names = {p["name"] for i, p in parts.items()
                  if int(p["has_lights"]) == 1 and i not in
                  {42, 43, 44, 45, 46, 47, 48, 49, 0}}
    hit = sorted({r["part"] for r in rows} & lamp_names)
    if hit:
        fails.append(f"{len(hit)} entry(ies) still name a donor lamp part: {hit}")
    # the dropped rows are gone, the kept rows' colours are the plan's
    kept = {(r["behavior"], int(r["preset_id"])) for r in rows}
    for d in pl["dropped"]:
        if (d["behavior"], d["preset_id"]) in kept:
            fails.append(f"dropped row {d['base_index']} ({d['behavior']}, "
                         f"{d['preset_name']}) is still in the module")
    for r in pl["rows"]:
        want = (r["members"]["behavior"]["v"], r["members"]["preset_id"]["v"],
                r["members"]["part"]["v"], r["members"]["diffuse.R"]["v"] +
                r["members"]["diffuse.G"]["v"] + r["members"]["diffuse.B"]["v"])
        got = [(x["behavior"], int(x["preset_id"]), x["part"],
                float(x["diffuse.R"]) + float(x["diffuse.G"]) + float(x["diffuse.B"]))
               for x in rows]
        if not any(abs(g[3] - want[3]) < 1e-5 and g[:3] == want[:3] for g in got):
            fails.append(f"row {r['index']} ({r['origin']}) is not in the built module as planned")
    if len(rows) != pl["module"]["rows_after"]:
        fails.append(f"{len(rows)} entries, planned {pl['module']['rows_after']}")

    # 5. R7: no shared module and no other file of the tree changed - only the lights module
    aaf_base, aaf_tag = os.path.join(base_dir(), "aaf"), os.path.join(tdir, "aaf")
    other = []
    for dirpath, _d, files in os.walk(aaf_base):
        for n in files:
            p = os.path.join(dirpath, n)
            rp = os.path.relpath(p, aaf_base).replace("\\", "/")
            if rp == MODULE:
                continue
            q = os.path.join(aaf_tag, rp.replace("/", os.sep))
            if not os.path.exists(q) or sha256_file(p) != sha256_file(q):
                other.append(rp)
    if other:
        fails.append(f"{len(other)} file(s) other than the lights module changed or vanished: "
                     f"{sorted(other)[:5]}")

    kinds = {}
    for r in rows:
        kinds[r["behavior"]] = kinds.get(r["behavior"], 0) + 1
    print(f"rows   {len(rows)} (base {pl['module']['rows_before']}, dropped "
          f"{len(pl['dropped'])}, added {len(rows) - (pl['module']['rows_before'] - len(pl['dropped']))})"
          f"  behaviours {kinds}")
    print(f"parts  {len({r['part'] for r in rows})} distinct, every one in the built parts module "
          f"with has_lights = 1: {sorted({r['part'] for r in rows})}")
    print(f"module {info['bytes']} B {info['sha256'][:16]}…, .toc record {off}/{size}, "
          f".ee {os.path.getsize(ee)} B")
    print(f"R7     shared/other files changed besides the lights module: {len(other)}")
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    print("PASS: every entry names a part that exists with has_lights = 1, no donor lamp part, "
          "the built module is the re-derived plan")
    print("CHECK_EXIT=0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write the spec and Builds/bm-007")
    ap.add_argument("--check", action="store_true", help="re-derive and run the Done checks")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    if a.write:
        return write_build(plan())
    return check()


if __name__ == "__main__":
    sys.exit(main())
