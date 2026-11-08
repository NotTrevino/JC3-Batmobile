# Dropped appearance classes D1..D6 — closest JC3 system, build recipe, proof

Card: appearance, dropped classes, part A (D1..D6). **Plan + recipe only.** No `.rbm`, texture,
build tree or ledger row was modified. Nothing was launched, installed or read from a game process.

Inputs are `Working/Appearance/progress.md` + `APPEARANCE_PLAN.md` §4 (the drop table), the BmAK
decode in `Research/BatmobileGrab/`, and five existing reports which this file **cites instead of
repeating**:

| cited report | what it already settles |
|---|---|
| `tmp/freebuff/reports/app-mud-and-dirt-default.md` | D1: BmAK mud scalars per instance, JC3 dirt members, corpus scan, `DirtColor` absent |
| `tmp/freebuff/reports/app-reflectance-f0.md` | D2: `CarPaintMM` has no F0 member, `GeneralMkIII.Reflectivity_1`, error table |
| `tmp/freebuff/reports/app-per-pixel-reflectivity.md` | D3: `s2` is per-pixel (4 levels), channel census, `GeneralMkIII.Gloss1Map`, current build defects |
| `tmp/freebuff/reports/app-anisotropic-highlights.md` | D4/D5: no aniso member in 961 headers, decoded vectors/scalars, ramp absent from the grab |
| `tmp/freebuff/reports/app-cockpit-interior-materials.md` | POL-1 interior slot/sampler state used by D3 and D6 rows |

Everything new here is: the **normalised mud bridge** (D1), the **closed-form metallic solve with
residuals** (D2), the **measured per-band vectors and the cap-vs-banding error split** (D3), the
**lobe→gloss/tint conversion** (D4), the **ramp synthesis** (D5), the **Lab colour table and the
two-tone bake** (D6), and the **per-class measurement** that proves each recipe on the built asset.

---

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: D1..D6 each with closest JC3 mechanism, numeric build recipe, evidence labels, UNKNOWN settler, built-asset measurement |
| file | `tmp/freebuff/reports/app-dropped-classes-plans-a.md` (this file) |
| why this file | the brief names it; every report of this project lives under `tmp/freebuff/reports/`, and all evidence it reads is read-only |
| reverted by | deleting this one file. No other write: `Research/`, `Tools/`, `Working/`, `Builds/` untouched; no texture baked, no `.rbm` re-encoded, no game launched |

Label legend used below: **[decoded]** = a file carries the bytes and a project tool/source string
reads them; **[derived]** = rule + stated inputs, arithmetic shown; **[UNKNOWN]** = what was tried
and the file that would settle it.

---

## 1. The six rows at a glance

| rule | class | rows | current disposition | closest JC3 mechanism (carrier) | verdict | recipe |
|---|---|---:|---|---|---|---|
| D1 | mud / wet-streak / dirt-density scalars | 41 | `drop`, "chapter-scripted, SupportDirt 0" | `CarPaintMM` dirt path: `SupportDirt` `cb2[19].y`@308, `m_DirtParams` `cb2[5]`@80, `m_DirtBlend` `cb2[6]`@96, `m_DirtColor` `cb2[7]`@112, sampler `s6` `DirtMap`, flag bit `0x4` | **closest + gap + action**: two authored block states (chapter A/B) instead of one static block | §2 |
| D2 | `Reflectivity_Multiplier` / `MaterialN_Reflectivity` | 27 | `drop`, "JC3 uses a fixed F0" | `CarPaintMM` `m_Metallic` `cb2[1]`@16 + `m_ClearCoat` `cb2[2]`@32 per channel; exact route `GeneralMkIII` `Reflectivity_1`@4 + `EnableVariableDialecticSpecFresnel`@16 | **closest + gap + action**: per-channel `m*` solve (this file), residual baked or written via `GeneralMkIII` | §3 |
| D3 | per-pixel reflectivity/roughness maps (4) | 4 | `drop`, "gloss per channel only" | `CarPaintMM` `s2` `PropertyMap` selector × `m_SpecularGloss`/`m_Metallic` float4; exact route `GeneralMkIII` `Gloss1Map` slot 1 / `Metallic1Map` slot 2 | **route**: banded `s2` + per-band vectors, error measured | §4 |
| D4 | anisotropic highlight vectors/scalars | 14 | `drop`, "no anisotropy input" | `CarPaintMM` per-channel gloss + `s1` normal streak + `s2` band selector + `s3` tint amounts | **closest + gap + action**: bake ramp into `s1`, lobes into `s2`/`s3` | §5 |
| D5 | `Aniso_ramp_Lacquered` | 1 | `drop`, "ramp has nowhere to be sampled" | same bake as D4 — the ramp is the **source curve**, not a shipped texture | **bake** (consumed, 0 new slots, 0 KB) | §6 |
| D6 | `Mud_Colour`, `Mud2_Colour`, `Damage_Dirt_Colour` | 12 | `drop`, "recorded in DirtColor, dirt disabled" | `m_DirtColor` `cb2[7]`@112 and `m_DamageColor` `cb2[17]`@272 (+ `m_Damage`@240, `m_DamageBlend`@256, `s4`/`s5`); second mud tone baked into `s0` under the `s6` G mask | **route** (first two exact, third baked) | §7 |

Row counts are `appearance_plan.json` `.components[rule]` [decoded]. All six keep their existing
`appearance_plan.py` rule id; what changes is `target`/`owner`/`note` and the build action, proposed
verbatim in §9 (not applied — `Tools/` is read-only for this card).

---

## 2. D1 — mud layer and wet streaks (41 rows)

### 2.1 What the evidence behind the drop actually says, and what it leaves open

