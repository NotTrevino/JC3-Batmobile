# Chase 09 — F-65 … F-72 (native stay-upright/steer fields and the unit gaps)

Scope: `Research/BatmobileGrab/FOOTAGE.md` rows **F-65 … F-72** — three `VALUE-NATIVE` fields
(`StayUprightStiffness`, `StayUprightDamping`, `BattleModeSteerBias`) and five `UNDOCUMENTED` units
(`AirControl`, `BattleModeYawOffset`, `ArmourModeDamageReduction`, `BattleModeThrottleSpeed`,
`BattleModeSteerBiasRate`). Read-only: no existing document edited, no game launched, nothing
committed, nothing written under the game folder.

**Result: 1 of 3 values FOUND, 0 of 5 units settled.** `BattleModeSteerBias` is **0.0** (its value
is the zero default, proven by absence in the wheel class's default object). The two `StayUpright*`
values are **STILL UNKNOWN**: no shipped file carries them — not the archetypes (G1-21), not the
class default object, not any subclass default, not an ini — and the executable's two store sites at
0x6dc belong to a different class's layout. The five unit rows stay **STILL UNKNOWN**: three of them
(`BattleModeYawOffset`, `ArmourModeDamageReduction`, and — by extension — the two rate fields) have a
*value* whose unit no file on this machine states, and two of those values are **0**, which is the
same number in any unit, so no build depends on the answer.

| row | question | answer | provenance |
|---|---|---|---|
| F-65 | `StayUprightStiffness` value | **STILL UNKNOWN** — declared, never serialised, only a native constructor can set it; exe stores unattributable | — |
| F-66 | `StayUprightDamping` value | **STILL UNKNOWN** — same evidence; the exe has **0** store sites at 0x6e0 | — |
| F-67 | `BattleModeSteerBias` value | **0.0** (factor) — the wheel class's default object has no 0x320 tag, and no wheel archetype writes it | decoded (absence ⇒ zero) |
| F-68 | unit of `AirControl` | **STILL UNKNOWN** — value found: **0.05** (`Default__Pawn`, FloatProperty at 0x448); no file states the unit | value: decoded |
| F-69 | unit of `BattleModeYawOffset` | **STILL UNKNOWN** — shipped value **0** in all four archetypes (class default 16384); 0 is unit-free | value: decoded |
| F-70 | unit of `ArmourModeDamageReduction` | **STILL UNKNOWN** — shipped value **0** in three of four, `—` in Joker (class default 20); 0 is unit-free | value: decoded |
| F-71 | unit of `BattleModeThrottleSpeed` | **STILL UNKNOWN** — shipped value **10.0** (class default 5.0); no file states the unit | value: decoded |
| F-72 | unit of `BattleModeSteerBiasRate` | **STILL UNKNOWN** — shipped value **3.0** (class default, chase-07); no file states the unit | value: decoded |

## Evidence

### Class default objects (route 1)

`Default__SVehicle`, `Default__SVehicleWheel`, `Default__Pawn` are in
`E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\Engine.upk`;
`Default__RVehicleBatmobileBase` is in `BmGame.upk` (same folder). They are the layer G1-21 never
read: `objects.jsonl` covers only the 15 `Playable_Batmobile*` packages.

```
$ python Tools/scripts/chase/chase09_cdo.py --find
Pawn                     Engine.upk export 9699
RVehicleBatmobileBase    BmGame.upk export 10923
SVehicle                 Engine.upk export 11160
SVehicleWheel            Engine.upk export 29506

$ python Tools/scripts/chase/chase09_cdo.py --class SVehicle --dump --json E:/Modding/ArkhamKnight/_grab/chase/svehicle_cdo.json
=== Default__SVehicle (Engine.upk, export 11160, class SVehicle, 408 B)  tags 32, stop=eof
    -- card offsets on SVehicle:
       StayUprightRollResistAngle         @0x06d4  absent
       StayUprightPitchResistAngle        @0x06d8  absent
       StayUprightStiffness               @0x06dc  absent
       StayUprightDamping                 @0x06e0  absent
```

The block is serialised around the four absences, which is the control: 0x6c8 `VectorProperty`
(1,1,1), then **0x6e4** `ObjectNCRProperty -> Default__SVehicle.MyStayUprightSetup` and **0x6ec**
`-> …MyStayUprightConstraintInstance`, then 0x70c…0x724 with floats. A property that differed from
its zero default would appear between 0x6c8 and 0x6e4; none does.

`--class SVehicleWheel` (22 tags) has 0x2f8/0x308 `NameProperty`, **0x318 = 5.0**, and **nothing
above 0x318** — `BattleModeSteerBias` at 0x320 is the first field past the last tag, so its cooked
value was zero.

`--class Pawn` (59 tags): **0x448 `AirControl` = 0.05000000074505806** (FloatProperty).

`--class RVehicleBatmobileBase` (181 tags): **0x11e4 `StrafeCooldown` = 0.75**, **0x1910
`BattleModeYawOffset` = 16384** (IntProperty), **0x1918 `ArmourModeDamageReduction` = 20**
(IntProperty). The four shipped `SimulationModel`/vehicle archetypes override both ints to **0**
(MODES.md; re-checked in `objects.jsonl`, which holds all four packages).

### Subclass / archetype scan (still route 1)

Every `Default__*Vehicle*` / `Default__*Pawn*` export in `Engine.upk` (1,488 `Default__` exports) and
`BmGame.upk` (2,975) was walked for the six offsets: **no object carries 0x6d4/0x6d8/0x6dc/0x6e0 for
a vehicle class** (the only hits are `Default__AkPlayerVehicleSoundInfo` at 0x6d8/0x6e0, an audio
object — rejected lookalike), `Default__Pawn` carries 0x448, and 0x320 appears only on
`RVehicleBehaviour_RunAway`/`_Wander` and `RVehicleSimBatmobile` (unrelated classes).

### Native code (route 2)

```
$ python Tools/scripts/chase/chase09_native.py 0x6dc
-- disp 0x6dc (1756): 2 store-form hit(s)
   file 0x0018f4ac -> VA 0x1401900ac  movss [reg+0x6dc], xmm
      VA 0x140190067  movss    xmm0, dword ptr [rbx + 0x6dc]
      VA 0x14019006f  movss    xmm1, dword ptr [rip + 0x1a314c5]   ; [0x01bc033c] = 1.0
      VA 0x140190098  divss    xmm6, dword ptr [rbx + 0x6e8]
      VA 0x1401900ac  movss    dword ptr [rbx + 0x6dc], xmm1
$ python Tools/scripts/chase/chase04_native.py 0x6e0
-- disp 0x6e0 (1760): 0 store-form hit(s)
```

**Not adopted.** The two 0x6dc sites are one clamp loop (`x += dt / [0x6e8]`, clamped to 1.0) that
also treats **0x6e4 and 0x6e8 as floats** — on `SVehicle`, 0x6e4 is an *object pointer* to
`RB_StayUprightSetup`, so this code is a different class using the same small displacement. There is
no symbol, no property-name string in the exe and no way to attribute the site to `SVehicle`;
0x6e0 has no site at all. This is the same wall chase-06 hit for F-44/F-45.

### Other shipped text (cross-check, not evidence of a value)

`BmGame\Config\*.ini` (10 files) contains no occurrence of `StayUpright`, `AirControl` or `SteerBias`
— no shipped config documents any of these fields.

## F-65 · `StayUprightStiffness`

**STATUS: STILL UNKNOWN.** No shipped file carries a value: absent from `Default__SVehicle`
(control: 0x6c8 and 0x6e4/0x6ec present), absent from every `Default__*Vehicle*` in `Engine.upk` and
`BmGame.upk`, absent from the four archetypes (MODES.md), and the setup object it would configure
(`RB_StayUprightSetup`) is native and carries no serialised tags. The executable has two store sites
at 0x6dc but they belong to another class's layout (0x6e4/0x6e8 read as floats).
Routes tried: (1) class default objects + subclass scan — no value; (2) exe — 2 sites, unattributable
and demonstrably not this field; (3) not a frame-measurable quantity (a constraint stiffness is not
visible in the captures); (4) not used, and no published source could outrank a file value (R4).
Provenance: none — the row must stay `UNKNOWN`.

## F-66 · `StayUprightDamping`

**STATUS: STILL UNKNOWN.** Same evidence as F-65 for 0x6e0, and the executable has **0** store-form
sites at that displacement — so there is not even a candidate site to reject.
Routes tried: (1) no value; (2) 0 sites; (3)(4) as F-65.
Provenance: none.

## F-67 · `BattleModeSteerBias`

**STATUS: FOUND. 0.0** (factor — `MODES.md` unit column says factor for this field).
Evidence: `Default__SVehicleWheel` (Engine.upk export 29506, 22 tags) has its last serialised tag at
0x318 = `5.0`; the field at 0x320 is the first offset past it and carries no tag, so the cooked value
was zero. No wheel archetype writes 0x320 (scan above; the 0x320 hits are `RVehicleBehaviour_*` and
the sim class, not a wheel), so the class default is what the car inherits.
Provenance: `decoded` (absence ⇒ zero, with the block's last-tag control stated). Routes tried:
(1) found as zero; (2) not needed; (3) a bias factor is not separable from steering input in the
captures.

## F-68 · unit of `AirControl`

**STATUS: STILL UNKNOWN (the unit).** The **value** is found: `Default__Pawn` (Engine.upk export
9699, 59 tags), FloatProperty **0x448 = 0.05000000074505806**.
What the files say about the unit: nothing. MODES.md's unit column says "engine value"; the type is
`float`; no ini, comment, enum or sibling field on this machine names the quantity (a fraction of
max acceleration, an acceleration, and a per-second rate are all consistent with 0.05, and the files
do not choose between them). It is **not** adopted as a factor.
Routes tried: (1) value found, unit not stated; (2) an attribution of `[pawn+0x448]` reads in the exe
is not possible for a 0x448 displacement (hundreds of sites, stripped binary); (3) a unit cannot be
measured from footage, only a value; (4) not used as a value source (R4).
Provenance of the number: `decoded`. Unit: unresolved.

## F-69 · unit of `BattleModeYawOffset`

**STATUS: STILL UNKNOWN (the unit).** The **shipped value is 0** in every one of the four
archetypes (`MODES.md`, re-confirmed from `objects.jsonl`), so the unit has no effect on any build:
0 is 0 whatever the scale.
What the class default adds (new in this chase): `Default__RVehicleBatmobileBase` (BmGame.upk export
10923, 181 tags) carries **0x1910 = 16384** as an `IntProperty`. 16384 is exactly 65536/4, i.e. a
quarter turn **if** the encoding is UE3 rotator units (65536 per 360°) — and Rotator fields in the
same engine are stored as int triples of that magnitude (`Default__Pawn` 0x214 `RotatorProperty =
[20000, 20000, 20000]`, Engine.upk export 9699). That is a consistent reading, **not a proof**: no
file on this machine states the encoding, so the unit is not adopted. It is recorded here as the
only candidate the numbers suggest, flagged as inference.
Routes tried: (1) class default object — value found, unit not stated; (2) a unit is not a constant
in the exe; (3) not measurable from footage (the shipped value is 0, so there is nothing to see);
(4) not used (R4).
Provenance of the number: `decoded`. Unit: unresolved.

## F-70 · unit of `ArmourModeDamageReduction`

**STATUS: STILL UNKNOWN (the unit).** The **shipped value is 0** in three of the four packages and
`—` (not serialised) in the Joker package (`MODES.md`), so again the unit cannot affect a build.
New in this chase: `Default__RVehicleBatmobileBase` carries **0x1918 = 20** as an `IntProperty`.
The magnitude 20 is compatible with a percentage, an integer factor or an absolute value; the files
say none of those, and `MODES.md` already records "int, undocumented scale". No ini, comment or
enum on this machine names the scale. Not adopted.
Routes tried: (1) value found, unit not stated; (2) the exe cannot attribute reads of a small
displacement (and 0x1918 has no clean store site); (3) not measurable from footage (shipped value
0); (4) not used (R4).
Provenance of the number: `decoded`. Unit: unresolved.

## F-71 · unit of `BattleModeThrottleSpeed`

**STATUS: STILL UNKNOWN (the unit).** The **shipped value is 10.0** in all four archetypes
(`MODES.md`); `Default__RVehicleSimBatmobile` carries **0x2ec = 5.0**, which the archetypes override
to 10.0 — a fact worth recording, because it shows the archetype does set this field deliberately.
`MODES.md`'s unit column says "undocumented (rate-sized)": the field sits in a block of cm/s speeds
(`TurningModeMaxSpeed` 0x2c4, `BattleModeMaxSpeed` 0x2f0 = 1200.0) but 10.0 is not a speed any of
those values makes sense of, and no file states the quantity. Not rescaled, not assigned a unit.
Routes tried: (1) value found, unit not stated; (2) unattributable read of a small displacement;
(3) a throttle ramp is a per-tick quantity, not visible in the captures; (4) not used (R4).
Provenance of the number: `decoded`. Unit: unresolved.

## F-72 · unit of `BattleModeSteerBiasRate`

**STATUS: STILL UNKNOWN (the unit).** The **value is 3.0** — `Default__RVehicleSimBatmobile` 0x3c4
(chase-07), not overridden by any archetype. The unit is not stated by any file.
One candidate the data allows, flagged as inference only: if `BattleModeSteerBias` (F-67, 0.0,
`SVehicleWheel` 0x320) is a factor and this is its rate, the unit would be "bias per second". The
two numbers cannot test that (0.0 × anything stays 0.0), so it is recorded as a candidate, not a
unit. `MODES.md` keeps the row `undocumented`.
Routes tried: (1) value found, unit not stated; (2) a unit is not a constant in the exe; (3) not
visible in the captures; (4) not used (R4).
Provenance of the number: `decoded`. Unit: unresolved.

---

## What this chase changes, and what it cannot

**Closed:** F-67 → `RESOLVED` / `FILE-VALUE`, value **0.0** (absence ⇒ zero in the wheel class's
default object, no archetype override).

**Narrowed, still open:**

| row | narrowed to |
|---|---|
| F-65 | not in any shipped package or default object; a native-constructor value only; the one exe site block is another class's |
| F-66 | same, and the exe has no store site at all at 0x6e0 |
| F-68 | value **0.05** is decoded; the unit is stated by no file (not a factor by assumption) |
| F-69 | shipped value **0** (unit-free); class default **16384**; rotator-unit reading is a candidate, not adopted |
| F-70 | shipped value **0** (unit-free); class default **20**; scale stated by no file |
| F-71 | shipped value **10.0** (class default 5.0); unit stated by no file |
| F-72 | shipped value **3.0**; unit stated by no file |

**Limits.** (1) Absence-as-zero (F-67) uses the cooked-default-object rule — a property differing
from its zero default is written — with the block's last-tag position as control; the residual risk
is a runtime assignment, and none exists in the shipped packages. (2) The executable route was
attempted for F-65/F-66 only; offsets this small are shared across classes, the binary is stripped,
and the one 0x6dc block self-identifies as another class (it reads SVehicle's pointer slot 0x6e4 as
a float), so it is rejected rather than adopted. (3) No unit row was closed: a unit is not a value
that a package or a frame can carry, and no shipped text on this machine documents these fields.
(4) Footage was not used for any row: a unit is not measurable from video, and every row here either
has a file value or has no visible quantity at all (R4: a file value always beats footage).
(5) Nothing under the game folder was written; the game was not launched.

Scripts: `Tools/scripts/chase/chase09_cdo.py` (`--find`, `--class … --dump`, `--json`) and
`Tools/scripts/chase/chase09_native.py` (Capstone window around a store site). Decodes:
`E:/Modding/ArkhamKnight/_grab/chase/svehicle_cdo.json`, `…/wheel_cdo.json`.
