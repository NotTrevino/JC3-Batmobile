# AUDIT-G3-01b — audit of COLLISION_GEOM.md against the later collision cards

**STATUS: done**

Deliverables (only these were written):

| path | what |
|---|---|
| `Tools/scripts/audit_g301b.py` | the audit tool (`--write` / `--check`) |
| `Research/BatmobileGrab/AUDIT_G301B.md` | 278 lines, 17/17 checks, `--check` exit 0 |

Nothing else was edited. All 13 audited inputs (9 cards + 4 reviews) are pinned by size + sha256 + date in
§1 of the output, so `--check` fails if any of them changes.

---

## 1. Answers to the three questions

### (1) Does COLLISION_BOXES settle the chassis/weapons boxes and the extents convention?

**Yes, both halves, and the numbers still agree.** `COLLISION_BOXES.md` decodes the chassis **2** boxes and the
weapons **1** box inside byte-mapped payloads (**1759/1759 B** and **143/143 B**, footer 9 B), so the box
inventory is no longer a claim about the header: the payload header's `box_count` (2 / 1) equals the decoded
element count. The element struct is **0x50** bytes with the extents as `FloatProperty` tags at
**0x40/0x44/0x48** and a bool word at **0x4C**, and the convention is decided as **FULL lengths** (worst
deviation 0.150 full vs 0.575 half against the tight hull; containment 28.1 cm vs 359.7 cm).

The three boxes' values match exactly at the printed 3 d.p.: max absolute difference **0.0000 cm** on extents
and **0.0000 cm** on centres. At the byte map's extra digit the largest gap is 345.6876 vs 345.688 (0.0004 cm).

The centres were the one item whose *label* was too strong in G3-01b (an inherited rule, not a decode);
`COLLISION_BOXES` now reads them from the TM's translation (floats 13..15), which agrees on all three boxes —
so the value survives and the label is now earned.

### (2) Are the `Batmobile_V3_Physics` bodies decoded later, or still open?

**Decoded later — the bodies are not open. The constraint and the bounds are.**

| object | later decode | state |
|---|---|---|
| body 169750 (`Batmobile_Chassis`, 1759 B) | BOXES byte map + SHAPES counts `[0,2,0,1]` | decoded |
| body 169751 (`Batmobile_Rig_Weapons_Trans`, 143 B) | BOXES byte map + SHAPES counts `[0,1,0,0]` | decoded |
| the 3 box records | BOXES: TM + 0x40/0x44/0x48 + 0x4C + end, 118 B each | decoded |
| 0x4C word | BOX_FLAGS: bit 6 = `bInterVehicleCollision`, 5 boxes / 4 bodies | name decoded (SDK layout + census), behaviour UNKNOWN |
| 169750's single convex element | BOXES (G3-01c layout), `ElemBox == vertex bounds` | decoded |
| constraint 171462 | **no later card** | UNKNOWN (offset names) |
| PhysicsAsset `Bounds` (72 B), StaticMesh `Bounds` | **no later card** | UNKNOWN (layout) |

### (3) Which points of the four G3-01b reviews did the later cards fix?

**8 fixed, 1 moot, 22 still open** (31 review points). The fixed ones: the 10894 selector reference (mode
review I1, the only *blocking* point), the 0x4C name, the sphyl count, the centres' label, the element chain,
the oracle, the hull provenance, and the header-word model. The moot one is the boxes review's report-wording
point (the `.md` already carries the `derived:` label it asked for).

Two findings worth flagging:

- **A reviewer's proposed fix is not accepted by a later card.** The boxes review (I-3) argued the 4° tilt's
  sign is fixed because the planes are rows; `MATRIX_ORDER.md` (newer) reports **row/column order UNSETTLED**
  and calls the one candidate case empty. So `COLLISION_BOXES.md`'s conditional ±4.00° is the correct state.
- **The boxes/cylinders reviews were never answered in their own artifacts.** `COLLISION_MODES.md` still
  prints its three UNKNOWN verdicts even though the selector is decoded elsewhere, and `COLLISION_BOXES.md`
  still contains the "12 bytes before the tag stream" mis-wording the review flagged.

---

## 2. Labels for every value used

| value | label |
|---|---|
| box extents / centres as printed in GEOM and BOXES | **decoded** (FloatProperty tags 0x40/0x44/0x48; TM translation floats 13..15) |
| agreement 0.0000 cm / 0.0000 cm | **derived** (arithmetic on the parsed card values) |
| 1759/1759, 143/143 B byte maps | **decoded** (BOXES) |
| 131/131 orthonormal, det +1 | **decoded** (BOXES) |
| `[0,2,0,1]` / `[0,1,0,0]`; sphyl count at 244 / 126 | **decoded** (SHAPES) |
| bit 6 = `bInterVehicleCollision`, 5 boxes / 4 bodies | **decoded** census; the **name** is from the SDK layout, not from the bytes |
| constraint 171462 offsets 84/92/100/144/156/168 | **decoded** (GEOM only); its **field names UNKNOWN** |
| Bounds arrays (PhysicsAsset 72 B; StaticMesh 175973/175974) | **UNKNOWN** (no layout; SDK tree has none either) |
| 4.00° about Y | magnitude/axis **decoded**, sign **UNKNOWN** (rows vs columns) |
| which component is attached per mode at runtime | **UNKNOWN** (setter branch decoded; no attachment logged) |
| 8 fixed / 22 open / 1 moot | **derived** from the status table |
| each status word | judgement **derived** from the cited evidence substring |

---

## 3. Commands run (with output)

All from `E:/Modding/JustCause3/JC3-Batmobile`.

**(a) File dates, to establish which card is "later"**

