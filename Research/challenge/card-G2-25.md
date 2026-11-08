# Assumption challenge — G2-25 · HUD vehicle-weapons API

Card: `GRAB_BACKLOG.md` §G2-25 (l. 732), tracker row §12 (l. 1308), MODLOG
`## G2-25 · HUD vehicle-weapons API — done` (l. 10268) plus the 2026-10-29 rework entries
(l. 14977 / 15002). Outputs under test: `Research/JC3Grab/JC3_HUD_WEAPONS.md` (222 lines),
`Research/JC3Grab/JC3_HUD_WEAPONS.json`, `Tools/scripts/jc3hudwpn.py` (1,117 lines).

Mode: read-only. No game launch, no write under `D:/Games`, no commit. Every number below was
re-read from `E:/Modding/_JC3grab/hud/dec/` (the G2-19 decompile: `scripts/` + `movie.xml`) and
from the repo tables `INDEX.jsonl`, `WEAPON_WIRING.jsonl`, `WEAPONS.jsonl`,
`Research/BatmobileGrab/HUD_INTERFACES.json`, `Research/BatmobileGrab/MECHANICS.md`. I did not run
`jc3hudwpn.py --check` (it only reads decoded text and repo files, but its result is derivable and
the numbers below are independent of its parser).

---

## VERDICT summary

| # | assumption | class | verdict |
|---|---|---|---|
| 1 | the 260-script export is the whole HUD code universe | "no carrier exists" search scope | **HOLDS** |
| 2 | "0 call sites in the movie" ⇒ the entity→HUD bridge is native | silent inference from absence | **WEAK** |
| 3 | 2 vehicle slots; `E_NUM_WEAPON_SLOTS` 7 is the on-foot wheel | fleet-wide claim on a sample | **HOLDS** |
| 4 | JC3's vehicle weapon HUD has no heat bar (stated absence both sides) | "no carrier exists" search scope | **HOLDS** (and is stronger than argued — see 4b) |
| 5 | `weapon_cooldown` is a `0..1` fraction, `1` = full ring | value treated as decoded that is inferred | **WEAK** |
| 6 | `UpdateVehicleWeapons` returns "before any drawing" when ammo ≤ 0 | behaviour read from the name/flow | **BROKEN** (cooldown + overcharge run first) |
| 7 | the lock envelopes are "angles in fractions of a turn" | unit convention | **BROKEN** (w612 = 1.4, > one turn; same class stores 5/10/15) |
| 8 | aim distances are metres (`750 m`) | unit convention | **WEAK** |
| 9 | one lock-on marker + one incoming warning | "no other carrier" + R5 reading of `MCI_missile_locked` | **WEAK** (a second, scripted warning instrument exists; "incoming" is name-based) |
| 10 | "69 icon ids in 110 files (69 full-res + `_sm` twins)" | count / sample | **BROKEN** as a count (112 files: 68 full-res numeric + 42 `_sm` + 2 named) |
| 11 | "the fleet's 88 wired weapon components use 23 distinct ids" | fleet-wide claim on a sample | **WEAK/BROKEN** — base mount only, no DLC weapon |
| 12 | `w613` "targets nothing" | name vs behaviour (done correctly) | **HOLDS** |
| 13 | WPN-12 "cannon cooldown" is a **map** | member read by its name (R5) | **WEAK** |
| 14 | the frozen T-HUD5 snapshot is the row "as the card saw it on 2026-10-27" | value treated as decoded | **WEAK** (unverifiable, contradicts the only other copy) |
| 15 | POI facts: 32 types, lock-on 21, 1.5 s, no progress bar, 0 `CreatePoi(21)` | counts | **HOLDS** |
| 16 | the movie's "heat" is the 11-state police wanted level | member read by name | **HOLDS** |
| 17 | reticle: 14 shapes, 5 look states, 2 size rigs of 5, y = −111 for 8/11/12 | counts / coordinate convention | **HOLDS** (one wording issue) |
| 18 | "no archive is opened, only decoded text" | provenance | **HOLDS** |

The card's arithmetic is in good shape; two claims are actually false (`#6`, `#7`), two counts are
off (`#10`, `#11`), and three interpretations are name-based where the files do not say
(`#5`, `#9`, `#13`). The heat answer (`#4`) is correct and could be made airtight from the clip
inventory rather than from the API's silence.

---

## 1. "260 scripts" / `hud.as` 11295 lines — is the export complete?

