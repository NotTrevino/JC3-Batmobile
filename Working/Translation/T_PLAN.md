# T_PLAN — the translation plan, mapped completely before execution

> **2026-10-24: the single backlog is now [GRAB_BACKLOG.md](../../GRAB_BACKLOG.md) (unified).** This file is kept as history and evidence; for *what to do next*, follow the unified backlog.

**Status:** written 2026-10-23, no build, no install, no value changed. This is the map the
translation runs against so that once it starts, improvisation is confined to §9 and nowhere else.

**Sources of every number below** (none is asserted from memory):

| claim family | source |
|---|---|
| row counts, dispositions, per-doc splits | `Working/Translation/T_ROWS.jsonl` + `T6_HUD_CAMERA.md`, counted by `Tools/scripts/status_audit.py` |
| G1/G2 coverage percentages | `STATUS.md` (generated; `status_audit.py --check`) |
| what test-085 carries | `Working/Translation/t1_edits.json` (35 edits / 16 rows), `T5_BUILD.md` |
| queued batch values | `T3_COVERAGE.md` §4 |
| fleet numbers behind class rows | `T3_FLEET.md` (`t3_fleet.py --check`), `FITS.md` |
| QA-1 measurements | `Working/Translation/QA1_RESULTS.md` |
| live build | `install.ps1 -Action Status` run 2026-10-23 **twice**: the first reading was `.ee` `10B14A60…D9F74E23` (test-087) against `.toc` `4FD6DB3C…C88541A0` — the postmortem's rollback had never run; restored to test-085 (`D9C4AAD3…8BB7FC2`), then **test-088** installed from Batch B2 (`5A79D885…6F7860` / `4FD6DB3C…C88541A0`, both == its receipt). `verify_install.py` 9/9 on both |

---

## 0. The no-guesswork contract

1. **Provenance.** Every value in a build must carry one of the evidenced classes from the
   ledger: `decoded`, `decoded (fleet)`, `derived`, `class`, `epe`, `read`. A row whose class is
   `assumed` is **not buildable** until its settle route (§4C) has run and the ledger class has
   been re-decided. That is what "we grabbed both ahead of time" buys: the BmAK side (G1) and the
   JC3 side (G2) are both complete, so no value needs to come from taste.
2. **Batch-before-build.** No pack/install until the batch table for it exists in §4 with: exact
   module + member, the `old` value read from the *live* build, the `new` value with its source,
   and the pass criterion from §5. Anything discovered mid-batch goes to the **next** batch.
3. **Approval.** Staged builds are the default; installing into the live dropzone needs explicit
   approval (plan §1.1.4). This plan does not install anything.
4. **Counts are generated.** `STATUS.md` is regenerated, never hand-edited; this plan must agree
   with it (cross-check in §11) and is corrected when it does not.
5. **Improvisation is declared, not avoided by vibes** — see §9 for the only places it can occur
   and the rule that governs each.

---

## 1. Where translation stands (verified 2026-10-23)

| workstream | metric | count | % | source |
|---|---|---:|---:|---|
| G1 BmAK | objects decoded | 19,203 / 20,128 | 95.4% | `grab.json` |
| G1 BmAK | offset fields named | 423 / 423 | 100% | `OFFSETS.json` |
| G2 JC3 | archive entries named | 81,952 / 81,953 | 99.999% | `INDEX.json` |
| G2 JC3 | vehicle modules decoded | 6,045 / 6,045 | 100% | `ENTITIES.md` |
| G2 JC3 | geometry blocks decoded | 77,611 / 77,611 | 100% | `GEOMETRY.md` |
| T translate | in-scope rows evidenced | 97 / 113 | 85.8% | `T_ROWS.jsonl` + T6 |
| T translate | assumed / blocked / out | 1 / 15 / 15 | — | same |
| T translate | queued (built, take pending) | 3 rows / 4 values (test-088) | — | `dispo = next`, §4 Batch B2 |
| T translate | built and file-verified | 16 rows / 35 values (test-085) + 3 rows / 4 values (test-088) | — | `t5_measure.py` 35/35 + 4/4 |
| T translate | test-087 | **withdrawn** — damage rows inverted the source behaviour | — | `POSTMORTEM_DAMAGE.md` |
| T translate | fully behaviour-verified | 0 / 113 | 0% | no drive covers a row end to end |
| QA-1 | manoeuvre takes run | 1 (take 1) | — | `QA1_RESULTS.md` |

**Row universe: 128 = 105 ledger rows + 23 T6 rows.** 15 are `out` (JC3 has no system for them)
and are excluded from every denominator; **113 in scope** = 97 evidenced + 1 assumed (signed off) +
15 blocked. The 86/12 split was settled by the Batch-C pass (§4C) on 2026-10-23; T-DM7 moved to
`out` (outgoing ram damage) and T-DM9 added as blocked after test-087.

**Live build: test-088** — Batch B2's four values, installed 2026-10-23 on top of test-085's 35,
so the live pair carries both (4/4 and 35/35 read back). The deploy test that day found the
dropzone was still holding **test-087's** `.ee`: the postmortem's rollback had never run (§sources).
`T5_BUILD.md` is the build record.

**QA-1 take 1** measured: 0–100 km/h 16.4 s / 257 m (T-M1), peak 138 km/h (T-E1), first shift
knee 67 km/h = computed 66.8 (T-E4 partial), braking 3.5–3.8 m/s² (T-K1 partial). Everything
else in §5 is open.

---

## 2. Row schema and dispositions (so the rest of this file is readable)

Each `T_ROWS.jsonl` row carries
`cells = [id, BmAK source, JC3 target, transform, now, proposed, confidence, verify]`,
plus `doc` (T-1 / T-2b / T-3), `section`, `dispo`, `edits` (values in test-085), `why`.

