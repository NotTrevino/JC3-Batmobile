# Tracker lock marker: the yellow / grey POI and its distance line

2026-11-06. Question: the operator sees a yellow or grey circle with a distance above tracked
vehicles in missions and encounters. Which HUD element is that, what colour states and distance text
does it carry, and how does our tracker lock drive it?

**Answer in one paragraph.** It is the JC3 **POI** system in `ui/hud.gfx`: `hud.as`
`CreatePoi(type, use_progress_bar, is_minor, label)` picks a type out of 32, `hud_code/poi.as`
`FillData` maps the type to an icon clip and colours the off-screen arrow, and `poi.Update(data)`
prints the distance from the caller's `m_Distance` **string** into `MCI_distance.TXT_distance`. The
yellow state is `POI_TYPE_MISSION` (19, arrow `0xFFE717`) and the grey state is `POI_TYPE_LOCKED`
(24, arrow `0x808080`); the tracked-vehicle health variant is `POI_TYPE_MISSION` with
`use_progress_bar = true`, which swaps the icon to `MCI_mission_health`. The type is fixed at creation
- `FillData` sets `m_Type` and `Update` has no type field - so our tracker lock changes state by
**removing the grey POI and creating a yellow one**, not by re-typing it. Distance arrives as a string
(`"358m"`, `"2.3km"` in the movie's own demo), so the metre/kilometre rule is ours to author.

Labels: `decoded` = read in the AS3 cited; `derived` = arithmetic on decoded values; `authored` = our
choice, not in either game.

## 1. The element, located

Source: the decompiled `ui/hud.gfx` export (260 AS3 scripts, `hud.as` 11,295 lines), read here
directly; the same export the project's `Tools/scripts/jc3hudwpn.py` reads.

| what | value | where |
|---|---|---|
| movie | `ui/hud.gfx`, stage 1280x720 @ 30 fps | `hud.as` `[SWF]` line 15 |
| pool | `m_POIs` array; `CreatePoi` reuses an unused entry, else pushes a new one | `hud.as` 3768-3790 |
| constructor | `CreatePoi(type:uint, use_progress_bar:Boolean, is_minor:Boolean, label:String) : MovieClip` | `hud.as` 3768 |
| per-frame update | `UpdatePoi(poi, data:Object) -> poi.Update(data)` | `hud.as` 3812 |
| show / hide | `ShowPoi(poi)` (0.5 s fade in), `HidePoi(poi)` / `RemovePoi(poi)` (0.35 s fade out, then `Clean()`) | `hud.as` 3792-3810, `poi.as` 625-641 |
| marker clips | `MCI_icon_and_label.MCI_icon.MCI_mission`, `…MCI_mission_health`, `…MCI_mission_minor`, and the `MCI_locked` / `MCI_encounter` / `MCI_kill` siblings | `poi.as` 474-616 |
| distance clip | `MCI_distance.TXT_distance` | `poi.as` 27, 815 |
| distance API | `UpdateDistance(new_show_distance:Boolean, new_distance:String)` | `poi.as` 801-816 |
| on-screen position | `poi.x`, `poi.y` set by the **caller** in stage pixels (demo: 600/300, 200/650, 1100/50) | `hud.as` 7861, 7878, 7895 |

There is no world-space argument anywhere in the POI API: the movie is handed stage pixels. The
world -> screen transform is native and stays `UNKNOWN` (`hud-radar-bmak-values.md` records the same
for the radar). Our tracker must therefore supply `x`/`y` itself.

## 2. Colour states

`FillData` builds the POI in one of two branches, `is_minor` true or false, and in both it sets
`arrow_color.color` per type and applies it to **`MCI_arrow`** - the off-screen pointer, not the icon:

| POI type | id | icon clip (normal / with `use_progress_bar`) | minor icon | arrow colour | hex | RGB |
|---|---|---|---|---|---|---|
| `POI_TYPE_MISSION` | 19 | `MCI_mission` / `MCI_mission_health` | `MCI_mission_minor` | `shared_lib.COLOR_MISSION` = **16770839** | **0xFFE717** | 255, 231, 23 (yellow) |
| `POI_TYPE_LOCKED` | 24 | `MCI_locked` | `MCI_locked_minor` | `shared_lib.COLOR_LOCKED` = **8421504** | **0x808080** | 128, 128, 128 (grey) |
| `POI_TYPE_ENCOUNTER` | 12 | `MCI_encounter` / `MCI_encounter_health` | `MCI_encounter_minor` | `COLOR_ENCOUNTER` = **12187115** | **0xB9F5EB** | 185, 245, 235 (pale cyan) |
| `POI_TYPE_OPEN_WORLD` | 20 | `MCI_generic_icon` (default branch) | `MCI_minor` | `COLOR_OPEN_WORLD` = **16777215** | **0xFFFFFF** | 255, 255, 255 |
| `POI_TYPE_CHALLENGE` | 25 | `MCI_challenge` / `MCI_challenge_health` | `MCI_challenge_minor` | `COLOR_CHALLENGE` = **1813130** | **0x1BAA8A** | 27, 170, 138 |
| `POI_TYPE_KILL_TARGET` | 15 | `MCI_kill` | `MCI_kill` | literal **13369344** | **0xCC0000** | 204, 0, 0 |

`decoded`, `poi.as` 462-616 and `shared_lib.as` 39-63. Two honesties about this table:

1. **The icon is not tinted by these constants.** Only the arrow gets the `ColorTransform` at
   creation. The yellow circle is the art inside `MCI_mission`, and the grey circle is the art inside
   `MCI_locked`; the constants merely make the arrow agree with the art. The icon does get a
   `m_Look` tint during `Update` (§4), which is a separate red/green/alpha channel.
2. **The circle geometry is symbol content, not script.** The clips are named and mapped, but whether
   `MCI_mission` draws a circle, a diamond or a ring is `DefineSprite` art and is **UNKNOWN** from the
   AS3. "Yellow circle" is consistent with the name and the operator's report; it is not proven by
   the decode.

So the operator's two states are type 19 (yellow, mission / tracked) and type 24 (grey, locked - the
"not available yet / not valid" state). The encounter marker is pale cyan, not grey; if the second
state they saw was an encounter rather than a locked target, the colour is `0xB9F5EB`.

