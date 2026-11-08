# Assumption challenge — card T-11 · Weapons translation

Written 2026-10-30. **Read-only review**: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/`, `Working/`, `Builds/` or any game file was modified; the only file written is this one.
No game was launched, nothing was written to `D:\Games`, nothing was committed, no secret was read.
Every command below is a read (`--check` writes nothing) or an in-memory Python heredoc; no probe
script was left on disk.

**In scope**, as the card requires: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–77), the T-11 card
(lines 863–877), its §12 row (line 1320), the MODLOG section `## T-11 · Weapons translation — done
(2026-10-28)` (line 13160), and the card's outputs — `Working/Translation/T7_WEAPONS.md` (496
lines), `Working/Translation/t7_weapons_edits.json`, `Tools/scripts/t7_weapons.py` (1,424 lines).
Cross-checked against the card's own `In:` files (`Research/BatmobileGrab/WEAPONS.json`,
`Research/JC3Grab/WEAPONS.jsonl`, `WEAPON_WIRING.md/.jsonl`, `SIGNATURE_DIFF.md`, `TURRET.md`,
`EMP.md`, `DAMAGE_MODEL.md/.json`), plus `SOCKETS_JC3.json`, `HUD_INTERFACES.json`,
`JC3_HUD_WEAPONS.json`, `FORCEPULSE.json`, `FEATURE_CENSUS.json`, `USAGES.json`,
`MOVING_PARTS.json`, `ENTITIES.md`, `VOCABULARY.md`, `T10_DAMAGE.md` and `G2X.md`.

**Card as written:** 12 WPN codes × 12 aspects, "Done: every WPN code has rows or a named omission;
every value cell has a class; every row's verify cell names a Q-3 check from §9 with a numeric
pass." Out: `T7_WEAPONS.md` + rows (doc `T-7`) + `t7_weapons_edits.json`.

---

## VERDICT

**The decode is largely sound and unusually well classed; the carrier choices and the absence
proofs are not, and the Done gate is red on disk today.** The BmAK numbers reproduce almost
exactly (FiringInterval 2.0 / 0.138, Speed 40000, Damage 50, Pawn.Health 1200, LockOnAngle 40,
LockOnRange 12000, LaunchRotationOffset −3640), the JC3 numbers reproduce (fire_rate 1.75 / 0.1,
damage 190, 1500-in-8 m blast, 2000 tank health, 4 fire points, 2 clips, 14 reticles, 307 pulses,
14 unowned, 145/232 nitro), and the card's own tallies recompute exactly (14 rows, 136 aspects =
72 + 53 + 7 + 4). What does not survive: three claims are false as written (a `GatlingGun` part
on the buggy, "extra root pointer (absent)", the "no overheat" take), one class is overstated
(`decoded` on a fire point whose rotation is missing), one requirement is silently reversed
(guided missiles → unguided, against R1), one count is typed and wrong (175 tune rows), and
`--check` exits 1.

| # | assumption | verdict |
|---|---|---|
| A1 | the Done gate (`t7_weapons.py --check`) is green and the delivered doc is reproducible | **BROKEN** — exit 1, md differs in 3 places; the MODLOG's "verbatim" PASS block quotes a superseded revision |
| A2 | `Pawn.Health` 1200 ÷ `Projectile.Damage` 50 = 24 hits, ratio carried by T-14's `max_health` 36000 | **HOLDS** — both values decoded, T-14 carries 36000 |
| A3 | w602's 1500-in-8 m blast is what a vehicle takes (the shell's own `damage` is 1.0) | **HOLDS** via G2-28's `channel: explosion`, with a stated caveat |
| A4 | `FiringInterval` (s) = JC3 `fire_rate` (s), 1:1 | **HOLDS** for the member; **WEAK** — `fire_rate_level_2` is untouched and inverts the order |
| A5 | `Projectile.Speed` 40000 UU/s → `velocity` 400 m/s (÷100) | **HOLDS as declared `derived`**; **WEAK** — the tune also carries `tracer_fire_velocity` 900 and only `velocity` is edited |
| A6 | the weapon point is `decoded` including `forward [0,0,−1]` | **BROKEN as a class** — `rotation_missing: true` on all three muzzle sockets; that forward is the identity fallback |
| A7 | `w619_buggy_mgun` is "the only driver-fired car MG with a `GatlingGun` part" | **BROKEN** — the buggy has no parts at all; `GatlingGun` is on a boat and two helicopters |
| A8 | the fleet's maximum is 2 driver slots (D-7's premise) | **HOLDS** — 53 armed entities, max 2; land = medium + Bavarium tank |
| A9 | D-7's options: "extra root pointer (absent), a switching action (absent), or 2 slots" | **BROKEN as worded** — the root carries four weapon pointers, two of them named gunner slots; what is absent is a third *driver* pointer and any switch |
| A10 | `secondary (id:00568A74)` is a driver slot | **HOLDS on behaviour** (no gunner seat on the tank); **WEAK on the label** — the name is recorded as "no name found" |
| A11 | WPN-6…WPN-10 are proven absences of the carrier | **HOLDS as word searches** (0/0 reproduced); **WEAK on scope** — the "103-class census" does not reproduce, and rope/aim-POI/lock-on machinery exists under words the search did not use |
| A12 | the Vulcan has no overheat on either side (`HeatUpPerSecond` 0.0 → `decoded`) | **BROKEN as a class and as a take** — overheat sound, cooled sound, `OverheatOffValue` 0.25 and a heat-bar geometry all ship; the take cannot fail |
| A13 | WPN-3's missile stays unguided ("the donor's own") | **BROKEN against R1/R5** — the fleet ships `missile_turning_speed` 75/150/250 (w609 is `air_lockon`) and BmAK locks at 40° |
| A14 | the WPN-3 take: "4 missiles leave the two pods" | **WEAK** — `missile_per_shot` 1, `burst_count` 1, no edit to the per-shot count |
| A15 | "7 carriers, 175 decoded tune rows" | **WEAK** — the count is a typed literal; the tune has 171 weapon rows (+8 blast rows) |
| A16 | §1's "player damage / radius" column: UNKNOWN for w603/w619 | **WEAK** — the column reads the blast only; §4 of the same doc prints `damage` 190 |
| A17 | the fleet-wide constants (25 ids, 53 armed, 307 pulses, 145/232 nitro, 2 clips, 14 shapes, 0 heat params) | **HOLDS** — all recomputed |
| A18 | `BattleModeSpotLight` is used as the EMP missile's fire point though it is not a muzzle | **HOLDS as a recorded donor-faithful choice**; WEAK — a light bone with a missing rotation |
| A19 | the card's own tallies (14 rows; 136 aspects; 5/6/3; 3 edits + 6 structural + 6 withdrawn) | **HOLDS** — recomputed; the dispositions match the ledger |
| A20 | the "no charge member" withdrawal (`ChargeUpTime` 2.5 s) | **HOLDS** — 0 charge members in the 25 tunes |

**Bottom line:** fix the six BROKEN items before T-19/B-05/B-06 consume the rows — the `--check`
failure first (it is the card's own Done gate), then the GatlingGun cell, then D-7's third option,
then the `decoded` fire point, then the unguided missile decision (a requirement regression, not a
typo), then the heat take (which cannot fail). The WEAK items are record-quality issues that a
small model will read literally.

---

## A1 · The Done gate is green, and the doc on disk is reproducible

**The result rests on:** `GRAB_BACKLOG.md` §0.2 step 6 ("run the **Done when** check, paste its
output summary into MODLOG") and R11 ("counts are generated, never typed … a script with
`--check`"), plus the MODLOG block "Done check (verbatim, exit 0)".

**Test.**

```
$ python Tools/scripts/t7_weapons.py --check ; echo EXIT=$?
FAIL: md differs: @@ -80,3 +80,3 @@ ... @@ -258,7 +258,7 @@
EXIT=1
```

Re-derived in memory to see every difference (no writes):

```
$ python - <<'EOF'
import importlib.util,difflib
spec=importlib.util.spec_from_file_location("t7","Tools/scripts/t7_weapons.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.render_md(m.build())  vs  open("Working/Translation/T7_WEAPONS.md").read()
EOF
gen lines 496 disk lines 496
@@ -80,3 +80,3 @@   (row table, T-WP6 carrier cell)
- ... **proven absence** - rope/winch geometry ships on 4 entities (10 part names) but no winch/rope/tow module type and 0 winch classes: ...
+ ... **proven absence** - no winch member path in the 52-type / 1,421-path vocabulary and no winch class in the 103-class fleet census (0 occurrences in both, measured); rope/winch geometry ships on 4 entities (TETHER.md §4) but ...
@@ -258,7 +258,7 @@  (same two sentences repeated in §4, plus the `*carrier*` note)
diff lines 25
```

So three regions of the delivered doc are stale relative to the generator: the tool now claims a
*measured* 0/0 scan against `VOCABULARY.md`/`ENTITIES.md`, while the file still cites `TETHER.md`
and the weaker wording. `--check` is the only guard that the numbers and the prose agree, and it
is red.

The MODLOG's quoted PASS line is also not what this tool prints:

```
MODLOG:   PASS: 14 rows = 12 WPN codes + 2 decision rows (5 with a JC3 carrier, 5 named omissions, 4 blocked) …
tool now: PASS: 14 rows = 12 WPN codes + 2 decision rows (5 with a JC3 carrier, 6 named omissions, 3 blocked) …
```

(`tmp/t7bak/T7.md:10` still contains `5 (5 named omissions, 4 blocked: T-WP4, T-WP5, T-WP13,
T-WP14)`, i.e. the pasted output belongs to the 06:49 revision where T-WP14 was `blocked`; by
23:38 T-WP14 had become `out` and the §12 row was updated, the MODLOG was not.)

**Verdict: BROKEN.** The card's Done condition is not met on the delivered artifacts, and the
journal's evidence line no longer matches the tool it claims to quote. This is not a value error —
`t7_weapons_edits.json` and the ledger cross-check still pass (the failure is the md alone) — but
`--check` red is exactly the state §0.7 says stops work.

---

## A2 · 24 BmAK hits, and the 24:2 ratio carried by `max_health` 36000

**The result rests on:** "`Health` 1200 / `Damage` 50 = **24 shell hits**" (T-WP1) and "the ratio
24:2 = 12x is carried by the **health** row (T-14 needs `max_health` 36000), never by the weapon's
damage".

**Test.**

```
$ python - <<'EOF'   # BmAK side
D=json.load(open("Research/BatmobileGrab/DAMAGE_RULES.json"))
[damage_values with value 1200]
EOF
{"class": "RVehicleBatmobile", "archetype": "Playable_Batmobile_SF.Batmobile", "name": "Pawn.Health", "type": "IntProperty", "value": 1200}
{"class": "RVehicleBatmobile", "archetype": "Playable_BatmobileMK2_SF.Batmobile_MK2", "name": "Pawn.Health", "value": 1200}
{"class": "RVehicleBatmobile", "archetype": "Playable_BatmobileFunhouse_SF.BatmobileFunhouse", "name": "Pawn.Health", "value": 1200}

$ python - <<'EOF'   # the projectile the heavy cannon fires
WEAPONS.json → Batmobile_Heavy_Cannon_Primary_Projectile
EOF
Projectile.Speed 40000.0 · Projectile.MaxSpeed 48000.0 · Projectile.Damage 50.0 · Projectile.DamageRadius 0.0
```

1200 ÷ 50 = 24 exactly, both operands decoded, and `DamageRadius 0` means a direct hit (no blast)
on the BmAK side — so the ratio is a pure direct-hit count. The receiving end is on disk:

```
$ grep -n "36000" Working/Translation/T10_DAMAGE.md
15:| `max_health` for that ratio | **36000** (H0; H1 18000, H2 35750) — shipped domain 500..4000 |
137:| T-DM1 | `max_health` | **edit** | 2000 | 36000 | 500..4000 | next |
```

**Verdict: HOLDS.** The arithmetic, both operands, the "no blast on the BmAK side" and the
hand-off target (T-14's `max_health` 36000) are all on disk. The only soft spot is inherited from
T-14: 36000 is 9× the fleet ceiling and is declared a switch there, and the 2-vs-3-hits count
depends on T-14's H0/H1/H2 model (`explosion` armour 250 / strength 50 on the medium tank).

---

## A3 · "1500 in 8 m" is what a vehicle takes, although the shell's own `damage` is 1.0

**The result rests on:** "a shell (1500 in 8 m) kills a stock tank in 2 hits (H0/H2) / 3 (H1)"
and "blast 1500 in 8 m (its own `ForcePulseSettings` bundle)".

**Test.** The w602 tune, read whole:

```
$ python - <<'EOF'  # Research/JC3Grab/WEAPONS.jsonl → w602_mediumtank_canon
for p,ty,v in inst["rows"]: ...
EOF
bullet_weapon[0].tuning.base_tuning.damage                      1.0
bullet_weapon[0].tuning.base_tuning.vehicle_damage_factor      1.0
bullet_weapon[0].tuning.bullet_is_explosive                    1
bullet_weapon[0].tuning.bullet_base_tuning.tracer_fire_velocity 900.0
velocity 500.0 · fire_rate 1.75 · max_range 1000.0 · fire_rate_level_2 0.12
-- tune w602_mediumtank_canon.ftune 8 rows
   PlayerDamage 1500 · PlayerDamageRadius 8.0 · AIDamage 550 · AIDamageRadius 6.0
```

So the **bullet's** damage is 1.0 and the 1500 lives in the explosion tune. The card's reading is
that the shell is explosive (`bullet_is_explosive 1`) and the blast does the work. That reading is
already the fleet model:

```
$ python - <<'EOF'  # DAMAGE_MODEL.json → vehicles.medium_tank and its arms
EOF
"tank_cannon": {"channel": "explosion", "damage": 1.0, "per_shot_vs_vehicle": 1.0,
                "blast_in_file": {"player_damage": 1500, "player_radius": 8.0, "ai_damage": 550}}
"medium_tank": {"max_health": 2000, "channels": {… "explosion": {"armor": 250, "strength": 50} …}}
```

2000 / 1500 = 2 hits ✓ (3 if the armour `strength` 50 halves it — H1, which the card already
prints).

**Verdict: HOLDS**, with the caveat the card itself does not spell out: `PlayerDamage`/`AIDamage`
could be "damage *to* the player/AI" rather than "caused by"; under that alternative a tank would
take `AIDamage` 550 → 4 hits. `DAMAGE_MODEL.md:19` states the same uncertainty ("whether a vehicle
takes `damage x vehicle_damage_factor` or the raw `damage` … is UNKNOWN"). Because the number
crosses as `derived` and T-14's 36000 rests on it, the Q-3 #3 count is the only falsifier — which
is what the card says.

---

## A4 · `FiringInterval` seconds → `fire_rate` seconds, 1:1

**The result rests on:** the edit table and both edits ("rate: 1:1 (both seconds): 1.75 -> 2 s",
"0.1 -> 0.138").

**Test.**

```
$ python - <<'EOF'
WEAPONS.json → Batmobile_Heavy_Cannon_Primary  /  Batmobile_Cannon_V2
EOF
RVehicleWeapon.FiringInterval                2.0
RVehicleWeapon.FiringInterval                0.1379999965429306
RBatmobileCannon.ComboFiringInterval         0.1379999965429306
(RBatmobileCannon.ChainGunMaxSpinSpeed 1440.0 carries the "1440" the doc quotes)

$ python - <<'EOF'
WEAPONS.jsonl → summaries
EOF
w602_mediumtank_canon  fire_rate 1.75   fire_rate_level_2 0.11999999731779099
w603_mediumtank_mgun   fire_rate 0.1    fire_rate_level_2 0.11999999731779099
```

Both BmAK values are exactly the edited `new` values, and the JC3 `old` values are exactly the
tune's `fire_rate`. 1/2 s for a tank cannon and 1/0.138 s = 7.25 rps for a coax MG are sane, and
G2-10 already established `fire_rate` is a period, not a rate.

**Verdict: HOLDS** for the member. **WEAK** for completeness: both tunes carry a second rate
member, `fire_rate_level_2` 0.12, which neither edit touches. After the edit, w603's base is 0.138
while its level-2 stays 0.12 — the *upgraded* gun would out-fire the translated one, and w602's
level-2 0.12 s (equal to w618's) would be 16× faster than its base 2 s if it ever applied. The card
never mentions the member or decides that it is a template default.

---

## A5 · `Projectile.Speed` 40000 UU/s → JC3 `velocity` 400 m/s

**The result rests on:** "`Projectile.Speed` 40000 UU/s = 400 m/s … `velocity` 500 (the member's
unit is not stated)", classed `derived`, "the /100 bridge".

**Test.**

```
$ python - <<'EOF'
WEAPONS.jsonl → every summary.velocity
EOF
ids with velocity 22
  w601/w606/w615/w618/w621 … 360.0   |  w602/w605/w616 500.0  |  w608…w614 600.0
  w603/w619 750.0 |  w604/w607/w610/w617/w620/w622 900.0
```

The ladder 360/500/600/750/900 is exactly what the card describes, and the BmAK side is 40000 (a
plain "400 m/s at 1 UU = 1 cm"). But the same tune holds a second velocity:

```
w602:  velocity 500.0        tracer_fire_velocity 900.0
w603:  velocity 750.0        tracer_fire_velocity 750.0
```

**Verdict: HOLDS as declared** — the class is `derived`, the `/100` is stated as inferred, and the
Q take ("time a shell to a wall 40 m away; pass = 0.10 s ±0.02") can fail the bridge. **WEAK on the
member:** for w602 the two candidates differ 1.8× and the edit moves only `velocity`; if the engine
flies the tracer member, the edit is inert and the take fails for the wrong reason. The card
mentions neither the second member nor which one the Q take distinguishes.

---

## A6 · The weapon point is `decoded`

**The result rests on:** "socket [0.0003, 1.7025, -0.4559] m, forward [0.0, -0.0, -1.0]" with
class **decoded** (T-WP1, T-WP2, T-WP4), and the same forward on three different sockets.

**Test.**

```
$ python - <<'EOF'
SOCKETS_JC3.json → sockets with role muzzle/light
EOF
BattleModeSpotLight bone=Batmobile_Rig_Weapons_Drone_Decoder pos=[0.000378, 1.834583, -0.066368]
                    fwd=[3.9e-05, -0.000108, -1.0] inside=True rotmissing=True
CannonMuzzle        bone=…Heavy_Cannon_Barrrel_02  pos=[0.000339, 1.702497, -0.455945]
                    fwd=[3.9e-05, -0.000108, -1.0] inside=True rotmissing=True
ChainGunMuzzle      bone=…Machine_Gun_01           pos=[-0.407368, 1.551869, -0.166883]
                    fwd=[3.9e-05, -0.000108, -1.0] inside=True rotmissing=True
MissileL            bone=Batmobile_Chassis         pos=[0.593771, 1.484682, -1.14681] rotmissing=False
```

`SOCKETS_JC3.json` counts 26 of 65 sockets with a missing rotation, and all three weapon points the
card uses are in that set. Their `forward_jc3` is therefore **the same identity fallback for all
three**, not a decoded direction (the two missile sockets, which do have rotations, print
different forwards — the contrast is in the same file).

**Verdict: BROKEN as a class.** The *position* reproduces to 4 dp and is genuinely decoded; the
*forward* is a default, and the row prints it as if decoded. It matters: the cannon row claims
`batmobile_cannon` (T-12 P-02) which T-12 itself records as **static** (`T8_PARTS.md:47 | P-02 |
… | static |`), so nothing will animate a direction the socket does not carry. The fix is a
one-word change (`decoded` → `decoded position / UNKNOWN direction`), not a new number.

---

## A7 · `w619_buggy_mgun` is "the only driver-fired car MG with a `GatlingGun` part"

**The result rests on:** the T-WP2 carrier cell and §1's id table ("the only driver-fired car MG
with a `GatlingGun` part, 1 carrier"), and the T-WP2 barrel-spin proposal ("spin the T-12 P-03
barrels").

**Test.**

```
$ python - <<'EOF'
FEATURE_CENSUS.json → part_behaviours where behaviour == "GatlingGun"
EOF
{"behaviour": "GatlingGun", "parts": 24, "entities": 12, "chassis": 3,
 "chassis_list": ["v1401_boat_mugello_racingboat",
                  "v2602_helicopter_urga_lightassault",
                  "v2604_helicopter_urga_advancedassault"]}

$ python - <<'EOF'
WEAPON_WIRING.jsonl → parts + weapons of the buggy, the boat, the heli
EOF
v0604_car_urga_buggy  weapons: [('w619_buggy_mgun', ['main_weapon'], '2')]
                      parts: []                                    ← no parts at all
v1401_boat_mugello_racingboat  parts: [('racingboat_minigun_l_barrel_signature','GatlingGun'),
                                       ('racingboat_minigun_r_barrel_signature','GatlingGun')]
v2602_helicopter_urga_lightassault parts: [ … ('lightassault_minigun_l_barrel','GatlingGun'),
                                            ('lightassault_minigun_r_barrel','GatlingGun')]
```

The buggy the card names as the barrel-spin proof has **no part of any behaviour**; the
`GatlingGun` parts belong to a boat and two helicopters. The card's own §4 barrel-spin row already
says the right thing — "`GatlingGun` part behaviour driven by `weapon_rpm` (**racing boat,
helicopters**)" — so the row table and §4 contradict each other, and the wrong one is in the
ledger-bearing cell.

**Verdict: BROKEN.** The *carrier* (a GatlingGun part driven by `weapon_rpm`, `MOVING_PARTS.json`
table row confirms `rpm_variable: weapon_rpm`) still exists — but not on the vehicle the card cites,
and the "1 carrier / only driver-fired car MG" claim about that vehicle is false. Correcting the
cell costs nothing and removes a claim a later session can disprove in one command.

---

## A8 · The fleet's maximum is two driver slots (D-7's premise)

**The result rests on:** "the fleet has **2 driver slots** at most (medium and Bavarium tank:
`main_weapon` + `id:00568A74`)" and "53 armed entities".

**Test.**

```
$ python - <<'EOF'
WEAPON_WIRING.jsonl → max(counts.driver_slots) and every row with ≥2
EOF
fleet rows 53 max driver_slots 2
2+ slots: v0201_car_capstone_mediumtank    driver 2 gunner 0  [w603→secondary, w602→main_weapon]
          v0202_car_capstone_bavariumtank  driver 2 gunner 0  [same pair]
          v2200_helicopter_capstone_assault, v2601_helicopter_urga_heavyassault,
          v2604_helicopter_urga_advancedassault, v4202_plane_capstone_fighterjet,
          v4602_plane_urga_fighterbomber, v4603_plane_urga_cargotransport
$ python - <<'EOF'  FEATURE_CENSUS.json totals
EOF
{"entities": 232, "armed_entities": 53, "armed_chassis": 21, "weapon_ids": 25}
```

Two driver slots on land is exactly right (only the two tanks), the sample is the complete armed
census rather than a sample, and 53/25/232 all reproduce.

**Verdict: HOLDS.** The sentence is under-inclusive (the assault helicopters and jets also have
two), not wrong; “fleet maximum 2” is true.

---

## A9 · D-7's three "ways out", one of them "extra root pointer (absent)"

**The result rests on:** T-WP13's closing note — "three ways out, none in the files: **extra root
pointer (absent)**, a switching action (absent), or 2 slots (contradicts D-7)".

**Test.**

```
$ sed -n '1,40p' Research/JC3Grab/WEAPON_WIRING.md      # the card's own dependency
| 1st driver | `id:851CAABE`  | `main_weapon` = `851CAABE` | driver |
| 2nd driver | `id:00568A74`  | **no name found**          | driver |
| 1st gunner | `mounted_weapon`| named in the file         | gunner seat |
| 2nd gunner | `id:AC0BC788`  | `mounted_weapon_2` = `AC0BC788` | gunner seat |
"Each root class (`CCar`, `CAirPlane`, `CBoat`, `CHelicopter`, `CTrain`) carries all four pointers".

$ python - <<'EOF'
WEAPON_WIRING.jsonl → every slot with a target, by gunner_slots
EOF
('main_weapon', 0, 'v0201_car_capstone_mediumtank') … 15 rows
('mounted_weapon', 1, 'v0200_car_capstone_apc')     ← a car root with a third weapon bound
('mounted_weapon', 1, 'v0504_car_solar_technicaljeep')
('mounted_weapon', 1, 'v0600_car_urga_armoredjeep')
('mounted_weapon', 2, 'v1200_boat_capstone_heavypatrol')
('mounted_weapon_2', 2, 'v1200_boat_capstone_heavypatrol')

$ python - <<'EOF'  hash test with Tools/scripts/rbmhdr.hash_jenkins
EOF
main_weapon 851CAABE   secondary 591E6BB7   mounted_weapon 4B86679F   mounted_weapon_2 AC0BC788
```

So the root can carry **four** weapons — two driver and two gunner — and the heavy patrol boat
binds both gunner pointers while the APC, the technical jeep and the armoured jeep bind a third
(`mounted_weapon`) on a *car*. "Extra root pointer (absent)" is therefore false; what is genuinely
absent is a **third driver** pointer and any active-slot/next-previous action (no such class exists
in the 127-row class census — see A11).

**Verdict: BROKEN as worded**, and this matters beyond pedantry: D-7 asked T-11 to find how the
slots could carry 11 weapons, and the row tells the next session that one of the two member routes
does not exist, when the member exists, is named, and is already filled on five entities. The
honest residue is narrower and testable: *no driver slot beyond two, and no switching action.*

---

## A10 · `secondary (id:00568A74)` is a driver slot

**The result rests on:** the slot cell of T-WP1/T-WP2/T-WP13 ("`secondary (id:00568A74)` - the slot
the medium tank binds w603 to", "the medium tank's second driver slot").

**Test.**

```
$ grep -n "00568A74" Research/JC3Grab/WEAPON_WIRING.md
12:| 2nd driver | `id:00568A74` | **no name found** | driver |
"The 2nd driver slot resisted a 1.1-million-string vocabulary search (57 weapon/mount words in
 2- and 3-word combinations, numeric suffixes); its id is the name of record."

