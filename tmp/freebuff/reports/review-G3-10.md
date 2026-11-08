# Review of G3-10 - JC3 vehicle physics roles (`PHYSICS_ROLES.md` / `.json`)

Reviewer: independent pass, did not write the card. Read-only; no game launched or read, no git.
Card under test: `Research/JC3Grab/PHYSICS_ROLES.md`, `Research/JC3Grab/PHYSICS_ROLES.json`,
producer `Tools/scripts/jc3_physics_roles.py`.

## VERDICT: **minor issues**

Every number I re-read reproduces exactly - the object census, the system-data arrays, the two
static compounds, the 11 constraints, the 56 mass blocks, the 42-part body map and the whole fleet
census (232 files / 233 entries, all six min/median/max/n triples identical). The card's refusal to
name mass/inertia/constraint fields is, on the raw bytes, the *correct* restraint.

Two things need correcting before the card can be called settled:

- **U-4 in section 7 states a premise the bytes refute** ("the 24 raycast ids below 42 ... they
  address a different index space than the 18-value extern window"). They are ordinary entries of
  the same 62-entry body table, not a second space (evidence in Spot-check 6 and Resolvable U-2).
- **Section 2's entire 42-row table has no stated source.** The names, damage types and both body
  ids are decoded from `Research/JC3Grab/PARTS_TABLE.jsonl` (the grab's `.vmodc` decode,
  `donor_parts()` in the producer), *not* from the `.physicsc` the card decodes, yet section 8's
  oracle list never mentions that file and the rows carry no offset. Under the card's own definition
  ("`decoded` = read from the file (offset given)") these 168 labels have provenance only in code.

Beyond that the record is stale against its own successor: `Research/JC3Grab/PHYSICS_ROLES2.md`
(GRB-G3-10b, "deps: G3-10") already claims three of the four section-7 UNKNOWNs and the core of
sections 3-5; the card mentions it nowhere (`grep -c "PHYSICS_ROLES2\|G3-10b"` = **0**).

## Check output (verbatim)

```
$ uv run --with numpy python Tools/scripts/jc3_physics_roles.py --check
OK donor 430 objects / 42 parts / 11 constraints / 56 mass props; fleet 232 files
CHECK_EXIT=0
```

## Spot-checks (raw re-reads, my own parsing)

Donor resolved from the producer's own constant:
`Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc`
(project-relative, 340,368 B). `jc3hkx.Packfile(path).blob == file bytes` is `True`, so offsets below
are file offsets.

| # | Card value (section) | My re-read | Match |
|---|---|---|---|
| 1 | 340,368 bytes, 430 objects, 16 classes, exact per-class counts (sect. 1) | 340,368 B; 430 objects; 16 classes; `CPfxPartIndexProperty 98, hkRefCountedProperties 92, hknpShapeMassProperties 56, hknpConvexPolytopeShape 54, hkGeometry 36, hknpDynamicCompoundShape 20, +Data 20, hknpExternMeshShape 18, +Data 18, hkpLimitedHingeConstraintData 9, hknpStaticCompoundShape 2, +Data 2, hkpRagdollConstraintData 2, hkRootLevelContainer 1, hknpPhysicsSceneData 1, hknpPhysicsSystemData 1` | **yes** |
| 2 | `hknpPhysicsSystemData` @0xA0, extent 20912; arrays 42/42/42/62/11/276, inline | offset `0xa0`, extent `20912`; `array_10 {ptr 288,size 42,cap 42,owned True}`, `array_20 {4320,42,42,True}`, `array_30 {7008,42,42,True}`, `body_entries {11712,62,62,True}`, `constraints {18560,11,11,True}`, `array_60 {18832,276,276,True}` | **yes** |
| 3 | Static compounds 0x8F20 and 0xC570, 7 instances each (sect. 3) | `hknpStaticCompoundShape 0x8F20` extent 1104, instances **7**; `0xC570` extent 1104, instances **7** (`jc3hkx.decode_compound`) | **yes** |
| 4 | 11 constraints at 0x4DA80..0x4E740, extents 304 (9 hinge) / 416 (2 ragdoll) (sect. 4) | offsets identical in order; `hkpLimitedHingeConstraintData` 304 x9, `hkpRagdollConstraintData 0x4DF40/0x4E210` 416 x2; count `{LimitedHinge 9, Ragdoll 2}` | **yes** |
| 5 | 56 mass props, 48 B each; first blob @0x5970 hex + 14 floats (sect. 5) | 56 objects, `set(extent) = {48}`; raw `0x5970` = `39170d3e65f484bd5b037dbf79ee9bbf75f75b3f21e889bcc2e3023faa27e9bf75f75bbf26e889bcc2e3023fa927e9bfe074e8be3e39563f`, floats `[0.137784, -0.064919, -0.988332, -1.218215, 0.859245, -0.016834, 0.511288, -1.821523, -0.859245, -0.016834, 0.511288, -1.821523, -0.454017, 0.836811]` (byte-identical) | **yes** |
| 6 | Sect. 2 body map: 42 parts, 4 wheels world -1, 39 distinct world ids, missing [22, 23, 36, 37]; raycast 42 distinct, 18 in 42..59, 24 below 42 | `PARTS_TABLE.jsonl` row `..._sportsmuscle_civilian_01.ee`, module `sportsmuscle_vehicle_parts.vmodc`, 42 parts; `body==-1` exactly the four wheels; distinct world ids 39, min -1 max 41, missing `[22,23,36,37]`; ray distinct 42, below 42 = 24, window `42..59` (18 values) | **yes** |
| 7 | Fleet: 232 files, 233 entries; objects 22/524/1536, polytopes 2/70/245, extern 1/22/50, static 0/11/34 (224), dynamic 1/14/59, mass 2/80/271, hinges 0/8/57 (220), ragdolls 0/0/29 (36) | independent tally: 232 files, **233** entries; every min/median/max and every `n_with` identical (`224/233` static, `220/233` hinges, `36/233` ragdolls); extern <= polytopes in 233/233 | **yes** |

## Issues (file, value, why)

1. **`PHYSICS_ROLES.md` sect. 2, all 42 rows - decoded labels with no provenance.** The world body id,
   raycast body id, name and damage type come from `Research/JC3Grab/PARTS_TABLE.jsonl`
   (`donor_parts()`), a different file from the one under review. The md never names it and sect. 8's
   oracles list only the packfile. Nothing in the record lets a reader re-find the table, and the
   card's own definition ("read from the file (offset given)") is not met: a part index is not an
   offset. Fix: one sentence per column ("decoded: `PARTS_TABLE.jsonl`, entity
   `..._sportsmuscle_civilian_01.ee`, module `sportsmuscle_vehicle_parts.vmodc`").
2. **`PHYSICS_ROLES.md` sect. 7 UNKNOWN 4 - a refuted premise inside an UNKNOWN.**
   "the 24 raycast ids below 42 (they address a different index space than the 18-value extern
   window) and the ids missing from the world table - no decoder maps either to an object."
   The bytes do map them: entry 22 `@0x3600` shape `0xB5D0 hknpConvexPolytopeShape` at
   `(-1.208, 0.705, -2.570)`, entry 23 `@0x3660` at `(1.208, 0.705, -2.570)`, entry 36 `@0x3B40` at
   `(-1.285, 0.703, 2.459)`, entry 37 `@0x3BA0` at `(1.285, 0.703, 2.459)` - exactly the four wheel
   corners, and exactly the four ids the parts table records as the wheels' raycast bodies. 32, 33
   and 38 are likewise plain entries (polytopes of the signal/taillight/mirror parts). There is one
   62-entry index space. The "different index space" reading is the plausible-sounding invention the
   one rule forbids; it should be deleted, not deferred.
3. **`PHYSICS_ROLES.md` sect. 3 - "What references them is UNKNOWN: no pointer from a body entry to
   a compound is decoded."** It is decodable with the field the card already knows: the shape pointer
   is word 0 of each 96-byte body entry. Slots resolving to `0x8F20`: `0x33C0` (= body entry
   **16**, `sportsmuscle_front_bumper`) and the shape-table slots `0x4A10, 0x5078, 0x4C6E0`; to
   `0xC570`: `0x3780` (= body entry **26**, `sportsmuscle_rear_bumper`) and `0x4A60, 0x5128,
   0x4AD40`. The two static compounds *are* the bumpers, each 7 convex pieces - consistent with the
   card's own "7 front + 7 rear pieces" from the card text, but not decoded here.
4. **`PHYSICS_ROLES.md` sect. 4 - "Which bodies each joins is UNKNOWN - the layout of both classes is
   NAMED-ONLY."** The card had already located the constraint array (`constraints`, ptr 18560,
   11 x 24 B). Each record carries the joined body at **+0x08** (not +0x04, which is 0 in all 11):
   `1, 3, 4, 6, 7, 16, 18, 19, 20, 26, 35` for `0x4DA80 ... 0x4E740`, with `+0x0C = 0x7FFFFFFF`
   constant and `+0x10 = 0`. That is the door/mirror/bumper/hood/trunk set the successor card
   reports; the data was in hand and left unread.
