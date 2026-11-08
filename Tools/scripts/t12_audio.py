#!/usr/bin/env python
"""t12_audio.py - T-16: audio translation, one row per JC3 event the Batmobile uses.

Reads the two generated audio evidence files and turns them into a build map:

    BmAK side   Research/BatmobileGrab/AUDIO_FEATURES.json   (G1-15: 361 event rows, 423 measured
                48 kHz WAVs with ITU-R BS.1770-4 loudness, 506 RTPC bindings)
    JC3 side    Research/JC3Grab/JC3_AUDIO_EVENTS.json        (G2-24: the donor's 45 pinned event
                GUIDs, their bank + ordinal, the `.epe` role names, `LandAudio.min_rpm`/`max_rpm`,
                the 649-sample census, the four weapon sources)

For every JC3 event the Batmobile uses it emits one row: BmAK event(s)/WAV(s) -> JC3 event GUID ->
sample slot -> transform (gain to +/-1 LU, PCM16 frame-count stretch, loop window, and the BmAK
RTPC `REV_RPM` curve re-based onto the JC3 RPM window).

What is read, what is derived, what is a selection
--------------------------------------------------
* read      the event GUIDs, banks, ordinals, role names, the **tune GUID** an event owns (`TLNB`
            body 0:16 = tune, 16:32 = owning event; the same tune GUID sits in the owner event's
            body at offset 32), `min_rpm`/`max_rpm`, the sample name table (index, name), the
            sample format/loop points, every BmAK loudness, WEM frame count and RTPC point.
* derived   gain_db = slot_lufs - source_lufs; delivered_lufs = integrated loudness of the payload
            the swap would write (mono downmix, gain, trim/pad with zeros to the slot's frame
            count, PCM16 clip + quantise); delta_lu = delivered - slot (the +/-1 LU gate); stretch
            = slot_frames / payload source frames; the RPM curve points
            rpm = min_rpm + x * (max_rpm - min_rpm).
* selected  which sample slot a replacement goes into, and which source feeds it. The bank stores
            event -> tune; what a tune plays (tune -> sample) is not stored, so the slot is chosen
            **by name** (and audition), exactly as test-060 did. Each row carries `slot.method` and
            `slot.confidence`; the nitro slots and their per-slot sources are the three test-060
            really swapped (`Tools/scripts/_apply_audio.py`, MODLOG §71).

Usage
    python Tools/scripts/t12_audio.py --write     # regenerate the JSON + MD (decodes + measures)
    python Tools/scripts/t12_audio.py --check     # Done-when gate: rebuild, re-measure, compare
    python Tools/scripts/t12_audio.py --check --fast   # reuse the stored measurements
    python Tools/scripts/t12_audio.py dump rows|slots|curves
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmak_audio_features as g15  # noqa: E402  (integrated_lufs / _float_mono, never re-written)
import jc3audio  # noqa: E402
import jc3index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_FEATURES.json")
JC3 = os.path.join(ROOT, "Research", "JC3Grab", "JC3_AUDIO_EVENTS.json")
OUTDIR = os.path.join(ROOT, "Working", "Translation")
JSON_NAME = "t12_audio_map.json"
MD_NAME = "T12_AUDIO.md"
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
CLI = os.path.join(ROOT, "Tools", "vgmstream-win64", "vgmstream-cli.exe")
VEH_BANK = os.path.join(ROOT, "Working", "Audio", "jc3bank", "sound", "fmod_banks", "vehicles.bank")
WPN_BANK = os.path.join("E:/Modding/_gamedata/JC3grab/audio", "weapons.bank")
BANKS = {"vehicles": (VEH_BANK, "sound/fmod_banks/vehicles.bank"),
         "weapons": (WPN_BANK, "sound/fmod_banks/weapons.bank")}
AUDIO_DEV = {"vehicles": 5}

# the card's feature codes (backlog §1.7) - every one needs at least one row
FEATURES = ["AUD-1", "AUD-2", "AUD-3", "AUD-4", "AUD-5", "AUD-6", "AUD-7"]
DISPOS = ["mapped", "kept vanilla", "named omission", "remove", "blocked"]

# ---------------------------------------------------------------------------------------------
# The editorial half: which BmAK sound answers which JC3 event, and which slot(s) to audition.
#   src      = how the BmAK source is named (explicit events, an engine-bed rule, or WAV paths)
#   slots    = candidate JC3 sample names (resolved against the bank's name table, never typed
#              as indices); `chosen` is the one a build may use, None = still UNKNOWN
#   method   = how the slot was picked;  confidence = proven / candidate / none
# ---------------------------------------------------------------------------------------------
E = "Playable_Batmobile_SF"           # the base package every event name below is read from

SPECS = [
    dict(id="A-01", role="engine_running_sound", feature="AUD-1", dispo="blocked",
         match="role-name: `engine_running_sound` is the car's engine bed; BmAK's engine bed is "
               "`Play_Batmobile_Idle` (group `engine`, no RTPC bindings) plus the cool-tick layer "
               "`Play_BML_EngineCoolTicks` (22 WEMs, binds `REV_RPM`). The other engine-group "
               "events that bind `REV_RPM` (Rotation, Reverse, Positional, Clutch, the transitions) "
               "are drive/one-shot layers, not the bed: A-05 covers Rotation and the rest answer no "
               "`.epe` role",
         src={"events": ["Play_Batmobile_Idle", "Play_BML_EngineCoolTicks"]},
         primary="Play_Batmobile_Idle",
         slots=["aston_martin_vantage_engine_rpm_idle_high",
                "aston_martin_vantage_engine_rpm_idle2",
                "aston_martin_vantage_engine_rpm_low2",
                "aston_martin_vantage_engine_rpm_medium_low",
                "aston_martin_vantage_engine_rpm_medium_high2",
                "aston_martin_vantage_engine_rpm_high"],
         chosen=None,
         method="name match; `aston_martin_vantage_engine_rpm_*` is the largest `_engine_rpm_` "
                "stack in vehicles.bank (size derived from the name table, asserted below) and "
                "`Play_Batmobile_Idle` is the engine-group idle event - a structural match, not "
                "proof of which family the donor's tune plays",
         confidence="candidate",
         verify="blocked: Q-1 #8 - the candidate layers are measured but which family the "
                "donor's `engine_running_sound` tune plays is UNKNOWN (the bank stores event->tune, "
                "not tune->sample), so no slot is chosen and B-11 has no gain to apply; the "
                "audition is the unblocker"),
    dict(id="A-02", role="exhaust_upgrade_nitrous", feature="AUD-2", dispo="mapped",
         match="role-name: `exhaust_upgrade_nitrous` is the boost layer; BmAK's afterburner is "
               "`Play_Batmobile_RocketTails`, which carries no media in the four packages "
               "(G1-15 `afterburner`: 2 events / 0 WEMs), so the replacement content is the "
               "turbo/start WEMs test-060 already used",
         src={"events": ["Play_Batmobile_RocketTails", "Stop_Batmobile_RocketTails"],
              "wavs": ["Working/Audio/bml/jc3_batmobile_start.wav",
                       "Working/Audio/hashid/EC2FD42B.wav"]},
         slots=["jc3_veh_land_premium_nitro_start",
                "jc3_veh_land_premium_nitro_loop",
                "jc3_veh_land_premium_nitro_stop"],
         # test-060 did not use one source for all three slots: _apply_audio.py JOBS maps
         # index 56 -> start.wav first 0.7445 s, 150 -> EC2FD42B.wav first 3.2254 s,
         # 355 -> EC2FD42B.wav last 0.756 s.  Each slot's gain is measured on its own span.
         slot_src={"jc3_veh_land_premium_nitro_start":
                   {"wav": "Working/Audio/bml/jc3_batmobile_start.wav", "span_s": 0.7445},
                   "jc3_veh_land_premium_nitro_loop":
                   {"wav": "Working/Audio/hashid/EC2FD42B.wav", "span_s": 3.2254},
                   "jc3_veh_land_premium_nitro_stop":
                   {"wav": "Working/Audio/hashid/EC2FD42B.wav", "span_s": 0.756,
                    "tail": True}},
         chosen="jc3_veh_land_premium_nitro_loop",
         method="proven swap: test-060 replaced FSB5 indices 56/150/355 (0-based) with these "
                "names' payloads and the bank still parsed + decoded (MODLOG §71, "
                "`_apply_audio.py`); the per-slot source and span are that script's JOBS table",
         confidence="proven",
         verify="Q-2 A2: hit nitro. Pass = the afterburner whine plays instead of the stock "
                "nitro for the full boost, all three payloads (start/loop/stop) audible; the "
                "start slot is the one that cannot reach +/-1 LU without clipping (see gain), "
                "so the audition must also say whether that clip is audible"),
    dict(id="A-03", role="exhaust_upgrade_tjump", aliases=["exhaust_upgrade_tjump_trail"],
         feature="AUD-2", dispo="blocked",
         match="role-name: turbo-jump layer (two roles share one GUID)",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="blocked: D-10 - if JC3 turbo jump is disabled the event never fires, so no "
                "replacement is chosen; if it stays, BmAK has no jump sound to put in it"),
    dict(id="A-04", role="GearChange", feature="AUD-1", dispo="blocked",
         match="role-name: shift one-shot <-> `Play_Batmobile_GearShift_Up` (same 5-value "
               "clutch/shift RTPC list as the BmAK clutch events)",
         src={"events": ["Play_Batmobile_GearShift_Up"]},
         slots=["jc3_veh_generic_gear_shift_performance_01",
                "jc3_veh_generic_gear_shift_performance_02",
                "jc3_veh_generic_gear_shift_performance_03"],
         chosen=None,
         method="candidate: the three `jc3_veh_generic_gear_shift_performance_*` samples are one "
                "of the shipped shift families (counted from the name table); what `performance` "
                "denotes is not measured by any field - the audition decides",
         confidence="candidate",
         verify="blocked: Q-2 A9 (0-100 with/without boost) - the BmAK shift WEMs are "
                "multi-channel and sit far below every `performance` shift slot once downmixed to "
                "the mono payload the swap writes, so the gain that reaches the slot clips and "
                "still lands above it (slot table); the probe must say whether that clip is "
                "acceptable or the stock shift stays"),
    dict(id="A-05", role="chassis_spinning_sound", feature="AUD-6", dispo="mapped",
         match="role-name: the body-spin bed <-> `Play_Batmobile_Rotation` (its RTPC list binds "
               "`BML_Steering_Rotation` + `BML_WheelSpeed`, i.e. yaw rate)",
         src={"events": ["Play_Batmobile_Rotation"]},
         slots=["jc3_veh_lave_chassis_spin_creaks_loop_fast"],
         chosen="jc3_veh_lave_chassis_spin_creaks_loop_fast",
         method="name match: the only `chassis_spin` sample in vehicles.bank",
         confidence="candidate",
         verify="Q-2 A10 (skid check): pass = the spin bed ramps with yaw in a handbrake turn "
                "and is silent in a straight line"),
    dict(id="A-06", role="DoorOpeningStart", feature="AUD-5", dispo="mapped",
         match="role-name: the driver door opening <-> `Play_CockpitOpen` (BmAK opens a canopy, "
               "not a door - MOD-4)",
         src={"events": ["Play_CockpitOpen"]},
         slots=["jc3_veh_door_tank_open_03", "jc3_veh_land_door_moderncar_openstart_01",
                "jc3_veh_land_door_90s_car_openstart_01"],
         chosen="jc3_veh_door_tank_open_03",
         method="name match: an armoured hinged shell is the tank door set; the car-door start "
                "samples are the fallback if the tank door reads too heavy",
         confidence="candidate",
         verify="Q-1 #3: walk around, enter from both sides. Pass = the open sound starts with "
                "the canopy motion and finishes before Rico is seated, 3/3"),
    dict(id="A-07", role="DoorClosingEnd", feature="AUD-5", dispo="mapped",
         match="role-name: the door closing end <-> `Play_CockpitClose`",
         src={"events": ["Play_CockpitClose"]},
         slots=["jc3_veh_door_tank_close_01", "jc3_veh_land_door_moderncar_closingend_01",
                "jc3_veh_door_tank_close_03"],
         chosen="jc3_veh_door_tank_close_01",
         method="name match: same family as A-06 so the open/close pair is coherent",
         confidence="candidate",
         verify="Q-1 #3: pass = the close sound ends within 0.3 s of the canopy reaching the "
                "body, no tail after the seat change, 3/3"),
    dict(id="A-08", role="in_water_move_sound", feature="AUD-6", dispo="blocked",
         match="no BmAK water-movement event exists (G1-15 has no water group)",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="blocked: D-8 - the donor keeps its own event; whether the car dies in water "
                "before the sound matters is the open question (Q-3 #4)"),
    dict(id="A-09", role="ground_roughness_sound_attached", feature="AUD-6", dispo="named omission",
         match="AUD-6/T-AU3: `BML_Impacts` is absent from BmAK (G1-15: impacts 16 rows / 5 events "
               "/ 0 WEMs), so JC3's ground-roughness bed stays",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="V-04 file check: event kept, no swap requested"),
    dict(id="A-10", role="sinking_sound", feature="AUD-6", dispo="blocked",
         match="no BmAK sinking event; water behaviour itself is D-8",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="blocked: D-8 (Q-3 #4 drive into a lake)"),
    dict(id="A-11", role="speedwind_sound_player", feature="AUD-3", dispo="named omission",
         match="AUD-3: the donor has no cabin effect at all - G2-24 §9/§8 name "
               "`speedwind_sound_player` as the nearest carrier, and G2X records AUD-3 as a "
               "proven absence of an interior member",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="V-04 file check: BmAK AUX_InBatmobile (9 events / 22 WEMs) cannot be added "
                "through a sample swap because no JC3 interior event exists to put it in"),
    dict(id="A-12", role="jump_air_whoosh_sound", feature="AUD-6", dispo="named omission",
         match="BmAK jump one-shots are `missing-bank` (G1-15 movement: Jump_Land/PreJump/"
               "PreLand/Wind, 0 WEMs), so there is nothing to swap in",
         src={"events": ["Play_Batmobile_Jump_Wind"]}, slots=[], chosen=None,
         method="none", confidence="none",
         verify="V-04 file check: event kept; BmAK media absent (T-AU5 pattern)"),
    dict(id="A-13", role="horn", feature="AUD-7", dispo="remove",
         match="AUD-7: BmAK ships no horn (G1-15 `horn`: 0 rows / 0 events) and the Arkham "
               "Batmobile has none; G2-24 §8 shows the horn is one `SAttachedEffect` per model",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="Q-1 #1: pass = the horn button produces no sound from the Batmobile; the "
                "`horn` object is deleted from the `.epe` in B (B-04), not muted in the bank"),
    dict(id="A-14", role="fire_post_explosion", feature="AUD-6", dispo="named omission",
         match="ARM-6 death look: BmAK `Play_Batmobile_Destroyed` is `missing-bank` (0 WEMs), and "
               "its explosion sweeteners are `missing-bank` too (G1-15 impacts)",
         src={"events": ["Play_Batmobile_HeavyCannon_Explosion",
                         "Play_Tank_Explosion_Barrage_Sweetener"]},
         slots=[], chosen=None, method="none", confidence="none",
         verify="Q-1 #6: pass = the death explosion is JC3's, with no crumple/deform sound "
                "(R1/ARM-6); BmAK media absent"),
    dict(id="A-15", role="explosion", feature="AUD-6", dispo="named omission",
         match="same as A-14: the BmAK explosion/death media are not in the four packages",
         src={"events": ["Play_Batmobile_Destroyed"]},
         slots=[], chosen=None, method="none", confidence="none",
         verify="Q-1 #6: pass = explosion sound unchanged from stock JC3"),
    dict(id="A-16", role="damage_smoke", feature="AUD-6", dispo="kept vanilla",
         match="FX-4/ARM-6: damage shows as scorch + smoke, never deform (R1); BmAK has no "
               "damage-smoke event, only particle systems (G1-16)",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="Q-3 #7: pass = smoke/scorch starts at the predicted health, no metal-bend sound"),
    dict(id="A-17", role="dynamic_break_large", feature="AUD-6", dispo="kept vanilla",
         match="part-break audio: the Batmobile's parts never deform or break off (R1/APP-7), so a "
               "break sound has nothing to fire on; BmAK ships no break event",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="Q-3 #7: pass = no break sound at any damage state (parts change material state, "
                "they do not separate)"),
    dict(id="A-18", role="dynamic_break_taillight",
         aliases=["dynamic_break_turnsignal", "dynamic_break_window_sm", "dynamic_break_window"],
         feature="AUD-6", dispo="kept vanilla",
         match="one GUID carries four tail/turn-signal/window break roles; the Arkham car loses no "
               "panels (R1) and BmAK has no break event",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="Q-3 #7: pass = lights switch off by state, no glass/panel break sound"),
    dict(id="A-19", role="dynamic_break_electric",
         aliases=["dynamic_break_light_off", "dynamic_break_light_on"],
         feature="AUD-6", dispo="kept vanilla",
         match="electric + light-on/off break roles (LGT-1 lamps); the lamp state is modelled, the "
               "break audio is not (R1)",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="Q-3 #7 / Q-1 #7: pass = a shot-out lamp goes dark silently"),
    dict(id="A-20", role="dynamic_break_small", feature="AUD-6", dispo="kept vanilla",
         match="small part-break role; same reason as A-17",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="V-04 file check: event kept; never fires (R1)"),
    dict(id="A-21", role="dynamic_break_medium", feature="AUD-6", dispo="kept vanilla",
         match="medium part-break role; same reason as A-17",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="V-04 file check: event kept; never fires (R1)"),
    dict(id="A-22", role="TireDestroyed", feature="AUD-6", dispo="kept vanilla",
         match="ARM-4: the wheels cannot be shot off or burst (BmAK has no wheel damage), so the "
               "tyre-destroyed event is unreachable; BmAK ships no tyre-damage event either",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="Q-1 #6: pass = pistol/rifle/MG fire on a wheel produces no burst sound and no "
                "wheel damage state"),
    dict(id="A-23", role="water_explosion", feature="AUD-6", dispo="blocked",
         match="water-impact explosion role; BmAK has no water group and water behaviour is D-8",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="blocked: D-8 (Q-3 #4 drive into a lake)"),
]

# 45 donor GUIDs, of which 23 are named by the `.epe`. Roles the table above does not cover fall
# through to `kept vanilla (no BmAK counterpart)` - the decision is recorded, not assumed.
WEAPON_ROWS = [
    dict(id="W-01", feature="AUD-5", weapon="w602", dispo="named omission",
         jc3="medium tank `Fire` + `ReloadStart`",
         match="WPN-1's carrier `w602_mediumtank_cannon` has no `.ee` and no `.fmod_guids`, and "
               "the firing vehicle's own events carry the sound (G2-24 §7); BmAK's cannon shot "
               "is not in the four packages (only `Play_Batmobile_HeavyCannon_Explosion`, "
               "missing-bank)",
         src={"events": ["Play_Batmobile_HeavyCannon_Explosion"]},
         slots=["jc3_wpn_mntd_tank_cannon_medium_01", "jc3_wpn_mntd_tank_cannon_medium_02",
                "jc3_wpn_tank_cannon_loaded_01", "jc3_wpn_tank_cannon_loaded_02"],
         chosen=None, method="name match (kept as the stock cannon; no BmAK source to swap in)",
         confidence="none",
         verify="Q-1 #5 / Q-3 #3: pass = the cannon fires from the muzzle with the tank's own "
                "cannon sample; shots-to-kill recorded, sound unchanged"),
    dict(id="W-02", feature="AUD-5", weapon="w603", dispo="named omission",
         jc3="w603 `.wtunec` only (no `.ee`, no `.fmod_guids`)",
         match="no audio member on either side: 171 tune members, 0 audio (G2-24 §7); BmAK's "
               "machine-gun fire is `Play_Batmobile_MShot` - the carriers differ, so WPN-2 must "
               "use W-03's `w619` route",
         src={}, slots=[], chosen=None, method="none", confidence="none",
         verify="V-04 file check: `w603` is not the audio carrier for WPN-2"),
    dict(id="W-03", feature="AUD-5", weapon="w619", dispo="mapped",
         jc3="w619 `.epe` `fire_sound_combi`",
         match="WPN-2 (Vulcan) candidate with a pinned fire event; BmAK `Play_Batmobile_MShot` "
               "(weapons group, 5 WEMs) is the chain-gun one-shot",
         src={"events": ["Play_Batmobile_MShot"]},
         slots=["jc3_wpn_minigun_fire_close_loop_04", "jc3_wpn_minigun_barrel_motor_loop",
                "jc3_wpn_minigun_endclick"],
         chosen="jc3_wpn_minigun_fire_close_loop_04",
         method="name match: `minigun_fire_close_loop` is the vehicle/player minigun fire loop; "
                "`barrel_motor_loop` + `endclick` are the spin-up/stop pair in the same family",
         confidence="candidate",
         verify="Q-1 #5 / Q-3 #3: pass = firing plays loop + end click, no gap between rounds, "
                "barrels spin in sync (ANI-3) 3/3 bursts"),
    dict(id="W-04", feature="AUD-5", weapon="w618", dispo="named omission",
         jc3="w618 `.epe` `fire`/`fire2..4`",
         match="WPN-3's carrier has its own event, but BmAK ships no missile-launch audio in the "
               "four packages (G1-15 weapons: 3 events, none missile; only "
               "`Play_HUD_Missile_Lock` for the reticle)",
         src={}, slots=["jc3_wpn_missile_fire_01", "jc3_wpn_missile_fire_02",
                        "jc3_wpn_missile_fire_03", "jc3_wpn_missile_fire_04",
                        "jc3_wpn_missile_trail_rear_loop"],
         chosen=None, method="name match (stock missile samples kept; no BmAK source)",
         confidence="none",
         verify="Q-1 #5: pass = four missiles fire with the stock missile launch sample and the "
                "trail loop, lock beep unchanged"),
    dict(id="W-05", feature="AUD-5", weapon="w602", dispo="named omission",
         jc3="medium tank `Fire` (vehicle-side event)",
         match="the vehicle event that actually carries the cannon shot; stock sample kept",
         src={}, slots=["jc3_wpn_tank_cannon_loaded_02"], chosen=None,
         method="name match (stock)", confidence="none",
         verify="Q-1 #5: pass = one shot = one loaded/cannon sample, reload sound once per cycle"),
    dict(id="W-06", feature="AUD-5", weapon="w602", dispo="named omission",
         jc3="medium tank `ReloadStart`",
         match="BmAK's reload audio is not in the four packages", src={},
         slots=["jc3_wpn_tank_cannon_loaded_unload_01", "jc3_wpn_tank_cannon_loaded_unload_02"],
         chosen=None, method="name match (stock)", confidence="none",
         verify="Q-1 #5: pass = the unload/load pair plays once per reload, no overlap"),
    dict(id="W-07", feature="AUD-5", weapon="lock-on UI",
         dispo="named omission",
         jc3="`Play_HUD_Missile_Lock` / `Play_Tank_Heavy_LockBeep` / `Locked` (HUD-2, WPN-12)",
         match="BmAK's lock-on UI group is 6 events / 23 rows and **every one is "
               "`missing-bank`** (0 WEMs), so there is nothing to audition",
         src={"events": ["Play_HUD_Missile_Lock", "Play_Tank_Heavy_LockBeep",
                         "Play_Tank_Heavy_Locked"]},
         slots=["jc3_w143_fire_leach_target_lock"], chosen=None,
         method="name match (stock JC3 lock tones kept)", confidence="none",
         verify="Q-1 #5: pass = lock beep + locked tone as stock, one per target"),
    dict(id="W-08", feature="AUD-4", dispo="blocked", weapon="battle mode",
         jc3="no event on the donor (battle mode would be a second variant, D-2)",
         match="AUD-4: BmAK `battle-mode` is 30 events / 75 WEMs (`Play_BattleMode_In/Out*`, "
               "`Play_BattlemodeEngine`), but a JC3 event to put them in exists only if a second "
               "variant ships",
         src={"group": "battle-mode"}, slots=[], chosen=None, method="none", confidence="none",
         verify="blocked: D-2 - two variants would give the battle car its own "
                "`engine_running_sound`; one hybrid car has no mode-switch event to hook"),
]


# ---------------------------------------------------------------------------------------------
def load():
    g = json.load(open(BMAK, encoding="utf-8"))
    j = json.load(open(JC3, encoding="utf-8"))
    return g, j


def ev_index(g: dict) -> dict:
    """event name -> the base-package row (dedupe the 3-4 packages that define each event)."""
    out = {}
    for e in g["events"]:
        cur = out.get(e["name"])
        if cur is None or (cur["package"] != E and e["package"] == E):
            out[e["name"]] = e
    return out


def media_index(g: dict) -> dict:
    return {m["wem_hex"]: m for m in g["media"]}


def bank_names(bank: str) -> list[str]:
    """The FSB5 name table of a bank, read through the G2-24 reader (no parallel parser)."""
    path, apath = BANKS[bank]
    if not os.path.exists(path):
        if bank != "weapons":
            raise SystemExit(f"bank missing: {path}")
        rows = jc3index.load_index(os.path.join(ROOT, "Research", "JC3Grab"))
        d = jc3audio.read_entry(apath, rows)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(d)
        print(f"  extracted {apath} -> {path} ({len(d):,} B)", file=sys.stderr)
    d = open(path, "rb").read()
    f = jc3audio.fev(d)
    return jc3audio.fsb(d, f["fsb_off"], True)["names"]


def vgm_measure(bank: str, index1: int) -> dict:
    """One sample through the project's vgmstream, measured with the G1-15 loudness function."""
    from scipy.io import wavfile
    path, _ = BANKS[bank]
    tmp = tempfile.mkdtemp(prefix="t12_")
    out = os.path.join(tmp, "s.wav")
    r = subprocess.run([CLI, "-s", str(index1), "-o", out, path], capture_output=True, text=True,
                       errors="replace")
    text = r.stdout + r.stderr
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"vgmstream failed on {bank}#{index1}: {text[-300:]}")
    got = {"index_1based": index1, "loop_start": None, "loop_end": None}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("sample rate:"):
            got["rate"] = int(line.split(":")[1].split("Hz")[0].strip())
        elif line.startswith("channels:"):
            got["channels"] = int(line.split(":")[1].strip())
        elif line.startswith("stream total samples:"):
            got["frames"] = int(line.split(":")[1].split("(")[0].strip())
        elif line.startswith("encoding:"):
            got["encoding"] = line.split(":", 1)[1].strip()
        elif line.startswith("loop start:"):
            got["loop_start"] = int(line.split(":")[1].split("(")[0].strip().split()[0])
        elif line.startswith("loop end:"):
            got["loop_end"] = int(line.split(":")[1].split("(")[0].strip().split()[0])
    sr, data = wavfile.read(out)
    a = g15._float_mono(data)
    got["lufs"] = g15.integrated_lufs(a, int(sr))
    got["peak_dbfs"] = round(20 * __import__("math").log10(max(float(abs(a).max()), 1e-9)), 2)
    got["duration_s"] = round(a.shape[0] / float(sr), 3)
    for p in os.listdir(tmp):
        os.remove(os.path.join(tmp, p))
    os.rmdir(tmp)
    return got


