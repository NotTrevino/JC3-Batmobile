# Audit — HUD cluster plan against HUD.md, HUD_SPEC.json and G3-HUD-CLUSTER.md

**Plan audited (not edited):** `tmp/freebuff/reports/hud-cluster-closest-system-plan.md`.
**Sources:** `Research/BatmobileGrab/HUD.md` (sections cited), `Research/BatmobileGrab/HUD_SPEC.json`
(`bmak` / `jc3` blocks) and `tmp/freebuff/reports/G3-HUD-CLUSTER.md`.
**Method:** each element/setter/value the plan names was looked up in those three files. "Plan statement"
is quoted or paraphrased; "source line" is the section/JSON key that carries it. Values the plan takes
from `Research/JC3Grab/JC3_HUD_WEAPONS.md`, the ledger or the build are out of scope and marked so.
Verdicts: **MATCH** = a named source says it; **MISMATCH** = source says something different;
**UNSOURCED** = none of the three files contains it.

---

## Claim table

| element or value | plan statement | source line | result |
|---|---|---|---|
| `UC_SetBoostLevel` | `(level:int, upgradeLevel:int)`; gauge shown while `level < 100`; hidden by `UC_HideBoostGauge` at ≥100 unless `bHoldBoostOnscreenUntilUsed` | `HUD.md:§4` (setter table, `0…100, upgradeLevel`); `HUD_SPEC.json` `bmak.uc_setters` → `UC_SetBoostLevel` `param1:int, param2:int`; G3 §2 | **MATCH** (the `bHoldBoostOnscreenUntilUsed` flag is G3-only, present in G3 §2) |
| boost fill clip | 102 frames, `gotoAndStop(level + 1)`, scale-y 0.011 → 1.0, bottom-anchored, `Cap` y 9.5 → −182.5, 101 steps | G3 §2 (bullet 2) | **MATCH** |
| `Upgrade1` / `Upgrade2` badges | at (−10.0, 96.3) / (−10.5, 100.6); 65 frames each; labels `Normal`/`Charging`; visible when `upgradeLevel > 0` / `> 1` | G3 §2 (bullet 3) — positions, 65 frames, labels, visibility | **MATCH** |
| "3 badge states (0, 1, 2)" | plan §3 derives three states from the two badges | G3 gives two badges with `> 0` / `> 1` visibility; no state count | **MATCH as derivation** (not a decoded count) |
| armour fill | `Math.max(0, health − 1)` onto `ArmourForeground` | `HUD.md:§4.1` (armour fill row); `HUD_SPEC.json` `bmak.health_contract.armour_fill` | **MATCH** |
| armour tiers | `max > 1` selects `Armour<n>`, `n = int((max − 1) * 4)` → 5 labels/tiers | `HUD.md:§4.1` (armour tier row); `HUD_SPEC` `armour_tier`, `armour_tier_count: 5`, `armour_tier_labels`; G3 §3 | **MATCH** |
| health proportion | "the BmAK health proportion is 0..2 in effect" | `HUD_SPEC` `health_is: "a proportion, not hit points: 1.0 is one full bar"`; `max_is: "the bar's ceiling; above 1 it adds armour tiers"`; G3 §3 gives 5 tiers but no upper bound of 2 | **UNSOURCED** — the 2.0 ceiling is nowhere in the three files |
| `max_health` 36,000 | plan §2: "`max_health` 36,000 (T-DM9, B-09) is what makes `h − 1` reach the armour band" | no entry in HUD.md / HUD_SPEC / G3 | **UNSOURCED** (ledger/build fact, not a HUD source) |
| damage readout | `UC_SetImpactDamageFlash(part, x, y, frames)`, `DamageEffectMovie` at `StageWidth*x` / `StageHeight*y`, `rotationY = ±60`, text `String(frames)` | G3 §3 (last paragraph) — `(part, x, y, frames)`, StageWidth/Height, ±60, `String(frames)` | **MATCH to G3**; **MISMATCH to HUD.md** — `HUD.md:§4` lists the setter as `part, amount, duration, frames`, and `HUD_SPEC` `uc_setters` gives `param2:Number, param3:Number, param4:int` (no x/y names) |
| damage flash bar-level | `BG`'s `Pulse`/`Idle` pair on the < 0.2 pulse | G3 §3 ("the bar-level damage flash is `BG`'s `Pulse`/`Idle` pair on the < 0.2 pulse"); `HUD_SPEC` `bmak.frame_labels` contains `Pulse`, `Idle` | **MATCH** |
| speedometer is not BmAK's | 0 of 252 `UC_*` setters speed/rev/gear-shaped; 0 speed tokens; `bDebugSpeedometer` false in both configs | `HUD.md:§7` (252 setters; `bmak_speedometer.py`), `HUD.md:§8` (only the debug readout, off in both configs); G3 §4 | **MATCH** |
| JC3 speedo constants | `SPEEDO_DEGREES = 250`, `SPEEDO_SMOOTHING_TIME = 0.05` | `HUD_SPEC.json` `jc3.constants` (both); `HUD.md:§6` table (both) | **MATCH** |
| `SetVisibilities` / `HideVehicleUi` | `SetVisibilities()` is literally `MCI_speedo.visible = true`; `HideVehicleUi()` hides `MCI_speedo`, `MCI_speedometer`, `MCI_nitro_meter`, `MCI_jump_meter`, `MCI_bavarium_shield` | G3 §4 (same sentence and list) | **MATCH** |
| `SetVehicleType` | writes only `hud_kph`/`hud_knots`, touches no `visible` | G3 §4; `HUD_SPEC` `jc3.vehicle_api` gives `SetVehicleType(type:int)` only | **MATCH** |
| meter call sites | `InitPrimaryMeter` 1 call site, `SetPrimaryMeterValue` 0 | G3 §4 ("`InitPrimaryMeter` 1 call site, `SetPrimaryMeterValue` 0, `SetVehicleType` 0") | **MATCH** |
| JC3 vehicle types | LAND 0, AIRPLANE 1, HELICOPTER 2, SEA 3; plan adds `TYPE_BATMOBILE = 4` | G3 §4 gives those four numbers; `HUD_SPEC` `jc3.vehicle_types` lists the four names in a different order, **no numbers** | **MATCH** (numbers from G3); "the movie never receives 4" is the plan's inference |
| JC3 movie size / scripts | 1280×720, 260 scripts, 9 DDS atlases | `HUD.md:§6` ("260 AS3 scripts, 1280×720 … nine external DDS atlases"); `HUD_SPEC` `jc3.scripts: 260`, `MovieWidth 1280`, `MovieHeight 720` | **MATCH** |
| BmAK stage | 1024×768 SWF surface, 1024×720 stage, 30 fps, `TickDeltaTime 0.033` | `HUD.md:§4` (first line); `HUD_SPEC` `constants.StageWidth 1024`, `StageHeight 720`, `MovieWidth 1024`, `MovieHeight 768`, `TickDeltaTime 0.033` | **MATCH** |
| clip transforms | `Health` −479.228/−328.300; `BoostMovie` −452.867/65.550; `Combo` −460.237/−263.250; `RemoteInterface` −525.275/225.000; yaw 10°–26°, right group −38°/−40° | G3 §1 table — every number and yaw | **MATCH** |
| remap to 1280×720 | `(x', y') = (640 + 1.25·x, 0.9375·(384 + y))`; 40.965/52.219, 73.916/421.453, 64.704/113.203, −16.594/570.938 | derived from G3 §1: surface 1024×768, centre (512, 384), `screen = (512+x, 384+y)`, JC3 1280×720 ÷ 1024×768 = 1.25 / 0.9375 | **MATCH** (arithmetic re-checked on all four rows: exact to 3 dp) |
| depth error | "z ≤ 56 against a focal length of order 10³, < 1 %" | G3 §1 table has z 56.890 / 51.171 / 36.326, but G3's prose says "the z values (**<= 25**)" | **MISMATCH to G3's prose, MATCH to G3's table** — the plan's 56 is the right number; G3's sentence is stale |
| `Cap` `Decrease` duration | "`Cap`'s `Decrease` label runs 65 frames = 2.167 s at 30 fps" | `HUD.md:§4` label list has `Decrease`/`DecreaseToZero`; G3 §2 says `SetBoostBarDecreasing` plays `Cap`'s `Decrease` — **no frame count**; the 65 frames in both sources belong to `Upgrade1/2` | **UNSOURCED / likely MISMATCH** — the 65-frame figure is the badges', not the `Cap` label's |
| 0.05 sweep, 5 tiers, 102-frame fill | taken as read in the plan's preamble | `HUD_SPEC` `max_change_per_frame 0.05`, `full_sweep_seconds 0.6667`, `armour_tier_count 5`; G3 §2/§3 | **MATCH** |
| `ch1040` | 1-frame clip in `BoostMovie`, identity UNKNOWN, no `SymbolClass` entry | G3 §UNKNOWNs (first bullet) | **MATCH** |
| `MCI_radial_loader_cooldown`, `SetCooldownRotation`, masks, `cooldown.rot_degrees = 360` | plan §1 C1 carrier | no entry in HUD.md, HUD_SPEC or G3 | **UNSOURCED** (from `JC3_HUD_WEAPONS.md` §3) |
| `MCI_bullet_bar` / `_anim` 65 frames, `magazine_ammo`/`size` → `65 * ammo / size`, early return at `ammo <= 0` | plan §2 C2 carrier | HUD_SPEC `jc3.vehicle_api` has `InitVehicleWeapons` / `UpdateVehicleWeapons` argument names (`magazine_ammo`, `magazine_size`, `weapon_cooldown`), but no frame formula and no early-return; G3 does not mention the slot's bar | **UNSOURCED** (from `JC3_HUD_WEAPONS.md`) |
| `MCI_selected_weapon_icon`, `GetWeaponIconName`, `weapon_icons/<id>.ddsc`, 69 ids, id 614 free, `_sm` twin | plan §3 C5 carrier | no entry in the three files; `HUD_SPEC` lists only the nine DDS atlases | **UNSOURCED** (from `JC3_HUD_WEAPONS.md` §6 / index census) |
| `MCI_inflict_damage`, `CreatePoi(type, progress, minor, label)` | plan §6 carriers | `CreatePoi`/`MCI_inflict_damage` not in HUD.md, HUD_SPEC or G3 | **UNSOURCED** (from `JC3_HUD_WEAPONS.md` §4/§5) |
| `MCI_inventory_infinity`, `infiniteAmmo` true branch | plan §2 trade-off ("hides both counters, shows `MCI_inventory_infinity`") | HUD_SPEC `InitVehicleWeapons` has `infiniteAmmo:Boolean = true`, nothing about a widget or which counters hide | **UNSOURCED** |
| `InitVehicleNitrous` / `InitVehicleWeapons` call sites | "0 call sites in the movie except 2 demo calls in `TestConstructor`" | `HUD.md:§8` says "the caller is game code, not the entity graph" but gives no call-site count; G3 §4 counts only `InitPrimaryMeter` 1 / `SetPrimaryMeterValue` 0 / `SetVehicleType` 0 | **UNSOURCED** (from `JC3_HUD_WEAPONS.md` §2/§7) |
| weapon slots / `main_weapon` + `id:00568A74`, `weapon_type` 2 | plan §0/§1 slot facts | HUD.md §6 says "two slots"; no ids, no component list; HUD_SPEC `has_vehicle_weapons: true` only | **UNSOURCED** in these files (build/`WEAPON_WIRING` fact) |
| `T-HUD13` "both icon ids ship", `T-HUD16` "cooldown = state/4" | plan §0/§1 | ledger rows, not in the three sources | **UNSOURCED** in these files |
| `MCI_speedo` guard `if (m_CurrentType != TYPE_BATMOBILE)` | plan §4 build | G3 §4 establishes `m_CurrentType` as the only discriminator (LAND/AIRPLANE/HELICOPTER/SEA) and the private-copy route; the exact guard is the plan's | **MATCH** (mechanism), guard is derived |
| `bmak_hud_cluster.py`, `hud_spec.py`, `bmak_speedometer.py`, `t19_hud.py` gates | plan §9 | all four exist under `Tools/scripts/`; `Working/HUD/CLUSTER.md` + `.json` exist | **MATCH (files exist)** |

