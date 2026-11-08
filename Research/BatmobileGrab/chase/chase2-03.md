# Chase 2-03 — second pass on the eight strafe rows (F-17 … F-24)

Scope: every row `Research/BatmobileGrab/chase/chase-03.md` leaves **STILL UNKNOWN** — F-17 … F-24,
all eight `RVehicleBatmobileBase` strafe/animation/target properties.

Read-only: no existing document, package or game file was changed; nothing was written under
`E:/Games` or `D:/Games`, no game was launched, nothing was committed. Writes: one new script
`Tools/scripts/chase/chase2_native.py` and this file.

**Smart-search tool:** `tmp/freebuff/reports/smart-search.md` shows `STATUS: deferred`, not `done`,
so `smart_search.py` was not run (the task makes it conditional on `done`).

**Result: 8 of 8 rows now have an answer — the class default object exists in `BmGame.upk` and the
class's constructor exists in the executable, at `0x14117A860`. chase-03 looked in the wrong
package scope and concluded from a false negative that neither existed.**

| row | member | status | value |
|---|---|---|---|
| F-17 | `StrafeRight` (0x11EC, `Vector3`) | **FOUND** | **(0.0, 0.0, 0.0)** — no direction is set |
| F-18 | `StrafeForce` (0x11F8, float) | **FOUND** | **0.0** |
| F-19 | `StrafeTorque` (0x11FC, float) | **FOUND** | **0.0** |
| F-20 | `StrafeDuration` (0x1200, float) | **FOUND** | **0.0 s** |
| F-21 | `StrafeTime` (0x1204, float) | **FOUND** | **0.0 s** |
| F-22 | `StrafeFwdCorrectionForce` (0x1208, float) | **FOUND** | **3000.0** |
| F-23 | `TransformationAnimNode` (0x1494, object) | **FOUND** | **none** (null reference) |
| F-24 | `StrafeTarget` (0x14E4, object) | **FOUND** | **none** (null reference) |

---

## The two objects chase-03 said did not exist

### 1. The class default object *is* cooked — in `BmGame.upk`, not in the 20 packages

chase-03 scanned the 20 `Playable_Batmobile*` packages (20 128 exports) and concluded "no CDO value
for any of the nine". The CDO is in `BmGame.upk`, which that scan never opened:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RVehicleBatmobileBase
Default__RVehicleBatmobileBase  export[10923]  class=RVehicleBatmobileBase  size=3186  chain=RVehicleBatmobileBase -> RVehicle -> AkVehicle
  RVehicleBatmobileBase.bWeaponsReady (0x11D8)         BoolProperty                 True
  RVehicleBatmobileBase.bWeaponGeneratorShielding (0x11E0) BoolProperty                 True
  RVehicleBatmobileBase.StrafeCooldown (0x11E4)        FloatProperty                0.75
  RVehicleBatmobileBase.StrafeFwdCorrectionForce (0x1208) FloatProperty                3000.0
  ...
