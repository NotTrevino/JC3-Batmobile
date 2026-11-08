STATUS: done

# Exit and eject — the ordered build steps, taken from the donor's exits (MOD-3)

Card scope: the Batmobile's **exit** (LB) and **eject** (hold A), as an ordered build sequence:
which donor exit is copied, which gates and speeds become BmAK values, where the launch arc comes
from, the camera and animation handoff, and what the three Q-1 probes settle.

**Sources, cited not re-derived:** `Research/JC3Grab/EJECT.md` (26 donor exits, gates, positions — the
card's `reports/G2-20.md`), `EJECT_MAP.md` (the button table and the BmAK body, 24/24 checks),
`EJECT_REVIEW.md` (engine eject names exist, no data references them), `INTERACTION.md` (which objects
carry their own world), `SEAT.md` (where the pose is chosen), `Research/BatmobileGrab/EJECT_MOVE.md`
(the glide kick's root motion), `CLASS_DEFAULTS.md` (`EjectUpDist` 1300.0, `ShortRangeGlideKickRange`
2500.0, `MaxEjectType`), `CAMERA.md` (`R3rdPersonCamera` rules), and the donor `.epe` itself
(`tmp/g3_11b/epe.xml` line numbers below are that converted file).

**New in this card:** the *ordering*, the statement that **no gate can be set to a BmAK value because
BmAK has no eject speed threshold**, the finding that **an exit carries no world matrix and so moves
only by its parent `PointNode`** (which makes the launch height a node edit, not an exit edit), and the
camera handoff as it actually ships in the `.epe` (`ExitLeftFramingCamera`/`ExitRightFramingCamera`).

Labels: **decoded** = read from a file (path, offset or line given); **decoded (fleet)** = counted
across the 232 vehicle dumps; **derived** = computed here from decoded facts, rule stated;
**operator-stated** = the operator's statement, no file; **UNKNOWN** = not decodable here, with the
file that would settle it and one pilot card with a pass band.

**Not done:** no game launch, no build write, no `.epe`/module edit, no ledger/backlog/tracker edit.
Only this file was created (revert = delete it).

---

## 0. The answer in eight lines

1. **The exit copied is `exit.driver.moving.parachute`** → state `S_EXIT_VEHICLE_PARA`, parent
   `point.driver`, gate **(5.0, 999.0)** — **decoded** (donor `.epe`; `EJECT.md` §2–§3). It is the
   donor's own exit, already parented to the seat point, so the copy is a **re-parent, not a new
   author**: 0 of 4,832 exits carry a launch member, and 0 of 26 donor exits carry their own world.
2. **No gate and no speed is set to a BmAK value, because BmAK has none.** BmAK's eject gates are a
   call (`CantEjectFromBatmobile`, condition undecoded), a space query
   (`CheckSpaceAboveBatmobileCockpit`) and a boolean (`BoostingOut`); its **only numeric eject value**
   is `EjectUpDist` **1300.0** — a distance, not a threshold — **decoded** (`CLASS_DEFAULTS.md:143`).
   The donor's **5 / 3 split** stays as shipped: driver side 5 (0..5 plain, 5..999 fast), passenger
   side 3 (0..3 pulled-out, 3..999 roll-out) — **decoded** (`EJECT.md` §3).
3. **The launch arc comes from BmAK, not from JC3.** The three sweeps in `EJECT.md` §5 are all
   negative (0 launch members in 4,832 exits; 2 of 104 classes name motion and neither moves the
   driver; 1 hit in 232 module graphs and it is `TrainGlobal.crashing_impulse`) — **decoded (fleet)**.
   The arc is therefore BmAK's two decoded numbers: **13.0 m up** (`EjectUpDist` 1300.0 × 0.01,
   **derived** cm convention) and **7.649 m forward over 3.7333 s** (`GlideKickShort_FromBatmobile`
   root motion 764.945 cm / 113 frames @ 30 fps — **decoded**, `EJECT_MOVE.md` §4).
4. **The height is a `PointNode` edit, not an exit edit.** Only `point.*` and `trigger.*` carry a
   `world` matrix (15 of 85 interaction objects); the other 70 inherit, and **all 26 exits are in the
   inheriting set** — **decoded** (`INTERACTION.md` §2). So the build clones `point.driver` as
   `point.driver.eject` and re-parents one exit; it does not touch the exit's own fields.
