# Independent review — T-17 · Effects translation

Reviewer: Buffy (did not write this card). Date: 2026-10-29. Read-only review: the only file
written is this report. No game launch, no commit, no edit to `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` or any game file.

**Change record (AGENTS.md).** Intended change: create this one review file. File:
`tmp/freebuff/reports/review-T-17.md`. Why this file: the review was asked to land exactly here and
nothing else is written. Revert: delete `tmp/freebuff/reports/review-T-17.md`.

**Scope reviewed:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the T-17 card (`GRAB_BACKLOG.md:932-937`), the
T-17 §12 row (`GRAB_BACKLOG.md:1326`); `MODLOG.md:12295-12423` (intended change + done);
`Working/Translation/T13_FX.md` (136 lines), `Working/Translation/t17_fx.json` (38,927 B),
`Tools/scripts/t17_fx.py` (747 lines); its five inputs (`Research/JC3Grab/FX_TABLE.jsonl`,
`Research/BatmobileGrab/PARTICLES_FEATURES.json`, `Research/JC3Grab/USAGES.json`,
`Research/JC3Grab/WEAPONS.jsonl`, `Research/BatmobileGrab/SOCKETS_JC3.json`) and
`Working/Translation/T_ROWS.jsonl`.

---

## VERDICT

**minor issues**

This is the best-built of the translation cards I have reviewed. Both `Out` paths exist, the 17
rows land in the ledger as doc `T-13` (17/17), `--check` is a genuine re-derivation that compares
both files byte-wise and cross-checks every ledger cell, and each row carries an effect path, an
attachment and a trigger — or a named omission. The five negative rows are real negatives: I
re-derived them independently from `FX_TABLE.jsonl` (0 of 955 paths match `tracer`, `haze` or
`brake`; the only 2 `shell_eject_*` paths are non-vehicle), and every chosen path, size, array
count and row count I spot-checked matches the table. The FX-code coverage is genuine too — all
four codes carry at least one chosen effect and/or a proven omission for each sub-requirement in §1.

What it needs fixing is narrower than T-16's: **the headline carrier metric is mislabelled** ("N
vehicles" is a count of `.ee` containers, and 289/298 of them exceed the 232-entity fleet), one
proposed trigger mechanism contradicts the doc's own §5, the 0-system groups are treated
inconsistently, and the `--check` gate does **not** actually enforce the card's Done clause ("every
FX code has …") — it only prints the coverage. Those are wrong statements and a decorative gate, not
wrong effects.

---

## Check output (verbatim)

Command, from `E:/Modding/JC3-Batmobile`:

```
python Tools/scripts/t17_fx.py --check
```

stdout, exact (exit status `0`):

```
PASS: 17 rows (12 chosen, 5 named omissions) | FX codes 4/4 | donor effects 85 | fleet .effc 955 | sockets 8 | ledger 17/17
EXIT=0
```

This is a real rebuild, not a cached pass: `cmd_check()` (`t17_fx.py:651-657`) calls
`build_payload()`, which re-reads all five inputs, re-derives every row, re-renders the doc and
compares `on_disk != payload` (`:658`) and `disk_md != new_md` (`:670`), then compares
`lr["cells"]` for every row against `T_ROWS.jsonl` (`:691-705`).

## Out paths

| path (card `Out` / row) | exists | size / lines |
|---|---|---|
| `Working/Translation/T13_FX.md` | yes | 14,499 B, 136 lines (MODLOG says 136 — match) |
| `Working/Translation/t17_fx.json` (row) | yes | 38,927 B, 17 rows |
| `Tools/scripts/t17_fx.py` (row) | yes | 39,616 B, 747 lines |
| rows in `T_ROWS.jsonl` as doc `T-13` (row) | yes | 17 rows, ids `T-FX7…T-FX23` |

No `Out` path is missing, and the "rows" half of the card is on disk in the ledger.

## Does the card's `Done` match what `--check` verifies?

Card (`GRAB_BACKLOG.md:937`): *"every FX code has a chosen effect or a named omission."*

