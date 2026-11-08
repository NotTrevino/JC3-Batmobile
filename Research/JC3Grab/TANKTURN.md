# Turn-on-the-spot (tank pivot)

G2-21. **Answer: no member set produces a pivot.** JC3 models all four tracked
chassis as ordinary `CCar` wheel vehicles - 4/6/8 discrete wheels with tyre slip curves -
and the four modules the card names carry **byte-identical member sets** in tanks and
cars, so no tuned value in them can switch a neutral turn on. None of the card's
candidate members (nor all five together) separates the tanks from the fleet, no member
of any driving module has a tank-unique value, and nothing in the whole module vocabulary
names a track, a pivot or a skid-steer mode. The deciding logic therefore cannot be
data: **MOD-2's turn-on-the-spot is a named omission**, carried by native code keyed to
the vehicle's identity (no data value distinguishes a pivot-capable vehicle). Whether the
game's tanks actually pivot, and which native key decides it, is `UNKNOWN` from these
files - a one-variable Q probe is the only way to settle it (R13).

## 1. The four chassis and the card's four modules

Sources: 232 decoded entity builds in `entities/`, 232 `.epe` graphs in `detail/`, `VOCABULARY.md` (1421 member rows). Player copies only: 145 builds carry a player `LandGlobal` (the `_ai` twin is a second instance in 13 builds and differs on a candidate member, so it is never read - same rule as `jc3fleet.py`).

| module | members (non-tank union) | members (tank union) | tank-only | non-tank-only |
|---|---|---|---|---|
| `LandGlobal` | 48 | 48 | 0 | 0 |
| `LandSteering` | 15 | 15 | 0 | 0 |
| `Transmission` | 40 | 40 | 0 | 0 |
| `CustomLandGlobal` | 61 | 61 | 0 | 0 |

Both unions are the same size and the difference columns are empty: **the tanks are not tuned from a different vocabulary**. Across every module type there are 52 distinct module types in the fleet, 25 of them on the tanks, and **0 tank-only module types** - there is no track module, no second steering module, no pivot module.

## 2. The card's candidates, each refuted

Value = player `LandGlobal`; fleet range = `VOCABULARY.md`; histogram = measured over the player copies.

| member | tank values (per chassis) | fleet histogram | VOCABULARY range | non-tank builds sharing a tank value | separates? |
|---|---|---|---|---|---|
| `number_of_wheels` | `v0200` [6]; `v0201` [8]; `v0202` [8]; `v0603` [4] | 2 x18, 3 x1, 4 x113, 6 x6, 8 x7 | 2 .. 8 (med 4, n=271) | 114 | **no** |
| `number_of_front_wheels` | `v0200` [-1]; `v0201` [4]; `v0202` [4]; `v0603` [-1] | -1 x138, 4 x7 | -1 .. 4 (med -1, n=271) | 133 | **no** |
| `is_all_wheel_steered` | `v0200` [0]; `v0201` [0]; `v0202` [0]; `v0603` [0] | 0 x142, 1 x3 | 0 .. 1 (med 0, n=271) | 130 | **no** |
| `is_rear_steered` | `v0200` [0]; `v0201` [0]; `v0202` [0]; `v0603` [0] | 0 x145 | 0 .. 0 (med 0, n=271) | 133 | **no** |
| `wheels_friction_type` | `v0200` [2]; `v0201` [2]; `v0202` [2]; `v0603` [2] | 0 x92, 1 x5, 2 x48 | 0 .. 2 (med 0, n=271) | 36 | **no** |

**All five together.** The tanks collapse to just three value tuples:

| tuple (`wheels`, `front`, `all-wheel-steer`, `rear-steer`, `friction`) | tank builds | non-tank builds with the same tuple |
|---|---|---|
| (4, -1, 0, 0, 2) | 3 | 23 |
| (6, -1, 0, 0, 2) | 3 | 3 |
| (8, 4, 0, 0, 2) | 6 | 1 |

**27 non-tank builds carry one of those tuples**, so the candidate set does not identify a tracked vehicle: the small tank's `(4, -1, 0, 0, 2)` is shared with 23 off-road builds (ATV, buggy, monster truck...), the APC's 6-wheel tuple with the armoured transport, and the medium/Bavarium 8-wheel tuple with `v4603` cargo plane. `is_rear_steered` is 0 on all 145 player copies (VOCABULARY range 0 .. 0), and the only `is_all_wheel_steered=1` builds in the game are three monster-truck builds - a wheeled vehicle, not a tank.

## 3. Tank-unique values exist - in no driving module

Every member (any of the 52 module types, player and AI instances) whose value is the same on all 12 tank builds and appears on no other vehicle: **262 members**, by module:

| module | tank-unique members |
|---|---|
| `DeformPoints` | 1 |
| `EffectAttachments` | 37 |
| `Fins` | 14 |
| `Propellers` | 16 |
| `WaterInteraction` | 194 |

