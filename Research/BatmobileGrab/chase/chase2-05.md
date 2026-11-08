# Chase 05, second pass — F-33 … F-40

Read first: `chase-05.md`. It closed **0 of 8** rows, all `STILL UNKNOWN` with reason `VALUE-NATIVE`.
This pass re-ran its three measurements with the class default object's **tag stream** instead of a
name search, and **three of the eight are serialised after all**.

| row | field | status | value | provenance |
|---|---|---|---|---|
| **F-33** | `BattleModeHeight` | **FOUND** | **250.0 cm** (= 2.50 m) | `decoded` |
| F-34 | `JumpRampUpwardForce` | STILL UNKNOWN | — | — |
| **F-35** | `ImpactShakeAbandonedVehicleFactor` | **FOUND** | **3.0** (factor) | `decoded` |
| **F-36** | `ImpactShakeDestructiblesFactor` | **FOUND** | **3.0** (factor) | `decoded` |
| F-37 | `ImpactShakeCoolDown` | STILL UNKNOWN | — | — |
| F-38 | `BattleModeSpeedDelta` | STILL UNKNOWN | — | — |
| F-39 | `TurnOnSpotSteeringSpeedCurve` | STILL UNKNOWN | — (not a scalar) | — |
| F-40 | `BattleModeMoving` | STILL UNKNOWN | — | — |

`chase-05.md`'s conclusion was that "there is no number on this machine to copy". For F-33/F-35/F-36
there is, and the reason it was missed is a measurement flaw, not a missing file.

## Why the first pass saw nothing — two measurement flaws, both now measured

**1. A cooked float tag carries no name.** The first pass tested "`objects.jsonl` has 0 tags *named*
`BattleModeHeight` …". In this tag format a `FloatProperty` is `int16 type, uint16 offset, float32
value` — **there is no name field** (see `Tools/scripts/upk_read.py`'s header comment: only complex
types carry `FName name, int32 size, int32 array index`). A float can only be found by **offset**, so
a name search returns 0 for every float in the game, serialised or not. The same is true of the
"CDO-qualified 0 records" test in `GlobalPersistentCookerData.upk`: that manifest lists typed
*property names*, and it cannot tell you that a float was written.

**2. The class default object is a partial list, so absence is not a value.** Measured:

```
$ python - <<'EOF'   (walk Default__RVehicleBatmobileBase / Default__RVehicleSimBatmobile)
RVehicleBatmobileBase declared properties: 518
RVehicleSimBatmobile  declared properties: 130
Default__RVehicleBatmobileBase: 181 tags, stop=eof, 0 with float value 0.0
Default__RVehicleSimBatmobile: 58 tags, stop=eof, 0 with float value 0.0
EOF
```

181 of 518 and **zero** zero-valued float tags: the cooked CDO writes only the non-default part of
the object. That cuts both ways, and this pass uses it consistently:

* a **present** tag at a card offset is a real value (F-33/F-35/F-36, below);
* an **absent** tag is *not* "the value is 0" — it is "not written here", which is why F-34/F-37/
  F-38/F-39/F-40 stay UNKNOWN rather than being reported as 0.

## Evidence: the tags, with bytes

`BmGame.upk` export **10923** `Default__RVehicleBatmobileBase` (class `RVehicleBatmobileBase`,
3,186 B, 181 tags, walk stops at `eof`), image offset `image+0x1022d59`. Offsets are the BMSDK
`classes.RVehicleBatmobileBase.properties` offsets, and the payload is read straight out of the
decompressed image:

| offset | field (BMSDK) | type | image offset | bytes | value |
|---|---|---|---|---|---|
| 0x1994 | `BattleModeWidth` (F-31, already FOUND) | FloatProperty | `image+0x10230b7` | `00 80 84 43` | 265.0 |
| 0x1998 | `BattleModeLength` (F-32, already FOUND) | FloatProperty | `image+0x10230bf` | `00 00 d7 43` | 430.0 |
| **0x199c** | **`BattleModeHeight` (F-33)** | FloatProperty | `image+0x10230c7` | `00 00 7a 43` | **250.0** |
| 0x1cc4 | `ImpactShakeForceFactor` | FloatProperty | `image+0x1023425` | `0a d7 23 3c` | 0.01 |
| 0x1cc8 | `ImpactShakeVehicleFactor` | FloatProperty | `image+0x102342d` | `00 00 00 40` | 2.0 |
| **0x1ccc** | **`ImpactShakeAbandonedVehicleFactor` (F-35)** | FloatProperty | `image+0x1023435` | `00 00 40 40` | **3.0** |
| **0x1cd0** | **`ImpactShakeDestructiblesFactor` (F-36)** | FloatProperty | `image+0x102343d` | `00 00 40 40` | **3.0** |
| 0x1cd4 | `ImpactShakeCoolDown` (F-37) | — | — | — | **ABSENT** |
| 0x1cd8 | `CameraImpactEffectFactorFwd` | FloatProperty | `image+0x1023445` | `cd cc 4c 3e` | 0.2 |

The two rows above and below each found value are serialised, which is what makes the find
attributable and not a layout guess: 265 / 430 / **250** are the three consecutive box dimensions
(`BattleModeWidth` / `Length` / `Height` at 0x1994 / 0x1998 / 0x199c), and 0.01 / 2.0 / **3.0** /
**3.0** / 0.2 are five consecutive shake-and-camera factors. `0x43 7a 00 00` = 250.0 and
`0x40 40 00 00` = 3.0 are plain little-endian floats a hex editor can check.

Command (the tool is new, `Tools/scripts/chase/chase2_defaults.py`; it walks **all 2,975**
`Default__*` exports of `BmGame.upk`, not the owning class only):

```
$ python Tools/scripts/chase/chase2_defaults.py
BmGame.upk: 177031 exports, image 356,085,334 B
walked 2975 Default__ objects, 2975 with a tag stream

