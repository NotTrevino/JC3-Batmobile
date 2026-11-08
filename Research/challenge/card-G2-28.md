# Assumption challenge — G2-28 · damage model, complete, with a predicted hits-to-kill table

**Card:** `GRAB_BACKLOG.md` §G2-28 (line 759), §12 row (line 1311).
**Outputs challenged:** `Research/JC3Grab/DAMAGE_MODEL.md`, `DAMAGE_MODEL.json`,
`Tools/scripts/damage_predict.py`, MODLOG §"G2-28 … done" (line 11230).
**Rules applied:** `GRAB_BACKLOG.md` §0.5 (R1–R14), especially R5 (a member is what it does, not
what it is called), R4 (no guess sold as fact), R11 (a table comes from a script with a check).

**Method.** Every check below was run against files already on disk: the 232 decoded entity caches
in `E:/Modding/JustCause3/_grab/entities/`, the exploded tune corpus in `E:/Modding/JustCause3/_grab/weapons/`,
`Builds/test-077` and `Builds/test-091`, `Research/BatmobileGrab/DAMAGE_RULES.md`, and `MODLOG.md`.
No game was launched, nothing was written under `D:/Games`, nothing was committed. One scratch
directory (`tmp/g228chk/`) was created for a `ConvertAdf` test and deleted again; the only file
left behind is this report.

---

## VERDICT summary

| # | assumption | verdict |
|---|---|---|
| 1 | "233 decoded `VehicleDamage` modules" is also "233 vehicles" / "233 roots" | **WEAK** — three different 233s are conflated |
| 2 | root `health` 100.0 / `invulnerable` 0 "on all 233 roots" | **HOLDS** (value, re-verified) but the sentence is a hard-coded literal in the generator |
| 3 | build = medium tank's profile, differing in 6 values; donor differs in 23 | **HOLDS** — reproduced exactly |
| 4 | that profile is *the medium tank's* | **WEAK** — it is `lave_health_tank.vmodc`, shared by 10 entity variants (APC, Bavarium tank, cargo plane) |
| 5 | build's part table = donor's with exactly 1 change | **HOLDS** — 24 identical names, 1 value changed |
| 6 | the part-type list is per vehicle family, not global | **HOLDS** — 6 distinct name sets, not 2 |
| 7 | "no file maps a weapon to a channel" (0 of 1,515 rows) | **HOLDS**, and is under-tested in the card: 0 of **19,458** rows over **190** tune files |
| 8 | the §3 "channel used" column | **BROKEN** — same gun type gets opposite channels, and the JSON contradicts the doc |
| 9 | the tank shell's carrier is `PlayerDamage` 1500 | **BROKEN** (R5) — the same ftunec ships `AIDamage` 550 in a 6 m radius; never mentioned |
| 10 | "primary component = largest damage" | **WEAK** — for the grenade it picks the `unknown` channel over the known one; the medium tank's headline flips 2 → 3/6 |
| 11 | `explosion_threshold`: "both readings fit the data" | **WEAK** — 134/233 thresholds equal `max_health`; 5 of 6 distinct values are health values |
| 12 | test-077 "failed with the symptom unrecorded"; H1/H2 remain live models | **BROKEN** — MODLOG §99 records the symptom, and it falsifies H1 *and* H2 for the bullet channel |
| 13 | fleet maximum `bullet_armor_strength` = 99, so 100 is out of domain | **HOLDS** for `bullet`; parenthetical ranges omit explosion/impact reaching 100 |
| 14 | ARM-1 gate: strength 100 (H1) or ≥ 144 (H2) | **WEAK** — 144 assumes all 8 pellets hit one component; and §12 says the gate is never reached |
| 15 | BmAK ratio = 1200/50 = 24 hits → `max_health` 36,000 | **WEAK** — 50 is only the *Primary* projectile (75 and 110 exist); H1 gives 18,000 |
| 16 | "`DAMAGE_RULES.md` §3.5 lists 60 for `Batmobile_Missile_*`" | **BROKEN as a finding today** — the file now says 250 and carries the "read by name" note |
| 17 | "`damage_audit.py` FAILS on the current build" | **BROKEN today** — exit 0, `check ok`, 5 declarations (T-14 removed the stale one) |
| 18 | part → damage type is UNKNOWN because every other parts file fails `ConvertAdf` | **HOLDS** — re-tested: still throws, 0 output |
| 19 | 81 cells with 27/27/19 finite | **HOLDS** — recomputed from the JSON |
| 20 | `--check` proves the document | **WEAK** — it proves byte-equality with its own generator; a wrong literal inside the generator passes |

