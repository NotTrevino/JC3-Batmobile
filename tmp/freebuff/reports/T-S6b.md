# T-S6b - JC3 suspension parameter set vs BmAK's suspension fields

STATUS: done - the parameter set is decoded, BmAK's matching fields are decoded by name and offset,
and the stiffness unit question is settled by a fleet-wide oracle. Every BmAK *value* stays UNKNOWN
(no project file decodes one), so the numeric stiffness bridge is UNKNOWN in its numbers while being
derived in its form.

## Answer in one paragraph

JC3 does not put suspension inside a handling module - it has a dedicated `Suspension` module
(49 rows on the donor, 16 named fields per axle plus a per-wheel hardpoint array). It carries a
spring rate (`front.strength` / `rear.strength`), **two** damper rates (`compression` for bump,
`relaxation` for rebound), a spring length with `min_length` and `max_length_offset`, a per-axle
`antirollbar_strength`, a `max_velocity_for_damp_clamp`, and `hardpoint_offset_along_spring`
(-0.0375 m front / -0.0429 m rear on the donor) which is the closest member to BmAK's
`SuspensionBias`. There is **no droop member**: only total travel.

BmAK's side is decoded from the class layout: `RVehicleSimBatmobile.BMWheelSuspensionStiffness`
(0x0304), `BMWheelSuspensionDamping` (0x0308), `BMWheelSuspensionBias` (0x030C),
`BMFrontWheelSuspensionBias` (0x0310), `BMFrontWheelMaxDroop` (0x0314),
`BMRearWheelMaxDroop` (0x0318), the pursuit-mode twins (`PM*`, 0x032C..0x0348),
`StationaryWheelSuspensionBias` (0x033C), `MaxPMSuspensionSpeed` (0x0340), plus
`SVehicle.ChassisMass` (0x0698) and `SVehicle.MassScale` (0x0814).

## The oracle (the part the brief asked for)

A spring must sag less than its own length. With four wheels each spring carries `m*g/4`, so
`sag = m*g/(4*k)`. If `strength` is mass-normalised the mass cancels; if it is absolute the sag
scales with the vehicle's mass. Scored on 166 fleet vehicles (mass 50-550,000 kg, median 2,000 kg,
65 above 3,000 kg):

| reading of `strength` | fits inside `length` | violated |
|---|---:|---:|
| mass-normalised, s^-2 | 164/166 | 2 (worst 1.0217x, both the same car: `v0510_car_solar_modernroadster`, 1000 kg, strength 20, length 0.12 m) |
| absolute N/m | 0/166 | 166 |
| absolute kN/m | 92/166 | 74 |

Decisive case, the heaviest vehicle `v0005_car_autostraad_minetruck` (550,000 kg, strength 30,
length 0.18 m): mass-normalised sag **0.0818 m** (fits); absolute N/m sag **44,962.5 m**;
absolute kN/m sag **44.96 m**. So `strength` is a **mass-normalised** rate (s^-2), and the absolute
readings are falsified - this oracle would fail if `strength` were N/m, and it does.

Consistency under that normalisation (derived, no mass term): damping ratio
`zeta = compression/(2*sqrt(strength))` spans 0.079..0.775 (median 0.198); natural frequency
`sqrt(strength)/(2*pi)` spans 0.318..1.424 Hz (median 0.872).

## The bridge

- **form (derived)**: `k_absolute = strength_JC3 * mass`, so `strength_JC3 = k_BmAK / m` and
  `c_JC3 = c_BmAK / m`. JC3 splits bump/rebound where BmAK has one damping field, so a BmAK
  damping value maps to *two* JC3 members (how it splits is UNKNOWN).
- **numbers (UNKNOWN)**: no project file decodes a numeric BmAK stiffness, damping, bias or droop.
  `DRIVE_MODES.json` *names* those fields (so the layout export reaches them) but carries no value,
  and `CLASS_DEFAULTS.json`'s CDO dump does not include `RVehicleSimBatmobile`'s
  `BMWheelSuspension*`. Where the numbers would be found: that class's class-default object in
  `BmGame.upk` (offset 0x0304 on the `RVehicleSimBatmobile` CDO), which no current script reads.
