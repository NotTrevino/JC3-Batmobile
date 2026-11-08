# Ejection: BmAK's launch, glide entry and landing, against JC3's hold-A / parachute / wingsuit

**Scope.** The four quantities the lore asks for — BmAK's **launch height**, **launch speed**,
**glide entry point** and **landing behaviour**, with numbers — then the JC3 members behind the
**hold-A eject**, the **parachute** state and the **wingsuit**, and the numbers our version has to hit
to match.

**Already covered, cited, not repeated.** This card does not re-derive:
`tmp/freebuff/reports/review-JC3-EJECT.md` (JC3's engine eject names exist, no data references them;
4,839 exits / 0 launch members; 17 hash-named members per exit, none float/vector);
`tmp/freebuff/reports/review-JC3-SEAT.md` and `Research/JC3Grab/SEAT.md` (the seat/exit-point geometry);
`Research/JC3Grab/EJECT_MAP.md` (the button table: A/A, LB, and the shipped-vs-export disagreement);
`Research/JC3Grab/EJECT.md` (the 26 donor exits and their speed gates);
`Research/BatmobileGrab/EJECT_VELOCITY.md` (the `(0,0,0)` `SetRBLinearVelocity` on `Car.Core.Mesh`);
`Research/BatmobileGrab/EJECT_MOVE.md` (the glide-kick root motion);
`tmp/freebuff/reports/DRIVERLEFT-regions.md` (the post-exit collision-mode selector). What is new here
is the **number for launch height** (`EjectUpDist` 1300.0, decoded below), the **landing side**, and
the **arithmetic that shows which of the four a JC3 exit can carry**.

**Not done.** No game launch, no attach, no build write, no ledger/backlog/tracker edit.

---

## 1. The BmAK eject chain, in order

| # | step | value | source |
|---|---|---|---|
| 1 | input | **A** runs `EjectFromVehicle` (one line, `DefaultInput.ini:267`); menu: **A, A** = "Eject Into Glide", **LB** = "Exit Batmobile" | decoded / menu-label, `EJECT_MAP.md` §2 |
| 2 | second press | the body writes `LastEjectFromBatmobileTime` beside `WorldInfo.TimeSeconds` (`+1273`/`+1291`); **no sub-second window constant exists** in the body (float constants 1.0, 600.0, 0.0, 1.0, 1.0) | decoded timestamp, window **UNKNOWN** |
| 3 | guard | `CantEjectFromBatmobile(74)` at `+3`; condition not decoded | call decoded |
| 4 | space check | `CheckSpaceAboveBatmobileCockpit()` at `+173` | decoded |
| 5 | seat release | `DriverLeave(true, …)` `+365`, `RemoveBatmobileBindsAndSetBatmanBinds()` `+424`, `PlayCockpitOpenFast()` `+443` | decoded |
| 6 | car | `SetRBLinearVelocity((0,0,0), false)` `+513` on **`EjectFromVehicle.Car.Core.Mesh`**, inside `if (FFInRange)` — the car is **stopped**, not launched | decoded, `EJECT_VELOCITY.md` |
| 7 | the launch | `TriggerSpecialMove(self, Loc, …)` `+1103` on `Car.ShortRangeGlideKick` → `GlideKick.GlideKickShort_FromBatmobile` | decoded, `EJECT_MOVE.md` |
| 8 | where it ends | the move's animations are named `…_Glide_Kick`; the body references `CapeGlideTarget` (`+1254`) and `AttackGlide` (`+1266`); the `Eject*Move` defaults all end `_To_Glide` | decoded names |
| 9 | offer range | `ShortRangeGlideKickRange` **2500.0** (25 m) — the range at which the kick is offered | decoded, `CLASS_DEFAULTS.md:149` |

---

## 2. The four numbers

### 2.1 Launch height — `EjectUpDist` = 1300.0

| fact | value | source |
|---|---|---|
| `RVehicleBatmobileBase.EjectUpDist` | **1300.0** (FloatProperty, offset 6032 / `0x1790`) | `CLASS_DEFAULTS.md:143,454`; `SAMPLER_FIELDS2.md:113` |
| what applies it | the native `ModifyEjectUpLoc` plus `SetBatmobileExit` | `NATIVE.md`, cited in `EJECT.md` §6 |
| the kick animation's own rise | **0 cm** (root translation `(764.945, 0, 0)`) | `EJECT_MOVE.md` §4 |
| under BmAK's centimetre convention | **13.0 m** | derived (×0.01) |

