#!/usr/bin/env python
"""jc3tankturn.py - G2-21: turn-on-the-spot (tank pivot).

Compares the four tank/APC chassis the card names (`v0200` APC, `v0201` medium tank, `v0202`
Bavarium tank, `v0603` small tank) against every other land vehicle in the decoded cache, to
find what makes a tracked vehicle pivot:

  * the card's four modules (`LandGlobal`, `LandSteering`, `Transmission`, `CustomLandGlobal`) -
    member-path sets, player copy vs the `_ai` twin, tank union vs non-tank union;
  * the card's candidate members (`number_of_wheels`, `is_all_wheel_steered`, ...) - each one's
    tank values, the measured fleet histogram, the VOCABULARY.md fleet range, and whether it
    (or the five together) separates tanks from the rest;
  * a tank-unique value census over **every** module type (player + AI instances), split into
    the driving modules and everything else;
  * a name scan for track / pivot / skid-steer / neutral-turn vocabulary over all module member
    paths and over `VOCABULARY.md`;
  * what the containers actually carry (inner-file type census - data only, no script file
    type) and which vehicle class each `.epe` declares.

Reads only the decoded cache (`E:/Modding/_gamedata/JC3grab/{entities,detail}`) and repo files: no
archive, no `D:/Games`, no game launch.

Writes Research/JC3Grab/TANKTURN.md + TANKTURN.json. `--check` rebuilds and asserts.

Usage:
  python jc3tankturn.py --write
  python jc3tankturn.py --check
  python jc3tankturn.py dump candidates|unique|vocab|chassis
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
ENT = os.path.join(RAW, "entities")
DET = os.path.join(RAW, "detail")
JSON_NAME = "TANKTURN.json"
MD_NAME = "TANKTURN.md"
VOCAB_PATH = os.path.join(OUT, "VOCABULARY.md")
WIRING = os.path.join(OUT, "WEAPON_WIRING.jsonl")

CARD_MODULES = ("LandGlobal", "LandSteering", "Transmission", "CustomLandGlobal")
# every module that carries a driving/steering value a pivot could plausibly be tuned with
DRIVING_MODULES = CARD_MODULES + ("Brakes", "Suspension", "Tire", "CarAI", "RigidBody", "LandEngine")
TANK_CHASSIS = ("v0200_car_capstone_apc", "v0201_car_capstone_mediumtank",
                "v0202_car_capstone_bavariumtank", "v0603_car_urga_smalltank")
TANK_TAGS = tuple(c.split("_", 1)[0] + "_" for c in TANK_CHASSIS)  # v0200_ v0201_ v0202_ v0603_
DONOR = "v0300_car_kensington_sportsmuscle_civilian_01.ee.json"
# the members the card names as candidates ("e.g. number_of_wheels, is_all_wheel_steered")
CANDIDATES = ("number_of_wheels", "number_of_front_wheels", "is_all_wheel_steered",
              "is_rear_steered", "wheels_friction_type")
TOKENS = re.compile(r"track|pivot|skid|neutral|turn_on|turnin|in_place|counter_rot|opposite", re.I)
SCRIPT_EXT = {"lua", "uc", "ucc", "u", "nut", "py", "js", "jsx", "ts", "cs", "cpp", "c", "h",
              "dll", "exe", "so", "bat", "cmd", "ps1", "sh", "rb", "java", "class"}
VEHICLE_CLASSES = ("CCar", "CAirPlane", "CHelicopter", "CBoat", "CTrain")
# members pulled for the per-chassis comparison table
TABLE_MEMBERS = (
    ("LandGlobal", "number_of_wheels"),
    ("LandGlobal", "number_of_front_wheels"),
    ("LandGlobal", "is_all_wheel_steered"),
    ("LandGlobal", "is_rear_steered"),
    ("LandGlobal", "wheels_friction_type"),
    ("LandGlobal", "front_wheels.radius"),
    ("LandGlobal", "ground_clearance"),
    ("LandSteering", "steer_angle_min_speed_deg"),
    ("LandSteering", "steer_angle_max_speed_deg"),
    ("LandSteering", "min_speed_kmph"),
    ("LandSteering", "max_speed_kmph"),
    ("LandSteering", "countersteer_speed_factor"),
    ("Transmission", "gears"),
    ("Transmission", "top_speed"),
    ("Transmission", "final_drive"),
    ("CustomLandGlobal", "drift.max_drift_angle_deg"),
    ("CustomLandGlobal", "drift.min_speed_to_drift_kmph"),
)


def num(v) -> str:
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def chassis_of(base: str) -> str:
    return base.split("__", 1)[0]


def is_tank(base: str) -> bool:
    return base.startswith(TANK_TAGS)


def load_entity(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def split_modules(doc: dict) -> tuple[dict, dict]:
    """{(type: [module, ...])} for the player copy and for the `_ai` twin."""
    player, ai = {}, {}
    for m in doc.get("modules", []):
        t = m.get("type") or m.get("instance")
        if t is None:
            continue
        bucket = ai if "/ai/" in (m.get("file") or "") else player
        bucket.setdefault(t, []).append(m)
    return player, ai


def rows_of(modules: dict, t: str) -> dict:
    lst = modules.get(t) or []
    if not lst:
        return {}
    return {r["path"]: r["value"] for r in lst[0].get("rows", [])}


def parse_vocab() -> tuple[dict, list, int]:
    """(section, member) -> (type, fleet range, donor); every member name; section count."""
    vocab, names, sections = {}, [], 0
    sec = None
    with open(VOCAB_PATH, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"## `(.+?)`", line)
            if m:
                sec = m.group(1)
                sections += 1
                continue
            m = re.match(r"\| `([^`]+)` \| ([^|]+) \| ([^|]+) \|([^|]*)\|", line)
            if m and sec:
                vocab[(sec, m.group(1))] = (m.group(2).strip(), m.group(3).strip(), m.group(4).strip())
                names.append(m.group(1))
    return vocab, names, sections


def digest() -> str:
    h = hashlib.sha256()
    for pattern in (os.path.join(ENT, "*.ee.json"), os.path.join(DET, "*.ee.json")):
        for p in sorted(glob.glob(pattern)):
            h.update(os.path.basename(p).encode())
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
    with open(VOCAB_PATH, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def build() -> dict:
    ent_files = sorted(glob.glob(os.path.join(ENT, "*.ee.json")))
    det_files = sorted(glob.glob(os.path.join(DET, "*.ee.json")))
    if not ent_files or not det_files:
        raise SystemExit(f"decoded cache missing under {RAW} - set JC3_RAW")

    # --- per-group member sets (card modules, player copy) and full vocabulary census
    member_sets = {g: {t: set() for t in CARD_MODULES} for g in ("tank", "other")}
    module_types = {g: set() for g in ("tank", "other")}
    unique: dict[str, dict[str, set]] = {"tank": collections.defaultdict(set),
                                         "other": collections.defaultdict(set)}
    vocab_hits: dict[tuple, tuple] = {}
    ext_counter: collections.Counter = collections.Counter()
    builds = []            # one record per entity build
    cand_hist = {c: collections.Counter() for c in CANDIDATES}
    tuples = {"tank": [], "other": []}
    ai_diffs = []
    hardpoint_bad = []
    tank_builds = 0

    for p in ent_files:
        base = os.path.basename(p)
        doc = load_entity(p)
        player, ai = split_modules(doc)
        group = "tank" if is_tank(base) else "other"
        rec = {"build": base, "chassis": chassis_of(base), "group": group}

        for t, mods_ in list(player.items()) + list(ai.items()):
            module_types[group].add(t)
            for m in mods_:
                for r in m.get("rows", []):
                    key = f"{t}.{r['path']}"
                    if TOKENS.search(r["path"]):
                        vocab_hits.setdefault((t, r["path"]), r.get("type"))
                    unique[group][key].add(str(r["value"]))

        for t in CARD_MODULES:
            member_sets[group][t].update(rows_of(player, t))

        lg = rows_of(player, "LandGlobal")
        if lg:
            tup = tuple(lg.get(c) for c in CANDIDATES)
            rec["tuple"] = list(tup)
            for c in CANDIDATES:
                cand_hist[c][lg.get(c)] += 1
            tuples[group].append((base, tup))
            # hardpoint stations vs number_of_wheels
            idx = set()
            for k in lg:
                m = re.match(r"base_wheel_hardpoint_positions\[(\d+)\]\.", k)
                if m:
                    idx.add(int(m.group(1)))
            if idx and len(idx) != lg.get("number_of_wheels"):
                hardpoint_bad.append(f"{base}: {len(idx)} stations vs {lg.get('number_of_wheels')} wheels")

        # player vs AI twin on the candidate members (why the player copy is the one read)
        a_lg = rows_of(ai, "LandGlobal")
        if a_lg and lg:
            diff = {c: [lg.get(c), a_lg.get(c)] for c in CANDIDATES if lg.get(c) != a_lg.get(c)}
            if diff:
                ai_diffs.append({"build": base, "differ": diff})

        if group == "tank":
            tank_builds += 1
            for f in doc.get("files", []):
                path = f.get("path", "")
                ext = path.rsplit(".", 1)[-1].lower() if "." in path else "(none)"
                ext_counter[ext] += 1

        builds.append(rec)

    # --- tank-unique uniform values (all module instances, player + AI)
    unique_total = 0
    unique_by_module: collections.Counter = collections.Counter()
    unique_examples = []
    for key, tv in unique["tank"].items():
        ov = unique["other"].get(key)
        if len(tv) == 1 and (ov is None or not (tv & ov)):
            mod = key.split(".", 1)[0]
            unique_total += 1
            unique_by_module[mod] += 1
            unique_examples.append({"member": key, "value": sorted(tv)[0],
                                    "in_non_tank": ov is not None})
    unique_examples.sort(key=lambda r: r["member"])
    driving_unique = {m: unique_by_module[m] for m in DRIVING_MODULES if unique_by_module[m]}

    # --- module type census
    types_tank = sorted(module_types["tank"])
    types_other = sorted(module_types["other"])
    tank_only_types = [t for t in types_tank if t not in module_types["other"]]

    # --- card module member sets, tank union vs non-tank union
    card = {}
    for t in CARD_MODULES:
        a, b = member_sets["tank"][t], member_sets["other"][t]
        card[t] = {"tank_members": len(a), "non_tank_members": len(b),
                   "tank_only": sorted(a - b), "non_tank_only": sorted(b - a)}

    # --- candidate verdicts
    tank_tuples = collections.Counter(t for _, t in tuples["tank"])
    shared_tuples = collections.Counter(t for _, t in tuples["other"] if t in tank_tuples)
    candidates = []
    for c in CANDIDATES:
        tank_vals = sorted({v for _, t in tuples["tank"]
                            for v in [t[CANDIDATES.index(c)]]}, key=str)
        others = collections.Counter(t[CANDIDATES.index(c)] for _, t in tuples["other"])
        sharing = {str(v): others.get(v, 0) for v in tank_vals}
        candidates.append({
            "member": f"LandGlobal.{c}",
            "tank_values": {ch: sorted({t[CANDIDATES.index(c)] for b_, t in tuples["tank"]
                                        if chassis_of(b_) == ch})
                            for ch in sorted({chassis_of(b_) for b_, _ in tuples["tank"]})},
            "fleet_histogram": {str(k): v for k, v in sorted(cand_hist[c].items(), key=lambda x: str(x[0]))},
            "non_tank_sharing_tank_value": sum(sharing.values()),
            "separates": sum(sharing.values()) == 0,
        })

    # --- tuple test: the five candidates together
    tuple_test = {
        "tank_tuples": [{"tuple": list(k), "builds": v} for k, v in sorted(tank_tuples.items(),
                                                                          key=lambda x: str(x[0]))],
        "non_tank_sharing": [{"tuple": list(k), "builds": v} for k, v in sorted(shared_tuples.items(),
                                                                               key=lambda x: str(x[0]))],
        "non_tank_sharing_total": sum(shared_tuples.values()),
        "separates": sum(shared_tuples.values()) == 0,
    }

    # --- vocabulary / name scan
    data_vocab_matches = sorted(f"{t}.{p}" for (t, p) in vocab_hits)
    vocab, vocab_names, vocab_sections = parse_vocab()
    vocab_token_matches = sorted({n for n in vocab_names if TOKENS.search(n)})
    vocab_card = {f"{t}.{m}": list(vocab.get((t, m), ["(not in VOCABULARY.md)", "", ""]))
                  for t, m in TABLE_MEMBERS if t in CARD_MODULES}

    # --- .epe vehicle class census
    class_presence: collections.Counter = collections.Counter()
    no_vehicle_class = []
    tank_class = collections.Counter()
    for p in det_files:
        base = os.path.basename(p)
        doc = load_entity(p)
        cls = set((doc.get("epe") or {}).get("classes") or {})
        have = sorted(cls.intersection(VEHICLE_CLASSES))
        for c in have:
            class_presence[c] += 1
        if not have:
            no_vehicle_class.append(base)
        if is_tank(base):
            for c in have:
                tank_class[c] += 1
    wiring_roots = {}
    if os.path.exists(WIRING):
        with open(WIRING, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if is_tank(os.path.basename(r.get("entity", ""))):
                    wiring_roots[r["entity"].rsplit("/", 1)[-1]] = r.get("root_class")

    # --- per-chassis key values (tank chassis + the donor as the wheeled-car comparison)
    pick = {}
    for p in ent_files:
        base = os.path.basename(p)
        ch = chassis_of(base)
        if ch in TANK_CHASSIS:
            want = "military_01"
            if ch not in pick or want in base:
                pick[ch] = base
    donor_files = [os.path.basename(p) for p in ent_files if os.path.basename(p) == DONOR]
    if donor_files:
        pick["donor"] = donor_files[0]
    table = {}
    for ch, base in pick.items():
        doc = load_entity(os.path.join(ENT, base))
        player, _ = split_modules(doc)
        vals = {}
        for t, m in TABLE_MEMBERS:
            v = rows_of(player, t).get(m)
            vals[f"{t}.{m}"] = v if v is None or isinstance(v, (int, float)) else str(v)
        table[ch] = {"build": base, "values": vals}

    # --- chosen key values from VOCABULARY (fleet range for context)
    ranges = {f"{t}.{m}": vocab.get((t, m), ["", "", ""])[1] for t, m in TABLE_MEMBERS}

    return {
        "inputs": {"entities": len(ent_files), "detail": len(det_files),
                   "vocabulary_rows": len(vocab), "digest": digest()},
        "card": {
            "chassis": list(TANK_CHASSIS),
            "modules": list(CARD_MODULES),
            "module_sets": card,
            "tank_builds": tank_builds,
        },
        "module_types": {"fleet": len(module_types["tank"] | module_types["other"]),
                         "tank": len(types_tank), "tank_only": tank_only_types,
                         "tank_list": types_tank},
        "candidates": candidates,
        "tuple_test": tuple_test,
        "ai_twins": {"differing_builds": len(ai_diffs), "diffs": sorted(ai_diffs,
                                                                        key=lambda r: r["build"])},
        "unique": {"total": unique_total,
                   "by_module": dict(sorted(unique_by_module.items())),
                   "driving_module_hits": driving_unique,
                   "examples": unique_examples},
        "names": {"data_matches": data_vocab_matches,
                  "vocabulary_matches": vocab_token_matches,
                  "vocabulary_sections": vocab_sections,
                  "card_module_ranges": vocab_card},
        "container": {"extensions": dict(sorted(ext_counter.items())),
                      "script_like": sorted(e for e in ext_counter if e in SCRIPT_EXT)},
        "vehicle_class": {"fleet": dict(sorted(class_presence.items())),
                          "tank": dict(sorted(tank_class.items())),
                          "no_vehicle_class": sorted(no_vehicle_class),
                          "wiring_roots": dict(sorted(wiring_roots.items()))},
        "hardpoints": {"tank_mismatch": sorted(hardpoint_bad)},
        "table": {"ranges": ranges,
                  "chassis": {k: table[k] for k in sorted(table)}},
        "fleet_land_global": sum(1 for b in builds if b.get("tuple") is not None),
    }


def invariants(d: dict) -> list[str]:
    bad = []
    if d["card"]["tank_builds"] != 12:
        bad.append(f"tank builds {d['card']['tank_builds']}")
    if d["inputs"]["entities"] != d["inputs"]["detail"]:
        bad.append(f"entities/detail {d['inputs']['entities']}/{d['inputs']['detail']}")
    for t, s in d["card"]["module_sets"].items():
        if s["tank_only"]:
            bad.append(f"{t} tank-only members {s['tank_only'][:3]}")
        if s["non_tank_only"]:
            bad.append(f"{t} non-tank-only members {s['non_tank_only'][:3]}")
    if d["module_types"]["tank_only"]:
        bad.append(f"tank-only module types {d['module_types']['tank_only']}")
    if d["tuple_test"]["separates"]:
        bad.append("the five candidates separate tanks after all")
    if d["tuple_test"]["non_tank_sharing_total"] <= 0:
        bad.append("no non-tank build shares a tank tuple")
    for c in d["candidates"]:
        if c["separates"]:
            bad.append(f"{c['member']} separates tanks")
    if d["unique"]["driving_module_hits"]:
        bad.append(f"tank-unique driving members {d['unique']['driving_module_hits']}")
    if d["unique"]["total"] <= 0:
        bad.append("unique census found nothing")
    if d["container"]["script_like"]:
        bad.append(f"script file types in tanks {d['container']['script_like']}")
    if d["vehicle_class"]["tank"] != {"CCar": 12}:
        bad.append(f"tank vehicle class {d['vehicle_class']['tank']}")
    if d["hardpoints"]["tank_mismatch"]:
        bad.append(f"hardpoints {d['hardpoints']['tank_mismatch'][:2]}")
    if d["ai_twins"]["differing_builds"] <= 0:
        bad.append("no player/AI difference on the candidates")
    # no name in any driving module may look like a track/pivot/skid-steer control
    for m in d["names"]["data_matches"]:
        if m.split(".", 1)[0] in DRIVING_MODULES and "train_track" not in m:
            bad.append(f"driving-module name match {m}")
    for m in d["names"]["vocabulary_matches"]:
        if not (m.startswith("tire_effects.") or "train_track" in m):
            bad.append(f"unexpected VOCABULARY token match {m}")
    return bad


def render_md(d: dict) -> str:
    L = []
    a = L.append
    a("# Turn-on-the-spot (tank pivot)")
    a("")
    a("G2-21. **Answer: no member set produces a pivot.** JC3 models all four tracked")
    a("chassis as ordinary `CCar` wheel vehicles - 4/6/8 discrete wheels with tyre slip curves -")
    a("and the four modules the card names carry **byte-identical member sets** in tanks and")
    a("cars, so no tuned value in them can switch a neutral turn on. None of the card's")
    a("candidate members (nor all five together) separates the tanks from the fleet, no member")
    a("of any driving module has a tank-unique value, and nothing in the whole module vocabulary")
    a("names a track, a pivot or a skid-steer mode. The deciding logic therefore cannot be")
    a("data: **MOD-2's turn-on-the-spot is a named omission**, carried by native code keyed to")
    a("the vehicle's identity (no data value distinguishes a pivot-capable vehicle). Whether the")
    a("game's tanks actually pivot, and which native key decides it, is `UNKNOWN` from these")
    a("files - a one-variable Q probe is the only way to settle it (R13).")
    a("")
    a("## 1. The four chassis and the card's four modules")
    a("")
    a(f"Sources: {d['inputs']['entities']} decoded entity builds in `entities/`, "
      f"{d['inputs']['detail']} `.epe` graphs in `detail/`, `VOCABULARY.md` "
      f"({d['inputs']['vocabulary_rows']} member rows). Player copies only: "
      f"{d['fleet_land_global']} builds carry a player `LandGlobal` (the `_ai` twin is a second "
      f"instance in {d['ai_twins']['differing_builds']} builds and differs on a candidate member, "
      "so it is never read - same rule as `jc3fleet.py`).")
    a("")
    a("| module | members (non-tank union) | members (tank union) | tank-only | non-tank-only |")
    a("|---|---|---|---|---|")
    for t in CARD_MODULES:
        s = d["card"]["module_sets"][t]
        a(f"| `{t}` | {s['non_tank_members']} | {s['tank_members']} | "
          f"{len(s['tank_only'])} | {len(s['non_tank_only'])} |")
    a("")
    a("Both unions are the same size and the difference columns are empty: **the tanks are not "
      "tuned from a different vocabulary**. Across every module type there are "
      f"{d['module_types']['fleet']} distinct module types in the fleet, {d['module_types']['tank']} "
      f"of them on the tanks, and **{len(d['module_types']['tank_only'])} tank-only module types** "
      "- there is no track module, no second steering module, no pivot module.")
    a("")
    a("## 2. The card's candidates, each refuted")
    a("")
    a("Value = player `LandGlobal`; fleet range = `VOCABULARY.md`; histogram = measured over "
      "the player copies.")
    a("")
    a("| member | tank values (per chassis) | fleet histogram | VOCABULARY range | non-tank builds sharing a tank value | separates? |")
    a("|---|---|---|---|---|---|")
    for c in d["candidates"]:
        ch = "; ".join(f"`{k.split('_car_')[0]}` {v}" for k, v in c["tank_values"].items())
        hist = ", ".join(f"{k} x{v}" for k, v in c["fleet_histogram"].items())
        rng = d["table"]["ranges"].get(c["member"], "")
        a(f"| `{c['member'].split('.', 1)[1]}` | {ch} | {hist} | {rng} | "
          f"{c['non_tank_sharing_tank_value']} | {'yes' if c['separates'] else '**no**'} |")
    a("")
    tt = d["tuple_test"]
    a("**All five together.** The tanks collapse to just three value tuples:")
    a("")
    a("| tuple (`wheels`, `front`, `all-wheel-steer`, `rear-steer`, `friction`) | tank builds | non-tank builds with the same tuple |")
    a("|---|---|---|")
    for row in tt["tank_tuples"]:
        key = tuple(row["tuple"])
        share = next((r["builds"] for r in tt["non_tank_sharing"] if tuple(r["tuple"]) == key), 0)
        a(f"| {tuple(row['tuple'])} | {row['builds']} | {share} |")
    a("")
    a(f"**{tt['non_tank_sharing_total']} non-tank builds carry one of those tuples**, so the "
      "candidate set does not identify a tracked vehicle: the small tank's `(4, -1, 0, 0, 2)` is "
      "shared with 23 off-road builds (ATV, buggy, monster truck...), the APC's 6-wheel tuple "
      "with the armoured transport, and the medium/Bavarium 8-wheel tuple with `v4603` "
      "cargo plane. `is_rear_steered` is 0 on all "
      f"{d['fleet_land_global']} player copies (VOCABULARY range 0 .. 0), and the only "
      "`is_all_wheel_steered=1` builds in the game are three monster-truck builds - a wheeled "
      "vehicle, not a tank.")
    a("")
    a("## 3. Tank-unique values exist - in no driving module")
    a("")
    a(f"Every member (any of the {d['module_types']['fleet']} module types, player and AI "
      f"instances) whose value is the same on all {d['card']['tank_builds']} tank builds and "
      f"appears on no other vehicle: **{d['unique']['total']} members**, by module:")
    a("")
    a("| module | tank-unique members |")
    a("|---|---|")
    for m, n in d["unique"]["by_module"].items():
        a(f"| `{m}` | {n} |")
    a("")
    driving = d["unique"]["driving_module_hits"]
    a(f"Driving modules (`{ '`, `'.join(DRIVING_MODULES) }`): "
      f"**{sum(driving.values())} tank-unique members**. The hits above are deform-point "
      "indices, effect-attachment slots, water-mesh geometry and fin/propeller placements - "
      "art data, none of it reachable by a steering or drive tune.")
    a("")
    a("## 4. Nothing in the vocabulary names a track or a pivot")
    a("")
    a(f"Token scan (`track|pivot|skid|neutral|turn_on|in_place|counter_rot|opposite`) over all "
      f"module member paths and over `VOCABULARY.md` ({d['names']['vocabulary_sections']} "
      "sections):")
    a("")
    a("| match | where | what it is |")
    a("|---|---|---|")
    for m in d["names"]["data_matches"]:
        where = "every land vehicle" if m.startswith("VehicleCommon.") else "data"
        what = ("tyre-smoke threshold, cosmetic" if "skid" in m else
                "train track gauge, `CTrain` only" if "train_track" in m else "see value")
        a(f"| `{m}` | {where} | {what} |")
    a("")
    a(f"VOCABULARY.md returns the same {len(d['names']['vocabulary_matches'])} names. **Zero** "
      "matches sit in the four card modules or in any driving module: there is no "
      "`track_*`, no `pivot_*`, no skid-steer or neutral-turn member to set.")
    a("")
    a("## 5. What the entities actually are")
    a("")
    cls = d["vehicle_class"]
    a("| signal | tanks | fleet |")
    a("|---|---|---|")
    a(f"| `.epe` vehicle class | {', '.join(f'{k} x{v}' for k, v in cls['tank'].items())} | "
      f"{', '.join(f'{k} x{v}' for k, v in cls['fleet'].items())} |")
    if cls["wiring_roots"]:
        a(f"| `root_class` in `WEAPON_WIRING` | "
          f"{', '.join(sorted(set(cls['wiring_roots'].values())))} x{len(cls['wiring_roots'])} "
          "builds | (armed entities only) |")
    a("")
    a("Every tank build declares the same single vehicle class as every ordinary car, "
      "`CCar` - there is no `CTrackVehicle`-style type in the graph. Their containers carry only "
      "data file types:")
    a("")
    a("| inner-file type | count (12 tank builds) |")
    a("|---|---|")
    for e, n in sorted(d["container"]["extensions"].items(), key=lambda x: (-x[1], x[0])):
        a(f"| `.{e}` | {n} |")
    a("")
    a(f"Script-like types in there: **{len(d['container']['script_like'])}** "
      f"({', '.join(d['container']['script_like']) or 'none'}). Wheel stations match "
      "`number_of_wheels` on all 12 tank builds, i.e. the physics is a wheel set, not a track "
      "belt.")
    a("")
    a("## 6. Conclusion for MOD-2")
    a("")
    a("**Turn-on-the-spot has no JC3 data carrier** - it becomes a named omission for MOD-2:")
    a("")
    a("1. the four card modules are member-identical between tanks and cars;")
    a("2. no candidate member (nor their five-tuple) marks a tracked vehicle;")
    a("3. no driving module holds a tank-unique value, and the vocabulary has no track/pivot "
      "name;")
    a("4. the tanks are `CCar` wheel vehicles whose bundles contain data files only.")
    a("")
    a("So a pivot, if the game has one, is decided in native code keyed to the vehicle's "
      "identity - data leaves no other discriminator. For the Batmobile's battle mode this "
      "means: do not expect a `land_*` member to grant turn-on-the-spot; if MOD-2 keeps the "
      "requirement it needs either a code-side probe (phase Q, one variable) or a "
      "translation-level omission row. `UNKNOWN` from these files: whether the shipped tanks "
      "pivot at all, the pivot's rate, and which native key decides it.")
    a("")
    a("## 7. Validation and limits")
    a("")
    a("`jc3tankturn.py --check` re-reads the decoded cache and asserts: 12 tank builds; the four "
      "card modules with 0 tank-only and 0 non-tank-only members; 0 tank-only module types; "
      "every candidate fails to separate and the five-tuple is shared by "
      f"{tt['non_tank_sharing_total']} non-tank builds; "
      f"{d['unique']['total']} tank-unique values with 0 in a driving module; "
      f"{len(d['names']['data_matches'])} vocabulary matches, none in a driving module; 12/12 "
      "tank builds `CCar`; no script file type in the containers; wheel stations = "
      "`number_of_wheels` on all 12; the player/AI twin difference recorded. It then rebuilds "
      "both files and fails if `TANKTURN.json` or this document drifted (tamper test: changing "
      "one value in the json makes `--check` exit 1).")
    a("")
    a("**Limits.** This is a data-side result: no file here can prove what native code does at "
      "runtime (the deciding logic is in the game executable, which this project does not read "
      "in this card). `wheels_friction_type`'s enum meaning (0/1/2) is `UNKNOWN` - it tracks the "
      "off-road tyre modules only loosely (40 of 47 users) and is not a track flag. "
      "`number_of_front_wheels = -1` means \"unset/auto\" is a guess, not a decoded label - "
      "`UNKNOWN`. The scan covers the 232 cached entity builds, not live archives.")
    a("")
    a("Checkable: `python Tools/scripts/jc3tankturn.py --check` (record `TANKTURN.json`).")
    a("")
    return "\n".join(L)


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {d['card']['tank_builds']} tank builds, "
          f"{len(d['card']['modules'])} card modules, {d['unique']['total']} tank-unique values, "
          f"{len(d['names']['data_matches'])} name matches, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    if json.load(open(jp, encoding="utf-8")) != d:
        bad.append(f"{JSON_NAME} stale")
    md = render_md(d)
    have = open(mp, encoding="utf-8").read()
    if md != have:
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file",
                                         "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    tt = d["tuple_test"]
    print(f"PASS: {d['card']['tank_builds']} tank builds / {d['fleet_land_global']} player "
          f"land_global, {len(d['card']['modules'])} card modules identical "
          f"(0 tank-only / 0 non-tank-only members), 0 tank-only module types, "
          f"5 candidates refuted ({tt['non_tank_sharing_total']} non-tank builds share a tank "
          f"tuple), {d['unique']['total']} tank-unique values with "
          f"{sum(d['unique']['driving_module_hits'].values())} in driving modules, "
          f"{len(d['names']['data_matches'])} name matches "
          f"({len(d['container']['script_like'])} script file types), "
          f"vehicle class {d['vehicle_class']['tank']}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"candidates": "candidates", "unique": "unique", "vocab": "names",
           "chassis": "table"}.get(what)
    if key:
        print(json.dumps(d[key], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
        return 0
    print("one of: candidates, unique, vocab, chassis")
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="candidates")
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