`app-mud-and-dirt-default.md` §1–§5 already establishes: the shipped mainbody instance carries
`Mud_Opacity = 50`, `Mud2_Opacity = 2`, `Mud_Edges_Opacity = 100` [decoded `MATERIALS.md:1064`];
`DirtColor` does not exist in BmAK (`Mud_Colour`, `Mud2_Colour`, `Damage_Dirt_Colour` do) [decoded,
206 systems]; JC3's dirt is a per-block path (members above, shared `vehicle_dirt_msk.ddsc` at
`s6`), and the donor ships `SupportDirt = 0` on all 16 paint blocks [decoded corpus scan: 76/399
blocks carry `1.0`].

What that report leaves open, and this section closes:

1. it proposes the **clean** block only (four members zeroed);
2. it does not give a numeric bridge from BmAK's scalars to `m_DirtParams`/`m_DirtBlend`;
3. it does not say how a **chapter** state is published when no script may run.

### 2.2 The bridge: BmAK units → block units [derived]

BmAK's mud scalars are multipliers into a mask (report §1), so the only defensible mapping is a
normalisation by the largest authored value **of the same parameter** across the five instances +
master, which yields a 0..1 block weight. Denominators, all from the decoded table: `Mud_Opacity`
100 (body and master), `Mud2_Opacity` 2.0 (body, wheel), `Mud_Edges_Opacity` 100 (body),
`Mud_WetStreaks` 1.2 (disc). Absent = inherit master (1.0 for streaks).

| instance | `Mud_Opacity` | `Mud2_Opacity` | `Mud_Edges_Opacity` | `Mud_WetStreaks` |
|---|---:|---:|---:|---:|
| raw: mainbody | 50 | 2.0 | 100 | absent (master 1.0) |
| raw: wheel-arch | 2.0 | 0.65 | 4.0 | absent (master 1.0) |
| raw: tyre | 30 | 1.5 | 1.2 | 1.0 |
| raw: wheel | 1.0 | 2.0 | 0.5 | 1.0 |
| raw: disc-break | 0 | 1.0 | 0.2 | 1.2 |
| raw: master default | 100 | 0.65 | 0.3 | 1.0 |
| **normalised: mainbody** | **0.50** | **1.00** | **1.00** | **0.833** |
| **normalised: wheel-arch** | 0.02 | 0.325 | 0.04 | 0.833 |
| **normalised: tyre** | 0.30 | 0.75 | 0.012 | 0.833 |
| **normalised: wheel** | 0.01 | 1.00 | 0.005 | 0.833 |
| **normalised: disc-break** | 0.00 | 0.50 | 0.002 | 1.000 |
| **normalised: master** | 1.00 | 0.325 | 0.003 | 0.833 |

[derived: division of the decoded table by the per-parameter maximum; raw values decoded
`SKINS.md:208` + `MATERIALS.md:1064`, quoted in the cited report §1.]

Two BmAK scalars have no member at all: `Mud_Density` 0.11 (wheel-arch only) and `Mud_Roughness`
0.2 (tyre only) [decoded]. Their closest carrier is the `s6` mask's unused channels plus the two
free components of `m_DirtParams` — a mask-authoring job, not a scalar write (§2.5).

### 2.3 The recipe: publish the chapter as two block states, not one

No script may drive the material at runtime, so the chapter transition is carried by **two authored
block sets** in two drop entries (`VARIANTS.md` already assigns one drop entry per skin; a "worn"
entry is the same mechanism). Both are `CarPaintMM`; only the dirt members and one flag bit differ.

| member (block offset) | **clean state** (chapter 0) | **dirtied state** (chapter N) | source |
|---|---|---|---|
| `SupportDirt` `cb2[19].y` (@308) | `0.0` | `1.0` | derived (off / on) |
| `m_DirtParams` `cb2[5]` (@80) | `(0, 0, 0, 0)` | `(0, 0, 1.5, 0)` | derived: the most common shipped pair (`app-mud…` §3), strength only |
| `m_DirtBlend` `cb2[6]` (@96) | `(0, 0, 0, 0)` | `(Mud_Opacity, Mud_Edges_Opacity, Mud2_Opacity, Mud_WetStreaks)` normalised, e.g. mainbody `(0.50, 1.00, 1.00, 0.833)` | derived §2.2 |
| `m_DirtColor` `cb2[7]` (@112) | `(0.2652, 0.1433, 0.06887, 1)` | same | decoded `Mud_Colour` |
| `flags` bit `0x4` (`SUPPORT_DIRT`, `factors.py:39`) | cleared | set | decoded flag table |
| sampler `s6` `DirtMap` | shared `vehicle_dirt_msk.ddsc` | **authored** mask (R = mud coverage, G = mud2 coverage, B = edge/streak, A = density) | derived (§2.5) |

Damage layer stays off in both states (`m_Damage`/`m_DamageBlend` = 0, `SupportDmgBlend` = 0); BmAK's
mud is not damage. The order of the `m_DirtBlend` components is a **declaration**, not a decode:
the member is a `float4` whose component semantics are [UNKNOWN] (cited report, UNKNOWN 3).

### 2.4 Which build file writes it

| step | file / function | line evidence |
|---|---|---|
| member values come from the spec | `Tools/scripts/bat_assemble.py` `maker()`, `blk.static_params` / `blk.static_support` writes | `bat_assemble.py:832` (`struct.pack("<7f", …support…)`), `:836` (`blk.flags`) |
| the spec is derived from BmAK | `Tools/scripts/factors.py` `RULES` muddy branch (`^Mud\|^Damage_[Dd]irt`) + `jc3_spec()` | `factors.py:126` |
| the block codec round-trips | `Tools/scripts/rbm_geom.py` `encode_carpaintmm` | `rbm_geom.py:708` |
| the state pair | two spec files (`schema 1`) fed to `bat_assemble.py`, one per drop entry | `bat_assemble.py:61` (`load_part_spec`) |

### 2.5 The `s6` mask is authored, not inherited [derived]

