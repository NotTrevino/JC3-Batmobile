# Independent review — T-10 · Re-open the `out` rows with the G2 evidence

Reviewer role: independent, read-only. The card's files were not edited; the only file written is
this report. Date 2026-10-29.

Sources read: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–79), §7 card T-10 (lines 851–861), §11
decision register, §12 row `| T-10 | done | …` (line 1319); `MODLOG.md` §"T-10 · Re-open the `out`
rows with the G2 evidence — done" (lines 12454–12563); outputs `Working/Translation/T10_OPEN_ROWS.md`
(229 lines), `Working/Translation/T10_OPEN_ROWS.json`, `Tools/scripts/t10_reopen.py`; evidence files
under `Research/JC3Grab/` and `E:/Modding/_JC3grab/hud/dec`.

## VERDICT: minor issues

The substance of the card is sound. All 16 rows exist in the two files the dispositions live in; the
10 rows that stay `out` each carry an evidence triple that `--check` re-reads from an existing file;
`t_rows.py check` and `status_audit.py --check` are both green; the five successor cards are real §7
cards; the ledger really did go 105 → 122 rows (`tmp/freebuff/pre_t10/T_ROWS.jsonl` = 105, and the
`T-13` document contributes exactly 17 of the 17 added rows).

It is not "sound" because:
1. the card's own `t10_reopen.py --check` fails at HEAD (exit 1, two stale-artifact FAILs);
2. the card's Done clause "no `out` row lacks a proof file" is not what any check verifies — for
   rows T-10 does not own the check is a substring match, and 6 such rows are unproven today;
