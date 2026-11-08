# The u32 at +12 of the wreck AggGeom payloads is the name index of `TM`

**STATUS: done — resolved.** The word is **a name index into the package's own name table**,
and it resolves to the string **`TM`** in all four packages. So the four wreck packages'
AggGeom payloads are identical *in meaning*: they differ only because each package interns the
name `TM` at a different slot. It is not a count and not an object reference.

| package | u32 @ +12 | name table | resolves to | `names.index("TM")` | as an export index |
|---|---:|---:|---|---:|---|
| `Playable_Batmobile_SF` | 2846 | 3151 | `TM` | 2846 | `Trail_Head_UPGR.ParticleModuleRequired` |
| `Playable_BatmobileMK2_SF` | 2851 | 3156 | `TM` | 2851 | `Impact_Full_UPGR.ParticleModuleRequired` |
| `Playable_BatmobileJoker_SF` | 3120 | 3394 | `TM` | 3120 | `JokersBatmobile.RB_ConstraintInstance` |
| `Playable_BatmobileFunhouse_SF` | 2836 | 3134 | `TM` | 2836 | `Batmobile_Muzzleflash_NoTracer.ParticleModuleRequired` |

Every one of the 32 bodies in each package carries the same word (32/32 in all four), so the
difference is one per-package fact repeated 32 times, not a per-body field.

---

## 1. Where the word sits — it is not an aggregate header field

The aggregate is `[nSphere][spheres…][nBox][boxes…][nSphyl][sphyls…][nConvex][convex…]`
(G3-01b / `COLLISION_SHAPES.md` §1), and every shaped element begins with a 20-byte
StructProperty tag. The wreck bodies hold **0 spheres and 1 box**, so the box count is at +4
and box element 0 starts at **+8**:

```
payload 143 B: nSphere=0 nBox=1; element 0 tag at +8: type=10 offset=0 name_index=2846 number=0 size=64 array=0
```

Read that tag with the project's own layout (`upk_read.walk_tags`, 20-byte named-property tag):

```
+8   u16 type        = 10      (StructProperty)
+10  u16 field offset = 0
+12  i32 FName index  = 2846    <-- the differing word
+16  i32 FName number = 0
+20  i32 size         = 64      (one TM struct = 16 floats)
+24  i32 array index  = 0
+28  ... 64 bytes of TM floats, then the extents tags at 0x40/0x44/0x48
```

So **+12 is that tag's name-index field**, and it is at +12 only because these particular
bodies start their box array at +8. In a body with spheres the same tag sits deeper.

The two neighbours are a free cross-check that this is a tag and not a run of numbers: the FName
number is 0 and the struct size is **64**, which is exactly the `TM` matrix the parser then reads
as 16 floats, and the element closes on the float/bool/end tag list at 0x40/0x44/0x4C that
`COLLISION_SHAPES.md` §3 documents.

## 2. Why it is a name index and not a count or an object reference

The three readings, each tested rather than asserted:

| reading | test | result |
|---|---|---|
| **name index** | `pkg.names[word]` in each package | `TM` in all four, and the word equals `names.index("TM")` exactly |
| **count** | a count of 2846 items has to fit somewhere | payload is **143 bytes** with `nSphere=0 nBox=1`; 2846 > 143, and the field is followed by a 64-byte struct, so nothing in the aggregate can hold that many |
| **object reference** | imports / exports | out of range for imports (**649** imports in `SF` vs word 2846); in range for exports only by coincidence (5490 exports), where it names a **particle module** in three packages and an **`RB_ConstraintInstance`** in the Joker one — four *different* objects for the same-looking slot, which cannot carry a shared meaning |

The export reading is the interesting negative: the same value lands on unrelated objects in each
package, whereas the name reading lands on the same string every time. Only the name reading is
consistent with "the layouts are identical".

## 3. The field is `TM` for every shaped element in the fleet

