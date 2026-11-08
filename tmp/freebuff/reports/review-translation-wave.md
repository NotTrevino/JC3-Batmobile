# Review 8299 — the translation wave since brief 8099

A review, not a build. Nothing was rebuilt, installed or driven; every number below was either
re-read from the evidence a report cites or re-derived by the script that owns it.

## 1. What was reviewed

Reports read (all of them, not a sample): `carrier-*`, `app-*`, `keep-audit-*` (audio/fx, systems),
`apply-*` (gadget rows, riot-mode rows, light rows, effect rows, the two keep-audit fixes,
texture-bake plan, mode switch, collision+audio leads, audio fix tree), and
`translation-closeout-t23`. Queue read: all 34 briefs in `tmp/freebuff/queue/`.

The arbiter for every disagreement was the script or ledger, not another report:

```
python Tools/scripts/t18_lights.py --check
PASS: 28 rows: 26 mapped, 2 named omissions, 0 sharing a lamp | targets 22 = 11 donor rows + 1 graph object + 10 custom | donor 21 rows / 22 objects | ledger 28/28

python Tools/scripts/t7_weapons.py --check
PASS: 15 rows = 13 WPN codes + 2 decision rows (13 with a JC3 carrier, 1 named omissions, 1 blocked) |
      164 aspects classified, 46 UNKNOWN | 3 edits + 6 structural + 6 withdrawn | 4 JC3 ids, 2 driver slots

python Tools/scripts/t23_closeout.py --check
gate TX: 75 codes (58 carried, 3 named omission, 4 blocked, 10 documented, 0 unmapped) | 199 ledger rows |
         assumed 1 (0 unsigned) | decisions 11/11 answered | 19 artefacts (17 payloads + 2 records) over 24 B steps
gate TX ok

python Tools/scripts/t11_modes.py --check
FAIL ledger T-WP4 is next, the row cites blocked
FAIL: 15 rows | MOD-1 4 / MOD-2 11 | compromises carried 8, inside band 1, omitted 6 | ledger 15/15
```

So the wave's headline counts hold: **199 ledger rows, 19 artefacts over 24 B steps, decisions
11/11, assumed 1 and signed**. The findings below are the places where a row or a report says
something the ledger or the script does not.

## 2. Findings

### F1 — The chapter damage masks were dropped with no card (high)

`apply-texture-bake-plan.md` §2/§4: "four of those (the chapter masks) cannot be built faithfully at
all without a variant set", and `D9` stays `drop` in `appearance_plan.py`.
`app-dropped-classes-plans-a.md` §11 #4 restates it: "the chapter transition is published as two
authored drop entries … the chapter→state map itself is `[UNKNOWN]`".

That is the "accept JC3 limit" pattern — except the same wave found a carrier:
`app-damage-chapter-masks.md` §7 names `SupportDmgBlend` + `m_Damage`, and what fails is only
*many* states (variants), not *one*. So the deliverable could be one static damaged set (the two
drop entries already describe it) and the row would be `next` with a named limit.

Nothing owns it. No row is created, no card number is attached, and the close-out does not list D9
among the omissions either. Fix: a card (next free number) or a signed decision, and one line in
`COMPROMISES_T`.

### F2 — Two rows' "card" is a research card that already refuted itself (high)

`Tools/scripts/t_blocked.py` `WAITS`:

- `T-MD8`: "a native turn-on-the-spot mechanism — G2-21 refuted its candidates and found 0
  tank-only driving members; a second variant does not create one".
- `B-12`'s Done text: T-MD8 and T-MD14 "stay named omissions — the pivot has no carrier even with
  two variants (G2-21) and the `BattleMode` usage has no consumer (U1)".

So the wait names G2-21, and G2-21 is the card that *closed the question negatively*. A reader of
the pin sees "carded"; the truth is "will never close, and the card that would close it has
already reported no carrier". That is an omission with a card number attached to it that cannot
deliver — worse than an undeclared omission because it looks like work in flight.

Fix (documentation, not code): move T-MD8/T-MD14 from `WAITS` to the resolved/omitted map with
"no carrier exists (G2-21, 0 of 216 candidates)" and a named workaround card if the operator wants
one (the entry reports 0 members, so a workaround is a new mechanism, e.g. a scripted yaw impulse).

### F3 — T-WP4's residual gap cites the wrong two cards, and t11_modes is red for it (high)

`Tools/scripts/t_blocked.py` (~line 198), `T-WP4` → `remaining`:

> "a 2.0 s held lock, an 8-target salvo and the reticle link have no member (cards B-24 / B-25)"

