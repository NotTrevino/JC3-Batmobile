# Assumption challenge — card T-17 · Effects translation

Written 2026-10-30. **Read-only review:** no source, generated artefact, build, save or game file was
modified; the only file written is this one. No game was launched, nothing was installed into
`D:\Games`, nothing was committed, no secrets read. Running the card's own gates created only
`Tools/scripts/__pycache__/*.pyc` (git-ignored).

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14, `GRAB_BACKLOG.md:1-60`), the T-17 card
(`GRAB_BACKLOG.md:932-938`), its §12 row (`GRAB_BACKLOG.md:1326`), `MODLOG.md` §"T-17 · Effects
translation — intended change" / "— done" (`MODLOG.md:12298-12432`), and the card's outputs:
`Tools/scripts/t17_fx.py`, `Working/Translation/T13_FX.md`, `Working/Translation/t17_fx.json`,
`Working/Translation/T_ROWS.jsonl` (doc `T-13`), `STATUS.md`, `GRAB_BACKLOG.md` §12.
Inputs read where a claim needed testing: `Research/JC3Grab/FX_TABLE.jsonl` (57,187 rows, 955
distinct `.effc`), `Research/JC3Grab/USAGES.json` (G2-22), `Research/JC3Grab/WEAPONS.jsonl`
(G2-10), `Research/BatmobileGrab/PARTICLES_FEATURES.json` (G1-16), `Research/BatmobileGrab/
SOCKETS_JC3.json` (G1-13), `Research/JC3Grab/VOCABULARY.md`, `Research/JC3Grab/G2X.md`,
`Research/BatmobileGrab/OFFSETS.json` + `BMSDK_OFFSETS.json`, `Tools/scripts/bmak_coverage.py`.

**Card as written** (`GRAB_BACKLOG.md:932`): *"per BmAK effect feature: JC3 effect chosen (existing
`.effc` path, by kind and size match from `FX_TABLE.jsonl`), attachment point (socket), trigger
(usage/weapon/damage state). … Out: `Working/Translation/T13_FX.md` + rows. Done: every FX code has
a chosen effect or a named omission."*

---

## VERDICT

**The effect files and the sockets are decoded; the count, the denominator, every trigger and one of
the five absences are not.** `t17_fx.py --check` exits 0 and the ledger is consistent, but the gate
cannot fail on the things that are wrong: it re-derives rows from rules the author typed, and its
only trigger check is "does a usage with this *name* exist". Of the 15 assumptions tested below,
**3 HOLD, 6 are WEAK and 6 are BROKEN**, including:

* **the unit** — "298 vehicles" is 298 *container files*; there are 309 vehicle containers over
  **117 distinct vehicle directories** in `FX_TABLE`, and the fleet is 232 (`VOCABULARY.md`, `n=232`
  on 64 `tire_effects` rows; `G2X.md:108`). A count of 298 cannot be a count of vehicles.
* **the trigger column** — the donor `v0300` signature `.ee` has **exactly one** decoded usage
  (`HeadLights`). It appears in none of `EngineNitro`, `EngineRunning`, `EngineSmoking`,
  `OnExploded`, `OnPartReachedDamageState`. All five trigger cells are word-similarity inferences,
  and the usage table's own effect names (`dynamic_nitrous`, `dynamic_exhaust`, `damage_smoke`,
  `engine_break`, `tail_damage`) have **zero** matching `.effc` paths.
* **T-FX13 / casings** — "no vehicle in the fleet carries a casing/shell effect" is refuted:
  `effects/jc_weapons/50_cal/bullet_eject_capstone.effc` is carried by 21 vehicle containers and
  `effects/jc_weapons/minigun/bullet_eject_minigun.effc` by 2. The needle was `casing|shell`, which
  never matches `bullet_eject_*`. This is the one FX-2 omission that should not be an omission.

