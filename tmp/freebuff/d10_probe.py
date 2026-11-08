import json, collections

CUR = json.load(open("Working/Translation/rc4_current.json", encoding="utf-8"))["modules"]
print("module keys:", ", ".join(sorted(CUR)))

TARGETS = [
    ("T-M1", "RigidBody", "mass", 4000),
    ("T-M2", "RigidBody", "unit_inertia_yaw", 1.79999995),
    ("T-M2", "RigidBody", "unit_inertia_pitch", 1.5),
    ("T-M2", "RigidBody", "unit_inertia_roll", 0.5),
    ("T-M4", "LandGlobal", "front_wheels.mass", 25),
    ("T-M4", "LandGlobal", "rear_wheels.mass", 75),
    ("T-S1", "Suspension", "front.strength", 80),
    ("T-S1", "Suspension", "rear.strength", 80),
    ("T-S2", "Suspension", "front.compression", 2.5),
    ("T-S2", "Suspension", "rear.compression", 2.5),
    ("T-R1", "LandGlobal", "front_wheels.arcade_friction_multiplier", 1),
    ("T-R1", "LandGlobal", "rear_wheels.arcade_friction_multiplier", 1),
    ("T-G5", "LandGlobal", "wheels_friction_type", 0),
    ("T-ST1", "LandSteering", "steer_angle_min_speed_deg", 35),
    ("T-ST1", "LandSteering", "steer_angle_max_speed_deg", 15),
    ("T-ST1", "LandSteering", "min_speed_kmph", 30),
    ("T-ST1", "LandSteering", "max_speed_kmph", 296.032013),
    ("T-ST1", "LandSteering", "steer_curve_falloff", 2),
    ("T-E1", "LandEngine", "min_rpm", 1000),
    ("T-E1", "LandEngine", "optimal_rpm", 5000),
    ("T-E1", "LandEngine", "max_rpm", 7300),
    ("T-E3", "LandEngine", "torque_factor_at_min_rpm", 0.860000014),
    ("T-E3", "LandEngine", "torque_factor_at_max_rpm", 0.839999974),
    ("T-E4", "Transmission", "gears", 6),
    ("T-E4", "Transmission", "upshift_rpm[0]", 7000),
    ("T-E4", "Transmission", "upshift_rpm[1]", 7000),
    ("T-E4", "Transmission", "upshift_rpm[2]", 7000),
    ("T-E4", "Transmission", "upshift_rpm[3]", 7000),
    ("T-E4", "Transmission", "upshift_rpm[4]", 7000),
    ("T-A2", "LandAerodynamics", "drag_coefficient", 0.139340296),
    ("T-A4", "LandAerodynamics", "lift_coefficient", -1.95000005),
    ("T-K1", "Brakes", "front.max_brake_torque", 10000),
    ("T-K1", "Brakes", "rear.max_brake_torque", 10000),
    ("T-AU4", "LandAudio", "max_rpm", 10000),
    ("T-DM2", "VehicleDamage", "bullet_armor_strength", 100),
    # B-24 handling payload
    ("T-G4", "LandGlobal", "ground_clearance", 0.7037),
    ("T-ST2", "LandSteering", "t_to_full_steer_s", 0.8),
    ("T-ST3", "LandSteering", "max_speed_t_to_full_steer_s", 0.6),
    ("T-ST4", "LandSteering", "steer_input_power_pc", 3),
    ("T-ST4", "LandSteering", "steer_input_power_durango", 3),
    ("T-ST4", "LandSteering", "steer_input_power_orbis", 3),
    ("T-ST6", "LandSteering", "wheel_drift_aligning_strength", 0.3),
    ("T-K3", "Brakes", "handbrake_friction_factor", 1),
    ("T-K4", "Brakes", "front.min_time_to_block", 5),
    ("T-K4", "Brakes", "rear.min_time_to_block", 5),
    ("T-DR1", "CustomLandGlobal", "drift.min_speed_to_drift_kmph", 10),
    ("T-DR1", "CustomLandGlobal", "drift.steering_sensitivity", 4),
    ("T-E2", "LandEngine", "torque_factor_at_optimal_rpm", 1393.5),
    ("T-A3", "LandAerodynamics", "top_speed_drag_coefficient", 2.0),
    ("T-E5", "LandAerodynamics", "drag_coefficient", 0.55),
    ("T-B1", "CustomLandGlobal", "arcade.nitro_boost.torque_multiplier", 2.0),
    ("T-B4", "CustomLandGlobal", "arcade.heat_boost.grip_multiplier", 4.26),
    ("T-B4", "CustomLandGlobal", "arcade.nitro_boost_upgraded.extra_top_speed", 100.92),
]

rows = [json.loads(l) for l in open("Working/Translation/T_ROWS.jsonl", encoding="utf-8") if l.strip()]
print("dispo counts:", dict(collections.Counter(r["dispo"] for r in rows)))
nxt = [r for r in rows if r["dispo"] == "next"]
with_edits = [r for r in nxt if r.get("edits")]
print("next:", len(nxt), "of which carry edits:", len(with_edits))
kinds = collections.Counter()
for r in with_edits:
    for e in r["edits"]:
        kinds[str(e)[:40]] += 1
print("next-edit sample:", json.dumps(with_edits[0]["edits"])[:300] if with_edits else "none")

print("\n%-6s %-17s %-46s %-12s %-12s %s" % ("row", "module", "member", "ledger old", "base", "match"))
bad = 0
for row, mod, mem, old in TARGETS:
    m = CUR.get(mod)
    if not m or "values" not in m:
        print("%-6s %-17s %-46s %-12s MISSING MODULE" % (row, mod, mem, old))
        bad += 1
        continue
    have = m["values"].get(mem, "<<missing>>")
    ok = isinstance(have, (int, float)) and abs(float(have) - float(old)) <= 1e-4 * max(1.0, abs(float(old)))
    if not ok:
        bad += 1
    print("%-6s %-17s %-46s %-12s %-12s %s" % (row, mod, mem, old, have, "ok" if ok else "MISMATCH"))
print("\nmismatches:", bad)
