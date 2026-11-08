# Independent review — T-15 · Modes translation

Reviewed: `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-15 card (§7) and its §12 row; `MODLOG.md`
§"T-15 · Modes translation — done (2026-10-28)" (line 13501) and the intended-change section
(line 13432); the three named outputs `Working/Translation/T11_MODES.md`,
`Working/Translation/t11_variants.json`, `Tools/scripts/t11_modes.py`; and the inputs the script
reads (`Research/BatmobileGrab/MODES.json`, `CAMERA.json`, `Research/JC3Grab/TANKTURN.json`,
`LIGHT_SYSTEM.json`, `USAGES.json`, `Working/Translation/t14_lights.json`, `T_ROWS.jsonl`).

**VERDICT: needs rework (narrow).** Every number I spot-checked is correct, all three `Out:` paths
exist, and the card's `--check` passes. But the record makes one factual absence claim that an
in-repo G1 evidence file refutes (`StandardTorqueVSpeedCurve`), one card-named behaviour (torque)
therefore has no row, one MOD-2 half of the hybrid is labelled `carried` although the doc itself
says its defining behaviour is absent (R5), and a set of numbers in the generated doc are typed
into the generator rather than read, so `--check` cannot watch them (R11). All fixes are
documentation/script edits plus a regeneration — no build or game data is affected.

## Check output (verbatim)

```
> python Tools/scripts/t11_modes.py --check
PASS: 15 rows | MOD-1 4 / MOD-2 11 | compromises carried 8, inside band 1, omitted 6 | ledger 15/15
```

exit status 0. This is byte-identical to the line pasted in the MODLOG done section.

Neighbouring checks I re-ran, also green:

```
> python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok

> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

The MODLOG quotes a different disposition split (`next 37 keep 60 … blocked 17 out 35`); the 198
total matches, so that paste is accurate for the moment it was taken and only drifted because
later cards (T-16…T-23) changed their own rows. Not a defect.

## Out paths / Done criterion

- `Out:` = `Working/Translation/T11_MODES.md` + rows; variant table `t11_variants.json`. All three
  named files exist (doc 16,225 B, json 28,142 B, script 42,683 B), the doc carries the 15 rows in
  §2, and the same 15 `T-MD*` ids are in `T_ROWS.jsonl` with matching cells — `--check` asserts
  exactly that (`lr["cells"] != row["cells"]`).
- The card's `Done when`, "every MOD-2 behaviour has a row in each variant or a named omission":
  under D-2 = hybrid there is one variant, which the card's own hybrid branch authorises and the
  doc states. What the check proves is weaker than the sentence: coverage is tested against a
  **hardcoded 9-item list** in the script (`t11_modes.py:56`), not against §1.6's MOD-2 line or the
  card's `Do` bullet list, and nothing asserts that an `omitted` row is a ledger named omission.
  Circular but not false — see issue 7.

## Issues

1. **False absence claim — `StandardTorqueVSpeedCurve` (R4).**
   `Working/Translation/T11_MODES.md:119` states "**`StandardTorqueVSpeedCurve` has no values in
   any file.**" and `:45` (T-MD4) says its points are `**UNKNOWN**`. Both are wrong: the values are
   in the G1 evidence set — `Research/BatmobileGrab/MECHANICS.md:114` (and the same block at
   `:250`, `:399`, `:548`, i.e. all four packages):
   `-1500→0, -300→200, 0→200, 750→170, 1600→150, 2100→105`;
   `Research/BatmobileGrab/README.md:53` also records "6 points", and `BMSDK_OFFSETS.json`,
   `CHAIN.json`, `OFFSETS.json`, `objects.jsonl` list the field. `GRAB_BACKLOG.md` HDL-2 itself
   sources this curve to `MECHANICS.md`. Only the narrow statement that the name is not among
   `MODES.json`'s 107 declared fields is true. Result: MOD-1's "high speed" row rests on
   T-E1/T-E3 instead, and the card's `Do` list ("top speed curve, **torque**, …") has no row that
   records the BmAK torque curve at all (T-MD7 carries `BattleMode*` drive factors, not torque).
   Fix: read the curve from `MECHANICS.md`/`CHAIN.json`, add it to T-MD4 (or a torque row), correct
   the §6 bullet.

