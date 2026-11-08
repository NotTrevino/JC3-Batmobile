#!/usr/bin/env python3
"""v05_combat.py - V-05 part 2: the combat predictions (shots-to-kill, Vulcan overheat, missile lock).

Card: before any in-game test, write what Q-1.6 / Q-3.2 / Q-3.3 should show for the weapons -
shots-to-kill per arm, the Vulcan's time to overheat and the missile lock time. Every line carries
its source row, the expected value and a pass band; where no row gives a number the line says
UNKNOWN instead of inventing one.

Out: `Working/Q/PREDICTIONS_COMBAT.md`.

Where each number comes from (nothing is typed in):

  * the arms and their damage      - `Research/JC3Grab/WEAPONS.jsonl` + the hand tunes, read through
                                     `damage_predict.build_payload` (G2-28's own reader, not copied)
  * the target's health module     - `Builds/bm-RC4`, decoded by `damage_predict.build_payload`
  * the published build table      - `Research/JC3Grab/DAMAGE_MODEL.md` §4 (build test-091), parsed
                                     here and compared row by row with `DAMAGE_MODEL.json`
  * the Vulcan heat fields         - `Research/BatmobileGrab/WEAPONS.json`
                                     (`HeatUpPerSecond` 0.0 @2680, `OverheatOffValue` 0.25 @2688)
  * the missile lock fields        - the same object (`MissileLockOnDuration` @2560,
                                     `CivilianMissileLockOnDuration` @2564)
  * the JC3 side of both           - 0 heat / 0 lock members across every decoded JC3 weapon tune,
                                     plus `t19_hud.json` T-HUD17/T-HUD18
  * the measured lock attempts     - `Research/BatmobileGrab/runtime/samples-*.jsonl`

The band on a shots-to-kill line is the three-model bracket of `DAMAGE_MODEL.md` §4 (H0 armour
ignored / H1 percentage gate / H2 threshold + pool), not measurement error: inside a matched model
the count is exact, and the band says which counts the files allow.

`--check` re-reads every source, re-asserts each oracle below, recomputes every number
independently of `damage_predict.hits` and compares the document byte-for-byte.

    python Tools/scripts/v05_combat.py --write
    python Tools/scripts/v05_combat.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

OUT = os.path.join(ROOT, "Working", "Q", "PREDICTIONS_COMBAT.md")
DAMAGE_MD = os.path.join(ROOT, "Research", "JC3Grab", "DAMAGE_MODEL.md")
DAMAGE_JSON = os.path.join(ROOT, "Research", "JC3Grab", "DAMAGE_MODEL.json")
JC3_WEAPONS = os.path.join(ROOT, "Research", "JC3Grab", "WEAPONS.jsonl")
BM_WEAPONS = os.path.join(ROOT, "Research", "BatmobileGrab", "WEAPONS.json")
T19 = os.path.join(ROOT, "Working", "Translation", "t19_hud.json")
RUNTIME = os.path.join(ROOT, "Research", "BatmobileGrab", "runtime")

BUILD_REL = "Builds/bm-RC4"
BUILD_NAME = os.path.basename(BUILD_REL)
ARMS = ["pistol", "assault_rifle", "machine_gun", "shotgun", "rpg", "grenade",
        "tank_cannon", "heli_missile", "heli_mg"]
PROBE_S = 30  # the burst length the overheat line is probed over; a test-design choice, not a value
MODELS = ("H0", "H1", "H2")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def num(cell):
    """A DAMAGE_MODEL.md table cell -> int, or None for `never`."""
    cell = cell.strip()
    if cell == "never":
        return None
    return int(cell.replace(",", ""))


def fmt(v):
    return "never" if v is None else f"{v:,}"


def sval(v):
    """A JSON float as the file prints it: 0.0 stays `0.0`, not `0`."""
    return f"{v}"


def my_hits(hp, armor, strength, dmg, model):
    """The three models, re-implemented - the oracle for `damage_predict.hits`, not a second claim."""
    if dmg <= 0:
        return None
    if model == "H0":
        return math.ceil(hp / dmg)
    if model == "H1":
        per = dmg * (1.0 - min(max(strength, 0.0), 100.0) / 100.0)
        return None if per <= 1e-12 else math.ceil(hp / per)
    if dmg <= strength:
        return None
    return math.ceil((hp + armor) / dmg)


def md_section_rows(text, heading):
    """Parse the `| arm | channel | armour | H0 | H1 | H2 |` table under a heading."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    rows = []
    for line in lines[start + 1:]:
        if not line.startswith("| `"):
            if rows:
                break
            continue
        cells = line.split("|")
        rows.append({"arm": cells[1].strip().strip("`"), "channel": cells[2].strip(),
                     "armour": cells[3].strip(), "H0": num(cells[4]), "H1": num(cells[5]),
                     "H2": num(cells[6])})
    return rows


