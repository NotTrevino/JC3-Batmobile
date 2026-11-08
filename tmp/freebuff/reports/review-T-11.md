# Independent review — T-11 · Weapons translation

Reviewer role: independent, read-only. Nothing under `Tools/`, `Research/`, `Working/`,
`GRAB_BACKLOG.md` or `MODLOG.md` was modified; the only file written is this report. Date 2026-10-29.

Read: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–79), §7 card T-11 (lines 863–876), §12 row
`| T-11 | done |` (line 1320); `MODLOG.md` §"T-11 · Weapons translation — done" (lines 13157–13279)
and §"T-11 fix · D-3 toggle withdrawn — done" (lines 13827–13897); outputs
`Working/Translation/T7_WEAPONS.md` (496 lines), `Working/Translation/t7_weapons_edits.json`,
`Tools/scripts/t7_weapons.py` (1,424 lines); inputs `Research/BatmobileGrab/WEAPONS.json`,
`SOCKETS_JC3.json`, `HUD_INTERFACES.json`, `Research/JC3Grab/WEAPONS.jsonl`, `WEAPON_WIRING.jsonl`,
`JC3_HUD_WEAPONS.json`, `DAMAGE_MODEL.json`, `FORCEPULSE.md`, `TETHER.md`, `FOOTAGE.md`.

## VERDICT: minor issues

The analysis is real and re-derivable: 14 ledger rows (12 WPN + the D-7 and D-3 decisions), 136
aspects each carrying an R4 class, 3 numeric edits whose `old` values the script re-reads out of
`WEAPONS.jsonl`, 6 structural items, 6 withdrawn values, and 53 UNKNOWNs. `--check` is green, the
ledger and `STATUS.md` are consistent, and every spot-check I ran matched the data.

It is not "sound" because the document contains **two claims its own input files refute**, and the
card's third `Done:` clause is **unmet for 10 of 14 rows and not checked by anything**:

1. `T7_WEAPONS.md:68` and `:413` say the medium tank is "the only land vehicle with two driver
   weapons"/"with 2" slots. The Bavarium tank binds the identical pair (v0202).
2. `T7_WEAPONS.md:106` and `:484` say the BmAK `InaccuracyVsTime` points are "not decoded".
   G1-23 (`Research/BatmobileGrab/FOOTAGE.md:107,129`) decodes them, and `T7_WEAPONS.md:145` in
   the same file quotes those exact points.
3. `Done:` "every row's verify cell names a Q-3 check from §9 with a numeric pass" holds for 4 rows
   (T-WP1/2/3/12) and fails for 10; `t7_weapons.py` only asserts the cell is non-empty.

None of the 14 dispositions, the 3 edits or any build value changes because of these; the doc needs
a correction pass, not a re-derivation.

## Check output (verbatim)

```
$ python Tools/scripts/t7_weapons.py --check
PASS: 14 rows = 12 WPN codes + 2 decision rows (5 with a JC3 carrier, 6 named omissions, 3 blocked) | 136 aspects classified, 53 UNKNOWN | 3 edits + 6 structural + 6 withdrawn | 4 JC3 ids, 2 driver slots | ledger 14/14 | json match True, md match True
exit 0
```

The other two commands the done section records:

```
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
exit 0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
exit 0
```

(The ledger is 198 rows now, not the 183 of the T-11 done section; other cards have written since.
The 14 `T-7` rows are still present and still agree with the doc — `ledger 14/14` in the PASS.)

## Out paths and Done criterion

| card requirement | state |
|---|---|
| `Out:` `Working/Translation/T7_WEAPONS.md` | exists, 496 lines; byte-compared by `--check` |
| `Out:` rows (doc `T-7`) | 14 rows in `T_ROWS.jsonl`, dispositions match (`--check` compares each) |
| `Out:` `Working/Translation/t7_weapons_edits.json` | exists; shape `{_comment, source, card, edits, structural, not_numeric, counts}`, i.e. `t1_edits.json` plus `structural`/`card`/`counts` — the card asked for "same shape as `t5*_edits.json`", which is satisfied |
| §12 row `Tools/scripts/t7_weapons.py --check` | exists, exit 0 |

