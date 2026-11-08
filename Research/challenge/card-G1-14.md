# Assumption challenge — G1-14 · Damage rules, health, armour, regeneration

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or the game install
was written; no game launched, no file in `D:\Games` touched, nothing installed, nothing
committed. This report is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-14 card (line 470) and its §12 row (line
1282), `MODLOG.md` §"G1-14 · Damage rules — done" (line 8246) and
§"G1-14 rework — done" (line 15612), `Research/BatmobileGrab/DAMAGE_RULES.md` (all 678 lines),
`DAMAGE_RULES.json`, `Tools/scripts/bmak_damage.py`, `Tools/scripts/upk_read.py`,
`Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs`, `Working/vendor/BmSDK/Pawn.g.cs`, and the
game packages `BmGame.upk`, `Startup.upk`, `Core.upk`, the four `Playable_Batmobile*_SF.upk`,
plus `Binaries/Win64/BatmanAK.exe`.

## VERDICT

**The method is sound and reproduces; two of its three headline numbers are wrong, because the
note looked for values in the archetype tag streams and never opened the class default object —
which ships.** 17 assumptions tested: **5 HOLD, 5 WEAK, 7 BROKEN.**

What holds: every reader count I re-derived independently — `HealthRecoverRate` 1
(`ExperienceAwarded`), `ArmourModeDamageReduction` 1 (`TakeDamage`), `LowHealthWarningLevel` 1
(`TakeDamage`), `WeaponGeneratorPower` 25 — by searching the 29,620 `Function` bodies for the
5-byte token `01 <export-index>` instead of the note's own walk; the 5 native verdicts (4 of the
5 bodies are nothing but `0x29 <own-parameter>` descriptors); `TakesDamageFromRam`'s 7-byte body;
`TakeRadiusDamageFromWeapon` carries no token for the script `TakeDamage` (the rework's
correction); the missile numbers 250 / 60 / Joker 250; `MyDamageType` on 14 of 26 projectile
archetypes; the `exec<>` counts (3/1/1/3/2/1/0/0 reproduce byte-for-byte); the `*Regen*`
negation — and stronger than the note tested it: exactly **one** object in the whole of
`BmGame.upk` has `/Regen/` in its own name (`RCrowdSpawnPointMaster.bRegenerateChildren`).

What breaks:

1. **"The value does not ship" is false.** `BmGame.upk` export **10923** is
   `Default__RVehicleBatmobileBase` (class `RVehicleBatmobileBase`, 3,186 B) and its tag stream
   carries `HealthRecoverRate` = **`[8.0, 4.0, 2.0]`** at the class offset **8220** the note itself
   quotes. The same CDO also ships `Health` = 1000, `ArmourModeDamageReduction` = **20** and
   `ArmourLevels` = `[0, 300, 600, 900, 1200]`. The "unshipped `BmScript` CDO" is on disk.
2. **The fleet is four cars, not three.** `Playable_BatmobileJoker_SF.upk` holds a fourth
   `RVehicleBatmobile` archetype, `Vehicle.JokersBatmobile`, and it overrides **neither** `Health`
   nor `ArmourModeDamageReduction`. It therefore inherits the CDO's **1000 / 20**, not the
   1200 / 0 the note generalises from the three it listed. The card's "1200 on all 3" and
   "reduces incoming damage by nothing as shipped" are both true of 3 of 4 shipped cars.
3. **Nothing that no archetype overrides has a value row.** The 251-row inventory is built from
   archetype tags, so `HealthRecoverRate` (the field §5 is about), `ArmourLevels`,
   `CurrentArmourLevel`, `HealthMax`, `bWeaponGeneratorShielding`, `WeaponGeneratorShielding`,
   `VulnerableToEMP` and `EMPRepairable` have **no row at all** — the card's Done clause "every
   damage-related field listed with value and source" is not met.
4. **The card's third `Do` item was never written.** There is no damage type → multiplier → mode
   table; §7 says the per-`DamageType` multipliers are engine-side and were not opened, and
   `MyDamageType` appears in the record only as a raw import index (-104/-105/-115/-121/-122).
