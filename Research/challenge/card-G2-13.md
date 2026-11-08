# Assumption challenge — card G2-13 · Turret and cannon mechanics

Written 2026-10-30. Read-only review: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified; the only file written is this one. No game was launched,
nothing was written to `D:\Games`, nothing was committed.

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-13 card (line 621), the §12 row (line 1296),
`MODLOG.md` §"G2-13 · Turret and cannon mechanics — intended change" (9595) and §"— done" (9624),
and the card's outputs: `Research/JC3Grab/TURRET.md` (384 lines), `TURRET.json`, `README.md` rows,
`Tools/scripts/jc3turret.py`. Cross-checked against `WEAPON_WIRING.jsonl` and `PARTS_TABLE.jsonl`
(the tables G2-13 reads), `MOVING_PARTS.md` (G2-14, which covers the `Turret` behaviour), and the
archive index.

**Card as written:** decode `aim_part_constraints`, `hinged_parts` and related arrays for six named
vehicles, record yaw/pitch limits, rates, pivot offsets, parent chain and how the aim target is
chosen. Done: the medium tank's turret+cannon chain fully described with numbers, same for one
wheeled vehicle.

---

## VERDICT

**The decode is careful and the numbers reproduce; the two generalisations it adds on top are not
supported, and one whole turret mechanism is missing from the picture.**

```
$ python Tools/scripts/jc3turret.py --check
PASS: 8 samples, 92 points on 52 weapons, 85 aim-constraint rows, 3 mediumtank constraints   EXIT=0
```

Independently re-derived from `WEAPON_WIRING.jsonl` + `PARTS_TABLE.jsonl`, with no code shared with
the card's tool: **92 points naming a part, on 52 weapons, across 41 entities; yaw = 18 `Turret` +
13 `Cannon` + 44 plain; pitch = 47 `Cannon`** — every count exact. The medium tank's three hinges,
the pivot arithmetic, the radian→degree conversion, the suspension reading of
`aim_part_constraints` and the Bavarium reuse all check out (§3–§5, §8, §9).

What does not survive:

| # | assumption | verdict |
|---|---|---|
| 1 | "a turret is two parts and two Havok hinges, not a special object" | **BROKEN as a generalisation** — the fleet has a `CTurretWeaponComponent` (on `v5603`, the monorail missile car); the 8 samples exclude it |
| 2 | the fire point's two unnamed properties are the whole turret link | **BROKEN** — a third, *named* property `id:A90F5E74 = turret_anchor` sits on 55 points, 23 of them without the yaw id; the doc reports neither |
| 3 | the hinge pivot frame is unproven | **HOLDS, over-cautious** — the data does settle it: all pivots are in the vehicle body frame (§3) |
| 4 | degrees from radians | **HOLDS** — `-3.124139 → -179.0`, `2.268928 → 130.0`, both kept in the json |
| 5 | 92/52/41 points, 18/13/44 yaw, 47 pitch | **HOLDS** — independently recounted |
| 6 | "fleet census" of fire points | **WEAK** — it is 92 of the 300 points and 41 of the 53 armed entities; the denominator is never given |
| 7 | the 44 plain yaw parts are "on aircraft pods" | **WEAK/label** — all 44 are `CHelicopter` pods, not fixed-wing |
| 8 | `aim_part_constraints` is suspension, not turret aim | **HOLDS** — 73 of 85 targets are brake/wheel/disc/caliper/engine; 12 are unclassified |
| 9 | no `Turret`/`Cannon` row in `aim_part_constraints`, 0 on the six | **HOLDS** — verified |
| 10 | no turret turn rate exists in the decoded data | **WEAK** — true of `.physicsc`, the parts arrays and `vehicle_common`, but the one `CTurretWeaponComponent` carries four `500` values and a `45` that were never examined |
| 11 | `STargetPoint` (0,1,0) is "the aim target … at the body centre" | **WEAK** — a local offset read by its name; no consumer is shown, and a point at the shooter's own origin is not a target |
| 12 | the turret aims through the weapon's AutoAim tune | **WEAK** — the tanks' tune has `CanTargetVehicles 0`; the doc notices and does not resolve it |
| 13 | `--check` green proves the decode | **WEAK** — same code re-derives; the tamper test proves the guard, not the reading |

