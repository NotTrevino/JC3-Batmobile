# Adversarial review — the numbers in `keep-audit-*.md`

**Scope.** The eight `keep`-audit reports in `tmp/freebuff/reports/`. Six numeric claims per report
were chosen for **build impact** (they move a module member, a hull set, a bank or a material, or they
are the number a verdict rests on), traced to the file/offset/row the report cites, and re-derived
here from bytes, JSON or the project's own tool. 48 claims in total.

**Result: 42 reproduced, 5 not reproduced, 1 source missing.** Five reports carry a claim that does
not survive its own source; one claim has no producer file to check against. Corrected statements are
in §10 and the per-report tables.

**Method.** Read-only. Every number below comes from the same sources the report cites, decoded by
`tmp/freebuff/scratch/verify_keep_audit3.py`, `verify_ka3b.py`, `verify_ka3c.py`, `verify_ka3d.py`
(logs `vka1.log`, `vka3c.log`, `vka3d.log`). No report, ledger row, module, build or game state was
modified; no game process was started. Commands are in §12.

**Change statement (AGENTS.md).**

| item | value |
|---|---|
| intended change | add one audit report; no other file touched |
| file | `tmp/freebuff/reports/review-keep-audit-numbers.md` (this file) |
| why this file | the brief names it; it is the only output of this pass |
| reverted by | deleting this file. The eight audited reports keep their pre-audit mtimes (05:27–06:45) and no ledger row was written by this pass; `GRAB_BACKLOG.md` (09:19) and `STATUS.md` (09:20) were touched by the background driver, not by this audit |

---

## 1. Scoreboard

| # | report | 6 claims | repro | not | missing |
|---:|---|---:|---:|---:|---:|
| 1 | `keep-audit-dimensions-wheels.md` | 6 | 6 | 0 | 0 |
| 2 | `keep-audit-suspension-and-mass.md` | 6 | 4 | **2** | 0 |
| 3 | `keep-audit-engine-boost-aero.md` | 6 | 5 | **1** | 0 |
| 4 | `keep-audit-damage-collision.md` | 6 | 6 | 0 | 0 |
| 5 | `keep-audit-audio-fx.md` | 6 | 5 | 0 | **1** |
| 6 | `keep-audit-lights.md` | 6 | 5 | **1** | 0 |
| 7 | `keep-audit-materials-textures.md` | 6 | 6 | 0 | 0 |
| 8 | `keep-audit-steering-and-drift.md` | 6 | 5 | **1** | 0 |
| | **total** | **48** | **42** | **5** | **1** |

The five failures are not bookkeeping slips: two are members the BmAK dump does not contain, one is a
terminal speed 54 km/h off, one is a channel census that undercounts its own entries by 3, and one puts
a proposed value outside the fleet domain it claims to be inside.

---

## 2. `keep-audit-dimensions-wheels.md` — 6/6

Source of the built numbers: `Builds/bm-RC2/…/modules/default/batmobile/
v0300_car_kensington_sportsmuscle_land_global.vmodc` (1,600 B, sha256 `f9a1455f…`), read at the
`offset-in-file` of `Working/Stance/land_global_check.xml`.

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | `ground_clearance` = **0.703700** @ `0x0070` | `land_global.vmodc` + `land_global_check.xml` | **0.703700** at `0x0070` | **reproduced** |
| 2 | front `radius`/`width` **0.682750 / 0.731950** @ `0x0074`/`0x007c`; rear **0.682650 / 0.731650** @ `0x0094`/`0x009c` | same | 0.68275 / 0.73195 / 0.68265 / 0.73165 | **reproduced** |
| 3 | four hubs (−1.2080/0.7047/−2.5700), (+1.2080/0.7047/−2.5699), (+1.2845/0.7027/+2.4589), (−1.2845/0.7027/+2.4589) | `TYRES.md` §1 + `stations.json` | bytes `0xe0–0x10c` carry exactly those triples in **(x,y,z)** order; `stations.json` matches all 12 components | **reproduced** (citation defect, below) |
| 4 | wheelbase **5.0289**, tracks **2.4160 / 2.5690** | arithmetic | 2.5700+2.4589 = 5.0289; 2×1.208 = 2.416; 2×1.2845 = 2.569 | **reproduced** |
| 5 | front Ø **1.3655** vs mesh mean **1.36545**; rear Ø **1.3653** vs **1.36530** | `TYRES.md` §1 tread values 1.3652/1.3657/1.3654/1.3652 | 2×0.682750 = 1.3655; mean(1.3652,1.3657) = 1.36545; 2×0.682650 = 1.3653; mean = 1.3653 | **reproduced** |
| 6 | `SVehicleWheel.WheelRadius` **64.0 cm** @ `CHAIN.json` offset **568**, all four wheels; 0.683−0.640 = **4.27 cm** inside the tyre | `CHAIN.json` | 16 `WheelRadius` records, every one offset 568 / value 64.0 (4 wheels × 4 packages); 0.68275−0.640 = **0.04275 m** | **reproduced** |

