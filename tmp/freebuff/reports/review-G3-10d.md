# review-G3-10d · independent audit of the constraint-partner claim

**STATUS: done.** `review_g310d.py --check` exits 0 (18/18 oracles, md+json byte-identical to a
fresh rebuild from the install); the reviewed tool's own `--check` also passes. The oracle in
G3-10d **reproduces exactly** (188 measurable records, 0.351 pair rate at 5 cm, 0.005 shuffled
control, 2011 mass-linked hulls over 46 files, 1.327 inertia spread once its rounding is
re-applied), and the inertia UNKNOWN is **confirmed** against 13 candidate readings. But the
inference drawn from that oracle does **not** survive: the universal claim "the partner of every
constraint is body 0 (the chassis)" is contradicted inside G3-10d's own data by 65 of the 188
measurable constraints, the worst with its "A side" 6.19 m from the chassis. The script also
carries leftovers of two concurrent edits: eight fields/constants collected and never used, one
oracle that cannot fail, and a reading hard-coded into two analyses presented as
interpretation-independent.

## VERDICT

| question | answer |
|---|---|
| Does `jc3_physics_roles4.py --check` pass? | **yes** (exit 0, 10/10 oracles) |
| Do its published numbers reproduce? | **yes, to the digit** — 188 / 0.351 / 0.005 / 2011 / 46 / 1.327 |
| Is the script clean of two-version leftovers? | **no** — see §3 |
| Is `+0x04 = 0` really "body 0"? | **not supported as a fleet-wide partner**: 65 records make it impossible; body 0 anchors alone in only 25 records at 5 cm and never past 10 cm |
| Is the inertia UNKNOWN sound? | **yes** — no reading of 13 passes the bar (best 1.337 vs 1.15) |

One-line result: **the measurement is right, the conclusion is not.**

## Files written (only these)

| file | size | what |
|---|---|---|
| `Tools/scripts/review_g310d.py` | new | the review tool; `--write` regenerates both outputs, `--check` re-derives every rate, distance, spread and source-text count and fails on drift |
| `Research/JC3Grab/PHYSICS_ROLES4_REVIEW.md` | 16,562 B | the tables, the counterexamples, the script audit |
| `Research/JC3Grab/PHYSICS_ROLES4_REVIEW.json` | 33,819 B | the same, machine-readable, with every record's distances |
| `tmp/freebuff/reports/review-G3-10d.md` | this file | |

Read-only everywhere else: `jc3_physics_roles4.py`, `PHYSICS_ROLES4.md/.json`, `jc3hkx.py`,
`jc3_physics_roles2.py`, everything under `E:/Modding/_gamedata/` and `Builds/` untouched; no
game touched, no build, no commit. Scratch probes lived in `tmp/freebuff/scratch/`.

## Commands and outputs (verbatim)

```
$ python Tools/scripts/jc3_physics_roles4.py --check
OK cinfos 494 / hulls 2011 / fleet files 50; md+json byte-identical
oracles: {"body0_is_special": true, "cinfo_body_id_a_in_range": true, "cinfo_body_id_b_in_range": true, "donor_deltas_are_rotations": true, "donor_frames_ab_share_pivot": true, "inertia_best_spread_above_bar": true, "inertia_linked_hulls": true, "inertia_readings_measured": true, "pair_beats_control_5cm": true, "pair_control_is_low_5cm": true}
exit=0
```

```
$ python Tools/scripts/review_g310d.py --write
wrote Research/JC3Grab/PHYSICS_ROLES4_REVIEW.md and Research/JC3Grab/PHYSICS_ROLES4_REVIEW.json
files 50 | cinfos 494 | measurable 188 | hulls 2011/46
P(recorded body<=5cm) 0.766 | P(body0<=5cm) 0.484 | P(both) 0.351 | control 0.005
counterexamples 65 (recorded-body nearest 53), max |d to body 0| 6.19 m
inertia: 13 readings, min spread 1.337, any decodes False
oracles: 18/18
write exit=0
```

```
$ python Tools/scripts/review_g310d.py --check
check OK: 50 files re-parsed, 494 cinfos, 188 measurable, P(b)=0.766 P(a)=0.484 P(both)=0.351, 65 counterexamples, min inertia spread 1.337, md+json byte-identical
check exit=0
```

```
$ ls -l Research/JC3Grab/PHYSICS_ROLES4_REVIEW.*
-rw-r--r-- 1 User 197121 33819 Nov  3 08:02 Research/JC3Grab/PHYSICS_ROLES4_REVIEW.json
-rw-r--r-- 1 User 197121 16562 Nov  3 08:02 Research/JC3Grab/PHYSICS_ROLES4_REVIEW.md
```

## 1. The inference, attacked with its own oracle

