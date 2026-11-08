# Apply: interior, glass, wheels, mud and skins folded into the appearance plan

STATUS: done. Five carrier reviews are now sections 7–11 of `Working/Appearance/APPEARANCE_PLAN.md`,
one section per surface, every row a BmAK number against the JC3 member that carries it (or the
stated reason none does). `Working/Appearance/progress.md` carries the same five reviews as
`## surfaces` subsections, generated from one table. T-21's completion note is section 0 of the
plan.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add a five-surface carrier table (`CROSS`) to the plan generator, render it as plan sections 7–11, emit the same entries as `## surfaces` in the progress table, and add a T-21 completion note (section 0) with the carried / unresolved counts |
| files changed | `Tools/scripts/appearance_plan.py`, `Tools/scripts/appearance_progress.py`, and the two generated outputs `Working/Appearance/APPEARANCE_PLAN.md`, `Working/Appearance/appearance_plan.json`, `Working/Appearance/progress.md`, `Working/Appearance/progress.json`, plus this report |
| why these files | `APPEARANCE_PLAN.md` and `progress.md` are generated; hand-editing them is reverted by the next `--write`. `appearance_plan.py` is the plan's only author and `appearance_progress.py` the progress table's only author, so the sections had to go into the generators to survive regeneration |
| how to revert | restore the two scripts from git (`git checkout -- Tools/scripts/appearance_plan.py Tools/scripts/appearance_progress.py`) and re-run `python Tools/scripts/appearance_plan.py --write` and `python Tools/scripts/appearance_progress.py`; delete this report. No ledger row, build file, texture or `.rbm` was touched |

No BmAK number below is new: each was decoded in the report named in the row and is copied from
it, not re-derived.

## 1. T-21 completion note — the numbers

`appearance_progress.py` (regenerated 2026-11-06, build `Working\Appearance\build`):

```
components 339 | transferred 167 | partial 36 | excluded 136 | missing 0
planned 172: bake 23 route 61 drop 88 | POL-1 24 POL-2 23 | unclassified 0
overall 54.6% | strict 49.3% | of everything JC3 has a slot for 91.1%
```

* **Faithfully carried by plan: 251 of 339 (74.0%)** = 167 already in the build + 23 bake rows (a
  sampler the block already has) + 61 route rows (a named carrier the build already writes).
* **Unresolved: 88 of 339 (26.0%)**, every one with a stated reason (section 4 of the plan lists
  them by rule). Of the 61 routed rows, 36 are `partial` — carrier named, a per-pixel part of the
  value lost — so counting only what is closed today (167 + 23 bake, which still needs the pipeline
  run) gives 190 of 339 (56.0%).
* **0 unclassified**, so the card's Done criterion is met.

Unresolved, by rule (counts from the same run):

| rule | rows | why it stays unresolved |
|---|---:|---|
| D1 | 41 | JC3 dirt is dynamic per object; BmAK mud is chapter-scripted — the scalars are written as a clean/dirty pair instead (plan section 10) |
| D6 | 12 | JC3 dirt colour is recorded in `m_DirtColor` with dirt disabled; nothing else to carry |
| D7 | 8 | rain direction / rain size are scene inputs in JC3, not material inputs |
| D9 | 4 | story-chapter damage masks; JC3 damage is hit-driven (`SupportDmgBlend` 0) |
| D10 | 3 | colour ramp lookups; no ramp sampler, and the ramp files are missing on disk |
| D11 | 9 | editor/fake helpers and smudge overlays — UE scaffolding, not a rendered input |
| D12 | 1 | editor helper (`Batmobile_V3_Emissive:vec:Art`) |
| D13 | 8 | tessellated displacement; the JC3 body is a fixed LOD mesh (R1: no deformation) |
| D14 | 2 | story EMP visuals (tyre EMP 0.0 / 350) |
| **sum** | **88** | matches `drop 88` in the run above |

(Copied from the generated plan section 4 table, not hand-counted.)

## 2. The five sections, what each adds and what stays open

### 2.1 Interior and cockpit (POL-1) — plan section 7

