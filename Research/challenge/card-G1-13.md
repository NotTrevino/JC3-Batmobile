# G1-13 · Sockets in JC3 space — assumption challenge

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), card **G1-13** (line 457), its §12 row (line 1281),
`MODLOG.md` §"G1-13 · Sockets — done", and the card's outputs
`Research/BatmobileGrab/SOCKETS_JC3.{json,md}`, `Tools/scripts/grab_sockets.py`,
`Tools/scripts/grab_model.py::sockets()`, `BONES.json`, `LIGHTS.json`, `ANIMATIONS.json`,
`POSES.json`, `MESHES.md`, `Working/TrueScale/stations.json`.

Read-only apart from this file. No game launched, nothing written to `D:/Games`, no commit.
All numbers below come from commands run in this session; quoted output is verbatim.

---

## VERDICT

The card's core deliverable holds up: the 65 socket records are real `SkeletalMeshSocket`
objects with a positional layout that can be read off the tag offsets, the rotator decode is
validated by two independent physical anchors, the 65/65 placement is reproducible, and
`--check` passes today. Two claims do **not** survive contact with the data:

* **BROKEN — "GRB-8 has 6 orphan light references".** Re-derived from the same dump, **15**
  light entries name a socket that the shipped mesh of *their own* package does not define.
  Nine of them are hidden because `grab_model.sockets()` falls back from `(package, name)` to a
  bare `name`, so an MK2/Funhouse light silently inherits a **Batmobile** bone.
* **WEAK — one rotation convention.** Positions use `qrot(bone_q, local, inverse=True)`; the
  forward/up/right columns use `qrot(socket_q · bone_q, axis)` with **no** inverse. Those two are
  mutually inconsistent for any socket whose composite rotation is not 0° or 180°. On this data
  the axis convention is the one that is physically anchored, which puts the **positions of 13
  sockets** (0.4–1.1 m apart between the two conventions) in doubt.

