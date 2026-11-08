# Chase 01 — F-1 … F-8 (projectile life, Vulcan heat, radial hit, tank shells, air time, air control, battle camera)

Scope: `Research/BatmobileGrab/FOOTAGE.md` rows **F-1 … F-8** — the eight rows whose reason is
`NOT-IN-CLIP`, `NATIVE`, `VALUE-NATIVE`, `WRONG-SCOPE` or `FILE-VALUE`. Read-only chase: no existing
document was edited, no game was launched, nothing was committed. The only writes are the two
scripts under `Tools/scripts/chase/` (`ch1_probe.py`, `ch1_dlo.py`) and this file. Game packages were
opened read-only from `E:\Games\Batman - Arkham Knight\`; nothing was copied out of the game tree and
nothing was written outside the repo.

**Result: 6 of 8 FOUND, 2 STILL UNKNOWN — and five of the six come from one place G1 never opened: the
class *default object*.**

| row | fact | value | status | provenance |
|---|---|---|---|---|
| F-1 | projectile lifetime | **14.0 s** (`Actor.LifeSpan`) | FOUND | decoded |
| F-2 | inaccuracy-vs-heat | heat term **0.0**; bloom is `InaccuracyVsTime` (0→3.0 over 2.5 s) | FOUND (closed before this chase) | decoded |
| F-3 | time-to-overheat | **never** — archetype `HeatUpPerSecond` 0.0 overrides the CDO's 0.3333 | FOUND (closed before this chase) | decoded |
| F-4 | how a radial hit is decided | the rule, not a number — native body not located | **STILL UNKNOWN** | — |
| F-5 | tank shells to destroy the Batmobile | health 1200 known; **shell damage exists in no file on this machine that the routes reached** | **STILL UNKNOWN** | — |
| F-6 | time airborne on a ramp/ledge jump | **1.212 s mean** (1.183–1.251 s, 3 jumps) | FOUND (measured before this chase) | derived (PTS measurement) |
| F-7 | `AirControl` | **0.05** (5 % air control) | FOUND | decoded |
| F-8 | `BattleModeCamConfig` | `FFreeCameraConfig`, **24 members** — table below | FOUND | decoded |

## The route that answered it

G1's readers (`batmobile_grab.py`, `grab_modes.py`) read the **15 `Playable_Batmobile*` packages** +
`BmGame`/`Startup` archetypes. `objects.jsonl` therefore contains the shipped *instances* and not the
class **default objects**. Those live in `BmGame.upk` (214 757 637 B) and `Engine.upk` (26 578 385 B)
in the same cooked folder, as exports named `Default__<Class>`, and their property tags carry **no
FName** — only the native class offset:

```
0400 c801 9a99193f 0400 cc01 000000bf ...
type=4 (Float)  offset=0x01C8  value=0.6
```

`Research/BatmobileGrab/BMSDK_OFFSETS.json` maps that offset back to a field (`Actor.LifeSpan` 348,
`Pawn.AirControl` 1096, `R3rdPersonCamera.BattleModeCamConfig` 15860, …; the file's own note: *"the
offsets are the same number space as FPropertyTagBat2.Offset"*). `Tools/scripts/chase/ch1_dlo.py`
walks the DLO's super chain so an inherited field still resolves. Every value below is printed by that
script; none is typed in by hand.

| tool | what it does |
|---|---|
| `Tools/scripts/chase/ch1_probe.py` | `names` / `census` / `defaults` / `fields` / `scanpath` / `scanfield` — FName-table and per-object property search on any cooked package |
| `Tools/scripts/chase/ch1_dlo.py` | `dlo` / `struct` / `findoff` / `chain` — class-default tags with SDK names, struct members, and the "does any class default carry this offset" test |

---

## F-1 · projectile lifetime — FOUND: 14.0 s

**Value:** `Actor.LifeSpan` = **14.0 s** for every projectile in the engine's `Projectile` class. The
Batmobile cannon's four projectile archetypes (`Batmobile_Heavy_Cannon_{Primary,HeadShot,BodyShot,
Fully_Upgraded}_Projectile`, `RBasicProjectile`) override neither it nor anything in between, so 14.0 s
is the cap that runs. It is a cap, not an observed flight: the Vulcan's impacts in the capture are
distant and no projectile is in frame, so the observed time from muzzle to impact stays unmeasured —
what the files now give is the *bound* (a shot that hits nothing is destroyed after 14 s).

**Provenance:** decoded.

**Evidence** — `Engine.upk`, `Default__Projectile`, export 30536, tag at field offset 0x015C:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo Engine.upk Default__Projectile --want LifeSpan
Default__Projectile  export[30536]  class=Projectile  size=230  chain=Projectile -> Actor -> StateObject
  Actor.LifeSpan (0x015C)                              FloatProperty                14.0
1 tag(s) shown, 1 named by the SDK table
```

