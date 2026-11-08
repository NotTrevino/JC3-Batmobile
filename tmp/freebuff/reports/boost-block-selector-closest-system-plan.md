# The boost-block selector — the build plan that closes T-MD14b's "no selector"

WHAT THIS IS: `tmp/freebuff/reports/T-MD14b.md` decoded three parallel boost blocks on one module and
correctly refused to call Pursuit/Battle expressible: the blocks exist, nothing selects them. Per the
project rule (`closest-system-rule`), the gap is closed by a build, so this file designs the selector:
which block carries Pursuit, which carries Battle, what (if anything) already flips them in JC3, and
what the build adds where nothing does.

WHAT THIS IS NOT: another census. The fleet scan, the member vocabulary, the offsets and the variant
pattern are taken as read from `T-MD14b.md`, `mode-switch-carriers.md` and
`Working/Translation/T-MD14B_STATES.{md,json}`; this file only assigns and builds.

## 1. The three blocks, as shipped (decoded)

| module | build count | block | offset | struct | size |
|---|---:|---|---:|---|---:|
| `CustomLandGlobal` (land) | 145 | `arcade.heat_boost` | 136 | `PerformanceBoost` | 20 B |
| | | `arcade.nitro_boost` | 156 | `PerformanceBoost` | 20 B |
| | | `arcade.nitro_boost_upgraded` | 176 | `PerformanceBoost` | 20 B |
| `AirGlobal` (air) | 41 | `nitro_boost` / `_upgraded` / `heat_boost` | 120 / 132 / 144 | `AirPerformanceBoost` | 12 B |
| `BoatGlobal` (boat) | 35 | the same three | — | — | — |

`PerformanceBoost` members (decoded, `Working/Translation/T-MD14B_STATES.md`): `torque_multiplier` @0,
`grip_multiplier` @4, `push_force` @8, `boost_blend_time` @12, `extra_top_speed` @16. **Five members,
no cap, no steering angle, no enable flag** — that absence is what shapes the whole design below.

Shipped land values (`mode-switch-carriers.md` §2.4):

| member | `nitro_boost` | `nitro_boost_upgraded` | `heat_boost` |
|---|---:|---:|---:|
| `push_force` | 15000 | 20000 | **0.0** |
| `torque_multiplier` | 2.0 | 2.0 | 2.0 |
| `grip_multiplier` | 1.0 | 4.26 | 4.26 |
| `extra_top_speed` (km/h) | 43.2 | 100.92 | 100.92 |
| `boost_blend_time` (s) | 0.2 | 0.2 | **0.0** |

Offset note (caveat, not a claim): `T-MD14b` gives `arcade` @136 **and** `heat_boost` @136 while the
next two blocks are 20 B apart (156, 176). That reads as `heat_boost` being the first rung at the
arcade block's own start; the `.vmodc` re-read in `t_md14b.py --check` is what would confirm the parent
offset, and the build must not write a block until it does.

## 2. The assignment: which block carries which mode

| block | assigned to | why this block and not another | values to write |
|---|---|---|---|
| `arcade.nitro_boost` (156) | **Pursuit** | it is the rung the fleet actually fires: upgrade level 0, the block `B-08` proved on our graph (`EngineNitro` → `exhaust_upgrade_nitrous`), and its `grip_multiplier` 1.0 is the "no extra grip" character Pursuit has | **unchanged** (15000 / 2.0 / 1.0 / 43.2 / 0.2) |
| `arcade.heat_boost` (136) | **Battle** | it is the only rung with no shipped consumer (`push_force` 0, `boost_blend_time` 0), so rewriting it can change no vanilla vehicle's behaviour | see the table below |
| `arcade.nitro_boost_upgraded` (176) | **left alone — JC3's own upgrade rung** | its `extra_top_speed` 100.92 km/h has **no BmAK counterpart**; selling it as a mode would add speed the Batmobile never gains | untouched (20000 / 2.0 / 4.26 / 100.92 / 0.2) |

