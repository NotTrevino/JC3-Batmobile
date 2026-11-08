# Operator digest — closest-system plans and today's audits (2026-11-07)

Scope: every file in `tmp/freebuff/reports/` whose name contains **closest-system-plan** or starts with
**audit-**. Times are file mtimes (`date -r`, local). Counts are read from each audit's own claim table,
legend/definition rows excluded; where a report restates a row in a later section that is noted rather
than double-counted. **No plan was edited by any of these audits** — each is `Revert: delete this file`.

---

## 1. The plans (12 match the name pattern)

| modified | report | audited today |
|---|---|---|
| 2026-11-06 06:57 | `air-control-closest-system-plan.md` | yes (1) |
| 2026-11-06 07:04 | `ram-assist-closest-system-plan.md` | yes (7) |
| 2026-11-06 07:13 | `lock-hold-salvo-closest-system-plan.md` | yes (5) |
| 2026-11-06 07:15 | `paint-gaps-closest-system-plan.md` | yes (6) |
| 2026-11-06 09:04 | `review-closest-system-plans.md` | no |
| 2026-11-07 17:23 | `control-scheme-closest-system-plan.md` | **no** |
| 2026-11-07 17:26 | `emp-effects-closest-system-plan.md` | **no** |
| 2026-11-07 17:32 | `collision-missing-shapes-closest-system-plan.md` | **no** |
| 2026-11-07 17:36 | `mode-swap-trigger-closest-system-plan.md` | **no** (cited by 3 only) |
| 2026-11-07 17:46 | `hud-cluster-closest-system-plan.md` | yes (4) |
| 2026-11-07 18:17 | `boost-block-selector-closest-system-plan.md` | yes (2) |
| 2026-11-07 18:51 | `moving-parts-behaviour-gaps-closest-system-plan.md` | yes (2) |

Five of the twelve have no audit: `control-scheme`, `emp-effects`, `collision-missing-shapes`,
`mode-swap-trigger`, and the `review-` index itself.

**Four audited plans fall outside the pattern** — a name filter would miss them:
`collision-impact-effects-plan.md` (2026-11-06 10:28) and `mode-switch-carriers.md` (07:28) in audit 3;
`summon-drive-in-closest-system.md` (10:20) and `unranked-weapons-closest-system.md` (07:49) in audit 8.
Three carrier reports were also read as sources: `lock-hold-and-salvo-carrier.md` (07:20),
`carrier-ram-and-dodge.md` (03:56), `carrier-air-control.md` (03:53).

---

## 2. The audits (8), counts per label, worst finding