No override in the chain — both subclass default objects carry **no** tag at 0x015C:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RProjectile --want LifeSpan
Default__RProjectile  export[31486]  class=RProjectile  size=94  chain=RProjectile -> Projectile
0 tag(s) shown, 0 named by the SDK table

$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RBasicProjectile --want LifeSpan
Default__RBasicProjectile  export[45069]  class=RBasicProjectile  size=122  chain=RBasicProjectile -> RProjectile -> Projectile
0 tag(s) shown, 0 named by the SDK table
```

Archetype side, already recorded: `WEAPONS.md` §4 — *"no projectile carries `LifeSpan`/`Lifetime`"*
across the 62 weapon objects (line 105); the mapping from cannon to projectile is `WEAPONS.md`
line 116 (`RBatmobileHeavyCannon.ProjectileArchetype` → `Batmobile_Heavy_Cannon_Primary_Projectile`).

**Routes tried:** (1) class defaults — answered; (2) native — not needed once (1) answered, and the
name `LifeSpan` does not occur in `BatmanAK.exe` (`b"LifeSpan\x00"` → 0 hits), so the property is not a
native-only member; (3) captures — no projectile in frame, nothing to time; (4) published sources —
not used.

## F-2 · inaccuracy-vs-heat — FOUND: no heat term; the bloom is time-based

**Value:** the shipped cannon archetypes serialise `InaccuracyAngle` **0.1** and `InaccuracyVsTime`
points **(0 s, 0.0)**, **(0.5 s, 0.0)**, **(1.5 s, 1.5)**, **(2.5 s, 3.0)**, `CIM_Linear`. Heat does not
move spread because heat never rises (F-3). The question "spread growth as the Vulcan heats" therefore
has the answer **0** — there is no heat-driven bloom — and the bloom in play is the time curve.

**Provenance:** decoded (archetype values; the class default is *different* — see the caveat below).

**Evidence** — `WEAPONS.md` lines 683–684 and 716–717 (archetypes, 4 packages, identical in every
instance: *"All 67 fields are identical in every instance (268 comparisons, 0 differences)"*):

```
| `RBatmobileCannon.HeatUpPerSecond` | 0x0A78 | FloatProperty | 0.0 |
| `InaccuracyVsTime.Points` | 0x0000 | ArrayProperty | array, 4 items: [0.0, 0.0, 0.0, 0.0, "CIM_Linear"]; [0.5, 0.0, …]; [1.5, 1.5, …]; [2.5, 3.0, …] |
```

**Caveat a build must not copy** — the *class default* object disagrees with the shipped archetypes:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RBatmobileCannon --want Inaccuracy
Default__RBatmobileCannon  export[46601]  class=RBatmobileCannon  size=1697  chain=RBatmobileCannon -> RVehicleWeapon -> RInventoryGadget -> Inventory
  RBatmobileCannon.InaccuracyAngle (0x0A70)            FloatProperty                1.5
  RBatmobileCannon.InaccuracyDropMultiplier (0x0C60)   FloatProperty                4.0
  InaccuracyVsTime (0x0C4C)                            StructProperty               InaccuracyVsTime
  InaccuracyVsTimeUpgrade (0x0C68)                     StructProperty               InaccuracyVsTimeUpgrade
```

`InaccuracyAngle` is **1.5** in the class default and **0.1** in all four archetypes. R4 (a file value
beats footage, and the spawnable instance beats the class default it inherits from) settles it: **0.1**
is the value that runs. A port that copies the class default would open the gun 15× wider.

**Routes tried:** (1) class defaults — cross-check only, and it fired the caveat above; (2) native — no
`Inaccuracy`-bearing native name needed; (3) captures — reticle bloom is visible but uncalibrated
against the curve (no pixel-to-angle reference), so no footage number is claimed (R4: file value
stands); (4) published sources — not used.

## F-3 · time-to-overheat from cold — FOUND: it never overheats

