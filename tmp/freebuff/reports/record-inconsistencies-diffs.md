# Record inconsistencies — `ROADMAP.md` §8 verified, corrections as unified diffs (not applied)

Card: `record-inconsistencies-diffs`. 2026-11-08. Report only. **No source file was modified.**

Scope: the four bullets of `ROADMAP.md` §8 ("Record inconsistencies to fix (found by the audits)"), expanded
to the twelve individual claims they contain (several bullets assert two to five things each). Each claim is
checked against the file `ROADMAP.md` names and against `Working/Roadmap/*.md`; where the claim is about a
`STATUS.md` line, the check goes to the generator (`Tools/scripts/status_audit.py`) and to the input that
generator reads, because `STATUS.md` is generated and never hand-edited (`STATUS.md`, line 1).

Rules followed: `tmp/freebuff/INSTRUCTIONS.md` (report only, no applying), `STAGES.md` line 4 (a row is never
omitted) and `AGENTS.md` (every JC3 claim cites a local file; UNKNOWN where nothing does).

How to read the diffs: they are `diff -u` output against the current working tree, printed with the CR
stripped for legibility. `GRAB_BACKLOG.md` is mixed LF/CRLF and the other two files are CRLF, so applying
them needs `git apply --ignore-whitespace` (or `patch -l`). The exact byte-preserving results of every patch
below already exist as generated copies in `tmp/freebuff/scratch/diffwork/*.fixed` — those are scratch
copies, not applied edits.

---

## 1. Verdicts

| # | `ROADMAP.md` §8 claim | evidence checked | verdict | where the fix belongs |
|---|---|---|---|---|
| 1 | `STATUS.md` lists event `0x6BB2C66E` UNKNOWN "but is resolved" | `STATUS.md` §`G2 — JC3`, bullet 3; source string `Tools/scripts/status_audit.py:301`; `Working/Roadmap/sound.md:20` ("STATUS.md:99 still says UNKNOWN (stale)"); `Research/BatmobileGrab/AUDIO_EVENT_6BB2C66E.md` | **partly supported** — STATUS does say UNKNOWN, and the twin is found; but "is resolved" overstates: the declared id is still carried by **no** bank | `Tools/scripts/status_audit.py:301` (generator) |
| 2 | the winch is listed `out` but the ledger says `blocked` | `status_audit.py:307` (hard-coded example list); `T_ROWS.jsonl`: `T-CT3` `blocked`, `T-W1` `superseded`, no winch row is `out` | **supported** | `Tools/scripts/status_audit.py:307` (generator) |
| 3 | live build is test-090 in `STATUS.md`, test-091 in the backlog | `status_audit.py:50-67` (`b2()`); input `Working/Translation/t5e_applied.json` → `applied[0].file` = `Builds/test-090/...suspension.vmodc`; `GRAB_BACKLOG.md:95,129,185,249,354,362,1293,1298` say test-091 | **supported**, but the fix is **not** in `STATUS.md` or in the script's prose — it is in the input record | `Working/Translation/t5e_applied.json` (input) — or the applier that writes its `file` field |
| 4 | ledger size "quoted as 198/199/216/221 in different places" | repo-wide grep for `198/199`, `198 / 199`, `216/221`, `216 / 221`: **only `ROADMAP.md:167` itself**; live ledger `T_ROWS.jsonl` = **244** rows; `+` T6's **37** = 281; in scope **260**, which is what `STATUS.md` and `status_audit.py:142-147` both print | **NOT SUPPORTED** — no record quotes those numbers; the sizes agree | `ROADMAP.md` §8 text (this bullet is wrong about the records) |
| 5 | the "T-14: 28 rows" are lamp rows, not damage rows | `Working/Translation/T14_LIGHTS.md:5` ("One row per entry of the Batmobile rig, `T-L8`…`T-L35`"); `T_ROWS.jsonl` doc `T-14` = 28 rows, ids `T-L8`…; the *card* T-14 in the pre-decision backlog was "Damage and armour translation" (`Backups/GRAB_BACKLOG.pre-decisions-20261028.md:902`) | **supported** — the ledger doc tag `T-14` is the lamps card (whose real number is T-18), while the card number T-14 was damage | `Tools/scripts/status_audit.py` (doc-table label) |
| 6 | `GRAB_BACKLOG.md` §0.7 prose says 81,952/81,953 | backlog `:106`, and again at `:351`; `STATUS.md` §`G2 JC3` = **81,953 / 81,953**, 100.000%, source `INDEX.json` | **supported** (two occurrences, not one) | `GRAB_BACKLOG.md:106,351` |
| 7 | D-6 "standalone" was disproven **in game** | `tmp/freebuff/reports/standalone-spawn-census-check.md` rows 1–2 (file-level census: the build carries the vanilla `_debug` leaf, and its inner `.epe` is still the civilian `_01` graph); **no in-game take exists** for it | **partly supported** — the substance is right, "in game" is not: the evidence is file-level only, and in-game testing is currently barred | `GRAB_BACKLOG.md:1800` (wording) |
| 8 | D-8 was overturned | `ROADMAP.md` §7 is the **only** record of the operator ruling; the carrier plan exists (`tmp/freebuff/reports/water-entry-teleport-closest-system-plan.md`, 23 KB, 2026-11-08); the ledger still carries the lore route (`T-WLD13`/`T-WLD14`, `why`: "D-8's lore route ships as it stands") | **supported**, weakly sourced (self-reference) | `GRAB_BACKLOG.md:1802` + a ledger re-pin of `T-WLD13`/`T-WLD14` |
| 9 | B-12 card calls turn-on-the-spot a "named omission" | `GRAB_BACKLOG.md:1419-1421` ("T-MD8 and T-MD14 stay **named omissions**"); `STAGES.md:4` ("A row is never omitted…") | **supported** | `GRAB_BACKLOG.md:1419-1421` |
| 10 | B-15/B-17/B-24/B-25 numbers collide with `Research/specs/` | `ls Research/specs/` → `B-15.md` (riot mode), `B-16.md` (winch anchor), `B-22.md`, `B-23.md`, `B-24.md` (held lock + 8-target salvo), `B-25.md` (lock reticle link). **No `B-17.md`.** Backlog §12 rows `B-15` (budget) and `B-16` (weapon-clone cleanup) collide; cards `B-24` (handling) and `B-25` (flares) collide; and both flares citations point at the **reticle** spec (`GRAB_BACKLOG.md:1592`, `:1967`) | **partly supported** — B-17 does not collide; B-16 does and is missing from the list; two citations are simply wrong | `GRAB_BACKLOG.md` (renumber + citations); `NEXT_TASKS.md:18` already owns it as `NEW-WPN-46` |
| 11 | `T10_DAMAGE.md` says T-DM7 is `out`; the ledger says `next` | `Working/Translation/T10_DAMAGE.md:143` and `:162`; `T_ROWS.jsonl` `T-DM7` → `dispo: next` | **supported** | `Working/Translation/T10_DAMAGE.md:143,162` |
| 12 | Q briefs 8600–8605 name RC4 and `install_v3.ps1` | grep: **only `8601`** names either (`8601:6`); `8600`, `8602`–`8605` name neither; `8606` (outside the range) names both | **NOT SUPPORTED** | `ROADMAP.md` §8 text |