- **Content: yes.** FX-1 (flame + haze), FX-2 (muzzle flashes, tracers, casings, missile trail,
  cannon impact), FX-3 (tyre kick-up, slide dust, scrape sparks, brake trail) and FX-4 (explosion,
  burn, post-burn) each have at least one row, and every row is either `chosen` or `absence`. I read
  the nineteen rules to confirm the sub-requirements of §1 map onto rows.
- **Gate: no.** In `cmd_check()` the coverage line is computed from the rows themselves
  (`covered = len(set(s["fx_codes_covered"]) & {...})`, `t17_fx.py:710-716`) and printed; `bad` is
  never incremented for it, and the function returns `1 if bad else 0`. Delete every FX-3 rule and
  `--check` still exits 0 with "FX codes 3/4" — the Done clause is reported, not enforced. (Contrast
  T-16, whose invariants iterate the feature list.) The derived-row problems (`problems`) *are*
  fatal, so a broken rule fails; a *missing* rule does not.

---

## Issues

### 1. Moderate — every "N vehicles" cell is a count of `.ee` containers, and several exceed the fleet size

`t17_fx.py:268`: `e["vehicles"] = sum(1 for c in e["containers"] if "/jc_vehicles/" in c)` — it
counts the **container files** that embed the effect, then the doc renders it as "… N vehicles"
(`jc3_cell`, `t17_fx.py:429-440`). So `T13_FX.md:68` says `chassis_slide_default.effc - 289
vehicles` and `:69` says `spark_trail_02_med.effc - 298 vehicles`, while `ENTITIES.md:3` puts the
fleet at **232** decoded `.epe` graphs. A carrier count above the whole fleet cannot be a vehicle
count.

Re-derived from `FX_TABLE.jsonl`: 309 distinct `/jc_vehicles/` container `.ee` files, spread over
117 distinct vehicle class directories; `chassis_slide_default.effc` has 290 containers total (289
under `/jc_vehicles/`) and only 113 distinct class directories; `spark_trail_02_med.effc` has 301
containers (298) and 116 directories. So the ranking key and the printed number are `.ee`-file
counts, and `MODLOG.md:12302` (*"then by how many of the 232 vehicles carry it"*) is wrong twice:
the count is not vehicles and it is not bounded by 232. The effect **choices** survive this
(identity is the donor flag, `t17_fx.py:370-372`), but every carrier number in the doc and the
"232" in the MODLOG are unusable as stated (R4/R11).

### 2. Moderate — T-FX10's trigger claim contradicts the doc's own §5

`T13_FX.md:60` proposes the cannon flash with *"use at CannonMuzzle when the cannon is cloned; the
effect rides the weapon bundle"*. `T13_FX.md:120` says the opposite for that carrier: *"w619 16,
w610 14, w618 12, w608 5 effects; **w602/w603/w604 ship no bundle of their own**, G2-10"*. T-16
W-01 (`T12_AUDIO.md`) and T-11 record WPN-1's carrier as `w602_mediumtank_cannon`. So the one
weapon FX-2 needs first (the heavy cannon) is the case where "the effect rides the bundle" does not
hold, and the doc gives no other route (an `SAttachedEffect` usage, a manual bundle entry). The
`now`/`propose` cells promise a mechanism the same document denies.

### 3. Moderate — the 0-system policy is applied two ways, and T-FX19's class name hides a judgement

`T13_FX.md:22` states the rule: *"A group with 0 systems is a proven absence on the BmAK side, not an
untranslated feature."* Heat-steam (0 systems, `:43`) follows it → named omission (`:59`). Wall-scrape
(0 systems, `:45`) does not → a **chosen** effect (`:69`), `confidence` `derived`.

`T13_FX.md:53` then redefines the R4 class: *"`derived` = the mapping needed judgement"*. R4's
`derived` means a value computed from decoded data (as T-16 uses it for `gain_db`), and R4 says
*"`assumed` is not buildable"*. Naming a judgement `derived` is exactly the relabelling R4 forbids.
T-FX19 is defensible on R1 grounds — the chosen `spark_trail_02_med.effc` **is** donor-carried
(`donor: true` in the JSON) — but it is then a "keep what the JC3 car already has" row, not a
translation of a BmAK feature, and the doc should say that and explain why heat haze is not treated
the same way.