G3-10d compares the pair (body 0, recorded body) against a *shuffled* body. That control is a
strawman: a random other body is usually a small part nowhere near the joint. The control that
decides between "`+0x04` is body 0" and "`+0x04` is a flag" is the recorded body **alone**, on the
same 188 records. Measured at four tolerances (decoded: signed distance from each record's stored
pivot to each body's decoded convex hull):

| tolerance | P(recorded body) | P(body 0) | P(both) | P(body 0 only) | P(neither) | shuffled | n |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.02 m | 0.575 | 0.170 | 0.074 | 0.096 | 0.330 | 0.000 | 188 |
| 0.05 m | **0.766** | **0.484** | **0.351** | 0.133 | 0.101 | 0.005 | 188 |
| 0.10 m | 0.963 | 0.543 | 0.543 | **0.000** | 0.037 | 0.016 | 188 |
| 0.20 m | 0.984 | 0.585 | 0.585 | **0.000** | 0.016 | 0.016 | 188 |

Three readings of this table:

1. **The recorded body fits better than body 0** at every tolerance (0.766 vs 0.484 at 5 cm). If
   `+0x04` were a real partner id, the two sides would be equally good fits; instead the recorded
   side is the one the pivot actually sits on.
2. **Body 0's independent contribution collapses with scale.** It anchors a pivot on its own in 25
   records at 5 cm (13 %), and in **zero** records past 10 cm. A genuine second body would be the
   near one exactly when the first is far from the joint; that never happens beyond 10 cm.
3. **The 66× headline is an artefact of the null.** 0.351/0.005 compares "two plausible bodies"
   against "one plausible body plus a random part". The honest ratio is 0.484/0.766 against the
   recorded body — i.e. body 0 is the *worse* fit of the two.

## 2. The counterexamples the card asked for

Constraints whose pivot is more than 0.20 m from body 0 while another body is within 5 cm:
**65 of 188 measurable records**, nearest body is the recorded one in **53**. All 65 sit in files
where body 0's transform is identity, so the measurement is same-frame (see §4).

| file | cinfo | A (word +0x04) | \|d\| to A (m) | B (word +0x08) | \|d\| to B (m) | nearest |
|---|---:|---:|---:|---:|---:|---:|
| `armoredtransport.physicsc` | 8 | 0 | **6.193** | 20 | 0.010 | 20 @ 0.010 |
| `armoredtransport.physicsc` | 7 | 0 | **6.192** | 18 | 0.010 | 18 @ 0.010 |
| `armoredtransport.physicsc` | 12 | 0 | **5.834** | 27 | 0.010 | 27 @ 0.010 |
| `armoredtransport.physicsc` | 14 | 0 | **5.834** | 30 | 0.010 | 30 @ 0.010 |
| `articulatedtruck.physicsc` | 4 | 0 | **5.275** | 20 | 0.010 | 20 @ 0.010 |
| `articulatedtruck.physicsc` | 5 | 0 | **5.017** | 25 | 0.010 | 25 @ 0.010 |
| `bavariumtank.physicsc` | 1 | 0 | **4.949** | 8 | 0.033 | 8 @ 0.033 |
| `apc.physicsc` | 11 | 0 | **4.340** | 22 | 0.011 | 22 @ 0.011 |
| `apc.physicsc` | 12 | 0 | **4.340** | 23 | 0.011 | 23 @ 0.011 |
| `armoredtransport.physicsc` | 11 | 0 | **3.340** | 26 | 0.010 | 26 @ 0.010 |
| `armoredtransport.physicsc` | 13 | 0 | **3.340** | 29 | 0.010 | 29 @ 0.010 |
| `apc.physicsc` | 10 | 0 | **2.746** | 15 | 0.027 | 13 @ 0.025 |

A two-body record whose A side is body 0 cannot have its A-side joint six metres outside the
chassis. The donor shows the same defect once at small scale: its ragdoll at
(0.031, 0.660, −2.389) is **1.187 m** from body 0's hull and 0.029 m from body 18. G3-10d records
that number in its own table and calls it *"a rear-mounted joint outside the chassis envelope"* —
which is the counterexample, filed as an aside.

What this refutes is the **universal** statement. What the bytes still allow is narrower: each
constraint names one body (`+0x08`) whose hull carries the pivot; body 0 is a plausible second
side for the subset whose pivot lies inside or on the chassis (0.543 within 10 cm); for the other
records the second side is not in any field decoded so far. `+0x04 = 0` is a constant, and
"constant body id vs constant flag" cannot be settled from shipping data — that part of G3-10d's
UNKNOWN is honest and stands.

## 3. Script hygiene: leftovers of two concurrent edits

Counted from the source text by the review tool (`--check` re-counts):

| token | occurrences | what it is |
|---|---:|---|
| `NO_BODY` | 1 | `0x7FFFFFFF` constant: defined, never compared |
| `quaternion` | 1 | body quaternion: collected, never read |
| `"position"` | 1 | body position: collected, never read |
| `word_0c` | 1 | cinfo `+0x0C`: collected, never read |
| `field_08` / `field_0c` / `field_10` | 1 each | body words: collected, never read |
| `pivots_equal` | 3 | computed, stored in JSON, used by no oracle |

Consequences, each verified rather than guessed:

- **An oracle that cannot fail.** `cinfo_body_id_a_in_range` tests `0 <= a < n_bodies`, which is
  vacuously true for `a == 0`. The report's "`+0x04` is 0 in 494/494" is prose, not an oracle.
  This review asserts it directly (it holds), along with `+0x0C == 0x7FFFFFFF` and
  `+0x10/+0x14 == 0`, which G3-10d's §1 table claims and never checks.
- **The missing frame check.** `position`/`quaternion` are collected and dropped. A version that
  transformed pivots into body frames would have needed them; the shipped data turns out to have
  body 0 at identity everywhere (3556 bodies, 447 non-identity, over 48 of 50 files, none of them
  body 0), so the omission does not change the numbers — but nothing in the code can tell a
  reviewer that, and for the 1 record whose recorded body is non-identity the `|d| to B` column is
  a cross-frame reading (187/188 are same-frame).
- **One reading hard-coded into two analyses.** `i16_16384` appears on 4 lines: once in the reading
  table and again inside the direction test and the per-slot correlation. Those two analyses are
  presented as properties of "the block" but are properties of one chosen scaling.
- **Six readings are fewer.** Scaling every int16 by one constant leaves max/min of the three
  ratios unchanged, so `raw`, `/16384` and `/32767` are the same test by construction (measured:
  max delta 0.0 across all triples). `u16` is genuinely different (delta 2.19). The table's six
  rows are 4 distinct tests; the conclusion is unaffected.
- **A frame-count artefact.** Two donor ragdolls yield a *third* 3×4 frame with pivot exactly
  (0, 0, 0) — the 16-float sliding-window detector picks up a zero-translation rotation inside the
  same object. "Frame counts 2 or 3" is a property of the detector, not the constraint, and it is
  why G3-10d's own `pivots_equal` is False on those records while `pivots_ab_equal` is True.
- **Prose vs table.** G3-10d writes *"every pivot is within 5 cm of its own body's hull except the
  two ragdolls on 7 and 18 (7.4 cm and 2.9 cm)"*. Body 18's own distance is 2.9 cm, i.e. **within**
  5 cm, and constraints 7 and 8 (bodies 19, 20) are at 5.54 cm, over the line and unmentioned. The
  bodies actually over 5 cm are 7, 19, 20.
- No duplicated function definitions: each `def` is unique. The damage is dormant fields and a
  mis-stated comparison, not two copies of a function.

## 4. Why the oracle is still usable (the frame premise)

`jc3hkx.decode_polytope` returns hull planes in the shape's own space; the pivot is a stored
translation. The comparison is only valid for a body whose transform is identity. Measured: 447
of 3556 bodies are non-identity, over 48 of 50 files, and **body 0 is identity in every file**.
So every `|d| to body 0` — the A side of every record and every counterexample above — is
same-frame. This premise is unstated in G3-10d and load-bearing for the side its claim depends on.

## 5. The inertia UNKNOWN, confirmed

Mass link reproduced: `polytope +0x20 → hkRefCountedProperties +0x10 →
hknpShapeMassProperties`, mass the f32 at `+0x28`, **2011** hulls over **46** files. Oracle: box
inertia from the hull AABB, requiring one constant scale per body (bar spread ≤ 1.15). 13
candidate readings — G3-10d's six plus 6×i32, 6×u32, 24×i8, 24×u8, 3×f64, 6×half: **none
decodes**. Best is `12 x int16` triple 4‑5‑6 at spread **1.337** (the card's 1.327 is that same
median with its 4‑decimal rounding of the box inertia re-applied: 1.3271), and the extra layouts
do not get closer. The UNKNOWN is sound and now harder to overturn — the card's per-slot hint
(slot 7 tracking mass, ρ 0.87) is reproduced but still not a layout.

## 6. What should change in the card

- The §2 headline should read: **one** body is recorded (`+0x08`); its hull carries the pivot
  (0.766 at 5 cm); `+0x04` is constant 0 and cannot be shown to be the partner — 65 records make
  "body 0" impossible there, and body 0 never anchors alone past 10 cm.
- `pair_beats_control_5cm` should be replaced by a recorded-body comparison; the shuffled control
  measures the wrong null.
- The 1.327 should be quoted as 1.337 with a note on the rounding, so a later reader does not
  chase a 0.01 discrepancy.

## UNKNOWN (what was tried, where it would be found)

- **The true second side of a constraint.** Not in any decoded field: `+0x00` is the
  constraintData fixup, `+0x04` constant, `+0x08` one body, `+0x0C`/`+0x10`/`+0x14` constant, and
  the body entry (96 B) carries no constraint list. Where it would be found: a body-side
  constraint array, or the engine's `hknpConstraintCinfo` reader (not in this tree).
- **What `+0x04 = 0` means.** Tried: all 494 records across 50 files, geometry against body 0
  alone, the pair, and a shuffled control. No shipped record varies the word. Where it would be
  found: a physicsc with a non-zero word, or the Havok class layout.
- **The 24 packed inertia bytes.** No layout of 13 reaches a constant per-body scale. Where it
  would be found: hull inertia integrated from face topology (`decode_polytope` exposes planes and
  vertices, not faces), or a Havok 2014 header.
- **Runtime meaning.** Every number is a file fact; no game was launched or attached to.
