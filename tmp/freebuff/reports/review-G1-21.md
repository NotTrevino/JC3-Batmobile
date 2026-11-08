# Independent review — G1-21 · Modes and transformation values

Reviewer: not the author. Read-only pass: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/`, `Working/` or any game file was modified. Only this file was written. No game launched, no
commit, no secrets.

Card: `GRAB_BACKLOG.md:544-550` (deps G1-08, serves MOD-1/2 and HDL-6). Tracker row:
`GRAB_BACKLOG.md:1289`. MODLOG section: `MODLOG.md:8733` (§"G1-21 · Modes and transformation
values — done (no build, 2026-10-25)").

Outputs: `Research/BatmobileGrab/MODES.md` (341 lines), `Research/BatmobileGrab/MODES.json`
(2,637 lines, 65,442 B), `Tools/scripts/grab_modes.py` (739 lines).

**Sources read for this review:** `BMSDK_OFFSETS.json` (what the classes declare, via the script's own
`build()`), `objects.jsonl` (raw archetype tag stream), `OFFSETS.json` (GRB-11 naming), `T_ROWS.jsonl`
(the four ledger rows), and a read-only re-run of `build()` and `write_markdown()` in memory.

## VERDICT: needs rework (narrow)

The record itself is good work: 107 declared family fields, 46 serialised, 61 absent, values read
from the archetype tag stream with the lookup pinned to the declaring class, units attached with a
stated basis, and every value I spot-checked reproduces exactly. The note is a genuine render of the
JSON (`write_markdown(build())` equals `MODES.md` byte for byte today).

But the card cannot currently prove itself, and the note carries one false claim about its own
evidence:

1. **`grab_modes.py --check` fails right now (exit 1, `STALE`)** — the tracker row's "`grab_modes.py
   --check` (26/26)" no longer reproduces. Root cause is in the generator: it writes the *live*
   ledger `dispo`/`why` into `MODES.json`, and a later card changed `T-BM1` from `out` to
   `superseded`, so the artifact went stale through no fault of this data.
2. **`MODES.md:6-7` names the wrong field at the wrong offset** ("offset 0x0320 is
   `BattleModeLatSlipScale` … and something else entirely on `RBasicProjectile`") — that sentence is
   hardcoded in the renderer, and the artifact says 0x0320 is `BattleModeTrailingSteerFactorMoving`
   on `RVehicleSimBatmobile` and `SVehicleWheel.BattleModeSteerBias` on the wheel class; no
   `RBasicProjectile` tag carries offset 0x320 at all.

Neither fault is deep, but the first is a red gate and the second is exactly the class of typed
claim R4/R11 exists to stop, so the card is not `done` as it stands.

## Check output (verbatim)

```
$ python Tools/scripts/grab_modes.py --check
STALE: MODES.json does not match a fresh build (run --write)
EXIT=1
```

Read-only diagnosis (no file written) — `build()` re-run in memory and compared to the stored artifact:

```
$ python - <<'EOF'
import sys, json
sys.path.insert(0,'Tools/scripts')
import grab_modes as G
fresh=G.build(); disk=json.load(open('Research/BatmobileGrab/MODES.json',encoding='utf-8'))
print('summary equal', fresh['summary']==disk['summary'])
print('checks equal', fresh['checks']==disk['checks'])
ff={(e['declaring_class'],e['field']):e for e in fresh['fields']}
df={(e['declaring_class'],e['field']):e for e in disk['fields']}
print('fields equal', ff==df, len(ff), len(df))
print('ledger dispo fresh', [(r['id'],r['dispo']) for r in fresh['ledger_rows']])
print('ledger dispo disk ', [(r['id'],r['dispo']) for r in disk['ledger_rows']])
print('md identical to a fresh render', open('Research/BatmobileGrab/MODES.md',encoding='utf-8').read()==G.write_markdown(fresh))
EOF
summary equal True
checks equal True
fields equal True 107 107
ledger dispo fresh [('T-BM1', 'superseded'), ('T-AC1', 'out'), ('T-RA1', 'out'), ('T-SR1', 'out')]
ledger dispo disk  [('T-BM1', 'out'), ('T-AC1', 'out'), ('T-RA1', 'out'), ('T-SR1', 'out')]
md identical to a fresh render True
```

So the failing gate is **not** the mode data: all 107 field entries, all 26 checks and the note are
current; the only difference is the embedded ledger `dispo`/`why` block.

## Issues

### 1. (blocking, gate) `--check` is red; the card's own verification no longer passes

`Tools/scripts/grab_modes.py:365-384` reads `Working/Translation/T_ROWS.jsonl` and stores each served
row's `dispo`/`why` into `MODES.json` (`ledger_rows`); `:718-729` then requires `disk == build()`.
`T-BM1` is `superseded` in the ledger today (`MODES.json` recorded `out` on 2026-10-25), so any later
translation work reddens this card. `GRAB_BACKLOG.md:1289` and `MODLOG.md:8798-8799` both claim
`--check` → `26/26`, which no longer reproduces.

The ledger row today:

```
$ python - <<'EOF'   # Working/Translation/T_ROWS.jsonl
...print(r["id"], r.get("dispo"), "|", r["cells"][1])
T-BM1 superseded | `BattleMode*` (9), `TurnOnSpot*` (3), `TransformationTurn*` (2), `TurningModeMaxSpeed`, `ArmourModeDamageReduction`
T-AC1 out | `AirControlYawTorqueFactorMax` 8000
T-RA1 out | `ImpactRoadAssist*` (90000 / 30000 / 2000), `PMDodge*`, `BattleDodgeImpulse`, `VehicleShovingTorque` 10000, `KillFlip*`, `KillKeepyUp*`, `ImpactShake*`
T-SR1 out | `JumpRampRightingTorque` 2000, `JumpNoRampRightingTorque` 2000, `StayUprightConstraintSetup/Instance`
```

Why it matters: `--check` is the only thing that proves the Done line, and it is the command the
tracker cites. A card whose check fails is not `done` under §0.3/§0.7, whatever the data says.

Fix, inside the generator (never by hand-editing `MODES.json`): keep the *tokens*, `counts` and
`numbers` the check consumes, but either drop `dispo`/`why` from the artifact or stop comparing them
— they are another card's decision record, not this card's data. Then `--write` once and `--check`.

### 2. (data, R4/R11) The note's opening justification names the wrong field at the wrong offset

`Research/BatmobileGrab/MODES.md:6-7`:

```
The lookup is class-scoped on purpose: offset 0x0320 is `BattleModeLatSlipScale`
on `RVehicleSimBatmobile` and something else entirely on `RBasicProjectile`, so a bare
offset match would invent values.
```

This sentence is hardcoded prose in the renderer (`Tools/scripts/grab_modes.py:471-473`), and both
halves are contradicted by the record it is describing:

- `MODES.md:102` — `BattleModeTrailingSteerFactorMoving` | **0x320** | float | -0.25 ×4;
  `MODES.md:89` — `BattleModeLatSlipScale` | **0x2d4** | float | 0.75 ×4. So the field at 0x320 on
  `RVehicleSimBatmobile` is not the one the sentence names.
- The other owner of 0x320 in the tag stream is the wheel, not a projectile: `MODES.md:203` —
  `BattleModeSteerBias` | 0x320 | `SVehicleWheel`, not serialised. A scan of `objects.jsonl` finds
  **zero** `RBasicProjectile` tags at offset 0x320 (or 0x2d4).

```
$ python - <<'EOF'   # raw tag stream, the data the script reads
... for cls=="RBasicProjectile" and offset in (0x320,0x2d4)
RBasicProjectile tags at 0x320/0x2d4: [] count 0
0x320 RVehicleSimBatmobile BattleModeTrailingSteerFactorMoving {'...': -0.25, ...}
0x320 SVehicleWheel BattleModeSteerBias {}
```

Why it matters: this is the sentence that justifies the whole method (and the review of `G1-21` would
otherwise read it as evidence for class scoping). It is typed, it is wrong, and the correct values are
in the same file two sections below and in `MODLOG.md:8750-8752` (which gets it right:
"offset 0x0320 is `BattleModeTrailingSteerFactorMoving` on `RVehicleSimBatmobile` and
`SVehicleWheel.BattleModeSteerBias` elsewhere"). The doc's own §Wheel table names the real
counter-example, so the fix is one sentence read from the record: derive the pair
(`offset`, declaring class) for one field that two classes share, or drop the example and state the
method without one.

### 3. (coverage) `--check` never reads `MODES.md`

`grab_modes.py:720` only tests `os.path.isfile(md_path)`; the staleness test at `:724` diffs the JSON
alone. A hand edit to the note therefore passes the gate — the failure mode that the G1-14 review
found in `DAMAGE_RULES.md`, and that note now closes by re-rendering and diffing byte for byte.
Today the file happens to equal a fresh render (verified above), so nothing is wrong *now*, but the
gate cannot catch drift, and the note calls itself "Generated by ..." without a check that enforces
it.

Fix: render `write_markdown(doc)` in `main()` and compare it to the file, printing `md: PASS|FAIL`
next to the JSON line.

### 4. (Done-line fidelity) the check proves "declared", not "appears with its value"

The card's Done is "every field named in rows T-BM1, T-AC1, T-RA1, T-SR1 appears **with its value**".
For a single-name token the check is `bool(hits)` (`grab_modes.py:406-408`), and its detail prints
`serialized=False` without failing; for a wildcard token it is likewise `bool(hits)`
(`:393-396`). The 61 fields with no value in the files are correctly exempt by construction, but a
token that resolved only to a declared-but-unsigned field would also pass, and the ledger's own
counts (9 / 3 / 2) are never asserted — they are reconciled in prose (`MODES.md:54-70`) and merely
printed next to the derived numbers.

Not wrong today (every single-name token in those four rows does resolve to a serialised field — the
`### Checks` table prints `serialized=True` for all of them), but the check does not verify the Done
wording it is cited for. Fix: require `serialized` for a single-name token, and assert
`serialised (sim) == ledger count` for the three parenthesised tokens.

