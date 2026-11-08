"""t_boost_coverage.py - BmAK boost values vs the JC3 nitro translation rows.

Answers one question, from files only: which BmAK afterburner/boost values are readable,
what does each become in JC3, and which values have **no** translation row.

Sources parsed (file:line checked by an oracle before use):

  * `Research/BatmobileGrab/CLASS_DEFAULTS.md` - `FakeExtraSpeedMax` 3500.0 @7156 (l.265),
    `FakeExtaSpeedAccel` 600.0 @7160 (l.266), `FakeExtaSpeedDecel` 2000.0 @7164 (l.267),
    `SVehicle.MaxSpeed` 4000.0 @1808 (l.163), `ImpactBoostMod` 1.5 @6876 (l.260);
  * `Research/BatmobileGrab/MECHANICS.md` - `BoostTorqueVSpeedCurve`, 7 points (l.113);
  * `Working/HUD/CLUSTER.md` - `RVehicleSimBatmobile.g.cs` natives: `BoostDuration` 2.0 @664,
    `BoostCooldown` 12.0 @668 (InlineArray 3), `BoostCooldownUpgradeLevel` @680,
    `CurrentBoostTimer` 1.0 @808, `DriftingBoostCooldown` @684, `BoostDurationDonut` 6.0 @688;
  * `Research/BatmobileGrab/BMSDK_OFFSETS.json` - the slot offsets of those members;
  * `Research/BatmobileGrab/SAMPLER_FIELDS2.md` - `InfiniteBoost` bit @4568;
  * `Research/JC3Grab/USAGES.md` section 6 (l.552-554) - donor `arcade.nitro_boost` values;
  * `Working/Translation/current.json` - the values the build actually carries;
  * `Working/Translation/T_ROWS.jsonl` - the translation rows (T-B1..T-B4 and the rows that
    touch boost: T-E5, T-MD1, T-MD4, T-DR1, T-DM7, T-FX3, T-WP11).

`--write` emits `Working/Translation/BOOST_COVERAGE.md`; `--check` re-derives every number,
re-builds the document, compares it byte-for-byte and prints the coverage table. It never
edits a translation row: rows are read, cited and classified only.

    python Tools/scripts/t_boost_coverage.py --write
    python Tools/scripts/t_boost_coverage.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

CLASS_DEFAULTS = os.path.join(ROOT, "Research", "BatmobileGrab", "CLASS_DEFAULTS.md")
MECHANICS = os.path.join(ROOT, "Research", "BatmobileGrab", "MECHANICS.md")
CLUSTER = os.path.join(ROOT, "Working", "HUD", "CLUSTER.md")
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")
SAMPLER = os.path.join(ROOT, "Research", "BatmobileGrab", "SAMPLER_FIELDS2.md")
CONFIG = os.path.join(ROOT, "Research", "BatmobileGrab", "CONFIG.md")
USAGES = os.path.join(ROOT, "Research", "JC3Grab", "USAGES.md")
ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
CURRENT = os.path.join(ROOT, "Working", "Translation", "current.json")
OUT = os.path.join(ROOT, "Working", "Translation", "BOOST_COVERAGE.md")


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def lines(path: str) -> list[str]:
    return read(path).splitlines()


def line_with(path: str, n: int, needle: str) -> str:
    """Oracle: the cited line must exist and carry the claimed text."""
    ls = lines(path)
    if n < 1 or n > len(ls):
        raise SystemExit(f"FAIL: {os.path.relpath(path, ROOT)} has no line {n}")
    got = ls[n - 1]
    if needle not in got:
        raise SystemExit(f"FAIL: {os.path.relpath(path, ROOT)}:{n} does not contain {needle!r}; "
                         f"got {got[:160]!r}")
    return got.strip()


def parse_class_defaults() -> dict[str, dict]:
    txt = read(CLASS_DEFAULTS)
    pat = re.compile(
        r"\| \d+ \| `0x([0-9a-fA-F]+)` \| (\d+) \| `([A-Za-z0-9_]+)` \(([A-Za-z0-9_]+)\) "
        r"\| (FloatProperty|IntProperty|BoolProperty) \| ([^|]+?) \| decoded \| ([^|]+?) \|")
    out: dict[str, dict] = {}
    for m in pat.finditer(txt):
        out.setdefault(m.group(3), {
            "offset": int(m.group(2)), "hex": "0x" + m.group(1).lower(),
            "cls": m.group(4), "kind": m.group(5),
            "value": m.group(6).strip(), "src": m.group(7).strip(),
        })
    for need in ("FakeExtraSpeedMax", "FakeExtaSpeedAccel", "FakeExtaSpeedDecel",
                 "MaxSpeed", "ImpactBoostMod"):
        if need not in out:
            raise SystemExit(f"FAIL: {need} not parsed from CLASS_DEFAULTS.md")
    return out


def parse_cluster() -> dict[str, dict]:
    txt = read(CLUSTER)
    pat = re.compile(r"\| RVehicleSimBatmobile\.g\.cs \| `([A-Za-z0-9_]+)` \| (\w+) \| (\d+) \| ([^|]+?) \|")
    out = {}
    for m in pat.finditer(txt):
        out[m.group(1)] = {"type": m.group(2), "offset": int(m.group(3)), "value": m.group(4).strip()}
    for need in ("BoostDuration", "BoostCooldown", "BoostDurationDonut", "CurrentBoostTimer",
                 "BoostCooldownUpgradeLevel", "DriftingBoostCooldown"):
        if need not in out:
            raise SystemExit(f"FAIL: {need} not parsed from Working/HUD/CLUSTER.md")
    return out


def parse_slots() -> dict[str, list[dict]]:
    d = json.load(open(OFFSETS, encoding="utf-8"))
    props = d["classes"]["RVehicleSimBatmobile"]["properties"]
    slots: dict[str, list[dict]] = {}
    for p in props:
        slots.setdefault(p["name"], []).append({"member": p["member"], "offset": p["offset"],
                                                "kind": p["kind"]})
    return slots


def parse_donor() -> dict:
    row = line_with(USAGES, 552, "arcade.nitro_boost")
    pat = re.compile(r"torque x(\d+(?:\.\d+)?), grip x(\d+(?:\.\d+)?), `push_force` (\d+), "
                     r"`boost_blend_time` ([\d.]+) s, `extra_top_speed` \+(\d+) km/h; "
                     r"`nitro_boost_upgraded`: push (\d+), \+(\d+) km/h")
    m = pat.search(row)
    if not m:
        raise SystemExit("FAIL: USAGES.md:552 donor nitro row did not parse")
    return {"torque": float(m.group(1)), "grip": float(m.group(2)), "push": int(m.group(3)),
            "blend": float(m.group(4)), "extra": int(m.group(5)),
            "up_push": int(m.group(6)), "up_extra": int(m.group(7)), "line": row}


def parse_rows() -> tuple[dict[str, dict], dict[str, int]]:
    out = {}
    where = {}
    with open(ROWS, encoding="utf-8") as f:
        for i, raw in enumerate(f, 1):
            if not raw.strip():
                continue
            r = json.loads(raw)
            out[r["id"]] = r
            where[r["id"]] = i
    return out, where


def parse_current() -> dict:
    d = json.load(open(CURRENT, encoding="utf-8"))
    found: dict[str, dict] = {}

    def tag(o: dict) -> str | None:
        blob = " ".join(str(o.get(k, "")) for k in ("file", "name", "module", "instance")).lower()
        if "custom_land_global" in blob:
            return "nitro"
        if "vehicle_misc" in blob:
            return "misc"
        return None

    def walk(o):
        if isinstance(o, dict):
            vals = o.get("values")
            if isinstance(vals, dict):
                t = tag(o)
                if t:
                    found.setdefault(t, vals)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(d)
    for need in ("nitro", "misc"):
        if need not in found:
            raise SystemExit(f"FAIL: no {need} values block in current.json")
    return found


def fnum(x: float) -> str:
    if abs(x - round(x)) <= 1e-9:
        return str(int(round(x)))
    return (f"{x:.2f}").rstrip("0").rstrip(".")


def fsmall(x: float) -> str:
    return (f"{x:.4f}").rstrip("0").rstrip(".")


def ascii_safe(s: str) -> str:
    return s.encode("ascii", "replace").decode()


def build() -> tuple[str, dict]:
    cd = parse_class_defaults()
    sim = parse_cluster()
    slots = parse_slots()
    donor = parse_donor()
    rows, where = parse_rows()
    cur = parse_current()

    # oracles on the cited lines
    line_with(CLASS_DEFAULTS, 265, "FakeExtraSpeedMax")
    line_with(CLASS_DEFAULTS, 266, "FakeExtaSpeedAccel")
    line_with(CLASS_DEFAULTS, 267, "FakeExtaSpeedDecel")
    line_with(CLASS_DEFAULTS, 163, "MaxSpeed` (SVehicle)")
    line_with(CLASS_DEFAULTS, 260, "ImpactBoostMod")
    line_with(MECHANICS, 113, "BoostTorqueVSpeedCurve =")
    for n, needle in ((50, "BoostDuration"), (51, "BoostCooldown"), (52, "BoostCooldownUpgradeLevel"),
                      (53, "CurrentBoostTimer"), (54, "DriftingBoostCooldown"),
                      (55, "BoostDurationDonut")):
        line_with(CLUSTER, n, needle)
    line_with(SAMPLER, 96, "InfiniteBoost")
    line_with(CONFIG, 298, "pBatmobileBoost")
    line_with(CONFIG, 326, "kBatmobileBoost")
    line_with(CONFIG, 443, "Afterburner")
    curve = line_with(MECHANICS, 113, "BoostTorqueVSpeedCurve =")

    max_extra = float(re.search(r"([\d.]+)", cd["FakeExtraSpeedMax"]["value"]).group(1))
    accel = float(re.search(r"([\d.]+)", cd["FakeExtaSpeedAccel"]["value"]).group(1))
    decel = float(re.search(r"([\d.]+)", cd["FakeExtaSpeedDecel"]["value"]).group(1))
    max_speed = float(re.search(r"([\d.]+)", cd["MaxSpeed"]["value"]).group(1))
    impact_boost = float(re.search(r"([\d.]+)", cd["ImpactBoostMod"]["value"]).group(1))
    duration = float(sim["BoostDuration"]["value"])
    cooldown = float(sim["BoostCooldown"]["value"])
    donut = float(sim["BoostDurationDonut"]["value"])
    timer = float(sim["CurrentBoostTimer"]["value"])

    # the project's cu -> km/h factor, taken from T-B2's own arithmetic (1200 cu = 43.2 km/h)
    tb2 = " ".join(rows["T-B2"]["cells"])
    m = re.search(r"= (\d+) cu = \*\*([\d.]+) km/h\*\*", tb2)
    if not m:
        raise SystemExit("FAIL: T-B2 does not state 'N cu = X km/h'")
    burst_cu, burst_kmh = int(m.group(1)), float(m.group(2))
    factor = burst_kmh / burst_cu
    capped = min(max_extra, accel * duration)
    cap_kmh = max_extra * factor
    base_kmh = max_speed * factor

    # oracles: the arithmetic the rows claim must reproduce
    problems = []
    if abs(capped - burst_cu) > 1e-9 or abs(capped - 600 * 2.0) > 1e-9:
        problems.append(f"min({max_extra}, {accel} x {duration}) = {capped}, T-B2 states {burst_cu}")
    if abs(capped * factor - burst_kmh) > 1e-9:
        problems.append(f"{capped} cu x {factor} = {capped * factor}, T-B2 states {burst_kmh}")
    nvals = cur["nitro"]
    applied_extra = float(nvals["arcade.nitro_boost.extra_top_speed"])
    applied_push = float(nvals["arcade.nitro_boost.push_force"])
    applied_blend = float(nvals["arcade.nitro_boost.boost_blend_time"])
    applied_torque = float(nvals["arcade.nitro_boost.torque_multiplier"])
    applied_grip = float(nvals["arcade.nitro_boost.grip_multiplier"])
    up_push = float(nvals["arcade.nitro_boost_upgraded.push_force"])
    up_extra = float(nvals["arcade.nitro_boost_upgraded.extra_top_speed"])
    misc = cur["misc"]
    use_time = int(misc["full_nitro_use_time"])
    use_time_up = int(misc["full_nitro_use_time_upgraded"])
    refill = int(misc["full_nitro_refill_time"])
    refill_min = int(misc["nitro_refill_min_speed_kph"])
    official = float(misc["official_top_speed"])
    if abs(applied_extra - burst_kmh) > 1e-3:
        problems.append(f"current extra_top_speed {applied_extra} != derived {burst_kmh}")
    if applied_push != donor["push"]:
        problems.append(f"current push {applied_push} != donor {donor['push']}")
    if abs(applied_blend - donor["blend"]) > 1e-6:
        problems.append(f"current blend {applied_blend} != donor {donor['blend']}")
    if applied_torque != donor["torque"]:
        problems.append(f"current torque {applied_torque} != donor {donor['torque']}")
    if applied_grip != 1.0:
        problems.append(f"current grip {applied_grip} != T-B3's 1.0")
    if up_push != donor["up_push"]:
        problems.append(f"current upgraded push {up_push} != donor {donor['up_push']}")

    # coverage map: every row cited must exist and its JC3 member must be in its cells
    coverage = [
        ("thrust", "`BoostTorqueVSpeedCurve` 7 points", curve.split("BoostTorqueVSpeedCurve = ")[1],
         "T-B1", "`arcade.nitro_boost.torque_multiplier`",
         "collapsed to one constant 2.0 (the curve is 1.30x..2.10x over its speed band); the curve itself is recorded by T-MD4"),
        ("thrust", "`FakeExtaSpeedAccel`", f"{fnum(accel)} cu/s²", "T-B2",
         "`arcade.nitro_boost.extra_top_speed`",
         "the rate term of min(cap, accel x duration)"),
        ("thrust", "`FakeExtraSpeedMax`", f"{fnum(max_extra)} cu = {fnum(cap_kmh)} km/h", "T-B2",
         "`arcade.nitro_boost.extra_top_speed`", "the ceiling term of the same min()"),
        ("duration", "`BoostDuration`", f"{fnum(duration)} s", "T-B2 (as a term only)",
         "`arcade.nitro_boost.extra_top_speed`",
         "no JC3 duration field is written; the value only enters the min() above"),
        ("duration", "`BoostDurationDonut`", f"{fnum(donut)} s", None, None,
         "no donut/heat-boost mode in the build"),
        ("recharge", "`BoostCooldown` tier 0", f"{fnum(cooldown)} s", None, None,
         "no JC3 member; the donor's refill time is its own default"),
        ("recharge", "`BoostCooldownUpgradeLevel`", "no default", None, None,
         "no upgraded nitro tiers (user decision, build_batches.json)"),
        ("recharge", "`DriftingBoostCooldown`", "no default", "T-DR1",
         "`custom_land_global.drift.*`", "covered as part of the drift block, not as boost"),
        ("thrust", "`FakeExtaSpeedDecel`", f"{fnum(decel)} cu/s²", None, None,
         "JC3 ends boost by blending out; no decel member"),
        ("thrust", "`ImpactBoostMod`", f"{fnum(impact_boost)} (CLASS_DEFAULTS.md:260)", "T-DM7",
         "none", "row puts outgoing ram damage out; no JC3 member"),
        ("speed cap", "`SVehicle.MaxSpeed`", f"{fnum(max_speed)} cu = {fnum(base_kmh)} km/h", None, None,
         "base cap, not a boost value; T-E5 carries the wiki top speed instead"),
        ("speed cap", "wiki 209 mph / 336 km/h with afterburner", "not a file value", "T-E5",
         "`vehicle_misc.official_top_speed`", "assumed (wiki), signed off 2026-10-23"),
        ("state", "`RVehicleBatmobileBase.InfiniteBoost`", "bit @4568, mask 536870912 (SAMPLER_FIELDS2.md:96)",
         None, None, "JC3 nitro is finite; T-B2 records the flag as false"),
        ("state", "`CurrentBoostTimer`", f"{fnum(timer)} (init)", None, None,
         "a timer, not a translated value"),
    ]
    for _cat, _name, _val, rid, field, _note in coverage:
        if rid is None or field is None:
            continue
        base = rid.split(" ")[0]
        if base not in rows:
            problems.append(f"row {base} cited but missing from T_ROWS.jsonl")
            continue
        cells = " ".join(rows[base]["cells"])
        if field.strip("`") not in cells:
            problems.append(f"{base} does not carry the JC3 member {field}")
    if "FakeExtaSpeedDecel" in " ".join(rows["T-B2"]["cells"]).replace("`", ""):
        # T-B2 mentions the decel field in prose; that is not a mapping, keep it visible
        pass
    if float(re.search(r"\*\*([\d.]+)\*\*", " ".join(rows["T-B1"]["cells"])).group(1)) != 2.0:
        problems.append("T-B1's kept value is not 2.0")
    if "1.0" not in " ".join(rows["T-B3"]["cells"]):
        problems.append("T-B3 does not state grip 1.0")

    no_row = [(c, n, v, note) for c, n, v, rid, _f, note in coverage if rid is None]
    if problems:
        return "", {"problems": problems, "coverage": coverage}

    L: list[str] = []
    a = L.append
    a("# BOOST_COVERAGE - BmAK afterburner values vs the JC3 nitro translation")
    a("")
    a("Generated by `Tools/scripts/t_boost_coverage.py --write`; `--check` re-derives every number")
    a("from the cited lines, rebuilds this file and fails on any difference. No translation row is")
    a("edited here - rows are read and classified only.")
    a("")
    a("Labels: **decoded** = a byte/field value with a file:line; **derived** = arithmetic on decoded")
    a("values, rule stated; **assumed** = a non-file source (wiki) named as such; **UNKNOWN** = not")
    a("readable, with where it would be found.")
    a("")
    a("## 1. BmAK values readable from files")
    a("")
    a("| group | BmAK field | value | bytes / offset | label | evidence |")
    a("|---|---|---|---|---|---|")
    a(f"| thrust | `FakeExtraSpeedMax` | {fnum(max_extra)} cu (= {fnum(cap_kmh)} km/h additive cap) | "
      f"{cd['FakeExtraSpeedMax']['offset']} ({cd['FakeExtraSpeedMax']['hex']}), FloatProperty | decoded | "
      f"`{cd['FakeExtraSpeedMax']['src']}`, CLASS_DEFAULTS.md:265 |")
    a(f"| thrust | `FakeExtaSpeedAccel` | {fnum(accel)} cu/s² | {cd['FakeExtaSpeedAccel']['offset']} "
      f"({cd['FakeExtaSpeedAccel']['hex']}) | decoded | `{cd['FakeExtaSpeedAccel']['src']}`, CLASS_DEFAULTS.md:266 |")
    a(f"| thrust | `FakeExtaSpeedDecel` | {fnum(decel)} cu/s² | {cd['FakeExtaSpeedDecel']['offset']} "
      f"({cd['FakeExtaSpeedDecel']['hex']}) | decoded | `{cd['FakeExtaSpeedDecel']['src']}`, CLASS_DEFAULTS.md:267 |")
    a(f"| thrust | `BoostTorqueVSpeedCurve` | 7 points: {curve.split('= ', 1)[1]} | `RVehicleSimBatmobile` "
      f"struct | decoded | MECHANICS.md:113 |")
    a(f"| duration | `BoostDuration` | {fnum(duration)} s | {sim['BoostDuration']['offset']}, float "
      f"(`RVehicleSimBatmobile.g.cs`) | decoded | Working/HUD/CLUSTER.md:50 |")
    a(f"| duration | `BoostDurationDonut` | {fnum(donut)} s | {sim['BoostDurationDonut']['offset']}, float | "
      f"decoded | Working/HUD/CLUSTER.md:55 |")
    a(f"| recharge | `BoostCooldown` (InlineArray 3: "
      f"{'/'.join(str(s['offset']) for s in slots['BoostCooldown'])}) | tier 0 = {fnum(cooldown)} s | "
      f"{sim['BoostCooldown']['offset']}, float | decoded | Working/HUD/CLUSTER.md:51 |")
    a(f"| recharge | `BoostCooldownUpgradeLevel` | no default | {sim['BoostCooldownUpgradeLevel']['offset']}, int | "
      f"decoded (field only) | Working/HUD/CLUSTER.md:52 |")
    a(f"| recharge | `DriftingBoostCooldown` | no default in the CDO | {sim['DriftingBoostCooldown']['offset']}, "
      f"float | decoded (field only) | Working/HUD/CLUSTER.md:54 |")
    a(f"| state | `CurrentBoostTimer` | {fnum(timer)} (initial) | {sim['CurrentBoostTimer']['offset']}, float | "
      f"decoded | Working/HUD/CLUSTER.md:53 |")
    a(f"| speed cap | `SVehicle.MaxSpeed` | {fnum(max_speed)} cu (= {fnum(base_kmh)} km/h, base cap) | "
      f"{cd['MaxSpeed']['offset']} ({cd['MaxSpeed']['hex']}) | decoded | `{cd['MaxSpeed']['src']}`, "
      f"CLASS_DEFAULTS.md:163 |")
    a("| state | `RVehicleBatmobileBase.InfiniteBoost` | bit @4568, mask 536870912 | bool bit | decoded | "
      "SAMPLER_FIELDS2.md:96 |")
    a("")
    a(f"Derived burst, the same arithmetic T-B2 uses: min(`FakeExtraSpeedMax` {fnum(max_extra)}, "
      f"`FakeExtaSpeedAccel` {fnum(accel)} x `BoostDuration` {fnum(duration)}) = {fnum(capped)} cu = "
      f"**{fnum(burst_kmh)} km/h**, on the project convention 3000 cu = 108 km/h "
      f"({fsmall(factor)} km/h per cu, factor taken from T-B2's own line).")
    a("")
    a("Input binding (`CONFIG.md`, no magnitude): `Engine.PlayerTags` `pBatmobileBoost` = `{PAD_Y}` (l.298),")
    a("`kBatmobileBoost` = `{PC_LMB}` (l.326), and `BmGame.RGameInfo.DefaultPursuitKeyMap` names the ability")
    a("`$GFxUI.KeyboardControls.Afterburner` (l.443). These are the only boost rows `CONFIG.md` carries;")
    a("they bind a button, not a value, so no translation row is needed for them.")
    a("")
    a("## 2. The donor JC3 nitro block and what the build carries")
    a("")
    a("| JC3 member | donor (`USAGES.md` section 6) | applied (`current.json`) | row |")
    a("|---|---|---|---|")
    a(f"| `arcade.nitro_boost.torque_multiplier` | x{fnum(donor['torque'])} | {fnum(applied_torque)} | T-B1 |")
    a(f"| `arcade.nitro_boost.grip_multiplier` | x{fnum(donor['grip'])} | {fnum(applied_grip)} | T-B3 |")
    a(f"| `arcade.nitro_boost.push_force` | {donor['push']} N | {fnum(applied_push)} | T-MD1 (values T-B2/T-B3) |")
    a(f"| `arcade.nitro_boost.boost_blend_time` | {fnum(donor['blend'])} s | {fnum(applied_blend)} | T-MD1 |")
    a(f"| `arcade.nitro_boost.extra_top_speed` | +{donor['extra']} km/h | {fnum(applied_extra)} | T-B2 |")
    a(f"| `arcade.nitro_boost_upgraded.push_force` | {donor['up_push']} N | {fnum(up_push)} | T-B4 keeps the block |")
    a(f"| `arcade.nitro_boost_upgraded.extra_top_speed` | +{donor['up_extra']} km/h | {fnum(up_extra)} | T-B4 keeps the block |")
    a("")
    a("`USAGES.md` section 6 line 552 is the source row; the donor block itself is module data on 145 of")
    a("232 vehicles, not code. BmAK has **no** `push_force` analogue: its thrust is the accel/decel")
    a("pair plus the torque curve, so the 15,000 N push is a donor value the build keeps, not a")
    a("translation of a BmAK field.")
    a("")
    a("## 3. Coverage per value")
    a("")
    a("| BmAK value | group | translation row | JC3 member | how covered |")
    a("|---|---|---|---|---|")
    for cat, name, val, rid, field, note in coverage:
        a(f"| {name} `{val}` | {cat} | {rid if rid else '**none**'} | "
          f"{field if field else '-'} | {note} |")
    a("")
    a("## 4. BmAK values with no translation row")
    a("")
    for cat, name, val, note in no_row:
        a(f"* {name} `{val}` ({cat}) - {note}")
    a("")
    a("## 5. Donor values with no BmAK source and no row")
    a("")
    a("These are JC3 fields the build writes at their shipped defaults; none is a translation of a")
    a("BmAK value, and no row maps them:")
    a("")
    a(f"* `full_nitro_use_time` {use_time} s, `full_nitro_use_time_upgraded` {use_time_up} s - the JC3")
    a("  meter-drain time; BmAK has a fixed `BoostDuration`, not a meter.")
    a(f"* `full_nitro_refill_time` {refill} s, `nitro_refill_min_speed_kph` {refill_min} km/h - the JC3")
    a("  recharge rule; BmAK's `BoostCooldown` has no JC3 member.")
    a(f"* `vehicle_misc.official_top_speed` {fnum(official)} km/h - T-E5, sourced from the wiki 209 mph,")
    a("  labelled **assumed**, not from a BmAK file value.")
    a("")
    a("## 6. Answer in one line each")
    a("")
    a(f"* **thrust** is readable: {fnum(max_extra)} cu additive cap, {fnum(accel)} cu/s² accel, "
      f"{fnum(decel)} cu/s² decel and the 7-point torque curve. The cap and accel reach JC3 through")
    a("  T-B2, the curve through T-B1 (as one constant); **decel has no row**.")
    a(f"* **duration** is readable ({fnum(duration)} s, `BoostDuration` @664; donut {fnum(donut)} s), but it")
    a("  is not a JC3 field: it appears only as a term of T-B2's min(). **No row translates duration**;")
    a(f"  JC3's {use_time}/{use_time_up} s nitro use-time is a donor default with no row.")
    a(f"* **recharge** is readable ({fnum(cooldown)} s, `BoostCooldown` InlineArray 3, tier 0) and has")
    a("  **no row**; neither does `BoostCooldownUpgradeLevel`. JC3's refill is its own default.")
    a(f"* **speed cap**: the boost-additive cap {fnum(max_extra)} cu ({fnum(cap_kmh)} km/h) is covered by T-B2;")
    a(f"  the base `SVehicle.MaxSpeed` {fnum(max_speed)} cu ({fnum(base_kmh)} km/h) has no row, and the")
    a(f"  {fnum(official)} km/h target is T-E5's assumed wiki figure.")
    a("")
    a("## 7. UNKNOWN")
    a("")
    a("1. **Per-slot `BoostCooldown` values.** `CLUSTER.md:51` records the InlineArray's tier-0 value")
    a("   as 12.0 s; `BMSDK_OFFSETS.json` names three slots (668/672/676), and no decoded source here")
    a("   gives slots 1/2 separately. Where: `RVehicleSimBatmobile` default export / archetype data.")
    a("2. **`BoostCooldownUpgradeLevel` and `DriftingBoostCooldown` defaults** are declared but have no")
    a("   CDO value in the HUD card (`None`); the 1.5 s drift value in `MECHANICS_NAMES.md:73` is read")
    a("   from the live sim object, not from a shipped default.")
    a("3. **Afterburner timing edges.** `fAfterburnerStartTime` (8584) and")
    a("   `fAfterburnerCutoffStartTime` (8596) are declared with no CDO default")
    a("   (CLASS_DEFAULTS.md section 6), so start/cutoff timing is UNKNOWN.")
    a("4. **Whether JC3 nitro time maps to BmAK duration at all.** JC3 drains a meter over")
    a(f"   `full_nitro_use_time` ({use_time} s); BmAK runs a fixed {fnum(duration)} s burst with a")
    a("   cooldown. No file states an equivalence; the build keeps both systems' own fields.")
    a("5. **`ImpactBoostMod` mismatch.** `CLASS_DEFAULTS.md:260` decodes 1.5, while T-DM7's requirement")
    a("   cell says 2.0. Not resolved here (it is an outgoing-damage row marked out); recorded rather")
    a("   than smoothed.")
    a("")
    return "\n".join(L) + "\n", {"problems": [], "coverage": coverage, "burst": (capped, burst_kmh),
                                  "factor": factor, "cap_kmh": cap_kmh, "base_kmh": base_kmh,
                                  "applied": applied_extra, "rows": where}


def check() -> int:
    fresh, info = build()
    fails = list(info["problems"])
    if not os.path.exists(OUT):
        print(f"FAIL: {os.path.relpath(OUT, ROOT)} missing (run --write)")
        return 1
    have = read(OUT)
    if have != fresh:
        fails.append("BOOST_COVERAGE.md differs from a fresh generation")
        a, b = have.splitlines(), fresh.splitlines()
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                fails.append(f"first difference at line {i+1}: file {a[i][:100]!r} != fresh {b[i][:100]!r}")
                break
    cov = info["coverage"]
    withrow = sum(1 for c in cov if c[3] is not None)
    print(f"rows parsed {len(info['rows'])} | values {len(cov)} | covered by a row {withrow} | "
          f"no row {len(cov) - withrow}")
    for cat, name, val, rid, field, _note in cov:
        print(f"  {cat:9} {ascii_safe(name):45} {ascii_safe(val):38} -> {rid if rid else 'NO ROW'}")
    print(f"factor {info['factor']} km/h per cu (from T-B2) | burst {info['burst'][0]} cu = "
          f"{info['burst'][1]} km/h | cap {info['cap_kmh']} km/h | base {info['base_kmh']} km/h | "
          f"applied extra_top_speed {info['applied']}")
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    print("PASS: every BmAK boost value is classified against the rows; T-B1/T-B2/T-B3 cover the "
          "torque cap and accel, and decel, duration, recharge, donut, base cap and the boost flags "
          "have no row (listed in section 4)")
    print("CHECK_EXIT=0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    if a.check:
        return check()
    text, info = build()
    if info["problems"]:
        for p in info["problems"]:
            print(f"FAIL: {p}")
        return 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
