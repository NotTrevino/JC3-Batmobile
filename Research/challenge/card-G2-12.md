# Assumption challenge — backlog card G2-12 (the armed Serpente: civilian → signature_preorder)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-12 card (§6, line 612),
its §12 row (line 1295), the MODLOG `G2-12 · … — intended change` and `G2-12 · … — done` sections,
the artifacts `Research/JC3Grab/SIGNATURE_DIFF.md` + `SIGNATURE_DIFF.json`, the generator
`Tools/scripts/jc3sigdiff.py`, and the data it reads (`INDEX.json`, `WEAPONS.jsonl` /
`WEAPON_WIRING.jsonl` for cross-checks, `PARTS_TABLE.jsonl`, the two `.ee` containers in
`D:/Games/Just Cause 3` through `jc3index`).

Constraints honoured: no game launched, nothing written into `D:/Games`, no capture copied, nothing
committed, no `--write`. The one command that writes anything is the card's own `--check`, which
re-converts the two inner `.epe`s into its scratch cache `E:/Modding/_JC3grab/sigdiff/`. That cache
was hashed before and after and is **byte-identical** (only mtimes move):

```
$ sha1sum /e/Modding/_JC3grab/sigdiff/*   (before)  … (after)   → diff: no differences
CACHE BYTES UNCHANGED
$ python Tools/scripts/jc3sigdiff.py --check
PASS: 566 -> 601 members, graph 450 -> 464 objects, 4 added / 1 removed, 19 part rows changed,
84 mesh pairs, 2 graph objects changed                                            EXIT=0
```

Method: the card's own gate first; then each claim attacked with the data on disk — the JSON
artifact, the archive index, in-memory parses of the two converted graphs (`jc3wiring.parse_epe`,
no file written), in-memory reads of paired `.rbm` meshes out of the containers, and Jenkins-hash
experiments for the hashed names. Where a claim needs a build/launch to settle, that is stated as a
limit rather than guessed.

## VERDICT

**One BROKEN, four WEAK, eleven HOLDS.** The diff itself is reproducible and unusually well built: every
number in the §12 row re-derives from `SIGNATURE_DIFF.json`, the parts comparison is field-by-field
over the whole decoded part record (not just the model strings), the weapon's slot names are genuine
Jenkins preimages (`main_weapon` → `851CAABE`, `mounted_weapon_2` → `AC0BC788`), and the "on the hood"
placement — which the doc asserts on the strength of a part name — turns out to be measurable to
6 cm against the entity's own `point.stunt.hood` matrix. The literal diff is sound.

What does not hold is one stated *limit*, and it is wrong in the doc's favour: `CMaterialEffectTable`
is not "a 30-byte hash blob whose contents are not decoded". It is a 640-byte table, and all seven
`tank_explosive_*.effc` paths it names resolve by Jenkins hash at fixed strides. The record claims
less than it knows. The two soft spots that matter for B-05 are softer than the tables: the "VFS tune
is authoritative" precedence rule is asserted, not tested — the gate only checks that some path
ending `.wtunec` exists — and the §2/§7 counts that a reader would naturally pair up (167 vs 162
added members) are two different populations, with five members in the container and in neither
toc. Everything else survived attack, several claims on evidence stronger than the card's own.