$ python - <<'EOF'  WEAPON_WIRING.jsonl → the tank's seats and slots
EOF
seats: ['interaction.seat.driver', 'interaction.seat.stunt']
slots: main_weapon → w602_mediumtank_canon ; "secondary (id:00568A74)" → w603_mediumtank_mgun
```

The word "secondary" is an interpolation (`hash_jenkins("secondary")` = `591E6BB7`, not
`00568A74`); the id is unnameable and the source file says so. The *behaviour* claim survives
anyway: the tank has no gunner seat, the fleet's gunner pointers always coincide with
`gunner_slots ≥ 1`, and `driver_slots: 2 / driver_weapons: 2` is what G2-11 measured. A
player-driven tank with two weapons and one seat must fire both from that seat.

**Verdict: HOLDS on behaviour** (which is what R5 asks for), **WEAK on the label** — the row prints
"secondary" as a name while its own source says "no name found", and the MODLOG then hardens it
("the fleet's maximum is 2 driver slots (medium + Bavarium tank: `main_weapon` + `id:00568A74`)").
Keeping the id in the cell is the fix.

---

## A11 · "No carrier exists" for WPN-6…WPN-10

**The result rests on:** five named omissions, each proved by a word scan: "no winch member path
in the 52-type / 1,421-path vocabulary and no winch class in the **103-class fleet census**", "no
allegiance-switch class", "no sonar class", "no tracker class (the only 'track' is CMusicTrack)",
"no non-lethal flag … 52-type / 1,421-path vocabulary".

**Test 1 — the words really are absent** (reproduced independently):

```
$ for w in winch rope tow cable grapple sonar tracker tracking hijack allegian hack lethal incapacit tranquil; do
    printf "%-12s V=%-3s E=%-3s\n" "$w" "$(grep -ic "$w" VOCABULARY.md)" "$(grep -ic "$w" ENTITIES.md)"; done
