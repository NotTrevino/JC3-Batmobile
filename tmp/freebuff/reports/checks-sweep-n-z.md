**STATUS: DONE — n..z sweep ran (plus the underscore names), 100 `--check` scripts, 72 ok, 28 red. Nothing fixed.** Page: `Working/Translation/CHECKS_SWEEP_NZ.md` (generated table + the hand-written five-script section); raw rows: `tmp/freebuff/scratch/sweep_n-z.jsonl`; full stdout per script in `tmp/freebuff/scratch/sweep_logs/`.

# Repo health sweep, letters n..z (+ digits, `_`)

`checks_sweep.py` takes a single character range, and the remaining names are split across three
character classes, so it ran three times and the rows were merged before rendering:

```
python Tools/scripts/checks_sweep.py n z --jobs 8 --jsonl tmp/freebuff/scratch/sweep_nz_letters.jsonl
python Tools/scripts/checks_sweep.py 0 9 --jobs 2 --jsonl tmp/freebuff/scratch/sweep_nz_digits.jsonl
python Tools/scripts/checks_sweep.py _ _ --jobs 2 --jsonl tmp/freebuff/scratch/sweep_nz_under.jsonl
cat sweep_nz_{letters,digits,under}.jsonl > tmp/freebuff/scratch/sweep_n-z.jsonl
python Tools/scripts/checks_sweep.py --render tmp/freebuff/scratch/sweep_n-z.jsonl \
       --md Working/Translation/CHECKS_SWEEP_NZ.md
```

- **n..z: 98 scripts**, 72 ok, 26 red.
- **0..9: none** — `no --check scripts under Tools/scripts for '0'..'9'`, so the range contributed no rows (the log records it).
- **`_`: 2 scripts**, both red (`_apply_move.py`, `_patch_bin.py`).
- 100 rows in total. No `x`, `y` or `z` file carries `--check`, which is why the rendered title reads `letters _..w` — the render titles the page from the first letters actually present, not from the requested range.

Each script ran under `tmp/freebuff/scratch/checks_guard.py` (audit hook, 300 s wall limit, `stdin`
closed, cwd = repo root); exit 77 = the guard blocked a write outside `tmp/`.

| candidates | ok | red | real failure | missing dependency | missing input file | usage error | skipped (write guard) | timeout |
|---|---|---|---|---|---|---|---|---|
| 100 | 72 | 28 | 18 | **0** | 2 | 2 | 6 | 0 |

No dependency was missing anywhere in this half. The two `missing input file` rows are not really
missing inputs — see the note under the table.

## Every failing script, with its reason class

### real failure (18)

