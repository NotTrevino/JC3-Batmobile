# review-G3-10e — are the JC3 hinge limits really at +0x0FC/+0x100?

VERDICT: **CONFIRMED** (with the report's UNKNOWN list partly closed and one fleet-wide sign
exception found). G3-10e's offsets survive every attack I could make. The reason is now decoded
rather than plausible: `JustCause3.exe` itself names the atom at `+0x0F8` `TYPE_ANG_LIMIT`, and the
Havok SDK header puts `m_minAngle` at atom+4 and `m_maxAngle` at atom+8 inside that 16-byte atom, so
the pair really is `+0x0FC`/`+0x100`, the `+0x104` float is `m_angularLimitsTauFactor`, and the atom
ends at `+0x108`. The four plain `hkpHingeConstraintData` in the fleet carry no type-14 atom at all
and are exactly 80 B shorter, which kills the "it's the neighbouring motor atom" explanation. A
door/hood geometry test agrees with both the units and the sign. The only new problem is semantic:
16 fleet door rows pair their hinge axis with the opposite side to their pivot, so on four assets a
positive angle may open the panel inward — that is UNKNOWN, and it does not affect the decode.

Outputs written:

| file | what |
|---|---|
| `Tools/scripts/jc3_physics_limits2.py` | the review, `--write` / `--check`, 18 oracles |
| `Research/JC3Grab/PHYSICS_LIMITS_REVIEW.md` | the review page |
| `Research/JC3Grab/PHYSICS_LIMITS_REVIEW.json` | every row, plus the header quotes |
| `tmp/freebuff/reports/review-G3-10e.md` | this report |

Nothing else was edited: `Research/JC3Grab/PHYSICS_LIMITS.md`, `Tools/scripts/jc3_physics_limits.py`,
`DOOR_ANGLES.json` and the game installs are read-only inputs.

## 1. Evidence that did not come from a command (fetched document, quoted)

Havok SDK header (2009 build; the game is 2014.1, so it is used for enum order and struct field
order only), `https://raw.githubusercontent.com/nitaigao/engine-showcase/master/etc/vendor/havok/Source/Physics/ConstraintSolver/Constraint/Atom/hkpConstraintAtom.h`:

```
enum AtomType
{
    TYPE_INVALID = 0,
    TYPE_BRIDGE,
    TYPE_SET_LOCAL_TRANSFORMS,
    TYPE_SET_LOCAL_TRANSLATIONS,
    TYPE_SET_LOCAL_ROTATIONS,
    TYPE_BALL_SOCKET,
    TYPE_STIFF_SPRING,
    TYPE_LIN,
    TYPE_LIN_SOFT,
    TYPE_LIN_LIMIT,
    TYPE_LIN_FRICTION,
    TYPE_LIN_MOTOR,
    TYPE_2D_ANG,
    TYPE_ANG,
    TYPE_ANG_LIMIT,
    TYPE_TWIST_LIMIT,
    TYPE_CONE_LIMIT,
    TYPE_ANG_FRICTION,
    TYPE_ANG_MOTOR,
    TYPE_RAGDOLL_MOTOR,
    TYPE_PULLEY,
    TYPE_OVERWRITE_PIVOT,
    TYPE_CONTACT,
```

and, in the same file:

```
struct hkpAngLimitConstraintAtom : public hkpConstraintAtom
{
    hkUint8 m_isEnabled;
    hkUint8 m_limitAxis;
    hkReal  m_minAngle;   // Mininum angle value in radians (may be negative).
    hkReal  m_maxAngle;   // Maximum angle value in radians (may be negative).
    hkReal  m_angularLimitsTauFactor; //+default(1.0) +absmin(0) +absmax(1)
```

So: type code 14 = `TYPE_ANG_LIMIT`; the atom is 2+1+1+4+4+4 = 16 B; min at +4, max at +8, tau at
+12. `hkpTwistLimitConstraintAtom` and `hkpConeLimitConstraintAtom` put min at +8, max at +12 and tau
at +16 and are 24 B of fields (32 B with the atom alignment) — the sizes G3-10e measured.

