# Keep audit — six WLD rows: BmAK behaviour against the donor-derived value

Rows audited: **T-WLD7, T-WLD13, T-WLD14, T-WLD16, T-WLD18, T-WLD19**.
Each row is set out the same way: what BmAK actually does (with the file it is read
from), what the donor's value makes JC3 do, then **LORE-EXACT** or **COMPROMISE** and,
for a compromise, the exact number to change.

Verdicts: **3 LORE-EXACT · 3 COMPROMISE** out of 6 rows.

Per `AGENTS.md`: these are findings and proposals only — no game file is modified.

| row | requirement | verdict | number to change |
|---|---|---|---|
| T-WLD7 | category captions stay correct | **COMPROMISE** (accepted, no write) | `UITypeDescription` 2432797658 / `UIFlagDescription` 1383769868 — replacement key not mintable |
| T-WLD13 | water: the car sinks | **LORE-EXACT** | `will_sink` 1 — keep |
| T-WLD14 | water: stall + entry damage | **COMPROMISE** | `car_common.engine_shut_down_delay_s` **30 → 0** (per-vehicle override) |
| T-WLD16 | cargo plane and boat can carry the car | **COMPROMISE** | plane payload ratio **15.0 % → 24.0 %** (6,000 / 25,000); gate is `CVehicleCargoBay.enabled` = 1 |
| T-WLD18 | no traffic record for the Batmobile | **LORE-EXACT** | 0 records at leaf hash 443190071 — keep |
| T-WLD19 | the donor's own traffic record is left alone | **LORE-EXACT** | donor record at offset 23240 — keep |

---

## T-WLD7 — category captions (`UITypeDescription`, `UIFlagDescription`)

**Requirement.** The Rebel Drop item's category captions stay correct.

### BmAK behaviour

BmAK gives the Batmobile **a category of one**. It is not filed beside anything; it has
its own page in every list that could hold it (`Research/BatmobileGrab/CONFIG.md`):

| evidence | line | value |
|---|---|---|
| `ShowcaseItems` | 279 | `( Page="Batmobiles", Item="Batmobile", Skin="Playable_Batmobile_Std", Levels="Showcase_Ambient_Background\|Showcase_Batm…")` — page **"Batmobiles"**, 3 items |
| `UpgradeHeaders` | 276 | `( Name="PageBatmobile", OX=30.0, OY=-100.0, TX=10.0, TY=-110.0 )` — upgrade page **"PageBatmobile"** |
| `UpgradeItems` | 277 | `( Page="Batmobile", Item="Batmobile", …, Scale=1.1, Icon="Batmobile", … )` — 38 items on that page, icon named `Batmobile` |
| `ChallengeCharacterIds` | 280 | `( Name="Batmobile", Id=100 )` — a character id of its own |

There is **no sports-car category anywhere in BmAK's Batmobile rows**: "sports" does not
appear in any of the four tables, and the vehicle's own icon is literally `"Batmobile"`.

### Donor-derived value

`profile/item.onlinec` carries two caption hashes that name a **shared UI category**, not
this car:

| field | hash | text (11/11 languages) |
|---|---:|---|
| `UITypeDescription` | 2432797658 | `SPORTS CAR` |
| `UIFlagDescription` | 1383769868 | `SPORTS CARS` |

Both resolve in `profile/online.stringlookup`, and both are the *same keys every sports
car in JC3 uses* — they are not per-item strings.

### Test — can a Batmobile caption be minted?

The project's own `StringHelpers.HashJenkins` port (`Tools/scripts/rbmhdr.py:54`) was
checked against two keys whose preimages are known, then asked for these two:

```
hash_jenkins("v0300_car_kensington_sportsmuscle_civilian_01") = 3535039305 = 0xD2B46B49  ✔ (T-WLD4)
hash_jenkins("..._civilian_01_desc")                          = 2073308658 = 0x7B942DF2  ✔ (T-WLD6)
hash_jenkins("SPORTS CAR")                                    = 2949097753  ≠ 2432797658
hash_jenkins("SPORTS CARS")                                   = 2711742874  ≠ 1383769868
560 case/prefix/suffix variants ("$UI.", "ui_", "_desc", "UIType3", …)   0 hits
```

