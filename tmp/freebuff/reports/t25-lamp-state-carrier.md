# T-25 · Lamp state and pulse: state members and proposed carriers

Scope: the T-25 row (`GRAB_BACKLOG.md:1257-1264`, tracker `:1873`) and the card note that `T-L10` and `T-L21…T-L23` keep `preset_id` 0 because nothing in JC3 carries the state that switches them on muzzle fire or on `bForensicsLightActive`. This report inventories the light members that hold a state, timer or trigger field, then records the carrier each light/muzzle note proposes for those four rows. Machine-readable copy: `Working/Prep/t25_lamp_state_carriers.json` (columns `lamp_row, candidate_member, source_path, source_line, evidence_quote, closes_gap`).

Premise quote (`GRAB_BACKLOG.md:1873`):

> the state/pulse that switches them (muzzle fire, `bForensicsLightActive`) has no JC3 member until this card shows a carrier

## 1. State, timer and trigger members

`LIGHTS.json` declares 19 `jc3_fields` (`Research/BatmobileGrab/LIGHTS.json:6-25`). Of those, six hold a state, a timing flag, a mode or a preset selector; the rest are geometry, colour or photometric numbers. `LIGHTS.md` adds the BmAK-side `Type` and `Behavior` enums, and the BmAK runtime adds the `bForensicsLightActive` bool. The effect side adds the one shipped trigger, `SAttachedEffect.Usage = Fire`.

| member | side | kind | source_path:line | evidence quote |
|---|---|---|---|---|
| `behavior` | JC3 `VehicleDynamicLights` | state selector | `Research/BatmobileGrab/LIGHTS.json:7` | `"behavior",` |
| `blinking` | JC3 `VehicleDynamicLights` | timer flag, no period | `Research/BatmobileGrab/LIGHTS.json:17` | `"blinking",` |
| `cast_shadows` | JC3 `VehicleDynamicLights` | boolean state | `Research/BatmobileGrab/LIGHTS.json:19` | `"cast_shadows",` |
| `volumetric_mode` | JC3 `VehicleDynamicLights` | mode state | `Research/BatmobileGrab/LIGHTS.json:21` | `"volumetric_mode",` |
| `light_type` | JC3 `VehicleDynamicLights` | mode state (0 point / 1 cone) | `Research/BatmobileGrab/LIGHTS.json:16` | `"light_type",` |
| `preset_id` | JC3 `VehicleDynamicLights` | preset/state selector | `Research/BatmobileGrab/LIGHTS.json:25` | `"preset_id"` |
| `min_luminosity` | JC3 `VehicleDynamicLights` | threshold | `Research/BatmobileGrab/LIGHTS.json:15` | `"min_luminosity",` |
| `Type` (`VEHLT_ForensicsLight` 12, `VEHLT_BattleModeLight` 16) | BmAK `VehicleLights` | BmAK state enum | `Research/BatmobileGrab/LIGHTS.md:19` | `| by_type | (stripped)=12, VEHLT_BattleModeLight=16, VEHLT_BootLight=3, VEHLT_ForensicsLight=12, VEHLT_HeadLight=46, VEHLT_Interior=4, VEHLT_TailLight=8 |` |
| `Behavior` (`none` 16, `HeadLight` 70, `TailLight` 15) | BmAK `VehicleLights` | BmAK behaviour enum | `Research/BatmobileGrab/LIGHTS.md:20` | `| by_behavior | (none)=16, HeadLight=70, TailLight=15 |` |
| `bForensicsLightActive` (offset 2180, 0x0884) | BmAK `RVehicle` | native boolean state | `Research/JC3Grab/LIGHTS_FORENSICS.md:57` | `| bForensicsLightActive | RVehicle | 2180 | 0x0884 | BoolProperty |` |
| `SAttachedEffect.Usage = Fire` | JC3 graph effect | trigger | `tmp/freebuff/reports/muzzle-and-forensics-lights.md:22` | `**The flash itself** is not a light in JC3: `SAttachedEffect` (5,342 objects in the 232 graphs) carries `Effect` + `Usage`; `Usage` = `Fire` (`hash_jenkins` 4131019937).` |

Reading of the inventory:

- **`behavior` is the only switchable state.** It names the owning system's state machine. Eight of its nine values are ordinary vehicle lighting (`None`, `HeadLight`, `TailLight`, `LeftSignal`, `RightSignal`, `Reverse`); only `SirenLightOn`, `SirenLightOffOnFast` and `SirenLightOnOffFast` (15 rows total, `LIGHTS_FORENSICS.md:192`) name an on/off state.
- **`blinking` is a flag with no period.** 664 rows set it (`LIGHTS_FORENSICS.md:193`) and no decoded file states a rate, so a timed pulse is not carried by that member yet.
- **`preset_id` selects a lamp definition, not a runtime state.** `0` is the shipped value that means "this row carries its own numbers" (17 rows, `muzzle-and-forensics-lights.md:20`), which is exactly what the four T-25 rows use.
- **`Type`, `Behavior`, `bForensicsLightActive` are BmAK-side.** They explain why the state is missing on the JC3 side: the forensics entries are among the 16 with no behaviour, and the switch lives in native code at 0x0884.
- **The fire trigger exists, but it reaches an effect.** `SAttachedEffect.Usage = Fire` (5,342 objects, hash 4131019937) starts an `.effc`; no `.effc` carries a light node, so the muzzle *light* is not on that path.

