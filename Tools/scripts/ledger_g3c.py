"""ledger_g3c.py - G3-20c: the remaining ledger rows against what the G3 cards actually decoded.

Thin ledger pass, no new decoding and no translation decision. For every row of
`Working/Translation/T_ROWS.jsonl` in the groups this task owns (T-20, T-3, T-7, T-15, T-14)
the row is either

  QUOTED - a named G3 card decodes the member the row is about; the exact value is quoted
           with `file:line`, and the `relation` says how it stands to the ledger's number
           (`agrees` / `differs` / `different-object` / `different-member` / `supplies`);
  OPEN   - no named card answers it; `supplier` names the file that would.

The card set is exactly the one the task names:
  Research/BatmobileGrab/{PACKAGES_G305,REMAINDER,SKINS,COLOUR,AUDIO_BANKS,CLASS_DEFAULTS}.md
  Research/JC3Grab/{DECODE_DEPTH,DECODE_DEPTH2,DECODE_DEPTH3,COLOUR,COLOUR_NATIVE}.md

The earlier keyword pass (`Working/Translation/LEDGER_G3.md`, `ledger_g3.py`) is NOT read and
is NOT evidence: none of its statuses are reused here.

Oracle (`--check`), all recomputed from the source bytes each run:
  1. the in-scope row set is derived from T_ROWS.jsonl and must equal the table's exactly;
  2. every quoted `file:line` is re-opened, and the quote must be a substring of that line
     after whitespace normalisation, as must each `must` value - so a moved line, a changed
     value or a wrong number fails the check;
  3. every "not in the class defaults" claim is asserted against the file it names;
  4. the status/relation/document counts and the per-card counts are recomputed and compared
     with the committed JSON, and the Markdown is byte-compared.

    python Tools/scripts/ledger_g3c.py --write
    python Tools/scripts/ledger_g3c.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3C.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3C.json")

SCOPE = ("T-20", "T-3", "T-7", "T-15", "T-14")

CD = "Research/BatmobileGrab/CLASS_DEFAULTS.md"
RM = "Research/BatmobileGrab/REMAINDER.md"
SK = "Research/BatmobileGrab/SKINS.md"
AB = "Research/BatmobileGrab/AUDIO_BANKS.md"
DD1 = "Research/JC3Grab/DECODE_DEPTH.md"
DD2 = "Research/JC3Grab/DECODE_DEPTH2.md"
DD3 = "Research/JC3Grab/DECODE_DEPTH3.md"
PK = "Research/BatmobileGrab/PACKAGES_G305.md"
BC = "Research/BatmobileGrab/COLOUR.md"
JC = "Research/JC3Grab/COLOUR.md"
JN = "Research/JC3Grab/COLOUR_NATIVE.md"

CARDS = [PK, RM, SK, BC, AB, CD, DD1, DD2, DD3, JC, JN]


def ev(path, line, quote, must=()):
    return {"file": path, "line": int(line), "quote": quote, "must": list(must)}


def R(rid, doc, member, status, relation, evidence, ledger, note, supplier="", absent=()):
    return {
        "id": rid,
        "doc": doc,
        "member": member,
        "status": status,
        "relation": relation,
        "evidence": list(evidence),
        "ledger": ledger,
        "note": note,
        "supplier": supplier,
        "absent": list(absent),
        "absent_file": CD if absent else "",
    }


NOTHING = "nothing in the named card set"

ROWS = [
    # ------------------------------------------------------------------ T-3
    R("T-G6", "T-3", "`land_global.front/rear_wheels.radius`", "OPEN", "confirms-open",
      [ev(RM, 1901, "| 171139 | `WheelFL` | `SVehicleWheel` | 14",
          ["past the 0x20000000 decode budget"])],
      "mesh 0.68275 / 0.68265 m (BmAK `SVehicleWheel.WheelRadius` 64.0)",
      "the four `SVehicleWheel` class defaults (WheelFL/FR/RL/RR, exports 171139-171142) are "
      "14-byte payloads past the 512 MiB decode budget, so the class-default route to "
      "`WheelRadius` is unread; CLASS_DEFAULTS has no `WheelRadius` tag at all",
      "`CHAIN.json` (the archetype wheel tags the row already cites); otherwise REMAINDER §3b "
      "once the budget allows",
      absent=["WheelRadius"]),

    R("T-S6", "T-3", "`suspension.*.length / min_length / strength / compression`", "OPEN",
      "confirms-open",
      [ev(DD1, 63, "| `hknpPhysicsSystemData` | 1 | PARTIAL |",
          ["the 80-byte body and 64-byte motion entry fields are counted and sized but not pinned"])],
      "no JC3 member; BmAK TravelUp 30 / TravelDown 40 / BMRearWheelMaxDroop 100",
      "JC3's suspension model is still not decoded: the wheel hardpoints read at +0x30 of the "
      "96-byte entries, but the 80-byte body and 64-byte motion entries are never pinned. On the "
      "BmAK side CLASS_DEFAULTS carries no suspension member on any class it reads "
      "(`Suspension`, `SuspensionTravel`, `BMRearWheelMaxDroop`, `WheelSuspensionStiffness` all "
      "absent), so the stroke/rate pair is still only in the archetype",
      "`Research/JC3Grab/PHYSICS_WRITE.md` UNKNOWN 4 (the body-entry fields) plus the archetype "
      "`SVehicleWheel` tags in `CHAIN.json`",
      absent=["Suspension", "SuspensionTravel", "BMRearWheelMaxDroop", "WheelSuspensionStiffness"]),

    R("T-ST7", "T-3", "`land_steering.t_to_full_steer_s` (BmAK `SteerSpeed` 220 deg/s)", "OPEN",
      "adjacent",
      [ev(CD, 317, "`DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) | FloatProperty | 1.0",
          ["1.0"])],
      "0.8 s low / 0.6 s high speed; BmAK 220 deg/s = 0.25 s to lock",
      "the only steering-rate member in the two class-default streams is "
      "`DriftCorrectionSteerSpeed` 1.0 (a neutral drift modifier, already used by T-ST5); "
      "`SteerSpeed` 220 deg/s and the `SteerSpeedVsSpeedCurve` knots are not class defaults, so "
      "the 0.25 s figure is not re-derived here",
      "the archetype `RVehicleSimBatmobile` tag stream (`objects.jsonl` / `CHAIN.json`)",
      absent=["`SteerSpeed`"]),

    R("T-K4", "T-3", "`brakes.*.handbrake`, `min_time_to_block` (BmAK `EbrakeTime`, `EBrakeBrakeForce`)",
      "QUOTED", "differs",
      [ev(CD, 183, "`EbrakeTime` (RVehicleBatmobileBase) | FloatProperty | 1.0", ["1.0"]),
       ev(CD, 184, "`EBrakeBrakeForce` (RVehicleBatmobileBase) | FloatProperty | 160000.0",
          ["160000.0"])],
      "`EbrakeTime` 0.75, `EBrakeBrakeForce` 640000, `HandbrakeOnSpeed` 10000, `HandbrakeOffSpeed` 1, "
      "`HandbrakeLatSlipFactor` 1.5/1.1",
      "same two member names, different numbers, and the card's object is explicitly the "
      "class-default export `BmGame.Default__RVehicleBatmobileBase` (BmGame.upk export 10923), not "
      "the four-car archetype the row reads: 1.0 vs 0.75 and 160000.0 vs 640000. The other three "
      "members the row cites are not class defaults. `EBrakeAccelForce` 100000.0 sits beside them "
      "(line 185)",
      "",
      absent=["HandbrakeOnSpeed", "HandbrakeOffSpeed", "HandbrakeLatSlip"]),

    R("T-DR1", "T-3", "`custom_land_global.drift.*` (BmAK `LatSlipFactor`, `HandbrakeLatSlipFactor`)",
      "OPEN", "adjacent",
      [ev(CD, 317, "`DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) | FloatProperty | 1.0",
          ["1.0"]),
       ev(CD, 312, "`DriftAngularVelocityFactor` (RVehicleBatmobileBase) | FloatProperty | 320.0",
          ["320.0"])],
      "`LatSlipFactor` 1.6, `HandbrakeLatSlipFactor` 1.5/1.1, `DriftingBoostCooldown` 1.5 s",
      "the class defaults carry the drift *steering* block (correction 1.0, angular-velocity "
      "factor 320.0, plus `DriftSpeedBySteer` / `DriftAngularVelocityBySteer` curves with 3 points "
      "each) but neither slip member the row cites",
      "the archetype tags for `LatSlipFactor` / `HandbrakeLatSlipFactor` (`CHAIN.json`, G1-1)",
      absent=["LatSlipFactor", "HandbrakeLatSlip"]),

    R("T-EF1", "T-3", "`vehiclecommon.tire_effects.*` (BmAK `SquealThreshold`, `SquealLatThreshold`)",
      "QUOTED", "differs",
      [ev(CD, 164, "`SquealThreshold` (SVehicle) | FloatProperty | 0.5", ["0.5"]),
       ev(CD, 165, "`SquealLatThreshold` (SVehicle) | FloatProperty | 0.5", ["0.5"])],
      "`SquealThreshold` 0.2, `SquealLatThreshold` 0.2 (row keeps 0.5 / 0.8 / 0.25 JC3 values)",
      "both thresholds decode as 0.5 on the class default (SVehicle, Engine\\SVehicle.g.cs:1493 and "
      ":1502), not 0.2; the card's object is the class default, so this is a second reading of the "
      "same member name, not a re-read of the archetype the row quotes",
      ""),

    R("T-DM7", "T-3", "outgoing ram damage (`ImpactMinDamageSpeed` etc.)", "QUOTED", "differs",
      [ev(CD, 257, "`ImpactMinDamageSpeed` (RVehicleBatmobileBase) | FloatProperty | 60.0", ["60.0"]),
       ev(CD, 256, "`ImpactMaxDamageSpeed` (RVehicleBatmobileBase) | FloatProperty | 200.0", ["200.0"]),
       ev(CD, 258, "`ImpactStrafeMod` (RVehicleBatmobileBase) | FloatProperty | 1.5", ["1.5"]),
       ev(CD, 260, "`ImpactBoostMod` (RVehicleBatmobileBase) | FloatProperty | 1.5", ["1.5"])],
      "`ImpactMinDamageSpeed` 20, `ImpactMaxDamageSpeed` 150, `ImpactStrafeMod` 2.25, `ImpactBoostMod` 2.0",
      "all four decode to different numbers on the class default: 60.0 / 200.0 / 1.5 / 1.5. The "
      "row's outgoing-damage conclusion is untouched by this card (it rests on the class API, "
      "G2-28), but its BmAK numbers are not the class-default ones",
      ""),

    R("T-DM8", "T-3", "`vehicledamage.impact_damage_factor`", "OPEN", "adjacent",
      [ev(CD, 255, "`ImpactMaxDamage` (RVehicleBatmobileBase) | FloatProperty | 100.0", ["100.0"])],
      "0 (declared switch); BmAK behaviour: ramming never damages the car",
      "the carrier is a JC3 module member and no named card reads it. The one BmAK number next to "
      "the behaviour is `ImpactMaxDamage` 100.0 (the outgoing impact magnitude the switch "
      "multiplies off), which the row does not cite",
      "`Working/Damage/*` plus the `vehicle_damage` module read the switch (the row's own source)"),

    R("T-DM9", "T-3", "entity root `CCar.invulnerable`", "OPEN", "adjacent",
      [ev(CD, 353, "`Health` (Pawn) | IntProperty | 1000", ["1000"]),
       ev(CD, 321, "`ArmourLevels` (RVehicleBatmobileBase) | ArrayProperty | count=5 int [0, 300, 600, 900, 1200]",
          ["[0, 300, 600, 900, 1200]"])],
      "all armour channels at the shipped ceiling; root flag 0; BmAK `Health` 1,200 (archetypes)",
      "the class defaults give BmAK's own armour ladder: Pawn `Health` 1000 and `ArmourLevels` "
      "[0, 300, 600, 900, 1200] with `LowHealthWarningLevel` 300 (line 322). Neither is the JC3 "
      "armour channel the row edits, and 1000 is not the 1,200 the row attributes to BmAK",
      "`Working/Damage/bm_health.json` and the 232-graph `DAMAGE_MECHANISMS.md` read (the row's "
      "own sources)"),

    R("T-FX6", "T-3", "entity-graph effect members", "QUOTED", "agrees",
      [ev(CD, 111, "`RearFinTrail` (RVehicleBatmobileBase) | ComponentProperty | Default__RVehicleBatmobile.FinTrail0 (ParticleSystemComponent)",
          ["FinTrail0"]),
       ev(CD, 112, "`BrakeLightTrailSystemL` (RVehicleBatmobileBase) | ComponentProperty | Default__RVehicleBatmobile.BrakeTrail0 (ParticleSystemComponent)",
          ["BrakeTrail0"]),
       ev(CD, 113, "`BrakeLightTrailSystemR` (RVehicleBatmobileBase) | ComponentProperty | Default__RVehicleBatmobile.BrakeTrail1 (ParticleSystemComponent)",
          ["BrakeTrail1"]),
       ev(CD, 114, "`SpeedLinesSystem` (RVehicleBatmobileBase) | ComponentProperty | Default__RVehicleBatmobile.SpeedLines0 (ParticleSystemComponent)",
          ["SpeedLines0"]),
       ev(CD, 131, "`HeatSteam` (RVehicleBatmobileBase) | ComponentProperty | Default__RVehicleBatmobile.HeatSteam (ParticleSystemComponent)",
          ["HeatSteam"]),
       ev(CD, 140, "`WallScrapeSparksSystemR` (RVehicleBatmobileBase) | ComponentProperty | Default__RVehicleBatmobile.WallScrape1 (ParticleSystemComponent)",
          ["WallScrape1"]),
       ev(CD, 141, "`WallScrapeSparksSystemL` (RVehicleBatmobileBase) | ComponentProperty | Default__RVehicleBatmobile.WallScrape0 (ParticleSystemComponent)",
          ["WallScrape0"]),
       ev(CD, 192, "`SideExhaustBurstEffect` (RVehicleBatmobileBase) | ObjectProperty | Exhaust.Batmobile_Side_Exhaust (ParticleSystem)",
          ["Batmobile_Side_Exhaust"]),
       ev(CD, 193, "`SideExhaustBoostEffect` (RVehicleBatmobileBase) | ObjectProperty | Exhaust.Batmobile_Side_Exhaust (ParticleSystem)",
          ["Batmobile_Side_Exhaust"]),
       ev(CD, 194, "`JumpLandSparksEffectL` (RVehicleBatmobileBase) | ObjectProperty | Impacts.Batmobile_Landing_Sparks_L (ParticleSystem)",
          ["Batmobile_Landing_Sparks_L"])],
      "carried from test-083: `BrakeLightTrailSystemL/R`, `RearFinTrail`, `SpeedLinesSystem`, "
      "`HeatSteam`, `WallScrapeSparksSystemL/R`, `ExhaustBurstEffect`, `SideExhaust*`, wheel particles",
      "every member the row lists is decoded as a component/object reference on the class default, "
      "with the asset it points at: FinTrail0, BrakeTrail0/1, SpeedLines0, HeatSteam, "
      "WallScrape1/0, `Exhaust.Batmobile_Side_Exhaust` (both side-exhaust members point at the same "
      "PS), `Impacts.Batmobile_Landing_Sparks_L`. The row's list is complete for these",
      ""),

    R("T-AU5", "T-3", "audio banks in the entity graph (`TransformationReverseDirection*`, `TaserSound`, `VehicleSound`)",
      "QUOTED", "differs",
      [ev(AB, 200, "**10 claimed / 90 event rows -> 10 found, 0 confirmed absent.**",
          ["10 found", "0 confirmed absent"]),
       ev(AB, 164, "**29** distinct `package.bank` references over **361** event rows",
          ["**29**", "**361**"]),
       ev(AB, 170, "| `BML_Battlemode` | `Engine` |", ["830548", "7"])],
      "blocked: \"these events have no JC3 bank and 10 BmAK banks are absent from the install\"",
      "the absence premise fails: the 10 banks the row calls absent are all FOUND (as `AkBank` "
      "exports in Startup/BmGame/StartupPatch, 0 confirmed absent), and 29 of 29 referenced banks "
      "are present as package exports with 0 absent. `BML_Battlemode` (830,548 B, 7 events) and "
      "`BML_Batmobile` (2,268,588 B, 53 events, line 168) are the transformation/mode banks. What "
      "stays open is the JC3-side translation of those events, not their source",
      ""),

    R("T-W1", "T-3", "11 BmAK weapon classes -> JC3 slots", "OPEN", "n/a",
      [], "superseded by T-11", "the card set holds no JC3 weapon-slot decode; the row is already "
      "superseded by T-11, whose rows carry the weapon ids and the two driver slots",
      "T-11's rows (`Working/Translation/T7_WEAPONS.md`, `Research/JC3Grab/WEAPONS.md`)"),

    R("T-BM1", "T-3", "`BattleMode*`, `TurnOnSpot*`, `TurningModeMaxSpeed`, `ArmourModeDamageReduction`",
      "QUOTED", "supplies",
      [ev(CD, 242, "`ArmourModeDamageReduction` (RVehicleBatmobileBase) | IntProperty | 20", ["20"]),
       ev(CD, 240, "`BattleModeYawOffset` (RVehicleBatmobileBase) | IntProperty | 16384", ["16384"]),
       ev(CD, 246, "`BattleModeWidth` (RVehicleBatmobileBase) | FloatProperty | 265.0", ["265.0"]),
       ev(CD, 243, "`BattleModeTransformationAnimName` (RVehicleBatmobileBase) | NameProperty | 'Batmobile_V2_Tank_Spread_Open_Game'",
          ["Batmobile_V2_Tank_Spread_Open_Game"])],
      "the row lists the member names without values (superseded by T-12 + T-15)",
      "the class defaults give values for the battle side: armour reduction 20, yaw offset 16384, "
      "the mode box 265 x 430 x 250 (lines 246-248), and the two transformation animation names. "
      "`TurnOnSpot*` and `TurningModeMaxSpeed` are in neither stream, which is consistent with the "
      "row's split to T-15/T-12 but is not a decode of them",
      "",
      absent=["TurnOnSpot", "TurningModeMaxSpeed"]),

    R("T-AC1", "T-3", "`AirControlYawTorqueFactorMax` 8000", "OPEN", "confirms-open",
      [], "out: no JC3 yaw-torque member (`VOCABULARY.md`)",
      "the named cards do not carry the member: no `AirControlYawTorque*` tag exists in either "
      "class-default stream, so the 8000 is not re-derived here and the JC3 half is unchanged",
      "the archetype `RVehicleSimBatmobile` tags in `objects.jsonl`; the JC3 absence is already "
      "proven in `Research/JC3Grab/VOCABULARY.md`",
      absent=["AirControlYawTorque"]),

    R("T-RA1", "T-3", "`ImpactRoadAssist*`, `PMDodge*`, `BattleDodgeImpulse`, `VehicleShovingTorque`, `KillFlip*`, `KillKeepyUp*`, `ImpactShake*`",
      "QUOTED", "differs",
      [ev(CD, 229, "`ImpactRoadAssistFactor` (RVehicleBatmobileBase) | FloatProperty | 40000.0", ["40000.0"]),
       ev(CD, 230, "`ImpactRoadAssistMaxTorque` (RVehicleBatmobileBase) | FloatProperty | 15000.0", ["15000.0"]),
       ev(CD, 235, "`ImpactRoadAssistAngleStrength` (RVehicleBatmobileBase) | FloatProperty | 1500.0", ["1500.0"]),
       ev(CD, 241, "`BattleDodgeImpulse` (RVehicleBatmobileBase) | FloatProperty | 100000.0", ["100000.0"]),
       ev(CD, 286, "`VehicleShovingTorque` (RVehicleBatmobileBase) | FloatProperty | 20000.0", ["20000.0"]),
       ev(CD, 270, "`KillFlipTorque` (RVehicleBatmobileBase) | FloatProperty | -2000000.0", ["-2000000.0"]),
       ev(CD, 272, "`KillKeepyUpFactor` (RVehicleBatmobileBase) | FloatProperty | 20.0", ["20.0"])],
      "`ImpactRoadAssist*` (90000 / 30000 / 2000), `VehicleShovingTorque` 10000, plus the "
      "`PMDodge*`, `BattleDodgeImpulse`, `KillFlip*`, `KillKeepyUp*`, `ImpactShake*` names",
      "seven of the row's numbers are different on the class default: RoadAssist factor 40000 "
      "(not 90000), max torque 15000 (not 30000), angle strength 1500 (not 2000), shoving torque "
      "20000 (not 10000); `BattleDodgeImpulse` 100000, `KillFlipTorque` -2000000, "
      "`KillKeepyUpFactor` 20.0 and `ImpactShake`/`ExplosiveImpactScreenShake` (18 nested props, "
      "lines 253 and 274) are decoded members. The row's `out` disposition rests on the JC3 "
      "vocabulary, which this card does not touch",
      ""),

    R("T-SR1", "T-3", "`JumpRampRightingTorque`, `JumpNoRampRightingTorque`, `StayUprightConstraintSetup/Instance`",
      "QUOTED", "differs",
      [ev(CD, 147, "`JumpRampRightingTorque` (RVehicleBatmobileBase) | FloatProperty | 5000.0", ["5000.0"]),
       ev(CD, 148, "`JumpNoRampRightingTorque` (RVehicleBatmobileBase) | FloatProperty | 2500.0", ["2500.0"]),
       ev(CD, 161, "`StayUprightConstraintSetup` (SVehicle) | ObjectProperty", ["MyStayUprightSetup"])],
      "`JumpRampRightingTorque` 2000, `JumpNoRampRightingTorque` 2000, `StayUprightConstraintSetup/Instance`",
      "the two torques decode as 5000.0 and 2500.0, not 2000 / 2000, and the stay-upright setup and "
      "instance are real object references (`RB_StayUprightSetup` / `RB_ConstraintInstance`). "
      "`JumpRampUpwardForce` 2000.0 (line 146) is the number that matches the row's 2000 - on a "
      "different member",
      ""),

    R("T-PA9", "T-3", "actor composition: components, refs", "QUOTED", "supplies",
      [ev(CD, 171, "`Components` (Actor) | ArrayProperty | count=4 ref ActorComponent",
          ["SVehicleMesh", "VisDmgComp", "BatmobileOnFireMeshComp0", "RVehicleSimBatmobile:SimulationModel"])],
      "carried by the entity graph; the row exists so the count is auditable",
      "the drivable class default's actor composition decodes exactly: 4 components (SVehicleMesh, "
      "VisDmgComp, BatmobileOnFireMeshComp0, SimulationModel). The base class default carries 3 "
      "(§5a, same line family), and that difference is the only component override between the two",
      ""),

    # ------------------------------------------------------------------ T-14
    R("T-L8", "T-14", "`HeadLight1` (row 13 point + row 8 volume)", "QUOTED", "supplies",
      [ev(CD, 263, "`HeadLightsColourPursuit` (RVehicleBatmobileBase) | StructProperty | raw 0000803f0000803f0000803f0000803f = 4 floats ['1.0', '1.0', '1.0', '1.0']",
          ["'1.0', '1.0', '1.0', '1.0'"]),
       ev(SK, 879, "| `HeadLight1` | `Winch_DOOR_Mesh` |", ["Winch_DOOR_Mesh"])],
      "BmAK LightColor 138,197,246,255 B 0.15 cone 20.0/70.0 R 6000.0; donor rows 13 + 8; anchor "
      "`sportsmuscle_LOD1·body·Winch_DOOR_Mesh·Winch_DOOR_Mesh_LIG`",
      "the pursuit headlight colour is a class default: 4 floats [1.0, 1.0, 1.0, 1.0] (white). The "
      "row's per-entry `LightColor` 138,197,246 is a different member on a different object, so it "
      "is not contradicted - but the car-level colour vector is decoded and it is white. SKINS "
      "confirms `HeadLight1`'s socket hangs on `Winch_DOOR_Mesh` in the baseline rig (the mk2 and "
      "jokerfied skins move it to `Batmobile_Chassis`)",
      ""),

    R("T-L9", "T-14", "`HeadLight2` (row 19 point + row 20 volume)", "QUOTED", "supplies",
      [ev(CD, 263, "`HeadLightsColourPursuit` (RVehicleBatmobileBase) | StructProperty | raw 0000803f0000803f0000803f0000803f = 4 floats ['1.0', '1.0', '1.0', '1.0']",
          ["'1.0', '1.0', '1.0', '1.0'"])],
      "BmAK LightColor 160,180,255,0 B 0.0 cone 10.0/35.0 R 0.1; donor rows 19 + 20",
      "same car-level colour vector as T-L8 (white 1,1,1,1); the row's second lamp entry is a "
      "different member with intensity 0",
      ""),

    R("T-L10", "T-14", "`ChainGunMuzzle` weapon light (omitted)", "OPEN", "n/a",
      [], "out: the fleet's 9 light behaviours have none for a gun",
      "no named card decodes the JC3 light behaviour list; the row's proof is "
      "`Research/JC3Grab/LIGHT_SYSTEM.md` §6",
      "`Research/JC3Grab/LIGHT_SYSTEM.md` (behaviours) - not in this card set"),

    R("T-L11", "T-14", "`HeadLight1` (stripped) -> `Front_Left_Point` + `Front_Left_Volumetric`",
      "OPEN", "adjacent",
      [ev(CD, 263, "`HeadLightsColourPursuit` (RVehicleBatmobileBase) | StructProperty | raw 0000803f0000803f0000803f0000803f = 4 floats ['1.0', '1.0', '1.0', '1.0']",
          ["'1.0', '1.0', '1.0', '1.0'"])],
      "BmAK LightColor 223,91,75,0 B 1.0 cone -/44.0 R 1024.0; donor rows 17 + 12",
      "the row's own light entry (red 223,91,75) has no class-default counterpart: the only decoded "
      "car-level light colour is the white pursuit vector, which belongs to the full rig, not this "
      "stripped variant",
      "`Research/JC3Grab/LIGHT_SYSTEM.md` presets (`Front_Left_Point` / `_Volumetric` rows)"),

    R("T-L12", "T-14", "`HeadLight2` (stripped) -> `Front_Right_Point` + `Front_Right_Volumetric`",
      "OPEN", "adjacent",
      [ev(CD, 263, "`HeadLightsColourPursuit` (RVehicleBatmobileBase) | StructProperty | raw 0000803f0000803f0000803f0000803f = 4 floats ['1.0', '1.0', '1.0', '1.0']",
          ["'1.0', '1.0', '1.0', '1.0'"])],
      "BmAK LightColor 223,91,75,0 B 1.0 cone -/44.0 R 1024.0; donor rows 11 + 14",
      "as T-L11: only the white pursuit colour vector is decoded at car level",
      "`Research/JC3Grab/LIGHT_SYSTEM.md` presets (`Front_Right_Point` / `_Volumetric` rows)"),

    R("T-L13", "T-14", "`LWheelLight` -> custom `sportsmuscle_wheel_f_l_arch` (preset 0)", "OPEN", "n/a",
      [], "custom entry, 25 members, G2-33 §7",
      "no named card covers the JC3 light-preset namespace or a custom preset-0 entry; the row's "
      "proof is `Research/JC3Grab/LIGHT_SYSTEM.md` §7",
      "G2-33 §7 recipe (`Research/JC3Grab/LIGHT_SYSTEM.md`)"),

    R("T-L14", "T-14", "`RWheelLight` -> custom `sportsmuscle_wheel_f_r_arch` (preset 0)", "OPEN", "n/a",
      [], "custom entry, 25 members, G2-33 §7",
      "as T-L13, mirrored",
      "G2-33 §7 recipe (`Research/JC3Grab/LIGHT_SYSTEM.md`)"),

    R("T-L15", "T-14", "`BrakeLightL` -> `Sport_Muscle_Rear_Break_Left` (row 18)", "QUOTED", "supplies",
      [ev(CD, 122, "`BrakeLightsLensFlare` (RVehicleBatmobileBase) | ObjectProperty | Batmobile.Batmobile_brakelights (LensFlare)",
          ["Batmobile.Batmobile_brakelights"])],
      "BmAK LightColor 255,38,0,0 B 1.0 R 150.0; donor row 18 on `sportsmuscle_signal_r_l`",
      "the brake lamps have their own flare object as a class default: "
      "`Batmobile.Batmobile_brakelights` (LensFlare). That is the object behind the row's brake "
      "colour, not a module member; `TailLightsLensFlare` (`Batmobile_brakelights_alwaysOn`, line "
      "123) is its always-on sibling",
      ""),

    R("T-L16", "T-14", "`BrakeLightR` -> `Sport_Muscle_Rear_Break_Right` (row 7)", "QUOTED", "supplies",
      [ev(CD, 123, "`TailLightsLensFlare` (RVehicleBatmobileBase) | ObjectProperty | Batmobile.Batmobile_brakelights_alwaysOn (LensFlare)",
          ["Batmobile_brakelights_alwaysOn"])],
      "BmAK LightColor 255,38,0,0 B 1.0 R 150.0; donor row 7 on `sportsmuscle_signal_r_r`",
      "the always-on tail flare is decoded as `Batmobile.Batmobile_brakelights_alwaysOn`; with "
      "`Batmobile_brakelights` (line 122) these are the two brake-lamp flare objects the rig carries",
      ""),

    R("T-L17", "T-14", "`BattleModeSpotLight` -> the graph's unreferenced `Front_Secondary_Head`",
      "QUOTED", "supplies",
      [ev(CD, 198, "`PSMLightTemplate` (RVehicleBatmobileBase) | ObjectProperty | Arch.BatmobilePSM_Light (RDeferred_SpotLight_Shadowed_Spawnable)",
          ["Arch.BatmobilePSM_Light"])],
      "BmAK LightColor 255,255,255,0 B 0.0 cone 5.0/15.0 R 4500.0; graph object hash 3189390601, "
      "no module row references it",
      "the battle spotlight's own carrier is a class default: `PSMLightTemplate` = "
      "`Arch.BatmobilePSM_Light`, a `RDeferred_SpotLight_Shadowed_Spawnable`. That is the object the "
      "row's battle spot corresponds to on the BmAK side - the module row the row proposes is a "
      "JC3-side question this card does not read",
      ""),

    R("T-L18", "T-14", "`HeadLight1` battle mode -> custom `headlight_battle_left`", "QUOTED", "supplies",
      [ev(CD, 264, "`HeadLightsColourBattle` (RVehicleBatmobileBase) | StructProperty | raw 0000c84100000000000000000000803f = 4 floats ['25.0', '0.0', '0.0', '1.0']",
          ["'25.0', '0.0', '0.0', '1.0'"])],
      "BmAK LightColor 255,0,0,0 B 5.0 cone 10.0/35.0 R 1024.0",
      "the battle headlight colour is a class default: 4 floats [25.0, 0.0, 0.0, 1.0] - red with an "
      "intensity above 1, so it is not the same number as the row's 255,0,0 even though both name "
      "red. The pursuit vector beside it is [1,1,1,1] (line 263)",
      ""),

    R("T-L19", "T-14", "`HeadLight2` battle mode -> custom `headlight_battle_right`", "QUOTED", "supplies",
      [ev(CD, 264, "`HeadLightsColourBattle` (RVehicleBatmobileBase) | StructProperty | raw 0000c84100000000000000000000803f = 4 floats ['25.0', '0.0', '0.0', '1.0']",
          ["'25.0', '0.0', '0.0', '1.0'"])],
      "BmAK LightColor 255,0,0,0 B 5.0 cone 10.0/35.0 R 1024.0",
      "same vector as T-L18: [25.0, 0.0, 0.0, 1.0]",
      ""),

    R("T-L20", "T-14", "`LWheelLight` battle mode -> custom `sportsmuscle_wheel_f_l_arch_battle`",
      "OPEN", "adjacent",
      [ev(CD, 264, "`HeadLightsColourBattle` (RVehicleBatmobileBase) | StructProperty | raw 0000c84100000000000000000000803f = 4 floats ['25.0', '0.0', '0.0', '1.0']",
          ["'25.0', '0.0', '0.0', '1.0'"])],
      "BmAK LightColor 255,0,0,0 B 0.0 cone 5.0/15.0 R 2048.0",
      "only the car-level battle colour vector is decoded; the wheel-arch battle lamp is a separate "
      "light entry with no class-default counterpart",
      "G2-33 §7 recipe (`Research/JC3Grab/LIGHT_SYSTEM.md`) plus the row's own light entry"),

    R("T-L21", "T-14", "`BattleModeSpotLight` forensics rig (omitted)", "OPEN", "n/a",
      [], "out: the `VEHLT_ForensicsLight` rig is a scanner mode",
      "no named card reads the forensics rig; the row's proof is `Research/BatmobileGrab/LIGHTS.json` "
      "plus `Research/JC3Grab/LIGHT_SYSTEM.md` §8",
      "`Research/BatmobileGrab/LIGHTS.md` (`problems`) - not in this card set"),

    R("T-L22", "T-14", "`HeadLight1` forensics rig (omitted)", "OPEN", "n/a",
      [], "out: forensics rig", "as T-L21", "`Research/BatmobileGrab/LIGHTS.md` - not in this card set"),

    R("T-L23", "T-14", "`HeadLight2` forensics rig (omitted)", "OPEN", "n/a",
      [], "out: forensics rig", "as T-L21", "`Research/BatmobileGrab/LIGHTS.md` - not in this card set"),

    R("T-L24", "T-14", "`Dashboard_Light` -> `Dash_Light` (row 2)", "OPEN", "n/a",
      [], "BmAK LightColor 172,245,255,0 B 5.0 cone 20.0/45.0 R 80.0; donor row 2",
      "no `Dash_Light` or dashboard-light member exists in either class-default stream, and no named "
      "card decodes the JC3 preset; the row's donor row 2 is a light-module entry",
      "the donor module's row 2 (`Working/Lights/*`, T14_LIGHTS.md §3)"),

    R("T-L25", "T-14", "`HeadLight1a` LensFlareComponent (rides T-L8)", "OPEN", "adjacent",
      [ev(CD, 122, "`BrakeLightsLensFlare` (RVehicleBatmobileBase) | ObjectProperty | Batmobile.Batmobile_brakelights (LensFlare)",
          ["Batmobile.Batmobile_brakelights"])],
      "no light component; flare rides the lamp row",
      "the only LensFlare class defaults decoded are the two brake-lamp ones (lines 122-123); the "
      "headlight flare objects the row cites are not class defaults, so their `SourceColor` is still "
      "only in the archetype. JC3 has no flare member (G1-17), which this card does not change",
      "the archetype's `LensFlareComponent` exports (REMAINDER §2 lists 24 of them by export, "
      "payloads terminator-only)"),

    R("T-L26", "T-14", "`HeadLight2a` LensFlareComponent (rides T-L9)", "OPEN", "adjacent",
      [ev(RM, 1127, "| 331 | `LensFlareComponent` | `LensFlareComponent` | 95/97 |", ["LensFlareComponent"])],
      "no light component; flare rides the lamp row",
      "the vehicle package's 24 `LensFlareComponent` objects decode as 95-105-byte payloads that end "
      "on the 2-byte terminator - no property value is read from them here",
      "the archetype `LensFlareComponent` payloads (not decoded: REMAINDER §2 treats them as "
      "terminator-only)"),

    R("T-L27", "T-14", "`HeadLight1b` LensFlareComponent (rides T-L8)", "OPEN", "adjacent",
      [ev(RM, 1127, "| 331 | `LensFlareComponent` | `LensFlareComponent` | 95/97 |", ["LensFlareComponent"])],
      "no light component; flare rides the lamp row", "as T-L26",
      "the archetype `LensFlareComponent` payloads"),

    R("T-L28", "T-14", "`HeadLight1c` (socket absent)", "OPEN", "n/a",
      [], "out: socket not in the shipped mesh",
      "no named card covers the socket list of the shipped mesh; the row's proof is "
      "`Research/BatmobileGrab/LIGHTS.json` (`problems`)",
      "`Research/BatmobileGrab/LIGHTS.md` - not in this card set"),

    R("T-L29", "T-14", "`HeadLight2b` LensFlareComponent (rides T-L9)", "OPEN", "adjacent",
      [ev(RM, 1127, "| 331 | `LensFlareComponent` | `LensFlareComponent` | 95/97 |", ["LensFlareComponent"])],
      "no light component; flare rides the lamp row", "as T-L26",
      "the archetype `LensFlareComponent` payloads"),

    R("T-L30", "T-14", "`HeadLight2c` (socket absent)", "OPEN", "n/a",
      [], "out: socket not in the shipped mesh", "as T-L28",
      "`Research/BatmobileGrab/LIGHTS.md` - not in this card set"),

    R("T-L31", "T-14", "`RWheelLight_top` flare (rides T-L14)", "OPEN", "adjacent",
      [ev(CD, 123, "`TailLightsLensFlare` (RVehicleBatmobileBase) | ObjectProperty | Batmobile.Batmobile_brakelights_alwaysOn (LensFlare)",
          ["Batmobile_brakelights_alwaysOn"])],
      "no light component; custom preset-0 lamp carries it",
      "the decoded flare objects are the brake ones only; the wheel-arch flare has none",
      "the archetype `LensFlareComponent` payloads plus G2-33 §7"),

    R("T-L32", "T-14", "`RWheelLight_bottom` flare (rides T-L14)", "OPEN", "adjacent",
      [ev(CD, 123, "`TailLightsLensFlare` (RVehicleBatmobileBase) | ObjectProperty | Batmobile.Batmobile_brakelights_alwaysOn (LensFlare)",
          ["Batmobile_brakelights_alwaysOn"])],
      "no light component; custom preset-0 lamp carries it", "as T-L31",
      "the archetype `LensFlareComponent` payloads plus G2-33 §7"),

    R("T-L33", "T-14", "`LWheelLight_top` flare (rides T-L13)", "OPEN", "adjacent",
      [ev(CD, 123, "`TailLightsLensFlare` (RVehicleBatmobileBase) | ObjectProperty | Batmobile.Batmobile_brakelights_alwaysOn (LensFlare)",
          ["Batmobile_brakelights_alwaysOn"])],
      "no light component; custom preset-0 lamp carries it", "as T-L31",
      "the archetype `LensFlareComponent` payloads plus G2-33 §7"),

    R("T-L34", "T-14", "`LWheelLight_bottom` flare (rides T-L13)", "OPEN", "adjacent",
      [ev(CD, 123, "`TailLightsLensFlare` (RVehicleBatmobileBase) | ObjectProperty | Batmobile.Batmobile_brakelights_alwaysOn (LensFlare)",
          ["Batmobile_brakelights_alwaysOn"])],
      "no light component; custom preset-0 lamp carries it", "as T-L31",
      "the archetype `LensFlareComponent` payloads plus G2-33 §7"),

    R("T-L35", "T-14", "`BootLight` -> custom `boot_light` (preset 0)", "OPEN", "n/a",
      [], "BmAK LightColor 152,255,225,0 B 5.0 cone 50.0/60.0 R 400.0",
      "no boot-light member exists in either class-default stream and no named card decodes the JC3 "
      "preset namespace",
      "G2-33 §7 recipe (`Research/JC3Grab/LIGHT_SYSTEM.md`) plus the row's own light entry",
      absent=["BootLight"]),

    # ------------------------------------------------------------------ T-7
    R("T-WP1", "T-7", "heavy cannon -> `w602_mediumtank_canon` on `main_weapon`", "OPEN", "n/a",
      [], "decoded tune rows, fire_rate 1.75 -> 2 s, velocity 500 -> 400",
      "the named cards hold no weapon tune: they cover the packages' class defaults, the untagged "
      "objects and the decoded assets, not the JC3 weapon tables",
      "`Research/JC3Grab/WEAPONS.md` / `WEAPON_WIRING.md` (T-11, B-06) - not in this card set"),

    R("T-WP2", "T-7", "Vulcan -> `w603_mediumtank_mgun` on `id:00568A74`", "OPEN", "n/a",
      [], "fire_rate 0.1 -> 0.138 s",
      "as T-WP1: no weapon tune in the named cards",
      "`Research/JC3Grab/WEAPONS.md` (T-11, B-06)"),

    R("T-WP3", "T-7", "missiles -> the donor's own `w618_sportsmuscle_missile`", "OPEN", "n/a",
      [], "4 fire points, blast 1100 in 8 m",
      "as T-WP1: no weapon tune in the named cards. The BmAK missile *components* are in the "
      "packages and are decoded as projectile objects (REMAINDER §2, `RocketTrail` x 8, "
      "`ImpulseComponent0` x 6), but no fire-point or blast value",
      "`Research/JC3Grab/WEAPONS.md` (T-11, B-06)"),

    R("T-WP4", "T-7", "EMP missile: launcher + disable", "OPEN", "negative",
      [ev(RM, 1778, "| 7319 | `DisabledByEmpFx` | `ComponentProperty` | 34", ["`DisabledByEmpFx`"]),
       ev(RM, 1848, "| 7497 | `SetDisabledByEMP` | `Function` | 209", ["`SetDisabledByEMP`"])],
      "blocked: JC3 has no disable/duration member for the Immobilizer",
      "the BmAK side of the disable is now named: a `SetDisabledByEMP` function and a "
      "`DisabledByEmpFx` component default on `BmScript.RVehicleBatmobile`. Both are descriptors - "
      "REMAINDER §3a's oracle shows the 97 property payloads are fixed-size descriptors and three "
      "same-class ones are byte-identical, so no value is read, and §4 UNKNOWN 1 puts the values in "
      "`BmScript`, which is not shipped. The JC3 disable member is untouched",
      "nothing in the packages: the disable is BmScript-side, and §4 UNKNOWN 1 records that package "
      "as not on disk"),

    R("T-WP5", "T-7", "EMP burst -> entity-level `CForcePulse` copy", "OPEN", "adjacent",
      [ev(RM, 1208, "| 5105 | `RB_RadialImpulseComponent` | `ImpulseComponent0` | 36/38", ["ImpulseComponent0"])],
      "blocked: the object can be copied but nothing fires it",
      "the Batmobile's own package carries one radial impulse component (`RB_RadialImpulseComponent` "
      "`ImpulseComponent0`, 36/38 bytes, terminator-closed). It is the BmAK physical half of the "
      "burst; it says nothing about what fires the JC3 pulse",
      "G2-16/G2-17 (`Research/JC3Grab/FORCEPULSE.md`) for the JC3 pulse and its trigger"),

    R("T-WP6", "T-7", "winch -> named omission (no functional winch class)", "QUOTED", "agrees",
      [ev(RM, 1209, "| 5268 | `RSimpleRopeComponent` | `RopeComponent0` | 44/46", ["RopeComponent0"]),
       ev(RM, 1210, "| 5269 | `RSimpleRopeComponent` | `RopeComponent1` | 52/54", ["RopeComponent1"])],
      "proven absence in JC3; BmAK ships rope/winch geometry (10 part names)",
      "the geometry half is decoded: two `RSimpleRopeComponent` objects (`RopeComponent0` 44/46 and "
      "`RopeComponent1` 52/54) in `Playable_Batmobile_SF`, both ending on the terminator, so they "
      "carry no pull parameter. That matches the row's 'geometry, no member' and adds the object "
      "count",
      ""),

    R("T-WP7", "T-7", "hacker -> named omission (no allegiance-switch class)", "QUOTED", "agrees",
      [ev(RM, 1202, "| 5010 | `ParticleSystemComponent` | `DroneHackerEffect0` | 36/38", ["DroneHackerEffect0"]),
       ev(RM, 1207, "| 5015 | `ParticleSystemComponent` | `DroneHackerEffect5` | 36/38", ["DroneHackerEffect5"])],
      "BmAK cites `Particles.DroneHacker_Beam` etc.; JC3 has no allegiance-switch class",
      "six `DroneHackerEffect0..5` particle components are present in the vehicle package (36/38 "
      "bytes each), consistent with the row's effect refs; still no class that switches allegiance",
      ""),

    R("T-WP8", "T-7", "sonar -> named omission (no sonar class)", "OPEN", "adjacent",
      [ev(AB, 172, "| `BML_Sonar` | `Engine` |", ["355830", "7"])],
      "no sonar class in the 103-class census; `CForcePulse` is the shockwave half",
      "the audio half of the sonar is available: bank `BML_Sonar` is a present `AkBank` export in "
      "BmGame (355,830 B, 7 events), referenced by 18 event rows. That is an asset, not the sonar "
      "class the row lacks",
      "`Research/JC3Grab/ENTITIES.md` (103-class census) for the class absence"),

    R("T-WP9", "T-7", "tracker -> named omission (no tracker class)", "OPEN", "n/a",
      [], "no tracker class (the only 'track' is `CMusicTrack`)",
      "nothing in the named cards covers the JC3 class census or the launch socket",
      "`Research/JC3Grab/ENTITIES.md`; the socket question is T-12's"),

    R("T-WP10", "T-7", "riot-suppressor mode -> named omission", "OPEN", "adjacent",
      [ev(RM, 1199, "| 5007 | `ParticleSystemComponent` | `ChargeParticle0` | 60/62", ["ChargeParticle0"]),
       ev(RM, 1200, "| 5008 | `ParticleSystemComponent` | `BeamElectricityComp0` | 36/38", ["BeamElectricityComp0"])],
      "no non-lethal flag/damage type/mode in the JC3 vocabulary",
      "the effect components behind the riot/taser half decode (`ChargeParticle0` 60/62, "
      "`BeamElectricityComp0` 36/38, `FireElectricityComp0` 36/38); no flag or mode exists in the "
      "class-default streams (`RiotSuppressor` absent), so the non-lethal mode is still a named "
      "omission on both sides",
      "`Research/JC3Grab/VOCABULARY.md` (the row's own proof)",
      absent=["RiotSuppressor"]),

    R("T-WP11", "T-7", "afterburner gadget mesh", "QUOTED", "agrees",
      [ev(RM, 1211, "| 5290 | `SkeletalMeshComponent` | `GadgetMesh` | 28/42", ["GadgetMesh"])],
      "the gadget is JC3 nitro (live since test-091); `RBatmobileBooster` 4 instances, 8 fields, "
      "'the gadget mesh only'",
      "ten `GadgetMesh` skeletal mesh components decode in the vehicle package (28-50 bytes, all "
      "terminator_early with 12 asset bytes behind the tags), so the row's 'mesh only' reading holds: "
      "the gadget is geometry, not a boost member",
      ""),

    R("T-WP12", "T-7", "HUD weapon slots (`HudModuleBatmobile`)", "OPEN", "n/a",
      [], "2 clips, 5 mapped elements, no heat",
      "the named cards hold no SWF/HUD decode; the row's facts are T-19's",
      "`Research/JC3Grab/JC3_HUD_WEAPONS.md` (T-19) - not in this card set"),

    R("T-WP13", "T-7", "driver weapon slots (all 11 weapons)", "OPEN", "n/a",
      [], "blocked: at most 2 driver slots, no active-slot index",
      "no named card decodes driver slots or weapon groups; that is G2-11's read of the 232 `.epe` "
      "graphs",
      "`Research/JC3Grab/WEAPON_WIRING.md` / G2-11 - not in this card set"),

    R("T-WP14", "T-7", "riot mode toggle (decision record)", "OPEN", "adjacent",
      [ev(RM, 1199, "| 5007 | `ParticleSystemComponent` | `ChargeParticle0` | 60/62", ["ChargeParticle0"])],
      "out: D-3 resolved - accept JC3 lethality, no toggle",
      "as T-WP10: no `RiotSuppressor` member exists in the class-default streams, so there is no "
      "BmAK default a toggle could read; the decision record is untouched",
      "the decision record itself (`Working/Translation/T7_WEAPONS.md`)",
      absent=["RiotSuppressor"]),

    # ------------------------------------------------------------------ T-20
    R("T-WLD1", "T-20", "Rebel Drop item record", "OPEN", "n/a",
      [], "leaf `v0300_..._batmobile`, `hash_jenkins` 443190071",
      "the named cards are BmAK-package and JC3-donor decodes; none reads `profile/item.onlinec`",
      "G2-26 (`Research/JC3Grab/...` item schema) and B-13's write"),

    R("T-WLD2", "T-20", "unlock link (`ItemReward` on task 1361701860)", "OPEN", "n/a",
      [], "`ItemReward` link, `permanent` 1, `quantity` 1",
      "no named card reads `task.onlinec`", "G2-26 / `Working/Translation/T15_WORLD.md`"),

    R("T-WLD3", "T-20", "drop-item UI profile", "OPEN", "n/a",
      [], "copy the donor profile: Type 1, UIType 3, UIFlag 5, UIDisplayOrder 12, RebelDropTimer 1800",
      "no named card reads the item profile; the 45/45 fleet census is the T-20 document's own input",
      "`Working/Translation/T15_WORLD.md` (the row's own source)"),

    R("T-WLD4", "T-20", "display name (`profile/online.stringlookup` pair)", "OPEN", "negative",
      [ev(DD1, 28, "| `.stringlookup` | 1 | 2210 | 1 | 0 | 0 |", ["2210"])],
      "carried: key `HashJenkins(leaf)` = 1621485476 is present 11/11 for the shipped `_debug` "
      "leaf in bm-013's drop (text BATMOBILE); 443190071 is the unshipped `..._batmobile` leaf",
      "the store's container is closed (1 file, 2,210 B, grade FULL) and the write side exists: "
      "`jc3strings_write` added exactly 22 pairs (14,712 -> 14,734) in bm-013, nothing else changed",
      "carrying bm-013's drop into the RC, then Q-1's runtime resolution"),

    R("T-WLD5", "T-20", "vehicle icon `textures/ui/vehicle_icons/<leaf>.ddsc`", "OPEN", "adjacent",
      [ev(DD2, 52, "| 77 | 66 | 68988624 | [16] | 594 | 44 | 22 |", ["[16]"])],
      "copy the donor's 18,688 B icon under the new leaf name",
      "the `.ddsc` container is decoded here (format 77 => 16-byte 4x4 blocks; the mip chain tiles "
      "the payload to EOF on 116/116 files). That is the reason a byte-identical copy needs no "
      "encoder, but the icon file itself is outside the donor entity and no card reads it",
      "the icon directory copy (G2-32) - `Working/Translation/T15_WORLD.md`"),

    R("T-WLD6", "T-20", "description pair (`<leaf>_desc`)", "OPEN", "negative",
      [ev(DD1, 28, "| `.stringlookup` | 1 | 2210 | 1 | 0 | 0 |", ["2210"])],
      "carried: `HashJenkins(\"..._debug_desc\")` = 4081821928 is present 11/11 in bm-013's "
      "drop with the Batmobile blurb; 2073308658 stays the donor's Serpente text",
      "as T-WLD4: the store's bytes are fully accounted and bm-013 writes exactly the two pairs",
      "carrying bm-013's drop into the RC, then Q-1"),

    R("T-WLD7", "T-20", "category captions (`UITypeDescription`, `UIFlagDescription`)", "OPEN", "n/a",
      [], "keep: both hashes resolve 11/11",
      "no named card reads the string store's contents", "`Working/Translation/T15_WORLD.md`"),

    R("T-WLD8", "T-20", "entry points (29 `entry.*` objects)", "OPEN", "n/a",
      [], "T-13's placement: 77/85 objects in the 0.05-0.30 m band",
      "no named card decodes the interaction graph; the placement is T-13's",
      "`Working/Translation/T13_*` / G2-18 - not in this card set"),

    R("T-WLD9", "T-20", "exit points (26 `exit.*` objects)", "OPEN", "n/a",
      [], "same pass; 8 `point.*` nodes",
      "as T-WLD8", "G2-18 §4 - not in this card set"),

    R("T-WLD10", "T-20", "stunt point nodes", "OPEN", "n/a",
      [], "8 `point.*` nodes, 19 objects mapped to a stunt role",
      "as T-WLD8", "G2-18 §3-4 - not in this card set"),

    R("T-WLD11", "T-20", "stunt areas (`StuntAreas`, weld rows)", "OPEN", "negative",
      [ev(DD3, 150, "| `v0300_car_kensington_sportsmuscle_civilian_01.epe` | **FULL** | 109,526 B, 0 unexplained bytes on round trip",
          ["**FULL**", "0 unexplained bytes"]),
       ev(DD1, 30, "| `.epe` | 1 | 109526 | 0 | 1 | 0 |", ["109526"])],
      "re-fit derived: 3 areas, 64 weld rows of which 8 real; 22/22 bound vertices placeable at "
      "0.036-0.105 m on a standing RC2 face (stored points sink 0.19-0.31 m; bbox map floats 0.32-0.49 m)",
      "the entity byte stream is closed (G3-19: 2,189 padding + 104 float ULP bytes, 0 unexplained; "
      "109,526 B) and the deform list already exists - 135 `DeformPoints` bound by the 3 areas. The "
      "missing piece is the re-fit write (22 `start_transform` + `vertices3D_local` pairs) and a "
      "third column (indices 135+) for full width; the derived table is "
      "`tmp/freebuff/reports/stunt-areas-deform-points.md` §4.3",
      "the 22-point write into `sportsmuscle_vehicle_deform.vmodc` + `sportsmuscle_stunt_areas.vmodc`, "
      "then `t_wld11b.py --check`"),

    R("T-WLD12", "T-20", "`rigid_body.mass` 975 -> 6000", "OPEN", "negative",
      [ev(DD1, 50, "| `hknpShapeMassProperties` | 56 | NAMED-ONLY | nothing | none |",
          ["no mass, inertia or centre of mass is read from it"]),
       ev(CD, 158, "`ChassisMass` (SVehicle) | FloatProperty | 210.0", ["210.0"])],
      "mass 975 -> 6000 = 6.154x the donor; the mass unit is UNKNOWN",
      "confirmed unknowable from the physics file on this evidence: the 56 "
      "`hknpShapeMassProperties` objects are NAMED-ONLY and no mass is read from them. On the BmAK "
      "side the only absolute mass member the class defaults carry is `ChassisMass` 210.0 - a "
      "different quantity from a rigid-body mass",
      "`Research/JC3Grab/PHYSICS_ROLES2/3.md` (the per-shape mass block) plus a runtime weigh-in"),

    R("T-WLD13", "T-20", "`WaterInteraction.will_sink` + `Buoyancy`", "OPEN", "n/a",
      [], "will_sink 1, buoyancy 2.0, drag 100.0",
      "no water/buoyancy member exists in the named cards' scope (BmAK class defaults carry none, "
      "JC3 decode cards read the mesh/physics/effect files only)",
      "`vehicle_common.vmodc` (the row's own source, R7-protected)"),

    R("T-WLD14", "T-20", "water kill/stall constants (shared `vehicle_common.vmodc`)", "OPEN", "adjacent",
      [ev(DD1, 22, "| `.vmodc` | 31 | 195998 | 31 | 0 | 0 | jc3adf.Adf + walk",
          ["31", "195998"])],
      "10/20/20/50 ms entry constants, `engine_shut_down_delay_s` 30, 0 overrides",
      "the shared module's family decodes FULL (31 `.vmodc`, 195,998 B, header total == length and "
      "allocations tile on every one), so the row's constants are read from a fully accounted file "
      "- but the values themselves come from `vehicle_common`, not from any named card",
      "`editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` (the row's own source)"),

    R("T-WLD15", "T-20", "tether (`vehicle`-side member)", "OPEN", "n/a",
      [], "out: no vehicle-side member; 335 tether paths are dialogue/UI",
      "no named card decodes the tether/grapnel members",
      "`Research/JC3Grab/TETHER.md` (`winch` = []) - not in this card set"),

    R("T-WLD16", "T-20", "cargo bay capacity", "OPEN", "n/a",
      [], "12 `CVehicleCargoBay` objects; 6000 kg is 15.0/6.0/40.0 % of them",
      "no named card reads `CVehicleCargoBay`", "G2-34 - not in this card set"),

    R("T-WLD17", "T-20", "helicopter airlift", "OPEN", "n/a",
      [], "out: 0 of 23 helicopters carries a `CVehicleCargoBay`",
      "no named card reads the helicopter bays", "G2-34 - not in this card set"),

    R("T-WLD18", "T-20", "traffic record (`settings/spawn_vehicle_defs.bin`)", "OPEN", "n/a",
      [], "0 records for the new leaf; D-6 standalone adds nothing",
      "no named card reads the spawn table", "G2-29 - not in this card set"),

    R("T-WLD19", "T-20", "the donor's own traffic record", "OPEN", "n/a",
      [], "donor record at 23240, 13 tags, 1 of 41 selectors",
      "as T-WLD18", "G2-29 - not in this card set"),

    # ------------------------------------------------------------------ T-15
    R("T-MD1", "T-15", "afterburner -> `arcade.nitro_boost`", "QUOTED", "supplies",
      [ev(CD, 265, "`FakeExtraSpeedMax` (RVehicleBatmobileBase) | FloatProperty | 3500.0", ["3500.0"]),
       ev(CD, 192, "`SideExhaustBurstEffect` (RVehicleBatmobileBase) | ObjectProperty | Exhaust.Batmobile_Side_Exhaust (ParticleSystem)",
          ["Batmobile_Side_Exhaust"])],
      "`Batmobile_Booster` gadget; JC3 nitro carries torque x2, grip x2, push 15000, +40 km/h",
      "the BmAK afterburner's own members decode: `FakeExtraSpeedMax` 3500.0 (with "
      "`FakeExtaSpeedAccel` 600.0 / `FakeExtaSpeedDecel` 2000.0 at lines 266-268) and the side-exhaust "
      "effect object. These are the additive-speed members T-B2 already uses; the JC3 nitro block "
      "itself is unchanged",
      ""),

    R("T-MD2", "T-15", "Immobilizer (EMP missile)", "OPEN", "negative",
      [ev(RM, 1848, "| 7497 | `SetDisabledByEMP` | `Function` | 209", ["`SetDisabledByEMP`"]),
       ev(RM, 1778, "| 7319 | `DisabledByEmpFx` | `ComponentProperty` | 34", ["`DisabledByEmpFx`"])],
      "blocked: the launcher can be mounted, the disable has no JC3 member",
      "the disable is a BmScript function (`SetDisabledByEMP`) with a component default "
      "(`DisabledByEmpFx`) - both names decoded, no values (REMAINDER §3a: the payloads are "
      "descriptors). So there is no BmAK class-default number a JC3 member could carry, and the "
      "row's block stands",
      "G2-16/G2-17 for the JC3 pulse; the disable behaviour is BmScript (not on disk)"),

    R("T-MD3", "T-15", "ram immunity", "QUOTED", "supplies",
      [ev(CD, 206, "`RamDamageType` (RVehicleBatmobileBase) | ClassProperty | RDmgType_Barge (None)", ["RDmgType_Barge"]),
       ev(CD, 205, "`CrushDamageType` (RVehicleBatmobileBase) | ClassProperty | Core.DmgType_Crushed (Class)",
          ["Core.DmgType_Crushed"])],
      "BmAK ramming never damages the Batmobile; JC3 `impact_damage_factor` 0",
      "BmAK gives the car two damage classes of its own: `RamDamageType` = `RDmgType_Barge` and "
      "`CrushDamageType` = `Core.DmgType_Crushed`. What the engine does with them is not in the "
      "bytes; the JC3 switch (T-DM8) is unchanged",
      ""),

    R("T-MD4", "T-15", "`StandardTorqueVSpeedCurve` / `BoostTorqueVSpeedCurve`", "OPEN", "negative",
      [ev(RM, 1895, "| 169320 | `SimulationModel` | `RVehicleSimBatmobile` | 4920", ["StructProperty@0x1dc=None"])],
      "6-point and 7-point curves on `RVehicleSimBatmobile`, identical in all four packages",
      "the class-default `SimulationModel` object (4,920 B, closes on the terminator) carries every "
      "one of its `StructProperty` curve slots as `None` (@0x104, 0x118, 0x194, 0x1a8, 0x1dc, 0x1f0, "
      "0x204, 0x218, 0x22c, 0x240, 0x254, 0x268, 0xc8), and the float values it does carry are "
      "offsets without member names. So the curves the row cites are not class defaults - they are "
      "archetype values, and no `StandardTorqueVSpeedCurve`/`BoostTorqueVSpeedCurve` name exists in "
      "either stream",
      "the archetype `SimulationModel` tag stream (`objects.jsonl` / `CHAIN.json`)",
      absent=["StandardTorqueVSpeedCurve", "BoostTorqueVSpeedCurve"]),

    R("T-MD5", "T-15", "`BattleModeVSpeedCurve`", "OPEN", "negative",
      [ev(RM, 1895, "| 169320 | `SimulationModel` | `RVehicleSimBatmobile` | 4920", ["StructProperty@0x1dc=None"])],
      "3 points: 0 -> 60, 600 -> 40, 1200 -> 30",
      "same evidence as T-MD4: every curve slot in the class-default `SimulationModel` is `None`, and "
      "`BattleModeVSpeedCurve` is not a member name in either class-default stream",
      "the archetype `SimulationModel` tag stream",
      absent=["BattleModeVSpeedCurve"]),

    R("T-MD6", "T-15", "`TurningModeMaxSpeed` 600 cm/s", "OPEN", "negative",
      [], "600 cm/s = 21.6 km/h with `BattleModeThrottleSpeed` 10",
      "no `TurningModeMaxSpeed` (or any `TurningMode*`) tag exists in either class-default stream, so "
      "the value is not a class default and is not re-derived here",
      "the archetype `RVehicleSimBatmobile` tags in `objects.jsonl`",
      absent=["TurningModeMaxSpeed"]),

    R("T-MD7", "T-15", "battle drive/slip factors", "OPEN", "negative",
      [], "`BattleModeDriveForceFactor` 500, `BattleModeLatSlipScale` 0.75, `LongSlipScale` 1.25, "
      "`SteerAngleFactor` 1, `TrailingSteerFactorMoving` -0.25, `DrivingForceZOffset` 20 cm",
      "none of the six is a class-default member: `BattleModeDriveForceFactor`, "
      "`BattleModeLatSlipScale`, `BattleModeLongSlipScale`, `BattleModeSteerAngleFactor` and "
      "`BattleModeTrailingSteerFactorMoving` are all absent from both streams (only the mode box, "
      "the yaw offset and the two transformation names are carried there)",
      "the archetype `RVehicleSimBatmobile` tags in `objects.jsonl`",
      absent=["BattleModeDriveForceFactor", "BattleModeLatSlip", "BattleModeLongSlip",
              "BattleModeSteerAngleFactor", "BattleModeTrailingSteerFactor"]),

    R("T-MD8", "T-15", "turn on the spot", "OPEN", "negative",
      [], "`TurnOnSpotFrontTorqueFactor` 0.8, `RearTorqueFactor` -0.8, `ModeEngineBrakingFactor` 2, "
      "`BattleModeTurnOnSpotTorqueFactor` 0.333333",
      "no `TurnOnSpot*` tag exists in either class-default stream - consistent with G2-21's finding "
      "that the pivot has no data carrier, but not a re-decode of those four numbers",
      "`Research/JC3Grab/TANKTURN.md` (G2-21) - not in this card set",
      absent=["TurnOnSpot"]),

    R("T-MD9", "T-15", "turret weapons", "OPEN", "n/a",
      [], "T-12's part angles carry the aim; T-11's clones carry the weapons",
      "no named card decodes the turret parts or the weapon clones",
      "T-12 / T-11 rows - not in this card set"),

    R("T-MD10", "T-15", "`ArmourModeDamageReduction`", "QUOTED", "differs",
      [ev(CD, 242, "`ArmourModeDamageReduction` (RVehicleBatmobileBase) | IntProperty | 20", ["20"])],
      "0, 'identical on the three packages that serialise it (Funhouse, MK2, V2)'",
      "the class default reads 20, not 0. The row's 0 is an archetype value from three other "
      "packages, so the two readings are of different objects with the same member name; neither "
      "refutes the other, and the class default is the one decoded here. A read of a fourth "
      "archetype, or of the four-car archetype set, would settle which object the translation should "
      "follow - that is not a decode this card performs",
      ""),

    R("T-MD11", "T-15", "battle camera FOV", "OPEN", "negative",
      [], "`BattleModeCamFOV` 60, `BattleModeWinchCamFOV` 60, `AntiPersonelBattleModeCamFOV` 40",
      "no `BattleModeCamFOV` (or `BattleModeCam*`) member exists in either class-default stream; the "
      "camera values live in the per-entity `.ctune`, which no named card reads",
      "the `.ctune` read (T-CAM9/T-CAM10, `Research/JC3Grab/CAMERA.md`) - not in this card set",
      absent=["BattleModeCamFOV"]),

    R("T-MD12", "T-15", "battle lights", "QUOTED", "supplies",
      [ev(CD, 264, "`HeadLightsColourBattle` (RVehicleBatmobileBase) | StructProperty | raw 0000c84100000000000000000000803f = 4 floats ['25.0', '0.0', '0.0', '1.0']",
          ["'25.0', '0.0', '0.0', '1.0'"]),
       ev(CD, 198, "`PSMLightTemplate` (RVehicleBatmobileBase) | ObjectProperty | Arch.BatmobilePSM_Light (RDeferred_SpotLight_Shadowed_Spawnable)",
          ["Arch.BatmobilePSM_Light"])],
      "4 `VEHLT_BattleModeLight` entries (T-L17-T-L20); the fleet's 9 behaviours have no battle value",
      "the battle light is a class-default pair: a colour vector [25.0, 0.0, 0.0, 1.0] and a spawned "
      "deferred spotlight template (`Arch.BatmobilePSM_Light`). Both are mode-level members, so the "
      "row's 'one behaviour, no mode' reading is what the data shows - the battle state is a colour "
      "and a template, not a light behaviour",
      ""),

    R("T-MD13", "T-15", "transformation stance", "QUOTED", "differs",
      [ev(CD, 243, "`BattleModeTransformationAnimName` (RVehicleBatmobileBase) | NameProperty | 'Batmobile_V2_Tank_Spread_Open_Game'",
          ["Batmobile_V2_Tank_Spread_Open_Game"]),
       ev(CD, 244, "`PursuitModeTransformationAnimName` (RVehicleBatmobileBase) | NameProperty | 'Batmobile_V2_Tank_Spread_Close_Game'",
          ["Batmobile_V2_Tank_Spread_Close_Game"])],
      "`TransformationTurnTorqueFactor` 3000, `TransformationTurnDecelTorqueFactor` 24000, "
      "`TransformationAnimNode` not serialised; '0 `TransformationAnimNode` values in the files'",
      "two transformation animation names ARE serialised as class defaults: "
      "`Batmobile_V2_Tank_Spread_Open_Game` and `Batmobile_V2_Tank_Spread_Close_Game`. The row's "
      "claim about `TransformationAnimNode` stands (that member name is in neither stream), but the "
      "animation itself is named - so 'no transformation animation exists' would overstate it. The "
      "two torque factors the row cites are not class defaults",
      "",
      absent=["TransformationAnimNode"]),

    R("T-MD14", "T-15", "battle audio (mode-switch sting)", "QUOTED", "different-member",
      [ev(CD, 199, "`Transform_In_Bed` (RVehicleBatmobileBase) | ObjectProperty | Ww_BML_Batmobile.Play_BattleMode_In_Bed (AkEvent)",
          ["Play_BattleMode_In_Bed"])],
      "`TransformationReverseDirectionIntoPursuitModeSound` V2 62 / MK2 60 / Joker 191 / Funhouse 60 "
      "and `...IntoBattleModeSound` V2 47 / MK2 45 / Joker 176 / Funhouse 45",
      "the class defaults carry a different set of four transform events: `Transform_In_Bed`, "
      "`Transform_In_Reverse_Bed`, `Transform_Out_Bed`, `Transform_Out_Reverse_Bed` (lines 199-202), "
      "all AkEvents in `Ww_BML_Batmobile` - the `BML_Batmobile` bank that AUDIO_BANKS finds present "
      "(2,268,588 B, 53 events). So the bank exists and the events are named; the row's cited "
      "`*IntoPursuitModeSound` names are not class defaults",
      ""),

    R("T-MD15", "T-15", "the hybrid itself (D-2)", "OPEN", "n/a",
      [], "one entity, one Rebel Drop entry; B-12 skipped",
      "a decision row: no card decodes a hybrid, and none is expected to. The named cards supply the "
      "two modes' inputs (T-MD10/T-MD12/T-MD13), not the choice",
      "the decision record itself (D-2, `MODDING_PLAN.md`)"),
]


# --------------------------------------------------------------------------- loading


def read_text(rel):
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def src_lines(rel):
    return read_text(rel).split("\n")


def norm(s):
    return " ".join(s.split())


def ledger_rows():
    rows = []
    with open(LEDGER, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rec["_line"] = n
            rows.append(rec)
    return rows


# --------------------------------------------------------------------------- checks


def verify(rows, table, quiet=False):
    """Recompute everything from the source bytes. Returns (records, stats). Raises on drift."""
    by_id = {r["id"]: r for r in table}
    if len(by_id) != len(table):
        raise SystemExit("duplicate row id in the table")

    scope = [r for r in rows if r["doc"] in SCOPE]
    got = [r["id"] for r in scope]
    if len(got) != len(set(got)):
        raise SystemExit("duplicate id in the ledger")
    if set(got) != set(by_id):
        missing = sorted(set(got) - set(by_id))
        extra = sorted(set(by_id) - set(got))
        raise SystemExit("row set mismatch: missing %s extra %s" % (missing, extra))
    for rid in got:
        if by_id[rid]["doc"] != next(r["doc"] for r in scope if r["id"] == rid):
            raise SystemExit("doc mismatch for %s" % rid)

    cache = {}
    errors = []
    for rid in got:
        rec = by_id[rid]
        if rec["status"] not in ("QUOTED", "OPEN"):
            errors.append("%s: bad status %r" % (rid, rec["status"]))
        if rec["status"] == "QUOTED" and not rec["evidence"]:
            errors.append("%s: QUOTED with no evidence" % rid)
        if rec["status"] == "OPEN" and not rec["supplier"]:
            errors.append("%s: OPEN with no supplier" % rid)
        for e in rec["evidence"]:
            if e["file"] not in cache:
                cache[e["file"]] = src_lines(e["file"])
            lines = cache[e["file"]]
            if not (1 <= e["line"] <= len(lines)):
                errors.append("%s: %s line %d out of range (%d lines)"
                              % (rid, e["file"], e["line"], len(lines)))
                continue
            text = norm(lines[e["line"] - 1])
            if norm(e["quote"]) not in text:
                errors.append("%s: quote not on %s:%d\n    want: %s\n    have: %s"
                              % (rid, e["file"], e["line"], norm(e["quote"]), text))
            for m in e["must"]:
                if norm(m) not in text:
                    errors.append("%s: value %r not on %s:%d" % (rid, m, e["file"], e["line"]))
        if rec["absent"]:
            body = read_text(rec["absent_file"])
            for name in rec["absent"]:
                if name in body:
                    errors.append("%s: %r IS present in %s (claim of absence fails)"
                                  % (rid, name, rec["absent_file"]))

    if errors:
        raise SystemExit("verification failed:\n  " + "\n  ".join(errors))

    status_counts = {}
    relation_counts = {}
    doc_counts = {}
    card_counts = {}
    records = []
    for ledger_row in scope:
        rec = by_id[ledger_row["id"]]
        status_counts[rec["status"]] = status_counts.get(rec["status"], 0) + 1
        relation_counts[rec["relation"]] = relation_counts.get(rec["relation"], 0) + 1
        doc_counts[rec["doc"]] = doc_counts.get(rec["doc"], 0) + 1
        for e in rec["evidence"]:
            card_counts[e["file"]] = card_counts.get(e["file"], 0) + 1
        records.append({
            "id": rec["id"],
            "doc": rec["doc"],
            "ledger_line": ledger_row["_line"],
            "dispo": ledger_row.get("dispo", ""),
            "section": ledger_row.get("section", ""),
            "member": rec["member"],
            "status": rec["status"],
            "relation": rec["relation"],
            "evidence": rec["evidence"],
            "ledger_value": rec["ledger"],
            "note": rec["note"],
            "supplier": rec["supplier"],
            "absent_claim": rec["absent"],
        })

    stats = {
        "rows_in_scope": len(scope),
        "status_counts": status_counts,
        "relation_counts": relation_counts,
        "doc_counts": doc_counts,
        "card_citation_counts": card_counts,
        "ledger_rows_total": len(rows),
        "excluded_docs": sorted({r["doc"] for r in rows if r["doc"] not in SCOPE}),
        "cards_read": CARDS,
        "cards_unused": [c for c in CARDS if c not in card_counts],
        "citations_verified": sum(len(r["evidence"]) for r in records),
        "absent_claims_verified": sum(len(r["absent_claim"]) for r in records),
    }
    return records, stats


# --------------------------------------------------------------------------- render

HEADER = """# LEDGER_G3C - the remaining ledger rows against what the G3 cards decoded

