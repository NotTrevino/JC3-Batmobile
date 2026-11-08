# Batmobile tyres — the three diameters (G1-18)

Measured from `Batmobile_V2.pskx`, **vertices owned by the wheel bones**, in metres, through
the ONE transform (`bat_assemble.to_jc3_rot`, then × `scale` 0.01 + `offset` from
`Working/TrueScale/stations.json`) — the same transform `bat_assemble.py` uses for the whole
car, so these numbers are directly comparable to `T_ROWS.jsonl` T-G1/T-G2 and to JC3's
`land_global.*_wheels.radius`.

Axes in that frame (MODLOG §70): **x = axle (lateral, left = −x), y = vertical, z =
longitudinal**; ground is y = 0.02.

## 1. Per wheel — tyre, rim, width

| corner | tyre faces (`*_Vis`) | Ø tread (y, vertical) | Ø (z, longitudinal) | Ø max radial about the hub | width (x) | station radius | tread bottom − ground |
|---|---|---|---|---|---|---|---|
| f_l | 6,700 | **1.3652** | 1.3672 | 1.3711 | 0.7314 | 0.6829 | +0.0021 |
| f_r | 6,700 | **1.3657** | 1.3674 | 1.3714 | 0.7325 | 0.6826 | +0.0018 |
| r_l | 7,564 | **1.3654** | 1.3673 | 1.3712 | 0.7318 | 0.6826 | +0.0000 |
| r_r | 7,564 | **1.3652** | 1.3673 | 1.3711 | 0.7315 | 0.6827 | +0.0001 |

All four tyres are the same mould to **0.5 mm**: Ø1.365 tread-to-tread, Ø1.371 with the
shoulder, 0.732 wide. The tread sits on the ground (rears 0.0000, fronts +2 mm), so the
station radius and the mesh agree to ≤2 mm.

**Rim and sidewall aperture** (front-left):

| what | where it is read | Ø |
|---|---|---|
| rim face / hubcap (`Wheel_Frnt_Left_Fan`, 32 faces) | the disc closing the wheel | **1.0254** |
| tyre bead aperture (inner end face, r 0.567–0.680) | where the sidewall meets the rim | 1.135 – 1.360 |
| tyre sidewall ring at mid-width (x −1.00…−0.94) | sidewall outer edge | 1.322 – 1.371 |

The rim barrel itself is not separately bone-owned: `*_Vis` owns the whole tyre and
`*_Disc` owns everything inboard of it, so 1.0254 (the `Fan`) is the measurable rim figure
and 1.135 the aperture it sits inside.

### The three bones, one wheel (naming gotcha: `Front` vs `Frnt`)