5. **`PHYSICS_ROLES.md` sect. 5 - the recorded "first blob" overruns its object by 8 bytes.**
   The section says 48 bytes each, then records 56 bytes / 14 floats at `0x5970`. Extent is 48 for
   all 56 objects, so floats 13-14 (`-0.454017, 0.836811`, bytes `0x30..0x37`) belong to the
   following object - they must not be offered as the mass block's content.
6. **`PHYSICS_ROLES.md` sect. 5 / sect. 7 - successor conflict recorded as open, correctly left
   open here, but the card points at nothing.** `PHYSICS_ROLES2.md` (G3-10b) asserts a mass at
   `+0x28` with donor values `[800.0, 40.0, ...]`. At block `0x5970` the word at `+0x28` is
   `0.511288` (`39170d3e...` dump, byte-identical above) and block `0x5FC0` has `0.0` there, so that
   resolution does not survive a raw re-read of the same file at the same offset. G3-10's "no mass
   ... is read" is therefore still the defensible statement; the record should say so and name the
   successor, rather than leaving a reader to discover a contradictory card.
7. **`PHYSICS_ROLES.md` - no successor pointer (staleness).** G3-10b exists with `Out:
   PHYSICS_ROLES2.md` and `deps: G3-10`; `grep -c "PHYSICS_ROLES2\|G3-10b"` on the card = **0**.
   Sections 3, 4, 5 and 7 are claimed there, so the card's open list reads as current when it is not
   (one item, U-2 below, is genuinely resolved; two are resolved wrongly; the mass link is not
   resolved at all).
