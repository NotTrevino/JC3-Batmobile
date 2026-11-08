# Hacker gadget visuals — beam, target outline, success feedback

**Status: research note.** Read from local decoded records only (AGENTS.md). The beam and the success
pop are measured in BmAK; the **target outline has no world-space asset in BmAK's files**, and JC3 has
no hack effect at all — both are called out instead of being filled in.

Sources: `Research/BatmobileGrab/WEAPONS.md` §6 (`RBatmobileAllegianceSwitcher` / `Drone_Hacker`),
`PARTICLES_FEATURES.md` (hacker systems), `MATERIALS.md` (`DroneHacker_Beam_INST`), `MECHANICS.md`
(gadget component rows), `HUD.md` (`HudModuleTargets`, `RHudModuleHackingMode`),
`Research/JC3Grab/GADGETS_HACK_TRACK.md` (field→JC3 map, `.effc` census), `HACKABLES.md` (the one real
hack), `JC3_HUD_WEAPONS.md` (POI types, lock-on reticle).

---

## 1. BmAK: the three things it shows, itemised

`RBatmobileAllegianceSwitcher` on `Drone_Hacker` (Batmobile, MK2, Funhouse — **all 13 fields identical**,
39 comparisons, 0 differences). Cooldown `WeaponCoolDown` = **1.0 s**.

### 1.1 The beam

| field | value |
|---|---|
| `BatmobileHackerEffect` | `Particles.DroneHacker_Beam` |
| `BatmobileHackerEffectHvyTank` | `Particles.CobraHacker_Beam` |
| `DroneHackerMaterial` | `Materials.DroneHacker_Beam_INST` (instance parameter **Green = 1.0025**) |
| `HackerEffect` | ArrayProperty, **6 items** → six beam attachment slots (`DroneHackerEffect0…5`) |

| system | emitters | lifetime | size (cm) | colour (start) | material |
|---|---:|---:|---|---|---|
| `DroneHacker_Beam` | 2 (beam×2) | **4 s** | **[35, 0, 0]** | **`[2.0, 0.0, 1.0]`** (magenta, HDR) | `Materials.DroneHacker_Beam_INST` |
| `CobraHacker_Beam` (heavy tank) | 2 (beam×2) | **10 s** | **[35, 0, 0]** | `[2.0, 0.0, 1.0]` | same |

So: a **35 cm-wide magenta beam**, held for **4 s** on a drone and **10 s** on a heavy tank, fired from
up to six sockets. It is a beam/tracer system, not a projectile.

### 1.2 The target outline — the honest result

**There is no world-space target outline in BmAK's decoded assets.** What exists is HUD-side:

| carrier | what it gives |
|---|---|
| `HudModuleTargets` element names `Tank_Hack_BOMB`, `Tank_Hack_EMP`, `Tank_Hack_FRIEND` | three *targeted-hack* marker names on the targets module |
| `HudModuleTargets` family `VehicleMissileTarget*`, `batmobile_lockon`, `batmobile_aim`, `missile_lockon_square_anim` | the crosshair/lock family around them |
| `RHudModuleHackingMode` | a hacking-mode HUD class — **no movie ships for it** in this install; its cached calls resolve to nothing |
| `xrayBatmobile_MASTER` / `xrayMetal_Batmobile_INST` | X-ray materials for the **Batmobile itself**, not for a hack target — wrong owner for this feature |

The marker names are real, the drawing is not decoded. So "what the target outline looks like" is
**UNKNOWN**; only the three marker identities (`BOMB` / `EMP` / `FRIEND`) and the fact they live on the
targets HUD module are measured.

### 1.3 Success feedback

| field | system | emitters | lifetime | size (cm) | scale over life |
|---|---|---|---:|---|---|
| `SuccessfulHackEffect` | `DroneHacker_Success` | 1 (sprite) | **0.5 s** | `[100, 100, 0]` | up to **100×** |
| `SuccessfulHackEffectHvyTank` | `CobraHacker_Success` | 3 (sprite×2) | 0.5 s | `[100, 150, 0]` … `[200, 200, 0]` | up to **50×** |

Both reuse the same magenta beam material, so the success pop is the same colour family as the beam.
Audio on success exists as a field (`SucessfullHackSound` = `Engine.Play_Batmobile_DroneHacker_Hacked`)
but the event is `missing-object` in the grab.

---

## 2. JC3: closest carriers

