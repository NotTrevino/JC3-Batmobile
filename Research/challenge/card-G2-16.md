# Assumption challenge — card G2-16 · The EMP truck

Written 2026-10-30. Read-only review: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified; the only file written is this one. No game was launched,
nothing was written to `D:\Games`, nothing was committed, no secrets read or echoed.

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-16 card (line 653), the §12 row (line 1299),
`MODLOG.md` §"G2-16 · The EMP truck — intended change" (9860) and §"— done" (9884), and the
outputs: `Research/JC3Grab/EMP.md` (225 lines), `EMP.json`, `Tools/scripts/jc3emp.py` (652 lines).

**Card as written:** "describe the EMP device: components, trigger (`entry.use_item`), radius,
duration, what it disables (vehicles, electronics, AI), effects and sounds, whether it can be
attached to another entity. Done: a yes/no answer 'can the EMP effect be fired by a driver of a
different vehicle', with evidence; the list of files that would have to be copied."

**Method.** The card's own reader was re-run (`--check`), then the claims were attacked with
probes that the card did **not** run: a reverse-reference sweep over every property of every one of
the truck's 454 objects, a class-name census over all 236 cached `.epe` graphs (232 vehicle
entities, not the card's 53-entity sample), byte-level comparison of the nine parts modules,
resolution of the trigger/entry pointers in three unrelated entities, Jenkins-hash checks of the
effect ids, and a parse of the `.stringlookup` member that the card never opened. Cached decoded
XMLs under `E:\Modding\_JC3grab\wiring\epe\` were used where possible so that no extra archive read
was needed.

---

## VERDICT

**The core deliverable holds: the truck really has no weapon component, nothing at all points at
its EMP pulse, and the effect/table/emitter files resolve exactly as the card says. Six statements
are wrong, and two of the wrong ones are load-bearing for the copy list** — the parts modules are
*not* shared across the nine variants (three different byte-blobs), and "the EMP pulse ... (2
variants)" contradicts the card's own table (mm250 has zero). The "dangling pulse ref" is a misread
of a `vec_events` member whose targets are never local, and the "stock `fow_weapon` tune" is a
mislabel of a `WeaponTuning` array — the FOW block is what actually carries the EMP's numbers,
which the card hides. The central negative (no vehicle holds `CEMPWeapon`) survives a full-fleet
census and is stronger than stated, but the *wiring* claim behind "any vehicle that carries the same
objects gets the same device" is weaker than stated: the donor's pulse has no owner, and the only
other entity that runs the same use-item state carries graph-script objects the truck does not have.

```
$ python Tools/scripts/jc3emp.py --check
PASS: 2 builds, 9 variants, 3 device parts, 2 EMP weapons, fleet CEMPWeapon 0      EXIT=0
```

| # | Assumption the result rests on | Verdict |
|---|---|---|
| A1 | "no weapon component at all" on the truck; EMP is not on a fire button | **HOLDS** (and stronger than stated) |
| A2 | No pointer from trigger / entry / vehicle to the EMP pulse | **HOLDS** (full reverse sweep, 0 hits) |
| A3 | `trigger.use_item` is a 2×-scaled *box over the flatbed* | scale HOLDS; "box"/"flatbed" **WEAK** |
| A4 | `trigger.use_item` is wired to `entry.use_item` (silent) | **WEAK** — shared unresolved id, no resolvable pointer |
| A5 | "the trigger's refs do not resolve … one pulse ref is dangling" | **BROKEN** — `vec_events` misread |
| A6 | "Same members, same parts, same trigger, same prompt" | **BROKEN** — entry `enabled` 1 vs 0, link target differs |
| A7 | "The parts module is shared by all 9 variants" | **BROKEN** — three distinct module blobs |
| A8 | Every variant carries the 3 parts + rotor row; no trigger on the other 7 | **HOLDS** |
| A9 | "the EMP pulse and its tune (2 variants)" | **BROKEN** — mm250 pulse count is 0 |
| A10 | "damage held at full for the whole radius" (*RadiusPercentageMax/Min) | **WEAK** — inferred, not EMP-specific |
| A11 | "an EMP is 3 flags + the table" | **HOLDS** as a fingerprint; "flags" is inferred |
| A12 | `emp_flatbed_table` maps every slot to `explosion_emp_flatbed.effc` | **HOLDS** — hash now proven; not script-backed |
| A13 | prompt `ui_activate_emp` means "activate the EMP" (silent) | **HOLDS** — 11-language string table |
| A14 | "No EMP sound" | **WEAK** — name-only negative |
| A15 | "the engine's EMP weapon class … two files"; 0 of 88 fleet components | **HOLDS** — 236-graph census, still 0 |
| A16 | the 88-component count is a sample, not the fleet (card's own limit) | **HOLDS** — limit honest, and now closed |
| A17 | "Both use the stock `fow_weapon` tune" | **BROKEN** — `fow_weapon` is an array in `WeaponTuning`; it is the *populated* block |
| A18 | "damage 500 / range 50 m / 750 m", "magazine 1" | units **WEAK**; magazine **BROKEN** (w503 = 3) |
| A19 | w702 handheld two-handed / w503 static prop "own rigid objects and hinge" | **HOLDS** structurally; "spin-up dials" **WEAK** (name) |
| A20 | `weapon_type` 6 / 2 carries "handheld / static turret" (silent) | **WEAK** — 2 is the universal mounted value |
| A21 | "Any vehicle entity that carries the same objects gets the same device" | **WEAK** — no owner, no graph script on the donor |
| A22 | "cannot be copied as a weapon-slot weapon" | **HOLDS** for the disable; **WEAK** as the whole answer (tune-swap path not evaluated) |
| A23 | "`car_explosion_medium` is the stock blast every car carries" | **WEAK** — 115 of 232 entities |
| A24 | "Duration … not in the files" | **WEAK** — true for gameplay, false for the visual (effc timelines) |

---

## A1 · "The truck has no weapon component at all" → HOLDS (and stronger)

The card asserts it from `sorted({o.cls for o in objs if "Weapon" in o.cls}) == []`, i.e. a
substring match on class names. That could miss a weapon held by a differently named class or by a
root slot pointer. Both attacks fail:

```
$ python -c '... parse v0505_car_solar_oldtruck_rebel_emp_01.ee.xml ...'
truck weapon-ish classes: Counter()
  id:851CAABE    = '00000000'               -> -        (main_weapon)
  id:00568A74    = '00000000'               -> -
  mounted_weapon = '00000000'               -> -
  id:AC0BC788    = '00000000'               -> -
  id:B5AE7986    = 'EE13C0B6=FFFFE90F'      -> CForcePulse CForcePulse
