# Collision impact and mode switch — plans v2 (corrections, and what survives "no crash damage")

Supersedes the contested rows of `tmp/freebuff/reports/collision-impact-effects-plan.md` (C) and
`tmp/freebuff/reports/mode-switch-carriers.md` (M). Audit: `tmp/freebuff/reports/audit-collision-impact-and-mode-switch-plans.md` (A).
Neither v1 report was edited. This file is the only write.

**The operator's observation is the test every row must pass:** a crash does **not** damage, scratch
or dent the BmAK car. I read it as three separable claims and test each row against them — no damage
(health), no scratch (scrape/paint), no dent (mesh deformation).

**Reconciliation in one paragraph.** The observation does not contradict the impact rows; it *selects*
which of them are usable. `DAMAGE_RULES.md:136` heads the ram field family **"outgoing"** and `:139`
says "every one of them is an *outgoing* multiplier" — so every `Impact*` / `BattleModeImpact*` value
governs what the car does **to the thing it hits**, and none of them can make the car take damage.
The incoming side is a separate function, `TakesDamageFromRam(Target, RamSpeed)`, which is **script and
returns `true` unconditionally** (`:192`, `:194-196`, `:202`): the entry point exists and is open, and
"no archetype value can switch it off from here". So BmAK's own data has **no immunity switch** — the
observation is an engine-side fact, not a decoded value. In JC3 the equivalent switches **do** exist as
data and the build already carries them: `impact_damage_factor` **0**, `deform_scale` **0**,
`impact_armor` **5000 @ 100** (`Research/JC3Grab/DAMAGE_MODEL.md:50,53`). That is the whole
reconciliation: **outgoing numbers stay, incoming immunity is JC3 data (`impact_damage_factor` 0,
`deform_scale` 0), and anything that would play the car's own destruction cue on contact is dropped.**

Labels: **decoded** = read in the cited file at the cited line; **derived** = arithmetic/set logic over
decoded values; **UNKNOWN** = searched and absent, with the file that would settle it.

---

## 0. Change record (required by `AGENTS.md`)

- **Intended change:** no game data is modified. This document corrects planning rows and adds
  verdicts; it is a plan only.
- **File:** `tmp/freebuff/reports/collision-impact-and-mode-switch-plans-v2.md` — the brief names it,
  and every related artefact already lives in `tmp/freebuff/reports/`.
- **Why this file is correct:** it is the only place the v1 collision and mode-switch rows are
  restated with their corrected sources; editing v1 in place would destroy the audit trail the audit
  relies on.
- **Revert:** delete this file. Nothing else was written or edited.

---

## 1. The one finding the audit could not see: the whole "base CDO" column is decoded

The audit called the base-CDO cells of C §4.1 **UNSUPPORTED** (A rows C12, C15, C16) because
`DAMAGE_RULES.md` §3.3 has only two columns. Correct — but the values are not missing, they are in the
class-default census, one row each:

| field | base CDO | offset / index | line |
|---|---:|---|---:|
| `ImpactMaxDamage` | **100.0** | `0x04d8` / 6856 | row 77 → `Research/BatmobileGrab/CLASS_DEFAULTS.md:255` |
| `ImpactMaxDamageSpeed` | **200.0** | `0x04e0` / 6860 | row 78 → `:256` |
| `ImpactMinDamageSpeed` | **60.0** | `0x04e8` / 6864 | row 79 → `:257` |
| `ImpactStrafeMod` | **1.5** | `0x04f0` / 6868 | row 80 → `:258` |
| `ImpactCivilianVehicleMod` | **1.0** | `0x04f8` / 6872 | row 81 → `:259` |
| `ImpactBoostMod` | **1.5** | `0x0500` / 6876 | row 82 → `:260` |
| `ImpactMaxDamagePow` | **0.666000009** | `0x0508` / 6880 | row 83 → `:261` |
| `StafeImpactImpulse` | **100000.0** | `0x0510` / 6896 | row 84 → `:262` |