**Bottom line:** the card met its Done line (medium tank + APC/armoured jeep described with
numbers) and the numbers are right. The problems are all in the *extra* claims: "not a special
object" ignores a real turret component, and "two point properties" misses a named third. Both are
cheap to fix from the tables G2-11 already produced; neither needs a re-decode.

---

## 1. "A turret is two parts and two Havok hinges, not a special object"

**Why the card rests on it.** TURRET.md's opening sentence — *"The short answer: a turret is
**two parts and two Havok hinges**, not a special object"* — and the §12 row, which summarises the
deliverable as that mechanism. It is what a B-05 port is told to build.

**Test.** Search the fleet's own wiring (G2-11, a dependency of this card) for a turret component
class:

```
$ grep -o "CTurretWeaponComponent\|CBarrelSpinWeaponComponent\|CAimPOIWeaponComponent" Research/JC3Grab/WEAPON_WIRING.jsonl | sort | uniq -c
     11 CAimPOIWeaponComponent
     12 CBarrelSpinWeaponComponent
      1 CTurretWeaponComponent
```

One vehicle in the fleet carries a turret weapon component — `v5603_train_urga_monorailmissilecar`
(`CTrain`), on `w614_monorailmissilecar_missile`:

```json
{"class": "CTurretWeaponComponent", "name": "TurretWeaponComponent",
 "props": {"id:569538FC": "500", "id:9CE47505": "500", "id:B912E42A": "500", "id:CE02A3EF": "500",
           "id:FF777489": "45", "id:509A8EB2": "3", ... 30 more unnamed ...}}
```

That is a special object that turns a turret, with four `500` values and a `45` that look exactly
like angles or rates (consistent with `500` being a speed and `45` an elevation). It is in the
fleet, in the table this card's dependency produced, and `v5603` appears nowhere in the output:

```
$ grep -c "v5603" Research/JC3Grab/TURRET.md
0
```

**Verdict: BROKEN as a generalisation.** The card's Done line named six vehicles and the record
added two; the sentence it prints is about all turrets. The correct claim is "in the six sampled
CCar/CHelicopter mounts a turret is two parts and two hinges; the fleet also has one
`CTurretWeaponComponent` (train missile car) whose unnamed numeric properties are not decoded
here". Note that the same paragraph's "**Not in the files:** a per-vehicle turret turn rate" is
then at risk too — the `500`s on that component are the only rate-shaped numbers in the fleet.

---

## 2. The fire point's unnamed properties are the whole turret link

**Why the card rests on it.** TURRET.md: *"the weapon's fire point names both parts in two unnamed
string properties"*, and the Limits line: *"The two point properties `id:80201E4D`/`id:5C19E7E0`
still have no recovered names; their meaning is proven by the part names and behaviours they
carry."* The port instruction is "copy the two point strings".

**Test 1 — there is a third property, and it is named.** The medium tank's `w602` fire point:

```
$ python - <<'EOF'   # WEAPON_WIRING.jsonl, v0201, w602 fire_position_0
w602_mediumtank_canon fire_position_0 xyz= [0.0, 0.3739, -5.8174]
  props: {'id:5C19E7E0': 'mediumtank_cannon', 'id:61ECCE72': '-1',
          'id:80201E4D': 'mediumtank_turret', 'id:8C547250': '0',
          'id:A90F5E74': 'turret_anchor', 'id:D04059E6': '-405742323'}
```

`id:A90F5E74` carries the **literal, named** string `turret_anchor`. It is not in either output:

```
$ grep -c "turret_anchor\|A90F5E74" Research/JC3Grab/TURRET.md Research/JC3Grab/TURRET.json
Research/JC3Grab/TURRET.md:0
Research/JC3Grab/TURRET.json:0
```

**Test 2 — it is not rare, and it is the only part link on many points.**

```
$ python - <<'EOF'   # every fire point in the fleet
points with id:A90F5E74: 55 | of which without id:80201E4D: 23
```

So 55 of the 300 fire points name a `turret_anchor`, and **23 of those name no yaw part at all** —
including the medium tank's own co-axial machine gun (`w603`'s `fire_position_0` carries
`turret_anchor` and neither `80201E4D` nor `5C19E7E0`). For a port that wants the MG to follow the
cannon, the two "turret link" properties are absent on exactly the weapon that needs them; the
named one is present.

