# Chase 02, second pass — F-8 … F-16 and the two UNKNOWNs the first pass left

Read first: `chase-02.md` (the first pass). It closed **F-9 … F-16**, all eight `FOUND`, from the
class *default objects* in `BmGame.upk`, and left three things open in its
*Limits / UNKNOWNs* section. That is what this pass takes: there is **no row in `chase-02.md` marked
`STILL UNKNOWN`**, so "every unresolved row" is those three items plus an independent check of the
eight values, because all eight rested on one property-tag walker and a walker that desyncs can still
land on the right offset with a wrong value.

Result:

| row | field | value | provenance | this pass |
|---|---|---|---|---|
| **F-8** | `BattleModeCamConfig` | `FFreeCameraConfig` struct, tag 0x3df4 (15860), 24 members — table below | `decoded` | **FOUND** (first pass: *"noted, not chased"*) |
| F-9 | `BattleModeWinchCamConfig` | struct @0x3e9c, 24 members | `decoded` | FOUND, re-derived byte-for-byte |
| F-10 | `BattleModeAbseilingCamConfig` | struct @0x3f44, 24 members | `decoded` | FOUND, re-derived byte-for-byte |
| F-11 | `BattleModeCamFOV` | **60.0 deg** | `decoded` | FOUND, re-derived byte-for-byte |
| F-12 | `BattleModeWinchCamFOV` | **60.0 deg** | `decoded` | FOUND, re-derived byte-for-byte |
| F-13 | `BattleModeHeadOffset` | **(0, 0, 150) cm** = 1.5 m | `decoded` | FOUND, re-derived byte-for-byte |
| F-14 | `BattleModeWinchHeadOffset` | **(0, 0, 300) cm** = 3.0 m | `decoded` | FOUND, re-derived byte-for-byte |
| F-15 | `BattleModeAbseilingExtraCameraRot` | rotator **(1500, 0, 0)** = +8.24 deg pitch | `decoded` value, `derived` degrees | FOUND, re-derived byte-for-byte |
| F-16 | `StrafeCooldown` | **0.75 s** | `decoded` | FOUND, re-derived byte-for-byte |
| **U-1** | unit of `maxPitch` / `MinPitch` (chase-02 limit 2) | 6000 / −8000 (F-9), 6000 / −14000 (F-8), 14500 / −14000 (F-10), unit **UNKNOWN** | value `decoded`, unit none | **STILL UNKNOWN** — see U-1 |
| **U-2** | does anything write `BattleModeCamFOV` at runtime (chase-02 limit 1) | **UNKNOWN** | — | **STILL UNKNOWN** — see U-2 |

Nothing here is `assumed`. Every number is a property tag read out of the shipped package, and every
row below carries the bytes it came from.

## Address label — correction to the first pass

`chase-02.md` prints `export file offset` / `abs`. That is not a file offset: `BmGame.upk` is
chunk-compressed (214,757,637 B on disk) and `Package.image` is the *decompressed* image
(356,085,334 B), so `export.offset` is **image-relative**. This pass prints `image+0x…` so the label
is exact; the numbers themselves are unaffected, and they reproduce (below).

## Evidence: independent re-derivation, not a re-read of the first pass

`Tools/scripts/chase/chase2_verify.py` finds each tag, prints the payload bytes at
`export.offset + tag.at`, and decodes them with `struct` only — the walker's own `_decode_simple` is
not consulted. The expected values are written down from `chase-02.md`'s table, so a MATCH proves the
first pass reproduced the bytes and a DIFF cannot hide.

```
$ python Tools/scripts/chase/chase2_verify.py --json E:/Modding/ArkhamKnight/_grab/chase/chase2_verify.json
package BmGame.upk: version 863, 177031 exports, image 356,085,334 B
  Default__R3rdPersonCamera: export 34970, image+0x12347c6, 34362 B, 447 tags, stop=eof
  Default__RVehicleBatmobileBase: export 10923, image+0x1022d59, 3186 B, 181 tags, stop=eof
...
F-11 BattleModeCamFOV  @0x4fd0  FloatProperty  image+0x123bbd8  payload 4 B
   bytes 00 00 70 42
   decoded 60.0  (chase-02 expected 60.0)
   MATCH
...
rows 9, diffs 0
$ python Tools/scripts/chase/chase2_verify.py --check --json "" ; echo $?
0
```

