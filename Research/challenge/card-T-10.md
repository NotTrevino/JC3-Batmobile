# Assumption challenge — backlog card T-10 (re-open the `out` rows with the G2 evidence)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-10 card (§7, line 851),
its §12 row (line 1319), the MODLOG sections `T-10 · Re-open the out rows with the G2 evidence —
intended change` (12127), `— done` (12457), `T-10 rework · … — intended change` (14952) and
`T-10 rework — done` (15052), and the outputs `Working/Translation/T10_OPEN_ROWS.md` +
`T10_OPEN_ROWS.json` + the generator `Tools/scripts/t10_reopen.py`, plus what they read:
`T_ROWS.jsonl`, `T6_HUD_CAMERA.md`, `Research/JC3Grab/*.md|json`, `Research/BatmobileGrab/*.json`,
the pre-edit snapshots in `tmp/freebuff/pre_t10/` and `tmp/t10rework/`, the successor cards' delivered
outputs (`T7_WEAPONS.md`, `T8_PARTS.*`, `T11_MODES.md`, `T13_FX.md`, `T14_LIGHTS.md`,
`BUILD_BATCHES.md`, `STATUS.md`), and — because the card's own gate reads them — the decoded JC3 data
`E:/Modding/JustCause3/_grab/entities/*.ee.json` (232) and `E:/Modding/JustCause3/_grab/hud/dec` (260 `.as`).

Constraints honoured: no game launched, nothing written into `D:/Games`, no archive opened, no game
file touched, nothing committed, no secrets, no `--write` on any tool, no file in the project modified
except this one. Scratch output was removed.

The card's gate is **green at HEAD**, which is the starting point for the challenge, not the answer:

```
$ python Tools/scripts/t10_reopen.py --check
PASS: 16 rows (5 superseded, 10 out, 1 blocked) | 10/10 out rows this card owns carry a proof file |
successors B-05, T-11, T-12, T-15, T-17, T-18 | decisions open none | json match True, md match True
later `out` rows: 26 of 32 cite a proof (an existing path or a real G/T/B card id), 6 do not
(T-FX13, T-FX16, T-MD5, T-MD6, T-MD7, T-WLD15)                                          EXIT=0
```

## VERDICT

**Six BROKEN, seven WEAK, four HOLDS.** The card's *bookkeeping* is sound: the 15 rows it re-decides
are exactly the `out` rows that existed (A1), the two places the dispositions live are compared on
every run, and the gate can fail (six tamper tests are recorded and I re-proved the mechanism, A14).
What does not survive are the **carrier verdicts** and the **absence surfaces** they rest on.

Two findings dominate. First, **`superseded` does not mean "a carrier exists"** (A2): three of the
five superseded rows were re-blocked or omitted by the very card they were handed to — the EMP pair
(WPN-4/WPN-5) is `blocked` in `BUILD_BATCHES.md`, 7 of T-15's 15 mode rows are `omitted`, and
T-CAM10's evidence is a file this project built (A15). The five rows left the completion denominator
on that word, so `STATUS.md`'s "resolved / in scope" no longer counts requirements that are still
open at code level.

Second, **the "52-type / 1,421-path vocabulary" is not a uniform fleet surface** (A3). It is an
aggregate in which the `VehicleParts` block — the module an upright constraint or a winch behaviour
would live in — comes from **4 entities, all monorail flatbed wagons**, because ConvertAdf failed on
`*_vehicle_parts.vmodc` in **228 of 232** caches, including the donor's own. And the population labels
inside the rows are inferred from counts, not read: `righting_torque` is called "23 aircraft" and is
in fact **18 bikes + 5 boats, zero aircraft** (A4), which removes the basis of T-SR1's `out`.

Where the card is strongest is exactly where it does not rely on a word list: T-HUD7's winch absence
rests on TETHER's class census (A11), and the HUD word scans that *are* complete for their question
(A12) hold up — I re-ran them and the allow-list hits are genuine.