### 4. Moderate (MODLOG) — "every one of the 22 `WeaponTuning` rows carries tracer_*" is false

`MODLOG.md:12310-12312`: *"every one of the 22 `WeaponTuning` rows carries
`tracer_texture_type`/`tracer_fire_velocity`/`tracer_time_to_live`"*. The script's own summary in
`t17_fx.json` says `"weapon_ids": 25, "weapon_tracer_ids": 11`, and re-running
`load_weapon_facts()` gives **11 of the 22 bullet-block rows** with all three fields (the 11 without
are the missiles and `w601`, which legitimately have no tracer). The doc row (`T13_FX.md:62`) states
the conclusion ("JC3 draws the tracer as a texture on the bullet") without the 11/22 number that
would back it. The conclusion holds for the guns — `w619_buggy_mgun` (tex 1, 750, 0.25) and
`w602_mediumtank_canon` (tex 1, 900, 0.0) do carry the fields — but the MODLOG sentence is a typed
overstatement.

### 5. Minor — T-FX17 attaches one wheel, not four

`T13_FX.md:67` gives `part wheel_f_l` for tyre kick-up; the rule's own rationale says *"attachment is
the four wheel parts"* (`t17_fx.py:174-175`), and §1 of MODLOG says "on the wheel parts" (plural).
The card asks for the effect's attachment point, so a single part is an incomplete build input: a
builder reading the row would emit dust from the front-left wheel only.

### 6. Minor — §4 prints the wrong denominator for the vehicle-carried negative

`T13_FX.md:106`: *"0 of 955 match over the vehicle-carried `.effc` paths"*. For
`absence="no_vehicle_paths"` the test pool is `veh` (`t17_fx.py:358`), i.e. the **589**
vehicle-carried paths, while the printed denominator is `fleet_effc` = 955. The two halves of that
sentence contradict each other; the correct statement is "0 of 589".

### 7. Minor — typed numbers in the renderer (R11)

`read_doc()` hard-codes: `"in 57,187 FX rows"` (`T13_FX.md:12`), `"G1-13, 65 sockets, 13/13 required
anchors present"` (`:78`), and the weapon-bundle counts `"w619 16, w610 14, w618 12, w608 5 effects;
w602/w603/w604 ship no bundle"` (`:120`). I re-derived the first two and both are right (57,187 rows
and 955 `.effc` in `FX_TABLE.jsonl`; 65 sockets in `SOCKETS_JC3.json`), but `--check` cannot see
them. The weapon counts are not derivable from any input the script reads — `WEAPONS.jsonl`'s
summary has no effect count — so they are G2-10 numbers typed into a generated file.

### 8. Minor — the trigger is a name lookup, not a verified link

`load_usages()` (`t17_fx.py:282-290`) keeps only `hash` and vehicle count per usage name; the
`trigger_evidence` check is "does this name exist". `T13_FX.md:57-58,71` claim the flame is under
`EngineNitro`, the base exhaust under `EngineRunning` and the explosion under `OnExploded`, but
`--check` never asserts that the chosen `.effc` is attached to that usage. `USAGES.json` does carry
the material to test it (`flame.exhaust_effect_files` shows `car_cycle_base_dual_nitrous` = 17
containers; `nitro_usages`/`usages` give the 18/69 carriers), so the assertion is available and
simply not made. The claim is likely right; the provenance is not machine-checked.

### 9. Minor — a typed `why` string already disagrees with the derived cell

`t17_fx.py:182`: *"`chassis_slide_*` (5 surfaces, 290 vehicles)"* vs the generated `T13_FX.md:68`
"289 vehicles". The `why` is what lands in `T_ROWS.jsonl`, so the ledger now carries a different
number from the doc. One is the `/jc_vehicles/` subset, the other all containers — which is itself
issue 1 in miniature.

### 10. Minor / cosmetic

- `T13_FX.md:64` prints *"1 systems / 1 names"*; `:46` leaves the `speed-lines` owner as *"FX?"* in a
  table whose stated purpose is that *"nothing falls between cards"*.
