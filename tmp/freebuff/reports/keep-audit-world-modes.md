# Keep audit — world and modes rows (merged)

Merge of two partial audits into one report. **No row was re-audited**: every verdict and number
below is copied from `keep-audit-world-modes-wld.md` (six world rows) and
`keep-audit-world-modes-md.md` (four modes rows), and §4 checks each number against the file it
came from.

| partial | rows | verdicts |
|---|---|---|
| `keep-audit-world-modes-wld.md` | T-WLD7, T-WLD13, T-WLD14, T-WLD16, T-WLD18, T-WLD19 | 3 LORE-EXACT · 3 COMPROMISE |
| `keep-audit-world-modes-md.md` | T-MD3, T-MD4, T-MD10, T-MD11 | 1 LORE-EXACT · 3 COMPROMISE |
| **merged** | **10** | **4 LORE-EXACT · 6 COMPROMISE** |

Verdict rules, as used in both partials: **LORE-EXACT** = the build holds BmAK's number, or BmAK
carries no number for that behaviour and the build's switch reproduces the observable;
**COMPROMISE** = a BmAK number exists and the build holds a different one, stated as
`BmAK value -> build value`.

---

## 1. One verdict table, all ten rows

| # | row | family | requirement | verdict | compromise number (BmAK -> build) |
|---|---|---|---:|---|---|
| 1 | `T-WLD7` | world / UI | category captions stay correct | **COMPROMISE** (accepted, no write) | `UITypeDescription` **2432797658** / `UIFlagDescription` **1383769868** (`SPORTS CAR` / `SPORTS CARS`); replacement key **not mintable** — no number to write |
| 2 | `T-WLD13` | world / water | the car sinks | **LORE-EXACT** | none — `will_sink` **1** kept |
| 3 | `T-WLD14` | world / water | stall + entry damage on water | **COMPROMISE** | `car_common.engine_shut_down_delay_s` **30 -> 0** (per-vehicle override; **5** if 0 disables the timer) |
| 4 | `T-WLD16` | world / cargo | plane and boat can carry the car | **COMPROMISE** | plane payload ratio **15.0 % -> 24.0 %** (6,000 / 25,000); gate is `CVehicleCargoBay.enabled` = **1** |
| 5 | `T-WLD18` | world / traffic | no traffic record for the Batmobile | **LORE-EXACT** | none — **0** records at leaf hash **443190071** |
| 6 | `T-WLD19` | world / traffic | donor's own traffic record left alone | **LORE-EXACT** | none — donor record at offset **23240**, **13 tags**, **1 of 41** selectors |
| 7 | `T-MD3` | modes MOD-1 | ram immunity | **LORE-EXACT** | none — BmAK carries a damage *class* (`RDmgType_Barge`), not a magnitude; build = `impact_damage_factor` **0** + `impact_armor` **5000 @ 100** + `melee_armor` **5000 @ 100** + `deform_scale` **0** |
| 8 | `T-MD4` | modes MOD-1 | high-speed torque curves | **COMPROMISE** | boost **1.30..2.10 -> 2.0** (**-0.10** at the 2100 cm/s end); standard floor **0.525 -> 0.65** (**+0.125**) |
| 9 | `T-MD10` | modes MOD-2 | armour reduction | **COMPROMISE** | **20 -> 0** (class default vs build; three archetypes agree with 0); if 20 is percent, single-profile equivalent **2500** HP (derived) |
| 10 | `T-MD11` | modes MOD-2 | battle camera | **COMPROMISE** | anti-personnel FOV **40 -> 55 (+15 deg)**; battle **60** inside the **55..63** band but unpinned; **1000 / 1000 cm** unset |

---

## 2. The six compromises, with their exact numbers

### 2.1 `T-WLD7` — category captions

The donor's `profile/item.onlinec` carries two shared keys, both of which resolve to the caption
*every* JC3 sports car uses:

| field | hash | text | change |
|---|---:|---|---|
| `UITypeDescription` | **2432797658** | `SPORTS CAR` | accepted, no write |
| `UIFlagDescription` | **1383769868** | `SPORTS CARS` | accepted, no write |