| # | assumption (stated or silent) | verdict |
|---|---|---|
| A1 | the 15 re-decided rows are every `out` row that existed | **HOLDS** — pre-T-10 ledger 8/8, pre-T-10 T6 7/7, same ids |
| A2 | `superseded` = a carrier exists, so the requirement is now another card's | **BROKEN** — 3 of 5 successors re-blocked/omitted the requirement |
| A3 | `VOCABULARY.md` (52 types / 1,421 paths) is the fleet-wide member surface | **BROKEN** — the parts block is 4 monorail wagons; 228/232 caches failed that module |
| A4 | `righting_torque` is "only in `DriverLean`, n=23 **aircraft**" ⇒ no land carrier | **BROKEN** — 18 bikes + 5 boats, 0 aircraft |
| A5 | n=145 is "145 **land** vehicles" | **WEAK** — 125 car + 19 bike + 1 plane (cargo tank) |
| A6 | the `must_not` word list bounds the behaviour, not just the spelling | **WEAK** — `air_steering.*` (18 paths) and `roll_to_fall_*` exist in the same file, unscanned |
| A7 | T-RA1's single negative scan proves no ram-assist/shove carrier | **WEAK** — collision-damper and push members sit in the same file, unscanned |
| A8 | "G2-28 found no outgoing ram damage" | **BROKEN as worded** — `rotor_collision.damage_to_other_per_second` 100000 on 232 entities |
| A9 | 260 scripts of `ui/hud.gfx` are the in-game HUD | **WEAK** — 1 of 25 non-font `ui/*.gfx`; the doc's "other 28" matches no count |
| A10 | T-HUD4: JC3 has no armour bar | **BROKEN** — `MCI_vehicle.MCI_bavarium_shield` + `InitBavariumShield(recharge)` |
| A11 | T-HUD7: no winch widget ⇒ row `out` | **WEAK** — `DualTether.MCI_tether_progress` exists; the `out` survives on TETHER, not on the scan |
| A12 | T-HUD6/8/9/10 absences | **HOLDS** — 48 `battle*` tokens are the gauge; `energy`'s one hit is the joke array |
| A13 | "§11 decisions still open on those successors: none" | **HOLDS** — but the derivation is a `"resolved" in line` substring test |
| A14 | a `needle` hit proves the carrier | **WEAK** — first substring occurrence; two needles are *negative* sentences |
| A15 | T-CAM10: a second per-variant `.ctunec` is the carrier | **BROKEN** — one tune exists, built here; T-15 says no value changes and the switch is missing |
| A16 | STATUS's "8 rows are superseded: T-10 re-opened them" | **WEAK** — 5 are T-10's; 3 are T-18's, and the prose is typed |
| A17 | the card is Done because "no `out` row lacks a proof file" | **HOLDS as scoped** — 10/10 own rows; 6 shared-ledger rows still cite nothing |

Counts: 4 HOLDS, 7 WEAK, 6 BROKEN.

---

## A1 — the 15 re-decided rows are every `out` row that existed. **HOLDS**

The card names 8 ledger rows and 7 T6 rows. Tested against the pre-edit snapshots the T-10 session
itself left behind, not against today's ledger (which 9 later cards have grown):

```
$ python -c "... tmp/freebuff/pre_t10/T_ROWS.jsonl ..."
pre-T-10 ledger rows 105
out 8
  T-LG5 T-2b | battle-mode and forensics rigs have no JC3 system
  T-FX4 T-2b | EMP/seismic/sonar are features JC3 does not have
  T-DM7 T-3  | BmAK impact fields are outgoing ram damage; JC3 has no vehicle-on-vehicle ram damage…
  T-W1  T-3  | JC3 gives a car no player-fired weapons
  T-BM1 T-3  | no transformation, tank turn or battle-mode armour in JC3
  T-AC1 T-3  | JC3 cars have no mid-air yaw authority
  T-RA1 T-3  | no ram/dodge/shove assist system for cars
  T-SR1 T-3  | JC3 has no upright constraint

$ python (parse the 6th cell of every `| T-` row of tmp/freebuff/pre_t10/T6_HUD_CAMERA.md)
7 ['T-HUD4', 'T-HUD6', 'T-HUD7', 'T-HUD8', 'T-HUD9', 'T-HUD10', 'T-CAM10']
```

8 + 7 = the card's 15, id for id. `T-HUD5` is the 16th line and the card's own expected-outcome
sentence names it (`T-HUD5/6 → G2-25`), so including it is the card's text, not an invention.
**HOLDS**, and it is a stronger check than the doc claims for itself: its §4 only scopes the Done
clause to the rows it owns, not the row *set*.

## A2 — `superseded` means "a carrier exists", therefore the value is someone else's. **BROKEN**

The doc's own definition, §2 header: *"A row with a carrier is **superseded** by the phase-T card
that will write it"*. `STATUS.md` then excludes the five from the denominator
(`Completion is evidenced / (rows - out - superseded)`, `status_audit.py:16`). The successors were
written after T-10 and are now `done`, so the claim is testable against their outputs.

`T-W1 → T-11` (11 BmAK weapon classes split over 12 WPN codes):

```
$ sed -n '10,14p' Working/Translation/T7_WEAPONS.md
| rows with a JC3 carrier | 5 (6 named omissions, 3 blocked: T-WP4, T-WP5, T-WP13) |
| JC3 weapon ids used | 4 of the fleet's 25 |
```

`T-FX4 → T-11` (the EMP/Immobilizer half) and → `T-17` (tyre smoke):

```
$ sed -n '107,108p' Working/Translation/BUILD_BATCHES.md
| WPN-4 | blocked | `T-WP4` (blocked) | T-11 |
| WPN-5 | blocked | `T-WP5` (blocked) | T-11 |

$ grep -n "the disable half cannot be built" Working/Translation/T7_WEAPONS.md
79:… | clone w618 + copy the `CForcePulse`; the disable half cannot be built | decoded · none yet …
```

