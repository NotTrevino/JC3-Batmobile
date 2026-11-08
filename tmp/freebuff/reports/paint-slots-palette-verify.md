# Do the paint slots verify against the palette? One row per slot, 32 slots, 4 exact / 13 differ / 15 unsourced

**Task.** Take every paint slot that `tmp/freebuff/reports/paint-slots-to-bmak-values-apply-plan.md`
names and maps to a BmAK colour value, and check its **slot index** and its **RGB triple** against
`tmp/freebuff/reports/COLOUR-palette.md` and the colour grab that report cites
(`Research/JC3Grab/PALETTE_HASH.md`, the `.epe`-to-palette decode; the tool is
`Tools/scripts/jc3_palette_hash.py`). Count exact matches, differences and slots with no source.

**Result.** 32 slots. **4 match exactly, 13 differ, 15 have no source at all.** The one class the
palette can referee — the 10 tint colour triples — fails 10/10: no palette record carries
`[0.025787, 0.025787, 0.03]`, and the source it should have come from (BmAK) is not this grab. The
palette's scalars fare better: `A = 1.0` and `clear_coat = 1.0` agree on all 10 records. Everything
in the `cb2`/`cb6`/`cb8`/`s0` half of the plan is **unsourced**, because the cited grab never states a
value for a cbuffer or sampler slot — it explicitly records the palette→`cb6` binding as UNKNOWN.

**Three defects found while checking the indices** (§4): the plan's palette record base is wrong by
16 B against the build palette and 48 B against the cited grab; the tint triple has no palette
provenance; and the albedo green byte `0x41` is 1 code value above its own stated linear value
(correct: `0x40`).

**Labels.** **decoded** = a byte or a `offset-in-file` read at the named offset. **derived** =
arithmetic on decoded values, shown. **UNKNOWN** = searched and absent, with the file that settles it.

---

## 1. Method, so the counts are auditable

**Verdict rule, applied to one slot at a time.** A slot is the *(carrier, index)* pair the plan names,
with the value the plan says to write in it.

| verdict | test |
|---|---|
| **match** | the cited source states a value for **that slot**, and the plan's written value equals it on **every** record/instance the slot covers |
| **differ** | the cited source states a value for that slot, and the plan's value differs on at least one record/instance |
| **no source** | the cited source states **no value** for that slot — neither the palette report nor its grab mentions it, or the grab explicitly records the binding as UNKNOWN |

The rule is deliberately strict about "every record": `metallic` is scored **differ** even though 8 of
10 tints already hold 1.0, because the slot as the plan writes it (all 10) is not what the source says
(two records are 0.0).

**Sources, in the order they are preferred in each row.**

| tag | file | what it can referee |
|---|---|---|
| `CP` | `tmp/freebuff/reports/COLOUR-palette.md` | the `.epe` reference, the 10-record palette, `Black` at `0x184`, `metallic = 1.0` in 8 of 10, the palette↔block write-back UNKNOWN |
| `GRAB` | `Research/JC3Grab/PALETTE_HASH.md` | the same palette fully decoded: 7 floats per record, per-record offsets `0x94 + 0x50·k`, all 10 tint triples, the `(0.4, 1, 1)` block override triple |
| `BP` | `tmp/freebuff/scratch/tint/palette.xml` | second witness, in-project: the **build's** palette export with `offset-in-file` on every member — used only to check the *indices*, never to referee a value |
| `CM` | `Research/JC3Grab/COLOUR.md` | the shipped paint blocks' own dynamic floats (`0.14, 0.19, 0.25, 1` …) and the "which float4 is TintColorR is UNKNOWN" statement |

`GRAB` is the grab `CP` cites: `CP`'s own text says "it decodes to the 10 tint records, `Black` =
`(0.2, 0.2, 0.2)` at `0x184`" and its §"Files written" names `Research/JC3Grab/PALETTE_HASH.md` as the
deliverable.

**Slots excluded from the 32, and why.** The plan names `cb2[3]` `m_Emissive`, `cb2[5..7]`
(`m_DirtParams`/`m_DirtBlend`/`m_DirtColor`), `cb2[8..14]` (decal count/width/4 colours/blend),
`cb2[15..17]` (`m_Damage`/`m_DamageBlend`/`m_DamageColor`), `cb2[18]`, `cb2[19]`, and all of `cb7`.
Each is mapped to **no BmAK colour value** (`—`, "0", or "no BmAK value maps to a `cb7` member"), so
there is no triple to check. The plan's own words for `cb2[3]`: "— (not a paint value here)".

