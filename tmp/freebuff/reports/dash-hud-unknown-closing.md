# Dash HUD gauges — walking the plan's UNKNOWN list against the three sources

Read: `tmp/freebuff/reports/dash-hud-gauges-plan.md` (the whole file, `:62-78` for the gauge table,
`:80-84` for the colour note, `:129`, `:190`, `:193`, `:229-250` and `:254-262` for the numbered
UNKNOWNs), `Research/BatmobileGrab/HUD.md` (350 lines), `Research/BatmobileGrab/HUD_SPEC.json`
(376 lines) and `Working/Translation/T6_HUD_CAMERA.md` (202 lines). Nothing was edited: the plan,
`HUD.json` and `HUD_SPEC.json` are as they were, and no build artefact was touched.

Machine-readable: `Working/Prep/dash_hud_unknowns.json` — **24 items in plan order**, fields
`item, search_terms, answer_or_null, answer_source_path, answer_source_line, status`, plus
`plan_line`, `matches_per_source`, `closest_evidence_*` and `settled_by`.

## 0. Count

| result | count |
|---|---:|
| UNKNOWN items walked | **24** |
| **CLOSED** (a cited line states the value) | **1** — N19, the cooldown-state pinning |
| **STILL_UNKNOWN** | **23** |
| colour items | 14 (all STILL_UNKNOWN) |
| numeric / binding / layout items | 10 (1 closed, 9 open) |

The plan's UNKNOWNs are 14 **colour cells** (one per gauge row of the table at `:62-78`, each marked
`UNKNOWN` in the colour column) plus 10 numbered or inline unknowns. Those 24 are the list walked
here; the plan has no 25-row table elsewhere, so 24 is the count its own text supports.

## 1. The one item a source closes

**N19 — "pin the 5 cannon-cooldown states to JC3 `weapon_cooldown` fractions"** (plan `:250`, §8.4).

`Working/Translation/T6_HUD_CAMERA.md:53` (row T-HUD16) states the value outright:

> `cooldown = BmAK state / 4 (state 0…4 -> 0.00, 0.25, 0.50, 0.75, 1.00)` … `-1` hides
> `MCI_radial_loader_cooldown`

**Status CLOSED** — the line gives the pinning, so no derived proposal is needed.