| script | exit | evidence from its own output | reason class |
|---|---|---|---|
| `rc_diff.py` | 1 | `FAIL both trees hold 705 files  706 / 723`; `FAIL MODLOG has no bm-RC2 entry (the documented finding)`; `check FAIL (2 failing assertion(s))` | RC1-vs-RC2 diff record: both stated invariants are wrong against the trees, and the md's claim about MODLOG is contradicted |
| `reset_delta.py` | 1 | `attached 77  unattached 138  newer 215` / `CHECK FAIL` (the older h..z page recorded 76 / 122 / 198) | the re-derivation disagrees with the stored record; the counts themselves moved since the earlier sweep, so the record is stale *and* the underlying data changed |
| `reset_status.py` | 1 | `FAIL` / `- Research/RESET_STATUS.md is stale` | stale document vs re-derivation |
| `reset_status2.py` | 1 | `FAIL` / `- Research/RESET_STATUS2.md is stale` | stale document vs re-derivation |
| `review_g321.py` | 1 | `FAIL: report differs from a fresh render` / `FAIL: json differs from a fresh build` | both stored artefacts drifted from their producer |
| `review_splits.py` | 1 | `FAIL: SPLIT_FACES.json differs from the re-derived record` | stored JSON drifted |
| `sampler_unknowns.py` | 1 | `FAIL: SAMPLER_UNKNOWNS.md differs from a fresh rebuild` | stale document |
| `t10_reopen.py` | 1 | `FAIL T10_OPEN_ROWS.md stale: the text differs` / `1 problem(s)` | stale document |
| `t12_audio.py` | 1 | md diff at `-E:\Modding\_JC3grab\audio\` / `+E:\Modding\_gamedata\JC3grab\audio\` | stale document: game-data root rename `_JC3grab` -> `_gamedata/JC3grab` |
| `t12_parts.py` | 1 | md diff at `_BmAKgrab/anims/keys/` -> `_gamedata/BmAKgrab/anims/keys/` | stale document, same rename family (BmAKgrab) |
| `t23_closeout.py` | 1 | `FAIL §11 has 11 decisions, expected D-1...D-10`; `FAIL BUILD_BATCHES.md differs…`; `FAIL build_batches.json differs…`; `3 problem(s)` | gate TX bookkeeping: the section it parses has one more decision than the D-1..D-10 it asserts, and both generated records are stale |
| `t7_weapons.py` | 1 | md diff inside the T-WP6 (winch) row: the stored prose claims "no winch/rope/tow module type", the re-derivation states the measured 52-type / 1,421-path vocabulary and 103-class census | stale document whose *evidence wording* changed, not just a path |
| `t9_interaction.py` | 1 | `FAIL: json section changed: source_digest`; md diff `digest da864a28edcbcbff` -> `a08510e57dd54a7f` | the upstream `Research/JC3Grab/INTERACTION.json` changed under the record; stored digest and prose are stale |
| `t_row_evidence.py` | 1 | md diff hunk at line 118, `FAIL document differs from the regenerated text` (its prose cites `Working/TrueScale/stations.json`) | stale document |
| `t_st7b.py` | 1 | `FAIL: json drifted` / `FAIL: markdown drifted` | both stored artefacts drifted |
| `t_vnf_six.py` | 1 | `+* PASS every file opened for grading exists (18 files)` then `FAIL document differs from the regenerated text` | stale document (content changed, the file-existence assertion still passes) |
| `v05_predictions.py` | 1 | `FAIL PREDICTIONS.md differs from the re-derived sheet`; `FAIL: 28 Q checks parsed, 20 predicted, 7 blocked, 1 excluded, 0 without a row` | the V-05 sheet is stale and **7 of 28 Q checks have no predicted value** (blocked, per the tool's own rule) |
| `v_joint_trace.py` | 1 | `oracles: 20/21 pass` / `DRIFT: Builds/bm-RC2/verify/joint_trace.md differs from the regenerated bytes` | one oracle red plus the RC2 verify page drifted from its re-derivation |

### usage error — `--check` not accepted (2)

| script | exit | evidence | reason class |
|---|---|---|---|
| `t5_apply.py` | 2 | `t5_apply.py: error: the following arguments are required: --aaf` (it has `--check-only`) | interface mismatch: `--check` is not this script's flag; no check ran |
| `t_rows.py` | 2 | `usage: t_rows.py [-h] {build,check,summary} ...` / `error: the following arguments are required: cmd` | interface mismatch: `check` is a **subcommand**, so this sweep never exercised it |

### missing input file (2) — the classifier's label, not a real missing input

| script | exit | evidence | reason class |
|---|---|---|---|
| `_apply_move.py` | 1 | `FileNotFoundError: [Errno 2] No such file or directory: '--check'` | the script takes a **file path** as its argument and opens it; the sweep's `--check` token became that path. Classified `missing input file: --check` by the tool's regex, in truth no `--check` mode exists |
| `_patch_bin.py` | 1 | same signature | same |

### skipped — writes outside `tmp/` (6, all exit 77)

| script | blocked path |
|---|---|
| `t10_damage.py` | `E:/Modding/_gamedata/JC3grab\tmp_t1\default_extended_effect_usages.vmodc` |
| `t3_fleet.py` | `E:\Modding\JC3-Batmobile\Working\Translation\T3_FLEET.md` |
| `v01_gates.py` | `E:\Modding\JC3-Batmobile\Builds\bm-RC1\verify\v01` |
| `v03_wiring.py` | `E:\Modding\JC3-Batmobile\Builds\bm-RC1\verify\_v03.epe` |
| `v03_wiring2.py` | `E:\Modding\JC3-Batmobile\Working\RC\verify-bm-RC2\_v03.epe` |
| `v05_combat.py` | `E:/Modding/_gamedata/JC3grab\tmp_t1\default_extended_effect_usages.vmodc` |

A skip is **not** a pass: these checks scratch a copy outside `tmp/` before comparing, so under this
harness their result is UNKNOWN. Note that three of them (`v01_gates.py`, `v03_wiring.py`,
`v03_wiring2.py`) are the release-candidate gates; `v01_gates.py` and `v03_wiring.py` also still
target **bm-RC1**, not RC2.

## The five whose failure would block the release candidate most

Written into the page as its own section (it is hand-written prose on top of the generated table, so
`--render` would drop it). Chosen by what each script asserts, not by how loudly it failed:

1. **`v01_gates.py` — the V-01 gate set itself** (aafdiff / `.toc` records / `spec_check.py` / both
   hard budgets / parts re-read / `jc3adf` re-read / `.epe` round trip / value read-back through the
   packed `.ee`). If this is red, the candidate ships bytes the game cannot read or overruns Model
   4,915 KB or Texture 7,065 KB. **Skipped here** (guard blocked `Builds/bm-RC1/verify/v01`) and it
   still points at RC1 — unjudged.
2. **`v05_predictions.py` — the V-05 predicted-results sheet.** Every Q check needs a prediction and a
   pass band before any in-game test; an unparsed id or a blocked row breaks that precondition. Red,
   with **7 of 28 Q checks blocked** — the RC's own success criteria are partly undefined.
3. **`v_joint_trace.py` — the row -> manifest -> generator -> built-tree joint chain.** This is the
   exact payload RC3 adds (turret/cannon hinges at constraint index 11 and 12), and it recomputes 21
   oracles against the built tree. Red: 20/21 oracles, RC2 verify page drifted.
4. **`v03_wiring2.py` — the V-03 wiring gates** (every `SWeaponPoint` names a real part; every
   `objectid` and asset path resolves; audio 5 slots / 45 GUIDs / 5 events; Rebel Drop hash and leaf
   ship). A dangling reference is a crash or a silently missing weapon, and its G4 delegate
   (`bm_audio.py --check`) is already red in the a..g half. **Skipped here** — unjudged.
5. **`rc_diff.py` — RC1 vs RC2, file by file.** The only proof the candidate differs from its
   predecessor only where planned; without it no RC can be certified a controlled change. Red on both
   its invariants (file counts 706 / 723 against a stated 705; and the MODLOG claim it was written to
   demonstrate).

Release-adjacent, also red: `t23_closeout.py` (gate TX bookkeeping, 3 problems), `reset_status.py` /
`reset_status2.py`, `v05_combat.py` (guard-blocked) and `t_rows.py` (never actually exercised here).

## Notes and limits

- **`checks_sweep.py` byline quirk (not fixed).** The rendered page says it was generated with
  `--md Working/Translation/CHECKS_SWEEP_A.md` — `page()` interpolates the literal a..g filename
  regardless of the path passed. The title's range (`_..w`) is likewise derived from the letters
  present. Neither affects the rows; both are recorded rather than patched, and the page was not
  hand-edited apart from the added section.
- **Cross-sweep comparison.** The older `Working/Translation/CHECKS_SWEEP_H.md` came from a different
  driver and cannot be diffed row for row; the visible deltas are `t3_fleet.py` (then `ok`, now
  guard-blocked on `Working/Translation/T3_FLEET.md`), `v03_wiring2.py` (then `real failure` on the
  `bm_audio` delegate, now blocked before it gets that far at `Working/RC/verify-bm-RC2`), and
  `reset_delta.py` (counts 76 / 122 / 198 -> 77 / 138 / 215).
- **Nothing touched.** Only `Working/Translation/CHECKS_SWEEP_NZ.md` and files under `tmp/` were
  written by this pass; no script, build, research record or game-data file was edited, and no fix was
  attempted. The six guard blocks are the evidence that no `--check` reached `Builds/`, `Working/` or
  the game data.
- **Page integrity.** Re-rendering the merged JSONL to a scratch page reproduces the delivered page's
  generated part byte for byte; the only difference is the appended five-script section.