The tyre-smoke half did land (`T-FX17`/`T-FX18`, carried). The EMP half did not: the row it was
superseded for is `blocked` on exactly the member T-FX4 needed (a disable state), and
`BUILD_BATCHES.md:21` still lists `WPN-4, WPN-5` among the **blocked codes**.

`T-BM1 → T-15` (mode scalars/curves) + `T-12` (pose):

```
$ grep -n "T-MD5 \|T-MD6 \|T-MD10 \|T-MD11 " Working/Translation/T11_MODES.md
49:| T-MD5 | … | omitted: the car keeps one top speed | decoded |
50:| T-MD6 | … | omitted: no 21.6 km/h battle cap | derived |
54:| T-MD10 | … | carried: the shipped value is 0, so there is no reduction to carry |
55:| T-MD11 | … | inside band: FOV 60 lies in the tune's 55-63, so no value changes and only the
    mode switch is missing | derived |
```

Two of the four successor rows are named omissions, one is "carried" only because the value is 0, and
the camera row says the only thing missing is the thing the row was about. T-15's own §12 summary is
`carried 7 / inside band 1 / omitted 7`.

`T-LG5 → T-18` is the one that holds: `t14_lights.json` tags four rows `VEHLT_BattleModeLight`
(T-L17…T-L20, the 16 donor entries) and they are mapped to a real `SVehicleLight` target.

**BROKEN for T-W1, T-FX4, T-BM1, T-CAM10 (A15); HOLDS for T-LG5.** The consequence is accounting, not
cosmetics: the same requirement is "excluded from the denominator" at row level and "blocked" at code
level in the final build table, so the 70 % "resolved in scope" line counts a population that dropped
these five rows for a reason that three of them cannot support.

## A3 — `VOCABULARY.md` (52 types / 1,421 paths) is the fleet-wide surface for "no member exists". **BROKEN**

Every `absent` triple in the card scans this one file. The card says it is *"derived from 232 decoded
`.ee` entities"*, and `facts()` reads its type/path counts straight off the headings
(`52`, `1,421`). Enumerating the same 232 caches independently:

```
$ python (walk E:/Modding/JustCause3/_grab/entities/*.ee.json; collect module types and errors)
distinct module types: 53          (52 named + 1 bucket whose rows failed to convert)
entities with a failed module: 228 of 232
[('oldtruck_vehicle_parts.vmodc', 9), ('monorailcargoengine_vehicle_parts.vmodc', 7), …]
VehicleParts modules decoded: 4 with rows: 4 total rows: 6640
   v5602_train_urga_monorailflatbed_military_catwalk.ee
   v5602_train_urga_monorailflatbed_military_containers.ee
   v5602_train_urga_monorailflatbed_military_containers_rigidobject.ee
   v5602_train_urga_monorailflatbed_military_empty.ee

$ python (the donor signature entity's own modules)
{"file": "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/signature/
          sportsmuscle_vehicle_parts.vmodc", "error": "convertadf-failed"}
```

So `jc3grab.py` (Gibbed `ConvertAdf`) lost the parts module in **228 of 232** entities, and the
`VehicleParts` block that survived — **56 of the 1,421 paths, 3.9 %** — describes four monorail
flatbed wagons, not the fleet and not the donor. The later cards did decode those modules by another
route (`jc3moving.py` imports `jc3adf`, and G2-14 reports 148 `hinged_parts` modules / 11,643 part
rows), so this is a **decoder split**, not missing data: the vocabulary simply does not contain what
G2-13/G2-14/G2-34 decoded.

