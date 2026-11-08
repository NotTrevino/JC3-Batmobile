# Apply the paint, collision and appearance v2 plans — third serial pass

Card: apply-v2-body-rows. 2026-11-08. Third serial pass over `Working/Translation/T_ROWS.jsonl`, after
the weapon pass (first) and the driving/world pass (second, `apply-v2-driving-and-world-rows.md`).
Inputs, read only: `tmp/freebuff/reports/paint-plans-v2.md` (the four paint channels, F0, wetness —
audit `audit-paint-plan-colour-numbers.md`, 12 MATCH / 5 MISMATCH / 3 UNSOURCED) and
`tmp/freebuff/reports/collision-impact-and-mode-switch-plans-v2.md` (the impact rows, the
no-crash-damage reconciliation, the mode swap with **U1 kept UNKNOWN**). Evidence read for the texture
rows: `Builds/bm-RC4-appearance/texture_ledger.json` `refusals`, and for the cross-check
`Builds/bm-RC4/receipt.json` `not_done` (6 sentences).

**Provenance / reversibility.** Intended change: replace the cells these two audits refuted, mark the
rows only a player take can confirm, add the 12 refused-texture rows with an action instead of a
refusal, add the paint-channel rows and the mode-swap row the ledger lacked, and keep the pin honest.
Files edited: this page, `Working/Translation/T3_COVERAGE.md` (§1c + T-DM7/T-DE1 cells),
`Working/Translation/T2_TRANSLATION.md` (T-MA3/T-MA7 cells), `Tools/scripts/t_rows.py`,
`Tools/scripts/t_blocked.py`; regenerated: `T_ROWS.jsonl`, `BLOCKED_PROPOSALS.{json,md}`, `STATUS.md`.
Backups: `Tools/scripts/t_blocked.py.bak-b14`, `Tools/scripts/t_rows.py.bak-b14`. Revert = restore those
two and `git checkout -- Working/Translation/T3_COVERAGE.md Working/Translation/T2_TRANSLATION.md
STATUS.md`, then `t_rows.py build`, `t_blocked.py --write`, `status_audit.py --write`. No game was
launched; no `.rbm`, texture, palette, `VALUES.json`, module or build was written (test ban holds).

---

## 1. Counts, before and after

