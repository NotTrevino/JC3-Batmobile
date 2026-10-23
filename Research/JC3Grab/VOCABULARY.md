# JC3 vehicle module vocabulary

Derived from **232** decoded `.ee` entities by `Tools/scripts/jc3grab.py`.
Each block is a module instance type; each row is a member path with its
type and the range seen across every decoded entity.

## `Aerodynamics`

| member | type | fleet range | donor |
|---|---|---|---|
| `aerodynamic_surfaces` | A[AerodynamicSurface] | 1 strings:  |  |
| `aerodynamic_surfaces[].air_density` | float | 0 .. 1.3 (med 1.3, n=77) |  |
| `aerodynamic_surfaces[].center_point[]` | float | -20 .. 36 (med 0, n=231) |  |
| `aerodynamic_surfaces[].drag_coefficient` | float | 0 .. 4 (med 0.5, n=77) |  |
| `aerodynamic_surfaces[].extra_brake_drag_coefficient` | float | 0.3 .. 3 (med 1, n=77) |  |
| `aerodynamic_surfaces[].frontal_area` | float | 0 .. 350 (med 10, n=77) |  |
| `aerodynamic_surfaces[].lift_coefficient` | float | 0 .. 8 (med 0, n=77) |  |
| `aerodynamic_surfaces[].name.hash` | uint32 | 0 .. 2.03933e+09 (med 5.06158e+08, n=77) |  |
| `aerodynamic_surfaces[].name.string` | string | 4 strings: AeroSurface, LeftWing, RightWing, TailWing |  |
| `aerodynamic_surfaces[].physics_component_name.hash` | uint32 | 0 .. 2.03933e+09 (med 5.06158e+08, n=77) |  |
| `aerodynamic_surfaces[].physics_component_name.string` | string | 4 strings: , LeftWing, RightWing, TailWing |  |
| `aerodynamic_surfaces[].pitch_steering_factor` | float | 0 .. 0 (med 0, n=77) |  |
| `aerodynamic_surfaces[].roll_steering_factor` | float | 0 .. 0 (med 0, n=77) |  |
| `aerodynamic_surfaces[].surface_normal_angles.pitch_deg` | float | 0 .. 0 (med 0, n=77) |  |
| `aerodynamic_surfaces[].surface_normal_angles.roll_deg` | float | 0 .. 0 (med 0, n=77) |  |
| `aerodynamic_surfaces[].surface_normal_angles.yaw_deg` | float | 0 .. 0 (med 0, n=77) |  |
| `aerodynamic_surfaces[].top_speed_drag_coefficient` | float | 0 .. 5 (med 2, n=77) |  |
| `aerodynamic_surfaces[].turn_steering_factor` | float | 0 .. 0 (med 0, n=77) |  |
| `drag_c_vs_attack_angle_deg.control_points[].x` | float | -9.86076e-32 .. 1 (med 1, n=820) |  |
| `drag_c_vs_attack_angle_deg.control_points[].y` | float | -22.782 .. 28.2649 (med 0, n=820) |  |
| `drag_c_vs_attack_angle_deg.control_points[].y2` | float | -22.782 .. 31.1877 (med 0, n=820) |  |
| `drag_c_vs_attack_angle_deg.number_of_control_points` | int8 | 2 .. 7 (med 2, n=41) |  |
| `drag_c_vs_attack_angle_deg.x_max` | float | 180 .. 180 (med 180, n=41) |  |
| `drag_c_vs_attack_angle_deg.x_min` | float | 0 .. 0 (med 0, n=41) |  |
| `drag_c_vs_attack_angle_deg.y_max` | float | 4 .. 4 (med 4, n=41) |  |
| `drag_c_vs_attack_angle_deg.y_min` | float | 1 .. 1 (med 1, n=41) |  |
| `lift_c_vs_attack_angle_deg.control_points[].x` | float | -68.4897 .. 66.2699 (med 0.0638298, n=820) |  |
| `lift_c_vs_attack_angle_deg.control_points[].y` | float | -3.85186e-34 .. 0.81 (med 0.333333, n=820) |  |
| `lift_c_vs_attack_angle_deg.control_points[].y2` | float | -253.966 .. 80000 (med 6.11266e-37, n=820) |  |
| `lift_c_vs_attack_angle_deg.number_of_control_points` | int8 | 12 .. 12 (med 12, n=41) |  |
| `lift_c_vs_attack_angle_deg.x_max` | float | 180 .. 180 (med 180, n=41) |  |
| `lift_c_vs_attack_angle_deg.x_min` | float | -8 .. -8 (med -8, n=41) |  |
| `lift_c_vs_attack_angle_deg.y_max` | float | 2 .. 2 (med 2, n=41) |  |
| `lift_c_vs_attack_angle_deg.y_min` | float | -1 .. -1 (med -1, n=41) |  |

## `AirAudio`

| member | type | fleet range | donor |
|---|---|---|---|
| `acceleration` | float | 100 .. 100 (med 100, n=41) |  |
| `idle_load` | float | 0.5 .. 0.5 (med 0.5, n=41) |  |
| `load_hold_dt` | float | 5 .. 5 (med 5, n=41) |  |
| `load_release_dt` | float | 5 .. 5 (med 5, n=41) |  |
| `max_rpm` | float | 5300 .. 5300 (med 5300, n=41) |  |
| `min_rpm` | float | 800 .. 4500 (med 4500, n=41) |  |
| `rpm_ramp_up_speed` | float | 0.25 .. 0.25 (med 0.25, n=41) |  |
| `shutdown_rpm` | float | 500 .. 500 (med 500, n=41) |  |
| `thrust_coef` | float | 0.3 .. 0.3 (med 0.3, n=41) |  |
| `top_speed` | float | 70 .. 70 (med 70, n=41) |  |
| `velocity_coef` | float | 0.7 .. 0.7 (med 0.7, n=41) |  |

## `AirEngine`

| member | type | fleet range | donor |
|---|---|---|---|
| `max_thrust` | float | 15000 .. 280000 (med 45000, n=41) |  |
| `max_thrust_acceleration` | float | 5000 .. 300000 (med 30000, n=41) |  |
| `min_thrust` | float | 1000 .. 125000 (med 5000, n=41) |  |
| `run_thrust` | float | 25000 .. 150000 (med 90000, n=41) |  |
| `taxiing_input_threshold` | float | 0.1 .. 0.9 (med 0.1, n=41) |  |
| `taxiing_max_thrust` | float | 5000 .. 600000 (med 5000, n=41) |  |
| `taxiing_top_speed` | float | 15 .. 30 (med 20, n=41) |  |

## `AirGlobal`

| member | type | fleet range | donor |
|---|---|---|---|
| `altitude_limit_threshold_high` | float | 5500 .. 5500 (med 5500, n=41) |  |
| `altitude_limit_threshold_low` | float | 4500 .. 4500 (med 4500, n=41) |  |
| `base_wheel_hardpoint_positions` | A[WheelHardpoint] | 1 strings:  |  |
| `base_wheel_hardpoint_positions[].position[]` | float | -24.974 .. 10.086 (med 0.337, n=531) |  |
| `front_wheels.arcade_drag_multiplier` | float | 0 .. 0.1 (med 0.1, n=41) |  |
| `front_wheels.arcade_friction_multiplier` | float | 1 .. 30 (med 2, n=41) |  |
| `front_wheels.mass` | float | 20 .. 500 (med 20, n=41) |  |
| `front_wheels.match_road_velocity_on_landing` | int8 | 0 .. 0 (med 0, n=41) |  |
| `front_wheels.radius` | float | 0.1 .. 0.88 (med 0.25, n=41) |  |
| `front_wheels.rim_radius` | float | 0.1 .. 0.45 (med 0.3, n=41) |  |
| `front_wheels.use_shape_cast` | int8 | 0 .. 0 (med 0, n=41) |  |
| `front_wheels.width` | float | 0.1 .. 0.5 (med 0.2, n=41) |  |
| `ground_pitch_angle_deg` | float | 0 .. 15 (med 0, n=41) |  |
| `heat_boost.boost_blend_time` | float | 0.2 .. 0.2 (med 0.2, n=41) |  |
| `heat_boost.extra_top_speed` | float | 150 .. 150 (med 150, n=41) |  |
| `heat_boost.push_acceleration` | float | 10 .. 10 (med 10, n=41) |  |
| `is_rear_steered` | int8 | 0 .. 1 (med 0, n=41) |  |
| `nitro_boost.boost_blend_time` | float | 0.2 .. 0.2 (med 0.2, n=41) |  |
| `nitro_boost.extra_top_speed` | float | 30 .. 30 (med 30, n=41) |  |
| `nitro_boost.push_acceleration` | float | 1 .. 10 (med 5, n=41) |  |
| `nitro_boost_upgraded.boost_blend_time` | float | 0.2 .. 0.2 (med 0.2, n=41) |  |
| `nitro_boost_upgraded.extra_top_speed` | float | 60 .. 60 (med 60, n=41) |  |
| `nitro_boost_upgraded.push_acceleration` | float | 2 .. 20 (med 10, n=41) |  |
| `number_of_front_wheels` | int32 | -1 .. 2 (med -1, n=41) |  |
| `number_of_wheels` | int32 | 0 .. 10 (med 3, n=41) |  |
| `rear_wheels.arcade_drag_multiplier` | float | 0 .. 0.1 (med 0.1, n=41) |  |
| `rear_wheels.arcade_friction_multiplier` | float | 1 .. 5 (med 2, n=41) |  |
| `rear_wheels.mass` | float | 20 .. 500 (med 20, n=41) |  |
| `rear_wheels.match_road_velocity_on_landing` | int8 | 0 .. 0 (med 0, n=41) |  |
| `rear_wheels.radius` | float | 0.1 .. 1 (med 0.33, n=41) |  |
| `rear_wheels.rim_radius` | float | 0.08 .. 0.5 (med 0.3, n=41) |  |
| `rear_wheels.use_shape_cast` | int8 | 0 .. 0 (med 0, n=41) |  |
| `rear_wheels.width` | float | 0.1 .. 0.5 (med 0.2, n=41) |  |

## `AirSteering`

| member | type | fleet range | donor |
|---|---|---|---|
| `PitchAxisTiming.CenteringInputTimeFactor` | float | 1 .. 5 (med 2, n=18) |  |
| `PitchAxisTiming.CounterInputTimeFactor` | float | 2 .. 10 (med 5, n=18) |  |
| `PitchAxisTiming.TimeToMaxInputAtMaxSpeed_s` | float | 1 .. 1.5 (med 1, n=18) |  |
| `PitchAxisTiming.TimeToMaxInputAtMinSpeed_s` | float | 1 .. 1 (med 1, n=18) |  |
| `ReferenceMaxSpeedKPH` | float | 325 .. 360 (med 360, n=18) |  |
| `ReferenceMinSpeedKPH` | float | 36 .. 36 (med 36, n=18) |  |
| `RollAxisTiming.CenteringInputTimeFactor` | float | 1 .. 5 (med 2, n=18) |  |
| `RollAxisTiming.CounterInputTimeFactor` | float | 2 .. 10 (med 5, n=18) |  |
| `RollAxisTiming.TimeToMaxInputAtMaxSpeed_s` | float | 1 .. 1.5 (med 1, n=18) |  |
| `RollAxisTiming.TimeToMaxInputAtMinSpeed_s` | float | 1 .. 1 (med 1, n=18) |  |
| `YawAxisTiming.CenteringInputTimeFactor` | float | 1 .. 5 (med 2, n=18) |  |
| `YawAxisTiming.CounterInputTimeFactor` | float | 2 .. 10 (med 5, n=18) |  |
| `YawAxisTiming.TimeToMaxInputAtMaxSpeed_s` | float | 1 .. 2 (med 1, n=18) |  |
| `YawAxisTiming.TimeToMaxInputAtMinSpeed_s` | float | 1 .. 1 (med 1, n=18) |  |
| `acceleration_smoothing` | float | 0 .. 0 (med 0, n=18) |  |
| `max_steering_angle` | float | 0.4 .. 0.6 (med 0.6, n=18) |  |
| `pitch_return` | float | 0 .. 0.1 (med 0, n=18) |  |
| `roll_return` | float | 0 .. 0.3 (med 0.3, n=18) |  |

## `AirplaneAI`

| member | type | fleet range | donor |
|---|---|---|---|
| `Altitude_Cruising` | float | 50 .. 100 (med 100, n=18) |  |
| `Input_Flight_Pitch.control_points[].x` | float | -3.85193e-34 .. 4.71587e+29 (med 7.79282e-30, n=90) |  |
| `Input_Flight_Pitch.control_points[].y` | float | -2.10195e-43 .. 4.71586e+29 (med 9.05205e-33, n=90) |  |
| `Input_Flight_Pitch.control_points[].y2` | float | -23.3309 .. 4.71587e+29 (med 0, n=90) |  |
| `Input_Flight_Pitch.number_of_control_points` | int8 | 2 .. 4 (med 3, n=18) |  |
| `Input_Flight_Pitch.x_max` | float | 0.08 .. 0.15 (med 0.1, n=18) |  |
| `Input_Flight_Pitch.x_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Flight_Pitch.y_max` | float | 1 .. 1 (med 1, n=18) |  |
| `Input_Flight_Pitch.y_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Flight_Roll.control_points[].x` | float | -3.85193e-34 .. 4.71588e+29 (med 1.88838e-36, n=90) |  |
| `Input_Flight_Roll.control_points[].y` | float | -3.85193e-34 .. 4.71587e+29 (med 7.79291e-30, n=90) |  |
| `Input_Flight_Roll.control_points[].y2` | float | -22.0068 .. 4.71587e+29 (med 0, n=90) |  |
| `Input_Flight_Roll.number_of_control_points` | int8 | 2 .. 4 (med 4, n=18) |  |
| `Input_Flight_Roll.x_max` | float | 0.1 .. 0.75 (med 0.5, n=18) |  |
| `Input_Flight_Roll.x_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Flight_Roll.y_max` | float | 0.75 .. 1 (med 1, n=18) |  |
| `Input_Flight_Roll.y_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Flight_Thrust.control_points[].x` | float | 0 .. 1 (med 1.61762e-36, n=90) |  |
| `Input_Flight_Thrust.control_points[].y` | float | 0 .. 1 (med 5.35676e-33, n=90) |  |
| `Input_Flight_Thrust.control_points[].y2` | float | -4.95277 .. 5.35702e-33 (med 0, n=90) |  |
| `Input_Flight_Thrust.number_of_control_points` | int8 | 2 .. 3 (med 3, n=18) |  |
| `Input_Flight_Thrust.x_max` | float | 20 .. 20 (med 20, n=18) |  |
| `Input_Flight_Thrust.x_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Flight_Thrust.y_max` | float | 1 .. 1 (med 1, n=18) |  |
| `Input_Flight_Thrust.y_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Flight_Yaw.control_points[].x` | float | 0 .. 4.54397e+30 (med 0.0632911, n=90) |  |
| `Input_Flight_Yaw.control_points[].y` | float | 0 .. 1 (med 0.427778, n=90) |  |
| `Input_Flight_Yaw.control_points[].y2` | float | -72.1786 .. 1 (med 0, n=90) |  |
| `Input_Flight_Yaw.number_of_control_points` | int8 | 2 .. 4 (med 4, n=18) |  |
| `Input_Flight_Yaw.x_max` | float | 0.02 .. 0.05 (med 0.02, n=18) |  |
| `Input_Flight_Yaw.x_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Flight_Yaw.y_max` | float | 1 .. 1 (med 1, n=18) |  |
| `Input_Flight_Yaw.y_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Taxi_Speed.control_points[].x` | float | 0 .. 1 (med 0.107595, n=90) |  |
| `Input_Taxi_Speed.control_points[].y` | float | 0 .. 1 (med 0.441667, n=90) |  |
| `Input_Taxi_Speed.control_points[].y2` | float | -28.1223 .. 6.4267e-32 (med 0, n=90) |  |
| `Input_Taxi_Speed.number_of_control_points` | int8 | 2 .. 4 (med 4, n=18) |  |
| `Input_Taxi_Speed.x_max` | float | 10 .. 20 (med 15, n=18) |  |
| `Input_Taxi_Speed.x_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Taxi_Speed.y_max` | float | 1 .. 1 (med 1, n=18) |  |
| `Input_Taxi_Speed.y_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Taxi_Turn.control_points[].x` | float | 0 .. 1 (med 0.0329114, n=90) |  |
| `Input_Taxi_Turn.control_points[].y` | float | 0 .. 1 (med 0.488889, n=90) |  |
| `Input_Taxi_Turn.control_points[].y2` | float | -414.1 .. 3.97121e-29 (med 0, n=90) |  |
| `Input_Taxi_Turn.number_of_control_points` | int8 | 2 .. 4 (med 4, n=18) |  |
| `Input_Taxi_Turn.x_max` | float | 0.15 .. 1 (med 0.5, n=18) |  |
| `Input_Taxi_Turn.x_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Input_Taxi_Turn.y_max` | float | 1 .. 1 (med 1, n=18) |  |
| `Input_Taxi_Turn.y_min` | float | 0 .. 0 (med 0, n=18) |  |
| `Limit_Flight_Speed.control_points[].x` | float | -3.86328e-34 .. 5.90084e+29 (med 5.04151e-31, n=90) |  |
| `Limit_Flight_Speed.control_points[].y` | float | -3.85188e-34 .. 5.90085e+29 (med 2.76056e-43, n=90) |  |
| `Limit_Flight_Speed.control_points[].y2` | float | -6.58235 .. 5.90089e+29 (med 0, n=90) |  |
| `Limit_Flight_Speed.number_of_control_points` | int8 | 2 .. 4 (med 3, n=18) |  |
| `Limit_Flight_Speed.x_max` | float | 1 .. 1 (med 1, n=18) |  |
| `Limit_Flight_Speed.x_min` | float | 0.05 .. 0.15 (med 0.15, n=18) |  |
| `Limit_Flight_Speed.y_max` | float | 100 .. 120 (med 100, n=18) |  |
| `Limit_Flight_Speed.y_min` | float | 35 .. 60 (med 60, n=18) |  |
| `Limit_Full_Roll` | float | 0.08 .. 1 (med 0.08, n=18) |  |
| `Limit_Path_Altitude` | float | 30 .. 30 (med 30, n=18) |  |
| `Limit_Path_Jump_Scalar_Flight` | float | 1.2 .. 5 (med 1.5, n=18) |  |
| `Limit_Path_Jump_Scalar_Taxi` | float | 1 .. 1 (med 1, n=18) |  |
| `Limit_Path_Radius` | float | 10 .. 35 (med 10, n=18) |  |
| `Limit_Pitch` | float | 0.7 .. 0.95 (med 0.8, n=18) |  |
| `Limit_Pitch_Yaw_Switch` | float | -1 .. 0.82 (med 0.6, n=18) |  |
| `Limit_Roll` | float | 0.7 .. 0.95 (med 0.82, n=18) |  |
| `Limit_Taxi_Speed.control_points[].x` | float | -3.85188e-34 .. 6.57762e+23 (med 0.175949, n=90) |  |
| `Limit_Taxi_Speed.control_points[].y` | float | -3.85188e-34 .. 6.57762e+23 (med 0.180556, n=90) |  |
| `Limit_Taxi_Speed.control_points[].y2` | float | -13.9715 .. 6.57762e+23 (med 0, n=90) |  |
| `Limit_Taxi_Speed.number_of_control_points` | int8 | 2 .. 4 (med 4, n=18) |  |
| `Limit_Taxi_Speed.x_max` | float | 1 .. 1 (med 1, n=18) |  |
| `Limit_Taxi_Speed.x_min` | float | 0 .. 0.05 (med 0.03, n=18) |  |
| `Limit_Taxi_Speed.y_max` | float | 13 .. 20 (med 15, n=18) |  |
| `Limit_Taxi_Speed.y_min` | float | 2 .. 5 (med 5, n=18) |  |
| `Speed_Cruising` | float | 60 .. 110 (med 100, n=18) |  |
| `Speed_Landing` | float | 50 .. 60 (med 50, n=18) |  |
| `Speed_Takeoff` | float | 50 .. 80 (med 80, n=18) |  |
| `Speed_Taxi` | float | 10 .. 10 (med 10, n=18) |  |
| `Stunt_BarrelRoll` | uint8 | 0 .. 1 (med 0, n=18) |  |
| `Stunt_Loop` | uint8 | 0 .. 1 (med 0, n=18) |  |
| `Stunt_UTurn` | uint8 | 0 .. 1 (med 0, n=18) |  |

