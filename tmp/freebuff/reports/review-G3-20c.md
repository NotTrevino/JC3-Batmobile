# review-G3-20c - spot-check of the G3-20c ledger pass

STATUS: done

## VERDICT

**ACCEPT WITH CORRECTIONS.**

The arithmetic and the citations hold; the QUOTED/OPEN boundary does not.

* **Counts exact.** 93 rows in scope, **68 OPEN / 25 QUOTED**, and the split per document is
  T-20 19 (0 QUOTED), T-3 17 (9), T-7 14 (3), T-15 15 (6), T-14 28 (7). Recomputed
  independently from `Working/Translation/LEDGER_G3C.json`; the pass's own `--check` passes
  (exit 0).
* **Citations 10 of 10 exact.** Every cited `file:line` I opened exists and carries the value
  the pass quotes, including the numbers quoted as *different* from the ledger's. No fabricated
  line, no paraphrased value, no off-by-one.
* **But 4 of the 10 sampled QUOTED rows are adjacency, not answers** (T-L8, T-L15, T-L18,
  T-WP6). The card decodes a *neighbouring* member or object that shares a name token; the
  pass quotes it, admits in prose it is "a different member on a different object", and still
  files the row QUOTED. Under the pass's own definition ("a named card decodes the member this
  row is about") those four are OPEN/adjacent.
* **And 3 of the 5 sampled OPEN rows are already answered on disk** (T-ST7, T-L24, T-MD9) by
  cards the pass did not search: `MECHANICS.md`, `LIGHTS.md`, `TURRET.md` / `WEAPON_WIRING.md`.
  Their `supplier` field sends a successor to re-decode data that already exists.
* **Two relation labels are wrong** for their row: T-AU5 `differs` (there is no member/value
  pair - the card refutes an absence claim) and T-WP6 `agrees` (there is no shared value at
  all).
* **Structural note: the brief's "at least two from each group" is unachievable for T-20** -
  that group has **0 QUOTED rows of 19**. The sample therefore covers the four groups that have
  QUOTED rows, with 3 + 3 + 2 + 2.

Nothing here is a claim about Batman: Arkham Knight, Unreal Engine 3 or JC3 behaviour. Every
line below is a file + line I opened in this session.

## What was checked

* **Ten QUOTED rows** (3 x T-3, 3 x T-14, 2 x T-7, 2 x T-15), each: open the cited card at the
  cited line, compare the quoted text and every quoted number, then ask whether that line
  answers the row's own BmAK source members or JC3 target - not merely whether it mentions the
  same word.
* **Five OPEN rows** (one each from T-20, T-3, T-7, T-14, T-15): search
  `Research/BatmobileGrab/` and `Research/JC3Grab/` for the row's subject and see whether any
  existing card already supplies it. Cards outside the pass's eleven named cards count here,
  because the brief asks whether "no existing card" answers the row.
* Rows, cards and statuses were read from `Working/Translation/LEDGER_G3C.md` (911 lines),
  `Working/Translation/LEDGER_G3C.json`, the row text in `Working/Translation/T_ROWS.jsonl`
  (lines 89-99, 123-133, 156-161, 184-197) and `tmp/freebuff/reports/G3-20c.md`.

## The ten QUOTED rows

Legend - **PASS**: the quote is at the cited line and answers the row's own member/target.
**FAIL**: the quote is at the cited line but the row is about a different member or object, so
QUOTED overstates what the card proves.

