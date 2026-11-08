# Keep-audit: T-MD3, T-MD4, T-MD10, T-MD11

Scope: four rows of the modes translation only. For each row: what BmAK intends
(`Research/BatmobileGrab`), what the JC3 side can carry (`Research/JC3Grab` and the build's own
module/tune files), a verdict of **LORE-EXACT** or **COMPROMISE**, and — for every compromise —
the exact number that differs. Last section: which of the four turn on the mode-switch question.

Inputs read (no new decode, no game launch):

| source | what it supplies |
|---|---|
| `Working/Translation/T11_MODES.md:47-55, 86-90` | the row definitions and the BmAK cell of each |
| `Research/BatmobileGrab/CLASS_DEFAULTS.md:205, 206, 242, 260` | `CrushDamageType`, `RamDamageType`, `ArmourModeDamageReduction`, `ImpactBoostMod` |
| `Research/JC3Grab/DAMAGE_MODEL.md:30-70` | the health module's three vehicles, field by field |
| `Working/Translation/T10_DAMAGE.md:138-168` | `impact_damage_factor` and the declared-switch ranges |
| `Working/Translation/BOOST_COVERAGE.md` §2-3 | the boost curve range and the nitro collapse |
| `Working/Camera/CAM_TUNE.json` | the written `.ctune` FOV readbacks (55 / 63) |
| `Working/Translation/LEDGER_G3C.md:818-882` | the per-row G3C verdicts, including the two disagreements |
| `Working/Translation/LEDGER_G3E.md:296-301` | `T-MD10` = **wrong value**, `T-MD11` = open |
| `Working/Translation/LEDGER_AUDIT.md:235-243` | build state: all four rows **NOT TRANSLATED** in the aaf |

Verdict rules used here:

* **LORE-EXACT** — every BmAK number the row names is present in the build at the same value, or
  BmAK carries no number for that behaviour and the build's switch reproduces the observable.
* **COMPROMISE** — a BmAK number exists and the build holds a different one. The compromise
  number is stated as `BmAK value -> build value`, never as a range.

Build state first, because it constrains every verdict: `LEDGER_AUDIT.md` reports all four rows as
**NOT TRANSLATED** in the aaf — `T-MD3` and `T-MD4` "no member/value/token match"; `T-MD10` and
`T-MD11` likewise, both `dispo=keep`. So each verdict below reads "does the *live build* hold the
BmAK number", not "did a translation pass exist".

---

## Row 1 — `T-MD3` ram immunity

**BmAK intent** (`T11_MODES.md:47`): ramming never damages the Batmobile (G1-14 damage rules).
The decoded support is a pair of damage *classes*, not a magnitude:

| BmAK member | value | evidence |
|---|---|---|
| `RamDamageType` (`RVehicleBatmobileBase`, ClassProperty) | `RDmgType_Barge` | `CLASS_DEFAULTS.md:206` (off 5676) |
| `CrushDamageType` (`RVehicleBatmobileBase`, ClassProperty) | `Core.DmgType_Crushed` | `CLASS_DEFAULTS.md:205` (off 5668) |

There is **no numeric ram-immunity field**: BmAK names the damage type the car deals, and the
engine decides what that does. The only numeric impact member on the class is `ImpactBoostMod`
**1.5** (`CLASS_DEFAULTS.md:260`), and that one is the outgoing boost multiplier, not a reduction —
`BOOST_COVERAGE.md` §3 maps it to `T-DM7`, which is `out`.

**JC3 carrier** (`T11_MODES.md:47`, `T-DM8`): `vehicledamage.impact_damage_factor` in
`lave_health_medium.vmodc`. Fleet value 1.0; declared switch range **1..12**, with **0** as the off
switch (`T10_DAMAGE.md:144`, `:64`).

**Build** (`DAMAGE_MODEL.md` §2, `Builds/test-091` vs the medium tank):

| field | applied | donor | medium tank |
|---|---:|---:|---:|
| `impact_damage_factor` | **0** | 1 | 1 |
| `impact_armor` @ `impact_armor_strength` | **5000 @ 100** | 0 @ 0 | 0 @ 0 |
| `melee_armor` @ `melee_armor_strength` | **5000 @ 100** | 0 @ 0 | 0 @ 0 |
| `deform_scale` | **0** | 1 | 1 |
| `max_health` | 2000 | 700 | 2000 |

**Verdict: LORE-EXACT.** Zero compromises. The observable BmAK asserts — ram a wall, ram a car,
take no damage — is produced by three fields at once: `impact_damage_factor` 0 (the collision
multiplier off), `impact_armor` 5000 @ 100 and `melee_armor` 5000 @ 100 (both channels at the fleet
ceiling), with `deform_scale` 0 so nothing crumples either. There is no BmAK number to miss,
because BmAK encodes a *damage class* rather than a factor.

