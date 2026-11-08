"""STATMAP v1: JC3 members x BmAK values. Tags: scraped/exact/magnitude/infer/none."""
import json, os

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"

# BmAK side: [scraped] GPCD schema classes (names+types certain; values unattributed)
# Values below: [exact] wiki-exact or [magnitude] range+pattern (offsets from serials).
BMAK = {
 "top_speed": {"v": "9545 UU/s (=343 kph = 213 mph)", "at": "RVehicle float @serial-bucket",
               "tag": "[magnitude] closest speed-magnitude; 2% over wiki 209mph (true spec may be ~213)",
               "alt": "10000x2 also speed-range; 10000 = 360 kph"},
 "power": {"v": "1200 x3 (three modes/states)", "at": "RVehicle floats",
           "tag": "[exact] wiki 1200 bhp exact match"},
 "torque": {"v": "10000 x2; EnginePeakTorque=100000 (b=400 single-collision)",
            "at": "RVehicle floats; SVehicleSimBase schema",
            "tag": "[magnitude] 10000-range; 100000 needs schema-link confirm"},
 "rpm": {"v": "6000 (rev limit)", "at": "RVehicle float", "tag": "[magnitude] range"},
 "gears": {"v": "ratios ~2.0 cluster + 2.25 + 0.75 (overdrive); BML has 4-state sets",
           "at": "RVehicle ~2.0 floats; GPCD VehicleTransmission.GearRatios+DifferentialRatio",
           "tag": "[magnitude] ratio-range + pattern; full ordered set open"},
 "mass": {"v": "NO direct member (VehicleMass absent from GPCD; mass lives in physics body)",
          "at": "GPCD negative search", "tag": "[none] use JC3 stock or game-feel fit"},
 "horsepower_direct": {"v": "1200 x3 (same as power)", "at": "RVehicle",
                       "tag": "[exact] no separate HP member exists"},
 "brakes": {"v": "Wheel floats 30/40-class; Sim 200/300-class forces", "at": "Wheel/Sim serials",
            "tag": "[magnitude] needs schema-link confirm"},
 "suspension": {"v": "Wheel 64/500/100-class; Sim 1500/3000/24000/8000-class; WheelSuspensionDamping 0.8 (b=456)",
                "at": "serials + GPCD WheelSuspension* schema", "tag": "[magnitude] damping-ratio 0.8 plausible"},
 "steering": {"v": "0.33 x2; BattleModeSteerAngleFactor (schema)", "at": "RVehicle floats + GPCD",
              "tag": "[magnitude] 0.33 rad ~19 deg plausible"},
 "nitro": {"v": "Boost* schema (BoostDuration 2.0? BoostTorqueVSpeedCurve); afterburner +30% wiki",
           "at": "GPCD BoostTorqueVSpeedCurve/StandardTorqueVSpeedCurve/BattleModeVSpeedCurve + wiki",
           "tag": "[magnitude] curves are STRUCTS (points not yet extracted)"},
 "rpm_response": {"v": "MinRPMForExhaustPops, MinimumSpeedForExhaust, ShortRPMBurstThrottleThreshold (names only)",
                  "at": "name table", "tag": "[scraped-names] values in native serials, unattributed"},
 "wheels": {"v": "radius/width/stiffness in WheelFL-FR serials (a=16 export refs + (4,568,64)... series)",
            "at": "SVehicleWheel exports + GPCD 84-prop schema", "tag": "[magnitude] export-ref graph resolved; scalar roles open"},
 "afterburner_speed": {"v": "209 mph base -> +30% = 272 mph w/ afterburner (wiki estimates)",
                       "at": "wiki (NOT gospel)", "tag": "[wiki] 058/059 applied 336/437kph caps; 84kph cap unexplained (gear table prime suspect)"},
}

JC3 = [
 ("transmission.top_speed", "320 (059: 1727)", "top_speed", "336kph->1727 disp-units (factor UNCONFIRMED; 059 still 84kph)"),
 ("transmission.final_drive", "3.91 (059: 4.4)", "gears", "ratio trim"),
 ("transmission.gears", "6 (XML gear table)", "gears", "count + per-gear ratios (BML set open)"),
 ("vehicle_misc.official_top_speed", "250 (059: 1328)", "top_speed", "display cap; same unit question"),
 ("land_engine.torque_factor_at_max_rpm", "0.84 (059: 1.176)", "torque", "x1.4 estimate stack"),
 ("land_engine.torque_factor_at_min_rpm", "0.86 (059: 1.204)", "torque", "x1.4 estimate stack"),
 ("land_engine.max_rpm", "14600 (test-003 baked)", "rpm", "BmAK 6000 suggests LOWER (untouched; flagged)"),
 ("land_engine.optimal-torque", "490 (semantics unknown)", "torque", "left alone; unknown semantics"),
 ("custom_land_global.extra_top_speed", "80/40/80 (059: 104/52/104)", "afterburner_speed", "x1.3 tiers"),
 ("custom_land_global.torque_multiplier", "2x3 (059: 2.5x3)", "nitro", "boost multipliers"),
 ("custom_land_global.grip/boost/punch", "misc multipliers", "nitro", "left stock"),
 ("rigid_body.mass", "975", "mass", "NO BmAK equivalent (physics-side; user: movement only)"),
 ("brakes.*", "stock", "brakes", "pending schema-link"),
 ("suspension.*", "stock", "suspension", "pending schema-link"),
 ("steering.*", "stock", "steering", "pending schema-link"),
 ("tires.*", "stock", "wheels", "pending schema-link"),
]

lines = ["# JC3 Serpente x BmAK Batmobile STATMAP v1",
         "",
         "Rule: JC3 side fully inventoried (`_move_stats.py`, 30 modules); BmAK side = "
         "GPCD schema [scraped] + serial values [exact]/[magnitude]. Tags: [scraped] certain, "
         "[exact] wiki-exact, [magnitude] range+pattern, [wiki] estimates, [none] no equivalent.",
         "",
         "| JC3 member (module) | JC3 value | BmAK equivalent | BmAK value | evidence |",
         "|---------------------|-----------|-----------------|------------|----------|"]
for jm, jv, bk, note in JC3:
    b = BMAK[bk]
    lines.append("| %s | %s | %s | %s | %s. %s |" % (jm, jv, bk, b["v"], b["tag"], note))
open(os.path.join(A, "STATMAP.md"), "w").write("\n".join(lines) + "\n")
json.dump({"bmak": BMAK, "jc3": JC3}, open(os.path.join(A, "statmap.json"), "w"), indent=1)
print("statmap rows:", len(JC3))