| # | assumption | verdict |
|---|---|---|
| A1 | the socket record layout (name, bone, location, rotation) can be read positionally | HOLDS |
| A2 | a missing rotator means identity; a missing location means the bone pivot | HOLDS |
| A3 | `FRotator` → PSK quaternion (Pitch, Yaw, Roll; 65536/turn) is decoded, not guessed | HOLDS |
| A4 | forward/up/right = `R(socket)·R(bone)` applied to local +X/+Y/+Z | HOLDS (physically) |
| A5 | positions and axes use the same rotation convention | **WEAK** (13 sockets, unresolved) |
| A6 | "61/65 inside the body box expanded by 0.5 m" proves the transform | WEAK (no discriminating socket) |
| A7 | the 65 decoded sockets are *all* the Batmobile_V2 sockets | HOLDS |
| A8 | one 65-socket table serves the mod ("the anchor table every later step uses") | WEAK (other skins: 55/63/64) |
| A9 | "GRB-8 has 6 orphan light references" | **BROKEN** (15) |
| A10 | `HeadLight1c`/`HeadLight2c` really have no carrier | HOLDS |
| A11 | the 6 `HeadLight*` sockets are "door-bound" | WEAK (name-based; bone's motion is unreadable) |
| A12 | the 4 `HangFromRope` anchors are "2.446 m above the box **by design**, not transform drift" | HOLDS for "not drift", WEAK for "by design" |
| A13 | `MissileLaunchSockets` → `MissileL`/`MissileR` is inferred, not read | HOLDS (disclosure correct) |
| A14 | units and frame (cm → m, X width, Y up, nose −Z, +X = left) | HOLDS (inherited per R2) |
| A15 | the `up_jc3` column means "up" | WEAK (it is local +Y = width; `right_jc3` is the up axis) |
| A16 | `forward` can be read as the direction a light/FX emits | WEAK (true for muzzle/tail/headlight, false for Afterburner) |

---

## A1 — The socket record layout is read positionally

**Claim.** `grab_model.sockets()` takes the first two `NameProperty` values as (socket, bone),
the first `VectorProperty` as the relative location and the first `RotatorProperty` as the
relative rotation, on an offset-only tag stream.

**Test.** Dump one raw record and the tag offsets of every record that is missing a field.

```
$ python - <<'PY'
... for p,t in g.tags(rows[0]): print(p, t.get("type"), t.get("value"))
<0x0054> NameProperty None Afterburner
<0x005C> NameProperty None JetSMove
<0x0064> VectorProperty None [-205.056992, 0.970673, -0.499941]
<0x0070> RotatorProperty None [32768, -32768, 0]
```

`0x0054 → 0x005C → 0x0064 → 0x0070` is an unbroken `FName(8) + FName(8) + FVector(12) +
FRotator(12)` struct, in that order, with no gap. Every one of the 65 records that carries both
vectors uses exactly `['<0x0054>', '<0x005C>', '<0x0064>']` or adds `'<0x0070>'`.

Two independent cross-checks agree: the second name resolves in `BONES.json` for 65/65 sockets,
and the first name matches the names `LIGHTS.json` uses to reference sockets
(`HeadLight1`, `BootLight`, … 101 light entries).

No record is silently dropped: `SkeletalMeshSocket` rows in `Playable_Batmobile_SF` = **65**,
and `sockets()` guards `if len(socks) != 65: raise`.

**Result: HOLDS.** The layout is structural, not "first vector looks like a location".

## A2 — Missing rotator = identity, missing location = bone pivot

**Claim** (`SOCKETS_JC3.md` §Convention): "A null rotator is identity. A null location
(`DriverAnimOrigin`) places the socket at its bone pivot." Counts: 26 missing rotations, 1
missing location.

**Test.** If the exporter wrote every field, absent fields would mean "unknown". If it omits
fields whose value is zero, absent fields mean exactly zero. Evidence:

* 26 records have 3 tags (`name, bone, location`) and no `0x0070` rotator.
* 1 record (`DriverAnimOrigin`) has 2 tags and no `0x0064` vector either.
* **No record in the package carries a zero-valued vector**: the query for a socket whose first
  `VectorProperty` is `(0,0,0)` printed an empty list.

So the dump demonstrably omits zero-valued fields (a zero location is written as *no* location),
which makes a zero rotator written as *no* rotator the consistent reading.

**Result: HOLDS**, as an inference that is supported by the omission behaviour. It is not
"decoded": nothing on disk states identity for those 26.

## A3 — The rotator → quaternion conversion is right

**Claim.** `rotator_quat()` treats the raw triple as UE3 `FRotator(Pitch, Yaw, Roll)` with
65536 units per turn, and composes `q = (cr·sp·sy − sr·cp·cy, −cr·sp·cy − sr·cp·sy,
cr·cp·sy − sr·sp·cy, cr·cp·cy + sr·sp·sy)`.

**Test — magnitude and sign of pitch on sockets whose bone rotation is identity.**
`Mine1..8` carry `[11325, 0, 0]`; `11325/65536×360 = 62.20°`. The record's forward is
`[0.000, 0.885, -0.466]`, i.e. `asin(0.885) = 62.2°` above the plane. `MissileL`/`MissileR`
carry `[8192, 0, 0]` = 45.0° and forward `[0.000, 0.707, -0.707]` = exactly 45° elevation.
`Dashboard`, `SpeedLines`, `FearGasTrail2L/R` carry `[0, 32768, 0]` (180° yaw) and their forward
is exactly `+Z`, the reverse of `Driver`'s `−Z`.

**Result: HOLDS.** Pitch maps to elevation with the right magnitude and sign on three separate
anchors, yaw maps to the ±Z reversal, and the zero component comes out exact.

## A4 — forward/up/right from `R(socket)·R(bone)`

**Claim** (`grab_sockets.py` docstring): forward is local +X through "socket rot \* bone bind
rot \* JC3 rotation"; "the muzzle and tail checks below prove the convention on known anchors".

**Test — physical semantics.** I recomputed all three axes under every plausible composition
order. Over 65 sockets × 3 axes the maximum error against the stored columns was:

```
R_bone*R_sock          max error = 1.995861
R_bone^-1*R_sock       max error = 2.000000
R_sock*R_bone          max error = 0.000001     <- what the file contains
R_sock*R_bone^-1       max error = 2.000000
R_bone only            max error = 2.000000
R_bone^-1 only         max error = 2.000000
q_sq*q_bone applied    max error = 0.000001
q_bone*q_sq applied    max error = 1.995861
```

That only reproduces the code. The discriminating test is where the sockets sit versus where
they point:

```
HeadLight1        pos=[-0.45 0.69 -2.98]  stored fwd=[0,-0,-1]  inverse fwd=[1,0,0]
Headlight_Centre  pos=[-0.00 0.65 -3.16]  stored fwd=[0,-0,-1]  inverse fwd=[1,0,0]
CannonMuzzle      pos=[ 0.00 1.70 -0.46]  stored fwd=[0,-0,-1]  inverse fwd=[1,0,0]
ChainGunMuzzle    pos=[-0.41 1.55 -0.17]  stored fwd=[0,-0,-1]  inverse fwd=[1,0,0]
RiotSuppressor…   pos=[ 0.39 1.45  0.14]  stored fwd=[0,-0,-1]  inverse fwd=[1,0,0]
BrakeLightL       pos=[-0.48 0.73  3.34]  stored fwd=[0.127,0,0.992]  inverse=[-0.992,0,-0.127]
SideExhaustL      pos= x=+1.174 (left)    stored fwd x=+0.757 (outboard)
SideExhaustR      pos= x=-1.173 (right)   stored fwd x=-0.764 (outboard)
```

The stored columns make 7 headlights and 3 muzzles point out of the nose at `−Z`, both brake
lights out of the tail at `+Z`, and both side exhausts outboard. The alternative convention makes
every one of them point sideways (`+X`) or back into the car (`+Z`) — 13 anchored sockets all
agreeing on the stored convention cannot be chance.

**Result: HOLDS**, on physical semantics rather than on algebra. Note the docstring's "socket rot
\* bone rot" is ambiguous about multiplication order, and the order that matches the file is
`R(socket)·R(bone)`, i.e. `qmul(lq, bwq)`.

## A5 — Positions and axes use the same convention — WEAK

**Claim (silent).** `world_position: bone pivot + qrot(bone q, relative location, inverse=True)`
and `forward: qrot(socket rot * bone rot, +X)` are two uses of the same bind rotation, so they
must share a sign convention.

**Test.** They do not. For every socket whose bone rotation is not 0°/180°, the inverse-convention
direction disagrees with the stored direction by 60–180°:

```
socket-axis rows that disagree with the position-consistent (inverse) derivation: 55
distinct sockets affected: 24 of 65
Cockpit_Hologram   180->  86.9 .. 103.7 deg
Dashboard_Light    60.0 / 60.0 deg
HangFromRope_*     180.0 deg
```

and the positions of 13 sockets move by 0.4–1.1 m when the position formula is flipped:

```
BrakeLightL   bone_pivot=[-0.89 1.23 0.64]  inverse=[-0.48 0.73 3.34]  forward=[-0.48 1.42 3.38]
ZapperRL      bone_pivot=[-0.89 1.23 0.64]  inverse=[-0.48 1.53 3.48]  forward=[-0.48 2.23 3.31]
LWheelLight   bone_pivot=[-1.21 0.70 -2.57] inverse=[-1.21 0.96 -2.06] forward=[-1.21 0.96 -3.08]
HangFromRope_Front_Left  inverse=[-1.58 5.31 -2.59] forward=[-0.84 5.31 -2.55]
rotated-bone sockets where the two conventions differ: 13   discriminating: 0
```

"discriminating: 0" is the problem: no socket is inside the body box under one convention and
outside under the other, so the body-box check cannot arbitrate. The strongest independent
evidence (the physical anchor directions in A4) points at the **stored axes** being right, which
implies the **position** formula is the one that is wrong for rotated bones — the 13 sockets
above would then be 0.4–1.1 m out. The alternative reading (positions right, axes wrong) is
excluded by A4.

Note this is the same rotation that `BONES.json` justifies as "that is what reproduces umodel's
own glTF inverse-bind matrices". Re-reading `grab_bones.gltf_check()`, that check compares only
`np.linalg.inv(mats)[:, :3, 3]`, i.e. **translations**. The rotation half of the PSK convention
is not covered by any glTF check, so the inverse sign is anchored on translations only — which is
exactly why it can be right for bone pivots and wrong for socket positions.

**Result: WEAK.** 13 of 65 positions are convention-dependent and the record gives the two halves
different signs. The card never states which convention positions use relative to the axis
columns, so a consumer cannot tell that the two columns are not in the same frame.

## A6 — "61/65 inside the body box +0.5 m" tests the transform — WEAK

**Claim.** 61/65 inside `stations.json body_bbox` expanded by 0.5 m; the 4 outside are the rope
anchors.

**Test.** Recount and probe the sensitivity:

```
inside raw (unpadded) body box: 60 of 65
outside raw box: DriverAnimOrigin [-0 0.022 0.154] -> outside_by_m 0.0
                 HangFromRope_Front_Left/Right, Rear_Left/Right  -> 2.4457 m each
```

`DriverAnimOrigin` sits 6.9 cm *below* the body's lower face and only passes because of the
arbitrary 0.5 m pad, and `outside_by_m` is measured against the padded box, so it reads `0.0`
for a socket that is outside the real box. More importantly, the test has no power: a wrong
socket transform of the size seen in A5 (0.4–1.1 m) still lands inside a box that is already
~7.0 × 3.5 m and padded by 0.5 m on every side.

**Result: WEAK.** It is arithmetic that is done correctly, but "61/65 inside" is not evidence
that the placement is right. The passes that do carry force are `muzzle_forward`, `tail_forward`
and `missile_forward_up`.

## A7 — 65 is all of the Batmobile_V2 sockets

**Test.** Independent count of `SkeletalMeshSocket` rows per package straight from the dump, and
the card's own "In" figure of 247:

```
Playable_BatmobileFunhouse_SF     63 sockets
Playable_BatmobileJoker_SF        64 sockets
Playable_BatmobileMK2_SF          55 sockets
Playable_Batmobile_SF             65 sockets
total 247
```

247 matches the card's `MECHANICS.md §Sockets (247 sockets, 65 on Batmobile_V2)` to the socket,
and 65 for the working package. Names are unique inside the package (65 rows → 65 keys, no
`setdefault` collision).

**Result: HOLDS.**

## A8 — One 65-socket table is "the anchor table every later step uses" — WEAK

**Test.** Compare the four skins by name and by bone:

```
Playable_BatmobileFunhouse_SF | same names: 62 | only here: ['HydraSocket'] | missing: ['Dashboard_Light','Headlight_Centre','PassengerNoiseOrigin']
Playable_BatmobileJoker_SF    | same names: 62 | only here: ['BatmobileAttach','HydraSocket'] | missing: ['Dashboard_Light','Headlight_Centre','PassengerNoiseOrigin']
Playable_BatmobileMK2_SF      | same names: 55 | only here: [] | missing: ['BrakeTrailL','BrakeTrailR','Dashboard_Light','Headlight_Centre','LWheelLight', …]  (10 names)

same name, different bone: 6 in each of the three skins — HeadLight1/1a/1b/2a/2b
Playable_Batmobile_SF:  HeadLight1 -> Winch_DOOR_Mesh
Playable_BatmobileMK2/Joker/Funhouse:  HeadLight1 -> Batmobile_Chassis
```

The card is worded "for every `Batmobile_V2` socket", so the *sentence* is scoped correctly. But
`SOCKETS_JC3.md` is titled "the anchor table every later step uses", G1-19/T-13 depend on it, and
a mod that ships the MK2 or Jokerified skin inherits a table that is missing 10 socket names and
has 6 headlights on a different bone. There are 182 sockets in the three skins that this card
does not place.

**Result: WEAK.** Fine as Batmobile_V2-only, unsafe as a fleet anchor table; the 6 headlight
bone differences are the kind of thing that silently breaks a door/light implementation.

## A9 — "GRB-8 has 6 orphan light references" — BROKEN

**Claim** (`SOCKETS_JC3.md`, `SOCKETS_JC3.json.verdict`, §12 row, MODLOG): "GRB-8's six orphan
light references are `HeadLight1c`/`HeadLight2c` in Batmobile, MK2 and Funhouse (2 here, 6 across
the three packages)"; `checks.grb8_orphan_refs_total_6 = PASS`.

**Test.** Re-derive "light entry whose socket name is not a `SkeletalMeshSocket` in the shipped
mesh of *its own* package", straight from the same two inputs, and compare with the flags
`LIGHTS.json` carries:

```
Playable_BatmobileFunhouse_SF    entries= 28 flagged_orphan=2 truly_absent=3  ['Dashboard_Light','HeadLight1c','HeadLight2c']
Playable_BatmobileJoker_SF       entries= 17 flagged_orphan=0 truly_absent=0  []
Playable_BatmobileMK2_SF         entries= 28 flagged_orphan=2 truly_absent=10 ['Dashboard_Light','HeadLight1c','HeadLight2c','LWheelLight','LWheelLight_bottom','LWheelLight_top','RWheelLight','RWheelLight_bottom','RWheelLight_top']
Playable_Batmobile_SF            entries= 28 flagged_orphan=2 truly_absent=2  ['HeadLight1c','HeadLight2c']
```

15 absent-socket references, not 6. The 9 that are not flagged are not flagged because of a
cross-package resolve in `grab_model.sockets()`:

```python
sock = sockets.get((r["package"], socket)) or sockets.get(socket) or {}
```

Nine entries therefore get a bone from a **different skin**:

```
('Playable_BatmobileMK2_SF','LWheelLight',   ['Funhouse','Joker','Batmobile'], 'Wheel_Frnt_Left_Disc', orphan=False)
('Playable_BatmobileMK2_SF','RWheelLight',   ['Funhouse','Joker','Batmobile'], 'Wheel_Frnt_Right_Disc', orphan=False)
('Playable_BatmobileMK2_SF','LWheelLight_top' / '_bottom' / 'RWheelLight_top' / '_bottom', same)
('Playable_BatmobileMK2_SF','Dashboard_Light', ['Playable_Batmobile_SF'], 'Batmobile_Chassis', orphan=False)
('Playable_BatmobileFunhouse_SF','Dashboard_Light', ['Playable_Batmobile_SF'], 'Batmobile_Chassis', orphan=False)
```

This is R5 in its textbook form: the entry is "carried" by the member whose *name* matches, not
by a member that exists in that mesh. It also means the MK2's 6 wheel lights and dashboard light
are reported as resolved when the MK2 mesh defines none of them.

The card's count is a count of flags in `LIGHTS.json`, re-derived by nothing: `checks
.grb8_orphan_refs_total_6` reads `len(orphan_refs) == 6` where `orphan_refs` is filtered on
`e.get("orphan_socket") or e.get("bone") is None` — a tautology over the upstream flags.

Within `Playable_Batmobile_SF` alone the number is right (2), so the G1-13 package-scoped claim
survives; the fleet sentence, and the §12 row's "6 GRB-8 orphan refs", do not.

**Result: BROKEN.** 6 → 15 (or, stated the other way: 9 references are orphans that the pipeline
hid by borrowing another skin's bone).

## A10 — `HeadLight1c`/`HeadLight2c` really have no carrier

**Test.** Search every exported object for the names:

```
$ python … json.dumps(row) contains "HeadLight1c" or "HeadLight2c"
Playable_BatmobileFunhouse_SF RVehicleBatmobile BatmobileFunhouse | socket rec? False
Playable_BatmobileMK2_SF      RVehicleBatmobile Batmobile_MK2      | socket rec? False
Playable_Batmobile_SF         RVehicleBatmobile Batmobile          | socket rec? False
rows mentioning 1c/2c: 3
```

Three rows, one per package, all the `RVehicleBatmobile` archetype (each holding both names) —
6 references, zero socket definitions, and the `1a/1b/2a/2b` siblings do appear as sockets
(`grep -o '"HeadLight[12][abc]"' objects.jsonl` → 7 occurrences for each of 1a, 1b, 2a, 2b vs 3
for 1c and 3 for 2c). So the "no carrier" conclusion is right *for these two names* and right
because the search covered every object, not a sample.

**Result: HOLDS.**

## A11 — The 6 `HeadLight*` sockets are "door-bound" — WEAK

**Claim.** "Six `HeadLight*` sockets ride `Winch_DOOR_Mesh` … a future winch-door part must carry
them." `door_bound` is computed as `s["bone"] == "Winch_DOOR_Mesh"`.

**Test.** Ask the data whether that bone is a door that moves.

```
POSES.json, G1-12 tank-spread pair:
  Winch_DOOR_Mesh  parent=Batmobile_Nose_Mesh  translation=(0,-0.022,0.002)
                   rotation 0.542 deg, articulated=false, local_rotation 0.0

ANIMATIONS.json, 253 sequences:
  sequences where Winch_DOOR_Mesh is active: 4   moved: 0
  removed_tracks[Winch_DOOR_Mesh] distribution: {'all': 144, None: 105, 'trans': 4}

Playable_Batmobile_SF   HeadLight1 -> Winch_DOOR_Mesh
Playable_BatmobileMK2/Joker/Funhouse  HeadLight1 -> Batmobile_Chassis
```

The bone is inert in every animation that has a readable track for it (0 moved), and in 144
sequences its track was **removed** entirely, so its motion is unknown rather than nil. Its
parent is `Batmobile_Nose_Mesh`, not a hinge bone. The other three skins put the same 6 sockets
on `Batmobile_Chassis`.

So "door-bound" is the name read as the behaviour (R5). It may well be right — the nose assembly
on this car does carry a winch door — but nothing on disk shows the bone rotating, and the
consequence the card draws ("a future winch-door part must carry them") rests on the name alone.

**Result: WEAK.** The bone name and the shared-parent fact are real; the behaviour is unverified.

## A12 — The rope anchors are "2.446 m above the box by design"

**Claim.** "They are placed correctly and are not a transform error; the body box check simply
excludes them."

**Test.** The number comes straight out of the decoded local offset and is convention-invariant
vertical:

```
HangFromRope_Front_Left   bone=Wheel_Front_Left   local=[36.7, -2.4, 460.5] cm
                          inverse=[-1.58 5.31 -2.59]   forward=[-0.84 5.31 -2.55]
HangFromRope_Rear_Left    local=[29.2, -17.2, 460.5] cm
```

`460.5 cm` of bone-local Z (PSK up) survives every rotation about Z, and `y = 5.308 m` in both
conventions, while the body box top is `2.362 m` — hence 2.446 m in all four cases. So it is
**not** transform drift: it is what the cooked record says, and it is invariant under the A5
ambiguity.

**Result: HOLDS** for "not drift". **WEAK** for "by design": no file says what the anchors are
for, the height is 4.6 m above the wheel pivots, and under A5 the horizontal share differs by
0.7 m between conventions. "By design" is a plausible story, not evidence.

## A13 — `MissileLaunchSockets` → `MissileL`/`MissileR` is inferred

**Claim.** "the array-to-socket mapping is stated as inferred, not read."

**Test.** The array tag carries no members:

```
5 MissileLaunchSockets ArrayProperty 'MissileLaunchSockets' None
```

and the string `MissileL` occurs nowhere in `Research/BatmobileGrab/*.md` or `*.json` except this
card's own outputs:

```
Research/BatmobileGrab/ASSETS.md:184:| RBatmobileMissileLauncher | 3 |
(no file contains "MissileL" outside SOCKETS_JC3.*)
```

`FOOTAGE.md:122` already records "launch sockets | 2 | `MissileLaunchSockets` | array present,
contents not decoded (2 entries)". Note also that the array belongs to
`Batmobile_EMP_Missile_Launcher` (`RBatmobileEMPMissile`), not to `RBatmobileMissileLauncher`, so
the 2-entry array and the 2 physical sockets agree in count but are attached to different
objects.

**Result: HOLDS** as a disclosure — the card says exactly what it knows. The mapping itself
remains unproven; the count agreement is the only support, and it is a coincidence-shaped one.

## A14 — Units and frame

**Claim.** JC3 metres, X width, Y up, Z length, nose at −Z; `to_jc3_rot(p) × 0.01 + offset`,
offset `[-0.0000005, 0.0222314, 0.1542974]` from `stations.json` (R2, one transform).

**Test.** `to_jc3_rot` maps PSK axes to `X→−Z, Y→−X, Z→+Y`. Checks against independent files:

* `stations.json body_bbox` spans x `-1.747…1.748` (3.495 m), y `0.091…2.362` (2.271 m), z
  `-3.42…3.605` (7.025 m). `MESHES.md` gives `Batmobile_V2` as `702.560 × 349.530 × 234.185` —
  length/width/height in the same ratio, so `0.01` is the right cm→m factor and the length axis
  really is Z.
* All 7 headlights sit at z ≈ −3.0…−3.16 (nose) with forward −Z; both brake lights at z ≈ +3.33
  with forward +Z; `WinchOrigin` at z −2.711, `Afterburner` at z +3.393.
* `+X = left` follows from the PSK Y → −X mapping (PSK +Y is UE right), and is consistent with
  `MissileL` at x = +0.594 and `MissileR` at x = −0.589.

**Result: HOLDS**, inherited from `bat_assemble`/G1-11 and consistent with the geometry files.
It is not re-derived in this card (correctly, per R2).

## A15 — The `up_jc3` column is "up" — WEAK

**Claim.** `convention.up = "socket local +Y through the same rotations"`, and the md calls local
+Y "up".

**Test.** `BONES.md` states the PSK frame is "X length, Y width, Z up". For an identity socket on
an identity bone (`Headlight_Centre`):

```
forward = [0, -0, -1]      (local +X -> nose)
up      = [-1, -0, -0]     (local +Y -> world -X, horizontal)
right   = [-0, 1, -0]      (local +Z -> world +Y, the actual up)
```

So the column named `up_jc3` is the car's **width** axis and `right_jc3` is the car's **up** axis.
This is conscious in the docstring ("The up vector is local +Y") but the field names, the md's
"Convention" bullet and any later consumer will read `up`/`right` as physical up/right.

**Result: WEAK.** Values correct, names wrong-but-documented. Anyone computing a lamp's vertical
tilt from `up_jc3` gets a 90° error.

## A16 — `forward` is the emission direction — WEAK

**Claim.** Implicit in `muzzle_forward` / `tail_forward` / `missile_forward_up` and in how the
card labels the column.

**Test.** Two sockets break it:

```
Afterburner        bone=JetSMove                 pos z=+3.393 (rear)  forward=[0,0,-1]  (into the car)
Afterburner_Front  bone=Batmobile_Chassis_Mesh   pos z=-2.930 (nose)  forward=[0,0,+1]  (into the car)
Cockpit_Hologram   up=[-0.009,-0.974,0.224]      (up points down)
Dashboard_Light    forward=[0,0.5,0.866]         (30 deg backward and up)
```

The afterburners are at the two ends and point *inward*, i.e. the effect blueprint's axis on that
socket is not +X. The docstring is careful ("This is the socket's frame, not an assumption about
where a muzzle points; the muzzle and tail checks prove the convention on known anchors"), and
the anchors it chose do support it — but the good result on 13 anchors does not generalise to all
65, and `Afterburner` is a named card anchor (G1-13 "Include at least … `Afterburner`,
`Afterburner_Front`") whose forward is not usable as a flame direction.

**Result: WEAK.** Correct as a raw basis, unsafe as a semantic "this is where it fires" column.

---

## Cross-cutting notes

* **R11 (counts generated, never typed).** The tables in `SOCKETS_JC3.md` are generated and
  `python Tools/scripts/grab_sockets.py --check` passes today (all 16 checks PASS, run in this
  session). The one count that is *not* re-derived is `grb8_orphan_refs_total_6`, which re-counts
  `LIGHTS.json`'s own flags (A9).
* **What would move this from "sound" to "tight"**, in order of value:
  1. Decide A5/A15 with one more anchor: a socket whose *position* is visible in the mesh (e.g.
     `LWheelLight_top` against the wheel-disc vertices). That is a geometric test, not a game
     launch, and it settles whether positions use `inverse=True` for rotated bones.
  2. Fix `grab_model.sockets()`'s bare-name fallback to be package-strict (or mark fallback
     resolutions) and re-derive the orphan count. Expect 15 fleet / 2 in this package.
  3. Add the three other skins' socket tables (182 sockets) or mark `SOCKETS_JC3.md` explicitly
     as `Playable_Batmobile_SF` only, with the 6 headlight-bone differences listed.
  4. Rename `up_jc3`/`right_jc3` to `local_y_jc3`/`local_z_jc3` (or `axis_width`/`axis_up`).
* **Not testable here:** whether UE3 actually attaches a light to a missing socket at the
  component origin (A9's runtime consequence), and whether `Winch_DOOR_Mesh` ever rotates
  (A11) — both need a game or a track dump the export does not carry.