Headline: **the numbers are almost all reproducible; the model choice is not.** One in-game datum
already on disk (`MODLOG` §99: "a couple mags killed the vehicle", on a build with
`bullet_armor_strength` 100) kills H1 and H2 for the bullet channel, and the card's own P1/P2
probes and ARM-1 conclusion are built on those two models.

---

## 1. "233 decoded `VehicleDamage` modules" = "233 vehicles" = "233 roots"

**Claim.** §1 step 4: "the 233 decoded `VehicleDamage` modules". §2: "The three vehicles". §7:
"`233` `VehicleDamage` modules". MODLOG done-check: "fleet 233 modules". §1 step 6 and §8: "100.0
on all 233 **roots**".

**Test.** Count caches, entities and modules; find entities with more than one module. Then compare
with the root census in `DAMAGE_MECHANISMS.md` §1, re-run through its own generator.

```
$ python - <<'EOF'  # glob E:/Modding/JustCause3/_grab/entities/*.ee.json
cache files 232
distinct entity strings 232
VehicleDamage modules 233
entities with >1 module: {'editor/entities/jc_vehicles/02_air/v4603_plane_urga_cargotransport/
                          v4603_plane_urga_cargotransport_military_cargo_tank.ee': 2}
```

The doubled entity's two modules are different modules on one vehicle:

```
lave_health_tank.vmodc        max_health 2000 bullet 5000 99 expl 250 50
plane_health_extreme.vmodc    max_health 2000 bullet 2000 99 expl 0 0
```

The root census is a *different* 233 — 233 root objects over 232 `.epe` graphs, with a **train**
entity doubled:

```
$ python Tools/scripts/jc3_damage_search.py --check
PASS damage mechanisms
232 entities, 91157 objects, 233 vehicle roots, 2 token classes, 27 token properties
  CCar 126 | CBoat 35 | CHelicopter 23 | CMotorBike 19 | CAirPlane 18 | CTrain 12
```

**Result.** There are 232 vehicle entities. "233" is (a) a module count in `fleet_census()`, (b) a
root-object count inherited from `DAMAGE_MECHANISMS.md`, and (c) a per-vehicle count in the §2
prose. (a) and (b) coincide numerically and are **not the same set** — (a) doubles a cargo-plane
variant, (b) doubles a train. `DAMAGE_MECHANISMS.md` line 28 states this correctly; G2-28's own
sentences drop the caveat, so "233 vehicles" is not supported and "all 233 roots" is true only in
the sense of root objects.

**Verdict: WEAK.**

## 2. Root `health` 100.0 and `invulnerable` 0 "on all 233 roots"

**Claim.** §1 step 6: "the entity root's `health` float32 (100.0 on all 233 roots) + the root's
`invulnerable` int32 (0 on all 233)"; §8: "all 233 roots are 100.0".

**Test 1 — is it re-derived?** `damage_predict.py` line 385 carries it as a **string literal**:

```
385:    # the fleet ships health=100.0 / invulnerable=0 on all 233 roots (DAMAGE_MECHANISMS §1)
389:                                 "invulnerable": "0 on all 233 roots (DAMAGE_MECHANISMS §1)",
```

The only root the card actually re-reads is the build's own `.epe` (`root_fields`, line 147).

**Test 2 — is the inherited claim true now?** Re-ran its source generator:

```
$ python Tools/scripts/jc3_damage_search.py --check
  CCar 126 roots | invulnerable {'0': 126} | health {'100': 126}
  CBoat 35 roots | ... {'100': 35}      CHelicopter 23 | CMotorBike 19 | CAirPlane 18 | CTrain 12
```

**Test 3 — the build's own root, read live:**

```
find_epe: Builds/test-091/aaf/.../v0300_car_kensington_sportsmuscle_civilian_01.epe
root_fields: health  {'value': '00 00 c8 42', 'float': 100.0, 'value_at': 537}
             invulnerable {'value': '00 00 00 00', 'int': 0, 'value_at': 1167}
```

**Result.** The value is right and independently reproducible; the `epe+1167` offset quoted in the
card matches the decode. What does **not** hold is that G2-28 verified it: a `--check` pass cannot
catch a wrong constant here, because the constant is part of the generator (see §20).

**Verdict: HOLDS on the value, WEAK as evidence produced by this card.** Also see §1 for the unit.

