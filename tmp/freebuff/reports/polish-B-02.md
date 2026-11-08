# Polish pass — B-02 · Split the body into movable parts

Card: `GRAB_BACKLOG.md` §8 `B-02` (lines 1000-1016), §12 row line 1333. Review:
`tmp/freebuff/reports/review-B-02.md` (**minor issues**, 6 items). Date 2026-11-01.

**Note on the card's report.** `tmp/freebuff/reports/B-02.md` does not exist in this tree (no B-02
report file was ever written; `tmp/freebuff/done/` holds only the challenge/review prompts). The card's
report used here is MODLOG §"B-02 · Part split — done (2026-10-24)", which is the section the review
itself cites, plus the §12 row. Nothing about the review changes on that account.

**Scope actually touched** (B-02's own outputs and its own two tools only):
`Tools/scripts/bat_assemble.py`, `Tools/scripts/silhouette_check.py`, new
`Tools/scripts/parts_manifest_check.py`, MODLOG (new entry), and B-02's own §12 row. Backups:
`Backups/polish-B-02-20261101/` (byte copies of both scripts and MODLOG taken before the first edit).
The parts build, all 80 RBMs and `parts_manifest.json` were **not** modified — no signed-off value
changed. No game file, no install, no launch, no other card's output, no commit.

## One line per review issue

1. **Recorded build command no longer runs (spec schema 2 vs gate 1).** **FIXED (and it was already
   stale).** `Working/Translation/T8_PARTS.json` is `schema: 1` again — T-12's 2026-10-29 regeneration
   reverted the 2026-10-28 bump — so the recorded command loads today: `schema 1, 11 parts`. Made
   durable by accepting schema 1 **or** 2 at the gate while still rejecting 3 (tested both ways). The
   gate is not weakened: `load_part_spec` validates every part's `pivot_bone`, `bone_roots`/
   `bone_prefixes` and `parent` immediately after it.
2. **The manifest's own 11 checks are never re-derived.** **FIXED.** New
   `Tools/scripts/parts_manifest_check.py --check` recomputes 14 assertions from disk: all 80 RBMs
   decoded and compared to `faces_per_lod` / `vertices_per_lod` / `blocks_per_lod`; pivots from
   `BONES.json`; the budget re-summed from file sizes; `scale`/`offset` against `build.log`'s transform
   line; and the entire cut re-run from `Batmobile_V2.pskx` through `bat_assemble.assign_parts`, so the
   split stats (1683 / 1176 / 193, 31 ties, 0 unresolved) and every per-part LOD0 count are recomputed
   rather than read. Five tampers (budget, pivot, triangles, ties, LOD count) are each CAUGHT, so the
   check is not vacuous.
3. **Gate reported as net coverage; gross holes 0.309 % is over BUD-1's 0.3 % oracle.** **FIXED as
   reporting; the 0.009 pt overshoot LEFT.** `silhouette_check.py` now prints a `BUD-1 oracle` line with
   the gross figure, an OVER/under verdict and an explicit "coverage above is NET". The geometry is not
   re-decimated: that would change signed-off RBMs. The card's `Done` (≥ 99.9 % coverage) still passes.
4. **The silhouette check cannot see a wrong pivot (the pivot cancels).** **FIXED.** Pivots are now
   proven independently: `parts_manifest_check.py` re-derives all 16 pivots from `BONES.json`'s bind
   through `bat_assemble.pivot_point` (wheels from `stations.json`), max delta **4.88e-07 m**, never
   reading `pivot_m` back. Wording corrected everywhere: 0.9997 measures decimation loss, not pivot
   placement; the pivot evidence is the bind-pose path.
5. **`T8_PARTS.md` prints the wrong pivot for 6 of the 11 parts.** **LEFT — another card's output and a
   signed-off value.** Confirmed 6/11 disagree with the manifest (machine gun 0.315 m, riot 0.150 m,
   flaps 0.120/0.120/0.390/0.389 m). That file is `t12_parts.py`'s regenerated output and
   `t12_parts.py --check` asserts its markdown text (`md match True`), so a hand edit breaks a standing
   check, while regenerating after a `t12_parts.py:517-519` fix rewrites T-12's signed-off doc. The
   defect is in T-12's generator, not in B-02's manifest or RBMs; those are now proven by issue 2's
   checker. Fix belongs to T-12.
6. **Minor / unverifiable.** (a) The "old body chain failed spec_check at 2 vs 16 planned" history has
   no artifact left — **LEFT**, cannot be re-derived offline. (b) Build arguments: **PARTLY FIXED** —
   the checker now matches the manifest's `scale`/`offset` to `build.log`'s transform line and re-derives
   the per-LOD budgets from the RBMs; the original argv is not in `build.log`, and reconstructing it
   would be inference (R4), so an exact argv rebuild stays a **limit**. (c) "Movable" = movable about
   the bind pivot, not a validated hinge (T8_PARTS.md already says so) — **LEFT**, no value changed.

## Commands run and their PASS lines

```
$ python Tools/scripts/silhouette_check.py --manifest Working/Appearance/build_parts/parts_manifest.json
applied the manifest offset [4.77e-07, 0.022231445, 0.154284012] to the source
reassembled 12 body/part LOD1 meshes; 215,893 source faces
frame 2400x864  source 215,893 tris  ours 40,248 tris
silhouette   source 1,131,963 px   ours 1,131,599 px   coverage 0.9997
holes        3,494 px = 0.309% of the source silhouette
of which interior tears (>=3 px inside the outline)  740 px = 0.065%
extra        3,130 px = 0.277% of the source silhouette
BUD-1 oracle   gross holes 0.309% of the source silhouette vs 0.3% = OVER; coverage 0.9997 above is NET (holes netted against 0.277% extra)
boundary edges   source 0%   ours 0%
EXIT 0   (1m28s)
```

```
$ python Tools/scripts/spec_check.py Working/Appearance/build_parts Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm
checked 295 blocks; spec mismatches 0; template values silently inherited 0
EXIT 0
```

```
$ python Tools/scripts/parts_manifest_check.py --check
  PASS manifest checks block all true               11 recorded checks
  PASS parts spec loads through bat_assemble's gate Working\Translation\T8_PARTS.json: schema 1, 11 parts
  PASS five LODs per entry                          16 entries x 5 LODs
  PASS every LOD file present                       80 of 80 files on disk
  PASS RBM triangle counts                          80 of 80 files match faces_per_lod
  PASS RBM vertex counts                            80 of 80 files match vertices_per_lod
  PASS RBM block counts                             80 of 80 files match blocks_per_lod
  PASS pivots from BONES.json                       16 entries, max delta 4.88e-07 m (tol 1e-05)
  PASS transform matches build.log                  scale 0.01 offset [0.0, 0.0222, 0.1543], max delta 3.1e-05 (log rounds to 4 dp)
  PASS model budget                                 4790.9 KB measured, manifest 4790.9 KB, cap 4915.0 KB (R9 wall 4915 KB)
  PASS split re-derived from the source             215893 body faces -> 171391 body + 44502 parts; split 1683 body / 1176 unique / 193 weight, ties 31 {'batmobile_missile_pod_l': 4, 'batmobile_missile_pod_r': 26, 'batmobile_riot_suppressor': 1}, unresolved 0
  PASS ties resolve to weapons only                 31 ties -> {'batmobile_missile_pod_l': 4, 'batmobile_missile_pod_r': 26, 'batmobile_riot_suppressor': 1}
  PASS per-part LOD0 faces                          16 entries match the re-derived cut
  PASS all faces accounted                          299837 faces in the source, body 215893 (expected 215893)
PASS: Working\Appearance\build_parts\parts_manifest.json re-derived from the files (14 assertions)
EXIT 0
```

Budget (the card's own number, re-measured from the 80 `*.rbm`): **4790.9 KB of 4915 KB** — green.

Tamper tests (proof the new check fails when it should):

```
$ python Tools/scripts/parts_manifest_check.py --check --tamper model_kb
TAMPER model_kb: model budget -> CAUGHT
$ python Tools/scripts/parts_manifest_check.py --check --tamper pivot
TAMPER pivot: pivots from BONES.json -> CAUGHT
$ python Tools/scripts/parts_manifest_check.py --check --tamper faces
TAMPER faces: RBM triangle counts -> CAUGHT
$ python Tools/scripts/parts_manifest_check.py --check --tamper ties
TAMPER ties: split re-derived from the source -> CAUGHT
$ python Tools/scripts/parts_manifest_check.py --check --tamper lods
TAMPER lods: five LODs per entry -> CAUGHT
```

Evidence for issues 1 and 5 (read-only checks):

```
$ python -c "import bat_assemble as B; B.load_part_spec('Working/Translation/T8_PARTS.json')"
LOADED OK: schema 1 parts 11

$ (schema-2 and schema-3 copies of the spec, in tmp/freebuff/b02polish/)
schema 2 -> ACCEPTED
schema 3 -> REJECTED: part spec ...: schema 3, expected 1 or 2

$ python Tools/scripts/t12_parts.py --check
PASS: 15 rows (11 cut parts, 12 with an animated joint, 4 with a shipped hinge, spins ['P-03']) |
25 BmAK row-sequence pairs (15 distinct clips) | fastest joint 1229.51 deg/s | pivots re-derived
through bat_assemble (max delta 1.3918e-05 m) | damage types ['Boat_Generic', 'Land_Generic',
'Land_Hood', 'Plane_Control_Surface', 'Train_Generic'] | internal rows ['P-02', 'P-05', 'P-13'] |
json match True, md match True
EXIT 0      <- T8_PARTS.md still matches its generator, which is why issue 5 was left

$ (T8_PARTS.md geometry table vs parts_manifest.json, pivot column, max |delta| per row)
machine gun 0.315 m | riot suppressor 0.150 m | flap l_f 0.120 m | flap r_f 0.120 m |
flap l_b 0.390 m | flap r_b 0.389 m; pivots 6 of 11 mismatched
```

## What this pass does not prove

Same limits as the card, unchanged: no game launch, no install, nothing under `D:/Games`, no dropzone
write, no save touched; the `.rbm`/manifest layer is verified, **not** behaviour in game (phase Q); the
parts are movable about bind pivots, not yet about validated hinges; `T8_PARTS.md`'s 6 wrong pivot cells
remain (issue 5, T-12); gross silhouette holes remain 0.009 pt over BUD-1's 0.3 % (issue 3, not
re-decimated); the original build argv is still not recorded anywhere machine-checkable (issue 6b).

COMPLETE