`--check` re-runs every comparison and exits non-zero on any DIFF (R11); it exited `0`, `diffs 0`.
The JSON (`image_offset`, `bytes`, per-member values) is the machine copy of the tables below.

## F-8 · `BattleModeCamConfig` — now FOUND

**STATUS: FOUND.** `BmGame.upk`, export 34970 `Default__R3rdPersonCamera`, StructProperty at field
offset **0x3df4 (15860)**, payload 266 B, tag at `image+0x1239eda`. First payload bytes
`0b 00 00 00 00 00 af c3 00 00 00 00 00 00 48 43 0b 00 0c 00 00 00 fa c3`.

Re-walked as 24 sub-tags whose offsets are relative to the struct and match the BmSDK
`classes.R3rdPersonCamera.structs.FFreeCameraConfig` member offsets 0/12/24/28/40/52/64/76/80/84/88/
92/96/100/104/108/112/116/120/132/144/156/160/164 one to one; the walk consumes 264 of the 266 B and
the last 2 B are the 0-type list terminator (same as F-9/F-10).

| member | off | F-8 `BattleModeCamConfig` | F-9 winch | F-10 abseiling |
|---|---|---|---|---|
| `StateFreeCameraSitOffsetMin` | 0 | [-350, 0, 200] | [-650, 0, 400] | [-1000, 0, 0] |
| `StateFreeCameraSitOffsetMax` | 12 | [-500, 0, 200] | [-800, 0, 400] | [-300, 0, -200] |
| `UseStateFreeCameraSitOffsetUp` | 24 | true | true | false |
| `StateFreeCameraSitOffsetUp` | 28 | [-1600, 0, 1400] | [-900, 0, 2800] | [0, 0, 0] |
| `StateFreeCameraPullOffset` | 40 | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] |
| `CameraPivotOffset` | 52 | [0, 0, 5] | [400, 0, 5] | [-100, 0, 700] |
| `ZoomedOffset` | 64 | [50, 0, -30] | [50, 0, -30] | [50, 0, -30] |
| `maxPitch` | 76 | 6000 | 6000 | 14500 |
| `MinPitch` | 80 | -14000 | -8000 | -14000 |
| `MinFreeCameraDistance` | 84 | 1000 | 1000 | 400 |
| `MaxFreeCameraDistance` | 88 | 1000 | 1000 | 400 |
| `ShortCamSpringConst` | 92 | 24 | 24 | 24 |
| `LongCamSpringConst` | 96 | 8 | 8 | 8 |
| `DefaultCameraPitch` | 100 | 0 | 0 | 0 |
| `CameraSitOffsetPower` | 104 | 1.25 | 1.5 | 1 |
| `CameraSitOffsetMin` | 108 | 16384 | 16384 | 16384 |
| `CameraSitOffsetMax` | 112 | 5000 | 16384 | 16384 |
| `bUseSeparate43Settings` | 116 | false | false | false |
| `StateFreeCamera43SitOffsetMax` | 120 | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] |
| `StateFreeCamera43SitOffsetMin` | 132 | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] |
| `StateFreeCamera43SitOffsetLookUp` | 144 | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] |
| `bDontModifySitOffsetWhenLookingUp` | 156 | false | false | false |
| `MinCameraSmoothingAngle` | 160 | 10 | 10 | 10 |
| `MaxCameraSmoothingAngle` | 164 | 10 | 10 | 10 |

The F-8 column is **new**: the first pass recorded only `StateFreeCameraSitOffsetMin [-350, 0, 200]`
from the tag's first bytes and did not decode the rest. Units: the three vectors are cm (UE3 length
unit, the same convention `MODES.md` carries for these fields); `maxPitch`/`MinPitch` stay
"as shipped" (see U-1).

Provenance class: `decoded` (cooked property tags, `BmGame.upk` export 34970, `image+0x1239eda`).
Routes tried this pass: (a) class default object — **found**; (b)/(c)/(d) not needed, a file value
wins (R4).

## F-9 … F-16 — the first pass stands, byte for byte

