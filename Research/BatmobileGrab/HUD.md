# Batmobile HUD — the whole modular HUD, its interfaces and what it draws

The first HUD pass carved **two** movies (`HudModuleBatmobile.Image`, `StoryModeHUD.HUD`) from a
hand-written list and called that "the HUD". It was not: the game runs **25 `RHudModule*` classes**,
carves **19 SwfMovie exports** for them, and the Batmobile shares its screen with radar, target
lock-on, alerts, boss bars and the on-foot combat HUD. The list was the architecture failure this
pass fixes: the roster is now read from the engine, and every module's movie is bound by evidence.

Re-runnable: `bmak_hud_inventory.py roster|build|interface|check`, `bmak_hud.py check`, `hud_spec.py`.

## 1. What is actually there

`BmGame.upk` + `Startup.upk` export **61 SwfMovie** objects. Nineteen of them are the in-game HUD:

| key | object | payload | inflated | scripts | sha256 |
|---|---|---:|---:|---:|---|
| `HudModuleBatmobile` | `HudModuleBatmobile.Image` | 423,056 | 671,744 | 99 | `2a5d0be143bd…` |
| `HudModuleTargets` | `HudModuleTargets.Image` | 252,938 | 618,496 | 253 | `85244d23781b…` |
| `RadialGadgetSelect` | `RadialGadgetSelect.Image` | 96,769 | 196,608 | 52 | `12bd7b781c31…` |
| `HudModuleScanner` | `HudModuleScanner.Image` | 78,376 | 200,704 | 87 | `f24bd5bd4dc3…` |
| `HudModuleHealth` | `HudModuleHealth.Image` | 73,533 | 163,840 | 74 | `e801a0227b80…` |
| `HudModuleStoryMode` | `HudModuleStoryMode.Image` | 73,215 | 176,128 | 64 | `bf786a78ebf4…` |
| `HudModuleBespokeLocalRadar` | `HudModuleBespokeLocalRadar.Image` | 66,317 | 139,264 | 58 | `f9f622d5a068…` |
| `HudModuleDetectiveMode` | `HudModuleDetectiveMode.Image` | 80,440 | 245,760 | 131 | `cb8a1a47d9f8…` |
| `HudModuleDownloadProgress` | `HudModuleDownloadProgress.Image` | 36,367 | 73,728 | 43 | `db7a9e0c09cd…` |
| `HudModuleObjectives` | `HudModuleObjectives.Image` | 33,271 | 65,536 | 24 | `fffce6dfb084…` |
| `HudModuleAlertsAndSurveillance` | `HudModuleAlertsAndSurveillance.Image` | 32,856 | 65,536 | 33 | `8e9658431c8d…` |
| `HudModuleCrimeSceneInfo` | `HudModuleCrimeSceneInfo.Image` | 30,904 | 61,440 | 30 | `9fc194826349…` |
| `HudModuleDetectiveModeJamming` | `HudModuleDetectiveModeJamming.Image` | 29,786 | 61,440 | 33 | `bfc6e95a50de…` |
| `HudModuleBoss` | `HudModuleBoss.Image` | 29,329 | 57,344 | 32 | `7f0802eea346…` |
| `StoryModeHUD` | `StoryModeHUD.HUD` | 23,758 | 60,077 | 39 | `1ceedb619922…` |
| `HudModuleRoomName` | `HudModuleRoomName.Image` | 15,016 | 32,768 | 15 | `55a45c184f7f…` |
| `ModularHudBm3` | `ModularHudBm3.Image` | 12,506 | 24,576 | 14 | `fea247fd8dc2…` |
| `HudModuleDownloadProgress_HudModuleDownload_Batman` | `HudModuleDownloadProgress.HudModuleDownload_Batman` | 11,993 | 24,576 | 15 | `893851787168…` |
| `HudModuleSuicideCars` | `HudModuleSuicideCars.Image` | 8,829 | 16,384 | 12 | `991560f8b154…` |