Two things this verdict does **not** claim:

1. The `0` is a JC3 off switch, not a translated BmAK value — `POSTMORTEM_DAMAGE.md:66` puts
   1..12 as the fleet domain and calls 0 "outside — off switch". The match is behavioural.
2. The **outgoing** half of BmAK's barge behaviour (`RDmgType_Barge`, and `ImpactBoostMod` 1.5) is
   not in this row and has no JC3 member (`T-DM7` = `out`, `T10_DAMAGE.md:162`). Ramming does not
   scratch the Batmobile; ramming is also not modelled as the Batmobile hurting the other car.

**Mode switch: not applicable.** `T-MD3` is MOD-1, `carried` in `BUILD_BATCHES.md` (ARM-3 /
MOD-1): BmAK's ram immunity is mode-independent, so the hybrid needs no switch to hold it.

---

## Row 2 — `T-MD4` high-speed torque curves

**BmAK intent** (`T11_MODES.md:50`): two curves on `RVehicleSimBatmobile`, identical in all four
packages. `x` is cm/s by the UE3 convention; `y` is raw (no documented scale, carried raw).

| `StandardTorqueVSpeedCurve` (6 pts) | | `BoostTorqueVSpeedCurve` (7 pts) | |
|---|---:|---|---:|
| -1500 cm/s (-54 km/h) | 0 | -1500 cm/s | 0 |
| -300 cm/s (-10.8 km/h) | 200 | -300 cm/s | 200 |
| 0 | **200** (peak) | 0 | **260** (peak) |
| 750 cm/s (27 km/h) | 170 | 1500 cm/s (54 km/h) | 260 |
| 1600 cm/s (57.6 km/h) | 150 | 2100 cm/s (75.6 km/h) | 220 |
| 2100 cm/s (75.6 km/h) | **105** (floor) | 2800 cm/s (100.8 km/h) | 200 |
| | | 3000 cm/s (108 km/h) | 150 |