2. **R5 — the Immobilizer is marked `carried` with its defining behaviour absent.**
   `T11_MODES.md:43` (T-MD2): the JC3 cell says "the disable itself has no JC3 member - T-WP4 is
   `blocked` for exactly that", the verify cell says "expect the blast, **not a disable**", yet the
   compromise is `carried`, the confidence `decoded` and the ledger disposition `next`
   (`t11_modes.py:190-206`). The row therefore counts the requirement as met by a carrier whose
   name sounds right (missile + pulse) while the behaviour the requirement names — disabling
   vehicles — is proven missing. T-WP4, the same BmAK object, is `blocked` in the ledger. It should
   be `omitted` / `blocked` for the disable half, with the launcher availability recorded separately.

3. **False generalisation in §3.** `T11_MODES.md:60-61`: "All four packages … carry the same
   `SimulationModel`, so a value that is serialised at all is the same on all four."
   `MODES.json` summary: 46 serialised, **31** `same_in_all_four` — 15 serialised fields differ.
   `ArmourModeDamageReduction` is serialised on 3 packages only (the doc says so later), and the two
   transformation sounds differ per package — and the doc's *own* T-MD14 cell prints
   `62/60/191/60`. The sentence must be scoped to the fields it actually holds for.

4. **R11 — values typed into the generator, so `--check` cannot detect drift.**
   `t11_modes.py:184` "`145 of 232 vehicles`" (232 typed); `:195` "`(3 instances, 63 fields)`"
   (available in `WEAPONS.json`, not read); `:326` "CAM-1: 7.00 m back, 1.30 m up, FOV **55-63**"
   (in `T6_HUD_CAMERA.md` §2 / the delivered `.ctune`, not read); `:367` the two
   `Transformation*Sound` value lists (present in `MODES.json`, not read); `:376` "30 battle
   events / 75 WEMs" (in `t12_audio_map.json` W-08, not read). All of these are **correct today**
   (see spot-checks), but the doc's closing claim (`:146`) that `--check` "re-reads every BmAK value
   the rows quote" is not true: the check regenerates these cells from the same typed strings, so a
   change in `MODES.json`, `WEAPONS.json` or the `.ctune` would pass green with a stale doc. The
   one `inside band` verdict also rests on a typed literal, `if not (55.0 <= cam[...] <= 63.0)`
   (`:430`), not on the tune.

5. **The confidence column is a constant.** All 15 rows are `decoded` (`add(... confidence="decoded")`
   in every block of `t11_modes.py`). R4's class column is therefore uninformative and mislabels
   rows: `21.6 km/h` on T-MD6 is a unit conversion (`derived`), T-MD11's `inside band` is a
   judgement, and T-MD4 is labelled `decoded` while its central value is declared `UNKNOWN`. The
   MODLOG's tamper table (`T-MD10` `decoded`→`derived` caught) shows the column is meant to
   discriminate.

6. **Speed-curve y-unit asserted, not bridged.** `T11_MODES.md:46` and `:96` call the curve's
   y-values "factor" and then "the factor is **40%**". `MODES.json` labels the field only
   `"curve (cm/s -> factor)"`; no file establishes a percent scale, so 40 vs 0.4 is a guess about
   the multiplier, and it is not listed in §6's UNKNOWNs. Either convert with a stated basis or
   record the unit as undocumented (the same treatment §6 gives `BattleModeThrottleSpeed` and
   `ArmourModeDamageReduction`).

