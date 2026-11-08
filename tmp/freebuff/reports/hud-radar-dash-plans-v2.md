# HUD, radar and dash plans v2 — every element, its BmAK setter, its JC3 receiver and the caller that is missing

**Task.** Rebuild the HUD/radar/dash plans after
`tmp/freebuff/reports/audit-hud-cluster-plan-against-movie-data.md` found the damage-flash signature
wrong and eleven rows unsourced, folding in `radar-setters-against-hud-grab.md`,
`radar-setters-to-jc3-minimap-plan.md`, `dash-hud-unknown-closing.md` and `dash-hud-gauges-plan.md`.
The operator's fixed targets are in `OPERATOR_PRIORITIES.md` §"HUD leads". One table covers every
element; each value below is tagged **decoded**, **derived** or **UNKNOWN**.

**Labels.** **decoded** = a setter name/signature or member read at the cited `file:line`.
**derived** = arithmetic or set logic on decoded values, shown. **UNKNOWN** = searched and absent,
with the file/instrument that would settle it.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: the v2 HUD/radar/dash table and build step |
| file | `tmp/freebuff/reports/hud-radar-dash-plans-v2.md` (this file) |
| why this file | the brief names it; it is a report, so nothing the game reads changes |
| reverted by | deleting this file. No movie, `.gfx`, `hud.as`, palette, entity or build was edited |

## 1. The corrections v2 carries

| # | fault | v2 ruling | evidence |
|---|---|---|---|
| F1 | damage flash adopted `(part, x, y, frames)` from G3 | **`(part, amount, duration, frames)`** | `HUD.md:174` "`UC_SetImpactDamageFlash` | `part, amount, duration, frames`"; `HUD_SPEC.json:231-232` `param1:String, param2:Number, param3:Number, param4:int` |
| F2 | the damage number's **position** derived as `StageWidth*x / StageHeight*y` | **UNKNOWN** — there is no x/y argument to compute it from | F1; G3's placement rested on the refuted signature |
| F3 | `Cap` `Decrease` = 65 frames = 2.167 s | **UNKNOWN** — 65 frames is `Upgrade1`/`Upgrade2`'s length | G3 §2 badge bullets; no source gives a `Cap` label length |
| F4 | "health proportion is 0..2 in effect" and `max_health` 36,000 | **UNSOURCED** (ledger/build facts), and the 2.0 ceiling is contradicted by the contract: 0..1 plus armour above 1 | `HUD_SPEC` `health_is` / `max_is`; `HUD.md:188-198` |
| F5 | radar `HUD.md:219` argument names (`x,y,z`, `kind`) | **refuted**; use `(angle, x, z)`, a **dot count** and an **urgency threshold** | `G3-HUD-RADAR.md:37,41,43`; PASS at `:101` |
| F6 | G3 §1 prose "z ≤ 25" | the table's z is 56.890 / 51.171 / 36.326 — the prose is stale, the number is not | `G3-HUD-CLUSTER.md` §1 table vs its own sentence |
| F7 | cooldown states → `Ready = −1`, `1..4 → 0.75…0.0` | two mappings exist; v2 uses `state / 4` (0.00…1.00) and keeps `−1` only for "hidden" | `T6_HUD_CAMERA.md:53` (T-HUD16), which also flags it "a Q check, not a file fact" |
| F8 | 15 radar setters assumed to reach a minimap | JC3 has **no minimap** (0 matches for `minimap` in 260 scripts); the receiver is the POI system | `hud-radar-bmak-values.md` §UNKNOWNs 6 |

**Eleven unsourced rows, consolidated.** The audit's UNSOURCED items (radial loader, ammo-bar
mechanism, icon-id census, `MCI_inflict_damage`/`CreatePoi`, `max_health`, slot wiring, 0..2
ceiling, `Cap` 65, `InitVehicle*` call sites, `infiniteAmmo` branch, `TCR`/`T-HUD13/16`) are marked
UNKNOWN or re-sourced in §3. No row inherits a value from a file that does not state it.

