# Assumption challenge — backlog card T-12 (moving-parts translation)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-12 card (§7, line 878),
its §12 row (line 1321), the MODLOG sections `T-12 · Moving-parts translation — intended change`
(12609), `— done` (12650), `T-12 rework — intended change` (15188) and `T-12 rework — done` (15272),
and the outputs `Working/Translation/T8_PARTS.md` + `T8_PARTS.json` + the generator
`Tools/scripts/t12_parts.py`, plus what it reads: `Research/BatmobileGrab/ANIMATIONS.json`,
`BONES.json`, `POSES.json`, `Research/JC3Grab/MOVING_PARTS.json`, `TURRET.json`, `DOORS.json`,
`PARTS_TABLE.jsonl`, `Working/Appearance/build_parts/parts_manifest.json`, `Tools/scripts/bat_assemble.py`,
and the exported key frames in `E:/Modding/ArkhamKnight/_grab/anims/keys/` (13 files, 4.2 MB for the base
package, R10 game data read-only outside the repo).

Constraints honoured: no game launched, nothing written into `D:/Games`, no archive opened, no game
file touched, no build run, nothing committed, no secrets, no `--write` on any tool, no file in the
project modified except this one.

The card's gate is **green at HEAD** — the starting point for the challenge, not the answer:

```
$ python Tools/scripts/t12_parts.py --check
PASS: 15 rows (11 cut parts, 12 with an animated joint, 4 with a shipped hinge, spins ['P-03']) |
25 BmAK row-sequence pairs (15 distinct clips) | fastest joint 1229.51 deg/s | pivots re-derived
through bat_assemble (max delta 1.3918e-05 m) | damage types ['Boat_Generic', 'Land_Generic',
'Land_Hood', 'Plane_Control_Surface', 'Train_Generic'] | internal rows ['P-02', 'P-05', 'P-13'] |
json match True, md match True                                                          EXIT=0
```

The rework already caught eight issues (schema 2 vs the loader, dropped translation lines, the
Vulcan's wrap, unchecked axis/reason, the 25-clips count, the local-vs-JC3 axis column, the six
child-bone headlines, two journal nits) — all verified fixed here. Everything below is either a
residual of those fixes or something neither pass looked at.

## VERDICT

**Five BROKEN, six WEAK, six HOLDS.** The **measurements** are the strongest part of this card and
they survive independent recomputation: the Vulcan really is 2160.0° = 6.00 turns over 3.899 s, the
peak frame step is 40.639° at dt 0.033053 s = 1229.51 °/s, no frame steps more than 180° so the
unwrap is safe (A5); the canopy really translates 72.481 cm; the 25 pairs / 15 distinct clips are
exact and each flap row reads its own side's clip (A17); the delivered JSON still loads through
`bat_assemble.load_part_spec` as an 11-part spec (A14).

What does not survive is **what the document says about those numbers**:

1. **The pivot "agreement" is a round trip, not a check** (A2). The 1.3918e-05 m delta is exactly the
   difference between `BONES.transform.offset_used` and the manifest's `offset`; recomputing with
   `offset_used` collapses it to 2.5e-07–3.9e-07 m, and the tolerance is that same offset delta plus
   1e-6. The gate therefore cannot fail and cannot detect a wrong joint or a wrong bone.
2. **The geometry table's "pivot (m, JC3)" column is not the part's pivot** for 6 of the 11 cut parts
   (A3): it prints the *child joint bone's* position, which differs from `parts_manifest.json` by
   0.131 m (front flaps) to 0.393 m (rear flaps) and 0.377 m (machine gun).
3. **"in JC3 space" means two different vectors in the same document** (A4): the table prints the
   bind-rotated world axis, the per-part bullet prints the coordinate-permuted *local* axis. For the
   four flaps the bullet says `[-0.0, 1.0, -0.0]` (vertical) where the table says
   `[-0.991, 0.016, 0.135]` (lateral) — a build following the bullet hinges the flap about the wrong
   line.