winch   V=0 E=0 | tow V=0 E=0 | cable V=0 E=0 | sonar V=0 E=0 | tracker V=0 E=0 | tracking V=0 E=0
hijack  V=0 E=0 | allegian V=0 E=0 | hack V=0 E=0 | lethal V=0 E=0 | incapacit V=0 E=0 | tranquil V=0 E=0
rope    V=55 E=3   → every hit is "propeller"   (grep -in rope VOCABULARY.md → propeller_offset[])
grapple V=2 E=0    → grapple_pull_armor, grapple_pull_armor_strength (n=233 each)
```

So the negative results are honest, and the two hits that look like counter-examples are not.

**Test 2 — the census denominator does not reproduce:**

```
$ python - <<'EOF'  ENTITIES.md class rows
EOF
class rows in census: 127
C-prefix 79 | >=10 occurrences 113 | 127 - 25 CInteraction* = 102 | 127 - 25 S* = 102
```

The card (and `G2X.md`) say "103-class fleet census"; the file they cite prints **127** class rows,
and no obvious filter lands on 103. The *absence* is unaffected; the *label* is a stale constant,
and a reader checking the number finds a different one.

**Test 3 — the search covers words, not behaviours, and misses the same files' own machinery:**

```
$ grep -in "CGrapplingHookPropData\|grapple_pull" ENTITIES.md VOCABULARY.md
ENTITIES.md:74:| `CGrapplingHookPropData` | 33 |
VOCABULARY.md:1472:| `grapple_pull_armor` | int32 | -1 .. 0 (med 0, n=233) | 0 |
VOCABULARY.md:1473:| `grapple_pull_armor_strength` | float | 0 .. 100 (med 0, n=233) | 0 |