## 2. Every HUD element

`movie` = the BmAK movie that owns the element. Signatures are the decoded ones; where the grab's prose
and the JSON disagree, the JSON arity and the AS3 name are used (F5).

### 2.1 Dash / cluster (17 rows)

| # | element | BmAK movie + setter signature (decoded) | closest JC3 `hud.gfx` element + member (decoded) | caller that is missing | build step |
|---:|---|---|---|---|---|
| H1 | Health bar (top left) | `HudModuleBatmobile` · `UC_SetHealth(param1:Number, param2:Number)` — `HUD.md:162`, `HUD_SPEC.json:219-220` | `MCI_vehicle` health paint, `hud_code/health/*`; **no public vehicle-health function** in the 260 scripts (`HUD_SPEC.json:315`, `vehicle_api` 11 members) | native vehicle-health binding (hp → proportion) | feed `min(1, hp/maxhp)`; `max = 1` |
| H2 | Armour overlay (5 tiers) | same setter, `max > 1` → `Armour<n>`, `n = int((max−1)*4)` — `HUD.md:193-195` | `MCI_vehicle_weapons1.MCI_bullet_bar` + `MCI_bullet_bar_anim`; frame `65*ammo/size` | `UpdateVehicleWeapons` — **0 call sites** | `magazine_ammo = 1+round(64·clamp(h−1,0,1))`, `size = 65`; tiers at 13/26/39/52/65 |
| H3 | Health low pulse (< 0.2) | `BG` `Pulse`/`Idle`; `MaxHealthChangePerFrame 0.05` — `HUD.md:196-197` | `MCI_bullet_bar` alpha pulse to 0.2 every 0.25 s (`is_low_ammo`) | same as H2 | feed `is_low_ammo = h < 0.2` |
| H4 | Damage number | `UC_SetImpactDamageFlash(param1:String, param2:Number, param3:Number, param4:int)` = **part, amount, duration, frames** — `HUD.md:174`, `HUD_SPEC.json:231-232` | `CreatePoi(type, use_progress_bar, is_minor, label)` (`hud.as:3768`) + `MCI_inflict_damage` | POI creator — **0 movie calls** (`JC3_HUD_WEAPONS.md:116`) | `label = str(amount or frames — see U3)`; show `MCI_inflict_damage` for `duration` |
| H5 | Damage flash position | **not in the signature** (F2) | POI position is caller-set in stage pixels (`hud.as` demo placements) | the part→screen projector | project the part's socket; **UNKNOWN** until the part list maps |
| H6 | Afterburner bar (left) | `UC_SetBoostLevel(param1:int, param2:int)` — 0…100 + upgradeLevel, `HUD.md:165`; `UC_HideBoostGauge()` | `MCI_nitro_meter` — `InitVehicleNitrous(recharge)` / `UpdateVehicleNitrous(recharge)` | native nitrous update — **0 movie callers** except 2 demo calls | `recharge = level/100` (both full = 1.0, no inversion) |
| H7 | Boost upgrade badges | `UC_ShowBoostUpgrade(param1:String, param2:String)` (`HUD_SPEC.json`); visibility from `UC_SetBoostLevel` arg 2 — `HUD.md:165` | `MCI_selected_weapon_icon` → `textures/ui/weapon_icons/<id>.ddsc` | `UpdateVehicleWeapons` (icon id) | 3 icons for upgradeLevel 0/1/2; id 614 is free |
| H8 | Quick-recharge / cooldown gauge (**left of the afterburner**) | **no setter** — 0 of 252 `UC_*` are cooldown-shaped; native `BoostCooldown[0] = 12.0 s`, `BoostDurationDonut = 6.0 s`, `BoostDuration = 2.0 s` | `MCI_radial_loader_cooldown` — `rot = weapon_cooldown*360`, masks 0–180 / 180–360 | `UpdateVehicleWeapons` (arg `weapon_cooldown`) | slot 1: `cooldown = 1 − t/12` while charging, `1.0` during the 2.0 s burn; `−1` at rest |
| H9 | Cannon-cooldown reticle | `UC_SetCannonCoolDown(int)` 0…4 → `Ready`/`PreReady`/`PreReadyLevel1/2`/`Blank` — `HUD.md:167` | `UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape)`; `E_RETICLE_CANNON = 8` exists, unbound | native reticle caller; the shape→weapon map | `weapon_cooldown = state/4` (F7); reticle shape **UNKNOWN** |
| H10 | Energy charges | `UC_SetEnergySystemParams(charges:int, max:int, proportion:Number, instant:Boolean, state:int)` — `HUD.md:166` | **none** (no charge gauge) | — | out, stated absence on both sides |
| H11 | Mode selector (DRIVE/BATTLE/ZOOMED) | `UC_SetBattleAndZoomMode(battle:Boolean, zoomed:Boolean)`; `BattleAndZoomInterface.visible` **false in DRIVE** — `HUD.md:173` | **none** | — | out; BmAK does not draw it while driving either |
| H12 | Speedometer | **none**: 0/252 setters, 0 speed tokens, `bDebugSpeedometer` false in both configs | `MCI_speedo` — `SetVisibilities()` is literally `MCI_speedo.visible = true` | native `m_CurrentType` delivery (`TYPE_BATMOBILE = 4`) | **suppress** in a private `ui/hud.gfx`: `if (m_CurrentType != TYPE_BATMOBILE) MCI_speedo.visible = true` |
| H13 | Combo meter | `UC_SetBatmobileCombo(param1:Number, param2:int, param3:Number)` — `HUD_SPEC.json:227-228` | **none** | — | out |
| H14 | XP bar | `UC_SetXpLevel(param1:Number, param2:Boolean)` — `HUD_SPEC.json:223-224` | none on the vehicle cluster (health paint has no XP) | — | out |
| H15 | Clock | **no `UC_*`** — timeline-driven (`RightSideParent.ClockTimer`) | none | — | out |
| H16 | Winch meter | `UC_SetWinchMeter(coneAngle, needleAngle, onTarget)` — `HUD.md:169` | none (no winch HUD) | — | out |
| H17 | Weapon names / special-weapon states | `UC_SetPrimaryWeapon(name)`, `UC_SetSecondaryWeapon(name,b,b)`, `UC_SetSpecialWeapons(3×state)` — `HUD.md:168` | `TXT_name`, `TXT_bullet_ammo`, `MCI_selected_weapon_icon` | `InitVehicleWeapons` (name, id) | names via `weapon_name`; `infiniteAmmo = true` hides counters |

