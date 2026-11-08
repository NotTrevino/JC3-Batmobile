STATUS: done — all 17 blocked rows are enumerated from the two documents the tracker reads, each with
the input it waits for; the first six were tested against the repo: **1 unblocked with evidence**
(T-FX3), **1 whose blocked reason is refuted and now needs an operator decision** (T-ST7), **1 half
unblocked** (T-WP4), and **3 still blocked** (T-AU3, T-S6, T-AU5). `T_ROWS.jsonl` was not edited; every
proposed row edit is `applies: false`. The checker re-derives the row set, cross-checks it against the
tracker's own generator and passes.

# 7210 — blocked translation rows, and what each waits for

## Files written

| file | role |
|---|---|
| `Tools/scripts/t_blocked.py` | the checker, `--write` / `--check` |
| `Working/Translation/BLOCKED_PROPOSALS.json` | the 17 rows, their waits, the six attempts, the proposed (unapplied) edits |
| `Working/Translation/BLOCKED_PROPOSALS.md` | the same, rendered |
| `tmp/freebuff/reports/7210-t-blocked-rows.md` | this report |
| `MODLOG.md` | one appended journal section (rule R14) |

`Working/Translation/T_ROWS.jsonl` is **read only** here; its sha256 is recorded in the JSON and
re-compared by `--check`, so a later disposition change fails the check instead of ageing silently.

## The count, reconciled

`STATUS.md:18` says **17 / 180**. That 17 is not a single field: the tracker adds the T6 table to the
ledger (`status_audit.py:121-141`).

- `T_ROWS.jsonl`: 198 rows, `dispo` counts `keep 60, next 40, out 36, epe 26, edit 16, blocked 13,
  superseded 7` → **13 blocked**.
- `T6_HUD_CAMERA.md`: 33 rows, **4 blocked** (`status_audit.t_rows()["t6"]`).
- 13 + 4 = **17**; in-scope = 180 (198 − 43 `out` − 8 `superseded` + 33 − 7 − 1, from
  `status_audit.t_rows()["in_scope"]`).

## The 17, one line each

| # | row | doc | waits for |
|---:|---|---|---|
| 1 | T-AU3 | T-2b | a JC3-format bank carrying the 90 BmAK events in 10 absent banks — no `.fev` project ships, so a bank cannot be authored (`JC3_AUDIO.md` §10 route b) |
| 2 | T-FX3 | T-2b | nothing structural: JC3's `usage_effects` carrier and the `EngineNitro` usage are decoded; only a decision on which usage raises the flame |
| 3 | T-S6 | T-3 | BmAK's numeric stiffness/damping in a known unit (no project file carries one) and JC3 has no droop member for `BM*MaxDroop` |
| 4 | T-ST7 | T-3 | an operator decision: accept 0.8/0.6 s, or route BmAK's 0.25 s through `t_to_full_steer_s` (the 0.5 s "floor" is refuted) |
| 5 | T-AU5 | T-3 | the same absent BmAK banks (transformation, taser, vehicle-voice events have no JC3 bank) |
| 6 | T-WP4 | T-7 | a JC3 member that disables an NPC vehicle — the missile half is decoded, the disable is not |
| 7 | T-WP5 | T-7 | a decoded trigger for the entity-level `CForcePulse` (14 unowned pulses; firing moment UNKNOWN) |
| 8 | T-WP13 | T-7 | a weapon-switch mechanism (max 2 driver slots, no active-slot index, no next/prev action in 232 `.epe`) or a decision to accept 2 |
| 9 | T-WLD4 | T-20 | a `.stringlookup` write side — the key and bytes are decoded (T-WLD4B), the writer does not exist |
| 10 | T-WLD6 | T-20 | the same write side, for the `<leaf>_desc` pair |
| 11 | T-WLD11 | T-20 | a deform-point list on the Batmobile body so the three stunt areas can be re-indexed (donor areas sit 0.6 m off the shell) |
| 12 | T-MD2 | T-15 | the disable half of T-WP4 |
| 13 | T-MD14 | T-15 | a mode-switch event or a second variant for the 30 battle-mode events (the hybrid has one mode) |
| 14 | T-HUD5 | T6 | a weapon component on the entity for the HUD's 2 slots (T-11 bound w602/w603 since; the 3 special-weapon states have no member) |
| 15 | T-CAM8 | T6 | a head-impulse / drift-orientation camera member — none decoded |
| 16 | T-CAM9 | T6 | a unit bridge from camera smoothing strength to JC3 spring stiffness |
| 17 | T-CAM11 | T6 | a numeric bridge to `AddCameraShake` |

## The first six, tested against files already in the repo

**T-FX3 — UNBLOCKED (evidence).** The row's "no usage slot" is false as an engine claim. The carrier
is the entity `usage_effects` array (module member at +32), the vocabulary has 155 usage ids, and the
donor's own two exhaust emitters already carry `EngineNitro` = **4197885156**; the fleet ships
`effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` in 17 cargo rows. Proposed edit
(unapplied): `dispo: epe`, value "usage 4197885156 on the donor's two emitters at the `Afterburner`
socket", label **decoded**. Evidence: `Research/JC3Grab/USAGES.json` (`4197885156`),
`Research/JC3Grab/FX_TABLE.jsonl` (`car_cycle_base_dual_nitrous`), `Working/Translation/T_FX3B.md`.