## 2. Commands and output (verbatim)

### 2.1 The exe's own `AtomType` enum

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python - <<'EOF'
import re
p = r"D:/Games/Just Cause 3/JustCause3.exe"
b = open(p,'rb').read()
print("exe bytes", len(b))
idxs = [m.start() for m in re.finditer(rb"TYPE_ANG_LIMIT", b)]
print("TYPE_ANG_LIMIT at", [hex(i) for i in idxs])
for i in idxs[:3]:
    s = b[max(0,i-1200):i+2400]
    toks = re.findall(rb"[ -~]{3,}", s)
    print("=== ctx", hex(i))
    print(b" | ".join(toks).decode('latin1'))
EOF
exe bytes 51083264
TYPE_ANG_LIMIT at ['0x2552848']
=== ctx 0x2552848
city | maxLength | maxAngImpulse | maxLinImpulse | pinionRadiusOrScrewPitch | leverageOnBodyB |
ropeLength | fixedPivotBinWorld | fixedPivotAinWorld | copyToPivotBfromPivotA | targetPosition |
previousTargetPositionOffset | maxFrictionForce | frictionAxis | ultimateStrengthOffDiag |
ultimateStrengthDiag | yieldStrengthOffDiag | yieldStrengthDiag | SolvingMethod | CallbackRequest |
AtomType | METHOD_OLD | METHOD_STABILIZED | CALLBACK_REQUEST_CONTACT_POINT_CALLBACK |
CALLBACK_REQUEST_SETUP_CALLBACK | CALLBACK_REQUEST_SETUP_PPU_ONLY | CALLBACK_REQUEST_NEW_CONTACT_POINT |
CALLBACK_REQUEST_NONE | LAST_MODIFIER_TYPE | TYPE_MODIFIER_CENTER_OF_MASS_CHANGER |
TYPE_MODIFIER_IGNORE_CONSTRAINT | TYPE_MODIFIER_MOVING_SURFACE | TYPE_MODIFIER_VISCOUS_SURFACE |
TYPE_MODIFIER_MASS_CHANGER | TYPE_MODIFIER_SOFT_CONTACT | FIRST_MODIFIER_TYPE | TYPE_CONTACT |
TYPE_WHEEL_FRICTION | TYPE_OVERWRITE_PIVOT | TYPE_DEFORMABLE_3D_ANG | TYPE_DEFORMABLE_3D_LIN |
TYPE_3D_ANG | TYPE_SETUP_STABILIZATION | TYPE_COG_WHEEL | TYPE_RACK_AND_PINION | TYPE_PULLEY |
TYPE_RAGDOLL_MOTOR | TYPE_ANG_MOTOR | TYPE_ANG_FRICTION | TYPE_CONE_LIMIT | TYPE_TWIST_LIMIT |
TYPE_ANG_LIMIT | TYPE_ANG | TYPE_2D_ANG | TYPE_LIN_MOTOR | TYPE_LIN_FRICTION | TYPE_LIN_LIMIT |
TYPE_LIN_SOFT | TYPE_LIN | TYPE_STIFF_SPRING | TYPE_BALL_SOCKET | TYPE_SET_LOCAL_ROTATIONS |
TYPE_SET_LOCAL_TRANSLATIONS | TYPE_SET_LOCAL_TRANSFORMS | TYPE_BRIDGE | MeasurementMode |
ZERO_WHEN_VECTORS_PERPENDICULAR | ZERO_WHEN_VECTORS_ALIGNED | ...
```

Read bottom-up (the run is descending) and anchored at `TYPE_BRIDGE = 1`, that gives 14 =
`TYPE_ANG_LIMIT`, 15 = `TYPE_TWIST_LIMIT`, 16 = `TYPE_CONE_LIMIT`, 17 = `TYPE_ANG_FRICTION`, 18 =
`TYPE_ANG_MOTOR`, 19 = `TYPE_RAGDOLL_MOTOR`, 23 = `TYPE_SETUP_STABILIZATION`, 2 =
`TYPE_SET_LOCAL_TRANSFORMS`, 5 = `TYPE_BALL_SOCKET`, 12 = `TYPE_2D_ANG`. Values 1..20 equal the
header's order (oracle `exe_enum_matches_header_1_20`).

**The trap this avoids:** the 2009 header has 23 = a soft-contact *modifier*; JC3 has 23 =
`TYPE_SETUP_STABILIZATION`. Naming the atoms from the old header alone would have mislabelled the
16-byte atom at `+0x0B0` of both classes. Above value 20 the exe is the only authority.

### 2.2 The fleet, re-read (atoms, flags, tau)

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python - <<'EOF'
import sys, glob, struct, json, math
sys.path.insert(0,'Tools/scripts')
import jc3hkx
HINGE="hkpLimitedHingeConstraintData"; RAG="hkpRagdollConstraintData"
files=sorted(glob.glob(r"E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc", recursive=True))
rows=[]; classes={}
for f in files:
    b=open(f,'rb').read(); pf=jc3hkx.Packfile(b)
    for o in pf.objects:
        classes[o.cls]=classes.get(o.cls,0)+1
        if o.cls not in (HINGE,RAG): continue
        base=pf.base; at=base+o.offset
        g=lambda off: struct.unpack_from("<f",b,at+off)[0]
        u=lambda off: struct.unpack_from("<H",b,at+off)[0]
        ub=lambda off: b[at+off]
        if o.cls==HINGE:
            rows.append(dict(f=f.split('/')[-1],off=o.offset,ext=pf.extents[o.offset],
              t=[u(0x20),u(0xB0),u(0xC0),u(0xE8),u(0xF8),u(0x108),u(0x118)],
              en=ub(0xFA),ax=ub(0xFB),mn=g(0xFC),mx=g(0x100),tau=g(0x104),
              free=ub(0x10A), ball_t=u(0x118)))
print("classes:", json.dumps(classes, indent=1)[:1500])
print("hinges",len(rows))
from collections import Counter
print("types", Counter(tuple(r['t']) for r in rows))
print("en", Counter(r['en'] for r in rows), "axis", Counter(r['ax'] for r in rows), "free", Counter(r['free'] for r in rows))
print("tau", Counter(round(r['tau'],4) for r in rows))
print("ext", Counter(r['ext'] for r in rows))
bad=[r for r in rows if not (r['mn']<=r['mx']+1e-9)]
print("min>max", len(bad))
EOF
classes: {
 "hkRootLevelContainer": 51,
 "hknpPhysicsSceneData": 50,
 "hknpPhysicsSystemData": 50,
 "hknpConvexPolytopeShape": 3716,
 "hkRefCountedProperties": 5969,
 "hknpShapeMassProperties": 4100,
 "CPfxPartIndexProperty": 5477,
 "hknpStaticCompoundShape": 775,
 "hknpStaticCompoundShapeData": 775,
 "hknpExternMeshShape": 1063,
 "hkGeometry": 2126,
 "hknpExternMeshShapeData": 1063,
 "hknpDynamicCompoundShape": 818,
 "hknpDynamicCompoundShapeData": 818,
 "hkpLimitedHingeConstraintData": 419,
 "hkpRagdollConstraintData": 71,
 "hknpConvexShape": 948,
 "hkpHingeConstraintData": 4,
 "hknpTriangleShape": 1
}
hinges 419
types Counter({(2, 23, 18, 17, 14, 12, 5): 419})
en Counter({1: 419}) axis Counter({0: 419}) free Counter({0: 419})
tau Counter({1.0: 419})
ext Counter({304: 419})
min>max 0
```

