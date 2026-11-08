# SOUND landmark - task map (as of 2026-11-08, read-only survey)

Rule applied: nothing here rests on pretrained JC3 knowledge; every claim cites a repo file. UNKNOWN where absent.
Stage key: GRAB / TRANSLATE / BUILD / VERIFY / PILOT / TEST / RELEASE. Size: S<=1 session, M 1-3, L 1-2 wk.
Path shorthand: RPT = tmp/freebuff/reports ; BG = Research/BatmobileGrab ; WT = Working/Translation ; Q = Working/Q.

## 0. State in one paragraph
The BmAK side is fully decoded and the JC3 side is fully measured; what ships today is **5 sample swaps** in two private bank copies (vehicles.bank, weapons.bank), same file sizes, pursuit set only. 24/45 donor GUIDs resolve in our vehicles.bank, **21/45 (19 effects + 2 character) are donor** (RPT/correction-8393-donor-audio-guids.md). **Nothing has been heard in-game since test-060** (nitro swap: "LOADS, ALIGNED, QUIET", MODLOG.md:3882; the whine itself was only spectrum-checked, MODLOG.md:3806-3815) and the test ban stands (Working/Q/APPROVAL_REQUEST.md). All RC5 audio work (9150) is not started (Working/RC5 and Builds/bm-RC5 do not exist; Builds/bm-RC5-audio holds only the loop-seam repair).
The structural ceiling: **JC3 banks are FMOD Designer/Ex FEV v56; events live in an unshipped FEV graph, so no new event can be authored (route b refused) and there is no FSB5 writer in the repo** (RPT/engine-audio-layers-plan.md s6.3; Research/JC3Grab/JC3_AUDIO.md s10; Working/Translation/T_MD14B_BANKS.md s0). BmAK audio can therefore only ride existing JC3 events by sample-swap in place (same size/frames), unless a loader / FSB5-writer / FEV route is found.

