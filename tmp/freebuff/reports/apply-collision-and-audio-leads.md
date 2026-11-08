# apply-collision-and-audio-leads — T-22/B-10 reopened, the drivable collision is now the source

**STATUS: done.** `collision-where` located the drivable car's rigid body, so **T-22 and B-10 are
reopened** on it and the plan that replaces the donor chassis is generated and checked
(`Working/Translation/T22_REOPEN.md`, `Tools/scripts/t22_reopen.py --check`, 10/10). The four
collision rows (`T-P3`, `T-CO1`, `T-CO2`, `T-CO3`) now name the real asset. `T-AU3`/`T-AU5` were
already `next` with the `AUDIO_BANKS.md` evidence (the previous apply pass) and are re-verified, not
re-pinned. The blocked set did **not** move — 15 (11 ledger + 4 T6) of 216 in scope — so the
`WAITS`/`in_scope` pins are unchanged; `t_blocked.py --write` refreshed the ledger sha and both
`--write` and `--check` pass. No game was launched and nothing under a game install was written.

## 1. What changed, and how to revert it

| file | change | revert |
|---|---|---|
| `Tools/scripts/t22_reopen.py` | **new**: the reopen plan generator, `--write`/`--check`, 10 oracles | delete the file |
| `Working/Translation/T22_REOPEN.md` / `.json` | **new**: the plan and the same rows as data | delete both |
| `Tools/scripts/t22_collision.py` | reads `COLLISION_WHERE.json`; `T-P3`/`T-CO2`/`T-CO3` re-rendered on the drivable asset; `drivable_asset` in the record | restore the three `render_rows` blocks and the inputs line |
| `Tools/scripts/t_rows.py` | `why` for `T-P3`, `T-CO1`, `T-CO2`, `T-CO3` rewritten | restore the four lines |
| `Working/Translation/T2_TRANSLATION.md` | §7 heading + intro, `T-CO1` row, §9 blocked line | restore the old heading/intro/row/line |
| `GRAB_BACKLOG.md` | §9 `T-22` and §8 `B-10` marked **REOPENED 2026-11-07** with the why and an amended `Done`; §12 rows `T-22`, `B-10` + a `Collision-reopen` row | restore those three blocks/rows |
| `Working/Translation/t16_collision.json`, `T_ROWS.jsonl` | **regenerated** by their own generators | re-run `t22_collision.py --write`, `t_rows.py build` after the revert |
| `Working/Translation/BLOCKED_PROPOSALS.{json,md}`, `STATUS.md` | **regenerated** (`t_blocked.py --write`, `status_audit.py --write`) | re-run after the revert |
| `Working/Translation/COMPROMISES_T.{json,md}`, `BUILD_BATCHES.md`, `build_batches.json` | **regenerated** — the cell edits made these two records stale (both are counts over row cells) | re-run `audit_compromises_t.py --write`, `t23_closeout.py --write` |
| `MODLOG.md` | one entry, 2026-11-07 | truncate it |
| `tmp/freebuff/reports/apply-collision-and-audio-leads.md` | this report | delete it |

`Backups/t_blocked.py.8203-before` is the pre-change copy of the pin (kept per the pin-upkeep rule,
even though no pin line needed editing).

## 2. The collision source, and what it changes

`tmp/freebuff/reports/collision-where.md` (G3-16) decoded `Physics.Batmobile_V3_Physics`
(BmGame.upk export 158266, 194 B): **2 body setups, 3 box elements, 1 constraint**, reached from
`Batmobile.SVehicleMesh` property offset 824. Boxes (`Research/BatmobileGrab/COLLISION_WHERE.md`):

| body | box | extents (cm) | centre (cm) | TM |
|---|---|---:|---|---|
| `Batmobile_Chassis` (169750) | 0 | 690.305 x 374.536 x 207.5 | (9, 0, 106.75) | identity (B-10e, `identity_error` 0.0) |
| `Batmobile_Chassis` (169750) | 1 | 679.585 x 345.688 x 103.5 | (0, 0, 79) | identity |
| `Batmobile_Rig_Weapons_Trans` (169751) | 0 | 166.177 x 189.365 x 39.8 | (-30.5, 0, 93.25) | 4.000 deg about y |

