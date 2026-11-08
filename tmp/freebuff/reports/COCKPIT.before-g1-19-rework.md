# Cockpit and driver placement (G1-19)

Everything here is measured from `Batmobile_V2.pskx` through the ONE transform
(`bat_assemble.to_jc3_rot` × 0.01 + `offset`, `Working/TrueScale/stations.json`), in the JC3
frame used everywhere else: **x = axle (left = −x), y = vertical (ground 0.020), z =
longitudinal, nose at −z**. Sources: `SLOTS.json` (material slots), `BONES.json` (bone
ownership), `SOCKETS_JC3.json` (`Driver`), `MATERIALS.md` (material graphs), plus
ray-casts against the mesh triangles (recipe in §7).

## 1. What is where — slot and bone

| part | material slot (faces, LOD0) | bone(s) | measured location, JC3 metres |
|---|---|---|---|
| **seat** — cushion, bolsters, rear lip | **11** `BatmobileV3_Cockpit_Seat` (13,014) | `Batmobile_Chassis` 12,470 · `CockPit_Mesh` 544 | cushion top **y 0.8407** under the Driver; cushion spans x ±0.30, z −1.45…−0.83 (0.62 m deep); rear lip at z −0.86; bolsters/tub walls beside the driver at x ±0.20…0.30, y 1.00…1.27, z −1.45…−1.20 (1,036 faces) |
| **cockpit tub, dash, cowl** | **10** `Batmobile_V3_Cockpit_MIC` (27,334) | `CockPit_Mesh` 14,136 · `Batmobile_Chassis` 13,198 | tub x ±0.404, y 0.676…2.029, z −2.232…−0.527; **dash front face** z −1.50…−1.60 at y 1.30…1.50 (3,310 + 3,862 centre-strip faces), its top lip band (z −1.56…−1.45, y 1.25…1.45) is 7,528 faces all on `Batmobile_Chassis` |
| **dashboard screens** | driver-facing panel of slot **10** (728 faces, 486 cm²) + centre panel of slot **12** `Cockpit_Master_Flip_Data` (100 faces, 404 cm²) | `Batmobile_Chassis` | panel: x ±0.328, y 1.317…1.560, z −1.865…−1.521. Centre screen: **x ±0.157 (0.314 m wide), y 1.416…1.561 (0.145 m tall), z −1.851…−1.662**, tilted 28° from vertical (plane normal (0, ±0.47, ±0.88)) |
| **canopy glass** — windscreen + side windows | **1** `Batmobile_V3_Glass_INST` (3,532; 1,716 on `CockPit_Mesh`) | `CockPit_Mesh` | windscreen plane: first hit **0.849 m** ahead of the mean eye (z −1.914 at y 1.655); side windows beside the driver at **x ±0.30, y ≈ 1.71** (z −1.38…−0.84) |
| **canopy roof over the driver** | **18** `Batmobile_Worn_NoRain` (524, `CockPit_Mesh`) = inner liner, **2** `Batmobile_V3_Mainbody_NEW_MIC` = outer skin | `CockPit_Mesh` (liner) · `Batmobile_Chassis` (skin) | liner **y 1.9662** above the Driver, skin y 1.9914 (2.5 cm above it) — **opaque: no glass on the centreline** |
| **yoke / steering control** | **— none —** | — | **absent**: the whole box \|x\| < 0.17, y 1.00…1.30, z −1.60…−1.10 contains **4 faces of any material** (see §6) |

Materials that carry the interior's look (`MATERIALS.md`, `Playable_Batmobile_SF`):

- `Batmobile_V3_Cockpit_MIC` → MIC of `Material_MASTERS.Batmobile_V3_Body_NoRain_MAT`,
  `Metalicity=0.90`, masks `Textures.Batmobile_V3_Int_Cockpit_M` + `_N`.
- `BatmobileV3_Cockpit_Seat` → MIC of `Engine.Batmobile_Hardleather_Master_MAT`,
  `EmissiveMultiply=15.0000` with `Emissive → Textures.Batmobile_V3_Int_Cockpit_E` — this is
  the material that makes the interior/screens glow; colour `Batmobile_V3_Int_Cockpit_D`,
  roughness `_S`, ramp `Maps.Batman_BM3_V2_Leather_Ramp`.
- `Batmobile_V3_Glass_INST` → MIC of `Batmobile_Glass` with `Glass_Opacity=1.2000`,
  `Glass_Reflectivity=0.8000`, `Glass_Roughness=1.1000`, `glass_smudges=0.2000`, textures
  `Batmobile_V3_Glass_S` (reflect/rough/normal mask), `_N`, `_A` (opacity) — tinted, alpha-mapped
  glass (APP-3).

## 2. The `Driver` socket

| field | value |
|---|---|
| `position_m` (JC3, through the one transform) | **(−0.0025, 0.8647, −1.0654)** — on the centreline, **0.845 m above the ground**, 1.065 m behind the car's midpoint toward the nose, 1.505 m behind the front axle (z −2.570) |
| bone / relative location | `Batmobile_Chassis`, (121.9658, 0.25, 84.2500) cm in the bone frame; rotation identity (`rotation_missing: true`) |
| `forward_jc3` | (0, 0, −1) — the driver faces the nose ✓ |
| seat surface under it (ray down onto slot 11) | **y 0.8407** → the socket sits **24 mm above the cushion**: it is the **hip / seat point**, not the feet and not the head |
| `DriverAnimOrigin` (second driver socket) | (−0.000, 0.022, 0.154) — a null location, i.e. the `Batmobile_Chassis` pivot at ground level: the origin for enter/exit animation, not for the seated pose |

