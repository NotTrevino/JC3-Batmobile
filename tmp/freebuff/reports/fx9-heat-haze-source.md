STATUS: done. T-FX9's "JC3 has no haze path" is a **keyword** negative, and it does not survive a
search at the level the format stores. No `.effc` in the game carries a single string, so the
original test (`haze`/`steam`/`heat` in 955 *paths*) could only ever find a filename. Searched
properly: JC3 ships **two real distortion/refraction texture families**, an exhaust-mounted effect
carried by **12 base-game vehicles** and attached by **24 objects literally named
`z80_exhaust_heat_l/r`**, and an effect whose render block is **unique in the whole corpus**. The
closest carrier to BmAK's heat-steam is `car_speedrom_heater.effc`. What is *not* decodable is the
per-instantiator blend mode and which texture each emitter binds — those are hashes with no name
table, so they are UNKNOWN, not absent.

## Files written

| file | what |
|---|---|
| `tmp/freebuff/reports/fx9-heat-haze-source.md` | this report |
| `Tools/scripts/fx9_haze.py` | new tool, `write` / `check`; re-scans the archives, 12/12 gates pass |
| `Research/JC3Grab/FX9_HAZE.md` | generated tables (paths, strings, textures, blocks, candidates, BmAK) |
| `Research/JC3Grab/FX9_HAZE.json` | same numbers, digest `1635cca08e759db67408899656fb7f707a453328` |
| `tmp/freebuff/scratch/scan_fx_strings.py`, `fx_hash_index.py`, `fx_candidates.py` | scratch scanners used before the tool existed |

No build tree, ledger row or `Builds/bm-*` file was touched. Revert = delete the five files above.

## What was searched

1. **All 955 distinct `EffectRTSystem` `.effc` paths** in `FX_TABLE.jsonl` (25,025 `.effc` rows in
   total, 57,187 fx rows), for the words `haze steam heat distort refract vapor vapour shimmer warp
   exhaust afterburner jet turbine bavarium fire smoke rotor`.
2. **Every string value inside all 955 files.** Decoded with the project's ADF v4 reader
   (`jc3fx.decode` → `jc3adf.walk`). A `.effc` is ADF v4 and a texture or shader name would be a
   `String` (`0x8955583E`) member — **result: 0 string values in 955/955 files.** The only strings
   the walker returns are the empty array labels of the container itself.
3. **The whole texture pool**: 25,707 `.trim` records, **208 distinct names**, named
   `<texture>.<grid>.trim` — the only place in this format a texture is named.
4. **The material/shader identity space**: `Instantiators[].RenderInfos[].RenderBlockTypeHash`,
   counted over all 955 effects. **8 distinct values** (below).
5. **Twelve candidate effects opened and censused** (exhaust, jet/turbine, rotor wash, fire,
   Bavarium trail, the unique-block explosion).
6. **BmAK side**: every one of the 206 systems in `PARTICLES_FEATURES.json` filtered for a
   distortion/steam material, plus the `heat-steam` and `afterburner-exhaust` groups.

## 1. Path keywords over the 955 (decoded)

| word | paths | note |
|---|---:|---|
| `haze` | 0 | |
| `steam` | 0 | |
| `heat` | **1** | `effects/jc_vehicles/exhaust/car_speedrom_heater.effc` |
| `distort` | 0 | |
| `refract` | 0 | |
| `vapor` / `vapour` | 0 / 0 | |
| `shimmer` / `warp` | 0 / 0 | |
| `exhaust` | 39 | 14 real vehicle exhaust effects |
| `afterburner` | 0 | |
| `jet` | 22 | includes `jet_exhaust_base`, `jet_cargo_exhaust_base`, `rocketboat_jet_exhaust`, `jet_wash_*` |
| `turbine` | 0 | |
| `bavarium` | 82 | includes `effects/trails/bavarium_trail_03.effc` |
| `fire` | 57 | `dmg_fire_engine`, `generic_fire_single_01`, … |
| `smoke` | 29 | |
| `rotor` | 28 | `rotor_wash_*` |

This reproduces T-FX9's own hit and shows why it read as a negative: the only distortion carrier in
JC3 is **not named after the effect**, it is named after the part it hangs on (`exhaust_heat`), and
it sits one level up, in the entity graph, not in the effect path.