**252 `UC_*` setters** across those movies are extracted into `HUD_INTERFACES.json`; the sizes and
hashes above live in `HUD_INVENTORY.json` and are what `check` re-reads from the game. Textures are
not in this inventory: each module's art streams from the `.tfc` companions and the first pass
exported only `HudModuleBatmobile.Image_I1`/`_I1B`/`_I1C6`/`_I28B`. The inventory covers every
HUD movie **this install ships**; the ten classes in §2 have no movie here, so their behaviour is
unmapped rather than assumed.

`ModularHudBm3` is the container document (the movie that hosts modules), `StoryModeHUD` is the
shared prompt/icon HUD, `RadialGadgetSelect` is the gadget wheel, and
`HudModuleDownloadProgress.HudModuleDownload_Batman` is the download module's extension movie —
the two movies in one package used to overwrite each other in one output directory; the inventory
keys them apart now.

## 2. The roster the grab was missing

`bmak_hud_inventory.py roster` reads `BmGame.upk`, lists every class default object that names a
`SwfMovie`, and keeps the `RHudModule*` subset. Twenty-five module classes exist; fifteen are bound
to a movie:

| native module | movie | bound by |
|---|---|---|
| `RHudModuleAlertsAndSurveillance` | `HudModuleAlertsAndSurveillance.Image` | default object |
| `RHudModuleBatmobile` | `HudModuleBatmobile.Image` | default object |
| `RHudModuleCrimeSceneInfo` | `HudModuleCrimeSceneInfo.Image` | default object |
| `RHudModuleDetectiveMode` | `HudModuleDetectiveMode.Image` | default object |
| `RHudModuleDetectiveModeJamming` | `HudModuleDetectiveModeJamming.Image` | default object |
| `RHudModuleDownloadProgress` | `HudModuleDownloadProgress.Image` | default object |
| `RHudModuleHealthBar` | `HudModuleHealth.Image` | default object |
| `RHudModuleLocalRadar` | `HudModuleBespokeLocalRadar.Image` | default object |
| `RHudModuleObjectives` | `HudModuleObjectives.Image` | default object |
| `RHudModuleRoomName` | `HudModuleRoomName.Image` | default object |
| `RHudModuleScanner` | `HudModuleScanner.Image` | default object |
| `RHudModuleStoryMode` | `HudModuleStoryMode.Image` | default object |
| `RHudModuleSuicideCars` | `HudModuleSuicideCars.Image` | default object |
| `RHudModuleTargets` | `HudModuleTargets.Image` | default object |
| `RHudModuleBoss` | `HudModuleBoss.Image` | **interface match** 2/2 |

Two owners sit outside the namespace and are recorded too, because a name filter cannot see them:
`RGFxMovieRadialGadgetSelect` owns `RadialGadgetSelect.Image` (the gadget wheel), and
`RHudModuleDownloadProgress` owns **two** movies — `HudModuleDownloadProgress.Image` and the
`HudModuleDownloadProgress.HudModuleDownload_Batman` extension. The inventory keeps `movies[]` per
class and carves both, instead of collapsing them to one path.

`RHudModuleBoss` has no `SwfMovie` in its default object, yet its class caches
`CachedFunction_JustShake` and `CachedFunction_SetHealthLevel`, and `HudModuleBoss` is the only
movie that defines `UC_JustShake` and `UC_SetHealthLevel`. That pairing is a proof, not a guess:
the matching rule in `interface` is "a module's cached function names must exist as `UC_*` in the
movie". `HudModuleBoss` also carries a `FireflyIcon` element, so the boss movie has a Firefly
path; `RHudModuleFirefly`'s own `SetHealthBar` does not match it, so the subclass reuse is
plausible but not proven.

**Ten classes have no movie in this install:** `RHudModuleBespokeBase`, `RHudModuleChallengeMode`,
`RHudModuleExtraSequence`, `RHudModuleFirefly`, `RHudModuleForensicBeaconTracking`,
`RHudModuleForensicDetail`, `RHudModuleGadgetSelect`, `RHudModuleHackingMode`,
`RHudModuleHeavyTankScanBase`, `RHudModulePerformanceTest`.

