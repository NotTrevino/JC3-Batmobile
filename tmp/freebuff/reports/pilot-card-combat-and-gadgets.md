# Q-PILOT step 7 — combat and gadget cards for phase Q-3

Lane 8014, 2026-11-07. **Revised in place the same day by `review-pilot-cards`** (§10 lists every
change). Eleven cards: cannon, Vulcan, lock-on missiles, EMP, riot mode, mode switch,
afterburner, sonar, winch, hacker, tracker. Card shape is `Working/Q/PILOT/CARD_FORMAT.md` §1–§3
unchanged. Bands come from `Working/Q/PREDICTIONS_COMBAT.md` (K-1…K-11), from the T-WP carrier rows
(`Working/Translation/T7_WEAPONS.md`) and from the build gates in `Working/Translation/BUILD_BATCHES.md`
(B-15, B-18…B-21). Bindings come from `Working/Q/PILOT/CONTROLS.md` only; a row marked `UNKNOWN`
there stays `UNKNOWN` here and carries a discovery step instead of a key.

**The test ban stands.** Nothing in this file launches or installs; these are cards for a later
session after the R6 review.

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one document: the Q-3 combat/gadget cards (Q-PILOT step 7) |
| file | `tmp/freebuff/reports/pilot-card-combat-and-gadgets.md` (this file) |
| why this file | the brief names it; a report, so no game input changes |
| reverted by | deleting this file. No other file was written |

## 1. What t7 actually says, and the three promises this file refuses

`python Tools/scripts/t7_weapons.py --check`, run for this document:

```
PASS: 15 rows = 13 WPN codes + 2 decision rows (13 with a JC3 carrier, 1 named omissions, 1 blocked)
      | 164 aspects classified, 46 UNKNOWN | 3 edits + 6 structural + 6 withdrawn
      | 4 JC3 ids, 2 driver slots | ledger 14/14 | json match True, md match True
```

So: **13 carrier rows, 1 named omission, 1 blocked** (`T-WP13`, the weapon-switch mechanism). Review
8299's corrections are carried exactly:

| the refusal | why |
|---|---|
| **no 2.0 s held lock** | K-11: `MissileLockOnDuration` 2.0 s is BmAK's; the build has **no lock-duration member at all**, the 7 capture files' 233 samples never exceed 1 s, and the only lock-shaped HUD fact is the POI 21 reticle's 1.5 s rotation. K-11 is `UNKNOWN` for the build, so a card may not band 2.0 s |
| **no 8-target salvo** | no card rows it. `T_WP13` (slot/switch) is **blocked**; `T-WP3` gives **4 fire points** on the donor. The "8-target" figure comes from a `t_blocked` mis-citation of **B-24/B-25**, which are the handling and lens-flare batch cards (`BUILD_BATCHES.md`, `apply-keep-audit-fixes-*.md`), not weapons |
| **riot is B-15's round, not a non-lethal weapon** | T-WP10: `base_tuning.damage` = 0, impulse kept, `RiotSuppressorFiringInterval` **0.75 s**, and the toggle is a **second weapon entity** (no per-weapon mode member). D-3 accepted JC3 lethality; riot is a zero-damage impulse round |

**B-15 has three meanings in this repo** — the budget card (`GRAB_BACKLOG.md:1955`, `done`), a
proposed HUD step (`BUILD_BATCHES.md:234`), and the riot build card `Research/specs/B-15.md` that
`T-WP10` cites. A combat card means the third, and §4.5 says so.

Gadget ownership, as the brief gives it: **EMP disable = B-18** (T-WP15 has no value until the probe
runs), **hacker = B-19**, **sonar = B-20**, **tracker = B-21**, **riot = B-15**. A card whose batch
has not landed writes `BLOCKED`, not `FAIL`.

## 2. The instrument, and the one thing it cannot count