`heat_boost` for Battle, with every number traced:

| member | shipped | write | derivation | level |
|---|---:|---:|---|---|
| `push_force` | 0.0 | **15000** | copy `nitro_boost`'s push so the state has a force at all; BmAK's `BattleModeDriveForceFactor` 500 is an engine **gain**, not a force, so no BmAK number maps onto this member | derived |
| `torque_multiplier` | 2.0 | **2.0** | keep — BmAK's `BattleModeDriveForceFactor` 500 has no documented unit, and no ratio to Pursuit's 500-vs-500 pair exists (both modes ship 500) | decoded value kept |
| `grip_multiplier` | 4.26 | **1.333** | BmAK's slip pair is a *ratio*, not a grip: `BattleModeLatSlipScale` 0.75 → lateral grip 1/0.75 = **1.333**; `LongSlipScale` 1.25 → longitudinal slip **+25 %**. JC3 has one grip number, so the lateral term is the one carried. 4.26 is 3.2× the derived value and has no BmAK basis | derived |
| `extra_top_speed` | 100.92 | **0.0** | Battle never *adds* speed in BmAK — it caps it (`TurningModeMaxSpeed` 600 cm/s, `BattleModeVSpeedCurve` 60→40→30 as speed rises). A `PerformanceBoost` has **no cap member**, so the honest write is "adds nothing" and the cap goes on the entity (§4 route A) | derived (stated omission of a value) |
| `boost_blend_time` | 0.0 | **0.2** | copy `nitro_boost`'s blend so the mode arrives as a 0.2 s ramp, not a step | derived |

Why not the other way round (Battle on `nitro_boost`, Pursuit on `heat_boost`): the always-reachable
rung must hold the mode the car spends most time in, and Battle's cap cannot be carried by any rung
(no cap member), so putting Battle on the reachable rung would leave a battle car that *accelerates
faster* than pursuit with no cap — the opposite of BmAK. Pursuit on the reachable rung is also the
only assignment that changes nothing for a player who never switches (§4 route B is inert until a
selector exists).

## 3. What already flips them in JC3 — and what does not

Searched (per the brief): the 232-build member vocabulary (`T-MD14b`), the module type dictionaries,
`Research/JC3Grab/USAGES.md` §6 (the nitro chain), `EJECT.md` (the turbo-jump ladder), and the fleet's
`arcade` blocks. Findings, by evidence level:

1. **The ladder is real and it is a naming pattern, not a member.** Every block that has an upgrade
   ships as a **pair**: `arcade.nitro_boost` / `nitro_boost_upgraded`, `arcade.turbo_jump` /
   `turbo_jump_upgraded`, and — the strongest case — `VehicleMisc.turbo_jump_cooldown` **5 s** /
   `turbo_jump_cooldown_upgraded` **2 s** (`Research/JC3Grab/EJECT.md:205-215`). Two *named* members
   holding both rungs means the engine stores both and picks one. **decoded** (names + values).
2. **`heat_boost` has no companion member** — no `heat_*` cooldown, no `heat_boost_level`, no flag. It
   is the third rung of a pattern whose first two rungs have companions. **decoded absence**.
3. **The game tracks an integer boost upgrade level.** `UC_SetBoostLevel(level, upgradeLevel)` takes
   it as a second argument and shows `Upgrade1` at `upgradeLevel > 0` and `Upgrade2` at `> 1`
   (`G3-HUD-CLUSTER.md` §2, `Research/BatmobileGrab/HUD.md` §4) — so BmAK's own HUD proves a *≥3-state*
   upgrade ladder exists engine-side. JC3's HUD counterpart takes no such argument
   (`InitVehicleNitrous(recharge)`, `Research/JC3Grab/JC3_HUD_WEAPONS.md` §7), so **JC3 keeps the
   level, not the movie**. **decoded interface / derived meaning**.
4. **No data member anywhere selects a block.** `T-MD14b`'s 51-module scan: one hit
   (`AirplaneAI.Limit_Pitch_Yaw_Switch`), not a selector. **decoded absence**.
