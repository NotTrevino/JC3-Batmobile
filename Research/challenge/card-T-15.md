# Assumption challenge — card T-15 · Modes translation

Written 2026-10-30. **Read-only review**: no file outside this one was modified — not
`GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`, `Tools/`, `Working/`, `Builds/`, and nothing in a game
install. No game launched, nothing written to `D:\Games`, nothing committed, no secret read.
Only the generators' own `--check` commands and in-memory Python heredocs were run; no probe script
was left on disk.

**In scope**, as the task requires: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–76), the T-15 card
(lines 915–922), its §12 row (line 1324), and the MODLOG sections `## T-15 · Modes translation —
intended change` (13435), `— done (2026-10-28)` (13504), `## T-15 rework · … intended change`
(14700) and `## T-15 rework — done (2026-10-29)` (14820), plus the card's outputs —
`Working/Translation/T11_MODES.md` (146 lines), `Working/Translation/t11_variants.json` (976 lines),
`Tools/scripts/t11_modes.py` (1,048 lines). Cross-checked against everything those files cite:
`Research/BatmobileGrab/MODES.json`, `CAMERA.json`, `objects.jsonl`, `WEAPONS.json`,
`Working/Translation/t14_lights.json`, `t12_audio_map.json`, `T_ROWS.jsonl`, `STATUS.md`,
`Working/Camera/CAM_TUNE.json`, `Research/JC3Grab/{USAGES,TANKTURN,LIGHT_SYSTEM,VOCABULARY}.json/md`,
and — for the claims T-15 leans on — `T7_WEAPONS.md`, `T6_HUD_CAMERA.md`, `T14_LIGHTS.md`,
`Research/BatmobileGrab/ANIMATIONS.md` and the G1-12 section of the MODLOG.

**Card as written:** "Do: if D-2 = two variants: list per variant every row that differs (top speed
curve, torque, steering/pivot, weapons enabled, camera tune, lights, armour reduction, audio) with
the BmAK source (`BattleModeVSpeedCurve` 0→60, 600→40, 1200→30 etc. — units converted). If D-2 =
hybrid: one row set with the compromise declared per row. … **Done: every MOD-2 behaviour has a row
in each variant or a named omission.**" D-2 is resolved **(b) one hybrid car**.

---

## VERDICT

**The gate is green and every number I could re-derive is right — but two of the fifteen rows
assert a weapon capability the project's own ledger calls `blocked`, and the "inside band" camera
row rests on misreading a speed-interpolated FOV pair as a range.** `t11_modes.py --check` passes
(exit 0), `t_rows.py check` and `status_audit.py --check` are green, all 198 ledger rows and the
`STATUS.md` line reconcile, the 107/46/61/31 field census and the 31-vs-15 split recompute exactly
from `MODES.json`'s `fields` array (not just its summary), the six torque-curve points reproduce
from `objects.jsonl` in all four packages, `TANKTURN.json` really has 5 refuted candidates and 0
tank-only module types, and the 9 light behaviours really have no battle value.

What does not survive: **T-MD9 says the hybrid carries "all weapons on the one car" and T-MD2 says
"the launcher is available in both modes", while `T-WP13` — a ledger row both files sit next to —
is `blocked` because "the fleet has 2 driver slots at most" for 11 weapons.** D-7 is a user
decision that every weapon *should* be available, not a demonstrated carrier; T-15 cites the
decision as if it were the capability. Second, **T-MD11's "FOV 60 lies in the tune's 55–63 band, so
no value changes"** describes `FOV [55,63]`, which the camera tune pairs with
`FOVVelocityRange [5,108]` — the FOV *sweeps* 55°→63° with speed, so 60 is a mid-sweep value, not a
band the car can sit in. The conclusion (no edit needed) is still right, the reason is not.
Third, **T-MD12 prints `decoded` for four battle lamps, two of which ship at brightness 0.0** and
one of which T-18 itself calls `derived` (a custom preset-0 entry). Fourth, **T-MD10 answers "armour
reduction" with the one field that carries that name, while three serialised battle impact-damage
fields (one of them package-varying) get no row and no omission** — a name-first search where a
behaviour-first one would have found them. Fifth, the "identical in all four packages" flag on the
battle curve is vacuous in `MODES.json` (per-package values are `None`); the truth is proven by
`objects.jsonl`, and `--check` does not test that path.