From step 6 (`tmp/freebuff/reports/pilot-card-driving-takes.md` §2): `qa1_hud.py` decodes the **HUD
speedometer only**, 5 fps, ±0.2 s / ±1 km/h / ±0.5 m. For combat that is enough for *timing* and not
enough for *counting*:

| number | channel | verdict |
|---|---|---|
| lock onset time | video: the reticle's state change, at 5 fps | readable to ±0.2 s — coarse but real |
| time-to-overheat | **audio**: the moment the `_Fire` events stop while the trigger is held | **UNKNOWN** — `qa1_hud.py` reads video only; needs an audio-event onset counter (§9) |
| shots to kill | audio event count (one `_Fire` = one round); the HUD has **no ammo counter**, only `DrawWeaponPowerLevel` | **UNKNOWN** — same missing tool |
| hull HP / damage dealt | no damage readout on any decoded HUD path | **UNKNOWN** — a health readout tool does not exist (see §9) |

Hence every "count" card here either bands a **binary** observation (the target survives / is
destroyed) or writes `UNKNOWN` with the tool named. No card writes a shot count it did not count.

## 3. The set-up every card shares

```
PRE-CONDITIONS
| P1 | LAUNCH passed, pid known | `Working/Q/PILOT/LAUNCH.md` | `RESULT: PASS` with pid |
| P2 | in the car | `Working/Q/PILOT/ENTER_EXIT.md` | `RESULT: PASS` |
| P3 | the batch that carries this weapon has landed | `python Tools/scripts/t23_closeout.py --check` | the card's `B-nn` row reads `applied` |
| P4 | build id | the LAUNCH RESULT line | a `test-0xx` / `bm-RC4` id, else `UNKNOWN` |
| P5 | target set | a parked stock vehicle + one pedestrian at a known spot, plus the airfield strip for timing legs | `SCREENSHOT.md` frame per target |
```

**`P3` is the gate that makes these cards honest.** If `B-18` (EMP), `B-19` (hacker), `B-20` (sonar),
`B-21` (tracker) or `B-15` (riot) has not applied, its card does not run: it writes
`RESULT: BLOCKED — P3 — B-nn not applied — <files>`.

**Riot's second entity** is why B-15 is a real card and not an edit: `T-WP10` "mode toggle" reads
*"no per-weapon mode member: the toggle is a second weapon entity/slot"* — and the slot count is
`T-WP13`, which is **blocked**. So the Q-3 riot take needs the B-15 entity, and if the build carries
only one cannon entity the card writes `BLOCKED` even when `P3` passes.

---

## 4. The cards

### 4.1 C1 — 60 mm cannon

```
GOAL: one press fires one round from the cannon muzzle, and the round kills a stock tank in the
      predicted 2-3 hits.
```

**Set-up.** Parked stock medium tank 25 m ahead, side-on; car stationary; battle-ish state per C6.

**Input.** `LMB` (keyboard) / `RB` (pad) — JC3 `FIRE_VEHICLE_WEAPON_PRIMARY`, **decoded**
(`Research/JC3Grab/INPUT.md`; `CONTROLS.md` row 10). BmAK's `RT` is a **menu label** in JC3, never a
key on a card. One press, one shot: `T-WP1` fire rate is `FiringInterval` **2 s**, so presses are
spaced 2.5 s.

**SEE — screen.** Muzzle flash at `CannonMuzzle` (`batmobile_cannon`), one round travelling, the
`DrawWeaponPowerLevel` element moving, the target's model taking the hit. **Audio.** `Play_..._Fire`
per shot and `_Reload` on the 2 s beat; `weapons.bank`'s tank-cannon events on the hit.

**Measure.** Two things, in order:
1. **Round count to destruction** — band **2–3 hits** (`DAMAGE_MODEL.md` §4 `table.medium_tank.tank_cannon`:
   `tank_cannon`, H0/H2 = 2, H1 = 3; `T7_WEAPONS.md` T-WP1 damage aspect). Counting needs §9's audio
   counter → until it exists, the card records the **destruction frame** and the number of visible
   muzzle flashes, and labels the count `±1`.
