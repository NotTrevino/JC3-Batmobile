# Assumption challenge — backlog card G1-19 (cockpit and driver placement)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-19 card, its §12
row, the `MODLOG.md` `G1-19 · done` entry and the `G1-19 rework` entry, the generator
`Tools/scripts/grab_cockpit.py`, and the generated record `Research/BatmobileGrab/COCKPIT.json` +
`COCKPIT.md`. Nothing was launched, written into `D:/Games`, or committed. The only file written is
this one.

## VERDICT

**No headline number in G1-19 is falsified.** The reworked card is generated output with a green
`--check`, and the three numbers a modder would actually copy — the `Driver` position, the cushion
top, the roof clearance — reproduce from the inputs and agree with the independent socket record.
What does not hold up is the **class column** and the **two negative claims**, both of which are
broader than the search behind them:

| # | assumption | verdict |
|---|---|---|
| A1 | `ground = 0.02` is a measured ground plane | **HOLDS mechanically, WEAK as a label** — it is a `--ground` parameter *default*, and the assembly is shifted so the tyres land on it; "0.8447 m above the ground" means above the contact patch as placed |
| A2 | `Driver` position read through the ONE transform | **HOLDS** — `--check` green, and it equals the independent `SOCKETS_JC3.json` mirror to 4 dp |
| A3 | the socket's `forward/up/right` are `read` | **WEAK (class wrong)** — the socket has **no authored rotation** (`rotation_missing: true`); the basis is the identity default |
| A4 | "the driver faces the nose" | **WEAK** — inherits A3; true by convention, not by data |
| A5 | the socket is the hip point | **HOLDS as an inference** — 24 mm above the cushion, nothing else in the box |
| A6 | `DriverAnimOrigin` is the enter/exit origin | **WEAK** — `location_missing: true` (it is the bone pivot), and "enter/exit" is read off the **name** (R5) |
| A7 | "no eye or camera point in any file" | **WEAK** — two places searched; the `Camera` AnimSet (350 anims) is dismissed in one clause without being opened |
| A8 | "no yoke" — the hand box holds 4 faces | **WEAK** — 4 faces are not identified (no material, no part), and the box's own bands total 28 |
| A9 | "the yoke is not hiding elsewhere" (12 exports) | **WEAK** — 12 **files**, 6 distinct variants, and the JSON stores **names only**, no per-export geometry test |
| A10 | roof over the driver is opaque, never glass | **HOLDS** for the stated domain — 63-ray grid, 0 glass hits |
| A11 | eye point | **HOLDS as labelled** — `assumed` input, `derived (assumed input)` output, R4-compliant |
| A12 | screen 0.3188 × 0.1512 m, 35.2° from vertical | **HOLDS** — recomputed 35.24° from the stored normal |
| A13 | "screen content is not in the material" | **WEAK** — one material checked, no carrier sweep |
| A14 | 13/13 required anchors, `Driver` the only driver anchor | **HOLDS** |

Counts: 5 HOLDS, 8 WEAK, 0 BROKEN.

## Method note

The card has a generator and a `--check`, so the challenge can be run against the machine rather
than the prose:

```
$ python Tools/scripts/grab_cockpit.py --check
OK: 65 sockets, Driver (-0.0025, 0.8647, -1.0654) on Batmobile_Chassis; seat 13,014 faces
(cushion y 0.8407) / tub 27,334 / screen 100 faces 0.3188 x 0.1512 m / glass 3,532; roof liner
1.9661 (hip-to-liner 1.1014); hand box 4 faces; panel 1043 faces; 12 mesh exports;
MD regenerates identical
EXIT=0
```

"MD regenerates identical" is the important half: `COCKPIT.md` cannot drift from `COCKPIT.json`,
so every number quoted below is the stored one.

---

## A1 — `ground = 0.02` treated as a measured ground plane. **HOLDS mechanically, WEAK as a label**