201 tags
```

`StrafeFwdCorrectionForce` (0x1208) holds **3000.0** there, and `StrafeCooldown` (not a row) holds
0.75. The eight chased members other than 0x1208 have **no tag** in this object.

### 2. The class constructor *is* in the executable — at `0x14117A860`

chase-03 scanned four offsets whose shipped values are known from archetypes (0x1CF8, 0x1FDC,
0x1FE0, 0x1FE4), found no stores, and concluded "the executable has no constructor for this class".
Those four are simply not members this constructor touches. Locating the constructor by its *own*
field stores instead gives a 839-byte function between `0x14117A860` and `0x14117ABA7` (boundaries
from `.pdata`):

```
$ python Tools/scripts/chase/chase2_native.py func 0x14117a860 --len 40
function 0x14117a860 .. 0x14117aba7  (839 bytes)
0x014117a860  48894c2408           mov      qword ptr [rsp + 8], rcx
0x014117a865  4883ec38             sub      rsp, 0x38
0x014117a869  488b442440           mov      rax, qword ptr [rsp + 0x40]
...
```

and the strafe block inside it:

```
$ python Tools/scripts/chase/chase2_native.py stores 0x14117a860 0x14117aba7
0x014117a96a  c780f011000000000000 dword ptr [rax + 0x11f0] <- 0   disp=0x11f0
0x014117a979  c780f411000000000000 dword ptr [rax + 0x11f4] <- 0   disp=0x11f4
0x014117a988  c780f811000000000000 dword ptr [rax + 0x11f8] <- 0   disp=0x11f8
0x014117a997  c780fc11000000000000 dword ptr [rax + 0x11fc] <- 0   disp=0x11fc
0x014117a9a6  c7800012000000000000 dword ptr [rax + 0x1200] <- 0   disp=0x1200
0x014117a9b5  c7800412000000000000 dword ptr [rax + 0x1204] <- 0   disp=0x1204
0x014117a9c4  c7800812000000000000 dword ptr [rax + 0x1208] <- 0   disp=0x1208
...
47 immediate store(s)
```

**Why this is `RVehicleBatmobileBase`'s constructor and not another class's:** it writes five
displacements that `BMSDK_OFFSETS.json` resolves to members of this class in one run —
`0x11F8 StrafeForce`, `0x1208 StrafeFwdCorrectionForce`, `0x1210 EbrakeTime`, `0x1444
ActualPMWeapons`, `0x147C BattleModePrimaryWeapon` — plus `0x11F0`/`0x11F4`, which are the *y* and
*z* components of the 12-byte `StrafeRight` struct at `0x11EC`. No other class shares that set.

### How the three layers compose (the rule used below)

`RVehicleBatmobileBase` declares 518 properties in `BMSDK_OFFSETS.json`; its CDO serialises **201**
tags. A cooked CDO writes only the properties that differ from the class default, so **absent tag =
class default**, and the class default is whatever the constructor above wrote. The shipped
Batmobile archetype then adds nothing: `scanfield` over `Playable_Batmobile_SF.upk` reports **0**
hits for `StrafeFwdCorrectionForce`, `StrafeForce`, `StrafeCooldown`, `StrafeRight` and
`StrafeTarget` (chase-03 measured the same over all 20 packages). So each value below is the value
that runs, and its layer is named.

---

## Row by row

### F-17 · `StrafeRight` (0x11EC, `Vector3`) — FOUND: (0.0, 0.0, 0.0)

* **Value:** a zero vector, i.e. **no strafe direction is set**. Units would be cm per component if
  it were a length; a zero vector is not a direction.
* **Provenance:** decoded (two explicit stores + the struct's class default for the third
  component).
* **Evidence:** the constructor zeroes the struct's y and z components —
  `0x014117a96a c780f011000000000000 mov dword [rax+0x11f0], 0` (y) and
  `0x014117a979 c780f411000000000000 mov dword [rax+0x11f4], 0` (z); the x component at `0x11EC`
  has **no store in the function and no CDO tag**, so it stays at the struct's serialised default,
  which is zero. `Default__RVehicleBatmobileBase` has no `0x11EC` tag at all, and the shipped
  archetype has none (0 hits).
* **Caveat, stated rather than hidden:** x is proven zero only by "no layer writes it and the CDO
  omits default-valued properties", not by an immediate store at 0x11EC. y and z are immediate
  stores and are stronger.
* **Routes tried this pass:** (a) CDO of the class in `BmGame.upk` — absent; (b) constructor
  disassembly — the two components; (c) not visible; (d) not used.

### F-18 · `StrafeForce` (0x11F8, float, engine force) — FOUND: 0.0

* **Value:** **0.0** (engine force units).
* **Provenance:** decoded (immediate store in the class constructor; no CDO or archetype override).
* **Evidence:** `0x014117a988 c780f811000000000000 mov dword [rax+0x11f8], 0`; the CDO has no tag at
  0x11F8; `scanfield … StrafeForce` = 0 in the shipped archetype package.
* **Routes tried this pass:** (a) CDO — absent tag; (b) constructor — the immediate; (c) an engine
  force is not visible; (d) not used.

### F-19 · `StrafeTorque` (0x11FC, float, engine torque) — FOUND: 0.0

* **Value:** **0.0**.
* **Provenance:** decoded (immediate store).
* **Evidence:** `0x014117a997 c780fc11000000000000 mov dword [rax+0x11fc], 0`; no CDO tag; no
  archetype tag.
* **Routes tried:** (a) CDO — absent; (b) constructor — the immediate; (c), (d) not applicable.

### F-20 · `StrafeDuration` (0x1200, float, s) — FOUND: 0.0

* **Value:** **0.0 s** — a zero-length burst, i.e. the burst path is disabled by its own defaults.
* **Provenance:** decoded (immediate store).
* **Evidence:** `0x014117a9a6 c7800012000000000000 mov dword [rax+0x1200], 0`; no CDO tag; no
  archetype tag (`StrafeDuration` 0 hits in the shipped package). Footage is irrelevant now: the
  file value exists and R4 puts a file value above a measurement.
* **Routes tried:** (a) CDO — absent; (b) constructor — the immediate; (c) none needed (no strafe in
  any clip, as chase-03 established); (d) not used.

### F-21 · `StrafeTime` (0x1204, float, s) — FOUND: 0.0

* **Value:** **0.0 s**.
* **Provenance:** decoded (immediate store).
* **Evidence:** `0x014117a9b5 c7800412000000000000 mov dword [rax+0x1204], 0`; no CDO tag; no
  archetype tag.
* **Routes tried:** (a) CDO — absent; (b) constructor — the immediate; (c), (d) not applicable.

### F-22 · `StrafeFwdCorrectionForce` (0x1208, float, engine force) — FOUND: 3000.0

* **Value:** **3000.0** (engine force units).
* **Provenance:** decoded (CDO tag; the CDO overrides the constructor's 0; the shipped archetype
  overrides neither).
* **Evidence:** the CDO tag

  ```
  Default__RVehicleBatmobileBase.StrafeFwdCorrectionForce (0x1208) FloatProperty 3000.0
  ```

  while the constructor writes 0 there (`0x014117a9c4 c7800812000000000000`). UE3 deserialises the
  CDO over the constructor's values and instances inherit the CDO, so **3000.0** is the value that
  runs. `scanfield Playable_Batmobile_SF.upk StrafeFwdCorrectionForce` = 0 hits, so no archetype
  overrides it. This is the only one of the eight with a non-zero value, and the only one chase-03's
  "no file states one" is flatly wrong about.

### F-23 · `TransformationAnimNode` (0x1494, `AnimNodeSequence`) — FOUND: none (null)

* **Value:** **no object reference** — the property is null.
* **Provenance:** decoded (three layers agree: no CDO tag at 0x1494, no store in the class
  constructor, no archetype tag).
* **Evidence:** the CDO's 201 tags contain no 0x1494 entry; `stores 0x14117a860 0x14117aba7` lists no
  store to 0x1494 (an object reference is assigned, not immediate-stored, and no `mov` to that
  displacement appears at all); `scanfield Playable_Batmobile_SF.upk TransformationAnimNode` = 0.
  Absent CDO tag = class default = null, so no anim node is named by the shipped data.
* **Consequence for the row:** the row asked *which* node the CDO points at; the answer is that it
  points at none, and the transformation anim node is chosen at runtime (or not at all).

### F-24 · `StrafeTarget` (0x14E4, `RVehicle`) — FOUND: none (null)

* **Value:** **no object reference** — the property is null (a strafe has no default target).
* **Provenance:** decoded (same three-layer absence as F-23).
* **Evidence:** no 0x14E4 tag in `Default__RVehicleBatmobileBase`; no store to 0x14E4 in the
  constructor; `scanfield … StrafeTarget` = 0 in the shipped archetype package.

---

## Corrections to chase-03 (files untouched)

1. **The install-wide name scan could not see compressed packages.** `chase_namescan.py` greps raw
   bytes for the property names, on the premise that "FName strings are plain ASCII in the package".
   `BmGame.upk` is compressed, so a raw grep of it finds **0** occurrences of names its decoded name
   table certainly holds:

   ```
   $ grep -c StrafeForce BmGame.upk                     # 214 757 637 B
   0
   $ python Tools/scripts/chase/ch1_probe.py names BmGame.upk -g "^Strafe"
     name[75151] StrafeCooldown
     name[75153] StrafeDuration
     name[75156] StrafeForce
     name[75164] StrafeRight
     name[75165] StrafeTarget
     name[75166] StrafeTime
   ```

   So "exactly one package in the whole install names them" is an artefact of the scan working only
   on uncompressed files; the 3 266-file, 11.71 GB pass proves nothing about compressed packages,
   `BmGame.upk` included.

2. **"No CDO value for any of the nine" is false.** `Default__RVehicleBatmobileBase` in `BmGame.upk`
   (`export[10923]`, 3 186 B, 201 tags) carries `StrafeCooldown` 0.75 and
   `StrafeFwdCorrectionForce` **3000.0**. chase-03's scan scope was the 20 `Playable_Batmobile*`
   packages; `BmGame.upk` was never opened for this purpose.

3. **"The executable has no constructor for this class" is false.** The constructor is
   `0x14117A860 … 0x14117ABA7` (`.pdata`), and it initialises the whole strafe block. The four
   offsets chase-03 tested (0x1CF8, 0x1FDC, 0x1FE0, 0x1FE4) are not members this constructor writes,
   so their absence proves nothing about the class.

4. **The zero-init run at `0x117A9xx` belongs to this class after all.** chase-03 called it "a class
   that is *not* `RVehicleBatmobileBase`"; it is inside `0x14117A860`, and its displacements
   (`0x11F0`, `0x11F4`, `0x11F8`, `0x11FC`, `0x1200`, `0x1204`, `0x1208`) resolve through
   `BMSDK_OFFSETS.json` to this class's strafe members.

5. **The conclusion "there is nothing to copy" is wrong for one row and right for seven.** F-22 has
   a decoded shipped value (3000.0); F-18…F-21 ship as 0.0; F-17 is the zero vector; F-23/F-24 are
   null. A port that needs a *working* strafe still has to choose its own forces (the shipped ones
   are zero), but that is now a fact about the data, not an absence of it.

## What this changes for the project

- The strafe block is **present and zeroed in the class constructor**, with one non-zero member
  (`StrafeFwdCorrectionForce` 3000.0) that only the CDO sets. A translation should carry those
  numbers as the shipped defaults, and must not read "zero" as "not implemented upstream": the
  fields exist, are serialised, and are simply disabled.
- `StrafeDuration`/`StrafeTime` = 0.0 s means the shipped burst has no duration; the air-control
  behaviour seen in the captures comes from `RVehicleSimBatmobile`'s torque factors (chase-01 F-6),
  not from this block.
- The remaining question is a *design* one (what strafe force the mod wants), not a data question.

## Reproduce

```
python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RVehicleBatmobileBase
python Tools/scripts/chase/chase2_native.py func   0x14117a860
python Tools/scripts/chase/chase2_native.py stores 0x14117a860 0x14117aba7
python Tools/scripts/chase/ch1_probe.py scanfield Playable_Batmobile_SF.upk StrafeFwdCorrectionForce
python Tools/scripts/chase/ch1_probe.py names BmGame.upk -g "^Strafe"
```

`chase2_native.py` is new this pass (`sections` / `string` / `xref` / `disasm` / `ptr` / `ptrtable`
 / `func` / `stores`); it opens `BatmanAK.exe` with `rb` only. No game was launched, nothing under
`E:/Games` or `D:/Games` was written, `FOOTAGE.md`, `chase-03.md`, `GRAB_BACKLOG.md` and `MODLOG.md`
were not edited, nothing was committed, and no secret is in this file.
