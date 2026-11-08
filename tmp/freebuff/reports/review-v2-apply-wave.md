# Review — the v2 apply wave, and the 91xx briefs rewritten for it

**Verdict:** the ledger and its two standing pages are consistent and both `--check` runs are green, but the
brief in this wave named figures from the **RC4 era** (`145 of 216 evidenced, 1 assumed, 15 blocked, 109
queued`) that STATUS.md no longer prints, and one pin was red when this review opened (`t23_closeout.py`
could not place `Working/Prep/t22_shape_edits.json`). Thirteen briefs were rewritten: seven because the
operator facts of 2026-11-08 contradict their text, one because it cited a report that does not exist, three
because a row or value they build on moved in the v2 passes, one because it cited the lock/salvo as a battle
weapon, and one because the HUD writer question is now answered offline. Nothing was built, installed or
launched.

## 1. Pages regenerated, checks green

```
python Tools/scripts/status_audit.py --write
python Tools/scripts/status_audit.py --check
STATUS.md is current                                  (exit 0)

python Tools/scripts/t23_closeout.py --write
wrote Working/Translation/BUILD_BATCHES.md
wrote Working/Translation/build_batches.json
gate TX: 75 codes (58 carried, 3 named omission, 4 blocked, 10 documented, 0 unmapped) | 244 ledger rows |
         assumed 1 (0 unsigned) | decisions 11/11 answered | 20 artefacts (17 payloads + 3 records) over 24 B steps
gate TX ok: every §1 code maps to a row, assumed rows are signed off, D-1...D-11 answered   (exit 0)

python Tools/scripts/t_rows.py check
ledger 244 rows | edit 16 next 120 keep 30 epe 38 re-read 0 blocked 27 out 6 superseded 7 | edits 35 over 16 rows
check ok                                             (exit 0)
```

The artefact count moved **19 → 20** in this pass (see §6); that is the only number in `BUILD_BATCHES.md`
that differs from the RC4-era sheet.

## 2. STATUS.md against the brief's figures — every difference explained

| figure | brief (RC4 era) | STATUS.md now | delta | why |
|---|---:|---:|---:|---|
| evidenced in scope | 145 | **170** | **+25** | the three v2 apply passes moved rows from `keep`/`other` to evidenced: air control (`T-AC1`), ram assist (`T-RA1`), water entry (`T-WT1`), flip recovery (`T-FR1`), the remote/summon rows (`T-SR1`, `T-WP15`), the control-scheme cells (`T-CT1`…`T-CT5`), the P-01…P-15 part cells, the paint channels, the collision-impact rows and the m ode rows re-decided against the v2 plans |
| rows assumed | 1 | **1** | 0 | unchanged — still `T-E5`, the 336.4 km/h top speed, and it is signed off |
| rows blocked | 15 | **31** | **+16** | each v2 plan that named a behaviour without a carrier also wrote the row that records it: remote control beyond its boundary, the static remote overlay, the thruster flip after an idle wait, the water teleport destination, the mode-swap trigger (`U1` kept UNKNOWN), the missing collision shapes, the two lights rows. `t_blocked.py` pins each with its written reason |
| rows queued for the next build | 109 | **120** | **+11** | `next` is a subset of evidenced; the same passes both moved rows into `next` and added new ones |
| rows fully behaviour-verified | 0 | **0** | 0 | no drive has covered a row end to end; the test ban is unchanged |
| denominator | 216 | **260** | **+44** | 244 ledger rows + the 37 T6 HUD/camera rows = 281 counted, minus 13 `out` (6 ledger + 7 T6) and 8 `superseded` (7 + 1) = 260. The RC4-era 216 was 199 + 37 − 20, i.e. the ledger grew by **45 rows** and the exclusions by one |

The arithmetic is closed on both sides: `260 = 170 evidenced + 1 assumed + 31 blocked + 58 other` and the
blocked/out/superseded columns of the per-document table sum exactly to the header row (31 = 27 ledger + 4
T6; 13 = 6 + 7; 8 = 7 + 1), so the growth is row addition and re-disposition, not a rule change inside
`status_audit.py`.

