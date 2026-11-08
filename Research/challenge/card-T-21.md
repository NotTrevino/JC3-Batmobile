# Assumption challenge — card T-21 · Appearance completion

Written 2026-10-30. **Read-only review with one disclosed exception.** Nothing in
`GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`, `Tools/`, `Builds/` or any game file was modified; no
game was launched, nothing was written to `D:\Games`, nothing was committed, no secret was read.

The exception: running the card's *second* Done command,
`python Tools/scripts/appearance_progress.py --build Working/Appearance/build_bud1 --strict-plan`,
rewrites `Working/Appearance/progress.json` and `progress.md` (the tool always writes — it has no
dry-run). I ran it, saw the rewrite, and restored both files: `progress.json` is now **byte-identical
to `tmp/progress.afterT21.json`** (`cmp` clean, 80,052 B) and `progress.md` is back to 25,500 B /
198 lines with the same `generated` value (`2026-10-28T06:53:14`) and mtime. The only unrecoverable
difference is the original `generated` stamp, whose seconds came from a 06:55 run of identical
content and which I could not reconstruct; I restored the 06:53:14 value from the card's own
`tmp/progress.afterT21.json` rather than invent one. This is also finding **A2** below.

**In scope, as required:** `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–77), the T-21 card (lines
955–963), its §12 row (line 1330), the MODLOG sections `## T-21 · Appearance completion — intended
change` (13124) and `— done (2026-10-28)` (13352), and the card's outputs —
`Working/Appearance/APPEARANCE_PLAN.md` (522 lines), `Working/Appearance/appearance_plan.json`
(96,186 B), `Tools/scripts/appearance_plan.py` (621 lines). Cross-checked against the card's `In:`
files (`Working/Appearance/progress.md`, `progress.json`, `Research/BatmobileGrab/SLOTS.json`,
`VARIANTS.md`), the build the numbers were measured from (`Working/Appearance/build_bud1/factors.json`,
`assembly.json`, `ddsc/`), the tools that produce them (`Tools/scripts/factors.py`,
`appearance_progress.py`), the grab (`Working/Appearance/grab/`, `grab_manifest.json`), and the
shader reflection `Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt`.

**Card as written:** "classify each of the 136 no-slot and 36 partial components: bake into
albedo/normal (POL-2), route to another block type, or drop with reason. Interior materials (POL-1).
Skins per D-5. Out: `APPEARANCE_PLAN.md` + `appearance_progress.py` reflecting the plan.
**Done: 0 unclassified components.**"

---

## VERDICT

**The 172 rows are real, the counts reproduce, and the plan is a genuinely useful classification —
but the card's Done gate is red today, the Done criterion is satisfied by construction, and the two
reasons that carry the most rows are not true as stated.** `appearance_plan.py --check` exits **1**
(`VARIANTS.md §3: expected 4 variant rows, parsed 0`) because `VARIANTS.md` was regenerated on
2026-10-29 with plain counts where the generator's regex requires `**bold**`; nothing re-ran T-21.
The "0 unclassified" that the card calls done is guaranteed by the table having exactly **21 rules
for exactly 21 distinct (class, status, why) triples** — one per reason string already in
`progress.json` — so the criterion can only fail if a *new* reason appears. And "drop = no carrier
exists" is false for **45 of the 141 drops**: `CarPaintMM` has `m_DirtParams`/`m_DirtBlend`/
`m_DirtColor` + the `s6 DirtMap` sampler and `m_Damage*` + `s4/s5`, and the build sets the
`SupportDirt`/`SupportDmgBlend` flags to 0 by decision (R1/APP-7), not for lack of a carrier.

What survives: the 339 / 167 / 36 / 136 / 0 input shape and the 23 / 8 / 141 split (all re-derived
here); the per-rule row counts (D1 41, D2 27, D4 14, D5 1, D6 12, D8 7, D7 8, D11 9, D12 1, D13 8,
D9 4, D3 4, D10 3, D14 2 = 141; P1 6, P2 15, P3 2 = 23; R1 3, R2 2, R3 2, R4 1 = 8); the interior
six-slot set and its 24-row tally (7 bake / 1 route / 16 drop); the "no F0, no anisotropy, no
weather input" claims against the shader reflection; the `progress.json` plan column (172 rows, 0
mismatches); and every one of the 17 "transferred" textures resolves to a bound sampler.

What does not: the gate (A1), the read-only-ness of the gate (A2), "0 unclassified" as evidence of
work (A3), the definition of `drop` (A4), the ramp reason (A5), the bake sources (A6), and the POL-1
"no untextured surface" (A7).

| # | assumption | verdict |
|---|---|---|
| A1 | the card's `--check` gate is green / reproducible | **BROKEN** |
| A2 | the Done checks are read-only | **BROKEN** (verified by running it) |
| A3 | "0 unclassified" is a test that can fail | **BROKEN** (21 reasons ↔ 21 rules) |
| A4 | `drop` means "no JC3 carrier exists" | **BROKEN** for D1 (41) + D9 (4) |
| A5 | the colour-ramp rows are dropped because the files are missing | **BROKEN** (2 of 3 are on disk) |
| A6 | the 6 micro-detail textures exist to be baked | **WEAK** (5 of 6 absent from the export) |
| A7 | POL-1: six slots, all samplers bound, no untextured surface | **WEAK** |
| A8 | POL-1's 24 rows are interior components | **WEAK** (binding-touch, body textures included) |
| A9 | the bake does not touch the R9 texture budget | **WEAK** (count argument, KB wall) |
| A10 | D3/D13's reasoning (per-pixel gloss, displacement) | **WEAK** (self-contradiction; inconsistent with P1) |
| A11 | "no F0 / no anisotropy / no weather input on CarPaintMM" | **HOLDS** |
| A12 | the skins re-run the same plan / the counts are G1-20's | **WEAK** (one build; §3 format changed) |
| A13 | the input is 339 / 167 and `progress.json` reflects the plan | **HOLDS** |

---

## A1 · The Done gate is green

**Claim.** §12: `| T-21 | done | … `Tools/scripts/appearance_plan.py --check` (172/172 classified:
23 bake POL-2, 8 route, 141 drop, 0 unclassified; …)`. The MODLOG done block prints
`check ok` and `md match True, json match True`.

**Test.**

```
$ python Tools/scripts/appearance_plan.py --check
VARIANTS.md §3: expected 4 variant rows, parsed 0
EXIT=1
```

**Why.** `Research/BatmobileGrab/VARIANTS.md` mtime `2026-10-29 04:14:54` — regenerated a day after
T-21 ran — and §3's table lost the bold counts the parser requires:

```
## 3. Materials (`Material` + `MaterialInstanceConstant`)