## `BikeAI`

| member | type | fleet range | donor |
|---|---|---|---|
| `Bike_Full_Lean_Angle` | float | 0.03 .. 0.05 (med 0.04, n=19) |  |
| `Bike_Lean_Limit` | float | 0.3 .. 0.7 (med 0.5, n=19) |  |
| `Input_Lean.control_points[].x` | float | 0 .. 1 (med 0.139241, n=95) |  |
| `Input_Lean.control_points[].y` | float | 0 .. 1 (med 0.419445, n=95) |  |
| `Input_Lean.control_points[].y2` | float | -25.9237 .. 0.183934 (med 0, n=95) |  |
| `Input_Lean.number_of_control_points` | int8 | 4 .. 4 (med 4, n=19) |  |
| `Input_Lean.x_max` | float | 0.35 .. 0.5 (med 0.4, n=19) |  |
| `Input_Lean.x_min` | float | 0 .. 0 (med 0, n=19) |  |
| `Input_Lean.y_max` | float | 1 .. 1 (med 1, n=19) |  |
| `Input_Lean.y_min` | float | 0 .. 0 (med 0, n=19) |  |
| `Input_Settings.Input_Speed.control_points[].x` | float | 0 .. 1 (med 0.146835, n=95) |  |
| `Input_Settings.Input_Speed.control_points[].y` | float | 0 .. 1 (med 0.408333, n=95) |  |
| `Input_Settings.Input_Speed.control_points[].y2` | float | -21.7752 .. 1 (med 0, n=95) |  |
| `Input_Settings.Input_Speed.number_of_control_points` | int8 | 3 .. 4 (med 4, n=19) |  |
| `Input_Settings.Input_Speed.x_max` | float | 15 .. 30 (med 20, n=19) |  |
| `Input_Settings.Input_Speed.x_min` | float | 0 .. 0 (med 0, n=19) |  |
| `Input_Settings.Input_Speed.y_max` | float | 1 .. 1 (med 1, n=19) |  |
| `Input_Settings.Input_Speed.y_min` | float | 0 .. 0 (med 0, n=19) |  |
| `Input_Settings.Input_Turn.control_points[].x` | float | 0 .. 1 (med 0.156962, n=95) |  |
| `Input_Settings.Input_Turn.control_points[].y` | float | 0 .. 1 (med 0.394445, n=95) |  |
| `Input_Settings.Input_Turn.control_points[].y2` | float | -25.9237 .. 0.183934 (med 0, n=95) |  |
| `Input_Settings.Input_Turn.number_of_control_points` | int8 | 4 .. 4 (med 4, n=19) |  |
| `Input_Settings.Input_Turn.x_max` | float | 0.1 .. 0.5 (med 0.25, n=19) |  |
| `Input_Settings.Input_Turn.x_min` | float | 0 .. 0 (med 0, n=19) |  |
| `Input_Settings.Input_Turn.y_max` | float | 1 .. 1 (med 1, n=19) |  |
| `Input_Settings.Input_Turn.y_min` | float | 0 .. 0 (med 0, n=19) |  |
| `Input_Settings.Limit_IsLargeVehicle` | uint8 | 0 .. 0 (med 0, n=19) |  |
| `Input_Settings.Limit_Speed.control_points[].x` | float | 0 .. 1 (med 0.289873, n=95) |  |
| `Input_Settings.Limit_Speed.control_points[].y` | float | 0 .. 1 (med 0.419444, n=95) |  |
| `Input_Settings.Limit_Speed.control_points[].y2` | float | -13.5907 .. 17.096 (med 0, n=95) |  |
| `Input_Settings.Limit_Speed.number_of_control_points` | int8 | 4 .. 5 (med 4, n=19) |  |
| `Input_Settings.Limit_Speed.x_max` | float | 1 .. 1 (med 1, n=19) |  |
| `Input_Settings.Limit_Speed.x_min` | float | 0 .. 0.07 (med 0.02, n=19) |  |
| `Input_Settings.Limit_Speed.y_max` | float | 30 .. 40 (med 35, n=19) |  |
| `Input_Settings.Limit_Speed.y_min` | float | 5 .. 7 (med 7, n=19) |  |

## `BoatAI`

| member | type | fleet range | donor |
|---|---|---|---|
| `Input_Speed.control_points[].x` | float | -1 .. 1 (med 1.75694e-32, n=175) |  |
| `Input_Speed.control_points[].y` | float | 0 .. 1 (med 1.55234e-31, n=175) |  |
| `Input_Speed.control_points[].y2` | float | -13.7777 .. 2.8125 (med 0, n=175) |  |
| `Input_Speed.number_of_control_points` | int8 | 3 .. 4 (med 3, n=35) |  |
| `Input_Speed.x_max` | float | 7 .. 15 (med 10, n=35) |  |
| `Input_Speed.x_min` | float | 1 .. 1 (med 1, n=35) |  |
| `Input_Speed.y_max` | float | 1 .. 1 (med 1, n=35) |  |
| `Input_Speed.y_min` | float | 0 .. 0 (med 0, n=35) |  |
| `Input_Turn.control_points[].x` | float | 0 .. 1 (med 0.112658, n=175) |  |
| `Input_Turn.control_points[].y` | float | 0 .. 1 (med 0.380556, n=175) |  |
| `Input_Turn.control_points[].y2` | float | -35.6219 .. 1.10654 (med 0, n=175) |  |
| `Input_Turn.number_of_control_points` | int8 | 4 .. 4 (med 4, n=35) |  |
| `Input_Turn.x_max` | float | 0.1 .. 0.5 (med 0.3, n=35) |  |
| `Input_Turn.x_min` | float | 0 .. 0 (med 0, n=35) |  |
| `Input_Turn.y_max` | float | 1 .. 1 (med 1, n=35) |  |
| `Input_Turn.y_min` | float | 0 .. 0 (med 0, n=35) |  |
| `Limit_IsLargeVehicle` | uint8 | 0 .. 1 (med 0, n=35) |  |
| `Limit_Path_Depth` | float | 5 .. 20 (med 10, n=35) |  |
| `Limit_Path_Jump_Scalar` | float | 1.5 .. 4.5 (med 2.2, n=35) |  |
| `Limit_Path_Radius` | float | 3 .. 30 (med 10, n=35) |  |
| `Limit_Speed.control_points[].x` | float | -1 .. 1 (med 0.211392, n=175) |  |
| `Limit_Speed.control_points[].y` | float | 0 .. 1 (med 0.275, n=175) |  |
| `Limit_Speed.control_points[].y2` | float | -6.54788 .. 19.3601 (med 0, n=175) |  |
| `Limit_Speed.number_of_control_points` | int8 | 4 .. 5 (med 4, n=35) |  |
| `Limit_Speed.x_max` | float | 1 .. 1 (med 1, n=35) |  |
| `Limit_Speed.x_min` | float | 0 .. 0.2 (med 0, n=35) |  |
| `Limit_Speed.y_max` | float | 15 .. 40 (med 30, n=35) |  |
| `Limit_Speed.y_min` | float | 3 .. 5 (med 5, n=35) |  |
| `Limit_Speed_Cruising` | float | 10 .. 40 (med 20, n=35) |  |

## `BoatAudio`

| member | type | fleet range | donor |
|---|---|---|---|
| `max_rpm` | float | 4400 .. 4500 (med 4400, n=35) |  |
| `min_rpm` | float | 250 .. 900 (med 900, n=35) |  |
| `rpm_mix` | float | 0.4 .. 0.4 (med 0.4, n=35) |  |
| `velocity_to_rpm` | float | 80 .. 80 (med 80, n=35) |  |

## `BoatBuoyancy`

| member | type | fleet range | donor |
|---|---|---|---|
| `base_air_drag` | float | 0 .. 50 (med 0.75, n=35) |  |
| `base_buoyancy` | float | 0.1 .. 1.45 (med 1, n=35) |  |
| `base_forward_drag` | float | 30 .. 500 (med 250, n=35) |  |
| `base_lateral_drag` | float | 100 .. 500 (med 250, n=35) |  |
| `base_position[]` | float | 0 .. 0.3 (med 0, n=105) |  |
| `base_radius` | float | 0.8 .. 1.5 (med 1, n=35) |  |
| `base_vertical_drag` | float | 100 .. 2000 (med 250, n=35) |  |
| `buoyancy_modules` | A[BoatBuoyancyModule] | 1 strings:  |  |
| `buoyancy_modules[].air_drag` | float | 0 .. 1 (med 0, n=294) |  |
| `buoyancy_modules[].buoyancy` | float | 1 .. 1 (med 1, n=294) |  |
| `buoyancy_modules[].forward_drag` | float | 1 .. 1 (med 1, n=294) |  |
| `buoyancy_modules[].lateral_drag` | float | 1 .. 1 (med 1, n=294) |  |
| `buoyancy_modules[].position[]` | float | -6 .. 6 (med 0.1, n=882) |  |
| `buoyancy_modules[].radius` | float | 0.5 .. 1.2 (med 1, n=294) |  |
| `buoyancy_modules[].vertical_drag` | float | 1 .. 2 (med 1, n=294) |  |
| `up_velocity_cap` | float | 5 .. 100 (med 40, n=35) |  |

## `BoatEngine`

| member | type | fleet range | donor |
|---|---|---|---|
| `engine_axis[]` | float | 0 .. 1 (med 0, n=105) |  |
| `engine_graphical_offset[]` | float | 0 .. 0 (med 0, n=105) |  |
| `engine_position[]` | float | -2 .. 0 (med 0, n=105) |  |
| `max_acceleration_vs_speed.control_points[].x` | float | 0 .. 1 (med 0.497436, n=175) |  |
| `max_acceleration_vs_speed.control_points[].y` | float | 0 .. 1 (med 0.507692, n=175) |  |
| `max_acceleration_vs_speed.control_points[].y2` | float | -3.60507 .. 2.02124 (med 0, n=175) |  |
| `max_acceleration_vs_speed.number_of_control_points` | int8 | 3 .. 4 (med 3, n=35) |  |
| `max_acceleration_vs_speed.x_max` | float | 50 .. 100 (med 50, n=35) |  |
| `max_acceleration_vs_speed.x_min` | float | 0 .. 0 (med 0, n=35) |  |
| `max_acceleration_vs_speed.y_max` | float | 10 .. 60 (med 50, n=35) |  |
| `max_acceleration_vs_speed.y_min` | float | 0 .. 0 (med 0, n=35) |  |
| `physics_component_name.hash` | uint32 | 0 .. 0 (med 0, n=35) |  |
| `physics_component_name.string` | string | 1 strings:  |  |
| `propeller_offset[]` | float | 0 .. 0 (med 0, n=105) |  |
| `propulsion_displacement_limit` | float | 0.02 .. 0.25 (med 0.1, n=35) |  |

## `BoatGlobal`

| member | type | fleet range | donor |
|---|---|---|---|
| `heat_boost.extra_top_speed` | float | 60 .. 80 (med 80, n=35) |  |
| `heat_boost.prop_rpm_multiplier` | float | 1.5 .. 2 (med 2, n=35) |  |
| `heat_boost.prop_torque_multiplier` | float | 1.5 .. 2 (med 2, n=35) |  |
| `nitro_boost.extra_top_speed` | float | 30 .. 40 (med 40, n=35) |  |
| `nitro_boost.prop_rpm_multiplier` | float | 1.5 .. 2 (med 1.5, n=35) |  |
| `nitro_boost.prop_torque_multiplier` | float | 1.5 .. 2 (med 1.5, n=35) |  |
| `nitro_boost_upgraded.extra_top_speed` | float | 60 .. 80 (med 80, n=35) |  |
| `nitro_boost_upgraded.prop_rpm_multiplier` | float | 2 .. 4 (med 2, n=35) |  |
| `nitro_boost_upgraded.prop_torque_multiplier` | float | 2 .. 5 (med 2, n=35) |  |
| `turbo_jump.punch_delay_time` | float | 0 .. 0.1 (med 0, n=35) |  |
| `turbo_jump.punch_speed_kph` | float | 50 .. 60 (med 50, n=35) |  |
| `turbo_jump.top_speed_jump_multiplier` | float | 1 .. 2 (med 2, n=35) |  |
| `turbo_jump.top_speed_kph` | float | 100 .. 200 (med 200, n=35) |  |
| `turbo_jump.up_multiplier` | float | 12 .. 25 (med 12, n=35) |  |
| `turbo_jump_upgraded.punch_delay_time` | float | 0 .. 0.1 (med 0, n=35) |  |
| `turbo_jump_upgraded.punch_speed_kph` | float | 80 .. 120 (med 80, n=35) |  |
| `turbo_jump_upgraded.top_speed_jump_multiplier` | float | 1 .. 2 (med 2, n=35) |  |
| `turbo_jump_upgraded.top_speed_kph` | float | 100 .. 200 (med 200, n=35) |  |
| `turbo_jump_upgraded.up_multiplier` | float | 25 .. 50 (med 25, n=35) |  |

## `BoatSteering`

| member | type | fleet range | donor |
|---|---|---|---|
| `acceleration_smoothing` | float | 0.01 .. 0.3 (med 0.05, n=35) |  |
| `steeringfilter.counterinput_speed_factor` | float | 3 .. 3 (med 3, n=35) |  |
| `steeringfilter.input_max_speed_kmph` | float | 50 .. 150 (med 150, n=35) |  |
| `steeringfilter.input_speedcurve_falloff` | float | 2 .. 2 (med 2, n=35) |  |
| `steeringfilter.input_start_speed_kmph` | float | 10 .. 20 (med 10, n=35) |  |
| `steeringfilter.t_to_full_input_max_speed_s` | float | 0.8 .. 4 (med 2, n=35) |  |
| `steeringfilter.t_to_full_input_min_speed_s` | float | 0.5 .. 2 (med 0.5, n=35) |  |
| `steeringfilter.zeroinput_speed_factor` | float | 2 .. 2 (med 2, n=35) |  |

## `Brakes`

| member | type | fleet range | donor |
|---|---|---|---|
| `front.handbrake` | int32 | 0 .. 0 (med 0, n=271) | 0 |
| `front.max_brake_torque` | float | 250 .. 1e+07 (med 5000, n=271) | 14000 |
| `front.min_time_to_block` | float | -1 .. 20 (med -1, n=271) | 1 |
| `handbrake_friction_factor` | float | 1 .. 10 (med 2, n=271) | 2 |
| `rear.handbrake` | int32 | 1 .. 1 (med 1, n=271) | 1 |
| `rear.max_brake_torque` | float | 500 .. 1e+07 (med 5000, n=271) | 14000 |
| `rear.min_time_to_block` | float | -1 .. 20 (med -1, n=271) | 1 |

## `Buoyancy`

| member | type | fleet range | donor |
|---|---|---|---|
| `bottom_area` | float | 3 .. 3 (med 3, n=198) | 3 |
| `buoyancy` | float | 0 .. 2 (med 2, n=198) | 2 |
| `buoyancy_modules` | A[BuoyancyModule] | 1 strings:  |  |
| `buoyancy_modules[].position[]` | float | 0 .. 0 (med 0, n=594) | 0 |
| `drag` | float | 100 .. 100 (med 100, n=198) | 100 |
| `radius` | float | 0.55 .. 0.55 (med 0.55, n=198) | 0.550000012 |
| `side_area` | float | 1.85 .. 1.85 (med 1.85, n=198) | 1.85000002 |
| `up_velocity_cap` | float | 20 .. 20 (med 20, n=198) | 20 |

## `CarAI`

| member | type | fleet range | donor |
|---|---|---|---|
| `Input_Speed.control_points[].x` | float | -1.70141e+38 .. 1 (med 8.68161e-34, n=630) | 0 |
| `Input_Speed.control_points[].y` | float | -1 .. 1 (med 0, n=630) | 0 |
| `Input_Speed.control_points[].y2` | float | -64.6583 .. 1.41208e-30 (med 0, n=630) | 0 |
| `Input_Speed.number_of_control_points` | int8 | 3 .. 4 (med 3, n=126) | 3 |
| `Input_Speed.x_max` | float | 12 .. 25 (med 15, n=126) | 15 |
| `Input_Speed.x_min` | float | 0 .. 1 (med 1, n=126) | 1 |
| `Input_Speed.y_max` | float | 1 .. 1 (med 1, n=126) | 1 |
| `Input_Speed.y_min` | float | 0 .. 0 (med 0, n=126) | 0 |
| `Input_Turn.control_points[].x` | float | -1 .. 1 (med 0.056962, n=630) | 0 |
| `Input_Turn.control_points[].y` | float | -1 .. 1 (med 0.269444, n=630) | 0 |
| `Input_Turn.control_points[].y2` | float | -140.107 .. 1 (med 0, n=630) | 0 |
| `Input_Turn.number_of_control_points` | int8 | 4 .. 4 (med 4, n=126) | 4 |
| `Input_Turn.x_max` | float | 0.15 .. 1 (med 0.5, n=126) | 0.5 |
| `Input_Turn.x_min` | float | 0 .. 0 (med 0, n=126) | 0 |
| `Input_Turn.y_max` | float | 1 .. 1 (med 1, n=126) | 1 |
| `Input_Turn.y_min` | float | 0 .. 0 (med 0, n=126) | 0 |
| `Limit_IsLargeVehicle` | uint8 | 0 .. 1 (med 0, n=126) | 0 |
| `Limit_Speed.control_points[].x` | float | -1 .. 1 (med 0.294937, n=630) | 0 |
| `Limit_Speed.control_points[].y` | float | -1 .. 1 (med 0.261111, n=630) | 0 |
| `Limit_Speed.control_points[].y2` | float | -11.1241 .. 23.7749 (med 0, n=630) | 0 |
| `Limit_Speed.number_of_control_points` | int8 | 4 .. 5 (med 4, n=126) | 4 |
| `Limit_Speed.x_max` | float | 1 .. 1 (med 1, n=126) | 1 |
| `Limit_Speed.x_min` | float | 0 .. 0.2 (med 0.05, n=126) | 0.100000001 |
| `Limit_Speed.y_max` | float | 22 .. 45 (med 30, n=126) | 35 |
| `Limit_Speed.y_min` | float | 2 .. 10 (med 5, n=126) | 5 |

## `CustomLandGlobal`

