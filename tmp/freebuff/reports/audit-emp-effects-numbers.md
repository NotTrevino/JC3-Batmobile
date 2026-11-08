# EMP figures in `emp-effects-closest-system-plan.md`, checked number by number against the JC3 EMP grab

**Provenance / reversibility.** New file, `tmp/freebuff/reports/audit-emp-effects-numbers.md`
= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/audit-emp-effects-numbers.md`. Intended change:
add one audit report; no source, record, package or game file is touched, and nothing was written
outside `tmp/freebuff/`. It is the correct file because it is the requested output path and the
only job artefact (`tmp/freebuff/running/L2__8812-audit-emp-effects-numbers.txt`, line 1). Revert =
delete this file.

Inputs (read-only): `tmp/freebuff/reports/emp-effects-closest-system-plan.md` (326 lines) and the
grab corpus under `Research/JC3Grab/` reached through `INDEX.jsonl`.

---

## 0. Result

- **60 figures** from the plan's four families (durations, radii/lengths, damage, counts) are listed
  below with every plan line where each appears, plus **5** more from the same plan line whose
  ranges also check (§6).
- Of the 60: **26 agree** with a line in the EMP grab, **0 disagree**, **34 are silent** and are
  marked **UNKNOWN**. Including §6, the run is **31 agree / 0 disagree / 34 unknown of 65**.
- The split is not random: **every figure the plan labels `decoded (`JC3Grab` file) is confirmed**,
  and **every figure the plan labels BmAK / `decoded (CDO export 46694)` / `PARTICLES.md` /
  `MATERIALS.md` is silent**, because the EMP grab holds no BmAK values at all (§1.3).
- One figure is not so much unconfirmed as **unrecorded**: `1,307 entity entries (3.96 GB)`
  (plan:105) has no counterpart in the grab; the only open flow that carries it is
  `tmp/freebuff/reports/immobiliser-and-emp-trigger.md:184`, not a grab file.

---

## 1. Method

### 1.1 The keyword search

Exact token `emp`, case-insensitive, boundary-delimited (`[^a-z0-9]emp[^a-z0-9]`), over the `path`
field of `Research/JC3Grab/INDEX.jsonl` (81,952 lines):

- substring `grep -i emp` → **192** lines, but almost all are `empty` / `temp` / `template`
  false positives (e.g. `ai/bts/empty_debug.btc`, `climate/zone_0/*_temp_0.ddsc`);
- token match → **52** lines. They fall into five path families:

| asset family the index names | `INDEX.jsonl` lines | grab file that holds its numbers |
|---|---|---|
| `editor/entities/jc_vehicles/.../v0505_car_solar_oldtruck_rebel_emp_01.*` and `..._rebel_emp_custom_mm250.*` (`.ee/.epe/.toc/.stringlookup`) | 37,561–37,570 | `EMP.md`, `EMP.json`, `FORCEPULSE.json`, `EMP_DISABLE.json` |
| `editor/entities/jc_weapons/02_two_handed/w702_emp/*` (`.ee/.epe/.wtunec/grip`) | 38,591–38,595 | `EMP.md` §6, `EMP.json` |
| `editor/entities/jc_weapons/05_stationary/w503_turret_emp/*` | 38,657–38,659 | `EMP.md` §6, `EMP.json` |
| `locations/region_02/missions/mm250/mm250_ss_emp.bl/.blo/.stringlookup` + its cinematics `animations/jc_cinematics/act2/mm250_ss_emp_explosion/*` | 43,927–43,931 and 15,060–15,070 | `EMP.md` §5 |
| textures `models/jc_environments/.../emp_device_01/*`, `models/jc_weapons/.../w702_fow_emp/*` | 55,305–55,318 and 60,608–60,611 | `EMP.md` §7 (paths only) |

### 1.2 What the index does **not** contain

The plan's three central data files are **absent from `INDEX.jsonl`**: `grep -c` returns **0** for
`truck_emp` (plan:101, 195), `explosion_emp` / `emp_flatbed` (plan:29, 120) and `emp_active`
(plan:30, 121). The index carries only 38 `.effc` and 2 `.ftune*` paths in total. So the index can
say *which entity owns* those files, never their contents; the numbers for them are only in
`Research/JC3Grab/EMP.md` §2/§4, which is quoted below from its own line numbers.

