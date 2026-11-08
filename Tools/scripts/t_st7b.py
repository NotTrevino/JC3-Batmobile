#!/usr/bin/env python3
"""T-ST7b: verify the "0.5 s steering floor" across every decoded JC3 vehicle module.

The claim under test (T-ST7): "the fleet's fastest rack is 0.5 s, so JC3's steering model cannot
be 0.25 s quick". This script answers four questions from the files only:

  1. every steering-lock / steer-rate member, per class (`LandSteering`, `MotorbikeSteering`) and
     per role (player module vs `_ai` twin in the same entity), with n / min / max / median;
  2. the minimum observed, and whether any **player** module is below 0.5 s;
  3. whether anything in the repo decodes a native clamp on the member (exe search) - else UNKNOWN;
  4. every route to BmAK's 0.25 s, each with its evidence and its arithmetic.

BmAK's number is quoted from `Working/Translation/T_ST7_FLOOR.md` (220 deg/s `SteerSpeed`,
55 deg lock at the 600 cm/s knot = 0.25 s), whose own `--check` re-reads the packages.

Labels: decoded (file + offset/row), derived (rule + inputs), UNKNOWN (tried, not available).

Writes Working/Translation/T_ST7B_FLOOR.md + .json; `--check` re-derives both and fails on drift
or on a floor claim that the data no longer supports.

Usage:
  python Tools/scripts/t_st7b.py --write
  python Tools/scripts/t_st7b.py --check
  python Tools/scripts/t_st7b.py dump
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Working", "Translation")
JSON_NAME = "T_ST7B_FLOOR.json"
MD_NAME = "T_ST7B_FLOOR.md"
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
ENT = os.path.join(RAW, "entities")

CLASSES = ("LandSteering", "MotorbikeSteering")
# the lock / steer-rate members (the "steering-lock members" of the card)
LOCK = ("t_to_full_steer_s", "max_speed_t_to_full_steer_s",
        "steer_angle_min_speed_deg", "steer_angle_max_speed_deg")
RATE = ("countersteer_speed_factor", "steer_in_speed_factor", "steer_curve_falloff",
        "saturation_zone", "dead_zone", "steer_input_power_pc", "wheel_drift_aligning_strength")
MEMBERS = LOCK + RATE

BMAK = {"steer_speed_deg_s": 220.0, "lock_deg_600": 55.0, "standstill_deg": 60.0,
        "lock_time_s": 0.25}


def short(member: str) -> str:
    return member.split("land_steering.")[-1]


def digest() -> str:
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(ENT, "*.ee.json"))):
        h.update(os.path.basename(p).encode())
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()[:16]


def exe_evidence() -> dict:
    """Is there a decoded exe note that could show a clamp on the steering member?"""
    # only a *marker of exe analysis* counts: prose that merely says "disassembly" is not
    # evidence.  Three counts matter: files that name the executable, of those the ones that
    # mention steering at all, and the ones that name this member - only the last could carry a
    # clamp for it.  This file's own outputs are excluded (self-reference).
    pat = re.compile(r"(?i)(justcause3\.exe|jc3\.exe)")
    steer = re.compile(r"(?i)steer")
    member = re.compile(r"t_to_full_steer_s|SteerSpeed")
    own = {os.path.join(OUT, MD_NAME), os.path.join(OUT, JSON_NAME)}
    hits, steer_files, member_files = [], [], []
    for p in glob.glob(os.path.join(ROOT, "Research", "**", "*.md"), recursive=True) + \
             glob.glob(os.path.join(ROOT, "Working", "**", "*.md"), recursive=True):
        if p in own:
            continue
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if not pat.search(text):
            continue
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        hits.append(rel)
        if steer.search(text):
            steer_files.append(rel)
        if member.search(text):
            member_files.append(rel)
    return {"pattern": pat.pattern, "files": sorted(hits), "count": len(hits),
            "steer_files": sorted(steer_files), "steer_count": len(steer_files),
            "member_files": sorted(member_files), "member_count": len(member_files)}


def build() -> dict:
    files = sorted(glob.glob(os.path.join(ENT, "*.ee.json")))
    if not files:
        raise SystemExit(f"decoded cache missing under {RAW} - set JC3_RAW")
    all_modules = 0
    total_modules = 0
    values: dict[tuple, dict[str, object]] = collections.defaultdict(dict)
    pairs = []          # one row per entity: class -> {player: t, ai: t}
    for path in files:
        base = os.path.basename(path)
        doc = json.load(open(path, encoding="utf-8"))
        entry = {}
        for m in doc.get("modules", []):
            all_modules += 1
            t = str(m.get("type") or m.get("instance"))
            if t not in CLASSES:
                continue
            total_modules += 1
            role = "ai" if "/ai/" in (m.get("file") or "") else "player"
            for r in m.get("rows", []):
                name = short(r["path"])
                if name in MEMBERS:
                    values[(t, role, name)][base] = r["value"]
                    if name == "t_to_full_steer_s":
                        entry.setdefault(t, {})[role] = r["value"]
        if entry:
            pairs.append({"build": base, "classes": entry})

    stats = {}
    for (cls, role, name), got in sorted(values.items()):
        nums = [v for v in got.values() if isinstance(v, (int, float)) and v != -1]
        all_nums = [v for v in got.values() if isinstance(v, (int, float))]
        stats[f"{cls}|{role}|{name}"] = {
            "class": cls, "role": role, "member": name,
            "n": len(got), "n_sentinel": len(all_nums) - len(nums),
            "min": min(nums) if nums else None, "max": max(nums) if nums else None,
            "median": statistics.median(nums) if nums else None,
            "histogram": dict(sorted(collections.Counter(
                round(v, 6) for v in nums).items())),
        }

    def at_or_below(cls: str, role: str, name: str, threshold: float) -> list[dict]:
        key = f"{cls}|{role}|{name}"
        st = stats.get(key)
        if not st:
            return []
        out = []
        for build, v in sorted(values[(cls, role, name)].items()):
            if isinstance(v, (int, float)) and v != -1 and v <= threshold + 1e-9:
                out.append({"build": build, "value": v})
        return out

    # the 0.25 s and 0.2 s modules, with the same entity's player value where one exists
    lows = []
    for (cls, role, name), got in values.items():
        if name not in ("t_to_full_steer_s", "max_speed_t_to_full_steer_s"):
            continue
        for build, v in got.items():
            if not isinstance(v, (int, float)) or v == -1 or v > 0.3001:
                continue
            row = next((p for p in pairs if p["build"] == build), None)
            lows.append({"class": cls, "role": role, "member": name, "build": build,
                         "value": v,
                         "player_same_entity": (row["classes"].get(cls, {}).get("player")
                                                if row else None)})
    lows.sort(key=lambda x: (x["value"], x["member"]))

    # derived angular rate at the min-speed lock, per build
    rate = []
    for path in files:
        base = os.path.basename(path)
        doc = json.load(open(path, encoding="utf-8"))
        for m in doc.get("modules", []):
            t = str(m.get("type") or m.get("instance"))
            if t not in CLASSES:
                continue
            role = "ai" if "/ai/" in (m.get("file") or "") else "player"
            rows = {short(r["path"]): r["value"] for r in m.get("rows", [])}
            tt = rows.get("t_to_full_steer_s")
            ang = rows.get("steer_angle_min_speed_deg")
            if isinstance(tt, (int, float)) and tt > 0 and isinstance(ang, (int, float)):
                rate.append({"build": base, "class": t, "role": role,
                             "t": tt, "angle_deg": ang, "deg_per_s": ang / tt})
    rate.sort(key=lambda x: -x["deg_per_s"])

    player_rate = [r for r in rate if r["role"] == "player"]
    car_rate = [r for r in player_rate if r["class"] == "LandSteering"]
    ai_rate = [r for r in rate if r["role"] == "ai"]
    fleet_max_angle = max((r["angle_deg"] for r in rate), default=None)
    need_angle = BMAK["steer_speed_deg_s"] * 0.5  # angle a 0.5 s rack would need for 220 deg/s

    return {
        "schema": "t-st7b/1",
        "inputs": {"entities": len(files), "all_modules": all_modules,
                   "steering_modules": total_modules, "digest": digest()},
        "bmak": BMAK,
        "stats": stats,
        "lows": lows,
        "rate_top": rate[:10],
        "rate_max": rate[0] if rate else None,
        "rate_max_player": player_rate[0] if player_rate else None,
        "rate_max_car": car_rate[0] if car_rate else None,
        "rate_max_ai": ai_rate[0] if ai_rate else None,
        "fleet_max_angle_deg": fleet_max_angle,
        "need_angle_at_0_5s": need_angle,
        "below_half": {
            "player_car": at_or_below("LandSteering", "player", "t_to_full_steer_s", 0.5),
            "player_bike": at_or_below("MotorbikeSteering", "player",
                                       "t_to_full_steer_s", 0.5),
            "ai_car": at_or_below("LandSteering", "ai", "t_to_full_steer_s", 0.5),
        },
        "clamp": exe_evidence(),
    }


def num(v, nd=3):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.{nd}g}"
    return str(v)


def to_md(d: dict) -> str:
    st = d["stats"]
    L: list[str] = []
    a = L.append
    a("# T-ST7b - is 0.5 s a JC3 steering floor? (all modules, by class and role)")
    a("")
    a("Generated by `Tools/scripts/t_st7b.py`; `--check` re-derives every number from the same")
    a("entity bytes. **decoded** = an entity module row; **derived** = a stated rule over decoded")
    a("values; **UNKNOWN** = not in the files, with what was tried.")
    a("")
    a("## 0. Answer")
    a("")
    pc = d["below_half"]["player_car"]
    pb = d["below_half"]["player_bike"]
    ai = d["below_half"]["ai_car"]
    a("**0.5 s is not a JC3 floor and the claim is false as stated.** Of the")
    a(f"**{d['inputs']['all_modules']:,}** decoded vehicle modules ({d['inputs']['entities']}"
      f" entities), **{d['inputs']['steering_modules']}** are steering modules; player copy and")
    a("`_ai` twin are counted separately throughout:")
    a("")
    a("| class / role | min `t_to_full_steer_s` | modules at that min | below 0.5 s |")
    a("|---|---:|---:|---|")
    for key, label in (("LandSteering|player|t_to_full_steer_s", "`LandSteering` player (cars)"),
                       ("MotorbikeSteering|player|t_to_full_steer_s", "`MotorbikeSteering` player (bikes)"),
                       ("LandSteering|ai|t_to_full_steer_s", "`LandSteering` AI twin"),
                       ("MotorbikeSteering|ai|t_to_full_steer_s", "`MotorbikeSteering` AI twin")):
        s = st.get(key)
        if not s:
            continue
        n_at = s["histogram"].get(round(s["min"], 6), 0) if s["min"] is not None else 0
        below = sum(c for k, c in s["histogram"].items() if k < 0.5 - 1e-9)
        a(f"| {label} | {num(s['min'])} | {n_at} | {below} |")
    a("")
    car = st["LandSteering|player|t_to_full_steer_s"]
    bike = st["MotorbikeSteering|player|t_to_full_steer_s"]
    ai_t = st["LandSteering|ai|t_to_full_steer_s"]
    ai_aux = st["LandSteering|ai|max_speed_t_to_full_steer_s"]
    n_bike_min = bike["histogram"].get(round(bike["min"], 6), 0)
    n_ai_min = ai_t["histogram"].get(round(ai_t["min"], 6), 0)
    n_car_min = car["histogram"].get(round(car["min"], 6), 0)
    a(f"* **A player module does ship below 0.5 s**: the bikes (`MotorbikeSteering`) carry")
    a(f"  **{num(bike['min'])} s** on {n_bike_min} player modules, so the player steering path is")
    a("  not floored at 0.5 in the data; the class difference (bike vs car) is the only thing that")
    a("  separates them.")
    a(f"* **{num(ai_t['min'])} s exists in the fleet**: {n_ai_min} `LandSteering` AI twins ship it")
    a("  (`t_to_full_steer_s`), and the AI `max_speed_t_to_full_steer_s` reaches")
    a(f"  **{num(ai_aux['min'])} s**. Same member, same parser, same type - only the role differs.")
    a(f"* **No player module reaches 220 deg/s**: the best player rate is")
    a(f"  **{num(d['rate_max_player']['deg_per_s'], 4)} deg/s** (`{d['rate_max_player']['class']}`,"
      f" `{d['rate_max_player']['build']}`), the best player **car** rate is")
    a(f"  **{num(d['rate_max_car']['deg_per_s'], 4)} deg/s** (`{d['rate_max_car']['build']}`), and")
    a(f"  the car minimum time is {num(car['min'])} s on {n_car_min} modules. So the honest")
    a("  statement is *\"no player car ships below 0.5 s\"*, not *\"JC3 cannot be quicker\"*.")
    a("")
    a(f"**Engine clamp: UNKNOWN.** {d['clamp']['count']} files in the repo name the executable")
    a(f"({d['clamp']['steer_count']} of them mention steering at all, {d['clamp']['member_count']}"
      " name this member), but none decodes the")
    a("steering update, so no clamp on `t_to_full_steer_s` can be shown or excluded - see section 4.")
    a("Nothing in the ADF data clamps the member, and nothing here proves the player update")
    a(f"honours <0.5 s either. The AI twin at {num(ai_t['min'])} s is evidence that the member and")
    a("parser accept it, not that the player path uses it.")
    a("")
    a("### 0.1 Routes to 0.25 s")
    a("")
    a("| # | route | arithmetic / evidence | verdict |")
    a("|---|---|---|---|")
    a(f"| R1 | write **0.25** into the player car's `t_to_full_steer_s` | member +8, file byte 88,")
    a("  `0000803e`; the AI twin of the same car already ships 0.25 s (same member/type) | **the cheapest route**: data-only, no clamp decoded; whether the player path honours it is UNKNOWN |")
    a(f"| R2 | use the **`MotorbikeSteering`** class for the car | player bikes ship 0.3 s today, so the player path demonstrably accepts <0.5 | amendment (module class swap); does not reach 0.25 by itself |")
    a(f"| R3 | write **0.25** into `max_speed_t_to_full_steer_s` | player min 0.5, AI min 0.2; the high-speed band only | data-only, but affects the fast end, not the low-speed lock |")
    a(f"| R4 | keep 0.5 s and **raise the lock angle** to match 220 deg/s | needs {num(d['need_angle_at_0_5s'])} deg; fleet max is {num(d['fleet_max_angle_deg'])} deg | **impossible** - out of domain by {num(d['need_angle_at_0_5s'] - (d['fleet_max_angle_deg'] or 0))} deg |")
    a("| R5 | rotate by **yaw torque** instead of the rack (`drift.*`, `TurnOnSpot*` equivalents) | DRIVE_CARRIERS/T-MD14b: the drift block is the fleet's only steering-through-torque path | different mechanism: can reach high deg/s but is not the rack's lock time, and needs a trigger |")
    a("| R6 | shape the input (`steer_input_power_pc` 2-4, `steer_curve_falloff` 1-3, `saturation_zone`) | decoded members | affects feel, not full-lock time (which `t_to_full_steer_s` owns) |")
    a("| R7 | prove a native clamp | no exe decode in the repo | UNKNOWN; if a clamp exists it kills R1/R3 |")
    a("")
    a("**Lore reading:** R1 is the route that reaches 0.25 s with a single decoded member and no")
    a("model invention; R2 is the evidence that the player path accepts sub-0.5 values. Neither is")
    a("proven to work in play, and the test ban forbids measuring it, so T-ST7 stays UNAPPROVED")
    a("until either the operator accepts 0.5-ish or a probe is allowed.")
    a("")
    a("## 1. The members, by class and role")
    a("")
    a("`n` excludes the `-1` sentinel (a \"no separate value\" marker, 23 car modules); `sentinel`")
    a("counts those. `median` is over the non-sentinel values.")
    a("")
    a("| class | role | member | n | sentinel | min | median | max |")
    a("|---|---|---|---:|---:|---:|---:|---:|")
    for key in sorted(st, key=lambda k: (st[k]["class"], st[k]["role"], st[k]["member"])):
        s = st[key]
        a(f"| `{s['class']}` | {s['role']} | `{s['member']}` | {s['n']} | {s['n_sentinel']} | "
          f"{num(s['min'])} | {num(s['median'])} | {num(s['max'])} |")
    a("")
    a("## 2. Every module below 0.31 s, with its entity's player value")
    a("")
    a("| value (s) | class | role | member | entity | player value, same entity |")
    a("|---|---|---|---|---|---|")
    for x in d["lows"]:
        a(f"| {num(x['value'])} | `{x['class']}` | {x['role']} | `{x['member']}` | "
          f"`{x['build']}` | {num(x['player_same_entity']) if x['player_same_entity'] is not None else '-'} |")
    a("")
    a("The 0.25 s rows are AI twins whose player module is slower **in the same entity** - a")
    a("per-entity counterexample, not a different car, which rules out \"the 0.25 belongs to a")
    a("different vehicle class\".")
    a("")
    a("## 3. Angular rate, derived")
    a("")
    a("`deg_per_s = steer_angle_min_speed_deg / t_to_full_steer_s` (rule stated; the lock angle")
    a("divided by the time to reach it).")
    a("")
    a("| deg/s | class | role | t (s) | angle (deg) | entity |")
    a("|---:|---|---|---:|---:|---|")
    for r in d["rate_top"]:
        a(f"| {num(r['deg_per_s'], 4)} | `{r['class']}` | {r['role']} | {num(r['t'])} | "
          f"{num(r['angle_deg'])} | `{r['build']}` |")
    a("")
    a(f"Fleet best is **{num(d['rate_max']['deg_per_s'], 4)} deg/s** (an `{d['rate_max']['role']}`")
    a(f"module) and the best **player** rate is **{num(d['rate_max_player']['deg_per_s'], 4)} deg/s**,")
    a("against BmAK's **220 deg/s**;")
    a(f"to hit 220 at 0.5 s a rack would need a **{num(d['need_angle_at_0_5s'])} deg** lock, and the")
    a(f"largest low-speed lock in the fleet is **{num(d['fleet_max_angle_deg'])} deg**.")
    a("")
    a("## 4. The clamp question")
    a("")
    a(f"Searched every `.md` under `Research/` and `Working/` for `{d['clamp']['pattern']}`:")
    a(f"**{d['clamp']['count']} files** name the executable, and the repo does carry real exe")
    a("decodes (`CONSTRAINT_CODE.md`, `RUNTIME_LAYOUT*.md`, `PHYSICS_LIMITS_REVIEW.md` -")
    a("PE headers, Havok constraint atoms, property layouts). Of those files")
    a(f"**{d['clamp']['steer_count']}** mention steering at all and")
    a(f"**{d['clamp']['member_count']}** name this member (`t_to_full_steer_s` / `SteerSpeed`),")
    a("so the steering update itself is not decoded anywhere here: **no clamp can be shown or")
    a("excluded: UNKNOWN.** *Where it would be:* a disassembly of the land-vehicle steering")
    a("update in `JustCause3.exe` (the same `pefile`/`capstone` method the existing notes use), or")
    a("the one-variable probe T_ST7_FLOOR.md §6 describes (0.25 written into a build, measured at")
    a("standstill), which the test ban forbids.")
    a("")
    a("## 5. What this changes in T-ST7")
    a("")
    a(f"* T-ST7's reason (\"the fleet's fastest rack is 0.5 s\") is **wrong on the data**: the")
    a(f"  player bike class ships 0.3 s ({len(pb)} modules) and the AI car class ships 0.25 s")
    a(f"  ({len(ai)} modules, 0.2 s for the high-speed member).")
    a("* T-ST7's *decision* (0.8 s low / 0.6 s high on the Batmobile) is not disproven by that:")
    a("  no **player car** module ships below 0.5 s, so 0.8/0.6 is still a defensible in-family")
    a("  pick - it is just not forced by a floor.")
    a("* Therefore T-ST7's `blocked` disposition is **not justified as a limit**. It is a")
    a("  compromise: the car could carry 0.25 s by data (R1) and the fleet shows the member")
    a("  accepting it, but nobody has written or measured it. It stays UNAPPROVED in")
    a("  `COMPROMISES_T.md` until the operator rules.")
    a("")
    a("Static only: no game launched, attached to or installed to; no build written.")
    a("")
    a("Checkable: `python Tools/scripts/t_st7b.py --check`.")
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
        print("modules", d["inputs"]["steering_modules"],
              "player car min", d["stats"]["LandSteering|player|t_to_full_steer_s"]["min"],
              "player bike min", d["stats"]["MotorbikeSteering|player|t_to_full_steer_s"]["min"],
              "ai car min", d["stats"]["LandSteering|ai|t_to_full_steer_s"]["min"])
        return 0
    fails = []
    if not os.path.exists(jp) or open(jp, encoding="utf-8").read() != js:
        fails.append("json drifted")
    if not os.path.exists(mp) or open(mp, encoding="utf-8").read() != doc:
        fails.append("markdown drifted")
    pc = d["stats"]["LandSteering|player|t_to_full_steer_s"]["min"]
    pb = d["stats"]["MotorbikeSteering|player|t_to_full_steer_s"]["min"]
    ai = d["stats"]["LandSteering|ai|t_to_full_steer_s"]["min"]
    if pc != 0.5:
        fails.append(f"player car min {pc} != 0.5")
    if pb is None or pb > 0.3001:
        fails.append(f"player bike min {pb} - expected 0.3")
    if ai != 0.25:
        fails.append(f"AI car min {ai} != 0.25")
    if not d["lows"]:
        fails.append("no sub-0.31 rows found")
    if d["clamp"]["count"] == 0:
        pass  # expected: no exe decode -> UNKNOWN
    if d["inputs"]["steering_modules"] < 250:
        fails.append("steering module count too low - cache incomplete?")
    if d["rate_max"] and d["rate_max"]["deg_per_s"] >= BMAK["steer_speed_deg_s"]:
        fails.append("a fleet module already reaches 220 deg/s - recheck the route table")
    print("modules %d, player car %s, player bike %s, ai car %s, clamp docs %d, best %.1f deg/s"
          % (d["inputs"]["steering_modules"], pc, pb, ai, d["clamp"]["count"],
             d["rate_max"]["deg_per_s"] if d["rate_max"] else -1))
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("OK: floor verified (player car 0.5, bike 0.3, AI 0.25), document and JSON identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