**STATUS: FOUND** for all eight, unchanged values, now with the payload bytes attached. Routes tried
this pass: re-derivation (fresh walk of the same package, decode independent of the walker), plus the
routes below for the two UNKNOWNs. What the second pass adds per row is evidence, not a new number:

| row | tag | payload bytes (hex) | decoded |
|---|---|---|---|
| F-9 | StructProperty @0x3e9c, image+0x1239ff8, 266 B | `0b 00 00 00 00 80 22 c4 …` | see table above (matches chase-02) |
| F-10 | StructProperty @0x3f44, image+0x123a116, 266 B | `0b 00 00 00 00 00 7a c4 …` | see table above (matches chase-02) |
| F-11 | FloatProperty @0x4fd0, image+0x123bbd8 | `00 00 70 42` | 60.0 |
| F-12 | FloatProperty @0x4fd4, image+0x123bbe0 | `00 00 70 42` | 60.0 |
| F-13 | VectorProperty @0x4fdc, image+0x123bbf0 | `00 00 00 00 00 00 00 00 00 00 16 43` | [0, 0, 150] |
| F-14 | VectorProperty @0x4ff8, image+0x123bc00 | `00 00 00 00 00 00 00 00 00 00 96 43` | [0, 0, 300] |
| F-15 | RotatorProperty @0x5034, image+0x123bc20 | `dc 05 00 00 00 00 00 00 00 00 00 00` | [1500, 0, 0] |
| F-16 | FloatProperty @0x11e4, image+0x1022d6d | `00 00 40 3f` | 0.75 |

`0x05dc` = 1500 and `0x4316` = 150.0 and `0x4396` = 300.0 are the little-endian encodings, so the
numbers above can be checked with a hex editor at the named image offset.

Provenance classes: `decoded` (F-15's degree figure `derived`, as chase-02 already recorded).

Two cross-checks this pass did not exist in the first pass:

1. **No duplicate tag at any of the nine offsets** — the script counts tags per offset and would have
   failed the row (`WARNING: >1 tag at this offset`); zero warnings, so the value at each offset is
   unambiguous and not a neighbour.
2. **No ini file sets any of them** — see route (a) below. `chase-02.md` inspected `BmCamera.ini`
   only; this pass grepped every ini in the install.

## Route (a), second half: every package and every ini, not just `BmGame.upk`

**Ini / coalesced config — 0 hits.** Every member name, BmGame + Engine + all 18 GB of DLC:

```
$ grep -rn -i -E "BattleModeCamFOV|BattleModeHeadOffset|BattleModeWinch|BattleModeAbseiling|StrafeCooldown|BattleModeCamConfig" --include="*.ini" .
(no output)
$ grep -rn -i "R3rdPersonCamera\|RVehicleBatmobileBase" --include="*.ini" BmGame/Config Engine/Config DLC
BmGame/Config/BmCamera.ini:1:[BmGame.R3rdPersonCamera]
BmGame/Config/DefaultCamera.ini:1:[BmGame.R3rdPersonCamera]
```

Only the class section exists, and it sets `EnableCameraAssist=True`; no member is configured, so no
load-time override exists. The section name `[BmGame.R3rdPersonCamera]` is also the reason the native
route cannot see these fields — the class is **packaged script**, not an Engine native class.

**Packages — no subclass default anywhere.** Two independent checks:

```
$ python Tools/scripts/chase/chase2_packages.py scan \
    --packages "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/BmGame.upk"
BmGame.upk: 2975 Default__ exports, 2 carry a card offset
   Default__RVehicleBatmobileBase (export 10923): [{'offset': 4580, ... 'value': 0.75}]
   Default__R3rdPersonCamera (export 34970): [ ... all eight, values as above ]
```

(2975 is every `Default__` object in the package, not the 235 name-filtered ones the first pass
scanned — the answer is the same, so the name filter hid nothing.)

```
$ python Tools/scripts/chase/chase2_packages.py sweep --root ".../DLC" --json chase2_sweep_dlc.json
swept 879 packages, 6.56 GB in 191s (34 MB/s); 1 package(s) carry a needle
  HIT DLC/350171/Content/BmGame/CookedPCConsole/GlobalPersistentCookerData.upk
```

That one hit is the DLC cook **manifest**, not a definition: 4,832 distinct `Default__*` strings,
8 occurrences of `Default__R3rdPersonCamera`, and the tool refuses to parse it as a package
(`not chunked and the name table is not where the header says`) because it is a name list.

The base game ships the same manifest, and it is the cheapest complete inventory of the cook:

```
$ python - <<'EOF'  (scan BmGame/CookedPCConsole/GlobalPersistentCookerData.upk for Default__ names)
manifest size 109,590,691  Default__ names: 4911
-- Default__ *Camera*: 80          (exactly ONE is R3rdPersonCamera)
-- Default__ *Batmobile*: 85       (RVehicleBatmobile, RVehicleBatmobileBase, RVehicleNPCBatmobile,
--                                  RVehicleSimBatmobile)
-- Default__ *SVehicle*: 5         -- Default__ *RVehicleSim*: 6
EOF
```

**No `Default__R3rdPersonCamera_<anything>` exists in the shipped game**, so no subclass default
overrides F-8 … F-15 anywhere; and the Batmobile's own vehicle defaults (chase-03/04/06/07) are the
only `RVehicleBatmobileBase` ones. Coverage limit: the DLC sweep read `.upk` files (879 / 6.56 GB);
BmGame's remaining 3,000+ packages were **not** streamed in this pass (the attempt ran at ~34–47 MB/s
and was cut off at 3.4 GB), so the completeness claim above rests on the manifest inventory, which
lists cooked object names game-wide, plus the BmGame.upk scan.