That matters for the rows that stay `out` for a *parts/constraint* reason (T-SR1's upright constraint,
T-RA1's assist) and not for the ones decided in a driving module (T-AC1). The doc's §4 caveat — "an
absence is an absence of names in a decoded surface" — is true but understates it: the surface is
fleet-wide in 51 of 52 types and a four-train sample in the one type that carries behaviours and
constraints. Also note `TETHER.md` counts **53** module types where the vocabulary counts 52; the two
G2 docs disagree because one counts the failed bucket.

## A4 — "`righting_torque` … only in `DriverLean`, n=23 aircraft … so there is no land carrier". **BROKEN**

This is the whole of T-SR1's `why`, carried into `t_rows.py:139` and `g2x_gate.py:194`. The n=23 is
read from the vocabulary; the word *aircraft* is inferred from the count. It is wrong:

```
$ python (module type == DriverLean, grouped by model family, over the 232 caches)
DriverLean families: {'bike': 18, 'boat': 5}

  v1500_boat_solar_jetski_{civilian_01,debug,signature_01}
  v1717_boat_na_duck_{civilian_01,debug}
  v3000_bike_autostraad_trials_{civilian_01,debug,signature_01}
  v3401_bike_mugello_modernsport_{civilian_01,debug}   v3402_…_modernsuper_{civilian_01,debug}
  v3500_bike_solar_oldmoped_{civilian_01,debug}        v3501_…_modernmoped_…
  v3502_bike_solar_modernroad_…                        v3503_…_oldroad_…
  v3600_bike_urga_combatdirt_{debug,military_01,rebel_01}
```

18 motorcycles and 5 jet-skis/amphibious quads; **zero** aircraft (`v2102`/`v2200`/`v2601`… are the
helicopter chassis and none carries `DriverLean`). The member the row dismisses is therefore a
**land-vehicle self-righting torque** — exactly what `DriverLean`'s own block describes:

```
| `leaning_torque` | float | 2000 .. 8000 (med 5000, n=23) |
| `righting_torque` | float | 1500 .. 4000 (med 3000, n=23) |
| `max_lean_angle_deg` | float | 20 .. 40 (med 30, n=23) |
```

and the fleet-wide lean/fall behaviour sits beside it in the shared module:

```
$ grep -n "roll_to_fall\|roll_rate_to_fall" Research/JC3Grab/VOCABULARY.md
1409:| `motorbike_common.roll_rate_to_fall_degs` | float | 800 .. 800 (med 800, n=232) |
1410:| `motorbike_common.roll_to_fall_no_driver_deg` | float | 50 .. 50 (med 50, n=232) |
1411:| `motorbike_common.roll_to_fall_with_driver_deg` | float | 80 .. 80 (med 80, n=232) |
```

The donor's "none" part of the claim is correct — the signature entity has 30 modules and no
`DriverLean`. But "no land carrier" is false, and the row's disposition (`out`, HDL-6 named omission)
was written on that sentence. The honest version is narrower and *not* obvious: the mechanism exists
on 18 bikes and 5 boats and on no car; whether a `CCar` module set accepts `DriverLean` is untested.
That is a different row — a `blocked`/UNKNOWN, not a "JC3 has no system".

## A5 — n=145 is "145 land vehicles". **WEAK**

Same inference pattern as A4, one order of magnitude smaller:

```
$ python (module type == CustomLandGlobal, grouped by family)
Counter({'car': 125, 'bike': 19, 'plane': 1})          total 145
  the plane: editor/entities/jc_vehicles/02_air/v4603_plane_urga_cargotransport/
             v4603_plane_urga_cargotransport_military_cargo_tank.ee
```

144 ground vehicles and one cargo-tank aircraft. The numbers the row quotes are fine — the donor
column of the vocabulary does read `gravity_multiplier_grounded` 1, `…_in_air_down` 1,
`…_in_air_up` 1, `takeoff_pitch_damping` 0.5 — so this is a population label, not a value error.
**WEAK**: it does not change T-AC1's answer (`air_steering` belongs to helicopters, A6), but the same
"n ⇒ family" step that broke A4 is what produced it.

## A6 — the `must_not` word list bounds the behaviour, not just the spelling. **WEAK**

T-AC1 scans for `air_control`, `aircontrol`, `yaw_torque`; T-SR1 for `upright`, `stayupright`. Both
lists are spellings, and the same decoded surface contains the nearest mechanism under other names:

```
$ grep -c "air_steering" Research/JC3Grab/VOCABULARY.md          → 18 paths
   HelicopterSteering.air_steering.YawAxisTiming.{Centering,Counter}InputTimeFactor
   HelicopterSteering.air_steering.max_steering_angle / pitch_return / roll_return …
$ python (entities with HelicopterSteering)                     → 23, all v21xx/v22xx/v26xx helicopters
$ grep -n "steering_factor" Research/JC3Grab/VOCABULARY.md
| `aerodynamic_surfaces[].turn_steering_factor` | float | 0 .. 0 (med 0, n=77) |
| `aerodynamic_surfaces[].pitch_steering_factor` | float | 0 .. 0 (med 0, n=77) |
$ grep -n "yaw_vel_damp" Research/JC3Grab/VOCABULARY.md
| `drift.drift_yaw_vel_damp` | float | 0.01 .. 0.05 (n=145) |  |  (+ exit/overdrift)
```

So a real air-steering family exists in the same 1,421 paths but only on helicopters — I checked, not
assumed — which is why **T-AC1's answer survives**: no land module carries a mid-air yaw torque, and
the aerodynamic steering factors that do exist are 0 across the fleet. `ParentIsUpRightCondition` in
`ENTITIES.md`/`EJECT.md` is a graph *condition*, not a torque, so it does not carry T-SR1 either.
**WEAK**: right conclusion, proof that would have missed a land `air_steering.*` if one existed, and
that cannot see the physics/`.physicsc` layer at all (constraints are not in a `.vmodc`).

## A7 — T-RA1's single negative scan proves "no ram-assist, dodge, shove or kill-flip member anywhere". **WEAK**

T-RA1 is the only one of the ten `out` rows whose entire evidence is one `absent` triple with no
second file:

```
$ python -c "import json; … T-RA1 in T10_OPEN_ROWS.json"
[{'kind': 'absent', 'file': 'Research/JC3Grab/VOCABULARY.md',
  'must_not': ['shov', 'dodge', 'road_assist', 'kill_flip', 'impact_shake'], 'ok': True}]
```

The vocabulary does contain the collision-response and push members the scan does not search:

```
| `velocity_damper.collision_spin_damping`   | float | 0 .. 5   (med 0.05, n=145) | 0.05 |
| `velocity_damper.collision_spin_threshold` | float | 0 .. 5   (med 2.5,  n=145) | 2.5  |
| `arcade.nitro_boost.push_force`            | float | 15000 .. 15000 (n=145) |
| `arcade.nitro_boost_upgraded.push_force`   | float | 20000 .. 20000 (n=145) |
| `rotor_collision.damage_to_other_per_second` | float | 100000 .. 100000 (n=232) |
```

None of these is a shove *assist* or a dodge, so the disposition survives; but "no member anywhere"
is a five-token claim about a file that demonstrably holds collision-response members of the same
subject. **WEAK**, and the doc's "10/10 with a proof file" counts this row as proven (A14, A17).

## A8 — "G2-28 found no outgoing ram damage". **BROKEN as worded**

The `why` sentence drops the qualifier the evidence file has. `DAMAGE_MODEL.md` never says anything
about outgoing damage — it is a health/armour + hits-to-kill document:

```
$ grep -n -i "incoming\|outgoing" Research/JC3Grab/DAMAGE_MODEL.md
267:- **the BmAK incoming-damage numbers**: `GetDamageMod` is native (G1-14 §7) …
$ grep -n "impact_damage_factor" Research/JC3Grab/DAMAGE_MODEL.md
50:| `impact_damage_factor` / `deform_scale` | 1 / 1 | 1 / 1 | 0 / 0 |
53:6 values: `deform_scale` 1 -> 0, `impact_armor` 0 -> 5000, …
```

That needle is a value-table row for the vehicle's **own** scalar: it supports "the impact switch is
incoming", not "no outgoing ram damage exists". And the fleet does carry an outgoing contact-damage
member, on every vehicle, in the shared module:

```
| `rotor_collision.damage_to_other_per_second` | float | 100000 .. 100000 (n=232) | 100000 |
```

`DAMAGE_MODEL.md:90` also records a *pulse* on an impact event:
`w604_helicopter_mgun_impact.ftunec` (PlayerDamage 25 in 1.5 m) as the `CForcePulse` of a weapon.
The second needle is the verdict cell of another card's three-candidate table, whose test was a path
scan, not a behaviour:

```
$ grep -n "collision" -A0 Research/JC3Grab/FORCEPULSE.md
181:| collision | 0 of 23 tune paths mention collision; no pulse owner is a collision object |
    collision does not trigger a pulse |
```

**BROKEN as worded.** What is established: the health/armour chain has no outgoing term, and no
pulse *owner path* names collision. What is not established — and what the row's sentence claims — is
that JC3 has no member that damages another entity on contact. Whether `rotor_collision` can be moved
off a rotor onto a car body is UNKNOWN and would be a Q-1 probe, not a translation row; the fix is
editorial plus one UNKNOWN, not a new feature.

## A9 — 260 scripts of `ui/hud.gfx` are the in-game vehicle HUD. **WEAK**

The count is right and re-derived on every run (`hud_scripts: 260`), but the movie is one of many:

```
$ find E:/Modding/JustCause3/_grab/hud/dec -name "*.as" | wc -l        → 260
$ grep -o '"path": *"ui/[^"]*\.gfx"' Research/JC3Grab/INDEX.jsonl | sort -u | wc -l   → 32
$ grep -c "^ui/font" (that list)                               → 7
   → 25 non-font movies, of which hud.gfx is 1; 24 not decompiled
   (ui/overlay.gfx, ui/main.gfx, ui/hud.gfx, ui/reward.gfx, ui/load.gfx, ui/pause.gfx …)
```

The doc's §4 says *"the other 28 `ui/*.gfx` movies in the index are not decompiled"*. No count
produces 28: 31 others in total, 24 other non-font movies. That is a typed number inside a generated
document (R11), and it understates the gap: `ui/overlay.gfx` is the obvious other home for a
vehicle-HUD element. **WEAK** — the five HUD rows are correctly worded "in the in-game HUD", but the
surface is 1 of 25 non-font movies and one typed number overstates nothing while understating the
set.

## A10 — T-HUD4: "JC3 has no armour bar". **BROKEN**

The row's scan searched `armour`/`armor` and allow-listed the 9 `CHAOS_REWARD_ARMORY` hits — both
verified. The HUD nevertheless has a **second per-vehicle meter** under a different name:

```
$ grep -n "MCI_vehicle.MCI_bavarium_shield" scripts/hud.as
4988:  this.MCI_safe_area_bottom_left.MCI_vehicle.MCI_bavarium_shield.Hide();
$ sed -n '5141,5155p' scripts/hud.as
5141: public function InitBavariumShield(recharge:Number) : void
5143:    this.MCI_safe_area_bottom_left.MCI_vehicle.MCI_bavarium_shield.Show();
5144:    this.MCI_safe_area_bottom_left.MCI_vehicle.MCI_bavarium_shield.SetProgress(1 - recharge);
5147: public function UpdateBavariumShield(recharge:Number, on_cooldown:Boolean) : void
$ grep -n "SHOW_SHIELD\|NO_SHIELD" scripts/hud.as
3517: health_bar.MCI_progress.gotoAndStop("NO_SHIELD");
3574: health_bar_clip.MCI_progress.gotoAndPlay("SHOW_SHIELD");
3579: health_bar_clip.MCI_progress.gotoAndPlay("HIDE_SHIELD");
```

So the vehicle HUD has (a) a bottom-left shield meter with its own init/update API and a ready sound,
and (b) a second *state* painted on the top-middle health bar that T-HUD3 already maps. The row was
decided by the member's **name** (armour) rather than the **behaviour** (a second, drivable health
layer on the vehicle HUD) — the R5 pattern, in the card that exists to apply R5. The proof file makes
it worse: `JC3_HUD_WEAPONS.md` is the *weapons* API document (`grep -i "bavarium\|shield\|health"`
returns one line, about BmAK's "per-target health"); it cannot prove anything about a health bar.

The driver bridge is the same class T-HUD2 accepted for nitrous (`InitVehicleNitrous(recharge)`), so
"no caller" is not the reason to say `out` either. **BROKEN**: the correct disposition is at least
`blocked`/UNKNOWN on whether BmAK's armour state can drive `InitBavariumShield`, not "JC3 has no
armour bar".

## A11 — T-HUD7: "no winch widget either", therefore `out`. **WEAK**

`winch` is genuinely 0 hits, but the HUD carries a rope/tether progress meter:

```
$ grep -rni "tether" scripts/ | grep -v movie.xml | head -3
scripts/DualTether.as:7:   public dynamic class DualTether extends MovieClip
scripts/DualTether.as:14:      public var MCI_tether_progress:MovieClip;
scripts/hud.as:761:      private const DUALTETHER_RETRACT_FADE_IN_TIME:Number = 0.3;
      … 10+ DUALTETHER_* layout constants
```

So the widget *shape* the row asked for exists; the row's `out` does not rest on the HUD half anyway.
It rests on TETHER.md, and that half is the strongest negative in the whole card:

```
$ grep -n "Functional winch\|0 tether" Research/JC3Grab/TETHER.md
174:- The fleet's 53 module types contain **0 tether/cargo/rope/winch/tow type** (none).
177:  **None is a winch, rope, tow or reel, so no vehicle part can pull another vehicle.**
180:- Functional winch classes anywhere in the fleet: **0**.
```

A module-type census and a 67-behaviour census over 11,643 part rows is a behaviour test, not a word
list. **WEAK**: right disposition, one of its two proofs is spelling-scoped (`winch` vs `tether`).

## A12 — T-HUD6/8/9/10 word scans are complete for their question. **HOLDS**

Re-ran the four scans with wider spellings than the tool uses:

```
battle* occurrences in scripts/: 48 (45 lines)   ← matches MODLOG's "48 `battle` hits"
   battle_won 7+2, BattleWon 6, battle_lost 5+2, battle 5, BattleGauge 4+4(Tweens),
   BATTLE_TWEEN_TIME 4, BattleGuage 4 (sic), battle_on 1, BattleRebelsVsDRM 1,
   BattlePrisonersVsBlackHand 1, BattleLost 1, BATTLE_MISSION 1   (sum 48, no vehicle-mode token)
zoom 0 · battlemode 0 · battle_mode 0
energy 1 line:  hud.as:10159  this.m_DogeText[DAMAGE_TYPE_EMP] = new Array("SO emp","SO fwum",
                "SUCH energy","SUCH pulse", …)          ← the allow-list hit is genuine
combo 0 · medal 0 · enemy_count 0 · enemycount 0 · chain 0 · streak 0
occupant 0 · passenger 0 · virus 0 · forensic 0
winch 0 (A11)      synchronised: no false hit anywhere
```

The 48 `battle` tokens are the province battle gauge and its won/lost banners — I read the tokens, not
the MODLOG's sentence — so T-HUD6's "no battle overlay" is a judgement about a *mode* overlay, and the
check deliberately does not search `battle` (it would fail on the gauge). That is defensible and
documented in the journal, not in the artifact. T-HUD8's single allow-list hit is exactly what it says
it is. **HOLDS** for all four, with one caveat: recharge meters exist
(`MCI_sungun_recharge`, `MCI_nitro_meter`, `MCI_jump_meter`, and the shield meter of A10), so T-HUD8's
absence is "no energy-*system* widget", not "no meter the number could ride".

## A13 — "§11 decisions still open on those successors: none". **HOLDS (brittle mechanism)**

```
$ grep -n "^| D-2 \|^| D-3 \|^| D-7 " GRAB_BACKLOG.md | cut -c1-200
1258:| D-2 | Pursuit/Battle: … | **resolved 2026-10-28 (user): (b) one hybrid car** — …
1259:| D-3 | Weapon lethality: … | **resolved 2026-10-28 (user): accept JC3 …
1263:| D-7 | Weapon slots: … | **resolved 2026-10-28 (user): every BmAK weapon in both battle
         and pursuit modes** — no per-mode split; …
```

Correct today. The derivation is `"resolved" in line.lower()` (`backlog_decisions`), so a line
reading *unresolved* would be counted as resolved:

```
$ python -c "print('substring reads resolved:', 'resolved' in '| D-11 | test unresolved |'.lower())"
substring reads resolved: True
```

**HOLDS** on the current register; the mechanism is one word away from a false "none".

## A14 — a `needle` hit proves the carrier. **WEAK**

`prove()` is `text.find(need)` on the whole file and prints the containing line; the doc states this
("`needle` = the file still contains the string"), so the assumption is declared — and then relied on
for 8 of the 16 rows. Occurrence counts of the actual needles:

```
 10x  WEAPONS.md            w618_sportsmuscle_missile
 94x  WEAPON_WIRING.md      main_weapon
  4x  EMP.md                CForcePulse
  2x  DAMAGE_MODEL.md       impact_damage_factor
 16x  TURRET.md             179
 13x  JC3_HUD_WEAPONS.md    InitVehicleWeapons
  3x  JC3_HUD_WEAPONS.md    MCI_vehicle_weapons0
  1x  each: "no vehicle weapon slot", "collision does not trigger a pulse", "righting_torque",
      "takeoff_pitch_damping", "gravity_multiplier_in_air_down",
      "Functional winch classes anywhere in the fleet: **0**",
      "Turn-on-the-spot has no JC3 data carrier", "VEHLT_BattleModeLight -> HeadLight"
```

Three consequences. (1) The mechanism has no **polarity**: `no vehicle weapon slot` and
`collision does not trigger a pulse` are *denials*, and the same green tick appears whether the file
asserts or refutes a carrier. (2) It has no **anchor**: `179` (16 hits, all hinge limits and
coordinates) is used to justify a battle *pose*, and the printed line is only the first hit. (3) It
has no **scope**: `main_weapon` (94 hits) proves the token is in the wiring table, not that a driver
slot is usable by this car. The six tamper tests show the machinery detects edits to the artefacts;
none of them shows the machinery can tell a supporting sentence from a contradicting one.
**WEAK** — acceptable as a "the evidence still says what the table quotes" check, not as proof.

## A15 — T-CAM10: "a second per-entity `.ctunec` per variant is the carrier". **BROKEN**

The only evidence is `exists` on a file this project built:

```
$ ls -la Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/
-rw-r--r-- 5968 Oct 23 22:45 bat_base.ctunec
-rw-r--r-- 5968 Oct  7 14:04 car_base.ctunec
$ ls …/vehicle_cameras/ | grep bat_base
bat_base.ctunec                      ← no second/battle tune, and no `.ctune`
```

Three problems. (a) The evidence is a **project artefact**, not a JC3 surface: it proves Batch F wrote
a tune, not that JC3 carries a battle camera. The rework replaced a self-citation with this, which is
the same self-reference one level removed. (b) The delivered T6 cell names a path that does not
exist — `**superseded by T-15** (D-2): … a second per-entity `.ctune` is the carrier
(`bat_base.ctune`, Batch F, test-091)` — while the T-10 doc and the file say `.ctunec`; `cell_must`
only checks the cell contains `T-15`, so the wrong filename passes. (c) The successor disagrees with
the reason: `T-MD11` says *one* per-entity tune, FOV 60 inside the tune's 55-63 band, **"no value
changes and only the mode switch is missing"** — i.e. no second tune was needed or written, and the
switch (the actual requirement) has no carrier. **BROKEN**: this row should read `out`/`blocked` for
the mode switch, or its carrier should be described as "the FOV value, carried in the one tune".

## A16 — STATUS: "8 rows are superseded: T-10 re-opened them and found a carrier". **WEAK**

```
$ python (ledger superseded rows)
T-L4  T-1  ['T-18'] | T-L7  T-1  ['T-18'] | T-LG4 T-2b ['T-18'] | T-LG5 T-2b ['T-18']
T-FX4 T-2b ['T-11','T-17'] | T-W1 T-3 ['T-11'] | T-BM1 T-3 ['T-12','T-15']
   + T-CAM10 (T6)                                   = 8 rows, of which T-10's are 5
$ grep -n "re-opened" Tools/scripts/status_audit.py
274:  f"- {t['superseded']} rows are superseded: T-10 re-opened them and found a carrier (weapons,
```

The count (8) is generated; the sentence around it is typed, and it credits T-10 with three rows
T-18 wrote (T-L4, T-L7, T-LG4). **WEAK** (R11 in a generated file: a number derived, the claim it
carries not). It also flatters the card: T-10's own table says 5, and A2 shows 3 of those 5 are not
carried.

## A17 — the card is Done because "no `out` row lacks a proof file". **HOLDS as scoped**

The check prints `10/10 out rows this card owns carry a proof file`, and the doc states the limit:
the wider reading of the card's Done clause is *"not asserted as met"*. Re-derived:

```
26 of 32 later `out` rows cite a proof (an existing path or a real G/T/B card id), 6 do not
(T-FX13, T-FX16, T-MD5, T-MD6, T-MD7, T-WLD15)
```

Six rows in the shared ledger cite nothing, and they are other cards' rows — T-MD5/T-MD6 are T-15's,
so the same card family that received T-BM1's mode rows left two of its own `out` rows unproven.
The scoping is honest and the number is correct. The only overreach is the word "proof": the counter
increments when every evidence string was *found*, which A7 and A14 show is weaker than proof.
**HOLDS as scoped.**

---

## What the card gets right, and should keep

- The disposition lives in three places and the gate compares all three (`T_ROWS.jsonl`,
  `T6_HUD_CAMERA.md`, this table); the tamper tests 1–6 are real and the artifact no longer rots when
  another card adds an `out` row (verified: `--check` is green and the later-row census is printed
  live, not stored).
- T-LG5's mapping (`VEHLT_BattleModeLight` is a donor light *type*, `HeadLight` is JC3's behaviour)
  is the one R5-clean supersession, and it says so in the row.