def media_frames(m: dict) -> int | None:
    """The WEM's own sample count (G1-15 keeps vgmstream's line verbatim)."""
    line = (m.get("vgmstream") or {}).get("stream_total_samples") or ""
    head = line.split("(")[0].strip()
    return int(head) if head.isdigit() else None


def mono_48k(path: str, span_s: float | None = None, tail: bool = False) -> tuple[int, np.ndarray]:
    """The payload's source, read the way `_apply_audio.py` reads it: 48 kHz, mono downmix."""
    from scipy.io import wavfile
    sr, data = wavfile.read(os.path.join(ROOT, path) if not os.path.isabs(path) else path)
    a = g15._float_mono(data)
    a = a.mean(axis=1) if a.shape[1] > 1 else a[:, 0]
    if span_s:
        n = int(round(float(span_s) * sr))
        a = a[-n:] if tail else a[:n]
    return int(sr), a


def measure_source(path: str, span_s: float | None = None,
                   tail: bool = False) -> dict:
    """Loudness and length of the exact span that feeds a slot (mono, as written)."""
    sr, a = mono_48k(path, span_s, tail)
    if sr != 48000:
        raise SystemExit(f"{path}: {sr} Hz source - the swap assumes 48 kHz")
    peak = 20 * __import__("math").log10(max(float(np.abs(a).max()), 1e-9))
    return {"rate": sr, "frames": int(a.shape[0]),
            "lufs": g15.integrated_lufs(a[:, None], sr), "peak_dbfs": round(peak, 2)}