| variant | count | extra vs V2 | missing vs V2 |
|---|---|---|---|
| V2 | 78 | — | — |
| MK2 | 80 | 4 | 2 |
```

```
generator regex (needs **78**): 0 matches
plain-count regex:              4 matches  → ('V2','78',' — | — |'), ('MK2','80',' 4 | 2 |'), …
```

The section split still matches (`"## 3. Materials"` is a prefix of the new heading), so the failure
is purely the `\*\*(\d+)\*\*` in `appearance_plan.py:parse_skins`. Two consequences: (a) the gate is
red; (b) even with the regex fixed, the §6 cells that the MODLOG calls "the extra/missing lists
verbatim" would now print `4` and `2` — the table carries *counts*, not lists. The counts
themselves (78 / 80 / 69 / 84) are unchanged, so the doc's numbers are still right.

Note the guard also pins the input shape (`components 339 / transferred 167`) and fails on legitimate
progress changes; that is a deliberate rework trigger, not a defect, but it means this card's gate is
coupled to files other cards regenerate.

**Verdict: BROKEN.**

---

## A2 · The Done checks are read-only

**Claim.** The card's Done is two commands, the second of which is
`python Tools/scripts/appearance_progress.py --build Working/Appearance/build_bud1 --strict-plan`.
§0.2/§0.5 do not say a check may rewrite its own input.

**Test.** I ran it as the card prints it:

```
$ python Tools/scripts/appearance_progress.py --build Working/Appearance/build_bud1 --strict-plan
…
plan: bake 23 route 8 drop 141 | unclassified 0
progress -> Working\Appearance\progress.json and Working\Appearance\progress.md
EXIT=0
```

Both files were rewritten (`generated` 2026-10-28T06:55… → 2026-10-30T05:01:10; sizes 80,052 →
77,301 and 25,500 → 25,303 because the rewrite also changed CRLF→LF). I restored both: `cmp
tmp/progress.afterT21.json Working/Appearance/progress.json` → byte-identical (80,052 B), and
`progress.md` back to 25,500 B / 198 lines.

**Why it matters.** `progress.json` is the *card's own `In:` file*. A Done check that regenerates its
input means the check can never be run against a frozen snapshot: if the build changes between the
plan and the check, the plan silently goes stale and the check still prints the same tally. The doc's
§9 "Reproduce" line names this command as the way to reproduce the plan, which cannot be true.

**Verdict: BROKEN** as a process/provenance claim (the numbers it printed are correct).

---

## A3 · "0 unclassified" is a test that can fail

**Claim.** The card's Done is `0 unclassified components`; the plan prints `unclassified 0` and
`--check` fails if it is not 0.

**Test.** Count the population the rules classify:

```
distinct (cls, status, why) triples among the 172: 21
rules in the plan:                                 21
triples with no rule:                               0
rules with 0 components:                           none
components per rule: D5 1, D10 3, P1 6, D3 4, R4 1, R2 2, D9 4, D11 9, D2 27, D1 41,
                     P2 15, D4 14, P3 2, D8 7, D12 1, R1 3, R3 2, D13 8, D7 8, D6 12, D14 2
