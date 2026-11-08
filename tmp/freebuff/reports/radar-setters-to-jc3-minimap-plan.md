# BmAK radar's 15 `UC_*` setters -> closest JC3 receiver, feed path, build step

Card: radar-setters-to-jc3-minimap-plan. 2026-11-07.

**Answer in one paragraph.** JC3 has **no minimap to receive these setters**: `grep -ri minimap`
over all 260 decompiled `ui/hud.gfx` scripts returns **0 matches** (`tmp/freebuff/reports/hud-radar-bmak-values.md`,
re-derived in `Working/Translation/HUD_RADAR_RECHECK.md`). What `ui/hud.gfx` does have is the **POI
marker system** - `CreatePoi(type, use_progress_bar, is_minor, label)` (`hud.as` 3768), a per-frame
`UpdatePoi(poi, data) -> poi.Update(data)` (`hud.as` 3812), and a data object whose keys (`m_Progress`,
`m_IconAlpha`, `m_IconScale`, `m_ArrowState`, `m_ShowDistance`/`m_Distance`, `m_Flash`, `m_Ping`,
`m_Look`, `m_ShowLabel`) are the only HUD variables in reach (`hud_code/poi.as` 711-752). Every one of
the 15 radar setters therefore lands on **POIs, POI data keys, or nothing**; the map background,
the rotating arrow, the mask and the heavy-tank radius ring have no JC3 receiver and must be
**authored by the build**. 7 setters carry over through a POI member, 6 carry partially (POI member
plus an authored transform or state machine), 2 have no receiver at all.

**Intended change / file / revert.** This card *creates one new file*,
`tmp/freebuff/reports/radar-setters-to-jc3-minimap-plan.md`; it is the correct file because the brief
names it and every other radar artefact already lives under `Working/HUD/` or `tmp/freebuff/reports/`.
It edits nothing else. **Revert = delete this file** (nothing else was written).

Labels: **decoded** = read in the file cited (line quoted); **derived** = arithmetic or set logic on
decoded values; **UNKNOWN** = not in any decoded file, with the file that would settle it.

---

## 1. What the movie actually is (the four facts the brief fixes)

| fact | value | evidence |
|---|---|---|
| setter count | **15** `public function UC_*` in `ModuleStruct_Bespoke_LocalRadar.as` (788 lines) | decoded, AS3; note `Research/BatmobileGrab/HUD_INTERFACES.json` lists **21** rows for this movie - the extra 6 are inherited module calls, not this class's own (recheck row 8) |
| scale | **80 px per distance unit**: `80 * target_location_distance * Math.sin/Cos(angle)`, and the same 80 for each tracking dot | decoded, AS3 lines 288, 289, 336, 337 |
| player-up | `UC_SetPlayerPosition`: `RootNetwork.rotation = angle * 57.3`, then root placed from `hypot(x,z)` and `atan2(-x,z) - angle` | decoded, AS3 563-572 |
| the two "kind" parameters | `UC_UpdateTargetPosition`'s 4th arg -> `Private_VehicleTracker(param1)` -> `NumTrackingDots` (a **dot count**); `UC_SetLockonValue`'s 2nd arg -> `param1 > param2` -> state 1 vs 2 (an **urgency threshold**) | decoded, AS3 277-341 and 360-393 |

Two consequences that shape every row below:

- **the module has no kind switch** (0 matches for `kind`, `helicopter`, `police`, `military`,
  `hack`, `elevation`, `arrow` - `Working/HUD/RADAR.json` `probes`), so "which icon" is a frame
  number (`gotoAndStop`) chosen by the native caller, not by this script;
- **nothing is timer-driven**: positions arrive per setter call and `UC_UpdateTargetPosition` returns
  early when angle/distance/bearing are unchanged (AS3 279-283). The 30 fps is playback rate.

## 2. What the JC3 side can receive

