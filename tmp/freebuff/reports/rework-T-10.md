# T-10 rework — re-opening the `out` rows

**STATUS: DONE.** The review's live failure is fixed (`t10_reopen.py --check` red → **green**), and
7 of its 8 issues are **CONFIRMED** and fixed in the generator; issue 6 is **confirmed except one
sub-item, which is REJECTED** with the command below. No disposition was changed, so no row's
meaning moved: this is a record-wording and check-strictness repair.

Card rules: `GRAB_BACKLOG.md` §0.5 R4 (provenance), R5 (behaviour, not member name), R11 (derived
numbers), R14 (journal). No game launched, nothing written to `D:/Games`, no `.ctunec` or build file
touched, no shared module edited, no hand edit of a generated output, no git.

---

## Per-issue verdicts

### 1. The card's `--check` is red at HEAD — **CONFIRMED**

Before any edit:

```
$ python Tools/scripts/t10_reopen.py --check
FAIL T10_OPEN_ROWS.json stale: the payload differs
FAIL T10_OPEN_ROWS.md stale: the text differs
2 problem(s)
exit 1
```

Cause, verified by diffing the stored payload against `derive()`: exactly one value moved -
`summary.foreign_out_rows` was **25** on disk, **26** re-derived - because the payload baked a
census of the **shared** `T_ROWS.jsonl`, which other cards keep writing. `T10_OPEN_ROWS.md:21`
carried the same number.

**Fix.** The census is no longer part of the compared payload or the document. `derive()` returns
`(payload, census)`; `--write`/`--check` print the census (`later 'out' rows: 26 of 32 cite a proof
…`) and the artifact stores nothing that another card can rot. Proof:

```
grep -c "foreign_out" Working/Translation/T10_OPEN_ROWS.json Working/Translation/T10_OPEN_ROWS.md
→ 0 / 0
```

and tamper 6 below (a synthetic later `out` row appended to the ledger) leaves `--check` **PASS**,
where it used to turn it red.