## 3. "The build is the tank's profile in 6 values; against the donor it differs in 23"

**Claim.** §2: "differs from the **medium tank's** in 6 values … Against the **donor** it differs in
23 values"; `DAMAGE_MODEL.json` `diffs`.

**Test.** Dump `Builds/test-091`'s `VehicleDamage` with the project's own reader and diff it against
both caches field by field.

```
build VehicleDamage: file lave_health_medium.vmodc  scalars 30  part rows 24
  bullet 5000@99  bullet_heavy 5@20  explosion 250@50  impact 5000@100
  fire 0@0  melee 5000@100  electricity -1@100  grapple_pull -1@100
  max_health 2000  impact_damage_factor 0  deform_scale 0
scalar diff tank->build: [impact_armor 0->5000, impact_armor_strength 0->100,
  melee_armor 0->5000, melee_armor_strength 0->100, impact_damage_factor 1->0,
  deform_scale 1->0]                                            (6)
scalar diff donor->build: 23 values
JSON diffs: scalars_build_vs_tank 6, scalars_build_vs_donor 23, scalars_tank_vs_donor 17
```

Nobody in the fleet carries the build's tuple: of 233 modules, **0** match its 30-scalar set and
**0** match its 8-channel `armour@strength` set. So "not a translation of the donor" is measured
fact, not inference.

**Verdict: HOLDS.**

## 4. …but "the medium tank's profile" is a name

**Claim.** §2: "the build is the tank's profile".

**Test.** Which vehicles carry the tank's exact 8-channel tuple plus its `max_health`?

```
tank tuple ((5000,99),(5,20),(250,50),(0,0),(0,0),(0,0),(-1,100),(-1,100)) max_health 2000
vehicles with the tank channel tuple: 10   with its max_health too: 10
   v0200_car_capstone_apc_{debug,military_01,rebel_01}
   v0201_car_capstone_mediumtank_{debug,military_01,rebel_01}
   v0202_car_capstone_bavariumtank_{debug,military_01,rebel_01}
   v4603_plane_urga_cargotransport_military_cargo_tank
```

The module file is literally the shared `lave_health_tank.vmodc` (10 users, one distinct channel
tuple across all 10). Likewise `lave_health_medium.vmodc` has 77 users and one distinct tuple.

**Result.** The build's numbers come from the **tank/APC/armoured airframe** health module, not from
"the medium tank" as an individual. The claim stays true in the sense that matters ("not the donor"),
but a reader will take "the tank's profile" as a unique kinship it does not have, and the row
"module file `lave_health_tank.vmodc`" is the real evidence.

**Verdict: WEAK (attribution, R5).**

## 5. "The build's part table is the donor's with exactly 1 change"

**Claim.** §2: `Land_Wheel.instantly_damaged_by_bullets` 1 → 0 is the only part-level edit; MODLOG:
"a fact no earlier document states".

**Test.** Parse `part_damage_types[i].*` for donor, tank and build; diff every value.

```
build part names: ['Default','Land_Generic','Land_Body','Land_Wheel',…,'Land_Grill']   (24)
names equal donor/build: True   tank/build: True
donor->build diffs 1: [(3, 'Land_Wheel', 'instantly_damaged_by_bullets', 1, 0)]
tank->build diffs 23
JSON diffs: part_table_build_vs_donor 1, part_table_build_vs_tank 23,
            part_table_tank_vs_donor 24
```

**Result.** Reproduced to the value, including the index (3) and the name. This is the card's
strongest single finding and it survives.

One caution for whoever uses it: MODLOG §99c recorded that **test-077**'s part table was the stock
medium car's too (`Land_Wheel 1020/400/100`). So the flag was flipped between 077 and 091 — the
edit is real, but "no earlier document states it" undersells §99c, which had already measured the
table and found it unchanged from stock.

**Verdict: HOLDS.**

## 6. "The type list is per vehicle family, not global"

**Claim.** §1 step 5: "the train's own health module carries a `Train_*` set of 13 names, so the
type list is per vehicle family". Tested on two families (24 `Land_*`, 13 `Train_*`).

**Test.** Cluster all 233 modules by their ordered list of `type.string` values.

```
distinct part-name sets: 6
  145 x 24 names, first: Default | second: Land_Generic
   32 x 17 names, first: Default | second: Boat_Generic
   23 x 14 names, first: Default | second: Heli_Generic
   18 x 15 names, first: Default | second: Plane_Generic
   12 x 13 names, first: Default | second: Train_Generic
    3 x 16 names, first: Default | second: Boat_Generic   (a second boat set)
```

