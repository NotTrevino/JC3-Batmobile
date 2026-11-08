# Assumption challenge — card T-13 · Interaction translation

Written 2026-10-30. **Read-only review**: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/`, `Working/`, `Builds/` or any game file was modified; the only file written is this one.
No game was launched, nothing was written to `D:\Games`, nothing was committed, no secret was read.
`t9_interaction.py --check` and in-memory Python heredocs only; no probe script was left on disk.

**In scope**, as the card requires: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–77), the T-13 card
(lines 888–903), its §12 row (line 1322), the MODLOG sections `## T-13 · Interaction translation —
intended change` (12862) and `— done (2026-10-28)` (12888), and the card's outputs —
`Working/Translation/T9_INTERACTION.md` (167 lines), `Working/Translation/t9_interaction.json`
(4,592 lines, 85 objects), `Tools/scripts/t9_interaction.py` (483 lines). Cross-checked against
the card's `In:` files (`Research/JC3Grab/INTERACTION.json` digest `da864a28edcbcbff`,
`Research/BatmobileGrab/COCKPIT.md`, `SOCKETS_JC3.json`, `SEAT.md`, `EJECT.md`), the mesh
`Working/TrueScale/body_lod1.rbm` through `rbm_geom`/`jc3interact`, `Working/TrueScale/stations.json`,
`DOORS.md`, `T8_PARTS.md` (T-12), §1.2 (DIM-1), §9b Q-1 #3, and §11 D-9.

**Card as written:** "for every interaction object, compute its new transform on the Batmobile
body … place it on the Batmobile surface at the analogous location (side of the cockpit for entry,
roof centre for `point.stunt`, front deck for `point.stunt.hood`, rear deck for `point.stunt.rear`),
offset outward by the donor's own clearance from its surface. Driver seat → `Driver` socket.
**Stunt areas → planes fitted to the Batmobile roof/deck faces (normals within 20° of up).** Decide
hijack entries per D-9. Done: every object has a new transform; every transform is ≥ 0.05 m outside
the hull and ≤ 0.30 m from the surface (stunt/entry) — checked by the script."

---

## VERDICT

**The gate is green and the frame/units are right; the Done rule is a tautology, one of the card's
deliverables (stunt-area planes, 20° normals) is missing from the implementation, and the anchor
stations sit on a mesh whose top surface moves 0.12–0.28 m within ±2 cm.** `--check` passes (exit
0), the 85 objects and their roles reconcile with `INTERACTION.json` exactly, the driver side is
not mirrored (the donor's own driver points are at −x), the `Driver` socket matches COCKPIT.md to
4 mm, and the coordinate frame (left = −x, ground 0.020, nose −z) is the project's own, quoted from
COCKPIT.md and `stations.json`. What does not survive: "every transform is ≥0.05 and ≤0.30 m" is
achieved by the same function that measures it (it cannot fail), the "decoded" hood clearance is a
chosen 0.06 m (the donor says 0.048), the nearest hull face to both stunt points is **28.8°/32.7°**
off up — outside the card's own 20° rule — and no plane is emitted at all: `plane_anchor()` with the
20° filter exists as dead code. The 85 rows also reduce to **5 distinct transforms**, 6 of the
85 object ids are duplicated (so "object id → new transform" is a list, not a map), and the seven
trigger volumes lose the scale that gives them their size (up to 19.1 × 14.1 × 23.4 m).

| # | assumption | verdict |
|---|---|---|
| A1 | the Done gate (`t9_interaction.py --check`) is green and the output is reproducible | **HOLDS** — `PASS … 77 placed in band`, exit 0; json + md + invariants all compare |
| A2 | "every transform is ≥0.05 m outside the hull and ≤0.30 m from the surface" is a test that can fail | **BROKEN as a test** — the same solver moves each point until its measured distance equals the target inside the band; 77/77 pass by construction |
| A3 | the hood's clearance is the donor's decoded 0.048 m | **WEAK** — `max(gap, 0.06)` replaces it with a chosen 0.06 m; the achieved distance is 0.0573 m |
| A4 | "clearance (m)" in the table is the distance to the hull | **WEAK** — it is the offset along the anchor normal (0.1659 hood / 0.1656 roof); the hull distance is 0.0573 / 0.1453, i.e. two different numbers under one name |
| A5 | "Stunt areas → planes fitted … normals within 20° of up" | **BROKEN** — not implemented: `plane_anchor`/`up_faces`/`UP_COS` are dead code, anchors are single down-rays with a hard-coded `[0,1,0]` normal, no plane/area is emitted |
| A6 | the anchor stations are stable points on the body | **WEAK** — ±2 cm along z moves the hood top by 0.12 m and the roof top by 0.28 m; at x = 0 the hood ray misses entirely; the "roof … canopy over the driver" is 0.57 m aft of the driver |
| A7 | the object's role comes from its behaviour | **WEAK (card-authored)** — classification is substring precedence `hood > stunt > passenger1 > driver`; four donor *states* are split across hood and roof purely by the word "hood" in one name |
| A8 | "70 of 85 have no position of their own, so there is nothing finer to copy" | **WEAK** — 70 inherited, but 15 carry an `own` world position *and* a mapped `batmobile` position the tool never reads (11 of them ≥1 m off; the nearest, `point.stunt.hood`, is 0.22 m and would have corroborated the anchor) |
| A9 | the cockpit side is the right surface for 54 entry/exit/trigger nodes | **WEAK** — the flank geometry is correct (nearest normals ±0.996 lateral) and the donor's own side agrees, but the Batmobile's aperture is the canopy (T-12), so the points sit on a closed panel |
| A10 | one seat (so `interaction.seat.passenger1` is UNKNOWN) | **WEAK** — 25 passenger objects are still placed on the right flank for a seat that the same file declares non-existent; Q-1 #3 expects driver entry *from both sides* |
| A11 | the output is "object id → new transform" | **WEAK** — 85 rows, 79 unique names (`transition.driver`/`stunt`/`passenger1` ×3 each), 5 distinct positions in total |
| A12 | frame and units (left = −x, ground 0.020, nose −z; metres) | **HOLDS** — quoted from COCKPIT.md and `stations.json`; mesh bbox matches DIM-1 within 1.7 cm |
| A13 | yaw is `atan2(fwd.x, −fwd.z)` and is derived, not decoded | **HOLDS as declared** |
| A14 | the D-9 drop set is the six hijack objects | **HOLDS** — 6 names, all `*pull.out*`/`*pulled.out*`, D-9 resolved "no" |
| A15 | the counts (85 / 77 / 6 / 1 / 1; roles 29-9-25-19-3) | **HOLDS** — every number recomputed, `INTERACTION.json` classes and prefixes sum to 85 |
| A16 | the body mesh is the right surface to measure against | **HOLDS with a limitation** — `body_lod1` is the highest LOD present and the only Batmobile surface on disk (DIM-4 has no Batmobile `.physicsc` yet) |
| A17 | a transform needs only pos/forward/up/yaw | **BROKEN for triggers** — 7 points carry a non-unit `scale` (2.65→19.1 m); the delivered transform has no scale field at all, so the volumes become points |

**Bottom line:** three repairs are needed before the rows are consumed by B-05/T-19/B-02 — carry
the trigger `scale` through (A17, without it the stunt triggers have no volume), implement the
stunt-area planes or strike that sentence from the card and the doc (A5), and make the placement
check something other than its own solver (A2). Then record A3/A4 honestly (the "decoded" hood
clearance is 0.06 chosen, and the column is an offset, not a clearance) and add the canopy caveat
(A9). Everything else is record quality.

---

## A1 · The Done gate is green and the output is reproducible

**The result rests on:** §0.2 step 6 (run the Done check, paste the output) and R11 (generated,
`--check`).

**Test.**

```
$ python Tools/scripts/t9_interaction.py --check ; echo EXIT=$?
PASS: 85 objects, 77 placed in band [0.05, 0.3] m, 6 dropped (D-9), 1 socket, 1 unknown
EXIT=0
```

`cmd_check` rebuilds `build()` from `INTERACTION.json` + the mesh, compares the whole JSON dict
(`old != d` → `json section changed: <key>`), compares the rendered md byte-for-byte, and then runs
`invariant_checks` (85 rows, every placed row measured and in band, socket at `DRIVER`, unknown has
no transform, counts add up, `dropped_D9 == 6`, `unknown == 1`). The delivered files are current —
unlike T-11, whose generator is red on disk today.

**Verdict: HOLDS.** The tamper test quoted in the MODLOG (`point.stunt` y → 1.6 →
`FAIL: json section changed: objects`) is structurally guaranteed by the dict comparison.

---

## A2 · The Done rule ("≥ 0.05 m outside the hull, ≤ 0.30 m from the surface") is a test that can fail

**The result rests on:** the card's Done line and the MODLOG's "All 77 placed transforms are >= 0.05 m
outside the hull and <= 0.30 m from the nearest body triangle (the card's rule)".

**Test.** The placement and the assertion are the same measurement:

```
$ sed -n '/def solve_offset/,/return off/p' Tools/scripts/t9_interaction.py
    def solve_offset(tris, surface, normal, target):
        """Distance along the anchor normal so the measured hull distance equals `target`."""
        off = target
        p = surface + normal * off
        d = float(jc3interact.nearest_distance(tris, np.array([p]))[0])
        for _ in range(10):
            if abs(d - target) <= 0.004:
                break
            off = min(max(off + (target - d), BAND[0] + 0.006), BAND[1] - 0.006)
            ...