### 1.3 The corpus searched for each number

`Research/JC3Grab/`: `EMP.md` (225 L), `EMP.json` (743 L), `EMP_DISABLE.json` (654 L),
`FORCEPULSE.md` (293 L), `FORCEPULSE.json`, `FX.md`, `FX_VOCAB.json`, `WEAPONS.md`,
`WEAPONS_SHARED.json`, `JC3_HUD_WEAPONS.md`, `VOCABULARY.md`, `DAMAGE_MODEL.md`, `WATER.md`,
`SIGNATURE_DIFF.md`.

`EMP_DISABLE.json`'s `bmak` block holds only **member offsets and two member names** for
`RBatmobileEMP`: offsets `[360, 792, 2096, 2176, 2200, 2232, 2240, 2348, 2416, 2440, 2472, 2496]`,
names `FireParticle` / `EMPFireSwitch`. It records **no BmAK value** — `DisableEnemy`,
`PowerLevel`, `Impulse`, `CoolDown`, `7500` all return **0 hits** across the whole grab. That is
why the BmAK figures below cannot be marked agree.

### 1.4 Status words

- **AGREE** — the grab records that figure for that asset, same value.
- **DISAGREE** — the grab records a different value for the same subject.
- **SILENT → UNKNOWN** — the grab carries no record of the figure. `UNKNOWN` is written in the
  status cell, per the instruction; it does not mean the plan is wrong, only unconfirmed here.
- Plan lines are absolute (`cat -n` of the plan). Grab lines are absolute in the file named.
- Excluded from the four tables, and why: byte offsets and hashes (identifiers, not figures);
  positions/colours (`(0, 2.0356, 0.6992)`, `[0, 8, 1000]`); `3/3`, `4/4` experiment repetition
  counts; the plan's §7 pass-band tolerances are kept only as one grouped row (`D12`) because they
  are observation bands, not EMP data.

---

## 2. Table A — durations (12 figures, 1 agree / 11 silent)

| # | figure as the plan states it | plan line(s) | grab file:line | status |
|---|---|---|---|---|
| D1 | disable window **`[2, 4, 8, 12]` s**, index = power level | 28, 59, 234, 261 | — no record (`EMP.json`, `EMP_DISABLE.json` have no `DisableEnemyDuration` key or value: 0 hits) | **SILENT → UNKNOWN** |
| D2 | stage lifetimes **1.0 s** (01–03), **4.0 s** (04) | 34, 67, 132, 133, 134, 135, 221, 238, 265 | — (`FX.md` has no `Lifetime` row; no BmAK value in the grab) | **SILENT → UNKNOWN** |
| D3 | lifetime spans **0.2–1.0 s** (01–03), **0.2–4.0 s** (04) | 67 | — | **SILENT → UNKNOWN** |
| D4 | `PowerLevelChargeTime` **`[0, 0.5, 1.0, 1.5]` s** | 35, 60, 235 | — (0 hits for the member name anywhere in the grab) | **SILENT → UNKNOWN** |
| D5 | charge emitter `Lifetime` **1.5 s** (spans the top charge level) | 144, 159, 206, 235, 264 | — | **SILENT → UNKNOWN** |
| D6 | cooldown **2.0 s** (archetype `WeaponCoolDown`) | 36–37, 62, 85, 179, 188, 244 | — for the 2.0 s; the field it is written into is `fire_rate` **0.0** (`EMP.json:671`, w702) / **0.5** (`EMP.json:735`, w503) | **SILENT → UNKNOWN** |
| D7 | cooldown **10.0 s** (CDO) | 37, 62 | — | **SILENT → UNKNOWN** |
| D8 | missile lock **2.0 s** (civilian **1.0**) | 72, 248 | — | **SILENT → UNKNOWN** |
| D9 | D10 minimum visible charge **0.1 s** | 88, 264 | — (arithmetic on D4, which is silent) | **SILENT → UNKNOWN** |
| D10 | `car_common.engine_shut_down_delay_s` **30** (boats/helis/planes/bikes **5**) | 103 | `VOCABULARY.md:1390` (30), `VOCABULARY.md:1387`, `:1401`, `:1408`, `:1414` (5); `WATER.md:229` | **AGREE** |
| D11 | `EmitterTemplates[i].StartTime` **0.0 s** | 137, 221 | — | **SILENT → UNKNOWN** |
| D12 | pass bands: restart **±1 s**, audio tail **0.3 s**, missile impact **0.4 s** | 261, 268, 270 | — (no probe band in any grab file) | **SILENT → UNKNOWN** |