**T-ST7 — reason refuted, needs a decision.** "The fleet's fastest rack is 0.5 s" is wrong: 0.25 s
ships in 4 `LandSteering` AI twins (0.2 s on the high-speed member) and **player** `MotorbikeSteering`
modules ship 0.3 s, so the player path is not floored at 0.5 s. No player *car* ships below 0.5 s, so
0.8/0.6 is still in-family; the honest status is a compromise, not a limit. Proposed edit (unapplied):
`dispo: next`, value 0.25 s via route R1 (`t_to_full_steer_s` = 0.25) or keep 0.8/0.6, awaiting the
operator. Evidence: `Research/JC3Grab/DRIVE_CARRIERS.json` (`t_to_full_steer_s`),
`Working/Translation/T_ST7B_FLOOR.md`.

**T-WP4 — PARTIALLY unblocked.** The launcher half is decoded (`Batmobile_EMP_Missile_Launcher`, 3
instances, 63 fields, `_ForCars` projectile a reference-only archetype with no scalar); the disable is
`SetDisabledByEMP` on `RVehicleBatmobileBase` with **no EMP-named member on any NPC `RVehicle*` class**
and JC3's EMP is the truck's entity-level pulse (`truck_emp_device_rebel` + `truck_emp.ftune`) — a
blast, not a disable. Proposed edit (unapplied): split into T-WP4a launcher (decoded, buildable) and
T-WP4b disable (named omission). Evidence: `Working/Translation/T_WP4C_TRACKER_EMP.md`,
`Research/JC3Grab/EMP.json`.

**T-AU3 — still blocked, and the row's wording is right.** All **27 of 27** BmAK banks are absent from
the JC3 install by name (archive index, FSB5 name tables, dropzone) and by Jenkins hash; the JC3 index
contains `BML_Batmobile` **0 times**. The loss is real because BmAK's FEV graph cannot be authored into
JC3's bank format. Evidence: `Working/Translation/T_AU3B.md`, `Research/JC3Grab/INDEX.jsonl`.

**T-AU5 — still blocked**, same 27/27 absence covering the transformation/taser/voice banks.

**T-S6 — still blocked on one value.** The member map is now decoded (spring rate, two damper rates,
anti-roll, a rest offset along the spring) and the unit of JC3 `strength` is proven mass-normalised by
a 166-vehicle oracle (`sag = g/(4·strength)`), but **BmAK's stiffness value exists in no project
file** — `BMSDK_OFFSETS.json` gives the name and offset only. JC3 also has no droop split. Evidence:
`Research/BatmobileGrab/BMSDK_OFFSETS.json`, `Working/Translation/T_S6B.md`.

## Correctness of the checker

- Re-derives the blocked set from both documents and asserts the id set equals the waits table (17).
- Cross-checks the total against `status_audit.t_rows()` — the function that writes `STATUS.md` — so
  the 17 and the 180 are the tracker's own numbers, not a copy of its classification rule.
- Re-runs every evidence marker; the two negative markers must occur **zero** times.
- Rebuilds both files and compares them byte for byte, and compares the ledger sha256.

Two reconciliations failed while building it and were fixed, not papered over: a hand-copy of the T6
row count gave 152 (blocked rows used as the row total) and then 181 (my own T6 line parse counted 34
rows where `status_audit` counts 33). Rather than guess which line differs, `in_scope` and the T6 row
count now come from `status_audit.t_rows()`; the 4 blocked T6 ids are still enumerated here and match
its `blocked = 4`.

## Commands, with verbatim output

**1 — the ledger**
```
$ python - <<'EOF'  # read T_ROWS.jsonl, count dispo, print each blocked row (900 chars each)
rows 198
keys of row0: ['id', 'doc', 'section', 'cells', 'dispo', 'why', 'edits']
dispo counts: Counter({'keep': 60, 'next': 40, 'out': 36, 'epe': 26, 'edit': 16, 'blocked': 13, 'superseded': 7})
blocked 13
{"id": "T-AU3", ...}   (13 rows printed, each truncated to 900 chars by the probe)
```

**2 — the tracker's own numbers (and why the hand-count was wrong)**
```
$ python - <<'EOF'  # import status_audit, print t_rows()
t_rows total: {"evidenced": 126, "assumed": 1, "blocked": 17, "out": 43, "superseded": 8, "other": 36, "rows": 231}
ledger rows: 198 t6: {"evidenced": 12, "assumed": 0, "blocked": 4, "out": 7, "superseded": 1, "other": 9, "next": 0, "rows": 33}
in_scope: 180
dispo-only out/sup: 36 7 -> in-scope 155
rows counted out/superseded by confidence cell: 0
```

