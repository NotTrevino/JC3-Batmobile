# D-07 · B-08 effects refresh — `Builds/bm-RC4-effects`

**STATUS: built, `bm_fx.py --check` green (0 failures).** The afterburner flame is placed on the
`Afterburner` socket in the RC4 line, every Effect hash resolves to an `.effc` path that is a file
in the build tree (30/30, 0 unresolved), and every `(Usage, object)` pair is in the fleet's
155-value vocabulary (65/65, 0 outside). No new usage was declared and none was needed.

| gate | result |
|---|---|
| Effect objects / distinct hashes | 36 / 30 |
| Hashes resolving to exactly one fleet `.effc` path | **30 / 30** |
| Those paths that are files in `Builds/bm-RC4-effects/aaf` | **30 / 30** (tree carries 74 `.effc`) |
| T-17 chosen paths inside the fleet vocabulary | **17 / 17** |
| Usage pairs outside the 155-value vocabulary | **0 / 65** (`declared new usages: none`) |
| Flame path in the build tree | `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` = True |
| Emitters carrying the flame | 2 (`exhaust_upgrade_nitrous`, `exhaust_upgrade_nitrous2`) |
| Emitter usage | **4197885156 = `EngineNitro`** |
| Object count | 416 -> 416 (0 added, 0 removed) |

## 1. Commands run

```text
python Tools/scripts/bm_fx.py --write --base bm-RC4-parts --tag bm-RC4-effects
python Tools/scripts/bm_fx.py --check --base bm-RC4-parts --tag bm-RC4-effects
```

Exit codes `0` and `0`. The check ends:

```text
PASS: Builds/bm-RC4-effects/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe 416 -> 416 objects, 2 mat edit(s) on socket Afterburner (JetSMove)
  Done 1  effect paths: 36 effect objects / 30 distinct Effect hashes, 30 resolve to exactly one of the fleet's `.effc` paths, 0 unresolved, 30/30 present in the build tree; T-17 chosen paths 17/17 in the vocabulary; flame path effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc in the build tree = True (donor container set 74 `.effc`)
  Done 2  usage vocabulary: 65 (usage, object) pairs over the 155-value fleet vocabulary, 0 outside; the 2 emitter(s) carry [4197885156] = ['EngineNitro']
```

Base is **`Builds/bm-RC4-parts`** (the RC4 line's 688-file entity tree, `.epe`
`v0300_car_kensington_sportsmuscle_civilian_01.epe`); the RC4 line still ships the donor leaf until
B-13b's rename is merged, so `bm_fx.py` now reads the single `.epe` name from the base tree instead
of hard-coding `civilian_01`. This is a **step tree**, not the merged RC: no `.ee`/`.toc` is written.

## 2. What was edited

| path | bytes | sha256 |
|---|---:|---|
| `aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` | 105,430 | `2ec0dcecb099a1bcec2abd96c96ba0d4fe8d29e9998e44fc11613ba6e11825b7` |
| `aaf/` tree | 688 files copied from `bm-RC4-parts` | 74 `.effc` present, unchanged |
| `receipt.json`, `install.ps1` | generated | installer never run |

Two `SAttachedEffect.world` matrices, no structure change:

| object | old (donor Serpente exhaust) | new (`Afterburner`) |
|---|---|---|
| `exhaust_upgrade_nitrous2` | `-0.4101563, 0.3728027, 2.47998` | `-0.009578, 0.537762, 3.393177` |
| `exhaust_upgrade_nitrous` | `0.4101563, 0.3728027, 2.47998` | `-0.009578, 0.537762, 3.393177` |

Socket `Afterburner`, bone `JetSMove` (parent `Batmobile_Chassis_Mesh`), world
`-3e-06,1,1.17e-10,0,1,3e-06,-3.9e-05,0,-3.9e-05,0,-1,0,-0.009578,0.537762,3.393177,1`.
The two emitters already pointed at the nitrous flame under `EngineNitro`; only their placement was
the Serpente's. **T-FX3's operator approval is therefore applied as decoded** — the usage is the
shipped one, and no new usage exists.

