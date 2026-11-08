# Review — G2-19 / T-13R: does JC3's car own the driver's pose? (SEAT)

**VERDICT: PARTLY HOLDS — the card's check passes and its transform is exact, but its central
claim is backwards.** The *clips* are character-side, as the card says. The **class token that
selects the family is a member of the vehicle** (`CInteractionGraph.modifier`), and so is the
idle state name (`set.node.npc.state = S_IDLE_DRIVER_VEHICLE`), which the card says does not
exist on the car. §5's "nothing the mod can edit on the car chooses the seated clip" is false:
one string on the graph does.

| question | card says | this review | verdict |
|---|---|---|---|
| `jc3seat.py --check` | PASS | PASS, exit 0 | HOLDS |
| what places Rico | `entry.driver` + 34 siblings | `point.driver`; `entry.driver` has no `world` | **BROKEN** (headline row) |
| the transform | -0.440, 0.340, 0.200 | identical, in 3 independent forms | HOLDS |
| T-13R built on it | yes | `bm_entity.py:205-235` maps `point.driver` only | HOLDS |
| vehicle-class field | "none … chosen by native code" | `CInteractionGraph.modifier` | **BROKEN** |
| clip families per class | 40 classes / 382 names | 40 / 383, and "36 MOD selectors" is 34 | minor |
| pose half not a vehicle member | §5 | state name + class token are both vehicle members | **BROKEN** |

---

## 1. The card's own check

```
cd E:/Modding/JustCause3/JC3-Batmobile && ( time timeout 580 python Tools/scripts/jc3seat.py --check ) 2>&1 | tail -30; echo "EXIT=${PIPESTATUS[0]}"
PASS: 34 driver points | 40 pose classes (382 clip names) | 36 MOD selectors | seat boxes 4 | candidate v0300_car_kensington_sportsmuscle (10 mm from the hip), json match True, md match True

real    0m1.262s
EXIT=0
```

So `SEAT.json` and `SEAT.md` agree with each other and with the index. The check is a
consistency check: it re-derives the card's numbers from cached outputs. It cannot tell whether
the numbers are the right ones, and two of them are not (section 5).

## 2. The interaction object and its transform, from the Serpente `.epe`

Read twice: once through the project's `.ee.xml` decode, once out of the raw cooked bytes that
`bm_rc.vfs()` pulls from the game archive. Both are the vanilla donor, untouched.

```
cd E:/Modding/JustCause3/JC3-Batmobile && timeout 200 python - <<'EOF'   # nesting-aware parse of the .ee.xml
...
EOF
parsed 62 objects from v0300_car_kensington_sportsmuscle_civilian_01.ee.xml

### 1. CInteractionGraph: the vehicle-class selector
   object 'CInteractionGraph' at depth 3
      _object_id             = 1A010368=FFFF8399
      modifier               = MOD_LOW
      name                   = graph
      world                  = 1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1
```

The driver-named objects, as the file actually stores them (element names are indexed slots;
the readable name is a `name` value):

```
 element          class                              name                          state                          world
 CInteractionGraphPointNode                   point.driver                  -                              OWN
 CInteractionGraphEntry   CInteractionGraphNodeOccupiedCondition entry.driver              S_ENTER_DRIVER_VEHICLE         -
 CInteractionGraphExit    CInteractionGraphExit                  exit.driver.default           S_EXIT_VEHICLE                 -
 CInteraction            CInteraction                           interaction.seat.driver       -                              -
 CInteractionComponentSetNode CInteractionComponentSetNode      set.node.npc                  S_IDLE_DRIVER_VEHICLE          -
```

Verbatim values of the two objects that matter:

```
### point.driver
 class=CInteractionGraphPointNode {'_object_id': '93F2612B=FFFF52D5', 'disable_event': '', 'enable_event': '', 'enabled': '1', 'name': 'point.driver', 'name_hash': '-1634751878', 'tags': '', 'world': '1,0,0,0, 0,1,0,0, 0,0,1,0, -0.44,0.34,0.2,1'}
### entry.driver
 class=CInteractionGraphNodeOccupiedCondition {'_object_id': '402CCDFD=FFFF1070', 'disable_event': '', 'enable_event': '', 'enabled': '1', 'interaction': '00000000', 'name': 'entry.driver', 'name_hash': '-1652380186', 'state': 'S_ENTER_DRIVER_VEHICLE', 'tags': '', 'check': '0', 'max': '3', 'min': '0'}
```

