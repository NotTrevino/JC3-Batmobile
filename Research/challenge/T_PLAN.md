# Challenge — `Working/Translation/T_PLAN.md`

Scope: every claim in the target that is **assumed**, **inferred**, **carried by a member name
rather than a behaviour**, or **numerically unsourced**. The target is a 2026-10-23 snapshot; it is
read-only here, as are `GRAB_BACKLOG.md`, `POSTMORTEM_DAMAGE.md` and every other document.

Method: each claim was re-derived from the evidence on disk with
`python Tools/scripts/chase/challenge_t_plan.py` (read-only; prints one `[Cn]` line per claim), plus
targeted lookups of the class default objects in `Engine.upk` / `BmGame.upk` via
`Tools/scripts/upk_read.py`. No game was launched, nothing was committed, no file under
`D:\Games` was written.

**Summary: 26 claims examined — 11 CONFIRMED, 11 REFUTED, 3 UNVERIFIABLE, 1 confirmed-with-unsourced-input.**
The refutations are of two kinds: (a) the plan is a dated snapshot whose counts no longer match the
ledger, and (b) three "chain" provenance cells name a file that does not contain the field they
cite. The values in (b) are still right — they are class-default values — but the citation is wrong,
which under R4 makes the row's provenance unverified as written.

| # | claim (short) | class | verdict |
|---|---|---|---|
| 1 | 6,045 modules decoded, source `ENTITIES.md` | unsourced attribution | REFUTED |
| 2 | 128 rows = 105 ledger + 23 T6 | unsourced (stale) | REFUTED |
| 3 | 15 `out`, 113 in scope = 97 + 1 + 15 | unsourced (stale) | REFUTED |
| 4 | per-doc split T-1 49 / T-2b 39 / T-3 15 / T6 23 | unsourced (stale) | REFUTED |
| 5 | disposition counts 51/16/3/16/11/8 | unsourced (stale) | REFUTED |
| 6 | "0/112" behaviour-verified vs 113 in scope | unsourced denominator | REFUTED |
| 7 | 77 carried (sums to 113) vs 78 carried (sums to 114) | unsourced arithmetic | REFUTED |
| 8 | T-A1 frontal area "derived" from 3.5 × 2.27 = 7.9 | inferred | REFUTED |
| 9 | T-B2 43.2 km/h from 3500 / 600 × 2.0, "(chain)" | value derived, citation unsourced | CONFIRMED (value) / REFUTED (citation) |
| 10 | T-ST5 DriftCorrectionSteerSpeed 1.0 "(chain)" | citation unsourced | CONFIRMED (value) / REFUTED (citation) |
| 11 | T-ST5 SteeringSpeedReCentreMod 1.0 "(chain)" | citation unsourced | CONFIRMED (value) / REFUTED (citation) |
| 12 | "no `*grip*`/`*traction*` member anywhere" | name-only absence | REFUTED (scope) |
| 13 | "no `*Align*` member" | name-only absence | REFUTED (scope) |
| 14 | T-K1 disproof 4×300/(6000×0.683) = 0.29 m/s² | inferred input | CONFIRMED (arithmetic) / input unsourced |
| 15 | camera 85/95 horizontal → 55/63 vertical | derived | CONFIRMED |
| 16 | T-S3 30 + 40 = 0.70 m | derived | CONFIRMED |
| 17 | donor `min_time_to_block` = 1 | decoded | CONFIRMED |
| 18 | donor drift sensitivity = 4 | decoded | CONFIRMED |
| 19 | T-S5 build 0.2 vs donor 0.1 | decoded | CONFIRMED (value) / route misattributed |
| 20 | T-W1 = 261 of 423 fields | decoded | CONFIRMED |
| 21 | T-E5 assumed on wiki 336 | assumed (declared) | CONFIRMED (as declared) |
| 22 | live build = test-088 | read | UNVERIFIABLE here |
| 23 | G1 19,203 / 20,128 objects | decoded | CONFIRMED |
| 24 | 423 / 423 offset fields named | decoded | CONFIRMED |
| 25 | 81,952 / 81,953 entries named | decoded | CONFIRMED |
| 26 | 77,611 / 77,611 geometry blocks | decoded | CONFIRMED |

## 1 · `L48` — "vehicle modules decoded 6,045 / 6,045 — source `ENTITIES.md`"

**Class:** unsourced attribution. **Verdict: REFUTED (attribution), number CONFIRMED.**
`ENTITIES.md` does not contain 6,045 (it describes **232** decoded `.epe` graphs and their class
inventory). 6,045 appears in `Research/JC3Grab/README.md` (`.vmodc` modules = 6,045, 100%) and in
`G2X.md` (`PASS: 6045 modules in 232 caches …`). The number is right; the citation would send a
reader to a file that cannot prove it, which is exactly what R4 forbids.