B-24 is the handling-values card and B-25 is the lens-flare/light-unit card. Neither has anything
to do with a held lock, a salvo or a reticle. **That gap has no card at all.** The pin's own
sentence says "has no member", which is the definition of a row that needs a card, and gives it
two unrelated ones.

Related mechanical drift, same cause: `Tools/scripts/t11_modes.py:686` hard-codes
`("T-WP4", "blocked")` in its expected ledger, so `t11_modes.py --check` now fails with
`ledger T-WP4 is next, the row cites blocked`. T-WP4 legitimately moved to `next` under operator
ruling 4 (the split); the script's expectation did not move with it.

Consequence for the wave: brief 8305 / 8506 / 8603 would have queued "lock-hold, salvo, reticle"
as scheduled build work. They now say explicitly that no card exists. The script fixes are small
but are outside this review's edit scope, so they are recorded here and in the two briefs that
touch them.

### F4 — The collision premise in the build payload is the superseded one (high)

`collision-where` (G3-16) and `Research/BatmobileGrab/COLLISION_WHERE.md` decode
`Physics.Batmobile_V3_Physics` (export 158266, reached from `SVehicleMesh` at property offset 824)
as **2 body setups / 3 boxes / 1 constraint**. `apply-keep-audit-fixes-systems.md` §1.3/§2 and
`Working/Translation/t16_collision_keepaudit.json` still describe "3 drivable boxes + 56 convex
elements; the 32 bodies are wreck geometry".

The 56 are not elements of the car: they are the two hidden `StaticMesh` convex sets (43 + 13),
which the collision-where pass reports as hidden. The ledger has already moved — T-22 and B-10 are
reopened, T-P3/T-CO1/T-CO2/T-CO3 carry the asset, and `T22_REOPEN.md` + `t22_reopen.py --check`
(10/10 oracles) is the authority.

Risk that remains: the *batch payload the build consumes* is `t16_collision_keepaudit.json` until
B-10 lands, so a D-08 build today would transcribe the 3-boxes+56 premise the reopen just replaced,
and no gate would catch it (`t22_reopen.py --check` checks the plan, not the shipped hull). The
briefs for D-08, RC4, V-02 and Q-2 now name `T22_REOPEN.md` as the source.

### F5 — Three different counts for the same weapon table (medium)

| report | claim |
|---|---|
| `apply-gadget-rows.md` | "T-7 named omissions 6 → 0", "0 named omissions" |
| `apply-riot-mode-rows.md` | "14 rows = 12 WPN codes + 2 decision rows (7 with a JC3 carrier, 4 named omissions)" |
| `t7_weapons.py --check` (actual) | **15 rows = 13 WPN codes + 2 decision rows (13 carried, 1 named omission, 1 blocked)** |

Both reports' numbers are stale against each other *and* against the script — the gadget pass
reduced omissions and the riot pass added rows, and neither re-read the other. A reader who takes
either report as the state of the table is wrong by 2–4 rows.

Also worth stating: of 164 classified aspects, **46 are UNKNOWN**. No report claims the weapon set
is fully translated, but the "13 of 15 carried" headline should not be read as "46 aspects
resolved".

### F6 — The appearance percentages and the plan tally are different denominators (medium)

Measured and consistent (`appearance_progress`): overall **54.6%**, strict **49.3%**, of-slotted
**91.1%**, textures **53.9%** (17/38 transferred + 7 partial). Plan tally:
**bake 23 / route 61 / drop 88 = 172 entries**.

"12 of 23 unfaithful" is true of the 23 texture rows only. The 88 drops are per-component, not
per-texture, so 12/23 must never be quoted as "half the appearance work fails". The 8303/8507
brief lines say "12 of 23 texture rows" for that reason.

### F7 — Two lights rows wait on cards that are already `done` (medium)

`t_blocked.py`:

```
"T-L28": "a body `_LIG` anchor node plus a `CarLight` block on the body (B-03 / B-04) - socket and ..."
"T-L30": "the same body-hosted `_LIG` node and `CarLight` block (B-03 / B-04) for `HeadLight2c`; ..."
```

`GRAB_BACKLOG.md` §12: **B-03 = done** (`lights_manifest.json`) and **B-04 = done**
(`bm_vehicle_parts.json`). Neither delivered a body-hosted `_LIG`/`CarLight` block — that is a
body-file edit, which is why the rows are still socket-absent. So the pin's wait text points at two
completed cards; anyone triaging "what unblocks T-L28" would go looking at finished work. The
`apply-wheels-and-tyres` pass already named the real residual (the `_LIG` node); the pin should say
that instead of B-03/B-04.