| # | assumption | verdict |
|---|---|---|
| A1 | the Done gate (`t11_modes.py --check`, ledger, STATUS) is green and reproducible | **HOLDS** — PASS, exit 0; 198 rows; STATUS current |
| A2 | the coverage list is the card's own and complete | **WEAK** — 8 card items ↔ 8 `CARD_ROWS` keys is bidirectional, but 6 of 15 rows are traceable to nothing in the card, and the 9-behaviour list the check compares against is a script literal |
| A3 | 107 declared / 46 serialised / 61 absent / 31 identical / 15 differ | **HOLDS** — recomputed from `fields`, not the summary; the 15 names match |
| A4 | `BattleModeVSpeedCurve` "identical in all four packages" | **WEAK** — `same_in_all_four` is `true` because all four per-package `values` are `None`; `objects.jsonl` does prove equality (`same: True`), but the check never reads that field |
| A5 | the per-field values printed are the shipped ones | **HOLDS** — 600 cm/s, 0 armour, 500/0.75/1.25/1.0/−0.25/20, 0.8/−0.8/2/0.333, 10, 3000/24000, the four sound ids per package |
| A6 | "`ArmourModeDamageReduction` is 0 … there is no reduction to carry" | **WEAK** — true of that field; `BattleModeImpactMaxDamagePow` (0.5 vs 0.666, package-varying), `…MaxDamageSpeed` 540 and `…MinDamageSpeed` 120 are battle damage modifiers with no row and no omission |
| A7 | "no JC3 member scales top speed by a mode"; "no turning-mode cap exists" | **HOLDS** — 52-type / 1,421-path vocabulary has no `*Mode*` member; the boost block is named |
| A8 | turn-on-the-spot has no data carrier | **HOLDS for the absence, WEAK for the explanation** — 5/5 candidates `separates: false`, 0 tank-only modules, 262 tank-unique in no driving module; "the pivot is native code keyed to the vehicle" is an inference, not a decoded fact |
| A9 | `BattleModeCamFOV` 60 "sits inside the delivered 55–63 band, so no value changes" | **WEAK** — FOV[0]=55 at 5 km/h and FOV[1]=63 at 108 km/h is an interpolation (`FOVVelocityRange`), not a band; 60 is a point on the sweep |
| A10 | the fleet has no battle light behaviour, so the lamps ride `HeadLight` | **HOLDS on the absence, WEAK on the carrier** — 9 behaviours with counts, 0 battle; but T-L17 and T-L20 ship brightness 0.0 and T-L20 is `derived`, while T-MD12 says `decoded` and lights all four |
| A11 | "the launcher is available in both modes (D-7)"; "all weapons on the one car" | **BROKEN** — `T-WP13` is `blocked`: 11 weapons, 2 driver slots, no active-slot index; D-7 is a decision, not a carrier |
| A12 | BmAK ships one car that transforms in place | **HOLDS, evidence uncited** — `Drive_To_Combat` and the 32 `transformation` sequences are decoded, the box grows 3.495→4.691 m; T-15 names no source and the check cannot see it |
| A13 | the counts (15 = 4 + 11; carried 7 / band 1 / omitted 7; next 4 / keep 4 / blocked 2 / out 5) | **HOLDS** — every figure recomputed from the files and the ledger |
| A14 | battle audio is 30 events / 75 WEMs and blocked | **HOLDS** — 30 sources, 75 WEMs summed, `dispo: blocked`, no carrier |
| A15 | `BattleModeCamConfig` is 24 fields read by name, 1000/1000 cm | **HOLDS** — 24 names, 24 values, `MinFreeCameraDistance`/`MaxFreeCameraDistance` = 1000/1000 |
| A16 | the card's hybrid branch is the one that runs | **HOLDS** — D-2 "(b) one hybrid car" in §11, one `hybrid` variant in the table, `B-12: skipped` |

**Bottom line:** T-15 needs two corrections before B-05/B-12 consume it — T-MD9 and T-MD2 must stop
claiming weapon availability (or carry T-WP13's slot limit as the reason the claim fails), and
T-MD11's "inside band" must be re-worded to "the tune's FOV sweep passes through 60". Then record
four smaller things: the battle-lamp brightness 0 rows, the three impact-damage fields, the vacuous
`same_in_all_four` flag, and the six rows the card's own list does not name. Everything else is
record quality; the gate itself is sound and the counting is honest.

---

## A1 · The Done gate is green and reproducible

**The result rests on:** §0.2 step 6 (run the Done check, paste the output) and R11 (generated,
`--check`).

**Test.**

```
$ python Tools/scripts/t11_modes.py --check
PASS: 15 rows | MOD-1 4 / MOD-2 11 | compromises carried 7, inside band 1, omitted 7 | ledger 15/15
EXIT=0

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT=0
```

`cmd_check` re-derives the payload, compares `t11_variants.json` as a dict (`on_disk != payload`),
renders the md and compares it byte-for-byte, then compares every row against `T_ROWS.jsonl` on
four things: presence, `dispo`, non-empty `why`, and `cells`. It also enforces the omitted/carried
rule in both directions (`omitted` must be `out`/`blocked`, and a carried row must not be), plus
the `problems` list from `build_payload`. The rework's tamper table (5/5 caught) is consistent with
that code.

**Verdict: HOLDS.** One caveat, exercised in A11: the ledger cross-check only *reads* the eight ids
the card cites and `T-WP4`; it does not notice that a cited carrier (`T-WP13`) contradicts a row.

---

## A2 · The coverage list is the card's own and complete

**The result rests on:** the rework's fix of review issue 7 ("coverage tested against the script's
own list") — `CARD_ROWS` parsed from the card's `Do:` parenthetical — and the doc's claim that
`--check` "parses the card from `GRAB_BACKLOG.md` and fails when an item is missing here".

**Test.**

```
$ grep -n "CARD_ROWS" -A 9 Tools/scripts/t11_modes.py | head -12
85:CARD_ROWS = {"top speed curve": ["T-MD5"],
86:             "torque": ["T-MD4"],
87:             "steering/pivot": ["T-MD7", "T-MD8"],
88:             "weapons enabled": ["T-MD9"],
89:             "camera tune": ["T-MD11"],
90:             "lights": ["T-MD12"],
91:             "armour reduction": ["T-MD10"],
92:             "audio": ["T-MD14"]}

$ sed -n '660,676p' Tools/scripts/t11_modes.py
        if item not in CARD_ROWS:
            problems.append(f"card item {item!r} has no row mapped in CARD_ROWS")
    for item, rids in CARD_ROWS.items():
        if item not in items:
            problems.append(f"CARD_ROWS maps {item!r}, which the card no longer lists")
        for rid in rids:
            if rid not in {r["id"] for r in rows}:
                problems.append(f"card item {item!r} maps {rid}, which is not a row")
```

The mapping is bidirectional and keyed to a card item **string**, so deleting a card item, renaming
it, or mapping it to a non-existent row all fail. That is a real fix. But two limits remain:

1. **The card names 8 items; the row set has 15 rows.** Six rows answer nothing in the card's
   parenthetical: `T-MD1` (afterburner), `T-MD2` (Immobilizer), `T-MD3` (ram immunity) — they answer
   MOD-1's bullets in §1.6, which the card does not restate — and `T-MD6` (turning cap), `T-MD13`
   (transformation stance), `T-MD15` (the hybrid itself), which answer nothing at all except the
   author's reading of MOD-2. No check asserts that a row is *required* by anything, so a row can be
   invented and still be green (and a row can be deleted as long as it is not in `CARD_ROWS` —
   `T-MD6`, `T-MD13`, `T-MD15` are deletable without failing).
2. **MOD-2's 9 behaviours are still a script literal:**

```
$ sed -n '72,78p' Tools/scripts/t11_modes.py
MOD2_BEHAVIOURS = ["turret weapons", "turn on the spot", "top speed curve", "armour reduction",
                   "battle camera", "battle lights", "steering and drive factors",
                   "battle audio", "transformation stance"]
MOD1_BEHAVIOURS = ["afterburner", "Immobilizer (EMP missile)", "ram immunity",
                   "high speed (standard/boost torque curve)"]
```

`for b in MOD2_BEHAVIOURS: if b not in covered2: problems.append(...)` compares the doc against
this list, not against §1.6's MOD-2 line. Tested in memory (the module is imported, the list
replaced, `build_payload()` called; nothing written):

