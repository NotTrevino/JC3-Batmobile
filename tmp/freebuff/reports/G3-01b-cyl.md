# G3-01b (open item) — the two CylinderComponent floats, named

**STATUS: done**

Task: name the two `CylinderComponent` floats 78.0 / 175.0 that `Research/BatmobileGrab/COLLISION.md`
records at native offsets 540 / 544 and leaves UNKNOWN, using the cooked script packages (class +
property list, or the default object's serialized layout) or the executable (static only).

## Answer (decoded + derived, oracles stated)

| native offset | name | class default (decoded) | Batmobile value (decoded) |
|---:|---|---:|---:|
| 540 (0x21C) | **`CollisionHeight`** | 22.0 | 78.0 |
| 544 (0x220) | **`CollisionRadius`** | 22.0 | 175.0 |
| 548 (0x224) | `AABBScale` | 1.0 | not overridden |

Evidence chain (all from `Engine.upk`, nothing from engine knowledge):

1. Class export **4062 `CylinderComponent`**, super `PrimitiveComponent` (export 3119); ten member
   exports: 3 `FloatProperty` (`AABBScale` 4053, `CollisionRadius` 4054, `CollisionHeight` 4055),
   1 `StructProperty` (`CylinderColor` 4052), 4 `BoolProperty` (4048..4051), 2 `Function`.
2. Member linked list (int32 at +2 of each export): `GetExtent -> SetCylinderSize -> CollisionHeight
   -> CollisionRadius -> AABBScale -> CylinderColor -> bDrawBoundingBox -> bDrawNonColliding ->
   bAlwaysRenderIfSelected -> bForceGreenWhenSelected -> 0` — one unreferenced head, covers all
   ten, no cycle (oracle).
3. **Default object export 4063**, walked from byte 0: 10 tags, **114/114 bytes parsed, no tail**.
   FloatProperty tags at **540, 544, 548** (22.0, 22.0, 1.0), the class's only StructProperty at
   **552**, one BoolProperty word at **556**, then the inherited `PrimitiveComponent` members
   (316, 364, 476, 480, 484).
4. Which float is which:
   - No ancestor owns 540: the ancestors' own default objects top out at **528**
     (`PrimitiveComponent`) and **120** (`ActorComponent`).
   - The class has exactly **three** float members and exactly three float slots above that
     boundary: 540, 544, 548.
   - In the member chain the three floats come **before** the struct and the bools, and by type the
     struct is at 552 and the bool word at 556 — both above all three floats. So chain order =
     ascending offset order, and the floats pair in chain order:
     `CollisionHeight -> 540`, `CollisionRadius -> 544`, `AABBScale -> 548`.
   - The reverse reading is **refuted by the same bytes**: it would require the class's only
     struct (`CylinderColor`) to sit *below* all three floats, but its tag is at 552 > 548.
   - Containment: 540..559 inclusive = 20 bytes = 3×4 (floats) + 4 (struct) + 4 (bool word); no gap.
5. `COLLISION.md`'s attribution is corrected in the output: 78.0/175.0 are **not** in the Startup
   templates (82147/82148 serialise only `ReplacementPrimitive` + `PerInstanceRandom`); they are in
   the **BmGame base** templates 142597/142598, which Startup and the Playable instances inherit.

## What the earlier partial run got wrong (this task resumed from it)

- `COLLISION_CYLINDERS.md/.json` existed with **5/7 checks** and offset 540 unnamed. Cause: the
  default-object walk was filtered to "exactly 3 float tags", which selected **start 8** instead of
  start 0; that walk drops the 540 tag (and the CDO then showed 364/544/548 only). Fixed to the
  walk that consumes the whole export (start 0, 114/114).
- The same file carried a **self-contradictory exe paragraph** ("no instruction-pattern site met the
  strict test" followed by a radial/axial conclusion). Removed; the exe probe is now reported as
  contributing nothing.
- One "fleet invariant" idea of mine (`548 == 1.0` wherever serialised, i.e. a scale) was **tested
  and refuted** by the data (0.4 and 2.0 occur in Startup/BmGame). It is kept in the output as a
  refuted hypothesis and is **not** used as evidence.

## Files written (only these)

| file | change |
|---|---|
| `Tools/scripts/grab_collision_cylinders.py` | rewritten (untracked file created by this task's earlier partial run): corrected CDO walk, ancestor-bounded float-slot pairing, real fleet scan, honest exe probe, 9 checks |
| `Research/BatmobileGrab/COLLISION_CYLINDERS.md` | regenerated |
| `Research/BatmobileGrab/COLLISION_CYLINDERS.json` | regenerated |
| `tmp/freebuff/reports/G3-01b-cyl.md` | this report |

Nothing else was written; no game process was started, attached to or read; nothing under
`E:/Games` or `D:/Games` was modified; no git commit/push.

## Commands and outputs (verbatim)

```
$ cd /e/Modding/JustCause3/JC3-Batmobile && uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_cylinders.py --write; echo "WRITE_EXIT=$?"; uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_cylinders.py --check; echo "CHECK_EXIT=$?"
wrote COLLISION_CYLINDERS.json and COLLISION_CYLINDERS.md (10 members in the class chain, 9/9 checks, 540=CollisionHeight 544=CollisionRadius 548=AABBScale)
WRITE_EXIT=0
OK: 540=CollisionHeight 544=CollisionRadius 548=AABBScale, 9/9 checks, md+pairing byte-identical=True
CHECK_EXIT=0
```

Earlier diagnostic run that produced the decoded numbers used in the answer (package side only):

```
$ uv run --with ... python - <<'EOF'   # Engine.upk: class 4062/4063, all CDO walks, ancestor CDOs
class export 4062 cdo export 4063
class super_index 3119 -> PrimitiveComponent
  chain: (4062, 'CylinderComponent', 128, 3119, 'PrimitiveComponent')
  chain: (3119, 'PrimitiveComponent', 1016, 2634, 'ActorComponent')
  chain: (2634, 'ActorComponent', 164, -20, 'Component')
cdo size 114
start  0 -> 10 tags, end 112/114 (eof), floats [540, 544, 548, 364]
start  8 ->  9 tags, end 112/114 (eof), floats [544, 548, 364]
start 16 ->  8 tags, end 112/114 (eof), floats [548, 364]
start 24 ->  7 tags, end 112/114 (eof), floats [364]
CDO walk start 0: 10 tags, end 112/114 (eof)
  at   4 off  540 (0x21C) FloatProperty    22.0
  at  12 off  544 (0x220) FloatProperty    22.0
  at  20 off  548 (0x224) FloatProperty    1.0
  at  44 off  552 (0x228) StructProperty   CylinderColor
  at  52 off  556 (0x22C) BoolProperty     True
  at  76 off  316 (0x13C) ObjectProperty   ReplacementPrimitive
  at  84 off  364 (0x16C) FloatProperty    0.6479690074920654
  at  92 off  476 (0x1DC) BoolProperty     True
  at 100 off  480 (0x1E0) BoolProperty     True
  at 108 off  484 (0x1E4) BoolProperty     True
  tail bytes after terminator: 0000
PrimitiveComponent: class 3119 cdo 3120 size 225; walk 18 tags end 223/225 (eof)
   offsets: [316, 360, 364, 368, 372, 376, 424, 428, 476, 480, 484, 488, 500, 504, 516, 525, 527, 528]
   tag at 540: []
ActorComponent: class 2634 cdo 2635 size 30; walk 1 tags end 28/30 (eof)
   offsets: [120]
   tag at 540: []
```

(The `tail bytes after terminator: 0000` is `d[end:]`, i.e. the terminating int16 itself; the export
ends there, so the walk consumes 114/114.)

Executable probe (static, read-only, no launch/attach):

```
.text va 0x1000 size 0x1958a00 ; sites: 336 (0x21C 166, 0x220 170)
windows containing both displacements (<=160 bytes apart): 95
```

## Checks now in the output (9/9 PASS)

1. Engine.upk holds the class export and its ten members, typed
2. the member linked list covers all ten and ends at 0
3. the default object walks byte 0 to its last byte, carrying 3 floats, the struct and one bool word
4. no ancestor class serialises anything at or above 540 (PrimitiveComponent 528, ActorComponent 120)
5. the class's own float slots are exactly 540, 544, 548
6. the chain ascends with the offset (struct 552, bool word 556 above the floats)
7. the class block 540..559 is fully packed
8. **both asked offsets are named** (540 = CollisionHeight, 544 = CollisionRadius)
9. the Batmobile's base templates carry 78.0 at 540 and 175.0 at 544

## UNKNOWN (with what was tried)

- **Which bit of the bool word at 556 is which of the four bools** — the word is serialised once, so
  its members are not separable from this stream. Not needed by the card.
- **`CylinderColor`'s fields** (552) — named, not decoded; irrelevant to the two floats.
- **Whether `CollisionHeight` is half or full height in this engine** — the bytes state no
  convention, so no extents/bounds are claimed. The cylinders are named, not sized; COLLISION.md's
  stance is unchanged.
- **The executable's property-registration table** — not found. Tried: the `CollisionRadius` /
  `CollisionHeight` strings (0 ASCII, 0 UTF-16 hits), a movss displacement scan for 0x21C/0x220
  (336 sites, 88 same-base windows within 160 bytes) and the radial/axial vector test
  (X,Y from 0x220, Z from 0x21C) — 0 qualifying sites. Those displacements are ordinary struct
  offsets in this binary with no class anchor, so the exe contributes no naming evidence. Where a
  registration table would be: a `UProperty` offset table or a server-side constructor; neither was
  located in `BatmanAK.exe`.
- **The stream prefixes** (4 bytes on instances, 12 bytes on templates) — outside the tag stream this
  script walks; still UNKNOWN from COLLISION.md.
- **A scale-consistency argument for 548** — refuted (0.4, 2.0 occur), so deliberately not used.
- **The 54 fleet objects that serialise both 540 and 544** — recorded, but they do not decide which
  slot is radius (a cylinder's two lengths can stand in any ratio); no claim is made from them.