**Result.** Six sets, one per family, with a second boat variant. The claim holds and is better
evidenced than the card shows: the donor's 24 `Land_*` names cover 145 of 233 modules.

**Verdict: HOLDS.**

## 7. "No file maps a weapon to a channel"

**Claim.** §1 step 3: "across the 9 weapon tunes decoded here (1,515 member rows) 0 member names
mention heavy/armour/penetration".

**Test.** The card tested 9 tunes. The exploded corpus holds **190** vehicle-weapon tune files (22
weapon dirs). Decoded all of them with the project's own reader and searched every member path:

```
files 190 decoded 190 failed 0 member rows 19458
member names matching heavy/armor/armour/damage_type/penetrat: 0
```

Also searched the 232 entity caches: `bullet_heavy` occurs **only** inside `VehicleDamage` modules,
in no weapon, projectile or tune file (232 files, all `entities/`).

**Result.** The null result is real and much stronger than the card's sample. Two scope caveats:
the 22 weapon dirs are `06_vehicle` only (Rico's hand weapons exist only inside archives, not
exploded here), and the search is over **member names**, not values — a channel could still be
selected by an enum value or by a damage-type object reference. Given `MyDamageType` is absent on 12
of 26 BmAK archetypes (`DAMAGE_RULES.md` §3.5), the negative is worth keeping but not universal.

**Verdict: HOLDS (with the scope stated).**

## 8. The §3 "channel used" column — a member read by its name

**Claim.** §3 assigns a channel to all nine arms: `rpg` → explosion, `heli_missile` → bullet,
`tank_cannon` → explosion, `heli_mg` → bullet, all small arms → bullet. Step 3 two pages earlier
says the mapping is UNKNOWN.

**Test A — is the assignment consistent with gun type?**

```
rpg           missile_weapon  → explosion
heli_missile  missile_weapon  → bullet
tank_cannon   bullet_weapon   → explosion
heli_mg       bullet_weapon   → bullet
```

Two `missile_weapon`s land on opposite channels; two `bullet_weapon`s land on opposite channels.
The column is therefore *not* derived from the gun type — it is a judgement about which number the
analyst decided "does the work".

**Test B — does the JSON agree with the doc?**

```
arms.grenade.channel        = "explosion"     arms.heli_missile.channel = "bullet"
table.donor.grenade.primary = {"channel": "unknown", "damage": 1012.500018, "component": "direct"}
table.medium_tank.heli_missile.primary = {"channel": "unknown", "damage": 1500.0}
table.build_test-091.tank_cannon.primary = {"channel": "explosion", "damage": 1500.0}
table.build_test_091.tank_cannon.components[1] = {"channel": "bullet", "damage": 1.0,
                                                  "H1": 200000}
```

The same arm carries `explosion` in one table and `unknown` in another, in one file.

**Result.** The single column every hits-to-kill number depends on is (i) declared UNKNOWN by the
card, (ii) filled anyway, (iii) internally inconsistent between two members of the same gun class,
and (iv) inconsistent between the JSON's two representations of the same arm. This is R5 in its
textbook form. It is *not* harmless: the armour pair used for an arm changes by up to two orders of
magnitude (medium tank `bullet` 5000@99 vs `explosion` 250@50 — 134 hits vs 2).

**Verdict: BROKEN.**

## 9. The tank shell's carrier: `PlayerDamage` 1500, and only that

**Claim.** §3 line for `tank_cannon`: "blast (PlayerDamage) 1500 in 8 m"; Q1-DM-A: "one tank shell
into the Batmobile's body, at the centre of the 8 m blast", expected 2/3/2 shells.

**Test.** Decode `w602_mediumtank_canon.ftunec` (present in 9 entity bundles) with the same reader
the card uses, and print every damage member:

```
PlayerDamage                 1500
PlayerDamageRadius            8.0
PlayerDamageRadiusPercentageMax  0.15
AIDamage                      550
AIDamageRadius                6.0
```

The card never mentions `AIDamage`: `grep -n "AIDamage\|ai_damage" DAMAGE_MODEL.md` → no hits
(only `damage_predict.py` lines 218/272 read it, for hand-weapon `PlayerDamage` rows).

