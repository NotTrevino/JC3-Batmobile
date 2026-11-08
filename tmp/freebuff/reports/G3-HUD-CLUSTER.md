# G3-HUD-CLUSTER - the Batmobile HUD cluster, decoded from the bytes

STATUS: done - the four operator leads are decided file-side: (a) CONFIRMED, (b) CONFIRMED,
(c) REFUTED as a gauge (the "second gauge" is the boost-upgrade badge pair plus the bar's `Cap`;
the cooldown exists natively and never reaches the movie), (d) CONFIRMED, with a per-vehicle
JC3 route that is derived, not built. No game was launched, attached to or written to; nothing
was installed.

## Files written

| file | what |
|---|---|
| `Tools/scripts/bmak_hud_cluster.py` | new tool: `--write` / `--check` / `--tamper-test`; re-derives every number from the movie bytes, the decompiled AS3, the BmSDK headers and JC3's `hud.as` |
| `Working/HUD/CLUSTER.json` | the generated record (clip transforms, boost fill, badges, native fields, JC3 API, speedometer proof) |
| `Working/HUD/CLUSTER.md` | the generated report: cluster, afterburner, health, speedometer, the four leads, the row table, the JC3 routes, COMPROMISES |
| `tmp/freebuff/reports/G3-HUD-CLUSTER.md` | this report |
| `tmp/freebuff/scratch/hud/{tree.py,t2.py,tags.txt,m.gfx,xo/}` | scratch: the first two parser probes and the ffdec tag dump used to settle the fill direction |

No existing file was edited. Nothing was written under a game install, `Builds/` or the dropzone.

## What was decoded

Sources, all read-only: `BmGame.upk` (`HudModuleBatmobile.Image`, re-carved), the decompiled AS3
of that movie (`E:/Modding/_gamedata/BmAKgrab_early/hud/modules/HudModuleBatmobile/dec`), the
BmSDK headers in `Working/vendor/BmSDK/`, JC3's `ui/hud.gfx` decompile
(`E:/Modding/_gamedata/JC3grab/hud/dec`), `Research/BatmobileGrab/{HUD.md,HUD_INTERFACES.json,
SPEEDOMETER.md,SPEEDOMETER.json}` and `Working/Translation/T6_HUD_CAMERA.md`.

### 1. The cluster and its stage position

The clip tree is read from the GFx tag stream (SymbolClass -> DefineSprite -> PlaceObject2), and
the **authored 3D transforms** from the parent classes, because the place tags for `Health` and
`BoostMovie` are identity matrices - the position lives in `AnimatorFactory3D` property arrays:

| clip | authored x | y | z | yaw | screen estimate (512+x, 384+y) |
|---|---:|---:|---:|---:|---|
| `HudMaster.LeftSideParent.Health` | -479.228 | -328.300 | 8.318 | 10.0° | **(32.8, 55.7)** |
| `HudMaster.LeftSideParent.BoostMovie` | -452.867 | 65.550 | 24.110 | 26.0° | **(59.1, 449.6)** |
| `HudMaster.LeftSideParent.Combo` | -460.237 | -263.250 | 36.326 | 26.0° | (51.8, 120.8) |
| `HudMaster.LeftSideParent.RemoteInterface` | -525.275 | 225.000 | 51.171 | 26.0° | (-13.3, 609.0) |
| `HudMaster.RightSideParent.BoostMovie` | 446.000 | 180.500 | 56.890 | -40.0° | right group |
| `HudMaster.RightSideParent.ClockTimer` | 399.200 | 60.750 | 0.000 | -38.0° | right group |

The screen estimate is **derived**: the root placements are identity, the movie's
`__setPerspectiveProjection_` sets `projectionCenter = (512,384)` (the centre of the 1024x768 SWF
surface, whose module stage is 1024x720), so the authored x/y are measured from that centre; the
z values (<= 25) against a focal length of order 10^3 move the projected point by < 1 %, so the
corner/edge assignment does not depend on the projection constant. The left/right grouping is
independently proven by `ModuleStruct_Batmobile.OnRatioChanged`:
`RightSideParent.x = base + band`, `LeftSideParent.x = base - band`.