| # | assumption | verdict |
|---|---|---|
| A1 | `signature_preorder` is the armed Serpente, so this diff is complete for the chassis | **HOLDS** — 3 builds exist; only `signature_preorder` carries a weapon class |
| A2 | the container's inner `.epe` is what the game builds; the standalone `.epe` is a different build | **WEAK** — the exclusion is right on bytes, but the authority claim is untested; both copies agree on every content marker |
| A3 | container arithmetic 566→601, +167/−132, 108 "same-role" replacements, 0 changed by name | **HOLDS** — recomputed; "same-role" is a file-naming rule and is disclosed as one |
| A4 | the 603 discarded `vec_events` are identity churn, not different event targets | **HOLDS** — a consistent 13→13 bijection over 38 changed slots; the record's "resolved" wording is still wrong |
| A5 | "2 changed graph objects", and the two unnamed root scalars really have no recoverable name | **HOLDS** — a 21,447-token vocabulary still gives no preimage; the hash convention is proven |
| A6 | the parts modules are the same 42 parts; only `model`/`model_swap` differ; no hinge/door/entry added | **HOLDS** — field-by-field over the whole decoded part record, flags and offsets included |
| A7 | "the same shell recompiled against the signature textures, not new geometry", from block count + AABB | **HOLDS** — but not for the reason given: block-level bytes prove it (body: 6 of 9 blocks byte-identical) |
| A8 | the 84 mesh "pairs" are real pairs (base stem ↔ `signature_` stem) | **HOLDS** for the ones probed; the pairing rule is a name convention |
| A9 | the weapon wiring: 4 type-2 points, one muzzle per point by position, one effect, one slot | **HOLDS** — root-space positions, distinct x, hash-verified effect path, other slots null |
| A10 | the pod sits "on the hood" | **HOLDS** — 6 cm from the entity's own hood point; the doc never cites it |
| A11 | the tune numbers, and "the VFS copy is authoritative" | **WEAK** — values reproduce; precedence untested and the gate's check is loose; units and the blast radius semantics are inferred |
| A12 | `CMaterialEffectTable` is a 30-byte hash blob, contents not decoded | **BROKEN** — 640 bytes, 7/7 `tank_explosive_*` hashes decode in it |
| A13 | `.ee.toc` is the load list and its counts explain the container counts | **WEAK** — counts reproduce, but 5 added members are in no toc and the 167 vs 162 gap is unremarked |
| A14 | the civilian has 0 weapon slots and no weapon | **HOLDS** — null slot + no weapon class in its decoded graph |
| A15 | positions are metres in root space (never stated) | **WEAK** — unstated; every value is consistent with metres |
| A16 | "the interaction graph changes one string only; no seat/entry/exit/trigger added" | **HOLDS** — no interaction class added or removed; one area string changed |

Counts: 11 HOLDS, 4 WEAK, 1 BROKEN.

---

## A1 — `signature_preorder` is the armed Serpente, so this is the complete diff. **HOLDS**

The card promises "a complete list of what JC3 changes to arm this **exact chassis**". That is only
complete if the chassis has one armed build. The index holds 54 files under
`…/v0300_car_kensington_sportsmuscle/`, and exactly three `.ee` builds:

```
entity (.ee) builds: 3
    v0300_car_kensington_sportsmuscle_civilian_01.ee
    v0300_car_kensington_sportsmuscle_debug.ee
    v0300_car_kensington_sportsmuscle_signature_preorder.ee
```

Third build probed in memory (`read_entity`, then the inner `.epe` decoded by the same graph reader):

```
civilian  container  5539952 8e8ac6fd9ecd  inner  109526 d4570984eb60  members 566
debug     container  5539360 374c938a5243  inner  109510 4625cd69128e  members 565
variant   container  5802496 985e8479eef2  inner  114962 cbafe09ef30f  members 601

debug.ee decoded graph: 450 objects
  CPartProp 40, CForcePulse 1, SEffects 1, SAttachedEffect 27, … SWeaponPoint 0,
  CMissileWeaponBase 0, CAimPOIWeaponComponent 0, CMaterialEffectTable 0
  w618 members: []
```

So there are three *distinct* builds (three different inner sha1s), and exactly one is armed. `debug`
mirrors the civilian at graph level — 450 objects, no weapon class, no `w618` member — which makes the
comparison the complete one for this chassis, not a sample. The doc's limits section already says no
other v0300 variant is compared; that is now a closed question.

One methodological note this probe produced: a raw string search of `debug.ee` shows
`CMissileWeaponBase 0` but `front_signature_area` **7** — the string table contains names that build
nothing. Had the check been a string count instead of a decoded graph, `debug` would have looked
armed. The generator's invariant tests use the decoded graph, which is why it is not fooled.

## A2 — the container member is the graph the game builds. **WEAK**

The record excludes the "loose `.epe` next to the container" as *a different build* and treats the
container member as authoritative. Two things are true and one is not.

True: they are different serialisations. Read both out of the archives in memory:

```
== …_civilian_01.ee
  inner member: 109526 sha1 d4570984eb607013fd1ad66cfe81267f8b78ad6e
  vfs  .epe   : 109766 sha1 201426a8b6cd97e0b46412d869b265a37e891648
  length delta: 240   common prefix: 28   common suffix: 106
  inner[28:] b4000f007ca1929a54dd00…      vfs[28:] bd000f007ca1929ae4dd00…
== …_signature_preorder.ee
  inner 114962 / vfs 115378, common prefix 28, common suffix 159
```

Not true (or at least unproven): that the container member is the one the game builds. And the
"loose" file is not loose — it is an ordinary index entry in the **patch** mount:

```
index: editor/entities/jc_vehicles/01_land/v0300…/…_civilian_01.epe   109766  patch_win64/game1  patch
       editor/entities/jc_vehicles/01_land/v0300…/…_signature_preorder.epe 115378  patch_win64/game1  patch
.ee mounts: {'base': 767, 'dlc': 195, 'patch': 1}      .epe entries: 344, all mount 'patch'
epe with a matching .ee: 344   epe without .ee: 0   ee without a standalone .epe: 619
```

A patch-mount copy is at least as likely to be the newer build as the base-game container, and the
record tests nothing about load order. What saves the conclusion is that both copies agree on every
semantic marker (string-table probe of all four blobs):

```
string                             civ inner   civ vfs   sig inner   sig vfs
CMissileWeaponBase                 -           -         yes         yes
sportsmuscle_missile_base_signature-           -         yes         yes
w618_sportsmuscle_missile          -           -         yes         yes
internal.fire_point.0              -           -         yes         yes
tank_explosion_effect_table        -           -         yes         yes
front_area                         yes         yes       -           -
front_signature_area               -           -         yes         yes
```

So the *diff* is robust to the choice even though the choice is unproven. Verdict **WEAK**: an
exclusion justified by size/sha1 (fair) plus an authority claim with no evidence (mine to flag). It
would cost one line to say "both copies carry the same change; the container member is used because
every other G2 card does, not because a test shows the game prefers it".

Note this is a project-wide convention, not a G2-12 defect: `jc3wiring.decode_epe` does the same for
all 53 entities G2-11 decoded.

## A3 — the container arithmetic. **HOLDS**

```
members counts: [566, 601] added 167 removed 132 changed 0 replaced 108
unpaired added 59 unpaired removed 24
added_by_kind {'effect': 11, 'graph': 1, 'lod': 24, 'mesh': 89, 'meta': 2, 'module': 2,
               'other': 6, 'physics': 1, 'texture': 27, 'tune': 4}
replaced_by_kind {'rbm': 84, 'lod': 23, 'vmodc': 1}
```

566 + 167 − 132 = 601; 167 − 108 = 59 unpaired; 132 − 108 = 24 unpaired; 84 + 23 + 1 = 108. Every
figure in the §12 row reproduces. One honest caveat that the doc itself states: "same-role
replacement" is `pair_stem()` — strip a leading `signature_`, pair by stem + extension. It is a
**naming rule**, not a content match, and the doc's own sentence ("a `signature/` path for the base
path") discloses that. A7 below supplies the content corroboration the label does not.

## A4 — the 603 discarded `vec_events` are identity churn. **HOLDS** (wording is wrong)

`graph_diff` drops every `vec_events` property before comparing, and reports the count:

```
skipped: {'refs': 51, 'vec_events': 603, 'volatile': 1245}
```

The record's wording is "resolving references by semantic path and **discarding** `vec_events`", i.e.
the resolution applies to object references and the events are dropped. What are they? Mostly empty
event slots on many objects. Re-running the comparison myself, resolving ids through each graph's own
oid map:

```
common paths with vec_events: 96
identical values: 565
differ, both non-empty: 38 | of which same first half: 0 same serial half: 0
differ, one side empty: 0
live event ids: 38 on the civilian side, 38 on the variant side, 0 resolvable as graph oids
```

The live ids are **not object references at all**: none of them is an oid in its own file, so
"resolving … by semantic path" cannot have applied to them; they are event ids in a separate space.
That is a wording defect in the record, not a wrong conclusion. The conclusion is testable another
way, and it passes: collect the before→after mapping of every non-empty changed slot and ask whether
it is consistent.