Note on numbering: the census prints a **row index** (`| 77 |`) that is not the file line — the rows are
at lines 255-262 (duplicate value-only block at `:562-569`). Cite the line, not the row.

All eight are **decoded**. So the verdict on those cells is **MIS-CITED**, not unsupported: right
numbers, wrong file. That also settles the brief's sharpest mismatch from the other direction — the
0.666 pair really does belong to `BattleModeImpactMaxDamagePow` (`DAMAGE_RULES.md:144`), and
`ImpactMaxDamagePow`'s only shipped value anywhere is the **CDO 0.666000009** at `CLASS_DEFAULTS.md:83`.

---

## 2. Contested collision rows — corrected value, line, verdict

**Row verdicts:** KEEP = usable as planned; KEEP-OUT = usable, but only as damage dealt to the target;
DROP = must not be built (it would contradict the observation); FIX = wording/citation only.

| # | contested row (v1) | v1 said | corrected value | source | label | verdict |
|---|---|---|---|---|---:|---|
| 1 | `Impact_Body_UPGR` emitters | 39 | **13** | `PARTICLES.md:125` | decoded | FIX |
| 2 | `Impact_Full_UPGR` emitters | 42 | **15** | `PARTICLES.md:126` | decoded | FIX |
| 3 | `Impact_Head_UPGR` emitters | 33 | **13** | `PARTICLES.md:127` | decoded | FIX |
| 4 | those counts, alternate column | — | module rows give **14 / 16 / 14** (BatmobileFunhouse) — **no** column gives 39/42/33 | `PARTICLES.md:335-337` | decoded | 39/42/33 **UNKNOWN origin** |
| 5 | `ImpactMaxDamagePow` shipped / Joker | 0.666 / 0.666 | **— / —** (no tag); base CDO **0.666000009** | `DAMAGE_RULES.md:150`; `CLASS_DEFAULTS.md:261` | decoded | FIX (the 0.666 pair is `:144` `BattleModeImpactMaxDamagePow`) |
| 6 | `ImpactMaxDamage` base | 100 | **100.0** | `CLASS_DEFAULTS.md:255` | decoded | FIX (was "UNSUPPORTED") |
| 7 | `ImpactMinDamageSpeed` base | 60 | **60.0**; archetypes 20 / 40 | `CLASS_DEFAULTS.md:257`; `DAMAGE_RULES.md:152` | decoded | KEEP |
| 8 | `ImpactMaxDamageSpeed` base | 200 | **200.0**; archetypes 150 / 180 | `CLASS_DEFAULTS.md:256`; `DAMAGE_RULES.md:151` | decoded | KEEP |
| 9 | `ImpactStrafeMod` base | 1.5 | **1.5**; archetypes 2.25 / 0.8 | `CLASS_DEFAULTS.md:258`; `DAMAGE_RULES.md:153` | decoded | KEEP |
| 10 | `ImpactBoostMod` base | 1.5 | **1.5**; archetypes 2 / — | `CLASS_DEFAULTS.md:260`; `DAMAGE_RULES.md:147` | decoded | KEEP |
| 11 | `ImpactCivilianVehicleMod` | 1.0 | **1.0** | `CLASS_DEFAULTS.md:259`; `DAMAGE_RULES.md:148` | decoded | KEEP |
| 12 | `StafeImpactImpulse` | 100000 | **100000.0** (sic, field name misspelled in the class) | `CLASS_DEFAULTS.md:262`; `DAMAGE_RULES.md:154` | decoded | FIX |
| 13 | "every field the body reads is listed there" | every field | **"11 fields, two serialised columns"**; base values are CDO, not §3.3 | `DAMAGE_RULES.md:136,139,156` | decoded | FIX |
| 14 | `ExplosiveImpactScreenShake` | "18 nested props", 5 shown | **18, all printed** — incl. `0x38 [150,150,150]`, `0x68 1.0`, `0x70 5.0`, `0x78 AdvancedOptions=None` | `CLASS_DEFAULTS.md:253` (dup `:560`) | decoded | KEEP (the omitted `150` is the largest value in the struct) |
| 15 | `CollisionFFWaveForm` CDO copy | omitted | archetype `0x019c`/5596 **and** CDO `0x00cc`/5596 | `CLASS_DEFAULTS.md:126`, `:204` | decoded | FIX |
| 16 | `chassis_slide_default` palette key | "—" | **0x74c4** (28 rows); slides `0x7528` / `0x74d8` / `0x7564` / `0x7500` | `PALETTE_HASH.md:71`, `:96-99` | decoded | FIX |
| 17 | `cargo_chassis_impact_*` set | cited to the collision package rows | exists, but its source is the **FX table**, not `DECODE_DEPTH.md` | `Research/JC3Grab/FX_TABLE.jsonl` | decoded (audit A-C27) | FIX (MIS-CITED) |
| 18 | "0 hits" for a speed field | 0 | **"0 collision-table speed members"**; `USAGES.md` has 7 `speed` hits, all `speedwind` / `speedrom` / nitro names | audit A-C28 (`USAGES.md:368,388,442-443`) | decoded (audit re-read) | FIX wording |
| 19 | `HeavyCannon_Impact_Px` "(4645–4655)" | index range | count **11** stands; the range is **not in the file** — drop it | `PARTICLES.md:107` | decoded / range UNKNOWN | FIX |
| 20 | ".effc string table: 0 values across 955 files, *the exhaust report*" | unnamed | **named:** 955 `.effc`, 0 string values | `tmp/freebuff/reports/exhaust-and-heat-plan.md:136` (count at `:121`, source `Research/JC3Grab/FX9_HAZE.md`) | decoded | FIX (citation existed, wasn't named) |
| 21 | band 3 = "+ `Engine.BML_Impacts` (`Play_Batmobile_Destroyed`)" | build it | **DROP.** Four events, all `Play_Batmobile_Destroyed` — it is the *car's own destruction* cue; firing it on a crash asserts the car is being destroyed | `AUDIO_FEATURES.md:729-731` | decoded | **DROP** |
| 22 | band table column "damage" | "damage (`shipped`)" | **"damage dealt to the target"** — 20→150 km/h ramp, `Pow` CDO 0.666, `StrafeMod` 2.25, `BoostMod` 2 | `DAMAGE_RULES.md:147-153` | decoded values, km/h **derived** | KEEP-OUT |
| 23 | band cut-points 20/75/150 and "band 0 spawns nothing" | presented as the port | still a **proposal**: no member gates sparks or scrape by speed; only damage is speed-gated | `DAMAGE_RULES.md:149-152`; `PARTICLES.md` (no speed) | **derived/proposal** | KEEP, labelled proposal |
| 24 | "no dent member, no dent asset" | treated as "no" | **confirmed** — the only `dent` matches in the grab are substrings of `identity rotation True` | `Research/BatmobileGrab/BOX_FLAGS.md:165-167` | decoded (absence) | **KEEP — now a requirement, not an inference** |
| 25 | `WallScrapeSparksSystemL/R` as the scrape | spark components | keep as **spark** components; BmAK has **no paint-scratch decal or scuff asset**, so "scratch" has nothing to port | `CLASS_DEFAULTS.md:140-141`, `:218-219` | decoded | KEEP (as sparks), scratch **UNKNOWN** |

### 2.1 What the observation kills, and what it does not

| claim | does it survive "no crash damage/scratch/dent"? | why |
|---|---|---|
| the eight `Impact*` damage fields | **yes, re-scoped** | outgoing only (`DAMAGE_RULES.md:136,139`); they set what the target loses |
| `BattleModeImpact*` 120/540, Pow 0.5/0.666 | **yes, re-scoped** | same outgoing family (`:144-146`) |
| `ImpactRoadAssist*` nine floats | **yes** | deflection physics, not damage |
| `ImpactSparks`, `JumpLandSparks`, `WallScrape*` | **yes** | particle and rumble members; they read as effects, never as damage |
| `ExplosiveImpactScreenShake` | **yes** | a shake, not a hit |
| `ImpactSparksSizeName = 'Size'` | **yes** | a parameter *name*; the curve that writes it stays UNKNOWN |
| band 3 destruction sound | **no — dropped** | it is the car's own destruction cue (`AUDIO_FEATURES.md:729-731`) |
| any dent / deform / mesh swap on impact | **no — never build it** | no BmAK member (`BOX_FLAGS.md:165-167`); in JC3 `deform_scale` is already **0** (`DAMAGE_MODEL.md:50,53`) |
| paint scratch / scuff | **nothing to port** | no scratch asset or member decoded; `scratch` = UNKNOWN in BmAK |
| "the car is immune, here is the field" | **no such field** | `TakesDamageFromRam` returns `true` unconditionally; immunity is engine-side (`DAMAGE_RULES.md:192-202`) |

---

## 3. Contested mode-switch rows — corrected value, line, verdict

The observation is about crashes, not modes, so nothing here is dropped on that ground. What these
rows lose is the right to claim values where the corpus holds two different objects.

| # | contested row (v1) | v1 said | corrected value | source | label | note |
|---|---|---|---|---|---:|---|
| 1 | part behaviours | 66 | **67** | `FEATURE_CENSUS.md:34` | decoded | off by one |
| 2 | `DriverLean` fleet | "23 aircraft" | **23 = 18 bikes + 5 boats, 0 aircraft** | `Research/challenge/card-T-10.md:58` (row A4) | decoded | v1 re-used the exact inference A4 marks BROKEN |
| 3 | `model_swap` | "string, one fleet value, 0..0 in the 100 rows" | **hash** `0..0`, n=100; **string** 1 distinct | `VOCABULARY.md:1605` / `:1606` | decoded | two members, not one |
| 4 | `_signature_shielded` | cited to `ENTITIES.md` | **`ENTITIES.md` 0 hits; `FORCEPULSE.json` 6 hits** | grep count, this run | decoded | MIS-CITED |
| 5 | `_signature_shielded_di_ravello` | listed as an entity variant | **UNKNOWN** — not in either cited file | would be settled by `Research/JC3Grab/INDEX.jsonl` (963 `.ee` paths) | **UNKNOWN** | drop until a path names it |
| 6 | `_civilian_01` "every armed chassis" | every | cited census rows show `debug` / `military_01` / `rebel_01` only; `_civilian_` exists as **386** paths | `FEATURE_CENSUS.md` rows; `mode-toggle-runtime-swap.md` §3 | decoded / **UNKNOWN** for "every" | narrow the claim |
| 7 | `TurnOnSpot` 0.8 / −0.8 / 2 | one set | **archetype** 0.8 / −0.8 / 2 **and** shipped-sim CDO **0.6 / −0.5 / 0.01** — v1 never said which object | `MODES.md:80-82`; `DRIVE_MODES.md:52-54` (stated at `:96`) | decoded | FIX: name the object |
| 8 | `BattleModeTurnOnSpotTorqueFactor` | 0.333333 | **0.333333** archetype (`MODES.md:92`) vs **0.3** on the sim (`DRIVE_MODES.md:61`) | both | decoded | two objects again; quote both |
| 9 | `TurningModeMaxSpeed` 600 cm/s = 21.6 km/h | 600 | **600 cm/s in all four packages**, 600/27.78 = 21.6 | `MODES.md:86` (derived) | decoded + derived | KEEP |
| 10 | `ArmourModeDamageReduction` | 0 shipped | **0** at `0x1918`; readers = `TakeDamage` only | `MODES.md:153`; `DAMAGE_RULES.md` §6.3 | decoded | KEEP — it is authored 0, not an undeclared switch |
| 11 | "0 handling members; the 42 hits are…" | 42 | count **not reproducible** (no regex/script named); the conclusion stands: no selector, no per-mode table among the 52 module types | `VOCABULARY.md` (52 sections); `DRIVE_CARRIERS.md` §0 | **UNKNOWN** (count) / decoded (conclusion) | FIX: drop the number, keep the negative |
| 12 | `ModularHud…`-style no-op rows | — | none | — | — | not applicable here |

### 3.1 The six carrier verdicts, restated with the object named

| pattern | carries which of the five rows | evidence |
|---|---|---|
| **boost state** (`nitro_boost`, `nitro_boost_upgraded`, `heat_boost`) | temporary handling only: torque ×2, grip ×1 / ×4.26, `extra_top_speed` +43.2 / +100.92, blend 0.2 s | `M §2.4` (decoded from `CustomLandGlobal`) |
| **hinged part + `*_T` variable** | stance/pose only | `all_hinged_part_properties`, 25 rows |
| **entity variant** (own `.ee`) | all five — but as **another vehicle**, not a switch | 963 `.ee`, 207 `_signature_`, 306 `_military_`, 758 `_rebel_` (`mode-toggle-runtime-swap.md` §3) |
| Bavarium shield part | none (damage prop) | 26 parts / 14 entities / 4 chassis |
| part damage/death swap | none (broken/intact) | `VOCABULARY.md:1605-1606` |

**Nothing in this section changes because of the no-crash-damage observation.** The observation does,
however, remove one tempting shortcut: a mode swap cannot be faked by ramming something to "change
state" — the car does not take that damage at all.

---

## 4. Closest system and build step — impact effects

**Closest system, named:**

1. **The effect carrier:** `chassis_impact_vfx` (171 entities) + `chassis_impact_default_sfx` (128) on the
   **same object hash `2963579072`** (`USAGES.md:329`) — attach one, get both.
2. **The surface axis:** the six-package `chassis_impact_{default,dirt,sand,snow,vegetation,water}` family
   plus the four-package `chassis_slide_*` family (`DECODE_DEPTH.md:208-224`; keys at `PALETTE_HASH.md:70-99`).
3. **The speed/contact axis — this is the one v1 missed:** JC3's only contact-rate channel,
   `rotor_collision.damage_to_other_per_second` = **2000/s** in `vehicle_common.vmodc` at **`0x138`**,
   with `min_rpm` **1260** at `0x130` giving the ~20 km/h floor (`tdm7-contact-damage-speed-band.md` §2).
4. **The self-immunity the operator described:** `impact_damage_factor` **0**, `deform_scale` **0**,
   `impact_armor` **5000 @ 100** (`DAMAGE_MODEL.md:50,53`) — already in the build.

**Build step (ordered, each step independently revertible):**

1. **Private `vehicle_common.vmodc` copy** for the Batmobile entity: `min_rpm` 0x130 → `1260` (floor),
   rate 0x138 → keep **2000**; size unchanged (12,271 B), `.toc` re-point with `eetoc.py patch`.
   Rationale: `tdm7` §3-§4 — the floor is a gate problem, the ceiling is an absent-member problem.
2. **Keep `VehicleDamage.impact_damage_factor` = 0 and `deform_scale` = 0**, `impact_armor` 5000 @ 100
   (`DAMAGE_MODEL.md:50,53`). This is the operator's "no damage, no dent" as data.
3. **Attach the effect tables** from a donor that carries `2963579072`: `chassis_impact_*` for the hit,
   `chassis_slide_*` for continuous contact. Copy the row, do not hand-write one — the numeric layout of
   an `SDynamicAttachedEffect` row is still UNKNOWN (`DECODE_DEPTH` gives package rows only).
4. **Run the 5-minute probe first** (`AGENTS.md` rule): clone the donor, change only the name, hit a wall
   at 20 and 80 km/h, read whether the target loses health and the Batmobile's bar does not move. A zero
   at 80 km/h means the consumer reads rotor RPM (a car has no rotor part) → revert step 1's `min_rpm`.
5. **Do not build:** the destruction cue on contact, any dent/deform, any scratch asset, any speed-banded
   *spark* gate presented as decoded. The band `20/75/150` stays a labelled proposal.

**Pilot sentence (from `tdm7` §5, unchanged):** at 80 km/h a head-on ram must remove **40–100 %** of a
stock car's 100-point bar while the Batmobile's own bar does not move; at 10 km/h, **0–5 %**.

---

## 5. Closest system and build step — the mode-swap trigger

**Closest system, named:** the **entity-variant pattern** — JC3 ships "the same vehicle in another
configuration" as a second `.ee` (963 entities; 207 `_signature_`, 306 `_military_`, 758 `_rebel_`,
386 `_civilian_`, 438 `_debug`), never as a runtime switch (`mode-toggle-runtime-swap.md` §3). It is the
only pattern that carries all five BmAK mode rows (own `arcade`/`CustomLandGlobal` values, own stance
parts). For the *transition polish* the closest carrier is the boost state's 0.2 s blend; for the stance,
the hinged-part table. Neither is a mode selector.