They fall into three groups, and the inventory reports them rather than hiding them:

- **base classes** — `BespokeBase`, `HeavyTankScanBase`: subclasses (`LocalRadar`) supply the movie.
- **native-only / dev** — `PerformanceTest` (0 default-object tags), `ForensicDetail` (0 cached
  names), `HackingMode`; no movie defines their cached names, so their calls resolve to nothing.
- **unshipped or extension movies** — `ChallengeMode` (`SetTanksByZone`), `ExtraSequence`
  (`SetSpeedBar`, `SetGubbinsInfo`, `SetReticle`), `ForensicBeaconTracking` (`SetLockon`),
  `Firefly` (a boss-movie icon exists, no name match). No carved movie implements their cached
  names. `GadgetSelect` is the odd one: it caches none at all, and the gadget wheel movie is owned
  by `RGFxMovieRadialGadgetSelect`, so the `RHudModule` class may not be the wheel's driver.

This is the part that changes how the grab is judged: a module whose movie is named differently
(`RHudModuleLocalRadar` → `HudModuleBespokeLocalRadar`) or omitted from its default object (Boss)
is invisible to a filename list, and both would have stayed invisible.

## 3. Decompilation

`ffdec` (JPEXS Free Flash Decompiler 26.4.0) reads the CFX container directly:

```
java -jar ffdec.jar -export script <out> movie.gfx
java -jar ffdec.jar -swf2xml <out>/movie.xml movie.gfx
java -jar ffdec.jar -dumpSWF movie.gfx > <out>/tags.txt
```

Each SwfMovie's `RawData` is `u32 length`, `CFX` magic, version `0x0f`, an 8-byte header, then a
zlib stream of GFx tags. `bmak_hud.py carve()` extracts that array; umodel cannot address the
dotted object path. The inflated streams and decompiled scripts stay outside the repository
(`_BmAK_grab/hud/modules/<key>/`).

## 4. The Batmobile module

51 frames, 30 fps, 1024×768 SWF surface, stage 1024×720; `ModularHudBm3.TickDeltaTime` is `0.033`.
The document class is `ModularHudBm3`; the module is `ModuleStruct_Batmobile`.

Main timeline labels:

| state | labels |
|---|---|
| drive / battle / zoom | `DRIVE`, `BATTLE`, `ZOOMED` |
| transitions | `DRIVETOBATTLE`, `BATTLETODRIVE`, `BATTLETOZOOMED`, `ZOOMEDTOBATTLE`, `ZOOMEDTODRIVE` |
| intro / outro | `Intro`, `In`, `Outro`, `Out`, `Initial`, `Prototype`, `FirstBootUp` |
| health | `Intro`, `IntroDelayed`, `Outro`, `XPFill`, `ShowDamage`, `Normal`, `Warning` |
| boost | `Intro`, `Outro`, `None`, `Charging`, `Decrease`, `DecreaseToZero` |
| energy | `Charges2`, `Charges3`, `Charges4`, `Full`, `BecomeFull`, `Use`, `LoseToHit`, `LoseToInaccuracy`, `Empty` |
| cannon | `PreReady`, `Ready`, `PreReadyLevel1`, `PreReadyLevel2`, `Blank` |
| winch | `Intro`, `Outro` |
| clock | `Initial`, `Pause`, `Resume`, `Expired`, `ExpiredOutro` |

`ModuleStruct_Batmobile.SetBattleAndZoomMode(battle, zoomed)` is the mode machine:

```text
DRIVE  --battle------------> BATTLE
DRIVE  --zoomed------------> ZOOMED (implies battle)
BATTLE --zoomed------------> ZOOMED
BATTLE --battle off--------> DRIVE
ZOOMED --zoomed off--------> BATTLE
ZOOMED --battle off--------> DRIVE
```