| bone | what it is | front-left extent (m) |
|---|---|---|
| `Wheel_Front_Left_Vis` | the tyre | x 0.731 · y 1.365 · z 1.367 · Ø1.371 max radial |
| `Wheel_Frnt_Left_Disc` | the inner wheel structure (inboard of the tyre: hub/strut/suspension) | x 1.026 (−1.551…−0.525, i.e. 0.317 m inboard of the tyre's inner face at −0.842) · **y 1.427** (0.070…1.497) · z 1.270 · Ø1.596 max radial |
| `Wheel_Frnt_Left_Fan` | the hubcap disc | Ø1.025 |

The `Disc` bone is not a bigger tyre: 338 of its 11,543 front-left vertices lie beyond the
tyre's radius, all at x −1.370…−1.046 and z −2.798…−2.328 — a vertical structure inside the
wheel envelope that stops 4.8 cm above the ground and reaches 11 cm above the tyre crown.
Front wheels use `Front` in the `*_Vis` name and `Frnt` in `*_Disc`/`*_Fan`; the rears use
`Rear` throughout.

## 2. The three numbers

| number | what it actually is | source |
|---|---|---|
| **1.366** | **tread-to-tread through the hub, and 2 × the physics radius** — these are the same number by design | this file: tyre Ø1.3652–1.3657 vertical = 2 × `stations.json` `radius` 0.6826–0.6829 = T-G2's `land_global.*_wheels.radius` **0.68275 / 0.68265**, which T-G6 keeps as the JC3 contact radius. T-G2's own photo fit: front Ø1.366, rear 1.369 |
| **1.40** | the **lore reference** — neither mesh nor physics | 4 ft 7 in = 1.397 m wiki estimate, user-verified against footage with Batman at 188 cm (MODLOG §70) |
| **1.42** | **unsourced** — the `bat_assemble.py` docstring figure | written in the initial commit (`7a0a07d`); `git log -S "1.42 m"` finds no other commit, and no file in the repo measures 1.42 (no 0.71 radius, no such value in any TrueScale or T doc) |

### The sidewall question D-1 asked

D-1: keep the PSKX true scale "unless G1-18 shows the 1.366 excludes the sidewall bulge".
It does exclude the bulge, and the bulge is **5.5 mm, not 34 mm**:

- tread band, vertical (where the tyre touches): 1.3652 – 1.3657
- longitudinal: 1.3672 – 1.3674
- max radial about the hub (the shoulder): **1.3711 – 1.3714**

Ø including the shoulder = **1.371**, which is still 2.0% short of 1.40 (reaching 1.40 needs
a 1.025× scale-up of the whole car, not a bulge correction). None of the three headline
numbers is "the bulge number" — that number is 1.371.

### What 1.42 was probably measuring

The only quantity in the wheel near 1.42 is the **`*_Disc` bone's vertical extent, 1.427 m**
— the inner wheel structure, which sits 4.8 cm above the ground and 11 cm above the tyre
crown, and whose radial envelope reaches Ø1.596. A bounding box taken over "the wheel"
(hub + tyre + Disc + Fan) rather than over the tyre reads Ø1.60 radial / 1.43 vertical, not
Ø1.42 of rubber. The docstring measured the assembly, not the tyre.

## 3. Physics chain — what the diameter is used for

| value | radius (m) | Ø (m) | source | used? |
|---|---|---|---|---|
| mesh / JC3 contact | 0.6829 · 0.6826 · 0.6826 · 0.6827 (f_l · f_r · r_l · r_r) | 1.365–1.366 | `stations.json` = T-G2 `land_global.*_wheels.radius` 0.68275 / 0.68265, mesh bounds verified against it | **yes** — T-G6 keeps it: the JC3 radius sets contact and ride height |
| BmAK `SVehicleWheel.WheelRadius` | 0.640 | 1.280 | `MECHANICS.md` | **no** — a contact-radius simplification inside a 1.366 m visual tyre (T-G6); not imported |
| lore wiki | 0.699 | 1.397 (≈1.40) | MODLOG §70 | reference only |

`front/rear_wheels.radius` therefore stays **0.68275 / 0.68265** and the wheel RBMs stay at
true scale.

## 4. Decision D-1 — resolved: keep the PSKX true scale

**No rescale of the car.** The measurement closes D-1's condition:

1. the tyre reads Ø1.366 tread-to-tread and Ø1.371 including the shoulder — the bulge is
   5.5 mm, far short of the 34 mm needed to reach 1.40;
2. 1.42 (the number that suggested a mismatch) has no source: it is an assembly-envelope
   figure from the initial commit's docstring, not a measurement of rubber;
3. T-G6 already keeps the mesh radius as the JC3 physics radius, so ride height, contact and
   track are unchanged; the whole car would move together through the one transform (R2) if
   it ever were rescaled.

DIM-2 ("tyre diameter matches the lore reference") is satisfied as **1.366 measured vs 1.40
reference, 2.4% apart, accepted**: the mesh is the physics source and the wiki number is an
estimate. Nothing in the repo is edited to make the tyre read 1.40.

## 5. How to re-measure

```python
import sys, json; import numpy as np
sys.path.insert(0, "Tools/scripts")
import psk2rbm as P, pskx_parts as PX, bat_assemble as BA
Pp, W, F, mats = P.read_pskx(PSKX)                    # Batmobile_V2.pskx
bones, Wt = PX.skeleton(PSKX)
fb = PX.face_bones(Pp, W, F, Wt, len(bones))          # face -> bone
st = json.load(open("Working/TrueScale/stations.json", encoding="utf-8"))
Vw = BA.to_jc3_rot(Pp[W["p"]]) * st["scale"] + np.array(st["offset"])   # the ONE transform
pts = Vw[np.unique(F["w"].astype(np.int64)[fb == names.index("Wheel_Front_Left_Vis")])]
hub = np.array(st["corners"]["f_l"]["hub_true"])      # y = vertical, x = axle
print(pts[:, 1].max() - pts[:, 1].min())              # 1.3652 tread diameter
```