```

and the invariant re-measures the same quantity:

```
$ sed -n '/def invariant_checks/,/return bad/p' Tools/scripts/t9_interaction.py
            elif not (lo <= m["nearest_m"] <= hi):
                bad.append(f"{r['name']}: {m['nearest_m']} m outside [{lo}, {hi}]")
```

The solver stops when the nearest-triangle distance equals a target that is itself inside the band
(0.06 hood, 0.1474 roof, 0.10 sides), with a ±4 mm tolerance and the offset clamped to
[0.056, 0.294]. The assertion then checks that the same distance is in [0.05, 0.30]. All five
measurement values are the five targets:

```
$ python - <<'EOF'   (Working/Translation/t9_interaction.json)
rows 85 ; nearest_m distribution {0.0279: 1, 0.0573: 9, 0.0969: 29, 0.1001: 25, 0.1453: 20}
EOF
```

**Verdict: BROKEN as a test.** A placement rule that is satisfied by construction cannot
discriminate a good placement from a bad one. The falsifiable content of the card is different and
none of it is checked: *is the anchor on the face the role means?* (see A5/A6 — for the two stunt anchors the nearest face is 28.8° and 32.7° off up) and *does the object sit where the lore puts it?*
(the canopy question, A9). The right repair is a second, independent check — e.g. "the nearest
triangle's normal is within N° of the anchor normal" — which the tool already has the pieces for
(`up_faces`).

---

## A3 · The hood's clearance is the donor's decoded 0.048 m

**The result rests on:** the §2 anchor table, "0.06 m - decoded (donor stunt-area gap 0.048 m, band
floor applied)", and the MODLOG's "donor clearances 0.048/0.1474 m where G2-18 decoded them".

**Test.**

```
$ python - <<'EOF'   (Research/JC3Grab/INTERACTION.json → stunt_areas)
areas: [('front_area', 0.048, 4, 'sportsmuscle_hood'),
        ('front_signature_area', 0.048, 4, 'sportsmuscle_hood_signature'),
        ('main_area', 0.1474, 8, 'sportsmuscle_body')]

