# T-15 rework — modes translation

**STATUS: DONE.** All 8 review issues verified against the data; **8 CONFIRMED, 0 REJECTED**, all
fixes applied **in the generator** (`Tools/scripts/t11_modes.py`) plus its ledger literals, and both
outputs regenerated. `--check` is green, the neighbouring checks are green, and a 5-case tamper test
(all five caught, each restored and re-checked) covers the review's own findings.

Card rules followed: `GRAB_BACKLOG.md` §0.5 R1–R14 — R11 (no typed numbers: every count is read and
re-derived), R4 (the class column is per row now), R5 (behaviour, not member name), R14 (journal).
No game launched, nothing written to `D:/Games`, no shared module edited, no hand edit of any
generated output, no git.

---

## Per-issue verdicts

### 1. False absence claim — `StandardTorqueVSpeedCurve` — **CONFIRMED**

Evidence (run before any edit):

```
> grep -n "StandardTorqueVSpeedCurve" Research/BatmobileGrab/ GRAB_BACKLOG.md
Research/BatmobileGrab/BMSDK_OFFSETS.json:23994/23995  "member"/"name": "StandardTorqueVSpeedCurve"
Research/BatmobileGrab/CHAIN.json:10989,11243,11497,11751  "name": "StandardTorqueVSpeedCurve"
Research/BatmobileGrab/MECHANICS.md:104,240,389,538  | `StandardTorqueVSpeedCurve` | StructProperty | 0x1F0 | 6 curve points |
Research/BatmobileGrab/MECHANICS.md:114,250,399,548
  StandardTorqueVSpeedCurve = -1500.0 → 0.0  -300.0 → 200.0  0.0 → 200.0  750.0 → 170.0  1600.0 → 150.0  2100.0 → 105.0
Research/BatmobileGrab/objects.jsonl  (4 SimulationModel objects, nested Points arrays)
```

and the old doc said the opposite:

```
T11_MODES.md:119  - **`StandardTorqueVSpeedCurve` has no values in any file.** ...
T11_MODES.md:45   ... so its points are **UNKNOWN**. ...
```

The only true part is the narrow one: it is not among `MODES.json`'s 107 declared fields —

```
> python -c "... print(n in names) ..."
StandardTorqueVSpeedCurve False      # MODES.json fields (107)
BattleModeVSpeedCurve True
```

so `T11_MODES.md` was claiming absence from *any* file when the values sit in a G1 record.

**Fix.** `gather()` now parses `Research/BatmobileGrab/objects.jsonl` (`class ==
RVehicleSimBatmobile`, `name == SimulationModel`, the nested `StandardTorqueVSpeedCurve` /
`BoostTorqueVSpeedCurve` / `BattleModeVSpeedCurve` `Points`) and `--check` asserts: standard = the 6
points above, boost = 7 points, 4 packages read, both identical in all four, and the object-stream
`BattleModeVSpeedCurve` equals `MODES.json`'s. `T-MD4` is now the row the card's "torque" item maps
to and prints both curves; §6 says explicitly that this is a **record boundary, not an absence**.

### 2. R5 — Immobilizer `carried` while its defining behaviour is absent — **CONFIRMED**

Old row (`T11_MODES.md:43`): compromise `carried`, disposition `next`, while its own JC3 cell said
"the disable itself has no JC3 member - T-WP4 is `blocked`" and its verify said "expect the blast,
**not a disable**". `T-WP4` in the ledger is `blocked` for the same object. A requirement was thus
counted as met by a carrier whose name sounds right (missile + pulse).

**Fix.** `T-MD2` → `compromise="omitted"`, `dispo="blocked"`; the cells now separate the launcher
(mountable, both modes per D-7) from the disable (named omission, T-WP4). `t_rows.py`'s `DISPO`
tuple follows. New `--check` rule (also issue 7): `omitted` ⇒ ledger `out`/`blocked`, and
`carried`/`inside band` ⇒ not.

