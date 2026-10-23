# JC3 wheel stations from `.physicsc`

Recovered by `Tools/scripts/jc3phys.py` from **232** entity bundles.
`.physicsc` is a Havok 2014 packfile, so these are read structurally (four
`float4` station quads forming a rectangle), not via a full Havok reader.

One station set: **17** entities; more than one: 3; none: 212.

Cross-check against the named `land_global.base_wheel_hardpoint_positions`: **17 agree**, 0 disagree (145 entities have named stations).

| quantity | min | median | max |
|---|---|---|---|
| wheelbase (m) | 2.418 | 3.003 | 3.228 |
| track (m) | 1.34 | 1.77 | 2.462 |

wheelbase / body length: 0.56 … 0.632 (median 0.601) — a plausibility check, not a rule.

## Land vehicles

| entity | track | wheelbase | hub y | body x×y×z | wb/length |
|---|---|---|---|---|---|
| `v0502_car_solar_modernsedan/v0502_car_solar_modernsedan_civic_police_01.ee` | 1.636 | 2.418 | 0.316 | 2.0196 × 1.6261 × 4.2288 | 0.572 |
| `v0502_car_solar_modernsedan/v0502_car_solar_modernsedan_civilian_01.ee` | 1.636 | 2.418 | 0.316 | 2.0267 × 1.5113 × 4.233 | 0.571 |
| `v0502_car_solar_modernsedan/v0502_car_solar_modernsedan_debug.ee` | 1.636 | 2.418 | 0.316 | 1.8328 × 1.37 × 4.1435 | 0.584 |
| `v0002_car_autostraad_oldcampervan/v0002_car_autostraad_oldcampervan_civilian_01.ee` | 1.34 | 2.465 | 0.333 | 1.9961 × 2.0128 × 4.3992 | 0.56 |
| `v0002_car_autostraad_oldcampervan/v0002_car_autostraad_oldcampervan_civilian_z80.ee` | 1.34 | 2.465 | 0.333 | 1.9961 × 2.0128 × 4.3992 | 0.56 |
| `v0002_car_autostraad_oldcampervan/v0002_car_autostraad_oldcampervan_debug.ee` | 1.34 | 2.465 | 0.333 | 1.726 × 1.8193 × 4.2327 | 0.582 |
| `v0508_car_solar_oldcompact/v0508_car_solar_oldcompact_civilian_01.ee` | 1.47 | 2.804 | 0.321 | 2.1657 × 1.4837 × 4.638 | 0.605 |
| `v0508_car_solar_oldcompact/v0508_car_solar_oldcompact_debug.ee` | 1.47 | 2.804 | 0.321 | 1.8516 × 1.3069 × 4.4507 | 0.63 |
| `v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee` | 1.77 | 3.003 | 0.4 | 2.1121 × 1.4051 × 4.9999 | 0.601 |
| `v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee` | 1.77 | 3.003 | 0.4 | 2.1121 × 1.4051 × 4.9999 | 0.601 |
| `v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_signature_preorder.ee` | 1.77 | 3.003 | 0.4 | 2.1121 × 1.4051 × 4.9999 | 0.601 |
| `v0009_car_autostraad_modernsaloon/v0009_car_autostraad_modernsaloon_civilian_01.ee` | 1.772 | 3.197 | 0.342 | 2.0417 × 1.4633 × 5.1968 | 0.615 |
| `v0009_car_autostraad_modernsaloon/v0009_car_autostraad_modernsaloon_debug.ee` | 1.772 | 3.197 | 0.342 | 2.0417 × 1.4633 × 5.1968 | 0.615 |
| `v0009_car_autostraad_modernsaloon/v0009_car_autostraad_modernsaloon_premium_01.ee` | 1.772 | 3.197 | 0.342 | 2.0417 × 1.4633 × 5.1968 | 0.615 |
| `v0603_car_urga_smalltank/v0603_car_urga_smalltank_debug.ee` | 2.462 | 3.228 | 0.615 | 2.4586 × 1.5084 × 5.1075 | 0.632 |
| `v0603_car_urga_smalltank/v0603_car_urga_smalltank_military_01.ee` | 2.462 | 3.228 | 0.615 | 2.4586 × 1.5084 × 5.1075 | 0.632 |
| `v0603_car_urga_smalltank/v0603_car_urga_smalltank_rebel_01.ee` | 2.462 | 3.228 | 0.615 | 2.4586 × 1.5084 × 5.1075 | 0.632 |