| member | type | fleet range | donor |
|---|---|---|---|
| `arcade.heat_boost.boost_blend_time` | float | 0 .. 0 (med 0, n=145) | 0 |
| `arcade.heat_boost.extra_top_speed` | float | 50 .. 120 (med 80, n=145) | 80 |
| `arcade.heat_boost.grip_multiplier` | float | 1.3 .. 4.5 (med 1.5, n=145) | 1.5 |
| `arcade.heat_boost.push_force` | float | 0 .. 0 (med 0, n=145) | 0 |
| `arcade.heat_boost.torque_multiplier` | float | 2 .. 4.5 (med 2, n=145) | 2 |
| `arcade.nitro_boost.boost_blend_time` | float | 0.2 .. 0.2 (med 0.2, n=145) | 0.200000003 |
| `arcade.nitro_boost.extra_top_speed` | float | 30 .. 60 (med 40, n=145) | 40 |
| `arcade.nitro_boost.grip_multiplier` | float | 1.2 .. 2 (med 2, n=145) | 2 |
| `arcade.nitro_boost.push_force` | float | 15000 .. 15000 (med 15000, n=145) | 15000 |
| `arcade.nitro_boost.torque_multiplier` | float | 1.5 .. 40 (med 2, n=145) | 2 |
| `arcade.nitro_boost_upgraded.boost_blend_time` | float | 0.2 .. 0.2 (med 0.2, n=145) | 0.200000003 |
| `arcade.nitro_boost_upgraded.extra_top_speed` | float | 60 .. 100 (med 80, n=145) | 80 |
| `arcade.nitro_boost_upgraded.grip_multiplier` | float | 1.5 .. 2.5 (med 1.5, n=145) | 1.5 |
| `arcade.nitro_boost_upgraded.push_force` | float | 20000 .. 20000 (med 20000, n=145) | 20000 |
| `arcade.nitro_boost_upgraded.torque_multiplier` | float | 2 .. 80 (med 2, n=145) | 2 |
| `arcade.turbo_jump.f_multiplier` | float | 12 .. 15 (med 15, n=145) | 15 |
| `arcade.turbo_jump.punch_delay_time` | float | 0.1 .. 0.1 (med 0.1, n=145) | 0.100000001 |
| `arcade.turbo_jump.punch_speed_kph` | float | 50 .. 50 (med 50, n=145) | 50 |
| `arcade.turbo_jump.r_multiplier` | float | 12 .. 15 (med 12, n=145) | 12 |
| `arcade.turbo_jump.top_speed_jump_multiplier` | float | 2 .. 2 (med 2, n=145) | 2 |
| `arcade.turbo_jump.top_speed_kph` | float | 200 .. 200 (med 200, n=145) | 200 |
| `arcade.turbo_jump_upgraded.f_multiplier` | float | 25 .. 30 (med 30, n=145) | 30 |
| `arcade.turbo_jump_upgraded.punch_delay_time` | float | 0.1 .. 0.1 (med 0.1, n=145) | 0.100000001 |
| `arcade.turbo_jump_upgraded.punch_speed_kph` | float | 80 .. 80 (med 80, n=145) | 80 |
| `arcade.turbo_jump_upgraded.r_multiplier` | float | 25 .. 30 (med 25, n=145) | 25 |
| `arcade.turbo_jump_upgraded.top_speed_jump_multiplier` | float | 2 .. 2 (med 2, n=145) | 2 |
| `arcade.turbo_jump_upgraded.top_speed_kph` | float | 200 .. 200 (med 200, n=145) | 200 |
| `drift.constant_drift_torque` | float | 0 .. 20000 (med 2000, n=145) | 0 |
| `drift.counter_steer_rot_factor` | float | 0 .. 0.6 (med 0.5, n=145) | 0 |
| `drift.counter_steer_torque` | float | 0 .. 60000 (med 10000, n=145) | 3000 |
| `drift.counter_steer_torque_brake` | float | 0 .. 45000 (med 10000, n=145) | 5000 |
| `drift.counter_steer_torque_handbrake` | float | 0 .. 100000 (med 36000, n=145) | 30000 |
| `drift.drift_entry_slip_angle` | float | 10 .. 180 (med 25, n=145) | 20 |
| `drift.drift_exit_slip_angle` | float | 1 .. 180 (med 8, n=145) | 2 |
| `drift.drift_limit_spread_angle_deg` | float | 10 .. 15 (med 15, n=145) | 15 |
| `drift.drift_yaw_vel_damp` | float | 0.01 .. 0.05 (med 0.02, n=145) | 0.0199999996 |
| `drift.exit_drift_yaw_vel_damp` | float | 0.2 .. 0.8 (med 0.5, n=145) | 0.5 |
| `drift.keep_velocity_strength` | float | 0 .. 1.5 (med 1, n=145) | 1 |
| `drift.max_drift_angle_deg` | float | 20 .. 60 (med 45, n=145) | 45 |
| `drift.max_drift_torque` | float | 0 .. 35000 (med 12000, n=145) | 5000 |
| `drift.max_keep_velocity_acceleration_g` | float | 2 .. 2 (med 2, n=145) | 2 |
| `drift.min_speed_to_drift_kmph` | float | 0 .. 60 (med 10, n=145) | 10 |
| `drift.overdrift_yaw_vel_damp` | float | 0 .. 1 (med 0.05, n=145) | 0.0299999993 |
| `drift.steering_sensitivity` | float | 0.5 .. 4 (med 2, n=145) | 4 |
| `drift.velocity_rotation_amount` | float | 20 .. 100 (med 60, n=145) | 80 |
| `drift.velocity_rotation_angle_exp` | float | 0.2 .. 8 (med 0.5, n=145) | 0.200000003 |
| `drift.velocity_rotation_end_angle` | float | 25 .. 65 (med 45, n=145) | 40 |
| `drift.velocity_rotation_start_angle` | float | 0 .. 30 (med 15, n=145) | 15 |
| `front_wheels_damage.broken_wheel_friction_fraction` | float | 0.5 .. 0.75 (med 0.75, n=145) | 0.5 |
| `front_wheels_damage.broken_wheel_radius_fraction` | float | 0.6 .. 0.8 (med 0.75, n=145) | 0.800000012 |
| `front_wheels_damage.skew_health` | int32 | 200 .. 400 (med 200, n=145) | 200 |
| `gravity_multiplier_grounded` | float | 1 .. 1.5 (med 1, n=145) | 1 |
| `gravity_multiplier_in_air_down` | float | 1 .. 2 (med 1.5, n=145) | 1 |
| `gravity_multiplier_in_air_up` | float | 1 .. 2 (med 1.5, n=145) | 1 |
| `linear_damping[]` | float | 0 .. 0 (med 0, n=435) | 0 |
| `rear_wheels_damage.broken_wheel_friction_fraction` | float | 0.5 .. 0.75 (med 0.75, n=145) | 0.5 |
| `rear_wheels_damage.broken_wheel_radius_fraction` | float | 0.6 .. 0.8 (med 0.75, n=145) | 0.800000012 |
| `rear_wheels_damage.skew_health` | int32 | 200 .. 400 (med 200, n=145) | 200 |
| `takeoff_pitch_damping` | float | 0.2 .. 0.8 (med 0.5, n=145) | 0.5 |

## `CustomVelocityDamper`

| member | type | fleet range | donor |
|---|---|---|---|
| `handbrake_spin_damping` | float | 0 .. 4 (med 0, n=145) | 0 |
| `velocity_damper.collision_spin_damping` | float | 0 .. 5 (med 0.05, n=145) | 0.0500000007 |
| `velocity_damper.collision_spin_threshold` | float | 0 .. 5 (med 2.5, n=145) | 2.5 |
| `velocity_damper.normal_spin_damping` | float | 0 .. 3 (med 0, n=145) | 0 |

## `Decals`

| member | type | fleet range | donor |
|---|---|---|---|
| `decal_counts` | A[int16] | 1 strings:  |  |
| `decal_counts[]` | int16 | 0 .. 16 (med 0, n=492) | 8 |
| `decal_indices` | A[int16] | 1 strings:  |  |
| `decal_indices[]` | int16 | -1 .. 0 (med 0, n=492) | -1 |

## `DeformPoints`

| member | type | fleet range | donor |
|---|---|---|---|
| `constraint_indices` | A[uint16] | 1 strings:  |  |
| `constraint_indices[]` | uint16 | 0 .. 344 (med 73, n=2282) | 131 |
| `hauling_hitch_indices` | A[uint16] | 1 strings:  |  |
| `light_indices` | A[uint16] | 1 strings:  |  |
| `light_indices[]` | uint16 | 0 .. 335 (med 60, n=3217) | 130 |
| `non_deformable_parts_indices` | A[uint16] | 1 strings:  |  |
| `non_deformable_parts_indices[]` | uint16 | 0 .. 326 (med 63, n=6659) | 121 |
| `points` | A[DeformPoint] | 1 strings:  |  |
| `points[].deform_point_type.hash` | uint32 | 1.21967e+09 .. 4.21119e+09 (med 1.21967e+09, n=28218) | 1219670572 |
| `points[].deform_point_type.string` | string | 5 strings: Constraint, Light, NonDeformablePart, None (+1) | None |
| `points[].end_transform[]` | float | -85.3009 .. 85.3009 (med 0, n=451488) | 1 |
| `points[].from_part` | string | 62 strings: oldjeep_antenna, oldjeep_axle_f_l, oldjeep_axle_f_r, oldjeep_b_l_blkr (+58) | sportsmuscle_signal_r_r |
| `points[].from_part_hash` | uint32 | 1.53152e+06 .. 4.29455e+09 (med 2.25078e+09, n=28218) | 2306150513 |
| `points[].from_part_index` | uint32 | 0 .. 118 (med 19, n=28218) | 30 |
| `points[].has_custom_end` | uint8 | 0 .. 0 (med 0, n=28218) | 0 |
| `points[].name` | string | 177 strings: antenna, antenna_trail, b_l_blkr_electric, b_l_blkr_glass (+173) | signal_r_r_glass_break |
| `points[].name_hash` | uint32 | 179854 .. 4.29451e+09 (med 2.08766e+09, n=28218) | 1557440190 |
| `points[].shape_key` | uint32 | 0 .. 0 (med 0, n=28218) | 0 |
| `points[].skinned_to_part` | string | 26 strings: oldjeep_back_gate, oldjeep_back_seat, oldjeep_body, oldjeep_door_f_l (+22) | sportsmuscle_trunk |
| `points[].skinned_to_part_hash` | uint32 | 1.53152e+06 .. 4.28816e+09 (med 2.4345e+09, n=28218) | 3807347875 |
| `points[].skinned_to_part_index` | uint32 | 0 .. 94 (med 0, n=28218) | 10 |
| `points[].start_transform[]` | float | -85.3009 .. 85.3009 (med 0, n=451488) | 1 |
| `points[].vertex_indices[]` | int16 | 0 .. 1441 (med 86, n=112872) | 33 |
| `points[].vertex_weights[]` | float | 0 .. 0.999936 (med 0.250008, n=112872) | 0.248307928 |
| `trailing_hitch_indices` | A[uint16] | 1 strings:  |  |
| `wheel_indices` | A[uint16] | 1 strings:  |  |
| `wheel_indices[]` | uint16 | 0 .. 338 (med 65, n=718) | 129 |

## `DriverLean`

| member | type | fleet range | donor |
|---|---|---|---|
| `counterlean_speed_factor` | float | 3 .. 100 (med 20, n=23) |  |
| `drift_factor_lean_power` | float | 0.2 .. 0.2 (med 0.2, n=23) |  |
| `drift_leaning_torque` | float | 9000 .. 12000 (med 9000, n=23) |  |
| `ease_in_angle_deg` | float | 5 .. 35 (med 20, n=23) |  |
| `lean_damping` | float | 0.2 .. 0.3 (med 0.2, n=23) |  |
| `lean_max_speed_kmph` | float | 150 .. 8000 (med 800, n=23) |  |
| `lean_ratio_for_max_steer` | float | 0.4 .. 0.4 (med 0.4, n=23) |  |
| `lean_speedcurve_falloff` | float | 1 .. 2 (med 2, n=23) |  |
| `lean_start_speed_kmph` | float | 30 .. 150 (med 100, n=23) |  |
| `leaning_torque` | float | 2000 .. 8000 (med 5000, n=23) |  |
| `max_drift_lean_angle_deg` | float | 40 .. 45 (med 45, n=23) |  |
| `max_lean_angle_deg` | float | 20 .. 40 (med 30, n=23) |  |
| `righting_torque` | float | 1500 .. 4000 (med 3000, n=23) |  |
| `t_to_full_lean_max_speed_s` | float | 0.2 .. 1 (med 0.8, n=23) |  |
| `t_to_full_lean_min_speed_s` | float | 0.1 .. 0.8 (med 0.2, n=23) |  |
| `zerolean_speed_factor` | float | 1 .. 10 (med 10, n=23) |  |

## `EffectAttachments`

| member | type | fleet range | donor |
|---|---|---|---|
| `all_effects` | A[EffectAttachment] | 1 strings:  |  |
| `all_effects[].deform_point.hash` | uint32 | 7.51804e+06 .. 4.29017e+09 (med 2.12234e+09, n=9230) | 2864934619 |
| `all_effects[].deform_point.string` | string | 82 strings: antenna, antenna_trail, b_l_blkr_electric, b_l_blkr_glass (+78) | window_r_r |
| `all_effects[].effect.hash` | uint32 | 7.94636e+06 .. 4.28116e+09 (med 1.74783e+09, n=9230) | 1747834702 |
| `all_effects[].effect.string` | string | 17 strings: burn_base, burn_engine, burn_roof, door_break (+13) | window_break |
| `effect_indices[]` | int32 | 0 .. 80 (med 21, n=885) | 27 |
| `on_part_broke_off[]` | int32 | 0 .. 84 (med 24, n=7590) | 50 |
| `on_part_burning[]` | int32 | 0 .. 53 (med 3, n=696) | 8 |
| `on_part_exploded[]` | int32 | 0 .. 72 (med 14, n=1346) | 46 |
| `on_part_loosened[]` | int32 | 4 .. 62 (med 19, n=248) |  |
| `on_part_reached_damaged_state[]` | int32 | 0 .. 77 (med 29, n=2893) | 44 |
| `part_effects` | A[PartEffectAttachments] | 1 strings:  |  |
| `part_effects[].effect_starts.on_part_broke_off` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_starts.on_part_burning` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_starts.on_part_exploded` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_starts.on_part_loosened` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_starts.on_part_reached_damaged_state` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_stops.on_part_broke_off` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_stops.on_part_burning` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_stops.on_part_exploded` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_stops.on_part_loosened` | A[int32] | 1 strings:  |  |
| `part_effects[].effect_stops.on_part_reached_damaged_state` | A[int32] | 1 strings:  |  |
| `part_effects[].effects_count` | int32 | 1 .. 19 (med 2, n=5280) | 1 |
| `part_effects[].first_effect_index` | int32 | 0 .. 84 (med 25, n=5280) | 50 |
| `part_effects[].part.hash` | uint32 | 1.53152e+06 .. 4.29247e+09 (med 2.20003e+09, n=5280) | 4050264034 |
| `part_effects[].part.string` | string | 125 strings: armoredtruck_body, armoredtruck_bumper_f, armoredtruck_bumper_r, armoredtruck_door_f_l (+121) | sportsmuscle_window_r_r |
| `usage_effects` | A[UsageEffectAttachments] | 1 strings:  |  |
| `usage_effects[].effect_indices` | A[int32] | 1 strings:  |  |
| `usage_effects[].usage.hash` | uint32 | 1.02641e+08 .. 4.19789e+09 (med 3.55154e+09, n=346) | 3551535361 |
| `usage_effects[].usage.string` | string | 12 strings: , EngineNitro, EngineRunning, EngineSmoking (+8) | HeadLights |

## `ExtendedEffectUsages`

| member | type | fleet range | donor |
|---|---|---|---|
| `usages` | A[ExtendedEffectUsage] | 1 strings:  |  |

## `ExtendedExposedVariables`

| member | type | fleet range | donor |
|---|---|---|---|
| `variables` | A[ExtendedExposedVariable] | 1 strings:  |  |
| `variables[].expression` | string | 2 strings: speed_rom_intensity = 1 - ( speed_rom_time_remaining / speed_rom_total_time ), speed_rom_threshold = speed_ms / speed_rom_speed_threshold |  |

## `Fins`

| member | type | fleet range | donor |
|---|---|---|---|
| `fins[].area` | float | 0 .. 2 (med 0, n=200) |  |
| `fins[].distance_to_hinge` | float | 0 .. 0 (med 0, n=200) |  |
| `fins[].effective_in_air` | uint8 | 0 .. 0 (med 0, n=200) |  |
| `fins[].effective_in_water` | uint8 | 0 .. 1 (med 1, n=200) |  |
| `fins[].height` | float | 0.1 .. 2 (med 0.5, n=200) |  |
| `fins[].hinge_angles.pitch_deg` | float | 0 .. 0 (med 0, n=200) |  |
| `fins[].hinge_angles.roll_deg` | float | -90 .. 20 (med 0, n=200) |  |
| `fins[].hinge_angles.yaw_deg` | float | 0 .. 0 (med 0, n=200) |  |
| `fins[].hinge_position[]` | float | -2.5 .. 20 (med 0, n=600) |  |
| `fins[].max_angle_deg` | float | 0 .. 40 (med 10, n=200) |  |
| `fins[].min_angle_deg` | float | -40 .. 0 (med -10, n=200) |  |
| `fins[].physics_component_name.hash` | uint32 | 0 .. 0 (med 0, n=200) |  |
| `fins[].physics_component_name.string` | string | 1 strings:  |  |
| `fins[].steering_factor` | float | 0 .. 1 (med 0, n=200) |  |
| `lift_vs_attack_angle_deg.control_points[].x` | float | 0 .. 1 (med 0.251899, n=200) |  |
| `lift_vs_attack_angle_deg.control_points[].y` | float | 0 .. 1 (med 0.294444, n=200) |  |
| `lift_vs_attack_angle_deg.control_points[].y2` | float | -62.3773 .. 12.5782 (med 0, n=200) |  |
| `lift_vs_attack_angle_deg.number_of_control_points` | int8 | 5 .. 5 (med 5, n=40) |  |
| `lift_vs_attack_angle_deg.x_max` | float | 90 .. 90 (med 90, n=40) |  |
| `lift_vs_attack_angle_deg.x_min` | float | 0 .. 0 (med 0, n=40) |  |
| `lift_vs_attack_angle_deg.y_max` | float | 0.7 .. 0.7 (med 0.7, n=40) |  |
| `lift_vs_attack_angle_deg.y_min` | float | 0 .. 0 (med 0, n=40) |  |
| `max_steering_vs_speed_ms.control_points[].x` | float | -9.86076e-32 .. 1.49519e+23 (med 0.306329, n=200) |  |
| `max_steering_vs_speed_ms.control_points[].y` | float | -3.85193e-34 .. 1.49517e+23 (med 0.627778, n=200) |  |
| `max_steering_vs_speed_ms.control_points[].y2` | float | -2.25609e-43 .. 1.49517e+23 (med 0, n=200) |  |
| `max_steering_vs_speed_ms.number_of_control_points` | int8 | 2 .. 4 (med 3, n=40) |  |
| `max_steering_vs_speed_ms.x_max` | float | 15 .. 20 (med 20, n=40) |  |
| `max_steering_vs_speed_ms.x_min` | float | 0 .. 0 (med 0, n=40) |  |
| `max_steering_vs_speed_ms.y_max` | float | 1 .. 1 (med 1, n=40) |  |
| `max_steering_vs_speed_ms.y_min` | float | 0 .. 0 (med 0, n=40) |  |
| `number_of_fins` | uint8 | 0 .. 5 (med 4, n=40) |  |
| `pressure_drag` | float | 0 .. 2e+06 (med 2e+06, n=40) |  |
| `pressure_drag2` | float | 0 .. 50000 (med 0, n=40) |  |
| `reference_speed_ms` | float | 20 .. 30 (med 30, n=40) |  |