`point.driver` carries the world matrix: **3×3 identity, translation (-0.440, 0.340, 0.200) m**.
`entry.driver` carries **no `world` value at all** — its `interaction` reference is `00000000`.
That is exactly what the card's own JSON records (`entry.driver … world_source = inherited`,
`point.driver … world_source = own`), so `SEAT.md`'s headline table row contradicts its own
JSON and its own §1 table (which lists `point.driver` with a transform and the verdict
"inside").

The same numbers in the game's bytes, independent of the XML converter:

```
cd E:/Modding/JustCause3/JC3-Batmobile && timeout 200 python - <<'EOF'   # bm_rc.vfs() on the cooked archive path
...
EOF
raw cooked .epe from the archive: 109766 bytes
  float32 (-0.44, 0.34, 0.20) occurrences: 1 at [71264]
    bytes 71264..71276: 0000803f00000000ae47e1be7b14ae3ecdcc4c3e0000803f000000002b61f293
  MOD_LOW                at byte 61924, context b'\x80?\x00\x00\x00\x00MOD_LOW\x00h\x03\x01\x1a\x99\x83\xff\xffgraph\x00PP...'
  point.driver           at byte 71292, context b'\xf2\x93\xd5R\xff\xffpoint.driver\x00PPP...'
  entry.driver           at byte 65676, context b'\x19\x8d\xf6\x1f\xff\xffentry.driver.pull.out.onground.no.door\x00P...'
  S_IDLE_DRIVER_VEHICLE  at byte 60041, context b'tNode\x00S_IDLE_DRIVER_VEHICLE\x00P\x00\x00\x00\x00+a\xf2\x93\xd5R\xff\xffR\xee\xf9)\xb6\xf1\xff\xffset.node.npc\x00PPP...'
```

Three things fall out of those bytes:

1. `(-0.44, 0.34, 0.20)` as `float32` occurs **once in 109,766 bytes**, 28 bytes before the
   `point.driver` name — the transform is that object's, not a coincidental triple.
2. `MOD_LOW` sits next to the graph's object id `1A010368=FFFF8399` and the name `graph`: the
   class token is in the cooked file, not only in the conversion.
3. `S_IDLE_DRIVER_VEHICLE` is followed by the id `93F2612B=FFFF52D5`, which is `point.driver`'s
   id, then `set.node.npc` — the car names the idle state *and* which node it applies to.

### Who references that node

```
 set.node.npc            .node         -> 93F2612B=FFFF52D5  'point.driver' [CInteractionGraphPointNode]
 set.node.npc            ._object_id   -> 29F9EE52=FFFFF1B6  'set.node.npc' [CInteractionComponentSetNode]
```

A `CInteractionComponentSetNode` inside the vehicle's own graph sets the character component of
`point.driver` to `S_IDLE_DRIVER_VEHICLE`. There are two more set nodes in the file, on the
`CInteraction` (`S_IDLE`) and `CInteractionTrigger` (`S_IDLE_PASSENGER_VEHICLE`) — the same
pattern for every rideable slot.

### T-13R used the right object

`Tools/scripts/bm_entity.py:205-235` (`interaction_transforms`) reads
`mapped["point.driver"]["serpente"]` and builds the seat as *BmAK `Driver` socket + (donor
`point.driver` − donor seat-part centroid)*; every other driver-named object is explicitly
skipped as "no named `world` member: inherits its graph node's transform (T-13R)"
(`bm_entity.py:495-499`). `SEAT.md`'s §5 statement "`entry.driver` is a transform plus a state
string, so the Batmobile's `Driver` socket can carry it" mixes the two objects: it is
`point.driver` that carries the transform, `entry.driver` that carries the state string.

## 3. The vehicle-class field: `CInteractionGraph.modifier`