### 5. (R4, journal only) the Joker behaviour claim goes beyond the tag stream

`MODLOG.md:8774-8778` says the Joker archetype "does not serialise them at all" and concludes "the
Joker car has no armoured-mode damage reduction and no pursuit/battle dodge in its archetype". The
absence is real (the values dict has three packages, not four), but in a cooked UE3 archetype an
untagged property is not zero — it falls back to the class default in the unshipped CDO, which is
exactly the gap this card states elsewhere ("the number that actually runs comes from the engine or
BmScript defaults"). The doc is careful (`—` in the Joker column, `MODES.md:152-153`, `:176-178`);
the journal is not, and that sentence is what a later card will quote. Reword to "no tag in the Joker
archetype at that offset; the running value is a CDO default, UNKNOWN from the files".

### 6. (minor, R11) typed numbers survive in the generated prose

These literals live in `write_markdown`, not in the record, and only happen to agree with it:

| line | typed text | record says |
|---|---|---|
| `MODES.md:29` (from `grab_modes.py:494-495`) | "`BattleModeThrottleSpeed` (10) and `BattleModeYawOffset` (0)" | 10 and 0 — matches, but typed |
| `MODES.md:66` (from `:529-531`) | "the nine scalars … the tenth serialised `BattleMode*` member" | 10 serialised sim fields (1 curve + 9 floats) — matches, but counted by hand |
| `MODES.md:56` (from `:510-512`) | "T-BM1 writes `BattleMode*` (9), `TurnOnSpot*` (3), `TransformationTurn*` (2)" | the ledger's counts, but typed |

R11 says counts are generated. They are right today; they would silently go stale if the archetypes
or the ledger changed, which is precisely what happened to the ledger block in issue 1.

### 7. (minor) the "in this record" column collapses four packages into one

`describe()` (`grab_modes.py:643-650`) prints `next(iter(f["values"].values()))` — the first package
in the record — as "value X" in the Ledger coverage table. For the three fields the Joker archetype
does not carry (`ArmourModeDamageReduction` → "value 0", `BattleDodgeImpulse` → "value 150000",
`PMDodge*`) the row therefore hides that one package has no tag, and issue 5 grows out of that
reading. The per-class tables above render all four columns, so the information exists; the summary
should say "3 of 4 packages" (or name the value per package) rather than print one.

## Spot-checks (value → where verified)

| value in doc | doc line | verified at (raw tag stream, `objects.jsonl`) |
|---|---|---|
| `TurningModeMaxSpeed` = 600 cm/s in all four packages | `:86` | `RVehicleSimBatmobile` offset `0x2c4` (708): `FloatProperty 600.0` ×4 (Funhouse, Joker, MK2, SF) |
| `ImpactRoadAssistFactor` = 90000 | `:144` | `RVehicleBatmobile` offset `0x1764`: `FloatProperty 90000.0` ×4 |
| `KillFlipTorqueDuration` = 0.5 / 0.5 / 0.75 / 0.5 (Joker 0.75) | `:165` | `RVehicleBatmobile` offset `0x1c1c`: `0.5, 0.5, 0.75, 0.5` (Joker 0.75) — doc column order V2/MK2/Joker/Funhouse matches |
| `BattleModeVSpeedCurve` 3 points: 0→60, 600→40, 1200→30 | `:248-256` | struct tag at `RVehicleSimBatmobile` 0x218, `count: 3`, items `[0.0, 60.0, …] [600.0, 40.0, …] [1200.0, 30.0, …]` |
| `ImpactShake` struct 0x4 = 0.33, 0x8 = [150,150,30], 0x38 = [1000,1000,200] | `:262-270` | struct tag at `RVehicleBatmobile` 0x1c28 (SF): `0.33000001311302185`, `[150,150,30]`, `[1000,1000,200]`, `AdvancedOptions`, `true` |
| summary 107 declared / 46 serialised / 61 absent / 31 identical in all four | `:12-16` | `build()["summary"]`: `declared 107, serialized 46, not_serialized 61, same_in_all_four 31` |
| "nine scalars + `BattleModeVSpeedCurve` = tenth serialised sim member" | `:66-68`, `:86-110` | `build()`: 10 serialised `BattleMode*` fields on `RVehicleSimBatmobile`, 1 of them `FInterpCurveFloat` |
| 26/26 checks | `:327` | `build()["checks"]`: 26 entries, 26 `pass: True` (unchanged from the stored artifact) |

Every spot-check reproduces. The data side of this card is sound; the failures are the gate
(issue 1), the one typed claim (issue 2) and the coverage gaps around the note (issues 3-4, 6-7).

## Limits of this review

I did not try to re-derive `BMSDK_OFFSETS.json` (the class dump) — I checked that the record uses it
consistently (class-scoped lookup, offset + declared type per row) and that the archetype values it
publishes match the raw tag stream. I did not run the game, so no shipped-vs-CDOD question was
settled: for the 61 fields with no tag and for the Joker-only absences, the running value remains
UNKNOWN, exactly as the note says.
