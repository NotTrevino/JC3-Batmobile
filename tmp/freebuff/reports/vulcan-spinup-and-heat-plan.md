# Vulcan barrels — BmAK's spin-up, rate ramp, tracer spacing and heat, and the JC3 members that carry them

**Question:** BmAK's Vulcan spin-up time, fire-rate ramp, tracer spacing and heat limit from the
weapon grab; then the JC3 gatling tune members for spin-up and rate, with a value for each.

**Verdict.** BmAK's chain gun spins up in **0.576 s** (`ChainGunMaxSpinSpeed` 1440.0 ÷
`ChainGunSpinAccel` 2500.0) and down in **0.720 s** (÷ `ChainGunSpinDecel` 2000.0), fires every
**0.138 s (7.25 rounds/s)** with **no rate ramp at all** — the "combo" interval is the *same* 0.138 s
— and draws **one tracer particle system** (`Particles.Batmobile_Muzzleflash_Tracer`, **1 emitter,
0.35–0.5 s** lifetime) with **no spacing field anywhere in the grab**: tracers are per-shot visuals,
not every-Nth. Its **heat limit does not exist in the shipped defaults**: `HeatUpPerSecond` is
**0.0**, so the gun never heats; the bar's position/size, the `bOverheating` bool and the overheat/
cooled sounds all ship, but no maximum exists to quote. On the JC3 side the rate members are decoded
(`WeaponTuning.fire_rate` **0.1 s** on every gatling weapon, `fire_rate_level_2` 0.12) and
`GatlingGun` is driven by `weapon_rpm`, but **heat is proven absent from JC3 weapons** and the
barrel-spin component's own **spin-up/spin-down members are not decoded** — that is the one gap.

Labels: **decoded** = read at the cited field; **derived** = arithmetic over decoded inputs, with the
assumption stated; **UNKNOWN** = searched and absent, with the settler named. All BmAK values are the
class defaults on `Batmobile_Cannon_V2`, which `WEAPONS.md` §8 records as **identical in all four
packages** (67 fields, 268 comparisons, 0 differences) unless a row says otherwise.

---

## 1. BmAK: the spin

| member | offset | type | value | role |
|---|---|---:|---:|---|
| `RBatmobileCannon.ChainGunMaxSpinSpeed` | 0x0A98 | FloatProperty | **1440.0** | the barrel spin ceiling |
| `RBatmobileCannon.ChainGunSpinAccel` | 0x0A9C | FloatProperty | **2500.0** | how fast it reaches the ceiling |
| `RBatmobileCannon.ChainGunSpinDecel` | 0x0AA0 | FloatProperty | **2000.0** | how fast it bleeds off |
| `RVehicleWeapon.TempName` | 0x0814 | StrProperty | **"Chain Gun"** | the weapon's own name in the grab |

Source: `Research/BatmobileGrab/WEAPONS.md` §8 `Batmobile_Cannon_V2` table (lines 687–689, 722).

**Spin-up / spin-down (derived).** The three values are in the same spin unit, but **the grab does not
name that unit** (revolutions per minute is the natural reading of a 1440 ceiling, and it is not
stated in `WEAPONS.md`). The time to traverse the ceiling is the ratio either way:

```
spin-up   = ChainGunMaxSpinSpeed / ChainGunSpinAccel = 1440 / 2500 = 0.576 s
spin-down = ChainGunMaxSpinSpeed / ChainGunSpinDecel = 1440 / 2000 = 0.720 s
```

Cross-check that the numbers behave like a rate: decel is **0.8×** accel (2000/2500), so spin-down is
**1.25×** spin-up (0.720/0.576) — the gun falls off its speed more slowly than it climbs, which is the
usual minigun shape. If the unit were rev/s the ratios would be unchanged and the times identical,
which is why no unit is claimed.

There is no "spin up before the first round" gate anywhere in the class defaults: the fire members
(§2) are constant, so the spin is a **visual/audio state**, not a rate limiter.