---

## Elements the plan covers that the sources do not show

These are not errors — they are claims whose only evidence is outside the three files, and the plan
should say so rather than let them read as HUD.md/HUD_SPEC/G3 findings:

1. **The per-slot cooldown ring** — `MCI_radial_loader_cooldown`, `SetCooldownRotation`, the two mask
   rotations, `rot_degrees = 360` (§1 C1). None of the three files names a radial loader.
2. **The ammo bar as the armour gauge** — `MCI_bullet_bar` / `MCI_bullet_bar_anim`, the
   `65 * ammo / size` frame rule, the `magazine_ammo <= 0` early return, `MCI_inventory_infinity`
   (§2 C2). HUD_SPEC has the argument names only.
3. **The badge-as-icon mechanism** — `MCI_selected_weapon_icon`, `GetWeaponIconName`, the
   `weapon_icons/<id>.ddsc` path, the 69-id census, "614 is free", the `_sm` twin (§3 C5).
4. **The damage readout carriers** — `MCI_inflict_damage` and `CreatePoi(..., label)` (§6).
5. **`max_health` 36,000** and the "health proportion is 0..2" premise (§2).
6. **Slot wiring** — `main_weapon` / `id:00568A74`, `weapon_type` 2, `T-HUD13`/`T-HUD16` (§0–§1).