**3 — the 4 T6 rows, with status_audit's blocked rule**
```
$ python - <<'EOF'  # parse T6_HUD_CAMERA.md the way status_audit.py:128-141 does
T6 blocked rows: 4
   T-HUD5 | proposed: **blocked**: the HUD supports it (G2-25: 2 slots, `InitVehic | conf: decoded
   T-CAM8 | proposed: **blocked**: no head-impulse or drift-orientation member | conf: decoded
   T-CAM9 | proposed: keep | conf: blocked
   T-CAM11 | proposed: **blocked** | conf: decoded
```

**4 — the evidence markers exist (run while writing the script)**
```
$ grep -c "4197885156" Research/JC3Grab/USAGES.json                 9
$ grep -c "car_cycle_base_dual_nitrous" Research/JC3Grab/FX_TABLE.jsonl   17
$ grep -c "BMWheelSuspensionStiffness" Research/BatmobileGrab/BMSDK_OFFSETS.json   2
$ grep -lc "t_to_full_steer_s" Research/JC3Grab/*.json              Research/JC3Grab/DRIVE_CARRIERS.json
$ grep -c "BML_Batmobile" Research/JC3Grab/INDEX.jsonl              0
```

**5 — the sheet, written**
```
$ python Tools/scripts/t_blocked.py --write
wrote Working/Translation/BLOCKED_PROPOSALS.{json,md}: 17 blocked rows (13 ledger + 4 T6) of 180 in scope; first six tested: T-AU3=still-blocked, T-FX3=unblocked-with-evidence, T-S6=still-blocked, T-ST7=reason-refuted-needs-decision, T-AU5=still-blocked, T-WP4=partially-unblocked
WRITE_EXIT=0
```

**6 — the checker**
```
$ python Tools/scripts/t_blocked.py --check
PASS: 17 blocked rows re-derived (13 ledger + 4 T6) of 180 in scope; 6 attempts, all evidence markers present; ledger sha256 unchanged
CHECK_EXIT=0
```

**7 — the counts it stores**
```
$ python -c "import json;d=json.load(open('Working/Translation/BLOCKED_PROPOSALS.json'));print(json.dumps(d['counts'],indent=1))"
{
 "ledger_blocked": 13,
 "t6_blocked": 4,
 "total_blocked": 17,
 "ledger_rows": 198,
 "in_scope_rows": 180,
 "status_md_says": "17 / 180 (STATUS.md:18)",
 "status_audit": {"rows": 198, "t6_rows": 33, "out": 43, "superseded": 8, "blocked": 17, "in_scope": 180},
 "reconciles": true
}
```

**8 — tamper: an edited sheet is caught, the restore is clean**
```
$ printf '\nTAMPER\n' >> Working/Translation/BLOCKED_PROPOSALS.md; python Tools/scripts/t_blocked.py --check
FAIL: BLOCKED_PROPOSALS.md differs from the re-rendered text
TAMPER_EXIT=1
$ cp tmp/freebuff/scratch/bp.bak Working/Translation/BLOCKED_PROPOSALS.md; python Tools/scripts/t_blocked.py --check
PASS: 17 blocked rows re-derived (13 ledger + 4 T6) of 180 in scope; 6 attempts, all evidence markers present; ledger sha256 unchanged
RESTORED_EXIT=0
```

**9 — the two failed reconciliations, for the record**
```
FAIL: counts do not reconcile: {... 'in_scope_rows': 152 ...}
FAIL: counts do not reconcile: {... 'in_scope_rows': 181 ...}
```
(both fixed by taking `in_scope` from `status_audit.t_rows()`; see "Correctness of the checker")

## UNKNOWNs

| what | tried | why still unknown |
|---|---|---|
| T-S6's stiffness/damping **value and unit** | `BMSDK_OFFSETS.json` (name + offset only), `T_S6B.md` field map, `DRIVE_MODES.json` (references, no value) | no file in the project decodes a numeric BmAK stiffness; it would be in a class-default decode of `RVehicleSimBatmobile`, which the SDK dump does not carry |
| T-WP4's victim-side disable member | `EMP.json`, `FORCEPULSE.json`, `T_WP4C_TRACKER_EMP.md` (absence over every member of both BmAK classes) | no EMP-named member on any NPC `RVehicle*` class; the disable is engine code (and `CEMPWeapon` has 0 vehicle users) |
| T-FX3's *new* usage | `USAGES.json` (155 ids, 6 named from a module) | whether a usage can be raised outside the arcade nitro fields is not decodable; it does not block this row |
| T-ST7 after the decision | `T_ST7B_FLOOR.md` routes R1-R7 | whether the **player** path honours 0.25 s can only be measured in game (test ban) |
| why my T6 line parse counted 34 rows vs `status_audit`'s 33 | compared both parses, then adopted the generator | not chased further because the blocked set (4) and the in-scope total (180) both come from the generator and match |

## Scope

Nothing was launched, attached to, installed or written outside `Working/Translation/` and the report
(MODLOG appended). No bank, module, build or game file was touched; the test ban is intact.