`m_isEnabled` is 1 in 419/419 and `m_limitAxis` is 0 in 419/419 — both inside the header's domain
(0/1 and 0..2). `m_angularLimitsTauFactor` is exactly 1.0 in 419/419, which is the header's
declared default, and it is the only one of the three floats that could be 1.0 everywhere.

### 2.3 The plain hinges and the rest pose

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python - <<'EOF'
... (corrected probe: o.cls == "hkpHingeConstraintData" collected separately) ...
print("plain hkpHingeConstraintData:", len(plain))
for f,off,ext,codes in plain[:4]:
    print(" ", f, off, ext, {hex(k):v for k,v in list(codes.items())[:14]})
...
print("hinges %d | rest angle in [min,max]: +conv %d, -conv %d" % (tot, ia, ib))
EOF
plain hkpHingeConstraintData: 4
  JC3grab\hkx\all\mediumoldfishing.physicsc 0x817b0 224 {'0x20': 2, '0x78': 2, '0xb0': 23, '0xc0': 12, '0xd0': 5}
  JC3grab\hkx\all\mediumoldfishing.physicsc 0x81890 224 {'0x20': 2, '0x78': 2, '0xb0': 23, '0xc0': 12, '0xd0': 5}
  JC3grab\hkx\all\mediumoldfishing.physicsc 0x81970 224 {'0x20': 2, '0x78': 2, '0xb0': 23, '0xc0': 12, '0xd0': 5}
  JC3grab\hkx\all\transport.physicsc 0x25910 224 {'0x20': 2, '0x78': 2, '0xb0': 23, '0xc0': 12, '0xd0': 5}
