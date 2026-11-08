# Weapon points in bm-RC2 vs the BmAK sockets - DONE report

STATUS: done. bm-RC2's `.epe` carries **9** `SWeaponPoint` objects. 5 of them name a BmAK
socket; all 5 sit exactly on it after the repo's single conversion (max |d| **0.000 cm**,
band 0.01 cm). The other 4 are type-4 `attach.vehicle` mount markers cloned from the APC
template - they have no BmAK socket, so their position stays UNKNOWN rather than being
scored. `--check` passes (7/7 gates) and re-derives the `.md` byte for byte. Read-only: the
build tree was not modified; the `.epe` is exported to a temp directory.

## Files written

| file | what |
|---|---|
| `Builds/bm-RC2/verify/weapon_points_vs_bmak.md` | the table: point, built position, BmAK socket position, per-axis and total difference in cm, band, status |
| `Tools/scripts/v_weapon_points_rc2.py` | `--write` / `--check`; `--check` re-exports the `.epe`, re-runs the socket->world step and the transform, and diffs the md |
| `tmp/freebuff/reports/weapon-points-vs-bmak.md` | this report |

Earlier briefs of this session are also complete, and their DONE paths exist
(`tmp/freebuff/reports/v05-combat-rewrite.md`, `t-rows-no-evidence.md`,
`review-tint-impact.md`).

## The conversion, and where it is decoded

```text
JC3 = to_jc3_rot(PSK_cm) * scale + offset        to_jc3_rot(p) = (-py, pz, -px)
scale = 0.01        offset = (-0.000000, 0.022231, 0.154297)
```

* `to_jc3_rot`: `Tools/scripts/bat_assemble.py`, the `to_jc3_rot` def (PSK X length, Y
  width, Z up -> JC3 X width, Y up, Z length, nose -Z; proper rotation, det +1).
* `scale`/`offset`: `Working/TrueScale/stations.json` (`scale`, `offset`).
* socket -> rig world `bone pivot + qrot(bone world q, local, inverse=True)`:
  `Tools/scripts/grab_sockets.py` (the `wp = bwp + qrot(...)` line), also recorded as
  `convention.world_position` in `Research/BatmobileGrab/SOCKETS_JC3.json`.
* combined rule: `SOCKETS_JC3.json` `convention.jc3_transform`.

The BmAK column is **derived**: the script re-runs that step from each socket's own
`relative_location_cm` and `BONES.json`'s bind world position/quaternion rather than
copying the stored `position_m`. Gate `conversion_reproduces_sockets_json` proves the
re-derivation lands on the stored values (max delta 4.86e-07 m).

## Result table (also in the md)

| point | parent component | built (m) | BmAK socket (m) | |d| (cm) | status |
|---|---|---|---:|---:|---|
| `CannonMuzzle` | `w602_mediumtank_canon` | 0.000339, 1.702497, -0.455945 | 0.000339, 1.702497, -0.455945 | 0.000 | match |
| `attach.vehicle` | `w602_mediumtank_canon` | 0.000000, -0.054057, 0.002083 | - | - | UNKNOWN |
| `attach.vehicle` | `w603_mediumtank_mgun` | 0.000000, -0.054057, 0.002083 | - | - | UNKNOWN |
| `ChainGunMuzzle` | `w603_mediumtank_mgun` | -0.407368, 1.551869, -0.166883 | -0.407368, 1.551869, -0.166883 | 0.000 | match |
| `MissileL` | `w618_sportsmuscle_missile` | 0.593771, 1.484682, -1.146810 | 0.593771, 1.484682, -1.146810 | 0.000 | match |
| `attach.vehicle` | `w618_sportsmuscle_missile` | 0.000000, -0.054057, 0.002083 | - | - | UNKNOWN |
| `MissileR` | `w618_sportsmuscle_missile` | -0.588846, 1.489689, -1.146764 | -0.588846, 1.489689, -1.146764 | 0.000 | match |
| `BattleModeSpotLight` | `w618_sportsmuscle_missile_emp` | 0.000378, 1.834583, -0.066368 | 0.000378, 1.834583, -0.066368 | 0.000 | match |
| `attach.vehicle` | `w618_sportsmuscle_missile_emp` | 0.000000, -0.054057, 0.002083 | - | - | UNKNOWN |