**Where.** `JC3_HUD_WEAPONS.md` sources paragraph: *"the decompiled `ui/hud.gfx` export (G2-19) -
`260` AS3 scripts, `hud.as` 11295 lines"*; §8 "the only call sites in all 260 scripts"; §9 check
table "scripts scanned 260".

**Test.** Count the export, and check that the classes the movie references are inside it (a
partial decompile would turn "0 call sites" into "0 call sites in the scripts we happened to get").

```
as files: 260          all files: 260          (every file is .as — no missing text assets)
hud.as lines: 11295
grep -rn "class uibase\|class shared_lib"  ->  scripts/uibase.as:14, scripts/shared_lib.as:12
distinct .gfx in INDEX.jsonl: 32; the only HUD movie among them is ui/hud.gfx
(ui/shared_lib.gfx is the other movie the scripts import from, and its classes are in the export)
```

**Result.** 260 `.as`, `hud.as` 11,295 lines, and the two cross-movie classes (`uibase`,
`shared_lib`) are present. No second HUD movie exists in the shipped set.

**Verdict: HOLDS.** The code universe the card claims to have searched is the code universe on
disk.

---

## 2. "0 call sites ⇒ the entity → HUD bridge is native / UNKNOWN"

**Where.** §8: *"These are **public** functions on the movie's document class: the game calls them
from native code through the HUD interface, which is not in these files."* MODLOG: "so the weapon-id
-> HUD bridge stays `UNKNOWN`".

**Test.** Grep every reference of the three functions and of the lock-on entry points:

```
InitVehicleWeapons      hud.as:5030 (definition), hud.as:7535, hud.as:7536   (TestConstructor)
UpdateVehicleWeapons    hud.as:5160 (definition)                            — 1 line total
UpdateWeaponReticle     hud.as:3866 (definition)                            — 1 line total
ShowMissileLocked       hud.as:5201 (definition)
HideMissileLocked       hud.as:5221 (definition)
FlashMissileLocked      hud.as:4954 (timer listener), 5206 (definition)
CreatePoi               hud.as:3768 (definition) + 3 calls: MISSION, CHALLENGE, OPEN_WORLD
```

**Result.** The absence is real and enumerable. What is *not* in the files is the caller; the step
from "the movie never calls it" to "native code calls it" is an inference — the only on-disk
evidence is that the functions are `public` and that `TestConstructor` (a debug entry point that is
itself in the shipped movie) calls two of them. It is a very reasonable inference, but it is the
same shape as a "no carrier exists" claim with no positive evidence.

**Verdict: WEAK.** Keep the UNKNOWN for the caller (it is correct); state that the "native"
attribution is an inference, not a decoded fact — the movie shows only that the API is reachable
and unused.

---

## 3. "2 slots, index 0/1; `E_NUM_WEAPON_SLOTS = 7` is the on-foot wheel"

**Where.** §3: *"the vehicle HUD has **2 slots** … Do not confuse this with `E_NUM_WEAPON_SLOTS = 7`,
which is the **on-foot** weapon wheel"*.

**Test.** Read the array construction and every consumer of the 7-slot constant:

```
hud.as:4951  this.m_WeaponsArray = new Array(
                 this.MCI_safe_area_bottom_right.MCI_vehicle_weapons0,
                 this.MCI_safe_area_bottom_right.MCI_vehicle_weapons1);
hud.as:4952  this.m_WeaponsDataArray = new Array(new Object(),new Object());
hud.as:429   private static const E_NUM_WEAPON_SLOTS:* = 7;
hud.as:5426  for(i = 0; i < E_NUM_WEAPON_SLOTS; i++)      // inside WeaponConstructor
hud.as:5536  for(slot = 0; slot < E_NUM_WEAPON_SLOTS; slot++)  // inside InitWeapons(weapon_data:Array)
movie.xml:   MCI_vehicle_weapons0 (char 1655, depth 15) and MCI_vehicle_weapons1 (char 1655, depth 3)
             — two instances, one sprite; no MCI_vehicle_weapons2 anywhere
```

**Result.** The vehicle array is hard-sized to two; both 7-slot loops are the on-foot
`WeaponConstructor` / `InitWeapons` path (`m_WeaponId`, `m_WeaponName`, weapon-selection wheel).
The sprite is reused for both slots, so the two slots are visually identical.

**Verdict: HOLDS.**

---