4. **The missile-hatch carrier limit is not UNKNOWN** (A7): `DOORS.json` holds the monorail
   `MissileHatch` hinge — axis `(0, 0, ±1)`, `0..150°`, `hkpLimitedHingeConstraintData`, 16 parts.
   T-12 looked only in `TURRET.json`'s 8 samples and declared it UNKNOWN.
5. **"damage types … land-first" is an alphabetical tie-break on a set that calls a train "land"**
   (A9): P-13 picks `Land_Generic` over the exact `Land_Steering_Wheel` because `sorted()[0]`, and
   P-07/P-08 get `Train_Generic` because the monorail sits under `01_land/`.

| # | assumption (stated or silent) | verdict |
|---|---|---|
| A1 | 15 rows = 11 cut parts + 4 no-part items, and the card's eight mechanisms are all present | **HOLDS** — 11/11 cut parts have a row; 8/8 mechanisms; invariants green |
| A2 | pivots "agree with BONES to 1.39e-5 m", the tolerance being BONES' own offset delta | **BROKEN** — round trip: with `offset_used` the delta is 2.5e-07–3.9e-07 m |
| A3 | the geometry table's `pivot (m, JC3)` is the part's pivot | **BROKEN** — 6 parts print the child joint, 0.131–0.393 m from the cut pivot |
| A4 | the per-part bullet's "(… in JC3 space)" is the same axis as the table's | **BROKEN** — local-permuted vs bind-rotated; the 4 flaps read vertical vs lateral |
| A5 | Vulcan = 6 turns / 2160° in 3.90 s at 1229.51 °/s; the 357.354° extent is one wrap | **HOLDS** — recomputed from the 119 key frames, 0 steps > 180° |
| A6 | P-02 is "static" (no rotation animated) | **WEAK** — it also carries a −5…20° hinge and a verify that expects pitch |
| A7 | the monorail MissileHatch hinge is not in the decoded set → limits UNKNOWN | **BROKEN** — `DOORS.json`: 0..150° about ±Z, 16 parts |
| A8 | the plane's AirBrake hinge is UNKNOWN | **HOLDS** — not in TURRET's 8 samples; MOVING_PARTS has no limits |
| A9 | damage types are `decoded (fleet)`, land carriers preferred | **BROKEN** — alphabetical `sorted(land)[0]`; "land" includes the monorail |
| A10 | "rate (BmAK anim length → deg/s)" | **WEAK** — it is peak frame speed; average/peak differs 1.51×–6.08× |
| A11 | the journal's "357.4° per spin" for the Vulcan | **WEAK** — stale number, corrected in the artifact but not in the old done entry |
| A12 | the canopy/hatch rows are moving parts | **WEAK** — `part: null`, geometry in the body; the canopy verify needs a part that does not exist |
| A13 | the canopy is fully described by `CockPit_Mesh` | **WEAK** — the same clips move `Batmobile_Nose_Mesh` 39.7–45.4 cm; the verify uses V2 numbers |
| A14 | `schema` 1 + `rows_schema` 2 keeps the file loadable as a part spec | **HOLDS** — `load_part_spec` returns 11 parts |
| A15 | no base sequence rotates the turbine; no steering bone exists | **HOLDS** — JetSMove rotates in 0 clips; 0 steering/yoke bones (nozzle caveat) |
| A16 | "4 with a shipped hinge" | **WEAK** — 4 rows over 3 distinct hinges; the cannon hinge is reused for an axially disagreeing part |
| A17 | 25 row-sequence pairs = 15 distinct clips | **HOLDS** — exact; P-11 reads the L clips, P-12 the R clips |

Counts: 6 HOLDS, 6 WEAK, 5 BROKEN.

---

## A1 — 15 rows cover the card's mechanisms and every cut part. **HOLDS**

Re-derived from the delivered JSON against the cut:

```
$ python -c "… T8_PARTS.json …"
schema 1 rows_schema 2 parts 11
rows 15  parts 11  static_rows ['P-02','P-05','P-13']  rows_with_joint 12  rows_with_hinge 4
missing cut parts: none            card mechanisms: turret, cannon, Vulcan, canopy, missile bays,
                                   fins/air-brakes all present
P-06 / P-07 / P-08 / P-13: part = null      (the card's 4 no-part items)
```

