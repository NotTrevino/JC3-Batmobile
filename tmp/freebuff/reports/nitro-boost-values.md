STATUS: done — every BmAK boost value that is readable from files is listed with its source, the
translation row that covers it (or `none`), and the JC3 donor side it lands in. Output is
`Working/Translation/BOOST_COVERAGE.md`, generated and verified by
`Tools/scripts/t_boost_coverage.py --check` (`CHECK_EXIT=0`). No translation row was edited.

## Files written

* `Tools/scripts/t_boost_coverage.py` — parses the BmAK sim/class defaults, the donor `USAGES.md`
  section 6 row, `current.json` and `T_ROWS.jsonl`; `--write` emits the document, `--check`
  re-derives every number, rebuilds every line, compares byte-for-byte and asserts the row
  citations. It refuses to run if any cited `file:line` no longer carries the claimed text.
* `Working/Translation/BOOST_COVERAGE.md` — 9,572 chars, 14 BmAK values, 7 rows cited.
* `tmp/freebuff/reports/nitro-boost-values.md` — this report.

## The values, in short

**Thrust (readable):** `FakeExtraSpeedMax` 3500 cu (`RVehicleBatmobileBase` @7156,
CLASS_DEFAULTS.md:265), `FakeExtaSpeedAccel` 600 cu/s² (@7160, :266), `FakeExtaSpeedDecel`
2000 cu/s² (@7164, :267), and `BoostTorqueVSpeedCurve` 7 points −1500→0 … 3000→150
(MECHANICS.md:113). On the project convention (3000 cu = 108 km/h) the derived burst is
min(3500, 600×2) = 1200 cu = **43.2 km/h**, exactly the applied `extra_top_speed`.

**Duration (readable, no JC3 field):** `BoostDuration` **2 s** (@664, `Working/HUD/CLUSTER.md:50`)
and `BoostDurationDonut` **6 s** (@688, :55), both from `RVehicleSimBatmobile.g.cs`.
`BoostDuration` enters JC3 only as the duration term of T-B2's `min()`; no row writes a JC3
duration, and JC3's own `full_nitro_use_time` 4 s / 8 s are donor defaults with no row.

**Recharge (readable, no row):** `BoostCooldown` InlineArray 3, tier 0 = **12 s** (@668/672/676,
`CLUSTER.md:51`); `BoostCooldownUpgradeLevel` (@680) and `DriftingBoostCooldown` (@684) are
declared with no CDO default. None has a boost row; `DriftingBoostCooldown` is covered only by
the drift row T-DR1. JC3's `full_nitro_refill_time` 2 s / `nitro_refill_min_speed_kph` 20 are
donor defaults, also without a row.

**Speed cap:** the boost-additive cap is `FakeExtraSpeedMax` 3500 cu = 126 km/h, covered by T-B2;
the base `SVehicle.MaxSpeed` 4000 cu = 144 km/h (CLASS_DEFAULTS.md:163) has no row; the 336.4 km/h
target is T-E5's wiki figure, labelled *assumed*, not a file value.

**Rows that cover boost:** T-B1 (torque ratio 2.0 of 1.30→2.10; curve recorded by T-MD4),
T-B2 (`extra_top_speed` 43.2 from cap × accel × duration), T-B3 (grip 1.0, absence proof),
plus T-MD1 (afterburner = nitro, push 15,000 N), T-DM7 (`ImpactBoostMod` out), T-DR1
(`DriftingBoostCooldown` as drift), T-FX3 (flame, blocked), T-WP11 (booster mesh).

**BmAK values with no row:** `FakeExtaSpeedDecel` 2000 cu/s²; `BoostCooldown` 12 s (recharge);
`BoostCooldownUpgradeLevel`; `BoostDurationDonut` 6 s; `CurrentBoostTimer` 1.0; `SVehicle.MaxSpeed`
4000 cu (base cap); `RVehicleBatmobileBase.InfiniteBoost` bit @4568. `BoostDuration` and
`DriftingBoostCooldown` are only indirect/other-row coverage, as noted above.

**Donor-side values with no BmAK source and no row:** `full_nitro_use_time` 4/8 s,
`full_nitro_refill_time` 2 s, `nitro_refill_min_speed_kph` 20, `push_force` 15,000 N (BmAK has no
push member at all: thrust is accel/decel + torque curve), `heat_boost`/`turbo_jump` (T-B4).

## Commands and verbatim output

```
$ python Tools/scripts/t_boost_coverage.py --write
wrote Working\Translation\BOOST_COVERAGE.md (9572 chars)

$ python Tools/scripts/t_boost_coverage.py --check
rows parsed 198 | values 14 | covered by a row 7 | no row 7
  thrust    `BoostTorqueVSpeedCurve` 7 points             -1500.0 ? 0.0  -300.0 ? 200.0  0.0 ? 260.0  1500.0 ? 260.0  2100.0 ? 220.0  2800.0 ? 200.0  3000.0 ? 150.0 -> T-B1
  thrust    `FakeExtaSpeedAccel`                          600 cu/s?                              -> T-B2
  thrust    `FakeExtraSpeedMax`                           3500 cu = 126 km/h                     -> T-B2
  duration  `BoostDuration`                               2 s                                    -> T-B2 (as a term only)
  duration  `BoostDurationDonut`                          6 s                                    -> NO ROW
  recharge  `BoostCooldown` tier 0                        12 s                                   -> NO ROW
  recharge  `BoostCooldownUpgradeLevel`                   no default                             -> NO ROW
  recharge  `DriftingBoostCooldown`                       no default                             -> T-DR1
  thrust    `FakeExtaSpeedDecel`                          2000 cu/s?                             -> NO ROW
  thrust    `ImpactBoostMod`                              1.5 (CLASS_DEFAULTS.md:260)            -> T-DM7
  speed cap `SVehicle.MaxSpeed`                           4000 cu = 144 km/h                     -> NO ROW
  speed cap wiki 209 mph / 336 km/h with afterburner      not a file value                       -> T-E5
  state     `RVehicleBatmobileBase.InfiniteBoost`         bit @4568, mask 536870912 (SAMPLER_FIELDS2.md:96) -> NO ROW
  state     `CurrentBoostTimer`                           1 (init)                               -> NO ROW
factor 0.036000000000000004 km/h per cu (from T-B2) | burst 1200.0 cu = 43.2 km/h | cap 126.00000000000001 km/h | base 144.00000000000003 km/h | applied extra_top_speed 43.2000008
PASS: every BmAK boost value is classified against the rows; T-B1/T-B2/T-B3 cover the torque cap and accel, and decel, duration, recharge, donut, base cap and the boost flags have no row (listed in section 4)
CHECK_EXIT=0
```