So the **caption key's preimage is not the visible text** and is UNKNOWN: unlike the
leaf-hash and `_desc` conventions (both verified above), a caption key cannot be computed
from the string we want to show. Editing the *text* at those two hashes would instead
relabel **every sports car in the game**.

### Verdict — COMPROMISE (accepted, no write)

The Batmobile will read **SPORTS CAR / SPORTS CARS** in the drop menu and garage. It is
wrong for a 6 t armoured car, and BmAK would have called the page "Batmobiles".

**Exact numbers:** `UITypeDescription` = **2432797658**, `UIFlagDescription` = **1383769868**.
**What to change them to:** nothing we can compute — the replacement key requires the
caption-hash preimage convention, which is UNKNOWN (§U1). The only honest options are
(a) accept the shared caption, or (b) decode the convention first, then mint
`hash_jenkins(<whatever the convention hashes>)` for "BATMOBILE"/"BATMOBILES" and add the
pairs in 11 languages.

---

## T-WLD13 — water: `WaterInteraction.will_sink` + `Buoyancy`

**Requirement.** The Batmobile is not amphibious; it sinks (D-8 = lore).

### BmAK behaviour

BmAK models **water contact, not flotation**. Everything the grab ties to water is a
contact effect:

| evidence | file:line | value |
|---|---|---|
| `BmScript.RVehicleBatmobile.SpawnWaterImpactEffect` / `StopWaterImpactEffect` | `PACKAGES_G305.md:535`, `:677` | 6 tagged properties (5 Struct + 1 Object), the entry/exit pair of the water-impact effect |
| `Engine.Water_Splash` on all four wheel emitters | `MECHANICS.md:594-597`, `:602-609` | listed on `WheelFL/FR/RL/RR` in all four Batmobile builds |
| `Batmobile_Burnout_Water` | `PARTICLES.md:115` | **4** emitters, lifetimes `0.2-0.4`, `0.2-0.4`, `0.2-1`, `1-2` s, spawn 15 / 15 / 500 |
| `Water_Trails_Activated` | `COLOUR_PARAMS.md:108` | block 16 float = **1** (on) |

There is **no sink flag, no buoyancy member, no swim/drown state** in
`RVehicleBatmobileBase`'s class defaults — `CLASS_DEFAULTS.md` matches **0** for
`water`, `sink`, `buoyancy`, `float`, `swim`, `drown`. So what BmAK's Batmobile does
*after* it enters deep water is **UNKNOWN from the grab**; only the spray is decoded.

### Donor-derived value

`WaterInteraction.will_sink` = **1**; `Buoyancy` buoyancy **2.0**, drag **100.0**,
radius **0.55**, side_area **1.85**, bottom_area **3**, up_velocity_cap **20**, with
**1** hull element; test-091's modules are byte-identical to the donor
(`build_check.identical = True`); fleet 189 of 232 sink.

### Verdict — LORE-EXACT

`will_sink` 1 is exactly the D-8 decision, and nothing in BmAK contradicts it (BmAK is
silent, not opposite). **The lore credit belongs to D-8, not to BmAK**: this is a
`keep` that survives because the lore says sink, not because a grab file says sink.

**Number:** `will_sink` = **1** — no change. `Buoyancy` 2.0 is donor-inherited and has
no BmAK counterpart, so it can be neither confirmed nor falsified (U2).

---

## T-WLD14 — water kill/stall constants (`vehicle_common.vmodc`)

**Requirement.** Entering water stalls the engine and damages the hull.

### BmAK behaviour

BmAK has **no water damage or stall member at all**: `CLASS_DEFAULTS.md` carries 0
water-named floats, and the impact/stall machinery in `DAMAGE_RULES.md` §3.3 is ram and
weapon damage only (speed bands, `ImpactMaxDamage`, strafe/boost mods). The only
water-facing behaviour decoded is the spray of T-WLD13.

So BmAK's stall timing is **UNKNOWN**. The row's justification is D-8 ("stall"), which is
a design decision.

### Donor-derived value

`editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc`, on **232/232**
entities, 0 per-vehicle overrides:

| key | value |
|---|---:|
| `vehicle_damage.min_water_entry_ms` | 10 |
| `vehicle_damage.fatal_water_entry_ms` | 20 |
| `vehicle_damage.min_water_entry_floating_ms` | 20 |
| `vehicle_damage.fatal_water_entry_floating_ms` | 50 |
| `car_common.engine_shut_down_delay_s` | **30** (boat / helicopter / plane / motorbike: 5) |

The row promises *"the engine dies on water entry, not on the first wave"*. With
`engine_shut_down_delay_s` 30 the engine keeps running for **30 s** after the entry —
it dies half a minute later, neither on entry nor on a wave. The `_ms` unit is also
UNKNOWN (card T-20 A13: 10 **ms** is implausible as an entry threshold; metres/second is
at least as likely), so the 10/20/20/50 pair may not be a timer at all.

### Verdict — COMPROMISE

**Exact number to change:** `car_common.engine_shut_down_delay_s` **30 → 0** (immediate
stall; use **5** if 0 is treated as "disable the timer"). Write it as a **per-vehicle
override in the Batmobile's own module**, not in `vehicle_common.vmodc`: R7 forbids
editing the shared file in place, and the fleet ships **0** overrides, so the override
mechanism itself is unproven (U4).
Leave 10/20/20/50 alone until the `_ms` unit is measured — changing a speed threshold as
if it were a timer would be a second error.

---

## T-WLD16 — cargo bay capacity

**Requirement.** The cargo plane and the transport boat can carry the car.

### BmAK behaviour

BmAK does have an airlift, and it is **not** a cargo bay: the Batmobile is carried
**vertically by the Batwing Carrier** (`Research/BatmobileGrab/ANIMATIONS.md`):

| anim | frames | seconds | tracks that move |
|---|---:|---:|---|
| `Batwing_Rescue_01` | 149 | **4.933** | `Batwing_Carrier` 26170.43 cm / 180.00°, `Batwing_Carrier_Door_L/R` 110.00° |
| `Batmobile_Vertical_Rescue_In` | 218 | **7.233** | `Batwing_Carrier` 36499.69 cm; door L/R |
| `Batmobile_Vertical_Rescue_Idle` | 113 | **3.733** | `Batwing_Carrier` 24.90 cm (hover hold) |
| `Batmobile_Vertical_Rescue_Out` | 133 | **4.400** | `Batwing_Carrier` 36480.46 cm / 7.07° |

AnimSet `Batwing_Rescue` (484 objects) is Joker-build content, and the carrier is a
**dedicated clamp-and-lift rig** with doors — not a flatbed with a mass limit. No mass gate
appears anywhere in the sequence.

### Donor-derived value

**12** `CVehicleCargoBay` objects on **12** entities: 4 boats `v1602_boat_urga_transport`
(mass **100,000**), 6 planes `v4603_plane_urga_cargotransport` (masses **25,000 and
40,000** — two bodies), 2 flatbeds `v5602_train_urga_monorailflatbed` (**15,000**).
The bay's 7 members are `_object_id, disable, enable, enabled, name, name_hash, world` —
**no capacity, mass or class field**; `enabled` = 1 on all 12; `enable`/`disable` events
are empty on all 12.

The row's ratios are 6,000 / 40,000 = 15.0 % (plane), / 100,000 = 6.0 % (boat),
/ 15,000 = 40.0 % (flatbed). The plane's **heavier** body was used, which hides the
other reading: 6,000 / 25,000 = **24.0 %**.

### Verdict — COMPROMISE

**Exact number to change:** the plane ratio **15.0 % → 24.0 %** (6,000 / 25,000); 6.0 %
and 40.0 % are arithmetic-correct and stay. The **gate that actually decides** carrying is
`CVehicleCargoBay.enabled` = **1** on the carrier's bay — there is no capacity number to
set, and the attach rule for a cloned bay is UNKNOWN (all 12 shipped bays have empty
enable/disable events).

---

## T-WLD18 — traffic record for the new leaf

**Requirement.** No traffic record exists for the Batmobile, so no NPC drives one.