## 4. "No heat bar in JC3's vehicle weapon HUD" (stated absence on both sides)

**Where.** §3/§7: *"no heat anywhere: 0 heat parameters, 0 mentions in either body, 0 of the 252
BmAK `UC_*` setters contain 'heat'"*; WPN-12 row "stated absence (both sides)".

**Test (a) — the movie.** `grep -rin heat` over all 260 scripts returns 19 files; every hit is the
police-wanted "heat": `HEAT_STATE_OFF … HEAT_STATE_CAN_APPLY_HEAT_POINTS` (hud.as:107-127) and the
`hud_code/heat/` clips. Neither `InitVehicleWeapons` (5030-5068) nor `UpdateVehicleWeapons`
(5160-5199) contains the word.

**Test (b) — the slot clip's widget inventory** (the doc does not do this, and it is the stronger
argument). The slot sprite 1655 places exactly seven named widgets and no heat widget:

```
TXT_selected_inventory_ammo · MCI_inventory_infinity · TXT_name · TXT_slash_mark
TXT_bullet_ammo · MCI_selected_weapon_icon · MCI_bullet_bar
```

**Test (c) — BmAK side.**

```
modules 19 · setters total 252 · heat setters 0
HudModuleBatmobile 37 · HudModuleTargets 16
HeatBarStart/HeatBarSize on Batmobile_Cannon_V2: 4 rows in MECHANICS.md
   (Playable_BatmobileFunhouse_SF, Playable_BatmobileJoker_SF,
    Playable_BatmobileMK2_SF, Playable_Batmobile_SF)
```

**Result.** Every leg is reproduced. The vehicle weapon slot has no heat widget at all, not merely
no heat argument — which is stronger than "0 heat parameters".

**Verdict: HOLDS.** Move the "the clip inventory has no heat widget" evidence into the doc; today
the claim leans on API silence, which invites the "maybe another argument carries it" objection.

---

## 5. "`weapon_cooldown` is a `0..1` fraction; `1` is a full ring"

**Where.** §3: *"`weapon_cooldown` is a **fraction, not a state**: `1` is a full ring, `-1` means
'this slot has no cooldown display at all'"*; `JC3_HUD_WEAPONS.json` `cooldown`.

test
```
hud.as:5349  rot = weapon_cooldown * 360;
hud.as:5350  object_rot = Math.min(rot,180);
hud.as:5352  object_rot = Math.max(rot - 180,0);
hud.as:7535  this.InitVehicleWeapons(0,141,"Panther",true,5,15,60);   // cooldown arg omitted
hud.as:7536  this.InitVehicleWeapons(1,141,"Minigun",true,2,20,100);   // cooldown arg omitted
grep UpdateVehicleWeapons -> definition only (0 calls, so no value is ever passed there either)
```

**Result.** No decoded caller ever passes a cooldown value. The "0..1" range comes only from the
`× 360` multiplication and from the names `MCI_mask_0_50` / `MCI_mask_50_100`. Both are consistent
with 0..1, and a percent convention (0..100) would saturate the ring, so 0..1 is the likely
reading — but nothing in the files states it, and there is no clamp (`rot` is an `int`; 2.0 would
yield 720° and simply saturate both masks).

**Verdict: WEAK.** It is the right working assumption for T-19/T-HUD5, but R4 it is
`decoded (inferred range)`, not `decoded`: no caller demonstrates it.

---

## 6. "`UpdateVehicleWeapons` … `<= 0` returns early, **before any drawing**"

**Where.** §2 table, row `new_magazine_ammo_amount`: *"`m_MagazineAmmo`; **`<= 0` returns early**,
before any drawing"*.

**Test.** Read the body in order:

```
5162  this.m_WeaponsDataArray[slot_index].m_MagazineAmmo = new_magazine_ammo_amount;
5163  this.m_WeaponsDataArray[slot_index].m_TotalInventoryAmmo = total_ammo;
5164  if(weapon_cooldown != -1) {
5166     this.SetCooldownRotation(slot_index,weapon_cooldown);
5167     this.AnimateOvercharged(slot_index,is_overcharged);
5168  }
5169  if(this.m_WeaponsDataArray[slot_index].m_MagazineAmmo <= 0) { return; }   // <- the early return
```

**Result.** The cooldown ring and the overcharge animation are updated **before** the early return;
only the bullet bar, the low-ammo pulse and the text are skipped. A weapon that has just fired its
last round still gets a new cooldown ring — a behaviour the doc's sentence denies.

