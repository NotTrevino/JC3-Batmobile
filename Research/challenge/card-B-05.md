# Assumption challenge — card B-05 · Entity graph (`.epe`)

**Scope.** `GRAB_BACKLOG.md` §0.5 (R1–R14), §8 card `B-05`, §12 row, MODLOG
§"B-05 · Entity graph (`.epe`) — done" and §"B-05 rework — intended change", the spec
`Research/specs/B-05.md`, `tmp/freebuff/reports/B-05.md`, `rework-B-05.md`, and the artefacts
`Working/Entity/bm_epe_edits.json`, `Builds/bm-005`, `Tools/scripts/bm_entity.py`.

**Method.** Every claim below was re-derived from files on disk with the project's own reader
(`jc3wiring.parse_epe`), the project's own hash (`rbmhdr.hash_jenkins`), `ConvertProperty`, and a
census over the 295 cached fleet graphs in `E:/Modding/JustCause3/_grab/wiring/epe` (named by
`GRAB_BACKLOG.md` §0.6). Scratch exports went to the OS temp dir only. No file in the repo was
modified except this report; no game was launched, nothing was written under `D:/Games` or
`E:/Games`, no build was touched, no git command ran. `bm_entity.py --check` was deliberately
**not** executed because it rewrites `tmp/b05/built.xml`; its individual claims were reproduced
instead (round trip, det, module bytes, counts).

Absolute numbers used throughout (fleet census, 295 graphs / 107,625 objects):
`SWeaponPoint` 420 · `CBulletWeaponBase` 96 · `CMissileWeaponBase` 35 · `SVehicleLight` 4707 ·
`CPartProp` 13,440 · `CForcePulse` 427 · `CInteractionGraphEntry|Exit` 11,751.
Built graph (on disk, `f4abe91d…`, 124,488 B): 467 objects = 466 classed + classless root,
46 classes, 4 `CBulletWeaponBase`, 0 `CMissileWeaponBase`, 1 `CForcePulse`, 6 `CPartProp`,
9 `SWeaponPoint`, 28 `SVehicleLight`.

---

## VERDICT SUMMARY

| # | Assumption | Verdict |
|---|---|---|
| A1 | The base `.epe` is the shipped graph; "6 props / 42 parts is the shipped pattern", so step 1 adds 0 props | **BROKEN** — the shipped graph is 450 objects / 40 props; the base is 416 / 6 |
| A2 | No `CPartProp` carries a behaviour (so props cannot be needed for behaviour) | **HOLDS** — 13,440/13,440 props have the same 5–6 admin members |
| A3 | The APC's `CBulletWeaponBase` is an acceptable carrier for the two `w618` **missile** rows (R5) | **BROKEN** — the fleet's `w618` is `CMissileWeaponBase`, and the same vehicle's armed variant is on disk |
| A4 | "No root slot is free" for the two `w618` components (`unbound[]`) | **BROKEN** — `mounted_weapon` is a used weapon slot (7 fleet vehicles) and is `00000000` in the build |
| A5 | T-WP4 is satisfied by one `SWeaponPoint` | **BROKEN** — the card's `CForcePulse` copy was not made and is not in `declared[]`/limits |
| A6 | `id:851CAABE` = `main_weapon`, `id:00568A74` = the second slot (decoded, not inferred) | **HOLDS** for `851CAABE` (hash decodes); **WEAK** for `00568A74` (name still UNKNOWN; role is per-vehicle) |
| A7 | `name_hash == hash_jenkins(name)` for every added/edited object | **HOLDS** — 0 mismatches in 18,698 fleet objects of these classes |
| A8 | The entry/exit matrix "sits in an unnamed member `id:999864F0`/`id:C8F5DB5C`", so entries keep donor placement | **BROKEN** — that unnamed mat is identity in 11,751/11,751 fleet entries/exits; it is not a placement |
| A9 | "15 of 84 transforms" is a coverage gap to be carried to V-03 | **BROKEN** as a completeness metric — 60 of the 84 objects have no transform of their own in any vehicle |
| A10 | `attach.vehicle` part binding goes through the three unnamed string ids, in mount/turret order | **WEAK** — mechanism exists but is a sample of exactly one vehicle (3/3 instances, all APC) |
| A11 | The six custom lights inherit `Front_Left_Point`'s placement ("all six sit at that lamp"), and B-07's module anchor will fix it | **WEAK** — the inherited mat has zero translation; "co-located" is not what the numbers show, and B-07's placement is unproven |
| A12 | All 19 B-04 part names are present in the built module | **HOLDS** — boundary-checked against the 39,278 B module, each name 2 structured occurrences |
| A13 | `SOCKETS_JC3.json position_m` is directly usable in `.epe` space (units/axes) | **HOLDS** for units/axes (det +1, row-major); **WEAK** for the `.epe`-origin identity (no on-disk proof) |
| A14 | `ConvertProperty` round-trips the built `.epe` byte-identically and `--write` is deterministic | **HOLDS** — reproduced now (same sha, identical 502,109 B XML) |
| A15 | The MODLOG "done" record and §12 describe the artefact on disk | **BROKEN** — §12 is current; MODLOG's done section and its verbatim block still cite the pre-rework file |
| A16 | T-WP5 has no carrier and no trigger (a "no carrier exists" claim) | **WEAK / partially contradicted** — pulses are bound to weapon components in the fleet; only the *firing* trigger is genuinely UNKNOWN |
| A17 | "Builds/bm-005 ships a loose `.epe`; the install is unproven offline" | **HOLDS as a declared limit** (verified: no `.ee` in the aaf, 1 file differs from bm-009) |

