# review-T-WP5b - independent re-derivation of T-WP5b's numbers

VERDICT: **MINOR ISSUES.** The decode holds: I re-derived two numeric claims straight from the cooked
packages (not through `t_wp5b.py`) and both are exact to the byte, with the claimed offsets matching
the property-tag offsets in the stream. The numbers, the labels and the two-export method are sound.
What is not sound is smaller: the *names* in the member table come from a layout file the document
never cites, one "UNKNOWN route" mis-describes 0x9b8 as a byte offset inside a 276-byte default
object, the `[1]` array notation reads as index 1 for a 1-element array, and the "power levels = 4"
row contradicts its own evidence (`MaxPowerLevel` defaults to 0).

STATUS: **done**. `--check` exits 0 (27 PASS, 0 failures). Claims 1 and 2 were re-derived from
`BmGame.upk` / `Playable_Batmobile_SF.upk` through `Tools/scripts/upk_read.py` before
`Tools/scripts/t_wp5b.py` was opened; that script was never opened in this review. No game was run or
attached to, and no file under `E:/Games` was written (test ban).

## What I ran

The check the report names, verbatim:

```
$ cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/t_wp5b.py --check; echo "CHECK_EXIT=$?"
```

```
PASS range 7500 uu (got 7500.0)
PASS range 75.0 m (got 75.0)
PASS disable durations 2/4/8/12 s (got [2.0, 4.0, 8.0, 12.0])
PASS charge times 0/0.5/1/1.5 (got [0.0, 0.5, 1.0, 1.5])
PASS EMPImpulse 5000 / EMPVehicleImpulse 20000
PASS cooldown 2.0 s on the archetype over a 10.0 s class default
PASS RBatmobileEMP declares 16 members
PASS the archetype serializes 12 tags
PASS 4 discharge ParticleSystems, Stage_01..04
PASS 4 AkSwitchNames, LVL1..LVL4
PASS both fire events are Engine.Play_Batmobile_EMP
PASS impulse 15000.0 with RIF_Constant falloff
PASS impulse damage type RDmgType_Explosion
PASS charge particle EMP_Burst_Charge
PASS at least 4 config rows for the burst (got 18)
PASS tap detent in the config
PASS hold detent in the config
PASS RVehicleBatmobileBase declares DisabledByEMP and VulnerableToEMP
PASS 0 CEMPWeapon among 88 vehicle components
PASS truck_emp tune 100 / 25 m
PASS car_explosion_medium 500 / 5 m
PASS 307 pulses over 232 entities
PASS 14 unowned pulses
PASS the two CEMPWeapon users
PASS T_WP5B_EMP_BURST.md re-derives byte for byte from the packages
PASS T_WP5B_EMP_BURST.json re-derives byte for byte from the packages
PASS: T-WP5b 0 failure(s)
CHECK_EXIT=0
```

My own reader (`tmp/freebuff/scratch/twp5b_review.py`, written for this review, importing only
`upk_read.py`):

```
$ cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run python tmp/freebuff/scratch/twp5b_review.py
```

```
cooked roots: ['E:/Games\\Batman - Arkham Knight\\BmGame\\CookedPCConsole']
BmGame.upk 214757637 bytes
version 863 licensee 32995 exports 177031

find Default__RBatmobileEMP -> 46694 Default__RBatmobileEMP
class RBatmobileEMP size 276 tags 15 stop eof

tags named in the claims:
  DisableEnemyDuration   ArrayProperty  @2400 size=20   val=None           floats=[2.0, 4.0, 8.0, 12.0] count=4
  PowerLevelChargeTime   ArrayProperty  @2424 size=20   val=None           floats=[0.0, 0.5, 1.0, 1.5] count=4
  EMPImpulse             ArrayProperty  @2512 size=8    val=None           floats=[5000.0] count=1
  EMPVehicleImpulse      ArrayProperty  @2528 size=8    val=None           floats=[20000.0] count=1

all tag offsets (sorted):
  @ 290 ByteProperty   TickGroup                  'TG_PreAsyncWork'
  @ 785 ByteProperty   GadgetType                 'GA_BatmobileWeapon_EMPBurst'
  @ 792 ObjectNCRProperty -                          175558
  @2068 StrProperty    -                          'EMP Burst'
  @2084 BoolProperty   -                          True
  @2096 FloatProperty  -                          10.0
  @2360 FloatProperty  -                          1.0
  @2396 FloatProperty  -                          7500.0
  @2400 ArrayProperty  DisableEnemyDuration       [2.0, 4.0, 8.0, 12.0]
  @2416 ObjectNCRProperty -                          158039
  @2424 ArrayProperty  PowerLevelChargeTime       [0.0, 0.5, 1.0, 1.5]
  @2488 ObjectNCRProperty -                          143128
  @2496 ObjectNCRProperty -                          172088
  @2512 ArrayProperty  EMPImpulse                 [5000.0]
  @2528 ArrayProperty  EMPVehicleImpulse          [20000.0]

EMP_Burst exports:

 Playable_Batmobile_SF.upk 5490 exports
find ImpulseComponent0 -> 14
  RB_RadialImpulseComponent class=RB_RadialImpulseComponent tags=5 stop=eof
     @ 544 FloatProperty  -                        1000.0
     @ 552 BoolProperty   -                        True
     @ 316 ObjectProperty ReplacementPrimitive     0
     @ 364 FloatProperty  -                        0.9753715395927429
     @ 512 StructProperty LightingChannels         ''
  ImpulseComponent0        class=RB_RadialImpulseComponent tags=5 stop=eof
     @ 540 ByteProperty   ImpulseFalloff           'RIF_Constant'
     @ 544 FloatProperty  -                        15000.0
     @ 564 ObjectNCRProperty -                        -123
     @ 316 ObjectProperty ReplacementPrimitive     0
     @ 364 FloatProperty  -                        0.2468947470188141
  RB_RadialImpulseComponent class=RB_RadialImpulseComponent tags=2 stop=eof
     @ 316 ObjectProperty ReplacementPrimitive     0
     @ 364 FloatProperty  -                        0.9298989772796631
  ImpulseComponent0        class=RB_RadialImpulseComponent tags=2 stop=eof
     @ 316 ObjectProperty ReplacementPrimitive     0
     @ 364 FloatProperty  -                        0.8149052262306213
  ...
```