### 2.2 Radar (15 setters, `HudModuleBespokeLocalRadar`)

The receiver is **not a minimap** (F8). It is the POI system: `CreatePoi(type, use_progress_bar,
is_minor, label)` (`hud.as:3768`), `UpdatePoi(poi, data)` (`hud.as:3812`), and the data keys
`m_Progress`, `m_IconAlpha`, `m_IconScale`, `m_ArrowState`, `m_ShowDistance`/`m_Distance`, `m_Flash`,
`m_Ping`, `m_Look`, `m_ShowLabel` (`hud_code/poi.as:711-752`).

| # | element | BmAK setter signature (decoded) | closest JC3 POI member | caller that is missing | build step |
|---:|---|---|---|---|---|
| R1 | Player position / map rotation | `UC_SetPlayerPosition(angle, x, z)`; `RootNetwork.rotation = angle*57.3`; **2-D x,z** — `G3-HUD-RADAR.md:43` | none — there is no player blip and no rotating map in `hud.gfx` | the map/root owner | author the map background + one rotating container; 80 px/unit applied by us |
| R2 | Target blip with facing arrow | `UC_UpdateTargetPosition(angle, distance, bearing, dots)`; `x = 80·d·sin(a)`, `y = −80·d·cos(a)`, `rotation = bearing*57.3` — `:37` | `poi.x/y` (stage px) + `m_ArrowState` (8 states at −135…180) + `m_Distance`/`m_ShowDistance` | per-frame vehicle→POI driver — **0 `CreatePoi` calls** | one POI per track; bearing → nearest `m_ArrowState` (8 steps, accuracy cost) |
| R3 | Lock-on bar | `UC_SetLockonValue(value, threshold)`; `value > threshold` → `State1` — `:41` | `CreatePoi(..., use_progress_bar = true, ...)` → `m_Progress` | POI creator | `m_Progress = value`; threshold **0.3 is plan-only** |
| R4 | Stationary lock-on bar | `UC_SetStationaryLockonValue(value)` — `:92` (plan) | `m_Progress` | POI creator | `m_Progress = value`; the 0.01 floor is plan-only |
| R5 | Target health title | `UC_SetHealthTitle(String)` | `CreatePoi(..., label)` → `m_ShowLabel` | POI creator | `label = title` |
| R6 | Target health value | `UC_SetHealthValue(value, critical)` | `m_Progress` (or label) | POI creator | `m_Progress = value`; `critical` → `m_Flash` |
| R7 | Heavy tanks (flash + radius) | `UC_PushHeavyTanksToFlash(count, jammed)`; per-tank `(ArrayIndex, X, Y, Bearing, MovieFrame)`, `−10000` = keep frame — `:33` | one POI per tank + `m_IconScale`; **no radius ring member** | POI creator + the native tank feed | bigger arrow via `m_IconScale`; the radius ring must be authored |
| R8 | Root network (roads/trails) | `UC_SetRootNetwork(String className)` | **none** | — | out; JC3 has no root-network layer |
| R9 | Roots permanently visible | `UC_SetRootsPermanentlyVisible(Boolean)` | **none** | — | out |
| R10 | Root opacity | `UC_SetRootNetworkOpacity(alpha)` | `m_IconAlpha` (per POI, not per network) | POI creator | fade each POI instead of the network |
| R11 | Map mask | `UC_SetMaskEnormous(Boolean)` → scale 8 or 1 | **none** | — | out; the 8/1 values are plan-only |
| R12 | Map pulse | `UC_DoPulse(seconds)` → `totalFrames − 55 − seconds*30` | `m_Ping` / `m_Flash` | POI creator | `m_Ping = true` on the POI; the frame formula is plan-only |
| R13 | Radar / tank visual mode | `UC_SetVisualMode(radar, tanks)` | **none** (no map/tank filter) | — | out; show/hide the authored map container instead |
| R14 | Intro | `UC_DoIntro()` | POI creation is the "show" | POI creator | create the POIs on battle entry |
| R15 | Outro | `UC_DoOutro()` | POI removal | POI lifecycle owner | remove the POIs on exit |

