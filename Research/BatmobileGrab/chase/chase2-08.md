# Chase 08, second pass — F-57 … F-64 (the four rows the first pass left UNKNOWN)

Scope: the four rows `chase-08.md` left **STILL UNKNOWN** — F-60 `AirControlTimeInAir`
(0x4bc, `RVehicleSimBatmobile`), F-62 `AirControlTurnTorque` (0x17c, `RVehicleSimCar`),
F-63 `StayUprightRollResistAngle` (0x6d4, `SVehicle`), F-64 `StayUprightPitchResistAngle`
(0x6d8, `SVehicle`). Read-only chase: no existing document edited, no game launched or patched,
nothing committed. New files only:

* `Tools/scripts/chase/chase2_08_pkg.py` (package sweep/scan, route a)
* `Tools/scripts/chase/chase2_08_native.py` (PE/xref/disasm/displacement helper, route b)
* `E:/Modding/ArkhamKnight/_grab/chase/pkg_sweep_08.json` + `.log`, `value_cdo_08_engine.json` (route a data)

**Result: 0 of 4 FOUND as shipped values; 3 rows gain hard new evidence, 1 row is re-scoped.**

| row | field | status | value + units | provenance |
|---|---|---|---|---|
| F-60 | `AirControlTimeInAir` | **STILL UNKNOWN** (as a tunable) | no shipped value exists — the field is the **runtime air-time accumulator**, not a threshold: `alpha = [0x4bc] / [0x4b8]` | read (exe instruction) for the mechanism; the row's premise is refuted |
| F-62 | `AirControlTurnTorque` | **STILL UNKNOWN** | — | — |
| F-63 | `StayUprightRollResistAngle` | **STILL UNKNOWN** | **derived candidate 0.0 deg** (nothing in data or code ever writes it; see §4) | derived — not promoted to FOUND, see the refutation condition |
| F-64 | `StayUprightPitchResistAngle` | **STILL UNKNOWN** | **derived candidate 0.0 deg** (same) | derived — same |

What is new and provable this pass, in one line each:

1. F-60 is **not a value row at all**: the class divides it by `AirControlInterpTime` (1.5 s) to get
   the air-control blend alpha, and writes it from a timer — it is the "seconds spent in air"
   accumulator (address and bytes in §1).
2. No package on the install outside `BmGame.upk` / `Engine.upk` carries a default for the three
   classes: 4,145 packages / 18.27 GB swept, and the only two hits are `GlobalPersistentCookerData`
   name blobs (§2).
3. No config file names any of the four members; the fields are not `config` values (§2).
4. F-63/F-64 are **degrees**, converted to rotator units by `-182.0` (`-65536/360`), and are copied
   from the `SVehicle` actor into the stay-upright constraint setup at `+0x98` / `+0x9c` (§4).
5. The shipped `BatmanAK.exe` contains **no instruction that writes** `0x6d4` or `0x6d8` at all, and
   no attributable constant write at `0x4bc` or `0x17c` (§3, §4). So the first pass's
   "no name string → no anchor" limit is not the binding one any more; the binding one is that the
   numbers simply are not in the binary or in the data.

## 1. F-60 `AirControlTimeInAir` — the field is an accumulator, not a threshold