```
changed slots: 38   distinct old event ids: 13   distinct new ids: 13
old ids mapping to >1 new id: 0
  04EC893A=FFFFF1E8 -> 597A1AFA=FFFF6DEF      4C13612F=FFFF9068 -> 15EC3812=FFFF8DA5
  4B37C0C5=FFFFB727 -> 14AA4863=FFFFBAC7      4CFD3D1B=FFFFE291 -> 324A5A66=FFFF9F3A
  4B961AE0=FFFFE587 -> 00908A1D=FFFF27B6      597B6EAC=FFFFAD38 -> 1AC2DE00=FFFF31A6
  … all 13 shown above; 13 → 13, injective
```

Thirteen event ids, each mapping to exactly one new id, reappearing across 38 slots — that is a
consistent renumbering of the same wiring, which is what the record asserts. A genuine re-target would
have to produce the same bijection by accident. Verdict **HOLDS**, and the record should replace
"resolving references by semantic path and discarding `vec_events`" with "`vec_events` are excluded
from the diff; 13 event ids are renumbered consistently across 38 slots".

## A5 — "2 changed objects", and the two unnamed scalars are unnamed. **HOLDS**

```
changed: root/CCar
  decals 1732285335 -> -211122583
  id:851CAABE 00000000 -> ->root/CMissileWeaponBase:w618_sportsmuscle_missile
  id:EA011E72 0.3 -> 1
  id:FFE31EE1 1 -> 0
  name …civilian_01 -> …signature_preorder
  palette -1071400364 -> None
  vehicle_parts 1526043305 -> 402479768
changed: root/CInteractionContext:context/CInteractionGraph:graph/
         CInteractionGraphPointNode:point.stunt.hood
  id:ED4F648C front_area -> front_signature_area
```

The record says two root scalars "have no Jenkins name" and no candidate in the shipped vocabulary
matched. Tested independently: the id form is `Jenkins(name)` (proven on known names), and the
vocabulary below — 21,447 tokens harvested from both containers' own string tables and graph blobs,
plus 1,322 names from 300 converted `.epe`/XML files under `E:/Modding/_JC3grab` — gives no preimage
for either id:

```
vocabulary (containers): 21447      vocabulary (converted XML): 1322
EA011E72 -> None        FFE31EE1 -> None
main_weapon      851CAABE   <- the root's slot key, so the method works on a known name
tuning_file      AA7096C9   <- the weapon's own tune-path property
mounted_weapon_2 AC0BC788   <- the root's second slot
vehicle_parts    860EAC9B   palette 6187A56B
```

So both scalars stay unnamed, and the doc's "recorded, not guessed" is correct. The judgement that
"neither is a weapon slot" is backed by the slot list itself (A9): all four named slots are accounted
for, so an unnamed float/int cannot be one.

Residual, stated so nobody forgets it: `0.3 → 1` and `1 → 0` are *behaviour-bearing* numbers on the
vehicle root (a factor and a flag), and a B-05 port must either copy the variant's values blindly or
find out what they do. The doc records them; it does not resolve them. That is the right call, but
"neither is a weapon slot" is weaker than "copy them as-is and retest".

## A6 — the parts modules are the same part set. **HOLDS**

```
parts only_civilian [] only_variant []
changed rows 19 changed_fields ['model', 'model_swap']
changed-field combos: {('model',): 15, ('model', 'model_swap'): 4}
civilian module 29886 B 23f0bcc8… 42 parts
variant  module 30382 B 627fd438… 42 parts
epe instantiated: 40 (civilian, missing [25,41]) / 41 (variant, missing [24])
table_mismatches: matches True, mismatches []
```

The comparison in `parts_diff` iterates **every key the decoder produces** — name, damage_type,
behaviour, model, model_swap, part_index, parent, `parent_space_offset[16]`, `centroid[4]`,
`deformation_centroid_offset[4]`, seventeen flags and seven instance ids (`jc3adf.parts`, lines
253-295) — and only `model`/`model_swap` differ. So "same behaviours, damage types, parents and flags"
is a decoded statement, not a name comparison. `PARTS_TABLE.jsonl` cross-checks both rows (42/42,
names and models).

