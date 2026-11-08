"""bm_parts_v2.py - B-04: the Batmobile `vehicle_parts.vmodc`, written from the cards that feed it.

`GRAB_BACKLOG.md` §8 (B-04): "1. Remove `door_f_l`/`door_f_r` and their `door_parts` entries
(old PRT-1; keep the index map documented). 2. Add every new part (`parts[]`: name, model
`.lod`, parent, `parent_space_offset` = pivot, damage type, `has_lights`, `is_deformable` 0,
collision ids). 3. Add behaviour entries (`hinged_parts`, `rotating_parts`, `door_parts`,
`aim_part_constraints`) per T-12/TURRET.md. 4. Pack with `eetoc --internal` (R8)."
Done: "`jc3parts.py check` and `jc3adf.py` re-read the built module; every part's model resolves
to a file in the build; `.toc` record for the module has a non-zero offset."

How the module is written
-------------------------
The shipped module cannot be read by `Tools/Gibbed/…ConvertAdf.exe` at all (MODLOG §98/§101) and
the patched reader (`Tools/Gibbed-patched/`, §101a) re-encodes it **+544 B** (§101b), so earlier
cards edited it only by in-place byte patching. B-04 has to add and remove `parts[]` records, which
no byte patch can do, so the module is rewritten through the patched converter's XML:

  1. export `Builds/bm-001/aaf/.../sportsmuscle_vehicle_parts.vmodc` (the identity build) to XML;
  2. remove the two door parts, their `door_parts` entries, their entries in the body's
     `children_part_indices`, and re-parent the four parts that hung on them;
  3. append one `Part` record per new part (B-02 geometry + B-03 lamp parts);
  4. append the `hinged_parts` / `rotating_parts` rows T-12 justifies;
  5. import the XML, and re-read the result with `jc3adf` before it is allowed into a build.

The +544 B is *placement padding, not lost data*: an unchanged export/import re-reads as
2802/2802 rows and 42/42 parts identical (MODLOG "B-04 start"). The rewritten file is therefore not
byte-identical to the shipped one; that is stated in the receipt and in the done section, and
in-game behaviour stays phase Q.

Provenance (R4) - every written value names its source
-----------------------------------------------------
| value | source |
|---|---|
| part names, pivots, parents, LOD files of the 11 cut parts | `Working/Appearance/build_parts/parts_manifest.json` (B-02) |
| lamp part names, pivots, parents, LOD files, 2 reserved indices | `Working/Appearance/build_lights/lights_manifest.json` (B-03) |
| `behavior`, `damage_type`, behaviour channel, rotation axis | `Working/Translation/T8_PARTS.json` rows P-01…P-15 (T-12) |
| `has_lights` = 1 on the 8 lamp parts | B-03 (each carries a `CarLight` block) |
| `is_deformable` = 0 | the card ("`is_deformable` 0") |
| collision ids `-1`/`-1` = no hull, no raycast body | `Working/Translation/t16_collision.json` (T-22) bindings + 599 fleet parts with body -1 / ray -1 in `Research/JC3Grab/PARTS_TABLE.jsonl` |
| `centroid` / `deformation_centroid_offset` = 0 | this module's own four non-deformable wheels carry 0,0,0 (values read from the file being edited) |
| `parent_space_offset` translation | derived: B-02 pivot − the parent part's frame origin chained from this module's own `parent_space_offset` |
| `rotating_parts[].position` | decoded (fleet): identical to the part's own `parent_space_offset` translation in 11/11 shipped rotating rows sampled across 4 modules |
| `rotating_parts[].number_of_blades` = 1 on a gun | decoded (fleet): `advancedassault_gatling_l_barrels` / `_r_barrels` ship blades 1 |
| `rpm_multiplier` 1.0 / `min|max_rpm_visible` -1 / `rpm_opacity_transition` -1 | the module's own type definitions (defaults) |
| hash of every HashString | `rbmhdr.hash_jenkins` (verified: `Land_Body` 934577878, `sportsmuscle_body` 3076414876, model path 1671449206) |

Nothing is guessed: `batmobile_jet` has no rotation axis in T-12 (`joint: null`), so it gets **no**
`rotating_parts` row, and the missile bays / canopy carry the door channel on rows whose `part` is
null, so **no** new `door_parts` row is written. Both are recorded in the spec as omissions.

Usage
    python Tools/scripts/bm_parts.py --write     # spec + Builds/bm-002 (never installs)
    python Tools/scripts/bm_parts.py --check     # no writes: re-read the build, run the Done checks
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
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3adf                                    # noqa: E402
import rbmhdr                                    # noqa: E402
from eetoc import read_toc, sarc_dir, unaaf       # noqa: E402

BASE_TAG = "bm-RC2"
TAG = "bm-RC3-parts"
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
GAME = r"D:\Games\Just Cause 3"
DROP = ("dropzone\\editor\\entities\\jc_vehicles\\01_land\\"
        "v0300_car_kensington_sportsmuscle")
MODELS = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
MODULE = MODELS + "/sportsmuscle_vehicle_parts.vmodc"
MODULE_NAME = "sportsmuscle_vehicle_parts.vmodc"
INTERNAL = ["sportsmuscle_vehicle_parts.vmodc"]
GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
ADF = os.path.join(ROOT, "Tools", "Gibbed-patched", "Gibbed.JustCause3.ConvertAdf.exe")
SPEC = os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts_v2.json")
PARTS_MANIFEST = os.path.join(ROOT, "Working", "Appearance", "build_parts",
                              "parts_manifest.json")
LIGHTS_MANIFEST = os.path.join(ROOT, "Working", "Appearance", "build_lights",
                               "lights_manifest.json")
T12 = os.path.join(ROOT, "Working", "Translation", "T8_PARTS.json")
T22 = os.path.join(ROOT, "Working", "Translation", "t16_collision.json")
PARTS_TABLE = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
HEALTH_MODULE = ("editor/entities/jc_vehicles/00_shared/modules/health/"
                 "lave_health_medium.vmodc")
DEFORM_MODULE = MODELS + "/sportsmuscle_vehicle_deform.vmodc"
CAP_MODEL_KB = 4915.0
SCHEMA = 1


# ------------------------------------------------------------------ helpers
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def member(node, name):
    return next((m for m in node.findall("member") if m.get("name") == name), None)


def string_of(part, name: str) -> str:
    hs = member(part, name)
    return (hs.find("member[@name='string']").text or "")


def set_string(part, name: str, text: str) -> None:
    hs = member(part, name)
    hs.find("member[@name='string']").text = text
    hs.find("member[@name='hash']").text = str(rbmhdr.hash_jenkins(text.encode("ascii")))


def floats(node) -> list[float]:
    return [float(m.text) for m in node.findall("member")]


def set_floats(node, values) -> None:
    kids = node.findall("member")
    assert len(kids) == len(values), (len(kids), len(values))
    for kid, v in zip(kids, values):
        kid.text = format(float(v), ".9g")


def decode_parts(blob: bytes) -> list[dict]:
    return jc3adf.parts(jc3adf.Adf(blob))


def rows_of(blob: bytes) -> dict:
    return {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(blob))}


def health_damage_types(aaf: str) -> list[str]:
    """The health module's `PartDamageType` names, read from the module itself (not typed)."""
    path = os.path.join(aaf, HEALTH_MODULE)
    if not os.path.exists(path):
        return []
    rows = rows_of(open(path, "rb").read())
    out: list[str] = []
    while f"part_damage_types[{len(out)}].type.string" in rows:
        out.append(rows[f"part_damage_types[{len(out)}].type.string"])
    return out


def deform_points(aaf: str) -> list[dict]:
    """Every deform point's part binding, read from the vehicle's own deform module."""
    path = os.path.join(aaf, DEFORM_MODULE)
    if not os.path.exists(path):
        return []
    rows = rows_of(open(path, "rb").read())
    out: list[dict] = []
    while f"points[{len(out)}].from_part_index" in rows:
        i = len(out)
        out.append({"name": rows.get(f"points[{i}].name"),
                    "from_part": rows.get(f"points[{i}].from_part"),
                    "from_part_index": rows.get(f"points[{i}].from_part_index"),
                    "skinned_to_part": rows.get(f"points[{i}].skinned_to_part"),
                    "skinned_to_part_index": rows.get(f"points[{i}].skinned_to_part_index")})
    return out


