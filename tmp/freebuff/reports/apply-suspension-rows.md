# Applying the suspension rows — T-S6, T-S4, T-S5, T-M3, T-R2, T-R3

Task 8208. Inputs: `tmp/freebuff/reports/suspension-unit-bridge.md` (T-S6, 14/14 oracles,
`Tools/scripts/t_s6_bridge.py`) and `tmp/freebuff/reports/keep-audit-suspension-and-mass.md`
(the keep-audit of T-M3, T-S4, T-S5, T-R2, T-R3). Output: the six ledger rows, two new build
cards, the blocked-row pins, and a green re-pin.

Every number below is **decoded** (read at a stated file), **derived** (rule + inputs shown) or
**UNKNOWN**. No game was launched; nothing was written outside `Working/Translation/`,
`Research/specs/`, `Tools/scripts/` and `tmp/freebuff/reports/`.

## 1. The six rows, as they now stand

| row | disposition | BmAK number | JC3 value | fit error | verdict |
|---|---|---|---|---|---|
| `T-S6` | `blocked` → **`next`** | stiffness 3000, damping 300, bias 10/50, TravelDown 40 cm, TravelUp 30 cm, droop 100 cm, PM 750 | `length` 0.40 m, `strength` 13.500 s^-2, `compression`/`relaxation` 1/2, front `hardpoint_offset_along_spring` −0.10 | **+5.8% / −5.5%** (stiffness), **−4.4%** (damping ratio), **−31.1%** (integer pair), **0.0%** (front bias) | derived bridge |
| `T-S4` | `next` (0 edits) | no antiroll member; native stay-upright constraint, 4 values **not serialised** | `antirollbar_strength` 0 / 0 | none — no number exists on either side | COMPROMISE, kept, restated |
| `T-S5` | `next` (0 edits) | no offset member; slip gains rear 1.6, handbrake 1.5 front / 1.1 rear | **0.1 front / 0.05 rear** (replaces 0.2 / 0.2) | none measurable — the gain → offset map is **UNKNOWN** | COMPROMISE, replaced |
| `T-M3` | `next` (0 edits) | **no CoM/mass/tensor tag** on any of the four `RB_BodySetup` exports | **−0.3** (re-stated as a declared fleet value, not a translation) | none; the derived candidate +0.148 m is **rejected** | COMPROMISE, kept, restated |
| `T-R2` | `next` (0 edits) | `Drag` @16, `DragNoLoad` @20, `DriftDrag` @712 **exist, no values decoded** | 0.1 / 0.1 | none derivable — one multiplier cannot carry a load-dependent pair | COMPROMISE, kept, cell corrected |
| `T-R3` | `keep` | no shape-cast member anywhere; four **raycast** wheels (export 5282) | 0 / 0 | **none — LORE-EXACT** | keep |

### 1.1 T-S6 — the bridge, number by number

```
length   = SuspensionTravelDown 40 cm x 0.01 = 0.40 m      (cm proven: WheelRadius 64.0 = 0.64 m)
f        = g/(4*strength*length), fleet median           = 0.4542   (n=126, IQR 0.327-0.454)
strength = 9.81 / (4 * 0.4542 * 0.40)                    = 13.500 s^-2
BmAK 3000 at the decoded 210 kg SVehicle.ChassisMass     = 14.286 s^-2   (f 0.4292)
                                                          fit error +5.8% / -5.5%
zeta     = 300 / (2*sqrt(3000*210)) = 0.1890   fleet 0.1976           -4.4%
compression/relaxation = 1 / 2  -> zeta 0.136                         -31.1% (integer quantisation)
front bias -10/100 = -0.10     fleet front median -0.100               0.0%
rear  bias  50 -> -0.50        fleet minimum (any axle) -0.375         outside range, 25.0% short
```

Both readings of the stiffness land inside the rule's own scatter (p5 −60% / p95 +50%), which is
why the fit error is quoted **per number** and not as a bound. The pursuit-mode 750 does **not** fit:
750/210 = 3.571 s^-2 gives 0.6867 m of sag = **172% of the 0.40 m travel** (implied mass 55.6 kg, or
a 1.51 m travel).

### 1.2 What the audit marked COMPROMISE, and what was written