---

## 3. Table B — radii and lengths (13 figures, 4 agree / 9 silent)

| # | figure as the plan states it | plan line(s) | grab file:line | status |
|---|---|---|---|---|
| R1 | `w702_emp` range **50 m** | 22, 100 | `EMP.md:170` (`500 / 50 m`); `EMP.json:673` (`"max_range": 50.0`) | **AGREE** |
| R2 | `w503_turret_emp` range **750 m** | 23, 100 | `EMP.md:170` (`500 / 750 m`); `EMP.json:737` (`"max_range": 750.0`) | **AGREE** |
| R3 | `truck_emp` `PlayerDamageRadius` **25 m** (and `AIDamageRadius` 25) | 101 | `EMP.md:40`, `EMP.md:44`; `FORCEPULSE.md:141` (`100 / 25`) | **AGREE** |
| R4 | radius factors `…RadiusMin` **1**, `…RadiusPercentageMax` **1** | 101, 196 | `EMP.md:41`, `:42`, `:45`, `:46` | **AGREE** |
| R5 | BmAK `Range` **7500.0 UU** | 35, 58 | — (0 hits for `7500` in the grab) | **SILENT → UNKNOWN** |
| R6 | derived **75 m** (7500 UU ÷ 100) | 79, 236, 261 | — (divides a silent figure) | **SILENT → UNKNOWN** |
| R7 | ring mesh **250 cm** = **2.5 m** | 33, 67, 138, 265 | — | **SILENT → UNKNOWN** |
| R8 | scale-over-life **20×** → **50 m** (D2) | 33, 39, 67, 80, 138, 237, 265 | — | **SILENT → UNKNOWN** |
| R9 | ratio **0.667** (50 / 75, D3) | 39, 81 | — | **SILENT → UNKNOWN** |
| R10 | alternate **30×** → **75 m** (D4) | 39, 82, 138, 237 | — | **SILENT → UNKNOWN** |
| R11 | missile explosion `[450,10,25]` cm = **4.5 m** (D9) | 87, 249, 265 | — | **SILENT → UNKNOWN** |
| R12 | arc radii A **1.0** / B **1.5** (`INST_New_Electric_Arc_BLUE_THIN`) | 36, 69, 141, 241 | — (material instance, BmAK) | **SILENT → UNKNOWN** |
| R13 | stage sizes **0.4 … 250 cm**; stage-04 **250×30×30 cm** | 67 | — | **SILENT → UNKNOWN** |

---

## 4. Table C — damage values (13 figures, 8 agree / 5 silent)