The card's part list is turret, cannon, Vulcan, turbine, canopy, hatches L/R, air-brakes/fins, yoke
— eight mechanisms; the rows are P-01…P-15 with the two pods (P-14/15) added for the shells. Every
one of the 11 cut parts in `parts_manifest.json` has a row (`invariants` also fails on a missing
one). The rework's own invariants are the reason this is checkable at all. **HOLDS**, and this is
the half of the Done clause the card can defend outright.

## A2 — "pivots re-derived through `bat_assemble.pivot_point`, max delta 1.3918e-05 m = BONES' own
offset delta; the tolerance is that number, not a guessed one". **BROKEN**

The comparison in `build()` is:

```python
derived = bat_assemble.pivot_point(b["bind"]["world_position_cm"], scale, offset)   # manifest offset
stored  = b.get("pivot_jc3_m")                                                      # BONES' own value
delta   = max(abs(a - c) for a, c in zip(derived, stored))
pivot_tolerance_m = round(offset_delta + 1e-6, 12)        # 1.3462e-05 + 1e-6
```

Both numbers come from the same bind position through the same transform; they can only differ by
the offset used. Test — recompute the same three pivots with each offset:

```
offset_computed [4.77e-07, 0.022231445, 0.154284012]
offset_used     [-4.77e-07, 0.022231445, 0.15429744]      offset_delta_m 1.3462e-05
Batmobile_Rig_Weapons_Turret_Root
   with offset_computed  delta 1.3678e-05
   with offset_used      delta 3.93e-07
CockPit_Mesh
   with offset_computed  delta 1.3178e-05
   with offset_used      delta 2.5e-07
Batmobile_Rig_Aero_Flap_L_B
   with offset_computed  delta 1.3708e-05
   with offset_used      delta 2.8e-07
```

So the 1.39e-05 m is the **offset difference**, the tolerance is that difference **plus 1e-6**, and
the check passes with a built-in ~4 % margin no matter which bone or joint the row names. It cannot
fail, and it cannot detect the thing that matters — whether the named bone is the joint. (The rework's
tamper test renamed a bone to a non-existent name, which fails on lookup, not on the delta.) The §12
sentence also equates two different numbers: 1.3918e-05 (the max delta) is not `offset_delta_m`
1.3462e-05. **BROKEN** as a validation claim; the values themselves are fine.

## A3 — the geometry table's `pivot (m, JC3)` column is the part's pivot. **BROKEN**

The renderer picks the **joint** bone's pivot for the per-part geometry row:

```python
pv = r["pivots"].get(joint.bone) or r["pivots"].get(joint.part_pivot_bone) or first
L.append(f"| `{r['part']}` | {parent} | `{pivot_bone}` | {faces} | {piv} |")
```

