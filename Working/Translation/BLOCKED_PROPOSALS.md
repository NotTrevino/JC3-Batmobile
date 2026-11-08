# Blocked translation rows - what each waits for

STATUS: partial - 31 blocked rows enumerated (27 ledger + 4 T6 = STATUS.md's 31 of 260), none left to test against the repo. `T-FX3` and `T-ST7` were refuted and resolved by the operator on 2026-11-06; `T-AU3` and `T-AU5` were refuted by `AUDIO_BANKS.md` (10 banks found, 0 absent) - all seven, with `T-S6` (derived unit bridge, 14/14 oracles), `T-WP4` (launcher split from the disable) and `T-WP13` (forced slots), have left the blocked set (section 'Resolved', below).

Ledger `T_ROWS.jsonl` sha256 `08d9a6000bddf46b...` (244 rows), T6 sha256 `4fff95a3667f7614...`. `T_ROWS.jsonl` is not edited; the proposed row edits below are for the operator.

## The 31

| # | row | doc | waits for |
|---:|---|---|---|
| 1 | `T-RA1` | T-3 | a triggered, non-damaging impulse/torque with target selection and a duration - no road-assist/dodge/shove/kill-flip member at any layer (card G2-35) |
| 2 | `T-RC1` | T-3 | an input carrier for remote drive - the land-vehicle action set has no aim/stick/cursor action, JC3 has no 2D vehicle stick and the gadget route is a proximity interaction; halted by ruling (`water-flip-damage-remote-plans-v2.md` section 4.4), with Rebel Drop carrying the summon |
| 3 | `T-RC2` | T-3 | a distance-to-player read and a HUD overlay element - 0 hits for static/noise/jam/overlay/fullscreen in the vehicle-HUD element table and none in the interaction layer; halted by ruling, not declared impossible |
| 4 | `T-CT1` | T-3 | the keymap writer (`T-CT5`) - the patch keymap's `EXIT_VEHICLE` / `RPADUP` pair has to be split into enter = Y and exit = LB |
| 5 | `T-CT2` | T-3 | the keymap writer plus the double-press timer - no hold/duration/tap field in 145+104+249 binding rows (U2) and 0 of 4,832 exits carries a launch member |
| 6 | `T-CT3` | T-3 | the keymap writer, for the winch on `RPADRIGHT` with `USE_VEHICLE_MOD` re-homed to Y |
| 7 | `T-CT4` | T-3 | BmAK's in-car steering response curve (`StandardSteeringSpeedCurve` / `DesiredTurnOnSpotSpeed` need the capture set, U6); the two axes are decoded |
| 8 | `T-CT5` | T-3 | a keymap writer - 0 of 575 `Tools/scripts` files writes a bin; the 12-byte binding record plus 18 B of `stringZ` records must re-parse to 145 patch bindings |
| 9 | `T-MS1` | T-3 | a consumer that swaps or replaces a vehicle entity at runtime (U1) - 0 `replace`, 0 `respawn`, 0 `despawn` and 0 `.ee` `swap` paths in 81,952, so the settler is `JustCause3.exe`; the two leaves and Rebel Drop are buildable without it |
| 10 | `T-TX1` | T-3 | the `Batmobile_Micropattern_A` pixels - 0 of 61 grab `.tga` carry the stem; settler is a re-grab of the `Playable_Batmobile*` packages |
| 11 | `T-TX2` | T-3 | the `Batmobile_Micropattern_A_Normal` pixels - same re-grab; no substitute map exists |
| 12 | `T-TX3` | T-3 | the `Batmobile_Micropattern_B` pixels - same re-grab |
| 13 | `T-TX4` | T-3 | the `Batmobile_Micropattern_C` pixels - same re-grab |
| 14 | `T-TX9` | T-3 | a chapter selector for `Damage_Chapter_Mask` (0 of 961 headers, `SupportDmgBlend` [0.0] in all 160 blocks) - and the operator's no-damage-stages ruling closes the crude single-state route |
| 15 | `T-TX10` | T-3 | the same chapter selector as `T-TX9` |
| 16 | `T-TX11` | T-3 | the same chapter selector as `T-TX9` |
| 17 | `T-TX12` | T-3 | the same chapter selector as `T-TX9` |
| 18 | `T-L28` | T-14 | a body `_LIG` anchor node plus a `CarLight` block on the body (B-03 / B-04) - socket and bone are null on `HeadLight1c`; the sprite waits on T-24 |
| 19 | `T-L30` | T-14 | the same body-hosted `_LIG` node and `CarLight` block (B-03 / B-04) for `HeadLight2c`; the sprite waits on T-24 |
| 20 | `T-WP6` | T-7 | a code-level pull loop (force, length clamp, reel, release) - the anchor object, rope mesh and VFX/SFX are decoded and buildable (`Research/specs/B-16.md`) |
| 21 | `T-WLD17` | T-20 | a cargo bay on a helicopter (0 of 23) plus the native attach rule a cloned bay would need - closest carrier is the cargo plane's bay (`Research/specs/B-16.md`) |
| 22 | `T-MD5` | T-15 | D-2 re-resolved to two variants (B-12) plus a runtime entity swap - the battle variant's own `arcade`/`CustomLandGlobal` values; no JC3 member scales top speed by a mode |
| 23 | `T-MD6` | T-15 | the same battle variant plus a decoded speed-cap member - no member in the fleet caps speed (nearest: `vehicle_misc.official_top_speed`, `extra_top_speed`) |
| 24 | `T-MD7` | T-15 | the battle variant's own `land_steering`/torque set (four of six factors) plus the swap; the two slip-scale members do not exist |
| 25 | `T-MD8` | T-15 | a native turn-on-the-spot mechanism - G2-21 refuted its candidates and found 0 tank-only driving members; a second variant does not create one |
| 26 | `T-MD13` | T-15 | the battle variant's part angles for the deployed pose (T-12) plus the swap; `TransformationAnimNode` still has no JC3 analogue |
| 27 | `T-MD14` | T-15 | a `BattleMode` usage a graph dispatches on plus a second variant to hang T-16's 30 battle-mode events on (B-12); no usage consumer is decoded (U1) |
| 28 | `T-HUD5` | T6 HUD/camera | a weapon component on the entity for the HUD's 2 slots (T-11 bound w602/w603 since; the 3 special-weapon states have no member) |
| 29 | `T-CAM8` | T6 HUD/camera | a head-impulse / drift-orientation camera member - none in any decoded camera module |
| 30 | `T-CAM9` | T6 HUD/camera | a unit bridge from BmAK's camera smoothing strength to JC3 spring stiffness |
| 31 | `T-CAM11` | T6 HUD/camera | a numeric bridge to `AddCameraShake` (game code; no values decoded) |

## The rows tested against the repo

## Resolved - no longer blocked

### T-ST7 - resolved-by-operator-ruling

**Ruling:** operator ruling 2026-11-06, option A: **0.25 s, no compromise** (`Working/Translation/DECISIONS_NEEDED.md`, 'OPERATOR RULINGS 2026-11-06', item 1), with the steering-rate / max-speed members checked so the whole BmAK rate is carried, not only the lock time

- `Research/JC3Grab/DRIVE_CARRIERS.json` marker `t_to_full_steer_s`: the steering member is decoded per module, so the fleet's values are data
- `Working/Translation/T_ST7B_FLOOR.md` marker `exists in the fleet`: 0.25 s ships in 4 LandSteering AI twins and 0.2 s on the high-speed member
- `Working/Translation/T_ST7B_FLOOR.md` marker `MotorbikeSteering`: a *player* module ships 0.3 s (2 modules), so the player path is not floored at 0.5 s either

**Applied:** ledger `T-ST7`: dispo `blocked` -> `next`, value 0.8 s low / 0.6 s high -> 0.25 s low / 0.091 s high (55 deg and 20 deg at 220 deg/s); the row left the blocked set, so this sheet enumerates 16

**Still open:** a game probe: neither value is measured (test ban), and 0.091 s is below the 0.2 s fleet minimum, i.e. a declared out-of-domain switch

### T-FX3 - resolved-by-operator-approval

**Ruling:** operator ruling 2026-11-06, item 2: **approve** the decoded afterburner-flame edit (`Working/Translation/DECISIONS_NEEDED.md`, 'OPERATOR RULINGS 2026-11-06')

- `Research/JC3Grab/USAGES.json` marker `4197885156`: usage id `EngineNitro` exists in the decoded 155-value usage vocabulary
- `Research/JC3Grab/FX_TABLE.jsonl` marker `car_cycle_base_dual_nitrous`: the fleet ships the dual nitro exhaust effect (17 cargo rows)
- `Working/Translation/T_FX3B.md` marker `EngineNitro`: the donor's two exhaust emitters already carry usage 4197885156, so the approved edit is placement on the `Afterburner` socket (B-08), not a new effect or a new usage

**Applied:** ledger `T-FX3`: dispo `blocked` -> `next`; the edit is B-08's placement - both `SAttachedEffect.world` mats from the Serpente's exhaust to the `Afterburner` socket (bone `JetSMove`), spec `Working/Effects/bm_fx_edits.json` `edits[]`, compiled by `Tools/scripts/bm_fx.py` into `Builds/bm-008/.../*_civilian_01.epe`; the row left the blocked set, so this sheet enumerates 15

**Still open:** `bm_fx.py --check` is red for an unrelated reason (6 `SWeaponPoint` objects gained a later `weapon_anchor` property in bm-008), and no probe was run: whether the flame follows the nozzle in motion is UNKNOWN (test ban)

### T-AU3 - resolved-by-evidence

**Ruling:** no operator decision needed: `Research/BatmobileGrab/AUDIO_BANKS.md` (G3-14) re-tested the absence claim against the whole BmAK install - 10 claimed banks, **10 found, 0 absent**, 117 `AkBank` payloads read

- `Research/BatmobileGrab/AUDIO_BANKS.md` marker `10 found, 0 confirmed absent`: every one of the 10 banks the row called absent is present in a BmAK package
- `Research/BatmobileGrab/AUDIO_BANKS.md` marker `BML_Batmobile_Subjective`: the four jump banks live in `Startup`, a package the old 3-package scan never opened
- `Working/Translation/T_AU3B.md` marker `ABSENT: 27 of 27`: the 27/27 absence is true of the JC3 install only: a carrier gap, not a missing source

**Applied:** ledger `T-AU3`: dispo `blocked` -> `next`; the source banks exist, so what remains is the JC3 event binding of the 26 ids; the row left the blocked set

**Still open:** a JC3-side event slot per id and, where JC3 has no sample, an auditioned substitute (`T_AU3B` section 4 lists the name-level candidates); no probe was run

### T-AU5 - resolved-by-evidence

**Ruling:** no operator decision needed: the same `AUDIO_BANKS.md` re-test (10 found / 0 absent) removes the 'absent banks' half; only these three families' own bank and slot remain

- `Research/BatmobileGrab/AUDIO_BANKS.md` marker `10 found, 0 confirmed absent`: the banks T-AU5 inherited from T-AU3 are present
- `Research/BatmobileGrab/ASSETS.md` marker `AkVehicleSound`: the Batmobile's vehicle-sound object is an `AkVehicleSound`, so the mapping is an object-level task, not a missing bank
- `Working/Translation/T_AU3B.md` marker `T-AU5`: the note records this row's own claim and that the loss is a JC3 carrier gap

**Applied:** ledger `T-AU5`: dispo `blocked` -> `next`; the source side is complete, and the row now names these events' own bank (UNKNOWN - not among `AUDIO_MAP.json`'s 361 rows) plus a JC3 slot and the mode-switch trigger as what it needs