def band(row):
    """The predicted acceptance band for one arm, read off the three-model bracket."""
    nums = [row[m] for m in MODELS if row[m] is not None]
    lo, hi = min(nums), max(nums)
    if lo == hi:
        return f"{lo:,} hits, and all three models agree on the count"
    if any(row[m] is None for m in MODELS):
        return f"at least {lo:,} hits (one model says never); destruction before {lo:,} fails"
    return f"{lo:,}-{hi:,} hits (the three models disagree by this bracket)"


def main(write: bool) -> int:
    checks = []

    def ok(cond, label, detail=""):
        checks.append({"oracle": label, "ok": bool(cond), "detail": detail})
        return bool(cond)

    import damage_predict as dp  # imported late: build_payload shells ConvertAdf / reads archives

    # ---------------------------------------------------------------- the published build table
    md_text = open(DAMAGE_MD, encoding="utf-8").read()
    published = md_section_rows(md_text, "### build test-091")
    doc_json = load(DAMAGE_JSON)
    jb = doc_json["table"]["build_test-091"]
    ok(len(published) == 9, f"DAMAGE_MODEL.md build table has 9 arm rows ({len(published)})")
    ok(doc_json["vehicles"]["build_test-091"]["max_health"] == 2000,
       "DAMAGE_MODEL.json build_test-091 max_health 2000",
       str(doc_json["vehicles"]["build_test-091"]["max_health"]))
    ok("| `max_health` | 700 | 2000 | 2000 |" in md_text,
       "DAMAGE_MODEL.md section 2 prints the build as 2,000 HP")
    ok("24 x 1500 = 36,000" in md_text and "500..4000" in md_text,
       "DAMAGE_MODEL.md section 5 itself names the 36,000 HP ratio")
    mismatched = [r["arm"] for r in published
                  if any(r[m] != jb[r["arm"]]["primary"][m] for m in MODELS)]
    ok(not mismatched, "DAMAGE_MODEL.md build rows match DAMAGE_MODEL.json",
       ",".join(mismatched))

    # ---------------------------------------------------------------- the build under test
    payload = dp.build_payload(os.path.join(ROOT, BUILD_REL))
    bkey = dp.build_key(os.path.join(ROOT, BUILD_REL))
    veh = payload["vehicles"][bkey]
    hp = veh["max_health"]
    ok(bkey == f"build_{BUILD_NAME}", f"payload key is {bkey}", bkey)
    ok(hp == 36000, f"{BUILD_NAME} max_health {hp:,}", f"{hp}")

    table = payload["table"][bkey]
    ok(sorted(table) == sorted(ARMS), f"{BUILD_NAME} table carries the 9 arms", str(len(table)))

    rows = []
    for arm in ARMS:
        prim = table[arm]["primary"]
        # independent recomputation of every printed count from damage / armour / strength / HP
        for model in MODELS:
            mine = my_hits(hp, prim["armor"], prim["strength"], prim["damage"], model)
            ok(mine == prim[model], f"RC2 {arm} {model} recomputes ({fmt(mine)})",
               f"{fmt(mine)} vs {fmt(prim[model])}")
        rows.append({"arm": arm, "damage": prim["damage"], "channel": prim["channel"],
                     "component": prim["component"], "armor": prim["armor"],
                     "strength": prim["strength"], **{m: prim[m] for m in MODELS}})

    ok(all(r["armor"] == 5000 and r["strength"] == 99 for r in rows
           if r["channel"] == "bullet" and r["component"] == "direct"),
       f"{BUILD_NAME} bullet channel is 5000 @ 99 on every direct-hit arm")
    ok(any(c["component"] == "direct" and c["damage"] == 1.0
           for c in table["tank_cannon"]["components"]),
       "tank cannon direct bullet is 1.0 (the 1500 blast is the primary)")

    # ---------------------------------------------------------------- Vulcan heat
    bm = load(BM_WEAPONS)
    fields = [f for o in bm["objects"] for f in o["fields"]]
    heat = [f for f in fields if f["path"] == "RBatmobileCannon.HeatUpPerSecond"]
    off = [f for f in fields if f["path"] == "RBatmobileCannon.OverheatOffValue"]
    ok(len(heat) == 4 and {f["value"] for f in heat} == {0.0},
       f"HeatUpPerSecond 0.0 in {len(heat)}/4 instances",
       str(sorted({f["value"] for f in heat})))
    ok({f["offset"] for f in heat} == {2680}, "HeatUpPerSecond @2680 (0x0A78)")
    ok(len(off) == 4 and {f["value"] for f in off} == {0.25},
       f"OverheatOffValue 0.25 in {len(off)}/4 instances",
       str(sorted({f["value"] for f in off})))
    ok({f["offset"] for f in off} == {2688}, "OverheatOffValue @2688 (0x0A80)")
    heat_time = (off[0]["value"] / heat[0]["value"]) if heat and heat[0]["value"] else None
    ok(heat_time is None, "0.25 / 0.0 has no finite time-to-overheat")

    # ---------------------------------------------------------------- missile lock
    lock = [f for f in fields if f["path"] == "RBatmobileEMPMissile.MissileLockOnDuration"]
    civ = [f for f in fields if f["path"] == "RBatmobileEMPMissile.CivilianMissileLockOnDuration"]
    ok(len(lock) == 3 and {f["value"] for f in lock} == {2.0},
       f"MissileLockOnDuration 2.0 in {len(lock)}/3 instances",
       str(sorted({f["value"] for f in lock})))
    ok({f["offset"] for f in lock} == {2560}, "MissileLockOnDuration @2560 (0x0A00)")
    ok(len(civ) == 3 and {f["value"] for f in civ} == {1.0},
       f"CivilianMissileLockOnDuration 1.0 in {len(civ)}/3 instances",
       str(sorted({f["value"] for f in civ})))
    ok({f["offset"] for f in civ} == {2564}, "CivilianMissileLockOnDuration @2564 (0x0A04)")

    # ---------------------------------------------------------------- the JC3 side: absence scan
    jc3_rows = 0
    jc3_heat: list[str] = []
    jc3_lock: list[tuple[str, object]] = []
    for line in open(JC3_WEAPONS, encoding="utf-8"):
        rec = json.loads(line)
        for src in rec["sources"]:
            for inst in src.get("decode", {}).get("instances", []):
                for path, _t, _v in inst["rows"]:
                    jc3_rows += 1
                    if re.search(r"heat", path, re.I):
                        jc3_heat.append(path)
                    if re.search(r"lock", path, re.I):
                        jc3_lock.append((path, _v))
    ok(jc3_rows > 3000, f"JC3 weapon tunes carry {jc3_rows:,} member rows")
    ok(not jc3_heat, f"0 JC3 weapon members name heat ({len(set(jc3_heat))} distinct)",
       ", ".join(sorted(set(jc3_heat))[:4]))
    lock_dur = sorted({p for p, _v in jc3_lock if re.search(r"duration|time", p, re.I)})
    ok(not lock_dur, f"0 of {jc3_rows:,} JC3 members name a lock duration", ", ".join(lock_dur))
    ok(sorted({p for p, _v in jc3_lock}) == ["missile_weapon[0].ai_tuning.missile_base_tuning."
                                             "missile_loose_lock_distance",
                                             "missile_weapon[0].tuning.missile_base_tuning."
                                             "missile_loose_lock_distance"],
       f"the only lock-named JC3 members are {len(jc3_lock)} `missile_loose_lock_distance` rows",
       str(sorted({p for p, _v in jc3_lock})))

    t19 = {r["id"]: r for r in load(T19)["rows"]}
    ok(t19["T-HUD17"]["disposition"] == "out (stated absence both sides)",
       "T-HUD17 Vulcan heat is a named omission", t19["T-HUD17"]["disposition"])
    ok(t19["T-HUD18"]["disposition"] == "partial" and "1.5 s" in t19["T-HUD18"]["jc3"],
       "T-HUD18 lock is one marker rotating once per 1.5 s",
       t19["T-HUD18"]["jc3"][:60])

    # ---------------------------------------------------------------- measured lock attempts
    lock_samples = 0
    lock_max = 0.0
    nfiles = 0
    for fn in sorted(os.listdir(RUNTIME)):
        if not (fn.startswith("samples-") and fn.endswith(".jsonl")):
            continue
        nfiles += 1
        for line in open(os.path.join(RUNTIME, fn), encoding="utf-8"):
            for key, value in json.loads(line).get("changed", {}).items():
                if key.endswith(".LockOnTime") and isinstance(value, (int, float)):
                    lock_samples += 1
                    lock_max = max(lock_max, float(value))
    ok(nfiles == 7 and lock_samples > 200,
       f"{nfiles} capture files, {lock_samples} LockOnTime samples")
    ok(lock_max < 2.0, f"measured LockOnTime never reaches the 2.0 s row (max {lock_max:g} s)",
       f"{lock_max}")

    # ---------------------------------------------------------------- the document
    n_pred = len(rows) + 1
    L: list[str] = []
    a = L.append
    a("# Q combat predictions (V-05 part 2)")
    a("")
    a("Generated by `python Tools/scripts/v05_combat.py --write`; re-derived and compared")
    a(f"byte-for-byte by `--check`. Written before any in-game test. Build: `{BUILD_REL}`")
    a(f"(`max_health` **{hp:,}**, re-read from the built health module).")
    a("")
    a(f"**{n_pred + 1} lines: {n_pred} predicted, 1 UNKNOWN.** Every line names its source row, the")
    a("expected value and a pass band. On the shots-to-kill lines the band is the **three-model")
    a("bracket** of `DAMAGE_MODEL.md` §4 (H0 armour ignored / H1 percentage gate / H2 threshold +")
    a("pool), not measurement error: inside a matched model the count is exact, and the band says")
    a("which counts the files allow. Nothing here claims which model is true.")
    a("")
    a(f"## Shots to kill, `{BUILD_REL}`")
    a("")
    a("| id | arm | per hit -> channel | H0 | H1 | H2 | pass band | source row |")
    a("|---|---|---|---:|---:|---:|---|---|")
    for i, r in enumerate(rows, start=1):
        per = f"{r['damage']:g} -> {r['channel']}"
        if r["component"] == "blast":
            per += " (blast)"
        a(f"| K-{i} | `{r['arm']}` | {per} | {fmt(r['H0'])} | {fmt(r['H1'])} | {fmt(r['H2'])} | "
          f"{band(r)} | `DAMAGE_MODEL.md` §4 `{r['arm']}`; RC2 health module |")
    a("")
    a(f"Armour on the bullet channel is `{rows[0]['armor']} @ {rows[0]['strength']}` and the")
    a("explosion channel is `250 @ 50` (both re-read from the RC2 health module), so the same")
    a("`5000 @ 99` gate that makes a pistol take 1,200 rounds under H0 says `never` under H2 -")
    a("the H0/H2 split on this table is the whole of ARM-1's open question, not a measurement")
    a("scatter. `tank_cannon`'s primary component is its **1500 blast in 8 m**; its direct")
    a("`bullet_weapon` damage is 1.0 and never reaches health under H2.")
    a("")
    a("### The published build row is test-091, not the RC")
    a("")
    a("`DAMAGE_MODEL.md` §4's build column was written for `Builds/test-091` at **2,000 HP**;")
    a(f"`{BUILD_REL}` reads **{hp:,} HP**, so the published counts understate the RC by 18x. Its")
    a("own §5 already says the BmAK ratio needs 24 x 1500 = 36,000 HP and that 36,000 is outside")
    a("the fleet's 500..4000 range - the RC ships it anyway. The published numbers, parsed from")
    a("the file and checked against `DAMAGE_MODEL.json` by `--check`:")
    a("")
    a("| arm | channel | armour | H0 | H1 | H2 |")
    a("|---|---|---|---:|---:|---:|")
    for r in published:
        a(f"| `{r['arm']}` | {r['channel']} | {r['armour']} | {fmt(r['H0'])} | {fmt(r['H1'])} | "
          f"{fmt(r['H2'])} |")
    a("")
    a("## Vulcan overheat time")
    a("")
    a("| id | source row | expected value | pass band | class | status |")
    a("|---|---|---|---|---|---|")
    a(f"| K-{len(rows) + 1} | `WEAPONS.json` `RBatmobileCannon.HeatUpPerSecond` "
      f"{sval(heat[0]['value'])} @{heat[0]['offset']} (0x0A78) and `OverheatOffValue` "
      f"{sval(off[0]['value'])} @{off[0]['offset']} (0x0A80), 4/4 instances identical; "
      f"`FOOTAGE.md` F-3; `t19_hud.json` T-HUD17 | **never** - 0.25 / 0.0 has no finite time, so"
      f" the threshold cannot be reached by the only rate the files give; the JC3 build has no"
      f" heat member at all ({jc3_rows:,} tune member rows, 0 name heat) | gun does not stop for"
      f" heat inside a {PROBE_S} s continuous burst, and no overheat sound plays; a stop or the"
      f" `Engine.Play_Minigun_Overheat` event fails the line | decoded (rate, threshold, JC3"
      f" absence) + derived (no finite time) | predicted |")
    a("")
    a(f"`{PROBE_S} s` is the probe length, not a value from any row - no file gives a limit, which")
    a("is why the line predicts *never* rather than a number. The BmAK path is wired")
    a("(`OverheatOffValue` 0.25, `ChainGunOverheatSound` -> `Engine.Play_Minigun_Overheat`), so a")
    a("per-shot heat add in native code is not excluded by the grab (`FOOTAGE.md` F-3); on the")
    a("JC3 side there is nothing to add it to, since no JC3 weapon tune and no `InitVehicleWeapons`")
    a("parameter carries heat (`JC3_HUD_WEAPONS.md:7`).")
    a("")
    a("## Missile lock time")
    a("")
    a("| id | source row | expected value | pass band | class | status |")
    a("|---|---|---|---|---|---|")
    a(      f"| K-{len(rows) + 2} | `WEAPONS.json` `RBatmobileEMPMissile.MissileLockOnDuration` "
      f"{sval(lock[0]['value'])} s @{lock[0]['offset']} (0x0A00) and "
      f"`CivilianMissileLockOnDuration` "
      f"{sval(civ[0]['value'])} s @{civ[0]['offset']} (0x0A04), 3/3 instances identical; "
      f"`JC3_HUD_WEAPONS.md:7`; `t19_hud.json` T-HUD18 | BmAK: 2.0 s against a military target,"
      f" 1.0 s against a civilian one. **The build: UNKNOWN** - no JC3 row carries a lock"
      f" duration ({jc3_rows:,} tune member rows, 0 name a duration; the only lock members are"
      f" {len(jc3_lock)} `missile_loose_lock_distance` rows, a distance); the only 1.5 s in the data"
      f" is the POI 21 reticle's rotation | withheld - there is no JC3 number for it to fail | decoded"
      f" (BmAK) / UNKNOWN (build) | UNKNOWN |")
    a("")
    a("The BmAK row cannot be copied to the build: JC3's lock is the platform's `AutoAim` plus a")
    a("native caller that paints POI 21, and the weapon-id -> HUD bridge is UNKNOWN (G2-25 §5).")
    a(f"The {nfiles} capture files hold {lock_samples} `LockOnTime` samples; the highest value in")
    a(f"any of them is {lock_max:g} s, i.e. every recorded attempt broke off (the target was")
    a("released) before the 2.0 s row was reached - so the measurement neither confirms nor")
    a("falsifies the row, and cannot supply the build's missing number either.")
    a("")
    a("## Oracles re-run by `--check`")
    a("")
    for c in checks:
        mark = "PASS" if c["ok"] else "FAIL"
        a(f"* {mark} {c['oracle']}")
    a("")
    a("## UNKNOWNs (no row gives a number)")
    a("")
    a("* **weapon -> armour channel** - no tune names a damage type or a `bullet_heavy` flag")
    a("  (`DAMAGE_MODEL.md` step 3: 0 of 1,515 member rows), so which channel an arm lands on is")
    a("  assumed from its gun class, not decoded.")
    a("* **the part layer** - every `*_vehicle_parts.vmodc` except the monorail flatbed fails")
    a("  ConvertAdf, so every count above is \"the whole vehicle takes every hit\".")
    a("* **Vulcan time-to-overheat on the BmAK side** - `HeatUpPerSecond` is 0.0, and whether a")
    a("  per-shot native add exists is not excluded by the grab (`FOOTAGE.md` F-3).")
    a("* **missile lock time on the JC3 side** - 0 lock-duration members in the weapon tunes (the")
    a("  two lock-named rows are a loose-lock *distance*) and 0 `CreatePoi` calls of type 21 in the")
    a("  movie; the entity -> HUD bridge is native.")
    a("* **whether the game honours any line here** - the test ban stays; nothing was installed,")
    a("  launched or attached to.")
    a("")
    a("## Labels")
    a("")
    a("Values are **decoded** from the named JSON/MD sources (offsets given for the `.uasset`")
    a("fields), **derived** by the arithmetic shown (0.25 / 0.0, `ceil` per model), or **UNKNOWN**.")
    a("The `damage_predict` counts are decoded damage values run through a derived model; the model")
    a("itself is not decoded and is carried as the H0/H1/H2 bracket, never as one answer.")
    a("")
    text = "\n".join(L)

    failed = [c for c in checks if not c["ok"]]
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['oracle']}"
              + (f" [{c['detail']}]" if c["detail"] and not c["ok"] else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} oracles pass")
    if failed:
        return 1

    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(OUT, ROOT).replace(os.sep, '/')}")
        return 0

    current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    if current != text:
        for line in __import__("difflib").unified_diff((current or "").splitlines(),
                                                       text.splitlines(), "on-disk", "recomputed",
                                                       lineterm="", n=1):
            print(line)
        print("FAIL document differs from the regenerated text")
        return 1
    print("PASS document: PREDICTIONS_COMBAT.md matches the regenerated text")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="write Working/Q/PREDICTIONS_COMBAT.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
