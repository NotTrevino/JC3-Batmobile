# Chase 04 — F-25 … F-32 (G1-21 mode fields with no archetype value)

Scope: `Research/BatmobileGrab/FOOTAGE.md` §6 rows **F-25 … F-32**, all `UNKNOWN` with reason
`VALUE-NATIVE`. Read-only chasing: no existing document edited, no game launched, nothing
committed.

**Result: 7 of 8 FOUND; F-25 is STILL UNKNOWN and the data now says why** — it is a runtime
countdown, not a tunable, and no shipped file carries a default for it. As in chase-02, the values
live in the **class default object** `Default__RVehicleBatmobileBase` in `BmGame.upk` (export
10923, 181 property tags, walk consumes 3184 of 3186 bytes, `eof`), which `objects.jsonl` never
read: G1-21 only had the 15 `Playable_Batmobile*` packages.

| row | field | value | provenance |
|---|---|---|---|
| F-25 | `ImpactRoadAssistTimer` | **no shipped value** — runtime countdown (executable: load, compare 0, `-= dt`, store) | decoded (absence) + native (behaviour) |
| F-26 | `ImpactRoadAssistMaxAngle` | **45.0 deg** | decoded |
| F-27 | `ImpactRoadAssistAngVelocityTime` | **0.25 s** | decoded |
| F-28 | `ImpactRoadAssistSteeringFactor` | **30.0** (factor, unitless) | decoded |
| F-29 | `ImpactRoadAssistLookAheadTime` | **1.0 s** | decoded |
| F-30 | `BattleModeTransformationAnimName` | **`Batmobile_V2_Tank_Spread_Open_Game`** (FName) | decoded |
| F-31 | `BattleModeWidth` | **265.0 cm** | decoded |
| F-32 | `BattleModeLength` | **430.0 cm** | decoded |

Units are the ones `MODES.md` already assigns by field name (deg / s / factor / name / cm); nothing
is rescaled.

## Evidence (one place for F-26 … F-32)

`E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk`, export **10923**
`Default__RVehicleBatmobileBase`:

| field | BmSDK offset | tag in the default object |
|---|---|---|
| `ImpactRoadAssistTimer` | 0x1758 = 5976 | **no tag** |
| `ImpactRoadAssistMaxAngle` | 0x176c = 5996 | FloatProperty `45.0` |
| `ImpactRoadAssistAngVelocityTime` | 0x1770 = 6000 | FloatProperty `0.25` |
| `ImpactRoadAssistSteeringFactor` | 0x1774 = 6004 | FloatProperty `30.0` |
| `ImpactRoadAssistLookAheadTime` | 0x1778 = 6008 | FloatProperty `1.0` |
| `BattleModeTransformationAnimName` | 0x193c = 6460 | NameProperty `'Batmobile_V2_Tank_Spread_Open_Game'` |
| `BattleModeWidth` | 0x1994 = 6548 | FloatProperty `265.0` |
| `BattleModeLength` | 0x1998 = 6552 | FloatProperty `430.0` |

The offset→field mapping is `BMSDK_OFFSETS.json` → `classes.RVehicleBatmobileBase.properties`
(5976 `ImpactRoadAssistTimer`, 5996 `ImpactRoadAssistMaxAngle`, 6000 `…AngVelocityTime`,
6004 `…SteeringFactor`, 6008 `…LookAheadTime`, 6460 `…TransformationAnimName`, 6548 `…Width`,
6552 `…Length`), and the tags sit exactly at those field offsets. The tag walk is not truncated:
it stops at `eof` after 181 tags.

Command and output (verbatim):

```
$ python Tools/scripts/chase/chase02_cdo.py --class RVehicleBatmobileBase --json E:/Modding/_BmAKgrab/chase/vehiclebase_cdo.json
...
    -- card offsets on RVehicleBatmobileBase:
       StrafeCooldown                     @0x11e4  SERIALISED 0.75
wrote E:/Modding/_BmAKgrab/chase/vehiclebase_cdo.json
```

The F-25 … F-32 offsets queried from that dump:

```
   0x1758 absent
   0x176c ('FloatProperty', 45.0, None)
   0x1770 ('FloatProperty', 0.25, None)
   0x1774 ('FloatProperty', 30.0, None)
   0x1778 ('FloatProperty', 1.0, None)
   0x193c ('NameProperty', 'Batmobile_V2_Tank_Spread_Open_Game', None)
   0x1994 ('FloatProperty', 265.0, None)
   0x1998 ('FloatProperty', 430.0, None)
```