| # | assumption | verdict |
|---|---|---|
| 1 | the card's gates are green on disk | **HOLDS** — `--check` exit 0, ledger/status/§12 consistent |
| 2 | "N vehicles carry effect X" is a vehicle count | **BROKEN** — it is a container count (309 containers, 117 dirs, fleet 232) |
| 3 | "955 distinct fleet `.effc`" | **BROKEN** — 955 is the whole table; 589 are fleet-carried |
| 4 | a usage name in `trigger` is decoded evidence | **BROKEN** — donor has one usage (`HeadLights`); no usage→file join exists |
| 5 | T-FX21's `OnExploded` citation | **BROKEN** — donor has no `OnExploded`; that usage attaches `engine_break` |
| 6 | T-FX13's "0 of 955" casing absence | **BROKEN** — `bullet_eject_*` on 21 + 2 vehicle containers |
| 7 | T-FX20's "the donor's own `BrakeLightTrailSystemL/R`" | **BROKEN** — it is a BmAK `RVehicleBatmobile` member, not the donor's |
| 8 | the other four absences (heat haze, tracer, cannon trail, brake) | **HOLDS** — wider needles find no counterpart |
| 9 | T-FX19 may choose an effect for a 0-system BmAK group | **WEAK** — same row says "0 systems (proven absent)"; T-FX9 in the same state was omitted |
| 10 | BmAK "21 systems, 2 of 6 names" is a per-name count | **WEAK** — 21 is the group total; T-FX10 and T-FX11 print the same 21 for different names |
| 11 | the donor is `_signature_preorder.ee` | **WEAK** — 85 vs 74 effects per variant; 11 signature-only, 2 of them chosen rows |
| 12 | "the donor `.ee` lists the effect" ⇒ the donor drives it | **WEAK** — carry ≠ spawn; the donor's own dust/fire modules have UNKNOWN usage names |
| 13 | the top-level `donor` bool means "donor-carried" | **WEAK** — it is the rule's preference flag; `chosen.donor` is the fact |
| 14 | "every one of the 22 `WeaponTuning` rows carries the tracer members" | **HOLDS** — 22 of 25 rows; the 3 without are the `impact` rows |
| 15 | "the weapon bundle brings the effects" (doc §5) | **UNKNOWN** — G2-10's bundle counts are not re-derived here |

**Bottom line.** T-17's *files, sockets and sizes* are real and re-derivable. What is not is the
sentence every row is built on — **"the donor already drives this under usage Y"**. The donor's
entity graph has one named usage. The card's own §5 admits this for `EngineNitro` alone; the same
limitation applies to the other four trigger cells, which are marked `decoded`. The consequence that
matters for the build is T-FX13: the `ChainGunShells` socket is left empty on the strength of a
negative that a broader needle refutes, while the Vulcan's own counterpart
(`bullet_eject_minigun.effc`) exists on a vehicle.

---

## 1. The gates are green (HOLDS)

**Test.** Ran the card's three checks and read the §12 row.

```
> python Tools/scripts/t17_fx.py --check
PASS: 17 rows (12 chosen, 5 named omissions) | FX codes 4/4 | donor effects 85 | fleet .effc 955
| sockets 8 | ledger 17/17
EXIT=0
> python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 |
edits 35 over 16 rows
check ok
EXIT1=0
> python Tools/scripts/status_audit.py --check
STATUS.md is current
EXIT2=0
> grep -n "^| T-17 " GRAB_BACKLOG.md
1326:| T-17 | done | ... 17 rows: 12 chosen `.effc`, 5 named omissions; FX-1…FX-4 4/4; 955 distinct
fleet `.effc`, 85 on the donor `v0300` signature `.ee`, 8 sockets ...
```

**Result.** 12 chosen + 5 omissions = 17 = the rules; 8 distinct sockets
(`Afterburner`, `SideExhaustL`, `CannonMuzzle`, `ChainGunMuzzle`, `ChainGunShells`, `MissileL`,
`ScrapeSparksL`, `BrakeTrailL`); donor-carried = 85 paths on the signature container (re-counted:
`len(FX_TABLE[container==…signature_preorder.ee]) == 85`). The ledger grew from 122 to 198 rows
after T-17 (later cards), which the MODLOG's "105 → 122" does not contradict — it was true then.

**Verdict: HOLDS** — the record is self-consistent. Consistency is not the same as correctness; see
§4, where the gate's trigger check is shown to be incapable of failing.

---

## 2. "N vehicles carry it" — the unit (BROKEN)

**The claim.** Every JC3 cell in `T13_FX.md` §2: "`dust_trail_asphalt.effc` - 161 vehicles",
"`chassis_slide_default.effc` - 289 vehicles", "`spark_trail_02_med.effc` - 298 vehicles",
"`exp_car_01.effc` - 126 vehicles". `T13_FX.md` §2 and the MODLOG's "298" repeat it.