5. **17 of the record's 17 virtual calls are named wrong**, because `EX_VirtualFunction` (0x1B)
   carries an *FName* index and the walk resolves it as an object index: the call to
   `HealthUpdated` at `TakeDamage`+1430 is recorded as `NotifyFinished.FinishedAction`, the call
   to `InGodMode` as `GridSample.Weight`, `SetBatmobileOnFire` as `ExitMove.I`. The note's
   promise that "each name it uses is also present in the record with its offset so a reader can
   re-check it" fails for every one of them.
6. §3.1's ordering — "`InCinematicMode` … cinematic mode returns early" — is contradicted by the
   body it is drawn from: `RPlayerControllerBase.InCinematicMode` is the reference at
   `TakeDamage`+377, *after* `ArmouredMode` (+112) and `ArmourModeDamageReduction` (+133).

---

## A1 · "The shipped number is whatever the native CDO in `BmScript` (not shipped) holds"

**BROKEN.**

The claim (note §5, MODLOG done entry, §12 row: "value UNKNOWN") rests on three steps: no
archetype tag carries the array → the field has no value in the files → the number lives in an
unshipped class default object.

Test 1 — is `Default__RVehicleBatmobileBase` on disk?

```
python - <<'PY'
import sys; sys.path.insert(0,'Tools/scripts'); import upk_read as U
pkg=U.Package(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk")
print(pkg.object_path(10923), pkg.object_class(10923), len(pkg.data(10923)))
PY
```
```
Default__RVehicleBatmobileBase RVehicleBatmobileBase 3186
```

It is export 10923 of the same `BmGame.upk` the note reads. A CDO is a normal cooked export: its
data is the tagged default-property stream, and the repo's own reader walks it.

Test 2 — the tag, at the offset the note quotes from the SDK (+8220):

```
python - <<'PY'
import sys,struct; sys.path.insert(0,'Tools/scripts'); import upk_read as U
pkg=U.Package(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk")
d=pkg.data(10923)
print("header :",d[2752:2772].hex(" "))
t,off=struct.unpack_from("<hH",d,2752); ni,nn,size,arr=struct.unpack_from("<iiii",d,2756)
print("type=%d prop_offset=%d name=%s size=%d count=%d"%(t,off,pkg.names[ni],size,arr))
print("payload:",d[2772:2772+16].hex(" "))
print("floats :",struct.unpack_from("<3f",d,2772))
PY
```
```
header : 09 00 1c 20 b4 a4 00 00 00 00 00 00 10 00 00 00 00 00 00 00
type=9 prop_offset=8220 name=HealthRecoverRate size=16 array_index=0
payload: 03 00 00 00 00 00 00 41 00 00 80 40 00 00 00 40
floats : (8.0, 4.0, 2.0)
```

`0x1c20` = 8220 is the offset `RVehicleBatmobileBase.g.cs:8874` declares (`Ptr + 8220`), so the
tag is the property it claims to be, from a second source. `9` is `ArrayProperty`, count 3,
stride 4, three floats: **8, 4, 2**.

Test 3 — the same walk over the whole CDO gives the neighbours the note lists as "not shipped"
values:

```
CDO Default__RVehicleBatmobileBase  {'ArmourModeDamageReduction': 20, 'ArmourLevels': None,
                                     'HealthRecoverRate': [8.0, 4.0, 2.0], 'Health': 1000}
```
(`ArmourLevels` decoded separately at offset 8108: `[0, 300, 600, 900, 1200]`.)

What is left of the claim: the **subclass** CDO `Default__RVehicleBatmobile` is genuinely not on
disk — it is not an export of `BmGame.upk` or `Startup.upk`, and `Core.upk`, the package the
archetypes import the class from (`class_index -137 → Core.RVehicleBatmobile`), is a 34,817-byte
stub whose 1,708 exports contain no such object. So a subclass override cannot be excluded. But
"the value does not ship" is still wrong: the base default ships, is readable, and is what a car
that overrides nothing gets (A3). The word "native" is also wrong — a CDO is a script object.

## A2 · "No archetype overrides it — it is absent from `CHAIN.json` (0 mentions) and from the 423-field `OFFSETS.json` (0 rows), so the tags carry no value"

**WEAK.** The premise reproduces; the inference does not.

