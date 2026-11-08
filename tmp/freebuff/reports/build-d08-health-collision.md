# D-08 · B-09/B-10 — `Builds/bm-RC4-damage-collision`

**STATUS: built; health green, collision green, all three required gates exit 0.** The private health
module carries `max_health` 36000 and the keep-audit values/thresholds, the private `.effc`-free
damage module is repointed in the `.epe`, and the body collision is BmAK's decoded driving asset
(`Physics.Batmobile_V3_Physics` — 2 bodies / 3 boxes / 1 constraint), not the old convex-hull plan.

| gate | result |
|---|---|
| `damage_audit.py --build` | **`check ok`** — 29 members, 6 outside the shipped range, **6 declared switches** |
| `damage_predict.py table --root` | exit 0 — `max_health 36000`, hits-to-kill table below |
| `jc3hkx.py check --all --file` | **`check ok`** — 340,368 B, 430 objects, 54 hulls (54 convex), 22 compounds, 0 station sets |
| `t22_reopen.py --check` | **PASS 10/10** — 2 bodies / 3 boxes / 1 constraint, built set 62 donor bodies, 2 shapes missing |
| `bm_health.py --check` | **PASS** — 605 `.toc` records, 6 edit rows, 0 problems |

## 1. Commands run

```text
python Tools/scripts/bm_health.py --write --base bm-RC4-parts --tag bm-RC4-damage-collision
# collision payload: the B-10e BmAK-chassis variant, Working/Collision2/batmobile.physicsc
python Tools/scripts/eetoc.py patch <ee> Builds/bm-RC4-parts/<ee>.toc --base-ee ... --internal batmobile_health_medium.vmodc
python Tools/scripts/jc3hkx.py check --all --file .../sportsmuscle.physicsc
python Tools/scripts/damage_audit.py --build Builds/bm-RC4-damage-collision/aaf
python Tools/scripts/damage_predict.py table --root Builds/bm-RC4-damage-collision
python Tools/scripts/t22_reopen.py --check
```

Health `--write` exit 0; `eetoc patch` exit 0 (605 records, 1 appended); `jc3hkx`, `damage_audit`,
`damage_predict`, `t22_reopen` all exit 0. Base is `Builds/bm-RC4-parts` (688-file RC4 tree); the
tree is `Builds/bm-RC4-damage-collision` (`.ee` 11,180,321 B, `.toc` 60,917 B / 605 records).

## 2. Health (B-09)

| item | value |
|---|---|
| private module | `editor/entities/.../batmobile_health_medium.vmodc`, 3,741 B, Jenkins `1928726201` |
| `.epe` `damage` property | shared `670155287` -> **`1928726201`** at byte 474 (one copy; shared hash 0) |
| `max_health` | **36000** (licensed for bm-009 and bm-RC2; `damage_audit` reports it as a declared switch, upper shipped bound 4000) |
| thresholds | explosion **4000**, npc_explosion **4000**, smoke **1050**, burn **250** |
| wheel rows | `front_/rear_wheels_damage.skew_health` 200 -> **400** (both, entity-local `custom_land_global.vmodc`) |
| declared switches | 6: `max_health`, `deform_scale` 0, `impact_damage_factor` 0, `impact_armor`, `melee_armor`, `melee_armor_strength` |
| part types | **59 parts / 19 distinct types**; 24 `PartDamageType` rows; **4 fallbacks** (`Boat_Antenna`, `Boat_Generic`, `Plane_Control_Surface`, `Train_Generic`) |
| R7 | shared `lave_health_medium.vmodc` unchanged (sha `AF5C33E6…`) |

Review 8299's "61 parts / 19 types" is the pre-B-04 count; this RC4 tree has 59 parts because
B-04 step 1 removes the two doors, and it still uses exactly 19 types with the same 4 fallbacks.
The `.toc`-sliced module equals the staged copy; the private module's values re-read member by
member with only the named rows changed.

## 3. Hits-to-kill (`damage_predict.py table`)

`build under test: Builds/bm-RC4-damage-collision (max_health 36000)`

| arm | channel | damage | H0 (armour ignored) | H1 (percentage gate) | H2 (threshold + pool) |
|---|---|---:|---:|---:|---:|
| pistol | bullet | 30.00 | 1200 | 120000 | never |
| assault_rifle | bullet | 32.00 | 1125 | 112500 | never |
| machine_gun | bullet | 28.00 | 1286 | 128572 | never |
| shotgun | bullet | 144.00 | 250 | 25000 | 285 |
| rpg | explosion | 1500.00 | **24** | 48 | 25 |
| grenade | unknown | 1012.50 | 36 | 36 | 36 |
| tank_cannon | explosion | 1500.00 | **24** | 48 | 25 |
| heli_missile | unknown | 1500.00 | 24 | 24 | 24 |
| heli_mg | bullet | 25.00 | 1440 | 144000 | never |

Read as the model states: H0 ignores armour, H1 is the percentage gate, H2 adds the threshold.
The heavy rounds (RPG / tank cannon) take **24-25 hits** in the honest H2 column; small arms never
reach the threshold while the pool holds. The predictor's own UNKNOWNs apply (part→type for every
vehicle except the monorail flatbed, weapon→armour channel, composition rule) — these are
"whole vehicle takes every hit" numbers, as the tool prints.

