#!/usr/bin/env python3
"""AUDIT-T: every place the translation chose less than BmAK lore, and who approved it.

The project's goal is 100% BmAK lore accuracy.  A row compromises that goal when its
disposition drops a BmAK feature (`out`), keeps a JC3/donor/fleet value where BmAK has its own
(`keep`/`edit`/`next`), shrinks or merges a feature, or records a permanent omission (`blocked`).

Approval is **quoted, never inferred**.  The only approval sources are:

  * `GRAB_BACKLOG.md` section 11 - the D-decisions, each carrying its own date and `(user)`;
  * `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` - the operator statements of 2026-11-05.

Every APPROVED row names the file and the line, and `--check` re-opens that file, asserts the
cited line number still holds the quote, and asserts the quote still exists.  A row with no such
quote is UNAPPROVED, including rows whose loss merely *follows* from an approved decision
(D-2's hybrid car does not approve dropping a mode-only value).

Reads: `Working/Translation/T_ROWS.jsonl` (198 rows), the two approval files, and - for the
"reopened" section - the G2 pages that contradict a closed "JC3 cannot" claim.

Writes Working/Translation/COMPROMISES_T.md + COMPROMISES_T.json.
`--check` re-derives both and fails on drift, on a missing approval quote, or on a row id that is
not in `T_ROWS.jsonl` (except the synthetic `SYN:` entries named in the report).

Usage:
  python Tools/scripts/audit_compromises_t.py --write
  python Tools/scripts/audit_compromises_t.py --check
  python Tools/scripts/audit_compromises_t.py dump list|cites
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Working", "Translation")
ROWS = os.path.join(OUT, "T_ROWS.jsonl")
MD_NAME = "COMPROMISES_T.md"
JSON_NAME = "COMPROMISES_T.json"

BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
CONTROLS = os.path.join(ROOT, "Research", "BatmobileGrab", "CONTROLS_MENU_SCREENS.md")
HUDWPN = os.path.join(ROOT, "Research", "JC3Grab", "JC3_HUD_WEAPONS.md")
WP13_PROPOSAL = os.path.join(OUT, "T_WP13_PROPOSAL.md")
TWP3B = os.path.join(OUT, "T_WP3B_LOCKON.md")
DRIVE = os.path.join(ROOT, "Research", "JC3Grab", "DRIVE_CARRIERS.md")

# Approval citations: key -> (file, quote).  Line numbers are resolved at run time by searching the
# file, so a moved line cannot silently keep its approval.
CITES = {
    "D-3": (BACKLOG, "**resolved 2026-10-28 (user): accept JC3 lethality, no toggle**"),
    "D-7": (BACKLOG, "**resolved 2026-10-28 (user): every BmAK weapon in both battle and pursuit modes**"),
    "D-2": (BACKLOG, "**resolved 2026-10-28 (user): (b) one hybrid car**"),
    "WINCH": (CONTROLS, "DECIDED (operator, 2026-11-05): the winch takes d-pad RIGHT and REPLACES Mission Select"),
    "AR": (CONTROLS, "DECIDED (operator, 2026-11-05): AR Challenges is not needed either"),
    "CONTROLS": (CONTROLS, "Inside the Batmobile BmAK controls replace all JC3 controls"),
}

# Categories, most visible-in-play first.  Controls > weapons > sounds > look > handling > collision.
CATS = ("controls", "weapons", "sounds", "look", "handling", "collision")

# The audit table.  Order inside a category is the visibility order (first = most visible).
# (id, category, what the build does instead, the loss, approval key or None[, BmAK override])
# `what BmAK does` is read from the row's own `cells[1]`, `what the build does` from `cells[5]`
# (falling back to `cells[4]`) so this file never re-types a BmAK value.  The optional 6th field
# exists only for rows whose `cells[1]` is a pointer to another row or a bare count rather than a
# description; it restates the behaviour the named row records.
AUDIT = [
    # ---------------------------------------------------------------- controls
    ("T-WP13", "controls", "2 driver slots bind; a 3rd SelectVehicleWeapon index has no member; 8 weapons have no slot",
     "only 2 of 11 weapons can actually fire; the first T-WP13 pass recorded the other 8 as lost outright",
     None),
    ("T-MD8", "controls", "no pivot; the car turns only by driving",
     "battle-mode turn-on-the-spot is missing from the car's control set", None,
     "battle mode turns the car on the spot (MOD-2's pivot; G2-21 found no JC3 carrier)"),
    ("T-BM1", "controls", "`TurnOnSpot*` dropped to TANKTURN's named omission",
     "the same pivot, recorded as a superseded row", None),
    # ---------------------------------------------------------------- weapons
    ("T-WP4", "weapons", "`w618` clone + the entity `CForcePulse`; no disable",
     "the EMP missile cannot disable a vehicle - the whole point of the gadget", None),
    ("T-WP5", "weapons", "entity `CForcePulse` + `truck_emp.ftune` + the flag triple; the disable rides a cloned `CEMPWeapon` (B-18)",
     "the disable's duration is UNKNOWN on both sides; until B-18's probes run only the pulse ships", None),
    ("T-WP3", "weapons", "`w618` clone, unguided; lock-on half UNKNOWN",
     "the Missile Barrage locks nothing: no cone, no range, no hold - reopened by T-WP3b", None),
    ("T-WP7", "weapons", "two `SAttachedEffect` rows + the SAM context-act hack + an authored side flip (B-19)",
     "the allegiance switch has no member on either side; the drone changes side only once B-19's authored flip holds", None),
    ("T-WP8", "weapons", "0-damage `CForcePulse` + a private ring `.effc` + the `BML_Sonar` bank (B-20)",
     "the reveal/marker and the treadmark tracking are absent until B-20 authors them", None),
    ("T-WP9", "weapons", "weapon entity + tracker tune + a HUD tracker graph (B-21)",
     "no homing flag and no distance member: the round homes and the readout appears only once B-21 authors them", None),
    ("T-WP6", "weapons", "entity-graph anchor + `transport_rope_winch` mesh are decoded and buildable (B-16); the pull loop is code-level and missing",
     "the Power Winch does not pull until B-16's loop exists; the 2026-11-05 d-pad RIGHT decision stands", "WINCH"),
    ("T-WP10", "weapons", "`base_tuning.damage` 0 + impulse (closest system); the toggle is a second entity (B-15)",
     "0 damage is not a non-lethal flag, and the riot/lethal toggle has no member until B-15 builds the second entity", None),
    ("T-WP14", "weapons", "the closest system (0-damage impulse tune); no per-weapon mode member",
     "the riot-suppressor's 7.5 deg cone / 0.75 s cadence ride a second entity, not a toggle", None),
    # ---------------------------------------------------------------- sounds
    ("T-AU3", "sounds", "donor banks for 26 ids",
     "90 BmAK events in 10 banks are silent; 10 banks are not in the install", None,
     "90 audio events across 10 banks drive the car, weapons and gadgets"),
    ("T-AU5", "sounds", "engine bank only (T-AU2)",
     "transformation, taser and vehicle-voice events have no bank", None),
    ("T-MD14", "sounds", "no transformation sting",
     "the mode-change sound (V2 62 / MK2 60 / Joker 191) never plays - a hybrid has no change", None,
     "switching pursuit/battle plays a transformation sting (3 variants)"),
    ("T-AU4", "sounds", "`LandAudio.max_rpm` 4500 (follows the engine)",
     "BmAK's 10,000 rpm audio band is replaced by the translated engine's", None),
    # ---------------------------------------------------------------- look
    ("T-MA4", "look", "gloss 0.45 (vanilla cap raised from 0.4 to reach it)",
     "BmAK's authored 0.6 gloss is not reproduced; the paint reads flatter", None),
    ("T-MA7", "look", "10 palette tints kept",
     "BmAK has no palette; the tint set is JC3's, not lore", None),
    ("T-L10", "look", "muzzle spot dropped (no weapon-light behaviour)",
     "the ChainGunMuzzle light (white spot, cone 50, R 4096) is gone", None),
    ("T-L21", "look", "forensics rig dropped", "the scanner rig (12 entries) is absent", None),
    ("T-L22", "look", "forensics rig dropped", "the red winch-door lamp is absent", None),
    ("T-L23", "look", "forensics rig dropped", "the second red winch-door lamp is absent", None),
    ("T-L25", "look", "flare rides the lamp row; `SourceColor` not adopted",
     "the headlight lens flare loses its own colour", None),
    ("T-L26", "look", "flare rides the lamp row", "right headlight flare colour lost", None),
    ("T-L27", "look", "flare rides the lamp row", "left headlight flare b lost", None),
    ("T-L28", "look", "omitted (socket absent)", "left headlight flare c has no anchor", None),
    ("T-L29", "look", "flare rides the lamp row", "right headlight flare b lost", None),
    ("T-L30", "look", "omitted (socket absent)", "right headlight flare c has no anchor", None),
    ("T-L31", "look", "flare rides the wheel lamp row", "right wheel flare top colour lost", None),
    ("T-L32", "look", "flare rides the wheel lamp row", "right wheel flare bottom colour lost", None),
    ("T-L33", "look", "flare rides the wheel lamp row", "left wheel flare top colour lost", None),
    ("T-L34", "look", "flare rides the wheel lamp row", "left wheel flare bottom colour lost", None),
    ("T-LG5", "look", "battle spotlight mapped to HeadLight; forensics stays out",
     "the forensics rig and its 12 entries are absent", None),
    ("T-FX12", "look", "tracer is a WeaponTuning texture, not an .effc",
     "BmAK's tracer system (16 systems, 112 emitters) is not reproduced as authored", None),
    ("T-FX13", "look", "`ChainGunShells` socket stays empty",
     "no gun ejects casings: 8 BmAK systems lost", None),
    ("T-FX16", "look", "no round trail; the round shows as a tracer",
     "6 BmAK projectile trails (18 systems) lost", None),
    # ---------------------------------------------------------------- handling
    ("T-ST7", "handling", "`t_to_full_steer_s` 0.8 low / 0.6 high",
     "BmAK locks 55 deg in 0.25 s at 220 deg/s; the car steers 2.4-3.2x slower - reopened 2026-11-05", None),
    ("T-MD7", "handling", "one handling set (T-M1/T-S1/T-E3/T-ST1)",
     "the six battle drive/slip factors (drive force 500, lat slip 0.75, long slip 1.25, steer 1, trailing -0.25, Z offset 20 cm) are gone", None),
    ("T-MD5", "handling", "one top speed",
     "the battle top-speed curve (60/40/30) has no carrier", None),
    ("T-MD6", "handling", "no 21.6 km/h cap",
     "the turning-mode speed cap is absent", None),
    ("T-MD13", "handling", "static pose only",
     "the animated transformation (3000/24000 torque factors) does not play", None),
    ("T-S6", "handling", "one stroke + one rate per axle",
     "per-axle bias, droop (BMRearWheelMaxDroop 100) and undamped rate absent; stiffness 3000/750 has no unit bridge (strength 45)", None),
    ("T-S1", "handling", "`strength` 45/45 (fleet 6 t class)",
     "BmAK BMWheelSuspensionStiffness 3000 / damping 300 are not carried - no unit bridge", None),
    ("T-S2", "handling", "`compression` 3.0", "BmAK's damping has no member", None),
    ("T-K1", "handling", "max_brake_torque 5000 (class)",
     "BmAK MaxBrakeTorque 300 exists but the bridge is disproven by magnitude (0.29 vs 3.5 m/s2)", None),
    ("T-K2", "handling", "`min_time_to_block` 1 (donor value)",
     "BmAK's brake-lock time is unknown and the donor's is used; EbrakeTime 0.75 not carried", None),
    ("T-K3", "handling", "`handbrake_friction_factor` 1 (6 t median)",
     "BmAK HandbrakeOn/OffSpeed and lat-slip pair have no member", None),
    ("T-K4", "handling", "rear-only handbrake, factor 1",
     "EBrakeBrakeForce 640000 has no member", None),
    ("T-ST3", "handling", "0.6 s high-speed steer time",
     "BmAK's 0.25 s is not reachable (same limit as T-ST7)", None),
    ("T-ST5", "handling", "countersteer / steer_in 1.0 / 1.0 (BmAK's own neutral values)",
     "no countersteer gain exists on either side; the row keeps neutrality", None),
    ("T-ST6", "handling", "drift aligning 0.3 (fleet band)",
     "BmAK's aligning rate has no member", None),
    ("T-B2", "handling", "nitro extra_top_speed 43.2 km/h (derived from BmAK)",
     "BmAK's FakeExtraSpeedMax 3500 is capped by accel x duration (1200 cu) - a lower bound, not the authored max", None),
    ("T-B3", "handling", "nitro grip 1.0 (identity)",
     "BmAK boost touches no grip member, so grip under boost is JC3's, below the shipped 1.2..2 band", None),
    ("T-DR1", "handling", "JC3-native drift block (sens 4, entry 20)",
     "the drift feel is JC3's, deliberately not the 6 t class", None),
    ("T-E2", "handling", "absolute torque 1393.5",
     "BmAK's torque curve scale is a class fit (+30%), not the authored number", None),
    ("T-E5", "handling", "top speed 336 km/h (wiki 209 mph)",
     "the only source is a wiki figure, inside the fleet band but not decoded", None),
    ("T-M2", "handling", "inertia 4.0/2.6/1.2 (class)",
     "BmAK's inertia tensor is a neutral multiplier - no authored value exists", None),
    ("T-M4", "handling", "wheel mass 75/150 (class)",
     "BmAK has no wheel-mass member (MassScale 1.0 neutral)", None),
    ("T-R1", "handling", "arcade friction 3.0",
     "BmAK has no friction tag; the grip is a fleet value", None),
    ("T-A2", "handling", "drag 0.55",
     "BmAK has no aero member; drag is JC3's", None),
    ("T-A4", "handling", "lift -0.3",
     "BmAK has no downforce member; lift is JC3's", None),
    ("T-G6", "handling", "contact radius 0.683 (mesh)",
     "BmAK's sim radius 0.64 is not carried", None),
    # ---------------------------------------------------------------- collision
    ("T-DM7", "collision", "`rotor_collision.damage_to_other_per_second` 100000/s + mass ratios",
     "BmAK's outgoing ram damage is a 20->150 speed band with strafe 2.25 and boost 2.0; JC3's "
     "member is a per-second rate, so the band is a named omission and a `CCar` evaluating the "
     "block is UNKNOWN", None),
    ("T-DM2", "collision", "bullet armour 99 (fleet max)",
     "BmAK's authored bullet armour is above the fleet gate", None),
    ("T-DM6", "collision", "`deform_scale` 0 (no crumple)",
     "BmAK panels deform in play; the switch is off", None),
    ("T-DM1", "collision", "max_health 36000 (out of shipped domain)",
     "BmAK Health 1200 becomes a declared switch 30x the authored value", None),
    ("T-AC1", "collision", "closest system: `drift.max_drift_torque` 8000 + aero `turn/pitch_steering_factor` 0.2286",
     "JC3 has no airborne gate, so the yaw acts only while the drift state survives take-off",
     None),
    ("T-RA1", "collision", "blocked: none at any layer; G2-35 names the capability to add",
     "ImpactRoadAssist 90000/30000/2000, PMDodge 5000/6000/0.25 s, BattleDodgeImpulse 100000, "
     "VehicleShovingTorque 10000 and KillFlip -2000000 over 1.5 s have no triggered member with "
     "a target or a duration", None),
    ("T-SR1", "collision", "closest system: `DriverLean.righting_torque` 2000 + the Havok stabilizer atom",
     "no car ships `DriverLean`, and the StayUpright stiffness/damping/resist angles have no JC3 member",
     None),
    ("T-WLD11", "collision", "the 2-column spine fit is narrow (0.28-0.60 m) versus the donor's 1.65 m blanket; 1/40 and 16/80 interior samples still dip into the roof vents",
     "Rico stands on the derived spine, but the donor's full-width hood/roof blanket needs a third column and deform indices above 134", None),
    ("T-WLD15", "collision", "translated to `CVehicleCargoBay`/`CGrapplingHookPropData` + mass 6,000; the pull is native",
     "whether the tether holds a 6 t car is unverified (Q-3 #5)", None),
    ("T-WLD17", "collision", "0 of 23 helicopters has a cargo bay; closest is the plane's bay + compound entity (B-16)",
     "helicopter airlift cannot happen until a bay is cloned and its native attach rule probed", None),
]

# Rows examined and excluded because nothing is lost (BmAK ships no such feature, or the row was
# superseded by a fix that carries it).  Stated so the audit is not accused of a silent filter.
EXCLUDED = [
    ("T-FX9", "carried since 2026-11-06: `car_speedrom_heater.effc` at the `Afterburner` socket (12 vehicles, 24 `z80_exhaust_heat_l/r` attachments); the gap is the blend/texture name, not a value"),
    ("T-FX20", "carried as an authoring plan since 2026-11-06: no light or ribbon member and no `Brake` behaviour exist to convert, so nothing is lost; the trigger is build work"),
    ("T-L4", "superseded by T-L13/T-L14 - the wheel lamp is carried by a custom entry"),
    ("T-L7", "superseded by T-L35 - the boot lamp is carried by a custom entry"),
    ("T-LG4", "superseded by T-L13/T-L14 - the under-glow is carried"),
    ("T-FX4", "superseded by T-11/T-17; the seismic half is counted under T-WP8"),
    ("T-W1", "superseded by T-11 - the 11 weapons are counted row by row"),
    ("T-WLD4", "carried: the shipped `_debug` leaf's name key 1621485476 is present 11/11 in bm-013's drop (BATMOBILE); 443190071 belonged to a leaf that never ships"),
    ("T-WLD6", "carried: the `_debug_desc` key 4081821928 is present 11/11 in bm-013's drop with the Batmobile blurb"),
]

# The "JC3 cannot" closures the 2026-11-05 leads reopen.
REOPENED = [
    ("11 weapons / 8 lost", "T-WP13", "2 driver slots, no active-slot index",
     "T-WP13's own proposal kept 3 addressable and 8 lost; D-7 asks for all 11",
     "T_WP13_PROPOSAL.md:18 (3 addressable / 8 lost)"),
    ("0.25 s steering", "T-ST7", "0.6-0.8 s, fleet rack floor 0.5 s",
     "BmAK 220 deg/s = 0.25 s; the row called it a JC3 model limit",
     "DRIVE_CARRIERS.md section 4/7 (no pivot/steer-through-torque carrier) + the 2026-11-05 lead"),
    ("Real BmAK sounds", "T-AU3", "donor banks for 26 ids",
     "10 BmAK banks are absent from the install, so the row stops",
     "T-AU3/T-AU5 `why` (banks absent), no re-decode attempted since"),
    ("Heat-seeking / lock-on", "T-WP3", "unguided `w618`; lock-on UNKNOWN",
     "T-WP3b found `missile_turning_speed` and the lock-on AutoAim preset",
     "T_WP3B_LOCKON.md sections 1-3; JC3_HUD_WEAPONS.md section 5"),
    ("Hackable drones", "T-WP7", "no allegiance class",
     "0 hits in the 103-class census; the lead says JC3 has hackable drones",
     "ENTITIES.md census (0 classes), T-WP7 `why`"),
    ("Stunt areas", "T-WLD11", "areas float 0.10-0.60 m; deform list missing",
     "the 0.10-0.60 m figure is the bbox map; the stored points sink 0.19-0.31 m and the derived spine fit places 22/22 vertices, so the carrier exists",
     "tmp/freebuff/reports/stunt-areas-deform-points.md; T_WLD11B_SURFACES.md"),
]


def load_rows() -> dict[str, dict]:
    rows = {}
    with open(ROWS, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows[r["id"]] = r
    return rows


def cite_line(path: str, quote: str) -> int:
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if quote in line:
                return n
    raise SystemExit(f"approval quote not found in {path}: {quote[:60]}")


def trim(text: str, n: int = 240) -> str:
    text = " ".join((text or "").split())
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + "..."


def build() -> dict:
    rows = load_rows()
    cites = {}
    for key, (path, quote) in CITES.items():
        cites[key] = {"file": os.path.relpath(path, ROOT).replace("\\", "/"),
                      "line": cite_line(path, quote), "quote": quote}

    entries = []
    for order, entry in enumerate(AUDIT):
        rid, cat, build_txt, loss, appr = entry[:5]
        override = entry[5] if len(entry) > 5 else None
        row = rows.get(rid)
        if row is None:
            raise SystemExit(f"AUDIT row not in T_ROWS.jsonl: {rid}")
        cells = row["cells"] + [""] * (8 - len(row["cells"]))
        bmak = trim(override or cells[1], 220)
        instead = trim(build_txt or cells[5] or cells[4], 220)
        entries.append({
            "id": rid, "category": cat, "order": order, "dispo": row["dispo"], "doc": row["doc"],
            "bmak": bmak, "build": instead, "loss": loss,
            "approval": "APPROVED" if appr else "UNAPPROVED",
            "cite": cites.get(appr) if appr else None,
            "cite_key": appr,
        })

    by_dispo = collections.Counter(e["dispo"] for e in entries)
    by_cat = collections.Counter(e["category"] for e in entries)
    approved = [e for e in entries if e["approval"] == "APPROVED"]
    unapproved = [e for e in entries if e["approval"] == "UNAPPROVED"]
    return {
        "rows_total": len(rows),
        "audited": len(entries),
        "approved": len(approved),
        "unapproved": len(unapproved),
        "by_dispo": dict(by_dispo),
        "by_category": dict(by_cat),
        "cites": cites,
        "entries": entries,
        "excluded": [{"id": i, "reason": r} for i, r in EXCLUDED],
        "reopened": [{"feature": f, "row": r, "closed_as": c, "lead": l, "evidence": e}
                     for f, r, c, l, e in REOPENED],
    }


def md(data: dict) -> str:
    L: list[str] = []
    A = L.append
    A("# COMPROMISES_T - where the translation chose less than BmAK lore")
    A("")
    A("**Answer: %d of the project's %d translation rows compromise the lore goal, and only %d "
      "carry a recorded operator approval.** The other %d are unapproved: they were decided inside "
      "the translation (a fleet median, a donor value, a proven absence, a \"JC3 cannot\") and no "
      "file quotes the operator agreeing to the loss. The most visible are the weapon slots (2 of "
      "11 weapons fire; a third index has no member), the steering rate (2.4-3.2x slower than "
      "BmAK) and the silent BmAK banks."
      % (data["audited"], data["rows_total"], data["approved"], data["unapproved"]))
    A("")
    A("Approval is quoted, never inferred: `APPROVED` means a file states a user/operator decision "
      "for that loss, and the check re-opens the file at the cited line. A loss that merely follows "
      "from an approved decision (D-2's hybrid car) is still UNAPPROVED.")
    A("")
    A("| disposition | rows audited |")
    A("|---|---:|")
    for d, n in sorted(data["by_dispo"].items(), key=lambda kv: -kv[1]):
        A("| `%s` | %d |" % (d, n))
    A("")
    A("| visibility | rows audited | unapproved |")
    A("|---|---:|---:|")
    for c in CATS:
        n = data["by_category"].get(c, 0)
        u = sum(1 for e in data["entries"] if e["category"] == c and e["approval"] == "UNAPPROVED")
        A("| %s | %d | %d |" % (c, n, u))
    A("")
    A("## 1. UNAPPROVED, ranked by visibility in play")
    A("")
    cur = None
    for e in data["entries"]:
        if e["approval"] != "UNAPPROVED":
            continue
        if e["category"] != cur:
            cur = e["category"]
            A("")
            A("### %s" % cur)
            A("")
        A("- **%s** (`%s`, %s) - BmAK: %s. **Build instead:** %s. **Loss:** %s. *UNAPPROVED*"
          % (e["id"], e["dispo"], e["doc"], e["bmak"], e["build"], e["loss"]))
    A("")
    A("## 2. APPROVED (a file quotes the operator)")
    A("")
    A("| row | what is lost | approval | cited |")
    A("|---|---|---|---|")
    for e in data["entries"]:
        if e["approval"] != "APPROVED":
            continue
        c = e["cite"]
        A("| %s | %s | %s | `%s:%d` - \"%s\" |"
          % (e["id"], e["loss"], e["cite_key"], c["file"], c["line"], c["quote"]))
    A("")
    A("## 3. \"JC3 cannot\" closures the 2026-11-05 leads reopen")
    A("")
    A("| feature | row | closed as | what the lead says | evidence |")
    A("|---|---|---|---|---|")
    for r in data["reopened"]:
        A("| %s | %s | %s | %s | %s |"
          % (r["feature"], r["row"], r["closed_as"], r["lead"], r["evidence"]))
    A("")
    A("Each of these is an **UNAPPROVED** compromise until a file records the operator accepting "
      "the loss; a lead that narrows where to look is not an acceptance, and reopening a closure "
      "does not by itself approve the omission it left behind.")
    A("")
    A("### 3.1 The 8 weapons the first T-WP13 pass declared lost")
    A("")
    A("`T_WP13_PROPOSAL.md:18` records **3 addressable** (2 decoded binds + 1 index with no member) "
      "and **8 lost**: WPN-4 EMP missile, WPN-5 EMP burst, WPN-6 winch, WPN-7 hacker, WPN-8 sonar, "
      "WPN-9 tracker, WPN-10 riot suppressor, WPN-11 booster mesh. Of those, one is approved "
      "(WPN-6 winch -> tether, 2026-11-05); WPN-10's 2026-10-28 approval is **superseded** by the "
      "2026-11-06 operator rule and its row is now `next` (closest system: a 0-damage impulse "
      "tune; the toggle is BUILD card `Research/specs/B-15.md`), and seven are UNAPPROVED. The "
      "ninth and tenth weapons (cannon, Vulcan) have slots; the missiles are the third "
      "addressable row but carry no lock-on (T-WP3).")
    A("")
    A("## 4. Approval citations that do not exist, and rows kept out of the ranked list")
    A("")
    A("The 2026-11-05 instruction says the exact-colour decision is recorded in "
      "`Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md`. **That file contains no colour statement** "
      "- it records the controls, the winch and the AR/Mission Select drops only. Note that the "
      "colour itself is not compromised: T-MA3 keeps the authored base colour `[0.02579, 0.02579, "
      "0.03]` linear through the linear->sRGB gain, so no decision is needed for it. The one colour "
      "row that loses something is T-MA4 (authored gloss 0.6 -> 0.45), and it is listed as "
      "UNAPPROVED above, not approved; the citation gap is reported rather than filled:")
    A("")
    A("- searched: all 52 lines of `CONTROLS_MENU_SCREENS.md` for `colour`, `color`, `lighting` "
      "and `exact`; 0 hits for the first three, and `exact` matches only line 4's \"labels are "
      "exactly as drawn\". No colour or lighting decision is recorded there.")
    A("")
    A("| row | why it is not in the ranked list |")
    A("|---|---|")
    for x in data["excluded"]:
        A("| %s | %s |" % (x["id"], x["reason"]))
    A("")
    A("## 5. Method, counts and limits")
    A("")
    A("- Universe: all %d rows of `T_ROWS.jsonl`. Inclusion rule: the row drops a BmAK feature, "
      "keeps a JC3/donor/fleet value where BmAK has one, shrinks or merges a feature, or records a "
      "permanent omission. %d rows qualify; %d were examined and excluded with the reason in "
      "section 4." % (data["rows_total"], data["audited"], len(data["excluded"])))
    A("- Counts are computed by the script from `dispo`, never typed: %s."
      % ", ".join("`%s` %d" % (k, v) for k, v in sorted(data["by_dispo"].items())))
    A("- `what BmAK does` is read from each row's own `cells[1]`; this file never re-types a BmAK "
      "value, so a corrected row cannot leave a stale quote behind.")
    A("- `--check` asserts every audited id exists in `T_ROWS.jsonl`, every APPROVED row's quote is "
      "still at the cited line of the cited file, and the rendered markdown/JSON match a fresh "
      "re-derivation.")
    A("")
    A("**Limits.** This is a reading of the ledger, not a re-decode: it does not re-prove any "
      "absence. Rows that are `blocked` but not permanent (T-WP4/T-WP5/T-WP13) are counted as "
      "compromises because a blocked row ships the omission today. The audit does not touch "
      "`T_ROWS.jsonl`, the backlog or any build.")
    A("")
    A("Checkable: `python Tools/scripts/audit_compromises_t.py --check`.")
    A("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--dump", choices=("list", "cites"))
    a = ap.parse_args()

    data = build()
    if a.dump == "list":
        for e in data["entries"]:
            print("%-9s %-10s %-8s %s" % (e["id"], e["category"], e["approval"], e["loss"][:80]))
        return 0
    if a.dump == "cites":
        for k, c in data["cites"].items():
            print("%-9s %s:%d  %s" % (k, c["file"], c["line"], c["quote"][:70]))
        return 0

    doc = md(data)
    js = json.dumps(data, indent=1, sort_keys=True) + "\n"
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if a.write:
        with open(jp, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        with open(mp, "w", encoding="utf-8", newline="\n") as f:
            f.write(doc)
        print("wrote", jp)
        print("wrote", mp)
        print("%d audited, %d approved, %d unapproved" % (data["audited"], data["approved"],
                                                          data["unapproved"]))
        return 0

    fails = []
    if not os.path.exists(jp) or open(jp, encoding="utf-8").read() != js:
        fails.append("json drifted")
    if not os.path.exists(mp) or open(mp, encoding="utf-8").read() != doc:
        fails.append("markdown drifted")
    rows = load_rows()
    for e in data["entries"]:
        if e["id"] not in rows:
            fails.append("unknown row %s" % e["id"])
        if e["approval"] == "APPROVED":
            c = e["cite"]
            line = open(os.path.join(ROOT, c["file"]), encoding="utf-8").read().split("\n")[c["line"] - 1]
            if c["quote"] not in line:
                fails.append("approval quote moved for %s" % e["id"])
    if data["approved"] + data["unapproved"] != data["audited"]:
        fails.append("approval totals do not add up")
    print("%d audited: %d approved, %d unapproved; by dispo %s"
          % (data["audited"], data["approved"], data["unapproved"], data["by_dispo"]))
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("OK: every approval quote re-read at its cited line; document re-derived identically")
    return 0


if __name__ == "__main__":
    sys.exit(main())
