# apply-gadget-rows — T-WP5 / T-WP7 / T-WP8 / T-WP9 / T-MD2

STATUS: done. The five rows now carry a closest-system chain with evidence, each names a build card
for its remaining gap, every one states in its own final text whether it is BmAK-exact, and no row
ends as `omitted` or as a bare proof of absence. Four new cards (B-18…B-21) in `GRAB_BACKLOG.md` §8
own the gaps; every standing gate is green.

## What changed, row by row

| row | was | now (disposition) | closest-system chain | card |
|---|---|---|---|---|
| T-WP5 EMP burst | `blocked`, "nothing fires it" | `next` | entity `CForcePulse` `EMP` + `truck_emp.ftune` (100 player/AI in 25 m at full radius) + `world` (0, 2.0356, 0.6992) + the flag triple `4912FC04` 0 / `AE6F7EFF` 1 / `CF4F7880` 1 (unique among 307 pulses) + `id:D3DDD766` → `CMaterialEffectTable emp_flatbed_table`; the disable writer is the engine's `CEMPWeapon` | **B-18** |
| T-WP7 drone hacker | `out`, "no allegiance class" | `next` | two `SAttachedEffect` rows (beam `Usage` 4131019937, success value-driven; 5,342 objects / 232 graphs) + the SAM context-act hack (`CInteractionGraph`, `use_item`, 2 `CInteractionTrigger` volumes, `rico_contextact_hack_sam*.anim`) + `faction` on weapon points + `CreatePoi` label for the HUD line | **B-19** |
| T-WP8 seismic sonar | `out`, "no sonar class" | `next` | `CForcePulse` with `gen_explosion_5m_nodamage.ftune` (0 damage / 5 m) + `CMaterialEffectTable` hook + the `BmGame.BML_Sonar` bank (355,830 B, 7 HIRC / 6 verified events) + `CreatePoi` for the reveal | **B-20** |
| T-WP9 vehicle tracker | `out`, "no tracker class" | `next` | mounted weapon entity + `missile_base_tuning.*` + `SWeaponPoint.world` with `LaunchRotationOffset` 5461 = **30.0 deg** at `BattleModeSpotLight` + the mission tracker graph `graphs/mission/mm130/mm130_tracker.gdc/.gsc` + `CreatePoi(POI_TYPE_LOCK_ON_TARGET 21)` | **B-21** |
| T-MD2 Immobilizer | `blocked`, compromise `omitted` | `next`, compromise **`carried`** | `w618` launcher clone → entity `CForcePulse` (`truck_emp.ftune`, flags, `emp_flatbed_table`) → `CEMPWeapon` (`w702_emp` id 702/type 6/500 damage/50 m; `w503_turret_emp` 503/2/500/750 m) as the disable writer; `is_disabled_by_emp` (exe 0x24EA080) is engine vocabulary with 0 asset bindings | **B-18** |

Every one of the five ends with an explicit `BmAK-exact` statement: **no** in all five, with the
exact reason (the disable duration is UNKNOWN on BmAK's own side too — `DisableEnemyDuration`
@2400 serialises no value; the allegiance flip, the reveal and the homing flag/distance have no
member on either side). Each row's ledger `why` repeats it, so the statement survives into
`T_ROWS.jsonl` and `STATUS.md`.

`T-MD2`'s compromise moved `omitted` → `carried` because the EMP is mode-independent (D-7): the
launcher, the pulse and the disable chain are not a mode behaviour, so the hybrid carries them and
only the writer is missing. Dispositions: T-7 named omissions 6 → **0**, blocked 3 (T-WP4/T-WP6/
T-WP13 unchanged); T-15 compromised rows now `carried` 8, `inside band` 1, `omitted` 6 (T-MD5/6/7/8/
13/14, none of them in this brief).

## The four new cards (`GRAB_BACKLOG.md` §8, tracker rows in §12)

* **B-18 · EMP disable write path** (serves WPN-4, WPN-5, MOD-1) — clone `w702_emp.wtunec`, mount
  the `CEMPWeapon` entity on the second driver slot `id:00568A74`, copy the pulse with the flag
  triple; invent no trigger; probes Q-EMP-1…4 measure whether the engine stalls a car and for how
  long (that bracket is the only source for `DisableEnemyDuration`).
