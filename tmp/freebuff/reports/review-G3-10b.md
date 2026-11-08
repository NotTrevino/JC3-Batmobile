# review-G3-10b — JC3 Serpente physics decode (constraints, pivots/limits, 56 masses, body entries)

**VERDICT: needs rework (limits section).** The card's core values reproduce exactly from the raw
`.physicsc` bytes — the 11 constraint joins, all 56 masses, the body-entry translation/rotation,
the two static-compound body refs. But the "limits" column is presented as **decoded** and is
not: 34 of its 66 values are bytes of an already-decoded atom transform, and 24 are the pivot
re-listed. Under this project's rule ("a hypothesis only counts if it is proven against the bytes
with an oracle") that column must be relabelled `derived (value-band filter, unproven)` or
UNKNOWN. Two smaller data defects (mass census truncation, a 2e-6 sum) go with it.

`T-AU`-style consumption is not at risk: nothing downstream has used these limits.

## Files written (only these)

| file | what |
|---|---|
| `Tools/scripts/review_physics_roles2.py` | the review tool, `--write` / `--check` (new file; reads `jc3hkx.py` unmodified) |
| `Research/JC3Grab/PHYSICS_ROLES2_REVIEW.md` | the review tables |
| `Research/JC3Grab/PHYSICS_ROLES2_REVIEW.json` | same, machine-readable |
| `tmp/freebuff/reports/review-G3-10b.md` | this report |

Read-only: `Builds/test-091/…/sportsmuscle.physicsc`, `E:/Modding/_gamedata/JC3grab/hkx/all`,
`Research/JC3Grab/PHYSICS_ROLES2.json`/`.md`, `Tools/scripts/jc3_physics_roles2.py`. No game
touched, no build, no git action.

## Commands and outputs (verbatim)

```
$ uv run python Tools/scripts/jc3_physics_roles2.py --check
OK 11 constraints / 11 cinfos / 56 mass props / 2 compounds; fleet 40 files
TARGET_CHECK_EXIT=0
```

```
$ uv run python Tools/scripts/review_physics_roles2.py --write
wrote Research\JC3Grab\PHYSICS_ROLES2_REVIEW.md and Research\JC3Grab\PHYSICS_ROLES2_REVIEW.json
R1 ids match True | R2 values match True | core True
limits: 34/66 inside a transform, 24 pivot duplicates
verdict: needs rework (limits section) (3 issues)
WRITE_EXIT=0
```

```
$ uv run python Tools/scripts/review_physics_roles2.py --check
OK core=match; limits 24 pivot dups; one-side 384/384; md+json byte-identical
CHECK_EXIT=0
```

```
$ uv run python -c "import json;d=json.load(open('Research/JC3Grab/PHYSICS_ROLES2_REVIEW.json',encoding='utf-8'));print('verdict:',d['verdict']);[print(' -',i) for i in d['issues']];print('R2 sum',repr(d['R2_masses']['exact_sum']),'stored',d['R2_masses']['stored_sum'],'delta',d['R2_masses']['sum_delta'])"
verdict: needs rework (limits section)
 - the 'limits' column is a value-band float dump, not a decoded limit: 34 of 66 reported values sit inside an already-decoded atom transform, and 24 are a pivot component re-listed; the column must be relabelled derived/UNKNOWN
 - the mass census is silently truncated: the stored/printed dict covers 52 of 56 blocks and drops 4 distinct values (['0.003', '0.018', '275.0', '35.0'])
 - the quoted mass total 1627.097155 is the sum of per-block values rounded to 6 dp, not the exact float sum 1627.097153256 (delta -1.744e-06)
R2 sum 1627.0971532561816 stored 1627.097155 delta -1.744e-06
```

## The three re-derived values

All three were read from `Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc`
(2,757,558 B, packfile base 784) with my own `struct.unpack_from` reads, and compared to what
`PHYSICS_ROLES2.json` claims.

### 1. The cinfo body ids — `hknpPhysicsSystemData+0x50`, 11 × 24 B, word 2

| source | values |
|---|---|
| raw bytes (this review) | `[1, 3, 4, 6, 7, 16, 18, 19, 20, 26, 35]` |
| G3-10b stored JSON | `[1, 3, 4, 6, 7, 16, 18, 19, 20, 26, 35]` — **match** |