```
$ python - <<'EOF'   (import t11_modes; drop one behaviour)
after removing 'battle lights' from MOD2_BEHAVIOURS: problems = []
row for battle lights still present: True
EOF
```

So deleting a behaviour from the *check's* list cannot turn the check red — the list is the
authority, and the author wrote it.

**Verdict: WEAK.** The card-facing half is genuinely card-driven; the MOD-facing half is not, and
six rows have no requirement behind them. Recording "rows MD1–MD3 come from §1.6 MOD-1; MD6, MD13,
MD15 are this card's decomposition of MOD-2" would close it in one paragraph.

---

## A3 · The field census: 107 declared, 46 serialised, 61 absent, 31 identical, 15 differ

**The result rests on:** §1's table and §3's opening — "The four packages declare the same 107 mode
fields … 46 of them are serialised and 61 are absent from every package, and of the 46 serialised
only **31 are identical on all four**".

**Test.** Recomputed from `MODES.json`'s `fields`, not its `summary`:

```
$ python - <<'EOF'   (Research/BatmobileGrab/MODES.json)
fields 107
serialized 46   same_in_all_four (of those) 31   differing 15
differing: ['TransformationReverseDirectionIntoPursuitModeSound',
 'TransformationReverseDirectionIntoBattleModeSound', 'BattleModePrimaryWeapon',
 'ImpactRoadAssistSceneryDuration', 'ImpactRoadAssistEnemyDuration', 'BattleDodgeImpulse',
 'ArmourModeDamageReduction', 'BattleModeImpactMaxDamagePow', 'KillFlipTorque',
 'KillFlipTorqueDuration', 'PMDodgeTorque', 'PMDodgeForce', 'PMDodgeDuration',
 'StayUprightConstraintSetup', 'StayUprightConstraintInstance']
EOF
```

The doc's 15-name list is verbatim the same set, and 107 − 46 = 61. `MODES.json`'s own `checks`
block also carries per-family assertions (e.g. "BattleMode*: 42 fields, 15 serialized").

**Verdict: HOLDS.** The doc's own §3 warning — "a number quoted without its package set is only the
value the packages that carry the field agree on" — is exactly right, and §3 prints the per-package
values where they differ (the four sound ids).

---

## A4 · `BattleModeVSpeedCurve` "identical in all four packages = True"

**The result rests on:** T-MD5's source cell, "…identical in all four packages = True", and the
`--check` line `if not m["curve_same"]: problems.append("BattleModeVSpeedCurve is no longer
identical in all four packages")`.

**Test.**

```
$ python - <<'EOF'   (MODES.json, BattleModeVSpeedCurve)
occurrences 4, packages = all four, serialized True
struct.points = [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]]
values = {Funhouse: None, Joker: None, MK2: None, V2: None}
same_in_all_four = True
EOF
```

`same_in_all_four` is computed by `grab_modes.py` line 348 as
`len({json.dumps(v) for _p, v in cooked}) == 1` over the per-package **values** — and for a curve
those values are all `None`, so the flag is `True` because `None == None`. The struct is stored once,
not per package. The doc's printed "= True" therefore cites a vacuous test.