## 2. Proposed carrier per lamp row

26 comparisons, four lamp rows. `closes_gap` is `yes` only where a shipped candidate supplies both the switch and the trigger the row needs; none does. `partly` means the candidate supplies one half (the state lamp, the lamp row, or the fire event).

### T-L10 · `ChainGunMuzzle` (muzzle fire)

| candidate member | source_path:line | evidence quote | closes_gap |
|---|---|---|---|
| `behavior` = `SirenLight*` state-driven lamp | `GRAB_BACKLOG.md:1262` | `state-driven precedent, 15 rows) and an `.effc` + `SAttachedEffect` `Usage` = `Fire` (5,342 objects` | partly |
| `behavior` = `None`, row on the gun bone | `muzzle-and-forensics-lights.md:9` | `The fleet's only lamps on a gun part are 6 rows on `bavariumtank_turret` (range 10, angle 10, white, behaviour `None`)` | no |
| `SAttachedEffect.Usage = Fire` → muzzle-flash `.effc` | `muzzle-and-forensics-lights.md:22` | `**The flash itself** is not a light in JC3: `SAttachedEffect` (5,342 objects in the 232 graphs) carries `Effect` + `Usage`; `Usage` = `Fire` (`hash_jenkins` 4131019937).` | partly |
| `blinking` = 1 | `muzzle-and-forensics-lights.md:28` | `- A lamp cannot be pulsed by the shot: the only time-varying members are `blinking` (664 rows carry 1) whose period no decoded file states (UNKNOWN), and the behaviour names, which have no forensics or weapon mode.` | no |
| `preset_id` 0 row (own numbers, no state) | `muzzle-and-forensics-lights.md:20` | `| `lights[i].preset_id` | 0 | 17 shipped rows carry 0 and state their own numbers |` | no |
| custom `muzzle_light` row + `SAttachedEffect` | `apply-light-rows.md:34` | `no per-shot pulse: `blinking` is a flag with no decoded period → **T-25**` | partly |
| a second light row driven by a behaviour | `muzzle-and-forensics-lights.md:94` | `they are the two gaps a build must close by composition (a second light row driven by a behaviour, or an authored `.effc` variant), and the row must say which it chose.` | partly |

### T-L21 · `BattleModeSpotLight` (forensics cyan)

| candidate member | source_path:line | evidence quote | closes_gap |
|---|---|---|---|
| `behavior` = `SirenLight*` state-driven lamp | `GRAB_BACKLOG.md:1262` | `state-driven precedent, 15 rows) and an `.effc` + `SAttachedEffect` `Usage` = `Fire` (5,342 objects` | partly |
| `RVehicle.bForensicsLightActive` (0x0884) | `Research/JC3Grab/LIGHTS_FORENSICS.md:57` | `| bForensicsLightActive | RVehicle | 2180 | 0x0884 | BoolProperty |` | no |
| `behavior` vocabulary (no forensics mode) | `muzzle-and-forensics-lights.md:51` | `JC3 lights have no enable member and no forensics behaviour (vocabulary: HeadLight, LeftSignal, None, Reverse, RightSignal, SirenLightOffOnFast, SirenLightOn, SirenLightOnOffFast, TailLight).` | no |
| custom `forensics_spot` cone row | `apply-light-rows.md:35` | `no enable member; `bForensicsLightActive` 0x0884 is native → **T-25**` | no |
| `blinking` = 1 | `muzzle-and-forensics-lights.md:56` | `- No time base: `blinking` is a flag only (664 rows set it, no period anywhere) and the forensics pulse/sweep in BmAK is C++ / Blueprint, not data in the packages.` | no |
| `preset_id` 0 row | `muzzle-and-forensics-lights.md:20` | `| `lights[i].preset_id` | 0 | 17 shipped rows carry 0 and state their own numbers |` | no |
| a second light row driven by a behaviour | `muzzle-and-forensics-lights.md:94` | `they are the two gaps a build must close by composition (a second light row driven by a behaviour, or an authored `.effc` variant), and the row must say which it chose.` | partly |

### T-L22 · `HeadLight1` (forensics red)