**One difference this review cannot explain from the files, stated rather than smoothed:** the brief's "216"
cannot be recovered row by row, because the per-document table is generated from the current ledger and the
ledger carries no history. 199 is the ledger length recorded by the RC4 wave review (`review-build-wave.md`
§1, `t_boost_rows`/`t_vnf_six` pins), and 37 is the T6 table's row count today; the 20 excluded rows are the
current out/superseded counts. If the old exclusions differed, the +44 is off by that difference — the file
that would settle it is a ledger snapshot, and none is kept.

## 3. The briefs rewritten (13)

Applier, kept for reproducibility and idempotent (it refuses a file that already carries the marker):
`tmp/freebuff/review_v2_apply.py`. Every edited file keeps its `DONE:` and `AFTER:` headers and gains one
closing line, `Updated by review v2-apply (2026-11-08): …`.

| brief | what changed on the page |
|---|---|
| **9105** lock/salvo | F7: the barrage **auto-fires at full lock** (no separate fire press) and the count is **1/4/7/10 by upgrade level**, built at 10; the decoded `MaxTargets` 8 is kept beside it as a CONFLICT, not overwritten; F1: the lock/salvo is the **pursuit** fire slot, not a battle weapon; "the composed salvo of eight rounds" → ten, with 8 carried |
| **9110** cannon/Vulcan/riot | F1: cannon, Vulcan and riot pods are **battle-only** (pursuit fires the EMP missile alone) so every set written there is mode-gated; F8: **RT = cannon, RB = Vulcan**; F7 applied to the missile pods/barrage line |
| **9130** mode pair + swap | F1: the two variants must differ in **weapon sets**, not only handling; F2: **T-MD10 is mode-invariant**, armour is identical, not a battle scalar; F9: the transform is **~2 s with a near-instant speed loss**, so the swap carries health and ammunition, never velocity, and animation/HUD must cover the window |
| **9143** paint | F6: the target is **dark gunmetal satin, specular edges, carbon-weave insets, white chevrons**; the white-violet RC is rejected on **lightness and hue**; carbon/chevron carriers are named as a check (closest member or exact card), not dropped |
| **9170** controls/eject | F4: **three-level eject** — hold A charges the height, tap A ejects higher, double-tap A is the lowest — replacing the double-press-only reading; the keymap carries the binding only and the level logic is code (`NEW-MOD-2` in `Working/Roadmap/modes_controls_anim.md` answered, `NEW-MOD-5`'s window still open) |
| **9171** health/explosion | F3: **out-of-combat regen and full health on re-summon are required lore**, carried on `RB-9`, rate value UNKNOWN (`NEW-ARM-01`); F5: the explosion is instant at zero health, so **T-FX22/T-FX23 are dropped** and the donor's fire/smoke stages must not be added |
| **9194** pilot cards | must encode F1/F4/F6/F7/F8 into the cards and refresh `Working/Q/PILOT/CONTROLS.md`; runs after the six branches (§4) |
| **9120** handling | the boost grip 1.5 / extra 80 cells now cite the donor decode that set them (`boost-selector-and-moving-parts-plans-v2.md`) |
| **9123** air control | names the rows it serves, **T-AC1** and **T-RA1**, both moved to `next` by the v2 pass |
| **9124** flip/water/remote | names **T-WT1** and **T-FR1**; restates that the halted remote half is a **note**, not a disposition of `out` |
| **9172** moving parts | points the P-01…P-15 cells at the post-v2 ledger instead of the older plan tables |
| **9160** HUD | cites `reports/hud-gfx-ffdec-roundtrip.md` and the receipted payload `Builds/probe-L0/P3-hud-gfx/payload/ui/hud.gfx`: the **writer** half is answered (CFX header kept, 2,405 tags in order, the single `DoABC` byte-identical, 839/839 shapes SVG-identical), the **loader** half stays UNKNOWN |
| **9140** textures | drops a report that does not exist (see the AFTER list below) |

### AFTER lines added or removed

| brief | change |
|---|---|
| **9130** | **+2**: `rc5-cannon-vulcan-riot-pods.md`, `rc5-lock-hold-salvo-reticle.md` — the per-mode weapon sets it now has to compose come from those two branches |
| **9194** | **+6**: `rc5-lock-hold-salvo-reticle.md`, `rc5-cannon-vulcan-riot-pods.md`, `rc5-mode-pair-and-swap.md`, `rc5-paint-channels.md`, `rc5-controls-entry-exit-eject.md`, `rc5-health-explosion-no-crash.md` — the operator-facts bands it must put on cards |
| **9140** | **−1**: `reports/locate-missing-pixel-sets.md`, which does not exist. Its job is done by `Working/Appearance/PIXEL_LOCATE.md`, already cited in the same brief. No replacement report was invented |

No other brief's AFTER list changed. `9100` and `9120` already wait on this report, which is correct and was
left alone.

## 4. One paragraph per build wave — do the dependencies still hold?

**Weapon wave (9100–9119, 29 briefs).** The chain still runs in order: scaffold (9100, which also waits on
this review and on the four repair reports) → entity slots (9101) → effects (9102) → tracker (9103) → EMP
missile (9104) → lock/salvo (9105) → booster (9106) → EMP burst (9107) → hacker (9108) → sonar (9109) →
unranked weapons (9110) → review (9119, which waits on all ten). Two dependencies are now content-wrong
rather than broken: 9105 and 9110 assumed "every weapon in both modes", which the operator fact overturns, so
both were rewritten and 9105 stays ahead of 9110. 9104's "the lock hold and salvo belong to a later brief" is
still true and still points forward correctly. 9119 waits on ten reports and will see the rewritten texts.

**Driving wave (9120–9130).** 9120 (handling) waits on this review and on 9100's scaffold; 9121 waits on
9120; 9122, 9123 and 9124 wait on 9120; 9130 waits on 9122, 9121 and four reports. The chain holds, and 9130
now additionally requires the two weapon branches because the mode pair must gate weapon sets — a dependency
the RC4-era text did not have. 9123 and 9124 now name the ledger rows the v2 pass moved, so a reader can check
them instead of trusting the brief.

**Body and world wave (9140–9179).** 9140, 9141, 9142, 9143, 9150, 9160, 9170, 9171, 9172, 9173 and 9174
each wait on the scaffold (plus a specific branch where they share a carrier), and 9179 waits on all sixteen.
The chain holds. Three content dependencies moved: 9143 now carries the operator's colour target, 9160 now
starts from a proven writer and a shipped probe payload instead of an open question, and 9171 now carries regen
and the dropped burn stages. 9140 lost a dependency on a report that never existed.

**Merge and verify wave (9190–9199).** 9190 waits on all twelve branch/review reports, 9191 and 9192 wait on
9190, 9193 waits on both verifies, 9194 waits on 9193 **and now the six operator-fact branches**, 9199 waits on
9193 and 9194. The wave holds, and the new 9194 edges make the "cards encode the facts" rule enforceable rather
than advisory. Nothing in this wave waits on a report that does not exist, and no wave reaches a real game folder.

## 5. Does any brief tell an agent to launch a game or run an install script?

**No.** Every 91xx brief was read in full and grepped for `launch`, `install`, `attach`:

- `9190` says "the `.ee` and `.toc` rebuild, receipt schema 2 and `install.ps1`" as an artefact to produce, then
  closes with "**No install script is run. Nothing here launches a game.**" — a prohibition, not an instruction.
- `9192` runs **V-06 install dry runs against a simulated dropzone root** and says "never a real game folder;
  no `-WhatIf` against a game directory".
- `9191` copies gate scripts; `9102`/`9103`/`9104` mention a missile's **"launch flash"** and a **"launcher"**
  part, which are payload names, not actions.
- No brief names the game executable, a dropzone under a game install, or an attach step.

## 6. The pin this review did have to fix (disclosed, because it is a script edit)

`t23_closeout.py --check` was **red** when this review opened:

```
FAIL t22_shape_edits.json: produced by T-22 / B-10 (plan only - nothing applied)
     but not named in BATCH_PAYLOADS/BATCH_KIND
```

The file exists at `Working/Prep/t22_shape_edits.json`, and the batch gate only looked in
`Working/Translation/` and `Working/Appearance/`. Two changes, both minimal:

1. a `PATCH_DIRS(name)` helper that also resolves `Working/Prep/`, used by both the payload and the record loop
   (the record loop is where a plan-only file belongs);
2. `"t22_shape_edits.json": "record"` in `BATCH_KIND`, with a comment saying it is a plan until B-10 applies it.

Effect: artefact count 19 → 20 (17 payloads + **3** records), gate TX green, `--check` exit 0. Nothing was
loosened: the file still has to exist, and B-10's payload obligations are unchanged.

## 7. Checks run for this page

```
python tmp/freebuff/review_v2_apply.py          -> 13 brief(s) edited (exit 0)
python Tools/scripts/status_audit.py --write    -> rewritten
python Tools/scripts/status_audit.py --check    -> STATUS.md is current (exit 0)
python Tools/scripts/t23_closeout.py --write    -> BUILD_BATCHES.md + build_batches.json
python Tools/scripts/t23_closeout.py --check    -> gate TX ok (exit 0), 20 artefacts, 244 ledger rows
python Tools/scripts/t_rows.py check            -> check ok (exit 0), 244 rows
grep -n -i "launch|install" tmp/freebuff/queue/91*.txt   -> negations and payload names only (§5)
```

A scripted reference audit ran over all 36 briefs (every `reports/…`, `Tools/…`, `Builds/…`, `Working/…`
token resolved against disk, every `T-…` id against the 244-row ledger): **0 unknown row ids**, and the only
genuinely missing report reference was `reports/locate-missing-pixel-sets.md` in 9140, now removed.

## 8. UNKNOWNs

| # | UNKNOWN | what was tried | what settles it |
|---|---|---|---|
| 1 | the exact row-by-row basis of the brief's 216 | recomputed the denominator from the current ledger and the T6 table; no ledger snapshot exists | a ledger snapshot or the RC4-era `T_ROWS.jsonl` |
| 2 | whether 9160 can ship the HUD edit at all | the writer half is proven (`hud-gfx-ffdec-roundtrip.md`); the loader is not | the P3 probe session under the test ban |
| 3 | does the operator's "1/4/7/10" replace the decoded `MaxTargets` 8 | both kept, conflict flagged in 9105 | a BmAK level table read, or a pilot observation at level 1 |
| 4 | whether carbon-weave and chevron paint carriers exist in JC3 | not searched in this review | 9143's own slot search; `appearance.md` question 10 |
| 5 | the eject level window (`NEW-MOD-5`) | still open; the operator named the mechanism, not the timing | a live click measurement |

## 9. Revert

- Briefs: each edited file ends with the line starting `Updated by review v2-apply (2026-11-08):`; delete that
  line and reverse the replacements recorded in `tmp/freebuff/review_v2_apply.py` (the three AFTER edits are
  the only structural ones: 9130 +2, 9194 +6, 9140 −1).
- `Tools/scripts/t23_closeout.py`: remove the `PATCH_DIRS` helper, restore the two inline candidate tuples, and
  delete the `t22_shape_edits.json` line from `BATCH_KIND`.
- `tmp/freebuff/review_v2_apply.py` and this report: delete.
- Regenerated pages: rerun `status_audit.py --write` and `t23_closeout.py --write`.
- No ledger row, plan, build tree, module or brief ordering was changed by this review, and no game was started.