## 2. Strings inside the files (decoded)

**0** non-empty string values across 955/955 files. Consequence, and it is the reason T-FX9 could
never be settled by name: **a JC3 effect file physically cannot name a texture, a shader or a blend
mode.** Material identity is a hash; blend mode is a field inside the render block, not a string.

## 3. Texture pool - the distortion assets do exist (decoded)

Words with hits among all 208 distinct `.trim` names:

| word | distinct names | names |
|---|---:|---|
| `dist` | 2 files, 1 stem | `e_smoke02dist_alpha_dif.tga.1_1d.trim` (bare + `effects/textures/…`) |
| `refract` | 3 files, 2 stems | `t_blast_refraction_alpha_dif.tga.1_1d.trim`, `t_blast_refraction_alpha_dif_b.tga.1_1d.trim` |
| `blur` | 2 | `t_explosiongrid_fumeblur_01_alpha_dif.tga.4_8ab/4_8bb.trim` |
| `haze`, `heat`, `steam`, `vapor`, `vapour`, `warp`, `shimmer` | **0 each** | — |

So JC3 has a smoke-**distortion** texture and a blast-**refraction** texture, and the refraction one
ships as a real 512×512 texture (`effects/textures/t_blast_refraction_alpha_dif.ddsc`, 349,680 B,
`DECODE_DEPTH.md:92`, trim grid "w-1 h+0 / w+0 h-1" in `DECODE_DEPTH5.md:117`). Carrier counts:

| texture family | `.trim` records | bundles carrying it |
|---|---:|---:|
| `e_smoke02dist_alpha_dif` | 625 | 625 |
| `t_blast_refraction_alpha_dif` (+ `_b`) | 391 | 385 |

The z80 jeep bundle that owns the heater effect carries both (`t_blast_refraction_alpha_dif` and
`e_smoke02dist_alpha_dif` are in its 65 trims), so the ingredient of a heat shimmer is present in the
same container as the exhaust-heat effect.

## 4. Render-block hashes - the shader identity space (decoded)

| hash | effects using it |
|---|---:|
| `3012430835` | 930 |
| `2199516487` | 487 |
| `522936798` | 240 |
| `160885388` | 201 |
| `1562615418` | 195 |
| `596852081` | 192 |
| `1338734832` | 117 |
| `2813794826` | **1** — only `effects/jc_environments/structures/military/bavarium_refinery_explosion.effc` |

Eight block types are all JC3's particle renderer exposes to content. That also bounds the answer to
"which shader": there is no per-effect shader name, only membership in this 8-value set (53 distinct
`TypeHash` values cover the emitter/modifier classes).

## 5. Candidate emitter settings

Decoded from each file's `EmitterTemplates[]`, `Emitters[]`, `Instantiators[]` and
`OutputBufferDescriptor`. `inst / emit / tmpl` = array lengths; `MaxParticles` is per template;
`blocks` counts render-block batches per hash.