```
grep -c HealthRecoverRate Research/BatmobileGrab/CHAIN.json Research/BatmobileGrab/OFFSETS.json
→ CHAIN.json:0   OFFSETS.json:0
```

and the four real archetypes carry no tag at property offset 8220 (`probe` in the appendix prints
`not overridden: … HealthRecoverRate` for all four). But "no override" is the *expected* state of
a field at its default: UE serialises a tag only when the value differs from the class default.
Absence is evidence that the class default applies, not evidence that no value exists. Every
field in the 251-row inventory is there because it happened to be overridden; the class defaults
of the whole class are outside the inventory's reach (A6).

## A3 · "`Pawn.Health` = 1200 on all **3** Batmobile archetypes (`BatmobileFunhouse`, `Batmobile_MK2`, `Batmobile`)"

**BROKEN** — a fleet-wide claim tested on 3 of the 4 shipped cars, and the missing one differs.

```
Playable_BatmobileFunhouse_SF.upk archetypes(RVehicleBatmobile)= 1   Vehicle.BatmobileFunhouse
Playable_BatmobileJoker_SF.upk   archetypes(RVehicleBatmobile)= 1   Vehicle.JokersBatmobile
Playable_BatmobileMK2_SF.upk     archetypes(RVehicleBatmobile)= 1   Vehicle.Batmobile_MK2
Playable_Batmobile_SF.upk        archetypes(RVehicleBatmobile)= 1   Vehicle.Batmobile
```

Tag at `Pawn.Health` (+1144, `IntProperty`) in each:

```
CDO Default__RVehicleBatmobileBase             {'ArmourModeDamageReduction': 20, 'Health': 1000, 'HealthRecoverRate': [8.0, 4.0, 2.0]}
Vehicle.BatmobileFunhouse                      {'ArmourModeDamageReduction': 0, 'Health': 1200}
Vehicle.JokersBatmobile                        {}
Vehicle.Batmobile_MK2                          {'ArmourModeDamageReduction': 0, 'Health': 1200}
Vehicle.Batmobile                              {'ArmourModeDamageReduction': 0, 'Health': 1200}
```

`Vehicle.JokersBatmobile`'s tag stream is empty for all five probed offsets, so it inherits the
CDO: **Health 1000**, not 1200. Note §4 says "on all **3** Batmobile archetypes"; the card's `In:`
list ("`RVehicleBatmobile`") does not exempt the Joker car, and the note's own records do not
either — `Batmobile_JokerMissile_Projectile` is a row in `damage_values`. Residual uncertainty:
the subclass CDO (A1) could set something else; nothing on disk says 1200 for this car.

## A4 · "`ArmourModeDamageReduction` ships **0**, so armoured/battle mode reduces incoming damage by nothing as shipped"

**BROKEN for the fourth car**, HOLDS for the three named ones, and the unit is unestablished.

The three rows in the record are right:
```
ArmourModeDamageReduction [('…BatmobileFunhouse', 0), ('…Batmobile_MK2', 0), ('…Batmobile', 0)]
```
and the tag stream agrees, so "that is the value the archetype authors set" (note §6.3) is
verified for them. But the CDO sets **20**, and `Vehicle.JokersBatmobile` overrides nothing, so
one shipped car runs with 20. `TakeDamage` is the field's only reader (A7), and nothing in the
note establishes whether the integer is a percentage, a flat subtraction or a bitmask — at 0 the
question does not arise; at 20 it does.

## A5 · "`Pawn.Health` = 1200 is the car's health" (R5: a member read by its name)

**WEAK.** The class does not use `Health` as its ceiling; `GetMaxHealth` does, and it is
computed from the armour ladder.

`RVehicleBatmobileBase.GetMaxHealth` (export 10597, 42-byte script):
```
04 92 19 2e aa 2a 00 00 01 65 f5 ff ff 09 00 c2 f5 ff ff 00 01 c2 f5 ff ff 10 01 6b 25 00 00 01 6a 25 00 00 16 04 3a 64 29 00
```
`0x2aaa` = 10922 (`RVehicleBatmobileBase` class, the `EX_DynamicCast`), `0x256b` = **9579**
`CurrentArmourLevel`, `0x256a` = **9578** `ArmourLevels`. Independent reader test over all
29,620 bodies:
```
RVehicleBatmobileBase.ArmourLevels       readers=1  [('…GetMaxHealth','0x1',1)]
RVehicleBatmobileBase.CurrentArmourLevel readers=2  [('…CanPlayerPurchaseBatmobileArmourUpgrade','0x1',4), ('…GetMaxHealth','0x1',1)]
```
and `GiveMaxHealth` (20-byte script `0f 01 c2f5ffff 1b 97980000 16 1b bca40000 4a 16 04`) assigns
`Core.Health = GetMaxHealth()` then calls `HealthUpdated`.