- T-HUD7's `out` rests on a class/behaviour census (0 tether/rope/tow module types, 67 part
  behaviours, none a winch), which is the kind of test the other nine rows should have had.
- The `T-HUD5` `blocked` call is right for the right reason: an API is not a carrier (A2's failure
  mode, avoided in the one row where it was noticed).
- §4's UNKNOWN statements are accurate about what an absence is; the problem is only how wide the
  surface actually is (A3, A9).

## What a rework would have to change (smallest set)

1. T-SR1: replace "23 aircraft … no land carrier" with the measured 18 bikes + 5 boats, 0 cars, and
   re-decide the row (`blocked`/UNKNOWN on `CCar` + `DriverLean`, or `out` for the *cars-only* wording
   the card can defend). Touches `t10_reopen.py`, `t_rows.py`, `g2x_gate.py`'s HDL-6 fact and §12.
2. T-HUD4: re-open on the shield meter (`InitBavariumShield`/`UpdateBavariumShield`,
   `health_bar` `SHOW_SHIELD`) and stop citing a weapons-API doc for a health element.
3. T-CAM10: drop the `exists` artefact as proof, fix the `.ctune`/`.ctunec` name in the T6 cell, and
   state what T-15 actually delivers (FOV value in the single tune; mode switch missing).
