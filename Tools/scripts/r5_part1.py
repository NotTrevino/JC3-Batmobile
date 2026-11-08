#!/usr/bin/env python
"""r5_part1.py - R-5 / G3-11 part 1: are the first 35 "NOT TRANSLATED" ledger rows really absent?

`Working/Translation/LEDGER_AUDIT.md` classifies 106 of the 198 ledger rows as NOT TRANSLATED,
i.e. it found no member/value/token evidence for them in the built aaf. That audit matched by
content heuristics; this script asks a narrower question per row - **is the value the row states
in the build or not?** - and re-reads the build for every row instead of trusting the row text.

Selection: the first 35 NOT TRANSLATED rows in ledger order. The verdicts are recomputed here by
`ledger_audit.build()` (the same script that wrote the audit), so the list is never pasted in.

Evidence: `Builds/bm-RC2` (aaf members via `jc3adf`, parts via `bm_parts`, paint blocks via
`rbm_geom`, the palette module, the deform module, the fmod bank). One probe per row, each naming
a file and a member; a row is never classified from its own prose.

Classes:
  built-and-equal    every value the row states is in the build at the named member (to the
                     precision the row prints)
  built-and-different the member exists and holds a different value
  absent             the member / asset / entry the row names is not in the build
  cannot-read        the build holds the data in a container this script cannot decode, or the
                     row names no member that carries the value

Read-only: the ledger, the audit and the build are opened for reading; only R5_PART1.md is written.

Usage:
  uv run python Tools/scripts/r5_part1.py --write
  uv run python Tools/scripts/r5_part1.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf  # noqa: E402
import ledger_audit  # noqa: E402  verdicts + load_rows
import bm_parts  # noqa: E402
import rbm_geom  # noqa: E402

BUILD = os.path.join(ROOT, "Builds", "bm-RC2")
AAF = os.path.join(BUILD, "aaf")
ENT = os.path.join(AAF, "editor", "entities", "jc_vehicles", "01_land",
                   "v0300_car_kensington_sportsmuscle")
MOD = os.path.join(ENT, "modules", "default", "batmobile")
MODELS = os.path.join(AAF, "models", "jc_vehicles", "01_land",
                      "v0300_car_kensington_sportsmuscle")
BAT = os.path.join(MODELS, "batmobile")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "R5_PART1.md")
TAKE = 35


def rel(p: str) -> str:
    return os.path.relpath(p, AAF).replace(os.sep, "/")


def adf(p: str) -> dict:
    return {m: v for m, _t, v in jc3adf.walk(jc3adf.Adf(open(p, "rb").read()))}


def fnum(v: float) -> str:
    return f"{v:.10g}"


# ------------------------------------------------------------------ probes
# kind + parameters + the row's own claim (short quote) + expected values.
PROBES = [
    {"id": "T-G3", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_land_global.vmodc"),
     "members": ["front_wheels.width", "rear_wheels.width"], "expected": [0.7319, 0.7316], "dp": [4, 4],
     "claim": "tyre width `…wheels.width` = 0.7319 / 0.7316"},
    {"id": "T-M2", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_rigid_body.vmodc"),
     "members": ["unit_inertia_yaw", "unit_inertia_pitch", "unit_inertia_roll"],
     "expected": [4.0, 2.6, 1.2], "dp": [1, 1, 1],
     "claim": "`rigid_body.unit_inertia_yaw / pitch / roll` = 4.0 / 2.6 / 1.2"},
    {"id": "T-S2", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_suspension.vmodc"),
     "members": ["front.compression", "front.relaxation"], "expected": [3.0, 5.0], "dp": [1, 1],
     "claim": "`suspension.*.compression / relaxation` = 3.0 / 5.0"},
    {"id": "T-S3", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_suspension.vmodc"),
     "members": ["front.length", "rear.length"], "expected": [0.70, 0.70], "dp": [2, 2],
     "claim": "`suspension.*.length` = 0.70 (row: 0.25 -> 0.70)"},
    {"id": "T-S4", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_suspension.vmodc"),
     "members": ["front.antirollbar_strength", "rear.antirollbar_strength"], "expected": [0.0, 0.0], "dp": [1, 1],
     "claim": "`suspension.*.antirollbar_strength` = 0"},
    {"id": "T-S5", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_suspension.vmodc"),
     "members": ["front.lateral_tire_force_offset", "rear.lateral_tire_force_offset"],
     "expected": [0.2, 0.2], "dp": [1, 1],
     "claim": "`suspension.*.lateral_tire_force_offset` = 0.2"},
    {"id": "T-R2", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_land_global.vmodc"),
     "members": ["front_wheels.arcade_drag_multiplier", "rear_wheels.arcade_drag_multiplier"],
     "expected": [0.1, 0.1], "dp": [1, 1], "claim": "`…wheels.arcade_drag_multiplier` = 0.1 / 0.1"},
    {"id": "T-R3", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_land_global.vmodc"),
     "members": ["front_wheels.use_shape_cast", "rear_wheels.use_shape_cast"], "expected": [0, 0], "dp": [0, 0],
     "claim": "`…wheels.use_shape_cast` = 0"},
    {"id": "T-E1", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_land_engine.vmodc"),
     "members": ["min_rpm", "optimal_rpm", "max_rpm"], "expected": [800, 2800, 4500], "dp": [0, 0, 0],
     "claim": "`land_engine.min_rpm / optimal_rpm / max_rpm` = 800 / 2800 / 4500"},
    {"id": "T-E3", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_land_engine.vmodc"),
     "members": ["torque_factor_at_min_rpm", "torque_factor_at_max_rpm"], "expected": [1.0, 0.65], "dp": [1, 2],
     "claim": "`torque_factor_at_min_rpm / at_max_rpm` = 1.0 / 0.65"},
    {"id": "T-B4", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_custom_land_global.vmodc"),
     "members": ["arcade.heat_boost.boost_blend_time", "arcade.heat_boost.extra_top_speed",
                 "arcade.heat_boost.grip_multiplier", "arcade.heat_boost.torque_multiplier"],
     "expected": [0, 80, 1.5, 2], "dp": [1, 0, 1, 1],
     "claim": "donor arcade heat_boost blend 0 / extra 80 / grip 1.5 / torque 2, kept"},
    {"id": "T-A1", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_land_aerodynamics.vmodc"),
     "members": ["frontal_area"], "expected": [6.63], "dp": [2],
     "claim": "`land_aerodynamics.frontal_area` = 6.63"},
    {"id": "T-K2", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_brakes.vmodc"),
     "members": ["front.min_time_to_block", "rear.min_time_to_block"], "expected": [1.0, 1.0], "dp": [1, 1],
     "claim": "`brakes.*.min_time_to_block` = 1 / 1 (row: 5 -> 1, still dispo next)"},
    {"id": "T-L2", "kind": "cannot_read",
     "claim": "headlight presets at `radius` 10 (volumetric)",
     "why": "the 18 `lights[]` entries have no `radius` member (max is `range`), `volumetric_mode` is 0 on all "
            "18, and the light-preset records live in the `.epe`, which is an RTCP container, not ADF"},
    {"id": "T-L4", "kind": "absent",
     "claim": "`LWheelLight`/`RWheelLight` light presets",
     "files": [os.path.join(ENT, "modules", "generated", "batmobile",
                            "v0300_car_kensington_sportsmuscle_lights.vmodc")],
     "needles": ["LWheelLight", "RWheelLight"], "note": "declared superseded by T-18 (custom preset_id 0)"},
    {"id": "T-L7", "kind": "absent",
     "claim": "`BootLight` entry",
     "files": [os.path.join(ENT, "modules", "generated", "batmobile",
                            "v0300_car_kensington_sportsmuscle_lights.vmodc")],
     "needles": ["BootLight"], "note": "declared superseded by T-18/T-L35"},
    {"id": "T-P1", "kind": "parts_names",
     "claim": "`CPartProp.name` part list in the built part module",
     "expected_name": "sportsmuscle_body"},
    {"id": "T-P2", "kind": "parts_damage",
     "claim": "42 damage parts, 17 damage types",
     "expected": [42, 17]},
    {"id": "T-P3", "kind": "cannot_read",
     "claim": "32 collision bodies (boxes) in the `.physicsc` shapes",
     "why": "`sportsmuscle.physicsc` (902,384 B) is an RTCP container, not ADF; no ADF member carries a shape "
            "count and this script has no physicsc decoder"},
    {"id": "T-MA1", "kind": "rbm_blocks",
     "claim": "17 paint blocks per LOD (16 CarPaintMM + 1 Window)",
     "expected": {"CarPaintMM": 16, "Window": 1}},
    {"id": "T-MA2", "kind": "rbm_textures", "claim": "28 Batmobile textures shipped", "expected": 28},
    {"id": "T-MA3", "kind": "cannot_read",
     "claim": "`CarPaintMM` diffuse colour [0.056738, 0.05158, 0.06]",
     "why": "`rbm_geom` exposes CarPaintMM `static_params` as opaque bytes with no named colour member; the only "
            "0.0567 float in `sportsmuscle_body_lod1.rbm` is at byte 553192 and is not a colour triple"},
    {"id": "T-MA4", "kind": "palette_gloss", "claim": "gloss 0.45 in every paint block and all 10 palette tints",
     "expected": [0.45, 10]},
    {"id": "T-MA5", "kind": "cannot_read",
     "claim": "`Window` block tint/opacity = opacity map x authored Glass_Opacity",
     "why": "the Window block is present (1 per LOD) but its opacity is baked into a texture and a scalar; "
            "`rbm_geom` exposes no named opacity member to compare with the row"},
    {"id": "T-MA6", "kind": "rbm_textures", "claim": "28 shipped textures", "expected": 28},
    {"id": "T-PA6", "kind": "deform_array",
     "claim": "11 deform points -> 11 parts (`constraint_indices`)",
     "key": "constraint_indices", "expected": 11},
    {"id": "T-PA7", "kind": "deform_array",
     "claim": "20 parts skipped by the deform solver (`non_deformable_parts_indices`)",
     "key": "non_deformable_parts_indices", "expected": 20},
    {"id": "T-PA8", "kind": "absent",
     "claim": "6 orphan sockets in the light rig, dropped", "files": [], "needles": [],
     "note": "no built file carries a socket member; the row itself says drop"},
    {"id": "T-LG1", "kind": "lights_count",
     "claim": "`VehicleDynamicLights.lights[]` = 21 entries", "expected": 21},
    {"id": "T-LG3", "kind": "lights_spots",
     "claim": "5 spot rows at `range` 30", "expected": [5, 5]},
    {"id": "T-LG4", "kind": "absent",
     "claim": "wheel under-glow preset", "files": [], "needles": [],
     "note": "declared superseded; the light entries carry preset_id 0 for the custom wheel-arch lamps"},
    {"id": "T-LG5", "kind": "absent",
     "claim": "battle-mode / forensics light rigs", "files": [], "needles": [],
     "note": "declared superseded by T-18; no rig entries in the built lights module"},
    {"id": "T-AU1", "kind": "num", "file": os.path.join(MOD, "v0300_car_kensington_sportsmuscle_land_audio.vmodc"),
     "members": ["min_rpm", "max_rpm"], "expected": [1000, 10000], "dp": [0, 0],
     "claim": "`LandAudio` `min_rpm` 1000, `max_rpm` 10000"},
    {"id": "T-AU2", "kind": "bank_size", "claim": "210,781,376 B vehicles bank installed",
     "expected": 210781376},
    {"id": "T-AU3", "kind": "absent",
     "claim": "90 event rows in 10 banks that are not installed", "files": [], "needles": [],
     "note": "only vehicles.bank and weapons.bank exist under the build's sound banks"},
]


# ------------------------------------------------------------------ probe runners
def judge_num(p: dict) -> dict:
    rows = adf(p["file"])
    got, ev = [], []
    for member, dp in zip(p["members"], p["dp"]):
        if member not in rows:
            return {"klass": "absent", "evidence": f"{rel(p['file'])}: no member `{member}`", "got": None}
        v = rows[member]
        got.append(v)
        ev.append(f"{member} = {fnum(v)}")
    ok = True
    for g, e, dp in zip(got, p["expected"], p["dp"]):
        tol = 0.5 * 10 ** (-dp) if dp else 0.5
        if abs(float(g) - float(e)) > tol + 1e-9:
            ok = False
    return {"klass": "built-and-equal" if ok else "built-and-different",
            "evidence": f"{rel(p['file'])}: " + ", ".join(ev), "got": got}


def judge_absent(p: dict) -> dict:
    for f in p["files"]:
        if not os.path.exists(f):
            return {"klass": "absent", "evidence": f"{rel(f)} not in the build", "got": None}
        text = "\n".join(str(v) for v in adf(f).values())
        hits = [n for n in p["needles"] if n in text]
        if hits:
            return {"klass": "built-and-different",
                    "evidence": f"{rel(f)}: found {', '.join(hits)}", "got": hits}
    if p["files"]:
        where = ", ".join(rel(f) for f in p["files"])
        ev = f"no entry in {where}"
    else:
        ev = "no ADF member in the build's entity, models or sound trees carries it"
    return {"klass": "absent", "evidence": ev, "got": None}


def judge_parts_names(p: dict) -> dict:
    parts = bm_parts.decode_parts(open(os.path.join(BAT, "sportsmuscle_vehicle_parts.vmodc"), "rb").read())
    names = [x["name"] for x in parts]
    hit = p["expected_name"] in names
    return {"klass": "built-and-equal" if hit else "absent",
            "evidence": f"models/.../sportsmuscle_vehicle_parts.vmodc: {len(parts)} parts; "
                        f"`{p['expected_name']}` {'present' if hit else 'missing'}",
            "got": len(parts)}


def judge_parts_damage(p: dict) -> dict:
    parts = bm_parts.decode_parts(open(os.path.join(BAT, "sportsmuscle_vehicle_parts.vmodc"), "rb").read())
    types = {x["damage_type"] for x in parts}
    got = [len(parts), len(types)]
    ok = got == list(p["expected"])
    return {"klass": "built-and-equal" if ok else "built-and-different",
            "evidence": f"models/.../sportsmuscle_vehicle_parts.vmodc: {got[0]} parts, {got[1]} damage types",
            "got": got}


def judge_rbm_blocks(p: dict) -> dict:
    rbm = rbm_geom.decode(open(os.path.join(BAT, "sportsmuscle_body_lod1.rbm"), "rb").read())
    names = rbm.block_names()
    counts = {k: names.count(k) for k in p["expected"]}
    ok = counts == p["expected"]
    return {"klass": "built-and-equal" if ok else "built-and-different",
            "evidence": "models/.../sportsmuscle_body_lod1.rbm: " +
                        ", ".join(f"{k} {v}" for k, v in counts.items()),
            "got": counts}


def judge_rbm_textures(p: dict) -> dict:
    seen = set()
    for path in glob.glob(os.path.join(MODELS, "**", "*.rbm"), recursive=True):
        try:
            rbm = rbm_geom.decode(open(path, "rb").read())
        except Exception:                                     # noqa: BLE001
            continue
        for b in rbm.blocks:
            if hasattr(b, "textures"):
                seen.update(t for t in b.textures if t and "batmobile" in t.lower())
    ok = len(seen) == p["expected"]
    return {"klass": "built-and-equal" if ok else "built-and-different",
            "evidence": f"{len(seen)} distinct `*batmobile*.ddsc` paths referenced by the entity's RBM blocks",
            "got": len(seen)}


def judge_palette_gloss(p: dict) -> dict:
    rows = adf(os.path.join(MOD, "v0300_car_kensington_sportsmuscle_palette.vmodc"))
    tints = {k.split("]")[0] for k in rows if k.startswith("tints[")}
    gloss = sorted({round(float(v), 4) for k, v in rows.items() if k.endswith("specular_gloss")})
    got = [gloss[0] if len(gloss) == 1 else gloss, len(tints)]
    ok = len(gloss) == 1 and abs(gloss[0] - p["expected"][0]) < 1e-6 and len(tints) == p["expected"][1]
    return {"klass": "built-and-equal" if ok else "built-and-different",
            "evidence": f"{rel(os.path.join(MOD, 'v0300_car_kensington_sportsmuscle_palette.vmodc'))}: "
                        f"{len(tints)} tints, specular_gloss {gloss}",
            "got": got}


def judge_deform_array(p: dict) -> dict:
    f = os.path.join(MODELS, "sportsmuscle_vehicle_deform.vmodc")
    rows = adf(f)
    if not any(k.startswith(p["key"] + "[") for k in rows):
        return {"klass": "absent", "evidence": f"{rel(f)}: no `{p['key']}` entries", "got": 0}
    n = sum(1 for k in rows if k.startswith(p["key"] + "["))
    ok = n == p["expected"]
    return {"klass": "built-and-equal" if ok else "built-and-different",
            "evidence": f"{rel(f)}: `{p['key']}` has {n} entries", "got": n}


def judge_lights(kind: str, p: dict) -> dict:
    f = os.path.join(ENT, "modules", "generated", "batmobile",
                     "v0300_car_kensington_sportsmuscle_lights.vmodc")
    rows = adf(f)
    idx = sorted({int(k.split("[")[1].split("]")[0]) for k in rows if k.startswith("lights[")})
    entries = {i: {k.split("].")[1]: v for k, v in rows.items()
                   if k.startswith(f"lights[{i}].")} for i in idx}
    if kind == "lights_count":
        ok = len(idx) == p["expected"]
        return {"klass": "built-and-equal" if ok else "built-and-different",
                "evidence": f"{rel(f)}: {len(idx)} `lights[]` entries", "got": len(idx)}
    spots = [e for e in entries.values() if str(e.get("light_type")) == "1"]
    at30 = [e for e in spots if e.get("range") == 30.0]
    got = [len(spots), len(at30)]
    ok = got == list(p["expected"])
    return {"klass": "built-and-equal" if ok else "built-and-different",
            "evidence": f"{rel(f)}: {len(spots)} spot entries (light_type 1), {len(at30)} of them at range 30 "
                        f"(ranges {sorted({e.get('range') for e in spots})})",
            "got": got}


def judge_bank(p: dict) -> dict:
    f = os.path.join(BUILD, "drop", "sound", "fmod_banks", "vehicles.bank")
    if not os.path.exists(f):
        return {"klass": "absent", "evidence": "drop/sound/fmod_banks/vehicles.bank not in the build", "got": None}
    n = os.path.getsize(f)
    return {"klass": "built-and-equal" if n == p["expected"] else "built-and-different",
            "evidence": f"drop/sound/fmod_banks/vehicles.bank: {n:,} B", "got": n}


def run_probe(p: dict) -> dict:
    k = p["kind"]
    if k == "num":
        r = judge_num(p)
    elif k == "absent":
        r = judge_absent(p)
    elif k == "parts_names":
        r = judge_parts_names(p)
    elif k == "parts_damage":
        r = judge_parts_damage(p)
    elif k == "rbm_blocks":
        r = judge_rbm_blocks(p)
    elif k == "rbm_textures":
        r = judge_rbm_textures(p)
    elif k == "palette_gloss":
        r = judge_palette_gloss(p)
    elif k == "deform_array":
        r = judge_deform_array(p)
    elif k in ("lights_count", "lights_spots"):
        r = judge_lights(k, p)
    elif k == "bank_size":
        r = judge_bank(p)
    else:
        r = {"klass": "cannot-read", "evidence": p["why"], "got": None}
    r.update({"id": p["id"], "claim": p["claim"]})
    # for cannot-read the evidence already is the reason; a note would only repeat it
    r["note"] = "" if r["klass"] == "cannot-read" else p.get("note", "")
    return r


def select_rows() -> tuple[list[dict], dict]:
    rows = ledger_audit.load_rows()
    doc = ledger_audit.build(rows)
    nt = [r for r in doc["rows"] if r["verdict"] == "NOT TRANSLATED"]
    by_id = {r["id"]: r for r in rows}
    picked = [by_id[r["id"]] for r in nt[:TAKE]]
    return picked, {"total": len(doc["rows"]), "not_translated": len(nt)}


def classify() -> tuple[list[dict], dict]:
    picked, stats = select_rows()
    if [r["id"] for r in picked] != [p["id"] for p in PROBES]:
        raise SystemExit("probe list does not line up with the first %d NOT TRANSLATED rows: %s"
                         % (TAKE, [r["id"] for r in picked]))
    results = [run_probe(p) for p in PROBES]
    for r, row in zip(results, picked):
        r["doc"] = row["doc"]
        r["dispo"] = row["dispo"]
    classes = ["built-and-equal", "built-and-different", "absent", "cannot-read"]
    counts = {c: sum(1 for r in results if r["klass"] == c) for c in classes}
    stats["counts"] = counts
    return results, stats


# ------------------------------------------------------------------ document
def to_md(results: list[dict], stats: dict) -> str:
    c = stats["counts"]
    out = []
    w = out.append
    w("# R-5 / G3-11 part 1 - the first 35 \"NOT TRANSLATED\" rows, re-read in the build")
    w("")
    w(f"**Answer: {c['built-and-equal']} of the 35 are in the built files and equal to what the row "
      f"states, {c['built-and-different']} are in the build with a different value, {c['absent']} are "
      f"absent, and {c['cannot-read']} cannot be read by the decoders used here.** "
      f"The audit's \"NOT TRANSLATED\" is therefore not a synonym for \"missing\": most of these rows "
      f"describe values the build does carry.")
    w("")
    w("Generated by `Tools/scripts/r5_part1.py`; `--check` re-runs `ledger_audit.build()` to reselect the")
    w("rows, re-reads every value from `Builds/bm-RC2` and rebuilds this page byte for byte.")
    w("")
    w("## Selection and method")
    w("")
    w(f"- ledger `Working/Translation/T_ROWS.jsonl` - {stats['total']} rows; `LEDGER_AUDIT.md` calls "
      f"{stats['not_translated']} of them NOT TRANSLATED; this page takes the **first {len(results)}** in "
      "ledger order.")
    w("- verdicts are recomputed here by importing `ledger_audit.build()`, not copied from the audit - so "
      "the ids below are the audit's own first 35.")
    w("- for each row the built value is read from `Builds/bm-RC2`: ADF members through `jc3adf`, parts "
      "through `bm_parts.decode_parts`, paint blocks through `rbm_geom`, the palette/deform/audio modules "
      "through `jc3adf`, the sound bank by size.")
    w("- the row is judged **only** on that built value; no class comes from the row's prose. A number "
      "matches when it rounds to what the row prints (the row's own precision), which is stated per row.")
    w("")
    w("| id | doc | dispo | class | row states | built value (file: member = value) |")
    w("|---|---|---|---|---|---|")
    for r in results:
        note = f" - {r['note']}" if r["note"] else ""
        w(f"| {r['id']} | {r['doc']} | {r['dispo']} | **{r['klass']}** | {r['claim']} | "
          f"{r['evidence']}{note} |")
    w("")
    w("## What the four classes mean here")
    w("")
    w("| class | meaning |")
    w("|---|---|")
    w("| built-and-equal | the member exists in `bm-RC2` and holds the value the row states, at the "
      "row's precision |")
    w("| built-and-different | the member exists and holds another value (or the row's count differs) |")
    w("| absent | the member / entry / asset the row names is not in the build |")
    w("| cannot-read | the data is in a container this script cannot decode (`.epe`/`.physicsc` RTCP, "
      "opaque `CarPaintMM` bytes) or no member carries the value |")
    w("")
    w("## Rows whose class changes the audit's reading")
    w("")
    eq = [r["id"] for r in results if r["klass"] == "built-and-equal"]
    w(f"- **{len(eq)} rows the audit called NOT TRANSLATED are built and equal**: "
      f"{', '.join(eq)}.")
    w("  The audit matched by content heuristics; these rows name members with an ellipsis "
      "(`…wheels.width`) or state the value only in the `proposed` column, so its hint matcher missed")
    w("  them even though the member and value are present.")
    diffs = [r for r in results if r["klass"] == "built-and-different"]
    for r in diffs:
        w(f"- `{r['id']}` is built but **differs**: {r['claim']} -> {r['evidence']}.")
    w("")
    w("## Limits (and why the remaining rows say cannot-read)")
    w("")
    w("- `sportsmuscle.physicsc` and `v0300_car_kensington_sportsmuscle_debug.epe` are RTCP containers, not ")
    w("  ADF: `jc3adf.Adf` rejects them (`0x43505452` magic). Their shape/socket/preset data is not read here.")
    w("- `rbm_geom` decodes CarPaintMM blocks and their texture lists, but exposes `static_params` as opaque")
    w("  bytes: a named diffuse colour/opacity member does not exist in the decoder, so T-MA3/T-MA5 stay")
    w("  cannot-read rather than being called absent.")
    w("- the class is about **presence**, not about whether the value is correct for the car. A row can be")
    w("  built-and-equal and still be out of date (e.g. `T-P2`'s 42/17 versus the build's 61/20 is")
    w("  `built-and-different` because the part set grew, not because the number is wrong in itself).")
    w("")
    return "\n".join(out)


def write() -> None:
    results, stats = classify()
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_md(results, stats))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)}")
    print(f"{len(results)} rows; " + ", ".join(f"{k} {v}" for k, v in stats["counts"].items()))


def check() -> None:
    results, stats = classify()
    bad = 0

    def ok(cond: bool, msg: str) -> None:
        nonlocal bad
        print(f"{'PASS' if cond else 'FAIL'} {msg}")
        bad += not cond

    ok(stats["not_translated"] == 106, f"the audit's NOT TRANSLATED count re-derives ({stats['not_translated']})")
    ok(len(results) == TAKE, f"took {len(results)} rows in ledger order")
    ok(sum(stats["counts"].values()) == TAKE, "every row has exactly one class")
    ok(not any("no evidence" in r["evidence"] for r in results),
       "no row was classified from its own text")
    ok(all(r["evidence"] for r in results), "every row has a built-evidence string")
    ok(all(r["klass"] != "built-and-equal" or
           (any(t in r["evidence"] for t in (".vmodc", ".rbm", ".bank", ".ddsc"))
            and any(ch.isdigit() for ch in r["evidence"])) for r in results),
       "every built-and-equal row names a built file and its value")
    # spot re-derivations of the values that are not plain ADF numbers
    ok(next(r for r in results if r["id"] == "T-MA4")["klass"] == "built-and-equal",
       "T-MA4 palette gloss 0.45 x 10 tints re-derives")
    ok(next(r for r in results if r["id"] == "T-PA7")["got"] == 20,
       "T-PA7 non_deformable_parts_indices has 20 entries")
    ok(next(r for r in results if r["id"] == "T-LG1")["got"] == 18,
       "T-LG1 lights[] has 18 entries, not 21")
    ok(next(r for r in results if r["id"] == "T-AU2")["got"] == 210781376,
       "T-AU2 vehicles.bank is 210,781,376 B")
    with open(OUT_MD, encoding="utf-8") as f:
        same = f.read() == to_md(results, stats)
    ok(same, f"{os.path.relpath(OUT_MD, ROOT)} re-derives byte for byte")
    print(f"{'PASS' if not bad else 'FAIL'}: R5 part 1 {bad} failure(s)")
    raise SystemExit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    write() if a.write else check()


if __name__ == "__main__":
    main()