5. **Camera:** the donor already ships `ExitLeftFramingCamera` / `ExitRightFramingCamera`
   (`CCameraObject`, FOV **50**, `lifetime` **0.7 s**) with `CCameraModifier` →
   `exit_left_framing.ctune` / `exit_right_framing.ctune` and a `CCameraTransitionCollection`
   containing `VehicleToExit` — **decoded** (`tmp/g3_11b/epe.xml:2705-2760`, `2843-2894`). Nothing is
   authored for the camera; the build keeps the pair and hands back to `bat_base.ctunec` after 0.7 s.
6. **Animation:** the exit hands the game one string, `S_EXIT_VEHICLE_PARA`, which is wired **twice**
   in `rico_base.afsmb` (@254304) and has the clip `PPparachute_vehicle_eject` (@180702 in
   `rico_base.asb`) plus the per-class `rico_vehi_car_low_driver_to_parachute.ban` (@727306) —
   **decoded** (`EJECT_MAP.md` §3.2). The exit itself holds no clip reference, and the driver exits
   carry **no `modifier`**, so no `MOD_*` is added (**decoded**, donor `.epe`).
7. **The three Q-1 probes decide the only two build choices that are still open:** whether the 13.0 m
   node stays (Q1-EJ-A), whether the para exit is the one the game offers at speed (Q1-EJ-B), and
   whether the eject ends in a glide or a fall (Q1-EJ-C) — §7.
8. **Everything else in the sequence is a copy of shipped data**, so the build's risk sits in four
   places only: the 13.0 m placement, the exit-point transform (R2), the gate unit (never converted),
   and the car's speed after the exit (BmAK zeroes it, JC3 has no member).

---

## 1. The donor exits this sequence uses (build input)

Positions are `EJECT.md` §2 / `INTERACTION.md` §2. **The Batmobile column is G2-18's bbox mapping and
is explicitly not the R2 build transform** — the build re-places with `bat_assemble.T(p)`; the mapped
number is used here only to show the point is inside the body.

