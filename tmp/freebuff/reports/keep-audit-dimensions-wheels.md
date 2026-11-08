# Keep-audit — dimensions and wheels (T-G1, T-G2, T-G3, T-G4, T-G6)

Every row the ledger marks **keep** with the reason *"build carries the proposal"* is checked here
against the BmAK source, with the arithmetic. The built numbers below are **decoded from the
shipped bytes** of `bm-RC2`, not quoted from a ledger.

**Source of the built values.** `Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/
v0300_car_kensington_sportsmuscle/modules/default/batmobile/
v0300_car_kensington_sportsmuscle_land_global.vmodc` (1,600 B, sha256 `f9a1455f…`), read at the
`offset-in-file` of each member in `Working/Stance/land_global_check.xml`:

| member | offset | built value |
|---|---:|---:|
| `ground_clearance` | `0x0070` | **0.703700** |
| `front_wheels.radius` | `0x0074` | **0.682750** |
| `front_wheels.rim_radius` | `0x0078` | 0.539013 |
| `front_wheels.width` | `0x007c` | **0.731950** |
| `rear_wheels.radius` | `0x0094` | **0.682650** |
| `rear_wheels.rim_radius` | `0x0098` | 0.538934 |
| `rear_wheels.width` | `0x009c` | **0.731650** |
| `base_wheel_hardpoint_positions[0]` | — | (-1.2080, **0.7047**, -2.5700) |
| `[1]` | — | (+1.2080, **0.7047**, -2.5699) |
| `[2]` | — | (+1.2845, **0.7027**, +2.4589) |
| `[3]` | — | (-1.2845, **0.7027**, +2.4589) |

`python Tools/scripts/v_wheels.py --check` → **check ok** (it re-derives radius/width against
`TYRES.md` and asserts part→slot, spin axis and hardpoint signs).

**Verdicts: 4 LORE-EXACT (T-G1, T-G2, T-G3, T-G6), 1 COMPROMISE (T-G4).** Two of the four exact
rows carry a *ledger-text* defect that does not affect the build (T-G1's rear hub y, T-G3's
mirrored station widths).

---

## T-G1 — hardpoints, wheelbase, track · **LORE-EXACT**

**BmAK number** [decoded: `Research/BatmobileGrab/TYRES.md` §1, hubs re-measured from
`Batmobile_V2.pskx` in `Working/TrueScale/stations.json`]:

| corner | hub x | hub y | hub z |
|---|---:|---:|---:|
| f_l | −1.2080 | 0.7047 | −2.5700 |
| f_r | +1.2080 | 0.7047 | −2.5699 |
| r_l | −1.2845 | 0.7027 | +2.4589 |
| r_r | +1.2845 | 0.7027 | +2.4589 |

**Built number** — identical to the table above (`Builds/bm-RC2/verify/wheels.md` §4, Δ ≤ 0.10 mm).

**Arithmetic**

```
wheelbase   = |−2.5700| + 2.4589        = 5.0289 m   (ledger 5.029  → −0.1 mm)
track front = 2 × 1.2080                = 2.4160 m   (ledger 2.416  → 0.0 mm)
track rear  = 2 × 1.2845                = 2.5690 m   (ledger 2.569  → 0.0 mm)
Δ vs TYRES.md hubs, per component       ≤ 0.10 mm  (f_r z 2.5699 vs 2.5700)
```

