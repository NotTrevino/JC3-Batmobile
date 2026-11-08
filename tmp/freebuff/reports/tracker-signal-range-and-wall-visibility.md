# Tracker signal strength, range falloff and the see-through outline

Operator fact, 2026-11-08: in BmAK a tracked vehicle carries a signal lock whose strength falls off
with distance, and a tracked vehicle can be seen through walls when it is close enough.

Sources read first: `tmp/freebuff/reports/hacker-and-tracker-gadgets.md`,
`tmp/freebuff/reports/tracker-lock-hud-plan.md`, `Working/Translation/T_WP4D_TRACKER_EMP.md`
(the corrected tracker card, not T-WP4c) and `tmp/freebuff/reports/radar-minimap-icon-plan.md`.
Fields then read in `Research/BatmobileGrab/objects.jsonl`, `HUD.md`, `HUD_SPEC.json`,
`HUD_INTERFACES.json`, `BMSDK_OFFSETS.json`, `CLASS_DEFAULTS.md`.

Labels: **decoded** = a value/tag/member read at the file and offset named; **derived** = arithmetic
or inference printed with it; **UNKNOWN** = searched and absent, with the place searched.
No field below is a plausible-sounding substitute: where BmAK has no member, the row says so.

## 1. Is the fact carried by BmAK fields at all?

The operator describes three things: a tracked state, a strength that falls off with distance, and
a see-through outline that appears inside a distance. BmAK carries the **state**, the **alpha
plumbing** and the **material**, but no metre value for either threshold:

| # | quantity | BmAK field (owner @ offset) | value / shape | label | evidence |
|---|---|---|---|---|---|
| 1 | tracked state on the target | `RVehicle.bBeingTracked` @ 0x0884 (2180), BoolProperty, bit mask 268435456 | member exists; no serialized value in any archetype tag | decoded (member) / UNKNOWN (when set) | `BMSDK_OFFSETS.json:18024-18035`; same bool word also carries `bShowOnLocalRadarInBatmobile` |
| 2 | signal strength shown to the player | HUD `LockonMeter` bar, fed by `UC_SetLockonValue(param1:Number, param2:Number)` | `LockonMeter.Bar.Element.scaleX = value`, `visible = value > 0.01`; `param2` is the bar's threshold | decoded (API + bar) / UNKNOWN (the function that turns distance into `value`) | `HUD.md:219`, `HUD.md:253-255`; `HUD_INTERFACES.json:257`; `radar-minimap-icon-plan.md:95` |
| 3 | lock range / angle of the tracker launcher | `RPursuitModeMissileLauncher.Range` @ 2448, `AutoTargetAngle` @ 2444 | members exist; the `Vehicle_Tracker` archetype serializes 7 tags, none at 2444/2448, and no class default carries them | decoded (members) / UNKNOWN (values, hence UNKNOWN falloff curve) | `BMSDK_OFFSETS.json:17690-17729`; `T_WP4D_TRACKER_EMP.md:194` |
| 4 | lock range on sibling weapons (for contrast, not the tracker) | `RBatmobileMissileLauncher.LockOnRange` @ 2436; `RBatmobileHeavyCannon.LockOnRange` @ 2476 + `CurrentLockOn` @ 2496; `RBatmobileAllegianceSwitcher.LockOnRange` @ 2400 | members only | decoded (members) / values not read | `BMSDK_OFFSETS.json:15015-15034`, `:14720-14739`, `:14650-14669` |
| 5 | see-through enable flag | `RVehicle.bDoXrayLevelFadeCheck` @ 2180, bit mask 524288 | member exists; serialized value not found | decoded (member) / UNKNOWN (value) | `BMSDK_OFFSETS.json:18047-18058` |
| 6 | see-through distance band | `RVehicle.MinDetectiveModeFadeDist` @ 4552, `MaxDetectiveModeFadeDist` @ 4556 (floats) | the only two distance-shaped xray members in the class; **no tag at 4552/4556 in any of the four packages and no CDO entry** | decoded (members) / **UNKNOWN (the two metre values)** | `BMSDK_OFFSETS.json:19360-19378`; tag scan of `objects.jsonl` for offsets 4552/4556 returned 0; `CLASS_DEFAULTS.md` lists no such field |
| 7 | per-frame outline strength | `RVehicle.CurrentXRayAlpha` @ 4540, `LastXrayMatUpdateTime` @ 4536, `iXrayMaterialExcludeIndex` @ 4544 / `...Index2` @ 4548 | runtime fields, not serialized | decoded (members) / UNKNOWN (update rule) | `BMSDK_OFFSETS.json:19335-19358` |
| 8 | material applied for the outline | `RVehicle.XRayMaterialMIC` @ 2268 = `Default__RVehicleBatmobile.MIC1`; `XrayMaterialsAssigned` @ 8564 = True; `SVehicleMesh.XRayMaterials` array count 18; `XrayLight` @ 5812 = `XrayLightComponent` | a translucent unlit xray material instance plus an 18-slot array and a point light | decoded | `CLASS_DEFAULTS.md:154`, `:401` (MIC), `:102`, `:483` (assigned), `:135`, `:452` (light); `objects.jsonl:19811` (18 entries, base), `:5385` (18, Funhouse), `:14330` (18, MK2), `:8778` (15, Joker) |
| 9 | outline style | material `Xray.xrayBatmobile_MASTER`: `BLEND_Translucent`, `MLM_Unlit`; `Alpha` 1.0; `MinDistFade` 0.9; `MaterialDensity` 500; `EnableWallFade` static switch; `OpacityMap`, `NormalMap`, `metalColour` | a soft translucent wall-fading silhouette with an opacity mask, not a hard line | decoded (values and switches) / **derived** (`MinDistFade` 0.9 read as a 0-1 fade fraction) / UNKNOWN (units of `MaterialDensity` 500) | `objects.jsonl:14901` (material), `:15075` (Alpha), `:15076` (MinDistFade), `:15077` (MaterialDensity), `:15121` (EnableWallFade), `:15171-15172` (OpacityMap, NormalMap), `:15259` (metalColour), `:15301` (`xrayMetal_Batmobile_INST`) |