**Verdict: BROKEN.** The census of point properties is incomplete (2 reported, at least 3 exist),
the third is the only one with a readable name, and the doc's sentence "their meaning is proven by
the part names and behaviours they carry" is a name-based proof (R5) that a named sibling property
argues against being the turret link at all.

---

## 3. The hinge pivot frame is unproven

**Why the card rests on it.** Limits: *"The hinge transform's frame (body-A local vs vehicle space)
is not proven: the medium tank's numbers agree with vehicle space, and on the wheeled mounts the
pitch pivot sits above an unconstrained adapter part, so a port should read them the way they are
printed."* And §1's prose composes them: *"The cannon pivots on X 0.25 m above the turret ring."*

**Test — the frame is decidable from the doc's own table.** The cannon (constraint 0) and the hatch
(constraint 1) both have parent 26, the turret:

```
$ python - <<'EOF'   # TURRET.json, v0201
(0, [0.0, 2.5347, 0.0],        -5.0,  20.0)   # cannon, parent 26
(1, [-0.4848, 2.921, 1.4785],   0.0, 130.0)   # hatch,  parent 26
(2, [0.0, 2.2812, 1.1382],   -179.0, 179.0)   # turret, parent 0
```

If a pivot were expressed in the parent part's frame, the hatch would sit 2.921 m *above the
turret's own origin* — i.e. roughly 5.2 m above the ground on a vehicle whose hull top is at the
turret ring (2.28 m) and whose hatch hinge is at 2.92 m absolute. The printed heights only make
sense as one common body/vehicle frame, which is also the only frame in which the doc's
0.2535 m difference (`2.5347 − 2.2812`) is a trunnion height rather than a doubling. The same
holds on the small tank: cannon y 1.9143 / turret y 1.8131 (+0.10), where a parent-local reading
would put the cannon 1.9 m above the turret.

**Verdict: HOLDS, but the caveat is wrong in a way that matters.** All pivots are body-frame; the
§1 arithmetic is valid; the Limits paragraph tells a port to distrust a frame the data settles. The
honest sentence is "the pivots are all in the vehicle body frame, as the hatch/cannon pair on the
medium tank shows".

---

## 4. Degrees are converted from radians correctly

**Why the card rests on it.** Every limit the port will copy (`-179..179`, `-5..20`, `0..130`,
`0..30`) is a converted value.

**Test.** The json keeps both:

```
$ python - <<'EOF'   # TURRET.json, v0201 constraint 2
{"i": 2, "max_deg": 179.0, "max_rad": 3.124139, "min_deg": -179.0, "min_rad": -3.124139, "pivot": [0.0, 2.2812, 1.1382]}
{"i": 1, "max_deg": 130.0, "max_rad": 2.268928, ...}
```

179 × π/180 = 3.124139 and 130 × π/180 = 2.268928 — exact. So the raw values are radians and the
conversion is right, and the odd-looking 179° (rather than 180°) is the game's own number, not a
rounding artefact of the reader.

**Verdict: HOLDS.** One of the few places where the record could have hidden a unit error and did
not — and keeping `*_rad` beside `*_deg` is what makes it checkable.

---

## 5. The fire-point census numbers

**Why the card rests on it.** The §12 row's most quotable sentence: *"92 fire points on 52 weapons
name the moving parts via `id:80201E4D`/`id:5C19E7E0` — 47/47 pitch parts `Cannon`, 75 yaw = 18
`Turret` + 13 `Cannon` + 44 aircraft pods, 2 cross-entity entries"*.

**Test — re-derived from a different pair of tables, with no shared code:**

```
$ python - <<'EOF'   # WEAPON_WIRING.jsonl + PARTS_TABLE.jsonl
points naming a part: 92 | weapons: 52 | entities: 41
yaw behaviours: {'Turret': 18, 'Cannon': 13, 'None': 44, '?': 1}
pitch behaviours: {'Cannon': 47, '?': 1}
plain yaw parts by root class: {'CHelicopter': 44}
```

Every number matches. The two `?` are the cross-entity cargo-plane entries (the part belongs to the
tank the plane carries), which the doc records separately and correctly — my lookup fails exactly
where the doc says it should.

