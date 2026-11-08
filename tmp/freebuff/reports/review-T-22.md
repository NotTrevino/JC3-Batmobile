# Review — T-22 · Collision translation

Reviewer: independent pass, read-only. Nothing under `Research/`, `Tools/`, `Working/` or either game
folder was edited; no game was launched; no commit. Card: `GRAB_BACKLOG.md` §0.5 / §1.9 / §12 line
1331, card at lines 967-971. Outputs reviewed: `Working/Translation/t16_collision.json`,
`Tools/scripts/t22_collision.py`, rows `T-P3` (`T1_TRANSLATION.md:167`), `T-CO2`/`T-CO3`
(`T2_TRANSLATION.md:168-169`), `T2_TRANSLATION.md:160` (§7 prose), and the MODLOG block
"T-22 · Collision translation — done".

## VERDICT: minor issues

The card reproduces and nearly every number in it re-derives from the raw files; the reader work is
real (I re-decoded the donor with `jc3hkx` and get the same 22 compounds / 54 hulls / 40 bound /
14 unbound / extents 400-1776 B / 8-36 v / 5-47 p / radius median 0.01 m, min 0.002436 m /
max 0.01 m, and 0 station quads). The three rows exist, are ledger-consistent, and the dispositions
are the ones the card names. Three issues are substantive enough to fix before B-10 reads the rows;
none of them invalidates the json, which records the underlying fact in each case.

## Check output (verbatim)

```
$ python Tools/scripts/t22_collision.py --check
PASS: 32 BmAK bodies | 7 mapped / 21 unmapped | 54 donor hull slots, one per part | 38/42 parts collide | rows 3 (next 2, keep 1) | stations unchanged
EXIT=0
```

This is byte-identical to the line quoted in the MODLOG done block. Neighbouring gates (not asked
for by the card, run to test the "every gate re-run" claim):

```
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok  (exit 0)
$ python Tools/scripts/status_audit.py --check
STATUS.md is current  (exit 0)
```

Note the counts have moved since the MODLOG block was written (`blocked 14 out 35` there,
`13 / 36` now) - a later card advanced one row. Nothing in T-22's three rows changed, and the gate
is green.

## Out paths and Done criterion

- `Working/Translation/t16_collision.json` — exists, 14 top-level keys.
- Rows — `T1_TRANSLATION.md:167`, `T2_TRANSLATION.md:168`, `:169`; three `T_ROWS.jsonl` records
  (`T-P3` doc T-1 `next`, `T-CO2` doc T-2b `next`, `T-CO3` doc T-2b `keep`).
- `Tools/scripts/t22_collision.py` — exists, `--check` exit 0.
- Done ("rows resolved; or closed as named omissions if G2-30 failed"): the check re-derives the
  three row lines, the json, the §7 prose sentence and the ledger dispositions, so "rows resolved"
  is gated - but only as *self-consistency*: the dispositions `next/next/keep` are a typed literal
  in `summary.dispositions` (t22_collision.py:328-330 region) and the row text is regenerated from
  the build, so `--check` cannot distinguish "resolved" from "regenerated wrong". Same pattern as
  T-18/T-20; worth saying out loud, not a defect on its own.

## Issues

### 1. `T-CO2`'s "fits one donor hull" is not what the card's own hull set does (R4) — fix before B-10

`T2_TRANSLATION.md:168`, generated at `t22_collision.py:446-447`:

> `3.1615x0.6342x1.0988 m fits one donor hull (longest hull axis 3.679 m)`

and the MODLOG repeats it as "fits one donor hull (longest hull axis 3.679 m) - no layout change".

The 3.1615 m box is `SUSP1_Wheel_Rear_Left_Mesh`. In this same json that bone does not go into the
3.679 m hull at all: `hull_set.parts` gives it `target_part: sportsmuscle_wheel_r_l`, whose donor
hull is `0.2958 x 0.8225 x 0.7822 m` (0.2958 m is 9 % of the box's 3.1615 m long axis; the hull's
longest axis, 0.8225 m, is 3.8x shorter than it), and records it as `folded_bones: ["SUSP1_Wheel_Rear_Left_Mesh"]` on the 0.9761 x 0.5534 x 1.0153 m
`Wheel_Back_Left_Vis_Mesh` entry. So the box the row names is the one the card *drops*, and 3.679 m
is the body hull's `z`, not the hull that would host it.