**Test 1 — arithmetic.** The fleet is 232 (`Research/JC3Grab/VOCABULARY.md` has 64 `tire_effects.*`
rows each marked `n=232`; `G2X.md:108` "232 vehicles"). A carrier count of 298 or 289 exceeds the
whole fleet.

**Test 2 — the code.** `Tools/scripts/t17_fx.py:268`:

```python
e["vehicles"] = sum(1 for c in e["containers"] if "/jc_vehicles/" in c)
```

That sums *containers*, not vehicles. Counted from `FX_TABLE.jsonl`:

```
jc_vehicles containers=309 distinct vehicle dirs=117
containers per vehicle dir: max=9, >1: 95
donor dir containers: ['…_debug.ee', '…_signature_preorder.ee', '…_civilian_01.ee']
```

**Test 3 — the fingerprint.** If the field is a container count, then `vehicles == containers`
exactly when every carrier is a vehicle container, and `vehicles < containers` otherwise. The record
shows both, every time:

```
T-FX7    donor=True  vehicles=17   containers=17
T-FX10   donor=False vehicles=11   containers=12
T-FX11   donor=False vehicles=15   containers=20
T-FX14   donor=True  vehicles=2    containers=3
T-FX18   donor=True  vehicles=289  containers=290
T-FX19   donor=True  vehicles=298  containers=301
```

**Result.** The number is a count of `.effc`-listing container files. The build has at most 117
vehicle directories and a fleet of 232, so "298 vehicles" is not a vehicle count under any reading.
The doc's `jc3_cell()` prints the label "vehicles" over it (`t17_fx.py:438`), and the ranking
(`t17_fx.py:370`) prefers the larger number — so the choice between candidates is being made on
container popularity while being reported as fleet popularity. Within a vehicle, more variants
(`_debug`, `_civilian_01`, `_blackhand_01`) inflate the count; the 21-carrier
`bullet_eject_capstone.effc` in §6 is mostly DLC blackhand *variants* of the same boats, not 21
different vehicles.

**Verdict: BROKEN.** Direction of the error is safe (the ranking still prefers common effects), but
every "N vehicles" figure in the doc, the MODLOG and the §12 row is wrong by an unknown factor
between 1 and ~2.6.

---

## 3. "955 distinct fleet `.effc`" (BROKEN)

**The claim.** `GRAB_BACKLOG.md:1326` "955 distinct fleet `.effc`"; `T13_FX.md` §4 "0 of 955 match
over the **vehicle-carried** `.effc` paths" (T-FX13); `t17_fx.py`'s `fleet_vehicle_effc`.

**Test.**

```
rows 57187
distinct containers 767 distinct paths 955
distinct effc carried by a jc_vehicles container 589
```

**Result.** 955 is the number of distinct `.effc` paths named by *any* container in the table —
characters, props, DLC, destruction, environments. Only **589** of them are carried by any
`/jc_vehicles/` container. `fleet_vehicle_effc` is defined as "paths with at least one jc_vehicles
carrier", which is 589, yet the printed count is 955 (`t17_fx.py:478`, `sum(1 for e in fx.values()
if e["vehicles"])` — correct — but the doc and §12 call that 955 the fleet). The T-FX13 sentence is
the worst case: it says "955 … over the vehicle-carried paths", mixing the two denominators in one
clause.

**Verdict: BROKEN** as a label. The negative tests themselves are over 955, which is the right
superset for a negative; the wording claims a smaller set than was searched, so no absence is
*weaker* than stated — but the "fleet" figure is not the fleet.

---

## 4. `trigger` is decoded evidence (BROKEN — the central one)

**The claim.** Five rows carry a usage name plus `trigger_evidence {hash, usage, vehicles}` and
`confidence: decoded`:

| row | trigger | evidence recorded |
|---|---|---|
| T-FX7 | `EngineNitro` | hash 4197885156, 18 vehicles |
| T-FX8 | `EngineRunning` | hash 2819629913, 69 vehicles |
| T-FX21 | `OnExploded` | hash 3587098424, 2 vehicles |
| T-FX22 | `OnPartReachedDamageState` | hash 2287746320, 3 vehicles |
| T-FX23 | `EngineSmoking` | hash 102641159, 23 vehicles |

And the doc's prose is stronger than the evidence: T-FX7 "the donor graph **already drives** the
nitrous exhaust under `EngineNitro`"; T-FX8 "`EngineRunning` **already drives** the dual exhaust on
the donor"; T-FX21 "the car explosion effect **the donor already spawns**".

**Test 1 — is the donor in those usages?**

```python
DON = "…/v0300_car_kensington_sportsmuscle_signature_preorder.ee"
for e in USAGES["usages"]: print(names, modules, len(vehicles), DON in vehicles, effects)
```

```
['EngineSmoking']          mods=23  vehicles=23  donor=False effects=[('damage_smoke', 23)]
['OnPartReachedDamageState'] mods=3 vehicles=3   donor=False effects=[('tail_damage', 3)]
['EngineRunning']          mods=69  vehicles=69  donor=False effects=[('EngineKeyOn',4),
                                                              ('EngineNitro',20),
                                                              ('dynamic_exhaust',46),
                                                              ('dynamic_test',19)]