| card `Done:` clause | verified by | result |
|---|---|---|
| every WPN code has rows or a named omission | `invariants()` loops WPN-1…WPN-12 and both decisions (`t7_weapons.py:1268-1275`) | met |
| every value cell has a class | every aspect carries `class` ∈ `CLASSES` (`:1289-1293`) | met (see issue 4 for the class vocabulary) |
| every row's verify cell names a Q-3 check from §9 with a numeric pass | only "cell is non-empty" (`:1285-1286`) | **not met** — 4 rows have it (T-WP1/2/3/12), 10 do not (issue 1) |

## Issues

**1. Done clause 3 is unmet for 10 of 14 rows, and nothing checks it (`GRAB_BACKLOG.md:875-876`;
`t7_weapons.py:1285-1286`; cells at `T7_WEAPONS.md:130,166,197,226,254,270,286,302,318,334,359,389,416,443`).**
The verify cells are:

- Q-3 #3 with a numeric pass: T-WP1, T-WP2, T-WP3 (`3/3`); T-WP12 has "Q-1 #5 / Q-3 #3 … pass = 2 slots".
- T-WP11: "Q-2 A9: 0-100 with and without boost" — a different Q set and no pass number.
- "none" / "none yet" / "none until": T-WP4, T-WP5, T-WP6, T-WP7, T-WP8, T-WP9, T-WP10,
  T-WP13, T-WP14.

§7 rule 5 also requires every row to end with "a file check (V phase), a screenshot gate, or a Q-take
with a numeric pass"; "none: nothing to fire" is none of the three. The underlying reason is
legitimate (an absence row has nothing to fire), but the deviation is nowhere recorded — not in the
doc, not in the §12 row, not in the MODLOG — and `--check` cannot see it. This is the same class of
gap T-10 handled explicitly ("its own card's to prove"). Fix: for the out/blocked rows render a file
check ("proof re-read by this script: `Research/JC3Grab/TETHER.md`"), or state the deviation in the doc
and the MODLOG as T-10 did.

**2. "The medium tank is the only land vehicle with two driver weapons" is false, and the doc
contradicts itself two paragraphs earlier (`T7_WEAPONS.md:68`, `:413`; typed at
`t7_weapons.py:743,1150`).** `Research/JC3Grab/WEAPON_WIRING.jsonl` gives the Bavarium tank
(`v0202_car_capstone_bavariumtank_military_01.ee`) exactly the same binding as the medium tank:
`main_weapon` → `w602_mediumtank_canon`, `secondary (id:00568A74)` → `w603_mediumtank_mgun`. 24 of
the 53 armed entities have `counts.driver_slots == 2`, including both tanks (and the helicopters,
jets and the cargo plane). The doc's own §2 D-7 row (`:66`) says "medium and Bavarium tank:
`main_weapon` + `id:00568A74`", so `:68` and `:413` are refuted by the same file. The decision does
not change — two tanks make the precedent stronger — but the sentence must not survive into a doc
T-12/T-14 will cite, and nothing in `--check` would ever catch it: the numbers are literals in the
renderer, not reads.

**3. "`InaccuracyVsTime` points are not decoded" is false in the project's own record
(`T7_WEAPONS.md:106`, `:484`; `t7_weapons.py:266,1220`).** `Research/BatmobileGrab/FOOTAGE.md:107`
(G1-23) has the decoded curve — "4 points, 0.0->0.0, 0.5->0.0, 1.5->1.5, 2.5->3.0" — and `:129`
marks gap F-2 **RESOLVED / FILE-VALUE** with the same four points. `T7_WEAPONS.md:145` (T-WP2) even
quotes them: "`InaccuracyVsTime` 0/0.5/1.5/2.5 s -> 0/0/1.5/3.0 (G1-23)". So the UNKNOWN class on
T-WP1's `spread curve` aspect and §6 item 6 rest on a premise the project already disproved. The
accurate statement is narrower and still true: the points are not in `WEAPONS.json` (the field is
`None`, `Points` `None`), they are decoded in G1-23's FOOTAGE.md F-2 — which also means the fit is
blocked by the unit/`scatter` bridge, not by missing points.

