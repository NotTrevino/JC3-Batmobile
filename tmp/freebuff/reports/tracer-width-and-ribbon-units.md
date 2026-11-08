# Tracer width and ribbon units — the three fields FX-12/16 left without a unit

Scope: only the three unit questions. The tracer/trail carriers are settled in
`tmp/freebuff/reports/fx12-16-tracer-and-trail.md` (cited, not redone) and the round-trail term search is
settled in `tmp/freebuff/reports/t-fx16-term.md` (cited, not redone). The material and gloss rows are
closed in `tmp/freebuff/reports/apply-colour-and-material-rows.md` and are **out of scope**.

Method: compare the BmAK tracer tune bytes with the field layout of the shipped JC3 `.wtunec` entries,
at the index locations FX-12/16 names — `Research/JC3Grab/INDEX.jsonl:38665`
(`w602_mediumtank_canon.wtunec`, `patch_win64/game1` @441,880,576), `:38666`
(`w603_mediumtank_mgun.wtunec`, @441,894,912) and `:37237`
(`v0200_car_capstone_apc_debug.ee`, `archives_win64/game35` @160,751,616 → inner
`w206_mounted_capstone_m2hm.wtunec`).

`tmp/fx12_probe.py` was re-run for this brief and reproduced all three files at their recorded sizes and
sha1s (`14224 / 1a8c072a…`, `14223 / d9f58989…`, `12677 / 20f90fb2…`), so the offsets below are read from
the same bytes FX-12/16 used, not copied from its prose.

## The verdict table

| field | BmAK raw value | JC3 field it maps to | unit | verdict |
|---|---|---|---|---|
| `tracer_expand_width` | no direct BmAK member; the trail's analogue is the ribbon's `ParticleModuleSize` `StartSize` **[50.0, 0.0, 0.0] uu = 0.50 m** plus a `SizeMultiplyLife` curve whose values are not decoded | `bullet_weapon[].tuning.bullet_base_tuning.tracer_expand_width`, **float @0x18C (396)**; `0.0` on w602 player, **2.0** on w603 player, **2.0** on w206 player (AI block: 2.0 on all three) | **metres added to the streak width** (absolute, not per second) | **derived** |
| `tracer_per_smoke_trail` | the trail's own rates: ribbon spawn **8.0 /s**, sprite spawn **1.0 /s** — neither is a per-tracer ratio, so there is no BmAK value to convert | `…bullet_base_tuning.tracer_per_smoke_trail`, **uint8 @0x19C (412)**; **1** on w602, **0** on w603 player (off), **3** on w206 | **count — tracers per smoke ribbon, `0` = off** (not an interval) | **derived** |
| int **250** at tag `@104` | `ParticleModuleTypeDataRibbon` tag at **0x68 (104)**, `IntProperty` **250**; siblings `@108` int **50**, `@112` bool **true** (grab label "tiles"), `@124` float **800.0** | **none** — `WeaponTuning` has no ribbon/type-data member (0 of 97 member names; the whole class is 22 ids) | **segment/tessellation count** (not centimetres) | **derived** |

## 1. Why `tracer_expand_width` is metres, not m/s

The layout is the deciding evidence, and it is visible in one block of the same tune:

| offset (player block) | member | type | value (w602 / w603 / w206) |
|---:|---|---|---|
| 0x180 (384) | `tracer_fire_velocity` | float | 900.0 / 750.0 / 600.0 |
| 0x184 (388) | `tracer_fire_length` | float | 30.0 / 20.0 / 15.0 |
| 0x188 (392) | `tracer_fire_width` | float | 0.5 / 0.05 / 0.03 |
| **0x18C (396)** | **`tracer_expand_width`** | **float** | **0.0 / 2.0 / 2.0** |
| 0x190 (400) | `tracer_time_to_live` | float | 0.0 / 0.25 / 0.0 |