### F8 — "10 banks found / 0 absent" is true of the pinned GUIDs, not of BmAK audio (medium)

The ledger evidence for T-AU3/T-AU5 is `AUDIO_BANKS.md`: **10 claimed / 10 found / 0 absent**. That
is the set of JC3 banks the 45 pinned GUIDs live in — the thing T-AU3 asked for, correctly closed.

It is *not* a statement about BmAK's audio coverage. `keep-audit-audio-fx.md` §2: **90 rows / 26
event ids** resolve to `missing-bank`, because 10 *BmAK* banks are not on disk
(`BML_Batmobile_Subjective`, `BML_Impacts`, `BML_Sonar`, `CHR_BatmanAlerts`, `CHR_BatmanDisruptor`,
`OBJ_Rolling_Objects`, `UI_InGame`, `VEH_Tank_Heavy`, `VEH_Tank_Missiles`, `VFX_Tank_Explosion`).

Two different sets of ten. Two reports, one word ("banks"), opposite results. The unblock is real;
the coverage claim attached to it would not be. Brief 8308 now separates them.

### F9 — Manufacturer's count quoted without its basis (low)

`T-FX5`: "74 `.effc` in the donor `.ee`, 23 unreferenced by the 51 rows". The 74 holds
(`FX_TABLE.jsonl:27222`, container/ext match). The 23 does not: `LEDGER-g3src.md:197` records that
the producer never states what it counted, and the keep-audit pass marks it UNKNOWN. Both
`keep-audit-audio-fx` and `T13_FX` carry the 23 in a table anyway. It is harmless (the row keeps
either way) but it is a number without evidence, and the next report should drop it or reproduce it.

### F10 — The audio fix report's own RED was then reported as fixed (high, caught in this review)

`audio-fix-tree.md` is explicit: bm-004c applies both derived fixes, `5/5 loudness` pass,
`2/3 loop-wrap` pass, and **`vehicles#279` still clicks** — wrap **-28.27 dBFS** on the decoded
record, **-39.68 dBFS** on the payload alone, against the -40 dBFS rule and 5.7 dB worse than the
payload's own p99 interior step (-46.01). The 408-frame trim gained 22.18 dB and did not clear it;
the diag's predicted -60.77 dBFS is not reproducible even though the payload sha matches.

My own first-pass brief text said both audio numbers "were fixed in bm-004c". That was wrong for
279 and is corrected in 8308 and 8403 — the honest state is one unresolved loop click with a
recorded measurement mismatch, and it is the *only* V-04 gate still red.

### F11 — Stale checkers are being read as failures (medium, process)

Three scripts fail for reasons that are not the code they test:

- `v05_driving.py --check` — "T-ST7 is no longer blocked; the turning circle must be re-derived".
  T-ST7 moved to `next` on 2026-11-06 (0.25 s low / 0.091 s high) and the prediction sheet still
  models the old blocked state. This one is a **real work item**: every driving band depends on the
  re-derived circle.
- `t_boost_rows.py` and `t_vnf_six.py` — hard-coded **198-row** ledger assertion; the ledger is 199.
- `t11_modes.py` — the T-WP4 drift in F3.

