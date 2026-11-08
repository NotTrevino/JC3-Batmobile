# Lock markers: the BmAK shapes, colours and circle-shrink timeline, and the overlay spec

2026-11-08. Operator fact: **battle mode** shows an orange diamond that appears instantly;
**pursuit mode** shows a diamond with the centres of its edges missing, plus a circle that appears
large and shrinks as the lock completes, so pursuit has a visible lock time. Question: export both
markers' shapes, colours and animation frames from the BmAK HUD movies, then write the drawing spec
the hook overlay (brief 7985) can implement directly.

**Answer in one paragraph.** The markers are in `HudModuleTargets`, not in the `ui/hud.gfx`
container: FFDec's export of the carved movie is in `E:/Modding/_BmAKgrab/hud/lock/` (movie, 520
shapes, 520 sprite timelines, AS3), and the numbers are in `MEASUREMENTS.md` beside it. The diamond
is `missile_lockon_square_anim_591`: stroke `#FF6600`, alpha 0.91, 57-58 px across a 81 px tile, a
20-frame spin that stops on frame 20. The lock circle is `VehicleVariableTargetLockon_580`: a
16-frame clip whose outer ring pops in at radius 58 px and closes to 31 px by frame 13 inside a
158 px tile, drawn `#FF6600` at alpha 0.42 over a constant inner box ring at radius 16-25 px.
`MissileLockOnDuration` (default **2.0 s**, `0x0A00`, WEAPONS.md:839) is the wall-clock lock time
and the baked ring is only 16 frames, so the ring is **frame-stepped by the lock fraction**, not
played: `SetLockonProportion(p)` = `gotoAndStop(1 + p * (totalFrames - 1))`
(`ModuleStruct_Targets_TargetMovie.as`). The markers are placed in **normalised viewport
coordinates** (`x = PositionX * ViewportWidth`, `y = PositionY * StageHeight`) with a separate
`ScreenSize` scale, so the overlay needs a projection and a size from the hook, not from the movie.
One operator fact does **not** reproduce from the data: the edge-centre gaps of the pursuit diamond.
None of the three lock clips has a gap (measured coverage is continuous), so the gaps are authored
from the operator's description.

Labels: **decoded** = read in the file cited; **derived** = arithmetic on decoded values;
**authored** = our choice, not in BmAK.

## 1. Where the markers were found, and what got exported

| item | value | source |
|---|---|---|
| movie | `HudModuleTargets` HUD module (carved `HudModuleTargets.gfx`, 252,938 B) | `E:/Modding/_BmAKgrab/hud/lock/HudModuleTargets.gfx` |
| export | 520 vector shapes, 520 sprite timelines, 153 `HudModuleTargets_fla` classes | `export/shapes/`, `export/sprites/`, `scripts/`, same folder |
| the two clashing paths | vehicle path `HudModuleTargets` (`batmobile_lockon`, `missile_lockon_square_anim`, `VehicleMissileTarget*`); radar path `HudModuleBespokeLocalRadar` (`LockonMeter`, `UC_SetLockonValue`) | `Research/BatmobileGrab/HUD.md` 248-255 |
| frame rate | **30 fps** - `ModularHudBm3.TickDeltaTime` is `0.033`; the container is `1280x720, 30 fps` | `Research/BatmobileGrab/HUD.md` 125, 268 |
| lock time member | `RBatmobileEMPMissile.MissileLockOnDuration` at `0x0A00`, FloatProperty, default **2.0**; civilian variant `0x0A04` = 1.0 | `Research/BatmobileGrab/WEAPONS.md` 839-840 |

`decoded`. Clips measured (all in `E:/Modding/_BmAKgrab/hud/lock/export/sprites/`):

| clip | frames | tile | role in the operator's description |
|---|---|---|---|
| `missile_lockon_square_anim_591` | 20, stop on 20 | 81x81 | the orange diamond |
| `VehicleVariableTargetLockon_580` | 16, stop on 16 | 158x158 | the circle that appears large and shrinks |
| `batmobile_lockon_277` | 16, stop on 16 | 55x51 | the red locked flash over a batmobile target |
| `VehicleMissileTarget_588` (+ `_bomb` 551, `_emp` 567, `_friend` 570, `_multi` 590, `Invalid` 593) | 124 / 16 / 10 | 608x608 | the red target box, scaled per target |
| `missile_border_anim_499` | 12 | 57x57 | orange border pulse |

