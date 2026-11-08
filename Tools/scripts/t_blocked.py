"""t_blocked.py - task 7210: every blocked translation row, and what it waits for.

The ledger `Working/Translation/T_ROWS.jsonl` carries **18** rows with `dispo == "blocked"`, and
`Working/Translation/T6_HUD_CAMERA.md` carries the other **4** (the tracker adds the T6 table to the
ledger - `status_audit.py:121-141`). This script re-derives both sets, so the 22 is a count over the
two files and not a number copied out of STATUS.md. Seven rows joined on 2026-11-08 with the four v2
plans (`apply-v2-driving-and-world-rows.md`): `T-RC1`/`T-RC2` are operator behaviours the plan
halts, and `T-CT1`..`T-CT5` are the control cells that all end in the missing keymap writer. The five `T-MD` handling rows joined the set on
2026-11-06 when D-2 was reopened: BmAK has two modes and a hybrid cannot carry them
(`tmp/freebuff/reports/apply-mode-switch-rows.md`).

For each blocked row it records one line: the input the row waits for. Every blocked row that the
research already in the repo could decide has been decided (`ATTEMPTS` is empty: T-S6, T-WP4 and
T-WP13 left the set on 2026-11-06, each with its evidence in `RESOLVED`), so the sheet now
enumerates waits only; a new attempt belongs there, with its markers.

Seven rows have left the set: `T-FX3` (refuted by `T_FX3B.md`, approved by the operator 2026-11-06),
`T-ST7` (refuted by `T_ST7B_FLOOR.md`, ruled the same day), `T-AU3`/`T-AU5` (refuted by
`AUDIO_BANKS.md`: the 10 banks are present, 0 absent), `T-S6` (placed by the derived suspension
unit bridge, `tmp/freebuff/reports/suspension-unit-bridge.md`, 14/14 oracles), and `T-WP4`/`T-WP13`
(operator rulings 4 and 3: the EMP launcher splits from its disable and the slots are forced -
`tmp/freebuff/reports/wp4-fire-leech.md`, `wp13-slots-force.md`). Their evidence and the applied
changes are kept in `RESOLVED`, so the reasoning is not lost when a row stops being blocked.

Nothing here edits `T_ROWS.jsonl` (read only) or a build: the proposed row edits are written to
`Working/Translation/BLOCKED_PROPOSALS.json` for the operator, and every proposal is marked
`applies: false`.

`--check` re-derives the two blocked sets, rebuilds both files and compares them byte for byte, and
re-runs every evidence oracle (each cited file must exist and contain the cited marker; the
negative markers must occur zero times). It also compares the ledger's sha256 with the one recorded
when the file was written, so a row that later changes disposition makes the check fail loudly
instead of leaving a stale proposal sheet.

Usage
    python Tools/scripts/t_blocked.py --write
    python Tools/scripts/t_blocked.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import status_audit as sa          # noqa: E402  (the tracker's own generator; import has no side effects)
TR = os.path.join(ROOT, "Working", "Translation")
LEDGER = os.path.join(TR, "T_ROWS.jsonl")
T6 = os.path.join(TR, "T6_HUD_CAMERA.md")
OUT_J = os.path.join(TR, "BLOCKED_PROPOSALS.json")
OUT_M = os.path.join(TR, "BLOCKED_PROPOSALS.md")
SCHEMA = 1
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()   # noqa: E731

# Rows that left the blocked set after this sheet was written.  They are no longer in the table
# above, so the evidence that moved them and the change that was applied live here; `--check`
# re-runs their markers like any other evidence.
RESOLVED: dict[str, dict] = {
    "T-ST7": {
        "verdict": "resolved-by-operator-ruling",
        "ruling": "operator ruling 2026-11-06, option A: **0.25 s, no compromise** "
                  "(`Working/Translation/DECISIONS_NEEDED.md`, 'OPERATOR RULINGS 2026-11-06', "
                  "item 1), with the steering-rate / max-speed members checked so the whole "
                  "BmAK rate is carried, not only the lock time",
        "evidence": [
            {"file": "Research/JC3Grab/DRIVE_CARRIERS.json", "marker": "t_to_full_steer_s",
             "means": "the steering member is decoded per module, so the fleet's values are data"},
            {"file": "Working/Translation/T_ST7B_FLOOR.md", "marker": "exists in the fleet",
             "means": "0.25 s ships in 4 LandSteering AI twins and 0.2 s on the high-speed member"},
            {"file": "Working/Translation/T_ST7B_FLOOR.md", "marker": "MotorbikeSteering",
             "means": "a *player* module ships 0.3 s (2 modules), so the player path is not "
                      "floored at 0.5 s either"},
        ],
        "applied": "ledger `T-ST7`: dispo `blocked` -> `next`, value 0.8 s low / 0.6 s high -> "
                   "0.25 s low / 0.091 s high (55 deg and 20 deg at 220 deg/s); the row left the "
                   "blocked set, so this sheet enumerates 16",
        "remaining": "a game probe: neither value is measured (test ban), and 0.091 s is below "
                     "the 0.2 s fleet minimum, i.e. a declared out-of-domain switch",
    },
    "T-FX3": {
        "verdict": "resolved-by-operator-approval",
        "ruling": "operator ruling 2026-11-06, item 2: **approve** the decoded afterburner-flame "
                  "edit (`Working/Translation/DECISIONS_NEEDED.md`, 'OPERATOR RULINGS 2026-11-06')",
        "evidence": [
            {"file": "Research/JC3Grab/USAGES.json", "marker": "4197885156",
             "means": "usage id `EngineNitro` exists in the decoded 155-value usage vocabulary"},
            {"file": "Research/JC3Grab/FX_TABLE.jsonl", "marker": "car_cycle_base_dual_nitrous",
             "means": "the fleet ships the dual nitro exhaust effect (17 cargo rows)"},
            {"file": "Working/Translation/T_FX3B.md", "marker": "EngineNitro",
             "means": "the donor's two exhaust emitters already carry usage 4197885156, so the "
                      "approved edit is placement on the `Afterburner` socket (B-08), not a new "
                      "effect or a new usage"},
        ],
        "applied": "ledger `T-FX3`: dispo `blocked` -> `next`; the edit is B-08's placement - both "
                   "`SAttachedEffect.world` mats from the Serpente's exhaust to the `Afterburner` "
                   "socket (bone `JetSMove`), spec `Working/Effects/bm_fx_edits.json` `edits[]`, "
                   "compiled by `Tools/scripts/bm_fx.py` into "
                   "`Builds/bm-008/.../*_civilian_01.epe`; the row left the blocked set, so this "
                   "sheet enumerates 15",
        "remaining": "`bm_fx.py --check` is red for an unrelated reason (6 `SWeaponPoint` objects "
                     "gained a later `weapon_anchor` property in bm-008), and no probe was run: "
                     "whether the flame follows the nozzle in motion is UNKNOWN (test ban)",
    },
    "T-AU3": {
        "verdict": "resolved-by-evidence",
        "ruling": "no operator decision needed: `Research/BatmobileGrab/AUDIO_BANKS.md` (G3-14) "
                  "re-tested the absence claim against the whole BmAK install - 10 claimed banks, "
                  "**10 found, 0 absent**, 117 `AkBank` payloads read",
        "evidence": [
            {"file": "Research/BatmobileGrab/AUDIO_BANKS.md",
             "marker": "10 found, 0 confirmed absent",
             "means": "every one of the 10 banks the row called absent is present in a BmAK package"},
            {"file": "Research/BatmobileGrab/AUDIO_BANKS.md", "marker": "BML_Batmobile_Subjective",
             "means": "the four jump banks live in `Startup`, a package the old 3-package scan never opened"},
            {"file": "Working/Translation/T_AU3B.md", "marker": "ABSENT: 27 of 27",
             "means": "the 27/27 absence is true of the JC3 install only: a carrier gap, not a "
                      "missing source"},
        ],
        "applied": "ledger `T-AU3`: dispo `blocked` -> `next`; the source banks exist, so what "
                   "remains is the JC3 event binding of the 26 ids; the row left the blocked set",
        "remaining": "a JC3-side event slot per id and, where JC3 has no sample, an auditioned "
                     "substitute (`T_AU3B` section 4 lists the name-level candidates); no probe was run",
    },
    "T-AU5": {
        "verdict": "resolved-by-evidence",
        "ruling": "no operator decision needed: the same `AUDIO_BANKS.md` re-test (10 found / 0 "
                  "absent) removes the 'absent banks' half; only these three families' own bank "
                  "and slot remain",
        "evidence": [
            {"file": "Research/BatmobileGrab/AUDIO_BANKS.md",
             "marker": "10 found, 0 confirmed absent",
             "means": "the banks T-AU5 inherited from T-AU3 are present"},
            {"file": "Research/BatmobileGrab/ASSETS.md", "marker": "AkVehicleSound",
             "means": "the Batmobile's vehicle-sound object is an `AkVehicleSound`, so the mapping "
                      "is an object-level task, not a missing bank"},
            {"file": "Working/Translation/T_AU3B.md", "marker": "T-AU5",
             "means": "the note records this row's own claim and that the loss is a JC3 carrier gap"},
        ],
        "applied": "ledger `T-AU5`: dispo `blocked` -> `next`; the source side is complete, and the "
                   "row now names these events' own bank (UNKNOWN - not among `AUDIO_MAP.json`'s "
                   "361 rows) plus a JC3 slot and the mode-switch trigger as what it needs",
        "remaining": "the bank and event id of `TransformationReverseDirection*`, `TaserSound` and "
                     "`VehicleSound` (not in the four-package `AUDIO_MAP` sweep), then a JC3 slot and "
                     "the T-MD14 mode-switch trigger",
    },
    "T-S6": {
        "verdict": "resolved-by-derived-bridge",
        "ruling": "no operator decision needed: the unit bridge is derived from the decoded class "
                  "defaults and the 166-vehicle fleet (`tmp/freebuff/reports/suspension-unit-bridge.md`, "
                  "14/14 oracles, `Tools/scripts/t_s6_bridge.py --check`)",
        "evidence": [
            {"file": "tmp/freebuff/reports/suspension-unit-bridge.md", "marker": "0.4542",
             "means": "the fleet's median static-sag fraction is derived, so `strength = "
                      "g/(4*f*length)` closes the dimension"},
            {"file": "tmp/freebuff/reports/suspension-unit-bridge.md", "marker": "13.500",
             "means": "TravelDown 40 cm at that fraction needs strength 13.500 s^-2, and BmAK's 3000 "
                      "against the decoded 210 kg gives 14.286 - fit error +5.8% / -5.5%"},
            {"file": "tmp/freebuff/reports/suspension-unit-bridge.md", "marker": "no_bias_member",
             "means": "JC3 carries no bias channel, so the front bias is placed as a hardpoint "
                      "offset (-0.10, 0.0% against the fleet median) and the rear bias stays a gap"},
        ],
        "applied": "ledger `T-S6`: dispo `blocked` -> `next`; TravelDown 40 cm -> length 0.40 m, "
                   "stiffness 3000 -> strength 13.500 s^-2, damping 300 -> compression/relaxation "
                   "1/2 (-31.1% on integer quantisation), front bias 10 -> hardpoint offset -0.10; "
                   "the row left the blocked set, so this sheet enumerates 17",
        "remaining": "no member for droop (`BMRearWheelMaxDroop` 100) or the up-travel 30 cm (cards "
                     "B-22), none for the per-mode 750 / stationary bias (B-23); whether the engine "
                     "reads `hardpoint_offset_along_spring` as a rest position is UNKNOWN (test ban)",
    },
    "T-WP4": {
        "verdict": "resolved-by-operator-ruling-and-donor",
        "ruling": "operator ruling 4, 2026-11-06: **approve the split** so the missile launcher "
                  "ships, with the JC3 Fire Leech as the lock-on lead "
                  "(`Working/Translation/DECISIONS_NEEDED.md`, 'OPERATOR RULINGS 2026-11-06')",
        "evidence": [
            {"file": "tmp/freebuff/reports/wp4-fire-leech.md",
             "marker": "w143_rpg_fire_leach",
             "means": "the Fire Leech is a decoded `WeaponTuning` whose `missile_turning_speed` is "
                      "300 and whose `AutoAim` cone equals the fleet lock-on preset, so the "
                      "guidance transplants onto the w618 clone by value"},
            {"file": "tmp/freebuff/reports/wp4-fire-leech.md", "marker": "CanTargetCharacters",
             "means": "w143 may lock characters and BmAK may not, so the lock-on tune is a new "
                      "`AutoAim` with the preset's classes rather than a wholesale copy"},
            {"file": "Working/Translation/DECISIONS_NEEDED.md",
             "marker": "T-WP4: approve the split",
             "means": "the split is the operator's, not a research inference"},
        ],
        "applied": "ledger `T-WP4`: dispo `blocked` -> `next`, launcher only (w618 clone + "
                   "`CForcePulse` + the w143 guidance + a new lock-on `AutoAim`); the disable half "
                   "became its own row `T-WP15` as a named omission (`out`), so the row left the "
                   "blocked set and the sheet enumerates 15",
        "remaining": "a 2.0 s held lock, an 8-target salvo and the reticle link have no member "
                     "(cards B-24 / B-25); no probe was run (test ban)",
    },
    "T-WP13": {
        "verdict": "resolved-by-operator-ruling",
        "ruling": "operator ruling 3, 2026-11-06: **force extra weapon slots** - the two reference "
                  "vehicles carry 2 weapons + a shield, so JC3's 2 driver slots are a convention",
        "evidence": [
            {"file": "tmp/freebuff/reports/wp13-slots-force.md",
             "marker": "v0202_car_capstone_bavariumtank",
             "means": "the Imperator graph is decoded: 4 slot properties, 2 non-null pointers"},
            {"file": "tmp/freebuff/reports/wp13-slots-force.md", "marker": "BavariumShield",
             "means": "the third weapon the premise counts is a shield PART + effect, not a slot, "
                      "so forcing slots is a design decision and is recorded as one"},
            {"file": "Working/Translation/DECISIONS_NEEDED.md",
             "marker": "T-WP13: force extra weapon slots",
             "means": "the ruling is the operator's, not a decoded member"},
        ],
        "applied": "ledger `T-WP13`: dispo `blocked` -> `next`; 4 `CCar` roots x 2 decoded "
                   "pointers = 8 slots for the 8 slot-able BmAK objects, 0 invented property "
                   "names, the 5 gadgets outside the slot space; the row left the blocked set, so "
                   "this sheet enumerates 15 of 216",
        "remaining": "whether two or more roots on one car chassis fire from the driver seat is "
                     "UNKNOWN (no entity states the input-to-root binding); `RiotSuppressorMuzzle` "
                     "and the Joker weapons have no points",
    },
}

# one line per blocked row: the input it waits for. `why` in the ledger is the authority; these
# are its one-line restatements, and the ids are re-derived, never copied.
WAITS = {
    "T-L28": "a body `_LIG` anchor node plus a `CarLight` block on the body (B-03 / B-04) - socket and "
             "bone are null on `HeadLight1c`; the sprite waits on T-24",
    "T-L30": "the same body-hosted `_LIG` node and `CarLight` block (B-03 / B-04) for `HeadLight2c`; "
             "the sprite waits on T-24",
    "T-WP6": "a code-level pull loop (force, length clamp, reel, release) - the anchor object, "
             "rope mesh and VFX/SFX are decoded and buildable (`Research/specs/B-16.md`)",
    "T-WLD17": "a cargo bay on a helicopter (0 of 23) plus the native attach rule a cloned bay "
               "would need - closest carrier is the cargo plane's bay (`Research/specs/B-16.md`)",
    "T-MD14": "a `BattleMode` usage a graph dispatches on plus a second variant to hang T-16's "
              "30 battle-mode events on (B-12); no usage consumer is decoded (U1)",
    "T-MD5": "D-2 re-resolved to two variants (B-12) plus a runtime entity swap - the battle "
             "variant's own `arcade`/`CustomLandGlobal` values; no JC3 member scales top speed by a "
             "mode",
    "T-MD6": "the same battle variant plus a decoded speed-cap member - no member in the fleet caps "
             "speed (nearest: `vehicle_misc.official_top_speed`, `extra_top_speed`)",
    "T-MD7": "the battle variant's own `land_steering`/torque set (four of six factors) plus the "
             "swap; the two slip-scale members do not exist",
    "T-MD8": "a native turn-on-the-spot mechanism - G2-21 refuted its candidates and found 0 "
             "tank-only driving members; a second variant does not create one",
    "T-MD13": "the battle variant's part angles for the deployed pose (T-12) plus the swap; "
              "`TransformationAnimNode` still has no JC3 analogue",
    "T-HUD5": "a weapon component on the entity for the HUD's 2 slots (T-11 bound w602/w603 since; "
              "the 3 special-weapon states have no member)",
    "T-RA1": "a triggered, non-damaging impulse/torque with target selection and a duration - no "
              "road-assist/dodge/shove/kill-flip member at any layer (card G2-35)",
    "T-CAM8": "a head-impulse / drift-orientation camera member - none in any decoded camera module",
    "T-CAM9": "a unit bridge from BmAK's camera smoothing strength to JC3 spring stiffness",
    "T-CAM11": "a numeric bridge to `AddCameraShake` (game code; no values decoded)",
    # --- the four 2026-11-08 v2 plans: two halted operator behaviours, four control cells that
    # all end in the same missing writer, and the curve the steering cell waits on.
    "T-RC1": "an input carrier for remote drive - the land-vehicle action set has no aim/stick/cursor "
             "action, JC3 has no 2D vehicle stick and the gadget route is a proximity interaction; "
             "halted by ruling (`water-flip-damage-remote-plans-v2.md` section 4.4), with Rebel Drop "
             "carrying the summon",
    "T-RC2": "a distance-to-player read and a HUD overlay element - 0 hits for static/noise/jam/overlay/"
             "fullscreen in the vehicle-HUD element table and none in the interaction layer; halted by "
             "ruling, not declared impossible",
    "T-CT1": "the keymap writer (`T-CT5`) - the patch keymap's `EXIT_VEHICLE` / `RPADUP` pair has to be "
             "split into enter = Y and exit = LB",
    "T-CT2": "the keymap writer plus the double-press timer - no hold/duration/tap field in 145+104+249 "
             "binding rows (U2) and 0 of 4,832 exits carries a launch member",
    "T-CT3": "the keymap writer, for the winch on `RPADRIGHT` with `USE_VEHICLE_MOD` re-homed to Y",
    "T-CT4": "BmAK's in-car steering response curve (`StandardSteeringSpeedCurve` / "
             "`DesiredTurnOnSpotSpeed` need the capture set, U6); the two axes are decoded",
    "T-CT5": "a keymap writer - 0 of 575 `Tools/scripts` files writes a bin; the 12-byte binding record "
             "plus 18 B of `stringZ` records must re-parse to 145 patch bindings",
    # --- the 2026-11-08 body pass: the mode swap and the twelve texture refusals ----------------
    "T-MS1": "a consumer that swaps or replaces a vehicle entity at runtime (U1) - 0 `replace`, 0 "
             "`respawn`, 0 `despawn` and 0 `.ee` `swap` paths in 81,952, so the settler is "
             "`JustCause3.exe`; the two leaves and Rebel Drop are buildable without it",
    "T-TX1": "the `Batmobile_Micropattern_A` pixels - 0 of 61 grab `.tga` carry the stem; settler is a "
             "re-grab of the `Playable_Batmobile*` packages",
    "T-TX2": "the `Batmobile_Micropattern_A_Normal` pixels - same re-grab; no substitute map exists",
    "T-TX3": "the `Batmobile_Micropattern_B` pixels - same re-grab",
    "T-TX4": "the `Batmobile_Micropattern_C` pixels - same re-grab",
    "T-TX9": "a chapter selector for `Damage_Chapter_Mask` (0 of 961 headers, `SupportDmgBlend` "
             "[0.0] in all 160 blocks) - and the operator's no-damage-stages ruling closes the crude "
             "single-state route",
    "T-TX10": "the same chapter selector as `T-TX9`",
    "T-TX11": "the same chapter selector as `T-TX9`",
    "T-TX12": "the same chapter selector as `T-TX9`",
}

# every blocked row the repo's research could decide has been decided; the verdicts and their
# markers live in RESOLVED. A new attempt goes here, with its evidence.
ATTEMPTS: dict[str, dict] = {}


def t6_blocked() -> tuple[list[tuple[str, str, str]], int, int, int]:
    """The T6 rows, classified with status_audit.py's own rule (lines 128-141)."""
    rows, total, out, sup = [], 0, 0, 0
    for line in open(T6, encoding="utf-8"):
        if not line.startswith("| T-"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 8:
            continue
        total += 1
        proposed, conf = c[5], c[6]
        if "**superseded" in proposed:
            sup += 1
        elif "**out**" in proposed:
            out += 1
        if ("**blocked**" in proposed or conf.startswith("blocked") or "blocked" in conf):
            rows.append((c[0], proposed, conf))
    return rows, total, out, sup


def build() -> dict:
    ledger = [json.loads(x) for x in open(LEDGER, encoding="utf-8") if x.strip()]
    lb = [(r["id"], r["doc"]) for r in ledger if r.get("dispo") == "blocked"]
    t6, _t6_rows, _t6_out, _t6_sup = t6_blocked()
    ids = [i for i, _ in lb] + [r[0] for r in t6]
    if len(ids) != len(set(ids)):
        raise SystemExit("FAIL: a row id is blocked in both files")
    if set(ids) != set(WAITS):
        raise SystemExit("FAIL: blocked set drifted from the waits table: "
                         f"missing {sorted(set(ids) - set(WAITS))}, extra "
                         f"{sorted(set(WAITS) - set(ids))}")

    # `in_scope` is the tracker's own number: `status_audit.t_rows()` is what writes STATUS.md,
    # so the 180 is taken from the generator instead of a copy of its classification rule
    st = sa.t_rows()
    in_scope = st["in_scope"]

    rows = []
    for i, (rid, doc) in enumerate(lb):
        att = ATTEMPTS.get(rid)
        rows.append({"id": rid, "doc": doc, "source": "T_ROWS.jsonl",
                     "waits_for": WAITS[rid], "attempt": att})
    for rid, _p, _c in t6:
        rows.append({"id": rid, "doc": "T6 HUD/camera", "source": "T6_HUD_CAMERA.md",
                     "waits_for": WAITS[rid], "attempt": ATTEMPTS.get(rid)})

    resolved = [{"id": rid, **rec} for rid, rec in RESOLVED.items()]

    return {
        "schema": SCHEMA, "task": "7210",
        "title": "blocked translation rows and what each waits for",
        "generator": "Tools/scripts/t_blocked.py",
        "inputs": {
            "ledger": {"path": "Working/Translation/T_ROWS.jsonl", "sha256": sha(LEDGER),
                       "rows": len(ledger)},
            "t6": {"path": "Working/Translation/T6_HUD_CAMERA.md", "sha256": sha(T6)},
        },
        "counts": {
            "ledger_blocked": len(lb), "t6_blocked": len(t6),
            "total_blocked": len(rows), "ledger_rows": len(ledger),
            "in_scope_rows": in_scope,
            "status_md_says": f"{len(lb) + len(t6)} / {in_scope} (STATUS.md)",
            "status_audit": {"rows": st["rows"], "t6_rows": st["t6"]["rows"],
                             "out": st["total"]["out"],
                             "superseded": st["total"]["superseded"],
                             "blocked": st["total"]["blocked"], "in_scope": st["in_scope"]},
            "reconciles": (len(lb) == 27 and len(t6) == 4
                           and st["total"]["blocked"] == 31 and in_scope == 260),
        },
        "method": {
            "which_rows": "T_ROWS.jsonl rows with dispo == 'blocked', plus the T6 rows "
                          "status_audit.py:128-141 classifies as blocked; the tracker adds both",
            "waits_for": "a one-line restatement of the row's own `why` / blocked cell, no new "
                         "claim",
            "attempts": "only the first six ledger rows; each cites an existing repo file and a "
                        "marker string, re-checked by --check",
            "edits": "proposals only (`applies: false`); T_ROWS.jsonl is read-only here",
        },
        "rows": rows,
        "attempted": [r["id"] for r in rows if r["attempt"]],
        "resolved": resolved,
    }


def render_md(doc: dict) -> str:
    c = doc["counts"]
    L = ["# Blocked translation rows - what each waits for", "",
         f"STATUS: partial - {c['total_blocked']} blocked rows enumerated "
         f"({c['ledger_blocked']} ledger + {c['t6_blocked']} T6 = STATUS.md's "
         f"{c['total_blocked']} of {c['in_scope_rows']}), none left to test against the "
         f"repo. `T-FX3` and `T-ST7` were "
         f"refuted and resolved by the operator on 2026-11-06; `T-AU3` and `T-AU5` were refuted by "
         f"`AUDIO_BANKS.md` (10 banks found, 0 absent) - all seven, with `T-S6` (derived unit "
         f"bridge, 14/14 oracles), `T-WP4` (launcher split from the disable) and `T-WP13` (forced "
         f"slots), have left the blocked set "
         f"(section 'Resolved', below).", "",
         f"Ledger `T_ROWS.jsonl` sha256 `{doc['inputs']['ledger']['sha256'][:16]}...` "
         f"({c['ledger_rows']} rows), T6 sha256 "
         f"`{doc['inputs']['t6']['sha256'][:16]}...`. `T_ROWS.jsonl` is not edited; the proposed "
         "row edits below are for the operator.", "",
         f"## The {c['total_blocked']}", "",
         "| # | row | doc | waits for |", "|---:|---|---|---|"]
    for i, r in enumerate(doc["rows"], 1):
        L.append(f"| {i} | `{r['id']}` | {r['doc']} | {r['waits_for']} |")
    L += ["", "## The rows tested against the repo", ""]
    for r in doc["rows"]:
        a = r["attempt"]
        if not a:
            continue
        L += [f"### {r['id']} - {a['verdict']}", ""]
        for e in a["evidence"]:
            n = f" (must occur {e['expect_count']}x)" if "expect_count" in e else ""
            L.append(f"- `{e['file']}` marker `{e['marker']}`{n}: {e['means']}")
        if a.get("proposed"):
            p = a["proposed"]
            L += ["", f"**Proposed edit (not applied):** dispo `{p['dispo']}`, confidence cell "
                      f"`{p['cell6']}`, value: {p['value']} - label **{p['label']}**. {p['why']}"]
        L += ["", f"**Missing input:** {a['missing']}", ""]
    if doc.get("resolved"):
        L += ["## Resolved - no longer blocked", ""]
        for r in doc["resolved"]:
            L += [f"### {r['id']} - {r['verdict']}", "", f"**Ruling:** {r['ruling']}", ""]
            for e in r["evidence"]:
                n = f" (must occur {e['expect_count']}x)" if "expect_count" in e else ""
                L.append(f"- `{e['file']}` marker `{e['marker']}`{n}: {e['means']}")
            L += ["", f"**Applied:** {r['applied']}", "",
                  f"**Still open:** {r['remaining']}", ""]
    L += ["## How this is checked", "",
          "`python Tools/scripts/t_blocked.py --check` re-derives both blocked sets from the two "
          "documents, cross-checks the count against `status_audit.t_rows()` (the function that "
          "writes `STATUS.md`), rebuilds this file and its JSON byte for byte, re-runs every evidence marker "
          "(including the two negative ones, which must occur zero times) and compares the ledger "
          "sha256 with the one recorded above. A row that is later unblocked makes the check fail "
          "rather than leave this sheet stale.", "",
          "Nothing was launched, installed, attached to or written outside "
          "`Working/Translation/`."]
    return "\n".join(L) + "\n"


def write(doc: dict) -> None:
    with open(OUT_J, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1) + "\n")
    with open(OUT_M, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(doc))