The wave reports list all of these, but they are also being counted among "reds" in the build/verify
briefs. The 83xx/84xx lines now say which is a test failure (none), which is a work item
(v05's turning circle), and which is a pin (198).

## 3. What held up (checked, not assumed)

- `T-AU2`'s "21 of 45 GUIDs still donor" is **counted**, not asserted: vehicles 24 / character 2 /
  effects 19, and test-060 swapped `vehicles.bank` only. The gap is B-26 with a named mechanism
  (`SAttachedEffect` per entity, no decoded per-entity bank override).
- `T-AU3`/`T-AU5` really are resolved: 10/10 claimed banks found, and `0x6BB2C66E` is the one GUID
  whose declared bank lacks it — named, not hidden.
- Lights: 28 rows, 26 mapped, 2 omissions, 22 targets, no two rows sharing a lamp. T-LG6's eight
  range values (60/45/40.96/20.48/10.24/4/1.5/0.8) and cone angles come from the BmAK light table;
  60 and 45 exceed the fleet max 50 and are declared R3 rather than silently clamped.
- Health/collision constants: chassis boxes 690.305×374.536×207.5 and 679.585×345.688×103.5, pod
  166.177×189.365×39.8 at 4.000°, `max_health` 36000 licensed for bm-009 + bm-RC2, thresholds
  4000/4000/1050/250 — all re-derived by `t22_reopen.py` (10/10) and `t16_*`, not copied.
- Effects: 17 rows, 17 carriers, **0** named omissions, and the private-effect writer is B-17.
- `t23_closeout.py --check` is now **green**: 75 codes, 58 carried / 3 named omission / 4 blocked /
  10 documented / 0 unmapped, decisions 11/11.
- The ledger is internally consistent: `t_rows.py check` 199 rows, 35 edits over 16 rows, no row
  both `next` and edited.

## 4. Brief edits

33 briefs updated in `tmp/freebuff/queue/` (every file in the 83/84/85/86/87 range that had not yet
run). Nothing was deleted or reordered; each file got one appended
`Updated by review 8299: …` paragraph and nothing else. `8135-…` starts with 81 and was left alone.

| range | briefs | what the appended line now says |
|---|---|---|
| build | 8300, 8301, 8302, 8303, 8304, 8305, 8306, 8307, 8308, 8309, 8311, 8312, 8320 | D-08 reads `T22_REOPEN.md` (2 bodies / 3 boxes / 1 constraint, 2 shapes missing, 0 free hull slots); D-09 carries 24-of-45 audio and the still-RED vehicles#279; D-10 uses 109 `next` rows and B-24's 15 values over 13 rows; D-12 uses the real B-12 split (4 flip / 2 omit / 2 same switch), not "13 of 15"; D-04 keeps 12-of-23 textures whole and 54.6/49.3/91.1/53.9 as the numbers; D-06 does not promise lock-hold/salvo |
| review/build gate | 8399 | the three genuine reds to check are v05_driving (work), t_boost_rows + t_vnf_six (198 pin), and T-WP4's mis-cited cards |
| verify | 8400, 8401, 8402, 8403, 8404, 8405, 8406 | file-gate counts (199 rows, 24 steps, 19 artefacts), RC2's 0.0004 silhouette margin and 61 parts, the 8 forced slots and Rebel Drop keys, the corrected 5/5 loudness + 2/3 loop-wrap, the turning circle as a precondition of V-05, and the disclosure list for APPROVAL_REQUEST |
| pilot | 8505, 8506, 8507, 8508, 8599 | cards match the real gains and gaps; no promise of a locked salvo or 17 delivered flares; combat steps marked not-yet-provable where B-15/B-18/B-19/B-20/B-21 are unbuilt |
| campaign | 8600, 8601, 8602, 8603, 8604, 8605, 8699 | expected gaps recorded as known, not as new failures; the collision gap routed to a B-10 fix card; 87xx fix briefs called for on the multi-element write and the lock-hold/salvo gap |

Two of those lines were corrected inside the same pass (F10): 8308 and 8403 first said both audio
numbers were fixed in bm-004c; they now carry 279's -28.27/-39.68 and the 2/3 result.

Applier, kept for reproducibility (idempotent — it refuses a file that already has the marker):
`tmp/freebuff/review_8299_apply.py`.

## 5. Residual risks this review does not fix

1. **`t16_collision_keepaudit.json` is still the build's collision payload** and still says
   3 boxes + 56 convex. Until B-10 rewrites it, a D-08 tree transcribes a superseded premise. The
   gate that would catch it does not exist yet (`t22_reopen.py` checks the plan).
2. **`t11_modes.py:686` and `t_blocked.py`'s T-WP4 `remaining`** are both stale in the same way and
   both small; they need a pin edit, which this review did not perform (out of scope: it edits
   briefs and findings, not pins).
3. **`v05_driving.py` is red for a real reason** — the turning circle is still the blocked-state
   model. Every driving band inherits that error until it is re-derived.
4. **`t_boost_rows.py` / `t_vnf_six.py` assert 198**; they will keep failing until someone decides
   the ledger is 199 (it is) and re-pins.
5. **F1 and F2 are decisions, not research**: one static damage set for D9, and no carrier for
   T-MD8/T-MD14. Both need the operator or a card number, not another pass.
6. **`vehicles#279`'s measurement mismatch** (diag -60.77 vs measured -28.27/-39.68 for the same
   payload sha) is UNKNOWN and is the only audio gate left red.

## 6. How to revert

- Briefs: each appended paragraph is the last block of its file; delete from the blank line before
  `Updated by review 8299:` to EOF. No other content changed.
- `tmp/freebuff/review_8299_apply.py`: delete it.
- This report: delete it.
- No ledger, plan, build or bank was modified by this review.