```

The classification is keyed on **(class, status, why)** — `_rule_for()` matches the exact reason
string that `progress.json` already recorded — and the rule table has exactly one rule per distinct
reason. So `unclassified` is 0 for every input that has no *new* reason string; the plan is a
re-encoding of `progress.json`'s reasons with an action attached, not an independent classification
of 172 components. The Done criterion is therefore a closed loop: it fails only if the generator and
the input fall out of sync, never because a component was overlooked. (The tamper test #4 in the
MODLOG — deleting rule D7 — does fail it, which proves the *table* is checked, not that the plan
found anything.)

This is not a fatal objection — the card asks for "one action per component, reason stated", and that
is what the plan does — but the done block presents `0 unclassified` as if it were a search result.

**Verdict: BROKEN** as evidence of coverage (the 172/172 tally itself is real).

---

## A4 · `drop` means "no JC3 carrier exists"

**Claim.** Plan §1: *"drop | 141 | no JC3 carrier exists; the value is dropped and the reason is
stated per rule"*; the doc's opening defines drop the same way. §12: *"141 drop"*.

**Test.** The block interface the same plan relies on
(`Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt`) carries the carriers:

```
float4 m_DirtParams;   float4 m_DirtBlend;   float4 m_DirtColor;      // static params
float4 m_Damage;       float4 m_DamageBlend; float4 m_DamageColor;   // static params
DirtMap            sampler s6     DamageNormalMap  sampler s4     DamageAlbedoMap  sampler s5
```

and the build turns them off *by value*: every material in `factors.json` carries
`"flags": {"value": 0, "source": "… decals/dirt/damage/… off (see support.*); IS_DEFORM off (user rule)"}`.

So the 41 `D1` rows ("JC3 dirt (dynamic per object); BmAK mud is chapter-scripted") and the 4 `D9`
rows ("story-chapter damage reveal (JC3 damage is hit-driven)") are dropped because the project
*chose* to disable JC3's dirt/damage carriers, not because the block has no input for them. 45 of
141 drops (32 %) fall outside the plan's own definition of the action. The reasons themselves are
good (R1/APP-7: scorch/smoke only, hit-driven damage) — they are decisions, and the taxonomy should
say "disabled by design", not "no carrier".

**Verdict: BROKEN** for the definition of `drop` (the dispositions of D1/D9 are defensible).

---

## A5 · The colour-ramp rows are dropped because the files are missing

**Claim.** D10 (`colour ramp lookup (and the ramp files are missing-on-disk)`), 3 rows:
`Batman_BM3_V2_Lacquered_Underlayer_Ramp`, `Batman_BM3_V2_Leather_Ramp`,
`Batmobile_V3_Body_ColourRamp`. Plan §4 repeats the reason; §8 relies on it.

**Test.** The reason is a **typed literal** in the upstream tool, not a disk check:

```
Tools/scripts/factors.py:122
  ("tex", r"^Colour_Ramp_Map$", "no-jc3-equivalent",
   "colour ramp lookup (and the ramp files are missing-on-disk)"),