Counts: **6 BROKEN, 5 WEAK, 6 HOLDS** (some sections carry two verdicts). The card's *mechanical*
claims — hash resolution, round trip, module bytes, deterministic write — are solid. Its
*completeness* claims are where it fails, and the two largest failures (A1, A3) were both
documented in the project's own earlier evidence that the final session overrode.

---

## A1 — "The base graph is the shipped graph; the shipped pattern is 6 props / 42 parts"

**The assumption, stated.** `Research/specs/B-05.md` L-3: *"the base graph carries **6** `CPartProp`
for **42** parts … adding 19 props would be the shipped pattern's opposite (6/42)"*. §12 repeats
*"0 `CPartProp` by declared narrowing (spec L-3: 6 props / 42 parts shipped, no prop carries a
behaviour)"*. Silent premise: `Builds/bm-009`'s `.epe` is a faithful copy of the shipped entity.

**Test.** The same entity's shipped graph is in the fleet cache. Counted with the same reader:

```
$ python -c "... jc3wiring.parse_epe('E:/Modding/JustCause3/_grab/wiring/epe/v0300_..._civilian_01.ee.xml')"
fleet civilian objects 450  CPartProp 40
base (bm-009, tmp/b05-spec/bm-009.xml) objects 416  CPartProp 6
missing from base: 34
['sportsmuscle_c_mirror', 'sportsmuscle_door_f_l', 'sportsmuscle_door_f_l_window',
 'sportsmuscle_door_f_r', 'sportsmuscle_door_f_r_window', 'sportsmuscle_engine',
 'sportsmuscle_f_l_seat', 'sportsmuscle_f_r_seat', ... 34 names]
```

The fleet census says 6/42 is not the shipped pattern but the *outlier*:

```
233 graphs matched to PARTS_TABLE
props/parts ratio: min 0.32  median 1.00  max 1.35
ratio>=0.9: 199  |  ratio<0.3: 0
   SM  v0300_..._sportsmuscle_civilian_01.ee.xml  props= 40 parts= 42 ratio=0.95
   SM  v0300_..._sportsmuscle_debug.ee.xml       props= 40 parts= 42 ratio=0.95
   SM  v0300_..._sportsmuscle_signature_...      props= 41 parts= 42 ratio=0.98
```