| vehicle | `graph.modifier` | clip family the `.asb` pairs with that token | clips in that folder |
|---|---|---|---|
| `v0300_car_kensington_sportsmuscle_civilian_01` (the Batmobile's donor) | `MOD_LOW` | `…/rico/vehicle/car/low/` | 23 |
| `v0405_car_mugello_moderncircuitracer_civilian_01` | `MOD_CIRCUIT` | `…/rico/vehicle/car/circuit/` | 9 |
| `v0001_car_autostraad_armoredtruck_commercial_01` | `MOD_HIGH` | `…/rico/vehicle/car/high/` | 4 |

All three read straight out of their vanilla `.ee.xml`:

```
v0300_car_kensington_sportsmuscle_civilian_01        modifier=['MOD_LOW']
v0405_car_mugello_moderncircuitracer_civilian_01     modifier=['MOD_CIRCUIT']
v0001_car_autostraad_armoredtruck_commercial_01      modifier=['MOD_HIGH']
```

Each of the three also names the same idle state, on its own driver node id — the layout is
identical, only the token differs:

```
v0300_car_kensington_sportsmuscle_civilian_01      modifier=MOD_LOW        set-nodes=[('93F2612B=FFFF52D5', 'S_IDLE_DRIVER_VEHICLE')]
v0405_car_mugello_moderncircuitracer_civilian_01   modifier=MOD_CIRCUIT    set-nodes=[('F3C9A386=FFFF8B38', 'S_IDLE_DRIVER_VEHICLE')]
v0001_car_autostraad_armoredtruck_commercial_01    modifier=MOD_HIGH       set-nodes=[('E838808C=FFFFD19D', 'S_IDLE_DRIVER_VEHICLE')]
```

**Why `modifier` is the selector, and not just a name.** In `rico_base.asb` every
`ANIM_…_VEHICLE_MOD_<X>` string is immediately followed by a `PPP`+clip-path string, and the
folder in that path is `<x>` lowercased:

```
cd E:/Modding/JustCause3/JC3-Batmobile && timeout 300 python - <<'EOF'
...
EOF
### ANIM_*_VEHICLE_MOD_LOW in the .asb
   idx   579 'ANIM_FORWARD_TO_REVERSE_DRIVER_VEHICLE_MOD_LOW'
        +1  'PPPanimations/jc_characters/main_characters/rico/vehicle/car/low/rico_vehi_car_low_tran...'
### ANIM_*_VEHICLE_MOD_CIRCUIT in the .asb
   idx   401 'ANIM_FORWARD_TO_REVERSE_DRIVER_VEHICLE_MOD_CIRCUIT'
        +1  'PPPanimations/jc_characters/main_characters/rico/vehicle/car/circuit/rico_vehi_car_circ...'
### ANIM_*_VEHICLE_MOD_HIGH in the .asb
   idx  1225 'ANIM_DRIVER_TO_STUNT_SIDE_P2_VEHICLE_MOD_HIGH'
        +1  'PPPanimations/jc_characters/main_characters/rico/vehicle/car/high/rico_vehi_car_high_dr...'
        +3  'ANIM_IDLE_DRIVER_VEHICLE'          (no MOD_ suffix)
        +4  'PPPanimations/jc_characters/main_characters/rico/vehicle/car/med/rico_vehi_car_med_driv...'
```

The same pattern across the whole file:

```
   MOD_LOW                          -> [..., 'car/low']
   MOD_MED                          -> [..., 'car/med']
   MOD_HIGH                         -> [..., 'car/high']
   MOD_CIRCUIT                      -> [..., 'car/circuit']
   MOD_CIRCUIT_RIGHT                -> ['car/circuit']
   MOD_TANK                         -> ['tank']
   MOD_BIKE                         -> folder 'bike' (13 anim names carry MOD_BIKE)
   MOD_BOAT                         -> ['boat']
```

So the token in the graph and the token in the animation name are the same vocabulary, and the
bare `ANIM_IDLE_DRIVER_VEHICLE` (no `MOD_`) pairs with `car/med` — which is why `MOD_MED` →
`car/med` and not the reverse.

**Fleet census** (295 vehicle `.ee.xml`, modifier read inside each `CInteractionGraph` block):

```
epe xml files: 295
files with a CInteractionGraph but no modifier: 18 ['v2906_drone_blackhand_elitedrone_debug', 'v2906_drone_blackhand_elitedrone_military_01', 'v5601_train_urga_monorailcargoengine_military_01', ...]
files with no CInteractionGraph at all: 8

   MOD_RIGHT     159    MOD_LOW        63    MOD_LOW_RIGHT  44    MOD_HELI      44
   MOD_HIGH       36    MOD_TANK       20    MOD_BOAT_CABIN 20    MOD_BOAT      18
   MOD_JET        18    MOD_BACK       17    MOD_BIKE       14    MOD_MED        6
   MOD_CIRCUIT     4    ... 48 distinct values in all
  files with >1 CInteractionGraph: 1 of 295
   v4603_plane_urga_cargotransport_military_cargo_tank   2 graphs: ['MOD_CARGO', 'MOD_TANK']
```

Three consequences, each from those numbers:

* The field is **per interaction graph, not per entity** — the one file with two graphs carries
  two different tokens (`MOD_CARGO` and `MOD_TANK`), i.e. one token per seat group.
* It is **not a pure car-class enum**: `MOD_RIGHT` (159 files) and `MOD_LEFT`/`MOD_BACK` are
  seat-side tokens, and 12 of the 48 values (`MOD_MECH`, `MOD_SOAPBOX`, `MOD_DIMAH`, …) have no
  `ANIM_*_VEHICLE_MOD_*` suffix in the `.asb`. The *car* rows are the four folders, and those
  four map 1:1 as shown.
* Vehicles with no graph are drones and monorail trains — no rideable seat, which is consistent
  with the field being about a seat's animation class.

## 4. What this does to the card's thesis

`SEAT.md`, one line under the title and again in §5:

> **Answer: the car does not own the pose.** … The *pose* is the character state machine's
> vehicle state …
> **The pose half is not a vehicle member.** Nothing the mod can edit on the car chooses the
> seated clip; it follows from the character state machine plus a class the game derives.

Half right, and the wrong half is the one a mod cares about.

* **Right:** no clip data, no skeleton, no IK target lives on the vehicle. The `.ban` files are
  in `rico_base.asb`, character-side. The card's In-list check (0 files under
  `jc_statemachine/vehicles/*`, 0 `.bsk`) stands.