| JC3 thing | what it is | evidence |
|---|---|---|
| `CreatePoi(type, use_progress_bar, is_minor, label)` | the **only** marker constructor; 32 `POI_TYPE_*` values, type and label fixed at creation | decoded, `hud.as` 3768; `poi.as` `FillData` 462-616; label immutability: `tracker-lock-hud-plan.md` §5 |
| `UpdatePoi(poi, data)` | the per-frame write channel; the data object's keys are the entire HUD input surface | decoded, `hud.as` 3812; `poi.as` 711-752 |
| `poi.x` / `poi.y` | **stage pixels in a 1280x720 movie**, set by the caller - no world-to-screen transform in the movie | decoded, `hud.as` 7861/7878/7895; recheck "JC3 side, in short" |
| `m_ArrowState` | an **8-way** direction enum drawn at `[-135,-90,-45,0,45,90,135,180]`; `ARROW_POINT_AT = 1` is declared with no case, so there is **no continuous rotation** | decoded, `poi.as` 163-183 + `UpdateArrow` 818 |
| POI progress bar | `m_Progress` -> `MCI_bar.scaleX`, only on a type created with `use_progress_bar` | decoded, `poi.as` 705-708 |
| vehicle cluster | 2 weapon slots, nitrous, speedo, vehicle health; `HideVehicleUi` hides the cluster | decoded, `JC3_HUD_WEAPONS.md` §3/§7, `T6_HUD_CAMERA.md` §1 |
| vehicle type | `SetVehicleType` = land / airplane / helicopter / sea | decoded, `HUD.md` §6 table |
| `ui/*.gfx` census | **31** distinct UI movies in `INDEX.jsonl` (59 archive records incl. base/patch copies); the only map-named one is **`ui/comm_map.gfx`** | derived from `Research/JC3Grab/INDEX.jsonl` (path scan, this card) |
| a minimap | **absent from `hud.gfx`** | decoded, 0 `minimap` matches over 260 scripts (`hud-radar-bmak-values.md`) |

**Feed path, stated once.** No decoded entity member carries radar data: `lock-on-reticle-hud-link.md`
§2/§5 finds 22 `AutoAim` members and **no** member naming a POI, clip, shape or colour, and
`JC3_HUD_WEAPONS.md` §8 finds 0 in-movie callers of the vehicle-HUD API. So every row's feed is
**engine call -> movie** (`CreatePoi`/`UpdatePoi`/`ShowPoi`/`HidePoi`) or **UI variable** (a key on the
POI data object), never entity data. The one entity-side fact that matters is behavioural, not HUD:
`autoaim_tuning_file` (`id:6D4C8277`) is the lock-on opt-in (`lock-on-reticle-hud-link.md` §3), and
`w618` on `v0300` already carries the lock-on preset at vehicle level while the build writes the
no-lockon one - which decides whether rows 3/4/5 ever fire.

## 3. The build blocks the table references

| block | what the build must add | why |
|---|---|---|
| **B1 POI pool** | a radar driver that owns N POIs (`CreatePoi` once per contact, reuse, `RemovePoi` on loss), and writes one `UpdatePoi` per contact per tick | the POI system is the only marker channel; the movie has no radar |
| **B2 heavy-tank ring** | an authored radius clip (or a second radial-gradient POI) because no JC3 member draws a ring | `poi.as` 711-752 has no radius/ring key |
| **B3 jam overlay** | authored `RadarDisruption` art in a private hud movie, or drop the jam state | no `jam`/`disrupt` element is decoded in `hud.gfx` (route: grep the 260 scripts, same method that returned 0 for `minimap`) |
| **B4 transform** | the transplant applies `x = 80*d*sin(a)`, `y = -80*d*cos(a)`, then subtracts the player yaw, then adds the stage centre (640,360 in a 1280x720 movie) | the movie takes stage pixels only (`hud.as` 7861) |
| **B5 heading quantiser** | bearing -> nearest `ARROW_*` state (8-way), or a private rotating clip if the arrow is not acceptable | `poi.as` 163-183 has no continuous rotation |
| **B6 lock/health meter** | a POI driver implementing the 3-state logic (`v > threshold`), destroy-and-recreate on label change, `m_Progress` as the bar | `m_Type`/label are creation-time only (`tracker-lock-hud-plan.md` §5) |
| **B7 text** | title/status strings via the `label` argument, recreated on change | same |
| **B8 show/hide/teardown** | group flags in the driver; `ShowPoi`/`HidePoi`/`RemovePoi` for intro/outro/visual mode | POIs have per-item show/hide only |
| **B9 ping latch** | `m_Ping` true once per pulse, period held in the driver | `m_Ping` takes no seconds |
| **B10 map art** (optional) | authored map background clip, or accept a flat radar (no art) | no JC3 map element in `hud.gfx`; `ui/comm_map.gfx` exists but is undecoded |

## 4. The numbered setter table

Column meanings: **closest JC3 receiver** = movie + script + variable; **feed** = engine call / UI
variable / entity data; **build step** = the B-block from §3 plus the concrete change; **evidence** =
label + the file that settles it.