A third, independent colour path exists in `Update` (`poi.as` 711-733): `data.m_Look` tints the
**icon** - `InRangeTargetHostile` (2) zeroes green and blue (red), `InRangeTargetAllied` (1) zeroes
red and blue (green), `OutOfRange` (4) sets alpha 0.8. That is how a marker greys out / fades without
changing type. It is an alpha-and-tint filter, not a second art state.

## 3. Distance text

`Update` calls `UpdateDistance(data.m_ShowDistance, data.m_Distance)` on every update (`poi.as` 739),
and the body is three lines:

```
private function UpdateDistance(new_show_distance:Boolean, new_distance:String) : void
   if (m_ShowingDistance != new_show_distance) ... TweenAlphaVisibility(MCI_distance, 0.2, 1 or 0)
   this.MCI_distance.TXT_distance.text = new_distance;
```

| fact | value | evidence |
|---|---|---|
| field names | `m_ShowDistance` (Boolean), `m_Distance` (**String**) | `poi.as` 739, `hud.as` 7851-7852 |
| fade in / out | 0.2 s / 0.2 s | `DISTANCE_FADE_IN_TIME`, `DISTANCE_FADE_OUT_TIME` |
| text clip height | 12 px (half 6) | `DIST_HEIGHT`, `DIST_HALF_HEIGHT` |
| gap from icon | 3 px | `ICON_AND_DIST_SPACING` |
| default placement (non-minor) | **to the right** of the icon at icon mid-height: `x = +iconHalfWidth + 3`, `y = 0` | `poi.as` 792-797, 850-860 |
| placement, minor + `ARROW_UP` | centred above: `x = 0`, `y = +3 + height/2` | `poi.as` 840-846 |
| placement, minor + left/right arrow | outside the icon on that side, right- or left-aligned | `poi.as` 847-853 |
| units / number formatting | **none in the movie** - the string is printed verbatim | `poi.as` 815 |

The movie's own demo supplies the format (`hud.as` 7846-7894):

| POI | label | `m_Distance` |
|---|---|---|
| `POI_TYPE_MISSION` | `"DESTROY"` | `"358m"` |
| `POI_TYPE_CHALLENGE` | `"ACTIVATE"` | `"2.3km"` |
| `POI_TYPE_OPEN_WORLD` | `"CALL IN"` | `"11.2km"` |

`derived` from those three: metres as an integer below 1000, kilometres with one decimal above. That
is the demo's convention, not a rule the movie enforces - nothing in `poi.as` reads a number or a
unit.

**Placement caveat for the operator's report.** Stock non-minor markers print the distance **beside**
the icon, at the icon's mid-height; "above" happens only for a `is_minor = true` POI in the
`ARROW_UP` state (and then the icon itself is hidden by
`m_Icon.visible = !m_IsMinor || !is_showing_arrow`). A POI that sits on a tracked vehicle and reads
above it is therefore not stock placement - either it was a minor POI pointing up off-screen, or the
marker was drawn by a private movie. Matching "above" exactly needs either that minor/arrow
combination or a private `hud.gfx` tweak.