## Elements the sources show that the plan omits

1. **`UC_SetCannonCoolDown` 0…4 and the reticle labels** (`PreReady`/`Ready`/`PreReadyLevel1/2`/`Blank`) —
   `HUD.md:§4`, `HUD_SPEC.frame_labels`; HUD.md §6 calls the cannon cooldown a "partial" map, and the
   plan never mentions it even though it is the second cooldown the plan is trying to carry (C1).
2. **`UC_SetEnergySystemParams`** and the energy charges family (`Charges2/3/4`, `BecomeFull`, `Empty`) —
   `HUD.md:§4`, `HUD_SPEC.frame_labels`; a second gauge system the plan does not dispose of.
3. **The health bar's own dynamics**: `MaxHealthChangePerFrame 0.05` (0.667 s sweep), `GoOffscreenTimer 2 s`,
   battle-mode `Delayed` intro and the force-visible rule — `HUD.md:§4`, `HUD_SPEC.health_contract`,
   G3 §3. The plan uses the armour formula but never the sweep/offscreen contract.
4. **`Health` clip = `Timeline_390`, 162 frames with `IntroDelayed/Intro/Idle/XPFill/Outro/Out`** — G3 §3.
5. **`Background` 32 frames with `Basic/Extra1..4` labels** — G3 §2 (the plan mentions only the two badge
   clips, not the background label set).
