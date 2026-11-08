# Radar and map icon — BmAK's blip states, and what JC3 can actually select

Answers three things in order: **what states BmAK's radar draws and in what colour**
(measured from the carved movie and its exported art), **where JC3 keeps vehicle icon
sets and which member selects one**, and **which icon/colour each BmAK state gets**.

Per `AGENTS.md`, this is a plan: no game file is modified by this document.

---

## 1. Evidence base

| source | what it holds |
|---|---|
| `Working/HUD/RADAR.md` + `RADAR.json` (card G3-HUD-RADAR) | the decoded module: stage, 15 `UC_*` setters with AS3 line numbers, the frame table, `px_per_distance_unit` 80, the negative result on "kind" |
| `Working/HUD/radar/_ffdec2/` | the ffdec export: **58** scripts, **81** shape SVGs, **72** images, **113** sprites, `symbolClass/symbols.csv` |
| `Working/Translation/HUD_RADAR_RECHECK.md` | independent re-test of the numbers, plus the JC3 POI facts (`ARROW_*`, `m_IconScale`, `poi.x`) |
| `Research/BatmobileGrab/HUD.md` | the module roster: `RHudModuleLocalRadar` → `HudModuleBespokeLocalRadar.Image`, 66,317 B packed / 139,264 B inflated, 58 scripts |
| `Research/JC3Grab/JC3_HUD_WEAPONS.md` + `.json` | the **32 `POI_TYPE_*` constants** (all values), `CreatePoi(type, use_progress_bar, is_minor, label)`, the icon symbol per type |
| `Research/JC3Grab/NAMES.md` §4–§7 | `UIImagePath` → `textures/ui/vehicle_icons/<leaf>.ddsc`, 45/45 fleet bridge, and the explicit **absence of a per-vehicle map marker** |
| `Research/JC3Grab/README.md` | "No per-vehicle map icon exists at all" |

Commands: `uv run python Tools/scripts/bmak_radar.py --check` → `PASS: G3-HUD-RADAR 0 failure(s)`;
`uv run python Tools/scripts/hud_radar_recheck.py --check` → 5 same / 0 differ / 3 no-source.

---

## 2. What BmAK's radar is

`BmGame.upk:HudModuleBespokeLocalRadar.Image` — 66,317 B packed, 139,264 B inflated,
sha256 `f9f622d5a068…`, stage **1024×720 px @ 30 fps**, AS3
`ModuleStruct_Bespoke_LocalRadar.as` (789 lines).

Named clips on its stage (`symbols.csv`, symbol ids in brackets):

| clip | symbol id | role |
|---|---:|---|
| `MasterMovie` | 267 | module root |
| `RadarMovie` | 266 | the radar disc |
| `warning_alert` | 254 | alert art |
| `lockonAndHealthMeter` | 219 | target health/tracker window |
| `lockonStatusTextContainer` | 218 | lock-on state text |
| `LockonMeter` | 207 | lock-on bar |
| `HeavyTankRadiusMovie` | 194 | heavy-tank danger radius |
| `MapBackground` | 171 | the map under the blips |
| `MapPulseTimer` | 170 | the sonar pulse ring |
| `HeavyTankElement` | 116 | the heavy-tank blip class |
| `trackingVehiclePathParent` | 117 | container for tracking dots |
| `trackingVehiclePathDot` | 2 | one path dot |

Plus four non-radar symbols in the same file (`Plant1`, `Plant2_Fake`, `Plant2_Tunnel`,
`Pipes`, ids 17/38/42/34) — set dressing inside the radar art, not icons.

---

## 3. How BmAK selects an icon: a frame number, not a kind

This is the part that matters for the port, and it is decoded:

- one clip, `Master.Radar.Target.Element`, is the blip (`AS3:279`);
- its art is chosen by `gotoAndStop(<frame>)` on that one clip (`AS3:270`);
- each heavy tank has its own element whose frame comes from a per-tank array:
  `HTD_MovieFrame` is assigned `HeavyTankDetailIndices++` per instance (`AS3:25`),
  read back at `AS3:255` (`this.HeavyTankDetailArray[_loc7_ + HTD_MovieFrame]`) and
  applied with `gotoAndStop` at `AS3:270`;