| exit | state | gate (parent speed) | conditions | donor xyz (m) | G2-18 Batmobile (m) | role in this sequence | evidence |
|---|---|---|---|---|---|---|---|
| **`exit.driver.moving.parachute`** | `S_EXIT_VEHICLE_PARA` | **5..999** | `ParentVelocityCondition` (5,999)<br>`ExitObstructedCondition` (check 0) | −0.440, 0.340, 0.200 | −0.578, 0.598, 0.392 | **the eject / hold-A carrier — the one copied and re-pointed** | decoded (donor `.epe`; `EJECT.md` §2) |
| `exit.driver.default` | `S_EXIT_VEHICLE` | 0..5 | `ExitObstructedCondition` (check 0)<br>`ParentVelocityCondition` (0,5)<br>`UserIsPlayerCondition` (check 1) | same | same | LB exit at rest | decoded |
| `exit.driver.roll.out` | `S_ROLL_OUT_EXIT_VEHICLE` | 5..999 | `ParentVelocityCondition` (5,999) | same | same | the fast exit that can **starve** the eject — Q1-EJ-B | decoded |
| `exit.driver.to.fall` | `S_EXIT_VEHICLE_TO_FALL` | 0..5 | `ParentVelocityCondition` (0,5)<br>`ExitObstructedCondition` (check 0) | same | same | at-rest alternate; kept unchanged | decoded |
| `exit.ai.driver.to.hood` | `S_EXIT_DRIVER_TO_HOOD_VEHICLE` | — | `ParentIsUpRightCondition` (check 1) | same | same | press-A "jump to roof" (JC3's first press, `EJECT_MAP.md` §4) | decoded |

The other 21 exits (AI driver variants, passenger side, stunt, swim, upside-down, pulled/pushed out)
are copied **unchanged and untouched**. They matter because they share the same seat point: any edit to
`point.driver` moves all of them, which is why the height goes on a **clone**.

Fleet context that bounds the copy: `exit.driver.moving.parachute` is on **221 of 232** vehicles and on
every class with a driver, so it is the generic "leave at speed" exit, not a car special —
**decoded (fleet)** (`EJECT.md` §4).

---

## 2. The ordered build steps

Target tree: `Builds/<tag>/aaff/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/`,
entity `…_civilian_01.ee` (or whatever the live tag's entity is). Steps 1–3 are pure copies; step 4 is
the only new object; steps 5–11 are decisions, not edits.

| # | step | object / file | value | evidence level |
|---:|---|---|---|---|
| 1 | copy the donor's 26 exits **verbatim** into the build `.epe`, names and states unchanged | build `.epe` graph | 26 exits, 61-name vocabulary | **decoded** (donor `.epe`; `EJECT.md` §2) |
| 2 | re-place `point.driver` for the Batmobile with the one transform | `point.driver` world | donor −0.440, 0.340, 0.200 → build `T(p)` | **derived** (R2 rule; G2-18 map is analysis) |
| 3 | keep every exit parented to `point.driver`; add no `world` to any exit | 26 exits | 0 world matrices added | **decoded** (15/85 own a world, all `point.*`/`trigger.*`) |
| 4 | clone the seat node and re-parent **one** exit to it | new `point.driver.eject`; `exit.driver.moving.parachute` | seat point + **13.0 m** local up | **decoded value + derived unit + derived placement** |
| 5 | leave all gates at donor values | the 7 gated exits | 5 / 3 split unchanged | **decoded** (donor; no BmAK threshold exists) |
| 6 | map the two BmAK conditions that have carriers; add neither `enabled=0` nor a new condition | `ExitObstructedCondition`, side framing | keep as shipped | **decoded** |
| 7 | do not zero the car's speed on exit; declare the divergence | — | none | **decoded** (BmAK `(0,0,0)`; JC3 has 0 members) |
| 8 | author the arc as placement only, not as velocity | `point.driver.eject` (step 4) | up 13.0 m; forward = inherited | **derived** from decoded BmAK numbers |
| 9 | hand the animation off by state string; add no `modifier` | `S_EXIT_VEHICLE_PARA` | `modifier` stays null | **decoded** |
| 10 | keep the shipped exit-framing camera pair; no camera edit | `ExitLeft/RightFramingCamera` | FOV 50, lifetime 0.7 s | **decoded** |
| 11 | freeze the sequence offline: read the built `.epe` back against the donor | build `.epe` | 26 exits, 1 re-parented, 25 unchanged, gates identical | **derived** (diff check) |

### Step 1 — copy the donor's exit block

The build copies `exit.driver.moving.parachute` and its 25 siblings **by name and state**, not by
re-authoring. The reason is the contract: an exit's behaviour is the **state string** it hands the
game, and that string is wired character-side (`rico_base.afsmb`). Authoring a new exit name would
point at a state nothing carries — the engine's own eject names (`ACT_EJECT_FROM_VEHICLE`,
`S_EJECT_FROM_VEHICLE_ALIVE/DEAD`) are present in `JustCause3.exe` and referenced by **0** of 1,170
scanned data files — **decoded** (`EJECT_REVIEW.md` §4–§5).

### Step 2 — the seat point is the R2 transform's, not G2-18's bbox mapping

G2-18 scaled the Serpente deform envelope onto the Batmobile bbox (factors 1.3139 / 1.49 / 1.3809) to
answer "inside or floating". That is an analysis frame and `INTERACTION.md` says so in its own header
("analysis only, **not** the R2 build transform"). The build writes the seat point through
`Tools/scripts/bat_assemble.py` `T(p) = to_jc3(p) × 0.01 + offset` like every other anchor —
**decoded rule (R2)**, value **derived** at build time.

**UNKNOWN:** the final millimetre value of `point.driver` in the built entity. Settling file:
`Working/TrueScale/stations.json` + `Tools/scripts/bat_assemble.py` (run gives it); it is not a number
this card may quote.

### Step 3 — an exit has no world, so it moves only with its node

`INTERACTION.md` §2: **15 of 85** interaction objects carry their own `world` matrix and all of them
are `point.*` / `trigger.*`; the other **70 inherit**, including every `exit.*` — **decoded**. This
settles the earlier open question "can an Exit override the inherited point?" (the
`eject-and-glider-landing-plan.md` U-1): **no, it has no field to override with.** The lever is the
parent node. Adding a `world` to an exit would be a shape no shipped object uses.

### Step 4 — the 13.0 m node (the only new object)

`EjectUpDist` = **1300.0** (`RVehicleBatmobileBase`, FloatProperty, off 6032 / `0x1790`) — **decoded**
(`CLASS_DEFAULTS.md:143,454`). Unit not printed; the cm reading is the convention every other BmAK
length in this grab uses (`CAMERA.md` 400 cm boom, `EJECT_MOVE.md` cm root motion) → **13.0 m,
derived**. What applies it is native (`ModifyEjectUpLoc` / `SetBatmobileExit`, `EJECT.md` §6), so the
number is a placement, not a velocity.

Build: clone `point.driver` as `point.driver.eject`, `world.translation = point.driver.world + 13.0 m
× car-local up`, and re-parent **only** `exit.driver.moving.parachute` to it. The other 25 exits keep
the seat node — **derived** from step 3's decoded shape.

**UNKNOWN:** whether a `PointNode` above the car makes the *player* start there or is only a
placement test point. Settling file: none in data (the node's consumer is native); probe **Q1-EJ-A**
decides, and if the player appears at seat height the node is a test point and the height must be
**dropped**, not faked.

### Step 5 — gates and speeds: what is set to BmAK, and what is kept

This is the card's sharpest negative. BmAK's eject has **no speed threshold**:

| gate | donor value | BmAK value | build action | why | evidence |
|---|---|---|---|---|---|
| `exit.driver.default` | 0..5 | none | **keep 0..5** | BmAK has no eject speed member; the only numeric is `EjectUpDist` | decoded (absence: `EJECT_MAP.md` §2 table has no speed row) |
| `exit.driver.to.fall` | 0..5 | none | **keep 0..5** | same | decoded |
| `exit.driver.roll.out` | 5..999 | none | **keep 5..999** | same; also the starver for Q1-EJ-B | decoded |
| `exit.driver.moving.parachute` | 5..999 | none | **keep 5..999** | same | decoded |
| `exit.passenger1.pulled.out` | 0..3 | — | **keep 0..3** | passenger side, not MOD-3 | decoded |
| `exit.passenger1.roll.out` | 3..999 | — | **keep 3..999** | same | decoded |
| car speed **after** the exit | inherited | **0** (`SetRBLinearVelocity((0,0,0))` on `Car.Core.Mesh`, `FFInRange` branch, +513) | **no edit — declared divergence** | JC3's exits carry 0 motion members; nothing can zero the parent | decoded (BmAK) / decoded absence (JC3) |
| battle-mode "no eject while moving" (operator: boost instead) | — | `BoostingOut` byte, 6 refs, branch undecoded | **out of scope** (MOD-2 / D-2) | needs the mode split before a speed-dependent eject rule can exist | operator-stated + decoded refs |

**Do not convert `5` to km/h.** The condition's unit is stated nowhere in the file and no conversion
exists — **UNKNOWN**, settling file: `JustCause3.exe` (`CInteractionGraphParentVelocityCondition`
consumer, not decoded). Quoting a m/s threshold would be the substitution `AGENTS.md` forbids.

The two conditions that *do* have a carrier, mapped 1:1:

| BmAK gate | member | JC3 carrier | status |
|---|---|---|---|
| `CheckSpaceAboveBatmobileCockpit()` (+173) | native | `ExitObstructedCondition` (check 0) — already on `moving.parachute` **and** `default` | **decoded** present; semantics of "check 0" UNKNOWN |
| `bCanGetOutOnLeftSide` (`0x11e0`) | BoolProperty | side framing pair + `exit.driver.*` side vocabulary | **decoded** (member + objects exist) |
| `bPreventBatmbileExit` (`0x11dc`) | BoolProperty | **none** — every one of the 4,832 fleet exits is `enabled=1`; `0` never appears | **decoded absence**; do not invent an `enabled=0` row |
| `CantEjectFromBatmobile` (+3) | native | none | condition **UNKNOWN**, settling file: `BmGame.upk` body of `CantEjectFromBatmobile` (not decoded) |

### Step 6 — the arc's provenance

The card asks where the launch arc comes from, so state it as provenance, in order:

1. **Not from JC3 data.** `EJECT.md` §5's three sweeps: exits 0/4,832 with a velocity/impulse/force
   member; graph classes 2/104 name motion (`CInteractionGraphParentVelocityCondition` is a *gate*,
   `CForcePulse` pushes off the **car**); vehicle modules 1/232 hits
   (`TrainGlobal.crashing_impulse`) — **decoded (fleet)**. The review adds `bail` and lowers it to the
   same single hit; the widened `veloc` lens reads 33 members, every one acting on the vehicle body
   (tyre slip, buoyancy, drift rotation, `RigidBody.max_linear_velocity`) — **decoded**
   (`EJECT_REVIEW.md` §2).
2. **Up: BmAK's `EjectUpDist`** 1300.0 → **13.0 m** (derived cm), applied natively as a placement.
3. **Forward: BmAK's glide kick** — `GlideKickShort_FromBatmobile` root translation **764.945 cm
   (7.649 m)**, vertical **0 cm**, **113 frames @ 30 fps = 3.7333 s**, mean **204.9 cm/s** — **decoded**
   (`EJECT_MOVE.md` §4). The mid-range variant bounds the pair at **949.433 cm / 3.7667 s**, chosen at
   runtime by `PickRandomAnim` — **decoded** (choice logic UNKNOWN).
4. **On the Batmobile: only (2) is authorable.** (3) has no carrier: it is root motion on a character
   animation that JC3 does not have, and the exit inherits the car's velocity instead. So the built
   arc is **"place 13.0 m up, then inherit car velocity + gravity"**, not "13.0 m up then 7.649 m at
   2.05 m/s". The 7.649 m is recorded as the **target the exit clip would have to travel** if a clip
   ever carries it — it is not written anywhere in this build.

**UNKNOWN:** the kick's per-frame curve (the keyframe block is zip-compressed, 28,812 of the export's
29,672 bytes). Settling file: `AnimSequence` `Batmobile_Short_Range_Glide_Kick` field 108's compressed
block in `Startup.upk` (EJECT_MOVE §6). Only the total and the mean are quotable.

### Step 7 — the animation handoff

Order of handoff, BmAK → JC3:

| # | BmAK step (script offset in `EjectFromVehicle`) | JC3 counterpart | carrier file | evidence |
|---:|---|---|---|---|
| a | seat release `DriverLeave(true, …)` +365; binds swap +424 | exit object fires, state string `S_EXIT_VEHICLE_PARA` | donor `.epe` exit; `rico_base.afsmb` @254304 (2 refs) | decoded |
| b | `PlayCockpitOpenFast()` +443 (clip `Cockpit_Open` 14 f / **0.433 s**) | canopy hinge (MOD-4 / T-12), not this sequence | `ANIMATIONS.md` via the entry/exit card | decoded |
| c | `TriggerSpecialMove(Car.ShortRangeGlideKick)` +1103 | nothing — the state is the whole handoff | `EJECT_MOVE.md` §1 | decoded call, trajectory gap |
| d | move names end `_To_Glide`; body refs `CapeGlideTarget` +1254 / `AttackGlide` +1266 | clip `PPparachute_vehicle_eject` @180702; per-class `rico_vehi_car_low_driver_to_parachute.ban` @727306 | `rico_base.asb` | decoded names |

**Build rule:** the exit's `modifier` stays **null**. The donor's seven driver exits all carry no
modifier, while the passenger rows carry `MOD_RIGHT` / `MOD_LOW_RIGHT` — **decoded** (donor `.epe`,
`EJECT.json`). The fleet has exit-specific selectors (`MOD_CAR_EXIT_ROLL` 9, `MOD_CAR_EXIT_RIGHT_ROLL`
9, `MOD_RIGHT` 1136, `MOD_LOW_RIGHT` 182) — **decoded (fleet)** — but which class this car is given is
native, and putting one on the eject exit would be an invention with a visible failure mode (a class
selector the car does not resolve to = no exit).

**UNKNOWN:** which pose family plays (bare `car` 2 clips, `car/low` 23, `car/med` 35, `car/circuit` 9).
Settling file: `rico_base.afsmb` class selectors (36 `MOD_*`, string table decoded, choice logic not);
pilot card C1 watches whether Rico's hands land on the Batmobile yoke.

### Step 8 — the camera handoff

The carrier ships **inside the mod's own `.epe`**, which is why this step has no author work:

| object | class | values | evidence |
|---|---|---|---|
| `ExitLeftFramingCamera` | `CCameraObject` | `FOV` **50**, `lifetime` **0.7**, `default` 0, DOF 0/1 | decoded (`tmp/g3_11b/epe.xml:2705-2735`) |
| `ExitLeftFraming` | `CCameraModifier` | → `…/framing/exit_left_framing.ctune` | decoded (line 2734) |
| `ExitRightFramingCamera` | `CCameraObject` | same values | decoded (line 2843+) |
| `ExitRightFraming` | `CCameraModifier` | → `…/framing/exit_right_framing.ctune` | decoded (line 2875) |
| `CCameraTransitionCollection` | collection | `VehicleToExit`, `ReelInToAction` (+ `ReelIn` link, 1 / 0) | decoded (lines 2752-2760) |
| framing tunes | `SphericalCoordinateFramingParams` | 11 rows, 685 / 686 B | decoded (`FX.md` root-class census) |

Handoff order therefore is: exit state → the side's framing camera activates (FOV 50) → holds
`lifetime` **0.7 s** → the car camera (built `bat_base.ctunec`, CAM-1: 7.00 m back / 1.30 m up /
FOV 55…63) resumes.

BmAK's side, for comparison: the special move's parent body pushes its own camera
(`TunnelCamera()` +2991, `SetCameraState()` +3249 — **decoded calls**, state name UNKNOWN), and
`R3rdPersonCamera` carries **13** configs, of which the nearest are `GlideInBatmobileCamConfig` and
`DiveToBatmobilePickupCamConfig` (**entry** cameras) — **decoded** (`CAMERA.json`). There is **no
`Eject*` camera config**, so BmAK's eject camera state has no BmAK name to copy.

**UNKNOWN:** which of the two framing cameras an eject with no side uses. Settling file: the
`Activate` event ids on the two `CCameraObject`s in the donor `.epe` (`597B6EAC=FFFFAD38` left,
`91F86276=FFFFB681` right — decoded ids, no emitter decoded); pilot card C2 sees which side the camera
sits on.

### Step 9 — the control side (only the part the sequence needs)

`A` runs `EjectFromVehicle` on exactly one ini line (`DefaultInput.ini:267`); the menu labels it
`A, A` = "Eject Into Glide" and `LB` = "Exit Batmobile" — **decoded** + **operator-stated**
(`EJECT_MAP.md` §2, §5). JC3's export puts `OPEN_PARACHUTE`, `STUNT_JUMP` and `JUMP` on the same **A**
(shipped table: `RPADDOWN`, 0 face buttons) — **decoded**.

So: **hold A = the eject**, and its vehicle-context gate is the exit graph's own speed condition, not
an input action. Nothing in the keymap can express "hold" (474 bindings parsed, 0 hold/duration
fields) — **decoded absence**; the press/hold split is the **game's menu**, not the file.

**UNKNOWN:** the hold threshold and whether the shipped or the exported table is live. Settling files:
`settings/keymap_gamepad.bin` (shipped) vs the player's `kepmap.txt` export — they disagree on the
control, and neither carries a duration; only a runtime observation settles it.

### Step 10 — freeze the sequence offline

Before any probe, read the built entity back and diff it against the donor:

| check | pass |
|---|---|
| exit count | **26** in, **26** out, same names and states |
| parents | **1** exit re-parented (`moving.parachute` → `point.driver.eject`), **25** still on `point.driver` |
| world matrices | **0** added to any `exit.*`; **1** added (the clone) |
| gates | all `min`/`max` pairs byte-identical to the donor |
| modifiers | driver exits still null; passenger rows unchanged |
| camera | `ExitLeft/RightFramingCamera` + both `CCameraModifier`s + the transition collection present, FOV 50 / lifetime 0.7 |
| heights | `point.driver.eject` = seat point + **13.0 m** along local up, no other node moved |

The tool is the `.epe` writer/reader used by build D-05 (`Tools/scripts/bm_entity.py`); the diff is a
text compare of the converted XML, not a new checker. **Derived** check, no new value.

---

## 3. The three Q-1 probes: what each confirms, and which build choice it owns

All three run on the **unmodified donor car first** (phase Q, batched per R13 note: they are
independent — A measures the exit's own pop, B which exit was offered, C what the chute does; none
changes another's variable). `EJECT.md` §8 is the design; this card adds what each one *decides in the
build*.

| probe | method | hypothesis / reading | what it decides in this build |
|---|---|---|---|
| **Q1-EJ-A** — is there an upward impulse in the exit itself? | exit at a steady speed **8 units** (comfortably over the 5 floor), flat ground, no input after | H1 no launch: vertical velocity ≤ 0 within **0.2 s**, apex **0.0 m ± 0.2 m** above the exit point. H2 launch: vertical velocity > 0 and apex **> 1.0 m** | **H2 → drop step 4's node entirely** (the game already launches; a node would double it). **H1 → keep the node, or declare the launch lost** if the node turns out to be only a test point |
| **Q1-EJ-B** — which fast exit wins? | exit at just over the gate, same run as A | `S_ROLL_OUT_EXIT_VEHICLE` (side roll, no chute) **or** `S_EXIT_VEHICLE_PARA` (chute state) — both pass gate 5..999 with no other condition, so the data does not choose | if the **roll-out** plays, `exit.driver.moving.parachute` is never offered at speed and step 1's carrier is unreachable: the eject must be re-pointed to the roll-out state, or `roll.out` re-gated. If the **para** plays, the copy stands |
| **Q1-EJ-C** — is the chute automatic? | same run, no input at all after the exit | H3 the chute opens by itself; H4 it needs the usual `OPEN_PARACHUTE` input | decides whether the eject's second half (BmAK's `_To_Glide`) is reachable from `hold A` alone or needs a second input; H4 means the "eject into glide" label is only half carried |

**One launch, one variable (R13).** A measures the exit's own vertical motion with no input; B reads
which state played in the *same* run (it costs no extra launch — the two outcomes look different);
C is the input-free tail of the same run. If the phase-Q batch must split them, C goes last because it
is the only one that changes what the player does after the exit.

---

## 4. Pilot cards (one sentence each, with the band that passes)

**C0 — the 13.0 m placement (only if H1 from Q1-EJ-A holds).**
Exit at speed with the 13.0 m node in the build: Rico must appear **13.0 m ± 1.0 m** above the car roof
at the exit, and **every other exit must still start at the seat** (±0.2 m) — pass if the offset
appears on the eject alone and no other exit moves.

**C1 — the animation handoff.**
Exit at speed and watch the body: the parachute-eject clip must play (airborne pose, no seated
wheel-hold) and Rico's hands must be within **±0.15 m** of the Batmobile's yoke grip while seated —
pass if the clip plays on 3/3 and the seated pose is not the Serpente's low-car pose frozen in place.

**C2 — the camera handoff.**
Exit at speed and watch the frame: the camera must switch to the exit framing (FOV **50** per the
`CCameraObject`, narrower than the built chase's 55…63) and return to the chase **0.7 s ± 0.2 s**
after the exit — pass if the framing is visible on 3/3 and the return lands inside the band.

**C3 — the gates stay BmAK-honest.**
Exit once at rest and once at just over the gate, and report which state played each time: at rest
`S_EXIT_VEHICLE` (plain), at speed `S_EXIT_VEHICLE_PARA` (or the roll-out, per Q1-EJ-B) — pass if the
state matches the gate's side on 3/3 each, and **fail if the plain exit plays above the gate** (that
would mean the copy lost its condition).

**C4 — the divergence is visible and accepted.**
Eject at 60 km/h and release everything: the car must **keep rolling** (BmAK zeroes it) — pass if the
car's speed after 2 s is ≥ 80 % of its speed at the exit, recorded as the accepted divergence; anything
else is a surprise that would reopen step 5's row.

---

## 5. UNKNOWNs, and the file that settles each

| # | UNKNOWN | why it blocks nothing today | settling file |
|---|---|---|---|
| U1 | the gate's unit (5 / 999 / 3) | the build keeps donor numbers; only a conversion would need it | `JustCause3.exe`, `CInteractionGraphParentVelocityCondition` consumer (not decoded) |
| U2 | whether a `PointNode` above the car places the player or is only a test point | step 4 is revertible by one node delete | native `PointNode` consumer (not decoded); **Q1-EJ-A** |
| U3 | which fast exit wins (roll-out vs para) | both are shipped; the build keeps both | exit selection code (not in data); **Q1-EJ-B** |
| U4 | whether `S_EXIT_VEHICLE_PARA` opens the chute by itself | the exit only names a state | `rico_base.afsmb` transition body (string table decoded, body not); **Q1-EJ-C** |
| U5 | BmAK's eject camera state name | no data file needs it; JC3's framing camera ships | `Research/BatmobileGrab/CAMERA.json` — 13 configs, **no `Eject*`**; the name would be in `BmGame.upk` `Default__R3rdPersonCamera` and is absent |
| U6 | which pose family plays (`car/low` vs `car/med`) | the exit's state is correct either way; only the look differs | `rico_base.afsmb` class selectors (36 `MOD_*`); **C1** |
| U7 | whether any JC3 path zeroes the parent's velocity on exit | BmAK's stop is cosmetic next to the exit itself | `JustCause3.exe` exit consumer; **C4** |
| U8 | the press/hold threshold (and which keymap table is live) | the sequence works on the exit graph, not on a hold timer | `settings/keymap_gamepad.bin` / `keymap_keyboard.bin` vs `kepmap.txt`; neither has a duration field, so only a runtime observation settles it |
| U9 | `CantEjectFromBatmobile`'s condition (+3) | it guards an eject that JC3 does not have as a call | `BmGame.upk` body of `CantEjectFromBatmobile` (not decoded) |
| U10 | the glide kick's per-frame curve | the build carries none of it | `Startup.upk` `Batmobile_Short_Range_Glide_Kick` field 108 compressed keyframe block (EJECT_MOVE §6) |
| U11 | the two `ExitObstructedCondition` "check 0" semantics | the donor ships the condition and the build copies it | `JustCause3.exe` condition consumer (not decoded) |

None of these is written as "JC3 has no system": each names the closest shipped thing and the file or
card that closes it (`STAGES.md`).

---

## 6. Checks run, and what was not

**Read for this card:** `Research/JC3Grab/EJECT.md` (full), `EJECT_MAP.md` (full, incl. its 24/24
check table), `EJECT_REVIEW.md` (§2–§7), `INTERACTION.md` §1–§2, `SEAT.md` §1–§4, `EJECT.json`
(26 donor exits: names, states, `modifier`, gate pairs), `Research/BatmobileGrab/EJECT_MOVE.md` (full),
`CAMERA.md` §1–§2b, `CLASS_DEFAULTS.md:87-94,143,149,220`, the converted donor `.epe`
`tmp/g3_11b/epe.xml` (lines 2700-2760, 2840-2894: the two framing cameras, their modifiers, the
transition collection), `Research/JC3Grab/FX.md` (`.ctunec` root-class census),
`tmp/freebuff/reports/eject-and-glider-landing-plan.md` and `entry-exit-and-controls-plan.md`
(cited for the numbers they already own).

**Verified this session, not quoted:** the donor exit list with each `modifier` (`exit.driver.*` all
null; `exit.ai.passenger1.*` and `exit.passenger1.default` / `.pulled.out` `MOD_RIGHT` /
`MOD_LOW_RIGHT`; `exit.passenger1.roll.out` `MOD_RIGHT`), the absence of any `Eject*` camera config in
`CAMERA.json`, and the two framing `CCameraObject`s' values (FOV 50, lifetime 0.7) in the converted
donor `.epe`.

**Not run:** no build, no `.epe` write, no module write, no `--check` of any generated card, no game.
The steps are a plan; step 10 is the check that would prove them, and it has not been executed because
no build tree was written. No number here is an estimate: each is a file value or an arithmetic step
shown next to it (1300.0 × 0.01; 764.945 cm / 3.7333 s).

**Known divergence from `EJECT.md`:** its §6/§8.6 call `EjectUpDist` "no value in the grab"; the value
is **1300.0** (`CLASS_DEFAULTS.md:143,454`) and is used here. The source file was not edited.

---

## 7. Files and revert

| file | change | revert |
|---|---|---|
| `tmp/freebuff/reports/eject-sequence-build-steps-from-donor-exits.md` | **new** (this report) | delete it |

Why this file: the card asks for the build steps as a report, and `tmp/freebuff/reports/` is where
every other card's plan lives (`eject-and-glider-landing-plan.md`, `entry-exit-and-controls-plan.md`,
`air-control-closest-system-plan.md`). Nothing else was touched: no `.epe`, no module, no ledger row,
no backlog or tracker edit, no game launch.