**Evidence.** `TYRES.md` §1/§4, `stations.json` `corners.*.hardpoint`, built bytes at the
`position` offsets. Verified independently by `v_wheels.py --check` ("hardpoint 0 is TYRES.md's
f_l hub to 1 mm", "x reads left(−)/right(+), z reads front(−)/rear(+)").

**Ledger-text defect (not a build defect).** The `keep` cell writes a single `y 0.7047` for all
four hardpoints. The rear hubs are **0.7027** — 2 mm lower. The built bytes carry the correct
per-corner y.

---

## T-G2 — tyre diameter · **LORE-EXACT**

**BmAK number** [decoded: `TYRES.md` §1, tread Ø measured on the `Wheel_*_Vis` bones]:

```
f_l 1.3652   f_r 1.3657   r_l 1.3654   r_r 1.3652   (m, tread-to-tread, vertical)
front mean 1.36545   rear mean 1.36530
```

**Built number** — `front_wheels.radius 0.682750`, `rear_wheels.radius 0.682650`.

**Arithmetic**

```
front Ø = 2 × 0.682750 = 1.365500 m   vs front mean 1.36545  → +0.05 mm
rear  Ø = 2 × 0.682650 = 1.365300 m   vs rear  mean 1.36530  →  0.00 mm
worst per-corner error: f_r tread r 0.68285 vs built 0.68275  → −0.10 mm
```

**Evidence.** `TYRES.md` §§1–2 and §4's "mesh / JC3 contact" row; built bytes `0x0074`/`0x0094`.
The station radii that the build averages are themselves the mesh measurement
(2 × 0.6826–0.6829 = 1.3652–1.3658, ≤ 0.6 mm of the tread), so the chain is
**mesh → station → built member** with no free parameter.

**Ledger wording.** "tyre Ø 1.366 m" is a rounding of the four-corner range 1.3652–1.3657; the
built members are 1.3655/1.3653. Same number to the printed precision.

---

## T-G3 — tyre width · **LORE-EXACT**

**BmAK number** [decoded: `TYRES.md` §1, x-extent of the tyre bone]:

```
f_l 0.7314   f_r 0.7325   r_l 0.7318   r_r 0.7315
front mean 0.73195   rear mean 0.73165
```

**Built number** — `front_wheels.width 0.731950`, `rear_wheels.width 0.731650`.

**Arithmetic**

```
front 0.731950 vs mean(0.7314, 0.7325) = 0.73195  → 0.0 mm
rear  0.731650 vs mean(0.7318, 0.7315) = 0.73165  → 0.0 mm
worst per-corner error ≤ 0.55 mm (f_l 0.7314 vs 0.73195)
```

**Evidence.** `TYRES.md` §1, `stations.json` `corners.*.tyre_width`, built bytes `0x007c`/`0x009c`.

**Known defect in the source file, harmless here (R3).** `stations.json`'s `tyre_width` is
**mirrored L↔R** relative to the mesh (file f_l 0.7325 is the mesh's f_r 0.7325). The build
consumes only the **per-axle mean**, which is invariant under the mirror, so the built width is
exact even though the corner attribution in `stations.json` is wrong. Any future per-corner use
of `tyre_width` would need that attribution re-derived.

---

## T-G4 — ride height / ground clearance · **COMPROMISE**

**BmAK number.** BmAK has **no `ground_clearance` member** — there is nothing in
`BMSDK_OFFSETS.json`'s `SVehicle`/`RVehicleBatmobile` layouts by that name. The only two BmAK
quantities in this area are:

| quantity | value | class |
|---|---:|---|
| hub height (front) | 0.7047 m | decoded (mesh) |
| hub height (rear) | 0.7027 m | decoded (mesh) |
| **underbody clearance** (body bbox min y 0.091 − ground 0.02) | **0.071 m** | derived from the mesh bbox |

**Built number** — `ground_clearance = 0.703700`.

**Arithmetic**

```
0.703700 = mean(0.7047, 0.7027)   → 1 mm below the front hub, 1 mm above the rear hub
0.703700 vs BmAK's measurable underbody clearance 0.071  → 0.6327 m apart (9.9x)
```

**Evidence for the verdict.** The ledger itself labels the row `derived (hub y; §70 assumed
clearance = hub height)` and its own note says *"ASSUMPTION: it equals the vanilla hub height;
semantics unknown"* (`Tools/scripts/physics_stations.py` docstring). The independent audit
**REFUTED** that class: `Research/challenge/T1_TRANSLATION.md` **C09** — *"T-G4 ride height
`derived` … REFUTED as class (it is assumed)"* — and `MODLOG` §ledger-audit lists T-G4 among the
**7 GUESSED** rows (`ground_clearance 0.7037 (assumed)`).

So the built number is a *bridge*, not a measurement: it copies the hub height into a member
whose meaning is unverified, and BmAK's actual clearance (0.071 m) differs from it by 0.63 m.

**One-line fix.** Run one probe build with `ground_clearance = 0.071` (BmAK's measured underbody
gap) and compare the resting stance/kerb scrape against 0.7037; adopt the value the engine
actually uses and reclassify the row `assumed` in the meantime.

---

## T-G6 — wheel radius (0.64 sim vs 0.683 mesh) · **LORE-EXACT**

The decision the operator asked for, and the evidence that settles it.

**BmAK numbers.** [decoded] `SVehicleWheel.WheelRadius = 64.0` cm = **0.640 m** (`CHAIN.json`
offset 568, all four wheels, all four packages); [decoded] tyre radius from the mesh
**0.68275 / 0.68265 m** (`TYRES.md` §1).

**Built number** — `front_wheels.radius 0.682750`, `rear_wheels.radius 0.682650`.

**What the JC3 member is used for — tested, not assumed.** `land_global.*_wheels.radius` is the
hub-to-ground distance of the **tyre**: it is an axle scalar paired with the hardpoints and with
`ground_clearance`, there is no second "visual radius" anywhere in `land_global`
(`Research/JC3Grab/VOCABULARY.md`: one `front_wheels`/`rear_wheels` structure, members `radius`,
`rim_radius`, `width` only), and `land_suspension.*.raycast_offset` is **0** on all 167 vehicles
that carry it — so the contact query starts at the hub and the radius *is* the contact distance.

The fleet arithmetic confirms the two are the same quantity:

```
hub y − radius, 144 land vehicles (Research/JC3Grab/FLEET.md, "hub y"/"tyre r" columns)
    min −0.1647   p10 −0.1003   median −0.0055   p90 +0.0340   max +0.1440
    mode bins: −0.01 (27 vehicles), −0.02 (21), +0.02 (21), 0.00 (18)
vanilla donor (Serpente):  hub 0.400 − radius 0.380 = +0.0200
our build:                 front 0.7047 − 0.68275 = +0.02195
                           rear  0.7027 − 0.68265 = +0.02005
```

A radius that were a *smaller contact approximation inside a bigger visual tyre* would show a
systematic positive bias (the visual-vs-contact gap) across the fleet. It does not: the median is
−5.5 mm and the distribution is centred on zero. The hub sits **one tyre radius above the
contact**, which is exactly the geometry of a visible tyre standing on the road. Our rear axle
reproduces the donor's +0.0200 to 0.05 mm and the front's +0.02195 sits in the +0.02 bin shared
by 21 vehicles.

**Verdict: 0.683 is LORE-ACCURATE, not a compromise.** 0.68275/0.68265 is the visible tyre's own
radius, so the tread meets the ground at the mesh's hub height — the car stands exactly as the
lore car stands. Carrying BmAK's 0.640 instead would put the contact surface **4.27 cm inside the
tyre**: either the tyre floats 4.3 cm off the road, or the hub is lowered 4.3 cm to restore
contact and the whole car sits 4.3 cm below its measured stance (`0.7047 − 0.640 = 0.0647` m of
air under the hub against a 0.7307 m wheel). Neither is the lore car.

**What is genuinely lost.** BmAK's build carries *two* radii — a 0.640 m simulation radius and a
0.683 m visual tyre — and JC3 carries *one*. That duality is inexpressible in `land_global`; the
built car is correct for the visible/contact geometry and simply has no separate sim radius to
mismatch. Record it as a **gap, not a delta**: nothing in the build is wrong, one BmAK field has
no JC3 carrier.

---

## Closest system, and the gap for the build (STAGES.md)

| gap | closest JC3 system | what the build must do |
|---|---|---|
| radius/width are **per axle**, BmAK is per corner (4 values each) | `land_global.front_wheels` / `rear_wheels` | keep the axle mean (deviation ≤ 0.55 mm); a per-corner value needs per-corner parts/rays, which no member offers |
| BmAK's **two** radii (0.640 sim / 0.683 visual) | one `radius` member | nothing to author; log the missing sim radius as a named BmAK field with no carrier (T-G6) |
| `ground_clearance` semantics **UNKNOWN** | `land_global.ground_clearance` | one probe build at 0.071 m (BmAK's measured underbody gap) vs 0.7037 |
| wheel *parts* still carry the Serpente transform (1.0130 m from their hardpoint) | `parent_space_offset` vs `base_wheel_hardpoint_positions[]` | re-emit the part translations at the true hubs (`bm_parts.py` already records this as owed) — open item, outside T-G1…T-G6 |
| `rim_radius` has no BmAK counterpart | `front/rear_wheels.rim_radius` (built 0.539013 / 0.538934 = vanilla × radius ratio) | accepted: the build scales the shipped value by the radius ratio, which is the only rule the data supports |

**Stage placement.** All five rows are *geometry already in the build*; only T-G4 needs a build
action, and it is the single probe in §STAGES' validation band (kerb/pothole/landing, Q2-A6).
Nothing here blocks a stage.

---

## UNKNOWN

1. **What `land_global.ground_clearance` actually controls** — the build sets it to the hub mean;
   BmAK's measured underbody gap is 0.071 m. No file decodes the consumer.
2. **Whether the runtime places a wheel part by `parent_space_offset` or by
   `base_wheel_hardpoint_positions[]`** (`Builds/bm-RC2/verify/wheels.md` §5) — decides whether
   the 1.0130 m part-transform delta is visible.
3. **What BmAK's 0.640 m sim radius is used for** (raycast contact, articulation limit, or
   nothing) — `SVehicleWheel` has no decoded consumer; only the value is decoded.
4. **The `tyre_width` corner attribution** — `stations.json` is mirrored L↔R and records no
   `tyre_bone`, so the derivation cannot be traced (R3).

---

## Checks run

| # | check | result |
|---|---|---|
| 1 | decode of the five members + four hardpoints from the built `land_global.vmodc` | values in the header table; offsets from `Working/Stance/land_global_check.xml` |
| 2 | `python Tools/scripts/v_wheels.py --check` | **check ok** (exit 0); radius = station mean ≤ 0.5 mm, width = mesh mean ≤ 0.5 mm, hardpoints/slots/signs asserted |
| 3 | ledger rows T-G1…T-G6 read from `Working/Translation/T_ROWS.jsonl` | all five `dispo: keep`; T-G4's class cell is the assumption |
| 4 | fleet radius semantics: 144 rows parsed from `FLEET.md` | hub−radius median −0.0055, p10 −0.1003, p90 +0.0340 |
| 5 | `Research/challenge/T1_TRANSLATION.md` C09 | T-G4 `derived` **REFUTED** as class |
| 6 | `MODLOG` ledger-audit line | T-G4 among 7 GUESSED (`0.7037 assumed`) |

No game process started; static reads and one read-only generator check.

## Reproduce

```bash
python Tools/scripts/v_wheels.py --check
python - <<'EOF'
import xml.etree.ElementTree as ET, struct
b=open('Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/v0300_car_kensington_sportsmuscle_land_global.vmodc','rb').read()
for m in ET.parse('Working/Stance/land_global_check.xml').getroot().iter('member'):
    if m.get('offset-in-file') and m.get('name') in ('ground_clearance',):
        print(m.get('name'), struct.unpack_from('<f', b, int(m.get('offset-in-file'),16))[0])
EOF
```