$ grep -n "SIDE_MARGIN\|def clearance_for" -A 6 Tools/scripts/t9_interaction.py
SIDE_MARGIN = 0.06          # band floor + 10 mm so a re-measure stays above 0.05
    gap = anchor.get("donor_gap_m")
    ...
    return {"m": round(max(float(gap), SIDE_MARGIN), 4),
            "source": f"decoded (donor stunt-area gap {gap} m, band floor applied)"}
```

max(0.048, 0.06) = **0.06**, so the value written is not the decoded one, while the class label
still begins with "decoded". The roof's 0.1474 does survive (it is above the floor), so the two
stunt anchors are treated differently and the label reads the same.

**Verdict: WEAK.** The donor gap is decoded; the number used is a chosen 6 cm, and the label
attributes it to the donor. The doc's own UNKNOWNs section already says the *side* clearance is
chosen; the hood's is chosen too and is labelled decoded. One line in `clearance_for` (and the
label) fixes it.

---

## A4 · "clearance (m)" is the distance to the hull

**The result rests on:** §4's table columns `clearance (m)` and `nearest (m)` sitting side by side,
and the §2 header "target clearance".

**Test.** For the two stunt anchors the table prints:

```
$ python - <<'EOF'   (t9_interaction.json)
point.stunt.hood  pos_m=[0.0005, 1.5265, -2.14]  clearance=0.1659  nearest=0.0573
point.stunt       pos_m=[0.0005, 2.2467, -0.5]   clearance=0.1656  nearest=0.1453
EOF
```

The "clearance" is the distance moved along the anchor normal (`clearance.m = off`), not the
distance to the surface; for the hood it is **2.8×** the nearest-triangle distance, because the
nearest triangle is not the ray-hit deck. Probing which triangle that is:

```
$ python - <<'EOF'   (nearest triangle per placed point, rbm_geom + jc3interact)
point.stunt.hood  d=0.0573 tri_c=[-0.0, 1.4905, -2.1847]     n=[0.334, 0.842, -0.424] off_up=32.7deg
point.stunt       d=0.1453 tri_c=[-0.0002, 2.1158, -0.5631]  n=[-0.016, 0.877, 0.481] off_up=28.8deg
entry.driver      d=0.0969 tri_c=[-1.4743, 1.1458, -0.9456] n=[-0.996, 0.067, 0.061] off_up=86.2deg
entry.passenger1  d=0.1001 tri_c=[1.4743, 1.1484, -0.9502]  n=[0.996, 0.067, 0.062]  off_up=86.2deg
EOF
```

So the hood point is 5.7 cm from the top of a **raised element** whose normal is 32.7° off vertical
(centroid y 1.4905, i.e. 13 cm above the deck ray-hit at 1.3606) — it is not "6 cm above the deck"
at all: the deck itself is 16.6 cm below the point. The reported pair (0.1659 / 0.0573) is correct
arithmetic for two different quantities; a reader will take "clearance 0.1659, target 0.06" as a
contradiction or as "16 cm off the surface".

**Verdict: WEAK.** Rename the column (`offset along normal`) or report the distance to the *anchor
face*, and the confusion disappears.

---

## A5 · "Stunt areas → planes fitted to the Batmobile roof/deck faces (normals within 20° of up)"

**The result rests on:** the card's Do step, the tool's docstring ("`UP_COS` = the card's 'normals
within 20 deg of up'"), and the MODLOG's "role anchors ray-cast on `body_lod1.rbm`: … roof y 2.0811
at z -0.5".

**Test 1 — the 20° machinery is never called.**

```
$ grep -n "plane_anchor\|up_faces\|UP_COS" Tools/scripts/t9_interaction.py
57:UP_COS = math.cos(math.radians(20.0))   # the card's "normals within 20 deg of up"
63:def up_faces(V, T):
73:    return ok & (n[:, 1] >= UP_COS), n, cent
76:def plane_anchor(V, T, x, z):
78:    mask, n, cent = up_faces(V, T)
```

Only the definitions. `anchor_table()` calls `top_hit()` (a vertical down-ray) and hard-codes
`"normal": [0.0, 1.0, 0.0]`; no caller of `plane_anchor`/`up_faces` exists, and the JSON carries no
plane, no area polygon, no face normal. The `stunt_areas` input (3 active areas, 4/4/8 triangles,
bboxes, `deform_points`, welds) is used only for `[0]` of `bat_center_geom` and `center_gap_m`.

**Test 2 — the faces actually nearest the two stunt points violate the card's own 20° rule:**

```
point.stunt       nearest triangle normal [-0.016, 0.877, 0.481]  → 28.8° off +up
point.stunt.hood  nearest triangle normal [ 0.334, 0.842, -0.424] → 32.7° off +up
```

**Verdict: BROKEN.** One of the card's two explicit geometric instructions is not implemented, and
the two points that were produced sit against faces the instruction would have excluded. Either
implement `plane_anchor` (which is written and tested by nothing) and emit the fitted plane, or
amend the card and the doc to say "a point per stunt object, placed above a ray-hit surface".

---

## A6 · The anchor stations are stable points on the body

**The result rests on:** four fixed stations — hood `x 0.0005, z -2.14`; roof `x 0.0005, z -0.5`;
sides `y 1.15, z -0.95` — each a single ray, reported to four decimals.

**Test.** The same ray code, swept by 2 cm:

```
$ python - <<'EOF'   (vertical down-ray onto body_lod1.rbm)
hood z=-2.14 grid:  x=-0.02 → 1.3599   x=0.0 → None   x=0.0005 → 1.3606   x=+0.02 → 1.3599
z scan at x=0.0005: -2.20 → 1.4826   -2.18 → 1.3882   -2.16 → 1.2405
                    -2.14 → 1.3606   -2.12 → 1.2737   -2.10 → 1.4114