**Control — the absence of 0x1758 is real, not a parse failure.** The *same* tag stream the
card's readers already walk carries the neighbouring `ImpactRoadAssist` fields from the shipped
`Playable_Batmobile_SF` archetype: offsets 5980 = 0.0, 5984 = 0.3330000042915344, 5988 = 90000.0,
5992 = 30000.0, 6012 = 2000.0. Those offsets sit in the same block (5976 … 6012, one float every
4 bytes), so a reader can see into the block; 5976 is simply not written. The same query finds **no**
archetype tag at any of 5976/5996/6000/6004/6008/6460/6548/6552 in any of the 15 packages.

**No subclass overrides them.** Scanning all 235 `Default__*Camera*` / `*Batmobile*` / `*Vehicle*`
objects in `BmGame.upk` for these eight offsets returns this default object only, plus one lookalike:

```
$ python Tools/scripts/chase/chase02_cdo.py --scan --offsets 0x1758,0x176c,0x1770,0x1774,0x1778,0x193c,0x1994,0x1998
-- scanning 235 Default__*Camera/Batmobile/Vehicle objects for offsets ['0x1758', '0x176c', '0x1770', '0x1774', '0x1778', '0x193c', '0x1994', '0x1998']
   Default__RVehicleBatmobileBase (export 10923): [(5996, None, 45.0), (6000, None, 0.25), (6004, None, 30.0), (6008, None, 1.0), (6460, None, 'Batmobile_V2_Tank_Spread_Open_Game'), (6548, None, 265.0), (6552, None, 430.0)]
   Default__RVehicleNPC (export 12268): [(5976, None, 2.0), (6008, None, 1.0)]
   -> 2 object(s) carry any of the card offsets
```

`Default__RVehicleNPC` at 5976 = 2.0 is **not** adopted: field offsets are class-scoped
(`MODES.md` makes the same point), the class is not in `BMSDK_OFFSETS.json`, so at 5976 it holds
whatever `RVehicleNPC` declares there — not `RVehicleBatmobileBase.ImpactRoadAssistTimer`. It is
recorded here as a rejected lookalike, not as a value.

## F-25 · `ImpactRoadAssistTimer`

**STATUS: STILL UNKNOWN — no shipped default exists.** The honest answer is that there is nothing
to copy: the field is a per-tick countdown. The card's own reason column said `VALUE-NATIVE`; the
executable now shows *what* it does.

Evidence — the only write to `[reg+0x1758]` in the shipped `BatmanAK.exe` (55 101 440 B) is a
decrement, at file offset 0x51308 / RVA 0x1000+0x1f08 / **VA 0x140051f08** (image base 0x140000000):

```
0x140051ee2: f30f108158170000    movss xmm0, dword ptr [rcx + 0x1758]   ; load the timer
0x140051ef3: 450f57d2            xorps xmm10, xmm10
0x140051efa: 410f2fc2            comiss xmm0, xmm10                    ; compare with 0.0
0x140051efe: 0f86dd040000        jbe  0x1400523e1                     ; leave when <= 0
0x140051f04: f30f5cc1            subss xmm0, xmm1                      ; -= delta time
0x140051f08: f30f118158170000    movss dword ptr [rcx + 0x1758], xmm0  ; store back
```

Reproduce with `python Tools/scripts/chase/chase04_native.py 0x1758` (finds the one store-form hit
and prints its file offset) and the capstone window above (script block in this session's log; the
exe is read in place, never patched, never run).

Scan for a *default* write (immediate store) anywhere in the exe: none — the scan reports
`0 store-form hit(s)` for an immediate-store form at 0x1758, and the single `movss` hit is the
decrement above. So no constant is written to it in code, and no package serialises it.

Caveats on that attribution: the exe is stripped and contains no `ImpactRoadAssist` string, so the
function is identified by field offset + behaviour (a float compared to zero and decremented by a
delta), not by symbol. That matches `ImpactRoadAssistTimer` being a countdown, which is *why* a
default would be meaningless — but the match is by offset, so the *name* of the field in that
routine is inferred, not proven.

What a port can use instead: the two duration fields the layout places either side of it are
serialised — `ImpactRoadAssistSceneryDuration` (0x175c): CDO **0.75 s**, V2 archetype **0.0 s**;
`ImpactRoadAssistEnemyDuration` (0x1760): CDO **1.5 s**, V2 archetype **0.333 s**. Which of them
seeds the timer is **not shown** by any file read here — UNKNOWN, and not asserted.