4. T-DM7: restore the qualifier ("no outgoing term in the health chain") and record
   `rotor_collision.damage_to_other_per_second` as the one outgoing contact member, UNKNOWN for a
   car body.
5. The `superseded` word: either add a `blocked-by-successor` outcome, or say in the row what the
   successor delivered (5 carriers / 6 omissions / 3 blocked) instead of "a carrier exists".
6. `status_audit.py:274` prose: attribute the 5 and derive the sentence, or say "5 are T-10's".
7. `VOCABULARY.md`'s parts gap: either record `convertadf-failed` (228/232) in the doc's header and
   point absence scans at the `jc3adf` decode G2-13/G2-14 use, or regenerate the block — until then
   every parts-module absence claim is a 4-train sample.

## Commands run (all read-only)

```
python Tools/scripts/t10_reopen.py --check
python -c "… T_ROWS.jsonl …"                 (198 rows; dispo census; superseded ids)
python -c "… tmp/freebuff/pre_t10/T_ROWS.jsonl …"   (105 rows; the 8 pre-T-10 out rows)
python -c "… tmp/freebuff/pre_t10/T6_HUD_CAMERA.md …" (the 7 pre-T-10 out rows)
python -c "… E:/Modding/JustCause3/_grab/entities/*.ee.json …"  (module types, errors, VehicleParts,
                                                          DriverLean, CustomLandGlobal, HelicopterSteering)
grep/find over E:/Modding/JustCause3/_grab/hud/dec           (260 .as; shield, tether, battle, energy, zoom …)
grep -o '"path": *"ui/[^"]*\.gfx"' Research/JC3Grab/INDEX.jsonl | sort -u
grep over Research/JC3Grab/{VOCABULARY,ENTITIES,TETHER,DAMAGE_MODEL,FORCEPULSE,TURRET,EMP,LIGHT_SYSTEM}.md
grep/sed over Working/Translation/{T7_WEAPONS,T11_MODES,T13_FX,T14_LIGHTS,BUILD_BATCHES}.md, STATUS.md
```

No `--write`, no game, no `D:/Games`, no build, no commit.