hinges 419 | rest angle in [min,max]: +conv 419, -conv 419
```

The plain hinge's atom list is `SET_LOCAL_TRANSFORMS, SET_LOCAL_TRANSFORMS, SETUP_STABILIZATION,
2D_ANG, BALL_SOCKET` — no `ANG_MOTOR` (18), no `ANG_FRICTION` (17), **no `ANG_LIMIT` (14)** — and
it is 224 B against the limited hinge's 304 B: 80 B = motor 40 + friction 16 + limit 16 + 8. So the
atom at `+0x0F8` exists only where a limit exists. (An earlier probe of mine compared a class name
against the literal string `"HINGE"` and collected all 423 objects into the plain list; that output
was discarded and the corrected probe above is the one used.)

### 2.4 The donor: constraint index → named part → range

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python - <<'EOF'
import sys, os
sys.path.insert(0,'Tools/scripts')
import jc3adf, jc3_door_angles as DA
d=r"Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
parts=jc3adf.parts(jc3adf.Adf(open(os.path.join(d,"sportsmuscle_vehicle_parts.vmodc"),'rb').read()))
blob=open(os.path.join(d,"sportsmuscle.physicsc"),'rb').read()
dec=DA.decode_physics(blob)
byc={}
for p in parts:
    byc.setdefault(p.get("constraint_index"), []).append(p)
print("i  data      class                          body  min..max  part (behaviour)")
for r in dec["records"]:
    ps=byc.get(r["index"],[])
    nm=", ".join("%s [%s] body %s"%(p["name"],p["behavior"],p["world_collision_body_id"]) for p in ps)
    lim="%7.2f..%7.2f"%(r["min_deg"],r["max_deg"]) if "min_deg" in r else "   -        "
    print("%2d %-9s %-30s %4d %s  %s"%(r["index"], hex(r["data"]) if r["data"] else "-", r["class"], r["body"], lim, nm))
EOF
i  data      class                          body  min..max  part (behaviour)
 0 0x4da80   hkpLimitedHingeConstraintData     1    0.00..  80.00  sportsmuscle_door_f_l [FrontLeftDoor] body 1
 1 0x4dbb0   hkpLimitedHingeConstraintData     3  -35.00..   0.00  sportsmuscle_l_mirror [None] body 3
 2 0x4dce0   hkpLimitedHingeConstraintData     4    0.00..  80.00  sportsmuscle_door_f_r [FrontRightDoor] body 4
 3 0x4de10   hkpLimitedHingeConstraintData     6  -35.00..   0.00  sportsmuscle_r_mirror [None] body 6
 4 0x4df40   hkpRagdollConstraintData          7    -          sportsmuscle_engine [None] body 7
 5 0x4e0e0   hkpLimitedHingeConstraintData    16  -15.00..   0.00  sportsmuscle_front_bumper [None] body 16
 6 0x4e210   hkpRagdollConstraintData         18    -          sportsmuscle_grill [None] body 18
 7 0x4e3b0   hkpLimitedHingeConstraintData    19    0.00..  30.00  sportsmuscle_hood [None] body 19
 8 0x4e4e0   hkpLimitedHingeConstraintData    20    0.00..  70.00  sportsmuscle_hood_signature [Hood] body 20
 9 0x4e610   hkpLimitedHingeConstraintData    26  -15.00..   0.00  sportsmuscle_rear_bumper [None] body 26
10 0x4e740   hkpLimitedHingeConstraintData    35    0.00..  90.00  sportsmuscle_trunk [None] body 35
```