- **mass anchor exists**: `SVehicle.ChassisMass` (0x0698) on BmAK's side, `RigidBody.mass` in kg on
  JC3's (donor 975 kg). BmAK's mass unit is UNKNOWN, so the ratio still needs one decoded pair.

## T-S6 verdict

- **right** that there is no droop member and no decoded numeric stiffness bridge;
- **right** that the bias member has no proven sign/scale bridge;
- **wrong** if read as "the parameters are absent": the module carries the spring rate, both damper
  rates, anti-roll strength and a rest offset along the spring, and `strength`'s mass-normalised
  unit is now decoded by the oracle above.

## Files written

- `Tools/scripts/t_s6b_suspension.py` (`--write` / `--check`; the check re-reads the grab, the BmSDK
  layout and the oracle and rebuilds the `.md` byte for byte)
- `Working/Translation/T_S6B.md` (163 lines)
- `Working/Translation/T_S6B.json`
- `tmp/freebuff/reports/T-S6b.md` (this report)

No `Builds/bm-*` tree was edited; nothing was written to a game install; no game was launched.

## Commands and output (verbatim)

```
$ uv run python Tools/scripts/t_s6b_suspension.py --write; echo "WRITE_EXIT=$?"
wrote Working/Translation/T_S6B.json and Working/Translation/T_S6B.md (163 lines)
fleet 166 vehicles; sag fit per-mass 164/166, N/m 0, kN/m 92; heavy v0005_car_autostraad_minetruck sag 0.0818 vs length 0.180000007
WRITE_EXIT=0

$ uv run python Tools/scripts/t_s6b_suspension.py --check; echo "CHECK_EXIT=$?"
PASS Working/Translation/T_S6B.md re-derives byte for byte from the sources
PASS fleet decoded: 166 vehicles with Suspension + mass
PASS mass-normalised reading fits 164/166, worst overshoot 1.0217x
PASS absolute N/m reading is falsified on all vehicles (166)
PASS heaviest vehicle: absolute sag 44962.5 m >> length 0.180000007 m
PASS heaviest vehicle: mass-normalised sag 0.0818 m inside the spring
PASS damping ratios plausible: median 0.198 in 0.079..0.775
PASS BmAK stiffness field is in the layout with an offset
PASS map names the JC3 spring-rate member
PASS: T-S6b 0 failure(s)
CHECK_EXIT=0
```

The first `--write` run reported 0/166 for the mass-normalised reading because the oracle scored the
wrong sag column; that was a bug in the draft script (fixed before the run above, and the failure is
what exposed it). The two remaining misses are reported in the `.md` rather than hidden, and the
check asserts them by ratio (worst 1.0217x), not by removing them.

## Row text

`T-S6` does not appear in `Working/Translation/LEDGER_G3B.md` (`grep -n "T-S6"` returns nothing), so
the row's own wording is taken from the task brief. The claim "no suspension bias/droop member or
unit bridge" is what the sections above test.

## UNKNOWNs

1. **Every numeric BmAK suspension value** (stiffness, damping, bias, max droop, chassis mass).
   Tried: `BMSDK_OFFSETS.json` + `OFFSETS.md` (names/offsets only), `CLASS_DEFAULTS.json`
   (no `BMWheelSuspension*` in the CDO dump), `DRIVE_MODES.json` (names the fields, no values).
   Would be found: the `RVehicleSimBatmobile` class-default object in `BmGame.upk` at 0x0304.
2. **BmAK's stiffness/damping/mass units.** Nothing decodes a unit; the bridge gives the *rule* only.
3. **Bias semantics.** `hardpoint_offset_along_spring` is non-zero on the donor (-0.0375/-0.0429 m),
   but whether it means the same thing as `BMWheelSuspensionBias` (and at what sign/scale) is
   undecoded.
4. **The droop split.** JC3 has total travel only; how BmAK's `MaxDroop` would have to be expressed
   as `length`/`min_length` is undecoded because the donor ships `min_length` = 0 and
   `max_length_offset` = 0.
5. **Load sharing.** The oracle assumes four equal springs (`m*g/4`). `antirollbar_strength` is 0 on
   the donor, so it cannot be the cause of the 2% overshoot on the Solar roadster; whether the
   roadster's mass split differs is UNKNOWN.

## COMPROMISES

None. No build output was changed by this task.
