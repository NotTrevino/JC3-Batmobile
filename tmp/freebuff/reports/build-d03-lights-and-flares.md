# D-03 — lights and flares, built into `Builds/bm-RC4-lights`

Date: 2026-11-07. Tree: `Builds/bm-RC4-lights`, a private copy of `Builds/bm-RC4-parts` (D-02)
with one inner file rewritten — the vehicle's `VehicleDynamicLights` module. Not installed, not
launched: `receipt.json` carries `installed: false`, `not_deployed: true`, and nothing in the game
folder was read or written.

```
python Tools/scripts/bm_rc4_lights.py --write     # exit 0
python Tools/scripts/bm_rc4_lights.py --check     # PASS, CHECK_EXIT=0
```

The rows come from `bm_lightrig.plan()` (B-07's generator, imported unchanged — no value is
retyped here), then the five light plans replace the donor numbers where they give one, and the
reverse pair is appended.

## 0. Counts

| count | value |
|---|---:|
| lights built (module entries in `bm-RC4-lights`) | **24** |
| lights planned (28 T-18 rows + 2 reverse additions) | **30** |
| built plan rows (T-18 rows carried into an entry) | **26** |
| blocked plan rows | **2** — `T-L28` (`HeadLight1c`), `T-L30` (`HeadLight2c`), both orphan sockets |
| blocked states with no plan row | **2** — underglow (BmAK has none), brake (no JC3 trigger/behaviour) |
| unproven carriers | **1** — the lamp-bound flare sprite (`T-24`) |
| donor rows dropped (no Batmobile lamp to name) | 10 |
| module rows before → after | 21 → 24 |
| entries by behaviour | `HeadLight` 15, `TailLight` 3, `None` 4, `Reverse` 2 |
| distinct parts used | 7, every one `has_lights = 1` |

26 built T-18 rows + 2 blocked = 28 T-18 rows; + 2 reverse additions = 30 planned; those 26 rows
collapse to 24 entries because three rows ride an already-written lamp row (`T-L25`/`T-L27` ride
`T-L8`; `T-L26`/`T-L29` ride `T-L9`; `T-L31`..`T-L34` ride `T-L13`/`T-L14`).

## 1. What was written

| item | value |
|---|---|
| tree | `Builds/bm-RC4-lights/` (`aaf`, `.ee`, `.toc`, `receipt.json`, `install.ps1`, `verify/`) |
| module | `editor/entities/…/modules/generated/v0300_car_kensington_sportsmuscle_lights.vmodc` |
| module bytes | 6,337 → **7,105 B** (+768), sha256 `01405084AEFE1DDF…` |
| `.toc` record | offset **16,499,504**, size **7,105** (non-zero; matches the `.ee` directory) |
| `.ee` | 11,178,919 → **11,179,037 B** (+118), sha256 `3E1280FBEFACED11…` |
| `.toc` | 60,806 B, 604 records, sha256 `B4F93C034E4D1102…` (size unchanged: the module swap is in-place, the record only moved) |
| inner files differing from `bm-RC4-parts` | **1** — the lights module (`aafdiff --hash`) |
| spec (the row plan, with per-member provenance) | `Working/Lights/bm_rc4_lights.json` |

## 2. Every built light, its plan row, host and values

`part (index)` is the D-02 parts split; the anchor's last node is the socket the BmAK entry hangs
on. Colour is 0–1 sRGB (BmAK `LightColor`/255); range in metres; `vol` is
`volumetric_mode`/`volume_intensity`.