**Citation defect (does not change a number).** The hub table is attributed to `TYRES.md` §1, but
`TYRES.md` contains no hub coordinates at all — its §1 is tyre/rim/width only, and there is no
`1.2080` or `1.2845` anywhere in the file. The numbers are real and do reproduce, from the second
source the report also names (`Working/TrueScale/stations.json`) and from the built bytes. The
`TYRES.md` half of the citation is wrong.

---

## 3. `keep-audit-suspension-and-mass.md` — 4/6

Built modules: `Builds/bm-RC2/…/rigid_body|suspension|land_global.vmodc` at the
`Working/Movement/live/*.xml` offsets. The XML exposes **one** instance with the front block at
`0x50…` and the rear at `0x90…` (duplicate member names, read in document order).

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | `center_of_mass_bias` **−0.3**, `mass` **6000**, inertia **4.0/2.6/1.2**, driver 0, calc 0 | built `rigid_body.vmodc` | −0.3 / 6000.0 / 4.0 / 2.6 / 1.2 / 0.0 / 0.0 | **reproduced** |
| 2 | antiroll **0/0**, lateral offset **0.2/0.2**, strength/length/compression/relaxation **45 / 0.7 / 3 / 5** on both axles | built `suspension.vmodc` | front @`0x50/0x64/0x68/0x70/0x78`: 0.0, 3.0, 0.7, 5.0, 45.0, 0.2 — rear @`0x90…0xb8`: identical | **reproduced** |
| 3 | wheel mass **75 front / 150 rear** | `land_global.*_wheels.mass` | 75.0 @`0x0084`, 150.0 @`0x00a4` | **reproduced** |
| 4 | wheel-mass CoM shift **(75 × 5.0289)/6000 = +0.063 m rearward** | arithmetic | the product is 0.0629, but the model is wrong: *versus a symmetric pair* the rear axle gains **150 kg** at 2.4589 m, not 75 kg at 5.0289 m → **150 × 2.4589/(6000+450) = 0.0572 m**. 0.063 reproduces only by halving the mass and doubling the lever | **not reproduced** |
| 5 | **three** drag members on `RVehicleSimBatmobile`: `Drag` 16, `DragNoLoad` 20, `DriftDrag` 712 | `BMSDK_OFFSETS.json` | the class has **one** drag member — `DriftDrag` @ **712**. `Drag` and `DragNoLoad` do not exist **anywhere** in the 41-class dump (`SVehicleSimCar` 12 props, `SVehicleSimBase` 21, `SVehicleSimBatmobile` 0 — none drag-named); `RVehicleSimBatmobile`'s property list starts at offset **456** | **not reproduced** |
| 6 | `use_shape_cast` 0 both axles; `raycast_offset` **0 on all 167 vehicles** | built module + `VOCABULARY.md` | 0/0 in the bytes; `VOCABULARY.md` row `front.raycast_offset` = **0 … 0, med 0, n=167**, donor 0 | **reproduced** |

---