**Verdict: HOLDS.** This is the strongest part of the card: an independently reproducible census
with zero unresolved names after the cross-entity case is handled.

---

## 6. "Fleet census" of fire points

**Why the card rests on it.** §3 is titled *"The point properties (fleet census)"* and opens
"Across 41 armed entities, 92 fire points on 52 weapons name a yaw part or a pitch part."

**Test.** The qualifying clause is present, but the denominator is not, and the fleet is bigger:

```
$ python - <<'EOF'   # WEAPON_WIRING.jsonl, all points
fire points: 300 | weapons with points: 88 | entities with points: 53
```

92 of 300 (31%), 52 of 88 weapons (59%), 41 of 53 entities (77%). G2-11's own count is 53 armed
entities / 88 components, so "41 armed entities" in a section headed "fleet census" reads as the
fleet size to anyone who has not just read G2-11.

**Verdict: WEAK.** Add the denominator ("of 300 points on 88 weapons / 53 entities, 92 name a
part"). The finding is unaffected — it is a presentation risk, not a wrong number.

---

## 7. The 44 plain yaw parts are "on aircraft pods"

**Why the card rests on it.** §3: "Yaw parts are `Turret` (true turrets), `Cannon` (boat/jeep
mounts …) or plain parts on aircraft pods."

**Test.** Resolve each plain yaw part's entity root class:

```
$ python - <<'EOF'
plain yaw parts by root class: {'CHelicopter': 44}
sample: v2200_helicopter_capstone_assault_debug.ee / assault_weaponry_r_r
```

All 44 are helicopter weapon pods (`CHelicopter`, `*_weaponry_*`), not fixed-wing aircraft (the
`CAirPlane` entities are v4202/v4602/v4800). "Aircraft" is not wrong in plain English, but the
project uses `CAirPlane`/`CHelicopter` as distinct root classes and the fleet's `CAirPlane` pods
are not in this set.

**Verdict: WEAK (label).** Say "helicopter weapon pods" — it also tells the reader that no
fixed-wing aircraft uses the two-property link.

---

## 8. `aim_part_constraints` is suspension, not turret aim

**Why the card rests on it.** The card's first Do item assumes this array drives the turret; the
record's headline finding is that it does not.

**Test.**

```
$ python - <<'EOF'   # TURRET.json aim_constraint_census
rows = 85 | with_constraints = 17 | modules = 78
behaviours = {'source:Axle': 2, 'source:None': 70, 'source:Spring': 13,
              'target:BrakeCalipers': 6, 'target:BrakeDisc': 12, 'target:BrakeDrum': 34,
              'target:Engine': 2, 'target:None': 12, 'target:Wheel': 19}
```

73 of 85 targets are brake drums, wheels, discs, calipers or engines; the sources are 13 springs,
2 axles and 70 plain parts with names like `atv_y_bar_r_r_b`. No row names a `Turret` or `Cannon`
part (count 0 in `behaviours`, which has no Turret/Cannon key at all).

**Verdict: HOLDS.** The behaviour names of the *targets* carry the claim, not the array's name —
which is exactly R5 done right. Residual: 12 target-`None` rows are unclassified; they do not
change the conclusion, but "all suspension" is 73/85 + 12 by exclusion.

---

## 9. The six turreted vehicles have 0 aim constraints

**Test.** Per-sample rows in the json and md:

```
$ grep -n "aim_part_constraints" Research/JC3Grab/TURRET.md | head -4
24:`v0201_car_capstone_mediumtank_military_01.ee` - 42 parts, 3 constraint objects (hkpLimitedHingeConstraintData 3); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.
49:`v0202_car_capstone_bavariumtank_military_01.ee` - 38 parts, 15 constraint objects (hkpLimitedHingeConstraintData 15); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.
86:`v0603_car_urga_smalltank_military_01.ee` - 37 parts, 17 constraint objects (hkpLimitedHingeConstraintData 16, hkpRagdollConstraintData 1); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.
125:`v0200_car_capstone_apc_military_01.ee` - 45 parts, 16 constraint objects (hkpLimitedHingeConstraintData 16); `aim_part_constraints` rows 0, `hinged_parts` rows 0, `rotating_parts` rows 0.
```