G3-20c. Generated by `Tools/scripts/ledger_g3c.py --write`; `--check` re-opens every cited
line, re-tests every quoted value and every "not in the class defaults" claim, recomputes the
counts from `Working/Translation/T_ROWS.jsonl` and compares this file byte for byte.

Scope: the {rows} rows of `Working/Translation/T_ROWS.jsonl` in groups **T-20, T-3, T-7, T-15,
T-14**. The other {other} rows are in {excluded} and are not touched by this pass.

Card set: the eleven files this task names -
`Research/BatmobileGrab/{{PACKAGES_G305,REMAINDER,SKINS,COLOUR,AUDIO_BANKS,CLASS_DEFAULTS}}.md`
and `Research/JC3Grab/{{DECODE_DEPTH,DECODE_DEPTH2,DECODE_DEPTH3,COLOUR,COLOUR_NATIVE}}.md`.

The earlier keyword pass (`Working/Translation/LEDGER_G3.md`) is **not** read and **not**
evidence; none of its statuses is reused.

## What a status means

| status | meaning |
|---|---|
| **QUOTED** | one of the named cards decodes the member this row is about. The exact value is quoted with `file:line`, and `relation` says how it stands to the ledger's own number. |
| **OPEN** | no named card answers it. `supplier` names the file or pass that would, and any `evidence` is labelled: **negative** (proves why it is still open), **adjacent** (a neighbouring decoded value that does not answer the row). |