| # | figure as the plan states it | plan line(s) | grab file:line | status |
|---|---|---|---|---|
| V1 | `w702_emp` damage **500** | 22, 100, 179, 243 | `EMP.md:170`; `EMP.json:670` (`"damage": 500.0`) | **AGREE** |
| V2 | `w503_turret_emp` damage **500** | 23, 100 | `EMP.md:170`; `EMP.json:734` (`"damage": 500.0`) | **AGREE** |
| V3 | `truck_emp` `PlayerDamage` **100** | 101, 195, 242 | `EMP.md:39`; `FORCEPULSE.md:141` | **AGREE** |
| V4 | `truck_emp` `AIDamage` **100** / `AIDamageRadius` **25** (the `AIDamage*` four "the same") | 101, 196 | `EMP.md:43`, `:44`, `:45`, `:46` | **AGREE** |
| V5 | BmAK missile `Damage` **60** | 72, 247 | — | **SILENT → UNKNOWN** |
| V6 | BmAK missile `DamageRadius` **0** | 72, 247 | — | **SILENT → UNKNOWN** |
| V7 | `EMPImpulse` **5000.0** / `EMPVehicleImpulse` **20000.0** | 61, 245 | — for the values. (`FORCEPULSE.md:125–141` confirms the tune is eight `ForcePulseSettings` numbers — 4 player + 4 AI — with no impulse among them, which supports the plan's U-8 but not the figure) | **SILENT → UNKNOWN** |
| V8 | medium-tank armour triple `bullet` **5000@99** / `explosion` **250@50** / `electricity` **−1@100** | 282 | `DAMAGE_MODEL.md:40`, `:42`, `:46` | **AGREE** |
| V9 | `electricity_armor` **−1..0**, `electricity_armor_strength` **0..100** (build at −1 @ 100) | 104 | `VOCABULARY.md:1464`, `:1465`; `DAMAGE_MODEL.md:46` | **AGREE** |
| V10 | `engine_max_damage_torque` **0.25–0.75** (fleet, **n=145**) | 102 | `VOCABULARY.md:831` (`0.25 .. 0.75 (med 0.75, n=145)`) | **AGREE** |
| V11 | `damage_from_parts[].damage_ratio_from_broken_off` **1** | 102 | `VOCABULARY.md:1391` (`1 .. 1 (med 1, n=3016)`) | **AGREE** |
| V12 | **0** of **1,515** weapon-tune member rows name a damage channel | 104 | `DAMAGE_MODEL.md:20` ("across the 9 weapon tunes decoded here (1,515 member rows) 0 member names mention heavy/armour/penetration") | **AGREE** |
| V13 | `EMP_Emissive_Multiplier` **350** (Batmobile) / **650** (Joker) | 70, 208 | — | **SILENT → UNKNOWN** |

---

## 5. Table D — counts (22 figures, 13 agree / 9 silent)

| # | figure as the plan states it | plan line(s) | grab file:line | status |
|---|---|---|---|---|
| C1 | **4 stages** in the BmAK burst | 33 | — | **SILENT → UNKNOWN** |
| C2 | emitters **10 / 10 / 10 / 13** (stages 01–04) | 67, 132–135 | — | **SILENT → UNKNOWN** |
| C3 | stage-04 rate **0–1500/s** | 67 | — | **SILENT → UNKNOWN** |
| C4 | stage-04 `MaxParticles` cap **6000** (D5) | 83, 136, 221, 239 | — (arithmetic on C3 × D2, both silent) | **SILENT → UNKNOWN** |
| C5 | charge system **4** light emitters | 68 | — | **SILENT → UNKNOWN** |
| C6 | `FireParticle` / `EMPFireSwitch` **4 items each** | 64, 160, 162, 250 | — for the count. The grab names both members and records their offsets (2440 / 2472; names at `EMP_DISABLE.json:22`, `:23`), but no item count | **SILENT → UNKNOWN** |
| C7 | missile explosion **14** emitters (`Batmobil_Rocket_Explosion`) / **9** (`_Small`) | 72 | — | **SILENT → UNKNOWN** |
| C8 | **307** pulses in the fleet (flags "unique among 307") | 101 | `FORCEPULSE.md:4` ("307 pulses in 232 vehicle `.ee` files"); `FORCEPULSE.md:34`, `:49`, `:50` give the three flags 2 distinct values each over 307 | **AGREE** |
| C9 | flag triple `4912FC04`=**0** / `AE6F7EFF`=**1** / `CF4F7880`=**1** | 101, 197 | `EMP.md:60`, `:61`, `:62` | **AGREE** |
| C10 | `is_disabled_by_emp` **0** asset bindings (literal and Jenkins hash) | 24, 105, 281 | `EMP_DISABLE.json:193` (`"is_disabled_by_emp": 0` hash), `:199` (literal 0) | **AGREE** |
| C11 | **1,941** entries, **3.98 GB** | 105 | `EMP_DISABLE.json:170` (`"entries": 1941`), `:168` (`"bytes": 3978089026` = 3.978 GB) | **AGREE** |
| C12 | **1,307** entity entries, **3.96 GB** (second pass) | 105 | — no such pass in any grab file (`grep -rn 1307` over `Research/JC3Grab` finds no count; `EMP_DISABLE.json` records one pass only) | **SILENT → UNKNOWN** |
| C13 | control hits `invulnerable` **289** / `is_in_water` **160** | 105 | `EMP_DISABLE.json:192`, `:194` | **AGREE** |
| C14 | **0** of **88** vehicle weapon components is a `CEMPWeapon` | 280 | `EMP.json:4` (`"cemp": 0`), `:5` (`"components": 88`); `EMP.md:223` | **AGREE** |
| C15 | `explosion_emp_flatbed.effc` **24,015 B** | 29, 120 | `EMP.md:100`; `EMP.json:45` (`"size": 24015`) | **AGREE** |
| C16 | `emp_active.effc` **8,783 B** | 30, 121 | `EMP.md:104`; `EMP.json:348` (`"size": 8783`) | **AGREE** |
| C17 | `.effc` vocabulary **94** member paths | 122 | `FX.md:62` ("Top 25 of 94 member paths") | **AGREE** |
| C18 | `emp_flatbed_table` payload **72 objects** | 150, 285 | — (`EMP.json:63`, `:354` name the table; no object/entry count anywhere) | **SILENT → UNKNOWN** |
| C19 | **30-byte** opaque entry | 150, 285 | `SIGNATURE_DIFF.md:546` ("`CMaterialEffectTable` is an opaque 30-byte hash blob") — class-level, same class | **AGREE** |
| C20 | icon ids **206**, **601–622**, **614 missing** | 26, 185 | `JC3_HUD_WEAPONS.md:161` (the 22-id list), `:162` ("**without an icon: 614**") | **AGREE** |
| C21 | `AutoAim` **22 members**, **0 durations** | 288 | `WEAPONS.md:304` and `:407` (22 members x 6 contexts; the member table `:302–333` has no duration row; `grep Duration WEAPONS_SHARED.json` = 0) | **AGREE** |
| C22 | **0** smoke / **0** flame / **0** debris emitters per burst (P-V3) | 266 | — (a claim about the build that will be made, not about data in the grab) | **SILENT → UNKNOWN** |

---

## 6. The same line's other figures (checked, outside the four families)

`plan:122` also states three `.effc` member ranges and a parameter range; all four agree:

| figure | plan line | grab file:line | status |
|---|---|---|---|
| `Timelines[].EndX[]` **0..1** | 122 | `FX.md:41` | **AGREE** |
| `Timelines[].StartX[]` **0..0.997** | 122 | `FX.md:42` (`0 .. 0.996999`) | **AGREE** |
| `Timelines[].XScaleRecip[]` **0..337** | 122 | `FX.md:43` (`0 .. 337.132`) | **AGREE** |
| `Params[]` **−10000..100000** | 122 | `FX.md:45` | **AGREE** |
| `emp_active` emitter hash **−1458959942**, `enabled` **0**, position **(−0.011, 2.448, 0.07)** | 121 | `EMP.md:132`, `:133` (member named at `EMP.md:127`) | **AGREE** |

---

## 7. Build writes: the plan's value vs the shipped value in the grab

These are not claims about the game — the plan says it will set them. Listed so a reader can see
each write against the grab, and because two of them (D6, R-write) are the only places a reader
could think the grab disagrees.

| plan write | plan line | shipped value in the grab | relation |
|---|---|---|---|
| `bm_emp_weapon.wtunec` `damage` **500** | 179 | `500.0` (`EMP.json:670`) | same as shipped |
| `bm_emp_weapon.wtunec` `max_range` **75** | 179, 243 | `50.0` (`EMP.json:673`, w702) | **differs by design** (D1); the plan states both numbers itself (22 vs 243) |
| `bm_emp_weapon.wtunec` `fire_rate` **2.0** | 179, 188 | `0.0` (w702, `EMP.json:671`) / `0.5` (w503, `EMP.json:735`) | **differs**; the grab also never states whether `fire_rate` is seconds-per-shot or shots-per-second, so the 2.0's unit is not checkable here |
| `weapon_type` **6**, class `CEMPWeapon` | 183 | `6` (`EMP.md:165`, `EMP.json:595`) | same as shipped |
| `weapon_id` into **601–622** (702 has no icon) | 26, 185 | `702` (`EMP.md:165`); icon set `JC3_HUD_WEAPONS.md:161–162` | **differs by design**, icon list confirmed |
| `bm_emp_pulse.ftune` `PlayerDamage` **100** | 195 | `100` (`EMP.md:39`) | same as shipped |
| `bm_emp_pulse.ftune` `PlayerDamageRadius` / `AIDamageRadius` **75** | 195–196, 222 | `25` (`EMP.md:40`, `:44`) | **differs by design** (D1) |
| `…RadiusMin` **1**, `…RadiusPercentageMax` **1** | 196 | `1` / `1` (`EMP.md:41`, `:42`) | same as shipped |
| `bm_emp_burst.effc` `Lifetime` **1.0 / 4.0**, `MaxParticles` **6000**, `StartTime` **0.0** | 132–137, 221 | no shipped value in the grab (BmAK; `FX.md` has no `Lifetime` row) | uncomparable — UNKNOWN |

---

## 8. Figures whose supporting offset the grab does not record

The plan cites a member offset for almost every BmAK figure. `EMP_DISABLE.json` records the
`RBatmobileEMP` / `Batmobile_EMP_Burst` offset set as
`[360, 792, 2096, 2176, 2200, 2232, 2240, 2348, 2416, 2440, 2472, 2496]`:

| plan offset | plan line | in the grab's offset set? |
|---|---|---|
| `WeaponCoolDown` @**2096** | 62 | yes |
| `FireStartEvent` @**2176**, `IndividualFireEvent` @**2200** | 66 | yes |
| `ChargeParticle` @**2416**, `FireParticle` @**2440**, `EMPFireSwitch` @**2472**, `ImpulseComponent` @**2496** | 63, 64, 65, 283 | yes |
| `Range` @**2396**, `DisableEnemyDuration` @**2400**, `PowerLevelChargeTime` @**2424**, `EMPImpulse` @**2512**, `EMPVehicleImpulse` @**2528** | 58, 59, 60, 61 | **no** |

Consequence: the five figures tied to those five offsets (D1, D4, R5, V7) cannot be confirmed even
as *members* from the grab, only from the plan's own BmAK export. (For orientation only, and
outside the searched corpus: `Research/BatmobileGrab/BMSDK_OFFSETS.json:14197–14286` carries the
names and offsets 2400 / 2424 / 2512 / 2528 — names and offsets, not the values.)

