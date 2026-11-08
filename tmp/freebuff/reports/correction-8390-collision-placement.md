# Correction 8390 — the B-10 collision placement gate: decided on the shipped bytes

DECISION: **(a), and it is already true on the artifact.** Body 0 sits on the chassis box's own
floor (0.030 m), not on DIM-1's render ground line (0.091 m). Re-measured on the bytes that ship,
the placement deviation is **0.0025 m (2.5 mm)** against the card's **5 cm** limit → **gate MET**.
The 6.1 cm figure is real, but it belongs to the **previous payload** (sha `0164936b…`), not to the
file in the RC4 tree.

Option (b) — "the ground line is the intended contact plane" — is refused on evidence:
`Tools/scripts/bm_collision2.py` records the decoded fact that DIM-1's `y_min` is a **render mesh
ground line, not a contact plane** (source comment, lines ~250-260), and BmAK's own box 0 bottom is
3.0 cm in bone space, i.e. **6.1 cm above** that render floor. Re-wording would enshrine the render
bbox rule that `T-22` was reopened to abandon.

## 1. What was re-measured (the shipped bytes, not the report text)

| quantity | value | how |
|---|---|---|
| shipped file | `Builds/bm-RC4/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc` | the only `.physicsc` under `Builds/bm-RC4/**` |
| size / sha256 | **340,368 B** / `fda78f4d8056a4ee…` | read off disk |
| `.toc` record | offset **15,993,844**, length **340,368** | `receipt.collision.toc_record` |
| body-0 hull, decoded from the file | 36 vertices, min `[-1.8732, 0.030, -3.359]`, max `[1.8722, 2.105, 3.544]`, size `[3.7454, 2.075, 6.903]` m | `hknpPhysicsSystemData` body table +0x2D20 → polytope relarray at +0x30, walked in this pass |
| BmAK chassis box 0 (JC3 axes) | min `[-1.8727, 0.030, -3.3615]`, max `[1.8727, 2.105, 3.5415]`, size `[3.7454, 2.075, 6.903]` | `Working/Collision2/bm_vehicle_hull.json` `chassis_box_0` (centre `[9.0, 0.0, 106.75]` cm, extents `[690.305, 374.536, 207.5]` cm) via the axis map |
| **placement deviation** | `[0.0005, **0.0000**, 0.0025]` m → max **2.5 mm** | difference of the two rows above |
| **size deviation** | `[0.0000, 0.0000, 0.0000]` m (receipt records `1.0e-04` from its 4-dp rounding) | same |

Both floors agree to the millimetre: **0.030 m on the box, 0.030 m on the hull**. The 6.1 cm is gone
in the shipped file.

## 2. Where the 6.1 cm actually is

| file | body-0 min y | sha256 | what it is |
|---|---:|---|---|
| `Working/Collision2/batmobile.physicsc` (current) | **0.030** | `fda78f4d…` | the box-floor variant; **this is what ships** |
| the payload quoted by `build-d08 §4` and `build-d13 §2` | **0.091** | `0164936b…` | the render-floor variant, replaced in place |
| `receipt.collision.gate.placement_dev_m` | — | — | `[2e-05, 0.0, 2e-05]`, `pass: **true**`, `limit_m 0.05` |

Note the offset and length are **identical** (15,993,844 / 340,368) in both reports and in the
receipt: the payload was rewritten in place, so only the hash and the body hull moved. That is why
the two reports' tables and the receipt disagree while every path, size and `.toc` number matches.

`receipt.collision.dev_vs_render_bbox_m = [0.1252, 0.196, **0.061**]` is the **render-bbox** delta —
the hull is deliberately narrower and lower than the render silhouette — and its third component is
the same 6.1 cm seen from the other side. It is not, and never was, the gate.

## 3. The tool in the brief is not the writer (a correction to correction 1/9)

`bm_vehicle_hull.py` **cannot** rebuild body 0: its `main()` (lines 493-503) writes only
`Working/Collision2/VEHICLE_HULL.md` and `bm_vehicle_hull.json` — the *record* of the BmAK box TMs
and the body table. It reads `Working/Collision2/batmobile.physicsc` as input.

The writer that owns the placement is **`bm_collision2.py` (B-10d)**, on `bm_collision.py`'s writer
paths:

- its declared rule: *"y: decoded — the bottom is BmAK's chassis box 0 floor, centre z 106.75 cm −
  extent z 207.5/2 = 3.00 cm, mapped to JC3 y (0.030 m). DIM-1's `y_min` (0.091 m) is the render
  mesh's ground line, not a contact plane; using it placed the hull 6.1 cm high"*
  (`bm_collision2.py`, target placement);
- it writes `Working/Collision2/batmobile.physicsc` (`OUT_BIN`) and re-emits every donor hull check
  through `bm_colhull.selftest`.

