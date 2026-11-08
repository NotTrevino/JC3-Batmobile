# Translation fleet evidence (heavy class)

Computed over **156 land vehicles** that carry `rigid_body.mass`. Each cell is
*n*, the **median**, and the interquartile band (p25 … p75). These are the numbers behind
the class claims re-decided in this pass and the T-3 factors, where BmAK has no value with
compatible units. `-1` in a steering or brake member is the game's sentinel, not a measured
time.

| member | all land | 3-8 t | 6 t+ |
|---|---|---|---|
| `rigid body mass` | n=156  **1850**  (712.5 … 5100) | n=35  **5100**  (3500 … 6000) | n=38  **1.5e+04**  (8125 … 2.275e+04) |
| `rigid body inertia yaw` | n=156  **1.986**  (1.45 … 4) | n=35  **2.94**  (2.48 … 4.08) | n=38  **8.745**  (4.638 … 25) |
| `rigid body inertia pitch` | n=156  **1.987**  (1.46 … 3) | n=35  **3**  (2.532 … 4.08) | n=38  **8.132**  (4.67 … 25) |
| `rigid body inertia roll` | n=156  **0.74**  (0.4476 … 1.2) | n=35  **0.8376**  (0.6 … 2) | n=38  **1.6**  (1.1 … 3.6) |
| `rigid body centre of mass bias` | n=156  **-0.3**  (-0.45 … 0) | n=35  **-0.3**  (-1.1 … 0) | n=38  **0**  (-0.85 … 0) |
| `damage max health` | n=156  **700**  (700 … 1400) | n=35  **1400**  (1400 … 1800) | n=38  **1600**  (1400 … 2000) |
| `damage deform scale` | n=156  **1**  (1 … 1) | n=35  **1**  (1 … 1) | n=38  **1**  (1 … 1) |
| `damage impact_damage_factor` | n=156  **1**  (1 … 1) | n=35  **1**  (1 … 1) | n=38  **1**  (1 … 1) |
| `damage impact_armor` | n=156  **0**  (0 … 0) | n=35  **0**  (0 … 0) | n=38  **0**  (0 … 5) |
| `damage explosion_threshold` | n=156  **700**  (700 … 1000) | n=35  **1000**  (1000 … 1800) | n=38  **1400**  (1000 … 2500) |
| `suspension front length` | n=125  **0.18**  (0.18 … 0.32) | n=35  **0.18**  (0.18 … 0.6) | n=26  **0.18**  (0.18 … 0.75) |
| `suspension front min_length` | n=125  **0**  (0 … 0) | n=35  **0**  (0 … 0) | n=26  **0**  (0 … 0) |
| `suspension front max_length_offset` | n=125  **0**  (0 … 0) | n=35  **0**  (0 … 0) | n=26  **0**  (0 … 0) |
| `suspension front damp clamp (m/s)` | n=125  **1.5**  (1.5 … 1.5) | n=35  **1.5**  (1.5 … 1000) | n=26  **1.5**  (1.5 … 1.5) |
| `suspension front lateral tyre offset` | n=125  **0.2**  (0.1 … 0.3) | n=35  **0.2**  (0 … 0.3) | n=26  **0**  (0 … 0.325) |
| `wheel front mass` | n=144  **75**  (50 … 150) | n=35  **150**  (75 … 150) | n=26  **175**  (75 … 1000) |
| `wheel rear mass` | n=144  **75**  (50 … 150) | n=35  **150**  (75 … 150) | n=26  **287.5**  (150 … 1000) |
| `wheel front shape cast` | n=144  **0**  (0 … 0) | n=35  **0**  (0 … 0) | n=26  **0**  (0 … 0) |
| `brakes handbrake friction factor` | n=144  **2**  (1 … 3) | n=35  **2**  (2 … 4) | n=26  **1**  (1 … 2.25) |
| `brakes front min_time_to_block` | n=144  **-1**  (-1 … 1) | n=35  **1**  (-1 … 1) | n=26  **-1**  (-1 … 1) |
| `steering max speed t to full (s)` | n=125  **-1**  (-1 … 0.8) | n=35  **-1**  (-1 … -1) | n=26  **-1**  (-1 … 1.25) |
| `steering input power pc` | n=125  **2**  (1 … 3) | n=35  **1**  (1 … 2) | n=26  **2**  (1 … 3) |
| `steering input power durango` | n=125  **3**  (1 … 3) | n=35  **1**  (1 … 3) | n=26  **3**  (1 … 3) |
| `steering input power orbis` | n=125  **2**  (1 … 3) | n=35  **1**  (1 … 2) | n=26  **2**  (1 … 3) |
| `steering countersteer factor` | n=125  **3**  (2.5 … 5) | n=35  **2.5**  (2.5 … 3) | n=26  **3**  (2.5 … 5) |
| `steering in speed factor` | n=125  **2**  (2 … 3) | n=35  **2**  (2 … 2) | n=26  **2**  (2 … 3) |
| `steering drift aligning` | n=125  **0.5**  (0.5 … 0.5) | n=35  **0.5**  (0.5 … 0.5) | n=26  **0.5**  (0.5 … 0.5) |
| `drift max angle (deg)` | n=144  **45**  (35 … 45) | n=35  **45**  (40 … 45) | n=26  **45**  (45 … 45) |
| `drift entry slip (deg)` | n=144  **25**  (20 … 180) | n=35  **180**  (30 … 180) | n=26  **180**  (140 … 180) |
| `drift min speed (km/h)` | n=144  **10**  (10 … 30) | n=35  **10**  (10 … 30) | n=26  **10**  (10 … 10) |
| `drift steering sensitivity` | n=144  **2**  (2 … 3) | n=35  **2**  (2 … 2) | n=26  **2**  (2 … 2) |
| `nitro torque multiplier` | n=144  **2**  (1.5 … 2) | n=35  **2**  (2 … 2) | n=26  **2**  (2 … 2) |
| `nitro extra top speed (km/h)` | n=144  **40**  (40 … 40) | n=35  **40**  (40 … 40) | n=26  **40**  (40 … 40) |
| `nitro grip multiplier` | n=144  **2**  (1.2 … 2) | n=35  **2**  (1.5 … 2) | n=26  **2**  (2 … 2) |
| `nitro push force` | n=144  **1.5e+04**  (1.5e+04 … 1.5e+04) | n=35  **1.5e+04**  (1.5e+04 … 1.5e+04) | n=26  **1.5e+04**  (1.5e+04 … 1.5e+04) |
| `nitro blend time (s)` | n=144  **0.2**  (0.2 … 0.2) | n=35  **0.2**  (0.2 … 0.2) | n=26  **0.2**  (0.2 … 0.2) |
| `aero frontal area` | n=144  **2.76**  (2.1 … 4.87) | n=35  **6.5**  (4 … 6.72) | n=26  **6.95**  (3.613 … 20) |
| `misc official top speed (km/h)` | n=156  **150**  (150 … 200) | n=35  **150**  (150 … 150) | n=38  **150**  (105 … 150) |
| `tire effects skid velocity (m/s)` | n=156  **0.5**  (0.5 … 0.5) | n=35  **0.5**  (0.5 … 0.5) | n=38  **0.5**  (0.5 … 0.5) |
| `tire effects slip to skid` | n=156  **0.8**  (0.8 … 0.8) | n=35  **0.8**  (0.8 … 0.8) | n=38  **0.8**  (0.8 … 0.8) |
| `tire effects skid velocity scale` | n=156  **0.25**  (0.25 … 0.25) | n=35  **0.25**  (0.25 … 0.25) | n=38  **0.25**  (0.25 … 0.25) |
