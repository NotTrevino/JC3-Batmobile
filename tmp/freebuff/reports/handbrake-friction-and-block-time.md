# Handbrake: the force ratio and the block time, checked against the bytes

Scope: rows **T-K3** and **T-K4** of `Working/Translation/T_ROWS.jsonl` (lines 39 and 92), checked
against `Research/BatmobileGrab/CHAIN.json` (the four shipped archetypes) and the class-default record
`T-K3` cites. Every value below carries its source offset. JC3 receivers are named, with the kind each
one is in the data.

Labels: **decoded** = read at the file, offset and line named; **derived** = arithmetic over decoded
values; **UNKNOWN** = absent from the bytes, with what would settle it.

---

## 0. Answer in one line

`EBrakeBrakeForce` **640,000** at offset **4628** is confirmed in all four shipped archetypes against a
class default of **160,000** at the same offset, so the row's **4.0** ratio is exact and unit-free.
The second number is not that clean: `min_time_to_block` has **no BmAK member at all** — the ledger's
**5** has no source, the row's "bytes carry **1**" is the **JC3 donor module's** value (not a BmAK
byte), and the proposed **0.3** is `HandBrakeOffTime` **0.3 s** at offset **960** on
`RVehicleSimBatmobile`, which is a handbrake *release* time, not a block time. JC3's receiver for the
ratio is `brakes.handbrake_friction_factor` — a **friction factor** (dimensionless, fleet 1..10); the
receiver for the time is `brakes.<front|rear>.min_time_to_block` — a **time by name**, float in the
data, unit not stated by any file.

---

## 1. T-K3 — `EBrakeBrakeForce` 640,000 against its class default 160,000

| quantity | value | offset | source | label |
|---|---:|---:|---|---|
| `RVehicleBatmobileBase.EBrakeBrakeForce`, shipped (V2 / MK2 / Joker / Funhouse) | **640000.0** | **4628** (0x1214) | `CHAIN.json:7822`, `:8650`, `:9352`, `:10173` — four archetype streams, identical value | decoded |
| `RVehicleBatmobileBase.EBrakeBrakeForce`, class default | **160000.0** | **4628** | `CLASS_DEFAULTS.md:184` (row 6) and `CLASS_DEFAULTS.md:512`; decoded from `BmGame\RVehicleBatmobileBase.g.cs:5280` | decoded |
| the shipped value re-read a second way | **640000** | `0x1214` | `MECHANICS_NAMES.md:33` ("`0x1214` | 640000 | `EBrakeBrakeForce` | FloatProperty | `RVehicleBatmobileBase`") | decoded (cross-check) |
| the row's proposed ratio | **4.0** | — | 640000 / 160000, exact to the float printed | **derived** |

**Verdict: confirmed.** Both numbers sit at the **same offset 4628**, on the **same class**, in two
independent records (the tag-stream chain and the SDK layout dump), so the division is legitimate: a
class default and an archetype override of one property. 640000 / 160000 = 4.0 exactly, no rounding.

Two related values the row quotes, checked for consistency:

| quantity | value | offset | source | note |
|---|---:|---:|---|---|
| `EbrakeTime`, shipped | **0.75** | **4624** | `CHAIN.json:7815`, `:8643`, `:9345`, `:10166` | decoded |
| `EbrakeTime`, class default | **1.0** | **4624** | `CLASS_DEFAULTS.md:183` | the override ratio is 0.75, not 1.0 — the row's "EbrakeTime 0.75" is the **shipped** number, and it differs from its own default |

