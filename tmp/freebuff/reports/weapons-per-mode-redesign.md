# Weapons per mode — the redesign the 2026-11-08 play facts force

**STATUS: done (report only).** No build, no tune, no ledger row, no queue brief and no other task's
file was edited. `9033` applies this: §5 is the rewrite list, §4 is the replacement `D-7` row, §6 is
the translation-record fallout.

**Provenance / reversibility.** New file, `tmp/freebuff/reports/weapons-per-mode-redesign.md`
= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/weapons-per-mode-redesign.md`. It is the output path
the brief names, and it is the right file because every comparable redesign report in this project
lives in `tmp/freebuff/reports/`. **Revert = delete this file.**

Labels: **decoded** = read at the cited file:line; **derived** = arithmetic or composition over
decoded values, shown; **operator** = the 2026-11-08 play facts, which no file confirms or refutes;
**UNKNOWN** = absent from the named files, with the file or take that would settle it.

---

## 0. Verdict in one screen

| question | answer |
|---|---|
| what changed | D-7's premise ("every weapon in both modes") is contradicted by the play facts: the modes have **different weapon sets** |
| pursuit fire paths needed | **1** — one driver fire action, the EMP missile |
| battle fire paths needed | **at least 2** (RT cannon, RB Vulcan) **plus the barrage**, which needs no press (auto-fires at full lock) but does need its own weapon root and a lock trigger |
| weapons that need no fire path at all | tracker (tracking state), boost (nitro block), barrage (auto-fire), plus the entity-object gadgets (EMP burst is a tap → one path; sonar/hacker/winch are interaction/module paths) |
| briefs that must be rewritten | **8 of 9**: 9103, 9104, 9105, 9106, 9107, 9108, 9109, 9130. **9110 needs no change** — it already states the new rule and is the model the other eight must be aligned to |
| hard contradiction inside the queue | 9105 says the lock/salvo is *pursuit*; 9110 says the barrage is *battle*. The play facts resolve it in **9110's** favour |
| translation rows this re-opens | `T-WP13` (D-7 slot row), `T-WP4`/`T-WP9` (launcher halves), `T-MD2` ("launcher available in both modes (D-7)") |

---

## 1. The facts this report is built on, and where each one comes from

### 1a. Operator play facts (operator, 2026-11-08; recorded in `MODLOG.md` §"Roadmap written", and restated in the brief for this report)

1. **Pursuit fires only the EMP missile (Immobiliser).**
2. **Tracking on/off and boost are pursuit-only, but they are not weapons.** The tracker HUD **persists into battle**.
3. **Battle: RT = the 60 mm cannon** (with a reload circle); **RB = the Vulcan** (crosshairs spread, then turn red, **no lockout**).
4. **The barrage auto-fires at full lock** and **locks 1/4/7/10 targets by upgrade level**.
5. **The EMP burst is a tap with a fixed stun**, and it **permanently disables unarmoured vehicles**.
6. `D-7` ("all weapons in both modes") **contradicts lore and must be re-proposed** (§4).

### 1b. File evidence

| fact | value | source | label |
|---|---|---|---|
| BmAK pursuit bindings | `RT` Accelerate · `RB` Cycle View · `X` Brake/Reverse · `Y` Afterburner · `B` Tracker/Immobilizer · `LT` hold Battle | `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` §"Pursuit mode" | decoded (menu transcription, not bytes) |
| BmAK battle bindings | `RT` 60mm Cannon · `RB` Vulcan Gun · `X` Missile Barrage · `B` EMP · `Y` Drone Virus · `d-pad` Scan/AR/Mission · `LB` exit | same file, §"Battle mode" | decoded (menu transcription) |
| an index is a **fire** path, not a selection | `DrivingMode.SelectVehicleWeapon` calls `ReadyToFire()`, `IsFiring()`, `RVehicleWeapon.TryToFireWeapon()` twice, `RSeqEvent_BatmobileRiddlerButton`; no body stores an active slot | `Working/Translation/T_WP13B.md` §4a, oracle `O9` | decoded |
| BmAK's four gadget indices | 1 → `XboxTypeS_B` `QuickGadgetB` · 2 → `XboxTypeS_X` · 3 → `XboxTypeS_Y` · 4 → `XboxTypeS_DPad_Up` `SelectVehicleWeapon` | `T_WP13B.md` §4a, oracles `O7`/`O8` | decoded |
| JC3 land-vehicle fire actions | `FIRE_VEHICLE_WEAPON_PRIMARY` = RSHOULDER / MOUSE1 · `FIRE_VEHICLE_WEAPON_SECONDARY` = LSHOULDER / MOUSE2; **selector actions `NEXT_WEAPON`/`PREV_WEAPON` are keyboard-only and on-foot**, so land-vehicle selectors = **none** | `T_WP13B.md` §4b, oracle `O10` | decoded |
| free land-vehicle buttons | `USE_VEHICLE_MOD` (d-pad right) and `VEHICLE_RELEASE_GRAPPLE` (d-pad down) | `T_WP13B.md` §4b | decoded |
| driver slots per root | **2** (`main_weapon` id:851CAABE, `secondary` id:00568A74); gunner slots `mounted_weapon`, `mounted_weapon_2`; max 2 driver slots on any of 53 armed graphs | `Working/Translation/T7_WEAPONS.md` §2; `T_WP13B.md` §1 | decoded |
| the four slots the build may write | `main_weapon` + `id:00568A74` on each of **four `CCar` roots** = up to 8 addressable weapon objects; spare pointers `id:8580BA42`, `id:CA86AA17` are null on all 54 roots | `T7_WEAPONS.md` `T-WP13`; `T_WP13B.md` §2, `O5` | decoded (roots/slots) / **UNKNOWN** (whether a spare fires) |
| the tank pair | `main_weapon` → `w602_mediumtank_canon`, `secondary (id:00568A74)` → `w603_mediumtank_mgun` | `T7_WEAPONS.md` §2; `Research/JC3Grab/WEAPON_WIRING.md:305` (quoted in `summon-and-unranked-weapon-plans-v2.md` §6) | decoded |
| the Immobiliser **is** the EMP missile | `RBatmobileEMPMissile` fires `Batmobile_EMPMissile_Projectile_ForCars`; both payload pointers `@2428`/`@2492` resolve to it; `bInstantFire` true `@2464`; socket `BattleModeSpotLight` `@2436`; rotator `-3640` = −19.995° `@2452` | `tmp/freebuff/reports/immobilizer-vs-emp-missile.md` §2/§5, A1-A7 | decoded |
| the tracker is a separate launcher on the same button/socket | `RBatmobileVehicleTracker` fires `Batmobile_Tracker_Projectile` (damage 0, `HomingDelay` 0.2 s); `bInstantFire` absent | same report §3 B1-B4; §6 `T-WP9` | decoded |
| tracking is automatic, not a press | D-11 mapping: "B = immobilizer on an auto-tagged enemy [CONFIRMED live; **tracking is automatic, not B**]" | `GRAB_BACKLOG.md` §11 `D-11` | decoded (live-confirmed operator record) |
| the tracker's marker | yellow `POI_TYPE_MISSION` 19 (`0xFFE717`) while tracked, grey `POI_TYPE_LOCKED` 24 (`0x808080`) otherwise; type fixed at creation → state change = remove + create; distance is a caller string into `MCI_distance.TXT_distance` | `tmp/freebuff/reports/tracker-lock-hud-plan.md` §2/§3/§5 | decoded (AS3) |
| the barrage's BmAK gates | `LockOnAngle` 40.0° `@0x0980`, `LockOnRange` 12000 cm = 120 m `@0x0984`, `FireInterval` 0.5 s `@0x098C`, `MaxTargets` 8 `@0x095C` (**the Joker instance**; the playable launchers set no tag → the playable count is UNKNOWN), `MaxTargetsPerLevel` `@0x0A20` payload undecoded | `tmp/freebuff/reports/lock-hold-salvo-reticle-plan-v2.md` §3.1 W2-W7 | decoded / UNKNOWN |
| the pursuit lock duration | `MissileLockOnDuration` 2.0 s `@0x0A00` (civilian 1.0 `@0x0A04`) — **declared on the pursuit class**; the battle missile launcher has **no duration member** | same report §1/§2 | decoded |
| no JC3 lock timer | `AutoAimSettings` has 22 members, none a duration; `missile_per_shot` is 1 | same report §3.2 D5, §4.2 | decoded (absence) |
| the EMP burst's BmAK numbers | `RBatmobileEMP`: `WeaponCoolDown` 2.0 s; 4 stages; trigger `trigger.use_item` @(0, 1.3507, 2.396) → `S_STUNT_USE_ITEM_VEHICLE`; `DisableEnemyDuration` @2400 / `Range` @2396 serialize **no value** | `tmp/freebuff/reports/emp-immobiliser-forcepulse-plans-v2.md` N1-N12, §2 | decoded (members) / UNKNOWN (values) |
| the EMP burst's JC3 carrier | entity `CForcePulse` + `truck_emp.ftune` (100 / 25 m, radius factors 1/1), the only pulse with the `0,1,1` flag triple; `CEMPWeapon` is **0 of 88** vehicle weapon components | same report N7-N16 | decoded |
| `is_disabled_by_emp` | **0** literal and **0** hash bindings in 1,941 entries / 3.98 GB | same report N17 | decoded (absence) |

---

## 2. The per-mode weapon table

Carriers are named as `T7_WEAPONS.md` (`T-WP<n>`) and `T_WP13B.md` (§5/§6) name them; the fire path is
the driver input that makes the weapon act. Rows are ordered by button, as the menu draws them.

### 2a. Pursuit mode — one fire path

| button | weapon | JC3 carrier (T7_WEAPONS.md · T_WP13B.md) | fire path | label |
|---|---|---|---|---|
| **B** | **EMP missile / Immobiliser** — `RBatmobileEMPMissile` `Batmobile_EMP_Missile_Launcher` + `Batmobile_EMPMissile_Projectile_ForCars` (WPN-4 launcher, WPN-4b disable) | `T-WP4`: a `w618_sportsmuscle_missile` clone (own fire-block values kept) + Fire Leech guidance + a new `AutoAim` (characters 0, cone 0.12/0.15, `MaxAimDistance` 120); the disable half `T-WP15` = pulse + cloned `w702_emp`, composed, not omitted. `T_WP13B` §5 WPN-4 places it on a driver slot; §6 leaves the slot as "shared with WPN-3 / spare" | **the only driver fire path in pursuit**: one land-vehicle fire action (`FIRE_VEHICLE_WEAPON_PRIMARY`, or a remapped equivalent) → the root's `main_weapon` → the missile clone; `SWeaponPoint` at `BattleModeSpotLight` with the −19.995° pitch | decoded (class, socket, instant fire) · derived (slot choice) |
| **B** (tracking on/off) | **Tracker** — `RBatmobileVehicleTracker` (WPN-9), *not a weapon* | `T-WP9`: "closest system: a mounted weapon entity `.ee` plus … a `SWeaponPoint`"; `T_WP13B` §5 WPN-9 = "none decoded"; the part that ships is the **HUD POI** (19/24) + the tag state | **none.** No projectile is fired by the player: tracking is automatic (D-11) and the tag is the acquisition state the missile locks onto. Building it as a launcher on the same button as the missile would put **two projectiles behind one press** | decoded (automatic tracking, D-11) · operator (on/off, not a weapon) |
| **B**'s HUD half | the yellow/grey marker + distance line | `tracker-lock-hud-plan.md` §5: `CreatePoi(POI_TYPE_MISSION …)` / `POI_TYPE_LOCKED`, remove+create transitions; the world→screen transform is native UNKNOWN | none (a HUD element, not an input) | decoded (API) / UNKNOWN (projection) |
| **Y** | **Afterburner / booster** — `RBatmobileBooster` (WPN-11), *not a weapon* | `T-WP11`: `arcade.nitro_boost` on 145/232 vehicles (torque ×2, grip ×2, blend 0.2 s, +40 km/h); `T_WP13B` §5 WPN-11 "no weapon slot – module block" | **none** — boost is a module block driven by its own button, not a weapon slot | decoded |
| RT · RB · X | Accelerate · Cycle View · Brake/Reverse | — (driving, per the menu) | not weapons | decoded (menu) |

**Pursuit total: 1 driver fire path.** The tracker adds a state toggle and a HUD element; the booster
adds a module block. Neither adds a weapon path. `T_WP13B`'s own arithmetic already said this in
another form: "**an index is a fire path, not a selection**" — so a mode that fires one weapon needs
exactly one index live.

### 2b. Battle mode — two decoded paths plus the barrage

| button | weapon | JC3 carrier (T7_WEAPONS.md · T_WP13B.md) | fire path | label |
|---|---|---|---|---|
| **RT** | **60 mm cannon** = WPN-1 Heavy Cannon — `RBatmobileHeavyCannon` `Batmobile_Heavy_Cannon_Primary` | `T-WP1`: `w602_mediumtank_canon` clone on `main_weapon` (id:851CAABE), `SWeaponPoint` at `CannonMuzzle`, `fire_rate` 1.75 → 2.0, `velocity` 500 → 400; reload circle = the HUD cooldown loader (`UC_SetCannonCoolDown` 0…4), 0.467 s per rack (`summon-and-unranked-weapon-plans-v2.md` §1) | **path 1**: `FIRE_VEHICLE_WEAPON_PRIMARY` → `main_weapon` | decoded |
| **RB** | **Vulcan** = WPN-2 — `RBatmobileCannon` `Batmobile_Cannon_V2` | `T-WP2`: `w603_mediumtank_mgun` clone on `secondary (id:00568A74)`, `SWeaponPoint` at `ChainGunMuzzle`; scatter 0.1 → 3.0 over 18.2 rounds, recover 0.35/reset 1.0, no heat member (`summon-and-unranked-weapon-plans-v2.md` §2) | **path 2**: `FIRE_VEHICLE_WEAPON_SECONDARY` → `id:00568A74` | decoded |
| **X** (label only) | **Missile barrage** = WPN-3 — `RBatmobileMissileLauncher` `Batmobile_Missile_Launcher` | `T-WP3`: `w618_sportsmuscle_missile` clone (+ `w614_monorailmissilecar_missile` as the guided/salvo donor, `summon-and-unranked-weapon-plans-v2.md` §4.2); `T_WP13B` §5 WPN-3 = spare `id:8580BA42` or shared slot, status "derived" | **no press**: auto-fires at full lock (operator). Needs its own weapon root (a third `CCar` root's `main_weapon`, `T-WP13`) **and** a lock→fire trigger, which no member carries (`AutoAimSettings` 22 members, none a timer; the HUD type-21 POI has 0 creators) | decoded (carrier, gates) · operator (auto-fire, 1/4/7/10) · UNKNOWN (the auto-fire trigger) |
| **B** | **EMP burst** = WPN-5 — `RBatmobileEMP` `Batmobile_EMP_Burst` | `T-WP5`: entity `CForcePulse` + `truck_emp.ftune` + the `0,1,1` flags; the disable half is the cloned `CEMPWeapon` `w702_emp` (`T-WP15`/B-18) | **path 3 (new)**: a tap. No land-vehicle action is free for it — both decoded vehicle fire actions are RT/RB's, `USE_VEHICLE_MOD` is the winch and `VEHICLE_RELEASE_GRAPPLE` is d-pad down. A new scoped action is the amendment | decoded (carrier) · operator (tap, fixed stun, permanent on unarmoured) · UNKNOWN (the button) |
| **Y** | **Drone Virus** = WPN-7 — `RBatmobileAllegianceSwitcher` | `T-WP7`: `SAttachedEffect` beam on the drone-side entity + the SAM context-act interaction graph; `T_WP13B` WPN-7 "none decoded" | **interaction, not a fire path**: `CInteractionGraph` + `CInteractionTrigger` + `rico_contextact_hack_sam*` | decoded (closest system) / UNKNOWN (the side flip) |
| **d-pad (Scan)** | **Seismic sonar** = WPN-8 — `RBatmobileSonar` | `T-WP8`: `CForcePulse` with `gen_explosion_5m_nodamage.ftune` (0 / 5 m) + an authored ring `.effc` + the `BML_Sonar` bank | **path 4 (new)**: a d-pad arm; no decoded land-vehicle action exists | decoded (carrier) / UNKNOWN (button scoping) |
| **d-pad right** | **Power winch** = WPN-6 — `RBatmobileWinch` | `T-WP6`: `CVehicleCargoBay`-style anchor at `WinchOrigin` + `transport_rope_winch` drum + Rico's tether runtime | **`USE_VEHICLE_MOD`** already sits on d-pad right (operator decision 2026-11-05 takes it for the winch) | decoded (button) / UNKNOWN (vehicle-side attach/reel/release) |
| — (no menu row) | **Riot mode** = WPN-10 — `RBatmobileCannon` riot fields | `T-WP10`: a private bullet tune with `base_tuning.damage` 0 + high impulse; a second weapon entity (`Research/specs/B-15.md`) | **path 5 (new)**: no button, no slot. A second entity on a third root | derived / UNKNOWN (toggle) |

**Battle total: 2 decoded driver fire paths (RT, RB) + the auto-fired barrage + 3 further paths battle
needs and JC3 does not ship (EMP burst tap, sonar, riot) + 2 non-fire interaction paths (hacker, winch).**
That is why the brief's "at least two plus the barrage" is the right floor and not the ceiling.

### 2c. What grew and what shrank

| mode | weapons the mode *fires* | distinct driver paths | notes |
|---|---:|---:|---|
| pursuit | 1 (EMP missile) | **1** | tracker = state, booster = module block |
| battle | 3 by button (cannon, Vulcan, barrage) + 1 tap (EMP burst) | **2 + barrage** (≥ 3) | the barrage needs no press but needs a root + a lock trigger |

Under D-7's old text both modes needed **all 11** weapons and therefore every path in the table: pursuit
would have needed a cannon, a Vulcan, a barrage, an EMP burst, a hacker, a sonar and a winch it never
fires. The play facts delete that requirement, and with it the reason `T-WP13` was forced to invent
**8 slots across 4 roots**.

---

## 3. Why pursuit needs exactly one path, and battle at least three — the argument, not the assertion

1. **An index is a fire path** (`T_WP13B` §4a, `O9`): pressing a button calls `TryToFireWeapon`; nothing
   selects. So "how many fire paths does a mode need" is exactly "how many distinct weapons does that
   mode fire, plus what it auto-fires".
2. **Pursuit fires one weapon** (operator 1). The tracker is a tracking state, not a shot (operator 2,
   and D-11's live confirmation that tracking is automatic); the booster is a module block (`T-WP11`).
   One weapon ⇒ **one path**. Nothing else in the pursuit menu is a weapon: RT/RB/X are accelerate,
   cycle view and brake.
3. **Battle decodes two fire actions and uses both**: `FIRE_VEHICLE_WEAPON_PRIMARY` (RSHOULDER/MOUSE1)
   and `FIRE_VEHICLE_WEAPON_SECONDARY` (LSHOULDER/MOUSE2) are the only land-vehicle fire actions in the
   shipped keymap (`T_WP13B` §4b, `O10`). RT and RB are the two guns (operator 3), so the two decoded
   actions are exactly enough — one each.
4. **The barrage is a third path that carries no button**: it auto-fires at full lock (operator 4), so it
   needs no decoded fire action at all, but it still needs (a) a weapon object behind a slot the engine
   fires — a third `CCar` root's `main_weapon`, the `T-WP13` composition — and (b) the thing that turns
   a held lock into a shot, which is **UNKNOWN** on both sides (no `AutoAimSettings` timer, no type-21
   POI creator, no `DrivingMode` branch that fires without a press).
5. **Battle's remaining buttons are paths JC3 does not ship** (EMP burst tap, sonar d-pad, riot mode) and
   two interaction shapes (hacker, winch). They are counted, not waved away — that is why the brief says
   "at least" two plus the barrage.
6. **The two modes can share the same two paths** because the modes are two entity variants (D-2 (a)),
   not two input layouts: the pursuit variant's `main_weapon` is the EMP missile, the battle variant's is
   the cannon. Same action, different bound weapon. So pursuit's single path is **one of the two
   already-shipped actions** — the redesign adds no input surface, it removes one.

Two honesty notes: (a) the *default* gamepad buttons for the two decoded actions are the bumpers, while
BmAK's cannon is on the right trigger, so a **rebind/scope amendment** is still required to reach RT/RB/B
(D-11 already rules BmAK's controls win inside the car, and native input scoping was permitted on
2026-11-08); (b) whether the engine fires a weapon behind a third root at all is still the
`id:8580BA42` experiment, unchanged by this report.

---

## 4. D-7, re-proposed

Current row (`GRAB_BACKLOG.md` §11, line 1801), verbatim:

> | D-7 | Weapon slots: which BmAK weapons take JC3's driver slots (cannon, Vulcan, missiles…) | G2-11 | **resolved 2026-10-28 (user): every BmAK weapon in both battle and pursuit modes** — no per-mode split; the slot count must carry all weapons (T-11 finds how, e.g. extra driver slots or mode-independent switching) | T-11 |

**Why it must be re-proposed.** Its two clauses are both refuted by play: there **is** a per-mode split
(the modes fire different weapons), and the slot count therefore does **not** have to carry all 11 in
either mode. Nothing in the files ever supported "all weapons in both modes" — `T-WP13` had to invent
four roots and eight slots to obey it, and `Research/challenge/card-T-15.md` A11 already recorded the
claim "the launcher is available in both modes (D-7)" as **BROKEN**.

Proposed replacement row (for `9033` to apply; operator answer required, so the row is a proposal):

> | D-7 | Weapon slots: which BmAK weapons take JC3's driver slots, **and are they mode-gated?** | G2-11, `OPERATOR_PRIORITIES.md`, the 2026-11-08 play facts | **RE-PROPOSED 2026-11-08 (operator facts): weapons are gated by mode, not duplicated.** Pursuit fires the **EMP missile alone** (tracker = tracking on/off + the marker, which persists into battle; boost = the `nitro_boost` block); battle fires the **60 mm cannon (RT)**, the **Vulcan (RB)** and the **missile barrage (auto-fires at full lock)**, plus the **EMP burst tap (B)** and the interaction gadgets. Slot arithmetic: pursuit **1** driver slot; battle **2** driver slots + **1** auto-fired weapon root; the rest of battle's gadgets are entity objects or new paths. Supersedes "every BmAK weapon in both battle and pursuit modes" and retires `T-WP13`'s forced 8-slot composition. | T-11 (`T-WP13`, `T-WP4`, `T-WP9`), T-MD2, WPN-1…WPN-11 |

**What the re-proposal changes downstream** (each of these is a row whose claim flips, and none of them
is edited here):

| row / file | today | after the re-proposal |
|---|---|---|
| `T7_WEAPONS.md` `T-WP13` | "**forced**: … Build **four `CCar` roots** … = **8 slots** for the 8 slot-able BmAK objects" | 2 slots + 1 auto-fire root in battle, 1 slot in pursuit; four roots become an option, not a requirement |
| `T7_WEAPONS.md` §2 D-7 table | "how do all 11 weapons take JC3's driver slots, **in both modes**?" / "`T-WP13` is `blocked`, not `out`" | the question is per-mode; `T-WP13` becomes `next` (composition known), not `blocked` |
| `T7_WEAPONS.md` `T-WP4` slot cell | "pursuit-mode missile gadget … T-WP13 owns the count" | pursuit-only by lore, `main_weapon` of the pursuit variant |
| `T7_WEAPONS.md` `T-WP9` | "closest system: a weapon entity with the tracker tune on the `BattleModeSpotLight` socket" | the tracker is a tracking state + POI; no projectile slot |
| `T-MD2` (`T11_MODES.md`) | "the launcher is available in both modes (D-7)" | "**pursuit only**; battle's missile is the barrage" (`card-T-15.md` A11 asked for exactly this) |
| `Tools/scripts/t7_weapons.py` | `T-WP13` aspect text encodes "every weapon in both modes" | generator must be re-run after its text changes — **not this report's work** |

---

## 5. Briefs that must be rewritten (9103-9110, 9130)

Each entry names the brief file, quotes **the sentences to change verbatim**, and gives the replacement
in one line. Everything not quoted stands.

### 9103 — `tmp/freebuff/queue/9103-rc5-tracker-launcher-and-marker.txt` — **rewrite**

> "Rank one of the operator's weapon list, first half: the tracker (RBatmobileVehicleTracker), the part without which the EMP missile does not work."

The tracker is no longer a ranked *weapon* (the operator's ranking pairs it with the missile, but the
2026-11-08 facts make tracking a state). Replace with: "Rank one's acquisition half: the tracker
(`RBatmobileVehicleTracker`) — the tracking state the EMP missile locks onto. It is **not a weapon** and
does not occupy a fire path."

> "Build the launcher on the same button and socket as the missile with its private tune, the 30.0 degree fire position, and the target marker as a HUD POI:"

This is the sentence that breaks the single-path rule: a launcher on the same button as the missile is
two projectiles behind one press. Replace the clause "Build the launcher on the same button and socket
as the missile with its private tune, the 30.0 degree fire position" with: "Build the tag as a **state**
on the same socket as the missile (`BattleModeSpotLight`, 30.0° = 5461 rotator units) with no fire
path — tracking is automatic (D-11) and the player toggles it; the marker as a HUD POI:".

Also add, in the same brief: the marker **persists into battle** (operator 2026-11-08), so the POI
driver ships in the shared/pursuit tree and must survive the variant swap. The rest of the paragraph
(`POI_TYPE_MISSION` 19 / `POI_TYPE_LOCKED` 24, the `0xFFE717`/`0x808080` arrows, `MCI_distance.TXT_distance`,
remove-and-create) is correct and stays.

### 9104 — `tmp/freebuff/queue/9104-rc5-emp-missile.txt` — **rewrite (one clause)**

> "Mount it as reports/immobiliser-launch-payload-build-plan.md and reports/emp-immobiliser-forcepulse-plans-v2.md direct, on the slot map that 9101 delivered."

"On the slot map" is mode-blind: the same `main_weapon` the missile needs is the cannon's slot in battle.
Replace with: "…direct, on the slot map that 9101 delivered, **on the pursuit variant's `main_weapon`
only** — battle's `main_weapon` is the 60 mm cannon (9110), so the missile must not be left bound in the
battle variant."

> "The lock hold and salvo belong to a later brief; do not invent them here."

Keep the sentence but fix the referent: the **salvo is battle's** (see 9110/9105), so the deferred part
is the pursuit lock circle only. Replace with: "The pursuit lock circle belongs to a later brief
(9105); do not invent the barrage or the salvo here — they are battle's (9110)."

### 9105 — `tmp/freebuff/queue/9105-rc5-lock-hold-salvo-reticle.txt` — **rewrite (this is the hard contradiction)**

> "Pursuit carries one fire slot and the lock/salvo is that slot's weapon (operator 2026-11-08), so the reticle and the salvo are pursuit behaviour, not a battle one."

This is refuted twice: by operator fact 1 (pursuit fires only the EMP missile) and by 9110's own
battle-only gating of the barrage, and it contradicts `CONTROLS_MENU_SCREENS.md` (`X | Missile Barrage`
is drawn on the **battle** menu). Replace with: "Pursuit carries one fire slot and that slot's weapon is
the **EMP missile**, whose **2.0 s acquisition** is the pursuit circle (`MissileLockOnDuration`, declared
on `RBatmobileEMPMissile`); the **salvo is battle behaviour** (`X | Missile Barrage`), so the held lock
that ends in a salvo is battle's and the shrinking circle is pursuit's."

> "Updated by review v2-apply (2026-11-08): autofire at full lock, 1/4/7/10 targets by level, decoded MaxTargets 8 kept as a conflict, pursuit-only slot"

The trailing clause is the same error in the header line. Replace "pursuit-only slot" with
"battle-only salvo, pursuit circle".

> "Build per reports/lock-hold-salvo-reticle-plan-v2.md: the pursuit circle that shrinks over the lock time and the battle instant diamond as two reticle behaviours, the target selection (crosshair-nearest first) as far as AutoAim can carry it, and the composed salvo at the lore maximum of ten rounds, with the decoded MaxTargets 8 carried beside it."

This survives — the v2 report's §1 already separates the two reticles exactly this way — but the salvo
must be bound to the battle tree, not here. Add one clause: "…the composed salvo **in the battle variant
(`Builds/bm-RC5-weapons`, 9110)** at the lore maximum of ten rounds…".

### 9106 — `tmp/freebuff/queue/9106-rc5-booster-mesh.txt` — **rewrite (mode gate + ranking)**

> "Rank two: the booster."

The operator called the booster rank two **of the weapon work**; the 2026-11-08 facts say boost is
**pursuit-only and not a weapon**. Replace with: "Rank two: the booster — **pursuit-only**, and not a
weapon (operator 2026-11-08), but still rank two in the weapon work order."

> "drive the deploy from the nitro state with the nearest animation driver named in the v2 plan"

Un-gated: the deploy must exist only where the nitro block exists. Replace with: "drive the deploy from
the nitro state with the nearest animation driver named in the v2 plan, **in the pursuit variant's
`arcade.nitro_boost` block only** — battle carries no boost (D-10 also forbids JC3 nitro tiers)."

Nothing else in 9106 changes: the 18 nozzles, the ring geometry, the 0.600 s / 0.833 s poses and the
budget line are mode-free.

### 9107 — `tmp/freebuff/queue/9107-rc5-emp-burst-and-disable.txt` — **rewrite (slot collision + the new stun facts)**

> "a private clone of w702_emp.wtunec, the CEMPWeapon-bearing entity on the second driver slot of the 9101 map, an entity CForcePulse with truck_emp.ftune"

"Second driver slot" is **the Vulcan's** (`id:00568A74` → `w603`, `T-WP2`/9110), so this sentence builds
two weapons into one slot. Replace with: "a private clone of `w702_emp.wtunec` on a **third `CCar`
root's `main_weapon`** (the `T-WP13` composition; the second driver slot is the Vulcan's), an entity
`CForcePulse` with `truck_emp.ftune`".

> "The disable half must be composed, not left out: use the route the v2 plan names and write the missing capability as an exact card if no member exists, because is_disabled_by_emp has zero bindings in 1,941 entries."

Correct as far as it goes, but it now carries a lore requirement the brief does not state. Add after
it: "The operator's 2026-11-08 facts fix the shape: the burst is a **tap** with a **fixed stun**, and it
**permanently disables unarmoured vehicles** — so the duration is not the tier array
`[2, 4, 8, 12] s` for unarmoured targets, and the armour gate needs the target's armour class
(`electricity_armor` is decoded per vehicle; which member keys 'unarmoured' is UNKNOWN)."

### 9108 — `tmp/freebuff/queue/9108-rc5-hacker-and-sam-hack.txt` — **rewrite (mode gate)**

> "Build in Builds/bm-RC5-hacker: the beam attachment rows with the magenta beam, the success feedback, the interaction shape on a SAM site and on a drone, and the flip of the target's side by the closest member the SAM data shows."

No mode. `Y | Drone Virus` is drawn on the battle menu only. Replace the opening with: "Build **battle
only** (Y = Drone Virus; pursuit carries no hacker) in Builds/bm-RC5-hacker: …".

### 9109 — `tmp/freebuff/queue/9109-rc5-sonar-pulse.txt` — **rewrite (mode gate)**

> "Rank five: sonar, the lowest-ranked weapon."

Same gap: `Scan` is a **battle** d-pad arm; the pursuit d-pad draws only AR Challenges and Mission Select.
Replace with: "Rank five: sonar, the lowest-ranked weapon — **battle only** (Scan is on the battle d-pad
arm; the pursuit d-pad has no Scan)."

### 9110 — `tmp/freebuff/queue/9110-rc5-cannon-vulcan-riot-pods.txt` — **no change**

This brief already carries the new rule and is the reference the other eight must match:

> "The cannon, the Vulcan and the riot pods are battle-only: pursuit fires the EMP missile and nothing else (operator 2026-11-08), so every set written here is gated to battle."

> "Missile pods and barrage: auto-fire at full lock, targets 1/4/7/10 by upgrade level (build 10), with the decoded 8 recorded beside the conflict, reports/missile-pod-salvo-plan.md."

> "Binds (operator 2026-11-08): RT = cannon, RB = Vulcan."

One thing 9110 does **not** say and should not be read as saying: it does not give the barrage a button.
`X | Missile Barrage` is the menu label; the fire is lock-driven, so 9110's "auto-fire at full lock" and
9105's salvo work must agree on that (they do once 9105 is rewritten).

### 9130 — `tmp/freebuff/queue/9130-rc5-mode-pair-and-swap.txt` — **rewrite (one clause)**

> "Operator facts of 2026-11-08 change the pair's content: pursuit carries the EMP missile alone while battle carries the rest, so the two variants must differ in their weapon sets and not only in their handling;"

Correct, and it is the sentence the whole redesign rests on. Keep it.

> "Rebuild the pair on the RC5 base with the pursuit and battle variant tables from 9121 and 9122, the transformation stance T-MD13, the turn on the spot T-MD8, and the battle audio switch T-MD14"

Wrong source list: 9121 (suspension travel) and 9122 (drive modes and yaw) are **handling** briefs and
carry no weapon-set table, so the sentence sends the variant's weapon half nowhere. Replace with:
"Rebuild the pair on the RC5 base with the **weapon sets from 9103-9110** and the **handling tables from
9121 and 9122**, the transformation stance T-MD13, the turn on the spot T-MD8, and the battle audio
switch T-MD14".

Also add to its Done line, because the swap now carries two different weapon sets: the `aafdiff` between
the variants must list the **weapon** files as well as the handling ones, and the pursuit variant must
show **one** bound driver weapon where the battle variant shows two plus the barrage root.

---

## 6. What 9033 must carry into the translation record (no edits made here)

| file | change needed | why |
|---|---|---|
| `GRAB_BACKLOG.md` §11 `D-7` | apply §4's replacement row (operator answer pending) | the decision text is contradicted by play |
| `Working/Translation/T7_WEAPONS.md` | regenerate after `Tools/scripts/t7_weapons.py`'s `T-WP13`/`T-WP4`/`T-WP9` text changes — **the generator, never the output** | the output is byte-for-byte generated (`--check` re-derives it) |
| `Working/Translation/T11_MODES.md` / `T-MD2` | "available in both modes (D-7)" → pursuit-only | `card-T-15.md` A11 |
| `Research/challenge/card-T-15.md` A11, `card-T-11.md` A9 | these audits *predicted* this; cite this report as the resolution | the audits must not be re-litigated as new findings |
| `tmp/freebuff/reports/weapons-ranking-build-order.md` §1 step 4 ("W1d lock hold + reticle") | its gate "8 targets acquire in the cone" is battle's, its "2.0 s fill" is pursuit's | same reticle split as 9105 |

---

## 7. UNKNOWNs

| # | what is unknown | what was tried | what settles it |
|---|---|---|---|
| U1 | **the barrage's auto-fire trigger** — nothing turns "full lock" into a shot | `AutoAimSettings` 22 members (no timer); HUD type-21 POI has 0 creators in 260 AS3 scripts; `DrivingMode` fires only on a press | a native hook / the RC5 probe: hold the reticle on 2 targets and see whether a shot leaves without a press |
| U2 | **whether a third `CCar` root (or a spare `id:8580BA42`) fires a weapon at all** | 54/54 roots carry the spares, **0** non-null; max 3 weapon components on one entity already ships | 5-minute test: point a spare at a copied `w602` and fire |
| U3 | **the EMP burst's button** — a tap needs an action, and both land-vehicle fire actions and the two free buttons are taken | keymap read: `FIRE_VEHICLE_WEAPON_PRIMARY/SECONDARY`, `USE_VEHICLE_MOD` (winch), `VEHICLE_RELEASE_GRAPPLE` (d-pad down) | a scoped input action (native input scoping permitted 2026-11-08), or an operator button decision |
| U4 | **"unarmoured" as a target class** — the permanent-disable gate | `is_disabled_by_emp` 0 bindings in 1,941 entries; `electricity_armor` decoded per vehicle (medium tank −1 @ strength 100) | the probe: EMP an armoured and an unarmoured vehicle and compare |
| U5 | **the playable barrage's target count** — 8 is the Joker *instance*, the playable launchers set no tag | `lock-hold-salvo-reticle-plan-v2.md` §3.1 W2 | operator observation already says 1/4/7/10; the decoded 8 stays beside it as a conflict |
| U6 | **the tracker marker's projection** — POIs take stage pixels, no world→screen in the movie | `tracker-lock-hud-plan.md` §1/§6 | a native POI caller trace, or a taken marker position over a moving target |

---

## 8. Commands run, and what this report did not do

Read-only this pass (no game process, no install, no build, no queue edit, no ledger edit):

```
# evidence reads (paths quoted throughout §1b)
Working/Translation/T7_WEAPONS.md
Working/Translation/T_WP13B.md
GRAB_BACKLOG.md                                   # §11 decision register, D-7 at line 1801
MODLOG.md                                         # "Operator gameplay facts (2026-11-08)"
Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md
tmp/freebuff/reports/immobilizer-vs-emp-missile.md
tmp/freebuff/reports/tracker-lock-hud-plan.md
tmp/freebuff/reports/lock-hold-salvo-reticle-plan-v2.md
tmp/freebuff/reports/emp-immobiliser-forcepulse-plans-v2.md
tmp/freebuff/reports/summon-and-unranked-weapon-plans-v2.md
tmp/freebuff/reports/weapons-ranking-build-order.md
OPERATOR_PRIORITIES.md
tmp/freebuff/queue/9101..9110, 9130 (brief texts quoted verbatim in §5)
ls tmp/freebuff/reports | grep -i per-mode   -> cameras-per-mode-plan.md only (no prior report on this)
```

**Not done, deliberately:** no tune, `.epe`, `.ee`, `.toc`, `hud.gfx` or install file was written; no
`Builds/` tree was created or touched; no queue brief was moved or edited; `T7_WEAPONS.md` was **not**
hand-edited (it is generated); `APPROVED_Q.txt` was not created.

**COMPROMISES:** none. Nothing in this redesign asks lore to give way — it removes a requirement that
lore never made (all weapons in both modes) and names the missing capabilities (U1-U6) as probes/cards
rather than omissions.