The claim itself is nevertheless true, and the tool has the proof in hand without using it:

```
$ python - <<'EOF'   (t11_modes.sim_curves → objects.jsonl, 4 packages)
BattleModeVSpeedCurve      count=3 packages=4 same=True   points [[0,60],[600,40],[1200,30]]
BoostTorqueVSpeedCurve     count=7 packages=4 same=True
StandardTorqueVSpeedCurve  count=6 packages=4 same=True
packages_read 4
```

`sim_curves()` computes `same` from the four real point lists, and `build_payload` checks it for the
two torque curves (`if not std["same"] or not boost["same"]`) but **not** for the battle curve. Tested
by handing `build_payload` a `sim_curves` in which the battle curve has `same: False` and only three
packages:

```
$ python - <<'EOF'   (import t11_modes; monkeypatch sim_curves)
battle curve same=False, 3 packages -> problems = []
EOF
```

`points` still equals `curve_points` because they are taken from the first package, so a real
divergence in one package would leave the check green.

**Verdict: WEAK.** The claim holds; the evidence line and the assertion are one `same` field away
from being real: print `curves["BattleModeVSpeedCurve"]["same"]` and assert it, exactly as the
torque curves are.

---

## A5 · The per-field values are the shipped ones

**The result rests on:** §2's rows and §3's table — 600 cm/s = 21.6 km/h, armour 0, the six handling
factors, the four turn-on-spot factors, throttle 10, 3000/24000, the four sound ids.

**Test.**

```
$ python - <<'EOF'   (MODES.json, per field)
TurningModeMaxSpeed              600.0 x4
ArmourModeDamageReduction        0 x3 (no Joker key)
BattleModeDriveForceFactor       500.0 x4
BattleModeLatSlipScale           0.75 x4      BattleModeLongSlipScale 1.25 x4
BattleModeSteerAngleFactor       1.0 x4       BattleModeTrailingSteerFactorMoving -0.25 x4
BattleModeDrivingForceZOffset    20.0 x4
TurnOnSpotFrontTorqueFactor      0.8 x4       TurnOnSpotRearTorqueFactor -0.8 x4
TurnOnSpotModeEngineBrakingFactor 2.0 x4      BattleModeTurnOnSpotTorqueFactor 0.33333 x4
BattleModeThrottleSpeed          10.0 x4      TransformationTurnTorqueFactor 3000.0 x4
TransformationTurnDecelTorqueFactor 24000.0 x4
TransformationReverseDirectionIntoPursuitModeSound V2 62, MK2 60, Joker 191, Funhouse 60
TransformationReverseDirectionIntoBattleModeSound  V2 47, MK2 45, Joker 176, Funhouse 45
EOF
```

600 cm/s = 6 m/s = 21.6 km/h ✓. The doc's 0.333333 prints `0.33`? No — the row prints "0.333333",
which is the float's short repr (`0.33333298563957214`) rounded to 6 dp by the generator; harmless.
The sound ids are exactly the per-package values, and the doc's choice to print all four is what
its own §3 rule demands.

One inconsistency **outside** the doc: the §12 row says "`ArmourModeDamageReduction` is 0 in
**every package**", while `MODES.json` has only three keys and the doc correctly says "the three
packages that serialise it" with "no tag in Joker". The §12 summary overstates by one package.

**Verdict: HOLDS** (the §12 wording is a one-line fix).

---

## A6 · "`ArmourModeDamageReduction` is 0 … there is no reduction to carry"

**The result rests on:** T-MD10 — "the shipped value is 0, so there is no reduction to carry" — and
the MODLOG's reading 2: "the requirement assumes battle-mode armour drops, the files say there is no
reduction at all".

**Test.** That is true of the field whose *name* matches the requirement. But the behaviour —
battle mode alters how much damage the car takes or deals on impact — has other serialised fields in
the same 107:

```
$ python - <<'EOF'   (MODES.json, damage-named fields)
ArmourModeDamageReduction        ser=True same=False  unit='int, undocumented scale'  0 / 0 / 0
BattleModeImpactMaxDamageSpeed   ser=True same=True   unit='cm/s'   540.0 x4
BattleModeImpactMinDamageSpeed   ser=True same=True   unit='cm/s'   120.0 x4
BattleModeImpactMaxDamagePow     ser=True same=False unit='factor'  0.5 / 0.666 / 0.5 / 0.5
EOF
```

`BattleModeImpactMaxDamagePow` is even one of the 15 package-varying fields §3 lists — so the doc
knows the name and prints it in §3's list, then never gives it a row, a compromise or a named
omission. Whether an "impact max damage power" is armour reduction or is the damage the Battlemobile
*deals* by ramming is not decidable from `MODES.json`; what is decidable is that a battle-only
damage modifier with a non-zero, package-varying value has no disposition in a row set whose Done
rule is "every MOD-2 behaviour has a row … or a named omission".

The same short search affects the scope claim: 12 of the 15 differing fields (PrimaryWeapon, the two
RoadAssist durations, BattleDodgeImpulse, ImpactMaxDamagePow, the two KillFlip, the three PMDodge,
the two StayUpright) are battle/pursuit-only behaviours with no row and no omission; only 3 of the
15 (the two transformation sounds, the armour int) are placed.