Mode machine (`SetBattleAndZoomMode`): `DRIVE -> BATTLE -> ZOOMED`, transitions by
`gotoAndPlay(<from>TO<to>)`; `BattleAndZoomInterface.visible` false in `DRIVE`. Boost has **no**
mode gate; the health bar's transform never changes with the mode - only its visibility.

### 2. Afterburner: one gauge, one value

* `UC_SetBoostLevel(level:int, upgradeLevel:int)`; shown while `level < 100`; hidden by
  `UC_HideBoostGauge` at `level >= 100` unless `bHoldBoostOnscreenUntilUsed`.
* Fill clip: **102 frames**, `this.FillMovie.gotoAndStop(this.BoostLevel + 1)`; the fill's scale-y
  goes **0.011 -> 1.0** with a fixed x/y anchor while the `Cap` rides up y **9.5 -> -182.5**:
  **vertical, bottom-anchored, fills upward**, 101 value steps.
* `SetBoostBarCharging(param1 > this.BoostLevel)` plays `Charging` on `Background.Upgrade1/2`
  (65 frames each, labels `Normal`/`Charging`); `SetBoostBarDecreasing` plays `Cap`'s `Decrease`
  and the bar's `Shake` while draining.
* Badges: `Upgrade1` at (-10.0, 96.3), `Upgrade2` at (-10.5, 100.6) - visible when
  `upgradeLevel > 0 / > 1`; `Background` has 32 frames, labels `Basic/Extra1..Extra4`.
* Native: `RVehicleSimBatmobile.BoostDuration` float 664 = **2.0 s**; `BoostCooldown`
  InlineArray<float> 668/672/676, tier 0 default = **12.0 s**; `BoostCooldownUpgradeLevel` int
  680; `CurrentBoostTimer` float 808 = 1.0; `BoostDurationDonut` 688 = 6.0;
  `DriftingBoostCooldown` 684. `RVehicleBatmobile.fAfterburnerStartTime` 8584 and
  `fAfterburnerCutoffStartTime` 8596 exist (no CDO default read).

### 3. Health bar

`UC_SetHealth(health, max)`; `Math.min(1, h)` onto `Healthbar.Bar`, `Math.max(0, h-1)` onto
`ArmourForeground`, `max > 1` selects `ArmourBackground` label `Armour<n>` with
`n = int((max-1)*4)` (5 tiers); pulse below 0.2; `MaxHealthChangePerFrame = 0.05` at 30 Hz
(0.667 s full sweep); `GoOffscreenTimer = 2` s; battle calls
`UC_SetHealthBarVisible(true,"Delayed")` and `UC_SetHealthBarVisible(false)` returns early in
battle. Clip `Health` = `Timeline_390`, 162 frames, labels
`IntroDelayed/Intro/Idle/XPFill/Outro/Out`. Damage readout
`UC_SetImpactDamageFlash(part, x, y, frames)` places a `DamageEffectMovie` at
`StageWidth*x`/`StageHeight*y` with `rotationY = ±60`, text = `String(frames)`; the bar-level
damage flash is `BG`'s `Pulse`/`Idle` pair on the < 0.2 pulse. Native vehicle health is
`RVehicle.MaxHealth` (IntProperty, offset 2148) / `RVehicle.GetMaxHealth()`; no armour field was
found in the BmSDK headers (UNKNOWN, see below).

### 4. Speedometer

BmAK draws none: 0 of 252 `UC_*` setters are speed/rev/gear-shaped, 0 speed tokens exist in this
movie, and `SPEEDOMETER.md`/`SPEEDOMETER.json` prove the only speedometer in the install is the
native debug readout `RPlayerController.bDebugSpeedometer`, off in both configs.

