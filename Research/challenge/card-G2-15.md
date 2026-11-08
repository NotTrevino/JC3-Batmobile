# Assumption challenge — card G2-15 · Door-part animation (canopy, missile hatches)

Written 2026-10-30. Read-only review: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified; the only file written is this one. No game was launched,
nothing was written to `D:\Games`, nothing was committed.

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-15 card, the §12 row (line 1298),
`MODLOG.md` §"G2-15 · Door-part animation — intended change" (9781) and §"— done" (9803), and the
outputs: `Research/JC3Grab/DOORS.md` (155 lines), `DOORS.json`, `Tools/scripts/jc3doors.py`.
Cross-checked against `TURRET.json` (G2-13's independent decode of the same medium-tank hatch),
`WEAPON_WIRING.jsonl` / `PARTS_TABLE.jsonl`, and the reader's own source.

**Card as written:** decode door members (hinge axis, open angle, speed, which interaction opens
it, whether weapons fire opens `MissileHatch`). Done: (a) can a door hinge about a transverse axis
(canopy tilting forward)? (b) what opens a `MissileHatch`? (c) does the driver's entry animation
open the driver door part?

---

## VERDICT

**The hinge decode and the census are sound and independently corroborated; the three answers are
honest about inference; two negative/counting sentences are wrong and the entry-path table hides a
state that contradicts its own binary.**

```
$ python Tools/scripts/jc3doors.py --check
PASS: 4 samples, 224 door rows / 220 hinged / X 60, both entry paths 21            EXIT=0
```

Re-derived from `DOORS.json`:

```
census: door_rows 224 | with_hinge 220 | limited 220 | other_classes {} | modules 78 | modules_with_doors 56
by_axis: {"X (transverse)": 60, "Y (vertical)": 132, "Z (longitudinal)": 28}
sum of by_behaviour rows: 224 | axis sums from by_behaviour: {'X': 60, 'Y': 132, 'Z': 28}
no_hinge: privatepropeller_wing_cl1/cr1, smallfloatprop_wing_l/r  (constraint -1)
```

Everything sums, every hinged row is a `hkpLimitedHingeConstraintData`, and the medium-tank hatch
is decoded identically by two independent tools (`DOORS.json` 0..130 at (-0.485, 2.921, 1.479) vs
`TURRET.json` constraint 1: 0..130 at [-0.4848, 2.921, 1.4785]). Answers (a) and (b) are correctly
labelled: (a) is a data answer with working examples, (b) is called an inference.

What does not survive:

| # | assumption | verdict |
|---|---|---|
| 1 | "none oblique" axes | **BROKEN sentence** — the doc's own examples include a hatch 2.3° off X; the census buckets it to "X" |
| 2 | the MODLOG's list of X-axis users | **BROKEN count** — lists 58 of 60 (two centre doors missing) |
| 3 | "a door is three pieces" | **WEAK** — true for 220 of 224 rows; the 4 exceptions are disclosed |
| 4 | X = transverse, Y = vertical, Z = longitudinal | **HOLDS** — three independent geometric patterns agree |
| 5 | degrees from radians, and the pivots | **HOLDS** — cross-checked against G2-13's raw-radian decode |
| 6 | "nothing in the entity opens the hatches" | **WEAK** — the search is name-equality; object-id refs are invisible, and the same weapon carries two unresolved ones |
| 7 | "the trigger is code-side" (b) | **HOLDS as labelled** — stated as inference, not decoded |
| 8 | entry paths: 21 both / 0 door-only / 4 no-door-only / 30 neither | **WEAK** — "neither" hides the medium tank's `S_ENTER_DRIVER_VEHICLE` and the APC's 10 other entry nodes; the md table omits the 4th sample |
| 9 | 0 animation members ⇒ the swing is not authored | **WEAK** — the check counts only `.ban/.anim/.sab`, and only inside the entity container |
| 10 | speed is absent everywhere | **WEAK/UNKNOWN** — correct label for what was read, but a negative over 78 modules and 4 entities |
| 11 | the census is fleet-wide | **WEAK by declaration** — 78 of 233 modules, 55 of 233 graphs (stated in Limits) |
| 12 | `--check` + tamper test proves the decode | **WEAK** — same code both sides; the real independent evidence is the TURRET.json agreement (§5) |

**Bottom line:** G2-15's data is good and the three answers are usable. Fix two sentences (1, 2),
scope two negatives (6, 10), and put the medium tank's row — with its `driver_enter_state: true` —
into the entry table (8). No re-decode needed.

---

## 1. "None oblique" axes

**Why the card rests on it.** MODLOG, census paragraph: *"By axis: **60 X (transverse)**, 132 Y
(vertical), 28 Z (longitudinal), none oblique."* A port copies an axis; if the real axis is tilted,
copying the bucket is wrong.

**Test.** `DOORS.json` keeps the raw axis per sample row. Scan the transverse list for any axis
that is not within 0.01 of a unit vector:

```
$ python - <<'EOF'   # DOORS.json census.transverse
transverse rows: 12 | non-unit axes: 1
   bavariumtank_vehicle_parts.vmodc bavariumtank_hatch [0.999, -0.04, 0.0]
```

And the same value is printed in the doc's own examples table:

```
| `bavariumtank_vehicle_parts.vmodc` | `bavariumtank_hatch` | FrontLeftDoor | (0.999, -0.04, 0) | 0 .. 130 deg |
```

`-0.04` on the y component is 2.3° of tilt — the same 0.9992/−0.0398 axis G2-13 prints for that
hatch in `TURRET.json`. Other rows are mildly tilted too (`apc_door_r` (0.001, −1, 0.002)).

**Verdict: BROKEN sentence.** "None oblique" is false in the doc's own table. The bucketing is
defensible for the *count* (every axis is dominantly one of X/Y/Z), but the count sentence should
read "every axis is within 2.3° of a principal axis; `bavariumtank_hatch` is the only visibly tilted
one", and a port should take the raw vector, not the bucket.

---

## 2. The MODLOG's list of X-axis users

**Why the card rests on it.** MODLOG (a): *"X-axis users are the hoods (26/26 rows), `TurretDoor`
(2/2), `CargoBayDoor` (5/5), 19 of 20 `Trunk` rows, 5 of 55 `FrontLeftDoor` rows and 1 `RearDoor`."*

**Test.**

```
$ python - <<'EOF'   # DOORS.json census.by_behaviour, X counts
Hood 26 | TurretDoor 2 | CargoBayDoor 5 | Trunk 19 | FrontLeftDoor 5 | RearDoor 1
sum = 58      census by_axis X = 60
remaining X rows: CenterLeftDoor 1, CenterRightDoor 1
```

The two missing behaviours are in the same table (`CenterLeftDoor {X:1,Y:3}`, `CenterRightDoor
{X:1,Y:5}`); the MODLOG enumeration simply omits them.

**Verdict: BROKEN count** (58 listed, 60 actual). The generated `DOORS.md` table is right; only the
MODLOG prose is short. Small, but it is the sentence a later session will quote for "what uses a
transverse hinge".

---

## 3. "A door is three pieces"

**Why the card rests on it.** DOORS.md's opening: *"A door is a behaviour name …, an entry in the
parts module's `door_parts[]` … and a `hkpLimitedHingeConstraintData` in `.physicsc`."*

**Test.**

```
$ python - <<'EOF'   # DOORS.json
door_rows 224 | with_hinge 220 | limited 220 | other_classes {}
no_hinge: [{constraint: -1, module: privatepropeller_vehicle_parts.vmodc, part: privatepropeller_wing_cl1}, … ×4]
```

Four rows carry a door behaviour with no constraint at all — two `privatepropeller_wing_*` and two
`smallfloatprop_wing_*`. The doc discloses this in §2 ("4 door rows have `constraint_index` -1 and
therefore no hinge at all (propeller-wing parts with a door behaviour)"), and the validation
asserts "every door part with a constraint is a limited hinge (or is listed as an exception)".

**Verdict: WEAK.** The three-piece rule is a rule with a stated 4-row exception class, which is
acceptable; the opening sentence reads as unconditional and could say "220 of 224". Note also that
the four exceptions are *wings* carrying a wing behaviour, i.e. the array is not door-only — worth
one clause in the definition.

---

## 4. X is transverse, Y is vertical, Z is longitudinal

**Why the card rests on it.** The whole of answer (a) is phrased in these labels: "60 of the 220
hinged door parts … rotate about X — hoods, roof hatches and canopies; 132 about Y (side doors)".

**Test.** Three independent geometric patterns in the same json:

```
donor side doors   sportsmuscle_door_f_l  pivot x −1.018, axis (0,−1,0)   # left/right pair, vertical hinge
donor hood         sportsmuscle_hood_signature pivot z −0.848, axis (1,0,0)  # front part, lateral hinge
monorail covers    hatch_l/r_01…08        pivot x ±1.35,  axis (0,0,∓1)    # side bay covers, fore-aft hinge
medium-tank hatch  mediumtank_hatch       pivot (−0.485, 2.921, 1.479), axis (1,0,0)
```

Parts separated in x hinge about Y (a side door swings on a vertical axis); a front hood/roof hatch
hinges about X (tilts fore-aft); the monorail's side covers at x ±1.35 hinge about Z (open outward
about a fore-aft axis). The labels are consistent with the geometry in all three cases, and the
same convention is used independently in `TURRET.md` (turret yaw about +Y at the ring).

**Verdict: HOLDS.** The axis naming is not asserted from a file header; it falls out of the pivots
and the part families.

---

## 5. Degrees from radians, and the pivot values

**Why the card rests on it.** Every limit a port copies (`0..80`, `0..70`, `0..100`, `0..130`,
`0..150`) and every pivot is a converted value.

**Test 1 — the same object, two tools.** G2-13 decoded the medium tank's parts with its own reader
and kept both radians and degrees:

```
$ python -c "…TURRET.json…"
(1, [-0.4848, 2.921, 1.4785], 0.0, 130.0)      # max_rad 2.268928
$ grep "mediumtank_hatch" Research/JC3Grab/DOORS.md
| v0201 medium tank | `mediumtank_hatch` | FrontLeftDoor | (1, 0, 0) | 0 .. 130 deg | (-0.485, 2.921, 1.479) | 26 |
```

130° = 2.268928 rad exactly, and the pivots agree to the third decimal. Two independently written
readers landing on the same hinge is the strongest check in this card.

**Test 2 — the json does not keep radians.**

```
$ python -c "…DOORS.json samples[0].door_parts[0]…"
{"axis": [0.0, -1.0, 0.0], "class": "hkpLimitedHingeConstraintData", "max_deg": 80.0, "min_deg": 0.0, "pivot": [-1.018, 0.622, -0.771]}
```

No `*_rad` here, so G2-15's own output cannot prove its conversion — it leans on G2-13's.

**Verdict: HOLDS**, with one observability note: keep `min_rad`/`max_rad` as `TURRET.json` does, or
a future reader has to re-derive the conversion through another card.

---

## 6. "Nothing in the entity opens the hatches"

**Why the card rests on it.** Answer (b): *"**Nothing in the entity opens them.** No object other
than `CPartProp` names a hatch part; there is no interaction entry for a hatch, no attached effect
on one, and no member on the weapon that names a door."*

**Test 1 — reproduce the name scan.** The tool's check is literal string equality between a
property value and a hatch part name:

```python
hatch_names = {d["name"] for d in rec["door_parts"]}
for o in objs:
    if o.cls == "CPartProp":
        continue
    for k, v in o.props.items():
        if v in hatch_names:
            refs.append({"class": o.cls, "name": o.name, "prop": k})
```

```
$ python -c "…DOORS.json monorail…"
hatch_refs_outside_part_prop: []
weapon_components: ['CTurretWeaponComponent']
```

So "no object **names** a hatch" is true and reproducible.

**Test 2 — what a name scan cannot see.** The monorail's only weapon carries a
`CTurretWeaponComponent` (the fleet's only one — see the G2-13 report) whose properties are almost
all unnamed object references:

```
"id:A956FDF3": "86D436D5=FFFF47F4", "id:C71EB86F": "01E34D70=FFFF4E63",
"id:569538FC": "500", "id:9CE47505": "500", "id:B912E42A": "500", "id:CE02A3EF": "500", "id:FF777489": "45", …
```

An object-id reference to a hatch would not match a name, and the component has two of them
unresolved. Resolving them needs the entity's `.epe` objects, which live in the raw cache outside
this repo (I did not read it). The same is true of the weapon object's own `id:B5AE7986`/
`id:F30CCB1C` refs.

**Verdict: WEAK.** "No object names a hatch" HOLDS and is exactly what the tool proves. "Nothing in
the entity opens them" is a stronger claim than a name scan can support, and this particular entity
is the worst case for it — it is the one with an unnamed-ref-heavy turret component. The honest
sentence: "no object *named* link exists; the only unresolved refs are on the turret component and
were not chased".

---

## 7. "The trigger is code-side" (answer b)

**Why the card rests on it.** §3 ends: *"the opening is decided in code (almost certainly on fire,
given the `Internal*` fire positions and the 150 deg travel) - that inference is not in the files."*
The §12 row repeats "trigger is code-side".

**Test.** The basis is present and checkable: six fire points named `InternalFirePosition_0…5`, all
inside the bay, and 16 covers above them:

```
points: InternalFirePosition_0, _2, _1, _3, _4, _5
| hatch | MissileHatch | (0,-0,-1) | 0 .. 150 | (-1.35, 3.35, -6.117) | 7 |
```

Nothing in the entity connects fire to a cover (tested in §6), so "code-side" is right and the
"almost certainly on fire" is flagged as inference (R4's rule: `assumed` is not buildable — here it
is not built on, only noted).

**Verdict: HOLDS as labelled.** The distinction between "no link exists" and "the likely trigger"
is exactly what the rules ask for. The only cost is that the §12 summary compresses the inference
into "trigger is code-side", which reads as a finding; it is an absence plus a guess.

---

## 8. Entry paths: 21 both / 0 door-only / 4 no-door-only / 30 neither

**Why the card rests on it.** Answer (c), and the §12 row's "21 both / 0 door-only / 4
no-door-only / 30 neither of 55 graphs, donor both".

**Test — the census as counts is right, the labels are not.**

```
$ python -c "…DOORS.json interactions…"
both 21 | door_only 0 | no_door_only 4 | neither 30 | entities 55 | with_door_parts 51
```

But the per-sample interaction records show what "neither" contains:

```
donor:       driver_door_entry true, driver_enter_state true, entries include entry.driver, entry.driver.no.door
APC:         driver_door_entry false, driver_enter_state false,
             entries: entry.stunt.driver.side.close.stationary, entry.stunt.driver.side.far.stationary,
                      entry.mounted_weapon.stationary.stunt, entry.jump_to_stunt, …
             states:  S_ENTER_STUNT_TO_DRIVER_SIDE_CLOSE_VEHICLE, S_EXIT_DRIVER_VEHICLE_IN_WATER, …
mediumtank:  driver_door_entry false, driver_enter_state TRUE, entries: entry.ai.driver.left, entry.jump_to_stunt, …
```

Two things follow. (i) The APC is in "neither" yet has ten entry nodes and driver enter/exit states
whose names are stunt/side entries — it is enterable, just not through a door path, which the prose
does say ("military vehicles … whose entry nodes carry other names"). (ii) The **medium tank has
`S_ENTER_DRIVER_VEHICLE` with no `entry.driver` node**, so "state present, entry node absent" is a
third pattern the both/neither binary cannot express — and the md's §4 table shows only three rows
(donor, APC, monorail), omitting the fourth sample that exhibits it.

**Verdict: WEAK.** The counts are right, the table is incomplete (3 of 4 samples), and the reader
who takes "neither" as "no driver entry" is wrong for the APC and for the medium tank. Answer (c)
itself is unaffected: the donor has both nodes, and the motion is not in the container.

---

## 9. 0 animation members ⇒ the swing is not authored

**Why the card rests on it.** §4: *"The donor's container is 566 members and holds 0 animation
files: the swing is not authored in the entity."*

**Test.**

```
$ python -c "…DOORS.json samples…"
donor:       members 566, animation_members []
APC:         members 631, animation_members []
monorail:    members 334, animation_members []
mediumtank:  members 642, animation_members []
$ grep -n -A2 'animation_members' Tools/scripts/jc3doors.py
        "animation_members": [m for m in members
                              if os.path.splitext(m)[1].lower() in (".ban", ".anim", ".sab")],
```

The count is by three extensions only, inside the entity container. So the proved statement is "no
`.ban`/`.anim`/`.sab` member in these four containers", not "no animation exists for the door". The
record's wording is careful — "not authored **in the entity**" — and the conclusion it draws ("the
file proves the branch, not that the part visibly moves") survives because the hinge is a physics
constraint with no curve.

**Verdict: WEAK.** Scope is stated and the conclusion is safe; the extension list is a blind spot
worth naming (a `.btr`/blend-space door animation elsewhere would not be seen), because the same
paragraph is the only evidence for "hinge with no curve".

---

## 10. Speed is absent everywhere

**Why the card rests on it.** Card Do asks for "speed"; Limits answer: *"Speed is absent everywhere
(no rate field, no animation curve), so it stays UNKNOWN."*

**Test.** The hinge object has five fields (`axis`, `min`, `max`, `pivot`, `size`); no rate member
appears in any sample's hinge dict, and `container.animation_members` is empty (§9). As a negative
over doors in 78 modules + 4 entities, it is consistent with everything I can see. The one
rate-shaped structure in the same vehicle's data is the `CTurretWeaponComponent`'s `500`s — not a
door, so it does not contradict this claim, but it does show the project has an unreviewed
numeric block on the very same entity.

**Verdict: WEAK.** UNKNOWN is the right value and the reasoning is stated; "everywhere" is a
negative over the cached window (see §11), not the game.

---

## 11. The census is fleet-wide

**Why the card rests on it.** §2 opens "60 of the 220 hinged door parts across 56 modules"; §12
quotes "224 door rows in 56 of 78 modules".

**Test.**

```
census: modules 78 | modules_with_doors 56 | door_rows 224
interactions: entities 55
```

and Limits: *"The census covers the 78 cached parts modules (56 with doors) and the 55 cached
`.epe` graphs, not all 233 entities."* So the denominators are stated in the record — the numbers
are "of the cached 78", not "of the fleet".

**Verdict: WEAK by declaration.** Nothing is hidden; a reader who quotes "224 door rows" without
"of 78 cached modules" (as the §12 row does) overstates it. Same shape as the other G2 cards' 78/233
and 55/233 windows.

---

## 12. `--check` and the tamper test prove the decode

**Why the card rests on it.** Validation: `--check` rebuilds both files; the tamper test changed
the donor door's `max_deg` to 95 and got exit 1.

**Test.**

```
$ python Tools/scripts/jc3doors.py --check
PASS: 4 samples, 224 door rows / 220 hinged / X 60, both entry paths 21            EXIT=0
```

The check re-derives with the same reader and compares json + md; the tamper test proves the
comparison is real. Neither can catch a decode that is wrong on both sides. The genuinely
independent evidence in this card is elsewhere: the medium-tank hatch agreeing with G2-13's
separate reader (§5), and the invariants that cross tables (16 hatches all `MissileHatch`, all
0..150 about ±Z, parents 7/8 — consistent with `WEAPON_WIRING.jsonl`'s parts list for the same
vehicle).

**Verdict: WEAK.** Same pattern as G2-10 and G2-13: `--check` is a regression guard and the record
calls it validation.

---

## What would make this card honest (no new decoding needed)

1. Replace "none oblique" with "every axis is within 2.3° of a principal axis;
   `bavariumtank_hatch` (0.999, −0.04, 0) is the one to copy raw".
2. Add `CenterLeftDoor` (1) and `CenterRightDoor` (1) to the MODLOG's X-axis list so it sums to 60.
3. Say "220 of 224 door rows are three-piece; 4 wing parts carry a door behaviour with no hinge".
4. Soften (b): "no object *names* a hatch; the only unresolved refs are two object ids on the
   turret component" — and, if the raw cache is ever read, resolve `86D436D5=FFFF47F4` and
   `01E34D70=FFFF4E63`.
5. Put the medium tank in the §4 table, with `driver_enter_state: true` beside `entry.driver: -`,
   and say the APC is entered by stunt/side entries rather than a door path.
6. Name the animation extensions the zero rests on (`.ban/.anim/.sab`), and keep `min_rad`/`max_rad`
   in the json as G2-13 does.