---

## 2. BmAK: the fire rate, and the ramp that is not there

| member | offset | type | value | meaning |
|---|---|---:|---:|---|
| `RVehicleWeapon.FiringInterval` | 0x0828 | FloatProperty | **0.1379999965429306** | seconds per round |
| `RBatmobileCannon.ComboFiringInterval` | 0x0B58 | FloatProperty | **0.1379999965429306** | the interval once "combo" fire is engaged |
| `RVehicleWeapon.WeaponCoolDown` | 0x0830 | FloatProperty | **1.0** | cooldown after the trigger is released |
| `RBatmobileCannon.ChainGunDamage` | 0x0B64 | IntProperty | **40** | per round |
| `RBatmobileCannon.UpgradedDamage` | 0x0B68 | IntProperty | **50** | per round, upgraded |
| `RBatmobileCannon.InaccuracyAngle` | 0x0A70 | FloatProperty | **0.1** | base spread |
| `InaccuracyVsTime.Points` | 0x0C4C | ArrayProperty | **4 points** | bloom over time, see below |

**Fire rate: 0.138 s → 7.246 rounds/s.** `1 / 0.138 = 7.2464`.

**Fire-rate ramp: none (decoded).** The class ships *two* interval members — one for normal fire, one
for combo fire — and they hold **the same value to the last float**
(`0.1379999965429306` both, offsets 0x0828 and 0x0B58). So engaging the combo changes the **sound**
(`ComboFireLoopingEvent` `Engine.Play_Minigun_Combo_Fire`, `EnterComboSound`
`Engine.Play_Minigun_Combo_Trans_In`, `ExitComboSound` `Engine.Play_Minigun_Combo_Trans_Out`) and the
**damage tier**, not the cadence. A port that ramps the rate would be inventing behaviour.

**The only ramp in the weapon is accuracy, not rate** (`InaccuracyVsTime.Points`, 4 points,
`CIM_Linear`):

| t (s) | inaccuracy | reading |
|---|---|---|
| 0.0 | 0.0 | first round, no bloom |
| 0.5 | 0.0 | holds flat for half a second |
| 1.5 | 1.5 | climbs |
| 2.5 | 3.0 | full bloom |

and the upgraded curve `InaccuracyVsTimeUpgrade.Points` (also 4 points) reaches the same 3.0 more
slowly: 0.0 → 0, 1.0 → 0, 3.0 → 1.5, 5.0 → 3.0. This is the "hold the trigger and the group opens
up" behaviour; it is the quantity a fire-rate ramp is usually confused with.

**Joker variant differs** (`Batmobile_JokerCannon_V2`, one instance, its own table): 
`RVehicleWeapon.FiringInterval` **0.100 s** (10 rounds/s), `ChainGunDamage` **999**, 
`RiotSuppressorFiringInterval` **0.333** (vs 0.75), `ImpactMomentum` **2000** (vs 60000). So the
Joker skin's chain gun is **1.38× faster** (0.138/0.100) and far harder-hitting — if the port targets
the Joker variant, 0.100 is its rate, not 0.138.

---

## 3. BmAK: tracer spacing

| item | value | source |
|---|---|---|
| tracer system | `RBatmobileCannon.ChainGunTracerSystem` = **`Particles.Batmobile_Muzzleflash_Tracer`** | `WEAPONS.md` line 669, resolved to `VFX_Batmobile.Particles.Batmobile_Muzzleflash_Tracer` (line 738) |
| the system | **1 emitter**, kinds `beam, sprite` (+ a `none`), **lifetime 0.35 – 0.5 s** | `PARTICLES.md` lines 120 / 330 / 477 |
| non-tracer muzzle flash | `RBatmobileCannon.GunFX` = `Particles.Batmobile_Muzzleflash_NoTracer` (**7 emitters**, 0.055–1.1 s) | `WEAPONS.md` line 666; `PARTICLES.md` line 119 |
| casing stream | `ChainGunLoopingShells` = `Particles.ChainGun_BulletCasing`; socket `"ChainGunShells"` | `WEAPONS.md` lines 670, 705 |
| per-Nth-round field | **none** — the 62 weapon objects carry no tracer-every-N, tracer-percentage or shot-counter member (`WEAPONS.md` §5 lists every field path matched by the G1-08 card, and tracer spacing is not among them) | `WEAPONS.md` §5 |