All eight samples show 0, and `hinged_parts`/`rotating_parts` 0 — so for those vehicles the hinge
really is only in `.physicsc`. The md also gives the fleet context (28 of 78 modules carry
`hinged_parts` rows, 22 `rotating_parts`), i.e. 148 and 47 rows elsewhere, and scopes the
conclusion with "for a tank".

**Verdict: HOLDS.** Scoped correctly, and the fleet counts are stated so the reader can see the
arrays are not universally empty.

---

## 10. No turret rotation rate or acceleration exists

**Why the card rests on it.** Limits: *"Rotation speeds and accelerations are not in the decoded
data — a limited hinge carries an axis and two angles, and the turn rate is code-side (UNKNOWN)"*;
§12: "Not in the files: a per-vehicle turret turn rate".

**Test 1 — the three places it looked are genuinely empty.**

```
$ python - <<'EOF'   # TURRET.json, v0201 constraint objects
{"class": "hkpLimitedHingeConstraintData", "i": 0, "max_rad": 0.349066, "min_rad": -0.087266, "pivot": [...], "axis": [...]}   # no rate member
$ python - <<'EOF'   # WEAPON_WIRING.jsonl, every weapon/point property containing speed|rate|aim|turn|rot
88 autoaim_tuning_file
```

Only `autoaim_tuning_file` matches — no rate on the weapon component either. And G2-14 confirms the
behaviour table has no row: `MOVING_PARTS.md:129 | Turret | no vehicle_common row | 22 | 22 | 7 |
CBoat, CCar`.

**Test 2 — the one turret component was not searched.** §1 above: `CTurretWeaponComponent` on
`v5603` carries `id:569538FC/9CE47505/B912E42A/CE02A3EF = 500` and `id:FF777489 = 45`, 30+
unnamed properties in total, none decoded by this card.

**Verdict: WEAK.** "Not in the decoded data" is true because the card chose the data; the fleet has
one turret component whose unnamed numbers are the best remaining candidate for a rate and an
elevation. UNKNOWN is still the right label for the six samples, but the sentence should say the
train's component was not examined.

---

## 11. `STargetPoint` (0,1,0) is the aim target at the body centre

**Why the card rests on it.** §5: *"Each sampled entity carries exactly one `STargetPoint` named
`AutoAimTargetPoint` … Its `world` matrix translation is (0, 1, 0) on every sample: the target
point is the vehicle origin one metre up at the body centre, not the muzzle and not the turret."*
Then: "the aim system picks a point (the entity's `STargetPoint`, or a soft-aim candidate), and the
two hinges are driven to put the cannon on it."

**Test.**

```
$ grep -n "STargetPoint" Research/JC3Grab/TURRET.md | head -3
| `STargetPoint` | `AutoAimTargetPoint` | -1 | 0, 1, 0 |     (all eight samples)
```

Three separate inferences are stacked on one number:

1. that `world` (0,1,0) is a *vehicle-local* offset — the same matrix convention as the fire
   points, whose `world` translations are part-local (`0, 0.3739, -5.8174` for the cannon), so
   this is likely, not shown;
2. that "the vehicle origin + 1 m" is "the body centre" — the medium tank's turret ring is at
   2.2812 and its hull top at 2.921, so 1 m is inside the hull but below the ring; "centre" is a
   plausible label, not a measured one;
3. that this object *is* what the turret aims at — the name says target point, and nothing in the
   decode shows a consumer. A point fixed at the vehicle's own origin cannot be the thing the
   vehicle aims at; it is either the point *other* units aim at on this vehicle, or a local
   offset the aim code applies to the target entity. The record does not distinguish these.

**Verdict: WEAK.** R5 in miniature: `STargetPoint` is a name, (0,1,0) is a local number, and the
paragraph turns them into a described aiming behaviour. The honest sentence is "one `STargetPoint`
per entity at local (0,1,0) with `min_aim_distance -1`; what reads it is not in the decode".

---

## 12. The turret aims through the weapon's AutoAim tune

**Why the card rests on it.** §5's second half attributes the aim choice to the tune the weapon
names (`autoaim_vehicle_mgun` for `w602`/`w603`/`w605`), and the §12 row ends with the tune's
numbers as the answer to "how the aim target is chosen".

**Test.** The doc prints the tune honestly, including the flag that contradicts a turret:

```
| `CanTargetCharacters` | 1 |
| `CanTargetRigidObjects` | 0 |
| `CanTargetVehicles` | 0 |
...
`CanTargetCharacters` is 1 while `CanTargetVehicles` and `CanTargetRigidObjects` are 0:
the soft aim assist on the tank cannon is for characters, not vehicles.
```

So a tank cannon bound to `autoaim_vehicle_mgun` selects characters and refuses vehicles. The doc
names the contradiction and then keeps the conclusion ("the aim system picks a point … the two
hinges are driven to put the cannon on it"). Either the tune is the *player's* soft-aim assist and
the AI's vehicle aiming is code-side, or `CanTarget*` does not mean what its name says — the record
does not decide, and the card's Done asks "how the aim target is chosen".

**Verdict: WEAK.** The values are right and the contradiction is not hidden, which is good; the
conclusion drawn from them (this tune is how the turret picks its target) is not supported by the
values in the same table.

---

## 13. `--check` green (with its tamper test) proves the decode

**Why the card rests on it.** The "Validation" paragraph: `--check` re-reads the eight entities and
rebuilds both files, plus the tamper test that changed `max_deg` to 90 and got exit 1.

**Test.**

```
$ python Tools/scripts/jc3turret.py --check
PASS: 8 samples, 92 points on 52 weapons, 85 aim-constraint rows, 3 mediumtank constraints   EXIT=0
$ grep -n "def cmd_check" Tools/scripts/jc3turret.py
```

The check re-derives with the same reader and compares json field-for-field and md byte-for-byte.
The tamper test is a good demonstration that it is a real guard — and it is still the same code on
both sides, so it proves *nothing changed*, not *the reading is right*. The independent evidence in
this card is the census in §5 (reproduced here from G2-11's tables) and the invariants
(`every Turret/Cannon part sits on a limited hinge`, `every pitch part is a Cannon`), which are
cross-table and therefore worth more than the byte compare.

**Verdict: WEAK.** Same shape as G2-10: `--check` is a regression guard; the record calls it
validation.

---

## 14. The Bavarium tank reuses both hinges unchanged

**Test.**

```
$ python - <<'EOF'   # TURRET.json
v0201 = [(0, [0.0, 2.5347, 0.0], -5.0, 20.0), (1, [-0.4848, 2.921, 1.4785], 0.0, 130.0), (2, [0.0, 2.2812, 1.1382], -179.0, 179.0)]
v0202 = [(0, [0.0, 2.5347, 0.0], -5.0, 20.0), (1, [-0.4921, 2.8222, 1.4826], 0.0, 130.0), (2, [0.0, 2.2812, 1.1382], -179.0, 179.0)]
```

Turret and cannon pivots/limits are byte-identical; the hatch differs by ~10 cm, and the Bavarium
adds 12 skirt hinges at 0..30°. That is consistent with the two tanks sharing turret and gun art on
different hulls, and it is a useful check in itself: the identical values come from two separately
read `.physicsc` files, so the reader is not copying one sample into another.

**Verdict: HOLDS.** Worth recording *because* identical numbers across two entities look like a
copy bug and are not one.

---

## What would make this card honest (no new decoding needed)

1. Rewrite the opening sentence: "in the six sampled mounts a turret is two parts and two hinges;
   the fleet also carries one `CTurretWeaponComponent` (`v5603`, train missile car) that is not
   decoded here" — and drop the absolute "not a special object".
2. Add `id:A90F5E74 = turret_anchor` to §3, with its count (55 points, 23 without the yaw id) and
   the note that the medium tank's co-axial MG links to the turret only through it.
3. Replace the "frame not proven" caveat with the fact: the pivots are body-frame, evidenced by the
   cannon/hatch pair both parented to the turret at absolute heights.
4. Give the census a denominator (92 of 300 points, 52 of 88 weapons, 41 of 53 entities) and say
   "helicopter pods" for the 44.
5. Scope "no rotation rate": `.physicsc`, the parts arrays and `vehicle_common` carry none; the
   `CTurretWeaponComponent`'s unnamed `500`s/`45` are the open lead.
6. Say what `STargetPoint` is *not* (a consumer is not in the decode), and note that the tanks'
   AutoAim tune has `CanTargetVehicles 0` — i.e. the tune is soft aim assist, not the turret's
   vehicle targeting.