---

## 9. Tally and limits

| family | figures | AGREE | DISAGREE | SILENT → UNKNOWN |
|---|---:|---:|---:|---:|
| A durations | 12 | 1 | 0 | 11 |
| B radii / lengths | 13 | 4 | 0 | 9 |
| C damage | 13 | 8 | 0 | 5 |
| D counts | 22 | 13 | 0 | 9 |
| §6 extra figures | 5 | 5 | 0 | 0 |
| **total** | **65** | **31** | **0** | **34** |

Limits.

1. **Silence is a property of the corpus, not of the plan.** 34 figures are UNKNOWN *here* because
   the EMP index resolves only to JC3 assets and the grab holds no BmAK values (`EMP_DISABLE.json`
   keeps offsets, not values). Those figures are labelled in the plan as `decoded (CDO export
   46694)`, `PARTICLES.md` or `MATERIALS.md` — i.e. `Research/BatmobileGrab`, which this audit was
   not asked to search and did not search for values.
2. **No DISAGREE was found and none is claimed**; one near-miss is recorded honestly in §7
   (`max_range` 75 vs 50, `fire_rate` 2.0 vs 0.0/0.5), which are stated writes, not data claims.
3. `C12` (1,307 entries / 3.96 GB) is the one figure whose apparent source is a *report* rather than
   a grab: `tmp/freebuff/reports/immobiliser-and-emp-trigger.md:184`. It is marked UNKNOWN because
   no grab file records that pass, not because it is doubted.
4. `C19` is a class-level agreement: `SIGNATURE_DIFF.md:546` describes `CMaterialEffectTable` as a
   30-byte hash blob for the class, not for `emp_flatbed_table` specifically.
5. Nothing was written, installed, launched or re-decoded for this audit; every number above is a
   grep of a file at the line named. Files, line counts and `INDEX.jsonl` offsets are as of this
   run.