| effect | bytes | carriers | inst | emit | tmpl | MaxParticles | tmpl Flags | emit Flags | blocks (batches) | Properties | OutBuf |
|---|---:|---:|---:|---:|---:|---|---|---|---|---:|
| **`car_speedrom_heater.effc`** | 14,703 | **12** | 5 | 5 | 5 | 10, 60, 3, 7, 100 | 1,1,1,0,1 | 1,1,3,2,3 | `3012430835`:8, `2199516487`:2 | 20.0, 100.0 | 41,520 |
| `car_cycle_base.effc` | 9,695 | 128 | 2 | 2 | 2 | 50, 50 | 1,1 | 0,0 | `3012430835`:4 | -1.0, 50.0 | 11,328 |
| `car_cycle_base_nitrous.effc` | 15,359 | 132 | 8 | 8 | 8 | 20,5,30,20,10,1,1,1 | 0,1,1,1,1,1,1,1 | 3,0,2,1,3,3,0,0 | `3012430835`:10, `2199516487`:2, `1562615418`:2, `522936798`:2 | 10.0, 500.0 | 12,256 |
| `jet_exhaust_base.effc` | 18,927 | 6 | 11 | 11 | 11 | 64,64,20,16×5,1,100,16,16 | 1×11 | 2,3,3,2,3,2,3,3,1,2,3 | `3012430835`:20, `2199516487`:2 | 20.0, 100.0 | 40,832 |
| `jet_cargo_exhaust_base.effc` | 14,351 | 9 | 7 | 7 | 7 | 10,30,16,16,1,16,16 | 1×7 | 2,3,3,3,3,2,3 | `3012430835`:12, `2199516487`:2 | -1.0, 500.0 | 12,096 |
| `rocketboat_jet_exhaust.effc` | 13,727 | 2 | 7 | 7 | 7 | 64,64,64,20,1,16,16 | 1×7 | 2,3,3,3,3,2,3 | `3012430835`:10, `2199516487`:4 | 20.0, 100.0 | 23,376 |
| `helicopter_base.effc` | 11,215 | 34 | 3 | 3 | 3 | 20, 100, 100 | 1,1,1 | 2,2,0 | `3012430835`:6 | 20.0, 100.0 | 26,432 |
| `dmg_fire_engine.effc` | 15,615 | 192 | 5 | 5 | 5 | 50,50,100,100,1 | 1×5 | 0,1,1,1,3 | `3012430835`:8, `2199516487`:2 | 20.0, 500.0 | 65,920 |
| `rotor_wash_asphalt.effc` | 9,039 | 65 | 2 | 2 | 2 | 200, 200 | 1,1 | 1,1 | `3012430835`:4 | 20.0, 100.0 | 48,128 |
| `bavarium_trail_03.effc` | 11,791 | 34 | 4 | 4 | 4 | 86, 10, 20, 100 | 0,0,0,0 | 0,0,0,0 | `3012430835`:8 | 20.0, 500.0 | 39,264 |
| `generic_fire_single_01.effc` | 11,807 | 145 | 4 | 4 | 4 | 14, 1, 20, 5 | 0,0,0,0 | 0,3,0,2 | `3012430835`:6, `2199516487`:2 | 20.0, 100.0 | 9,520 |
| `bavarium_refinery_explosion.effc` | 44,335 | **1** | 35 | 28 | 28 | up to 200 | mostly 0 | mostly 0 | `3012430835`:82, `2813794826`:2, +5 | 20.0, 700.0 | — |

**Blend mode: UNKNOWN for every one of them.** There is no blend enum member in the decoded path set
(`FX_VOCAB` has 94 `.effc` member paths: no `Blend`, no `Material`, no `Texture`, no `Sampler`), and
the render block is an opaque `uint32[]`. What *is* readable per instantiator is
`RenderBlockData[]`, which contains floats. For the heater effect:

| instantiator | block | `RenderBlockData[]` as uint32 → float |
|---|---|---|
| 0 (sprite, header 64 B) | `3012430835` | `[3125323646, 0, 0, 1056964608=0.5, 100, 0, 1065353216=1.0, 0.5, 100, 0, 1.0, 3542070757, 1.0, 0, 3238604654, 2178, 32, 1.0, 0, 1092616192=10.0]` |
| 1 (sprite) | `3012430835` | `[436538540, 6, 16, 0.5, 100, 0, 1084227584=5.0, 0.5, 100, 0, 1.0, 3735928559, 1.0, 1098907648=8.0, 168989877, 0, 28, 1.0, 0, 10.0]` |
| 2 (mesh, header 16 B) | `2199516487` | `[1, 0, 1, 0]` |
| 3 (sprite) | `3012430835` | `[869501834, 6, 4, 0.5, 100, 0, 10.0, 0.5, 100, 0, 1.0, 1449055171, 1.0, 8.0, 1403783250, 48, 28, 1.0, 0, 10.0]` |
| 4 (sprite) | `3012430835` | `[124404425, 6, 1, 0.5, 50, 0, 1101004800=20.0, 0.5, 100, 1.0, 0, 3735928559, 1.0, 8.0, 4131540938, 4177, 32, 1.0, 0, 10.0]` |

Four sprite instantiators with four different `RenderBlockData[0]` values (3125323646, 436538540,
869501834, 124404425) — i.e. four different texture/per-material constants inside one effect. Those
values are the per-emitter texture binding, but **which texture** is UNKNOWN: no string names them
and the three standard hashes do not resolve them (see §7).