Driving modules (`LandGlobal`, `LandSteering`, `Transmission`, `CustomLandGlobal`, `Brakes`, `Suspension`, `Tire`, `CarAI`, `RigidBody`, `LandEngine`): **0 tank-unique members**. The hits above are deform-point indices, effect-attachment slots, water-mesh geometry and fin/propeller placements - art data, none of it reachable by a steering or drive tune.

## 4. Nothing in the vocabulary names a track or a pivot

Token scan (`track|pivot|skid|neutral|turn_on|in_place|counter_rot|opposite`) over all module member paths and over `VOCABULARY.md` (52 sections):

| match | where | what it is |
|---|---|---|
| `VehicleCommon.tire_effects.effect_frame_delay_skid` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.tire_effects.effect_frame_hold_skid` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.tire_effects.min_skid_for_effect_front` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.tire_effects.min_skid_for_effect_rear` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.tire_effects.min_skid_velocity_for_skid_ms` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.tire_effects.skid_effect_drift_boost` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.tire_effects.skid_velocity_scale` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.tire_effects.slip_angle_to_peak_to_skid` | every land vehicle | tyre-smoke threshold, cosmetic |
| `VehicleCommon.train_common.train_track_width_scale` | every land vehicle | train track gauge, `CTrain` only |

VOCABULARY.md returns the same 9 names. **Zero** matches sit in the four card modules or in any driving module: there is no `track_*`, no `pivot_*`, no skid-steer or neutral-turn member to set.

## 5. What the entities actually are

| signal | tanks | fleet |
|---|---|---|
| `.epe` vehicle class | CCar x12 | CAirPlane x18, CBoat x35, CCar x126, CHelicopter x23, CTrain x12 |
| `root_class` in `WEAPON_WIRING` | CCar x12 builds | (armed entities only) |

Every tank build declares the same single vehicle class as every ordinary car, `CCar` - there is no `CTrackVehicle`-style type in the graph. Their containers carry only data file types:

| inner-file type | count (12 tank builds) |
|---|---|
| `.rbm` | 2496 |
| `.ddsc` | 1350 |
| `.effc` | 1152 |
| `.trim` | 876 |
| `.lod` | 705 |
| `.vmodc` | 354 |
| `.ctunec` | 204 |
| `.pfxc` | 54 |
| `.etunec` | 36 |
| `.wtunec` | 33 |
| `.ftunec` | 21 |
| `.epe` | 12 |
| `.fmod_guids` | 12 |
| `.physicsc` | 12 |
| `.stringlookup` | 12 |
| `.afsmb` | 9 |
| `.asb` | 9 |
| `.bsk` | 9 |

Script-like types in there: **0** (none). Wheel stations match `number_of_wheels` on all 12 tank builds, i.e. the physics is a wheel set, not a track belt.

## 6. Conclusion for MOD-2

**Turn-on-the-spot has no JC3 data carrier** - it becomes a named omission for MOD-2:

1. the four card modules are member-identical between tanks and cars;
2. no candidate member (nor their five-tuple) marks a tracked vehicle;
3. no driving module holds a tank-unique value, and the vocabulary has no track/pivot name;
4. the tanks are `CCar` wheel vehicles whose bundles contain data files only.

So a pivot, if the game has one, is decided in native code keyed to the vehicle's identity - data leaves no other discriminator. For the Batmobile's battle mode this means: do not expect a `land_*` member to grant turn-on-the-spot; if MOD-2 keeps the requirement it needs either a code-side probe (phase Q, one variable) or a translation-level omission row. `UNKNOWN` from these files: whether the shipped tanks pivot at all, the pivot's rate, and which native key decides it.

## 7. Validation and limits

`jc3tankturn.py --check` re-reads the decoded cache and asserts: 12 tank builds; the four card modules with 0 tank-only and 0 non-tank-only members; 0 tank-only module types; every candidate fails to separate and the five-tuple is shared by 27 non-tank builds; 262 tank-unique values with 0 in a driving module; 9 vocabulary matches, none in a driving module; 12/12 tank builds `CCar`; no script file type in the containers; wheel stations = `number_of_wheels` on all 12; the player/AI twin difference recorded. It then rebuilds both files and fails if `TANKTURN.json` or this document drifted (tamper test: changing one value in the json makes `--check` exit 1).

**Limits.** This is a data-side result: no file here can prove what native code does at runtime (the deciding logic is in the game executable, which this project does not read in this card). `wheels_friction_type`'s enum meaning (0/1/2) is `UNKNOWN` - it tracks the off-road tyre modules only loosely (40 of 47 users) and is not a track flag. `number_of_front_wheels = -1` means "unset/auto" is a guess, not a decoded label - `UNKNOWN`. The scan covers the 232 cached entity builds, not live archives.

Checkable: `python Tools/scripts/jc3tankturn.py --check` (record `TANKTURN.json`).