**Value:** **there is no time to overheat.** The archetype value `HeatUpPerSecond` = **0.0** means
firing adds no heat, with `OverheatOffValue` **0.25**; the bar cannot reach a stop and the gun fires
indefinitely. The class default is **0.3333 / 0.5**, i.e. the stock gun *would* heat at a third of a bar
per second; the shipped Batmobile cannon overrides it to zero. The behaviour reported in play (fires
seemingly forever) is the archetype's field, not a missing number.

**Provenance:** decoded (archetype overrides the class default).

**Evidence** — `WEAPONS.md` lines 683–684 (archetypes) and the class default:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RBatmobileCannon --want Heat
Default__RBatmobileCannon  export[46601]  class=RBatmobileCannon  size=1697  chain=RBatmobileCannon -> RVehicleWeapon -> RInventoryGadget -> Inventory
  RBatmobileCannon.HeatUpPerSecond (0x0A78)            FloatProperty                0.33329999446868896
  RBatmobileCannon.OverheatOffValue (0x0A80)           FloatProperty                0.5
  HeatBarStart (0x0A88)                                StructProperty               HeatBarStart
  HeatBarSize (0x0A90)                                 StructProperty               HeatBarSize
```

The four archetype values (0.0 / 0.25 / `HeatBarStart` `[0.79, 0.68]` / `HeatBarSize` `[0.125, 0.03]`)
are `WEAPONS.md` lines 683–684 and 686–687. No overheat duration is computed here: turning 0.3333 into
seconds would need the bar's zero point, which the record does not carry — and it is moot for the
shipped gun, whose heat term is 0.0.

**Routes tried:** (1) class defaults — cross-check, produced the 0.3333 caveat; (2) native — not needed;
(3) captures — the Vulcan capture fires for tens of seconds without an overheat stop, consistent with
0.0, but the measurement is not needed to read the field; (4) published sources — not used.

## F-4 · how a radial hit is decided (`ShouldRadialDamageHit`) — STILL UNKNOWN

**Status:** STILL UNKNOWN. The *rule* is a boolean decision inside the executable; it is not a number
and no tagged object carries it.

**What the chase established (all new):**

1. The function is declared in `BmGame.upk` as `RVehicleBatmobileBase.ShouldRadialDamageHit`,
   export **10903**, class `Function`, **size 48** — a declaration with its parameter stubs
   (`ShouldRadialDamageHit.ReturnValue` export 10900 BoolProperty,
   `… .DamageRadius` 10901 FloatProperty, `… .DamageLocation` 10902 StructProperty). No shipped object
   is an instance of the rule.
2. The **native binding name** is present exactly once in `BatmanAK.exe`:

```
$ python - <<'EOF'
d=open(r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe",'rb').read()
i=d.find(b"ShouldRadialDamageHit\x00")
print(hex(i), i)
j=d.find(b"ARVehicleBatmobileBaseexecShouldRadialDamageHit\x00")
print(hex(j), j, d[j:j+51])
print("VA", hex(0x195a000 + (j - 0x1958e00)))
EOF
0x1e11e42 31530562
0x1e11e28 31530536 b'ARVehicleBatmobileBaseexecShouldRadialDamageHit\x00ARV'
VA 0x1e13028
```

That is the UE3 native-binding string `<Class>exec<Function>`, in `.rdata` (section VA 0x195A000, raw
0x1958E00 → VA **0x1E13028**). It exists only for a function with a native implementation, which is why
the package side has a declaration and no body.
3. **No code anchor was found**: scanning the whole `.data` section (raw 0x3089000, size 0xE2E00) for a
   qword equal to that string's VA yields **0** hits, so the name does not sit in a
   `{name, function pointer}` table that can be followed to the body. There is no PDB, an IDA/Ghidra
   database does not exist in this workspace, and locating the body through the UE3 `UFunction`
   registration path would need the runtime name index — a speculative reconstruction, not evidence.

**Routes tried:** (1) class defaults / tagged objects — the function has no serialised value; (2) native
— name located (address above), body not located, no disassembly attempted without an anchor
(`capstone` 5.0.7 is available if an anchor is ever found); (3) captures — the Vulcan capture shows
outcomes, not the decision; (4) published sources — the BmSDK-AK C# bindings only re-declare the
signature, they do not carry the body.

**What would close it:** a `.pdb`/map for `BatmanAK.exe`, or an anchor into the native function table.

## F-5 · tank shells to destroy the Batmobile — STILL UNKNOWN

**Value:** **UNKNOWN.** What is known stays as stated in the row: `RVehicleBatmobile.Health` =
`[1200, 1200, 1200]` (IntProperty, 3 packages). Shells-to-kill is 1200 / (damage of one shell), and the
divisor is not in any file these routes reach.

**What the chase established:**

- The class-default route finds **no tank weapon class at all**. The `RVehicleNPCWeapon` family in
  `BmGame.upk` — 84 813 names, 177 031 exports — is:

```
$ python Tools/scripts/chase/ch1_probe.py defaults BmGame.upk -g "Default__RVehicleNPCWeapon"
export[129901] Default__RVehicleNPCWeapon            size=38
export[129977] Default__RVehicleNPCWeapon_RPG        size=50
export[129995] Default__RVehicleNPCWeapon_APCMissileLauncher size=2
export[130053] Default__RVehicleNPCWeapon_APCMissileTurret   size=42
export[130110] Default__RVehicleNPCWeapon_Gun        size=18
export[130153] Default__RVehicleNPCWeapon_ScriptedRPG size=26
```

  None of them carries a `Damage` field (`dlo … --want damage` → `0 tag(s)`), and the name table has no
  `TankCannon` / `TankShell` / `Tank*Weapon` class (a `grep` of the decoded FName table for
  `Tank[A-Za-z]*Weapon` returns nothing).
- So the shell's damage is a per-**archetype** value on an enemy projectile in a mission/showcase
  package, not a class default. The grab does not include those packages, and scanning the remaining
  ~3 270 packages (44 GB) for one archetype is out of proportion to this row; the captures contain no
  tank hit either (`NOT-IN-CLIP`, unchanged).
- The tank packages that *do* exist are art-only: `Showcase_Vehicles_LightTank.upk` (570 exports:
  33 `ParticleSpriteEmitter`, 24 `ParticleLODLevel`, … and the Batmobile shell *bones*
  `Batmobile_L_Shell_001`…), i.e. no vehicle, weapon or damage object — `census` output.

**Routes tried:** (1) class defaults in `BmGame.upk`/`Engine.upk` for every `RVehicleNPC*Weapon*` and
for `Projectile`/`RProjectile`/`RBasicProjectile` — no damage field; (2) native — the shell's damage is
data, not code, so this route does not apply; (3) captures — no tank is hit in the five clips; (4)
published sources — not used (never as a sole value).

**What would close it:** the enemy projectile archetype (a package name or object name would let the
same `ch1_dlo.py`/`grab_model.py` pair read its `Projectile.Damage` in one command), or a capture of a
tank shell actually hitting the Batmobile.

## F-6 · time airborne on a ramp/ledge jump — FOUND: 1.212 s mean

**Value:** **1.212 s mean** across three ramp jumps — **1.251 / 1.183 / 1.200 s**, 37–38 unique frames
each. Measured from presentation timestamps, not frame counts, because all five captures are
variable-frame-rate at a ~31 fps cadence. Already recorded as `MEASURED` in `FOOTAGE.md` §1 and the F-6
row; this chase re-read it and adds the decoded context below.

**Provenance:** derived (PTS measurement of `C:\Users\User\Videos\Captures`, read in place, never
copied in).

**Evidence:** `FOOTAGE.md` §1 (captures table: 189 / 202 / 267 frames, nominal 60000/1001, 60/1, 60/1;
"only 37-38 unique frames per 1.2 s") and the F-6 row itself. The observable's *file* side:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RVehicleSimBatmobile --want AirControl
  RVehicleSimBatmobile.AirControlYawTorqueFactorMax (0x04A8)   FloatProperty   5000.0
  RVehicleSimBatmobile.AirControlPitchTorqueFactorMax (0x04AC) FloatProperty   5000.0
  RVehicleSimBatmobile.AirControlYawTorqueFactorMin (0x04B0)   FloatProperty   2000.0
  RVehicleSimBatmobile.AirControlPitchTorqueFactorMin (0x04B4) FloatProperty  3000.0
  RVehicleSimBatmobile.AirControlInterpTime (0x04B8)           FloatProperty   1.5
```

i.e. the transfer into air control takes **1.5 s** — longer than the 1.212 s mean air time, so a jump
never completes the blend before landing. `AirControlTimeInAir` (0x04BC) has **no** tag here, and
`Default__RVehicleSimCar` (export 129609) carries none either (`0 tag(s)`), and no
`Default__SVehicleSimCar` ships in `BmGame.upk` — so that one field still has no file value; the
measured 1.212 s is the observable, as the row says.

**Routes tried:** (1) class defaults — added 4 torque factors + the 1.5 s interp, not the air-time
field; (2) native — not attempted (the observable is measured); (3) captures — this *is* the route that
answered; (4) published sources — not used.

## F-7 · `AirControl` — FOUND: 0.05

**Value:** `Pawn.AirControl` = **0.05** — the engine's air-control authority, unitless (0.05 = 5 % of
ground control), decoded from the class default object of `Pawn` itself. `RVehicleSimBatmobile` does not
override it (no tag at 0x0448); the Batmobile instead layers its own four torque factors on top (F-6
table above).

