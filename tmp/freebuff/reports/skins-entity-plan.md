# Skins as extra Rebel Drop entries (D-5): per-skin entity plan

**STATUS: done (report only).** No build tree, `.ee`, `.epe`, parts module, Rebel Drop table, ledger row or
queue brief was written or edited; nothing was launched.

**Provenance / revert.** New file `tmp/freebuff/reports/skins-entity-plan.md`
(= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/skins-entity-plan.md`). **Revert = delete this file.**

Labels: **decoded** (file:line / field), **derived** (rule + inputs), **UNKNOWN** (tried, where it would be).

---

## 0. The plan in ten lines

| question | answer |
|---|---|
| is a skin a tint? | **no** — V2 vs Joker: **61** materials and **54** textures differ, **5** sockets, **40** bones; MK2 has its **own 4 materials and 5 textures** (`VARIANTS.md` §1-§4) |
| what a skin entity must carry | its own skin mesh (or the same mesh re-skinned), its material set, its texture set, its socket list, its own parts module; **physics is shared** (`RVehicleSimBatmobile` identical in all four, 0 differing tags) |
| the model wall | **4,915 KB hard** (`settings/asset_memory_budgets.bin`, Vehicle-HD Model `[4096, 4915]`), base car at **4,791.3 KB** → **123.7 KB** left |
| the texture wall | **7,065 KB hard** (Vehicle-HD Texture `[6144, 7065]`); RC4 bound **5,380.9 KB** (33 `.ddsc`) → 1,684.1 KB to the hard wall, but **over** the self-imposed 4,648 fitted cap by 732.9 (`NEW-APP-8`) |
| per entity or global | what the cap counts is **bound, non-vanilla resident bytes of the spawned vehicle's parts module** (`bm_budget.py`, calibrated on renders); whether two modded vehicles resident at once **stack** is **UNKNOWN** — no test spawned two |
| skin model, derived | MK2 **≈ 4,755 KB** (margin ≈ 160 KB), Joker/Funhouse **≈ 4,886 KB** (margin ≈ **29 KB**) — face-ratio estimate only; must be measured |
| skin textures | **UNKNOWN KB**: the extra sets are named (5 / 31 / 24) but no `.ddsc` size was measured for them; measure with `tex_bytes()`/`tex2ddsc` |
| Rebel Drop | one 128-byte `Item` per skin, `Name` = `hash_jenkins(<leaf>)`, free `UIDisplayOrder` 12, 13, 14; **each needs its own vanilla leaf** because D-6 (new path) is disproven in game |
| the alternative | spawn through the native hook (entity path in hand) — removes the leaf-per-skin limit, but the spawn call and path resolution are **UNKNOWN** (`9101`) |
| verdict on D-5 | **feasible**, but Joker/Funhouse have almost no model margin and are gameplay-different (Joker has 5 gadgets, not 10) |

---

## 1. What differs from the base car, per skin (decoded: `VARIANTS.md`)

Reference = V2, `Playable_Batmobile_SF`, `Batmobile` (3,905 B), 5,490 records.

### 1.1 Mesh and rig

| | V2 | MK2 | Joker | Funhouse |
|---|---|---|---|---|
| skin mesh | `Batmobile_V2` | `Batmobile_MK2_Skin` | `Batmobile_Jokerfied_Skin` | `Batmobile_Jokerfied_Skin` (**same export**) |
| verts | 201,338 | 199,628 | 202,795 | 202,795 |
| LOD0 / LOD1 / LOD2 faces | 299,837 / 144,857 / 21,720 | 297,566 / 115,056 / 21,242 (**−0.76 % LOD0, −20.6 % LOD1**) | 305,786 / 117,897 / 21,407 (**+1.98 %**) | same as Joker |
| bones | **180** | **175** | **220** | **220** |
| materials on the mesh | 19 | 19 | 20 | 20 |
| bounds (cm) | 702.560 × 349.530 × 234.185 | 702.539 × 349.487 × 234.185 | 713.804 × 349.156 × 233.900 (**11.2 cm wider**) | same as Joker |
| export (B) | 20,151,210 | 20,034,142 | 20,385,512 | 20,385,512 |

Shared side-meshes (`Batmobile_V3_Destroyed` 36,513 faces / 1 material; `Batmobile_V2_Fire` 1,196 / 1;
`Batwing_Carrier` 14,508 / 3 — Joker only).

**Rig consequence:** BmAK's 175/180/220-bone skeletons do **not** transfer to the JC3 car, which is a set of
rigid parts on one 180-bone chassis rig (`BONES.md`). A skin therefore delivers **geometry + materials +
textures**, and has to be re-cut into the same part set as the base build
(`Working/Appearance/build_parts/parts_manifest.json`, 16 entries), not carried as a skeleton.

### 1.2 Sockets

| | V2 | MK2 | Joker | Funhouse |
|---|---:|---:|---:|---:|
| count | 65 | **55** | 64 | 63 |
| only here | — | — | `BatmobileAttach`, `HydraSocket` | `HydraSocket` |
| missing vs V2 | — | `BrakeTrailL/R`, `Dashboard_Light`, `Headlight_Centre`, `LWheelLight` (+`_bottom`, `_top`), `RWheelLight` (+`_bottom`, `_top`) — **10** | `Dashboard_Light`, `Headlight_Centre`, `PassengerNoiseOrigin` | same 3 as Joker |

**Build consequence:** the base build's lamp/emitter sockets must be preserved per skin. MK2 needs its 10
missing sockets re-authored or the lamp rig loses the wheel lights and brake trails; Joker/Funhouse lose the
dashboard light and the passenger noise origin.

### 1.3 Materials and textures

| | V2 | MK2 | Joker | Funhouse |
|---|---:|---:|---:|---:|
| materials | 78 | **80** (+4 / −2) | **69** (+26 / −35) | **84** (+13 / −7) |
| textures | 92 | **95** (+5 / −2) | **100** (+31 / −23) | **102** (+24 / −14) |

* **MK2** adds `Batmobile_MK2_Body_MIC`, `Batmobile_MK2_WheelArch_MAT`,
  `Batmobile_MK2_WheelArchs_MIC_INST`, `Batmobile_MK2_Wheel_INST`; drops `BatmobileV3_Wheel_V2_MIC` and
  `Batmobile_V3_Mainbody_NEW_MIC`. Its 5 new textures: `Batmobile_MK2_Body2_D`, `_Body2_R`,
  `_WheelArch2_D`, `_WheelArch2_R`, `_Wheel_MK2_D`.
* **Joker** adds 26 materials (the Jokerfied body/gloves/hair/teeth/shoes family plus `Batwing_Carrier_*`,
  `Hydra_Trails_*`, `Game_Cameo_Squirting_FLOWER_MAT`) and **drops 35** — including the whole EMP, sonar,
  winch, drone-hacker and power-cell set. Its 31 new textures are the Jokerfied body/tyre/arch maps plus
  Batwing and hair/teeth/trousers sets.
* **Funhouse** = Joker's skin with the **13 Jokerfied materials only** (it lacks Joker's Batwing/Hydra/dust
  set) and **24 Jokerfied textures** (it lacks Joker's 7 Batwing/core-mask/contrail maps).

### 1.4 Lights

| | V2 | MK2 | Joker | Funhouse |
|---|---|---|---|---|
| light-rig rows | 28 | 28 (identical bones/`Type`/`MaterialType`) | **17** (first 16 of V2's rows, then `Dashboard`/`VEHLT_Interior` instead of `BootLight`), **0 of 17 carry a `MaterialType`** (V2: 18 of 28) | 28 (identical) |
| `InteriorLightsSwitchedOn` | `1` | `1` | **absent** | `1` |

### 1.5 Gameplay differences that a "skin" must not pretend to be

| | V2 | MK2 | Joker | Funhouse |
|---|---|---|---|---|
| gadgets / projectiles | 10 / 8 | 10 / 8 | **5 / 2** (own `Batmobile_JokerCannon_V2`, `JokerHeavy_Cannon`, `JokerMissile_Launcher`; **no EMP, sonar, tracker, winch, drone hacker**) | 10 / 8 |
| `VEH_Player` ref @0x12BC | `Batmobile` | `Batmobile_MK2` | `Batmobile_Joker` | **`Batmobile_MK2`** |
| weapon values | — | identical | identical (shared objects: 0 of 1065 comparisons differ) | identical |

**Consequence for D-5:** MK2 and Funhouse are true reskins of the same car (same 10 gadgets, same 28 light
rows, same sim). **Joker is a different vehicle** — 5 gadgets, no EMP/sonar/tracker/winch/hacker, a threat
component, a 17-row light rig with no material binding. Shipping it as a "skin" of our build would either
strip our weapons (lore-wrong: the Joker Batmobile is a different car) or hand it our weapons (asset-wrong).
Recommendation: MK2 + Funhouse are skins; **Joker is a separate vehicle decision**, not a skin.

---

## 2. The budget walls, and what they count

### 2.1 The walls (decoded)

`settings/asset_memory_budgets.bin` — vanilla, 3,104 B RTPC, no patch override; converted to
`Research/Budgets/vanilla_budgets.xml`; `[soft, hard]` KB (`MODLOG.md` §76):

| class | Model | Texture |
|---|---|---|
| **Vehicle-HD** | **[4096, 4915]** | **[6144, 7065]** |
| Vehicle-LD | [10240, 11059] | [12228, 13414] |

The UE modpack raises **only the hard** numbers (Model → 78,640, Texture → 113,040), which is what proves the
second value is the cap. R9 gate = Model ≤ 4,915 KB, Texture ≤ 7,065 KB (`Working/Roadmap/appearance.md`
V-01).

### 2.2 What is actually counted (decoded + calibrated)

`Tools/scripts/bm_budget.py` docstring: *"every mesh a part's `.lod` reaches, MINUS meshes byte-identical to
the vanilla Serpente's"*. Calibration on builds that rendered:

| build | non-vanilla bound KB | outcome |
|---|---:|---|
| test-065 | 3,757.5 | rendered |
| test-081 | 4,091.5 | rendered |
| test-085 / test-091 | 4,657.6 | rendered (despite 6,132–7,032 KB *reachable* incl. vanilla) |
| test-091 resident-but-unbound `.rbm` | 8,456 | rendered — **unbound bytes do not count** |
| test-064 textures | 22,085 | **whole entity vanished** (render *and* collision) |

Vanilla resident baseline: **1,901 KB textures / 4,328 KB models**. That is why the fitted cap is
`(7,065 − 1,901) × 0.9 = 4,648 KB` — the new car adds to a pool that already holds the vanilla residency.

### 2.3 Per entity or global? — the honest answer

| evidence | what it supports |
|---|---|
| a build over the cap makes **that entity** vanish; under the cap it renders (test-064 → test-065) | the budget is checked against the **loaded set of the spawned vehicle** |
| `bm_budget.py` measures **one** parts module's bound meshes | the unit of measure is **per vehicle entity** |
| vanilla resident (1,901 / 4,328) is subtracted from the cap before fitting | the cap is a **shared residency pool**, not a private per-file allowance |
| BmAK ships four skin packages, each with its own mesh/materials/textures, and they coexist in one game | a per-variant resident set is normal in the source game (BmAK evidence, **not** JC3) |

**Verdict:** the cap is **per resident vehicle set**, and the "per entity" reading is only true while one
modded vehicle is resident. Whether **two** modded Batmobiles resident at the same time each get 4,915 KB or
share one pool has **never been tested** → **UNKNOWN** (Q-probe: spawn base + one skin, watch which vanishes).
This matters directly for D-5: if the pool is shared, summoning a skin next to the base car costs both.

### 2.4 The base car's position (decoded)

| axis | value | margin to hard wall |
|---|---:|---:|
| Model | **4,791.3 KB** of 4,915 (`RC4` R9 gate, 16 far LODs trimmed from 5,972.9) | **123.7 KB (2.5 %)** |
| Texture | **5,380.9 KB** (33 `.ddsc`) per `V-01-RC2`; RC4 `budget.json` also prints 5,380.9 | **1,684.1 KB** to 7,065 |
| Texture vs the fitted cap 4,648 | 5,380.9 | **over by 732.9 KB** — the `NEW-APP-8` inconsistency (another file says 4,015.5) |

### 2.5 Per-skin budget (**derived** estimate, must be measured)

No skin `.rbm` set has been extracted, so the numbers below scale the base by LOD0 face ratio and assume the
same far-LOD trim. They are **estimates**, not measurements:

| skin | LOD0 ratio vs V2 | estimated model KB | margin to 4,915 | notes |
|---|---:|---:|---:|---|
| MK2 | 0.9924 | **≈ 4,755** | ≈ **160** | 10 fewer bones, LOD1 20.6 % lighter → the cheapest skin |
| Joker | 1.0198 | **≈ 4,886** | ≈ **29** | 220 bones, 11.2 cm wider; **any added lamp/FX mesh blows the wall** |
| Funhouse | 1.0198 | **≈ 4,886** | ≈ **29** | same mesh as Joker |

Texture side: **UNKNOWN KB per skin**, because the extra sets are named but unsized. What is known: the
counts are **+5 (MK2) / +31 (Joker) / +24 (Funhouse)** on top of V2's 92, and RC4 already binds 33 of the
base's. Measure with `tex_bytes()` (same scaling as `tex2ddsc.mip_chain`) before any build is scheduled;
at 1024² a single D map is hundreds of KB, so Joker's 31 extras cannot fit under 1,684 KB without
downsizing.

**Build rule that follows:** MK2 can be built at base fidelity; Joker/Funhouse must either
(a) drop to the base car's already-trimmed LOD set and reuse shared materials, (b) ship a texture tail
(downsize `*_D` to 512, `*_N/_R` to 256 — the same `allocate_caps` ladder RC4 used), or (c) be **one
entity with a material swap** (see §5).

---

## 3. The Rebel Drop entry recipe, per skin

From `REBELDROP.md` §7 (128-byte `Item`, stride proven by the string pointer, not the hash read):

1. **Leaf name** of the entity to spawn: `Name` binds by hash of that leaf.
2. **`Name` = `hash_jenkins(<leaf>)`** (32-bit). Example in the doc:
   `hash_jenkins("v0300_car_kensington_sportsmuscle_batmobile") = 443190071 = 0x1A6A8B37`. **But** that leaf
   is unregistered and D-6 is disproven in game (`Working/Roadmap/damage_world.md` §0.1: *"A NEW entity path
   does not spawn, whatever its content"*), so RC4 hijacks the traffic-free vanilla leaf
   `v0300_car_kensington_sportsmuscle_debug` (hash **1621485476**).
3. **One `Item` per skin**, every field from the donor row except the identity/UI ones:

| field | base car (RC4) | MK2 | Joker | Funhouse |
|---|---|---|---|---|
| `Name` | `hash_jenkins(<leaf>)` | `hash_jenkins(<MK2 leaf>)` | `hash_jenkins(<Joker leaf>)` | `hash_jenkins(<Funhouse leaf>)` |
| `BaseName` | donor `276735921` (meaning UNKNOWN) | same | same | same |
| `DlcId` | `0` | 0 | 0 | 0 |
| `Type` / `UIType` | `1` / `3` | 1 / 3 | 1 / 3 | 1 / 3 |
| `Purchasable` / `Consumable` / `Collectable` / `MaxInventory` / `Region` | `0` | 0 | 0 | 0 |
| `Rewardable` | `1` | 1 | 1 | 1 |
| `Feats` | empty | empty | empty | empty |
| `RebelDropTimer` | `1800` donor, mod uses `0` | 0 or 1800 | 0 or 1800 | 0 or 1800 |
| `UIFlag` | donor `5` (mod uses 3) | 5 | 5 | 5 |
| **`UIDisplayOrder`** | **12** (vanilla max 11; 12 slots free) | **13** | **14** | **15** |
| `UIName` | = `Name` | = `Name` (or a shared display key; 27/45 mod entries do) | | |
| `UIDescription` / `UITypeDescription` / `UIFlagDescription` | donor hashes `2073308658` / `2432797658` / `1383769868` | same or per-skin | | |
| `UIImagePath` / `UIVideoPath` | the leaf name | leaf | leaf | leaf |
| `UIPar0..4` | `0.83 / 0.4 / 0.45 / 0.09 / 0` | donor | donor | donor |

4. **Array mechanics:** append to `Items[]`, bump the count, write the two strings into the string area
   (`stride` 128, `strings_start` = block end).
5. **Unlock:** vanilla gates the donor through task `1361701860` (type 19, permanent 1, delivery 0, qty 1).
   The mod's 45 added entries carry **no reward** and work; whether "no reward" is the rule is **UNKNOWN**
   (Q-1 probe).

**The hard limit for D-5:** one hijacked leaf = one entity, so the three skins need **three more unregistered,
traffic-free vanilla leaves** — the same hunt RC4 did once. If only the `_debug` leaf is safe, D-5 cannot be
three entries; it is then either one entry + material swap (§5) or the hook route (§4).

---

## 4. The runtime alternative: spawn through the native hook

| step | what it needs | status |
|---|---|---|
| 1. resolve the entity path at runtime | the entity root/path API (`9101` decodes the roots and slots) | **queued**, not done |
| 2. call the spawn | a spawn/streaming callable that takes a path — the same consumer whose absence breaks D-6 | **UNKNOWN** (no decoded call site; the D-6 failure is behavioural evidence that the *data* route is closed, not that a code route is) |
| 3. hand the vehicle to the Rebel Drop menu | a table entry is still needed for UI, unless the menu is bypassed and the car is spawned directly | **UNKNOWN** |
| 4. leave the vanilla leaf alone | eliminates the leaf-per-skin limit entirely | — |

**Why it is worth keeping on the table:** it is the only route that scales past the number of hijackable
leaves, and it also solves the "second leaf" problem for the battle-mode variant (`9130`). It does **not**
remove the budget question (§2.3) — a spawned second vehicle is still resident.

---

## 5. The cheapest lore-faithful alternative (no new leaves)

**One entity, per-skin material instances + texture tail + a mesh variant per build.** BmAK's own evidence
supports the reverse (four packages, four archetypes), but JC3's `MaterialInstanceConstant` path is already
how RC4 carries 19 slots — so a *skins switch* inside one entity is possible in principle (swapping the
`.lod` of the body parts and the paint MIC). That keeps one leaf, one budget, and one physics body. Its cost:
the skin meshes must still be cut into the same 16 parts, and Joker's 40 extra bones / 11.2 cm width mean it
is **not** a pure swap (a new mesh, not just a new texture).

This is an option, not the recommendation: D-5 says "extra Rebel Drop entries", and §3 shows the limit is
leaves, not data.

---

## 6. Ledger rows and cards touched

| record | effect |
|---|---|
| **D-5** (skins as extra entries) | this report is its input; feasibility: MK2 yes, Funhouse yes at zero margin, **Joker no (different vehicle)** |
| **D-6** / `T-WLD1`, `T-WLD4`, `T-WLD6` | unchanged, but they need the leaf-per-skin consequence stated: each entry needs its own hijacked vanilla leaf |
| **`NEW-APP-21`** (skin entity clone) | its "budget per entity or global = UNKNOWN" is now **narrowed**: per resident set, pooling **UNKNOWN** (§2.3) |
| **`NEW-APP-7`** (budget ledger) | must include the skin column: MK2 ≈ +0 KB over base (same trim), Joker/Funhouse ≈ +95 KB over base by face ratio, and the texture tail |
| **`NEW-APP-8`** (texture figure reconciliation) | unchanged; this report cannot resolve 5,380.9 vs 4,015.5 vs 5,855.8 |
| **`V-01`** gate | a skin branch must pass Model ≤ 4,915 / Texture ≤ 7,065 on its own |

**COMPROMISES: none taken.** The plan does not accept a wrong number anywhere; where a number is missing
(skin texture KB, per-pool stacking) it is marked UNKNOWN with the tool that would measure it.

---

## 7. UNKNOWNs

| # | unknown | what was tried | settler |
|---|---|---|---|
| U1 | skin **texture** KB (5 / 31 / 24 new maps) | `VARIANTS.md` lists names only; no `.ddsc` measured for skins | `tex_bytes()` / `tex2ddsc` over the skin texture set |
| U2 | skin **model** KB (the ≈4,755 / 4,886 figures are face-ratio estimates) | no skin `.rbm` tree extracted | `bm_budget.py` on a skin build tree |
| U3 | does a second resident modded vehicle **share** the 4,915/7,065 pool | every calibration used one vehicle; test-064/065 one variable | spawn base + skin together (Q-probe) |
| U4 | how many vanilla leaves are hijackable | RC4 proved the `_debug` leaf; the fleet has 233 vehicles with 158 registered (`G2-27`) | the leaf-hunt pass already used for RC4 |
| U5 | whether a hook spawn exists and what it takes | D-6 disproves the data path; no spawn call decoded | `9101` (entity roots/slots), then a call-site hunt |
| U6 | whether "no task reward" is what makes an added entry available | mod's 45 added entries behave so; not decoded | Q-1 probe |
| U7 | Joker's unnamed floats (9 values) and tag mapping | `VARIANTS.md` §6 flags them UNKNOWN | not needed for D-5 |
