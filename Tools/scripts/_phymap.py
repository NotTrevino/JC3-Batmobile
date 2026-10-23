"""PHYSMAP: JC3 physics members x BmAK equivalents, evidence-tagged."""
import json, os

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
inv = json.load(open(os.path.join(A, "jc3_phys.json")))

def val(mod, name, occ=0):
    vs = [m["val"] for m in inv[mod]["members"] if m["name"] == name]
    return vs[occ] if len(vs) > occ else "?"

ROWS = [
 ("rigid_body.mass", val("rigid_body", "mass"),
  "SVehicle.ChassisMass x MassScale (GPCD schema)",
  "mass values in native serials, unattributed", "[scraped-schema]+[magnitude]"),
 ("rigid_body.unit_inertia_{yaw,pitch,roll}", "1.8/1.5/0.5",
  "SVehicle.InertiaTensorMultiplier",
  "multiplier struct in native serial", "[scraped-schema]"),
 ("rigid_body.center_of_mass_bias", val("rigid_body", "center_of_mass_bias"),
  "KEEP (no BmAK CoM member; mass distribution is per-body PhysX)",
  "-", "[none]"),
 ("rigid_body.{linear,angular}_damping", "0/0",
  "KEEP (both zero stock; nothing to match)", "-", "[none]"),
 ("suspension.strength F/R", "%s/%s" % (val("suspension", "strength", 0), val("suspension", "strength", 1)),
  "WheelSuspensionStiffness/Damping/Bias (GPCD) + Sim 1500/3000-class values",
  "native serials, unattributed", "[scraped-schema]+[magnitude]"),
 ("suspension.length/min/max", "0.25/0/+0",
  "SuspensionTravelUp/Down (GPCD)",
  "native serials", "[scraped-schema]"),
 ("suspension.{compression,relaxation}", "4,3 / 7,4",
  "WheelSuspensionDamping + Sim damping values",
  "native serials", "[scraped-schema]+[magnitude]"),
 ("front/rear_tire curves", "7-pt x/y/y2, peak 1.0@0.405slip",
  "LongSlipRatio/LatSlipAngle + Long/LatExtremum/AsymptoteSlip/Value + WheelInertia (GPCD tire model)",
  "curve params in native serials", "[scraped-schema]"),
 ("tires.grip_multipliers", "1.5/2/1.5 (custom_land_global tiers)",
  "LongSlipFactor/LatSlipFactor/Handbrake+Parked factors (GPCD)",
  "native serials", "[scraped-schema]"),
 ("brakes.max_brake_torque", "10000 x2",
  "SVehicleWheel.BrakeTorque + BrakeTyreType/HandbrakeTyreType",
  "native serials", "[scraped-schema]"),
 ("steering.35deg->15deg", val("land_steering", "steer_angle_min_speed_deg") + "->" + val("land_steering", "steer_angle_max_speed_deg"),
  "BattleModeSteerAngleFactor + SteerFactor + BML_Steering RTPC (default 100.0, scraped serial)",
  "RTPC verified; angle factors in native serials", "[scraped]+[magnitude]"),
 ("steering.sensitivity/drift", "4 / 0.3",
  "BattleModeTrailingSteerFactorMoving, TurnOnSpotTorqueFactor (GPCD names)",
  "native serials", "[scraped-names]"),
 ("aerodynamics.drag/lift/frontal", "0.33 / -1.95 / 2.4",
  "KEEP (no BmAK aero members in schema; Batmobile downforce is mesh+code)",
  "-", "[none]+[scraped-negative]"),
 ("buoyancy.*", "boat params",
  "KEEP (Batmobile does not float)", "-", "[none]"),
 ("RAY wheel stations (physicsc)", "4 stations (test-055 aligned)",
  "BmAK wheel positions (stance stations) + WheelRadius/WheelWidth (GPCD)",
  "specs + test-055", "[scraped]+[verified-055]"),
 ("custom_land_global.push_force/punch", "15000/20000N tiers, 0.1s delay",
  "RBatmobileBooster thrust (native 23B serial: values 2375-class?)",
  "unattributed", "[magnitude]"),
 ("body_COL", "external mesh, follows render",
  "BmAK PhysX collision (per-body; follows mesh)",
  "established behavior", "[verified-prior]"),
]

lines = ["# JC3 Serpente x BmAK Batmobile PHYSMAP v1",
         "",
         "Rule: JC3 side fully inventoried (`_phys_inv.py` -> `jc3_phys.json`, all members). "
         "BmAK side = GPCD schema [scraped] + serial values [magnitude]. Tags as stated.",
         "",
         "| JC3 member | JC3 value | BmAK equivalent | BmAK value | evidence |",
         "|------------|-----------|-----------------|------------|----------|"]
for jm, jv, be, bv, ev in ROWS:
    lines.append("| %s | %s | %s | %s | %s |" % (jm, jv, be, bv, ev))
open(os.path.join(A, "PHYSMAP.md"), "w").write("\n".join(lines) + "\n")
json.dump([{"jc3": jm, "jc3val": jv, "bmak": be, "bmakval": bv, "ev": ev} for jm, jv, be, bv, ev in ROWS],
          open(os.path.join(A, "phymap.json"), "w"), indent=1)
print("phymap rows:", len(ROWS))
