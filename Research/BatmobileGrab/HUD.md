# Batmobile HUD and camera — grab, decompile, translation

The G1/G2 grab opened `Playable_Batmobile_SF.upk` (mesh, materials, textures, audio) and the native
class layout. It did **not** contain the HUD: `Playable_Batmobile_SF.upk` has no `SwfMovie`, and
`ls CookedPCConsole | grep -i hud` finds nothing, because the HUD ships as **sub-packages inside**
`BmGame.upk` and `Startup.upk`, not as files of their own.

This pass found, carved and **decompiled** both HUD movies, and decoded the camera class that drives
the Batmobile. Re-runnable: `bmak_hud.py build|check`, `hud_spec.py`, `bmak_camera.py`.

## 1. What was grabbed

| package | object | serialized | payload | inflated | sha256 |
|---|---|---:|---:|---:|---|
| `BmGame.upk` | `HudModuleBatmobile.Image` (SwfMovie) | 423,138 B | 423,056 B | 671,744 B | `2a5d0be143bd…` |
| `Startup.upk` | `StoryModeHUD.HUD` (SwfMovie) | 23,872 B | 23,758 B | 60,077 B | `1ceedb619922…` |

- `HudModuleBatmobile.Image` is the **Batmobile HUD module** — the in-vehicle overlay.
- `StoryModeHUD.HUD` is the **shared prompt HUD** (122 `CI_*` input-prompt classes plus the `HUD_I*`
  icon textures it draws). It is not Batmobile-specific.
- Both are CFX containers: `u32 length`, `CFX` magic, version `0x0f`, an 8-byte header, then a zlib
  stream of GFx tags. `bmak_hud.py` carves `RawData` directly because umodel cannot address the
  dotted object path (`HudModuleBatmobile.Image`); the inflated streams live outside the repo in
  `_BmAK_grab/hud/`.

Four HUD textures belong to the Batmobile module and were exported with umodel:

| texture | DDS | note |
|---|---:|---|
| `HudModuleBatmobile.Image_I1` | 3,025,248 B | main atlas, streamed from `.tfc` |
| `HudModuleBatmobile.Image_I1B` | 2,368 B | small element |
| `HudModuleBatmobile.Image_I1C6` | 65,664 B | element |
| `HudModuleBatmobile.Image_I28B` | 1,152 B | element |

## 2. The movie is now decompiled

`ffdec` (JPEXS Free Flash Decompiler 26.4.0) reads the CFX container directly:

```
java -jar ffdec.jar -export script <out> HudModuleBatmobile.gfx
java -jar ffdec.jar -swf2xml <out>/movie.xml HudModuleBatmobile.gfx
java -jar ffdec.jar -dumpSWF HudModuleBatmobile.gfx > <out>/tags.txt
```

**99 ActionScript 3 scripts**, 51 frames, 30 fps, 1024×768 SWF surface. The stage class declares
1024×720; `ModularHudBm3.TickDeltaTime` is `0.033` (30 Hz). The document class is `ModularHudBm3`
(`rs.document.GFxDocument`); the Batmobile module is `ModuleStruct_Batmobile`.

The main timeline labels that matter:

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
| clock | `Initial`, `Pause`, `Resume`, `Expired`, `ExpiredOutro` (bonus/penalty are sprite animations, not labels) |

`hud_spec.py` extracts the whole list into `HUD_SPEC.json`.

## 3. The state machine

`ModuleStruct_Batmobile.SetBattleAndZoomMode(battle, zoomed)` is the mode machine:

```text
DRIVE  --battle------------> BATTLE
DRIVE  --zoomed------------> ZOOMED (implies battle)
BATTLE --zoomed------------> ZOOMED
BATTLE --battle off--------> DRIVE
ZOOMED --zoomed off--------> BATTLE
ZOOMED --battle off--------> DRIVE
```