**Verdict: WEAK.** T-MD10 is honest about the field it read; the doc's sentence "there is no
reduction at all" is a fleet-level inference from one member. Either add a "battle-only fields with
no row" list (12 names, one line each) or restrict the sentence to the member.

---

## A7 · No JC3 member scales top speed by a mode

**The result rests on:** T-MD5's carrier cell — "no JC3 member scales top speed by a mode: the engine
curve is torque-vs-rpm (T-E3), the boost is a separate arcade block (T-B2)" — and T-MD6's "no
turning-mode cap exists in the fleet vocabulary (no member, `VOCABULARY.md`)".

**Test.** The vocabulary is the fleet-wide census, not a sample:

```
$ grep -inc "mode" Research/JC3Grab/VOCABULARY.md
6
$ grep -in "mode" Research/JC3Grab/VOCABULARY.md | head
1526:| `lights[].volumetric_mode` | int16 | 0 .. 1 (med 0, n=3217) | 0 |
708:## `HelicopterModel`
…
$ grep -in "max_speed\|top_speed\|extra_top" Research/JC3Grab/VOCABULARY.md | head -4
27:| `aerodynamic_surfaces[].top_speed_drag_coefficient` | float | 0 .. 5 (med 2, n=77) |
59:| `top_speed` | float | 70 .. 70 (med 70, n=41) |
92:| `heat_boost.extra_top_speed` | float | 150 .. 150 (med 150, n=41) |
96:| `nitro_boost.extra_top_speed` | float | 30 .. 30 (med 30, n=41) |
```

None of the six "mode" hits is a mode-gate member (`volumetric_mode` is a light flag; the rest are
class names/prose). The speed members that exist are exactly the ones the row names: the arcade
`*_boost.extra_top_speed` block (T-B2/T-B3) and the engine curve (T-E3). TANKTURN's census (A8)
independently shows 0 tank-only module types across 52.

**Verdict: HOLDS.** This is the strongest kind of negative in the doc: a closed vocabulary searched
in full, with the one adjacent member (`extra_top_speed`) named and routed to its own row rather
than silently ignored.

---

## A8 · Turn-on-the-spot has no data carrier

**The result rests on:** T-MD8 — "none - G2-21: 5 candidates refuted, 52 module types (25 on the
tanks, 0 tank-only), 262 tank-unique values with 0 in a driving module; **the pivot is native code
keyed to the vehicle**" — and the MODLOG's "G2-21 proved the requirement has no data carrier".

**Test.**

```
$ python - <<'EOF'   (Research/JC3Grab/TANKTURN.json)
candidates: [('LandGlobal.number_of_wheels', False), ('LandGlobal.number_of_front_wheels', False),
             ('LandGlobal.is_all_wheel_steered', False), ('LandGlobal.is_rear_steered', False),
             ('LandGlobal.wheels_friction_type', False)]
module_types: fleet 52, tank 25, tank_list 25 names, tank_only []
unique.by_module: {DeformPoints 1, EffectAttachments 37, Fins 14, Propellers 16, WaterInteraction 194}
unique sum 262, driving_module_hits {}
EOF
```

`TANKTURN.md` §2 shows why each candidate fails (the small tank's tuple `(4,-1,0,0,2)` is shared with
23 off-road builds; the 8-wheel tuple with a cargo plane). The absence is measured across all 271
player copies and the tank-specific values are in no driving module.

**Verdict: HOLDS for the absence, WEAK for the explanation.** "The pivot is native code keyed to the
vehicle" is an inference from "no data member", not a decoded fact — no file on disk shows that
code. The omission stands on the measured absence alone; the sentence should read "the pivot needs
a mechanism no data module carries", not a claim about the engine's implementation.

---

## A9 · "`BattleModeCamFOV` 60 sits inside the delivered 55–63 band, so no value changes"

**The result rests on:** T-MD11 — compromise `inside band`, "FOV 60 lies in the tune's 55-63, so no
value changes and only the mode switch is missing" — and the check
`if not (tune["fov_lo"] <= cam["BattleModeCamFOV"] <= tune["fov_hi"]): problems.append(...)`.

**Test.** What the tune actually holds:

```
$ python - <<'EOF'   (Working/Camera/CAM_TUNE.json)
FOV[0]: old 30.0 -> new 55.0  readback 55.0
FOV[1]: old 55.0 -> new 63.0  readback 63.0
CameraPosition[1] (up):  1.3   CameraPosition[2] (back): 7.0
readback 8/8 ok
EOF

$ sed -n '127,128p' Working/Translation/T6_HUD_CAMERA.md
| T-CAM2 | `DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10 | `FOV [30,55]` over `FOVVelocityRange [5,50]` | UE3 horizontal → JC3 vertical (16:9) | 30…55° v | `FOV [55,63]` v; …
| T-CAM3 | `DrivingCamFOVInterpMaxSpeed` 3000 cm/s | `FOVVelocityRange` | 3000 cm/s = 108 km/h | 5…50 km/h | `[5,108]` | decoded | FOV stops changing at 108 |

$ grep -n "FOVVelocityRange" -A 2 Tools/scripts/bmak_camfile.py
    dict(member="FOVVelocityRange", index=1, row="T-CAM3", old=50.0, new=108.0),