Not just the four wrecks — the tag's name index resolves to `TM` on every sphere, box and sphyl
element in the four packages that carry `RB_BodySetup` geometry:

```
  BmGame         name_index 78655  'TM'        872 element(s)
  Orphan         name_index 19772  'TM'        242 element(s)
  Startup        name_index 62018  'TM'       2105 element(s)
  StartupPatch   name_index 47845  'TM'        236 element(s)
PASS  all shaped elements' tag name index resolves to 'TM'
      3455 elements over 4 packages; resolved names: ['TM']
```

3455 elements, four different indices, one resolved string. That is the same behaviour as the
four wreck packages, at a much larger sample: the index tracks the package's name table, the
string does not move.

## 4. What this does to the earlier findings

* `tmp/freebuff/reports/reverify-BMAK-PHYSICS.md` said the payloads "differ in exactly one u32 at
  +12". Correct, and now explained: the difference is **interned-name numbering**, so the
  collision layouts *are* identical in meaning — the old card's "byte-identical" sentence is
  false only at the byte level and harmless at the semantic level. The safer wording for any
  later card: *identical apart from the per-package FName index of `TM`*.
* The same report's narrative parenthetical "(and per body within a package)" is not supported
  by its own data or by this scan: the word is **constant across all 32 bodies** in each of the
  four packages (`u32_12_values` in its JSON was already a one-element set per package).

## 5. Commands and output

Read-only probe first, to locate the field:

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && timeout 300 python tmp/freebuff/scratch/word12_probe.py
### Playable_Batmobile_SF / Root   128-byte AggGeom payload
  first 32 bytes: 00000000010000000a0000001e0b000000000000400000000000000000000000
   +0  u32=0          u16=(0, 0)
   +4  u32=1          u16=(1, 0)
   +8  u32=10         u16=(10, 0)
   +12 u32=2846       u16=(2846, 0)
   +16 u32=0          u16=(0, 0)
   +20 u32=64         u16=(64, 0)
   +24 u32=0          u16=(0, 0)
   +28 u32=0          u16=(0, 0)

  reading the first 28 bytes as [nSphere][nBox][element tag]
   +0  nSphere  = 0
   +4  nBox     = 1
   +8  type=10 offset=0 | +12 name index=2846 number=0 size=64 array=0

  resolved as a NAME INDEX -> 'TM'  (package name table 3151 entries)
  resolved as an EXPORT index -> 'ParticleModuleRequired'
  exports: 5490, imports: 649
