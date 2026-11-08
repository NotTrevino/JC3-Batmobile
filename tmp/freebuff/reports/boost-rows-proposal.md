# Boost rows proposal: BmAK afterburner values with no translation row

**Status: proposed, checker PASS (see below).** Proposal page:
`Working/Translation/BOOST_ROWS_PROPOSAL.md` (machine-checked JSON). Checker:
`python Tools/scripts/t_boost_rows.py --check`. `T_ROWS.jsonl` was not edited (198 rows before and
after; the checker prints its sha256 and asserts no proposal id exists in it).

## Decisions

| BmAK value (unit) | source | JC3 carrier | converted | decision |
|---|---|---|---|---|
| `BoostDuration` 2.0 s | `CLUSTER.md:50` | `VehicleMisc.full_nitro_use_time` (+`_upgraded`) | 2.0 s (1 s = 1 s) | **map** (P-B5) |
| `BoostCooldown` 12.0 s (tier 0) | `CLUSTER.md:51` | `VehicleMisc.full_nitro_refill_time` | 12.0 s (1 s = 1 s) | **map** (P-B6) |
| `FakeExtaSpeedDecel` 2000 cu/s² | `CLASS_DEFAULTS.md:267` | none (blend only) | 72 km/h/s recorded | omit (P-B7) |
| `BoostDurationDonut` 6.0 s | `CLUSTER.md:55` | none (no donut mode) | 6.0 s recorded | omit (P-B8) |
| `SVehicle.MaxSpeed` 4000 cu | `CLASS_DEFAULTS.md:163` | `official_top_speed` exists but is T-E5's | 144 km/h recorded | omit - conflict (P-B9) |
| `InfiniteBoost` false bit | `SAMPLER_FIELDS2.md:96` | none (JC3 nitro is finite) | false | omit (P-B10) |
| `BoostCooldownUpgradeLevel` none | `CLUSTER.md:52` | none (no tiers built) | none | omit (P-B11) |
| `CurrentBoostTimer` 1.0 s | `CLUSTER.md:53` | none (runtime state) | 1.0 s recorded | omit (P-B12) |

## Why these splits

`Research/JC3Grab/USAGES.md` section 6 (line 552) is the donor block: torque x2, grip x2,
`push_force` 15000, `boost_blend_time` 0.2 s, `extra_top_speed` +40 km/h. It has **no** duration,
cooldown, decel, donut, cap or flag member. So:

* **duration and recharge** cannot be carried by the block, but the JC3 nitro system does have
  `VehicleMisc.full_nitro_use_time` and `full_nitro_refill_time`, present on all 232 vehicles
  (`DRIVE_CARRIERS.md:301,303`; the build writes 4 s / 2 s today). Both are mapped 1:1 in seconds,
  with the semantic difference declared: BmAK is a fixed burst + cooldown, JC3 is a meter drain +
  refill. The base and `_upgraded` use-time both take 2.0 s because BmAK has one duration and no
  upgraded tier; leaving `_upgraded` at 8 s would contradict the only BmAK duration.
* **decel** has no decel member anywhere in the block; JC3 blends torque out, and turning a
  cu/s² ramp into a blend time needs a velocity step the files do not give (UNKNOWN). The converted
  72 km/h/s is recorded so a future derivation has its input.
* **donut** has no mode: `heat_boost` is kept at Serpente defaults with no BmAK source (T-B4), and
  putting 6 s into `full_nitro_use_time` would make every boost 6 s.
* **base cap** has a real JC3 field, but it is already claimed by T-E5's signed-off 336.4 km/h; a
  second write would overwrite that decision. 4000 cu is the engine's base cap, not a boost value.
* **flags/state** (`InfiniteBoost`, `BoostCooldownUpgradeLevel`, `CurrentBoostTimer`) have no
  carrier: JC3 nitro is finite and metered, no upgraded tiers are built, and the timer is runtime
  state the engine overwrites.

## Verification actually run

```
python Tools/scripts/t_boost_rows.py --check
-> oracles PASS, exit 0
python Tools/scripts/v_entity_unexplained.py --check
-> oracles: 23/23 pass, document identical
```

The boost checker re-reads each BmAK file:line (`CLUSTER.md` 50/51/52/53/55,
`CLASS_DEFAULTS.md` 163/267, `SAMPLER_FIELDS2.md` 96), asserts the value literal is on that line,
re-runs each conversion from the declared constants, verifies each map row's JC3 member in
`Working/Translation/current.json` and its fleet domain line in `DRIVE_CARRIERS.md`, verifies each
omit row's evidence (including T-B2/T-B4/T-E5 cells), parses the uncovered set out of
`BOOST_COVERAGE.md` (7 section-4 bullets + `BoostDuration`), and asserts `T_ROWS.jsonl` still has
198 rows with no proposal id in it.

## Limitations

* Static only: no value was written to any module and the game was not launched, so the two mapped
  rows are proposals with Q-2 gates, not measured behaviour.
* `full_nitro_use_time` / `full_nitro_refill_time` are outside the donor block section 6 cites; the
  decision to use them is stated as an equivalence (time for time), not as a decoded donor mapping.
* `BoostCooldown` slots 1/2 and the `DriftingBoostCooldown` default remain UNKNOWN (BOOST_COVERAGE
  section 7), so only tier 0 is proposed.
* `T_ROWS.jsonl` was deliberately not edited: adopting these ids (P-B5..P-B12) is a separate change.

## Files and revert

* new: `Working/Translation/BOOST_ROWS_PROPOSAL.md`, `Tools/scripts/t_boost_rows.py`, this report.
* read-only: `BOOST_COVERAGE.md`, `USAGES.md`, `CLUSTER.md`, `CLASS_DEFAULTS.md`,
  `SAMPLER_FIELDS2.md`, `DRIVE_CARRIERS.md`, `current.json`, `T_ROWS.jsonl`.
* revert: delete the three new files. No build, module, game file or translation row was changed.