It calls `BattleAndZoomInterface.gotoAndPlay(<from>TO<to>)`, sets the interface visible outside DRIVE,
and keeps the heavy reticle at alpha 1 when leaving DRIVE. Entering battle forces the health bar
visible with the `Delayed` intro; leaving it hides the health bar only when health is full and XP has
settled.

`BattleModeOpacity` is a separate setter (`UC_SetBattleModeOpacity`) — the overlay is dimmed, not a
second screen.

## 4. The data contract

The script module (`RHudModuleBatmobile`, 66 properties / 52 functions) drives the movie through the
`UC_*` functions. **31 public setters** were extracted; the ones with real state are:

| setter | arguments | what it drives |
|---|---|---|
| `UC_SetHealth` | `health, max` | health 0…1, armour above 1, `Armour<n>` background, 2 s offscreen timer |
| `UC_SetHealthBarVisible` | `visible, introSuffix` | `Intro`/`Outro`, `Delayed` variant |
| `UC_SetXpLevel` | `proportion, instant` | XP bar, `XPFill` |
| `UC_SetBoostLevel` | `0…100, upgradeLevel` | boost gauge frames, upgrade badges, charging/decreasing states |
| `UC_SetEnergySystemParams` | `charges, max, proportion, instant, state` | `Charges<n>`, fill/target frames, hit/depleting animations |
| `UC_SetCannonCoolDown` | `0…4` | reticle `Ready` / `Blank` / `PreReady*` |
| `UC_SetSpecialWeapons` | `3 × state` | `Unavailable` / `Available` / `Used` / `Lost` |
| `UC_SetWinchMeter` | `coneAngle, needleAngle, onTarget` | winch cone and needle rotation |
| `UC_SetTurnAround` | `direction` | turn-back symbol, mirrored by sign |
| `UC_SetOccupant` | `visible, name, icon, …` | passenger HUD |
| `UC_SetBatmobileCombo` | `proportion, count, seconds` | combo meter |
| `UC_SetBattleAndZoomMode` | `battle, zoomed` | the mode machine |
| `UC_SetImpactDamageFlash` | `part, amount, duration, frames` | hit flash |
| `UC_SetVirusUploadState` | `state, warning` | virus upload widget |
| `UC_SetForensicTracking` | `text` | forensic tracking readout |
| `UC_SetEnemyCount` / `UC_SetMedal*` | counts | challenge HUD |

The script side resolves each setter by name (`CachedFunction_Set*`), which is why the movie's `UC_*`
names can differ from the module's `Set*` names.

**Numbers that are in the movie, not in the class dump:**

| constant | value |
|---|---|
| `TickDeltaTime` | 0.033 s (30 Hz) |
| `MaxHealthChangePerFrame` | 0.05 of full health per frame |
| health pulse threshold | `< 0.2` |
| health bar offscreen timer | 2 s |
| energy gauge max step | 0.02 per frame |
| boost range | 0…100 (hide at 100 when not held) |
| perspective projection FOV | 56° |
| projection center | (512, 384) on a 1024×768 surface |
| stage | 1024×720 |

## 5. JC3's HUD, for comparison

`ui/hud.gfx` was extracted from the **patch** archive (`patch_win64/game6+288028672`, 386,281 B;
base copy 296,631 B) and decompiled the same way: **260 ActionScript 3 scripts**, 1280×720, 30 fps.
The movie references **nine external DDS atlases**, all extracted from the patch copy:

| atlas | bytes | size |
|---|---:|---|
| `hud_i46.dds` | 1,044,608 | 1024×1020 |
| `hud_i60.dds` | 1,044,608 | 1024×1020 |
| `hud_i5a.dds` | 1,040,512 | 1024×1016 |
| `hud_iee.dds` | 1,040,512 | 1024×1016 |
| `hud_i1bf.dds` | 1,032,368 | 1020×1012 |
| `hud_i32.dds` | 1,028,224 | 1024×1004 |
| `hud_i126.dds` | 397,440 | 1024×388 |
| `hud_i6b7.dds` | 16,512 | 128×128 |
| `hud_i6ba.dds` | 16,512 | 128×128 |