**Build step (ordered):**

1. **Author two leaves from the one hybrid chassis** — `batmobile_pursuit.ee` and `batmobile_battle.ee` —
   each carrying its own module values. This step needs **no** trigger and is verifiable on its own.
2. **Prove both leaves spawn and drive** through the **Rebel Drop** path (candidate 2 in the trigger plan,
   `REBELDROP.md` §7) — proven delivery, no entity swap, no exe work.
3. **Audio carrier, only once a trigger exists:** `TransformationReverseDirectionIntoBattleModeSound`
   (`0x12e4`) and `…IntoPursuitModeSound` (`0x12dc`) are the only mode-transition vocabulary in `MODES.md`
   (`:136-137`) — and they are **sounds, not triggers**.
4. **The trigger itself is the gap.** `USE_VEHICLE_MOD` (RPADRIGHT) is the closest keymap action, but its
   consumer is unknown, and the 0.40 s hold is **authored, not decoded** (audit C7, C15). Do not present
   either as a BmAK value.
5. **Do not build** an in-place handling switch: no selector member and no per-mode table exist among the
   52 module types, so there is nothing to attach the second value set to.

---

## 6. U1 — explicit UNKNOWN, and the file that settles it

| field | value |
|---|---|
| id | **U1** — is there any consumer that swaps or replaces a vehicle entity at runtime? |
| status | **UNKNOWN** — no consumer found, and not refuted |
| searched | `Research/JC3Grab/INDEX.jsonl`, 81,952 paths: `spawn` 722, `replace` **0**, `swap` 658 (all mesh/texture assets; 0 in `graphs/`, 0 `.ee`, 0 `.bl`), `variant` 4 (all art), `respawn` **0**, `despawn` **0**, `teleport` 11 |
| what the hits prove | teleport consumers exist and address entities; **none** spawns, replaces or despawns one |
| **file that settles it** | **`JustCause3.exe`** — its entity/vehicle streaming consumer. `INDEX.jsonl` holds **0 `.exe` and 0 `.dll`** entries, so the answer is not in the archive at all. Second read: the exe's script binding for the three teleport graphs |
| cheapest non-code fallback | Rebel Drop (§5 step 2) — delivers the battle leaf without a swap |
| what would change the answer | a decoded exe call taking an entity and returning another, or a live probe that watches the entity id while the bound action is pressed |
| why it stays UNKNOWN and is not filled in | path-level search cannot see a consumer implemented entirely inside the exe; `AGENTS.md` forbids inventing the mechanism |