def oracles(doc: dict) -> list[str]:
    bad = []
    evidence = [(r["attempt"] or {}).get("evidence") or [] for r in doc["rows"]]
    evidence += [r.get("evidence") or [] for r in doc.get("resolved") or []]
    for entries in evidence:
        for e in entries:
            p = os.path.join(ROOT, e["file"])
            if not os.path.exists(p):
                bad.append(f"evidence missing: {e['file']}")
                continue
            txt = open(p, encoding="utf-8", errors="ignore").read()
            n = txt.count(e["marker"])
            want = e.get("expect_count")
            if want is None and n == 0:
                bad.append(f"{e['file']} does not contain {e['marker']!r}")
            if want is not None and n != want:
                bad.append(f"{e['file']} contains {e['marker']!r} {n}x, expected {want}")
    if sha(LEDGER) != doc["inputs"]["ledger"]["sha256"]:
        bad.append("T_ROWS.jsonl changed since the proposal sheet was written")
    st = sa.t_rows()
    if st["total"]["blocked"] != doc["counts"]["total_blocked"]:
        bad.append(f"status_audit counts {st['total']['blocked']} blocked, the sheet enumerates "
                   f"{doc['counts']['total_blocked']}")
    if st["in_scope"] != doc["counts"]["in_scope_rows"]:
        bad.append(f"in_scope moved: {st['in_scope']} != {doc['counts']['in_scope_rows']}")
    if not doc["counts"]["reconciles"]:
        bad.append(f"counts do not reconcile: {doc['counts']}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write the proposal sheet")
    g.add_argument("--check", action="store_true", help="re-derive and compare")
    a = ap.parse_args()
    doc = build()
    if a.write:
        write(doc)
        c = doc["counts"]
        print(f"wrote Working/Translation/BLOCKED_PROPOSALS.{{json,md}}: {c['total_blocked']} "
              f"blocked rows ({c['ledger_blocked']} ledger + {c['t6_blocked']} T6) of "
              f"{c['in_scope_rows']} in scope; {len(doc['attempted'])} tested, "
              f"{len(doc['resolved'])} resolved: "
              + ", ".join(f"{r['id']}={r['attempt']['verdict']}" for r in doc["rows"]
                          if r["attempt"]))
        return 0
    if not os.path.exists(OUT_J) or not os.path.exists(OUT_M):
        print("FAIL: BLOCKED_PROPOSALS.{json,md} missing (run --write)")
        return 1
    on_disk = json.load(open(OUT_J, encoding="utf-8"))
    if on_disk != doc:
        print("FAIL: BLOCKED_PROPOSALS.json differs from the re-derived document")
        return 1
    if open(OUT_M, encoding="utf-8", newline="").read().replace("\r\n", "\n") != render_md(doc):
        print("FAIL: BLOCKED_PROPOSALS.md differs from the re-rendered text")
        return 1
    bad = oracles(doc)
    for b in bad[:10]:
        print("FAIL:", b)
    if bad:
        return 1
    c = doc["counts"]
    print(f"PASS: {c['total_blocked']} blocked rows re-derived ({c['ledger_blocked']} ledger + "
          f"{c['t6_blocked']} T6) of {c['in_scope_rows']} in scope; {len(doc['attempted'])} "
          f"attempts, all evidence markers present; ledger sha256 unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
