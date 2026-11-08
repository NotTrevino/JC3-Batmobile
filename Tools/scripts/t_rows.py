"""t_rows.py - one disposition for every translation row (T-1 and T-2b).

`T1_TRANSLATION.md` and `T2_TRANSLATION.md` are prose tables: 88 numbered rows,
each a falsifiable property.  Prose cannot fail a build, so this tool turns every
row into a ledger line with a **disposition** and then checks the ledger against
the documents and against the build's edit list:

  edit       the proposed value is a module member and is in `t1_edits.json`
  keep       the build already carries the proposal (no edit needed)
  epe        the value lives in the entity graph, not a module (parts, lights)
  re-read    verified by decoding the built entity, not by an edit
  blocked    the value cannot be written with this toolkit (write side missing)
  out        no JC3 expression exists (feature gap, not a translation row)
  superseded a G2 carrier exists: the requirement moved to the phase-T card in
             `superseded_by` (T-10, `GRAB_BACKLOG.md` §7).  A `superseded` row is not
             unfinished work in this table - its successor owns the value - and it is not
             `out` either: the old "no JC3 system" claim is refuted, so `why` says how.

Usage:
  python t_rows.py build      # parse both tables -> T_ROWS.jsonl
  python t_rows.py check      # ledger vs documents vs t1_edits.json
  python t_rows.py summary    # counts by disposition and by family
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
DOCS = [("T-1", os.path.join(WORK, "T1_TRANSLATION.md")),
        ("T-2b", os.path.join(WORK, "T2_TRANSLATION.md")),
        ("T-3", os.path.join(WORK, "T3_COVERAGE.md")),
        # T-17 (effects): generated with its own --check by t17_fx.py, parsed here like the rest
        ("T-13", os.path.join(WORK, "T13_FX.md")),
        # T-18 (lights): generated with its own --check by t18_lights.py
        ("T-14", os.path.join(WORK, "T14_LIGHTS.md")),
        # T-11 (weapons): generated with its own --check by t7_weapons.py
        ("T-7", os.path.join(WORK, "T7_WEAPONS.md")),
        # T-20 (world): generated with its own --check by t15_world.py
        ("T-20", os.path.join(WORK, "T15_WORLD.md")),
        # T-15 (modes): generated with its own --check by t11_modes.py
        ("T-15", os.path.join(WORK, "T11_MODES.md"))]
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
EDITS = os.path.join(WORK, "t1_edits.json")

ROW_RE = re.compile(r"^\|\s*(T-[A-Z]{1,3}\d+)\s*\|")
HEAD_RE = re.compile(r"^##\s+(.*)$")
# a verification table's first column is a row *family*, not a definition
SKIP_SECTION = re.compile(r"^\d+\.\s+(Verification|Blocked rows)")

# Rows whose disposition is not "keep".  A row absent from this table is a keep:
# the build already carries the proposal, which is what test-084 measured.
DISPO: dict[str, tuple[str, str]] = {
    # --- the four 2026-11-08 v2 plans (driving, world, parts, controls) ----------------
    # `why` is the short form; the four reports under `tmp/freebuff/reports/` carry the decode:
    # `water-flip-damage-remote-plans-v2.md` (operator observations), `boost-selector-and-moving-
    # parts-plans-v2.md` (P-01..P-15), `controls-entry-exit-eject-plans-v2.md` (the control cells)
    # and `air-control-and-ram-assist-plans-v2.md` (the T-AC1 / T-RA1 figures corrected above).
    "T-WT1": ("next", "water entry teleports the car to land instead of sinking it (`water-flip-damage-remote-plans-v2.md` section 1.3): `will_sink` 1 -> 0 on the car's own `..._water_interaction.vmodc`, a water watcher on `sinking_progress` >= 0.30 (chosen) or the in-water exit state, and a nearest-land ring 8 -> 40 m; the destination rule is UNKNOWN, so the ring thresholds are chosen, not decoded"),
    "T-FR1": ("next", "a flipped or stuck car rights itself with its thrusters after a rest (`section 2.3`): the gate is `CInteractionGraphParentIsUpRightCondition`, the timer pair is `BatmobileStuckTimeMax` 2.0 / `BatmobileStuckTimeFlip` 0.5, the lift is `turbo_jump` 50 / 0.0 / 12 on the `EngineTurboJump` usage, and `DriverLean.righting_torque` 3000 is the probe (0 cars ship `DriverLean`, 230,300 N.m for 0.5 s is the derived hook)"),
    "T-DE1": ("next", "health to zero explodes the car and kills its occupants while collisions do nothing (`section 3.3`): `impact_damage_factor` 0 and `deform_scale` 0 already ship, the blast is the root `CForcePulse` -> `car_explosion_medium.ftune` (500 in 5 m); the step is to prove the pulse survived into the car's `.ee` and probe `smoke_threshold`/`burn_threshold` 0, and NOT to wire a destroyed-mesh `mshswap`"),
    "T-RC1": ("blocked", "remote control is HALTED by the plan, not declared impossible (`section 4.4`): it has no input carrier (no aim/stick/cursor action on a land vehicle, no 2D vehicle stick, and the gadget route is a proximity interaction with 0 range members), the overlay has no HUD element, and the car's arrival is already a Rebel Drop item keyed by the entity-leaf Jenkins hash - so a second arrival path buys nothing"),
    "T-RC2": ("blocked", "the static overlay and the 150 m hard stop are HALTED by the plan (`section 4.3-4.4`): BmAK's 100 m is a gadget float (`JammingRange` 10000 cm), the vehicle-HUD element table has 0 static/noise/jam/overlay members, and no vehicle, HUD or interaction member carries a distance-to-player read"),
    "T-RC3": ("next", "homing drives an existing instance to the player (`section 4.3`): `car_drive_to_point.btc` (80,366 B, one of 26 vehicle micro-behaviours) plus the `CarAI` tune 35 / 5 / 15 / 0.5 is the carrier; the trigger must NOT be LB, which is exit (T-CT1), and whether a tree binds to one vehicle with a target point is UNKNOWN, so the row is probe-gated"),
    "T-PT1": ("epe", "P-01 turret: hinge `constraint_index` 11, axis [0,1,0], limits -1.047198..1.047198 rad (-60..60 deg) - the axis agrees with the donor, the range does not"),
    "T-PT2": ("out", "P-02 cannon: `joint: null` and no rotation is animated, so a hinge cannot reproduce it; the 53.376 / 36.129 cm bone translation is a named omission and the -5..20 deg belongs to the carrier's hinge, not the row"),
    "T-PT3": ("epe", "P-03 machine gun: 6.00 turns with peak 1229.51 deg/s and mean 553.8 deg/s - both stated, since 2160 / 3.90 = 553.8; `GatlingGun` is proven on boats and helicopters only, so the car case is a probe"),
    "T-PT4": ("epe", "P-04 riot suppressor: BmAK's -89.999..0 deg line about -Z and the carrier's +X -5..20 deg are two different lines in one row - pick one before writing; it is the only `axis_agrees: false` part row"),
    "T-PT5": ("out", "P-05 jet: `batmobile_jet` is in no name table and no export, the spin is not bound to `engine_rpm`, and the 40.163 cm `JetSMove` translation has no bone to drive - every jet-named export is accounted for, so the driver is code"),
    "T-PT6": ("epe", "P-06 canopy: the 12.494 deg rotation rides the donor `Hood` channel and the 72.481 cm translation is a named omission - JC3 door parts rotate only, never translate"),
    "T-PT7": ("epe", "P-07 left cover: 15.007 deg at 32.14 deg/s, no hatch bone and no hatch part, so the omitted `door_parts` row stays omitted and the pod bones carry the lift"),
    "T-PT8": ("epe", "P-08 right cover: the mirror of P-07 with its own 75.10 deg/s bottom rate"),
    "T-PT9": ("epe", "P-09 flap L front: the part bone reads 20.010 deg at 37.20 deg/s while the row headline quotes 25.817 deg at 48.70 deg/s from a second bone - state which bone is which"),
    "T-PT10": ("epe", "P-10 flap R front: the mirror of P-09"),
    "T-PT11": ("epe", "P-11 flap L rear: piston 54.787 deg at 106.14 deg/s, part bone 29.986 deg at 56.85 deg/s"),
    "T-PT12": ("epe", "P-12 flap R rear: piston 54.799 deg at 105.82 deg/s, not P-11's 106.14 - the older plan copied the left rate onto the right"),
    "T-PT13": ("out", "P-13 yoke: `joint: null`, no part, 0 yoke faces in the hand box and 0 bone matches over 180 bones and 324 packages - there is nothing to animate"),
    "T-PT14": ("epe", "P-14 pod L: it carries the `Missiles_*_T` joint and `moves_with: P-07`, so the right word is 'no behaviour of its own', not 'static'"),
    "T-PT15": ("epe", "P-15 pod R: the same joint, `moves_with: P-08`"),
    "T-CT1": ("blocked", "enter = Y and exit = LB (operator rules 2-3): the shipped pair is both on `RPADUP` and has to be split, and no keymap writer exists (T-CT5); the corrected facts are that no X token count exists (the 8-token button is `LSHOULDER` alone, export X carries 3) and that five buttons collide, not one"),
    "T-CT2": ("blocked", "eject = double press of A (operator rule 4): the exit half is data (`S_EXIT_VEHICLE_PARA` behind a speed gate), the double press is not - no hold/duration/tap field in 145+104+249 binding rows and 0 of 4,832 exits carries a launch member; the keymap writer is the other half"),
    "T-CT3": ("blocked", "winch = D-pad Right (operator rule 5): it displaces `USE_VEHICLE_MOD`, which T-CT1's Y row re-homes, and it waits on the same missing keymap writer"),
    "T-CT4": ("blocked", "steering axes are decoded (`aTurn` = `RightX`, `aStrafe` = `LeftX`, stated separately rather than blended) but BmAK's in-car response curve needs the capture set (U6) before a rate is written"),
    "T-CT5": ("blocked", "the build step every control row waits for: 0 of 575 `Tools/scripts` files writes a bin, so the 12-byte binding record plus 18 B of `stringZ` records must be serialised into the 7,207 B patch keymap and re-parse to 145 patch / 131 base bindings"),
    # --- the 2026-11-08 body pass: paint channels, the mode swap, the twelve texture refusals ------
    # `why` is the short form; `paint-plans-v2.md` and `collision-impact-and-mode-switch-plans-v2.md`
    # carry the decode, and `Builds/bm-RC4-appearance/texture_ledger.json` the refusals.
    "T-PC1": ("next", "the four gloss channels become [0.60, 0.75, 0.85, 0.98] = 1 - Material0..3_Roughness; ch1's 0.75 replaces the 0.60 the build reused from ch0 (paint v2 D1), and the write is impossible until `VALUES.json:5` gloss_cap leaves 0.40 (`factors.py:256`)"),
    "T-PC2": ("next", "metallic becomes [0, 0, 1, 1]: `Material2_Metalicity` 1.0 is decoded, ch3's 1.0 is derived (only the metal branch reaches F0 0.0060), and ch0/ch1 stay dielectric; `factors.py:264-271` needs the spec authored because ch3's reflectivity 0.15 is under its 0.5 trigger"),
    "T-PC3": ("next", "clear coat becomes [1, 1, 1, 1] from the JC3 palette (clear_coat 1.000 on 10/10) - BmAK has no clear-coat parameter at all, so this is sourced elsewhere and labelled so"),
    "T-PC4": ("next", "the three tints become [0.022, 0.02, 0.02] / [0.47402, 0.35289, 0.21428] / [0, 0, 0] and cb6[4] becomes [0.75, 0, 1]: the build wrote the body colour into all three tint vectors, which are channels 1-3, not 0 (paint v2 D2/D3)"),
    "T-PC5": ("next", "F0 is recorded, not written: 0.0080 / 0.0080 / 0.0360 / 0.0060 and MK2 0.162, carried approximately by cb2[1]'s metal branch with the residuals +0.032 / +0.032 / 0 / +0.014 declared; ch3 takes the nearest-wins 0.15 (763), not 767's 0.5"),
    "T-PC6": ("out", "the four wetness numbers have no member on CarPaintMM (0 of 13 headers) - the wet look is the scene's; the composite gloss 0.70 / 0.8125 / 0.8875 / 0.985 is a bake fallback, and the 0.6 -> clearcoat 1.0 bridge is withdrawn (+67 % with no formula)"),
    "T-MS1": ("blocked", "the mode swap waits on U1: no selector member exists, so the carrier is two `.ee` leaves proven through Rebel Drop; the trigger's nearest action is `USE_VEHICLE_MOD` with an unknown consumer and an authored 0.40 s hold, and U1 is settled only by `JustCause3.exe` (no .exe in the archive)"),
    "T-TX1": ("blocked", "Micropattern_A: 0 of 61 grab `.tga` carry the stem, so the plate cannot be baked; the shipped P1 microdetail layer is the closest carrier and the missing plate is declared absent - settler is a re-grab of the Playable_Batmobile packages"),
    "T-TX2": ("blocked", "Micropattern_A_Normal: same pixels gap with no substitute at all (the P1 bake writes tangent XY into s1, not a second map)"),
    "T-TX3": ("blocked", "Micropattern_B: same pixels gap, declared absent"),
    "T-TX4": ("blocked", "Micropattern_C: same pixels gap, declared absent"),
    "T-TX5": ("keep", "Wheel_E: the refusal is the built state - the four arch strips stay dark, as the ledger's R2 row states; no colour is guessed"),
    "T-TX6": ("out", "Body_ColourRamp: no pixels and no ramp sampler in 961 headers, so nothing can bind; the colour is carried by the s0 region means"),
    "T-TX7": ("out", "Lacquered_Underlayer_Ramp: the pixels ARE in the grab (Startup, 4,050 B) but no header declares a ramp sampler - a sampler refusal, not a pixel one"),
    "T-TX8": ("next", "Aniso_ramp_Lacquered: no ramp and no aniso sampler, so the closest system is a two-slot gloss split 0.75 / 0.45 with the BRDF declared isotropic"),
    "T-TX9": ("blocked", "Body_Damage_ChapterMask: no chapter selector (0 of 961 headers, SupportDmgBlend [0.0] in all 160 blocks), and the one writeable state paints every chapter damaged - declined twice because the operator wants no damage stages"),
    "T-TX10": ("blocked", "Weaponry_Damage_ChapterMask: same selector gap and the same decline as T-TX9"),
    "T-TX11": ("blocked", "WheelArch_Damage_ChapterMask: same selector gap and the same decline as T-TX9"),
    "T-TX12": ("blocked", "Undercarriage_Damage_ChapterMask: same selector gap and the same decline as T-TX9"),
    # --- the handling keep-audit (2026-11-06): every COMPROMISE in the dimensions/wheels,
    # steering/drift and engine/boost/aero reports gets its replacement value or its
    # closest-system composition, with the derivation in the ledger cell.
    # `why` is the short form; the three audits under `tmp/freebuff/reports/keep-audit-*.md`
    # carry the decode, and `tmp/freebuff/reports/apply-keep-audit-fixes-handling.md` the apply.
    "T-G4": ("next", "replacement 0.071 m = body bbox min y 0.091 - ground 0.02 (derived from `stations.json`): BmAK has no `ground_clearance` member, so the only measurable lore gap is the underbody clearance, and 0.071 is coherent with the tyre contact (0.7047 - 0.68275 = 0.0220 m); the old 0.7037 was the hub mean, 0.6327 m above the gap (9.9x), which is why C09 refuted the `derived` class; inside the shipped 0.05..1 domain (med 0.4, n=271); kerb/pothole/landing probe is Q2-A6 (`keep-audit-dimensions-wheels.md` T-G4)"),
    "T-ST2": ("next", "replacement 0.25 s by operator ruling 2026-11-06 item 1 (`DECISIONS_NEEDED.md`: 'T-ST7: A, 0.25 s (BmAK 55 deg / 220 deg/s)'), derivation 55 deg / 220 deg/s = 0.25 s at BmAK's base rate (`T_ST7B_FLOOR.md` section 3); the 0.0833 s the 720 deg/s curve implies is NOT taken because the ruling fixes the response at 0.25 s; 0.25 s ships on 4 LandSteering AI twins, so it is in-domain (`steering-st7-apply.md`)"),
    "T-ST3": ("next", "replacement 0.091 s = 20 deg / 220 deg/s (operator ruling 2026-11-06 item 1 applied to the high-speed member; T-ST7 owns both times): BmAK's rate curve is flat, so the high-speed full-lock time is the lock angle over the same 220 deg/s rate; declared R3 - below the 0.2 s fleet minimum (`steering-st7-apply.md` section 3)"),
    "T-ST4": ("next", "replacement 1 / 1 / 1 = identity from the absence proof: BmAK has no input-exponent member and every steering modifier in the chain is 1.0 with `DriftSteeringAssist` absent (`CHAIN.json`), so absence means identity (the `T-B3` precedent); 1.0 is the fleet floor in 1..3 (n=145), and a cubic pad curve would make half stick 12.5 % of the rate (`keep-audit-steering-and-drift.md` section 5)"),
    "T-ST6": ("next", "replacement 0.625 = 1 / rear `LatSlipFactor` 1.6 (`CHAIN.json`): the reciprocal of the rear slip gain is the aligning authority that holds the same line, inside the shipped 0.3..0.8 band (n=19, median 0.5); INFERRED bridge, falsifier: if 0.625 refuses to rotate while 0.3 rotates the direction is inverted and 0.48 = 0.3 x 1.6 is the value (`keep-audit-steering-and-drift.md` section 6)"),
    "T-K3": ("next", "replacement 4.0 = `EBrakeBrakeForce` 640,000 / its class default 160,000 (`MECHANICS_NAMES.md:32`, `CLASS_DEFAULTS.md:184`): a force ratio is the only unit-free bridge, which is why it survives T-K1's disproof of the direct force -> torque bridge; inside the shipped 1..10 domain (n=145) but above the 6 t band 1..2.25, declared R3 (`keep-audit-steering-and-drift.md` section 7)"),
    "T-E2": ("next", "replacement 2921 N.m = 894.8 kW / (471.239 rad/s x 0.65) at the edited 4500 rpm band - the torque the lore 1200 bhp needs at T-E1's band; the 1393.5 x 2.844 ratio was computed at the donor's 5000 rpm and delivers only 572 hp (47.7 %) at 4500, while the 0-60 in 2.7 s route gives 2513 N.m (59,580 N / 16.19 gearing x 0.683 m); declared R3, above the fleet p95 2,500; `FITS.md` holds 834.1 at 4 t and 1,100 for 6-15 t, not the 1,121 the old cell quoted (`keep-audit-engine-boost-aero.md` T-E2)"),
    "T-E5": ("next", "keep 336.4 as the top of a **300-336 km/h band labelled assumed** (the 2026-10-23 sign-off covers the label, not a measurement) and do NOT tune drag to it: `land_aerodynamics.drag_coefficient` stays T-A2's class fit 0.55, so the pair is two decisions, not one translation; at T-E2's 2921 N.m x the 0.65 wash at 4500 rpm = 894.7 kW, Cd.A = 0.55 x 6.634667 = 3.649 m^2 and rho 1.2 the predicted terminal is (2P/(rho Cd A))^(1/3) = 74.2 m/s = 267 km/h (265 at rho 1.225) - the number a take compares with - while 93.44 m/s at the same power would need Cd.A = 1.828 m^2, i.e. Cd 0.276, also not written; the Cd 0.1213 this row used to carry was reverse-engineered from the label and is rejected/not written (0.1213 x 6.635 = 0.805 m^2 is only 394 kW at 93.44 m/s, not the 894.7 kW it cited, and the earlier 260 km/h did not follow from its own inputs - correction 8391); any top-speed take tests **reachability of a label, not fidelity to BmAK**; whether `official_top_speed` is a cap is UNKNOWN (`keep-audit-engine-boost-aero.md` T-E5)"),
    "T-B1": ("next", "replacement 6.3 = 1 + 6.00 / 1.13 (BmAK's `FakeExtaSpeedAccel` 600 cu/s^2 = 6.00 m/s^2 thrust over the built car's measured 1.13 m/s^2 low-speed acceleration, 6,777 N / 6,000 kg): 6.3x adds the lore thrust while 2.0 adds only 1.13 m/s^2 (18.8 %); `extra_top_speed` 43.2 and `boost_blend_time` 0.2 stay - 43.2 km/h reproduces the 1.30..2.10 band between 39 and 144 km/h; inside the shipped 1.5..40 domain (med 2, n=145) (`keep-audit-engine-boost-aero.md` T-B1)"),
    "T-B4": ("next", "replacement from the T-MD14b donor decode, block by block: `heat_boost` grip 1.5 / extra 80 and `nitro_boost_upgraded` grip 1.5 / extra 80 (the ATV donor's own values), `nitro_boost` grip 2 / speed 40 unchanged, and the battle rung writes `heat_boost` grip 1.333 = 1 / `BattleModeLatSlipScale` 0.75 with `extra_top_speed` 0.0 because battle caps speed and never adds it; the target module is read before it is written, since the 2.4 table (1.0 / 4.26 / 4.26, 43.2 / 100.92 / 100.92) is a different `CustomLandGlobal` copy (`boost-selector-and-moving-parts-plans-v2.md` section 0, A-C1). The bytes carry two inherited scalings that are not BmAK numbers - the bytes carry two inherited scalings that are not BmAK numbers (grip 4.26 = 1.5 x 2.844, the torque ratio; extra 100.92 = 80 x 1.2615, the 336.4/250 tier scale), and with T-E2/T-B1 carrying the power ratio, scaling grip by it double-counts; BmAK states no grip change in boost at all (T-B3 identity); blend 0, torque 2 and turbo_jump 0.1 s / 50 km/h / top 200 stay as the donor ships them (n=145) (`keep-audit-engine-boost-aero.md` T-B4)"),
    "T-A3": ("next", "replacement 1.0 = identity from the absence proof: BmAK's chain has no drag member at all (grep `Drag|Lift|Aero|Downforce|Area` returns only `SelfDriveUseTightArea` and `UprightLiftStrength`), and the member's consumer is UNKNOWN, so 1.0 provably changes nothing while 2.0 drops the ceiling to 161 km/h under the multiplying reading; inside the shipped 1..30 domain (med 2, n=306) at its floor; a 1.0 vs 2.0 probe settles whether the member is live (`keep-audit-engine-boost-aero.md` T-A3)"),
    # --- T-1, motion --------------------------------------------------------
    "T-G5": ("edit", "probe: friction_type 0 -> 2, carried and read back"),
    "T-M1": ("edit", "mass 4000 -> 6000 (armored class)"),
    "T-M2": ("edit", "yaw/pitch/roll 1.8/1.5/0.5 -> 4.0/2.6/1.2"),
    "T-M4": ("edit", "wheel mass 25/75 -> 75/150"),
    "T-S1": ("edit", "suspension strength 80/80 -> 45/45"),
    "T-S3": ("next", "suspension length 0.25 -> 0.70 = BmAK SuspensionTravelUp 30 + TravelDown 40 cm (archetype, all four wheels); in the 6t+ band 0.18..0.75; gate A6: ride height + landing"),
    "T-S2": ("edit", "compression 2.5 -> 3.0"),
    "T-R1": ("edit", "arcade friction 1.0 -> 3.0 (the understeer row)"),
    "T-ST1": ("edit", "steer 55 deg at 20 km/h -> 20 deg at 72, falloff 1.5"),
    "T-E1": ("edit", "rpm band 1000/5000/7300 -> 800/2800/4500"),
    "T-E3": ("edit", "torque factors at min/max rpm 0.86/0.84 -> 1.0/0.65"),
    "T-E4": ("edit", "6 gears at 7000 -> 5 gears at 4200"),
    "T-A2": ("edit", "drag 0.139 -> 0.55"),
    "T-A4": ("edit", "lift -1.95 -> -0.3"),
    "T-K1": ("edit", "brake torque 10000 -> 5000"),
    "T-B3": ("next", "nitro grip 5.68 -> 1.0: BmAK boost touches no grip member (absence proven by G1-1 + bmak_chain), so identity; below shipped 1.2..2, declared R3; gate A9"),
    "T-ST5": ("next", "countersteer/steer_in 2.0/1.5 -> 1.0/1.0: BmAK's drift-correction steer speed and re-centre mod both read 1.0 (neutral, no assist gain), declared below the shipped bands (R3); gate A7"),
    "T-B2": ("next", "nitro extra_top_speed 50.46 -> 43.2 = min(FakeExtraSpeedMax 3500, FakeExtaSpeedAccel 600 x BoostDuration 2.0) cu = 43.2 km/h, in-domain; gate A2"),
    "T-K2": ("next", "brakes min_time_to_block 5 -> 1: the donor's shipped value; brake-lock absence now proven exhaustively across the chain (HandBrakeOffTime 0.3 s named for a later semantics pass); gate A5"),
    "T-L1": ("epe", "light rig is SVehicleLight presets in the entity graph"),
    "T-L2": ("epe", "flare entries map onto the same two headlight presets"),
    "T-L3": ("epe", "brake rows are presets in the entity graph"),
    "T-L4": ("superseded", "closed by T-18: no JC3 wheel preset exists, so the lamp is a custom `preset_id 0` entry (G2-33 §7 recipe, `Research/JC3Grab/LIGHT_SYSTEM.md`); the rows are T-L13/T-L14 and the flare rows ride them"),
    "T-L5": ("epe", "secondary spot preset in the entity graph"),
    "T-L6": ("epe", "dashboard preset in the entity graph"),
    "T-L7": ("epe", "boot preset in the entity graph"),
    "T-P1": ("epe", "part names live in the entity graph, carried from test-083"),
    "T-P2": ("next", "update the count and record the fallbacks: 24 donor `Land_*` types joined to 42 parts in bm-009 and **61 in bm-RC2** (17 / 19 distinct types), with four types used by the build having no row (`Boat_Antenna`, `Boat_Generic`, `Plane_Control_Surface`, `Train_Generic`) and falling back to `Default`; BmAK has no per-part damage table, so this is a donor carry - `keep-audit-damage-collision.md` T-P2 and section 4.3"),
    "T-P3": ("next", "reopened 2026-11-07 on `COLLISION_WHERE.md` (G3-16): the drivable rigid body is `Physics.Batmobile_V3_Physics` - 2 bodies / 3 boxes / 1 constraint, reached from `SVehicleMesh` property offset 824 - so the hull set is those 3 boxes (chassis 690.305x374.536x207.5 + 679.585x345.688x103.5, pod 166.177x189.365x39.8 at 4 deg), not the 11 of 32 wreck boxes G2-30 could reach; the built set still carries 62 donor bodies with only body 0's hull rewritten (B-10e), so 2 shapes are missing; plan `T22_REOPEN.md`"),
    # --- T-2b, the other half ----------------------------------------------
    "T-PA1": ("epe", "wheel parts in the built graph"),
    "T-PA2": ("epe", "light points -> parts in the built graph"),
    "T-PA3": ("epe", "part -> collision body ids in the built graph"),
    "T-PA4": ("epe", "wheel_parts slots in the built graph"),
    "T-PA5": ("epe", "door parts in the built graph"),
    "T-PA6": ("epe", "constraint points in the built graph"),
    "T-PA7": ("epe", "non-deformable part list in the built graph"),
    "T-PA8": ("epe", "6 orphan sockets dropped, they cannot be driven"),
    # --- the appearance/materials keep-audit (2026-11-06): every COMPROMISE gets its replacement ---
    # `why` is the short form; `tmp/freebuff/reports/keep-audit-materials-textures.md` carries the
    # decode behind each replacement value, and `colour-bmak-wet-look.md` the BmAK parameters.
    "T-MA3": ("next", "replacement 0x43/0x41/0x45 = 0.0566/0.0516/0.0600 linear, gain 1.0: the 3.4476 GRB-6 gain was applied on top of BmAK's own already-adjusted colour (base [0.025787, 0.025787, 0.03] x Diffuse_Adjust [2.2, 2.0, 2.0]) and delivered 3.44x the authored brightness - the white-violet car (`colour-bmak-wet-look.md` section 2, `keep-audit-materials-textures.md` section 4)"),
    "T-MA4": ("next", "replacement 0.600 in the paint blocks and the palette: the 'vanilla cap at 0.4' is refuted by the donor's own palette (8 of 10 tints at 0.45), so 0.45 was 0.75x authored; 0.6 is above every value the fleet is seen to use, declared R3 (`keep-audit-materials-textures.md` section 5)"),
    "T-MA5": ("next", "the unported glass pair is derived from the measured mask: `SpecFresnel` 0.45 = mean(`Glass_S`.R) 0.565 x `Glass_Reflectivity` 0.8, `SpecGloss` 0.92 = 1 - mean(`Glass_S`.G) 0.074 x `Glass_Roughness` 1.1; plus the normal is moved from block table position 1 to `s2`, where `window.fb.txt` samples it (`keep-audit-materials-textures.md` section 6, `app-per-pixel-reflectivity.md` section 7 T5a)"),
    "T-MA7": ("next", "keep the 10-tint menu but set every tint to the T-MA3 colour and `specular_gloss` 0.600: as delivered one menu click discards the lore colour, and the row's 'all 10 at 0.45' is wrong on 2 (`keep-audit-materials-textures.md` section 8)"),
    "T-LG1": ("next", "recount 18, not 21 (21 - 10 dropped + 7 added, `bm_lightrig.plan()`): the row's own evidence is the built module's count, and B-07 changed it - `keep-audit-lights.md` section 5"),
    "T-LG3": ("next", "recount 4 rows at range 30 / angle 40 (rows 2, 4, 6, 10), not 5; 1 at 10/60 and 13 at 2/10 - `keep-audit-lights.md` section 5"),
    "T-LG6": ("next", "replacement values derived per lamp: range = Radius_cm / 100 -> 60, 45, 40.96, 20.48, 10.24, 4, 1.5, 0.8 (60 and 45 above the fleet max 50, declared R3); angle = OuterConeAngle -> 70, 60, 50, 44, 35, 15; multiplier = clamp(5 x Brightness, 0.5, 5) -> 0.75 / 5; blinking 0 on the four cloned rows, since no BmAK entry authors a blink; InnerConeAngle has no member (second row on the same part); units UNKNOWN, Q-1 night take - `keep-audit-lights.md` section 6"),
    "T-LG2": ("keep", "closed for the donor join only: `t2_lg2.py` measures the `.epe`, not BmAK fidelity, and B-07 dropped 10 / added 7 rows - `keep-audit-lights.md` section 5"),
    "T-L7": ("superseded", "corrected by T-18: `Rear_Point` is not one of the 22 objects this rig's graph instantiates, so the boot lamp is a custom `preset_id 0` entry (row T-L35)"),
    "T-LG4": ("superseded", "closed by T-18: the absent preset is replaced by a custom `preset_id 0` entry on a new `sportsmuscle_wheel_f_*_arch` part (G2-33 §7), rows T-L13/T-L14"),
    # --- T-10 (2026-10-28): the `out` rows re-decided against the G2 evidence ----------
    # `why` is checked against the T-10 table by `t10_reopen.py --check`, so edit both.
    "T-LG5": ("superseded", "split: the battle-mode spotlight is a donor light type (`VEHLT_BattleModeLight`) with no JC3 behaviour of its own - the fleet has none, so T-18 maps the lamps onto `HeadLight`; the forensics rig stays a named omission - proof `Research/JC3Grab/LIGHT_SYSTEM.md`"),
    "T-AU1": ("keep", "LandAudio's two members (min_rpm 1000, max_rpm 10000) stay; the event->parameter edge is not decoded (0 fields resolve it), so which BmAK curve becomes min/max rpm is UNKNOWN and the mapping is B-11's bank task - `keep-audit-audio-fx.md` section 3"),
    "T-AU2": ("keep", "holds for 1 of 3 banks: test-060 swapped `vehicles.bank` only, so 24 of the 45 pinned GUIDs are ours and 21 (effects.bank + character.bank: breaks, explosion, fire_post_explosion, TireDestroyed, damage_smoke, water_explosion, speedwind, jump_air_whoosh) still play donor audio; per-vehicle replacement needs an override (`SDynamicAttachedEffect` per entity or a per-entity bank), which is card B-26 - `keep-audit-audio-fx.md` section 3"),
    "T-AU3": ("next", "AUDIO_BANKS.md (G3-14) re-tested the absence claim against the whole BmAK install: 10 claimed banks, 10 found, 0 absent, 117 AkBank payloads read - so the source exists and what remains is the JC3 event binding of the 26 ids (T_AU3B.md: the 27/27 absence is true of the JC3 install only)"),
    "T-AU4": ("edit", "LandAudio.max_rpm 10000 -> 4500, follows T-E1"),
    "T-FX1": ("keep", "lore-exact: all three donor breaks have same-meaning vehicle .effc carriers (window 12, taillight 1, lamp on/off 2, electric 1) but JC3's window effects are per-vehicle, so B-11's plan picks the variant per part (canopy vs side glass) instead of inheriting one - `keep-audit-audio-fx.md` section 4"),
    "T-FX2": ("keep", "lore-exact: `dmg_fire_engine_*` (41 vehicle paths), `dmg_fire_spread_roof` (5, all vehicle) and `dmg_fire_spread_base` (2); the roof emitter needs the canopy part + socket, which is B-02/B-03 work, not a new effect - `keep-audit-audio-fx.md` section 4"),
    "T-FX3": ("next", "operator ruling 2026-11-06 item 2: the donor's two emitters already carry EngineNitro (4197885156) in the entity graph, so the approved edit is B-08's placement of both SAttachedEffect.world mats at the Afterburner socket (bone JetSMove) - spec Working/Effects/bm_fx_edits.json, compiled into Builds/bm-008; the 'no usage slot' reason was false (T_FX3B.md)"),
    "T-FX4": ("superseded", "split: the EMP *effect* has a carrier (`CForcePulse`, G2-16) but the weapon-slot copy does not, so the EMP/Immobilizer half moves to T-11 and the tyre-smoke half to T-17 (FX-3 `tire_effects`); seismic sonar stays a named omission - no sonar class in `Research/JC3Grab/ENTITIES.md`"),
    "T-FX5": ("keep", "the 74 holds (FX_TABLE.jsonl:27222, container == donor .ee); the '23 unreferenced' half is UNKNOWN - the producer never states what it counted (LEDGER-g3src.md:197); those paths are donor content outside the 51-row effect set, so the build owes them no carrier - `keep-audit-audio-fx.md` section 4"),
    "T-DM1": ("next", "T-14 option B decides max_health 2000 -> 36000 (24 heavy-cannon hits x 1500 shell damage), out of the shipped 500..4000 domain so it is a declared switch; B-09 writes it, pending Q1-DM-A (18000 if the percentage gate ships)"),
    "T-DM2": ("edit", "bullet armour 100 -> 99, the fleet maximum"),
    "T-DM3": ("next", "keep 5 @ 20, labelled a donor carry: BmAK has no per-channel armour (one TakeDamage, ArmourModeDamageReduction 0, generator shield) and no decoded JC3 weapon writes `bullet_heavy`, so the value reproduces nothing measurable until B-09 decodes a channel carrier - `keep-audit-damage-collision.md` T-DM3"),
    "T-DM4": ("next", "record all four thresholds the module carries (explosion 4000, npc_explosion 4000, smoke 1050, burn 250) - the ledger named three; every one is at the top of its shipped domain, so it is a fleet maximum, not a BmAK figure, and the BmAK timing is UNKNOWN - `keep-audit-damage-collision.md` T-DM4"),
    "T-DM5": ("next", "keep the donor's 24 `Land_*` types but correct the record: the 32 boxes are collision geometry on the destroyed asset (PHYSICS.md), `RVisualDamageComponent` decodes nothing (6 B), the join is 42 parts in bm-009 and 61 in bm-RC2 (17 / 19 distinct types), and `Boat_Antenna` IS a real PartDamageType declared by all 35 boat entities - it is only absent from this vehicle's land table, so the Default fallback is real - `keep-audit-damage-collision.md` T-DM5"),
    "T-DM6": ("next", "keep 0 and withdraw the '1 - all 156 land vehicles ship 1' proposal: 1 is the fleet rule R1 forbids importing, and the BmAK evidence is UNKNOWN (destroyed mesh, damage masks and a Damage_States package are not panel deformation) - `damage_switches.json` declares the switch - `keep-audit-damage-collision.md` T-DM6"),
    "T-CO1": ("next", "no longer 'donor chassis by decision': `COLLISION_WHERE.md` (G3-16) decoded the drivable asset as `Physics.Batmobile_V3_Physics` (BmGame export 158266, 2 bodies / 3 boxes / 1 constraint, reached from `SVehicleMesh` property offset 824), so T-22 and B-10 are reopened to author those 2 bodies into the donor's hull slots (`T22_REOPEN.md`); the 1 constraint has no decoded JC3 writer and the live per-mode Batman-vs-Batmobile mesh is still UNKNOWN (`BatmanVsBatmobileCollisionMode` not serialised)"),
    "T-CO2": ("next", "the 3.1615x0.6342x1.0988 m 'largest' box is the wreck set's maximum and a wreck wheel, not the car: `COLLISION_WHERE.md` shows the drivable car's largest box is the chassis box 690.305x374.536x207.5 cm (6.903x3.745x2.075 m), so the superlative is scoped to the wreck and the car's hull target is T-P3's chassis body (at 1 cm = 0.01 m the wreck box still fits one donor hull, unchanged)"),
    "T-CO3": ("next", "keep the donor's flags (38/42 = 1, the 4 wheels = 0 with `world_collision_body_id` -1) and restate the reason as a donor carry: the drivable asset has 2 bodies (chassis + weapons pod, 3 boxes, 1 constraint) and 0 per-part bodies (`COLLISION_WHERE.md`), while the donor gives 38 parts their own - a declared difference, not a BmAK value - and bm-RC2 has 61 parts so the 42 denominator is stale"),
    # --- T-3, the factors the first table never named ----------------------
    "T-G6": ("keep", "BmAK sim radius 0.64 m vs the mesh 0.683: the mesh is the contact radius"),
    # --- T-3 suspension bridge (2026-11-06): `suspension-unit-bridge.md`, 14/14 oracles -------
    "T-S6": ("next", "moved off blocked: the unit bridge is derived (`tmp/freebuff/reports/suspension-unit-bridge.md`, 14/14 oracles) - TravelDown 40 cm -> length 0.40 m at the fleet median static sag 0.4542 gives strength 13.500 s^-2, BmAK 3000 at the decoded 210 kg gives 14.286 (fit error +5.8% / -5.5%), damping 300 -> zeta 0.189 (-4.4%) -> compression/relaxation 1/2 (-31.1% on integer quantisation), front bias 10 -> hardpoint offset -0.10 (0.0% vs the fleet median); still open and carded: droop + travel-up (B-22), per-mode and stationary rate (B-23)"),
    # --- the suspension/mass keep-audit (2026-11-06): every COMPROMISE gets its replacement ---
    # `why` is the short form; `tmp/freebuff/reports/keep-audit-suspension-and-mass.md` carries the
    # decode behind each row and the reason the replacement is or is not a number.
    "T-M3": ("next", "keep -0.3, re-stated as a declared fleet value rather than a translation: BmAK has no CoM member at all (the four `RB_BodySetup` exports carry no mass, inertia or tensor tag) and the one derived candidate (+0.148 m rearward, body bbox vs wheelbase midpoint) is rejected - the member's axis convention is UNKNOWN, +0.148 is above the fleet maximum +0.1, and -0.3 is what QA-1's handling was tuned on; the lever for a real weight distribution is the hull mass blocks, not the bias (`keep-audit-suspension-and-mass.md` T-M3)"),
    "T-S4": ("next", "keep 0 and record what it is not: BmAK's roll control is a native stay-upright constraint whose four values are serialised in no package (`RB_StayUprightSetup` 2 B / 0 tags, 0 exe store sites for the damping), so 0 reproduces 'no shipped car uses the field' and no replacement value exists to write - roll feel must come from a measured take (`keep-audit-suspension-and-mass.md` T-S4)"),
    "T-S5": ("next", "replacement 0.1 front / 0.05 rear - the donor's asymmetric pair - instead of the symmetric 0.2 fleet median: BmAK's lateral slip gains are asymmetric (rear `LatSlipFactor` 1.6, front inherited; handbrake 1.5 front / 1.1 rear) and the symmetric pick discarded the one thing BmAK states about front-vs-rear grip; the slip-gain -> force-offset mapping stays UNKNOWN, so the pair is a decision, not a conversion (`keep-audit-suspension-and-mass.md` T-S5)"),
    "T-R2": ("next", "keep 0.1 / 0.1 until the triple is decoded: `RVehicleSimBatmobile.Drag` @16, `DragNoLoad` @20 and `DriftDrag` @712 exist in the class dump and carry no decoded value, and one arcade multiplier cannot hold a load-dependent pair - T-A2's absence proof stops at `SVehicleSimCar`, one class short; the decode is card T-26 (`keep-audit-suspension-and-mass.md` T-R2)"),
    "T-R3": ("keep", "LORE-EXACT: BmAK has no shape-cast member anywhere and its four wheels are raycasts (`Batmobile.SimulationModel`, export 5282), JC3 0 is raycast on all 26 6 t+ and 35 3-8 t land vehicles - the same contact model on both sides, so there is no replacement value and no fit error; residual `raycast_offset` 0 = the ray starts at the hub (T-G6)"),
    "T-ST7": ("next", "operator ruling 2026-11-06 (option A, no compromise): 0.25 s low speed = 55 deg / 220 deg/s and 0.091 s high speed = 20 deg / 220 deg/s, so the whole rate is carried; the 0.5 s 'family floor' is refuted by T_ST7B_FLOOR.md (0.25 s on 4 AI twins, 0.3 s on 2 player bike modules)"),
    "T-K4": ("next", "replacement `min_time_to_block` 0.3 = `HandBrakeOffTime` 0.3 s (INFERRED kind-match) with `handbrake_friction_factor` 4.0 from T-K3, and the front axle composed as yaw torque: all four BmAK wheels carry `HandbrakeLatSlipFactor` (front 1.5, rear 1.1) but JC3 ships `front.handbrake` 0 on 145/145, so the rotation the front slip would make must come from `drift.counter_steer_torque_handbrake`, with 1.1/1.5 = 0.733 the share to recover; the ledger's 5 was stale - the bytes carry 1 (T-K2) (`keep-audit-steering-and-drift.md` section 8)"),
    "T-DR1": ("next", "replacement `min_speed_to_drift_kmph` 0 and `steering_sensitivity` 2: `HandbrakeOnSpeed` 10,000 cm/s = 360 km/h is above the car's 336 km/h top speed and `HandbrakeOffSpeed` 1 cm/s = 0.036 km/h, so BmAK has no effective gate (0 ships in 4 builds); `DriftCorrectionSteerSpeed` 1.0 with `DriftSteeringAssist` absent means no drift steering gain beyond the base rate, and the fleet median is 2; the remaining cells (45 deg max, entry 20 / exit 2, yaw damping, handbrake torque) have no BmAK member and stay JC3-native, labelled as such (`keep-audit-steering-and-drift.md` section 9)"),
    "T-EF1": ("keep", "tire effects are fleet-invariant"),
    "T-DM7": ("next", "moved off `out`: an outgoing contact-damage member exists on every vehicle - `rotor_collision.damage_to_other_per_second` 100000/s with `light_object_mass_ratio` 0.02, `mass_ratio_when_no_mass` 0.1 and `min_rpm` 30 (n=232, donor included) - so the outgoing channel is data, not a gap; the speed band (20->150, strafe 2.25, boost 2.0) has no JC3 member and whether a `CCar` evaluates the block is UNKNOWN (carrier `tmp/freebuff/reports/carrier-ram-and-dodge.md`)"),
    "T-DM8": ("keep", "impact_damage_factor 0 = incoming collision damage off, matching the BmAK health bar; a declared switch, not a value"),
    "T-DM9": ("next", "T-14 decided option B: invulnerable stays 0 and ARM-1/ARM-2 ride on the armour channels plus max_health (T-DM1, B-09 writes it). Option A's `CCar.invulnerable` whole-vehicle gate is unproven for a vehicle root (DAMAGE_MECHANISMS.md section 4) and would make ARM-2 impossible"),
    "T-FX6": ("epe", "vehicle effects are carried in the entity graph"),
    "T-AU5": ("next", "the 10 banks once called absent are all present (AUDIO_BANKS.md: 10 found, 0 absent), so only the JC3 slot is missing; these three event families are not among AUDIO_MAP.json's 361 rows, so their own bank is UNKNOWN and is the next input"),
    "T-W1": ("superseded", "refuted by G2-10/G2-11: the fleet's vehicle weapon ids and two driver slots on `CCar`, and the donor chassis ships `w618_sportsmuscle_missile`; split per weapon into T-11 (WPN-1…WPN-12), slots gated by D-3/D-7"),
    "T-BM1": ("superseded", "split: the mode scalars/curves and `ArmourModeDamageReduction` go to T-15 (gated by D-2), the transformation pose to T-12; turn-on-the-spot stays a named omission, proof `Research/JC3Grab/TANKTURN.md` (no tank-only member, 0 in any driving module)"),
    "T-AC1": ("next", "moved off `out`: the carriers exist as a composed pair - `CustomLandGlobal.drift.max_drift_torque` (0x48, the fleet's only yaw torque on a land vehicle, 0..35000) for yaw and `AerodynamicSurface.turn/pitch_steering_factor` (0x38/0x3C) for air authority; no exact airborne-gated torque member exists (0 `air_control`/`yaw_torque` rows in `Research/JC3Grab/VOCABULARY.md`), so the gap is the airborne gate the build composes (build card `tmp/freebuff/reports/air-control-closest-system-plan.md`, carrier `tmp/freebuff/reports/carrier-air-control.md`)"),
    "T-RA1": ("blocked", "moved off `out` to `blocked`: no road-assist, dodge, shove or kill-flip member exists at any layer (modules, entity graphs, `CDamageController`, `.physicsc`, script layer), so the capability to be found is a triggered, non-damaging impulse/torque with target selection and a duration - backlog card G2-35 (`Research/specs/G2-35.md`), carrier `tmp/freebuff/reports/carrier-ram-and-dodge.md` section 8/9"),
    "T-SR1": ("next", "moved off `out`: `DriverLean.righting_torque` (1500..4000, 23 rows = 18 bikes + 5 jet-skis, 0 aircraft per `Research/challenge/card-T-10.md` A4) carries BmAK's 2000 as a land self-righting torque and the Havok `TYPE_SETUP_STABILIZATION` atom (+0x0B0, 419/419 hinges, `Research/JC3Grab/PHYSICS_LIMITS_REVIEW.md`) is the closest StayUpright constraint; a car module shipping `DriverLean` is UNKNOWN, so the build composes it (build card `tmp/freebuff/reports/air-control-closest-system-plan.md`)"),
    "T-PA9": ("keep", "actor plumbing carried by the entity graph"),
    # --- T-17 (2026-10-28): effects translation, one row per effect feature ------------------
    # `why` is the short form; T13_FX.md §4/§5 carry the long proof and the authoring plan, and
    # t17_fx.py --check verifies the cells, the disposition and the chosen effect path still
    # re-derive. T-FX9/12/13/16/20 left `out` on 2026-11-06 (brief 8202): five research reports
    # replaced the keyword test with a shipped carrier or an authoring plan.
    "T-FX7": ("epe", "afterburner flame = the donor's car_cycle_base_dual_nitrous effect under the EngineNitro usage (G2-22)"),
    "T-FX8": ("epe", "always-on exhaust = the donor's car_cycle_base_dual effect under EngineRunning (G2-22)"),
    "T-FX9": ("next", "carrier `effects/jc_vehicles/exhaust/car_speedrom_heater.effc` (12 vehicles, 24 `z80_exhaust_heat_l/r` attachments, both distortion texture families in its bundle; `fx9-heat-haze-source.md` §8) at the `Afterburner` socket; plan = attach, then tune the 4 sprite `RenderBlockData[0]` constants + `MaxParticles` in a private copy, in place; gap = no member names a blend or the per-emitter texture (`effc-format-writable.md` §4)"),
    "T-FX10": ("next", "cannon muzzle flash = tank_canon_muzzleflash (11 vehicles) at CannonMuzzle; needs the T-11 clone"),
    "T-FX11": ("next", "Vulcan muzzle flash = helicopter_minigun_muzzleflash (15 vehicles) at ChainGunMuzzle; needs the T-11 clone"),
    "T-FX12": ("next", "linear half = the cloned `WeaponTuning` (`tracer_fire_width` 0.5 @0x188 already equals the 50 uu ribbon, `tracer_time_to_live` 0.0 @0x190 -> 1.25 s, 8 members); art half = a private copy of `missile_trail_car.effc` with two emitters (ribbon 0.50 m / 1.25 s / 8 per s, sprite 0.035-0.05 s / 1 per s / -0.50 m) - growth, card B-17; JC3 binds no effect to a bullet in flight (`fx12-16-tracer-and-trail.md` §8-§10)"),
    "T-FX13": ("next", "carrier = `SAttachedEffect ShellEjection` (Effect 600259254, Usage 4131019937 = `Fire`, `name_hash` 3811014039, no `world`) under the mounted-MG entity + `bullet_eject_minigun.effc` (6,703 B, 30-particle cap, gravity `Params[12]` -9.82, cone `Params[9]/[10]`); 14 decoded containers / 5 vehicle dirs (21 for capstone); gap = no spawn-rate member (BmAK 4/s for 1.0 s is code-side) and the cone axis is not decoded (`fx13-shell-casings.md` §3/§4/§7)"),
    "T-FX14": ("next", "missile trail = missile_trail_car (2 vehicles, on the donor) at MissileL/R; needs the T-11 missile (D-7)"),
    "T-FX15": ("next", "cannon impact = the 7-variant tank_explosive_* family (19 vehicles) on the hit surface; needs the T-11 cannon"),
    "T-FX16": ("next", "no bullet-bound carrier: the round trail is the T-FX12 private copy's sprite emitter (0.035-0.05 s, 1 per s, -0.50 m) alongside the ribbon (0.50 m / 1.25 s / 8 per s) from `missile_trail_car.effc`; the old `0 of 955` named no search term, so it was UNKNOWN not a negative (`FX16_TERM.md`)"),
    "T-FX17": ("epe", "tyre kick-up = the donor's 6-variant dust_trail_* family (161 vehicles) on the wheel parts (T-EF1)"),
    "T-FX18": ("epe", "slide dust = the donor's 5-variant chassis_slide_* family (289 vehicles) on the body (T-EF1)"),
    "T-FX19": ("epe", "BmAK ships 0 wall-scrape systems (G1-16); the donor already carries spark_trail_02_med at the ScrapeSparks sockets"),
    "T-FX20": ("next", "authoring plan: private copy of `car_cycle_base_dual_nitrous.effc` (donor boost glow, 20,671 B in its `.ee`) restyled on `t_velocity_streak_alpha_dif.dds.1_1b.trim` (657 B, in the donor `.ee`) at the `BrakeTrailL/R` sockets; gap = no light member names a trail (25 members), no `Brake` behaviour (9 states), and BmAK `BrakeTrail0/1` serialise no system so width/length/colour are UNKNOWN (`fx20-brake-trail.md` §3/§6/§8)"),
    "T-FX21": ("epe", "death explosion = the donor's exp_car_01 (126 vehicles) under OnExploded (G2-22) plus the blast tune (G2-10)"),
    "T-FX22": ("epe", "burn states = the donor's dmg_fire_engine / _spread_base / _spread_roof family under the damage-state usage"),
    "T-FX23": ("epe", "engine smoke = the donor's dmg_smoke_engine under EngineSmoking (23 vehicles), then dmg_post_burn"),    # --- T-18 (2026-10-28): lights translation, one row per entry of the Batmobile rig ------
    # `why` is the short form; T14_LIGHTS.md §3 carries the target, the anchor and the proof, and
    # t18_lights.py --check re-derives the cells, the disposition and the target of every row.
    "T-L8": ("next", "HeadLight1 = the donor's `Sport_Muscle_Headlight_Point_Left` row 13 + `Sport_Muscle_Headlight_Volume_Left` row 8, repointed at sportsmuscle_body with the BmAK colour (T14_LIGHTS.md §3)"),
    "T-L9": ("next", "HeadLight2 = the donor's `Sport_Muscle_Headlight_Point_Right` row 19 + `Sport_Muscle_Headlight_Volume_Right` row 20, repointed at sportsmuscle_body with the BmAK colour (T14_LIGHTS.md §3)"),
    "T-L10": ("out", "the ChainGunMuzzle spot is a weapon light: the fleet's 9 behaviours have none for a gun, and the muzzle flash is the T-FX11 .effc - proof `Research/JC3Grab/LIGHT_SYSTEM.json` (`module.behaviors`) + `Research/JC3Grab/LIGHT_SYSTEM.md` §6"),
    "T-L11": ("next", "HeadLight1 = the donor's `Front_Left_Point` row 17 + `Front_Left_Volumetric` row 12, repointed at sportsmuscle_body with the BmAK colour (T14_LIGHTS.md §3)"),
    "T-L12": ("next", "HeadLight2 = the donor's `Front_Right_Point` row 11 + `Front_Right_Volumetric` row 14, repointed at sportsmuscle_body with the BmAK colour (T14_LIGHTS.md §3)"),
    "T-L13": ("next", "LWheelLight = custom entry `sportsmuscle_wheel_f_l_arch` (preset_id 0, G2-33 §7 recipe) - no JC3 preset is this lamp"),
    "T-L14": ("next", "RWheelLight = custom entry `sportsmuscle_wheel_f_r_arch` (preset_id 0, G2-33 §7 recipe) - no JC3 preset is this lamp"),
    "T-L15": ("next", "BrakeLightL = the donor's `Sport_Muscle_Rear_Break_Left` row 18, repointed at sportsmuscle_body with the BmAK colour (T14_LIGHTS.md §3)"),
    "T-L16": ("next", "BrakeLightR = the donor's `Sport_Muscle_Rear_Break_Right` row 7, repointed at sportsmuscle_body with the BmAK colour (T14_LIGHTS.md §3)"),
    "T-L17": ("next", "BattleModeSpotLight = the graph's unreferenced `Front_Secondary_Head` given a module row on sportsmuscle_body (T14_LIGHTS.md §3)"),
    "T-L18": ("next", "HeadLight1 = custom entry `headlight_battle_left` (preset_id 0, G2-33 §7 recipe) - no JC3 preset is this lamp"),
    "T-L19": ("next", "HeadLight2 = custom entry `headlight_battle_right` (preset_id 0, G2-33 §7 recipe) - no JC3 preset is this lamp"),
    "T-L20": ("next", "LWheelLight = custom entry `sportsmuscle_wheel_f_l_arch_battle` (preset_id 0, G2-33 §7 recipe) - no JC3 preset is this lamp"),
    "T-L21": ("out", "the `VEHLT_ForensicsLight` rig (12 entries) is a scanner mode, not the car's lights and the fleet has no forensics behaviour - the card keeps it out; proof `Research/BatmobileGrab/LIGHTS.json` + `Research/JC3Grab/LIGHT_SYSTEM.md` §8"),
    "T-L22": ("out", "the `VEHLT_ForensicsLight` rig (12 entries) is a scanner mode, not the car's lights and the fleet has no forensics behaviour - the card keeps it out; proof `Research/BatmobileGrab/LIGHTS.json` + `Research/JC3Grab/LIGHT_SYSTEM.md` §8"),
    "T-L23": ("out", "the `VEHLT_ForensicsLight` rig (12 entries) is a scanner mode, not the car's lights and the fleet has no forensics behaviour - the card keeps it out; proof `Research/BatmobileGrab/LIGHTS.json` + `Research/JC3Grab/LIGHT_SYSTEM.md` §8"),
    "T-L24": ("next", "Dashboard_Light = the donor's `Dash_Light` row 2, repointed at sportsmuscle_body with the BmAK colour (T14_LIGHTS.md §3)"),
    "T-L25": ("out", "HeadLight1a is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L8"),
    "T-L26": ("out", "HeadLight2a is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L9"),
    "T-L27": ("out", "HeadLight1b is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L8"),
    "T-L28": ("out", "the `HeadLight1c`/`HeadLight2c` sockets are not in the shipped mesh, so the flare has nowhere to hang; proof `Research/BatmobileGrab/LIGHTS.json` (`problems`) + `Research/BatmobileGrab/LIGHTS.md`"),
    "T-L29": ("out", "HeadLight2b is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L9"),
    "T-L30": ("out", "the `HeadLight1c`/`HeadLight2c` sockets are not in the shipped mesh, so the flare has nowhere to hang; proof `Research/BatmobileGrab/LIGHTS.json` (`problems`) + `Research/BatmobileGrab/LIGHTS.md`"),
    "T-L31": ("out", "RWheelLight_top is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L14"),
    "T-L32": ("out", "RWheelLight_bottom is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L14"),
    "T-L33": ("out", "LWheelLight_top is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L13"),
    "T-L34": ("out", "LWheelLight_bottom is a LensFlareComponent: JC3 has no flare member (G1-17), the glow is T-L13"),
    "T-L35": ("next", "BootLight = custom entry `boot_light` (preset_id 0, G2-33 §7 recipe) - no JC3 preset is this lamp"),
    # --- T-11 (2026-10-28): weapons translation, one row per WPN code + the two decision rows ------
    # `why` is the short form; T7_WEAPONS.md carries every aspect with its class, and t7_weapons.py
    # --check re-derives the cells, the disposition and every edit against both game sides.
    "T-WP1": ("next", "heavy cannon = `w602_mediumtank_canon` on `main_weapon` (the medium tank's own binding) with fire_rate 1.75->2 s and velocity 500->400 m/s from the BmAK values; the 24:2 damage ratio is T-14's health row, not a weapon number"),
    "T-WP2": ("next", "Vulcan = `w603_mediumtank_mgun` on the second driver slot `id:00568A74` with fire_rate 0.1->0.138 s; barrel spin is the T-12 P-03 part; heat is a proven absence on both sides (G1-23)"),
    "T-WP3": ("next", "missiles = the donor's own `w618_sportsmuscle_missile` (4 fire points, blast 1100 in 8 m); lock-on has a HUD marker but no time/range member, so that half is UNKNOWN (G2-25)"),
    "T-WP4": ("next", "launcher half only (operator ruling 4, 2026-11-06: split approved): a `w618` clone + G2-16's entity-level `CForcePulse` copy, plus the Fire Leech's guidance - `w143_rpg_fire_leach` `missile_turning_speed` 300 / random 60 / acceleration 30->65 over 0.2->10 s / accel-random 2->5 (5 values; w618's own turning speed is 0) - and a NEW lock-on `AutoAim` with the fleet lock-on preset's classes (`CanTargetCharacters` 0), w143's 0.12/0.15 cone and `MaxAimDistance` 120 m; every fire-block value stays w618's. The disable half is T-WP15, and the 2.0 s lock hold / 8-target salvo / reticle link have no member (cards B-24 / B-25)"),
    "T-WP15": ("next", "moved off `out` on 2026-11-08: the disable half is a composed route, not an omission - the launch is T-WP4 (a `w618` clone carrying the entity `CForcePulse` + `truck_emp.ftune`), the stall is T-WP5's pulse (100 in 25 m, second slot) and the stalled state is written by a cloned `CEMPWeapon` (`w702_emp`), because `is_disabled_by_emp` has 0 bindings in the 1,941 vehicle entries and no NPC `RVehicle*` class carries an EMP member; what stays UNKNOWN is the duration only (`DisableEnemyDuration` @2400 serialises no value), so the four probes Q-EMP-1…4 are pilot cards and nothing is launched (`tmp/freebuff/reports/emp-immobiliser-forcepulse-plans-v2.md`)"),
    "T-WP5": ("next", "moved off `blocked`: the burst is the entity `CForcePulse` `EMP` + `truck_emp.ftune` (100 in 25 m at full radius, unique flag triple 4912FC04=0/AE6F7EFF=1/CF4F7880=1, `emp_flatbed_table`) and the disable is the engine's own `CEMPWeapon` (`w702_emp`, 0 of 88 vehicle weapon components), so the missing link is one named writer - BUILD card B-18 with probes Q-EMP-1…4 (report `tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §7-§8); BmAK-exact: no"),
    "T-WP6": ("blocked", "the entity-graph clone is decoded and buildable (a `CVehicleCargoBay`-style anchor with `world`/`enabled`/`enable`/`disable` at the `WinchOrigin` socket, the `transport_rope_winch` mesh, BmAK's two `RSimpleRopeComponent`s and its VFX/SFX), but no JC3 data pulls: 0 functional winch classes, 0 of 53 module types and 0 of 67 part behaviours with length/force/reel/release - the code-level pull loop is card `Research/specs/B-16.md`"),
    "T-WP7": ("next", "moved off `out`: closest chain = two `SAttachedEffect` rows on a drone-side entity (beam + success; `Effect`+`Usage`, 5,342 objects / 232 graphs), the SAM context-act hack as the interaction (`CInteractionGraph`, `use_item`, 2 `CInteractionTrigger` volumes, `rico_contextact_hack_sam*.anim`) and `faction` on weapon points; the allegiance flip has no member - BUILD card B-19 (`tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP7); BmAK-exact: no"),
    "T-WP8": ("next", "moved off `out`: the base sonar is a visible pulse - entity `CForcePulse` with `gen_explosion_5m_nodamage.ftune` (0 damage / 5 m, 2 pulses), a private ring `.effc` and the `BmGame.BML_Sonar` bank (355,830 B, 7 HIRC / 6 verified events); the trigger and the reveal are BUILD card B-20, the treadmark half is `missing-object` on BmAK's side (`tmp/freebuff/reports/sonar-and-scan-pulse.md` §4); BmAK-exact: no"),
    "T-WP9": ("next", "moved off `out`: closest chain = a mounted weapon entity + `missile_base_tuning.*` + the `BattleModeSpotLight` fire position with `LaunchRotationOffset` 5461 = 30.0 deg baked into `SWeaponPoint.world`, plus the HUD `CreatePoi` tracker graph (`graphs/mission/mm130/mm130_tracker.gdc`); no homing flag/delay and no distance member exist - BUILD card B-21 (`tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP9); BmAK-exact: no"),
    "T-WP10": ("next", "operator rule 2026-11-06 supersedes the 2026-10-28 lethality decision: no non-lethal carrier exists (no stun/taser/ragdoll/water/electrical path - `tmp/freebuff/reports/non-lethal-cannon-carrier.md`), so the closest system is a private tune with `base_tuning.damage` 0 + impulse + the 0.75 s cadence and gel VFX; the toggle becomes a second weapon entity in `Research/specs/B-15.md`"),
    "T-WP11": ("keep", "the afterburner is JC3 nitro and is live since test-091 (T-B2/T-B3); the `Batmobile_Booster` gadget mesh is a cockpit part row (B-04)"),
    "T-WP12": ("next", "WPN-12's API facts (2 slots, 14 reticle shapes, cooldown 0..1, no heat param, one lock POI) - the hud.gfx translation is T-19, which lists T-11 as a dep"),
    "T-WP13": ("next", "forced on operator ruling 3: the reference graphs (Imperator `v0202_car_capstone_bavariumtank`, Urga Mstitel `v2601_helicopter_urga_heavyassault`) carry 2 non-null slot pointers each and a `BavariumShield` PART that is not a slot, so a third slot is a decision, not a decoded value. Build 4 `CCar` roots x (`main_weapon` + `id:00568A74`) = 8 slots for the 8 slot-able BmAK objects, using only decoded property names (0 invented), with the 5 non-slot gadgets carried outside the slot space (`CForcePulse`, nitro, winch B-16, sonar B-20, hacker B-19); gaps: `RiotSuppressorMuzzle` has no point and the Joker weapons have no sockets"),
    "T-WP14": ("next", "the 2026-10-28 decision (accept JC3 lethality, no toggle) is superseded by the 2026-11-06 rule: the row now takes the closest system (0-damage + impulse tune) and the missing mode toggle is a BUILD gap, not an accepted compromise (proof `tmp/freebuff/reports/non-lethal-cannon-carrier.md`, gap `Research/specs/B-15.md`)"),
    # --- T-20 (2026-10-28): world translation, one row per WLD requirement ---------------
    # `why` is the short form; T15_WORLD.md carries the numbers and t15_world.py --check
    # re-derives the cells, the disposition and the ledger from the five G2 world files.
    "T-WLD1": ("next", "the Rebel Drop item is one record keyed by `hash_jenkins(leaf)` = 443190071; B-13 writes Name/UIName/UIImagePath/UIVideoPath (G2-26)"),
    "T-WLD2": ("next", "the unlock is an `ItemReward` link on the donor's own task 1361701860 (Type 19), not an item field; the shipped mod proves the item.onlinec write path"),
    "T-WLD3": ("next", "all 45 vanilla vehicle drops share Type 1/UIType 3/Rewardable 1, so the donor's profile is the class value; the enums' meanings are UNKNOWN"),
    "T-WLD4": ("next", "the key is `HashJenkins(leaf)` and the shipped `_debug` leaf's pair 1621485476 is present 11/11 in bm-013's drop (text BATMOBILE); 443190071 belonged to a leaf that never ships. Remaining: carry the drop into the RC and Q-1"),
    "T-WLD5": ("next", "the icon is a plain texture named after the leaf and the new leaf has none; copy the donor's 18,688 B file under the new name (G2-32)"),
    "T-WLD6": ("next", "the `_desc` key `HashJenkins(leaf + \"_desc\")` = 4081821928 is present 11/11 in bm-013's drop with the Batmobile blurb; the remaining step is T-WLD4's drop carry and Q-1"),
    "T-WLD7": ("keep", "UITypeDescription/UIFlagDescription resolve 11/11 to SPORTS CAR / SPORTS CARS - a category caption, valid for any vehicle in the slot"),
    "T-WLD8": ("epe", "29 entry objects placed on the cockpit sides by T-13 (77/85 in the 0.05-0.30 m band); B-05 moves the graph"),
    "T-WLD9": ("epe", "26 exit objects ride the placed point nodes; state names unchanged so the animation wiring stays valid (G2-18 §4)"),
    "T-WLD10": ("epe", "the `point.stunt*` nodes are placed on the hull top by T-13 (roof y 2.0811, deck y 1.3606)"),
    "T-WLD11": ("next", "the 22 bound vertices are placeable on the RC2 shell by the derived spine fit (P-1: 22/22 at 0.036-0.105 m, up-cos 0.749-0.994); the write is 22 `start_transform[12..14]` + `vertices3D_local` pairs, and a 3-column ribbon (deform indices above 134) closes the roof-vent chord"),
    "T-WLD12": ("next", "mass 975 -> 6000 = 6.154x the donor (T-M1's 6 t class row); the contact hull is T-22's, and the mass unit is UNKNOWN (G2-34)"),
    "T-WLD13": ("keep", "the donor already sinks (`will_sink` 1, buoyancy 2/drag 100/radius 0.55) and test-091's modules are identical, so D-8's lore route ships as it stands"),
    "T-WLD14": ("keep", "the water kill/stall constants are fleet-wide in `vehicle_common` (10/20/20/50 ms, 30 s engine) with 0 overrides; R7 forbids editing the shared file"),
    "T-WLD15": ("next", "translated to the closest system: `CVehicleCargoBay` (7 members) and `CGrapplingHookPropData` (33 tags) are the only attach/release objects, and the car supplies its 6,000 mass (6.154x the 975 donor) plus the `grapple_pull` damage channel; the pull itself is native code, so Q-3 #5 verifies it"),
    "T-WLD16": ("keep", "12 CVehicleCargoBay objects already enabled; the 6000 car is 15.0/6.0/40.0 % of the cargo plane, boat and flatbed bodies"),
    "T-WLD17": ("blocked", "data-level: `bay_helicopters` = [] - 0 of 23 helicopters carries a `CVehicleCargoBay` and the census has no helicopter hook class; the closest carrier is the cargo plane's bay + the compound cargo-tank entity (25,000 + 40,000); the missing capability is the native attach rule a cloned bay would need - card `Research/specs/B-16.md`"),
    "T-WLD18": ("keep", "the spawn table keys on the full path string and the new leaf has 0 records there; D-6 standalone means nothing is added"),
    "T-WLD19": ("keep", "the donor's record carries ambient+liberated and matches 1 of 41 selectors, so replacing that leaf would put AI Batmobiles in traffic (G2-29, D-6)"),
    # --- T-15 (2026-10-28): modes translation under D-2's hybrid ---------------------------
    # `why` is the short form; T11_MODES.md carries the numbers and t11_modes.py --check
    # re-derives the cells, the disposition and the ledger from MODES.json / CAMERA.json.
    "T-MD1": ("next", "the afterburner is JC3 nitro (`arcade.nitro_boost`, 145/232) and is live since test-091; a hybrid has no pursuit gate, so the boost is always on tap"),
    "T-MD2": ("next", "moved off `blocked`: the launcher (`w618` clone), the entity `CForcePulse` (`truck_emp.ftune`, flag triple, `emp_flatbed_table`) and the engine's `CEMPWeapon` (`w702_emp`, 500/50 m) are the disable chain end to end, and the missing writer of `is_disabled_by_emp` (exe 0x24EA080) is BUILD card B-18 with probes Q-EMP-1…4; the EMP is mode-independent so the hybrid carries it - BmAK-exact: no (`tmp/freebuff/reports/immobiliser-and-emp-trigger.md` §7-§8)"),
    "T-MD3": ("keep", "ram immunity is the entity switch `impact_damage_factor` 0 (T-DM8) - mode-independent, one car carries it as-is"),
    "T-MD4": ("keep", "`StandardTorqueVSpeedCurve` and `BoostTorqueVSpeedCurve` are read from the G1 object stream (6 and 7 points, identical in all four packages) - the curves live on `RVehicleSimBatmobile`, outside the mode families G1-21 records"),
    "T-MD5": ("blocked", "re-opened by D-2 on 2026-11-06: a hybrid cannot hold a second speed curve, the battle entity can - the row waits on D-2's re-resolution to two variants (B-12) and on the runtime swap that is UNKNOWN (`mode-switch-carriers.md` §7 U1)"),
    "T-MD6": ("blocked", "the cap needs a second value set and a variant supplies one, but no decoded member is a speed cap - the row waits on D-2 and on B-12's read of the battle copy's modules"),
    "T-MD7": ("blocked", "four of the six factors land on the battle entity's own handling modules; the two slip scales have no member on either side, so the variant carries a partial set - the row waits on D-2 and on the runtime swap"),
    "T-MD8": ("blocked", "G2-21 proved the requirement has no data carrier and a second variant does not change that, so the pivot stays a named omission in both variants and the row waits on a native mechanism"),
    "T-MD9": ("next", "turret/cannon aim is T-12's part angles and the weapons are T-11's; D-7 removed the per-mode split"),
    "T-MD10": ("keep", "`ArmourModeDamageReduction` is 0 on the three packages that serialise it, so the hybrid's single armour profile is already the BmAK value"),
    "T-MD11": ("keep", "`BattleModeCamFOV` 60 sits inside the delivered `.ctune`'s 55-63 band, so no value changes; only the mode switch is missing (T-CAM10's second tune needs two variants)"),
    "T-MD12": ("next", "the four `VEHLT_BattleModeLight` lamps map onto JC3's `HeadLight` behaviour (T-L17-T-L20) because the fleet's nine light behaviours have no battle value: they light with the headlights"),
    "T-MD13": ("blocked", "re-opened by D-2 on 2026-11-06: the pose is a per-entity constant the battle variant can hold, the animation is not - the row waits on D-2 and on B-12"),
    "T-MD14": ("blocked", "D-2's reopening gives T-16's 30 battle events a second entity to live on, but a new `Usage` hash still needs a consumer (U1) and swapping entities is not an audio transition, so the row stays blocked"),
    "T-MD15": ("next", "D-2's 2026-10-28 answer chose a single hybrid entry, so the variant table has one row and the split's values are recorded per row rather than built; D-2 was reopened on 2026-11-06, so whether this row survives is B-12's outcome"),
    "T-L10": ("next", "custom `preset_id 0` row `muzzle_light` on the gun bone - `light_type` 0 / `angle` 10 / `range` 10, `diffuse` 1/1/1 from `LightColor` 255,255,255 (LIGHTS_FORENSICS T-L10); the flash is `SAttachedEffect` `Usage` = `Fire` -> `effects/jc_weapons/muzzle_flash/rico_50cal_muzzleflash.effc` (21 carriers); no per-shot pulse member exists (T-25)"),
    "T-L21": ("next", "custom cone row `forensics_spot` - `light_type` 1 / `angle` 50 / `range` 50 / `diffuse` 0.765,1.000,0.957 plus the graph-side `spot_angle` 50 / `spot_inner_angle` 0 (LIGHTS_FORENSICS T-L21); the `bForensicsLightActive` 0x0884 state has no JC3 member (T-25)"),
    "T-L22": ("next", "custom cone row `forensics_head_left` - `light_type` 1 / `angle` 35 / `range` 30 / `multiplier` 5 / `cast_shadows` 1 / `volumetric_mode` 1 / `volume_intensity` 0.02, inner cone 10 (LIGHTS_FORENSICS T-L22); the enable state is T-25"),
    "T-L23": ("next", "custom cone row `forensics_head_right`, the same numbers as T-L22 (the two heads are identical in every package) (LIGHTS_FORENSICS T-L23); the enable state is T-25"),
    "T-L25": ("next", "no flare member, but three carriers are measured: `CarLight`+`Window` block copy from `sportsmuscle_headlight_f_l_01_lod1.rbm`, `volumetric_mode` 1 / `volume_intensity` 0.002 on the lamp entry, and `effects/flare/headlight_flare_01.effc` (8,079 B, in 160 vehicle bundles) spawned at the socket (lens-flare-carriers T-L25); the sprite binding is T-24"),
    "T-L26": ("next", "same three carriers as T-L25 on the right (`sportsmuscle_headlight_f_r_01_lod1.rbm`, the volumetric member, the flare effect) (lens-flare-carriers T-L26); the sprite binding is T-24"),
    "T-L27": ("next", "rides T-L25's left lens mesh - one `CarLight` block per mesh, a second `HeadLight` row on the same part is legal, the element stack collapses to one glow + one light + one sprite (lens-flare-carriers T-L27); the binding is T-24"),
    "T-L28": ("blocked", "socket and bone are null (`LIGHTS.json` problems); the carrier is the donor's body-hosted `HeadLight` pattern (rows 3/10 at `dashboard_LIG`/`front_primary_LIG`) and our body has no `_LIG` node with 0 `CarLight` blocks in the 25 assembled RBMs (lens-flare-carriers T-L28), so it waits on B-03 (block) and B-04 (node) - not an omission"),
    "T-L29": ("next", "rides T-L26's right lens mesh, second element of the right stack (lens-flare-carriers T-L29); the sprite binding is T-24"),
    "T-L30": ("blocked", "socket and bone are null (`LIGHTS.json` problems); same body-hosted pattern and the same missing `_LIG` node + `CarLight` block as T-L28 (lens-flare-carriers T-L30) - waits on B-03/B-04"),
    "T-L31": ("next", "wheel glare = an authored `CarLight` emitter in `sportsmuscle_wheel_f_r_lod1.rbm` (today `CarPaintMM`-first, no emissive block) + a `HeadLight` entry on part 27 at `Wheel_Frnt_Right_Disc` + an optional flare spawn (lens-flare-carriers T-L31); the emitter is B-03, the sprite binding is T-24"),
    "T-L32": ("next", "rides the T-L31 right wheel entry - one emitter, two BmAK elements, one shared geometry slot (lens-flare-carriers T-L32); the binding is T-24"),
    "T-L33": ("next", "wheel glare = an authored `CarLight` emitter in `sportsmuscle_wheel_f_l_lod1.rbm` + a `HeadLight` entry on part 26 at `Wheel_Frnt_Left_Disc` (lens-flare-carriers T-L33); the emitter is B-03, the binding is T-24"),
    "T-L34": ("next", "rides the T-L33 left wheel entry - one emitter, two BmAK elements (lens-flare-carriers T-L34); the binding is T-24"),
}


VOCAB = ("edit", "next", "keep", "epe", "re-read", "blocked", "out", "superseded")

# T-10: rows whose requirement moved to a phase-T card.  The card ids are checked for
# existence by `t10_reopen.py`, which owns the whole re-decision table.
SUPERSEDED: dict[str, list[str]] = {
    "T-L4": ["T-18"],
    "T-L7": ["T-18"],
    "T-LG4": ["T-18"],
    "T-LG5": ["T-18"],
    "T-FX4": ["T-11", "T-17"],
    "T-W1": ["T-11"],
    "T-BM1": ["T-12", "T-15"],
}


def parse_docs() -> list[dict]:
    rows: list[dict] = []
    seen: dict[str, str] = {}
    for tag, path in DOCS:
        if not os.path.exists(path):
            raise SystemExit(f"missing {path}")
        section = ""
        for line in open(path, encoding="utf-8"):
            h = HEAD_RE.match(line)
            if h:
                section = h.group(1).strip()
                continue
            if SKIP_SECTION.match(section):
                continue
            m = ROW_RE.match(line)
            if not m:
                continue
            rid = m.group(1)
            if rid in seen:
                raise SystemExit(f"{rid} appears twice ({seen[rid]} and {path})")
            seen[rid] = path
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append({"id": rid, "doc": tag, "section": section, "cells": cells})
    return rows


def load_edits() -> dict[str, int]:
    data = json.load(open(EDITS, encoding="utf-8"))
    counts: dict[str, int] = {}
    for e in data["edits"]:
        counts[e["row"]] = counts.get(e["row"], 0) + 1
    return counts


def build() -> int:
    rows = parse_docs()
    edits = load_edits()
    out = []
    problems = []
    for r in rows:
        dispo, why = DISPO.get(r["id"], ("keep", "build carries the proposal; nothing to edit"))
        if dispo not in VOCAB:
            problems.append(f"{r['id']}: bad disposition {dispo!r}")
        if dispo == "edit" and r["id"] not in edits:
            problems.append(f"{r['id']}: disposition edit but no row in {os.path.basename(EDITS)}")
        if dispo == "next" and r["id"] in edits:
            problems.append(f"{r['id']}: marked next but already in {os.path.basename(EDITS)}")
        if dispo == "superseded" and not SUPERSEDED.get(r["id"]):
            problems.append(f"{r['id']}: superseded without a successor card")
        if dispo != "superseded" and SUPERSEDED.get(r["id"]):
            problems.append(f"{r['id']}: has a successor card but is {dispo}")
        row = {**r, "dispo": dispo, "why": why, "edits": edits.get(r["id"], 0)}
        if dispo == "superseded":
            row["superseded_by"] = SUPERSEDED[r["id"]]
        out.append(row)
    for rid in edits:
        if rid not in {r["id"] for r in rows}:
            problems.append(f"{rid}: in {os.path.basename(EDITS)} but not in the tables")
    for rid in DISPO:
        if rid not in {r["id"] for r in rows}:
            problems.append(f"{rid}: disposition for a row the tables do not have")
    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"{LEDGER}: {len(out)} rows, {sum(r['edits'] for r in out)} edits over "
          f"{sum(1 for r in out if r['edits'])} rows")
    for p in problems:
        print("FAIL", p)
    return 1 if problems else 0


def load_ledger() -> list[dict]:
    if not os.path.exists(LEDGER):
        raise SystemExit("no T_ROWS.jsonl - run `t_rows.py build`")
    return [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]


def check() -> int:
    rows = parse_docs()
    ledger = load_ledger()
    edits = load_edits()
    problems: list[str] = []
    doc_ids = [r["id"] for r in rows]
    led_ids = [r["id"] for r in ledger]
    for rid in doc_ids:
        if rid not in led_ids:
            problems.append(f"{rid}: in the tables, missing from the ledger")
    for rid in led_ids:
        if rid not in doc_ids:
            problems.append(f"{rid}: in the ledger, not in the tables (stale)")
    if len(led_ids) != len(set(led_ids)):
        problems.append("ledger has duplicate ids")
    for r in ledger:
        if r["dispo"] not in VOCAB:
            problems.append(f"{r['id']}: disposition {r['dispo']!r}")
        if r["dispo"] == "edit" and r["id"] not in edits:
            problems.append(f"{r['id']}: edit disposition, no entry in the edit list")
        if r["dispo"] == "next" and r["id"] in edits:
            problems.append(f"{r['id']}: marked next but already in the edit list")
        if r["dispo"] not in ("edit", "next") and r["id"] in edits:
            problems.append(f"{r['id']}: in the edit list but disposition is {r['dispo']}")
        if not r.get("why"):
            problems.append(f"{r['id']}: no reason")
        if r["dispo"] == "superseded":
            if not r.get("superseded_by"):
                problems.append(f"{r['id']}: superseded without superseded_by")
            elif r["superseded_by"] != SUPERSEDED.get(r["id"]):
                problems.append(f"{r['id']}: superseded_by {r['superseded_by']} disagrees with "
                                f"the disposition table {SUPERSEDED.get(r['id'])}")
        elif r.get("superseded_by"):
            problems.append(f"{r['id']}: superseded_by set but disposition is {r['dispo']}")
    for rid in edits:
        if rid not in led_ids:
            problems.append(f"{rid}: edit row absent from the ledger")
    counts = {}
    for r in ledger:
        counts[r["dispo"]] = counts.get(r["dispo"], 0) + 1
    print(f"ledger {len(ledger)} rows | " + " ".join(f"{k} {counts.get(k,0)}" for k in VOCAB)
          + f" | edits {sum(edits.values())} over {len(edits)} rows")
    if problems:
        for p in problems:
            print("FAIL", p)
        print(f"{len(problems)} problem(s)")
        return 1
    print("check ok")
    return 0


def summary() -> int:
    ledger = load_ledger()
    by_doc: dict[str, dict[str, int]] = {}
    for r in ledger:
        d = by_doc.setdefault(r["doc"], {})
        d[r["dispo"]] = d.get(r["dispo"], 0) + 1
    for doc in sorted(by_doc):
        print(doc, dict(sorted(by_doc[doc].items())))
    fam: dict[str, set[str]] = {}
    for r in ledger:
        family = re.match(r"T-([A-Z]{1,3})", r["id"]).group(1)
        fam.setdefault(family, set()).add(r["dispo"])
    for family in sorted(fam):
        print(f"  {family:3} {' '.join(sorted(fam[family]))}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="parse both tables and write T_ROWS.jsonl").set_defaults(func=build)
    sub.add_parser("check", help="ledger vs tables vs the edit list").set_defaults(func=check)
    sub.add_parser("summary", help="counts by disposition").set_defaults(func=summary)
    a = ap.parse_args()
    sys.exit(a.func())


if __name__ == "__main__":
    main()