- "5 surfaces" (`:68`) and "one per surface (6 variants)" (`:67`) infer surface semantics from name
  needles; the counts are right (`collision/chassis_slide_` matches 5 paths, `wheels/trail/dust_trail_`
  6), but "surface" is an interpretation, not a field.

---

## Spot-checks

| # | doc value | verified where | result |
|---|---|---|---|
| 1 | "955 distinct (589 carried by a vehicle) in 57,187 FX rows" (`T13_FX.md:12`) | re-read `FX_TABLE.jsonl`: 57,187 non-empty lines; 955 distinct `.effc` paths; 589 of them have a `/jc_vehicles/` container | match |
| 2 | "donor chassis effects **85** carried by `v0300…signature_preorder.ee`" (`:12`) | 85 distinct `.effc` whose container set contains the exact signature `.ee` path (`t17_fx.py:55-56`) | match |
| 3 | T-FX7 `car_cycle_base_dual_nitrous.effc` — "20,671 B, 337 arrays, 3161 rows" (`:57`) | `FX_TABLE.jsonl` row for that path: size 20,671, arrays 337, rows 3,161; JSON `chosen.donor` true | match |
| 4 | T-FX7/T-FX8 "17 vehicles" (`:57-58`) | `USAGES.json` `flame.exhaust_effect_files` also reports 17 containers for both; consistent, but a container count (issue 1) | number matches, unit wrong |
| 5 | T-FX18 "289 vehicles" (`:68`) | 289 = `/jc_vehicles/` containers; 290 containers total, 113 distinct class directories; fleet is 232 entities (`ENTITIES.md:3`) | **contradicts the "vehicles" label** (issue 1) |
| 6 | "0 of 955" for tracer / haze / brake omissions (`:104-108`) | needle scan of the 955 paths: 0 contain `tracer`, 0 `haze`, 0 `brake`; 2 contain `shell` (`shell_eject_12ga*`) and none is vehicle-carried | match |
| 7 | "sockets used 8" (`:15`) | 8 distinct socket names in the JSON (`summary.sockets`) and in §3's table | match |
| 8 | T-FX21 `exp_car_01.effc` — "34,895 B, 759 arrays, 6891 rows" (`:71`) | `FX_TABLE.jsonl`: 34,895 / 759 / 6,891 | match |

---

## What would make this card `sound`

1. Rename the metric to what it measures (`containers`, or derive distinct class directories) and
   restate the ranking as `.ee`-carrier count; correct `MODLOG.md:12302`'s "232 vehicles".
2. Give T-FX10 a real route (an `SAttachedEffect` usage or a manual bundle entry) or state it as
   UNKNOWN — do not claim the cannon rides a bundle that §5 says does not exist.
3. Pick one policy for 0-system groups, apply it to both heat-steam and wall-scrape, and label
   T-FX19 as donor-carried/keep (or as an addition), not as R4 `derived`.
4. Enforce FX coverage in `cmd_check()` (`if covered < 4: bad += 1`) so the Done clause has teeth,
   and fix `MODLOG.md`'s "every one of the 22" to 11 of 22.
5. Attach T-FX17 to all four wheels (or say the builder must mirror it), fix the 955/589 denominator,
   and derive or cite the three typed counts.

## Limits of this review

- Read-only: the MODLOG's four tamper tests were not re-run (they require editing the JSON, MD,
  rules or ledger). The mechanisms they exercise are real code — the payload/document compares
  (`t17_fx.py:658,670`), the `problems` list for refuted negatives (`:358-363`), and the ledger
  dispo/cell compare (`:691-705`) — and I confirmed the negative test's input (0 needle matches), so
  the claims are plausible but not reproduced here.
- No game launched; every `verify` cell is a Q-1/Q-2/Q-3 probe and is unverified by construction.
- `T_ROWS.jsonl` and `STATUS.md` were not rebuilt (read-only); the check's 17/17 covers the ledger as
  it stands.

## Files touched by this review

`tmp/freebuff/reports/review-T-17.md` (this file). Nothing else.