| # | setter | BmAK meaning (decoded) | closest JC3 receiver and file | feed | build step | evidence |
|---|---|---|---|---|---|---|
| 1 | `UC_PushHeavyTanksToFlash(int count, Boolean jammed)` | declares `count` heavy tanks and consumes a flat int array `[count, (ArrayIndex, PositionX, PositionY, Bearing, MovieFrame) x n]`; `ArrayIndex == -1` drives the **radius ring** (`HeavyTanksRadiusXY.x/y`, `scaleX = scaleY = bearing` used as a radius scale, `Show`/`Hide` animation); otherwise the tank clip's `x`, `y`, `rotation`, `gotoAndStop(frame)`, with `-10000` = keep previous; `jammed` toggles `RadarDisruption.Child.visible` | one POI per tank: `CreatePoi`/`UpdatePoi` (`hud.as` 3768/3812) with `m_IconScale` for size and `m_ArrowState` for heading; **ring = none** (`poi.as` 711-752 has no radius key); **jam = none decoded** in `hud.gfx` | engine call (POI create/update) + UI vars | **B1 + B2 + B3**: POI per tank; authored ring clip; jam overlay authored or dropped | meaning **decoded** (AS3 164-276); ring/jam receiver **UNKNOWN**, settled by a grep of the 260 `ui/hud.gfx` scripts for `radar`/`jam`/`disrupt` (the `minimap` 0-match shows the method) |
| 2 | `UC_UpdateTargetPosition(Number angle, Number distance, Number bearing, int dots)` | the blip: `x = 80*d*sin(a)`, `y = -80*d*cos(a)`, `Element.rotation = bearing*57.3`; early-return when the (a,d,b) triple is unchanged; 4th arg -> `Private_VehicleTracker(dots)` | `UpdatePoi` + `poi.x`/`poi.y` (`hud.as` 3812, 7861) for position; heading has only `m_ArrowState` (8-way, `poi.as` 163-183); `m_ShowDistance`/`m_Distance` for the range text | engine call + UI vars | **B4 + B5**: apply the 80 px/unit and the player-up rotation in the driver, quantise bearing to the nearest arrow state | meaning **decoded** (AS3 277-341, 80 at 288/289); receiver **decoded** (`poi.as` 711-752); the missing continuous rotation is **decoded** (`ARROW_POINT_AT` has no case, `poi.as` 818) |
| 3 | `UC_SetStationaryLockonValue(Number value)` | forces `display_state = 3`, meter to `State0`, status text to `"$Tracking.VehicleLockonStationary"`, then `Bar.Element.scaleX = value`, visible while `value > 0.01` | POI progress bar `m_Progress` -> `MCI_bar.scaleX` on a `use_progress_bar` type (`poi.as` 705-708); the status string is the `label` passed to `CreatePoi` (`hud.as` 3768) | UI var (`m_Progress`) + creation-time `label` | **B6 + B7**: one progress-bar POI in "stationary" state, bar = value, label = the stationary string; recreate to change label | meaning **decoded** (AS3 342-359); bar/label receiver **decoded** (`poi.as` 705-708, `hud.as` 3768); label immutability **decoded** (`tracker-lock-hud-plan.md` §5) |
| 4 | `UC_SetLockonValue(Number value, Number threshold)` | bar fill; `is_increasing`; state = increasing or `value == 1` ? 0 : (`value > threshold` ? 1 : 2), i.e. **the 2nd arg is an urgency threshold, not a kind**; strings `$Tracking.VehicleLockon`, `...VehicleNoLockon`, `...VehicleNoLockonUrgent` | `m_Progress` for the bar, `m_Look` as the only colour state (2 = red, 1 = green, 4 = alpha 0.8, `poi.as` 711-733), `label` for the line | UI vars | **B6**: implement the threshold in the driver (constant 0.3 in the debug keys, AS3 700/712), map state 0/1/2 to a POI type or tint; three labels -> three POIs or a private clip | meaning **decoded** (AS3 360-393); threshold semantics **decoded** (AS3 373); tint/bar receiver **decoded** (`poi.as` 711-733, 705-708) |
| 5 | `UC_SetHealthTitle(String title)` | one text field: `LockonAndHealthMeter.HealthStatusTextContainer.Child.LockonStatusText.text` | `label` argument of `CreatePoi` (`hud.as` 3768) - static text under the marker | creation-time argument | **B7**: pass the title as the label; a changing title costs a destroy/create | meaning **decoded** (AS3 394-398); receiver **decoded** (`hud.as` 3768 + demo labels `"DESTROY"`/`"ACTIVATE"`, `hud.as` 7846-7894) |
| 6 | `UC_SetHealthValue(Number value, Boolean critical)` | target health bar `scaleX = value`, visible above 0.01; `Private_SetBarState` picks `HOT_HEALTH` over `HOT_TRACKER` (health wins); `critical` -> `gotoAndPlay("HealthCritical")` else `"Health"` | `m_Progress`/`m_ProgressMax` on a mission POI with `use_progress_bar` -> `MCI_mission_health` + `MCI_bar.scaleX` (`poi.as` 705-708, 474-616); no critical clip - `m_Flash` (0.5 s, floor 0.3) is the nearest | UI vars | **B6**: progress POI, `m_Progress = value` (already a 0..1 proportion), `m_Flash = critical` | meaning **decoded** (AS3 399-420); receiver **decoded** (`poi.as` 705-708); critical art **derived** (no `Critical` clip in the POI cases) |
| 7 | `UC_DoOutro()` | `gotoAndPlay("GoOffscreen")` on the module; frame 40 fires `HudIsOffscreen()` -> `DeferredExternalInterface("DXI_LocalRadarOffscreen")` | `HidePoi` / `RemovePoi`: 0.5 s / 0.35 s fades then `Clean()` (`hud.as` 3792-3810, `poi.as` 625-641) | engine call | **B8**: `RemovePoi` every radar POI; the `DXI_*` callback equivalent is a graph/native notification and has no HUD member | meaning **decoded** (AS3 455-459, `frame40`); receiver **decoded** (`hud.as` 3792-3810); the DXI side **UNKNOWN**, settled by the native `RHudModuleLocalRadar` caller in `BmGame.upk` |
| 8 | `UC_DoIntro()` | `gotoAndPlay("Onscreen")` - the module's entrance animation | `ShowPoi` (0.5 s fade in), `CreatePoi` for an absent marker (`hud.as` 3792-3810) | engine call | **B8**: create + `ShowPoi` for all contacts | meaning **decoded** (AS3 460-464); receiver **decoded** (`hud.as` 3792-3810) |
| 9 | `UC_SetVisualMode(Boolean radar, Boolean tanks)` | `Radar` clip to `ShowRadar`/`HideRadar`, or `gotoAndStop("Offscreen")` if never initialised and hidden; `HeavyTanksParent.visible = tanks`; hides the radius ring when tanks go off; sets `HudInitialised` | per-POI `ShowPoi`/`HidePoi` (no group switch in the POI API), plus `HideVehicleUi` for the whole vehicle cluster (`JC3_HUD_WEAPONS.md` §7) | engine calls + driver flags | **B8**: radar/tank flags gate POI creation and `ShowPoi`; there is no "radar off but lock-on on" split in JC3, so the driver must own both groups | meaning **decoded** (AS3 470-496); `HideVehicleUi` **decoded** (`JC3_HUD_WEAPONS.md` §7); absence of a POI group switch **decoded** (`poi.as` 625-641 shows per-item only) |
| 10 | `UC_SetRootsPermanentlyVisible(Boolean on)` | `Map` to `"Pulse"` + `PulseTimer.stop()` when on, `"PulseFade"` when off - the permanent map pulse | `m_Ping` on the POI data object ("radar ping animation", `poi.as` 711-752) | UI var | **B9**: latch `m_Ping = true` once, and re-send at the driver's own cadence; no start/stop, no period | meaning **decoded** (AS3 497-509); receiver **decoded** (`poi.as` update-key table, `tracker-lock-hud-plan.md` §4); the missing stop/period is **derived** from that key list |
| 11 | `UC_DoPulse(Number seconds)` | `Map` to `"Pulse"`, then `PulseTimer.gotoAndPlay(totalFrames - 55 - seconds*30)`, clamped to >= 1 frame - a **seconds** input rendered as a frame offset | `m_Ping` again; no seconds field, and the POI flash is `m_Flash`'s fixed 0.5 s | UI var + authored timer | **B9**: convert seconds to the driver's tick count; the animation itself is the POI ping | meaning **decoded** (AS3 510-521, arithmetic at 514); receiver **decoded** (`poi.as` keys); `totalFrames` **UNKNOWN** (symbol content - `HUD_RADAR_RECHECK.md` row 6) |
| 12 | `UC_SetRootNetwork(String className)` | `getDefinitionByName` -> `new` -> `addChild` under `Radar.Map.RootNetwork`; `CalibrationDistance = hypot(WestExtent.x, WestExtent.y)`; removes `WestExtent`; re-places via `UC_SetPlayerPosition`. Symbol classes in the movie: `Plant1`, `Pipes`, `Plant2_Tunnel`, `Plant2_Fake` | **none** - no JC3 map/root-network element in `hud.gfx`; `poi.x`/`poi.y` are absolute stage pixels (`hud.as` 7861) | n/a (no receiver) | **B10** (optional): authored map background clip in a private hud movie, with the calibration distance as an authored constant; otherwise ship a flat radar | meaning **decoded** (AS3 522-555; symbol list in `Working/HUD/RADAR.json`); JC3 receiver **UNKNOWN**, settled by decompiling `ui/comm_map.gfx` (the only map-named movie in `INDEX.jsonl`) - not decoded in this repo |
| 13 | `UC_SetMaskEnormous(Boolean enormous)` | `Radar.Map.MaskInstance` `scaleX`/`scaleY` = 8 or 1 - lets off-map blips survive the mask | **none**: the POI API exposes `m_IconScale` for the icon only and no container mask (`poi.as` 711-752) | n/a (no receiver) | **B4**: clamp or drop out-of-range contacts in the driver (the 8x mask becomes a radius test) | meaning **decoded** (AS3 556-562); receiver **decoded-absent** (`poi.as` key list); what the 8x radius equals in stage px is **UNKNOWN** (symbol content) |
| 14 | `UC_SetPlayerPosition(Number angle, Number x, Number z)` | `RootNetwork.rotation = angle*57.3`; `hypot(x,z)` and `atan2(-x,z) - angle` place the root: **player-up 2-D x,z map**, no altitude term | caller-set `poi.x`/`poi.y` in stage pixels (`hud.as` 7861/7878/7895) - **no container rotation exists**, only the 8-way arrow | engine call per POI + authored transform | **B4**: rotate every contact by `-player_yaw` before the stage-pixel conversion, and add the stage centre (640,360) | meaning **decoded** (AS3 563-572); receiver **decoded** (`hud.as` 7861; recheck "no world-space mapping in the movie") |
| 15 | `UC_SetRootNetworkOpacity(Number alpha)` | `RootNetwork.alpha = alpha` - fades the map without touching the blips | `m_IconAlpha` (0..1, per POI) (`poi.as` 711-752) | UI var | **B4**: apply to every radar POI's `m_IconAlpha`; there is no per-group alpha, so the map fade becomes a blip fade | meaning **decoded** (AS3 573-576); receiver **decoded** (`poi.as` 711-752) |