5. **Nothing keys a boost rung to a driving input.** The only handling-changing runtime state in the
   fleet is the boost itself, and it is entered by the game's own nitro input, not by a data action.
   **decoded** (`mode-switch-carriers.md` §2.4, §2.7).

**Answer to "what existing trigger flips between nitro, upgraded nitro and heat boost":** the vehicle's
**nitro upgrade level**, an engine-side integer with **one rung per block**, evidenced by the paired
`_upgraded` members (§3.1) and the `upgradeLevel` argument the HUD takes (§3.3). It is **not** exposed
as a module member, so it cannot be set from the files; and `heat_boost`'s rung is not proven reachable
at all (`push_force` 0, blend 0, no companion member). Evidence level: **derived** for the ladder,
**UNKNOWN** for heat_boost's rung. Settler for both: the boost-state consumer in `JustCause3.exe`
(not decoded); the nearest offline probe is `t_md14b.py --dump` plus a live read (§7).

## 4. What the build adds, since no selector exists

### Route A — two entities, each carrying its own rung (recommended; carries all five mode rows)

The Batmobile's `.ee` splits into `batmobile_pursuit.ee` and `batmobile_battle.ee` (the fleet's own
`_signature_shielded` / `_military_01` pattern, `mode-switch-carriers.md` §2.5). Each ships a **private
copy** of `custom_land_global.vmodc` (the `B-09`/`B-11` private-module pattern, R7):

- **pursuit copy**: `nitro_boost` as shipped; `heat_boost` rewritten per §2 is harmless because nothing
  selects it.
- **battle copy**: `nitro_boost` carries the **battle** values from §2 (so the always-reachable rung is
  battle, which is correct for a battle entity); `heat_boost` mirrors them; and the entity's own
  `LandGlobal` speed value carries the **21.6 km/h cap** (`TurningModeMaxSpeed` 600 cm/s) that no boost
  member can express.

**What the selector becomes:** *which entity you are driving*. That needs the swap trigger, which is
`B-12`'s open precondition and is planned in `tmp/freebuff/reports/mode-swap-trigger-closest-system-plan.md`
(candidate 1 `USE_VEHICLE_MOD`, candidate 2 the Rebel Drop item pair). **No new member is needed for the
block question** — this is the one route where the missing selector stops mattering.

Cost: the cap/steering ride the entity, so both entities must be kept in step; a mid-drive switch loses
velocity (a spawn cannot carry it, same report).

### Route B — one entity, `heat_boost` rewritten (in place, partial, inert until a rung is proven)

Ship §2's `heat_boost` values in the single hybrid entity. If the ladder reaches rung 2, the block is
Battle; if it never does, the write is **inert** — which is a testable, reversible state, and the reason
this route can be built *before* the selector is proven. It buys the multipliers (grip, torque, push,
blend) and **not** the cap, the steering set, turn-on-the-spot or the stance (`mode-switch-carriers.md`
§3, §5 Option B). Evidence: decoded members, derived values, **UNKNOWN** reachability.

### Route C — a gadget-driven or script-event switch (not viable in data; named rather than skipped)

- The only data path from an expression to a runtime value is `ExtendedExposedVariables` — **2
  expressions in the whole fleet**, both the speed-ramp pair (`mode-switch-carriers.md` §2.1). It drives
  an exposed variable, and **no module member consumes such a variable to pick a boost block**, so a
  "gadget writes `battle_mode_T`" build would have nothing to read it. UNKNOWN, settler: the
  `ExtendedExposedVariables` consumer in the exe (`mode-switch-carriers.md` §7 U2).
- A vehicle "gadget" in JC3 is a `SAttachedEffect`/part behaviour, not a state machine (G2-14/G2-15), so
  there is no gadget slot to hang a mode on. Decoded absence.

## 5. The numbers from the BmAK mode table (what the two copies carry)