**Verdict: BROKEN.** The base is a damaged graph, and the project already knew it. MODLOG
§"B-05 — deferred: the base graph is missing 34 part props…" (line 17827) measured exactly this
(`CPartProp 40 → 6, delta −34`, `450 − 416 = 34 = 40 − 6`), called step 1 *"a repair"* of 32 of the
34 plus 19 new parts, and proposed the whole-graph gate **"`CPartProp` count == part count"**. The
final session instead re-read 6/42 as the shipped pattern and added 0, so the gate that would have
caught the regression was never run.

**Consequence.** Done criterion 3 (`416 + 51 = 467`) is arithmetically true but measured from a base
that is missing 34 objects the shipped entity carries. The built car is 467 objects where the
shipped entity plus the 51 planned additions is 450 + 51 = **501**. This is a correctness gap in the
deliverable, not merely a bookkeeping one, and it is not listed among the card's limits.

---

## A2 — "No `CPartProp` carries a behaviour"

**The assumption.** L-3/§12: *"no prop carries a behaviour"*, therefore props are not needed for
lights or weapons, therefore step 1 may add none.

**Test.** Member-name census over every prop in the fleet:

```
CPartProp member-name census (fleet):
  _object_id: 13440   name: 13440   name_hash: 13440
  part_index: 13440   id:D04059E6: 13440   _GUID: 13374
```

Every one of 13,440 props has the same identity/admin members and nothing else.

**Verdict: HOLDS.** The *behaviour* half of L-3 is correct: a prop is a name+index binding, not a
behaviour. (This does not rescue A1 — the fleet's near-1:1 props:parts ratio shows props are still
the shipped way to register a part, even without behaviour members.)

---

## A3 — The APC `CBulletWeaponBase` template is an acceptable carrier for the missile rows (R5)

**The assumption, stated.** The generator docstring: *"The components are clones of the armed APC's
`CBulletWeaponBase` … the ~60 unnamed members are copied verbatim, because their meaning is
UNKNOWN. That means the unnamed weapon-path members still name the donor template until B-06
repoints them."* The rework report calls the class mismatch a *"residual observation"*, and §12
carries it only as *"components are APC clones (32 `w206`-path strings …) for B-06 to repoint"*.

**Test 1 — what class a `w618` weapon is in the fleet.**

```
('CMissileWeaponBase', '2', '618') 2
('CBulletWeaponBase', '2', '618') 0
```

**Test 2 — the same vehicle's armed variant is on disk**, and it carries the thing B-05 needed:

```
v0300_..._signature_preorder.ee.xml  464 objects  props 41  lights 22  points 4  CMissileWeaponBase 1
  component CMissileWeaponBase w618_sportsmuscle_missile A7E417D5=FFFF20AF
Research/JC3Grab/SIGNATURE_DIFF.json → weapon.class = "CMissileWeaponBase",
  weapon_type 2, 4 points (fire..fire4), slots {id:851CAABE: A7E417D5=FFFF20AF, …}
```

**Test 3 — what the build actually contains.**

```
CBulletWeaponBase: 4      CMissileWeaponBase: 0
  CBulletWeaponBase w618_sportsmuscle_missile      wid 618 type 2
  CBulletWeaponBase w618_sportsmuscle_missile_emp  wid 618 type 2
grep -o w206 built.xml | wc -l          → 32
grep -o 50calImpact | wc -l             → 4
```

**Verdict: BROKEN (R5).** The two missile rows are carried by bullet-weapon objects whose unnamed
majority is w206 ("M2 .50 cal") data. The requirement "weapon components … per T-11" is carried by
the objects' *names*, not their behaviour, and a like-for-like donor (`CMissileWeaponBase`, same
vehicle, same 4 points) was available in the project's own cache. The card's `T-WP3`/`T-WP4`
"written" statements rest on a class substitution that no row justifies.

**Consequence.** B-06 is asked to "repoint" the clone, but a repoint cannot change a class. The
missile components need to be rebuilt from the missile donor, not patched.

---

## A4 — "No root slot is free": the two `w618` components are unbound