['OnExploded']             mods=2   vehicles=2   donor=False effects=[('engine_break', 2)]
['Explosion']              mods=23  vehicles=23  donor=False effects=[('engine_break',6),
                                                    ('explosion_glass',3),
                                                    ('explosion_rotor',23),
                                                    ('explosion_rotor_rear',9)]
['EngineNitro']            mods=18  vehicles=18  donor=False effects=[('EngineNitro',4),
                                                              ('dynamic_nitrous',14)]
['HeadLights']             mods=145 vehicles=145 donor=True  effects=[('dynamic_headlight',145)]
```

`USAGES.json` also records the donor-level map. Its complete set of **named** usages:

```
flame.donor_usages: [{"effects": ["dynamic_headlight"], "hash": 3551535361, "name": "HeadLights"}]
```

One. The other ~49 donor effect modules have `name: None, name_source: UNKNOWN` — including
`['flame']`, `['damage_fire_left','damage_fire_right','engine_fire_drips','engine_fire_ground']`
and `['combined_wheel_default_sfx','vehicle_dust_trail']`.

**Test 2 — does the usage table name the chosen file?** No. The usage table's `effect` field is an
effect *module* name, and none of those exists as an `.effc` path:

```
dynamic_exhaust        paths=0
dynamic_nitrous        paths=0
damage_smoke           paths=0
explosion_rotor        paths=0
tail_damage            paths=0
engine_break           paths=0
dynamic_burn_engine    paths=0
car_cycle_base_dual    paths=1  ['effects/jc_vehicles/exhaust/car_cycle_base_dual.effc']
```

So there is no join on disk from a usage to a chosen `.effc`. The link "`EngineNitro` ⇒
`car_cycle_base_dual_nitrous`" is the word *nitrous*; "`EngineSmoking` ⇒ `dmg_smoke_engine`" is the
word *smoke*; "burn states ⇒ `dmg_fire_*`" is the word *burn*. That is exactly the R5 failure the
card's own house rules forbid — a member read by its name, not its behaviour.

**Test 3 — can the gate catch it?** No. `t17_fx.py:349-354`:

```python
trig = usages.get(rule["trigger"])
row["trigger_evidence"] = ({"usage": rule["trigger"], "hash": trig["hash"],
                            "vehicles": trig["vehicles"]} if trig else None)
```

It asserts the name exists and copies the count. It never checks that the usage carries the chosen
effect and never checks donor membership. `--check` can only fail on the trigger if the usage *name*
is misspelled.

**Result.** Five trigger cells are inference. One of them (T-FX21) is additionally mis-cited (§5).
The doc's §5 flags this for `EngineNitro` only — an honest note applied to one fifth of the cases it
covers. The real trigger for the donor is largely UNKNOWN: `damage_smoke`, `vehicle_dust_trail` and
`flame` are decoded *module names* with undecoded usage.

**Verdict: BROKEN.** The effect file, the socket and the size are decoded; the *when* is not.

---

## 5. T-FX21's `OnExploded` citation (BROKEN)

**The claim.** `T13_FX.md` §2: "death explosion = the donor's `exp_car_01` effect under the
`OnExploded` usage (G2-22)"; propose: "the car explosion effect the donor already spawns".

**Test.**

```
['OnExploded'] mods=2 vehicles=2 donor=False effects=[('engine_break', 2)]
  vehicles: v4800_plane_brothers_vintagefighter_debug.ee, …_rebel_01.ee