-- 30 tag(s) at the card offsets
   control BattleModeLength ... Default__RVehicleBatmobileBase @0x1994 FloatProperty = 265.0 [OWNING CLASS]
   control ... @0x1998 FloatProperty = 430.0 [OWNING CLASS]
   F-33 BattleModeHeight      Default__RVehicleBatmobileBase @0x199c FloatProperty = 250.0 [OWNING CLASS]
   control ImpactShakeVehicleFactor ... @0x1cc8 FloatProperty = 2.0 [OWNING CLASS]
   F-35 ImpactShakeAbandonedVehicleFactor @0x1ccc FloatProperty = 3.0 [OWNING CLASS]
   F-36 ImpactShakeDestructiblesFactor    @0x1cd0 FloatProperty = 3.0 [OWNING CLASS]
   ... (24 more, all "other class": layout coincidences, listed in the JSON)

-- per row
   0x1994 control           hits  1  on RVehicleBatmobileBase 1  [('Default__RVehicleBatmobileBase', 265.0)]
   0x1998 control           hits  1  on RVehicleBatmobileBase 1  [('Default__RVehicleBatmobileBase', 430.0)]
   0x199c F-33              hits  1  on RVehicleBatmobileBase 1  [('Default__RVehicleBatmobileBase', 250.0)]
   0x1ccc F-35              hits  1  on RVehicleBatmobileBase 1  [('Default__RVehicleBatmobileBase', 3.0)]
   0x1cd0 F-36              hits  1  on RVehicleBatmobileBase 1  [('Default__RVehicleBatmobileBase', 3.0)]
   0x1cd4 F-37              hits  1  on RVehicleBatmobileBase 0  ABSENT   (the hit is Default__RVehicleNPC, other class)
