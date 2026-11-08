# T-FX3 — afterburner flame approved and queued

**STATUS: done.** The operator's 2026-11-06 item 2 ("approve the decoded afterburner-flame edit")
is applied to the ledger row `T-FX3` and to its `BLOCKED_PROPOSALS` entry together: `blocked` → `next`
(the build queue). `t_blocked.py` is re-pinned to 15 blocked (11 ledger + 4 T6), and
`t_rows.py check`, `t_blocked.py --check` and `status_audit.py --check` all pass. No game was
launched, attached to or installed to; no build tree was written.

## 1. What changed, and how to revert it

| file | change | revert |
|---|---|---|
| `Working/Translation/T2_TRANSLATION.md` | row `T-FX3` rewritten (target, transform, now, proposed, conf, verify); the §9 "blocked rows" line marked unblocked; the §11 "no JC3 usage slot" bullet corrected | restore the four original cells (`**no usage slot** …`, `blocked`, `—`) and the two prose lines; re-run `t_rows.py build` |
| `Tools/scripts/t_rows.py` | `DISPO["T-FX3"]`: `("blocked", "no usage slot …")` → `("next", …)` | restore that one line |
| `Working/Translation/T_ROWS.jsonl` | **regenerated** (`t_rows.py build`), not hand-edited: `T-FX3` `dispo: next`, 8 cells as below | reverse the two edits, re-run `build` |
| `Tools/scripts/t_blocked.py` | `T-FX3` removed from `WAITS`/`ATTEMPTS`, added to `RESOLVED` with its ruling and applied change; pins 15/11; header prose | restore the removed blocks, drop the `RESOLVED` entry, restore the 16/12 literals |
| `Working/Translation/BLOCKED_PROPOSALS.{json,md}` | **regenerated** (`--write`): 15 rows, `T-FX3` and `T-ST7` under "Resolved – no longer blocked" | re-run `--write` after the revert |
| `STATUS.md` | **regenerated** (`status_audit.py --write`): blocked 15 / 180, queued 42 | re-run `--write` after the revert |

Ruling text (`Working/Translation/DECISIONS_NEEDED.md`, "OPERATOR RULINGS 2026-11-06", item 2):

> **T-FX3: approve** the decoded afterburner-flame edit.

## 2. The exact edit, and the file it lives in

The row's stated blocker ("no usage slot for an exhaust flame") was already false: the donor's two
exhaust emitters **already carry** usage `4197885156` = `EngineNitro`, and the flame is
`effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` (hash `-776668445`). What was actually
missing was **placement** — the donor `world` matrices are the Serpente's rear-exhaust positions
(`±0.410, 0.373, 2.480`), not the Batmobile's jet.

**Edit spec:** `Working/Effects/bm_fx_edits.json`, `edits[]` — two `SAttachedEffect.world` matrices:

| object (class `SAttachedEffect`) | old | new |
|---|---|---|
| `exhaust_upgrade_nitrous2` | `1,0,0,0, 0,-4.371139E-08,1,0, 0,-1,-4.371139E-08,0, -0.4101563,0.3728027,2.47998,1` | `-3e-06,1,1.17e-10,0, 1,3e-06,-3.9e-05,0, -3.9e-05,0,-1,0, -0.009578,0.537762,3.393177,1` |
| `exhaust_upgrade_nitrous` | `1,0,0,0, 0,-4.371139E-08,1,0, 0,-1,-4.371139E-08,0, 0.4101563,0.3728027,2.47998,1` | same as above |

The new matrix is the `Afterburner` socket: bone `JetSMove` (parent `Batmobile_Chassis_Mesh`),
position `[-0.009578, 0.537762, 3.393177] m` (`Working/Effects/bm_fx_edits.json` `socket`,
`Research/BatmobileGrab/SOCKETS_JC3.json` G1-13).

**Compiled by:** `Tools/scripts/bm_fx.py` (B-08, done 2026-10-31) into
`Builds/bm-008/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe`
(467 objects). B-08's own re-derivation: 48 effect objects, 32 hashes, **32/32 resolved**, 0
unresolved, 2 emitters with usage `[4197885156]` (`EngineNitro`), the flame `.effc` present in both
the donor container and the build tree.

No usage id is written by this edit — the usage was already right; adding one would have been the
"new usage" invention the rules forbid.

Ledger row after the rebuild (`T_ROWS.jsonl`, row `T-FX3`):