**Why the ratio is the right bridge (the row's argument, restated with its evidence):** the JC3 member
it lands on is dimensionless (§3), so any constant scale in Unreal's force units cancels. That is the
whole justification, and it is sound as arithmetic; it says nothing about the *effect* of the number
(§5).

---

## 2. T-K4 — `min_time_to_block`: 5 (ledger) / 1 (row cell) / 0.3 (proposal)

| claim | stated value | what the bytes show | offset | label |
|---|---:|---|---:|---|
| ledger | **5** | **no member named `MinTimeToBlock` or `min_time_to_block` exists anywhere in `BMSDK_OFFSETS.json`** (0 hits for both spellings) and 0 hits in `CHAIN.json`; T-K2 already records the chain as having "no brake-lock member" | — | **UNKNOWN / unsourced** |
| row cell "the bytes carry 1" | **1** | that 1 is the **JC3 donor module's** value — `Brakes.front.min_time_to_block` donor column **1** and `Brakes.rear.min_time_to_block` donor **1** (`VOCABULARY.md:387`, `:391`). It is not a BmAK byte: no such BmAK property exists to carry it | JC3 module member (no class offset); BmAK side: none | **decoded (JC3 donor) / mislabelled as "bytes"** |
| proposal | **0.3** | `HandBrakeOffTime` = **0.3 s**, declared at offset **960** in the `RVehicleSimBatmobile` block (`BMSDK_OFFSETS.json:24667`; the class opens at `:23946`); the value is asserted by T-K2 ("`HandBrakeOffTime` 0.3 s (handbrake release time, `Default__RVehicleSimBatmobile`)") | **960** | **decoded declaration / value not in any class-default record** |
| proposal, donor-side check | **1** → **0.3** | the donor's value is 1, so the proposal is a **0.3× change** to a member whose unit is unstated (1 s → 0.3 s if seconds) | — | **derived** |

**Verdict: half-confirmed.** The 5 is unsourced and should be dropped. The 1 is real but belongs to
the JC3 donor, not to "the bytes" of the Batmobile. The 0.3 is a real decoded *declaration* with a
cited value, but it is `HandBrakeOffTime` — the time the handbrake **takes to release** — not a
"minimum time to block". Mapping one onto the other is an **INFERRED kind-match**, which is how T-K4
itself labels it.

### 2.1 The one gap in the 0.3

`HandBrakeOffTime` appears in `CLASS_DEFAULTS.md` **nowhere** (0 hits for the member; no row at offset
960), even though that file decodes `Default__RVehicleBatmobileBase` and `Default__RVehicleSimBatmobile`,
which is the object T-K2 names as the value's owner. So the 0.3 currently rests on **one sentence in
T-K2**, not on a class-default row a build step can cite. That is a record gap, not a contradiction:
the declaration and its offset are decoded, the value's provenance is single-source.

---

## 3. The JC3 receivers, and what kind each one is

| receiver | member | type | fleet range | donor | kind in the data |
|---|---|---|---:|---:|---|
| T-K3 ratio 4.0 | `brakes.handbrake_friction_factor` | float | **1 .. 10** (med 2, n=271) | **2** | **friction factor** — dimensionless multiplier; no force and no time anywhere in its row (`VOCABULARY.md:388`; `DRIVE_CARRIERS.md:269` gives the player-copy 1 and 1..10) |
| T-K4 time 0.3 | `brakes.front.min_time_to_block` | float | **−1 .. 20** (med −1, n=271) | **1** | **time by name** — the data gives type `float` and a −1 sentinel but **states no unit**; the row is `VOCABULARY.md:387` |
| T-K4 time 0.3 | `brakes.rear.min_time_to_block` | float | **−1 .. 20** (med −1, n=271) | **1** | same (`VOCABULARY.md:391`) |

Answers to the question as asked:

* **`handbrake_friction_factor` is a friction factor.** Fleet 1..10, median 2, donor 2; the AI twin
  ships 2 against the player's 1 (`DRIVE_CARRIERS.md:283`). A force **ratio** is the correct kind to
  write into it — the ratio is unit-free and the member is dimensionless, which is exactly the bridge
  T-K3 claims.
* **`min_time_to_block` is a time in the member's name and a float in the data.** No file states the
  unit (seconds vs ticks), and the fleet's median **−1** reads as an "unused" sentinel, so the range
  includes a non-time state. Writing 0.3 into it assumes seconds.
* Nothing here is a force on the JC3 side: JC3's brake force lives in `brakes.<axle>.max_brake_torque`
  (250 .. 1e7, donor 14000), which is a torque, and T-K1 already disproved the direct BmAK force →
  JC3 torque bridge. So the ratio has no force receiver — only the friction factor.

---

## 4. The two numbers side by side

| | T-K3 | T-K4 |
|---|---|---|
| BmAK value | `EBrakeBrakeForce` 640000 | none (`min_time_to_block` does not exist) |
| BmAK offset | **4628** | — |
| class default | 160000 at **4628** | — |
| proposed build number | **4.0** | **0.3** |
| JC3 receiver | `brakes.handbrake_friction_factor` | `brakes.front/rear.min_time_to_block` |
| kind match | factor → factor (**exact kind**) | release time → block time (**INFERRED kind**) |
| inside the shipped domain? | 4.0 is inside **1..10** but above the 6 t band **1..2.25** (T-K3's own note) | 0.3 is inside **−1..20**, so domain-legal |
| confidence | **decoded + derived, exact** | **decoded donor + INFERRED time** |

---

## 5. Unsettled — only what the bytes could not settle

**T-K3 (force ratio 4.0).**

1. **Whether `handbrake_friction_factor` is linear in braking force.** No consumer is decoded: the
   member is a module value and the arithmetic is native. A 4.0 factor need not produce 4× the
   deceleration; only a stop-distance measurement settles it (the row's own T-B test).
2. **The unit of `EBrakeBrakeForce`.** 640000 is a force in Unreal units, but nothing in the files
   names the unit, so no absolute value can be carried — only the ratio. That is why the row proposes
   a ratio, and the limit stands.
3. **Whether 4.0 is too far out of band.** The fleet's 6-tonne chassis run 1..2.25 while the whole
   fleet allows 1..10; 4.0 is legal data but evidence-free at that weight. Only the test says whether
   the rear axle locks or just slows.

**T-K4 (time 0.3).**

1. **What `min_time_to_block` means.** "Minimum time to block" has no decoded definition — whether it
   is the time before the wheel may lock, a debounce on the block state, or a per-step minimum, is not
   in any file. Mapping a *release* time onto it is a name-level match, not a semantic one.
2. **Its unit.** The record gives type `float`, range −1..20 and median −1; no file states seconds.
   0.3 interpreted as ticks or as a normalised value would mean something else.
3. **The provenance of the 0.3 itself.** `HandBrakeOffTime` has a decoded declaration at offset 960 but
   **no class-default row** in `CLASS_DEFAULTS.md`; its value is single-sourced from T-K2's sentence.
   A `--check` re-read of that offset in `Default__RVehicleSimBatmobile` would close it.
4. **Where the ledger's 5 came from.** No BmAK member, no chain hit, no module member with 5 on this
   chassis; the number cannot be traced to any file read here, so it can only be dropped, not
   explained.

---

## 6. Sources, limits, revert

**Sources.** `Working/Translation/T_ROWS.jsonl:39` (T-K3), `:92` (T-K4), T-K2 row (same file);
`Research/BatmobileGrab/CHAIN.json:7815/7822` (+ the other three archetype copies at 8643/8650,
9345/9352, 10166/10173); `Research/BatmobileGrab/CLASS_DEFAULTS.md:183-184`, `:512`;
`Research/BatmobileGrab/MECHANICS_NAMES.md:32-33`; `Research/BatmobileGrab/BMSDK_OFFSETS.json:24667`
(offset 960, `RVehicleSimBatmobile` block opening at `:23946`) and the absence of any
`MinTimeToBlock`/`min_time_to_block` member; `Research/JC3Grab/VOCABULARY.md:385-391`;
`Research/JC3Grab/DRIVE_CARRIERS.md:267-283`.

**Limits.** Desk check only: no module was re-decoded, no game opened, no build run. The JC3 fleet
ranges and donor values are quoted from the generated records, not re-measured. Nothing here claims a
behaviour, only what each number is and which member receives it.

**Revert.** Delete this file and its copy under `tmp/freebuff/reports/`. No other file was created,
edited or moved; the two ledger rows, `CHAIN.json`, `CLASS_DEFAULTS.md` and the JC3 records were read
only.
