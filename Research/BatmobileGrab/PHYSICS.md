# Batmobile collision bodies (PHY-1)

Decoded by `Tools/scripts/grab_physics.py` from the four vehicle packages. Per-bone collision boxes: `RB_BodySetup` -> `AggGeom`, extents and local centre in centimetres (1 uu = 1 cm).

**4 vehicles, 32 bodies each, 128 records total.** All four vehicles carry byte-identical collision layouts.

Physics assets: `Batmobile_V3_Destroyed_Physics`, `PhysicsAssetInstance`

## Coverage by category

| category | bodies | bones |
|---|---|---|
| cockpit | 1 | `CockPit_Mesh` |
| destruction debris | 18 | `Object001`, `Object003_frag_007`, `Object003_frag_008`, `Object003_frag_017`, `Object003_frag_023`, `Object003_frag_024`, `Object003_frag_025`, `Object004_frag_002`, `Object004_frag_003`, `Object004_frag_006`, `Object004_frag_007`, `Object007`, `Object`, `Object011`, `Object013`, `Object009`, `Object017`, `Object015` |
| door | 2 | `Rear_Door_BOTTOM`, `Rear_Door_MIDDLE` |
| jet fin | 1 | `Jet_Fins001` |
| root placeholder | 1 | `Root` |
| turret | 1 | `Main_Turret_00` |
| wheel/suspension | 8 | `SUSP2_Wheel_Front_Left_Mesh`, `SUSP2_Wheel_Front_Right_Mesh`, `Wheel_Front_Left_Vis_Mesh`, `Wheel_Back_Left_Vis_Mesh`, `Wheel_Front_Right_Vis_Mesh`, `SUSP1_Wheel_Rear_Right_Mesh`, `Wheel_Rear_Right_Vis_Mesh`, `SUSP1_Wheel_Rear_Left_Mesh` |

## Bodies