- frame **`-10000` means "keep the previous frame"** (the `AS3:164` block).

So the icon family is a **frame table on one symbol**, and *which frame is a cop, a
tank, a helicopter, or red-versus-green* is symbol content that the export does not
resolve. `UC_UpdateTargetPosition`'s 4th argument is **not** a kind — it is
`Private_VehicleTracker(param4)` → `NumTrackingDots`, the number of
`trackingVehiclePathDot` children (`AS3:311–331`). `UC_SetLockonValue`'s second
argument is an **urgency threshold** (`value > threshold` → `State1`, else `State2`).

**No vehicle-type, colour or elevation switch exists in the module script**: 0 matches
for `kind`, `colour`, `color`, `red`, `green`, `helicopter`, `police`, `military`,
`hack`, `elevation`. That is a negative search result, and it is why §4 is short.

---

## 4. The blip states BmAK actually decodes

Fifteen `UC_*` setters (`RADAR.json`, line numbers from the AS3):

| state | setter | what visibly changes | colour |
|---|---|---|---|
| radar on | `UC_DoIntro()` (460) | intro animation | art |
| radar off / screen away | `UC_DoOutro()` (455), `Radar.gotoAndStop("Offscreen")` (477) | module leaves / offscreen frame | art |
| sonar pulse | `UC_DoPulse(param1)` (510); `AS3:514` `totalFrames - 55 - param1*30` | `MapPulseTimer` frame | art |
| blip position + facing | `UC_UpdateTargetPosition(angle, distance, bearing, dots)` (277) | `x = 80·d·sin a`, `y = −80·d·cos a`, `rotation = bearing·57.3` | art |
| blip heading history | same call, 4th arg | `NumTrackingDots` dots | art |
| map rotation (player-up) | `UC_SetPlayerPosition(angle, x, z)` (563) | `RootNetwork.rotation = angle·57.3` | n/a |
| heavy-tank blip | `UC_PushHeavyTanksToFlash(int, bool)` (164) | `HeavyTankElement` frame via `HTD_MovieFrame` | art |
| heavy-tank radius ring | `HeavyTankRadiusMovie` | ring clip | art |
| lock-on bar | `UC_SetLockonValue(value, threshold)` (360) | `LockonMeter.Bar.Element.scaleX = value`, `visible = value > 0.01` (`AS3:356–357`) | art |
| stationary lock-on | `UC_SetStationaryLockonValue(value)` (342) | the same bar (`AS3:367`) | art |
| target health window | `UC_SetHealthTitle(String)` (394), `UC_SetHealthValue(Number, Boolean)` (399) | `HealthMeter.Bar.Element.scaleX` (`AS3:404`) | art |
| root network (hack) | `UC_SetRootNetwork(String)` (522), `UC_SetRootNetworkOpacity(Number)` (573), `UC_SetRootsPermanentlyVisible(bool)` (497) | named root network shown/tinted by opacity | art |
| mask / zoom | `UC_SetMaskEnormous(bool)` (556) | mask scaled 8× | n/a |
| visual mode | `UC_SetVisualMode(bool, bool)` (470) | **two unnamed booleans — meaning UNKNOWN** | unknown |

**Colour for every one of those rows is "art"**, because the script never sets a
colour. That is the honest answer to "what colours does BmAK's radar use": the module
draws with the art in its frames, and the script carries no colour at all.

---

## 5. The colour that *is* measurable — the vector-art census

The ffdec export wrote **81** shape SVGs for the radar movie. Their solid fills, counted:

| fill | occurrences |
|---|---:|
| `#ffffff` | 1 |
| `#66ff00` | 1 |
| `#00ff00` | 1 |
| `#00cc00` | 1 |

Four distinct fills, all in the white + green family; **no red, orange, blue or amber
fill anywhere in the 81 shapes**. Two limits keep this from being a full palette:

- it is *solid fills only* — gradients and strokes are separate SVG attributes and were
  not counted;
- the movie also carries **72 bitmap `images/`**, which can be coloured and are not
  vector fills at all.

So: the radar's vector art is **white plus three greens**, and any red/green "hacked"
state — the operator's lead — has **no vector support** in this movie. Whether a bitmap
or a native tint supplies it is UNKNOWN (§9, U3).

