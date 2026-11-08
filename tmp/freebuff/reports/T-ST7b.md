STATUS: done - the 0.5 s "floor" is disproved on the data: a **player** bike module ships 0.3 s and a
**car's AI twin** ships 0.25 s. No player car is below 0.5 s, no engine clamp can be shown (UNKNOWN),
and 0.25 s is reachable as data (one float) but unmeasured because of the test ban.

## Summary

Scanned all **6,045 decoded vehicle modules** (232 entities; 5,327 player + 718 `_ai`), of which
**271 are steering modules** (`LandSteering`, `MotorbikeSteering`), split by class and role.

**The floor claim.** T-ST7 said "the fleet's fastest rack is 0.5 s, so JC3's steering model cannot
be that quick". That is false as stated:

| class / role | min `t_to_full_steer_s` | modules at min | below 0.5 s |
|---|---:|---:|---:|
| `LandSteering` player (cars) | 0.5 | 6 | 0 |
| `MotorbikeSteering` player (bikes) | 0.3 | 2 | 9 |
| `LandSteering` AI twin | 0.25 | 4 | 4 |

- **A player module ships below 0.5 s**: the moped (`v3501_bike_solar_modernmoped`, civilian and
  debug) carries `t_to_full_steer_s` = **0.3 s**; three more bike builds carry 0.3 s on
  `max_speed_t_to_full_steer_s`. So the player steering path is not floored at 0.5 in the data.
- **0.25 s exists in the fleet**: 4 `LandSteering` AI twins ship exactly 0.25 s - the Mugello
  vintage sports variants, whose **player module in the same entity is 1.2 s**, which rules out
  "that value belongs to a different car". The AI `max_speed_t_to_full_steer_s` reaches **0.2 s**.
- **No player module reaches BmAK's 220 deg/s**: best player rate **116.7 deg/s** (moped, 35 deg /
  0.3 s), best player **car** rate **80 deg/s** (40 deg / 0.5 s), against 220 deg/s.
- **0.5 s is only the player-car minimum**, not an engine floor.

**Clamp question: UNKNOWN, with the reason pinned down.** The repo does carry real `.exe` decodes
(`CONSTRAINT_CODE.md`, `RUNTIME_LAYOUT*.md`, `PHYSICS_LIMITS_REVIEW.md`). Of the 22 files that name
`JustCause3.exe`, **4 mention steering at all** and **0 name this member**
(`t_to_full_steer_s` / `SteerSpeed`), so the land-steering update itself is not disassembled
anywhere in the repo. No clamp can be shown or excluded; the one-variable probe that would settle
it is barred by the test ban.

**Routes to 0.25 s (all listed with evidence in the note):**

| # | route | verdict |
|---|---|---|
| R1 | write 0.25 into the player car's `t_to_full_steer_s` (member +8, file byte 88, `0000803e`) | cheapest, data-only; the AI twin already ships it, player path unproven |
| R2 | use the `MotorbikeSteering` class for the car | amendment; proves the player path accepts <0.5 (0.3 s) but does not reach 0.25 |
| R3 | 0.25 in `max_speed_t_to_full_steer_s` | affects the high-speed band only |
| R4 | keep 0.5 s and raise the lock angle to match 220 deg/s | **impossible**: needs 110 deg, fleet max is 45 deg |
| R5 | yaw torque instead of the rack (drift block) | different mechanism, needs a trigger |
| R6 | input shaping (`steer_input_power_pc`, `steer_curve_falloff`, `saturation_zone`) | feel, not full-lock time |
| R7 | prove a native clamp | UNKNOWN, no steering decode |

**What it changes.** T-ST7's *reason* is wrong, its *decision* (0.8 s low / 0.6 s high) is still an
in-family pick because no player **car** ships below 0.5 s - but the `blocked` disposition is not
justified as a "JC3 model limit". It is a compromise: R1 would reach 0.25 s with one decoded
member. T-ST7 stays UNAPPROVED in `COMPROMISES_T.md`.

## Files written

- `Tools/scripts/t_st7b.py` - the generator (`--write` / `--check` / `--dump`).
- `Working/Translation/T_ST7B_FLOOR.md` - the note: answer, member table by class/role, every
  sub-0.31 module with its entity's player value, derived deg/s, clamp section, routes.
- `Working/Translation/T_ST7B_FLOOR.json` - the same record, plus histograms.
- `tmp/freebuff/reports/T-ST7b.md` - this report.

Not edited: `T_ST7_FLOOR.md`, `T_ROWS.jsonl`, `VOCABULARY.md`, any build, any game file.

## Commands and output

```
$ python Tools/scripts/t_st7b.py --write
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_ST7B_FLOOR.json
wrote E:\Modding\JC3-Batmobile\Working\Translation\T_ST7B_FLOOR.md
modules 271 player car min 0.5 player bike min 0.300000012 ai car min 0.25
```

```
$ python Tools/scripts/t_st7b.py --check
modules 271, player car 0.5, player bike 0.300000012, ai car 0.25, clamp docs 22, best 180.0 deg/s
OK: floor verified (player car 0.5, bike 0.3, AI 0.25), document and JSON identical
```

`--check` re-reads every entity, re-derives both files byte-for-byte, and asserts: player-car min is
exactly 0.5, player-bike min 0.3, AI-car min 0.25, at least one sub-0.31 row exists, the steering
module count is sane, and **no fleet module already reaches 220 deg/s** (which would void the route
table). The two bugs it caught during development were real: a self-referential exe scan (the
document it wrote matched its own marker) and list lengths used where counts at the minimum were
meant.

## UNKNOWNs

1. **Whether a native clamp exists on `t_to_full_steer_s`.** *Tried:* every `.md` in `Research/` and
   `Working/` for the executable marker, then for steering and for the member; 22 / 4 / 0 files.
   The exe decodes present cover PE layout, Havok constraint atoms and property schemas, not the
   land-steering update. *Where:* a `pefile`/`capstone` disassembly of that update, or the probe.
2. **Whether the player path honours 0.25 s.** The AI twin at 0.25 is evidence about the member and
   parser, not the player update. *Where:* the one-variable probe (0.25 in a build, measured at
   standstill), barred by the test ban.
3. **The meaning of `-1` in `t_to_full_steer_s`** (23 car modules) and in
   `max_speed_t_to_full_steer_s`. Read here as "no separate value / inherit" (they are excluded
   from min/median); the semantic is not decoded. *Where:* the steering update.
4. **Whether `steer_angle_min_speed_deg` is degrees of road-wheel angle or of steering input**; the
   deg/s column is derived on the former reading (same reading T-ST7_FLOOR uses).
5. **Bike-specific behaviour**: the 0.3 s moped module may be gated by `MotorbikeSteering`'s own
   path; whether a car could use that class unchanged is not decoded.

## COMPROMISES

T-ST7 (`blocked`, 0.8 s low / 0.6 s high) is an **unapproved** compromise, now with a documented
route out (R1): the files do not forbid 0.25 s, they simply contain no player car below 0.5 s. The
`blocked` label in `T_ROWS.jsonl` is not edited here (this card is read-only on other tasks' files);
the audit in `Working/Translation/COMPROMISES_T.md` already lists the row as UNAPPROVED.

Static only: no game launched, attached to or installed to; no build or install written.