| # | plan row(s) | BmAK socket | part (index) | behaviour | colour | range | angle | mult | lt | sh | vol |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | T-L24 | `Dashboard_Light` | `sportsmuscle_body` (0) | HeadLight | 0.675/0.961/1.000 | 0.8 | 45 | 1.0 | 1 | 0 | 0/1.0 |
| 1 | T-L16 | `BrakeLightR` | `sportsmuscle_tailstrip_r_r` (49) | TailLight | 1.000/0.149/0.000 | 2.0 | 10 | 2.0 | 0 | 0 | 0/1.0 |
| 2 | T-L8, T-L25, T-L27 | `HeadLight1`, `HeadLight1a`, `HeadLight1b` | `sportsmuscle_headlight_f_l` (44) | HeadLight | 0.541/0.773/0.965 | **60.0** | **70** | 1.0 | 1 | 0 | 1/0.002 |
| 3 | T-L12 | `HeadLight2` | `sportsmuscle_headlight_f_r` (45) | HeadLight | 0.875/0.357/0.294 | 2.0 | 10 | 1.0 | 0 | 0 | 0/1.0 |
| 4 | T-L11 | `HeadLight1` | `sportsmuscle_headlight_f_l` (44) | HeadLight | 0.875/0.357/0.294 | 30.0 | 40 | 2.0 | 1 | 0 | 0/1.0 |
| 5 | T-L8 | `HeadLight1` | `sportsmuscle_headlight_f_l` (44) | HeadLight | 0.541/0.773/0.965 | **18.0** | **70** | 1.0 | 1 | 0 | 0/1.0 |
| 6 | T-L12 | `HeadLight2` | `sportsmuscle_headlight_f_r` (45) | HeadLight | 0.875/0.357/0.294 | 30.0 | 40 | 2.0 | 1 | 0 | 0/1.0 |
| 7 | T-L11 | `HeadLight1` | `sportsmuscle_headlight_f_l` (44) | HeadLight | 0.875/0.357/0.294 | 2.0 | 10 | 1.0 | 0 | 0 | 0/1.0 |
| 8 | T-L15 | `BrakeLightL` | `sportsmuscle_tailstrip_r_l` (48) | TailLight | 1.000/0.149/0.000 | 2.0 | 10 | 2.0 | 0 | 0 | 0/1.0 |
| 9 | T-L9 | `HeadLight2` | `sportsmuscle_headlight_f_r` (45) | HeadLight | 0.627/0.706/1.000 | **18.0** | **70** | 1.0 | 1 | 0 | 0/1.0 |
| 10 | T-L9, T-L26, T-L29 | `HeadLight2`, `HeadLight2a`, `HeadLight2b` | `sportsmuscle_headlight_f_r` (45) | HeadLight | 0.627/0.706/1.000 | **60.0** | **70** | 1.0 | 1 | 0 | 1/0.002 |
| 11 | T-L17 | `BattleModeSpotLight` | `sportsmuscle_body` (0) | HeadLight | 0.604/0.604/0.953 | 10.0 | 60 | 1.0 | 1 | 0 | 0/0.25 |
| 12 | T-L10 | `ChainGunMuzzle` | `sportsmuscle_body` (0) | None | 1.000/1.000/1.000 | 10 | 10 | 1 | 0 | 0 | 0/1 |
| 13 | T-L13 (+T-L31/T-L33 riders) | `LWheelLight` | `sportsmuscle_wheel_f_l_arch` (42) | HeadLight | 0.627/0.706/1.000 | 2 | 10 | 1 | 0 | 0 | 0/1 |
| 14 | T-L14 (+T-L32/T-L34 riders) | `RWheelLight` | `sportsmuscle_wheel_f_r_arch` (43) | HeadLight | 0.627/0.706/1.000 | 2 | 10 | 1 | 0 | 0 | 0/1 |
| 15 | T-L18 | `HeadLight1` (battle) | `sportsmuscle_headlight_f_l` (44) | HeadLight | 1.000/0.000/0.000 | **10.24** | **35** | **5.0** | 1 | 1 | 1/0.02 |
| 16 | T-L19 | `HeadLight2` (battle) | `sportsmuscle_headlight_f_r` (45) | HeadLight | 1.000/0.000/0.000 | **10.24** | **35** | **5.0** | 1 | 1 | 1/0.02 |
| 17 | T-L20 | `LWheelLight` (battle) | `sportsmuscle_wheel_f_l_arch` (42) | HeadLight | 1.000/0.000/0.000 | **20.48** | **15** | 1.0 | 1 | 0 | 0/1 |
| 18 | T-L21 | `BattleModeSpotLight` (forensics) | `sportsmuscle_body` (0) | None | 0.765/1.000/0.957 | 50 | 50 | 1 | 1 | 0 | 0/1 |
| 19 | T-L22 | `HeadLight1` (forensics) | `sportsmuscle_body` (0) | None | 1.000/0.000/0.000 | 30 | 35 | 5 | 1 | 1 | 1/0.02 |
| 20 | T-L23 | `HeadLight2` (forensics) | `sportsmuscle_body` (0) | None | 1.000/0.000/0.000 | 30 | 35 | 5 | 1 | 1 | 1/0.02 |
| 21 | T-L35 | `BootLight` | `sportsmuscle_body` (0) | TailLight | 0.596/1.000/0.882 | **4.0** | **60** | 1.0 | 1 | 0 | 0/1 |
| 22 | D-03 reverse (addition) | — | `sportsmuscle_tailstrip_r_l` (48) | **Reverse** | 1.000/1.000/1.000 | 2.0 | 10 | 1.0 | 0 | 0 | 0/1.0 |
| 23 | D-03 reverse (addition) | — | `sportsmuscle_tailstrip_r_r` (49) | **Reverse** | 1.000/1.000/1.000 | 2.0 | 10 | 1.0 | 0 | 0 | 0/1.0 |