**Radar icons per operator class.** The movie has **no class switch**: 0 matches for `kind`,
`helicopter`, `police`, `military`, `hack`, `red`, `green`, `colour` in the module script
(`G3-HUD-RADAR.md` §7). Colour is symbol content, and the 32 decoded `POI_TYPE_*` constants contain
**no vehicle-class type** (`JC3_HUD_WEAPONS.md:106-110`). So every class icon is **authored**, not
decoded:

| lead | BmAK evidence | JC3 carrier | label |
|---|---|---|---|
| icons are arrows that point where the vehicle faces | `rotation = bearing*57.3` decoded | `m_ArrowState`, 8 quantised angles (−135…180) | **decoded** (member) / **derived** (quantisation cost) |
| tanks have bigger arrows | `HeavyTankElement` + `HeavyTankRadiusMovie` exist; **no size** | `m_IconScale` (scaled through `Update`) | **decoded** carrier / **UNKNOWN** ratio |
| cops own icon | no `police` token | nearest type `POI_TYPE_HEAT_RADIO = 11` | **derived** (choice) |
| military own icon | no `military` token | nearest type `POI_TYPE_ENCOUNTER = 12` | **derived** (choice) |
| tracked vehicles, green | only `trackingVehiclePathDot` (path dots, not the vehicle) | no green; `m_ArrowState` rotates but does not recolour | **UNKNOWN** — authored green icon |
| hacked: red → green | no `hack`/`red`/`green` | two authored icons swapped on state; **no colour member** | **derived** (icon swap) / **UNKNOWN** (state source) |
| helicopter: arrow with spinning blades | no `helicopter` token; frame table UNKNOWN | no rotor member; a POI carries one static icon | **UNKNOWN** — needs a 2-frame icon or a custom clip |