| candidate member | source_path:line | evidence quote | closes_gap |
|---|---|---|---|
| `behavior` = `SirenLight*` state-driven lamp | `GRAB_BACKLOG.md:1262` | `state-driven precedent, 15 rows) and an `.effc` + `SAttachedEffect` `Usage` = `Fire` (5,342 objects` | partly |
| `RVehicle.bForensicsLightActive` (0x0884) | `Research/JC3Grab/LIGHTS_FORENSICS.md:57` | `| bForensicsLightActive | RVehicle | 2180 | 0x0884 | BoolProperty |` | no |
| custom `forensics_head_left` cone row | `apply-light-rows.md:36` | `same state → **T-25**` | no |
| `blinking` = 1 | `muzzle-and-forensics-lights.md:82` | `- No time base: `blinking` is a flag only (664 rows set it, no period anywhere) and the forensics pulse/sweep in BmAK is C++ / Blueprint, not data in the packages.` | no |
| `cast_shadows` 1 + `volumetric_mode` 1 / `volume_intensity` 0.02 | `muzzle-and-forensics-lights.md:62` | ``cast_shadows` 1 with `volumetric_mode` 1 + `volume_intensity` 0.02 (only 2 rows do this, on the motor yacht's 15/35 headlight) for BmAK's `CastDynamicShadows`.` | no |
| a second light row driven by a behaviour | `muzzle-and-forensics-lights.md:94` | `they are the two gaps a build must close by composition (a second light row driven by a behaviour, or an authored `.effc` variant), and the row must say which it chose.` | partly |

### T-L23 · `HeadLight2` (forensics red)

| candidate member | source_path:line | evidence quote | closes_gap |
|---|---|---|---|
| `behavior` = `SirenLight*` state-driven lamp | `GRAB_BACKLOG.md:1262` | `state-driven precedent, 15 rows) and an `.effc` + `SAttachedEffect` `Usage` = `Fire` (5,342 objects` | partly |
| `RVehicle.bForensicsLightActive` (0x0884) | `Research/JC3Grab/LIGHTS_FORENSICS.md:57` | `| bForensicsLightActive | RVehicle | 2180 | 0x0884 | BoolProperty |` | no |
| custom `forensics_head_right` cone row | `apply-light-rows.md:37` | `same state → **T-25**` | no |
| `blinking` = 1 | `muzzle-and-forensics-lights.md:82` | `- No time base: `blinking` is a flag only (664 rows set it, no period anywhere) and the forensics pulse/sweep in BmAK is C++ / Blueprint, not data in the packages.` | no |
| `cast_shadows` 1 + `volumetric_mode` 1 / `volume_intensity` 0.02 | `muzzle-and-forensics-lights.md:62` | ``cast_shadows` 1 with `volumetric_mode` 1 + `volume_intensity` 0.02 (only 2 rows do this, on the motor yacht's 15/35 headlight) for BmAK's `CastDynamicShadows`.` | no |
| a second light row driven by a behaviour | `muzzle-and-forensics-lights.md:94` | `they are the two gaps a build must close by composition (a second light row driven by a behaviour, or an authored `.effc` variant), and the row must say which it chose.` | partly |

**Tally:** 26 comparisons - 0 `yes`, 10 `partly`, 16 `no`. The four `partly`-per-row proposals are the same composition idea (a state lamp row or a second behaviour-driven row); they name the mechanism but no shipped row binds it to fire or forensics, so none closes the gap on its own.

## 3. Gap closure

The gap is **not closed by any candidate above**, but it is closable by composition, and this is the route.

**Closest JC3 state system:** `VehicleDynamicLights.lights[i].behavior`, using the `SirenLight*` trio - `SirenLightOn` 9 rows, `SirenLightOffOnFast` 3, `SirenLightOnOffFast` 3 (`Research/JC3Grab/LIGHTS_FORENSICS.md:192`). It is the only shipped lamp member whose value names a runtime on/off state; all other state-ish members are static flags, modes or preset selectors. For T-L10 the per-shot trigger already exists on the effect side as `SAttachedEffect.Usage = Fire` (5,342 objects), but it reaches an `.effc`, not a light.

**Single build step that closes the gap:** in the built `.epe`, add one graph state per switch - a forensics-active state for T-L21…T-L23 and the weapon-fire state for T-L10 - and bind the four `preset_id` 0 lamp rows' `behavior` to a `SirenLight*`-style on/off pair driven by that state; then probe the lamp off with the state off and on with it on.

Why this closes it: the four rows keep their own numbers (`preset_id` 0) while `behavior` supplies the runtime switch they lack, and the graph state supplies the event the packages hold only natively (`bForensicsLightActive` at 0x0884) or in the weapon's fire animation.

Still open after that step: the pulse rate. `blinking` carries no decoded period (664 rows, `LIGHTS_FORENSICS.md:193`), so a timed pulse needs the probe measurement, not another member search. The same single step's off/on probe is the place to measure it.

## 4. Checks

- 26 comparison rows, 4 lamp rows, 0 `yes`, 10 `partly`, 16 `no` (JSON `checks`).
- 11 state/timer/trigger members inventoried across `LIGHTS.md`, `LIGHTS.json`, `LIGHTS_FORENSICS.md` and the light/muzzle notes.
- Every `source_line` re-grepped after writing; every quote is a substring of the cited line.
- No source plan, research record or backlog row was edited. Files written: `Working/Prep/t25_lamp_state_carriers.json`, this report, and its mirror.