JC3 side (decoded from `hud.as`): `SetVehicleType` only writes the unit label
(`hud_kph`/`hud_knots`) and touches no `visible`; `SetVisibilities()` is literally
`MCI_speedo.visible = true`; `HideVehicleUi()` hides `MCI_speedo` + `MCI_speedometer` +
`MCI_nitro_meter` + `MCI_jump_meter` + `MCI_bavarium_shield`; `InitPrimaryMeter` 1 call site,
`SetPrimaryMeterValue` 0, `SetVehicleType` 0 - the caller is native. There is **no per-vehicle
switch** in the movie; the only discriminators are `m_CurrentType` (LAND 0, AIRPLANE 1,
HELICOPTER 2, SEA 3) and `TXT_name`. Route (derived, R7-compliant): a **private copy of
`ui/hud.gfx`** whose `SetVisibilities` leaves `MCI_speedo` hidden for this vehicle; never the
shared module.

## 5. JC3 host for each gauge

See `Working/HUD/CLUSTER.md` section 7 for the table with the next 5-minute experiment per route.
Summary: the primary boost -> `MCI_nitro_meter` (`SetProgress` 0..1, `Hide`, ready sound at 1);
health -> the vehicle health paint; both need a caller that does not exist in the movie (native,
UNKNOWN). Reusing the BmAK `BoostMovie` inside `hud.gfx` and a custom HUD module are both
**UNKNOWN** - no evidence either way - with a tag-version comparison as the cheap probe.

## 6. Row table

| BmAK element | decoded evidence | JC3 route | status |
|---|---|---|---|
| afterburner (primary) | `UC_SetBoostLevel(level 0..100, upgrade)`; `Fill` 102 frames, frame = level+1, scale-y 0.011 -> 1.0 bottom-anchored | `MCI_nitro_meter` (`InitVehicleNitrous`/`UpdateVehicleNitrous`, `SetProgress(0..1)`) | decoded / map (caller native, UNKNOWN) |
| second cooldown gauge | not present: 0 cooldown setters, 1-frame unnamed clip at (5.0,-83.7); `BoostCooldown[3]` + `BoostCooldownUpgradeLevel` native only | none (JC3 `MCI_nitro_meter` is the only recharge member) | refuted in BmAK / UNKNOWN in retail |
| upgrade badges | `Upgrade1/2` at x -10.0/-10.5, 65 frames, `Normal`/`Charging`, visible by `upgradeLevel` | none | decoded / no JC3 member |
| health bar | `UC_SetHealth(health, max)`; `Bar` fill `min(1,h)`; pulse < 0.2; 2 s offscreen; 0.05/frame at 30 Hz | `MCI_vehicle` health paint / bar | decoded / map health 0..1 |
| armour tiers | `max(0,h-1)` onto `ArmourForeground`; `max>1` selects `Armour<n>` of 5 | none - no armour field in the vehicle HUD | decoded / out (stated absence) |
| damage readout | `UC_SetImpactDamageFlash(part,x,y,frames)`: number at `StageWidth*x`, `StageHeight*y`, rotationY ±60 | none | decoded / out |
| speedometer | 0 of 252 setters, 0 speed tokens; `bDebugSpeedometer` off in both configs | `MCI_speedo` - the Batmobile must hide it (private `hud.gfx` copy) | decoded / route derived, caller UNKNOWN |

## COMPROMISES (for operator approval - this report approves none)

### C1 - the second (cooldown) gauge
BmAK sends no cooldown value to the HUD (0 setters); the native `BoostCooldown` tiers never reach
the movie. JC3 has one recharge member (`MCI_nitro_meter`) which the primary boost gauge already
uses.
**RECOMMENDED COMPROMISE:** omit the second gauge and keep `MCI_nitro_meter` as the single boost
bar; accuracy lost: the recharge-tier feedback the badges give in BmAK is gone.

### C2 - armour above 1.0
BmAK draws a second fill (`ArmourForeground`) and five `Armour<n>` tiers; JC3's vehicle HUD has no
armour field, so health > 1 would clip at full.
**RECOMMENDED COMPROMISE:** map health 0..1 only, dropping the armour overlay; accuracy lost:
armour damage reads as nothing until the bar starts moving.