## Route (b): native code — no site exists, and that is the answer

`chase04_native.py` finds *store* forms; it reported 0 for every offset in the first pass's set.
This pass searched the **load** forms too, and every flattened offset (`struct base + member`) plus
the three struct bases:

```
$ python Tools/scripts/chase/chase2_native2.py
BatmanAK.exe: 55,101,440 bytes, image base 0x140000000, .text raw 0x400..0x1958e00
-- BattleModeCamConfig.maxPitch @ 0x3e40: 0 load/store site(s); 0 raw occurrence(s) in .text
-- BattleModeCamConfig.MinPitch @ 0x3e44: 0 load/store site(s); 0 raw occurrence(s) in .text
-- BattleModeWinchCamConfig.maxPitch @ 0x3ee8: 0 load/store site(s); 0 raw occurrence(s) in .text
-- BattleModeAbseilingCamConfig.maxPitch @ 0x3f90: 0 ... ; 1 raw occurrence(s)   (stack frame, not a field)
-- BattleModeCamFOV @ 0x4fd0: 0 load/store site(s); 0 raw occurrence(s) in .text
-- BattleModeCamFOV(Winch) @ 0x4fd4: 0 ... ; 2 raw occurrence(s)
-- BattleModeCamConfig base @ 0x3df4: 0 ... ; 2 raw occurrence(s)
...(17 displacements in total: 0 instruction sites)
```

The raw byte matches that do exist are **not instruction displacements**: for each one the script
disassembled back up to 11 bytes, required the instruction to end exactly at the displacement and to
carry `mem.disp == offset`, and printed the match; all 52 at 0x3f98 for example are
`mov qword ptr [rbp + 0x3f98], r10` / `mov r10, qword ptr [rbp + 0x3f98]` pairs inside one
function's stack frame (0x140805931, 0x14080595b), not a camera field. So the
executable never names these offsets: `R3rdPersonCamera` is script-side (see the ini section name)
and its members are reached through the UE3 property objects, whose `Offset` is data.

## U-1 · unit of `maxPitch` / `MinPitch` — STILL UNKNOWN

**STATUS: STILL UNKNOWN (the unit).** The values are `decoded`: 6000 / −14000 (F-8), 6000 / −8000
(F-9), 14500 / −14000 (F-10), all FloatProperty, bytes `00 80 bb 45` (6000.0), `00 c0 5a c6`
(−14000.0), `00 00 fa c5` (−8000.0), `00 90 62 46` (14500.0).

Routes tried this pass:

| route | result |
|---|---|
| (a) class default object | value found (above); the tag is a bare `FloatProperty`, no enum, no unit |
| (a) ini / coalesced config | 0 hits for `maxPitch`/`MinPitch` in every ini incl. DLC |
| (a) every other default object in `BmGame.upk` | `Default__RVehicleSimBatmobile` etc. carry no such member; the struct is the only place |
| (b) native code | **no site exists** to read a scale constant from: 0 instruction displacements for 0x3e40/0x3e44/0x3ee8/0x3f90 and for the flattened `MinFreeCameraDistance` offsets except coincidental stack frames |
| (d) published sources | not consulted for a unit; no URL in the repo states it |

What is *not* claimed: the self-consistent reading is rotator units (6000 × 360/65536 = 32.96 deg,
−8000 = −43.95 deg, 14500 = 79.65 deg, −14000 = −76.90 deg), which would make these ordinary camera
pitch clamps, while the same numbers in degrees would be meaningless. That is an **inference**, not
evidence — no file, ini, or code constant states it — so per R4 it stays out of the build and the
field keeps `undocumented` in `MODES.md`. F-15's degree conversion is unaffected: that field is a
`RotatorProperty`, where 65536-per-revolution is the encoded type, not a guess about a float.

To close it, one of these would have to appear: a shipped ini/code site that scales the field, or a
capture where the pitch clamp is measured against a known angle. Neither exists on this machine.

## U-2 · does anything write `BattleModeCamFOV` at runtime — STILL UNKNOWN

**STATUS: STILL UNKNOWN.** The configured value is 60.0 deg (F-11/F-12, decoded). Whether a speed-FOV
or battle-mode transition changes it *at play time* is not in any file read here.

Routes tried this pass:

| route | result |
|---|---|
| (b) native store sites for 0x4fd0 / 0x4fd4 | 0 instruction sites (store *and* load forms, `chase2_native2.py`) |
| (a) any other default object overriding it | 0 — the 2,975 `Default__` objects of `BmGame.upk` contain exactly two carriers, and neither is another camera |
| (a) manifest inventory | exactly one `Default__R3rdPersonCamera`, no subclass default |
| (a) ini | 0 hits |
| (c) captures | not attempted: FOV is not measurable from pixels without a calibrated target, and no capture holds one; a frame-timed read would be a guess dressed as a measurement |

The honest reading of the negative: **native code cannot change it** (no reference exists), so a
runtime writer would have to be UnrealScript bytecode inside a cooked package. This pass did not
decode script bytecode, and the install ships no `.u` script packages to read (the cook holds only
`.upk`, `.tfc`, `.bin`), so that route stops here rather than failing. No number is claimed.

## Limits of this pass

1. `BmGame.upk`'s remaining ~3,000 packages were not streamed (see route (a)); the DLC sweep covered
   879 packages / 6.56 GB. The completeness claim for "no overriding default" therefore rests on the
   game-wide cook manifest (4,911 `Default__` names) plus the full `BmGame.upk` default scan.
2. Only `BatmanAK.exe` `.text` was searched for the offsets; the shipped DLLs are third-party
   (APEX, PhysX, GFSDK, EasyHook) and hold no game class layout. No DLL was searched for script.
3. Script bytecode (the only remaining writer for U-2) was not decoded — a separate card.
4. No capture was used and no published source was consulted for a number; every value above is a
   file value, so footage could not override them (R4).
5. `chase-02.md`'s and this file's addresses are image offsets inside the decompressed package, not
   on-disk file offsets (see the label note); the on-disk bytes differ because the package is
   chunk-compressed.

## Files

- `Tools/scripts/chase/chase2_verify.py` — re-derivation + F-8; `--check` exits non-zero on a DIFF.
- `Tools/scripts/chase/chase2_native2.py` — load/store site search in `.text`, disassembly context,
  RIP-relative float resolution.
- `Tools/scripts/chase/chase2_packages.py` — `sweep` (streaming name search) and `scan` (default
  objects carrying the card offsets).
- `E:/Modding/ArkhamKnight/_grab/chase/chase2_verify.json`, `chase2_native2.json`, `chase2_sweep_dlc.json`.

`FOOTAGE.md`, `chase-02.md`, `GRAB_BACKLOG.md`, `MODLOG.md` and every other existing document were
**not edited** (card rule); nothing was launched, patched, committed, or written under `D:/Games` or
`E:/Games`, and no secret is in this file.
