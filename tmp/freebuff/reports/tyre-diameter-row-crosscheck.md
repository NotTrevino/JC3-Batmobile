# DIM-2's tyre range against the G1-18 measurements in TYRES.md

Card: 8824-tyre-diameter-row-crosscheck. 2026-11-08.

**Answer.** `GRAB_BACKLOG.md:143` (DIM-2) states the tyre diameter as "PSKX **1.365–1.366 m**
measured on all four tyres". `Research/BatmobileGrab/TYRES.md` records **three** diameters per tyre —
tread (y), through-the-axle (z) and **max radial, which the page itself calls the shoulder**. The
1.365–1.366 range **covers every tread value (4 of 4)** and **covers no shoulder value (0 of 4)**:
the shoulders read **1.3711–1.3714 m**, i.e. **5.1–5.4 mm above** the range's top. The inside-the-range
claim is therefore true only for the tread column, and the row's range is **narrower than the grab**
for the shoulder (and for the z diameter, which also falls outside). The 2.4% distance to the 1.40 m
reference is also wrong: TYRES.md computes **2.5%** from the tread (`TYRES.md:156`).

Citation legend: **BACKLOG** = `GRAB_BACKLOG.md`; **TYRES** = `Research/BatmobileGrab/TYRES.md`.

## 1. Every diameter TYRES.md records, per tyre

Header of the source table, `TYRES:14–16`: "`| corner | tyre faces (*_Vis) | verts | Ø tread (y) | Ø (z) |
Ø max radial | width (x) |`". The fifth column is the shoulder — confirmed by the page's own second
table, `TYRES:105`: "`| corner | tread Ø (y) | Ø max radial (shoulder) | bulge |`".

**Tread (y):**

| corner | tread Ø | quoted line |
|---|---:|---|
| f_l | **1.3652** | `TYRES:17` `| f_l | 6,700 | 6,485 | **1.3652** | 1.3672 | 1.3711 | 0.7314 |` |
| f_r | **1.3657** | `TYRES:18` `| f_r | 6,700 | 6,490 | **1.3657** | 1.3674 | 1.3714 | 0.7325 |` |
| r_l | **1.3654** | `TYRES:19` `| r_l | 7,564 | 7,432 | **1.3654** | 1.3673 | 1.3712 | 0.7318 |` |
| r_r | **1.3652** | `TYRES:20` `| r_r | 7,564 | 7,440 | **1.3652** | 1.3673 | 1.3711 | 0.7315 |` |

Summary line: `TYRES:29` "`All four tyres are the same mould to **0.5 mm** (tread Ø 1.3652–1.3657,
shoulder Ø 1.3711–1.3714,`".

**Shoulder (Ø max radial):**

| corner | shoulder Ø | quoted line |
|---|---:|---|
| f_l | **1.3711** | `TYRES:17` (column 5) and `TYRES:107` `| f_l | 1.3652 | 1.3711 | 5.9 mm |` |
| f_r | **1.3714** | `TYRES:18` and `TYRES:108` `| f_r | 1.3657 | 1.3714 | 5.7 mm |` |
| r_l | **1.3712** | `TYRES:19` and `TYRES:109` `| r_l | 1.3654 | 1.3712 | 5.8 mm |` |
| r_r | **1.3711** | `TYRES:20` and `TYRES:110` `| r_r | 1.3652 | 1.3711 | 5.9 mm |` |

Summary: `TYRES:116` "`three headline numbers is "the bulge number" — that number is 1.3714.`" and
`TYRES:149` "`the tyre reads Ø1.3652–1.3657 tread-to-tread and Ø1.3711–1.3714 including the
shoulder`".

**Through-the-axle (z)** — not a "shoulder" but recorded, and relevant to the range claim:
1.3672 (f_l, `TYRES:17`), 1.3674 (f_r, `TYRES:18`), 1.3673 (r_l, `TYRES:19`), 1.3673 (r_r,
`TYRES:20`).

## 2. Does DIM-2's 1.365–1.366 cover every measured value?

DIM-2's stated range, verbatim (`BACKLOG:143`):

> `| DIM-2 | Tyre diameter matches the lore reference | PSKX **1.365–1.366 m** measured on all four tyres (`TYRES.md`, T-G2) vs wiki 1.40 → 2.4% apart, **accepted**; ...`

| measurement | values | inside 1.365–1.366? | verdict |
|---|---|---|---|
| tread Ø (y) | 1.3652, 1.3657, 1.3654, 1.3652 | **yes — 4 of 4** (max 1.3657) | **covered**; the brief's range rounds these correctly |
| shoulder Ø (max radial) | 1.3711, 1.3714, 1.3712, 1.3711 | **no — 0 of 4**; overshoot 5.1 mm (1.3711) to 5.4 mm (1.3714) above 1.366, or 6.1–6.4 mm above 1.365 | **not covered** — the range is **too narrow** for the shoulder |
| Ø through the axle (z) | 1.3672, 1.3674, 1.3673, 1.3673 | **no — 0 of 4**; overshoot 1.2–1.4 mm above 1.366 | **not covered** — too narrow for the z measure too |

**Which the grab supports:** TYRES.md supports "**1.3652–1.3657 m tread** on all four tyres", not
"1.365–1.366 m diameter" unqualified. Its own headline is the two-number form,
`TYRES:29`: "tread Ø 1.3652–1.3657, shoulder Ø 1.3711–1.3714". A reader of DIM-2 alone would conclude
the whole tyre is inside 1.366, which the grab contradicts for the shoulder by more than 5 mm — and
D-1's whole resolution turns on exactly that gap (`TYRES:102–116`, "the 1.366 **does** exclude the
sidewall bulge").

**Second defect, same row:** "vs wiki 1.40 → **2.4%** apart" disagrees with the grab's arithmetic.
`TYRES:113–114`: "`Reaching 1.40 from the shoulder (Ø 1.3714) needs ×1.021 (+2.1%); from the tread
(Ø 1.3654) it needs ×1.025 (+2.5%)`", and `TYRES:156`: "`reference, 2.5% apart, accepted`". Derived:
(1.40 − 1.3654) / 1.3654 = 2.53% → **2.5%**. The 2.4% happens to be what the **z** diameter gives,
(1.40 − 1.3673) / 1.3673 = 2.39% — consistent with the range having been written off the z column.

## 3. The G1-18 rows already agree with the grab

The brief pairs DIM-2 with G1-18, so for contrast: G1-18 cites both numbers and matches TYRES.md
exactly, which is why the DIM-2 row stands out.

| G1-18 citation | quoted line | matches TYRES.md? |
|---|---|---|
| tread / shoulder / width, all four tyres | `BACKLOG:1825` "`all four tyres Ø1.3652–1.3657 tread / Ø1.3711–1.3714 shoulder / 0.7314–0.7325 wide`" | **yes** — `TYRES:29`, `TYRES:17-20` |
| D-1 input line | `BACKLOG:1795` "`tread Ø1.3652–1.3657, shoulder Ø1.371, all four wheels within 0.5 mm`" | **yes** (shoulder rounded to 1.371) |
| bulge / shortfall in that same D-1 cell | `BACKLOG:1795` "`the bulge is 5.5 mm … still 2.0% short`" | **no** — `TYRES:112` says bulge "**5.7–5.9 mm**" and `TYRES:115` says "still **2.1%** short". A second, smaller discrepancy, outside DIM-2 but in the same evidence chain, and not what this card was asked to fix. |

## 4. Proposed corrected DIM-2 wording (not applied)

`GRAB_BACKLOG.md` is **not edited** — the card says not to, and this section is the proposal only.

Replacement for the DIM-2 row's measured-value cell (`BACKLOG:143`):

> PSKX **tread Ø 1.3652–1.3657 m** on all four tyres (Ø 1.3672–1.3674 through the axle; **Ø 1.3711–1.3714
> including the shoulder**) (`TYRES.md`, T-G2) vs wiki 1.40 → **tread 2.5% apart, shoulder 2.1% apart**,
> **accepted**; the single-figure range 1.365–1.366 covers the **tread only**, not the shoulder. The
> docstring's 1.42 has no source and what it measured is UNKNOWN (`TYRES.md` §3) (D-1 resolved: keep
> the PSKX)

Full row, as it would read:

> `| DIM-2 | Tyre diameter matches the lore reference | PSKX tread Ø **1.3652–1.3657 m** on all four tyres (Ø 1.3672–1.3674 through the axle; Ø **1.3711–1.3714 including the shoulder**) (`TYRES.md`, T-G2) vs wiki 1.40 → tread 2.5% apart, shoulder 2.1% apart, **accepted**; the 1.365–1.366 range covers the tread only (D-1 resolved: keep the PSKX) | \`land_global.*_wheels.radius\`, wheel RBMs |`

Why this wording: it keeps the row's decision (**accepted**) and its job (a dimension gate against the
lore reference), states the two diameters the grab actually measures, and makes the shoulder gap
explicit rather than implying a single 1.365–1.366 tyre. Optional one-line variant if brevity matters:

> PSKX **tread Ø 1.3652–1.3657 m** (shoulder Ø **1.3711–1.3714**) on all four tyres vs wiki 1.40 →
> tread 2.5% / shoulder 2.1% apart, **accepted**; 1.365–1.366 is the tread range only.

## 5. Checks run

| check | result |
|---|---|
| tread values read | 4 of 4, `TYRES:17-20`, min 1.3652 / max 1.3657 |
| shoulder values read | 4 of 4, `TYRES:17-20` + `TYRES:107-110`, min 1.3711 / max 1.3714 |
| z values read | 4 of 4, `TYRES:17-20`, min 1.3672 / max 1.3674 |
| DIM-2 range vs tread | 4/4 inside |
| DIM-2 range vs shoulder | 0/4 inside; 5.1–5.4 mm above 1.366 |
| DIM-2 range vs z | 0/4 inside; 1.2–1.4 mm above 1.366 |
| 2.4% claim | **differs** from `TYRES:114`/`:156` (2.5% from tread, 2.1% from shoulder); 2.39% matches the z diameter |
| G1-18 vs grab | values match (`BACKLOG:1795`, `:1825`); D-1 cell's 5.5 mm / 2.0% do not (grab: 5.7–5.9 mm / 2.1%) |
| `GRAB_BACKLOG.md` edited | **no** — read only |
| game launched / anything built | **no** — file reads only; nothing written outside this page |

## 6. UNKNOWNs

1. **Which diameter DIM-2's "1.365–1.366" was intended to name.** The row says "diameter" without a
   column. The tread reading is the only one it fits, and the 2.4% figure fits the z column, so the row
   may have mixed two measures. No file records the intent; the corrected wording above removes the
   ambiguity without needing it.
2. **Whether the shoulder belongs in a "tyre diameter" gate at all.** D-1 treats 1.3714 as the
   authoritative bulge number (`TYRES:116`) and 1.40 as a wiki estimate, but no card states whether
   DIM-2 is a tread gate or an overall-envelope gate. This page reports both and recommends stating
   both in the row rather than choosing.
3. **The D-1 cell's 5.5 mm bulge.** `BACKLOG:1795` disagrees with `TYRES:112`'s 5.7–5.9 mm; whether
   that cell or the page is stale is not settled here (out of the card's scope, flagged only).
