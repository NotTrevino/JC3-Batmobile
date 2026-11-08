# Applying the winch/tether rows (T-WP6, T-WLD15, T-WLD17)

**STATUS: done.** `tmp/freebuff/reports/winch-and-tether.md` says the winch's **entity-graph half is
decoded and buildable** (anchor object, drum mesh, rope components, VFX/SFX) while the **pull loop
is code-level absent**; the tether is native character code; helicopter airlift is **data-blocked**
(0 of 23 helicopters has a cargo bay). The three rows are therefore no longer omissions:

| row | was | now | why |
|---|---|---|---|
| `T-WP6` | `out` (named omission) | **`blocked`** | translated carrier + member paths are decoded; the missing half is exactly named: a pull loop with force, length clamp, reel and release |
| `T-WLD15` | `out` | **`next`** | translated to the only attach/release objects (`CVehicleCargoBay`, `CGrapplingHookPropData`), the car's 6,000 mass and the `grapple_pull` gate; the pull is native, so Q-3 #5 verifies it |
| `T-WLD17` | `out` | **`blocked`** | data-level: no helicopter carries `CVehicleCargoBay` (0/23) and no helicopter hook class exists; the missing capability is the native attach rule a cloned bay needs |

All three now state which case applies: **translated row** (T-WP6, T-WLD15) or **data-level
capability card** (T-WLD17) — none is recorded as an accepted compromise.

## 1. What the rows carry (member paths, values, evidence)

**T-WP6 — winch.** BmAK side: `RBatmobileWinch` / `Batmobile_Winch`, 18 fields, `FireEffect`
`Winch.Winch_Muzzle`, `ImpactEffect` `VFX_Batmobile.winch_latched`, `FireSound`
`Engine.Play_BML_WinchFire`, `ImpactSound` `Engine.Play_BML_Winch_Attatch`, `ProjectileRope`
@0x0A18, `StubRope` @0x0A10, the `0x0970` bool, `Core.WinchPullType` (values UNKNOWN) and the
function `RestoreOldRopeLengthIfShorter`.

JC3 side (translated):

| capability | JC3 member / object | value | evidence |
|---|---|---|---|
| anchor object | `CVehicleCargoBay`-style object: `world`, `enabled`, `enable`, `disable`, `name`, `name_hash`, `_object_id` | `enabled` 1, both events **empty** (as on all 12 shipped bays) | `TETHER.md` §2 |
| attach point | `WinchOrigin`, bone `Batmobile_Chassis` | relative **(286.554, 0, 59.0) cm**, rotation identity | `Research/BatmobileGrab/SOCKETS_JC3.json` |
| drum mesh | `transport_rope_winch` part | part_index 26, parent 0, `Boat_Generic` → re-typed, `behavior` `None`, 6 model files | `TETHER.md` §4 |
| rope | BmAK `RSimpleRopeComponent` pair | material `VFX_Generic.fx_Winch_M_lit_INST` @560, floats **3.5** @680 and **0.8690145611763** @364 (names UNKNOWN) | `WEAPONS.md:1242-1243,1265-1266` |
| force gate (not a force) | `grapple_pull_armor` / `grapple_pull_armor_strength` | -1..0 / 0..100.0 | `ARMOR_STEP.md:182-183` |
| trigger | `RELEASE_GRAPPLE` (RPADRIGHT / V), `VEHICLE_RELEASE_GRAPPLE` (LPADDOWN) | operator decision 2026-11-05: d-pad RIGHT | `INPUT.md:169,175` |

Missing (the exact gap): **no length, force, reel rate or release member** anywhere — 0 functional
winch classes, 0 of 53 module types, 0 of 67 part behaviours; BmAK's own length is a function and
its force is script-side.

**T-WLD15 — tether a 6 t car.** Translated: the car contributes `RigidBody.mass` **6,000** (6.154×
the 975 donor) and the `grapple_pull` damage channel; the two attach/release objects are
`CVehicleCargoBay` (7 members) and `CGrapplingHookPropData` (33 tags on 3 cargo holders, events
empty). The pull is character-side native code (335 `tether` index paths, all dialogue/UI).
Verified by Q-3 #5, not written.

**T-WLD17 — helicopter airlift.** Data-level: `bay_helicopters` = `[]`, 0 of 23; the census has no
helicopter hook class; the closest carrier is the cargo plane's bay (6 entities) plus the compound
`v4603_plane_urga_cargotransport_military_cargo_tank` (`CAirPlane` + `CCar`, bodies 25,000 + 40,000).
The missing capability is the native attach rule a bay cloned onto a helicopter would need.

## 2. The winch clone's entity-graph plan (B-05 step)