The test itself is also scalar, not axis-wise: `max(max(h['box_precise']) for h in
donor['hulls_by_part'])` (t22_collision.py:448) compares the box's largest extent to the largest
extent of *any* hull. Against the body hull that is 2.085 x 1.212 x 3.6788, the box's 3.1615 m only
"fits" if its long axis is aligned with the hull's `z` - an orientation the check never tests. The
conclusion "no layout change" therefore does not follow. The honest statement, which the json
supports, is: *the four suspension-arm boxes (211.5-316.2 cm) have no hull of their own; they are
folded into the wheel hull, i.e. that extent gets no collision and the sim covers suspension travel.*
That is a build decision for B-10, and it should be named as one (R4), not converted into a fit.

### 2. `hulls_per_part: 1` / "one per part" is contradicted by the same file on 2 of 42 parts

`t22_collision.py:334` (`dec["hulls_per_part"] = 1`, typed), PASS line at `:545` ("54 donor hull
slots, one per part"), `GRAB_BACKLOG.md:1331` ("54 hulls, one per part"), MODLOG ("One hull per
part"). The donor has 40 hulls bound to parts, and `donor_parts` itself shows
`hulls: 0` for `sportsmuscle_front_bumper` and `sportsmuscle_rear_bumper`, both with
`has_world_collision_shape: 1`. So 40 of 42 parts carry exactly one bound hull, 2 carry none, and
14 hull instances carry no part index (`decomposition.unbound_note`). "One per part" is a true
summary of the *bound* set and false of the part table; the field name invites a reader to think
every part has a hull, which matters because those 2 parts are exactly the bodies whose 14 hulls
are unusable as slots.

### 3. `max_hulls: 54` counts 14 hulls the card itself says are not authorable (R11/R4)

`t22_collision.py:333` (`dec["max_hulls"] = donor["hulls"]`), quoted as "max_hulls is fixed at 54"
in the MODLOG. `unbound_note` (:345) then says the same 14 instances "are not free slots", and
`decomposition.new_hull` says the object count is fixed at 54 either way. Both are true; but the
parameter the card asked for - "the convex-decomposition parameters that exist (max hulls, convex
radius)" - is therefore 40 usable slots, not 54, and the MODLOG's "max_hulls is fixed at 54" reads
as a capacity the writer has. The usable number is `donor["hulls_bound_to_a_part"]`, already in the
json.

### 4. `unbound_note`'s "the donor's two bumpers" is not what the geometry shows

`t22_collision.py:345-346`, MODLOG "14 unbound (the two bumpers' panels, which carry no part
index)". I re-decoded the 14 unbound polytopes (`part_index is None` on all 14, so that half is
right) and their bounds are not a two-bumper set:

- 7 at `z -2.37 … -2.59`, `y 0.18 … 0.50`, `|x| <= 1.05` - a front-bumper strip, symmetric. Good.
- 4 at `z -0.11 … 0.08`, `y -0.52 … 0.49`, `|x| <= 0.49` - mid-car / underbody, not bumper height.
- 3 at `z 1.83 … 2.52`, `x 0.51 … 1.04` only, `y 0.19 … 0.73` - a rear **one-sided** cluster with no
  left-hand mirror, which a rear bumper would have.

"Belong to the two bumpers" is a plausible-sounding attribution with no derivation behind it; the
data supports "14 hulls with no part index, 7 of them a front-bumper strip". This is prose, not a
row, so it is a documentation defect only.

### 5. The 18 "destruction debris" are not `Object*_frag_*` (MODLOG precision, R11)