---

## 6. JC3: where vehicle icon sets live, and what selects one

### 6.1 There is no minimap and no per-vehicle map marker

- **0 hits** for `minimap` / `mini-map` anywhere in `Research/JC3Grab` (the only
  `ToggleStreamingMiniMap` in the project is BmAK's own `RCheatManager` cheat,
  `Research/BatmobileGrab/CONTROLS.md`).
- Of **696** `textures/ui/` textures in `INDEX.jsonl`, the map-related ones are
  `textures/ui/world_map.ddsc`, `textures/ui/dev_map_grid.ddsc`,
  `textures/ui/rom/cimagallo_icon.ddsc` and `textures/ui/rom/region11_icon.ddsc` —
  **no marker, pin, waypoint or faction sprite**.
- `NAMES.md` §2 and §7 state it plainly: *"no per-vehicle file: there is not one
  map-marker texture for vehicles in the index"*, and `README.md` repeats *"No
  per-vehicle map icon exists at all"*.

### 6.2 The icon set that does exist for a vehicle

| set | path | count | key |
|---|---|---:|---|
| vehicle icon (menu / Rebel Drop / garage) | `textures/ui/vehicle_icons/<leaf>.ddsc` | **113** files (incl. `placeholder`) | the entity leaf name |
| store art | `textures/ui/store/…` | 17 | a *different* naming scheme |
| weapon icon (HUD slot) | `textures/ui/weapon_icons/<id>.ddsc` | 110 (69 ids + `_sm` twins) | the weapon id as a string |

**The member that selects a vehicle's icon is `UIImagePath`** on the Rebel Drop item
record, `profile/item.onlinec`: `UIImagePath = v0300_car_kensington_sportsmuscle_civilian_01`,
resolved to `textures/ui/vehicle_icons/<UIImagePath>.ddsc`. The bridge is exact —
**45 of 45** vanilla vehicle items have a name string and **45 of 45** have the matching
icon file, and **no `.gfx` movie contains the leaf, the name hash or the string
`vehicle_icons`**, so the lookup is data-driven.

### 6.3 The icon set on the map/HUD — the POI system

The only per-marker icon machinery JC3 ships is the POI system inside `ui/hud.gfx`
(260 scripts, 1280×720 @ 30 fps, 9 external DDS atlases, largest `hud_i46.dds`
1,044,608 B at 1024×1020).

```
CreatePoi(type, use_progress_bar, is_minor, label)
```
`hud_code/poi.as` switches on `type` and picks `m_Icon` for that type. The 32
constants, all values, from `JC3_HUD_WEAPONS.json`:

| # | constant | # | constant |
|---:|---|---:|---|
| 0 | `POI_TYPE_LABEL` | 16 | `POI_TYPE_DUAL_TETHER` |
| 1 | `POI_TYPE_ROM_START_WINGSUIT` | 17 | `POI_TYPE_LABEL2` |
| 2 | `POI_TYPE_ROM_START_LAND_RACE` | 18 | `POI_TYPE_GRENADE` |
| 3 | `POI_TYPE_ROM_START_SCRAPYARD` | 19 | `POI_TYPE_MISSION` |
| 4 | `POI_TYPE_ROM_START_SPEED` | 20 | `POI_TYPE_OPEN_WORLD` |
| 5 | `POI_TYPE_ROM_START_DELIVERY` | **21** | **`POI_TYPE_LOCK_ON_TARGET`** |
| 6 | `POI_TYPE_ROM_START_SHOOTING` | 22 | `POI_TYPE_WEAPON_PICKUP` |
| 7 | `POI_TYPE_ROM_START_DESTRUCTION` | 23 | `POI_TYPE_CHOP_SHOP` |
| 8 | `POI_TYPE_ROM_START_AIR_RACE` | 24 | `POI_TYPE_LOCKED` |
| 9 | `POI_TYPE_ROM_START_SEA_RACE` | 25 | `POI_TYPE_CHALLENGE` |
| 10 | `POI_TYPE_USER_PLACED` | 26 | `POI_TYPE_ROM_START_FLIGHT_MASTER` |
| 11 | `POI_TYPE_HEAT_RADIO` | 27 | `POI_TYPE_ROM_START_SKY_TERROR` |
| 12 | `POI_TYPE_ENCOUNTER` | 28 | `POI_TYPE_WEAPON_RETICLE_AUTO_WINGSUIT` |
| 13 | `POI_TYPE_ENCOUNTER_START` | 29 | `POI_TYPE_ROM_START_MECH_ARENA` |
| 14 | `POI_TYPE_WEAPON_RETICLE_AUTO` | 30 | `POI_TYPE_ROM_START_SCRAPHEAP` |
| 15 | `POI_TYPE_KILL_TARGET` | 31 | `POI_TYPE_ROM_START_ATTACKWAVE` |

