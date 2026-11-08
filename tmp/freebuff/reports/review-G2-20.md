# Review — G2-20 · Exit, bail-out and eject

Reviewer: independent (did not write the card). Read-only pass: `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/` and `Tools/` were only read; nothing outside this file was written, no game launched,
no git.

Scope checked: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-20 card (§6, line 691) and its §12 row
(line 1303); `MODLOG.md` §"G2-20 · Exit, bail-out and eject — done" (line 11849);
`Research/JC3Grab/EJECT.md` (327 lines), `Research/JC3Grab/EJECT.json`,
`Tools/scripts/jc3eject.py` (733 lines), plus `Research/JC3Grab/README.md` lines 772 / 940.

## VERDICT

**Minor issues.**

The extraction is sound and the numbers are real. I re-derived the headline fleet figures
independently from `E:/Modding/_JC3grab/detail` and every one matched exactly (4,832 exits in
232 graphs, 61 names, the 9-key member set, `enabled` 1 and `interaction` `00000000` on all
4,832, 4,057 `CInteractionGraphParentVelocityCondition`, 104 graph classes, 221
`exit.driver.moving.parachute` with the 125/35/23/19/19 class split), and the donor's
`turbo_jump` values and the 19 BmAK eject properties with their offsets are exactly as tabled.
The card's Done clause is met in the body (exit → `exit.driver.moving.parachute` stated;
launch → *none/UNKNOWN* with Q1-EJ-A), the UNKNOWNs are real, and R5 is handled better than in
most cards — "up" is explicitly labelled a property name, not a measured trajectory.

It is not clean, though: the headline and the §12 row state as fact an exit *selection* the
doc's own §3 calls UNKNOWN; the §3 justification for that UNKNOWN is factually wrong (the two
fast exits are not condition-symmetric — the parachute exit carries an extra
`ExitObstructedCondition`); two of the most-quoted facts in the §12 row (`enabled` 1,
`interaction` `00000000`) are hardcoded prose that `--check` never derives; and one §6 claim is
refuted by the doc's own table. None of these inverts a conclusion or hides a gap, so: fix the
wording, not the work.

## Check output (verbatim)

Command run from `E:/Modding/JC3-Batmobile`:

```
$ python Tools/scripts/jc3eject.py --check
PASS: 4832 exits in 232 graphs (61 names) | donor 26 exits, 7 speed-gated, 5 unconditional | launch members: exits 0, graph classes 2, vehicle modules 1 | BmAK eject props 19, json match True, md match True
```

Exit status `0`. Identical to the summary pasted in `MODLOG.md` line 11849 and to the row quoted
in `Research/JC3Grab/G2X.md` line 41 (gate run).

Out paths from the card and row — all present:

| path | state |
|---|---|
| `Research/JC3Grab/EJECT.md` (card's only declared Out) | exists, 327 lines, header digest `8dca980204969198` = `EJECT.json` `digest` |
| `Research/JC3Grab/EJECT.json` | exists, keys `card/donor/fleet/launch/donor_jump/bmak/counts/digest` |
| `Tools/scripts/jc3eject.py` | exists, `--write`/`--check`/`dump` |
| `Research/JC3Grab/README.md` §"Exit, bail-out and eject (`EJECT.md`, G2-20)" + Files row | present (lines 772, 940) |
| `GRAB_BACKLOG.md` §12 row `G2-20 \| done \| …` | present (line 1303) |
| `MODLOG.md` §"G2-20 … — done" | present (line 11849) |

## Issues

### 1. (R4) The headline and the §12 row state the exit *selection* as fact, while §3 says it is UNKNOWN — `Research/JC3Grab/EJECT.md:10`, `GRAB_BACKLOG.md:1303`, `MODLOG.md:11849`

`EJECT.md` line 10 reads "Exiting above the speed gate **selects** `exit.driver.moving.parachute`
→ `S_EXIT_VEHICLE_PARA`". The data does not say that: `roll.out` and `moving.parachute` both sit
at gate 5..999 and the document itself says at line 114 "which one wins is not in the data —
UNKNOWN, probe Q1-EJ-B". The §12 evidence row repeats the stronger form ("so `S_EXIT_VEHICLE_PARA`
is *the fast exit*", "the two fast exits share a gate so the winner is code" — the two halves of
that sentence contradict each other). Why it matters: this is the one sentence a phase-T reader
will lift into MOD-3, and it converts a Q-1 probe result into a settled carrier. The honest form
is the one §8 already uses. Fix: "exiting above the gate offers the two fast exits
(`roll.out`, `moving.parachute`); the parachute state is the one MOD-3 wants, and selection is
UNKNOWN (Q1-EJ-B)".