def build_payload(path: str, gain_db: float, frames: int,
                  span_s: float | None = None, tail: bool = False) -> dict:
    """What B-11 writes into the slot, then measured: mono downmix, gain, trim/pad with zeros,
    PCM16 clip + quantise.  `delivered_lufs` is measured on that payload, not on its inputs."""
    sr, a = mono_48k(path, span_s, tail)
    x = a * (10 ** (gain_db / 20.0))
    trimmed = max(0, len(x) - frames)
    padded = max(0, frames - len(x))
    x = x[:frames] if trimmed else np.concatenate([x, np.zeros(padded)])
    clip = float((np.abs(x) > 1.0).mean())
    q = np.round(np.clip(x, -1.0, 1.0) * 32767.0) / 32768.0
    return {"delivered_lufs": g15.integrated_lufs(q[:, None], sr),
            "clip_pct": round(100.0 * clip, 2),
            "padded_frames": padded, "trimmed_frames": trimmed,
            "src_frames": int(a.shape[0])}


def src_events(spec: dict, g: dict, idx: dict, m: dict) -> list[dict]:
    """Resolve a spec's `src` to BmAK event rows + their media."""
    src = spec.get("src") or {}
    out = []
    if "group" in src:
        for name, e in idx.items():
            if e["group"] != src["group"]:
                continue
            if "rtpc" in src and not any(r.get("param") == src["rtpc"] for r in e["rtpc"]):
                continue
            out.append(e)
    for name in src.get("events", []):
        e = idx.get(name)
        if e is not None and e not in out:
            out.append(e)
    rows = []
    for e in sorted(out, key=lambda x: x["name"]):
        med = [m[w] for w in e["wems"] if w in m]
        baked = max(med, key=lambda x: x["lufs"]) if med else None
        rows.append({
            "event": e["name"], "group": e["group"], "status": e["status"],
            "event_id": e["event_id_hex"], "wems": len(e["wems"]),
            "media_measured": len(med),
            "lufs_range": [min((x["lufs"] for x in med), default=None),
                           max((x["lufs"] for x in med), default=None)] if med else None,
            "wems_lufs": sorted(({"wem": x["wem_hex"], "lufs": x["lufs"], "wav": x["wav"],
                                  "channels": x["channels"]} for x in med),
                                key=lambda x: x["lufs"]),
            "source": baked and {"wem": baked["wem_hex"], "lufs": baked["lufs"],
                                 "duration_s": baked["duration_s"], "wav": baked["wav"],
                                 "channels": baked["channels"],
                                 "frames": media_frames(baked), "rate": baked["sample_rate"],
                                 "peak_dbfs": baked["peak_dbfs"]},
            "rtpc_rev_rpm": next((r["points"] for r in e["rtpc"]
                                  if r.get("param") == "REV_RPM"), None),
            "loop_evidence": e["loop"],
        })
    for wav in src.get("wavs", []):
        p = os.path.join(ROOT, wav)
        if not os.path.exists(p):
            rows.append({"event": None, "wav": wav, "source": None, "status": "missing-wav"})
            continue
        from scipy.io import wavfile
        sr, data = wavfile.read(p)
        a = g15._float_mono(data)
        rows.append({"event": None, "wav": wav, "status": "wav",
                     "source": {"wav": wav, "lufs": g15.integrated_lufs(a, int(sr)),
                                "duration_s": round(a.shape[0] / float(sr), 3),
                                "channels": int(a.shape[1]), "frames": int(a.shape[0]),
                                "rate": int(sr), "wem": None}})
    return rows


