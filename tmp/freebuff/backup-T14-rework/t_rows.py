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
    "T-E2": ("keep", "absolute torque stays 1393.5: +30% over the class fit, inside the fleet"),
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
    "T-P2": ("keep", "damage types are in VehicleDamage, carried"),
    "T-P3": ("next", "written (G2-30): 11 driveable boxes map onto 7 donor hull slots (body, 2 doors, 4 wheels); 21 are not driveable collision (18 debris, Root, turret, fin) and 11 T-8 parts have no slot; hull set + radius x k in `t16_collision.json`"),
    # --- T-2b, the other half ----------------------------------------------
    "T-PA1": ("epe", "wheel parts in the built graph"),
    "T-PA2": ("epe", "light points -> parts in the built graph"),
    "T-PA3": ("epe", "part -> collision body ids in the built graph"),
    "T-PA4": ("epe", "wheel_parts slots in the built graph"),
    "T-PA5": ("epe", "door parts in the built graph"),
    "T-PA6": ("epe", "constraint points in the built graph"),
    "T-PA7": ("epe", "non-deformable part list in the built graph"),
    "T-PA8": ("epe", "6 orphan sockets dropped, they cannot be driven"),
    "T-LG2": ("keep", "closed by t2_lg2.py: 21 rows / 22 objects, row-for-row the donor's"),
    "T-L7": ("superseded", "corrected by T-18: `Rear_Point` is not one of the 22 objects this rig's graph instantiates, so the boot lamp is a custom `preset_id 0` entry (row T-L35)"),
    "T-LG4": ("superseded", "closed by T-18: the absent preset is replaced by a custom `preset_id 0` entry on a new `sportsmuscle_wheel_f_*_arch` part (G2-33 §7), rows T-L13/T-L14"),
    # --- T-10 (2026-10-28): the `out` rows re-decided against the G2 evidence ----------
    # `why` is checked against the T-10 table by `t10_reopen.py --check`, so edit both.
    "T-LG5": ("superseded", "split: the battle-mode spotlight (16 entries) is a decoded behaviour value (`VEHLT_BattleModeLight`, G2-33) and moves to T-18 under D-2; the forensics rig (12 entries) stays a named omission - proof `Research/JC3Grab/LIGHT_SYSTEM.md`"),
    "T-AU1": ("keep", "LandAudio keeps its two members; the mapping is a bank task"),
    "T-AU2": ("keep", "engine bank already swapped (test-060)"),
    "T-AU3": ("blocked", "10 banks are absent from the install"),
    "T-AU4": ("edit", "LandAudio.max_rpm 10000 -> 4500, follows T-E1"),
    "T-FX1": ("keep", "break effects carried"),
    "T-FX2": ("keep", "burn effects carried"),
    "T-FX3": ("blocked", "no usage slot for an exhaust flame"),
    "T-FX4": ("superseded", "split: EMP has a carrier (`CForcePulse` + `CEMPWeapon`, G2-16) so the EMP/Immobilizer half moves to T-11 and the tyre-smoke half to T-17 (FX-3 `tire_effects`); seismic sonar stays a named omission - no sonar class in `Research/JC3Grab/ENTITIES.md`"),
    "T-FX5": ("keep", "23 unreferenced .effc belong to donor parts"),
    "T-DM1": ("keep", "max_health 2000 kept: 6 t p75 and land max; BmAK Health 1200 has no unit bridge"),
    "T-DM2": ("edit", "bullet armour 100 -> 99, the fleet maximum"),
    "T-DM3": ("keep", "heavy armour 20 carried"),
    "T-DM4": ("keep", "4000/1050/250 thresholds carried, at the fleet maximum"),
    "T-DM5": ("keep", "24 damage types and the part join carried"),
    "T-DM6": ("keep", "deform_scale 0 is a declared cosmetic switch (no crumple), outside the shipped 1..2 range; not a value"),
    "T-CO1": ("keep", "donor chassis by decision"),
    "T-CO2": ("next", "the largest box 3.1615x0.6342x1.0988 m fits one donor hull (longest axis 3.679 m) at 1 cm = 0.01 m, so no layout change; `t16_collision.json`"),
    "T-CO3": ("keep", "the donor's flags are carried: 38/42 parts = 1, the 4 wheels = 0 with `world_collision_body_id` -1 - wheels are sim-only on both sides (`t16_collision.json`)"),
    # --- T-3, the factors the first table never named ----------------------
    "T-G6": ("keep", "BmAK sim radius 0.64 m vs the mesh 0.683: the mesh is the contact radius"),
    "T-S6": ("blocked", "JC3 has no suspension bias/droop member or unit bridge for stiffness"),
    "T-ST7": ("blocked", "BmAK 220 deg/s is 0.25 s to lock; the JC3 family floor is 0.5 s"),
    "T-K4": ("keep", "rear-only handbrake, factor 1 = the 6 t median; e-brake force has no member"),
    "T-DR1": ("keep", "JC3-native drift block kept for character: sensitivity 4 vs 6 t median 2 and entry 20 vs 180, so not class evidence"),
    "T-EF1": ("keep", "tire effects are fleet-invariant"),
    "T-DM7": ("out", "stays `out`: G2-28 found no outgoing ram damage - its chain is hit -> own health and the only impact member is `impact_damage_factor` (incoming), and G2-17 refutes a collision trigger; proof `Research/JC3Grab/DAMAGE_MODEL.md` + `Research/JC3Grab/FORCEPULSE.md`"),
    "T-DM8": ("keep", "impact_damage_factor 0 = incoming collision damage off, matching the BmAK health bar; a declared switch, not a value"),
    "T-DM9": ("blocked", "VehicleDamage has no immunity member, but the entity root does: CCar.invulnerable int32 at epe+1167; 4-byte write, probe not yet built (DAMAGE_MECHANISMS.md)"),
    "T-FX6": ("epe", "vehicle effects are carried in the entity graph"),
    "T-AU5": ("blocked", "transformation/taser banks are absent from the install"),
    "T-W1": ("superseded", "refuted by G2-10/G2-11: 25 vehicle weapon ids and two driver slots on `CCar`, and the donor chassis ships `w618_sportsmuscle_missile`; split per weapon into T-11 (WPN-1…WPN-12), slots gated by D-3/D-7"),
    "T-BM1": ("superseded", "split: the mode scalars/curves and `ArmourModeDamageReduction` go to T-15 (gated by D-2), the transformation pose to T-12; turn-on-the-spot stays a named omission, proof `Research/JC3Grab/TANKTURN.md` (no tank-only member, 0 in any driving module)"),
    "T-AC1": ("out", "stays `out`, re-checked as the card asks: `gravity_multiplier_*` and `takeoff_pitch_damping` do exist (145 land vehicles; donor 1/1/1 and 0.5) but neither is a yaw torque - no `air_control`/`yaw_torque` member exists in `Research/JC3Grab/VOCABULARY.md`"),
    "T-RA1": ("out", "stays `out`: no ram-assist, dodge, shove or kill-flip member anywhere in the 52-type / 1,421-path vocabulary (`Research/JC3Grab/VOCABULARY.md`); the nearest real mechanism is the entity `impact_damage_factor` switch, which is T-DM8"),
    "T-SR1": ("out", "stays `out`: `righting_torque` exists but only in `DriverLean` on 23 aircraft and the donor has none, so there is no land carrier - self-righting stays a named omission (`Research/JC3Grab/VOCABULARY.md`, G2X HDL-6)"),
    "T-PA9": ("keep", "actor plumbing carried by the entity graph"),
    # --- T-17 (2026-10-28): effects translation, one row per effect feature ------------------
    # `why` is the short form; T13_FX.md §4 carries the long proof, and t17_fx.py --check
    # verifies the cells, the disposition and the chosen effect path still re-derive.
    "T-FX7": ("epe", "afterburner flame = the donor's car_cycle_base_dual_nitrous effect under the EngineNitro usage (G2-22)"),
    "T-FX8": ("epe", "always-on exhaust = the donor's car_cycle_base_dual effect under EngineRunning (G2-22)"),
    "T-FX9": ("out", "no heat haze: G1-16 heat-steam is 0 systems and FX_TABLE has 0 haze paths in 955"),
    "T-FX10": ("next", "cannon muzzle flash = tank_canon_muzzleflash (11 vehicles) at CannonMuzzle; needs the T-11 clone"),
    "T-FX11": ("next", "Vulcan muzzle flash = helicopter_minigun_muzzleflash (15 vehicles) at ChainGunMuzzle; needs the T-11 clone"),
    "T-FX12": ("out", "no tracer .effc (0 of 955): the tracer is a WeaponTuning texture member (G2-10), carried by the weapon clone"),
    "T-FX13": ("out", "no vehicle carries a casing/shell effect; ChainGun_BulletCasing has no JC3 carrier"),
    "T-FX14": ("next", "missile trail = missile_trail_car (2 vehicles, on the donor) at MissileL/R; needs the T-11 missile (D-7)"),
    "T-FX15": ("next", "cannon impact = the 7-variant tank_explosive_* family (19 vehicles) on the hit surface; needs the T-11 cannon"),
    "T-FX16": ("out", "no cannon-round trail effect exists (0 of 955); the round shows as the tracer (T-FX12)"),
    "T-FX17": ("epe", "tyre kick-up = the donor's 6-variant dust_trail_* family (161 vehicles) on the wheel parts (T-EF1)"),
    "T-FX18": ("epe", "slide dust = the donor's 5-variant chassis_slide_* family (289 vehicles) on the body (T-EF1)"),
    "T-FX19": ("epe", "BmAK ships 0 wall-scrape systems (G1-16); the donor already carries spark_trail_02_med at the ScrapeSparks sockets"),
    "T-FX20": ("out", "no brake-trail effect path (0 of 955) and no BrakeLightTrail system in G1-16's 206; T-FX6 keeps the donor's own"),
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
    "T-WP4": ("blocked", "the EMP missile can be a `w618` clone plus G2-16's entity-level `CForcePulse` copy, but JC3 has no disable/duration member for the Immobilizer - blocked on the behaviour, not on the carrier"),
    "T-WP5": ("blocked", "the EMP burst is an entity-level `CForcePulse` copy (G2-16) - the object can be built, but nothing in the decoded files fires it (G2-17: 14 unowned pulses, firing moment UNKNOWN)"),
    "T-WP6": ("out", "named omission: 0 functional winch classes in the fleet - rope/winch geometry on 4 entities but no winch/tow/rope module type and no part that pulls; proof `Research/JC3Grab/TETHER.md`"),
    "T-WP7": ("out", "named omission: no allegiance-switch class in the 103-class fleet census (`allegian`/`hacker`/`hijack` appear nowhere); proof `Research/JC3Grab/ENTITIES.md`"),
    "T-WP8": ("out", "named omission: no sonar class in the 103-class census; `CForcePulse` is the shockwave half only, which is T-WP5; proof `Research/JC3Grab/ENTITIES.md`"),
    "T-WP9": ("out", "named omission: no tracker class in the 103-class census, the only 'track' is `CMusicTrack`; proof `Research/JC3Grab/ENTITIES.md`"),
    "T-WP10": ("out", "named omission under D-3: no non-lethal flag, damage type or weapon mode in the 52-type / 1,421-path vocabulary; proof `Research/JC3Grab/VOCABULARY.md`"),
    "T-WP11": ("keep", "the afterburner is JC3 nitro and is live since test-091 (T-B2/T-B3); the `Batmobile_Booster` gadget mesh is a cockpit part row (B-04)"),
    "T-WP12": ("next", "WPN-12's API facts (2 slots, 14 reticle shapes, cooldown 0..1, no heat param, one lock POI) - the hud.gfx translation is T-19, which lists T-11 as a dep"),
    "T-WP13": ("blocked", "D-7 asks for all 11 weapons in both modes, and the fleet has 2 driver slots at most with no active-slot index, no next/previous weapon action and no weapon group anywhere in the 232 `.epe` graphs (G2-11); no mechanism carries 11"),
    "T-WP14": ("out", "D-3 resolved 2026-10-28 (user): accept JC3 lethality, no toggle - the row is the decision record, and the riot suppressor stays a named omission in T-WP10 because no non-lethal flag/damage type/mode exists (proof `Research/JC3Grab/VOCABULARY.md`, `Research/JC3Grab/G2X.json` WPN-10)"),
    # --- T-20 (2026-10-28): world translation, one row per WLD requirement ---------------
    # `why` is the short form; T15_WORLD.md carries the numbers and t15_world.py --check
    # re-derives the cells, the disposition and the ledger from the five G2 world files.
    "T-WLD1": ("next", "the Rebel Drop item is one record keyed by `hash_jenkins(leaf)` = 443190071; B-13 writes Name/UIName/UIImagePath/UIVideoPath (G2-26)"),
    "T-WLD2": ("next", "the unlock is an `ItemReward` link on the donor's own task 1361701860 (Type 19), not an item field; the shipped mod proves the item.onlinec write path"),
    "T-WLD3": ("next", "all 45 vanilla vehicle drops share Type 1/UIType 3/Rewardable 1, so the donor's profile is the class value; the enums' meanings are UNKNOWN"),
    "T-WLD4": ("blocked", "the name is a `profile/online.stringlookup` pair keyed by the leaf hash and 443190071 resolves in 0 of 11 languages; no `.stringlookup` writer exists in `Tools/scripts`"),
    "T-WLD5": ("next", "the icon is a plain texture named after the leaf and the new leaf has none; copy the donor's 18,688 B file under the new name (G2-32)"),
    "T-WLD6": ("blocked", "UIDescription 2073308658 is the Serpente's own blurb; a `<leaf>_desc` pair is needed and the store has no writer"),
    "T-WLD7": ("keep", "UITypeDescription/UIFlagDescription resolve 11/11 to SPORTS CAR / SPORTS CARS - a category caption, valid for any vehicle in the slot"),
    "T-WLD8": ("epe", "29 entry objects placed on the cockpit sides by T-13 (77/85 in the 0.05-0.30 m band); B-05 moves the graph"),
    "T-WLD9": ("epe", "26 exit objects ride the placed point nodes; state names unchanged so the animation wiring stays valid (G2-18 §4)"),
    "T-WLD10": ("epe", "the `point.stunt*` nodes are placed on the hull top by T-13 (roof y 2.0811, deck y 1.3606)"),
    "T-WLD11": ("blocked", "the 3 stunt areas bind donor `deform_points` indices and float 0.10-0.60 m off the Batmobile shell; the mesh has no deform-point list to rebind and no toolkit pass rewrites it"),
    "T-WLD12": ("next", "mass 975 -> 6000 = 6.154x the donor (T-M1's 6 t class row); the contact hull is T-22's, and the mass unit is UNKNOWN (G2-34)"),
    "T-WLD13": ("keep", "the donor already sinks (`will_sink` 1, buoyancy 2/drag 100/radius 0.55) and test-091's modules are identical, so D-8's lore route ships as it stands"),
    "T-WLD14": ("keep", "the water kill/stall constants are fleet-wide in `vehicle_common` (10/20/20/50 ms, 30 s engine) with 0 overrides; R7 forbids editing the shared file"),
    "T-WLD15": ("out", "no vehicle-side tether/winch member exists (`winch` = [], 335 tether paths are dialogue/UI); the car supplies its mass and nothing else"),
    "T-WLD16": ("keep", "12 CVehicleCargoBay objects already enabled; the 6000 car is 15.0/6.0/40.0 % of the cargo plane, boat and flatbed bodies"),
    "T-WLD17": ("out", "0 of 23 helicopters carries a CVehicleCargoBay, so no helicopter can airlift any car (G2-34)"),
    "T-WLD18": ("keep", "the spawn table keys on the full path string and the new leaf has 0 records there; D-6 standalone means nothing is added"),
    "T-WLD19": ("keep", "the donor's record carries ambient+liberated and matches 1 of 41 selectors, so replacing that leaf would put AI Batmobiles in traffic (G2-29, D-6)"),
    # --- T-15 (2026-10-28): modes translation under D-2's hybrid ---------------------------
    # `why` is the short form; T11_MODES.md carries the numbers and t11_modes.py --check
    # re-derives the cells, the disposition and the ledger from MODES.json / CAMERA.json.
    "T-MD1": ("next", "the afterburner is JC3 nitro (`arcade.nitro_boost`, 145/232) and is live since test-091; a hybrid has no pursuit gate, so the boost is always on tap"),
    "T-MD2": ("next", "the Immobilizer's launcher takes a driver slot and D-7 puts every weapon in both modes; the missing disable member is T-WP4's `blocked` row"),
    "T-MD3": ("keep", "ram immunity is the entity switch `impact_damage_factor` 0 (T-DM8) - mode-independent, one car carries it as-is"),
    "T-MD4": ("keep", "`StandardTorqueVSpeedCurve` has no values in MODES.json (not among the 107 declared fields), so the speed profile rests on T-E1/T-E3 and the curve is UNKNOWN"),
    "T-MD5": ("out", "`BattleModeVSpeedCurve` 0->60, 600->40, 1200->30 needs a mode switch a hybrid does not have; the points are recorded for the two-variant route"),
    "T-MD6": ("out", "`TurningModeMaxSpeed` 600 cm/s = 21.6 km/h is a mode-only cap and no JC3 member carries one"),
    "T-MD7": ("out", "the six battle drive/slip factors are mode deltas on the handling rows; a hybrid has one handling set (T-M1/T-S1/T-E3/T-ST1)"),
    "T-MD8": ("out", "turn-on-the-spot: G2-21 refuted 5 candidates and found 0 tank-only members, so the pivot has no data carrier (named omission)"),
    "T-MD9": ("next", "turret/cannon aim is T-12's part angles and the weapons are T-11's; D-7 removed the per-mode split"),
    "T-MD10": ("keep", "`ArmourModeDamageReduction` is 0 on the three packages that serialise it, so the hybrid's single armour profile is already the BmAK value"),
    "T-MD11": ("keep", "`BattleModeCamFOV` 60 sits inside the delivered `.ctune`'s 55-63 band, so no value changes; only the mode switch is missing (T-CAM10's second tune needs two variants)"),
    "T-MD12": ("next", "the four `VEHLT_BattleModeLight` lamps map onto JC3's `HeadLight` behaviour (T-L17-T-L20) because the fleet's nine light behaviours have no battle value: they light with the headlights"),
    "T-MD13": ("out", "`TransformationAnimNode` is serialised in no package, so only T-12's end pose exists - the animated transformation is a named omission"),
    "T-MD14": ("blocked", "T-16 W-08 is blocked: the donor has no mode-switch event and a hybrid has no second variant to hang the 30 battle events on"),
    "T-MD15": ("next", "D-2 chose one hybrid car: B-12 is `skipped: D-2` and B-13 ships a single drop entry carrying both modes"),
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
