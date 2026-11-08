# Correction 8395 — T-WP4's card citation (DONE)

**Status: fixed.** `Working/Translation/T_ROWS.jsonl` line 154 (row `T-WP4`) no longer cites
`B-24 / B-25`; the two places now name the rows that own the work and state that no card owns the
lock hold / salvo.

## 1. What was wrong

`T-WP4` is the EMP missile (`RBatmobileEMPMissile` + `Batmobile_EMPMissile_Projectile_ForCars`),
built as a `w618` clone plus an entity-level `CForcePulse` with no disable half (the disable is
T-WP15). Its `why` field and its last `cells` entry both ended with **"(cards B-24 / B-25)"**.

- **B-24** is the handling-values card (`t1_handling.json`, 15 values).
- **B-25** is the lens-flare / light-unit card (24 light rows, flare carriers).
- Neither has an EMP missile, a lock cone, a hold timer or a salvo.

So the pointer told a reader that two unrelated payloads owned T-WP4's remaining gap, and the
genuinely ownerless part — the 2.0 s held lock, the 8-target salvo, the reticle link — appeared
owned when it is not.

## 2. The change

Two string replacements, both inside `T-WP4` only:

| field | before | after |
|---|---|---|
| `why` (tail) | `The disable half is T-WP15, and the 2.0 s lock hold / 8-target salvo / reticle link have no member (cards B-24 / B-25)` | `The disable half is T-WP15; the 2.0 s lock hold / 8-target salvo / reticle link have no member (T-WP3b owns the lock half, B-18 the pulse/disable clone; no card claims the hold/salvo)` |
| gate `cells` (tail) | `... they have no member (cards B-24 / B-25)` | `... they have no member (T-WP3b owns the lock half, B-18 the pulse/disable clone; no card claims the hold/salvo)` |

Unchanged: `dispo = "next"`, `edits = 0`, the operator-ruling text (split approved 2026-11-06), the
five transplanted Fire Leech guidance values, the `AutoAim` recipe, and the whole loss description.
The row still says the launcher half ships and the disable half is T-WP15.

Why these pointers and not a new card: **T-WP3b** is the open lock/cone row (it already owns "no
cone, no range, no hold" for the missile barrage) and **B-18** is the EMP pulse/disable clone. The
2.0 s hold, 8-target salvo and reticle link have **no member and no card**; the edit says so rather
than inventing a card id (`AGENTS.md`: do not fill a gap with a plausible-looking claim).

## 3. Checks

```
$ python -c "...assert count('cards B-24 / B-25')==2 ..."   # before the edit
occurrences a: 1 b: 1 bad citation total: 2
after: dispo= next | B-24/25 left: False

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
check_exit=0

$ grep -n "B-24\|B-25" Working/Translation/T_ROWS.jsonl
(no match)
```

The JSONL still parses (each line was `json.loads`-ed after the write). Only free text changed, so
the row's visibility bucket, disposition, `edits` count and the ledger totals (145/216 evidenced,
15 blocked, 109 queued, 8 out, 8 superseded) are untouched — `status_audit.py --check` confirms the
generated STATUS.md is current.

## 4. Revert

**`git checkout` does not restore this file**: it is untracked (`git ls-files` -> "Did you forget to
'git add'?"). To revert, replace the new string in both places with `(cards B-24 / B-25)` and re-run
`python Tools/scripts/status_audit.py --check`. No other row, no build tree and no installed file
was touched.

## 5. Limits

- T-WP3b is a **ledger row**, not a card; the edit says it owns the lock half, which is accurate but
  means the hold/salvo still has no card. If one is wanted, it must be created in the card register,
  not implied by this citation.
- Whether the 2.0 s hold / 8-target salvo can ever be carried is still **UNKNOWN**: no member exists
  in the weapon or entity vocabulary read by T-7, and this correction does not change that.

Updated by review 8399: the B-24 / B-25 citation was confirmed wrong and replaced with T-WP3b / B-18
plus an explicit "no card owns the hold/salvo".