**Still open:** the bank and event id of `TransformationReverseDirection*`, `TaserSound` and `VehicleSound` (not in the four-package `AUDIO_MAP` sweep), then a JC3 slot and the T-MD14 mode-switch trigger

### T-S6 - resolved-by-derived-bridge

**Ruling:** no operator decision needed: the unit bridge is derived from the decoded class defaults and the 166-vehicle fleet (`tmp/freebuff/reports/suspension-unit-bridge.md`, 14/14 oracles, `Tools/scripts/t_s6_bridge.py --check`)

- `tmp/freebuff/reports/suspension-unit-bridge.md` marker `0.4542`: the fleet's median static-sag fraction is derived, so `strength = g/(4*f*length)` closes the dimension
- `tmp/freebuff/reports/suspension-unit-bridge.md` marker `13.500`: TravelDown 40 cm at that fraction needs strength 13.500 s^-2, and BmAK's 3000 against the decoded 210 kg gives 14.286 - fit error +5.8% / -5.5%
- `tmp/freebuff/reports/suspension-unit-bridge.md` marker `no_bias_member`: JC3 carries no bias channel, so the front bias is placed as a hardpoint offset (-0.10, 0.0% against the fleet median) and the rear bias stays a gap

**Applied:** ledger `T-S6`: dispo `blocked` -> `next`; TravelDown 40 cm -> length 0.40 m, stiffness 3000 -> strength 13.500 s^-2, damping 300 -> compression/relaxation 1/2 (-31.1% on integer quantisation), front bias 10 -> hardpoint offset -0.10; the row left the blocked set, so this sheet enumerates 17

