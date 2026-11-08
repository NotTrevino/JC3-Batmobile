# The 4 `attach.vehicle` mount markers in bm-RC2 - DONE report

STATUS: done. The four type-4 points are the JC3 **mounted-weapon** (`MountAttach`) mechanism,
cloned from the APC's `w206` gun mount: they bind a weapon to a yaw part (`id:80201E4D`) and a
pitch/mount arm (`id:5C19E7E0`) **by name**. Their matrix is an identity rotation plus the one APC
template offset, and **no object in the `.epe` references their object ids** - the names are the
wiring. None of the four built weapons has a type-4 point in the donor; BmAK has a driver seat and
**no mount concept**, so there is no anchor to score them against and the position stays UNKNOWN.
`--check` passes (10/10 gates) and re-derives the `.md` byte for byte. Read-only: the `.epe` is
exported to a temp dir, no build file touched.

## Files

| file | what |
|---|---|
| `Builds/bm-RC2/verify/mount_markers.md` | the answer: 4-row marker table, donor census by type, per-weapon donor counterpart, reference analysis, BmAK seat/mount surface, deviations |
| `Tools/scripts/v_mount_markers.py` | `--write` / `--check`; `--check` re-exports the `.epe`, re-resolves the parts and the donor graph, diffs the md |
| `tmp/freebuff/reports/apc-mount-markers.md` | this card |

## What each of the four is (decoded)

| # | object id | parent weapon | `5C19E7E0` pitch arm | `80201E4D` yaw part | world (m) |
|---:|---|---|---|---|---|
| 1 | `EC9CC816=FFFF8003` | `w602_mediumtank_canon` | `batmobile_cannon` | `batmobile_turret` | 0.000000, -0.054057, 0.002083 |
| 2 | `B8D99B2D=FFFF8006` | `w603_mediumtank_mgun` | `batmobile_machine_gun` | `batmobile_turret` | same |
| 3 | `26287F48=FFFF8009` | `w618_sportsmuscle_missile` | `batmobile_missile_pod_r` | `batmobile_missile_pod_l` | same |
| 4 | `CAC72B9B=FFFF800D` | `w618_sportsmuscle_missile_emp` | `batmobile_missile_pod_r` | `batmobile_missile_pod_l` | same |

Decoded: `SWeaponPoint`, `type = 4`, `name = attach.vehicle`, `name_hash = 2049066765`,
`fire_effect = 0`, class hash `-405742323`; rotation identity, translation
`(0, -0.05405688, 0.002082527)` for all four.

## What the type-4 point does in the donor (decoded, `WEAPON_WIRING.jsonl`)

300 weapon points: type 0 x54, 1 x38, 2 x186, **4 x22**. All 22 type-4 points belong to
`w206_mounted_capstone_m2hm` (APC / technical jeep / armoured jeep / heavy patrol) and
`w616_corvette_canon`, bindings `mounted_weapon` / `mounted_weapon_2` / `main_weapon`, on 17
entities, and each names `<chassis>_weapon_mount_vertical` (pitch) on `<chassis>_turret_base` or
`_mount_horizontal` (yaw). The APC pair `apc_weapon_mount_vertical` / `apc_turret_base` is one of
seven such pairs - so type 4 is "a gun mounted on a chassis", not a tank cannon's fire point.

Per built weapon, in the donor:

* `w602_mediumtank_canon` - type **2** only (`fire_position_0`, naming
  `mediumtank_cannon`/`mediumtank_turret`), no type-4. The clone added one; its Batmobile part pair
  is a correct renaming of the tank pair, so it is the binding the turret port wants, carried on the
  mounted-weapon mechanism instead of the cannon's own point.
* `w603_mediumtank_mgun` - type **2** `fire_position_0` with no part strings. The marker makes the
  coax gun aimable by binding it to the turret pair.
* `w618_sportsmuscle_missile` - four type-**2** `internal.fire_point.N` points, no mount;
  `w618_sportsmuscle_missile_emp` is **not in the donor graph at all**. Both built missile weapons
  got the same marker pair, which **cross-pairs the pods**: `_r` as the pitch arm, `_l` as the yaw
  part.

## Does the wiring reference them?

* **By part name - yes, and only this.** `jc3wiring.py` `mount_parts()` (line 228) collects type-4
  strings that equal a chassis part name -> `WEAPON_WIRING.md` "mount parts"; `TURRET.md` reads the
  same two properties as yaw/pitch. `bm_entity.py` (731-748, 778) asserts every name resolves in
  the built module, so a wrong name would be caught; its tamper test rewrites one of these strings
  (MODLOG, B-05 rework). A wrong **name** matters.
* **By object id - no.** Each marker's object id occurs exactly once (`1, 1, 1, 1`), its own
  definition; no slot, property, part, interaction or physics object points at the point object.