`TrimIndex` is `14` on almost every instantiator of almost every effect in the corpus (e.g.
`headlight_flare_01` and `car_speedrom_heater` both `14`), so it is a global trim-mode constant, not
a per-file or per-emitter trim reference; it cannot be used to bind a texture. UNKNOWN.

## 6. BmAK side - where the heat haze actually lives

`heat-steam` feature group, verbatim from `PARTICLES_FEATURES.json`:

```json
{"name": "heat-steam", "systems": 0, "rows": 0, "distinct": 0, "emitters": 0,
 "referenced": 0, "lifetime": null, "spawn_rate": null,
 "note": "no system of that name ships in the 206; heat/steam is the HUD + audio side
          (G1-14 recorded the weapon generator heat, not a particle)"}
```

So on the BmAK side there is **no heat-steam system to match emitter-for-emitter**, exactly as
G1-16/T-FX9 say. But distortion is present as a *material* in 16 distinct systems:

| BmAK system | group | emitters | lifetime | distortion material |
|---|---|---:|---|---|
| `batmobileExhaust_burst` | afterburner-exhaust | **17** | 0.05 .. 1.5 | `Engine.Fire_Distortion` |
| `SideExhaust_Boost` | afterburner-exhaust | 5 | 0.15 .. 0.35 | *(none - `Engine.INST_JetExhaust`, `Engine.MAT_Fire_Dissipate`)* |
| `SideExhaust_Burst` | afterburner-exhaust | 3 | 0.1 .. 0.4 | *(none - `Engine.Fire_Flames3`, `Engine.explosion_med_01`)* |
| `Batwing_Booster_CINE` | afterburner-exhaust | 11 | 0.05 .. 2.0 | `Engine.Distortion_mesh` |
| `Batwing_Exhaust_P` | afterburner-exhaust | 11 | 0.3 .. 5.0 | `Shaders.Engine_Distortion` |
| `Batmobile_Explosion` | explosion | 14 | 0.1 .. 5.0 | `Engine.MAT_Distortion_MESH` |
| `Batmobil_Rocket_Explosion_Small` | explosion | 9 | 0.2 .. 3.0 | `Engine.steam` |
| `EMP_Burst_Stage_01..03` | emp | 10 each | 0.2 .. 1.0 | `Engine.AR_Distortion` |
| `EMP_Burst_Stage_04` | emp | 13 | 0.2 .. 4.0 | `Engine.AR_Distortion`, `Engine.MAT_Distortion_MESH` |
| `Batmobile_canonMuzzleflash` / `_NV` | muzzle-flash | 4 / 5 | 0.05 .. 1.0 | `Engine.steam` |
| `Anti_firearm_gel_Miss` / `_Px` | gel-rounds | 14 / 15 | 0.1 .. 1.0 | `Engine.Distort_s` |
| `RiotSuppressor_BulletCasing` | casings | 6 | 0.05 .. 1.1 | `Engine.steam` |
| `Batmobile_Seismic_Sonar` / `_Charged` | sonar | 7 / 10 | 1.0 .. 10.0 | `Materials.SeismicScan_Distortion` |

The heat-steam the operator sees above the exhaust is therefore the **`Engine.Fire_Distortion`
emitter inside `batmobileExhaust_burst`** (17 emitters: 9 sprite, 2 mesh, 2 light, 4 stubs; life
0.05–1.5 s; rate 0–15/s), not a system of its own. Its material name is a *name*, because BmAK is
UE3 `.upk` and the project reads export names; JC3 gives only `3012430835`-style ids.

## 7. Comparison, one candidate at a time

