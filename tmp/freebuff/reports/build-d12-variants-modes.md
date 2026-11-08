# B-12 — the variant pair, built (pursuit vs battle)

**Task:** build step **B-12** (reopened 2026-11-06 with D-2). `apply-mode-switch-rows.md` recorded the
two-mode plan and four unmet preconditions; this pass builds the mechanism it named — `bm_build.py
--variant pursuit|battle`, two trees under `Builds/bm-RC4-modes`, an `aafdiff` that must list exactly
the planned files — and reports which rows are carried **exactly**, which by **closest-system plus
build composition**, and which are **not built**.

**State after this pass:** the pair exists and is measurable. `--variant` is registered (precondition
4's build-surface half), 2 variant trees exist, both trees' receipts re-read green, and the
cross-variant `aafdiff` is exactly the 2 declared files. **No game was launched, nothing was
installed, no dropzone or vanilla file was touched.** The card stays `todo` because the runtime swap
(U1) is still UNKNOWN and the table still declares one row set — see §6.

Labels: **decoded** = read at the file/member named, on disk, this pass; **derived** = arithmetic
over decoded inputs; **composed** = two decoded facts joined by a build decision; **UNKNOWN** =
searched and absent, with its settler named.

---

## 0. Answer, in one table

| | result |
|---|---|
| pair built | `Builds/bm-RC4-modes/pursuit/` and `Builds/bm-RC4-modes/battle/`, one build tree each, one receipt + one installer each, never run |
| mechanism | `bm_build.py --variant pursuit\|battle` reads the variant out of the edit spec, refuses a spec that disagrees, and writes `<build>/variant.json` (planned files + per-row carry) into the receipt |
| `aafdiff` | **exactly the 2 planned files**: 588 identical, 2 changed, 0 added, 0 removed, 0 size deltas — PASS |
| rows carried **exactly** | **0** |
| rows by **closest-system + build composition** | **2** — T-MD5, T-MD6 |
| rows on the **same unbuilt switch** | **2** — T-MD10, T-MD11 |
| rows **not built** | **4** — T-MD7, T-MD13, T-MD8 (named omission), T-MD14 (named omission) |
| values written | `official_top_speed` 336.4 → **21.6** km/h; `arcade.nitro_boost.extra_top_speed` 43.2 → **0** |
| budgets (both trees) | model **4,657.6** KB of 4,915; texture **5,855.8** KB of 7,065 — unchanged from the base |

The headline is the zero. JC3 has no member that switches a handling value per mode
(`mode-switch-carriers.md` §2.7), so a variant cannot "carry a row" the way a member edit does: the
second value set *is* the whole carrier, and even the two rows this build writes are a composition,
not a translation. Calling them exact would be the plausible-sounding implementation `AGENTS.md`
forbids.

---

## 1. What was built

### 1.1 The mechanism (`Tools/scripts/bm_build.py`)

`--variant pursuit|battle` adds no new edit format. A variant spec is an ordinary schema-1 edit spec
plus three keys, and `load_variant()` requires them:

```json
{"schema": 1, "card": "B-12", "variant": "battle",
 "planned_files": ["editor/.../x.vmodc"],
 "rows": [{"row": "T-MD6", "carry": "composed", "why": "..."}],
 "steps": [{"applier": "t5_apply", "edits": "...", "current": "..."}]}
```

* every `--edits` spec must declare the same `variant` as the flag — a spec that disagrees raises,
  because a tree that does not know which variant it is cannot be diffed against its sibling;
* `carry` is validated against `exact | composed | same_switch | not_built`, and a row may not be
  declared twice;
* the declaration is written to `<build>/variant.json` and copied into `receipt.json` as
  `bm.variant`, with a receipt check naming the counts. No other build behaviour changed.

### 1.2 The two trees

| | `Builds/bm-RC4-modes/pursuit/` | `Builds/bm-RC4-modes/battle/` |
|---|---|---|
| base | `Builds/bm-RC4-base` | `Builds/bm-RC4-base` |
| spec | `Working/Translation/b12_variant_pursuit.json` (0 steps) | `Working/Translation/b12_variant_battle.json` (1 step → `b12_battle_edits.json`) |
| aaf tree | 590 files, 22,011,703 B, digest `561D301D0499EE7B…` | 590 files, 22,011,703 B, digest `3BF77C6AEE12EDDA…` |
| edits | 0 | **2 rows over 2 modules** |
| packed `.ee` | 10,737,057 B, `6AB8275F566A3542…` | 10,737,057 B, `4709D823A2ED2E93…` |
| `.toc` | 50,643 B, 506 records | 50,643 B, 506 records |
| identity | **byte-identical to `bm-RC4-base`** (control) | differs in `.ee` only, `.toc` list identical |

Pursuit is deliberately an identity build: it is the delivered car and the control that proves the
difference seen in battle is the variant's, not the scaffold's.

**One limit, stated plainly:** the pair is two *build trees*, i.e. two payloads with two `.ee`
hashes, but both still carry the same internal entity name and path. Making them two coexisting
entities (name/hash, second drop entry) is **B-13** plus U1 — not built here, and not claimed.

---

## 2. The `aafdiff` — exactly the planned files

`python Tools/scripts/b12_variant_diff.py --pursuit …/pursuit/aaf --battle …/battle/aaf --out
tmp/freebuff/reports/aafdiff-pursuit-battle.md`, comparison **SHA-256** (so a same-size value change
cannot hide):

| Bucket | Count |
|---|---:|
| Files only in pursuit | 0 |
| Files only in battle | 0 |
| Common, identical content | **588** |
| Common, **different content** | **2** |
| …of which size differs | 0 |

| Bytes A | Bytes B | Delta | Path |
|---:|---:|---:|---|
| 3,399 | 3,399 | +0 | `…/modules/default/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc` |
| 2,332 | 2,332 | +0 | `…/modules/default/v0300_car_kensington_sportsmuscle_vehicle_misc.vmodc` |

Gate result: **`PASS: the diff is exactly the declared file set`** (exit 0). The declaration is read
from the battle build's own `variant.json`, not from the report, so the build and the assertion
cannot drift apart silently. `aafdiff`'s full report is at
`tmp/freebuff/reports/aafdiff-pursuit-battle.md`.

Note the near-miss the size check would have hidden: both files are byte-length-identical before and
after, which is exactly why the gate hashes instead of trusting sizes.

---

## 3. The rows this build actually flips

`t11_variants.json` lists **13 rows whose pursuit and battle text differ** (T-MD1, 2, 4, 5, 6, 7, 8,
9, 10, 11, 12, 13, 14). **That is a text count, not a value count** — the corrected split is 4 rows
flipping to the battle variant, 2 named omissions, and 2 turning on the same switch. The build is the
arbiter, and it changes **2 of those 13 rows' worth of bytes**:

| row | carry | file / member | evidence |
|---|---|---|---|
| **T-MD5** | **composed** | `…_custom_land_global.vmodc`, `arcade.nitro_boost.extra_top_speed` 43.2000008 → **0** | BmAK's battle envelope is a curve (0→60, 600→40, 1200→30) and **no member takes a curve**. The variant carries the envelope's end state instead: with the nitro delta at 0, the battle entity cannot regain the pursuit's +43.2 km/h — the only in-place speed change in the fleet (§2.4). The 3 curve points stay raw in the table |
| **T-MD6** | **composed** | `…_vehicle_misc.vmodc`, `official_top_speed` 336.399994 → **21.6** | 21.6 km/h is BmAK's decoded `TurningModeMaxSpeed` (600 cm/s); `official_top_speed` is the fleet's decoded km/h stat (T-E5). Both numbers decoded, the *join* is the composition: BmAK's member is a turning-mode cap, JC3's is a top-speed stat, and no cap member exists |
| **T-MD7** | not built | — | `BattleModeSteerAngleFactor` is **1**, so the steering angle does not change; `LatSlipScale` 0.75 / `LongSlipScale` 1.25 / `DrivingForceZOffset` 20 cm have **no member on either side**. The row flips in the table and writes nothing — the honest outcome |
| **T-MD13** | not built | — | pose is a per-entity graph constant, and the member-level route is **blocked by the toolchain**: `ConvertAdf --e sportsmuscle_vehicle_parts.vmodc` throws `NullReferenceException` in `InstanceMemberInfo.PrepareForWritting` → `InstanceInfo.GuessInlineArrayCopyPosition` (measured this pass). `bm_build` has no `.epe` applier, so the pose is declared, not written |
| **T-MD10** | same switch | — | `ArmourModeDamageReduction` is **0 in every shipped package**, so both variants are identical here; flipping changes no file |
| **T-MD11** | same switch | — | battle FOV **60** already sits inside the delivered 55–63 band |
| **T-MD8** | named omission | — | no pivot carrier in *either* variant (G2-21 refuted every candidate) |
| **T-MD14** | named omission | — | `BML_Battlemode` media exist but no `Usage` consumer dispatches on a battle mode (U1), and an entity swap is not an entry/exit transition |

**Rows carried exactly: none.** The seven remaining rows (T-MD1, 2, 3, 4, 9, 12, 15) are identical in
both variants — same values, same files — so no variant distinction exists for them to carry.

---

## 4. The values, re-read from the built tree

`t5_apply` asserts each `old` before writing and re-reads each `new` after; this is the independent
second read of the battle tree by a separate process:

| module | member | before | after | decoded text |
|---|---|---:|---:|---|
| `VehicleMisc` | `official_top_speed` | 336.399994 | 21.6 | `21.6000004` |
| `CustomLandGlobal` | `arcade.nitro_boost.extra_top_speed` | 43.2000008 | 0 | `0` |
| `CustomLandGlobal` | `arcade.nitro_boost.torque_multiplier` | 2 | 2 | `2` (untouched) |
| `CustomLandGlobal` | `arcade.nitro_boost.grip_multiplier` | 1 | 1 | `1` (untouched) |
| `LandSteering` | `steer_angle_min/max_speed_deg` | 55 / 20 | 55 / 20 | unchanged, as T-MD7 requires |

Applied list (`battle/applied.json`): T-MD5 3,399 → 3,399 B; T-MD6 2,332 → 2,332 B; both
`members_unchanged` = all remaining members, which `t5_apply` enforces by failing if any untouched
member moves.

Budgets, measured on this build by `bm_build.py` (not carried from the base): model non-vanilla
**4,657.6** KB of 4,915 (reachable 7,032.4); texture resident **5,855.8** KB of 7,065. The variant
adds no asset, so this is the base's number holding — and it is the D-04 budget's, unchanged.

---

## 5. Checks actually run

All in `E:/Modding/JustCause3/JC3-Batmobile` with `OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8` (this host
caps allocations, so numpy-heavy helpers need the single thread).

| command | result |
|---|---|
| `py_compile bm_build.py b12_variant_diff.py b12_variants.py` | OK |
| `bm_build.py --tag bm-RC4-modes/pursuit --variant pursuit … --force` | **exit 0** — 10/10 receipt checks, `.ee`/`.toc` **byte-identical to `bm-RC4-base`** |
| `bm_build.py --tag bm-RC4-modes/battle --variant battle … --force` | **exit 0** — 10/10 checks incl. "only edited modules differ (2 changed)", "no edit step outside the named list (1 step, 2 rows)", variant counts |
| `b12_variant_diff.py --pursuit … --battle … --out …` | **exit 0** — `PASS: the diff is exactly the declared file set` |
| `bm_build.py … --tag …/battle --check` | **exit 0** — 20/20, `.ee`/`.toc` re-read and hashed against the receipt, source digest `3BF77C6AEE12EDDA…`, budgets green, `installed: false` |
| independent decode of the battle tree's 3 modules | values as §4 |
| `b12_variants.py --check` | **exit 1, by design** — see §6 |

The first build attempt failed and was fixed at the cause, not around it: `t5_apply` keys its guard
on `old`/`new`, and the edit list had been written with `from`/`to` (that spelling belongs to
`t1_apply`'s validation list). The list was corrected and the battle tree rebuilt from scratch with
`--force`.

---

## 6. Why `b12_variants.py --check` is red, and what closes it

```
preconds : 1 decision reopened; 2 one row set; 3 swap UNKNOWN (U1); 4 --variant True, 2 variant-named tree(s)
FAIL: precondition(s) met, so the card is buildable and must not stay a todo: build surface
      (--variant registered: True; variant-named trees: 2)
```

That is the checker doing its job: on 2026-11-06 it was written to pass *only* while the card is
live **and unbuilt**, and to fail the moment a precondition is met. Precondition 4 is now met, so it
fails. It is not a defect in the build, and it is not fixed by weakening the assertion.

One correction was made in the checker: its tree scan was one level deep and reported **0**
variant-named trees while two existed in the `bm-RC4-modes/` container. It now also scans one level
inside a container, which is where the pair must live for the sibling `variant.json` the diff gate
reads. Everything else about that check is untouched.

What still holds the card open:

* **Precondition 3 — the runtime swap — is UNKNOWN (U1)** and cannot be derived from disk. The pair
  proves two value sets exist; it does not prove the game can switch between them.
* **Precondition 2** — `t11_variants.json` still declares **one** variant (`hybrid`, schema 1). Two
  row sets (schema 2) were not emitted; `b12_variant_battle.json` is the build's declaration, not the
  table's second row set.
* The card's register entry still reads `todo: D-2 reopened`, and D-2 remains reopened.

Closing it is a governance edit (card tag + tracker + schema-2 row set), not a build edit.

---

## 7. Limits and UNKNOWNs

| # | limit | settler |
|---|---|---|
| 1 | **nothing was launched.** No in-game swap, no rendering check, no drop-entry test | a test ban (U1), then V-01/V-02 per variant |
| 2 | the two trees share the internal entity name, so they are two payloads, not two coexisting entities | B-13 (name/hash, second drop item) + U1 |
| 3 | T-MD13's pose is not written | an `.epe` applier for `bm_build`, or a Gibbed fix for the parts module's inline-array decode (`NullReferenceException`, reproducible) |
| 4 | T-MD7's two slip scales and `DrivingForceZOffset` have no member | `VOCABULARY.md` has no such member; 52 module types searched |
| 5 | T-MD6's join is a composition, not a decode | a live probe that reads whether `official_top_speed` governs the battle envelope |
| 6 | the battle envelope's 3 curve points remain raw (unit undocumented) | BmAK CDO decode (`MODES.md` source offsets) |
| 7 | no `exact` carry exists for any row | this is a property of JC3's vocabulary, not of this build |

---

## 8. Revert

1. **Trees:** `rm -rf Builds/bm-RC4-modes` — nothing outside it was written; the pair is two
   directory trees plus their receipts, snapshots and generated installers.
2. **Scaffold:** revert `Tools/scripts/bm_build.py` — `--variant`, `VARIANT_NAMES`/`CARRY`,
   `load_variant()`, the `receipt.bm.variant`/`variant.json` write and the one receipt check. `Tools/`
   is untracked in git, so the pre-change form is the base build's receipt (B-12 absent from
   `bm.variant`) plus the docstring's old Usage block.
3. **Checker:** revert `b12_variants.py`'s `named_builds()` to the one-level scan (back to reporting
   0 trees).
4. **New files, delete:** `Tools/scripts/b12_variant_diff.py`,
   `Working/Translation/{b12_current,b12_battle_edits,b12_variant_pursuit,b12_variant_battle}.json`,
   `tmp/freebuff/reports/aafdiff-pursuit-battle.md`.
5. Nothing in `GRAB_BACKLOG.md`, `T_ROWS.jsonl`, `t11_variants.json` or any other build was changed
   by this pass, so no ledger reversal is needed.

---

## 9. Sources

* `tmp/freebuff/reports/apply-mode-switch-rows.md` §2–§5 — the closest system per row, the two-mode
  plan, the four preconditions this pass acts on.
* `tmp/freebuff/reports/mode-switch-carriers.md` §2.4, §2.7, §4 — no mode member; the boost as the
  only in-place change; U1.
* `Working/Translation/t11_variants.json` — the 15 rows and both halves.
* `Builds/bm-RC4-modes/{pursuit,battle}/receipt.json`, `variant.json`, `applied.json` — measured.
* `tmp/freebuff/reports/aafdiff-pursuit-battle.md` — the SHA-256 diff.