The card prints "**0.8447 m above the ground**". That 0.8447 is `hip_y − stations.ground`:

```
$ python -c "...COCKPIT.json driver..."
"above_ground_m": 0.8447, "cushion_y": 0.8407, "above_cushion_m": 0.024
$ python -c "...stations.json..."
"scale": 0.01, "offset": [..., 0.02223144531250008, ...], "ground": 0.02,
"body_bbox": [[-1.747, 0.091, -3.42], [1.748, 2.362, 3.605]]
```

So where does the 0.02 come from? Not from the mesh — from a command-line default:

```
$ grep -rn 'ground' Tools/scripts/bat_assemble.py
12:    offset: track centred on X = 0, tyres' lowest point on the JC3 ground (`--ground`),
537:    ap.add_argument("--ground", type=float, default=0.02, ...)
663:    ground = min(h[0][1] - h[1] for h in hubs.values())
665:    offset = np.array([-xc, a.ground - ground, a.center_z - zc])
```

`bat_assemble.py:663` measures the tyre-bottom y, then `:665` **shifts the whole assembly** so that
that point lands on `a.ground`. The datum is therefore a *chosen* value, not a discovered one — the
mesh was moved to 0.02, so 0.02 can never be checked against the mesh. The measurement itself is
still sound, and stronger than the prose suggests: because the wheels were placed exactly on the
datum, "0.8447 m above the ground" is exact to the millimetre above the contact patch, and the
body's lowest y (0.091) confirms the chassis sits 7 cm above it. What is wrong is only the label:
"the ground" is a **project convention with a 2 cm default**, and it should be classed
`convention (--ground default 0.02)` rather than `read`. Anyone rebuilding with `--ground 0.05`
gets a `Driver` 0.8447 m above *that* plane, and the number in the card silently moves with it.

## A2 — `Driver` position read through the ONE transform. **HOLDS**

Two independent records agree:

```
$ python -c "...SOCKETS_JC3.json Driver..."
"position_m": [-0.002546, 0.864732, -1.06536],
"bone_position_m": [-0.0, 0.022231, 0.154297],
"relative_location_cm": [121.965767, 0.25, 84.249992]
$ COCKPIT.json -> "position_m": [-0.0025, 0.8647, -1.0654]
```

And the axis mapping is arithmetically consistent, which is the part worth testing: relative
(121.9658, 0.25, 84.25) cm → (1.2197, 0.0025, 0.8425) m; position − bone = (−0.0025, 0.8425,
−1.2197). So `jc3 = (−Y, Z, −X)·0.01 + bone`: one mapping, applied once, no axis flipped by hand
somewhere else. The cockpit script takes the socket record rather than re-deriving it, so this is
also a case where the card does *not* duplicate a transform.

## A3 — the socket basis classed `read`. **WEAK (wrong class)**

`COCKPIT.md` §2, the row as generated:

```
| bone / relative location | `Batmobile_Chassis`, (121.9658, 0.25, 84.25) cm in the bone frame;
  rotation null (`rotation_missing: true`) | read |
| `forward_jc3` | (0, 0, -1) - the driver faces the nose | read |
| socket basis | `up_jc3` (-1, 0, 0), `right_jc3` (0, 1, 0) - the socket's own up is the car's
  lateral axis; build the seated pose on world up, not on the socket basis | read |
```

The record says the rotation is absent:

```
$ python -c "...COCKPIT.json driver..."
"rotation_missing": true,
"forward_jc3": [0.0, 0.0, -1.0], "up_jc3": [-1.0, 0.0, 0.0], "right_jc3": [0.0, 1.0, 0.0]
$ python -c "...SOCKETS_JC3.json Driver..."
"relative_rotation_raw": null, "relative_rotation_deg": null,
"relative_rotation_quat": [0.0, 0.0, 0.0, 1.0], "rotation_missing": true
```