```

and the donor's fire/explosion modules in its own map:

```
None UNKNOWN ['water_explosion']
Explosion  module usage name ['explosion']
None UNKNOWN ['fire_post_explosion']
```

**Result.** Three separate failures: (a) the donor is not one of the two `OnExploded` vehicles —
both are the vintage fighter; (b) the effect that usage attaches is `engine_break`, a break effect,
not an explosion; (c) the donor's *actual* explosion usage is `Explosion` (hash 3600488098, 23
vehicles, effects `explosion_rotor` / `explosion_rotor_rear` / `explosion_glass` / `engine_break`),
which the record never mentions. `exp_car_01` is genuinely carried by the donor (126 containers) —
that half holds — but "under the `OnExploded` usage" is false, and so is "already spawns".

**Verdict: BROKEN.**

---

## 6. T-FX13 · casings — the negative that a wider needle refutes (BROKEN)

**The claim.** `T13_FX.md` §2: "**no vehicle-carried effect**; non-vehicle matches:
`shell_eject_12ga.effc`, `shell_eject_12ga_auto.effc`"; "no vehicle-carried effect: no JC3 vehicle
gun ejects casings"; §4 proof: "0 of 955 match over the vehicle-carried `.effc` paths". Proposal:
"the `ChainGunShells` socket stays empty".

**Test.** The rule is `match=["casing","shell"]` (`t17_fx.py:129`). Broadened to the words the game
actually uses:

```
== casing/shell/eject/brass/ammo: 11 hit(s)
   0   effects/destruction/props/sparks_ammo_cashes_crate_01.effc
   21  effects/jc_weapons/50_cal/bullet_eject_capstone.effc
   2   effects/jc_weapons/minigun/bullet_eject_minigun.effc
   0   effects/jc_weapons/pistol/bullet_eject_pistol.effc
   0   effects/jc_weapons/pistol/bullet_eject_revolver.effc
   0   effects/jc_weapons/pistol/bullet_eject_smg.effc
```

Carrier detail:

```
effects/jc_weapons/50_cal/bullet_eject_capstone.effc   total=22 veh=21
     dlc/…/jc_vehicles/01_land/v0600_car_urga_armoredjeep/v0600_car_urga_armoredjeep_blackhand_01.ee
     dlc/…/jc_vehicles/03_sea/v1200_boat_capstone_heavypatrol/v1200_…_blackhand_01.ee
effects/jc_weapons/minigun/bullet_eject_minigun.effc   total=4  veh=2
     dlc/…/jc_vehicles/03_sea/v1706_boat_na_rocketboat/v1706_boat_na_rocketboat_01.ee
     dlc/…/jc_vehicles/03_sea/v1706_boat_na_rocketboat/v1706_boat_na_rocketboat_debug.ee
effects/jc_weapons/shotgun/impacts/shell_eject_12ga.effc total=3 veh=0
```

**Result.** `bullet_eject_*` is the game's casing effect family, and two members are carried by
vehicle containers — 21 and 2 respectively (remember: containers, not vehicles, per §2; still
non-zero either way). `bullet_eject_minigun` is the minigun case, which is precisely the Vulcan slot
FX-2 is translating. The "0 of 955" is true *for the needle the rule used*; the needle was chosen
from BmAK's vocabulary (`ChainGun_BulletCasing`, `RiotSuppressor_BulletCasing`) rather than from
JC3's (`bullet_eject`). The doc then converts the needle result into a behaviour claim — "no JC3
vehicle gun ejects casings" — which the data on disk contradicts. (Whether the eject effect is
*tied to the weapon* rather than merely listed on the vehicle is a separate question the record
never asks; the absence was declared before it was posed.)

**Verdict: BROKEN.** T-FX13 should be re-opened: `ChainGunShells` has a shipped effect and a
`vehicle fire` trigger to inherit from T-11's weapon clone, not an empty socket.

---

## 7. T-FX20's "the donor's own `BrakeLightTrailSystemL/R`" (BROKEN)

**The claim.** `T13_FX.md` §2 propose: "the donor's own `BrakeLightTrailSystemL/R` stays as the
entity graph carries it (T-FX6)"; why: "no brake-trail effect path exists in the fleet (0 of 955) and
no `BrakeLightTrail` system is in G1-16's 206". MODLOG repeats it at `MODLOG.md:12359`.

**Test 1 — whose member is it?**

```
Research/BatmobileGrab/OFFSETS.md:391
| RVehicleBatmobile | 0x1234 | ObjectNCRProperty | - | 4 | named-sdk | BrakeLightTrailSystemL | BmSDK-AK class dump: RVehicleBatmobileBase.BrakeLightTrailSystemL … |
Research/BatmobileGrab/OFFSETS.md:392   … BrakeLightTrailSystemR …
Tools/scripts/bmak_coverage.py:103
if n.startswith(("BrakeLightTrail", "RearFinTrail", "SpeedLines", "WallScrapeSparks")) or n == "HeatSteam":
    return "T-FX6", "vehicle effect system, not a physics number"