So the height and the travel come from **two different places**: `EjectUpDist` (native placement, 13.0 m)
and the kick's root motion (0 m up, 7.65 m forward). The unit of `EjectUpDist` is not printed in
`BmGame.upk` — the cm reading is derived from every other BmAK length in this grab (`CAMERA.md:169`,
`WEAPONS.md:695`, and the animation's own `cm` root motion), and is the number §4 uses.

### 2.2 Launch speed — 204.9 cm/s, and it is not car-relative

| quantity | short-range kick | mid-range kick |
|---|---|---|
| root translation | **764.945 cm (7.649 m)** | **949.433 cm (9.494 m)** |
| vertical rise | 0 cm | 0 cm |
| frames @ rate | 113 @ 30 fps | 114 @ 30 fps |
| duration | **3.7333 s** | 3.7667 s |
| mean speed | **204.9 cm/s (2.049 m/s)** | 252.1 cm/s (2.521 m/s) |
| mean step per frame | 6.83 cm | 8.38 cm |

which of the two plays is `PickRandomAnim` over an `AnimName` array — **not decoded**
(`EJECT_MOVE.md` §6). The car's own velocity is zeroed on the `FFInRange` branch before the move is
triggered, so 2.05 m/s is Batman's speed **over the ground**, not over the car.

### 2.3 Glide entry point — the end of the kick, 7.649 m out, 0 m up, at t = 3.7333 s

| fact | value | source |
|---|---|---|
| entry time | **3.7333 s** (short) / 3.7667 s (mid) after the press | `EJECT_MOVE.md` §4 |
| entry offset | **(+7.649, 0, 0) m** from the eject point | same |
| glide entry moves that exist | `GlideInMove` → `Get_In_Batmobile_Gliding`; `GlideBoostInMove` → `Get_In_Batmobile_Glide_Boost` | `CLASS_DEFAULTS.md:82,83` |
| glide anim lengths | `BatMobile_Glide_In` 2.0 s, `BatMobile_Glide_In_Front` 1.8 s, `BatMobile_Glide_Boost_In_Back` 2.3333 s | `EJECT_MOVE.md` §5 |

### 2.4 Landing behaviour — the land clips carry no motion

| sequence | length | frames | root motion |
|---|---|---|---|
| `BatMobile_Glide_Out_Land_Back` | **3.5333 s** | 107 | none (field 108 absent) |
| `BatMobile_Glide_Out_Land_Back_02` | **3.3 s** | 100 | none |
| `BatMobile_Glide_Out` | 1.4333 s | 44 | none |
| `BatMobile_Glide_Out_02` | 2.0 s | 61 | none |

`EJECT_MOVE.md` §5 is the census. The consequence is the landing number: because the land clips are
in place, **all forward travel has already happened before touchdown**. The glide leg's length is
**UNKNOWN** (no glide-distance member anywhere in the grab), so the only pinned distance is the kick's
7.649 m; the landing itself adds **0 m** and takes 3.3–3.53 s of animation.

---

## 3. The JC3 members behind each half

### 3.1 hold-A eject

| member | value | source |
|---|---|---|
| action name | **`OPEN_PARACHUTE`** on **`RPADDOWN`** in the shipped gamepad table; on **`A`** in the player's export; keyboard `A` | `EJECT_MAP.md` §3, `INPUT.md:52` |
| share | `STUNT_JUMP` and `JUMP` sit on the **same** control in both tables — the press/hold fingerprint, not its proof | `EJECT_MAP.md` §3 |
| hold field | **none**: 474 bindings parsed, 0 hold/duration/tap words; `settings/parachuteparams.bin` is 344 B of asset paths only (`parachute.bsk`, `parachute.asb`) | `EJECT_MAP.md` §3.1 |
| eject action | **none** matches `/EJECT/` in any of the four tables — the only eject names are in the exe (`ACT_EJECT_FROM_VEHICLE`), unreferenced by data | `review-JC3-EJECT.md` |
| vehicle-context gate | the donor exit's parent-speed condition: `exit.driver.moving.parachute` → **`S_EXIT_VEHICLE_PARA`**, gate **(5.0, 999.0)**; plain `exit.driver.default` → `S_EXIT_VEHICLE`, gate (0.0, 5.0) | `EJECT.md` §3 |
| exit point | `point.driver` donor **(−0.440, 0.340, 0.200)**; Batmobile **(−0.578, 0.598, 0.392)** m, "inside", tolerance 0.585 / 0.0428 | `INTERACTION.md:47`, `SEAT.md:30` |
| fleet reach | the fast exit is on **221 of 232** vehicles | `EJECT.md` §4 |
| state machine | `S_EXIT_VEHICLE_PARA` **×2** in `rico_base.afsmb` @254304; `ACT_EXIT_VEHICLE` ×1 @106752; `ACT_EJECT_FROM_VEHICLE` **0** | `EJECT_MAP.md` §3.2 |

### 3.2 parachute

| member | value | source |
|---|---|---|
| clip | **`PPparachute_vehicle_eject`** @180702 in `rico_base.asb` (2,678,768 B), plus `PPparachute_opened` @399106 and `rico_vehi_car_low_driver_to_parachute.ban` @727306 | `EJECT_MAP.md` §3.2 |
| vehicle→chute transition | the exit's `state` string, nothing else; **no chute physics member exists** in the 232 module dumps (`parachute` raw 28 / member **0** — all 28 are asset paths) | `EJECT_MAP.md` §3.1 |
| chute numbers | **none decoded**: `parachuteparams.bin` carries paths, and the only `Parachute.*` members in the whole grab are **weapon auto-aim** parameters (`AlwaysTargetDistance` 3, `AngleThreshMultiplierCutoff` 50…500), not flight | `WEAPONS.md:513-517` |
| voices | `bark_rico_parachute_ejecting_01..04` — 8 index paths | `review-JC3-EJECT.md` §5 |

### 3.3 wingsuit

| member | value | source |
|---|---|---|
| actions | `OPEN_WINGSUIT`, `WINGSUIT_TAKEOFF` (both `RPADUP` shipped / `Y` export), `WINGSUIT_BOOST` (RT), `WINGSUIT_AIRBRAKE` (LT), `WINGSUIT_EVADE`, `FREEFLY` (F10), `FREEFLY_COMBO1/2` | `EJECT_MAP.md` §3, `INPUT.md:81-84` |
| clip | `PPparachute_from_wingsuit` in `rico_base.asb` — the chute-open-from-wingsuit pose | `review-JC3-EJECT.md` §5 |
| numbers | **none decoded**: no wingsuit tune in `settings/`, no wingsuit member in the 232 module dumps (`wingsuit` member 0) | `EJECT_MAP.md` §3.1, `STANDALONE.md` |
| conflict | `Y` is JC3's `ENTER_VEHICLE`/`EXIT_VEHICLE`/`OPEN_WINGSUIT`/`WINGSUIT_TAKEOFF` and BmAK's afterburner — a doc-side conflict, already flagged in `EJECT_MAP.md` §5 | `EJECT_MAP.md` |

---

## 4. What matches, with the numbers

| quantity | BmAK | JC3 carrier that can hold it | match number | verdict |
|---|---|---|---|---|
| **launch height** | `EjectUpDist` **1300.0** → **13.0 m** (derived, cm) | the exit's **`PointNode`**: `point.driver` is the position every driver exit inherits | **+13.0 m** on a dedicated eject point | **carrier exists, one edit** — the exit objects inherit `point.driver` (`SEAT.md:25,30`), so a second `PointNode` at **(−0.578, 13.598, 0.392)** re-pointed at `exit.driver.moving.parachute` keeps every other exit on the ground. Whether an `Exit` can override the inherited point is **UNKNOWN** (U-1). |
| **launch speed** | **2.049 m/s** forward, 0 rise, over **3.7333 s** = **7.649 m** | **none** — 0 of 4,839 exits carry a velocity/impulse, and the 17 hash-named members per exit are int/mat/vec_events (**0 float, 0 vector**) | the exit clip would have to travel **7.649 m in 3.7333 s** | **gap.** JC3's exit hands the player to the engine with inherited velocity; at the gate's floor (5 units) the player is already moving faster than 2.05 m/s, so the 7.65 m figure is **only reachable if the car is stopped** — which is exactly what BmAK does (`(0,0,0)` on `Car.Core.Mesh`) and JC3 has no exit-side member for. |
| **glide entry** | at **t = 3.7333 s**, **+7.649 m** forward, 0 rise | `S_EXIT_VEHICLE_PARA` is entered **at the exit**, not 3.73 s later; the fall exit `exit.driver.to.fall` exists only at gate **(0.0, 5.0)** | chute must open **3.7333 s** after the press | **gap with a mechanism:** at speed JC3 gives the para state immediately (gate 5..999), and the only speed-gated alternative is the roll-out, so the 3.73 s delay cannot come from the exit graph. It can come from the **clip** (`PPparachute_vehicle_eject`, length **UNKNOWN**) or from the player's `OPEN_PARACHUTE` hold — whose duration is also **UNKNOWN** (no hold field in 474 bindings). |
| **landing** | land clips **3.5333 s / 3.3 s**, **0 m** root motion; last 7.649 m of travel already spent in the kick | native (no member); the `S_*` states have no distance fields | **0 m** travel during landing; pegged distance **7.649 m** from eject point | **matches by construction** — nothing to author: if the kick's 7.649 m is reproduced, landing adds none. The glide leg's distance stays **UNKNOWN** (U-3). |
| car stops on eject | `(0,0,0)` on `Car.Core.Mesh` when `FFInRange` | **none** decoded | — | **gap, out of this card's four** — recorded because it is what makes the 2.05 m/s figure absolute rather than relative. |

### 4.1 The arithmetic that decides the build

1. BmAK's eject is **13.0 m up, then 7.649 m forward at 2.05 m/s**, in **3.7333 s**, from a **stopped** car.
2. JC3's fastest exit (`S_EXIT_VEHICLE_PARA`) is offered from **5 game speed units** up. The unit is
   **UNKNOWN** (`EJECT.md` §8.4: nothing in the file states it), so no m/s threshold is quoted — but
   any non-zero car speed adds to the player's exit velocity and will exceed 2.05 m/s for a car at
   the gate's floor. The two models only agree if the car is at rest, which the gate forbids.
3. Therefore **height** must be authored as a placement (the `PointNode` edit) and **forward travel**
   must be authored by the exit clip, not by car speed. That is the one design conclusion of this card.
4. The 3.73 s glide delay is the same problem: JC3 enters `S_EXIT_VEHICLE_PARA` at t=0, so the delay
   lives in the chute-open path (`OPEN_PARACHUTE` hold or the clip), never in the exit graph.

---

## 5. Build recipe

1. **Exit**: keep the donor's `exit.driver.moving.parachute` (`S_EXIT_VEHICLE_PARA`, gate 5..999) as the
   hold-A outcome; keep `exit.driver.default` (0..5) as the at-rest outcome. Both already sit on
   `point.driver`; no gate edit is proposed, because the gate's unit is unknown and inventing one
   would be the substitution the rules forbid.
2. **Height**: add `point.driver.eject` at **(−0.578, 13.598, 0.392)** m and re-point only
   `exit.driver.moving.parachute` to it (U-1 decides whether an `Exit` can override the inherited
   point; if it cannot, the height must be dropped to 0 and declared).
3. **Delay / glide entry**: do **not** try to hold the player in the para state for 3.73 s from entity
   data. Set the chute-open path to the clip/hold mechanism (U-2), and declare 3.7333 s as the target
   the clip or the hold must hit.
4. **Landing**: nothing. The land clips add 0 m; the 7.649 m figure is the kick's, and the glide leg is
   left to native flight (U-3 quantifies what that costs).
5. **Wingsuit**: leave JC3's `OPEN_WINGSUIT`/`WINGSUIT_TAKEOFF` alone. No wingsuit number exists in
   either grab, so there is nothing to match and nothing to change; the doc-side `Y` conflict belongs
   to the controls card, not here.
6. **Car stop**: not solvable from an exit (U-4). Record it as a known divergence from the four
   quantities rather than faking it with a brake.

---

## 6. UNKNOWNs, file/probe and a pilot check each

| id | UNKNOWN | what settles it | one-sentence check + pass band |
|---|---|---|---|
| U-1 | whether an `Exit` object can override the inherited `point.driver` position | `Research/Epe/serpente_civilian.xml`: does any `CInteractionGraphExit` carry its own position, or only `point.driver`? | Hold A at speed: Rico starts ~13 m above the car and the other exits still start at the seat — pass if the height offset appears on the eject only and every other exit stays put. |
| U-2 | the chute-open delay: clip length vs hold duration | `rico_base.asb` clip body for `PPparachute_vehicle_eject` (undecoded), or a runtime hold measurement | Hold A for 1 s: the chute opens about 3.7 s after the eject, not instantly — pass if open-time is 3.73 ± 0.3 s from press. |
| U-3 | the glide leg's distance (and so the true touchdown range) | no member exists; it is native flight, measurable only in game | Eject at 5 units over flat ground, no input: touchdown within 7.6–12 m of the eject point — pass if outside that band it is recorded as a mismatch, not tuned away. |
| U-4 | whether any JC3 data path can zero the parent's velocity on exit | the exits carry 0 motion members (decided); the remaining candidate is native or a vehicle module member — `RigidBody` sweep found none | Eject at speed: the car keeps rolling — pass if the divergence is accepted (BmAK stops it, JC3 will not), recorded as a known difference. |
| U-5 | `EjectUpDist`'s unit | no unit in `BmGame.upk`; cm is the convention used by every other BmAK length here | Same as U-1: the observed rise is 13 m, not 1.3 m or 130 m — pass if the apex is 13 ± 1 m above the car roof. |
| U-6 | BmAK's press/hold window and first-press behaviour | body stores a timestamp but no window constant; `CantEjectFromBatmobile`'s condition undecoded | Two A presses 0.2 s apart: eject happens on the second — pass if a single press does not eject. |
| U-7 | which high-speed exit wins (roll-out vs para) | both pass gate 5..999 with no other condition; native selection | Hold A at 5+ units: the chute state plays, not the side roll — pass if the chute appears on the first attempt. |

---

## 7. Checks run, and the limits

**Read for this card (static):** `CLASS_DEFAULTS.md` (`EjectUpDist` 1300.0 @6032, `ShortRangeGlideKickRange`
2500.0 @6848, `MaxEjectType` `EBET_NormalEject` @5902, the six `Eject*Move` defaults, `GlideInMove`/
`GlideBoostInMove`), `SAMPLER_FIELDS2.md:112-120`, `EJECT_MOVE.md` (root motion 764.945/949.433 cm,
113/114 frames @30 fps, the 55-sequence census), `EJECT_VELOCITY.md` (the zero vector and its receiver),
`EJECT.md` §3/§5/§6/§8, `EJECT_MAP.md` §2/§3/§3.1/§3.2/§6, `INTERACTION.md:47`, `SEAT.md:12-44`,
`INPUT.md:74,81-84,223,261`, `INPUT_D11.md`, `review-JC3-EJECT.md`, `DRIVERLEFT-regions.md`,
`WEAPONS.md:513-517`, `STANDALONE.md`.

**Not run:** no build, no `.epe`/`.effc` write, no `--check` of any card, no game. Every number above is
a file value or an arithmetic step shown next to it. The four-quantity match in §4 is a static
comparison; the two arithmetic conflicts (speed floor vs 2.05 m/s, para-at-t0 vs 3.73 s) are the
finding, and they are the reason the recipe authors height and delay rather than a velocity.

**Two stale cells corrected in passing, not edited at source:** `EJECT.md` §6 and §8.6 say
`EjectUpDist` "has no value in the grab" — `CLASS_DEFAULTS.md:143,454` now carries **1300.0**, so that
sentence is out of date; and `EJECT.md` §5's "0 launch members" holds (re-verified in
`review-JC3-EJECT.md` against 4,839 exits). The source files were left untouched.

## 8. Files and revert

| file | change | revert |
|---|---|---|
| `tmp/freebuff/reports/eject-and-glider-landing-plan.md` | **new** (this report) | delete it |

Read-only: `Research/BatmobileGrab/{EJECT_MOVE,EJECT_VELOCITY,CLASS_DEFAULTS,SAMPLER_FIELDS2,OFFSETS}.md`,
`Research/JC3Grab/{EJECT,EJECT_MAP,EJECT_REVIEW,SEAT,INTERACTION,INPUT,INPUT_D11,STANDALONE,WEAPONS}.md`,
`Research/Epe/serpente_civilian.xml` (referenced, not modified),
`tmp/freebuff/reports/{review-JC3-EJECT,review-JC3-SEAT,DRIVERLEFT-regions}.md`.
No module, `.epe`, game file, ledger row, backlog or tracker was changed; nothing was launched.
