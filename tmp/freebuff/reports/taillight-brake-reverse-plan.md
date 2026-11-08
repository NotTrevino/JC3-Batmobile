# Rear lamps — BmAK tail / brake / reverse states, and the JC3 trigger for each

**Question:** tabulate BmAK's tail, brake and reverse lamp states (colour, brightness, fade time),
map each to the JC3 car-light trigger it would use (brake pedal, gear, handbrake), and give the
member values.

**Verdict in one paragraph.** BmAK's rear lighting is **one emitter, three cues**. There are exactly
**two `VEHLT_TailLight` entries per package** (`BrakeLightL`, `BrakeLightR`) — **8 in the whole
rig** — both `PointLightComponent`, both colour **`[255, 38, 0, 0]`** (i.e. **#FF2600**, R255 G38
B0), both **radius 150.0, falloff 6.0, shadows off**, and both with **`Brightness` not serialised**
(the value in force is `Default__LightComponent`'s **1.0**). **Tail vs brake is not distinguished in
the lamp at all** — it is distinguished by two separate `LensFlare` objects
(`BrakeLightsLensFlare` @5516, `TailLightsLensFlare` @5524) and two brake-trail particle systems
(@4660/@4668). **There is no reverse lamp**: the rig has **0** reverse-type entries, and the only
reverse signals are audio (`Play_Batmobile_Reverse`, the `Reverse` AkState) and the sim flag
`bInReverseMode`. **No fade time exists anywhere** — there is no light-fade member on the vehicle or
the light component (only `bLOD2Fade`, a bool, and `IndoorLightsFade`, an interior value); the
brake-light *duration* that does exist is `SelfDriveBrakeLights` (a float on `RVehicle`, used by
self-drive — unfortunately its value is not serialised). On the JC3 side the carrier is the
`TailLight` **behaviour** on a `VehicleDynamicLights` entry: the vanilla `TailLight` tuple is
`range 2.0, falloff_start 0.0, near_cap 1.0, multiplier 2.0, angle 10.0, diffuse (1.0, 0.2478,
0.079)` — which is **almost exactly BmAK's brake colour**, so the mapping is direct. The trigger is
the hard part: **JC3 has no brake-pedal action** (the 16 land actions are `ACCELERATE`, `REVERSE`,
`HANDBRAKE`, turns, fire, …; braking is "not accelerating"), and **no `BrakeLight` behaviour exists**
— only `TailLight`. Reverse *does* exist as a behaviour (`Reverse`, 191 entries) and as an action
(`REVERSE`, LTRIGGER), but BmAK has no reverse lamp to map, so adding one is an **addition**, not a
translation.

Labels: **decoded** = read from the cited file at the cited export/offset; **derived** = arithmetic
or mapping; **UNKNOWN** = searched and absent, with where it would be settled.

---

## 1. BmAK's rear lamp census (decoded)

`Research/BatmobileGrab/LIGHTS.md` summary: 101 entries, 4 vehicles, 129 components, and
`by_type`: `VEHLT_HeadLight` 46, `VEHLT_BattleModeLight` 16, `(stripped)` 12, `VEHLT_ForensicsLight`
12, **`VEHLT_TailLight` 8**, `VEHLT_Interior` 4, `VEHLT_BootLight` 3. **Zero** entries of any
reverse type. `by_behavior`: `HeadLight` 70, **`TailLight` 15** (8 tail entries + 7 entries whose
type the cooker stripped and whose socket name implies tail), `(none)` 16.

The two tail entries per package, from the component table (all four packages agree except where
noted):

| package | socket | bone | component | colour | source | intensity | radius | falloff | shadows |
|---|---|---|---|---|---:|---:|---:|---|
| `Playable_Batmobile_SF` | `BrakeLightL` | `SUSP2_Wheel_Rear_Left` | `PointLightComponent` | `[255, 38, 0, 0]` | component | 1.0 | 150.0 | 6.0 | False/False |
| `Playable_Batmobile_SF` | `BrakeLightR` | `SUSP2_Wheel_Rear_Right` | `PointLightComponent` | `[255, 38, 0, 0]` | component | 1.0 | 150.0 | 6.0 | False/False |
| `Playable_BatmobileMK2_SF` | `BrakeLightL` / `R` | rear suspension bones | `PointLightComponent` | `[255, 38, 0, 0]` | component | 1.0 | 150.0 | 6.0 | False/False |
| `Playable_BatmobileJoker_SF` | `BrakeLightL` / `R` | rear suspension bones | `PointLightComponent` | `[255, 38, 0, 0]` | component | 1.0 | 150.0 | 6.0 | False/False |
| `Playable_BatmobileFunhouse_SF` | `BrakeLightL` / `R` | rear suspension bones | `PointLightComponent` | `[255, 38, 0, 0]` | component | 1.0 | 150.0 | 6.0 | False/False |

Three points that matter for a port:

1. **The lamps hang off the rear suspension arms**, not the body (`SUSP2_Wheel_Rear_Left/Right`), so
   they move with wheel travel. Their sockets are unresolved for 3 of the 4 packages
   (`LIGHT_SOCKETS.md`: only `Playable_Batmobile_SF`'s table was decoded, 26/28 rows verified;
   MK2/Joker/Funhouse have no socket table ⇒ those 73 rows are UNVERIFIED, not verified-wrong).
2. **Colour is the component's own value**, so it is authored, not inherited.
3. **`Brightness` is not serialised** ⇒ the value in force is the class default **1.0**
   (`Default__LightComponent`, `Engine.upk`). Contrast the battle-mode lamps, which *do* serialise
   `Brightness 5.0` — so a static 1.0 brake lamp is a deliberate cooked value, not an oversight.

### 1.1 The colour byte order — one contradiction to record

`LIGHTS.md` prints the column as `colour [R,G,B,A]` and its own prose says "`FColor` is read
**B,G,R,A** - UE3's memory layout for it". Those two statements cannot both hold for the printed
numbers, and the data picks a side:

| row | printed | as R,G,B | as the prose's B,G,R | which is plausible |
|---|---|---|---|---|
| `BrakeLight*` | `[255, 38, 0, 0]` | red-orange #FF2600 | blue #0026FF | **R,G,B** (tail lamps are red) |
| `VEHLT_BattleModeLight` headlights | `[255, 0, 0, 0]` | red | blue | **R,G,B** (battle mode is red in-game) |
| `HeadLight1` (sport) | `[138, 197, 246, 255]` | pale blue | orange | **R,G,B** (a blue-white headlight) |

So this report reads the triples as **R,G,B**, and flags `LIGHTS.md`'s prose as the thing that is
wrong (its column header and its values agree with each other). The one place it would bite is a
build that converts the triple by hand — convert `[255,38,0] / 255` to `(1.0, 0.149, 0.0)`, not
`(0.0, 0.149, 1.0)`.

### 1.2 Tail vs brake vs reverse — where each state actually lives

| state | lamp | what changes | evidence |
|---|---|---|---|
| **tail** (lights on, driving) | `BrakeLightL/R`, `[255,38,0]`, 1.0, r150 | `TailLightsLensFlare` present | `RVehicleBatmobileBase.TailLightsLensFlare` @5524 (ObjectProperty `LensFlare`) |
| **brake** | the **same** two lamps | `BrakeLightsLensFlare` + `BrakeLightTrailSystemL/R` + brighter lens flare | `BrakeLightsLensFlare` @5516, `BrakeLightTrailSystemL` @4660 / `R` @4668 (`ParticleSystemComponent`) |
| **reverse** | **none** | audio state + sim flag only | `Play_Batmobile_Reverse` (AkEvent), `Reverse` AkStateName (`AUDIO.md`), `SVehicle.bInReverseMode` (bool @1676) |

That is the single most useful finding for the port: **BmAK never changes the lamp for braking — it
adds a flare and a particle trail.** The lamp's colour and brightness are constant; the state is
carried by the flare. A JC3 port that raises `diffuse`/`multiplier` on brake would be *inventing* a
behaviour BmAK does not have, while a port that leaves the lamp steady and adds an emissive/flare
matches it.

### 1.3 Brightness and fade in BmAK terms

| quantity | value | status |
|---|---|---|
| brake lamp `Brightness` | **1.0** | decoded (class default; not serialised on the component) |
| brake lamp radius | **150.0** | decoded (component) |
| brake lamp `FalloffExponent` | **6.0** | decoded (component) |
| brake lamp cone | none (`PointLightComponent`) | decoded |
| **fade time** | **no member** | searched: no `Fade*Time*` on any light class; only `LightComponent.bLOD2Fade` (bool @544), `OmniFadeRadiusFactor` (@568), `RVehicle.IndoorLightsFade` (@4168, interior). **UNKNOWN/absent.** |
| brake-light duration the vehicle *does* have | `RVehicle.SelfDriveBrakeLights` (float @2452) | offset decoded, **value not serialised** |
| brake→reverse handoff timers | `EmergencyBrakeTimer` @4620, `HoldingBrakeTime` @656, `HandBrakeOffTime` @960 | decoded offsets, values UNKNOWN |
| brake input | `SVehicle.OutputBrake` @1884, `AkVehicle.BrakeOnStoppedCounter` @2124 | decoded |

So the honest answer on fade: **BmAK's rear lamps have no fade time as data**; the only time-like
members near them belong to the brake *system* (self-drive brake-light duration, emergency-brake
timer), and none is serialised in a shipped object.

---

## 2. JC3's light system, and which trigger reaches it

`Research/JC3Grab/LIGHT_SYSTEM.md` (G2-33): 223 vehicles, **3,217 light entries**, **25 members each**,
9 behaviour values. The behaviour vocabulary is the state machine:

| behaviour | entries | BmAK counterpart |
|---|---:|---|
| `None` | 1,177 | — |
| `HeadLight` | 1,027 | headlights (separate card) |
| **`TailLight`** | **301** | **`VEHLT_TailLight` — this is the carrier** |
| `LeftSignal` / `RightSignal` | 253 / 253 | none in BmAK |
| **`Reverse`** | **191** | **none in BmAK** (no lamp exists) |
| `SirenLightOn` / `SirenLightOffOnFast` / `SirenLightOnOffFast` | 9 / 3 / 3 | none |

**There is no `BrakeLight` behaviour.** 3,217 entries, 9 behaviours, and brake is not one of them —
so in JC3 a braking car either brightens its `TailLight` entry natively or does not show it at all.

### 2.1 The trigger table (this is the part that decides the design)

JC3's land-vehicle action set is 16 names (`INPUT.md`, `DRIVE_CARRIERS.md` §4). The relevant ones:

| JC3 action | gamepad | keyboard | BmAK meaning | reaches a tail/brake/reverse light? |
|---|---|---|---|---|
| `ACCELERATE` | RTRIGGER | W | throttle | braking is the **absence** of it — no `BRAKE` action exists |
| `REVERSE` | **LTRIGGER** | S | reverse gear/throttle | the `Reverse` behaviour's natural trigger; sim flag `bInReverseMode` |
| `HANDBRAKE` | **RPADLEFT** | Space | handbrake | **no light member**; `Brakes.rear.handbrake` is a physics flag |
| `TURN_LEFT` / `TURN_RIGHT` | LSTICK | A/D | steering | signals only (BmAK has none) |
| — | — | — | brake pedal | **no action** |

Mapping, stated plainly:

| BmAK state | JC3 trigger | JC3 behaviour | can JC3 express it? |
|---|---|---|---|
| tail on | vehicle lights state (no brake action exists) | `TailLight` | **yes** — data |
| brake | **no action**; would have to be "`ACCELERATE` released while moving" or a native brake test | `TailLight` (same entry) | **no** — no `BRAKE` action and no `BrakeLight` behaviour: **UNKNOWN / code bridge** |
| reverse | `REVERSE` (LTRIGGER) | `Reverse` | **yes, but only if a lamp is added** — BmAK has none |
| handbrake | `HANDBRAKE` (RPADLEFT) | — | **no light wiring at all** |

---

## 3. Member values for the port

### 3.1 The tail/brake entry (BmAK-faithful)

Behaviour `TailLight` on the donor's own rear-light part. Values are the **vanilla `TailLight`
tuple** (`LIGHTS.md` §"Vanilla field values per behavior") — which, notably, is nearly BmAK's own
lamp colour:

| member | value | source |
|---|---:|---|
| `behavior` | `TailLight` | the only tail behaviour (301 entries); BmAK `VEHLT_TailLight` → `TailLight` per `LIGHTS.md` by_behavior |
| `behavior_hash` | *derive at build time* — `rbmhdr.hash_jenkins("TailLight")` | derived; do **not** copy a hand-computed number (a hand-rolled Jenkins gives neither this nor the known `HeadLight` 3460580079). `LIGHT_SYSTEM.md` §9 verifies `hash_jenkins` on all 3,217 shipped `behavior_hash` values, so the project function is the source |
| `diffuse.R` | **1.0** | BmAK `[255,38,0]` / 255 → **1.0** |
| `diffuse.G` | **0.149** | 38 / 255 = 0.149019… |
| `diffuse.B` | **0.0** | 0 / 255 |
| `range` | **2.0** | vanilla `TailLight` |
| `falloff_start` | **0.0** | vanilla `TailLight` |
| `near_cap` | **1.0** | vanilla `TailLight` |
| `multiplier` | **2.0** | vanilla `TailLight` (this is the one brightness-like member; BmAK's 1.0 does **not** map 1:1 — see `LIGHT_ENTRY11.md`, "Brightness semantics … the bridge is T-18's") |
| `angle` | **10.0** | vanilla `TailLight` |
| `min_luminosity` | 0.0 | all 3,217 entries |
| `light_type` | 0 | 2,494 entries (point/omni) — matches BmAK's `PointLightComponent` |
| `blinking` | 0 | steady |
| `cast_shadows` | 0 | BmAK ships shadows off |
| `projected_texture_index` | -1 | all but 2 entries |
| `volumetric_mode` | 0 | all but 2 |
| `volume_intensity` | 0.01 | the value shipped with `near_cap 1` / `multiplier 1` rows (1,171 entries share it) |
| `uvscale.u` / `.v` | 1.0 / 1.0 | all 3,217 |
| `preset_id` | **0** | 17 shipped entries use 0 (the modernbus brake lights are two of them) and every entry states its own numbers — so 0 removes any dependence on preset semantics, which `LIGHT_SYSTEM.md` §3 calls UNKNOWN |
| `part` / `part_index` | **`sportsmuscle_taillight_r_l` = part 8**, **`sportsmuscle_taillight_r_r` = part 9** (both `has_lights = 1`, damage type `Land_Light`); `sportsmuscle_taillight_r_c` = part 31 (`Land_Generic`) | decoded from the donor's parts module (`PARTS_TABLE.jsonl`); every vanilla light part has `has_lights = 1` (`LIGHT_SYSTEM.md` §4) |
| `deformable_transform` | the part's own `_LIG` node chain | BmAK's socket bone is `SUSP2_Wheel_Rear_Left/Right`; the JC3 part carries its own node, so the chain is the *part's*, not the suspension arm's — this is the one place the port deliberately differs (BmAK lamps ride the suspension; JC3 lamps ride a body part) |

**A note on that last row.** `LIGHTS.md`'s own mapping put the BmAK brake lamps on
`|sportsmuscle_LOD1|body|SUSP2_Wheel_Rear_Left|SUSP2_Wheel_Rear_Left_LIG` (part `sportsmuscle_body`).
That reproduces BmAK's *motion* (lamps follow the suspension) but puts the light on the body part,
whereas JC3's donor already has dedicated taillight parts and meshes
(`sportsmuscle_taillight_r_l/_r_r/_r_c`, with `CarLight` blocks — 11,367 in the fleet). A part that
exists and has an emitter mesh is the safer carrier: `LIGHT_SYSTEM.md` §6 requires both a part and a
`CarLight` block, and §7c documents the exact failure mode of hanging a light on a part with no
`CarLight` block.

### 3.2 The reverse entry (an addition, clearly labelled)

| member | value | why |
|---|---:|---|
| `behavior` | `Reverse` | the only reverse behaviour, 191 entries |
| `diffuse` | **1.0, 1.0, 1.0** | vanilla `Reverse` tuple |
| `range` / `falloff_start` / `near_cap` / `multiplier` / `angle` | **2.0 / 0.0 / 1.0 / 1.0 / 10.0** | vanilla `Reverse` tuple |
| `preset_id` | 0 | same reasoning as §3.1 |
| part | the donor's reversing-lamp part if one exists, else a new light part | BmAK has none, so there is nothing to be faithful to |

This is **not a translation of BmAK** — BmAK's reverse cue is auditory. If the goal is fidelity,
skip it; if the goal is a car that reads as reverse-capable, this is the row.

### 3.3 Fade

JC3's entry has **no fade member** either (the 25 members are listed in §1 of `LIGHT_SYSTEM.md`;
fade is not among them). So on both sides "fade time" resolves to: **no data on BmAK's lamps, no
member on JC3's entries**. A visible fade would be a native/material effect — the `CarLight`
material parameters are explicitly **UNKNOWN** (`LIGHT_SYSTEM.md` §5, MODLOG §102d: the emissive
parameters are not decoded, so blocks can be copied byte-exact but not authored). **Do not invent a
fade number.**

---

## 4. What the build is

1. **Replace nothing on the lamp side; add two entries** pointing at the donor's existing
   `sportsmuscle_taillight_r_l` / `_r_r` parts, behaviour `TailLight`, `preset_id 0`, the §3.1
   values. That reproduces BmAK's constant red-orange lamp exactly (1.0, 0.149, 0.0).
2. **Do not attempt a brake state** — it has no trigger (§2.1) and no behaviour. If the operator
   wants a visible brake, the only honest options are (a) accept JC3's native tail brightening,
   or (b) a code bridge that raises `multiplier`/emissive on a brake test, which is the same wall
   as every other missing input in this project.
3. **Leave reverse alone** unless a lamp is wanted; the `REVERSE` action and `Reverse` behaviour
   both exist, so it is the cheapest of the three to add *as an addition*.
4. **No fade value anywhere.**

---

## 5. The cheapest experiment

Read-only, no launch: open the donor's `.ee` entity cache and list its existing `TailLight` and
`Reverse` entries. `LIGHT_SYSTEM.md` §4 says the donor's **left tail-light part carries a
`TailLight`, a `LeftSignal` and a `Reverse` entry** — if the donor already ships a `Reverse` entry on
a lamp we intend to keep, then reverse needs *no new row at all*, only the behaviour value, and
§3.2 collapses into "reuse the shipped entry". That single read decides whether the reverse lamp is
free or new.

---

## 6. If files are touched later — change, file, revert

Nothing was modified for this report.

| intended change | file | why it is the right file | revert |
|---|---|---|---|
| add the tail/brake lamp entries | the private `.ee`'s `VehicleDynamicLights` module (`lights[]`) | the module entry is the only thing that binds a lamp to a part (`LIGHT_SYSTEM.md` §1, §4) | rebuild from the build manifest |
| make the lamp visible as geometry | the rear part's `lod1.rbm` `CarLight` block (+ `Window` lens) | `CarLight` is the emitter mesh; copy byte-exact, never author (§5) | same |
| reorder/relabel | `Working/Lights/bm_lightrig.json` | the build's light ledger | git checkout of that file |
| nothing for brake or fade | — | no trigger, no behaviour, no member | — |

## 7. UNKNOWNs, each with its settler

| # | unknown | settler |
|---|---|---|
| U1 | whether anything at runtime raises the brake lamp (a Kismet colour/brightness set) | the entity graph / Kismet bodies; the shipped default is 1.0 white-class default |
| U2 | `SelfDriveBrakeLights` value (the only brake-light timer) | live object read; not serialised |
| U3 | what JC3 does on braking — brighten `TailLight`, or nothing | native light state machine; no `BrakeLight` behaviour exists to read |
| U4 | whether `multiplier 2.0` is the brake or the tail brightness | `LIGHT_SYSTEM.md` §3: a preset does not fix the numbers, and no file ties `multiplier` to a state |
| U5 | the socket tables for MK2 / Joker / Funhouse (`LIGHT_SOCKETS.md` U1) | decode those three cooked meshes |
| U6 | whether a light can hang on a suspension bone in JC3 | `deformable_transform` resolution (the §112 probe) |
| U7 | `CarLight` emissive parameters (so no authored colour/fade) | MODLOG §102d — not decoded; copy blocks |
| U8 | the donor's shipped `Reverse` entry contents | the donor entity cache (§5) |
| U9 | the R,G,B vs B,G,R question in `LIGHTS.md` (§1.1) | the raw `FColor` bytes at `LightComponent+512`; this report's resolution is by plausibility against three known-hue lamps, which is strong but not a byte proof |

## 8. Sources

**BmAK:** `Research/BatmobileGrab/LIGHTS.md` (the 101-entry census, `by_type`/`by_behavior`, the
per-component colour/intensity/radius/falloff table, the vanilla per-behaviour field values, the
G1-17 precedence rule), `LIGHT_SOCKETS.md` (socket→bone verification and the three packages with no
table), `LIGHT_ENTRY11.md` (the precedence chain, `Brightness 0.0` semantics, and the explicit
statement that BmAK brightness does not map 1:1 onto JC3 `multiplier`), `BMSDK_OFFSETS.json`
(`BrakeLightsLensFlare` @5516, `TailLightsLensFlare` @5524, `BrakeLightTrailSystemL/R` @4660/@4668,
`SelfDriveBrakeLights` @2452, `HeadlightsSwitchedOn` @2184, `LightComponent.LightColor` @512,
`bLOD2Fade` @544, `OmniFadeRadiusFactor` @568, `IndoorLightsFade` @4168, `SVehicle.bInReverseMode`
@1676, `OutputBrake` @1884, `HoldingBrakeTime` @656, `HandBrakeOffTime` @960), `AUDIO.md` /
`ASSETS.md` (`Play_Batmobile_Reverse`, the `Reverse` AkStateName).
**JC3:** `Research/JC3Grab/LIGHT_SYSTEM.md` (25 members, 9 behaviours with counts, the vanilla
per-behaviour values, `preset_id 0`, `has_lights`, the `CarLight` block and its UNKNOWN parameters),
`INPUT.md` / `DRIVE_CARRIERS.md` §4 (the 16 land actions — and the absence of `BRAKE`),
`ENTITIES.md` (the donor's `sportsmuscle_taillight_r_l/_r_r/_r_c` light meshes).