So the shipped maximum is armour-level-driven out of `ArmourLevels = [0, 300, 600, 900, 1200]`,
i.e. 300 per upgrade tier up to 1200, and 1200 is the archetypes' serialised `Health`, which the
class can rewrite. Whether 1200 survives into play (it is also what `LoadHealth`/DDA restore) is
NOT established — the note's flat "1,200" hides that chain, and `CurrentArmourLevel` is itself
untagged everywhere, so its default is not on disk.

## A6 · "Every damage-related field listed with value and source" (card `Done`)

**BROKEN.** The inventory is 251 rows over 45 archetypes, and its membership rule is "an
archetype tag exists", not "the field is damage-related":

```
bWeaponGeneratorShielding      ABSENT
WeaponGeneratorShielding       ABSENT
VulnerableToEMP                ABSENT
bAttackBlocked                 ABSENT
BlockedHitLocation             ABSENT
HealthRecoverRate              ABSENT
ArmourLevels                   ABSENT
CurrentArmourLevel             ABSENT
EMPRepairable                  ABSENT
HealthMax                      ABSENT
ArmourModeDamageReduction      ['…ArmourModeDamageReduction', ×3]
Health                         ['Pawn.Health', ×3]
```

`bWeaponGeneratorShielding` and `WeaponGeneratorShielding` are the ones that matter most: the
note's own §4 says "the weapon generator is the shield" and names `bWeaponGeneratorShielding` as
the flag `DrainWeaponGeneratorForDamage` reads, yet neither field has a value row, because
neither is overridden by an archetype. The DAMAGE_FIELD regex also cannot reach
`VulnerableToEMP` / `EMPRepairable` (it has `invuln`, not `vulnerab`/`repair`), so even a
tag-driven field of that name would have been dropped. A field inventory that only holds
overrides is a list of *deltas*, not of fields.

## A7 · "Exactly 1 script function reads it" / the reader counts

**HOLDS.** Re-derived without the note's walk, using the 5-byte instance-variable token
`01 <export index>` over all 29,620 `Function` bodies:

```
RVehicleBatmobileBase.ArmourModeDamageReduction readers=1 [('RVehicleBatmobileBase.TakeDamage','0x1',1)]
RVehicleBatmobileBase.HealthRecoverRate         readers=1 [('RVehicleBatmobileBase.ExperienceAwarded','0x1',1)]
RVehicleBatmobileBase.LowHealthWarningLevel     readers=1 [('RVehicleBatmobileBase.TakeDamage','0x1',2)]
RVehicleBatmobileBase.WeaponGeneratorPower      readers=25
```
25 matches the note's "read by 25 script functions in total", including the states
(`DrivingMode.PreRender`, `Firing.BeginState`, `Primed.ReadyToFire`). One correction to the prose:
`QuarterHealth` is **not** a class field — `TakeDamage.QuarterHealth` (10422) and
`TakeDamage.OldHealth`, `DamageAmount` are `EX_LocalVariable` slots of the function itself, so
"thresholds: `QuarterHealth`, `LowHealthWarningLevel`" mixes a local with a field.

## A8 · "Recovery is awarded per experience event, indexed by difficulty" and the meaning of 8/4/2

**WEAK.** The two ingredients are present and ordered as the sentence needs; the subscript and
the arithmetic are not decoded, so the unit of 8/4/2 is open.

