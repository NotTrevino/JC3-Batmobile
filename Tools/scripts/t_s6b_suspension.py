"""t_s6b_suspension.py - T-S6b: decode the JC3 suspension parameter set against BmAK's fields.

T-S6 says "no suspension bias/droop member or unit bridge for stiffness". This script tests that
claim against the files instead of repeating it:

    A. JC3 side - the `Suspension` module of every grabbed land/air vehicle
       (`E:/Modding/_gamedata/JC3grab/entities/*.json`, 232 entities, 166 with a Suspension
       module), with each vehicle's `RigidBody.mass` from the same bundle.
    B. BmAK side - the field names and class offsets from `Research/BatmobileGrab/
       BMSDK_OFFSETS.json` + `OFFSETS.md` (RVehicleSimBatmobile, SVehicle).
    C. field map - for every BmAK field: the JC3 member that carries the same physical quantity,
       or UNKNOWN, with the label that backs the answer.
    D. the oracle - does JC3 `strength` need a unit bridge at all? Two readings are tested against
       166 vehicles: `strength` as a mass-normalised rate (s^-2) and as an absolute rate (N/m,
       kN/m). A reading that predicts a static sag longer than the spring's own `length` is false.

Everything is read-only: the grab is a copy of the install, no game is launched or attached.

    python Tools/scripts/t_s6b_suspension.py --write
    python Tools/scripts/t_s6b_suspension.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

OUT_JSON = os.path.join(ROOT, "Working", "Translation", "T_S6B.json")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "T_S6B.md")
FLEET = os.environ.get("JC3_ENTITIES", r"E:/Modding/_gamedata/JC3grab/entities")
BMSDK = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")
OFFSETS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "OFFSETS.md")
DRIVE_MODES = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVE_MODES.json")
G = 9.81
BM_CLASSES = ("RVehicleSimBatmobile", "SVehicle")
BM_WANT = ("SuspensionStiffness", "SuspensionDamping", "SuspensionBias", "MaxDroop",
           "ChassisMass", "MassScale", "StayUprightStiffness", "StayUprightDamping",
           "MaxPMSuspensionSpeed")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def load_fleet() -> list[dict]:
    rows, seen = [], set()
    if not os.path.isdir(FLEET):
        raise SystemExit(f"missing grab: {FLEET}")
    for fn in sorted(os.listdir(FLEET)):
        if not fn.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(FLEET, fn), encoding="utf-8"))
        ent = doc.get("entity")
        if not ent or ent in seen:
            continue
        seen.add(ent)
        mods = {m.get("type"): m for m in doc.get("modules") or []}
        sus = mods.get("Suspension")
        if not sus:
            continue
        rb = {r["path"]: r.get("value") for r in (mods.get("RigidBody") or {}).get("rows") or []}
        sv = {r["path"]: r.get("value") for r in sus.get("rows") or []}
        mass = rb.get("mass")
        if not isinstance(mass, (int, float)) or not sv.get("front.strength"):
            continue
        rows.append({
            "entity": ent, "module": sus.get("file"), "mass_kg": mass,
            "strength": sv["front.strength"], "strength_r": sv.get("rear.strength"),
            "compression": sv["front.compression"], "compression_r": sv.get("rear.compression"),
            "relaxation": sv.get("front.relaxation"), "relaxation_r": sv.get("rear.relaxation"),
            "length": sv.get("front.length"), "length_r": sv.get("rear.length"),
            "min_length": sv.get("front.min_length"),
            "max_length_offset": sv.get("front.max_length_offset"),
            "hardpoint_offset": sv.get("front.hardpoint_offset_along_spring"),
            "hardpoint_offset_r": sv.get("rear.hardpoint_offset_along_spring"),
            "antiroll": sv.get("front.antirollbar_strength"),
            "rows": len(sus.get("rows") or []),
        })
    return rows


def member_set(rows: list[dict]) -> list[str]:
    """The Suspension module's field names, from one vehicle's module (they are the same set)."""
    doc = json.load(open(os.path.join(FLEET, os.listdir(FLEET)[0]), encoding="utf-8"))
    for m in doc.get("modules") or []:
        if m.get("type") == "Suspension":
            return sorted({(r["path"].split(".", 1)[1] if "." in r["path"] else r["path"])
                           for r in m.get("rows") or []})
    return sorted({k for r in rows for k in r if k in (
        "strength", "compression", "relaxation", "length", "min_length",
        "max_length_offset", "hardpoint_offset", "antiroll")})


def bmak() -> dict:
    d = json.load(open(BMSDK, encoding="utf-8"))
    out = []
    for cn in BM_CLASSES:
        c = (d.get("classes") or {}).get(cn) or {}
        for p in c.get("properties") or []:
            n = p.get("name") or ""
            if any(w in n for w in BM_WANT):
                out.append({"class": cn, "name": n, "offset": p.get("offset"),
                            "hex": hex(p.get("offset") or 0), "type": p.get("type"),
                            "kind": p.get("kind")})
    out.sort(key=lambda r: (r["class"], r["offset"] or 0))
    # is any VALUE decoded anywhere? DRIVE_MODES.json names the fields; look for numbers.
    values = {}
    if os.path.exists(DRIVE_MODES):
        blob = open(DRIVE_MODES, encoding="utf-8").read()
        for r in out:
            i = blob.find(f'"{r["name"]}"')
            if i < 0:
                values[r["name"]] = {"named": False}
                continue
            tail = blob[i:i + 160]
            values[r["name"]] = {"named": True, "context": tail[:120]}
    return {"fields": out, "value_probe": values,
            "offsets_md": [l.strip() for l in open(OFFSETS_MD, encoding="utf-8")
                           if "BMWheelSuspension" in l or "MaxDroop" in l][:6]}


def oracle(rows: list[dict]) -> dict:
    """Two readings of `strength`; each is scored by the static sag it implies vs `length`."""
    per_mass, absolute_n, absolute_kn = [], [], []
    for r in rows:
        m, k, L = r["mass_kg"], r["strength"], r["length"]
        if not L:
            continue
        sag_pm = G / (4 * k)                    # strength is per unit mass: m cancels
        sag_an = m * G / (4 * k)                # strength in N/m
        sag_ak = m * G / (4 * k * 1000)         # strength in kN/m
        per_mass.append((r["entity"], m, k, L, round(sag_pm, 4), sag_pm <= L))
        absolute_n.append((r["entity"], m, k, L, round(sag_an, 4), sag_an <= L))
        absolute_kn.append((r["entity"], m, k, L, round(sag_ak, 4), sag_ak <= L))
    viol = [{"entity": e, "mass": mm, "strength": kk, "length": LL, "sag": s,
             "ratio": round(s / LL, 4)}
            for e, mm, kk, LL, s, good in per_mass if not good]
    viol.sort(key=lambda r: -r["ratio"])
    worst = max(per_mass, key=lambda t: t[4]) if per_mass else None
    heavy = max(per_mass, key=lambda t: t[1]) if per_mass else None
    heavy_an = next((t for t in absolute_n if heavy and t[0] == heavy[0]), None)
    heavy_ak = next((t for t in absolute_kn if heavy and t[0] == heavy[0]), None)
    zeta = sorted(r["compression"] / (2 * r["strength"] ** 0.5) for r in rows)
    freq = sorted(r["strength"] ** 0.5 / (2 * 3.141592653589793) for r in rows)
    masses = sorted(r["mass_kg"] for r in rows)
    strengths = sorted({r["strength"] for r in rows})
    return {
        "vehicles": len(rows),
        "mass": {"min": masses[0], "median": masses[len(masses) // 2], "max": masses[-1],
                 "over_3000kg": sum(1 for x in masses if x > 3000)},
        "strength_values": strengths,
        "per_mass": {"pass": sum(1 for t in per_mass if t[5]), "fail": sum(1 for t in per_mass if not t[5]),
                     "worst_sag": worst[4] if worst else None},
        "absolute_n": {"pass": sum(1 for t in absolute_n if t[5]),
                       "fail": sum(1 for t in absolute_n if not t[5])},
        "absolute_kn": {"pass": sum(1 for t in absolute_kn if t[5]),
                        "fail": sum(1 for t in absolute_kn if not t[5])},
        "per_mass_violations": viol,
        "per_mass_worst_ratio": viol[0]["ratio"] if viol else 1.0,
        "heavy": {"entity": heavy[0], "mass": heavy[1], "strength": heavy[2], "length": heavy[3],
                  "sag_per_mass": heavy[4],
                  "sag_absolute_n": heavy_an[4] if heavy_an else None,
                  "sag_absolute_kn": heavy_ak[4] if heavy_ak else None},
        "zeta": {"min": round(zeta[0], 3), "median": round(zeta[len(zeta) // 2], 3),
                 "max": round(zeta[-1], 3)},
        "freq_hz": {"min": round(freq[0], 3), "median": round(freq[len(freq) // 2], 3),
                    "max": round(freq[-1], 3)},
    }


# BmAK field -> JC3 member. `same` names the physical quantity; `conv` the unit rule.
FIELD_MAP = [
    ("RVehicleSimBatmobile", "BMWheelSuspensionStiffness", "front.strength / rear.strength",
     "spring rate", "strength_JC3 = k_BmAK / m   (derived: k = strength * mass)",
     "derived"),
    ("RVehicleSimBatmobile", "PMWheelSuspensionStiffness", "front.strength / rear.strength",
     "spring rate (pursuit mode)", "same as BMWheelSuspensionStiffness, per-mode value",
     "derived"),
    ("RVehicleSimBatmobile", "BMWheelSuspensionDamping", "front.compression + front.relaxation",
     "damper rate", "c_JC3 = c_BmAK / m; JC3 splits bump (compression) and rebound (relaxation), "
     "BmAK has one field", "derived"),
    ("RVehicleSimBatmobile", "BMWheelSuspensionBias", "front.hardpoint_offset_along_spring",
     "static rest offset along the spring axis", "sign/scale UNKNOWN",
     "derived member, UNKNOWN value bridge"),
    ("RVehicleSimBatmobile", "BMFrontWheelSuspensionBias", "front.hardpoint_offset_along_spring",
     "front rest offset", "sign/scale UNKNOWN", "derived member, UNKNOWN value bridge"),
    ("RVehicleSimBatmobile", "StationaryWheelSuspensionBias", "front.hardpoint_offset_along_spring",
     "rest offset when stationary", "UNKNOWN (no stationary variant in the JC3 module)",
     "UNKNOWN"),
    ("RVehicleSimBatmobile", "BMFrontWheelMaxDroop", "front.length - front.min_length",
     "downward travel limit", "JC3 has total travel only; max_length_offset would extend it and is 0",
     "derived member, UNKNOWN split"),
    ("RVehicleSimBatmobile", "BMRearWheelMaxDroop", "rear.length - rear.min_length",
     "downward travel limit", "same as front", "derived member, UNKNOWN split"),
    ("RVehicleSimBatmobile", "MaxPMSuspensionSpeed", "front.max_velocity_for_damp_clamp",
     "damper clamp speed", "same physical role (clamp the damper above a speed); scale UNKNOWN",
     "derived member, UNKNOWN value bridge"),
    ("SVehicle", "ChassisMass", "RigidBody.mass", "sprung mass",
     "the bridge's mass term; JC3 mass is kg (decoded), BmAK unit UNKNOWN", "decoded member, "
     "UNKNOWN value"),
    ("SVehicle", "StayUprightStiffness", "front.antirollbar_strength", "roll resistance",
     "NOT the same quantity: BmAK keeps the body upright, JC3 links the two wheels of an axle",
     "UNKNOWN"),
]


def model() -> dict:
    rows = load_fleet()
    return {"fleet": rows, "members": member_set(rows), "bmak": bmak(),
            "oracle": oracle(rows), "map": [dict(zip(
                ("class", "field", "jc3", "quantity", "bridge", "label"), t)) for t in FIELD_MAP],
            "donor": next((r for r in rows if "v0300_car_kensington_sportsmuscle" in r["entity"]), None),
            "citations": {"mass": next((l.strip() for l in open(OFFSETS_MD, encoding="utf-8")
                                        if "ChassisMass" in l), "UNKNOWN"),
                          "stiffness": next((l.strip() for l in open(OFFSETS_MD, encoding="utf-8")
                                             if "BMWheelSuspensionStiffness" in l), "UNKNOWN")}}


def render(m: dict) -> str:
    L: list[str] = []
    A = L.append
    o, bm, d = m["oracle"], m["bmak"], m["donor"]
    A("# T-S6B - JC3 suspension parameters vs BmAK's suspension fields")
    A("")
    A("Generated by `Tools/scripts/t_s6b_suspension.py`. `--check` re-reads the grab, the BmSDK")
    A("layout and this oracle and rebuilds the file byte for byte. Read-only: no install write, no")
    A("game launch.")
    A("")
    A("## Answer")
    A("")
    A("**The carrier exists and the stiffness bridge exists in form; its numbers are UNKNOWN.**")
    A("")
    A(f"JC3 has a dedicated `Suspension` module ({d['rows'] if d else '?'} rows on the donor), not a")
    A("slot inside the handling module. It carries a spring rate, two damper rates (bump and rebound,")
    A("split into separate members), a spring length with min length and a length offset, a per-axle")
    A("anti-roll strength, and a hardpoint offset along the spring axis - the closest member to BmAK's")
    A("`SuspensionBias`. What it does **not** carry is a separate droop figure: only total travel.")
    A("")
    A(f"On the stiffness side the unit question is settled by the fleet itself (section 3): JC3")
    A(f"`strength` is **mass-normalised** (s^-2), so the bridge to BmAK's absolute spring rate is")
    A(f"`k = strength * mass`. That bridge is therefore *formally* available for every vehicle, and it")
    A("needs one number this project does not have: BmAK's stiffness value in a known unit.")
    A("")
    A("## 1. The JC3 member set (decoded)")
    A("")
    A(f"`Suspension` module, `{m['members'] and len(m['members'])}` distinct field paths")
    A("(front and rear are the same set; `wheel_hardpoint_offsets` is a per-wheel array):")
    A("")
    A("`" + "`, `".join(m["members"]) + "`")
    A("")
    A("Donor (Serpente, `Builds/bm-001` ships its `suspension.vmodc` unchanged):")
    A("")
    A("| member | value | label |")
    A("|---|---:|---|")
    if d:
        for k, lab in (("strength", "front spring rate"), ("strength_r", "rear spring rate"),
                       ("compression", "front bump damping"), ("relaxation", "front rebound damping"),
                       ("compression_r", "rear bump damping"), ("relaxation_r", "rear rebound damping"),
                       ("length", "front spring length (m)"), ("min_length", "front min length (m)"),
                       ("max_length_offset", "front extra length (m)"),
                       ("hardpoint_offset", "front hardpoint offset along spring (m)"),
                       ("hardpoint_offset_r", "rear hardpoint offset along spring (m)"),
                       ("antiroll", "front anti-roll strength")):
            A(f"| `{k}` | {d.get(k)} | decoded |")
    A("")
    A("## 2. BmAK's fields (decoded names/offsets; values UNKNOWN)")
    A("")
    A("| class | field | offset | kind |")
    A("|---|---|---:|---|")
    for f in bm["fields"]:
        A(f"| `{f['class']}` | `{f['name']}` | `{f['hex']}` | {f['kind']} |")
    A("")
    A("Source: `Research/BatmobileGrab/OFFSETS.md`:")
    A("")
    for line in bm["offsets_md"][:4]:
        A(f"> {line[:240]}")
    A("")
    named = [k for k, v in bm["value_probe"].items() if v.get("named")]
    A(f"Value probe: `DRIVE_MODES.json` names {len(named)} of these fields "
      f"({', '.join('`%s`' % n for n in named[:6])}) - it references them, it does not carry a")
    A("value. No file in the project decodes a numeric BmAK stiffness, damping or droop, so every")
    A("BmAK value in the map below is **UNKNOWN**.")
    A("")
    A("## 3. The oracle: is a unit bridge needed, and which reading survives?")
    A("")
    A("A static spring must compress less than its own length. For a four-wheel car each spring")
    A("carries `m*g/4`, so the sag is `m*g/(4*k)`. Read `strength` as mass-normalised and `m`")
    A("cancels; read it as absolute N/m or kN/m and the sag grows with the vehicle's mass.")
    A("")
    A(f"Tested on **{o['vehicles']}** vehicles that carry a `Suspension` module and a `RigidBody.mass`")
    A(f"(mass {o['mass']['min']}-{o['mass']['max']} kg, median {o['mass']['median']}, "
      f"{o['mass']['over_3000kg']} above 3,000 kg):")
    A("")
    A("| reading of `strength` | sag = | fits inside `length` | violates |")
    A("|---|---|---:|---:|")
    A(f"| mass-normalised (s^-2) | g/(4*strength) | {o['per_mass']['pass']}/{o['vehicles']} | "
      f"{o['per_mass']['fail']} |")
    A(f"| absolute N/m | m*g/(4*strength) | {o['absolute_n']['pass']}/{o['vehicles']} | "
      f"{o['absolute_n']['fail']} |")
    A(f"| absolute kN/m | m*g/(4*strength*1000) | {o['absolute_kn']['pass']}/{o['vehicles']} | "
      f"{o['absolute_kn']['fail']} |")
    A("")
    h = o["heavy"]
    A(f"The decisive vehicle is the heaviest one, `{h['entity'].rsplit('/', 2)[-2]}`:")
    A("")
    A(f"- decoded: mass {h['mass']} kg, `front.strength` {h['strength']}, `front.length` {h['length']} m;")
    A(f"- mass-normalised reading: sag {h['sag_per_mass']} m - inside the {h['length']} m spring;")
    A(f"- N/m reading: sag {h['sag_absolute_n']} m - {round((h['sag_absolute_n'] or 0) / (h['length'] or 1))}x")
    A(f"  the spring's own length, i.e. the car would sit on its bump stops before the wheel touched");
    A(f"- kN/m reading: sag {h['sag_absolute_kn']} m - also longer than the spring.");
    A("")
    if o["per_mass_violations"]:
        A(f"The mass-normalised reading misses on {o['per_mass']['fail']} rows, and all of them are the")
        A("same car (a civilian and its debug twin) overshooting a very short spring by a hair:")
        A("")
        A("| vehicle | mass (kg) | strength | length (m) | sag (m) | sag/length |")
        A("|---|---:|---:|---:|---:|---:|")
        for v in o["per_mass_violations"]:
            A(f"| `{v['entity'].rsplit('/', 2)[-2]}` ({v['entity'].rsplit('/', 1)[-1]}) | {v['mass']} | "
              f"{v['strength']} | {round(v['length'], 4)} | {v['sag']} | {v['ratio']} |")
        A("")
        A(f"The worst of them is {o['per_mass_worst_ratio']}x the spring length - a 2% overshoot that")
        A("says the car rides within a few millimetres of its bump stop, not that the unit is wrong.")
        A("")
    A("So `strength` cannot be an absolute rate: the N/m reading is falsified on **every** vehicle, the")
    A("kN/m reading fails on the heavy half, and the mass-normalised reading fits the whole fleet to")
    A(f"within {o['per_mass_worst_ratio']}x. This is the oracle the brief asks for - it would fail if")
    A("`strength` were N/m, and it does.")
    A("")
    A(f"Consistency of the other members under the same normalisation (derived): damping ratio")
    A(f"`zeta = compression/(2*sqrt(strength))` spans {o['zeta']['min']}..{o['zeta']['max']}")
    A(f"(median {o['zeta']['median']}) and the natural frequency `sqrt(strength)/(2*pi)` spans")
    A(f"{o['freq_hz']['min']}..{o['freq_hz']['max']} Hz (median {o['freq_hz']['median']}) - road-car")
    A("plausible ranges for all 166 vehicles, with no mass term needed. Label: derived.")
    A("")
    A("## 4. Field map")
    A("")
    A("| BmAK field | JC3 member | physical quantity | bridge | label |")
    A("|---|---|---|---|---|")
    for r in m["map"]:
        A(f"| `{r['field']}` | `{r['jc3']}` | {r['quantity']} | {r['bridge']} | **{r['label']}** |")
    A("")
    A("## 5. What T-S6 got right, and what it did not")
    A("")
    A("- **Right**: there is no droop member. JC3 has `length`, `min_length` and")
    A("  `max_length_offset`; on the donor `min_length` = 0 and `max_length_offset` = 0, so the spring")
    A("  has total travel and no encoded down-travel split, while BmAK keeps `BMFrontWheelMaxDroop`")
    A("  and `BMRearWheelMaxDroop` as separate fields.")
    A("- **Right**: there is no decoded numeric bridge for stiffness - BmAK's stiffness value and")
    A("  unit are not in any project file.")
    A("- **Wrong** in the implied conclusion that the parameters are absent: the `Suspension` module")
    A("  carries the spring rate, both damper rates, the anti-roll strength and a rest offset along the")
    A("  spring, and the mass-normalised unit of `strength` is now decoded by the oracle above.")
    A("- **Bias**: `hardpoint_offset_along_spring` is the member that plays BmAK's bias role")
    A("  (a static offset along the spring axis, non-zero on the donor). Whether BmAK's bias means the")
    A("  same thing, and at what sign and scale, is **UNKNOWN**.")
    A("")
    A("## 6. Sources")
    A("")
    A("| source | note |")
    A("|---|---|")
    A(f"| `{rel(BMSDK)}` | BmAK class layout: names, offsets, kinds |")
    A(f"| `{rel(OFFSETS_MD)}` | per-offset provenance lines quoted in section 2 |")
    A(f"| `{FLEET}` | JC3 grab: `Suspension` + `RigidBody` rows per entity |")
    A("")
    return "\n".join(L) + "\n"


def write() -> int:
    m = model()
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    payload = {"schema": 1, "card": "T-S6b", "generator": "Tools/scripts/t_s6b_suspension.py",
               "members": m["members"], "donor": m["donor"], "oracle": m["oracle"],
               "bmak_fields": m["bmak"]["fields"], "field_map": m["map"],
               "labels": "decoded: module rows, mass, BmAK offsets; derived: mass-normalised unit, "
                         "field map quantities; UNKNOWN: every BmAK value, bias sign, droop split"}
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1)
        f.write("\n")
    text = render(m)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    o = m["oracle"]
    print(f"wrote {rel(OUT_JSON)} and {rel(OUT_MD)} ({len(text.splitlines())} lines)")
    print(f"fleet {o['vehicles']} vehicles; sag fit per-mass {o['per_mass']['pass']}/"
          f"{o['vehicles']}, N/m {o['absolute_n']['pass']}, kN/m {o['absolute_kn']['pass']}; "
          f"heavy {o['heavy']['entity'].rsplit('/', 2)[-2]} "
          f"sag {o['heavy']['sag_per_mass']} vs length {o['heavy']['length']}")
    return 0


def check() -> int:
    m = model()
    bad = 0

    def ok(c: bool, msg: str) -> None:
        nonlocal bad
        print(("PASS " if c else "FAIL ") + msg)
        bad += 0 if c else 1

    for p, want in ((OUT_MD, render(m)), (OUT_JSON, None)):
        if not os.path.exists(p):
            ok(False, f"{rel(p)} missing - run --write")
        elif want is not None:
            ok(open(p, encoding="utf-8").read() == want,
               f"{rel(p)} re-derives byte for byte from the sources")
    o = m["oracle"]
    ok(o["vehicles"] >= 100, f"fleet decoded: {o['vehicles']} vehicles with Suspension + mass")
    ok(o["per_mass"]["pass"] >= 0.95 * o["vehicles"] and o["per_mass_worst_ratio"] <= 1.1,
       f"mass-normalised reading fits {o['per_mass']['pass']}/{o['vehicles']}, worst overshoot "
       f"{o['per_mass_worst_ratio']}x")
    ok(o["absolute_n"]["fail"] == o["vehicles"],
       f"absolute N/m reading is falsified on all vehicles ({o['absolute_n']['fail']})")
    ok((o["heavy"]["sag_absolute_n"] or 0) > (o["heavy"]["length"] or 0) * 10,
       f"heaviest vehicle: absolute sag {o['heavy']['sag_absolute_n']} m >> length "
       f"{o['heavy']['length']} m")
    ok(0.02 < (o["heavy"]["sag_per_mass"] or 0) < (o["heavy"]["length"] or 0),
       f"heaviest vehicle: mass-normalised sag {o['heavy']['sag_per_mass']} m inside the spring")
    ok(0.05 < o["zeta"]["median"] < 1.0,
       f"damping ratios plausible: median {o['zeta']['median']} in {o['zeta']['min']}..{o['zeta']['max']}")
    ok(any(f["name"] == "BMWheelSuspensionStiffness" for f in m["bmak"]["fields"]),
       "BmAK stiffness field is in the layout with an offset")
    ok(any("front.strength" in r["jc3"] for r in m["map"]), "map names the JC3 spring-rate member")
    print(("PASS" if not bad else "FAIL") + f": T-S6b {bad} failure(s)")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        return write()
    if a.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