JC3 already ships the vehicle cluster the Batmobile needs:

| feature | JC3 API | constants |
|---|---|---|
| speedometer | `InitPrimaryMeter(type, big_tick, max)`, `SetPrimaryMeterValue(value)`, `SetVehicleInfo`, `SetVehicleType` | `SPEEDO_DEGREES = 250`, `SPEEDO_SMOOTHING_TIME = 0.05`, circular **or** vertical |
| nitrous | `InitVehicleNitrous(recharge)`, `UpdateVehicleNitrous(recharge)`, `HideVehicleNitrous` | 0…1 recharge, ready sound at 1 |
| vehicle weapons | `InitVehicleWeapons(slot, id, name, …)`, `UpdateVehicleWeapons(…)` | two slots (`EVEHICLE_WEAPON_SLOT_MAIN/ALTERNATIVE`) |
| vehicle health | `hud_code/health/*`, `MCI_vehicle` | damage paint/health managers |
| turbo jump | `InitVehicleTurboJump`, `UpdateVehicleTurboJump` | 0…1 |
| vehicle types | `SetVehicleType` | land / airplane / helicopter / sea |

That changes the HUD translation from "build a HUD" to "bind the existing JC3 cluster":

| BmAK element | JC3 host | disposition |
|---|---|---|
| speed | `MCI_speedo` circular meter | **reuse** — BmAK's movie has no speedometer of its own |
| boost gauge 0…100 + upgrades | `MCI_nitro_meter` nitrous recharge | **map**: `recharge = level / 100`; upgrade badges have no JC3 equivalent |
| health + armour | vehicle health paint/bar | **map** health 0…1; armour >1 has no JC3 equivalent |
| cannon cooldown / reticle | vehicle weapon slot + `MCI_speedo` | **partial**: JC3 has armed vehicles; the Batmobile mod has no weapon component yet |
| battle mode / zoom overlay | none | **out** — no battle mode or zoom in JC3 |
| winch meter | none | **out** — no vehicle winch |
| energy system (charges) | none | **out** — no Batmobile energy charges |
| combo / medals / clock / enemy count | none (challenge HUD) | **out** — challenge-only |
| occupants | none | **out** — JC3 cars have no passenger HUD |
| virus upload / forensic tracking | none | **out** — story gadgets |

## 6. Verification

- `bmak_hud.py check`: both movies re-read from the game, size + SHA-256 equal.
- `hud_spec.py --check`: 99 BmAK scripts, 260 JC3 scripts, the constants above.
- ffdec exported 99/99 BmAK scripts and 260/260 JC3 scripts without an error.
- The movie's identifiers and frame labels are in `HUD_SPEC.json`; the decompiled scripts stay
  outside the repository (`_BmAK_grab/hud/dec`, `_JC3grab/hud/dec`).
- **Not verified:** nothing was loaded into either game. JC3's `ui/hud.gfx` was read, not replaced.

## 7. Reproduce

```bash
python Tools/scripts/bmak_hud.py build          # carve both movies -> HUD.json
python Tools/scripts/bmak_hud.py check          # re-read the game, compare size/hash
# ffdec -> scripts, tags.txt, movie.xml (see §2)
python Tools/scripts/hud_spec.py --bmak E:/Modding/_BmAK_grab/hud/dec \
       --jc3 E:/Modding/_JC3grab/hud/dec --write
```

## 8. Open questions

- **Which frames are used at runtime?** The labels prove the graph; the transition timings are in
  the movie, not the module.
- **Can JC3's HUD API be called from a mod?** `InitVehicleNitrous`/`UpdateVehicleNitrous` are the
  natural host, but the caller is game code, not the entity graph. This needs a script hook or a
  `ui/hud.gfx` patch, which has not been attempted.
- **The Batmobile's own speedometer** is absent from the movie on purpose — Arkham Knight draws speed
  in the cockpit/other HUD, so JC3's speedometer is the only one to reuse.