For six rows the joint is a child bone, so the table prints a point that is not the part's cut pivot
(`parts_manifest.json`'s `pivot_m`, which is what B-02 cut the geometry about):

```
id    part                        printed (md)                manifest pivot_m             delta m
P-03  batmobile_machine_gun       -0.407, 1.619, 0.810        -0.092, 1.413, 0.810          0.377
P-04  batmobile_riot_suppressor    0.389, 1.451, 0.410         0.388, 1.563, 0.560          0.187
P-09  batmobile_aero_flap_l_f     -1.155, 1.358, -0.798       -1.208, 1.367, -0.918          0.131
P-10  batmobile_aero_flap_r_f      1.155, 1.358, -0.798        1.208, 1.367, -0.918          0.131
P-11  batmobile_aero_flap_l_b     -1.200, 1.852, 1.641        -1.209, 1.800, 1.251          0.393
P-12  batmobile_aero_flap_r_b      1.200, 1.852, 1.640         1.209, 1.800, 1.251          0.393
P-01  batmobile_turret             0.000, 0.876, 0.333         0.000, 0.876, 0.333          0.000
```

Even worse for the machine gun, the same row pairs the *bone* `…Machine_Gun_Root` (true pivot
−0.092, 1.413, 0.810) with the *position* of its grandchild `…Machine_Gun_02`. A build that hinges
the cut part at the printed column swings the flap 13–39 cm off its cut pivot, i.e. the flap
translates instead of hinging. The behaviour table has the same column, but there it is labelled
`pivot (m)` under `BmAK joint bone`, which is defensible; the *geometry* table's per-part header is
not. **BROKEN** (documentation, 6 of 11 rows; the underlying joint positions are right).

## A4 — the per-part bullet's "(… in JC3 space)" is the table's `axis (JC3 space)`. **BROKEN**

Two different vectors carry the same label:

| source | value for P-09 |
|---|---|
| behaviour table, `axis (JC3 space)` | `[-0.991, 0.016, 0.135]` = `joint.axis_world_jc3` (local axis through the bind rotation) |
| per-part detail bullet, "turns about its local +Z (`[… ] in JC3 space`)" | `[-0.0, 1.0, -0.0]` = `joint.axis_jc3` (the same local axis only coordinate-permuted) |

`axis_jc3` is just `to_jc3_rot([0,0,1])`; `axis_world_jc3` applies the bone's bind quaternion. They
coincide for every row whose bind rotation is axis-aligned — the turret, gun, suppressor, canopy,
hatches and pods — which is why the flagship rows look consistent, and they diverge only where the
bind rotation is not:

```
P-01 turret      axis_jc3 [-0.000, 1.000, -0.000]  axis_world [-0.0002, 1.0000, -0.0001]
P-04 suppressor  axis_jc3 [-0.000, 0.000, -1.000]  axis_world [ 0.0000, -0.0001, -1.0000]
P-09 flap L-F    axis_jc3 [-0.000, 1.000, -0.000]  axis_world [-0.9907, 0.0163, 0.1351]   ← 90° apart
P-10 flap R-F    axis_jc3 [-0.000, 1.000, -0.000]  axis_world [-0.9907, -0.0164, 0.1351]  ← 90° apart
P-11 flap L-B    axis_jc3 [-0.000, 1.000, -0.000]  axis_world [-0.9947, -0.0000, 0.1032]  ← 90° apart
P-12 flap R-B    axis_jc3 [-0.000, 1.000, -0.000]  axis_world [-0.9946, 0.0029, 0.1040]   ← 90° apart
```

The `axis_agrees` check uses `axis_world_jc3` and is right; the bullet that a human or a small model
reads is the vertical one. The rework fixed the table (issue 6) but left the bullet. **BROKEN** for
the four flap rows: a hinge built on the bullet's axis is perpendicular to the real one.

## A5 — the Vulcan is 6.00 turns / 2160.0° in 3.90 s at 1229.51 °/s, and 357.354° is one wrap.
**HOLDS (strongest measurement in the card)**

Recomputed from the raw key file, independent of `t12_parts.py`:

```
sequence Batmobile_V2_ChainGun_Spin, bone Batmobile_Rig_Weapons_Machine_Gun_02
frames 119   dt 0.033053 s   first 0.003°   last 0.003°   min -179.493   max 177.861
span 357.354°   sum|short-way steps| 2160.0°   turns 6.0   net 2160.0
max step 40.639°  -> 40.639/0.033053 = 1229.51 °/s
steps above 180°: 0        all steps same sign: True
```

Two independent reasons the number is safe: every step is 40.6° at most, so the ±180° short-way rule
cannot reverse a step (a step must exceed 180° to be mis-read), and the channel is closed
(first = last = 0.003°) with a monotonic sign, so the sum is a winding number — 6 exactly. The clip's
`sequence_length` is 3.933333 s at `psa_rate` 30.254236 while the exported frame times end at 3.90028 s;
the doc uses the sample duration, which is the one that matches the 119 keys (one frame apart).
**HOLDS**, including the `is_spin` flag and the "±180° extent, not a limit" wording.

## A6 — P-02 is a static row. **WEAK**

Three cells of the same row disagree:

```
joint              null                      → summary.static_rows ['P-02','P-05','P-13']
hinge              mediumtank_cannon, axis [1,0,0], -5.0..20.0°, Land_Generic
verify             "Q-1 #4: cannon pitch limits. Pass = the barrel stops at the carrier's own
                    -5..20 deg and does not enter the hull, 3/3"
static_reason      "no rotation is animated; the bones translate (…Barrrel_02 53.376 cm in
                    Batmobile_V2_Cannon_Fire) and a hinge cannot reproduce translation"
```

The data is solid — `removed_tracks` for the clip marks `Heavy_Cannon_Barrel_01` and
`Barrrel_02` as `rot`, so the rotation channel was dropped as constant and only the 36.1/53.4 cm
recoil remains. But the row simultaneously says "static", ships a −5…20° hinge, and asks a Q take to
observe pitch. A build card cannot do both, and `BUILD_BATCHES.md` lists ANI-2 as `documented`
(not carried, not omitted), so nothing else decides it. **WEAK**: the measurement is right, the
disposition is ambiguous — the "static" verdict should be a named omission of the *pitch*, with the
hinge kept only as a carrier note.

## A7 — "the monorail's `MissileHatch` hinge is not among TURRET's 8 samples, so their carrier limits
stay UNKNOWN". **BROKEN**

`DOORS.json` (G2-15, the door card this card's own `In:` list names) decoded exactly that hinge:

```
/samples[2]/door_parts[0]  {"behaviour":"MissileHatch","constraint":0,
   "hinge":{"axis":[0,-0,-1],"class":"hkpLimitedHingeConstraintData","max_deg":150.0,
            "min_deg":0.0,"pivot":[-1.35,3.35,-6.117],"size":304},
   "name":"monorailmissilecar_missile_hatch_l_01","parent":7}
… 16 rows (8 L at axis -Z, 8 R at +Z), all 0 .. 150 deg, entity v5603_train_urga_monorailmissilecar
$ grep -n "MissileHatch" Research/JC3Grab/DOORS.md
21:| v5603 monorail missile car | `monorailmissilecar_missile_hatch_l_01` | MissileHatch | (0,-0,-1)
    | 0 .. 150 deg | (-1.35, 3.35, -6.117) | 7 |
```

So P-07/P-08's `carrier limits` cell ("no hinge") and UNKNOWN #4's "UNKNOWN" are both wrong: the
carrier is a 0..150° limited hinge about the longitudinal axis, i.e. 10× the BmAK span (15°), which
would not constrain the motion and is what a build needs. The sentence searched `TURRET.json` only,
while `DOORS.json` was in the card's `In:` list. **BROKEN**, but the consequence is small: the limit
to write is the animation's 15°, and the carrier's 150° merely does not bind.

## A8 — the plane's `AirBrake` hinge is UNKNOWN. **HOLDS**

The other half of the same UNKNOWN sentence is right, and I tried to break it:

```
TURRET.json samples (8): v0201 mediumtank, v0202 bavariumtank, v0603 smalltank, v0200 apc,
  v0600 armoredjeep, v0504 technicaljeep, v0300 donor, v0604 buggy      — no plane
MOVING_PARTS.json AirBrake: {"channel":"hinged","variable":"air_brakes_T","parts":3,
  "chassis":1,"chassis_list":["v4602_plane_urga_fighterbomber"],"classes":["CAirPlane"],
  "proof":"unproven-on-CCar"}      — no axis, no limits, no pivot
grep -rn "fighterbomber" Research/JC3Grab/*.json → FEATURE_CENSUS only (three behaviour lists)
```

No decoded file carries the fighter-bomber's flap constraint, so UNKNOWN is the honest answer and
the row correctly quotes only the animation span (blade 20.0°/30.0°, piston 25.8°/54.8°).
**HOLDS.**

## A9 — damage types are "`decoded (fleet)` — `PARTS_TABLE.jsonl`'s `dt` per behaviour, land
carriers preferred". **BROKEN**

The rule is `sorted(v["land"] or v["all"])[0]` — the **alphabetically first** value of a set whose
"land" test is `"/01_land/" in entity`:

```
P-13 SteeringWheel   land ['Land_Generic','Land_Steering_Wheel']  → chosen 'Land_Generic'
P-07 MissileHatch    land ['Train_Generic']                      → chosen 'Train_Generic'
P-09 AirBrake        land []                                     → chosen 'Plane_Control_Surface'
P-14 missile pod     land []  all []                             → inherited from P-07 ('Train_Generic')

Train_Generic parts in the fleet: 1 entity — 01_land/v5603_train_urga_monorailmissilecar
SteeringWheel dts in the fleet:    {'Land_Generic','Land_Steering_Wheel','Boat_Steering_Wheel'}
```

Two errors of description. "Land preferred" is satisfied by a **train** type because the monorail
lives under `01_land/`, so P-07/P-08/P-14/P-15 carry a train damage type on a car. And the exact
value the behaviour has (`Land_Steering_Wheel`) is passed over for the generic one because
`Land_Generic` sorts first. Neither will break the game (the damage type selects a part-table
channel), but the row says "preferred", and preference is alphabetical. **BROKEN** as a method
claim; the values are defensible except `Train_Generic` on a car.

## A10 — "rate (BmAK anim length → deg/s)". **WEAK**

The card's method implies travel ÷ length. The generator stores the **peak** frame-to-frame speed
(`max |Δ| / dt`), and the doc says "at up to", so it is honest — but the two quantities are far apart
and the headline sentence mixes them:

```
id   span     travel   duration   peak      average   peak/avg
P-01 120.000  250.00   2.567      174.05     97.39     1.79
P-03 357.354 2160.00   3.900     1229.51    553.85     2.22
P-04  89.999   90.00   1.734      315.39     51.90     6.08
P-06  12.494   13.09   0.469      136.09     27.90     4.88
P-09  25.817   25.82   0.801       48.70     32.23     1.51
```

P-04 is the clearest case: 90° in 1.734 s is 51.9 °/s on average, and the row's rate cell says
315.39 °/s — 6.08× higher. The Vulcan sentence "travels 2160° = 6.00 turns over 3.90 s at up to
1229.51 °/s" invites 2160/1229.5 = 1.76 s, not 3.9 s. **WEAK**: the number is real, the label
("rate") is not the card's definition, and the average is nowhere in the doc.

## A11 — the journal's Vulcan figure. **WEAK**

The old `T-12 · … — done` table still reads:

```
| Vulcan | …_Machine_Gun_02 | +X local / −Z vehicle | 357.4° per spin | 1229.5 °/s (≈205 rpm) | …
```

357.4° is the *wrap extent*, i.e. exactly the artefact the rework's issue 3 removed from the
artifact. The rework corrected two journal nits (the 262-line count, `Land_Selector`) and left this
one; MODLOG is append-only, so a reader of the done section alone gets one wrap per spin.
**WEAK** (R14 accuracy; §12 and the artifact are right).

## A12 — the canopy and hatch rows are moving parts. **WEAK**

Four rows have `part: null`; the JSON also says so in the LOD cell:

```
P-06 canopy   part null  lod_policy "not a separate part - geometry stays in the body/pod shell"
P-07/08 hatch part null  lod_policy same
P-13 yoke     part null  lod_policy same, and no bone
```

Yet P-06/P-07/P-08 carry a joint, a hinge and a verify that expects movement:

```
P-06 verify  "canopy opens on entry (MOD-4/ANI-8). Pass = it moves 0.71 m and 11 deg without
              intersecting the roof, and closes on exit, 3/3"
```

With the canopy geometry inside the static `body` part there is nothing to hinge; ANI-8/MOD-4 cannot
pass until B-02 cuts a canopy part. UNKNOWN #4 says exactly this for the **hatches** ("a separate
hatch part needs a face-level re-cut before `MissileHatch` can move it") but UNKNOWN #3 talks about
the canopy as if a `Hood`-driven canopy part existed. The summary's "12 with an animated joint"
counts three rows that cannot move. **WEAK**: the data is right, the deliverability statement is
incomplete and asymmetric.

## A13 — the canopy is fully described by `CockPit_Mesh`, and the verify's numbers belong to it.
**WEAK**

The same open/close clips move a second bone 40 cm:

```
Cockpit_Close              CockPit_Mesh 72.4813 cm   Batmobile_Nose_Mesh 41.0135 cm
Cockpit_Open               CockPit_Mesh 72.3771 cm   Batmobile_Nose_Mesh 39.6914 cm
Batmobile_V2_Cockpit_Close CockPit_Mesh 71.0094 cm   Batmobile_Nose_Mesh 45.3528 cm
Batmobile_V2_Cockpit_Open  CockPit_Mesh 71.0094 cm   Batmobile_Nose_Mesh 45.3528 cm
```

The row's bone list is `[CockPit_Mesh]` and the nose is not mentioned, so the mechanism the row
describes is half the mechanism the clip animates (the nose panel slides 40–45 cm as the canopy
lifts). Separately, the row quotes the union max (72.481 cm, 12.494°) while its verify asks for
"0.71 m and 11 deg" — the V2 clips' own 71.0094 cm / 11.227°. Two clips, two numbers, no statement of
which one the build should reproduce. **WEAK** (coverage + which-clip ambiguity).

## A14 — `schema` 1 + `rows_schema` 2 keeps the file loadable as a `bat_assemble --parts` spec.
**HOLDS**

```
$ python -c "import bat_assemble; spec=bat_assemble.load_part_spec('Working/Translation/T8_PARTS.json')"
load_part_spec OK; parts: 11
$ python -c "… T8_PARTS.json …"
schema 1 rows_schema 2 parts 11
```

This was the rework's issue 1 and it is genuinely fixed: the behaviour rows sit under `rows`, the
`parts` array still has only name/parent/pivot_bone/bone_roots, and the consumer accepts it.
**HOLDS.**

## A15 — no base-package sequence rotates the turbine, and no steering bone exists. **HOLDS**

```
JetSMove rotation spans over all 37 base-package sequences: 0
BONES.json: 180 bones; names containing 'steer' 0, 'yoke' 0; 40 'Wheel' bones (all suspension/road:
  SUSP1_Wheel_Front_Left, Wheel_Parent_F_L, Wheel_Frnt_Left_Fan, Batmobile_L_F_Wheel_Armour …)
COCKPIT.md: the hand box |x| < 0.17, y 1.00..1.30, z -1.60..-1.10 holds 4 faces of any material
anim tracks with a steering-ish bone: none
```

So P-05's "no rotation is animated" and P-13's "no bone carries this part" are true. Two caveats worth
recording rather than counting as failures: (a) the **nozzles** are descendants of the part's root
(`Nozzle_005 → Jet_Root → JetSMove → Chassis`) and they rotate up to 22.18° in
`Batmobile_V2_Tank_Spread_Close` — 234 nozzle spans > 0.5° exist, and the row's `prefix:JetSMove`
filter never sees them, so "the jet part has no animated joint" is true of the pivot bone only;
(b) the sentence "the spin itself is driven by `engine_rpm` (code, not an animation)" is an inference
about Arkham's code that no file in this card shows — `engine_rpm` is JC3's `EngineRotatingPart`
variable, not a BmAK channel. **HOLDS** on the measured claims; the code attribution is the kind of
thing the project otherwise marks UNKNOWN.

## A16 — "4 with a shipped hinge". **WEAK**

The four rows resolve to three distinct hinges:

```
P-01 mediumtank_turret   v0201 mediumtank   -179..179 about +Y   axis_agrees True
P-02 mediumtank_cannon   v0201 mediumtank     -5..20  about +X   (joint null → axis_agrees None)
P-04 mediumtank_cannon   v0201 mediumtank     -5..20  about +X   axis_agrees False
P-06 sportsmuscle_hood   v0300 donor          0..70   about +X   axis_agrees True
```

"4" is a row count, not four carriers, and the one hinge used twice is used for a part whose measured
axis is perpendicular to it (the row says DISAGREES). P-02 carries a hinge for a part it calls static
(A6). The number is not wrong so much as uninformative: `4` over `3 distinct`, one reused against the
data. **WEAK.**

## A17 — 25 row-sequence pairs = 15 distinct clips, and each row reads its own side. **HOLDS**

```
P-01 1  P-03 1  P-04 2  P-06 5  P-07 2  P-08 2  P-09 2  P-10 2  P-11 2  P-12 2  P-14 2  P-15 2
pairs 25   distinct 15
P-09 L clips  Batmobile_V2_Aero_Flap_L_Down/Up
P-10 R clips  Batmobile_V2_Aero_Flap_R_Down/Up
P-11 L clips  (left rear)      P-12 R clips  (right rear)
```

I checked the mirror worry — each flap clip animates only its own side (the L clip contains L bones
only, the R clip R bones only, with the blade sign flipped: L-F 0…+20.01 vs R-F −20.01…0) — so P-12
borrowing the L clip would have been a real error, and it does not. The four hatches/pods sharing
`Missles_Up/Down` is correct (one clip animates both L and R mid-bones: 10.8658 / 10.8634 cm).
**HOLDS**, exact.

---

## What the card gets right, and should keep

- The key-frame measurements are genuinely measured: 119 keys, real dt from `frame_times_s`, no
  assumptions about fps, and the wrap is handled with a proof (no step > 180°, closed, monotonic).
- The generator is the only writer and `--check` re-derives both artifacts byte for byte; the six
  rework invariants (schema, loadability, axis presence, static reason, spin travel, sequence text)
  are the right ones.
- The child-bone disclosure (issue 7) is now honest and gives both the part bone's own span/rate and
  the child joint's — which is exactly what exposed A3 (the geometry table still mixes them).
- Refusing to invent: the AirBrake limit, the hatches' missing part, the canopy's translation and
  the pivot's rpm-driven spins are all recorded as UNKNOWN/gaps rather than filled.

## What a rework would have to change (smallest set, generator only)

1. Geometry table: print the part's `parts_manifest.json` pivot (and keep the joint pivot in the
   behaviour table, where its header already says `BmAK joint bone`). 6 rows change.
2. Per-part bullet: print `axis_world_jc3` (or label the parenthetical "local +Z in JC3 axes") — 5
   rows read wrong today.
3. Pivot tolerance: compare against a *different* source (e.g. the manifest's part pivot, or the
   joint bone's bind position vs the hinge's shipped pivot) and drop the `offset_delta + 1e-6`
   identity; state what the check can and cannot catch.
4. P-07/P-08: fill `carrier limits 0..150° (±Z, hkpLimitedHingeConstraintData)` from `DOORS.json`
   and correct UNKNOWN #4.
5. P-13: choose `Land_Steering_Wheel` (exact behaviour) over `sorted(land)[0]`, and say in P-07/08
   that `Train_Generic` is the only carrier (a train), not a land preference.
6. P-02: either a `blocked`/omitted pitch with the hinge as a carrier note, or a moving row — one
   disposition, not three.
7. P-06: record that a canopy part must be cut (as the hatches already say), and name which clip the
   verify's 0.71 m / 11° belongs to.

## Commands run (all read-only)

```
python Tools/scripts/t12_parts.py --check
python -c "import bat_assemble; bat_assemble.load_part_spec('Working/Translation/T8_PARTS.json')"
python -c "… T8_PARTS.json …"                       (rows, summary, pivots, joints, damage types)
python -c "… parts_manifest.json vs BONES.json …"   (part pivot vs bone pivot, 16 entries)
python -c "… bat_assemble.pivot_point with offset_used / offset_computed …"
python -c "… TURRET.json samples; DOORS.json MissileHatch; MOVING_PARTS AirBrake …"
python -c "… PARTS_TABLE.jsonl Train_Generic / MissileHatch / SteeringWheel dt …"
python -c "… E:/Modding/ArkhamKnight/_grab/anims/keys/Playable_Batmobile_SF__Batmobile_V2_Pose_States.json …"
        (ChainGun_Spin 119 frames, travel/rate recomputed; flap L/R tracks; JetSMove spans)
grep/sed over T8_PARTS.md, MODLOG.md, GRAB_BACKLOG.md §12, BUILD_BATCHES.md, COCKPIT.md
```

No `--write`, no game, no `D:/Games`, no build, no commit.