$ python - <<'EOF'  the aim component on the card's own two carriers
EOF
v0300_car_kensington_sportsmuscle w618_sportsmuscle_missile
  components: ['CAimPOIWeaponComponent']
  props: {"name": "aim.poi", "id:2D0B3C09": "50", …}
v0604_car_urga_buggy w619_buggy_mgun
  props: {"name": "aim.poi", "id:2D0B3C09": "25", …}
total CAimPOIWeaponComponent: 11

$ python - <<'EOF'  shipped autoaim presets
EOF
autoaim_vehicle_lockon_missile       vehicle_lockon.wtune              members=126 with_lock=0
autoaim_vehicle_no_lockon_missile    autoaim_vehicle_no_lockon_missi   members=126 with_lock=0
lockon preset users: []          ← 0 of the 25 ids reference it
```

Three carriers exist that the word scan cannot see: a grappling-hook prop class (33 instances) and
grapple-pull armour members (n=233) in the very files searched for "winch"; a per-weapon
`aim.poi` component sitting on the two weapons the card chooses, while T-WP3's note says "the
AutoAim → POI link is unwritten"; and a shipped `autoaim_vehicle_lockon_missile` preset that no id
references.

**Verdict: HOLDS for WPN-7/WPN-8/WPN-10 as word-level absences** (nothing in those two files or in
the weapon tunes carries them) and **WEAK for WPN-6/WPN-9 and for the lock-on half of WPN-3** — the
"no carrier exists" is stronger than a four-word scan supports, the census number it cites does not
reproduce, and two of the missed carriers sit on the entities this card is editing. The genuinely
absent parts are the *numbers* (lock time and range, a disable state, a non-lethal flag), and those
are already reported as UNKNOWN.

---

## A12 · The Vulcan has no overheat on either side, so heat is a `decoded` absence

**The result rests on:** "`HeatUpPerSecond` 0 = **no overheat** (`OverheatOffValue` 0.25);
`HeatBarStart` [0.79, 0.68] and `HeatBarSize` [0.125, 0.03] are HUD bar geometry" → "both sides
absent" → class **decoded**; and the WPN-2 take "hold the trigger 2 s into a wall; pass = 14 ±1
impacts and **no overheat** (the BmAK heat rate is 0)".

**Test.**

```
$ python - <<'EOF'  every BmAK member containing "eat"
EOF
HeatBarSize                                     n=4  e.g. ('Batmobile_Cannon_V2', [0.125, 0.03])
HeatBarStart                                    n=4  e.g. ('Batmobile_Cannon_V2', [0.79, 0.68])
RBatmobileCannon.ChainGunOverheatSound          n=4  e.g. ('Batmobile_Cannon_V2', -148)
RBatmobileCannon.HeatUpPerSecond                n=4  e.g. ('Batmobile_Cannon_V2', 0.0)
RBatmobileCannon.OverheatOffValue               n=4  e.g. ('Batmobile_Cannon_V2', 0.25)