Pass band 0.01 cm (0.1 mm), **derived**: the export prints metres with 6 decimals, so one
quantum is 1e-6 m = 1e-4 cm; the band is 100x that and still ~1000x below any physically
meaningful offset on a 5 m car. Verdicts are `match` / `UNKNOWN`; a value outside the band
would print `MISMATCH` and fail `mounts_within_band`.

Two findings worth keeping:

* **`BattleModeSpotLight` is the BmAK launch socket by name, not a missile tube.**
  `WEAPONS.md` records `RPursuitModeMissileLauncher.LaunchSocketName = "BattleModeSpotLight"`
  (member table, 0x0984). The socket itself rides `Batmobile_Rig_Weapons_Drone_Decoder`;
  the two physical missile sockets are `MissileL`/`MissileR`. So the EMP point follows
  BmAK's own launch-socket name, but it is the spotlight/decoder anchor.
* **The 4 `attach.vehicle` rows are not positions.** Type 4 (`MountAttach`), cloned from
  the APC template with identity rotation and the template offset `0, -0.05405688,
  0.002082527`; they name the chassis parts (`80201E4D` / `5C19E7E0`), not a fire point.

## Commands, verbatim

```text
$ python Tools/scripts/v_weapon_points_rc2.py --write
wrote Builds/bm-RC2/verify/weapon_points_vs_bmak.md: 9 points, 5 compared, max |d| 0.000 cm
  CannonMuzzle           0.000339, 1.702497, -0.455945  match    0.000 cm
  attach.vehicle         0.000000, -0.054057, 0.002083  UNKNOWN (no BmAK socket)
  attach.vehicle         0.000000, -0.054057, 0.002083  UNKNOWN (no BmAK socket)
  ChainGunMuzzle         -0.407368, 1.551869, -0.166883  match    0.000 cm
  MissileL               0.593771, 1.484682, -1.146810  match    0.000 cm
  attach.vehicle         0.000000, -0.054057, 0.002083  UNKNOWN (no BmAK socket)
  MissileR               -0.588846, 1.489689, -1.146764  match    0.000 cm
  BattleModeSpotLight    0.000378, 1.834583, -0.066368  match    0.000 cm
  attach.vehicle         0.000000, -0.054057, 0.002083  UNKNOWN (no BmAK socket)
```

```text
$ python Tools/scripts/v_weapon_points_rc2.py --check
  point_count_9                            PASS
  socket_points_5                          PASS
  attach_points_4                          PASS
  all_socket_points_resolve                PASS
  conversion_reproduces_sockets_json       PASS
  mounts_within_band                       PASS
  file_matches_rederivation                PASS (7421 bytes of text)
OK: 5/9 points compared, max |d| 0.000 cm, band 0.01 cm
```

The export that feeds the parse (temp dir, read-only source):

```text
$ Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe -e Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe tmp/freebuff/scratch/rc2epe/rc2.xml
EXIT=0
```

Read-only check on the built graph, and evidence lookups:

```text
$ grep -c "SWeaponPoint" tmp/freebuff/scratch/rc2epe/rc2.xml
9
$ grep -n "LaunchSocketName" Research/BatmobileGrab/WEAPONS.md
846:| `RPursuitModeMissileLauncher.LaunchSocketName` | 0x0984 | NameProperty | "BattleModeSpotLight" |
```

## UNKNOWNs

* **Where the 4 `attach.vehicle` markers sit in BmAK terms.** No BmAK socket or bone of
  that name exists (checked the 65-socket list). They are template offsets. Would be found
  in: a BmAK `MountAttach` table, which this repo has not decoded.
* **Which `MissileLaunchSockets` array entry maps to which mesh socket.** `WEAPONS.md`
  decodes the array as shape only (2 items, 8 B each); the `MissileL`/`MissileR` pairing is
  inferred from name/location, not read from the array.
* **Whether JC3 uses a point's translation at runtime or only its rotation.** The numbers
  match a fleet vehicle's stored form; the engine side is native and not decoded in this
  repo.

## COMPROMISES

None. The audit is read-only; nothing was installed, launched or tested (test ban kept).
