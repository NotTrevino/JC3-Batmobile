# Independent review — G2-15 · Door-part animation (canopy, missile hatches)

Reviewer: independent pass, read-only (no file edited except this report). Card source:
`GRAB_BACKLOG.md` §6 `#### G2-15`, tracker row §12, MODLOG §"G2-15 · Door-part animation (canopy,
missile hatches) — done (2026-10-26)" (MODLOG.md:9800).

## VERDICT

**sound** — with 4 minor wording/provenance issues, none of which changes an answer.

The card's three questions are answered, every answer is backed by a decoded value, the doc is
generated (not hand-written) and `--check` byte-compares both outputs and re-asserts the invariants.
Nothing is presented as measured that is only inferred: the one inference the doc makes (the
`MissileHatch` trigger) is explicitly labelled as not in the files. The issues below are a handful of
typed numeric literals inside the generated prose and two sentences that claim slightly more than the
scan behind them.

Out paths: the card's `Out:` is `Research/JC3Grab/DOORS.md` — exists (10,386 B, 202 lines). The
tracker row also cites `Research/JC3Grab/DOORS.json` and `Tools/scripts/jc3doors.py`; both exist. The
tracker's evidence text matches the doc and the json in every number I checked.

## Check output (verbatim)

```
> python Tools/scripts/jc3doors.py --check
PASS: 4 samples, 224 door rows / 220 hinged / X 60, both entry paths 21
```

Exit code 0.

Independently reproduced in memory (no file written): `jc3doors.build()` equals the on-disk
`DOORS.json` (`rebuild equals disk: True`), `render_md(build())` equals the on-disk `DOORS.md`
(`md rebuild equals disk: True`), and `invariants(build())` returns `[]`. A simulated json tamper
(donor door `max_deg` 80 → 95) reproduces the MODLOG's recorded failure exactly:
`json section changed: samples`.

**Done-criterion match.** The card's Done is answer-shaped, not count-shaped, so the mapping is:
(a) transverse hinge → asserted by the census (`X (transverse)` > 0) plus the donor hood and medium
tank hatch axis classes; (b) what opens a `MissileHatch` → asserted by the monorail's 16 hatches,
their `MissileHatch` behaviour and 0..150° hinges, and `hatch_refs_outside_part_prop == []`; (c) does
entry open the door part → asserted by the donor's two entry paths, the APC/monorail absence, and the
donor container's 0 animation members. So each answer's *facts* are checked, and the prose cannot
drift from them because the whole md is re-rendered and compared.

## Issues

1. **minor (R11) — typed numeric literals inside the generated prose.** `DOORS.md:46` carries
   "`mediumtank_hatch` (0..130 deg) or `sportsmuscle_hood_signature` (0..70 deg)", `:96` and
   `:144` "0..150 deg about ±Z", `:143` "the monorail's 16 hatches", `:42` "eight per side". These
   are string literals in `render_md()` (jc3doors.py:349-352, :380, :440-444), not interpolations, so
   `--check` could not catch them going stale: `render_md` is both the source of the doc and the
   thing the check compares. `invariants()` covers some of them (tank 0..130, monorail `max_deg`
   150, `len(door_parts) == 16`) but not the donor hood's 0..70 or the 8/8 split. All values are
   **correct today** (verified below); the fix is to interpolate them from `d` like the rest of the
   table.

2. **minor (R4/R5) — one word overreaches the data.** `DOORS.md:46`: "60 of the 220 hinged door
   parts ... rotate about **X** - hoods, roof hatches and **canopies**". No part in the 78 cached
   modules is a canopy: the 60 X-axis rows are `Hood` (26), `Trunk` (19), `CargoBayDoor` (5),
   `FrontLeftDoor` (5, incl. the APC/tank hatches), `TurretDoor` (2), `RearDoor` (1),
   `CenterLeft/RightDoor` (1+1). "Canopies" is the reader's extrapolation (the thing B-05 will build),
   not a fleet part; the rest of the doc is careful to say "an ordinary `FrontLeftDoor`/`Hood` part".

3. **minor (R4) — "tilts forward" is not a decoded direction.** `DOORS.md:46`. The hinge axis proves
   a *pitch* hinge (rotation in the YZ plane), which is what a forward-tilting canopy needs; it does
   not establish which way the part swings — the limits are plain `0..70°` with no sign convention in
   any file read here, and the doc's own §5 says an angle is the authored limit. Fine as a design
   statement, but it sits in the sentence that presents the evidence.