**So the spacing is the fire interval itself: one tracer per round, every 0.138 s (7.25/s), each
living 0.35–0.5 s.** At 7.25 rounds/s a tracer's 0.35–0.5 s life means roughly **2.5–3.6 tracers are
in the air at any instant** — the visual density BmAK shows. That count, not a "every 3rd round" rule,
is what a port needs to reproduce.

The tracer is a **beam** particle (the system's emitter kinds are `beam, sprite`), which matches the
streak look; the muzzle flash is a separate system set to `NoTracer`, i.e. BmAK splits flash and
tracer rather than drawing both from one emitter.

---

## 4. BmAK: the heat limit — it does not exist in the defaults

| member | offset | type | value | reading |
|---|---|---:|---:|---|
| `RBatmobileCannon.HeatUpPerSecond` | 0x0A78 | FloatProperty | **0.0** | **the gun accumulates no heat** |
| `RBatmobileCannon.OverheatOffValue` | 0x0A80 | FloatProperty | **0.25** | the value the heat must fall to before the gun is usable again |
| `bOverheating` | bits 4, `0x10` | BoolProperty | **False** | the runtime flag, default off |
| `HeatBarStart` | 0x0A88 | StructProperty | **[0.79, 0.68]** | where the bar is drawn (2-D, HUD space) |
| `HeatBarSize` | 0x0A90 | StructProperty | **[0.125, 0.03]** | the bar's size |
| `RBatmobileCannon.ChainGunOverheatSound` | 0x09C8 | ObjectNCRProperty | `Engine.Play_Minigun_Overheat` | **missing-object** in the package |
| `RBatmobileCannon.ChainGunCooledSound` | 0x09D0 | ObjectNCRProperty | `Engine.Play_Minigun_Cooled` | — |
| `RBatmobileCannon.ChainGunScreenShake` | 0x0BA4 | StructProperty | 7 props, 112 B (`bChainGunScreenShake` **True**) | shake, not heat |

**No maximum is stored.** The grab has a *rate* (`HeatUpPerSecond`), a *threshold* (`OverheatOffValue`
0.25), a *flag* (`bOverheating`) and the bar's *rectangle* — but no heat cap, no cool rate, and no
`OverheatValue`. With `HeatUpPerSecond = 0.0` the shipped default **cannot overheat**, so the bar never
fills and the 0.25 threshold is never reached. The heat display on the BmAK HUD is therefore dead in
the default data (consistent with `dash-hud-gauges-plan.md`: the bar geometry exists, no `UC_*` setter
mentions heat, `0 of 252`).

If a heat limit is wanted, it must be **chosen**: the only decoded numbers to anchor it are the 0.25
recovery threshold and the bar rectangle (its fill fraction, not a temperature). This report does not
invent a cap.

---

## 5. JC3: the tune members that carry rate, and the value for each

Source: `Research/JC3Grab/WEAPONS.md` §2 (per-weapon table), §10 (card mapping), §12 (member
vocabulary over 22 `WeaponTuning` ids). Values below are the shipped tune of the gatling weapons, read
from our build's vehicle tunes.

| JC3 member | value on gatling weapons | unit / meaning | BmAK counterpart |
|---|---|---|---|
| `WeaponTuning.fire_rate` | **0.1** on `w604_helicopter_mgun`, `w607_heavyhelicopter_mgun`, `w610_fighterjet_mgun`, `w617_vintagefighter_mgun`, `w620_racingboat_mgun`, `w622_advancedhelicopter_mgun` (also `w603` mediumtank mgun, `w619` buggy mgun) | **seconds between shots** (`WEAPONS.md` §2) → **10 rounds/s** | 0.138 s / 7.25 rps |
| `WeaponTuning.fire_rate_level_2` | **0.12** (22/22 ids carry it, min = max = 0.12) | a second-level rate; **what selects it is not decoded** (`WEAPONS.md` §12 lists it with one value across all 22) | no BmAK counterpart |
| `WeaponTuning.burst_count` | **1** | rounds per burst | 1 (continuous) |
| `WeaponTuning.burst_cooldown` | **0** | seconds between bursts | — |
| `WeaponTuning.fully_automatic` | **1** | hold-to-fire | 1 |
| `WeaponTuning.magazine_size` | **-1** | no magazine | no magazine |
| `WeaponTuning.unlimited_ammo` | **1** | never runs dry | — |
| `WeaponTuning.max_range` | **500** (mguns; 200 buggy, 1000 tank canon) | metres | — |
| `bullet_base_tuning.velocity` | **900** (mguns) | projectile speed | — |
| `bullet_base_tuning.tracer_fire_velocity` | 100 … 900 | tracer's own speed | — |
| `bullet_base_tuning.tracer_fire_length` | 10 … 40 | tracer streak length | beam length |
| `bullet_base_tuning.tracer_fire_width` | 0.03 … 0.5 | tracer width | — |
| `bullet_base_tuning.tracer_time_to_live` | 0 … 2 | tracer lifetime, seconds | **0.35–0.5 s** |
| `bullet_base_tuning.tracer_per_smoke_trail` | 0 … 3 | smoke puffs per trail | — |
| `bullet_base_tuning.tracer_expand_width` | 0 … 2 | width growth | — |
| `bullet_base_tuning.tracer_texture_type` | 1 (single value) | texture variant | — |
| `bullet_base_tuning.smoke_trail_tile_size` | 0 … 5 | trail tiling | — |

**Rate conversion to match BmAK:** `fire_rate` is seconds per shot, so a Vulcan that fires every
0.138 s needs `fire_rate = 0.138` — the tune ships 0.1, so this is a **+38 % interval** edit
(10 → 7.25 rounds/s). The Joker variant's 0.100 needs no edit at all.

**Heat:** `WEAPONS.md` §10 states it as a proven absence — *"No member of any decoded class names heat,
cooling or temperature … no weapon tunes a temperature anywhere"*; the only cooldown-shaped member is
`burst_cooldown`. So there is **no** JC3 heat member to set, and BmAK's `HeatUpPerSecond` /
`OverheatOffValue` have nothing to map to. This is the same finding as `dash-hud-gauges-plan.md` §7.

---

## 6. JC3: the spin — two layers, one of them not decoded

The barrel spin in JC3 is **split** as in BmAK, but along a different seam:

| layer | member / object | value | status |
|---|---|---|---|
| **weapon side** | `CBarrelSpinWeaponComponent` — present on **12 entities**, e.g. `w620_racingboat_mgun` (`WEAPON_WIRING.md` line 1026), `w604`/`w607`/`w622` helicopter mguns | component **present**; its **spin-up / spin-down / rpm members are not decoded** — the class appears only as a component count in `ENTITIES.md` (12) and `FEATURE_CENSUS.md` (12 devices, 4 classes) | **UNKNOWN values** |
| **part side** | behaviour **`GatlingGun`** on the barrel part | `rpm_variable` = **`weapon_rpm`**, `rotoscope_enabled` **0**, `rotoscope_rpm_per_cycle` **20.0**, `inverted` **0**, `special_collision_enabled` **0**, `number_of_water_collision_sensors` **0** | **decoded** (`MOVING_PARTS.json` → `all_rotating_part_properties`) |
| **part geometry** | `rotating_parts[]` row: `part_index`, `position[0..2]`, `rotation_axis[0..2]`, `max_rpm_visible`, `min_rpm_visible`, `number_of_blades`, `rpm_multiplier`, `rpm_opacity_transition` | member **names decoded**; the per-row **values are not in the repo** (only `-1.0` sentinel seen in `EMP.json`) | **UNKNOWN values** |
| **live donor** | `racingboat_minigun_l_barrel_signature` (**part 21** ← base 7) and `racingboat_minigun_r_barrel_signature` (**part 22** ← base 8), both `GatlingGun` | — | decoded (`WEAPON_WIRING.md` line 1044) |

So, of the two spin quantities asked for:

* **spin-up time** — BmAK 0.576 s. JC3: the component that would hold it
  (`CBarrelSpinWeaponComponent`) is **identified but undecoded**; the part side has an rpm channel
  (`weapon_rpm`) with no acceleration member exposed. **UNKNOWN on the JC3 side**, settler below.
* **spin rate** — BmAK 1440 (unit unnamed). JC3: `weapon_rpm` is the channel, and
  `rotating_parts[].max_rpm_visible` / `min_rpm_visible` / `rpm_multiplier` are the members that scale
  it, with **values not decoded** for any gatling part. **UNKNOWN values.**

What *is* settled: JC3's cadence is **not** gated by spin either — `fire_rate` is a constant in
`WeaponTuning`, exactly as BmAK's `FiringInterval` is constant. Both games spin the barrels for looks
and sound.

---

## 7. The port table — what to set, member by member

Assuming the Batmobile's Vulcan is wired to a JC3 gatling weapon (the closest donor is
**`w620_racingboat_mgun`**: 2 muzzles, `BarrelSpinWeaponComponent`, `GatlingGun` barrel parts, 0.1 s
rate):

