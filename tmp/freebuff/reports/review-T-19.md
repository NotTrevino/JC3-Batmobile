# Independent review — T-19 · HUD translation

Reviewer: Buffy (did not write this card). Date: 2026-10-29. Read-only review: the only file
written is this report. No game launch, no commit, no edit to `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` or any game file.

**Change record (AGENTS.md).** Intended change: create this one review file. File:
`tmp/freebuff/reports/review-T-19.md`. Why this file: the review was asked to land exactly here and
nothing else is written. Revert: delete `tmp/freebuff/reports/review-T-19.md`.

**Scope reviewed:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-19 card (`GRAB_BACKLOG.md:947-950`), the
T-19 §12 row (`GRAB_BACKLOG.md:1327`); `MODLOG.md:13468-13667` (intended change + done);
`Working/Translation/T6_HUD_CAMERA.md` (§1a block, lines 31-83), `Working/Translation/t19_hud.json`,
`Tools/scripts/t19_hud.py` (21,718 B); its inputs (`Research/BatmobileGrab/HUD_INTERFACES.json`,
`Research/JC3Grab/JC3_HUD_WEAPONS.json`, `Working/Translation/t7_weapons_edits.json`), plus
`Research/BatmobileGrab/HUD.md` / `HUD_SPEC.json` and `Working/Translation/T7_WEAPONS.md` for the
provenance of the claims.

---

## VERDICT

**minor issues**

The card is done and the gate is real. The §1a block exists inside the named doc, the JSON mirrors
it, and `--check` enforces what the Done clause asks for: all five `wpn12` elements from G2-25 must
have a row (read from the evidence file, not just a typed list), every row must carry a proof, every
proof is re-evaluated against `JC3_HUD_WEAPONS.json`, T-HUD1…3 must still be in §1, T-HUD5's
original row must still record its blocked state, and the doc block and JSON are compared byte for
byte. I re-derived eight of the row values straight from the two evidence JSONs and all matched.

The defects are in how three rows are worded and classed, not in the structure:
**"heat bar absent on both sides" is false on the BmAK side** (the cannon carries
`HeatBarStart`/`HeatBarSize`; only a `UC_*` setter is absent), the cooldown row presents an invented
5-state→fraction pinning as `derived`, and the lock-on omission's only machine proof proves the BmAK
requirement rather than the JC3 absence. Two classes are also set higher than the row's own limit
cell justifies.

---

## Check output (verbatim)

Command, from `E:/Modding/JC3-Batmobile`:

```
python Tools/scripts/t19_hud.py --check
```

stdout, exact (three lines; exit status `0`):

```
rows 10 over 5/5 elements | map 6 partial 2 out 2 | proofs 12 | kept T-HUD1..3 3/3
doc match True, json match True
check ok
EXIT=0
```

This is a real re-derivation, not a cached pass: `check()` calls `build()`, which re-reads all three
inputs, re-resolves every BmAK setter signature and re-evaluates every proof, then re-renders the
block and compares it with the doc (`check()` in `t19_hud.py`), and compares the payload with
`t19_hud.json`.

## Out paths

| path (card `Out` / row) | exists | evidence |
|---|---|---|
| `Working/Translation/T6_HUD_CAMERA.md` §1a (card `Out`, row) | yes | generated block between `<!-- T19-HUD-BEGIN -->` (line 31) and `<!-- T19-HUD-END -->` (line 83) |
| `Working/Translation/t19_hud.json` (row) | yes | 10 rows, 12 proofs, 2 slot bindings, `kept` = T-HUD1…3 |
| `Tools/scripts/t19_hud.py` (row) | yes | `--write` / `--check` / `--show <row>` |

The card's `Out` is "rows in `T6_HUD_CAMERA.md`"; that is satisfied without touching
`T_ROWS.jsonl`, which the row also states and which I confirmed (no `T-HUD1x/2x` ids in the ledger).

## Does the card's `Done` match what `--check` verifies?

Card (`GRAB_BACKLOG.md:950`): *"each HUD element mapped or omitted with proof."*