The review's related note - the doc says "§11 decisions still open … none" while the done section's
PASS string said "decisions open D-2, D-3, D-7" - is a journal artifact, not a data error: the
artifact was regenerated after those decisions were resolved (journaled in T-11's section). Handled
under issue 7 (append-only correction).

### 2. Done clause "no `out` row lacks a proof file" is wider than the check — **CONFIRMED**

`t_rows.py check` never looks at proof files, and `t10_reopen.py` proved only its own 10 rows; for
other cards' `out` rows it accepted a `PROOF_RE` substring match, and:

```
PROOF_RE.search("no notes .md")  → <Match '.md'>
PROOF_RE.search("see G2-99")     → <Match 'G2-'>
```

At HEAD 6 foreign `out` rows failed even that: `T-FX13, T-FX16, T-MD5, T-MD6, T-MD7, T-WLD15` - so
the sentence as written is false today.

**Fix (honest scope + a real citation test).** The document now states the verified scope ("the
`out` rows this card owns, 10/10") and says explicitly that the **wider reading is not asserted as
met**; it is measured by the live census `--check` prints. `PROOF_RE` is replaced by `PATH_RE` (a
backticked repo path that **exists**) + `CARD_ID_RE` (a **real** §7 card id), so `"no notes .md"` and
`"see G2-99"` no longer count. §4 of the doc carries both the scope statement and the census
explanation.

### 3. R5 — a BmAK light-type enum presented as a decoded JC3 behaviour — **CONFIRMED**

Old text: `T10_OPEN_ROWS.md:129` "the battle-mode spotlight (16 entries) is a decoded behaviour value
(`VEHLT_BattleModeLight`, G2-33)"; `:131` "is a real behaviour value on the same light part". The
evidence:

```
Research/JC3Grab/LIGHT_SYSTEM.md:227-228  The same socket also carries 1 `VEHLT_BattleModeLight`
  entry (VEHLT_BattleModeLight -> HeadLight) - that is LGT-2's battle-mode spotlight …
Research/JC3Grab/LIGHT_SYSTEM.md:235      | `behavior` | `HeadLight` | … (VEHLT_HeadLight -> HeadLight, G1-17 mapping) | decoded |
Research/BatmobileGrab/LIGHTS.json summary.by_type  "VEHLT_BattleModeLight": 16, "VEHLT_ForensicsLight": 12
Research/BatmobileGrab/LIGHTS.json summary.by_behavior  "HeadLight": 70, "(none)": 16, "TailLight": 15
```

`VEHLT_*` is the **donor** enum; `HeadLight` is the JC3 behaviour T-18 maps it to (4 rows,
T-L17…T-L20), and the fleet has no battle-light behaviour at all. Merging the donor count (16) with
the JC3 value is exactly the R5 pattern.

**Fix.** `T-LG5`'s split/why/note now read: donor light type, 16 entries, no JC3 behaviour of its
own, `HeadLight` is T-18's mapping, 4 rows carry it (ids printed from `t14_lights.json`), forensics
rig (12 entries) a named omission. The needle is now the mapping string
`VEHLT_BattleModeLight -> HeadLight`, not the bare enum name. Generated output:

```
**Split:** battle-mode spotlight: 16 donor entries -> T-18's 4 `HeadLight` rows (T-L17, T-L18, T-L19, T-L20); forensics rig (12 entries) -> named omission
- `needle` `VEHLT_BattleModeLight -> HeadLight` — the donor rig's 16 `VEHLT_BattleModeLight` entries are a light *type*, not a JC3 behaviour: LIGHT_SYSTEM.md §7a gives the JC3 `behavior` as `HeadLight`, the mapping T-18 uses
```

### 4. R4 — the T-FX4 carrier is overstated — **CONFIRMED**

Old evidence note: "the EMP device's own weapon classes and the entity-level pulse (G2-16)", with a
needle on `CEMPWeapon` - which only proves the class is *named*. `Research/JC3Grab/EMP.md:3`:

```
**Answer: yes for the effect, no as a weapon-slot copy.** … and no vehicle weapon slot in the game
currently holds the engine's EMP weapon class (`CEMPWeapon`).
```

**Fix.** `T-FX4` now says the **effect** has a carrier (`CForcePulse`) and the weapon-slot copy does
not; `CForcePulse` and `no vehicle weapon slot` are needles of their own, and the split says "with no
weapon slot". The ledger `why` in `t_rows.py` was updated to the same text (the check compares them).

### 5. HUD searches are spelling-brittle — **CONFIRMED**

```
$ (walk E:/Modding/JustCause3/_grab/hud/dec, *.as)
as count 260
'armour': 0 files      'armor': 7 files  (9 occurrences, all `chaos_reward_armory` / "armory")
'enemy': 0             'enemycount': 0    'energy': 1 file  (`such energy`, a joke string)
```

The conclusions survived, but a field named `armor` / `enemyCount` would not have been caught.

**Fix.** `T-HUD4` searches `armour` **and** `armor`; `T-HUD9` adds `enemycount`; `T-HUD8` adds
`energy`. Each HUD evidence item may now carry an allow-list, and `prove()` reports what it
explained instead of silently passing. Generated detail:

```
- ok: .../hud/dec: 260 scripts read, 0 unexplained hits of armour, armor; explained: armor 9 all in the allow-list
```

Functional probe (in memory, no file edited): `prove(('hud', …, ['armory']))` →
`{'ok': False, 'detail': '... ui/hud.gfx names armory (9 of 9)'}` - a word the movie really contains
still fails.

### 6. R11 — not every number is derived — **CONFIRMED, except one REJECTED sub-item**

Typed literals in the old script (exact lines):

```
54:  HUD_SCRIPTS = 260
76:  "25 vehicle weapon ids"       79: "11 weapon classes"
225: "the battle-mode spotlight (16 entries)"   (and "12 entries")
95/164/184/187: "103-class" / "52-type / 1,421-path"
734-735: the same two counts in §4
```

All of these are correct today, but nothing recomputes them; `HUD_SCRIPTS` is a typed minimum that
would not follow the directory.

**REJECTED sub-item:** the review lists "`9 arguments`/`6` (T-HUD4 note)" as a literal in `ROWS`.
It is not in the script - `grep -c "9 arguments" Tools/scripts/t10_reopen.py` → **0** (old and new).
Those numbers are `prove()`'s echo of `JC3_HUD_WEAPONS.md`'s own line, re-read on every run; the doc
line is evidence output, not a typed claim.

**Fix for the confirmed part.** `facts()` now derives every one of them: `LIGHTS.json`
(16 battle / 12 forensics), `FEATURE_CENSUS.json` (25 ids, 26 spellings, 21 armed chassis),
`WEAPONS.json` (11 BmAK gadget classes), `VOCABULARY.md` (52 types / 1,421 paths, parsed from the
generated tables) and `ENTITIES.md` (103 classes, parsed); `HUD_SCRIPTS` is deleted and the live
`.as` count is used in the doc and the checks. The document prints the derived values (16, 12, 4,
25, 26, 21, 11, 52, 1,421, 103, 260) and a change in any record now turns `--check` red.

### 7. R14 — the done section contradicts itself on a number — **CONFIRMED**

`MODLOG.md:12492-12493` pastes `ledger 122 rows | … out 9 superseded 4 | …`; the prose at `:12502` says
"`t_rows.py check` now reports `out 4 superseded 4`". `t_rows.py` counts over the whole ledger
(`counts[r["dispo"]]` at `t_rows.py:382`), so `out 9` is the tool's output for that run (T-10's 4
remaining `out` rows + 5 concurrent T-FX rows); the prose silently re-scoped it.

**Fix (append-only).** The journal is not rewritten. The `T-10 rework — done` section states which
reading is correct and what the sentence should be read as. No other line of the old section is
retracted.

### 8. Minor — self-citing evidence for T-CAM10, and the `.ctune`/`.ctunec` name — **CONFIRMED**

The only evidence was a needle in `Working/Translation/T6_HUD_CAMERA.md`, the file whose T-CAM10 cell
T-10 rewrote: `bat_base.ctune` occurs there at lines 135 (the rewritten cell), 140 and 143 - the check
cannot tell that row from independent proof. The delivered file is
`Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec` (**exists, 5,968 B**),
i.e. `ctunec`, one letter off the name the row used. Also `T-HUD5` showed successor `—` while its own
`why` named T-11 / B-05.

**Fix.** A new evidence kind `exists` points at the built `.ctunec` (file exists, non-empty, size
printed), the row says `.ctunec`, and `T-HUD5` lists `T-11, B-05`. Generated:

```
- `exists` the file exists — the delivered per-entity camera tune is a real file in the built tree (Batch F, test-091) - not a citation of this card's own row
  - ok: Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec: exists, 5,968 B
| T-HUD5 | T-6 | blocked | **blocked** | T-11, B-05 | D-7 | `Research/JC3Grab/JC3_HUD_WEAPONS.md` | HUD-2, WPN-12 |
```

---

## Files changed

| file | change |
|---|---|
| `Tools/scripts/t10_reopen.py` | shared-ledger census out of the compared payload/doc (printed live); Done clause scoped and stated; `PROOF_RE` → `PATH_RE` + `CARD_ID_RE`; `T-LG5` R5 rewrite; `T-FX4` R4 rewrite; HUD US-spelling searches with an allow-list; `facts()` derives the flagged numbers (`HUD_SCRIPTS` removed); `exists` evidence kind for T-CAM10; `T-HUD5` successors `T-11, B-05` |
| `Tools/scripts/t_rows.py` | the three `DISPO` `why` strings that must equal the table: `T-LG5`, `T-FX4`, `T-W1` (numbers moved out of the short form) |
| `Working/Translation/T10_OPEN_ROWS.md` | **regenerated** by `--write` |
| `Working/Translation/T10_OPEN_ROWS.json` | **regenerated** by `--write` |
| `Working/Translation/T_ROWS.jsonl` | **regenerated** by `t_rows.py build` (198 rows; 3 `why` texts) |
| `GRAB_BACKLOG.md` | §12 `T-10` line only - `diff` shows exactly one changed line (proof scope + T-11/B-05 + the rework section) |
| `MODLOG.md` | "T-10 rework · … — intended change" (before any edit) + "T-10 rework — done" (with the issue-7 correction) |
| `tmp/t10rework/` | pre-edit copies of every file above (revert path) |

`STATUS.md` was **not** regenerated: no disposition or count moved, and `status_audit.py --check` is
green. No `.ctunec`, build artifact, `Research/**` record or game file was written.

## Check output (verbatim)

```
> python Tools/scripts/t10_reopen.py --check
PASS: 16 rows (5 superseded, 10 out, 1 blocked) | 10/10 out rows this card owns carry a proof file | successors B-05, T-11, T-12, T-15, T-17, T-18 | decisions open none | json match True, md match True
later `out` rows: 26 of 32 cite a proof (an existing path or a real G/T/B card id), 6 do not (T-FX13, T-FX16, T-MD5, T-MD6, T-MD7, T-WLD15)
```

exit status 0.

```
> python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
```

exit status 0.

```
> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

exit status 0.

## Tamper test (6/6, each restored to PASS)

| tamper | result |
|---|---|
| `T10_OPEN_ROWS.json` summary `rows` 16 → 17 | exit 1, `FAIL T10_OPEN_ROWS.json stale: the payload differs` |
| ledger `T-AC1` `out` → `next` | exit 1, `FAIL T-AC1: ledger says 'next', the T-10 table says 'out'` and `FAIL T-AC1: the table keeps it 'out' but the files do not` |
| one evidence line in `T10_OPEN_ROWS.md` | exit 1, `FAIL T10_OPEN_ROWS.md stale: the text differs` |
| `T6_HUD_CAMERA.md` `T-HUD5` cell loses `JC3_HUD_WEAPONS.md` | exit 1, `FAIL T-HUD5: the T6 cell does not name 'JC3_HUD_WEAPONS.md'` |
| HUD probe `['armory']` (in memory) | `{'ok': False, 'detail': '... ui/hud.gfx names armory (9 of 9)'}`; with the allow-list, `armor` → `ok: True, explained: armor 9` |
| a synthetic later `out` row appended to the ledger (another card's row) | **PASS**, artifact unchanged; only the printed census moves (26 of 33, 7 unproven) - the issue-1 rot is gone |

## Residual notes

- The later-row census **is** the honest measure of the card's Done sentence's wider reading, and it
  is not met at HEAD (6 rows cite nothing). Those rows belong to T-13/T-15/T-17/T-20; fixing them is
  their cards' work, not a T-10 edit, and the document now says so instead of implying coverage.
- `T-SR1`'s "n=23 aircraft" and `T-AC1`'s "145 land vehicles" remain quoted from `VOCABULARY.md` in
  the ledger `why` prose (the review spot-checked both as correct); they are not count tables, and
  the evidence needles re-read the same file.