| dispo | meaning | ledger count |
|---|---|---:|
| `keep` | build already carries the proposed value; nothing to edit | 51 |
| `edit` | value was edited in test-085 (file-verified; behaviour open) | 16 |
| `next` | resolved and **queued** for the next build | 3 |
| `epe` | carried by the entity graph (parts/lights/effects), not a module value | 16 |
| `blocked` | no value can be written yet; blocker and route named | 11 (+4 in T6) |
| `out` | JC3 has no system; excluded, counted for completeness | 8 (+7 in T6) |

Per-document split (must equal `STATUS.md`): T-1 49 rows, T-2b 39, T-3 15, T6 23.

---

## 3. Stage model — every row travels S0 → S6

| stage | what happens | input | output | gate (must pass to leave the stage) |
|---|---|---|---|---|
| **S0** evidence capture | G1/G2 grabs read the shipped files | game archives/packages | `Research/*`, `VOCABULARY.md`, `T3_FLEET.md`, `FITS.md` | `grab_model.py check`, `jc3index.py check`, `jc3fx.py check`, `jc3hkx.py check --all` — **closed for all rows** |
| **S1** row decision | a row exists with source → target → transform → confidence → verify | S0 evidence | a `T_ROWS.jsonl` row (or T6 table row) | row count reconciles in `status_audit.py --write`; 126 rows, 0 `other` — **done** |
| **S2** value derivation | the `proposed` value is produced by script or class rule | fleet tables, fits, decoded constants | evidenced class on the row | `t3_fleet.py --check`, `bmak_coverage.py --check`; 86 done, 12 assumed pending (§4C) |
| **S3** batch staging | exact `old → new` per member, written before building | §4 batch table | edits JSON checked against table + live build | `t1_apply.py` (every `old` equals the live build; every member exists) |
| **S4** build, install, file proof | pack, install (on approval), read back like the engine | edits JSON + base build | new test-0xx build | `t5_apply.py` (35/35 + 0 collateral), `t5_build.py` (aafdiff + `.toc` records), `verify_install.py` 9/9, `t5_measure.py` per-row read-back |
| **S5** behaviour proof | the prescribed manoeuvre from §5, one instrument, one take | installed build + take | measurement / screenshot, pass or fail | the pass criterion named on the row; **0/112 complete today** |
| **S6** journal + audit | append MODLOG, regenerate STATUS, update this plan | results | append-only record | `status_audit.py --check` green |

**A row is "translated" only at S5.** S4 proves bytes; S5 proves behaviour. `STATUS.md` keeps
these separate (`rows fully behaviour-verified = 0`) and so does this plan.

---

## 4. Batches — the executable backlog, in order

No batch other than A exists yet as buildable data; B–G are *specified* here so execution does
not have to invent anything.

### Batch A — test-085 (done, S4 complete)

35 values / 16 rows over 10 modules, all read back through the installed `.toc` (35/35),
`verify_install` 9/9, stations 4/4 (`T5_BUILD.md` §1–2). Rows: T-G5, T-M1, T-M2, T-M4, T-S1,
T-S2, T-R1, T-ST1, T-E1, T-E3, T-E4, T-A2, T-A4, T-K1, T-AU4, T-DM2.
Their S5 cells: measured 2 (T-M1, T-E1), partial 2 (T-E4, T-K1), open 12.

### Batch B — test-087: **withdrawn after the drive** (2026-10-23)

The nine-value build was installed and driven. It is a failed test, and the failure is in the row,
not in the tuning: `T-DM7` translated the Batmobile's ram **attack** as JC3 collision **defence**, and
`impact_damage_factor 0 → 1` turned ramming damage on. The full chain is in
`POSTMORTEM_DAMAGE.md`; the live build rolls back to test-085.

What the nine values were, kept as the audit trail:

| # | module.member | old (live 085) | new (087) | row | verdict |
|---|---|---|---|---|---|
| 1 | `vehicledamage.impact_damage_factor` | 0 | 1.0 | T-DM7 | **withdrawn** — direction error (now T-DM8, keep 0) |
| 2 | `vehicledamage.impact_armor` | 5000 | 5.0 | T-DM7 | **withdrawn** — removed a misrecorded cap |
| 3 | `vehicledamage.deform_scale` | 0 | 1.0 | T-DM6 | **withdrawn** — cosmetic switch stays off |
| 4 | `custom_land_global.arcade.nitro_boost.grip_multiplier` | 5.68 | 2.0 | T-B3 | staged, not cleared |
| 5 | `land_steering.countersteer_speed_factor` | 2.0 | 3.0 | T-ST5 | staged, not cleared |
| 6 | `land_steering.steer_in_speed_factor` | 1.5 | 2.0 | T-ST5 | staged, not cleared |
| 7 | `brakes.front.min_time_to_block` | 5 | 1.0 | T-K2 | staged, not cleared |
| 8 | `brakes.rear.min_time_to_block` | 5 | 1.0 | T-K2 | staged, not cleared |
| 9 | `custom_land_global.arcade.nitro_boost.extra_top_speed` | 50.46 | 40.0 | T-B2 | staged, not cleared |

- The six surviving values were re-staged in `t5c_edits.json` as `class` medians. **Batch B2
  (below) re-sourced them behaviour-first on 2026-10-23**: four values were rebuilt on the donor's
  shipped values and T-ST5's two were withdrawn (rule R1/R2). `t5b_edits.json` is marked withdrawn
  so nobody rebuilds test-087.
- **Why the offline proof did not catch it:** every gate (9/9 apply, 9/9 read-back, 505 `.toc`
  records) proves the bytes. The behaviour cell said "ram a wall: damage taken", which is the
  opposite of the source, and no take had ever established the immunity baseline the change
  silently deleted.
