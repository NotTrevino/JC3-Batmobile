# INTEGRATION / VERIFY / PILOT / TEST / RELEASE + PIPELINE HEALTH - landmark map

Date of map: 2026-11-08. READ-ONLY survey of E:\Modding\JustCause3\JC3-Batmobile. No project file edited, no game launched, no installer run.
Labels: evidence = file path read; UNKNOWN = not in any file read. Pretrained JC3/BmAK knowledge not used as evidence.

## 0. Read-only checks I ran (this session)

| command | result |
|---|---|
| `python Tools/scripts/status_audit.py --check` | PASS ("STATUS.md is current") |
| `python Tools/scripts/t_rows.py check` | PASS ("ledger 199 rows ... check ok") |
| `grab_model.py check` | PASS 15/15, schema 6 |
| `bmak_chain.py --check` | PASS (336 cross-checked, 0 conflicts) |
| `bmak_coverage.py --check` | PASS |
| `jc3index.py check` | PASS (81,953 rows, 0 unnamed; note GRAB_BACKLOG.md §0.7 comment still says "81,952 / 81,953 named" = stale prose) |
| `jc3hkx.py check --all` | PASS (233 entities, 18,865 hulls) |
| `t3_fleet.py --check` | PASS |
| `jc3fx.py check` | UNKNOWN: killed by my 200 s timeout (exit 124), neither pass nor fail |

Conclusion for GRAB_BACKLOG.md §0.7 standing gates: 8 of 9 pass today, 1 not determined (jc3fx, slow). The gates do NOT cover V-01..V-07, so they say nothing about the four verify reds.

## 1. Where the pipeline actually is (facts)