Constraint export 171462 (86 B) names [Weapons_Trans, Weapons_Trans, Chassis]; parent/child order is
UNKNOWN (no `RB_ConstraintSetup` layout).

**Why the two cards reopen.** T-22 was closed on the 32-body *wreck* census (`PHYSICS.json`) and its
rows concluded "the drivable car has no physics asset". B-10's `Done` gate was the render bbox
(`DIM-1` 3.495 x 2.271 x 7.025 m), which B-10d already showed is 25 cm narrower and 20 cm taller than
the drivable chassis box. So the delivered hull set rewrites **1 of 62 donor body entries** (B-10e),
and **2 of BmAK's 3 boxes have no shape at all**.

**The plan** (`T22_REOPEN.md`, 5 steps): S1 chassis box 0 into body 0's existing hull slot (writable —
G2-30 proved scale/translate); S2 chassis box 1 into a second shape instance in body 0's compound
(**0 free hull slots** — the 54 hulls are all accounted for and the 14 unbound instances are the
donor's bumpers — so this is the open writer question, with a 5-minute discriminator: re-point 2
unbound instances and run `jc3hkx.py check --all --file`); S3 the pod box at 4 deg carried rigid
with body 0 (no `Rig_Weapons_Trans` part exists to bind a separate body to); S4 the 1 constraint is a
**named omission** — `bm_collision.json` carries 0 constraint data and no JC3 constraint writer is
decoded; S5 acceptance = `jc3hkx.py check --all --file` + shape union within 5 cm of the two chassis
boxes + pod at 4 deg, then Q-2 kerb/ram. The donor's other 61 part bodies stay as JC3's per-part
contact because BmAK has only 2 bodies — declared as a difference, not sold as parity. That is the
honest replacement of "donor chassis by decision".

## 3. Rows (the ledger)

| row | before | now |
|---|---|---|
| `T-CO1` | `next`, "donor chassis by decision" ancestry, BmAK cell = 3 boxes + 56 convex elements | drivable asset = `Physics.Batmobile_V3_Physics` (2 bodies / 3 boxes / 1 constraint, reached from `SVehicleMesh` @824); proposed = author the 2 bodies, keep the 61 donor part bodies, constraint named; conf `decoded (asset) / UNKNOWN (constraint parent, pod simulation)` |
| `T-P3` | "11 driveable boxes map onto 7 donor hull slots" | hull target is the asset's 3 boxes; the built set carries 62 donor bodies with 1 rewritten hull, so 2 shapes are missing; verify `T22_REOPEN.md` + `t22_reopen.py --check` |
| `T-CO2` | "largest box 316.15x63.42x109.88 cm" | that is the **wreck** maximum (a wreck wheel); the car's largest is the chassis box 690.305x374.536x207.5 cm |
| `T-CO3` | "no per-part flag; the car has 2 whole-car meshes + 3 boxes" | the asset is 2 bodies / 3 boxes / 1 constraint and 0 per-part bodies, vs the donor's 38 — the difference is declared |

`STATUS.md`: rows resolved from evidence **142 -> 145** of 216 (the three collision rows are now
classified on the decoded asset instead of falling into `other`); blocked **15 / 216** unchanged;
queued 109 unchanged; in scope 216 unchanged. This is a reclassification with a new source, not a
value that was built or driven.

## 4. Audio (T-AU3 / T-AU5)

Already re-pinned by the earlier apply pass, and verified in place, not re-edited:
`T-AU3` and `T-AU5` are `dispo: next`, their cells carry `AUDIO_BANKS.md` (G3-14: **10 claimed banks,
10 found, 0 absent**, 117 `AkBank` payloads, 447 media rows) and `T_AU3B.md`'s "ABSENT: 27 of 27 is
the JC3 install", and `t_blocked.py`'s `RESOLVED` holds both with their evidence markers. The one
thing still unnamed is `0x6BB2C66E` (`Play_BatSniperRifle_Vehicle_Tracking_Fire`) — not in any of the
117 payloads — plus the JC3-side event binding and, for T-AU5's three families, their own bank (none
is among `AUDIO_MAP.json`'s 361 rows). Nothing to add to the ledger; the remaining work is the JC3
event slot, which is exactly what both rows now say.