```

**Test 2 — is it in G1-16's 206?**

```
PARTICLES systems 206 groups 21
systems with Brake/BrakeLight: []
systems with Scrape: []
systems with Heat/Steam: []
```

`BrakeLightTrailSystemL/R` occurs in this repo only as `RVehicleBatmobileBase` members (BMSDK class
dump) and in the coverage router — it is a **BmAK** member name, never a JC3 donor member.

**Result.** The omission itself survives (no `brake` effect path exists — see §8), and T-FX6 owning
the BmAK member is correct per `bmak_coverage.py`. But the sentence "the donor's own …" attributes a
BmAK member to the JC3 donor, and the "not among G1-16's 206" comparison is vacuous: a BmAK class
member could never appear in a JC3 particle-system census. The "proof" for the *carrier* half is a
category error, even though the conclusion happens to be right.

**Verdict: BROKEN** (the wording and its proof; the omission stands).

---

## 8. The other four absences (HOLDS)

Each rule's needle, then a wider one over all 955 paths.

| row | rule needle | hits | wider needle | hits | verdict |
|---|---|---|---|---|---|
| T-FX9 | `haze` | 0 | `heat|haze|steam|vapor` | 1 — `effects/jc_vehicles/exhaust/car_speedrom_heater.effc` (12) | **HOLDS** — a heater, not haze |
| T-FX12 | `tracer` | 0 | `tracer|beam|bullet` | 25 — all `bullet_eject_*`, `impact_*_exp_bullet`, `lightning_gun_destruction_beam` | **HOLDS** — no tracer effect file |
| T-FX16 | `canon_trail`,`shell_trail` | 0 | `/jc_weapons/` + `trail` | 19 — missile, grenade, rpg, emp, c4 only | **HOLDS** — no cannon-round trail |
| T-FX20 | `brake` | 0 | `brake|stoplight|tail_?light` | 1 — `dmg_taillight_break.effc` (166) | **HOLDS** — a damage effect, not a trail |

`PARTICLES_FEATURES.json` corroborates the BmAK half of T-FX9 (`heat-steam` group, 0 systems) and
T-FX20 (no brake/scrape/heat system in 206).

**Verdict: HOLDS.** These are the negatives the card got right: the needle result and the behaviour
claim agree. Note the asymmetry with §6 — the method is only as good as the word list, and the
casing list was taken from the wrong side of the translation.

---

## 9. T-FX19 chooses an effect for a 0-system group (WEAK)

**The claim.** T-FX19 BmAK cell: "G1-16 wall-scrape: **0 systems (proven absent)**, 0 emitters";
JC3 cell: "`effects/trails/spark_trail_02_med.effc` - 298 vehicles"; propose: "use the nearest fleet
effect". `confidence: derived`.

**Test.** Compare the two zero-system rows:

```
T-FX9  bmak: group heat-steam, systems 0, lifetime null → chosen null, absence {matches: 0}
T-FX19 bmak: group wall-scrape, systems 0, lifetime null → chosen spark_trail_02_med
```

Both print "0 systems (proven absent)" through the same `bmak_cell()` branch. In the same doc, one
becomes a named omission and the other a chosen effect.

**Result.** The card has no stated rule for a 0-system group. The MODLOG's "Two things the card did
not assume" says a 0-system group "is a BmAK absence, not an untranslated feature" — T-FX19
contradicts that: it translates a feature the source does not have. Also, `HeatSteam` *is* a BmAK
`RVehicleBatmobile` member routed to T-FX6, so "0 systems" describes particle systems only, not the
absence of the feature; the doc's parenthetical "proven absent" overstates it in both rows.

**Verdict: WEAK** — harmless for the build (a shipped spark effect on an existing socket), but it
means the doc's own rule is applied inconsistently and a later card cannot tell which convention
holds.

---

## 10. BmAK "systems" counts vs filtered names (WEAK)

**The claim.** T-FX10: "G1-16 muzzle-flash: 21 systems, **2 of 6 names**"; T-FX11: "G1-16
muzzle-flash: **21 systems / 6 names**".

**Test.** Both rows read the same group:

```
--- T-FX10 bmak [{"group":"muzzle-flash","systems":21,"distinct":6,"emitters":117,
                  "names_filtered":true,  "names":[canon…2]}]