Secondary source for the member *names* and the 16 count (the package stores simple properties
offset-only, so the names cannot come from the package):

```
$ F="E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/BmGame/RBatmobileEMP.g.cs"; grep -c "Property:" "$F"
16
215:    /// FloatProperty: Range
219-        get { return BmSDK.Framework.MarshalUtil.ToManaged<float>(Ptr + 2396); }
224:    /// ArrayProperty: DisableEnemyDuration
228-        get { return BmSDK.Framework.MarshalUtil.ToManaged<BmSDK.TArray<float>>(Ptr + 2400); }
242:    /// ArrayProperty: PowerLevelChargeTime
246-        get { return BmSDK.Framework.MarshalUtil.ToManaged<BmSDK.TArray<float>>(Ptr + 2424); }
350:    /// IntProperty: MaxPowerLevel
354-        get { return BmSDK.Framework.MarshalUtil.ToManaged<int>(Ptr + 2548); }
```

## Claim 1 - "`RBatmobileEMP.Range` @2396 = 7500 uu = 75 m" - HOLDS

Re-derived independently: `Default__RBatmobileEMP` (export 46694, class `RBatmobileEMP`, size 276 B)
carries a `FloatProperty` tag at **offset 2396** with value **7500.0**. The offset comes from the
package's own tag header (`uint16 Offset`), not from the report, so the pairing "offset 2396 ->
7500.0" is decoded from `BmGame.upk` alone. The name `Range` is BmSDK's (`.g.cs:215`, `Ptr + 2396`),
which matches.

**Labels: correct as written.** `decoded` for 7500 uu at +2396 - right, and the value is a class
default (it sits in `Default__RBatmobileEMP`, not in the archetype), which is what the table says.
`75 m` as `derived (uu/100)` - right to label it derived, but see F5: the factor itself is not
evidenced anywhere in the files or elsewhere in this project.

## Claim 2 - "`DisableEnemyDuration[4]` @2400 = 2/4/8/12 s; `PowerLevelChargeTime[4]` @2424 = 0/0.5/1/1.5 s" - HOLDS

Re-derived independently and exactly:

* `@2400 ArrayProperty DisableEnemyDuration size=20 count=4 floats=[2.0, 4.0, 8.0, 12.0]` -
  20 bytes = 4-byte count + 4 x 4-byte floats, so the payload is self-consistent, not a
  stride guess.
* `@2424 ArrayProperty PowerLevelChargeTime size=20 count=4 floats=[0.0, 0.5, 1.0, 1.5]`.

Both offsets match BmSDK (`Ptr + 2400`, `Ptr + 2424`) and both values match the report's table to the
digit, including the seconds reading (the floats are already seconds, no conversion claimed).

**Labels: correct.** `decoded` for both rows; no derived step was needed or claimed.

## Findings