The battle/pursuit split of these clips (which label frame of the cursor each mode draws) is
**UNKNOWN** - see §6.

## 2. The diamond - shape and colour (`missile_lockon_square_anim_591`, decoded)

Tile 81x81, transparent background, opaque bbox:

| frame | 1 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|
| bbox | 57x57 | 55x55 | 43x43 | 53x53 | 58x57 |

Constant stroke with an oscillating bbox = a square outline spinning through 45 deg and back, then
`stop()`. 20 frames at 30 fps = **0.667 s** per cycle, 0.333 s per half turn.

| property | value |
|---|---|
| stroke colour | `#FF6600` = (255, 102, 0) |
| stroke alpha | 232/255 = **0.91** (edges anti-aliased to 55/255) |
| stroke width | about 2 px across a 57 px diamond = **0.035 x across** (derived from the row profile: 5 opaque px through a 45-deg edge) |
| fill | none |

No gap: the angular coverage of frame 1 in 10-deg bins has **no empty bin** (min 4 px), so this
graphic is a continuous outline. The operator's "centres of its edges missing" is therefore not in
this clip (§5).

## 3. The circle - the shrink timeline (`VehicleVariableTargetLockon_580`, decoded)

Tile 158x158, transparent, centre (77, 78). Radius histogram (px bins with >= 6 pixels):

| frame | inner ring | outer (lock) ring |
|---|---|---|
| 1 | 16-25 | 16-25, partial arc (bbox 36x38) |
| 2 | 16-25 | **55-58** |
| 4 | 17-24 | 48-52 |
| 6-10 | 16-25 | 42-46 |
| 11 | 17-24 | 38-41 |
| 12 | 17-24 | 33-36 |
| 13-16 | 17-31 | **25-31** (merged with the inner ring) |

| property | value |
|---|---|
| ring colour | (255, 101, 0) = `#FF6500` |
| ring alpha | 106/255 = **0.42** |
| ring stroke | 4-5 px of a 158 px tile = **0.028 x tile** |
| start radius | **58 px** of 158 = 0.367 of the tile |
| end radius | **31 px** of 158 = 0.196 of the tile |
| frames 1-2 tint | colour-transformed through (0,255,255) -> (50,224,205) -> (152,163,103): a cyan-to-orange tint-in |
| baked length | 15 frames = 0.5 s, then `stop()` |

The inner ring (16-25 px, constant) is the target box the circle closes onto, not the lock; the outer
ring is the lock. Timing is **not** the baked length: see §4.

## 4. Timing: how 2.0 s of lock maps onto a 16-frame clip

`ModuleStruct_Targets_TargetMovie.as`, decoded:

```
public function SetLockonProportion(param1:Number) : *
{
   if(this.CursorLockonNumFrames > 0) {
      _loc2_ = 1 + param1 * (this.CursorLockonNumFrames - 1);
      if(this.CursorLockonFrame != _loc2_) { this.CursorLockonMovie.gotoAndStop(_loc2_); ... }
   }
}
```

- `CursorLockonNumFrames = CursorMovie.getChildByName("Lockon").totalFrames` (same class, in
  `SetCursor`) - 16 for this clip.
- The caller passes the lock fraction in `TAI_Cursor_LockonProportion`:
  `SetCursor(..., param6, ...)` -> `SetLockonProportion(param6)` (`ModuleStruct_Targets.as` 306).
- So the ring is **frame-stepped**, one of 16 poses per lock value, and the 2.0 s of
  `MissileLockOnDuration` is spent across those 16 poses (125 ms per pose, derived). The 5-frame
  hold at radius 47 (frames 6-10) covers 0.63 s of the 2.0 s lock - that is the slow middle band of
  the ring, not a play-once animation.
- `MissileLockOnDuration` is the *native* timer; the movie only receives a 0..1 fraction. Nothing in
  the movie knows 2.0 s: `UNKNOWN` whether the native code uses exactly this member for the fraction
  (only the offset and default are decoded).

## 5. Operator fact that the data does not reproduce

The operator says the **pursuit** diamond has the centres of its edges missing. Measured silhouettes:

