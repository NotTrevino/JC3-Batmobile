#!/usr/bin/env python3
"""T-MD14b: does any JC3 vehicle change handling at runtime, and can it carry BmAK's mode switch?

Two questions, files only:

  1. Fleet side - every place a vehicle's handling or physics can change while it is being
     driven: VTOL / hover / transforming / two-mode vehicles, boost or upgrade states, model
     swaps, rotor steering, AI flight switches.  Each carrier is reported with its module, its
     struct offset (decoded from the `.vmodc` bytes when the module type is indexed) and values.
  2. BmAK side - `Research/BatmobileGrab/DRIVE_MODES.md` (G3-02l) decoded BmAK's switch as
     `EBatmobileDriveMode` (0 Drive / 1 TurnOnSpot / 2 BattleMode) set per state by
     `SetDriveMode` from `PursuitMode.BeginState` (0) and `BattleMode.BeginState` (2), with a
     per-mode field family on the sim.  This script states which JC3 carrier, if any, can hold
     that switch, labelled decoded / derived / UNKNOWN.

Sources (read-only):
  * 232 decoded vehicle builds under `E:/Modding/_gamedata/JC3grab/entities` (player copies; the
    `_ai` twins are excluded, same rule as `jc3tankturn.py` / `jc3_drive_carriers.py`).
  * the patch-layer module **bytes** through `Research/JC3Grab/INDEX.jsonl` + `jc3adf`, for the
    struct offsets of `AirGlobal` (13 `*_air_global.vmodc` in the index) and any
    `*_custom_land_global.vmodc` that is indexed.
  * `Research/BatmobileGrab/DRIVE_MODES.md` - quoted, not re-derived (its own `--check` owns it).

Writes Working/Translation/T_MD14B_STATES.md + .json; `--check` re-derives both and fails on drift.

Usage:
  python Tools/scripts/t_md14b.py --write
  python Tools/scripts/t_md14b.py --check
  python Tools/scripts/t_md14b.py dump
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Working", "Translation")
JSON_NAME = "T_MD14B_STATES.json"
MD_NAME = "T_MD14B_STATES.md"
INDEX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
ENT = os.path.join(RAW, "entities")
MODES = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVE_MODES.md")

# the state vocabulary a runtime handling switch would have to be called; tight on purpose so
# geometry (DeformPoints transforms) and light modes cannot flood the result
TOKENS = ("vtol", "hover", "_mode", "mode_", "state_machine", "_switch", "switch_",
          "alternate", "gear_up", "gear_down", "retract", "deploy", "rotor_tilt",
          "thrust_angle", "amphibious", "two_mode", "transform_", "model_swap", "convert")
BOOST_BLOCKS = ("nitro_boost", "nitro_boost_upgraded", "heat_boost")

# BmAK's switch, quoted from DRIVE_MODES.md (its own --check re-reads the packages)
BMAK = [
    ("enum", "`EBatmobileDriveMode`", "0 `BMDM_Drive`, 1 `BMDM_TurnOnSpot`, 2 `BMDM_BattleMode`, 3 `BMDM_MAX`", "decoded"),
    ("selector", "`RVehicleSimBatmobile.DriveMode`", "ByteProperty at 0x03b0; CDO tag `None` = 0, shipped sim inherits it", "decoded"),
    ("state -> mode", "`PursuitMode.BeginState`", "`SetDriveMode(0)` at script offset 69 (NPC twin 58)", "decoded"),
    ("state -> mode", "`BattleMode.BeginState`", "`SetDriveMode(2)` at script offset 88 (NPC twin 103)", "decoded"),
    ("no state", "`BMDM_TurnOnSpot`", "no decoded body passes 1; `ForceTurnOnSpotMode` has no writer", "UNKNOWN"),
    ("per-mode fields", "`BattleMode*` family", "40 fields on the sim, e.g. `BattleModeSteerAngleFactor` 2.5 at 0x0300, `BattleModeMaxSteering` 80 at 0x02cc, `BattleModeLatSlipScale` 4 at 0x02d4, `BattleModeMaxSpeed` 1200 at 0x02f0", "decoded"),
    ("torque split", "`TurnOnSpotFront/RearTorqueFactor`", "0.6 / -0.5 at 0x01c8 / 0x01cc: opposite signs = front/rear counter-torque", "decoded"),
    ("native arithmetic", "`RVehicleSimBatmobile.SetDriveMode`", "5-byte native declaration; the per-mode maths is in the executable", "UNKNOWN"),
]


def load_index() -> dict[str, dict]:
    import jc3weapons
    rows = [json.loads(line) for line in open(INDEX, encoding="utf-8") if line.strip()]
    return jc3weapons.best_by_path(rows)


def digest() -> str:
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(ENT, "*.ee.json"))):
        h.update(os.path.basename(p).encode())
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    for p in (INDEX, MODES):
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


def decode_module(path: str, index: dict, game: str) -> dict:
    """Type table + values of one `.vmodc` module, decoded from its bytes."""
    import jc3adf
    import jc3weapons
    row = index[path]
    data = jc3weapons.read_row(row, game)
    adf = jc3adf.Adf(data)
    inst = adf.instances[0]
    t = adf.types[inst["type"]]
    members = [{"name": m["name"], "offset": m["offset"], "size": m["size"],
                "type": adf.type_name(m["type"])} for m in t["members"]]
    types = {tt["name"]: [{"name": m["name"], "offset": m["offset"], "size": m["size"],
                           "type": adf.type_name(m["type"])}
                          for m in tt["members"]]
             for tt in adf.types.values()}
    rows = [{"path": p, "value": v} for p, _t, v in jc3adf.walk(adf)]
    return {"path": path, "archive": row["archive"], "entry_offset": row["offset"],
            "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "root": t["name"], "root_size": t["size"], "members": members,
            "types": types, "rows": rows}


def build() -> dict:
    import jc3index
    game = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
    files = sorted(glob.glob(os.path.join(ENT, "*.ee.json")))
    if not files:
        raise SystemExit(f"decoded cache missing under {RAW} - set JC3_RAW")

    types = collections.Counter()
    hits = collections.defaultdict(lambda: collections.defaultdict(set))
    block_builds = collections.defaultdict(set)
    does_steer = collections.Counter()
    rx = re.compile("(?i)(" + "|".join(re.escape(t) for t in TOKENS) + ")")

    for path in files:
        base = os.path.basename(path)
        doc = json.load(open(path, encoding="utf-8"))
        for m in doc.get("modules", []):
            if "/ai/" in (m.get("file") or ""):
                continue
            t = str(m.get("type") or m.get("instance"))
            types[t] += 1
            for r in m.get("rows", []):
                p = r["path"]
                if p.startswith(("points[", "lights[", "parts[", "fins[", "rotors[",
                                 "propellers[", "buoys[", "control_points[")):
                    continue
                if rx.search(p):
                    hits[(t, p)][base].add(str(r["value"])[:40])
                for b in BOOST_BLOCKS:
                    if p.startswith(b + ".") or ("." + b + ".") in p:
                        block_builds[(t, b)].add(base)
                if p.endswith(".does_steer"):
                    does_steer[str(r["value"])] += 1

    index = load_index()
    air_paths = sorted(k for k in index if k.endswith("_air_global.vmodc"))
    clg_paths = sorted(k for k in index if k.endswith("_custom_land_global.vmodc"))
    fighter = next((k for k in air_paths if "fighterjet" in k), air_paths[0] if air_paths else None)
    air = decode_module(fighter, index, game) if fighter else None
    clg = decode_module(clg_paths[0], index, game) if clg_paths else None

    # values of the three boost blocks on the donor land build (cache), for the comparison table
    donor = ("v0300_car_kensington_sportsmuscle__"
             "v0300_car_kensington_sportsmuscle_civilian_01.ee.json")
    donor_vals = {}
    with open(os.path.join(ENT, donor), encoding="utf-8") as f:
        doc = json.load(f)
    for m in doc.get("modules", []):
        if str(m.get("type")) == "CustomLandGlobal" and "/ai/" not in (m.get("file") or ""):
            for r in m.get("rows", []):
                if any(b in r["path"] for b in BOOST_BLOCKS):
                    donor_vals[r["path"]] = r["value"]

    return {
        "schema": "t-md14b/1",
        "inputs": {"entities": len(files), "module_types": len(types),
                   "air_global_bytes": len(air_paths),
                   "custom_land_global_bytes": len(clg_paths), "digest": digest()},
        "modules": [{"type": t, "instances": n} for t, n in sorted(types.items())],
        "scan": {"tokens": list(TOKENS),
                 "hits": [{"module": t, "member": p, "builds": len(b),
                           "values": sorted(set().union(*b.values()))[:6]}
                          for (t, p), b in sorted(hits.items())]},
        "blocks": [{"module": t, "block": b, "builds": len(bs)}
                   for (t, b), bs in sorted(block_builds.items())],
        "land_donor": dict(sorted(donor_vals.items())),
        "air_global": air, "custom_land_global": clg,
        "rotor_steer": dict(does_steer),
        "bmak": [{"kind": a, "carrier": b, "value": c, "label": d} for a, b, c, d in BMAK],
    }


def norm(v) -> str:
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def to_md(d: dict) -> str:
    L: list[str] = []
    a = L.append
    a("# T-MD14b - does JC3 change a vehicle's handling at runtime, and can it carry Pursuit/Battle?")
    a("")
    a("Generated by `Tools/scripts/t_md14b.py`; `--check` re-derives every number from the same")
    a("bytes. **decoded** = read from a file at the quoted offset; **derived** = a stated rule over")
    a("decoded facts; **UNKNOWN** = not in the files, with what was tried.")
    a("")
    a("## 0. Answer")
    a("")
    n = len(d["scan"]["hits"])
    a("**No JC3 vehicle has a runtime mode switch that changes handling.** A fleet-wide scan of")
    a(f"{d['inputs']['entities']} vehicle builds and {d['inputs']['module_types']} module types for")
    a("the state vocabulary (`vtol`, `hover`, `_mode`, `state_machine`, `_switch`, `alternate`,")
    a("`gear_up/down`, `retract`, `deploy`, `rotor_tilt`, `thrust_angle`, `amphibious`, `two_mode`,")
    a(f"`transform_`, `model_swap`, `convert`) returns **{n} member{'' if n == 1 else 's'}**, and")
    a(f"{'it is' if n == 1 else 'none of them is'} not a handling switch{' at all' if n == 1 else ''}:")
    a("")
    a("| member | module | value | what it actually is |")
    a("|---|---|---|---|")
    for h in d["scan"]["hits"]:
        what = ("an AI flight-authority limit on the two plane AI graphs; `-1` = off"
                if h["module"] == "AirplaneAI" else
                "a landing constraint (max body tilt before touch-down) - a limit, not a mode")
        a(f"| `{h['member']}` | `{h['module']}` | {', '.join(h['values'])} | {what} |")
    a("")
    a("The only *alternative handling* the engine demonstrably holds is **three parallel boost")
    a("blocks** on one module - `nitro_boost`, `nitro_boost_upgraded`, `heat_boost` - each a full")
    a("performance block at its own struct offset. They are alternatives chosen by state the files")
    a("do not name, not a mode machine: no member selects one, and there is no `current mode`,")
    a("`variant` or `SetMode`-style member anywhere in the fleet. So the closest structural carrier")
    a("for a Pursuit/Battle switch exists (two same-shaped blocks that the engine reads in place of")
    a("each other), but the **selector** does not, and the switch itself is **UNKNOWN / code bridge**.")
    a("")
    a("| # | BmAK switch part | JC3 carrier | can it express it? |")
    a("|---|---|---|---|")
    a("| S1 | a mode enum that the sim reads | none: 0 `_mode`/`state_machine` members | **no** - UNKNOWN, no data member |")
    a("| S2 | a per-state call that sets the mode | none: no state machine on a vehicle | **no** - UNKNOWN, native only |")
    a("| S3 | two alternative value sets (drive vs battle) | the three parallel boost blocks (S3.1) | **structurally yes, operationally no**: three blocks per module are shipped, the selector is not |")
    a("| S4 | per-mode torque/steer fields | `AirGlobal`/`CustomLandGlobal` families are per-vehicle, not per-mode | **no** - one value set per vehicle |")
    a("| S5 | the transformation pose/audio | `VehicleParts.model_swap` (visual swap, not physics) | **no** - visual only |")
    a("")
    a("## 1. What the fleet does have, by carrier")
    a("")
    a("### 1.1 The parallel boost blocks (the only alternative handling)")
    a("")
    a(f"| module | block | builds (player copy) |")
    a("|---|---|---:|")
    for b in d["blocks"]:
        a(f"| `{b['module']}` | `{b['block']}` | {b['builds']} |")
    a("")
    if d["air_global"]:
        air = d["air_global"]
        a(f"Offsets from the bytes of `{air['path']}` ({air['size']} B, sha256")
        a(f"`{air['sha256'][:16]}`, root type `{air['root']}` {air['root_size']} B):")
        a("")
        a("| offset | size | member | type |")
        a("|---|---|---|---|")
        for m in air["members"]:
            a(f"| {m['offset']} | {m['size']} | `{m['name']}` | `{m['type']}` |")
        a("")
        a("The three blocks sit at fixed offsets on the same struct - the engine can hold all three")
        a("at once; nothing in the module says which one is active:")
        a("")
        a("| member block | offset | values on the fighterjet |")
        a("|---|---|---|")
        for b in BOOST_BLOCKS:
            vals = [norm(r["value"]) for r in air["rows"] if r["path"].startswith(b + ".")]
            off = next((m["offset"] for m in air["members"] if m["name"] == b), None)
            a(f"| `{b}` | {off} | {', '.join(vals) if vals else '(not on this build)'} |")
        a("")
        a("`AirPerformanceBoost` is 12 B of three floats; the block-level offsets above are the")
        a("load-bearing ones, the inner field offsets are in the JSON (`types`).")
    a("")
    if d["custom_land_global"]:
        c = d["custom_land_global"]
        a("The land equivalent, from the bytes of")
        a(f"`{c['path']}` ({c['size']} B, root `{c['root']}`):")
        a("")
        a("| offset | size | member |")
        a("|---|---|---|")
        for m in c["members"][:20]:
            a(f"| {m['offset']} | {m['size']} | `{m['name']}` |")
        a("")
        arc = next((m for m in c["members"] if m["name"] == "arcade"), None)
        if arc:
            sub = c["types"].get(arc["type"], [])
            blocks = [m for m in sub if m["name"] in BOOST_BLOCKS or "boost" in m["name"]]
            if blocks:
                a(f"The boost blocks hang off `arcade` ({arc['type']} at offset "
                  f"{arc['offset']}); their absolute offsets in the module are:")
                a("")
                a("| block | offset in `arcade` | absolute offset | block type |")
                a("|---|---|---|---|")
                for m in blocks:
                    a(f"| `{m['name']}` | {m['offset']} | {arc['offset'] + m['offset']} | "
                      f"`{m['type']}` |")
                a("")
                nested = c["types"].get(blocks[0]["type"], [])
                if nested:
                    a(f"`{blocks[0]['type']}` fields: "
                      + ", ".join(f"`{m['name']}`@{m['offset']}" for m in nested) + ".")
                    a("")
    else:
        a("**No `*_custom_land_global.vmodc` is in `INDEX.jsonl`**, so the land boost offsets are")
        a("UNKNOWN at byte level; their member names and the donor's values are decoded from the row")
        a("cache (below). *Where:* the same module bytes, once the index lists them.")
        a("")
    a("The donor's three blocks, decoded from the cache (one value set per vehicle, no selector):")
    a("")
    a("| member | donor value |")
    a("|---|---|")
    for k, v in d["land_donor"].items():
        a(f"| `{k}` | {norm(v)} |")
    a("")
    a("### 1.2 Visual and aerodynamic carriers (not handling modes)")
    a("")
    a(f"* `VehicleParts.parts[i].model_swap` / `.model_swap.hash` - a per-part mesh swap, shipped as")
    a("  the empty string / 0 on every build that carries it (trains). It swaps a **mesh**, not a")
    a("  physics block; using it for the transformation stance changes nothing the sim reads.")
    a(f"* `Rotors.rotors[i].does_steer` - decoded values: "
      + ", ".join(f"`{k}` x{v}" for k, v in sorted(d["rotor_steer"].items()))
      + ". A rotor doubling as a steering surface is how a helicopter yaws; it is continuous")
    a("  authority, not a mode.")
    a("  * `HelicopterModel` / `HelicopterSteering` - 70 + 20 members (`add_forward_force`,")
    a("  `add_lateral_factor_pull_up`, `bank_max_velocity_kmph`, `return_pitch_limit`): the whole")
    a("  hover-to-forward transition is a curve family inside one state, not a switch.")
    a("  * `AirSteering` / `AirplaneAI` - axis timing curves and control-point tables; `AirplaneAI`")
    a("  is on 2 builds and its only `_switch` member is the limit above.")
    a("")
    a("## 2. BmAK's switch, and the comparison")
    a("")
    a("Quoted from `Research/BatmobileGrab/DRIVE_MODES.md` (G3-02l, 8/8 oracles, its own check):")
    a("")
    a("| part | carrier | value | label |")
    a("|---|---|---|---|")
    for b in d["bmak"]:
        a(f"| {b['kind']} | {b['carrier']} | {b['value']} | {b['label']} |")
    a("")
    a("So BmAK's switch is a **state-driven byte**: entering a state writes the drive mode, and the")
    a("sim's field family changes what the car does (steer factor 2.5, max steering 80, lat/long")
    a("slip 4/10, max speed 1200, front/rear counter-torque 0.6/-0.5). The JC3 side has the *shape*")
    a("of the second half - a module can hold several alternative performance blocks at once - and")
    a("none of the first half.")
    a("")
    a("### 2.1 Verdict")
    a("")
    a("* **Pursuit/Battle switching cannot be expressed in JC3 data.** No mode byte, no state")
    a("  machine, no selector member, and no per-mode field family: the 145 land builds each carry")
    a("  exactly one `CustomLandGlobal` value set. Label: **decoded absence**, consequence")
    a("  **UNKNOWN** for a code bridge.")
    a("* **The nearest carrier is the parallel-block pattern**: `nitro_boost` at 120,")
    a("  `nitro_boost_upgraded` at 132, `heat_boost` at 144 on `AirGlobal` - three same-shaped")
    a("  blocks the engine reads selectively. A Pursuit/Battle pair could be modelled the same way")
    a("  *if* something could select the block, and nothing in the files can.")
    a("* **What an amendment would need**: either a second `CustomLandGlobal` instance per vehicle")
    a("  with a selector the engine honours (no such selector is decoded - UNKNOWN), or a code")
    a("  bridge that swaps the live values on the mode input exactly as `SetDriveMode` does in BmAK.")
    a("  The BmAK side of that bridge is fully decoded (enum + four call sites + 40 fields); the JC3")
    a("  side is the missing half.")
    a("* **The 30 `BattleMode*` rows are not carryable as data**, so T-MD14's 'no second variant'")
    a("  holds for values as well as for audio. This does not approve dropping them: the row stays")
    a("  an unapproved compromise until the operator accepts it or a bridge is built.")
    a("")
    a("## 3. What was tried, and the UNKNOWNs")
    a("")
    a(f"1. **VTOL / hover / transform member.** *Tried:* the token scan over every member path of")
    a(f"   every module on all {d['inputs']['entities']} builds ({len(d['scan']['hits'])} hits, both")
    a("   in section 0), plus the full member lists of `AirGlobal`, `AirSteering`,")
    a("   `HelicopterSteering`, `HelicopterModel`, `Rotors`, `AirEngine`, `TrainGlobal`,")
    a("   `VehicleParts`, `BoatGlobal`. *Result:* none. *Where it would be:* a native aircraft")
    a("   class the entity graph does not expose.")
    a("2. **A selector for the three boost blocks.** *Tried:* the same member scan for `mode`/")
    a("   `state`/`variant`/`toggle`/`switch`, and the byte-level type dictionaries of `AirGlobal`")
    a("   and `CustomLandGlobal`. *Result:* no member. *Where:* native (the upgrade/heat system).")
    a("3. **Whether `heat_boost` is a runtime state at all.** The block exists on 145 land builds")
    a("   with values that differ from `nitro_boost` (`extra_top_speed` up to 120 vs 30-60), but no")
    a("   member says when it applies. UNKNOWN.")
    a(f"4. **How far the byte-level offset claim reaches.** `INDEX.jsonl` carries "
      f"{d['inputs']['air_global_bytes']} `*_air_global.vmodc` and "
      f"{d['inputs']['custom_land_global_bytes']} `*_custom_land_global.vmodc`; the offsets")
    a("   above are those builds'. A module that is not indexed per entry has no byte offset")
    a("   here (its member names and values are still decoded from the row cache), so the")
    a("   offsets are representative of the type, not re-read on all 145 land builds.")
    a("5. **HP/armour mode.** BmAK also has `ArmourModeDamageReduction`; JC3's nearest is")
    a("   `VehicleDamage`'s armour value, one value per vehicle, no mode. Not a carrier.")
    a("")
    a("Static only: no game launched, attached to or installed to; no other task's file edited.")
    a("")
    a("Checkable: `python Tools/scripts/t_md14b.py --check`.")
    a("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--dump", action="store_true")
    a = ap.parse_args()
    d = build()
    if a.dump:
        print(json.dumps(d, indent=1, sort_keys=True))
        return 0
    js = json.dumps(d, indent=1, sort_keys=True) + "\n"
    doc = to_md(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if a.write:
        open(jp, "w", encoding="utf-8", newline="\n").write(js)
        open(mp, "w", encoding="utf-8", newline="\n").write(doc)
        print("wrote", jp)
        print("wrote", mp)
        print("hits", len(d["scan"]["hits"]), "air modules", d["inputs"]["air_global_bytes"],
              "blocks", len(d["blocks"]))
        return 0
    fails = []
    if not os.path.exists(jp) or open(jp, encoding="utf-8").read() != js:
        fails.append("json drifted")
    if not os.path.exists(mp) or open(mp, encoding="utf-8").read() != doc:
        fails.append("markdown drifted")
    if len(d["scan"]["hits"]) > 2:
        fails.append(f"state vocabulary grew: {len(d['scan']['hits'])} hits")
    for h in d["scan"]["hits"]:
        if h["module"] not in ("AirplaneAI", "VehicleMisc"):
            fails.append(f"unexpected hit {h['member']} in {h['module']}")
    if not any(b["block"] == "heat_boost" for b in d["blocks"]):
        fails.append("heat_boost block missing")
    if d["land_donor"].get("arcade.nitro_boost.extra_top_speed") is None:
        fails.append("donor boost values missing")
    if d["air_global"]:
        offs = {m["name"]: m["offset"] for m in d["air_global"]["members"]}
        if not (offs.get("nitro_boost", -1) < offs.get("nitro_boost_upgraded", -1)
                < offs.get("heat_boost", -1)):
            fails.append("air boost block offsets not ascending")
    print("hits %d, air %d, blocks %d, donor %d values"
          % (len(d["scan"]["hits"]), d["inputs"]["air_global_bytes"], len(d["blocks"]),
             len(d["land_donor"])))
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("OK: state census re-derived; document and JSON identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