```

The `.ctune` field is `FOV` **paired with** `FOVVelocityRange`: the camera's FOV interpolates from
`FOV[0]` (55°) at 5 km/h to `FOV[1]` (63°) at 108 km/h. It is a two-point speed curve, not a
permitted range. So:

* "FOV 60 lies in the band" is true only in the trivial sense that 60 is between two numbers; the
  camera never *holds* 60 for long — it passes through it. There is no setting to "carry".
* The conclusion the row needs — *no edit is required* — is still correct, and for a stronger
  reason: the drive camera is already narrower than the battle value at low speed and wider at high
  speed, so BmAK's fixed battle FOV has no single JC3 counterpart at all.

**Verdict: WEAK** (reason, not outcome). Re-word T-MD11 to "the delivered tune sweeps 55°→63° with
speed (`FOV`/`FOVVelocityRange`); a fixed 60 has no member, and a hybrid cannot switch framing
anyway", and label the compromise `omitted`/`inside band` with that sentence rather than a "band".
Note this also means the check's inequality is testing a reading, not a fact in the file.

---

## A10 · The fleet has no battle light behaviour, so the lamps ride `HeadLight`

**The result rests on:** T-MD12 — "the fleet's light vocabulary is 9 behaviours (…) with 0 battle
value, so T-18 maps the battle lamps onto `HeadLight`: T-L17, T-L18, T-L19, T-L20" — and the check
`if li["battle_behaviour"]: problems.append(...)` / `len(li["battle_rows"]) != 4`.

**Test 1 — the vocabulary is closed and has no battle value:**

```
$ python - <<'EOF'   (LIGHT_SYSTEM.json → module.behaviors)
HeadLight 1027, LeftSignal 253, None 1177, Reverse 191, RightSignal 253,
SirenLightOffOnFast 3, SirenLightOn 9, SirenLightOnOffFast 3, TailLight 301
battle-ish: []
```

Nine behaviours with fleet counts — `LIGHT_SYSTEM.md` labels the column "entries" out of the 3,217
`VehicleDynamicLights` entries — zero battle. This is a strong absence, and it is the same list
T-18's `t14_lights.json → behaviour_vocabulary` carries.

**Test 2 — what the four carrier rows actually are:**

```
$ python - <<'EOF'   (t14_lights.json, the four VEHLT_BattleModeLight rows)
T-L17  BattleModeSpotLight  brightness 0.0  colour 255,255,255  (white)
T-L18  HeadLight1           brightness 5.0  colour 255,0,0      (red)
T-L19  HeadLight2           brightness 5.0  colour 255,0,0      (red)
T-L20  LWheelLight          brightness 0.0  colour 255,0,0      (red)

$ grep -n "T-L20" Working/Translation/T14_LIGHTS.md
| `T-L20` | `LWheelLight` → HeadLight | custom `sportsmuscle_wheel_f_l_arch_battle` (preset 0) | … | LightColor 255,0,0,0 B 0.0 … | derived · Q-1 #7: the arch lamp turns red in battle mode
```

So **two of the four lamps ship at brightness 0.0** (they are dark in the donor), and T-L20 is a
custom, preset-0 entry that T-18 labels **derived**, not decoded. T-MD12 says `decoded` and "the
battle lamps come on with the lights" — i.e. the JC3 build will light two lamps BmAK ships dark, and
one lamp whose entry does not exist in the donor's graph. That is the R5 shape: a member named
`VEHLT_BattleModeLight` read as "a lamp that lights in battle mode".

**Verdict: HOLDS on the absence** (nothing else could carry it), **WEAK on the carrier claim.** The
row should read: "4 donor entries map to `HeadLight`; 2 ship at brightness 0 (T-L17 white, T-L20
red) and T-L20 is custom/derived, so the delivered car lights two lamps the donor keeps dark —
Q-1 #7 must be read with that expectation, and the confidence is `derived`, not `decoded`."

---

## A11 · "The launcher is available in both modes (D-7)"; "all weapons on the one car"

**The result rests on:** two rows and their variant-table cells:

* T-MD2 (Immobilizer): "the launcher is available in both modes (D-7), the disable is not carried",
  pursuit "the launcher, no disable", battle "the same launcher, no disable";
* T-MD9 (turret weapons): "carried: all weapons on the one car, no mode gate", with disposition
  `next` and confidence `decoded`.

**Test.** D-7 is a **decision**, not a carrier:

```
$ grep -n "| D-7 |" GRAB_BACKLOG.md
| D-7 | Weapon slots: which BmAK weapons take JC3's driver slots (cannon, Vulcan, missiles…) | G2-11 | **resolved 2026-10-28 (user): every BmAK weapon in both battle and pursuit modes** — no per-mode split; the slot count must carry all weapons (T-11 finds how, e.g. extra driver slots or mode-independent switching) | T-11 |
```

"the slot count must carry all weapons (T-11 finds how)" is an instruction to T-11. T-11's answer is
in the same ledger T-15 is checked against:

```
$ python - <<'EOF'   (T_ROWS.jsonl)
T-WP13 -> blocked | D-7 asks for all 11 weapons in both modes, and the fleet has 2 driver slots at most
                     with no active-slot index, no next/p…