6. **`MaxHealthChangePerFrame`/`pulse_below 0.2` as the flash carrier** — G3 §3 uses it for the damage
   flash; the plan takes the pulse wording but not the sweep/`GoOffscreenTimer` pair.
7. **The XP bar, combo meter, winch meter, occupants, special weapons, virus upload, forensic tracking,
   battle/zoom machine** — `HUD.md:§4`–§6 and G3's row table; all are "out"/"none" and the plan is silent,
   so the cluster's scope boundary is not stated.
8. **The 37-setter count and `UC_ShowBoostUpgrade`** — `HUD.md:§4` ("The 37 setters are in
   `HUD_INTERFACES.json`"), `HUD_SPEC.uc_setters`; the badge plan instead rides the weapon icon and never
   mentions the existing `UC_ShowBoostUpgrade(String, String)` setter, which is the natural badge carrier
   before a new icon id.
9. **`MCI_nitro_meter` as the boost bar** — HUD.md §6 and G3's disposition (C1/C4) still map the primary
   boost gauge there; the plan's §5 uses it for the fill/rise route but its §1 replaces the second gauge
   without stating that the first gauge is unaffected.

---

## Corrections for the plan owner

1. **Fix the `Cap` frame count (row "`Cap` `Decrease`").** The 65 frames belong to `Upgrade1/2`
   (`G3 §2`); no source gives a length for the `Cap` `Decrease` label. Drop "= 2.167 s" or label it as an
   assumption.
2. **Reconcile the damage-flash signature.** `G3 §3` says `(part, x, y, frames)`; `HUD.md:§4` and
   `HUD_SPEC.uc_setters` say `part, amount, duration, frames`. One of the two is wrong; the plan silently
   picks G3's. Say which and why.
3. **Drop or source "0..2" and 36,000.** `HUD_SPEC` defines health as a 0..1 proportion with armour above
   1; nothing caps it at 2 or gives 36,000. Both are build/ledger facts — cite them or remove them.
4. **Attribute the six unsourced carriers.** The radial loader, ammo bar, icon-id mechanism,
   `MCI_inflict_damage`/`CreatePoi`, `max_health` and the slot wiring all come from
   `JC3_HUD_WEAPONS.md`, `WEAPON_WIRING` or the ledger — none from the three files this plan presents as
   its evidence. Add the citations so the audit trail is not misread.
5. **Correct G3's stale "z <= 25".** The plan's "z ≤ 56" matches G3's own table; note that the sentence in
   G3 §1 is the error, so a later reader does not "fix" the plan back to 25.
6. **Address `UC_ShowBoostUpgrade` before inventing icon ids.** HUD.md §4 / HUD_SPEC list a real
   badge setter (`param1:String, param2:String`) that the plan does not dispose of; if it is unusable,
   say why, otherwise it is the cheaper C5 carrier.
7. **State the scope the sources show.** The plan closes six gaps but never says that the energy system,
   XP, combo, winch, occupants, battle/zoom and the cannon reticle remain out — G3/HUD.md list them, so
   their absence reads as an omission rather than a decision.

---

## Limits

* Static reads only; no movie, `.gfx`, JSON regeneration or tool run beyond listing the four gate scripts
  and the two `Working/HUD` files (all present).
* `HUD_SPEC.json` was read through its `bmak`/`jc3` keys (setters, constants, health contract, vehicle
  API, types); values it does not carry are marked UNSOURCED rather than guessed.
* `Working/HUD/CLUSTER.md` §7, which the plan quotes for C1, was not opened; the identical sentence is in
  G3's COMPROMISES C1, which was read.
* The plan was not edited. This audit touches only this file. **Revert:** delete this file.