| # | row (doc) | cited line | what that line actually says | does it answer the row's BmAK source / JC3 target? | verdict |
|---|---|---|---|---|---|
| 1 | `T-K4` (T-3) | `CLASS_DEFAULTS.md:183`, `:184` | `EbrakeTime` (RVehicleBatmobileBase) FloatProperty **1.0**; `EBrakeBrakeForce` **160000.0** - section 4, `BmGame.Default__RVehicleBatmobileBase`, BmGame.upk export 10923 | **Yes.** Same two member names the row cites (0.75 / 640000), on the base CDO, so `differs` is correct. `MECHANICS.md:64-69` independently carries 0.75 / 640000 as offset-only archetype floats, which supports the pass's "not the archetype the row reads" | **PASS** |
| 2 | `T-EF1` (T-3) | `CLASS_DEFAULTS.md:164`, `:165` | `SquealThreshold` (SVehicle) **0.5**; `SquealLatThreshold` (SVehicle) **0.5** | **Yes.** The row's two members (0.2 / 0.2), second reading on the subclass default, `differs` correct | **PASS** |
| 3 | `T-AU5` (T-3) | `AUDIO_BANKS.md:200` (also `:164`, `:168`, `:170`) | "**10 claimed / 90 event rows -> 10 found, 0 confirmed absent.**"; "**29** distinct `package.bank` references over **361** event rows"; `BML_Batmobile` 2268588 B / 53 events; `BML_Battlemode` 830548 B / 7 events | **Yes, and it is the pass's strongest finding.** The row's premise ("10 BmAK banks are absent from the install") is refuted by the card's own re-test. No keyword match: same 10 banks, same 29 references | **PASS** (relation `differs` is the wrong enum - see corrections) |
| 4 | `T-L8` (T-14) | `CLASS_DEFAULTS.md:263` + `SKINS.md:879` | `HeadLightsColourPursuit` raw `0000803f...` = 4 floats [1.0, 1.0, 1.0, 1.0]; `HeadLight1` socket bone `Winch_DOOR_Mesh` (SKINS section 5, `playable`, 65 sockets = baseline) | **No.** The row is the per-entry lamp: `LightColor 138,197,246,255`, `B 0.15`, cone `20.0/70.0`, `R 6000.0`. The card's member is the car-level pursuit colour struct - a different object, and the pass says so itself ("a different member on a different object, so it is not contradicted"). The socket line is adjacent geometry, not the row's value | **FAIL** - adjacency filed as QUOTED |
| 5 | `T-L15` (T-14) | `CLASS_DEFAULTS.md:122` | `BrakeLightsLensFlare` (RVehicleBatmobileBase) ObjectProperty = `Batmobile.Batmobile_brakelights` (LensFlare) | **No.** A LensFlare object is not the brake lamp's colour, intensity or range; the row is `BrakeLightL` -> `Sport_Muscle_Rear_Break_Left` with `LightColor 255,38,0,0 B 1.0 R 150.0`. Nothing decodes that flare's colour, so "the object behind the row's brake colour" is an unverified link. This is the "BrakeLight" token matching, not the member | **FAIL** - keyword match |
| 6 | `T-L18` (T-14) | `CLASS_DEFAULTS.md:264` | `HeadLightsColourBattle` raw `0000c841...` = 4 floats [25.0, 0.0, 0.0, 1.0] | **No.** The row is the battle-mode `HeadLight1` entry: `LightColor 255,0,0,0 B 5.0 cone 10/35 R 1024`. The card is the car-level colour struct, a different member, and the card itself marks the struct "layout not decoded" - so the pass's "intensity above 1" is interpretation, not a read value | **FAIL** - neighbour member, and one interpretation on top |
| 7 | `T-WP6` (T-7) | `REMAINDER.md:1209`, `:1210` | exports 5268/5269 `RSimpleRopeComponent` `RopeComponent0` 44/46 and `RopeComponent1` 52/54, both "terminator" (no property read) | **No.** The row's BmAK source is `RBatmobileWinch` with `FireEffect`, `ImpactEffect`, `FireSound`, `ImpactSound` and 14 more fields. The card decodes two component *objects* and no member of them; the pass admits "they carry no pull parameter". `agrees` claims a shared value that does not exist | **FAIL** - object count only, not the row's members |
| 8 | `T-WP11` (T-7) | `REMAINDER.md:1211` (through `:1220`) | export 5290 `SkeletalMeshComponent` `GadgetMesh` 28/42, `terminator_early`; `:1212-:1220` give nine more, so "ten `GadgetMesh`" is correct | **Partly.** It confirms the gadget is a skeletal-mesh component with no boost fields, which is the row's "mesh only" reading on the geometry side. It does **not** decode `RBatmobileBooster`'s 8 fields, so "the booster class carries no boost member" still rests outside this card. Weakest pass in the sample | **PASS** (with the caveat) |
| 9 | `T-MD1` (T-15) | `CLASS_DEFAULTS.md:265` + `:192` | `FakeExtraSpeedMax` (RVehicleBatmobileBase) **3500.0**; `SideExhaustBurstEffect` = `Exhaust.Batmobile_Side_Exhaust` (ParticleSystem) | **Yes** as boost-side inputs - the row is the afterburner -> `arcade.nitro_boost` MOD record and both quoted values are boost members. Note the pass did not cite the literal afterburner members that are in the same card (`AfterburnerSystem`, `AfterburnerWarmupSystem`, `:186`, `:187`), so the "the afterburner's own members" wording is inference where a direct citation existed | **PASS** (better citations available) |
| 10 | `T-MD14` (T-15) | `CLASS_DEFAULTS.md:199` | `Transform_In_Bed` (RVehicleBatmobileBase) ObjectProperty = `Ww_BML_Batmobile.Play_BattleMode_In_Bed` (AkEvent) | **No - and that is correct here.** The row's `TransformationReverseDirectionIntoPursuitModeSound` / `...IntoBattleModeSound` names are not class defaults; the card gives four *different* transform events. `different-member` is exactly the right relation and the prose says so. Honest adjacency, correctly labelled | **PASS** |

