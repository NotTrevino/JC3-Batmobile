# Review 8399 — the build wave, the RC4 artifact, and every compromise in it

**Verdict: the wave is honest about more than it can prove, but four claims are still stated too
generously and nine gaps have no owner. `Builds/bm-RC4` is a real artifact (696-file `aaf`, 714
`.toc` records, 9 drop files, `receipt.complete = false`) and its own `--check` is 22/22. It is
not complete, and this review does not mark it so.**

Read for this review: `build-d01`…`build-d13` (13 reports), `COMPROMISES_T.md`/`.json`, the RC4
receipt, `T22_REOPEN.md`, `bm_rc4.py`, `bm_rc4_lights.py`, `bm_health.py`, `bm_budget.py`,
`aafdiff.py`, `install_v3.ps1`, `BUILD_BATCHES.md`, `GRAB_BACKLOG.md`, `MODDING_PLAN.md`.
Nothing was built, installed, or launched; no build artifact was written by this review.

---

## 1. The three reds (checked first, as instructed)

All three are genuine and all three are stale **checkers**, not build regressions.

| script | measured 2026-11-07 | cause |
|---|---|---|
| `Tools/scripts/v05_driving.py --check` | **FAIL** | T-ST7 was unblocked 2026-11-06; the script still asserts it is blocked, so the turning circle is not re-derived from the built `t_to_full_steer_s` 0.8 low / 0.6 high |
| `Tools/scripts/t_boost_rows.py` | **20/21** | pins a **198-row** ledger; the ledger now has **199** (145/216 evidenced, 15 blocked, 35 edits over 16 rows) |
| `Tools/scripts/t_vnf_six.py` | **AssertionError** | hard-coded **198** |

Disposition: brief **8396**. The pins become 199 (read from the ledger, not hard-coded) and the
turning circle is re-derived from the built values; the T-ST7 red stays visible until a driving take
resolves it. No assertion is deleted or loosened.

---

## 2. The reopened collision, as merged

`T22_REOPEN.md` says 2 of the 3 BmAK shapes are missing. The merged RC confirms it.

| fact | merged value | where |
|---|---|---|
| BmAK asset | `Physics.Batmobile_V3_Physics`, **2 bodies / 3 boxes / 1 constraint** | B-10e reading of export 169750 |
| `sportsmuscle.physicsc` | **340,368 B**, internal at `.toc` offset **15,993,844**, sha256 `0164936b…9323` | `Builds/bm-RC4/drop/…debug.ee.toc` |
| hulls written | **5** (body 0 + 4 wheels) | body-0 hull AABB |
| donor bodies kept | **62**; shapes missing **2**; free hull slots **0 of 54** | receipt `collision` |
| hull shape vs chassis box 0 | **0.0000 m** (size `[3.7454, 2.075, 6.903]` exact) | build-d08 §4 |
| hull placement | `[0.0005, 0.061, 0.0025] m` → **6.1 cm high** | same |
| card gate (5 cm) | **NOT MET** — `receipt.collision.gate.pass = false` | receipt, `not_done[0]` |
| 1 constraint | **named omission** — no JC3 constraint writer | build-d08 §4 |

The 6.1 cm is the render mesh's floor (0.091 m) versus the box's floor (0.030 m): the hull keeps
DIM-1's ground line. It is a measurement, not a merge defect, and the tree carries it as delivered.
Brief **8390** owns either dropping the ground line or re-wording the card; nothing may pass it as
green in the meantime.

---

## 3. T-WP4's card citation

`Working/Translation/T_ROWS.jsonl`, row `T-WP4`, cites **B-24 / B-25**. Those are the
handling-values card and the lens-flare/light-unit card. T-WP4 is the EMP missile
(`RBatmobileEMPMissile` + `Batmobile_EMPMissile_Projectile_ForCars`, built as a `w618` clone plus an
entity `CForcePulse` with **no disable**). Lock-hold/salvo has **no card**, and the lock half is
T-WP3b. The citation is wrong and it sends a reader to two unrelated payloads.
Brief **8395** replaces it with the owning cards (B-18 pulse/disable, T-WP3b lock half, B-15 if the
riot toggle is the carrier) or creates the missing card.