`relative_rotation_quat` is (0,0,0,1) because **there is no quaternion in the file** — it is the
loader's identity default, and `up_jc3 = (-1,0,0)` is just that identity run through the fixed UE→JC3
axis map. The page is honest that the rotation is null, but then classes the three derived axes as
`read`, which is exactly the R4 case of a default passing as a measurement. R15's own vocabulary
has the right label: `class default`. The practical advice ("build the seated pose on world up, not
on the socket basis") is correct *because* the basis is a default — so the card draws the right
conclusion and then hides its reason.

## A4 — "the driver faces the nose". **WEAK**

`forward_jc3 (0,0,-1)` is the JC3 forward axis under an identity rotation (A3). It is true of every
rotationless socket in the package, so it says nothing about where the driver looks; the evidence
that the driver faces the nose is the seat's rear lip and the screen ahead, not this vector. It
happens to be right — the cushion is under the socket and the screen is at z −1.755 — but the
sentence attributes it to the socket. Consequence if wrong: none for the geometry, but ANI-9 would
be building a seated pose on a defaulted heading.

## A5 — the socket is the hip point. **HOLDS as an inference**

```
"cushion_y": 0.8407, "above_cushion_m": 0.024
```

A ray down from the socket lands on slot 11 at 0.8407, 24 mm below it, and the hand box above it is
essentially empty (A8). 24 mm is also the right order for a hip socket (the mesh surface is the
cushion top, the bone is at the seat pan). The card does not claim more than this — it says
"hip / seat point, not the feet and not the head" and shows the ray. There is no independent source
for the interpretation, so it stays an inference, but it is an inference with a measurement under
it rather than a name.

## A6 — `DriverAnimOrigin` is "the enter/exit origin". **WEAK (name read as behaviour, R5)**

```
$ python -c "...COCKPIT.json anim_origin..."
"position_m": [0.0, 0.0222, 0.1543], "location_missing": true
$ python -c "...SOCKETS_JC3.json DriverAnimOrigin..."
"relative_location_cm": null, "location_missing": true, "rotation_missing": true
```

The socket has **no location at all**; its position is the `Batmobile_Chassis` bone pivot at ground
level. The card says so ("a null location"), which is good — but then concludes "the enter/exit
origin". Nothing on disk distinguishes "enter/exit origin" from "animation origin for the seated
clip", and the two readings disagree about what ANI-9 should do with it. The name is
`DriverAnimOrigin`; the card converts a name into a function, which is the exact R5 failure mode.
Correct output here is UNKNOWN / "purpose not established from the mesh": all that is known is that
it is a rotationless, locationless socket on the chassis pivot.

## A7 — "no eye or camera point in any file". **WEAK (two places searched)**

The card searches the socket table and the property names:

```
**No eye or camera socket ships in the mesh**: `SOCKETS_JC3.json` has 65 sockets and 2 driver-role
anchors, neither an eye point; `MECHANICS.md` carries no camera/eye property. The only camera-named
members in the grab are `RVehicleWeapon.OverrideCamera` (a `NameProperty`, default `CustomCamera`)
and an AnimSet named `Camera`; neither is an eye point.
```

Both facts check out:

```
$ driver-role sockets: ['Driver', 'DriverAnimOrigin']
$ grep -n -i 'camera\|eye' Research/BatmobileGrab/MECHANICS.md
1235:| Playable_BatmobileJoker_SF | `Camera` | AnimSet | 350 | — | — |
```

But the `Camera` AnimSet is a **camera animation set of 350 sequences** — the single most likely
carrier of a cockpit camera in the whole package — and it is waved away in half a clause ("neither
is an eye point") without being parsed. The claim "no eye point in any file" is therefore really
"no eye point in the socket table or the property names". The two-line dismissal may well be right;
it just has not been tested, and the sentence's scope is wider than the search. Verdict WEAK, not
BROKEN: no counter-evidence was found, only an untested candidate.

## A8 — "no yoke", on a box holding 4 faces. **WEAK**

```
$ python -c "...COCKPIT.json hand_box..."
{"faces": 4,
 "bands": {"y 0.90..1.00": 24, "y 1.00..1.10": 0, "y 1.10..1.20": 0, "y 1.20..1.30": 4},
 "rule": "all three vertices of the face inside |x| < 0.17, y 1.00..1.30, z -1.60..-1.10"}
```

Note the arithmetic: the bands hold **28** faces, `faces` is **4**. Both are "right" under their own
rule (the 24 in the 0.90–1.00 band sit just below the box and are excluded from `faces`), but the
page quotes only the 4 and the reader never sees the 24. Those 4 faces are not identified — no
material, no slot, no part — so "no steering geometry" is a judgement that 4 unnamed faces at
y 1.20–1.30 near the driver are not a yoke. The instrument panel is 0.44 m further forward
(z −1.510 vs the box's −1.10..−1.60 rear edge), which supports the reading, but the identification
is missing where the card elsewhere identifies every other part by slot and bone. WEAK.

## A9 — "the yoke is not hiding elsewhere", tested on 12 exports. **WEAK**

```
$ python -c "...COCKPIT.json mesh_exports..."
{"count": 12, "names": ["Batmobile_V3_Destroyed", "Batmobile_Jokerfied_Skin", "Batmobile_V2_Fire",
"Batmobile_V3_Destroyed", "Batmobile_Jokerfied_Skin", "Batwing_Carrier", "Batmobile_V3_Destroyed",
"Batmobile_MK2_Skin", "Batmobile_V2_Fire", "Batmobile_V2", "Batmobile_V3_Destroyed",
"Batmobile_V2_Fire"]}
```

12 entries, **6 distinct names** (Destroyed ×4, Fire ×3, Jokerfied ×2, plus MK2, V2, Batwing
Carrier). So "12 mesh exports" counts files, not bodies, and `--check` prints "12 mesh exports"
as though breadth had been demonstrated. More importantly the record stores the **names only** — no
per-export face count, no per-export hand-box test — so the fleet claim rests on a filename list,
not on geometry. The claim is very likely true (a Destroyed or Jokerfied skin of the same body has
the same interior), but it is a fleet-wide negative tested on a sample of *names*.

## A10 — roof over the driver is opaque, glass is front and sides. **HOLDS**

```
"roof": ... "sweep": {"rays": 63, "glass": 0, "x": [-0.15, 0.15], "z": [-1.35, -0.95],
                      "step": 0.05, "first": {"Batmobile_V3_Cockpit_MIC": 15, "Batmobile_Worn_NoRain": 48}}
```

and the page states the domain it swept: *"Of the 63 vertical rays from y 1.40 at |x| <= 0.15 and
z -1.35..-0.95, 0 hits glass"*. 63 = 7×9 on a 5 cm grid, zero glass, first surfaces split between
liner and MIC — consistent with the per-column table (1.8838 … 2.0007). This is a grid sample, not
an exhaustive sweep, but the claim is written to the grid's own extent, which is the honest form.
The one thing the grid cannot see is a hole smaller than 5 cm; nothing in the slot inventory
suggests one.

## A11 — the eye point rests on assumed anthropometry. **HOLDS (as labelling)**

```
"eye": { "assumed": "seated eye height / sitting height: standard adult anthropometry, no file in
the project ships it", "class": "assumed",
  "builds": [ {..., "class": "derived (assumed input: seated eye height, no source)"} ] }
```

The card's §4 heading is literally `The eye point - derived (assumed input)`, and MODLOG's rework
entry says the values are `assumed` so the eye point is `derived (assumed input)`. This is the
R4-correct treatment of a number with no provenance: it is not presented as decoded, and the
assumption travels with the value. Two builds are given (1.76 m mean and the project's 1.88 m
reference), so a reader who dislikes the anthropometry can rebase it from the hip — which is the
only reason the assumption is survivable. HOLDS.

## A12 — screen 0.3188 × 0.1512 m, 35.2° from vertical, centre (0, 1.4857, −1.7552). **HOLDS**

Recomputed from the stored normal, using JC3's vertical (y):

```
$ screen normal: [-0.001, 0.577, 0.739], size: [0.3188, 0.1512, 0.1942]
  acos(|n·y|) = 54.76 deg  ->  tilt from vertical = 90 - 54.76 = 35.24 deg
```

35.24 ≈ the printed 35.2, and the size is the bbox extent (`x -0.1594..0.1594` = 0.3188,
`y 1.4101..1.5613` = 0.1512). Cross-checked against the page's own row:

```
| **centre screen** | **12** `Cockpit_Master_Flip_Data` (100) | ... **0.3188 x 0.1512 m**, ...
  centre (0, 1.4857, -1.7552); mean normal (-0.001, 0.577, 0.739), 35.2 deg from vertical |
```

(The pre-rework 28° in the old MODLOG entry is gone from the generated page.) Note one trap this
check walked into and out of: measuring the tilt against **z** instead of **y** gives 47.65°, which
looks like a contradiction. JC3's vertical is y, so 35.2° is the correct convention — a reminder
that the card's coordinate sentence ("x = axle, y = vertical, z = longitudinal, nose at -z") is
load-bearing, and it is stated in the page.

## A13 — "screen content is not in the material". **WEAK**

`Cockpit_Master_Flip_Data` is a parentless master material with all four channels unconnected and
no texture parameters — that is read, and it is a fair conclusion about *that* material. But the
claim in §6 is "the picture does not [ship]", and the search is one material: nothing checks that no
other material or texture-parameter set targets the screen slot, and a runtime-driven material
(a `MaterialInstance` whose parent resolves at load) would not show its picture in the export at
all. Same shape as A7 — a negative stated more widely than it was searched. WEAK.

## A14 — anchors and the two driver sockets. **HOLDS**

```
$ python -c "...SOCKETS_JC3.json..."
required_anchors: names 13, present 13, missing []
counts: {'sockets': 65, ..., 'required_anchors': 13, 'required_present': 13, 'missing_locations': 1}
driver-role sockets: ['Driver', 'DriverAnimOrigin']
$ COCKPIT.json anchors: {"required": 13, "present": 13, "driver_required": true,
                         "driver_anim_required": false}
```

`Driver` is in the 13-name required list; `DriverAnimOrigin` is not; exactly one socket has no
location (`DriverAnimOrigin`, A6). The page's sentence — "`Driver` is the only driver anchor in the
list" — is exactly right and is the sentence the pre-rework version got wrong, so the review fix
landed. HOLDS.

---

## What a rework would have to touch

Nothing here is a wrong number; the fixes are class labels and claim scopes, all in the generator:

1. **A3/A4** — class `forward_jc3` / `up_jc3` / `right_jc3` as `default (rotation_missing)` and drop
   "the driver faces the nose" from the socket row (it is a consequence of a default).
2. **A6** — replace "the enter/exit origin" with UNKNOWN / "purpose not established", keeping the
   `location_missing: true` fact.
3. **A7** — either parse `Camera` (AnimSet, 350 anims) or narrow the sentence to "no eye point in
   the 65 sockets or in the property names; the `Camera` AnimSet was not examined".
4. **A8/A9** — identify the 4 hand-box faces by slot/bone, print the 28-face band total next to the
   4, and either scan the other exports or reword "12 mesh exports" to "6 distinct variants, names
   listed; interiors not compared".
5. **A13** — widen the material sweep or narrow the claim.
6. **A1** — print the datum: `ground = stations.ground = 0.02 (bat_assemble --ground default)`, so
   "0.8447 m above the ground" reads as "above the contact patch as placed".

None of that changes the `Driver` position, the cushion, the roof clearance or the eye arithmetic —
which is why the verdict is "no BROKEN", and why the card's own check stays green while it happens.