Full card: **`Research/specs/B-16.md`**. In one paragraph: add four objects to the private `.epe` —
(1) `WinchAnchor`, a clone of a shipped `CVehicleCargoBay` (`name`/`name_hash`, `world` =
translation-only from `WinchOrigin` at (2.86554, 0, 0.590) m, `enabled` 1, `enable`/`disable`
empty); (2) a `WinchDrum` part using the `transport_rope_winch` mesh (parent 0, no behaviour,
damage type re-typed to the body's land type); (3) and (4) BmAK's `RopeComponent0`/`RopeComponent1`
with material `fx_Winch_M_lit_INST` and the 3.5 / 0.8690145611763 floats (meaning UNKNOWN). Then the
pull loop — force toward the hit point, length clamp, reel rate, release on d-pad RIGHT — is written
outside data, because no JC3 file supplies it.

## 3. Files changed, and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/t7_weapons.py` | new `row_winch()` replaces `omission(... WPN-6 ...)` | restore the omission call, re-run `--write` |
| `Working/Translation/T7_WEAPONS.md` | **regenerated**: T-WP6 is a translated `blocked` row | `--write` after the revert |
| `Tools/scripts/t15_world.py` | T-WLD15 → `next` translated; T-WLD17 → `blocked` data-level | restore the two `add()` blocks |
| `Working/Translation/T15_WORLD.md`, `t15_world.json` | **regenerated** | `--write` after the revert |
| `Tools/scripts/t_rows.py` | `DISPO` for the three rows | restore the three lines |
| `Working/Translation/T_ROWS.jsonl` | **regenerated** (`t_rows.py build`) | `build` after the revert |
| `Tools/scripts/t_blocked.py` | `WAITS` + pins: 12 blocked = 8 ledger + 4 T6, in scope 185 | restore `WAITS` entries and the old pin tuple |
| `Working/Translation/BLOCKED_PROPOSALS.{md,json}` | **regenerated**: 12 rows, T-WP6 and T-WLD17 included | `--write` after the revert |
| `Tools/scripts/audit_compromises_t.py` | the three audit entries re-worded (T-WP6 keeps its `WINCH` approval) | restore the three tuples |
| `Working/Translation/COMPROMISES_T.{md,json}` | **regenerated**: 72 audited, 1 approved, 71 unapproved | `--write` |
| `STATUS.md` | **regenerated**: blocked 12 / 185 | `--write` |
| `Research/specs/B-16.md` | **new** build card | delete |

## 4. Checks actually run

```
$ python Tools/scripts/t7_weapons.py --write
T7_WEAPONS.md + t7_weapons_edits.json: 14 rows (12 WPN + 2 decisions), 145 aspects
(47 UNKNOWN), 3 edits, 518 md lines                                  exit=0
$ python Tools/scripts/t15_world.py --write
t15_world.json: 19 rows, 8/8 WLD codes, dispositions
{'next': 9, 'keep': 6, 'epe': 3, 'blocked': 1, 'out': 0}             exit=0
$ python Tools/scripts/t_rows.py build
T_ROWS.jsonl: 198 rows, 35 edits over 16 rows                        exit=0
$ python Tools/scripts/t_blocked.py --write
BLOCKED_PROPOSALS.{json,md}: 12 blocked rows (8 ledger + 4 T6) of 185 in scope;
2 tested, 4 resolved                                                 exit=0
$ python Tools/scripts/audit_compromises_t.py --write
72 audited, 1 approved, 71 unapproved                                exit=0
$ python Tools/scripts/status_audit.py --write   -> STATUS.md current exit=0

checks
$ python Tools/scripts/t7_weapons.py --check
PASS: 14 rows ... (7 with a JC3 carrier, 3 named omissions, 4 blocked) | 145 aspects
classified, 47 UNKNOWN | ... | json match True, md match True        exit=0
$ python Tools/scripts/t15_world.py --check
PASS: 19 rows | WLD codes 8/8 | dispositions next 9, keep 6, epe 3, blocked 1, out 0 |
ledger 19/19                                                        exit=0
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 50 keep 60 epe 26 re-read 0 blocked 8 out 31
superseded 7 | check ok                                             exit=0
$ python Tools/scripts/t_blocked.py --check
PASS: 12 blocked rows re-derived (8 ledger + 4 T6) of 185 in scope; 2 attempts, all
evidence markers present; ledger sha256 unchanged                    exit=0
$ python Tools/scripts/audit_compromises_t.py --check
72 audited: 1 approved, 71 unapproved; by dispo {'blocked': 7, 'out': 29,
'superseded': 2, 'next': 13, 'edit': 10, 'keep': 11}
OK: every approval quote re-read at its cited line; document re-derived identically   exit=0
$ python Tools/scripts/status_audit.py --check
STATUS.md is current                                                exit=0
```

Note on the pin: `t_blocked.py`'s invariant is "ledger blocked == WAITS", and three rows
(`T-WLD4`, `T-WLD6`, `T-WLD11`) had been unblocked by earlier lanes while their `WAITS` lines
remained, so the tracker failed before this change. They are removed from `WAITS`, and the pins now
read 8 ledger + 4 T6 = 12 blocked of 185 in scope — the numbers `status_audit` re-derives.

## 5. What is still missing (named, not accepted)

1. **Pull loop** — force, length clamp, reel rate and release: engine code on both sides. No JC3
   file supplies it; the only precedent (`dualtether_test_to_vehicle.gdc/.gsc`) is unread.
2. **Force in newtons** — impossible: `RigidBody.mass`'s unit is unknown and no tether force exists,
   so the winch can only be stated as 6.154× the donor's class. BmAK's own feat bound (≥ ~2 t) is
   **below** a 6 t car.
3. **Rope floats** 3.5 and 0.8690145611763 — names undecoded.
4. **Helicopter bay attach rule** — native; needs a probe after a bay is cloned onto a helicopter.
5. **Q-3 #5 is not run** (test ban): both winch rows are predictions, not measurements.