**It contradicts the plan's own §8.4** (`:246-250`), which proposes `Ready → −1` and states `1…4 →
0.75, 0.5, 0.25, 0.0`. T6 pins the opposite direction (`state 0 → 0.00`, rising to `1.00`) and keeps
`−1` only for "hidden at rest". A build step must pick one: T6 is the cited value, the plan is a
proposal, and T6 itself flags the direction as "a Q check, not a file fact" (`:53`). This note closes
the item per the brief's rule; it does not settle which mapping the build should use, and the plan
was not edited.

## 2. The 23 that stay UNKNOWN

### 2.1 The fourteen colours

Search terms: `colour`, `color`, `0xRRGGBB`, `rgb(`, `tint`, `SetColorTransform`. Token hits across
all three sources: **HUD.md 0, HUD_SPEC.json 0, T6_HUD_CAMERA.md 0** (the only `0x…` strings in T6 are
code addresses such as `0x140113480`, not RGB triples). No line in any of the three states a colour,
so every colour cell stays open — the plan's claim at `:80` holds against all three files.

| id | item | plan line | status |
|---|---|---|---:|
| C01 | colour of the boost gauge | `:62` | STILL_UNKNOWN |
| C02 | colour of the boost fill (`FillMovie` + `Cap`) | `:63` | STILL_UNKNOWN |
| C03 | colour of the boost badges (`Upgrade1/2`) | `:64` | STILL_UNKNOWN |
| C04 | colour of the health gauge | `:66` | STILL_UNKNOWN |
| C05 | colour of the health fill (`Healthbar.Bar`) | `:67` | STILL_UNKNOWN |
| C06 | colour of the armour fill | `:68` | STILL_UNKNOWN |
| C07 | colour of the damage number | `:69` | STILL_UNKNOWN |
| C08 | colour of the cooldown reticle | `:71` | STILL_UNKNOWN |
| C09 | colour of the energy charges | `:73` | STILL_UNKNOWN |
| C10 | colour of the mode selector | `:74` | STILL_UNKNOWN |
| C11 | colour of the combo meter | `:75` | STILL_UNKNOWN |
| C12 | colour of the XP bar | `:76` | STILL_UNKNOWN |
| C13 | colour of the clock | `:77` | STILL_UNKNOWN |
| C14 | colour of the winch meter | `:78` | STILL_UNKNOWN |

Settled by: the decompiled `HudModuleBatmobile` AS3 colour constants, the GFx tag stream's
`DefineShape` fills, and the `Image_I1*.tfc` atlases — all outside the repo (`HUD.md:39` says the art
streams from the `.tfc` companions and was not inventoried).

### 2.2 The ten numeric / binding / layout items

| id | item | plan line | closest evidence found | status |
|---|---|---|---|---:|
| N15 | local transform of `Health.Healthbar.Bar` (plan: "MATRIX3D, not decoded") | `:67` | **none** — 0 hits for `Healthbar`/`MATRIX3D` in all three | STILL_UNKNOWN |
| N16 | JC3 vehicle-health setter name | `:190` | `HUD.md:278` lists only `hud_code/health/*`, `MCI_vehicle` and "damage paint/health managers"; `HUD_SPEC.json:315` opens `vehicle_api`, whose 11 members contain no health function | STILL_UNKNOWN |
| N17 | which `reticle_shape` a vehicle cannon gets | `:193` | `T6:51` (T-HUD14) `E_RETICLE_CANNON = 8`, but "no file maps … to a vehicle cannon" | STILL_UNKNOWN |
| N18 | whether BmAK art can be imported into `ui/hud.gfx` | `:239` | **none** — 0 hits for `BoostMovie`/`import`/`sprite` in all three | STILL_UNKNOWN |
| N19 | cooldown states → fractions | `:250` | `T6:53` (T-HUD16) states `state / 4` | **CLOSED** |
| N20 | armour tiers' native source (`max` above 1) | `:129` | `T6:23` (T-HUD4): JC3 has no armour bar and no armour field; nothing on BmAK's native source | STILL_UNKNOWN |
| N21 | which caller drives `InitVehicleNitrous`/`UpdateVehicleNitrous` | `:233` | `T6:87` "need a caller"; `HUD.md:335` "the caller is game code, not the entity graph" | STILL_UNKNOWN |
| N22 | the Vulcan heat bar's scale | `:72` | `T6:54` (T-HUD17) restates the absence (no setter, no JC3 argument) and gives no scale | STILL_UNKNOWN |
| N23 | whether a private `ui/hud.gfx` copy is the only way to keep `MCI_speedo` hidden | `:229` | `HUD.md:286` names `MCI_speedo` as JC3's speedo; no source states the `SetVisibilities()` rule (plan-only) | STILL_UNKNOWN |
| N24 | what `UC_SetColorTransform`'s six parameters tint | `:82` | **none** — `SetColorTransform` appears 0 times in all three; `HUD_SPEC.json` carries the signature of `UC_SetColorTransform` only if present in `uc_setters` (it is not) | STILL_UNKNOWN |

Where each would be settled (also in the JSON as `settled_by`):

| id | what would close it |
|---|---|
| N15 | the movie's `PlaceObject`/`DefineSprite` tree (`ffdec -dumpSWF`) for `Health.Healthbar.Bar` |
| N16 | the native HUD binding that calls `hud_code/health/*` — `HUD_SPEC.json`'s 11-member `vehicle_api` has no health entry, so the movie alone cannot name it |
| N17 | the native caller of `UpdateWeaponReticle`, or `Research/JC3Grab/JC3_HUD_WEAPONS.json` gaining a shape→weapon map |
| N18 | an SWF/AVM tag comparison of the two movies (`HUD.md:316` opens the question list; none of its entries names art import) |
| N20 | an `RVehicle` armour field in the BmSDK headers — neither `HUD.md`'s §4.1 contract nor `HUD_SPEC.json → bmak.health_contract` names one |
| N21 | the game-side HUD caller in native code — `HUD.md:335` says it is game code, not an entity member |
| N22 | the `Batmobile_Cannon_V2` script field domain; no file read here states a scale |
| N23 | a test install of a private `ui/hud.gfx` (R7 route), forbidden by the test ban |
| N24 | the decompiled `UC_SetColorTransform` body (`HUD_INTERFACES.json` holds the signature only) |

## 3. What the three sources *did* add, beyond closing one item

- `T6_HUD_CAMERA.md:53` also states the JC3 rotation rule (`rot = cooldown × 360` over
  `MCI_mask_0_50` / `MCI_mask_50_100`, `−1` hides the loader) — the plan had this from G2-25, and T6
  confirms it independently.
- `T6:51` (T-HUD14) and `T6:54` (T-HUD17) confirm two *absences* the plan asserts (reticle binding,
  heat bar) rather than contradicting them; an absence is recorded here as STILL_UNKNOWN, not CLOSED,
  because neither line states the value the item asks for.
- `HUD.md` §4.1 and `HUD_SPEC.json → bmak.health_contract` agree on every health number the plan
  already quotes (proportion, armour tier 5, pulse 0.2, 0.05/frame, 2 s); no new number, no conflict.

## 4. Files, revert

**Written:** `Working/Prep/dash_hud_unknowns.json` and this report. Nothing else.
**Untouched:** `tmp/freebuff/reports/dash-hud-gauges-plan.md`, `Research/BatmobileGrab/HUD.json`,
`Research/BatmobileGrab/HUD_SPEC.json`, `HUD.md`, `T6_HUD_CAMERA.md`.

**Revert:** delete the two files above. No source, movie or build file was modified.