def tree_hashes(root: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(dirpath, name)
            out[os.path.relpath(path, root).replace("\\", "/")] = sha256_file(path)
    return out


def tree_diff(a: str, b: str) -> dict:
    """Counts for two unpacked `aaf` trees (same scope `aafdiff.py` reports)."""
    ha, hb = tree_hashes(a), tree_hashes(b)
    only_a = sorted(set(ha) - set(hb))
    only_b = sorted(set(hb) - set(ha))
    changed = sorted(k for k in set(ha) & set(hb) if ha[k] != hb[k])
    return {"root_a": rel(a), "root_b": rel(b), "files_a": len(ha), "files_b": len(hb),
            "identical": len(set(ha) & set(hb)) - len(changed), "changed": len(changed),
            "only_in_a": len(only_a), "only_in_b": len(only_b),
            "changed_files": changed, "only_in_a_files": only_a}


# ------------------------------------------------------------------ the plan
def frame_origins(parts: list[dict]) -> dict[int, tuple[float, float, float]]:
    """Absolute frame origin of every part in *this module*, chained from parent_space_offset."""
    by_index = {p["part_index"]: p for p in parts}
    out: dict[int, tuple[float, float, float]] = {}

    def origin(i: int) -> tuple[float, float, float]:
        if i in out:
            return out[i]
        p = by_index[i]
        off = p["parent_space_offset"]
        t = (off[12] or 0.0, off[13] or 0.0, off[14] or 0.0)
        parent = p["parent_part_index"]
        base = (0.0, 0.0, 0.0) if parent is None or parent < 0 or parent not in by_index \
            else origin(parent)
        out[i] = (base[0] + t[0], base[1] + t[1], base[2] + t[2])
        return out[i]

    for i in by_index:
        origin(i)
    return out


def count_fleet_no_hull() -> tuple[int, int]:
    """(parts with body -1 and ray -1, parts total) in PARTS_TABLE.jsonl."""
    hit = total = 0
    with open(PARTS_TABLE, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            for p in row["parts"]:
                total += 1
                if p.get("body") == -1 and p.get("ray") == -1:
                    hit += 1
    return hit, total


def donor_wheel_parts(entity_sub: str = "v0300_car_kensington_sportsmuscle_civilian_01") -> set[int]:
    """The donor's wheel part indices, from PARTS_TABLE.jsonl `wheels[].part` (decoded wheel_parts)."""
    with open(PARTS_TABLE, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if entity_sub in row["entity"]:
                return {w["part"] for w in row["wheels"]}
    raise SystemExit(f"no PARTS_TABLE row for {entity_sub}")


def build_plan() -> dict:
    """Assemble every part row and behaviour row from the named inputs (no hand values)."""
    pm = json.load(open(PARTS_MANIFEST, encoding="utf-8"))
    lm = json.load(open(LIGHTS_MANIFEST, encoding="utf-8"))
    t12 = json.load(open(T12, encoding="utf-8"))
    t22 = json.load(open(T22, encoding="utf-8"))
    base_module = os.path.join(ROOT, "Builds", BASE_TAG, "aaf", MODULE)
    before = decode_parts(open(base_module, "rb").read())
    origins = frame_origins(before)
    by_name = {p["name"]: p for p in before}
    no_hull, parts_total = count_fleet_no_hull()

    rows = {r["part"]: r for r in t12["rows"] if r.get("part")}

    def module_part(name: str) -> dict:
        """B-02/B-03 name (`body`, `wheel_f_l`) -> the part record in the shipped module."""
        for cand in (name, "sportsmuscle_" + name):
            if cand in by_name:
                return by_name[cand]
        raise SystemExit(f"parent {name!r} is not a part of the base module")

    # ---- index map: 0..41 keep their shipped indices (1 and 2 are freed), 42.. are new
    reserved = {l["part"]: l["part_index"] for l in lm["lamps"] if l["part_index"] is not None}
    free = [i for i in range(256) if i >= 42]
    taken = set(reserved.values())
    lamp_indices: dict[str, int] = {}
    cursor = 0
    for lamp in lm["lamps"]:
        name = lamp["part"]
        if name in reserved:
            lamp_indices[name] = reserved[name]
            continue
        while free[cursor] in taken:
            cursor += 1
        lamp_indices[name] = free[cursor]
        taken.add(free[cursor])
    next_free = 50
    cut_indices: dict[str, int] = {}
    for e in pm["entries"]:
        if e["kind"] != "part":
            continue
        while next_free in taken:
            next_free += 1
        cut_indices[e["name"]] = next_free
        taken.add(next_free)
        next_free += 1

    def pivot_of(name: str) -> list[float]:
        for e in pm["entries"]:
            if e["name"] == name:
                return list(e["pivot_m"])
        raise SystemExit(f"no B-02 pivot for {name}")

    new_parts: list[dict] = []
    new_by_name: dict[str, dict] = {}

    def resolve_parent(name: str) -> dict:
        """Base-module part or a part this card adds (the manifests are in parent-first order)."""
        for cand in (name, "sportsmuscle_" + name):
            if cand in by_name:
                return {"name": cand, "part_index": by_name[cand]["part_index"]}
            if cand in new_by_name:
                return {"name": cand, "part_index": new_by_name[cand]["part_index"]}
        raise SystemExit(f"parent {name!r} is neither in the base module nor added here")

    def frame_of(parent: dict) -> list[float]:
        if parent["name"] in by_name:
            return list(origins[parent["part_index"]])
        p = new_by_name[parent["name"]]
        base = p["parent_frame_origin_m"]
        return [base[0] + p["parent_space_offset"][0],
                base[1] + p["parent_space_offset"][1],
                base[2] + p["parent_space_offset"][2]]
    # Translate rule (Q-1 probe 7 crash, 2026-11-02): no shipped car parents a part under a WHEEL part
    # (PARTS_TABLE.jsonl: 174 wheeled entities, 0 cars; the 4 hits are bikes whose wheel part is the fork).
    # The game updates a wheel node's raycast body (Serpente wheels: body -1, ray 22/23/36/37) when the
    # wheel has children -> +0x151410f on a raycast slot with no shape. The AK grab skins the arch lights
    # to the wheel disc/damper bones; in JC3 they hang on the wheel's parent at the same rest position.
    wheel_idx = donor_wheel_parts()
    by_index = {p["part_index"]: p for p in before}
    hoisted: dict[str, str] = {}
    # ---- B-03 lamp parts (geometry already in the parent part's frame: offset identity)
    for lamp in lm["lamps"]:
        name = lamp["part"]
        parent_name = lamp["parent_part"]
        parent = resolve_parent(parent_name)
        if parent["part_index"] in wheel_idx and parent["name"] in by_name:
            up = by_index[by_name[parent["name"]]["parent_part_index"]]
            hoisted[name] = f"{parent['name']} -> {up['name']}"
            parent = {"name": up["name"], "part_index": up["part_index"]}
        pivot = list(lamp["pivot_m"])
        frame = frame_of(parent)
        offset = [pivot[0] - frame[0], pivot[1] - frame[1], pivot[2] - frame[2]]
        new_parts.append({
            "name": name,
            "part_index": lamp_indices[name],
            "parent": parent["name"],
            "parent_index": parent["part_index"],
            "pivot_m": pivot,
            "parent_frame_origin_m": list(frame),
            "parent_space_offset": offset,
            "model": f"{MODELS}/{name}.lod",
            "lod_files": [f"{name}_lod{i}.rbm" for i in (1, 2, 3)],
            "source_dir": "Working/Appearance/build_lights",
            "behaviour": "None",
            "behaviour_hash": 0,
            "behaviour_source": "B-03: static lamp part (`CarLight` + `Window`), no behaviour row",
            "damage_type": "Land_Light",
            "damage_type_source": ("decoded (fleet): every one of the donor's 10 lamp parts in "
                                   "Working/Parts/PRT1_PARTMAP.md carries Land_Light"),
            "has_lights": 1,
            "is_deformable": 0,
            "provenance": {
                "name/pivot/parent/model": "Working/Appearance/build_lights/lights_manifest.json (B-03)",
                "has_lights": "B-03: the part carries a CarLight block",
                "is_deformable": "B-04 card: `is_deformable` 0",
                "parent_space_offset": ("derived: B-03 pivot_m - the parent part's frame origin "
                                        "chained from this module's parent_space_offset"),
            },
        })
        new_by_name[name] = new_parts[-1]
    # ---- B-02 cut parts (vertices relative to their own pivot: offset = pivot - parent frame)
    for e in pm["entries"]:
        if e["kind"] != "part":
            continue
        name = e["name"]
        parent_name = e["parent"]
        parent = resolve_parent(parent_name)
        pivot = list(e["pivot_m"])
        frame = frame_of(parent)
        offset = [pivot[0] - frame[0], pivot[1] - frame[1], pivot[2] - frame[2]]
        row = rows.get(name)
        if row is None:
            raise SystemExit(f"no T-12 row for B-02 part {name}")
        new_parts.append({
            "name": name,
            "part_index": cut_indices[name],
            "parent": parent["name"],
            "parent_index": parent["part_index"],
            "pivot_m": pivot,
            "parent_frame_origin_m": list(frame),
            "parent_space_offset": offset,
            "model": f"{MODELS}/{name}.lod",
            "lod_files": list(e["lod_files"]),
            "source_dir": "Working/Appearance/build_parts",
            "behaviour": row["behaviour"] or "None",
            "behaviour_hash": (0 if not row["behaviour"]
                               else rbmhdr.hash_jenkins(row["behaviour"].encode("ascii"))),
            "behaviour_source": f"T-12 {row['id']} `behaviour`",
            "damage_type": row["damage_type"],
            "damage_type_source": f"T-12 {row['id']} `damage_type` (land-first)",
            "has_lights": 0,
            "is_deformable": 0,
            "t12_row": row["id"],
            "channel": row["behaviour_channel"],
            "provenance": {
                "name/pivot/parent/model": ("Working/Appearance/build_parts/parts_manifest.json "
                                            "(B-02)"),
                "behaviour/damage_type": f"Working/Translation/T8_PARTS.json {row['id']} (T-12)",
                "is_deformable": "B-04 card: `is_deformable` 0",
                "parent_space_offset": ("derived: B-02 pivot_m - the parent part's frame origin "
                                        "chained from this module's parent_space_offset"),
            },
        })
        new_by_name[name] = new_parts[-1]

    # ---- collision ids: no hull, no raycast body (T-22 + the fleet's hull-less pattern)
    for p in new_parts:
        p.update({
            "has_world_collision_shape": 0,
            "world_collision_body_id": -1,
            "raycast_body_id": -1,
            "world_collision_instance_id": -1,
            "raycast_instance_id": -1,
            "collision_source": (f"t16_collision.json (T-22) bindings: a part with no hull is "
                                 f"world_collision_body_id -1; {no_hull}/{parts_total} fleet parts "
                                 f"ship body -1 / ray -1"),
        })

    # ---- behaviour arrays
    by_index_new = {p["name"]: p for p in new_parts}
    hinged = [by_index_new[n] for n in [p["name"] for p in new_parts]
              if by_index_new[n].get("channel") == "hinged"]
    rotating_rows = []
    omitted = []
    for p in new_parts:
        if p.get("channel") != "rotating":
            continue
        row = rows[p["name"]]
        axis = (row.get("joint") or {}).get("axis_jc3")
        if axis is None:
            omitted.append({
                "array": "rotating_parts", "part": p["name"], "t12_row": row["id"],
                "why": ("T-12 records `joint: null` for this part - its bones translate and no "
                        "rotation is animated, so `rotation_axis` has no source (R4: no value "
                        "without provenance). The row is left out, not guessed."),
                "unblocks": "a decoded rotation axis for this part, or a fleet carrier probe",
            })
            continue
        rotating_rows.append({
            "part_index": p["part_index"],
            "part": p["name"],
            "number_of_blades": 1,
            "number_of_blades_source": ("decoded (fleet): `advancedassault_gatling_l_barrels` / "
                                        "`_r_barrels` ship number_of_blades 1"),
            "position": p["parent_space_offset"],
            "position_source": ("decoded (fleet): equals the part's own parent_space_offset "
                                "translation in 11/11 shipped rotating rows sampled across 4 modules"),
            "rotation_axis": list(axis),
            "rotation_axis_source": f"T-12 {row['id']} `joint.axis_jc3`",
            "rpm_multiplier": 1.0,
            "min_rpm_visible": -1.0,
            "max_rpm_visible": -1.0,
            "rpm_opacity_transition": -1.0,
            "rpm_source": "this module's own type definitions (defaults)",
        })
    door_rows_before = [p for p in before if p["name"] in ("sportsmuscle_door_f_l",
                                                           "sportsmuscle_door_f_r")]
    for row in [r for r in t12["rows"] if not r.get("part") and r.get("behaviour_channel")]:
        omitted.append({
            "array": {"door": "door_parts", "hinged": "hinged_parts",
                      "rotating": "rotating_parts"}.get(row["behaviour_channel"],
                                                         row["behaviour_channel"]),
            "part": None, "t12_row": row["id"],
            "why": (f"T-12 {row['id']} carries the `{row['behaviour_channel']}` channel but its "
                    f"`part` is null (`{row['behaviour']}`, geometry stays in the shell), so no "
                    f"part row can reference it"),
            "unblocks": "a part that owns that geometry",
        })

    removals = []
    for p in door_parts_named(before):
        removals.append({
            "name": p["name"], "part_index": p["part_index"],
            "why": "B-04 step 1 / PRT-1: the Batmobile has no doors",
            "door_parts_entry": p["part_index"] in (1, 2, 25),
        })
    orphans = [p for p in before if p["parent_part_index"] in
               [d["part_index"] for d in door_parts_named(before)]]
    return {
        "before": before,
        "origins": origins,
        "removals": removals,
        "reparent": [{"name": p["name"], "part_index": p["part_index"],
                      "from": p["parent_part_index"], "to": 0,
                      "why": ("its parent is one of the removed door parts; the nearest surviving "
                              "ancestor is `sportsmuscle_body` (0)")} for p in orphans],
        "new_parts": new_parts,
        "hoisted_off_wheels": hoisted,
        "wheel_parts": sorted(wheel_idx),
        "hinged": [p["part_index"] for p in hinged],
        "hinged_parts": [p["name"] for p in hinged],
        "rotating": rotating_rows,
        "omitted": omitted,
        "aim_part_constraints": [],
        "aim_note": ("G2-13 `Research/JC3Grab/TURRET.md`: `aim_part_constraints` = 85 rows in 17 of "
                     "78 modules, all suspension, **0 on the six turreted vehicles** - so the "
                     "turret/cannon aim is not a module array and no row is written (T-12 gives "
                     "every weapon part channel `none`)."),
        "index_map": {
            "removed": [1, 2],
            "kept": [p["part_index"] for p in before
                     if p["part_index"] not in (1, 2)],
            "new": {p["name"]: p["part_index"] for p in new_parts},
            "note": ("`part_index` is a field, not the array position: the surviving records keep "
                     "their shipped indices (so 1 and 2 are now free) and every reference "
                     "(`parent_part_index`, `children_part_indices`, `wheel_parts`, `door_parts`) "
                     "keeps its meaning."),
        },
        "no_hull": f"{no_hull}/{parts_total}",
    }


def door_parts_named(parts: list[dict]) -> list[dict]:
    return [p for p in parts if p["name"] in ("sportsmuscle_door_f_l", "sportsmuscle_door_f_r")]


# ------------------------------------------------------------------ XML surgery
def new_array(inst, wrap, name: str, element_type: str, element_hash: str, items: list,
              new_id: int):
    """Turn an empty (`id=-1`) array reference into a hoisted data array.

    Gibbed indexes an instance's string tables by member id, so ids must stay 0..N-1 with
    N = the number of top-level members; the caller passes the next free id.
    """
    ref = member(wrap, name)
    assert ref.get("id") == "-1", (name, ref.get("id"))
    ref.set("id", str(new_id))
    arr = ET.SubElement(inst, "member")
    arr.set("name", name)
    arr.set("gbltype", "Array")
    arr.set("id", str(new_id))
    arr.set("type-hash", ref.get("type-hash"))
    arr.set("type", f"A[{element_type}]")
    return arr, element_hash


def write_module(plan: dict, base_module: str, out_module: str, workdir: str) -> dict:
    """Export -> edit -> import the parts module; return what the XML edit did."""
    xml_in = os.path.join(workdir, "base.xml")
    xml_out = os.path.join(workdir, "bm_vehicle_parts.xml")
    r = subprocess.run([ADF, "--e", base_module, xml_in], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ConvertAdf export failed: {r.stdout[-300:]}{r.stderr[-300:]}")
    root = ET.fromstring(open(xml_in, encoding="utf-8-sig").read())
    inst = root.find("instances/instance")
    wrap = member(inst, "VehicleParts")
    parts_el = member(inst, "parts")
    tdump = {t.get("name"): t for t in root.find("type-definitions").findall("type")}
    part_hash = tdump["Part"].get("name-hash")

    # --- 1. remove the door parts, their own hoisted arrays *stay* (ids must remain contiguous)
    drop_names = [d["name"] for d in plan["removals"]]
    killed = set()
    for ent in list(parts_el.findall("member")):
        if string_of(ent, "name") in drop_names:
            for m in ent.findall("member"):
                if m.get("is-reference") == "yay" and m.get("id") not in (None, "-1"):
                    killed.add(m.get("id"))          # emptied below, never removed
                    data = next(x for x in inst.findall("member") if x.get("id") == m.get("id"))
                    for kid in list(data.findall("member")):
                        data.remove(kid)
            parts_el.remove(ent)
    # --- 2. door_parts entries for indices 1 and 2
    doors = member(inst, "door_parts")
    for ent in list(doors.findall("member")):
        if member(ent, "part_index").text in ("1", "2"):
            doors.remove(ent)
    # --- 3. the body must not list the removed children; orphans move to the body
    reparent = {r["part_index"]: r["to"] for r in plan["reparent"]}
    for ent in parts_el.findall("member"):
        pi = int(member(ent, "part_index").text)
        if pi in reparent:
            member(ent, "parent_part_index").text = str(reparent[pi])
            # world transform kept: local = W_child @ inv(W_new_parent) (row-vector chain, as bm_hide)
            import numpy as np
            bi = {q["part_index"]: q for q in plan["before"]}
            def W(q):
                M = np.array(q["parent_space_offset"], np.float64).reshape(4, 4)
                up = bi.get(q["parent_part_index"])
                return M @ W(up) if up is not None and up is not q else M
            local = W(bi[pi]) @ np.linalg.inv(W(bi[reparent[pi]]))
            set_floats(member(ent, "parent_space_offset"), local.reshape(-1).tolist())
        kids = member(ent, "children_part_indices")
        if kids.get("id") not in (None, "-1"):
            data = next(x for x in inst.findall("member") if x.get("id") == kids.get("id"))
            for kid in list(data.findall("member")):
                if kid.text in ("1", "2") and (plan["removals"] or pi != 0):
                    data.remove(kid)   # B-04R keeps the doors: only the body still lists them
    if not plan["removals"] and reparent:   # B-04R: kept parents give their re-parented children up
        arrays = {x.get("id"): x for x in inst.findall("member") if x.get("id")}
        def kid_array(ent):
            ref = member(ent, "children_part_indices").get("id")
            return arrays.get(ref) if ref not in (None, "-1") else None
        by_pi = {int(member(e, "part_index").text): e for e in parts_el.findall("member")}
        for ent in parts_el.findall("member"):
            arr = kid_array(ent)
            for kid in list(arr.findall("member")) if arr is not None else []:
                if int(kid.text) in reparent and int(member(ent, "part_index").text) != reparent[int(kid.text)]:
                    arr.remove(kid)
        for pi, to in sorted(reparent.items()):
            arr = kid_array(by_pi[to])
            proto = arr.find("member")
            if str(pi) not in [k.text for k in arr.findall("member")]:
                kid = ET.SubElement(arr, "member", dict(proto.attrib))
                kid.attrib.pop("offset-in-file", None)
                kid.text, kid.tail = str(pi), proto.tail
    # --- 4. append one Part record per new part, cloned from a childless template
    template = next(e for e in parts_el.findall("member")
                    if string_of(e, "name") == "sportsmuscle_plate_r")
    for ref in ("children_part_indices", "hide_parts_when_broken",
                "meshswap_parts_when_broken", "loosen_parts_when_broken",
                "break_parts_when_broken"):
        assert member(template, ref).get("id") == "-1", ref
    for ent in parts_el.findall("member"):   # B-04R: parts kept in the index space but not drawn
        if string_of(ent, "name") in plan.get("start_deleted", ()):
            member(ent, "starts_deleted").text = "1"
    for p in plan["new_parts"]:
        clone = copy.deepcopy(template)
        clone.set("type-hash", part_hash)
        set_string(clone, "name", p["name"])
        set_string(clone, "damage_type", p["damage_type"])
        set_string(clone, "behavior", p["behaviour"])
        set_string(clone, "model", p["model"])
        set_string(clone, "model_swap", "")
        member(clone, "part_index").text = str(p["part_index"])
        member(clone, "parent_part_index").text = str(p["parent_index"])
        off = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0,
               p["parent_space_offset"][0], p["parent_space_offset"][1],
               p["parent_space_offset"][2], 1]
        set_floats(member(clone, "parent_space_offset"), off)
        set_floats(member(clone, "centroid"), [0, 0, 0, 0])
        set_floats(member(clone, "deformation_centroid_offset"), [0, 0, 0, 0])
        for flag, value in (("is_deformable", 0), ("has_lights", p["has_lights"]),
                            ("has_world_collision_shape", 0),
                            ("world_collision_body_id", -1), ("raycast_body_id", -1),
                            ("world_collision_instance_id", -1), ("raycast_instance_id", -1),
                            ("grandpa_world_instance_id", -1), ("grandpa_raycast_instance_id", -1),
                            ("constraint_index", p.get("constraint_index", -1))):
            member(clone, flag).text = str(value)
        parts_el.append(clone)
    if plan.get("link_children"):   # B-04R: every new part is listed by its parent, as every vanilla part is
        arrays = {x.get("id"): x for x in inst.findall("member") if x.get("id")}
        by_pi = {int(member(e, "part_index").text): e for e in parts_el.findall("member")}
        for p in plan["new_parts"]:
            ref = member(by_pi[p["parent_index"]], "children_part_indices")
            if ref.get("id") in (None, "-1"):
                nid = str(len(list(inst)))
                arr = ET.SubElement(inst, "member", {"name": "children_part_indices", "gbltype": "Array",
                                                     "id": nid, "type-hash": ref.get("type-hash"),
                                                     "type": ref.get("type")})
                ref.set("id", nid)
                arrays[nid] = arr
            kid = ET.SubElement(arrays[ref.get("id")], "member", {"gbltype": "Primitive", "type": "int8"})
            kid.text = str(p["part_index"])
    # behaviour name of the vanilla template is "None" with hash 0; keep every HashString honest
    for ent in parts_el.findall("member"):
        name = string_of(ent, "name")
        if name not in [p["name"] for p in plan["new_parts"]]:
            continue
        beh = member(ent, "behavior")
        p = next(x for x in plan["new_parts"] if x["name"] == name)
        beh.find("member[@name='hash']").text = str(p["behaviour_hash"])

    # --- 5. behaviour arrays (ids continue from the instance's member count)
    added = []
    next_id = len(list(inst))
    if plan["hinged"]:
        arr, _h = new_array(inst, wrap, "hinged_parts", "HingedPart",
                            tdump["HingedPart"].get("name-hash"), plan["hinged"], next_id)
        for pi in plan["hinged"]:
            item = ET.SubElement(arr, "member")
            item.set("gbltype", "Structure")
            item.set("type-hash", tdump["HingedPart"].get("name-hash"))
            item.set("type", "HingedPart")
            m = ET.SubElement(item, "member")
            m.set("name", "part_index")
            m.set("gbltype", "Primitive")
            m.set("type", "int8")
            m.text = str(pi)
        added.append(("hinged_parts", len(plan["hinged"]), next_id))
        next_id += 1
    if plan["rotating"]:
        arr, _h = new_array(inst, wrap, "rotating_parts", "RotatingPart",
                            tdump["RotatingPart"].get("name-hash"), plan["rotating"], next_id)
        for row in plan["rotating"]:
            item = ET.SubElement(arr, "member")
            item.set("gbltype", "Structure")
            item.set("type-hash", tdump["RotatingPart"].get("name-hash"))
            item.set("type", "RotatingPart")
            # members MUST be emitted in the type's declared order: the importer lays values
            # out by position inside the structure, not by name
            for name, kind, value in (("part_index", "int8", row["part_index"]),
                                      ("number_of_blades", "int8", row["number_of_blades"])):
                m = ET.SubElement(item, "member")
                m.set("name", name)
                m.set("gbltype", "Primitive")
                m.set("type", kind)
                m.text = str(value)
            for name, values in (("position", row["position"]),
                                 ("rotation_axis", row["rotation_axis"])):
                m = ET.SubElement(item, "member")
                m.set("name", name)
                m.set("gbltype", "InlineArray")
                m.set("type-hash", "3897827182")
                m.set("type", "IA[float]")
                for v in list(values):
                    k = ET.SubElement(m, "member")
                    k.set("gbltype", "Primitive")
                    k.set("type", "float")
                    k.text = format(float(v), ".9g")
            for name, value in (("rpm_multiplier", row["rpm_multiplier"]),
                                ("min_rpm_visible", row["min_rpm_visible"]),
                                ("max_rpm_visible", row["max_rpm_visible"]),
                                ("rpm_opacity_transition", row["rpm_opacity_transition"])):
                m = ET.SubElement(item, "member")
                m.set("name", name)
                m.set("gbltype", "Primitive")
                m.set("type", "float")
                m.text = format(float(value), ".9g")
        added.append(("rotating_parts", len(plan["rotating"]), next_id))
        next_id += 1

    ET.ElementTree(root).write(xml_out, encoding="utf-8", xml_declaration=True)
    r = subprocess.run([ADF, "--i", xml_out, out_module], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("ConvertAdf import failed:\n"
                         + "\n".join((r.stdout + r.stderr).splitlines()[:6]))
    # the rewritten module must decode before it is allowed anywhere near a build
    after = decode_parts(open(out_module, "rb").read())
    if len(after) != len(plan["before"]) - len(plan["removals"]) + len(plan["new_parts"]):
        raise SystemExit(f"re-read {len(after)} parts, expected "
                         f"{len(plan['before']) - len(plan['removals']) + len(plan['new_parts'])}")
    for p in plan["new_parts"]:
        got = next((q for q in after if q["part_index"] == p["part_index"]), None)
        if not got or got["name"] != p["name"] or got["model"] != p["model"]:
            raise SystemExit(f"new part {p['name']} did not survive the re-encode")
    return {"arrays": added, "xml": rel(xml_out)}


# ------------------------------------------------------------------ build
def write_lods(aaf: str, plan: dict, modules_dir: str) -> list[dict]:
    """`.lod` for each new part: the LOD list then the trailing distance, vanilla layout."""
    made = []
    for p in plan["new_parts"]:
        lines = [f"{MODELS}/{f}" for f in p["lod_files"]]
        while len(lines) < 5:
            lines.append("")
        text = "\r\n".join(lines + ["1.0"]) + "\r\n"
        path = os.path.join(aaf, MODELS, f"{p['name']}.lod")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        made.append(rel(path))
    return made


def copy_meshes(aaf: str, plan: dict) -> list[str]:
    copied = []
    for p in plan["new_parts"]:
        src_dir = os.path.join(ROOT, p["source_dir"])
        for name in p["lod_files"]:
            src = os.path.join(src_dir, name)
            if not os.path.exists(src):
                raise SystemExit(f"{p['name']}: missing {src}")
            dst = os.path.join(aaf, MODELS, name)
            shutil.copyfile(src, dst)
            copied.append(name)
    return copied


def used_model_bytes(aaf: str, parts: list[dict]) -> tuple[int, int]:
    """(bytes of the distinct .rbm files the module's part models reference, files)"""
    seen, total = set(), 0
    for p in parts:
        lod = os.path.join(aaf, p["model"])
        if not os.path.exists(lod):
            continue
        for line in open(lod, encoding="utf-8").read().splitlines():
            line = line.strip()
            if not line.endswith(".rbm") or line in seen:
                continue
            seen.add(line)
            path = os.path.join(aaf, line)
            if os.path.exists(path):
                total += os.path.getsize(path)
    return total, len(seen)


def centroid_note() -> str:
    """What the base module's non-deformable parts actually hold, measured (not rounded)."""
    base_module = os.path.join(ROOT, "Builds", BASE_TAG, "aaf", MODULE)
    parts = decode_parts(open(base_module, "rb").read())
    # only the *float noise floor* counts: a centroid axis that reads as zero but is not exactly 0.
    # A real centroid coordinate (e.g. 2.56, or the steering wheel's -0.428) is not noise.
    tiny = [(p["part_index"], v) for p in parts if not p.get("is_deformable")
            for v in p.get("centroid", []) if 0 < abs(v) < 1e-6]
    if not tiny:
        return ("the game's use of `centroid` for a non-deformable part is UNKNOWN; every "
                "non-deformable part in the base module carries exactly 0.0")
    noise = max(abs(v) for _i, v in tiny)
    return ("the game's use of `centroid` for a non-deformable part is UNKNOWN; the "
            f"{len({i for i, _v in tiny})} non-deformable parts whose centroid reads as zero "
            f"carry 0, +-{noise:.3e}, 0, 0 (float noise, not a value), so \"0,0,0\" is a "
            "rounding; the new parts write exactly 0.0")


def hinged_carrier(aaf: str, plan: dict) -> dict:
    """Which members the built module's `hinged_parts` rows actually carry, and T-12's extents."""
    module = os.path.join(aaf, MODULE)
    rows = rows_of(open(module, "rb").read()) if os.path.exists(module) else {}
    members = sorted({k.split(".", 1)[1] for k in rows
                      if k.startswith("hinged_parts[") and "." in k})
    t12 = json.load(open(T12, encoding="utf-8"))
    by_part = {r["part"]: r for r in t12["rows"] if r.get("part")}
    spans = {}
    for p in plan["new_parts"]:
        row = by_part.get(p["name"])
        if not row or not row.get("joint"):
            continue
        spans[p["name"]] = max((c["span_deg"] for c in row["joint"].get("candidates", [])),
                               default=None)
    return {"row_members": members,
            "note": ("`HingedPart` in this module carries only the member(s) listed in "
                     "`row_members`; T-12's decoded travel per part (`t12_span_deg`) has no "
                     "member to travel in, so the flap extents are NOT written by this "
                     "module and stay a T-12/Q-1 row"),
            "t12_span_deg": spans}


def spec_document(plan: dict, module_written: dict, receipt_like: dict, aaf: str) -> dict:
    new = plan["new_parts"]
    health = health_damage_types(aaf)
    unmapped = [{"part": p["name"], "damage_type": p["damage_type"],
                 "resolves_through": "Default"}
                for p in new if p["damage_type"] not in health]
    base_aaf = os.path.join(ROOT, "Builds", BASE_TAG, "aaf")
    diff = tree_diff(base_aaf, aaf)
    return {
        "schema": SCHEMA,
        "card": "B-04",
        "generator": "Tools/scripts/bm_parts.py",
        "scope": ("`sportsmuscle_vehicle_parts.vmodc`: PRT-1 door removal + the B-02/B-03 parts "
                  "+ the behaviour rows T-12 justifies"),
        "inputs": {
            "base_module": f"Builds/{BASE_TAG}/aaf/{MODULE}",
            "parts": "Working/Appearance/build_parts/parts_manifest.json (B-02)",
            "lights": "Working/Appearance/build_lights/lights_manifest.json (B-03)",
            "t12": "Working/Translation/T8_PARTS.json (T-12)",
            "t22": "Working/Translation/t16_collision.json (T-22)",
            "t18": "Working/Translation/t14_lights.json (T-18)",
            "turret": "Research/JC3Grab/TURRET.md (G2-13)",
            "fleet_parts": "Research/JC3Grab/PARTS_TABLE.jsonl",
            "converter": "Tools/Gibbed-patched/Gibbed.JustCause3.ConvertAdf.exe (MODLOG §101a)",
        },
        "before": {
            "parts": len(plan["before"]),
            "bytes": receipt_like.get("base_module_bytes"),
            "door_parts": [p["part_index"] for p in plan["before"]
                           if p["part_index"] in (1, 2, 25)],
        },
        "removals": plan["removals"],
        "reparent": plan["reparent"],
        "index_map": plan["index_map"],
        "parts": new,
        "behaviour": {
            "hinged_parts": {"rows": plan["hinged"], "parts": plan["hinged_parts"],
                             "source": "T-12 rows with `behaviour_channel: hinged` (AirBrake)",
                             **hinged_carrier(aaf, plan)},
            "rotating_parts": {"rows": plan["rotating"],
                               "source": "T-12 rows with `behaviour_channel: rotating`"},
            "door_parts": {"rows": [25],
                           "source": ("the shipped list minus 1 and 2: 25 = "
                                      "`sportsmuscle_hood_signature` (PRT1_PARTMAP.md)")},
            "aim_part_constraints": {"rows": plan["aim_part_constraints"],
                                     "source": plan["aim_note"]},
        },
        "omissions": plan["omitted"],
        "done": {
            "clause_1": {
                "card": "`jc3parts.py check` and `jc3adf.py` re-read the built module",
                "carried_by": [
                    "python Tools/scripts/bm_parts.py --check (step 2: jc3adf on the "
                    ".toc-sliced bytes)",
                    "python Tools/scripts/jc3adf.py info|dump <built module>"],
                "donor_side_only": ("`jc3parts.py check` does NOT read the build: it reads "
                                    "Research/JC3Grab/ENTITIES.md, "
                                    "Working/Translation/current.json (build=Builds/test-091) "
                                    "and PARTS_TABLE.jsonl, and prints `donor table has 42 "
                                    "parts` against this build's 59"),
            },
            "clause_2": {
                "card": "every part's model resolves to a file in the build",
                "carried_by": ["python Tools/scripts/bm_parts.py --check (step 3)"],
            },
            "clause_3": {
                "card": "the .toc record for the module has a non-zero offset",
                "carried_by": ["python Tools/scripts/bm_parts.py --check (step 1)"],
            },
        },
        "unknowns": [
            centroid_note(),
            "`sportsmuscle_vehicle_deform.vmodc` still names parts 1 and 2 as deform targets - the "
            "card edits the parts module only, so that file is untouched (open item; "
            "`bm_parts.py --check` step 7 reads the built deform module and prints the count)",
            "the existing body/wheel parts keep the shipped Serpente transforms; B-02 re-pivoted "
            "the geometry, so the body/wheel re-emit is still owed (named in the done section)",
            "" + str(len(unmapped)) + " of the " + str(len(new)) + " new parts use a damage type "
            "with no `PartDamageType` row in this vehicle's health module, so they resolve through "
            "`Default` at runtime - see `damage_types_unmapped` (B-09 owns the table)",
        ],
        "damage_types_unmapped": {
            "health_module": HEALTH_MODULE,
            "health_module_types": health,
            "rows": unmapped,
            "note": ("values are T-12's (correct provenance); this card creates the parts, B-09 "
                     "owns the damage table, so the fallback is recorded here instead of hidden"),
        },
        "diff": {
            "scope": "the `aaf` unpacked trees only (Builds/<tag>/verify/ duplicates every file)",
            **diff,
            "note": ("`only_in_a` names files the base `aaf` has and this one does not; the file a "
                     "whole-root diff reports as base-only, bm-001's `applied.json` "
                     "({\"applied\": []}, B-01's empty record), sits outside these trees. A "
                     "whole-root diff is NOT this number: `verify/` duplicates every changed and "
                     "new file, so the roots differ by more files than the aaf trees do"),
        },
        "module": module_written,
        "summary": {
            "diff_changed": diff["changed"],
            "diff_only_in_build": diff["only_in_b"],
            "damage_types_unmapped": len(unmapped),
            "parts_before": len(plan["before"]),
            "parts_after": len(plan["before"]) - len(plan["removals"]) + len(new),
            "parts_added": len(new),
            "parts_removed": len(plan["removals"]),
            "reparented": len(plan["reparent"]),
            "hinged_rows": len(plan["hinged"]),
            "rotating_rows": len(plan["rotating"]),
            "door_rows": 1,
            "aim_rows": 0,
            "omitted_rows": len(plan["omitted"]),
        },
    }


def write_build(plan: dict) -> int:
    base_dir = os.path.join(ROOT, "Builds", BASE_TAG)
    tag_dir = os.path.join(ROOT, "Builds", TAG)
    base_ee = os.path.join(base_dir, EE)
    for p in (os.path.join(base_dir, "aaf"), base_ee, base_ee + ".toc"):
        if not os.path.exists(p):
            raise SystemExit(f"base build incomplete: {rel(p)}")
    if os.path.exists(tag_dir):
        shutil.rmtree(tag_dir)
    os.makedirs(tag_dir)
    shutil.copytree(os.path.join(base_dir, "aaf"), os.path.join(tag_dir, "aaf"))
    aaf = os.path.join(tag_dir, "aaf")
    print(f"tree   {rel(aaf)} (copied from {BASE_TAG})")

    work = os.path.join(ROOT, "tmp", "b04", "build")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    if True:
        module_out = os.path.join(work, MODULE_NAME)
        info = write_module(plan, os.path.join(base_dir, "aaf", MODULE), module_out, work)
        shutil.copyfile(module_out, os.path.join(aaf, MODULE))
        info["bytes"] = os.path.getsize(module_out)
        info["sha256"] = sha256_file(module_out)
        base_bytes = os.path.getsize(os.path.join(base_dir, "aaf", MODULE))
        info["base_bytes"] = base_bytes
        info["delta_bytes"] = info["bytes"] - base_bytes
        print(f"module {MODULE_NAME}: {base_bytes} -> {info['bytes']} B "
              f"({info['delta_bytes']:+d}), arrays {info['arrays']}")

    lods = write_lods(aaf, plan, MODELS)
    meshes = copy_meshes(aaf, plan)
    # SmallPack packs only what `@files.xml` lists (deploy.py step 2, MODLOG §103a)
    from deploy import add_to_manifest
    listed = add_to_manifest(aaf, [f"{MODELS}/{n}" for n in meshes] + [
        f"{MODELS}/{p['name']}.lod" for p in plan["new_parts"]])
    print(f"meshes {len(meshes)} .rbm + {len(lods)} .lod, {listed} registered in @files.xml")

    ee = os.path.join(tag_dir, EE)
    r = subprocess.run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf, ee],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"SmallPack failed: {r.stdout[-400:]}{r.stderr[-400:]}")
    shutil.rmtree(os.path.join(tag_dir, "verify"), ignore_errors=True)
    r = subprocess.run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee,
                        os.path.join(tag_dir, "verify")], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"SmallUnpack failed: {r.stdout[-400:]}{r.stderr[-400:]}")

    # aafdiff against the base build's own unpacked tree
    r = subprocess.run([sys.executable, os.path.join(HERE, "aafdiff.py"),
                        os.path.join(base_dir, "verify"), os.path.join(tag_dir, "verify"),
                        "--hash"], capture_output=True, text=True)
    changed = []
    for line in r.stdout.splitlines():
        if not line.startswith("|") or "Bytes A" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-: "):
            continue
        changed.append(cells[3].strip("`"))
    print(f"diff   {len(changed)} file(s) changed vs {BASE_TAG}")

    toc = ee + ".toc"
    r = subprocess.run([sys.executable, os.path.join(HERE, "eetoc.py"), "patch", ee,
                        base_ee + ".toc", "--base-ee", base_ee,
                        "--internal", MODULE_NAME, "--include-lod", "-o", toc],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"eetoc patch failed: {r.stdout[-400:]}{r.stderr[-400:]}")
    print("toc    " + r.stdout.strip().splitlines()[-1])

    recs = read_toc(open(toc, "rb").read())
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    bad = [(n, (o, s), real.get(n)) for n, o, s in recs if o and real.get(n) != (o, s)]
    if bad:
        raise SystemExit(f"{len(bad)} internal .toc record(s) disagree with the .ee: {bad[:3]}")
    mod_rec = next((x for x in recs if x[0].endswith(MODULE_NAME)), None)

    parts_after = decode_parts(open(os.path.join(aaf, MODULE), "rb").read())
    used, files = used_model_bytes(aaf, parts_after)
    base_parts = decode_parts(open(os.path.join(base_dir, "aaf", MODULE), "rb").read())
    base_used, base_files = used_model_bytes(os.path.join(base_dir, "aaf"), base_parts)
    base_rec = json.load(open(os.path.join(base_dir, "receipt.json"), encoding="utf-8"))

    info["xml_sha256"] = sha256_file(info["xml"]) if info.get("xml") and \
        os.path.exists(info["xml"]) else None
    info["xml_bytes"] = os.path.getsize(info["xml"]) if info.get("xml") and \
        os.path.exists(info["xml"]) else None
    info["xml_scope"] = ("scratch: `tmp/` is disposable and `--write` regenerates this file; "
                         "`--check` compares it only when it is present, so the pointer cannot "
                         "dangle silently. The durable record is this module's sha256.")
    spec = spec_document(plan, {k: info[k] for k in ("bytes", "sha256", "base_bytes",
                                                    "delta_bytes", "arrays", "xml",
                                                    "xml_sha256", "xml_bytes", "xml_scope")},
                         {"base_module_bytes": info["base_bytes"]}, aaf)
    spec["build"] = {
        "tag": TAG, "ee_bytes": os.path.getsize(ee), "ee_sha256": sha256_file(ee),
        "toc_bytes": os.path.getsize(toc), "toc_sha256": sha256_file(toc),
        "toc_records": len(recs), "changed_files": changed,
        "module_toc_record": {"name": mod_rec[0], "offset": mod_rec[1],
                              "size": mod_rec[2]} if mod_rec else None,
        "meshes_copied": len(meshes), "lods_written": len(lods),
        "model_bytes": used, "model_files": files,
        "model_kb": round(used / 1024.0, 3), "cap_kb": CAP_MODEL_KB,
    }
    os.makedirs(os.path.dirname(SPEC), exist_ok=True)
    with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(spec, f, indent=1)

    receipt = {
        "tag": TAG,
        "built": datetime.datetime.now().isoformat(timespec="seconds"),
        "base": f"Builds/{BASE_TAG}",
        "src": rel(aaf),
        "card": "B-04",
        "ee": {"bytes": os.path.getsize(ee), "sha256": sha256_file(ee)},
        "toc": {"bytes": os.path.getsize(toc), "sha256": sha256_file(toc),
                "records": len(recs), "ee_entries": len(real)},
        "module": {"path": MODULE, "bytes": info["bytes"], "sha256": info["sha256"],
                   "base_bytes": info["base_bytes"], "delta_bytes": info["delta_bytes"],
                   "toc_offset": mod_rec[1] if mod_rec else 0,
                   "toc_size": mod_rec[2] if mod_rec else 0},
        "modules_changed": [x for x in changed if x.endswith(".vmodc")],
        "meshes_added": meshes,
        "lods_added": [os.path.basename(x) for x in lods],
        "changed_files": changed,
        "edits": len(plan["new_parts"]) + len(plan["removals"]),
        "replaced": base_rec.get("replaced", {}),
        "textures": 0,
        "budgets": {"model_kb": round(used / 1024.0, 3), "model_cap_kb": CAP_MODEL_KB,
                    "model_files": files,
                    "base_model_kb": round(base_used / 1024.0, 3),
                    "delta_kb": round((used - base_used) / 1024.0, 3),
                    "textures_added": 0,
                    "note": ("model bytes = every distinct .rbm reachable from the built "
                             "module's part models. This is NOT the R9 appearance figure: it "
                             "also counts the 40 shipped Serpente part meshes the module still "
                             "references (B-02 measured the appearance set instead: 4,790.9 KB, "
                             "B-03's net 4,899.6 of 4,915). bm-002 does not re-emit body/wheels, "
                             "so R9 is reported as the delta against bm-001 and stays open until "
                             "that re-emit lands. No .ddsc is added, so the texture budget is "
                             "unchanged.")},
        "checks": [],
        "installed": False,
        "bm": {"card": "B-04", "tag": TAG, "base": f"Builds/{BASE_TAG}",
               "installer_actions": ["Install", "Verify", "Rollback091", "Status"],
               "installed": False},
    }
    with open(os.path.join(tag_dir, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    write_installer(tag_dir, receipt)
    # the receipt must carry the Done results, not just the hashes: run the card's own check now
    # and record what it actually returned (B-04 polish, review issue 8).
    record: list[dict] = []
    rc = check(record=record)
    receipt["checks"] = record
    with open(os.path.join(tag_dir, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    print(f"{TAG}   .ee {receipt['ee']['bytes']} B {receipt['ee']['sha256'][:16]}…, "
          f".toc {receipt['toc']['bytes']} B, module record offset "
          f"{receipt['module']['toc_offset']}")
    return rc


def write_installer(tag_dir: str, receipt: dict) -> None:
    body = f"""<#
    {TAG} installer (B-04 parts module). Generated by Tools/scripts/bm_parts.py, never run.
    Close the game before -Action Install. Rollback091 restores test-091.
#>
[CmdletBinding()]
param([ValidateSet('Install','Verify','Rollback091','Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$GameDir = '{GAME}'
$EeT = Join-Path $GameDir '{DROP}\\{EE}'
$EeSha = '{receipt["ee"]["sha256"]}'
$TocSha = '{receipt["toc"]["sha256"]}'
$B = '{tag_dir}'
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
    with open(os.path.join(tag_dir, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
        f.write(body)


# ------------------------------------------------------------------ check
def check(record: list | None = None) -> int:
    """The card's three Done criteria, re-read from the built artefacts (no writes).

    Also re-derives the whole spec from its inputs (`build_plan()` + `spec_document()`) and diffs
    it against the file on disk, so a stale or hand-edited spec fails here (B-04 polish, review
    issue 2 / R11). `record`, when given, is filled with the result for the receipt.
    """
    tag_dir = os.path.join(ROOT, "Builds", TAG)
    fails: list[str] = []
    if not os.path.exists(SPEC):
        print(f"FAIL: {rel(SPEC)} missing (run --write)")
        return 1
    if not os.path.isdir(tag_dir):
        print(f"FAIL: {rel(tag_dir)} missing (run --write)")
        return 1
    if not os.path.exists(os.path.join(tag_dir, "receipt.json")):
        print(f"FAIL: {rel(tag_dir)}/receipt.json missing (run --write)")
        return 1
    spec = json.load(open(SPEC, encoding="utf-8"))
    receipt = json.load(open(os.path.join(tag_dir, "receipt.json"), encoding="utf-8"))
    ee = os.path.join(tag_dir, EE)
    toc = ee + ".toc"
    aaf = os.path.join(tag_dir, "aaf")
    if not (os.path.exists(ee) and os.path.exists(toc)):
        print("FAIL: the build has no .ee/.toc pair")
        return 1
    # --- the spec must be what its inputs derive, not a value typed at some earlier time
    fresh = spec_document(build_plan(), spec["module"],
                          {"base_module_bytes": spec["module"]["base_bytes"]}, aaf)
    stale = sorted(k for k in fresh if k != "module" and spec.get(k) != fresh[k])
    spec_ok = not stale
    if stale:
        fails.append("the spec is not what build_plan()/spec_document() derive from its inputs "
                     f"(stale or hand-edited key(s): {stale})")
    print(f"0. spec re-derived from its inputs: {'PASS' if spec_ok else 'FAIL'}"
          + ("" if spec_ok else f" (differs in {stale})"))
    if sha256_file(ee) != receipt["ee"]["sha256"]:
        fails.append(".ee sha256 differs from the receipt")
    if sha256_file(toc) != receipt["toc"]["sha256"]:
        fails.append(".toc sha256 differs from the receipt")
    if not receipt.get("checks"):
        fails.append("receipt.checks is empty - the Done results are not recorded in the receipt")

    # --- the module, read through its own .toc record (the way the game reads it)
    recs = {n: (o, s) for n, o, s in read_toc(open(toc, "rb").read())}
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    rec = next((v for n, v in recs.items() if n.endswith(MODULE_NAME)), None)
    if rec is None:
        fails.append(f"no .toc record for {MODULE_NAME}")
        module_blob = b""
    else:
        if rec[0] == 0:
            fails.append(f"{MODULE_NAME}: .toc record is external (offset 0 = the archive copy)")
        if real.get(next(n for n in recs if n.endswith(MODULE_NAME))) != rec:
            fails.append(f"{MODULE_NAME}: .toc record disagrees with the .ee directory")
        module_blob = unaaf(open(ee, "rb").read())[0:]
    print(f"1. .toc record  {MODULE_NAME}: offset={rec[0] if rec else None} size={rec[1] if rec else None} "
          f"({'PASS' if rec and rec[0] else 'FAIL'})")
    if module_blob:
        stream = unaaf(open(ee, "rb").read())
        blob = stream[rec[0]:rec[0] + rec[1]]
        if blob != open(os.path.join(aaf, MODULE), "rb").read():
            fails.append("the .toc-sliced module is not the staged module")
    else:
        blob = b""

    if blob and blob[:4] != b" FDA":
        fails.append(f"the .toc-sliced bytes are not an ADF file (magic {blob[:4]!r})")
        blob = b""
    parts = decode_parts(blob) if blob else []
    rows = rows_of(blob) if blob else {}
    print(f"2. jc3adf re-read {MODULE_NAME}: {len(blob)} B, {len(parts)} parts, {len(rows)} rows")
    names = [p["name"] for p in parts]
    for gone in ("sportsmuscle_door_f_l", "sportsmuscle_door_f_r"):
        if gone in names:
            fails.append(f"{gone} is still in the built module")
    if any(p["parent_part_index"] in (1, 2) for p in parts):
        fails.append("a part still parents to the removed door indices 1/2")
    if [rows.get("door_parts[0].part_index"), rows.get("door_parts[1].part_index")] != [25, None]:
        fails.append(f"door_parts is {[rows.get('door_parts[0].part_index'), rows.get('door_parts[1].part_index')]}, expected [25, None]")

    # every spec row must be exactly what the build holds
    for want in spec["parts"]:
        got = next((p for p in parts if p["part_index"] == want["part_index"]), None)
        if got is None:
            fails.append(f"{want['name']}: part_index {want['part_index']} not in the module")
            continue
        checks = (
            ("name", got["name"], want["name"]),
            ("model", got["model"], want["model"]),
            ("parent_part_index", got["parent_part_index"], want["parent_index"]),
            ("damage_type", got["damage_type"], want["damage_type"]),
            ("behavior", got["behavior"], want["behaviour"]),
            ("has_lights", got["has_lights"], want["has_lights"]),
            ("is_deformable", got["is_deformable"], want["is_deformable"]),
            ("has_world_collision_shape", got["has_world_collision_shape"], 0),
            ("world_collision_body_id", got["world_collision_body_id"], -1),
            ("raycast_body_id", got["raycast_body_id"], -1),
        )
        for what, a, b in checks:
            if a != b:
                fails.append(f"{want['name']}.{what}: build {a!r} vs spec {b!r}")
        for k in range(3):
            if abs(got["parent_space_offset"][12 + k] - want["parent_space_offset"][k]) > 1e-5:
                fails.append(f"{want['name']}.parent_space_offset[{k}]: "
                             f"{got['parent_space_offset'][12 + k]} vs "
                             f"{want['parent_space_offset'][k]}")
    # behaviour arrays
    hinge = [rows.get(f"hinged_parts[{i}].part_index") for i in range(64)
             if f"hinged_parts[{i}].part_index" in rows]
    if hinge != spec["behaviour"]["hinged_parts"]["rows"]:
        fails.append(f"hinged_parts {hinge} vs spec {spec['behaviour']['hinged_parts']['rows']}")
    rot = [rows.get(f"rotating_parts[{i}].part_index") for i in range(64)
           if f"rotating_parts[{i}].part_index" in rows]
    want_rot = [r["part_index"] for r in spec["behaviour"]["rotating_parts"]["rows"]]
    if rot != want_rot:
        fails.append(f"rotating_parts {rot} vs spec {want_rot}")
    for i, want in enumerate(spec["behaviour"]["rotating_parts"]["rows"]):
        for k in range(3):
            got = rows.get(f"rotating_parts[{i}].position[{k}]")
            if got is None or abs(got - want["position"][k]) > 1e-5:
                fails.append(f"rotating_parts[{i}].position[{k}] {got} vs {want['position'][k]}")
            got = rows.get(f"rotating_parts[{i}].rotation_axis[{k}]")
            if got is None or abs(got - want["rotation_axis"][k]) > 1e-5:
                fails.append(f"rotating_parts[{i}].rotation_axis[{k}] {got} "
                             f"vs {want['rotation_axis'][k]}")
    aim = [rows.get(f"aim_part_constraints[{i}].source_part_index") for i in range(8)
           if f"aim_part_constraints[{i}].source_part_index" in rows]
    if aim:
        fails.append(f"aim_part_constraints has {len(aim)} row(s); T-12/G2-13 justify none")

    # --- every part's model resolves to a file in the build (and is packed, and listed)
    missing_models, missing_files, unpacked = [], [], []
    for p in parts:
        lod = p["model"]
        if not lod:
            continue
        path = os.path.join(aaf, lod)
        if not os.path.exists(path):
            missing_models.append((p["name"], lod))
            continue
        for line in open(path, encoding="utf-8").read().splitlines():
            line = line.strip()
            if not line.endswith(".rbm"):
                continue
            if not os.path.exists(os.path.join(aaf, line)):
                missing_files.append((p["name"], line))
            elif line not in real:
                unpacked.append((p["name"], line))
    print(f"3. models resolve {len(parts) - len(missing_models)}/{len(parts)} parts; "
          f"{len(missing_files)} missing .rbm, {len(unpacked)} not packed")
    for row in missing_models[:5]:
        fails.append(f"model missing for {row[0]}: {row[1]}")
    for row in missing_files[:5]:
        fails.append(f"mesh missing for {row[0]}: {row[1]}")
    for row in unpacked[:5]:
        fails.append(f"mesh not packed in the .ee for {row[0]}: {row[1]}")

    # --- nothing else may have moved: every surviving part must read back as it shipped
    base_module = os.path.join(ROOT, "Builds", BASE_TAG, "aaf", MODULE)
    base_parts = decode_parts(open(base_module, "rb").read())
    moved, reparented = [], []
    for old in base_parts:
        if old["name"] in [d["name"] for d in spec["removals"]]:
            continue
        new = next((p for p in parts if p["part_index"] == old["part_index"]), None)
        if new is None:
            fails.append(f"surviving part {old['name']} ({old['part_index']}) vanished")
            continue
        for key, value in old.items():
            if key == "children_part_indices":
                continue
            if key == "parent_part_index" and new[key] != value:
                reparented.append((old["name"], value, new[key]))
                continue
            if new[key] != value:
                moved.append((old["name"], key, value, new[key]))
    for row in moved[:8]:
        fails.append(f"untouched part moved: {row[0]}.{row[1]} {row[2]!r} -> {row[3]!r}")
    print(f"4. surviving parts {len(base_parts) - len(spec['removals'])} re-read identical: "
          f"{len(moved)} field(s) moved, {len(reparented)} re-parented "
          f"({[r[0] for r in reparented]})")
    want_reparent = {r["name"] for r in spec["reparent"]}
    if {r[0] for r in reparented} != want_reparent:
        fails.append(f"re-parented set {sorted(r[0] for r in reparented)} != "
                     f"{sorted(want_reparent)}")

    used, files = used_model_bytes(aaf, parts)
    base_used, base_files = used_model_bytes(os.path.join(ROOT, "Builds", BASE_TAG, "aaf"),
                                             base_parts)
    print(f"5. model bytes (distinct .rbm the module references): {used} B = "
          f"{used / 1024.0:.1f} KB ({files} files); {BASE_TAG} {base_used / 1024.0:.1f} KB "
          f"({base_files} files), delta {(used - base_used) / 1024.0:+.1f} KB")

    # --- R9's status belongs in the check output, not only in the receipt (review issue 3)
    b = receipt.get("budgets") or {}
    print(f"6. R9    model cost {b.get('model_kb')} KB vs cap {b.get('model_cap_kb')} KB, delta "
          f"{b.get('delta_kb')} KB vs {BASE_TAG}, textures +{b.get('textures_added', 0)} - "
          f"OPEN: this is NOT the R9 appearance figure (see receipt.budgets.note)")

    # --- the build's own deform module, which this card does not edit (review issue 1 blindness)
    dp = deform_points(aaf)
    dangling = [d for d in dp if d["from_part_index"] in (1, 2)
                or d["skinned_to_part_index"] in (1, 2)]
    print(f"7. deform module   {len(dp)} point(s) read from the build, {len(dangling)} still "
          f"naming the removed indices 1/2 "
          f"({sorted({str(d['from_part']) for d in dangling})}) - open item: this card edits the "
          f"parts module only")

    # --- the scratch XML pointer must not dangle silently (review issue 9)
    xml = (spec.get("module") or {}).get("xml")
    if xml and os.path.exists(xml):
        xml_ok = sha256_file(xml) == (spec["module"].get("xml_sha256") or "")
        print(f"8. scratch XML     {rel(xml)}: {'PASS' if xml_ok else 'FAIL'} "
              f"({os.path.getsize(xml)} B)")
        if not xml_ok:
            fails.append("the scratch XML differs from the spec's xml_sha256")
    elif xml:
        print(f"8. scratch XML     {rel(xml)}: absent (regenerable by --write; the module sha256 "
              f"is the durable record)")

    for line in fails[:25]:
        print("  FAIL", line)
    summary = (f"{'PASS' if not fails else 'FAIL'}: {rel(tag_dir)} re-read "
               f"({receipt['ee']['sha256'][:16]}…, {len(recs)} .toc records, "
               f"{len(parts)} parts, {len(fails)} problem(s))")
    print(summary)
    if record is not None:
        record.append({"command": "python Tools/scripts/bm_parts.py --check",
                       "exit": 0 if not fails else 1, "pass_line": summary,
                       "spec_rederived": spec_ok, "problems": fails})
    return 0 if not fails else 1


# ------------------------------------------------------- B-04 joints: v2 entry
#
# This copy never edits bm_parts.py and never writes into Builds/bm-RC2. It copies
# bm-RC2's aaf tree into Builds/bm-RC3-parts and rewrites ONLY the `constraint_index`
# member of the P-01/P-02 part records, taking the value from
# Working/Parts/bm_vehicle_parts_v2.json. Every other byte of the module is copied
# unchanged, so every other part row stays byte-identical to bm-RC2.
import math

sys.path.insert(0, HERE)
import jc3adf

JOINT_MODULE = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/"
                "sportsmuscle_vehicle_parts.vmodc")
PHYSICSC_MODULE = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/"
                   "sportsmuscle.physicsc")
BUILD_DIR = os.path.join(ROOT, "Builds", TAG)
BASE_DIR = os.path.join(ROOT, "Builds", BASE_TAG)
RECEIPT = os.path.join(BUILD_DIR, "receipt.json")
JOINT_KEYS = ("constraint_index", "constraint_class", "constraint_axis", "constraint_pivot_m",
              "constraint_min_rad", "constraint_max_rad", "constraint_min_deg",
              "constraint_max_deg", "constraint_frame", "constraint_source")


def load_spec() -> dict:
    with open(SPEC, encoding="utf-8") as f:
        return json.load(f)


def joint_rows(spec: dict) -> list[dict]:
    """Manifest records that ask for a joint (the only rows with `constraint_index`)."""
    return [p for p in spec["parts"] if "constraint_index" in p]


def _find_member(adf, th, name, base, depth=0):
    """Absolute file offset + member record of `name`, searched down the struct tree."""
    t = adf.type(th)
    if not t or depth > 4:
        return None
    for m in t["members"]:
        if m["name"] == name:
            return base + m["offset"], m
        hit = _find_member(adf, m["type"], name, base + m["offset"], depth + 1)
        if hit:
            return hit
    return None


def joint_layout(blob: bytes) -> dict:
    """Where `parts[i].constraint_index` lives: array start, stride, field offset and type."""
    adf = jc3adf.Adf(blob)
    inst = adf.instances[0]
    pos, pm = _find_member(adf, inst["type"], "parts", inst["offset"])
    at = adf.type(pm["type"])
    part = adf.type(at["element"])
    ci = next(m for m in part["members"] if m["name"] == "constraint_index")
    prim = jc3adf.PRIMITIVES[ci["type"]]
    a_off, count = struct.unpack_from("<QQ", blob, pos)
    return {"adf": adf, "count": count, "stride": part["size"], "elems": adf.data_off + a_off,
            "ci_off": ci["offset"], "ci_fmt": prim[1], "ci_size": prim[2],
            "ci_type": prim[0]}


def constraint_at(lay: dict, blob: bytes, i: int) -> int:
    return struct.unpack_from(lay["ci_fmt"], blob,
                              lay["elems"] + i * lay["stride"] + lay["ci_off"])[0]


def part_row(blob: bytes, lay: dict, i: int) -> bytes:
    start = lay["elems"] + i * lay["stride"]
    return blob[start:start + lay["stride"]]


def patch_module(src: bytes, spec: dict):
    """Return (new bytes, layout, evidence). Refuses anything but a -1 -> manifest change."""
    lay = joint_layout(src)
    rows = jc3adf.parts(lay["adf"])
    by_name = {p["name"]: i for i, p in enumerate(rows)}
    out = bytearray(src)
    evidence = []
    for p in joint_rows(spec):
        if p["name"] not in by_name:
            raise SystemExit(f"manifest part {p['name']} is not in the module")
        i = by_name[p["name"]]
        if i != p["part_index"]:
            raise SystemExit(f"{p['name']}: manifest part_index {p['part_index']} != module row {i}")
        old = constraint_at(lay, src, i)
        new = int(p["constraint_index"])
        if old != -1:
            raise SystemExit(f"{p['name']}: module row already carries {old}, not -1")
        pos = lay["elems"] + i * lay["stride"] + lay["ci_off"]
        struct.pack_into(lay["ci_fmt"], out, pos, new)
        evidence.append({"part": p["name"], "part_index": i,
                         "constraint_index_old": old, "constraint_index_new": new,
                         "byte_offset": pos, "field_bytes": lay["ci_size"],
                         "field_type": lay["ci_type"],
                         "constraint_axis": p["constraint_axis"],
                         "constraint_pivot_m": p["constraint_pivot_m"],
                         "constraint_min_deg": p["constraint_min_deg"],
                         "constraint_max_deg": p["constraint_max_deg"],
                         "constraint_min_rad": p["constraint_min_rad"],
                         "constraint_max_rad": p["constraint_max_rad"],
                         "constraint_class": p["constraint_class"],
                         "constraint_frame": p["constraint_frame"]})
    new_blob = bytes(out)
    check = joint_layout(new_blob)
    for ev in evidence:
        got = constraint_at(check, new_blob, ev["part_index"])
        if got != ev["constraint_index_new"]:
            raise SystemExit(f"{ev['part']}: wrote {ev['constraint_index_new']}, read back {got}")
    return new_blob, lay, evidence


def row_diff(base: bytes, built: bytes, lay: dict) -> list[int]:
    return [i for i in range(lay["count"]) if part_row(base, lay, i) != part_row(built, lay, i)]


def physicsc_state() -> dict:
    path = os.path.join(BUILD_DIR, "aaf", *PHYSICSC_MODULE.split("/"))
    if not os.path.exists(path):
        return {"path": PHYSICSC_MODULE, "bytes": None, "sha256": None,
                "changed_by_this_build": False,
                "why": "physicsc not present in the tree"}
    blob = open(path, "rb").read()
    return {"path": PHYSICSC_MODULE, "bytes": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest().upper(),
            "changed_by_this_build": False,
            "constraint_objects": None,
            "why": ("copied unchanged: this generator writes the parts module only. "
                    "JOINT_FIELDS.md §4 counts 11 constraint objects, so 11/12 are the "
                    "append positions and no hinge object exists yet - the index is "
                    "correct only once those two objects are appended.")}


def build() -> int:
    spec = load_spec()
    src_mod = os.path.join(BASE_DIR, "aaf", *JOINT_MODULE.split("/"))
    with open(src_mod, "rb") as f:
        src = f.read()
    if os.path.isdir(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    shutil.copytree(os.path.join(BASE_DIR, "aaf"), os.path.join(BUILD_DIR, "aaf"))
    new, lay, evidence = patch_module(src, spec)
    dst_mod = os.path.join(BUILD_DIR, "aaf", *JOINT_MODULE.split("/"))
    with open(dst_mod, "wb") as f:
        f.write(new)
    changed_rows = row_diff(src, new, lay)
    diffs = [k for k in range(min(len(src), len(new))) if src[k] != new[k]]
    expected = set()
    for ev in evidence:
        expected.update(range(ev["byte_offset"], ev["byte_offset"] + ev["field_bytes"]))
    parts = jc3adf.parts(lay["adf"])
    receipt = {
        "schema": 1, "card": "B-04 + JOINT_FIELDS", "tag": TAG, "base": BASE_TAG,
        "generator": "Tools/scripts/bm_parts_v2.py",
        "spec": "Working/Parts/bm_vehicle_parts_v2.json",
        "scope": ("copy of bm-RC2's parts module with only the P-01/P-02 "
                  "`constraint_index` members rewritten"),
        "module": JOINT_MODULE,
        "module_bytes": len(new),
        "base_sha256": hashlib.sha256(src).hexdigest().upper(),
        "module_sha256": hashlib.sha256(new).hexdigest().upper(),
        "parts": len(parts),
        "joint_rows": evidence,
        "changed_rows": changed_rows,
        "other_rows_byte_identical": len(parts) - len(changed_rows),
        "byte_diffs": len(diffs),
        "diff_offsets": [hex(d) for d in diffs],
        "diff_all_inside_constraint_fields": set(diffs) == expected,
        "physicsc": physicsc_state(),
        "commands": ["python Tools/scripts/bm_parts_v2.py --write",
                     "python Tools/scripts/bm_parts_v2.py --check",
                     "python Tools/scripts/jc3adf.py dump " + JOINT_MODULE + " --paths",
                     "python Tools/scripts/jc3parts.py check"],
    }
    with open(RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {os.path.relpath(dst_mod, ROOT)}: {len(new)} bytes, "
          f"{len(parts)} parts, rows changed {changed_rows}, {len(diffs)} byte(s) differ")
    for ev in evidence:
        print(f"  [{ev['part_index']}] {ev['part']}: constraint_index "
              f"{ev['constraint_index_old']} -> {ev['constraint_index_new']}, "
              f"axis {ev['constraint_axis']}, "
              f"{ev['constraint_min_deg']}..{ev['constraint_max_deg']} deg")
    print(f"wrote {os.path.relpath(RECEIPT, ROOT)}")
    return 0 if changed_rows == [ev["part_index"] for ev in evidence] else 1


def check() -> int:
    spec = load_spec()
    fails = []
    rows = joint_rows(spec)
    if len(rows) != 2:
        fails.append(f"manifest has {len(rows)} joint rows, expected 2 (P-01, P-02)")
    for p in rows:
        missing = [k for k in JOINT_KEYS if k not in p]
        if missing:
            fails.append(f"{p['name']}: missing {missing}")
            continue
        if p["constraint_class"] != "hkpLimitedHingeConstraintData":
            fails.append(f"{p['name']}: class {p['constraint_class']}")
        if p["constraint_frame"] != "vehicle":
            fails.append(f"{p['name']}: frame {p['constraint_frame']}")
        ax = p["constraint_axis"]
        if abs(math.sqrt(sum(a * a for a in ax)) - 1.0) > 1e-6:
            fails.append(f"{p['name']}: axis {ax} is not a unit vector")
        if max(abs(a - b) for a, b in zip(p["constraint_pivot_m"], p["pivot_m"])) > 1e-9:
            fails.append(f"{p['name']}: constraint_pivot_m != pivot_m")
        if not p["constraint_min_rad"] < p["constraint_max_rad"]:
            fails.append(f"{p['name']}: min_rad >= max_rad")
        for rad, deg in ((p["constraint_min_rad"], p["constraint_min_deg"]),
                         (p["constraint_max_rad"], p["constraint_max_deg"])):
            if abs(rad - deg * math.pi / 180.0) > 1e-5:
                fails.append(f"{p['name']}: {rad} rad != {deg} deg")
        if not 0 <= p["constraint_index"]:
            fails.append(f"{p['name']}: constraint_index {p['constraint_index']} is negative")
    base_path = os.path.join(BASE_DIR, "aaf", *JOINT_MODULE.split("/"))
    built_path = os.path.join(BUILD_DIR, "aaf", *JOINT_MODULE.split("/"))
    if not os.path.exists(built_path):
        print(f"missing {os.path.relpath(built_path, ROOT)} (run --write)")
        return 1
    base = open(base_path, "rb").read()
    built = open(built_path, "rb").read()
    lay = joint_layout(built)
    parts = jc3adf.parts(lay["adf"])
    lay_base = joint_layout(base)
    if len(parts) != lay["count"]:
        fails.append(f"decoded {len(parts)} parts, array count {lay['count']}")
    by_name = {p["name"]: i for i, p in enumerate(parts)}
    expected_rows = []
    evidence = []
    for p in rows:
        i = by_name.get(p["name"], p["part_index"])
        if i != p["part_index"]:
            fails.append(f"{p['name']}: manifest index {p['part_index']} vs module row {i}")
        old = constraint_at(lay_base, base, i)
        new = constraint_at(lay, built, i)
        if old != -1:
            fails.append(f"{p['name']}: bm-RC2 row already carries {old}")
        if new != p["constraint_index"]:
            fails.append(f"{p['name']}: built row carries {new}, manifest {p['constraint_index']}")
        expected_rows.append(i)
        evidence.append((i, p, old, new))
    changed = row_diff(base, built, lay)
    if changed != sorted(expected_rows):
        fails.append(f"rows differing from bm-RC2: {changed}, expected {sorted(expected_rows)}")
    diffs = [k for k in range(min(len(base), len(built))) if base[k] != built[k]]
    expected_bytes = set()
    for i in expected_rows:
        pos = lay["elems"] + i * lay["stride"] + lay["ci_off"]
        expected_bytes.update(range(pos, pos + lay["ci_size"]))
    if set(diffs) != expected_bytes:
        fails.append(f"byte diffs {len(diffs)} at {[hex(d) for d in diffs[:8]]}, "
                     f"expected {len(expected_bytes)} inside the two fields")
    if len(base) != len(built):
        fails.append(f"file length changed {len(base)} -> {len(built)}")
    for i, p, old, new in evidence:
        print(f"  [{i}] {p['name']}: constraint_index {old} -> {new} "
              f"({lay['ci_type']} at +0x{lay['elems'] + i * lay['stride'] + lay['ci_off']:x}); "
              f"axis {p['constraint_axis']}, pivot {p['constraint_pivot_m']} m, "
              f"limits {p['constraint_min_deg']}..{p['constraint_max_deg']} deg = "
              f"{p['constraint_min_rad']}..{p['constraint_max_rad']} rad, "
              f"{p['constraint_class']} in {p['constraint_frame']} frame")
    if fails:
        for f in fails:
            print("  ", f)
        print(f"FAIL: {len(fails)} problem(s) in {len(parts)} parts")
        return 1
    print(f"ok: {len(parts)} parts; {len(evidence)} joint rows hold their manifest indices; "
          f"{len(parts) - len(changed)}/{len(parts) - len(changed)} other part rows byte-identical "
          f"to {BASE_TAG}; {len(diffs)} byte(s) changed inside the two constraint_index fields")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="copy Builds/bm-RC2 into Builds/bm-RC3-parts and patch the two joints")
    ap.add_argument("--check", action="store_true",
                    help="no writes: compare the built module with the manifest and bm-RC2")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    return build() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