```

Then the tool (new, read-only, exits non-zero on any failed oracle):

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && timeout 500 python Tools/scripts/bmak_word12.py
  scanning BmGame         1081 bodies
    BmGame: 800/1081 bodies, 579 elements
  scanning Orphan          269 bodies
  scanning Startup        2099 bodies
    Startup: 400/2099 bodies, 1559 elements
    Startup: 800/2099 bodies, 1970 elements
    Startup: 1200/2099 bodies, 2338 elements
    Startup: 1600/2099 bodies, 2728 elements
    Startup: 2000/2099 bodies, 3116 elements
  scanning StartupPatch    260 bodies
### 1. the word at +12, per wreck package
  package                          word   names resolves TM index as an export index
  Playable_Batmobile_SF            2846   3151  'TM'     2846     'Trail_Head_UPGR.ParticleModuleRequired'
  Playable_BatmobileMK2_SF         2851   3156  'TM'     2851     'Impact_Full_UPGR.ParticleModuleRequired'
  Playable_BatmobileJoker_SF       3120   3394  'TM'     3120     'JokersBatmobile.RB_ConstraintInstance'
  Playable_BatmobileFunhouse_SF    2836   3134  'TM'     2836     'Batmobile_Muzzleflash_NoTracer.ParticleModuleRequired'
PASS  every wreck package's word resolves to the name 'TM'
      Playable_Batmobile_SF: 2846 -> 'TM'
      Playable_BatmobileMK2_SF: 2851 -> 'TM'
      Playable_BatmobileJoker_SF: 3120 -> 'TM'
      Playable_BatmobileFunhouse_SF: 2836 -> 'TM'
PASS  each word equals the position of 'TM' in that package's own name table
      Playable_Batmobile_SF: word 2846, names.index('TM') 2846
      Playable_BatmobileMK2_SF: word 2851, names.index('TM') 2851
      Playable_BatmobileJoker_SF: word 3120, names.index('TM') 3120
      Playable_BatmobileFunhouse_SF: word 2836, names.index('TM') 2836
PASS  the word is constant over every body inside a package
      bodies per word: Batmobile_SF=32, BatmobileMK2_SF=32, BatmobileJoker_SF=32, BatmobileFunhouse_SF=32
PASS  the word is in range as a name index in all four
      name table sizes: 3151, 3156, 3394, 3134
PASS  the word is out of range as an import index, so a package reference cannot explain it
      imports per package: 649, 649, 699, 623
PASS  read as an export index it names four different, unrelated objects
      Playable_Batmobile_SF: 2846 -> 'Trail_Head_UPGR.ParticleModuleRequired'
      Playable_BatmobileMK2_SF: 2851 -> 'Impact_Full_UPGR.ParticleModuleRequired'
      Playable_BatmobileJoker_SF: 3120 -> 'JokersBatmobile.RB_ConstraintInstance'
      Playable_BatmobileFunhouse_SF: 2836 -> 'Batmobile_Muzzleflash_NoTracer.ParticleModuleRequired'

### 2. the word cannot be a count
  payload 143 B: nSphere=0 nBox=1; element 0 tag at +8: type=10 offset=0 name_index=2846 number=0 size=64 array=0
  the word 2846 read as the tag's name index, its neighbours 0 (number) and 64 (size = the TM struct's 64 bytes) as the FName's number and the struct size
PASS  the same three fields read cleanly: number 0, size 64 = one TM struct
      number=0 size=64 (a TM is 64 bytes: 16 floats)
PASS  a count of that value cannot fit the payload
      word 2846 > payload 143 bytes

### 3. the field is 'TM' for every shaped element in the fleet
  BmGame         name_index 78655  'TM'        872 element(s)
  Orphan         name_index 19772  'TM'        242 element(s)
  Startup        name_index 62018  'TM'       2105 element(s)
  StartupPatch   name_index 47845  'TM'        236 element(s)
PASS  all shaped elements' tag name index resolves to 'TM'
      3455 elements over 4 packages; resolved names: ['TM']

### result
ALL 9 ORACLES PASS — the word at +12 is the FName index of the element tag's struct name, 'TM', which each package stores at its own index.
EXIT=0
```

Re-run the tool alone (`python Tools/scripts/bmak_word12.py --check`) for the oracle lines
without the per-element dump.

## 6. Files touched

| file | change | revert |
|---|---|---|
| `Tools/scripts/bmak_word12.py` | **new**, read-only: reads four `.upk` + four more for the fleet check, writes nothing | delete the file |
| `tmp/freebuff/scratch/word12_probe.py` | scratch probe used to locate the field | delete |
| this report | new | delete |

No existing card, script or output was edited (`grab_collision_shapes.py`, `reverify_physics.py`,
`PHYSICS.md/json`, `PHYSICS_REVERIFY.md/json`, `COLLISION_SHAPES.md/json` are untouched).

## 7. What stays open

* **Why the cooker interned `TM` at a different slot in each package** — UNKNOWN and irrelevant
  to geometry: the name tables differ in size and order per package (`3151 / 3156 / 3394 /
  3134` entries here, `78655` for the same string inside `BmGame.upk`).
* **The engine-side member name of the 20-byte tag's `name index` field** — not needed for this
  answer; the tag layout used here is the one `upk_read.walk_tags` already walks in every other
  card, and the `size=64` neighbour confirms it.