--- T-FX11 bmak [{"group":"muzzle-flash","systems":21,"distinct":6,"emitters":117,
                  "names_filtered":false, "names":[6 names]}]
```

**Result.** 21 is the *group* total and does not change when the name filter changes; the cell
therefore reads as if 21 systems belong to the two cannon-named emitters. G1-16 gives per-group
systems/emitters/lifetime, and the filter only chooses which names to display. The pairing is
visually a "fleet-wide claim (21) tested on a sample (2 names)".

**Verdict: WEAK** — a presentation error; it does not change any chosen effect, but it invites a
reader to believe the cannon muzzle flash has 21 systems of its own.

---

## 11. The donor is the `_signature_preorder` variant (WEAK)

**The claim.** `t17_fx.py:55` `DONOR = …v0300_car_kensington_sportsmuscle_signature_preorder.ee`;
"donor effects 85" in the gate output and the §12 row; T-FX14/T-FX15 propose "already on the donor".

**Test.**

```
T-FX7  sig=True civ=True dbg=True   car_cycle_base_dual_nitrous.effc
T-FX14 sig=True civ=False dbg=False missile_trail_car.effc
T-FX15 sig=True civ=False dbg=False tank_explosive_default.effc
…
sig total 85  civ total 74  sig-only paths 11
```

**Result.** The three donor containers disagree: `civilian_01` and `debug` carry 74, the signature
one 85. Two chosen effects (`missile_trail_car`, `tank_explosive_default`) are carried **only** by
the signature variant. If the build clones any other variant, those two rows lose their
"donor-carried" basis. `FX_TABLE.jsonl` contains no bare `v0300_car_kensington_sportsmuscle.ee`, so
"the donor `.ee`" is not a single file.

**Verdict: WEAK** — the choice of signature variant is stated and defensible (D-4 keeps the armed
one), but "the donor carries it" is variant-dependent for 2 of 12 rows and the doc does not say so.

---

## 12. "carried" ⇒ "spawns" (WEAK)

**The claim.** Every chosen row's `now` cell: "carried: the donor `.ee` lists the effect (FX_TABLE
container set)" — accurate. T-FX21's propose: "the car explosion effect the donor already spawns" —
not the same statement.

**Test.** `FX_TABLE.jsonl` records that a container *names* a path (`container → path`). Whether the
entity spawns it requires an effect module with a usage, which is `USAGES.json`. The donor's own
effect modules:

```
None UNKNOWN ['flame']
None UNKNOWN ['damage_fire_left', 'damage_fire_right', 'engine_fire_drips', 'engine_fire_ground']
None UNKNOWN ['combined_wheel_default_sfx', 'vehicle_dust_trail']
None UNKNOWN ['chassis_sliding']
```

**Result.** The donor's dust, fire and flame modules exist but their usage names were not decoded.
So "lists the effect" is proven and "drives it under X" is not — for the dust rows as much as for
`EngineNitro`. The doc separates the two phrases in the cells but merges them in the prose.

**Verdict: WEAK** — the `now` column is honest; the `propose` column overstates.

---

## 13. The top-level `donor` field (WEAK)

**The claim.** `t17_fx.json` rows carry `donor: true` for 12 rows, including T-FX12 (tracers), T-FX13
(casings), T-FX16 (cannon trail), T-FX20 (brake) — rows with **no chosen effect at all**.

**Test.** `t17_fx.py:337` `row["donor"] = rule["donor"]` — the rule's *preference flag*
(`donor=True` means "prefer an effect the donor chassis already carries", see the RULES header),
copied verbatim. The genuine carrier fact is `row["chosen"]["donor"]`, computed at line 269 as
`DONOR in e["containers"]`.

**Result.** Two keys named `donor` in one record with different meanings: one is a ranking
preference, one is a decoded fact. For T-FX12/13/16/20 the top-level value is `true` while nothing is
chosen and (for 12/16) no such effect exists anywhere.

**Verdict: WEAK** — no decision depends on it (the gate uses `chosen.donor` for ranking), but it is
a field read by its name, and a later reader will take it as "the donor carries it".

---

## 14. The tracer mechanism, 22 rows (HOLDS)

**The claim.** T-FX12: "JC3 draws it as a texture, and every one of the 22 `WeaponTuning` rows
carries `tracer_texture_type` / `tracer_fire_velocity` / `tracer_time_to_live`".

**Test.**

```
WEAPONS rows 25
kinds Counter({'missile': 11, 'bullet': 11, 'impact': 3})
tracer_texture_type      in 22/25 rows
tracer_fire_velocity     in 22/25 rows
tracer_time_to_live      in 22/25 rows
tracer_fire_length       in 22/25 rows
rows without tracer members: ['w604_helicopter_mgun_impact','w610_fighterjet_mgun_impact',
                              'w617_vintagefighter_mgun_impact']