| # | bone | collision | extents X×Y×Z (cm) | centre (cm) | category |
|---|---|---|---|---|---|
| 0 | `Root` | 1 box | 30.3×30.3×30.3 | (0, 0, 0) | root placeholder |
| 1 | `SUSP2_Wheel_Front_Left_Mesh` | 1 box | 211.54×51.093×109.003 | (66.542, -1.608, 12.661) | wheel/suspension |
| 2 | `SUSP2_Wheel_Front_Right_Mesh` | 1 box | 157.805×60.058×110.255 | (64.419, 28.091, 15.607) | wheel/suspension |
| 3 | `Wheel_Front_Left_Vis_Mesh` | 1 box | 97.605×55.342×101.533 | (11.718, -3.285, -4.991) | wheel/suspension |
| 4 | `Wheel_Back_Left_Vis_Mesh` | 1 box | 98.989×60.573×108.901 | (2.755, 1.781, -9.909) | wheel/suspension |
| 5 | `Wheel_Front_Right_Vis_Mesh` | 1 box | 97.01×52.545×103.247 | (0.404, -1.591, 0.384) | wheel/suspension |
| 6 | `SUSP1_Wheel_Rear_Right_Mesh` | 1 box | 317.942×64.552×97.966 | (-121.915, 25.708, -17.364) | wheel/suspension |
| 7 | `Wheel_Rear_Right_Vis_Mesh` | 1 box | 106.61×64.812×106.033 | (0.059, -1.273, -2.678) | wheel/suspension |
| 8 | `SUSP1_Wheel_Rear_Left_Mesh` | 1 box | 316.155×63.418×109.881 | (-117.414, -17.569, -12.155) | wheel/suspension |
| 9 | `Object001` | 1 box | 40.267×51.068×50.379 | (-245.722, 13.217, 28.159) | destruction debris |
| 10 | `Main_Turret_00` | 1 box | 114.042×64.794×79.53 | (-37.52, 1.287, -17.554) | turret |
| 11 | `CockPit_Mesh` | 1 box | 143.357×80.663×64.851 | (-1.842, -4.191, 21.586) | cockpit |
| 12 | `Rear_Door_BOTTOM` | 1 box | 26.006×152.76×71.739 | (13.996, 1.491, 40.038) | door |
| 13 | `Rear_Door_MIDDLE` | 1 box | 59.101×197.09×37.58 | (6.467, -5.005, -14.893) | door |
| 14 | `Object003_frag_007` | 1 box | 89.649×63.024×65.765 | (2.173, -8.362, -2.622) | destruction debris |
| 15 | `Object003_frag_008` | 1 box | 144.953×111.448×117.238 | (1.704, -3.677, 4.732) | destruction debris |
| 16 | `Object003_frag_017` | 1 box | 89.817×75.49×26.539 | (-0.663, 0.766, 18.174) | destruction debris |
| 17 | `Object003_frag_023` | 1 box | 128.557×94.312×101.819 | (-1.445, -1.988, -0.414) | destruction debris |
| 18 | `Object003_frag_024` | 1 box | 117.992×92.692×102.093 | (-1.929, 0.823, -0.936) | destruction debris |
| 19 | `Object003_frag_025` | 1 box | 104.668×61.156×90.378 | (0.887, 12.673, 6.955) | destruction debris |
| 20 | `Object004_frag_002` | 1 box | 82.268×83.697×79.315 | (-19.944, 3.363, -0.3) | destruction debris |
| 21 | `Object004_frag_003` | 1 box | 61.13×41.854×64.069 | (1.1, 6.473, -3.332) | destruction debris |
| 22 | `Object004_frag_006` | 1 box | 91.434×73.846×64.868 | (6.79, -2.994, -18.721) | destruction debris |
| 23 | `Object004_frag_007` | 1 box | 80.714×60.293×63.52 | (10.36, 10.925, -14.706) | destruction debris |
| 24 | `Jet_Fins001` | 1 box | 129.11×61.195×28.711 | (-0.388, 9.832, -1.784) | jet fin |
| 25 | `Object007` | 1 box | 138.533×73.341×28.961 | (-4.007, 3.85, -9.774) | destruction debris |
| 26 | `Object` | 1 box | 70.096×41.614×27.411 | (2.668, 38.829, 5.337) | destruction debris |
| 27 | `Object011` | 1 box | 142.069×97.628×44.313 | (-1.213, -33.476, 52.419) | destruction debris |
| 28 | `Object013` | 1 box | 130.594×118.598×54.127 | (-2.476, -4.679, 61.885) | destruction debris |
| 29 | `Object009` | 1 box | 166.12×141.823×62.936 | (-5.308, 1.818, 40.067) | destruction debris |
| 30 | `Object017` | 1 box | 77.622×73.176×23.906 | (-11.188, 5.85, 50.459) | destruction debris |
| 31 | `Object015` | 1 box | 78.331×65.638×42.043 | (24.174, -40.507, 45.973) | destruction debris |

## Largest collision volumes

| bone | volume (m³, box) |
|---|---|
| `SUSP1_Wheel_Rear_Left_Mesh` | 17.6248 |
| `SUSP1_Wheel_Rear_Right_Mesh` | 16.0851 |
| `Object003_frag_008` | 15.1516 |
| `Object009` | 11.8620 |
| `Object003_frag_023` | 9.8760 |
| `SUSP2_Wheel_Front_Left_Mesh` | 9.4250 |
| `Object003_frag_024` | 8.9327 |
| `SUSP2_Wheel_Front_Right_Mesh` | 8.3595 |

## What this means

- Every body is a **single axis-aligned-ish box** (box count 1, sphere count 0) with an identity rotation and a local centre, so the shapes are box hulls around each bone, not convex hulls.

- **There is no chassis body.** The 32 bones cover wheels/suspension, cockpit, doors, jet fins, the turret and the `Object*_frag_*` debris pieces — the main hull has no `RB_BodySetup`. Hull collision for the *driveable* car therefore does not come from this asset; it comes from the vehicle sim plus JC3's `sportsmuscle.physicsc` (MODLOG §65–70, §96–101), while this asset is what the game hands to the **destroyed** wreck.

- The extents are the per-bone envelopes the wreck's debris spawns from, so they also give a second, independent check on our own per-bone rig: a bone whose box is far larger than our geometry at that bone means our part is oversized there.

