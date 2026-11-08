# Rotor-collision gate on a car: what `min_rpm` reads, and whether the block can open

Row: **T-RA1** (`Working/Translation/T_ROWS.jsonl:103`), blocked on one question — can the rotor-RPM
collision block open on a car? Source of the block and its offsets:
`tmp/freebuff/reports/ram-assist-closest-system-plan.md` §2.1–§2.2. That plan's 1260-RPM derivation is
**not repeated here**; this note only asks what the gate's input is and whether a car can satisfy it.

Labels: **decoded** = member/value/offset read at the named file; **derived** = a stated rule over
decoded inputs; **UNKNOWN** = absent, with the consumer file named.

---

## 0. Verdict

**UNKNOWN** — not because the numbers are missing, but because the block names no input.

`RotorCollision` is **four floats and nothing else** (`min_rpm` 0x130 = 30, `mass_ratio_when_no_mass`
0x134 = 0.1, `damage_to_other_per_second` 0x138 = 100000, `light_object_mass_ratio` 0x13C = 0.02 —
plan §2.1, fleet-wide identical on 232 builds, `VOCABULARY.md:1415-1418`). No member in the block, and
no member elsewhere in `VehicleCommon`, carries or points at an RPM **source**. So the data settles
the threshold and not the quantity compared against it.

Two conditional outcomes, both fully decoded except the one link:

| if `min_rpm` reads | value on a car | gate opens? | why |
|---|---|---|---|
| **engine RPM** | idle 800 … 4500 (`LandEngine.min_rpm`/`max_rpm`, `VOCABULARY.md:55`; plan §2.3 inputs) | **YES** — 800 ≥ 30 at idle, always | the car's engine RPM starts four times above the 30 gate and never drops below it while running |
| **rotor RPM** | **0** — a car ships no `vehicle_parts` module, so it has no rotating part (plan §2.2) | **NO** — 0 < 30 | the gate's own name and its sibling rotating-part table (`all_rotating_part_properties[].rpm_variable` = `main_rotor_rpm` / `tail_rotor_rpm` / `rotor_rpm`, plan §2.2) point at rotor RPM, which a `CCar` never produces |

**Which is more likely, stated as inference and not as decode:** rotor RPM. Three decoded facts push
that way — the block is named for it, its siblings in the same `VehicleCommon` instance are
`helicopter_common` / `plane_common` / `motorbike_common` (aircraft/rotor-specific vocabulary,
`VOCABULARY.md:1398-1427`), and the same file's rotating-part table exposes rotor-flavoured rpm
variables. None of the three is a consumer, so the verdict stays UNKNOWN.

**Settling file:** the native consumer of `damage_to_other_per_second` — the `RotorCollision` tick in
`JustCause3.exe` — or the engine-side class layout behind `RotorCollision`. No decoded exe or
class-layout record for it exists in this project (`jc3adf.py dump` reads the module instance's four
floats and stops there); that is the file a Q-phase probe or an exe decode would have to open.

---

## 1. Where the numbers come from (no re-derivation)

| member | offset | value | source | label |
|---|---:|---:|---|---|
| `rotor_collision.min_rpm` | **0x130** | **30.0** | plan §2.1 read-back; `VOCABULARY.md:1418` (30 on n=232) | decoded |
| `rotor_collision.mass_ratio_when_no_mass` | **0x134** | **0.1** | plan §2.1; `VOCABULARY.md:1417` | decoded |
| `rotor_collision.damage_to_other_per_second` | **0x138** | **100000.0** | plan §2.1; `VOCABULARY.md:1415` | decoded |
| `rotor_collision.light_object_mass_ratio` | **0x13C** | **0.02** | plan §2.1; `VOCABULARY.md:1416` | decoded |
| the whole block | instance-relative 224, 16 B, 4 floats | — | plan §2.1 (`RotorCollision`, hash `0xed54d0d9`, size 16) | decoded |

Read this session to confirm the shape, not to re-derive the plan: the member list is exactly those
four floats — **no fifth member, no reference to an rpm variable, no state flag**. That absence is the
report's central fact.

### 1.1 The BmAK object list adds nothing to the gate

`Research/BatmobileGrab/objects.jsonl` was scanned in full (20,128 exports): exactly **one** object
whose name, outer or class contains `rotor` — line **6164**, `Helicopter.Blades` /
`Helicopter_Police_Rotor_S_MAT`, class `Material`, 528 B. There is **no** `RotorCollision` object and
no rotor-RPM member anywhere in BmAK's object list.