## 3. Which BmAK effects are carried by a new private effect, and which by a shipped one

**New private `.effc` authored in this build: 0.** Private copies are B-17 (the `.effc` writer,
`Working/Effects/EFFC_WRITER.md`: 95/95 sampled effects re-encode byte-identically, so the writer
exists but has not been run to author these copies). Every BmAK effect below rides a **shipped**
JC3 effect in this build:

| row | BmAK effect | carrier in this build | shipped / private |
|---|---|---|---|
| T-FX7 | afterburner flame (`batmobileExhaust_burst` family) | `car_cycle_base_dual_nitrous.effc`, 2 emitters moved to `Afterburner` | **shipped, written** |
| T-FX8 | base exhaust / idle | `car_cycle_base_dual.effc`, donor objects kept | shipped, kept |
| T-FX9 | heat haze (`batmobileExhaust_burst`) | `car_speedrom_heater.effc` (the fleet's only heat-named effect) | **shipped**; tuning copy = B-17 |
| T-FX10 | cannon muzzle flash | `tank_canon_muzzleflash.effc` | shipped; attach rides B-06 |
| T-FX11 | Vulcan muzzle flash | `helicopter_minigun_muzzleflash.effc` | shipped; B-06 |
| T-FX12 | tracers (art half) | `missile_trail_car.effc`; linear half is the cloned `WeaponTuning` | **shipped**; private copy = B-17 |
| T-FX13 | shell casings | `bullet_eject_minigun.effc` + `SAttachedEffect ShellEjection` (Effect 600259254, Usage 4131019937 = `Fire`) | **shipped**; copy/attachment on the weapon = B-17 |
| T-FX14 | missile launch trail | `missile_trail_car.effc` | shipped; B-06 |
| T-FX15 | cannon impacts | `tank_explosive_default.effc` (+ 7 surface variants) | shipped; B-06 |
| T-FX16 | cannon round trail | `missile_trail_car.effc` (same file as T-FX12) | **shipped**; private copy = B-17 |
| T-FX17 | tyre smoke / kick-up | `dust_trail_asphalt.effc` (6 variants) | shipped, kept |
| T-FX18 | slide dust | `chassis_slide_default.effc` (5 variants) | shipped, kept |
| T-FX19 | wall-scrape sparks | `spark_trail_02_med.effc` on `dynamic_trail_effect` | shipped, donor carried |
| T-FX20 | brake-light trails | restyle of `car_cycle_base_dual_nitrous.effc` at `BrakeTrailL/R` | **shipped**; private copy + authored brake trigger = B-17 |
| T-FX21 | death explosion | `exp_car_01.effc` | shipped, kept |
| T-FX22 | burn states | `dmg_fire_engine.effc` (3 variants) | shipped, kept |
| T-FX23 | post-burn / engine smoke | `dmg_post_burn.effc` | shipped, kept |

So the answer to "which are carried by a new private effect": **none yet** — the five rows that ask
for a private copy (T-FX9 heat haze, T-FX12 tracer, T-FX13 casings, T-FX16 round trail, T-FX20 brake
trail) all name a shipped carrier and an authoring plan, and B-17 owns the copy. The one effect this
step actually writes into the graph is the flame, and it rides the shipped nitrous effect.

Private-copy constraint recorded for B-17: the build-tree gate counts only paths present as files
under `aaf/`. T-FX9's `car_speedrom_heater.effc` is **not** in this tree today (it is not referenced
by the `.epe`), so attaching it requires copying the file into `aaf/effects/...` and registering it
in `@files.xml`; the same applies to `missile_trail_car.effc` and `bullet_eject_minigun.effc`.

## 4. Review 8299's open numbers, as they bear on this build