(`?` is the console's cp1252 rendering of `→`/`²`; the document is UTF-8 and carries the real
characters. The factor line prints raw floats in the console; the document uses `0.036`.)

Evidence greps used to locate the values (all cited lines are re-checked by the script):

```
$ grep -n -E "FakeExta|FakeExtra|BoostDuration|BoostCooldown|InfiniteBoost|MaxSpeed" \
    Research/BatmobileGrab/CLASS_DEFAULTS.md Research/BatmobileGrab/SAMPLER_FIELDS2.md
163: | 83 | `0x0358` | 1808 | `MaxSpeed` (SVehicle) | FloatProperty | 4000.0 | decoded | Engine\SVehicle.g.cs:1376 (off 1808) |
265: | 87 | `0x0560` | 7156 | `FakeExtraSpeedMax` (RVehicleBatmobileBase) | FloatProperty | 3500.0 | decoded | ...
266: | 88 | `0x0568` | 7160 | `FakeExtaSpeedAccel` ... | 600.0 | decoded | ...
267: | 89 | `0x0570` | 7164 | `FakeExtaSpeedDecel` ... | 2000.0 | decoded | ...

$ sed -n '48,56p' Working/HUD/CLUSTER.md
| RVehicleSimBatmobile.g.cs | `BoostDuration` | float | 664 | 2.0 |
| RVehicleSimBatmobile.g.cs | `BoostCooldown` | float | 668 | 12.0 |
| RVehicleSimBatmobile.g.cs | `BoostCooldownUpgradeLevel` | int | 680 | None |
| RVehicleSimBatmobile.g.cs | `CurrentBoostTimer` | float | 808 | 1.0 |
| RVehicleSimBatmobile.g.cs | `DriftingBoostCooldown` | float | 684 | None |
| RVehicleSimBatmobile.g.cs | `BoostDurationDonut` | float | 688 | 6.0 |

$ sed -n '552p' Research/JC3Grab/USAGES.md
| input (physics) | `arcade.nitro_boost`: torque x2, grip x2, `push_force` 15000, `boost_blend_time` 0.2 s, `extra_top_speed` +40 km/h; `nitro_boost_upgraded`: push 20000, +80 km/h | donor `custom_land_global.vmodc` |
```

`CONFIG.md` contributes bindings only, not magnitudes: `pBatmobileBoost` = `{PAD_Y}` (l.298),
`kBatmobileBoost` = `{PC_LMB}` (l.326), `DefaultPursuitKeyMap` ability
`$GFxUI.KeyboardControls.Afterburner` (l.443).

## No row edits

`Working/Translation/T_ROWS.jsonl` was not written: the script only reads it (`json.loads` per
line) and cites row ids. `T-B1`, `T-B2`, `T-B3`, `T-B4`, `T-DM7`, `T-DR1`, `T-E5`, `T-FX3`,
`T-MD1`, `T-MD4`, `T-WP11` are referenced by id; their `cells` are checked to contain the JC3
member the table claims.

## UNKNOWNs

1. **Per-slot `BoostCooldown` values** — the InlineArray has three slots (668/672/676) and the HUD
   card records only the tier-0 value 12.0 s. Where: `RVehicleSimBatmobile` default export or
   archetype data. Not readable in the decodes here.
2. **`BoostCooldownUpgradeLevel` / `DriftingBoostCooldown` shipped defaults** — declared, no CDO
   value (`None` in the HUD card); the 1.5 s figure in `MECHANICS_NAMES.md:73` is a live-object
   read, not a class default.
3. **Afterburner start/cutoff timing** — `fAfterburnerStartTime` (8584) and
   `fAfterburnerCutoffStartTime` (8596) have no CDO default (CLASS_DEFAULTS.md section 6), so the
   edges of a burst are UNKNOWN.
4. **Whether JC3's meter time and BmAK's fixed burst are equivalent** — no file states it; the
   build keeps JC3's 4/8 s use-time and BmAK's 2 s `BoostDuration` side by side. This is a
   modelling gap, not a decoded value.
5. **`ImpactBoostMod` mismatch** — CLASS_DEFAULTS.md:260 decodes 1.5, T-DM7's requirement cell
   says 2.0. Recorded in section 7 of the document, not resolved here (outgoing-damage row, `out`).
6. **`BoostCooldown` vs `bInfiniteBoost` semantics** — both members exist (sim @660/668 and base
   @4568) but no file here states whether the cooldown array is per-tier recharge or a lockout;
   the row-less classification is by name and offset only.

COMPROMISES: none — no lore or gameplay value is changed by this card; it is a read-only audit.