def rpm_curve(points: list | None, lo: float, hi: float) -> list | None:
    """Re-base a BmAK `REV_RPM` curve (x is normalised 0..1) onto the JC3 rpm window.

    The y values are kept verbatim: which FMOD target (volume / pitch / low-pass) each Wwise
    curve drives is not in the recovered data, so the fit can only move the domain.
    """
    if not points:
        return None
    return [{"rpm": int(round(lo + x * (hi - lo))), "y": y, "curve_type": ct}
            for x, y, ct in points]


def bank_tunes(bank: str = "vehicles") -> dict:
    """Read the event -> tune edge out of the bank, through the G2-24 reader (no second parser).

    `TLNS` -> `LIST TMLN` -> `TLNB`: body 0:16 is the tune GUID, body 16:32 the GUID of the event
    that owns it.  Both directions are counted so the doc can cite a measurement, and the whole
    `TLNS` section is searched for sample GUIDs to keep the `tune -> sample` negative honest.
    """
    path, _ = BANKS[bank]
    d = open(path, "rb").read()
    f = jc3audio.fev(d)
    evs = jc3audio.fev_events(d, f)
    bodies = jc3audio.fev_event_bodies(d, f)
    tunes = jc3audio.fev_tunes(d, f)
    waves = {w["guid"] for w in jc3audio.fev_waves(d, f)}
    body_by = {e["guid"]: b for e, b in zip(evs, bodies)}
    off, size = f["sections"]["TLNS"]
    seg = d[off:off + 8 + size]
    tune_guids = {t["tune_guid"] for t in tunes}
    return {
        "by_event": {t["event_guid"]: t for t in tunes},
        "events": len(evs), "tunes": len(tunes), "waves": len(waves),
        "owner_guid_is_event": sum(1 for t in tunes if t["event_guid"] in body_by),
        "owner_body_holds_tune": sum(
            1 for t in tunes
            if len(body_by.get(t["event_guid"], b"")) >= 48
            and body_by[t["event_guid"]][32:48].hex() == t["tune_guid"]),
        "tune_guids_unique": len(tune_guids),
        "wave_guids_in_tune_list": sum(1 for g in waves if bytes.fromhex(g) in seg),
    }