## `HelicopterAI`

| member | type | fleet range | donor |
|---|---|---|---|
| `Input_Altitude.control_points[].x` | float | 0 .. 1 (med 0.405063, n=115) |  |
| `Input_Altitude.control_points[].y` | float | 0 .. 1 (med 0.322222, n=115) |  |
| `Input_Altitude.control_points[].y2` | float | -11.3976 .. 12.94 (med 0, n=115) |  |
| `Input_Altitude.number_of_control_points` | int8 | 3 .. 5 (med 5, n=23) |  |
| `Input_Altitude.x_max` | float | 20 .. 20 (med 20, n=23) |  |
| `Input_Altitude.x_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Input_Altitude.y_max` | float | 1 .. 1 (med 1, n=23) |  |
| `Input_Altitude.y_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Input_Altitude_Landing` | float | -0.5 .. -0.01 (med -0.25, n=23) |  |
| `Input_Pitch.control_points[].x` | float | 0 .. 1 (med 0.437975, n=115) |  |
| `Input_Pitch.control_points[].y` | float | 0 .. 1 (med 0.397222, n=115) |  |
| `Input_Pitch.control_points[].y2` | float | -9.98869 .. 20.1351 (med 0, n=115) |  |
| `Input_Pitch.number_of_control_points` | int8 | 4 .. 5 (med 5, n=23) |  |
| `Input_Pitch.x_max` | float | 10 .. 32 (med 20, n=23) |  |
| `Input_Pitch.x_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Input_Pitch.y_max` | float | 0.8 .. 1 (med 1, n=23) |  |
| `Input_Pitch.y_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Input_Roll.control_points[].x` | float | 0 .. 1 (med 0.435443, n=115) |  |
| `Input_Roll.control_points[].y` | float | 0 .. 1 (med 0.366667, n=115) |  |
| `Input_Roll.control_points[].y2` | float | -10.9353 .. 13.7226 (med 0, n=115) |  |
| `Input_Roll.number_of_control_points` | int8 | 4 .. 5 (med 5, n=23) |  |
| `Input_Roll.x_max` | float | 20 .. 40 (med 25, n=23) |  |
| `Input_Roll.x_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Input_Roll.y_max` | float | 0.7 .. 1 (med 0.9, n=23) |  |
| `Input_Roll.y_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Input_Yaw.control_points[].x` | float | 0 .. 3.77148 (med 0.126582, n=115) |  |
| `Input_Yaw.control_points[].y` | float | 0 .. 1 (med 0.327778, n=115) |  |
| `Input_Yaw.control_points[].y2` | float | -9.13409 .. 1 (med 0, n=115) |  |
| `Input_Yaw.number_of_control_points` | int8 | 3 .. 5 (med 3, n=23) |  |
| `Input_Yaw.x_max` | float | 0.15 .. 0.5 (med 0.2, n=23) |  |
| `Input_Yaw.x_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Input_Yaw.y_max` | float | 1 .. 1 (med 1, n=23) |  |
| `Input_Yaw.y_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Limit_Path_Altitude.control_points[].x` | float | 0 .. 3.79492 (med 3.34342e-32, n=115) |  |
| `Limit_Path_Altitude.control_points[].y` | float | 0 .. 1 (med 6.61015e-33, n=115) |  |
| `Limit_Path_Altitude.control_points[].y2` | float | -14.6356 .. 16.9475 (med 0, n=115) |  |
| `Limit_Path_Altitude.number_of_control_points` | int8 | 3 .. 5 (med 3, n=23) |  |
| `Limit_Path_Altitude.x_max` | float | 20 .. 40 (med 30, n=23) |  |
| `Limit_Path_Altitude.x_min` | float | 0 .. 0 (med 0, n=23) |  |
| `Limit_Path_Altitude.y_max` | float | 10 .. 25 (med 15, n=23) |  |
| `Limit_Path_Altitude.y_min` | float | 0 .. 5 (med 0, n=23) |  |
| `Limit_Path_Jump_Scalar` | float | 1 .. 1.5 (med 1.5, n=23) |  |
| `Limit_Path_Radius` | float | 7 .. 15 (med 10, n=23) |  |
| `Limit_Speed_Flight` | float | 50 .. 70 (med 56, n=23) |  |
| `Limit_Speed_Hover` | float | 20 .. 60 (med 30, n=23) |  |

## `HelicopterModel`

| member | type | fleet range | donor |
|---|---|---|---|
| `add_bank_roll_deg` | float | 5 .. 15 (med 15, n=23) |  |
| `add_bank_roll_pull_up_deg` | float | 5 .. 20 (med 5, n=23) |  |
| `add_climb_pitch_deg` | float | 0 .. 15 (med 0, n=23) |  |
| `add_dive_pitch_deg` | float | 20 .. 50 (med 45, n=23) |  |
| `add_force_forward_power` | float | 1 .. 1 (med 1, n=23) |  |
| `add_force_lateral_power` | float | 0.001 .. 1 (med 0.001, n=23) |  |
| `add_forward_force` | float | 15 .. 35 (med 30, n=23) |  |
| `add_lateral_factor_pull_up` | float | 0.05 .. 0.15 (med 0.15, n=23) |  |
| `add_right_force` | float | 15 .. 80 (med 30, n=23) |  |
| `altitude_input_power` | float | 0.3 .. 1.5 (med 1, n=23) |  |
| `altitude_limit_threshold_high` | float | 3300 .. 3300 (med 3300, n=23) |  |
| `altitude_limit_threshold_low` | float | 3000 .. 3000 (med 3000, n=23) |  |
| `angular_drag` | float | 0.5 .. 28 (med 2, n=23) |  |
| `bank_max_velocity_kmph` | float | 60 .. 250 (med 150, n=23) |  |
| `bank_start_velocity_kmph` | float | 30 .. 50 (med 30, n=23) |  |
| `center_of_torques_x` | float | 0 .. 0 (med 0, n=23) |  |
| `center_of_torques_y` | float | 2.5 .. 4 (med 3, n=23) |  |
| `center_of_torques_z` | float | -1.6 .. 0.2 (med 0, n=23) |  |
| `climb_speed_low_speed_kmph` | float | 100 .. 500 (med 100, n=23) |  |
| `counter_pitch_angle_deg` | float | 0 .. 10 (med 0, n=23) |  |
| `counter_pitch_speed_kmph` | float | 30 .. 30 (med 30, n=23) |  |
| `dive_speed_low_speed_kmph` | float | 100 .. 200 (med 100, n=23) |  |
| `forward_drag` | float | 1 .. 70 (med 16, n=23) |  |
| `forward_drag_no_input` | float | 0.5 .. 0.5 (med 0.5, n=23) |  |
| `high_speed_altitude_d` | float | 0 .. 1 (med 0.2, n=23) |  |
| `high_speed_altitude_i` | float | 0 .. 1 (med 0.1, n=23) |  |
| `high_speed_altitude_p` | float | 0.2 .. 5 (med 5, n=23) |  |
| `high_speed_max_drag_yaw_speed` | float | 0.8 .. 1.2 (med 0.8, n=23) |  |
| `lateral_drag` | float | 1 .. 80 (med 16, n=23) |  |
| `lateral_drag_no_input` | float | 0.5 .. 0.5 (med 0.5, n=23) |  |
| `low_speed_altitude_d` | float | 0 .. 0.2 (med 0.2, n=23) |  |
| `low_speed_altitude_i` | float | 0 .. 0.3 (med 0.2, n=23) |  |
| `low_speed_altitude_p` | float | 0.1 .. 1 (med 0.5, n=23) |  |
| `low_speed_max_drag_yaw_speed` | float | 1 .. 3 (med 1.2, n=23) |  |
| `max_climbing_gs` | float | 1 .. 4 (med 2, n=23) |  |
| `max_diving_gs` | float | 1 .. 3 (med 2, n=23) |  |
| `max_pitch_high_speed_deg` | float | 5 .. 10 (med 5, n=23) |  |
| `max_pitch_low_speed_deg` | float | 20 .. 25 (med 20, n=23) |  |
| `max_roll_deg` | float | 30 .. 30 (med 30, n=23) |  |
| `max_roll_input_for_climb` | float | 0.3 .. 0.3 (med 0.3, n=23) |  |
| `max_speed_dive_kmph` | float | 150 .. 300 (med 250, n=23) |  |
| `max_speed_t_to_full_yaw_s` | float | 1.2 .. 2 (med 2, n=23) |  |
| `min_altitude_input` | float | 0.1 .. 0.1 (med 0.1, n=23) |  |
| `min_speed_dive_kmph` | float | 0 .. 30 (med 0, n=23) |  |
| `pitch_d` | float | 0.05 .. 0.8 (med 0.2, n=23) |  |
| `pitch_i` | float | 0.025 .. 0.8 (med 0.1, n=23) |  |
| `pitch_input_dead_zone` | float | 0 .. 0 (med 0, n=23) |  |
| `pitch_input_power` | float | 2 .. 2 (med 2, n=23) |  |
| `pitch_max_amplitude` | float | 0.5 .. 5 (med 1, n=23) |  |
| `pitch_p` | float | 0.025 .. 1 (med 0.05, n=23) |  |
| `roll_d` | float | 0.05 .. 0.8 (med 0.1, n=23) |  |
| `roll_i` | float | 0 .. 0.4 (med 0.1, n=23) |  |
| `roll_input_power` | float | 2 .. 2 (med 2, n=23) |  |
| `roll_max_amplitude` | float | 1 .. 3 (med 3, n=23) |  |
| `roll_p` | float | 0.035 .. 1 (med 0.035, n=23) |  |
| `t_to_full_yaw_s` | float | 0.5 .. 1.8 (med 1.2, n=23) |  |
| `tail_distance_to_com_m` | float | 4 .. 20 (med 8, n=23) |  |
| `tail_lateral_drag` | float | 0 .. 1 (med 1, n=23) |  |
| `tail_vertical_drag` | float | 0 .. 1 (med 0.5, n=23) |  |
| `trim_input_gain` | float | 20 .. 30 (med 25, n=23) |  |
| `unsettled_altitude_gain_climb` | float | 0.5 .. 0.5 (med 0.5, n=23) |  |
| `unsettled_altitude_gain_dive` | float | -1.5 .. -1.5 (med -1.5, n=23) |  |
| `vertical_drag` | float | 1 .. 80 (med 16, n=23) |  |
| `vertical_drag_no_input` | float | 0.5 .. 0.5 (med 0.5, n=23) |  |
| `yaw_d` | float | 0 .. 0.8 (med 0.1, n=23) |  |
| `yaw_drag_no_input` | float | 0.1 .. 1.5 (med 1, n=23) |  |
| `yaw_i` | float | 0 .. 0.1 (med 0, n=23) |  |
| `yaw_input_power` | float | 2 .. 3 (med 2, n=23) |  |
| `yaw_max_amplitude` | float | 2 .. 8 (med 2, n=23) |  |
| `yaw_p` | float | 0.1 .. 2 (med 0.5, n=23) |  |

## `HelicopterSteering`

| member | type | fleet range | donor |
|---|---|---|---|
| `air_steering.PitchAxisTiming.CenteringInputTimeFactor` | float | 1.5 .. 4 (med 1.5, n=23) |  |
| `air_steering.PitchAxisTiming.CounterInputTimeFactor` | float | 2 .. 8 (med 2, n=23) |  |
| `air_steering.PitchAxisTiming.TimeToMaxInputAtMaxSpeed_s` | float | 1 .. 4 (med 1, n=23) |  |
| `air_steering.PitchAxisTiming.TimeToMaxInputAtMinSpeed_s` | float | 1 .. 4 (med 1, n=23) |  |
| `air_steering.ReferenceMaxSpeedKPH` | float | 120 .. 360 (med 360, n=23) |  |
| `air_steering.ReferenceMinSpeedKPH` | float | 30 .. 36 (med 36, n=23) |  |
| `air_steering.RollAxisTiming.CenteringInputTimeFactor` | float | 2 .. 4 (med 2, n=23) |  |
| `air_steering.RollAxisTiming.CounterInputTimeFactor` | float | 5 .. 8 (med 5, n=23) |  |
| `air_steering.RollAxisTiming.TimeToMaxInputAtMaxSpeed_s` | float | 1 .. 4 (med 1, n=23) |  |
| `air_steering.RollAxisTiming.TimeToMaxInputAtMinSpeed_s` | float | 1 .. 3 (med 1, n=23) |  |
| `air_steering.YawAxisTiming.CenteringInputTimeFactor` | float | 1.5 .. 5 (med 2, n=23) |  |
| `air_steering.YawAxisTiming.CounterInputTimeFactor` | float | 2 .. 20 (med 10, n=23) |  |
| `air_steering.YawAxisTiming.TimeToMaxInputAtMaxSpeed_s` | float | 1 .. 2 (med 1.5, n=23) |  |
| `air_steering.YawAxisTiming.TimeToMaxInputAtMinSpeed_s` | float | 0.5 .. 2 (med 1.5, n=23) |  |
| `air_steering.acceleration_smoothing` | float | 0 .. 0.1 (med 0, n=23) |  |
| `air_steering.max_steering_angle` | float | 0.3 .. 1 (med 1, n=23) |  |
| `air_steering.pitch_return` | float | 2 .. 2.15 (med 2, n=23) |  |
| `air_steering.roll_return` | float | 1.8 .. 2.15 (med 1.8, n=23) |  |
| `return_pitch_limit` | float | 0.7 .. 0.7 (med 0.7, n=23) |  |
| `return_roll_limit` | float | 0.7 .. 0.7 (med 0.7, n=23) |  |

## `LandAerodynamics`

| member | type | fleet range | donor |
|---|---|---|---|
| `air_density` | float | 1.25 .. 1.3 (med 1.3, n=306) | 1.29999995 |
| `drag_coefficient` | float | 0 .. 4 (med 0.5, n=306) | 0.800000012 |
| `frontal_area` | float | 0.2 .. 80 (med 2.9, n=306) | 2.5 |
| `lift_coefficient` | float | -2 .. 0.1 (med -0.05, n=306) | -0.300000012 |
| `top_speed_drag_coefficient` | float | 1 .. 30 (med 2, n=306) | 2 |

## `LandAudio`

| member | type | fleet range | donor |
|---|---|---|---|
| `max_rpm` | float | 1800 .. 10000 (med 5000, n=145) | 10000 |
| `min_rpm` | float | 0 .. 1000 (med 500, n=145) | 1000 |

## `LandEngine`

| member | type | fleet range | donor |
|---|---|---|---|
| `clutch_slip_rpm` | float | 0 .. 2300 (med 0, n=145) | 0 |
| `engine_damage_noise_scale` | float | 1 .. 2 (med 1, n=145) | 1 |
| `engine_max_damage_torque` | float | 0.25 .. 0.75 (med 0.75, n=145) | 0.75 |
| `engine_min_noise` | float | 0 .. 0.05 (med 0, n=145) | 0 |
| `max_rpm` | float | 2000 .. 1e+07 (med 5800, n=145) | 7300 |
| `min_rpm` | float | 250 .. 3500 (med 1000, n=145) | 1000 |
| `optimal_rpm` | float | 1100 .. 9000 (med 3350, n=145) | 5000 |
| `resistance_at_max_rpm` | float | 0 .. 0.75 (med 0.2, n=145) | 0.200000003 |
| `resistance_at_min_rpm` | float | 0 .. 0.2 (med 0.075, n=145) | 0.0500000007 |
| `resistance_at_optimal_rpm` | float | 0 .. 0.5 (med 0.1, n=145) | 0.100000001 |
| `rev_limiter_rpm_drop` | float | 50 .. 50 (med 50, n=145) | 50 |
| `rpm_power_band` | int32 | 0 .. 0 (med 0, n=145) | 0 |
| `torque_factor_at_max_rpm` | float | 0 .. 1 (med 0.86, n=145) | 0.839999974 |
| `torque_factor_at_min_rpm` | float | 0 .. 1.1 (med 0.95, n=145) | 0.860000014 |
| `torque_factor_at_optimal_rpm` | float | 0 .. 50000 (med 540, n=145) | 490 |

## `LandGlobal`

| member | type | fleet range | donor |
|---|---|---|---|
| `base_wheel_hardpoint_positions` | A[WheelHardpoint] | 1 strings:  |  |
| `base_wheel_hardpoint_positions[].position[]` | float | -3.599 .. 3.599 (med 0.394, n=3381) | 1.44599998 |
| `front_wheels.arcade_drag_multiplier` | float | 0 .. 0.5 (med 0.1, n=271) | 0.100000001 |
| `front_wheels.arcade_friction_multiplier` | float | 0.8 .. 5 (med 2.8, n=271) | 1 |
| `front_wheels.mass` | float | 10 .. 100000 (med 75, n=271) | 25 |
| `front_wheels.match_road_velocity_on_landing` | int8 | 1 .. 1 (med 1, n=271) | 1 |
| `front_wheels.radius` | float | 0.2 .. 1.8 (med 0.36, n=271) | 0.379999995 |
| `front_wheels.rim_radius` | float | 0.127 .. 0.8 (med 0.24765, n=271) | 0.300000012 |
| `front_wheels.use_shape_cast` | int8 | 0 .. 1 (med 0, n=271) | 0 |
| `front_wheels.width` | float | 0.0375 .. 1.42 (med 0.245, n=271) | 0.245000005 |
| `ground_clearance` | float | 0.05 .. 1 (med 0.4, n=271) | 0.400000006 |
| `is_all_wheel_steered` | int8 | 0 .. 1 (med 0, n=271) | 0 |
| `is_rear_steered` | int8 | 0 .. 0 (med 0, n=271) | 0 |
| `normal_clipping_angle_cosine` | float | 0.1 .. 0.8 (med 0.2, n=271) | 0.200000003 |
| `number_of_front_wheels` | int32 | -1 .. 4 (med -1, n=271) | -1 |
| `number_of_wheels` | int32 | 2 .. 8 (med 4, n=271) | 4 |
| `rear_wheels.arcade_drag_multiplier` | float | 0 .. 0.5 (med 0.1, n=271) | 0.100000001 |
| `rear_wheels.arcade_friction_multiplier` | float | 1 .. 6 (med 3, n=271) | 1 |
| `rear_wheels.mass` | float | 10 .. 100000 (med 75, n=271) | 75 |
| `rear_wheels.match_road_velocity_on_landing` | int8 | 1 .. 1 (med 1, n=271) | 1 |
| `rear_wheels.radius` | float | 0.18 .. 1.8 (med 0.36, n=271) | 0.379999995 |
| `rear_wheels.rim_radius` | float | 0.1145 .. 0.8 (med 0.24765, n=271) | 0.300000012 |
| `rear_wheels.use_shape_cast` | int8 | 0 .. 1 (med 0, n=271) | 0 |
| `rear_wheels.width` | float | 0.0375 .. 2.8 (med 0.255, n=271) | 0.284999996 |
| `wheels_friction_type` | int32 | 0 .. 2 (med 0, n=271) | 0 |

## `LandSteering`