- Stage table (STAGES.md): GRAB -> TRANSLATE -> BUILD -> PILOT -> TEST. Test ban lifts only when `tmp/freebuff/APPROVED_Q.txt` exists. It is ABSENT (checked).
- STATUS.md (generated, current): T = 148/221 in-scope rows evidenced (67.0%), 1 assumed, 15 blocked, 110 queued, **0 rows behaviour-verified**. (V-07 on 2026-11-07 quoted 145/216; the number moved after task 9030, which edited the ledger.)
- RC4 = `Builds/bm-RC4`: 9 drop files, 401,700,202 B, `receipt.complete = false` (receipt.json). Pursuit set only; battle pair unmerged (`Builds/bm-RC4-modes`).
- RC4 verify chain (`tmp/freebuff/reports/operator-digest-verify-chain-rc4.md`): 4 reds + 1 printed miss: V-03 G2 (4 dangling `F30CCB1C` fire refs), V-03 G3 (6 dangling asset paths), V-01 `tree` (size pins), V-04 loop wrap (vehicles#279), V-05 T-ST7 miss (built 0.80/0.60 s vs goal 0.250/0.091 s, still printed RED).
- RC5 repair wave 9001-9004 is DONE (reports exist): fire refs 4 -> 0 (`rc5-dangling-fire-refs.md`, `Builds/bm-RC5-entity/fire_refs.json`), G3 paths 6 -> 3 on unchanged RC4 with 1 stock + 2 real gaps for the merge to fill (`rc5-six-dangling-asset-paths.md`), size pins reconciled (`rc5-size-pins-reconcile.md`: .ee = 11,225,533 B sha b72690d3..., receipt 217,652 B; retired values were mid-rebuild snapshots), loop #279 seam repaired 3/3 <= -40 dBFS in `Builds/bm-RC5-audio` (`rc5-loop279-wrap-build.md`).
- RC5 branch trees that exist: only `Builds/bm-RC5-audio` and `Builds/bm-RC5-entity` (the latter holds JSON edit lists only). `Tools/scripts/bm_rc5.py` (named in brief 9190) does NOT exist yet; it is produced by 9100. `Builds/bm-RC5` does not exist. RC5 merge (9190) is therefore ~0% done.
- Queue (51 files in tmp/freebuff/queue). Computed by me from AFTER headers: READY now = 9031, 9050, 9054 only. Everything else waits: 9032 -> 9033 -> 9100 -> {91xx builds} -> 9119/9179 reviews -> 9190 -> 9191 + 9192 -> 9193 -> 9194 -> 9199; Q chain 8600-8605/8699 waits on APPROVED_Q.txt and report chain; 8906 waits on a producer stuck in low/too-similar.
- MODLOG.md has no RC5 section (last section = VX for RC4, 2026-11-07). STATUS.md prose ("Built and measured ... test-085..090", "bm-RC4 - what its bytes carry") is RC4-era and not RC5-aware.

## 2. TASK LIST (existing + inferred NEW-INT-n)

Size: S <=1 session, M 1-3, L 1-2 wk. "Session" = one Freebuff brief (~7-15 min actual, EST 50-60 in headers) for desk work; one game sitting for Q.

### 2a. Pipeline health and ledger reconciliation

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| NEW-INT-1 | Resolve ESCALATE E6 ("lane L1/L2/L3 log ambiguous, judge=None"): watchdog classifier cannot tell live from idle; watchdog says "lanes 0 < cap 3 ... start ONE lane" every 2 min while keeper says "all 3 lanes already running". Fix lives OUTSIDE repo (`C:\Users\User\.claude\skills\freebuff\...`; Claude watchdog session lacked read access) | pipeline | blocked | operator grants access to skill dir (or fixes) | all queue throughput | S | tmp/freebuff/ESCALATE.txt; watchdog.log tail; keeper.log; watchdog-claude.out |
| NEW-INT-2 | Restart/confirm lanes: driver-L1 exited 14:02Z "no live session for 2 min -> back to queue: 9054"; `running/` empty; 3 ready briefs not being claimed | pipeline | todo | NEW-INT-1 / operator (lane start) | 9031, 9050, 9054 | S | tmp/freebuff/driver-L1.log; watchdog.log F6 lines |
| NEW-INT-3 | Decide NO_RESTOCK (present since Nov 3): queue is NOT auto-refilled; watchdog E4 "only 3 ready briefs, need >= 8". Either lift or keep hand-writing unique briefs | pipeline | todo | operator decision | queue depth | S | tmp/freebuff/NO_RESTOCK; watchdog.log E4 |
| NEW-INT-4 | Similarity guard hygiene: every new brief hand-written, max pairwise trigram overlap 0.34; 3 files currently in low/too-similar; 8906 AFTER-deadlocked on one (E1) -> rewrite the producer (jeb-qwen-fair-test) uniquely or drop 8906's AFTER | pipeline | todo | none | 8906 (non-critical) | S | tmp/freebuff/low/too-similar/; QUEUE_MAP.md 2026-11-08 notes |
| NEW-INT-5 | Daily hours: not binding. hours-log shows 53/53 readings 2026-11-08 (picker). Record as non-blocker; re-check after 4 days of full lanes | pipeline | done (monitor) | - | - | S | tmp/freebuff/hours-log.jsonl |
| G3-11 | Ledger reconciliation (R-5) | TRANSLATE | done (caveats) | - | - | S | Working/Translation/LEDGER_AUDIT.md: value-verified 48/198, string-only 44, guessed 7, not translated 106 |
| G3-11b/c/d, G3-20b..e, R-5-part1 | follow-up re-checks | TRANSLATE | done | - | - | S | LEDGER_AUDIT2.md, MISSING_ROWS.md, LEDGER_G3B/C/E.md, R5_PART1.md ("not translated" != missing: 20 of first 35 built and equal) |
| G3-20 | Ledger rows from G3 results (synthesis) | TRANSLATE | partial (keyword pass: 180 OPEN / 2 CORRECTED / 16 SUPPLIED, unverified) | superseded by 20b-e verified passes; the first-pass file is not reconciled into one verdict | clean final "what is translated" answer | M | GRAB_BACKLOG.md §12 G3-20 row |
| NEW-INT-6 | One authoritative ledger-vs-build reconciliation of ALL 199 rows after the 9030-9033 apply wave and again after RC5 merge (tie each row to read-back from the built .toc). RESET_FINDINGS §3 failure "ledger drifted from builds" is only closed per sub-batch | TRANSLATE/VERIFY | todo | 9033, 9190 | honest "complete" flag in RC5 receipt | M | RESET_FINDINGS.md §5.5, §6 R-5 |
| 9030 | apply v2 weapon/lock/HUD rows | TRANSLATE | done | - | 9031 | S | tmp/freebuff/reports/apply-v2-weapon-lock-hud-rows.md |
| 9031 | apply v2 driving + world rows | TRANSLATE | queued READY | lanes (NEW-INT-2) | 9032 | S | tmp/freebuff/queue/9031-... |
| 9032 | apply v2 body rows | TRANSLATE | queued | 9031 | 9033 | S | queue/9032-... |
| 9033 | review v2 apply wave; rewrite 91xx briefs | TRANSLATE | queued | 9032 | 9100, 9120, every 91xx | S | queue/9033-... |
| NEW-INT-7 | STATUS-stale fix: `status_audit.py` embeds literal prose (test-085..090 batches, "bm-RC4" section) so `--check` stays green while text ages; GRAB_BACKLOG.md §12 tracker is not an input to the audit. Needs RC5 section generated from receipt + tracker/ledger reconciliation | VERIFY | todo | 9190 (RC5 receipt) | trustworthy VX | S | tmp/freebuff/reports/stale-status-numbers.md; STATUS.md |
| NEW-INT-8 | Update stale prose: GRAB_BACKLOG.md §0.7 (81,952), §3 ("live dropzone carries test-091", phase counts), §12 rows `V-01 ... V-07` placeholder, `Q-1 ... Q-5 | todo`; MODLOG has no RC5 entries; add RC5 sections as 9190-9193 land | VERIFY | todo | RC5 reports | operator comprehension | S | GRAB_BACKLOG.md lines 105-110, 332-357, 1973-1974 |

### 2b. G-leftovers that feed the merge (owned by this landmark only as dependencies)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| 9050 | exe entity-swap consumer (U1: how JC3 replaces/spawns a vehicle entity at runtime) | GRAB | queued READY | lanes | 9130 mode pair (D-2) | M | queue/9050-...; reports/mode-toggle-runtime-swap.md |
| 9054 | locate the 8 missing BmAK pixel sets | GRAB | queued READY (previous session ended unfinished, returned to queue) | lanes | 9140 textures | M | queue/9054-...; driver-L1.log 14:02Z |
| 9051/9052/9053 | native remainder triage, event 6BB2C66E bank chase, unnamed wavc | GRAB | done | - | - | S | tmp/freebuff/done/ |
| G3-07 | JC3 runtime oracle (`Tools/scripts/jc3oracle.py` + `Research/JC3Grab/ORACLE.md`) - read-only memory inspector, validate on vanilla Serpente then drop | GRAB / TEST instrument | open (nothing built: jc3oracle.py absent). Static layout only: G3-07a done 8/8; G3-07b1/b2/e done but answers UNKNOWN (root global, transform-vs-AABB, who writes part node +0x150/+0x158 - "no such chain", RUNTIME_LAYOUT5 REFUTED the candidate); G3-07d and 07f BLOCKED (inputs absent) | game must run to read it (test ban) + operator approval; static route has hit UNKNOWN twice | collision/colour verdicts at runtime (R-3), G3-09/G3-10 runtime halves | L | GRAB_BACKLOG.md §6b G3-07 and §12; Research/JC3Grab/RUNTIME_LAYOUT*.md; reports/G3-07d.md, G3-07f.md |
| NEW-INT-9 | Decide whether the Q instrument is the runtime oracle at all, or screenshots + `qa1_hud.py` only. No Q brief or card references jc3oracle; if not built, collision/mesh frame (the Q re-test 5 failure) is judged by eye again | TEST | todo (operator decision) | operator | Q-1 collision item, R-3 | S | RESET_FINDINGS.md §1 "runtime oracle", §6 R-3 |
| BmSDK 7992 | upstream/GOG research | GRAB | done | - | - | S | reports/bmsdk-upstream-gog-research.md: no GOG port exists; Epic fork keys on PE timestamp 0x6508B1CE, same as the GOG exe (identity of the two binaries NOT verified) |
| BmSDK 7993 | GOG exe address hunt (read-only) | GRAB | done (partial) | - | - | M | reports/bmsdk-gog-address-hunt.md: of 25 BmSDK code addresses 2 land on a function start; startup functions + GNames/GObjObjects/GEngine established; UObject/app cluster UNKNOWN |
| BmSDK 7994 | BmSDK on a COPY of the GOG game (`E:\Games\BmAK-GOG-sdk`, 68 G) | GRAB | done (partial) | - | - | M | reports/bmsdk-gog-copy-port.md: .NET runtime + managed BmSDK code run; remaining 22 UObject/FName addresses are Steam values = UNKNOWN, scripts reaching them will fault; GOG exe sha256 4b81c4cd... unchanged |
| BmSDK 7995 | port to the REPACK exe (`E:\Games\Batman Arkham Knight`) | GRAB | done (dead end) | - | - | S | reports/bmsdk-port-to-repack-exe.md: code in encrypted .text1, hook offset 0x5B7220 is string data; PreInit UNKNOWN |
| NEW-INT-10 | Finish BmSDK on the GOG copy: re-derive the 22 remaining addresses (UObject/FName/app) OR operator supplies a Steam copy. Value: live BmAK runtime values (R-3 for the BmAK side, U-1/U-2 defaults, event-to-bank links). NOT on the critical path for the JC3 product | GRAB | todo (optional) | operator (Steam copy / authorise launching BmAK for scraping) | BmAK-side oracle only | L | OPERATOR_PRIORITIES.md "Steam copy"; bmsdk-gog-copy-port.md |

### 2c. BUILD wave to RC5 (owned elsewhere; listed because 9190 depends on every item)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| 9100 | RC5 scaffold + merge script (`bm_rc5.py`) | BUILD | queued | 9033 | all 91xx | M | queue/9100-... |
| 9101-9103 | entity roots/slots; effect-writer payloads; tracker launcher+marker | BUILD | queued (chain) | 9100 -> 9101 -> 9102 -> 9103 | 9104.. | M each | queue/ |
| 9104-9110 | EMP missile, lock-hold/salvo/reticle, booster mesh, EMP burst, hacker/SAM, sonar, cannon/Vulcan/riot/pods | BUILD | queued | 9103/9104/9102 chain | 9119 | M each | queue/; OPERATOR_PRIORITIES.md ranking |
| 9119 | review weapon builds | BUILD | queued | 9101-9110 | 9190 | S | queue/9119-... |
| 9120-9124 | handling; suspension; drive modes+yaw; air control+ram; flip/water/remote | BUILD | queued | 9033, 9100, 9120 chain | 9130, 9179 | M each | queue/ |
| 9130 | mode pair + swap (D-2) | BUILD | queued | 9122, 9121, 9050 | 9179 | L | queue/9130; GRAB_BACKLOG D-2 (reopened) |
| 9140-9143, 9150, 9160 | textures (12/23 unfaithful), collision (2/3 boxes), lights/flares/beams, paint, audio override (21/45 GUIDs donor) and layers, HUD | BUILD | queued | 9100 (+9054, 9103) | 9179 | M-L each | queue/; correction-8392/8393 |
| 9170-9174 | controls/entry/exit/eject; health->explosion no crash; moving parts; world spawn/traffic/summon; surface/weather/impact FX | BUILD | queued | 9101 / 9102 | 9179 | M each | queue/ |
| 9179 | review body + world builds | BUILD | queued | all of the above | 9190 | S | queue/9179-... |
| NEW-INT-11 | Budget guard during the wave: Model 4,791.3 / 4,915 KB (margin 123.7 KB = 2.5%) and Texture 5,380.9 (RC4 V-01) - 5,855.8 (RC2) / 7,065 KB. RC5 adds booster mesh, 3 new CCar roots, up to 8 missing + 4 chapter-mask textures, HUD gfx, flares, wheel emitters. A single over-budget branch fails the merge; also "allocator 4,648.0 KB present and OVER its own sub-allocation" in RC4 V-01. Run `bm_budget.py` per branch, not only at merge | BUILD/VERIFY | todo | each 91xx branch | 9190 | S | Tools/scripts/bm_budget.py; operator-digest-verify-chain-rc4.md (V-01 budget) |

### 2d. INTEGRATION (RC5 merge)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| 9190 | RC5 merge: `bm_rc5.py --write`, 3-way .epe merge of branches, module merges (expect overlaps like RC4's custom_land_global D-08 vs D-10), budgets, .ee/.toc rebuild, receipt schema 2, install.ps1; `complete` true only if `not_done` derived empty; conflict table with stated rules | INTEGRATION | queued | 9101-9110, 9119, 9179 (14 AFTER files) | 9191, 9192 | M | queue/9190-...; Builds/bm-RC4/receipt.json (RC4 precedent: 22 gates, 120-file aafdiff) |
| NEW-INT-12 | Merge conflict policy for module overlaps with >2 branches (handling, suspension, drive modes, air control, flip all touch `custom_land_global.vmodc` members; RC4 resolved a 2-branch case member-disjoint) - pre-write a member-ownership table before 9190 | INTEGRATION | todo | 9120-9124 reports | 9190 | S | Builds/bm-RC4/receipt.json module_merges; reports/correction-8397-module-conflict.md |
| NEW-INT-13 | Decide the RC5 `complete` flag honestly: items structurally not finishable (UNKNOWN U1 swap trigger, engine behaviour, T-MD8/T-MD14 omission unless 9050/9130 find a carrier, T-ST7) keep `complete = false` with named owners. Operator needs to see this up front, since STAGES.md exit demands "0 omitted" | INTEGRATION | todo | 9190 | operator expectations | S | STAGES.md BUILD exit; Working/Q/APPROVAL_REQUEST.md §3 |
| NEW-INT-14 | RC5 installer: RC4 `install.ps1` has no Rollback091 (grep count 0) and snapshots by diff; confirm RC5 installer retains that and that Q briefs name the right installer (8601 says `install_v3.ps1` + bm-RC4, APPROVAL_REQUEST says `Builds/bm-RC4/install.ps1`) | INTEGRATION | todo | 9190 | 9192 V-06, Q-1 | S | Builds/bm-RC4/install.ps1; queue/8601-...; GRAB_BACKLOG V-06-RC2 / V-06-fix rows; reports/install-v3-guard-fix.md |

### 2e. VERIFY (V-01..V-07 against RC5)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| V-01 (RC4) | file gates | VERIFY | **RED on `tree`** (.ee -2 B, receipt +3,734 B vs pins). Root cause already found: stale pins from mid-rebuild reads; authoritative .ee 11,225,533 B / b72690d3 (rc4_pins.py). All other 11 V-01 sub-gates PASS | - (cause fixed in 9003 for RC5) | - | S | reports/verify-v01-file-gates-rc4.md; rc5-size-pins-reconcile.md |
| 9191 | V-01 + V-03 + V-04 on RC5 (copies of RC4 gates; do not edit gates to pass) | VERIFY | queued | 9190 | 9193 | M | queue/9191-... |
| V-03 (RC4) G2 | 4 dangling fire refs | VERIFY | **RED (RC4)**; fix designed+checked: null the four owner links (`rc5_fire_refs.py --check` dangling 4 -> 0). Gate had mis-attributed member (they're on `CBulletWeaponBase`, not the `Fire` SAttachedEffect) | merge must apply the edit list | 9191 | S | reports/rc5-dangling-fire-refs.md; Builds/bm-RC5-entity/fire_refs.json |
| V-03 (RC4) G3 | 6 dangling asset paths | VERIFY | **RED (RC4)**; 3 were gate normalisation errors, 1 stock reference, **2 real gaps** the merge must fill (names in report) | 9190 must carry the 2 missing assets | 9191 | S | reports/rc5-six-dangling-asset-paths.md; Builds/bm-RC5-entity/asset_refs.json; Tools/scripts/v03_wiring_rc5.py |
| V-04 (RC4) loop wrap | vehicles#279 below -40 dBFS rule | VERIFY | **RED (RC4)**; fixed in `Builds/bm-RC5-audio` (3/3 loops pass). Caveat: RC5 audio branch is a separate tree from the 9150 override build - the seam edit must survive 9150's rebuild | 9150, 9190 | 9191 | S | reports/rc5-loop279-wrap-build.md; Builds/bm-RC5-audio/verify |
| NEW-INT-15 | Re-run loop-seam check on the MERGED bank after 9150 changes banks (9150 may regenerate vehicles.bank/weapons.bank, undoing the seam fix) | VERIFY | todo | 9150, 9190 | 9191 | S | queue/9150-...; rc5-loop279-wrap-build.md |
| V-02 | silhouette 99.9004% (limit 99.9: passes by 0.0004 pt), parts 59/59, interaction 77/77, collision placement 0.25 cm (MET on shipped payload only; 2 of 3 BmAK boxes have no shape instance) | VERIFY | PASS on RC4 (marginal); needs RC5 | 9141 collision (3/3 boxes), 9101 (new roots), 9140 | 9192 | M | reports/verify-v02-geometry-poses-rc4.md, verify-v02a/b |
| 9192 | V-02 + V-05 + V-06 on RC5 (checkers read ledger length, not pinned counts); install dry run, 6 cases, simulated dropzone only | VERIFY | queued | 9190 | 9193 | M | queue/9192-... |
| V-05 | predictions sheet; RC4: 27 of 28 predicted, 1 excluded (battle variant by D-2); v05_driving 34/34 | VERIFY | done on RC4 but **T-ST7 miss RED** (built 0.80/0.60 s vs goal 0.250/0.091 s). Operator ruled 0.25 s; T-ST7 evidence for operator: a player module ships 0.3 s full lock (MotorbikeSteering) | handling branch 9120 must move it; if RC5 still prints it, name the number | 9192 | S | Working/Q/PREDICTIONS.md D-4/D-5; Working/Translation/T_ST7_EVIDENCE.md; GRAB_BACKLOG.md T-ST7-evidence row |
| NEW-INT-16 | Regenerate PREDICTIONS.md / PREDICTIONS_COMBAT.md / PREDICTIONS_LOOKS.md / predictions.json for RC5 values only via generator scripts; A9 band (4.5-7.5 m/s^2) is "declared, not sourced"; looks thresholds 2.0-3.0 m, 60/255, <=12, 8/255, 6 s are pilot-declared | VERIFY | todo (partly 9194) | 9192 | Q judging | M | Working/Q/PREDICTIONS*.md; operator-digest-pilot-cards-status.md §2 |
| V-06 | install dry run | VERIFY | PASS on RC4 (6 cases, sim root `E:/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc4`); RC2's Rollback091 FAIL is resolved by the RC4 installer design (no Rollback091; snapshot by diff). Caveat: Rollback after install-over-install removes targets as if uninstalling | needs RC5 repeat | 9193 | S | reports/verify-v06-install-dry-run-rc4.md; Builds/bm-RC4/verify/dropzone_sim.md |
| V-04 other | RC4 audio: loudness 5/5, events 24/45 resolved, 21 donor, length/decode/tail green | VERIFY | PASS-with-compromise | 9150 (override build) | - | M | reports/verify-v04-audio-rc4.md |
| 9193 | Gate VX for RC5: STATUS + BUILD_BATCHES regen, MODLOG VX, `Working/Q/APPROVAL_REQUEST_RC5.md`, recommendation to repoint 8600-8605 | VERIFY | queued | 9191, 9192 | 9194, 9199, approval | S | queue/9193-... |
| V-07 (RC4) | VX + approval request | VERIFY | done on RC4 (superseded by RC5) | - | - | S | reports/verify-v07-gate-vx.md; Working/Q/APPROVAL_REQUEST.md |
| NEW-INT-17 | Prove RC5 reads back in the game's own terms, not only file-to-file: every ledger value read through the built `.toc` is already required (V-01 readback 695 slices, 17/17 handling members); no gate checks that the engine honours it. Document explicitly that VERIFY = file evidence only (GRAB_BACKLOG §14 anti-goal) so VX is never mistaken for behaviour | VERIFY | todo | - | - | S | GRAB_BACKLOG.md §14 |

### 2f. Approval gate

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| APPROVAL-RC4 | `Working/Q/APPROVAL_REQUEST.md` (describes bm-RC4: 9 files, 383 MiB, 3 sessions Q-1 ~45 min / Q-2 ~40 / Q-3 ~45 as derived estimates) | VERIFY | done, but about the WRONG candidate once RC5 exists | - | - | S | Working/Q/APPROVAL_REQUEST.md |
| APPROVED_Q.txt | Operator writes `tmp/freebuff/APPROVED_Q.txt`; authorises install + Q-1 only (not code change/push/second tree). Only operator (or Claude on operator's word) may write it | VERIFY->PILOT | **blocked - operator only**; file absent | 9193 request (RC5) or operator accepts RC4 | 8600 Q-0 and the entire Q chain | S | Working/Q/APPROVAL_REQUEST.md §5; tmp/freebuff/queue/8600-... |
| NEW-INT-18 | Operator decision RC4-now vs RC5-later: approving RC4 means testing a candidate with 4 reds, pursuit-only car, 12/23 textures, 21/45 donor audio; the same sessions could be spent on RC5 | VERIFY | todo (operator decision) | operator | schedule | S | Working/Q/APPROVAL_REQUEST.md §3 |
| NEW-INT-19 | Repoint Q briefs 8600-8605/8699: their AFTER lists name RC4 reports (`verify-v07-gate-vx.md`, `review-pilot-cards.md`) and 8601 says "install bm-RC4 with install_v3.ps1"; 9193 only RECOMMENDS the repoint ("do not edit the Q briefs") and the operator must apply it | TEST | todo | 9193 + operator | Q chain correctness | S | queue/8600..8699; queue/9193-... |
| NEW-INT-20 | Fill pilot calibration fields only the operator knows: `ENTER_KEY`, `SAVE_SLOT_CLICK`, `SERPENTE_SPAWN` (stock spawn route), Rebel Drop navigation keys, main-menu labels, QA-1 airfield coordinates, JC3 windowed-launch flag (all UNKNOWN in repo) | PILOT | blocked - operator | operator | Q-0 P2/P3 | S | Working/Q/PILOT/PROVE_CARDS.md §1; pilot-card-world-and-vehicle.md; LAUNCH.md lines 118-130 |

### 2g. PILOT

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| Q-PILOT (8500-8508, 8599) | 34 cards (8 driving, 11 combat/gadget, 6 looks/audio, 9 prove-set) + CONTROLS/LAUNCH/LOAD_SAVE/SPAWN/ENTER_EXIT/AIRFIELD/SCREENSHOT/RECORD/KILL; reviewed (defect classes fixed) | PILOT | done as WRITTEN; **never executed** (no PROVE_LOG.md, no RESULTS.md) | - | - | M | Working/Q/PILOT/; reports/operator-digest-pilot-cards-status.md (18 of 34 have a numeric band, 15 of 34 have an UNKNOWN expected value) |
| 9194 | refresh cards for RC5: add cards for tracker marker, EMP missile lock, booster ring, EMP burst, hacker, sonar, flip recovery, water teleport, remote range, health-to-explosion, controls; remove/rewrite bands changed by RC5 | PILOT | queued | 9193 | 9199 | M | queue/9194-... |
| 8600 (Q-0) | Prove pilot cards on a stock Serpente: P1 LAUNCH ... P9 KILL; "a small model completes every card with no operator help" is the PILOT exit | PILOT | queued, gated | APPROVED_Q.txt + 8599 + calibration (NEW-INT-20) | 8601 | M | queue/8600-...; Working/Q/PILOT/PROVE_CARDS.md |
| NEW-INT-21 | Save backup + snapshot before first launch (`um backup`), PID capture and kill-by-PID path proven; the operator's profile 76561197960271872 save is at risk if installer snapshot logic fails on a real tree | PILOT | todo | approval | Q-0/Q-1 | S | Working/Q/PILOT/LOAD_SAVE.md; GRAB_BACKLOG §9b "Before every session" |
| NEW-INT-22 | Decide whether the BmAK-side comparison drives (same actions, BmAK keys) still happen; Q-PILOT item 2 in GRAB_BACKLOG §9b, no brief or card for it | PILOT | todo (operator decision) | operator + BmAK launch authorisation | optional | M | GRAB_BACKLOG.md §9b Q-PILOT item 2 |

### 2h. TEST (in-game campaign)

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| Q-0 / 8600 | stock-Serpente card proof | TEST | queued, gated | APPROVED_Q.txt, NEW-INT-20 | 8601 | M | queue/8600 |
| Q-1 / 8601 | static, spawn, looks, moving parts, weapons at wall, self-damage, night lights, audio at standstill (8 items, ~45 min derived estimate); expect known gaps: 12/23 textures, 4 chapter masks, 17 flares, light ranges 60/45 | TEST | queued, gated | Q-0, approval, install | 8602 | L | queue/8601; GRAB_BACKLOG §9b Q-1 |
| Q-2 / 8602 | airfield driving takes A2, A5, A6, A7, A9 then A1, A3, A4 (A8/A10/A15/A16 per card list), three repeats each, record with audio, vs V-05 bands | TEST | queued, gated | Q-1 report | 8603 | L | queue/8602; pilot-card-driving-takes.md |
| Q-3 / 8603 | world + combat: ram, 5-star heat, weapons vs targets, water, tether, traffic, lamp/engine FX; C1-C11 cards; cards whose build gate has not landed write BLOCKED not FAIL | TEST | queued, gated | Q-2 report | 8604 | L | queue/8603; pilot-card-combat-and-gadgets.md |
| Q-4 / 8604 | fix-loop triage from RESULTS.md/FIXES.md: group by cause, one fix card per failure; no compromise fixes, no retune on the spot | TEST | queued, gated | Q-3 | 8605, 8699 | M per loop | queue/8604; GRAB_BACKLOG §9b Q-4 rule: max ONE extra session per original session before the user decides |
| NEW-INT-23 | Fix-loop execution cycle (not a single brief): per failure -> TRANSLATE row change -> BUILD one value -> re-run V gates -> new RC tree -> re-install -> re-test in next planned session. No queue brief exists for iterations; 8699 is meant to write 87xx fix briefs after the fact | TEST | todo | Q results | Q-5/QX | L (repeats) | GRAB_BACKLOG.md §9b Q-4; queue/8699 |
| NEW-INT-24 | Record RESULTS.md / FIXES.md / PROVE_LOG.md templates that refuse placeholders (9194 promises this for cards; files do not exist yet) | PILOT/TEST | todo | 9194 | all Q reporting | S | Working/Q/RESULTS.md absent |
| QX gate | every Q check passed or named omission accepted by user | TEST | todo | Q-1..Q-4 | R-1, R-2, Q-5 | - | GRAB_BACKLOG.md §9b |
| Q-5 / 8605 | showcase recording (credits Rocksteady/WB, Avalanche) + KB field note + release list; must not imply unbuilt features (chapter damage states, flares, locked salvo, T-MD8, T-MD14) | TEST/RELEASE | queued, gated | Q-4 empty fix loop | R-1/R-2 | S-M | queue/8605 |
| 8699 | final review of test campaign + next-queue plan | TEST | queued, gated | Q-4 | - | S | queue/8699 |
| 9199 | desk review of RC5 campaign before asking approval (recount ledger, receipt not_done, texture refusals, donor GUIDs, missing boxes, mode rows; compare to RC4/STATUS) | VERIFY | queued | 9193, 9194 | operator ask | S | queue/9199-... |

### 2i. RELEASE

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| R-1 | What may be shared: mesh/textures/audio/particles are extracted from Arkham Knight and per toolkit rule R10 CANNOT be published -> release the PIPELINE only (scripts + edit specs that rebuild from the user's own copies of both games). Write `RELEASE.md`; run `um publish check .` on release folder: must find no game files or extracted assets; README with install-from-your-own-games steps, credits, AI disclosure | RELEASE | todo | QX | R-2 | S | GRAB_BACKLOG.md §10 R-1 |
| NEW-INT-25 | Release-folder assembly: Builds/ trees (383 MiB, contain AK-derived .ee/banks/ddsc) must be excluded; `Tools/` is untracked in git (MODLOG 8301 revert note) - decide which scripts ship, make them runnable on a clean machine with paths parameterised (many hard-coded E:\ / D:\ paths) | RELEASE | todo | R-1 policy | R-1 lint | M | GRAB_BACKLOG.md §10; MODLOG.md 2026-11-06 "Tools/ is untracked in git" |
| NEW-INT-26 | Lint risk: repo carries Research/ JSON with extracted BmAK values and tmp/ junk; `um publish check` may flag; plan a clean export directory rather than publishing the repo | RELEASE | todo | R-1 | - | S | AGENTS.md; git status (many modified/untracked files) |
| R-2 | Knowledge-base field note via `um kb new`, `um kb check`; PR only after the user agrees (`um kb pr <note> --yes`) | RELEASE | todo | QX, operator agreement to PR | - | S | GRAB_BACKLOG.md §10 R-2 |
| NEW-INT-27 | Publishing needs operator approval (private build + KB note); git commit/push is also operator-gated (INSTRUCTIONS.md: "no git commits, no PRs" for lanes; commit history has only 2 commits while ~60 files are modified/untracked) | RELEASE | todo | operator | release | S | tmp/freebuff/INSTRUCTIONS.md §3; git status |
| NEW-INT-28 | Showcase/credits text lists omissions honestly (T-MD8 turn on spot, T-MD14 battle audio, unlocked salvo, chapter damage states, flares) per Q-5 brief | RELEASE | todo | Q-4 | R-1 | S | queue/8605 |

## 3. (a) DONE, with evidence

- GRAB: G1 19,203/20,128 objects, 423/423 offsets; G2 81,953/81,953 named (my `jc3index.py check`), 6,045/6,045 modules, 77,611 geometry blocks (STATUS.md). Standing gates 8 of 9 pass in my run.
- TRANSLATE: ledger 199 rows, `t_rows.py check` ok; gate TX (`t23_closeout.py --check`): 75 codes, decisions 11/11 answered (D-2 reopened) per reports/verify-v07-gate-vx.md. STATUS.md current.
- BUILD: RC4 packed (`Builds/bm-RC4`, 9 files, receipt schema 2, `complete=false`); RC5 repair wave 9001-9004 and v2 plan wave 9010-9019, 9030 (reports present in tmp/freebuff/reports).
- VERIFY on RC4: V-01 11/12 sub-gates, V-02 pass (marginal 99.9004%), V-03 G1/G4/G5, V-04 loudness/events/length/decode, V-05 coverage 27/28 with all three checkers exit 0, V-06 six cases, V-07 approval request written (reports/operator-digest-verify-chain-rc4.md).
- PILOT: cards written and reviewed (reports/operator-digest-pilot-cards-status.md); none executed.
- Installer safety: v2 -> v3 guard fix, tested on copies only (reports/install-v3-guard-fix.md, install-v3-check-failing.md).
- BmSDK: three investigations done; GOG copy runs managed BmSDK code (reports/bmsdk-gog-copy-port.md). No game folder touched; GOG exe sha256 unchanged.
- Earlier in-game history exists (test-085..091 drops, QA-1 take 1, Q-1a chain, entry confirmed in game per RESET_FINDINGS §3), but 0 ledger rows are behaviour-verified (STATUS.md).

## 4. (b) BLOCKERS, root first

1. **Freebuff lanes are not actually running work** (watchdog: 0 lanes < cap 3 with 3 ready briefs, every 2 min since at least 14:16Z; driver-L1 exited 14:02Z; running/ empty), and E6 ("log ambiguous") is unresolved because the classifier lives outside the repo. Without this nothing in section 2c-2e advances. Operator action: restart lanes or grant read access to `C:\Users\User\.claude\skills\freebuff` (see watchdog-claude.out). Also NO_RESTOCK + similarity guard means only hand-written unique briefs enter.
2. **Serial desk chain before any RC5 build**: 9031 -> 9032 -> 9033 -> 9100 -> 91xx. Only 9031/9050/9054 are ready.
3. **RC5 merge (9190) needs ~14 predecessor reports**; its checker `bm_rc5.py` does not exist.
4. **Operator-only items**:
   - write `tmp/freebuff/APPROVED_Q.txt` (absent) - unblocks Q-0 and the whole Q chain;
   - choose RC4 vs RC5 as the first tested candidate (NEW-INT-18) and repoint Q briefs (NEW-INT-19);
   - supply pilot calibration values (NEW-INT-20: keys, save slot click, stock Serpente spawn route, Rebel Drop keys, airfield coordinates, windowed flag);
   - be present for in-game sessions or authorise an unattended agent launch (save backups, `um win` screenshot test, PID kill);
   - re-resolve D-2 (two entities vs hybrid) - RC4 carries pursuit only and T-MD5..T-MD8/T-MD13/T-MD14 depend on it;
   - Steam copy of BmAK + permission to launch BmAK for scraping (optional, NEW-INT-10);
   - approvals for compromises (lore-accuracy rule says none are accepted; any unavoidable one needs operator relay), for git commit/push, for `um kb pr`, and for any publishing.
5. **Runtime oracle gap (G3-07)**: JC3 root global, transform-vs-AABB and part-node writer are UNKNOWN after static attack (RUNTIME_LAYOUT5 refuted the last candidate); G3-07d/07f blocked on missing inputs; `jc3oracle.py` absent. Collision/colour judgement at Q will rely on screenshots unless the operator authorises attach-and-read, which still needs approval since it is a launched game.
6. **Content gaps that make `complete = true` unreachable by RC5 unless closed**: 12/23 textures (8 pixel sets not located, 9054 pending), 21/45 audio GUIDs donor (9150), 2/3 collision boxes without shape instance + 1 constraint (9141), battle pair/swap trigger U1 (9050/9130), T-ST7 0.25 s steering (9120), 15 blocked rows (STATUS.md).

## 5. (c) OPEN QUESTIONS FOR THE OPERATOR

1. Test RC4 (as-is, pursuit only, four reds acknowledged in APPROVAL_REQUEST.md) soon, or wait for RC5 (est. 3-6 days desk)?
2. D-2: two Rebel Drop entries / two entities, or hybrid? And is the unknown swap trigger (U1) acceptable to carry as a named gap, or must 9050 find it first?
3. T-ST7: the 0.25 s full-lock ruling is operator-set; evidence says a player module ships 0.3 s (MotorbikeSteering). Confirm 0.25 s stays the target (that is what keeps V-05 RED).
4. Will you (or an agent) run the in-game sessions? Who clicks menus (calibration fields UNKNOWN)? Is unattended agent piloting allowed with the stock-Serpente proof first?
5. Authorise a read-only attach to the running JC3 for the G3-07 oracle (R-3), or run Q on screenshots and QA-1 HUD only?
6. Steam copy of BmAK, and permission to launch BmAK (not JC3) for BmSDK scraping?
7. Lift NO_RESTOCK and let a restocker write briefs, or keep hand-written fillers? Who fixes the watchdog classifier (E6)?
8. Release scope: pipeline-only (R-1 rule) confirmed? Will you accept `complete=false` in the shipped receipt with named omissions? OK to open a KB PR?
9. Is the 17-flare / chapter-damage-mask / 8 missing texture set shortfall acceptable at first Q, or must textures close before approval? (Lore accuracy rule says no compromises; this is the practical sequencing question.)
10. Max fix-loop budget: backlog says one extra session per original session before the user decides; confirm that rule or give a different cap.

## 6. (d) RISKS

- **Fix-loop iterations after first in-game test (largest schedule risk).** Nothing has behaviour-verified: 0 of 221 rows. 110 queued rows have no pass yet; Q-2 alone is 9+ takes each with a band; a single wrong shared value (e.g. top speed predicted 267 km/h vs assumed label 336.4) forces rebuild + V gates + reinstall. History: the repo has already burned test-085..091 builds and four appearance builds + four handling sets "tuned by feel" (GRAB_BACKLOG §14).
- **History: Q re-test 5 caused the 2026-11-02 reset** (RESET_FINDINGS.md): file-vs-file verification passed while the game showed otherwise (collision off, white-violet paint). VERIFY green is NOT evidence; the same failure mode recurs if Q-1 judges collision/colour without an oracle. Colour: "BmAK black" has no known JC3 value (T-MA3/ALB-2; paint combine rule UNKNOWN; G3-09d write path open).
- **Marginal gates**: silhouette 99.9004 vs 99.9 limit; model budget margin 2.5% (123.7 KB); any RC5 geometry addition could flip V-02 / V-01 budget red.
- **Merge conflicts**: many branches edit the same module members; RC4 had 2 branches on one module and needed a hand-written rule (8397). RC5 has 5+ (handling, suspension, drive modes, air control/ram, flip/water).
- **Audio seam regression** if 9150 regenerates banks (NEW-INT-15).
- **Pipeline fragility**: lanes dead now; E6 unresolved; briefs of ~7-15 min actually run vs EST 50-55 headers; held tasks (8158/8134) once stalled chain; similarity guard silently moves briefs to low/too-similar and has blocked dependents before (8214, 8401 merge, 8906 now); `AFTER:` deadlock when a producer is stripped.
- **Installer safety on the real dropzone**: only ever run on copies; RC2 installer defect (Rollback091 deletes) shows real-folder risk; real dropzone state "already holds the build". Snapshot-by-diff semantic can delete files on Rollback when installed over an already-matching tree. Saves backup mandatory.
- **UNKNOWN engine behaviours that only Q can settle** (APPROVAL_REQUEST §3): steering rate, drift labels, collision/light domains at runtime, tank pivot key, missile lock time, which high-speed lock, whether 6,000 kg mass is design not decoded.
- **Operator availability**: all in-game steps and approval are single-person; each Q failure needs operator turnaround.
- **Small-model reliability**: pilot cards must run on weaker agents; 15 of 34 have UNKNOWN expected value, 4 declared-not-sourced bands.
- **Release legal**: derived assets cannot ship; users must own both games (R-1).
- **Docs drift**: STATUS/ledger/tracker are three ledgers (stale-status-numbers.md); MODLOG lacks RC5.
- **BmSDK**: all 22 UObject/FName addresses UNKNOWN on GOG; repack exe is a dead end; Steam-only upstream. A Steam copy may not match the GOG installed packages (STATUS says same cooked packages; binary identity not verified).

## 7. (e) EFFORT ESTIMATE TO FINISHED, IN-GAME-VERIFIED, RELEASED

Assumptions (derived from file dates, not measured for the future): lanes get restarted; 3 lanes, hours not binding (53/53); a brief takes ~7-15 min of wall time but chains are serial; RC4 went from queue start (2026-11-06, wave D 8300) to VX (2026-11-07) in about 2 days for ~25 briefs plus reviews. The RC5 queue is 59 briefs (9001-9199), of which 9001-9004 and 9010-9019, 9030, 9051-9053 are done.

| phase | what | estimate (calendar days) |
|---|---|---|
| Restore lanes (NEW-INT-1/2) | operator action | 0.1-1 |
| Desk: 9031 -> 9033 serial | ~3 briefs | 0.5 |
| Desk: 91xx build wave (about 33 builds + 2 reviews, chain depth ~8) | 3 lanes parallel after 9101/9102 | 2-4 (depends on rewrites / over-budget failures) |
| Merge + verify + VX + pilot refresh + review (9190-9199) | 6 briefs in a 4-deep chain | 1-2 |
| Operator approval + calibration | operator availability | 0.5-2 |
| Q-0 (stock Serpente) | 1 sitting ~1 h plus card fixes | 1 |
| Q-1, Q-2, Q-3 | 3 sittings, each ~45 min planned, realistically 1-2 h with launch/menu issues | 3-5 |
| Fix loops | realistic count: **2-3 loops per original session on first contact** (collision, paint, steering/handling bands, weapons wiring are the usual failures; 0 rows verified and 110 queued), i.e. **~4-6 extra Q sessions in total**; each loop = triage + translate + rebuild + re-verify + reinstall = 1.5-3 days | 6-12 |
| QX, Q-5 showcase, R-1/R-2 | recording + lint + docs | 2-3 |

Total: **about 3-5 days to a candidate worth testing (RC5 VX)**, then **about 2-4 weeks** to QX-passed-or-named-omission, plus 2-3 days for release. Realistic total Q sessions: 1 (Q-0) + 3 planned + 4-6 fix sessions = **8-10 sittings**, with a wide error bar. If fix loops hit the backlog's "one extra session per original session" cap, the operator decides how to proceed (that rule is a stop, not a plan).

If RC4 is tested immediately (NEW-INT-18 option A): Q-0 and Q-1 can start as soon as the operator writes APPROVED_Q.txt and fills the calibration fields; but 4 reds + pursuit-only + 12/23 textures means most Q-1..Q-3 checks will be recorded as known-gap fails, so fix loops would be longer.