**4. R4 class vocabulary: `UNKNOWN` is used for "not applicable", and the doc misquotes R4's list
(`T7_WEAPONS.md:7`; `t7_weapons.py:50`; R4 at `GRAB_BACKLOG.md:66`).** 27 of the 53 UNKNOWN aspects
have `-` on both the JC3 and the transform side — e.g. T-WP6/7/8/9/10 `slot` ("no JC3 slot can carry
it") and `weapon point` ("-"), T-WP12 `projectile speed`/`blast`/`effects`, and ten of T-WP13's
twelve rows. Those are "this quantity does not exist", not "the files do not say", and they inflate
the headline "53 UNKNOWN" that the MODLOG presents as "the parts of a weapon that do not cross".
Separately, the doc says "Classes are R4's (`decoded`, `decoded (fleet)`, `derived`, `class`,
`read`, `UNKNOWN`)", but R4's own list is `decoded`, `decoded (fleet)`, `derived`, `class`, `epe`,
`read` — no `UNKNOWN`, and the script's `CLASSES` drops `epe`. Worth aligning the wording before
another card copies the list.

**5. Field counts are class aggregates presented as object properties (`T7_WEAPONS.md:76-77`;
`t7_weapons.py` WPN-1/WPN-2 row builders).** "`RBatmobileHeavyCannon` `Batmobile_Heavy_Cannon_Primary`
(4 packages, 165 fields)": in `WEAPONS.json` that object name exists in **3** packages
(Funhouse, MK2, SF) with **41** fields each; 4 and 165 are the `RBatmobileHeavyCannon` class totals
(4 instances incl. `Batmobile_JokerHeavy_Cannon`, 165 fields over all of them). T-WP2's
"(5 instances, 280 fields)" is the same class-level read (5 = four `Batmobile_Cannon_V2` + one
`Batmobile_JokerCannon_V2`; the object itself has 67 fields), but at least it is labelled
"instances". Both numbers are typed into the row builder. A builder reading "41 fields" would get
the right object; "165" is the class.

**6. R11 — many numbers in the prose are literals, not derivations (`t7_weapons.py`, whole row
builders).** Correct as far as I checked (see Spot-checks), but not re-derived, so a change in the
source data would leave them stale: "175 decoded tune rows" (w602's `_flat` length), "7 carriers",
"blast 1500 in **8 m**" (a hard-coded 8 next to the derived radius), "`max_health` 36000" and
"24:2 = 12x", "232 `.epe` graphs", "65 placed" sockets, "4 of the fleet's 25" ("25" typed, though
`len(J.rows)` is 25), and T-WP13's "5 fire points across the two carriers" — 5 is `w602`(1) +
`w618`(4); the row's own slot aspect names `w602` and `w603` (1 + 1 = 2), so "the two carriers" is
undecidable as written. The summary table (`rows`, aspects by class, edits/structural/withdrawn,
gadget classes, ids used, driver slots) *is* derived, which is what R11 mainly asks for.

**7. R5-style name inference, mild (two places).** T-WP3 marks `spread curve` `decoded (fleet)` and
says "keep unguided: the donor's missile is `autoaim_vehicle_no_lockon_missile`" — the conclusion is
also supported by `missile_turning_speed` 0 (`WEAPONS.md:192,442`), so the number carries it, but the
sentence leads with a preset *name*. T-WP2's "barrel spin | `GatlingGun` part behaviour driven by
`weapon_rpm`" is a part-type name plus a member, and the row's own note concedes "there is no JC3
spin-speed member: the rate is code". Neither is the T-10 `VEHLT_BattleModeLight` mistake (a donor
enum sold as a behaviour), but both should say which part is data and which is code.

**8. §12 row wording (`GRAB_BACKLOG.md:1320`): "D-7 has no carrier for 11 weapons".** Read literally
that says none of the 11 has a carrier, which contradicts T-WP13 (2 of 11 have a slot). The MODLOG
phrase "no mechanism carries 11 weapons" is the accurate one. Cosmetic, but the tracker line is what
T-23 will read.