**Verdict: BROKEN** (word "before any drawing"). Fix: "skips the bar/text update; the cooldown and
overcharge paths still run".

---

## 7. "Angles in fractions of a turn"

**Where.** §5.1: *"`w609` is an air-to-air missile (angles in fractions of a turn, vehicles + rigid
objects, 750 m)"*, following the envelope table of `0.085 / 0.3 / 1.4 / 0.12 / 0.15`.

**Test.** Print the `AutoAim` rows the table is built from, including the neighbouring fields in
the same class (the doc's table only keeps seven keys):

```
w612_fighterbomber_missile_air_lockon_autoaim.wtune
   OnFoot.AngleThresholdNewTarget       float  1.399999976158142
   OnFoot.AngleThresholdCurrentTarget   float  1.399999976158142
autoaim_w613_bombs.wtune
   OnFoot.AngleThresholdNewTarget       float  0.11999999731779099
   OnFoot.StickyAimStartAngle           float  5.0
   OnFoot.StickyAimAngleNewTarget       float  10.0
   OnFoot.StickyAimAngleCurrentTarget   float  15.0
   OnFoot.MinAimDistance                float  15.0
```

**Result.** A fraction of a turn cannot exceed 1; `w612` is `1.4` (= 504°). In the same class the
`StickyAim*Angle` fields hold 5 / 10 / 15, which are plainly degrees (a 5° sticky-aim start), while
the thresholds hold 0.085…1.4. The one convention that fits both is **radians for the thresholds**
(0.085 rad ≈ 4.9°, 1.4 rad ≈ 80°) — or "turn fractions" only for the ≤1 values and something else
for w612, which is not a coherent reading. The doc never prints a unit in the table, then asserts
one in prose.

**Verdict: BROKEN.** Delete "fractions of a turn"; record the thresholds as
`read (unit UNKNOWN; radians fit all seven values, 1.4 rules out turn fractions)`.

---

## 8. Distances are metres

**Where.** §5.1 tables (`25 / 750`, `5 / 750`, `15 / -1`) and prose "750 m".

**Test.** The tune fields are bare floats (`OnFoot.MinAimDistance 25.0`,
`OnFoot.MaxAimDistance 750.0`); no field name in the class carries a unit (contrast
`arcade.turbo_jump.punch_speed_kph`, which does). The repo's own `WEAPON_WIRING.jsonl` has
`nearest_gunner_seat.distance_m`, but that is a *derived* field computed by the G2-11 script from
world units, not a unit read from a file.

**Result.** 750 is "world units"; calling it metres assumes JC3's 1 unit = 1 m. Plausible (the
Batmobile target length is 7.026 m and donor cars are 6–8 units), but not stated in any decoded
file and not proven by this card.

**Verdict: WEAK.** Keep the numbers, label the unit `derived (assumed 1 unit = 1 m)`.

---

## 9. "One lock-on marker and one incoming warning" — and only those

**Where.** §5: *"**These are two different instruments.** … the Batmobile's HUD needs both, and JC3
has exactly one of each."* MODLOG: "the lock-on is **one POI** … a different instrument from
`MCI_missile_locked`, the flashing (0.5 s) *incoming*-missile warning".

**Test (a) — the POI facts.** Reproduced exactly (see §15). **HOLDS.**

**Test (b) — what `MCI_missile_locked` means.** Its whole API is a timer toggle:

```
hud.as:5201  public function ShowMissileLocked() : void { this.m_MissileLockedFlashing.start(); }
hud.as:5206  FlashMissileLocked()  -> toggles .alpha / .visible on MCI_safe_area_bottom_middle.MCI_missile_locked
hud.as:5221  HideMissileLocked()  -> stop + alpha 0
hud.as:283   MISSILE_LOCKED_TIMER = 0.5
```
No string, comment or dependent clip says "incoming". The clip itself (`char 1781`, bottom-middle,
depth 7) has no named children and no text.

**Test (c) — are there other missile-warning instruments?** Yes, and the doc never mentions it:

```
movie.xml:101890  MCI_wingsuit_missile_locked_distance_circle
movie.xml:102103  MCI_wingsuit_missile_locked   (child: TXT_wingsuit_missile_locked)
hud.as:10185-10220  drives it: SetMissileWarningState(STATE_LOCKED) / STATE_EVADE,
                    scales it 2 -> 1, tweens the text, uses m_Distance / m_Radius
```