| BmAK quantity | value | JC3 member | value to write | note |
|---|---:|---|---:|---|
| fire interval | 0.138 s | `WeaponTuning.fire_rate` | **0.138** | +38 % over the shipped 0.1 |
| rounds/s | 7.246 | (derived) | 7.25 | `1/0.138` |
| rate ramp | none | `fire_rate_level_2` | **leave 0.12** | no BmAK ramp exists; do not invent one |
| burst | 1 / continuous | `burst_count`, `fully_automatic` | 1, **1** | already correct |
| tracer lifetime | 0.35–0.5 s | `bullet_base_tuning.tracer_time_to_live` | **0.4** (mid) or 0.5 (max) | BmAK's range; pick per look |
| tracer per round | 1 (every shot) | (no frequency member) | — | tracers are per-bullet in JC3 |
| tracer length/width | beam streak | `tracer_fire_length`, `tracer_fire_width` | 10–40, 0.03–0.5 (within fleet) | no BmAK number exists |
| spin-up | 0.576 s | `CBarrelSpinWeaponComponent` (members UNKNOWN) | **measure first** | see §8 |
| spin ceiling | 1440 (unit unstated) | `GatlingGun` → `weapon_rpm`; `rotating_parts[].max_rpm_visible` | UNKNOWN | `rpm_multiplier` is the only exposed scalar |
| heat cap | none exists | none exists | — | do not add; BmAK cannot heat either |
| heat threshold | `OverheatOffValue` 0.25 | none | — | no JC3 heat model |