Records start at 0x4880 and are 24 B apart to 0x4970. Words 3/4/5 are the single triple
`(0x7FFFFFFF, 0, 0)` in all 11, i.e. the sentinel is real, and `--check` (its own) confirms the
pointer bijection onto the 11 constraint objects.

### 2. The 56 masses — `hknpShapeMassProperties+0x28`

| check | value |
|---|---|
| blocks re-read | **56**, every per-block float equal to the stored one (`values_match True`) |
| exact float sum | **1627.0971532561816** |
| stored sum | **1627.097155** → delta **−1.744e-06** |
| full census | **16** distinct values: `1.0×17, 25.0×10, 5.0×6, 40.0×4, 30.0×2, 0.002×2, 0.006×2, 0.009×2, 0.005×2, 0.012×2, 0.004×2, 800.0×1, 275.0×1, 0.003×1, 0.018×1, 35.0×1` |
| stored census | 12 entries covering **52** of 56 blocks; drops `275.0, 35.0, 0.018, 0.003` |

So the mass field, its offset and its authored-discrete character are right; the **sum** is the
sum of 6-dp-rounded values (the tool rounds each mass before summing), and the **census in both
`.md` and `.json` is truncated** (`distinct[...][:12]`) without saying so — the printed dict
sums to 52, not 56, so it cannot be the census it is presented as.

### 3. Body entry 22 — `+0x30..+0x3C` (and the compound shape pointers)

| source | translation (x, y, z, w) |
|---|---|
| raw bytes, body table at 0x2DC0 + 96·22 | `(-1.208, 0.7047, -2.57, 1.0)` |
| G3-10b stored JSON | `(-1.208, 0.705, -2.570)` — **match** (6-dp rounding) |

Same pass: body 16's shape pointer is `0x8F20` (`hknpStaticCompoundShape`) and body 26's is
`0xC570` (`hknpStaticCompoundShape`), and the reverse pointer map gives body refs `[[16], [26]]`
— exactly the card's §5 claim. Body 22's shape is `0xB5D0` (`hknpConvexPolytopeShape`).

## "One side per constraint" — does it still hold after G3-10c?

**Yes, and it is stronger than when G3-10b wrote it.** Three independent reads now agree:

1. **The record itself** — all six words of every cinfo in the donor: word 3 is `0x7FFFFFFF`,
   words 4 and 5 are `0`, word 2 is the only body id. Across the fleet the set of words 3/4/5 is
   the single triple `(0x7FFFFFFF, 0, 0)`, and there are **0 null cinfo pointers** in 40 decoded
   files.
2. **The pointer graph** — exactly **one** fixup targets each constraint data object: 11/11 in the
   donor (`0x4DA80→0x4880`, `0x4DBB0→0x4898`, …, i.e. only its own cinfo record) and
   **384/384** constraint objects across the fleet. If a second body were stored anywhere as a
   pointer into the constraint, this count would be ≥ 2.
3. **G3-10c's independent six-word dump** reaches the same conclusion, and adds the type tag at
   +0xC0.

So the card's reading is right as a statement about **storage**: one side per cinfo record. It is
*not* a claim that the joint has one body — the physical hinge still joins a part to something;
what that something is remains UNKNOWN, and both cards say so (G3-10b's UNKNOWN-2, G3-10c's
UNKNOWN-1). The only wording risk is the column header "joins body N", which reads like the
complete join; "stored body id" would be exact.

## The defect that drives the verdict: the "limits" column

The tool collects limits as *any float in the last 40 floats of the object whose absolute value is
in (0.01, π+0.01]*. For the 304-byte hinge objects that window starts at `+0x90`, while the second
atom transform occupies `+0x70..+0xA8`. So the window overlaps bytes the same tool already decoded
as a rotation and a pivot.