| member | type | fleet range | donor |
|---|---|---|---|
| `countersteer_speed_factor` | float | 1.5 .. 20 (med 3, n=252) | 2 |
| `dead_zone` | float | 0 .. 0.1 (med 0, n=252) | 0 |
| `max_speed_kmph` | float | 50 .. 300 (med 150, n=252) | 220 |
| `max_speed_t_to_full_steer_s` | float | -1 .. 5 (med -1, n=252) | 0.850000024 |
| `min_speed_kmph` | float | 1 .. 80 (med 20, n=252) | 30 |
| `saturation_zone` | float | 0.9 .. 1 (med 1, n=252) | 1 |
| `steer_angle_max_speed_deg` | float | 10 .. 35 (med 15, n=252) | 15 |
| `steer_angle_min_speed_deg` | float | 20 .. 45 (med 35, n=252) | 35 |
| `steer_curve_falloff` | float | 0 .. 3 (med 2, n=252) | 2 |
| `steer_in_speed_factor` | float | 1.2 .. 10 (med 2, n=252) | 1.5 |
| `steer_input_power_durango` | float | 1 .. 3 (med 3, n=252) | 3 |
| `steer_input_power_orbis` | float | 1 .. 3 (med 2, n=252) | 3 |
| `steer_input_power_pc` | float | 1 .. 4 (med 2, n=252) | 3 |
| `t_to_full_steer_s` | float | 0.25 .. 10 (med 1.2, n=252) | 1.20000005 |
| `wheel_drift_aligning_strength` | float | 0 .. 0.5 (med 0.5, n=252) | 0.300000012 |

## `MotorbikeSteering`

| member | type | fleet range | donor |
|---|---|---|---|
| `land_steering.countersteer_speed_factor` | float | 2 .. 5 (med 2, n=19) |  |
| `land_steering.dead_zone` | float | 0 .. 0.15 (med 0, n=19) |  |
| `land_steering.max_speed_kmph` | float | 80 .. 250 (med 200, n=19) |  |
| `land_steering.max_speed_t_to_full_steer_s` | float | -1 .. 0.4 (med 0.4, n=19) |  |
| `land_steering.min_speed_kmph` | float | 10 .. 30 (med 20, n=19) |  |
| `land_steering.saturation_zone` | float | 0.95 .. 1 (med 1, n=19) |  |
| `land_steering.steer_angle_max_speed_deg` | float | 5 .. 20 (med 12, n=19) |  |
| `land_steering.steer_angle_min_speed_deg` | float | 30 .. 45 (med 35, n=19) |  |
| `land_steering.steer_curve_falloff` | float | 0 .. 2 (med 2, n=19) |  |
| `land_steering.steer_in_speed_factor` | float | 1.5 .. 2 (med 1.5, n=19) |  |
| `land_steering.steer_input_power_durango` | float | 1 .. 2 (med 1, n=19) |  |
| `land_steering.steer_input_power_orbis` | float | 1 .. 2 (med 1, n=19) |  |
| `land_steering.steer_input_power_pc` | float | 1 .. 2 (med 1, n=19) |  |
| `land_steering.t_to_full_steer_s` | float | 0.3 .. 2 (med 0.6, n=19) |  |
| `land_steering.wheel_drift_aligning_strength` | float | 0.3 .. 0.8 (med 0.5, n=19) |  |
| `wheelie.dead_zone` | float | 0.4 .. 0.95 (med 0.8, n=19) |  |
| `wheelie.input_reactiveness` | float | 0.1 .. 0.2 (med 0.1, n=19) |  |
| `wheelie.max_lean_angle_deg` | float | 15 .. 15 (med 15, n=19) |  |
| `wheelie.min_speed` | float | 0 .. 0 (med 0, n=19) |  |
| `wheelie.nosie_angle_deg` | float | 30 .. 30 (med 30, n=19) |  |
| `wheelie.nosie_center_of_mass_offset[]` | float | -0.7 .. 0 (med -0.15, n=57) |  |
| `wheelie.nosie_torque` | float | -8000 .. 1500 (med -5000, n=19) |  |
| `wheelie.wheelie_angle_deg` | float | 25 .. 30 (med 30, n=19) |  |
| `wheelie.wheelie_center_of_mass_offset[]` | float | -0.15 .. 0.7 (med 0, n=57) |  |
| `wheelie.wheelie_torque` | float | -1500 .. 8000 (med 5000, n=19) |  |

## `MotorbikeSuspension`

| member | type | fleet range | donor |
|---|---|---|---|
| `land_suspension.front.antirollbar_strength` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.front.compression` | float | 2 .. 6 (med 4, n=19) |  |
| `land_suspension.front.direction[]` | float | -1 .. 0 (med 0, n=57) |  |
| `land_suspension.front.hardpoint_offset_along_spring` | float | -0.15 .. 0 (med -0.05, n=19) |  |
| `land_suspension.front.lateral_tire_force_offset` | float | 0 .. 0.45 (med 0.4, n=19) |  |
| `land_suspension.front.length` | float | 0.15 .. 0.6 (med 0.2, n=19) |  |
| `land_suspension.front.longitudinal_tire_force_offset` | float | 0 .. 0.3 (med 0.3, n=19) |  |
| `land_suspension.front.max_length_offset` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.front.max_velocity_for_damp_clamp` | float | 1.5 .. 1500 (med 1.5, n=19) |  |
| `land_suspension.front.min_length` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.front.raycast_offset` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.front.relaxation` | float | 4 .. 25 (med 8, n=19) |  |
| `land_suspension.front.strength` | float | 30 .. 200 (med 150, n=19) |  |
| `land_suspension.front.tire_drag_force_offset` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.rear.antirollbar_strength` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.rear.compression` | float | 2 .. 8 (med 4, n=19) |  |
| `land_suspension.rear.direction[]` | float | -1 .. 0.4 (med 0, n=57) |  |
| `land_suspension.rear.hardpoint_offset_along_spring` | float | -0.15 .. 0 (med -0.1, n=19) |  |
| `land_suspension.rear.lateral_tire_force_offset` | float | 0 .. 0.45 (med 0.4, n=19) |  |
| `land_suspension.rear.length` | float | 0.15 .. 0.5 (med 0.2, n=19) |  |
| `land_suspension.rear.longitudinal_tire_force_offset` | float | 0 .. 0.3 (med 0.3, n=19) |  |
| `land_suspension.rear.max_length_offset` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.rear.max_velocity_for_damp_clamp` | float | 1.5 .. 1500 (med 1.5, n=19) |  |
| `land_suspension.rear.min_length` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.rear.raycast_offset` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.rear.relaxation` | float | 4 .. 25 (med 9, n=19) |  |
| `land_suspension.rear.strength` | float | 30 .. 200 (med 200, n=19) |  |
| `land_suspension.rear.tire_drag_force_offset` | float | 0 .. 0 (med 0, n=19) |  |
| `land_suspension.wheel_hardpoint_offsets` | A[WheelHardpointOffset] | 1 strings:  |  |
| `upper_steering_offset` | float | 0 .. 0 (med 0, n=19) |  |
| `wheel_hardpoint_offsets[].offset[]` | float | 0 .. 0.4 (med 0, n=117) |  |
| `wheel_hardpoint_offsets[].wheel_index` | int32 | 0 .. 2 (med 1, n=39) |  |

## `Palette`

| member | type | fleet range | donor |
|---|---|---|---|
| `tints` | A[Tint] | 1 strings:  |  |
| `tints[].clear_coat` | float | 0 .. 1 (med 1, n=3602) | 1 |
| `tints[].metallic` | float | 0 .. 1 (med 0, n=3602) | 1 |
| `tints[].name.hash` | uint32 | 7.91634e+07 .. 4.26185e+09 (med 2.28386e+09, n=3602) | 2930093752 |
| `tints[].name.string` | string | 155 strings: Alaskan Blue, Almond Green, Aquamarine, Arabian Grey (+151) | Green |
| `tints[].occurrence` | int32 | 50 .. 100 (med 100, n=3602) | 100 |
| `tints[].specular_gloss` | float | 0 .. 1 (med 1, n=3602) | 0.449999988 |
| `tints[].tint_b.A` | float | 1 .. 1 (med 1, n=3602) | 1 |
| `tints[].tint_b.B` | float | 0.05 .. 0.88 (med 0.58, n=3602) | 0.200000003 |
| `tints[].tint_b.G` | float | 0.05 .. 0.88 (med 0.602667, n=3602) | 0.423999995 |
| `tints[].tint_b.R` | float | 0.05 .. 0.88 (med 0.608, n=3602) | 0.200000003 |
| `tints[].tint_g.A` | float | 1 .. 1 (med 1, n=3602) | 1 |
| `tints[].tint_g.B` | float | 0 .. 0.88 (med 0.65, n=3602) | 0.200000003 |
| `tints[].tint_g.G` | float | 0.05 .. 0.9 (med 0.65, n=3602) | 0.423999995 |
| `tints[].tint_g.R` | float | 0.05 .. 0.9 (med 0.65, n=3602) | 0.200000003 |
| `tints[].tint_r.A` | float | 1 .. 1 (med 1, n=3602) | 1 |
| `tints[].tint_r.B` | float | 0 .. 0.88 (med 0.426471, n=3602) | 0.200000003 |
| `tints[].tint_r.G` | float | 0.0325 .. 0.88 (med 0.458667, n=3602) | 0.423999995 |
| `tints[].tint_r.R` | float | 0 .. 0.88 (med 0.498824, n=3602) | 0.200000003 |

## `Propellers`

| member | type | fleet range | donor |
|---|---|---|---|
| `diameter` | float | 0.3 .. 0.3 (med 0.3, n=38) |  |
| `docking_controls.docking_yaw_throttle_limit` | float | 0 .. 0.8 (med 0.8, n=38) |  |
| `docking_controls.max_docking_control_throttle` | float | 0.05 .. 0.3 (med 0.22, n=38) |  |
| `docking_controls.max_docking_speed_ms` | float | 20 .. 20 (med 20, n=38) |  |
| `docking_controls.optimal_docking_speed_ms` | float | 10 .. 10 (med 10, n=38) |  |
| `max_reverse_rpm` | float | 500 .. 2000 (med 2000, n=38) |  |
| `max_rpm` | float | 2000 .. 10000 (med 8000, n=38) |  |
| `max_steering_vs_speed_ms.control_points[].x` | float | -3.85193e-34 .. 5.47013e+23 (med 0.129114, n=190) |  |
| `max_steering_vs_speed_ms.control_points[].y` | float | -3.85193e-34 .. 5.47013e+23 (med 0.833333, n=190) |  |
| `max_steering_vs_speed_ms.control_points[].y2` | float | -3.43528 .. 5.47013e+23 (med 0, n=190) |  |
| `max_steering_vs_speed_ms.number_of_control_points` | int8 | 2 .. 5 (med 3, n=38) |  |
| `max_steering_vs_speed_ms.x_max` | float | 10 .. 30 (med 20, n=38) |  |
| `max_steering_vs_speed_ms.x_min` | float | 0 .. 0 (med 0, n=38) |  |
| `max_steering_vs_speed_ms.y_max` | float | 1 .. 1 (med 1, n=38) |  |
| `max_steering_vs_speed_ms.y_min` | float | 0 .. 0 (med 0, n=38) |  |
| `max_thrust` | float | 8000 .. 200000 (med 60000, n=38) |  |
| `number_of_propellers` | uint8 | 1 .. 2 (med 2, n=38) |  |
| `pitch` | float | 0.6 .. 0.6 (med 0.6, n=38) |  |
| `propellers[].distance_to_hinge` | float | 0 .. 1 (med 0.35, n=76) |  |
| `propellers[].docking_limits.docking_strafe_angles.invert_steering_input` | uint8 | 0 .. 0 (med 0, n=76) |  |
| `propellers[].docking_limits.docking_strafe_angles.steer_left_angle_deg` | float | -90 .. -90 (med -90, n=76) |  |
| `propellers[].docking_limits.docking_strafe_angles.steer_right_angle_deg` | float | 90 .. 90 (med 90, n=76) |  |
| `propellers[].docking_limits.docking_yaw_angles.invert_steering_input` | uint8 | 0 .. 0 (med 0, n=76) |  |
| `propellers[].docking_limits.docking_yaw_angles.steer_left_angle_deg` | float | -90 .. -45 (med -90, n=76) |  |
| `propellers[].docking_limits.docking_yaw_angles.steer_right_angle_deg` | float | 45 .. 90 (med 90, n=76) |  |
| `propellers[].hinge_angles.pitch_deg` | float | 0 .. 10 (med 0, n=76) |  |
| `propellers[].hinge_angles.roll_deg` | float | 0 .. 0 (med 0, n=76) |  |
| `propellers[].hinge_angles.yaw_deg` | float | 0 .. 0 (med 0, n=76) |  |
| `propellers[].hinge_position[]` | float | -2.5 .. 16.5 (med 0, n=228) |  |
| `propellers[].impeller_intake_position[]` | float | -2 .. 1.3 (med 0, n=228) |  |
| `propellers[].is_impeller` | uint8 | 0 .. 1 (med 0, n=76) |  |
| `propellers[].max_angle_deg` | float | 0 .. 28 (med 20, n=76) |  |
| `propellers[].min_angle_deg` | float | -28 .. 0 (med -20, n=76) |  |
| `propellers[].physics_component_name.hash` | uint32 | 0 .. 0 (med 0, n=76) |  |
| `propellers[].physics_component_name.string` | string | 1 strings:  |  |
| `propellers[].trim_flattening_in_turns` | float | 0 .. 1 (med 1, n=76) |  |
| `propellers[].zero_angle_deg` | float | 0 .. 0 (med 0, n=76) |  |
| `thrust_vs_advance_ratio.control_points[].x` | float | 0 .. 1 (med 0.465823, n=190) |  |
| `thrust_vs_advance_ratio.control_points[].y` | float | 0 .. 1 (med 0.761111, n=190) |  |
| `thrust_vs_advance_ratio.control_points[].y2` | float | -13.7689 .. 14.5808 (med 0, n=190) |  |
| `thrust_vs_advance_ratio.number_of_control_points` | int8 | 5 .. 5 (med 5, n=38) |  |
| `thrust_vs_advance_ratio.x_max` | float | 2 .. 2 (med 2, n=38) |  |
| `thrust_vs_advance_ratio.x_min` | float | 0 .. 0 (med 0, n=38) |  |
| `thrust_vs_advance_ratio.y_max` | float | 1 .. 1 (med 1, n=38) |  |
| `thrust_vs_advance_ratio.y_min` | float | 0 .. 0 (med 0, n=38) |  |
| `trim_deg_vs_speed_ms.control_points[].x` | float | -9.86076e-32 .. 3.35944e+33 (med 1.4013e-45, n=190) |  |
| `trim_deg_vs_speed_ms.control_points[].y` | float | -3.88185e-34 .. 3.35944e+33 (med 0, n=190) |  |
| `trim_deg_vs_speed_ms.control_points[].y2` | float | -15.999 .. 3.35944e+33 (med 0, n=190) |  |
| `trim_deg_vs_speed_ms.number_of_control_points` | int8 | 2 .. 4 (med 2, n=38) |  |
| `trim_deg_vs_speed_ms.x_max` | float | 1 .. 30 (med 20, n=38) |  |
| `trim_deg_vs_speed_ms.x_min` | float | 0 .. 0 (med 0, n=38) |  |
| `trim_deg_vs_speed_ms.y_max` | float | 0 .. 12 (med 5, n=38) |  |
| `trim_deg_vs_speed_ms.y_min` | float | 0 .. 8 (med 0, n=38) |  |

## `RigidBody`

| member | type | fleet range | donor |
|---|---|---|---|
| `add_drivers_mass` | int32 | 0 .. 1 (med 0, n=233) | 0 |
| `angular_damping` | float | 0 .. 0.3 (med 0, n=233) | 0 |
| `center_of_mass[]` | float | -23.72 .. 5.58 (med 0, n=699) | 0.649999976 |
| `center_of_mass_bias` | float | -2 .. 0.1 (med -0.2, n=233) | -0.300000012 |
| `driver_center_of_mass[]` | float | 0 .. 0.5 (med 0, n=699) | 0 |
| `linear_damping` | float | 0 .. 0.1 (med 0, n=233) | 0 |
| `mass` | float | 50 .. 550000 (med 3000, n=233) | 975 |
| `max_angular_velocity` | float | -1 .. 100 (med -1, n=233) | -1 |
| `max_linear_velocity` | float | -1 .. 1000 (med -1, n=233) | -1 |
| `unit_inertia_pitch` | float | 0.35 .. 130.5 (med 2.85, n=233) | 1.5 |
| `unit_inertia_roll` | float | 0.1 .. 12.34 (med 0.95, n=233) | 0.5 |
| `unit_inertia_yaw` | float | 0.31 .. 132.23 (med 2.92, n=233) | 1.79999995 |
| `use_calculated_inertia` | int32 | 0 .. 1 (med 1, n=233) | 1 |

## `Rotors`

| member | type | fleet range | donor |
|---|---|---|---|
| `acceleration_multiplier` | float | 5 .. 10 (med 5, n=41) |  |
| `acceleration_rpm` | float | 20 .. 200 (med 30, n=41) |  |
| `deceleration_freespin_multiply` | float | 0.04 .. 4 (med 0.25, n=41) |  |
| `deceleration_multiplier` | float | 0.04 .. 1.25 (med 0.75, n=41) |  |
| `freespin_control` | float | 5 .. 10 (med 9, n=41) |  |
| `max_rpm` | float | 160 .. 300 (med 300, n=41) |  |
| `rotors` | A[Rotor] | 1 strings:  |  |
| `rotors[].axis[]` | float | -1 .. 1 (med 0, n=177) |  |
| `rotors[].does_steer` | int32 | 0 .. 1 (med 0, n=59) |  |
| `rotors[].physics_component_name.hash` | uint32 | 0 .. 4.24969e+09 (med 1.56865e+09, n=59) |  |
| `rotors[].physics_component_name.string` | string | 6 strings: , LeftRotor, OuterLeftRotor, OuterRightRotor (+2) |  |
| `rotors[].position[]` | float | -28 .. 28 (med 0, n=177) |  |
| `rotors[].rotation_speed` | float | 0.5 .. 1 (med 0.5, n=59) |  |
| `rotors[].torque` | float | 0 .. 1 (med 1, n=59) |  |
| `thrust_smoothing` | float | 25000 .. 25000 (med 25000, n=41) |  |

## `Rudders`

| member | type | fleet range | donor |
|---|---|---|---|
| `rudders` | A[Rudder] | 1 strings:  |  |
| `rudders[].air_density` | float | 0 .. 1.3 (med 1.3, n=187) |  |
| `rudders[].distance_to_hinge` | float | 0 .. 0 (med 0, n=187) |  |
| `rudders[].drag_coefficient` | float | 0 .. 20 (med 1, n=187) |  |
| `rudders[].frontal_area` | float | 0 .. 800 (med 6, n=187) |  |
| `rudders[].hinge_angles.pitch_deg` | float | -0.1 .. 0 (med 0, n=187) |  |
| `rudders[].hinge_angles.roll_deg` | float | 0 .. 90 (med 0, n=187) |  |
| `rudders[].hinge_angles.yaw_deg` | float | 0 .. 0 (med 0, n=187) |  |
| `rudders[].hinge_point[]` | float | -41 .. 44 (med 0, n=561) |  |
| `rudders[].lift_coefficient` | float | 0 .. 10 (med 2, n=187) |  |
| `rudders[].max_angle_deg` | float | 0 .. 20 (med 20, n=187) |  |
| `rudders[].min_angle_deg` | float | -20 .. 0 (med -20, n=187) |  |
| `rudders[].name` | string | 9 strings: Elevator, Fuselage Horizontal Drag, Fuselage Vertical Drag, Left Aileron (+5) |  |
| `rudders[].physics_component_name.hash` | uint32 | 0 .. 3.56797e+09 (med 0, n=187) |  |
| `rudders[].physics_component_name.string` | string | 8 strings: , Elevator, FuselageHorizontal, FuselageVertical (+4) |  |
| `rudders[].pitch_steering_factor` | float | 0 .. 1 (med 0, n=187) |  |
| `rudders[].roll_steering_factor` | float | -1 .. 1 (med 0, n=187) |  |
| `rudders[].turn_steering_factor` | float | 0 .. 1 (med 0, n=187) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.control_points[].x` | float | -2.52441e-29 .. 7.32541e+28 (med 1, n=3740) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.control_points[].y` | float | -2.52441e-29 .. 7.3254e+28 (med 0.5, n=3740) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.control_points[].y2` | float | -33.153 .. 7.32539e+28 (med 0, n=3740) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.number_of_control_points` | int8 | 2 .. 8 (med 2, n=187) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.x_max` | float | 500 .. 500 (med 500, n=187) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.x_min` | float | 0 .. 0 (med 0, n=187) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.y_max` | float | 1 .. 10 (med 10, n=187) |  |
| `rudders[].zero_angle_deg_vs_speed_kph.y_min` | float | -10 .. -3 (med -10, n=187) |  |