`ExperienceAwarded` refs at the note's own offsets:
```
{'at': 65, 'token': 'EX_FinalFunction',   'ref': 'RGameInfo.GetDifficulty'}
{'at': 71, 'token': 'EX_InstanceVariable','ref': 'RVehicleBatmobileBase.HealthRecoverRate'}
{'at': 137,'kind': 'float', 'value': 2.0}
```
plus locals `HealthRecovery` (Float), `HealthToRecover` (Int), `XpAwarded`, `TeethXpAwarded`, and
`Core.Health` written twice. So: `GetDifficulty` is called, the array is read three tokens later,
and the result reaches the **int** `Core.Health` through two locals. What is *not* shown: that the
array is indexed by the difficulty value (the walk resolves no expression tree — the note says so
itself), that 3 entries = 3 difficulties, and what 8 / 4 / 2 are (HP per award? a fraction of max
health? a multiplier on the XP?). "Not a passive timer" is also an argument from absence on the
script side only; a native tick would not appear in these bodies.

## A9 · "0 `*Regen*` members of 25 on the 70 `RVehicle*`/`Pawn`/`AkVehicle` classes"

**HOLDS**, and the test can be made exhaustive on the artifact instead of prefix-filtered:

```
objects whose own name matches /Regen/ in BmGame.upk: 1
    ('RCrowdSpawnPointMaster.bRegenerateChildren', 'BoolProperty')
```
```
grep -c "/// .*Property: " Working/vendor/BmSDK/*.g.cs      (3,849 property rows in the dump)
grep -rn "Property: [A-Za-z_]*Regen[A-Za-z_]*" ...           → 0
```
`Startup.upk`'s only `/Regen/` hit is an asset name, `Jokerfied.CITY_Statues_Generic_Regent_full_Joker_R`.
Caveat: this covers `BmGame.upk` plus the dumped SDK only; a `Regen` member declared in a package
that is neither would be invisible, and `RCrowdSpawnPointMaster` is not in the dumped SDK at all,
so the SDK half of the negation is weaker than the export half.

## A10 · "Each name it uses is also present in the record with its offset so a reader can re-check it"

**BROKEN.** `EX_VirtualFunction` (0x1B) is in the walk's `REF_TOKENS` and resolved with
`pkg.object_path(index)`, but its operand is an **FName table index**, not an object reference.
All 17 virtual calls in the 14 traced bodies are therefore recorded under an unrelated object:

```
TakeDamage at 1407  idx 69773  recorded=ExitMove.I                        name-table=SetBatmobileOnFire
TakeDamage at 1430  idx 42172  recorded=NotifyFinished.FinishedAction      name-table=HealthUpdated
TakeDamage at 217   idx 43926  recorded=GridSample.Weight                 name-table=InGodMode
TakeDamage at 432   idx 54204  recorded=RHelicopterBase.bIsAggro           name-table=NotifyTakeDamageWhileInCinematicMode
TakeDamage at 691   idx 54203  recorded=RHelicopterBase.new_lineofsight     name-table=NotifyTakeDamage
ExperienceAwarded at 165 idx 39063 recorded=IsAlreadyDoingJob.ReturnValue  name-table=GetMaxHealth
LoadHealth at 199   idx 39063  recorded=IsAlreadyDoingJob.ReturnValue      name-table=GetMaxHealth
… 17 of 17
```
The prose survives this (its names — `RVehicle.UnStickTyres`, `RPlayerController.NumBatmobileMissileHits`,
`RPersistentData.AutoActivateTutorial`, `RVehicleCombatManager.PlayCommanderBark` — come from
imports and instance variables, which are resolved correctly), but the record cannot be audited
at those offsets, and "who notifies the health change" (`HealthUpdated`, TakeDamage+1430) is lost
from the trace. The same mis-resolution makes the `walk.unaligned_sample` rows meaningless names.

## A11 · "`InCinematicMode` and `SelfDriveMode` gate the hit (cinematic mode returns early)"

**BROKEN as stated.** Byte order says the opposite of "early":

```
RVehicle.SelfDriveMode                          at 57
RVehicleBatmobileBase.ArmouredMode              at 112
RVehicleBatmobileBase.ArmourModeDamageReduction at 133
InCinematicMode.ReturnValue                     at 371   (record's `at`; 372 in a raw operand scan)
RPlayerControllerBase.InCinematicMode           at 377   (EX_FinalFunction 97237; 378 raw)
```
The cinematic check sits ~250 bytes *after* the armour scaling it is said to precede. I tried to
settle it with jump targets (`0x07 0x16 0x00` at offset 2 → 33; etc.) and this is where the note's
own caveat bites: a naive `off+3+delta` walk gives 15 targets "past end" and lands on
`EX_EndParmValue` bytes, i.e. the jump offsets cannot be trusted without a real decoder. So
neither "early" nor "gate" is decoded; the reference order is the only fact, and it does not
support the sentence.