MODLOG: "18 of the 32 bones are `Object*_frag_*` debris". Only 10 of the 32 match that pattern
(`Object003_frag_007/008/017/023/024/025`, `Object004_frag_002/003/006/007`); the other 8 are plain
`Object`, `Object001`, `Object007`, `Object009`, `Object011`, `Object013`, `Object015`, `Object017`.
The row and `PHYSICS.md:14` list all 18 correctly, so only the MODLOG's characterisation is off. The
category itself is name-driven by exclusion (`t22_collision.py:112-118`: any bone not matched by the
name rules becomes `DEBRIS`), which is defensible for a `Batmobile_V3_Destroyed_Physics` asset but
means "destruction debris" is a name inference, not a measured property.

### 6. The audit trail says 4/4 tamper tests; only the outputs' self-consistency is gated

`GRAB_BACKLOG.md:1331` claims "4/4 tamper tests". One of them (`t16_collision.json` `hulls` 54 ->
55) fails only because the json is compared to a re-derivation; a tamper *inside* the derivation
(e.g. `hulls_per_part` or the "one per part" string, issue 2) is invisible to `--check`. No
independent invariant such as `hulls == hulls_bound + hulls_unbound` or
`parts_colliding + len(parts_without) == parts` is asserted - both hold, so this is a gap in the
gate's strength, not a wrong number.

### 7. Minor: the card's `max hulls` / `convex radius` never reach a row

The card names them explicitly; they live only in `decomposition` (json). The `T-P3` cell says
"hull set, slot binding, radius x k", so a reader does get the radius rule, but the next card's
only text (`GRAB_BACKLOG.md:1331`) is where 54 and 0.01 x k appear, and B-10's card (`:1070`) does
not restate them. Acceptable, worth noting since `--check` gates the json, not that row.

## Spot-checks

| value | where verified |
|---|---|
| wheel `scale_k` 1.660052, hull `0.491 x 1.3654 x 1.2986` | tyre Ø = 2 x mean station radius = 2 x 0.6827 = 1.3654 m (`stations.json`), donor wheel hull longest axis 0.8225 m from my own `jc3hkx.decode_polytope` re-read: 1.3654 / 0.8225 = 1.66005; `0.2958/0.8225/0.7822 x k` = 0.491 / 1.3654 / 1.2986 |
| body `scale_k` 1.676259, hull `3.495 x 2.0316 x 6.1666`, radius 0.016763 | `parts_manifest.json` body bbox `[-1.748, 0.091, -3.42] .. [1.747, 2.362, 3.605]` -> 3.495 x 2.271 x 7.025 m; ratios to the 2.085 x 1.212 x 3.6788 body hull = 1.67626 / 1.8738 / 1.90957, `min` = 1.676259; x `k` -> 3.495 / 2.0316 / 6.1666; 0.01 x 1.676259 = 0.016763 |
| donor census: 22 compounds, 54 hulls, 40 bound, 14 unbound, 400 B / 1776 B, 8-36 v, 5-47 p, radius median 0.01, min 0.002436 | my own pass over `sportsmuscle.physicsc` (340,368 B) via `jc3hkx`: identical on every count, incl. `hulls_bound_to_a_part` using `load_part_names()` |
| 0 station quads; stations untouched | `jc3hkx.stations(Packfile(blob))` returns `[]` (0), so `stations.in_physicsc: 0` is right and R3's "nothing to move in this file" holds |
| 38/42 `has_world_collision_shape`, 4 wheels 0 with `world_collision_body_id -1` | `Donor` decode via `jc3adf.parts` on `sportsmuscle_vehicle_parts.vmodc` (29,886 B): 38 set, 4 unset - `wheel_f_l/r_l/f_r/r_r`, each body id -1, part indices 11/12/26/27 as the row says |
| largest BmAK box `316.155 x 63.418 x 109.881` at 2.2031e6 cm3, `Root` 30.3 cm cube | `PHYSICS.json` `Playable_Batmobile_SF.bodies`, volume sort over all 32: it is the maximum by volume (next: `SUSP1_Wheel_Rear_Right` 2.0106e6, itself 317.942 cm on one axis); the old §7 numbers `211.5 / 51.1 / 109.0` are `SUSP2_Wheel_Front_Left`, so the prose correction at `T2_TRANSLATION.md:160` is the right maximum by volume |
| 11 T-8 parts without a slot | `Working/Translation/T8_PARTS.json` `parts` length = 11 |