```
dispo: next
cells[2] (target): entity-graph `SAttachedEffect` on the donor's two emitters
                   (`exhaust_upgrade_nitrous2`, `exhaust_upgrade_nitrous`), `usage` 4197885156 `EngineNitro`
cells[3] (transform): epe — placement only
cells[4] (now): already carried: both emitters are `EngineNitro` in the donor graph; only their
                `world` mat was the Serpente's exhaust
cells[5] (proposed): **next** (operator ruling 2026-11-06, item 2): keep `EngineNitro` and place both
                     emitters at `Afterburner` (bone `JetSMove`, [-0.009578, 0.537762, 3.393177] m) - the
                     two `SAttachedEffect.world` matrices in `Working/Effects/bm_fx_edits.json` `edits[]`,
                     compiled by `Tools/scripts/bm_fx.py` into `Builds/bm-008/.../*_civilian_01.epe`
cells[6] (conf): decoded
cells[7] (verify): boost: flame at the jet nozzle, loops while nitro is held; 32/32 effect hashes resolve
```

## 3. Commands and output (verbatim)

```
$ python Tools/scripts/t_rows.py build
E:\Modding\JC3-Batmobile\Working\Translation\T_ROWS.jsonl: 198 rows, 35 edits over 16 rows

$ python Tools/scripts/t_blocked.py --write
wrote Working/Translation/BLOCKED_PROPOSALS.{json,md}: 15 blocked rows (11 ledger + 4 T6) of 180 in scope; 4 tested, 2 resolved: T-AU3=still-blocked, T-S6=still-blocked, T-AU5=still-blocked, T-WP4=partially-unblocked

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 42 keep 60 epe 26 re-read 0 blocked 11 out 36 superseded 7 | edits 35 over 16 rows
check ok

$ python Tools/scripts/t_blocked.py --check
PASS: 15 blocked rows re-derived (11 ledger + 4 T6) of 180 in scope; 4 attempts, all evidence markers present; ledger sha256 unchanged

$ python Tools/scripts/status_audit.py --write   # STATUS.md: rows blocked 15 / 180; rows queued 42
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
```

Counts before → after: `next` 41 → 42, `blocked` 12 → 11, in-scope blocked 16 → 15. The proposals
sheet now lists 15 rows and two resolved: `T-ST7`, `T-FX3`.

## 4. The owning build tool's check is red — pre-existing, not from this edit

```
$ python Tools/scripts/bm_fx.py --check
FAIL: the built .epe differs from the re-derived plan: 6 object(s) missing, 6 unexpected, e.g.
missing ("SWeaponPoint", "attach.vehicle", ..., ("id:8C547250", 0.0), ("id:D04059E6", -405742323.0))
unexpected (same objects, plus ("id:A90F5E74", "weapon_anchor"))
CHECK_EXIT=1 (1 failure(s))
```

The diff is entirely on six `SWeaponPoint` objects that gained an `id:A90F5E74 = weapon_anchor`
property after B-08 (a later weapon step wrote into `Builds/bm-008`'s `.epe`); none of the
`SAttachedEffect` rows or the flame differ. `bm_fx.py` was not edited by this card, and the ledger
change does not touch `.epe` bytes, so this is a stale-plan failure against the *whole* object set,
not a T-FX3 regression. It needs the weapon-lane owner to re-derive the plan (or scope the compare
to its own objects).

## 5. UNKNOWNs

- **Whether the flame follows the nozzle on a moving car.** The `world` matrix is stored as binary
  floats inside the `.epe` RTPC object, whose `SAttachedEffect` member offset is not decoded
  (`T_FX3B.md` §1: two literal-byte probes miss because the text is a rendering, not the disk bytes).
  Only a render would settle it, and no game was launched.
- **Whether `EngineNitro` fires on the Batmobile's own boost.** `EngineNitro` is raised by the arcade
  nitro field, which the build ships (T-FX7 rows), but no decoded file states the trigger for this
  vehicle — no probe was run.
- **Whether a usage outside the arcade nitro fields can be raised** (a Batmobile-only state): still
  UNKNOWN; `USAGES.json` names 6 of 155 usages from a module. This does not affect T-FX3, which uses
  an existing usage.

## 6. Knock-ons not re-run for this card

`v05_driving.py`, `audit_compromises_t.py`, `ledger_g3c.py` and `t_st7b.py` were already red after the
T-ST7 change (`tmp/freebuff/reports/steering-st7-apply.md` §6); they read the ledger's dispositions or
the turning circle, so they will report the same drift here. They were not re-run for this card and
were not edited.

## COMPROMISES

**None.** The approved edit is applied as decoded: the existing `EngineNitro` usage on the two donor
emitters, moved to the `Afterburner` socket. No capability of the effect was dropped to fit a JC3
limit — the row's supposed limit (no usage slot) was simply not real.
