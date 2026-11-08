# Keep-audit — suspension, mass and wheel force (T-M3, T-S4, T-S5, T-R2, T-R3)

Five rows marked **keep / "nothing to edit"**. Each is restated against what BmAK actually
serialises, then judged on the question that matters: **does the donor value reproduce BmAK
behaviour, or does it merely sit in the JC3 fleet range?**

**Built values (decoded from `bm-RC2` bytes at the `offset-in-file` of the module XMLs)**

| module | member | built |
|---|---|---:|
| `rigid_body` | `center_of_mass_bias` | **−0.300000** |
| `rigid_body` | `mass` | **6000.0** |
| `rigid_body` | `unit_inertia_yaw / pitch / roll` | **4.0 / 2.6 / 1.2** |
| `rigid_body` | `add_drivers_mass` / `use_calculated_inertia` | 0 / 0 |
| `suspension.front` and `.rear` | `antirollbar_strength` | **0.0 / 0.0** |
| `suspension.front` and `.rear` | `lateral_tire_force_offset` | **0.2 / 0.2** |
| `suspension.*` | `strength` / `length` / `compression` / `relaxation` / `hardpoint_offset_along_spring` | 45 / 0.7 / 3 / 5 / −0.1 |
| `land_global.front_wheels` | `use_shape_cast` / `arcade_drag_multiplier` / `arcade_friction_multiplier` | **0 / 0.1 / 3.0** |
| `land_global.rear_wheels` | same three | **0 / 0.1 / 3.0** |
| `land_global.*_wheels` | `mass` (front / rear) | **75 / 150** |

**Verdicts: 4 COMPROMISE (T-M3, T-S4, T-S5, T-R2), 1 LORE-EXACT (T-R3).**

Short answer to the operator's question: **one of the five reproduces a BmAK mechanism (T-R3,
raycast contact); the other four sit in the fleet range and have no BmAK number to be measured
against at all.**

---

## T-M3 — centre-of-mass bias −0.3 · **COMPROMISE (fleet range, no BmAK number)**

**BmAK number: there is none, and that is decoded, not assumed.** All four `RB_BodySetup` exports
serialize exactly `PreCachedPhysDataVersion`, a bool, an optional name/object ref, and `AggGeom`
(`INERTIA.md` §1). No `Mass`, `MassScale`, `Inertia` or `InertiaTensor` tag exists on any of them,
and a scale-free scan of the `AggGeom` payloads finds no triple shaped like a moment tensor
(`INERTIA.md` §2). The class defaults carry only **neutral multipliers**:
`BatmobileMassRatio` 1.0, `MassScale` 1.0, `InertiaTensorMultiplier` [1, 1, 1].

The nearest thing to a CoM statement in the whole grab is the **stay-upright setup**, and it is
empty: `Batmobile.RB_StayUprightSetup` is **2 bytes with 0 tags** in all four packages
(exports 5106 / 5157 / 3123 / 5196, `COLLISION_WHERE.md` §"Stay-upright and simulation",
`REMAINDER_SAMPLE_AUDIT.md`: `empty_stub x4`).

**Built number** — `center_of_mass_bias = −0.3`.