### 2.5 The review script

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/jc3_physics_limits2.py --write
wrote Research/JC3Grab/PHYSICS_LIMITS_REVIEW.md and Research/JC3Grab/PHYSICS_LIMITS_REVIEW.json
hinges 419 / plain 4 / ragdolls 71 / panels 9 / files 51
oracles 18/18

$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/jc3_physics_limits2.py --check
OK hinges 419 / plain 4 / ragdolls 71 / panels 9 / files 51; md+json identical
oracles: {"ang_limit_is_14": true, "donor_map_is_complete": true, "every_fleet_atom_code_has_a_name": true, "exe_enum_matches_header_1_20": true, "hinge_is_enabled_is_bool": true, "hinge_limit_atom_16B": true, "hinge_limit_axis_valid": true, "hinge_min_cannot_be_tau": true, "hinge_min_le_max": true, "hinge_tau_in_unit_interval": true, "limit_atom_sizes_match_header": true, "no_unexpected_size_mismatch": true, "panel_sign_and_units": true, "plain_hinge_has_no_limit_atom": true, "plain_hinge_is_80B_shorter": true, "ragdoll_pairs_ordered": true, "ragdoll_tau_in_unit_interval": true, "ragdoll_twist_then_two_cones": true}

$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/jc3_physics_limits.py --check
OK hinges 419 / ragdolls 71 / files 51; md+json byte-identical
oracles: {"hinge_atom_codes_constant": true, "hinge_extent_uniform": true, "hinge_factor_is_one": true, "hinge_limits_on_grid": true, "hinge_limits_vary_per_car": true, "hinge_limits_within_pi": true, "hinge_min_le_max_all": true, "non_limit_not_claimed": true, "ragdoll_atom_codes_constant": true, "ragdoll_extent_uniform": true, "ragdoll_factor_constant": true, "ragdoll_pairs_ordered": true, "transform_w_slots_zero": true, "transforms_decode": true}
```

(The reviewed script still passes unchanged, so nothing in this review contradicts its numbers.)

### 2.6 Fleet door rows, by behaviour / axis / range

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python - <<'EOF'
import json, collections
doc=json.load(open("Research/JC3Grab/DOOR_ANGLES.json",encoding="utf-8"))
row=[d for c in doc["cars"] for d in c["doors"]]
h=[d for d in row if isinstance(d.get("hinge"),dict)]
def key(d):
    hg=d["hinge"]; ax=tuple(round(v,3) for v in hg.get("axis") or [])
    return (d["behaviour"], ax, round(hg["min_deg"],1), round(hg["max_deg"],1))
tab=collections.Counter(key(d) for d in h)
for k,v in sorted(tab.items(), key=lambda kv:(-kv[1],kv[0]))[:30]: print(v,k)
print("distinct", len(tab))
EOF
53 ('FrontLeftDoor', (0.0, -1.0, 0.0), 0.0, 80.0)
51 ('FrontRightDoor', (0.0, 1.0, 0.0), 0.0, 80.0)
24 ('RearRightDoor', (0.0, 1.0, 0.0), 0.0, 80.0)
23 ('Hood', (1.0, 0.0, 0.0), 0.0, 30.0)
17 ('RearLeftDoor', (0.0, -1.0, 0.0), 0.0, 80.0)
15 ('Trunk', (-1.0, 0.0, 0.0), 0.0, 80.0)
8 ('MissileHatch', (0.0, 0.0, -1.0), 0.0, 150.0)
8 ('MissileHatch', (0.0, 0.0, 1.0), 0.0, 150.0)
5 ('Hood', (1.0, 0.0, 0.0), 0.0, 80.0)
4 ('CargoBayDoor', (1.0, 0.0, 0.0), 0.0, 15.0)
4 ('CargoBayDoor', (1.0, 0.0, 0.0), 0.0, 43.0)
4 ('FrontLeftDoor', (0.0, -1.0, 0.0), 0.0, 90.0)
4 ('FrontLeftDoor', (1.0, 0.0, 0.0), 0.0, 130.0)
4 ('RearRightDoor', (0.0, -1.0, 0.0), 0.0, 80.0)
3 ('CenterLeftDoor', (0.0, -1.0, 0.0), -0.5, 0.5)
3 ('CenterRightDoor', (0.0, -1.0, 0.0), -0.5, 0.5)
3 ('FrontLeftDoor', (0.0, -0.359, -0.933), 0.0, 80.0)
3 ('FrontLeftDoor', (0.0, 0.0, -1.0), 0.0, 80.0)
3 ('FrontLeftDoor', (0.087, -0.996, 0.0), 0.0, 80.0)
3 ('FrontRightDoor', (0.0, 0.353, 0.936), 0.0, 80.0)
3 ('FrontRightDoor', (0.087, 0.996, 0.0), 0.0, 80.0)
3 ('RearDoor', (0.0, -1.0, 0.0), 0.0, 80.0)
3 ('RearDoor', (0.0, 1.0, 0.0), 0.0, 80.0)
3 ('RearLeftDoor', (0.0, -1.0, 0.0), 0.0, 90.0)
3 ('Trunk', (0.0, 1.0, 0.0), 0.0, 75.0)
2 ('CargoBayDoor', (-1.0, 0.0, 0.0), 0.0, 90.0)
2 ('CenterLeftDoor', (0.0, -1.0, 0.0), 0.0, 100.0)
2 ('CenterLeftDoor', (0.994, 0.108, 0.0), 0.0, 90.0)
2 ('CenterRightDoor', (0.0, 1.0, 0.0), 0.0, 80.0)
2 ('CenterRightDoor', (0.0, 1.0, 0.0), 0.0, 100.0)
distinct 71
```