So the rebuild the brief asks for has **already been run** and its output is what ships. Running
`bm_vehicle_hull.py --write/--check` instead would rewrite the record and leave the hull untouched —
which is why this correction re-measured the binary rather than re-running a generator that cannot
change it.

## 4. Cells that are now wrong (left unedited: they are historical reports)

| file | cell | reads now | correct value |
|---|---|---|---|
| `tmp/freebuff/reports/build-d08-health-collision.md` §4 | built body-0 hull AABB | min `[-1.8732, 0.091, -3.359]`, max `[1.8722, 2.166, 3.544]` | min y **0.030**, max y **2.105** |
| same | deviation vs chassis box 0 | `max 0.061 m` | **0.0025 m** |
| same | shipped payload sha | `0164936b928f821c…` | `fda78f4d8056a4ee…` |
| same | UNKNOWN #1 ("the 6.1 cm vertical offset … a drive question") | open | closed by measurement: placement dev 0.0000 m on y |
| `tmp/freebuff/reports/build-d13-release-candidate-4.md` §2 | hull placement vs box | `[0.0005, 0.061, 0.0025]` → 6.1 cm | `[0.0005, 0.0000, 0.0025]` → **2.5 mm** |
| same | card gate 5 cm | **NOT MET** | **MET** |
| same | `.physicsc` sha | `0164936b…` | `fda78f4d…` |
| same §8 bullet 1 | "Rebuild B-10 with the chassis box's own placement … to clear the 5 cm gate" | to do | done; the bullet should read "the gate is met; the shape count is the open half" |

Nothing was edited in either report by this pass — the wrong cells are listed so the operator can
decide whether those two files are corrected in place or superseded by a pointer to this one.

## 5. What is still open — and it is not placement

`receipt.collision.gate.shapes_pass = **false**`, and that half is honest:

- **1 of 3 boxes carried**: chassis box 1 (centre `[0, 0, 79.0]` cm, extents `679.585 × 345.688 ×
  103.5` cm, identity TM, export 169750 box 1) and the weapons pod (centre `[-30.5, 0, 93.25]` cm,
  extents `166.177 × 189.365 × 39.8` cm, **4.000°** about y, export 169751 box 0) have **no shape
  instance**.
- **0 of 54 hull slots free**; 62 donor bodies over 54 hull objects; the 14 "unbound" instances are
  the two bumper compounds' children (bodies 16/26), which is why landing a shape on body 0 needs
  insertion, not a free slot.
- **The 1 constraint** is a named omission: no `RB_ConstraintSetup` layout exists in
  `BMSDK_OFFSETS.json`, so there is nothing to serialise it with.

Per `closest-system-rule` this stays a build gap with a route, not a report line: the union hull in
`tmp/freebuff/reports/collision-missing-shapes-closest-system-plan.md` covers both missing boxes
inside the 5 cm band **without a new slot** (box 1 protrudes past box 0 by 3.640 cm at −x; the pod
lies entirely inside box 0), so the build's next measurable step is to re-derive the union on the
shipped bytes and carry "3 boxes / 1 hull" in the receipt rather than "1 of 3".

## 6. Checks run in this pass

| check | result |
|---|---|
| `python Tools/scripts/bm_collision2.py --check` | **CHECK OK**: 10 oracles, 6 audit rows, body hull `3.745 × 2.075 × 6.903` m, **340,368 B**, wheel hulls unchanged 4/4, exit 0 |
| `python Tools/scripts/bm_vehicle_hull.py --check` | **CHECK OK**: 10 oracles, 90 lines, pskx `[702.56, 349.53, 234.185]` cm, chassis TM identity, bodies 62, exit 0 |
| body-0 AABB re-decoded from the shipped `.physicsc` | min y **0.030**, max y **2.105**; placement dev 2.5 mm (this pass) |
| `python Tools/scripts/bm_rc4.py --check` | **COULD NOT RUN**: `MemoryError` in `tree()` at `bm_rc4.py:118` while hashing `Builds/bm-RC4-base/aaf`. Not a data failure — the check needs more memory than this machine gave it. The RC-level gate assertion (`bm_rc4.py:863-871`) is therefore **unverified by command**; the receipt's own cells were read instead. |
| `jc3hkx` re-read of the shipped file | implied green by `bm_collision2 --check` (it runs `check_file`), not re-run separately |

## 7. Pilot card

"In the Batmobile, drive up a 10 cm kerb slowly and ram a low wall at 30 km/h: the car climbs the
kerb without a step and the wall stops it at the body's skin, not 6 cm early." Pass band: no visible
vertical step at the kerb (≤2 cm ride-height change from the collision alone), and the wall contact
point within 5 cm of the body's visible panel.