---

## 4. Value audit — what the reports built against what BmAK says

Method: every value table in the 13 reports was compared with its ledger row and the BmAK member
the row cites. Counts audited per report: d03 **24 light rows**, d04 **23 texture rows / 38
objects**, d05 **15 weapon rows + 4 roots**, d06 **15 tune rows / 164 aspects**, d07 **30 effect
objects / 17 T-17 paths**, d08 **59 parts / 19 types / 62 bodies**, d09 **45 GUIDs**, d10 **15 T1
values + 5 prep rows**, d11 **21 profile fields**, d12 **8 mode rows**, d13 **9 drop files / 714
records**. Bytes are the packed artifact, not the plan.

| # | built value | BmAK / ledger says | verdict | file + byte |
|---|---|---|---|---|
| 1 | body-0 hull shape exact, placed on the mesh floor | chassis box 0 floor 0.030 m (B-10e, export 169750) | **stand-in**: mesh-space placement | `sportsmuscle.physicsc`, `.toc` 15,993,844 |
| 2 | 2 of 3 box shapes absent, constraint absent | 2 bodies / 3 boxes / 1 constraint | **stand-in / omission** | same file, 54 hull slots, 0 free |
| 3 | `max_health` 36,000 | BmAK `Health` **1,200** (T-DM1) | **approximation** (30x) | `batmobile_health_medium.vmodc`, `.toc` 23,252,584 (3,741 B) |
| 4 | `drag_coefficient` 0.1213 | BmAK has **no aero member** (T-A2); 0.55 was the class value | **derived from an assumption** (336.4 km/h label) | `custom_land_global.vmodc`, internal record |
| 5 | `t_to_full_steer_s` 0.8 / 0.6 | `SteerSpeed` **220 °/s**, lock 0.25 s (T-ST7) | **approximation** (2.4-3.2x slower); already reopened | `land_steering.vmodc` |
| 6 | `steer_time` 0.091 s | below the 0.2 s fleet minimum (T-ST3) | **declared out-of-domain** | same |
| 7 | `wheel_drift_aligning_strength` 0.625 | BmAK `LatSlipFactor` 1.6, no aligning member (T-ST6) | **INFERRED reciprocal**, falsifier 0.48 | same |
| 8 | handbrake factor 1.0, rear only | 1.5 front / 1.1 rear, 640,000 force (T-K4) | **approximation**; ledger `from` still says 5, build used 1 | `custom_land_global.vmodc` |
| 9 | boost grip 1.5 / 80 (restored) | BmAK states no boost grip change (T-B3) | **donor restored by proof of absence** — defensible | same |
| 10 | 24 light rows: range 60 / angle 70, multiplier 1.0, row 11 donor tuple | shipped max 50/50; BmAK Brightness 0.15 has no bridge; row 11 has no BmAK data | **out-of-domain + fleet mode + donor row** | lights module, `.toc` 16,499,504 (7,105 B) |
| 11 | 12 of 23 texture rows unfaithful: 4 chapter masks + 8 missing pixel sets | pixel sets absent / no chapter selector | **stand-in / omitted pixels** | 33 `.ddsc` in `aaf`; `receipt.complete = false` |
| 12 | 21 of 45 audio GUIDs donor (19 effects + 2 character) | BmAK: 90 events / 10 banks (T-AU3) | **donor**; mechanism undecoded (B-26) | `vehicles.bank` 210,781,376 B, `weapons.bank` 177,586,080 B |
| 13 | vehicles#279 loop wrap -39.68 dBFS payload | rule -40 dBFS; own p99 -46.01 | **measured red**, 2/3 not 3/3 | same banks |
| 14 | 30 effect objects on donor `.effc` paths; exhaust/sparks donor-carried; tracers/casings/trails absent | 16 tracer systems / 112 emitters; 8 casing systems; 18 trail systems (T-FX12/13/16) | **donor + omissions** | `.epe` 134,072 B at `.toc` 17,713,812 |
| 15 | 15 weapon rows; disable half has no member; tracer units + AutoAim unit UNKNOWN | BmAK 40° cone, 0.75 s riot cadence | **omission / UNKNOWN** | 7 private `.wtunec` |
| 16 | 4 roots, 3 childless; 2 pulses at graph origin; 69 interaction objects skipped | no shipped childless-root precedent; chassis offset UNKNOWN | **design stand-in** | same `.epe` |
| 17 | 59 parts / 19 damage types; 4 type fallbacks (`Boat_Antenna`, `Boat_Generic`, `Plane_Control_Surface`, `Train_Generic`) | 19 types used of the donor's 19/17 | **fallback**, named | `vehicle_parts.vmodc`, internal |
| 18 | 21 of 22 Rebel fields donor; donor icon 18,688 B; donor `UIVideoPath` | Batmobile leaf + keys 443190071 / 1621485476 / 4081821928 | **donor-carried**, leaf removed (0 refs) | `item.onlinec` 77,569 B, `online.stringlookup` 1,746,322 B, icon 18,688 B |
| 19 | mode pair: **0 rows carried exactly**, 2 composed, 2 same-switch, 4 not built | BmAK battle factors (T-MD7 etc.) | **composed / not built**; not merged into RC | `Builds/bm-RC4-modes/*` |
| 20 | 16 far-LOD `.lod` trimmed to fit 4,791.3 KB | budget 4,915 KB | **approved-by-budget trim**, reversible by `bm_budget.py` | `aaf`, 181 RBMs |