Routes tried: (1) class default object — absent there and in all 235 candidate default objects and
in all 15 archetypes; (2) executable static analysis — only a decrement, no default constant;
(3) captures — the timer is internal state, not visible in any footage; (4) published sources —
not used, and they could not outrank a file value (R4).

## F-26 · `ImpactRoadAssistMaxAngle`

**STATUS: FOUND. 45.0 deg.** `BmGame.upk` export 10923, FloatProperty at 0x176c (5996) = `45.0`;
`MODES.md` unit column: deg. Not overridden by any archetype or default object.
Provenance: `decoded`. Routes tried: (1) found; (2)(3)(4) not needed.

## F-27 · `ImpactRoadAssistAngVelocityTime`

**STATUS: FOUND. 0.25 s.** Same object, FloatProperty at 0x1770 (6000) = `0.25`; unit s by the name
convention in `MODES.md`. Provenance: `decoded`. Routes tried: (1) found.

## F-28 · `ImpactRoadAssistSteeringFactor`

**STATUS: FOUND. 30.0** (dimensionless factor, carried as shipped, not rescaled). Same object,
FloatProperty at 0x1774 (6004) = `30.0`. Provenance: `decoded`. Routes tried: (1) found.
Note: the field is named a *factor*, so 30.0 is not a percentage and is not converted to one.

## F-29 · `ImpactRoadAssistLookAheadTime`

**STATUS: FOUND. 1.0 s.** Same object, FloatProperty at 0x1778 (6008) = `1.0`. Provenance:
`decoded`. Routes tried: (1) found.

## F-30 · `BattleModeTransformationAnimName`

**STATUS: FOUND. `Batmobile_V2_Tank_Spread_Open_Game`** (FName; the "V2" is the Batmobile V2
variant, not the vehicle chassis). Same object, NameProperty at 0x193c (6460). The neighbouring
0x1944 tag is a second name (`Batmobile_V2_Tank_Spread_Close_Game`), which is the close-side
counterpart — recorded as context, not part of the row.
Provenance: `decoded`. Routes tried: (1) found.

## F-31 · `BattleModeWidth`

**STATUS: FOUND. 265.0 cm.** Same object, FloatProperty at 0x1994 (6548) = `265.0`; unit cm per
`MODES.md` (= 2.65 m). Provenance: `decoded`. Routes tried: (1) found.

## F-32 · `BattleModeLength`

**STATUS: FOUND. 430.0 cm.** Same object, FloatProperty at 0x1998 (6552) = `430.0` (= 4.30 m).
Provenance: `decoded`. Routes tried: (1) found.
`BattleModeHeight` (0x199c) is the next tag, 250.0 cm — outside this row set, noted only.

---

## Why G1-21 missed these, and what it means for FOOTAGE.md (read-only here)

`grab_modes.py` compares the BmSDK declaration inventory with `objects.jsonl`, and
`objects.jsonl` covers only the 15 `Playable_Batmobile*` packages (`GAME` glob in
`batmobile_grab.py`). The class default objects live in `BmGame.upk`, which no G1 reader opened.
The FOOTAGE.md sentence "not serialised in any of the four archetypes or their class defaults"
is right about the archetypes and wrong about "class defaults" — the defaults were never looked at.

Suggested status change (not applied): F-26 … F-32 → `RESOLVED` / `FILE-VALUE`; F-25 →
`UNKNOWN` with reason replaced by "no shipped default; runtime countdown (exe VA 0x140051f08)", so
the reason is now evidence rather than `VALUE-NATIVE`.

## Limits / UNKNOWNs of this chase

1. Class-default values are what every non-overriding instance inherits; the archetypes serialise
   nothing for these fields (verified at the byte-offset level, with neighbours present as a
   control), and no default object in `BmGame.upk` overrides them.
2. F-25's code attribution is by field offset and instruction shape, not by symbol — the exe is
   stripped and holds no `ImpactRoadAssist` strings.
3. F-28's 30.0 is a factor with no documented scale; F-26's 45.0 is degrees by name convention.
4. `BattleModeTransformationAnimName` names an animation; whether that sequence exists in the
   cooked `AnimSet`s is a separate question and was not checked here.
5. The executable scan only recognises direct `mov dword [reg+disp], imm32` and `movss
   [reg+disp], xmm` forms. It found zero immediate stores for any of the eight offsets, so no
   native constant is claimed for the seven found rows — their values are the serialised CDO tags.
6. Nothing was written under the game folder; extracted decodes are under
   `E:/Modding/_BmAKgrab/chase/`.