T-WP4  -> blocked | the EMP missile can be a `w618` clone plus G2-16's entity-level CForcePulse copy,
                     but JC3 has no disable/duration memb…
T-WP5  -> blocked | the EMP burst is an entity-level CForcePulse copy (G2-16) - the object can be built,
                     but nothing in the decoded files …
EOF
```

`T-WP13` is exactly the row that says the hybrid cannot carry all weapons: 11 classes, 2 slots, no
active-slot index, no next/previous-weapon action. T-15's own table cites the mechanics (`w618`
missile clone, `w602` cannon, the tank's pair) and never cites `T-WP13`; the check asserts
`T-WP4` is blocked but never asserts anything about `T-WP13`, so the contradiction is invisible to
`--check`. And `w618` is the donor's *ordinary* missile (T-WP3), so calling it "the launcher" for the
EMP is the same name-matching T-WP4 itself refuses.

Two precise failures follow:

* **T-MD9's "carried"** is false as written: the mode gate is indeed absent, but "all weapons on the
  one car" is a capability whose owner is `blocked`. Its §12/§5 text should say "no mode gate
  (carried); the 11-weapon count is T-WP13's blocked slot problem, not this row's".
* **T-MD2's reason** ("the launcher is available in both modes") is unsupported for the same reason,
  and the carrier named is a non-EMP missile. The row's own `blocked` disposition is right; only the
  explanation is wrong.

**Verdict: BROKEN** for the availability claim in T-MD2/T-MD9 (evidence: `T-WP13 blocked`), while the
dispositions themselves (T-MD2 `blocked`, T-MD9 `next`) are defensible once the text stops asserting
the capability.

---

## A12 · BmAK ships one car that transforms between pursuit and battle in place

**The result rests on:** T-MD15 — "BmAK ships one car that transforms between pursuit and battle in
place", `carried`, confidence `decoded` — the row on which the whole hybrid rests, and T-MD13's "the
stationary pose is T-12's part angles … no JC3 anim node drives a transformation".

**Test.** The transformation is decoded elsewhere — and T-15 cites none of it:

```
$ grep -n "Drive_To_Combat\|transformation" Research/BatmobileGrab/ANIMATIONS.md | head -4
74:| `transformation` | 32 | 2136 | 1768 | Drive_To_Combat, Batmobile_V2_Tank_Spread_Close, … |
84:| Batmobile | `BM_Batmobile_Chassis` | `Drive_To_Combat` | 61 | 2.000 | 30.00 | 75 | `transformation` | 0 |

$ sed -n '/## G1-12 · Pose deltas — done/,/^## G1-13/p' MODLOG.md | head -14
**Canonical pair:** `Batmobile_V2_Tank_Spread_Open_Game` frame 0 (pursuit) and frame 60 (battle, 1.967 s).
… The full box grows 3.495 x 2.341 x 7.026 -> 4.691 x 2.865 x 7.443 m.
**Measured:** turret `Turret_Top` rises 0.633 m … the chassis settles 0.050 m …
```

So "one car, transforms, in place" is supported: the `_Game` pair is the gameplay transition
(1.967 s), the turret rises 0.633 m, and the box grows 0.34 m in height. The `decoded` label is fair.

**Verdict: HOLDS, evidence uncited.** The claim has no source cell in the row, and `--check` cannot
see the animation files, so nothing would notice if it were false. Cite `POSES.json` / G1-12 (and
`ANIMATIONS.md`'s 32 `transformation` sequences) in T-MD15 and T-MD13's "the pose is reachable".

---

## A13 · The counts

**The result rests on:** "15 rows — MOD-1 4, MOD-2 11", "`carried` 7, `inside band` 1, `omitted` 7",
"`next` 4, `keep` 4, `blocked` 2, `out` 5", the rework's "ledger 198 rows", and `STATUS.md`'s
`| T-15 | 15 | 8 | 0 | 2 | 5 | 0 | 4 | 0 |`.

**Test.**

```
$ python - <<'EOF'   (T_ROWS.jsonl, STATUS.md)
total 198
T-MD rows 15
dispo Counter({'out': 5, 'next': 4, 'keep': 4, 'blocked': 2})
{T-MD1 next, T-MD2 blocked, T-MD3 keep, T-MD4 keep, T-MD5 out, T-MD6 out, T-MD7 out,
 T-MD8 out, T-MD9 next, T-MD10 keep, T-MD11 keep, T-MD12 next, T-MD13 out, T-MD14 blocked,
 T-MD15 next}