8. **`PHYSICS_ROLES.md` sect. 2 - "parts with no world body (`-1`)" is an interpretation, not a
   decode.** The field is a grab-side integer; the card reads `-1` as "no part-level world body".
   That reading is *supported* (those four parts are exactly the ones whose wheel colliders are body
   entries 22/23/36/37, all `hknpConvexPolytopeShape`), but it is stated as if decoded. Label it
   derived, with that correspondence as the oracle.
9. **`PHYSICS_ROLES.md` sect. 6 - "232 decode files, 233 vehicle physics entries" is unexplained.**
   Reproduced, and the extra entry is identifiable: one file carries two physics blocks
   (`editor__entities__jc_vehicles__02_air__v4603_plane_urga_cargotransport__..._military_cargo_tank.ee.json`).
   One clause would stop a reader treating 232/233 as a typo.
10. **sect. 7 UNKNOWN 1 - the 96-byte body entry fields.** Over-scoped rather than wrong: with the
    packfile's pointer slots, `+0x00` is the shape pointer (entries 16/26 -> static compounds,
    22/23/36/37 -> wheel polytopes) and `+0x30` is the translation triple with `w = 1.0` (the field
    `jc3hkx.stations()` already uses). Two of the "field names are not decoded" gaps are closed by
    data the card has.

Not issues (checked, hold): sect. 1's six arrays are all `owned: True`; sect. 4's "constraint array
size (11) matches the object count" (verified); sect. 6's "one `hknpPhysicsSystemData` per file" and
"extern meshes never exceed convex polytopes" (233/233, 0 violations); sect. 2's `range(42, 42+18)`
window equality; the missing world ids `[22,23,36,37]` being exactly the wheel raycast ids.

## Resolvable UNKNOWNs (and how)

- **U-2 (sect. 7, "24 raycast ids ... different index space"):** fully resolvable and already
  refuted - index body entries `11712 + 96*i` and read word 0 through `pf.pointers` plus the
  translation at `+0x30`. Done above: one space, both wheels' colliders are body entries.
- **U-3 (sect. 7, constraint axis/pivot/limits):** the joined body is a plain word at cinfo `+0x08`
  (issue 4). The axis/pivot *inside* the constraint objects remains open and I did not close it;
  the successor's per-offset float table is the next thing to test, and its 3x4-det oracle is a
  sound method.
- **U-4's second half ("the ids missing from the world table - no decoder maps either to an
  object"):** resolved by the same scan - 22/23/36/37 are body entries with polytope shapes at the
  four wheel corners, so the "missing" world ids are the wheels' own colliders, not a gap.
- **sect. 3 (what references the compounds):** resolved (issue 3) - entry `+0x00` of bodies 16 and
  26, plus the shape-table slots listed.
- **sect. 7 UNKNOWN 2 (mass/inertia/centre of mass):** *not* resolvable on the evidence I can see.
  `+0x28` does not hold a mass in this donor (issue 6); the 24 bytes at `+0x10..+0x27` are not
  IEEE floats. Any claim here needs a containment oracle (a decoded triple inside the owning hull's
  AABB), and no decoder in the tree does that yet.
- **sect. 7 UNKNOWN 1 (remaining body-entry words):** closable only by a domain census over the
  fleet bodies (the successor's approach); not closed here.

## What I did not verify

The three parsed-limit claims I left alone: whether `array_60` (276 entries, 8 B) is the shape
table, the fleet-wide `hknpDynamicCompoundShape` instance totals, and the card's `.json` key names
(I compared values, not the file schema). No game was launched or read; nothing under `E:/Games` or
`D:/Games` was written; no git operations; the only file written is this report.