Two absences are worth stating plainly:

- **No BmAK member is named `SignalStrength`, `SignalRange` or `TrackerRange`.** A full member scan
  of `BMSDK_OFFSETS.json` returns only audio `Signals`/`SignalSmoothing*` (an audio effector) and the
  lock-on members above. The "signal strength" is the HUD bar's `value` argument, not a replicated
  float on the vehicle; what computes it from distance is native.
- **The see-through threshold has no decoded number.** `MinDetectiveModeFadeDist` and
  `MaxDetectiveModeFadeDist` are the right fields, and both are unset in the data this grab holds.
  So "close enough" is an operator observation with a named carrier, not a decoded metre value.

## 2. Reproducing part 1 - the range-faded signal lock

What BmAK does, in data terms: a tracked actor (`bBeingTracked`) raises a HUD bar
(`LockonMeter`) whose fill is a 0-1 `value`, plus a distance-bearing marker. The falloff from
distance is native (`Range` @ 2448 is unset), so the curve is authored in the reproduction.

Closest JC3 system: **the HUD POI** for the marker and **the radar lock-on bar** for the strength.

| piece | JC3 carrier (file:line) | value to write | label |
|---|---|---|---|
| marker over the chosen actor | `CreatePoi(type, use_progress_bar, is_minor, label)` - `hud.as:3768`; type 21 `POI_TYPE_LOCK_ON_TARGET` draws `MCI_lock_on.MCI_reticle` rotated 1.5 s/turn (`JC3_HUD_WEAPONS.md:110-112`); type 19 `POI_TYPE_MISSION` is the yellow state (`tracker-lock-hud-plan.md:49-50`) | `CreatePoi(POI_TYPE_LOCK_ON_TARGET, false, false, "")`, then `RemovePoi` + `CreatePoi(POI_TYPE_MISSION, ...)` on mark-confirm, because `m_Type` is fixed at creation (`tracker-lock-hud-plan.md:150-157`) | decoded (API/type/icon) / derived (the state mapping) |
| strength fade | `data.m_IconAlpha` 0..1 (`tracker-lock-hud-plan.md:128`); `data.m_Look = 4` sets icon alpha 0.8 (`:71-73`, `:124`) | `m_IconAlpha = clamp(1 - (d - D0) / (D1 - D0), 0, 1)`; `m_Look = (d >= D1) ? 4 : -1`; update at 10 Hz (the movie has no timer, `:196`) | decoded (fields) / **authored** (D0, D1 and the clamp shape) |
| distance text | `m_Distance` is a **string** printed verbatim into `MCI_distance.TXT_distance` (`poi.as:739`, `:815`); demo uses `"358m"`, `"2.3km"` (`hud.as:7846-7894`) | `"<int>m"` under 1000, `"<n.n>km"` at or above | decoded (string) / derived (format) |
| radar bar | `UC_SetLockonValue(value, threshold)` sets `LockonMeter.Bar.Element.scaleX = value`, visible above 0.01 (`radar-minimap-icon-plan.md:95`; `HUD.md:219`) | pass the same normalised strength as `value`; `threshold` 0.01 | decoded (setter + bar) / derived (reuse of the strength) |
| blip position, if the radar route is used | `UC_UpdateTargetPosition(angle, distance, bearing, dots)` (`radar-minimap-icon-plan.md:90`), `px_per_distance_unit` 80 (`:15`) | `x = 80*d*sin(a)`, `y = -80*d*cos(a)` | decoded (formula and scale) |
| who creates it | nothing in the movie: 0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET, ...)` call sites (`JC3_HUD_WEAPONS.md:116`); the entity-side bridge is native (`:7`, `:148`) | a mission-style tracker graph (pattern `graphs/mission/mm130/mm130_tracker.gdc`) drives the POI | decoded (absence) / UNKNOWN (which native path paints it) |

**Gap and build step.** JC3 has the marker and the bar but no decoded link from a tracked actor to
either. Build step: author the tracker driver that (a) creates the type-21 POI on the marked
vehicle, (b) updates `m_IconAlpha`, `m_Look` and `m_Distance` at 10 Hz from the target's range, and
(c) calls `UC_SetLockonValue` with the same value; then run the B-21 probe
(`T_ROWS.jsonl:160`): fire at a moving car and record whether the round homes and a POI with a live
distance appears. The POI's screen position is still supplied by the caller -
`poi.x`/`poi.y` are stage pixels and there is no world-space argument (`tracker-lock-hud-plan.md:36`,
`:38-39`), so the driver must project or reuse a native placement; that projection is UNKNOWN.

## 3. Reproducing part 2 - see-through when close

What BmAK does, in data terms: a tracked vehicle swaps its mesh materials to `MIC1`
(`XRayMaterialMIC` @ 2268), which resolves to the unlit translucent `xrayBatmobile_MASTER` with
`MinDistFade` 0.9, `MaterialDensity` 500 and the `EnableWallFade` switch, and an
`XrayLightComponent` lights it; `bDoXrayLevelFadeCheck` plus `CurrentXRayAlpha` drive the fade per
frame, and `MinDetectiveModeFadeDist` / `MaxDetectiveModeFadeDist` are the two distance fields.
What BmAK does **not** carry is the numeric value of either distance.

Closest JC3 system, split by what is being drawn:

| piece | JC3 carrier (file:line) | value to write | label |
|---|---|---|---|
| a marker that ignores walls | the HUD POI is pure screen space: `poi.x`/`poi.y` in stage pixels, no world-space argument anywhere in the API (`tracker-lock-hud-plan.md:36`, `:38-39`); it draws over geometry because it is a 2D movie element, not because of a depth test | the type-21/19 POI from part 1, with `m_IconAlpha` fading in inside D0 and out beyond D1 | decoded (screen-space API) / derived (hence occlusion-free) |
| an outline on the actor itself | the only vehicle outline shaders JC3 resolves are `CarOutline`, `CarOutlineDeform`, `CarOutlineSkinned` (`COLOUR_NATIVE.md:34`); **no decoded entity member applies an outline pass and no material-override member exists** | author a `CarOutline` material instance on the tracked vehicle's mesh; the value that would gate it is UNKNOWN | decoded (shader names) / **UNKNOWN (selection member, depth behaviour, distance gate)** |
| a per-actor fade alpha | no JC3 counterpart to `CurrentXRayAlpha`, `bDoXrayLevelFadeCheck`, `MinDetectiveModeFadeDist` or `MaxDetectiveModeFadeDist` was found | none - author inside the material instance (opacity parameter) | UNKNOWN |

**Gap and build step.** JC3 can draw an occlusion-free **marker** today (the POI), but it has no
decoded way to draw an occlusion-free **silhouette of a chosen actor**: `CarOutline` is a shader
name, not an entity member, and the HUD movie never touches vehicle materials. Build step: ship the
marker through the POI driver (part 1), then author a `CarOutline`-based material instance on the
tracked car's mesh and toggle it from the same driver; the B-21 probe
(`T_ROWS.jsonl:160`) settles only the marker half. Whether the engine accepts a runtime material
swap on a `CCar` part is UNKNOWN and is the one thing a 5-minute test would answer (clone a car,
swap one part's material to a `CarOutline` instance, look through a wall).

## 4. Pilot card

Each sentence is one line on a card; the pass band is **authored**, because the decoded fields that
would give metres (`Range` @ 2448, `MinDetectiveModeFadeDist` @ 4552 / `MaxDetectiveModeFadeDist`
@ 4556) have no serialized value.

1. **Signal lock:** at **40 m** the lock bar reads full and the distance text updates; at **140 m**
   the bar reads zero and the marker drops to `m_Look = 4` (icon alpha 0.8) - pass band 40/140 m,
   authored, against BmAK's `LockonMeter` value and `Range` @ 2448 (value UNKNOWN).
2. **See-through:** at **45 m** the tracked car's xray outline is visible through a wall; at **130 m**
   it is not - pass band 45/130 m, authored, against BmAK's `MinDistFade` 0.9 and `MaterialDensity`
   500 (no metre value in `MinDetectiveModeFadeDist` / `MaxDetectiveModeFadeDist`, both UNKNOWN).

## 5. What would settle the two UNKNOWNs

- **The tracker's range and falloff curve:** the `Vehicle_Tracker` archetype's bytes at 2444/2448 in
  the four `Playable_Batmobile*_SF.upk` packages (T-WP4D's own re-read already says absent), or a
  runtime sample of `UC_SetLockonValue`'s first argument against distance.
- **The see-through distance:** a `Playable_Batmobile*` export that serializes offsets 4552/4556,
  or the native `RVehicle` tick that writes `CurrentXRayAlpha`; neither is in this grab.
- **The JC3 outline selection member:** the `CarOutline` shader's caller in the executable, or a
  clone test that swaps one part's material and observes whether it draws through geometry.

Revert: delete this file. Nothing outside `tmp/freebuff/reports/` was written.