- **Explicitly not in this batch:** anything `assumed`, anything blocked, the withdrawn camera
  values, and any row whose `old` value differs from the live build (t1_apply fails → stop).

### Batch C — assumption clearing (executed 2026-10-23: 11 settled, 1 signed off)

**Outcome.** 11 rows were re-decided against generated fleet evidence and their ledger class is now
`decoded`/`derived`/`class`; **T-E5 stays `assumed` with a written sign-off** (its 209 mph target is
a wiki figure — the mod's stated lore goal, requirement 1 — with no file source; file-side it is
inside the shipped domain 25…350). The pass also found and fixed **three false "keep" claims**
(the ledger said the donor ships `min_time_to_block` 5 — it ships 1; it called T-S5 "unchanged by
the project" — the build holds 0.2 vs the donor's 0.1; the T-3 audit called drift sensitivity 2 —
the donor ships 4), and it promoted **two more unattributed build values into Batch B** (T-K2,
T-B2). Each row below records the route that was executed; the table is kept as the audit trail.

| row | member | kept value | settle route | output |
|---|---|---|---|---|
| T-S5 | `suspension.*.lateral_tire_force_offset` | 0.2 | fleet stat from `VOCABULARY.md` (front med 0.2, n=167; `land_suspension` med 0.4, n=19) | ledger class → `class`, or queued correction |
| T-ST3 | `land_steering.max_speed_t_to_full_steer_s` | 0.6 s | fleet stat (`land_steering` med 0.4, n=252 with sentinel −1) | same |
| T-ST4 | `steer_input_power_pc/durango/orbis` | 3 / 3 / 3 | `T3_FLEET.md` already carries all three (med 2 / 3 / 2) | same |
| T-ST6 | `wheel_drift_aligning_strength` | 0.3 | `T3_FLEET.md` `steering drift aligning` (med 0.5, band 0.5…0.5) | same |
| T-K2 | `brakes.*.min_time_to_block` | 5 | `T3_FLEET.md` (med −1 / 1; armored transport 1) | same |
| T-B2 | `arcade.nitro_boost.extra_top_speed` | 50.46 | fleet stat + BmAK boost-band note in the row | same |
| T-E5 | `vehicle_misc.official_top_speed` | 336 (wiki) | written decision: wiki 209 mph is the only target; cite fleet band (med 150, max 350) | signed-off row |
| T-A1 | `land_aerodynamics.frontal_area` | 6.63 | derive from the mesh cross-section (3.5 × 2.27 = 7.9 m²) and cite `FITS.md` (fit 4.92 describes other cars) | derived row |
| T-B4 | `arcade.heat_boost.*`, `turbo_jump*` | Serpente defaults | written keep: no BmAK source, Batmobile has no jump/heat boost | signed-off row |
| T-MA5 | `Window` block tint/opacity | opacity 1.0 | noon screenshot gate (§5.B): canopy reads as glass | measured row |
| T-MA7 | `Palette.tints[]` (10 tints) | leave | written design decision (shrinking it fights the game) | signed-off row |
| T-DR1 | `custom_land_global.drift.*` | 45° / 20° / sens 4 | written class decision (deliberate outliers vs 6 t medians) + drift manoeuvre (§5.A7) | signed-off row |

**Rule:** after this batch, `status_audit.py` must show `rows assumed = 0`; every former
assumed row is either evidenced or explicitly signed off with its reason in `why`.

### Batch B2 — the staged values, re-sourced behaviour-first (executed 2026-10-23)

**Rule R1 applied before anything was packed.** Every staged value had to name (a) the BmAK
behaviour behind it, or prove that none exists, (b) the JC3 mechanism and its shipped domain, and
(c) the take that can fail. Two of test-087's six survivors failed that test and were withdrawn;
the four that remain are sourced to the **donor's shipped values** (`decoded`), not to a fleet
median, because R2 forbids a median on a row that carries a behaviour.

| # | module.member | old (live 085) | new | source | BmAK behaviour behind it | take → pass | row |
|---|---|---:|---:|---|---|---|---|
| 1 | `arcade.nitro_boost.grip_multiplier` | 5.68 | **2.0** | `decoded` (donor; fleet domain 1.2 … 2) | **none** — no grip or traction member under boost exists in the streams; the boost evidence is `BoostTorqueVSpeedCurve`, which is torque | **A9** 0–100 with and without boost: boost improves 0–100, no grip snap on engage | T-B3 |
| 2 | `arcade.nitro_boost.extra_top_speed` | 50.46 | **40** | `decoded` (donor; domain 30 … 60) | boost extends the torque band **2100 → 3000 cm/s** at the same torque floor (75.6 → 108 km/h, **+32.4 km/h**, ×1.30 → ×2.10) — a bound, not a number | **A2** airfield run, boost off then on: terminal speed rises while boosting, delta recorded | T-B2 |
| 3 | `brakes.front.min_time_to_block` | 5 | **1** | `decoded` (donor; land IQR −1 … 1) | **none** — no brake-lock member and no anti-lock behaviour (`MaxBrakeTorque`, `EbrakeTime`, `EBrakeBrakeForce`, `Handbrake*`, `BlockThrottleUntilReleased` only) | **A5** braking 100 → 0 on tarmac: ≤ ~100 m, no lock-up | T-K2 |
| 4 | `brakes.rear.min_time_to_block` | 5 | **1** | same | same | **A5** | T-K2 |
| ✗ | `land_steering.countersteer_speed_factor` | 2.0 | *withdrawn* | — | BmAK gives the **rate** (`SteerSpeed` 220 °/s, `SteerSpeedVsSpeedCurve` 720 °/s flat → T-ST7) and the drift pair (`LatSlipFactor` 1.6, `HandbrakeLatSlipFactor`), no countersteer gain | **A7** drift release: angle holds, no snap-back, countersteer catches | T-ST5 |
| ✗ | `land_steering.steer_in_speed_factor` | 1.5 | *withdrawn* | — | same | **A7** | T-ST5 |