* **Coordinates - read by nothing decoded.** Only the two strings are consumed.

## Would a wrong position matter?

In the entity graph, no: nothing reads the matrix. As a part binding, yes - that is what the turret
port copies. As coordinates it is unmeasured (the APC template offset) and only a risk if the
runtime reads `MountAttach` matrices, which is UNKNOWN.

## BmAK seat / mount concept

`SOCKETS_JC3.json`: **65 sockets**, roles include `driver`, `muzzle`, `missile`, `winch` - **no
`mount` or `attach` role**; the only name containing either word is `WinchAttach` (both winch
anchors, not weapon mounts). `COCKPIT.json`: 2 driver anchors - `Driver` hip socket
`(-0.0025, 0.8647, -1.0654)` and the anim origin `(0.0, 0.0222, 0.1543)` - plus the cockpit seat
material. So BmAK has a **seat** and no **weapon mount**; there is nothing to compare these four
with. (JC3 keeps the two apart too: a seat is `interaction.seat.gunner1` on
`point.mounted_weapon`; `attach.vehicle` binds parts.)

## Deviations recorded (facts, not failures)

* **0/4** built weapons has a type-4 point in the donor - all four markers are clone additions.
* **3/4** pitch arms are not `Cannon` parts (donor pitch census is 47/47 `Cannon`): `GatlingGun`
  for the MG arm, `None` for the pod arm. `GatlingGun` is a real parts behaviour (24 cached parts,
  `card-B-04.md`), so it is a new pairing, not a broken name.
* **2/4** mount arms are parented to the yaw part (donor shape); the pods break it -
  `batmobile_missile_pod_r` is on the body and paired with the other pod.
* Both missile markers are identical, so the EMP weapon did not get its own mount.
* Correction to the task-7240 card: these markers carry **no `A90F5E74` property** ("weapon_anchor");
  that id does not occur in the built `.epe` at all. Their only strings are the two part names.

## Commands, verbatim

```text
$ python Tools/scripts/v_mount_markers.py --write
wrote Builds/bm-RC2/verify/mount_markers.md: 4 markers
  w602_mediumtank_canon              mount=batmobile_cannon           yaw=batmobile_turret           oid_refs=1
  w603_mediumtank_mgun               mount=batmobile_machine_gun      yaw=batmobile_turret           oid_refs=1
  w618_sportsmuscle_missile          mount=batmobile_missile_pod_r    yaw=batmobile_missile_pod_l    oid_refs=1
  w618_sportsmuscle_missile_emp      mount=batmobile_missile_pod_r    yaw=batmobile_missile_pod_l    oid_refs=1
  ... 10 gates PASS
WRITE_EXIT=0
```

```text
$ python Tools/scripts/v_mount_markers.py --check
  four_markers                     PASS
  all_named_attach_vehicle         PASS
  identical_world                  PASS
  identity_rotation                PASS
  two_part_strings                 PASS
  parts_in_module                  PASS
  no_oid_reference                 PASS
  bmak_has_no_mount                PASS
  donor_type4_is_the_apc_mount     PASS
  cloned_offset_is_the_apc_offset  PASS
  file_matches_rederivation        PASS (11632 bytes)
OK
CHECK_EXIT=0
```

```text
$ Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe -e \
    Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe \
    <temp>/rc2.xml
EXIT=0
```

Evidence lookups that anchor the prose:

```text
$ grep -n "5C19E7E0\|80201E4D\|pitch part\|yaw part" Research/JC3Grab/TURRET.md
3:   ... the weapon's fire point names both parts in two unnamed string properties.
299: Every pitch part is a `Cannon` part. Yaw parts are `Turret` ... or plain parts on aircraft pods.
$ python -c "... TURRET.json['point_census'] ..."
{'pitch': {'Cannon': 47}, 'yaw': {'Cannon': 13, 'None': 44, 'Turret': 18}, 'points': 92, 'weapons': 52}
```

## UNKNOWNs

1. Whether JC3 reads a `MountAttach` matrix at runtime. No decoded file reads it; the engine is
   native. If it does, the APC offset would seat a mounted weapon wrongly and by how much is not
   derivable here.
2. Where a Batmobile weapon mount *would* sit. BmAK has no mount anchor, so there is no reference
   value.
3. Whether the missile pods should be aimable at all - the donor gives its sports-muscle missile no
   mount; the clone gives both missile weapons the APC's. A design choice, not a decoded value.
4. Whether the runtime aims a `GatlingGun` part like a `Cannon` one. The donor has no `GatlingGun`
   pitch arm (its pitch census is entirely `Cannon`).

## COMPROMISES

None. Read-only audit; nothing installed, launched or tested (test ban kept).