**Net effect of U1 on the ledger (from `mode-toggle-runtime-swap.md` §4):** three losses (T-MD5 battle
top-speed curve, T-MD6 21.6 km/h cap, T-MD15 one-row variant table) turn on the swap; four survive it
(T-MD7 slip scales partly, T-MD8 turn-on-spot, T-MD13 animation node, T-MD14 audio); three are already
carried (T-MD11 camera, T-MD12 lamps, T-MD10's 0).

---

## 7. Checks run

```
grep -nE "BattleModeImpact|ImpactBoostMod|ImpactCivilianVehicleMod|ImpactMaxDamage|ImpactMinDamageSpeed|ImpactMaxDamageSpeed|ImpactStrafeMod|StafeImpactImpulse" Research/BatmobileGrab/DAMAGE_RULES.md
   → 144-154 (the 11 field rows); 136 "outgoing"; 139 "every one of them is an *outgoing* multiplier"; 156 "11 distinct class fields"
sed -n '186,217p' Research/BatmobileGrab/DAMAGE_RULES.md   → §3.4 TakesDamageFromRam, script, "return true", 7 bytes
grep -n "ImpactMaxDamage|StafeImpactImpulse|ImpactCivilianVehicleMod" Research/BatmobileGrab/CLASS_DEFAULTS.md
   → rows 77-84 at file lines 255-262: 100.0 / 200.0 / 60.0 / 1.5 / 1.0 / 1.5 / 0.666000009 / 100000.0   ← the audit's "UNSUPPORTED base column", decoded
grep -nE "ImpactSparks|WallScrape|CollisionFFWaveForm|ImpactSparksSizeName|ExplosiveImpactScreenShake" Research/BatmobileGrab/CLASS_DEFAULTS.md
   → 115,116,117,126,140,141,194,195,204,218,219,221,253
grep -nE "Impact_Body_UPGR|Impact_Full_UPGR|Impact_Head_UPGR|HeavyCannon_Impact" Research/BatmobileGrab/PARTICLES.md
   → 125=13, 126=15, 127=13, 107=11; module table 335-337 = 14/16/14
grep -n "part behaviours" Research/JC3Grab/FEATURE_CENSUS.md → 34: 67
grep -nE "chassis_slide" Research/JC3Grab/PALETTE_HASH.md → 71: 0x74c4; 96-99: 0x7528/0x74d8/0x7564/0x7500
sed -n '54,60p' Research/challenge/card-T-10.md → A4 at :58 "18 bikes + 5 boats, 0 aircraft"
grep -n "model_swap" Research/JC3Grab/VOCABULARY.md → 1605 hash 0..0 n=100; 1606 string 1 distinct
grep -c signature_shielded ENTITIES.md FORCEPULSE.json → 0 / 6
sed -n '78,83p' Research/BatmobileGrab/MODES.md → 80-82 TurnOnSpot 0.8 / -0.8 / 2 (78 is the header, 79 the separator)
grep -nE "TurnOnSpot" Research/BatmobileGrab/DRIVE_MODES.md → 52-54 CDO 0.6 / -0.5 / 0.01; 61 0.3; 96 states it
sed -n '38,59p' Research/JC3Grab/DAMAGE_MODEL.md → impact_damage_factor / deform_scale 1/1 donors, 0/0 build
grep -n "955" tmp/freebuff/reports/exhaust-and-heat-plan.md → :136 "955 files, 0 string values"
```

**Limits, stated.** All static reads; no game launched. Four claims are audit re-reads, not my own
re-derivation, and are marked so above: the `USAGES.md` 7-hit `speed` census (row 18), the
`cargo_chassis` source (row 17) and the `PARTICLES.md` counts behind the audit's C29. `JustCause3.exe`
was not opened — U1 stays UNKNOWN by design, not by omission. Nothing was modified in
`Research/`, `Builds/` or the game install.

---

## 8. Answers in one line each

- **Does a crash damage the car?** No, and no BmAK field could make it: the whole `Impact*` family is
  outgoing (`DAMAGE_RULES.md:136,139`), and the incoming entry point returns `true` unconditionally
  (`:192-202`). In the JC3 build the immunity is data: `impact_damage_factor` 0, `deform_scale` 0.
- **Does it dent?** No member, no asset, no morph (`BOX_FLAGS.md:165-167`); `deform_scale` stays 0.
- **Does it scratch?** Nothing to port — the `WallScrape*` members are spark components, not paint damage.
- **What is the impact build?** Private `vehicle_common.vmodc` (`min_rpm` 1260, rate 2000) + copied
  `2963579072` effect tables + the two JC3 immunity switches already at 0.
- **What is the mode-swap build?** Two `.ee` leaves, both proven through Rebel Drop; the swap trigger
  itself is **U1 = UNKNOWN**, settled only by `JustCause3.exe`.