$ python - <<'EOF'  resolve the sound refs
EOF
RBatmobileCannon.ChainGunOverheatSound -> Engine.Play_Minigun_Overheat
RBatmobileCannon.ChainGunCooledSound   -> Engine.Play_Minigun_Cooled

$ python - <<'EOF'  charge/heat members in the 25 JC3 tunes
EOF
charge members: 0        (0 heat members too — JC3_HUD_WEAPONS.json "params_with_heat": [])
```

The object ships an overheat sound, a cooled sound, an "overheat off value", and a heat-bar
geometry. Reading `HeatUpPerSecond = 0.0` as "no overheat behaviour" is precisely the R5 failure
mode ("a member read by its name"): a *passive* heat rate of 0 is fully consistent with heat being
added per shot, and the per-shot member is not in the grab, so the behaviour's trigger is
**UNKNOWN**, not absent. The take then cannot fail: the clone has no heat member at all, so the Q
recording can only ever show "no overheat", whatever BmAK did. §9's own Q-3 #3 asks for "Vulcan
overheat time (WPN-2)" — the card and the check it claims to satisfy disagree.

**Verdict: BROKEN as a class and as a take.** Two cheap repairs: class the aspect `UNKNOWN` (with
the four members quoted), and give WPN-2 a take that can fail — e.g. "hold 6 s: if the clone does
not overheat, record that BmAK's heat curve is unbuilt" — instead of one that is true by
construction.

---

## A13 · WPN-3's missile stays unguided because the donor's is

**The result rests on:** "spread curve | none (guided) | `scatter` 0/0, `turning_speed` 0 | keep
unguided: the donor's missile is `autoaim_vehicle_no_lockon_missile`" (class **decoded (fleet)**),
with BmAK's `LockOnAngle` 40° / `LockOnRange` 12000 in the same row.

**Test.**

```
$ python - <<'EOF'  WEAPONS.jsonl → turning speed and presets of every missile
EOF
w608_fighterjet_missile            presets ['autoaim_vehicle_no_lockon_missile','rpg_assault_helicopter']
                                   missile_turning_speed 75.0