```

(The script's descriptive labels for 0x1994/0x1998 say "control"; the BMSDK check below fixes them
to `BattleModeWidth` 0x1994 and `BattleModeLength` 0x1998 — **`chase-05.md`'s table puts the two
controls at 0x1990/0x1994, four bytes low**; 0x1990 is `PreventModeSwitchDuration`.)

```
$ python - (BMSDK_OFFSETS.json, classes.RVehicleBatmobileBase.properties, by offset)
   0x1990 PreventModeSwitchDuration(float)   0x1994 BattleModeWidth(float)
   0x1998 BattleModeLength(float)            0x199c BattleModeHeight(float)
   0x1cc4 ImpactShakeForceFactor(float)      0x1cc8 ImpactShakeVehicleFactor(float)
   0x1ccc ImpactShakeAbandonedVehicleFactor(float)
   0x1cd0 ImpactShakeDestructiblesFactor(float)  0x1cd4 ImpactShakeCoolDown(float)
   0x1cd8 CameraImpactEffectFactorFwd(float)     0x1cdc CameraImpactEffectFactorSide(float)
   0x1ce0 VehicleImpactEffectFactorFwd(float)    0x1eb4 BattleModeSpeedDelta(float)
```

**No archetype overrides them.** Re-measured by offset (the test that works for floats) across the
20,128 exports of `Research/BatmobileGrab/objects.jsonl`: **0 tags** at 0x199c, 0x1ccc, 0x1cd0 —
and also 0 at the two controls 0x1994/0x1998, whose values are equally CDO-only. So the four shipped
`Playable_Batmobile*` archetypes inherit these class defaults; the values above are what the game
runs.

## F-33 · `BattleModeHeight` — FOUND

**STATUS: FOUND. 250.0 cm = 2.50 m.**
Evidence: `BmGame.upk` export 10923 `Default__RVehicleBatmobileBase`, FloatProperty at class offset
0x199c, payload at `image+0x10230c7`, bytes `00 00 7a 43`. BMSDK offset 0x199c = `BattleModeHeight`.
Unit cm from the row's own unit column and the two serialised neighbours (265 cm width, 430 cm
length) — a 2.65 × 4.30 × 2.50 m battle-mode box. Provenance class: `decoded`.
Routes tried this pass: (a) **class default object tag stream — found**; (a) ini — 0 hits for
`BattleModeHeight` in every ini incl. DLC; (a) archetypes by offset — 0 tags; (b)/(c)/(d) not needed,
a file value wins (R4).
Consistency note (`derived`, not claimed as evidence): 2.50 m is taller than the 2.271 m body
(`DIM-1`), which is what raising the turret in battle mode would do.

## F-35 · `ImpactShakeAbandonedVehicleFactor` — FOUND

**STATUS: FOUND. 3.0** (factor, the row's unit column).
Evidence: same object, FloatProperty at 0x1ccc, `image+0x1023435`, bytes `00 00 40 40`. BMSDK 0x1ccc.
Neighbours serialised at 0x1cc4 = 0.01 and 0x1cc8 = 2.0, so the tag stream is not shifted.
Provenance class: `decoded`.
Routes tried this pass: (a) CDO tag stream — **found**; (a) 2,975-default sweep — this is the only
carrier; (a) archetypes by offset — 0; (a) ini — 0; (b) native — see below, no attributable site.
Note vs `chase-05.md`: it described this as the first of "three rows the class skips between 0.01333
and 1.5". The *archetypes* skip all three; the **CDO does not** — it carries 0x1ccc and 0x1cd0 and
skips only 0x1cd4.

## F-36 · `ImpactShakeDestructiblesFactor` — FOUND

**STATUS: FOUND. 3.0** (factor).
Evidence: same object, FloatProperty at 0x1cd0, `image+0x102343d`, bytes `00 00 40 40`. BMSDK 0x1cd0.
Provenance class: `decoded`. Routes tried: as F-35.

## F-34 · `JumpRampUpwardForce` — STILL UNKNOWN

**STATUS: STILL UNKNOWN.** No tag at 0x1a60 in `Default__RVehicleBatmobileBase` (the CDO is a
partial list, so this is "not written", not "zero"), 0 tags at that offset in the 20,128 archetype
exports, 0 hits in every ini.
Routes tried this pass, both new:

* **(b) every load/store site**, not only immediate stores — 10 instructions in `.text` reference
  displacement 0x1a60 and none is this class's field: `movups xmm0, [rdi+0x1a60]` at RVA 0x5b0c9
  (a 16-byte vector read, so not a float member), `lea rcx,[rbx+0x1a60]` at RVA 0x247f48 (a
  destructor call chain on unrelated offsets 0x1a2c/0x1a1c/0x1a14), `lea rcx,[rbp+0x1a60]` at
  0x48839b and a stack-frame `sub dword [rsp+0x1a60]` at 0xa78fbc. The only RIP-relative constants
  in the windows read as subnormals (`1.11e-39`, `3.27e-37`) — name strings, not forces.
* **(a) 2,975-default sweep** — two other-class hits (`RPawnVillainGunPredBase` IntProperty −1,
  `RPlayerController` ArrayProperty), neither on this class.
The behaviour is real and already measured (ramp jumps: 1.212 s mean air time, FOOTAGE §3), but an
engine force has no documented bridge to an air time, so no number is claimed.

## F-37 · `ImpactShakeCoolDown` — STILL UNKNOWN

**STATUS: STILL UNKNOWN.** No tag at 0x1cd4 in the Batmobile CDO; the stream goes 0x1cd0 → 0x1cd8.
Routes tried this pass:

* **(a) 2,975-default sweep** — the only hit at 0x1cd4 is `Default__RVehicleNPC` = 20.0, a
  **different class** with its own layout (RVehicleNPC is absent from BMSDK, so the offset cannot be
  mapped to a member name there). Not evidence for this row, and not used.
* **(b) load/store sites** — 8 instructions reference 0x1cd4; the only one with a nearby
  RIP-relative constant is `mov qword ptr [rbx+0x1cd4], r9` at RVA 0x3efccf, whose window reads
  150.0 — a 64-bit pointer store, not a float cooldown of this class.
* (c) footage: a shake re-trigger interval would need repeated impacts in one clip; none of the
  captures holds them (the first pass measured this too).

## F-38 · `BattleModeSpeedDelta` — STILL UNKNOWN

**STATUS: STILL UNKNOWN.** No tag at 0x1eb4 in the CDO; 0 tags at that offset in the archetypes;
0 ini hits.
Routes tried this pass: (a) 2,975-default sweep — the only hit is `Default__RVehicleTank`
IntProperty −1 (other class); (b) 8 load/store sites, the closest a `comiss xmm0,[rbx+0x1eb4]` at
RVA 0x56a4d comparing against a 0.2 constant — a float compare in unrelated code, not an
initialiser; (c) still no capture with a controlled normal-vs-battle speed pair.

## F-39 · `TurnOnSpotSteeringSpeedCurve` — STILL UNKNOWN

**STATUS: STILL UNKNOWN** (and it is not a scalar). No tag at 0x0268 in
`Default__RVehicleSimBatmobile` (58 tags, none at that offset), 0 in the archetypes, 0 in the inis.
Routes tried this pass: (a) 2,975-default sweep — 11 hits at 0x0268, every one a different class
(`RBMBehaviour_Combat` 800.0, `RBmPawnSpawner` IntProperty 200, `RNavigationHandle` −1.0,
`RVehicleBehaviour_*` …), i.e. the low-offset collision `MODES.md` warns about; (b) 523 instructions
reference 0x0268 and none can be bound to the sim class — a curve is a heap `TArray` + interp mode,
so it cannot appear as a stored constant. The CDO writing no tag means either an empty curve or one
built at runtime; the two are not distinguishable from the file, so no points are claimed.

## F-40 · `BattleModeMoving` — STILL UNKNOWN

**STATUS: STILL UNKNOWN.** No `BoolProperty` tag at 0x0294 in `Default__RVehicleSimBatmobile` (it
has 0 bool tags at all), and the CDO is a partial list, so this is "not authored", not "false".
Routes tried this pass: (a) 2,975-default sweep — 9 hits at 0x0294, all other classes
(`RVehicleBehaviour_FollowVehicle` BoolProperty = true with bits 0x00000001,
`RVehicleBehaviour_PursuitCop` false, `RBmPawnSpawner` StrProperty 'PawnDead', …), none on
`RVehicleSimBatmobile`; (b) 278 instructions reference 0x0294, all unrelated. A runtime flag with no
authored default stays UNKNOWN.

## Routes tried this pass (summary)

| route | F-33 | F-35 | F-36 | F-34 | F-37 | F-38 | F-39 | F-40 |
|---|---|---|---|---|---|---|---|---|
| (a) CDO **tag stream** (all 2,975 defaults) | **FOUND** | **FOUND** | **FOUND** | absent | absent | absent | absent | absent |
| (a) archetypes by **offset** (`objects.jsonl`, 20,128) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| (a) every ini incl. DLC (member names) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| (a) manifest `GlobalPersistentCookerData.upk` | names only — cannot carry a float value (flaw 1) | | | | | | | |
| (b) load **and** store sites + RIP-relative constants | n/a | unbound | unbound | 10 unbound | 8 unbound | 8 unbound | 523 unbound | 278 unbound |
| (c) captures | F-33 measurable only with a calibrated stick (none in frame) | | | air time ≠ force | not visible | needs two modes in one clip | not in any capture | not visible |
| (d) published sources | not used; no URL in the repo states these | | | | | | | |

The DLC sweep from the F-8…F-16 card is relevant here too: of 879 DLC packages (6.56 GB) only the
cook manifest contains these class names, and it is a name list, so no DLC package overrides them.

## What this changes for the project

1. **F-33 `BattleModeHeight` = 250.0 cm** now exists as a file value; the battle-mode box is
   265 × 430 × 250 cm (F-31/F-32/F-33), all three from the same default object.
2. **F-35 / F-36 = 3.0** replace "must choose our own value" for those two rows. `chase-05.md`
   point 2 said a JC3 shake implementation "must choose its own values for the three that do not
   [exist]" — now only F-37 (`ImpactShakeCoolDown`) needs a design-chosen value, and it should be
   recorded as our choice, never as Arkham's. Note the archetypes do *not* ship 3.0: they ship
   `ImpactShakeForceFactor` 0.01333 and `ImpactShakeVehicleFactor` 1.5 (their own overrides of the
   CDO's 0.01 / 2.0).
3. **Do not repeat a name-based search for a float.** Any future `VALUE-NATIVE` verdict should be
   re-checked by offset against the CDO tag stream before it is believed — `chase-05.md`'s row set is
   the proof of why.
4. F-34/F-37/F-38/F-39/F-40 keep their `VALUE-NATIVE` verdicts, now with the CDO tag stream, the
   load-site scan and the constant resolution behind them rather than the name search.

## Reproduce

```
python Tools/scripts/chase/chase2_defaults.py --json E:/Modding/ArkhamKnight/_grab/chase/chase2_defaults.json
python Tools/scripts/chase/chase2_native2.py --disp \
  "F-34=0x1a60" "F-37=0x1cd4" "F-38=0x1eb4" "F-39=0x268" "F-40=0x294" \
  --json E:/Modding/ArkhamKnight/_grab/chase/chase2_native2_05.json
grep -rn -i -E "BattleModeHeight|JumpRampUpwardForce|ImpactShake|BattleModeSpeedDelta|TurnOnSpot|BattleModeMoving" \
  --include="*.ini" "E:/Games/Batman - Arkham Knight"
```

Evidence files: `E:/Modding/ArkhamKnight/_grab/chase/chase2_defaults.json` (every card-offset tag in all 2,975
default objects), `chase2_native2_05.json` (per-offset sites with disassembly context).

`FOOTAGE.md`, `chase-05.md`, `GRAB_BACKLOG.md` and every other existing document were **not edited**
(card rule). Nothing was launched, patched, committed, or written under `D:/Games` or `E:/Games`; the
game package was opened read-only. No secret is in this file.