It calls `BattleAndZoomInterface.gotoAndPlay(<from>TO<to>)`, sets the interface visible outside
`DRIVE`, and keeps the heavy reticle at alpha 1 when leaving `DRIVE`. Entering battle forces the
health bar visible with the `Delayed` intro; leaving it hides the bar only when health is full and
XP has settled. `UC_SetBattleModeOpacity` dims the overlay rather than switching screens.

The 37 setters are in `HUD_INTERFACES.json`; the ones with real state:

| setter | arguments | what it drives |
|---|---|---|
| `UC_SetHealth` | `health, max` | health 0…1, armour above 1, `Armour<n>`, 2 s offscreen timer |
| `UC_SetHealthBarVisible` | `visible, introSuffix` | `Intro`/`Outro`, `Delayed` variant |
| `UC_SetXpLevel` | `proportion, instant` | XP bar |
| `UC_SetBoostLevel` | `0…100, upgradeLevel` | boost gauge, upgrade badges, charging states |
| `UC_SetEnergySystemParams` | `charges, max, proportion, instant, state` | `Charges<n>`, fill/target, hit/deplete animations |
| `UC_SetCannonCoolDown` | `0…4` | reticle `Ready` / `Blank` / `PreReady*` |
| `UC_SetSpecialWeapons` | `3 × state` | `Unavailable` / `Available` / `Used` / `Lost` |
| `UC_SetWinchMeter` | `coneAngle, needleAngle, onTarget` | winch cone and needle rotation |
| `UC_SetTurnAround` | `direction` | turn-back symbol |
| `UC_SetOccupant` | `visible, name, icon, …` | passenger HUD |
| `UC_SetBatmobileCombo` | `proportion, count, seconds` | combo meter |
| `UC_SetBattleAndZoomMode` | `battle, zoomed` | the mode machine |
| `UC_SetImpactDamageFlash` | `part, amount, duration, frames` | hit flash |
| `UC_SetVirusUploadState` | `state, warning` | virus upload widget |
| `UC_SetForensicTracking` | `text` | forensic tracking readout |
| `UC_SetEnemyCount` / `UC_SetMedal*` | counts | challenge HUD |

The script side resolves each setter by name (`CachedFunction_Set*`), which is why the movie's
`UC_*` names can differ from the module's `Set*` names.

### 4.1 The vehicle health contract

`UC_SetHealth(health, max)` is read out of the decompiled setter, not described:
`hud_spec.py` extracts every expression below into `HUD_SPEC.json → bmak.health_contract`, and
`--check` fails if the movie stops agreeing with it.

| term | source expression | reads as |
|---|---|---|
| `health` | `this.TargetHealthProportion = param1` | a **proportion**, not hit points: 1.0 is one full bar |
| `max` | `this.HealthMax = param2` | the bar's ceiling; above 1 it adds armour tiers |
| bar fill | `Math.min(1, this.CurrentHealthProportion)` | the first bar is always 0…1 |
| armour fill | `Math.max(0, this.CurrentHealthProportion - 1)` | everything above 1 is the armour overlay |
| armour tier | `param2 > 1 ? int((param2 - 1) * 4) : 0` | `max` selects `Armour0…Armour4` (5 labels) |
| pulse | `param1 < 0.2 && TargetHealthProportion < 0.2` | the bar pulses below 20 % |
| sweep rate | `MaxHealthChangePerFrame = 0.05` at 30 Hz | 20 frames = **0.667 s** empty→full |
| offscreen | `GoOffscreenTimer = 2` | hides 2 s after full and XP settled |
| visibility | `UC_SetHealthBarVisible`, battle mode forces it | damage shows the bar; `Delayed` intro in battle |

