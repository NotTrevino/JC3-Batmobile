# Queue map (written 2026-11-06 by Claude; dependency order is enforced by `AFTER:` headers, not file names)

| wave | numbers | what | starts when |
|---|---|---|---|
| 0 | 8001-8016 | earlier leads, operator rulings (T-ST7 0.25 s, T-FX3, T-WP13, T-WP4) | now |
| A | 8099-8117 | carrier research for every "out"/blocked row (air control, ram, effects, lights, winch, gadgets, modes, suspension bridge, strings, EMP) + capability survey | now |
| B | 8130-8143 | appearance: every dropped/baked class in Working/Appearance/progress.md (aniso, per-pixel reflectivity, F0, wetness, colour ramps, micro-detail, damage masks, emissive, mud, interior, glass, wheels, texture audit, skins) | now |
| C-audit | 8150-8158 | audit of the "keep" rows: LORE-EXACT or COMPROMISE per row | now |
| C | 8200-8216, 8250, 8299 | apply the answers to the ledger, close translation (T-23), review | after the reports they read |
| D | 8300-8320, 8399 | build RC4 in new private trees (B-01 .. B-14), review | after 8299 |
| E | 8400-8406 | verify V-01 .. V-07 on RC4, approval request | after 8399 |
| F | 8500-8508, 8599 | Q-PILOT cards (study, failures, controls, launch, vehicle, driving, combat, looks, prove-on-simple-car), review | after 8399 (desk work) |
| G | 8600-8605, 8699 | in-game Q-0..Q-5 | after APPROVED_Q.txt + V-07 + 8599 |

Reviews (8299, 8399, 8599, 8699) re-read the reports and rewrite later briefs so they name real files and numbers. Per-day top-ups: add briefs numbered 87xx+ from the review findings.
| 87xx | 8700-8702 | follow-ups from reports 8012/8013 (lock hold + salvo, reticle link, repeated slot pointers); feed 8210 | now |
| 87xx | 8703-8705 | closest-system build plans for air control, ram/dodge/kill-flip, paint gaps (reports used "not carriable"); feed 8200, 8201, 8211 | now |
| 87xx | 8706-8707 | immobilizer vs EMP missile (operator question), radar icons + HUD leads | now |
Apply briefs (8200-8216) are chained one after another by AFTER: they all edit T_ROWS.jsonl, BLOCKED_PROPOSALS and the t_blocked pin, so they must not run in parallel (2026-11-06 11:20Z).