Derived ratios used below (rule stated: each point divided by that curve's own peak):
standard = 1.00 at 0, 0.85 at 750 cm/s, 0.75 at 1600 cm/s, 0.525 at 2100 cm/s; boost/standard at
the same speed = 1.00 at -300, 1.30 at 0, 1.53 at 750, 1.73 at 1500, 2.10 at 2100, 1.90 at 2800.

**Provenance caveat first.** `LEDGER_G3C.md:832-836` records that the class-default
`SimulationModel` carries every curve slot as `None` and that **neither curve name exists in either
class-default stream** — so these numbers are archetype values from G1's `objects.jsonl`, single
source, and `T-MD4` is `open` in `LEDGER_G3E.md`. Nothing here re-decodes them.

**JC3 carrier** (`T11_MODES.md:50`): there is **no torque-vs-speed curve in the fleet**. The engine
curve is torque-vs-**rpm**, two points: `min_rpm/optimal_rpm/max_rpm` **800 / 2800 / 4500** (T-E1,
read back from `…_land_engine.vmodc`) and `torque_factor_at_min_rpm/at_max_rpm` **1.0 / 0.65**
(T-E3, read back 1.0 / 0.6499999762). The boost half is the arcade block, not a curve:
`arcade.nitro_boost.torque_multiplier` **2.0** (T-B1, donor x2).

**Verdict: COMPROMISE.** Both halves lose the speed axis; the exact numbers that differ:

| what | BmAK | build | delta |
|---|---:|---:|---|
| boost torque over its band | **1.30 .. 2.10** (curve) | **2.0** (constant) | +0.70 at 0 cm/s, **-0.10 at 2100 cm/s** |
| standard torque at the top end | **0.525** (normalized, 75.6 km/h) | **0.65** (at 4500 rpm) | **+0.125** held by JC3 |
| speed at which the curve ends | 2100 cm/s standard / 3000 cm/s boost | no speed term in the engine model | carried instead as `extra_top_speed` **43.2 km/h** (T-B2) |
| reverse side | 0 at -1500 cm/s, rising to 200 at -300 cm/s | no negative-speed torque member | not carried |

The one number to quote as *the* compromise is the boost collapse: **2.10 -> 2.0**, and at the
bottom of the band **1.30 -> 2.0**. `BOOST_COVERAGE.md` §3 already states it as "collapsed to one
constant 2.0 (the curve is 1.30x..2.10x over its speed band)", and `T-B1` is the row that does it.
The second is the standard curve's floor: **0.525 -> 0.65**, i.e. the build keeps 12.5 percentage
points more torque at the top than the standard curve asks for. Both are consequences of the same
missing axis, not of a wrong value: JC3 has no member that scales torque by road speed.

**Mode switch: no.** `T-MD4` is MOD-1 (`carried`, `BUILD_BATCHES.md` MOD-1): the standard curve is
the base profile and the boost curve is the afterburner, which is a button (`pBatmobileBoost`
PAD_Y / PC_LMB, `BOOST_COVERAGE.md` §1) rather than pursuit-vs-battle. Neither curve is battle-only,
which is exactly why `T-MD5` (3-point `BattleModeVSpeedCurve`) exists as a separate omitted row.

---

## Row 3 — `T-MD10` armour reduction

**BmAK intent** (`T11_MODES.md:54`): `ArmourModeDamageReduction`, IntProperty at offset 6424. The
two readings disagree, and this row is the only one of the four that `LEDGER_G3E.md:300` calls
**wrong value**:

| object | value | evidence |
|---|---:|---|
| class default (CDO) | **20** | `CLASS_DEFAULTS.md:242` (`RVehicleBatmobileBase.g.cs:7290`) |
| archetype, Funhouse / MK2 / V2 | **0** | `T11_MODES.md:54`, `:82` |
| archetype, Joker | field absent | `T11_MODES.md:82` ("no tag in Joker") |
| unit | **undocumented** | `T11_MODES.md:86` — "int, undocumented scale (none basis)" |

So "BmAK's intended number" is **20** on the shipped default and **0** on three of four packages.
`LEDGER_G3C.md:874` puts it precisely: "the two readings are of different objects with the same
member name; neither refutes the other". The build followed **0**.

**JC3 carrier**: no mode member at all (`T11_MODES.md:54`). The reduction can only land in the
health module's channels, so the relevant applied state is (`DAMAGE_MODEL.md` §2):
`max_health` **2000**, `bullet_armor` **5000 @ 99**, `impact_armor` **5000 @ 100**,
`melee_armor` **5000 @ 100**, `explosion_armor` **250 @ 50**.

**Verdict: COMPROMISE.** Exact numbers:

| quantity | value | label |
|---|---:|---|
| BmAK class default | **20** | decoded (int, scale unknown) |
| build's value | **0** | decoded, = "no reduction to carry", `T11_MODES.md:54` |
| difference | **20 -> 0** | the compromise number |
| single-profile equivalent if 20 means percent | **2000 / (1 - 0.20) = 2500** effective HP | derived (arithmetic on 2000; percent not decoded) |
| nearest JC3 gate | `bullet_armor_strength` 99, fleet max | decoded (`T10_DAMAGE.md:138`) |

Why this is not LORE-EXACT even though the build matches the three archetypes: the row's job is to
carry the mode's **effect**, and the only nonzero reading of that field is 20 — a mode with no
effect is not a translation of a mode that has one. The build is `keep`/`carried` on the strength of
the 0 reading, which is why G3E rejects the value. And even taking 0 as correct, the row cannot be
called exact without also saying the armour mode is indistinguishable from pursuit mode on the
damage side — which is what the 0 buys.

**Mode switch: yes — this row turns on it.** `ArmourModeDamageReduction` only exists in armour
(battle) mode; the hybrid has one damage profile and no second mode to enter, so the 20 can be
expressed only by inflating the single profile (the 2500 HP arithmetic above) or not at all. Row is
MOD-2.

---

## Row 4 — `T-MD11` battle camera

**BmAK intent** (`T11_MODES.md:55`, `:92-94`): three numbers from `R3rdPersonCamera`, plus a
24-field config:

| BmAK field | value | unit |
|---|---:|---|
| `BattleModeCamFOV` | **60** | deg |
| `BattleModeWinchCamFOV` | **60** | deg |
| `AntiPersonelBattleModeCamFOV` | **40** | deg |
| `BattleModeCamConfig.MinFreeCameraDistance` / `MaxFreeCameraDistance` | **1000 / 1000** | cm |

The config carries 24 named fields; the two distances are read by name. Spring/distance fields have
no unit bridge (`T-CAM9` blocked); the FOV does.

**JC3 carrier**: one per-entity `.ctune`. The written candidate (`Working/Camera/CAM_TUNE.json`) is
`bat_base.ctunec`, and its own banner reads "CAM-1 candidate … **not packed, not installed**":

| member | index | old | new (readback) | row |
|---|---:|---:|---:|---|
| `FOV` | 0 | 30.0 | **55.0** | T-CAM2 |
| `FOV` | 1 | 55.0 | **63.0** | T-CAM2 |
| `CameraPosition` | 1 | 2.0 | 1.30 | T-CAM5 |
| `CameraPosition` | 2 | 5.0 | 7.00 | T-CAM5 |
| `LookAtPoint` | 1 | 1.25 | 1.55 | T-CAM5 |

**Verdict: COMPROMISE.** Exact numbers:

| BmAK number | tune value | delta | carried? |
|---|---:|---:|---|
| battle FOV **60** | band **55 .. 63** | 0 deg of value change, but **not pinned** — 60 is only reached between the two FOV keys | inside band only |
| anti-personnel FOV **40** | band floor **55** | **+15 deg too wide** (40 -> 55) | no |
| winch FOV **60** | no winch camera exists | 0 of 1 carried | no |
| free-camera distance **1000 / 1000 cm** | no unit bridge (T-CAM9) | no value written | no |

The compromise number to quote is **40 -> 55 (+15 deg)**: the narrow anti-personnel framing cannot
be produced by this tune, because nothing in the written camera goes below the 55 floor. Battle FOV
60 is the one that survives — `T11_MODES.md:55` already calls it "inside band" — but it survives as
a point on an interpolated ramp, not as a setting, and the whole file is a candidate that is neither
packed nor installed.

**Mode switch: yes — this row turns on it.** A battle FOV is a second camera state; with one camera
there is no state to switch into, so 60 exists only as a by-product of the speed ramp. Row is MOD-2
(`CAM-2`, `BUILD_BATCHES.md:72`).

---

## Summary

| row | behaviour | verdict | compromise number (BmAK -> build) |
|---|---|---|---|
| `T-MD3` | ram immunity | **LORE-EXACT** | none — BmAK carries a damage class (`RDmgType_Barge`), not a magnitude; build = `impact_damage_factor` 0 + `impact_armor` 5000 @ 100 + `melee_armor` 5000 @ 100 + `deform_scale` 0 |
| `T-MD4` | torque curves vs speed | **COMPROMISE** | boost **1.30..2.10 -> 2.0** (0.10 short at the 2100 cm/s end); standard floor **0.525 -> 0.65** (+0.125) |
| `T-MD10` | armour reduction | **COMPROMISE** | **20 -> 0** (class default vs build; archetypes agree with 0); if 20 is percent, single-profile equivalent **2500** HP (derived) |
| `T-MD11` | battle camera | **COMPROMISE** | anti-personnel FOV **40 -> 55 (+15 deg)**; battle **60** inside the 55..63 band but unpinned; **1000/1000 cm** unset |

Score: **1 LORE-EXACT, 3 COMPROMISE**.

### Which rows turn on the mode-switch question

| row | mode family | turns on the mode switch? | why |
|---|---|---|---|
| `T-MD3` | MOD-1 | **no** | ramming is mode-independent in BmAK; the one switch is always on |
| `T-MD4` | MOD-1 | **no** | standard curve = base profile, boost curve = afterburner button, neither battle-only (the battle-only speed cap is `T-MD5`, omitted) |
| `T-MD10` | MOD-2 | **yes** | `ArmourModeDamageReduction` has no meaning outside armour mode; the 20 is unreachable without a second damage profile |
| `T-MD11` | MOD-2 | **yes** | `BattleModeCamFOV` 60 / anti-personnel 40 are second-camera states; one camera cannot switch |

So exactly **two of the four — `T-MD10` and `T-MD11` — are gated on the mode switch**, and both are
the rows whose BmAK numbers are otherwise reachable without any new member. The other two are
gated on a missing *axis* (speed, in `T-MD4`) or on nothing (`T-MD3`).

### What would settle each

| row | what would close it |
|---|---|
| `T-MD3` | nothing — the behaviour is reproduced; only `T-DM7` (outgoing barge) stays open |
| `T-MD4` | the archetype `SimulationModel` tag decode (G3C's open item); until then the curve is single-source from G1 |
| `T-MD10` | the fourth archetype (Joker lacks the tag) or the four-car archetype set, to say whether 20 or 0 is the intended value |
| `T-MD11` | packing and installing the `.ctune` (it is a candidate), then a battle-framing test at 60 and 40 |

### Limits

No game was launched; no file was decoded for this audit. Every number above is quoted from the
files named in the header table, with the two arithmetic steps (curve normalization to peak,
2000/0.8) marked **derived**. `T-MD4`'s curve values are the one single-source figure in the set
(archetype, not class default) and `T-MD10`'s 20-vs-0 is the one unresolved value conflict.