### 2. (data) "Both high-speed exits have the same gate and no other condition" is false — `Research/JC3Grab/EJECT.md:112`

Verified from the donor `.epe` XML and from `EJECT.json`: `exit.driver.roll.out` has exactly one
child (`CInteractionGraphParentVelocityCondition` 5..999); `exit.driver.moving.parachute` has two
(`…ParentVelocityCondition` 5..999 **and** `CInteractionGraphExitObstructedCondition`, check 0,
`id:A3CC001A` = `S_EXIT_VEHICLE_PARA`). The document's own §2 table shows this, and
`EJECT.json` `donor.exits[…].condition_classes` for the parachute exit is
`["CInteractionGraphParentVelocityCondition", "CInteractionGraphExitObstructedCondition"]`. So the
stated basis for Q1-EJ-B (perfect symmetry) is wrong — the parachute exit has an obstruction path
the roll-out does not. The conclusion ("selection is code") may still be right; the sentence that
supports it is not. This is a claim the data refutes, not an UNKNOWN.

### 3. (R11) Facts quoted as the card's evidence are typed literals in the renderer, not derived — `Tools/scripts/jc3eject.py:report()` (lines ~418–430)

`--check` only diffs the regenerated text against disk, so anything the renderer hardcodes is
permanently "green". Hardcoded in the generated doc:

* `EJECT.md:27` "`enabled` | `1` on all 4832; `0` never appears" — `build()`'s `counts` has no
  `enabled` check. `fleet()` does collect per-name `enabled` counters, and `EJECT.json` carries
  them, but nothing asserts them, so a fleet-wide `enabled: "0"` would not change the PASS line.
* `EJECT.md:28` "`interaction` … `00000000` (null) on all 4832" — `interaction` is not aggregated
  anywhere; this value is pure prose.
* `EJECT.md:29` "`disable_event` / `enable_event` … empty on every donor exit" — typed; the donor
  rows in `donor_exit_rows()` do not keep those values.