* **B-19 · Drone hacker chain** (WPN-7) — beam + success attachments, the context-act interaction,
  the authored side flip on the target's weapon points (no `allegiance`/`owner` member exists in
  295 wiring dumps), optional player-side drone through `Item.Name` = `hash_jenkins(leaf)`.
* **B-20 · Sonar pulse and reveal** (WPN-8) — 0-damage pulse, a private ring `.effc` via B-17's
  writer, the six `BML_Sonar` events, an authored vehicle action and marker pass; the treadmark
  half stays out because both of its BmAK assets are `missing-object`.
* **B-21 · Vehicle tracker** (WPN-9) — weapon entity + tune, 30.0 deg baked into the fire position,
  authored homing on the projectile, tracker graph + distance HUD element (T-19).

## Files written

* `Tools/scripts/t7_weapons.py` — `row_wpn5` extended (closest chain, trigger, build card, BmAK-exact
  aspects; disposition `next`); new `row_wp7`, `row_wp8`, `row_wp9` replace the three `omission(...)`
  calls; §6 items 2–3 now name B-18/B-20 instead of "stays blocked".
* `Tools/scripts/t11_modes.py` — T-MD2 rebuilt (chain, `carried`, `next`, probes, why) and §5's
  `instead` note updated.
* `Tools/scripts/t_rows.py` — `DISPO` for the five ids moved to `next` with the evidence in each
  `why`.
* `Tools/scripts/audit_compromises_t.py` — the four weapon AUDIT entries restated (plan + loss) so
  the compromises doc does not keep the old "nothing; no … class" text.
* `GRAB_BACKLOG.md` — B-18…B-21 cards + four §12 tracker rows (additive; nothing removed).
* Generated by the owners' own tools: `Working/Translation/T7_WEAPONS.md`,
  `t7_weapons_edits.json`, `T11_MODES.md`, `t11_variants.json`, `T_ROWS.jsonl`,
  `COMPROMISES_T.md`/`.json`, `STATUS.md`.

## Commands and output (verbatim)

```
$ python Tools/scripts/t7_weapons.py --write
T7_WEAPONS.md + t7_weapons_edits.json: 14 rows (12 WPN + 2 decisions), 161 aspects (44 UNKNOWN), 3 edits, 559 md lines
t7write=0
$ python Tools/scripts/t11_modes.py --write
...\t11_variants.json: 15 rows (MOD-1 4, MOD-2 11), compromises {'carried': 8, 'inside band': 1, 'omitted': 6}
...\T11_MODES.md: 172 lines
t11write=0
$ python Tools/scripts/t_rows.py build
...\T_ROWS.jsonl: 198 rows, 35 edits over 16 rows
trowsbuild=0
$ python Tools/scripts/audit_compromises_t.py --write
wrote ...\COMPROMISES_T.json / COMPROMISES_T.md
72 audited, 1 approved, 71 unapproved
auditwrite=0
$ python Tools/scripts/status_audit.py --write      # the re-pin
wrote E:\Modding\JustCause3\JC3-Batmobile\STATUS.md
statuswrite=0

$ python Tools/scripts/t7_weapons.py --check
PASS: 14 rows = 12 WPN codes + 2 decision rows (11 with a JC3 carrier, 0 named omissions, 3 blocked) | 161 aspects classified, 44 UNKNOWN | 3 edits + 6 structural + 6 withdrawn | 4 JC3 ids, 2 driver slots | ledger 14/14 | json match True, md match True
t7check=0
$ python Tools/scripts/t11_modes.py --check
PASS: 15 rows | MOD-1 4 / MOD-2 11 | compromises carried 8, inside band 1, omitted 6 | ledger 15/15
t11check=0
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 75 keep 60 epe 26 re-read 0 blocked 9 out 5 superseded 7 | edits 35 over 16 rows
check ok
$ python Tools/scripts/audit_compromises_t.py --check
72 audited: 1 approved, 71 unapproved; by dispo {'blocked': 9, 'out': 5, 'superseded': 2, 'next': 35, 'edit': 10, 'keep': 11}
OK: every approval quote re-read at its cited line; document re-derived identically
$ python Tools/scripts/status_audit.py --check
STATUS.md is current
$ python Tools/scripts/t17_fx.py --check
PASS: 17 rows (17 chosen, 0 named omissions) | FX codes 4/4 | donor effects 85 | fleet .effc 955 | sockets 8 | ledger 17/17

$ python Tools/scripts/grab_model.py check            -> checks 15/15, schema 6, OK
$ python Tools/scripts/bmak_chain.py --check          -> PASS: 105 objects, 9225 named bindings, 336 cross-checked, 0 conflicts
$ python Tools/scripts/bmak_coverage.py --check       -> check ok (423 fields -> 19 rows; 777 feature rows -> 34, 0 unassigned)
$ python Tools/scripts/t3_fleet.py --check            -> check ok (41 members over 156 vehicles)
$ python Tools/scripts/jc3index.py check              -> check ok: 81952 rows, 78907 paths, 1 unnamed entry, DLC 20682/20682 named
$ python Tools/scripts/jc3hkx.py check --all          -> check ok: 233 entities, 18865 hulls (convex 18865), 0 problems
$ python Tools/scripts/jc3fx.py check                 -> check ok: 57,187 effect/camera/trim files, 0 problems
```