2. **Muzzle-origin check** — the round leaves from the cannon, not the car origin (`T-WP1` verify:
   "a shell fired at a wall leaves from CannonMuzzle (not the car origin)").

**Failure behaviour.** No muzzle flash on `LMB` but the car reverses → the primary fire is not bound
to the Batmobile's weapon: `FAIL`, and the settling file is `Research/JC3Grab/WEAPON_WIRING.jsonl`
(the `main_weapon` pointer). Round leaves the car origin → `FAIL`, `SOCKETS_JC3.json`'s
`CannonMuzzle` was not placed. Target survives 4 hits → `FAIL` (the blast did not carry).

**RESULT**
```
RESULT: PASS — cannon fires from CannonMuzzle, stock tank destroyed in <n> hits — pid=<pid> — caps/q3_c1/*
RESULT: BLOCKED — P3 — B-05 not applied — <files>
RESULT: STOP — step <n> — "<the SEE that failed>" — <files so far>
```
**TRAPS:** K-1/K-3 (the binding was wrong twice), K-5 (a field not sampled leaves no trace).

### 4.2 C2 — Vulcan, and the overheat band that is a non-event

```
GOAL: the Vulcan streams rounds from the chain-gun muzzle and does not stop for heat inside a 30 s
      burst.
```

**Input.** `RMB` / `LB` — JC3 `FIRE_VEHICLE_WEAPON_SECONDARY`, **decoded** (`CONTROLS.md` row 11).
BmAK's `RB` for the Vulcan is a **menu label**.

**Measure — K-10.** Hold the trigger **30 s** (the probe length, not a decoded value). Band:
**no stop and no overheat sound**. The BmAK rate is `HeatUpPerSecond` **0.0** with
`OverheatOffValue` **0.25**, so 0.25 / 0.0 has **no finite time**; the JC3 side has **no heat member at
all** (0 of 4,054 tune members name heat; `JC3_HUD_WEAPONS.md:7`). A stop inside 30 s, or
`Engine.Play_Minigun_Overheat`, **fails** the line.