* `EJECT.md:46` "the 142 state machines it does carry are character-side" and line 45
  "0 `jc_statemachine/vehicles/` files" — typed; the script never reads `INDEX.jsonl`. (The 142
  does have prior provenance: `Research/JC3Grab/SEAT.md:13` from G2-19. My own `INDEX.jsonl` scan
  finds 0 `jc_statemachine/vehicles/` rows — correct — but 152 rows whose path contains
  `statemachine`, so the 142 figure cannot be reproduced without G2-19's exact filter.)
* Also typed: "## 2. The donor's **26** exits" (line 50), "Those **five** are entered from code"
  (line 92), "splits at **5**" (line 98), and "0 launch members in **4,832** exits, 0 in **232**
  module graphs" in the §7 table (line 278).

I re-ran all of these independently against the raw data and **all of them are correct**
(`enabled` = 1 ×4832, `interaction` = `00000000` ×4832, events empty ×26, 0 vehicle state-machine
files). So this is an R11 gap, not a wrong number: two of the four claims the §12 row leads with
are not re-derivable by the command the row names. Cheapest fix: fold `enabled`/`interaction`
counters and the state-machine counts into `build()["counts"]` and print them from the values.

### 4. (R4/data) "An exit in this game is a state name plus a set of gates" over-generalises — `Research/JC3Grab/EJECT.md:7`, `:27`

23 of the 4,832 exits carry **no** `state` value; all 23 are `exit.stunt_to_reel` (the
helicopter-only exit §4 lists). `EJECT.json` `fleet.exit_keys` shows it plainly: `state: 4809`,
`modifier: 1399` against `4832` for the other seven keys. The document presents the 9-key set as if
every key is populated on every exit and never mentions the 23 state-less ones or which exit they
belong to. Minor, but it is exactly the kind of "the table says every" claim the tracker then
quotes. Also loose in the same sentence: "the only numbers any exit carries are the gates" — every
exit also carries `name_hash` (`-624301289` for `exit.driver.default`), `enabled` 1 and
`interaction` 0.

### 5. (data) "the same string" in `ExitObstructedCondition` is true for 3 of 4 donor cases — `Research/JC3Grab/EJECT.md:43`

The doc generalises from `moving.parachute` ("as the exit's own `state`, and inside its
`ExitObstructedCondition` (the same string, under the hashed key `id:A3CC001A`)"). Counted from
the XML: 4 exits have an `ExitObstructedCondition`; 3 hold their own state string;
`exit.driver.to.fall` holds **`S_EXIT_VEHICLE`**, not `S_EXIT_VEHICLE_TO_FALL`. That matters a
little because `to.fall` is one of the four exits §3 reasons about, and the substitution is
itself a data point (an obstructed fall-out degrades to the plain exit). ROOT cause is simply that
the sentence generalises a single observation; no fix beyond a qualifier.

### 6. (R5, self-contradiction) "the only numeric eject property on the vehicle" — `Research/JC3Grab/EJECT.md:261`

The claim is refuted by the doc's own §6 table three lines above it: `MaxEjectType` is a
`ByteProperty` and `GetOutOnTopOnSteepInclinePitch` an `IntProperty` (offset `0x2170`), both on
`RVehicleBatmobile`. Verified in `EJECT.json.bmak.properties` (`kind` values include
`BoolProperty, ByteProperty, FloatProperty, IntProperty, ObjectProperty, StructProperty`). What is
true and worth keeping is "the only float *distance*" — narrow the sentence to that.

### 7. (R4 phrasing) "JC3 has no eject." — `Research/JC3Grab/EJECT.md:7`

The evidence supports "no entity or graph data in the grab authors an upward launch"; the flat
sentence is a statement about the engine, which §8 (items 1–3) and `MODLOG.md:12056` both concede
is native code / UNKNOWN. The body is careful; the first line of the document is not. Reword to
"JC3's data authors no eject".

### 8. (R14) The "verbatim" `--write` block in MODLOG is not verbatim — `MODLOG.md:11886`–`11889`

The pasted line is `wrote E:\Modding\JC3-Batmobile\Research\JC3Grab\EJECT.md (327 lines) +
E:\Modding\JC3grab\EJECT.json` — the second path is missing `JC3-Batmobile\Research\`. The session
noticed and appended a correction immediately below, so the record is honest, but a "verbatim"
block that needed a correction is an R14 wrinkle (the summary line after it is accurate and
matches my run).

### Note (not a defect): what `--check` does and does not prove for the card's Done clause

Card Done: "a stated mapping for BmAK ejection (launch → glide) or UNKNOWN (→ Q-1 probe)".
`--check` proves the md/json are byte-identical to a fresh re-derivation from the raw data; it
proves nothing about the mapping sentence, which is a literal in `report()` (lines ~505–521). The
Done clause is satisfied **only by reading the prose**, and it is satisfied in the body (§7 table:
exit → stated, launch → `none`, glide → carrier named / behaviour UNKNOWN → Q1-EJ-C). That is the
same shape as the other G2 readers, so I record it rather than fault it — but a reviewer should
not read "PASS" as "the mapping is proven". The `EJECT.json` is an extra output beyond the card's
Out path; it is what makes the doc's tables re-derivable (R11), so it belongs.

## Spot-checks

All three were re-derived with an independent script over the same raw inputs, not by re-reading
`EJECT.json`.

| # | value in `EJECT.md` | where verified |
|---|---|---|
| 1 | "`CInteractionGraphExit` objects: **4832** in 232 graphs, 61 distinct names, 26 in the donor" (line 19–20); "a set of **9** keys" listing `_object_id, disable_event, enable_event, enabled, interaction, modifier, name, name_hash, state` (line 21–25); `enabled` 1 and `interaction` `00000000` on all (lines 27–28) | Independent walk of all 232 `E:/Modding/_JC3grab/detail/*.ee.json`: **4832 / 232 / 61**, key union exactly those 9, `enabled {'1': 4832}`, `interaction {'00000000': 4832}`. Matches `EJECT.json` `counts` (`fleet_exits 4832`, `fleet_graphs 232`, `fleet_names 61`) and `fleet.exit_keys`. |
| 2 | "`CInteractionGraphParentVelocityCondition` has **4057** instances" (line 37–38), "graph vocabulary is **104** classes" (line 35), and "`exit.driver.moving.parachute` … on **221** of the 232 vehicles, 125 cars / 35 boats / 23 helis / 19 jets / 19 bikes" (lines 44–46, table row line 131) | Same independent walk: `ParentVelocityCondition 4057`, `classes 104`, `para 221` with roots `{CCar 125, CBoat 35, CHelicopter 23, CMotorBike 19, CAirPlane 19}` (sum 221). Matches `EJECT.json.fleet.names` and `counts.graph_classes_with_launch_name 2`. |
| 3 | The donor jump table (lines 197–216): `punch_speed_kph` 50 / 80, `top_speed_kph` 200, `f_multiplier` 15 / `r_multiplier` 12, `top_speed_jump_multiplier` 2, upgraded 30 / 25, `punch_delay_time` 0.1, `turbo_jump_cooldown` 5 / `…_upgraded` 2, `high_up_in_air_height` 10, gravity multipliers 1 | Re-read from `E:/Modding/_JC3grab/entities/v0300_car_kensington_sportsmuscle__…_civilian_01.ee.json` module rows: every value identical (`punch_delay_time` raw `0.100000001`, printed as `0.1` by `:g` — correct). Also confirmed `TrainGlobal.crashing_impulse` ×12 and the "145 land vehicles / 232 cooldown" figures (145 files carry `CustomLandGlobal.arcade.turbo_jump.punch_speed_kph`; 232 carry `VehicleMisc.turbo_jump_cooldown`). |
| 4 (bonus) | Donor gates: `default` 0..5, `to.fall` 0..5, `roll.out` 5..999, `moving.parachute` 5..999; `S_EXIT_VEHICLE_PARA` count 2 in the donor `.epe`; 19 BmAK eject properties at `0x0340 … 0x1790` | Parsed `Research/Epe/serpente_civilian.xml` directly (gates and condition children as tabled; the `id:A3CC001A` state appears exactly twice). Parsed `Research/BatmobileGrab/BMSDK_OFFSETS.json`: 19 members, offsets `832/1120/1124/1312/8384…8560/4576/5604/5902/6032` = `0x0340/0x0460/0x0464/0x0520/0x20c0…0x2170/0x11e0/0x15e4/0x170e/0x1790`, matching the §6 table exactly. |

## Tamper test

Not re-run (the card's tamper was already journaled at `MODLOG.md:11896` and re-running it would
mean writing `Research/`, which this review may not do). What the journal records is consistent
with the script: `--check` compares both files textually and exits 1 naming the stale one.

## Limits of this review

I did not re-derive the G2-18 geometry columns (§2 `parent`/`Serpente`/`Batmobile`/`verdict`),
which `jc3eject.py` imports from `INTERACTION.json` rather than computing — those belong to G2-18
and were reviewed there. I did not read BmAK asset payloads, and the two claims that depend on
them (`Eject` package, `Eject_To_Spot` config) are typed into the doc; both do check out against
`Research/BatmobileGrab/ASSETS.md` lines 260/346, but the script does not verify them.