**Roll-up (derived from the rows):** carried by a POI member end-to-end = **7** (3, 5, 6, 7, 8, 10, 15);
carried with an authored transform, quantiser or state machine = **6** (1, 2, 4, 9, 11, 14); no
receiver, authored or dropped = **2** (12, 13). **0** rows were closed as "JC3 cannot" and **0** rows
are fed by entity data.

## 5. UNKNOWNs, each with the file that settles it

1. **The in-game minimap.** 0 `minimap` matches in `hud.gfx`; either it is native or lives in another
   movie. Settle with: decompile the other 30 `ui/*.gfx` movies (list in `Research/JC3Grab/INDEX.jsonl`),
   starting with `ui/comm_map.gfx` and `ui/overlay.gfx`.
2. **Heavy-tank ring and jam overlay receivers.** No `radius`/`jam` key in `poi.as` 711-752. Settle
   with: a grep of the 260 `hud.gfx` scripts for `radar`, `jam`, `disrupt`, `radius`.
3. **Who fills `VehicleTrackingCoordinatesArray`.** Only the debug `Tick()` writes it (Standalone
   keyboard path, AS3 585-600), so the shipped dot positions come from native. Settle with:
   `RHudModuleLocalRadar`'s function bodies in `BmGame.upk` (`upk_read.py`).