**This is the Batmobile's bar, not Batman's.** `HudModuleHealth` is a second, separate contract:
`UC_SetHealthLevel(health:Number, instant:Boolean)`, `UC_SetArmourLevel(armourType:int,
proportion:Number, instant:Boolean)`, `UC_SetArmourMaxima(current:int, max:int)`,
`UC_SetAdrenalineLevel`, `UC_SetBatmobileTakedownDisplay`. Its elements are the Batsuit health,
ballistic armour, adrenaline and combo/takedown HUD. The vehicle bar has 0…1 + armour tiers; the
on-foot bar has an armour *type* plus a max pair. Reading one as the other would be wrong.

The movie has no notion of damage *sources*, so it cannot say whether a hit should count. It is the
instrument, not the rule: the Batmobile's immunity is engine-side
(`Research/JC3Grab/DAMAGE_MECHANISMS.md`), and this bar is what a take reads to prove it.

## 5. What the rest of the HUD draws

Every row below is read from the movies, not from a wiki. Element names are AS3 classes in the
decompiled package.

| module | elements | driven by |
|---|---|---|
| `HudModuleTargets` | `VehicleMissileTarget`, `…_bomb`, `…_emp`, `…_friend`, `…_multi`, `…Invalid`, `missile_border_anim`, `missile_lockon_square_anim`, `batmobile_lockon`, `batmobile_aim`, `batmobileattack`, `Tank_Hack_BOMB/EMP/FRIEND`, compass ring, `FocusDetail*`, grapple/winch reticles, `Vehicle_Onscreen` markers | `UC_SetBatmobileWeapon(primary, bool)`, `UC_SetBatmobileWeaponHit`, `UC_SetBatmobileWeaponFailure`, `UC_SetCompassMode`, `UC_SetFocusDetail`, `UC_SendToFlash(8 args)`, `UC_SetGrappleBoost`, `UC_SetSuperEject` |
| `HudModuleBespokeLocalRadar` | `RadarMovie`, `MapBackground`, `MapPulseTimer`, `LockonMeter`, `lockonAndHealthMeter`, `lockonStatusTextContainer`, `HeavyTankRadiusMovie`, `warning_alert` | `UC_SetPlayerPosition(x,y,z)`, `UC_UpdateTargetPosition(x,y,z,kind)`, `UC_SetLockonValue(value, kind)`, `UC_SetStationaryLockonValue`, `UC_SetHealthTitle/Value`, `UC_SetRootNetwork*`, `UC_PushHeavyTanksToFlash`, `UC_SetMaskEnormous`, `UC_DoPulse` |
| `HudModuleAlertsAndSurveillance` | `AudioSurveillanceAlert`, `AudioSurveillanceBar`, `AudioSurveillanceCompass`, `AudioTextFields` | `UC_SetupTripleTracker(a,b,c)`, `UC_SetTripleTrackerState(5 args)`, `UC_SetInterceptAngle(angle, range)`, `UC_SetForensicTrail`, `UC_SetAudioText`, `UC_SetMovieState` |
| `HudModuleHealth` | `health_inner`, `health_inner_pulse`, `new_actualbar`, ballistic armour, `mAdrenalineBar*`, `mBatmobileTakedownBar`, `mDualCombatBar`, combo counters, `Takedown`, `CriticalStrike`, XP text | `UC_SetHealthLevel`, `UC_SetArmourLevel`, `UC_SetArmourMaxima`, `UC_SetAdrenaline` / `UC_SpendAdrenaline` / `UC_ReduceAdrenaline`, `UC_SetCombo` / `UC_SetComboChallenge`, `UC_SetBatmobileTakedownDisplay`, `UC_SetDualPlayDisplay`, `UC_ShowCritical*`, `UC_ShowPostCombatBreakdown` |
| `HudModuleStoryMode` | `_bar_threat`, `_clip_threat_*`, `WarningMessage`, `WarningMessageOneShot`, `lapCounter`, `mIntelMeter`, command-beacon charge, `ZoomMode_Gizmo_Master`, Explosive Gel | `UC_SetThreatLevel(String, String, Boolean, Boolean)`, `UC_HideThreatMeter`, `UC_SetWarningBar(0…1)`, `UC_SetWarningMessage`, `UC_OneShotWarningMessage`, `UC_SetLapCount`, `UC_ToggleLapCount`, `UC_SetZoomMode`, `UC_SetIntelVisible`, `UC_SetCommandBeaconCharge`, `UC_SetGenericMessage`, `UC_QueueDiscovery` |
| `HudModuleBoss` | `mHealthBar`, `mHealthBarSliderChild`, `FireflyIcon` | `UC_SetBossName`, `UC_SetHealthLevel(value, a, b, c)`, `UC_JustShake` |
| `HudModuleScanner` | scan reticle, timeline, deep-scan markers, case-file view | `UC_SetScanAnimProportion`, `UC_SetScannerPosition`, `UC_SetTimelinePosition`, `UC_SetTimelineHighlight`, `UC_AddTimelineFill`, `UC_ShowTimeline`, `UC_PlayScanAnim`, `UC_SetDeepScanLevel`, `UC_InitDeepScanParams`, `UC_FindDeepScanEvidence` |
| `HudModuleDetectiveMode` | detective-vision overlays, evidence/NPC detail, smoke level, cursor | `UC_SetEvidenceDetail`, `UC_SetNPCInfo`, `UC_SetNPCCount`, `UC_SetScannerDetail`, `UC_SetSmokeLevel`, `UC_SetInfoText`, `UC_UpdateCursorLocation` (+ `UC_Hide*`) |
| `HudModuleDetectiveModeJamming` | jammed / compromised overlay | `UC_SetDetectiveModeJammed`, `UC_SetCompromiseLevel` |
| `HudModuleObjectives` | objective text, arrows, most-wanted bars, side-story completion | `UC_FlushObjective`, `UC_ObjectivesPromptCallback` |
| `HudModuleRoomName` | room/location caption (`RoomName` clip) | **no `UC_*` setter**: `ModuleStruct_RoomName.SetRoomName()` reads the module's own state |
| `HudModuleCrimeSceneInfo` | `CrimeSceneText` caption | **no `UC_*` setter** (only the six shared module calls) |
| `HudModuleSuicideCars` | suicide-car level readout | `UC_SetSuicideCarsLevel` |
| `HudModuleDownloadProgress` | progress bar, messages, intro/outro | `UC_SetProgressLevel`, `UC_SetDisplayMessage`, `UC_ShowIntro/Outro` |
| `RadialGadgetSelect` | gadget wheel, per-character icon sets, charges, prompts | `UC_OpenWheel`, `UC_CloseWheel`, `UC_SelectWheelGadget`, `UC_SendGadgetsToFlash`, `UC_SetGadgetParams`, `UC_SetWheelArrowAngle`, `UC_UpdateSelectedIndex`, `UC_GadgetFailed` |
| `StoryModeHUD` | 122 `CI_*` input-prompt classes and `HUD_I*` icons | prompt requests (`RequestPromptMapping*`) |
| `ModularHudBm3` | container document; module load/unload, tint, visibility, deferral | `UC_GetDeferredExternalCalls`, per-module `LoadModule`/`CreateHudExtension` |

