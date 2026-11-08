# G3-HUD-RADAR - BmAK local radar decoded

STATUS: done for what the movie's own bytes carry; several sections are UNKNOWN **with a route**, and
no row was closed as "JC3 cannot". The radar's selector/animation contract is decoded: stage size,
the 15 `UC_*` setters, the arrow rotation, the 80 px/unit mapping, the player-up rotation, and the
fact that the two "kind" parameters are **not** kinds (one is a dot count, one an urgency threshold).

## What was produced

| file | what |
|---|---|
| `Tools/scripts/bmak_radar.py` | `--write` / `--check` / `--tamper`; carves the movie, reads the ffdec export, rebuilds `RADAR.md` byte for byte |
| `Working/HUD/RADAR.md` | 133 lines: the 7 requested sections + row-by-row table + compromises |
| `Working/HUD/RADAR.json` | every decoded fact as JSON (stage, setters with AS3 line numbers, probes, leads) |
| `Working/HUD/radar.gfx` | the carved CFX payload (66,317 B, sha256 `f9f622d5a068919e…` - same pin as `HUD.md`) |
| `Working/HUD/radar/radar_inflated.bin` | the inflated tag stream (139,264 B) |
| `Working/HUD/radar/_ffdec2/` | ffdec `-export all` of the .gfx: **58** scripts, **113** sprites, `shapes/*.svg`, `images/*.png`, `frames/*.png`, `symbolClass/symbols.csv` |

`Research/BatmobileGrab/HUD.md` and `Working/Translation/T6_HUD_CAMERA.md` were **not** edited.

## Decoded (with the evidence)

1. **Layout**: stage **1024x720 px @ 30 fps**, from the movie's own
   `[SWF(width="1024", height="720", frameRate="30")]` metadata (AS3 line 8). The module's clips, per
   `symbolClass/symbols.csv`: `RadarMovie`, `warning_alert`, `lockonAndHealthMeter`,
   `lockonStatusTextContainer`, `LockonMeter`, `HeavyTankRadiusMovie`, `MapBackground`,
   `MapPulseTimer` (plus `MasterMovie`). **Per-clip placement is UNKNOWN**: ffdec `-export all` emits
   `frames/*.png` and `sprites/`, not `PlaceObject` matrices, so "bottom-right" cannot be stated in
   stage pixels from this export; the route is a `PlaceObject2` walk of the `DefineSprite` tags in
   `radar.gfx`, or `ffdec -export frame`.
2. **Icon carriers**: 113 `DefineSprite`s, 16 symbolClass entries, plus the separate classes
   `HeavyTankElement` and `trackingVehiclePathDot`. Icon choice is a **frame table**:
   `gotoAndStop(<frame>)` on `Master.Radar.Target.Element` and one frame per heavy tank
   (`HTD_MovieFrame`), with `-10000` meaning "keep the previous frame" (decoded, AS3 line 164 block).
   The frame→art mapping is symbol content and stays UNKNOWN; no per-icon PNG was generated for that
   reason (the drawable art itself *is* exported by ffdec under `shapes/`, `images/`, `sprites/`).
3. **Facing arrow**: `UC_UpdateTargetPosition(angle, distance, bearing, int)` sets
   `x = 80*d*sin(a)`, `y = -80*d*cos(a)`, `rotation = bearing*57.3`. So a blip is a rotating clip -
   the operator's "icons are pointers" lead is **CONFIRMED**.
4. **The 4th argument is not a kind**: it is passed to `Private_VehicleTracker(param1)`, which sets
   `NumTrackingDots` and positions that many `trackingVehiclePathDot` children. `UC_SetLockonValue`'s
   second argument is an urgency threshold (`value > threshold` → `State1`, else `State2`).
5. **Player-up map**: `UC_SetPlayerPosition(angle, x, z)` sets `RootNetwork.rotation = angle*57.3`
   and places the root from `hypot(x, z)` and `atan2(-x, z) - angle` - a **2-D x,z** map, no altitude.
6. **Scale**: **80 px per distance unit** (decoded constant); world radius in metres **UNKNOWN** (the
   native side owns the divisor). Standalone debug build divides the pixel radius by 400.
7. **No vehicle-type / colour / elevation switch exists in this script**: 0 matches for `kind`,
   `elevation`, `helicopter`, `police`, `military`, `hack`, `red`, `green`, `colour`.

## Operator leads (verdicts)

| lead | verdict | evidence |
|---|---|---|
| arrows pointing where the vehicle faces | **CONFIRMED** | clip `rotation = bearing*57.3` |
| tanks have bigger arrows | **CONFIRMED carrier, size UNKNOWN** | `HeavyTankElement` (DefineSprite_116) + `HeavyTankRadiusMovie` |
| helicopter has its own icon | **UNKNOWN** | 0 `helicopter` matches; route = frame table / symbol art |
| cops have their own icon | **UNKNOWN** | 0 `police` matches |
| tracked vehicles: own green icon | **UNKNOWN** | 0 `green`; only `trackingVehiclePathDot` path dots |
| military vehicles: own icon | **UNKNOWN** | 0 `military` matches |
| hacked: red → green | **UNKNOWN** | 0 `hack`/`red`/`green`; colour is symbol content |
| icons vary with elevation | **UNKNOWN** | no altitude input in either setter; route = native `RHudModuleLocalRadar` callers |

