# Independent review — B-08 · Effect attachments

Reviewer: Buffy (not the author). Date 2026-10-31. Read-only: no file edited except this report; no
game launched; no git.

Card: `GRAB_BACKLOG.md` §8 `#### B-08 · Effect attachments   S · deps: B-05, T-17 · serves: FX-1…4`
Done line: *"every effect path resolves; usage hash exists in the fleet vocabulary."*

## VERDICT: **minor issues**

The card's two Done criteria pass on a re-run, every Out path exists, the numbers are computed by the
script rather than typed, and the genuinely unknown parts (effect-matrix axis, loose-`.epe` install)
are labelled UNKNOWN. Five issues are recorded below; one is a **factual claim the coordinates
contradict** (the donor has one emitter per side, not "two emitters per pipe", so the build doubles
the emitter count at one nozzle and the doc rationalises it as the donor's density). None of them
invalidates the delivered `.epe`; the fix for the first is either a one-line deletion in a later card
or a Q-1 observation. No rework of the build is required to make the Done line pass.

## Check output (verbatim)

```
$ python Tools/scripts/bm_fx.py --check
PASS: Builds/bm-008/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe 467 -> 467 objects, 2 mat edit(s) on socket Afterburner (JetSMove)
  Done 1  effect paths: 48 effect objects / 32 distinct Effect hashes, 32 resolve to exactly one of the fleet's `.effc` paths, 0 unresolved; T-17 chosen paths 12/12 in the vocabulary; flame path effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc in the build tree = True (donor container set 74 `.effc`)
  Done 2  usage vocabulary: 89 (usage, object) pairs over the 155-value fleet vocabulary, 0 outside; the 2 emitter(s) carry [4197885156] = ['EngineNitro']
CHECK_EXIT=0
```

Side effect of the check: it rewrites `tmp/b08/built.xml`; its sha256 was `fc209d2f7f0dd42031f785e70b03a7d2148e2ffd3271d0e4941eb64a0552c377` before and after, so the run is deterministic and changed nothing.

## Issues

### 1. "The donor runs two emitters per pipe" — the data says one per side (claim not supported)

- `MODLOG.md:18363` — *"the donor runs two emitters per pipe (each points at a **dual** exhaust
  `.effc`), so a one-nozzle car keeps the pair at the one socket"*.
- `Tools/scripts/bm_fx.py:22` — same sentence in the module docstring.
- `MODLOG.md:18430` (limit 2) restates it as *"2 objects × a *dual* `.effc` = the donor's own
  per-pipe density"*.

The recorded `old` matrices in `Working/Effects/bm_fx_edits.json` (`edits[0].old`, `edits[1].old`)
are the donor positions and differ **only in x**: `+0.4101563` and `-0.4101563`, same
`y 0.3728027`, same `z 2.47998`. Two objects at one point per side is **one emitter per pipe**, not
two. Moving both onto the single `Afterburner` nozzle therefore places **two identical dual-pipe
effects at the same point** (likely 2× particle density), while the justification says this matches
the donor's per-pipe density. Whether the duplicate is visually wrong is genuinely UNKNOWN (it is a
Q-1 observation), but the causal claim is contradicted by the build's own spec. Recommended
correction: say "one emitter per side, both kept on the single nozzle → two emitters at one point;
density is UNKNOWN, probe with Q-1 #5" — or drop one emitter in a later card.

### 2. Done 1's "every effect path resolves" is fleet resolution, not loadability in this entity

The check resolves each `Effect` hash against the 955 `.effc` paths in `Research/JC3Grab/FX_TABLE.jsonl`
and separately requires only the **flame** path to exist in the build tree or in the donor container
(`Tools/scripts/bm_fx.py:446-451`). Re-computed from the built graph (`tmp/b08/built.xml`):

```
effect objects 48 distinct hashes 32
hashes with no fleet path 0
distinct hashes whose .effc is NOT in the donor .ee: 2
    ('ShellEjection', 'effects/jc_weapons/50_cal/bullet_eject_capstone.effc')
    ('Fire_AI', 'effects/jc_weapons/muzzle_flash/rico_50cal_muzzleflash.effc')
```