---

## 2. The 32 rows

### 2.1 Palette slots — 14 rows (2 match, 12 differ, 0 unsourced)

Plan target for every tint: `tint_r = tint_g = tint_b = [0.025787, 0.025787, 0.03]`, `A = 1.0`,
`specular_gloss` 0.600, `metallic` 1.0, `clear_coat` 1.0. Plan's own slot line:

> `| palette record (alternative carrier) | `tints[i].tint_r/g/b` @ `0x50+80i+20/+36/+52` | none | same three floats, `A = 1.0` |`

| # | slot | plan value | source value | source line (quoted) | verdict |
|---:|---|---|---|---|---|
| P1 | `tints[0].tint_r/g/b` (White) | 0.025787 / 0.025787 / 0.03 | 0.880000 / 0.880000 / 0.880000 | `GRAB` §6: `\| 0 \| White \| 100 \| (0.880000, 0.880000, 0.880000) \| 1.000000 \| 0.000000 \| 0.000000 \| 1.000000 \|` | **differ** |
| P2 | `tints[1]` (Evergreen Pearl) | same | 0.094118 / 0.229412 / 0.164706 | `GRAB` §6: `\| 1 \| Evergreen Pearl \| 100 \| (0.094118, 0.229412, 0.164706) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P3 | `tints[2]` (Garnet Red Metallic) | same | 0.426471 / 0.050000 / 0.050000 | `GRAB` §6: `\| 2 \| Garnet Red Metallic \| 100 \| (0.426471, 0.050000, 0.050000) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P4 | `tints[3]` (Black) | same | 0.200000 / 0.200000 / 0.200000 | `GRAB` §6: `\| 3 \| Black \| 100 \| (0.200000, 0.200000, 0.200000) \| 1.000000 \| 0.000000 \| 0.000000 \| 1.000000 \|` — and `CP`: "`Black` = `(0.2, 0.2, 0.2)` at `0x184`" | **differ** |
| P5 | `tints[4]` (Grey) | same | 0.410667 / 0.410667 / 0.410667 | `GRAB` §6: `\| 4 \| Grey \| 100 \| (0.410667, 0.410667, 0.410667) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P6 | `tints[5]` (Silver) | same | 0.424000 / 0.424000 / 0.424000 | `GRAB` §6: `\| 5 \| Silver \| 100 \| (0.424000, 0.424000, 0.424000) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P7 | `tints[6]` (Blue) | same | 0.218667 / 0.322667 / 0.458667 | `GRAB` §6: `\| 6 \| Blue \| 100 \| (0.218667, 0.322667, 0.458667) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P8 | `tints[7]` (Brown) | same | 0.432000 / 0.389333 / 0.384000 | `GRAB` §6: `\| 7 \| Brown \| 100 \| (0.432000, 0.389333, 0.384000) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P9 | `tints[8]` (Red) | same | 0.538667 / 0.200000 / 0.200000 | `GRAB` §6: `\| 8 \| Red \| 100 \| (0.538667, 0.200000, 0.200000) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P10 | `tints[9]` (Green) | same | 0.200000 / 0.424000 / 0.200000 | `GRAB` §6: `\| 9 \| Green \| 100 \| (0.200000, 0.424000, 0.200000) \| 1.000000 \| 0.450000 \| 1.000000 \| 1.000000 \|` | **differ** |
| P11 | `tints[i].A` (all 10) | 1.0 | 1.000000 × 10 | `GRAB` §6 A column, every row `1.000000`; `CP`: "every record re-read from `0x94 + 0x50*k` equals the ADF walk (10/10)" | **match** |
| P12 | `specular_gloss` @ +68 (all 10) | 0.600 | 0.450000 × 8, 0.000000 × 2 | `GRAB` §6 gloss column; `CP` §4 refutation 4 context: "eight records have `metallic = 1.0`" beside gloss `0.450000`, and `GRAB` §6 rows 0 and 3 carry `0.000000` | **differ** |
| P13 | `metallic` @ +72 (all 10) | 1.0 | 1.0 × 8, 0.0 × 2 (White, Black) | `GRAB` §6: "`metallic = 1.0` in records 1, 2, 4, 5, 6, 7, 8, 9 (8 of 10)"; plan states the same: "**1.0** (8 of 10 tints already 1; the other 2 are 0)" | **differ** (8/10 already agree) |
| P14 | `clear_coat` @ +76 (all 10) | 1.0 | 1.000000 × 10 | `GRAB` §6 coat column, every row `1.000000`; plan: "**1.0** (already 1 on all 10 tints)" | **match** |

**P1–P10 are the substantive failures.** The plan's triple is a **BmAK** value
(`Material0_BaseColour`, `colour-bmak-wet-look.md` §2) written *into* the palette; the palette is not,
and was never claimed to be, its source. So "differ" here is not a contradiction the plan makes — it
is the measurement that **the palette cannot corroborate the colour at all**, and that after the write
no record retains a colour any source attests. The nearest record to `[0.025787, 0.025787, 0.03]` is
`Black` at `0.2` — 7.8× brighter — and no record has `R = G ≠ B`, which the plan's triple does
(`0.025787, 0.025787, 0.03`), so the blue bias the plan wants does not exist anywhere in the table.

### 2.2 Cbuffer and sampler slots — 18 rows (2 match, 1 differ, 15 unsourced)

| # | slot | plan value | source value | source line (quoted) | verdict |
|---:|---|---|---|---|---|
| B1 | `cb2[0]` @0 `m_SpecularGloss` | `[0.6, 0.6, 0.6, 0.6]` | — | `GRAB`/`CP` name no `cb2` value. `CP`'s only block-side number is the override triple, §"UNKNOWN": "**Any write-back between the palette's numbers and the paint blocks'** `(0.4, 1, 1)` override triple. No file maps one to the other." | **no source** |
| B2 | `cb2[1]` @16 `m_Metallic` | `[0.0, 0.0, 1.0, 0.0]` | — | same; `CM` §1 lists the float4 *names* only. The component position (2 = 1.0) is the plan's own inference and it flags the conflict: "`colour-bmak-wet-look.md` §6 records it as 'one value for the whole block'" | **no source** |
| B3 | `cb2[2]` @32 `m_ClearCoat` | `[1.0, 1.0, 1.0, 1.0]` | — | same; consistent with `GRAB`'s palette coat 1.0 but a different carrier | **no source** |
| B4 | `cb2[4]` @64 `m_DiffuseWrap` | not written | — | plan: "**not written** \| role UNKNOWN (§5)"; `CP` never names `m_DiffuseWrap` | **no source** |
| B5 | `cb6[0]` @0 `m_TintColorR` | `[0.025787, 0.025787, 0.03, 1.0]` | index UNKNOWN; block content `(0.14, 0.19, 0.25, 1)` | `GRAB` §9.1: "**Which tint the engine selects … and whether it copies that tint into the CarPaintMM dynamic float4s.** The `.epe` says *which palette module* the entity uses; it carries no selected index". `CM` §6.1: "Which dynamic float4 is `TintColorR` … UNKNOWN" | **no source** |
| B6 | `cb6[1]` @16 `m_TintColorG` | same | index UNKNOWN | same `GRAB` §9.1 / `CM` §6.1 line | **no source** |
| B7 | `cb6[2]` @32 `m_TintColorB` | same | index UNKNOWN | same | **no source** |
| B8 | `cb6[4].x` @64 `m_SpecularGlossOverride` | 0.600 | **0.4** | `GRAB` §9.2: "the paint blocks' own override triple is `(0.4, 1, 1)`"; `CM` §1 shows the same `…, 0.4, 1, 1` on the three paint blocks | **differ** |
| B9 | `cb6[4].y` @68 `m_MetallicOverride` | 1.0 | **1** | `GRAB` §9.2: "the paint blocks' own override triple is `(0.4, 1, 1)`" — middle component | **match** |
| B10 | `cb6[4].z` @72 `m_ClearCoatOverride` | 1.0 | **1** | `GRAB` §9.2, third component of `(0.4, 1, 1)` | **match** |
| B11 | `cb8[8]` `ModelDiffuseColor` | not written | — | plan: "**not written**"; `CP` never names `cb8` | **no source** |
| B12 | `s0` `DiffuseMap` / `t0` — effective albedo | `0x43 / 0x41 / 0x45` | — | no palette or grab line states an albedo byte. `CP`'s palette has no `s0`; `GRAB` decodes no texture | **no source** |
| B13 | `s0` — authored raw | `0x2D / 0x2D / 0x30` | — | same | **no source** |
| B14 | reflectivity 0.2 (`Material0_Reflectivity`) | **no slot** | — | plan §3.3: "`cb2` has gloss, metallic, clearcoat only"; `CP` §UNKNOWN lists no reflectivity member either | **no source** |
| B15 | `Wetness_Refl_Fresnel` 0.6 | no slot | — | plan §3.6: "0 of 13 `carpaintmm*` headers declare a wetness member"; `CP` silent | **no source** |
| B16 | `Wetness_Reflectivity_Multiplier` 0.6 | no slot | — | same | **no source** |
| B17 | `RainReflectivityMul` 1.6 | no slot | — | same | **no source** |
| B18 | `RainRoughnessMul` 0.75 | no slot | — | same | **no source** |

B14–B18 are scored **no source**, not "differ", because the plan declares them unwritable and writes
nothing. The palette grab agreeing that no such member exists is not a value match.

---

## 3. The count

| verdict | palette rows | cbuffer/sampler rows | **total** |
|---|---:|---:|---:|
| **match exactly** | 2 (P11 `A`, P14 `clear_coat`) | 2 (B9, B10) | **4** |
| **differ** | 12 (P1–P10, P12, P13) | 1 (B8) | **13** |
| **no source** | 0 | 15 (B1–B7, B11–B18) | **15** |
| **rows** | 14 | 18 | **32** |

Reconciliation: 4 + 13 + 15 = 32, and 14 + 18 = 32.

The headline in one line: **the only slots this source can referee are the palette's 14, and 12 of them
disagree with the plan.** Of the 18 cbuffer/sampler slots, 15 cannot be checked at all against a
palette grab; the 3 that can are the `cb6[4]` override triple, where 2 agree and 1 (gloss 0.6 vs 0.4)
does not.

**What "differ" does and does not mean.** 12 of the 13 differences are *intentional overwrites*: the
plan is replacing the donor's numbers with BmAK's, and it says so. None of them is an internal
contradiction of the plan. The verification's value is the negative result: the palette provides **no
independent attestation for any value the plan writes**, and for the 10 tint triples the post-write
state has no source anywhere in the grab.

---

## 4. Index checks, and the three defects

### 4.1 The palette record base is wrong in the plan — and in the file it cites

The plan's formula, §1.4:

> so `tints[i].tint_r.R` is at file offset `0x50 + 80·i + 20`, and a one-float edit changes exactly 4 bytes

`BP` (the build palette's own ADF export, `offset-in-file` on every member) gives record 0's
`tint_r.R` at **`00000074`**, then `000000C4`, `00000114`, `00000164`, `000001B4`, `00000204`,
`00000254`, `000002A4`, `000002F4`, `00000344` — a stride of exactly `0x50`, base `0x74`.

* Plan at `i = 0`: `0x50 + 0 + 20` = **`0x64`**. Build palette: **`0x74`**. **16 B (0x10) low.**
* `GRAB` §6, the cited grab's own byte check, puts record 0 at **`0x94`** ("each record re-read from its
  own `0x94 + 0x50*k`"), confirmed by `CP`'s "`Black` … at `0x184`" because `0x94 + 0x50·3 = 0x184`.
  Plan at `i = 0` is therefore **48 B (0x30) low** against the grab it says it decodes.

The missing 16 bytes are the array header, which `TINT_WRITE.md` names in the very sentence the plan
paraphrases: "data base `0x50`, array header 16 B". Correct forms:

```
build palette  (BP)          tints[i].tint_r.R = 0x74 + 0x50·i
cited grab     (GRAB)        tints[i].tint_r.R = 0x94 + 0x50·i
plan, as written             tints[i].tint_r.R = 0x64 + 0x50·i   <- neither
```

`TINT_WRITE.md` contains the same contradiction internally: its formula `0x50 + 80*i + 20 + 4*c` and
its own decoded line `<member name="R" … offset-in-file="00000074">` cannot both be right. The plan
inherited the formula and not the correction. **The member offsets inside the record are right**:
`BP`'s type definition gives `tint_r` offset `20`, `tint_g` `36`, `tint_b` `52`, `specular_gloss`
`68`, `metallic` `72`, `clear_coat` `76` — exactly the plan's `+20/+36/+52` and `+68/+72/+76`.

**Effect.** A write plan that edits `0x50+80i+20` writes into the previous record's `clear_coat`/
padding region — at `i = 0`, `0x64` is inside the array header, 16 B before White's `tint_r`.

### 4.2 The cbuffer slot arithmetic does hold

Checked, and it is correct. `cb2` float4 *i* at `+0x9 + 16·i` gives `0x9`, `0x19`, `0x29` for
`i = 0, 1, 2` — the three offsets the plan prints. `cb6[4].x/y/z` at `64/68/72` from `payload +0x145`
gives `0x185/0x189/0x18D` — also what the plan prints. `CM` §1 independently decodes
`static_params` at `0x9` (288 B) and `dynamic_params` at `0x145` (76 B), and `BP`'s stride/member
agreement shows the same ADF walk is sound. **What has no source is the member identity**: which of the
four dynamic float4 is `TintColorR`, recorded UNKNOWN by both `GRAB` §9.1 and `CM` §6.1. So the index
arithmetic is verified and the semantics are not — which is why rows B5–B7 are `no source` rather than
`match`.

### 4.3 The albedo green byte is 1 code value high

The plan's §3.1 row quotes `0x43 / 0x41 / 0x45` "(= 0.0566 / 0.0516 / 0.0600 linear)". Recomputing the
stated transfer (`linear → 8-bit sRGB`, the 2.4-piece curve) on the plan's own linear numbers:

```
0.056738 ->  67.365 -> 67 = 0x43   OK
0.051580 ->  64.197 -> 64 = 0x40   plan says 0x41  <- 1 low-value error
0.060000 ->  69.283 -> 69 = 0x45   OK
```

`0x41` (65) is **0.052861** linear, not 0.05158 — 2.5 % high on the green channel, enough to tint the
charcoal slightly green and to break the M1/§4B assertion band if it is tightened below ±1 code value.
The raw authored triple is exact by the same arithmetic (`0.025787 → 44.57 → 45 = 0x2D`,
`0.03 → 48.39 → 48 = 0x30`), so only the adjusted triple carries the error — inherited from T-MA3,
which prints the same three bytes beside the same three floats.

### 4.4 The build's palette is not the one the plan describes

`BP` is the palette the current build ships (`solar_cars_palette.vmod`, 920 B). Its 10 records — same
names, `White` … `Green` — hold **`0.0500000007` on every channel of every record**, `A = 1`,
`specular_gloss = 0.449999988` on all 10, `metallic = 1`, `clear_coat = 1`. Compare the cited grab's
vanilla 1,897 B table: real colours (`White` 0.88, `Black` 0.2) and gloss `0.45 × 8 / 0.0 × 2`.

Consequences for two plan statements, which are **true of the grab and false of the build**:

* "**1.0** (8 of 10 tints already 1; the other 2 are 0)" — correct for `GRAB`, but the build palette
  has **no zeros**: `metallic = 1` on 10/10. The two records the plan expects to change are already 1.
* gloss `0.45 × 8 / 0.0 × 2` (T-MA4/T-MA7) — the build palette is `0.45 × 10`.

Neither changes a written value (the plan overwrites all 10 either way), but the read-back M7
("assert 0.6 across 10 tints") cannot distinguish a correct write from a partial one on this build,
because 10/10 already have the same gloss and metallic.

---

## 5. What this verification does not cover

* **Only COLOUR-palette.md + its grab.** The cbuffer slots may be checkable against another source
  (e.g. `Research/JC3Grab/TINT.md` line 44 for `static_params[0] = (0.0, 0.4, 0.3737, 1.0)`, or a
  `.rbm` re-decode of the built files). That is outside this brief and is not claimed.
* **No build, no write, no game.** Everything above is a file read: two reports, one ADF XML export,
  and one arithmetic check. No `.rbm`, `.vmodc` or `.dds` was modified; the palette was not re-exported.
* **`GRAB` was not re-run.** `jc3_palette_hash.py --check` needs `_gamedata/JC3grab` (outside this
  repository); its decoded offsets are taken as published, and only `BP`, which is in-project, was read
  directly.
* **The "no source" bucket is not an error count.** 15 of those 18 rows are slots the plan itself
  labels unwritable or unbound; a palette grab is simply the wrong instrument for them.

## 6. Revert

Delete this file. Nothing else was created or changed; no input report, palette, build artefact or
script was touched.