**There is no `POI_TYPE` for a vehicle, a police car, a tank or a helicopter.** The 32
types are mission/label/reticle kinds; the one that draws a rotating reticle is 21,
`POI_TYPE_LOCK_ON_TARGET` → `MCI_icon_and_label.MCI_icon.MCI_lock_on.MCI_reticle`,
one turn per **1.5 s**.

What a POI does and does not expose (decoded in `poi.as` / `hud.as`):

| property | JC3 member | value |
|---|---|---|
| icon by type | `type` arg of `CreatePoi` → `m_Icon` | 32 types, no vehicle type |
| size | `m_IconScale` → `m_Icon.scaleX/scaleY` | a **ratio**; no absolute pixel size field |
| direction | `ARROW_*` enum | **8-way**: rotations `[-135, -90, -45, 0, 45, 90, 135, 180]`; `ARROW_POINT_AT = 1` is declared but **has no case**, so no continuous bearing |
| pulse | `m_Flash` | alpha tween; no frame-counted pulse of BmAK's shape |
| position | `poi.x = …` set by the **caller in stage pixels** (`hud.as:7861, 7878, 7895`) | no world→pixel mapping inside the movie |
| colour | **none** | a POI has no colour member; colour is whatever the atlas art is |

And the caller is native: **0 `CreatePoi(...)` call sites** in the movie, so a mod
cannot create a POI from the entity graph — this is the same native-caller gap the
lock-on card (G2-25) recorded.

---

## 7. State → icon and colour: the mapping

Two different questions are answered here, and they must not be merged: *what the
entity can select* (§7.1) and *what the HUD can draw* (§7.2).

### 7.1 Entity-side: the icon a car shows in a menu

| BmAK state | JC3 carrier | icon | colour |
|---|---|---|---|
| drivable car in Rebel Drop / garage | `UIImagePath` on `profile/item.onlinec` | `textures/ui/vehicle_icons/<leaf>.ddsc`, 18,688 B | the art in that file — **not decoded**, and every vanilla icon is the same size/format, one ADF texture |
| Batmobile renamed to a new leaf | add `<leaf>.ddsc` + string pair | picked up by name, no movie change | ours to draw |
| missing / placeholder | `textures/ui/vehicle_icons/placeholder.ddsc` | fallback | art |

This is the only icon selector the entity data owns, and it is **menu/garage, not
radar** — the same texture does not appear on the map.

### 7.2 HUD-side: blips

| BmAK radar state | nearest JC3 element | icon | colour |
|---|---|---|---|
| plain target blip (`Element` frame) | wait — no vehicle POI type exists | none for vehicles | — |
| target with facing | `POI_TYPE_LOCK_ON_TARGET` (21) | `MCI_lock_on.MCI_reticle`, rotates 1.5 s/turn | art (reticle) |
| lock-on bar (`LockonMeter`) | POI progress bar (`use_progress_bar` arg) | bar on the same POI | art |
| target health window | none | — | — |
| heavy-tank blip + radius | none | — | — |
| tracking path dots | none | — | — |
| sonar pulse (`MapPulseTimer`) | `m_Flash` alpha tween only | — | — |
| hack/tracked (root network) | none | — | — |
| player arrow | none (the player arrow is not one of the 32 POI types) | — | — |

So on the HUD side the honest count is: **1 of 9 states has a real JC3 carrier**
(lock-on, type 21), 1 partial (a pulse as an alpha flash), and 7 have nothing — which
matches `HUD.md` §6's disposition row: *"radar, target lock-on, missile boxes, alerts,
threat meter, boss bar → none — out"*.

### 7.3 Colour, stated without invention