```

**Result.** 25 rows = 11 bullet + 11 missile + 3 impact. All 22 non-impact rows carry all four
members; the three exceptions are the impact rows, which are not `WeaponTuning`. The count and the
"every" are correct for the population they mean.

**Verdict: HOLDS** — with the standing caveat that "drawn as a texture" is inferred from the member
names (`tracer_texture_type`), i.e. an R5 read. The absence of a tracer `.effc` (§8) is independent
evidence for the same conclusion.

---

## 15. "The effect rides the weapon bundle" (UNKNOWN)

**The claim.** `T13_FX.md` §5: "the effects named are the fleet's own for that weapon *kind*,
measured per id: the weapon bundles carry them, so a clone brings them (w619 16, w610 14, w618 12,
w608 5 effects; w602/w603/w604 ship no bundle of their own, G2-10)."

**Test.** Not re-derived in this pass: the claim comes from `WEAPONS.jsonl`'s `carriers`/`tunes`
sections (G2-10), which record which entity bundles reference which weapon ids. Re-running that
decode is outside a read-only assumption challenge against `FX_TABLE`/`USAGES`.

**Result.** No contradiction found in the files read here (the rows' chosen paths are all
`jc_weapons/*` files carried by weapon or vehicle containers), but the bundle→effect link was not
independently reproduced.

**Verdict: UNKNOWN** — stated as such, and used only to justify `dispo: next` on FX-2 rows, which is
T-11's call anyway.

---

## What a rework would have to change

1. **T-FX13** — delete the named omission. `bullet_eject_minigun.effc` (2 vehicle containers) and
   `bullet_eject_capstone.effc` (21) are the shipped casing effects; `ChainGunShells` should carry
   one, subject to T-11 deciding the weapon clone.
2. **The trigger column** — either mark the five usage-based rows `derived` with the note "usage name
   only; the donor's graph has no such usage", or drop the trigger claim to UNKNOWN, as §5 already
   does for `EngineNitro`. `--check` should assert donor membership in the usage's vehicle list, and
   that the usage's effect name resolves to the chosen path — the first would fail today.
3. **The count** — rename `vehicles` to `containers`, or compute distinct vehicle directories
   (117 in `FX_TABLE`) and state the denominator once. Any "N of 232" phrasing must go with it.
4. **The label** — "955 distinct `.effc` (all containers); 589 fleet-carried".
5. **T-FX20** — say "the BmAK `RVehicleBatmobileBase.BrakeLightTrailSystemL/R` is T-FX6's", not "the
   donor's own".
6. **T-FX19 / T-FX9** — pick one convention for a 0-system group and write it down.

**Card status.** The §12 row says `done`. Under R4's own classes the effect *choice*, *attachment*
and *size* are decoded; the *trigger* is not, and one of five omissions is refuted by data on disk.
A `done` with one refuted omission is a regression against the card's Done line ("every FX code has
a chosen effect or a named omission") only in the sense that the omission was not earned — the row
count is met, the evidence for T-FX13 is not.