One scope note the doc does not spell out: a field the ADF walker does not decode would be invisible
to this comparison. The two modules *do* differ in sha1 and by 496 bytes, which the 23 changed paths
explain, but "identical except for 23 path strings" is a claim about the decoded schema, not about
every byte of the `.vmodc`.

## A7 — "the same shell recompiled against the signature textures, not new geometry". **HOLDS, but not for the stated reason**

The doc's evidence is "same block counts and the same AABBs, i.e. the kit is the same shell…". That
is a non-sequitur by itself, and the doc's own Limits paragraph admits it ("aabb_equal means the same
bounds, not the same vertices"). A byte-level test settles it, and it is the test the card should
carry. Block-level first, splitting each `.rbm` on the block footer `0x89ABCDEF` (the body file
yields exactly one footer per block the header declares):

```
== sportsmuscle_body_lod1.rbm  blocks 9/9  size 403514 -> 403373 (delta -141)
   identical blocks: 6   differing: [-47, -47, -47]        <- 3 x -47 = -141, the whole delta
```

Then the string sets of each pair, which is where the -47s come from:

```
== sportsmuscle_body_lod1.rbm  403514 -> 403373
   only in signature (3):  …/textures/signature/v0300…_body_signature_dif.ddsc
                           …/v0300…_body_mpm.ddsc
                           textures/00_general/dummy/a00_dummy_black_mpm.ddsc
   only in base (3):       …/v0300…_body_dif.ddsc
                           …/v0300…_body_mpm.ddsc
                           …/v0300…_body_msk.ddsc
== sportsmuscle_wheel_f_l_lod1.rbm  43886 -> 43930
   only in signature (2):  …/textures/signature/car_tire_sport02_signature_dif.ddsc , "333?fff?"
   only in base (1):       models/jc_vehicles/00_shared/car_tire/texture/car_tire_sport02_dif.ddsc
== sportsmuscle_door_f_l_lod1.rbm  65526 -> 65479
   only in signature (3):  …/textures/signature/v0300…_body_signature_dif.ddsc,
                           …/v0300…_body_mpm.ddsc, dummy/a00_dummy_black_mpm.ddsc
   only in base (3):       …/v0300…_body_dif.ddsc, …_body_mpm.ddsc, …_body_msk.ddsc
```

So the claim is true: the vertex blocks are untouched and the new strings are exactly the signature
texture paths (whose `.ddsc` files are in the added-members list). **HOLDS** — and note the doc
*understates* what is provable here; a 20-line block/string diff belongs in the generator, and it
would make "not new geometry" a measurement instead of an inference from bounds.

## A8 — the 84 "pairs" are real pairs. **HOLDS (sample)**

The pairing is `pair_stem()` (strip `signature_`), so a mis-paired file would silently compare two
unrelated meshes and the invariant "same block count and AABB" would fail. I probed three pairs at
byte level (A7): in the body (9 blocks) six blocks are byte-identical and the three that differ do so
only by their texture-name table; in the wheel and door the string-set diff is exactly the base
texture names replaced by `signature/...` ones. No pair compared geometry that was not the same part.

```
pairs: 84   standalone_added: 5 (w143_rpg_fire_leach_projectile_body_lod1…5, 8 blocks each)
pairs with aabb_equal False: []   pairs with different block counts: []
```

The five unpaired meshes are the RPG projectile LODs, as the doc says. Verdict HOLDS on a 3-of-84
sample; the rule is a name convention and the doc labels it as one.

## A9 — the weapon wiring. **HOLDS**

Read from the graph and re-verified:

```
slots: {'id:851CAABE': 'A7E417D5=FFFF20AF', 'id:00568A74': None, 'id:AC0BC788': None,
        'mounted_weapon': None}
weapon_id 618  weapon_type 2  class CMissileWeaponBase
  point internal.fire_point.0 type 2 [0.182, 1.085, -1.566]  muzzle fire
  point internal.fire_point.1 type 2 [0.058, 1.085, -1.566]  muzzle fire2
  point internal.fire_point.2 type 2 [-0.063, 1.085, -1.566] muzzle fire3
  point internal.fire_point.3 type 2 [-0.19, 1.085, -1.566]  muzzle fire4
  all four muzzles: effect 667364510 -> effects/jc_weapons/muzzle_flash/
                    sportsmuscle_missile_muzzleflash.effc  (source: container)
  aim: CAimPOIWeaponComponent aim.poi  id:2D0B3C09 = 50
```