### C3 - speedometer
JC3 draws a speedometer for every land vehicle and `SetVisibilities` re-shows it unconditionally;
BmAK's Batmobile HUD draws none.
**RECOMMENDED COMPROMISE:** ship a private `ui/hud.gfx` copy whose `SetVisibilities` leaves
`MCI_speedo` hidden for this vehicle; accuracy lost: none - this removes a JC3-only element.

### C4 - fill direction and motion
BmAK's boost fill is vertical, bottom-anchored, 101 steps plus a `Shake` and a rising `Cap`; JC3's
nitro meter is a horizontal 0..1 progress member.
**RECOMMENDED COMPROMISE:** keep JC3's orientation and drive `SetProgress(level/100)`; accuracy
lost: the vertical rise and the drain shake.

### C5 - upgrade badges
`Upgrade1/2` are two 65-frame badge clips toggled by `UC_SetBoostLevel`'s second argument; JC3 has
no badge member.
**RECOMMENDED COMPROMISE:** drop them; accuracy lost: the player cannot see the boost-recharge
upgrade level.

## Reopened T-6 dispositions (this task's brief)

* `T-HUD1` ("speed -> **reuse** `MCI_speedo`") is reopened: with no BmAK speedometer the correct
  disposition is **suppress** for this vehicle, not reuse.
* `T-HUD2` ("boost -> `MCI_nitro_meter`, `recharge = level / 100`, badges have no equivalent")
  stands as a map, and now has a decoded basis (`Fill` 102 frames, `level+1`, bottom-anchored) plus
  C4 for the orientation loss. Its "badges have no equivalent" line is confirmed (no JC3 member),
  and the lead-(c) claim does not add a second member to map.
* `T-HUD3`/`T-HUD4` (health / armour) stand; C2 covers the armour loss.

## Commands run (verbatim)

```
$ python Tools/scripts/bmak_hud_cluster.py --write
wrote E:\Modding\JC3-Batmobile\Working\HUD\CLUSTER.json
wrote E:\Modding\JC3-Batmobile\Working\HUD\CLUSTER.md
{
 "leads": {
  "RemoteInterface": { "x": -13.3, "y": 609.0 },
  "BoostMovie": { "x": 59.1, "y": 449.6 },
  "Health": { "x": 32.8, "y": 55.7 },
  "Combo": { "x": 51.8, "y": 120.8 }
 },
 "boost": "Y, bottom-anchored: fill scale-y 0.011 -> 1.0 with a fixed x/y anchor, the Cap riding up y 9.5 -> -182.5",
 "badges": [ "Upgrade1", "Upgrade2" ],
 "speed_setters": [],
 "sim": { "BoostCooldown": 12.0 }
}
```

```
$ python Tools/scripts/bmak_hud_cluster.py --check
PASS: cluster record current
```

```
$ python Tools/scripts/bmak_hud_cluster.py --tamper-test
PASS: tamper at clips.Health.transform.x rejected
PASS: tamper at jc3.api rejected
PASS: tamper at bmak.health.pulse_below rejected
PASS: 3/3 tamper probes
```

```
$ python -c "import json;d=json.load(open('Working/HUD/CLUSTER.json'));n=d['native'];print('SIMDEF',n['sim_defaults']);..."
SIMDEF {'BoostDuration': 2.0, 'BoostCooldown': 12.0, 'BoostDurationDonut': 6.0, 'CurrentBoostTimer': 1.0}
BASEDEF {}
VEHDEF {}
RVehicleSimBatmobile.g.cs {'BoostDuration': (664, 'float', []), 'BoostCooldown': (668, 'float', []), 'BoostCooldownUpgradeLevel': (680, 'int', []), 'CurrentBoostTimer': (808, 'float', []), 'DriftingBoostCooldown': (684, 'float', []), 'BoostDurationDonut': (688, 'float', [])}
RVehicleBatmobile.g.cs {}
RVehicleBatmobileBase.g.cs {}
RVehicle.g.cs {'MaxHealth': (2148, 'int', [])}
```

```
$ python Tools/scripts/bmak_speedometer.py --check
PASS: speedometer record current
```