**Result.** The field is a *pair* — `PlayerDamage`/`PlayerDamageRadius` and `AIDamage`/`AIDamageRadius`
— and a medium tank shell arriving at the Batmobile is an **AI** shot. The card picked the player
half by its name. Under 550 the same probe reads very differently:

| | 1500 (card) | 550 (`AIDamage`) |
|---|---:|---:|
| H0 (2000 HP) | 2 | 4 |
| H1 (strength 50 → 275) | 3 | 8 |
| H2 (250 pool) | 2 | 5 |

Q1-DM-A is the *only* probe the card offers to separate H1 from H0/H2 at a small count, and its
expected numbers are conditional on an unstated member choice. (Every tank-cannon row of all three
vehicle tables inherits it. Rico's RPG and grenade are player-thrown, so `PlayerDamage` is the
defensible choice there — the problem is specific to the AI weapons, `w602`/`w604`.)

**Verdict: BROKEN (R5).** The fix is cheap: print both members and give both counts.

## 10. "Primary component = the largest damage"

**Claim.** §4: "Per-shot damage against the **primary** component (the largest one), on that
component's channel."

**Test.** The JSON keeps every component. Two cases where "largest" decides the headline:

```
medium_tank.rpg      components: blast 1500 explosion 250@50 -> 2/3/2
                                  direct 15 unknown           -> 134
                     primary: blast (largest)                 2/3/2   consistent
medium_tank.grenade  components: blast 700 explosion 250@50   -> 3/6/4
                                  direct 1012.5 unknown       -> 2/2/2
                     primary: direct (largest, unknown channel) 2/2/2  <- discards the known channel
build.grenade        same shape: 3/6/4 (blast) vs 2/2/2 (direct); primary = 2/2/2
```

**Result.** The rule is stated, so it is not hidden, but it has a consequence the card does not
draw: for the two thrown/AI arms whose components disagree, the rule prefers the component whose
channel nobody can name, and the reported count drops from a 3–6 hit bracket to a single "2". The
"lower bound on hits" note is technically right, but the reader is handed the most optimistic cell
of the strongest vehicle as its headline.

**Verdict: WEAK** (a defensible convention, sold as a neutral one).

## 11. `explosion_threshold`: "both readings fit the data"

**Claim.** §1 step 7: "the fleet's 500..4000 range overlaps max_health 500..4000, so both readings
fit the data"; §8 repeats it as an UNKNOWN.

**Test.** Census of both members over 233 modules:

```
distinct explosion_threshold: [500, 700, 1000, 1800, 2000, 4000]
distinct max_health:          [500, 700, 1400, 1500, 1800, 2000, 4000]
explosion_threshold == max_health: 134 of 233
threshold values not on the max_health ladder: [1000]
```

**Result.** The range claim is exact. But "both readings fit equally" is not what the data shows:
57 % of the fleet sets the threshold to *exactly* its own health, and five of the six threshold
values are health values (only 1000 is not). A designer tuning "damage that destroys outright" would
have no reason to reproduce the health ladder that precisely; a health-threshold reading explains it
for free. The card presents a 50/50 and the data leans one way.

**Verdict: WEAK.** Not broken — the reading is still not stated in any file, and 1000 is a real
counter-example.

## 12. test-077 "symptom unrecorded" — and what the symptom does to H1 and H2

**Claim.** §1.1 model table: "**Counter-evidence:** test-077 shipped exactly strength 100 and still
failed (MODLOG 98, symptom unrecorded)"; MODLOG: "the *mechanism* … step 3 … and step 7 … have no
bridge in any file", with H1/H2 carried as live models and Q1-DM-A/B as the discriminators.

**Test.** Read the record forward from §98. `MODLOG.md` §99 (line 4946) opens with:

> ## 99. 077 in-game: "a couple mags killed the vehicle". Module linkage PROVEN; real parity gaps found.
> User, one line: "note: couple mags killed the vehicle." Live dropzone unchanged (test-077 …)

and §99d (line 5019) concludes:

> 074 already ran `bullet_armor` 5000/99 — the tank's own pair, byte for byte — and bullets still
> chipped the vehicle (090, 096). … **The armour gate is therefore not what stops bullets on this
> vehicle.**

Now put the shipped numbers beside that sentence:

```
Builds/test-077:  max_health 2000   bullet_armor 5000   bullet_armor_strength 100
Builds/test-091:   max_health 2000   bullet_armor 5000   bullet_armor_strength  99   (T-DM2)
assault rifle w111: damage 32, vehicle_damage_factor 1 → 2000 / 32 = 63 rounds ≈ two 30-round mags
```

