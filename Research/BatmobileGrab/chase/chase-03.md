# Chase 03 - F-17…F-24 (`RVehicleBatmobileBase` strafe, anim node and target)

Rows: `Research/BatmobileGrab/FOOTAGE.md` §6, F-17…F-24, all eight `UNKNOWN` with reason
`VALUE-NATIVE`. Read-only chase: no existing doc, package or game file was modified; the only
writes are the two scripts under `Tools/scripts/chase/`, the extracted evidence under
`E:\Modding\_BmAKgrab\chase\`, and this file. No game was launched.

**Result: 0 of 8 found. All eight stay `UNKNOWN`, but the reason is now measured rather than
assumed**: the class has a cooked *schema* entry and **no CDO value** for any of the nine
strafe/animation properties, and the executable carries no constructor that writes the class's
members at all (checked against three members whose shipped values are known). What a build
should therefore not do is copy a number: there is none to copy.

Tools (new, in the repo):

| tool | what it does |
|---|---|
| `Tools/scripts/chase/chase_g1_values.py packages` | route 1: every `Default__*` object and every tag named by F-17…F-24 across the 20 `Playable_Batmobile*` packages (`objects.jsonl`, 20,128 objects) |
| `Tools/scripts/chase/chase_g1_values.py scan` | route 2: PE section table + a displacement-store scanner over `BatmanAK.exe` (`C7` = `mov r/m32, imm32`, `F3 0F 11` = `movss`, `mod=10` → disp32), per field offset |
| `Tools/scripts/chase/chase_g1_values.py dump <rva> <len>` | hex+ASCII of a code window with the offset stores it contains |
| `Tools/scripts/chase/chase_namescan.py` | route 1 global: one pass over all **3,266** `.upk` in `BmGame\CookedPCConsole` (11.71 GB) for the nine property names |

Evidence files: `E:\Modding\_BmAKgrab\chase\g1_chase_native.json` (every hit, with RVA and bytes),
`E:\Modding\_BmAKgrab\chase\namescan.json` (the package scan).

---

## The four findings that decide all eight rows

### 1. No cooked archetype carries any of the properties (route 1, first attempt)

```
> python Tools/scripts/chase/chase_g1_values.py packages
{"packages_scan": 20128, "default_objects": 7, "vehicle_class_defaults": [],
 "objects_carrying_a_chased_field": []}