def build(measure: bool = True, prev: dict | None = None) -> dict:
    g, j = load()
    idx = ev_index(g)
    med = media_index(g)
    la = j["land_audio"]["members"]
    lo, hi = float(la["min_rpm"]), float(la["max_rpm"])
    names = {"vehicles": bank_names("vehicles"), "weapons": bank_names("weapons")}
    at = {"vehicles": {n: i + 1 for i, n in enumerate(names["vehicles"])},
          "weapons": {n: i + 1 for i, n in enumerate(names["weapons"])}}
    stored = (prev or {}).get("measurements", {})

    def slot_row(bank: str, name: str) -> dict:
        k = f"{bank}:{name}"
        if k in stored and not measure:
            got = dict(stored[k])
        else:
            got = vgm_measure(bank, at[bank][name])
        row = {"bank": bank, "index_1based": at[bank][name],
               "index_0based": at[bank][name] - 1, "name": name}
        row.update(got)
        return row

    specs = {s["id"]: s for s in SPECS + WEAPON_ROWS}
    by_role = {}
    for s in SPECS:
        for role in [s.get("role")] + list(s.get("aliases") or []):
            if role:
                by_role[role] = s
    donor = []
    un = 0
    for e in j["donor"]["events"]:
        roles = [r["name"] for r in e["roles"]]
        role = roles[0] if roles else None
        spec = next((by_role[r] for r in roles if r in by_role), None)
        bank = e["banks"][0] if e["banks"] else {}
        if spec is None:
            un += 1
        donor.append({"id": spec["id"] if spec else "D-%02d" % un, "guid": e["guid"],
                      "role": role, "roles": roles,
                      "bank": bank.get("bank"), "ordinal": bank.get("ordinal"),
                      "spec": spec["id"] if spec else None})

    src_cache: dict = {}

    def source_stats(path: str, span_s=None, tail: bool = False) -> dict:
        key = (path, span_s, tail)
        if key not in src_cache:
            src_cache[key] = measure_source(path, span_s, tail)
        return src_cache[key]

    def target_of(spec: dict, sources: list[dict], slot: str | None = None):
        """The source that feeds one slot: an explicit `slot_src` span, else the row's `primary`
        event, else the first measured source.  Returns None when the row has no media."""
        ss = (spec.get("slot_src") or {}).get(slot) if slot else None
        if ss:
            return {"path": ss["wav"], "span_s": ss.get("span_s"), "tail": bool(ss.get("tail")),
                    "label": os.path.basename(ss["wav"]), "rule": "slot_src",
                    "stats": source_stats(ss["wav"], ss.get("span_s"), ss.get("tail"))}
        cand = [s for s in sources if s.get("source")]
        pr = spec.get("primary")
        if pr:
            cand = [s for s in cand if s.get("event") == pr] or cand
        if not cand:
            return None
        s = cand[0]
        # "loudest variant" means loudest **as the payload reads it** (mono downmix): a 6-channel
        # WEM can lead on the shipped multi-channel LUFS and still be the quietest mono payload.
        vars_ = [(source_stats(v["wav"]), v["wav"]) for v in s.get("wems_lufs") or []]
        if vars_:
            best = max(vars_, key=lambda t: (t[0]["lufs"] if t[0]["lufs"] is not None else -999))
        else:
            best = (source_stats(s["source"]["wav"]), s["source"]["wav"])
        return {"path": best[1], "span_s": None, "tail": False,
                "label": s.get("event") or os.path.basename(best[1]), "rule":
                "primary" if (pr and s.get("event") == pr) else "first",
                "stats": best[0]}

    tune_info = bank_tunes("vehicles")

    def finish(rows: list[dict], kind: str) -> list[dict]:
        out = []
        for r in rows:
            spec = specs.get(r["spec"]) if r.get("spec") else None
            tune = None
            if r.get("guid") and r.get("bank") == "vehicles":
                tt = tune_info["by_event"].get(r["guid"].replace("-", ""))
                if tt:
                    tune = {"tune_guid": tt["tune_guid"], "index": tt["index"],
                            "owner_matches_row": tt["event_guid"] == r["guid"].replace("-", "")}
            if spec is None:
                # no `.epe` role and no BmAK behaviour -> no semantic bridge.  Keeping it as
                # shipped is the default, not a decision, so R4 makes the row `blocked`.
                out.append({**r, "kind": kind, "feature": "UNASSIGNED", "dispo": "blocked",
                            "match": "pinned by the entity but no `.epe` object names this GUID "
                                     "and no BmAK behaviour maps to it (G2-24 §3)",
                            "sources": [], "slots": [], "chosen": None, "tune": tune,
                            "slot_method": "none", "slot_confidence": "none",
                            "verify": "blocked: Q-1 - keeping it exactly as shipped is the "
                                      "default, not a decision; an audition has to say whether "
                                      "this shared bank event is audible on the car before the "
                                      "row can be called kept vanilla",
                            "note": None})
                continue
            sources = src_events(spec, g, idx, med)
            slots = []
            for nm in spec.get("slots", []):
                b = "weapons" if nm.startswith(("jc3_wpn", "jc3_w143", "jc3_50", "jc3_w502")) \
                    else "vehicles"
                if nm not in at[b]:
                    slots.append({"name": nm, "bank": b, "missing": True})
                    continue
                s = slot_row(b, nm)
                t = target_of(spec, sources, nm)
                if t:
                    src = t["stats"]
                    gain = round(s["lufs"] - src["lufs"], 2)
                    pay = build_payload(t["path"], gain, s["frames"],
                                        t["span_s"], t["tail"])
                    s["gain_db"] = gain
                    s["src_lufs"] = src["lufs"]
                    s["delivered_lufs"] = pay["delivered_lufs"]
                    s["delta_lu"] = (round(pay["delivered_lufs"] - s["lufs"], 2)
                                     if pay["delivered_lufs"] is not None else None)
                    s["clip_pct"] = pay["clip_pct"]
                    s["source_frames"] = pay["src_frames"]
                    s["padded_frames"] = pay["padded_frames"]
                    s["trimmed_frames"] = pay["trimmed_frames"]
                    s["stretch_ratio"] = round(s["frames"] / max(pay["src_frames"], 1), 4)
                    s["source"] = t["label"]
                    s["source_span_s"] = t["span_s"]
                    s["source_rule"] = t["rule"]
                s["chosen"] = nm == spec.get("chosen")
                slots.append(s)
            out.append({
                **r, "kind": kind, "feature": spec["feature"], "dispo": spec["dispo"],
                "match": spec["match"], "sources": sources, "tune": tune,
                "carrier": spec.get("jc3"),
                "slots": slots, "chosen": spec.get("chosen"),
                "slot_method": spec["method"], "slot_confidence": spec["confidence"],
                "verify": spec["verify"], "note": spec.get("note"),
                "curve_rpm": rpm_curve(next((s["rtpc_rev_rpm"] for s in sources
                                             if s.get("rtpc_rev_rpm")), None), lo, hi),
            })
        return out

    rows = finish(donor, "donor")

    # weapon / battle-mode rows: their JC3 identity is a role name, not a donor GUID
    wrows = []
    for spec in WEAPON_ROWS:
        row = {"id": spec["id"], "guid": None, "role": spec.get("weapon") or spec["jc3"],
               "roles": [spec.get("weapon") or spec["jc3"]],
               "bank": None, "ordinal": None, "spec": spec["id"]}
        wrows.append(row)
    rows += finish(wrows, "weapon")

    raw = [s for r in rows for s in r["slots"] if not s.get("missing")]
    seen, slots = set(), []
    for x in sorted(raw, key=lambda s: (s["bank"], s["index_1based"])):
        k = (x["bank"], x["name"])
        if k not in seen:
            seen.add(k)
            slots.append(x)
    derived = ("bank", "name", "chosen", "gain_db", "src_lufs", "delivered_lufs", "delta_lu",
               "clip_pct", "source_frames", "stretch_ratio", "padded_frames", "trimmed_frames",
               "source", "source_span_s", "source_rule")
    measurements = {f"{s['bank']}:{s['name']}": {k: v for k, v in s.items() if k not in derived}
                    for s in slots}
    doc = {
        "schema": 1,
        "card": "T-16",
        "generated_by": "Tools/scripts/t12_audio.py",
        "inputs": {"bmak": "Research/BatmobileGrab/AUDIO_FEATURES.json (G1-15)",
                   "jc3": "Research/JC3Grab/JC3_AUDIO_EVENTS.json (G2-24)",
                   "banks": {"vehicles": VEH_BANK, "weapons": WPN_BANK},
                   "loudness": "ITU-R BS.1770-4 via bmak_audio_features.integrated_lufs",
                   "decode": CLI},
        "method": {
            "slot": "the bank stores event -> tune (`TLNS` -> `LIST TMLN` -> `TLNB`: body 0:16 is "
                    "the tune GUID, 16:32 the GUID of the event that owns it) but stores no "
                    "tune -> sample field, so the slot is chosen by sample name and audition; "
                    "`slot_confidence` says whether test-060 already proved that index "
                    "(`proven`) or it is a name match (`candidate`)",
            "gain": "gain_db = slot LUFS - the LUFS of the span that feeds it (mono downmix, as the "
                    "swap writes it); delivered_lufs is measured on the payload the swap would "
                    "write (gain, trim/pad with zeros to the slot's frame count, PCM16 clip + "
                    "quantise); delta_lu = delivered - slot is the +/-1 LU gate, clip_pct the share "
                    "of samples the gain pushed into the clip",
            "stretch": "the swap must keep the slot's byte size (route a), so the source is "
                       "trimmed/padded to `frames`; stretch_ratio = frames / payload source frames",
            "loop": "no measured slot carries an FSB5 loop field (`loop_start` is null on every "
                    "one); whether the loop is then produced by the event/tune graph, or this bank "
                    "version simply carries no loop metadata, was not measured - UNKNOWN",
            "curve": "BmAK `REV_RPM` x is normalised 0..1; JC3 drives rpm 1000..10000 "
                     "(`LandAudio.min_rpm`/`max_rpm`), so rpm = min + x*(max-min). The y target "
                     "(volume/pitch/low-pass) is not in the recovered data - UNKNOWN",
        },
        "tunes": {k: v for k, v in tune_info.items() if k != "by_event"},
        "jc3": {"land_audio": la, "donor_events": len(donor), "named": j["donor"]["named"],
                "banks": j["banks"], "samples": j["samples"]["summary"]},
        "bmak": {"rows": g["summary"]["rows"], "media": g["summary"]["media"],
                 "decoded": g["summary"]["decoded"], "groups": g["summary"]["groups_used"]},
        "rows": rows,
        "slots": slots,
        "measurements": measurements,
    }
    nm = names["vehicles"]
    stacks: dict = {}
    for n in nm:
        mt = re.match(r"(.+)_engine_rpm_(.+)$", n)
        if mt:
            stacks.setdefault(mt.group(1), []).append(n)
    doc["engine_census"] = {"names": len(nm),
                            "engine_named": sum(1 for n in nm if "engine" in n),
                            "rpm_stacks": {k: sorted(v) for k, v in sorted(stacks.items())}}
    doc["summary"] = summarise(doc)
    return doc