**Result.** (i) The "incoming" reading of the vehicle clip is an interpretation of its name; the
movie cannot even trigger it (`ShowMissileLocked` has 0 callers), so nothing on disk separates
"a missile is locked on you" from "you have a missile lock". (ii) The movie does contain a second,
*scripted* missile-warning instrument with a distance circle and explicit `STATE_LOCKED` /
`STATE_EVADE` states — for the wingsuit — so "exactly one of each" is true only for the
vehicle cluster, and the search stopped at the clip the API names.

**Verdict: WEAK.** Keep the POI half; restate the warning half as "one un-triggered clip named
`MCI_missile_locked`; the only scripted missile warning in the movie is the wingsuit's
(`MCI_wingsuit_missile_locked`, `STATE_LOCKED`/`STATE_EVADE`), which is a closer behavioural match
for 'incoming' than the vehicle clip is".

---

## 10. "69 icon ids in 110 `weapon_icons/*.ddsc` files (69 full-res plus `_sm` twins)"

**Where.** §6: *"`INDEX.jsonl` carries **69 distinct icon ids** in 110
`textures/ui/weapon_icons/*.ddsc` files (69 full-res plus `_sm` low-res twins)"*; `--check` line
"69 weapon icons".

**Test.** Dedupe by path (INDEX repeats paths per mount) and classify by filename:

```
distinct icon paths 112
plain ids 68 · sm ids 42 · named 2 (placeholder.ddsc, skramps.ddsc)
ids without sm 27 · sm without plain [41]
614 in plain False · in sm False
plain+sm+named files 112
```

**Result.** Three different numbers: 112 files (not 110), 68 + 2 = 70 full-res files (not 69), and
69 distinct **numeric** ids only because id `41` exists **only** as `41_sm.ddsc` — i.e. a full-res
request for id 41 (`GetWeaponIconName(41,false)` → `weapon_icons/41.ddsc`) would find no file. The
wired-id conclusion still holds:

```
wired ids 23 · without plain icon [614] · with plain 22
```

**Verdict: BROKEN** for the 110/69 split (a real second gap, id 41, is masked by the same
miscount); **HOLDS** for "614 is the one wired id with no icon".

---

## 11. "The fleet's 88 wired weapon components use 23 distinct ids"

**Where.** §6: *"The fleet's 88 wired weapon components use 23 distinct ids; 22 of them have an
icon"*.

**Test.** Count the wiring table, then check what its chassis set covers:

```
weapons entries 88 · distinct weapon_id 23  ['206','601'..'622']
wiring rows 53 · distinct entities 53 · any dlc path? False
vehicle dirs: {'02_air': 23, '01_land': 18, '03_sea': 12}     # base mount only
WEAPONS.jsonl rows 25 · prefixes {'w6': 25} · w7/w8/w9: []
icon ids present in INDEX but not wired: [11..901 incl. 630,631,636,640,701,702,704,801,802,901]
```

**Result.** The 88/23 numbers reproduce, but the census is the 232 base-mount entities (the same
scope limit G2-22 has). The shipped icon set contains ids (`701/702/704/801/802/901`, plus
`630/631/636/640`) that belong to weapons absent from the census — DLC mech/black-hand/sky-fortress
weapons. So "the fleet's" is a sample.

**Verdict: WEAK/BROKEN** for the word "fleet". It should read "the 88 weapon components wired on the
232 base-mount vehicle entities already decoded" and the DLC weapon ids should be flagged as not censused.

---

## 12. "`w613` … targets nothing" (the ES name promises a lock the data does not implement)

**Where.** §5.1: *"`w613` - the 'ground lockon' - **targets nothing**: `CanTargetCharacters` /
`Vehicles` / `RigidObjects` are all 0, `MaxAimDistance` is -1 and `missile_turning_speed` is 0"*.

**Test.** Read the tune rows straight out of `WEAPONS.jsonl`:

```
w613  OnFoot.CanTargetCharacters 0 · CanTargetVehicles 0 · CanTargetRigidObjects 0
      OnFoot.MaxAimDistance -1.0 · MinAimDistance 15.0
      missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed 0.0  (ai_tuning also 0.0)
w609  turning 150 (player) / 300 (ai) · damage 1500 · MaxAimDistance 750 · MinAimDistance 25
w612  turning 300 · damage 1500 · MaxAimDistance 750 · MinAimDistance 5
```