No report claims a decoded BmAK number that the bytes do not carry: the stand-ins are labelled in
their own cells. The four that are stated too generously are #3 (36,000 reads as a choice, not a
30x approximation), #4 (336.4 is presented next to its drag as if measured), #12/#13 (the audio
section of d13 says "cards" without the 21-GUID count) and #19 (a built mode pair that the RC does
not contain).

---

## 5. The nine corrections, and what each owns

| brief | compromise | evidence | owner output |
|---|---|---|---|
| **8390** | collision: 6.1 cm placement, 2 of 3 boxes absent, constraint omitted | d08 §4, d13 §2, receipt gate false | `correction-8390-collision-placement.md` |
| **8391** | T-E5 336.4 assumed; drag 0.1213 derived from it | d10 §5.2 | `correction-8391-top-speed-label.md` |
| **8392** | 12/23 texture rows unfaithful | d04 §3, receipt `complete=false` | `correction-8392-unfaithful-textures.md` |
| **8393** | 21/45 donor audio GUIDs; vehicles#279 red | d09 §5-6 | `correction-8393-donor-audio-guids.md` |
| **8394** | lights out-of-domain 60/70, fleet multiplier, donor row 11 | d03 §3-8 | `correction-8394-light-units-domain.md` |
| **8395** | T-WP4 cites B-24/B-25 (handling/flares) | T_ROWS.jsonl | `correction-8395-twp4-card-citation.md` |
| **8396** | v05_driving / t_boost_rows / t_vnf_six stale (199 vs 198) | this review §1 | `correction-8396-stale-checkers.md` |
| **8397** | D-08 wheel `skew_health` lost to D-10 in `custom_land_global` | d13 §1, receipt `conflicts[0]` | `correction-8397-module-conflict.md` |
| **8398** | modes built but unmerged; B-25/B-26 + B-17…B-20 no payload | d12 §0, d13 §5 | `correction-8398-unshipped-cards.md` |

Each brief states the measured fact, the file and byte/offset, the exact outcome required, and how
to revert. None of them permits marking a card done without a payload.

**8395 was executed in this same pass** (not queued): both `T-WP4` occurrences of "(cards B-24 / B-25)"
now read "T-WP3b owns the lock half, B-18 the pulse/disable clone; no card claims the hold/salvo".
`dispo` stays `next`, `edits` 0, and `status_audit.py --check` reports STATUS.md current. The file is
untracked, so its revert is a manual reverse replacement, not `git checkout`; the DONE report records
the exact strings and this limitation.