| JC3 thing | fact | source |
|---|---|---|
| hack-named `.effc` | **0** paths exist; the whole census found 1 hack in the fleet | `GADGETS_HACK_TRACK.md` §1 |
| closest beam `.effc` | `dlc/bavarium_sea_heist/effects/jc_weapons/lightning_gun/lightning_gun_destruction_beam.effc` and `effects/jc_weapons/sungun/destructon_beam.effc` — both **0 vehicle carriers** | ″ §2 |
| attachment mechanism | `SAttachedEffect` with `Effect` + `Usage` (5,342 objects in 232 graphs) | ″ |
| success event | none — JC3 has no "hack succeeded" event; a second attachment must be driven by the weapon that finishes the hack | ″ |
| material instance in an effect | impossible — a JC3 `.effc` has no material-member path; colour must be authored into the effect | ″ |
| the one real hack | `w501_turret_sam_v2.ee`: `CInteractionGraph` + `rico_contextact_hack_sam*.anim` + 2 `CInteractionTrigger` volumes | `HACKABLES.md` §2 |
| target marker | HUD POI: `CreatePoi(type, use_progress_bar, is_minor, label)`, 32 `POI_TYPE_*`; `POI_TYPE_LOCK_ON_TARGET = 21` draws one reticle rotating 360° per **1.5 s** | `JC3_HUD_WEAPONS.md` § |
| vehicle→POI bridge | `CAimPOIWeaponComponent` on 11 builds; no decoded link from it to the HUD POI | ″ |
| outline | **none** — no outline/marker world material was found; the lock-on reticle is the only target graphic | `GADGETS_HACK_TRACK.md` §4.3 |

---

## 3. Pairing, item by item

| BmAK item | JC3 closest carrier | match | what we add |
|---|---|---|---|
| `DroneHacker_Beam` (35 cm, 4 s, magenta) | `lightning_gun_destruction_beam.effc` attached by `SAttachedEffect` / `Usage Fire` at the drone's beam socket | mechanism matches, **asset does not exist** | author a beam `.effc` clone: 35 cm ribbon, 4 s life, colour `[2, 0, 1]`, Green 1.0025 |
| six beam sockets (`HackerEffect` 6 items) | six `SAttachedEffect` rows on the weapon entity | shape matches | add six attachment rows, one per socket |
| `CobraHacker_Beam` (35 cm, **10 s**) | same slot, different effect path | no analogue | author a second beam variant (10 s) |
| `DroneHacker_Success` (0.5 s sprite, 100 cm, 100×) | second `SAttachedEffect` | mechanism matches, no event exists | author a 0.5 s pop effect and trigger it from the hack weapon |
| `CobraHacker_Success` (0.5 s, 200 cm, 50×) | same slot | no analogue | author the second success variant |
| `DroneHackerMaterial` (Green 1.0025) | no material member in a JC3 `.effc` | **impossible as-is** | bake the tint into the effect's texture/params |
| target outline (BmAK `Tank_Hack_*` markers) | HUD POI type 21 (`POI_TYPE_LOCK_ON_TARGET`) + `CreatePoi(...)` | partial: reticle only | add a POI on the target with the `use_progress_bar` flag for the hack timer, plus a label; **author** an outline shader/quad if the Batmobile look needs one — JC3 has none |
| `RHudModuleHackingMode` panel | `ui/hud.gfx` POI + label | no dedicated module | reuse the POI label / progress bar; a hacking panel has to be authored |
| success sound | entity audio module (`.bnk` + audio objects) | not a tune member | wire an audio object on the weapon entity |

**Not carried by either game's data:** the hack duration, the disable outcome, and the target's
appearance change. BmAK states none of them; JC3's only hack is a local context act whose ownership
effect is UNKNOWN (`HACKABLES.md` §9).

## 4. Values we use

| # | setting | value | source |
|---|---|---|---|
| 1 | beam width | **35 cm** | BmAK `start_size [35,0,0]` |
| 2 | beam life | **4 s** (drone) / **10 s** (heavy tank) | BmAK lifetimes |
| 3 | beam colour | **`[2.0, 0.0, 1.0]`** magenta, parameter Green **1.0025** | BmAK start colour + material instance |
| 4 | beam sockets | **6** | BmAK `HackerEffect` array, 6 items |
| 5 | success pop | **0.5 s**, 100 cm sprite, scale to 100× (heavy: 200 cm, 50×) | BmAK success systems |
| 6 | cooldown | **1.0 s** → JC3 `fire_rate` 1.0 | BmAK `WeaponCoolDown` |
| 7 | target marker | `POI_TYPE_LOCK_ON_TARGET` (21), `use_progress_bar = 1`, label = target name | JC3 HUD API |
| 8 | reticle spin | **1.5 s / 360°** | JC3 `hud_code/poi.as` |
| 9 | target outline | **not set** — no asset in either game | — |
| 10 | hack duration | **not set** — UNKNOWN both sides | — |

## 5. Checks run for this note

* Re-read `RBatmobileAllegianceSwitcher` (§6) and confirmed 13 fields × 3 packages, 39 comparisons.
* Re-read `PARTICLES_FEATURES.md` hacker rows for beam widths, lifetimes, colours and success sizes.
* Re-read `MATERIALS.md` `DroneHacker_Beam_INST` (Green 1.0025) and confirmed there is no victim-outline
  material owned by a hack target.
* Re-read `HUD.md` for the `Tank_Hack_BOMB/EMP/FRIEND` names and the missing `RHudModuleHackingMode` movie.
* Re-read `GADGETS_HACK_TRACK.md` (`.effc` 0 hack / 2 beam / 3 marker), `HACKABLES.md`, `JC3_HUD_WEAPONS.md`.
* No game process started; `Research/` was read only.