Carried in full: `Int_Cockpit_D/N` (4096×4096 DXT1) on `s0`/`s1`, `Int_Cockpit_M` on `s3`
TintMap, Metalicity 0.9000 → `m_Metallic` `cb2[1]`, ClearCoat [1,1,1,1] → `m_ClearCoat` `cb2[2]`.
Narrowed: `EmissiveMultiply` 15.0 × 1024² mask → `m_Emissive` `cb2[3]` + `SupportSoftTint`
`cb2[19].z`; `Int_Cockpit_S` (R channel dead) → `m_SpecularGloss` `cb2[0].x` mean.
Not carried (11 of 15 components): the two `Colour_Ramp_Map` lookups (64×512; the lacquered one is
missing on disk), `Aniso_ramp_Lacquered` (no anisotropy member in the 961 headers), the centre
screen (BmAK ships no texture — 0.3188 × 0.1512 m must be authored), and the yoke (absent in BmAK;
4 faces in the hand box — author as `VehicleParts` with `damage_type = Land_Steering_Wheel`).

### 2.2 Glass and canopy — plan section 8

`Batmobile_Glass`'s 8 inputs are unconnected in all four packages, so the master carries nothing.
Tint [0.02579, 0.02579, 0.03] has no vector → bake into `t0` RGB with `TintPower` at 1.
`Glass_Opacity` 1.2 → `t0` alpha (`V3_Glass_A` repack); `Glass_Reflectivity` 0.8 →
`SpecGloss`/`SpecFresnel` `cb1[0]` (split UNKNOWN); `Glass_Roughness` 1.1 → `DiffuseRougness`
`cb1[8]` (bridge underived); `V3_Glass_S` per-pixel → `t3` channels (map undecoded);
`glass_smudges` 0.2 and the unbound `V2_GLASS_MASK` have no member. 9 of 13 rows are not faithful.
Cracking is the one place JC3 has more: `t4`/`t5` plus `WindowContactPoints[32]` — nothing to carry.

### 2.3 Wheels and tyres — plan section 9

Geometry is exact: tyre 1.3652–1.3657 m OD and 0.7314–0.7325 m wide → `radius` 0.68275 / 0.68265,
`width` 0.73195 / 0.73165, ≤ 0.55 mm per corner, spin axis `+x`. Albedo and normal are shipped for
wheel, tyre and disc. Lost: `Wheel_V2_R`, `Tyre_V2_R`, `BRAKE_DISC_R` are read but never shipped —
only the scalars remain (`m_SpecularGloss` 0.6088 / 0.052 / 0.9586, `m_Metallic` 0.3561 / 0.431).
7 of 14 components carry a value no member reproduces; `Discbreak_front/back` needs a block split,
the 4 split flares are contradictory between `lights_manifest.json` and `COMPROMISES_T.md`, the
tyre EMP is dropped (D14), and `rim_radius` 0.539 vs 1.0254 m (`Fan`) is a 26 mm decision.

### 2.4 Mud and dirt default (D1) — plan section 10

The D1 premise is corrected: BmAK's clean state is **not** zero scalars — the mainbody instance
carries `Mud_Opacity` 50, `Mud2_Opacity` 2, `Mud_Edges_Opacity` 100 (master 100 / 0.65 / 0.3), and
`DirtColor` does not exist in BmAK at all (0 hits over 206 systems; the real names are `Mud_Colour`,
`Mud2_Colour`, `Damage_Dirt_Colour`). `Mud_Colour` [0.2652, 0.1433, 0.06887] equals JC3's own
`m_DirtColor` (0.2652, 0.1433, 0.0689). The build must write the clean state explicitly —
`SupportDirt` `cb2[19].y` 0.0, `m_DirtParams` `cb2[5]` (0,0,0,0), `m_DirtBlend` `cb2[6]` (0,0,0,0),
`m_DirtColor` `cb2[7]` (0.2652, 0.1433, 0.0689, 1) — because the donor `sportsmuscle_body_lod1`
ships 0.0 on all 16 `CarPaintMM` blocks, i.e. the car is clean by omission today. Four scalars
(`Mud_WetStreaks`, `Mud_Roughness`, `Mud_Density`, `Mud_Reflectivity`) have no member; the closest
carrier is the shared `s6 vehicle_dirt_msk.ddsc`, which needs an authored mask.

### 2.5 Skins and variants (D-5) — plan section 11