w609_fighterjet_missile_air_lockon presets ['rpg_assault_helicopter']      missile_turning_speed 150.0
                                   (name: air_lockon; max_range 750; damage 1500; 1.0 vehicle factor)
w621_advancedhelicopter_missile    missile_turning_speed 0.0
w618_sportsmuscle_missile          missile_turning_speed 0.0     ← the carrier the card picks
prototype_helicopter_missiles (boss) missile_turning_speed 45.0 / 250.0 (player/AI)
```

BmAK's launcher locks (`LockOnAngle` 40.0, `LockOnRange` 12000.0, `MissileNumberParameter` →
number of targets) and the fleet has guided missiles with a member that carries the guidance
(`missile_turning_speed`), one of them literally named `air_lockon`. The card's `decoded (fleet)`
class is attached to the sentence "keep unguided: the donor's missile is …", i.e. to a
**donor-first** argument — the exact inversion R1 forbids ("Lore over the donor car … BmAK
behaviour first") and the one R5 warns about (behaviour replaced by the nearest-sounding member).

**Verdict: BROKEN against R1/R5.** This is the only finding here that changes a *requirement*: the
row currently ships "missiles that do not home" as fleet-decoded fact when the fleet can home. The
honest choices are (a) clone a guided missile (w609 carries 150°/s and the lock-on name) and class
the guidance `decoded (fleet)` with the donor's tunelessness noted, or (b) keep w618 and class the
row `class` with "unguided — donor behaviour, contradicts BmAK's lock" in `why`. What is not
available is "the fleet has no guidance".

---

## A14 · The WPN-3 take: "4 missiles leave the two pods"

**The result rests on:** the verify cell "Q-3 #3: 4 missiles leave the two pods and hit what the
reticle covers; a stock car takes the predicted 2, 3/3 salvos".

**Test.**

```
$ python - <<'EOF'  the donor's w618 in the entity graph and the tune
EOF
w618_sportsmuscle_missile points: 4 ['internal.fire_point.2','internal.fire_point.0',
                                     'internal.fire_point.1','internal.fire_point.3']