Two checks that matter for the "member read by its name" rule:

* the effect hash is a genuine preimage, not a guess: `hash_jenkins("effects/jc_weapons/muzzle_flash/
  sportsmuscle_missile_muzzleflash.effc") = 667364510`, and that path is **not** in the index — so
  "a member of this `.ee`, no VFS entry" is true, and the resolution preferred the container.
* the slot names are preimages too (`main_weapon` → `851CAABE`, `mounted_weapon_2` → `AC0BC788`), so
  "`main_weapon`" is decoded, not a vocabulary guess. `id:00568A74` stays unnamed, which matches
  G2-11's row.

The point↔muzzle pairing compares `world` translations, and that is legitimate here because every
container of those transforms is identity:

```
CCar 1,0,0,0,…   CMissileWeaponBase 1,0,0,0,…   CAimPOIWeaponComponent 1,0,0,0,…
SEffects (empty)  SWeaponPoint .0 1,0,0,0, 0,1,0,0, 0,0,1,0, 0.182,1.085,-1.566,1
```

Four distinct x values, four muzzles at those same x — the pairing can only match 1:1. Verdict
**HOLDS**.

## A10 — "a four-tube missile pod on the hood". **HOLDS (better evidence than the card uses)**

The doc says "on the hood" on the strength of part names (`sportsmuscle_hood_signature` →
`sportsmuscle_missile_base_signature`). The entity already contains the measurement: its own
stunt-area point for the hood versus the fire points:

```
point.stunt.hood    world = 1,0,0,0, 0,1,0,0, 0,0,1,0, 0,1.050659,-1.504883,1
point.stunt         world = 1,0,0,0, 0,1,0,0, 0,0,1,0, 0,1.487549,0.421875,1     (the roof)
SWeaponPoint.0      world = … 0.182,1.085,-1.566,1
```

The pod's muzzles are **6 cm in z (1.566 − 1.505) and 3 cm in y (1.085 − 1.051)** from the entity's
own hood point, and 1.77 m ahead of / 0.75 m above the driver seat (`point.driver` at −0.44, 0.34,
0.2). The part tree corroborates it
structurally (41 is a child of 25). Both the geometry and the hierarchy agree, and the doc cites
neither. Verdict **HOLDS** — this is the strongest part of the card, and it is the one claim it
asserts most casually.

## A11 — the tune values, and "the VFS copy is authoritative". **WEAK**

Values reproduce exactly from the decoded tunes:

```
tuning.base_tuning.damage 1500   impulse 350   vehicle_damage_factor 1
tuning.missile_base_tuning.missile_turning_speed 0   missile_loose_lock_distance 0   gravity -9.82
ai_tuning.base_tuning.damage 30  ai_base_tuning.range [10, 100]
magazine_size -1   max_range 300   fire_rate 0.5   burst_count 1   unlimited_ammo 1
embedded wtunec 12773 B / 148 rows; VFS copy 14244 B / 155 rows, mount 'patch', 1 index entry at
  that path
the 7-row diff is entirely "absent in the embedded copy", e.g. fire_rate_level_2 0.11999999731779099
ftunec 8 rows, all damage: PlayerDamage 1100, PlayerDamageRadius 8, PlayerDamageRadiusMin 0.1,
  PlayerDamageRadiusPercentageMax 0.15, AIDamage 500, AIDamageRadius 8, AIDamageRadiusMin 0.1,
  AIDamageRadiusPercentageMax 0.15
```

Three soft spots:

1. **"The VFS copy is authoritative" is a precedence rule with no test.** The mount field says
   `patch`, and patch-over-base is the natural reading, but nothing in the card demonstrates that
   the game reads the `.wtunec` at that path rather than the graph's embedded copy. The gate's check
   is looser than the claim: `if not d["tunes"].get("vfs_wtunec")` is filled by an `endswith(
   "w618_sportsmuscle_missile.wtunec")` search over the whole index, so a stray copy in any
   directory would satisfy "the tune path in the graph exists as a VFS entry". It happens to be the
   same directory here, so the sentence is true in fact.
