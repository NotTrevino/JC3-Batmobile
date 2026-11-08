# T-DM7 — the ram speed band tied to JC3's outgoing contact channel

Row: `Working/Translation/T_ROWS.jsonl:95` (T-DM7, disposition `next`). Inputs read
first, not re-derived here: `tmp/freebuff/reports/ram-assist-closest-system-plan.md`
(§1, §2.1-2.5, §4, §7), `tmp/freebuff/reports/audit-ram-assist-plan-numbers.md` (claim table,
C1-C6) and `tmp/freebuff/reports/carrier-ram-and-dodge.md` (§0, §2, §9).

Settled by those reports and taken as given: the member and its 100000 population
(`VOCABULARY.md`:1415-1418), the block's offsets `0x130-0x13C` and the 12,271-byte file
(ram plan §2.1), the archetype band 20/150/2.25/2.0 (ram plan §1), the `min_rpm` 1260
derivation (§2.3) and the 2000/s reference rate (§2.4).

Labels: **decoded** = read from the named file at the named line/offset; **derived** =
arithmetic over decoded inputs; **UNKNOWN** = searched and not settled, with the settler named.

## 1. Is the block evaluated on a car at all?

**Loaded on a car: decoded. Evaluated on a car: UNKNOWN.** The two claims are separate and only
the first is in the files.

| step | evidence | label |
|---|---|---|
| the block is in the Batmobile's own module set | `Working/Translation/current.json` line(s) 27827, 27828, 27829, 27830, 28246, 28247, 28248, 28249: `rotor_collision.damage_to_other_per_second` = 100000, under module `VehicleCommon`, `VehicleCommon (vehicle_common.vmodc)` (`vehicle_common.vmodc`) | decoded |
| the same block is in every vehicle's set | `Research/JC3Grab/VOCABULARY.md` lines 1415, 1416, 1417, 1418 — `rotor_collision.damage_to_other_per_second` float, 100000 .. 100000, n=232, donor 100000 | decoded |
| the block sits in the shared vehicle module, not a car-only module | ram plan §2.1: one `VehicleCommon` instance at 0x50, `rotor_collision` at 0x130, rate at **0x138**, `min_rpm` 0x130, `mass_ratio_when_no_mass` 0x134, `light_object_mass_ratio` 0x13C — read back by struct.unpack | decoded |
| a car has nothing for the gate to read | ram plan §2.2: the Batmobile ships **no `vehicle_parts` module**, so no rotor part exists and any rotor-RPM read is 0 | decoded |
| the engine's consumer runs the block for a `CCar` | no file names the consumer; the member name is rotor-bound and the gate's input is unnamed. Static settler = the RotorCollision consumer in `JustCause3.exe`, not decoded; experiment = **Q-RAM-1A** (`min_rpm` 0) | **UNKNOWN** |

So the honest answer to the open question is: **the data says a car carries the block; only the
engine can say whether it acts on it.** The name plus the missing rotor part is a reason to doubt
it, not proof. The plan's two-stage probe is the right settler and is not repeated here.

## 2. What value and gating reproduce each band edge

The band has two edges and JC3 has **one gate**; the gate can buy the floor, nothing can buy the
ceiling.

| band edge | member / value | what it reproduces | label |
|---|---|---|---|
| floor **20 km/h** | `rotor_collision.min_rpm` @0x130 = **1260** | engine RPM at 20 km/h in 1st (radius 0.68265, final drive 5.1401253, 1st 3.15: 77.71 wheel rpm x 16.19 = 1258 -> 1260). Fires above the floor **only if** the gate reads engine RPM (H1); under H2 (rotor RPM, 0 on a car) it never fires | derived (ram plan §2.3) |
| floor, H2-safe variant | `min_rpm` = **0** | removes the gate entirely so the channel fires on any contact; this is the stage-A control, not a band edge | derived (ram plan §2.5) |
| ceiling **150 km/h** | **none** | no `max_rpm`, no speed member, no max-speed gate in the block or beside it. Cannot be expressed; the band's top is a named gap | **UNKNOWN** (searched: ram plan §2.3, §3; carrier §2, §9) |
| rate magnitude | `damage_to_other_per_second` @0x138 = **2000/s** | a mid-band 80 km/h ram (~0.05 s contact) removes a 100-point victim bar; at 20 km/h it caps at 100, at 150 km/h it deals 52.8 — the speed-inverse ramp | derived (ram plan §2.4) |
| strafe **2.25** / boost **2.0** | none | one rate, no per-state input. If a multiplier existed: 4500/s and 4000/s | **UNKNOWN** (ram plan §2.4) |
| mass scaling | `light_object_mass_ratio` 0.02 (0x13C), `mass_ratio_when_no_mass` 0.1 (0x134) | kept as shipped: 40/s against a light prop, 200/s against a massless object | decoded (ram plan §2.1) |

Arithmetic check on the two edges, using the plan's contact model `t = 1.1 m / v`:

| speed | contact time | damage at 2000/s | BmAK's intent |
|---:|---:|---:|---|
| 20 km/h | 0.198 s | 396 -> capped 100 | ≈ 0: the band starts here, so damage should be minimal |
| 80 km/h | 0.050 s | 100 | ≈ 46 % of max |
| 150 km/h | 0.026 s | 52.8 | 100 %: the band ends here, so damage should be max |

**No single value reproduces both edges.** To make 150 km/h lethal you need 
`100 / 0.0264 = 3788/s`, which then deals 150+ at 80 km/h (capped 100) and still caps at 20 km/h;
to make 20 km/h harmless you need the gate, not the rate. The floor is a gate problem, the ceiling
is an absent-member problem, and the middle is inverted either way. That is why the build buys the
floor with `min_rpm` and declares the ramp.

## 3. Which module of the Batmobile entity should carry the edit

**`VehicleCommon` — the entity's `vehicle_common.vmodc` — edited as a private copy.** The block is
loaded through that module in the Batmobile's own set (`current.json`: module
`VehicleCommon`, `VehicleCommon (vehicle_common.vmodc)`, file `vehicle_common.vmodc`; rate value at lines
27827, 27828, 27829, 27830, 28246, 28247, 28248, 28249). The shipped original lives at
`Builds/bm-RC2/aaf/editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` in the shared vehicle module directory and is **never edited** (R7: private copy,
then repoint the entity's module entry and add the file to `@files.xml`; ram plan §2.1, §2.5).

Build tree check: `Builds/bm-RC2/aaf/editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc` exists on disk = **True**. The write is four 4-byte
floats at fixed offsets in a 12,271-byte file whose size does not change; `.toc` re-point with
`eetoc.py patch`; values read back with `jc3adf.py dump` before packing.

Companion module in the same entity: `VehicleDamage.impact_damage_factor` stays **0** (T-DM8), or
the ram damages the Batmobile itself.

## 4. If the block is not evaluated on a car

**Closest JC3 system that applies contact damage on a ground vehicle: none decoded.** The nearest
*applied* damage to another object on a ground vehicle is the vehicle-owned `CForcePulse`
explosion (307 objects, 126 owned by a `CCar`), which fires on an explosion and never on contact
(`FORCEPULSE.md`: collision 0 of 23 tune paths). Weapons are the other route, and they are
projectiles, not contact.

**Build step that closes the gap:** stage A is the test, not a guess — private copy with
`min_rpm` 0 and rate 2000 (Q-RAM-1A). A negative result proves the consumer does not run for a
car; the fallback is then a `CForcePulse` on the ram button (B-16-style, speculative) or
contact damage in code, and either way T-DM7's band stays a named omission rather than a carried
value.

## 5. Pilot card (one sentence)

> **Q-RAM-1B** — At 80 km/h (inside the 20–150 band) a head-on ram must remove **40–100 %** of a
> stock car's 100-point health bar while the Batmobile's own bar does not move, and at 10 km/h
> (outside the band, below the 1260 gate) the same hit must remove **0–5 %**; a zero at 80 km/h
> means the gate reads rotor RPM and `min_rpm` reverts to 0.

## 6. Labels at a glance

| claim | label |
|---|---|
| `rotor_collision.damage_to_other_per_second` 100000, n=232 | decoded (`VOCABULARY.md`:1415) |
| block in `VehicleCommon` at 0x130-0x13C, rate at 0x138 | decoded (ram plan §2.1) |
| Batmobile module set carries `VehicleCommon` / `vehicle_common.vmodc` | decoded (`current.json`) |
| 20 km/h floor = `min_rpm` 1260 (engine-RPM reading) | derived (gearing, ram plan §2.3) |
| 2000/s mid-band rate; 4500/4000 if a state multiplier existed | derived / UNKNOWN |
| 150 km/h ceiling | **UNKNOWN** — no member |
| consumer runs the block on a `CCar` | **UNKNOWN** — Q-RAM-1A / the exe consumer |

## Sources

* `Working/Translation/T_ROWS.jsonl:95` — the row and its `next` disposition.
* `Working/Translation/current.json` — rotor lines 27827, 27828, 27829, 27830, 28246, 28247, 28248, 28249; module `VehicleCommon`, `VehicleCommon (vehicle_common.vmodc)` / `vehicle_common.vmodc`.
* `Research/JC3Grab/VOCABULARY.md` lines 1415, 1416, 1417, 1418 — the 100000 population (n=232).
* `Research/BatmobileGrab/DAMAGE_RULES.md` lines 152 (ImpactMinDamageSpeed), 151 (ImpactMaxDamageSpeed), 153 (ImpactStrafeMod), 147 (ImpactBoostMod) — archetype band values; `CLASS_DEFAULTS.md` lines 257 (ImpactMinDamageSpeed), 256 (ImpactMaxDamageSpeed), 258 (ImpactStrafeMod), 260 (ImpactBoostMod) — class defaults.
* `tmp/freebuff/reports/ram-assist-closest-system-plan.md` §1-§4, §7;
  `tmp/freebuff/reports/audit-ram-assist-plan-numbers.md` claims 1-6, C1-C6;
  `tmp/freebuff/reports/carrier-ram-and-dodge.md` §0, §2, §9.