**Tally: 6 PASS, 4 FAIL.** Every one of the 10 quotes is textually correct. The failures are
classification failures, not citation failures.

## The five OPEN rows

| # | row (doc) | the pass's reason | what an existing card already says | verdict on OPEN |
|---|---|---|---|---|
| 1 | `T-ST7` (T-3) - `SteerSpeed` 220 deg/s, steer-curve knots | "the only steering-rate member in the two class-default streams is `DriftCorrectionSteerSpeed` 1.0 ... `SteerSpeed` and `SteerSpeedVsSpeedCurve` are not class defaults", supplier "the archetype `RVehicleSimBatmobile` tag stream (`objects.jsonl` / `CHAIN.json`)" | `Research/BatmobileGrab/MECHANICS.md:65`: `SteerSpeed` `0x0DC` **220** FloatProperty `SVehicleSimCar`; `MECHANICS.md:108` `SteerSpeedVsSpeedCurve` `0x194` **2 curve points**; `MECHANICS.md:254`: `SteerSpeedVsSpeedCurve = 0.0 -> 220.0  3500.0 -> 20.0`. The row's BmAK numbers are already decoded there | **Wrong.** The class-default half is true, but the supplier is not needed - the decode exists. Should cite `MECHANICS.md` and stay adjacent, not open |
| 2 | `T-L24` (T-14) - `Dashboard_Light` -> `Dash_Light` (row 2) | "no `Dash_Light` or dashboard-light member exists in either class-default stream, and no named card decodes the JC3 preset", supplier "the donor module's row 2" | `Research/BatmobileGrab/LIGHTS.md:68`: `Dashboard_Light` `Batmobile_Chassis` `VEHLT_Interior` `VEHLTMAT_Interior` behaviour `TailLight`; `LIGHTS.md:301` (Playable_Batmobile_SF row): `[172, 245, 255, 0]`, intensity `5.0`, radius `80.0`, cone `20.0 / 45.0` - **exactly the values in the row**. JC3 side: `Research/JC3Grab/ENTITIES.md:215` (`Dash_Light`, colour 1,0.9765,0.9176, angle 60) and `LIGHT_SYSTEM.md:122` (`Dash_Light` x221) | **Wrong.** Both halves are decoded by existing cards |
| 3 | `T-MD9` (T-15) - turret weapons | "no named card decodes the turret parts or the weapon clones" | `Research/JC3Grab/TURRET.md:9-39`: a JC3 turret is a `Turret` yaw part + `Cannon` pitch part, each one `hkpLimitedHingeConstraintData`, with pivots, axes, limits and the fire point naming both parts; `:146-153` for the APC. `WEAPON_WIRING.md:26-31` and `:329` bind the weapons to those parts and name the two driver slots | **Wrong** as written: the turret/aim half is decoded on disk, in a card, with limits |
| 4 | `T-WP13` (T-7) - driver weapon slots | "no named card decodes driver slots or weapon groups", supplier `WEAPON_WIRING.md` / G2-11 | `Research/JC3Grab/WEAPON_WIRING.md:31`: "the only slot data in the game files is these two root pointers ... there is no active-slot index, no next/previous weapon action and no weapon group anywhere in the `.epe`"; `:26-27` two slots max across 53 armed entities; `JC3_HUD_WEAPONS.md:180` two HUD slots | **Holds in substance, wrong in form.** The row really is blocked, and the card that proves it is the supplier the pass names - so this should be `confirms-open` citing `WEAPON_WIRING.md:31`, not "no named card decodes it" |
| 5 | `T-WLD4` (T-20) - display name `443190071`, 0 of 11 languages | "the store's container is decoded; the missing half is a writer, and no card provides one", citing `DECODE_DEPTH.md:28` (`.stringlookup` 1 / 2210 / FULL) | `Research/JC3Grab/NAMES.md:9-10` (profile/online.stringlookup is the only store; the entity's own holds prompts only), `:110` (45/45 resolution), `:132` (rename = add a pair, a recipe); `challenge`/`specs` B-13 agree "no writer". No card supplies a writer | **Holds.** Correct OPEN with a correct negative |

**Tally: 1 holds (T-WLD4), 1 holds in substance but mislabelled (T-WP13), 3 are answered on disk
(T-ST7, T-L24, T-MD9).**

## Corrections for a successor

1. Demote `T-L8`, `T-L9`, `T-L15`, `T-L16`, `T-L18`, `T-L19` from QUOTED to OPEN/adjacent. Their
   cards decode car-level colour structs and brake/tail **flare objects**, not the per-entry
   lamp members the rows carry (`LightColor`, intensity, cone, range). `T-L17` (the
   `PSMLightTemplate` spotlight spawner) is a genuinely related carrier and can stay.
2. Demote `T-WP6` and `T-WP7` to OPEN. `RopeComponent0/1` and `DroneHackerEffect0..5` are
   component *objects* with the property list terminated at byte 36-52; they carry no
   `RBatmobileWinch` / `RBatmobileAllegianceSwitcher` member and no reference to
   `Particles.DroneHacker_Beam` (`REMAINDER.md:1202`, `:1207`, `:1209`, `:1210`). The pass's
   `agrees` relation for T-WP6 asserts a shared value that does not exist.
3. Fix two relation values: `T-AU5` `differs` -> `supplies` (or `n/a`; it is an absence claim,
   not a member number), and `T-WP6` `agrees` -> none, since the row goes back to OPEN.
4. Re-point three suppliers at cards that already hold the answer: `T-ST7` ->
   `Research/BatmobileGrab/MECHANICS.md:65`, `:108`, `:254`; `T-L24` ->
   `Research/BatmobileGrab/LIGHTS.md:68`, `:301` plus `Research/JC3Grab/ENTITIES.md:215`;
   `T-MD9` -> `Research/JC3Grab/TURRET.md:9-39` with `WEAPON_WIRING.md:26-31`.
5. Re-label `T-WP13` `confirms-open` with `Research/JC3Grab/WEAPON_WIRING.md:31`.
6. `T-FX6`'s prose "every member the row lists is decoded ... The row's list is complete for
   these" overreaches: the row also lists a bare `ExhaustBurstEffect` and "wheel particles".
   `CLASS_DEFAULTS.md` has only `SideExhaustBurstEffect` / `SideExhaustBoostEffect`
   (`:192`, `:193`) and no wheel particle member (only the `Wheels` array at `:160`). The eight
   cited members are real; the completeness claim is not. (Not in my ten - noted because I
   opened the lines for the `ExhaustBurstEffect` token.)
7. `T-MD1` should cite the literal afterburner members in the same card instead of, or as well
   as, `FakeExtraSpeedMax`: `AfterburnerSystem` `CLASS_DEFAULTS.md:186`,
   `AfterburnerWarmupSystem` `:187`.

## Files written

- `tmp/freebuff/reports/review-G3-20c.md` - this file.

Nothing else was created, edited or deleted. `Working/Translation/LEDGER_G3C.md`,
`LEDGER_G3C.json`, `Tools/scripts/ledger_g3c.py`, `tmp/freebuff/reports/G3-20c.md` and every
`Research/` card were read only. No game file was touched, nothing was installed, no process was
run or attached, no commit, no network write.

## Commands run, verbatim

Recomputing the counts from the pass's own JSON (independent of its `--check`):

```
$ python - <<'PY'
import json, collections
d=json.load(open('Working/Translation/LEDGER_G3C.json',encoding='utf-8'))
rows=d['rows']
print('rows',len(rows))
by=collections.Counter(r['status'] for r in rows)
print('status',dict(by))
per=collections.Counter((r['doc'],r['status']) for r in rows)
print('per-doc',sorted(per.items()))
q=collections.defaultdict(list)
for r in rows:
    if r['status']=='QUOTED': q[r['doc']].append(r['id'])
for k in sorted(q): print(k,len(q[k]),q[k])
PY
rows 93
status {'OPEN': 68, 'QUOTED': 25}
per-doc [(('T-14', 'OPEN'), 21), (('T-14', 'QUOTED'), 7), (('T-15', 'OPEN'), 9), (('T-15', 'QUOTED'), 6), (('T-20', 'OPEN'), 19), (('T-3', 'OPEN'), 8), (('T-3', 'QUOTED'), 9), (('T-7', 'OPEN'), 11), (('T-7', 'QUOTED'), 3)]
T-14 7 ['T-L8', 'T-L9', 'T-L15', 'T-L16', 'T-L17', 'T-L18', 'T-L19']
T-15 6 ['T-MD1', 'T-MD3', 'T-MD10', 'T-MD12', 'T-MD13', 'T-MD14']
T-3 9 ['T-K4', 'T-EF1', 'T-DM7', 'T-FX6', 'T-AU5', 'T-BM1', 'T-RA1', 'T-SR1', 'T-PA9']
T-7 3 ['T-WP6', 'T-WP7', 'T-WP11']
count exit=0
```

The pass's own oracle, unchanged:

```
$ python Tools/scripts/ledger_g3c.py --check
check OK: 93 rows in scope, 97 citations re-read from the source lines, 29 absent-claims re-tested, 7 cards cited, 4 unused
  OPEN    68
  QUOTED  25
check exit=0
```

The quote checks were done by opening each cited file at the cited offset, not by grep alone:
`CLASS_DEFAULTS.md` 100-139, 144-177, 155-209; `REMAINDER.md` 1199-1220, 1778, 1848;
`AUDIO_BANKS.md` 155-204; `SKINS.md` 840-883; `DECODE_DEPTH.md` 15-69; `T_ROWS.jsonl` 89-99,
123-133, 156-161, 184-197. Line numbers were confirmed against `^## ` section headers (section 3
= `BmScript.Default__RVehicleBatmobile`, Startup.upk export 7530; section 4 =
`BmGame.Default__RVehicleBatmobileBase`, BmGame.upk export 10923), which is why `:183`/`:184`
and `:164`/`:165` are on different objects, as the pass says.

## UNKNOWNs

1. **Whether the four FAIL rows should be OPEN/adjacent or stay QUOTED is a labelling judgement,
   not a fact about the bytes.** The quoted text and numbers are correct; what is unproven is
   that the card's member is the row's member. A successor needs a rule, not another read.
2. **Whether `FakeExtraSpeedMax` is an afterburner member.** The base CDO carries both it
   (`:265`) and `AfterburnerSystem` / `AfterburnerWarmupSystem` (`:186`, `:187`); no card links
   the additive-speed value to the booster function. Tried: `CLASS_DEFAULTS.md` section 4 tag
   list and `REMAINDER.md` for `RBatmobileBooster` fields. It would be settled by decoding
   `RBatmobileBooster`'s 8 fields (REMAINDER section 3a) or by a drive.
3. **Whether `HeadLightsColourBattle` [25.0, 0.0, 0.0, 1.0] is RGBA or intensity-scaled RGB.**
   The card marks the struct "layout not decoded", so the pass's "intensity above 1" is not
   evidence, and neither is mine. Would be found in `RDeferred_SpotLight_Shadowed_Spawnable`'s
   property names, not in these bytes.
4. **The other 15 QUOTED rows and 63 OPEN rows were not sampled.** In particular `T-DM7`,
   `T-RA1`, `T-SR1`, `T-PA9`, `T-BM1` (T-3), `T-L9`, `T-L16`, `T-L17`, `T-L19` (T-14),
   `T-WP7` (T-7), `T-MD3`, `T-MD10`, `T-MD12`, `T-MD13` (T-15) were left unopened. Their line
   numbers are covered by `--check`'s substring test; their *relevance* is not.
5. **T-20 has no QUOTED rows at all**, so no T-20 quote could be tested and the brief's "two
   from each group" could not be met. If the pass intended T-20 to quote something
   (`DECODE_DEPTH.md` is cited there only as a negative), that is a gap in the pass, not in this
   check.
6. **Whether the archetype that carries `EbrakeTime` 0.75 / `EBrakeBrakeForce` 640000 is "the
   four-car archetype"** as `T-K4`'s prose asserts: `MECHANICS.md:64-69` shows those two floats
   as offset-only on the archetype objects, unnamed, so the object is supported but the
   four-car attribution is the pass's inference.