```

The real per-texture check is a different branch (`factors.py:197`, `missing-on-disk -- texture {v}
not in the dump`), and `factors.json` contains **0** dispositions with that branch. Two of the three
ramps are on disk and in the grab manifest:

```
$ find Working/Appearance -iname "*Ramp*"
Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batman_BM3_V2_Leather_Ramp.tga
Working/Appearance/grab/Startup/Texture2D/Batman_BM3_V2_Lacquered_Underlayer_Ramp.tga
grab_manifest objects[28] Batman_BM3_V2_Leather_Ramp  →  Playable_Batmobile_SF\Texture2D\…tga
grab_manifest objects[83] Batman_BM3_V2_Lacquered_Underlayer_Ramp → Startup\…tga
```

Only `Batmobile_V3_Body_ColourRamp` is genuinely absent from the 115-file grab and the 88-object
manifest. A dropped row is allowed to be a design decision (a colour ramp has no JC3 input), but the
*stated proof* is false for two of the three rows and is generated by a hard-coded string — the one
audit trail the plan offers for those rows does not exist.

**Verdict: BROKEN.**

---

## A6 · The 6 micro-detail textures exist to be baked

**Claim.** Bake group (23 rows): *"6 micro-detail textures (`Batmobile_Microdetail`, `Micropattern_A/
_A_Normal/_B/_C`, `neutral_normal`), 15 micro-detail tiling sizes, 2
`underlayer_Detail_to_Roughness` — all baked into s1/s0 at convert time"*. Plan §2: *"the BmAK source
texture is baked into a sampler the block already has"*.

**Test.** Check each of the six against the grab (115 files) and the manifest (88 objects):

```
grab files 115 | manifest objects 88
Batmobile_Microdetail            on disk ✔
Batmobile_Micropattern_A         absent
Batmobile_Micropattern_A_Normal  absent
Batmobile_Micropattern_B         absent
Batmobile_Micropattern_C         absent
neutral_normal                   absent
```

The props do reference them — `grep Micropattern` over the dumped materials finds
`Micropattern_A`, `_A_Normal`, `_B`, `_C` in `Batmobile_V3_Cockpit_MIC.props.txt` and
`Batmobile_V3_Emissive.props.txt` — and the grab exported only `Micropattern_D_N` and
`Micropattern_E_N`. `neutral_normal` is not a texture asset at all: it is a *value* on five
dispositions (`tex:Material1_Microdetail_N` …), i.e. the neutral default, so there is nothing to bake
for it even if a file existed.

So 5 of the 6 P1 rows have no source texture in the export. The bake slot exists on every material
(19/19 bind s1), so the action is well-formed — it just cannot run for five of six rows without a new
grab, and neither the plan nor `--check` says so. (`--check` never looks at the grab.)

**Verdict: WEAK** — the classification stands, the executability does not.

---

## A7 · POL-1: six slots, all samplers bound, no untextured surface

**Claims.** §12: *"POL-1 interior 6 slots all samplers bound"*. Plan §5: *"All six already have their
four samplers bound (`s0` diffuse, `s1` normal, `s2` property map, `s3` tint map), so … the interior
has no untextured surface"*; *"none of them is a missing colour or a missing normal map"*.

**Tests.**

```
interior table (from appearance_plan.json):
  10 Batmobile_V3_Cockpit_MIC     s0,s1,s2,s3   17 planned rows
  11 BatmobileV3_Cockpit_Seat     s0,s1,s2,s3    6
  12 Cockpit_Master_Flip_Data     s0,s1,s2,s3    0
  14 Stagg_Battery_01_MAT         s0,s1,s2,s3    0
  15 Stagg_Battery_Energy_01_MAT  s0,s1,s2,s3    0
  16 Nimbus_Power_Cell_Mat        s0,s1,s2,s3    1