## 1. Task table

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-15 | Decode BmAK audio by feature (361 events, 447 WEMs, 423 decoded, 506 RTPC bindings) | GRAB | done | - | T-16 | M | BG/AUDIO_FEATURES.md ; GRAB_BACKLOG.md:1822 |
| G2-24 | JC3 vehicle audio system census (45 donor GUIDs, 257 events, 649 samples, routes a/b/c) | GRAB | done | - | T-16, B-11 | M | Research/JC3Grab/JC3_AUDIO.md ; GRAB_BACKLOG.md:1846 |
| G2-23 | Nitro chain + audio carriers (event f74ea43b, EVTS 249, nitro start/loop/stop samples) | GRAB | done | - | A-02 | S | Research/JC3Grab/USAGES.md s6 ; GRAB_BACKLOG.md:1845 |
| G3-14 | BmAK banks referenced vs present (29/29 present; T-AU3/T-AU5 "absent" refuted) | GRAB | done | - | T-AU3, T-AU5 | S | BG/AUDIO_BANKS.md ; GRAB_BACKLOG.md:1920 |
| G3-06e | Vehicle audio objects decode (AkVehicleSound x4, AkDialogueComponent x1) | GRAB | todo | G3-14 (met) | AUD-1, AUD-3 | S | GRAB_BACKLOG.md:1909 |
| 9052 chase (0x6BB2C66E) | Locate event 0x6BB2C66E | GRAB | done: no missing bank. AkEvent `Play_BatSniperRifle_Vehicle_Tracking_Fire` (0x6BB2C66E) is a per-character twin; the cooked event is `Play_Disruptor_Vehicle_Tracking_Fire` 0x8EA6FCA0 in CHR_BatmanDisruptor. STATUS.md:99 still says UNKNOWN (stale) | - | tracker-fire sound | S | BG/AUDIO_EVENT_6BB2C66E.md ; RPT/audio-event-6bb2c66e-bank-chase.md |
| T-16 | Audio translation map (53 rows: 5 mapped, 7 kept vanilla, 11 named omission, 1 remove, 29 blocked) | TRANSLATE | done | - | B-11 | M | WT/T12_AUDIO.md ; WT/t12_audio_map.json |
| T-AU1 | LandAudio min/max rpm 1000/10000 kept; event->param edge undecoded | TRANSLATE | done (keep) | - | - | S | WT/T_ROWS.jsonl ; RPT/keep-audit-audio-fx.md |
| T-AU4 | LandAudio.max_rpm 10000 -> 4500 (follows T-E1) | BUILD | queued (edit row, not in a build) | T-E1 | AUD-1 pitch ceiling | S | WT/T_ROWS.jsonl (T-AU4) |
| T-AU2 | Engine start/loop sample swap (1 of 3 banks) | BUILD | partial (vehicles only; 21 GUIDs donor) | B-26 | - | M | WT/T_ROWS.jsonl ; RPT/correction-8393-donor-audio-guids.md |
| T-AU3 | Bind 26 BmAK event ids (10 banks, 90 rows) to JC3 event slots | TRANSLATE | queued (`next`; banks proven present; JC3 binding + per-event media extraction missing) | NEW-AUD-1, NEW-AUD-2 | AUD-2..6 | L | WT/AU_BLOCKED_RETEST.md ; WT/T_AU3B.md |
| T-AU5 | TransformationReverseDirection* / TaserSound / VehicleSound: bank + slot | TRANSLATE | queued (`next`; their bank UNKNOWN, not among the 361 AUDIO_MAP rows) | NEW-AUD-3 | AUD-4 | M | WT/AU_BLOCKED_RETEST.md |
| B-11 | Audio bank: 2 private bank copies, 5 payload swaps, .fmod_guids 45 re-emitted, installer | BUILD | done (RC4 tree) | - | V-04 | M | Working/Audio/bm_bank_manifest_rc4.json ; Builds/bm-RC4-audio/receipt.json ; GRAB_BACKLOG.md:1954 |
| A-02 | AUD-2 nitro start/loop/stop swap (loop = vehicles#151) | BUILD | done (static) | - | in-game listen | S | Builds/bm-RC4-audio/events.json |
| A-05 | Chassis spin creak loop vehicles#279 (BmAK Play_Batmobile_Rotation) | BUILD | done static; RC5 seam repair measured 0 LSB | - | in-game listen | S | Builds/bm-RC5-audio/verify/loops_rc5.md |
| A-06 / A-07 | Cockpit open/close one-shots (vehicles #7, #98) | BUILD | done (static) | - | in-game listen | S | WT/T12_AUDIO.md |
| W-03 | Minigun/Vulcan fire loop swap (weapons #408) | BUILD | done (static) | - | in-game listen | S | Builds/bm-RC4-audio/verify/audio.md |
| V-04 | Audio gates (decode, length, loudness +-1 LU, loop seam <= -40 dBFS, tail) | VERIFY | partial: RC4 loop gate RED (vehicles#279 -38.03 dBFS), loudness 5/5 green | in-game confirmation | RC release | S | Builds/bm-RC4-audio/verify/audio.md ; GRAB_BACKLOG.md:1979 |
| 9004 rc5-loop279 | Loop seam repair 3/3 <= -40 dBFS (decoded + payload) | BUILD | done (tree Builds/bm-RC5-audio, static only) | - | 9190 merge | S | RPT/rc5-loop279-wrap-build.md ; Builds/bm-RC5-audio/verify/loops_rc5.md |
| NEW-AUD-0 | Re-run official V-04 gate on the RC5 merge and flip V-04 RED to GREEN in tracker | VERIFY | queued (inside 9191) | 9190 | RC5 | S | tmp/freebuff/queue/9191-rc5-verify-files-wiring-audio.txt |
| 9150 | RC5 audio: private effects-class bank + per-entity SAttachedEffect binding + engine-layer / horn / idle / afterburner / battle-audio plans + 0x6BB2C66E event; tree bm-RC5-audio2, script rc5_audio2.py | BUILD | queued, not started | 9100 scaffold | 9190 | L | tmp/freebuff/queue/9150-rc5-audio-override-and-layers.txt |
| B-26 | Per-entity audio override: 21 of 45 GUIDs (19 effects, 2 character) | BUILD | todo (no payload in RC4; entity-level bank override honoured? UNPROVEN) | NEW-AUD-4 | AUD-2, T-AU2 | M | GRAB_BACKLOG.md:1608 ; Research/specs/B-26.md |
| 9191 | Verification group A incl. V-04 on RC5 | VERIFY | queued | 9190 | 9193 | S | tmp/freebuff/queue/9191-rc5-verify-files-wiring-audio.txt |
| AUD-1 | Engine start/idle/RPM layers (BmAK: 11 RPM layers MK1 / 9 MK2 + 5 non-RPM) | BUILD | partial: plan only; A-01 `engine_running_sound` (905be2e5, vehicles/146) blocked: which sample family the donor tune plays is UNKNOWN | NEW-AUD-5, NEW-AUD-6 | AUD-4, listen tests | L | RPT/engine-audio-layers-plan.md ; WT/T12_AUDIO.md A-01 |
| NEW-AUD-1 | Extract/decode media for the 10 "found" banks (sonar 6 events, impacts, disruptor/tracker, UI_InGame lock, tank heavy lock beep, tank missiles, explosion, rolling objects, jump/subjective = 90 rows). AUDIO_FEATURES shows media 0 / "missing-bank" for them: re-grab from the G3-14 carriers | GRAB | todo | - | T-AU3, all gadget/lock/death/impact sounds | M | BG/AUDIO_FEATURES.md (sonar, tracker, lock-on-ui, death, impacts = 0 WEMs) ; WT/AU_BLOCKED_RETEST.md s3 |
| NEW-AUD-2 | Per-event JC3 binding for the 26 ids: closest JC3 event + gap each (closest-system rule); auditionable candidates | TRANSLATE | todo | NEW-AUD-1 | T-AU3 | M | memory/closest-system-rule.md ; WT/T_AU3B.md |
| NEW-AUD-3 | Locate bank for TransformationReverseDirection*, TaserSound, VehicleSound (only 4 Playable_Batmobile* packages were scanned) | GRAB | todo | - | T-AU5, AUD-4 | S | WT/T_ROWS.jsonl (T-AU5) |
| NEW-AUD-4 | 5-minute experiment: is a per-entity SAttachedEffect to a private bank honoured, or does a loose effects.bank apply to every vehicle? Decide B-26 route (override / accept global / stated gap) | TEST | todo | operator launch approval | B-26, 9150 | S | GRAB_BACKLOG.md:1621 (Stop clause) |
| NEW-AUD-5 | FSB5 sample-add tool (or prove impossible); also test whether master.banklist accepts an extra bank file | BUILD | todo (no writer exists) | - | pitch bend, reverse bed, clutch, ticks, battle engine | L | RPT/engine-audio-layers-plan.md s6.3 ; WT/T_MD14B_BANKS.md s0 |
| NEW-AUD-6 | Audition: which family does the engine_running_sound tune (146) play; tune->sample is not stored (0/649), so solo-swap by listening | TEST | todo | operator in-game, test ban | A-01, AUD-1 | M | WT/T12_AUDIO.md A-01 ; Research/JC3Grab/JC3_AUDIO.md |
| NEW-AUD-7 | Engine RPM layer build: reuse the 9 shipped families (idle, persist-idle, band RPM x3, gain layers, start/shutdown, gearshift) driven by rpm/rpm_norm/load params; LandAudio 1000-4500 | BUILD | todo | NEW-AUD-6, T-E1 | AUD-1 | L | RPT/engine-audio-layers-plan.md s6.1, s2 |
| NEW-AUD-8 | Engine start/stop transition (Play_Batmobile_Engine_Transition_In, Startup RTPC 0 crank / 1 run) into the start/shutdown slots | BUILD | todo | NEW-AUD-6 | AUD-1 | M | RPT/idle-and-startup-plan.md ; engine-audio-layers-plan s6.1 |
| NEW-AUD-9 | Gear-shift loudness (3 shift slots +3.5..+3.7 LU outside gate) and A-04 resolution | TRANSLATE | blocked | Q-2 A9 listen | AUD-1 | S | WT/T12_AUDIO.md (summary, A-04) |
| AUD-2 burnout | BML_Burnout (31 rows / 10 events / 141 WEMs): burnout and boost layers beyond nitro | BUILD | partial (nitro start/loop/stop only; nitro start slot -1.59 LU outside gate) | NEW-AUD-5 | - | M | BG/AUDIO_FEATURES.md ; WT/T12_AUDIO.md |
| NEW-AUD-10 | Afterburner audio timing per element (boost 2.0 s, cooldown 12.0 s); nitro start gain fix; tag->button for boost UNKNOWN | BUILD | todo | tag->button UNKNOWN (G2-23) | AUD-2 | S | RPT/afterburner-effects-audio-plan.md ; GRAB_BACKLOG.md:1845 |
| AUD-3 / A-11 | Interior/cabin layer AUX_InBatmobile (9 events / 22 WEMs; 35 rows incl. RainDensity/Speed RTPC) | BUILD | partial: named omission (no JC3 interior event); nearest speedwind_sound_player is a character-bank GUID | B-26 / NEW-AUD-4 | - | M | WT/T12_AUDIO.md A-11 ; BG/AUDIO_FEATURES.md |
| AUD-4 / T-MD14 | Battle-mode transform in/out + 30 battle events + steering bed (event 0xD28CAFB1) | BUILD | blocked (named omission in RC4) | D-2 / 9130 mode pair, NEW-AUD-3, NEW-AUD-5 | MOD-2 | L | RPT/battle-audio-switch-event.md s4 ; WT/T_MD14B_BANKS.md |
| NEW-AUD-11 | Interim battle audio via a second EngineNitro-style usage (fires on boost input) - report calls it a compromise | BUILD | todo (needs operator via Claude) | operator decision | AUD-4 interim | M | RPT/battle-audio-switch-event.md s4 |
| NEW-AUD-12 | Two-entity mode pair carries the battle audio set (entity B .fmod_guids) | BUILD | blocked | D-2 option (a); swap trigger UNKNOWN (U1, 9050) | AUD-4 | M | GRAB_BACKLOG.md:1796 ; tmp/freebuff/queue/9050-exe-entity-swap-consumer.txt |
| AUD-5 weapons | Every weapon fire/loop/tail/impact/lock (7 weapon rows, 10 WEMs): cannon, missiles (RocketTails, lock beep), tank heavy | BUILD | partial: Vulcan loop swapped; W-01/04/05/06/07 named omission (BmAK media absent, see NEW-AUD-1) | NEW-AUD-1 | - | L | WT/T12_AUDIO.md W-01..W-07 |
| NEW-AUD-13 | Lock/UI beeps: Play_HUD_Missile_Lock, Play_Tank_Heavy_LockBeep / Locked: decode and map (JC3 lock-duration member UNKNOWN) | TRANSLATE | todo | NEW-AUD-1 | HUD-2 lock diamond | M | WT/T12_AUDIO.md W-07 ; Working/Q/PREDICTIONS_ALL.md Q3-3 |
| NEW-AUD-14 | Gadget audio: sonar (BML_Sonar 6 events), tracker (Deploy + fire 0x8EA6FCA0), EMP (only Immobiliser_Impact in VFX_Tank_Explosion; emp group 0 rows), carriers + import rows | TRANSLATE | todo (B-20 owns sonar audio ids; B-20 no payload in RC4) | NEW-AUD-1, B-20 | gadget lanes | M | GRAB_BACKLOG.md:1498, 1966 ; OPERATOR_PRIORITIES.md:37 |
| NEW-AUD-15 | Hacker / SAM-hack / winch sounds: confirm BmAK has any (AUDIO_FEATURES groups emp 0, winch 0); record lore-absent vs omission | GRAB | todo | player answer (c5) | gadget lanes | S | BG/AUDIO_FEATURES.md |
| AUD-6 | Tyres, skids, impacts: BML_Tyres, BML_Impacts (16 rows, 0 WEMs); JC3 ground_roughness / TireDestroyed / dynamic_break kept vanilla | BUILD | partial: named omissions (A-09, A-16..A-22 kept vanilla) | NEW-AUD-1 | - | M | WT/T12_AUDIO.md ; BG/AUDIO_FEATURES.md |
| NEW-AUD-16 | Tyre/skid layers from BML_Tyres + Drift/BML_Slide RTPC: choose JC3 skid slot | TRANSLATE | todo | NEW-AUD-5, NEW-AUD-6 | AUD-6 | M | BG/AUDIO_FEATURES.md burnout group |
| NEW-AUD-17 | Death explosion: Play_Batmobile_Destroyed 0x3531A5D5 (BML_Impacts); JC3 `explosion` d167a490 and fire_post_explosion live in shared effects.bank | BUILD | blocked (named omission) | B-26, NEW-AUD-1 | - | M | WT/T12_AUDIO.md A-14, A-15 |
| AUD-7 | Horn/radio: BmAK has no horn event, no horn input (3 proofs); JC3 radio 0/232; row A-13 `remove` the horn object (fd69c63c; 178 vehicles carry one) | BUILD | partial: decided remove, apply + verify pending (B-04) | B-04 apply | - | S | RPT/horn-and-siren-plan.md ; WT/T12_AUDIO.md A-13 |
| NEW-AUD-18 | Weapon-warning alert (FBatmobileWeaponWarningContainer AkEvent) and Play_HUD_fail 0xDEAD7680 mapped | TRANSLATE | todo | NEW-AUD-1 | HUD warn | S | RPT/horn-and-siren-plan.md |
| NEW-AUD-19 | Voice lines (28 rows / 20 events / 91 WEMs; 24 streamed lines carry no bytes on disk): in scope or lore-omit | TRANSLATE | todo (operator decision) | player answer (c7) | - | S | BG/AUDIO_FEATURES.md ; GRAB_BACKLOG.md:1822 |
| NEW-AUD-20 | 22 unnamed donor GUIDs D-01..D-22: audition whether audible on the car, then kept vanilla | TEST | blocked | Q-1 session | T-16 closure | M | WT/T12_AUDIO.md |
| NEW-AUD-21 | Water/sinking/turbo-jump/jump-wind dispositions (A-03, A-08, A-10, A-12, A-23) after D-8, D-10 | TRANSLATE | blocked | D-8, D-10 | - | S | WT/T12_AUDIO.md |
| NEW-AUD-22 | Whole-bed mix balance (engine + wind + weapons); only per-slot +-1 LU is gated today | VERIFY | todo | NEW-AUD-7 | PILOT | M | WT/T12_AUDIO.md summary |
| NEW-AUD-23 | Install/rollback of banks on the real dropzone (loose banks override archive; 210,781,376 B + 177,586,080 B; rehearsed offline only) | TEST | queued | operator approval (APPROVED_Q.txt absent) | all listen tests | S | Builds/bm-004/receipt.json ; Working/Q/APPROVAL_REQUEST.md |
| Q-1 / Q1-8 | Audio at standstill: start, idle, rev sweep, boost blip, doors, horn silent, weapons, explosion, break sounds | PILOT | queued (test ban) | NEW-AUD-23 | Q-2 | M | Working/Q/PILOT/AUDIO.md ; Working/Q/PREDICTIONS_ALL.md Q1-8 |
| Q-2 A2, A9, A10 | nitro hit, 0-100 shift with audio, handbrake spin creak | TEST | queued | Q-1 | V-04 close | M | WT/T12_AUDIO.md |
| Q-3 #3, #4, #7 | Weapons at target, lake, damage-state audio | TEST | queued | Q-2 | - | M | WT/T12_AUDIO.md |
| NEW-AUD-24 | Loop-gap listening check of the 3 loops, `um win record` WITH audio (QA-1 lost rpm channel with --no-audio) | TEST | queued | NEW-AUD-23 | V-04 | S | GRAB_BACKLOG.md:1685 |
| T-AU3/T-AU5 sign-off | Compromise approval for named audio omissions (lanes recommend, user approves via Claude) | RELEASE | todo | all above | release gate | S | memory/compromise-approval.md ; WT/COMPROMISES_T.md:45-46 |
| NEW-AUD-25 | Release notes audio section (BmAK vs donor sounds, loose-bank install, rollback, ~388 MB of banks) | RELEASE | todo | final decisions | release | S | GRAB_BACKLOG.md:1774 |
| NEW-AUD-26 | Ledger hygiene: STATUS.md:99 says 0x6BB2C66E UNKNOWN; AUDIO_FEATURES media-0 rows stale vs G3-14 | RELEASE | todo | - | - | S | STATUS.md:99 ; BG/AUDIO_EVENT_6BB2C66E.md |

## 2. (a) Done, with evidence
- BmAK decode: 361 events / 447 WEMs (423 decoded) - BG/AUDIO_FEATURES.md; 29 banks present - BG/AUDIO_BANKS.md; 117-payload search for 0x6BB2C66E - BG/AUDIO_EVENT_6BB2C66E.md.
- JC3 audio census (45 GUIDs, 257 events, 649 samples, FEV v56 build 50) - Research/JC3Grab/JC3_AUDIO.md, JC3_AUDIO_EVENTS.json.
- T-16 map 53 rows - WT/T12_AUDIO.md; keep audit - RPT/keep-audit-audio-fx.md.
- B-11 RC4 banks: 5 swaps, sizes unchanged, 45 GUIDs re-emitted, installer rehearsed offline, 5/5 tampers caught - Builds/bm-RC4-audio/receipt.json, Builds/bm-004/receipt.json.
- V-04 loudness 5/5 (RC4); loop RED then repaired statically 3/3 in Builds/bm-RC5-audio/verify/loops_rc5.md.
- Only in-game evidence ever: test-060 loaded and aligned (MODLOG.md:3882); audio not reported heard.
- Read-only plans: engine layers, idle/startup, afterburner, battle-audio, horn - RPT/*-plan.md.

## 3. (b) BLOCKERS, root first
1. **Test ban / no operator launch approval** (tmp/freebuff/APPROVED_Q.txt absent by design; Working/Q/APPROVAL_REQUEST.md). Every "heard in game" item waits.
2. **No FEV authoring and no FSB5 writer**: new events/samples impossible; 6 mandatory engine layers + battle engine + reverse + clutch + ticks stay wrong/silent (engine-audio-layers-plan s6.2-6.3). Needs NEW-AUD-5 or another carrier.
3. **Shared effects.bank / character.bank**: 21/45 GUIDs cannot be swapped per vehicle; B-26 route unproven (NEW-AUD-4).
4. **tune->sample not stored** (0/649): slot choice is by name + audition, so A-01 and the 22 unnamed GUIDs need listening (NEW-AUD-6, NEW-AUD-20).
5. **JC3 has no mode flag** (battle audio, D-2 reopened, swap trigger U1 UNKNOWN): AUD-4 / T-MD14 blocked on 9130 + 9050.
6. **Media extraction gap**: ~90 events of 10 banks decoded only as ids - NEW-AUD-1 gates lock beeps, sonar, tracker, death, impacts, tails.
7. Pipeline chain: 9100 scaffold -> 9150 -> 9190 merge -> 9191 verify -> 9193 gate -> approval -> pilot.

## 4. (c) Questions only the player can answer (BmAK/JC3 sound)
1. Engine: at idle vs throttle, is the turbine whine or a V8 growl the identity sound? Which 3 layers matter most if only 3 fit?
2. Does the engine pitch audibly bend with RPM, or is it mostly a volume crossfade?
3. Battle mode: are the transform in/out stingers heard gear-by-gear (In_A..F, Out_A..H)? Is the steering bed audible turning on the spot? (Per memory/decision-rule-lore-accuracy.md compromises are not asked; the interim NEW-AUD-11 must go through Claude.)
4. Does the cabin sound change in cockpit camera; does rain change it?
5. Does BmAK have any audible horn, EMP, SAM-hack, winch or radio sound? (AUDIO_MAP has none.)
6. Which weapon sounds are signature: cannon boom, Vulcan spin-up/down, missile whoosh, lock-beep rate?
7. Are Oracle/Alfred voice calls during driving in scope?
8. In JC3 today: is the swapped nitro whine audible over wind and engine when boosting (test-060 never reported)?
9. Is there a distinct tyre screech on drift in BmAK, or only engine/pitch change?

## 5. (d) Risks
- Same-size splice forces stretch/clip/pad of each BmAK sample into a donor slot; long loops may sound different.
- Loose banks (210 MB + 177 MB) override the archive; a game update or other mod can desync to silence/crash; rollback rehearsed offline only.
- Swapped slots (nitro, door, minigun) live in shared vehicles.bank/weapons.bank, so other vehicles/weapons using those events probably play BmAK sounds. Not surfaced in RC4 docs; UNKNOWN until NEW-AUD-4.
- LandAudio rpm window and event->param edge may not be tunable (UNKNOWN).
- Stale docs (STATUS.md:99, AUDIO_FEATURES media-0) can mislead small models.
- Lore-accuracy rule vs FEV ceiling will force named omissions needing sign-off.
- The -40 dBFS loop threshold is a brief-set number with no listening validation yet.

## 6. (e) Remaining effort
Open rows: about 38 (4 GRAB, ~9 TRANSLATE, ~12 BUILD, ~8 TEST/VERIFY, ~4 PILOT/RELEASE).
- Agent-only work (extractions, maps, 9150 build, 9191 verify, builds NEW-AUD-7/8/10, doc hygiene): about 35-45 briefs (M/L need 2-3 each), roughly 0.5-1 day throughput at 100/day but serial chain 9100 -> 9150 -> 9190 -> 9191 stretches it to about 3-4 calendar days.
- Operator-gated listening (NEW-AUD-4, -6, -20, -23, -24, Q-1/2/3 audio): about 4-6 human sessions of 30-60 min, plus 2-3 fix loops each: about 5-8 calendar days after launch approval.
- Wildcards: NEW-AUD-5 (FSB5 writer) is L and may be impossible; AUD-4 depends on D-2 / 9130 / 9050 (outside this landmark).
- Estimate to in-game-verified sound with named omissions for battle / interior / extra layers: about 8-12 calendar days, about 45 agent-sessions + 5 human sessions. Full lore-accurate sound (battle + layers + interior): UNKNOWN, gated by NEW-AUD-4, -5, -12.