roof z=-0.5 grid:   -0.60 → 2.1084   -0.55 → 2.1086   -0.52 → 2.0921
                    -0.50 → 2.0811   -0.48 → 1.7981   -0.45 → 1.8029
EOF
```

Three consequences:

1. **At x = 0 the hood ray misses the mesh entirely** (`None`, and `_ray_hit` would raise
   `SystemExit("ray … misses the body mesh")`). The tool survives only because the area's centre x
   is 0.0005, not 0 — a mesh seam (the classic edge-on-ray failure, `u >= 0, v >= 0` failing on
   both adjacent triangles).
2. **The hood top is non-monotone at cm scale** — 1.2405 / 1.3606 / 1.2737 within 4 cm of z. The
   "front deck surface" is one sample of a surface that swings 0.12 m; the panel structure (vents,
   slots) is being hit rather than a deck.
3. **The roof station is a knife edge**: 2.0811 at z −0.50, **1.7981** two centimetres aft. So
   `ROOF_Z = -0.50` is the canopy's trailing edge, not "roof centre". The parenthetical is repeated
   verbatim in the MODLOG done section ("topmost body surface at z -0.5 over the driver") and is
   wrong by station: the driver is at z −1.0654, where the top ray gives y 1.9957 (COCKPIT.md:
   liner 1.9661, skin 1.9914) — 0.57 m forward and 8.5 cm lower than the anchor. The plane the 20
   stunt objects are placed over is the deck **behind** the cockpit.

The side anchors are sound by contrast: the nearest triangles are `[-0.996, 0.067, 0.061]` and
`[0.996, 0.067, 0.062]` — genuine flanks at x −1.468 / +1.467.

**Verdict: WEAK.** The positions are not wrong in the sense of being off the car, but the reported
4-decimal anchor is a ±0.12 m (hood) / −0.28 m one-sample (roof) estimate, and the roof's label
("canopy over the driver") does not match the station. A 5×5 ray grid per anchor (or the dead
`plane_anchor`) would make the number mean something.

---

## A7 · The object's role comes from its behaviour, not its name

**The result rests on:** `classify()` — "deterministic, ordered rules" — and the 85-row table.

**Test.**

```
$ python - <<'EOF'   (import classify, run it over INTERACTION.json)
    if "hood" in name:   kind, role = "hood", "hood"
    elif "stunt" in name: kind, role = "roof", "stunt"
    elif "passenger1" in name: kind, role = "right", "passenger"
    else: kind, role = "left", "driver"
