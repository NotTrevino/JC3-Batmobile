# Recount: the pulse numbers in `force-pulse-as-boost-and-shove-carrier-plan.md`, against `FORCEPULSE.json`

**Provenance / reversibility.** New file, `tmp/freebuff/reports/force-pulse-carrier-recount.md`
= `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/force-pulse-carrier-recount.md`. Intended change:
add one recount; **the plan file is read and left unchanged** (not edited, not reformatted), and no
other file is written. It is the correct file because it is the requested output path and the only
job artefact. Revert = delete this file.

Primary source: `Research/JC3Grab/FORCEPULSE.json` (27,992 lines, 761,684 B), counted key by key.
Reference for the three headline numbers: the G2-17 row, `GRAB_BACKLOG.md:1839` ("307 pulses in all
232 vehicle `.ee` / 79 chassis … **31 members**"). Line numbers below are absolute in the file named;
every count was recomputed from the JSON, not copied from `FORCEPULSE.md`.

---

## 0. Result

- **Pulses, chassis, members — all three match**, from unambiguous JSON keys:

| number | G2-17 row | plan | JSON key counted | JSON value | verdict |
|---|---:|---:|---|---:|---|
| pulses | 307 | 307 (plan:10, 33, 85, 195, 222, 279, 396) | `census.objects`; also `totals.objects` and `sum(len(e["pulses"]) for e in entities)` | 307 | **MATCHED** |
| chassis | 79 | 79 (plan:33) | `census.chassis` (and `totals.chassis`) | 79 | **MATCHED** |
| members | 31 | 31 (plan:33, 85; 5 named + 26 hashed) | `len(members)`; and `members[].kind` | 31 = 5 `named` + 26 `hashed` | **MATCHED** |

- The plan quotes **28 figures** in all. **23 match**, **5 differ** (§2), and **1 name** cannot be
  pinned to the JSON (§UNKNOWN). The 3 headline numbers are all matches, so the score on the rest is
  20 matched / 5 differing of 25.
- The differing ones are worth fixing; two are load-bearing for the plan's argument
  (the owner-class table at plan:283–285 omits `CMotorBike` 19, and plan:65 calls six matrices
  "non-identity" when the JSON has six **distinct** matrices of which five are non-identity):
  §2.3 and §2.2.

---

## 1. What was counted, and how

The JSON is a complete census of `CForcePulse` objects: 232 `entities`, each with a `pulses` list,
plus the aggregates `census`, `totals`, `members`, `tunes`, `owners`, `positions`, `ranges`,
`unowned`, `names`. Every figure below names the key (or the recomputation over
`entities[].pulses[]`) it came from. No count was taken from `FORCEPULSE.md`, and none from the plan.

Recomputation used for cross-checking (read-only, **no file written**):

```
$ PYTHONIOENCODING=utf-8 python -   # json.load('Research/JC3Grab/FORCEPULSE.json')
pulses by entities: 307 | census.objects 307 | entities 232 | chassis 79
named: 5 hashed: 26 total 31
tunes: 23, len(tunes[i]['values']) == 8 for all 23, all 'consistent': true
positions: {'(0.0, 0.0, 0.0)': 292, '(0.0129, 0.5109, 0.0)': 10, '(0.0, 0.2613, 5.5002)': 2,
            '(0.0, 2.0356, 0.6992)': 1, '(0.0, 4.8101, 0.0)': 1, '(-9.616, -2.3759, -4.2695)': 1}
world: 6 distinct values; identity on 292 pulses; non-identity on 15 pulses
owners sum: 307   unowned: 14   other_refs: 1
```

---

## 2. Every number the plan quotes

### 2.1 The census numbers (pulses, entities, chassis, members)

| # | figure | plan line(s) | JSON key | counted | verdict |
|---|---|---|---:|---|---|
| 1 | **307** pulses | 10, 33, 85, 195, 222, 279, 396 | `census.objects` / `totals.objects` / Σ `entities[].pulses` | 307 / 307 / 307 | **MATCHED** |
| 2 | **232** vehicle `.ee` | 33 | `census.entities` / `totals.entities_with_pulses` / `len(entities)` | 232 / 232 / 232 | **MATCHED** |
| 3 | **79** chassis | 33 | `census.chassis` / `totals.chassis` | 79 / 79 | **MATCHED** |
| 4 | **31** members | 33, 85 | `len(members)` | 31 | **MATCHED** |
| 5 | **5** named / **26** hashed | 33 | `members[].kind` | 5 / 26 (named: `SettingsFile`, `_object_id`, `name`, `name_hash`, `world`) | **MATCHED** |
| 6 | **eight** numbers per tune | 36, 85 | `len(tunes[i]["values"])` | 8 on 23/23 tunes | **MATCHED** |
| 7 | **23** tunes | 53, 85 | `len(tunes)`; `members[SettingsFile].distinct` | 23 / 23 | **MATCHED** |
| 8 | **292** of 307 at the entity origin | 62, 222–223 | `positions["(0.0, 0.0, 0.0)"]`; identity `world` | 292 / 292 | **MATCHED** |
| 9 | the 14 origin exceptions (EMP, 2 cargo, 1 barrel, 10 at `(0.0129,0.5109,0)`) | 63–65 | `positions` (6 keys) | **15** exceptions — see §2.1a | **DIFFERS** |
| 10 | **293** of 307 carried by an owner | 279 | 307 − `owners["(none)"]`; `totals.other_refs` | 293; 1 | **MATCHED** |
| 11 | **14** unowned = 10 barrel + 2 cargo + EMP + mm340 | 320 (§4.1) | `len(unowned)` | 14, composition exact | **MATCHED** |

**2.1a — the origin exceptions (plan:63–65).** `positions` has six keys summing to 307, so the
exceptions to "origin" are **15**, not 14. The plan names the EMP (1), two cargo (2), "a barrel" (1)
and ten at `(0.0129, 0.5109, 0)` (10) = 14. The unlisted fifteenth is one pulse at
`(0.0, 4.8101, 0.0)`: `v4603_plane_urga_cargotransport_military_cargo_tank.ee`, pulse
`w602_mediumtank_canon`, parent `None`, tune `w602_mediumtank_canon.ftune`, owner
`CBulletWeaponBase` (`entities[].pulses[].xyz` / `.name` / `.owners`). Two separate points:

- a count difference — 15 exceptions, not 14;
- an attribution difference — the pulse at `(-9.616, -2.3759, -4.2695)` is **not a barrel**. It is
  `explosion_force_pulse` on `v4603_plane_urga_cargotransport_mm340.ee`, parent `CVehicleRule`, tune
  `w704_m488.ftune` — the mm340 rule pulse the plan itself describes in §4.2. The ten
  `barrel_explosion.ftune` pulses are all at `(0.0129, 0.5109, 0)` (10 of the 14 `unowned` entries).

### 2.2 The matrix count (plan:65)

> "Six matrices are non-identity and carry rotation + translation only (columns are unit length …)"

`members[world].distinct` = **6**, and those six values cover 307 pulses as:
identity **292**, `(0.0129,0.5109,0)` translation 10, `(0,2.0356,0.6992)` 1, `(0,0.2613,5.5002)` 2,
`(0,4.8101,0)` with a 180° y-rotation 1, `(-9.616,…)` with an oblique rotation 1.

So: **six distinct**, **five non-identity** (15 pulses), and of those five, **three carry no rotation
at all** (pure translation) and **two carry rotation**. The plan's sentence is wrong in both halves —
it should read "six distinct matrices, one of them identity; five non-identity, two of which carry
rotation". The plan's later use of this fact ("the matrices are rotation-only, so at unit scale the
two agree", plan:71–73) survives: no pulse scales, and only two matrices rotate at all.

### 2.3 The owner-class table (plan:283–285)

| plan row | plan value | `owners` key | verdict |
|---|---|---:|---|
| `CCar` | 126 | `owners["CCar"]` = 126 | **MATCHED** |
| `CBoat` | 35 | 35 | **MATCHED** |
| `CHelicopter` | 23 | 23 | **MATCHED** |
| `CAirPlane` | 18 | 18 | **MATCHED** |
| `CTrain` | 12 | 12 | **MATCHED** |
| `CBulletWeaponBase` | 29 | 29 | **MATCHED** |
| `CMissileWeaponBase` | 25 | 25 | **MATCHED** |
| `CRPGFireLeachWeapon` | 6 | 6 | **MATCHED** |
| `(none)` | 14 | 14 | **MATCHED** |
| **`CMotorBike`** | **absent** | **19** | **DIFFERS — omitted** |
| row total "88" (CBoat+CHelicopter+CAirPlane+CTrain) | 88 | 35+23+18+12 = 88 (true as written) | arithmetic right, population incomplete |
| whole table | 288 | `owners` sums to **307** | **DIFFERS by 19** |

The plan's table therefore accounts for **288 of 307** pulses. `CMotorBike` **19** is missing, and it
is listed in the G2-17 row the plan is working from (`GRAB_BACKLOG.md:1839`: "CMotorBike 19"). Adding
it makes the vehicle rows 126 + 19 + 88 = 233 and the total 307. Nothing else in the table changes.

Related, not wrong but worth keeping straight: `totals.root_classes` is a **different** count —
`CCar` **125** and `(none)` **19** over 232 entities — because it classes the *entity root*, not the
pulse's owner. The plan correctly uses `owners`, so its 126 is right; a recount that reached for
`totals.root_classes` would "find" a false 125.

### 2.4 The hashed-member table (plan:200–206)

| # | plan value | `members[]` entry | counted | verdict |
|---|---|---|---|---|
| 12 | `id:24872388` = **6** distinct | `distinct` = 6 | 6 | **MATCHED** |
| 13 | `id:9865E7F2` = **5** | 5 | 5 (values 100/40/50/25/250 exactly as the plan lists) | **MATCHED** |
| 14 | `id:060AAA81` = **3**, "20 (286), 5 (11 = fuel tank), 60 (10 = barrel)" | 3 | 3; 20 × 286, 5 × 11, 60 × 10 | **MATCHED** |
| 15 | `id:530046B3` = **9** | 9 | 9 | **MATCHED** |
| 16 | `id:F39EC6EA` = **3**, "0.1 (287), 0.8 (fuel tank), 0.75 (barrel)" | 3 | 3; 0.1 × 287, 0.8 × 10, 0.75 × 10 | **MATCHED** |
| 17 | `id:A1B0DAF9` = **4**, "2 / 3 / −1 / 0" | 4 | 4; 2 × 238, 3 × 29, −1 × 38, 0 × 2 | **MATCHED** |
| 18 | seven flags "**2 each**" (`4912FC04`, `AE6F7EFF`, `CF4F7880`, `2849C306`, `5AF29116`, `831DAB81`, `34303F77`) | `distinct` = 2 on all seven | 2 × 7 | **MATCHED** |
| 19 | "**100** on all **115** car blasts" | `tunes[car_explosion_medium].objects` = 115; `id:24872388` value 100 | 115 pulses; 100 × 268 overall | **MATCHED** |

Completeness note (no wrong number): two rows state a distinct count and then list fewer values.
`id:24872388` has **6** distinct values and the row names **5** — the sixth is **50** on the one
`prototype_missile_explosion_sam.ftune` pulse. `id:530046B3` has **9** and the row names **5** — the
others are `1.5` ×3 (`w604`), `7` ×1 (`prototype_missile_explosion_sam`), `50` ×1 (`w704_m488`). The
counts the plan prints are right; the enumerations are partial by one and by four.

### 2.5 The tune-side numbers

| # | figure | plan line(s) | JSON key | counted | verdict |
|---|---|---|---|---|---|
| 20 | `PlayerDamage` **0 … 3000** | 43 | `ranges["PlayerDamage"]` | min 0, max 3000 | **MATCHED** |
| 21 | `PlayerDamageRadius` **1.5 … 50** | 44 | `ranges["PlayerDamageRadius"]` | 1.5 / 50 | **MATCHED** |
| 22 | AI twin "**0/5 … 1000/50**" | 48 | `ranges["AIDamage"]`, `ranges["AIDamageRadius"]` | 0 / 1000; 0 / 50 | **MATCHED** |
| 23 | `*RadiusPercentageMax` and `*RadiusMin` **0 … 1** | 45–46 | `ranges[...]` | 0 / 1 both | **MATCHED** |
| 24 | falloff pairs: "**0/0** on the stock vehicle blasts", "**0.1/0.25** on `barrel_explosion` and `bike_explosion_medium`", "**0.25/0.25** on the fuel tank and `w704_m488`", "**1.0/1.0** on `truck_emp` and `w613_bomb`" | 55–56 | `tunes[].values` | car 0/0 ✓; barrel **0.1/0.25** ✓; **bike 0.1/0.15** ✗; fuel tank 0.25/0.25 ✓; `w704_m488` 0.25/0.25 ✓; `truck_emp` 1.0/1.0 ✓; `w613_bomb` 1.0/1.0 ✓ | **DIFFERS on one tune** |
| 25 | JSON is **28,992** lines | 10 | `wc -l Research/JC3Grab/FORCEPULSE.json` | **27,992** | **DIFFERS** |
| 26 | "**1** unrelated reference" (the graph script) | 279, §4.2 | `totals.other_refs`; `totals.other_ref_list` | 1 (`CGraphScriptGameObject`, `id:65424AC6`, object `GraphScript`, mm340) | **MATCHED** |

**2.5a — the bike tune (plan:55).** `tunes[bike_explosion_medium.ftune].values` gives
`PlayerDamageRadiusPercentageMax` = **0.15** and `PlayerDamageRadiusMin` = **0.1**; the plan pairs the
bike with `barrel_explosion` as "0.1/0.25". Barrel is 0.1/0.25 (Pmax 0.1, Pmin 0.25), so the pair in
the sentence is the barrel's, applied to both. The correct statement is "0.1/0.25 on
`barrel_explosion`; 0.1/0.15 on `bike_explosion_medium`". The plan's derived falloff rule
(`max(Pmax·R, Pmin·R)` then falloff to R) is unaffected — it is a rule over each tune's own pair.

---

## 3. Tally

| group | figures | matched | differs |
|---|---:|---:|---:|
| pulses / entities / chassis (G2-17's three) | 3 | 3 | 0 |
| members (count, split, per-tune numbers) | 4 | 4 | 0 |
| space (origin, exceptions, matrices) | 3 | 1 | 2 (§2.1a, §2.2) |
| ownership (pointered, unowned, owner classes) | 3 | 2 | 1 (§2.3) |
| hashed members (§2.4) | 8 | 8 | 0 |
| tune ranges and falloff | 6 | 5 | 1 (§2.5a) |
| file size (lines) | 1 | 0 | 1 |
| **total** | **28** | **23** | **5** |

The five differences are: the 14-vs-15 origin exceptions (with one misattributed pulse), the
"six non-identity matrices" claim, the missing `CMotorBike` 19 in the owner table, the
`bike_explosion_medium` falloff pair, and the JSON's line count.

---

## UNKNOWN

1. **The name "`BOMB_JEEP`" for the mm340 pulse** (plan §4.2, echoed from `GRAB_BACKLOG.md:1839`).
   `totals.other_ref_list` gives the holder as a `CGraphScriptGameObject` with `id:65424AC6`, object
   name **`GraphScript`**; the pulse itself is `explosion_force_pulse` with tune `w704_m488.ftune`.
   No `BOMB_JEEP` string exists in `FORCEPULSE.json`. Decided by the `GraphScript` bytecode blob in
   `editor/entities/jc_vehicles/02_air/v4603_plane_urga_cargotransport/v4603_plane_urga_cargotransport_mm340.ee`,
   or by the object's own name table if the string is an object name.
2. **Whether the 41 multi-pulse entities matter for the plan's carrier argument** (`totals.multi_pulse_entities`
   = 41). The plan never quotes this figure; it is named here only so a later row does not mistake
   "one pulse per owner" for a fleet rule. Decided by the plan's own §4.1 if it is ever rewritten —
   no recursion needed today.

---

## 4. Limits

1. **The JSON is the source, not the game.** Every count above is a property of
   `FORCEPULSE.json`; whether its census is *complete* (i.e. that no `.ee` in the archives was
   skipped) is `Tools/scripts/jc3forcepulse.py --check`'s claim, which this recount did not re-run.
2. **`FORCEPULSE.md` was not recounted** — the task named the JSON as primary. Where the two could
   differ, the JSON value is reported. (The `.md` agrees with the JSON on every figure checked en
   route: 307 / 232 / 79 / 31 / 23 / 292 / 293 / 14.)
3. **Plan §4.2's "`CShapeTrigger` 32, `CEventTrigger` 18"** is not a `CForcePulse` number and is not
   in this JSON; it belongs to the G2-35 census and was not recounted here.
4. **The plan file was not modified.** Only this report was written.