- **T-FX20** brake-trail width/length/colour: no `ParticleSystem` template, float at `@364` unnamed
  — so no BmAK number exists to write; the row is carried by the plan, not by a value.
- **T-FX12** tracer colour/material: `tracer_texture_type` is enum `1` and the `.ddsc` is unnamed —
  the linear half is tunable in the clone, the art half stays the shipped carrier.
- **T-FX9 / T-FX16** ride shipped effects, exactly as this build reports.
- **T-FX5's "23 unreferenced `.effc`"** remains UNKNOWN (the producer never states what it counted);
  it is not used by this build's gates.

## 5. Effect-hash resolution detail

`bm_fx.py` now asserts the stronger criterion the brief names: for every distinct `Effect` value in
the built `.epe`, the hash must map (through `Research/JC3Grab/FX_TABLE.jsonl`, 955 distinct
`.effc`) to exactly one path, **and that path must exist under the build's `aaf/`**. The RC4 base
already satisfied it (30/30 in tree); the flame's path is the donor's own and is present. The gate
also still checks the T-17 chosen paths against the fleet vocabulary (17/17) and the flame path
against the donor container set (74 `.effc`).

`bm_fx.py --check` with its default `bm-008` target is **red**, but not from this run:

```text
FAIL: the built .epe differs from the re-derived plan: 6 object(s) missing, 6 unexpected
      (SWeaponPoint ... id:A90F5E74 = weapon_anchor)            # pre-existing B-16 drift
FAIL: Done 1: 2 Effect path(s) are not files in the build tree:
      ['effects/jc_weapons/50_cal/bullet_eject_capstone.effc',
       'effects/jc_weapons/rico_50cal_muzzleflash.effc']        # the new gate on the stale bm-008 tree
```

The first is B-16's known per-branch base drift (bm-008 was built on the pre-rework bm-005 and later
weapon steps wrote `weapon_anchor` into its `.epe`); the second is the new gate correctly flagging
two weapon effects that `bm-008`'s older tree does not carry. Neither mentions a T-17 row or the
flame, and neither is a regression of this step. Fixing bm-008 means rebuilding it from the current
base (B-16), which would edit an existing build tree and is not this brief.

## 6. Files changed, why, and how to revert

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/bm_fx.py` | `--base`/`--tag` (`set_tags`, `.epe` name read from the base), tag-specific spec path, refuse to rebuild a foreign tag in place, build-tree effect-resolution gate, T-17 action table refreshed to 17 carriers / 0 omissions, tag-specific scratch XML | it is B-08's only generator and it had `bm-005`/`bm-008` hard-coded | `git checkout -- Tools/scripts/bm_fx.py` |
| `Builds/bm-RC4-effects/` | new tree: `aaf/` (copy + edited `.epe`), `receipt.json`, `install.ps1` | the requested build | `rm -rf Builds/bm-RC4-effects` |
| `Working/Effects/bm_fx_edits_bm-RC4-effects.json` | generated spec for this tag (bm-008's `bm_fx_edits.json` untouched) | keeps the phase-B record intact | delete the file |
| `tmp/freebuff/reports/build-d07-effects.md` | this report | the requested record | delete it |

Nothing was installed, launched or attached to; no game folder was written.

## 7. UNKNOWNs

1. **Whether the flame renders at the jet nozzle** — the `SAttachedEffect.world` member is binary in
   the RTPC `.epe`; only a render settles it, and no game was launched.
2. **Whether `EngineNitro` fires on the Batmobile's own boost** — the usage is shipped and raised by
   the arcade nitro field; no decoded file states this vehicle's trigger and no probe ran.
3. **Private-copy acceptance** — growth (extra emitters/arrays) by the `.effc` writer is expressible
   in the format but has not been built or re-read; B-17's last step.
4. **T-FX20's brake trigger** — no JC3 brake state exists (9 behaviours, no `Brake`); authoured
   behaviour is B-17.
5. **The two `bm-008` gate failures** — pre-existing base drift, not repaired here (B-16).