EOF
```

The name decides the surface; `class`, `state` and `world` are copied but never used for placement.
Four donor **states** are therefore split across two anchors because one of the two names contains
"hood":

```
S_PULL_UP_TO_STUNT_CLOSE_VEHICLE   entry.pull.up.to.stunt.hood.close → hood   entry.pull.up.to.stunt.close → roof
S_PULL_UP_TO_STUNT_FAR_VEHICLE     entry.pull.up.to.stunt.hood.far   → hood   entry.pull.up.to.stunt.far   → roof
S_STEP_OVER_LOW_TO_STUNT_VEHICLE_P1  entry.step.over.low.stunt.hood  → hood   entry.step.over.low.stunt    → roof
S_STEP_OVER_HIGH_TO_STUNT_VEHICLE_P1 entry.step.over.high.stunt.hood → hood  entry.step.over.high.stunt    → roof
```

The same behaviour (one animation state) lands on the front deck in one object and on the roof in
its twin. Two further names are resolved by the fallback alone: `entry.stunt.to.driver.side.enter
.vehicle2/3` go to the **roof** although their state is `S_ENTER_STUNT_TO_DRIVER_SIDE_VEHICLE`
(driver side), and `exit.ai.passenger1.to.hood` goes to the **hood** although its state is
`S_EXIT_DRIVER_TO_HOOD_VEHICLE` (a *driver* exit).

**Verdict: WEAK, and card-authored.** The card itself asks for "roof centre for `point.stunt`,
front deck for `point.stunt.hood`", i.e. it mandates the name split, so the tool complies with its
brief. The consequence for R5 is that these rows must not be read as behaviour-verified: they are
name-placed, and the state field that *would* verify them is in the same JSON and unused. Recording
that in the doc's UNKNOWNs costs one sentence and protects the rows from a later "R5 violation"
finding.

---

## A8 · "70 of 85 have no position of their own, so there is nothing finer to copy"

**The result rests on:** §6, "the donor's world positions are mostly inherited container origins
(70 of 85), so there is nothing finer to copy".

**Test.**

```
$ python - <<'EOF'   (INTERACTION.json counts)
world_source: {'inherited': 70, 'own': 15}
verdict: {'n/a (container origin)': 32, 'inside': 30, 'floating': 23}
frames.mapping: "u = (p - serpente_min)/(serpente_size); p' = bat_min + u*bat_size"
counts.by_class: CInteraction 3, CInteractionGraphEntry 29, CInteractionGraphExit 26,
                 CInteractionGraphPointNode 8, CInteractionGraphTransition 12, CInteractionTrigger 7