**Result.** "A couple of mags" is 60-odd rifle rounds ≈ 1,920 of 2,000 HP. That is H0 to within
one magazine. It is *impossible* under H1 (strength 100 = 0 damage, "never") and impossible under
H2 (a hit at or below strength 100 is absorbed, and the 5,000-point pool is never touched). So the
one in-game observation the project has **falsifies both models the card treats as live** for the
bullet channel, and supports "the armour pair is not on the bullet path at all".

Two consequences the card should carry and does not:

1. The bracket is not three-way. For bullets, H0 is the only model consistent with the record;
   H1/H2 are contradicted by measurement, not merely untested.
2. ARM-1's whole premise — "the gate needs `bullet_armor_strength` 100 (H1) or ≥ 144 (H2)" — is
   aimed at a member that has demonstrably done nothing in three shipped tests (073/074/077).

**Verdict: BROKEN.** The "symptom unrecorded" clause is factually wrong on disk (it was recorded
the next day, and §99 is the most discriminating datum in the file), and the model weighting built
on it is contradicted by that datum.

## 13. "Fleet maximum `bullet_armor_strength` = 99, so 100 is out of domain"

**Claim.** §1 step 4: "`<channel>_armor_strength` (0..99 for bullets, 0..100 for
electricity/grapple)"; §5: "the fleet maximum is 99".

**Test.** Histogram over 233 modules:

```
bullet_armor_strength counts: [(0, 183), (50, 18), (60, 9), (75, 4), (99, 19)]
```

and the audit's own ranges for the other channels:

```
bullet_heavy_armor_strength   shipped 0..50      explosion_armor_strength  shipped 0..100
impact_armor_strength         shipped 0..100     electricity/grapple       shipped 0..100
```

**Result.** "99 is the bullet maximum" holds (19 modules sit there). The parenthetical range claim is
incomplete: strength 100 is *shipped* on the explosion and impact channels (13 modules each), so
"0..99 for bullets, 0..100 for electricity/grapple" understates where 100 already occurs. That
matters to §5's argument, which leans on 100 being out of the shipped domain — it is out of the
domain for **bullet** only.

**Verdict: HOLDS for the claim as used, WEAK as worded.**

## 14. ARM-1 gate = 100 (H1) or ≥ 144 (H2)

**Claim.** §5: "H2: `bullet_armor_strength` >= 144"; "the shotgun delivers 144 per pull"; "the
build ships 50" for explosion.

**Test.** The decoded values are right:

```
shotgun  w151_RYS_96: damage 90, vehicle_damage_factor 0.2, bullets_per_shot 8 → 144.000002
```

But `bullets_per_shot 8` is eight independent projectiles. 144 is the per-pull damage **only if all
eight pellets hit the same component**, which is the best case for a shotgun, not the expected case;
at any spread the per-hit figure is 18 x k. So "≥ 144" is an upper bound on the gate, derived from an
upper bound on the weapon.

**Result.** Arithmetic holds; the inference "a gate at 144 would stop the shotgun" does not, because
a gate at 144 stops only the pulls where every pellet arrives. Combined with §12, the gate question
is moot for the bullet channel anyway: strength 100 shipped and the car still died to two mags.

**Verdict: WEAK.**

## 15. BmAK ratio: 1200/50 = 24 hits → `max_health` 36,000

**Claim.** §5: "`Pawn.Health` **1200**, the heavy cannon projectile `Damage` **50** … so the BmAK
ratio is **1200 / 50 = 24 heavy-cannon hits**"; "`max_health` = 24 x 1500 = 36,000".

**Test A — is 50 *the* heavy cannon?**

```
DAMAGE_RULES.md §3.5: Batmobile_Heavy_Cannon_Primary_Projectile      Damage 50
                      Batmobile_Heavy_Cannon_BodyShot_Projectile     Damage 75
                      Batmobile_Heavy_Cannon_Fully_Upgraded_Projectile 75 (TurretShotDamage 110)
                      Batmobile_Heavy_Cannon_HeadShot_Projectile      TurretShotDamage 110
```

Three hit locations, three numbers. 50 is the weakest; 1200/50 = 24, 1200/75 = 16, 1200/110 ≈ 11.

**Test B — is 1500 the JC3 shell on a 50-strength vehicle?** The build ships
`explosion_armor_strength` 50, so under the card's own H1 the 1500 blast arrives as 750:

```
H0: 24 × 1500 = 36,000      H1: 24 × 750 = 18,000      H2: (250 + 24×1500) = 36,250
```

which is exactly what `Working/Translation/t10_damage_edits.json` line 225 records ("the H0 answer;
H2 needs 35750, H1 18000"). `DAMAGE_MODEL.md` §5 prints only 36,000 and calls it "24 x 1500".

**Result.** 24 is the ratio for one of four heavy-cannon archetypes, and 36,000 is the H0/H2 answer
only. The downstream card already knows this; the G2-28 document, which is the source T-14 cites,
does not say it. The ratio also crosses two games' damage scales (a BmAK projectile `Damage` against
a JC3 `ForcePulseSettings.PlayerDamage`), which §8 admits but §5 then uses as if they were one unit.

**Verdict: WEAK.**

## 16. "`DAMAGE_RULES.md` §3.5's missile number is wrong"

**Claim.** MODLOG: "It lists `Batmobile_Missile_*` `Projectile.Damage` = **60**; the package decodes
`Batmobile_Missile_Projectile` = **250** … The 60 is the EMP missile read once and applied to both."

**Test.** Read the file as it stands today:

```
$ sed -n '263,265p' Research/BatmobileGrab/DAMAGE_RULES.md
Read the missiles by name, not by family: `Batmobile_Missile_Projectile` is **250** and
`Batmobile_EMPMissile_Projectile` is **60**; the Joker missile is **250**.
The EMP missile is the outlier on the low side, not a second missile class.
```

and the table it sits under: `…_Missile_Projectile | 250 | 0 | -122`, `…_EMPMissile_Projectile |
60 | 0 | -121`.