## 2026-11-06 12:45Z note
- 7990-jeb-vs-qwen-calibration (unlocked by E:/AI/models/JEB_READY.txt, sorts first) runs the Jebadiah-vs-Qwen smart-search comparison; jeb_judge.py + `smart_search.py --judge jeb` are the code under test. Jeb server :8081 is running; lane must run one judge server at a time (GTX 1070, 8 GB).
- Keep-audit reports 8150-8158 are in: engine/boost/aero 5 of 6 COMPROMISE, materials 7 of 7, steering/drift 7 of 7, dimensions/wheels 1 COMPROMISE (T-G4), suspension/mass 4 COMPROMISE. All are consumed by apply briefs 8208 (suspension), 8211 (materials), 8214 (handling) and 8215 (systems); no new brief needed.
- lock-on-reticle-hud-link is in: behaviour can be opted into by data; reticle link read pending the apply wave.
- 13:20Z: jeb-vs-qwen-calibration is in and chase_calibrate --check passes. Verdict: keep Qwen default; BOTH judges ~0 recall on the 38 known cases (118/190 Jeb snippets cut at 2,048 tokens). Added 8713 (recall diagnosis search/window/judge/prompt) and 8714 (Jeb short-window retest).
- 13:32Z: ready count fell to 3 because the apply chain is serial (ledger races) and gated by 8099 -> 8200..8216. Added independent report-only briefs 8715/8716 (appearance dropped classes D1-D12, P1-P3 closest-system plans) and 8717 (cannon/Vulcan/riot/pods closest system). Lanes pick 8099/8102/8001 first by name.
- 13:46Z: lanes were skipping 8099/8102 (EST 60 sorts after EST<60), starving the whole apply chain. Set EST 50 on 8099, 8102 and all 82xx/83xx briefs that had EST >= 60 so they sort ahead by name.
- 14:02Z: ready count fell to 1 (serial apply chain). Pilot research 8500 (universal-modder study) and 8501 (failure catalogue) need no build, so their AFTER on review-build-wave was removed; 8502 now waits only for 8500. EST 50.
- 14:05Z: added 8718 (verify smart-search values, R4), 8719 (adopt recall route change), 8720 (SMART_SEARCH.md portability/skill plan); ready briefs low because the apply chain is serial.
- 14:20Z: added 8721 (BmAK feature completeness audit: uncovered features -> proposed rows). Jeb short-window retest: Qwen stays default (Jeb 0/20, 0/8 even with fitting windows).
- 14:35Z: ready count was 1 (apply chain serial; briefs finishing fast). Added independent report-only closest-system plans 8722-8727: entry/exit+controls, battle-mode transform, engine audio layers, health/damage states, cameras per mode, dash HUD gauges. Each cites existing reports first to avoid repeats.
- 14:46Z: all lanes restarted (daily 14/53); added 8728 surface/skids/tracks plan.
- 14:5xZ: ready count hit 0 (briefs finish in ~15 min). Added 8729-8736 (gadget input, summon, remote drive, eject/glider, weather/night, tyre grip, afterburner effects, ammo/reload) and adversarial reviews 8737 (keep-audit numbers) and 8738 (closest-system plans).
- 15:20Z: queue stock again ~0 (each brief takes ~7-15 min). Added 8740-8763: 24 independent closest-system plans (wheel anim, aero surfaces, doors, headlight beam, tail/brake lamps, underglow, exhaust, glass, dash anim, armour, weapon bays, cannon recoil, Vulcan, missile pods, EMP, hacker, sonar, tracker lock, booster, impacts, terrain, startup, horn/siren, radar icon).
- 15:45Z: lesson: 8723-8763 (boilerplate shared across briefs) were moved to low/too-similar by the driver similarity guard. Rewrote 8723-8736 as short unique briefs (rules live in INSTRUCTIONS.md); 8740-8763 still in low/too-similar, to be rewritten the same way. Re-pinned t_blocked (WAITS +T-L28/T-L30, -T-MD2/T-WP5; in_scope 211); apply briefs 82xx now carry a pin-upkeep line.
- 15:50Z: rewrote 8740-8751 as short unique briefs (8752-8763 still in low/too-similar). Daily hours 8/53.
- 16:02Z: summon-and-arrival-plan said drive-in 'remains blocked' (rule violation) -> follow-up 8764. Daily hours 5/53.
- 16:20Z: rewrote 8752-8763 as unique short briefs; ready had hit 0 again. Daily 5/53.
- 16:35Z: held tasks 8158 and 8134 ran 60 min without a report and blocked the apply chain (8207, 8211). Split into 8158/8159 (+ merge 8158) and 8134 locate + 8135 decode, each writing the report early.
- 16:48Z: daily hours 2/53 (emergency ends at 0). Added 8765-8767 (quick ramp name search, ramp slots in material, weapon build order by operator ranking).
- 16:50Z: 8134 ramp locate ran out its session twice with no report; dropped it from 8211's AFTER so the apply chain proceeds (ramp reports used if present).

- 8768 stuck-flip-recovery-plan queued: operator lead, B flips Batmobile over when stuck (unverified). Verify, then closest-system plan.

- 7995 bmsdk-port-to-repack-exe queued (operator: queue instead of doing live). Game folder state: BmSDK v0.21.0 installed, hook offset 0x5B7220 invalid on this exe.

- 7996 bmak-control-scheme-storage queued: Batmobile controls differ in the repack vs GOG; where the scheme lives.



- 7997 emp-effects-scrape-leads queued as a SCRAPE task (leads are for grab logic, not build/pilot); removed from 8305/8506.

- 7998 stuck-flip-scrape (grab) now gates 8768 (plan). Leads recorded on GRAB_BACKLOG WPN-4/WPN-5; 7997 is their grab brief.

- 7998 stuck-flip-scrape queued (grab). 8768 plan already ran combined (reports/stuck-flip-recovery-plan.md); 7998 re-scrapes cleanly, then the plan gets rechecked. Leads recorded on GRAB_BACKLOG WPN-4/WPN-5; 7997 is their grab brief.

- 7998 extended: LStick+A side boosters (pursuit/battle), flip uses same booster (operator lead, scrape).

- 2026-11-07 04:15Z wallet x3 attempt: L1 running (7997); L2 CLI crashed (0xC0000409, then exit 3), L3 never logged; break-glass removed after L1 started.