weapon slots empty? True
```

All four `jc3wiring`-documented weapon slots are null, and the only pointer the `CCar` root does
carry is to the *plain* blast pulse, not the EMP. The fleet statement behind the negative ("no
vehicle weapon slot holds `CEMPWeapon`") was also re-tested at full width, see A15.

## A2 · "No reference from the trigger, the entry or the vehicle to the EMP pulse" → HOLDS

The card only printed the trigger's own props; it never swept the entity for references *into* the
pulse. Doing that over all 454 objects and every property string:

```
PULSE EMP 594C9A11=FFFFC0C2 settings truck_emp.ftune
refs to EMP pulse oid 594C9A11=FFFFC0C2 : [] count 0
who refs entry 52EA5205=FFFF8B92 : []
who refs trigger 01151709=FFFFA375 : []
```

Zero inbound references to the pulse, the entry and the trigger alike. This is the strongest single
result in the card and it survives.

**Caveat on the reader.** References were resolved as exact `HASH=ID` pairs. Resolving on the id
half alone finds one extra live reference in the entity (`4924FAAC=FFFFA6E4`, whose left half does
not match any object). That does not change this verdict (the EMP pulse's id `FFFFC0C2` resolves
under neither rule), but it means "dangling" in this reader is pair-exact, not id-exact.

## A3 · "`trigger.use_item` is a 2×-scaled box over the flatbed" → scale HOLDS, "box/flatbed" WEAK

The scale is decoded, not assumed:

```
TRIG 01151709=FFFFA375
  world: 2,0,0,0, 0,2,0,0, 0,0,2,0, 0,1.350708,2.395996,1