### 3. False generalisation in §3 — **CONFIRMED**

```
> python -c "... print(M['summary']) ..."
{'declared': 107, 'serialized': 46, 'not_serialized': 61, 'same_in_all_four': 31, ...}
serialized but differing 15 ['TransformationReverseDirectionIntoPursuitModeSound',
 'TransformationReverseDirectionIntoBattleModeSound','BattleModePrimaryWeapon',
 'ImpactRoadAssistSceneryDuration','ImpactRoadAssistEnemyDuration','BattleDodgeImpulse',
 'ArmourModeDamageReduction','BattleModeImpactMaxDamagePow','KillFlipTorque',
 'KillFlipTorqueDuration','PMDodgeTorque','PMDodgeForce','PMDodgeDuration',
 'StayUprightConstraintSetup','StayUprightConstraintInstance']
```

Old text (`:60-61`): "All four packages … carry the same `SimulationModel`, so a value that is
serialised at all is the same on all four" — false for 15 of the 46.

**Fix.** §3 is generated from those numbers: 107 declared / 46 serialised / 61 absent, **31
identical on all four**, the 15 that differ named, and `ArmourModeDamageReduction`'s missing
package (Joker) stated. No number is typed.

### 4. R11 — values typed into the generator — **CONFIRMED**

Old script, every one present:

```
184:  f"km/h, {n['boost_blend_time']:g} s blend ({F['nitro_carriers']} of 232 vehicles)"
195:  bmak="`RBatmobileEMPMissile` ... (3 instances, 63 fields)"
326:  jc3="...(CAM-1: 7.00 m back, 1.30 m up, FOV 55-63, test-091)..."
367:  bmak="`TransformationReverseDirectionIntoPursuitModeSound` 62/60/191/60 and ..."
376:  why="T-16 measured 30 battle events / 75 WEMs ..."
430:  if not (55.0 <= cam["BattleModeCamFOV"] <= 63.0):
633:  a("  a bridge, and 60 deg already sits inside the delivered 55-63 band.")
```

and the doc claimed (`:146`) "`--check` … re-reads every BmAK value the rows quote", which the typed
strings made untrue. All five values are correct today (spot-checked), so this was a guard problem,
not a wrong number.

**Fix — each now read from its record:**

| value | new source |
|---|---|
| "145 of 232 vehicles" | `USAGES.json` `nitro.arcade.carriers.nitro_boost` + `nitro.arcade.entities` |
| "3 instances, 63 fields" (+ "11 BmAK weapon classes") | `WEAPONS.json` `classes[] RBatmobileEMPMissile` (`instances`, `fields`) + `counts.gadget_classes` |
| 7.00 m / 1.30 m / FOV 55-63 | `Working/Camera/CAM_TUNE.json` `edits[]` `CameraPosition[2]`, `CameraPosition[1]`, `FOV[0]`, `FOV[1]` `readback` (CAM-1 re-read the written `.ctune`; `readback 8/8` asserted) |
| 62/60/191/60 and 47/45/176/45 | `MODES.json` per-package values, printed as `V2 62, MK2 60, Joker 191, Funhouse 60` |
| 30 events / 75 WEMs | `t12_audio_map.json` W-08 `len(sources)` and `sum(wems)` |