2. **Units are inferred.** `fire_rate 0.5` is written "0.5 s" and `max_range 300` "300 m". Both are
   conventional and consistent with the rest of the project, but neither is labelled as derived.
3. **The blast is described more confidently than the fields support.** "1100 player damage in 8 m"
   reads the two fields by name; next to them sits `PlayerDamageRadiusPercentageMax` 0.15 and
   `PlayerDamageRadiusMin` 0.1, which is what a radius-falloff pair looks like (full damage inside
   ~15 % of the radius). Whether 1100 lands at 8 m, at 1.2 m, or is a maximum with falloff is
   **UNKNOWN** from the names alone — the doc's phrasing implies the first.

Same class of claim as §8's "unguided": `missile_turning_speed 0` plus an autoaim tune *named*
`autoaim_vehicle_no_lockon_missile` is strong, but the name is the evidence, and the doc says so
("as the name and the 0 turn rate say") — that is R5-compliant disclosure, which is why this is
WEAK and not BROKEN.

## A12 — `CMaterialEffectTable` is a 30-byte blob, contents not decoded. **BROKEN**

The §9 Limits paragraph and the MODLOG "Limits" say:

> `CMaterialEffectTable` is an opaque 30-byte hash blob (class `CMaterialEffectTable`); its contents
> are not decoded.

The object is:

```
class CMaterialEffectTable  oid 810E8FCE=FFFF15A3
   name        'tank_explosion_effect_table'
   name_hash   -81972670  = 0xFB1D3242 = Jenkins("tank_explosion_effect_table")
   id:D04059E6 1097221416 = 0x41664528 = Jenkins("CMaterialEffectTable")   (class id, not data)
   id:AB772F9C vec_byte 640 B = 32 × 20-byte records
```

640 bytes, not 30. And the contents resolve. Searching the blob for the Jenkins hash of each added
effect path:

```
HIT effects/jc_weapons/tank_explosive/tank_explosive_concrete.effc  0x7a87a775 little  @0
HIT effects/jc_weapons/tank_explosive/tank_explosive_default.effc   0x73e070d2 little  @180
HIT effects/jc_weapons/tank_explosive/tank_explosive_dirt.effc      0x61874058 little  @60
HIT effects/jc_weapons/tank_explosive/tank_explosive_grass.effc     0x3f0b828a little  @120
HIT effects/jc_weapons/tank_explosive/tank_explosive_metal.effc     0xe8c58fc8 little  @260
HIT effects/jc_weapons/tank_explosive/tank_explosive_sand.effc      0x37b8b6b1 little  @20
HIT effects/jc_weapons/tank_explosive/tank_explosive_snow.effc      0x378e2e9d little  @160
hits: 7
```

Seven hits, all on 20-byte boundaries (0, 20, 60, 120, 160, 180, 260 of 640 = 32 records × 20 bytes),
so the table is a material→effect list and the seven `tank_explosive_*.effc` members the card records as
"added, not proven table entries" are **proven** entries. The pulse also points at the table by
object id, which the record does not mention:

```
CForcePulse w618_sportsmuscle_missile  x=F8894393=FFFF0D20
   SettingsFile  editor/entities/jc_explosions/weapons/w618_sportsmuscle_missile.ftune
   id:D3DDD766   '810E8FCE=FFFF15A3'      <- the table's object id (civilian: '00000000')
```

(`id:D3DDD766` is null on the civilian's only `CForcePulse` and set on the variant's added one, which
is the `CForcePulse 1→2` class delta already in the tables.)

Verdict **BROKEN**: the limit is wrong on size, wrong on decodability, and it hides a small decoded
result the card could state. It is broken in the safe direction (the record claims less than it
knows), so nothing downstream is wrong — but a "limits" line that is false is still false, and the
next card will repeat it.

## A13 — `.ee.toc` is "the load list", and its counts line up with the container's. **WEAK**

```
toc counts [468, 498]  external [30, 38]  added 162  removed 132
§2 container: added 167, removed 132
```

468 + 162 − 132 = 498 ✓, and the shapes match the member diff. But the two added-sets are not the
same set, and the doc never says so:

```
added members NOT in the toc (5):
    editor/entities/jc_environments/shared/rigid_object_effect_settings_default.etunec
    effects/textures/erosion/erosion_03_smallcurve_dif.ddsc
    effects/textures/t_bullet_impact_s2_dif.ddsc
    effects/textures/t_bullet_impact_s2_dif.tga.1_1a.trim
    effects/textures/t_explosiongrid_fume_07_whitesmoke_alpha_dif.tga.8_8b.trim
```

Those five are in the variant container and in **neither** toc (checked by name against both decoded
tocs), and `toc.added − members.added = 0` — the toc's added set is a strict subset of the member
diff's. So the toc is not an exhaustive load list, or those five are reached by hash rather than by
path. §7 presents the toc as "the load list" and gives kind counts that differ from §2's by exactly
this gap (texture 25 vs 27, tune 3 vs 4, other 4 vs 6), with no sentence connecting the two sections.
Verdict **WEAK**: the numbers are right; the relationship between "the load list" and the container
is asserted, not explained.

(Also unremarked: the kind tables differ between the two sections — texture 27/19 in §2 vs 25/19 in
§7, tune 4/0 vs 3/0 — the same 5-member gap showing up again.)

## A14 — the civilian has 0 weapon slots and no weapon. **HOLDS**

```
weapon slots in the civilian: all four null; graph holds no CMissileWeaponBase/SWeaponPoint
graph class deltas: CMissileWeaponBase 0->1, SWeaponPoint 0->4, CAimPOIWeaponComponent 0->1,
                    SAttachedEffect 27->31, SEffects 1->2, CForcePulse 1->2, CMaterialEffectTable 0->1,
                    CPartProp 40->41
```

The invariant in the generator also requires `main_weapon` to go `00000000 → component`, so a civilian
that already had one would fail. Verdict **HOLDS**.

## A15 — positions are metres in root space. **WEAK (unstated)**

The doc prints `0.182, 1.085, -1.566` with no unit and no frame. Everything is consistent with
metres in the entity's root frame: driver at `0.34 m` height, roof at `1.49 m`, hood at `1.05 m`,
exhaust effects at `z 2.48 m`, and the pod at `y 1.085` — a 4.3 m sports car with a bonnet-height
pod. The `world` matrices of every parent (root, weapon, aim) are identity and `SEffects` is empty,
so the numbers are root-space by construction, not by assumption. Verdict **WEAK** only because the
record never states the convention a port needs; there is no error to fix.

## A16 — "the interaction graph changes one string only; no seat, entry, exit or trigger is added". **HOLDS**

```
class_deltas: no CInteraction*, CInteractionGraph*, CInteractionTrigger entry added or removed
graph added: 4 subtrees — CPartProp:sportsmuscle_hood_signature (2 obj), CForcePulse (1),
             CMaterialEffectTable (1), CMissileWeaponBase (11)          = 15 objects
graph removed: CPartProp:sportsmuscle_hood (1)                          -> 450 + 15 - 1 = 464 ✓
changed: CCar (7 props) + CInteractionGraphPointNode:point.stunt.hood (1 string)
```

The interactions subtree is byte-for-byte the same apart from `front_area → front_signature_area`;
`git`-style equality of the subtree follows from the diff reporting no added/removed/changed node
inside `CInteractionContext`. One wording nit worth keeping: the CCar part of the diff changes
**seven** properties including the two unnamed scalars (A5), so "the diff is one string plus a weapon"
is not what the table says; the doc's own tables are correct, its §8 sentence is a summary.

---

## What is missing that would close the gap cheaply

1. **A12 in one function** — decode the material effect table: 20-byte records, first 4 bytes the
   effect hash, resolved against the container index. It turns a false limit into a decoded table
   and lets the record say "the blast chooses one of seven added effects by surface material".
2. **A7 in the generator** — a block-level byte diff of the 84 pairs (footer-split, then compare
   blocks). That is what makes "same shell, recompiled" a measurement, and it costs a few seconds.
3. **A4 wording** — the events are not resolved by semantic path (their ids are not oids); what the
data shows is 13 event ids renumbered consistently across 38 slots. Say that instead of "discarded
as id churn", which is true but unsupported as written.
4. **A11** — test the `.wtunec` precedence (or say it is assumed) and label the units.
