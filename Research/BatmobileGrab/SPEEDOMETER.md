# The Batmobile speedometer: a native debug readout, not a HUD movie

**Verdict.** Batman: Arkham Knight ships **no Scaleform speedometer**. The only thing in the
install named a speedometer is `RPlayerController.bDebugSpeedometer`, a `BoolProperty` exposed as
the **"Speedometer"** item in the developer debug menu (`RDebugMenuContent.DoGadgetsMenu`). It is
**off** in both configs (`BmGame.ini:6303`, `DefaultGame.ini:989`) and it is drawn by **native
code** through `RPlayerControllerBase.DrawHUD`, the 39-byte, bytecode-less base function that
`RPlayerController.DrawHUD` calls. No `RHudModule*` touches it.

Checkable: `Tools/scripts/bmak_speedometer.py --check` (record `SPEEDOMETER.json`).

## 1. Why it cannot be a HUD movie

- The 19 carved HUD movies define **252 `UC_*` setters** (149 distinct names); none names
  speed, revs, gear or a dial. `HUD_INTERFACES.json` is the whole set.
- Inflating all **19** movies and scanning the tag streams for `speed*` finds exactly two tokens:
  `SpeedMin` and `SpeedMax` in `HudModuleHealth.Image`. FFDec's tag dump shows both are
  **`FrameLabel`** tags (tag id 43), i.e. animation labels, not text fields and not a gauge:

  ```
  00012e46:  0. FrameLabel (name: "SpeedMin") tagId= 43 len= 9  53 70 65 65 64 4d 69 6e 00
  000133a0: 57. FrameLabel (name: "SpeedMax") tagId= 43 len= 9  53 70 65 65 64 4d 61 78 00
  ```

- The native hooks that *look* like a speedometer are orphans:
  `RHudModuleExtraSequence.SetSpeedBar(Speed:FloatProperty)` has `CachedFunction_SetSpeedBar`,
  but `RHudModuleExtraSequence` has **no movie** in this install and no movie defines
  `UC_SetSpeedBar`; `RHudModuleLocalRadar.SetBatmobileRevDisplayActive` has no counterpart in
  `HudModuleBespokeLocalRadar` either.

## 2. The native path that does exist

| layer | object | evidence |
|---|---|---|
| flag | `BmGame.RPlayerController:bDebugSpeedometer` | `BoolProperty` on the player controller |
| config | `bDebugSpeedometer=False` | `BmGame.ini:6303`, `DefaultGame.ini:989` |
| toggle | `RDebugMenuContent.DoGadgetsMenu` | the only function whose bytecode references the property; its string pool contains the menu label `Speedometer` |
| script draw | `RPlayerController.DrawHUD` (656 B) | calls `RPlayerControllerBase.DrawHUD` |
| native draw | `RPlayerControllerBase.DrawHUD` (39 B) | bytecode-less export: the native thunk that paints the canvas HUD |
| canvas | `RPlayerController.PreRender` | owns the `Canvas` variable the HUD draws through |

So the class that draws the number is **`RPlayerController`**, through its native base
`RPlayerControllerBase.DrawHUD`; `PreRender` is the per-frame canvas context. Nothing here is
Scaleform; the paint is a native thunk, which is exactly why a movie inventory could not find it.

## 3. The fields that supply the number

`RVehicle` exposes **no scalar speed property** (checked across `RVehicle*.g.cs`: only thresholds
and multipliers). The magnitude a native readout reads is therefore the actor's velocity vector,
`Engine.Actor.Velocity`, taken on the player's vehicle; the Batmobile adds the artificial-speed
fields below. Values are class defaults read from `Default__RVehicleBatmobileBase` at the BmSDK offsets.

| class | field | type | offset | default | role |
|---|---|---|---:|---:|---|
| `RVehicleBatmobileBase` | `CurrentThrottle` | float | 6408 | *absent* (0) | current throttle |
| `RVehicleBatmobileBase` | `ThrottleSpeed` | float | 6412 | **2.0** | throttle → speed |
| `RVehicleBatmobileBase` | `FakeExtraSpeed` | float | 7152 | *absent* (0) | boost's artificial speed, live |
| `RVehicleBatmobileBase` | `FakeExtraSpeedMax` | float | 7156 | **3500.0** | ceiling of the artificial speed |
| `RVehicleBatmobileBase` | `FakeExtaSpeedAccel` | float | 7160 | **600.0** | how fast it ramps |
| `RVehicleBatmobileBase` | `FakeExtaSpeedDecel` | float | 7164 | **2000.0** | how fast it bleeds |
| `RVehicleBatmobileBase` | `BattleModeSpeedDelta` | float | 7860 | *absent* (0) | battle-mode speed offset |
| `Engine.Actor` | `Velocity` | `StructProperty` (FVector) | — | live | the measured magnitude |

The last row is the one field not in `RVehicleBatmobileBase.g.cs`: it is verified directly in
`Engine.upk` as export `Actor.Velocity` of class `StructProperty` (an FVector), and it is the only
live speed reading in the table. The `RVehicle` dump has no scalar `Speed` property at all — only the
thresholds and multipliers above, plus damage/turn-speed tuning.

`3500` is in Unreal units (cm/s): **126 km/h**. The debug readout's conversion and units are
inside the native function and are **not claimed** here; the table is the input side only.

## 4. What this means

- The earlier HUD record's "the movie has no speedometer, AK draws it elsewhere" is now
  substantiated and sharpened: the elsewhere is **one disabled debug flag**, not a retail gauge.
- If a speedometer is visible in normal play, this install's data says it is not a shipped UI
  asset and not `bDebugSpeedometer` (off). The next check is empirical: enable the debug menu's
  `Speedometer` item and compare the readout, or capture the frame and identify which of the
  elements above it tracks. The packages hold no retail speedometer asset to search for by name —
  only this debug property.
- For the JC3 translation the decision does not change: JC3's `MCI_speedo` remains the display
  (T-HUD1), and the Batmobile's `Velocity`/`FakeExtraSpeed` values are what a future caller would
  feed it.

## 5. Reproduce

```bash
python Tools/scripts/bmak_speedometer.py --write   # -> SPEEDOMETER.json
python Tools/scripts/bmak_speedometer.py --check   # re-derive movies, config, refs, fields
java -jar E:/Modding/_shared/tools/ffdec/ffdec.jar -dumpSWF \
     E:/Modding/_BmAK_grab/hud/modules/HudModuleHealth/movie.gfx | grep -n Speed
```