```

"Box" and "over the flatbed" are not in the object: the trigger carries no extent property, so
"box" comes from the class name `CInteractionTrigger` (R5 — behaviour read from a name), and "over
the flatbed" is a reading of the local `z = 2.396` as the truck's rear bed. Both are plausible and
harmless; neither is evidence.

## A4 · The trigger→entry pairing (silent) → WEAK

The card presents `entry.use_item` and `trigger.use_item` as one interaction ("`trigger.use_item`
is a 2× box … and `entry.use_item` runs the state"). The pairing rests on the shared `use_item`
name, the shared entity and one shared id — not on a resolvable pointer:

```
ENTRY 52EA5205=FFFF8B92 ... 'id:565F571C': '6D433019=FFFF8C71', 'state': 'S_STUNT_USE_ITEM_VEHICLE'
TRIG  01151709=FFFFA375 ... 'id:A5C536A1': '6D433019=FFFF8C71, E880D61A=0000CAE5'
who refs entry … []      who refs trigger … []
```

The trigger's outgoing list `id:A5C536A1` and the entry's `id:565F571C` name the **same** object —
and that object (`6D433019=FFFF8C71`) exists in no cached graph. Two further entities show the same
member pointing at *different* absent ids:

```
truck  entry.id:565F571C = 6D433019=FFFF8C71   (enabled 1)
mm250  entry.id:565F571C = C6F3CC5F=FFFF1D0E   (enabled 0)
plane  entry.id:565F571C = F067CEE2=FFFF1103   (enabled 1)   v4603_…_mm340, same state
```

So the link is a real, per-build, external id — not a broken pointer and not a local object. "The
trigger fires this entry" is therefore an inference from names + positions + one shared id. It is a
reasonable inference (the mm340 cargo plane uses the same construction), but it is not read from a
pointer, and the card does not say so.

## A5 · "the trigger's refs do not resolve inside the entity … one pulse ref is dangling" → BROKEN

The pulse's second ref is not an object pointer at all. Its type says so:

```
  id:06A05F33    type=vec_events value=5FED74E7=FFFF7F53
  id:D3DDD766    type=objectid   value=EE5AEE78=FFFFD9E6   -> CMaterialEffectTable emp_flatbed_table