EOF
```

70/85 reproduces, and the 30 inside / 23 floating / 32 origin values are exactly why a role method
beats copying. But the same file ships a **mapped `batmobile` position for every one of the 85**,
including the 15 with an `own` world position, and the tool reads none of them. Where I make that
comparison (the only independent cross-check available):

```
$ python - <<'EOF'   (all 15 `own` points: mapped batmobile vs the tool's placement)
point.stunt                      mapped [ 0.0005, 2.3074,  0.698 ]  tool [ 0.0005, 2.2467, -0.50]   d=1.20
point.stunt.hood                 mapped [ 0.0005, 1.6564, -1.9627]  tool [ 0.0005, 1.5265, -2.14]   d=0.22
trigger.stationary.stunt         mapped [-0.0367, 1.9805, -0.0181]  tool [ 0.0005, 2.2467, -0.50]   d=0.55
trigger.stunt                     mapped [-0.5382, 2.5494, -0.0089]  tool [ 0.0005, 2.2467, -0.50]   d=0.79
trigger.stunt.vehicle.to.vehicle  mapped [-0.5382, 2.5494, -0.0089]  tool [ 0.0005, 2.2467, -0.50]   d=0.79
point.driver                      mapped [-0.5776, 0.5976,  0.3916]  tool [-1.571,  1.15,   -0.95]   d=1.76
point.passenger1                  mapped [ 0.5815, 0.5976,  0.3916]  tool [ 1.5744, 1.15,   -0.95]   d=1.76
trigger.driver                    mapped [-1.9441,-0.0833,  0.5118]  tool [-1.571,  1.15,   -0.95]   d=1.95
trigger.passenger1                mapped [ 1.9451,-0.0833,  0.5118]  tool [ 1.5744, 1.15,   -0.95]   d=1.95
point.passenger1.onground         mapped [ 0.0005, 0.091,   0.1154]  tool [ 1.5744, 1.15,   -0.95]   d=2.18
trigger.step.to.stunt             mapped [ 0.0005, 0.091,   0.1154]  tool [ 0.0005, 2.2467, -0.50]   d=2.24
point.driver.side                 mapped [-0.341,  2.281,   0.626 ]  tool [-1.571,  1.15,   -0.95]   d=2.30
point.driver.onground             mapped [-1.747,  0.091,   1.179 ]  tool [-1.571,  1.15,   -0.95]   d=2.38
trigger.driver.fast               mapped [-2.1288,-0.1484,  1.3534]  tool [-1.571,  1.15,   -0.95]   d=2.70
point.passenger1.side             mapped [-0.236,  2.311,   1.5102]  tool [ 1.5744, 1.15,   -0.95]   d=3.27
EOF
```

The cross-check is mixed: 11 of the 15 land ≥ 1 m from the tool's answer (the mapping does not keep
sides or heights — a "side" point mapped 2.31 m up, `trigger.step.to.stunt` mapped at y 0.091 on the
ground), while 4 land close — `point.stunt.hood` at **0.22 m**, `trigger.stationary.stunt` 0.55 m,
and the two stunt triggers 0.79 m — and the two stunt **heights** agree (2.31 vs 2.25 m; 1.66 vs
1.53 m). So the method is defensible and the sentence is not: 15 objects do have something finer to
copy, and the one nearest match is a genuine corroboration of the front-deck anchor that the doc
never claims.

**Verdict: WEAK.** Say "70 of 85 inherit a container origin, and the 15 own positions map to 11
≥1 m / 3 within 1 m / 1 within 0.25 m of the role anchor, so they are not usable as placements" —
that is true, it is the evidence the doc already has, and it records the one useful check
(`point.stunt.hood` at 0.22 m) as a corroboration.

---

## A9 · The cockpit side is the right surface for 54 entry/exit/trigger nodes

**The result rests on:** the card's "side of the cockpit for entry" and the placement of 29 driver
objects at x −1.571 and 25 passenger objects at x +1.5744.

**Test 1 — the flank is real and not mirrored:**

```
$ python - <<'EOF'   (nearest triangle at the side points)
entry.driver      pos_m=[-1.571, 1.15, -0.95] nearest=0.0969  normal=[-0.996, 0.067, 0.061]
entry.passenger1  pos_m=[ 1.5744,1.15, -0.95] nearest=0.1001  normal=[ 0.996, 0.067, 0.062]

$ python - <<'EOF'   (the donor's own sides)
point.driver      world x -0.44   →  mapped batmobile [-0.5776, 0.5976, 0.3916]
point.passenger1  world x  0.44   →  mapped batmobile [ 0.5815, 0.5976, 0.3916]
EOF
```

Left = driver is the donor's own arrangement (the Serpente's driver points are at −x) and the same
convention as COCKPIT.md's frame (left = −x), so nothing is mirrored. The flank normals are lateral.

**Test 2 — the aperture is not on that flank:**

```
$ grep -n "canopy" Working/Translation/T8_PARTS.md
275:3. **The canopy opens by translation, not by hinge.** The canopy clips move …
146:- **verify**: Q-1 #3: canopy opens on entry (MOD-4/ANI-8). Pass = it moves 0.71 m and 11 deg …
$ grep -n "door" Research/JC3Grab/DOORS.md
13:| v0300 Serpente (civilian) | `sportsmuscle_door_f_l` | FrontLeftDoor | …
39:The donor's three `door_parts[]` entries are its two side doors and `sportsmuscle_hood_signature`
```

The donor had side doors; the Batmobile's opening is the canopy, which moves `CockPit_Mesh`
**72.481 cm and 12.494°** and would have to be driven by the `Hood` channel (T8_PARTS.md "What the
files do not give" item 3, lines 275–278: "the canopy opens by translation, not by hinge … JC3 door
parts only rotate about a hinge … can reproduce the rotation but not the lift"). The gap it opens
is above and forward of the seat, not at x ±1.57 at y 1.15. So the 54 side nodes sit on a closed
panel, and Q-1 #3's entry take (via the canopy) will animate the player through the roof line while
the interaction node it triggers is on the flank.

**Verdict: WEAK.** The card mandates the side, and the tool follows it faithfully; what is missing
is the consequence in the doc (and in the rows that will consume it): the entry node is not at the
aperture the player actually uses. This is the "behaviour before member" question applied to a
surface rather than a member, and it deserves one sentence in §6.

---

## A10 · One seat, so `interaction.seat.passenger1` is UNKNOWN

**The result rests on:** "`interaction.seat.passenger1` has no transform - the Batmobile cockpit has
one seat (COCKPIT.md §1)".

**Test.**

```
$ python - <<'EOF'   (t9_interaction.json counts/by_role)
roles: driver 29, hood 9, passenger 25, stunt 19, seat.driver 1, seat.passenger1 1, seat.stunt 1
unknown: 1  (interaction.seat.passenger1, transform null)
EOF
```

The seat row is dropped because there is one seat, while 25 passenger objects (`entry.passenger1`,
`exit.passenger1.*`, `exit.ai.passenger1.*`, `point.passenger1*`, `trigger.passenger1`,
`transition.passenger1*`) are placed on the right flank for that same non-existent seat. Either the
passenger path is dead (then it belongs with the D-9 drops, with the "one seat" reason) or a second
seat exists (then the seat row should be placed like `seat.stunt` is). The doc picks neither.

A second, related gap: Q-1 #3's checklist (line 1172) says "Walk-around interaction: driver entry
**from both sides** (WLD-3, canopy opens: MOD-4/ANI-8)", but the placement
gives the driver only the left: the right flank has passenger nodes only, and there is no
`entry.driver` on the right.

**Verdict: WEAK** (inconsistent, and it collides with a Q-1 check that the same §1 walk-around
plan and this card's own serves list (WLD-3) are written against).

---

## A11 · The output is "object id → new transform"

**The result rests on:** the card's Out line — "`t9_interaction.json` (object id → new transform)".

**Test.**

```
$ python - <<'EOF'   (INTERACTION.json names vs the delivered json)
points 85 unique 79
dupes: {'transition.passenger1': 3, 'transition.stunt': 3, 'transition.driver': 3}
EOF
$ python - <<'EOF'   (delivered transforms)
rows 85 with transform 84, distinct positions 5
(-0.0025, 0.8647, -1.0654) 1
(-1.571, 1.15, -0.95) 29
(1.5744, 1.15, -0.95) 25
(0.0005, 1.5265, -2.14) 9
(0.0005, 2.2467, -0.5) 20
EOF
```

So the "map" is a list with six duplicate keys (the three `transition.*` names appear three times
each, distinguished only by their `state`), and the 84 transforms are five points repeated: all 29
driver objects share one transform, all 25 passenger objects another. The card's Done rule ("every
object has a new transform") is met in the letter; a consumer keyed by object id cannot use the file
as a map without inventing (name, state) keys.

**Verdict: WEAK.** Either key the rows by `name` + `state` (or an index) and say so, or note in the
doc that the reader must key on the pair. This is B-05's input; it will be read by a script.

---

## A12 · Frame and units

**The result rests on:** §2's "Frame (JC3, the same one as COCKPIT.md): x lateral (left = -x), y
vertical (ground 0.020), z longitudinal, nose at -z", and metres throughout.

**Test.**

```
$ sed -n '8p' Research/BatmobileGrab/COCKPIT.md
Frame: **x = axle (left = -x), y = vertical (ground 0.02), z = longitudinal, nose at -z**.

$ python - <<'EOF'   (Working/TrueScale/stations.json)
{"scale": 0.01, "ground": 0.02, "hardpoint_x": "true"}
EOF
$ python - <<'EOF'   (t9_interaction.json)
mesh Working/TrueScale/body_lod1.rbm verts 28940 tris 20000
bbox [[-1.7531, 0.0783, -3.4218], [1.7508, 2.3667, 3.6093]]
EOF
DIM-1 (GRAB_BACKLOG §1.2): 7.026 × 3.495 × 2.271 m
```

The frame sentence is verbatim COCKPIT.md, `ground` 0.02 is `stations.json`, and the mesh bbox
(7.031 × 3.504 × 2.288) matches DIM-1 within 1.7 cm — the body is the true-scale one, in the same
space as the sockets the rest of the project uses. The `Driver` socket
(−0.0025, 0.8647, −1.0654) and its measured 27.9 mm to the cushion triangle
(normal `[0.169, 0.985, 0.02]`, i.e. the seat) sit within 4 mm of COCKPIT.md §2's "24 mm above the
cushion" (cushion ray y 0.8407).

**Verdict: HOLDS.** The one thing to keep in mind is that COCKPIT.md §2 also warns the socket's own
basis is rotated (`up_jc3 (-1,0,0)`); the tool correctly builds on world up.

---

## A13 · Yaw is derived, not decoded

**The result rests on:** §6, "Yaw is `atan2(forward.x, -forward.z)` … it is derived from the anchor
normal, not decoded from the donor".

**Test.**

```
$ python - <<'EOF'   (t9_interaction.json transforms)
entry.driver      forward [1.0, 0.0, 0.0]    yaw 90.0
point.stunt       forward [0.0, 0.0, -1.0]   yaw 0.0
interaction.seat.driver forward [0.0, 0.0, -1.0] yaw 0.0
EOF
```

The formula is stated, the classes are right (the side forward is `[-normal_x, 0, 0]`, i.e. pointing
into the car; hood/roof forward is the nose), and the donor's rotation part is the identity in every
one of the 85 world matrices (`world: "1,0,0,0, 0,1,0,0, 0,0,1,0, …"`; only the seven triggers have
a non-unit diagonal, A17), so there is no donor facing to copy. Whether an *entry*
node's forward should point into the car or out of it is not decidable from any file here — the doc
labels the value derived, which is the correct treatment.

**Verdict: HOLDS as declared.**

---

## A14 · The D-9 drop set

**The result rests on:** "D-9 is resolved **no**: hijack objects (*pull.out*, *pulled.out*) dropped".

**Test.**

```
$ python - <<'EOF'   (dropped rows)
['exit.driver.pulled.out', 'entry.driver.pull.out.onground.no.door',
 'entry.passenger1.pull.out.onground', 'exit.passenger1.pulled.out',
 'entry.passenger1.pull.out.onground.no.door', 'entry.driver.pull.out.onground']
EOF
$ grep -n "| D-9 |" GRAB_BACKLOG.md
| D-9 | … enemies pull Rico out of a moving car | … | **resolved 2026-10-28 (user): no** | …
```

Six names, all carrying `pull.out`/`pulled.out`, exactly the two prefixes the card names, and the
decision is on the record. The dropped rows keep a transform (the Drop only changes disposition),
which the doc says.

**Verdict: HOLDS.** (The one nuance: `S_PULLED_OUT_VEHICLE` also covers the *player's* forced exit;
the card scopes the drop to hijack/hijacked entries and D-9's answer was "no", so the set is
consistent with the decision, not with the state name.)

---

## A15 · The counts

**The result rests on:** "85 objects: 77 placed … 6 hijack objects dropped … `Driver` socket 1;
`interaction.seat.passenger1` UNKNOWN"; the role table 29/9/25/19/3.

**Test.**

```
$ python - <<'EOF'   (INTERACTION.json counts)
objects 85 ; by_prefix {entry 29, exit 26, interaction 3, point 8, transition 12, trigger 7}
by_class {CInteraction 3, CInteractionGraphEntry 29, CInteractionGraphExit 26,
          CInteractionGraphPointNode 8, CInteractionGraphTransition 12, CInteractionTrigger 7}
$ python - <<'EOF'   (t9_interaction.json)
rows 85 ; placed 77 ; dropped_D9 6 ; socket 1 ; unknown 1 ; in_band 77
roles: driver 29, hood 9, passenger 25, stunt 19, seat.driver 1, seat.passenger1 1, seat.stunt 1
```

3+29+26+8+12+7 = 85 and 29+26+3+8+12+7 = 85; the roles sum to 85; 77+6+1+1 = 85. The invariant
`c["placed"] + c["dropped_D9"] + c["socket"] + c["unknown"] == c["objects"]` is enforced in code.

**Verdict: HOLDS.**

---

## A16 · The body mesh is the surface to measure against

**The result rests on:** the card's "Batmobile body mesh" and the tool's
`Working/TrueScale/body_lod1.rbm`.

**Test.**

```
$ ls Working/TrueScale/
body_lod1.rbm body_lod2.rbm body_lod3.rbm body_lod4.rbm body_lod5.rbm
land_global_true.vmodc sportsmuscle_true.physicsc
```

`body_lod1` is the highest LOD present (there is no `body_lod0`), and there is no Batmobile
`.physicsc` — the only hull on disk is `sportsmuscle_true.physicsc`, the donor's, and DIM-4 records
that the collision hull "needs the writer, G2-30". So the render mesh is the only Batmobile surface
on disk, which is what the card names.

**Verdict: HOLDS with a limitation** that should travel with the rows: the interaction points are
placed against LOD1 geometry, while the surface the player's capsule will collide with in-game is
the collision hull (still the donor's; `INTERACTION.md` tabulates 3.003 m wheelbase vs the
Batmobile's 5.0289 m). When
G2-30/T-22 lands, these 84 transforms should be re-measured — the doc does not say so.

---

## A17 · A transform needs only pos / forward / up / yaw

**The result rests on:** the transform schema in `t9_interaction.json` (`pos_m`, `forward`, `up`,
`yaw_deg`), the delivered rows' lack of any scale field, and the card's Out line "object id → new
transform".

**Test.**

```
$ python - <<'EOF'   (Research/JC3Grab/INTERACTION.json, `scale` and world matrix diagonals)
scale field: [1.0, 1.0, 1.0] × 78 ; [2.65, 1.91, 2.83] × 2 ; [10.0, 10.0, 10.0] × 1
             [3.6904, 1.7762, 6.7485] × 1 ; [19.1198, 14.1098, 23.4098] × 1
             [1.9478, 1.5964, 5.1157] × 1 ; [14.32, 9.31, 18.61] × 1

trigger.driver                  scale=[2.65, 1.91, 2.83]        bm=[-1.9441, -0.0833, 0.5118]
trigger.passenger1              scale=[2.65, 1.91, 2.83]        bm=[ 1.9451, -0.0833, 0.5118]
trigger.stunt                   scale=[14.32, 9.31, 18.61]      bm=[-0.5382, 2.5494, -0.0089]
trigger.stunt.vehicle.to.vehicle scale=[19.1198, 14.1098, 23.4098] bm=[-0.5382, 2.5494, -0.0089]
trigger.stationary.stunt        scale=[1.9478, 1.5964, 5.1157]  bm=[-0.0367, 1.9805, -0.0181]
trigger.step.to.stunt           scale=[10.0, 10.0, 10.0]        bm=[0.0005, 0.091, 0.1154]
trigger.driver.fast             scale=[3.6904, 1.7762, 6.7485]  bm=[-2.1288, -0.1484, 1.3534]
```

Seven of the 85 objects are `CInteractionTrigger`s whose `scale` is a real box (up to 19.1 × 14.1 ×
23.4 m — the stunt trigger spans most of the car). All seven carry `world_source: own`, so the scale
is decoded donor data, not container inheritance. The delivered rows keep `clearance`, `measure`,
`anchor` and `transform` — and no scale, no extents, no orientation axes beyond forward/up. A
consumer that rebuilds triggers from these rows would place 19-metre volumes as points.

Two of those triggers also share a mapped position: `trigger.stunt` and
`trigger.stunt.vehicle.to.vehicle` both land on `[-0.5382, 2.5494, -0.0089]`, which is **above the
mesh's own maximum y 2.3667** — the mapped position is outside the car, another sign the mapping is
not a placement.

**Verdict: BROKEN for triggers.** Carry `scale` (mapped by the same `scale_xyz` the frames block
already computes) into the transform, or state in the doc that trigger volumes are unmodelled and
let the trigger card own them. The card's Out line does not mention scale, so the fix is a doc +
schema note plus one field in `build()`.

---

## What this challenge did not test

- **Anything in-game.** R6 forbids a launch before phase V exits; Q-1 #3 (entry from both sides,
  canopy) is the only falsifier for the side-vs-canopy question and it is still unrun.
- **The `deform`/welding data of the stunt areas** (`INTERACTION.json` `stunt_areas.weld_pairs`,
  `real_welds`, `deform_points`): T-WLD11 is `blocked` on it elsewhere; T-13 does not touch it.
- **The build's LOD0 and collision hull** (A16): not on disk for the Batmobile yet.
- **How large the trigger volumes should be on the Batmobile**: the donor's boxes are decoded (A17),
  the mapping's `scale_xyz` exists, but nothing checks the mapped size against the body.

## Reproduce

```
python Tools/scripts/t9_interaction.py --check        # A1: PASS, exit 0
python Tools/scripts/t9_interaction.py --write       # regenerates md + json (not run here)
```

The heredocs above are read-only and each prints what its section quotes; the two geometry probes
copy `t9_interaction._ray_hit` and `jc3interact.nearest_distance`'s math and add no files.

Nothing in the repo, `Builds/`, `E:/Modding/JustCause3/_grab`, `E:/Modding/ArkhamKnight/_grab` or `D:/Games` was
written, and no process was launched.