**Not an issue, but a reconciliation a reader must do:** the T-11 done section's verbatim PASS says
"5 with a JC3 carrier, **5** named omissions, **4** blocked", while the current PASS (and the §12 row)
says 5 / **6** / **3**. The T-11 fix block (`MODLOG.md:13827-13897`) explains it — T-WP14 moved
`blocked` → `out` when D-3 was withdrawn, aspect totals unchanged (136 / 53) — and the §12 row was
updated there. Both files are consistent once the later block is read; nothing is hidden.

## Spot-checks (value → where verified)

| value in `T7_WEAPONS.md` | verified at |
|---|---|
| "`Health` 1200 / `Damage` 50 = **24 shell hits**" and "a shell kills a stock tank in 2 hits (H0/H2) / 3 (H1)" | `Research/BatmobileGrab/WEAPONS.json` `Batmobile_Heavy_Cannon_Primary_Projectile` `Projectile.Damage` = 50.0; `Research/JC3Grab/DAMAGE_MODEL.json` `arm_targets.bmak_ratio.health` = 1200, `.heavy_cannon_hits` = 24 (1200/50 = 24 ✓), `table.medium_tank.tank_cannon.primary` H0/H2 = 2, H1 = 3 ✓ |
| "`LaunchRotationOffset` [-3640, 0, 0] = -20 deg" and "`LaunchSocketName` = `BattleModeSpotLight`" (T-WP4) | `WEAPONS.json` `Batmobile_EMP_Missile_Launcher` `RPursuitModeMissileLauncher.LaunchRotationOffset` = [-3640, 0, 0] → 3640 × 360 / 65536 = 19.9956 → 20 ✓; `LaunchSocketName` = `BattleModeSpotLight` ✓ |
| "175 decoded tune rows" / "7 carriers" for `w602_mediumtank_canon` | `Research/JC3Grab/WEAPONS.jsonl`: `entities` = 7 ✓; the script's own `_flat()` filter yields 175 non-empty member rows for w602 (179 raw rows, 4 dropped) ✓ |
| "53 armed entities", "max 2 driver slots" | `WEAPON_WIRING.jsonl`: 53 rows ✓, `max(counts.driver_slots)` = 2 ✓ — and the same file lists the Bavarium tank among the 2-slot entities (issue 2) |
| "132 member names on `w609_fighterjet_missile_air_lockon`, of which 0 contain 'lock'" | `t7_weapons.py` `autoaim_members()`/`autoaim_lock_members()` on the loaded jsonl: 132 and `[]` ✓ |
| "307 pulses … 14 of the fleet's 307 … have no owner pointer" | `Research/JC3Grab/FORCEPULSE.md:4` "307 pulses in 232 vehicle `.ee` files", `:7` "293 of 307" (307 − 293 = 14) ✓ |
| "blast 1500 in 8 m", "`impulse` 0 on the direct hit" (w602); "`damage` 190 direct, vehicle factor 0.3", "`impulse` 60 per hit" (w603) | `WEAPONS.jsonl` flat members: w602 `PlayerDamage` 1500, `PlayerDamageRadius` 8, `…base_tuning.impulse` 0; w603 `damage` 190, `vehicle_damage_factor` 0.3, `impulse` 60 ✓ |
| "`RiotSuppressorLockOnAngle` 7.5, `RiotSuppressorFiringInterval` 0.75", "`FiringInterval` 0.138 … the combo interval is the same value" | `WEAPONS.json` `Batmobile_Cannon_V2`: 7.5, 0.75, `RVehicleWeapon.FiringInterval` 0.1379999965, `RBatmobileCannon.ComboFiringInterval` 0.1379999965 ✓ |

## Limits of this review

- Read-only: no output, script, ledger, research or game file was modified; no game launched; nothing
  committed. The three tamper tests recorded in the MODLOG were not re-run by mutating files (that
  needs write access to `Working/` and `Tools/`); `--check`'s md/json equality and the ledger
  disposition comparison are structural in `cmd_check()`, so their failure modes are credible.
- Numbers that live only in prose were checked by hand against the json (above); I did not audit all
  136 aspects. The UNKNOWN-vs-`-` count (27 of 53) is computed from the live `build()`.
- The 183-row ledger in the done section is historical; the live numbers quoted here are as of
  today's 198-row ledger.