So **30/32** distinct effect paths ship inside the donor `.ee`'s 74-effect container; 2 resolve only
across the fleet (they are weapon-effect objects inherited from B-05's APC clones). The Done output
is honest as written ("resolve to exactly one of the fleet's `.effc` paths"), but the card's short
Done line ("every effect path resolves") and the `MODLOG` Done-1 heading read stronger than what was
proven. Note that the `MODLOG` start entry (`MODLOG.md:18305`) does disclose the 3 objects that miss
the donor set, but the done section does not carry that caveat. Recommended: print "30/32 in the
donor container, 2 fleet-only (weapon objects, B-06's payload)".

### 3. Tautological count in the Done-1 line

`Tools/scripts/bm_fx.py:519-520` prints

```
T-17 chosen paths {d['chosen_paths']}/{d['chosen_paths']} in the vocabulary
```

The numerator and denominator are the same variable, so the line always reads "12/12" even if a
chosen path were outside the vocabulary (that case fails separately via
`chosen_outside_vocabulary`, so it is a reporting defect, not a missed check). It is quoted as
evidence in `MODLOG.md:18377` and in `tmp/freebuff/reports/B-08.md`. Recommended: `12/{len(T-17 rows
with a chosen path)}` or drop the ratio.

### 4. Receipt has no `budgets` block (R9 reporting)

`Builds/bm-008/receipt.json` keys: `base, card, counts, done, edits, epe, flame, installed, rows,
schema, socket, tag, world` — no `budgets`. `bm-002`, `bm-007` and `bm-009` receipts do carry one.
R9 says "Every build reports both [Model 4,915 KB, Texture 7,065 KB]". Here the build adds no model
or texture (only the `.epe`, same 124,520 B), so there is no budget risk — but the report is missing.
Recommended: inherit `bm-005`'s two numbers and state "unchanged" rather than omit the block.

### 5. The `aafdiff` evidence does not name `--hash`

`MODLOG.md:18409` quotes *"changed 1 [.epe]"*, but `aafdiff.py` compares **sizes** unless `--hash` is
passed. Re-run without it:

```
| Common, identical content | 689 |
| Common, **different content** | 0 |
```

and with it:

```
| Common files with different content (1) |
by extension: `.epe` x1
| 124520 | 124520 | +0 | .../v0300_car_kensington_sportsmuscle_civilian_01.epe |
```

The claim is true only under `--hash`; the command as documented reproduces "0 changed" and looks
like the build did nothing. Recommended: quote the command with `--hash`.

### 6. Machine-absolute path inside the generated spec (hygiene)

`Working/Effects/bm_fx_edits.json:274` — `"expected_xml": "E:\\Modding\\JC3-Batmobile\\tmp\\b08\\built.xml"`.
Every other path in the spec is repo-relative through `E.rel`, so this one is inconsistent and
non-portable (it also makes the R-1 pipeline set carry a machine path). No functional effect; the
check regenerates it every run.

## Spot-checks (value, where verified)

| # | value in the doc | where checked | result |
|---|---|---|---|
| 1 | `Afterburner` socket at `(-0.009578, 0.537762, 3.393177)`, bone `JetSMove`, forward `(-3.9e-05, 0, -1)` | `Research/BatmobileGrab/SOCKETS_JC3.json` → socket `Afterburner` | **exact match**, `inside_body_box: true` |
| 2 | 48 effect objects / 32 distinct `Effect` hashes / 0 unresolved | re-counted from `tmp/b08/built.xml` with the same four classes | **48 / 32 / 0** |
| 3 | 89 (usage, object) pairs over a 155-value vocabulary; emitters carry `4197885156` = `EngineNitro` | re-counted from `tmp/b08/built.xml`; `Research/JC3Grab/USAGES.json` | **89 pairs, 57 distinct usages, 155 vocabulary, 0 outside; EngineNitro = 4197885156** |
| 4 | "T-17 chosen paths 12/12" | `Working/Translation/t17_fx.json` → rows with a `chosen` block | **12** (of 17 rows) |
| 5 | "donor container set 74 `.effc`" and flame path inside it | `Research/JC3Grab/FX_TABLE.jsonl`, container endswith the donor `.ee` | **74**; flame path present |
| 6 | "one file changed" between bm-005 and bm-008 | `python Tools/scripts/aafdiff.py Builds/bm-005/aaf Builds/bm-008/aaf --hash` | **689 identical, 0 only-in, 1 changed (`.epe`), 0 byte delta** |
| 7 | objects `467 -> 467` | receipt `counts` + check line | **467 / 467, added 0** |

## What was not re-run (read-only review)

- The 3/3 tamper tests quoted in `MODLOG.md` (they need editing `Builds/bm-008`'s `.epe` and
  re-importing). They are plausible and their failure strings match the code paths in `check()`
  (`world` mismatch, Done 1 unresolved hash, Done 2 outside-vocabulary), but I did not reproduce
  them, so their numbers are the author's, not independently verified.
- The `ConvertProperty` round trip is executed inside `--check` and passed; no separate run was made.

## Summary of the audit questions

| question | answer |
|---|---|
| Do every Out paths exist? | **Yes** — `Tools/scripts/bm_fx.py`, `Working/Effects/bm_fx_edits.json`, `Builds/bm-008/{aaf,receipt.json,install.ps1}`, `tmp/freebuff/reports/B-08.md`; the §12 row is present |
| Does the Done criterion match what `--check` verifies? | **Mostly** — Done 2 exactly; Done 1 verifies *fleet* resolution plus flame presence, not that every referenced `.effc` ships in this entity (Issue 2) |
| Are numbers script-derived (R11)? | **Yes** — 955/48/32/12/155/89/74/467 all recomputed by `bm_fx.py` from the T-17 JSON, FX table, USAGES and the built graph; the only typed text is prose. The tautological `12/12` (Issue 3) is a presentation defect |
| Any value without provenance / guess as fact (R4)? | One unsupported claim (Issue 1). The real unknowns — effect-matrix axis, loose-`.epe` install — are explicitly UNKNOWN (`MODLOG.md:18420-18435`) |
| Member name confused with behaviour (R5)? | **No.** The effect is selected by `hash_jenkins(path)`, the trigger by usage hash → name lookup (`bm_fx.py:121-133`); the card's behaviour (nitro flame at the jet) is what is carried |
| Any claim the data cannot support? | Issue 1, and the Done-1 wording overstates loadability (Issue 2) |