## 4. Collision (B-10)

Source of truth: `Working/Translation/T22_REOPEN.md` + `t22_reopen.py --check` = **10/10 oracles**.
The decoded drivable asset is `Physics.Batmobile_V3_Physics` (BmGame export 158266): 2 bodies,
3 boxes, 1 constraint, reached from `SVehicleMesh` @824.

| BmAK box | extents | centre | TM |
|---|---|---|---:|
| chassis 0 | 690.305 x 374.536 x 207.5 cm | (9, 0, 106.75) | identity |
| chassis 1 | 679.585 x 345.688 x 103.5 cm | (0, 0, 79) | identity |
| weapons pod | 166.177 x 189.365 x 39.8 cm | (-30.5, 0, 93.25) | 4.000 deg about y |

**Shipped payload**: `Working/Collision2/batmobile.physicsc` (B-10e's BmAK-chassis variant,
340,368 B, sha256 `0164936b928f821c…`), copied to the tree's
`models/.../sportsmuscle.physicsc`. The body hull is the chassis box, mapped into JC3 axes:

| quantity | m |
|---|---|
| BmAK chassis box 0 (JC3 axes) | min `[-1.8727, 0.030, -3.3615]`, max `[1.8727, 2.105, 3.5415]`, size `[3.7454, 2.075, 6.903]` |
| built body-0 hull AABB | min `[-1.8732, 0.091, -3.359]`, max `[1.8722, 2.166, 3.544]`, size `[3.7454, 2.075, 6.903]` |
| **deviation vs chassis box 0** | x **0.0005**, y **0.061**, z **0.0025** -> max **0.061 m** |
| **deviation vs DIM-1 render bbox** | x **0.1252**, y **0.1960**, z **0.0610** -> max **0.196 m** |

The size is exact on all three axes; the hull sits **6.1 cm higher** than the raw box because the
built hull's floor is the render mesh's floor (0.091 m) while the box's floor is 0.030 m. That is the
one honest miss: the plan's 5 cm band is exceeded by **1.1 cm on the vertical centre**, while the
two horizontal axes are within 5 mm. Against the render bbox the hull is deliberately wider/lower
(BmAK's drivable box vs the render silhouette), so the 0.196 m figure is a difference, not an error.

**What the built set carries**: 5 hulls written (body 0 + the 4 wheels), **62 donor body entries**
stay (JC3's per-part contact), **2 of BmAK's 3 boxes have no shape instance** (chassis box 1 and the
pod), **0 of 54 hull slots are free** (the 14 unbound instances are the donor bumpers), and the
**1 constraint is a named omission** — no JC3 constraint writer is decoded. `jc3hkx` re-reads the
file clean: 430 objects, 54 convex hulls, 22 compounds / 112 instances / 22 exact AABB unions,
0 station sets (R3: stations untouched).

Scope note, stated rather than implied: `bm_health.py` was extended with `--base`/`--tag` and run
into this tree. `bm_collision.py` still targets DIM-1's render bbox (its 5 cm body-bbox plan is the
one T22_REOPEN supersedes), and `bm_colhull.py` builds the mesh's convex hull (the B-10c plan the
drivable asset replaces). Neither was re-run to overwrite the BmAK-box payload; the shipped
collision is B-10e's already-written BmAK variant. Running either old plan would ship the wrong hull.

## 5. Files changed, why, and how to revert

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/bm_health.py` | `--base`/`--tag` (`set_tags`), tag-specific spec `Working/Damage/bm_health_bm-RC4-damage-collision.json`, refuse in-place rebuild of a foreign tag | B-09's generator had `bm-002`/`bm-009` hard-coded | `git checkout -- Tools/scripts/bm_health.py` |
| `Builds/bm-RC4-damage-collision/` | new tree: `aaf/` (health module, wheels, `.epe`, BmAK `sportsmuscle.physicsc`), `.ee`, `.toc`, `receipt.json`, `install.ps1` | the requested output | `rm -rf Builds/bm-RC4-damage-collision` |
| `Working/Damage/bm_health_bm-RC4-damage-collision.json` | generated spec for this tag | keeps `Working/Damage/bm_health.json` (bm-009) intact | delete the file |
| `tmp/freebuff/reports/build-d08-health-collision.md` | this report | the requested record | delete it |

Nothing was installed, launched or attached to; the game folder was not written.

## 6. UNKNOWNs

1. **The 6.1 cm vertical offset** of the body hull vs BmAK chassis box 0 — caused by the render
   floor; whether the engine wants box-space or mesh-space placement is a drive question.
2. **The constraint's parent/child** — no `RB_ConstraintSetup` layout; the 1 constraint stays a
   named omission.
3. **Whether the pod body is simulated** (bool at 0x224 true, unnamed) and **whether 2 shapes can be
   added** — 0 free hull slots; S2's 5-minute discriminator was not run.
4. **Hits-to-kill is model-level**: no part→type for this vehicle, no weapon→armour channel, and the
   composition rule is unstated (damage_predict's own list).
5. **No drive** — Q-2 kerb/ram and the damage feel are unobserved (test ban).