**Result.** The correction has been made in the cited file. The finding is true as history and false
as a description of the repository: a reader who follows the pointer today finds 250 and an explicit
warning against exactly the mistake the card reports. Either the card wrote before the fix (it did —
G1's note was edited afterwards) or it did not re-read. `DAMAGE_MODEL.md` should be re-pointed at
the current text.

**Verdict: BROKEN as a live finding** (stale). The underlying value 250 is correct.

## 17. "`damage_audit.py` FAILS on the current build"

**Claim.** MODLOG: "`damage_audit.py` FAILS on the current build. `FAIL bullet_armor_strength:
declared as a switch but 99 is inside the shipped 0..99 … (exit 1, 29 members, 5 outside the shipped
range, 6 declared switches)` … **Not fixed here**".

**Test.** Run it:

```
$ python Tools/scripts/damage_audit.py
member                               build       shipped    donor  verdict
bullet_armor_strength                   99      0..99            0  inside
…
29 members, 5 outside the shipped range, 5 declared switches
check ok
EXIT=0
```

**Result.** It passes. The stale declaration was removed by T-14 on 2026-10-29
(`MODLOG` line 12989, "removes the `bullet_armor_strength: 100` declaration";
`Working/Translation/damage_switches.json` mtime 2026-10-29 02:46, `_t14` note in the file). The
"6 declared switches" is 5 today. As written, the sentence is false; as history it is accurate.

**Verdict: BROKEN as a live finding** (superseded within a day).

## 18. "Part → damage type is UNKNOWN for all three vehicles"

**Claim.** §1 step 1 and §8: "the only `VehicleParts` module in the fleet that decodes: 4 entities,
all the same shared file"; "every other `*_vehicle_parts.vmodc` fails ConvertAdf".

**Test A — the census.** Over 232 caches, `VehicleParts` modules: **4**, entities **4**, all
`monorailflatbed_vehicle_parts.vmodc` (`v5602_train_urga_monorailflatbed_military_{catwalk,
containers,containers_rigidobject,empty}`). No module type containing "Part" other than
`VehicleParts` (53 types seen).

**Test B — do the others still fail?** Re-ran the same binary the project uses, on the donor's own
file and three others:

```
Tools/Gibbed/…ConvertAdf.exe E:/Modding/JustCause3/_grab/probe/sportsmuscle_vehicle_parts.vmodc out.xml
  at …AdfFile.InstanceMemberInfo.PrepareForWritting …
  at …AdfFile.InstanceInfo.GuessInlineArrayCopyPosition …   → no file produced
apc: exceptions=1 produced=0   armoredjeep: exceptions=1 produced=0   assault: exceptions=1 produced=0
```

**Result.** Holds today, and the failure is identical to MODLOG §98's. One wording point: this is a
*tool* limit, not the absence of a carrier — the donor's part map exists and is **attached**
(MODLOG §99a proves the `.epe` references `sportsmuscle_vehicle_parts.vmodc` by Jenkins hash
`5AF592A9`, and `Builds/test-033` holds the archive copy the engine loads). "No carrier exists" would
be wrong; "no tool can open the carrier" is what the data says.

**Verdict: HOLDS** (with that wording corrected).

## 19. 81 cells, 27/27/19 finite

**Claim.** MODLOG done-check: "9 arms x 3 vehicles, models H0, H1, H2, finite H0 27 / H1 27 / H2 19,
never H1 0 / H2 8".

**Test.** Recount from `DAMAGE_MODEL.json`:

```
cells 27 (9 arms × 3 vehicles)   finite {'H0': 27, 'H1': 27, 'H2': 19}
```

**Result.** Exact, including the 8 `never` cells (`H2` absorbed on the 5000@99 bullet channel).
Arithmetic in the tables re-derived by hand for pistol/rifle/shotgun/tank shell/grenade on all three
vehicles from the scalars above; every cell matches `ceil`/pool arithmetic as documented
(e.g. build tank shell H2 = ceil((250+2000)/1500) = 2, H1 = ceil(2000/750) = 3).

**Verdict: HOLDS.**

## 20. What `--check` actually proves

**Claim.** MODLOG: "`python Tools/scripts/damage_predict.py --check` → exit 0 … json match True";
§9 presents `--check` as the reproduction.

**Test.** Read `cmd_check` (line 924ff): it rebuilds the payload, re-renders the markdown, and
compares both byte-for-byte with the files on disk. The tamper test in MODLOG (edit a number →
`FAIL: … stale`) is consistent with that.

**Result.** `--check` proves *the document equals its generator*. It cannot detect a wrong constant
inside the generator, and the generator contains at least two: the 100.0/0 root sentence (§2) and the
`aim` sentence quoting "symptom unrecorded" (§12). A generator check is necessary but not sufficient
evidence; the card presents it as if it were the latter ("Nothing in this file claims a composition
the data does not state").

**Verdict: WEAK** (a self-consistency check described as a correctness check).

---

## What survives, and what the card should say instead

**Survives, reproduced to the value:** the fleet census (§7 of the doc — all 8 channels, all pairs,
exact counts), the donor/tank/build scalars (§3), the six-value build-vs-tank diff, the 23-value
build-vs-donor diff, the one-value part-table edit (§5), the six part-name families (§6), the nine
arm values including `w602` damage 1.0 / AI 20×10 and the shotgun's 8×90×0.2, the 81 cells and their
27/27/19 finite count, the BmAK 1200/50 arithmetic, the `VehicleParts` census, and the "no file maps
a weapon to a channel" negative (now 0/19,458 over 190 tunes).

**Does not survive:**
1. the channel column (§8) — the single input every cell depends on, assigned by judgement and
   self-contradictory between the doc's two tables;
2. the tank shell's 1500-vs-550 choice (§9) — the discriminating probe Q1-DM-A is conditional on it;
3. the H1/H2 bracket (§12) — the project's own in-game record falsifies both for bullets;
4. three stale "findings" (§12 symptom, §16 missile note, §17 audit) that a re-read would have caught.

**Consequences for the cards that follow.** ARM-1's "the gate is out of the shipped domain" is
arithmetically true and practically irrelevant: the gate has shipped at 100 (test-077) and bullets
still killed the car, so no `bullet_armor_strength` value expresses ARM-1. What is left as a carrier
is `max_health` (raising the pool), `invulnerable` (whole-vehicle, kills ARM-2), or the part table
(one flag already edited). Q1-DM-A should be rewritten to print both blast halves (1500/8 m and
550/6 m) and to expect 2/3/2 or 4/8/5; Q1-DM-B's H1/H2 expectations are already refuted by
test-077 and the probe should be re-scoped to the explosion channel, which is the only one with no
in-game datum against it.

**Reproduce.**

```
python Tools/scripts/damage_predict.py --check
python Tools/scripts/jc3_damage_search.py --check
python Tools/scripts/damage_audit.py
# census / diff / part-table comparisons: Tools/scripts/t1_current.py dump + the 232 .ee.json caches
# tune scan: jc3weapons.decode_tune over E:/Modding/JustCause3/_grab/weapons/*/*.wtunec,*.ftunec
```