| constraint | reported limits | inside a decoded transform | pivot re-listed |
|---|---:|---:|---:|
| `0x4DA80` LimitedHinge | 6 | 3 | 3 |
| `0x4DBB0` LimitedHinge | 6 | 3 | 3 |
| `0x4DCE0` LimitedHinge | 6 | 3 | 3 |
| `0x4DE10` LimitedHinge | 6 | 3 | 3 |
| `0x4DF40` Ragdoll | 6 | 3 | 0 |
| `0x4E0E0` LimitedHinge | 6 | 3 | 3 |
| `0x4E210` Ragdoll | 6 | 3 | 0 |
| `0x4E3B0` LimitedHinge | 6 | 3 | 3 |
| `0x4E4E0` LimitedHinge | 6 | 3 | 3 |
| `0x4E610` LimitedHinge | 6 | 3 | 3 |
| `0x4E740` LimitedHinge | 6 | 4 | 0 |
| **total** | **66** | **34** | **24** |

Concretely, the left-door hinge row prints `+0x0A0=-1.018478, +0x0A4=0.622335,
+0x0A8=-0.771416` as "limits", and the same row's pivot (decoded 16 bytes after the rotation at
`+0x070`) is exactly `(-1.018478, 0.622335, -0.771416)`. The 42 values outside a transform may
well include real angles (`1.396263` = 80.0°, `0.523599` = 30.0°, `0.261799` = 15.0° are
plausible), but nothing in either card proves which field they are: the card's own §8 calls them
"limits read at measured offsets", which is a decode claim its method does not support.

## Other issues (minor)

1. **Mass census truncation** — `distinct[...][:12]` in the tool, printed and stored as if complete;
   covers 52/56 blocks and drops 4 distinct values (above).
2. **Mass total precision** — `1627.097155` is the sum of per-block 6-dp-rounded masses; the exact
   float sum is `1627.0971532561816` (delta −1.744e-06). Small, but the number is quoted as exact.
3. **Docstring claims an oracle that never ran** — the module docstring says the mass "rank-correlate[s]
   with the owning hull's AABB volume", while §2/UNKNOWN-4 of the same card correctly say the
   mass↔hull oracle could not be run (0 of 56 resolved). G3-10c has since decoded the link
   (54/54 via `polytope+0x20 → hkRefCountedProperties → +0x10`) and measured the correlation, so
   the claim is not wrong today — but at the time of writing the docstring asserted a check the
   report says was not performed.
4. **The fleet cinfo oracle is weaker than its name** — `cinfo_ok` skips null pointers (`if p`)
   and compares `a50["size"] == len(cons)`, so it cannot catch a null (measured: 0) or a duplicate.
   The donor oracle (sorted pointers == sorted constraint offsets) is the strict one and does pass.
5. **Column wording** — "joins body N" should be "stored body id" (see above).

## What holds (so a rework can be local)

- 11 constraints, 11 cinfos, 24-byte stride, true bijection, one body id each, sentinel
  `0x7FFFFFFF`, tail zeros — re-derived and consistent with G3-10c.
- All 56 mass floats at `+0x28`; positivity; authored-discrete values (16 of them).
- Body-entry translation/rotation fields, the four wheel-corner bodies (22/23/36/37), the
  "no second id space" conclusion, and the two static compounds at bodies 16 and 26.
- Fleet invariants over 40 decodable raw files (41 present; `town_01_ai_junction.physicsc` has 0
  system datas, which the card states).

## UNKNOWNs of this review

- **Which tail value is really a limit.** Not resolved here either. The tail window overlaps the
  atom transforms, so separating a limit field from transform bytes needs the
  `hkpLimitedHingeConstraintData` / `hkpRagdollConstraintData` layout, or a round trip against a
  constraint whose angle is known from the `.ee` entity. The 32 values outside the transforms are
  angle-plausible but unproven.
- **The partner body.** Confirmed absent from the cinfo (donor + fleet) and from the pointer graph;
  where it lives is still unknown. G3-10c points at the body table's `+0x20` graph or the `.ee`
  constraint list; neither is decoded.
- **Whether `+0x28` is a mass in kg.** The card labels the unit a hypothesis and this review does
  not test it; only "positive and authored" is re-derived.
- **Fleet depth.** 40 raw files, not the 232-file `hkx/out` corpus (summaries only) — unchanged
  from the card, and the reason the fleet invariants are 40-file invariants.
