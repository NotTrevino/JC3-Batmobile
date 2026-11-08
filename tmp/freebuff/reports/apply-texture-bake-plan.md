# Merging the four texture plans into one build order

Four reports each planned a slice of the textures the build still drops or bakes. This report merges
them into **one ordered list**, states where each row's meaning lands, and records the rows that have
**no faithful route**. Nothing was baked, no `.ddsc` was written, no build or game touched.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one generated plan (md + json), one generator, and this report; refresh `progress.json`/`progress.md` and the plan page |
| files | `Working/Appearance/TEXTURE_BUILD_PLAN.md`, `Working/Appearance/TEXTURE_BUILD_PLAN.json`, `Tools/scripts/texture_build_plan.py`, `Working/Appearance/progress.{json,md}`, `Working/Appearance/appearance_plan.json`, `Working/Appearance/APPEARANCE_PLAN.md`, this report |
| why these files | the brief names `Working/Appearance` for the plan; `progress.*` and `appearance_plan.json` are generated from the build and the rule table, so they had to be re-run for the plan annotation to be current |
| reverted by | deleting the three new files and re-running `appearance_progress.py` + `appearance_plan.py --write`. No `Research/`, `Builds/`, `Tools/scripts/appearance_progress.py`, ledger or `t_blocked.py` edit |

## 1. The merged order (23 rows, 7 stages)

| stage | what | rows |
|---:|---|---:|
| 1 | albedo and normal already shipped (reference rows, no action) | 2 |
| 2 | **mask packing** — BmAK's separate masks into one `s2`/`s3` RGBA (`D3`) | 4 |
| 3 | **micro-detail bake into `s1`** — `P1`/POL-2, reoriented normal mapping | 6 |
| 4 | **emissive** — `CarLight s5` where a lamp block exists, else the `m_Emissive` bands (`R2`) | 2 |
| 5 | glass — the `Window` material tint (`R4`) | 1 |
| 6 | **colour ramps** — blocked on pixels that are not on disk (`D10`), or folded into the bake (`D5`) | 4 |
| 7 | **chapter damage masks** — no faithful route: one static state exists, four chapters do not (`D9`) | 4 |

Order is dependency order, not preference: the mask pack comes before the bake because the bake's
per-channel weight **is** the mask channel; the bake comes before the emissive atlas because both
write the same texture budget; the ramps and the chapter masks come last because they are blocked.

Per-row destinations, transforms and checks are in `TEXTURE_BUILD_PLAN.md` (§1, one table per stage)
and `TEXTURE_BUILD_PLAN.json` (`rows[]` with `stage`, `rule`, `dest`, `ch`, `xform`, `check`,
`faithful`, `status`). The page and the json are both produced by
`Tools/scripts/texture_build_plan.py --write`; `--check` re-derives them byte for byte and passes.

The three "destinations" the four reports agree on:

| meaning | destination | source report |
|---|---|---|
| per-pixel material properties | `CarPaintMM s2 PropertyMap`, four bands, one channel per material | `app-texture-binding-audit.md` §6; `app-per-pixel-reflectivity.md` §5.1 |
| tiling micro-detail | baked into `s1 NormalMap` (RNM), weight per mask channel | `app-microdetail-bake-plan.md` §4 |
| per-pixel emissive | `CarLight s5 EmissiveMap` **only**; `CarPaintMM` has a constant `m_Emissive` | `app-emissive-mask-channel.md` §2.3, §5.1-5.2 |

## 2. The rows with no faithful route (12 of 23) — flagged, not hidden

| texture | why there is no faithful route | what would open it |
|---|---|---|
| `Batmobile_Micropattern_A` | the pixels are **not in the 115-file grab** (the body family binds it) | re-grab those `Texture2D` objects |
| `Batmobile_Micropattern_A_Normal` | same | same |
| `Batmobile_Micropattern_B` | same (`Batmobile_V3_Emissive` binds it) | same |
| `Batmobile_Micropattern_C` | same (cockpit + emissive) | same |
| `Batmobile_V3_Wheel_E` | named by `SLOTS.json` slot 5, **no `*_Wheel_E.tga` on disk**; the four arch lamp strips therefore stay dark (`static.Emissive = [0,0,0,0]`) | a grab of the master that owns slot 5's `Emissive_Map` |
| `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | the **name is indexed** (`COCKPIT.md:31`, `COLOUR_PARAMS.md:79`) but **no texture file exists** in the grab; JC3 also has no ramp sampler | a grab of the ramp texture; then `s3 TintMap` as a 2-D approximation |
| `Batman_BM3_V2_Leather_Ramp` | same (name indexed at `COCKPIT.md:33`, texture record `#5399`, no file) | same |
| `Batmobile_V3_Body_ColourRamp` | same (`SLOTS.md:30`) | same |
| `Batmobile_V3_TEXTURES_Body_Damage_ChapterMask` | the mask exists and *can* drive one static pre-damaged look (`SupportDmgBlend` 1 + non-zero `m_Damage`), but JC3 has **one** `s5` slot and **no chapter state** (0 in every file) | four entity/material variants — a build decision, not a texture |
| `Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask` | same | same |
| `Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask` | same | same |
| `Batmobile_V3_Undercarriage_Damage_ChapterMask` | same | same |

