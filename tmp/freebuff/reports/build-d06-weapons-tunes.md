# B-06 — the BmAK weapon tune set in `Builds/bm-RC4-weapons`

**STATUS: done.** `Builds/bm-RC4-weapons` is staged from `Builds/bm-RC4-entity` (B-05's graph) and
ships **7 private files**: 5 `.wtunec` tunes (cannon, Vulcan, missile, EMP launcher, riot) and 2
`AutoAim` tunes (EMP lock-on, riot). **50 values are written**, each at its decoded
`offset-in-file`, so every file keeps its shipped byte size. Both gates are green
(`bm_weapons.py --check`, `jc3weapons.py --check --root`), Done 1 reports **0 dangling** weapon
paths, and `t7_weapons.py --check` still reads its 15 rows.

The graph is unchanged in shape: **477 objects / 47 classes** before and after (plus the one
classless root), with **5 members repointed** (4 `AA7096C9` tune paths + 1 `6D4C8277` autoaim path).

---

## 1. What was built, and from what

| file | row | bytes | source | carrier |
|---|---|---:|---|---|
| `…/06_vehicle/w602_batmobile_cannon/w602_batmobile_cannon.wtunec` | T-WP1 | 14,224 | `w602_mediumtank_canon.wtunec` (patch) | `CBulletWeaponBase` `w602_mediumtank_canon` |
| `…/06_vehicle/w603_batmobile_vulcan/w603_batmobile_vulcan.wtunec` | T-WP2 | 14,223 | `w603_mediumtank_mgun.wtunec` (patch) | `CBulletWeaponBase` `w603_mediumtank_mgun` |
| `…/06_vehicle/w618_batmobile_missile/w618_batmobile_missile.wtunec` | T-WP3 | 14,244 | `w618_sportsmuscle_missile.wtunec` (patch) | `CBulletWeaponBase` `w618_sportsmuscle_missile` |
| `…/06_vehicle/w618_batmobile_emp_missile/w618_batmobile_emp_missile.wtunec` | T-WP4 | 14,244 | the same `w618` tune | `CBulletWeaponBase` `w618_sportsmuscle_missile_emp` |
| `…/06_vehicle/w618_batmobile_emp_missile/autoaim_batmobile_emp_lockon.wtunec` | T-WP4 | 2,227 | `00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtunec` | the EMP component's `6D4C8277` |
| `…/06_vehicle/riot_batmobile_suppressor/riot_batmobile_suppressor.wtunec` | B-15 (T-WP10/14) | 14,224 | **this build's cannon copy** (chained, so velocity 400 and tracer TTL 1.25 come with it) | **unbound** — no riot entity object exists |
| `…/06_vehicle/riot_batmobile_suppressor/riot_batmobile_suppressor_autoaim.wtunec` | B-15 (T-WP10/14) | 2,214 | `00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtunec` | **unbound** |

`Builds/bm-RC4-entity`'s `.epe` is `b0a8b5a9…` (133,896 B, 477 objects, 47 classes). B-05's 4
components and the 8 forced slot pointers are not touched by this card; only the five path members
above change.

Riot is a **second weapon entity** (B-15) and the Joker weapons have no decoded socket, so their
tunes are authored here and stay **unbound/unreferenced**; the manifest records that as `L-4`.

## 2. Every member written (offset in file, old → new, BmAK source number)

Offsets are absolute bytes in the private copy (ConvertAdf `offset-in-file`), the same coordinate
the decision report uses. All files are the same size as their source (a patch, never a re-encode:
ConvertAdf `-e`/`-i` would shrink 14,224 → 14,208 B).

### 2.1 `w602_batmobile_cannon.wtunec` — T-WP1 (3 writes)

| member (path) | offset | old → new | BmAK source number |
|---|---:|---|---|
| `bullet_weapon[0].tuning.base_tuning.fire_rate` (`…wtune.fire_rate`) | `0xA0` | 1.75 → **2.0** | BmAK cannon `FiringInterval` = **2.0 s** (`RVehicleWeapon.FiringInterval`, WEAPONS.md:553) |
| `…wtune.velocity` | `0x9C` | 500.0 → **400.0** | BmAK `Projectile.Speed` = **40000.0 UU/s = 400 m/s** (WEAPONS.md:333, export 15 tag @668; 1 UU = 1 cm) |
| `bullet_weapon[0].tuning.bullet_base_tuning.tracer_time_to_live` | `0x190` | 0.0 → **1.25** | `Particles.Rocket.Batmobile_CanonTrail` ribbon `ParticleModuleLifetime.Lifetime` = **1.25 s** (export 2241 @96; FX-16 §7) |

Tracer members left **exactly as shipped** (FX-16 §8/§9 — no exact BmAK number exists):

| member | value kept | why |
|---|---:|---|
| `tracer_fire_width` | 0.5 | already exact: ribbon `StartSize` 50 uu = **0.50 m** |
| `tracer_fire_length` | 30.0 | the ribbon's 250-uu field is labelled "beam length"; distance vs segment count is **UNKNOWN** |
| `tracer_fire_velocity` | 900.0 | the ribbon's `VelocityOverLifetime` values are not decoded; 900 is the streak stretch rate |
| `tracer_expand_width` | 0.0 | size-over-life curve not decoded; the unit is **UNKNOWN** |
| `smoke_trail_tile_size` | 5.0 | the BmAK sprite has no tile-size value in the grab |
| `tracer_per_smoke_trail` | 1 | the ribbon's 8/s spawn rate is a particle rate, not a per-tracer interval |
| `bullets_per_tracer` | 1 | BmAK has no per-N-bullets tracer value |
| `tracer_texture_type` | 1 | enum already 1; enum → `.ddsc` mapping is **UNKNOWN** |

### 2.2 `w603_batmobile_vulcan.wtunec` — T-WP2 (1 write)

| member | offset | old → new | BmAK source number |
|---|---:|---|---|
| `…wtune.fire_rate` | `0xA0` | 0.1 → **0.138** | BmAK Vulcan `FiringInterval` = **0.138 s** (7.25 rounds/s; `RVehicleWeapon.FiringInterval`, WEAPONS.md:553) |

No Vulcan tracer write: the BmAK Vulcan's own trail system was not decoded, so there is no source
number to write (writing the cannon's 0.5 m width onto the minigun would be a donor value).

### 2.3 `w618_batmobile_missile.wtunec` — T-WP3 (copy only, 0 writes)

The private copy exists so the missile component no longer names a shared shipped tune. No numeric
row: T-11 has none for `w618`.

### 2.4 `w618_batmobile_emp_missile.wtunec` — T-WP4 (5 writes, Fire Leech guidance)

| member | offset | old → new | BmAK source number |
|---|---:|---|---|
| `missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed` | `0x198` | 0.0 → **300.0** | w143 Fire Leech guidance transplanted by value (apply-weapon-slot-rows §2); BmAK homing rate has **no decoded member** (`RBatmobileMissile.AccelRate` absent, WEAPONS.md:193) |
| `…missile_turning_speed_random` | `0x19C` | 0.0 → **60.0** | w143 Fire Leech guidance (same report) |
| `…missile_acceleration[0]` | `0x188` | 200.0 → **65.0** | BmAK acceleration target **65**, over the 0.2 → 10 s bracket (same report); w618's 200 is the shipped missile value |
| `…missile_acceleration_time[0]` | `0x180` | 5.0 → **10.0** | BmAK acceleration bracket end **10 s** |
| `…missile_acceleration_random[0]` | `0x190` | 0.0 → **5.0** | w143 Fire Leech acceleration random **random 5** |

The fire block stays w618's (damage 1500, velocity 360, max_range 300, fire_rate 0.5), as T-WP4
requires.

### 2.5 `autoaim_batmobile_emp_lockon.wtunec` — T-WP4 (19 writes, 17 leaves already at target)

A new AutoAim, not a wholesale copy: w143's own tune targets characters (1) and not rigid objects
(0), which would let the Batmobile lock pedestrians. The cone values are the fleet lock-on preset;
the classes are BmAK's `RVehicle` lock.

| member × state blocks | offsets | old → new | BmAK source number |
|---|---|---|---|
| `AngleThresholdNewTarget` ×1 (`OnFoot`) | `0x50` | 0.05 → **0.12** | fleet lock-on preset **0.12** (`autoaim_vehicle_lockon_missile`); the other 5 states already 0.12 |
| `AngleThresholdCurrentTarget` ×1 (`OnFoot`) | `0x54` | 0.12 → **0.15** | fleet lock-on preset **0.15**; the other 5 states already 0.15 |
| `MaxAimDistance` ×6 | `0x8C`…`0x244` | −1 → **120.0** | BmAK `RBatmobileMissileLauncher.LockOnRange` = **12000 UU = 120 m** (WEAPONS.md:556) |
| `CanTargetVehicles` ×5 | `0xF0`…`0x250` | 0 → **1** | BmAK lock target type **`RVehicle`** (`OnFoot` was already 1) |
| `CanTargetRigidObjects` ×6 | `0x9C`…`0x254` | 0 → **1** | BmAK lock target type `RVehicle`; rigid objects kept (apply-weapon-slot-rows §2) |
| `CanTargetCharacters` ×0 | — | 0 (kept) | BmAK `RVehicle` must **not** target pedestrians |

17 leaves were already at the target (5 × 0.12, 5 × 0.15, 1 × vehicles 1, 6 × characters 0) and
were left unwritten; the manifest lists them under `autoaim.already`.

### 2.6 `riot_batmobile_suppressor.wtunec` — B-15 (4 writes, from this build's cannon copy)

| member | offset | old → new | BmAK source number |
|---|---:|---|---|
| `bullet_weapon[0].tuning.base_tuning.damage` | `0xF4` | 1.0 → **0.0** | no riot damage on BmAK's side; the cannon's `ChainGunDamage` 40 is lethal-only (apply-riot-mode-rows §4) |
| `…base_tuning.impulse` | `0xE0` | 0.0 → **100.0** | `RBatmobileCannon.ImpactMomentum` = **60000** (WEAPONS.md:680) and `RiotSuppressorVillainImpulse` = **6000** (WEAPONS.md:692); clamped to the tune maximum **100** player / 40 AI |
| `…base_tuning.vehicle_impulse_factor` | `0xE8` | 0.5 → **1.0** | same impulse pair; no per-target attenuation is decoded |
| `…wtune.fire_rate` | `0xA0` | 2.0 → **0.75** | `RBatmobileCannon.RiotSuppressorFiringInterval` = **0.75 s** (WEAPONS.md:691) |

`object_impulse_factor` was already 1.0 and is **not** written.

### 2.7 `riot_batmobile_suppressor_autoaim.wtunec` — B-15 (18 writes)

| member × state blocks | offsets | old → new | BmAK source number |
|---|---|---|---|
| `AngleThresholdNewTarget` ×6 | `0x50`…`0x208` | 0.03 → **7.5** | `RBatmobileCannon.RiotSuppressorLockOnAngle` = **7.5** (WEAPONS.md:690) |
| `AngleThresholdCurrentTarget` ×6 | `0x54`…`0x20C` | 0.05 → **7.5** | same |
| `StickyAimStartAngle` ×6 | `0x60`…`0x218` | 1.0 → **7.5** | same; which of the three is *the* cone is **UNKNOWN** (apply-riot-mode-rows §6.3) |

## 3. Done 1 — no dangling weapon path

The built `.epe` names **10** weapon paths:

* **5 private, present in the build**: the 4 tune paths (`.wtune` → the `.wtunec` extension resolves
  in the tree) and the EMP AutoAim;
* **5 shipped**: the M2 body model / collision `.pfx` / grip point, the shared
  `rigid_object_effect_settings_default.etune`, and the remaining shared `autoaim_assault_rifle`
  from B-05's component set;
* **0 dangling**.

The riot tunes are authored but not named by the graph (no riot object), so they are outside this
count and recorded as unbound.

## 4. Checks actually run

```
$ python Tools/scripts/bm_weapons.py --write
wrote …/v0300_car_kensington_sportsmuscle_civilian_01.epe: 4 component(s), 7 private file(s),
50 value writes                                                        exit=0
  w602_batmobile_cannon.wtunec  (14224 B)  fire_rate=2, velocity=400, tracer_time_to_live=1.25
  w603_batmobile_vulcan.wtunec  (14223 B)  fire_rate=0.138
  w618_batmobile_missile.wtunec (14244 B)  copy only
  w618_batmobile_emp_missile.wtunec (14244 B)  turning 300, random 60, accel 65, time 10, random 5
    autoaim_batmobile_emp_lockon.wtunec (2227 B)  19 write(s), 17 already at target
  riot_batmobile_suppressor.wtunec (14224 B)  damage=0, impulse=100, vehicle_impulse_factor=1,
                                              fire_rate=0.75
    riot_batmobile_suppressor_autoaim.wtunec (2214 B)  18 write(s), 0 already
  Done 1: 10 weapon path(s) named - 5 private, 5 shipped, 0 dangling

$ python Tools/scripts/bm_weapons.py --check
PASS: …/v0300_car_kensington_sportsmuscle_civilian_01.epe 477 -> 477 objects, 5 member(s)
repointed
  files: 5 private tune(s) + 2 AutoAim; 50 value writes (13 tune + 37 aim, 17 aim leaves already
  at target)
  Done 1: 10 weapon path(s) named - 5 private, 5 shipped, 0 dangling                exit=0

$ python Tools/scripts/jc3weapons.py --check --root Builds/bm-RC4-weapons
Builds\bm-RC4-weapons: 7 tune file(s) under editor/entities/jc_weapons
  w602_batmobile_cannon.wtunec  fire_rate  2      (T-WP1 expected 2)      ok
  w602_batmobile_cannon.wtunec  velocity   400    (T-WP1 expected 400)    ok
  w603_batmobile_vulcan.wtunec  fire_rate  0.138  (T-WP2 expected 0.138)  ok
check ok: 3/3 edit(s) re-read from the built tunes, 7/7 tune file(s) decode       exit=0

$ python Tools/scripts/t7_weapons.py --check
PASS: 15 rows = 13 WPN codes + 2 decision rows (13 with a JC3 carrier, 1 named omissions,
1 blocked: T-WP6) | 164 aspects classified, 46 UNKNOWN | 3 edits + 6 structural + 6 withdrawn |
4 JC3 ids, 2 driver slots | ledger 14/14 | json match True, md match True            exit=0
```

`bm_weapons.py --check` also re-runs the ConvertProperty round trip (`.epe` export → import is
byte-identical), re-hashes the built copies against the manifest, re-reads every written value at
its offset, and checks all 7 private files are registered in `aaf/@files.xml` (SmallPack drops
unlisted files). `jc3weapons.py` re-reads only its own 3 T-11 edits; the other 47 writes are read
back from the built bytes by `bm_weapons.py`.

## 5. Row coverage against the 15-row set

| rows | carried here | where |
|---|---|---|
| T-WP1, T-WP2, T-WP3, T-WP4 (launcher half) | **yes** — tunes + AutoAim, 4 bound components | §2.1–2.5 |
| T-WP10, T-WP14 (riot) | **tune authored**; entity/toggle is B-15 and unbound | §2.6–2.7 |
| T-WP15 | **named omission** — the disable half has no tune member | not written |
| T-WP6 | the **1 blocked** row | not written |
| T-WP5, T-WP7, T-WP8, T-WP9, T-WP11, T-WP13 | entity-side (B-18…B-21, B-16, B-05's slots) | not tunes |
| T-WP12 | HUD rows (T-19) | not tunes |

The lock-hold / 8-target salvo / reticle-link gap has **no card** in the row set: `t_blocked.py`'s
citations of B-24/B-25 are wrong (those cards are handling and flares), so the gap is named here
rather than carried by a card.

## 6. Limits and UNKNOWN (recorded, not silently accepted)

1. **L-1** — the `w618` pair names a missile tune on a `CBulletWeaponBase` component (B-05 clones
   the APC's bullet weapon for all four). A missile tune on a bullet carrier is a name-level match;
   the behaviour is UNKNOWN.
2. **L-2** — each private copy keeps its shipped ADF instance name (`w602_mediumtank_canon.wtune`
   etc.); renaming needs a re-encode that is not byte-identical. Whether the instance name is
   load-bearing is UNKNOWN.
3. **L-3** — whether a dropzone-loose `.epe` overrides the packed `.ee` is UNKNOWN (B-05 limit).
4. **L-4** — the riot tune and AutoAim are **unbound**: B-15's second weapon entity does not exist
   in this tree, and the third slot index is blocked (`mode-switch-carriers.md` §7 U1).
5. **L-5** — the AutoAim angle unit is UNKNOWN (0.15 = 54° as turns, 8.6° as radians); BmAK's 40°
   cone cannot be written until it is settled.
6. **Tracer art** — colour, the two-emitter composition, the −50 uu sprite offset, tiling and the
   materials have no tune member (FX-16 §9); only the linear half ships here.
7. **No runtime observation** — every number is a file read + a byte read-back; nothing here was
   fired in game (R6/test ban).

## 7. Files changed, and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/bm_weapons.py` | retargeted to `bm-RC4-entity`/`bm-RC4-weapons`; leaf-path walker, 5 tunes + 2 AutoAim, per-write BmAK citation, new checks | restore the previous script (`git checkout -- Tools/scripts/bm_weapons.py` if tracked, else restore the backup) and re-run `--write` |
| `Builds/bm-RC4-weapons/` | new build tree, `receipt.json`, `install.ps1` | delete the directory |
| `Working/Weapons/manifest.json` | regenerated for this build (schema 2) | re-run the previous script's `--write`, or restore the file |
| `tmp/freebuff/reports/build-d06-weapons-tunes.md` | this report | delete it |

No shipped `w6xx` file and no `Builds/bm-RC4-entity` byte was modified (R7): the shipped tunes are
re-read and pinned by sha1 on every run, and the base `.epe` is compared against the sha this card
recorded.