| metric | before (after pass 2) | after | source |
|---|---:|---:|---|
| ledger rows | 225 | **244** | `t_rows.py check` header |
| in-scope rows | 244 | **260** | `t_blocked.py` header line |
| blocked (ledger + T6) | 18 + 4 = **22** | 27 + 4 = **31** | `t_rows.py` counts + `t_blocked.py` |
| queued (`next`) | 114 | **120** | `t_rows.py` counts |
| `epe` | 38 | **38** | `t_rows.py` counts |
| `out` in the ledger | 3 | **6** | `t_rows.py` counts (T6's 7 unchanged → 13 total) |
| `keep` | 29 | **30** | `t_rows.py` counts |
| resolved from evidence / in scope | 164 / 244 (67.2%) | **170 / 260 (65.4%)** | `STATUS.md` as `status_audit.py` writes it |

The in-scope count moves by +16 (19 new rows − 3 `out`), which is why the pin was updated in §6. The
resolved **share** falls (67.2 % → 65.4 %) because nine of the new rows are `blocked` and three are
`out` — the refusal list was carrying those gaps unrecorded, not resolving them.

## 2. Cells the audits refuted, and what replaced them

| row | old cell | new cell | audit line |
|---|---|---|---|
| `T-MA3` | albedo **`0x43/0x41/0x45`** = 0.0566/**0.0516**/0.0600 (sRGB 0.265/**0.254**/0.272) | **`0x43/0x40/0x45`** = 0.0566/**0.051574**/0.0600 (sRGB 0.265/**0.2518**/0.272) | `paint-plans-v2.md` **M3** (`sRGB(0.05158) = 0.2518 → 64.20 → 0x40`; 0x41 is 0.052861 linear, **2.5 % high on green**) |
| `T-MA7` | "…the T-MA3 `0x43/0x41/0x45`…" | "…the T-MA3 `0x43/0x40/0x45`…" | same M3; the tint menu must not carry the retired byte |
| `T-DM7` | `rotor_collision` byte offset **UNKNOWN** (inside the `.ee`-embedded shared module) | block at **0x130-0x13C**, rate **0x138**, `min_rpm` 0x130, `mass_ratio_when_no_mass` 0x134, `light_object_mass_ratio` 0x13C — **decoded by `struct.unpack`** | `tdm7-contact-damage-speed-band.md` §2 rows 1-2; the "offset UNKNOWN" was stale |
| `T-DM7` | rate **100000/s** presented as the value to carry, plan's floor absent | 100000/s **kept as the decoded value**, and the v2 plan's "**2000/s at 0x138**, keep" recorded as its **derived write target**, with the conflict named UNKNOWN | `VOCABULARY.md:1415` measures **100000 .. 100000, n=232, donor included**; `tdm7` §43 labels the 2000/s row "**derived (ram plan §2.4)**", §102 lists the decoded value as 100000. **I did not overwrite 100000 with 2000** — "keep 2000" cannot be kept and the shipped number is only settled by re-reading 0x138 |
| `T-DM7` | — | floor **`min_rpm` 30 → 1260** (the ~20 km/h gate) + the 20/80 km/h clone-and-ram probe added to the cell | `collision-impact-and-mode-switch-plans-v2.md` §4 steps 1 and 4 |
| `T-DE1` | pulse/tune decoded, immunity implied by `impact_damage_factor` 0 | adds **`TakesDamageFromRam` returns `true` unconditionally** (`DAMAGE_RULES.md:192-202`), so BmAK has **no immunity switch** and the observation is engine-side | `collision-…-v2.md` §2.1 ("no such field") |

**Two numbers I deliberately did not write.** (a) the 2000/s above; (b) the paint plan's `F0_d = 0.04`
bridge, which the plan itself marks **ASSUMED** — it is carried into `T-PC5` labelled, not into a
written member. Nothing else in the two inputs was applied to a cell without a decoded or derived
source.

## 3. Rows marked take-gated (only a player take can confirm them)

"take-gated" is written into the row's `proposed` cell, so the ledger itself says the row cannot close
on a file read. Marked: `T-PC1`, `T-PC2`, `T-PC3`, `T-PC4`, `T-PC5` (pilot band 67/64/69 ±2 code
values), `T-TX8` (highlight elongation), plus the rows whose own verify cell is already a probe and
whose text now says so — `T-DE1` (explosion within 0-1 s), `T-DM7` (20/80 km/h clone-and-ram).

## 4. The twelve texture rows — action instead of refusal

`texture_ledger.json` refuses 12 of the 23 texture rows the receipt calls unfaithful: **4 chapter
masks** + **8 pixel-set refusals** (4 `Micropattern_*`, `Wheel_E`, `Body_ColourRamp`,
`Lacquered_Underlayer_Ramp`, `Aniso_ramp_Lacquered`). Each now has a row with the closest-system
action:

| row | texture | refusal | closest-system action | dispo |
|---|---|---|---|---|
| `T-TX1` | `Batmobile_Micropattern_A` | 0 of 61 grab `.tga` | one P1 microdetail layer (already shipped) + the extra plate **declared absent**, no synthetic tiles | `blocked` |
| `T-TX2` | `Micropattern_A_Normal` | 0 of 61 | same, and **no substitute map** exists (P1 writes tangent XY into `s1`) | `blocked` |
| `T-TX3` | `Micropattern_B` | 0 of 61 | declared absent | `blocked` |
| `T-TX4` | `Micropattern_C` | 0 of 61 | declared absent | `blocked` |
| `T-TX5` | `Batmobile_V3_Wheel_E` | 0 of 61, "four arch strips stay dark" | **the refusal is the built state** — keep the strips dark, no colour guess | `keep` |
| `T-TX6` | `Body_ColourRamp` | no pixels **and** 0 of 961 headers name a ramp sampler | the colour is carried by `s0`'s region means (`T-PC1`…`T-PC4`) | `out` |
| `T-TX7` | `Lacquered_Underlayer_Ramp` | **pixels present** (Startup, 4,050 B) but no ramp sampler | corrected verdict: a **sampler** refusal, not a pixel one | `out` |
| `T-TX8` | `Aniso_ramp_Lacquered` | no ramp, 0 aniso samplers | **two-slot gloss split 0.75 / 0.45**, BRDF declared isotropic | `next` |
| `T-TX9` | `Body_Damage_ChapterMask` | no chapter selector; `SupportDmgBlend` `[0.0]` in all 160 blocks | crude single state rejected (paints every chapter) **and** declined by the no-damage-stages ruling | `blocked` |
| `T-TX10` | `Weaponry_Damage_ChapterMask` | same | same | `blocked` |
| `T-TX11` | `WheelArch_Damage_ChapterMask` | same | same | `blocked` |
| `T-TX12` | `Undercarriage_Damage_ChapterMask` | same | same | `blocked` |

The 13th refusal (`Batman_BM3_V2_Leather_Ramp`, pixels present, no sampler) is *not* in the 12
(`counted_in_the_12: false`) and is recorded in `T-TX7`'s text rather than given a row, so the count of
new texture rows matches the receipt's sentence exactly.

**Paint channels added** (`paint-plans-v2.md` §3, none of which the ledger carried):
`T-PC1` gloss `[0.60, 0.75, 0.85, 0.98]`, `T-PC2` metallic `[0, 0, 1, 1]`, `T-PC3` clear coat
`[1, 1, 1, 1]` (sourced elsewhere), `T-PC4` tints + the `cb6[4]` triple `[0.75, 0, 1]`, `T-PC5` F0
`0.0080 / 0.0080 / 0.0360 / 0.0060` and MK2 `0.162` with its residuals, `T-PC6` the wetness family
(`out`, no member). The writer blockers are named in the cells: `gloss_cap` 0.4 → 1.0, `albedo_gain`
→ 1.0, and the three `factors.py` rules that cannot emit the values from the dumps.

**Mode swap added**: `T-MS1`, `blocked` on **U1**. It carries the two corrections the mode rows needed
and the ledger never stated: `TurnOnSpot*` exists in **two objects** (archetype 0.8 / −0.8 / 2 vs
shipped-sim CDO 0.6 / −0.5 / 0.01), `BattleModeTurnOnSpotTorqueFactor` is **0.333333 archetype vs 0.3
on the sim**, part behaviours are **67** not 66, and `_signature_shielded` is **MIS-CITED** (0 hits in
`ENTITIES.md`, 6 in `FORCEPULSE.json`). The `.ee`-leaf + Rebel Drop route is written as the buildable
half; the trigger stays UNKNOWN.

## 5. Cross-check: every `receipt.json` `not_done` sentence, and the rows that answer it

| # | `not_done` sentence (verbatim, abridged) | rows that answer it |
|---:|---|---|
| 1 | "**12 of 23 texture rows are unfaithful (4 chapter masks + 8 missing pixel sets)**: the tree is NOT complete" | `T-TX1`…`T-TX12` (12 rows, §4); `T-TX5` is the one the tree already matches, `T-TX6`/`T-TX7` are `out` on the sampler, `T-TX8` has the gloss-split action |
| 2 | "**B-10 shape set is incomplete**: 1 of 3 BmAK boxes carried — chassis box 1 and the weapons-pod box have no hull shape instance: 2 of 3 boxes missing, 0 free hull slots" | `T-P3` (bodies 2 / boxes 3 / constraint 1, card `T22_REOPEN.md`), `T-CO1`, `T-CO2` — the hull target and the body count |
| 3 | "**B-12/D-2 modes**: pursuit set only; 0 exact, 2 composed (`T-MD5`, `T-MD6`), 2 same unbuilt switch (`T-MD10`, `T-MD11`), 4 not built (`T-MD7`, `T-MD13`, `T-MD8`, `T-MD14`)" | those eight rows plus **`T-MS1`**, which is the swap trigger they all depend on and the row that keeps U1 UNKNOWN |
| 4 | "**B-17..B-20** are declared no-payload in BUILD_BATCHES and ship no payload" | `T-FX12` (B-17 tracer), `T-WP5` (B-18 EMP), `T-WP7` (B-19 hacker/tracker), `T-WP8` (B-20 sonar) |
| 5 | "**B-25 and B-26** are cards only; neither has a payload" | `T-WP4` (B-25 lock hold / 8-target salvo), `T-AU2` (B-26 per-vehicle bank override) |
| 6 | "**runtime load, Rebel Drop resolution and the Q takes are untested**" | **no row can answer this** — it is the take gate itself: `T-WLD1`, `T-WLD4`, `T-WLD6` (the drop keys) plus every take-gated row in §3 and the §4 `T-TX*` verify cells |

Five of the six sentences already had a row; sentence 1 had **none** (the refusals lived only in the
ledger JSON), which is what §4 fixes. Sentence 6 is not a row-level defect and is recorded as such.

## 6. Pin upkeep

| pin | before | after |
|---|---|---|
| `t_blocked.py` `WAITS` | 22 ids | **31 ids** — added `T-MS1` and `T-TX1`, `T-TX2`, `T-TX3`, `T-TX4`, `T-TX9`, `T-TX10`, `T-TX11`, `T-TX12` (+ `T-CT1`…`T-CT5` from pass 2 remain) |
| `reconciles` | `len(lb) == 18`, `t6 == 4`, `blocked == 22`, `in_scope == 244` | `len(lb) == 27`, `t6 == 4`, `blocked == 31`, `in_scope == 260` |

`t_blocked.py` was backed up to `.bak-b14` before pass 2 and not edited again destructively; it was run
`--write` then `--check` after this pass, and `--check` re-ran every `RESOLVED` evidence marker and
compared the ledger sha256.

## 7. Checks run

| check | result |
|---|---|
| `python Tools/scripts/t_rows.py build` | `244 rows, 35 edits over 16 rows` |
| `python Tools/scripts/t_rows.py check` | `ledger 244 rows \| edit 16 next 120 keep 30 epe 38 re-read 0 blocked 27 out 6 superseded 7 \| edits 35 over 16 rows` → `check ok` |
| `python Tools/scripts/t_blocked.py --write` / `--check` | `31 blocked rows (27 ledger + 4 T6) of 260 in scope; 0 tested, 7 resolved` → `PASS … ledger sha256 unchanged` |
| `python Tools/scripts/status_audit.py --write` / `--check` | `STATUS.md is current` — 170 / 260 resolved (65.4 %), 31 blocked, 120 queued, `T-3` 62 rows |
| `python Tools/scripts/bmak_coverage.py --check` | `check ok` (423 G1 fields still assigned, 0 unassigned) |
| `python Tools/scripts/t10_reopen.py --check` | **exit 0** — `16 rows (5 superseded, 6 out, 2 blocked)`, json/md match. Two notes: the two `why` edits from pass 2 were reverted in `t_rows.py` (the corrections stay in the T-3 cells, and the T-10 table is that tool's authority), and it prints an **informational census** that 6 `out` rows (its `later` group: `T-PC6`, `T-PT13`, `T-PT2`, `T-PT5`, `T-TX6`, `T-TX7`) do not cite a proof file. Those rows cite the plan paths in their `proposed` cells; the census is a `--check` print, not a stored table, and `--check` still passes |

## 8. Rows left open, and the file that would settle each

| row / group | open because | settler |
|---|---|---|
| `T-TX1`…`T-TX4` | the four micropattern plates have no pixels (0 of 61 `.tga`) | a re-grab of the `Playable_Batmobile*` packages (`Working/Appearance/grab/**/Texture2D`) |
| `T-TX9`…`T-TX12` | no chapter selector for `Damage_Chapter_Mask` (0 of 961 headers; `SupportDmgBlend` `[0.0]` in 160 blocks) | a `CarPaintStatic` header declaring a chapter uniform, the SHEX body, or a probe of `SupportDmgBlend` 1 |
| `T-MS1` | U1: no runtime entity swap consumer | `JustCause3.exe` (the archive holds 0 `.exe`), second read = its binding for the 11 `teleport` graphs |
| `T-PC1`…`T-PC5` | the writer cannot emit them (`gloss_cap` 0.40, metallic trigger 0.5, coat gated on `Normal_Map_Lacquer`) and the values are only confirmed by a take | step 0's `VALUES.json` edit + `spec_check.py --block 3` + the body take |
| `T-PC2`, `T-PC5` | whether the SHEX reads `cb2[1].w`; `F0_d = 0.04` is ASSUMED | the `carpaintmm*.fb.txt` / `Batmobile_Worn` SHEX body |
| `T-PC6` | un-decoded composition order of the four wet numbers | the BmAK material-function graph (stripped: 944/944 slots zero) |
| `T-DM7` | is the shipped rate 100000/s or the plan's 2000/s? | re-read `vehicle_common.vmodc` at **0x138** (12,271 B, `struct.unpack`) |
| `T-DE1` | whether the car's `.ee` still carries `CForcePulse` + `car_explosion_medium`; the blast's firing instant | `jc3forcepulse.py` dump, then the §3.3 pilot |
| `T-TX8` | the gloss split needs a highlight take | a lacquered-shell highlight take (band: streak elongates, no cross lobe) |

## 9. What this pass did not do

No `.rbm`, texture, palette, `VALUES.json`, module, `.ee` or `Builds/` file was touched; the paint
plan's step 0-5 is a plan, and none of it was run. `factors.py`, `bat_assemble.py`, `spec_check.py`,
`appearance_bake.py` and `jc3forcepulse.py` were not invoked. `JustCause3.exe` was not opened, so U1
stays UNKNOWN by design. The 12 texture rows record an action per refusal; they do not claim any
refused plate was carried.