`Research/BatmobileGrab/MODES.md` (serialised, all four packages) and `DRIVE_MODES.md` (G3-02l):

| BmAK member | value | carries in the build |
|---|---:|---|
| `TurningModeMaxSpeed` | **600 cm/s = 21.6 km/h** | battle entity's `LandGlobal` speed value (no boost member can cap) |
| `BattleModeVSpeedCurve` | **0→60, 600→40, 1200→30** | no JC3 car curve member; recorded, not carried (see the conflict below) |
| `BattleModeMaxSpeed` | **1200 cm/s = 43.2 km/h** (DRIVE_MODES; **not serialised** per MODES.md) | battle cap candidate; 43.2 km/h coincides with `nitro_boost.extra_top_speed` 43.2 — a coincidence, not a proof |
| `BattleModeMaxSteering` | **80°** (DRIVE_MODES; not serialised) | battle entity's steering limit |
| `BattleModeLatSlipScale` | **0.75** serialised (DRIVE_MODES says 4) | → `grip_multiplier` **1.333** |
| `BattleModeLongSlipScale` | **1.25** serialised (DRIVE_MODES says 10) | nothing in JC3 (one grip number only) — stated loss |
| `BattleModeSteerAngleFactor` | **1** | battle steering set |
| `BattleModeTrailingSteerFactorMoving` | **−0.25** | battle steering set (rear-axle trailing steer) |
| `BattleModeDriveForceFactor` | **500** (engine gain) | not mapped: no documented unit, and Pursuit ships 500 too |
| `BattleModeThrottleSpeed` | **10** (undocumented, rate-sized) | nothing |
| `BattleModeStopAndTurnAngleStationary` | **30°** | turn-on-the-spot (T-MD8, still needs a joint) |
| `BattleModeDrivingForceZOffset` | **20 cm** | nothing (no member) |
| `BattleModeTurnOnSpotTorqueFactor` | **0.333333** | turn-on-the-spot |
| `TurnOnSpotFrontTorqueFactor` / `Rear` | **0.8 / −0.8** | turn-on-the-spot |
| `TurnOnSpotModeEngineBrakingFactor` | **2** | nothing (no member) |
| `TransformationTurnTorqueFactor` / `Decel` | **3000 / 24000** | stance turn, not a boost member |