**Derived:** the gate is not a BmAK construct and BmAK cannot supply its input. BmAK has no
`rotor_collision` block to compare against, so nothing on that side can be used to infer which RPM the
JC3 consumer reads. (`rotor_collision` appears only in JC3's module vocabulary.)

---

## 2. Can the car's engine RPM reach the gate?

**Yes, trivially — if the gate reads engine RPM.** Decoded engine band: `min_rpm` 800, `optimal_rpm`
2800, `max_rpm` 4500 (`land_engine`, plan §2.3 input table; `VOCABULARY.md:55`). The gate is 30, i.e.
**26.7× below idle**. A running car's engine RPM is always ≥ 800, so a 30 threshold would be satisfied
at every instant, at any speed, including stationary. A 1260 threshold (the plan's 20 km/h figure)
would be satisfied above ~20 km/h in first gear.

**And no, if it reads rotor RPM** — 0 at all times on a `CCar`, since a car's private module set has
no `vehicle_parts` at all (plan §2.2; its set is brakes, custom_land_global, land_aerodynamics,
land_audio, land_engine, land_global, land_steering, palette, rigid_body, suspension, transmission,
vehicle_misc). **Derived:** with `min_rpm` 0 the gate is `0 ≥ 0` and passes (which is why the plan's
stage A ships 0); at the shipped **30** it is `0 ≥ 30` and fails, so under the rotor hypothesis the
block **cannot open on a car at any speed**, and no `min_rpm` value above 0 could change that.

---

## 3. Does the no-mass fallback apply to a car?

`mass_ratio_when_no_mass` = **0.1** at 0x134 is a **scale on the rate for the other body**, not a gate
on the actor. Two decoded facts fix its role:

* it sits beside `light_object_mass_ratio` 0.02, i.e. a pair of target-mass scales
  (`VOCABULARY.md:1416-1417`), and the plan's own table labels it "scale when the other object has no
  mass" (§2.1 `role` column);
* its value is identical on **232/232** builds, so it is not a per-vehicle setting.

**Derived:** the fallback keys on the **target**, so:

| contact | fallback applies? | why |
|---|---|---|
| Batmobile vs a **static / scenery / character** (no vehicle mass) | **YES** — 200/s on the plan's 2000 rate | the other body has no mass |
| Batmobile vs **another vehicle** | **NO** — full rate (2000/s) | the other body has mass |
| Batmobile **as the target** of someone else's rotor block | **NO** — the car has `CCar.health` 100 and real mass (plan §2.4) | the fallback is about the other body |

So the 0.1 value is not a reason the block fails on a car; it is the scale the block uses when a car
rams something massless. It applies **independently of which RPM the gate reads**.

---

## 4. What would flip UNKNOWN to YES or NO

| step | what it shows | cost |
|---|---|---|
| the plan's stage A (`min_rpm` 0, rate 2000) in game | whether the consumer runs for a `CCar` **at all** — a negative result kills the channel regardless of input | one build + one ram |
| then stage B (`min_rpm` 1260) at 80 km/h | H1 vs H2: damage at 80 km/h ⇒ engine RPM (YES); none ⇒ rotor RPM (NO) | one build + two rams |
| exe decode of the `RotorCollision` consumer | the input directly, no probe | an exe-side decode that does not exist yet |

The static route is exhausted: four floats, no source member, no BmAK counterpart, and no decoded
consumer. Anything further is either the two-build probe or the exe.

---

## 5. Sources, limits, revert

**Sources (read only):** `tmp/freebuff/reports/ram-assist-closest-system-plan.md` §0–§3 (offsets,
values, the car module set, the rotating-part sibling evidence); `Research/JC3Grab/VOCABULARY.md:55`,
`:1398-1427`, `:1415-1418`; `Research/BatmobileGrab/objects.jsonl` (full 20,128-object scan, one
`rotor` hit at line 6164); `Research/JC3Grab/MOVING_PARTS.md:181-187` (the rotating-part member list).

**Limits.** Desk decode only; no game opened, no build run, no module re-decoded. The verdict reads
the member list and the plan's read-backs, not a live consumer. "Rotor RPM is more likely" is an
inference from names and neighbours, labelled as such.

**Revert.** Delete this file and its copy under `tmp/freebuff/reports/`. No other file was created,
edited or moved; the plan, the vocabulary record and `objects.jsonl` were read only.