```
$ ls -l --time-style=+%Y-%m-%d_%H:%M Research/BatmobileGrab/{COLLISION_GEOM,COLLISION_BOXES,COLLISION_CONVEX,COLLISION_CYLINDERS,COLLISION_MODES,COLLISION_SHAPES,BOX_FLAGS,MATRIX_ORDER,COLLISION_SELECTOR,SELECTOR_POLARITY}.md
-rw-r--r-- 1 User 197121 21084 2026-11-04_14:43 Research/BatmobileGrab/BOX_FLAGS.md
-rw-r--r-- 1 User 197121 20182 2026-11-03_02:47 Research/BatmobileGrab/COLLISION_BOXES.md
-rw-r--r-- 1 User 197121 13994 2026-11-03_01:59 Research/BatmobileGrab/COLLISION_CONVEX.md
-rw-r--r-- 1 User 197121 12938 2026-11-03_03:43 Research/BatmobileGrab/COLLISION_CYLINDERS.md
-rw-r--r-- 1 User 197121  4937 2026-11-03_01:16 Research/BatmobileGrab/COLLISION_GEOM.md
-rw-r--r-- 1 User 197121  4128 2026-11-03_02:18 Research/BatmobileGrab/COLLISION_MODES.md
-rw-r--r-- 1 User 197121 11675 2026-11-03_06:06 Research/BatmobileGrab/COLLISION_SELECTOR.md
-rw-r--r-- 1 User 197121 11617 2026-11-04_12:43 Research/BatmobileGrab/COLLISION_SHAPES.md
-rw-r--r-- 1 User 197121 10979 2026-11-04_15:14 Research/BatmobileGrab/MATRIX_ORDER.md
-rw-r--r-- 1 User 197121  8133 2026-11-04_22:13 Research/BatmobileGrab/SELECTOR_POLARITY.md
```

**(b) First build — my bug (int tested against a string)**

```
$ python Tools/scripts/audit_g301b.py --write
Traceback (most recent call last):
  ...
TypeError: 'in <string>' requires string as left operand, not int
```

Fixed: the 171462 presence test now uses the string `"171462"`.

**(c) Second build — citation validation caught a bad citation of mine**

```
$ python Tools/scripts/audit_g301b.py --write
FAIL: citation validation failed:
  M7: '### UNKNOWN' not in Research/BatmobileGrab/COLLISION_CONVEX.md
```

Fixed: the heading is `## UNKNOWN`. (This is the guard working: a claim whose evidence substring is absent
aborts the build rather than printing.)

**(d) Third build — written and verified**

```
$ python Tools/scripts/audit_g301b.py --write
WROTE Research\BatmobileGrab\AUDIT_G301B.md (275 lines)
$ python Tools/scripts/audit_g301b.py --check
AUDIT_G301B.md current (275 lines, all checks pass)
```

**(e) Read-back found three presentation defects** (unescaped `|` in two table headers/cells, a lost space
rendering as `-box`, and `REF` where `COLLISION_BOXES.md` was meant), plus two over-claims in prose
("settles all three" and a precision figure I had not computed). Fixed all five in the script.

**(f) Final build, check, and defect scan**

```
$ python Tools/scripts/audit_g301b.py --write
WROTE Research\BatmobileGrab\AUDIT_G301B.md (278 lines)
$ python Tools/scripts/audit_g301b.py --check
AUDIT_G301B.md current (278 lines, all checks pass)
$ grep -n "|diff|\|^-box\| in REF \|1.3e-04" Research/BatmobileGrab/AUDIT_G301B.md
(no output; exit 1 = no match)
```

**(g) Protected inputs unchanged**

```
$ ls -l --time-style=+%Y-%m-%d_%H:%M Research/BatmobileGrab/COLLISION_{BOXES,CONVEX,GEOM}.md tmp/freebuff/reports/review-G3-01b.md
-rw-r--r-- 1 User 197121 20182 2026-11-03_02:47 Research/BatmobileGrab/COLLISION_BOXES.md
-rw-r--r-- 1 User 197121 13994 2026-11-03_01:59 Research/BatmobileGrab/COLLISION_CONVEX.md
-rw-r--r-- 1 User 197121  4937 2026-11-03_01:16 Research/BatmobileGrab/COLLISION_GEOM.md
-rw-r--r-- 1 User 197121  7440 2026-11-03_03:24 tmp/freebuff/reports/review-G3-01b.md
```

Dates and sizes are the pre-task values; the sha256 in the output's §1 pins all 13 inputs.

---

## 4. Limitations

- **This is a document-level audit.** I parsed the cards and reviews; I did not re-open `BmGame.upk` or re-run
  `grab_collision_boxes.py --check` / `grab_collision_convex.py --check` in this task. Every "decoded" value
  above is decoded *in the card cited*, at the offset the card states; the audit's own new arithmetic is the
  GEOM-vs-BOXES comparison. That comparison is exact at printed precision, so a mis-transcription between the
  two cards is ruled out, but a shared decoder bug would not be.
- **A status is only as good as "later".** Ordering uses file mtimes (listed in §1 of the output); if a card is
  regenerated, `--check` fails on the changed sha and the ordering must be re-read.
- **The 0x4C name is not byte-derived.** `bInterVehicleCollision` comes from the BmSDK-AK layout, as BOX_FLAGS
  states; the bytes give the offset and the bit, not the name.
- **The mode → mesh step stays UNKNOWN.** The setter's branch polarity is decoded (4/4 decisive), but no card
  observes which component is attached, so "mode 2 = battle mesh live" is still an inference from the
  value → mesh table.

## 5. Revert

```bash
rm Research/BatmobileGrab/AUDIT_G301B.md Tools/scripts/audit_g301b.py tmp/freebuff/reports/AUDIT-G3-01b.md
```

No input was modified, so nothing else needs reverting.