## 4. The update payload, in full

`poi.Update(data)` reads exactly these keys (`poi.as` 711-752):

| key | effect |
|---|---|
| `m_Look` | icon tint: 2 = red, 1 = green, 4 = alpha 0.8 |
| `m_IconScale` | `scaleX/scaleY` on the icon (ROM-start types multiply by 0.7) |
| `m_ArrowState` | `-1` unset, `0` hidden, `1` point-at, `2..9` left/right/up/down and diagonals |
| `m_ShowDistance` / `m_Distance` | §3 |
| `m_IconAlpha` | icon alpha 0..1 |
| `m_Flash` | tween icon alpha to **0.3** every **0.5 s**, loop |
| `m_ShowLabel` | label fade 0.4 s in / 0.4 s out; text set once by `CreatePoi`'s `label` |
| `m_WeaponId` | only read for `POI_TYPE_WEAPON_PICKUP` |
| `m_Progress` / `m_ProgressMax` | only when the type was created with `use_progress_bar` |
| `m_Ping` | radar ping animation |

Arrow states (`poi.as` 163-183): `ARROW_HIDDEN 0`, `ARROW_POINT_AT 1` (declared, no case in
`UpdateArrow`), `LEFT 2`, `RIGHT 3`, `UP 4`, `DOWN 5`, `UP_LEFT 6`, `UP_RIGHT 7`, `DOWN_LEFT 8`,
`DOWN_RIGHT 9`, `UNSET -1`. `ShowsArrow` is true for anything except `-1` and `0`.

`m_Progress` on a mission POI drives `MCI_bar.scaleX` (`poi.as` 705-708), i.e. the health ring on
`MCI_mission_health`. With `use_progress_bar = false` the plain `MCI_mission` is used and no bar is
drawn.

## 5. How our tracker lock drives it

Our tracker is the BmAK `Vehicle_Tracker` (`RPursuitModeMissileLauncher`, 7 fields; projectile
`Batmobile_Tracker_Projectile`, 16 fields) - a marking projectile, not a damage weapon: damage 0,
`Projectile.DamageRadius` 0.0, `MyDamageType` null, homing delay **0.2 s**, launch offset
**5461 rotator units = 30.0 deg**, `MaxSpeed` 20000, `AccelRate` 30000
(`GADGETS_HACK_TRACK.md` §3, `hacker-and-tracker-gadgets.md`). The marker it should raise is the
BmAK `Vehicle_Onscreen` marker family (`HUD.md` §4, `HudModuleTargets`), which is the yellow/grey
circle plus a range readout.

Because `m_Type` is fixed at `FillData`, each state transition is a **destroy-and-create**, not a
field update. Two POIs (grey then yellow) never coexist on the same target.

| tracker state | when | POI action | fields we send |
|---|---|---|---|
| idle | no candidate in the launcher cone, nothing marked | none, or `RemovePoi` if a POI exists | - |
| acquiring | target acquired, projectile in flight (0 -> 0.2 s) or lock window running | `CreatePoi(POI_TYPE_LOCKED, false, false, "")`, `ShowPoi`, `UpdatePoi` each tick | `m_ShowDistance=true`, `m_Distance="<n>m"`, `m_IconScale=1`, `m_IconAlpha=1`, `m_Flash=true`, `m_ShowLabel=false`, `m_ArrowState=ARROW_HIDDEN` |
| marked | projectile impact / mark confirmed | `RemovePoi(grey)`, then `CreatePoi(POI_TYPE_MISSION, true, false, "")`, `ShowPoi`, `UpdatePoi` | `m_Flash=false`, `m_ShowLabel=false`, `m_Progress=<health 0..1>`, `m_ProgressMax=1`, same distance fields |
| marked, off-screen | target outside the safe area | same POI, updated | `m_ArrowState` = nearest of `2..9`, icon auto-hidden only for minor POIs, so also `m_IconAlpha` |
| marked, out of range | range > acquire range | same POI | `m_Look=4` (icon alpha 0.8) and the distance string still updating |
| mark lost / expired | target dead, mark timer out, player leaves | `RemovePoi` | - (0.35 s fade, then `Clean`) |

`authored`: type 24 for "acquiring" and type 19 for "marked" is our mapping. The movie has no
"tracking" semantic; what it has is a grey *locked* art and a yellow *mission* art, which is exactly
the pair the operator reports, and reusing them keeps the marker inside stock art - no private movie
needed for the two states.