The audit's finding was that four of the five keep-audit rows sit in the fleet range and have no
BmAK number to be measured against, and one (T-R3) matches a BmAK mechanism. So the writes split
three ways:

- **A replacement value exists (T-S5).** The symmetric 0.2 was replaced by the donor's asymmetric
  pair **0.1 front / 0.05 rear**, because asymmetry is the one thing BmAK states about front-vs-rear
  lateral behaviour (rear `LatSlipFactor` 1.6, front inherited, `HandbrakeLatSlipFactor` 1.5 / 1.1).
  The ledger cell says plainly that a slip **gain** is not a force **offset**: it is a decided pair,
  not a conversion.
- **No replacement value exists, so the cell now says what the value is (T-S4, T-R2).** T-S4: 0 is
  the fleet median and reproduces "no shipped car uses the field", not BmAK's roll mechanism — the
  numbers that would describe it (`StayUprightRollResistAngle`, `...PitchResistAngle`,
  `...Stiffness`, `...Damping`) are declared and serialised in no package. T-R2: the cell no longer
  says "—"; it names `RVehicleSimBatmobile.Drag` 16 / `DragNoLoad` 20 / `DriftDrag` 712 and records
  that T-A2's absence proof stopped at `SVehicleSimCar`, one class short.
- **A derived candidate was rejected (T-M3).** The body-bbox-vs-wheelbase-midpoint candidate
  (+0.148 m rearward) is **not** adopted: the member's axis convention is UNKNOWN, +0.148 is above
  the fleet maximum (+0.1), and −0.3 is what QA-1's handling was tuned on. The row now names the
  real levers instead — the `physicsc` hull mass blocks (CoM at `+0x10..0x17`, 0.0156 m median
  oracle error) and the wheel mass 75/150 = **+0.063 m** rearward (derived), which the ledger had
  never named.
- **T-R3 needed no change** beyond the LORE-EXACT statement: BmAK has no shape-cast member and JC3 0
  is raycast on all 26 6 t+ and 35 3–8 t land vehicles, so there is no replacement value and no fit
  error to report — only the residual that `raycast_offset` 0 puts the ray's start at the hub.

### 1.3 Where a member is missing — the cards

T-S6 has BmAK numbers with no JC3 channel; both are now written as cards, each citing the arithmetic
and a Done/Stop gate:

| card | holds | the wall |
|---|---|---|
| `Research/specs/B-22.md` | `BMRearWheelMaxDroop` **100** cm, `SuspensionTravelUp` **30** cm | one `length` per axle; `min_length` and `max_length_offset` are **0 on all 166** fleet vehicles and the engine's reading of `max_length_offset` is UNKNOWN. The up half is authored as `max_length_offset` 0.30 in a private copy, gated on the 0.40 vs 0.70 m decision |
| `Research/specs/B-23.md` | `PMWheelSuspensionStiffness` **750**, `PMWheelSuspensionBias` **20**, `StationaryWheelSuspensionBias` **5** | no per-mode or stationary member at any speed gate; 750 cannot share the 0.40 m travel (172% sag), so it can only arrive through the reopened mode switch (B-12) or a script |

Both cards state the same rule: **do not write 750 into `strength`** and **do not write
`max_length_offset` before T-S3's 0.40 vs 0.70 m is settled**, or the two travels are counted twice.
`T-R2`'s decode is card **T-26** (below), which is the only one of the three that is a decode task
rather than a build task.

## 2. Pin upkeep — `Tools/scripts/t_blocked.py`

T-S6 leaving `blocked` changes **which rows are blocked** (14 → 13 in the ledger), not the in-scope
count (216). The pins were updated and both commands pass.

Backup first: `Tools/scripts/t_blocked.py.bak-20261106` (26,502 B, the pre-edit copy). The file is
**untracked in git**, so the backup is the only pre-edit copy; `git show HEAD:` has no such path
(an attempt produced an empty stub, which was deleted).