```

`vec_events` is an *event* list, and its targets are external by design. Every other pulse in the
fleet that fills it references ids that are equally absent from their own entity:

```
v0505…cargo_barrel.ee  force barrel_explosion.ftune -> 10 ids, all MISSING locally
v4603…mm340.ee         explosion_force_pulse w704_m488 -> 2 ids, both MISSING locally
v0505…rebel_emp_01.ee  EMP truck_emp.ftune -> 1 id, MISSING
```

The barrel truck's cargo explosions obviously work in game, so a missing `vec_events` target is
normal, not evidence of stripped data. The card's phrasing ("the pulse's object references … no
such object in the entity") and its Limit ("One pulse ref is dangling") turn a member type into a
data defect. The factual half — no local object has id `FFFF7F53` — is true; the interpretation is
wrong.

## A6 · "Same members, same parts, same trigger, same prompt" → BROKEN

`EMP.json` itself carries the counter-evidence the prose skips:

```
emp_01  entry.use_item: enabled 1, id:565F571C 6D433019=FFFF8C71, trigger links 6D433019=FFFF8C71, E880D61A=0000CAE5
mm250   entry.use_item: enabled 0, id:565F571C C6F3CC5F=FFFF1D0E, trigger links C6F3CC5F=FFFF1D0E, E880D61A=0000CAE5
```

Same member count (794), same object count (454), same module bytes (see A7), same trigger
position, same prompt — but the mission build's use-item **entry is disabled at spawn** and its
trigger names a different target object. "Same trigger" is false; "same prompt" is true. For the
deliverable this matters: the mission truck is the *proof* that the action exists in the data with
the entry switched off, which is exactly the kind of "the objects are there, nothing calls them"
state the card elsewhere attributes only to the other seven variants.

## A7 · "The parts module is shared by all 9 variants" → BROKEN

Byte-level check of the one member every variant carries:

```
$ python -c '... sha1 of *_vehicle_parts.vmodc for all 9 ...'
commercial_01 / cargo_barrel / cargo_random / cargo_wine / debug   48670  sha1 97d6f28e1a58
military_01                                                       49134  sha1 d9a41d3dcf0e
rebel_01 / rebel_emp_01 / rebel_emp_custom_mm250                  48958  sha1 07a2980b28dd
rot_rows 1, number_of_blades [6], part_index [46]      (all nine)
```

Three distinct modules, not one shared file: each build embeds its own copy (R8's "never
internalise a module the archives carry" territory). What *is* true, and what the card actually
needs, is the content claim: all nine carry the three device parts and the 6-blade `rotating_parts[]`
row for part 46. The copy list's "the module's `rotating_parts[]` row" stays correct; the sentence
"shared by all 9 variants" and the implied "edit it once" do not. Note also that `rebel_01`'s module
is byte-identical to `emp_01`'s — the plain rebel truck already ships the device geometry, and the
whole difference between the two builds is entity objects. That *supports* the card's central
"the device lives in the entity" thesis better than the "shared module" wording does.

## A8 · Every variant has the parts; the other seven have no trigger → HOLDS

The card's claim was not encoded in `EMP.json` (the variant rows have no trigger field), so it was
tested directly:

```
commercial_01 … rebel_01   entry.use_item=0  trigger.use_item=0  CPartProp(emp)=0
```

All seven non-EMP variants: no `entry.use_item`, no `trigger.use_item`, no `CPartProp` on the
device parts. Together with A7's rotor rows, "the geometry but nothing calls it" holds.

## A9 · "the EMP pulse and its tune (2 variants)" → BROKEN

The card's own table says `emp_01` = 1, `mm250` = 2 builds minus pulse. The sentence in §5 claims
the pulse is added in *two* variants, borrowing the `CPartProp` count:

```
variants: emp_props 3 / emp_pulse 0   (mm250)
          emp_props 3 / emp_pulse 1   (emp_01)
```

`EMP.json` → `mm250` `pulses`: only `CForcePulse car_explosion_medium.ftune`. So: props 2
variants, pulse + tune 1 variant. The sentence is internally contradicted and wrong on its face.

## A10 · "damage held at full for the whole radius" → WEAK

The eight values and their names are decoded — the strings really are in the file:

```
'truck_emp.ftune', 'ForcePulseSettings', 'PlayerDamage', 'PlayerDamageRadius',
'PlayerDamageRadiusPercentageMax', 'PlayerDamageRadiusMin', 'AIDamage', …
```

What is *not* decoded is what `*RadiusPercentageMax` / `*RadiusMin` mean. Across the 23 explosion
tunes in the fleet:

```
(Pmax, Pmin)          tunes
(0.0, 0.0)              6   incl. car_explosion_medium (500 dmg in 5 m)
(0.15, 0.10)            5
(0.25, 0.25)            3
(1.0, 1.0)              3   incl. truck_emp, w613_bomb (1500/25 m), prototype_missile_explosion_sam
(1.0, 0.9)              3   machine-gun impacts (1.5–5 m, 25–150 dmg)
(0.10, 0.25)            1
(0.20, 0.10)            1
(0.05, 0.10)            1
```

Two consequences. First, `0.0/0.0` cannot mean "0 % damage" — `car_explosion_medium` kills — so the
literal reading of the names is already refuted by the corpus, and the "held at full" reading is an
interpretation of a pair whose semantics are UNKNOWN. Second, `1.0/1.0` is shared with a bomb and a
SAM: "full damage through the whole radius" is not an EMP fingerprint, it is a common blast shape.
The numbers 100 / 25 / 1 / 1 are solid (`decoded`); the words around them are `derived` at best.

## A11 · "an EMP is 3 flags + the `emp_flatbed_table`" → HOLDS as a fingerprint, "flags" inferred

The three differing members are typed `int` with values 0/1, so "flags" is a fair description, and
the pattern is unique in the whole fleet:

```
pattern (id:4912FC04, id:AE6F7EFF, id:CF4F7880) over 307 pulses
  (1,0,0) 278    (0,0,0) 16    (1,0,1) 12    (0,1,1) 1   <- the EMP