**Provenance:** decoded.

**Evidence** — `Engine.upk`, `Default__Pawn`, export 9699, tag at 0x0448 (1096 B, the offset
`MODES.json` gives for `Pawn.AirControl`):

```
$ python Tools/scripts/chase/ch1_dlo.py dlo Engine.upk Default__Pawn --want AirControl
Default__Pawn  export[9699]  class=Pawn  size=598  chain=Pawn -> Actor -> StateObject
  Pawn.AirControl (0x0448)                             FloatProperty                0.05000000074505806
1 tag(s) shown, 1 named by the SDK table
```

**Correction to the row's wording** (recorded here, `FOOTAGE.md` left untouched as instructed): the row
says *"not serialised in any of the four archetypes **or their class defaults**"*. The archetype half is
right; the class-default half is wrong — `Default__Pawn` carries it, and `Default__RVehicleSimBatmobile`
carries five of the six `AirControl*` fields (F-6 table). What G1 could not see is that the defaults
live in `Engine.upk`/`BmGame.upk`, outside its 15-package scope.

**Routes tried:** (1) class defaults — answered; (2) native — `b"AirControl\x00"` does **not** occur in
`BatmanAK.exe` (0 hits), so no native constant is needed; (3) captures — the observable is F-6's air
time; (4) published sources — not used.