**Fleet comparison** — built −0.3; `center_of_mass_bias` domain across 233 vehicles −2 … 0.1,
median −0.2; 3–8 t median −0.3 (`VOCABULARY.md` l.1051, T-M3's own cell). The build is **exactly
the 3–8 t median** — i.e. it is a class pick, not a translation.

**Verdict: COMPROMISE.** Nothing on the BmAK side can confirm or refute it. Two derived
candidates point in *different* directions:

```
body bbox centre z      = (−3.420 + 3.605)/2 = +0.0925 m
wheelbase midpoint z    = (−2.570 + 2.4589)/2 = −0.05555 m
bbox centre is 0.148 m BEHIND the wheelbase midpoint   (a rearward bias, +0.148)
built bias is −0.3                                     (a forward bias, if −z is front)
```

Whether BmAK's car is nose- or tail-heavy is **UNKNOWN**: no mass bytes exist to weigh the
front. `−0.3` is a plausible nose-heavy setting for a front-engine car, and it is what QA-1's
handling was tuned on — but it is a fleet value, and the row says so.

**Nearest ways to shift the CoM in JC3 (what the wave asked for)**

| lever | member | note |
|---|---|---|
| direct offset | `rigid_body.center_of_mass_bias` | the only member that moves the CoM without changing anything else; built −0.3 |
| **hull geometry and hull mass blocks** | `physicsc` `hknpShapeMassProperties` — mass `f32` at `+0x28`, **CoM at payload group 1** (`+0x10..0x17`) | `INERTIA.md`: the JC3 CoM is *decoded* as the per-hull centroid (oracle error 0.0156 m median, 56/56 donor blocks). Moving or re-weighting a hull moves the CoM with no bias edit |
| wheel mass | `land_global.front/rear_wheels.mass` | built **75 front / 150 rear** — asymmetric, and it shifts the CoM by (75 × 5.0289)/6000 = **+0.063 m rearward** versus a symmetric pair (derived). A lever the ledger never names |
| inertia distribution | `rigid_body.unit_inertia_yaw/pitch/roll` 4.0/2.6/1.2 + `use_calculated_inertia 0` | distribution, not position |
| point mass | `rigid_body.add_drivers_mass` 0 | adds the driver's mass; position not decoded |

**One-line fix.** Keep −0.3 but state it as *fleet median, no BmAK evidence*; if a nose-heavy car
is actually wanted, derive the bias from the hull-mass CoM above rather than from the class.

---

## T-S4 — antiroll bar 0 · **COMPROMISE (fleet all-zero; BmAK uses a different mechanism)**

**BmAK number.** **No antiroll member exists** in the 41-class SDK dump: a scan of
`BMSDK_OFFSETS.json` for `AntiRoll|Anti-Roll|Sway` returns only camera sway fields
(`bSwayWithPelvis`, `bUseFullSway`, …) — nothing on `SVehicle`, `SVehicleWheel`,
`RVehicleSimCar` or `RVehicleSimBatmobile`.

BmAK does resist roll, but by a **native stay-upright constraint**:
`StayUprightConstraintSetup` → `RB_StayUprightSetup` (empty, 2 B) and `StayUprightConstraintInstance`
→ `RB_ConstraintInstance` (2 B). The four numbers that would describe it are declared by the class
and **not serialised in any package**: `StayUprightRollResistAngle`, `StayUprightPitchResistAngle`,
`StayUprightStiffness`, `StayUprightDamping` (`MODES.md` §"Not serialised in any shipped archetype
(4)"). `bStayUpright` itself is **false** in the class default (`CLASS_DEFAULTS.json`, mask 0x10).

**Built number** — `antirollbar_strength = 0.0` on both axles.

**Fleet comparison** — front domain 0 … 0.8, **median 0** (n = 167), donor 0; the 19-vehicle
sample is 0 … 0 (`VOCABULARY.md` l.1147/1161). The build is the fleet **median**, and every
sampled vehicle is 0 — the field is effectively unused by shipped cars.

**Verdict: COMPROMISE.** 0 does not reproduce BmAK's roll behaviour; it reproduces *"nobody
uses this field"*. BmAK's roll resistance is an engine-side uprighting constraint whose angle,
stiffness and damping are not in the files, so there is no number to match and no way to tell
whether the built car rolls like the lore car.

**One-line fix.** Leave 0; add to the row that BmAK's roll resistance lives in a **native
upright constraint with no serialised values** (`RB_StayUprightSetup`, 2 B, 0 tags) — the field is
not a translation of it, and any roll tuning must come from a measured take, not from BmAK.

---

## T-S5 — lateral tyre force offset 0.2 · **COMPROMISE (fleet median; BmAK asymmetry lost)**

**BmAK number.** No offset member. The closest decoded quantities are the wheel class's lateral
**slip gains**, and they are **asymmetric front-to-rear** (`COLLISION_WHERE.md` §Wheels, decoded
tag lists):

| wheel | serialised floats of interest |
|---|---|
| `Batmobile.WheelFL` / `WheelFR` | `HandbrakeLatSlipFactor` **1.5** (no `LatSlipFactor` tag → inherited, UNKNOWN) |
| `Batmobile.WheelRL` / `WheelRR` | `LatSlipFactor` **1.6**, `HandbrakeLatSlipFactor` **1.1** |

Plus `BattleModeLatSlipScale` **0.75** on `RVehicleSimBatmobile` (`MODES.md` l.89).

**Built number** — `lateral_tire_force_offset = 0.2` front **and** rear.

**Fleet comparison** — domain 0 … 1.5, **median 0.2**, IQR 0.1 … 0.3 (n = 167); donor **0.1 front /
0.05 rear** (`VOCABULARY.md` l.1151/1165). The build is the fleet median — but it is also a
**symmetric** pick, while the donor it replaced was asymmetric.

**Verdict: COMPROMISE.** Three separate problems:

1. 0.2 is the fleet median, not a BmAK value.
2. It is **symmetric**, where the donor (0.1 / 0.05) and BmAK's slip gains (rear 1.6 vs front
   inherited; handbrake 1.5 front vs 1.1 rear) are both **asymmetric** — the asymmetry is the one
   thing BmAK states about front-vs-rear lateral behaviour, and the build discards it.
3. The quantities are not the same thing: a slip *gain* scales the lateral force, an *offset*
   moves where it is applied. Matching one to the other is a gap, not a conversion.

**One-line fix.** Restore an asymmetric pair — 0.1 / 0.05 (the donor) or a ratio derived from the
1.6 : 1.0 slip factors — and record that the mapping from slip gain to force offset is UNKNOWN.

---

## T-R2 — arcade drag multiplier 0.1 / 0.1 · **COMPROMISE (modal fleet value; BmAK drag members exist but are undecoded)**

**BmAK number.** The ledger says "—", and `T-A2`'s chain grep (`RVehicle → RVehicleBatmobileBase →
RVehicleSimCar → RVehicleSimBatmobile → SVehicleSimCar`) found no drag member. **That grep misses
the simulation model.** The SDK dump carries three drag members on `RVehicleSimBatmobile`, the very
class of `Batmobile.SimulationModel` (export 5282, 2328 B):

| member | offset | type |
|---|---:|---|
| `RVehicleSimBatmobile.Drag` | **16** (`0x10`) | FloatProperty |
| `RVehicleSimBatmobile.DragNoLoad` | **20** (`0x14`) | FloatProperty |
| `RVehicleSimBatmobile.DriftDrag` | **712** (`0x2c8`) | float |

**No value for any of the three is decoded** in the grab: no `.md` carries a serialised `Drag`,
`DragNoLoad` or `DriftDrag` figure, and whether they are serialised on this model at all is
UNKNOWN. So the honest BmAK number is **"three candidate members exist, no values"**.

**Built number** — `arcade_drag_multiplier = 0.1` front and rear.

**Fleet comparison** — domain 0 … 0.5, **median 0.1**, donor 0.1 (n = 271; the 41-vehicle sample is
0 … 0.1). 0.1 is the modal value: every sampled vehicle carries it.

**Verdict: COMPROMISE.** The built value is the fleet mode, and the BmAK drag model (a full
`Drag` / `DragNoLoad` / `DriftDrag` triple) has no counterpart in JC3's single arcade multiplier.
The row is right that there is nothing to edit, and wrong to imply no BmAK member exists.

**One-line fix.** Change the cell from "—" to "`RVehicleSimBatmobile.Drag` 16 / `DragNoLoad` 20 /
`DriftDrag` 712 exist in the class dump, values not decoded" — and note that `T-A2`'s absence proof
stops at `SVehicleSimCar`, one class short of where the numbers would be.

---

## T-R3 — use_shape_cast 0 · **LORE-EXACT**

**BmAK number.** **No shape-cast member exists** anywhere in the 41-class dump (a scan for
`ShapeCast|Shape Cast` returns zero hits), and BmAK's wheel contact is **decoded as raycast**:
`Batmobile.SimulationModel` (export 5282, class `RVehicleSimBatmobile`, 2328 B) *"drives the four
raycast wheels"* (`COLLISION_WHERE.md` l.132, decoded), with radius 64 cm and 30 cm up / 40 cm down
travel on the fronts, 40 cm down on the rears. The wheels serialize **no `RB_BodyInstance` or wheel
shape** (same file, l.146).

**Built number** — `use_shape_cast = 0` on both axles, with `raycast_offset = 0` on both axles.

**Fleet comparison** — 0 on **all 26** 6 t+ and **all 35** 3–8 t land vehicles; only the
out-of-class 1.2 t cars set 1 (`T-R3`'s cell, `VOCABULARY.md` l.857/871).

**Verdict: LORE-EXACT.** This is the one row of the five where the donor value matches a **BmAK
mechanism**, not just the fleet: BmAK finds the road with four raycast wheels and has no
shape-cast member at all, and JC3 with `use_shape_cast 0` does the same. The value is decoded on
both sides of the same idea.

Residual caveat, not a defect: `raycast_offset 0` on all 167 vehicles means the ray starts at the
hub, so the contact radius is `radius` — which is the same finding as `keep-audit-dimensions-
wheels.md` T-G6.

---

## Closest system and the gap for the build (STAGES.md)

| gap | closest JC3 system | what the build must do |
|---|---|---|
| BmAK has **no mass/CoM/tensor** at all | `rigid_body.center_of_mass_bias` + `physicsc` hull mass blocks (CoM at `+0x10..0x17`, decoded) | treat the bias as a tuning knob; if a specific weight distribution is wanted, **move hulls / re-weight hull mass blocks**, not the bias |
| BmAK roll control is a **native upright constraint with no serialised numbers** | `suspension.*.antirollbar_strength` (all fleet cars 0) | roll behaviour must be tuned against a take; the field is unrelated to BmAK's mechanism |
| BmAK's front/rear lateral asymmetry (`LatSlipFactor` 1.6 rear, handbrake 1.5/1.1) | `suspension.front/rear.lateral_tire_force_offset` | keep an **asymmetric** pair; the gain→offset mapping is a build-time decision, not a translation |
| BmAK's `Drag` / `DragNoLoad` / `DriftDrag` triple | `…wheels.arcade_drag_multiplier` (single multiplier) | one multiplier cannot carry a load-dependent drag pair; decode the three values before claiming any drag translation |
| wheel contact model | `…wheels.use_shape_cast 0` + `raycast_offset` | **already right** — this is the closest exact match in the whole set |

**Stage placement.** None of the five blocks a stage. T-M3 and T-S4 are handling-feel knobs whose
BmAK counterpart is unreadable; they belong to the Q driving takes, not to a geometry or asset
stage.

---

## UNKNOWN

1. **BmAK's CoM position** — no mass and no tensor in any of the four body setups; only geometry.
2. **`StayUprightRollResistAngle` / `PitchResistAngle` / `Stiffness` / `Damping` values** — declared,
   absent from all four packages; the exe has 0 store sites for the damping (`chase-09.md` F-65/F-66).
3. **`RVehicleSimBatmobile.Drag` / `DragNoLoad` / `DriftDrag` values** — members named at 16 / 20 /
   712, no serialised value decoded anywhere in the grab.
4. **Whether `LatSlipFactor` is authored on the front wheels** — not serialised on `WheelFL/FR`, so
   the front value is a class default not in these bytes.
5. **What `center_of_mass_bias`'s unit and axis are** — the domain −2 … 0.1 and the built −0.3 fit a
   metres-forward convention, but no file states it.

---

## Checks run

| # | check | result |
|---|---|---|
| 1 | decode of `rigid_body`, `suspension`, `land_global`, `land_steering` from the built `.vmodc` | values in the header table; mass 6000, bias −0.3, antiroll 0/0, lateral offset 0.2/0.2, shape cast 0/0, drag 0.1/0.1 |
| 2 | `BMSDK_OFFSETS.json` scan for `ShapeCast|AntiRoll|Sway|Lateral|TireForce|Drag|CoM` | **0** shape-cast and **0** antiroll members; **3** drag members on `RVehicleSimBatmobile` (16 / 20 / 712); no CoM member |
| 3 | `INERTIA.md` §1-2 | no mass, no tensor on the four `RB_BodySetup` exports; class multipliers neutral |
| 4 | `COLLISION_WHERE.md` §Wheels + §Stay-upright | raycast wheels; `RB_StayUprightSetup` 2 B / 0 tags in 4 packages; slip factors 1.6 / 1.5 / 1.1 |
| 5 | `MODES.md` §StayUpright | 4 upright fields declared and **not serialised**; `bStayUpright` false |
| 6 | `VOCABULARY.md` fleet domains | bias −2…0.1 (med −0.2); antiroll 0…0.8 (med 0); lateral offset 0…1.5 (med 0.2, donor 0.1/0.05); drag 0…0.5 (med 0.1); shape cast 0…1 (med 0) |
| 7 | wheel-mass CoM arithmetic | 75 kg extra at the rear axle over 6000 kg = **+0.063 m** rearward |

No game process started; static reads and three read-only decodes.

## Reproduce

```bash
python - <<'EOF'
import xml.etree.ElementTree as ET, struct
MOD="Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/"
for mod,src in (('rigid_body','Working/Movement/live/'),('suspension','Working/Movement/live/'),('land_global','Working/Movement/live/')):
    b=open(MOD+'v0300_car_kensington_sportsmuscle_%s.vmodc'%mod,'rb').read()
    for m in ET.parse(src+'v0300_car_kensington_sportsmuscle_%s.xml'%mod).getroot().iter('member'):
        o=m.get('offset-in-file')
        if o and m.get('name') in ('center_of_mass_bias','antirollbar_strength','lateral_tire_force_offset','use_shape_cast','arcade_drag_multiplier','mass'):
            print(mod, m.get('name'), round(struct.unpack_from('<f',b,int(o,16))[0],4))
EOF
```