4. **World radius in metres / the pixel radius the 8x mask covers.** No metre constant in the AS3.
   Settle with: the native divisor in `RHudModuleLocalRadar` + `CLASS_DEFAULTS.json`.
5. **`m_Ping`'s animation length and whether it accepts a period.** `poi.as` passes it through with no
   argument. Settle with: `poi.as`'s ping branch and `MCI_ping` symbol frames in `ui/hud.gfx`.
6. **Continuous blip rotation.** `ARROW_POINT_AT = 1` is declared with no case, so no bearing-driven
   rotation is decoded. Settle with: a private movie's own clip (authored), or `MCI_arrow`'s symbol
   script in the `hud.gfx` export.
7. **The DXI callback equivalent** for `HudIsOffscreen`. Settle with: the native `RHudModuleLocalRadar`
   caller, or a graph-side trigger in the transplant.

## 6. In-game check (pilot card)

**Pilot-card check:** with the radar transplant installed, in free roam drive a 40 s loop holding a
90 deg turn above 80 km/h with at least 3 hostile vehicles and 1 heavy tank inside radar range -
**PASS = all of: 20/20 sampled blips sit within +/-10 % of `80 px` per radar unit from the player
marker; every blip's heading is the nearest of the 8 `ARROW_*` directions, i.e. within +/-22.5 deg of
true bearing; the map's player-up rotation lags the car's yaw by <= 5 deg; 0 blips render outside the
mask radius; and the lock-on bar reads 1.00 +/- 0.02 at lock** - any single blip outside those bands,
or any lock-on state that fails to fall to 0 by 0.3 s after the target is lost, is a **FAIL**.