| candidate | what it carries that BmAK needs | what it does not |
|---|---|---|
| **`car_speedrom_heater.effc`** | 5 emitters (4 sprite + 1 mesh) at an exhaust, 5 templates, `MaxParticles` 10/60/3/7/100; 12 base-game vehicles carry it and 24 graph objects named `z80_exhaust_heat_l/r` attach it (card-B-08 trace, re-counted here as 12 carriers); lives in the same bundle as `e_smoke02dist` + `t_blast_refraction` textures | no distortion material *name*; blend mode UNKNOWN; no per-emitter texture binding decoded |
| `jet_exhaust_base.effc` | afterburner-scale plume: 11 emitters, 20 sprite batches + 1 mesh, MaxParticles up to 100 | it is a flame plume; no distortion-specific block; 6 carriers only |
| `jet_cargo_exhaust_base.effc` / `rocketboat_jet_exhaust.effc` | large-vehicle exhaust, 7 emitters each, mesh block ×2/×4 | same; no distortion block distinction |
| `helicopter_base.effc` | turbine exhaust, 34 carriers, 3 emitters | sprite-only, no mesh block, no distortion |
| `rotor_wash_asphalt.effc` | airborne downwash, 200-particle emitters, 65 carriers | dust, not refraction; no mesh block |
| `bavarium_trail_03.effc` | hot trail, 4 emitters, 34 carriers | all blocks `3012430835`, no unique/distortion block |
| `dmg_fire_engine.effc` | engine fire and smoke, 5 emitters, 192 carriers | fire/smoke, not shimmer |
| `bavarium_refinery_explosion.effc` | **the only effect in 955 using block `2813794826`**, 35 instantiators, 28 emitters, up to 200 particles | one carrier only, an environment explosion; what that block does is UNKNOWN |

**Hash-oracle test (negative).** To rule out "the texture is named, we just cannot see it", the four
per-emitter `RenderBlockData[0]` values were hashed against all 109 texture stems in the corpus, with
`crc32`, FNV-1a-32 and FNV-1-32, bare and with `effects/textures/`, `_dif`, `_alpha_dif`, `.tga`,
`.tga.1_1d` suffixes: **0 matches**. So the binding is not a trivial name hash; texture naming stays
UNKNOWN.

## 8. Verdict

**Closest carrier: `effects/jc_vehicles/exhaust/car_speedrom_heater.effc`.** It is the only effect in
the corpus whose name or attachment says *heat*, it is mounted at exhausts on 12 shipped cars by 24
objects named `z80_exhaust_heat_l/r`, it is a multi-emitter sprite+mesh effect (5 emitters, 100-particle
ceiling), and its bundle ships both JC3 distortion textures. It is a **carrier**, not a proof of
refraction: whether its sprites actually bend the image behind them cannot be read from the file.

Runner-up for the *distortion* half: block `2813794826`, used by exactly one effect
(`bavarium_refinery_explosion.effc`). Eight block types exist in all of JC3; a distortion/refraction
block is almost certainly one of them, and this is the only one no other effect uses — but naming it
is UNKNOWN, so this is a lead, not a finding.

### What would have to change in a private copy

1. **Attach, do not author.** A copy of `car_speedrom_heater.effc` needs no new bytes to be carried:
   the z80 objects reference the effect by hash from the entity graph, so the Batmobile entity gets an
   object of the same class at the `Afterburner` socket (T-FX7/T-FX8 pattern), pointing at the same
   `.effc` hash. That reproduces placement and emitter set exactly.
2. **Strength** is per-instantiator `RenderBlockData[]` floats (0.5 = `1056964608`,
   5.0 = `1084227584`, 8.0 = `1098907648`, 10.0 = `1092616192`, 20.0 = `1101004800` in the heater
   effect). Editing those uint32s is how the shimmer's rate/scale would be tuned — which slot is
   which is UNKNOWN, so a private copy must be tuned by changing one slot at a time and observing
   (the test ban applies: this stays a build-time step, recorded, not run here).
3. **BmAK parity of the emitter list** needs the `batmobileExhaust_burst` distortion emitter's job
   (`Engine.Fire_Distortion`, 0.05–1.5 s life) carried by the heater's 4 sprite instantiators. The
   heater gives 4 sprite + 1 mesh at 10/60/3/7/100 particles, so the count is available; the
   *distortion* material is the part that cannot be named on the JC3 side.

### The exact missing capability, if this carrier is rejected

JC3 content can reference a render block by hash, and the whole game ships **8** of them; it cannot
author a new one, and a `.effc` stores no material name, no blend enum and no texture path. So the
capability that would have to be added is:

> **an authorable particle material with a refraction/distortion blend, addressable from a `.effc`
> instantiator by something other than one of the 8 shipped `RenderBlockTypeHash` values, plus a
> readable per-emitter texture reference** — i.e. a material registry the mod layer can extend
> (BmAK's `Engine.Distort_s` / `Engine.Fire_Distortion` equivalent). No such registry is present in
> the archives; the 8 hashes and the 208-name trim pool are the entire surface.

Per the operator rule, T-FX9 should therefore be re-opened as a **to-do**, not left `out`: carrier
named (`car_speedrom_heater.effc`, 12 carriers, 24 `exhaust_heat` objects), gap named (the block
above).

## Commands and output, verbatim

```text
$ python tmp/freebuff/scratch/scan_fx_strings.py --json tmp/freebuff/scratch/fx_strings2.json
effc paths: 955 of 25025 rows
CONTAINER FAIL : ''
  120 files, 0 distinct strings
  ...
  900 files, 0 distinct strings

files decoded: 955   distinct strings: 0

== string member paths ==

== strings matching distortion words ==
(0 distinct)
wrote tmp/freebuff/scratch/fx_strings2.json
```

```text
$ python tmp/freebuff/scratch/fx_hash_index.py
files 955
RenderBlockTypeHash: 8 distinct
TypeHash: 53 distinct
wrote ...\tmp\freebuff\scratch\fx_hash_index.json
```

```text
$ python tmp/freebuff/scratch/fx_candidates.py
### effects/jc_vehicles/exhaust/car_speedrom_heater.effc
  size 14703 B | rows 1943 | carries in 12 containers | mount base
  instantiators 5 | emitters 5 | emitter templates 5
  RenderBlockTypeHash (batches): {3012430835: 8, 2199516487: 2}
  Properties [20.0, 100.0]
  OutputBufferSize [41520]
  TrimIndex [14, 14, 65535, 14, 14]
...
```

```text
$ python Tools/scripts/fx9_haze.py write --write
wrote E:\Modding\JustCause3\JC3-Batmobile\Research\JC3Grab\FX9_HAZE.md
wrote E:\Modding\JustCause3\JC3-Batmobile\Research\JC3Grab\FX9_HAZE.json
effc 955 strings 0 blocks 8 trims 208 digest 1635cca08e759db67408899656fb7f707a453328

$ python Tools/scripts/fx9_haze.py check --check
  effc_paths             PASS
  files_decoded          PASS
  string_values_zero     PASS
  string_values_same     PASS
  block_hashes_same      PASS
  type_hashes_same       PASS
  trim_names_same        PASS
  trim_distortion_same   PASS
  candidates_same        PASS
  bmak_same              PASS
  digest_same            PASS
  md_matches             PASS
gates 12/12 pass
```

## UNKNOWNs

1. **Blend mode of every JC3 particle emitter.** Tried: all 94 decoded `.effc` member paths
   (`FX_VOCAB.json`) — no blend/material/texture/sampler member; the render block is `uint32[]` with
   no declared layout. Would be found in: the engine's render-block layout, not in the archives.
2. **Which texture each heater instantiator binds.** Tried: four distinct `RenderBlockData[0]`
   values, hashed against all 109 texture stems under crc32 / FNV-1a / FNV-1 with six suffixes
   (0 matches); `TrimIndex` is the constant 14 corpus-wide, so it is not the binding. Would be found
   in: a texture-name↔hash table for effects, which the archives do not carry.
3. **What block `2813794826` is** (the single-effect block in `bavarium_refinery_explosion`).
   Tried: cross-referenced every effect using it (n=1) and every block's effect set. Would be found
   in: the same missing render-block registry.
4. **Whether `car_speedrom_heater` actually bends the image** (as opposed to being a warm smoke puff
   named "heat"). Tried: name, placement on 12 vehicles via 24 `z80_exhaust_heat_l/r` objects,
   sprite+mesh composition, distortion textures in the same bundle. Would be settled by: one captured
   frame of a Z80 with the effect running — **not run** (test ban).
5. **Emitter flag semantics** (`template Flags` 1/0, `emitter Flags` 1/2/3) — no decoded meaning, so
   no claim is made that the heater loops, spawns on death, or is one-shot.
