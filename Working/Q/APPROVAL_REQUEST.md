# Approval request - phase Q on bm-RC4 (gate VX)

Written by V-07 for the operator. **Nothing here has been installed.** No approval marker exists:
`tmp/freebuff/APPROVED_Q.txt` is deliberately absent, and only the operator (or Claude on the
operator's word) may write it. Until then the test ban stands.

## 1. What would be installed

`Builds/bm-RC4` -> `<GameDir>/dropzone`, by `Builds/bm-RC4/install.ps1`
(6,535 B, sha256 `b4589d40f3bed7c1dd2300d2698790c4fc9fee7e5213398a00ebad3aded15382`),
against receipt schema **2**.

**9 files, 401,700,202 B (383 MiB):**

| # | path under `dropzone/` | bytes | sha256 (first 16) |
|---:|---|---:|---|
| 1 | `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee` | 11,225,533 | `b72690d32c61a30c` |
| 2 | `.../v0300_car_kensington_sportsmuscle_debug.ee.toc` | 68,675 | `cde0678e2fb710ba` |
| 3 | `profile/item.onlinec` | 77,569 | `239d6b6d2425fb8c` |
| 4 | `profile/online.stringlookup` | 1,746,322 | `6dcdf0ce1af304b6` |
| 5 | `profile/task.onlinec` | 168,174 | `9250e2712478d50c` |
| 6 | `settings/spawn_vehicle_defs.bin` | 27,785 | `797391dcef5fb5b6` |
| 7 | `sound/fmod_banks/vehicles.bank` | 210,781,376 | `aab92ca03f8cbbfe` |
| 8 | `sound/fmod_banks/weapons.bank` | 177,586,080 | `d05b74ed9111ecad` |
| 9 | `textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc` | 18,688 | `5096fb74d8fcce49` |

Six of the nine do not exist in a vanilla dropzone (the entity, its `.toc`, the icon, both banks and
the spawn table); three replace shipped profile files, and those are the ones that need a backup.

**Dry run, already done on a copy:** `Builds/bm-RC4/verify/dropzone_sim.md` - Status/WhatIf 0 writes,
Install 9/9 on an empty root, Install over an installed root byte-identical with Verify 9/9, decoy
backed up and restored by Rollback, and `-GameDir E:/Modding/not_the_sim` refused with exit 2. All
six cases matched their expected exit code; the record holds every case's exit code and raw output.

**Rollback:** `-Action Rollback` restores what Install snapshotted (`<GameDir>/snapshot/...`) and
removes the targets that did not exist. Snapshotting is by **diff**: targets whose hash already
matches are not backed up, so a Rollback after an install-over-install removes them as if uninstalling.

## 2. Expected sessions

Three sessions, in this order. Lengths are **derived estimates** from each card's checklist, not
measurements:

| session | content | checklist | estimate |
|---|---|---|---:|
| **Q-1** | static, spawn, looks, moving parts, weapons at a wall, self-damage, night lights, audio at standstill | 8 items | ~45 min |
| **Q-2** | driving takes at the airfield with the QA-1 HUD: A1, A2 (+boost), A3, A4, A5, A6, A7, A8, A9, A10, A15, A16 | 8 takes + 4 checks | ~40 min |
| **Q-3** | world and combat: ram, 5-star heat, weapons vs targets, water, tether, traffic count, lamp/engine FX | 7 items | ~45 min |

Each session needs approval, a save backup, `-Action Install` then `-Action Verify` green, a fixed
window size, `um win` screenshot test and the PID recorded for `um win kill`. Every check has a
prediction and a band (`Working/Q/PREDICTIONS.md`, `PREDICTIONS_COMBAT.md`, `PREDICTIONS_LOOKS.md`);
nothing in Q is judged without one.

**Pilot cards** (read-through only until approval): `Working/Q/PILOT/` - `LAUNCH.md`, `LOAD_SAVE.md`,
`SPAWN_BATMOBILE.md`, `ENTER_EXIT.md`, `CONTROLS.md`, `AIRFIELD.md`, `SCREENSHOT.md`, `RECORD.md`,
`KILL.md`, plus `CARD_FORMAT.md`. Each is one action per line with a scriptable check.

## 3. Every red or UNKNOWN the operator is accepting

**Red / incomplete, with the file that proves it**

| item | state | proves |
|---|---|---|
| stale checkers | `v05_driving` T-ST7 gate, `t_boost_rows` 198-row pin, `t_vnf_six` 198/145 pins - all fixed against the **199-row** ledger; the T-ST7 miss stays **RED** (built 0.80 / 0.60 s vs goal 0.091-0.250 s) | `tmp/freebuff/reports/correction-8396-stale-checkers.md`; `Working/Q/PREDICTIONS.md` D-4 |
| textures | `receipt.complete = false`: **12 of 23** rows unfaithful - 4 chapter masks, 8 missing pixel sets (14 refusal records) | `Builds/bm-RC4-appearance/texture_ledger.json`; 8392 |
| audio | **21 of 45** GUIDs have no carrier here (19 effects + 2 character banks); `vehicles#279` loop is a named compromise | `Builds/bm-RC4-audio/events.json`; 8393 |
| collision | on the shipped payload `fda78f4d…` placement is **0.25 cm** and the gate is MET; **2 of 3** BmAK boxes have no shape instance; **1** constraint is a named omission. The **6.1 cm** figure belongs to payload `0164936b…`, which is not in this tree | `Builds/bm-RC4/verify/geometry.md` line 4 and 18-19; 8390 |
| module conflict | D-08 vs D-10: **8397 merged both sets**; `skew_health` is present in the packed `custom_land_global.vmodc`. The brief's "not carried" is the pre-8397 state | `Builds/bm-RC4/.../custom_land_global.vmodc`; 8397 |
| mode pair | RC4 is the **pursuit set only**; the battle pair is unmerged in `Builds/bm-RC4-modes`. T-MD8 (turn on the spot) and T-MD14 (battle audio) are **named omissions**, and T-MD5…T-MD8/T-MD13/T-MD14 cannot ride a hybrid | `GRAB_BACKLOG.md` B-12, D-2; 8398 |
| no-payload cards | B-12 (D-2 reopened), B-17…B-20, B-25/B-26 declare **no payload in RC4** | `Working/Translation/BUILD_BATCHES.md` §4; 8398 |
| top speed | **336.4 km/h is `assumed`** (wiki 209 mph), not measured; the build predicts **267 km/h** at Cd 0.55; the 0.1213 Cd written to reach the label is withdrawn | `Working/Q/PREDICTIONS.md` D-2; 8391 |
| runtime | **untested**: the load, Rebel Drop leaf **1621485476**, and every Q take. No install has run against a game folder | this gate |

**UNKNOWN, named**

* whether the engine honours the steering rate (0.091-0.250 s), the drift labels (0.625 / 0.48), or
  the collision and light domains at runtime - the Q takes are the only oracle;
* whether the game's own tanks pivot and which native key decides it (T-MD8's omission);
* the missile lock time on the JC3 side (no lock-duration member in 4,054 tune rows);
* which high-speed lock the build carries (20 deg gives 13.82 m, the 15 deg T-ST7 names gives 18.77 m);
* whether the 6,000 kg mass is a design value rather than a decoded one (it is a design value).

## 4. Decisions still open

* **D-2** is **reopened**: RC4 ships pursuit only. Approving Q tests that car; it does not approve a
  battle mode, and B-12 stays unbuilt until the operator re-resolves D-2.

## 5. What approval means

Writing `tmp/freebuff/APPROVED_Q.txt` authorises install and Q-1 on the operator's machine. It does
not authorise a code change, a push, or a second build tree. A failed check is recorded in
`Working/Q/RESULTS.md` with its measured value and band, and the row stays open; no band is lowered.