BmAK gives the Batmobile a category of one (`ShowcaseItems` page "Batmobiles",
`UpgradeHeaders` "PageBatmobile", `CharacterIds Id=100`), so "SPORTS CAR" is wrong for a 6 t
armoured car — but the caption key's preimage is UNKNOWN and cannot be computed from the visible
string:

```
hash_jenkins("SPORTS CAR")  = 2949097753  ≠ 2432797658
hash_jenkins("SPORTS CARS") = 2711742874  ≠ 1383769868
560 prefix/suffix/case variants                0 hits
```

The two controls (`3535039305` leaf, `2073308658` `_desc`) do verify, so the failure is in the
caption convention, not the hasher. Editing the text at those hashes would relabel every sports car
in the game. **Exact numbers: 2432797658, 1383769868 — replacement value: none computable.**

### 2.2 `T-WLD14` — water stall

BmAK has **0** water-named floats in the class defaults, so its stall timing is UNKNOWN and the row
rests on D-8. The donor's shared module, on 232 of 232 entities with 0 overrides:

| key | value | action |
|---|---:|---|
| `car_common.engine_shut_down_delay_s` | **30** | **30 -> 0** (immediate stall), or **5** if 0 is read as "disable the timer" |
| `vehicle_damage.min_water_entry_ms` | 10 | leave — `_ms` unit UNKNOWN |
| `vehicle_damage.fatal_water_entry_ms` | 20 | leave |
| `vehicle_damage.min_water_entry_floating_ms` | 20 | leave |
| `vehicle_damage.fatal_water_entry_floating_ms` | 50 | leave |

With 30 s the engine dies half a minute after entry, which is neither "on entry" nor "on the first
wave". The one number to change is **30 -> 0**, written as a per-vehicle override in the
Batmobile's own module (R7 forbids editing `vehicle_common.vmodc`; the fleet ships 0 overrides, so
the mechanism is unproven — U4).

### 2.3 `T-WLD16` — cargo capacity

BmAK has an airlift, not a cargo bay: the Batwing Carrier clamps the car vertically
(`Batmobile_Vertical_Rescue_In` 218 frames / 7.233 s, carrier travel 36499.69 cm), with no mass
gate anywhere in the sequence. The donor's 12 `CVehicleCargoBay` objects carry no capacity member,
so the row's percentages are ratios against module mass:

| carrier | mass | ratio | action |
|---|---:|---:|---|
| plane `v4603_plane_urga_cargotransport` (heavy body) | 40,000 | 15.0 % | replaced by the other body's reading |
| plane, same entity (light body) | **25,000** | **24.0 %** | **15.0 % -> 24.0 %** (6,000 / 25,000) |
| boat `v1602_boat_urga_transport` | 100,000 | 6.0 % | arithmetic-correct, stays |
| flatbed `v5602_train_urga_monorailflatbed` | 15,000 | 40.0 % | arithmetic-correct, stays |

The deciding gate is not a number: `CVehicleCargoBay.enabled` = **1** on all 12 bays, and the
attach rule for a cloned bay is UNKNOWN (all 12 ship empty `enable`/`disable` events).

### 2.4 `T-MD4` — torque curves

BmAK's two curves, identical in all four packages, `x` cm/s and `y` raw:

* `StandardTorqueVSpeedCurve`: -1500→0, -300→200, 0→**200**, 750→170, 1600→150, 2100→**105**
* `BoostTorqueVSpeedCurve`: -1500→0, -300→200, 0→**260**, 1500→260, 2100→220, 2800→200, 3000→150

JC3 has no torque-vs-speed member at all — only torque-vs-rpm (`800 / 2800 / 4500` rpm,
`1.0 / 0.65`) plus the nitro block. The exact numbers that differ:

| what | BmAK | build | delta |
|---|---:|---:|---|
| boost torque across its band | **1.30 .. 2.10** | **2.0** (`nitro_boost.torque_multiplier`) | **+0.70** at 0 cm/s, **-0.10** at 2100 cm/s |
| standard torque at the top end | **0.525** (105/200, at 75.6 km/h) | **0.65** (at 4500 rpm) | **+0.125** held by JC3 |
| speed axis | 2100 cm/s standard / 3000 cm/s boost | no speed term | carried as `extra_top_speed` **43.2 km/h** |