## 3. What the attack found

**Confirmed, three ways, each of which could have failed:**

| attack | result |
|---|---|
| Is code 14 really the *limit* atom in Havok 2014.1? | The exe's own enum says `TYPE_ANG_LIMIT = 14`, and the hinge's whole atom list (`SET_LOCAL_TRANSFORMS, SETUP_STABILIZATION, ANG_MOTOR, ANG_FRICTION, ANG_LIMIT, 2D_ANG, BALL_SOCKET`) is the canonical limited-hinge set. |
| Are `+0x0FC`/`+0x100` inside the limit atom, or in the motor? | Inside: motor `+0x0C0..+0x0E7` (40 B), friction `+0x0E8..+0x0F7` (16 B), limit `+0x0F8..+0x107` (16 B). The header's field order puts min at atom+4 = `+0x0FC`, max at +8 = `+0x100`, tau at +12 = `+0x104`. The 419/419 `isEnabled = 1`, `limitAxis = 0` and `tau = 1.0` all land in the header's domains. |
| Could `+0x0FC` be the tau factor with min/max shifted? | No: 192 hinges have a negative min, 181 a max above 1 rad, and the header clamps tau to [0,1]. |
| Is it a limit at all, or an authored cosmetic value? | The 4 plain hinges have **no** type-14 atom and are 80 B shorter; the atom's size (16 B) matches the header's struct exactly. |
| Units? | Header: radians. 419/419 inside ±pi, 405/419 on a 0.5° grid, 64 distinct pairs. |
| Sign and magnitude? | Rotating the donor's named panels: front-left door +80° goes 0.84 m **outboard** (x −0.837 → −1.677) and −80° goes 0.54 m **into the chassis**; front-right door mirrors (axis `(0,+1,0)`, same 0..80, same 0.84 m outboard); hood (behaviour `Hood`) rises 0.84 m at 70°; trunk rises 1.06 m at 90°; inner hood 0.42 m at 30°. 5/5 panels with a rule pass. Reading the floats as degrees (80 rad = 13 turns) or flipping the sign would drive every panel through the car. |