bound-slot sets over all 19 materials: {'s0','s1','s2','s3'} × 18, {'s0','s1'} × 1
```

The "four samplers bound" claim is literally true — but "bound" is a *key present*, and two of the six
are bound to placeholders:

```
Cockpit_MIC.s0      = {"solid": [0.43137…], "kind": "colour",
                       "source": "generated from bmak:Main_BaseColour (…)"}
Cockpit_Master_Flip_Data.s0 = {"solid": [0.5,…], "source": "neutral (no colour data: mid grey)"}
Cockpit_Master_Flip_Data.s1 = {"vanilla": "textures/00_general/dummy/a00_dummy_flat_nrm.ddsc"}
Cockpit_Master_Flip_Data.s2/s3 = {"vanilla": "textures/00_general/dummy/a00_dummy_black_mpm.ddsc"}
Seat / Battery / Energy / Nimbus: s2 and s3 are the vanilla dummies (no authored mask)
```

The cockpit shell's diffuse is a flat grey generated from `Main_BaseColour`; the authored interior
diffuse (`Batmobile_V3_Int_Cockpit_D`) is bound to the **seat**, not the cockpit. `Flip_Data` is
entirely dummy: mid grey, flat normal, black property/tint maps — it *is* an untextured material
(100 LOD0 faces). So "no untextured surface" is true of the slot keys and false of two materials, and
"none of them is a missing colour or a missing normal map" is false for `Flip_Data` by construction.
Also note the plan renders this claim as a *branch*: if the four samplers were missing it would print
a different sentence and still exit 0 — the sentence is not checked.

**Verdict: WEAK.** The six-slot set itself holds (see A8), and the generated-colour decision is
recorded, but the POL-1 "closed with no new interior texture" conclusion rests on boundness, not on
content.

---

## A8 · POL-1's 24 rows are interior components

**Claim.** §12/§5: *"24 of the 172 rows touch an interior material — 7 bake, 1 route, 16 drop.
**POL-1 closes with no new interior texture**"*. Plan §5: *"A component shared by two interior
materials … appears in both rows, which is why the column sums to more than the 24 unique interior
components listed next."*

**Tests.**

```
POL-1 rows: 24  Counter({'drop': 16, 'bake': 7, 'route': 1})          ✔ the tally
interior column sum: 17 + 6 + 0 + 0 + 0 + 1 = 24                      ✗ "more than the 24"
```

The 24 count is a *binding-touch* count: a row is tagged POL-1 if **any** material that binds the
texture is one of the six. The tagged texture rows are:

```
Aniso_ramp_Lacquered                binders: Cockpit_MIC + 6 body materials
Batman_BM3_V2_Lacquered_Underlayer_Ramp  binders: Cockpit_MIC + 5 body materials
Batman_BM3_V2_Leather_Ramp          binders: Cockpit_Seat only
Batmobile_Micropattern_C            binders: Cockpit_MIC, Emissive
Batmobile_V3_Int_Cockpit_E          binders: Cockpit_Seat
Batmobile_V3_Int_Cockpit_S          binders: Cockpit_Seat
Nimbus_Power_Cell_S                 binders: Nimbus_Power_Cell_Mat
neutral_normal                      binders: Cockpit_MIC, Emissive
```

Two of the seven "interior" texture rows are the **body lacquer anisotropic ramps** — car-exterior
signals that happen to also be bound on the cockpit material. So "24 interior components remain" is
true as "24 rows touch an interior material" and misleading as "the interior has 24 gaps": the
interior-only set is smaller, and the doc's own §5 sentence about the column over-summing is false
for its own data (24 = 24).

**Verdict: WEAK.**

---

## A9 · The bake does not touch the R9 texture budget

**Claim.** Plan §2: *"The bake changes no block count and no texture count, so it does not touch the
R9 texture budget."*

**Test.** R9 is a **KB** wall (Texture 7,065 KB), not a count wall. The reference build's textures:

```
Working/Appearance/build_bud1/ddsc: 28 files, total 4,048,448 B = 3,953.6 KB, largest 1,398,256 B
```

The bake replaces the s1 normal content of every material (18 CarPaintMM + 1 Window). Re-baking a
micro-detail pattern into a 1.4 MB normal at higher resolution increases KB while leaving the count
at 28 — precisely the case the sentence rules out. Whether the headroom is enough is unmeasured; the
plan's own §8 lists per-skin budget as UNKNOWN but asserts the V2 bake is free.

**Verdict: WEAK** — a non-sequitur (count ⇒ no KB change) in a document whose budget rule is KB.

---

## A10 · D3 and D13's reasoning

**D3 (4 rows, per-pixel roughness → drop).** Plan D3 note: *"s2 PropertyMap selects one of four
material channels per pixel; it cannot vary roughness per pixel"*. The first clause is the
counter-example: if the map selects a channel per pixel, gloss **does** vary per pixel — among four
values. The true limitation is "not continuously", which the row does not say. The channel semantics
are also inferred upstream, not decoded: `factors.py` header — *"Channel semantics INFERRED from
vanilla data (§78)"*. So the drop rests on an inferred mapping, stated as a decoded one.

**D13 (8 rows, tessellated displacement → drop) vs P1 (6 rows, micro-detail → bake).** Both are
normal-space signals carried by the body's `s1` normal; P1 proves the mechanism exists and is the
plan's largest bake group, while D13 drops displacement as *"no tessellation on the JC3 side"*. The
real distinction (displacement moves the silhouette, micro-detail only shades) is never made, so two
adjacent rows use opposite dispositions for the same carrier. If D13 were baked like P1 the bake
count would be 31 and the drop count 133.

**Verdict: WEAK** (D3 wording + D13 consistency).

---

## A11 · "No F0 / no anisotropy / no weather input on CarPaintMM"

**Claims.** D2: *"CarPaintMM has no reflectance input"*; D4/D5: *"no anisotropy input"*; D7/D8:
*"JC3 weather system (engine-global)"*. These carry 27 + 15 + 15 = 57 of the 141 drops.

**Test.** The shader reflection the tool cites:

```
m_SpecularGloss (4ch) m_Metallic (4ch) m_ClearCoat (4ch) m_Emissive (4ch) m_DiffuseWrap
m_DirtParams m_DirtBlend m_DirtColor m_DecalCount[unused] m_DecalWidth m_Decal1-4Color
m_DecalBlend m_Damage m_DamageBlend m_DamageColor                    = 18 float4
SupportDecals SupportDmgBlend SupportLayered SupportOverlay SupportRotating
SupportDirt SupportSoftTint                                          = 7 floats
m_TintColorR/G/B + m_SpecularGlossOverride m_MetallicOverride m_ClearCoatOverride
samplers s0..s3 (diffuse/normal/property/tint) + s4..s9 (damage/dirt/decal)
```

No reflectance/F0, no anisotropy, no rain/wetness parameter — the claims hold, and the reflection is
a real decoded interface (in `Tools/JCMR-src`), not a name list. Caveat: one of the 18 is marked
`[unused]` (`m_DecalCount`) and two `[unused]` model colours sit outside the static block, so "18
static" counts an unused member; and the scope is this one shader. That is the scope the rows need.

**Verdict: HOLDS.**

---

## A12 · The skins re-run the same plan

**Claim.** §12/§6: *"the generated §6 reproduces G1-20's material counts (V2 78 / MK2 80 / Joker 69 /
Funhouse 84) with the extra/missing lists verbatim; the actions are per factor name, so MK2's
replacement body/wheel materials re-run the same plan"*.

**Tests.**

- `VARIANTS.md` §3 now stores **counts**, not lists: `MK2 | 80 | 4 | 2`, `Joker | 69 | 26 | 35`,
  `Funhouse | 84 | 13 | 7` (the lists moved to the prose below the table). So "verbatim lists" is
  stale, and the cells the doc prints would be `4` / `2` once the parser is fixed (A1).
- The counts 78 / 80 / 69 / 84 are still exactly right.
- "Re-run the same plan" is tested on **one** factors.json (the V2 reference build). MK2's extra
  materials (`Batmobile_MK2_Body_MIC`, `Batmobile_MK2_Wheel_INST`, …) and Joker/Funhouse's
  Jokerfied set have no factors.json, and the rules key on *reason strings produced by that run* —
  so a new material set produces a new reason population, not "the same plan". The doc admits the
  per-skin counts are UNKNOWN, then asserts the re-run anyway; it also gives the correct conditional
  (*"they need their own `factors.json` run"*), so the two sentences disagree.

**Verdict: WEAK** (per-skin UNKNOWNs are honest; the "re-runs unchanged" claim is a one-build sample).

---

## A13 · The input is 339 / 167 and `progress.json` reflects the plan

**Claims.** Plan header: *"components 339 = transferred 167 + partial 36 + excluded 136 + missing 0"*;
card `Out:` — *"`appearance_progress.py` reflecting the plan"*.

**Tests.**

```
progress.json overall: 339 / 167 / 36 / 136 / 0                     ✔ (and plan totals agree)
progress rows carrying a plan: 172, mismatches vs appearance_plan.json: 0
transferred texture components: 17, of which bound to no sampler: 0
texture rows with no binding material: 0
```

All 17 "transferred" textures resolve to a sampler in `factors.json` (26 distinct textures bound;
9 bound textures are not components — the tyre/wheel/decoy dummies). The 23/8/141 split, the per-rule
counts and the MODLOG's per-group labels (41 / 27 / 14+1 / 12 / 9+1 / 8+7 / 8 / 4 / 4 / 3 / 2 = 141)
all re-derive.

**Verdict: HOLDS.**

---

## What this challenge did not test

- Whether the micro-detail bake is *possible* at the resolution the materials need, or how s1
  re-baking interacts with the body's authored normal (`Factors` note: "one normal per block,
  priority Normal_Map > Texture_Normal > …").
- Whether `neutral_normal` should be a planned row at all (it is a parameter *value*, not a
  component); the plan treats it as one and tags it POL-1 + POL-2.
- The `Window` block parameter values (MODLOG §102d, undisclosed here) — the plan routes the glass
  rows and keeps the vanilla response; that is stated, not verified.
- Any visual result: no game launched, no build installed, no screenshot (R6).
- The Joker/Funhouse material sets (no `factors.json` exists), as the doc says.
- Whether "drop" for D1/D9 would be better expressed as `route` to the disabled carrier; that is a
  taxonomy question for T-23, not a data question.

## Reproduce

```
python Tools/scripts/appearance_plan.py --check          # exit 1, VARIANTS.md §3 (A1)
python Tools/scripts/appearance_plan.py --show Batmobile_V3_Cockpit_MIC
python - <<'…'                                           # A3/A7/A8/A13: triples ↔ rules, POL-1 tag,
  #  interior table, plan column, distinct bound-slot sets (all in-memory reads)
grep -n "Colour_Ramp_Map" Tools/scripts/factors.py       # A5: the literal reason at :122
find Working/Appearance -iname "*Ramp*" -o -iname "*Micropattern*"   # A5/A6
python - <<'…'                                           # A6: 6 bake names vs 115 grab files / 88 manifest objects
du -cb Working/Appearance/build_bud1/ddsc/* | tail -1    # A9: 4,048,448 B
grep -n "m_SpecularGloss\|m_Dirt\|m_Damage\|SupportDirt" Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt
```

Files read: `GRAB_BACKLOG.md`, `MODLOG.md` (13124–13163, 13352–13441), `MODDING_PLAN.md` (phase 6
item 6), `Working/Appearance/{APPEARANCE_PLAN.md,appearance_plan.json,progress.json,progress.md,grab_manifest.json}`,
`Working/Appearance/build_bud1/{factors.json,assembly.json,coverage.md,ddsc/}`,
`Research/BatmobileGrab/{SLOTS.json,VARIANTS.md,VALUES.json}`, `Tools/scripts/{appearance_plan.py,
appearance_progress.py,factors.py}`, `Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt`,
`Tools/GibbedSrc/…/Blocks/CarPaint*.cs`, `tmp/progress.afterT21.json`.