The facing arrow, the tank scale and the class icons can all ride one POI per vehicle; the helicopter
rotor cannot, because a POI icon has no sub-frame animation (settle: `hud_code/poi.as`'s icon
`Update`, `:764-818`).

## 3. The value ledger — what each number is

| value | as used | label | source or settler |
|---|---:|---|---|
| health proportion | `min(1, hp/maxhp)`, `max = 1` | **decoded** contract, **derived** feed | `HUD.md:188-190` |
| armour tiers | 5 (`max > 1`, `n = int((max−1)*4)`) | **decoded** | `HUD.md:193-194` |
| armour tier frames | 13/26/39/52/65 | **derived** (`65/5`) | `MCI_bullet_bar_anim` 65 frames |
| health sweep | 0.05/frame at 30 Hz = 0.667 s | **decoded** | `HUD.md:197` |
| offscreen timer | 2 s | **decoded** | `HUD.md:198` |
| pulse threshold | < 0.2 | **decoded** | `HUD.md:196` |
| boost range | 0…100 int, upgradeLevel 0…2 | **decoded** | `HUD.md:165` |
| boost fill frames | 102, `frame = level+1`, 101 steps | **decoded** | G3 §2 |
| boost burn / cooldown / donut | 2.0 / 12.0 / 6.0 s | **decoded** (tier 0 only) | `CLUSTER.json` `native.sim_defaults`; tiers 1–2 **UNKNOWN** |
| cooldown ring fraction | `1 − t/12`, 30°/s | **derived** | from the two decoded timers |
| cooldown state mapping | `state/4` = 0.00…1.00, `−1` hidden | **decoded** (T6) but flagged a Q check | `T6_HUD_CAMERA.md:53` |
| cannon reticle shape | `E_RETICLE_CANNON = 8` | **decoded** constant, **UNKNOWN** binding | `T6:51` |
| damage flash args | part, amount, duration, frames | **decoded** | `HUD.md:174`, `HUD_SPEC.json:231-232` |
| damage number text | `String(frames)` per G3 vs `amount` per the signature | **UNKNOWN** | both name a different arg; settle in the AS3 body |
| damage number position | `StageWidth*x` etc. | **UNKNOWN** (F2) | needs the part→screen map |
| `Cap` Decrease length | "65 frames / 2.167 s" | **UNKNOWN** (F3) | Settle: the `Cap` label's frame count in `BoostMovie` |
| `max_health` 36,000 | — | **UNSOURCED** | ledger (T-DM9/B-09), not a HUD file |
| "health 0..2" ceiling | — | **UNSOURCED**, contradicted | `HUD_SPEC` health contract is 0..1 + armour |
| radar scale | 80 px per distance unit; ×57.3 | **decoded** | `G3-HUD-RADAR.md:38`, PASS `:102` |
| radar world radius (m) | — | **UNKNOWN** | native divisor; `upk_read.py` on `RHudModuleLocalRadar` |
| heavy-tank sentinel | `−10000` = keep frame | **decoded** | `G3-HUD-RADAR.md:33` |
| tracking-dot arg | 4th arg = `NumTrackingDots` | **decoded** | `:41`, PASS `:101` |
| lock-on threshold | 0.3 | **plan-only** | AS3 ~700/712, not in the grab |
| lock-on / health 0…1 + 0.01 floor | — | **plan-only** | `Bar.Element.scaleX = value` in the AS3 |
| mask scale 8 / 1 | — | **plan-only** | no grab line mentions a multiplier |
| pulse frame formula | `totalFrames − 55 − seconds*30` | **plan-only** | `totalFrames` is symbol content |
| arrow states | 8 angles, `ARROW_POINT_AT = 1` has **no case** | **decoded** member, **UNKNOWN** pointing behaviour | `hud-radar-bmak-values.md` (poi.as:818) |
| POI types | 32 constants, 21 = lock-on | **decoded** | `JC3_HUD_WEAPONS.md:106-110` |
| minimap | — | **absent** (0/260 scripts) | `hud-radar-bmak-values.md` |