**Superseded by Batch B3 below (same day).** Rows 1–4 were re-sourced from the grab itself
(`CHAIN.json`) once `bmak_chain.py` bound SDK layout names to the cooked values, and T-ST5's two
withdrawn rows are un-withdrawn with BmAK's own 1.0 / 1.0. The table stays as the record of what
Batch B2 decided.

**Why T-ST5 was withdrawn** *(B2's reasoning at the time — B3 revisits it)*. Its proposed 3.0 / 2.0 was a 6 t fleet median on a row whose own
`verify` cell is a behaviour, and BmAK supplies no countersteer gain to translate — exactly what
R2 forbids. The build's 2.0 / 1.5 **is the donor's shipped pair** (`VOCABULARY.md` donor column),
so the row became a `keep` with a named origin (R5) and its gate A7 runs against the live build,
needing no build of its own. If A7 fails, the escalation is T-ST7's rate argument, not a gain vote.

**The two defects this pass found.** 5.68 sat outside *every* shipped range for
`nitro_boost.grip_multiplier`, and 5 had no source (Batch C had already disproved "vanilla Serpente
= 5"). Neither is a translation: both are now the shipped value of the chassis being converted.

**Status:** four values staged with behaviour and take named → cleared for packing under §0.2.
Rows stay `next` until their take passes (R4). `t5c_edits.json` carries `behaviour` and `take`
per edit, plus a `withdrawn` list so T-ST5's audit trail is not lost.

**The staging gate reads a snapshot, not the dropzone.** `t1_apply.py` compares `old` against
`current.json`, which is a decode of the **base the batch was written from** — for the original 35
that is test-083, so Batch B2 got its own: `t1_current.py Builds/test-085/aaf -o
t5c_current.json`, then `t1_apply.py --edits t5c_edits.json --current t5c_current.json` → **4/4**.
The control is the point: the 35-edit list pointed at that same snapshot **fails** (T-K1 expects
10000, the snapshot holds 5000 …), so the gate discriminates builds instead of passing vacuously.
A future batch regenerates its own snapshot from its own base; `current.json` is never rewritten
for a batch that is already built.

### Batch B3 — the staged values re-sourced from the grab itself (executed 2026-10-23)

**What changed.** `bmak_chain.py` joins the BmSDK layout names onto every cooked value the grab
holds and writes `Research/BatmobileGrab/CHAIN.json` (cross-check vs `OFFSETS.json`: 336 named
values, 0 disagreements; `bmak_chain.py --check` re-derives it). Four staged rows had claimed
BmAK carries no member for their quantity; the chain shows three of them do. Batch B2's donor
values are superseded by BmAK-derived numbers, T-ST5 is un-withdrawn, and every row still names
the take that can fail (R1) with its out-of-domain position declared (R3).

| # | module.member | old (test-088) | new | source | the BmAK value it comes from | take → pass | row |
|---|---|---:|---:|---|---|---|---|
| 1 | `land_steering.countersteer_speed_factor` | 2.0 | **1.0** | `decoded` (chain) | `DriftCorrectionSteerSpeed` **1.0** — drift correction at base steering rate; `DriftSteeringAssist`/`DriftSteeringBias` absent → false / 0. **R3**: below shipped 1.5 … 20 (n=252) | **A7** drift release: angle holds, no snap-back | T-ST5 |
| 2 | `land_steering.steer_in_speed_factor` | 1.5 | **1.0** | `decoded` (chain, kind-match) | `SteeringSpeedReCentreMod` **1.0** — the chain's only other steering-rate modifier (documented as a kind-match, not proven). **R3**: below shipped 1.2 … 10 | **A7** | T-ST5 |
| 3 | `arcade.nitro_boost.extra_top_speed` | 40 | **43.2** | `derived` (chain) | min(`FakeExtraSpeedMax` 3500, `FakeExtaSpeedAccel` 600 × `BoostDuration` 2.0) = 1200 cu = **43.2 km/h**; `InfiniteBoost` false (bit 29 clear). In-domain 30 … 60 | **A2** top-speed delta, boost off then on | T-B2 |
| 4 | `arcade.nitro_boost.grip_multiplier` | 2.0 | **1.0** | `derived` (absence proof) | no `*grip*`/`*traction*` member anywhere (G1-1 423/423 named + chain grep) → identity. **R3**: below shipped 1.2 … 2 | **A9** 0–100 with and without boost | T-B3 |
| — | `brakes.front/rear.min_time_to_block` | 1 / 1 | *unchanged* | `decoded` (donor) | still no brake-lock member — now proven exhaustively; `HandBrakeOffTime` **0.3 s** named as the family's only time member, and the JC3 member's own semantics are unrecorded, so mapping it would be a guess. Donor value stands | **A5** braking 100 → 0 | T-K2 |

`t5d_edits.json` carries the four numeric edits against a `t5d_current.json` snapshot of
test-088; `t1_apply.py --edits t5d_edits.json --current t5d_current.json` must print **4/4**
before `t5_apply.py --aaf Builds/test-088/aaf --out Builds/test-089/aaf` writes the tree the
takes will run against. Rows stay `next` until their take passes (R4).

### Batch B4 — the sweep that found one more bridge (executed 2026-10-23)

Every remaining `class`/donor row was re-checked against `CHAIN.json` with a chain grep for its
own quantity. One row had a same-quantity, same-unit bridge all along; the rest closed as
*proven absence* or a *disproven bridge* — each negative is now a chain result in the cell, not
an assertion.

| row | chain result | decision |
|---|---|---|
| **T-S3** `suspension.*.length` | `SVehicleWheel.SuspensionTravelUp` **30** + `SuspensionTravelDown` **40** cm (archetype, all four wheels) = **0.70 m** stroke; `length/min_length` carry one stroke (T-S6) | **0.25 → 0.70**, staged (`t5e_edits.json`, `next`, gate A6) — built as **test-090** |
| T-K1 `max_brake_torque` | `SVehicleSimCar.MaxBrakeTorque` **300** exists, but 4×300/(6000×0.683) = **0.29 m/s²** vs the measured 3.5–3.8 → the bridge is disproven by magnitude | stays `class` 5,000; cell now carries the disproof |
| T-M2 / T-M3 / T-M4 | only neutral multipliers (`InertiaTensorMultiplier` [1,1,1], `MassScale` 1.0); no CoM, no wheel-mass member | absence proven in-cell |
| T-A2 / T-A4 | no aero member anywhere (nav `SelfDriveUseTightArea` and upright `UprightLiftStrength` only) | absence proven in-cell |
| T-ST6 / T-K3 | no `*Align*` member; handbrake family is On/Off speed + lat-slip + off-time, no friction factor | absence proven in-cell |

### Batch D — blocked triage (14 rows): 7 routable, 2 research-gated, 5 permanent omissions

| row(s) | blocker | route | owner / first action (scheduled 2026-10-23) | class |
|---|---|---|---|---|
| T-P3, T-CO2, T-CO3 | no `.physicsc` **writer** (reading is solved, G2-8) | writer spike, else the standing decision "chassis stays JC3-side" closes them as keeps | **G2 write side** (`jc3hkx.py`): round-trip one hull, then the decision either way — *the spike, not the row, sets the deadline*: write it and these three become a batch, or refuse it and they close as keeps with the reason in `why` | routable |
| T-FX3 | `usage_effects[].usage` hash vocabulary unknown | fleet-wide dump of usage names (12 exist; a G2-style script) → then an FX batch | **G2 tooling** (`jc3usage.py`, same family as `jc3index.py`): dump every `usage` name across the 6,045 vehicle modules and match an exhaust-flame slot. *First in the queue — it is a read, needs no feature work, and unblocks the only FX row* | routable |
| T-L4, T-LG4 | JC3 has no wheel-light preset | custom `SVehicleLight` in our `.epe` — part of the LGT-1 light-part build (plan phase 0) | **LGT-1**: rides the one-variable part-exposure probe already staged in test-083; both rows wait on that build, not on a value | routable (feature) |
| T-HUD5 | HUD weapon slot exists, entity has no weapon component | needs WPN-2 (plan phase 1) | **WPN-2**: port `CBulletWeaponBase` + `SWeaponPoint(turret_anchor)` into the `.epe`; WPN-1 (catalogue) is its prerequisite | routable (feature) |
| T-CAM9, T-CAM11 | no unit bridge: spring strengths, shake amplitude | disassemble/bridge research; if no bridge, they convert to permanent omissions — **never hand-substituted** | **CAM-1 (phase 6)**: disassemble the spring and shake paths; a failed bridge writes the permanent reason into `why` and moves the row out of `blocked`, it does not invent a number | research |
| T-S6 | JC3 has no per-axle bias / droop / undamped-rate member | translatable halves already in T-S1/S2/S3; remainder is a named omission | none — permanent, reason in `why` | permanent |
| T-ST7 | 55° lock at 220 °/s = 0.25 s; fleet rack floor 0.5 s | JC3 model limit, documented | none — permanent, reason in `why` | permanent |
| T-AU3, T-AU5 | 10 BmAK banks absent from the install | assets do not exist; donor banks kept | none — permanent, reason in `why` | permanent |
| T-CAM8 | no head-impulse / drift-orientation member | no member, documented | none — permanent, reason in `why` (T6 row) | permanent |

**Rule:** routable rows may only move to a buildable batch through a new decode or a feature
task recorded in `MODDING_PLAN.md`; permanent rows stay `blocked` with the reason, and count as
named omissions — that is the honest end state, not a failure to finish.

### Batch E — carried rows awaiting S5 (66 rows, no build needed)

38 evidenced `keep` + 16 `epe` + 12 evidenced T6 rows. Their values are already in the live build
or the entity graph; all they owe is their §5 check. Groups:

- **graph/carried (16 `epe`):** T-L1…T-L3, T-L5…T-L7 (light presets), T-P1, T-PA1…T-PA8
  (parts/wheels/constraints), T-FX6 (effect graph).
- **file-provable now (verify cell is a tool):** T-G1, T-G2, T-G3, T-MA1, T-MA2, T-PA2,
  T-LG1, T-LG2, T-PA8, T-PA9, T-CO1 — run their tools against the installed build; most are
  already green from T-5 and are re-run per build.
- **behaviour-open (see §5):** the rest, including T-G5, T-M2…T-M4, T-S3, T-R1, T-ST1, T-E2,
  T-E5, T-B1…T-B3, T-A1…T-A4, T-K3, T-MA3…T-MA7, T-LG3, T-LG6, T-AU2, T-FX1, T-FX2, T-DM1…T-DM7,
  T-K4, T-DR1, T-EF1, and the T6 driving rows (T-HUD1…T-HUD3, T-CAM1…T-CAM7, T-CAM12, T-CAM13).

### Batch F — camera re-derivation (executed 2026-10-23: built as **test-091**)

test-086's values are withdrawn and were never reused. The composition is decoded
(`CAMERA.md` §2b, `bmak_camdecode.py --check` 18/18: boom + pitch-lerped sit, additive — at rest
7.00 m behind, 1.30 m above), and the FOV conversion is corrected (BmAK horizontal 85/95 → JC3
vertical ≈55…63). `bmak_camfile.py` was un-withdrawn: its `guard()` now fails closed on wrong
inputs (the 400/400 cm chase config **and** a green `bmak_camdecode --check`) instead of refusing,
and its eight `EDITS` are the T6 rows. T-CAM9 and T-CAM11 stay blocked regardless (§4D).

| # | tune field | old | new | row | pass |
|---|---|---:|---:|---|---|
| 1 | `CameraPosition[1]` height (m) | 2.0 | **1.30** | T-CAM5 | A15 distance at rest |
| 2 | `CameraPosition[2]` back (m) | 5.0 | **7.00** | T-CAM5 | A15 distance at rest |
| 3 | `LookAtPoint[1]` pivot (m) | 1.25 | **1.55** | T-CAM5 | A15 |
| 4 | `FOV[0]` vertical (°) | 30 | **55** | T-CAM2 | A15 wide chase, no fisheye |
| 5 | `FOV[1]` vertical (°) | 55 | **63** | T-CAM2 | A15 |
| 6 | `FOVVelocityRange[1]` (km/h) | 50 | **108** | T-CAM3 | A15 FOV stops changing at 108 |
| 7 | `RollWithVehicleAmount` | 0.3 | **0.38** | T-CAM6 | A15 car leans, camera follows |
| 8 | `CollisionStartPoint[1]` (m) | 1.0 | **1.6** | T-CAM13 | A15 no clipping through the taller body |

T-CAM4/FollowCameraRange and T-CAM7/PitchLimit keep their values (the rows say keep); T-CAM12's
400 cm boom is the composition, folded into row 2. Built by `bmak_cambuild.py pack --base
Builds/test-090 --tag test-091`: **13/13 pack checks**, `verify` **14/14**, installed (the pack
step's stage path was buggy when base ≠ donor — it wrote the patched `.epe` into test-085; fixed
with an aaf-contained path + escape guard, and test-085's tree was restored from test-083 and
cross-checked against its independent `verify/` copy). A15 is now unblocked.

### Batch G — feature-gated translation (not value work)

Weapon rows, custom wheel lights, HUD caller — these belong to plan phases 1/6 (WPN-2, LGT-1,
bridge work), not to the value pipeline. They are listed here so no one waits for T on them.

---

## 5. Verification campaign (S5): every open verify cell has exactly one gate

One take per manoeuvre, one instrument per number. Where a shift point or pitch is the
measurement, the take **must be recorded with audio** (take 1's lesson: `--no-audio` cost the
rpm channel). Each pass criterion is quoted from the row's `verify` cell.

### A. Driving manoeuvres (QA-1, `qa1_hud.py` where speed is the number)

| # | manoeuvre | rows it clears | pass |
|---|---|---|---|
| A1 | launch 0–100 (done) | T-M1 ✅, T-E2 open | 16.4 s / 257 m baseline, repeatable ±5% |
| A2 | airfield top-speed run, boost off then on | T-E5, T-B2, T-A2, T-A1 | terminal speed matches the row's expectation; coast-down distance recorded |
| A3 | constant-radius corner at 60 and 100 km/h | T-M2, T-M3, T-A4, T-G5 (low-speed probe) | 6 t-class yaw response; low-speed grip differs as the enum probe predicts, or the probe is declared no-op |
| A4 | steering hold at 60/100 km/h | T-R1, T-ST1, T-ST2, T-ST3 | front stops washing out; steering still acts at speed |
| A5 | braking 100 → 0 on tarmac (full stop, no corner exit) | T-K1, T-K2 | stop distance ≤ the 3.5–3.8 m/s² extrapolation (~100 m) |
| A6 | kerb strike, pothole, landing at 3 speeds | T-S1, T-S2, T-S3, T-M4, T-G4, T-G6 | no bottoming, no wheel jitter, ride height holds |
| A7 | handbrake drift 40/60 km/h, then release | T-K3, T-K4, T-DR1, T-ST5, T-ST6 | drift angle holds, no snap-back, countersteer catches |
| A8 | shift-point run **with audio** through gears 1–4 | T-E4, T-E3, T-AU4 | pitch steps at 66.8 / 108.4 / 146.1 / 182.9 km/h, no hunting |
| A9 | 0–100 with and without boost | T-B1, T-B3 | boost improves 0–100; no grip snap on engage |
| A10 | skidpad/skid check | T-EF1, T-R2, T-R3 | skid smoke appears at the same slip as a reference 6 t car |
| A11 | ram a wall at 40 km/h | T-DM7, T-DM6, T-DM5, T-CO1, T-PA3 | damage taken, panels deform, no instant destruction |
| A12 | 5-star pursuit survival ≥ 2 min | T-DM1, T-DM2, T-DM3, T-DM4 | survives minutes, not magazines |
| A13 | break a window, burn the engine | T-FX1, T-FX2, T-DM4 | the right effect on the right part |
| A14 | wheels steer/spin, doors/hood animate | T-PA4, T-PA5, T-PA6, T-PA7 | animation present, no part flies off |
| A15 | camera drive (only after Batch F) | T-CAM1…T-CAM7, T-CAM12, T-CAM13 | distance/FOV/roll at the decoded values |
| A16 | HUD drive | T-HUD1, T-HUD2, T-HUD3 | speed reads true; boost fills/drains the nitro meter; damage paints the bar |

### B. Screenshot gates (visual, pass is a named condition, not a mood)

| gate | rows | pass |
|---|---|---|
| noon daylight | T-MA3, T-MA4, T-MA5 | body luminance above the road it sits on; satin not wet-mirror; canopy reads as glass |
| dusk/night, beams on/off | T-LG3, T-LG6, T-L1…T-L7, T-FX6 | 5 cones only, correct colours, brake rows red, beams reach the road |
| paint menu | T-MA7 | 10 tints, none alters the body beyond gloss |
| damage/parts visual | T-DM6, T-PA7 | panels deform; lamps/plates do not crumple |

### C. File-level gates (re-run per build, cheap)

`t1_apply.py` → `t5_apply.py` → `t5_build.py` → install (approval) → `verify_install.py` →
`t5_measure.py` → station scan; plus `t2_lg2.py`, `jc3parts.py check`, `LIGHTS.json problems`
(T-PA8), `SLOTS.json` vs built RBM (T-MA2), entity census (T-PA9), hull bbox vs mesh (T-CO1).

**No in-game check required (verify cell is `—`):** T-S4, T-R2, T-R3, T-ST4, T-B4, T-A3,
T-AU1, T-FX5 (plus T-LG6-style rows that are covered elsewhere). They close at S4.

**Row coverage guarantee:** each of the 113 in-scope rows appears in §4 exactly once
(16 built + 4 queued + 1 assumed + 15 blocked + 77 carried = 113) and its `verify` cell lands
in §5.A, §5.B, §5.C or "no check". `bmak_coverage.py --check` additionally proves all 423 BmAK
fields are assigned to a row, so a factor cannot hide outside the plan.

---

## 6. Dependencies and interfaces

| T work | waits on | belongs to |
|---|---|---|
| Batch B staging | nothing (evidence complete) | T-5 continuation |
| Batch B S5 (A11, A7) | Batch B installed | T-5 |
| Batch C settle routes | only `VOCABULARY.md` / `T3_FLEET.md` / written decisions | T-1/T-2b/T-3 rows |
| T-L4 / T-LG4 | LGT-1 light-part build + custom `SVehicleLight` | plan phase 0 (LGT-1) |
| T-HUD5 | WPN-2 weapon component | plan phase 1 |
| T-P3 / T-CO2 / T-CO3 | `.physicsc` writer spike, or the standing chassis decision | plan risk list |
| Batch F (camera) | nothing now (composition decoded); values must be regenerated | plan phase 6 (CAM-1) |
| A8 (shift points) | an audio-enabled take | QA-1 |
| Rows verified | the takes in §5 | QA-1 |

The plan header's "next handling build is the four-row / six-value batch" **is** Batch B here;
`GRAB_BACKLOG.md`'s "Next five moves" is superseded by §10 of this file.

---

## 7. Coverage proof (why the backlog is complete)

```
113 in-scope rows
├── 16  built + file-verified (test-085)      → owe S5 only (§5)
├── 3   queued (t5c_edits.json, 4 values, all `decoded (donor)`; cleared 2026-10-23 with a
│        behaviour and a take each — Batch B2) → S4, then their take
├── 1   assumed, signed off (T-E5: wiki top speed) → re-derive after T-B1
├── 15  blocked (Batch D + T-DM9 small-arms immunity) → routes or named omission
└── 78  carried (keep + epe + 12 T6) → S5 checks only
+15 out = 128 total rows (excluded by rule; T-W1 alone accounts for 261 of 423 BmAK fields)
```

Nothing in this file is a placeholder for "figure it out later": every row has a disposition,
every not-yet-buildable row has a route or a permanent reason, and every buildable row has an
exact value table and a pass criterion.

---

## 8. Gates — the re-runnable check list

| gate | command | proves | last result |
|---|---|---|---|
| G1 inventory | `grab_model.py check` | BmAK objects/values/curves/sockets | schema 6, green (2026-10-23) |
| G1 offsets | `OFFSETS.json` summary | 423/423 fields named | green (G1h) |
| G2 index | `jc3index.py check` | 81,952/81,953 named, paths resolve | green (G3h) |
| G2 geometry | `GEOMETRY.md` totals | 77,611/77,611 blocks | green (G3f) |
| G2 shapes | `jc3hkx.py check --all` | hull/plane/station invariants | green (G2-8) |
| G2 effects | `jc3fx.py check` | 62.5 M rows re-read | green (G2-9) |
| coverage | `bmak_coverage.py --check` | all 423 fields have a row | per T-3 §2 |
| fleet | `t3_fleet.py --check` | the class numbers behind every class row | per T-3 §3 |
| row audit | `status_audit.py --check` | `STATUS.md` matches the ledger | green (G3h) |
| staging | `t1_apply.py` | edits' `old` == the batch's own base snapshot; members exist | 35/35 (T-5, vs `current.json` = test-083) + 4/4 (B2, vs `t5c_current.json` = test-085); control: the 35-edit list **fails** against test-085's snapshot |
| apply | `t5_apply.py` | every edit applied, 0 collateral | 35/35 (T-5) |
| pack | `t5_build.py` | aafdiff + `.toc` records (478/478) | green (T-5) |
| install | `verify_install.py` | deployed pair through its `.toc` | 9/9 (T-5) |
| read-back | `t5_measure.py` | every `new` as the engine reads it | 35/35 (T-5) |
| camera | `bmak_camdecode.py --check`, `bmak_camfile.py check` | composition + emitted tune | 18/18, 8/8 |
| HUD | `bmak_hud_inventory.py check`, `bmak_speedometer.py --check`, `hud_spec.py --check`, `bmak_hud.py check` | 25-class roster, 19 movies, 252 setters; native speedometer record; legacy scripts | 25/19/252, speedometer PASS, 99/99, 260/260 |
| behaviour | §5 takes | **nothing** — this gate is at 0/112 | QA-1 take 1: 2 measured, 2 partial |

**Rule:** S6 of every batch re-runs `status_audit.py --check` and the S4 gates for its own build;
a failing gate stops the batch, it is not worked around.

---

## 9. Improvisation register — the only places improv can happen, and the rule for each

| where improv is unavoidable | why | pre-declared rule |
|---|---|---|
| driving takes (traffic, road, driver) | the game world is not a lab | one manoeuvre per take, entry/exit conditions from §5; a missed window = **re-take**, never reinterpret the data |
| visual verdicts (screenshots) | "looks right" is partly judgement | pass is the named measurable condition (luminance vs road, cone count); if it cannot be measured, record both screenshots and state the ambiguity |
| feel rows (T-ST1 lock, T-DR1 drift, T-K2 ABS) | a driver judges them | paired A/B against a reference 6 t vehicle in the same take; verdict written before comparing numbers |
| evidence arriving mid-batch | a decode lands during staging | never merge; the new row joins the **next** batch |
| module size changes at pack | Gibbed normalises padding | existing rule: prove unrelated by re-encoding the unedited file; `.toc` rebuilt with all records checked (T-5 precedent) |
| a manoeuvre that cannot be executed | e.g. 5-star pursuit varies | record the attempt, keep the row open, name the blocker — do not downgrade the pass |
| blocked-row conversions | writer/feature work lands | move only through §4D routes + a MODLOG entry; the batch table is amended before the value is built |

---

## 10. Execution order after approval (what "proceed" means)

1. ✅ **Batch C, desk only** — done 2026-10-23: 11 rows re-decided from fleet evidence, T-E5
   signed off, `STATUS.md` regenerated (assumed 12 → 1).
2. ✅ **Batch B stage** — done 2026-10-23: `t5b_edits.json` (9 values, old read from the live
   test-085 decode), `t1_apply` 9/9.
3. ❌ **Batch B build** — built and driven, then **withdrawn**: test-087 turned collision damage on
   because T-DM7 read the Batmobile's ram *attack* as defence (`POSTMORTEM_DAMAGE.md`). Rollback to
   test-085; the six surviving values are staged in `t5c_edits.json` and are not cleared.4. ✅ **Behaviour rows first** — done 2026-10-23 as **Batch B2** (§4): each staged value now
   names its BmAK behaviour (or the search that proves none exists), its source class and the take
   that can fail; two values were withdrawn under R2 and four were re-sourced to the donor.
   The damage block stays settled as switches (`damage_audit.py`), not values. What remains here is
   the takes themselves: §5.A manoeuvres (A2 boost top speed, A5 braking, A7 drift, A9 boost grip),
   one each, entered in `QA1_RESULTS.md` — they need a driver, not a desk.
5. **§5.B screenshot gates** — noon, dusk/night, paint menu in one evening session.6. ✅ **Batch D triage** — done 2026-10-23: the 7 routable rows now carry an owner and a first
   action in §4D (usage-vocabulary dump first, then the `.physicsc` write spike, features behind
   LGT-1 / WPN-2), and the 5 permanent omissions keep their reason in `why`, so they stop being
   todos and start being named omissions.
7. **S6 after every step** — MODLOG append, `status_audit.py --write`, this plan's counts
   corrected if they moved.

Nothing in this order requires a value, threshold or pass criterion that is not already written
in this file or in the documents it cites.

---

## 11. Cross-check record (this plan vs STATUS / GRAB_BACKLOG / MODDING_PLAN)

Agreements verified 2026-10-23 (re-counted after Batch B2): **128 rows / 113 in scope /
97 evidenced / 1 assumed / 15 blocked / 15 out / 3 queued / 35 values over 16 rows /
0 behaviour-verified** — all four documents now say the same thing (`STATUS.md` generated,
`GRAB_BACKLOG.md` T-section, `MODDING_PLAN.md` header, this file).

Stale claims found and corrected in this pass:

| where | was | is | evidence |
|---|---|---|---|
| `MODDING_PLAN.md` §0.1 | live build = test-083 | **test-085** | `install.ps1 -Action Status` matches test-085's receipt, run 2026-10-23 |
| `MODDING_PLAN.md` header | G2 = 99.998% | **99.999%** | `STATUS.md` (81,952/81,953) |
| `MODDING_PLAN.md` phase-0 | QA-1 shown as not started | harness built, take 1 measured, 2 rows closed / 2 partial | `QA1_RESULTS.md` |
| `T6_HUD_CAMERA.md` §4 | "T-CAM5 is blocked on the boom composition" | composition **decoded** (§2b); the block that remains is T-CAM9/T-CAM11 | `CAMERA.md` §2b, `bmak_camdecode.py --check` 18/18 |
| **this file §sources** | live `.ee` == test-085 | the dropzone held **test-087's** `.ee` (postmortem rollback never ran); restored 2026-10-23, 9/9 | `verify_install.py` 8/9 → `install.ps1 Install` → 9/9 |
| **this file §2** | ledger `blocked` 10, `out` 7 | **11 and 8** (50/4 → 51/3 kept/queued after B2) | `t_rows.py check`: 105 rows, sums to 105 |
| `T1_TRANSLATION.md` §6/8/10 | T-ST5, T-B2, T-B3, T-K2 sourced by `class` median | **`decoded (donor)`**, T-ST5 withdrawn to `keep` | Batch B2 table above; `t5c_edits.json` |

**Execution pass 2026-10-23 (Batch C, then Batch B withdrawn):** counts moved 86 → 97 evidenced
(85.8%), 12 → 1 assumed, 4 → 4 queued rows (6 values). The intermediate 86.6% / 6 queued / 9 values
reading was the staged test-087 state; withdrawing its three damage rows is what moved it back and
retired T-DM7. Three further claims corrected against the
decoded fleet: "vanilla Serpente = min_time_to_block 5" (donor ships **1**), "T-S5 unchanged by
the project" (build 0.2 vs donor 0.1), and the T-3 audit's "donor drift sensitivity 2" (donor
ships **4** — the build block is the donor's, member for member). `t_rows.py check`,
`status_audit.py --check` and `t1_apply.py` (both batches) are green.