* **Wrong:** the *choice* is a vehicle member twice over —
  1. `graph.modifier` = `MOD_LOW` (**vehicle**), which is the token the animation names carry
     (`ANIM_…_VEHICLE_MOD_LOW`) and which selects `car/low` (23 clips);
  2. `set.node.npc.state` = `S_IDLE_DRIVER_VEHICLE` (**vehicle**), addressed to `point.driver`
     by id.
  "The game derives the class" is not needed: the class is written in the file, once per graph.
* §4's "none of the three class folders is named inside the vehicle's own modules" is literally
  true (`car/low` appears nowhere in the Serpente `.ee.xml` — measured: `'car/low' anywhere in
  the serpente .ee.xml: False`) but misleading: the *token* is named, and the token is what the
  animation name concatenates.

**For the Batmobile.** `bm_entity.py:79` sets `ENT` to `…/v0300_car_kensington_sportsmuscle`,
i.e. the mod's entity *is* the Serpente's file, and nothing in `Tools/scripts` writes
`modifier` (no hit for `modifier` in `bm_entity.py` or `bm_rc.py`). The Batmobile therefore
inherits `MOD_LOW` and should play the `car/low` family — consistent with T-13R's use of the
door-left entry. If the cockpit ever needs a different family, the lever is that one string
(`MOD_LOW` → `MOD_MED` …) in the graph, not a new animation. Whether the game honours it is
**UNKNOWN** (section 6).

## 5. Two counts in the card that do not reproduce

```
unique rico/vehicle clip paths in the .asb: 383
  ones the card's clip_families() drops (no subfolder): ['animations/jc_characters/main_characters/rico/vehicle/rico_vehi_crawl_out.ban']
VEHICLE_MOD_ suffixes: 34 ; clip_families() keys: 40 ; selectors['mods']: 36
extra keys in the card's mods set: ['BACK', 'CAR_MOUNTED_WEAPON_PARA']
```