Count: **8 supported** (one of them with the fix in an input rather than a document), **3 partly supported**,
**2 not supported** (#4, #12 — the claim about the records is itself the error).

---

## 2. Diffs — `GRAB_BACKLOG.md`

Five hunks: the two 81,952 occurrences (#6), the B-12 omission wording (#9), the two flares citations and the
renumbering (#10), and the D-6/D-8 decision rows (#7, #8).

```diff
--- a/GRAB_BACKLOG.md
+++ b/GRAB_BACKLOG.md
@@ -105,3 +105,3 @@
 python Tools/scripts/bmak_coverage.py --check        # every BmAK field has a row
-python Tools/scripts/jc3index.py check               # 81,952 / 81,953 named
+python Tools/scripts/jc3index.py check               # 81,953 / 81,953 named
 python Tools/scripts/jc3hkx.py check --all           # Havok shapes invariants
@@ -350,3 +350,3 @@
 **What already happened and is not repeated:** G1 18/18 units (423/423 fields, 19,203/20,128
-objects); G2 11/11 units (81,952/81,953 entries, 6,045/6,045 modules, 77,611/77,611 geometry
+objects); G2 11/11 units (81,953/81,953 entries, 6,045/6,045 modules, 77,611/77,611 geometry
 blocks, 57,187 FX files, 18,865 hulls); translation batches A (test-085), B2 (088), B3 (089),
@@ -1418,5 +1418,6 @@
 Done: `aafdiff` between variants lists only the files the variant table names; each variant holds
-its own values for T-MD5/T-MD6/T-MD7/T-MD13, and T-MD8 and T-MD14 stay **named omissions** — the
-pivot has no carrier even with two variants (G2-21) and the `BattleMode` usage has no consumer
-(U1).
+its own values for T-MD5/T-MD6/T-MD7/T-MD13, and T-MD8 and T-MD14 stay **blocked with their gap named**, not omitted (`STAGES.md` line 4) —
+T-MD8's gap is G2-21 (`TANKTURN.md`: no member set produces a pivot, so a turn-on-the-spot needs a
+native capability card, not an omission) and T-MD14's is U1 (a `BattleMode` `Usage` hash with no
+consumer). Each gets a capability card.
 
@@ -1564,3 +1565,3 @@
 
-#### B-24 · Handling values: the three keep-audits' replacements   M · deps: T-1 · serves: T-ST2, T-ST3, T-ST4, T-ST6, T-K3, T-K4, T-DR1, T-E2, T-E5, T-B1, T-B4, T-A3, T-G4
+#### B-27 · Handling values: the three keep-audits' replacements   M · deps: T-1 · serves: T-ST2, T-ST3, T-ST4, T-ST6, T-K3, T-K4, T-DR1, T-E2, T-E5, T-B1, T-B4, T-A3, T-G4
 In: `tmp/freebuff/reports/keep-audit-dimensions-wheels.md`, `keep-audit-steering-and-drift.md`,
@@ -1586,3 +1587,3 @@
 
-#### B-25 · Lens flares and the light units (17 flare entries, 4 cone/intensity members)   S · deps: B-03, B-07 · serves: T-LG6
+#### B-28 · Lens flares and the light units (17 flare entries, 4 cone/intensity members)   S · deps: B-03, B-07 · serves: T-LG6
 **No payload in RC4** — the flare sprite cannot be attached (no effect member on a lamp), and the
@@ -1591,3 +1592,3 @@
 In: `tmp/freebuff/reports/keep-audit-lights.md` §3/§6, `Research/BatmobileGrab/LIGHTS.json`,
-`Research/JC3Grab/LIGHT_SYSTEM.md` §3/§8, card `Research/specs/B-25.md`.
+`Research/JC3Grab/LIGHT_SYSTEM.md` §3/§8, `tmp/freebuff/reports/keep-audit-audio-fx.md` §4.
 Do: 1. Carry the 17 LensFlareChart entries as part-side emitters, not `lights[]` rows: 10 are
@@ -1799,5 +1800,5 @@
 | D-5 | Skins (MK2, Jokerfied) as extra drop entries, palette tints, or not at all | G1-20 | **resolved 2026-10-28 (user): skins as extra Rebel Drop entries** (MK2, Jokerfied, …) | APP-8 |
-| D-6 | Standalone entity, or keep replacing the Serpente (which may put NPC Batmobiles in traffic) | G2-27, G2-29 | **resolved 2026-10-28 (user): standalone entity** (no Serpente replacement) | WLD-1/8, B-13 |
+| D-6 | Standalone entity, or keep replacing the Serpente (which may put NPC Batmobiles in traffic) | G2-27, G2-29 | **resolved 2026-10-28 (user): no Serpente replacement.** What the build carries is the unused vanilla leaf `v0300_car_kensington_sportsmuscle_debug` (B-13b; `tmp/freebuff/reports/standalone-spawn-census-check.md` row 1), which is in no traffic table (G2-29) — so the traffic risk D-6 names is absent; but the car is **not** a standalone entity, since its inner `.epe` keeps the civilian `_01` graph (same report, row 2). The wording is corrected; the decision stands | WLD-1/8, B-13 |
 | D-7 | Weapon slots: which BmAK weapons take JC3's driver slots (cannon, Vulcan, missiles…) | G2-11 | **resolved 2026-10-28 (user): every BmAK weapon in both battle and pursuit modes** — no per-mode split; the slot count must carry all weapons (T-11 finds how, e.g. extra driver slots or mode-independent switching) | T-11 |
-| D-8 | Water: BmAK's Batmobile is not amphibious. Sink and stall (lore), or JC3 default? | G2-31 | **resolved 2026-10-28 (user): lore** — sink and stall, Rico swims out | WLD-6 |
+| D-8 | Water: BmAK's Batmobile is not amphibious. Sink and stall (lore), or JC3 default? | G2-31 | **overturned 2026-11-08 (operator)**: water teleports to land (`ROADMAP.md` §7; carrier `tmp/freebuff/reports/water-entry-teleport-closest-system-plan.md`). The 2026-10-28 sink-and-stall answer is withdrawn; T-WLD13/T-WLD14 ("D-8's lore route ships as it stands") are stale and need a re-pin | WLD-6 |
 | D-9 | Can enemies pull Rico out of the Batmobile? | G2-18 | **resolved 2026-10-28 (user): no** — enemies cannot pull Rico out | T-13 |
@@ -1960,4 +1961,4 @@
 | B-14 | done | `Builds/bm-RC1/` (`drop/` 8 files + `receipt.json` schema 2 + `install.ps1` Status/WhatIf/Install/Verify/Rollback091) + `python Tools/scripts/bm_rc.py --check` (`PASS: bm-RC1 0 failure(s)`: -WhatIf == receipt, 2 offline rehearsals) + `Working/RC/bm_rc_manifest.json` + MODLOG §"B-14 done" (3-way .epe merge of B-06/07/08; B-10 integrated; found: 4 wheel lod4/5 unpacked -> V-02) |
-| B-15 | done | new card (found by V-01): `Tools/scripts/bm_budget.py` applied in `bm_rc.py` step 3b; non-vanilla model 5,972.9 -> 4,791.3 KB of 4,915 (R9; method calibrated on test-065/081/085/091, which rendered); 16 far-LOD .lod trims; Serpente panels not unbound (vanilla-identical, not counted; V-02 checks if they draw) + MODLOG §"B-15" |
-| B-16 | done | new card (found by V-03): weapon-clone cleanup in `bm_rc.py` (4 `F30CCB1C` owner links -> null, 12 APC mounted-M2 body members removed; medium-tank + preorder convention) + RC merge per-branch base fix (bm-007/008 on the pre-rework bm-005) + MODLOG §"RC merge fix" |
+| B-29 | done | new card (found by V-01): `Tools/scripts/bm_budget.py` applied in `bm_rc.py` step 3b; non-vanilla model 5,972.9 -> 4,791.3 KB of 4,915 (R9; method calibrated on test-065/081/085/091, which rendered); 16 far-LOD .lod trims; Serpente panels not unbound (vanilla-identical, not counted; V-02 checks if they draw) + MODLOG §"B-15" |
+| B-30 | done | new card (found by V-03): weapon-clone cleanup in `bm_rc.py` (4 `F30CCB1C` owner links -> null, 12 APC mounted-M2 body members removed; medium-tank + preorder convention) + RC merge per-branch base fix (bm-007/008 on the pre-rework bm-005) + MODLOG §"RC merge fix" |
 | B-17 | todo | **no payload in RC4** (declared no-payload in `BUILD_BATCHES` §4); card in §8; writer proof `tmp/freebuff/reports/effc-format-writable.md` + `python Tools/scripts/effc_writer.py check` (95/95 carry byte-identical, 91.49% bytes from fields, one edited copy re-read); the five plans it executes are `Working/Translation/T13_FX.md` §5 |
@@ -1966,3 +1967,3 @@
 | B-20 | todo | **no payload in RC4** (declared no-payload in `BUILD_BATCHES` §4); card in §8; `tmp/freebuff/reports/sonar-and-scan-pulse.md` §4 (pulse + ring + `BML_Sonar`); audio ids `Research/BatmobileGrab/AUDIO_BANKS2.md:154-169` |
-| B-25 | todo | **no payload in RC4**: the flare sprite cannot be attached (no effect member on a lamp); card in §8, 17 flare entries + 4 cone/intensity members, per `Research/specs/B-25.md` |
+| B-28 | todo | **no payload in RC4**: the flare sprite cannot be attached (no effect member on a lamp); card in §8, 17 flare entries + 4 cone/intensity members, per `Research/JC3Grab/LIGHT_SYSTEM.md` §3/§8 |
 | B-26 | todo | **no payload in RC4**: the 21 pinned audio GUIDs stay donor; card in §8, private bank + per-entity binding rows, per `Research/specs/B-26.md` |
```

Renumbering rule used: the **spec** series is authoritative (`B-15` riot, `B-16` winch anchor, `B-22` droop,
`B-23` springs, `B-24` held lock + salvo, `B-25` reticle link — all already cited by reports and receipts),
so the backlog-only cards move to free numbers: handling `B-24`→`B-27`, flares `B-25`→`B-28`, tracker
`B-15`→`B-29`, tracker `B-16`→`B-30`. `B-26` (audio) is untouched because no `Research/specs/B-26.md`
exists: the backlog's own citation at `:1968` reads "per `Research/specs/B-26.md`", a file that is not on
disk, and that dangling citation is left for the renumber brief to settle rather than invented here.

Not covered by these hunks, and not diffable as text (they are renumbering fallout across 20 files that
name `B-24`/`B-25`): `MODLOG.md:21206,21246,21251,21252,21339`, `NEXT_TASKS.md:18-22`, the `Builds/bm-RC4*`
receipts, `Working/Roadmap/appearance.md` and `handling.md`, and the Q-brief filenames. `NEXT_TASKS.md:18`
already carries this as `NEW-WPN-46`, so the item is a duplicate of a planned fix, not a new one.

---

## 3. Diff — `Working/Translation/T10_DAMAGE.md` (#11)

```diff
--- a/Working/Translation/T10_DAMAGE.md
+++ b/Working/Translation/T10_DAMAGE.md
@@ -142,3 +142,3 @@
 | T-DM6 | `deform_scale` | **keep** | 0 | 0 | 1..2 (declared switch) | keep |
-| T-DM7 | `outgoing ram damage` | **out** | - | - | - | out |
+| T-DM7 | `outgoing ram damage` | **next** | `rotor_collision.damage_to_other_per_second` 100000/s, `light_object_mass_ratio` 0.02, `mass_ratio_when_no_mass` 0.1, `min_rpm` 30 (n=232, donor included) | the outgoing channel is data; the 20->150 speed band has no JC3 member, and whether a `CCar` evaluates the block is UNKNOWN | `tmp/freebuff/reports/carrier-ram-and-dodge.md` §2/§9 | next |
 | T-DM8 | `impact_damage_factor` | **keep** | 0 | 0 | 1..12 (declared switch) | keep |
@@ -161,3 +161,3 @@
 - **T-DM6** — cosmetic off switch (no panel crumple), already declared in damage_switches.json
-- **T-DM7** — unchanged: G2-28 found no outgoing ram-damage member; the only impact member is incoming (impact_damage_factor)
+- **T-DM7** — **moved off `out` 2026-11-06**: G2-28's `impact_damage_factor` is incoming, but every vehicle carries an *outgoing* contact channel — `rotor_collision.damage_to_other_per_second` 100000/s with `light_object_mass_ratio` 0.02, `mass_ratio_when_no_mass` 0.1 and `min_rpm` 30 (n=232, donor included). The ledger row is `next`; the probe is `tmp/freebuff/reports/collision-impact-and-mode-switch-plans-v2.md` §4 steps 1 and 4
 - **T-DM8** — incoming collision damage off (BmAK: ramming does not scratch it); declared switch
```

The table's last column is the ledger disposition, so leaving `out` there would keep disagreeing with
`T_ROWS.jsonl` even after the verdict cell changed; both cells are corrected.

---

## 4. Diff — `Tools/scripts/status_audit.py` (#1, #2, #5)

`STATUS.md` is generated (its line 1 says so and `Why the old numbers were wrong` says "regenerated, never
hand-edited"), so all four `STATUS.md` items land here or in the script's inputs — never in `STATUS.md`.

| item | STATUS line | generator site | input it reads |
|---|---|---|---|
| #1 `0x6BB2C66E` UNKNOWN | §`G2 — JC3` bullet 3 | `status_audit.py:301` — a **hard-coded prose string**, not computed | none; the string itself is the record |
| #2 winch `out` | §`T — translate` bullet 3 | `status_audit.py:305-308` — count is computed (`t['out']`), the **example list is hard-coded** | `T_ROWS.jsonl` `dispo` (the count is right; only the examples are wrong) |
| #3 live build | §`Built and measured` | `status_audit.py:50-67` `b2()` derives the tag by regex from `applied[0].file` | `Working/Translation/t5e_applied.json` → `Builds/test-090/…` |
| #5 T-14 label | §`Translation rows by document` | `status_audit.py:214-218` prints the raw `doc` value | `T_ROWS.jsonl` `doc` field (correct data, unlabelled) |

```diff
--- a/Tools/scripts/status_audit.py
+++ b/Tools/scripts/status_audit.py
@@ -42,4 +42,7 @@
 EVIDENCE = {"decoded", "decoded (fleet)", "derived", "derived (assumption noted)",
             "class", "epe", "read"}
+
+
+DOC_LABELS = {"T-14": "T-14 (lights - the 28 `T-L*` rows; card T-18)"}
 
 
@@ -214,5 +217,5 @@
     for name in sorted(d["t"]["docs"]):
         v = d["t"]["docs"][name]
-        L.append(f"| {name} | {v['rows']} | {v['evidenced']} | {v['assumed']} | "
+        L.append(f"| {DOC_LABELS.get(name, name)} | {v['rows']} | {v['evidenced']} | {v['assumed']} | "
                  f"{v['blocked']} | {v['out']} | {v['superseded']} | {v['next']} | {v['other']} |")
     h = d["t"]["t6"]
@@ -299,5 +302,5 @@
         "  233 roots; 10 `CDamageController` objects ship 1). The field is 4 bytes at `epe+1167` —",
         "  T-DM9's route (`Research/JC3Grab/DAMAGE_MECHANISMS.md`).",
-        "- The 10 BmAK audio banks once reported absent are all FOUND in the install (`AUDIO_BANKS.md`, G3-14: 10 found, 0 absent); only event `0x6BB2C66E` has no located bank (UNKNOWN). Rows T-AU3/T-AU5 were re-pinned to `next` on 2026-11-06 (the source side is complete; what remains is the JC3 event binding).",
+        "- The 10 BmAK audio banks once reported absent are all FOUND in the install (`AUDIO_BANKS.md`, G3-14: 10 found, 0 absent). Event `0x6BB2C66E` itself is carried by no bank, but its cooked twin `0x8EA6FCA0` (`Play_Disruptor_Vehicle_Tracking_Fire`) sits in `CHR_BatmanDisruptor` with 18 media ids (`Research/BatmobileGrab/AUDIO_EVENT_6BB2C66E.md`; `Working/Roadmap/sound.md` item 9052), so the tracker-fire sound has a carrier and no id is UNKNOWN. Rows T-AU3/T-AU5 were re-pinned to `next` on 2026-11-06 (the source side is complete; what remains is the JC3 event binding).",
         "",
         "### T — translate",
@@ -304,7 +307,8 @@
         f"- {t['assumed']} in-scope rows still rest on an assumption rather than a value with evidence.",
         f"- {t['blocked']} rows are blocked (camera composition, springs, JC3 model limits, rows awaiting a re-pin).",
-        f"- {t['out']} rows are out because JC3 has no system for them (air control, ram assist,",
-        "  winch, energy HUD, etc.) and none has a G2 carrier; they are excluded from the completion",
-        "  denominator rather than counted as unfinished.",
+        f"- {t['out']} rows are out because JC3 has no system for them (`T_ROWS.jsonl` `dispo: out`:",
+        "  T-PT2, T-PT5, T-PT13, T-PC6, T-TX6, T-TX7, plus the 7 T6 rows); each row's own `why` names the",
+        "  missing system. None has a G2 carrier, so they are excluded from the completion denominator",
+        "  rather than counted as unfinished.",
         f"- {t['superseded']} rows are superseded: T-10 re-opened them and found a carrier (weapons,",
         "  EMP, battle-mode values, the battle spotlight, the battle camera), so their values moved to",
```

Why the example list is replaced by ids rather than by new example words: the six `out` ids above are read
straight out of `T_ROWS.jsonl`, so the sentence can be checked by grep. Any prose paraphrase of what those
rows are about would be a new unverified claim, which is exactly the failure mode this card exists to fix.

**#3 is deliberately not in this patch.** The tag `test-090` is correct for the record `b2()` reads; the
disagreement is that `Working/Translation/t5e_applied.json` names `Builds/test-090/…` while the build tree
and backlog call the live pair `test-091`. Two candidate corrections, both inputs, neither applied:

- if test-090 is the live pair and the backlog is stale: change the eight `test-091` mentions in
  `GRAB_BACKLOG.md` (95, 129, 185, 249, 354, 362, 1293, 1298);
- if test-091 is the live pair: re-point `t5e_applied.json`'s `applied[].file` at `Builds/test-091/…`
  **and** nothing else — `STATUS.md` then follows on the next run.

Deciding which is a build question (`Builds/test-091` and `Builds/test-090/install.ps1 -Action Status`), not
a text one, so it is named here rather than guessed.

---

## 5. Diff — `ROADMAP.md` §8 itself (#4, #12, and the wording of #1/#3)

Two of the twelve claims are wrong about the records, and two more are right about the fact but wrong about
where the fix goes. Correcting the claim list is part of the same job, otherwise the next audit re-finds them.

```diff
--- a/ROADMAP.md
+++ b/ROADMAP.md
@@ -165,8 +165,19 @@
 ## 8. Record inconsistencies to fix (found by the audits)
 
-- `STATUS.md`: event `0x6BB2C66E` is listed UNKNOWN but is resolved (tracker AkEvent twin, `sound.md` item 5); the winch is listed `out` but the ledger says `blocked`; the live build is test-090 here but test-091 in the backlog; ledger size is quoted as 198/199/216/221 in different places; and the "T-14: 28 rows" are lamp rows, not damage rows.
-- `GRAB_BACKLOG.md`: §0.7 prose says 81,952/81,953 (now 81,953); D-6 "standalone" was disproven in game (RC4 replaces a vanilla `_debug` leaf); D-8 was overturned; the B-12 card calls turn-on-the-spot a "named omission" (forbidden by `STAGES.md`); B-15/B-17/B-24/B-25 numbers collide with `Research/specs/`.
-- `T10_DAMAGE.md` says T-DM7 is `out`; the ledger says `next`.
-- Q briefs 8600–8605 name RC4 and `install_v3.ps1`; repoint them after L0.
+- `STATUS.md` (generated — fixes go to `Tools/scripts/status_audit.py` or its inputs, never to the file):
+  event `0x6BB2C66E` is listed UNKNOWN although its twin `0x8EA6FCA0` is in `CHR_BatmanDisruptor` and the
+  id itself is still in no bank (fix: `status_audit.py:301`); the winch is listed `out` but is `blocked`
+  (`T-CT3`; fix: the hard-coded example list at `:305-308`); the live build is test-090 here but test-091
+  in the backlog (fix: `Working/Translation/t5e_applied.json`, or the backlog's eight mentions); the
+  "T-14: 28 rows" are lamp rows, not damage rows (fix: a doc label in the table emitter at `:214-218`).
+  Ledger size is **not** quoted as 198/199/216/221 anywhere — it is 244 rows plus T6's 37, 260 in scope.
+- `GRAB_BACKLOG.md`: §0.7 prose says 81,952/81,953 at two places (`:106`, `:351`); D-6's "standalone" is
+  wrong at file level (RC4 carries the vanilla `_debug` leaf over the civilian `_01` graph), not "in game";
+  D-8 was overturned; the B-12 card calls turn-on-the-spot a "named omission" (forbidden by `STAGES.md`);
+  B-15/B-16/B-24/B-25 collide with `Research/specs/` (B-17 does not), and the flares card cites the reticle
+  spec at `:1592`/`:1967` — see `NEW-WPN-46` in `NEXT_TASKS.md`.
+- `T10_DAMAGE.md` says T-DM7 is `out` at `:143` and `:162`; the ledger says `next`.
+- Q briefs 8600–8605: only `8601` names RC4 and `install_v3.ps1`; `8600` and `8602`–8605 name neither
+  (`8606` does). Repoint them after L0.
 
 ## 9. Bottom line: how long
```

--- a/ROADMAP.md
+++ b/ROADMAP.md
@@ -167,4 +167,8 @@
-- `STATUS.md`: event `0x6BB2C66E` is listed UNKNOWN but is resolved (tracker AkEvent twin, `sound.md` item 5); the winch is listed `out` but the ledger says `blocked`; the live build is test-090 here but test-091 in the backlog; ledger size is quoted as 198/199/216/221 in different places; and the "T-14: 28 rows" are lamp rows, not damage rows.
-- `GRAB_BACKLOG.md`: §0.7 prose says 81,952/81,953 (now 81,953); D-6 "standalone" was disproven in game (RC4 replaces a vanilla `_debug` leaf); D-8 was overturned; the B-12 card calls turn-on-the-spot a "named omission" (forbidden by `STAGES.md`); B-15/B-17/B-24/B-25 numbers collide with `Research/specs/`.
-- `T10_DAMAGE.md` says T-DM7 is `out`; the ledger says `next`.
-- Q briefs 8600–8605 name RC4 and `install_v3.ps1`; repoint them after L0.
+- `STATUS.md` (generated — fixes go to `Tools/scripts/status_audit.py` or its inputs, never to the file):
+  event `0x6BB2C66E` is listed UNKNOWN although its twin `0x8EA6FCA0` is in `CHR_BatmanDisruptor` and the
+  id is still in no bank (fix: `status_audit.py:301`); the winch is listed `out` but is `blocked`
+  (`T-CT3`; fix: the hard-coded example list at `:305-308`); the live build is test-090 here but test-091
+  in the backlog (fix: `Working/Translation/t5e_applied.json`, or the backlog's eight mentions); the
+  "T-14: 28 rows" are lamp rows, not damage rows (fix: a doc label in the table emitter at `:214-218`).
+  Ledger size is **not** quoted as 198/199/216/221 anywhere — it is 244 rows plus T6's 37, 260 in scope.
+- `GRAB_BACKLOG.md`: §0.7 prose says 81,952/81,953 at two places (`:106`, `:351`); D-6's "standalone" is
+  wrong at file level (RC4 carries the vanilla `_debug` leaf over the civilian `_01` graph), not "in game";
+  D-8 was overturned; the B-12 card calls turn-on-the-spot a "named omission" (forbidden by `STAGES.md`);
+  B-15/B-16/B-24/B-25 collide with `Research/specs/` (B-17 does not), and the flares card cites the reticle
+  spec at `:1592`/`:1967` — see `NEW-WPN-46` in `NEXT_TASKS.md`.
+- `T10_DAMAGE.md` says T-DM7 is `out` at `:143` and `:162`; the ledger says `next`.
+- Q briefs 8600–8605: only `8601` names RC4 and `install_v3.ps1`; `8600` and `8602`–`8605` name neither
+  (`8606` does). Repoint them after L0.
```

---

## 6. Records that need a decision, not a diff

These came out of the same check and are named so the fixes are not mistaken for text edits:

1. **`T-WLD13` / `T-WLD14`** (#8). Their `why` still ships D-8's lore route ("sink and stall"), so after the
   D-8 row is corrected the ledger is the stale record. A re-pin to the teleport row is a translate decision
   (`STAGES.md`: closest system + gap + build action), not a wording change.
2. **`B-12` / `T-MD8`** (#9). Removing the words "named omission" satisfies `STAGES.md` line 4 but leaves
   T-MD8 without the capability card that replaces the omission. The card is `TANKTURN.md`'s G2-21 gap.
3. **`Research/specs/B-22.md` / `B-23.md`** (#10). Both exist and no backlog card or §12 tracker row names
   them, so the collision audit found two specs with no card as well as two cards with colliding numbers.
4. **`Research/specs/B-26.md`** (#10). Cited by `GRAB_BACKLOG.md:1968` and absent from disk; either the spec
   is unwritten or the citation is stale. Not guessed here.
5. **Queue briefs 8600–8605** (#12). The repoint after L0 is real work, but only `8601` currently needs it.

## 7. What this report does not claim

- No in-game evidence was produced or consulted for D-6 or D-8; both verdicts rest on files (and, for D-8,
  on an operator ruling recorded only in `ROADMAP.md` §7).
- The task-number collisions are reported as they stand in `GRAB_BACKLOG.md` §8/§12 only. Whether the
  `Builds/bm-RC4*` receipts mean spec `B-24`/`B-25` or backlog `B-24`/`B-25` was **not** audited file by
  file; the renumber brief must do that before touching them.
- `STATUS.md` was read as generated output and not edited; the line numbers it cites in other documents
  (`sound.md` says "STATUS.md:99") drift whenever the file is regenerated, which is why every citation here
  uses a section and a quoted string instead.
- No patch was applied. `tmp/freebuff/scratch/diffwork/*.fixed` are generated copies; the four sources named
  above are byte-identical to `HEAD`.

## 8. Reproduce

```bash
cd /e/Modding/JustCause3/JC3-Batmobile
python -c "import json;[print(json.loads(l)['id'],json.loads(l)['dispo']) for l in open('Working/Translation/T_ROWS.jsonl') if json.loads(l)['id'] in ('T-DM7','T-CT3','T-W1')]"
grep -rn "81,95[23]" GRAB_BACKLOG.md
grep -rn "198/199\|216/221" --include=*.md --include=*.py .      # only ROADMAP.md:167
ls Research/specs/ | grep -E "^B-(1[4-9]|2[0-9])"                 # B-15,B-16,B-22,B-23,B-24,B-25; no B-17
grep -n "install_v3\|RC4" tmp/freebuff/queue/860[0-5]*.txt        # hits in 8601 only
python -c "import json;print(json.load(open('Working/Translation/t5e_applied.json'))['applied'][0]['file'])"
sed -n '299,309p' Tools/scripts/status_audit.py                   # the two hard-coded prose blocks
sed -n '5p' Working/Translation/T14_LIGHTS.md                     # "One row per entry ... T-L8...T-L35"
```