## 4. The operator targets, gap by gap

| target (`OPERATOR_PRIORITIES.md`) | decoded anchor | carriable? | what closes it |
|---|---|---|---|
| health bar **top left** | `Health` at (−479.228, −328.300, 8.318), yaw 10° → screen **(32.8, 55.7)** | position itself is **not a member**; JC3 anchors the health paint to `MCI_vehicle` | private `hud.gfx` re-parent (derived), or accept JC3's anchor |
| health **in battle mode** | `UC_SetHealthBarVisible(true, "Delayed")` forced in battle; `false` returns early in battle | **yes** — setter exists | feed visibility from the mode switch |
| afterburner **left, in pursuit** | `BoostMovie` at (−452.867, 65.550, 24.110) → **(59.1, 449.6)**, left edge, lower half | the *bar* yes (`MCI_nitro_meter`); the *left* position no | private `hud.gfx` placement |
| cooldown gauge **to its left** | BmAK has **no cooldown element** (native only) | element yes (`MCI_radial_loader_cooldown`), position no (it lives in the weapon slot, bottom-right) | private `hud.gfx` re-parent + slot-1 feed |
| **no speedometer** | 0/252 setters; `bDebugSpeedometer` false | **yes** — suppression | the H12 guard in a private copy |
| radar icons per class | no class/colour switch in the movie | **no** — all six are authored | authored icon set on POIs (§2.2) |
| arrows show facing | `rotation = bearing*57.3` | **partial** — 8 `m_ArrowState` steps | accept quantisation, or a custom rotating clip |
| bigger tank arrows | `HeavyTankElement` | **partial** — `m_IconScale` | pick the ratio at art time (no size in any file) |
| helicopter arrow, spinning blades | none | **no** | authored 2-frame icon / custom clip (UNKNOWN) |
| hacked red → green | none | **partial** | two authored icons swapped |

**One gate behind five of these:** the private `ui/hud.gfx` copy (R7). Both the top-left/bottom-left
placement and the speedometer suppression live in it. The 5-minute probe is unchanged: patch the
copy to `MCI_speedo.visible = false` unconditionally, drive the Batmobile and a vanilla car in one
session. Speedo gone on both = the copy loads and the layout work is worth doing; unchanged =
the private-copy route (and every position target above) is dead with one experiment.

## 5. The missing caller, in one place

| receiver | calls in the movie | who should call it | what settles it |
|---|---:|---|---|
| `InitVehicleNitrous` / `UpdateVehicleNitrous` | 0 (+2 demo calls in `TestConstructor`) | native nitrous update (H6) | live slot read; `JC3_HUD_WEAPONS.md` §7 census is 0 |
| `UpdateVehicleWeapons` | 0 | native weapon-slot update (H2, H7, H8, H17) | same |
| vehicle health paint | 0 public functions | native health binding (H1) | `HUD_SPEC.json` `vehicle_api` has no health entry |
| `UpdateWeaponReticle` | 0 | native reticle caller (H9) | shape→weapon map is not in any file |
| `CreatePoi` / `UpdatePoi` | 0 for `POI_TYPE_LOCK_ON_TARGET` | per-frame vehicle→POI driver (R1–R15) | `JC3_HUD_WEAPONS.md:116`; the radar's native caller is `RHudModuleLocalRadar` |