## `StuntAreas`

| member | type | fleet range | donor |
|---|---|---|---|
| `number_of_stunt_areas` | uint8 | 1 .. 11 (med 3, n=175) | 3 |
| `number_of_welding_info` | uint16 | 0 .. 29 (med 1, n=175) | 8 |
| `stunt_areas[].active` | uint16 | 0 .. 1 (med 0, n=5600) | 0 |
| `stunt_areas[].bounding_box_local.max_x` | float | -2.82759 .. 43.4207 (med 0.5, n=5600) | 0.5 |
| `stunt_areas[].bounding_box_local.max_y` | float | -0.0375938 .. 12.9519 (med 0.5, n=5600) | 0.5 |
| `stunt_areas[].bounding_box_local.max_z` | float | -17.5845 .. 47.9578 (med 0.5, n=5600) | 0.5 |
| `stunt_areas[].bounding_box_local.min_x` | float | -43.4207 .. 2.8276 (med -0.5, n=5600) | -0.5 |
| `stunt_areas[].bounding_box_local.min_y` | float | -0.5 .. 12.0556 (med -0.5, n=5600) | -0.5 |
| `stunt_areas[].bounding_box_local.min_z` | float | -24.0507 .. 33.637 (med -0.5, n=5600) | -0.5 |
| `stunt_areas[].center_local[]` | float | -22.7628 .. 40.7974 (med 0, n=16800) | 0 |
| `stunt_areas[].deform_points[]` | uint32 | 0 .. 345 (med 0, n=89600) | 0 |
| `stunt_areas[].edge_validity[]` | uint8 | 1 .. 1 (med 1, n=89600) | 1 |
| `stunt_areas[].name` | string | 3 strings: NoName, front_area, main_area | NoName |
| `stunt_areas[].name_hash` | uint32 | 0 .. 3.99853e+09 (med 0, n=5600) | 0 |
| `stunt_areas[].number_of_deform_points` | uint16 | 0 .. 16 (med 0, n=5600) | 0 |
| `stunt_areas[].number_of_triangles` | uint16 | 0 .. 14 (med 0, n=5600) | 0 |
| `stunt_areas[].part_hash` | uint32 | 0 .. 4.24458e+09 (med 0, n=5600) | 0 |
| `stunt_areas[].part_index` | uint32 | 0 .. 62 (med 0, n=5600) | 0 |
| `stunt_areas[].part_name` | string | 7 strings: NoName, armoredtruck_body, oldcampervan_body, oldjeep_body (+3) | NoName |
| `stunt_areas[].triangle_indices[]` | uint8 | 0 .. 15 (med 0, n=235200) | 0 |
| `stunt_areas[].vertices3D_local[]` | float | -43.4207 .. 47.9578 (med 0, n=268800) | 0 |
| `welding_info[].edge_a_index` | int16 | -1 .. 13 (med -1, n=11200) | -1 |
| `welding_info[].edge_b_index` | int16 | -1 .. 15 (med -1, n=11200) | -1 |
| `welding_info[].stunt_area_a_index` | int16 | -1 .. 10 (med -1, n=11200) | -1 |
| `welding_info[].stunt_area_b_index` | int16 | -1 .. 9 (med -1, n=11200) | -1 |

## `Suspension`

| member | type | fleet range | donor |
|---|---|---|---|
| `front.antirollbar_strength` | float | 0 .. 0.8 (med 0, n=167) | 0 |
| `front.compression` | float | 1 .. 6 (med 2, n=167) | 4 |
| `front.direction[]` | float | -1 .. 0 (med 0, n=501) | 0 |
| `front.hardpoint_offset_along_spring` | float | -0.375 .. 0.5 (med -0.1, n=167) | -0.0375000015 |
| `front.lateral_tire_force_offset` | float | 0 .. 1.5 (med 0.2, n=167) | 0.100000001 |
| `front.length` | float | 0.12 .. 1.5 (med 0.2, n=167) | 0.25 |
| `front.longitudinal_tire_force_offset` | float | 0 .. 0.2 (med 0, n=167) | 0 |
| `front.max_length_offset` | float | 0 .. 0 (med 0, n=167) | 0 |
| `front.max_velocity_for_damp_clamp` | float | 1.5 .. 1500 (med 1.5, n=167) | 1.5 |
| `front.min_length` | float | 0 .. 0 (med 0, n=167) | 0 |
| `front.raycast_offset` | float | 0 .. 0 (med 0, n=167) | 0 |
| `front.relaxation` | float | 2 .. 15 (med 5, n=167) | 7 |
| `front.strength` | float | 4 .. 80 (med 30, n=167) | 40 |
| `front.tire_drag_force_offset` | float | 0 .. 0 (med 0, n=167) | 0 |
| `rear.antirollbar_strength` | float | 0 .. 0.8 (med 0, n=167) | 0 |
| `rear.compression` | float | 1 .. 6 (med 2, n=167) | 3 |
| `rear.direction[]` | float | -1 .. 0 (med 0, n=501) | 0 |
| `rear.hardpoint_offset_along_spring` | float | -0.375 .. 0.5 (med -0.1, n=167) | -0.042857144 |
| `rear.lateral_tire_force_offset` | float | 0 .. 1.5 (med 0.2, n=167) | 0.0500000007 |
| `rear.length` | float | 0.1 .. 1.5 (med 0.2, n=167) | 0.25 |
| `rear.longitudinal_tire_force_offset` | float | 0 .. 0.2 (med 0, n=167) | 0 |
| `rear.max_length_offset` | float | 0 .. 0 (med 0, n=167) | 0 |
| `rear.max_velocity_for_damp_clamp` | float | 1.5 .. 10000 (med 1.5, n=167) | 1.5 |
| `rear.min_length` | float | 0 .. 0 (med 0, n=167) | 0 |
| `rear.raycast_offset` | float | 0 .. 0 (med 0, n=167) | 0 |
| `rear.relaxation` | float | 2 .. 20 (med 8, n=167) | 4 |
| `rear.strength` | float | 4 .. 100 (med 30, n=167) | 35 |
| `rear.tire_drag_force_offset` | float | 0 .. 0 (med 0, n=167) | 0 |
| `wheel_hardpoint_offsets` | A[WheelHardpointOffset] | 1 strings:  |  |
| `wheel_hardpoint_offsets[].offset[]` | float | -0.75 .. 0.75 (med 0, n=2187) | 0 |
| `wheel_hardpoint_offsets[].wheel_index` | int32 | 0 .. 9 (med 2, n=729) | 3 |

## `Tire`