def summarise(d: dict) -> dict:
    rows = d["rows"]
    by_dispo = {}
    for r in rows:
        by_dispo[r["dispo"]] = by_dispo.get(r["dispo"], 0) + 1
    by_feature = {}
    for r in rows:
        if r["feature"] not in FEATURES:
            continue
        b = by_feature.setdefault(r["feature"], {"rows": 0, "mapped": 0, "other": 0})
        b["rows"] += 1
        b["mapped" if r["dispo"] == "mapped" else "other"] += 1
    slots = d["slots"]
    deltas = [s["delta_lu"] for s in slots if s.get("delta_lu") is not None]
    over = [f"{s['bank']}#{s['index_1based']} `{s['name']}` {s['delta_lu']:+.2f}"
            for s in slots if s.get("delta_lu") is not None and abs(s["delta_lu"]) > 1.0]
    chosen_over = [f"{r['id']} `{s['name']}` {s['delta_lu']:+.2f}"
                   for r in rows for s in r["slots"]
                   if s.get("chosen") and s.get("delta_lu") is not None
                   and abs(s["delta_lu"]) > 1.0]
    return {
        "unassigned_rows": sum(1 for r in rows if r["feature"] == "UNASSIGNED"),
        "slots_stock": sum(1 for s in slots if "gain_db" not in s),
        "rows": len(rows), "donor_rows": sum(1 for r in rows if r["kind"] == "donor"),
        "weapon_rows": sum(1 for r in rows if r["kind"] == "weapon"),
        "mapped_rows": sum(1 for r in rows if r["dispo"] == "mapped"),
        "chosen_slots": sum(1 for r in rows for s in r["slots"] if s.get("chosen")),
        "by_disposition": dict(sorted(by_dispo.items())),
        "features": dict(sorted(by_feature.items())),
        "slot_candidates": len(slots),
        "slots_missing_from_bank": sum(1 for r in rows for s in r["slots"] if s.get("missing")),
        "slots_with_gain": len(deltas),
        "max_abs_delta_lu": max((abs(x) for x in deltas), default=None),
        "slots_over_1lu": over,
        "chosen_over_1lu": chosen_over,
        "looped_slots": sum(1 for s in slots if s.get("loop_start") is not None),
        "rpm_curve_rows": sum(1 for r in rows if r.get("curve_rpm")),
        "tunes_resolved": sum(1 for r in rows if r.get("tune")),
        "tunes_unknown": sum(1 for r in rows if r["kind"] == "donor" and not r.get("tune")),
        "engine": d.get("engine_census", {}),
        "banks": d.get("tunes", {}),
    }


# ---------------------------------------------------------------------------------------------
def fnum(v, n=2):
    if v is None:
        return "UNKNOWN"
    if isinstance(v, float):
        if abs(v) < 0.5 * 10 ** -n:
            v = 0.0          # no "-0.00" in a generated table
        return f"{v:.{n}f}"
    return str(v)


def cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def render_md(d: dict) -> str:
    s = d["summary"]
    L = ["# T-12 audio — the Batmobile's sound map (T-16)", "",
         "Generated by `Tools/scripts/t12_audio.py` from `Research/BatmobileGrab/AUDIO_FEATURES.json`",
         "(G1-15, BmAK) and `Research/JC3Grab/JC3_AUDIO_EVENTS.json` (G2-24, JC3). One row per JC3",
         "event the Batmobile uses: BmAK event(s)/WAV(s) → JC3 event GUID → sample slot →",
         "transform. `--check` rebuilds this file, re-decodes every chosen sample and compares.", "",
         "## Summary", "",
         "| fact | value |", "|---|---|",
         f"| rows | **{s['rows']}** ({s['donor_rows']} donor events + {s['weapon_rows']} weapon/mode rows) |",
         f"| dispositions | " + ", ".join(f"`{k}` {v}" for k, v in s["by_disposition"].items()) + " |",
         f"| slot candidates measured | **{s['slot_candidates']}** ({s['looped_slots']} with an FSB5 loop field) |",
         f"| slots with a measured gain match | {s['slots_with_gain']} ({s['slots_stock']} kept stock, no BmAK source), "
         f"max |delivered − slot| **{fnum(s['max_abs_delta_lu'])} LU** |",
         f"| slots outside the ±1 LU gate | {len(s['slots_over_1lu'])}" +
         (" (" + "; ".join(s['slots_over_1lu']) + ")" if s["slots_over_1lu"] else "") + " |",
         f"| chosen slots outside the gate | {len(s['chosen_over_1lu'])}" +
         (" (" + "; ".join(s['chosen_over_1lu']) + ")" if s["chosen_over_1lu"] else "") + " |",
         f"| rows whose event→tune edge resolved | {s['tunes_resolved']} (of {s['donor_rows']} donor rows; "
         f"{s['tunes_unknown']} UNKNOWN - banks this card does not decode) |",
         f"| pinned donor GUIDs no `.epe` object names | {s['unassigned_rows']} (`blocked`, no feature) |",
         f"| names not found in the bank | {s['slots_missing_from_bank']} |",
         f"| rows with an RPM curve fit | {s['rpm_curve_rows']} |",
         f"| JC3 rpm window (`LandAudio`) | {d['jc3']['land_audio'].get('min_rpm')} … {d['jc3']['land_audio'].get('max_rpm')} |",
         "", "## What is read, derived and selected", "",
         "| class | what |", "|---|---|",
         "| `read` | event GUID, bank, ordinal, `.epe` role, `min_rpm`/`max_rpm`, sample name and index, "
         "sample rate/channels/frames/loop, every BmAK LUFS and RTPC point |",
         "| `derived` | `gain_db`, `delivered_lufs`, `delta_lu`, `clip_pct`, `source_frames`, "
         "`stretch_ratio`, the rpm curve domain |",
         "| *selected* | which slot a replacement goes into and which source feeds it — the bank "
         "stores event→tune but no tune→sample, so the slot is chosen by name and audition; "
         "`proven` only where test-060 swapped that index |",
         "", "## Feature coverage", "",
         "| feature | rows | mapped | other (kept vanilla / omission / blocked) |", "|---|---|---|---|"]
    for f in FEATURES:
        b = s["features"].get(f, {"rows": 0, "mapped": 0, "other": 0})
        L.append(f"| {f} | {b['rows']} | {b['mapped']} | {b['other']} |")
    L += ["", f"`UNASSIGNED` = a donor GUID the `.epe` does not name: {s['unassigned_rows']} rows, all",
          "`blocked` - keeping them exactly as shipped is the default, not a decision (R4).", "",
          "## The rows", "",
          "| id | feature | JC3 event (GUID · bank/ordinal · role) | BmAK source | dispo | slot |"
          " gain | verify |", "|---|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        ev = "—"
        if r["guid"]:
            ev = f"`{r['guid'][:8]}` · {r['bank']}/{r['ordinal']} · `{r['role'] or 'unnamed'}`"
        else:
            ev = f"`{r['role']}`"
        src = ", ".join(
            (f"`{x['event']}`" if x.get("event") else os.path.basename(x["wav"]))
            + (f" ({x['wems']} WEMs)" if x.get("wems") else "")
            + ("" if x.get("source") else " *(no media)*")
            for x in r["sources"]) or "—"
        ch = next((x for x in r["slots"] if x.get("chosen")), None)
        n_sl = len(r["slots"])
        slot = (f"`{ch['name']}`" if ch else
                (f"{n_sl} candidate{'s' if n_sl != 1 else ''}, UNKNOWN" if n_sl else "—"))
        gain = fnum(ch.get("gain_db")) if ch else "—"
        L.append(f"| {r['id']} | {r['feature']} | {cell(ev)} | {cell(src)} | `{r['dispo']}` |"
                 f" {cell(slot)} | {gain} | {cell(r['verify'])} |")
    L += ["", "## Why each row maps or does not", "",
          "| id | match / reason | slot method | confidence |", "|---|---|---|---|"]
    for r in d["rows"]:
        L.append(f"| {r['id']} | {cell(r['match'])} | {cell(r['slot_method'])} |"
                 f" `{r['slot_confidence']}` |")
    L += ["", "## Sample slots measured (the swap targets)", "",
          "| bank | # | name | rate | ch | frames | loop | LUFS | peak dBFS | source | gain dB |"
          " delivered | Δ LU | clip % | stretch |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in d["slots"]:
        loop = (f"{x['loop_start']}..{x['loop_end']}"
                if x.get("loop_start") is not None else "one-shot")
        src = x.get("source") or "—"
        if x.get("source_span_s"):
            src += f" ({x['source_span_s']} s{' tail' if x.get('source_rule') == 'slot_src' else ''})"
        L.append(f"| {x['bank']} | {x['index_1based']} | `{x['name']}` | {x.get('rate')} |"
                 f" {x.get('channels')} | {x.get('frames')} | {loop} | {fnum(x.get('lufs'))} |"
                 f" {fnum(x.get('peak_dbfs'))} | {cell(src)} | {fnum(x.get('gain_db'))} |"
                 f" {fnum(x.get('delivered_lufs'))} | {fnum(x.get('delta_lu'))} |"
                 f" {fnum(x.get('clip_pct'))} | {fnum(x.get('stretch_ratio'), 4)} |")
    L += ["", "`#` is the 1-based index vgmstream takes; `index_0based` in the JSON is the index",
          "`Tools/scripts/_apply_audio.py` uses. `gain dB` is what B-11 applies; `delivered` is the",
          "integrated loudness **measured on the payload the swap writes** (mono downmix, gain,",
          "trim/pad with zeros to the slot's frame count, PCM16 clip + quantise) and `Δ LU` is",
          "`delivered − slot`, the card's ±1 LU test. `clip %` is the share of samples the gain",
          "pushed past full scale. The stretch is the trim/pad factor that keeps the payload's byte",
          "size (route a).",
          "",
          "**No candidate carries an FSB5 loop field** — not `premium_nitro_loop`, not",
          "`minigun_fire_close_loop_04`, not `missile_trail_rear_loop`. Their names say loop and the",
          "files' loop fields are empty. Whether the looping is then produced by the event/tune",
          "graph, or this bank build simply ships no loop metadata, was **not measured** — UNKNOWN.",
          "A swapped payload only has to fill the slot's frame count; it cannot move a loop point",
          "that is not in the file.",
          "", "## RPM curve fits (BmAK `REV_RPM` → JC3 rpm)", ""]
    any_curve = False
    for r in d["rows"]:
        if not r.get("curve_rpm"):
            continue
        any_curve = True
        pts = ", ".join(f"{p['rpm']}→{p['y']:+.3f}" for p in r["curve_rpm"])
        L.append(f"- **{r['id']}** ({r['feature']}): {pts}")
    if not any_curve:
        L.append("- none")
    L += ["", "The y values are the BmAK curve's own normalised values. Which FMOD target they",
          "drive (volume dB, pitch cents, low-pass) is **not** in the recovered RTPC data, so the",
          "fit re-bases the domain only; B-11 must not read y as a pitch multiplier until a probe",
          "says so (UNKNOWN, Q-1 #8).", "",
          "## Weapons", "",
          "| id | weapon | JC3 carrier / event | BmAK source | dispo |", "|---|---|---|---|---|"]
    for r in d["rows"]:
        if r["kind"] != "weapon":
            continue
        evs = [x.get("event") or os.path.basename(x.get("wav") or "") for x in r["sources"]]
        src = len(evs) > 4 and f"{len(evs)} events (`{evs[0]}` …) "or", ".join(evs) or "—"
        L.append(f"| {r['id']} | {r['role']} | {cell(r.get('carrier') or r['roles'][0])} |"
                 f" {cell(src)} | `{r['dispo']}` |")
    L += ["", "`w602`/`w603` carry no audio of their own (G2-24 §7); WPN-2's audio route is `w619`",
          "(W-03), WPN-1 and WPN-3 keep JC3's stock weapon samples because BmAK's cannon and",
          "missile launch media are not in the four vehicle packages.", "",
          "## Named omissions and decisions", "",
          "| id | what stays vanilla / waits | why |", "|---|---|---|"]
    for r in d["rows"]:
        if r["feature"] == "UNASSIGNED":
            continue
        if r["dispo"] in ("named omission", "kept vanilla", "remove", "blocked"):
            L.append(f"| {r['id']} | `{r['dispo']}` | {cell(r['match'])} |")
    L.append(f"| D-01…D-{s['unassigned_rows']:02d} | `kept vanilla` | {s['unassigned_rows']} pinned "
             "GUIDs that no `.epe` object names and no BmAK behaviour answers (G2-24 §3): they are "
             "the vehicle bank's shared set, kept exactly as shipped |")
    b = s["banks"]
    L += ["", "## Event → tune (the edge the bank does store)", "",
          "`TLNS` → `LIST TMLN` → `TLNB` holds one body per event: **body 0:16 is the tune GUID,",
          "body 16:32 the GUID of the event that owns it**, and the owner event's own body carries",
          "the tune GUID at offset 32.", "",
          f"* {b['tunes']} tunes / {b['events']} events in vehicles.bank: {b['owner_guid_is_event']} "
          f"tune bodies name an `EVTS` GUID and {b['owner_body_holds_tune']} owner event bodies "
          "hold the tune GUID at offset 32.",
          f"* {b['wave_guids_in_tune_list']} of {b['waves']} sample GUIDs occur anywhere in the "
          "`TLNS` section: **tune → sample is not stored.**",
          f"* {s['tunes_resolved']} donor rows resolve their tune here (vehicles.bank); "
          f"{s['tunes_unknown']} sit in banks this card does not decode (UNKNOWN).",
          "", "| row | role | tune GUID | tune # |", "|---|---|---|---|"]
    for r in d["rows"]:
        if not r.get("tune"):
            continue
        L.append(f"| {r['id']} | `{r['role'] or 'unnamed'}` | `{r['tune']['tune_guid']}` |"
                 f" {r['tune']['index']} |")
    e = s["engine"]
    stacks = ", ".join(f"`{k}` {len(v)}" for k, v in (e.get("rpm_stacks") or {}).items())
    L += ["", "## What the files do not give (UNKNOWN)", "",
          "1. **Which sample an event plays.** event→tune is stored (above); **tune→sample is",
          "   not** — no sample GUID appears in the tune list and the rest of the tune body is not",
          "   decoded. Every `candidate` slot is a name match with a Q-1 audition as its verify;",
          "   only the nitro slots are proven.",
          f"2. **Which sample the donor's own engine event reaches.** vehicles.bank has "
          f"{e.get('engine_named')} names containing `engine` out of {e.get('names')}, and the "
          f"`_engine_rpm_` layer stacks are {stacks}. The donor is a fictional sports car, so no "
          "name says which family its `engine_running_sound` tune uses — A-01 lists **every** "
          "layer of the largest stack as candidates and stays `blocked` until the audition.",
          "3. **The RTPC y target** (volume / pitch / low-pass). The recovered entries carry",
          "   parameter, curve type and points only.",
          "4. **JC3 has no speed/boost parameter.** `LandAudio` is `min_rpm` + `max_rpm` only, so",
          "   the BmAK `Speed`, `BML_WheelSpeed`, `BML_Steering*`, `Drift`, `EngineHeat`,",
          "   `Occlusion` bindings have no JC3 input to drive them; they are recorded per source",
          "   event in the JSON and cannot be mapped.",
          "5. **Whether a bank swap alone silences the horn.** The horn is a GUID-pinned event;",
          "   deleting the object is the data side, the input binding is code (Q-1).",
          "", "## Reproduce", "",
          "```",
          "python Tools/scripts/t12_audio.py --write      # regenerate JSON + MD, decode + measure",
          "python Tools/scripts/t12_audio.py --check      # Done-when gate (rebuilds and compares)",
          "python Tools/scripts/t12_audio.py --check --fast   # skip the decode, reuse measurements",
          "python Tools/scripts/t12_audio.py dump rows|slots|curves",
          "```", "",
          "The first run extracts `sound/fmod_banks/weapons.bank` (177,586,080 B) to",
          "`E:\\Modding\\_gamedata\\JC3grab\\audio\\` — game data stays outside the repo (R10).", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------
def invariants(d: dict) -> list[str]:
    bad = []
    s = d["summary"]
    if s["donor_rows"] != 45:
        bad.append(f"{s['donor_rows']}/45 donor events")
    if s["weapon_rows"] != len(WEAPON_ROWS):
        bad.append(f"{s['weapon_rows']} weapon rows, expected {len(WEAPON_ROWS)}")
    for r in d["rows"]:
        if r["dispo"] not in DISPOS:
            bad.append(f"{r['id']} disposition {r['dispo']!r}")
        if not r["verify"]:
            bad.append(f"{r['id']} has no verify cell")
        if r["dispo"] == "mapped" and not r["sources"] and not any(
                x.get("wav") for x in r["sources"]):
            bad.append(f"{r['id']} mapped with no BmAK source")
        if r["dispo"] == "mapped" and not r["slots"]:
            bad.append(f"{r['id']} mapped with no slot candidate")
        for x in r["slots"]:
            if x.get("missing"):
                bad.append(f"{r['id']} slot {x['name']} not in {x['bank']}")
        if r["chosen"] and not any(x.get("chosen") for x in r["slots"]):
            bad.append(f"{r['id']} chosen slot not among the candidates")
    for f in FEATURES:
        if f not in s["features"]:
            bad.append(f"{f} has no row")
    if s["unassigned_rows"] != 45 - 23:
        bad.append(f"{s['unassigned_rows']} unassigned rows, expected 22 (45 pinned - 23 named)")
    covered = set()
    for x in SPECS:
        covered.add(x["role"])
        covered.update(x.get("aliases") or [])
    for r in d["rows"]:
        if r["kind"] != "donor":
            continue
        for role in r.get("roles") or []:
            if role not in covered:
                bad.append(f"named role {role} has no decision row")
    if s["slots_missing_from_bank"]:
        bad.append(f"{s['slots_missing_from_bank']} slot names not in the bank")
    # ---- the measured gain gate: a `mapped` row must have a chosen slot whose delivered
    # payload was measured, and |delivered - slot| must be within the card's 1 LU.
    for r in d["rows"]:
        has_src = any(x.get("source") for x in r["sources"])
        for x in r["slots"]:
            if has_src and "gain_db" not in x:
                bad.append(f"{r['id']} slot {x['name']} has a source but no gain")
            if not has_src and x.get("gain_db") is not None:
                bad.append(f"{r['id']} slot {x['name']} has a gain with no source")
            if "gain_db" in x and x.get("delta_lu") is None:
                bad.append(f"{r['id']} slot {x['name']} has a gain but no measured delta")
            if x.get("chosen"):
                if x.get("delta_lu") is None:
                    bad.append(f"{r['id']} chosen slot {x['name']} has no measured delta")
                elif abs(x["delta_lu"]) > 1.0:
                    bad.append(f"{r['id']} chosen slot {x['name']} misses the 1 LU gate "
                               f"({x['delta_lu']:+.2f} LU)")
        if r["dispo"] == "mapped":
            if not r["chosen"]:
                bad.append(f"{r['id']} is mapped with no chosen slot")
            elif not any(x.get("chosen") for x in r["slots"]):
                bad.append(f"{r['id']} chosen slot not among the candidates")
        if r["dispo"] == "kept vanilla" and not r.get("spec"):
            bad.append(f"{r['id']} is kept vanilla without a SPECS decision")
        if r["dispo"] == "blocked" and not str(r["verify"]).startswith("blocked:"):
            bad.append(f"{r['id']} is blocked but its verify does not name the blocker")
    if s["chosen_over_1lu"]:
        bad.append(f"chosen slot(s) outside the gate: {s['chosen_over_1lu']}")
    if s["slots_with_gain"] == 0:
        bad.append("no slot was gain-matched")
    # ---- the tune edge and the engine census are measurements, not prose
    b = d.get("tunes") or {}
    if b.get("tunes") != b.get("events"):
        bad.append(f"{b.get('tunes')} tunes for {b.get('events')} events")
    if b.get("owner_guid_is_event") != b.get("tunes"):
        bad.append(f"{b.get('owner_guid_is_event')}/{b.get('tunes')} tune bodies name an EVTS GUID")
    if b.get("owner_body_holds_tune") != b.get("tunes"):
        bad.append(f"{b.get('owner_body_holds_tune')}/{b.get('tunes')} event bodies hold the tune"
                   f" GUID at offset 32")
    if b.get("wave_guids_in_tune_list"):
        bad.append(f"{b.get('wave_guids_in_tune_list')} sample GUIDs occur in TLNS - the"
                   f" tune->sample negative would be false")
    e = d.get("engine_census") or {}
    stacks = e.get("rpm_stacks") or {}
    if not stacks:
        bad.append("no `_engine_rpm_` stack found in the name table")
    else:
        big = max(stacks.items(), key=lambda kv: len(kv[1]))
        a1 = next((x for x in SPECS if x["id"] == "A-01"), None)
        if a1 and sorted(a1["slots"]) != sorted(big[1]):
            bad.append(f"A-01 lists {len(a1['slots'])} layers, the largest stack `{big[0]}` has "
                       f"{len(big[1])}")
        a1row = next((r for r in d["rows"] if r["id"] == "A-01"), None)
        listed = sorted(s["name"] for s in (a1row or {}).get("slots") or [] if not s.get("missing"))
        if a1row and listed != sorted(big[1]):
            bad.append(f"A-01 carries {len(listed)} of the {len(big[1])} `{big[0]}` layers")
    if e.get("engine_named") is None or e.get("names") is None:
        bad.append("engine census missing")
    la = d["jc3"]["land_audio"]
    if float(la.get("min_rpm", 0)) != 1000.0 or float(la.get("max_rpm", 0)) != 10000.0:
        bad.append(f"LandAudio {la}")
    if d["jc3"]["donor_events"] != 45 or d["jc3"]["named"] != 23:
        bad.append(f"donor {d['jc3']['donor_events']}/{d['jc3']['named']}")
    if d["bmak"]["rows"] != 361 or d["bmak"]["media"] != 447:
        bad.append(f"G1-15 {d['bmak']['rows']}/{d['bmak']['media']}")
    ids = [r["id"] for r in d["rows"]]
    if len(set(ids)) != len(ids):
        bad.append("duplicate row id")
    return bad


def cmd_write(measure: bool = True) -> int:
    prev = None
    jp = os.path.join(OUTDIR, JSON_NAME)
    if not measure and os.path.exists(jp):
        prev = json.load(open(jp, encoding="utf-8"))
    d = build(measure, prev)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(jp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUTDIR, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    s = d["summary"]
    print(f"{JSON_NAME}/{MD_NAME}: {s['rows']} rows ({s['donor_rows']} donor + "
          f"{s['weapon_rows']} weapon/mode), {s['mapped_rows']} mapped with "
          f"{s['chosen_slots']} chosen slot(s), {s['slot_candidates']} slot candidates, "
          f"{s['slots_with_gain']} gain-matched (max |delivered-slot| "
          f"{s['max_abs_delta_lu']} LU, {len(s['slots_over_1lu'])} over 1 LU), "
          f"{s['rpm_curve_rows']} rpm curves, tunes {s['tunes_resolved']}/{s['donor_rows']}, "
          f"dispositions {s['by_disposition']}, {len(md.splitlines())} md lines")
    return 0


def cmd_check(fast: bool = False) -> int:
    jp, mp = os.path.join(OUTDIR, JSON_NAME), os.path.join(OUTDIR, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    have = json.load(open(jp, encoding="utf-8"))
    d = build(not fast, have if fast else None)
    if fast:
        d["measurements"] = have.get("measurements", {})
        for r in d["rows"]:
            for x in r["slots"]:
                got = d["measurements"].get(f"{x['bank']}:{x['name']}")
                if got:
                    for k, v in got.items():
                        x.setdefault(k, v)
        d["slots"] = have.get("slots", d["slots"])
        d["summary"] = summarise(d)
    bad = invariants(d)
    if have != d:
        diff = []
        for k in sorted(set(have) | set(d)):
            if have.get(k) != d.get(k):
                diff.append(k)
        bad.append("json stale: " + ",".join(diff))
    md = render_md(d)
    got = open(mp, encoding="utf-8").read()
    if md != got:
        ud = list(difflib.unified_diff(got.splitlines(), md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(ud[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    s = d["summary"]
    print(f"PASS: {s['rows']} rows = {s['donor_rows']}/45 donor events + {s['weapon_rows']} "
          f"weapon/mode rows | dispositions {s['by_disposition']} | {s['mapped_rows']} mapped with "
          f"{s['chosen_slots']} chosen slot(s) | {s['slot_candidates']} slot candidates "
          f"({s['slots_with_gain']} gain-matched on the written payload, max |delivered-slot| "
          f"{s['max_abs_delta_lu']} LU, {len(s['slots_over_1lu'])} over 1 LU - chosen "
          f"{len(s['chosen_over_1lu'])}; {s['slots_stock']} kept stock) | tunes "
          f"{s['tunes_resolved']}/{s['donor_rows']} | {s['rpm_curve_rows']} rpm curves | features "
          f"{len(s['features'])}/7 | json match True, md match True")
    return 0


def cmd_dump(what: str) -> int:
    d = build(False, json.load(open(os.path.join(OUTDIR, JSON_NAME), encoding="utf-8")))
    key = {"rows": "rows", "slots": "slots", "curves": "rows"}.get(what)
    if key is None:
        print("one of: rows, slots, curves")
        return 2
    if what == "curves":
        print(json.dumps([{k: r[k] for k in ("id", "feature", "curve_rpm")} for r in d["rows"]
                          if r.get("curve_rpm")], indent=1)[:20000])
    else:
        print(json.dumps(d[key], indent=1, sort_keys=True)[:20000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--fast", action="store_true", help="skip the decode, reuse measurements")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="rows")
    a = p.parse_args()
    if a.write:
        return cmd_write(not a.fast)
    if a.check:
        return cmd_check(a.fast)
    if a.cmd == "dump":
        return cmd_dump(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