## 7. Evidence index

| file | what it settled |
|---|---|
| `Working/HUD/radar/_ffdec2/scripts/ModuleStruct_Bespoke_LocalRadar.as` | all 15 setter bodies, the 80 px constant (288/289/336/337), the 400 debug divisor (596), `rotation = bearing*57.3` (301), the dot-count call (290), the threshold test (371), the map placement (563-572) |
| `Working/HUD/RADAR.md`, `Working/HUD/RADAR.json` | the decoded summary, the symbol list, the probe counts (0 kind/elevation/colour) |
| `tmp/freebuff/reports/G3-HUD-RADAR.md` | the lane's own conclusions (route (b) premise now corrected) |
| `tmp/freebuff/reports/hud-radar-bmak-values.md` | 0 `minimap` matches over 260 JC3 scripts; POI placement in stage pixels; 8-way arrow; no continuous rotation |
| `Working/Translation/HUD_RADAR_RECHECK.md` | the 8-row number recheck; stage 1280x720 @ 30 fps; the 15-vs-21 setter-count note |
| `tmp/freebuff/reports/tracker-lock-hud-plan.md` | `CreatePoi`/`UpdatePoi`/`ShowPoi`/`HidePoi`/`RemovePoi` (hud.as 3768-3816), the full POI data key list (poi.as 711-752), `m_Progress` -> `MCI_bar.scaleX` (705-708), label immutability, `m_Ping` |
| `Research/JC3Grab/JC3_HUD_WEAPONS.md` | 260 scripts, 2 vehicle slots, `HideVehicleUi`, one lock-on POI (21), 0 in-movie callers |
| `Research/BatmobileGrab/HUD.md` | the radar module's element list, `SetVehicleType` land/airplane/helicopter/sea, 252 setters / 19 movies |
| `Working/Translation/T6_HUD_CAMERA.md` | `RHudModuleLocalRadar` -> "JC3 minimap is a different system", disposition `out` |
| `tmp/freebuff/reports/lock-on-reticle-hud-link.md` | no entity member names a POI/clip/shape; `autoaim_tuning_file` is the only lock-on opt-in |
| `Research/JC3Grab/INDEX.jsonl` | 31 distinct `ui/*.gfx` movies; `ui/comm_map.gfx` is the only map-named one |

## 8. Checks run for this card

| check | result |
|---|---|
| setter census vs the AS3 | 15 `public function UC_*` in the file; the table has 15 rows, names identical, parameter types identical |
| 80 px / 57.3 / 400 | re-read at AS3 288, 289, 336, 337, 301, 596 |
| the 4th argument is a dot count | AS3 290 `Private_VehicleTracker(param4)` -> `NumTrackingDots` (329) |
| the 2nd lock-on argument is a threshold | AS3 371 `param1 > param2 ? 1 : 2` |
| `ui/*.gfx` census | 59 archive records, 31 distinct paths, 1 map-named (`ui/comm_map.gfx`) |
| `minimap` in `hud.gfx` | 0 matches (from `hud-radar-bmak-values.md`, not re-run here) |
| game launched / installed / packed | **no** - nothing was launched, installed or written outside this file |