JC3 selects no colour: a POI has no colour field, and the icon art lives in the `hud_i*`
atlases. Therefore **we cannot say "state X is red, state Y is green" on the JC3 side
from any file**. The two colour facts that *are* measured are BmAK's (§5: white +
`#66ff00`/`#00ff00`/`#00cc00`) and the absence of red in its vector art.

---

## 8. What we would change, and where

Nothing here is approved or applied. Two independent levers:

1. **Menu icon (data, safe).** Drop `textures/ui/vehicle_icons/<leaf>.ddsc` (18,688 B,
   ADF) and set the item's `UIImagePath` to the same leaf. Three things must agree: the
   `.ee` leaf, the item `Name`/`UIName`, and the string pair in
   `profile/online.stringlookup`.
2. **Radar blips (code/HUD, not data).** No entity member exists; the only route is a
   `ui/hud.gfx` patch adding a POI type, or a script hook that calls `CreatePoi` — both
   outside what the entity graph can do, and both unproven. Until then the stated
   compromise stands: no rotating per-target arrows, no heavy-tank ring, no elevation.

---

## 9. The five-minute experiment

1. Take the donor `.ee` and clone it under a new leaf; do **not** rename the item.
2. Add a dummy `<leaf>.ddsc` for the new leaf next to the vanilla ones.
3. Open Rebel Drop. If the new art appears, `UIImagePath` is proven to be the selector
   with no movie work (it should — the 45/45 bridge already implies it).
4. Then, for the radar, read one `CreatePoi` call site in `hud.as` and log its `type`
   argument at runtime — one run tells us whether any shipped code passes a vehicle-ish
   type, which is the only way a blip gets made without a patch.

---

## 10. UNKNOWNs

| # | question | status |
|---|---|---|
| U1 | frame → art table for `Master.Radar.Target.Element` | **UNKNOWN** — the AS3 only passes frame numbers |
| U2 | colour of each blip frame | **UNKNOWN** — art content; only the vector fill census (§5) is measured |
| U3 | is the "hacked red / tracked green" state real? | **UNKNOWN** — 0 colour identifiers in the script, 0 red fills in the vector art |
| U4 | per-icon pixel sizes | **UNKNOWN on both sides** — no size field in BmAK, only `m_IconScale` ratio in JC3 |
| U5 | `MapPulseTimer` period | **UNKNOWN** — `totalFrames` is symbol content |
| U6 | `UC_SetVisualMode(bool, bool)` semantics | **UNKNOWN** — two unnamed booleans |
| U7 | world radius in metres | **UNKNOWN** — 80 px per radar unit is decoded, the divisor is native |
| U8 | which `.gfx` symbol draws the menu icon | **UNKNOWN** — no movie contains the leaf or `vehicle_icons` |
| U9 | any shipped `CreatePoi` with a vehicle type | **UNKNOWN** — 0 call sites in the movie; native side not read |
| U10 | does a per-vehicle map marker exist outside the index | **no** — 0 marker-like textures among 696 `textures/ui/`, stated in three separate documents |

---

## 11. Change record

- **Intended change:** none to game data.
- **File written:** `tmp/freebuff/reports/radar-minimap-icon-plan.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete the file. Nothing else was touched.

## 12. Checks run

- `Working/HUD/RADAR.json` re-read: 15 setters with AS3 lines 164–573, stage
  1024×720 @ 30 fps, `px_per_distance_unit` 80, `tracker_counts_dots: true`;
- `symbolClass/symbols.csv` read directly: 16 entries, symbol ids 0–267 as quoted;
- fill census: `grep -ho 'fill="#…"' shapes/*.svg | sort | uniq -c` over **81** SVGs
  → the four fills in §5 (1 each);
- POI constants: all **32** read out of `Research/JC3Grab/JC3_HUD_WEAPONS.json` and
  listed with their numeric values, not summarised;
- the "no vehicle POI / no minimap / no marker sprite" claims are negative search
  results over `Research/JC3Grab/*.md`, `INDEX.jsonl`'s 696 `textures/ui/` paths, and
  the three documents that assert the absence — reported as absences, not as guesses;
- **not verified:** nothing was loaded into the game. Neither movie was mounted and no
  POI was created.
