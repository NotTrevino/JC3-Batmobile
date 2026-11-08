# Independent review — G3-01d (BmAK collision → render mesh frame link)

Reviewer: independent (did not write the card). Date: 2026-11-03.
Read: `tmp/freebuff/reports/G3-01d.md`, `Research/BatmobileGrab/COLLISION_FRAME.md`,
`Research/BatmobileGrab/COLLISION_FRAME.json`, `Tools/scripts/grab_collision_frame.py`, plus the four
inputs it consumes (`COLLISION_CONVEX.json`, `COLLISION_BOXES.json`, `BONES.json`, `MESHES.json`).

Read-only: I ran `--check` only; I did **not** run `--write` (it would rewrite the card's outputs).
No game launched, nothing written under `E:/Games` or `D:/Games`, no git command.

Method limitation: my spot-checks use the same decoder (`Tools/scripts/upk_read.py`), so a decoder bug
would be common-mode. I compensated by resolving the **export record** (which that decoder does not
parse) and by reading the tag streams myself, export by export.

---

## VERDICT: **minor issues**

Every decoded number I re-read is correct: the three component translations, the one serialised
rotator, the SkeletalMesh size, the 180/180 bone-name run, and the "not serialised" verdicts (those six
objects do have real property streams — 2–5 tags each — with no `Translation` tag, so the absence is
genuine, not an empty parse). The margin arithmetic also reproduces exactly.

What is not sound is the *evidence packaging*: one of the "7/7" checks is a tautology that cannot fail,
the only threshold in the card is a chosen 15 cm mislabelled as "5 % of the car's width" (which would be
17.48 cm), the report calls an AABB-containment test a silhouette test, and the battle-hull overshoot is
explained by an unlabelled hypothesis. None of these changes the +5.0 cm result or the pursuit
inside-ness, so the card does not need re-deriving — it needs three claims restated and one check fixed.

I also found that two things the card presents as inherited "rule" or as assumption are actually
**decodable from the bytes** (archetype chain, sibling outer), and that one UNKNOWN (U-2) is resolvable
outright. Those are in §4 — they strengthen the card rather than damage it.

---

## 1. Check output (verbatim)

```
cd "E:/Modding/JC3-Batmobile" && uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_frame.py --check; echo "CHECK_EXIT=$?"
```

```
OK: 9 components, ref skeleton NOT decoded, pursuit offset [5.0, 0.0, 0.0] cm, margins 0.22 / -12.57 cm, 7/7 checks, md byte-identical
CHECK_EXIT=0
```

Matches the report's quoted line exactly. Note that the "7/7" includes the unfalsifiable check in I1.

---

## 2. Spot-checks — 5 decoded values re-read from the raw packages

All read by me with `upk_read.Package` / `pkg.data(export)` / `struct` at the byte offsets named.
"Walk start" is the offset the card's own rule picks; I reproduced it independently.

| # | decoded value claimed | where I read it | match |
|---|---|---|---|
| 1 | `BmGame.upk` 175716 `Default__RVehicleBatmobileBase.SVehicleMesh`, 157 B: `VectorProperty` @400 = **[-50.0, 0.0, -95.0]**, no rotator | export data, walk from start 12 → 8 tags, stop `end` | **yes** (exact) |
| 2 | `BmGame.upk` 176111 `…BatmanCollisionMeshBattleMode0`, 123 B: `VectorProperty` @400 = **[-40.0, 0.0, -110.0]**, `RotatorProperty` @412 = **[750, 0, 0]** | same method, start 12 → 7 tags | **yes** (exact; 750/65536·360 = 4.119873046875°) |
| 3 | `BmGame.upk` 176112 `…BatmanCollisionMeshPursuitMode0`, 107 B: `VectorProperty` @400 = **[-45.0, 0.0, -95.0]**, no rotator | same method, start 12 → 6 tags | **yes** (exact) |
| 4 | `SkeletalMesh` 5284 = **20,151,210 B**; the 180 bone names appear at **stride 44 from byte 8423**, in `BONES.json` order, bone 0 = `Batmobile_Chassis` | `Playable_Batmobile_SF.upk` export 5284, 180 records at `8423 + 44k` | **yes** (180/180 names match, first `Batmobile_Chassis`, last `…Piston_Top_001`) |
| 5 | The six instance/Startup layers "serialise no Translation" (so they inherit) | their tag streams: 5289 5 tags, 5392 2, 5393 2, 169640 2, 171103 2, 171104 2 — all `stop: end`, **no** tag at offset 400/412/424 and no object reference to another component | **yes** — real parsed streams, so the absence is evidence, not an empty parse |

Also re-derived by hand from the card's own inputs (not a separate spot-check): pursuit margins
18.78 / 12.84 / 15.55 / 15.66 / 0.22 / 9.87 cm, battle hull after the 4.1199° pitch
(-337.62 … 377.16 in X, -26.40 … 317.31 in Z), and the chassis-box margins 8.96 / -12.57 / 3.22 and
3.28 / -12.46 / 23.46 — all reproduce. The rotation math and the sign conventions are right.

---

## 3. Issues

### I1 — one of the seven checks is a tautology

```python
check("no ref-skeleton transform is claimed unless its layout reproduces the bind pose ...",
      (lay_.get("ok") == BONE_COUNT) == bool(sk.get("layout_accepted")), ...)
```

`layout_accepted` is defined three lines earlier as `bool(best and best["ok"] == BONE_COUNT)`, so the
comparison is `X == X` and can never be false. The check is printed as PASS and counted in "7/7", but it
tests nothing — it restates the assignment. The card's own defence against dressing up a rejected search
is therefore the one check that cannot detect dressing up. Fix: assert the *data* (e.g. that the accepted
layout exists only if 180/180, and that the accepted layout's offsets equal the independently decodable
record structure in §4 R1), or drop the check and say so in the doc.

### I2 — the only threshold is a chosen number labelled as a derived rule, and its arithmetic is wrong

The chassis-box check passes at `overshoot 12.57 <= 15.0`, and the detail string (in the doc, the JSON and
the report) says the 15 cm tolerance is "*a stated rule (5 % of the car's width 349.5 cm)*".
5 % of 349.53 is **17.48 cm**, not 15. So either the rule is 5 % (→ 17.48, still passes) or it is 15 cm
(→ a chosen value, which §6b forbids: "*no `chosen`/`assumed`*"). As written the number is dressed as
derived. This matters beyond pedantry because the same check is one of the inputs to
"frame link: **PROVEN within tolerance**" — and the chassis box is genuinely **outside** the render bounds
by 12.57 cm in Y on *both* sides (hi −12.46), i.e. 374.5 cm wide against the mesh's 349.5 cm. That is not
a positive frame result; it is a full-size box that a threshold lets through.

### I3 — "inside the render silhouette" is an AABB test

The report: "*Through the decoded chain the hull sits inside the render silhouette with no fitting
parameter*". The oracle is `margin(hull_AABB, render_bounds_AABB)`: a box inside a box is not inside a
mesh. The doc is more careful ("render bounds"), the report is not, and the doc's verdict
"PROVEN within tolerance" never states what the tolerance for the *frame link* is. It is the margin set
itself: the positive margins (12.84–18.78 cm in X, 15.55/15.66 in Y, 0.22/9.87 in Z) bound the possible
frame error to under ~12.8 cm on X only *if* the hull is meant to be inside — they cannot confirm the
+5.0 cm offset to better than that. State it as a consistency bound on the decoded offsets, which is what
the numbers support.

### I4 — the battle-hull explanation is an unlabelled inference, and a competing one fits the same numbers

The card reports the battle hull overshooting the render bounds by 72.16 cm and explains it as
"*the battle-mode collision mesh is a bulked-up shape, not the render silhouette; this is a finding about
the battle shape, not a frame error*". Nothing decoded excludes the alternative: the battle hull belongs to
the **transformed** vehicle (tank/spread stance), while the comparison is against the **bind pose** of the
render mesh. The hull is 493 cm wide against a 349.5 cm bind-pose body — a spread stance is exactly what
would produce that, and it is not a property of "the shape being bulked up". Settling it needs the
transformed pose's bounds (`ANIMATIONS.md` pose states / the tank-spread anim), not more frame work.
Either label this an inference with the alternative named, or compare against the posed mesh.

### I5 — parameters the card calls "no fitting parameter"

Three component-transform fields are never given a value, only a rule: Rotation (absent tag → "default"),
**Scale3D** (absent tag → class default) and Translation (absent → inherit). The chain table has no Scale
column, the JSON's `scale_label` names no number, and the chain text says "a pure component-offset chain".
If any component's effective scale were not 1, the whole hull/bounds comparison changes. State
`Scale3D = (1,1,1)` and `Rotation = (0,0,0)` explicitly as `derived (absent tag at 424/412 + class
default)`, with the default's source (BMSDK layout / CDO), or decode the defaults. Same for the walk start
(`component_tags` searches 0..40 and takes the most tags): it is a parameter, corroborated by the exact
5 cm multiples and by COLLISION.md, which is good — say that, rather than "no fitting parameter".

### I6 — "decoded from the packages" overstates one link, and a supporting fact is available but uncited

- Criterion 1's heading says the chain is decoded from the packages, but the bone link comes from
  `BONES.json`, i.e. an umodel PSK export of the same SkeletalMesh. The report does disclose this in
  Limitations; the heading and the "Decoded chain" table do not.
- "Bone space and mesh space therefore coincide" additionally needs bone 0 to be a root. `BONES.json`
  records `bones[0].parent_index = 0` (self, i.e. no parent), which settles it — cite it. As written, U-2
  ("the record's parent-index field is unknown") makes it look as if the hierarchy is unknown when the
  PSK side already answers it (and see R1: the upk record's parent field is decodable too).

### I7 — minor wording

- The doc's "*Record layout fitted by oracle: FName (8 B), then quat at 16, translation at 32*" presents a
  layout the same sentence rejects (12/180). With R1 the sentence can state the proven record structure
  instead.
- Bone 0's numbers are rounded up in the report (`[2e-05, 0.0, 0.0]`, quat z `-2e-05`) versus the JSON
  (`1.5e-05`, `-1.9646e-05`). As a "< 2e-5" bound it is right; as a value it should be labelled rounded.

---

## 4. Resolvable UNKNOWNs (from the bytes — with how)

**R1 — U-2 is resolvable outright, and it pins the record layout the card calls UNKNOWN.**
The 44-byte ref-skeleton record, tested field by field against `BONES.json`'s 180 entries:

| field | result |
|---|---|
| @0 | FName index (record 0 = 200 → `Batmobile_Chassis`) |
| @4 | **`flags` 180/180** |
| @8 | **`parent_index` 180/180** (bone 0 → 0, self = root) |
| @12 | constant `0xFFFFFFFF` on the sampled records |
| @16 | 16 B quaternion (record 0 = (≈0, ≈0, ≈0, −0.99999994) = identity) |
| @32 | 12 B translation (record 0 = (0, −0.0, 0), vs PSK 1.5e-05 cm) |

That is `FName(8) + flags(4) + parent(4) + const(4) + quat(16) + translation(12) = 44`, which **confirms
the card's quat@16 / translation@32 by elimination** — the layout is no longer the open question. U-2 as
written ("the remaining 8 bytes: flags / parent index order") is closed; the card should record it as
decoded, with the 180/180 counts.

**R2 — U-1 narrows to a values problem, and one hypothesis is now rejected.**
With the layout pinned, the failure is in the values, not the field positions. I tested the obvious
alternative the card did not: comparing the stored transforms against `BONES.json`'s **world**
(`world_position_cm` / `world_rotation_quat`) rather than local bind transforms. Result: 2/180 exact
(card's local comparison: 12/180) — **worse, so "the record stores world transforms" is rejected**. That
is a useful negative to record. The remaining candidates worth testing are the quaternion's component
order/sign and whether the record stores component-space rather than parent-relative transforms — both are
one-line variants of the card's existing loop.

**R3 — "separate children of the vehicle" is decoded, not an assertion.**
All three component exports (5289, 5392, 5393) have `outer_index = 5281` = `Vehicle.Batmobile`, and none of
the nine tag streams carries an object reference to another component (no `AttachParent`-style link). So
siblings-under-the-actor is readable from the export table; the card can cite the outer index and drop the
wording's implied assumption.

**R4 — the inheritance chain is decodable, and it reaches the BmGame base exactly as the card assumes.**
The export record's archetype field (at `export_offset + (idx-1)*72 + 20`, which `upk_read` does not
parse) gives:

```
Playable 5289 → BmScript.Default__RVehicleBatmobile.SVehicleMesh   (Startup 169640)
Startup 169640 → BmGame.Default__RVehicleBatmobileBase.SVehicleMesh (BmGame 175716)
BmGame 175716 → Default__RVehicle.SVehicleMesh                      (BmGame 2268)
Playable 5392 → BmScript.Default__RVehicleBatmobile.BatmanCollisionMeshBattleMode0  (Startup 171103)
Startup 171103 → BmGame.Default__RVehicleBatmobileBase.BatmanCollisionMeshBattleMode0 (BmGame 176111)
Playable 5393 → …PursuitMode0 (Startup 171104) → …Base.…PursuitMode0 (BmGame 176112) → 0 (none)
```

So the card's "the instances and the Startup templates inherit the BmGame base value" is not merely the
rule COLLISION.md records — it is the decoded archetype chain, and the +5.0 cm result rests on a chain that
can be printed. Cite this instead of the rule.

**R5 — the battle-hull question is a pose question, not a frame question** (see I4). Settle by taking the
tank/spread pose bounds from `ANIMATIONS.md` and comparing the same hull against those; if the 493 cm width
matches the spread stance, the "bulked-up shape" wording should be replaced.

---

## 5. What the card gets right (so a fix does not disturb it)

- All nine component sizes, objects, classes and walk starts reproduce; the three base translations and the
  single rotator are exact, and the six "not serialised" verdicts rest on real parsed streams.
- The 20 MB SkeletalMesh and the 180/180 stride-44 name run are exactly as reported — a genuinely strong
  locator, verified independently.
- The pursuit-hull result is real: +5.0 cm relative offset and positive clearance on all six faces,
  arithmetic reproduced from the decoded inputs with no rounding drift.
- Honest disclosure of the bone-link substitution and of the rejected layout; the search really is recorded
  as UNKNOWN rather than dressed up (it is only the *check* that fails to test this, I1).
- `--check` does re-derive the whole document byte-identically and fails on any check; nothing is stale.

---

## 6. Required changes

1. Fix or remove the tautological check (I1) and stop counting it toward "7/7".
2. Re-label the chassis-box tolerance: it is a **chosen** 15 cm, or 17.48 cm = 5 % of 349.53; either way
   say so, and stop counting the chassis box as a proof of the frame link (I2).
3. Restate "inside the silhouette" as AABB-inside-AABB and give the frame-link consistency bound
   (~12.8 cm X) instead of "PROVEN within tolerance" (I3).
4. Label the battle-hull explanation a hypothesis and name the pose alternative (I4, R5).
5. State Rotation = 0 and Scale3D = (1,1,1) with their source, and call the walk start a parameter that is
   corroborated (I5).
6. Fix the "decoded from the packages" heading for the bone link and cite `BONES.json` `parent_index = 0`
   (I6).
7. Fold in R1 (record structure decoded), R2 (world-space rejected), R3 (outer index) and R4 (archetype
   chain) — all four make the record stronger, and three of them close or narrow the UNKNOWN list.