```
$ for f in SetVehicleType InitPrimaryMeter SetPrimaryMeterValue InitSecondaryMeter SetVisibilities; do
      printf "%-22s %s\n" "$f" "$(grep -c "this\.$f(" .../hud.as)"; done
SetVehicleType         0
InitPrimaryMeter       1
SetPrimaryMeterValue   0
InitSecondaryMeter     1
SetVisibilities        0
```

```
$ java -jar ffdec.jar -dumpSWF movie.gfx > tags.txt      (scratch dump, used to settle the fill)
$ grep -n "DefineSprite (chid: 1036)" tags.txt && sed -n '23155,23170p' tags.txt
00084ca5:      0. PlaceObject2 (chid: 1032, dpt: 3, nm: "Cap") tagId= 26 len=      29  ...
00084cc8:      1. ShowFrame               tagId=  1 len=       0
00084cca:      2. PlaceObject2 (chid: 1035, dpt: 1) tagId= 26 len=      27  1e 01 00 0b 04 c9 ...
00084cf5:      4. ShowFrame               tagId=  1 len=       0
```

```
$ java -jar ffdec.jar -swf2xml out.xml movie.gfx
File not found.            <- ffdec 26.4.0 refuses the CFX container for -swf2xml; the
                              tag tree was therefore parsed in Python (bmak_hud_cluster.py) and
                              cross-checked against -dumpSWF, which reads it fine.
```

Two bugs were found and fixed while verifying, both in my own new tool (no existing file touched):
a shallow copy of the per-depth placement slots made every frame show the last frame's matrix
(the fill then read scale-y 1.0 everywhere), and `--check` compared a tuple to a list in
`bmak.boost.upgrade_visibility` and failed on unchanged input. The tamper test exists because of
the second one.

## UNKNOWNs

* **What ch1040 is.** The third child of `BoostMovie` is a 1-frame clip at (5.0, -83.7) with no
  instance name in the tag stream and no setter. A 1-frame clip cannot carry a gauge value, but
  its identity (the scanlines overlay is a candidate) is not proven. Where it would be found: the
  `SymbolClass` table has no entry for 1040; its shape reuses an embedded symbol, so only the
  original FLA (not shipped) would name it.
* **Whether retail draws a second/cooldown gauge outside this module.** 0 of 252 setters in 19
  movies carry a cooldown or charge value, so the Batmobile module cannot; a different module
  (e.g. the radar or the container `ModularHudBm3`) could paint one natively. Where it would be
  found: `RHudModuleBatmobile`'s cached function list (37 names, none about cooldown) or a frame
  capture. Not in the files.
* **The vehicle armour field.** `RVehicle.MaxHealth` exists (int, 2148) but no armour/armour-tier
  native field was found in the BmSDK headers, although the movie draws `Armour0..4` from
  `UC_SetHealth`'s `max`. Where it would be found: the damage component's per-channel armour
  (`DAMAGE_MODEL.md` calls it a per-channel number) rather than a vehicle scalar; not decoded here.
* **The JC3 caller.** `InitPrimaryMeter`/`SetPrimaryMeterValue`/`SetVehicleType` are called from
  native code (0-1 call sites in the movie), so how JC3 decides *which* meter a vehicle gets, and
  whether a Batmobile-only flag is possible without a private `hud.gfx`, is UNKNOWN. Where it
  would be found: the game's HUD binding code, not the movie; or an experiment (section 5).
* **Reusing BmAK art inside `hud.gfx`.** Whether a BmAK `DefineSprite` (AVM2, CFX v0f, art in
  `Image_I1*.tfc`) can be imported into JC3's `hud.gfx` is UNKNOWN: no file states the GFx
  runtime version of either side's loader. 5-minute probe: compare the two movies' SWF/AVM tags
  with `ffdec -dumpSWF`.
* **`Health` sub-clip offsets.** The health bar's internal children (`Healthbar`, `ArmourForeground`,
  `BG`, `XPbar`) are placed with `PlaceObject3` (MATRIX3D), which this tool does not decode; their
  local offsets are therefore not quoted. The `Health` clip's own transform (the one that answers
  the operator's question) is decoded.