- **Elements:** the five G2-25 `wpn12` element names are read from
  `JC3_HUD_WEAPONS.json` and each must be covered by a row (`build()` → `wpn12` loop); a missing
  element is a failure, and the MODLOG's tamper #4 ("delete the heat row → `FAIL G2-25 element
  'Vulcan heat' has no row`") is consistent with that code path.
- **Mapped or omitted:** every disposition must start with `map`/`partial`/`out`, and every row
  must have at least one proof that holds. `partial` is a third state the card does not name, but
  the two rows that use it (T-HUD15, T-HUD18) also state exactly which half is missing.
- **Proof:** the proofs are member-existence proofs, not behaviour proofs (see issue 3). That
  matches the card's letter, but for the two `out` rows the proof direction is not always the
  omission.
- **Keep clause:** T-HUD1…3 presence and T-HUD5's `blocked` cell are asserted from the doc text, so
  "keep T-HUD1…3" is machine-checked rather than trusted.

Overall the Done clause is enforced, which puts this card ahead of T-17 (where the FX-coverage line
is printed but never asserted).

---

## Issues

### 1. Moderate — "heat bar absent on both sides" is false on the BmAK side

`T6_HUD_CAMERA.md:54` (disposition `out (stated absence both sides)`), `:39` and `:77` (the §1a
paragraph: *"the **heat bar** is absent on both sides (0 JC3 arguments, 0 body mentions, 0 of 252
BmAK setters)"*), `:39`, and the §12 row (*"heat = stated absence both sides"*).

BmAK has the heat bar: `HeatBarStart` / `HeatBarSize` exist as members of `Batmobile_Cannon_V2`
(`Research/BatmobileGrab/BMSDK_OFFSETS.json:13900` and `CHAIN.json:3503,3834,4244`), which the row's
own limit cell says (*"BmAK's heat is `HeatBarStart`/`HeatBarSize` on `Batmobile_Cannon_V2`"*). What
is absent is a **`UC_*` HUD setter** (0 of 252 setter names contain `heat` — I re-derived that), and
on the JC3 side a heat element (`params_with_heat` `[]`, `body_mentions` 0 — also re-derived). So the
element is a one-sided omission (`BmAK: 2 weapon-script fields, 0 HUD setters; JC3: no element`),
not a two-sided absence. The wording matters for the build: a reader could conclude there is no heat
value to show, when there is one on the weapon and only the HUD path is missing. G2-25 itself uses
"stated absence (both sides)" (`JC3_HUD_WEAPONS.json` `wpn12` heat row), so the phrase was inherited
— but T-19's own limit cell contradicts it and the row should have been corrected here.

### 2. Moderate — the cooldown transform is an invented pinning, classed `derived`

`T6_HUD_CAMERA.md:53` (T-HUD16): *"cooldown = BmAK state / 4 (state 0…4 -> 0.00, 0.25, 0.50, 0.75,
1.00)"*, class `derived`, disposition `map`; limit: *"the division by 4 is the only monotone map
between the two domains, and its direction is a Q check, not a file fact"*.

- "The only monotone map" is false: any strictly increasing map from {0..4} into [0,1] is monotone
  (e.g. `(state+1)/5`), so this is a chosen convention, not a consequence of the data.
- The state order is not pinned either. `HUD.md:138` lists the cannon states as `PreReady`, `Ready`,
  `PreReadyLevel1`, `PreReadyLevel2`, `Blank`; the doc never says that integer `0` is `PreReady` nor
  which end of the loader is "full". G2-25's own limit says the states *"have to be pinned to 5
  fractions before the loader reproduces them"* — T-19 pins them by assumption.
- The class is too strong. The document applies a stricter standard one row above: T-HUD15 has a
  member with no unit bridge and is `UNKNOWN`/`partial`. Here the member exists but the mapping is
  an assumption whose direction the row itself calls a Q check, so R4 ("assumed is not buildable")
  makes this at most `partial`, with the fraction vector as the proposed value.

If the loader runs the other way, the HUD shows a full ring when the cannon is ready.

### 3. Minor — the lock-on omission's proof proves the requirement, not the omission

`T6_HUD_CAMERA.md:56` (T-HUD19, disposition `out`) and its proof at `:73`
(`bmak.missile_target_kinds` = 6). The proof counts the six BmAK target kinds — i.e. it proves the
feature exists on the BmAK side. Nothing in the machine check proves the JC3 side has no element for
them; that comes from G2-25 §7 prose (`targets_element_cell`). The card's "omitted with proof" is
therefore met only in the BmAK direction for this row. By contrast T-HUD17's proofs are JC3-side
zeros (`params_with_heat` `[]`, `body_mentions` 0), but its BmAK half ("0 of 252") is typed prose in
the limit cell rather than an evaluated proof, and the interface JSON does carry
`setters_with_heat: []`, so that half could be proved too.

### 4. Minor — two classes are set above what the row's own limit cell says

- T-HUD14 (`:51`): class `decoded`, disposition `map (shape id UNKNOWN)`, limit *"the shape id is
  the closest named member, not a proven binding"*. R4 classes describe the value, and this value is
  explicitly unproven — it should be `UNKNOWN` (like T-HUD15) even though `E_RETICLE_CANNON = 8`
  itself is decoded.
- T-HUD16 (`:53`): `derived`, see issue 2.

### 5. Minor — the weapon ids in T-HUD11/T-HUD13 are typed, not read from the file named as their source

`T6_HUD_CAMERA.md:39` says the block quotes `t7_weapons_edits.json` for *"which weapon the two clips
actually show"*, and `T-HUD11` (`:48`) says *"slot 0 = the cannon clone of `w602_mediumtank_cannon`
… slot 1 = the Vulcan clone of `w603_mediumtank_mgun`"*. That JSON's `structural` entries name only
"the cannon clone" and "the Vulcan clone" — no weapon ids — and `--check` only asserts that two such
bindings exist (`len(bindings) < 2`). The ids come from `T7_WEAPONS.md:68,140` prose, which is the
right source (T-11 did choose w602/w603), but the cell is typed in `t19_hud.py` `ROWS`, not derived
from the JSON the doc points at.

Related, in T-HUD13 (`:50`): *"ids 602, 603, 618, 619: all four are in the shipped icon set, so both
slots draw"*. Only 602 and 603 are bound; 618 (donor missile) and 619 (the alternative Vulcan) are
not on a slot, and the proof `icons.ids` holds all four (`:65`). The proof is a superset check, so it
does not establish "both slots draw" — it only establishes that the four ids have icons.

### 6. Minor — typed numbers inside a generated block (R11)

Derived and correct: 10 rows, 5 elements covered, 6/2/2 dispositions, 12 proofs, 3 kept. Typed in
the renderer and not re-derivable by `--check`: *"5/5"* (`:41`; `counts.elements` is the number of
elements covered *by rows*, and the divisor is a literal `5`), *"0 of 252"* (`:77`), *"11-state"*
(`:54`, matches `heat.police_heat_states` 11), *"5 look states"* and *"marker y -111 for shapes
8/11/12"* (`:51`; the JSON has `inflict_damage_y` `[-111,-21]`, `hidden_inflict_damage_shape` 3 and
the shapes 8/11/12 do exist, but the association is prose), and `"rotated 360 deg"` (`:55`; G2-25
states it, no numeric field carries it).

### 7. Nit — small wording/provenance slips

- `T6_HUD_CAMERA.md:55`: the lock-on clip is written `MCI_lock_on.MCI_reticle`, while G2-25 says
  `MCI_icon.MCI_lock_on.MCI_reticle`.
- `T6_HUD_CAMERA.md:50`: *"0 of `HudModuleBatmobile`'s 37 setters name an icon"* is a name test;
  `UC_SetOccupant(param1…param5)` does pass an icon string (HUD.md's setter table: "visible, name,
  icon, …"), so "name an icon" is narrower than it reads. The conclusion (no weapon-icon id in
  BmAK) still holds.
- Removing the block leaves two extra blank lines compared with `tmp/T6_HUD_CAMERA.beforeT19.md`;
  everything else is identical, so the MODLOG's "identical line by line" is true up to whitespace.
- `ELEMENTS` in `t19_hud.py` duplicates the five `wpn12` names as a typed list. It is a belt-and-
  braces check (both must pass), but if G2-25 ever renames an element the doc would print "4/5"
  while the failure message comes from the other list.

---

## Spot-checks

| # | doc value | verified where | result |
|---|---|---|---|
| 1 | T-HUD11 *"2 slots"* and proof `slots.count = 2` (`:48,63`) | `JC3_HUD_WEAPONS.json` `slots.count` = 2, clips `MCI_vehicle_weapons0/1`, constants main 0 / alt 1 | match |
| 2 | T-HUD14 *"shape `E_RETICLE_CANNON = 8`"* (`:51`) | `reticle.shapes` = `{E_RETICLE_CANNON: 8, …}` (14 shapes) | match |
| 3 | T-HUD17 *"`params_with_heat` empty and `body_mentions` 0"* (`:54`) | `heat.params_with_heat` = `[]`, `heat.body_mentions` = 0 | match |
| 4 | *"0 of 252 setters name heat"*, *"37 setters"* (`:54`, `:77`) | `HUD_INTERFACES.json`: 252 setters over 19 module objects, none matching `heat`; `HudModuleBatmobile` has exactly 37 | match |
| 5 | T-HUD18 *"`POI_TYPE_LOCK_ON_TARGET = 21` … every 1.5 s"* (`:55`) | `lockon.lock_on_type` 21, `lock_on_rotation_time` 1.5 | match |
| 6 | T-HUD16 *"rot = cooldown x 360"* (`:53`) | `cooldown.rot_degrees` 360, `toggled_by` "weapon_cooldown != -1" | match |
| 7 | *"5/5 G2-25 elements"* (`:41`) | `wpn12` element list = weapon slots, reticle, cannon cooldown, Vulcan heat, missile lock (5) | match |
| 8 | T-HUD17 *"heat bar absent on both sides"* (`:54`, `:77`) | `BMSDK_OFFSETS.json:13900` / `CHAIN.json:3503` carry `HeatBarStart` (and `HeatBarSize`) on the cannon | **contradicts the doc** (issue 1) |

---

## What would make this card `sound`

1. Reword the heat row and the §1a/§12 sentence to what the files say: BmAK has the heat fields but
   no HUD setter; JC3 has no heat element. Keep `out`, drop "both sides".
2. Downgrade T-HUD16 to `partial`/`UNKNOWN` with the five proposed fractions recorded as a proposal
   (or pin the state order from the movie and drop the "only monotone map" sentence).
3. Make the omission proofs two-sided: add a JC3-side absence proof for T-HUD19 (the movie's element
   list has no target-kind family) and a `setters_with_heat == []` proof for T-HUD17.
4. Set T-HUD14's class to `UNKNOWN` (the binding is unproven), and either read the two weapon ids
   from a file or point the doc at `T7_WEAPONS.md` instead of `t7_weapons_edits.json`.
5. Derive the "5/5" denominator from `wpn12` and pull "0 of 252" from `bmak.all_setters`.

## Limits of this review

- Read-only: `--write` was not run (it would rewrite the doc), and the MODLOG's five tamper tests
  were not reproduced. The code paths they exercise are real — the block byte-compare and JSON
  compare in `check()`, the element-coverage loop in `build()`, and the proof evaluator
  `_eval_proof()` — and I re-derived every proof value independently, so the claims are plausible.
- No game launched, so every `verify` cell (Q-3 #3 and the `n/a` omissions) is unverified by
  construction.
- The doc's unchanged header text ("25 native HUD modules, 19 carved movies, 252 `UC_*` setters")
  predates T-19 and was not reviewed beyond noting that `HUD_INTERFACES.json` carries 19 module
  objects and 252 setters.

## Files touched by this review

`tmp/freebuff/reports/review-T-19.md` (this file). Nothing else.