---

## 8. The 5-minute experiment that settles the JC3 spin

1. Decode `CBarrelSpinWeaponComponent` from one entity that carries it — e.g.
   `v1401_boat_mugello_racingboat_signature_preorder.ee`, whose only spin-bearing weapon is
   `w620_racingboat_mgun` (`WEAPON_WIRING.md` line 1026) — with the same Gibbed ADF pass the vehicle
   modules already use. That yields the component's member names and defaults; if it holds a spool
   time, that is BmAK's 0.576 s counterpart.
2. If it holds nothing usable, read the barrel in-game: time from trigger to full spin on the
   racing boat and compare with 0.576 s. One number, one clip.
3. Only then decide whether to leave the donor's spin alone (recommended: spin is cosmetic in both
   games) or to tune `rpm_multiplier`.

No game process was started for this report; no `.wtune`, `.vmodc`, part or build file was written.

---

## 9. Checks run

| check | result |
|---|---|
| spin members | `ChainGunMaxSpinSpeed` 1440.0, `SpinAccel` 2500.0, `SpinDecel` 2000.0 (`WEAPONS.md:687-689`) |
| spin arithmetic | 1440/2500 = **0.576 s**; 1440/2000 = **0.720 s**; 0.720/0.576 = 1.25 = 2500/2000 |
| rate | `RVehicleWeapon.FiringInterval` = `RBatmobileCannon.ComboFiringInterval` = **0.1379999965429306** → 7.2464 rps |
| ramp | none: the two interval members are byte-identical in value |
| accuracy ramp | `InaccuracyVsTime` 0→0, 0.5→0, 1.5→1.5, 2.5→3.0; upgrade 0→0, 1→0, 3→1.5, 5→3.0 |
| tracer | `Batmobile_Muzzleflash_Tracer`, **1 emitter**, lifetime **0.35–0.5 s**; flash system `..._NoTracer` has 7 emitters |
| tracer spacing field | **absent** from the 62 weapon objects (§5 field index) |
| heat | `HeatUpPerSecond` **0.0**, `OverheatOffValue` **0.25**, `bOverheating` False, `HeatBarStart` [0.79,0.68], `HeatBarSize` [0.125,0.03]; no cap member |
| Joker variant | `FiringInterval` **0.100**, `ChainGunDamage` **999**, `RiotSuppressorFiringInterval` 0.333 |
| JC3 rate | `fire_rate` **0.1** on all eight mguns; `fire_rate_level_2` 0.12 on 22/22 |
| JC3 heat | proven absent (`WEAPONS.md` §10) |
| JC3 spin | `GatlingGun` → `weapon_rpm` decoded; `CBarrelSpinWeaponComponent` on 12 entities, members **undecoded** |