The band test now uses the re-read `fov_lo`/`fov_hi`, and §7 says what is re-read (those inputs) and
what is *cited* (T-11's ids, T-12's angles, B-12/B-13's status).

### 5. `confidence` column is a constant — **CONFIRMED**

```
> grep -c 'confidence="decoded"' tmp/t15rework/t11_modes.py
15
> grep -c 'confidence="derived"' tmp/t15rework/t11_modes.py
0
```

**Fix.** `T-MD6` (600 cm/s → 21.6 km/h is a conversion) and `T-MD11` ("inside band" is a comparison
of two decoded numbers) are now `derived`; `T-MD4` stays `decoded` because its central value is now
genuinely decoded from `objects.jsonl`. `--check` asserts every class is in R4's vocabulary
(`decoded`, `decoded (fleet)`, `derived`, `class`, `epe`, `read`) **and** that the set is not just
`{decoded}` — a future constant column fails.

### 6. Speed-curve y unit asserted, not bridged — **CONFIRMED**

```
> python -c "... print(f['unit'], f['unit_basis']) ..."
BattleModeVSpeedCurve unit='curve (cm/s -> factor)' unit_basis='type'
Research/BatmobileGrab/MODES.md:23  | `type` | the slot type says what it is: object ref, name, bool, struct, curve |
```

i.e. the record's basis is the *slot type*, so the string "factor" carries no scale, and no file
establishes a percent. Old doc (`:46` "cm/s -> factor"; `:94` "at 600 cm/s the factor is **40%**";
review cites `:96` — the quote is at `:94` today, substance unchanged).

**Fix.** All three places now print the out-values raw (`0 -> 60, 600 -> 40, 1200 -> 30`), the row
cell says "y raw: the record's unit is … on the `type` basis, so no percent/factor scale is
established", and §6 adds a bullet listing `60/40/30` (battle) and `0/200/200/170/150/105`
(standard torque) as **not** asserted to be factors/percentages/multipliers. No rescaling.

### 7. Done criterion checked against the script's own list — **CONFIRMED**

Old `t11_modes.py:56` held `MOD2_BEHAVIOURS` as a typed 9-item list, and no rule tied
`compromise == "omitted"` to a ledger `out`/`blocked` disposition (the only match for
"omitted"/"ledger" in the old file is an unrelated row string) — which is exactly how the card's
"torque" item had no row while the check stayed green.

**Fix.** `card_behaviours()` parses the T-15 card out of `GRAB_BACKLOG.md` and extracts the `Do:`
parenthetical ("every row that differs (top speed curve, torque, steering/pivot, weapons enabled,
camera tune, lights, armour reduction, audio)"). `CARD_ROWS` maps each item to its row(s); `--check`
fails when the card lists an item with no mapping, when a mapping names a non-row, or when a mapped
item disappears from the card. "torque" maps to `T-MD4`, which now carries the torque curve. The
`omitted` ⇔ ledger rule is in `cmd_check`. Tamper case 5 below proves the card path fires.

### 8. Minor — positional indexing of the camera config — **CONFIRMED**

```
> grep -n "config_values" tmp/t15rework/t11_modes.py
140:  "config_values": cam["configs"]["BattleModeCamConfig"]["values"],
325:  f"(min/max distance {cam['config_values'][9]:g}/{cam['config_values'][10]:g} cm)"
588:  f"including min/max distance {cam['config_values'][9]:g}/{cam['config_values'][10]:g} cm."
```

`fields[9]`/`[10]` are `MinFreeCameraDistance`/`MaxFreeCameraDistance` **today** (1000/1000,
`CAMERA.json`), but the two indices are the only thing tying the labels to the values.

**Fix.** `gather()` zips `configs.BattleModeCamConfig.fields` with `values`, raises if the lengths
differ, and looks both distances up by name (also asserting non-zero). `config_values` is gone; the
doc prints `MinFreeCameraDistance`/`MaxFreeCameraDistance 1000/1000 cm, read by name`. `grep
config_values Tools/scripts/t11_modes.py` → none.

### Not-an-issue notes

- The review's own "Check output" quote matched the old run, and the drift it observed in
  `t_rows.py check`'s disposition split (`next 37 keep 60 … blocked 17 out 35` vs today's
  `next 40 keep 60 … blocked 13 out 36`) is from other cards' rows, as the review says. No action.
- `T11_MODES.md:96` in the review vs `:94` for the "40%" quote is a citation offset, not a
  disagreement; two further doc quotes moved by one line for the same reason. Substance confirmed.

---