## COMPROMISES (for operator review — nothing here was accepted silently)

1. **T-WP5 / T-MD2 — the disable is not carried as a value.** The pulse, its tune, its flags and the
   material table are decoded and will ship; what writes `is_disabled_by_emp` is engine code with 0
   asset bindings, and BmAK's own `DisableEnemyDuration` serialises no value in any of the three
   packages. B-18's probes Q-EMP-1…4 are the only instrument; they are gated by the test ban.
2. **T-WP7 — the allegiance flip has no member.** The effects, cadence, HUD line and interaction are
   carried; the side change is authored (B-19) and which runtime value it must write is UNKNOWN.
3. **T-WP8 — the reveal is authored.** The pulse, the ring and all six sound events are carried; no
   decoded JC3 script creates a scan POI, and BmAK's treadmark effect/sound are `missing-object` in
   its own grab.
4. **T-WP9 — homing and the distance readout are authored.** The fire position (30.0 deg), the tune
   and the POI system are carried; no homing flag/delay member exists in 444 tune member paths and
   `CreatePoi` carries no distance.

## UNKNOWNs

* What the three EMP pulse flags mean (`4912FC04`/`AE6F7EFF`/`CF4F7880`) and whether they are the
  disable — Q-EMP-2 would decide; no data does.
* Whether the engine reads `is_disabled_by_emp` by name/hash at all (the vocabulary string is not
  proof; the ADF measurement in `ARMOR_STEP.md` §2 is the precedent, not yet run on this block).
* Whether a `CEMPWeapon` is accepted in a car's weapon slot (0 of 88 vehicle components is one).
* The firing moment of any `CForcePulse` (293/307 are owned by an explosion pointer; 14 unowned).
* What a `CMaterialEffectTable` draws (opaque 30-byte blob, 72 objects) and the field list of
  `.ctunec`'s `CameraShakeModifierParams`, so the charge/blast shake numbers convert through nothing.
* Which member a cloned tracker missile must carry for homing, and where a POI distance would come
  from — both are B-21 probe questions.

## Revert

Every change is additive or a re-derivation, so reverting any file restores the previous document by
re-running its tool:

* `Tools/scripts/t7_weapons.py` — restore `row_wpn5`'s old return dict and swap `row_wp7/8/9` back to
  the three `omission(...)` calls (the helper is still present, untouched); then
  `python Tools/scripts/t7_weapons.py --write`.
* `Tools/scripts/t11_modes.py` — restore the old T-MD2 `add(...)` block (`omitted` / `blocked`) and the
  old `instead` entry; `python Tools/scripts/t11_modes.py --write`.
* `Tools/scripts/t_rows.py` — restore the five old `DISPO` lines; `python Tools/scripts/t_rows.py build`.
* `Tools/scripts/audit_compromises_t.py` — restore the four AUDIT tuples; `--write`.
* `GRAB_BACKLOG.md` — delete the B-18…B-21 sections and their four §12 tracker rows (nothing else in
  the file was touched).
* Generated docs and `STATUS.md` are never hand-edited: the `--write` of each owning tool restores
  them once the scripts are reverted.

No game was launched, nothing was installed, no `Builds/bm-*` tree was edited, and no shipped
`.effc`/`.tune`/`.ee` was patched in place (R7). `MODLOG.md` was left untouched per the session rules;
this report is the journal entry.