* **"382 clip names" is 383.** The card's `clip_families()` requires a class subfolder and
  drops `rico_vehi_crawl_out.ban`, which sits directly in `…/rico/vehicle/`.
* **"36 `MOD_*` class selectors … straight out of its [`.afsmb`'s] string table"** — the
  `.afsmb` contains **no** `MOD_*` tokens at all:
  ```
  ### MOD_ tokens in rico_base.afsmb (the state machine)
     strings carrying MOD_: 3 ; distinct tokens: 3
        MOD_SAMPLER_3
        MOD_SAMPLER_2
        MOD_SAMPLER_1
     any 'S_...MOD_...': []
  ```
  The 36 come from the `.asb`'s folder names, and include two that are not modifiers (`BACK`,
  `CAR_MOUNTED_WEAPON_PARA`); the real `ANIM_*_VEHICLE_MOD_*` suffix set is **34**. The
  table's *content* is sound, its source label and its count are not.

## 6. What stays UNKNOWN

* **Whether the engine reads `CInteractionGraph.modifier`.** No native code, no schema, no
  doc in this repo ties that member to the `.asb` lookup. The case here is the value
  vocabulary (identical `MOD_*` tokens on both sides) plus one token per seat group in the one
  two-seat file. A 5-minute experiment: change the Serpente's `MOD_LOW` to `MOD_MED` in an
  installed build and watch whether the idle seated pose changes from `car/low` to `car/med`
  (the `med` set is 35 clips with visibly different arms). That is a phase-Q look, not a file
  read.
* **Which family the Batmobile actually plays in game.** Unchanged from the card: needs the
  same look. The card's "watch whether the hands land on the yoke" probe is still the right
  one, and now it has a predicted answer (`car/low`).
* **The seat height rows** (§3 of the card) were not re-measured here; this review covers the
  interaction object, the transform and the class field only.

## 7. Files and commands

Probe scripts (scratch, not part of the tool chain):

```
tmp/freebuff/scratch/seat_review_probe.py      # nesting-aware .ee.xml parse; class + transform
tmp/freebuff/scratch/seat_review_evidence.txt  # its output
tmp/freebuff/scratch/seat_node_evidence.txt    # set-node + id resolution
tmp/freebuff/scratch/seat_class_evidence.txt   # MOD_<X> -> clip folder adjacency
tmp/freebuff/scratch/seat_mod_map.txt          # every MOD_<X> and the path that follows
tmp/freebuff/scratch/seat_census.txt           # 295-file modifier census
tmp/freebuff/scratch/seat_afsmb.txt            # .afsmb MOD_ token count, graphs per file
tmp/freebuff/scratch/seat_rawbytes.txt         # float32 / string offsets in the cooked .epe
```

Commands, all run from `E:/Modding/JustCause3/JC3-Batmobile` (full output quoted in the sections above):

```
python Tools/scripts/jc3seat.py --check                     -> PASS, exit 0
python tmp/freebuff/scratch/seat_review_probe.py            -> 62 objects, graph modifier MOD_LOW
python - <<EOF (id resolution) EOF                           -> point.driver OWN, entry.driver inherited
python - <<EOF (three cars' modifier) EOF                    -> MOD_LOW / MOD_CIRCUIT / MOD_HIGH
python - <<EOF (asb adjacency) EOF                           -> LOW->car/low, CIRCUIT->car/circuit, HIGH->car/high
python - <<EOF (three cars, nesting-aware) EOF              -> each: modifier + set-node S_IDLE_DRIVER_VEHICLE
python - <<EOF (mod map + folder counts) EOF                 -> car 2, car/circuit 9, car/high 4, car/low 23, car/med 35
python - <<EOF (295-file census) EOF                         -> 48 distinct values, 1 file with 2 graphs
python - <<EOF (afsmb MOD_ tokens) EOF                       -> 3, all MOD_SAMPLER_n
python - <<EOF (bm_rc.vfs raw bytes) EOF                     -> (-0.44,0.34,0.2) once at 71264
```