## Files changed

| file | change |
|---|---|
| `Tools/scripts/t11_modes.py` | generator: object-stream torque curves; five records read for the previously typed numbers; name-based camera-config lookup; card-derived coverage list; `omitted` ⇔ ledger, confidence-vocabulary/non-constant assertions; §3 scoped, §6 curve-unit UNKNOWN, §7 claim qualified; `T-MD2` → omitted/blocked; `T-MD6`/`T-MD11` → derived |
| `Tools/scripts/t_rows.py` | `T-MD2` `("next", …)` → `("blocked", …)`; `T-MD4` `why` rewritten (curve decoded) |
| `Working/Translation/T11_MODES.md` | **regenerated** by `--write` (173 lines) |
| `Working/Translation/t11_variants.json` | **regenerated** by `--write` (new facts: curves, EMP, audio, tune, card items) |
| `Working/Translation/T_ROWS.jsonl` | **regenerated** by `t_rows.py build` (198 rows) |
| `STATUS.md` | **regenerated** by `status_audit.py --write` (T-15: blocked 2, queued 4) |
| `GRAB_BACKLOG.md` | §12 `T-15` line only — `diff` against the pre-edit copy shows exactly one changed line |
| `MODLOG.md` | "T-15 rework · … — intended change" (written before any edit) + "T-15 rework — done" |
| `tmp/t15rework/` | pre-edit copies of every file above (revert path) |

**Note on a concurrent session:** the shared `t_rows.py` already carried another session's
uncommitted T-14 changes (`T-DM1` keep→next, `T-DM9` blocked→next) when `t_rows.py build` ran. This
card changed only `T-MD2`/`T-MD4`; the rebuild carried those rows as that session left them.

## Untouched

`Research/**` (G1/G2 own those records), `Builds/`, `E:/Modding/_JC3grab`, `E:/Modding/_BmAKgrab`,
`D:/Games`, every game file, dropzone and save, every shared game module, git (no commit, no push).

---

## Check output (verbatim)

```
> python Tools/scripts/t11_modes.py --check
PASS: 15 rows | MOD-1 4 / MOD-2 11 | compromises carried 7, inside band 1, omitted 7 | ledger 15/15
```

exit status 0.

```
> python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
```

exit status 0.

```
> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

exit status 0.

## Tamper test (5/5 caught, each restored to PASS)

| tamper | result |
|---|---|
| `t11_variants.json`: `T-MD2` compromise `omitted` → `carried` | exit 1, `FAIL: t11_variants.json differs from the re-derived record`, first difference at char 26974 |
| md cell: `T-MD6` confidence `derived` → `decoded` | exit 1, md diff at `@@ -47,7 +47,7 @@` |
| ledger: `T-MD2` `blocked` → `next` | exit 1, `FAIL T-MD2: ledger dispo next != blocked` and `FAIL T-MD2: \`omitted\` but the ledger says next` |
| source drift: `CAM_TUNE.json` `FOV[1]` readback 63 → 64 | exit 1, md diff at `@@ -52,7 +52,7 @@` — the old typed `55-63` would have stayed green |
| card drift: `+ sonar` added to the card's `Do:` list | exit 1, `FAIL card item 'sonar' has no row mapped in CARD_ROWS` |

## Residual UNKNOWNs (unchanged, now honestly labelled)

- `BattleModeVSpeedCurve` / the torque curves: **y axis undocumented**; out-values carried raw, no
  percent/factor claim.
- 61 of the 107 declared mode fields are serialised in no package → `UNKNOWN`, not zero.
- `ArmourModeDamageReduction` = 0 on the 3 packages that carry it, unit undocumented → no reduction.
- `BattleModeThrottleSpeed` (10) carried raw (unit undocumented).
- Battle camera spring/distance fields have no unit bridge (T-CAM9 blocked); only the FOV does.
- No battle light behaviour exists in the fleet (9 behaviours, 0 battle).