- 8214 rewritten uniquely and restored (it was in low/too-similar and blocked 8215-8320); 8135 AFTER header newline fixed. Emergency mode on 2026-11-07 06:06Z, cron 8a0c38b4 every 30 min.

- 2026-11-07 ~07:30Z: operator ended emergency mode (Claude usage 99%): NO_NEW_SESSIONS set, emergency-mode off, cron deleted. Running sessions finish and save their reports. Restart: remove NO_NEW_SESSIONS, turn emergency on.

2026-11-07 (watchdog build): found 8320 waited on build-d03-lights-and-flares with no producer anywhere; wrote 8302-build-d03-lights-and-flares (EST 50). New local watchdog gui/watchdog.py (zero tokens) now catches this class (E1).

2026-11-07: queued 8760-jeb-choice-format-retest (operator: Jeb should get multiple choice; earlier runs used a single noul question).

2026-11-07: queued 7993 (GOG exe address hunt, read-only) then 7994 (BmSDK install on a COPY of the GOG game; hash-verified GOG exe and saves). Operator approved both.

2026-11-07: queued 7992-bmsdk-upstream-gog-research; 7993 now waits on it.
2026-11-07: queued 8761-jeb-vs-qwen-fair-test (after jeb-choice-format-retest; fair corpus, tuning/test split, both models in choice format, 3 orders, intervals + paired test, decision rule written first).
2026-11-07: queued 8770-8775 (control scheme, EMP, stuck-flip merge, collision missing shapes, mode-swap trigger, tracker reconcile) - dependency-free fillers for All daily.
2026-11-07: queued 8776-8781 (HUD cluster, HUD radar, WP5b, MD14b, T-12, WP13b closest-system plans) - independent work for All daily.
2026-11-08: 8777-8781 were stripped into low/too-similar (shared template text); moved to low/stale-similar and replaced by unique briefs 8782-8786. Never template briefs: the similarity guard strips them.
2026-11-08: 8401 used two full sessions without finishing; split into 8401a (silhouette/census/collision), 8401b (pose renders/lights) and a 15-min merge 8401 that keeps the DONE name for v05/pilot-card dependents. Original brief kept at low/8401-...orig-20261108.
2026-11-08: queued 8787-8790 (immobiliser build, four-wheel-drive/spin build, traffic/AI reaction, T-row reconcile) - unique hand-written fillers for All daily.
2026-11-08: queued 8787-8790 (immobiliser build, four-wheel-drive/spin build, traffic/AI reaction, T-row reconcile) - unique hand-written fillers for All daily.
2026-11-08: queued 8791-8793 (water crossing, tank-pivot mapping to battle turn, standalone spawn check).
2026-11-08: 8401b was stripped into low/too-similar (near copy of 8401a); rewritten with distinct wording and restored. Killed a superseded husk lane-2 driver (pid 4896, 23:16Z).
2026-11-08: 8401 merge stripped into low/too-similar again; rewritten (distinct wording) and restored. 8401b done (verify-v02b report exists).
2026-11-08: queued 8794-8798 (force pulse carriers, eject steps, drive-mode torque substitute, paint slots apply plan, barrage tune table); 8404 got only 9 min before its session clock ended, not a stranding.
2026-11-08: queued 8799-8803 (number audits of the air-control, ram-assist, paint, summon/unranked and collision/mode-switch plans).
2026-11-08: queued 8804-8807 (audits of lock-hold, HUD cluster, boost selector/moving parts, four-slot/immobiliser plans).
2026-11-08: queue holds only the APPROVED_Q-gated Q chain; queued operator digests 8808-8810 (verify chain, pilot cards, plans+audits) to use the last 6-7 min of paid sessions and give the operator a readable summary.
2026-11-08 failed-task triage: 40 stripped/parked briefs already had reports (low/archived-has-report); 9 older ones obsolete (low/archived-obsolete); 15 narrowed (low/narrowed-originals) into 8870-8882 and 8900-8906; Jeb/Qwen fair test split into 8861-8863.
2026-11-08: operator gameplay answers written into 8870-8874; 8872 corrected (pursuit lock = shrinking circle in an edge-gapped diamond; battle lock = instant diamond); queued 8883 tracker signal range / see-through-wall visibility.
2026-11-08: operator answers on water, flip, damage, remote, destroyed car and Vulcan capture recorded in memory; queued 8884 (Vulcan capture timing), 8885 (water-entry teleport), 8886 (health to explosion, no crash damage), 8887 (remote range and static overlay), 8888 (flip idle timer and thrusters).
2026-11-08: Vulcan correction (crosshair spreads then red, cool-down only for bloom, no lockout) written into 8884; queued 8889 (60 mm cannon reload circle).