3. one evidence note states an R5 error (a BmAK light-type enum described as "a decoded behaviour
   value") and one overstates what a cited class provides (`CEMPWeapon`).

No disposition is wrong, so this is not "needs rework".

## Check output (verbatim)

The card's `--check` command, as named in the §12 row, run from the project root:

```
$ python Tools/scripts/t10_reopen.py --check
FAIL T10_OPEN_ROWS.json stale: the payload differs
FAIL T10_OPEN_ROWS.md stale: the text differs
2 problem(s)
exit 1
```

The two checks the card's `Done:` line names:

```
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
exit 0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
exit 0
```

(The ledger is 198 rows now, not the 122 of the T-10 section; other cards have written since. The
T-10 counts are historical in that sense, except for the `--check` failure, which is live.)

## Out paths and Done criterion

| card requirement | state |
|---|---|
| `Out:` updated rows | `T_ROWS.jsonl` and `T6_HUD_CAMERA.md` both carry the new dispositions and `t10_reopen.py --check` re-compares them row by row; agrees |
| `Out:` MODLOG section with a table old row → new disposition → evidence file | present, `MODLOG.md:12460-12484`, 16 rows |
| §12 row's `T10_OPEN_ROWS.md` | exists, 229 lines (matches the "229 lines" claim) |
| §12 row's `T10_OPEN_ROWS.json` | exists, `problems: []` |
| §12 row's `Tools/scripts/t10_reopen.py --check` | exists, but **exit 1** (see issue 1) |

| card `Done:` clause | verified by | result |
|---|---|---|
| `t_rows.py check` green | `t_rows.py check` | green |
| `status_audit.py --check` green | `status_audit.py --check` | green |
| no `out` row lacks a proof file | `t10_reopen.py`: re-reads the evidence for the 10 rows it owns; for other cards' `out` rows only regex-matches the reason text | **only the 10 own rows are proven**; 6 foreign `out` rows carry no proof (issue 2) |

## Issues

**1. The card's `--check` is red at HEAD (`Tools/scripts/t10_reopen.py:638,672,790`; `T10_OPEN_ROWS.md:21`).**
A field-by-field diff of the on-disk JSON against `derive()` shows exactly one differing value:
`summary.foreign_out_rows` is **25** in the artifact and **26** re-derived. The markdown diff is a
single line (21) for the same reason. Everything T-10 itself decided still verifies. The cause is
structural: the artifact bakes a census of the *shared* `T_ROWS.jsonl` — `out` rows written by other
cards after T-10 — into text that `--check` then compares byte-for-byte, so every later card that adds
an `out` row invalidates T-10's deliverable without touching anything T-10 owns. T-11 and T-18 handled
this by re-running `--write` and journaling it (`MODLOG.md:13157`, `:13219`: "24 later `out` rows cite
a proof, 2 do not … decisions open none"); no session has run it since. Two remedies, either is
enough: re-run `--write` and journal the new output, and/or keep the foreign-row census out of the
compared payload (report it, do not store it).
Related, same cause: the on-disk doc now says "§11 decisions still open on those successors | none"
(`T10_OPEN_ROWS.md:18`, gates without "(open)"), whereas the done section's recorded PASS says
"decisions open D-2, D-3, D-7" (`MODLOG.md:12497`) — the artifact was regenerated after D-2/D-3/D-7
were resolved, and that regeneration is journaled in T-11's section, not T-10's. The file is therefore
not the file the done section describes.

**2. The Done clause "no `out` row lacks a proof file" is wider than the check (`GRAB_BACKLOG.md:861`;
`t10_reopen.py:396`).** `t_rows.py check` never looks at proof files. `t10_reopen.py` re-reads evidence
only for the 10 rows it owns; for `out` rows other cards wrote it accepts the row if `PROOF_RE`
matches the reason text, and `PROOF_RE = r"\.md|G1-|G2-|_JC3grab|0 of \d+|0 systems|proven absent"`
accepts non-evidence: in-memory, `PROOF_RE.search("no notes .md")` → `'.md'` and
`PROOF_RE.search("see G2-99")` → `'G2-'`, i.e. a dangling card id counts as a cited proof. At HEAD
6 foreign `out` rows fail even that test (T-FX13, T-MD13, T-MD5, T-MD6, T-MD7, T-WLD15), so the
card's literal Done sentence is false today. T-10 records them as "its own card's to prove"
(`T10_OPEN_ROWS.md:21`, MODLOG "UNKNOWNs and limits"), which is a defensible scope call — but it is a
reduction of the card text, and the reduction should be stated as such rather than presented as the
clause being verified.

**3. R5 — a BmAK light-type enum is presented as a decoded JC3 behaviour (`T10_OPEN_ROWS.md:129,131`;
`t10_reopen.py` T-LG5 `why`/evidence note).** The doc says "the battle-mode spotlight (16 entries) is
a decoded behaviour value (`VEHLT_BattleModeLight`, G2-33)" and "the battle spotlight is a real
behaviour value on the same light part". `VEHLT_*` is the **donor** enum: `Research/JC3Grab/LIGHT_SYSTEM.md:227-228`
reads "The same socket also carries 1 `VEHLT_BattleModeLight` entry (`VEHLT_BattleModeLight` ->
HeadLight)", and the same file's §7a table gives the JC3 `behavior` as `HeadLight`, sourced from
`Research/BatmobileGrab/LIGHTS.json … (VEHLT_HeadLight -> HeadLight, G1-17 mapping)`. T-10's own
successor work confirms there is no JC3 battle-light behaviour: `T11_MODES.md:53` — "the fleet's light
vocabulary is 9 behaviours … with 0 battle value, so T-18 maps the battle lamps onto `HeadLight`" and
"carried as headlights: the battle lamps come on with the lights, not on a mode"; `T14_LIGHTS.md:64-67`
builds T-L17…T-L20 as `VEHLT_BattleModeLight → HeadLight`. So the *carrier* is real (the light entry and
its socket) and the supersede → T-18 stands; what is not supported is calling the value a behaviour.
This is the R5 pattern: the name that sounds like the behaviour used as the behaviour. The parenthetical
"(16 entries)" makes it worse — 16 is the BmAK rig count (from the ledger's own T-LG5 cells, "16 + 12
entries"), while the JC3 side produced 4 rows (T-L17…T-L20); the doc merges donor count and JC3 value
into one claim.

**4. R4 — the T-FX4 carrier is overstated (`T10_OPEN_ROWS.md:69-74`; evidence note at :73 "the EMP
device's own weapon classes and the entity-level pulse (G2-16)", whose quoted line at :74 is EMP.md's
"holds the engine's EMP weapon class (`CEMPWeapon`)").** `Research/JC3Grab/EMP.md` opens with "**yes
for the effect, no as a weapon-slot copy**", states "no vehicle weapon slot in the game currently holds
the engine's EMP weapon class (`CEMPWeapon`)", and "nothing in the files says whether the pulse actually
fires when the action runs (that is code)". The `needle CEMPWeapon` only proves the class is *named*
in that doc. T-11 then had to write exactly that caveat per row (`T7_WEAPONS.md:79-80`: "no weapon slot
for the pulse … the trigger stays UNKNOWN"). The supersede is still right (the effect has a carrier);
the sentence should say "the effect, not the weapon".

**5. The HUD searches are spelling-brittle (`T10_OPEN_ROWS.md:140-141` and the `hud` notes).** The
must-not word for armour is British `armour`; the data is American. Independently, over
`E:/Modding/_JC3grab/hud/dec` (260 `.as`, count confirmed): `armour` → 0 files, `armor` → **7 files**
(all `CHAOS_REWARD_ARMORY` / `gotoAndStop("ARMORY")` in `hud.as` and the settlement-list scripts). The
conclusion therefore survives — those hits are a chaos-reward icon, not vehicle armour — but the check
as written could not have caught a field named `armor`. Same class of gap for `enemy_count`
(`enemyCount` would not match; `enemy` itself has 0 hits, so the conclusion holds) and `energysystem`
(`energy` has 1 hit, a joke string, so again the conclusion holds). Cheap fix: search the US spelling
too and filter the known ARMORY hit, as `prove()` already prints the offending hits.

**6. R11 — not every number in the doc is derived.** The summary table (16 / 5 / 10 / 1 / 14 / 10-10 /
25-6 / 0) is derived and byte-compared, which is what R11 asks for a count table. The prose numbers are
literals inside the script's `ROWS` strings and are printed verbatim: "16 entries"/"12 entries"
(T-LG5), "25 vehicle weapon ids" and "11 weapon classes" (T-W1), "9 arguments"/"6" (T-HUD4 note),
"52-type / 1,421-path" and "103-class" (§4 template), and `HUD_SCRIPTS = 260`
(`t10_reopen.py:54`, a typed minimum that would not follow the directory if it grew). Most of them are
echoed in the evidence line quoted immediately below (145, 23, 179, 9/6, 25 all check out — see
Spot-checks), but 52 / 1,421 / 103 / 16 / 12 are not recomputed anywhere. Minor, and squarely inside
the "quoted from a named source file" pattern the project uses elsewhere.

**7. R14 — the done section contradicts itself on a number (`MODLOG.md:12492-12493` vs `:12502`).** The
pasted output says `ledger 122 rows | … out 9 superseded 4 | …`; the prose immediately below says
"`t_rows.py check` now reports `out 4 superseded 4` for the ledger". `t_rows.py check` prints
ledger-wide counters (`Tools/scripts/t_rows.py:383-384`), so `out 9` is the right value for that run
(T-10's 4 remaining
`out` ledger rows + the 5 concurrent T-FX rows). The prose silently re-scopes the number to T-10's own
rows without saying so, and understates the printed output by 5.

**8. Minor: self-citing evidence for T-CAM10 (`T10_OPEN_ROWS.md:190-192`).** The only evidence path is
`Working/Translation/T6_HUD_CAMERA.md`, i.e. the file whose T-CAM10 cell T-10 itself rewrote; the needle
`bat_base.ctune` occurs at lines 135 (the rewritten cell), 140 and 143 of that file, so the check cannot
distinguish "the row I just wrote" from independent proof. The fact is true — the per-entity tune really
was built — but the stronger evidence is `Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec`
(and MODLOG §Batch F). Note also that the built file is `bat_base.ctunec`, not the `bat_base.ctune` the
doc names (the internal tune name is `bat_base.ctune`; the shipped file carries the `c`). One letter,
worth being consistent about.
Also minor, same table: T-HUD5 stays `blocked` with successor "—" while its own `why` names the
unblocker (T-11 / B-05); the column would read better as `T-11, B-05`.

**Tamper-test claims.** Not re-run by editing files (read-only). The "proven-absence half can fail" claim
was reproduced in memory without touching the file: `t.prove(t.norm(("hud","","",["cooldown"],"sim")), hud)`
returns `{'ok': False, 'detail': '… ui/hud.gfx names cooldown'}`, so the `hud` check does catch a word the
movie really contains. The ledger/table disagrees are also structural in `derive()` (any `actual != now`
is a problem), so the claimed tamper tests 1 and 3 are credible; test 3 is what is failing now, for a
count rather than a disposition.

## Spot-checks (value → where verified)

| value in `T10_OPEN_ROWS.md` | verified at |
|---|---|
| T-AC1 "145 land vehicles; donor 1/1/1 and 0.5" | `Research/JC3Grab/VOCABULARY.md:491-493` `gravity_multiplier_grounded` / `…_in_air_down` / `…_in_air_up`, all `n=145`, donor column `1`; `:498` `takeoff_pitch_damping` `0.2 .. 0.8 (med 0.5, n=145)`, donor `0.5` — matches |
| T-SR1 "`righting_torque` … only in `DriverLean`, n=23, donor none" | `VOCABULARY.md:566` `1500 .. 4000 (med 3000, n=23)` with an empty donor cell, inside the `## \`DriverLean\`` block that starts at `:550` and ends before `:571` (`## \`EffectAttachments\``) — matches; "aircraft" comes from `G2X.md:105`, not re-derived here |
| T-BM1 "`179`" / "-179 .. +179 deg" | `Research/JC3Grab/TURRET.md:10` "constraint 2, pivot (0, 2.2812, 1.1382), axis +Y, **-179 .. +179 deg**", and the per-entity rows `:33,:70,:109,:146,:187,:223` — matches |
| T-W1 "25 vehicle weapon ids" | `Research/JC3Grab/WEAPONS.md:17` "22 of the 25 ids have their own directory"; no line says 25 elsewhere, so the 25 is that count — matches |
| "103-class fleet census" and "no sonar class" | `Research/JC3Grab/ENTITIES.md` class inventory: 103 table rows counted programmatically, and 0 rows containing `sonar` — matches |
| "260 scripts read, 0 hits of `armour`" | `E:/Modding/_JC3grab/hud/dec`: 260 `.as` files found, `armour` 0 files — matches; but `armor` 7 files (all `CHAOS_REWARD_ARMORY`), see issue 5 |
| "9 arguments / 6 arguments, 2 slots" | `Research/JC3Grab/JC3_HUD_WEAPONS.md:5`, `:14`, `:34`, `:53` — matches |

## Limits of this review

- Read-only: no card file, script, ledger, `Research/` file or game file was modified, and no game was
  launched. Nothing was committed.
- The tamper tests were not re-run by mutating files (that would need write access to `Tools/`); one was
  reproduced in memory, as noted.
- The ledger has moved from 122 to 198 rows since T-10 was marked done, so the absolute counts in the
  T-10 done section and in issue 7 are as-of-then; the live failure in issue 1 is as-of-now.
- "Aircraft" in T-SR1, and the 52-type / 1,421-path census, were taken from the G2/G2X reports and the
  JC3Grab README (`README.md:122`) rather than re-derived from the decoded entities.