- `missile_lockon_square_anim_591` f1/f5/f10/f15/f20: angular coverage continuous, no empty bin - a
  closed diamond.
- `VehicleVariableTargetLockon_580`: two closed circles, no gap.
- `batmobile_lockon_277` f8: a closed red diamond over a closed ring.

So the gap is either (a) drawn by the mode-specific cursor label frame inside the target cursor
(which FFDec did not export: no sprite in `export/sprites/` has the 1075-frame cursor timeline -
largest is 594 frames) or (b) authored. **Both facts are kept: the operator's gap wins, and the
overlay draws it**; the exact BmAK bracket geometry stays `UNKNOWN`.

## 6. UNKNOWNs

1. **Which clip each mode draws.** `ModuleStruct_Targets_TargetMovie` has label blocks at frames
   529, 546, 590, 708, 725, 748, 763, 777 (`addFrameScript` stops at 528, 545, 589, ...), and
   `SetCursor` switches on the label name (`"vehicle_main"`, `"vehicle_lockon"`, `"vehicle_detail"`).
   The 1075-frame cursor timeline itself is not in the sprite export, so which label is battle and
   which is pursuit is `UNKNOWN`; the two clips above are the only diamond+circle assets the module
   contains.
2. **World -> screen projection.** The movie receives normalised coordinates and never a world
   vector; the transform is native (`HUD.md` 248-255 records the same for the radar, and the radar's
   `UC_UpdateTargetPosition(x,y,z)` shows only that the game can hand it positions).
3. **Marker screen size.** `ScreenSize` arrives as a 0..1-ish scalar and is turned into
   `StageHeight * param5 / 25` (decoded, `SetCursor`), but what native value it carries per target
   distance is `UNKNOWN`.
4. **`batmobile_lockon`'s role.** A 16-frame red flash that settles by frame 8; whether it is the
   lock-success flash or the batmobile target's static art is `UNKNOWN` (no call site names it).

## 7. Drawing spec for the hook overlay (brief 7985)

All numbers below are in **viewport fractions** where the size is unknown at draw time; the overlay
should work from the projected point plus a per-target size.

### 7.1 Shared