Both are in the required-anchor list of `SOCKETS_JC3.json` (`required_anchors` 13/13 present).

## 3. Canopy clearance above the Driver

Ray straight up from the Driver, first surface per height (all materials tested):

| z (longitudinal) | inner roof surface y | material |
|---|---|---|
| −1.35 | 1.884 | `Batmobile_Worn_NoRain` (liner) |
| −1.25 | 1.901 | `Batmobile_V3_Cockpit_MIC` |
| −1.20 | 1.928 | liner |
| **−1.065 (the Driver)** | **1.966** | liner (skin 1.991) |
| −1.00 (head column) | **1.986** | liner (skin 2.016) |
| −0.95 | 2.001 | liner |
| −0.80 | 1.808 | seat (the headrest/rear structure) |

**Hip-to-liner clearance: 1.101 m.** The roof over the driver's head is opaque body — a vertical
ray at any \|x\| ≤ 0.15 hits `Batmobile_Worn_NoRain` then `Batmobile_V3_Mainbody_NEW_MIC`, never
`Batmobile_V3_Glass_INST`; glass appears only at \|x\| ≈ 0.30 (the side windows, y ≈ 1.71) and
ahead (the windscreen, z ≈ −1.91).

## 4. The eye point — derived, because no file has one

There is **no eye or camera socket in the mesh**: `SOCKETS_JC3.json` has 65 sockets and only two
driver anchors (`Driver`, `DriverAnimOrigin`); `MECHANICS.md` carries no camera/eye property
(only `RVehicleWeapon.OverrideCamera` and an AnimSet named `Camera`, neither of which is an eye
point). So the eye point below is **`Driver` hip + seated eye height** from standard adult
anthropometry, stated explicitly so the assumption travels with the number:

| build | seated eye height above the seat | **eye point** | sitting height (crown) | crown y | clearance to the liner at the head column (z −1.00, y 1.986) |
|---|---|---|---|---|---|
| adult mean, 1.76 m | 0.79 m | **(−0.003, 1.655, −1.065)** | 0.91 m | 1.775 | **0.211 m** |
| 1.88 m (the project's scale reference, MODLOG §70) | 0.84 m | **(−0.003, 1.705, −1.065)** | 0.97 m | 1.835 | **0.151 m** |

Both builds clear the canopy with the seat upright: **headroom above the eyes 0.331 / 0.281 m,
above the crown 0.21 / 0.15 m** (ANI-9's "head under the canopy" is satisfied by 15–21 cm).

Sightlines from the mean eye (−0.003, 1.655, −1.065):

- level forward: hits `Batmobile_V3_Glass_INST` (windscreen) at **0.849 m**;
- to the centre screen (0, 1.489, −1.757): **0.711 m, 13.5° below the level line** — the dash lip
  at z −1.52 (y 1.31…1.40) does not occlude it (a level ray from the eye passes at y 1.545);
- the wider instrument panel (y 1.317…1.560) sits 14…21° below the level line;
- for the 1.88 m build the level line meets the cowl/windscreen base at 0.750 m.

## 5. APP-3 — what is visible through the glass

The interior is enclosed by: windscreen ahead (z ≈ −1.91), side windows at \|x\| ≈ 0.30 beside
the driver's head, and an **opaque roof** (liner `Batmobile_Worn_NoRain` + skin `Mainbody`)
directly overhead. So seat and screens are visible **through the windscreen and the side windows,
not from above**. The glass is tinted and alpha-mapped (`Glass_Opacity 1.2`, `_A` opacity map),
and the interior glow comes from the seat material's emissive map ×15.

## 6. Gaps — stated, not smoothed

1. **No yoke / steering control.** Every material was tested in \|x\| < 0.17, y 1.00…1.30,
   z −1.60…−1.10 (the volume a driver's hands occupy): **4 faces total** (24 faces at y 0.90…1.00
   on the cushion front, 4 at y 1.20…1.30); y 1.00…1.20 is empty. The nearest centreline surface
   is the dash face at z −1.50. The other 11 mesh exports in the packages are the Destroyed/Fire
   variants, the MK2 and Jokerfied skins and the Batwing carrier — none is an interior, so the
   yoke is not hiding in another mesh. Consequence for ANI-9: the seated pose has nothing to
   grip; a grip point, if one is wanted, must come from the JC3 side (G2-19).
2. **No eye point in any file** (§4) — the eye above is derived from anthropometry, not read.
3. **Screen content is not in the material.** `Cockpit_Master_Flip_Data` is a master `Material`
   with no parent and *no connected* Diffuse/Specular/Power/Emissive expressions
   (`MATERIALS.md`: `DiffuseColor→—; SpecularColor→—; SpecularPower→—; EmissiveColor→—`) and no
   texture parameters — the 0.314 × 0.145 m panel geometry ships, the picture does not. What
   glows in the cockpit comes from `BatmobileV3_Cockpit_Seat`'s `Int_Cockpit_E` ×15, not from a
   screen texture.

## 7. How to re-measure

```python
Vw = to_jc3_rot(Pp[W["p"]]) * st["scale"] + np.array(st["offset"])   # the ONE transform
# seat: cast a ray down from (Driver.x, 1.40, Driver.z) onto the faces of material 11 -> y 0.8407
# roof: cast the same ray up; first hit is the liner (18), second the skin (2)
# empty box: faces whose three vertices all lie inside |x|<0.17, y 1.00..1.30, z -1.60..-1.10
```

Möller–Trumbore against the PSKX triangles, both windings (no back-face culling), materials
from `mats` (identical to `SLOTS.json`'s `slots[i].material`, verified), bone ownership from
`pskx_parts.face_bones`.