```

Their meaning stays UNKNOWN, exactly as the card says.

## A12 · "emp_flatbed_table maps every material slot to one effect hash, which is the embedded explosion_emp_flatbed.effc" → HOLDS, but it is prose, not data

This sentence is the one substantive claim in §4 that `EMP.json` cannot support: the reader records
the table as `{class, name}` only. The table is in fact a 32-slot byte array, and the hash resolves:

```
CMaterialEffectTable emp_flatbed_table EE5AEE78=FFFFD9E6
  id:AB772F9C = 66,B4,C9,CE,00,…  (32 × 16-byte records, all bytes 66 B4 C9 CE)

$ python -c 'from rbmhdr import hash_jenkins; …'
effects/destruction/explosion_emp_flatbed.effc     0xcec9b466   = CEC9B466
effects/props/emp_active.effc                      0xa90a09ba   = -1458959942  (= mm250 emitter's effect)
```

Both hashes in the card match Jenkins of the two embedded effect paths — the claim is **true**, and
the mm250 emitter's "-1458959942" is likewise proven to be `emp_active.effc`. But the sentence is
hard-coded in `render_md()` and is checked by nothing: `--check` rebuilds the same prose from the
same constants, so a wrong sentence would pass forever. Same for A8's "no trigger" and A21's
wiring (R4/R11: a table in a doc should come from data that `--check` compares).

## A13 · The prompt's meaning (silent) → HOLDS, with the evidence the card could have used

`prompt = ui_activate_emp` is decoded; that it means "activate the EMP" was inferred from the
string. The container has a `stringlookup` member the card never opened:

```
Languages[0..10].SortedPairs[·].Hash = 3386737555 = jenkins("ui_activate_emp")
  lang0 'Activate EMP'      lang1 "Activer l'IEM"    lang2 'EMP aktivieren'
  lang3 "Attiva l'EMP"      lang4 'Activar PEM'      lang6 'Aktywuj IEM'   … 11 languages
```

So the label is a shipped localised UI string, not a guess. This is the one semantic claim in the
card that can be *proven* from data, and the card left it as an inference.

## A14 · "No EMP sound" → WEAK (name-only negative)

Tested both halves of the claim and one place the card did not look:

```
emp_01 attached effects: 46 — engine_running_sound, horn, GearChange, brake_squeal_sound_heavy_vehicle,
  chassis_spinning_sound, dynamic_break_electric, water_explosion, exhaust* … (no 'emp' name)
explosion_emp_flatbed.effc: 113 printable strings, 0 matching sound|fmod|event|audio|play
fmod_guids member: 'vehicles', 'character', 'effects*'
```

No attached effect is named after the EMP (true), the effect file names no sound (true, and it also
cannot rule one out — its strings are all ADF type names), and the fmod member lists only three
banks. A pulse sound could still be played by the code that fires the pulse. "No EMP sound" is
therefore plausible but unproven; it should read "no EMP-named sound in the entity or the effect".

## A15 · "`CEMPWeapon` in two files; 0 of 88 vehicle components" → HOLDS, wider than stated

The card's negative is measured on its 53-entity sample. The cache holds **all 232 vehicle graphs**,
so the claim was re-tested at full width:

```
cached epe: 236   entities with weapon-class objects: 57
[('SWeaponPoint',302), ('CBulletWeaponBase',58), ('CLightWeaponComponent',30), ('CMissileWeaponBase',26),
 ('CBarrelSpinWeaponComponent',15), ('CAimPOIWeaponComponent',13), ('CRPGFireLeachWeapon',6),
 ('CLaserBeamWeaponComponent',3), ('CTurretWeaponComponent',2), ('CEMPWeapon',2), …]
CEMPWeapon total: 2      (only w702_emp.ee.xml and w503_turret_emp.ee.xml)
WEAPON_WIRING entities: 53   components: 88
```

0 of 232 vehicles hold the class; the only two are the handheld and the static prop, as the card
says. The honest bound is "all decoded vehicles + those two weapons", not "the game": DLC mech and
prop entities are not in this cache, and the class's EMP behaviour is still known only from its
name (R5).

## A16 · The sample/fleet distinction → HOLDS

The card's own Limit states the count covers "the 53 armed entities in `WEAPON_WIRING` (88
components), not all 233 vehicle entities". That is an honest limit, and A15's census closes it at
232/232. No further objection.

## A17 · "Both use the stock `fow_weapon` tune" → BROKEN (and it hides the useful bit)

There is no `fow_weapon` tune. The tune's class is `WeaponTuning`, and `fow_weapon` is one of four
weapon-array members. What the two EMP weapons actually do is populate *that* block:

```
w702_emp.wtunec / w503_turret_emp.wtunec  class = WeaponTuning
  members: missile_weapon, grenade_weapon, bullet_weapon, fow_weapon
  populated: fow_weapon[0]  (base_tuning.damage, impulse, recoil, scatter, shake, rumble,
             mounted_input, sungun_tuning, typhoon_tuning, namaste_tuning, stupka_tuning,
             missile_strike_tuning, balloon_tuning, ai_tuning …)

w610_fighterjet_mgun.wtunec   rows 148   bullet_weapon 128   fow_weapon 1 (empty)
w608_fighterjet_missile.wtunec rows 148  missile_weapon 128  fow_weapon 1 (empty)
WEAPONS.md §1 blocks: 11 bullet, 11 missile, 0 fow among the 22 vehicle weapons
```

So the EMP weapons are the only weapons seen that carry their numbers in the FOW block — the
special-weapon tuning that also holds Sun Gun / Typhoon / Namaste / Stupka / balloon-strike
sub-tunings. That is a data-side distinction the write-up erases, and it is the closest thing to a
"carrier" for the effect. The substantive half of the claim survives: the only string containing
"emp" in either tune is the tune's own file name (`w702_emp.wtune`), so no EMP-named field exists.

## A18 · "damage 500 / range 50 m / 750 m", "magazine 1" → units WEAK, magazine BROKEN

```
w702: damage 500.0  max_range 50.0   magazine_size 1   fire_rate 0.0   velocity 400.0
w503: damage 500.0  max_range 750.0  magazine_size 3   fire_rate 0.5   velocity 600.0
```

`EMP.json` records `magazine_size 3` for w503; the §12 row and the MODLOG ("magazine 1") repeat the
w702 value for both. The md's own §6 table avoids the number, so only the tracker and log are wrong. "50 m / 750 m" labels `max_range` as metres
on the strength of the world-coordinate convention: the field sits in the same 200…1000 band as
every vehicle weapon's `max_range` and entity positions are metres, but no file states the unit, so
it is `derived`, not `decoded`. Also worth stating: the 500 is `fow_weapon[0].tuning.base_tuning.damage`
(player); the AI damage in the same block is **190**.

## A19 · "w702 handheld two-handed" / "w503 static prop with its own rigid objects and hinge" → HOLDS (structure), WEAK ("spin-up dials")

```
w503_turret_emp.ee  19 objects: CRigidObject 2, CConstraint 2, CConstraintLimitedHingeData 2,
                    CConstraintPositionMotorData 2, SPhysicsParams 3, CTurretWeaponComponent 1
w702_emp.ee         31 objects: CBarrelSpinWeaponComponent 3, CInteractionComponentPickup 1,
                    CWallPenetrationWeaponComponent 1
paths: jc_weapons/02_two_handed/w702_emp, jc_weapons/05_stationary/w503_turret_emp
```

Two hinges with position motors = the turret's aim mechanism, as described. "three
`CBarrelSpinWeaponComponent`s **for the spin-up dials**" is a name-based function claim (R5) — the
class is real, what it turns is not decoded.

## A20 · `weapon_type` 6 / 2 as "handheld / static turret" (silent) → WEAK

The md puts `kind` (from the directory names) directly above `weapon id / type`, inviting a
correspondence the fleet refutes:

```
w011_pistol_u_pozhar_98   CBulletWeaponBase  id 11   type 0
w111_assault_rifle_up_39  CBulletWeaponBase  id 111  type 1
w501_turret_sam_v2        CMissileWeaponBase id 501  type 2
w503_turret_emp           CEMPWeapon         id 503  type 2
w702_emp                  CEMPWeapon         id 702  type 6
WEAPON_WIRING.md: "its weapon_type is 2 for every weapon" (all vehicle weapons)
```

`2` is the mounted/vehicle norm (it is also on a SAM turret and on the EMP turret); `6` is the
outlier and is unique among the five weapons sampled. Whether `6` means "FOW/special" is UNKNOWN —
there is no `weapon_type` census in the repo to decide it. The card's `kind` labels are from paths,
not from the member.

## A21 · "Any vehicle entity that carries the same objects gets the same device" → WEAK

This is the answer's load-bearing sentence, and the donor's own data weakens it. The EMP pulse is
ownerless while the plain blast has an explicit owner, and the truck has no graph-script object —
the only other entity that runs the same use-item state does:

```
truck CCar.id:B5AE7986 -> CForcePulse (plain) ; EMP pulse: 0 inbound refs; CGraphScriptGameObject: 0
plane v4603…mm340: CGraphScriptGameObject ×2, one GraphScript id:65424AC6 -> 875B9AD5=FFFF75FD
      = CForcePulse 'explosion_force_pulse' on w704_m488.ftune (its own BOMB_JEEP blast)
plane entry.use_item: S_STUNT_USE_ITEM_VEHICLE, prompt ui_activate_cargobay_door
```

In the plane, the use-item state has a script object that owns a dedicated pulse. In the truck,
nothing owns the EMP pulse and no script object exists in the `.epe`. Either the firing is hard-coded
per entity in the engine, or the link lives outside the container. "Carry the same objects → get the
same device" therefore understates the risk: the same objects in the donor are, by every decoded
pointer, inert data. The card does say the firing is code/UNKNOWN; it should not also say that
carrying the objects is sufficient.

## A22 · "cannot be copied as a weapon-slot weapon" → HOLDS for the disable, WEAK as the whole answer

The disable half is sound: 0 of 232 vehicles carry `CEMPWeapon`, and the class is the only
EMP-named carrier in the data (A15), so there is no data-only route to the *disable* effect. But the
card never evaluates the path its own §12 row names ("or a missile with an EMP explosion tune"), and
that path is visible in the data: every weapon's blast is a `CForcePulse` whose `SettingsFile` is a
per-weapon `.ftune`, so pointing one at `truck_emp.ftune` is exactly how the game sizes any weapon
blast:

```
v0201_car_capstone_mediumtank_*.ee  w602_mediumtank_canon        -> w602_mediumtank_canon.ftune        (CBulletWeaponBase)
v0300_car_kensington_…_preorder.ee  w618_sportsmuscle_missile    -> w618_sportsmuscle_missile.ftune    (CMissileWeaponBase)
v5603_train_urga_monorailmissilecar CForcePulse                  -> rpg_assault_helicopter.ftune       (CMissileWeaponBase)
```

That route copies 100 damage in 25 m (A10/A18) but not the disable — unless the disable rides the
three unnamed ints, which is UNKNOWN. As an answer to "can the EMP effect be fired by a driver of a
different vehicle", "no as a weapon, yes as objects" is incomplete: it omits "yes as a blast tune,
damage only", which is the cheapest path and the one the tracker already proposes for WPN-4.

## A23 · "the ordinary explosion pulse every car has" / "the stock blast every car carries" → WEAK

```
entities: 232   entities with a car_explosion_medium pulse: 115
```

About half the vehicle fleet; the rest use boat/plane/bike/heli/barrel tunes. True for the truck,
over-general for the fleet. Not load-bearing, but it is the kind of "every" that becomes a rule
later.

## A24 · "Duration … not in the files" → WEAK (right for gameplay, wrong for the effect)

The tune is exactly eight named numbers (proven by the strings in A10), so no gameplay duration is
in it. But the embedded `explosion_emp_flatbed.effc` is a runtime effect with `Timelines`,
`StartTime`, `EmitterLifetimeIndex`, `MaxParticles` etc. — the *visual* duration is in the files;it is the *disable* duration that is not. Also: the tune's absence of a duration does not prove the
disable duration is absent from the pulse, because the pulse still has 25 hashed members and the
three EMP-only ints are unnamed. "Not in any decoded member" is the accurate form; the card's
"not in the files" is a step too strong.

## Where the card is at its best

- The copy list is the right shape and the right granularity (parts, props, pulse, tune, table,
  effect, trigger, module row), and A12 proves the two effect hashes in it.
- The two negative answers — no weapon component, no pointer to the pulse — are clean and both
  survive independent, wider tests.
- The `mm250` reading (a charging prop with the emitter disabled at spawn, no pulse) is correct and
  is the single most useful observation for the Batmobile: the mission build proves the device can
  exist without the pulse.
- Recording duration/disable as UNKNOWN rather than inventing numbers is exactly R4.

## What should change in the card's outputs

1. §5 "Same members, same parts, same trigger, same prompt" → mm250's entry is `enabled 0` and its
   trigger link id differs (A6).
2. §5 "the parts module is shared by all 9 variants" → three distinct modules (A7); the identical
   `rebel_01`/`emp_01` module is the better fact to report.
3. §5 "the EMP pulse and its tune (2 variants)" → 1 (A9).
4. §2 "the pulse's other members are … object-id properties … one ref dangling" → `id:06A05F33` is a
   `vec_events` list whose targets are never local (A5).
5. §6 "Both use the stock `fow_weapon` tune" → `WeaponTuning` with the `fow_weapon[0]` block
   populated (A17); add "player 500 / AI 190, w503 magazine 3" (A18).
6. §2 "damage held at full for the whole radius" → keep the numbers, mark the reading `derived` and
   note that `1.0/1.0` also ships on the bomb and the SAM (A10).
7. Add: prompt key `ui_activate_emp` = "Activate EMP" in 11 languages (A13); `emp_flatbed_table`
   slot = Jenkins of `explosion_emp_flatbed.effc` (A12); the cargo plane as the only other user of
   `S_STUNT_USE_ITEM_VEHICLE` and the only one whose pulse has a `CGraphScriptGameObject` owner
   (A21).
8. Every sentence added in 7 should be in `EMP.json`, not only in the template, so `--check` can
   fail when the data changes.

---

**Reproduce.** All probes read `Research/JC3Grab/{INDEX.jsonl,EMP.json,FORCEPULSE.json,
WEAPON_WIRING.jsonl,WEAPONS.md}` and `E:\Modding\_JC3grab\wiring\epe\*.xml`; the three archive reads
(the two `.ftunec`/`.stringlookup` extractions, one vehicle weapon tune on each side) used
`jc3grab.read_entry` + `jc3detail.inner_files` read-only against `D:\Games`. Nothing was written
outside this file.