The HUD is therefore **event-driven at the module level**: `UC_SetSelectiveVisibilityModule(name)`
appears in every module and is how battle mode, zoom and per-vehicle layouts add and remove whole
module groups; `UC_ShakeEntireHud` / `UC_ShakeAndFlashHud` are implemented by each module; and the
targets movie reacts to weapon events (`Weapon`, `WeaponHit`, `WeaponFailure`) rather than to a
health value.

### 5.1 Battle-mode and lock-on behaviour, concretely

- **Battle mode** is a Batmobile-module state machine (§4) plus the container's selective
  visibility: `ZoomInterfaceTopBottom`, `battle_mode_topCorner`/`bottomCorner`,
  `battleMode_crosses_group_anim`, `recticuleHeavy` and `battleAndZoomInterfaceMovie` are the
  elements that appear. The on-foot HUD is unaffected — it is a different module.
- **Lock-on / missile boxes** has two independent paths. The vehicle path is
  `HudModuleTargets`: `batmobile_lockon`, `batmobile_aim`, `missile_lockon_square_anim` and the
  `VehicleMissileTarget*` family (plain, bomb, EMP, friend, multi, invalid);
  `ModuleStruct_Targets_TargetMovie` carries `bBatmobileTarget`, so these are the Batmobile's
  target clips. The movie defines no separate incoming-missile class — a box on a vehicle is this
  family. The radar path is `HudModuleBespokeLocalRadar`: `LockonMeter` +
  `lockonAndHealthMeter` + `lockonStatusTextContainer`, driven by `UC_SetLockonValue` and
  `UC_UpdateTargetPosition`. Both can be on screen at once, and the native modules
  (`RHudModuleTargets`, `RHudModuleLocalRadar`) cache different function sets.