## 4. `keep-audit-engine-boost-aero.md` — 5/6

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | torque **1393.524536**, rpm **800 / 2800 / 4500**, factors **1.0 / 0.65** | built `land_engine.vmodc` | 1393.524536 / 800 / 2800 / 4500 / 1.0 / 0.65 | **reproduced** |
| 2 | `frontal_area` **6.634667**, `Cd` **0.55**, `top_speed_drag_coefficient` **2.0**, lift **−0.3**, rho **1.3** | built `land_aerodynamics.vmodc` | 6.634667 / 0.55 / 2.0 / −0.3 / 1.3 (working XML still reads Cd **0.139340296**, i.e. the T-A2 edit is in the bytes only) | **reproduced** |
| 3 | three arcade boost blocks: nitro 2.0/1.0/15000/0.2/**43.2**; heat 2.0/**4.26**/0/0/**100.92**; upgraded 2.0/4.26/20000/0.2/100.92 | built `custom_land_global.vmodc` | all three groups present in order, values as tabled (torque, grip, push, blend, extra) | **reproduced** |
| 4 | peak power **572 hp**, **47.7 %** of 1200; P@2800 = 408.6 kW = **548 hp** | arithmetic on #1 | 408.6 kW / 547.9 hp and 426.8 kW / 572.4 hp; 572.4/1200 = **0.477** | **reproduced** |
| 5 | `Cd·A` = **3.649**, terminal speed **56.5 m/s = 203 km/h** | arithmetic | 0.55×6.634667 = 3.6491; v = (2×426,808/(1.3×3.6491))^(1/3) = **56.46 m/s = 203.2 km/h** | **reproduced** |
| 6 | "at the old Cd the same power gives **267 km/h**", so Cd 0.139→0.55 "cost **17 %** of terminal speed" | arithmetic | at Cd **0.139340296**: Cd·A 0.9242, v = **89.2 m/s = 321.2 km/h**; the cost is **36.7 %**, not 17 %. 267 km/h needs Cd ≈ 0.242 at this power and area | **not reproduced** |

---

## 5. `keep-audit-damage-collision.md` — 6/6

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | thresholds **4000 / 4000 / 1050 / 250**, `bullet_heavy_armor` **5 @ 20**, `deform_scale` **0**, `impact_damage_factor` **0**, `max_health` **36000** | `damage_audit.py` module read; `bm_health.json` | audit table: 4000, 4000, **1050**, **250**, 5@20, 0, 0, 36000 | **reproduced** (see note) |
| 2 | bm-009 audit **exit 0**; bm-RC2 **exit 1** with `FAIL max_health = 36000 … not declared in damage_switches.json` | `damage_audit.py` | bm-009 exit 0; bm-RC2 exit 1 with exactly that FAIL line; 36000 also reported `OUT OF DOMAIN` in the member table | **reproduced** |
| 3 | wreck asset **32 bodies**, 128 records, largest box **317.942 × 64.552 × 97.966 cm**, "all four vehicles byte-identical" | `PHYSICS.md` / `PHYSICS.json` | 32 bodies in each of the 4 packages; `317.942` present; the only field that differs between packages is the export **`index`** (32 diffs) — geometry is identical, the records are not literally byte-identical | **reproduced** (with that caveat) |
| 4 | drivable asset **3 boxes** (690.305 × 374.536 × 207.5; 679.585 × 345.688 × 103.5; 166.177 × 189.365 × 39.8) + **43 + 13 = 56** convex elements | `COLLISION_GEOM.md/.json`, `COLLISION_CONVEX.md` | all nine extents present in `COLLISION_GEOM.json`; 43 + 13 = 56 | **reproduced** |
| 5 | `Pawn.Health` **1200** on the 3 archetypes; cannon `Damage` **50** → **24 hits** | `DAMAGE_RULES.md`, `T10_DAMAGE.md` | 1200 / 50 = **24**; the 1200 and the 50 rows are in `DAMAGE_RULES.md` | **reproduced** |
| 6 | bm-RC2 `sportsmuscle.physicsc` **902,384 B** sha `eda17906…`; bm-009 **340,368 B** sha `1b90daef…` | files on disk | 902,384 B / `eda17906…`; 340,368 B / `1b90daef…` | **reproduced** |

**Note on #1.** `Working/Damage/bm_health.json` holds only four changed rows (`max_health` 2000→36000,
`explosion_threshold` 4000→4000, `deform_scale` 0, `impact_damage_factor` 0) plus two `skew_health`
rows. The 1050 / 250 / 5@20 numbers exist only in the module and therefore only in the
`damage_audit.py` table — the report's citation to `bm_health.json` covers 4 of the 8 values.

---

## 6. `keep-audit-audio-fx.md` — 5/6, 1 source missing

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | 361 rows / 118 event ids / 447 media / 508 entries, 18,176,431 B / 27 banks, 34,409,121 B | `AUDIO_MAP.json` `summary` | every field identical | **reproduced** |
| 2 | bucket split **27 lore-exact / 124 approximate / 181 missing / 29 dialogue** | the report's own §1 rule | no bucket field exists in `AUDIO_MAP.json` (`events[]` keys: name, bank, status, media, targets, …). `status` counts are **239 resolved / 8 no-media / 90 missing-bank / 24 streamed** — a different partition. No producer file stores 27/124/181/29 | **source missing** |
| 3 | 90 missing-bank rows over 26 ids and **10** banks (the ten named) | `AUDIO_MAP.json` | `missing_rows` 90, `missing_ids` 26, `missing_banks` length 10, names as listed | **reproduced** |
| 4 | FX_TABLE **57,187 rows / 1,533 paths / 955 EffectRT / 338 under `/jc_vehicles/`**; `roof` **5**, `window` **12**, `electric` **42** | `FX_TABLE.jsonl` | 57,187 / 1,533 / 955 / 338; keyword census glass 14, window 12, light 28, taillight 1, headlight 7, electric 42, burn 17, fire 57, smoke 29, roof 5, spread 12, engine 45 | **reproduced** |
| 5 | 45 pinned GUIDs split **vehicles 24 / character 2 / effects 19**; vehicles bank **257** events | `JC3_AUDIO.md` | `257` present; `vehicles/24` and `effects/19` present; 24+2+19 = 45. The `character 2` token is not verbatim in the file (implied by the total) | **reproduced** (with that caveat) |
| 6 | `LandAudio` has exactly **2** members: `min_rpm` **1000.0**, `max_rpm` **10000.0** | `JC3_AUDIO.md` §4 | table rows read 1000.0 and 10000.0 | **reproduced** |

The report's separate T-FX5 "74 holds / 23 **UNKNOWN**" is correctly labelled UNKNOWN and was not
scored as a claim.

---

## 7. `keep-audit-lights.md` — 5/6

Built rows from `Builds/bm-007/…/modules/generated/…_lights.vmodc` (5,745 B) via
`bm_lightrig.decode_module()`, which returns **18** rows.

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | **28** BmAK entries per rig, **101** over 4 rigs | `LIGHTS.json` | 28 / 28 / 17 / 28 = 101 | **reproduced** |
| 2 | headlight `Radius` **6000**, cone **20/70**, `Brightness` **0.15** | `LIGHTS.json` entry 0 | Radius 6000.0, Inner 20.0, Outer 70.0, Brightness 0.15000000596 | **reproduced** |
| 3 | **15** entries author `LightColor`, `Brightness`, `Radius`; **8** author `InnerConeAngle` | `LIGHTS.json` | **18** author colour, **18** brightness, **18** radius, **10** inner cone (**16** outer, **18** falloff). Component classes: 15 `SpotLight`, 2 `PointLight`, 1 `RHelicopterSpotLight`, 10 `LensFlare` | **not reproduced** |
| 4 | **18** rows built (21 − 10 + 7) | built module | `decode_module()` → 18 | **reproduced** |
| 5 | 4 rows at `range 30 / angle 40`, 1 at `10 / 60`, 13 at `2 / 10`; `blinking` on rows **3, 5, 7, 9** | built module | exactly `{(2,10):13, (30,40):4, (10,60):1}`; `blinking` true at indices **3, 5, 7, 9** | **reproduced** |
| 6 | fleet multiplier census `1×2188, 2×792, 0.5×174, 0.7×30, 3×12, 5×12, 0.3×6, 0.4×3` = **3,217** | `LIGHT_SYSTEM.md` | same eight counts; sum **3,217** | **reproduced** |

The 13-colour-exact / 5-approximate / 10-absent split is a matching exercise against the 18 rows, not
a stored number; it was not scored. The channel census in #3 is the one that breaks: the report
undercounts colour, brightness and radius by 3 each and the inner cone by 2, because it appears to
have counted the 15 spot entries and ignored the 2 point + 1 helicopter lamps that also author colour.

---

## 8. `keep-audit-materials-textures.md` — 6/6

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | body LODs **17 blocks (16 `CarPaintMM` + 1 `Window`)**, wheels **5 (4+1)**; whole car **185 + 25 = 210**, not 235 | `Working/Appearance/build/*.rbm` via `rbm_geom` | 5 body RBMs each `{CarPaintMM:16, Window:1}`; 20 wheel RBMs each `{CarPaintMM:4, Window:1}`; totals **185 `CarPaintMM` + 25 `Window` = 210** | **reproduced** |
| 2 | body `s0` is a **solid colour 0.4784/0.4588/0.4941**; no `NEW_Batmobile_V2_BODY_D` in the grab; largest shipped map **1024²**; **21** Batmobile `.ddsc` | `factors.json`, grab, `.ddsc` headers | s0 `[0.47843137, 0.45882353, 0.49411765, 1.0]`; no BODY_D in the grab dir; 21 unique `.ddsc`, max 1024×1024 | **reproduced** |
| 3 | base ×2.2 = **0.0567/0.0516/0.06**; ×3.4476 = **0.1946/0.1779/0.2086**; **3.44×** | `VALUES.json` + arithmetic | 0.02579×2.2 = 0.056738; ×3.4476 = 0.19561 → per channel 0.1946/0.1779/0.2086; ratio **3.432** (the 3.4476 is the gain factor) | **reproduced** |
| 4 | authored gloss **0.600**, build **0.45 in every paint block**, ratio **0.75**; palette **8×0.45 + 2×0.0** | RBMs, `factors.json`, palette | RBMs: `0.45` ×30 in `body_lod1`, ×5 in a wheel LOD, **250** across all RBMs, `0.4` only ×2; palette 8×`0.449999988` + 2×`0.0`; 0.45/0.6 = 0.75. `factors.json` still holds **0.4** for the paint materials — the 0.45 is written by the palette/writer step, not by the plan | **reproduced** (see note) |
| 5 | glass **1.2 / 0.8 / 1.1 / 0.2**; derived `SpecFresnel` **0.452**, `SpecGloss` **0.9186** | `MATERIALS.md:1062` | four archetype rows read `Glass_Opacity=1.2000, Glass_Reflectivity=0.8000, Glass_Roughness=1.1000, glass_smudges=0.2000`; 0.565×0.8 = 0.452; 1−0.074×1.1 = 0.9186 | **reproduced** |
| 6 | **24** bound BmAK TGAs, **21** shipped `.ddsc`, **9** solid slots, **32** dummy `s2`/`s3` | `factors.json`, build dir | 24 distinct `tga` sources, 21 unique `.ddsc`, 9 solid slots, 32 `s2`/`s3` on `a00_dummy_black_mpm` | **reproduced** |

**Note on #4.** The number is right where the report says it is (the written RBMs and the palette), and
`0.4` is present only twice in one body LOD, so the "0.4 cap" story is indeed dead. But "0.45 in every
paint block" is not visible in `factors.json`, which still carries `0.4` for `Mainbody`, `Turret`,
`WheelArchs`, `Undercarriage_NEW`, `Emissive` and `Cockpit` — a reader checking the plan rather than the
RBM would conclude the opposite.

---

## 9. `keep-audit-steering-and-drift.md` — 5/6

Built cells cited from `Builds/test-091/…/modules/default/*.vmodc` (not from `bm-RC2`).

| # | claim | cited source | re-derived | status |
|---:|---|---|---|---|
| 1 | `land_steering` carries `0.8×1, 0.6×1, 3.0×3, 0.3×1`, **no** 1.2, no 0.85 | `Builds/test-091` bytes | 1,073 B: 0.8 ×1, 0.6 ×1, 3.0 ×3, 0.3 ×1, 1.2 ×0, 0.85 ×0 | **reproduced** |
| 2 | `brakes` carries `1.0×4`, **`5.0×0`**, `2.0×3` → `min_time_to_block` is **1**, the ledger's 5 is stale | `Builds/test-091` bytes | 548 B: 1.0 ×4, 5.0 ×0, 2.0 ×3 | **reproduced** |
| 3 | `EBrakeBrakeForce` **640,000** vs class default **160,000** → ratio **4.0** | `MECHANICS_NAMES.md:32`, `CLASS_DEFAULTS.md:184` | 640000 (instance, `RVehicleBatmobileBase` +0x1214) and 160000.0 (class default @4628); 640000/160000 = 4.0 | **reproduced** |
| 4 | `HandbrakeOnSpeed` **10,000 cm/s = 360 km/h**, `HandbrakeOffSpeed` **1 cm/s ≈ 0.036 km/h** | `MECHANICS_NAMES.md:67-68` | 10000 @ +0x164, 1 @ +0x168; ×0.036 → 360.0 and 0.036 km/h | **reproduced** |
| 5 | rear `LatSlipFactor` **1.6** → **1/1.6 = 0.625**, and 0.625 "lands inside the shipped land band **0.3 … 0.8, n=19, median 0.5**" | `COLLISION_WHERE.md:110-113`; fleet band | 1.6 confirmed on WheelRL/RR, 1/1.6 = 0.625; handbrake 1.5 FL/FR and 1.1 RL/RR; 1.1/1.5 = 0.733 ✓. **But `VOCABULARY.md` gives `wheel_drift_aligning_strength` 0 … 0.5, median 0.5, n=252, donor 0.3** — 0.625 is **outside** the fleet domain, not inside it | **not reproduced** |
| 6 | lock **60°** at a flat **720 °/s** → **0.0833 s**; build 0.8 s = **75 °/s**, **9.6×** slower | `T1_TRANSLATION.md` §6 | 60/720 = 0.08333; 60/0.8 = 75 °/s; 0.8/0.08333 = 9.6 | **reproduced** |

The drift-block census in the report's §9 also reproduces exactly: `45×3, 20×2, 10×2, 4.0×1, 0.02×2,
0.03×1, 30000×1` in the `test-091` `custom_land_global.vmodc`.

---

## 10. Corrected statements

Each line replaces the failing cell; the source is the column above. Nothing in the reports was edited.

**`keep-audit-suspension-and-mass.md`**

- **T-M3 wheel-mass lever (claim 4):** "the asymmetric wheel masses move the CoM **+0.057 m**
  rearward (150 kg × 2.4589 m ÷ 6,450 kg versus a symmetric 75/75 pair)". The printed
  `75 × 5.0289 / 6000 = 0.063` halves the added mass and doubles the lever; it is not the shift
  "versus a symmetric pair". The lever is still the ledger's only un-named CoM knob, just 10 % weaker
  than claimed.
- **T-R2 drag members (claim 5):** "the dump contains **one** drag member on the simulated model —
  `RVehicleSimBatmobile.DriftDrag` @ **712**, value not decoded. `Drag` and `DragNoLoad` are not
  members of any of the 41 classes, at 16/20 or anywhere else." The row's real defect stands (BmAK
  does have drag state that JC3's single multiplier cannot carry), but the evidence is one member,
  not three, and the offsets 16/20 are not in the dump.

**`keep-audit-engine-boost-aero.md`**

- **T-E5/T-A3 terminal-speed cross-check (claim 6):** "at the pre-edit `Cd 0.139340296` the same
  power gives **321 km/h**, so raising Cd to 0.55 cost **36.7 %** of terminal speed, not 17 %.
  A 267 km/h figure corresponds to `Cd ≈ 0.242`, which no version of this module carries." The
  203 km/h figure itself reproduces.

**`keep-audit-lights.md`**

- **§4 channel accounting (claim 3):** "**18** of the 28 entries author `LightColor`, `Brightness`
  and `Radius` (15 spot + 2 point + 1 helicopter spot), **10** author `InnerConeAngle`, 16 author
  `OuterConeAngle`, 18 author `FalloffExponent`." The table's 15/15/15/8 omits the two brake point
  lamps and the forensics helicopter spot, which is why its "0 of 15 carried" percentages are
  computed on the wrong denominator. The verdict (0 brightness / 0 cone / 0 radius carried, 13
  colours exact) is unaffected: the carried count is still 0.

**`keep-audit-steering-and-drift.md`**

- **T-ST6 in-band argument (claim 5):** "0.625 is the reciprocal of the rear slip gain, but it is
  **above the fleet maximum** for `wheel_drift_aligning_strength` (0 … 0.5, med 0.5, n=252; donor
  0.3) — it is an R3 value, not a band pick. The band 0.3 … 0.8 / n=19 is not what `VOCABULARY.md`
  reports." The reciprocal bridge and the falsifier test (T-C) are unaffected; only the claim that
  the proposal is inside the shipped domain fails, and a 0.625 build would be a deliberate
  out-of-domain choice that the row must declare as R3.

**`keep-audit-audio-fx.md`** (source missing, not wrong)

- **§2 bucket split:** the totals 27/124/181/29 cannot be checked against any producer: `AUDIO_MAP.json`
  stores no bucket, and its `status` field partitions the same 361 rows as 239/8/90/24. Either the
  classifier script that produced 27/124/181/29 is added to the repo, or the table should state that
  the split is a reading of the §1 rule made in that report and is not a stored artefact. The
  row counts beneath it (361 / 332 vehicle / 29 dialogue) do add up.

---

## 11. Additional defects found outside the six-claim sample

1. **`dimensions-wheels`:** the hub table's `TYRES.md` §1 citation does not exist in that file (§2).
2. **`damage-collision`:** neither the 42-part (bm-009) nor the 61-part (RC2) count is a field in
   either `receipt.json` — `bm-009` contains no `61`, `bm-RC2` contains no `42`, and the hull bounds
   `3.499 / 2.283 / 7.037` are in neither receipt. The report's §4.1/§4.3 argument is sound, but its
   part-count evidence is not in the file it names; `Working/Damage/sportsmuscle_parts_v077.xml`
   exposes only 1 instance, so the count cannot be read from there either.
3. **`damage-collision` "byte-identical":** `PHYSICS.json`'s four packages differ in the `index`
   field of all 32 bodies. Say "geometry-identical", not "byte-identical".
4. **`materials-textures`:** `factors.json` (the plan) and the written RBM disagree on gloss
   (0.4 vs 0.45) for six paint materials. Any future read-back of T-MA4 must say **which** artefact it
   reads; today the row's own two citations point at opposite values.
5. **`audio-fx`:** the 45-GUID split is only checkable as `vehicles/24` + `effects/19` + the implied 2;
   a `character/2` token does not appear in `JC3_AUDIO.md`, so a future edit could change it silently.
6. **`steering-and-drift`:** the fleet domains quoted in T-ST2/T-ST3 come from a doc that
   `VOCABULARY.md` contradicts on the steering ladder as well (`max_speed_t_to_full_steer_s` −1 … 5,
   med −1, n=252) — the "IQR −1 … 0.8, n=125" in the report is not the row that file carries.

## 12. Limits of this review

- **Static only.** No module was re-written, no build re-run, no game launched. Every "carries" claim
  above is a decode of an existing `.vmodc`/`.rbm`/`.json`, not a runtime measurement, and none of the
  audited reports' in-game falsifiers were executed (test ban: `tmp/freebuff/APPROVED_Q.txt` absent).
- **Six claims per report is a sample**, chosen for build impact. A report can pass all six and still
  contain a wrong seventh — that is exactly what the `lights` channel census shows.
- **Where a claim is about a fleet statistic** (n=167, n=252), the check is that the cited row says the
  number; the underlying fleet sweep was not re-run.
- **`keep-audit-damage-collision` part counts and `keep-audit-materials-textures` slot→mesh map** remain
  unverified for the reasons in §11.2 and the reports' own UNKNOWNs.
- **Classification judgements** (lore-exact / compromise) were not re-litigated; only the numbers
  behind them.

## 13. Reproduce

```bash
cd "E:/Modding/JustCause3/JC3-Batmobile"
python tmp/freebuff/scratch/verify_keep_audit3.py   # A/B/C + first pass at D..G
python tmp/freebuff/scratch/verify_ka3b.py          # corrected shapes: hardpoints, boost blocks, audit table
python tmp/freebuff/scratch/verify_ka3c.py          # audio/fx, lights, materials, thresholds
python tmp/freebuff/scratch/verify_ka3d.py          # light rows, RBM gloss, glass, dummies
python Tools/scripts/damage_audit.py --build Builds/bm-RC2/aaf   # exit 1 (max_health 36000)
python Tools/scripts/damage_audit.py --build Builds/bm-009/aaf   # exit 0
```

All five scripts are read-only and write only their own log under `tmp/freebuff/scratch/`.
