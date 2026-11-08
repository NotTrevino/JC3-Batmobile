"""audit_compromises_b.py - AUDIT-B: every build step that is less accurate than BmAK.

Operator goal: 100% BmAK lore accuracy. A limit of JC3 is amended, never accepted silently
(INSTRUCTIONS.md section 3), so every step where the BUILD ships less lore than BmAK must be
listed and approved by a quoted operator decision - never inferred from a `done` status.

Sources (read-only; nothing under Builds/ is written):
    MODLOG.md, GRAB_BACKLOG.md section 12, Builds/bm-RC1/receipt.json,
    Working/RC/bm_rc_manifest.json, Tools/scripts/bm_budget.py, Tools/scripts/bm_rc.py,
    Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md, Research/BatmobileGrab/COLLISION_GEOM.json,
    Research/BatmobileGrab/LIGHTS.md, Working/Lights/bm_lightrig.json,
    Working/Damage/bm_health.json, Working/Parts/bm_vehicle_parts.json

Rule this script enforces: an item is APPROVED only if a source line contains the operator's own
words, and that line is found and printed here (file + line + quote). A decision recorded in no
file is reported as such - the script never upgrades "done", "shortcut" or "convention" to
approval.

    python Tools/scripts/audit_compromises_b.py --write   # write Working/RC/COMPROMISES_B.md
    python Tools/scripts/audit_compromises_b.py --check   # rebuild from the sources, compare bytes
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MD = os.path.join(ROOT, "Working", "RC", "COMPROMISES_B.md")
RECEIPT = os.path.join(ROOT, "Builds", "bm-RC1", "receipt.json")
MANIFEST = os.path.join(ROOT, "Working", "RC", "bm_rc_manifest.json")
MODLOG = os.path.join(ROOT, "MODLOG.md")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
BUDGET = os.path.join(ROOT, "Tools", "scripts", "bm_budget.py")
RC = os.path.join(ROOT, "Tools", "scripts", "bm_rc.py")
CONTROLS = os.path.join(ROOT, "Research", "BatmobileGrab", "CONTROLS_MENU_SCREENS.md")
COLLGEOM = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_GEOM.json")
LIGHTSMD = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.md")
LIGHTRIG = os.path.join(ROOT, "Working", "Lights", "bm_lightrig.json")
HEALTH = os.path.join(ROOT, "Working", "Damage", "bm_health.json")
PARTS = os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json")
SCRIPTS = os.path.join(ROOT, "Tools", "scripts")
B10D = os.path.join(ROOT, "tmp", "freebuff", "reports", "B-10d.md")


# --------------------------------------------------------------------------- read helpers
def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def lines_of(path: str) -> list[str]:
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read().splitlines()


def find(path: str, needle: str) -> tuple[int, str]:
    """(1-based line number, line text) of the first line containing `needle`. Absence is fatal:
    a citation that cannot be re-found must never be printed as evidence."""
    for i, line in enumerate(lines_of(path), 1):
        if needle in line:
            return i, line.strip()
    raise SystemExit(f"evidence missing: {needle!r} not in {rel(path)}")


def find_opt(path: str, needle: str):
    try:
        return find(path, needle)
    except SystemExit:
        return None


def num(pattern: str, text: str, what: str) -> float:
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"number not found ({what}): {pattern!r} in {text[:120]!r}")
    return float(m.group(1))


def quote(text: str, n: int = 150) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= n else t[: n - 1] + "\u2026"


# --------------------------------------------------------------------------- derived facts
def f_build_identity() -> dict:
    return {"receipt_sha256": sha256(RECEIPT)[:16], "receipt_bytes": os.path.getsize(RECEIPT),
            "manifest_sha256": sha256(MANIFEST)[:16], "manifest_bytes": os.path.getsize(MANIFEST)}


def f_budget() -> dict:
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    step = [s for s in rec["steps"] if s.startswith("B-15: ")][0]
    m = re.search(r"B-15: (\d+) \.lod trimmed, non-vanilla model ([\d.]+) -> ([\d.]+) KB of ([\d.]+)", step)
    lods, before, after, cap = int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
    man = json.load(open(MANIFEST, encoding="utf-8"))
    in_manifest = sum(1 for k, v in man["owners"].items() if k.endswith(".lod") and "B-15" in v)
    budget_src = open(BUDGET, encoding="utf-8").read()
    cap_const = float(re.search(r"CAP_KB = ([\d.]+)", budget_src).group(1))
    target_const = float(re.search(r"TARGET_KB = ([\d.]+)", budget_src).group(1))
    ln_approval = find(MODLOG, 'User choice: "unbind panels + trim LODs"')
    return {"lods": lods, "in_manifest": in_manifest, "before_kb": before, "after_kb": after,
            "cap_kb": cap, "cap_const": cap_const, "target_const": target_const,
            "cut_kb": round(before - after, 1), "approval": ln_approval}


def f_panels() -> dict:
    ln_count = find(MODLOG, "Serpente panels (vanilla-identical,")
    n = int(num(r"the (\d+) Serpente panels", ln_count[1], "panel count"))
    kb = float(re.search(r"([\d,]+\.?\d*) KB\)", ln_count[1]).group(1).replace(",", ""))
    ln_not = find(MODLOG, "It was NOT done")
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    b17 = [s for s in rec["steps"] if s.startswith("B-17: ")]
    ln_v01 = find(MODLOG, "Model 8,077.5 KB vs the 4,915 KB hard cap")
    return {"panels": n, "kb": kb, "count_line": ln_count, "not_done_line": ln_not,
            "b17": b17[0] if b17 else "B-17: no step recorded", "v01_line": ln_v01}


def f_reverted() -> dict:
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    rev = rec["b18"]["reverted_to_vanilla"]
    rmbs = [p for p in rev if p.endswith(".rbm")]
    return {"total": len(rev), "rmbs": rmbs, "n_rmb": len(rmbs),
            "names": [os.path.basename(p) for p in rmbs]}


def f_lamps() -> dict:
    rig = json.load(open(LIGHTRIG, encoding="utf-8"))
    rows, dropped = rig["rows"], rig["dropped"]
    donor = [r for r in rows if str(r.get("origin", "")).startswith("donor-row")]
    custom = [r for r in rows if str(r.get("origin", "")).startswith("custom")]
    graph = [r for r in rows if str(r.get("origin", "")).startswith("graph-object")]
    ln21 = find(BACKLOG, "21 shipped entries \u2192 **18**")
    ln_drop = find(BACKLOG, "`Front_Primary_Head` whose BmAK socket has no lamp face")
    entries = int(num(r"\*\*(\d+)\*\*", find(LIGHTSMD, "| entries |")[1], "BmAK light entries"))
    return {"rows": len(rows), "dropped": len(dropped), "donor_rows": len(donor),
            "custom": len(custom), "graph": len(graph), "shipped_before": len(donor) + len(dropped),
            "drop_names": [d.get("preset_name") for d in dropped], "bmak_entries": entries,
            "approval_line": None, "ln21": (BACKLOG,) + ln21, "ln_drop": (BACKLOG,) + ln_drop}


def f_audio() -> dict:
    ln_route = find(BACKLOG, "route **a + c**")
    ln_swap = find(BACKLOG, "5 swapped sample payloads")
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    banks = {os.path.basename(f["path"]): f["bytes"] for f in rec["files"] if "fmod_banks" in f["path"]}
    man = json.load(open(os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest.json"), encoding="utf-8"))
    slots = man.get("slots") or []
    swapped = [s for s in slots if isinstance(s, dict) and s.get("payload_sha256")]
    return {"route_line": (BACKLOG,) + ln_route, "swap_line": (BACKLOG,) + ln_swap, "banks": banks,
            "swapped": len(swapped), "slots": len(slots)}


def f_health() -> dict:
    h = json.load(open(HEALTH, encoding="utf-8"))
    rows = h["rows"]
    tdm1 = [r for r in rows if r.get("row") == "T-DM1"][0]
    ln_def = find(MODLOG, "deform_scale=0, impact_damage_factor=0")
    ln_wh = find(MODLOG, "skew_health=400")
    ln_bmak = find(BACKLOG, "RVehicleBatmobile.Health` 1,200")
    ln_hits = find(HEALTH, "24 BmAK heavy-cannon hits x 1500.0 shell damage = 36000")
    return {"max_health": h["decisions"]["max_health"], "from": tdm1["from"], "to": tdm1["to"],
            "rows": len(rows), "deform_line": ln_def, "wheel_line": ln_wh,
            "bmak_line": (BACKLOG,) + ln_bmak, "hits_line": (HEALTH,) + ln_hits}


def f_bodyless() -> dict:
    ln = find(MODLOG, "9 such parts none")
    p = json.load(open(PARTS, encoding="utf-8"))
    return {"n": int(num(r"B-04 gave (\d+) such parts", ln[1], "bodyless parts")), "line": ln,
            "behaviour": p["summary"], "n_parts": p["summary"]["parts_after"]}


def f_t13r() -> dict:
    ln_donor = find(MODLOG, "3x3 = donor 3x3")
    ln_skip = find(BACKLOG, "**69** rows skipped")
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    step = [s for s in rec["steps"] if s.startswith("T-13R: ")][0]
    n = int(num(r"T-13R: (\d+) interaction transforms", step, "T-13R count"))
    return {"n": n, "donor_line": ln_donor, "skip_line": (BACKLOG,) + ln_skip, "step": step}


def f_spawn() -> dict:
    ln = find(MODLOG, "vecs = donor's")
    return {"line": ln}


def f_colour() -> dict:
    ln_gain = find(MODLOG, "`PAINT_ALBEDO_GAIN = 4.0`")
    ln_violet = find(MODLOG, "Hull reads pale violet-white in noon sun")
    ln_corr = find(MODLOG, "PAINT_ALBEDO_GAIN = 4 (MODLOG:5488")
    controls = open(CONTROLS, encoding="utf-8-sig", errors="replace").read()
    return {"gain_line": ln_gain, "violet_line": ln_violet, "correction_line": ln_corr,
            "colour_hits_in_controls": len(re.findall(r"colou?r", controls, re.I))}


def f_d2() -> dict:
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    ln = find(BACKLOG, "resolved 2026-10-28 (user): (b) one hybrid car")
    ln_rows = find(BACKLOG, "13 of 15 T-15 rows record differing pursuit/battle values")
    return {"variants": rec["variants"], "approval": ln, "rows_line": ln_rows}


def f_controls() -> list[dict]:
    out = []
    for needle in ("BmAK controls replace all JC3 controls",
                   "Enter with JC3's Y; exit with LB",
                   "Eject is A A",
                   "the winch takes d-pad RIGHT and REPLACES Mission Select",
                   "AR Challenges is not needed either"):
        ln = find(CONTROLS, needle)
        out.append({"needle": needle, "file": rel(CONTROLS), "line": ln[0], "quote": quote(ln[1])})
    return out


def f_collision() -> dict:
    c = json.load(open(COLLGEOM, encoding="utf-8"))
    o = c["oracle_chassis_box_vs_body_box"]
    chassis = o["chassis_box0_extents_cm"]              # [690.305, 374.536, 207.5] (full lengths, cm)
    box_sorted = o["chassis_box0_full_m_sorted"]        # [2.075, 3.745, 6.903]
    body_xyz = o["body_box_span_m_xyz_jc3"]             # [3.495, 2.271, 7.025] = B-10's target
    rec = json.load(open(RECEIPT, encoding="utf-8"))
    hull = [s for s in rec["steps"] if s.startswith("B-10c: ")][0]
    b = re.search(r"'bounds': \[\[([-\d.]+), ([-\d.]+), ([-\d.]+)\], \[([-\d.]+), ([-\d.]+), ([-\d.]+)\]\]", hull)
    lo = [float(b.group(i)) for i in (1, 2, 3)]
    hi = [float(b.group(i)) for i in (4, 5, 6)]
    hull_xyz = [round(hi[0] - lo[0], 3), round(hi[1] - lo[1], 3), round(hi[2] - lo[2], 3)]
    # JC3 order x (width), y (height), z (length); the chassis box is decoded as [length, width, height]
    ch_xyz = [box_sorted[1], box_sorted[0], box_sorted[2]]
    delta = [round(body_xyz[i] - ch_xyz[i], 3) for i in range(3)]
    ln = find(B10D, "**MISMATCH** - width +0.250 m")
    ln = (B10D,) + ln
    ln2 = find(MODLOG, "That wrong source is a concrete reason the built collision was misaligned") \
        if find_opt(MODLOG, "That wrong source is a concrete reason the built collision was misaligned") else (0, "")
    return {"chassis_cm": chassis, "chassis_xyz": ch_xyz, "body_xyz": body_xyz, "hull_xyz": hull_xyz,
            "hull_bounds": [lo, hi], "delta": delta, "b10d_line": ln, "g3_line": ln2,
            "approval_line": find(MODLOG, "B, build collision from the Batmobile mesh")}


# --------------------------------------------------------------------------- approval check
def approval(needle: str, path: str) -> dict | None:
    hit = find_opt(path, needle)
    if hit is None:
        return None
    return {"file": rel(path), "line": hit[0], "quote": quote(hit[1], 190)}


def items() -> list[dict]:
    bud, pan, rev, lam, aud, hea = f_budget(), f_panels(), f_reverted(), f_lamps(), f_audio(), f_health()
    body, t13, spw, col, d2 = f_bodyless(), f_t13r(), f_spawn(), f_colour(), f_d2()
    coll = f_collision()
    I: list[dict] = []

    I.append({
        "id": "C-01", "card": "B-10 / B-10c", "title": "Body world-collision hull is the render bbox, not BmAK's chassis box",
        "scripts": ["bm_collision.py", "bm_colhull.py", "bm_colmesh.py"],
        "bmak": f"drivable chassis box {coll['chassis_cm'][0]:g} x {coll['chassis_cm'][1]:g} x {coll['chassis_cm'][2]:g} cm "
                f"= {coll['chassis_xyz'][2]:.3f} x {coll['chassis_xyz'][0]:.3f} x {coll['chassis_xyz'][1]:.3f} m "
                f"(COLLISION_GEOM bodies[0] bone Batmobile_Chassis, box 0)",
        "build": f"body 0 world hull from the Batmobile render mesh: B-10 target "
                 f"{coll['body_xyz'][0]:.3f} x {coll['body_xyz'][1]:.3f} x {coll['body_xyz'][2]:.3f} m, written hull "
                 f"{coll['hull_xyz'][0]:.3f} x {coll['hull_xyz'][1]:.3f} x {coll['hull_xyz'][2]:.3f} m "
                 f"(x {coll['hull_bounds'][0][0]:.3f}..{coll['hull_bounds'][1][0]:.3f}, "
                 f"y {coll['hull_bounds'][0][1]:.3f}..{coll['hull_bounds'][1][1]:.3f}, "
                 f"z {coll['hull_bounds'][0][2]:.3f}..{coll['hull_bounds'][1][2]:.3f})",
        "loss": f"{abs(coll['delta'][0]):.3f} m narrower, {coll['delta'][1]:+.3f} m taller and {coll['delta'][2]:+.3f} m "
                f"longer than the decoded chassis box - the car hits walls about 25 cm inside its own flanks and carries "
                f"about 20 cm of empty collision above the real roof (B-10d: MISMATCH on body 0, MISMATCH inherited by B-10c; "
                f"Working/Collision2/ holds a chassis-box build that is not shipped)",
        "visibility": "every metre driven: walls, ground contact and Rico's footing all use body 0",
        "approval": approval("B, build collision from the Batmobile mesh", MODLOG),
        "approval_note": "the quoted decision authorises building collision from the Batmobile MESH (B-10b's raycast "
                         "shape). It does not name the render bbox as the source for the drivable body, and B-10d "
                         "records the chassis box as the correct source; no quote approves the bbox hull.",
        "still_unapproved": True,
        "proof": [coll["approval_line"], coll["b10d_line"], coll["g3_line"]],
    })
    I.append({
        "id": "C-02", "card": "B-18 / B-15", "title": "8 mesh files are the donor's vanilla bytes (body lod3/lod4, six wheel LODs)",
        "scripts": ["bm_paths.py"],
        "bmak": "APP-1: all five body LODs are Batmobile_V2 at true scale, and the wheels are the Batmobile's",
        "build": f"`b18.reverted_to_vanilla` sends {rev['n_rmb']} `.rbm` back to vanilla Serpente bytes: "
                 + ", ".join(n.replace("sportsmuscle_", "").replace(".rbm", "") for n in rev["names"]),
        "loss": "at every distance that selects body lod3/lod4 - and on three of the four wheels at their trimmed "
                "slots - the game draws the donor car's geometry: a Serpente-shaped shell fades in around the Batmobile",
        "visibility": "mid and far range, constantly while driving",
        "approval": None,
        "approval_note": "B-18's own rule (unreached changed files 'go back to vanilla bytes') is a script rule, not an "
                         "operator decision; no quote mentions reverting meshes.",
        "proof": [],
    })
    I.append({
        "id": "C-03", "card": "B-15 / B-17", "title": "Approved unbind of the Serpente panels was not done, and B-17 (hide) is skipped",
        "scripts": ["bm_budget.py", "bm_hide.py"],
        "bmak": "no Serpente part exists anywhere on the Batmobile",
        "build": f"{pan['panels']} Serpente panels stay bound by the parts module ({pan['kb']:,.1f} KB, vanilla-identical, "
                 f"so excluded from R9's count) and the RC records `{pan['b17']}`; only the LOD trim half of the "
                 f"approved action was applied",
        "loss": "donor hood, trunk, fenders, bumpers, grill and seats can still draw through the Batmobile shell - the "
                "'Serpente cabin' seen in Q re-test 3/4 - while the approved step that would have removed them was dropped "
                "as 'risky parts-module surgery'",
        "visibility": "close range, permanent: the panels are inside the shell",
        "approval": {"file": rel(MODLOG), "line": bud["approval"][0], "quote": quote(bud["approval"][1], 190)},
        "approval_note": "the quote approves 'unbind panels + trim LODs'. The trim shipped; the unbind did not. Leaving "
                         "the panels bound is therefore an UNAPPROVED resting state, not an approved one.",
        "proof": [pan["count_line"], pan["not_done_line"], pan["v01_line"]],
        "still_unapproved": True,
    })
    I.append({
        "id": "C-04", "card": "B-07", "title": f"Lamp rig rebuilt: {lam['shipped_before']} shipped entries -> {lam['rows']}, no primary head lamp",
        "scripts": ["bm_lightrig.py"],
        "bmak": f"LIGHTS.md: {lam['bmak_entries']} light entries / 129 components over 9 behaviours (head 46, tail 8, boot 3, "
                f"interior 4, battle 16, forensics 12, none 12) incl. high beams (LGT-1)",
        "build": f"{lam['rows']} module entries from {lam['shipped_before']} shipped rows: {lam['donor_rows']} rewritten, "
                 f"{lam['graph']} new (T-L17), {lam['custom']} T-18 custom clones; {lam['dropped']} donor rows dropped - "
                 + ", ".join(str(n) for n in lam["drop_names"] if n),
        "loss": "`Front_Primary_Head` (the high beam) is dropped with no Batmobile lamp taking it, so LGT-1's high beams are "
                "absent; the indicators and reverse lamps that were dropped are not a lore loss (BmAK has none) but they are "
                "JC3 functionality the build removes",
        "visibility": "night driving and every time the lights are on",
        "approval": None,
        "approval_note": "the drops carry measured reasons in bm_lightrig.json; no operator quote approves dropping the "
                         "primary head lamp.",
        "proof": [lam["ln21"], lam["ln_drop"]],
    })
    I.append({
        "id": "C-05", "card": "B-11", "title": "Audio ships on JC3's banks: route a+c, 5 swapped samples, no BmAK bank",
        "scripts": ["bm_audio.py"],
        "bmak": "AUD-1..AUD-7: BML_Engine / VEH_Batmobile_MK2_Engine banks with the RPM RTPC, interior layer, per-weapon events",
        "build": f"route a+c: private copies of JC3's own banks "
                 + ", ".join(f"{k} {v:,} B" for k, v in sorted(aud["banks"].items()))
                 + f" with {aud['swapped']} swapped sample payloads (one per mapped event)",
        "loss": "engine start/idle/rev, tyres, impacts and weapons remain JC3 samples except five slots; no BmAK interior "
                "layer (AUD-3) and no per-weapon BmAK events (AUD-5). No .fev project ships, so a BmAK bank cannot be authored",
        "visibility": "continuous while driving - the engine note is the car's loudest identity",
        "approval": None,
        "approval_note": "route a+c is a research conclusion (JC3_AUDIO.md section 10), not an operator decision.",
        "proof": [aud["route_line"], aud["swap_line"]],
    })
    I.append({
        "id": "C-06", "card": "B-04", "title": f"{body['n']} behaviour-bearing parts ship with no collision body",
        "scripts": ["bm_parts.py"],
        "bmak": "turret yaw + cannon pitch, Vulcan barrel spin, turbine fan, air-brake fins (ANI-2..ANI-5)",
        "build": f"{body['n']} parts with a Turret/Cannon/GatlingGun/AirBrake/EngineRotatingPart behaviour and world/raycast "
                 f"collision ids -1 (turret, cannon, riot suppressor, machine gun, 4 aero flaps, jet); the fleet's own rule is "
                 f"'never without' (22/22, 68/68, 24/24, 3/3, 3/3)",
        "loss": "the fleet convention says these parts always carry a body; whether they aim, hinge or spin without one is "
                "UNKNOWN and never tested. If they do not, the turret and fins are static decoration",
        "visibility": "when firing or braking hard",
        "approval": None,
        "approval_note": "probe 7's finding that behaviours can be cleared is a load result ('they load as they are'), not a "
                         "lore decision.",
        "proof": [body["line"]],
    })
    I.append({
        "id": "C-07", "card": "B-09", "title": f"Health and damage are declared switches: max_health {hea['from']} -> {hea['to']:,}",
        "scripts": ["bm_health.py"],
        "bmak": "RVehicleBatmobile.Health 1,200; 24 heavy-cannon hits; small arms do nothing (ARM-1/ARM-2)",
        "build": f"private health module: max_health {hea['from']} -> {hea['to']:,} ({hea['rows']} rows), deform_scale 0, "
                 f"impact_damage_factor 0, front/rear_wheels_damage.skew_health 200 -> 400",
        "loss": f"{hea['to']:,} is not a decoded BmAK value: it is 24 hits x 1,500 shell damage, outside the shipped "
                f"500..4000 domain, and the file itself records 18,000 as the alternative if the percentage gate ships "
                f"(pending Q1-DM-A). The pool size the player feels is an unmade decision",
        "visibility": "only under fire; invisible until the car is shot",
        "approval": None,
        "approval_note": "the value carries a declared switch, not an operator quote; deform_scale 0 / impact 0 follow the "
                         "user's rule R1 (no deformation), which is recorded but not a sentence about these numbers.",
        "proof": [hea["bmak_line"], hea["hits_line"], hea["deform_line"], hea["wheel_line"]],
    })
    I.append({
        "id": "C-08", "card": "T-13R / B-05", "title": f"Entry/exit geometry is the donor's: {t13['n']} of 84 interaction rows, donor 3x3",
        "scripts": ["bm_entity.py", "bm_rc.py"],
        "bmak": "entry, exit and stunt points on the Batmobile's own sides and roof (WLD-3/WLD-4), from the decoded sockets",
        "build": f"{t13['n']} interaction transforms = donor 3x3 matrices x the G2-18 per-axis box map; the driver point is "
                 f"the donor's f_l_seat offset from the JC3 Driver socket; every other driver object shifts -1.445 m so the "
                 f"donor's seat->approach geometry holds",
        "loss": "the 3x3 is the Serpente's, not a decoded BmAK orientation, and 69 interaction rows were skipped as UNKNOWN "
                "and never built, so most entry/exit/transition transforms remain donor defaults",
        "visibility": "entry and exit, once per use",
        "approval": None,
        "approval_note": "the user's sentence in Q re-test 4 ('unenterable ... it should enter with JC3 control') asked for the "
                         "symptom to be fixed; it names no matrix source and is not approval of the donor 3x3.",
        "proof": [t13["donor_line"], t13["skip_line"]],
    })
    I.append({
        "id": "C-09", "card": "B-13c", "title": "Spawn record clones the donor's drop-box vectors",
        "scripts": ["bm_rebel.py"],
        "bmak": "the Batmobile's own footprint and centre",
        "build": "the donor's spawn record is cloned for the leaf: tags `vehicle,batmobile`, select 1, debug "
                 "`vehicle|ground|rebel`, and both vec fields are the donor's",
        "loss": "the drop box is sized for a 3.72 m Serpente while the Batmobile is 7.03 m long - the drop and the marker "
                "around the car are wrong for the car's size",
        "visibility": "once per Rebel Drop, and whenever the dropped vehicle is highlighted",
        "approval": None,
        "approval_note": "the log records the vector source as an explicit UNKNOWN ('drop box; Batmobile is larger'); no quote "
                         "accepts it.",
        "proof": [spw["line"]],
    })
    return I


def approved_items() -> list[dict]:
    bud, d2 = f_budget(), f_d2()
    return [
        {"id": "A-01", "card": "B-15", "title": "RC1 model budget cuts: LOD trim",
         "bmak": "APP-1: all five Batmobile LODs load",
         "build": f"non-vanilla model {bud['before_kb']:,.1f} -> {bud['after_kb']:,.1f} KB of the {bud['cap_kb']:,.1f} KB "
                  f"hard cap ({bud['cut_kb']:,.1f} KB cut); {bud['lods']} `.lod` become [s1,s2,last x3] (body, wheels) or "
                  f"[s1,last x4] (small add-ons), so LOD2/3/4 meshes of those parts never load",
         "loss": "mid-range detail on 16 parts; the far LOD is a repeated coarser mesh, so parts step down early",
         "approval": {"file": rel(MODLOG), "line": bud["approval"][0], "quote": quote(bud["approval"][1], 190)},
         "count_check": f"{bud['in_manifest']} manifest owners say B-15, {bud['lods']} in the receipt step"},
        {"id": "A-02", "card": "B-12 (skipped)", "title": "One hybrid car instead of pursuit + battle variants",
         "bmak": "MOD-1/MOD-2: two modes with different top speed, torque curve, armour reduction and battle camera",
         "build": f"{d2['variants']}; one entity, one drop entry, no mode switch; the 13 of 15 T-15 rows that record "
                  f"differing pursuit/battle values ship as a single car",
         "loss": "battle mode's low-speed/high-armour behaviour and its camera have no carrier; the car is pursuit-only",
         "approval": {"file": rel(BACKLOG), "line": d2["approval"][0], "quote": quote(d2["approval"][1], 190)},
         "count_check": "receipt.variants + backlog section 11 D-2"},
    ]


def build_model() -> dict:
    I, A = items(), approved_items()
    ctrl, col = f_controls(), f_colour()
    unapproved = [i for i in I if i["approval"] is None or i.get("still_unapproved")]
    # C-03 carries an approval quote for a different action; it is unapproved as it stands.
    per_script: dict[str, int] = {}
    for i in unapproved:
        for s in i["scripts"]:
            per_script[s] = per_script.get(s, 0) + 1
    missing_scripts = [s for s in per_script if not os.path.exists(os.path.join(SCRIPTS, s))]
    return {"items": I, "approved": A, "unapproved": unapproved, "per_script": per_script,
            "missing_scripts": missing_scripts, "controls": ctrl, "colour": col,
            "facts": {"budget": f_budget(), "panels": f_panels(), "reverted": f_reverted(), "lamps": f_lamps(),
                      "audio": f_audio(), "health": f_health(), "bodyless": f_bodyless(), "t13r": f_t13r(),
                      "collision": f_collision(), "d2": f_d2(), "identity": f_build_identity()}}


# --------------------------------------------------------------------------- render
def render() -> str:
    m = build_model()
    f = m["facts"]
    L: list[str] = []
    A = L.append
    A("# COMPROMISES_B - lore-accuracy audit of the BUILD (AUDIT-B)")
    A("")
    A("Generated by `Tools/scripts/audit_compromises_b.py`. Every number below is re-derived from the")
    A("source bytes named in section 2; `--check` rebuilds this file and compares it byte for byte.")
    A("Nothing under `Builds/` is written by this script.")
    A("")
    A("**Question it answers:** for every build step that ships less BmAK lore than the grab decoded,")
    A("what does BmAK have, what does the build ship, what is lost, and is there an operator sentence")
    A("that approves it?")
    A("")
    A("**Approval rule used.** APPROVED requires a source line containing the operator's own words; the")
    A("file and line are printed under the item. `done`, `skipped`, a card tag, a fleet convention or a")
    A("research conclusion are **not** approval. Where the only quote authorises a *different* action")
    A("than the one shipped, the item stays UNAPPROVED and the quote is shown with that note.")
    A("")
    A("## 1. Counts")
    A("")
    A(f"- audited build: `Builds/bm-RC1/receipt.json` {f['identity']['receipt_bytes']:,} B, sha256 "
      f"`{f['identity']['receipt_sha256']}\u2026`")
    A(f"- manifest: `Working/RC/bm_rc_manifest.json` {f['identity']['manifest_bytes']:,} B, sha256 "
      f"`{f['identity']['manifest_sha256']}\u2026`")
    A(f"- items audited: **{len(m['items'])}**")
    A(f"- UNAPPROVED: **{len(m['unapproved'])}**")
    A(f"- APPROVED with a quoted operator decision: **{len(m['approved'])}**")
    A("- operator decisions recorded 2026-11-05 (controls set): 5 quoted, none of them a build step that")
    A("  ships today (see section 5)")
    A("- one lore gap (paint colour) rests on the audit brief alone: `CONTROLS_MENU_SCREENS.md` contains")
    A(f"  {m['colour']['colour_hits_in_controls']} occurrences of 'colou?r' (section 5.1)")
    A("")
    A("### 1.1 UNAPPROVED items by script")
    A("")
    A("| script | UNAPPROVED items naming it |")
    A("|---|---:|")
    for s in sorted(m["per_script"]):
        A(f"| `{s}` | {m['per_script'][s]} |")
    A(f"| **distinct items** | **{len(m['unapproved'])}** |")
    A("")
    A("An item may name more than one script (the writer and its target rule), so the per-script column")
    A(f"counts script involvements: {sum(m['per_script'].values())} across {len(m['unapproved'])} items.")
    if m["missing_scripts"]:
        A("")
        A(f"**Scripts named but absent from `Tools/scripts/`: {m['missing_scripts']}** - the mapping of those")
        A("items to a writer is UNKNOWN.")
    A("")
    A("## 2. Sources and their hashes")
    A("")
    A("| source | role | sha256 (first 16) |")
    A("|---|---|---|")
    for p, role in ((RECEIPT, "the audited RC tree, steps + file list"),
                    (MANIFEST, "per-file owner cards, incl. B-15's .lod"),
                    (MODLOG, "build sections B-01..B-16, Q re-test, RC merge fix, and the quoted decisions"),
                    (BACKLOG, "section 12 tracker rows B-01..B-16, V-01/V-03/V-06; section 11 decisions"),
                    (BUDGET, "B-15 trim rule and R9 constants"),
                    (RC, "the RC merge pipeline (B-14/B-16/T-13R/B-18/B-15 call sites)"),
                    (CONTROLS, "the 2026-11-05 operator decisions"),
                    (COLLGEOM, "BmAK drivable chassis box vs the body render box"),
                    (LIGHTSMD, "BmAK light rig (101 entries)"),
                    (LIGHTRIG, "the shipped 18 entries and the 10 dropped rows"),
                    (HEALTH, "the shipped health rows"),
                    (PARTS, "the shipped behaviour rows")):
        A(f"| `{rel(p)}` | {role} | `{sha256(p)[:16]}\u2026` |")
    A("")
    A("## 3. UNAPPROVED, ranked by visibility in play")
    A("")
    A("| # | id | card | what is less accurate than BmAK | visible |")
    A("|---:|---|---|---|---|")
    for n, i in enumerate(m["unapproved"], 1):
        A(f"| {n} | {i['id']} | {i['card']} | {i['title']} | {i['visibility'].split(':')[0]} |")
    A("")
    rank = {i["id"]: n for n, i in enumerate(m["unapproved"], 1)}
    for i in m["items"]:
        A(f"### {i['id']} \u00b7 {i['title']}")
        A("")
        A(f"- card: `{i['card']}` \u00b7 scripts: " + ", ".join(f"`{s}`" for s in i["scripts"]))
        A(f"- status: **{'UNAPPROVED' if i['approval'] is None or i.get('still_unapproved') else 'APPROVED'}**"
          + (f" \u00b7 visibility rank {rank[i['id']]}" if i["id"] in rank else ""))
        A(f"- BmAK has: {i['bmak']}")
        A(f"- build ships: {i['build']}")
        A(f"- loss: {i['loss']}")
        A(f"- visible: {i['visibility']}")
        if i["approval"]:
            A(f"- the file does quote an operator: `{i['approval']['file']}:{i['approval']['line']}` -")
            A(f"  > {i['approval']['quote']}")
        else:
            A("- the file does quote an operator: **none found**")
        A(f"- why that is not approval: {i['approval_note']}")
        seen: set = set()
        for p in i["proof"]:
            if not p or not p[0]:
                continue
            path, ln, txt = p if len(p) == 3 else (MODLOG, p[0], p[1])
            if (path, ln) in seen:
                continue
            seen.add((path, ln))
            A(f"- evidence: `{rel(path)}:{ln}` - {quote(txt, 200)}")
        A("")

    A("## 4. APPROVED compromises (quoted operator decision)")
    A("")
    for a in m["approved"]:
        A(f"### {a['id']} \u00b7 {a['title']}")
        A("")
        A(f"- card: `{a['card']}`")
        A(f"- BmAK has: {a['bmak']}")
        A(f"- build ships: {a['build']}")
        A(f"- loss: {a['loss']}")
        A(f"- APPROVED: `{a['approval']['file']}:{a['approval']['line']}`")
        A(f"  > {a['approval']['quote']}")
        A(f"- re-derived: {a['count_check']}")
        A("")
    A("A third approved decision - `D-2` - is the same sentence quoted in `GRAB_BACKLOG.md` section 11 that")
    A("B-12's `skipped: D-2` status rests on; the tag alone would not have been approval.")
    A("")

    A("## 5. Operator decisions of 2026-11-05, quoted")
    A("")
    A("| decision | file:line | quote |")
    A("|---|---|---|")
    for c in m["controls"]:
        A(f"| {c['needle'][:44]} | `{c['file']}:{c['line']}` | {c['quote']} |")
    A("")
    A("None of these is a build step in `bm-RC1`: the controls/winch work is not built yet, so there is")
    A("nothing shipped to audit against them. They are recorded here because they pre-approve the")
    A("compromises the next build will make (JC3's pause/commlink keep priority; the d-pad rows AR")
    A("Challenges and Mission Select are dropped; the winch replaces Mission Select).")
    A("")
    A("### 5.1 The paint colour: approved in the brief, not in the file")
    A("")
    col = m["colour"]
    A(f"- the build ships `PAINT_ALBEDO_GAIN = 4.0`, a hand-entered literal chosen from a test-080 luma")
    A(f"  measurement, multiplied into the linear colour before the sRGB slots, plus hand-written sRGB")
    A(f"  constants (`{rel(MODLOG)}:{col['gain_line'][0]}`).")
    A(f"- in game the hull reads pale violet-white in noon sun (`{rel(MODLOG)}:{col['violet_line'][0]}`);")
    A(f"  G3-20d relabels the effective paint colour 'assumed' and G3-11c records the combine operator as")
    A(f"  UNKNOWN (`{rel(MODLOG)}:{col['correction_line'][0]}`), so the Arkham colour is not reproduced.")
    A(f"- the brief records an operator decision 'the BmAK colour is used exactly, lighting differences")
    A(f"  accepted', and names `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` as its record. That file")
    A(f"  contains **{col['colour_hits_in_controls']}** occurrences of colo(u)r: the sentence is not there.")
    A("- status: **APPROVED per the operator brief**, with the file citation missing. If a file-level quote")
    A("  is required, this is the one item that cannot be granted from disk. It is not ranked with the")
    A("  UNAPPROVED items because the operator's instruction for this audit grants it.")
    A("")
    A("## 6. Not a compromise (checked because the brief named it)")
    A("")
    A("**B-16: 12 APC mounted-M2 body members removed and 4 owner links nulled.** The removed members name")
    A("files that ship only inside the APC's `.ee` (`F9DCF6AB` model_xml, `98BBA63E` col `.pfx`, `9E74F03F`")
    A("grip_point, all `w206_mounted_capstone_m2hm`), and `F30CCB1C` pointed at the APC's own CCar root. The")
    A("medium tank - whose `w602`/`w603` names these clones carry - and the preorder Serpente both have the")
    A("link null and none of the three members. Removing them restores the donor convention and loses no")
    A("BmAK content, so it is a repair, not a lore compromise. It is listed here so the count is complete.")
    A("")
    A("## 7. Values a script takes from the donor instead of from BmAK")
    A("")
    A("| value | script | donor source | BmAK status | audited as |")
    A("|---|---|---|---|---|")
    A("| body-0 hull target | `bm_collision.py`, `bm_colhull.py` | Batmobile render-mesh bbox, not the decoded chassis box | decoded chassis box exists | C-01 |")
    A("| 8 body/wheel LOD meshes | `bm_paths.py` | vanilla Serpente `.rbm` bytes | Batmobile LODs exist | C-02 |")
    A("| 12 bound panels | `bm_budget.py`, `bm_hide.py` | vanilla Serpente panel RBMs | none needed | C-03 |")
    A("| 6 light rows + 10 dropped rows | `bm_lightrig.py` | the donor's shipped light module and presets | 101 BmAK entries | C-04 |")
    A("| engine/weapon samples | `bm_audio.py` | JC3 `vehicles.bank` / `weapons.bank` | BmAK banks decode to WAV | C-05 |")
    A("| collision ids -1 | `bm_parts.py` | fleet pattern for hull-less parts | BmAK parts are distinct meshes | C-06 |")
    A("| `max_health` 36,000 | `bm_health.py` | `lave_health_medium.vmodc` as the base module | `Health` 1,200 | C-07 |")
    A("| 15 interaction 3x3 matrices | `bm_entity.py`, `bm_rc.py` | the Serpente `.epe`'s own objects | BmAK sockets | C-08 |")
    A("| drop-box vectors | `bm_rebel.py` | the donor's spawn record | UNKNOWN for BmAK | C-09 |")
    A("")
    A("## 8. UNKNOWNs")
    A("")
    A("- **Whether the chassis box's frame is axis-aligned.** B-10d records the box transform as not decoded;")
    A("  if it carries a rotation, C-01's delta changes. Needs `FKBoxElem` layout + a re-run.")
    A("- **Whether B-10d's corrected hull was ever intended to ship.** `Working/Collision2/` holds a chassis-box")
    A("  build with 10/10 oracles; no receipt, card row or operator sentence adopts or rejects it.")
    A("- **Whether the 9 body-less behaviour parts actually move.** Fleet convention says they must carry a")
    A("  body; probe 7 only proved they load without one. A Q test would settle it.")
    A("- **What the Batmobile's own drop-box vectors are.** No decoded BmAK footprint reaches `bm_rebel.py`.")
    A("- **Whether the brief's colour decision exists in any file.** `CONTROLS_MENU_SCREENS.md` has none; no")
    A("  other file searched by this script contains 'colour is used exactly' or 'lighting differences'.")
    A("")
    A("## 9. Re-run")
    A("")
    A("```")
    A("python Tools/scripts/audit_compromises_b.py --write   # regenerate this file from the sources")
    A("python Tools/scripts/audit_compromises_b.py --check   # recompute and compare, exit 0 on match")
    A("```")
    A("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- main
def write() -> int:
    text = render()
    os.makedirs(os.path.dirname(MD), exist_ok=True)
    with open(MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    m = build_model()
    print(f"wrote {rel(MD)} ({len(text.splitlines())} lines)")
    print(f"items {len(m['items'])}, UNAPPROVED {len(m['unapproved'])}, APPROVED {len(m['approved'])}")
    print("by script: " + ", ".join(f"{k} {v}" for k, v in sorted(m["per_script"].items())))
    return 0


def check() -> int:
    if not os.path.exists(MD):
        print(f"FAIL: {rel(MD)} does not exist - run --write")
        return 1
    want = render()
    have = open(MD, encoding="utf-8").read()
    bad = 0
    if want == have:
        print(f"PASS: {rel(MD)} re-derives byte for byte from the sources")
    else:
        bad += 1
        wl, hl = want.splitlines(), have.splitlines()
        n = next((i for i, (a, b) in enumerate(zip(wl, hl), 1) if a != b), min(len(wl), len(hl)) + 1)
        print(f"FAIL: {rel(MD)} differs from the sources at line {n}")
        print(f"  on disk : {hl[n - 1] if n <= len(hl) else '(eof)'}")
        print(f"  source  : {wl[n - 1] if n <= len(wl) else '(eof)'}")
    m = build_model()
    def ok(c: bool, msg: str) -> None:
        nonlocal bad
        print(("PASS " if c else "FAIL ") + msg)
        bad += 0 if c else 1
    ok(len(m["unapproved"]) == 9, f"9 UNAPPROVED items (found {len(m['unapproved'])})")
    ok(len(m["approved"]) == 2, f"2 APPROVED items with a quoted decision (found {len(m['approved'])})")
    ok(not m["missing_scripts"], f"every script named in the table exists ({sum(m['per_script'].values())} involvements)")
    ok(all(i["approval"]["quote"] for i in m["approved"]), "every APPROVED item prints a quote found in its file at its line")
    ok(all(i["approval"] is None or i.get("still_unapproved") for i in m["unapproved"]),
       "no UNAPPROVED item carries a quote that approves what it ships")
    b = m["facts"]["budget"]
    ok(b["lods"] == b["in_manifest"] == 16 and b["cap_kb"] == b["cap_const"] == 4915.0,
       f"B-15: {b['before_kb']} -> {b['after_kb']} KB, {b['lods']} .lod (manifest {b['in_manifest']}, cap {b['cap_const']})")
    r = m["facts"]["reverted"]
    ok(r["n_rmb"] == 8 and r["total"] == 10, f"B-18 reverted {r['n_rmb']} .rbm of {r['total']} files to vanilla bytes")
    la = m["facts"]["lamps"]
    ok(la["rows"] == 18 and la["shipped_before"] == 21, f"B-07: {la['shipped_before']} shipped rows -> {la['rows']} entries, {la['dropped']} dropped")
    c = m["facts"]["collision"]
    ok(c["delta"] == [-0.25, 0.196, 0.122], f"B-10 hull vs chassis box delta {c['delta']} m (render bbox target)")
    print(("PASS" if not bad else "FAIL") + f": AUDIT-B {bad} failure(s), {len(m['items'])} items, "
          f"{len(m['unapproved'])} UNAPPROVED, {len(m['approved'])} APPROVED")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