Four more rows are **partial** rather than unfaithful, and the plan says so per row: the four
per-pixel property masks (`BRAKE_DISC_R`, `Int_Cockpit_S`, `Missile_Upgrade_S`,
`Nimbus_Power_Cell_S`) become four bands instead of 8 bits; `Aniso_ramp_Lacquered` is a UV-space fake
folded into the bake; `Batmobile_V3_Glass_S` is a material tint only.

## 3. Progress, recomputed — and why the percentages do not move

`python Tools/scripts/appearance_progress.py` (writes `progress.json` + `progress.md`):

| class | total | transferred | partial | missing | excluded | % |
|---|---:|---:|---:|---:|---:|---:|
| geometry | 25 | 25 | 0 | 0 | 0 | 100.0 |
| materials | 19 | 19 | 0 | 0 | 0 | 100.0 |
| **textures** | **38** | **17** | **7** | **0** | **14** | **53.9** |
| factors | 257 | 106 | 29 | 0 | 122 | 46.9 |
| **overall** | **339** | **167** | **36** | **0** | **136** | **54.6** |

strict (transferred only) **49.3 %**; of everything JC3 has a slot for **91.1 %**. The plan tally on
the same run: **bake 23, route 61, drop 88, unclassified 0** (`appearance_plan.py --check`:
*md match True, json match True*).

**This is the honest part of the answer: the percentages did not move, and they should not.**
`appearance_progress.py` computes `(transferred + 0.5 x partial) / total` from what the **build**
contains — a `.ddsc` at the expected path, a block of the spec's type in the parts, a factor's
disposition. A plan action is an annotation written beside that number by `attach_plan()`; it is not
an input to `summarise()`. Reclassifying a row from `drop` to `route` therefore cannot raise the
percentage — only a converted, registered texture can. The plan page's numbers that *did* change are
the plan tallies (`route 61`, `drop 88`, up from the pre-merge split), and the `unclassified` count
stayed at 0, which is the gate that matters.

## 4. What moved in the rule table, and what did not

Read-only for this task: `Tools/scripts/appearance_plan.py` was **not** edited here. Its rules
already express the four reports:

| rule | action | rows in this plan | verdict |
|---|---|---|---|
| `P1` | bake | 6 | matches `app-microdetail-bake-plan.md` — bake into `s1`, five tiles absent |
| `P2` | bake | (factors) | the `MicroDetail_size` values, consumed at bake time |
| `P3` | bake | (factors) | the roughness coupling, folded as a mean |
| `R2` | route | 2 | matches `app-emissive-mask-channel.md` — `CarLight s5`, else bands |
| `R4` | route | 1 | glass tint |
| `D3` | route | 4 | four bands on `s2` |
| `D5` | route | 1 | anisotropy folded into the bake |
| `D9` | drop | 4 | **stays drop**: one static state, no chapter selector — the report's "closest system + gap" |
| `D10` | drop | 3 | **stays drop**: the ramp pixels are absent, so the ramp rows stay open and say so |

So no row changed disposition in this pass, which is why the plan tallies are stable at
`bake 23 / route 61 / drop 88`; the merge added the **order, the destination and the check** per
texture, which is what the build briefs consume.

## 5. Gates run

| gate | result |
|---|---|
| `appearance_progress.py` (writes progress.json + md) | exit 0; overall 54.6 %, textures 53.9 %, plan bake 23 / route 61 / drop 88, unclassified 0 |
| `appearance_plan.py --write` then `--check` | *md match True, json match True* → **check ok** |
| `texture_build_plan.py --write` then `--check` | 23 rows, faithful yes 5 / partial 6 / no 12 → **check ok** (byte-stable: no timestamp in the page) |
| `t_blocked.py --check` | **PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope; ledger sha256 unchanged** |
| `t_rows.py check` | **check ok** — ledger 199 rows (edit 16, next 86, keep 52, epe 26, re-read 0, blocked 11, out 1, superseded 7), 35 edits over 16 rows; unchanged by this task (no `T_ROWS.jsonl` edit) |
| `status_audit.py --check` | **STATUS.md is current** |

Pin upkeep: this task changes **no ledger row and no `blocked` set** (all edits are in
`Working/Appearance` and `Tools/scripts`), so `WAITS` and `in_scope == 216` in
`Tools/scripts/t_blocked.py` needed no edit and `--check` passes unchanged. `t_blocked.py` was not
modified, so no backup was required.

## 6. Limits

- The plan is a schedule, not evidence of work done: a row keeps its build status
  (`excluded`/`partial`) until a converted `.ddsc` exists and is registered.
- 12 of 23 rows cannot be built faithfully today. Four of those (the chapter masks) cannot be built
  faithfully at all without a variant set; the other eight are waiting on pixels that no file in this
  tree carries.
- The bake's tiling unit (`MicroDetail_size` = 15 / 30 / 45 / 120 / 250) is still the one number that
  changes the output, and it is UNKNOWN: check C2 (repeat-frequency peak) is the only reader that can
  settle it.
- No game launch, no install, no build step; every number above is a file read or an arithmetic on one.