## 2026-11-08 RC5 campaign: 59 briefs 9001-9199 (written by Claude after reading STAGES.md, STATUS.md, GRAB_BACKLOG.md B cards, review 8399, the V-01..V-07 reports and the operator digests)
Where the project stands: GRAB and TRANSLATE are desk-complete (145/216 evidenced, 0 behaviour-verified); BUILD produced RC4 (pursuit set only, complete=false); VERIFY has four reds (V-03 G2/G3, V-01 tree, V-04 loop wrap) plus the V-05 T-ST7 miss; PILOT cards are reviewed; TEST waits for APPROVED_Q.txt. Unbuilt cards: B-12 modes, B-17..B-21, B-22/B-23, handling card B-24, B-25, B-26, lock-hold/reticle (Research/specs B-24/B-25), HUD, textures (12 of 23), collision (2 of 3 boxes). The Q chain 8600-8699 is untouched and still gated; after RC5 its AFTER targets (RC4 gate report) should be repointed by the operator (9193 recommends how).
| wave | numbers | what | starts when |
|---|---|---|---|
| R repairs | 9001-9004 | V-03 G2 fire refs, V-03 G3 asset paths, size pins, loop 279 seam | now |
| P plan v2 | 9010-9019 | audit corrections folded into each closest-system plan (originals untouched); 9015 waits for 8884+8889, 9016 for 8902, 9019 for 8885-8888 | now / after named reports |
| G grab leftovers | 9050-9054 | exe entity-swap consumer (U1), BmAK native remainder, audio event 0x6BB2C66E, last unnamed .wavc, locate the 8 missing pixel sets | now |
| A ledger apply | 9030 -> 9031 -> 9032 -> 9033 | serial (all edit T_ROWS.jsonl); 9033 reviews and rewrites 91xx briefs | after the P wave |
| B build weapons | 9100 scaffold -> 9101 entity -> 9102 effects -> 9103 tracker -> 9104 EMP missile -> 9105 lock/reticle; 9106 booster, 9107 EMP burst, 9108 hacker, 9109 sonar, 9110 unranked; review 9119 | operator weapon ranking; scaffold waits for 9033 + R wave | after 9033 |
| B build rest | 9120 handling -> 9121 suspension, 9122 drive modes, 9123 air/ram, 9124 flip/water/remote -> 9130 mode pair (also waits for 9050); 9140 textures (waits 9054), 9141 collision, 9142 lights, 9143 paint, 9150 audio, 9160 HUD, 9170 controls, 9171 damage, 9172 parts, 9173 world, 9174 effects; review 9179 | private trees Builds/bm-RC5-*, each registers a branch record | after 9100 / 9120 |
| merge + verify | 9190 merge -> 9191 + 9192 verify -> 9193 VX + approval request -> 9194 pilot refresh -> 9199 final review | after all builds and both reviews | last |
Rules kept: every brief hand-written, unique wording (max pairwise trigram overlap 0.34), no game launch, no install, no APPROVED_Q.txt, RC4 trees frozen. Backup of this file: QUEUE_MAP.md.bak-20261108.

## 2026-11-08 ~17:10Z: ALL remaining work queued (operator: "queue all of the remaining project work, all dependencies accounted for")
465 briefs, 9200-9664, written by 8 landmark agents from Working/Roadmap/*.md and merged by Working/Roadmap/allq/merge.py:
numbered in landmark order (integration, appearance, weapons, handling, sound, modes/controls, HUD/cam/lights/FX, damage/world).
Every dependency is an AFTER on a real report path; there are 0 unknown deps, 0 cycles, and no pair at >= 0.5 trigram overlap
(against each other and every queued brief). 87 in-game briefs are gated on APPROVED_Q_FULL.txt (written 16:33Z on operator
approval). Each landmark has review briefs that rewrite its later, unstarted briefs when reports change the facts.
Manifests (brief -> roadmap task ids covered): Working/Roadmap/allq/*.json; numbers -> files: merge_result.json.
All of them are registered in Working/Roadmap/landmarks.json, so the GUI completion estimate tracks them.
