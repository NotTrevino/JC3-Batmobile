# V-07 - gate VX: STATUS regenerated, MODLOG VX written, approval request filed

**STATUS: done.** `STATUS.md` regenerates and verifies at the operator's numbers
(**145/216 evidenced, 1 assumed, 15 blocked — 11 ledger + 4 T6, 109 queued, 8 out, 8 superseded**),
`t23_closeout.py --check` is green at **11/11 decisions** (after regenerating a stale
`BUILD_BATCHES` record that the check correctly refused), the MODLOG carries a **VX** section with
every verify result, and `Working/Q/APPROVAL_REQUEST.md` exists. **`tmp/freebuff/APPROVED_Q.txt` was
not created** — verified absent; only the operator writes it.

## 1. What was run

```
python Tools/scripts/status_audit.py --write   -> exit 0
python Tools/scripts/status_audit.py --check   -> exit 0; "STATUS.md is current"
python Tools/scripts/t23_closeout.py --check   -> exit 1; FAIL BUILD_BATCHES.md and
                                                  build_batches.json differ from the re-derived
                                                  record (regenerate with --write)
python Tools/scripts/t23_closeout.py --write   -> exit 0; wrote both records
python Tools/scripts/t23_closeout.py --check   -> exit 0; gate TX: 75 codes (58 carried,
                                                  3 named omission, 4 blocked, 10 documented,
                                                  0 unmapped) | 199 ledger rows | assumed 1
                                                  (0 unsigned) | decisions 11/11 answered |
                                                  19 artefacts (17 payloads + 2 records) over 24 B steps
                                                  siblings: t_rows.py 0, status_audit.py 0,
                                                  bmak_coverage.py 0
```

**The `t23` red is disclosed, not silenced.** The check failed before any work because
`BUILD_BATCHES.md` / `build_batches.json` had not been rewritten since the RC4 and mode-pair
corrections. The decisions themselves were already 11/11; regenerating made the generated pages
match the re-derived record, and the check now passes on its own terms. Neither the check nor its
assertions were edited.

`STATUS.md` (regenerated, decoded from `T_ROWS.jsonl` + T6):

| metric | value |
|---|---|
| rows resolved from evidence (in scope) | **145 / 216 = 67.1 %** |
| rows assumed | 1 / 216 (signed off) |
| rows blocked | **15 / 216** = **11 ledger + 4 T6** (`STATUS.md` line 36: T6 HUD/camera blocked 4) |
| rows queued for the next build | **109** |
| rows out / superseded | **8 / 8** |
| rows fully behaviour-verified | **0 / 216** — no drive covers a row end to end |

## 2. The approval request

`Working/Q/APPROVAL_REQUEST.md` contains, as the card requires:

* **what would be installed** — the receipt's **9** drop files, **401,700,202 B**, each with size and
  sha256, and the installer identity (6,535 B, sha256 `b4589d40…`); six are new files, three replace
  shipped profile files, and the diff-snapshot consequence for Rollback is stated;
* **the session plan** — **three sessions** (Q-1 static, Q-2 driving, Q-3 world/combat) with derived
  length estimates (~45 / ~40 / ~45 min) labelled as estimates from each card's checklist;
* **the pilot cards** — `Working/Q/PILOT/`: `LAUNCH`, `LOAD_SAVE`, `SPAWN_BATMOBILE`, `ENTER_EXIT`,
  `CONTROLS`, `AIRFIELD`, `SCREENSHOT`, `RECORD`, `KILL` (+ `CARD_FORMAT`), read-through only;
* **every red or UNKNOWN**, each with the file that proves it (section 3 below);
* **the open decision** — D-2 is reopened, so approving Q tests the pursuit car, not a battle mode.

The dry-run reference is `Builds/bm-RC4/verify/dropzone_sim.md` (six required cases at their expected
exit codes, including the guard negative exit **2**).

## 3. Disclosures, each against the file that proves it

