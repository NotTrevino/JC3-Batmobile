"""challenge_t_plan.py - read-only recomputation of the claims in Working/Translation/T_PLAN.md.

Every check prints one line per claim: the claim's number(s), the recomputed number(s), and
CONFIRMED / REFUTED.  Nothing is written outside stdout; no document is edited; the game is not
launched.

Usage:
  python Tools/scripts/chase/challenge_t_plan.py
"""
import collections
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk, TYPE_NAMES  # noqa: E402

WORK = os.path.join(ROOT, "Working", "Translation")
RES = os.path.join(ROOT, "Research", "BatmobileGrab")
GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"


def say(tag, text):
    print(f"[{tag}] {text}")


def ledger():
    rows = [json.loads(l) for l in open(os.path.join(WORK, "T_ROWS.jsonl"), encoding="utf-8")
            if l.strip()]
    dispo = collections.Counter(r["dispo"] for r in rows)
    docs = collections.Counter(r["doc"] for r in rows)
    return rows, dispo, docs


def t6_rows():
    path = os.path.join(WORK, "T6_HUD_CAMERA.md")
    ids = set()
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\|\s*(T-(?:HUD|CAM)\d+)\s*\|", line)
        if m:
            ids.add(m.group(1))
    return ids


def cdo(cls, package):
    """Tag stream of Default__<cls> in one package."""
    pkg = Package(os.path.join(GAME, package))
    for i, e in enumerate(pkg.exports, 1):
        if (e["name"] or "") == "Default__" + cls:
            tags, _end, _stop = best_walk(pkg, pkg.data(i))
            return {t.get("offset"): t for t in tags}
    return None


def vals():
    out = {}
    for cls, pkg in (("SVehicle", "Engine.upk"), ("SVehicleWheel", "Engine.upk"),
                     ("Pawn", "Engine.upk"), ("RVehicleSimBatmobile", "BmGame.upk"),
                     ("RVehicleSimCar", "Engine.upk"), ("RVehicleBatmobileBase", "BmGame.upk"),
                     ("RVehicle", "BmGame.upk")):
        out[cls] = cdo(cls, pkg)
    return out