missile_per_shot: None (summary)   tune row missile_weapon[0].tuning.missile_base_tuning.missile_per_shot 1
burst_count 1   fire_rate 0.5   velocity 360
```

Four *fire points*, one missile per shot, burst 1, no edit proposes changing `missile_per_shot`
(the withdrawal list even drops BmAK's salvo count as an undecoded curve parameter). One press can
only produce one missile from one of the four points.

**Verdict: WEAK.** The take describes a salvo behaviour the build does not have, so it fails for a
reason unrelated to the value under test (or passes by reinterpreting "4 missiles" as four presses).
Make the pass condition "four presses cycle the four fire points, one missile each" — or add the
per-shot member to the edit list with a class.

---

## A15 · "7 carriers, 175 decoded tune rows"

**The result rests on:** the T-WP1 carrier cell ("`w602_mediumtank_canon` - the medium tank's
cannon, 7 carriers, **175 decoded tune rows**") and the charge withdrawal ("no charge member in
the **175** decoded rows").

**Test.**

```
$ grep -n "175" Tools/scripts/t7_weapons.py
235:  f"`{wid}` - the medium tank's cannon, 7 carriers, 175 decoded tune rows, blast "
277:  "no charge member in the 175 decoded rows", …

$ python - <<'EOF'  the actual rows
EOF
summary weapon_rows 171
instance rows [171, 8]          # WeaponTuning 171 rows + ForcePulseSettings 8 rows
entities 7 carriers 7
```

"7 carriers" is right; "175" is a hand-typed constant that no count produces (171 weapon rows, or
179 with the blast tune). R11 ("counts are generated, never typed") is breached inside a cell the
row classes `decoded`.

**Verdict: WEAK** (a single digit, but it is the kind of number a later session will trust).

---

## A16 · §1's "player damage / radius" column says UNKNOWN for w603 and w619

**The result rests on:** §1's id table "`w603_mediumtank_mgun` … player damage / radius =
**UNKNOWN / UNKNOWN m**" and the same for `w619`, while §4's T-WP2 row says "`damage` 190 direct,
vehicle factor 0.3".

**Test.** The table is generated from `J.get(wid, "PlayerDamage")`, i.e. the blast tune only:

```
$ python - <<'EOF'  WEAPONS.jsonl → w603 summary
EOF
"bullet.player.damage": 190.0
"bullet.player.vehicle_damage_factor": 0.30000001192092896
(and the raw rows: bullet_weapon[0].tuning.base_tuning.damage 190.0, vehicle_damage_factor 0.3)
```

w603 and w619 have no `.ftune` (not explosive), so the column prints UNKNOWN; their real damage
member is 190. The doc therefore answers "what damage does the Vulcan do" two ways: UNKNOWN in §1,
190 in §4.

**Verdict: WEAK** — a reporting defect, not a data defect. The column should be headed "blast
(`PlayerDamage`)" or print the bullet damage with its own class. Note the row's *class* for the
aspect stays legitimately UNKNOWN for a different reason ("no BmAK health to ratio against"), which
the table's UNKNOWN currently hides.

---

## A17 · The fleet-wide constants

**The result rests on:** "JC3 weapon ids used 4 of the fleet's 25", "53 armed entities", "307
pulses on 232 vehicles", "14 unowned pulses", "`arcade.nitro_boost` on 145/232 vehicles", "2
clips", "14 reticle shapes", "0 heat params", "driver slots 2", "65 placed sockets", "25 ids with
a 360..900 velocity band".

**Test and result** (every one a census, not a sample):

```
FEATURE_CENSUS.json totals   232 entities, 53 armed_entities, 21 armed_chassis, 25 weapon_ids
WEAPONS.jsonl                25 rows ; 22 with a velocity, ladder 360/500/600/750/900
FORCEPULSE.json              objects 307, entities 232, unowned 14, graphs 232
                             truck_emp.ftune: PlayerDamage 100 / radius 25.0 (held to full radius)