| item | value | origin |
|---|---|---|
| anchor | target's projected screen point `(sx, sy)` in pixels; the game gives the HUD fractions `x/W`, `y/H` | decoded (`SetCursor`), projection authored |
| marker across | `D` = target size on screen, authored from distance; BmAK baseline: diamond 57 px on a 1024x720 stage = **0.056 W** (0.079 H) | decoded bbox, scaled authored |
| diamond stroke | width `0.035 * D`, colour `#FF6600`, alpha **0.91** | decoded |
| circle stroke | 4-5 px of the 158 px tile = `0.028-0.032 * tile`; against the ring's start diameter (0.734 tile) that is `0.038-0.043 * D_circle`; colour `#FF6500`, alpha **0.42** | decoded |
| fps for any motion | 30 (the HUD pipeline's rate) | decoded (`TickDeltaTime` 0.033) |

### 7.2 Battle mode - instant orange diamond

1. On target acquisition, draw immediately, no fade, no grow (operator: appears instantly; matches a
   frame-stepped clip at frame 1).
2. Four equal edges, vertices on the vertical/horizontal axes, half-diagonal `D/2`, stroke as above.
3. Optional spin: `missile_lockon_square_anim` f1..f20 = 0.667 s per revolution (decoded). The
   operator does not describe a spin, so leave it **off** unless asked.
4. No lock fraction, no circle.

### 7.3 Pursuit mode - gapped diamond plus shrinking circle

1. **Diamond**: same four vertices, but each edge drawn as two segments, leaving a gap centred on the
   edge. Authored gap: **20 % of the edge length** (no BmAK value exists, §6.1); draw it as 4
   corner brackets of 40 % edge length each.
2. **Circle**: centre `(sx, sy)`, radius from the lock fraction `p` in 0..1 by the measured table
   (normalised to the 158 px tile, then scaled by `D_circle / 0.734` since the ring's start diameter
   is 0.734 of the tile):

| `p` (lock 0..1) | step `n = round(1 + 15p)` | radius / tile | radius / start radius |
|---|---|---|---|
| 0.00-0.03 | 1 | 0.158 (pop-in arc) | 0.43 |
| 0.07 | 2 | 0.367 | 1.00 |
| 0.20 | 4 | 0.317 | 0.86 |
| 0.33-0.60 | 6-10 | 0.278 | 0.76 |
| 0.67 | 11 | 0.250 | 0.68 |
| 0.73 | 12 | 0.218 | 0.59 |
| 0.80-1.00 | 13-16 | 0.177 | 0.48 |

3. **Timing**: drive `p = clamp(t / MissileLockOnDuration, 0, 1)` with `t` the time the target has
   been inside the lock cone and `MissileLockOnDuration` **2.0 s** (decoded default; 1.0 s for
   civilian targets). Do **not** play the clip at 30 fps: the baked 0.5 s length would finish the
   ring in a quarter of the lock (decoded, §4). Equivalent closed form: `radius(p) = 0.367 - 0.190 * p`
   of the tile, with the table above as the stepped reference.
4. **Locked**: at `p >= 1`, hold the end radius (0.177 of the tile) and swap the diamond to full red
   saturation for 0.53 s if a success flash is wanted (`batmobile_lockon`: 42x39 px, (254,24,24)) -
   authored, since its call site is `UNKNOWN`.
5. **Lost lock**: `p` decays to 0 and the circle disappears; BmAK has no reverse clip in these
   assets (`UNKNOWN`).

### 7.4 What the hook must supply

| input | why |
|---|---|
| target world position -> viewport pixels | the movie gets normalised fractions only; the projection is native (§6.2) |
| per-target screen size (or distance) | the diamond/box size (`ScreenSize`, §6.3) |
| lock fraction `p` | the ring pose; from the lock timer / `MissileLockOnDuration` |
| mode flag (battle / pursuit) | picks 7.2 or 7.3 |
| on-screen test | combat clips are drawn for visible targets only; the offscreen case is a separate pulsar in BmAK (`OffScreenPulsar`) |

## 8. Files written

- `E:/Modding/_BmAKgrab/hud/lock/` - export already present (`HudModuleTargets.gfx`,
  `export/shapes` 520 SVGs, `export/sprites` 520 timelines, `scripts/` AS3); added by this task:
  `MEASUREMENTS.md` and `preview/` (15 upscaled crops of the frames cited).
- This report.

## 9. Commands run (verbatim, key ones)

```
cd /e/Modding/_BmAKgrab/hud/lock && ls scripts/scripts/ ; ls export/shapes | head -6 ;
  grep -n "missile_lockon_square_anim\|VehicleVariableTargetLockon\|batmobile_lockon\|lockon" scripts/scripts/ModuleStruct_Targets.as
    -> only TestSetCursor(1,"vehicle_lockon",...) at 152 and the SetCursor call at 306

cd ... && ls scripts/scripts/HudModuleTargets_fla | grep -i "missile\|lock\|batmobile\|tank|reticl|square"
    -> VehicleMissileTarget_588/_bomb_551/_emp_567/_friend_570/_multi_590/Invalid_593,
       missile_lockon_square_anim_591, missile_border_anim_499, batmobile_lockon_277,
       VehicleVariableTargetLockon_580, tank_hack_544

python (PIL 12.3.0) over export/sprites: per-frame bbox/colour/radius histograms
    -> the tables in sections 2-3; MEASUREMENTS.md records the raw numbers

grep "MissileLockOn" Research/BatmobileGrab/*.md
    -> WEAPONS.md:839 | RBatmobileEMPMissile.MissileLockOnDuration | 0x0A00 | FloatProperty | 2.0
       WEAPONS.md:840 | ...CivilianMissileLockOnDuration | 0x0A04 | FloatProperty | 1.0
```

## 10. UNKNOWNs

See §6 - repeated here for the report contract: the mode->label mapping, the native world->screen
transform, the per-target `ScreenSize` values, and `batmobile_lockon`'s call site. None of them block
the overlay: it needs a projected point and a lock fraction, both of which the hook owns.

## COMPROMISES

None from lore accuracy. The pursuit diamond's edge gaps are drawn from the operator's description
because no BmAK asset in this module contains them (§5); that is a `UNKNOWN` geometry, not a
substitution of another game's art.