## 5. Pin upkeep

The blocked set is **15 = 11 ledger + 4 T6**, in scope **216** — no row changed blocked-ness (the
collision rows stay `next`: the missing input is a writer/slot question, not absent research), so
`WAITS` and `reconciles`/`in_scope` were left as pinned and only the ledger sha pin moved. Backed up
first (`Backups/t_blocked.py.8203-before`), then `--write` then `--check`.

## 6. Commands and output (verbatim)

```
$ python Tools/scripts/t22_collision.py --write
wrote Working\Translation\t16_collision.json: 32 bodies, 54 hull slots, 7 mapped, 21 unmapped; 3 rows regenerated
exit=0
$ python Tools/scripts/t22_collision.py --check
PASS: 32 BmAK wreck bodies | drivable 2 bodies / 3 boxes | 7 mapped / 21 unmapped | 54 donor hull slots, one per part | 38/42 parts collide | rows 3 (next 3) | stations unchanged
exit=0
$ python Tools/scripts/t22_reopen.py --write && python Tools/scripts/t22_reopen.py --check
wrote Working/Translation/T22_REOPEN.{json,md}: Physics.Batmobile_V3_Physics 2 bodies / 3 boxes / 1 constraint; built 62 donor bodies, 2 shape(s) missing; 10/10 oracles
PASS: 10 oracles - Physics.Batmobile_V3_Physics (2 bodies / 3 boxes / 1 constraint), built set 62 donor bodies, 2 shape(s) missing, plan 5 steps
exit=0
$ python Tools/scripts/t_rows.py build && python Tools/scripts/t_rows.py check
199 rows, 35 edits over 16 rows
ledger 199 rows | edit 16 next 109 keep 29 epe 26 re-read 0 blocked 11 out 1 superseded 7 | edits 35 over 16 rows
check ok
exit=0
$ python Tools/scripts/t_blocked.py --write
wrote Working/Translation/BLOCKED_PROPOSALS.{json,md}: 15 blocked rows (11 ledger + 4 T6) of 216 in scope; 0 tested, 7 resolved
exit=0
$ python Tools/scripts/t_blocked.py --check
PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 216 in scope; 0 attempts, all evidence markers present; ledger sha256 unchanged
exit=0
$ python Tools/scripts/status_audit.py --write && python Tools/scripts/status_audit.py --check
wrote STATUS.md   (rows resolved 145/216, blocked 15/216, queued 109)
STATUS.md is current
exit=0
$ python Tools/scripts/audit_compromises_t.py --write && --check
72 audited, 1 approved, 71 unapproved
OK: every approval quote re-read at its cited line; document re-derived identically
exit=0
$ python Tools/scripts/t23_closeout.py --write && --check
7 problem(s) -> 5 problem(s), all pre-existing (below)
exit=1
$ python Tools/scripts/bmak_coverage.py --check
check ok
exit=0
```

## 7. Limits, named not implied

- **No drive and no write to a build.** The plan is not built: `Working/Collision/batmobile.physicsc`
  still carries the 62 donor bodies and body 0's single re-cut hull (`192c1247…`). The runtime
  question (does the engine accept 3 shape instances in one compound, and does the pod body need its
  own?) is a phase-Q/builder question, and S2's 5-minute discriminator is named rather than run.
- **The constraint has no carrier** — the row says named omission instead of claiming the 1-constraint
  asset is reproduced.
- **The live Batman-vs-Batmobile mesh per mode** is still UNKNOWN (`BatmanVsBatmobileCollisionMode` at
  offset 5895 is not serialised); nothing here changes that.
- **Two pre-existing red checks, not caused by this work and not hidden:**
  `t23_closeout.py --check` fails on `§11 has 11 decisions, expected D-1...D-10` and `B-17`…`B-20:
  no payload and not declared as a no-payload step` (5 problems; the BUILD_BATCHES drift this change
  did cause was regenerated, leaving exactly the pre-existing set). `t11_modes.py --check` fails on
  `ledger T-WP4 is next, the row cites blocked`, a T-WP4 state from an earlier pass that this task
  does not touch. Everything this task owns is green.