| member | type | fleet range | donor |
|---|---|---|---|
| `brake_long_tire_0_sa.control_points[].x` | float | -4.21169 .. 3.07852e+34 (med 0.158974, n=2900) | -4.21168518 |
| `brake_long_tire_0_sa.control_points[].y` | float | -126.519 .. 3.07849e+34 (med 0.572222, n=2900) | 0.166666672 |
| `brake_long_tire_0_sa.control_points[].y2` | float | -120.703 .. 3.07849e+34 (med 0, n=2900) | 0.78125 |
| `brake_long_tire_0_sa.number_of_control_points` | int8 | 6 .. 7 (med 6, n=290) | 6 |
| `brake_long_tire_0_sa.x_max` | float | 0.5 .. 1 (med 0.5, n=290) | 1 |
| `brake_long_tire_0_sa.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `brake_long_tire_0_sa.y_max` | float | 1 .. 3.2 (med 1, n=290) | 3.20000005 |
| `brake_long_tire_0_sa.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `brake_long_tire_peak_sa.control_points[].x` | float | -3.85186e-34 .. 2.85387e+34 (med 0.125933, n=2900) | 0 |
| `brake_long_tire_peak_sa.control_points[].y` | float | -3.85186e-34 .. 2.85387e+34 (med 0.466667, n=2900) | 0 |
| `brake_long_tire_peak_sa.control_points[].y2` | float | -168.171 .. 2.85386e+34 (med 0, n=2900) | 0 |
| `brake_long_tire_peak_sa.number_of_control_points` | int8 | 7 .. 9 (med 8, n=290) | 9 |
| `brake_long_tire_peak_sa.x_max` | float | 0.75 .. 1 (med 0.75, n=290) | 1 |
| `brake_long_tire_peak_sa.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `brake_long_tire_peak_sa.y_max` | float | 1 .. 3 (med 1, n=290) | 3 |
| `brake_long_tire_peak_sa.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `brake_long_tire_sat_sa.control_points[].x` | float | -3.86675e-34 .. 2.7988e+34 (med 0.186985, n=2900) | 0 |
| `brake_long_tire_sat_sa.control_points[].y` | float | -90.0954 .. 2.7988e+34 (med 0.671875, n=2900) | 0 |
| `brake_long_tire_sat_sa.control_points[].y2` | float | -167.954 .. 2.7988e+34 (med 0, n=2900) | 0 |
| `brake_long_tire_sat_sa.number_of_control_points` | int8 | 6 .. 9 (med 9, n=290) | 9 |
| `brake_long_tire_sat_sa.x_max` | float | 1 .. 1 (med 1, n=290) | 1 |
| `brake_long_tire_sat_sa.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `brake_long_tire_sat_sa.y_max` | float | 0.5 .. 3 (med 1, n=290) | 3 |
| `brake_long_tire_sat_sa.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `brake_peak_sr` | float | -0.8 .. -0.1 (med -0.8, n=290) | -0.200000003 |
| `brake_sat_sr` | float | -0.98 .. -0.4 (med -0.95, n=290) | -0.949999988 |
| `full_friction_camber_angle_deg` | float | 4 .. 75 (med 75, n=290) | 10 |
| `fwd_long_tire_0_sa.control_points[].x` | float | -9.86076e-32 .. 3.84406e+08 (med 0.182278, n=2900) | -3.85185989e-34 |
| `fwd_long_tire_0_sa.control_points[].y` | float | -9.86076e-32 .. 2.7329e+08 (med 0.767708, n=2900) | -3.85185989e-34 |
| `fwd_long_tire_0_sa.control_points[].y2` | float | -148.974 .. 2.73291e+08 (med 0, n=2900) | 0 |
| `fwd_long_tire_0_sa.number_of_control_points` | int8 | 7 .. 9 (med 8, n=290) | 8 |
| `fwd_long_tire_0_sa.x_max` | float | 1 .. 2 (med 2, n=290) | 2 |
| `fwd_long_tire_0_sa.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `fwd_long_tire_0_sa.y_max` | float | 0.95 .. 3.2 (med 1, n=290) | 3.20000005 |
| `fwd_long_tire_0_sa.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `fwd_long_tire_peak_sa.control_points[].x` | float | -9.922e-32 .. 6.28785e+13 (med 0.23038, n=2900) | -3.85185989e-34 |
| `fwd_long_tire_peak_sa.control_points[].y` | float | -126.519 .. 6.28784e+13 (med 0.663889, n=2900) | -3.85185989e-34 |
| `fwd_long_tire_peak_sa.control_points[].y2` | float | -152.716 .. 6.28784e+13 (med 1.4013e-45, n=2900) | -9.86076132e-32 |
| `fwd_long_tire_peak_sa.number_of_control_points` | int8 | 5 .. 8 (med 8, n=290) | 8 |
| `fwd_long_tire_peak_sa.x_max` | float | 1 .. 2 (med 2, n=290) | 2 |
| `fwd_long_tire_peak_sa.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `fwd_long_tire_peak_sa.y_max` | float | 0.75 .. 3.2 (med 0.85, n=290) | 3.20000005 |
| `fwd_long_tire_peak_sa.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `fwd_long_tire_sat_sa.control_points[].x` | float | -120.703 .. 5.99772e+22 (med 0.348718, n=2900) | -9.86076132e-32 |
| `fwd_long_tire_sat_sa.control_points[].y` | float | -33.0629 .. 5.99772e+22 (med 0.615972, n=2900) | -9.86076132e-32 |
| `fwd_long_tire_sat_sa.control_points[].y2` | float | -29.5653 .. 5.99772e+22 (med 0, n=2900) | -3.85185989e-34 |
| `fwd_long_tire_sat_sa.number_of_control_points` | int8 | 4 .. 10 (med 6, n=290) | 7 |
| `fwd_long_tire_sat_sa.x_max` | float | 1 .. 2 (med 2, n=290) | 1 |
| `fwd_long_tire_sat_sa.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `fwd_long_tire_sat_sa.y_max` | float | 0.2 .. 3 (med 0.6, n=290) | 0.5 |
| `fwd_long_tire_sat_sa.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `fwd_peak_sr` | float | 0.4 .. 9 (med 0.4, n=290) | 0.5 |
| `fwd_sat_sr` | float | 1 .. 10 (med 1, n=290) | 2 |
| `lat_peak_sa_deg` | float | 8 .. 15 (med 12, n=290) | 12 |
| `lat_sat_sa_deg` | float | 15 .. 25 (med 20, n=290) | 20 |
| `lat_tire_0_sr.control_points[].x` | float | -9.86076e-32 .. 1 (med 0.195618, n=2900) | -3.85185989e-34 |
| `lat_tire_0_sr.control_points[].y` | float | -9.86076e-32 .. 1 (med 0.708333, n=2900) | -3.85185989e-34 |
| `lat_tire_0_sr.control_points[].y2` | float | -360.019 .. 2.73751 (med 0, n=2900) | -3.85185989e-34 |
| `lat_tire_0_sr.number_of_control_points` | int8 | 7 .. 10 (med 8, n=290) | 8 |
| `lat_tire_0_sr.x_max` | float | 20 .. 30 (med 25, n=290) | 20 |
| `lat_tire_0_sr.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_0_sr.y_max` | float | 1 .. 3.35 (med 1, n=290) | 3.3499999 |
| `lat_tire_0_sr.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_brake_peak_sr.control_points[].x` | float | -9.86076e-32 .. 1.02983e+37 (med 0.173126, n=2900) | -3.85185989e-34 |
| `lat_tire_brake_peak_sr.control_points[].y` | float | -9.86076e-32 .. 1.02983e+37 (med 0.794444, n=2900) | -3.85185989e-34 |
| `lat_tire_brake_peak_sr.control_points[].y2` | float | -269.142 .. 1.02983e+37 (med 0, n=2900) | -3.85185989e-34 |
| `lat_tire_brake_peak_sr.number_of_control_points` | int8 | 7 .. 8 (med 8, n=290) | 8 |
| `lat_tire_brake_peak_sr.x_max` | float | 15 .. 25 (med 20, n=290) | 20 |
| `lat_tire_brake_peak_sr.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_brake_peak_sr.y_max` | float | 0.9 .. 3 (med 1, n=290) | 2.5999999 |
| `lat_tire_brake_peak_sr.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_brake_sat_sr.control_points[].x` | float | -9.89424e-32 .. 2.61371e+29 (med 0.312821, n=2900) | -3.85185989e-34 |
| `lat_tire_brake_sat_sr.control_points[].y` | float | -9.87043e-32 .. 1 (med 0.670833, n=2900) | -3.85185989e-34 |
| `lat_tire_brake_sat_sr.control_points[].y2` | float | -170.92 .. 4.67969 (med -0.10875, n=2900) | 0 |
| `lat_tire_brake_sat_sr.number_of_control_points` | int8 | 7 .. 9 (med 8, n=290) | 8 |
| `lat_tire_brake_sat_sr.x_max` | float | 15 .. 45 (med 35, n=290) | 45 |
| `lat_tire_brake_sat_sr.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_brake_sat_sr.y_max` | float | 0.3 .. 2.2 (med 1, n=290) | 1.79999995 |
| `lat_tire_brake_sat_sr.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_fwd_peak_sr.control_points[].x` | float | -3.85316e-34 .. 6.03929e+15 (med 0.191561, n=2900) | -3.85316028e-34 |
| `lat_tire_fwd_peak_sr.control_points[].y` | float | -3.87153e-34 .. 6.03932e+15 (med 0.664931, n=2900) | -3.85352762e-34 |
| `lat_tire_fwd_peak_sr.control_points[].y2` | float | -30.1494 .. 2.10063 (med -0.41179, n=2900) | -3.85389496e-34 |
| `lat_tire_fwd_peak_sr.number_of_control_points` | int8 | 8 .. 9 (med 8, n=290) | 8 |
| `lat_tire_fwd_peak_sr.x_max` | float | 15 .. 35 (med 25, n=290) | 20 |
| `lat_tire_fwd_peak_sr.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_fwd_peak_sr.y_max` | float | 0.7 .. 3.1 (med 0.85, n=290) | 3.0999999 |
| `lat_tire_fwd_peak_sr.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_fwd_sat_sr.control_points[].x` | float | -31.897 .. 6.49165e+06 (med 0.261344, n=2900) | -31.8970108 |
| `lat_tire_fwd_sat_sr.control_points[].y` | float | -3.9443e-31 .. 6.49171e+06 (med 0.569097, n=2900) | 0 |
| `lat_tire_fwd_sat_sr.control_points[].y2` | float | -51.9314 .. 6.49165e+06 (med -0.137687, n=2900) | 0.40625 |
| `lat_tire_fwd_sat_sr.number_of_control_points` | int8 | 6 .. 10 (med 8, n=290) | 6 |
| `lat_tire_fwd_sat_sr.x_max` | float | 15 .. 45 (med 45, n=290) | 45 |
| `lat_tire_fwd_sat_sr.x_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `lat_tire_fwd_sat_sr.y_max` | float | 0.5 .. 2.5 (med 0.6, n=290) | 1.5 |
| `lat_tire_fwd_sat_sr.y_min` | float | 0 .. 0 (med 0, n=290) | 0 |
| `no_friction_camber_angle_deg` | float | 15 .. 150 (med 150, n=290) | 35 |
| `wheel_load_responsiveness` | float | 0.05 .. 0.3 (med 0.05, n=290) | 0.200000003 |

## `TrainAudio`

| member | type | fleet range | donor |
|---|---|---|---|
| `load_smoothing` | float | 0.1 .. 0.1 (med 0.1, n=12) |  |
| `max_rpm_vs_speed.control_points[].x` | float | 0 .. 3.41359e+31 (med 3.41359e+31, n=60) |  |
| `max_rpm_vs_speed.control_points[].y` | float | 0.7 .. 3.4136e+31 (med 3.4136e+31, n=60) |  |
| `max_rpm_vs_speed.control_points[].y2` | float | 0 .. 3.4136e+31 (med 3.4136e+31, n=60) |  |
| `max_rpm_vs_speed.number_of_control_points` | int8 | 2 .. 2 (med 2, n=12) |  |
| `max_rpm_vs_speed.x_max` | float | 50 .. 50 (med 50, n=12) |  |
| `max_rpm_vs_speed.x_min` | float | 0 .. 0 (med 0, n=12) |  |
| `max_rpm_vs_speed.y_max` | float | 1 .. 1 (med 1, n=12) |  |
| `max_rpm_vs_speed.y_min` | float | 0 .. 0 (med 0, n=12) |  |
| `min_rpm_vs_speed.control_points[].x` | float | 0 .. 3.41359e+31 (med 3.41359e+31, n=60) |  |
| `min_rpm_vs_speed.control_points[].y` | float | 0.1 .. 3.4136e+31 (med 3.4136e+31, n=60) |  |
| `min_rpm_vs_speed.control_points[].y2` | float | 0 .. 3.4136e+31 (med 3.4136e+31, n=60) |  |
| `min_rpm_vs_speed.number_of_control_points` | int8 | 2 .. 2 (med 2, n=12) |  |
| `min_rpm_vs_speed.x_max` | float | 50 .. 50 (med 50, n=12) |  |
| `min_rpm_vs_speed.x_min` | float | 0 .. 0 (med 0, n=12) |  |
| `min_rpm_vs_speed.y_max` | float | 1 .. 1 (med 1, n=12) |  |
| `min_rpm_vs_speed.y_min` | float | 0 .. 0 (med 0, n=12) |  |
| `rpm_smoothing` | float | 0.1 .. 0.1 (med 0.1, n=12) |  |

## `TrainGlobal`

| member | type | fleet range | donor |
|---|---|---|---|
| `crashing_impulse` | float | 100000 .. 100000 (med 100000, n=12) |  |
| `derailing_explosion_damage` | int32 | 75 .. 75 (med 75, n=12) |  |
| `drag` | float | 0.01 .. 0.01 (med 0.01, n=12) |  |
| `max_acceleration_vs_speed.control_points[].x` | float | 0 .. 3.41359e+31 (med 3.41359e+31, n=60) |  |
| `max_acceleration_vs_speed.control_points[].y` | float | 0.5 .. 3.4136e+31 (med 3.4136e+31, n=60) |  |
| `max_acceleration_vs_speed.control_points[].y2` | float | 0 .. 3.4136e+31 (med 3.4136e+31, n=60) |  |
| `max_acceleration_vs_speed.number_of_control_points` | int8 | 2 .. 2 (med 2, n=12) |  |
| `max_acceleration_vs_speed.x_max` | float | 50 .. 50 (med 50, n=12) |  |
| `max_acceleration_vs_speed.x_min` | float | 0 .. 0 (med 0, n=12) |  |
| `max_acceleration_vs_speed.y_max` | float | 20 .. 20 (med 20, n=12) |  |
| `max_acceleration_vs_speed.y_min` | float | 0 .. 0 (med 0, n=12) |  |
| `max_angle_to_derail` | float | 8 .. 8 (med 8, n=12) |  |
| `max_deceleration` | float | 80 .. 80 (med 80, n=12) |  |

## `Transmission`

| member | type | fleet range | donor |
|---|---|---|---|
| `clutch_delay` | float | 0.05 .. 0.5 (med 0.2, n=145) | 0.100000001 |
| `decay_time_to_cruise_rpm` | float | -1 .. 10 (med -1, n=145) | 5 |
| `downshift_rpm[]` | float | 0 .. 8400 (med 1600, n=1160) | 0 |
| `final_drive` | float | -1 .. 37.33 (med 3.92, n=145) | 3.91000009 |
| `forward_ratio_percentage` | float | 0 .. 100 (med 0, n=145) | 0 |
| `gear_ratios[]` | float | 0 .. 10.63 (med 1, n=1160) | 0 |
| `gears` | int32 | 1 .. 8 (med 5, n=145) | 6 |
| `low_gear_forward_ratio_pct` | float | 0 .. 100 (med 50, n=145) | 50 |
| `low_gears_final_drive` | float | -1 .. 30 (med -1, n=145) | -1 |
| `manual_clutch` | int32 | -1 .. 0 (med 0, n=145) | 0 |
| `manual_clutch_blend_rpm` | float | 3000 .. 6500 (med 5000, n=145) | 5000 |
| `manual_clutch_blend_time` | float | 0 .. 0 (med 0, n=145) | 0 |
| `nitrous_gears` | int32 | 0 .. 2 (med 0, n=145) | 0 |
| `reverse_gear_ratio` | float | 1 .. 12.04 (med 3.21, n=145) | 2.3900001 |
| `reverse_uses_forward_gears` | int32 | 0 .. 0 (med 0, n=145) | 0 |
| `sequential` | int32 | 0 .. 1 (med 1, n=145) | 1 |
| `target_cruise_rpm` | float | 1000 .. 3000 (med 2000, n=145) | 2400 |
| `top_speed` | float | 90 .. 505 (med 150, n=145) | 320 |
| `upshift_rpm[]` | float | 0 .. 1e+07 (med 3200, n=1160) | 0 |

## `VehicleCommon`

| member | type | fleet range | donor |
|---|---|---|---|
| `all_door_part_properties` | A[DoorPartProperties] | 1 strings:  |  |
| `all_door_part_properties[].name.hash` | uint32 | 2.46453e+07 .. 3.42067e+09 (med 1.63983e+09, n=3248) | 2754955073 |
| `all_door_part_properties[].name.string` | string | 14 strings: CargoBayDoor, CenterLeftDoor, CenterRightDoor, FrontLeftDoor (+10) | MissileHatch |
| `all_fin_part_properties` | A[FinPartProperties] | 1 strings:  |  |
| `all_fin_part_properties[].name.hash` | uint32 | 1.92505e+09 .. 1.92505e+09 (med 1.92505e+09, n=232) | 1925053179 |
| `all_fin_part_properties[].name.string` | string | 1 strings: BoatRudder | BoatRudder |
| `all_hinged_part_properties` | A[HingedPartProperties] | 1 strings:  |  |
| `all_hinged_part_properties[].lod` | int8 | 0 .. 1 (med 1, n=5800) | 1 |
| `all_hinged_part_properties[].name.hash` | uint32 | 2.4019e+08 .. 4.28835e+09 (med 2.68991e+09, n=5800) | 3130390193 |
| `all_hinged_part_properties[].name.string` | string | 25 strings: AirBrake, BoatEngine, Elevator, Flaps (+21) | FrontRightTibia |
| `all_hinged_part_properties[].target_position_variable.hash` | uint32 | 1.24006e+08 .. 4.26673e+09 (med 2.7038e+09, n=5800) | 2703802677 |
| `all_hinged_part_properties[].target_position_variable.string` | string | 24 strings: air_brakes_T, elevon_left_T, elevon_right_T, flaps_T (+20) | front_right_tibia_t |
| `all_hinged_part_properties[].use_target_position_as_angle` | int8 | 0 .. 1 (med 0, n=5800) | 0 |
| `all_propeller_part_properties` | A[PropellerPartProperties] | 1 strings:  |  |
| `all_propeller_part_properties[].name.hash` | uint32 | 2.05975e+07 .. 2.05975e+07 (med 2.05975e+07, n=232) | 20597522 |
| `all_propeller_part_properties[].name.string` | string | 1 strings: Propeller | Propeller |
| `all_rotating_part_properties` | A[RotatingPartProperties] | 1 strings:  |  |
| `all_rotating_part_properties[].inverted` | int8 | 0 .. 1 (med 0, n=2784) | 0 |
| `all_rotating_part_properties[].name.hash` | uint32 | 2.05975e+07 .. 4.24969e+09 (med 1.58885e+09, n=2784) | 1588853057 |
| `all_rotating_part_properties[].name.string` | string | 12 strings: EngineRotatingPart, GatlingGun, LeftRotor, MainRotor (+8) | OuterRightRotor |
| `all_rotating_part_properties[].number_of_water_collision_sensors` | int8 | 0 .. 5 (med 3, n=2784) | 3 |
| `all_rotating_part_properties[].rotoscope_enabled` | int8 | 0 .. 1 (med 1, n=2784) | 1 |
| `all_rotating_part_properties[].rotoscope_rpm_per_cycle` | float | 20 .. 50 (med 20, n=2784) | 50 |
| `all_rotating_part_properties[].rpm_variable.hash` | uint32 | 2.63945e+07 .. 4.03535e+09 (med 3.79323e+09, n=2784) | 3793226054 |
| `all_rotating_part_properties[].rpm_variable.string` | string | 8 strings: engine_rpm, main_rotor_rpm, propeller_rpm, radar_fast_rpm (+4) | rotor_rpm |
| `all_rotating_part_properties[].special_collision_enabled` | int8 | 0 .. 1 (med 1, n=2784) | 1 |
| `all_spring_part_properties` | A[SpringPartProperties] | 1 strings:  |  |
| `all_spring_part_properties[].name.hash` | uint32 | 9.45391e+08 .. 9.45391e+08 (med 9.45391e+08, n=232) | 945390958 |
| `all_spring_part_properties[].name.string` | string | 1 strings: Spring | Spring |
| `all_vehicles_common.high_up_in_air_height` | float | 10 .. 10 (med 10, n=232) | 10 |
| `all_vehicles_common.radar_rpm_fast` | float | 60 .. 60 (med 60, n=232) | 60 |
| `all_vehicles_common.radar_rpm_slow` | float | 30 .. 30 (med 30, n=232) | 30 |
| `all_wheel_part_properties` | A[WheelPartProperties] | 1 strings:  |  |
| `all_wheel_part_properties[].name.hash` | uint32 | 8.74198e+07 .. 3.98533e+09 (med 3.87607e+09, n=928) | 883474233 |
| `all_wheel_part_properties[].name.string` | string | 4 strings: BrakeCalipers, BrakeDisc, BrakeDrum, Wheel | BrakeDrum |
| `boat_common.crash_in_air_min_vel_change_ms` | float | 5 .. 5 (med 5, n=232) | 5 |
| `boat_common.crash_min_vel_change_ms` | float | 20 .. 20 (med 20, n=232) | 20 |
| `boat_common.engine_shut_down_delay_s` | float | 5 .. 5 (med 5, n=232) | 5 |
| `car_common.crash_in_air_min_vel_change_ms` | float | 5 .. 5 (med 5, n=232) | 5 |
| `car_common.crash_min_vel_change_ms` | float | 20 .. 20 (med 20, n=232) | 20 |
| `car_common.engine_shut_down_delay_s` | float | 30 .. 30 (med 30, n=232) | 30 |
| `damage_from_parts[].damage_ratio_from_broken_off` | float | 1 .. 1 (med 1, n=3016) | 1 |
| `damage_from_parts[].damage_ratio_from_damaged` | float | 0 .. 0 (med 0, n=3016) | 0 |
| `damage_from_parts[].damage_ratio_from_loose` | float | 0 .. 0.95 (med 0.95, n=3016) | 0 |
| `damage_from_parts[].part_behavior.hash` | uint32 | 2.63551e+08 .. 4.24969e+09 (med 1.79005e+09, n=3016) | 1588853057 |
| `damage_from_parts[].part_behavior.string` | string | 13 strings: Elevator, LeftAileron, LeftRotor, LeftWing (+9) | OuterRightRotor |
| `damageable_physics_components[].damage_from_parts` | A[PhysicsComponentDamageFromPart] | 1 strings:  |  |
| `damageable_physics_components[].physics_component_name.hash` | uint32 | 2.63551e+08 .. 4.24969e+09 (med 1.79005e+09, n=3016) | 1588853057 |
| `damageable_physics_components[].physics_component_name.string` | string | 13 strings: Elevator, LeftAileron, LeftRotor, LeftWing (+9) | OuterRightRotor |
| `helicopter_common.crash_in_air_min_vel_change_ms` | float | 5 .. 5 (med 5, n=232) | 5 |
| `helicopter_common.crash_min_vel_change_ms` | float | 20 .. 20 (med 20, n=232) | 20 |
| `helicopter_common.engine_shut_down_delay_s` | float | 5 .. 5 (med 5, n=232) | 5 |
| `motorbike_common.animation_max_roll_error_deg` | float | 5 .. 5 (med 5, n=232) | 5 |
| `motorbike_common.animation_roll_pid_d` | float | 0.8 .. 0.8 (med 0.8, n=232) | 0.800000012 |
| `motorbike_common.animation_roll_pid_i` | float | 0.5 .. 0.5 (med 0.5, n=232) | 0.5 |
| `motorbike_common.animation_roll_pid_p` | float | 15 .. 15 (med 15, n=232) | 15 |
| `motorbike_common.crash_in_air_min_vel_change_ms` | float | 5 .. 5 (med 5, n=232) | 5 |
| `motorbike_common.crash_min_vel_change_ms` | float | 15 .. 15 (med 15, n=232) | 15 |
| `motorbike_common.engine_shut_down_delay_s` | float | 5 .. 5 (med 5, n=232) | 5 |
| `motorbike_common.roll_rate_to_fall_degs` | float | 800 .. 800 (med 800, n=232) | 800 |
| `motorbike_common.roll_to_fall_no_driver_deg` | float | 50 .. 50 (med 50, n=232) | 50 |
| `motorbike_common.roll_to_fall_with_driver_deg` | float | 80 .. 80 (med 80, n=232) | 80 |
| `plane_common.crash_in_air_min_vel_change_ms` | float | 5 .. 5 (med 5, n=232) | 5 |
| `plane_common.crash_min_vel_change_ms` | float | 20 .. 20 (med 20, n=232) | 20 |
| `plane_common.engine_shut_down_delay_s` | float | 5 .. 5 (med 5, n=232) | 5 |
| `rotor_collision.damage_to_other_per_second` | float | 100000 .. 100000 (med 100000, n=232) | 100000 |
| `rotor_collision.light_object_mass_ratio` | float | 0.02 .. 0.02 (med 0.02, n=232) | 0.0199999996 |
| `rotor_collision.mass_ratio_when_no_mass` | float | 0.1 .. 0.1 (med 0.1, n=232) | 0.100000001 |
| `rotor_collision.min_rpm` | float | 30 .. 30 (med 30, n=232) | 30 |
| `tire_effects.effect_frame_delay_notyre` | uint8 | 5 .. 5 (med 5, n=232) | 5 |
| `tire_effects.effect_frame_delay_roll` | uint8 | 3 .. 3 (med 3, n=232) | 3 |
| `tire_effects.effect_frame_delay_skid` | uint8 | 5 .. 5 (med 5, n=232) | 5 |
| `tire_effects.effect_frame_delay_spin` | uint8 | 3 .. 3 (med 3, n=232) | 3 |
| `tire_effects.effect_frame_hold_notyre` | uint8 | 2 .. 2 (med 2, n=232) | 2 |
| `tire_effects.effect_frame_hold_roll` | uint8 | 2 .. 2 (med 2, n=232) | 2 |
| `tire_effects.effect_frame_hold_skid` | uint8 | 2 .. 2 (med 2, n=232) | 2 |
| `tire_effects.effect_frame_hold_spin` | uint8 | 2 .. 2 (med 2, n=232) | 2 |
| `tire_effects.max_slip_velocity_notyre_eff` | float | 10 .. 10 (med 10, n=232) | 10 |
| `tire_effects.min_skid_for_effect_front` | float | 0.01 .. 0.01 (med 0.01, n=232) | 0.00999999978 |
| `tire_effects.min_skid_for_effect_rear` | float | 0.01 .. 0.01 (med 0.01, n=232) | 0.00999999978 |
| `tire_effects.min_skid_velocity_for_skid_ms` | float | 0.5 .. 0.5 (med 0.5, n=232) | 0.5 |
| `tire_effects.min_slip_velocity_for_spin_ms` | float | 1 .. 1 (med 1, n=232) | 1 |
| `tire_effects.min_slip_velocity_notyre_eff` | float | 2 .. 2 (med 2, n=232) | 2 |
| `tire_effects.min_spin_for_effect_front` | float | 0.3 .. 0.3 (med 0.3, n=232) | 0.300000012 |
| `tire_effects.min_spin_for_effect_rear` | float | 0.1 .. 0.1 (med 0.1, n=232) | 0.100000001 |
| `tire_effects.min_spin_velocity_roll_effect` | float | 20 .. 20 (med 20, n=232) | 20 |
| `tire_effects.skid_effect_drift_boost` | float | 3 .. 3 (med 3, n=232) | 3 |
| `tire_effects.skid_velocity_scale` | float | 0.25 .. 0.25 (med 0.25, n=232) | 0.25 |
| `tire_effects.slip_angle_to_peak_to_skid` | float | 0.8 .. 0.8 (med 0.8, n=232) | 0.800000012 |
| `tire_effects.slip_effect_drift_boost` | float | 1.5 .. 1.5 (med 1.5, n=232) | 1.5 |
| `tire_effects.slip_ratio_to_peak_to_spin` | float | 0.5 .. 0.5 (med 0.5, n=232) | 0.5 |
| `tire_effects.slip_velocity_scale` | float | 0.25 .. 0.25 (med 0.25, n=232) | 0.25 |
| `train_common.ambient_traffic_speed_kmph` | float | 125 .. 125 (med 125, n=232) | 125 |
| `train_common.cruise_control_responsiveness` | float | 0.1 .. 0.1 (med 0.1, n=232) | 0.100000001 |
| `train_common.train_track_width_scale` | float | 0.7 .. 0.7 (med 0.7, n=232) | 0.699999988 |
| `vehicle_damage.damageable_physics_components` | A[DamageablePhysicsComponent] | 1 strings:  |  |
| `vehicle_damage.fatal_water_entry_floating_ms` | float | 50 .. 50 (med 50, n=232) | 50 |
| `vehicle_damage.fatal_water_entry_ms` | float | 20 .. 20 (med 20, n=232) | 20 |
| `vehicle_damage.fire_spreading_speed_ms` | float | 1.5 .. 1.5 (med 1.5, n=232) | 1.5 |
| `vehicle_damage.in_air_vulnerability_duration` | float | 2 .. 2 (med 2, n=232) | 2 |
| `vehicle_damage.min_water_entry_floating_ms` | float | 20 .. 20 (med 20, n=232) | 20 |
| `vehicle_damage.min_water_entry_ms` | float | 10 .. 10 (med 10, n=232) | 10 |

## `VehicleDamage`

| member | type | fleet range | donor |
|---|---|---|---|
| `bullet_armor` | int32 | 0 .. 5000 (med 0, n=233) | 0 |
| `bullet_armor_strength` | float | 0 .. 99 (med 0, n=233) | 0 |
| `bullet_heavy_armor` | int32 | 0 .. 100 (med 0, n=233) | 0 |
| `bullet_heavy_armor_strength` | float | 0 .. 50 (med 0, n=233) | 0 |
| `burn_duration_s` | uint16 | 20 .. 20 (med 20, n=233) | 20 |
| `burn_threshold` | uint16 | 50 .. 250 (med 100, n=233) | 80 |
| `deform_scale` | float | 1 .. 2 (med 1, n=233) | 1 |
| `electricity_armor` | int32 | -1 .. 0 (med 0, n=233) | 0 |
| `electricity_armor_strength` | float | 0 .. 100 (med 0, n=233) | 0 |
| `explosion_armor` | int32 | 0 .. 250 (med 0, n=233) | 0 |
| `explosion_armor_strength` | float | 0 .. 100 (med 0, n=233) | 0 |
| `explosion_delay_s` | uint16 | 5 .. 10 (med 8, n=233) | 8 |
| `explosion_threshold` | int32 | 500 .. 4000 (med 1000, n=233) | 700 |
| `fire_armor` | int32 | 0 .. 0 (med 0, n=233) | 0 |
| `fire_armor_strength` | float | 0 .. 0 (med 0, n=233) | 0 |
| `grapple_pull_armor` | int32 | -1 .. 0 (med 0, n=233) | 0 |
| `grapple_pull_armor_strength` | float | 0 .. 100 (med 0, n=233) | 0 |
| `impact_armor` | int32 | 0 .. 5 (med 0, n=233) | 0 |
| `impact_armor_strength` | float | 0 .. 100 (med 0, n=233) | 0 |
| `impact_damage_factor` | float | 1 .. 12 (med 1, n=233) | 1 |
| `impact_deform_threshold` | int32 | 0 .. 0 (med 0, n=233) | 0 |
| `max_health` | int32 | 500 .. 4000 (med 700, n=233) | 700 |
| `melee_armor` | int32 | 0 .. 0 (med 0, n=233) | 0 |
| `melee_armor_strength` | float | 0 .. 0 (med 0, n=233) | 0 |
| `npc_explosion_threshold` | int32 | 500 .. 4000 (med 1000, n=233) | 700 |
| `part_damage_types` | A[PartDamageType] | 1 strings:  |  |
| `part_damage_types[].damaged_health` | int32 | 0 .. 1500 (med 30, n=4820) | 0 |
| `part_damage_types[].damages_owning_vehicle` | int8 | 0 .. 1 (med 1, n=4820) | 1 |
| `part_damage_types[].initial_health` | int32 | 50 .. 10000 (med 300, n=4820) | 200 |
| `part_damage_types[].instantly_broken_by_bullets` | int8 | 0 .. 0 (med 0, n=4820) | 0 |
| `part_damage_types[].instantly_damaged_by_bullets` | int8 | 0 .. 1 (med 0, n=4820) | 0 |
| `part_damage_types[].instantly_loosened_by_bullets` | int8 | 0 .. 0 (med 0, n=4820) | 0 |
| `part_damage_types[].loosen_health` | int32 | 0 .. 500 (med 50, n=4820) | 50 |
| `part_damage_types[].type.hash` | uint32 | 5.54723e+06 .. 4.28232e+09 (med 2.52747e+09, n=4820) | 2987839894 |
| `part_damage_types[].type.string` | string | 24 strings: Default, Land_Antenna, Land_Axle, Land_Back_Gate (+20) | Land_Grill |
| `smoke_threshold` | uint16 | 200 .. 1050 (med 250, n=233) | 200 |
| `vulnerable_duration_s` | uint16 | 5 .. 5 (med 5, n=233) | 5 |
| `vulnerable_explosion_threshold` | int32 | 10 .. 100 (med 35, n=233) | 35 |
| `weapon_deform_threshold` | int32 | 0 .. 0 (med 0, n=233) | 0 |

## `VehicleDynamicLights`

| member | type | fleet range | donor |
|---|---|---|---|
| `lights` | A[VehicleDynamicLight] | 1 strings:  |  |
| `lights[].angle` | float | 10 .. 50 (med 10, n=3217) | 40 |
| `lights[].behavior` | string | 6 strings: HeadLight, LeftSignal, None, Reverse (+2) | HeadLight |
| `lights[].behavior_hash` | uint32 | 6.12583e+08 .. 4.25361e+09 (med 1.21967e+09, n=3217) | 3460580079 |
| `lights[].blinking` | int32 | 0 .. 1 (med 0, n=3217) | 0 |
| `lights[].cast_shadows` | int8 | 0 .. 1 (med 0, n=3217) | 0 |
| `lights[].deformable_transform` | string | 146 strings: |armoredtruck_LOD1|body|dash_LIG, |armoredtruck_LOD1|body|front_primary_LIG, |armoredtruck_LOD1|body|headlight_f_l|headlight_f_l_LIG, |armoredtruck_LOD1|body|headlight_f_l|point_headlight_f_l_LIG (+142) | |sportsmuscle_LOD1|body|engine|fender_r|headlight_f_r_01|headlight_f_r_01_LIG |
| `lights[].deformable_transform_hash` | uint32 | 2.55359e+06 .. 4.27985e+09 (med 2.18e+09, n=3217) | 2351519326 |
| `lights[].diffuse.B` | float | 0 .. 1 (med 1, n=3217) | 1 |
| `lights[].diffuse.G` | float | 0 .. 1 (med 1, n=3217) | 0.913999975 |
| `lights[].diffuse.R` | float | 0 .. 1 (med 1, n=3217) | 0.713 |
| `lights[].falloff_start` | float | 0 .. 0.8 (med 0.8, n=3217) | 0.800000012 |
| `lights[].light_type` | int32 | 0 .. 1 (med 0, n=3217) | 1 |
| `lights[].min_luminosity` | float | 0 .. 0 (med 0, n=3217) | 0 |
| `lights[].multiplier` | float | 0.3 .. 5 (med 1, n=3217) | 2 |
| `lights[].near_cap` | float | 0 .. 1 (med 1, n=3217) | 1 |
| `lights[].part` | string | 103 strings: armoredtruck_body, armoredtruck_headlight_f_l, armoredtruck_headlight_f_r, armoredtruck_reverse_r_l (+99) | sportsmuscle_headlight_f_r_01 |
| `lights[].part_hash` | uint32 | 1.82687e+07 .. 4.29247e+09 (med 2.22537e+09, n=3217) | 2518658659 |
| `lights[].part_index` | uint32 | 0 .. 112 (med 23, n=3217) | 37 |
| `lights[].preset_id` | uint32 | 0 .. 4.27615e+09 (med 2.34115e+09, n=3217) | 1729670457 |
| `lights[].projected_texture_index` | int8 | -1 .. 0 (med -1, n=3217) | -1 |
| `lights[].range` | float | 0.1 .. 50 (med 10, n=3217) | 30 |
| `lights[].uvscale.u` | float | 1 .. 1 (med 1, n=3217) | 1 |
| `lights[].uvscale.v` | float | 1 .. 1 (med 1, n=3217) | 1 |
| `lights[].volume_intensity` | float | 0.01 .. 1 (med 1, n=3217) | 1 |
| `lights[].volumetric_mode` | int16 | 0 .. 1 (med 0, n=3217) | 0 |

## `VehicleMisc`

| member | type | fleet range | donor |
|---|---|---|---|
| `close_door_duration_s` | float | 0.5 .. 1.5 (med 0.5, n=233) | 0.5 |
| `doors` | A[VehicleDoor] | 1 strings:  |  |
| `doors[].close_door_duration_s` | float | 3 .. 5 (med 5, n=8) |  |
| `doors[].door_behavior.hash` | uint32 | 5.06158e+08 .. 3.40628e+09 (med 3.40628e+09, n=8) |  |
| `doors[].door_behavior.string` | string | 3 strings: CargoBayDoor, LeftWing, RightWing |  |
| `doors[].open_door_duration_s` | float | 3 .. 5 (med 5, n=8) |  |
| `full_nitro_refill_time` | float | 2 .. 2 (med 2, n=233) | 2 |
| `full_nitro_use_time` | float | 4 .. 4 (med 4, n=233) | 4 |
| `full_nitro_use_time_upgraded` | float | 8 .. 8 (med 8, n=233) | 8 |
| `max_landing_speed_kmph` | float | 170 .. 250 (med 170, n=233) | 170 |
| `max_take_off_speed_kmph` | float | 150 .. 150 (med 150, n=233) | 150 |
| `max_tilt_to_land_deg` | float | 80 .. 80 (med 80, n=233) | 80 |
| `nitro_refill_min_speed_kph` | float | 15 .. 20 (med 20, n=233) | 20 |
| `official_top_speed` | float | 25 .. 350 (med 150, n=233) | 250 |
| `open_door_duration_s` | float | 0.5 .. 2.5 (med 0.5, n=233) | 0.5 |
| `patch_provision.value_0` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_1` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_10` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_11` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_12` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_13` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_14` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_15` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_16` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_17` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_18` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_19` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_2` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_3` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_4` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_5` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_6` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_7` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_8` | float | 0 .. 0 (med 0, n=233) | 0 |
| `patch_provision.value_9` | float | 0 .. 0 (med 0, n=233) | 0 |
| `turbo_jump_cooldown` | float | 5 .. 5 (med 5, n=233) | 5 |
| `turbo_jump_cooldown_upgraded` | float | 2 .. 2 (med 2, n=233) | 2 |

## `VehicleParts`

| member | type | fleet range | donor |
|---|---|---|---|
| `aim_part_constraints` | A[AimPartConstraint] | 1 strings:  |  |
| `children_part_indices[]` | int8 | 1 .. 24 (med 13, n=96) |  |
| `door_parts` | A[DoorPart] | 1 strings:  |  |
| `fin_parts` | A[FinPart] | 1 strings:  |  |
| `hinged_parts` | A[HingedPart] | 1 strings:  |  |
| `parts` | A[Part] | 1 strings:  |  |
| `parts[].always_break_on_death` | int8 | 0 .. 1 (med 1, n=100) |  |
| `parts[].always_loosen_on_death` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].always_mesh_swap_on_death` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].appears_on_death` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].behavior.hash` | uint32 | 0 .. 3.49872e+09 (med 3.49872e+09, n=100) |  |
| `parts[].behavior.string` | string | 5 strings: FrontWagonCoupling, FrontWagonCouplingLinked, None, RearWagonCoupling (+1) |  |
| `parts[].break_parts_when_broken` | A[int16] | 1 strings:  |  |
| `parts[].centroid[]` | float | -9.40552 .. 9.16294 (med 0, n=400) |  |
| `parts[].children_part_indices` | A[int8] | 1 strings:  |  |
| `parts[].constraint_index` | int16 | -1 .. -1 (med -1, n=100) |  |
| `parts[].damage_type.hash` | uint32 | 2.63802e+09 .. 4.10712e+09 (med 2.63802e+09, n=100) |  |
| `parts[].damage_type.string` | string | 3 strings: Train_Body, Train_Coupling_Linked, Train_Generic |  |
| `parts[].deformation_centroid_offset[]` | float | -0.0634442 .. 0.340346 (med 0, n=400) |  |
| `parts[].disappears_on_death` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].disappears_when_broken` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].grandpa_raycast_instance_id` | int16 | -1 .. -1 (med -1, n=100) |  |
| `parts[].grandpa_world_instance_id` | int16 | -1 .. -1 (med -1, n=100) |  |
| `parts[].has_lights` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].has_world_collision_shape` | int8 | 0 .. 1 (med 1, n=100) |  |
| `parts[].hide_parts_when_broken` | A[int16] | 1 strings:  |  |
| `parts[].is_deformable` | int8 | 0 .. 1 (med 0, n=100) |  |
| `parts[].loosen_parts_when_broken` | A[int16] | 1 strings:  |  |
| `parts[].meshswap_parts_when_broken` | A[int16] | 1 strings:  |  |
| `parts[].model.hash` | uint32 | 1.86459e+08 .. 4.2932e+09 (med 1.78075e+09, n=100) |  |
| `parts[].model.string` | string | 25 strings: models/jc_vehicles/01_land/v5602_train_urga_monorailflatbed/monorailflatbed_body.lod, models/jc_vehicles/01_land/v5602_train_urga_monorailflatbed/monorailflatbed_bogie_f.lod, models/jc_vehicles/01_land/v5602_train_urga_monorailflatbed/monorailflatbed_bogie_r.lod, models/jc_vehicles/01_land/v5602_train_urga_monorailflatbed/monorailflatbed_container_f.lod (+21) |  |
| `parts[].model_swap.hash` | uint32 | 0 .. 0 (med 0, n=100) |  |
| `parts[].model_swap.string` | string | 1 strings:  |  |
| `parts[].name.hash` | uint32 | 1.63837e+08 .. 4.03787e+09 (med 1.97028e+09, n=100) |  |
| `parts[].name.string` | string | 25 strings: monorailflatbed_body, monorailflatbed_bogie_f, monorailflatbed_bogie_r, monorailflatbed_container_f (+21) |  |
| `parts[].only_collides_once_broken` | int8 | 0 .. 1 (med 0, n=100) |  |
| `parts[].only_collides_once_loose` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].parent_part_index` | int8 | -1 .. 0 (med 0, n=100) |  |
| `parts[].parent_space_offset[]` | float | 0 .. 1 (med 0, n=1600) |  |
| `parts[].part_index` | int8 | 0 .. 24 (med 12, n=100) |  |
| `parts[].prevent_breaking_while_alive` | int8 | 0 .. 1 (med 1, n=100) |  |
| `parts[].prevent_loosening_while_alive` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].prevent_mesh_swap_while_alive` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].raycast_body_id` | int16 | -1 .. 32 (med 20, n=100) |  |
| `parts[].raycast_instance_id` | int16 | -1 .. 23 (med 11, n=100) |  |
| `parts[].should_break` | int8 | 0 .. 1 (med 1, n=100) |  |
| `parts[].starts_deleted` | int8 | 0 .. 1 (med 0, n=100) |  |
| `parts[].starts_loose` | int8 | 0 .. 0 (med 0, n=100) |  |
| `parts[].world_collision_body_id` | int16 | -1 .. 25 (med 13, n=100) |  |
| `parts[].world_collision_instance_id` | int16 | -1 .. 23 (med 11, n=100) |  |
| `point_part_constraints` | A[PointPartConstraint] | 1 strings:  |  |
| `propeller_parts` | A[PropellerPart] | 1 strings:  |  |
| `rotating_parts` | A[RotatingPart] | 1 strings:  |  |
| `skinned_parts` | A[SkinnedPart] | 1 strings:  |  |
| `spring_parts` | A[SpringPart] | 1 strings:  |  |
| `wheel_parts` | A[WheelPart] | 1 strings:  |  |