**Still open:** no member for droop (`BMRearWheelMaxDroop` 100) or the up-travel 30 cm (cards B-22), none for the per-mode 750 / stationary bias (B-23); whether the engine reads `hardpoint_offset_along_spring` as a rest position is UNKNOWN (test ban)

### T-WP4 - resolved-by-operator-ruling-and-donor

**Ruling:** operator ruling 4, 2026-11-06: **approve the split** so the missile launcher ships, with the JC3 Fire Leech as the lock-on lead (`Working/Translation/DECISIONS_NEEDED.md`, 'OPERATOR RULINGS 2026-11-06')

- `tmp/freebuff/reports/wp4-fire-leech.md` marker `w143_rpg_fire_leach`: the Fire Leech is a decoded `WeaponTuning` whose `missile_turning_speed` is 300 and whose `AutoAim` cone equals the fleet lock-on preset, so the guidance transplants onto the w618 clone by value
- `tmp/freebuff/reports/wp4-fire-leech.md` marker `CanTargetCharacters`: w143 may lock characters and BmAK may not, so the lock-on tune is a new `AutoAim` with the preset's classes rather than a wholesale copy
- `Working/Translation/DECISIONS_NEEDED.md` marker `T-WP4: approve the split`: the split is the operator's, not a research inference

**Applied:** ledger `T-WP4`: dispo `blocked` -> `next`, launcher only (w618 clone + `CForcePulse` + the w143 guidance + a new lock-on `AutoAim`); the disable half became its own row `T-WP15` as a named omission (`out`), so the row left the blocked set and the sheet enumerates 15