## 2 · `L58` — "Row universe: 128 = 105 ledger rows + 23 T6 rows"

**Class:** unsourced (dated snapshot). **Verdict: REFUTED now.**
`t_rows.py` ledger is **198 rows** (T-11/T-13/T-14/T-15/T-17/T-20 added since), and
`T6_HUD_CAMERA.md` now carries **33** row ids (`T-HUD*`/`T-CAM*`). 105 + 23 = 128 was true on
2026-10-23; it is not a statement about today's ledger. Evidence: `[C1]` of the script.

## 3 · `L58-62` — "15 are `out` … 113 in scope = 97 evidenced + 1 assumed + 15 blocked"

**Class:** unsourced (dated snapshot). **Verdict: REFUTED now** (internally consistent: 97+1+15 = 113).
Current ledger: `out` **35**, `blocked` **14**, `next` **39**, `superseded` 7, `keep` 61, `edit` 16,
`epe` 26. `STATUS.md` now reports `rows assumed 1 / 181`. Evidence: `[C3]`.

## 4 · `L89` — "Per-document split … T-1 49, T-2b 39, T-3 15, T6 23"

**Class:** unsourced (dated snapshot). **Verdict: REFUTED now.**
Ledger docs: T-1 49, T-2b 39, **T-3 17**, T-7 14, T-13 17, T-14 28, T-15 15, T-20 19 (202 rows of
generated docs beyond the original two). Evidence: `[C2b]`.

## 5 · `L84-92` — disposition counts `keep 51 / edit 16 / next 3 / epe 16 / blocked 11 / out 8`

**Class:** unsourced (dated snapshot). **Verdict: REFUTED now.**
Current: keep 61, edit 16, next 39, epe 26, blocked 14, out 35, superseded 7. Evidence: `[C2]`.

## 6 · `L102` and `L441` — "behaviour proof **0/112** complete today"

**Class:** unsourced denominator. **Verdict: REFUTED.**
The plan says 113 rows are in scope in the same document (`L58`, `L377`) and never names the row it
drops to reach 112. Either the denominator is 113 (and one row was silently excluded) or one row is
not in scope (and the "113" statements are wrong). Evidence: `[C13]`.

## 7 · `L377` vs `L412` — "16 built + 4 queued + 1 assumed + 15 blocked + 77 carried = 113" vs
"+15 out = 128 total rows … 78 carried"

**Class:** unsourced arithmetic. **Verdict: REFUTED (internal).**
16+4+1+15+77 = 113 ✓, but 16+4+1+15+**78** = **114**, and §7's own tree says "78 carried
(keep + epe + 12 T6)". So §7 disagrees with §5 by three rows in two places (the 77/78 and the
12-T6-versus-16-epe split). Evidence: `[C12]`.

## 8 · `L174` — T-A1 `land_aerodynamics.frontal_area` **6.63**, settle route "derive from the mesh
cross-section (3.5 × 2.27 = 7.9 m²)"

**Class:** inferred (a derivation that does not produce the value). **Verdict: REFUTED as described.**
3.5 × 2.27 = **7.95 m²**, not 6.63, and the row itself (`T1_TRANSLATION.md` L170) keeps 6.63 as a
**`class`** value ("inside the heavy-class band … IQR 4 … 6.72, median 6.5") — it never claims the
mesh derivation. So the ledger is honest and the *plan's* Batch-C cell misdescribes what was done:
the value is a class-median pick, not a derivation, and calling the row "derived row" overstates it.
Evidence: `[C6]`, `T1_TRANSLATION.md` L166/L170.

## 9 · `L241` — T-B2 `43.2 km/h` = `min(FakeExtraSpeedMax 3500, FakeExtaSpeedAccel 600 ×
BoostDuration 2.0)`, provenance **"(chain)"**

**Class:** citation unsourced (value derived). **Verdict: CONFIRMED (value), REFUTED (citation).**
`CHAIN.json` contains **none** of `FakeExtraSpeedMax`, `FakeExtaSpeedAccel`, `BoostDuration`
(`[C8]`). The three values are class-default-object fields, re-read for this challenge:
`BmGame.upk Default__RVehicleBatmobileBase` 0x1bf4 = **3500.0**, 0x1bf8 = **600.0**;
`Default__RVehicleSimBatmobile` 0x298 = **2.0** (`[C10]`). Arithmetic ✓: 1200 cu = 12 m/s =
43.2 km/h (`[C7]`). The cell's provenance word must be `decoded` (class default), not "(chain)".