| what changed | from → to |
|---|---|
| `RESOLVED["T-S6"]` | new — verdict `resolved-by-derived-bridge`, 3 evidence oracles |
| `WAITS["T-S6"]` | removed (a resolved row waits for nothing) |
| `ATTEMPTS["T-S6"]` | removed (its `still-blocked` verdict is superseded) |
| `counts["reconciles"]` | `14 ledger + 4 T6 = 18` → **`13 ledger + 4 T6 = 17`** |
| docstring | "18 blocked of 216 / 14 rows" → **"17 blocked of 216 / 13 rows"**; five rows have left the set, not four |
| `render_md` | "two tested … 1 still blocked (T-S6)" → "one tested"; `T-S6` added to the left-the-set sentence |
| `in_scope == 216` | unchanged — verified against `status_audit`, not assumed |

The three evidence markers are checked by `--check` like every other resolved row: `0.4542`, `13.500`
and `no_bias_member` in `tmp/freebuff/reports/suspension-unit-bridge.md` — i.e. the sheet fails if the
bridge report stops saying what this row says it says.

## 3. Checks run (all green, in this order)

```
$ python Tools/scripts/t_rows.py build
T_ROWS.jsonl: 198 rows, 35 edits over 16 rows
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 80 keep 56 epe 26 re-read 0 blocked 13 out 0 superseded 7 | edits 35 over 16 rows
check ok                                                              (exit 0)

$ python Tools/scripts/status_audit.py --write      (exit 0, STATUS.md regenerated)
$ python Tools/scripts/status_audit.py --check
STATUS.md is current                                                  (exit 0)

$ python Tools/scripts/t_blocked.py --write
wrote BLOCKED_PROPOSALS.{json,md}: 17 blocked rows (13 ledger + 4 T6) of 216 in scope;
1 tested, 5 resolved: T-WP4=partially-unblocked                      (exit 0)
$ python Tools/scripts/t_blocked.py --check
PASS: 17 blocked rows re-derived (13 ledger + 4 T6) of 216 in scope; 1 attempts,
all evidence markers present; ledger sha256 unchanged                 (exit 0)
```

`status_audit` reports the same 216 in scope and **blocked 17**, so the tracker, the ledger and the
blocked sheet now agree with each other and with each other's hashes. The counts moved for one
reason and one only: `T-S6` left the blocked set.

## 4. Files changed

| file | change |
|---|---|
| `Working/Translation/T3_COVERAGE.md` | `T-S6` row: disposition blocked → next, the bridge cell (length 0.40 m, 13.500 s^-2, 1/2, −0.10, the fit errors) and the B-22 / B-23 references |
| `Working/Translation/T1_TRANSLATION.md` | `T-M3`, `T-S4`, `T-S5`, `T-R2`, `T-R3` cells: the audit's BmAK number, the replacement (T-S5) or the restatement (T-S4/T-M3/T-R2), plus T-26 |
| `Working/Translation/T_ROWS.jsonl` | regenerated by `t_rows.py build` (198 rows) — the `why` of each of the six rows |
| `Tools/scripts/t_rows.py` | `DISPO` entries for the six rows |
| `Tools/scripts/t_blocked.py` | the pins in section 2 (backup `.bak-20261106`) |
| `Working/Translation/BLOCKED_PROPOSALS.{json,md}` | regenerated (17 of 216, T-S6 in `resolved`) |
| `STATUS.md` | regenerated by `status_audit.py --write` |
| `Research/specs/B-22.md`, `Research/specs/B-23.md` | new cards for the members that do not exist |

## 5. UNKNOWN, and what would close it

1. **`hardpoint_offset_along_spring` as a rest position** — whether the engine reads −0.10 as ride
   height or as a force offset. A take on Q-2 A3 would settle it; until then the front bias is a
   placement, not a proof.
2. **`max_length_offset` semantics** (B-22) — 0 on all 166 fleet vehicles, so nothing in the data
   says whether 0.30 means "extends 0.30 m past rest" or something else.
3. **The unit of `BMWheelSuspensionStiffness`** — closed only to ±5.8%, because the 210 kg is a class
   default and no BmAK body setup serialises a mass. A second BmAK vehicle would test the rule
   one-sidedly; there is only one in the grab.
4. **The `Drag` / `DragNoLoad` / `DriftDrag` values** (T-R2) — card T-26.
5. **Whether pursuit mode re-authors a travel** (B-23) — the 1.51 m implied length has no fleet
   counterpart, so the mode's travel is UNKNOWN, not merely absent.