## JC3 host routes (none implemented, none claimed to work)

- **(a) reuse the BmAK SWF in JC3's `ui/hud.gfx` pipeline** - derived: both are Scaleform, but the
  module needs BmAK's `ModuleStruct`/`ModularHudBm3` loader and the native `RHudModuleLocalRadar`
  setters. 5-minute experiment: pack the 139,264 B movie as an extra JC3 gfx and load it; one frame
  of output means the loader contract is the only blocker.
- **(b) JC3 custom blip / minimap element** - derived-UNKNOWN: JC3's minimap is AS3 in `hud.gfx` with
  a `POI_*` set, but a *rotating* per-vehicle arrow is not decoded. 5-minute experiment: read the
  minimap script's blip-add call for a rotation field.
- **(c) JC3 world-space marker object** - UNKNOWN; route: grep `Research/JC3Grab` for a HUD-icon
  component type.

## COMPROMISES (recommendations only - the operator approves, not this agent)

1. **Flat minimap instead of a rotating pointer radar.**
   RECOMMENDED COMPROMISE: use JC3 minimap blips for vehicle positions and omit per-target heading
   arrows until route (a) or (b) is proven. Why: no JC3 member that rotates a blip by bearing is
   decoded. Accuracy lost: the player cannot read a target's heading - most of what this radar is for.
2. **No elevation cue.**
   RECOMMENDED COMPROMISE: show no altitude (or a tint by height) until the native caller is read.
   Why: the module script has no altitude input at all. Accuracy lost: air targets read as ground.
3. **No heavy-tank radius ring.**
   RECOMMENDED COMPROMISE: skip `HeavyTankRadiusMovie` until its frame table is decoded. Why: the
   ring is art-driven. Accuracy lost: the heavy-tank danger radius is not shown.

## Commands and output (verbatim, final run)

```
$ uv run python Tools/scripts/bmak_radar.py --write; echo "WRITE_EXIT=$?"
wrote Working\HUD\RADAR.md and RADAR.json (133 lines)
stage 1024x720 @ 30 fps; 58 scripts, 113 sprites, 15 UC_ setters, 80 px/unit
WRITE_EXIT=0

$ uv run python Tools/scripts/bmak_radar.py --check; echo "CHECK_EXIT=$?"
PASS movie size 66317 / 139264 B
PASS movie sha256 f9f622d5a068 matches the HUD.md pin f9f622d5a068
PASS stage 1024x720 @ 30 fps
PASS 15 UC_ setters decoded from the AS3
PASS the 4th argument of UC_UpdateTargetPosition feeds NumTrackingDots, not a kind
PASS 80 px per distance unit
PASS no kind/elevation identifiers in the module script (kind=0, elevation=0)
PASS Working\HUD\RADAR.md exists
PASS Working\HUD\RADAR.json exists
PASS RADAR.md re-derives byte for byte from the carved movie + AS3 export
PASS: G3-HUD-RADAR 0 failure(s)
CHECK_EXIT=0

$ uv run python Tools/scripts/bmak_radar.py --tamper; echo "TAMPER_EXIT=$?"
tampered byte at 10045: b'8' -> b'9'; recomputed px/unit = 90 (clean file: 80)
PASS tamper detected
TAMPER_EXIT=0
```

Carve + export commands used to produce the AS3 the script reads:

```
$ uv run python -c "import bmak_hud; raw,data=bmak_hud.carve('BmGame.upk','HudModuleBespokeLocalRadar.Image')"
packed 66317 inflated 139264 sha256 337a91f5810eb550 magic b'CFX'
$ ffdec-cli.exe -onerror ignore -export all Working/HUD/radar/_ffdec2 Working/HUD/radar/radar.gfx
Export finished. Total export time: 01:01.810 / OK   (58 scripts, 2888 files)
```

## UNKNOWNs (each with the route, none closed as "JC3 cannot")

1. **Per-clip placement / "bottom-right" in stage pixels** - ffdec's `-export all` carries no
   matrices; route: `PlaceObject2` walk of `radar.gfx`, or `ModularHudBm3`'s stage in the container
   movie.
2. **Frame → icon art table** (which frame is a tank / cop / helicopter / red / green) - the AS3 only
   passes frame numbers; route: the `DefineSprite` frame lists in the ffdec export.
3. **Elevation mechanism** - not in this movie; route: `RHudModuleLocalRadar` function bodies in
   `BmGame.upk` (`upk_read.py`) and `CLASS_DEFAULTS.json` for its constants.
4. **World radius in metres, `MapPulseTimer` period, distance fade, off-range clamping** - route:
   `scripts/HudModuleBespoke_LocalRadar_fla/MapPulseTimer_21.as` + the native defaults.
5. **Native kind mapping (which actor class sends which value)** - the module has no kind switch, so
   the question moves to the native callers; not decoded here.
6. **Per-icon PNG renders** - not produced: the art is exported (`shapes/*.svg`, `images/*.png`,
   `sprites/`) but the frame table that assigns art to icons is UNKNOWN, so per-icon files would be
   guesses.