| # | audit (modified) | plan audited | MISMATCH | OVERSTATED | UNSUPPORTED | most serious single finding |
|---|---|---|---:|---:|---:|---|
| 1 | `audit-air-control-plan-numbers.md` 20:15 | `air-control-closest-system-plan.md` | 5 | 0 | 0 | the airborne window is printed **1.212 s** at `Research/BatmobileGrab/FOOTAGE.md:27` but the three samples give **1.211 s**, so D3 **9696** and D4 **14544** inherit a **−5.33** / **−8.0** error |
| 2 | `audit-boost-selector-and-moving-parts-plans.md` 20:24 | `boost-block-selector-`, `moving-parts-behaviour-gaps-` | 0 | 8 | 2 | the "shipped" boost row `grip 1.0 / 4.26 / 4.26`, `speed 43.2 / 100.92 / 100.92` is one module copy (`mode-switch-carriers.md:112-118`); the donor T-MD14b decoded carries **grip 2 / — / 1.5**, **speed 40 / 80 / 80** — so "Pursuit is unchanged" is false on that donor |
| 3 | `audit-collision-impact-and-mode-switch-plans.md` 20:19 | `collision-impact-effects-plan.md`, `mode-switch-carriers.md` | 3 | 8 (9 rows) | 11 (13 rows) | the `ImpactMaxDamagePow` row carries **0.666** twice, which is `BattleModeImpactMaxDamagePow`'s value at `Research/BatmobileGrab/DAMAGE_RULES.md:144`; the field's own line `:150` is **— / —** |
| 4 | `audit-hud-cluster-plan-against-movie-data.md` 20:20 | `hud-cluster-closest-system-plan.md` | 3 | 0 | 0 (11 UNSOURCED) | the damage-flash setter is **`part, amount, duration, frames`** at `Research/BatmobileGrab/HUD.md:174` (`HUD_SPEC.json:231`), not G3's `(part, x, y, frames)` the plan adopts |
| 5 | `audit-lock-hold-salvo-and-fire-leech.md` 20:18 | `lock-hold-salvo-closest-system-plan.md` | 0 | 3 | 3 | the **2.0 s** lock hold has no JC3 member: `Working/Translation/T_WP3B_LOCKON.md:163` — `AutoAimSettings` is 22 members, none a duration; `aim_timer_override` is 4.0 and not lock-gated |
| 6 | `audit-paint-plan-colour-numbers.md` 20:23 | `paint-gaps-`, `colour-bmak-wet-look.md` | 5 | 0 | 0 (3 UNSOURCED) | ch3 takes **0.5** from parent 767, but `Research/BatmobileGrab/COLOUR_PARAMS.md:37` gives **0.15** on 763 — the nearest-MIC rule the ch0 row uses yields F0 **0.0060**, not **0.0200** |
| 7 | `audit-ram-assist-plan-numbers.md` 20:14 | `ram-assist-closest-system-plan.md`, `carrier-ram-and-dodge.md` | 2 | 0 | 0 (1 UNSOURCED) | `KillFlipTorque` **−2,000,000** is the class default; the archetype ships **−200** and duration **0.5 s** at `Research/BatmobileGrab/DAMAGE_RULES.md:594`, so "57× short" and "2000× out of domain" describe a value the game does not ship |
| 8 | `audit-summon-and-unranked-weapon-plans.md` 20:16 | `summon-drive-in-closest-system.md`, `unranked-weapons-closest-system.md` | 2 | 3 | 5 | the plan's cannon muzzle **0.247, 0.485, −2.018** is `w603_mediumtank_mgun`'s row; the cannon's own `fire_position_0` is **0, 0.3739, −5.8174** at `Research/JC3Grab/WEAPON_WIRING.md:316` |
| | **totals (8 audits, 13 plan-sides)** | | **20** | **22** | **21** | + **23 UNSOURCED** rows under that fifth label |

Notes on the numbers, so they are not re-totalled wrongly later:
- The label vocabularies differ. Reports 1, 4, 5, 6, 7 also use **UNSOURCED** (23 rows: 2 / 11 / 6 / 3 / 1)
  for "the cited file does not carry it", which the other reports would call UNSUPPORTED; report 1 uses
  **PARTIAL** (2 rows: A7, C6) where the others would say OVERSTATED. Neither is in the 21 above.
- A row can carry two labels: audit 5's **L6** is both OVERSTATED and UNSUPPORTED; audit 3's rows 20 /
  M16 are the same **66 vs 67** claim in two sections; audit 8's **W9/W10** are MISMATCH *because stale*.
- Audit 3's raw grep is 9 OVERSTATED / 13 UNSUPPORTED; three of those are §4 restatements of M30, C28
  and C30.
- Audit 2's declared summary is "48 claims checked: **VERIFIED 38, OVERSTATED 8, UNSUPPORTED 2**", split
  22 boost rows (17/5/0) and 26 moving-parts rows (21/3/2). Audit 6's is "20 audited rows: **MATCH 12,
  MISMATCH 5, UNSOURCED 3**".

---

## 3. Where the failures cluster

Three shapes account for most of the 63 flagged rows: **(a) a number from the wrong copy or the wrong
field** (2 B6/B7, 3 C13, 6 ch3, 7 C1, 8 W3); **(b) an imported convention presented as decoded**
(1 A4, 4 `Cap` 65 frames, 5 L2/L6, 8 S6); **(c) a citation that does not resolve as written**
(3 M25/M30, 8 S9/W4/W5/W7). The mechanism claims themselves — offsets 120/132/144, 12 B blocks, all
five `PerformanceBoost` member offsets, every `P-01…P-15` row id, all four `AirControl*` offsets,
`missile_per_shot` @44, `aim_timer_override` @108 — are verified; what fails is provenance at the edges.

## 4. What this digest did not do

Corrections were **not applied**: every audit ends with a numbered list for the plan owner, every plan's
mtime in §1 predates the audits (latest plan 18:51, earliest audit 20:14), and each is as published (audit 6 C7 and audit 3 §5 remain open). No game, decode
or archive was opened here — figures are transcribed from the eight audit files.

Revert: delete this file.