`vehicle_dirt_msk.ddsc` is a shared vanilla texture; its channel layout is [UNKNOWN] and it is not
the BmAK mud mask (BmAK's mask is chapter-driven, not in the 61-texture grab). Author one BC1
`512²` mask (128 KB): `R` = mainbody mud coverage (edge-weighted, from `Mud_Edges_Opacity` 1.00 vs
`Mud_Opacity` 0.50), `G` = mud2 coverage (`Mud2_Opacity` 1.00), `B` = wet streaks (`Mud_WetStreaks`
0.833), `A` = `Mud_Density` 0.11 scaled to 8 bits = 28. Budget: 128 KB against the ≈694 KB free
reported in `app-per-pixel-reflectivity.md` §8.

### 2.6 Measurement that proves it on the built asset

1. **Member readback** — decode both block sets with `rbm_geom.decode` and print
   `(SupportDirt, m_DirtParams, m_DirtBlend, m_DirtColor, flags, s6)` per block: clean must be
   `(0, 0, 0, 0, colour, no 0x4)` and dirtied `(1, 0,0,1.5,0, §2.2 vector, colour, 0x4)`, exact
   equality (same oracle as `spec_check.py:162-173`).
2. `python Tools/scripts/spec_check.py <build_dir> <template.rbm>` → 0 mismatches, 0 silent
   template inheritances.
3. **Mask census**: mean coverage per channel of the authored `s6` (target R 0.50±0.02, G 1.00,
   B 0.83±0.02, A 28/255) and the dirt-covered area of the wheel-arch material under the dirty state
   (`R>0.5` fraction) must equal `Mud_Edges_Opacity` 1.00 within 1 %.
4. **State-pair diff** (offline, no game): the two block sets differ in exactly 4 members + 1 flag
   bit = 10 scalar words (`SupportDirt` 1, `m_DirtParams` 4, `m_DirtBlend` 4, `flags` 1);
   `m_DirtColor` is identical in both. A byte diff of the two blocks must show changes only inside
   those 10 words.

### 2.7 [UNKNOWN] and what settles it

| unknown | tried | file that settles it |
|---|---|---|
| chapter → state map (which chapter turns how much mud on) | `Mud_Opacity` is constant per instance, so the state is in the mask, not the scalar; no chapter table in the grab | BmAK cooked packages (`BmGame/CookedPCConsole`, reader `Tools/scripts/upk_read.py`), searching `MaterialInstanceConstant` swaps on `Batmobile_V3_Mainbody_NEW_MIC`; result would land in a new `Research/BatmobileGrab/MUD_STATES.md` |
| `m_DirtParams.zw`, `m_DirtBlend` component meanings | no SHEX body on disk; only layouts | decompiled `carpaintmm` DXBC (shader cache), recorded under `Research/JC3Grab/` (no such file yet) |
| whether the engine writes dirt at runtime | no project decode of the writer | JC3 executable's vehicle update path; the project file today is `Research/JC3Grab/COLOUR.md` §6 (open item) |
| `Mud_Density`, `Mud_Roughness` consumers | no member; nearest is `s6` B/A + `m_DirtParams.zw` | same DXBC decode |

---

## 3. D2 — dielectric reflectance (27 rows)

### 3.1 What is already settled

`app-reflectance-f0.md` §1–§4 establishes the member audit (`CarPaintMM` has 0 of 13 headers with a
reflectance float, `ModelSpecularColor` `[unused]`), the `GeneralMkIII` exact route, and that
6 of 20 decoded values land exactly. It does **not** give the closed-form per-channel metallic that
the build needs, nor the residual sign per row. That is §3.2.

### 3.2 The solve, per decoded value [derived]

Model (metal/dielectric split, as the report's §4):

```
F0(m, a) = F0_d · (1 − m) + a · m          m = m_Metallic channel value
m*       = clamp((F0_bmak − F0_d) / (a − F0_d), 0, 1)
F0_bmak  = F0_d · R                        R = Reflectivity_Multiplier / MaterialN_Reflectivity
```

Inputs: `F0_d = 0.04` (convention, **assumed**, the report's UNKNOWN 1), `R` decoded (§3 of the
report), `a` = albedo proxy from the same report (Body/Emissive 0.1124, Cockpit 0.04494,
Undercarriage 0.0562, Mainbody/WheelArchs 0.0258, 0.03 for untextured parts — the last is derived).

| # | material | scalar | R | F0_bmak | a | **m\*** | F0(m\*) | residual | meaning |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Body/Emissive | `Reflectivity_Multiplier` | 1.00 | 0.0400 | 0.1124 | 0.000 | 0.0400 | **0.0000** | exact |
| 2 | Cockpit | `Reflectivity_Multiplier` | 0.40 | 0.0160 | 0.04494 | 0 (was −4.86) | 0.0400 | +0.0240 | spec 2.5× too bright |
| 3 | Cockpit | `Reflectivity_BaseMaterial2_Multiplier` | 5.00 | 0.2000 | 0.04494 | 1 (was 32.4) | 0.0449 | −0.1551 | spec 4.5× too dark |
| 4 | Cockpit | `Reflectivity_Material3` | 1.00 | 0.0400 | 0.04494 | 0.000 | 0.0400 | **0.0000** | exact |
| 5 | Cockpit_Seat | `Reflectivity_Multiplier` | 1.20 | 0.0480 | 0.0300 | 0 (was −0.80) | 0.0400 | −0.0080 | 17 % too dark |
| 6 | Upgrades | `Reflectivity_Multiplier` | 1.20 | 0.0480 | 0.0300 | 0 (was −0.80) | 0.0400 | −0.0080 | 17 % too dark |
| 7 | Wheel_V2 | `Reflectivity_Multiplier` | 1.00 | 0.0400 | 0.0300 | 0.000 | 0.0400 | **0.0000** | exact |
| 8 | Discbreak | `Reflectivity_Multiplier` | 1.00 | 0.0400 | 0.0300 | 0.000 | 0.0400 | **0.0000** | exact |
| 9 | Tyre | `Reflectivity_Multiplier` | 0.20 | 0.0080 | 0.0300 | 1 (was 3.20) | 0.0300 | +0.0220 | 3.75× too bright |
| 10 | Mainbody | `Material0_Reflectivity` | 0.20 | 0.0080 | 0.0258 | 1 (was 2.25) | 0.0258 | +0.0178 | 3.2× too bright |
| 11 | Mainbody | `Material1_Reflectivity` | 0.20 | 0.0080 | 0.0258 | 1 (was 2.25) | 0.0258 | +0.0178 | 3.2× too bright |
| 12 | Mainbody | `Material2_Reflectivity` | 0.90 | 0.0360 | 0.0258 | 0.282 | 0.0360 | **0.0000** | exact |
| 13 | Mainbody | `Material3_Reflectivity` | 0.15 | 0.0060 | 0.0258 | 1 (was 2.39) | 0.0258 | +0.0198 | 4.3× too bright |
| 14 | WheelArchs | `Material0_Reflectivity` | 0.15 | 0.0060 | 0.0258 | 1 (was 2.39) | 0.0258 | +0.0198 | 4.3× too bright |
| 15 | WheelArchs | `Material1_Reflectivity` | 0.20 | 0.0080 | 0.0258 | 1 (was 2.25) | 0.0258 | +0.0178 | 3.2× too bright |
| 16 | WheelArchs | `Material2_Reflectivity` | 0.90 | 0.0360 | 0.0258 | 0.282 | 0.0360 | **0.0000** | exact |
| 17 | WheelArchs | `Material3_Reflectivity` | 0.50 | 0.0200 | 0.0258 | 1 (was 1.41) | 0.0258 | +0.0058 | 1.29× too bright |
| 18 | Undercarriage | `Material1_Reflectivity` | 0.40 | 0.0160 | 0.0562 | 0 (was −1.48) | 0.0400 | +0.0240 | spec 2.5× too bright |
| 19 | Joker hair | `Reflectivity` | 0.20 | 0.0080 | 0.0300 | 1 (was 3.20) | 0.0300 | +0.0220 | 3.75× too bright |
| 20 | Joker hair | `Reflectivity_Multiplier` | 4.00 | 0.1600 | 0.0300 | 0 (was −12.0) | 0.0400 | −0.1200 | spec 4× too dark |

[derived: the three formulas applied to the decoded `R` and the cited albedo proxies; "was" is the
unclamped solve, showing why the clamp is hit. 6/20 exact, 14/20 with |residual| 0.0058..0.1551.]

Two columns matter to the build and are new: **`m*` is per channel, not per material** (rows 10–13
and 14–17 are four different channels of one block), and the residual is **signed** — the clamp at
0 means "too bright", at 1 means "too dark". The current spec writes one flat vector per material
(`factors.json`: body `[0,0,1,0]`, cockpit `[0.9,0.9,0.9,0.9]`), which hits neither.

### 3.3 Recipe

| step | write | numbers | label |
|---|---|---|---|
| D2-A | `m_Metallic[k] = m*_k` for k=0..3, per material | §3.2 column `m*` | derived |
| D2-B | `m_SpecularGloss[k]` unchanged (gloss is lobe width, not F0) | — | decoded (member roles) |
| D2-C | `m_ClearCoat[k] = 1` only where residual < −0.10 (rows 3, 20) — the second lobe is the only energy-adding member | 2 of 20 rows | derived |
| D2-D | low-F0 classes (rows 2, 5, 6, 9–11, 13–15, 17–19) get the residual baked as an albedo darkening in the same channel: `s0' = s0 · (F0_bmak / F0(m*))` | e.g. tyre 0.030 → 0.008 = ×0.267; wheel-arch ch0 ×0.233; mainbody ch0 ×0.310 | derived |
| D2-E | exact route: swap those blocks to `GeneralMkIII`, write `Reflectivity_1 = 0.04·R` and `EnableVariableDialecticSpecFresnel = 1` | 20 writes, error 0 by construction | derived + [UNKNOWN] layout |

D2-D's cost is measured, not assumed: the darkening is a diffuse change of
ΔL* = 116·(f(Y')−f(Y)), computed per channel in §8 M2. D2-E is blocked on the `GeneralMkIII`
serialiser (`rbm_geom.py` names the hash and frames the payload, `encode_block` raises for it —
`rbm_geom.py:743`), tracked in `tmp/freebuff/reports/G3-04e.md`.

### 3.4 Measurement that proves it on the built asset

Reconstruct F0 from the built block — `F0 = 0.04(1−m) + a·m` with `m` read back from
`static_params[1]` — and compare with `0.04·R` per row. Pass: max |F0 − F0_bmak| = 0.0000 on the 6
exact rows, and every other row equals the residual in §3.2 to 1e-6. For D2-D, measure the baked
`s0` channel mean vs the target `s0·(F0_bmak/F0(m*))`: mean ratio within 1 %. For D2-E, a byte-exact
`GeneralMkIII` round trip plus a readback of `Reflectivity_1`.

---

## 4. D3 — per-pixel reflectivity / roughness (4 texture rows)

### 4.1 What is already settled, and what was missing

`app-per-pixel-reflectivity.md` §5.1 gives the banding device (bin edges 0.15/0.40/0.70, `s2` BC1
linear, per-band vectors), and §4.2 gives the current defects. It did **not** compute the per-band
vectors from the maps, so the build had no numbers to write. They are computed here.

### 4.2 Measured band tables [derived from the decoded maps]

Band edges 0.15 / 0.40 / 0.70; `gloss_k = 1 − mean(roughness in band k)`; `metallic_k = mean(B in
band k)`; fractions are texel shares. Roughness channel is the one the census shows alive (R for the
`_R` maps, G for the `_S` maps whose R is exactly 0 — `app-per-pixel…` §4). Sizes are the actual TGA
sizes (note: missile is 1024², not the 256² quoted in the cited report's budget table).

| material / map | size | rough ch | band fractions (0/1/2/3) | **gloss vector** | **metallic vector** | banding p95 |
|---|---|---|---:|---|---|---:|
| `Batmobile_V3_BRAKE_DISC_R` → `Batmobile_V3_Discbreak_MIC` | 1024×512 | R | 0.957 / 0.002 / 0.001 / 0.040 | `(1.000, 0.695, 0.353, 0.002)` | `(0.424, 0.606, 0.603, 0.601)` | 0.000 |
| `Batmobile_V3_Int_Cockpit_S` → `BatmobileV3_Cockpit_Seat` | 1024² | G | 0.004 / 0.723 / 0.252 / 0.021 | `(0.914, 0.654, 0.566, 0.161)` | `(0.153, 0.289, 0.262, 0.065)` | 0.086 |
| `Batmobile_V3_Missile_Upgrade_S` → `BatmobileV3_Upgrades_MAT_INST` | 1024² | G | 0.007 / 0.513 / 0.413 / 0.066 | `(0.922, 0.658, 0.451, 0.250)` | `(0.845, 0.310, 0.340, 0.476)` | 0.137 |
| `Nimbus_Power_Cell_S` → `Nimbus_Power_Cell_Mat` | 1024² | G | 0.005 / 0.055 / 0.629 / 0.311 | `(0.861, 0.734, 0.412, 0.224)` | `(0.0, 0.0, 0.0, 0.0)` | 0.113 |
| `Batmobile_V3_TEXTURES_Tyre_V2_R` → `Batmobile_V3_Tyre_V2_MIC` | 1024² | R | 0.052 / 0.000 / 0.000 / 0.948 | `(1.000, 0.705, 0.397, 0.000)` | `(0.732, 0.612, 0.340, 0.085)` | 0.000 |
| `Batmobile_V3_TEXTURES_Wheel_V2_R` → `BatmobileV3_Wheel_V2_MIC` | 2048² | R | 0.000 / 0.779 / 0.098 / 0.123 | `(0.883, 0.707, 0.463, 0.106)` | `(0.395, 0.341, 0.413, 0.406)` | 0.106 |

[derived: `np.digitize` at the three edges over the decoded TGA channels; p95 of
`|(1−roughness) − gloss_band|` over all texels.]

### 4.3 The new finding: the four-band limit is not the error source — the paint gloss cap is

Same maps, the vectors clamped by `VALUES.json` `paint.gloss_cap = 0.40` (whose own `source` field
says it is *"vanilla paint channel 1 of sportsmuscle_body_lod1.rbm block 6"* — a **paint** constant):

| material | bands above 0.40 | p95 error uncapped | p95 error capped |
|---|---:|---:|---:|
| disc | 0,1 | 0.000 | **0.600** |
| cockpit seat | 0,1,2 | 0.086 | 0.329 |
| missile pod | 0,1,2 | 0.137 | 0.290 |
| power cell | 0,1,2 | 0.113 | 0.251 |
| tyre | 0,1 | 0.000 | **0.600** |
| wheel | 0,1,2 | 0.106 | 0.310 |

The banding itself is accurate to p95 ≤ 0.137 gloss; applying the paint cap to a brake disc, a tyre
and a seat multiplies the error by 4–∞. The cap is therefore applied **only where BmAK's own gloss
sits at the authored paint level** (`Batmobile_V3_Mainbody_NEW_MIC`, `WheelArchs`, `Undercarriage`,
`Turret`, `Emissive`, `Cockpit_MIC` — the six whose authored gloss is 0.6 and whose cap is a paint
decision, GRB-6). The four D3 materials are not paint and carry their measured vector unchanged.

### 4.4 Recipe

| step | content | numbers |
|---|---|---|
| D3-A | band map: `s2` BC1, linear (no sRGB), bin 1→R=255, 2→G=255, 3→B=255, 0→black | edges 0.15/0.40/0.70 → 8-bit 38/102/178 |
| D3-B | `m_SpecularGloss = gloss vector` per table | 4 floats per material, 6 materials |
| D3-C | `m_Metallic = metallic vector` | same |
| D3-D | `s3` stays tint (or dummy black) — `s2` and `s3` are different textures, so tint is not disturbed | decoded `COLOUR.md` §2 |
| D3-E | downscale each band map to 512² (disc 512×256, cell 256²) — four levels have no high-frequency content | cost: disc 64 KB + cockpit 128 + missile 128 + cell 32 + tyre 128 + wheel 128 = **608 KB** of the ≈694 KB free |
| D3-F | exact route per part: `GeneralMkIII` with `Gloss1Map`=rough, `Metallic1Map`=metal | 8-bit per pixel, 2 slots, 512² = 128 KB each |

D3-E's resolution loss is bounded: at 512² on a 1024² source each band texel covers 2×2 source
texels, so a band boundary moves by ≤ 2 source texels — measured as the band-fraction delta in §8 M3.

### 4.5 Measurement

1. **Band round trip**: decode the built `s2`, histogram R/G/B/black; each must equal the source
   band fractions in §4.2 within ±1 % (3 % absolute at 512²).
2. **Gloss error**: per texel `|gloss_band − (1 − roughness_source_resampled)|`; p95 ≤ 0.15 (the
   widest bin half-width). The uncapped values above already pass; a material that fails has had the
   paint cap misapplied.
3. **Vector readback**: `m_SpecularGloss`/`m_Metallic` equal §4.2 exactly (spec_check compares to
   `factors.json`; this replaces the current `0.0/0.0` seat and the `0.9586` disc).

---

## 5. D4 — anisotropic highlights (14 rows)

### 5.1 Evidence already settled

`app-anisotropic-highlights.md` §2–§5: no aniso member in 961 headers; the effect is **two coloured
lobes** (`Fake_Aniso_1 = Material3_Anisotropic_thin`, `2 = broad`, same GUIDs), driven by a UV-space
fake; decoded colours, brightness, orientation, UV magnitude/shift; ramp texture absent from the grab.
Its build action (BAKE-ANISO-1/2) is directionally right but has no numbers. They are below.

### 5.2 The numbers the bake consumes [decoded]

| material | lobe 1 colour | lobe 2 colour | Y(lobe1) | Y(lobe2) | b1 | b2 | orient | uv mag | uv shift | channel choice |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `Batmobile_V3_Emissive` | `(0.07182, 0.07061, 0.06428)` | `(0.05607, 0.1230, 0.2762)` | 0.0704 | 0.1198 | 0.5 | 0.1 | 1 | 1 | 0 | `(0.9507, 0.9274, 1, 1)` |
| `Batmobile_V3_Cockpit_MIC` | `(0.6742, 0.6615, 0.5340)` | `(0.5385, 0.5489, 0.7921)` | 0.6550 | 0.5643 | 2.0 | 0.1 | 1 | 1 | 0 | `(0, 0, 1, 0)` |
| `Batmobile_V3_Discbreak_MIC` | — (brightness 0/0) | — | — | — | 0 | 0 | **0** | 1 | absent | — |
| `BatmobileV3_Cockpit_Seat` | inherits master | inherits master | 0.6550 | 0.5643 | 0.01 | 1.0 | 1 | 1 | 0 | — |
| `Mainbody/Turret/Undercarriage/WheelArchs` | `Material3_…_thin` `(0.1957, 0.2, 0.33)` | `…_broad` `(0.462, 0.7335, 0.9723)` | 0.2219 | 0.6744 | master default | master default | 1 | 1 | 0 | from mask |

[decoded: `SKINS.md` slots 3/5/10/11/13, `VEC_DEFAULTS.md` exports 667/676/699/709; the luminance
column is derived `Y = 0.2126R + 0.7152G + 0.0722B`.]

The cockpit's lobes are 9.3× brighter than the Emissive ones (0.655 vs 0.070) — the same bake
strength cannot serve both, which is why brightness is a per-material input, not a global constant.

### 5.3 Recipe [derived, from the decoded numbers]

| step | content | numbers |
|---|---|---|
| D4-A | `s1` normal: add a directional streak along the UV axis given by `orient` and `uv mag`, offset by `uv shift`; amplitude from `b1`,`b2` via `A_b = min(0.35, 0.10 + 0.12·b)` | cockpit lobe1 A=0.34, lobe2 A=0.112; emissive 0.16 / 0.112; seat 0.101 / 0.22 |
| D4-B | `s2` band map: lobe-1 texels → R (band 1), lobe-2 texels → G (band 2), base → black (band 0); source = `Anisotropic_Channel_Choice` mask | cockpit choice `B=1` → band 2 only; emissive `(0.95, 0.93, 1)` → near-uniform bands |
| D4-C | `m_SpecularGloss[b] = min(1, gloss_base · (1 + b_b))` — a stated multiplicative bridge, clamped at 1 | cockpit: band1 1.0, band2 0.44, base 0.40; emissive: 0.60 / 0.44 / 0.40; seat 0.404 / 0.80 |
| D4-D | lobe **hue** cannot live in gloss, so it rides `s3` tint amounts: band 1 tint `= c1/max(c1)`, band 2 `= c2/max(c2)` | cockpit band1 `(1.000, 0.981, 0.792)`, band2 `(0.680, 0.693, 1.000)` |
| D4-E | `Discbreak` gets `b1=b2=0`, `orient=0` → no streak, band 0 only: the decoded zeros are honoured, not a default | 2 of 14 rows are no-ops by authored data |
| D4-F | `m_ClearCoat` per band 0 (the lobes are a wet-lacquer look, not a coat) | 0 |

Cost: no new textures — `s1`, `s2`, `s3` already exist; the streak is a modification of the normal
map already produced by the texture stage. The view-dependent travel of a true anisotropic lobe stays
a gap (§5.5), and is not papered over.

### 5.4 Measurement

Offline, on the baked `s1`: compute the mean absolute tangent-space slope along the streak axis vs
across it, `K = mean|∂n_x/∂u| / mean|∂n_x/∂v|`. Pass: `K = 1/uv_mag` · stretch factor from the ramp,
i.e. K ≥ 1.0 for every material with `orient=1` and K ≈ 1.0 (isotropic) for the disc. Also compare
`m_SpecularGloss` band deltas to §5.3 (cockpit Δ(1→0) = 0.60; emissive 0.20; seat 0.396) and the
`s2` band fractions to the `Anisotropic_Channel_Choice` mask coverage (cockpit band2 = 1.00).

### 5.5 Gaps and settlers

| gap | closest carrier | file that settles it |
|---|---|---|
| ramp curve (streak width profile) | §6 | Arkham Engine package with `Aniso_ramp_Lacquered`; `Research/BatmobileGrab/TEXTURES.md` has 0 aniso entries, sibling `Engine.Aniso_ramp_D` decoded (`COLOUR_PARAMS.md:78`) |
| highlight does not travel with the view | no tangent-frame term in any header | decompiled `carpaintmm`/`characterhair` DXBC; `Research/JC3Grab/` currently has layout only |
| `TEXCOORD6.y` per-vertex scalar | could modulate all bands continuously | `carpaintmm.fb.txt` PS input signature names it, semantics [UNKNOWN]; the T6 probe in the cited report |

---

## 6. D5 — the anisotropic ramp texture (1 row)

`Aniso_ramp_Lacquered` is an **Engine-package reference**, not one of the 61 grabbed textures
[decoded: 0 hits in `Research/BatmobileGrab/TEXTURES.md`; reference at `COLOUR_PARAMS.md:78`]. Its
pixels, resolution, format and curve are [UNKNOWN]; JC3 ships 0 assets with "aniso" in the name
[decoded VFS index].

**Recipe.** The ramp is the *source curve* of D4-A, so it is consumed, not shipped: 0 new texture
slots, 0 KB.

| step | content | numbers |
|---|---|---|
| D5-A | until the Engine package is read, synthesise a 256×1 RGB ramp between the two decoded lobe colours with a smoothstep at u=0.5 | 256 samples; cockpit endpoint ΔY 0.0907, emissive 0.0494 |
| D5-B | stretch profile: the ramp's derivative is the lobe half-width; with `uv mag = 1` the streak covers 1 UV unit, so the ramp's 256 samples map onto 256 normal-map texels along the streak | 256 texels of a 1024² map = 25 % |
| D5-C | when the ramp lands, D5-A is replaced by a resample of the real curve — no other step changes | 1 file swap |

**Measurement.** On the baked `s1`, sample the perturbation angle along the streak parameter at 16
even stations; the sequence must be monotone from the lobe-1 angle to the lobe-2 angle, and the
standard deviation of the step must be ≤ 10 % of its mean (a piecewise-linear seam fails this).
Also assert the shipped build contains no `*aniso*` texture (count = 0).

**Settles it:** the Arkham Engine package containing `Aniso_ramp_Lacquered` (reader
`Tools/scripts/upk_read.py`, packages under `E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole`);
the result belongs in `Research/BatmobileGrab/TEXTURES.md` as a new census row.

---

## 7. D6 — mud / dirt colours (12 rows)

### 7.1 Decoded colours and their distances [decoded + derived]

| parameter | linear RGBA | Lab (D65) | where |
|---|---|---|---|
| `Mud_Colour` | `(0.2652, 0.1433, 0.06887, 1)` | (71.9, 4.6, 16.3) | `SKINS.md:208` |
| `Mud2_Colour` | `(0.1492, 0.05605, 0.01548, 1)` | (60.5, 7.5, 25.6) | `SKINS.md:208` |
| `Damage_Dirt_Colour` | `(0.41573, 0.389493, 0.33165, 1)` | (84.9, −0.2, 3.7) | `SKINS.md:208`, `COLOUR_PARAMS.md:67,152` |

ΔE76: mud↔mud2 **15.0**, mud↔damage **18.7**, mud2↔damage **33.7**
[derived: linear → sRGB → XYZ → Lab, then Euclidean]. 15.0 is above the ~2.3 just-noticeable
threshold, so the two mud tones are two visible tones and must not be collapsed.

JC3 has exactly two colour members in the paint block: `m_DirtColor` `cb2[7]`@112 and
`m_DamageColor` `cb2[17]`@272 (with `m_Damage`@240, `m_DamageBlend`@256, `SupportDmgBlend`
`cb2[18].y`@292, and the damage maps at `s4`/`s5`) [decoded `CB0_SLOTS.md` §3]. That is a 2-of-3
match: mud → `m_DirtColor`, damage-dirt → `m_DamageColor`, `Mud2_Colour` has no member.

### 7.2 Current build state (defect table)

`Working/Appearance/build_bud1/factors.json` [decoded]:

| material | `DirtColor` | `DamageColor` | correct? |
|---|---|---|---|
| Mainbody / WheelArchs / Undercarriage / Turret | `(0.265184, 0.143257, 0.0688671, 1)` | `(0.41573, 0.389493, 0.33165, 1)` | yes |
| Tyre | `(0,0,0,1)` | `(0,0,0,1)` | **no** — mud colour missing |
| Discbreak | `(0,0,0,1)` | `(0,0,0,1)` | **no** |
| Cockpit_Seat / Upgrades / cockpit | `(0,0,0,1)` | `(0,0,0,1)` | **no** |
| Wheel_V2 | `(0,0,0,1)` | `(0,0,0,1)` | **no** |

Four of the eight mud-class materials ship a black dirt colour even though the value is decoded.

### 7.3 Recipe

| step | write | numbers | label |
|---|---|---|---|
| D6-A | `m_DirtColor = Mud_Colour` on **every** block in the mud class (fix the 4 missing) | `(0.2652, 0.1433, 0.06887, 1)` | decoded |
| D6-B | `m_DamageColor = Damage_Dirt_Colour` on all 12 rows | `(0.41573, 0.389493, 0.33165, 1)` | decoded |
| D6-C | `Mud2_Colour` (ΔE 15.0 from mud) is baked into `s0` under the `s6` G mask: `s0' = s0·(1−m_G) + Mud2_Colour·m_G` | G mask = §2.5 mask, coverage from `Mud2_Opacity` (body 1.00, tyre 0.75, wheel 1.00, disc 0.50, arch 0.325) | derived |
| D6-D | damage layer stays `SupportDmgBlend = 0` with the colour inert; enabling it is D9's business, not this row | 0 | decoded |

D6-C needs no new texture: `s0` is already bound and the mask is the same `s6` authored for D1.

### 7.4 Measurement

1. Block readback: `m_DirtColor`/`m_DamageColor` equal the decoded vectors bit-exactly on all 12
   rows (`spec_check` compares to `factors.json`; a missing row fails).
2. Bake fidelity: mean Lab of the `s0` texels with `m_G > 0.5` vs `Mud2_Colour` → ΔE76 ≤ 2.0
   (the bake is a colour composite, so 2.0 is the just-noticeable bound). Untouched texels: ΔE ≤ 0.5.
3. Contrast preserved: ΔE76 between the G=1 and G=0 composites ≥ 12 of the authored 15.0.

---

## 8. The measurement set, as runnable checks

| id | proves | command (offline, no game) | pass |
|---|---|---|---|
| M0 | no silent inheritance | `python Tools/scripts/spec_check.py Working/Appearance/build_bud1 <template.rbm>` | 0 mismatches, 0 template-value leftovers |
| M1 | D1 members + state pair | `python - <<PY` decode each block, print `(support[5], static[5], static[6], static[7], flags, tex[6])` | clean/dirtied equal §2.3 exactly |
| M2 | D2 reflectance | reconstruct `F0 = 0.04(1−m)+a·m` from `static_params[1]` | 6 rows error 0.0000; others == §3.2 residual |
| M3 | D3 bands | decode `s2`, histogram channels; gloss error vs the source map at source resolution | band fractions ±1 %; p95 ≤ 0.15 |
| M4 | D4 streak | `K = mean|∂n_x/∂u| / mean|∂n_x/∂v|` on the built `s1` | K ≥ 1.0 where `orient=1`, ≈1.0 for the disc |
| M5 | D5 ramp | 16-station monotonicity of the perturbation angle | monotone, step σ ≤ 10 % of mean; 0 `*aniso*` textures shipped |
| M6 | D6 colours | Lab of the two colour members and of the baked `s0` mask regions | members exact; bake ΔE ≤ 2.0 |
| M7 | budgets | sum of texture bytes + model bytes | textures ≤ 4,648 KB, model ≤ 4,424 KB (cited report §8) |

M1–M6 all read the built `.rbm`/`.ddsc` with `rbm_geom.decode` + Pillow, so they run against the
release tree without the game. Only D4's view-dependent travel needs a rendered frame, and that is
gated on `tmp/freebuff/APPROVED_Q.txt` (STAGES.md test ban).

---

## 9. Proposed rule rewrite (not applied — `Tools/` is read-only for this card)

`Tools/scripts/appearance_plan.py` `RULES` entries keep their ids; the `target`/`owner`/`note`
strings should read:

| id | proposed `action` / `target` / `owner` |
|---|---|
| D1 | `route` / `CarPaintMM dirt path (SupportDirt @308, m_DirtParams@80, m_DirtBlend@96, m_DirtColor@112, s6 mask, flag 0x4) as two authored chapter states` / `B-03 (block values) + texture stage (s6 mask)` |
| D2 | `route` / `per-channel m_Metallic from the closed-form solve; residual baked into s0 or written via GeneralMkIII.Reflectivity_1` / `B-03 + texture stage; G3-04e for GeneralMkIII` |
| D3 | `route` / `s2 four-band selector + per-band gloss/metallic vectors (measured in app-dropped-classes-plans-a §4)` / `texture stage + B-03` |
| D4 | `bake` / `s1 directional streak + s2 lobe bands + s3 lobe tints, per-channel gloss` / `texture stage + B-03` |
| D5 | `bake` / `source curve for the s1 streak; consumed, 0 slots` / `texture stage` |
| D6 | `route` / `m_DirtColor = Mud_Colour, m_DamageColor = Damage_Dirt_Colour; Mud2_Colour baked into s0 under the s6 G mask` / `B-03 + texture stage` |

`appearance_plan.py --check` will fail until those strings and `progress.json`'s reasons are changed
together; that is the intended coupling (the tool's header says so).

---

## 10. Build order and dependencies

| order | step | depends on | produces |
|---:|---|---|---|
| 1 | D2-A/B/C per-channel metallic/coat | §3.2 table | 6 exact + 14 measured-residual blocks |
| 2 | D1 two states + `s6` mask | §2.2 table | clean + dirtied drop entries |
| 3 | D6-A/B colour fix | §7.1 | 12 correct colour members |
| 4 | D3 band maps + vectors | §4.2 | 6 banded materials, 608 KB |
| 5 | D6-C + D4-A/D | `s6`, `s1`, `s2`, `s3` | baked second mud tone, lobe streak |
| 6 | D5-A ramp synthesis | D4-A | 256×1 curve (interim) |
| 7 | D2-E exact reflectance | `GeneralMkIII` serialiser | 0-residual reflectance |

---

## 11. COMPROMISES (project rule: every one listed)

1. `F0_d = 0.04` is a convention, not a decoded constant; every D2 residual scales with it.
2. D2 albedo proxies (0.1124 / 0.04494 / 0.0562 / 0.0258 / 0.03) are derived luma values; the 0.03
   for untextured parts is a placeholder.
3. D1's `m_DirtBlend` component order is a declared bridge; the member's component semantics are
   `[UNKNOWN]`.
4. D1's chapter transition is published as two authored drop entries, because no runtime script may
   run; the chapter→state map itself is `[UNKNOWN]`.
5. D3 bin edges 0.15/0.40/0.70 are fixed (not optimised per map); the resulting p95 is measured, not
   assumed.
6. D3 band maps are downscaled to 512²/256² to fit the texture budget; boundary error ≤ 2 source
   texels.
7. D4's brightness→gloss bridge is multiplicative and clamped; it is a derivation, not a decode.
8. D4's streak does not travel with the view — the residual is named, not hidden.
9. D5's ramp is synthesised from two colours and a smoothstep until the Engine package is read.
10. D6's third colour is baked into albedo; the engine never sees `Mud2_Colour` as a dirt colour.

---

## 12. Reproduce

```bash
cd E:/Modding/JustCause3/JC3-Batmobile
python - <<'PY'
import json
p=json.load(open('Working/Appearance/appearance_plan.json'))
for r in p['components']:
    if r['rule'] in ('D1','D2','D3','D4','D5','D6'):
        print(r['rule'], r['class'], r['component'])
PY
# D3 numbers (band tables of §4.2): the np.digitize census over
# Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/*.tga, edges 0.15/0.40/0.70,
# gloss=1-mean(roughness|band), metallic=mean(B|band), p95 of |1-rough - gloss_band|.
# D2 solve (m* table of §3.2): m* = clamp(((0.04*R) - 0.04) / (a - 0.04), 0, 1).
# D6 Lab table: linear -> sRGB -> XYZ(D65) -> Lab, CIE76 distance.
python Tools/scripts/spec_check.py Working/Appearance/build_bud1 \
  Working/Serpente/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm
```

Revert: delete this file. Nothing else was written.