| gap | what the file says | owner |
|---|---|---|
| stale checkers | `v05_driving` T-ST7 gate (now 34/34, miss still **RED** at 0.80 / 0.60 s vs 0.091-0.250 s), `t_boost_rows` 20/21 and `t_vnf_six` AssertionError, both on **198-row pins against a 199-row ledger** | `correction-8396-stale-checkers.md`, `Working/Q/PREDICTIONS.md` |
| `receipt.complete = false` | **12 of 23** texture rows unfaithful — 4 chapter masks + 8 missing pixel sets; the ledger holds 14 refusal records, each with `counted_in_the_12`, `present_in_playable_batch`, `present_in_grab` | `Builds/bm-RC4-appearance/texture_ledger.json`, 8392 |
| collision | shipped payload `fda78f4d…`: placement **[0.0005, 0.0000, 0.0025] m = 0.25 cm**, gate **MET**; **2 of 3** BmAK boxes have no shape instance; **1** constraint is a named omission | `Builds/bm-RC4/verify/geometry.md` lines 11, 18-19; 8390 |
| audio | 45 GUIDs = **24 resolved + 21 donor** (19 effects + 2 character) | `Builds/bm-RC4-audio/events.json`; 8393 |
| module conflict | `skew_health` **is present** in the packed `custom_land_global.vmodc`; 8397 resolved D-08/D-10 as one merged module | that `.vmodc`; 8397 |
| mode pair, no-payload cards | RC4 = pursuit set only; battle pair unmerged in `Builds/bm-RC4-modes`; B-12/B-17…B-20/B-25/B-26 declare **no payload in RC4**; T-MD8 and T-MD14 are **named omissions** | `BUILD_BATCHES.md` §4, B-12 row, `GRAB_BACKLOG.md` D-2; 8398 |
| top speed | T-E5 **336.4 km/h is `assumed`**; the build predicts **267 km/h** at Cd 0.55; the 0.1213 Cd is withdrawn | `Working/Q/PREDICTIONS.md` D-2; 8391 |
| runtime | load, Rebel Drop leaf **1621485476** and every Q take are **untested**; no install ran against a game folder | this gate |

### Two review-8399 lines that the files contradict, recorded rather than repeated

1. **"collision gate false: 6.1 cm"** — on the bytes that ship, the gate is **MET at 0.25 cm**; the
   6.1 cm vector belongs to payload `0164936b…`, which is **not in this tree** (`geometry.md` says so
   in its own words). The approval request carries both figures with that provenance, so Q reads the
   expected failure against the payload it belongs to.
2. **"D-08 skew_health rows not carried"** — that was the state before **8397**, which merged both
   sets; `skew_health` is in the packed module today. The brief line is the pre-8397 state.

## 4. Files written and revert

| file | change | revert |
|---|---|---|
| `STATUS.md` | regenerated by `status_audit.py --write` | previous copy |
| `Working/Translation/BUILD_BATCHES.md`, `build_batches.json` | regenerated by `t23_closeout.py --write` | previous copies |
| `MODLOG.md` | appended `## 2026-11-07 · VX — gate V, and the approval request (V-07)` | delete that section |
| `Working/Q/APPROVAL_REQUEST.md` | new | delete |
| `tmp/freebuff/reports/verify-v07-gate-vx.md` | this report | delete |

No `Builds/` tree was written; the dropzone sim root from V-06 was left as the last case left it.

## 5. UNKNOWNs

* **Runtime behaviour of everything above** — the test ban stands; the gate authorises a decision, not
  a result.
* **Whether the operator accepts the disclosed gaps** — that is the decision the request asks for.
* **D-2's resolution** — reopened; until it is answered, B-12 and the battle half of the mode pair
  stay unbuilt, and no amount of Q-1..Q-3 testing changes that.
* **The brief's 6.1 cm and "skew_health not carried"** — both are contradicted by the shipped bytes
  and by 8390/8397; which document is authoritative is a records question, not a build one.
