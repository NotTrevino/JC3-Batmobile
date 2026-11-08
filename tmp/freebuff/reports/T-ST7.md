# DONE — T-ST7 (steering floor)

STATUS: done

## Summary

The blocker's first clause is refuted by the shipped bytes. BmAK's 0.25 s is reproducible
(55° at the curve's 600 cm/s knot ÷ 220 °/s = 0.25 s in all four `RVehicleSimBatmobile`
archetypes), and **0.5 s is not a JC3 hard floor**:

- **player** `LandSteering.t_to_full_steer_s`: n=125, min **0.5 s**, 6 vehicles at 0.5, **none below**.
- **AI twin** (`*_land_steering_ai.vmodc`): n=125, min **0.25 s**, 4 modules at 0.25 — the four
  Mugello vintage-sports variants, whose player module is 1.2 s.

So 0.5 s is the lowest shipped **player** value, not a clamp: no decoded input contains a clamp
check, and the shipped data is not itself floored at 0.5 s (the AI twin proves the member and the
ADF parser accept 0.25 s). Whether the **player** steering update honours a value below 0.5 s is
**UNKNOWN until measured**; the one-variable probe and its exact edit target are in the findings
file. The BmAK 220 is decoded from the archetype tag stream at native offset **0x0DC**; only the
slot's *name* comes from the BMSDK table. The 55° is the curve value at 600 cm/s (standstill is
60°, i.e. 0.273 s) — the row's 0.25 s uses the 600 cm/s knot, and the Joker curve falls to 50° at
1100 cm/s, so "55° plateau" was too strong.

## Files written

| file | what |
|---|---|
| `Tools/scripts/t_st7.py` | the tool; `--write` generates, `--check` recomputes and compares byte for byte |
| `Working/Translation/T_ST7_FLOOR.md` | the findings (verdict, both re-derivations, exact member/offset, oracles) |
| `Working/Translation/T_ST7_FLOOR.json` | the same numbers, machine-readable |
| `tmp/freebuff/reports/T-ST7.md` | this report |

Nothing else was touched. No game process, no install, no build, no git.

## The exact member and offset

Target (staged donor module found on disk):
`E:/Modding/_gamedata/JC3grab/rc_merge/stage/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/v0300_car_kensington_sportsmuscle_land_steering.vmodc`

| quantity | value |
|---|---|
| ADF type | `LandSteering` |
| instance offset | 80 (0x50) |
| member | `t_to_full_steer_s` at **+8 (0x08)** |
| file byte of the float | **88 (0x58)** |
| current | `cdcc4c3f` = 0.800000012 s |
| for 0.25 s | `0000803e` |
| revert | write `cdcc4c3f` back |

BmAK-side equivalent: the FloatProperty at **0x0DC** in `RVehicleSimBatmobile` (220.0); 110.0
there gives 0.5 s at the same 55° knot.

## Commands run, with output

Fleet split (player vs AI twin), all land entities:

```
== land: entities with LandSteering = 250
  t_to_full_steer_s: n=250 positive=250 min=0.25 max=10
   bottom: [(0.25, 4), (0.5, 80), (0.8, 7), (0.9, 3), (1, 8), (1.1, 3), (1.2, 25), (1.4, 3)]
  max_speed_t_to_full_steer_s: n=250 positive=108 min=0.200000003 max=5
   bottom: [(0.2, 2), (0.5, 11), (0.6, 16), (0.7, 3), (0.8, 19), (0.85, 3), (1, 12), (1.2, 6)]
```

The 250 rows are 125 entities x (player + `_ai`). Split by module path:

```
player: modules=125 entities=125 | t_to_full_steer_s: n=125 pos=125 min=0.5 median=1.79999995
   bottom: [(0.5, 6), (0.8, 7), (0.9, 3), (1, 8), (1.1, 3), (1.2, 25)]
player: modules=125 entities=125 | max_speed_t_to_full_steer_s: n=125 pos=102 min=0.5 median=1.0
   bottom: [(0.5, 9), (0.6, 16), (0.7, 3), (0.8, 19), (0.85, 3), (1, 10)]
ai: modules=125 entities=125 | t_to_full_steer_s: n=125 pos=125 min=0.25 median=0.5
   bottom: [(0.25, 4), (0.5, 74), (1.5, 2), (2, 45)]
ai: modules=125 entities=125 | max_speed_t_to_full_steer_s: n=125 pos=6 min=0.200000003 median=0.5
   bottom: [(0.2, 2), (0.5, 2), (1, 2)]
player modules below 0.5: []
player modules ==0.5: 6
ai modules ==0.25: 4
```

BmAK archetype walk (`upk_read.best_walk`):

```
packages 15
Playable_BatmobileFunhouse_SF.upk sim exports [(5368, 'SimulationModel', 2328)]
   i 5368 tags 37 end 2326 why eof | @0xDC [(220.0, 2306)] | curve [[('0.0','60.0'), ('600.0','55.0'), ('1100.0','55.0'), ('1300.0','30.0'), ('2000.0','20.0')]]
```

(all four archetypes report `220.0` at tag payload byte 2306; the module layout probe below gives
the same for Joker/MK2/base.)

JC3 module bytes (member layout and value):

```
== v0300_car_kensington_sportsmuscle_land_steering.vmodc file bytes 1073 instance v0300_car_kensington_sportsmusc LandSteering off 80 size 60
  +  8 (0x08) t_to_full_steer_s                  float    size 4
  t_to_full_steer_s bytes at file 88 cdcc4c3f = 0.800000011920929
```

Final generation and check:

```
ok   bmak_archetypes
ok   bmak_steer_speed_220
ok   bmak_lock_55_at_600
ok   lock_time_025
ok   fleet_player_min_050
ok   fleet_ai_counterexample_025
ok   fleet_aux_min
ok   raw_member_offset_8
ok   raw_decode_agrees
ok   target_module
ok   write_bytes_025
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_ST7_FLOOR.md
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_ST7_FLOOR.json
write_exit=0
=== check ===
... same 11 lines ...
check ok
check_exit=0
```

## What the T-ST7 row should say next

Not "blocked: the fleet floor is 0.5 s" — that premise is false. The row's reason should read:
"0.25 s is shipped in the AI twin of four Mugello variants; the player path is UNKNOWN below
0.5 s and needs the one-variable probe at `t_to_full_steer_s` +8 (file byte 88 in the staged
module)." Whether to take 0.25 is a build decision; this task did not edit the row
(`T_ROWS.jsonl` belongs to another task).

## UNKNOWNs

1. **Does the player steering update honour `t_to_full_steer_s` < 0.5 s?** UNKNOWN. Tried: the
   fleet minimum (0.5, no player value below), the AI twins (0.25, but a different module
   consumer), the ADF type defaults (no clamp), and every decoded JC3 doc (no steering code).
   It would be shown by a one-variable probe build (write `0000803e` at file byte 88 and measure
   lock-to-lock) or by disassembling the steering update for a clamp — neither is available under
   this task's ban on builds, installs and game launches.
2. **The shipped raw player-module bytes for the other 124 entities.** Only a few module files are
   unpacked on disk; the fleet numbers therefore rest on the jc3grab entity decode. The sportsmuscle
   **AI** copy on disk reads 2.0 s, exactly its entity row, and every parsed copy puts the member at
   +8 — that is the byte-level confirmation of the decode. The sportsmuscle **player** copy under
   `b13b/unpacked` reads 0.8 s where the entity decode says 1.2 s, so that tree is a project build
   copy, not a shipped anchor; it is reported in the oracle table and excluded as evidence.
3. **The slot name at 0x0DC.** The value (220.0) and the offset are decoded from the archetype tag
   stream; the name `SVehicleSimCar.SteerSpeed` is named-sdk (`BMSDK_OFFSETS.json`, offset 220),
   not decoded from the package's own name table.
4. **The steer-angle reading of `StandardSteeringSpeedCurve`.** The 55° is a decoded curve value;
   reading its units as degrees of steer angle (rather than another quantity) is the derived step,
   inherited from T1's T-ST1 and not independently proven here.