**F1 (minor) - the member names are uncited, and the document implies the packages alone supply
them.** §1 says the file is "Generated ... from the two packages' bytes and the research JSONs", but
the package serialises simple properties *without a name* (offset only - visible above as
`@2396 FloatProperty 7500.0` with no name). Every name in the 16-row table (`Range`,
`DisableEnemyDuration`, `ImpulseFalloff`, ...) comes from `BmSDK/Generated/BmGame/RBatmobileEMP.g.cs`
and, for the impulse component, from a layout that file does not have. Fix: add the `.g.cs:line` to
each row, or say once "names and kinds from BmSDK-AK's generated layout; offsets and values from the
packages".

**F2 (minor) - `EMPImpulse[1]` / `EMPVehicleImpulse[1]` reads as index 1.** Both arrays have
`count=1`; the value is at index 0 and the "[1]" is a length. A reader who takes it as an index gets
an out-of-range element. Fix: `EMPImpulse[0]` (length 1) or `EMPImpulse (1 element)`.

**F3 (minor) - "power levels = 4 ... `MaxPowerLevel` @2548 (both absent = 0)" contradicts itself.**
Neither `PowerLevel` @2544 nor `MaxPowerLevel` @2548 is serialised in the default object (the tag dump
has no such offsets), so the serialised default really is 0 - and a `MaxPowerLevel` of 0 cannot be the
evidence for 4 levels. The 4 is decoded from the two arrays' length (`count=4`), which is solid. Fix:
drop the parenthetical from the "4" row and state that the count is decoded from array length, while
`MaxPowerLevel >= 0` in the default object so whether it is a max index or a count is UNKNOWN.

**F4 (minor, but it is an error) - UNKNOWN #2's route points at the wrong thing.** It says to dump
`EMPForceFeedbackWaveform` "at offset 0x9b8 in the default object". 0x9b8 = **2488**, which is the
`EMPFFWaveForm` *field offset* in the layout - and the tag at that offset is
`@2488 ObjectNCRProperty -> 143128`, i.e. the waveform is the imported object 143128, not bytes at
0x9b8 of a **276-byte** export. Fix: "dump export 143128 (the `EMPFFWaveForm` object at field +2488)".

**F5 (minor) - the uu -> m factor is stated but not evidenced.** `75 m` is labelled
`derived (uu/100)`, which is honest, but `grep -rn "uu/100\|100 uu\|1 m = 100" Research/BatmobileGrab/*.md`
returns nothing, so no other document in this project pins 1 uu = 1 cm and the packages do not carry a
unit. The claim is only as good as that convention; one citation (or a second, independent
measurement, e.g. a known vehicle length in uu and m) would make it a real derivation.

## Would the oracle have caught a wrong number?

Yes for these two: `--check` re-decodes the packages and refuses to pass when a value moves, and the
report also ships `--tamper` with 5 probes. More importantly my re-derivation did not go through
`t_wp5b.py` at all - it opened the same exports with `upk_read.py` and read the tags itself - so the
agreement is two independent reads of the same bytes, not a script agreeing with itself.

## Not independently checked (out of the two-claim scope, named so nobody assumes otherwise)

* "the archetype serializes 12 tags, 3 variants" - the `EMP_Burst` archetypes are not in `BmGame.upk`
  (my search over its 177,031 exports printed none); they are in `Playable_Batmobile_SF.upk`, which I
  opened only for `ImpulseComponent0`.
* "cooldown 2.0 s on the archetype over a 10.0 s class default" - I did re-derive the **class
  default** half (`@2096 FloatProperty 10.0` in `Default__RBatmobileEMP`); the 2.0 override was not
  re-read.
* The four discharge ParticleSystems, the four `AkSwitchName`s, `Play_Batmobile_EMP` on both events,
  the wheel material names, and all 18 config rows.
* Every JC3 claim (routes a-e, the 88-component census, 307 pulses / 232 entities, the two
  `CEMPWeapon` users) - that is T-WP5's and 7322's ground, and this review is scoped to the BmAK
  numbers.

## UNKNOWNs (this review's own)

1. **`MaxPowerLevel` semantics** (max index vs count) - the packages show no value (default 0) and the
   `.g.cs` gives only `IntProperty` +2548. Route: `RBatmobileEMP` bytecode, or a live watch; not
   decidable from data.
2. **Whether the 12-tag / 3-variant count holds** - route: dump `Batmobile_EMP_Burst*` from
   `Playable_Batmobile_SF.upk` (5490 exports) with `upk_read.export_summary`.
3. **The uu -> m factor's provenance** - route: any project document that records it (none found by
   grep), or an independent length measurement.
4. **Which of the two `RB_RadialImpulseComponent` @364 floats is the "junk" one** - I see
   0.2468947470188141 on `ImpulseComponent0` (the instance the burst uses), and 0.9753715395927429 on
   the class default export; neither name is in any layout read here, matching the report's UNKNOWN #1.
   What the float *means* (a radius fraction? a mass?) is not in the files.
