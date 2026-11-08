# Brake deceleration bridge: BmAK 300 vs the measured 3.5–3.8 m/s²

Question: using BmAK's `MaxBrakeTorque` **300** and the car's own mass and wheel radius, what
stopping deceleration do BmAK's values imply, how does that compare with the footage band named
in the T-K1 cell, and is the chosen JC3 value **5,000** supported by any BmAK-derived number?

Read first, as required: `Working/Translation/COMPROMISES_T.md`:84 (T-K1) records the choice —
“`SVehicleSimCar.MaxBrakeTorque` **300** ... the bridge is disproven by magnitude: 4 × 300 N·m
over 6,000 kg × 0.683 m = **0.29 m/s²**, against the 3.5–3.8 m/s² ... **Build instead:**
max_brake_torque 5000 (class).” The row itself is `Working/Translation/T_ROWS.jsonl`:37.

Method fixed before the numbers: the direct bridge `F = T / r` over `n` braked wheels, then
`a = F / m`. It is the same arithmetic T-K1 used, so the comparison is like-for-like. The
bridge is itself unproven — T-K1 declared it disproven by magnitude, not by units. Every row
carries decoded, derived or UNKNOWN.

| # | quantity | value | status | evidence / step |
|---|---|---|---|---|
| 1 | BmAK `SVehicleSimCar.MaxBrakeTorque` | 300 N·m | decoded | `CHAIN.json` 4 records, offset 236, FloatProperty, named_by sdk-layout |
| 2 | car mass `RigidBody.mass` | 6000 kg | derived (class, T-M1) | `Working/Translation/current.json` modules.RigidBody; T-M1: 6,000 kg armored transport, `T3_FLEET.md` p75 |
| 3 | front wheel radius `LandGlobal.front_wheels.radius` | 0.682750 m | decoded (module) | same file, modules.LandGlobal; T-G6 keeps the mesh radius |
| 4 | rear wheel radius `LandGlobal.rear_wheels.radius` | 0.682650 m | decoded (module) | same file; sensitivity line only |
| 5 | braked wheels `n` | 4 (assumed: all four, front and rear torque equal) | UNKNOWN | no JC3 member says how many wheels one brake-torque value drives; front/rear are both 5,000 in `Brakes` |
| 6 | brake force per wheel `T / r` | 439.4 N | derived | 300 / 0.682750 |
| 7 | total brake force `n × T / r` | 1,757.6 N | derived | 4 × 439.4 |
| 8 | **deceleration implied by BmAK 300**  `a = n·T / (m·r)` | **0.2929 m/s²** | derived | 4×300 / (6000×0.682750); with the rear radius 0.2930 |
| 9 | measured deceleration (footage, QA-1 take 1) | 3.5 m/s² avg (138→100 km/h, 3.0 s, ~99 m); 3.82 last 122→100; 3.82 on grass | measured | `Working/Translation/QA1_RESULTS.md` §4; the 100→0 km/h tarmac stop was **not captured** (car left the road) |
| 10 | ratio measured / BmAK-implied | 11.95× – 12.97× | derived | same two rows |
| 11 | **JC3 torque for 3.5 m/s²**  `T = a·m·r / n` | **3,584 N·m per wheel** | derived | 3.5×6000×0.682750 / 4 |
| 12 | **JC3 torque for 3.8 m/s²** | **3,892 N·m per wheel** | derived | 3.8×6000×0.682750 / 4 |
| 13 | JC3 torque for the 3.82 m/s² segment | 3,912 N·m per wheel | derived | 3.82×m×r / 4 |
| 14 | BmAK value as a JC3 input | 300 N·m | decoded, not transferable | T-K1: the member's scale is not JC3's; carrying 300 would give the same 0.29 m/s² |
| 15 | built JC3 value `brakes.front/rear.max_brake_torque` | 5000 / 5000 N·m | class (T-K1; `COMPROMISES_T.md`:84) | `current.json` modules.Brakes; class median at 3–6 t, chosen because the bridge is disproven |
| 16 | deceleration implied by 5,000 | 4.882 m/s² | derived | 4×5000 / (6000×0.682750) |
| 17 | deceleration implied by 2,500 (armored-transport class cell) | 2.441 m/s² | derived | 4×2500 / (m·r) |
| 18 | deceleration implied by 10,000 (pre-edit value) | 9.764 m/s² | derived | 4×10000 / (m·r) |
| 19 | 5,000 vs the measured band | 1.39× – 1.28× above | derived | same rows |
| 20 | per-axle reading of 5,000 (n = 2) | 2.441 m/s² | UNKNOWN which reading applies | if JC3's brake torque drives an axle rather than a wheel, every `a` halves |
| 21 | grip ceiling on deceleration (tyre μ) | UNKNOWN | UNKNOWN | BmAK has no friction member (T-R1); JC3 ships `arcade_friction_multiplier` 3, not a μ; a torque rise past the grip limit changes nothing |
| 22 | loaded (dynamic) wheel radius | UNKNOWN | UNKNOWN | 0.68275 m is the static mesh radius kept by T-G6; deflection under load is not modelled here |

## Verdict

**5,000 is not supported by any BmAK-derived number.** The only brake torque BmAK stores is
300 N·m (four records, one per sim). Through the direct bridge it gives
**0.293 m/s²**, while the footage band the T-K1 cell names is **3.5–3.8 m/s²**;
reproducing that band would need **3,584–3,892 N·m per wheel**
(4 braked wheels), i.e. **11.9–13.0×** BmAK's number. 5,000 lands
on neither: it implies **4.88 m/s²**, **1.28–1.39×
above** the only measured deceleration.

What 5,000 *is* — stated in its own row — is the **class median at 3–6 t**, chosen because the
direct bridge is disproven. That is a class fallback, not a derivation: no BmAK member, no
arithmetic on BmAK values and no measured point produces 5,000. The correct label is “class
median, bridge disproven by magnitude”, which is what `COMPROMISES_T.md` already says; it should
not be presented as BmAK-derived.

Two limits keep even the comparison open: whether the torque is per wheel or per axle (which
halves or doubles every `a` above) and the tyre grip ceiling (a value past the grip limit does
not shorten the stop). Both are UNKNOWN in the table, so the table fixes the arithmetic and the
size of the gap, not the physics of JC3's brake application.

## Sources

* `Working/Translation/T_ROWS.jsonl`:37 — T-K1 row (cells, disproof arithmetic, 5,000 class median).
* `Working/Translation/COMPROMISES_T.md`:84 — the T-K1 compromise entry.
* `Research/BatmobileGrab/CHAIN.json` — `SVehicleSimCar.MaxBrakeTorque` 300.0, offset 236, 4 records.
* `Working/Translation/current.json` — modules `RigidBody` (mass), `LandGlobal` (radii), `Brakes` (5,000/5,000).
* `Working/Translation/QA1_RESULTS.md` §4 — the measured braking segments and the missing 100→0 tarmac stop.