## F-8 · `BattleModeCamConfig` — FOUND: `FFreeCameraConfig`, 24 members

**Value:** the battle-mode free-camera configuration as shipped in
`Default__R3rdPersonCamera` (`BmGame.upk`, export 34970), struct tag at field offset **0x3DF4 (15860)**,
266 B, 24 members:

| member | offset | value |
|---|---:|---|
| `StateFreeCameraSitOffsetMin` | 0x0000 | `[-350.0, 0.0, 200.0]` |
| `StateFreeCameraSitOffsetMax` | 0x000C | `[-500.0, 0.0, 200.0]` |
| `UseStateFreeCameraSitOffsetUp` | 0x0018 | `True` |
| `StateFreeCameraSitOffsetUp` | 0x001C | `[-1600.0, 0.0, 1400.0]` |
| `StateFreeCameraPullOffset` | 0x0028 | `[0.0, 0.0, 0.0]` |
| `CameraPivotOffset` | 0x0034 | `[0.0, 0.0, 5.0]` |
| `ZoomedOffset` | 0x0040 | `[50.0, 0.0, -30.0]` |
| `maxPitch` | 0x004C | `6000.0` (rotator units, 32.96 deg) |
| `MinPitch` | 0x0050 | `-14000.0` (rotator units, -76.90 deg) |
| `MinFreeCameraDistance` | 0x0054 | `1000.0` |
| `MaxFreeCameraDistance` | 0x0058 | `1000.0` |
| `ShortCamSpringConst` | 0x005C | `24.0` |
| `LongCamSpringConst` | 0x0060 | `8.0` |
| `DefaultCameraPitch` | 0x0064 | `0.0` |
| `CameraSitOffsetPower` | 0x0068 | `1.25` |
| `CameraSitOffsetMin` | 0x006C | `16384.0` |
| `CameraSitOffsetMax` | 0x0070 | `5000.0` |
| `bUseSeparate43Settings` | 0x0074 | `False` |
| `StateFreeCamera43SitOffsetMax` | 0x0078 | `[0.0, 0.0, 0.0]` |
| `StateFreeCamera43SitOffsetMin` | 0x0084 | `[0.0, 0.0, 0.0]` |
| `StateFreeCamera43SitOffsetLookUp` | 0x0090 | `[0.0, 0.0, 0.0]` |
| `bDontModifySitOffsetWhenLookingUp` | 0x009C | `False` |
| `MinCameraSmoothingAngle` | 0x00A0 | `10.0` |
| `MaxCameraSmoothingAngle` | 0x00A4 | `10.0` |