## `WaterInteraction`

| member | type | fleet range | donor |
|---|---|---|---|
| `add_skin_friction_laminar` | float | -0.8 .. 0 (med -0.8, n=233) | -0.800000012 |
| `add_skin_friction_turbulent` | float | 1 .. 5 (med 3, n=233) | 3 |
| `angular_drag_pitch` | float | 0.05 .. 0.05 (med 0.05, n=233) | 0.0500000007 |
| `angular_drag_ref_speed_kmph` | float | 50 .. 150 (med 50, n=233) | 50 |
| `angular_drag_roll` | float | 0.05 .. 0.2 (med 0.05, n=233) | 0.0500000007 |
| `angular_drag_roll_at_speed` | float | 0.05 .. 0.85 (med 0.05, n=233) | 0.0500000007 |
| `angular_drag_yaw` | float | 0.05 .. 0.15 (med 0.05, n=233) | 0.0500000007 |
| `anti_penetration_max_accel` | float | 15 .. 30 (med 15, n=233) | 15 |
| `anti_penetration_multiplier` | float | 1 .. 3 (med 2, n=233) | 2 |
| `anti_penetration_power` | float | 1 .. 3 (med 1, n=233) | 1 |
| `buoyancy_factor_vs_speed_ms.control_points[].x` | float | -3.86542e-34 .. 7.84867 (med 1, n=1165) | 1 |
| `buoyancy_factor_vs_speed_ms.control_points[].y` | float | -3.86332e-34 .. 7.84867 (med 0, n=1165) | 0 |
| `buoyancy_factor_vs_speed_ms.control_points[].y2` | float | -7.9548 .. 7.84867 (med 0, n=1165) | 0 |
| `buoyancy_factor_vs_speed_ms.number_of_control_points` | int8 | 2 .. 5 (med 2, n=233) | 2 |
| `buoyancy_factor_vs_speed_ms.x_max` | float | 1 .. 40 (med 20, n=233) | 20 |
| `buoyancy_factor_vs_speed_ms.x_min` | float | 0 .. 0 (med 0, n=233) | 0 |
| `buoyancy_factor_vs_speed_ms.y_max` | float | 1 .. 1 (med 1, n=233) | 1 |
| `buoyancy_factor_vs_speed_ms.y_min` | float | 0 .. 0 (med 0, n=233) | 0 |
| `depth_full_anti_penetration` | float | 0 .. 0.1 (med 0.1, n=233) | 0.100000001 |
| `depth_full_drag` | float | 0 .. 0.2 (med 0.1, n=233) | 0.100000001 |
| `drag_falloff_power` | float | 0.4 .. 1 (med 1, n=233) | 1 |
| `flat_water_vs_speed_ms.control_points[].x` | float | -3.41917e-43 .. 4.56927e+19 (med 0.325316, n=1165) | 4.56927082e+19 |
| `flat_water_vs_speed_ms.control_points[].y` | float | -3.41917e-43 .. 4.56921e+19 (med 0.618919, n=1165) | 4.56920881e+19 |
| `flat_water_vs_speed_ms.control_points[].y2` | float | -3.85197e-34 .. 4.56921e+19 (med 0, n=1165) | 4.56920837e+19 |
| `flat_water_vs_speed_ms.number_of_control_points` | int8 | 2 .. 3 (med 3, n=233) | 3 |
| `flat_water_vs_speed_ms.x_max` | float | 20 .. 30 (med 30, n=233) | 30 |
| `flat_water_vs_speed_ms.x_min` | float | 0 .. 0 (med 0, n=233) | 0 |
| `flat_water_vs_speed_ms.y_max` | float | 1 .. 1 (med 1, n=233) | 1 |
| `flat_water_vs_speed_ms.y_min` | float | 0 .. 0 (med 0, n=233) | 0 |
| `part_elements` | A[PartWaterInteractionElement] | 1 strings:  |  |
| `part_elements[].from_part.hash` | uint32 | 2.2904e+07 .. 4.28057e+09 (med 2.74325e+09, n=223) | 3076414876 |
| `part_elements[].from_part.string` | string | 74 strings: advancedassault_body, apc_body, armoredjeep_body, armoredtransport_body (+70) | sportsmuscle_body |
| `part_elements[].hull.triangles` | A[uint8] | 1 strings:  |  |
| `part_elements[].hull.vertices` | A[float] | 1 strings:  |  |
| `part_elements[].name.hash` | uint32 | 8.36339e+08 .. 2.68284e+09 (med 2.68284e+09, n=223) | 2682837062 |
| `part_elements[].name.string` | string | 2 strings: bodty, body | body |
| `planing_vs_forward_speed_ms.control_points[].x` | float | -9.89578e-32 .. 2.35051e+34 (med 0.606329, n=1165) | 1 |
| `planing_vs_forward_speed_ms.control_points[].y` | float | -3.88027e-34 .. 2.35051e+34 (med 0.236111, n=1165) | 1 |
| `planing_vs_forward_speed_ms.control_points[].y2` | float | -7.04484 .. 2.35051e+34 (med 0, n=1165) | 0 |
| `planing_vs_forward_speed_ms.number_of_control_points` | int8 | 2 .. 5 (med 5, n=233) | 5 |
| `planing_vs_forward_speed_ms.x_max` | float | 20 .. 20 (med 20, n=233) | 20 |
| `planing_vs_forward_speed_ms.x_min` | float | 0 .. 0 (med 0, n=233) | 0 |
| `planing_vs_forward_speed_ms.y_max` | float | 0 .. 0.1 (med 0.1, n=233) | 0.100000001 |
| `planing_vs_forward_speed_ms.y_min` | float | 0 .. 0 (med 0, n=233) | 0 |
| `pressure_drag` | float | 100 .. 5000 (med 5000, n=233) | 5000 |
| `pressure_drag_2` | float | 10000 .. 30000 (med 20000, n=233) | 20000 |
| `reference_drag_speed_ms` | float | 20 .. 20 (med 20, n=233) | 20 |
| `suction_drag` | float | 100 .. 5000 (med 5000, n=233) | 5000 |
| `suction_drag_2` | float | 2000 .. 30000 (med 20000, n=233) | 20000 |
| `triangles[]` | uint8 | 0 .. 94 (med 28, n=65220) | 6 |
| `vertices[]` | float | -43.9089 .. 49.7703 (med 0, n=47064) | 0 |
| `will_sink` | int32 | 0 .. 1 (med 1, n=233) | 1 |