**Failure behaviour.** Gun stops at ~10 s → `FAIL`; that would mean a per-shot heat add in native code
that the grab does not exclude (`FOOTAGE.md` F-3), and the settling file is
`Research/BatmobileGrab/WEAPONS.json` (the `HeatUpPerSecond` field) plus a re-read of `FOOTAGE.md`.
Barrels do not spin → not this card: it is T-12 **P-03**'s part behaviour (`T-WP2` "barrel spin").
Shots to kill: **UNKNOWN** — `T-WP2` damage is UNKNOWN ("BmAK gives no soldier/vehicle health to ratio
against"), so no card may band a count.

**RESULT**
```
RESULT: PASS — 30 s burst, no overheat stop, barrels spinning — pid=<pid> — caps/q3_c2/*
RESULT: FAIL — gun stopped at <t> s (heat) — pid=<pid> — caps/q3_c2/*
```

### 4.3 C3 — missiles with lock-on (no 2.0 s promise)

```
GOAL: the reticle acquires a target, N missiles leave the pods, and what the round does is recorded —
      the lock time is recorded, not asserted.
```

**Set-up.** Two parked cars 30 m and 60 m ahead, plus one moving car for the homing check.

**Input.** **UNKNOWN.** JC3 has no barrage action: `CONTROLS.md` rows 12–14 and 17 are all `UNKNOWN`;
BmAK's is `QuickGadgetX` → `SelectVehicleWeapon(2)` (`DefaultInput.ini:269`), a **selection**, not a
fire key (`CONTROLS.md` §2 E). Discovery route in §8. This card may not name a key until §8 resolves.

**SEE — screen.** The POI 21 reticle (`POI_TYPE_LOCK_ON_TARGET`, one rotating reticle, **1.5 s per
turn**) changes state; missiles leave both pods (`T-WP3`: **4 fire points**, sockets `MissileL` /
`MissileR`). **Audio.** `Play_..._ApRocket_Fire` per launch; no `MCI_missile_locked` — that flashing
string is the *incoming* warning, a different instrument (`JC3_HUD_WEAPONS.md` §1.5).

**Measure.**
| quantity | band | source |
|---|---|---|
| lock **onset** time | **recorded, not banded** — the build has no duration member; every recorded sample ≤ **1 s** | K-11 (`UNKNOWN` for the build) |
| missiles per press | **4** (the donor's fire points); **not 8** | `T-WP3`; the salvo figure has no card |
| hit / no-hit on a parked car | at least one round hits the aimed car | `T-WP3` verify |

The BmAK numbers 2.0 s / 1.0 s are quoted **as BmAK's**, in a note, never as the card's band.

**Failure behaviour.** Reticle never appears → the lock marker is T-WP3's named gap; `UNKNOWN`, not
`FAIL`, and the settling file is `Research/JC3Grab/JC3_HUD_WEAPONS.md` §1.5 (the AutoAim → POI link
"is not in any file"). Fewer than 4 missiles → `FAIL` the fire-point placement. A salvo of 8 → record
it as an observation and **do not** score it: no card rows 8, and `T-WP13` is blocked on exactly this
question.

**RESULT**
```
RESULT: PASS — lock at <t> s (recorded), 4 missiles from both pods, <n> hit — pid=<pid> — caps/q3_c3/*
RESULT: UNKNOWN — no reticle (AutoAim->POI link undecoded) — pid=<pid> — caps/q3_c3/*
```

### 4.4 C4 — EMP burst (B-18)

```
GOAL: the pulse fires from a car action and a target vehicle stops, with the disable duration
      measured rather than assumed.
```

**Gate.** `B-18` applied (`P3`). `T-WP15` — the disable half — **has no value until the probe runs**
(`BUILD_BATCHES.md` B-18 gate: "Q-EMP-1…4 answered and the duration written from the measurement").

**Input.** **UNKNOWN.** `CONTROLS.md` row 15: JC3 has no action; BmAK's battle screen says `B` = EMP,
D-11 says `B` = immobiliser — the two labels disagree (conflict D). Discovery in §8.

**SEE — screen.** A pulse ring plus `explosion_emp_flatbed.effc` on the target; the target **stops**
(no damage numbers exist to show). **Audio.** The pulse's own event; EMP has no weapon-sound member
(`T-WP5`).

**Measure.** 
| quantity | band | source |
|---|---|---|
| disable happens | target stops moving/turning, no hull damage | B-18 gate |
| disable **duration** | **measured**, written back into `T-WP15` | B-18 gate ("the duration written from the measurement") |
| damage | **0** — the pulse does 100 player damage in 25 m on the truck precedent, i.e. not a disable | `EMP.json`; `T-WP5` |

There is no numeric band: `T-WP15` is a named omission until this take fills it. The card's job is to
**produce** the number, and the honest RESULT is `PASS` only for "the target stopped and the duration
is <t> s, written to T-WP15".

**Failure behaviour.** Pulse fires, target keeps driving → `FAIL`; the settling file is
`Working/Translation/T_WP4C_TRACKER_EMP.md` (the `SetDisabledByEMP` finding: no EMP-named member on
any NPC `RVehicle*`). Nothing fires at all → the trigger is the unknown (`T-WP5`: 14 unowned pulses,
firing moment UNKNOWN) → `UNKNOWN`.

### 4.5 C5 — riot mode (B-15, zero-damage impulse round)

```
GOAL: the riot round pushes a target and leaves its health unchanged, at a 0.75 s cadence.
```

**Gate.** `B-15` applied **and** the build carries the **second cannon entity** (`T-WP10` mode toggle;
if only one cannon entity exists, `RESULT: BLOCKED`).

**Input.** **UNKNOWN** — the toggle is a second entity/slot, and the slot count is `T-WP13` **blocked**.
No key is guessed; §8's discovery route applies to `QuickGadget*` tokens only.

**SEE.** `Riot_Suppressor.Anti_firearm_gel_Miss` on the hit, `Batmobile_RiotSuppressor_Tracer` in
flight, `RiotSuppressor_BulletCasing` ejected. **Audio.** `Play_RiotSuppressor_Bolt` per round,
`Play_RiotSupressor_Impacts` on the hit — both are `missing-object` in the JC3 grab (`T-WP10` sounds),
so silence is an expected possible outcome and is recorded, not failed.

**Measure.**
| quantity | band | source |
|---|---|---|
| target health after 5 hits | **unchanged** (0 damage) | `T-WP10`: `base_tuning.damage` = 0 |
| target displaced | **pushed** (impulse > 0) | `T-WP10` knock-back row (unit UNKNOWN) |
| cadence | **0.75 s** per round (vs 0.138 s lethal) | `T-WP10` `RiotSuppressorFiringInterval`, **decoded** |
| cone | 7.5° — **UNKNOWN which member** carries it | `T-WP10` lock-on cone row (`derived`) |

Health "unchanged" needs a health readout that does not exist (§9); the observable substitute is
**"the target still drives after 5 hits"**, which the card may band. Damage is the `UNKNOWN` half.

### 4.6 C6 — mode switch (battle ↔ pursuit)

```
GOAL: the car changes mode on one input and the plates/weapons change with it — or the card records
      that the change cannot be triggered by a decoded input.
```

**Input.** **UNKNOWN.** `CONTROLS.md` row 18: BmAK's `LT` hold is `aLeftTrigger` (`DefaultInput.ini:253`)
with the call path undecoded; JC3's `LT` is **`REVERSE`** (decoded) — so holding it reverses the car
unless the build consumes the axis (conflict C). The threshold is also UNDECODED: the only floats are
`0.05` (offset 257) and the ini `DeadZone` **0.2** (conflict H).

**SEE.** Armour plates fold, weapon silhouettes swap, `TryToChangeMode` is native (no script trace).

**Measure.** Binary + threshold hunt:
1. hold `LT` progressively; note the trigger amount at which the plates move. Band: **0.05 or 0.2**,
   and any other value is recorded as "threshold elsewhere" (not a FAIL of the card);
2. if the car reverses instead → conflict C is live: `FAIL`, no mode change on that axis.

**Failure behaviour.** Plates never move → the input→state link is UNKNOWN (`K-2`: "Do not write a
card that claims a decoded binding") → `UNKNOWN`.

### 4.7 C7 — afterburner

```
GOAL: the boost fires and adds the predicted speed, with no grip snap.
```

**Input.** **UNKNOWN.** `CONTROLS.md` row 8: BmAK `Y` = `bVehicleBoostButton` (`DefaultInput.ini:270`)
has **no JC3 action name**; `LShift` is `HANDBRAKE`; `WINGSUIT_BOOST` is wingsuit-only. Discovery §8.

**SEE.** Flame at the `Afterburner` socket (`EngineNitro` usage 4197885156 on the donor's two
emitters, `T_FX3B.md`), speed surge. **Audio.** `car_cycle_base_dual_nitrous` on the exhaust.

**Measure.** Peak delta against the no-boost leg: **+32.4 to +43.2 km/h** (`PREDICTIONS.md` D-2b; the
fleet `nitro_boost` gives +40 km/h, torque ×2). Grip must stay at 1.0 (`T-B3`): a sideways step on
engage is a FAIL. The speed instrument is the step-6 one (`qa1_hud.py`, ±1 km/h).

### 4.8 C8 — sonar (B-20)

```
GOAL: the pulse fires from a car action, pushes a parked car without damaging it, plays both sonar
      events, and the markers appear and expire.
```

**Gate.** `B-20`. **Input.** **UNKNOWN** — BmAK `L3` (`BatmobileSonar`, `DefaultInput.ini:256`); JC3
has no sonar/scan action (`CONTROLS.md` row 16). Discovery §8.

**SEE.** A pulse ring; the parked car **moves** and does not break. **Audio.** `Pulse_Search`
(`0x97CBF248`) and `Pulse_Full` (`0xFFCC9813`) — both decoded `BML_Sonar` event ids, verified as
`fnv1(lower(name))` (`AUDIO_BANKS2.md`). **Markers:** N markers appear and expire (B-20 gate).

**Measure.** Binary set from the B-20 gate: pulse fires from a car action; parked car pushed, **0
damage**; both events play; N markers appear and expire. Radius has **no BmAK member** (`T-WP8`): the
5 m comes from the zero-damage precedent `gen_explosion_5m_nodamage.ftune`, a **design value**, and
the card says so. **The reveal is `UNKNOWN`** until a marker exists (`T-WP8` "0 decoded script creates
a scan/reveal POI").

### 4.9 C9 — winch

```
GOAL: the cable fires and latches, and the card records that it does not pull (no loop yet).
```

**Input.** **UNKNOWN** — operator decision 2026-11-05: **D-Pad Right**, replacing Mission Select
(`CONTROLS.md` row 20). JC3 candidates are `VEHICLE_RELEASE_GRAPPLE` (`V`) and `USE_VEHICLE_MOD`
(`MMB`), neither calling a winch. Discovery §8.

**SEE.** Cable leaves the car, `winch_latched` effect on the hit (`RBatmobileWinch.ImpactEffect`),
`FireSound` (`T-WP6`). **Measure — this is a negative band, by design:** `T-WP6`'s verify is *"fire
the winch at a pole — **no pull until B-16's loop exists**"*. So `PASS` = cable attaches and the car
does **not** get pulled. A pull would contradict `T-WP6` and needs `MODLOG` §87 re-read.

### 4.10 C10 — hacker (B-19)

```
GOAL: a stock drone stops firing for its own side and starts firing for the player's.
```

**Gate.** `B-19`. **Input.** **UNKNOWN** — BmAK `Y` = `QuickGadgetY` → `SelectVehicleWeapon(3)`
(`DefaultInput.ini:270`), a selection, not a fire key. Discovery §8.

**SEE.** `Particles.DroneHacker_Beam`, then `DroneHacker_Success`; the drone's muzzle stops. **Audio.**
`HackingSound`, `SucessfullHackSound`, `BeamPositionalSound` — **0 audio members in the JC3 weapon
tunes**, so absence is expected and recorded.

**Measure.** Binary: the beam plays, the **cooldown is 1 s** (`WeaponCoolDown`, decoded), and the
side flip happens. The flip is the gadget's whole behaviour and has **no member on either side**
(`T-WP7`: 0 allegiance members in 295 `.ee` dumps) → the card's `UNKNOWN` is "did the flip hold",
and B-19 is the probe that answers it.

### 4.11 C11 — tracker (B-21)

```
GOAL: the round homes onto a moving car and a POI with a live distance follows it.
```

**Gate.** `B-21`. **Input.** **UNKNOWN** — BmAK `B` = `QuickGadgetB` → `SelectVehicleWeapon(1)`
(`DefaultInput.ini:268`); D-11 says B = immobiliser, the battle screen says EMP (conflict D).
Discovery §8. Note K-4's correction: targets are **tagged automatically in range** — the card must not
require a "tag" input to make a lock possible.

**SEE.** A yellow/grey circle on the tracked car, a distance readout, the round curving. **Audio.** the
tracker has **no bank** (`T-WP9` sounds: none decoded).

**Measure.** Binary: the round homes; a POI with a **live distance** appears. The fire direction is
**30.0 deg** up (`LaunchRotationOffset` [5461,0,0] = 5461/65536 × 360) from socket
`BattleModeSpotLight` — a decoded number the card may check as "does the round leave upward".
Homing flag/delay have **no member** (`T-WP9`), so "which member the engine reads" is `UNKNOWN`.

---

## 5. Which card may move which row

| card | rows it can move | verdict it may write |
|---|---|---|
| C1 | WPN-1 (`T-WP1`) | PASS / FAIL |
| C2 | WPN-2, K-10 | PASS / FAIL |
| C3 | WPN-3, K-11 (recorded only) | PASS / UNKNOWN / BLOCKED |
| C4 | WPN-4, WPN-4b (`T-WP15`), B-18 | PASS (duration written) / UNKNOWN / BLOCKED |
| C5 | WPN-10, B-15 | PASS / UNKNOWN / BLOCKED |
| C6 | `T-MD5`, `T-MD6` (composed), `T-MD10`, `T-MD11` (same-switch); `T-MD8`, `T-MD14` stay omissions | UNKNOWN unless a threshold is seen — B-12's runtime swap is U1 |
| C7 | WPN-11 (`T-WP11`), `T-B1`/`T-B2`/`T-B3` | PASS / FAIL |
| C8 | WPN-8, B-20 | PASS / UNKNOWN / BLOCKED |
| C9 | WPN-6, B-16 dep | PASS (no-pull) / FAIL |
| C10 | WPN-7, B-19 | PASS / UNKNOWN / BLOCKED |
| C11 | WPN-9, B-21 | PASS / UNKNOWN / BLOCKED |

A card never moves a row whose gate has not landed, and never writes `PASS` for a count it could not
count (§2).

## 6. How to write the result

Same file and grammar as step 6 (`Working/Q/RESULTS.md`, append-only, **seven** columns, the RESULT
line verbatim beneath the row). A combat row keeps those seven and appends two, `weapon` and `target`,
declared here so every combat row shares one nine-column header:

```
| C3 | missiles, lock onset | 0.6 s (recorded) | none - K-11 UNKNOWN | UNKNOWN | caps/q3_c3/lock.mp4 @ 2026-11-07T15:11:04Z | bm-RC4 | w618 | parked sedan |
```

## 7. The discovery rule for every `UNKNOWN` input

`CONTROLS.md` §2 lists the conflicts; the discovery route is the same for all of them and is the only
legal way a card gets a key:

**Route 1 — the ini (a data answer, BmAK scheme only).**
```
DO   grep -n "QuickGadgetX\|QuickGadgetY\|QuickGadgetB\|bVehicleBoostButton\|BatmobileSonar\|aLeftTrigger" \
       <BmAK>/BmGame/Config/BmInput.ini <BmAK>/BmGame/Config/DefaultInput.ini
SEE  the token appears on a `Bindings=(Name="<pad/key>",Command="<token>")` line
IF NOT  the token is absent -> the binding is not in either ini: STOP, do not guess
```
`BmInput.ini` is **not in this repo** (`CONTROLS.md` §4: "BmInput.ini is not in this repo; the merged
array is the oracle"), so step 1 is a live read of the installed game. What the repo already holds is
`DefaultInput.ini`'s line numbers, which is what `CONTROLS.md`'s token table cites.

**Route 2 — the HUD / controls screen (a label, not a key).**
The in-game controls screen transcribed in `CONTROLS_MENU_SCREENS.md` names labels only ("Afterburner",
"Missile Barrage", "Scan", "EMP"). A label is **never** promoted to a key: `CONTROLS.md` rule 6
(`UNKNOWN` rows may not appear as keys).

**Route 3 — the radial/preview HUD.** `DrawWeaponSelectHud` exists (`CONTROLS_CONSUMERS.md`), so a
weapon is *selectable*; what it does not prove is which physical input selects it. A card may record
"the slot is selectable" and still not name the input.

**What none of the three can do:** create a JC3 keymap action. `INPUT_D11.md`: **0 of 134** decoded
vehicle modules reference any keymap action, and no entity names `keymap`. So for the six BmAK-only
gadgets the honest end state is `UNKNOWN` **even after** the ini read — the ini names BmAK's pad key,
and JC3 will not deliver that action to the Batmobile unless the build routes it. That routing is a
build item (D-11's switch), not a pilot step.

## 8. Repeats and the circuit breaker

* Weapons: **5 presses per observation**, 2 clean takes. Timing: **3 attempts**, 2 clean.
* Three identical failures = `STOP` (`CARD_FORMAT.md` §2 rule 5) and the observation goes on the
  RESULT line.
* One launch per boot, `KILL.md` only by PID — these cards do not launch or kill.

## 9. Instrument gaps (UNKNOWN + the exact tool needed)

| number | why | exact tool needed |
|---|---|---|
| shots to kill (C1, C2) | no ammo counter; the HUD carries `DrawWeaponPowerLevel` only | an **audio event-onset counter** over the take (one `Play_*_Fire` = one round) — nothing in `Tools/scripts` reads audio |
| time-to-overheat (C2) | it is an audio event, not a HUD value | the same counter, tuned to `Engine.Play_Minigun_Overheat` |
| damage dealt / target health (C1, C5) | no health readout on any decoded HUD path | a **health readout tool** (in-memory read of the target's health component) — does not exist in the repo; `qa1_hud.py` is video-only |
| mode-switch threshold (C6) | `TryToChangeMode` is native, no script trace | a **sampler on `LastTriggerAmount` + the mode field** (`K-5` is exactly this lesson: a field not sampled leaves no trace) |
| sonar marker count (C8) | POI creation is engine-side, 0 decoded script creates a scan POI | a **POI census** (entity/POI dump) — not in the repo |
| lock duration (C3) | 0 JC3 members name one | a **live read of the lock field** on the weapon instance (`K-5` again); until then K-11 stays `UNKNOWN` |

Every one of these is a tool, not a measurement the pilot can improvise. A card that needs one writes
`UNKNOWN` and this table's tool name.

## 10. Checks run for this document, and revert

| # | check | result |
|---|---|---|
| 1 | `python Tools/scripts/t7_weapons.py --check` | exit 0 — `15 rows = 13 WPN + 2 decisions (13 carriers, 1 omission, 1 blocked)`, `46 UNKNOWN` aspects |
| 2 | the three refusals traced | K-11 (`UNKNOWN` for the build; 233 samples, max 1 s), `T-WP3` = 4 fire points + `T-WP13` blocked, `T-WP10` = damage 0 / 0.75 s / second entity |
| 3 | B-24/B-25 checked before repeating the salvo claim | they are **handling** and **lens-flare** batch cards (`BUILD_BATCHES.md`, `apply-keep-audit-fixes-*.md`), not weapons — so no salvo card exists and none is promised |
| 4 | gadget gates read from the batch table | B-18 EMP (probe writes `T-WP15`), B-19 hacker, B-20 sonar, B-21 tracker, B-15 riot |
| 5 | every key checked against `CONTROLS.md` | only rows **10/11/21/22/23** are decoded; the other gadget rows are `UNKNOWN` and carry §7's discovery route |
| 6 | audio strings decoded, not remembered | `Pulse_Search` `0x97CBF248`, `Pulse_Full` `0xFFCC9813` (`AUDIO_BANKS2.md`); `MCI_missile_locked` is the *incoming* warning |
| 7 | card shape vs `CARD_FORMAT.md` §1–§3 | GOAL / PRE-CONDITIONS / input / SEE / measure / failure / RESULT |

No game process was started, no build installed, no T row and no `PREDICTIONS_COMBAT.md` line edited.
**Revert:** delete this file.