- **Threat / intercept** is `HudModuleAlertsAndSurveillance`: the triple tracker
  (`UC_SetupTripleTracker`, `UC_SetTripleTrackerState` with five flags), the intercept angle and
  range (`UC_SetInterceptAngle(angle, range)`), the forensic trail and the audio alert text.
  This is a module-level event stream, not a health-bar event; the movie does not draw an
  incoming missile itself — its classes are the audio/compass alert and the three tracker rows.
- **Boss** is `HudModuleBoss` with a boss name and a health level; `FireflyIcon` is the one
  special case, and `RHudModuleFirefly` is a thin subclass that reuses the same movie.

## 6. JC3's HUD, for comparison

`ui/hud.gfx` came from the patch archive (`patch_win64/game6+288028672`, 386,281 B; base copy
296,631 B) and decompiles to **260 AS3 scripts**, 1280×720, 30 fps. It references nine external
DDS atlases (largest `hud_i46.dds`, 1,044,608 B, 1024×1020).

JC3 ships the vehicle cluster the Batmobile needs:

| feature | JC3 API | constants |
|---|---|---|
| speedometer | `InitPrimaryMeter(type, big_tick, max)`, `SetPrimaryMeterValue`, `SetVehicleInfo`, `SetVehicleType` | `SPEEDO_DEGREES = 250`, `SPEEDO_SMOOTHING_TIME = 0.05`, circular or vertical |
| nitrous | `InitVehicleNitrous(recharge)`, `UpdateVehicleNitrous`, `HideVehicleNitrous` | 0…1, ready sound at 1 |
| vehicle weapons | `InitVehicleWeapons(slot, id, name, …)`, `UpdateVehicleWeapons` | two slots |
| vehicle health | `hud_code/health/*`, `MCI_vehicle` | damage paint/health managers |
| turbo jump | `InitVehicleTurboJump`, `UpdateVehicleTurboJump` | 0…1 |
| vehicle types | `SetVehicleType` | land / airplane / helicopter / sea |

Translation disposition for the Batmobile's cluster (T-6 rows):

| BmAK element | JC3 host | disposition |
|---|---|---|
| speed | `MCI_speedo` circular meter | **reuse** — no module movie implements a speedometer (see §8) |
| boost gauge 0…100 + upgrades | `MCI_nitro_meter` nitrous recharge | **map**: `recharge = level / 100`; badges have no equivalent |
| vehicle health + armour | vehicle health paint/bar | **map** health 0…1; armour >1 has no JC3 equivalent |
| cannon cooldown / reticle | vehicle weapon slot + `MCI_speedo` | **partial**: the HUD supports it, the entity has no weapon component |
| battle mode / zoom overlay | none | **out** |
| winch meter | none | **out** |
| energy system (charges) | none | **out** |
| combo / medals / clock / enemy count | none | **out** |
| occupants / virus upload / forensic tracking | none | **out** — story gadgets |
| radar, target lock-on, missile boxes, alerts, threat meter, boss bar | none | **out** — these are Batman-specific modules and have no JC3 API |