4. **minor — the bold claim in (b) is stronger than the scan behind it.** `DOORS.md:104`
   "**Nothing in the entity opens them.**" The scan (`build()`, jc3doors.py:206-218) matches object
   *property values* that equal a hatch **part name**; an index-, hash- or id-based reference would
   not be seen. Likewise "no interaction entry for a hatch" is not asserted — the only monorail
   interaction check rejects entries containing the substring `door`. The paragraph immediately after
   (:106-110) states it correctly ("No object other than `CPartProp` names a hatch ... the opening is
   decided in code ... that inference is not in the files"), so this is a headline that should be the
   narrower sentence.

5. **nit (provenance of a definition).** `DOORS.md:3` defines a door as "a behaviour name in
   `vehicle_common.all_door_part_properties`", but `jc3doors.py` never reads `vehicle_common`; it
   trusts the module's `door_parts[]`. The premise is inherited from G2-14 and **cross-checked
   true**: all 14 behaviours in G2-15's census (incl. `LeftWing`/`RightWing`) carry
   `table: all_door_part_properties` in `MOVING_PARTS.json`. No action, just not re-derived here.

6. **nit (MODLOG only).** MODLOG.md:9823 lists the X-axis users as "hoods (26/26) ... 5 of 55
   FrontLeftDoor rows and 1 RearDoor" — that sums to 58, not 60; the missing two are
   `CenterLeftDoor` 1 and `CenterRightDoor` 1. The **doc's** numbers are right (60 = 26+19+5+5+2+1+1+1).
   Also MODLOG:9836 says the animation filter is "(`.ban`/`.anim`)", the code also tests `.sab`.

Nothing in the doc confuses a member's *name* with its *behaviour* (R5): it states up front that the
module stores no angle, speed, animation name or interaction, and treats the behaviour name plus the
`door_parts[]` index plus the `.physicsc` hinge as three separate carriers. The one place names are
used is the `MissileHatch` question, and there the doc says the name is not a trigger.

## Spot-checks

| # | value (doc) | where verified | result |
|---|---|---|---|
| 1 | donor `sportsmuscle_door_f_l`/`_f_r` ±Y `0..80°` at (±1.018, 0.622, −0.771); hood `+X 0..70°` at (0, 1.057, −0.848) (DOORS.md §1, :14-16) | `DOORS.json` `samples[donor].door_parts[*].hinge` (`axis [0,-1,0]`, `max_deg 80.0`, `pivot [-1.018,0.622,-0.771]`; hood `[1,0,0]` / `70.0`), i.e. the raw `hkpLimitedHingeConstraintData` fields at `0x30` axis / `0x60` pivot / `0xFC` limits | matches |
| 2 | monorail 16 `MissileHatch`, all `0..150°` about ±Z, "eight per side" (DOORS.md :17-42, :96) | `DOORS.json` hatch axes counted: `{(0,-0,-1): 8, (0,0,1): 8}`, every row `min_deg 0.0 / max_deg 150.0`, `class hkpLimitedHingeConstraintData` | matches (8 + 8) |
| 3 | "Across 55 cached entity graphs, 21 both, 0 door-only, 4 no-door-only, 30 neither" (DOORS.md :120-123) | independent **plain-text** scan of `E:/Modding/JustCause3/_grab/tmp/epe_cache/*.xml` (no project decoder): 55 files → both 21, door_only 0, no_door_only 4, neither 30 | matches exactly |
| 4 | "224 door rows in 56 of 78 modules, 220 hinged, X 60 / Y 132 / Z 28" (DOORS.md :46, table :49-52) | `DOORS.json` `census`; and an independent `jc3adf.walk` over the 78 cached `*_vehicle_parts.vmodc`: 78 modules, 56 with `door_parts[0].part_index`, **224** `door_parts[]` rows whose only sub-member anywhere is `part_index` (supports "stores only part_index") | matches |
| 5 | "4 door rows have `constraint_index` -1 ... propeller-wing parts" (DOORS.md :62) | `DOORS.json` `census.no_hinge` = exactly 4 rows, all `constraint: -1`: `privatepropeller_wing_cl1`, `privatepropeller_wing_cr1`, `smallfloatprop_wing_l`, `smallfloatprop_wing_r`; `other_classes {}` so all 220 others are limited hinges | matches |
| 6 | "donor's container is 566 members and holds 0 animation files" (DOORS.md :133-134) | `DOORS.json` `container` `{members: 566, animation_members: []}`; independent extension census of the donor `.ee` members: `.ddsc 116, .rbm 198, .lod 59, .vmodc 31, .trim 60, .effc 74, .ctunet 17, .etunec 2, .pfxc 4, .physicsc 1, .epe 1, ...` — **no** `.ban`/`.anim`/`.sab`/`.asb` at all, so the claim holds beyond the 3-extension filter | matches |
| 7 | medium tank `mediumtank_hatch` `FrontLeftDoor` +X `0..130°` at (−0.485, 2.921, 1.479) (DOORS.md :29) | `DOORS.json` `samples[mediumtank]` | matches |

Cross-card consistency (not required by the review, checked because it is cheap): `MOVING_PARTS.json`
(G2-14) independently reports `door_parts` **224 rows / 56 modules** and `MissileHatch` **16 parts /
1 chassis**, and lists all 14 door behaviours with `table: all_door_part_properties` — every census
number agrees.

One structural check worth recording: the constraint→part mapping (`part.constraint_index` indexes
the constraint list sorted by object offset, jc3doors.py:87-101) is plausible from geometry — left
hatches get the `-Z` hinge at x = −1.35 and right hatches the `+Z` hinge at x = +1.35, and the donor's
left door pivot sits at x = −1.018 — so the axes are attached to the correct side of each part.

## What was read

`GRAB_BACKLOG.md` §0.5 (R1-R14), §6 `#### G2-15`, §12 row; `MODLOG.md:9778-9855` (intended change and
done); `Research/JC3Grab/DOORS.md` (all 202 lines); `Research/JC3Grab/DOORS.json` (census, samples,
interactions); `Tools/scripts/jc3doors.py` (all 589 lines); `Research/JC3Grab/MOVING_PARTS.json` for
the door-behaviour table; the raw inputs under `E:/Modding/JustCause3/_grab/tmp` for the independent counts.
No game launched, nothing committed, no file edited except this report.