global Counter({'keep': 60, 'next': 40, 'out': 36, 'epe': 26, 'edit': 16, 'blocked': 13, 'superseded': 7})
$ grep -n "| T-15 |" STATUS.md
31:| T-15 | 15 | 8 | 0 | 2 | 5 | 0 | 4 | 0 |
```

15 = 4 + 11 ✓; compromises 7 + 1 + 7 = 15 ✓; dispositions 4 + 4 + 2 + 5 = 15 ✓; the global ledger
totals (60+40+36+26+16+13+7 = 198) ✓. The `STATUS.md` line's columns are the audit's own.

**Verdict: HOLDS** (every figure, including the reworked 8→7 / 6→7 that the §12 row records).

---

## A14 · Battle audio is 30 events / 75 WEMs and blocked

**The result rests on:** T-MD14 — "T-16 row W-08 is `blocked`: the donor carries no mode-switch
event and a hybrid has no second variant to hang a battle bank on" — and the variant table's
"`Play_BattleMode_In/Out*` 30 events / 75 WEMs".

**Test.**

```
$ python - <<'EOF'   (t12_audio_map.json, W-08)
event sources 30
sum wems 75
statuses {'no-media', 'resolved'}
groups ['battle-mode']
carrier "no event on the donor (battle mode would be a second variant, D-2)"
dispo blocked
EOF
```

30 sources, 75 WEMs summed, all in group `battle-mode`, `dispo: blocked` with no chosen slot. Note
the two statuses: some events are `no-media` (named but no sample decoded), so "75 WEMs" counts
declared WEMs, not measured media — the doc says "30 events / 75 WEMs" without that nuance, which
is T-16's record to qualify.

**Verdict: HOLDS.**

---

## A15 · `BattleModeCamConfig` is 24 fields read by name

**The result rests on:** §3 — "`BattleModeCamConfig` carries 24 fields including
`MinFreeCameraDistance`/`MaxFreeCameraDistance` 1000/1000 cm, looked up by name".

**Test.**

```
$ python - <<'EOF'   (CAMERA.json → configs.BattleModeCamConfig)
keys ['fields', 'values']; 24 fields, 24 values
StateFreeCameraSitOffsetMin [-350,0,200] … MinFreeCameraDistance 1000.0
MaxFreeCameraDistance 1000.0 … MaxCameraSmoothingAngle 10.0
(other configs: DrivingCamConfig, BoostingCamConfig, BattleModeWinchCamConfig, … 13 in all)
EOF
```

24 / 24, the two named fields at index 9 and 10 with 1000.0 each, and the name-keyed lookup is real
(`cfg_idx = {n: i for i, n in enumerate(cfg_names)}`). The class-level `MinFreeCameraDistance` 164 /
`MaxFreeCameraDistance` 200 in the same file are a *different* pair (free-camera limits), and the doc
does not confuse them.

**Verdict: HOLDS.** The row's honest limit — "the spring/distance fields have no unit bridge
(T-CAM9 blocked)" — is exactly the right treatment of the rest of the struct.

---

## A16 · The card's hybrid branch is the one that runs

**The result rests on:** "D-2 is resolved: (b) one hybrid car. The card's hybrid branch is the one
that runs … so there is no per-variant table to build", and the variant table's
`{"id": "hybrid", "rows": 15, "entities": 1, "drop_entries": 1, "mode_switch": null,
"B-12": "skipped: D-2", "B-13": "ships the single entry"}`.

**Test.**

```
$ grep -n "| D-2 |" GRAB_BACKLOG.md
| D-2 | Pursuit/Battle: (a) two Rebel Drop entries, (b) one hybrid car, (c) research a runtime toggle first | … | **resolved 2026-10-28 (user): (b) one hybrid car** — a single Rebel Drop entry carrying both modes; … (B-12 `skipped: D-2`) | MOD-2, T-15, B-12 |
$ grep -n "#### B-12" -A 4 GRAB_BACKLOG.md
#### B-12 · Variants (only if D-2 = two variants)   S · deps: B-05…B-11, T-15 · serves: MOD-1/2
```

The card is explicitly conditional on D-2, the decision names T-15, and B-12 is skipped, so building
a two-variant table would have been wrong. The 15 rows with one declared compromise each is the
hybrid branch.

**Verdict: HOLDS.** The one consequence worth stating in the doc: because B-12 is skipped, the
`pursuit`/`battle` columns in `t11_variants.json` are a *record*, not an input to any build — the doc
says "so B-12 can be built later", which overstates (B-12 is skipped, not deferred), though it costs
nothing.

---

## What this challenge did not test

- **Anything in-game.** R6 forbids a launch before phase V exits; every `verify` cell is a §9b/Q
  probe that has not been run — including the one that would settle A10's brightness-0 lamps
  (Q-1 #7).
- **Whether the five battle-mode steering factors would actually produce BmAK's battle handling**
  (T-MD7 `out`): the values are recorded but no JC3 member exists, so there is nothing to test.
- **`BattleModePrimaryWeapon`, the `RoadAssist`, `KillFlip`, `PMDodge` and `StayUpright` fields**
  (A6's long tail): 12 package-varying mode fields with no row; their semantics are not decoded
  anywhere on disk, so a row would be `class`, not `decoded`.
- **The `.ctune`'s `FOV` interpolation law** (A9): that the FOV moves linearly in speed between
  `FOVVelocityRange[0..1]` is CAM-1/T-CAM2's reading; T-15 inherits it without re-checking the
  ADF layout.

## Reproduce

```
python Tools/scripts/t11_modes.py --check          # A1: PASS, exit 0
python Tools/scripts/t_rows.py check               # A1/A13: 198 rows, check ok
python Tools/scripts/status_audit.py --check       # A1: STATUS.md is current
```

The heredocs above are read-only; the two probes that import `t11_modes` call only `sim_curves()`
and read the same records the generator reads, and add no files.

Nothing in the repo, `Builds/`, `E:/Modding/JustCause3/_grab`, `E:/Modding/ArkhamKnight/_grab` or `D:/Games` was
written, and no process was launched.
