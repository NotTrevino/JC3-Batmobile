"""Append the review-8299 correction line to the not-yet-run build/verify/pilot briefs.

Never deletes or rewrites a brief: opens in append mode, refuses a brief that
already carries the line, and reports any named brief that is absent.
"""
import os
import sys

Q = os.path.join("tmp", "freebuff", "queue")
MARK = "Updated by review 8299"

UPDATES = {
    "8300-build-d01-scaffold-rc4.txt":
        "Updated by review 8299: BUILD_BATCHES.md carries 19 artefacts (17 payloads + 2 records) over 24 B steps and "
        "B-17\u2026B-20 are declared no-payload gates (t23_closeout.py --check is green at decisions 11/11). The live ledger "
        "is 199 rows / 35 edits over 16 rows; test-091 stays the identity base. Do not gate on t_boost_rows.py or "
        "t_vnf_six.py \u2014 both still fail on a hard-coded 198-row pin.",
    "8301-build-d02-parts-split.txt":
        "Updated by review 8299: bm-RC2 carries 61 parts (42 bm-009 parts + 19 B-04 additions, incl. wheel-arch parts "
        "42/43), 19 damage types with 4 fallback types (Boat_Antenna, Boat_Generic, Plane_Control_Surface, "
        "Train_Generic); T-P2's 42-part denominator is stale. The parts payload is the parts batch in BUILD_BATCHES.md; "
        "keep 99.9% silhouette as the gate (RC2 passed by 0.0004).",
    "8302-build-d03-lights-and-flares.txt":
        "Updated by review 8299: t18_lights.py --check is 28 rows = 26 mapped + 2 named omissions (T-L28/T-L30), 22 "
        "targets (11 donor rows + 1 graph object + 10 custom), 18 built rows (21-10+7). T-LG6 carries Range "
        "60/45/40.96/20.48/10.24/4/1.5/0.8 (60 and 45 above the fleet max 50, declared R3), OuterCone "
        "70/60/50/44/35/15, multiplier clamp(5 x Brightness, 0.5, 5) = 0.75/5, blinking 0. The 17 lens-flare entries "
        "are card B-25 (part-side emitters + the light-unit probe) \u2014 do not count them as delivered lamp rows.",
    "8303-build-d04-materials-textures.txt":
        "Updated by review 8299: TEXTURE_BUILD_PLAN.md has 23 rows and 12 have no faithful route \u2014 4 chapter damage "
        "masks (D9, one static state only) and 8 textures whose pixels are absent (Batmobile_Micropattern_A/_Normal/B/C, "
        "Batmobile_V3_Wheel_E, Batman_BM3_V2_Lacquered_Underlayer_Ramp, Batman_BM3_V2_Leather_Ramp, "
        "Batmobile_V3_Body_ColourRamp). Do not forecast a percentage rise: appearance_progress gives overall 54.6%, "
        "strict 49.3%, of-slotted 91.1%, textures 53.9% (17/38 transferred + 7 partial); plan tally bake 23 / route 61 "
        "/ drop 88.",
    "8304-build-d05-entity-graph.txt":
        "Updated by review 8299: the .epe consumes 8 forced slots (4 CCar roots x main_weapon + id:00568A74) with 5 "
        "gadgets outside the slot space, the T-WP4 split (w618 clone + CForcePulse + w143 guidance + a new lock-on "
        "AutoAim), the winch anchor objects, and B-12's precondition 3 (runtime swap UNKNOWN, "
        "mode-switch-carriers.md \u00a77 U1). B-26 (per-entity audio override, 21 of 45 GUIDs) is entity-side too \u2014 name "
        "it in the object count if it lands here.",
    "8305-build-d06-weapons-tunes.txt":
        "Updated by review 8299: t7_weapons.py --check now reads 15 rows = 13 WPN codes + 2 decision rows, 13 with a "
        "JC3 carrier, 1 named omission, 1 blocked (apply-gadget-rows' '0 named omissions' and apply-riot-mode-rows' "
        "'4 named omissions' are both stale). Riot is B-15 (base_tuning.damage 0 + impulse + 0.75 s cadence, a second "
        "weapon entity); RiotSuppressorMuzzle has no point and the Joker weapons have no sockets. The "
        "lock-hold/salvo/reticle gap has no card \u2014 t_blocked.py mis-cites B-24/B-25 (handling, flares).",
    "8306-build-d07-effects.txt":
        "Updated by review 8299: T13_FX.md is 17 rows, 17 chosen carriers, 0 named omissions; the private-effect work "
        "is B-17 (writer). Five rows still carry no BmAK number: T-FX20 brake-trail width/length/colour (no "
        "ParticleSystem template; float at @364 unnamed), T-FX12 tracer colour/material (enum 1, .ddsc unnamed); "
        "T-FX9/T-FX16 ride shipped effects. T-FX5's '23 unreferenced .effc' is UNKNOWN \u2014 the producer never states "
        "what it counted.",
    "8307-build-d08-health-collision.txt":
        "Updated by review 8299: the drivable collision is decoded \u2014 Physics.Batmobile_V3_Physics = 2 bodies / 3 boxes "
        "/ 1 constraint (chassis 690.305x374.536x207.5 @ (9,0,106.75) and 679.585x345.688x103.5 @ (0,0,79); pod "
        "166.177x189.365x39.8 @ (-30.5,0,93.25) at 4.000 deg). Use T22_REOPEN.md + t22_reopen.py --check, not the old "
        "convex-hull plan and not the '3 boxes + 56 convex' premise still in t16_collision_keepaudit.json. The 5 cm "
        "gate is against the chassis boxes and the pod; 62 donor bodies stay, 2 shapes are missing, 0 of 54 hull slots "
        "are free, the 1 constraint is a named omission. Health: max_health 36000 licensed for bm-009 and bm-RC2; "
        "thresholds 4000/4000/1050/250; 61 parts / 19 types with 4 fallbacks.",
    "8308-build-d09-audio.txt":
        "Updated by review 8299: 24 of 45 GUIDs are ours and 21 still donor (19 effects + 2 character) \u2014 that gap is "
        "B-26, not this step; T-AU1's event->parameter edge is UNKNOWN. All 10 banks are present (G3-14: 10 found / 0 "
        "absent). Fix vehicles#279 (-39.68 payload vs -40) and the weapons#408 loop click from Builds/bm-004c before "
        "re-encoding; V-04 compares length within 1 frame, loudness within 1 LU, loop clicks above -40 dBFS.",
    "8309-build-d10-handling-values.txt":
        "Updated by review 8299: the ledger has 109 'next' rows, not 40; the edit rows are 16 (35 values) and the "
        "keep-audit payload is B-24 = 15 values over 13 rows (t1_handling.json) \u2014 T-ST2 0.25 s, T-ST3 0.091 s (below "
        "the 0.2 s fleet minimum, declared R3), T-ST4 1/1/1, T-ST6 0.625 (INFERRED, falsifier 0.48), T-K3 4.0, T-E2 "
        "2921 N.m, T-E5 336.4 + Cd 0.1213, T-B1 6.3, T-B4 donor 1.5/80, T-A3 1.0, T-G4 0.071 m. T-E5 is the one "
        "'assumed' row (signed off 2026-10-23) \u2014 report it as a label, not a measurement.",
    "8311-build-d11-rebel-drop-text.txt":
        "Updated by review 8299: T-WLD4/T-WLD6/T-WLD11 closed as 'next' on computed keys \u2014 HashJenkins(leaf) "
        "443190071 belongs to a leaf that never ships, the shipped _debug pair 1621485476 is present 11/11 with text "
        "BATMOBILE, and _desc key 4081821928 is present 11/11. Carry the drop (T-WLD4) and the 18,688 B icon copy "
        "(T-WLD5); bm_rebel.py --check must show the blurb resolving to Batmobile text, not the Serpente's.",
    "8312-build-d12-variants-modes.txt":
        "Updated by review 8299: B-12's split is 4 rows flipping to the battle variant (T-MD5, T-MD6, T-MD7, T-MD13), "
        "2 named omissions (T-MD8 pivot, T-MD14 battle audio) and 2 turning on the same switch (T-MD10, T-MD11) \u2014 "
        "not '13 of 15'. D-2 is REOPENED; preconditions 3 (runtime swap UNKNOWN) and 4 (bm_build.py has no --variant, "
        "0 variant trees) are unmet, so aafdiff cannot run until both exist. t11_modes.py records 15 rows: carried 8, "
        "inside band 1, omitted 6.",
    "8320-build-d13-release-candidate-4.txt":
        "Updated by review 8299: merge B-10's reopened collision (2 bodies / 3 boxes / 1 constraint; the chassis-box "
        "Done gate in \u00a78 B-10) and B-25/B-26 as cards; BUILD_BATCHES now has 24 steps with B-17\u2026B-20 declared "
        "no-payload. Budgets stay Model 4,915 KB / Texture 7,065 KB. Expect 12 of 23 texture rows to be unfaithful (4 "
        "chapter masks + 8 missing pixel sets) and record them in the receipt \u2014 do not mark the tree complete.",
    "8399-review-build-wave.txt":
        "Updated by review 8299: check three genuine reds first \u2014 v05_driving.py (T-ST7 unblocked, turning circle must "
        "be re-derived), t_boost_rows.py and t_vnf_six.py (hard-coded 198-row ledger pin). Also verify the reopened "
        "collision (T22_REOPEN.md: 2 of 3 shapes missing) in the merge, and T-WP4's card citation (B-24/B-25 are "
        "handling and flares, not lock-hold/salvo).",
    "8400-verify-v01-file-gates-rc4.txt":
        "Updated by review 8299: read back the 199-row ledger (15 blocked, 145/216 evidenced, 35 edits over 16 rows) "
        "and B-24's 15 values (t1_handling.json) alongside the 35 values test-085 already carries; the batch sheet has "
        "24 steps and 19 artefacts. Do not gate on t_boost_rows.py or t_vnf_six.py (198-row pins).",
    "8401-verify-v02-geometry-poses-rc4.txt":
        "Updated by review 8299: RC2's silhouette margin was 0.0004 over the 99.9% limit; the parts set is now 61 "
        "parts (incl. wheel-arch parts 42/43). The pose set must include the battle pose, which B-12 now says is a "
        "second entity's angles (T-MD13 blocked, 4 pose rows). Collision is no longer a render-bbox gate \u2014 B-10's is "
        "the 2 chassis boxes + the pod at 4.000 deg.",
    "8402-verify-v03-wiring-rc4.txt":
        "Updated by review 8299: wiring must include the 8 forced weapon slots (4 CCar roots x 2), the Fire Leech "
        "missile clone, the winch anchor object, and B-18/B-19/B-20/B-21's objects if they ship in this tree; Rebel "
        "Drop strings resolve to keys 443190071 / 1621485476 / 4081821928. Dangling must be 0 per category.",
    "8403-verify-v04-audio-rc4.txt":
        "Updated by review 8299: expect 21 of 45 GUIDs still donor (19 effects + 2 character) unless B-26 shipped; "
        "vehicles#279 (-39.68 vs -40) and the weapons#408 loop click were fixed in Builds/bm-004c. Gates: length "
        "within 1 frame, loudness within 1 LU, loop points free of clicks above -40 dBFS.",
    "8404-verify-v05-predictions-rc4.txt":
        "Updated by review 8299: v05_driving.py --check is red because T-ST7 is no longer blocked \u2014 re-derive the "
        "turning circle (2026-11-06 ruling: 0.25 s low / 0.091 s high, the latter out-of-domain) before the sheets. "
        "Carry T-E5's 336.4 km/h as a label band with Cd 0.1213, and the reopened collision (2 bodies / 3 boxes / 1 "
        "constraint, 2 shapes missing) as a named Q-2 check.",
    "8405-verify-v06-install-dry-run-rc4.txt":
        "Updated by review 8299: the RC2 failure case was a dropzone that already holds the build; install_v3.ps1 "
        "refuses non-simulation paths, and the receipt is schema 2 with 19 artefacts over 24 steps. Rollback091 must "
        "restore the simulated dropzone sha256-identical.",
    "8406-verify-v07-gate-vx.txt":
        "Updated by review 8299: STATUS.md regenerates to 145/216 evidenced, 15 blocked (11 ledger + 4 T6), 109 "
        "queued, 8 out, 8 superseded; t23_closeout.py --check is now green (decisions 11/11, no-payload gates "
        "declared). Disclose in APPROVAL_REQUEST the still-red v05_driving.py, t_boost_rows.py and t_vnf_six.py, and "
        "the 21-of-45 donor audio GUIDs unless B-26 ships.",
    "8505-pilot-card-driving-takes.txt":
        "Updated by review 8299: the steering-lock card uses 0.25 s (T-ST7 ruling) and must be paired with the "
        "re-derived turning circle from V-05 (v05_driving.py is red until then); T-ST3's 0.091 s is out-of-domain "
        "(below the 0.2 s fleet minimum), so its card must expect a possible engine filter. The first five rows to "
        "move are A2, A5, A6, A7, A9.",
    "8506-pilot-card-combat-and-gadgets.txt":
        "Updated by review 8299: t7_weapons reads 13 carrier rows + 1 named omission + 1 blocked; riot is B-15's "
        "zero-damage impulse round (0.75 s cadence, second entity), EMP disable B-18, hacker B-19, sonar B-20, "
        "tracker B-21. Do not promise a 2.0 s held lock or an 8-target salvo \u2014 no card exists (t_blocked mis-cites "
        "B-24/B-25).",
    "8507-pilot-card-looks-and-audio.txt":
        "Updated by review 8299: 12 of 23 texture rows are unfaithful (4 chapter damage masks need variants; 8 pixel "
        "sets are missing), light range 60/45 exceeds the fleet max 50 (R3), and the 17 lens flares are B-25 with the "
        "light-unit probe \u2014 the night card must not count them as delivered. Overall appearance 54.6% (strict 49.3%, "
        "of-slotted 91.1%).",
    "8508-pilot-card-proving-on-a-simple-car.txt":
        "Updated by review 8299: prove on the Serpente with the same instruments; the driving set depends on the "
        "re-derived turning circle (v05_driving.py red) and the 0.25 s lock, and the combat set depends on "
        "B-15/B-18/B-19/B-20/B-21 not being built yet \u2014 mark those steps not-yet-provable rather than failed.",
    "8599-review-pilot-cards.txt":
        "Updated by review 8299: check cards against the actual state \u2014 15 blocked rows (11 ledger + 4 T6), 12-of-23 "
        "textures unfaithful, 21-of-45 audio GUIDs donor unless B-26, collision 2 bodies / 3 boxes with 2 shapes "
        "missing, and the 3 stale checkers (v05_driving, t_boost_rows, t_vnf_six) which are not test evidence.",
    "8600-q0-prove-pilot-cards.txt":
        "Updated by review 8299: Q-0 runs only with APPROVED_Q.txt; the stock-Serpente proof does not depend on the "
        "open rows, but record the 3 stale checks and the reopened B-10 so session 1 does not treat them as "
        "regressions.",
    "8601-q1-session-static-looks.txt":
        "Updated by review 8299: the looks session must expect 12-of-23 texture rows not shipped, 4 chapter damage "
        "masks absent (one static state only), 17 flares on B-25 (may be missing), and light ranges 60/45 above the "
        "fleet band. Record those as known gaps, not new failures.",
    "8602-q2-session-driving-takes.txt":
        "Updated by review 8299: the driving bands come from the re-derived turning circle (v05_driving.py is red "
        "until T-ST7's 0.25 s is folded in); the collision is now BmAK's 2 bodies / 3 boxes with 2 shapes missing, so "
        "a kerb/ram fail may be a hull-shape gap \u2014 write it as a B-10 fix card, not a retune.",
    "8603-q3-session-world-and-combat.txt":
        "Updated by review 8299: do not expect a 2.0 s held lock, an 8-target salvo or the reticle link (no card); "
        "riot is B-15's 0-damage round, EMP disable B-18, hacker B-19, sonar B-20, tracker B-21. Mode switch needs "
        "B-12's runtime swap, which is UNKNOWN (U1), so T-MD8 and T-MD14 stay omissions.",
    "8604-q4-fix-loop-triage.txt":
        "Updated by review 8299: triage against the real open set (15 blocked, 109 queued, 12-of-23 textures "
        "unfaithful, 21-of-45 audio GUIDs donor, collision 2 shapes missing); the 3 stale checkers (v05_driving, "
        "t_boost_rows, t_vnf_six) are card work, not test failures.",
    "8605-q5-showcase-recording.txt":
        "Updated by review 8299: the showcase must not imply unbuilt features \u2014 chapter damage states, 17 flares, a "
        "locked salvo, turn-on-the-spot (T-MD8) and battle audio (T-MD14) are omissions/cards; list them in the "
        "release notes.",
    "8699-review-test-campaign.txt":
        "Updated by review 8299: separate verified from unbuildable \u2014 15 blocked rows, 12-of-23 texture rows "
        "unfaithful, 21-of-45 audio GUIDs donor, collision 2 shapes missing, T-MD8/T-MD14 omissions; the 3 stale "
        "checkers are not evidence. Write 87xx fix briefs for the multi-element collision write and the "
        "lock-hold/salvo gap (no card).",
}


def main() -> int:
    missing = [n for n in UPDATES if not os.path.exists(os.path.join(Q, n))]
    if missing:
        print("MISSING:", ", ".join(missing))
        return 1
    changed = 0
    for name, text in sorted(UPDATES.items()):
        path = os.path.join(Q, name)
        raw = open(path, "rb").read().decode("utf-8")
        if MARK in raw:
            print("SKIP already updated:", name)
            continue
        with open(path, "a", encoding="utf-8", newline="") as f:
            if not raw.endswith("\n"):
                f.write("\n")
            f.write("\n" + text + "\n")
        changed += 1
    print(f"updated {changed} of {len(UPDATES)} briefs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