**The assumption, stated.** `declared[]`: *"no pointer is free: `main_weapon` and `id:00568A74` are
the cannon and Vulcan, `id:AC0BC788` and `mounted_weapon` ship `00000000`."* §12: *"the two `w618`
components are **unbound** (`unbound[]`: no free root slot exists)"*.

**Test 1 — which root members bind weapon components anywhere in the fleet.**

```
slot -> vehicles: {'mounted_weapon': 7, 'id:00568A74': 16, 'id:851CAABE': 17}
vehicles by #bound weapon slots: {1: 16, 2: 12}
vehicles with >=3 bound slots: 0
```

`mounted_weapon` is a *named* weapon slot: hash_jenkins("mounted_weapon") = `0x4B86679F`, and the
APC binds its `w206` there (`v0200_car_capstone_apc_debug.ee.xml` →
`mounted_weapon = '53FFE54B=FFFFC221'`).

**Test 2 — the built graph's own slot values.**

```
slots: main=851CAABE DF009C2C=FFFF8002  00568A74 DD9B64C0=FFFF8005
       AC0BC788 00000000  mounted_weapon 00000000
    mounted_weapon -> 00000000
```

**Verdict: BROKEN.** A null pointer is the *definition* of a free slot, and `mounted_weapon` is
proven to accept a weapon component both in this very entity family (the sportsmuscle's `CCar`
carries the member) and in seven fleet vehicles. At minimum `w618_sportsmuscle_missile` could have
been bound there. The fleet census does support "there are only three such slots and no vehicle
binds three at once", so *one* of the two missiles may still be unbound — but the claim as written
("no pointer is free") is false, and the limit understates what was buildable.

---

## A5 — T-WP4 is satisfied by one `SWeaponPoint`

**The assumption, stated.** §12 and the report list T-WP4 as written: *"w618 emp 1 point"*. The card
step 2 and the structural row require more:

```
t7_weapons_edits.json: {"row":"T-WP4","what":"`SWeaponPoint` at `BattleModeSpotLight` with the
  -20 deg pitch + a `CForcePulse` copy","note":"the launcher's own LaunchSocketName, G2-16's pulse"}
```

**Test 1 — pulse objects in the build.**

```
CForcePulse: 1
  name= CForcePulse  id= 68834B60=FFFF7104        (bm-009's own generic pulse, unchanged)
base bm-009: CForcePulse CForcePulse 68834B60=FFFF7104
```

**Test 2 — what the same vehicle's armed variant does.** `SIGNATURE_DIFF.json` `graph.added`
contains `{"class":"CForcePulse","name":"w618_sportsmuscle_missile"}` — a *named* pulse added with
the missile. **Test 3 — pulses are a weapon-component attachment in the fleet:** 427 `CForcePulse`
objects, 404 with an external reference; the referencing parents are
`CBulletWeaponBase` 50, `CMissileWeaponBase` 35, `CCar` 163, `CBoat` 46, …