Anchors (all rows; the row order matches the table): body rows use
`|sportsmuscle_LOD1|body|Batmobile_Chassis|Batmobile_Chassis_LIG` (rows 0, 21), the drone-decoder
node `…|Batmobile_Rig_Weapons_Drone_Decoder|…_LIG` (rows 11, 18), the gun node
`…|Batmobile_Rig_Weapons_Machine_Gun_01|…_LIG` (row 12); headlight rows use
`|sportsmuscle_LOD1|body|Winch_DOOR_Mesh|Winch_DOOR_Mesh_LIG` (rows 2–7, 9, 10, 15, 16, 19, 20);
tail rows use `…|SUSP2_Wheel_Rear_Left|…_LIG` / `…_Right|…_LIG` (rows 1, 8, 22, 23); wheel rows
use `|sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|Wheel_Frnt_Left_Disc_LIG` and the `_f_r`
mirror (rows 13, 14, 17).

## 3. Which numbers came from which plan

Overrides are keyed by the B-07 row's origin so a re-index cannot silently retarget them; each
member's provenance is stored in `bm_rc4_lights.json` → `rows[].members[].src`.

| row | member | value | plan row and flag |
|---|---|---|---|
| 2, 10 | `range` | 60.0 | headlight-beam-plan §3 (BmAK 6000 cm → 60 m, **M**/**D**; **G** that JC3 renders a shipped-max-exceeding value, U-1) |
| 2, 10 | `angle` | 70 | same (BmAK outer cone **M**; shipped JC3 max is 50, U-1) |
| 2, 10 | `falloff_start` | 0.8 | same (**G**: BmAK falloff is a spot exponent, JC3's is a start fraction) |
| 2, 10 | `multiplier` | 1.0 | same (**G**: no decoded Brightness→multiplier bridge; fleet mode) |
| 2, 10 | `volumetric_mode` / `volume_intensity` | 1 / 0.002 | lens-flare-carriers §2.3, §5.1 (halo = one of three decoded flare carriers) |
| 5, 9 | `range` / `angle` | 18.0 / 70 | headlight-beam-plan §3 (second spot 1800 cm) |
| 5, 9 | `falloff_start` | 0.0 | same (BmAK falloff 2.0 → hard-edged, **G**) |
| 2, 5, 9, 10 | `light_type` | 1 | headlight-beam-plan §3: a cone; fleet `light_type 1` rows are the cones |
| 15, 16 | `range` / `angle` / `multiplier` | 10.24 / 35 / 5.0 | underglow-and-accent §1 (battle: 1024 cm, 10°/35°, Brightness 5.0) with muzzle-and-forensics T-L22's member recipe |
| 15, 16 | `cast_shadows` | 1 | underglow-and-accent §1 (BmAK `CastDynamicShadows` True) |
| 17 | `range` / `angle` | 20.48 / 15 | underglow-and-accent §4 (battle wheel: 2048 cm, 15°) |
| 21 | `range` / `angle` / `falloff_start` | 4.0 / 60 / 0.8 | underglow-and-accent §4 (boot: 400 cm, 50°/60°, falloff **G**) |
| 0 | `range` / `angle` / `falloff_start` | 0.8 / 45 / 0.8 | underglow-and-accent §4 (interior: 80 cm, 20°/45°, falloff **G**) |
| 22, 23 | all 25 members | vanilla `Reverse` tuple | taillight-brake-reverse-plan §3.2 — an **addition**, not a BmAK translation |

Rows 1, 8 (tail) already equalled the plan's vanilla `TailLight` tuple (range 2.0, falloff 0.0,
near_cap 1.0, multiplier 2.0, angle 10.0, colour 1.0/0.149/0.0), row 12 already equalled the
muzzle recipe (range 10, angle 10, white, `light_type 0`), rows 13/14 already equalled the wheel
recipe, and rows 18–20 already equalled the forensics recipes: no change was invented for them.

Row 11 (`T-L17`) keeps the donor graph object's own members (`radius 10`, `spot_angle 60`, `volume 0.25`) —
`apply-light-rows.md` leaves it as the graph-object carrier, and no plan gives it other numbers.

## 4. Lens-flare carriers

`lens-flare-carriers.md` names three carriers; the build places what data can carry and records the
rest.

1. **Emissive lens geometry (`CarLight`)** — already in the D-02 tree; this step only counts it.
   Measured on `Builds/bm-RC4-lights/aaf`: **24 `CarLight` blocks over 8 lamp parts**, one per LOD
   (lod1/lod2/lod3), each RBM's block list exactly `['CarLight']`:
   `headlight_f_l` 13,762 / 12,466 / 7,570 B, `headlight_f_r` 13,762 / 12,466 / 7,642 B,
   `wheel_f_l_arch` 22,078 / 13,720 / 8,110 B, `wheel_f_r_arch` 22,078 / 13,756 / 8,074 B,
   `wheel_r_l_arch` 27,904 / 15,130 / 8,614 B, `wheel_r_r_arch` 27,946 / 15,130 / 8,650 B,
   `tailstrip_r_l` 7,402 / 6,226 / 4,702 B, `tailstrip_r_r` 7,402 / 6,226 / 4,702 B.
   The check fails if any lamp part loses its block.
2. **Volumetric halo on the lamp row** — `volumetric_mode 1`, `volume_intensity 0.002` on the two
   60 m beam rows (2, 10), and `1 / 0.02` on the two battle beams (15, 16) and both forensics
   beams (19, 20), matching the only shipped shadow-casting rows.
3. **Additive billboard sprite** — **not built**: no member binds an effect to a lamp, and
   `.effc` files carry no strings, so `headlight_flare_01.effc` cannot be attached from this
   module. Unproven; card `T-24`.

Per-row flare disposition: rows 2/5/9/10 carry `T-L25`..`T-L27`, `T-L29` (the four socketed
headlight flare rows) — glow + halo placed, sprite unproven; rows 13/14 carry `T-L31`..`T-L34` (the
wheel flare rows) — glow placed on the arch meshes, sprite unproven; `T-L28`/`T-L30` blocked (§5).

## 5. Blocked, and why

| what | plan row | why it is not in the tree |
|---|---|---|
| `T-L28` `HeadLight1c`, `T-L30` `HeadLight2c` | lens-flare-carriers §3, §5.3 | Both rows have a **null socket and null bone** in `LIGHTS.json`, and `LIGHTS.md` lists `HeadLight1c`/`HeadLight2c` as problems ("socket does not exist in the shipped mesh"). The body part has neither a `_LIG` node nor a `CarLight` block, so there is no anchor to hang an entry on. Needs B-03/B-04 geometry, then a row. |
| underglow / underbody lamp | underglow-and-accent §1.2, §5.1 | BmAK ships **no** underglow: 0 of 21 sockets are under/floor, 0 `underglow`/`neon` hits, 0 class-default members. Its low accent is the `Batmobile_V3_Emissive` wheel **material** (`Emissive_Map` + mask), which is a texture, not a lamp — adding a lamp would be a feature, and the plan says do not. |
| brake state | taillight-brake-reverse-plan §2.1 | JC3 has **no `BRAKE` action and no `BrakeLight` behaviour**; BmAK does not change its lamp for braking either — it adds a flare (`BrakeLightsLensFlare`) and a particle trail. The two `TailLight` rows (1, 8) are the whole lamp side. |
| lamp-bound flare sprite | lens-flare-carriers §2.4 | `headlight_flare_01.effc` exists in 160 vehicle bundles, but no light member points at an effect and `.effc` carries 0 strings, so the sprite cannot be named from this module (`T-24`). |
| rear-arch lights | lens-flare-carriers §5.4 / `lit_parts_without_entry` | `sportsmuscle_wheel_r_l_arch` (46) and `_r_r_arch` (47) are lit parts with `CarLight` blocks, but BmAK has **no rear wheel socket** (no T-18 row), so no entry is written — the same pattern as 13 of the fleet's lit parts. |

## 6. Checks run (all read back from the files)

`python Tools/scripts/bm_rc4_lights.py --check` → **PASS, `CHECK_EXIT=0`**:

- the stored row plan equals a fresh re-derivation (24 rows), and the built module is
  **byte-identical** to a fresh re-encode of that plan;
- the module inside `builds/bm-RC4-lights/*.ee` equals the `aaf` copy, and the unpacked `verify/`
  copy equals both;
- `.toc` record for the module = **offset 16,499,504 / size 7,105**, equal to the `.ee` directory
  entry and to the module's byte length;
- every one of the 24 rows: `part_index` resolves in the parts module to the named part, that part
  is `has_lights = 1`, and `part_hash` / `behavior_hash` / `deformable_transform_hash` all equal
  `rbmhdr.hash_jenkins` of their strings;
- the plans' numbers re-read from the built module: **two 70° entries per headlight part**, reaches
  exactly `[18, 18, 60, 60]`, **2 `Reverse` rows both on tail strips**, **4 behaviour-`None` rows**
  (muzzle + forensics spot + two forensics heads);
- `aafdiff --hash` against `bm-RC4-parts`: **1** inner file differs — the lights module;
- `CarLight` census: 24 blocks / 8 lamp parts (§4).

Known state, recorded rather than claimed as green: `python Tools/scripts/bm_lightrig.py --check`
**fails at HEAD (8 failures)** because T-18 gained four custom rows (`T-L10`, `T-L21`..`T-L23`)
after `bm-007` was built — its plan is 22 rows, its build 18. That is the pre-existing `bm-007`
line, not this tree; this step did not modify `bm_lightrig.py`, `bm-007` or the T-18 spec.

## 7. Files changed, and how to revert

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/bm_rc4_lights.py` | new: the D-03 generator (imports `bm_lightrig`'s encoder, adds the plan overlays, the reverse pair, the build/check and the `CarLight` census) | it is the step's own generator; nothing shared was forked | delete the file |
| `Working/Lights/bm_rc4_lights.json` | new: the 24-row plan with per-member provenance, overrides, blocked list, counts and the measured census | the build's own light ledger, separate from `bm_lightrig.json` | delete the file |
| `Builds/bm-RC4-lights/` | new build tree (aaf + `.ee` + `.toc` + receipt + installer + verify) | the requested output tree | `rm -rf Builds/bm-RC4-lights` |

`Builds/bm-RC4-parts` was read only (copy source) and is unchanged; its `.ee`/`.toc` hashes in
`bm-RC4-parts/receipt.json` still verify. No `Research/`, no T-18 spec, no material and no mesh was
written.

## 8. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | whether `angle 70` / `range 60` render outside the shipped set (shipped max 50/50) | one in-game night look; both are legal floats |
| U-2 | Brightness → `multiplier` bridge (0.15 → 1.0 is the fleet mode, not a conversion) | side-by-side look |
| U-3 | whether the two-spot stack + halo reads too hot on one socket | the same look |
| U-4 | which side the renderer reads (module vs `.epe` `SVehicleLight`); the inner cone (20°) exists only on the `.epe` side and is **not** written here | `LIGHT_SYSTEM.md` §2, Q-1 probe |
| U-5 | whether the anchor chain resolves inside the non-rigged lamp parts | §112 / LGT-1 §5 probe |
| U-6 | whether reverse has any visible cue at runtime (BmAK's is audio; this is an addition) | drive test |
| U-7 | flare sprite binding | `T-24` |