## 10. Change record (per `AGENTS.md`)

1. **Intended change:** add one report giving BmAK's Vulcan spin/rate/tracer/heat numbers from the
   weapon grab and the JC3 members that carry rate and spin.
2. **File:** `tmp/freebuff/reports/vulcan-spinup-and-heat-plan.md` — the brief names this path; every
   comparable plan lives in `tmp/freebuff/reports/`. No `Research/` card is regenerated and no build
   file is written.
3. **Revert:** delete this file. Nothing else changed (read-only JSON/Markdown queries and
   `write_file`).

## 11. UNKNOWNs

| # | UNKNOWN | settler |
|---|---|---|
| U-1 | the unit of `ChainGunMaxSpinSpeed` / `SpinAccel` / `SpinDecel` | `WEAPONS.md` records the numbers, not the unit; rpm is the natural reading and the ratios are unit-independent |
| U-2 | any BmAK heat **cap** | no member exists; `HeatUpPerSecond` is 0.0, so the default cannot heat at all |
| U-3 | tracer spawn interval inside `Batmobile_Muzzleflash_Tracer` | `PARTICLES.md` records emitter count and lifetime, not spawn rate; one tracer per shot is implied by the single-emitter system |
| U-4 | `CBarrelSpinWeaponComponent`'s spin-up / spin-down / rpm members | decode the component from `v1401_..._preorder.ee` (§8 step 1) |
| U-5 | `rotating_parts[]` values (`max_rpm_visible`, `rpm_multiplier`, `number_of_blades`) for the gatling parts | same decode; only member names are in the repo |
| U-6 | which level `fire_rate_level_2` applies to | it is 0.12 on all 22 tunes and no decoded member selects it |
| U-7 | whether JC3 gates fire on barrel spin | no decoded member ties `weapon_rpm` to `fire_rate`; in BmAK the fire interval is constant, so spin is cosmetic on both sides |