This is the single structural fact of the whole HUD: **BmAK drives its HUD from native setters, and
JC3's equivalents are also native-only**, so every gauge needs a caller before any value matters. The
two exceptions are the POI system (any script may create a POI) and the private movie copy.

## 6. The build step

1. **Probe the copy (5 min, no install).** Private `ui/hud.gfx`, `MCI_speedo.visible = false`
   unconditionally; one session, two cars (§4 gate).
2. **Copy, don't edit.** Ship the private movie; never the shared `ui/hud.gfx` (R7). Re-parent the
   health clip to top-left and the nitro/loader pair to the left band inside the copy.
3. **Feed the values.** In the entity/tune: `BoostCooldown` 12.0 / donut 6.0 / duration 2.0 from the
   sim defaults; health as `min(1, hp/maxhp)`; slot 1 `weapon_cooldown = 1 − t/12`; slot bar
   `magazine_ammo = 1+round(64·armour)`, `size = 65`; icons for upgradeLevel 0/1/2 (id 614 free).
4. **Radar.** One POI per tracked vehicle: `m_ArrowState` from `bearing*57.3` quantised to 8,
   `m_IconScale` for tanks, `m_Distance` on, `label` for the target name/health, two authored icons
   for the hacked red→green swap, six class icons. No map background unless the private copy can host
   one (R1 is the only row that needs it).
5. **Gates, all read-only:** `bmak_hud_cluster.py --check`, `hud_spec.py --check`,
   `bmak_speedometer.py --check`, `t19_hud.py --check`, `bmak_radar.py --check`,
   `hud_radar_recheck.py --check`, then `bm_rc4.py --check` and `v03_wiring.py --check` for the new
   references. Any failure stops before the copy is installed.
6. **Pass bands:** no speedo pixels in the Batmobile take and a working speedo in the vanilla take;
   boost ring one turn per 12.0 s ±0.3 s; armour 5 segments, ±1 per 20 %; 8 distinct arrow headings;
   tank arrow visibly larger; helicopter icon distinguishable from the cop/military set.

Not in this step: no game launch, no install, no movie edit. Steps 1 and 2 are the only ones that
touch a file, and both are a copy.

## 7. Checks run for this report, and revert

| # | check | result |
|---|---|---|
| 1 | damage-flash signature re-read at both cited lines | `HUD.md:174` = **part, amount, duration, frames**; `HUD_SPEC.json:231-232` = `String, Number, Number, int` — the audit and the brief are right, G3's `(part, x, y, frames)` is not |
| 2 | radar setters checked against `G3-HUD-RADAR.md` and `HUD.md:219` | 3 refuted arg names (`x,y,z`, `kind`, `kind`), now carried as angle / dots / threshold; 15 setters, 4 absent from `HUD.md` |
| 3 | JC3 receiver read in `hud-radar-bmak-values.md` / `JC3_HUD_WEAPONS.md` | `CreatePoi` `hud.as:3768`, `UpdatePoi` `:3812`, 9 POI data keys, 32 types, 0 minimap matches, 0 lock-on `CreatePoi` calls |
| 4 | mouse-checked every movie element name against `HUD.md` §4–§5 | 17 dash rows and 15 radar rows come from decoded setter tables, not from G3's prose |
| 5 | unsourced values enumerated | `Cap` 65 frames, 36,000 HP, 0..2 ceiling, 0.3 threshold, 0..1 + 0.01 floors, mask 8/1, pulse formula, icon sizes, world radius — each marked UNKNOWN/plan-only in §3 |
| 6 | caller census cross-checked | `InitVehicleNitrous`/`UpdateVehicleNitrous`/`UpdateVehicleWeapons`/`UpdateWeaponReticle` 0 movie call sites; `CreatePoi` 0 for type 21 |

Not run: no movie carve, no `ffdec`, no `--check` script, no game, no install. Every number above is a
file read or arithmetic on one; the pass bands are stop conditions for a later pilot, not measurements.

**Revert:** delete this file. Nothing else was written.