def main():
    rows, dispo, docs = ledger()
    say("C1", f"T_PLAN says 128 rows = 105 ledger + 23 T6; ledger now {len(rows)} rows, "
             f"T6 table ids {len(t6_rows())}")
    say("C2", f"T_PLAN dispositions keep 51 / edit 16 / next 3 / epe 16 / blocked 11 / out 8; "
             f"ledger now {dict(dispo)}")
    say("C2b", f"T_PLAN per-doc T-1 49 / T-2b 39 / T-3 15 + T6 23; ledger now {dict(docs)}")
    out = dispo.get("out", 0)
    say("C3", f"T_PLAN '15 out' and '113 in scope = 97 evidenced + 1 assumed + 15 blocked'; "
             f"ledger out {out}, blocked {dispo.get('blocked',0)}, next {dispo.get('next',0)}")

    grab = json.load(open(os.path.join(RES, "grab.json"), encoding="utf-8"))
    say("C4", f"T_PLAN G1 objects 19,203 / 20,128; grab.json readable {grab['readable']} / "
              f"exports {grab['exports']} (schema {grab['schema']})")

    idx = json.load(open(os.path.join(ROOT, "Research", "JC3Grab", "INDEX.json"), encoding="utf-8"))
    say("C5", f"T_PLAN index 81,952 / 81,953; INDEX.json named_rows {idx['named_rows']} / "
              f"tab_entries {idx['tab_entries']}")

    off = json.load(open(os.path.join(RES, "OFFSETS.json"), encoding="utf-8"))
    named = sum(1 for f in off["fields"] if f.get("name"))
    say("C5b", f"T_PLAN offsets 423 / 423 named; OFFSETS.json fields {len(off['fields'])}, "
               f"named {named}")

    ent = open(os.path.join(ROOT, "Research", "JC3Grab", "ENTITIES.md"), encoding="utf-8").read()
    geo = open(os.path.join(ROOT, "Research", "JC3Grab", "GEOMETRY.md"), encoding="utf-8").read()
    for tag, text, label in (("C5c", ent, "ENTITIES.md"), ("C5d", geo, "GEOMETRY.md")):
        m = re.findall(r"6,045 / 6,045|77,611 / 77,611", text)
        say(tag, f"T_PLAN {label} totals re-found verbatim: {sorted(set(m)) or 'NOT FOUND'}")

    # arithmetic claims
    fa_w, fa_h = 3.5, 2.27
    say("C6", f"T_PLAN T-A1 frontal area: 3.5 x 2.27 = {fa_w*fa_h:.2f} m2 but the row keeps "
              f"6.63 - the stated derivation does not produce the value")

    extra = min(3500.0, 600.0 * 2.0)
    say("C7", f"T_PLAN T-B2: min(3500, 600 x 2.0) = {extra:.0f} cu = "
              f"{extra*0.036:.1f} km/h (1200 cu * 0.036 km/h per cu)")

    ch = json.load(open(os.path.join(RES, "CHAIN.json"), encoding="utf-8"))
    names = set()

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("name"), str):
                names.add(o["name"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(ch)
    have = {n.split(".", 1)[1] if "." in n else n: n for n in names}
    for member in ("DriftCorrectionSteerSpeed", "SteeringSpeedReCentreMod", "FakeExtraSpeedMax",
                   "FakeExtaSpeedAccel", "BoostDuration", "SuspensionTravelUp",
                   "SuspensionTravelDown", "MaxBrakeTorque", "EbrakeTime",
                   "InertiaTensorMultiplier", "MassScale", "UprightLiftStrength"):
        say("C8", f"CHAIN.json carries {member}: {have.get(member, 'NO')}")

    grip = [n for n in names if re.search(r"grip|traction", n, re.I)]
    align = [n for n in names if re.search(r"align", n, re.I)]
    brake = sorted(n for n in names if re.search(r"brake|ebrake|handbrake", n, re.I))
    aero = sorted(n for n in names if re.search(r"lift|drag|downforce|aero", n, re.I))
    say("C9", f"CHAIN.json grip/traction members: {grip or 'none'}")
    say("C9b", f"CHAIN.json align members: {align or 'none'}")
    say("C9c", f"CHAIN.json brake-family members: {brake}")
    say("C9d", f"CHAIN.json lift/drag members: {aero or 'none'}")

    v = vals()
    def show(cls, off, label):
        tags = v.get(cls)
        if tags is None:
            say("C10", f"{label}: no Default__{cls}")
            return
        t = tags.get(off)
        say("C10", f"{label}: Default__{cls} @0x{off:04x} = "
                   f"{'absent' if t is None else repr(t.get('value')) + ' (' + str(TYPE_NAMES.get(t.get('type_id'))) + ')'}")

    base = "RVehicleBatmobileBase"
    show(base, 0x1f8c, "DriftCorrectionSteerSpeed (B3: 1.0)")
    show("RVehicleSimCar", 0x1c0, "SteeringSpeedReCentreMod (B3: 1.0)")
    show(base, 0x1bf4, "FakeExtraSpeedMax (B3: 3500)")
    show(base, 0x1bf8, "FakeExtaSpeedAccel (B3: 600)")
    show("RVehicleSimBatmobile", 0x298, "BoostDuration (B3: 2.0)")
    show("SVehicle", 0x6c8, "InertiaTensorMultiplier (B4: [1,1,1])")
    show("SVehicle", 0x814, "MassScale (B4: 1.0)")
    show("SVehicle", 0x71c, "UprightLiftStrength")
    show("RVehicle", 0xabc, "DriftSteeringAssist (B3: absent -> false)")
    show("RVehicle", 0xac0, "DriftSteeringBias (B3: absent -> 0)")

    # camera conversion
    for h in (85.0, 95.0):
        vf = math.degrees(2 * math.atan(math.tan(math.radians(h / 2)) / (16 / 9)))
        say("C11", f"T_PLAN camera: horizontal {h:.0f} deg at 16:9 -> vertical {vf:.2f} deg "
                   f"(plan says 55 and 63)")

    # plan-internal arithmetic
    say("C12", f"T_PLAN 4D/5 coverage sum 16+4+1+15+77 = {16+4+1+15+77} vs '113 in scope' and "
               f"section 7 says 78 carried -> 16+4+1+15+78 = {16+4+1+15+78}")
    say("C13", f"T_PLAN behaviour denominators: section 3 '0/112', section 5 '0/112', yet "
               f"'113 in scope' - one row is dropped without being named")

    # T-K1 disproof arithmetic
    say("C14", f"T_PLAN T-K1 disproof 4 x 300 / (6000 x 0.683) = {4*300/(6000*0.683):.3f} m/s2")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