**Result.** Every number holds, including the AI twin that the doc's table does not show (ai damage
30, ai turning 300 for w609/w612 — which is why "turning speed 150" is the player value and should
be labelled as such). This is exactly the R5 pattern the card says it follows: the name says
lock-on, the data says unguided.

**Verdict: HOLDS.**

---

## 13. WPN-12 "cannon cooldown" = **map**

**Where.** §7 table, cannon-cooldown row: *"weapon_cooldown … SetCooldownRotation 0..1 → 360 deg …
map (0..1 replaces 5 states)"*; limit: *"BmAK sends 5 categorical states, JC3 takes a 0..1
fraction: the 5 states have to be pinned"*.

**Test.** Both sides are UI calls with different shapes:

```
JC3   SetCooldownRotation (hud.as:5342)   Number in 0..1 -> ring rotation (see #5)
BmAK  UC_SetCannonCoolDown(param1:int)   HUD_INTERFACES.json, args "" (untyped in the dump),
      the doc's own text: "0…4 -> reticle Ready / Blank / PreReady*"
```

**Result.** Nothing in either file ties BmAK's five reticle states to JC3's ring fraction; the
equivalence rests on the shared words "cannon cool down". The five states are reticle *looks*
(Ready/Blank/PreReady) in BmAK, whereas the JC3 fraction drives a loader mask — a loader is not a
reticle state. The doc records the pinning as UNKNOWN but still prints "map".

**Verdict: WEAK.** Colour it `partial` until a Q-3 probe shows the loader reproducing the BmAK
reticle states; "map" claims a behaviour no file connects.

---

## 14. The frozen T-HUD5 snapshot is "the row as the card saw it on 2026-10-27"

**Where.** §7: *"T-HUD5 … as this card saw it on 2026-10-27, frozen here (sha256
`e41b8a5849f00e55`)"*; rework log: "`--check` asserts the snapshot text equals the frozen constant,
its sha256 matches".

**Test.** Recompute the digest and compare with the only other copy of that row on disk:

```
json rows.t_hud5.sha256      e41b8a5849f00e550d354a17c83367ef79d7675b14c4e10e3b036fb4e1ab4cb9
recomputed sha256            e41b8a5849f00e550d354a17c83367ef79d7675b14c4e10e3b036fb4e1ab4cb9
snapshot text                "... **blocked**: the HUD supports it, the entity does not | decoded | ..."
tmp/T6_HUD_CAMERA.beforeT19.md:24
                             "... **blocked**: the HUD supports it (G2-25: 2 slots, `InitVehicleWeapons`
                              / `UpdateVehicleWeapons`, cooldown) but the entity still has no weapon
                              component - T-11/B-05, slots per D-7 (`Research/JC3Grab/JC3_HUD_WEAPO..."
git log                      2 commits; neither contains T6_HUD_CAMERA.md history for 10-27
```

**Result.** The digest is self-consistent — but it hashes the same constant the check compares
against, so it proves integrity, not provenance. The one copy that claims to be pre-T-19 on disk
has a different blocked-reason cell, and the repo has no history that could settle which text stood
on 10-27. Since the rework's whole purpose was to stop the generator depending on a mutable foreign
row, the snapshot is a reasonable engineering fix; the historical claim around it is not verifiable.

**Verdict: WEAK.** Say "a frozen reconstruction of the row's 2026-10-27 shape; the pre-T-19 copy in
`tmp/` differs in the blocked cell" instead of "as the card saw it", and keep the digest as an
integrity check only.

---

## 15. POI facts: 32 types, lock-on = 21, 1.5 s, no progress bar, 0 movie callers

**Test.**

```
grep -c "private const POI_TYPE_" hud.as                      32
hud.as:1011   POI_TYPE_LOCK_ON_TARGET:int = 21
poi.as:75     LOCK_ON_TARGET_ROTATION_TIME:Number = 1.5
poi.as:529-533 case 21: MCI_icon.MCI_lock_on; TweenRotation(MCI_reticle,1.5,360,TM_LINEAR,TR_LOOP);
               m_HasProgressBar = false