## A12 · The `exec<>` counts are registrations of the traced functions

**WEAK.** The counts reproduce exactly — but they are substring counts, and one in each of two
rows belongs to a different function:

```
TakeDamage            exec-prefixed occurrences=3
   @31448519  b'execTakeDamageFromChainGun'      ← different function
   @38072304  b'execTakeDamage'
   @38075592  b'execTakeDamage'
SetDamageLevel        exec-prefixed occurrences=3
   @31414236  b'execSetDamageLevel'
   @31414268  b'execSetDamageLevelFlags'         ← different function
   @31534086  b'execSetDamageLevel'
```
```
record: TakeDamage 3, SetDamageLevel 3, SetArmouredMode 2, ShouldRadialDamageHit 1,
        CanBatmobileDoImpactDamage 1, GetDamageMod 1, the rest 0
```
"Those strings belong to parent registrations" is therefore only partly supported: at most 2 of
`TakeDamage`'s 3 are `execTakeDamage`. None of the 5 verdicts changes (the body decides, A17).

## A13 · The card's third `Do` item — "the rule as a table: damage type → multiplier → which mode"

**BROKEN (not delivered).** `DAMAGE_RULES.md` has no damage-type table. §3 is
"damage type → entry → what scales it → mode" and gives entry points, fields and mode gates; §7
states "The per-`DamageType` multipliers live in the damage classes (each projectile's
`MyDamageType` import); those classes are engine-side and were not opened here." In
`damage_values`, `MyDamageType` appears only as a raw import index (`-104`, `-105`, `-115`,
`-121`, `-122`), with no multiplier, no class and no mode attached. The §12 row says `done`
without that qualification, so any later card that reads "damage rules (G1-14)" for a
type→multiplier map is reading a table that does not exist.

## A14 · "`MyDamageType` present on 14 of 26 projectile archetypes" (rework issue 2)

**HOLDS.** From the record: 26 distinct archetypes with `Projectile` in the path, 14 with a
`MyDamageType` row.

## A15 · "Missile 250 vs EMP missile 60, Joker missile 250" (rework issue 1)