**Distance is ours to format.** `m_Distance` is a string; we produce it from the target's range each
update as `"<int>m"` under 1000 and `"<n.n>km"` at or above, matching the demo's three strings
(`derived`). The 0.2 s fade and 3 px gap are the movie's; the number is ours.

**Position is ours too.** `poi.x` / `poi.y` are stage pixels in a 1280x720 movie. The POI system does
no world-to-screen projection, so the tracker driver must project the target's world position (or
reuse whatever native POI placement the vehicle path already uses, which is `UNKNOWN`). Until that is
settled, the marker cannot appear over the vehicle by data alone.

**Health ring.** `use_progress_bar = true` on the mission type selects `MCI_mission_health` and feeds
`MCI_bar.scaleX` from `m_Progress`; BmAK's `TargetHealthProportion` is already a 1.0-full proportion
(`HUD.md` §4), so it maps to `m_Progress` one-to-one with no conversion. That is the only place the
stock marker can show target condition; BmAK's 6-kind `VehicleMissileTarget*` family has no carrier
and stays authored (`lock-on-reticle-hud-link.md` L-1).

**Optional lock reticle.** `POI_TYPE_LOCK_ON_TARGET` (21) is a separate POI type on the same pool; if
the tracker should also show the rotating lock reticle, create a second POI of type 21 for the
acquiring state (`MCI_lock_on.MCI_reticle`, `TweenRotation(..., 1.5, 360, linear, loop)`, no progress
bar). It is not required for the yellow/grey circle and it is not created by anything in the movie -
the caller creates it, as ours would.

### Timing we use

| number | value | source |
|---|---|---|
| acquiring flash period | 0.5 s, floor alpha 0.3 | `poi.as` `FLASH_TIME` / `FLASH_MIN_ALPHA` (decoded) |
| POI fade in / out | 0.5 s / 0.35 s | `poi.as` `FADE_IN_TIME` / `FADE_OUT_TIME` (decoded) |
| distance fade | 0.2 s each way | `DISTANCE_FADE_IN_TIME/OUT` (decoded) |
| distance refresh | 10 Hz (0.1 s) | **authored** - the movie has no timer; native calls `UpdatePoi` |
| homing / mark delay | 0.2 s | BmAK `RBatmobileMissile.HomingDelay` (decoded) |
| launch offset | 30.0 deg | BmAK `LaunchRotationOffset` 5461/65536*360 (derived) |
| acquire window | 2.0 s | BmAK `RBatmobileMissileLauncher.MissileLockOnDuration`; **not a tracker field**, borrowed from the launcher and flagged as such |
| lock reticle spin | 1.5 s per turn | `poi.as` `LOCK_ON_TARGET_ROTATION_TIME` (decoded) |

## 6. UNKNOWN, and what would settle it

1. **The marker art's shape.** `MCI_mission` / `MCI_locked` are clip names; the geometry is
   `DefineSprite` content. Route: ffdec `-export all` of `ui/hud.gfx` and inspect the two symbols.
2. **Who writes `poi.x` / `poi.y` in the shipping game.** The movie only consumes stage pixels; the
   world-to-screen transform is native. Route: trace the native POI caller, or observe a stock
   mission marker while moving.
3. **Whether the tracked-vehicle marker in a stock mission is type 19 or a private type.** The mission
   graphs (`graphs/mission/mm130/mm130_tracker.gdc/.gsc`, `graphs/spawner_group_tracker.gdc/.gsc`,
   37 encounter graphs) call `CreatePoi`, but the graph bytecode is not decoded here, so the type id
   they pass is not read. Route: decode `mm130_tracker.gdc`'s literal pool for the constant 19/24.
4. **POI count cap.** `CreatePoi` traces when no free entry exists and appends a new one; no maximum
   is stated.
5. **Distance units in the live game.** The demo strings are the only formatting evidence; the
   shipping caller's string is native.

## 7. What this report changes

Nothing in the build. It is a HUD plan: the marker exists, it is stock, its two states are
`POI_TYPE_MISSION` (yellow `0xFFE717`) and `POI_TYPE_LOCKED` (grey `0x808080`), and the distance is a
caller-formatted string printed by `MCI_distance.TXT_distance`. Our tracker lock can reproduce both
states with stock art, but only if a caller supplies `x`/`y`, the distance string and the health
fraction - three things the movie does not compute.

Checks run: values re-derived from `poi.as` 27/163-183/462-616/711-816 and `shared_lib.as` 39-63;
`hud.as` 3768-3816 and 7846-7894 read for the API and the demo strings. No game launch, no archive
opened, nothing written outside `tmp/freebuff/reports/`.