**Still open:** a 2.0 s held lock, an 8-target salvo and the reticle link have no member (cards B-24 / B-25); no probe was run (test ban)

### T-WP13 - resolved-by-operator-ruling

**Ruling:** operator ruling 3, 2026-11-06: **force extra weapon slots** - the two reference vehicles carry 2 weapons + a shield, so JC3's 2 driver slots are a convention

- `tmp/freebuff/reports/wp13-slots-force.md` marker `v0202_car_capstone_bavariumtank`: the Imperator graph is decoded: 4 slot properties, 2 non-null pointers
- `tmp/freebuff/reports/wp13-slots-force.md` marker `BavariumShield`: the third weapon the premise counts is a shield PART + effect, not a slot, so forcing slots is a design decision and is recorded as one
- `Working/Translation/DECISIONS_NEEDED.md` marker `T-WP13: force extra weapon slots`: the ruling is the operator's, not a decoded member

**Applied:** ledger `T-WP13`: dispo `blocked` -> `next`; 4 `CCar` roots x 2 decoded pointers = 8 slots for the 8 slot-able BmAK objects, 0 invented property names, the 5 gadgets outside the slot space; the row left the blocked set, so this sheet enumerates 15 of 216

**Still open:** whether two or more roots on one car chassis fire from the driver seat is UNKNOWN (no entity states the input-to-root binding); `RiotSuppressorMuzzle` and the Joker weapons have no points

## How this is checked

`python Tools/scripts/t_blocked.py --check` re-derives both blocked sets from the two documents, cross-checks the count against `status_audit.t_rows()` (the function that writes `STATUS.md`), rebuilds this file and its JSON byte for byte, re-runs every evidence marker (including the two negative ones, which must occur zero times) and compares the ledger sha256 with the one recorded above. A row that is later unblocked makes the check fail rather than leave this sheet stale.

Nothing was launched, installed, attached to or written outside `Working/Translation/`.