Quote the boost collapse as **2.10 -> 2.0** (`BOOST_COVERAGE.md` §3: "collapsed to one constant
2.0, the curve is 1.30x..2.10x over its speed band") and the standard floor as **0.525 -> 0.65**.
Provenance: archetype values from G1's `objects.jsonl`, single source — neither curve name exists
in either class-default stream (`LEDGER_G3C.md:832-836`).

### 2.5 `T-MD10` — armour reduction

| quantity | value | label |
|---|---:|---|
| BmAK class default | **20** | decoded int, scale undocumented |
| BmAK archetypes (Funhouse / MK2 / V2) | **0** | decoded; Joker has no tag |
| build | **0** | no reduction carried |
| difference | **20 -> 0** | the compromise number |
| single-profile equivalent if 20 is percent | **2000 / (1 - 0.20) = 2500** HP | derived |
| nearest JC3 gate | `bullet_armor_strength` **99** | fleet max |

`LEDGER_G3E.md:300` calls this row **wrong value**. A mode with no effect is not a translation of a
mode that has one, which is why 0 is not accepted as exact even though three archetypes print it.

### 2.6 `T-MD11` — battle camera

| BmAK number | tune value | delta | carried? |
|---|---:|---:|---|
| battle FOV **60** | band **55 .. 63** (`FOV[0]` 55.0, `FOV[1]` 63.0) | 0 deg of value change, unpinned | inside band only |
| anti-personnel FOV **40** | floor **55** | **+15 deg too wide** | no |
| winch FOV **60** | no winch camera | 0 of 1 | no |
| free-camera distance **1000 / 1000 cm** | no unit bridge (T-CAM9) | no value written | no |

The compromise number is **40 -> 55 (+15 deg)**. The `.ctune` holding the 55/63 band is itself a
candidate — `CAM_TUNE.json`'s banner reads "not packed, not installed".

---

## 3. Rows that depend on the mode-switch question

| row | mode family | depends on the mode switch? | why |
|---|---|---|---|
| `T-MD10` | MOD-2 | **yes** | `ArmourModeDamageReduction` has no meaning outside armour mode; the 20 is unreachable without a second damage profile |
| `T-MD11` | MOD-2 | **yes** | battle 60 / anti-personnel 40 are second-camera states; one camera cannot switch |
| `T-MD3` | MOD-1 | no | ramming is mode-independent; the switch is always on |
| `T-MD4` | MOD-1 | no | standard curve = base profile, boost curve = afterburner button; the battle-only cap is `T-MD5`, a separate omitted row |
| `T-WLD7` | world | no | caption hash; gated on the hash-preimage convention (U1), not on a mode |
| `T-WLD13` | world | no | water; rests on D-8, BmAK silent (U2) |
| `T-WLD14` | world | no | water; gated on the shared-module override (U4) |
| `T-WLD16` | world | no | cargo; gated on `CVehicleCargoBay.enabled` and an UNKNOWN attach rule (U5) |
| `T-WLD18` | world | no | traffic; gated on the leaf hash **443190071** |
| `T-WLD19` | world | no | traffic; gated on leaving offset **23240** untouched |

**Exactly two of the ten — `T-MD10` and `T-MD11` — turn on the mode switch.** They are both MOD-2,
both already COMPROMISE, and both would stay COMPROMISE forever if the hybrid never gains a second
mode: no JC3 value change closes either one, only a second state. The other eight are gated on a
missing axis (`T-MD4`), a missing convention or mechanism (`T-WLD7`, `T-WLD14`, `T-WLD16`), a
hashed absence that is already correct (`T-WLD18`, `T-WLD19`), lore that BmAK cannot confirm
(`T-WLD13`), or nothing at all (`T-MD3`).

---

## 4. Cross-check: every table number against its source report

Checked by string match against the two partials, plus the arithmetic each one states.

| number in this report | source | present in source | arithmetic |
|---|---|---|---|
| `2432797658`, `1383769868` | wld §T-WLD7 | yes, both | — |
| `2949097753`, `2711742874` (controls) | wld §T-WLD7 | yes, both | — |
| `will_sink` **1**, `Buoyancy` **2.0** | wld §T-WLD13 | yes | — |
| `engine_shut_down_delay_s` **30 -> 0**, alt **5** | wld §T-WLD14 | yes | — |
| water pair **10 / 20 / 20 / 50** | wld §T-WLD14 | yes | — |
| plane **15.0 % -> 24.0 %**, bodies **25,000 / 40,000** | wld §T-WLD16 | yes | 6000/25000 = 0.2400; 6000/40000 = 0.1500 |
| boat **6.0 %**, flatbed **40.0 %** | wld §T-WLD16 | yes | 6000/100000 = 0.0600; 6000/15000 = 0.4000 |
| `CVehicleCargoBay.enabled` **1**, **12** bays | wld §T-WLD16 | yes | — |
| hash **443190071**, **0** records | wld §T-WLD18 | yes | — |
| offset **23240**, **13 tags**, **1 of 41** | wld §T-WLD19 | yes | — |
| `impact_damage_factor` **0**, **5000 @ 100** ×2, `deform_scale` **0** | md §Row 1 | yes | — |
| boost **1.30 .. 2.10 -> 2.0**, **-0.10 / +0.70** | md §Row 2 | yes | 260/200 = 1.30; 220/105 = 2.095 ≈ 2.10; 2.10-2.0 = 0.10; 2.0-1.30 = 0.70 |
| standard **0.525 -> 0.65**, **+0.125** | md §Row 2 | yes | 105/200 = 0.525; 0.65-0.525 = 0.125 |
| `extra_top_speed` **43.2 km/h** | md §Row 2 | yes | — |
| armour **20 -> 0**, equivalent **2500** HP, gate **99** | md §Row 3 | yes | 2000/0.8 = 2500 |
| FOV **60** / **40** / band **55 .. 63** / **+15 deg** | md §Row 4 | yes | 55-40 = 15 |
| free-camera distance **1000 / 1000 cm** | md §Row 4 | yes | — |

No number was changed, rounded or re-derived during the merge. The two figures marked **derived**
in their source (2500 HP, and the 0.525 normalization) stay marked derived here.

---

## 5. Totals, and what stays open

| outcome | count | rows |
|---|---:|---|
| LORE-EXACT | **4** | `T-WLD13`, `T-WLD18`, `T-WLD19`, `T-MD3` |
| COMPROMISE | **6** | `T-WLD7`, `T-WLD14`, `T-WLD16`, `T-MD4`, `T-MD10`, `T-MD11` |
| depends on the mode switch | **2** | `T-MD10`, `T-MD11` |

| row | what would close it |
|---|---|
| `T-WLD7` | the caption-hash convention (U1); then mint "BATMOBILE"/"BATMOBILES" in 11 languages |
| `T-WLD13` | nothing to change; BmAK's sink behaviour stays UNKNOWN (U2) |
| `T-WLD14` | a proven per-vehicle override (U4) + the `_ms` unit measured (U7) |
| `T-WLD16` | the cargo-bay attach rule (U5); the ratio itself is decided (24.0 %) |
| `T-WLD18` / `T-WLD19` | nothing — both are absences that are already correct |
| `T-MD3` | nothing; only `T-DM7` (outgoing barge) stays open |
| `T-MD4` | the archetype `SimulationModel` tag decode |
| `T-MD10` | the fourth archetype (Joker lacks the tag), or the mode switch |
| `T-MD11` | pack/install the `.ctune`, then a battle-framing test at 60 and 40 |

Limits, carried over unchanged: no game was launched and no file was decoded for either partial or
for this merge. Every number traces to the files named inside the two partials; `T-MD4`'s curve is
the one single-source figure (archetype, not class default) and `T-MD10`'s 20-vs-0 is the one
unresolved value conflict. Merging changed nothing in game data.