**Declared conflict, not resolved by preference:** `MODES.md` records `BattleModeMaxSpeed`,
`BattleModeMaxSteering`, `BattleModeStopAndTurnAngleMoving` as **not serialised** ("the class declares
them, the packages do not carry a tag"), while `DRIVE_MODES.md` quotes 1200 / 80 / and slip 4 / 10.
Both cannot be the running value. The build must use the **serialised** numbers (MODES.md) and treat the
DRIVE_MODES trio as CDO-derived until a CDO dump settles it (`chase08_cdo.py` / `BMSDK_OFFSETS.json`;
`mode-switch-carriers.md` §7 U6 is the same gap). Consequence: the battle cap is **600 cm/s (21.6 km/h,
TurningModeMaxSpeed)**, which *is* serialised, and 1200 cm/s is a candidate second cap, not the value.

## 6. Evidence level per step

| step | what | level | evidence |
|---|---|---|---|
| 1 | three blocks, offsets, 5 named members | **decoded** | `T-MD14b.md`; `T-MD14B_STATES.json`; `t_md14b.py --check` |
| 2 | shipped values per block | **decoded** | `mode-switch-carriers.md` §2.4 (module bytes) |
| 3 | the ladder is `base` / `_upgraded` pairs | **decoded** | `EJECT.md:205-215` (`turbo_jump*`, `turbo_jump_cooldown` 5 s / `_upgraded` 2 s) |
| 4 | the selector is an engine-side upgrade level 0..2 | **derived** | pairs (§3.1) + the HUD's `upgradeLevel` (§3.3) + the 3 blocks |
| 5 | `heat_boost` is rung 2 / reachable | **UNKNOWN** | no companion member, `push_force` 0; settler: the exe's boost-state consumer |
| 6 | Pursuit = `nitro_boost` unchanged | **decoded value, derived assignment** | §2 |
| 7 | Battle = `heat_boost` with 15000 / 2.0 / 1.333 / 0.0 / 0.2 | **derived** | §2 table; each number traced to a BmAK member or a shipped sibling |
| 8 | the cap cannot be carried by any block | **decoded absence** | `PerformanceBoost` has 5 members, no cap |
| 9 | the two-entity swap carries the cap | **derived** | variant pattern (§2.5) + `B-12`'s precondition; the swap itself is `B-12`'s UNKNOWN U1 |
| 10 | the battle cap is 21.6 km/h, not 43.2 | **decoded (serialised)** | `MODES.md` `TurningModeMaxSpeed` 600 |
| 11 | the stance/pose has a carrier | **decoded** | `all_hinged_part_properties` (`landing_gears_T` pattern) — pose yes, animated `TransformationAnimNode` no |

## 7. UNKNOWNs, each with its settler

| # | unknown | settler (file or probe) |
|---|---|---|
| U1 | does the boost ladder reach rung 2 (`heat_boost`)? | the boost-state consumer in `JustCause3.exe` (not decoded); offline, `t_md14b.py --dump` + the `arcade` type dictionary |
| U2 | does `grip_multiplier` ×1.333 read as "more lateral grip" in JC3's tyre model? | `Research/JC3Grab/USAGES.md` §6 (it gives only the 2.0 / 4.26 shipped values); the tyre/contact solver is native — Q-2 take |
| U3 | is `BattleModeMaxSpeed` 1200 cm/s or unserialised? | `chase08_cdo.py` / a CDO dump of `RVehicleSimBatmobile` (MODES.md vs DRIVE_MODES.md conflict) |
| U4 | can the two entities be swapped at runtime? | `B-12` U1 / `mode-swap-trigger-closest-system-plan.md` (no spawn action class in the interaction census) |
| U5 | does `boost_blend_time` 0.2 s apply on entry *and* exit? | `USAGES.md` §6 (value decoded, direction not); Q-2 take |
| U6 | the `arcade`/`heat_boost` parent offset ambiguity (§1 note) | `t_md14b.py --check` byte re-read of the three `*_custom_land_global.vmodc` |

## 8. Gates the build must pass

| gate | command | what it proves |
|---|---|---|
| block census unchanged | `python Tools/scripts/t_md14b.py --check` | 9 blocks, offsets ascending, the 3 land blocks still present |
| the built module's blocks | `python Tools/scripts/bm_rc4.py --check` | the RC re-reads its own modules (note: this check currently dies with `MemoryError` on this machine — `correction-8390-collision-placement.md` §6) |
| battle entity values | `python Tools/scripts/t11_modes.py --check` | the 15-row mode record still re-derives if the rows change |
| two-entity pair | `python Tools/scripts/b12_variants.py --check` | the card is buildable only once D-2 is re-resolved; until then this plan is a proposal, not a flip |

## 9. Pilot cards (one sentence each, with the pass band)

- **Pursuit / reachable rung:** "In pursuit, hold boost and the car gains about 43 km/h with the same
  lateral slide as before." Pass band: **+43.2 km/h ±3**, and no change in turn radius at 40 km/h
  beyond ±10 %.
- **Battle / `heat_boost`:** "In battle, hold boost into a hard turn and the car holds the line instead
  of washing wide, and it never exceeds 21.6 km/h in turning mode." Pass band: lateral slide **reduced
  ≥20 %**, speed capped at **21.6 km/h ±0.5**.
- **Blend:** "The change arrives over about a fifth of a second, with no visible step in the speed
  needle." Pass band: **0.2 s ±0.05**, monotone ramp.
- **Inertness (route B before U1 is settled):** "A pursuit-only drive is byte-for-byte the same
  behaviour as before the change." Pass band: 0 measurable difference in a back-to-back take.