**Fourteen of the fifteen movie-bound modules have no JC3 host at all.** They are still grabbed,
because the question "what does the Batmobile HUD show" is not the same as "what can JC3 draw";
conflating the two is what let the first pass call a two-movie carve "the HUD".

## 7. Verification

- `bmak_hud_inventory.py check`: 25 native modules and their movie bindings unchanged, 19 carved
  movies byte-identical to the game, 61 SwfMovie census unchanged, gaps listed.
- `bmak_hud.py check`: the two legacy movies re-read, size + SHA-256 equal.
- `hud_spec.py --check`: 99 BmAK scripts, 260 JC3 scripts, constants and the health contract.
- `bmak_hud_inventory.py interface`: 252 `UC_*` setters across 19 movies; Boss bound 2/2 by
  interface evidence; 10 classes without a movie reported.
- `bmak_speedometer.py --check`: 19 movies / 252 setters with no speed input, `SpeedMin`/`SpeedMax`
  classified as `FrameLabel` tags, `bDebugSpeedometer` false in both configs, one script reference
  (`RDebugMenuContent.DoGadgetsMenu`), native `DrawHUD` 39 B, seven vehicle fields at their offsets.
- ffdec exported every carved movie without an error (19/19).
- **Not verified:** nothing was loaded into either game. `ui/hud.gfx` was read, not replaced; the
  Batmobile movies were never mounted.

## 8. Open questions

- **Where is the speedometer?** It is not a HUD movie. The install's only speedometer is the
  **native debug readout** gated by `RPlayerController.bDebugSpeedometer`, off in both configs and
  drawn through `RPlayerControllerBase.DrawHUD`; the debug menu item is
  `RDebugMenuContent.DoGadgetsMenu` → "Speedometer". `SPEEDOMETER.md` documents the class, the draw
  path and the fields that feed the number, and `bmak_speedometer.py --check` re-derives it. The
  only speed tokens in the movies are `SpeedMin`/`SpeedMax` **FrameLabels** in
  `HudModuleHealth.Image` — animation labels, not a gauge. If a speedometer is visible in normal
  play, that is the open question: this install says it is neither a shipped UI asset nor the
  (off) debug flag.
- **Which movie does `RHudModuleGadgetSelect` use?** `RadialGadgetSelect.Image` is the obvious
  candidate (a gadget wheel with `UC_OpenWheel`/`UC_SelectWheelGadget`), but the class caches no
  function names, so the inventory lists it as unclaimed rather than asserting the pairing.
- **Are the unmapped modules dead?** `ExtraSequence`, `ChallengeMode`, `HackingMode`,
  `ForensicBeaconTracking` and `PerformanceTest` cache function names no movie defines. Either
  their movies are cut from this install, or the calls no-op. Their existence is recorded; nothing
  is claimed about runtime.
- **Can JC3's HUD API be called from a mod?** `InitVehicleNitrous`/`UpdateVehicleNitrous` are the
  natural host, but the caller is game code, not the entity graph. This needs a script hook or a
  `ui/hud.gfx` patch, neither attempted.

## 9. Reproduce

```bash
python Tools/scripts/bmak_hud_inventory.py roster      # 25 classes -> movies
python Tools/scripts/bmak_hud_inventory.py build       # carve 19 movies -> HUD_INVENTORY.json
python Tools/scripts/bmak_hud_inventory.py decompile   # ffdec -> scripts
python Tools/scripts/bmak_hud_inventory.py interface   # 252 setters -> HUD_INTERFACES.json
python Tools/scripts/bmak_hud_inventory.py check       # roster + bytes + gaps
python Tools/scripts/bmak_hud.py check                 # the two legacy movies
python Tools/scripts/hud_spec.py --check \
    --bmak E:/Modding/_BmAK_grab/hud/dec \
    --jc3 E:/Modding/_JC3grab/hud/dec     # needs movie.xml for the Armour0..4 labels
```