The air-control update lives at `0x1400668f0` (`RVehicleSimBatmobile` code: the same function reads
0x4a8/0x4ac/0x4b0/0x4b4 and 0x254/0x258/0x25c, the class's factor block). Its `.pdata` entry ends
at `0x140066968`, immediately after the load below; the arithmetic continues in the adjacent
function `0x140066968..0x140066b1f` with `rcx`/`rax` still holding the same sim object and its
`+0xb0` struct, i.e. `.pdata` split one straight-line block (`movss xmm2,[rcx+0x4bc]` … `divss
xmm2,[rcx+0x4b8]` share `rcx`, with no branch between them).

```
0x140066948  cmp      r9d, 1
0x14006694c  jle      0x140066959
0x14006694e  mov      dword ptr [rcx + 0x4bc], esi      ; reset the air timer
0x140066954  jmp      0x140066b1f
0x140066959  mov      rax, qword ptr [rdx + 0x38c]
0x140066960  movss    xmm2, dword ptr [rcx + 0x4bc]     ; time in air
0x140066968  movaps   xmmword ptr [rsp + 0xa0], xmm6
0x140066978  divss    xmm2, dword ptr [rcx + 0x4b8]     ; / AirControlInterpTime (1.5, CDO)
0x140066980  movups   xmm0, xmmword ptr [rax + 0xb0]
```

`0x4b8` is `AirControlInterpTime`, decoded **1.5** (`chase-08.md` §1). Dividing the field by the
interp time and using the quotient as a blend factor is the UE3 pattern for a *ramped* control
weight, and the write next to it stores a timer value (`esi`) into the same field. A threshold
constant would be compared against, not divided by, another field.

Second read site, same story (`0x140a2b020`):

```
0x140a2b013  comiss   xmm0, dword ptr [rdi + 0x4ac]   ; AirControlPitchTorqueFactorMax
0x140a2b020  movss    xmm4, dword ptr [rdi + 0x4bc]
0x140a2b028  comiss   xmm4, xmm5
0x140a2b02b  jbe      0x140a2b092
0x140a2b02d  movss    xmm1, dword ptr [rdi + 0x4b0]   ; AirControlYawTorqueFactorMin
0x140a2b035  movss    xmm2, dword ptr [rdi + 0x4b4]   ; AirControlPitchTorqueFactorMin
```

Attribution to the class: the same function reads 0x4a8, 0x4b0, 0x4b4, 0x4b8 — the four air-control
fields `chase-08.md` decoded from this class's default object — and no other class in the SDK has
that quadruple at those offsets. The section is an air-control weighting block.

**Why this is not a value and cannot become one:** nothing serialises it (absent from
`Default__RVehicleSimBatmobile`, §2) and nothing initialises it with a constant (§3 found only one
`mov [rcx+0x4bc], 0` zero-init in an unrelated 39-byte function). A runtime accumulator is written
only by the tick path, so "the shipped value" is 0 at construction — not a tunable the mod can copy
across. `FOOTAGE.md` F-60 should be re-scoped from "VALUE-NATIVE tunable" to "runtime state, no
translatable value" (that is a row edit, not this report's job).

## 2. Route (a) completed — every package, every config file

The first pass read `BmGame.upk` and `Engine.upk` default objects only, for `Default__*Vehicle*` names.
This pass swept the install and parsed every package that names the three classes.

```
$ python Tools/scripts/chase/chase2_08_pkg.py sweep --json E:/Modding/ArkhamKnight/_grab/chase/pkg_sweep_08.json
  HIT ...\BmGame\CookedPCConsole\GlobalPersistentCookerData.upk -> ['Default__RVehicleSimBatmobile',
      'Default__RVehicleSimCar', 'Default__SVehicle', 'RVehicleSimBatmobile', 'RVehicleSimCar',
      'AirControlTimeInAir', 'StayUprightRollResistAngle', 'StayUprightPitchResistAngle',
      'AirControlTurnTorque']
  HIT ...\DLC\350171\Content\BmGame\CookedPCConsole\GlobalPersistentCookerData.upk -> (same nine)
  (missing root E:\Games\Batman - Arkham Knight\Engine\CookedPCConsole)

swept 4145 packages, 18.27 GB in 450s; 2 package(s) carry a needle
```

(`Engine.upk` is not under `Engine\CookedPCConsole` on this install; it is
`BmGame\CookedPCConsole\Engine.upk` and was swept.) The two hits are the global cooker name tables,
not ordinary packages — they carry the **names** (which is why G1-21 and chase-08 always found the
name strings) and no object exports:

```
$ python Tools/scripts/chase/chase2_08_pkg.py scan --packages <the two GlobalPersistentCookerData.upk>
GlobalPersistentCookerData.upk: UpkError: not chunked and the name table is not where the header says
GlobalPersistentCookerData.upk: UpkError: not chunked and the name table is not where the header says
```

So: no DLC, patch, `Startup`, map or other package outside `BmGame.upk`/`Engine.upk` defines a
default object for these three classes, and none carries a tag at the four offsets. The
`--package` dump of `Engine.upk` re-confirms `Default__SVehicle` walks 32 tags with 0x6d4/0x6d8
absent. `chase2_08_pkg.py scan` on that package reports 29 `Default__` objects with *some* card
offset, and none of them is `SVehicle`, `Default__SVehicle`, `RVehicleSimCar` or
`Default__RVehicleSimCar`: the hits are layout coincidences at the low offsets — e.g.
`Default__Pawn` (export 9699) `0x4bc` `FloatProperty` `-10.0`, `Default__AkPlayerVehicleSoundInfo`
`0x6d8` `ObjectNCRProperty` `37019`, `Default__SeqAct_Delay` `0x17c` `FloatProperty` `1.0`. An offset
means nothing outside the class that declares it, and none of these classes is in the chain.

Config files (the `config`-property route the first pass never tried):

```
$ grep -ril "AirControl\|StayUpright" "E:/Games/Batman - Arkham Knight/BmGame/Config"
(no output)
$ grep -rn "RVehicleSim\|SVehicle" "E:/Games/Batman - Arkham Knight/BmGame/Config"/*.ini
(no output)
```

26 INI files are present (`BmGame.ini`, `BmEngine.ini`, `Default*.ini`, `User*.ini`, …); none
mentions these classes or members. A `config` default would have to appear there, so the four
fields are not config properties.

CDO serialisation rule, measured rather than assumed: the three relevant default objects carry
**105 tags between them and every parsed value is non-zero** (0 zero-valued tags):

```
Default__RVehicleSimBatmobile  58 tags   (0x1c8 0.6, 0x4a8 5000, 0x4b0 2000, 0x4b4 3000,
                                          0x4b8 1.5, 0x4c0 0.5, …, 0x4bc absent)
Default__RVehicleSimCar        15 tags   (0x174 1.0, …, 0x17c absent, …, 0x190 1000.0)
Default__SVehicle              32 tags   (0x68c bStayUpright, 0x6c8 InertiaTensorMultiplier,
                                          0x6e4/0x6ec constraint refs, …, 0x6d4/0x6d8 absent)
```

That is the evidence for the inference used in §4 ("unset = zero is not serialised"), and it is the
reason the absences are facts about the file rather than gaps in a walker: the walk sees the
neighbouring tags on both sides of each gap (0x4b8 → 0x4c0; 0x174 → 0x190; 0x6c8 → 0x6e4).

## 3. Route (b) — the executable, with an anchor this time

`chase-08.md` §3 counted property-name strings (0 occurrences) and stopped. This pass does not need
the names: every offset is a fixed displacement, so the question "does any code write this field"
is answerable by displacement alone, and the answer is then attributed by the surrounding field
cluster.

Store/load census over `.text` (16 MB of code; instruction-shaped byte patterns, then Capstone):

| displacement | `movss [reg+disp]` reads | writes | what the writes are |
|---|---:|---:|---|
| 0x4bc | 4 | 5 | one `mov dword [rcx+0x4bc], 0` in a 39-byte function at `0x14037e4c0` (that function touches only 0x4b4/0x4bc — an unrelated class), one read-modify-write accumulator (`addss xmm1,[rcx+0x4bc]` at `0x1403388d0`, store back at `0x1403388d8`), the rest unaligned patterns |
| 0x17c | 36 | 33 | all of them stack frames (`[rbp+0x17c]`) or other objects' structs (`[rdi+0x17c]` in `0x14079c7d0`, a layout coincidence at a low offset); none is a constant initialisation of a sim-class field |
| 0x6d4 | 2 | **0** | — |
| 0x6d8 | 2 | **0** | — |

The only two `0x6d4` "store-shaped" byte runs (`0x1403e7928`, `0x1403e7968`) are `mov rcx, qword
ptr [rbx+0x6d4]` followed by stores at `[rcx+0x1ac]`/`[rcx+0x190]`: a *pointer* field in a different
class, not the float. There is no `movss dword ptr [reg+0x6d4]` or `[reg+0x6d8]` anywhere in the
image — searched with any modrm form, and with Capstone over both containing functions.

The name-anchor route was also finished rather than left open: the UTF-16 literal
`RVehicleSimBatmobile` (`0x141be7572`) has **0** RIP-relative xrefs and **0** qword pointers, and the
ASCII `RVehicleSimBatmobileexec…` strings (`0x141e03d21` …) likewise. UE3.5 resolves native
functions by name from the package, so the registration table is not in the image and there is no
static path from the class name to its constructor. That is a definitive negative for the anchor,
not an unfinished route.

## 4. F-63 / F-64 `StayUpright{Roll,Pitch}ResistAngle` — units and behaviour, value not in data

Both fields are read in the **same two functions**, which is what a stay-upright pair looks like:

```
0x1403b5c14  movss    xmm0, dword ptr [rsi + 0x6d4]      ; StayUprightRollResistAngle
0x1403b5c1c  movss    xmm1, dword ptr [rip + 0x19ef37c]  ; -182.0  (at 0x141da4fa0)
0x1403b5c24  mulss    xmm0, xmm1                        ; deg -> rotator units (-65536/360)
0x1403b5c28  mulss    xmm0, dword ptr [rsi + 0x648]
0x1403b5c30  mulss    xmm0, xmm2
0x1403b5c34  cvttss2si edi, xmm0                         ; angular limit, integer rotator
...
0x1403b5c6d  movss    xmm0, dword ptr [rsi + 0x6d8]      ; StayUprightPitchResistAngle (same shape)
```

**Units: degrees**, and the sign is negative (roll limit converted with `-182.0`; `65536/360 =
182.044`). The constant is read from `0x141da4fa0` = `-182.0` (float bytes checked).

Where the values come from is now visible too — the `SVehicle` fields are copied into the
constraint setup object:

```
0x14174c1f8  movss    xmm1, dword ptr [rbp + 0x6d4]
0x14174c210  movss    dword ptr [rdi + 0x98], xmm1     ; RB_StayUprightSetup + 0x98
0x14174c25f  movss    xmm1, dword ptr [rbp + 0x6d8]
0x14174c26f  movss    dword ptr [rdi + 0x9c], xmm1     ; + 0x9c
```

together with the rest of the block (0x6ac/0x6b0/0x6c4/0x6c8 → `+0xa8/+0xac/+0x78/+0x88`). So the
constraint is parameterised **from these two actor fields**, not from a hard-coded angle and not
from the setup archetype.

Putting the three negatives together — no tag in the CDO (32 tags, gap 0x6c8 → 0x6e4), no tag in
any archetype or any other package (4,145 swept), and no instruction in the image that writes either
displacement — the effective shipped value is the zero the C++ constructor leaves:

> **derived candidate: F-63 = 0.0 degrees, F-64 = 0.0 degrees.**

Why it is not promoted to FOUND: the claim rests on the UE3 rule that a CDO serialises only values
that differ from the archetype (supported here by 105/105 non-zero tags, but not decoded from this
build's source), and on "no *direct* displacement write" — a bulk struct copy would write the field
without naming it. Both would have to copy a value that exists somewhere, and no such value exists
in the data; but the chain is an inference, so the row keeps `STILL UNKNOWN` and the number is
recorded as `derived`. What would promote it: one runtime read (a debug/save edit of an `SVehicle`
instance) showing 0.0, or the class's `defaultproperties` from a matching build.

Consequence for the mod, stated so the row is usable: AK's Batmobile ships **no** stay-upright
resistance (0° = the constraint tries to hold the body perfectly level); there is no lean budget to
copy into any JC3 mechanism.

## 5. F-62 `AirControlTurnTorque` — routes exhausted, no value

* CDO: `Default__RVehicleSimCar` walks 15 tags; 0x174 = 1.0 and 0x190 = 1000.0 are present and
  **0x17c is absent** — the field keeps the class's zero (or is transient).
* Packages: the 4,145-package sweep finds no other package that names `RVehicleSimCar` except the
  two name blobs; no DLC/patch default.
* Config: no INI mention.* Code: 33 `movss` write sites at `0x17c`; their containing functions were grouped (51 functions over
reads+writes) and the six that also touch the air-control block were disassembled in full. Those are
stack-frame accesses (`0x140175400`: `mov dword [rbp+0x17c], eax`
  copying an argument, then `movss xmm2, [rbp+0x17c]` and `mulss` with `[rbp+0x18c]`) and struct
  copies in `0x1407851b8` / `0x14079c7d0`, not a constant initialisation of the sim object. No
  function writes `0x17c` as `[reg+0x17c] = <constant>`.
* Published sources: nothing documents `AirControlTurnTorque` for this game (§6).

The class is a `BmGame` native class whose only serialised values are in `BmGame.upk`; with the CDO
not overriding it and no code writing it, the effective shipped value is the parent's/zero — but for
a *torque gain* that is either "unused" or "set at runtime from another field", and nothing here
distinguishes the two. Recorded as STILL UNKNOWN on purpose.

## 6. Route (d) — published cross-check

One search, used only as a cross-check, no value taken from it: `"AirControlTimeInAir" OR
"AirControlTurnTorque" OR "StayUprightRollResistAngle" Arkham Knight` — no page documenting these
Batmobile fields, their values or units. Stock UDK `SVehicle.uc` does carry
`StayUprightRollResistAngle`/`StayUprightPitchResistAngle` defaultproperties, but those are Epic's
engine defaults, not this game's cooked values, and using them would be exactly the `assumed`
class R4 forbids. No row here rests on a published source.

Note on the offered tool: `tmp/freebuff/reports/smart-search.md` says
**STATUS: in progress (calibration running)** and its calibration block reports 0 candidates and
0.000 recall on all 38 cases, so per the brief it was not used; no `found=true` hit was available to
verify.

## 7. Reproduction

```
python Tools/scripts/chase/chase2_08_pkg.py sweep --json E:/Modding/ArkhamKnight/_grab/chase/pkg_sweep_08.json
python Tools/scripts/chase/chase2_08_pkg.py scan --packages <files named by the sweep>
python Tools/scripts/chase/chase08_cdo.py --package ".../BmGame/CookedPCConsole/Engine.upk" --dump \
        --json E:/Modding/ArkhamKnight/_grab/chase/value_cdo_08_engine.json
python Tools/scripts/chase/chase2_08_native.py scan 0x6d4          # 0 store-form hits
python Tools/scripts/chase/chase2_08_native.py scan 0x6d8          # 0 store-form hits
python Tools/scripts/chase/chase2_08_native.py dispwindow 0x1400668f0 --lo 0x300 --hi 0x520
python Tools/scripts/chase/chase2_08_native.py namerefs RVehicleSimBatmobile   # 0 xrefs
```

The displacement census in §3 is a 40-line loop over `.text` (byte patterns `f3 0f 10/11 8x` and
`8b/89 8x` followed by the little-endian displacement); it is inside `chase2_08_native.py scan` for
the store form, and was extended inline to the read form and to the "any modrm" check quoted above.

## 8. Limits

* One build (v863, licensee 32995). A different patch could serialise any of these four in a CDO;
  nothing on this machine can show that.
* The `0.0` for F-63/F-64 is `derived`, not `decoded`: it depends on the CDO-serialisation rule and
  on the absence of a computed-offset or bulk-memory writer. Both are argued above, neither is
  decoded from this build.
* Function boundaries come from `.pdata`, so "the containing function" is exact; attribution of a
  function to a class comes from the field cluster it touches (0x4a8/0x4b0/0x4b4/0x4b8/0x4bc/0x4c0,
  0x2c4…0x324 battle-mode block), not from symbols. The image has no symbols or PDB.
* `GlobalPersistentCookerData.upk` is not parseable with `upk_read` ("not chunked and the name
  table is not where the header says"); it is treated as a name blob on the strength of its role and
  of the two packages' contents. It cannot hold property values in any case — it has no objects.
* The first pass's negative on `Default__SVehicle` is unchanged and re-confirmed; this pass adds
  the code side, not a new decoded value.