```

20,128 exports over the 20 `Playable_Batmobile*` packages: **7** `Default__*` objects (none a
vehicle class), **0** objects whose tags name any of the eight fields. MODES.md's
"not serialised in any shipped archetype" stands, now with the CDO half measured too.

### 2. Exactly one package in the whole install names them - and it has no value for them

```
> python Tools/scripts/chase/chase_namescan.py
{"files": 3266, "bytes": 11709428859, "seconds": 308.2, "hit_count": 1}
```

The one hit is `GlobalPersistentCookerData.upk` (109,590,691 B). Its name stream carries each
property exactly once, class-qualified and typed:

| record in the package | count |
|---|---|
| `FloatProperty BmGame.RVehicleBatmobileBase:StrafeCooldown` | 1 |
| `StructProperty BmGame.RVehicleBatmobileBase:StrafeRight` | 1 |
| `FloatProperty BmGame.RVehicleBatmobileBase:StrafeForce` | 1 |
| `FloatProperty BmGame.RVehicleBatmobileBase:StrafeTorque` | 1 |
| `FloatProperty BmGame.RVehicleBatmobileBase:StrafeDuration` | 1 |
| `FloatProperty BmGame.RVehicleBatmobileBase:StrafeTime` | 1 |
| `FloatProperty BmGame.RVehicleBatmobileBase:StrafeFwdCorrectionForce` | 1 |
| `ObjectProperty BmGame.RVehicleBatmobileBase:TransformationAnimNode` | 1 |
| `ObjectProperty BmGame.RVehicleBatmobileBase:StrafeTarget` | 1 |

That is the **class schema**: the properties exist, with their types (`StrafeRight` really is a
struct, `StrafeTarget`/`TransformationAnimNode` really are object refs). The same file also holds
the class's CDO name stream - 1,424 `…BmGame.Default__RVehicleBatmobileBase:…` records - and
**`Default__RVehicleBatmobileBase:Strafe` occurs 0 times**, while e.g.
`Default__RVehicleBatmobileBase:SVehicleMesh` is there. So the CDO names its mesh, its components
and its other properties, and names **none** of the nine: no default *value* is stored for them
anywhere in the install.

Read-only side note, recorded as the next step and not as a value: `upk_read.Package` refuses this
package (`UpkError: not chunked and the name table is not where the header says`; its header name
table at 0x174 holds 5 names, the 1,424-record stream lives at 0x3792c0/0x5455b0), so the value
stream of that package is not decoded yet. Finding 3 is what makes that irrelevant for a *default*:
there is no CDO entry to decode.

### 3. The executable has no constructor for this class (route 2)

A C++ default for a field appears as an immediate store at the field's displacement. The test is
the class's own members whose shipped values are known from the archetypes (MODES.md): if this
class had a compiled initialiser in the image, it would set them too.

```
0x1cf8 VehicleShovingTorque (10000 in all four archetypes)  stores: 0
0x1fdc PMDodgeTorque        (6000)                          stores: 0
0x1fe0 PMDodgeForce         (10000)                         stores: 0
0x1fe4 PMDodgeDuration      (0.15)                          stores: 0
```

**Zero** immediate stores at any of the four, in the whole 55,101,440-byte image. So the class's
members are not written by compiled code - its values come from data (the archetype tags, and the
CDO where one exists). That is why the strafe block has no constructor value either, and it also
means the `mov dword [reg+11F8h], …` hits below are **not** this class's initialiser.

### 4. The displacement hits that do exist cannot be bound to the class

`+11F8h` is a displacement, not a field name: MODES.md's own rule is that the same offset means
different members in different classes. What the scan found at the strafe block:

| offset | stores | what they are |
|---|---:|---|
| 0x11EC (`StrafeRight`) | 1 | `mov dword [rsi+11ECh], 0` at RVA 0x12F5ADB - one component, not the vec3 |
| 0x11F0 / 0x11F4 (the vec3's tail) | 2 / 2 | zero-inits at 0x117A96A/0x117A979 and 0x117C9CA/0x117C9D9 |
| 0x11F8 (`StrafeForce`) | 18 | a zero-init run at 0x117A988, `-1.0` at 0x3FFC23/0x3FFEF9/0x400627/0x400C60, `2000.0` at 0x400C6F, 2 `movss` stores |
| 0x11FC (`StrafeTorque`) | 4 | zero-init at 0x117A997 / 0x117C9F7, an **int `1`** at 0x1182B15 (`1.4e-45` read as float) |
| 0x1200 (`StrafeDuration`) | 4 | zero-init at 0x117A9A6 / 0x117CA06, an **int `1`** at 0x1182BC1 |
| 0x1204 (`StrafeTime`) | 3 | zero-init at 0x117A9B5 / 0x117CA15, an **int `1`** at 0x1187DFE |
| 0x1208 (`StrafeFwdCorrectionForce`) | 5 | zero-init at 0x117A9C4 / 0x117CA24, ints `1`, `2`, `3` at 0x117CBA8/0x117CBE0/0x117CCF9 |
| 0x1494 (`TransformationAnimNode`) | 0 | object refs are assigned, not immediates |
| 0x14E4 (`StrafeTarget`) | 0 | same |

Two independent reasons this is not a value: the ints 1/2/3 stored at off-block displacements are
indices or counts in *some other* structure (a float field never holds a denormal), and the
neighbouring zero-inits at 0x117A9xx belong to a class-wide initialiser that touches
`+09A0h`, `+10F4h`, `+1444h`, `+11A4h` (= 1), `+11F0h`…`+1228h` in one run (dump below) - a class
that is *not* `RVehicleBatmobileBase`, since finding 3 shows this class is never initialised in
code.

```
> python Tools/scripts/chase/chase_g1_values.py dump 0x117a900 0x140
0x117a960  00 00 00 00 00 48 8b 44 24 40 c7 80 f0 11 00 00   .....H.D$@......
0x117a970  00 00 00 00 48 8b 44 24 40 c7 80 f4 11 00 00 00   ....H.D$@.......
0x117a980  00 00 00 48 8b 44 24 40 c7 80 f8 11 00 00 00 00   ...H.D$@........
0x117a990  00 00 48 8b 44 24 40 c7 80 fc 11 00 00 00 00 00   ..H.D$@.........
0x117a9a0  00 48 8b 44 24 40 c7 80 00 12 00 00 00 00 00 00   .H.D$@..........
```

`48 8b 44 24 40` = `mov rax,[rsp+40h]` (reload `this`), `c7 80 <disp32> <imm32>` = `mov dword
[rax+disp], imm`; the run is a "set every field to zero in declaration order" initialiser for
whatever class/size that object is.

---

## Row by row

### F-17 · `StrafeRight` (0x11EC, `Vector3`, cm per component if it were a length) - **STILL UNKNOWN**

* **Value:** none. Not 0-by-omission, not a direction - no file states one.
* **Provenance:** would be `decoded` if a value existed; it does not.
* **Evidence:** schema record `StructProperty BmGame.RVehicleBatmobileBase:StrafeRight` (1
  occurrence, `GlobalPersistentCookerData.upk`, name stream at 0x540310-0x54033F);
  `Default__RVehicleBatmobileBase:StrafeRight` 0 occurrences; 0 tags in 20,128 objects; one
  immediate store at RVA 0x12F5ADB (`mov dword [rsi+11ECh], 0`, bytes
  `c786ec11000000000000`) covering only the x component of a 12-byte field.
* **Routes tried:** (1) archetypes + CDOs - negative, measured; (1b) whole install name scan -
  schema only, no CDO value; (2) exe displacement scan - 1 unbindable store; (3) footage - a
  direction vector is not visible; (4) web - 0 results for the property with the class name.

### F-18 · `StrafeForce` (0x11F8, `float`, engine force) - **STILL UNKNOWN**

* **Value:** none.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema record 1 occurrence; CDO record 0; 0 archetype tags; 18 displacement
  stores (list above), the largest being `2000.0` at RVA 0x400C6F next to `-1.0` at 0x400C60 -
  two different objects that both happen to have a float at +11F8h. The class's known members
  (finding 3) have **no** stores, so none of the 18 can be this class's default.
* **Routes tried:** 1, 1b, 2 (18 hits, none bindable), 3 (an engine force is not visible), 4 (0
  results).

### F-19 · `StrafeTorque` (0x11FC, `float`, engine torque) - **STILL UNKNOWN**

* **Value:** none.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema 1; CDO 0; archetype tags 0; 4 stores - zero-inits at 0x117A997/0x117C9F7,
  `movss` at 0x58F89, and **int 1** at 0x1182B15, which is not a torque in any unit.
* **Routes tried:** 1, 1b, 2, 3, 4 - all negative.

### F-20 · `StrafeDuration` (0x1200, `float`, s) - **STILL UNKNOWN**

* **Value:** none. This is the one row where footage could have helped *if* a strafe were in a
  clip; none is.
* **Provenance:** would be `decoded` or `derived` (PTS measurement); neither exists.
* **Evidence:** schema 1; CDO 0; tags 0; 4 stores (zero-inits + int 1 at 0x1182BC1).
* **Routes tried:** (1) 1b negative; (2) unbindable; (3) the five captures were enumerated with
  `ffprobe` - Air steer down 202 f / 7.153 s, Air steer right 267 f / 8.882 s, Air steer up 189 f
  / 6.388 s, VulcanFire 1,352 f / 49.213 s, Battlemode entry+movement+boost 1,096 f / 40.042 s -
  and none contains a lateral *burst* that could define an on/off duration (the air-steer clips
  are ramp jumps, the battle-mode clip is the transformation, movement and boost, the Vulcan clip
  is firing); (4) web - nothing.

### F-21 · `StrafeTime` (0x1204, `float`, s) - **STILL UNKNOWN**

* **Value:** none.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema 1; CDO 0; tags 0; 3 stores (zero-inits + int 1 at 0x1187DFE).
* **Routes tried:** 1, 1b, 2, 3 (same clip inventory as F-20), 4 - all negative.

### F-22 · `StrafeFwdCorrectionForce` (0x1208, `float`, engine force) - **STILL UNKNOWN**

* **Value:** none.
* **Provenance:** would be `decoded`; none found.
* **Evidence:** schema 1; CDO 0; tags 0; 5 stores - zero-inits at 0x117A9C4/0x117CA24 plus the
  ints **1, 2 and 3** at 0x117CBA8/0x117CBE0/0x117CCF9, the clearest proof that this displacement
  is an array index or counter in another structure.
* **Routes tried:** 1, 1b, 2, 3, 4 - all negative.

### F-23 · `TransformationAnimNode` (0x1494, `AnimNodeSequence`) - **STILL UNKNOWN**

* **Value:** none, and none is possible: it is an **object reference** to an anim node, not a
  number. "Finding the value" would mean finding which node object the CDO points at.
* **Provenance:** would be `decoded` (an object name); none found.
* **Evidence:** schema record `ObjectProperty BmGame.RVehicleBatmobileBase:TransformationAnimNode`
  (1); CDO-qualified 0; tags 0; **0** immediate stores (an object ref cannot be an immediate);
  the transformation itself is visible in the Battlemode capture, but the visible animation is not
  the node reference.
* **Routes tried:** 1, 1b, 2, 3, 4 (web: 0 results). The value would come from decoding
  `GlobalPersistentCookerData.upk`'s object stream, which `upk_read` cannot open yet.

### F-24 · `StrafeTarget` (0x14E4, `RVehicle`) - **STILL UNKNOWN**

* **Value:** none. A runtime target reference; a default would only exist if the CDO named one,
  and it does not.
* **Provenance:** would be `decoded` (an object name); none found.
* **Evidence:** schema `ObjectProperty BmGame.RVehicleBatmobileBase:StrafeTarget` (1);
  CDO-qualified 0; tags 0; 0 immediate stores.
* **Routes tried:** 1, 1b, 2, 3 (an object reference is not visible), 4 (0 results).

---

## What changed for the project

1. **MODES.md's `VALUE-NATIVE` reason is now backed by two measurements**: the class schema is
   cooked in exactly one package (`GlobalPersistentCookerData.upk`) and the CDO has **no entry**
   for any of the nine properties; and the executable has **no initialiser** for the class at all
   (proved against `VehicleShovingTorque`/`PMDodge*`, whose shipped values are known).
2. **The eight rows should not be "chased" again by the same routes.** The remaining route is a
   reader for `GlobalPersistentCookerData.upk` (its schema/object stream), and even that can only
   confirm "no value"; the only other source is a runtime probe.
3. **A translation that needs these numbers is blocked, not `class`**: there is nothing to copy.
   If the Batmobile mod wants a strafe, it is a design choice with a value of our own, declared
   as such - not a value from the game.
4. One doc drift is worth a G-card note (not edited here, read-only): MODES.md says the *files*
   carry no value, which is right, but it does not mention that the class schema and a CDO-less
   property set are cooked in `GlobalPersistentCookerData.upk`. A one-line record of that
   package would stop the next session re-running the 3,266-package scan.

## Reproduce

```
python Tools/scripts/chase/chase_g1_values.py packages
python Tools/scripts/chase/chase_g1_values.py scan
python Tools/scripts/chase/chase_namescan.py            # ~5 min, 11.71 GB, read-only
python Tools/scripts/chase/chase_g1_values.py dump 0x117a900 0x140
```

`chase_g1_values.py` reads `BatmanAK.exe` with its own PE section table, so every RVA above is a
file-backed image address (`rva = section.VirtualAddress + file_offset - section.PointerToRawData`).