### BmAK behaviour

The Batmobile is a **unique player vehicle**: its own showcase page ("Batmobiles",
`CONFIG.md:279`), its own upgrade page ("PageBatmobile", `:276`), and its own character id
`( Name="Batmobile", Id=100 )` (`:280`). No BmAK table puts it in an ambient NPC pool —
there is no traffic table in the grab at all.

### Donor-derived value

`settings/spawn_vehicle_defs.bin`, **27,513 B**, **86 records**; the key is the **leaf
hash**, not the path (card T-20 A4: `name_hash D2B46B49` 1 hit at offset **896**,
`path_hash` **0** hits in the whole file, all 86 record hashes at a 12-byte stride,
max offset **1,064**). The new leaf `v0300_car_kensington_sportsmuscle_batmobile` hashes to
**443190071** = `0x1A6A8B37`, present **0** times little-endian and **0** times as ASCII.

### Verdict — LORE-EXACT

0 records is right: a lone Batmobile cannot be ambient traffic.

**Number:** 0 records at hash **443190071** — no change. One wording correction: the row
says the table *"keys on the full path string"*; it keys on the **leaf hash**, and the
path is payload. The `keep` decision is unaffected.

---

## T-WLD19 — the donor's own traffic record

**Requirement.** The donor's record is left alone, so the mod does not replace the donor
leaf and spawn NPC Batmobiles.

### BmAK behaviour

BmAK has no equivalent: there is no Serpente and no ambient civilian pool in the grab.
BmAK is **silent**, so this row cannot be judged against BmAK behaviour — it is judged
against the lore rule "no NPC Batmobiles".

### Donor-derived value

Donor record at offset **23240**, **13** tags
(`vehicle, ground, car, civilian, racing, modern, muscle, kensington, sports, unarmed,
unarmored, ambient, liberated`), satisfying **1 of 41** selectors →
`03_CivilianCarLiberatedProvince`. Leaving it untouched means Serpentes keep cruising in
liberated provinces — JC3's own civilian fleet, which no Batman lore speaks against.

Provenance caveat: the "41" is **asserted, not derived** — `t15_world.py:644` fails if the
count is not 41, and the population comes from a token regex over `global.blo`, not from a
decoded rule table (card T-20 A4, WEAK).

### Verdict — LORE-EXACT

Replacing the donor leaf is what the row forbids, and the record is untouched.

**Number:** offset **23240**, 13 tags, 1 selector — no change. Treat "41" as a pinned
heuristic, not evidence (U6).

---

## UNKNOWNs opened by this audit

| # | question | route |
|---|---|---|
| U1 | what string does the caption hash 2432797658 hash? (560 prefixes/suffixes tested, 0 hits, while the leaf and `_desc` conventions verify) | read the frontend `.gfx` that requests the caption by id; or diff `ui_localization.stringlookup` neighbours |
| U2 | does BmAK's Batmobile sink? Only spray is decoded (0 water members in the class defaults) | watch a deep-water entry in BmAK, or read the native `SpawnWaterImpactEffect` caller |
| U3 | does BmAK stall its engine in water, and after how long? | same watch test; no member exists in the grab |
| U4 | is a per-vehicle override of a `vehicle_common.vmodc` key even possible? The fleet ships 0 overrides and R7 forbids editing the shared file | clone the key into the Batmobile's own module and read it back at runtime |
| U5 | what is the attach rule for a `CVehicleCargoBay`? `enable`/`disable` are empty on all 12 | Q-3 #5 airlift probe |
| U6 | what does "41 selectors" count? Asserted in `t15_world.py:644`, not derived | decode `global.blo`'s selector table |
| U7 | is `min_water_entry_ms` milliseconds or metres/second? 10 ms is implausible; `_s` is spelled elsewhere in the same module | measure the entry speed at which damage starts |

---

## Change record

- **Intended change:** none to game data. Findings and numbers only.
- **File written:** `tmp/freebuff/reports/keep-audit-world-modes-wld.md`.
- **Why this file:** the request names it as the deliverable.
- **Revert:** delete the file. Nothing else was touched.