**HOLDS.** `Projectile.Damage`: `Batmobile_Missile_Projectile` 250.0 (Funhouse, MK2, main),
`Batmobile_EMPMissile_Projectile` 60.0, `Batmobile_JokerMissile_Projectile` 250.0 (with
`DamageRadius` 300.0, unlike the others' 0.0 — a difference the 60/250 wording hides).

## A16 · "No token in this body references the script `TakeDamage`" (the radial hand-off is UNKNOWN)

**HOLDS.** In `TakeRadiusDamageFromWeapon`'s 288-byte script there is no `0x1b`/`0x1c` with
export 10436 (`RVehicleBatmobileBase.TakeDamage`) and none with the name index `TakeDamage`:
```
TakeRadiusDamageFromWeapon refs TakeDamage? False False False
```
Its call target is the imported `Core.TakeRadiusDamageFromWeapon` (`1c` + `-1635`), as the rework
says. How the engine gets from there to the override is still UNKNOWN.

## A17 · "A cooked native function keeps its parameter list as `0x29 <own-property>` descriptors in place of bytecode"

**WEAK (4 of 5 exact).**

```
ShouldRadialDamageHit       body=10 bytes  all-0x29-descriptors=True  [DamageLocation, DamageRadius]
CanBatmobileDoImpactDamage  body= 5 bytes  all-0x29-descriptors=True  [OtherVehicle]
SetDamageLevel              body=10 bytes  all-0x29-descriptors=True  [PlayerBatmobileName, NewDamageLevel]
SetArmouredMode             body= 5 bytes  all-0x29-descriptors=True  [OnOrOff]
GetDamageMod                body=20 bytes  all-0x29-descriptors=False
   49 02 00 28 15 | 29 d9 31 00 00 | 29 d8 31 00 00 | 29 d7 31 00 00
```
`GetDamageMod` opens with 5 bytes that are not a descriptor (`49 02 00 28 15`) before its three
descriptors; `TakesDamageFromRam`'s 7 bytes (`04 00 00 00 00 00 00`) are the analogous residue
the note already marks UNKNOWN. The rule as written ("keeps its parameter list in place of
bytecode") is slightly stronger than the data: the safe statement is "no statement bytecode, and
descriptors for its own parameters, possibly behind a short unrecognised header". The verdicts
themselves hold — none of the five has a body that could be script.

---

## Tests that failed, and why (so nobody repeats them)

- **Raw byte scanning for a value override is invalid on these packages.** I scanned all 3,266
  `.upk` for the tag bytes `09 00 1c 20` and for the strings `Default__RVehicleBatmobile…` to
  test "no carrier exists". `BmGame.upk` — which demonstrably contains the tag — reported *no*
  match, because export data is chunk-compressed on disk and only the decompressed stream has the
  tag. Any "no other package carries it" claim must be made from `pkg.data()`, not from file
  bytes. The `GlobalPersistentCookerData.upk` hits for `Default__RVehicleBatmobile` are name-table
  entries only (every class's CDO is name-registered game-wide); they prove nothing about values.
- **A jump-target decode of `TakeDamage` is not possible with the sizes available.** 15 computed
  targets fall past the end of the 2,028-byte body and the ones that land do so on operand bytes.
  That is the honest limit behind A11, not an argument for either reading.
- `pkg.find("TakeDamage")` returns `RVehicle.TakeDamage` (94-byte body), not the Batmobile
  override; every function used here is selected by full `object_path` for that reason.

## What later cards should quote instead

| quantity | note says | on disk |
|---|---|---|
| `HealthRecoverRate` | UNKNOWN, "does not ship" | `[8.0, 4.0, 2.0]` on `Default__RVehicleBatmobileBase` (`BmGame.upk` export 10923, tag at +8220); unit undecoded |
| `Health` | 1200, all 3 archetypes | 1200 on 3 archetypes; **1000** inherited by `Vehicle.JokersBatmobile` |
| `ArmourModeDamageReduction` | 0 as shipped | 0 on 3 archetypes; **20** on the base CDO and on `Vehicle.JokersBatmobile`; unit undecoded |
| max health | 1200 | computed: `ArmourLevels[CurrentArmourLevel]`, ladder `[0,300,600,900,1200]`, read by `GetMaxHealth` and assigned in `GiveMaxHealth` |
| damage type → multiplier | "in the engine-side damage classes" | no table in the note and none in `damage_values`; card item 3 undelivered |

R4 asks for a number only with provenance; these five are the ones a fix would have to restate
before `ARM-2`, `G2-28` or `T-14` can cite G1-14 for a ratio.

## Appendix · commands used

```bash
# CDO and its tags
python -c "import sys;sys.path.insert(0,'Tools/scripts');import upk_read as U;p=U.Package(r'E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk');print(p.object_path(10923),p.object_class(10923),len(p.data(10923)))"

# tag at +8220 -> ArrayProperty HealthRecoverRate [8,4,2]
python - <<'PY'
import sys,struct; sys.path.insert(0,'Tools/scripts'); import upk_read as U
pkg=U.Package(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk"); d=pkg.data(10923)
t,off=struct.unpack_from("<hH",d,2752); ni,nn,size,arr=struct.unpack_from("<iiii",d,2756)
print(t,off,pkg.names[ni],size,arr,struct.unpack_from("<3f",d,2772))
PY

# every archetype's override stream at the four offsets of interest
#   Health 1144 | ArmourModeDamageReduction 6424 | CurrentArmourLevel 8104
#   ArmourLevels 8108 | HealthRecoverRate 8220   (offsets from Working/vendor/BmSDK/*.g.cs)
#   4 archetypes: Playable_BatmobileFunhouse_SF, ...Joker_SF, ...MK2_SF, ..._SF

# reader counts, independent of the note's walk
#   for every Function export: script = data[22:-16]; look for 01 <export index> / 02 <export index>

# exec strings
python -c "d=open(r'E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe','rb').read();print(d.count(b'execTakeDamage'))"
```