USAGES.json                  nitro carriers {"nitro_boost": 145, "heat_boost": 145, …}
JC3_HUD_WEAPONS.json         slots.count 2 (MCI_vehicle_weapons0/1) ; heat.params_with_heat []
                             reticle.shapes 14 ; lockon POI_TYPE_LOCK_ON_TARGET 21, 1.5 s, 0.5 s
WEAPON_WIRING.jsonl          53 rows, max driver_slots 2
SOCKETS_JC3.json             sockets 65, placed 65, missing_rotations 26
```

**Verdict: HOLDS.** These are the parts of the card a later session can rely on without
re-deriving anything, and they all reproduce to the digit.

---

## A18 · `BattleModeSpotLight` is the EMP missile's fire point, though it is not a muzzle

**The result rests on:** the T-WP4 weapon-point cell ("socket `BattleModeSpotLight` is not a
muzzle: it is the battle spotlight bone") and the structural item "`SWeaponPoint` at
`BattleModeSpotLight` with the -20 deg pitch".

**Test.**

```
$ python - <<'EOF'  SOCKETS_JC3.json → BattleModeSpotLight
EOF
bone=Batmobile_Rig_Weapons_Drone_Decoder   role="light"
pos=[0.000378, 1.834583, -0.066368]  rotmissing=True  inside_body_box=True

$ python - <<'EOF'  WEAPONS.json → the EMP launcher
EOF
RPursuitModeMissileLauncher.LaunchSocketName    BattleModeSpotLight
RPursuitModeMissileLauncher.LaunchRotationOffset [-3640, 0, 0]     (-3640 × 360/65536 = −19.995°)
RBatmobileEMPMissile.MissileLockOnDuration 2.0 ; CivilianMissileLockOnDuration 1.0
```

−20° is right, and the socket is a decoded BmAK member (`LaunchSocketName`), so placing the point
there is a faithful translation rather than a guess. Two caveats belong in the text: the socket is
a light bone (G1-13's role field says so) and its own rotation is missing, so the only direction
the point will have is BmAK's −20° pitch.

**Verdict: HOLDS as a recorded choice**; **WEAK** in that it is carried under a `decoded` class
with no note about the missing socket rotation (same defect as A6).

---

## A19 · The card's own tallies

**The result rests on:** "14 rows = 12 WPN codes + 2 decision rows", "136 aspects (UNKNOWN 53,
decoded 72, decoded (fleet) 7, derived 4)", "5 with a JC3 carrier, 6 named omissions, 3 blocked",
"3 edits + 6 structural + 6 withdrawn", and the dispositions in `T_ROWS.jsonl`.

**Test.**

```
$ python - <<'EOF'  count aspect rows in the delivered doc by class
EOF
aspect rows found 136 {'decoded': 72, 'derived': 4, 'UNKNOWN': 53, 'decoded (fleet)': 7}
row-table rows 14

$ python - <<'EOF'  the generator's own summary and dispositions
EOF
rows 14, wpn_codes 12, decision_rows 2, with_carrier 5, omissions 6,
blocked ['T-WP4','T-WP5','T-WP13'], edits 3, structural 6, not_numeric 6, jc3_ids_used 4
dispositions: WP1-3 next · WP4,5 blocked · WP6-10 out · WP11 keep · WP12 next · WP13 blocked · WP14 out
```

72 + 53 + 7 + 4 = 136 ✓ and every class is one of R4's five. The ledger cross-check inside
`--check` passed (the only failure reported was the md), so `T_ROWS.jsonl` carries all 14 with
these dispositions — which is also why §12's "5 with a JC3 carrier, 6 named omissions, 3 blocked"
is right and the MODLOG's "5 omissions, 4 blocked" is the stale line (A1).

**Verdict: HOLDS.**

---

## A20 · "No charge member" — the withdrawal of `ChargeUpTime` 2.5 s

**The result rests on:** the withdrawn value "`ChargeUpTime` 2.5 s — no charge member in JC3's 25
tunes".

**Test.**

```
$ python - <<'EOF'  every row of every tune of the 25 ids containing "charge"
EOF
charge members: 0
```

and the BmAK side does carry it (`RBatmobileHeavyCannon.ChargeUpTime 2.5`,
`ChargeMaxDamageRadius 0.0`, plus the `ChargingScreenShake` block whose `offset 0x0004` is
1000000 — a real charge-up feedback). The withdrawal is therefore correct as a *no-carrier*
statement, and it is one of the six values the card chose not to invent.

**Verdict: HOLDS.**

---

## What this challenge did not test

- **Anything in-game.** R6 forbids a launch before phase V exits; every take in the card
  (`Q-3 #3`, `Q-1 #5`, `Q-2 A9`) is still unproven, and this review cannot change that. Where the
  card says "2 hits" or "7.25 rounds/s", the numbers are arithmetic on decoded values, not
  behaviour.
- **The BmAK collision/damage channel mapping beyond `damage` and `Pawn.Health`** (how
  `RDmgType_BatmobileCannon`, `TurretShotDamage` 75 and `RVehicleBatmobileBase.TakeDamage` compose)
  — out of scope for T-11 and already T-14's.
- **Whether a gunner slot can be fired by a driver** (A9's residue). That is a behavioural question
  no decoded file answers; the fleet evidence is only that the pointers exist and are filled when a
  gunner seat exists.
- **The tuning snapshots' provenance within `WEAPONS.jsonl`** (base vs patch copy), which the G2-10
  challenge card already examined; this review used the file as delivered.

## Reproduce

```
python Tools/scripts/t7_weapons.py --check          # A1: currently exit 1 (md differs)
python Tools/scripts/t7_weapons.py show rows        # the 14 rows, as the generator sees them
python Tools/scripts/t_rows.py check               # ledger sums
python Tools/scripts/status_audit.py --check       # STATUS.md vs the ledger
```

The heredocs above are all read-only; each prints what the section quotes. Nothing in the repo,
`Builds/`, `E:/Modding/_JC3grab`, `E:/Modding/_BmAKgrab` or `D:/Games` was written, and no process
was launched.