1. **It sits inside the spatial triple** — `length`, `width`, `expand` are three contiguous floats, and
   the time field is the *next* one. A rate would be grouped with a life or given a rate word; the only
   rate-shaped member here is `tracer_fire_velocity` (the streak's stretch speed), which is named for it.
2. **It is independent of the life field.** `2.0` ships with `tracer_time_to_live` = **0.0** (w206
   player), **0.25** (w603), **0.4** (w602 AI) and **0.5** (w206 AI). A m/s reading only means anything
   as `expand × TTL`, and the tune carries no second time factor to do that multiplication — the same
   value would be inert on the weapon whose TTL is 0 yet still ships as 2.0.
3. **`0.0` must mean "no expansion".** As a multiplier a zero would collapse the streak to zero width,
   which no fleet weapon does; as an additive length `0.0` is simply "no growth", and w602 player (a
   0.5 m wide, 30 m long streak) is the one block that leaves it at 0.
4. **The naming convention of this class names rates explicitly**: `fire_rate` ("seconds per shot",
   `WEAPONS.md:82`), `scatter_recover_rate`, `tracer_fire_velocity`. `tracer_expand_width` carries no rate
   word while its own neighbour does — the absence is informative inside one 9-member block.

So the readable value is "the streak's width grows to `tracer_fire_width + tracer_expand_width` metres
over its life". That is derived, not decoded: the ADF stores no unit tag.

## 2. Why `tracer_per_smoke_trail` is a count, not an interval

1. **Type.** It is a **uint8**, and it is packed immediately before another uint8 count,
   `bullets_per_tracer` (`@0x19D`), which every reader agrees is "1 tracer per N bullets". Two adjacent
   `*_per_*` uint8s are the same kind of value.
2. **The block's time values are floats.** `tracer_time_to_live` (s), `smoke_trail_tile_size` (m) and
   `fire_rate` (s/shot) are all floats; an interval in seconds could not be expressed in a uint8 without
   a second scale member, and none exists in the 9-member block.
3. **Values.** 0…4 across the fleet, with `0` on w603's player block — exactly how an "off" count reads
   (no smoke ribbon on any tracer). An interval of `0` seconds would be undefined rather than off.
4. **Name shape.** `per_smoke_trail` = "per smoke trail", i.e. how many tracers share one — the same
   `per` used by `bullets_per_tracer`, not `interval`/`_time`/`_rate`.

Reading: `1` = a smoke ribbon on every tracer, `3` = one every third tracer, `0` = none. Derived.

## 3. Why the ribbon's `250` at `@104` is a count, not centimetres

1. **Type against the export's own convention.** The tag is an **`IntProperty`**; every distance in the
   same `Batmobile_CanonTrail` export is a **`FloatProperty`**: `StartSize` `[50.0, 0.0, 0.0]`,
   `StartLocation` `[-50.0, 0.0, 0.0]`, the float `800.0` at `@124` (`PARTICLES.md:3769-3773`). A
   centimetre distance written as an integer would be the only one in the system.
2. **The ribbon's own geometry rules 2.5 m out.** Width `0.5 m`, lifetime `1.25 s`, on a round flying
   `400 m/s` (`40000.0 cm/s`, `WEAPONS.md:368`) — the ribbon spans roughly `500 m`. A `250 cm = 2.50 m`
   ribbon is 0.5 % of that; `250` segments is about `2 m` per segment, the tessellation such a ribbon
   needs, and it pairs with the `tiles: true` flag (texture repeats along the ribbon rather than being
   stretched once).
3. **The label is not evidence.** `grab_particles.py:248` builds `{"length": 0x68, "tiles": 0x70,
   "max_length": 0x74, "frequency": 0x78}` as a **heuristic map**, and FX-12/16 §7 already records that
   the UE property name behind the tag was never recovered. "length" here is the grab's guess, and the
   `@108 = 50` int that the map does not cover is a second count-shaped sibling.

Reading: a tessellation/segment count for the ribbon. Derived; it changes no build value, because JC3's
tune has no ribbon member at all — the build writes `tracer_fire_length` (metres) instead.

## 4. What remains open

| item | why it stays open | what would settle it |
|---|---|---|
| whether the engine applies `tracer_expand_width` as a terminal width or as a width-per-frame | no unit metadata in ADF v4; the layout only proves it is a length, not verb | a probe: set `tracer_expand_width` 0 vs 2 on the same tune and measure the streak's width at end of life |
| the exact meaning of `tracer_per_smoke_trail` values 2 and 4 | only 0/1/3 appear in the three tunes read; 2/4 are fleet values not opened here | read the two remaining fleet tune blocks, or a probe counting smoke per tracer |
| which UE property is `@104` of `ParticleModuleTypeDataRibbon` | the class is not in `BMSDK_OFFSETS.json` (0 classes match `Ribbon`/`TypeData`), so no name map exists in the grab | a `BmGame` class dump that includes the particle module classes, or the engine's ribbon serializer |
| the ribbon's `VelocityOverLifetime` curve | not captured by G1-6 (FX-12/16 §7 limit b) | a re-grab of `ParticleModuleVelocityOverLifetime` for emitter 4870 |

## 5. Limits

Byte reads only: three `.wtunec` blocks at the INDEX locations above, the BmAK ribbon module tags in
`objects.jsonl`/`PARTICLES.md`, and `grab_particles.py`'s tag map. Nothing was launched, no archive or
build was written, and no file outside `tmp/freebuff/reports` was touched. The three verdicts are
`derived` — each rests on type/adjacency/neighbour evidence within one block, not on a unit field, so the
first two rows are safe to build against and the probe in §4 is what would promote them to `decoded`.