7. **Done criterion is checked against the script's own list.** `MOD2_BEHAVIOURS`
   (`t11_modes.py:56`) is typed; a behaviour missing from that list would never fail the check
   (this is how "torque" from the card's `Do` list escapes). No assertion ties
   `compromise == "omitted"` to a ledger `out`/`blocked` disposition, so an `omitted` row could be
   left `next` and still pass.

8. **Minor — positional indexing of the camera config.** `t11_modes.py:325` and `:588` print
   `cam["config_values"][9]`/`[10]` as "min/max distance"; they are `MinFreeCameraDistance` /
   `MaxFreeCameraDistance` today (1000/1000, `CAMERA.json` `fields[9]`/`[10]`) but a re-ordered
   field list would silently relabel the row. Index by name.

## Spot-checks

| value in `T11_MODES.md` | where verified |
|---|---|
| `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h (T-MD6, `:47`, `§3`) | `Research/BatmobileGrab/MODES.json` field, `values` 600.0 on all four packages, `unit` "cm/s", `unit_basis` "conv"; 600/100×3.6 = 21.6 ✔ |
| `BattleModeVSpeedCurve` 0→60, 600→40, 1200→30, identical in all four = True (T-MD5, `§3`) | `MODES.json` `struct.points` = [[0,60],[600,40],[1200,30]], `same_in_all_four` true; corroborated `MECHANICS.md:115` ✔ |
| `BattleModeCamFOV` 60 / `BattleModeWinchCamFOV` 60 / `AntiPersonelBattleModeCamFOV` 40; `BattleModeCamConfig` 24 fields, min/max distance 1000/1000 cm (T-MD11, `§3`) | `Research/BatmobileGrab/CAMERA.json` `values` 60.0 / 60.0 / 40.0 on class `R3rdPersonCamera`; `configs.BattleModeCamConfig.fields` length 24, `fields[9]`=`MinFreeCameraDistance`, `fields[10]`=`MaxFreeCameraDistance`, values 1000.0/1000.0 ✔ |
| nitro "torque x2, grip x2, push 15,000, +40 km/h, 0.2 s blend (145 of 232 vehicles)" (T-MD1, `:42`) | `Research/JC3Grab/USAGES.json` `nitro.arcade.donor.nitro_boost` = {2, 2, 15000, 40, 0.2 s}; `nitro.arcade.carriers.nitro_boost` = 145 ✔ |
| EMP "`RBatmobileEMPMissile` … (3 instances, 63 fields)" (T-MD2, `:43`) | `Research/BatmobileGrab/WEAPONS.json` `classes[]` entry `RBatmobileEMPMissile`: instances 3, fields 63 ✔ |
| transformation sounds 62/60/191/60 and 47/45/176/45 in V2/MK2/Joker/Funhouse order (T-MD14, `:55`) | `MODES.json` `TransformationReverseDirectionIntoPursuitModeSound` {V2 62, MK2 60, Joker 191, Funhouse 60}; `TransformationReverseDirectionIntoBattleModeSound` {47, 45, 176, 45} ✔ (note the doc abbreviates the second field as `...BattleModeSound`) |
| "4 `VEHLT_BattleModeLight` entries … spotlight, two heads, one wheel arch" (T-MD12, `:53`) | `Working/Translation/t14_lights.json` rows T-L17 `Front_Secondary_Head`, T-L18 `headlight_battle_left`, T-L19 `headlight_battle_right`, T-L20 `sportsmuscle_wheel_f_l_arch_battle` ✔ |
| 107 declared / 46 serialised / 61 absent; `BattleModeMaxSpeed`, `BattleModeSteerBias`, `Strafe*` not serialised (`§3`, `§6`) | `MODES.json` summary {declared 107, serialized 46, not_serialized 61}; those fields `serialized: false`, `values: {}` ✔ |

Nothing in the doc or the json is contradicted by the raw data I read; the defects are claims about
absence, labelling, and numbers that are right but unguarded.

## What would clear it

1. Read `StandardTorqueVSpeedCurve` from `MECHANICS.md`/`CHAIN.json`, carry it in T-MD4 or a new
   torque row, and correct `T11_MODES.md:119` (and `:45`).
2. Re-class T-MD2's compromise/disposition so the absent Immobilizer disable is a stated omission.
3. Scope the §3 sentence to the fields where `same_in_all_four` is true.
4. Move the typed values (232, 63, 55-63, the two sound lists, 30/75) into `gather()` so `--check`
   re-reads them, and drop or qualify the `:146` "re-reads every BmAK value" sentence.
5. Make `confidence` reflect each row's actual class (conversion → `derived`, UNKNOWN → not
   `decoded`).

Reviewer wrote only this file; no other file was modified, no game was launched, nothing was
committed.
