# JC3 damage, health and immunity — where it actually lives

T-DM9 was `blocked` because `VehicleDamage` has no small-arms immunity member: the build
already sits at the shipped maximum in every armour channel and bullets still destroy the car.
This is the G2 search that looked outside the module, over **232 decoded `.epe` graphs / 91,157
objects** (`_JC3grab/detail`, produced by `jc3detail.py`). Re-runnable:
`python Tools/scripts/jc3_damage_search.py --write|--check`, record in `DAMAGE_MECHANISMS.json`.

## 1. The vehicle root carries an entity-level switch

Every vehicle entity's root object carries three properties that are **not** in any `.vmodc`:

| property | type | shipped value | what it is |
|---|---|---|---|
| `health` | float32 | **100.0** on all 233 roots | the entity's base health scale (percent) |
| `invulnerable` | int32 | **0** on all 233 roots | engine-level "cannot be damaged" gate |
| `damage` | int32 (object id) | 6 distinct across 126 cars | reference to the `VehicleDamage` module instance |

| root class | roots | `invulnerable` | `health` |
|---|---:|---|---|
| `CCar` | 126 | 0 × 126 | 100 × 126 |
| `CBoat` | 35 | 0 × 35 | 100 × 35 |
| `CHelicopter` | 23 | 0 × 23 | 100 × 23 |
| `CMotorBike` | 19 | 0 × 19 | 100 × 19 |
| `CAirPlane` | 18 | 0 × 18 | 100 × 18 |
| `CTrain` | 12 | 0 × 12 | 100 × 12 |

233 roots in 232 entities (one train entity carries two). So the division of labour is:

- **the module** (`lave_health_medium.vmodc`) holds health, thresholds, armour channels and the
  impact factor;
- **the entity root** holds the boolean the module cannot express.

Every *shipped* vehicle leaves the boolean at 0. No vehicle in the fleet is immune, which is
exactly why nine passes over `VOCABULARY.md` never saw a clue: the vocabulary is module members.

## 2. The flag is live, not vestigial

`CDamageController` — the destructible-prop controller used for cargo, barrels and the monorail
flatbed — carries the same pair, and **10 of its 104 objects ship `invulnerable = 1`** (in 4
entities: oldtruck cargo barrel/random/wine, monorail flatbed containers). Value `1` is authored
by the game and accepted by the engine; it is not a name-only field.

Two false leads, recorded so they are not re-chased:

- `CVehicleRule.health / invulnerable` (59 objects, 8 entities) is **spawn-rule metadata**
  (`chance`, `heat_level`, `spawn_event`); all values are 0 and it does not damage anything.
- `CConstraintBreakableDecoratorData.Indestructible` (8 objects, 1 entity) is a physics-constraint
  decorator on breakable props, not a vehicle.

## 3. The byte address

An `.epe` serialises each property as `type byte · uint32 Jenkins hash · value`. With
`hash_jenkins("invulnerable") = af4406fb`, the donor entity
(`Builds/test-085/aaf/…/v0300_…_civilian_01.epe`, 105,430 B) contains exactly one occurrence:

```text
type 0x0e @1162   hash af4406fb @1163   value 00 00 00 00 @1167   → int32 0
```

The type is calibrated by two neighbours whose values the graph dump also gives:

| property | type | value bytes | graph dump |
|---|---|---|---|
| `health` | `0x09` | `00 00 c8 42` = **100.0f** | 100 |
| `damage` | `0x0e` | `17 c2 f1 27` = **670155287** | 670155287 |
| `invulnerable` | `0x0e` | `00 00 00 00` = **0** | 0 |

So `0x09` is float32 and `0x0e` is int32, and writing the flag is a **4-byte edit at
`epe + 1167`: `00 00 00 00` → `01 00 00 00`**. The pack/repack route is the one the camera patch
already proved (`bmak_camfile.py`: assert the old bytes, patch, re-read; `bmak_cambuild.py`: repack
with the matching `.toc`).

`jc3_damage_search.py --epe <file.epe>` prints this triple for `health`, `invulnerable` and
`damage`, so the offset is verified per build rather than copied between them.

## 4. What this does to T-DM9

- It is **not** a value in `VehicleDamage` and cannot be reached from the module. Any further
  attempt to buy immunity with `bullet_armor` / `*_armor_strength` numbers is wasted work.
- It **is** a routable mechanism: one int32, at a named hash, with a value the game itself ships.
- Caveats to state before the probe:
  - the flag is **whole-vehicle**. It also blocks the destruction BmAK does have (tank battles),
    so it is the right switch for "ramming and small arms do not scratch it" and the wrong tool
    for "vulnerable only to heavy weapons". That finer split needs the damage channels, which can
    only reduce, not exempt.
  - nothing in the shipped vehicle fleet uses it, so the engine path is **unproven for a vehicle
    root**; the evidence that `1` is honoured comes from `CDamageController` (props).
- Probe build (one variable, no other edit): set `invulnerable = 1` on the Batmobile's `CCar`
  root. Take: 200 rounds of SMG at the body + a full-boost ram into traffic and into a wall →
  health bar untouched, no fire, no explosion; then confirm a deliberate high-explosive still
  behaves as the flag implies.

## 5. Reproduce

```bash
python Tools/scripts/jc3_damage_search.py --write      # re-scan 232 graphs → DAMAGE_MECHANISMS.json
python Tools/scripts/jc3_damage_search.py --check      # the record still matches the decode
python Tools/scripts/jc3_damage_search.py --epe \
  Builds/test-085/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe
```

The graph dumps themselves are produced by `Tools/scripts/jc3detail.py` from the archives; they
stay outside the repository (`E:/Modding/_JC3grab/detail/`), only the derived record is committed.