11 looks exist (4 vehicles + 3 damage states + 4 upgrade visuals); 1 is carried (V2). V2→Joker
differs by 61 materials, 54 textures and 40 bones, so skins cannot be palette tints — each is a
drop entry with its own `.rbm` and blocks (Joker 26 materials / 31 textures on a 78 / 92 baseline).
Upgrade visuals are half-carried (`Missile_Upgrade_D/N`, `Power_Cell_INT_D`, `Nimbus_Power_Cell_N`,
`Stagg_Battery_01_D/N` ship; every `_S` was dropped by D3 and no `_GLOW` shipped). Damage states
have no material route — `mshswap` is the mechanism. One useful exemption: `SimulationModel` is
byte-identical across the four packages (2,328 B, 37 tags, 0 differing) and weapons differ in 0
fields, so a skin costs meshes, materials and textures only. Per-skin texture budget against the
R9 wall (7,065 KB per entity) is still UNMEASURED.

Also recorded from that report: `Working/Appearance/VARIANTS.md` does not exist — the dataset the
plan already reads is `Research/BatmobileGrab/VARIANTS.md`, so section 6's source line is correct
and no path was changed.

## 3. How the sections are maintained

`CROSS` in `Tools/scripts/appearance_plan.py` is the single table: `appearance_plan.py` renders it
as sections 7–11 (title, source, verdict, and a BmAK input / value / JC3 member / gap table), and
`appearance_progress.py` imports it and prints the same five entries as `###` subsections under
`## surfaces` in `progress.md`. Editing one entry updates both documents on the next `--write`, so
the two cannot disagree about a surface.

## 4. Checks run (verbatim results)

```
python Tools/scripts/appearance_plan.py --write
  components 339 | transferred 167 | partial 36 | excluded 136 | missing 0
  planned 172: bake 23 route 61 drop 88 | POL-1 24 POL-2 23 | unclassified 0
  md -> Working/Appearance/APPEARANCE_PLAN.md
  json -> Working/Appearance/appearance_plan.json
  exit 0
python Tools/scripts/appearance_plan.py --check      -> "check ok"        exit 0
python Tools/scripts/appearance_progress.py          -> 339 / 167 ok, 54.6% exit 0
python Tools/scripts/appearance_plan.py --check      -> "check ok"        exit 0  (after progress)
python Tools/scripts/t_blocked.py --check
  PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope; 0 attempts,
  all evidence markers present; ledger sha256 unchanged                        exit 0
python Tools/scripts/t_rows.py check
  ledger 199 rows | ... blocked 11 out 1 superseded 7 | edits 35 over 16 rows
  check ok                                                                     exit 0
python Tools/scripts/status_audit.py --check         -> "STATUS.md is current" exit 0
```

**Pin upkeep:** none required. The change adds no ledger row and no blocked row, so `WAITS` and the
`in_scope ==` value in `Tools/scripts/t_blocked.py` are untouched; the check above re-derives 216 in
scope / 15 blocked exactly as before, and `t_blocked.py` was not edited (no backup needed).

Generated headings, verified after the write:

```
21: ## 0. T-21 completion note      343: ## 7. Interior and cockpit (POL-1)
47: ## 1. The actions               362: ## 8. Glass and canopy
55: ## 2. POL-2 - the micro-detail  381: ## 9. Wheels and tyres
89: ## 3. Routed carriers           397: ## 10. Mud and dirt default (D1)
155: ## 4. Dropped, with the reason 412: ## 11. Skins and variants (D-5)
264: ## 5. POL-1 - interior         427: ## 12. Every planned component
318: ## 6. Skins (D-5)              604: ## 13. UNKNOWNs and limits
                                    624: ## 14. Reproduce and revert
```

## 5. Limits (unchanged by this pass)

* The 23 bake rows remain `excluded`: the bake is planned, not run — `appearance_pipeline.py` has
  no bake step yet. A plan row is not a shipped value.
* The `Window` block's numeric members are still undecoded (MODLOG §102d), so the glass scalars
  stay vanilla until that decode lands; section 8 says so per row.
* Sections 7–11 quote decoded numbers; they do not re-derive them. If a source report is revised,
  the `CROSS` row is the one place to update, then `--write` + `--check`.