(rotator-unit conversions are derived: 6000/65536×360 = 32.96 deg, −14000/65536×360 = −76.90 deg.)

**Provenance:** decoded.

**Evidence:**

```
$ python Tools/scripts/chase/ch1_dlo.py struct BmGame.upk Default__R3rdPersonCamera 0x3DF4
tag 0x3DF4 R3rdPersonCamera.BattleModeCamConfig = FFreeCameraConfig : 24 member(s)

  StateFreeCameraSitOffsetMin                  (0x0000) VectorProperty       [-350.0, 0.0, 200.0]
  ...
  MaxCameraSmoothingAngle                      (0x00A4) FloatProperty        10.0
```

Sibling battle-mode camera fields in the same default object (not part of the struct, but the rest of
what the battle camera runs on):

```
  R3rdPersonCamera.FreeCameraHeadOffset (0x0E58)        VectorProperty   [0.0, 10.0, 80.0]
  R3rdPersonCamera.BattleModeCamFOV (0x4FD0)            FloatProperty    60.0
  R3rdPersonCamera.BattleModeWinchCamFOV (0x4FD4)       FloatProperty    60.0
  R3rdPersonCamera.BattleModeHeadOffset (0x4FDC)        VectorProperty   [0.0, 0.0, 150.0]
  R3rdPersonCamera.BattleModeWinchHeadOffset (0x4FF8)   VectorProperty   [0.0, 0.0, 300.0]
  R3rdPersonCamera.BattleModeAbseilingExtraCameraRot (0x5034) RotatorProperty [1500, 0, 0]
```

**Correction to the row's wording** (again recorded, not edited): the row's reason is `WRONG-SCOPE` and
it says the struct is *"not serialised in any of the four archetypes or their class defaults"*. The
class-default half is false — the struct is there, with all 24 members. (Two sibling chases reached the
same three camera structs in the same default object from the other side: `chase-02.md` F-9/F-10 decode
the winch and abseiling configs and note *"`BattleModeCamConfig` (F-8, same finding)"*. This chase reads
the battle one; the tables do not conflict.)

**Routes tried:** (1) class defaults — answered; (2) native — `b"BattleModeCamConfig\x00"` does not occur
in `BatmanAK.exe` (0 hits); (3) captures — a camera config is not recoverable from pixels without a
calibration reference; (4) published sources — not used.

---

## UNKNOWNs and limits, stated rather than filled

- **F-4** is a *rule*, not a value, and its body was not located: the exe carries the native-binding name
  (`0x1E13028` VA) but no pointer from `.data` to it, and there is no PDB/map. A disassembly would be
  guesswork about which of 55 MB of `.text` is the function; that was not done, so the decision stays
  UNKNOWN rather than described plausibly.
- **F-5** needs a number that lives on an enemy projectile archetype outside both the grab and the
  camera/vehicle class defaults. The negative is measured, not assumed: no tank weapon class in
  84 813 names, no `Damage` on any `RVehicleNPCWeapon` default, tank packages art-only.
- **A class default is not the shipped value.** Two rows proved the difference in opposite directions:
  F-3/F-2 (archetype overrides CDO: 0.0 vs 0.3333, 0.1 vs 1.5) and F-1/F-7/F-8 (nothing overrides the
  CDO, so the CDO *is* the shipped value). Any consumer of these numbers must say which layer it read.
- The default-object walk assumes the DLO's tag offsets are the native class offsets, which
  `BMSDK_OFFSETS.json` states and which the two independent checks (`Pawn.AirControl` 1096 ↔ 0x0448,
  `R3rdPersonCamera.BattleModeCamConfig` 15860 ↔ 0x3DF4, both confirmed by the field's declared type and
  its neighbours) support. A wrong offset would show up as a value whose type does not match the SDK
  member's kind; none did in the rows above.
- `Default__SVehicleSimCar` does not ship in `BmGame.upk`, so `AirControlTimeInAir` (0x04BC) has no value
  on either layer — the row's `VALUE-NATIVE` reason survives for that one field even though its six
  siblings now have values.
- No footage number was used to override a file value (R4), and no published source was used as a sole
  value. No game was launched, nothing under `D:/Games` was written, no shared module was edited, no git
  action was taken, and no secret is in this file.
