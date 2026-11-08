STATUS: DONE — T-FX16's search term located (`canon_trail` + `shell_trail`, the rule's `match` list at `t17_fx.py:154`), run over the 955 paths with 15 candidates, `--check` green (27/27, exit 0).

## Files

| file | what |
|---|---|
| `Working/Translation/FX16_TERM.md` | 132 lines: verdict, method, candidate table with counts, what the zero means, the one-line repair (text only) |
| `Tools/scripts/t_fx16_term.py` | new script, `--write` / `--check`; derives 955 / 589 from `FX_TABLE.jsonl` with `t17_fx.py`'s own rule |
| `tmp/freebuff/reports/t-fx16-term.md` | this report |

Untouched (mtime Oct 28, before this task): `Working/Translation/T13_FX.md`,
`Working/Translation/t17_fx.json`, `Tools/scripts/t17_fx.py`; `T_ROWS.jsonl` not opened for
writing either.

## Verbatim commands

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_fx16_term.py --write
cd "E:/Modding/JustCause3/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_fx16_term.py --check
```

`--write` and `--check` both exit 0; `--check` reports the doc byte-identical to the re-derivation.

## The answer

**The term is `canon_trail` plus `shell_trail`.** It is decided, not guessed: it is the `match`
list of the T-FX16 rule in `Tools/scripts/t17_fx.py` (line 154), the list `derive()` feeds to the
`no_paths` absence test. Both needles return 0 of 955, and their union returns 0 — so the
published "0 of 955" is reproduced exactly.

Counts per candidate over the 955 distinct `.effc` paths (vehicle-carried 589 in brackets):

| candidate | all / 955 | vehicle / 589 | note |
|---|---:|---:|---|
| `canon_trail` | 0 | 0 | decoded needle |
| `shell_trail` | 0 | 0 | decoded needle |
| `cannon` | 0 | 0 | row text; zero too (spelling: the fleet writes `canon`) |
| `trail` | 84 | 46 | the broad word; does **not** reproduce 0 |
| `bullet` | 23 | 16 | row's own "tracer on the bullet" |
| `projectile` | 1 | 0 | BmAK group name |
| `round` | 11 | 10 | row text |
| `rocket` | 5 | 5 | BmAK name `Batmobile_JokersRocket_Trail` |
| `mud` | 1 | 0 | BmAK name `Batmobile_Mud_Trail` |
| `canon` | 1 | 1 | one-n control: `tank_canon_muzzleflash.effc` |
| `tracer` | 0 | 0 | T-FX12 control; zero too |
| `spark_trail` | 8 | 3 | T-FX19 control |
| `exhaust` | 39 | 37 | T-FX7/8 control |
| `smoke` | 29 | 20 | control |
| `missile` | 30 | 25 | T-FX14 control |

## Two findings that matter beyond the count

- **Zero alone identifies nothing.** Four candidates return 0 (`canon_trail`, `shell_trail`,
  `cannon`, `tracer`) for unrelated reasons, so a bare "0 of 955" is not evidence until the needle
  is printed beside it. That is the defect the row has.
- **The zero is narrow, not "no trail exists".** 84 paths carry `trail`, 30 carry `missile`,
  23 carry `bullet`. What is absent is only an effect *named* a cannon/shell trail. Whether one of
  the 84 is functionally that trail is a content question, not a name search — left UNKNOWN.
- The `cannon`/`canon` pair is a real trap: the two-n spelling returns 0 while `canon` finds the
  fleet's tank flash, so a sloppy reconstruction could "prove" an absence where a file exists.

## Proposed repair (text only, not applied)

> 0 of 955 match `canon_trail` or `shell_trail` over all distinct `.effc` paths (`t17_fx.py` T-FX16 `match`)

No row, ledger, `T13_FX.md` or `t17_fx.json` was edited; the row's conclusion is unchanged by
naming the term, since the count stays 0.

## UNKNOWNs

- Whether a JC3 cannon-round trail exists under another name — the 84 `trail`, 30 `missile` and
  23 `bullet` paths were counted, not opened one by one.
- Whether the BmAK trail needs an `.effc` at all: the row's tracer-texture answer rests on
  `WEAPONS.md` §6 and was not re-tested here.
- Runtime behaviour: nothing launched, the test ban stays.
- Whether the two needles are complete for the feature: the rule also names no `trail` fallback, so
  a differently-named JC3 file would never be found by this test — that is a design limit of the
  probe, not a measured absence.

## Labels

Decoded: the 955/589 pools and every count, the `match` list and its line number, the row's
`absence` record, the `T13_FX.md` proof string. Derived: which candidate the row means, the
reading of the zero set, the proposed proof line. UNKNOWN: the list above.