`relation` values: `agrees` (same value), `differs` (same member name, different number),
`different-object` (the card decodes the same member on an explicitly different export),
`different-member` (the card decodes a neighbouring member, not the row's),
`supplies` (the row names the member without a value, or the card answers its question),
`confirms-open` / `n/a`.

No row here is a translation decision: this pass records what the files say, not what to write.

## Status counts

| status | rows |
|---|---:|
{status_table}

| relation | rows |
|---|---:|
{relation_table}

## Per-document counts

| doc | rows |
|---|---:|
{doc_table}

## Which card answers how many rows

| card | citations |
|---|---:|
{card_table}

Cards read but answering nothing in scope: {unused}.

## Row index

| id | doc | dispo | status | relation | evidence |
|---|---|---|---|---|---|
{index_table}

## Rows

{body}
"""


def md_escape(s):
    return s.replace("|", "\\|")


def render(records, stats):
    status_table = "\n".join("| %s | %d |" % (k, v) for k, v in sorted(stats["status_counts"].items()))
    relation_table = "\n".join("| %s | %d |" % (k, v) for k, v in sorted(stats["relation_counts"].items()))
    doc_table = "\n".join("| %s | %d |" % (k, v) for k, v in sorted(stats["doc_counts"].items(),
                                                                    key=lambda kv: (-kv[1], kv[0])))
    card_table = "\n".join("| `%s` | %d |" % (k, v)
                           for k, v in sorted(stats["card_citation_counts"].items(),
                                              key=lambda kv: (-kv[1], kv[0])))
    idx = []
    for r in records:
        first = r["evidence"][0] if r["evidence"] else None
        ev_at = "`%s:%d`" % (first["file"].split("/")[-1], first["line"]) if first else "-"
        idx.append("| `%s` | %s | %s | **%s** | %s | %s |"
                   % (r["id"], r["doc"], r["dispo"], r["status"], r["relation"], ev_at))

    body = []
    last_doc = None
    for r in records:
        if r["doc"] != last_doc:
            body.append("\n### group %s\n" % r["doc"])
            last_doc = r["doc"]
        body.append("#### `%s` - %s\n" % (r["id"], md_escape(r["member"])))
        body.append("- ledger line %d, dispo `%s`; row now: %s"
                    % (r["ledger_line"], r["dispo"], md_escape(r["ledger_value"])))
        body.append("- **%s** (%s)" % (r["status"], r["relation"]))
        if r["evidence"]:
            for e in r["evidence"]:
                body.append("- `%s:%d` - \"%s\""
                            % (e["file"], e["line"], md_escape(norm(e["quote"]))))
        if r["supplier"]:
            body.append("- would be supplied by: %s" % md_escape(r["supplier"]))
        body.append("- %s\n" % md_escape(r["note"]))

    return HEADER.format(
        rows=stats["rows_in_scope"],
        other=stats["ledger_rows_total"] - stats["rows_in_scope"],
        excluded=", ".join(stats["excluded_docs"]),
        status_table=status_table,
        relation_table=relation_table,
        doc_table=doc_table,
        card_table=card_table,
        unused=", ".join("`%s`" % c for c in stats["cards_unused"]) or "none",
        index_table="\n".join(idx),
        body="\n".join(body),
    )


def payload(records, stats):
    return {
        "task": "G3-20c",
        "generated_by": "Tools/scripts/ledger_g3c.py",
        "source_ledger": "Working/Translation/T_ROWS.jsonl",
        "scope_groups": list(SCOPE),
        "label": "decoded (file + line, quoted from the card) | OPEN (supplier named)",
        "stats": stats,
        "rows": records,
    }


# --------------------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    rows = ledger_rows()
    records, stats = verify(rows, ROWS, quiet=args.check)
    md = render(records, stats)
    js = json.dumps(payload(records, stats), indent=2, ensure_ascii=False, sort_keys=False) + "\n"

    if args.write:
        os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        print("wrote %s" % os.path.relpath(OUT_MD, ROOT))
        print("wrote %s" % os.path.relpath(OUT_JSON, ROOT))
        print("rows in scope: %d  (%s)" % (stats["rows_in_scope"],
                                           ", ".join("%s %d" % kv for kv in sorted(stats["status_counts"].items()))))
        print("citations verified: %d, absent-claims verified: %d"
              % (stats["citations_verified"], stats["absent_claims_verified"]))
        return 0

    # --check: byte-compare against the committed artefacts, then re-assert the counts.
    for path, want, what in ((OUT_MD, md, "Markdown"), (OUT_JSON, js, "JSON")):
        if not os.path.exists(path):
            raise SystemExit("missing %s - run --write first" % os.path.relpath(path, ROOT))
        with open(path, "r", encoding="utf-8", newline="") as fh:
            got = fh.read()
        if got.replace("\r\n", "\n") != want:
            raise SystemExit("%s drifted: %s differs from what the source bytes re-derive"
                             % (os.path.relpath(path, ROOT), what))

    with open(OUT_JSON, "r", encoding="utf-8") as fh:
        committed = json.load(fh)
    if committed["stats"] != json.loads(js)["stats"]:
        raise SystemExit("committed stats differ from the recomputed stats")
    if [r["id"] for r in committed["rows"]] != [r["id"] for r in records]:
        raise SystemExit("committed row order differs from the ledger's")

    print("check OK: %d rows in scope, %d citations re-read from the source lines, "
          "%d absent-claims re-tested, %d cards cited, %d unused"
          % (stats["rows_in_scope"], stats["citations_verified"],
             stats["absent_claims_verified"], len(stats["card_citation_counts"]),
             len(stats["cards_unused"])))
    for k in sorted(stats["status_counts"]):
        print("  %-7s %d" % (k, stats["status_counts"][k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