CreatePoi call sites: hud.as:7846 MISSION, 7863 CHALLENGE, 7880 OPEN_WORLD  (0 of type 21)
```

**Result.** All reproduced: 32 constants numbered 0…31, 21 is the lock-on, one full turn per 1.5 s,
no progress bar, and no in-movie creator for it.

**Verdict: HOLDS.**

---

## 16. "The movie's heat code is the 11-state police wanted level"

**Test.** `hud_code/heat/` has five clips (`heat.as`, `heat_info_group.as`,
`heat_reinforcement_video.as`, `heat_searching_meter.as`, `heat_standard.as`); `heat.as` defines
`HEAT_STATE_OFF … HEAT_STATE_CAN_APPLY_HEAT_POINTS` = 0…10 (11 states); `hud.as` also carries
`CHAOS_REWARD_POLICE_GATE / _STATION / _HAVOC` and drives `MCI_heat_container`.

**Result.** 11 states, police/reinforcement semantics, no weapon connection. Correct.

**Verdict: HOLDS.**

---

## 17. Reticle facts and the y = −111 convention

**Test.**

```
shape ids: 0..13 (14) incl. E_RETICLE_CANNON 8
look states: 5 (InRangeTargetNeutral/Allied/Hostile, InRangeNoTarget, OutOfRange)
case labels in the size switch: 14; width computed for 5 ids (0/4 cross, 1 circle, 6 rocket, 9 flak)
RETICLE_CROSS_WIDTH_MIN 5 · CIRCLE_WIDTH_MIN 14 · ROCKET_WIDTH_MIN 5
hud.as:3882  if(reticle_shape == 8 || 11 || 12) MCI_safe_area_center.MCI_inflict_damage.y = -111;
hud.as:3886  else ... .y = -21
hud.as:3871  reticle_shape == 3 -> MCI_inflict_damage.visible = false
```

**Result.** Every count matches. One wording slip: the y offset belongs to
`MCI_inflict_damage` (the hit indicator at stage centre), not to the reticle marker itself; and
−111/−21 are Flash stage units (y down, origin top-left), not "px" in any authored sense.

**Verdict: HOLDS** (counts and convention); fix the subject of the y sentence and label the
units as stage units.

---

## 18. "No archive is opened; only decoded text"

**Test.** `jc3hudwpn.py` reads `HUD = os.path.join(GRAB, "hud", "dec", "scripts")` with
`GRAB = E:\Modding\_JC3grab`, plus `Research/JC3Grab/{INDEX,WEAPONS,WEAPON_WIRING}` and
`Research/BatmobileGrab/HUD_INTERFACES.json` / `HUD.md`. Nothing in the script opens
`D:/Games` or an `.arc` (contrast G2-22's `--check`, which does).

```
as files: 260 · all files: 260 · movie.xml present in hud/dec
```

**Result.** Provenance claim is accurate; the export is on disk and the script reads only it.

**Verdict: HOLDS.**

---

## Residual UNKNOWNs (after this challenge)

- Who calls the API, with which values: still UNKNOWN — and `weapon_cooldown`'s range cannot be
  narrowed from decoded data because no caller ever passes it (#5).
- The unit of the `AutoAim` angle thresholds: UNKNOWN, but "fractions of a turn" is ruled out by
  `w612` 1.4 (#7). Radians fit; needs a probe or a code source.
- Whether `MCI_missile_locked` means "you are locked" or "you have a lock": UNKNOWN; the only
  scripted sibling is the wingsuit warning (#9).
- The DLC/mech weapon ids and their HUD wiring: not censused (#11).
- Whether BmAK's 5 reticle cooldown states can be expressed as the JC3 0..1 ring: UNKNOWN (#13).

## What a follow-up should change (not done here — read-only)

1. §2: fix "before any drawing" — the cooldown/overcharge block runs before the early return (#6).
2. §5.1: delete "angles in fractions of a turn"; print the unit as UNKNOWN with the 1.4 counter-
   example and note radians fits (#7); label damage/turning speed as player-tuning (AI 30 / 300).
3. §6: correct the icon census to 112 files (68 full-res numeric + 42 `_sm` + 2 named), add the
   id-41 gap, scope "the fleet's 88/23" to the base mount, and list the DLC icon ids with no
   census (#10, #11).
4. §5: add the wingsuit missile-warning instrument and mark the "incoming" reading of
   `MCI_missile_locked` as an interpretation (#9).
5. §3/§7: mark the `0..1` cooldown as inferred, and the cooldown WPN-12 row as `partial` until a
   probe pins the 5 BmAK states (#5, #13).
6. §7: reword the frozen T-HUD5 note to "frozen reconstruction"; keep the digest as integrity only
   (#14).