**Verdict: BROKEN.** The `CForcePulse` copy that T-WP4 names was not created, and its absence is in
neither `declared[]`, `unbound[]`, the report's limits, nor §12. This is a silent omission of half a
structural row, unlike T-WP5 which is explicitly blocked. (The `-20°` pitch is also not recorded in
the built point's `world`; the point uses the socket basis verbatim.)

---

## A6 — Root slot identity: `id:851CAABE` = `main_weapon`, `id:00568A74` = second slot

**The assumption.** The generator's `WEAPONS` table hard-codes `slot_hash: "851CAABE"` for
`main_weapon` and `"00568A74"` for `secondary`, sourced from `T7_WEAPONS.md`/T-WP13 ("the medium
tank's second driver slot"). This is the R5 risk: a member identified by a name that *sounds* right.

**Test 1 — decode the hash.** `rbmhdr.hash_jenkins("main_weapon") & 0xffffffff` = `2233248446` =
**`0x851CAABE`**. So the id is not an inference: the game's own member hash decodes to `main_weapon`.

**Test 2 — the other id.** No candidate in a 3,521-word vocabulary (repo docs + fleet member names,
plus hand-built `_weapon`/`weapon_*`/`slot_*` combinations) hashes to `0x00568A74`. The name is
UNKNOWN; only the behaviour (16 vehicles bind a weapon component there) is measured.

**Test 3 — is `851CAABE` exclusively a cannon slot?** No: the same vehicle's armed variant binds its
`CMissileWeaponBase w618` to `id:851CAABE` (`SIGNATURE_DIFF.json weapon.slots`). The slot is
`main_weapon`; *what* occupies it is per vehicle.

**Verdict: HOLDS for `851CAABE` (hash-decoded); WEAK for `00568A74`** (role inferred from one donor
class, name unknown). No evidence contradicts either binding.

---

## A7 — `name_hash == hash_jenkins(name)`

**The assumption.** Done criterion 2 is built on this equality (41/41 added objects checked). Silent
premise: the equality is universal, so a correct hash means a resolvable name.

**Test.** Fleet-wide, all objects of the relevant classes, normalising signed/unsigned 32-bit:

```
CPartProp:          name_hash==jenkins(name) 13440, differ 0
SVehicleLight:      name_hash==jenkins(name) 4707,  differ 0
CBulletWeaponBase:  name_hash==jenkins(name) 96,    differ 0
SWeaponPoint:       name_hash==jenkins(name) 420,   differ 0
CMissileWeaponBase: name_hash==jenkins(name) 35,    differ 0
```

**Verdict: HOLDS.** This is the card's strongest claim; the hash is a decode, not a convention.

---

## A8 — The entry/exit transform "sits in an unnamed member `id:999864F0` / `id:C8F5DB5C`", so entries keep donor placement

**The assumption, stated.** §12: *"60 entries/exits/transitions with an unnamed matrix member
`id:999864F0`/`id:C8F5DB5C` (UNKNOWN)"*; report limit 3: *"entries and exits keep their donor
placement; V-03 will see it."* Silent premise: the unnamed mat the code found is the placement
transform.

**Test 1 — what that unnamed mat contains across the fleet.**

```
entry/exit objects with an unnamed mat: 11751  non-identity: 0
```

All 11,751 `CInteractionGraphEntry`/`Exit` objects in 295 graphs carry the same identity matrix
(`1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1`). A member that is identity in every vehicle is not a
per-instance placement.

**Test 2 — where the positions actually come from.** The transform carrier is the point node /
trigger, which B-05 *did* write:

```
CInteractionGraphPointNode point.driver    built=(-1.571,1.15,-0.95)  t9=[-1.571, 1.15, -0.95]
CInteractionTrigger       trigger.driver   built=(-1.571,1.15,-0.95)  t9=[-1.571, 1.15, -0.95]
… 15/15 written origins equal t9 pos_m
```

and in t9 every entry's position equals its point node's position (`entry.driver` and
`point.driver` are both `[-1.571, 1.15, -0.95]`).

**Test 3 — identify the two hashes.** None of 3,521 candidate names (including `world`, `mat`,
`transform`, `matrix`, `local`, `WorldMatrix`, `transform_local`, all fleet member/class names)
hashes to `0x999864F0` or `0xC8F5DB5C`.

**Verdict: BROKEN.** The named member is not the placement; the skipped entries/exits have no
placement of their own to preserve. The claim "entries keep donor placement" is therefore not
supported by any measurement, and the 60 skipped rows are not 60 unplaced objects. The hash
identity remains genuinely UNKNOWN, but it is a different unknown than the card describes.

---

## A9 — "15 of 84 transforms" is a coverage gap

**The assumption.** §12/report: *"**15/84** interaction transforms … entries and exits keep their
donor placement"*, carried as the card's first limit.

**Test.** `t9_interaction.json` has 85 objects / 84 with a `transform`; the skipped classes are
29 `Entry` + 26 `Exit` + 12 `Transition` + 2 `CInteraction` = 69, of which the build skips 60 for
"no named `world`" and 9 for duplicate class+name. Fleet test A8 shows `Entry`/`Exit` never carry a
transform; the `CInteraction` class carries none either (the code's own comment). The only classes
with a placement in this graph family are `PointNode` (8) and `Trigger` (7) — exactly the 15 written.

**Verdict: BROKEN as a completeness metric.** The denominator counts objects that have no transform
member in any shipped vehicle. Reporting 15/84 makes a complete step look 18 % done and sends V-03 to
look for a placement defect that does not exist. The honest number is "15/15 objects that own a
transform"; the surviving real unknown is the 9 duplicate class+name transitions (3 objects each).

---

## A10 — `attach.vehicle` binds parts through three unnamed string ids, in mount/turret order

**The assumption.** The template carries the part names in *unnamed* string members after `world`
(`PART_REF_IDS = ("5C19E7E0", "80201E4D", "A90F5E74")`); B-05 writes `strs[0]=mount`,
`strs[1]=turret`, drops the third.

**Test.** Fleet census of every `attach.vehicle` point:

```
attach.vehicle part-ref string members, by id attr:  5C19E7E0 3   80201E4D 3   A90F5E74 3
type values: {'4': 3}
sample values: ['apc_weapon_mount_vertical', 'apc_turret_base', 'weapon_anchor']
```

Three instances in 295 graphs, all in the APC, all with the same three ids. Built graph:

```
refs by id: [('5C19E7E0','string','batmobile_cannon'),
             ('80201E4D','string','batmobile_turret')]  type= ['4']
… ×4 components
```

The ordering matches the donor (`5C19E7E0` = mount, `80201E4D` = turret). **Verdict: WEAK.** The
mechanism is consistent, but it is a sample of exactly one vehicle, and the omission of
`weapon_anchor` was justified only by "B-04 has no part with that name" (checked: no B-04 part name
contains `anchor`). A different vehicle's `attach.vehicle` point — if one existed — is the only thing
that could confirm the ids are semantic rather than APC-specific. None exists in the cache.

---

## A11 — The six custom lights inherit `Front_Left_Point`'s placement; B-07 will place them

**The assumption, stated.** `declared[]`: *"every clone inherits `Front_Left_Point`'s slots, so all
six sit at that lamp and keep its `preset_id` … placement is B-07's module anchor, not this step."*

**Test 1 — the inheritance is real.** The build's 28 lights group by `id:A04C3B1E` as:

```
0.7198463,-0.6040228,-0.3420202,0, … -> 7  ['Front_Left_Point',
  'sportsmuscle_wheel_f_l_arch_light','headlight_battle_right_light',
  'sportsmuscle_wheel_f_r_arch_light','headlight_battle_left_light',
  'sportsmuscle_wheel_f_l_arch_battle_light','boot_light_light']
```

**Test 2 — but that matrix carries no translation.** Every light matrix in the build ends in
`…, 0,0,0,1` or `…, 0,0,0.5,1`; the 8 distinct matrices use only rotation/scale, and translation is
zero for all 28. `SVehicleLight` has no part-name member (`member names` census: photometric
members + `id:*` slots only). The lights module is what binds `part`/`part_index`/
`deformable_transform` (`Working/Lights/v082/lights.xml`, `VehicleDynamicLight` members).

**Verdict: WEAK.** The clones do inherit the donor's orientation and `preset_id`, but the statement
"all six sit at that lamp" is not shown by the data — a zero-translation matrix cannot place
anything at a lamp. What is actually wrong is inherited *orientation* and preset; what is actually
unverified is the forward-looking claim that B-07's module entry will position them (B-07 is `todo`,
and `LGT1_FINDINGS.md` §7 says the name-chain question itself is still an unrun one-install probe).

---

## A12 — Every B-04 part name resolves in the built module

**The assumption.** Done 2: *"all 19 B-04 part names are present … read from the module's bytes by
`--check`."* The risk (flagged by the earlier review) is substring coincidence.

**Test.** Boundary-aware scan of the 39,278 B module: each name must occur with a non-identifier
byte on both sides.

```
module bytes 39278 names 19
names whose bytes are absent or only substring: none
batmobile_jet hits 2   batmobile_turret hits 2   batmobile_missile_pod_l hits 2
```

**Verdict: HOLDS.** (Two occurrences each, both structured — not an accident of a longer string.)

---

## A13 — `position_m` from `SOCKETS_JC3.json` is directly usable in `.epe` space

**The assumption.** R2's single transform produces socket positions "already in JC3 space", and the
generator writes them straight into `SWeaponPoint.world` / `SVehicleLight` matrices without
rescaling. Silent premises: (a) entity-graph space is metres; (b) the basis is row-major rows
0–2 = X/Y/Z, row 3 = origin; (c) the graph origin is the assembled body's origin.

**Test 1 — the built mats.**

```
CannonMuzzle         det=+1.0000 origin=[0.0003, 1.7025, -0.4559]
ChainGunMuzzle       det=+1.0000 origin=[-0.4074, 1.5519, -0.1669]
MissileL             det=+1.0000 origin=[0.5938, 1.4847, -1.1468]
MissileR             det=+1.0000 origin=[-0.5888, 1.4897, -1.1468]
BattleModeSpotLight  det=+1.0000 origin=[0.0004, 1.8346, -0.0664]
```

All orthonormal, det +1, matching the fleet's 420/420 convention.

**Test 2 — scale sanity against shipped data.** The shipped interaction point nodes are
`(-0.44,0.34,0.2)`, `(0,1.487549,0.421875)`, `(0,1.050659,-1.504883)` for a 3.72 m car; the new
Batmobile values (`-1.571,1.15,-0.95`; `0,2.2467,-0.5`) are the same order of magnitude in metres.
The donor `SWeaponPoint` `FirePosition` in the APC sits at `y≈2.63` for a ~2.6 m vehicle.

**Verdict: HOLDS for (a) and (b); WEAK for (c).** Nothing on disk ties `bat_assemble`'s per-part
`offset`/centring (`bat_assemble.py:665`, `offset = [-xc, a.ground-ground, a.center_z-zc]`) to the
`.epe` entity origin; the identity `graph space == assembled-body space` is only checkable in game.
The card does not state it as an assumption.

---

## A14 — Round trip and determinism

**The assumption.** Done 1 and the `--write` determinism claim.

**Test (re-run now, export to OS temp only).**

```
e1=0  i=0  e2=0
f4abe91da0bc3ce371edb1da135e0eb34357555741a409cb377b0785cb4e9fdf *…/v0300_…_civilian_01.epe
f4abe91da0bc3ce371edb1da135e0eb34357555741a409cb377b0785cb4e9fdf */tmp/tmp.…/rt.epe
XML identical 502109 B
```

**Verdict: HOLDS.** Same sha and same 502,109 B XML as the rework report.

---

## A15 — The MODLOG "done" record and §12 describe the artefact on disk

**The assumption, silent.** The §12 row's evidence paths and the MODLOG section describe the current
file. A reader taking the evidence at face value gets the right bytes.

**Test.** On-disk artefact vs the two records:

```
disk:  Builds/bm-005/…_civilian_01.epe     124488 B  f4abe91d…
§12:  ".epe 124,488 B `f4abe91da0bc3ce3…`"                          → current
MODLOG §"B-05 · Entity graph (`.epe`) — done":
      "d118c0aa29167a5e…", "124,520 B" and a verbatim `--write` block quoting that sha   → stale
grep "^## B-05" MODLOG.md  → last section is "B-05 rework — intended change";
                              no "B-05 rework — done" section exists
```

`tmp/freebuff/reports/rework-B-05.md` states: *"`MODLOG.md` | `B-05 rework — intended change` +
`B-05 rework — done` (appended)"*. That is not true on disk.

**Verdict: BROKEN (R14).** §12 was updated; the MODLOG done section — the record the §12 row itself
cites — still asserts a file that no longer exists (wrong size, wrong sha), and the append the
rework report says happened did not. Anything that re-runs the quoted verbatim block will "fail" and
be tempted to rebuild the pre-rework file. (This is bookkeeping, not geometry — A14 shows the
artefact itself is sound.)

---

## A16 — "T-WP5 has no carrier, and no trigger exists"

**The assumption.** Report/spec L-1: *"`T-WP5` has no trigger in any file"*; `T7_WEAPONS.md`:
*"no slot: the pulse is an entity object … the trigger stays UNKNOWN"*; T10 row: *"the EMP effect has
a carrier (`CForcePulse`) but the weapon-slot copy does not."*

**Test 1 — do pulses have a carrier/binding in the fleet?**

```
CForcePulse total 427  graphs 285  with an external reference (owned) 404
referencing parent/member: CForcePulse/_object_id 427, CCar 163, CBulletWeaponBase 50,
  CBoat 46, CMissileWeaponBase 35, CHelicopter 28, SDeformPointAttachment 24, CAirPlane 21, …
```

A `CForcePulse` is attachable to a weapon component (85 such refs), and the same vehicle's armed
variant ships exactly that (`SIGNATURE_DIFF.graph.added` `CForcePulse:w618_sportsmuscle_missile`).

**Test 2 — a firing trigger in the decoded files?** Not found in this session either; the only
pulse-specific tune named is `truck_emp.ftune`, and G2-17's own census records 14 unowned pulses with
the firing moment UNKNOWN. So the *trigger* claim is consistent with the evidence available.

**Verdict: WEAK / partially contradicted.** "No carrier exists" is wrong as stated — an
entity-level `CForcePulse` bound to a weapon component is a shipped, common carrier (and the direct
prerequisite for T-WP4, see A5). "No trigger exists in any decoded file" remains UNKNOWN-supported,
not proven.

---

## A17 — The loose-`.epe` install is unproven (declared limit)

**The assumption (declared, not hidden).** *"`Builds/bm-005` stages the aaf and the loose `.epe`;
there is no `.ee`/`.toc` re-pack … Whether JC3 honours a loose `.epe` … is UNKNOWN offline."*

**Test.** The build tree and the diff from its base:

```
bm-009 files 689   bm-005 files 689
only in bm-005 0   only in bm-009 0
changed 1   editor\entities\…\v0300_…_civilian_01.epe
directory listing: no *.ee, no *.toc — only the .epe, .fmod_guids, .stringlookup, health .vmodc
```

**Verdict: HOLDS as a declaration.** The paragraph is accurate: there is nothing but the loose
`.epe`, one file differs, and the question is genuinely offline-unanswerable. It is correctly
carried as a limit rather than presented as a result.

---

## What survives, and what a reviewer should do next

**Survives cleanly:** hash resolution (A7), the module-name proof (A12), round trip and determinism
(A14), the `main_weapon` hash decode (A6), the no-behaviour prop census (A2), and the honest
declaration of the loose-`.epe` install (A17). The engineer's mechanical discipline — bytes derived,
tamper tests that fail, counts not typed — is real.

**The two failures that change the deliverable:**
1. **A1** — the base is missing 34 `CPartProp` the shipped graph carries; the card's step-1
   "narrowing" cites the damaged graph as the pattern, and the project's own earlier section says
   step 1 is a repair and proposes `CPartProp count == part count` as a gate. Neither the gate nor
   the repair was run, and the resulting car is 467 objects instead of 501.
2. **A3** — the missile rows are bullet-weapon objects; the correct donor (`CMissileWeaponBase`,
   same vehicle, four points) was already decoded in the project tree.

**The four claims to correct in the §12 row:** "no root slot is free" (A4), "T-WP4 written" (A5),
"60 entries keep donor placement" (A8/A9), "all six custom lights sit at that lamp" (A11); and the
MODLOG done section must be re-pointed at `f4abe91d…` / 124,488 B with the missing rework outcome
appended (A15).

**Not testable offline, and therefore still open:** whether the game resolves a loose `.epe`; whether
`id:00568A74`'s role is the Vulcan slot; whether the graph origin equals the assembled-body origin
(A13c); whether the unnamed light slots/orientation matter behaviourally (A11); whether any pulse
fires without a trigger (A16). Each needs phase Q/V, not another offline reading.