**Two divergences from the 2009 header, both named and neither touching the limits:** the
`ANG_MOTOR` atom is 40 B here vs 32 B in 2009, and `TYPE_SETUP_STABILIZATION` (23) does not exist
in 2009. A `no_unexpected_size_mismatch` oracle fails if any *other* atom disagrees.

**Ragdoll half of the UNKNOWN list closed:** `+0x130` = `TYPE_TWIST_LIMIT`, `+0x150` and `+0x170` =
`TYPE_CONE_LIMIT` (twice — a 2014 addition). Their min/max/tau offsets (+8/+12/+16) and 32-byte
sizes match the header's `hkpTwistLimitConstraintAtom` / `hkpConeLimitConstraintAtom` exactly, and
tau is 0.8 (inside [0,1]) in 71/71.

**The one new problem (semantic, not structural):** across the fleet, 16 of the 209 rows whose hinge
axis lies in the car's Y pair the axis with the *opposite* side to their pivot. Four assets are
involved — `modernbus_door_r_r_2` (0..80), `heavytroop_door_r_r` (−1..1), `heavyassault_door_b_r`
(−90..0), `cargotransport_door_int_r` (0..90). Under the donor's convention those panels would open
inward; either they do (interior doors on aircraft/bus) or their part frames are mirrored. This does
not change any decoded value — it is a reading question about those four assets.

## 4. UNKNOWNs

1. **What the extra 8 B in the 40-byte `ANG_MOTOR` are.** No 2014.1 header is available; the 2009
   struct is 32 B. Does not affect the limit atoms.
2. **`TYPE_SETUP_STABILIZATION`'s fields.** 16 B, constant per class, no 2009 struct to pin it.
3. **Which of the two cone atoms bounds which ragdoll axis.** Nothing in the bytes orders them.
4. **The −100 rad min sentinel's exact semantics.** It reads exactly −100.0 in every ragdoll; "no
   lower limit" is derived, not decoded.
5. **The four assets with the opposite axis/pivot pairing** (section 3). Needs each part's centroid
   in the hinge's space; this pass decoded that only for the donor.
6. **Which angular axis of the frame the hinge spins about.** `m_limitAxis` is 0 in all 419 and
   `m_freeRotationAxis` is 0 in all 419, so the pair bounds frame axis 0 by the header's definition;
   the *world* axis differs per car (those are the `axis` values used above).

## 5. Reproduce

```
python Tools/scripts/jc3_physics_limits2.py --write
python Tools/scripts/jc3_physics_limits2.py --check
```

Inputs (read-only): `D:/Games/Just Cause 3/JustCause3.exe`,
`E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc` (51 files), the donor
`Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc`
and its `sportsmuscle_vehicle_parts.vmodc`, `Research/JC3Grab/DOOR_ANGLES.json`. No game process was
run, nothing was written outside `Research/JC3Grab/PHYSICS_LIMITS_REVIEW.*`, the new script, and
this report.