**8402 (V-03) was executed after this review** and found the wiring is not clean. `v03_wiring_rc4.py`
(7 gates, deterministic over two runs) reports G1/G4/G5 pass and **G2/G3 fail**: four
`SAttachedEffect` "Fire" objects on the three extra roots carry `4DAE31AE=FFFF05DA`, an object no
node in the merged graph defines (cause: B-05 clones the donor root's members, not its children), and
six donor asset paths (incl. `truck_emp.ftune`, `rigid_object_effect_settings_default.etune`, the
w206 sub-assets) are in neither the build nor the 81,952-entry archive index. That is a new finding,
not covered by 8390-8398; it needs a B-05/B-18 correction before V-06/V-07. See
`verify-v03-wiring-rc4.md`.

---

## 6. The 84xx verification briefs, rewritten

All seven were rewritten against the artifact rather than the pre-build plan and carry a new
`Updated by review 8399` line. The facts they now gate on:

| brief | rewritten to verify |
|---|---|
| **8400** V-01 | 696 tree files, 714 `.toc` records, 9 drop files, 225 records differ / 26 at offset 0 (19 size-only), internal offsets (`.epe` 17,713,812/134,072; physicsc 15,993,844/340,368; health 23,252,584/3,741; lights 16,499,504/7,105), model 4,791.3 / texture 5,380.9, aafdiff 120 = 20+2+98, ledger 199 rows. No gating on the 198-row pins |
| **8401** V-02 | silhouette margin vs 99.9 %, 59 parts / 19 types, delivered pose only (T-MD13 unwritten), 5 hulls / 62 bodies / 2 missing boxes / 0 free slots / 1 constraint / 6.1 cm gate false, 24 lights rows at 60/70 |
| **8402** V-03 | 8 slots (4 roots × 2), 2 pulses at origin, 69 skipped interaction objects, 30/30 `.effc`, 7 tunes, 15 weapon rows, keys 443190071/1621485476/4081821928, 24/45 audio |
| **8403** V-04 | 2 banks with exact sizes, 45 GUIDs 24/45, 5/5 loudness, **2/3 loop** (vehicles#279 -39.68), `TMPDIR` on E: |
| **8404** V-05 | the three reds with their exact failure, ledger 198→199, T-E5 label + Cd 0.1213, T-ST6/T-K3/T-K4 out-of-domain, Q-2 collision expectation |
| **8405** V-06 | install.ps1 6,535 B / `df2348…`, 9 files, sim root `E:/Modding/_dropzone_sim_rc4`, 6 cases incl. decoy, REFUSED exit 2, SHA-256 via .NET, `IO.Path` split |
| **8406** V-07 | STATUS 145/216 / 15 blocked / 109 queued, and disclosure of 8390-8394 + 8397-8398 |

---

## 7. Checks run, and limits of this review

Run: the three reds above; `bm_rc4.py --check` result read from the d13 report (**22 PASS, 0 FAIL**);
receipt fields read directly (`complete`, `collision.gate`, `conflicts`, `not_done`, `drop` 9);
report tables grepped and read in full where a number was cited. No build was re-run, so the RC's
byte counts are the d13 report's, not re-derived here.

Limits, stated rather than implied:

1. **This is a ledger-level audit, not a binary re-derivation of all 199 rows.** Numbers were
   compared report-table → ledger row → cited BmAK member. V-01/V-04 are the phases that slice the
   packed `.toc` and decode every edited value; this review did not duplicate them.
2. **The 6.1 cm is taken from two independent reports (d08 measured, d13 receipted)**; it was not
   re-measured from the hull bytes in this pass.
3. **T-WP4's row text was not re-opened line-by-line** — the mis-citation is the one the 8299 wave
   recorded, and d05's payload matches it (clone + pulse, no disable).
4. **No runtime claim**: load, Rebel Drop resolution at leaf 1621485476, and every Q take remain
   untested (test ban). Nothing here says the car drives.
5. `Builds/bm-RC4` remains `complete: false`; the 12 texture rows and the collision gate are the two
   reasons, and neither is closed by this review.
