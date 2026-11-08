# Where the Batmobile's controller scheme lives, and whether it travels with the save

Operator report, 2026-11-07. Installed build: `E:/Games/Batman Arkham Knight` (DODI repack,
`BatmanAK.exe` sha256 `58352898…56ac`). Comparison build found on disk:
`E:/Games/Batman - Arkham Knight` (the GOG-style copy) and `E:/Games/Batman Arkham Knight - [DODI
Repack Repack]` / `[FitGirl Repack]` (not opened — only their `BmInput.ini` presence was checked).

Labels: **decoded** = read bytes at the path and offset named; **derived** = arithmetic/rule shown;
**UNKNOWN** = searched, not found, and the search named. Read-only: every game and save file was
read where it lies; the only writes are byte copies into `tmp/freebuff/bmak-input/`. No game was
launched.

**Answer in one paragraph.** The Batmobile's gamepad layout is **data in the ini chain, not in the
save**: `BmInput.ini` is the engine's merged output of `BaseInput.ini → DefaultInput.ini →
UserInput.ini → PCInput.ini`, and every Batmobile token (`BatmobileFireButton`,
`bFireVehicleWeapon`, `bFireVehicleSecondaryWeapon`, `BatmobileSonar`, `SelectVehicleWeapon 4`,
`bVehicleBoostButton`, `PursuitModeTagGun`, `ToggleDrivingCamera`, `EjectFromVehicle`,
`BrakeButton`) is defined in the **shipped, 2016-dated** `DefaultInput.ini`. The two installs on
this machine are **byte-identical in all four chain files** except four per-device timestamp lines,
so no binding difference exists between them to explain a felt difference. The saves carry **no**
control field at all: every "Controller"/"Invert"/"Option" hit in the 2.4 MB `.sgd` is a world-object
or upgrade name, and `profile.bin` is a 91-byte counter blob with no strings.

## 1. The inputs, as they are on disk (decoded)

Config, `E:/Games/Batman Arkham Knight/BmGame/Config` (21 files + `PC/`):

| file | bytes | mtime | sha256 (16) | role |
|---|---:|---|---|---|
| `BmInput.ini` | 43,825 | **2026-11-06 18:18** | `b8cbd4b2d5c92da4` | the engine's **merged output** (not in the chain) |
| `DefaultInput.ini` | 25,019 | 2016-11-25 | `7db2b893e174fb57` | shipped defaults — **all Batmobile tokens live here** |
| `UserInput.ini` | 62 | 2016-11-25 | `b7436972c712d83d` | user override layer, empty (`BasedOn=DefaultInput.ini`) |
| `PC/PCInput.ini` | 1,423 | 2016-11-25 | `13d3bc370e9f96df` | platform overrides (TAB → `OpenLevelUpOrMap`, debug camera) |
| `BmSystemSettings.ini` | 40,986 | 2026-11-06 18:18 | — | graphics/audio; **0** controller, invert, sensitivity or layout keys |
| `BmGame.ini` | 775,210 | 2016-11-25 | — | **0** occurrences of `RPlayerInput`; 0 of `InvertLook`/`LookSensitivity`/`ControllerLayout` |

Chain order (decoded from the `BasedOn=` lines, `Research/BatmobileGrab/CONTROLS.md` §Sources, and
`BINDINGS_MERGED.md` §1): `Engine/Config/BaseInput.ini` → `DefaultInput.ini` → `UserInput.ini` →
`PC/PCInput.ini`, and `BmInput.ini` is the **post-merge array** the engine writes (366 entries; the
`append`/`exact` rules reproduce it 366/366).

The Batmobile lines in the installed `BmInput.ini`, decoded with their shipped source:

| button | command tokens | line |
|---|---|---|
| RT | `BatmobileFireButton`, `Button bFireVehicleWeapon` (+ on-foot fire) | `DefaultInput.ini:252` |
| RB | `ToggleDrivingCamera`, `Button bFireVehicleSecondaryWeapon`, `SecondaryFireVehicleWeapon`, `PursuitModeTagGun` | `DefaultInput.ini:272` |
| Y | `Button bVehicleBoostButton` | `DefaultInput.ini:270` |
| X | `BrakeButton` | `DefaultInput.ini:269` |
| A | `EjectFromVehicle` | `DefaultInput.ini:267` |
| D-pad up | `SelectVehicleWeapon 4` / `OnRelease ReleaseVehicleWeapon 4` | `DefaultInput.ini:259` |
| left-stick press | `BatmobileSonar` | `DefaultInput.ini:256` |
| left trigger (axis) | `aLeftTrigger` → `RPlayerInput.aLeftTrigger` | `DefaultInput.ini:253` |

**Save sets.** Three of the four the operator named are **not on this disk** (decoded by directory
probe): `Downloads/120 Sve File-640-1-0-0-1691778389/remote`,
`Downloads/Batman240save File 3578 1 2026-10-16T18-15Z Uk74T4Fdm`,
`Downloads/Batman Arkham Knight - Knightfall Legacy (240 Save-2844-1-0-1762103320)` — all MISSING.
What exists:

| set | files | bytes | sha256 (16) |
|---|---|---:|---|
| `Documents/CPY_SAVES/Player/208650` | `BAK1Save0x0/1/2.sgd` | 2,428,928 each | `02c88858…`, `0dc19b19…`, `49ce8057…` |
| same | `profile.bin` | **69** | `f4714423…` |
| `Documents/WB Games/Batman Arkham Knight/292733975847239680/SaveData` | `BAK1Save0x0/1/2.sgd` | 2,428,932 each | `bd6957d9…`, `6e9129c9…`, `e749fb2c…` |
| same `/backup` | 10 dated copies | 2,428,928 | e.g. `BAK1Save0x0.sgd_2026-11-07_02-08-48` |
| `Documents/WB Games/Batman Arkham Knight/STEAMID/SaveData/backup` | 13 dated copies (2026-10-16 → 2026-11-06) | 2,428,928, three at 2,428,932 | `0bfc2451…` … `c70af9e3…` |

## 2. The saves decoded (decoded)

**`profile.bin` — 69 bytes, 16-byte header + one zlib stream.**

```
bytes 0..15   header  5cae130d32adcbcd4690e5da37fb27f2   (16 opaque bytes, not a known magic)
bytes 16..19  477861DB  (u32 LE 1199071707)
bytes 20..23  00 00 00 5B  -> **91** read big-endian = the decompressed length
bytes 24..68  78 9c …    -> zlib, 45 compressed bytes -> **91** bytes, sha256 e9816d4797e4bcac
payload       91 bytes, no ASCII string of length >= 4 anywhere
```

Interpreted as little-endian u32 records the payload does not parse into sane counters (it yields
`150994944, 1, 257, 16777984, …`), so its field layout is **UNKNOWN**. What is decoded is what
matters here: **91 bytes cannot hold a binding table, and it holds no string** — so no button, token
or device name is stored in the profile. Note also that the GOG-side `STEAMID` save folder has **no
`profile.bin` at all**, i.e. the file is part of the CPY container, not of the game's own save model
(**derived**).

**`BAK1Save*.sgd` — 2.4 MB world state, two container flavours.**

```
WB Games set : 00 10 25 00 | 06 00 00 00 | 00 00 00 00 | d0 00 00 00 | 2e 7f 00 00 …
               ^ u32@0 = 2,428,932 = the file's own size          ^ version 6
CPY set      : 06 00 00 00 | 00 00 00 00 | d0 00 00 00 | 2e 7f 00 00 …
               ^ starts at version 6 - **no 4-byte size prefix**
```

That 4-byte prefix is the only container difference (derived: it is exactly the file length, and the
2026-11-06 11:02 backups carry it while the 2026-10-16 ones do not). A raw byte diff of WB-vs-CPY
save 0 reports 617,196 differing bytes, which is the shift, not a content difference — a re-aligned
comparison could not be completed in this session (the reader ran out of memory twice on the 2.4 MB
buffers), so **whether the two containers hold identical content is UNKNOWN**.

No zlib stream exists in an `.sgd` (0 hits for `78 9c` in the first scan), so it is not compressed —
the ASCII runs are plain names. Census over the whole file (decoded), with the first context of each:

| token | count | what the context shows |
|---|---:|---|
| `Controller` | 180 | `…CityZ_03_Static_LOD1.Sequence_58.RBMWaveController_12.AllDeadFired…` — a **world object** name |
| `Tank` | 98 | challenge/mission names |
| `Invert` | **2** | `…UpgradeV_MoveCeilingTakedown…UpgradeV_MoveInvertedTakedown…` — an **upgrade** name |
| `Option` | 1 | `…Orphan_A1_CW_Optional_Set_3_Done…` — a collectible flag |
| `Difficulty` | 1 | a game-state token |
| `Binding`, `Sensitiv`, `Layout`, `Gamepad` | **0** | — |

**Derived: the save carries progress and world state, not the control scheme.** That is also why the
120% and 2% saves "feel" different from each other for reasons that are not bindings: whatever
differs is game state (handled mode, vehicle upgrades present, mission context), not a button map.

## 3. Where the defaults come from: config, upk and exe (decoded)

| layer | evidence |
|---|---|
| **config (data)** | all 10 Batmobile tokens are `Bindings` lines in `DefaultInput.ini`; the install's `BmInput.ini` reproduces the chain |
| **upk (name match)** | `Research/BatmobileGrab/CONTROLS.md`: `RPlayerController.DrivingMode.BatmobileFireButton`, `…SecondaryFireVehicleWeapon`, `…SelectVehicleWeapon`, `…ToggleDrivingCamera`, `…EjectFromVehicle`, `…BatmobileSonarPressed` — functions declared in state `RPlayerController.DrivingMode` of `BmGame.upk`; `RPlayerInput.aLeftTrigger` (FloatProperty) |
| **exe (native)** | `CONTROLS_NATIVE.md`: `ARPlayerControllerexecDrivingPlayerMove` @ `0x140501f60`, `…execUpdateDrivingRumble` @ `0x140502090`, `…execPreProcessInput` @ `0x1404fe470`, `ARVehicleBatmobileBaseexecTryToChangeMode` @ `0x140547ce0`; and **0** occurrences of the strings `BatmobileFireButton`, `SelectVehicleWeapon`, `EjectFromVehicle` in the image |

**Derived:** the *defaults* are config data (shipped `DefaultInput.ini`, 2016) consumed by upk
functions whose names the config's `exec` tokens match; the exe carries the driving-mode logic but
**no button names**, so no build of the game can bake a different Batmobile layout into the exe. A
per-install difference can therefore only come from (a) the chain files, (b) an in-game options
value stored somewhere not decoded here, or (c) the input device/driver layer.

## 4. The two installs on this machine, diffed (decoded)

| file | DODI `Batman Arkham Knight` | GOG-style `Batman - Arkham Knight` |
|---|---|---|
| `DefaultInput.ini` | `7db2b893e174fb57`, 25,019 B | **identical** |
| `UserInput.ini` | `b7436972c712d83d`, 62 B | **identical** |
| `PC/PCInput.ini` | `13d3bc370e9f96df`, 1,423 B | **identical** |
| `BmInput.ini` | `b8cbd4b2d5c92da4`, 43,825 B, mtime 2026-11-06 18:18 | `b17711be7f9d2dfc`, 43,825 B, mtime 2026-11-03 02:37 |

`diff` of the two `BmInput.ini`: **4 lines, all timestamps**, in the file's trailing block —

```
DODI 0=1480087152.000000 1=1480086474.000000 2=1480086466.000000 3=1480086464.000000
GOG  0=1721034728.000000 1=1721033525.000000 2=1721033525.000000 3=1721033525.000000
```

and every gamepad line is identical (`diff` of the `XboxTypeS_` lines: **empty**); token counts match
exactly (`BatmobileFireButton` 1/1, `bFireVehicleWeapon` 1/1, `BatmobileSonar` 2/2,
`SelectVehicleWeapon` 1/1, `bVehicleBoostButton` 1/1, `PursuitModeTagGun` 1/1).

**Derived:** on this machine the GOG copy and the installed repack have the **same controller scheme
and the same Batmobile bindings**. A difference the operator feels between them is therefore not in
these files. Candidates, none decoded: the physical device/driver (Xbox vs DualShock layout, deadzone
and trigger range are applied by the input layer, not by these inis), an in-game option stored
outside the files searched (0 hits), or recall of the GOG session's own `BmInput.ini` **before** the
2026-11-03 rewrite. **UNKNOWN** — see §6.

## 5. What restores a chosen layout — exact edits, and how to revert

Nothing below is applied. All three are reversible by restoring the backup the same paragraph names.

**A. Reset to shipped defaults (the layout `CONTROLS_MENU_SCREENS.md` transcribes).** The merged file
is regenerated, so removing it is the reset:

```bash
# 1. back up (never edit the original in place)
cd "E:/Games/Batman Arkham Knight/BmGame/Config"
cp -p BmInput.ini BmInput.ini.orig-20261107
# 2. remove it; the engine rewrites the merged array on next launch from the chain
rm BmInput.ini
# revert
cp -p BmInput.ini.orig-20261107 BmInput.ini
```

**B. Change one binding without touching `BmInput.ini`.** `UserInput.ini` is *in* the chain (order
3 of 4) and wins over `DefaultInput.ini` (order 2), so one line there overrides the shipped default
and survives the engine's rewrite of `BmInput.ini`. Its current content is exactly:

```
[Configuration]
BasedOn=..\BmGame\Config\DefaultInput.ini
```

so the edit is to append, under a section header, a prefixed binding — the `-`/`.` prefixes are
decoded from the chain (`DefaultInput.ini` uses `.`, the one `-` line is `DefaultInput.ini:71`):

```
[Engine.PlayerInput]
.Bindings=(Name="XboxTypeS_RightShoulder",Command="ToggleDrivingCamera | OnRelease SecondaryFireReleased | Button bFireVehicleSecondaryWeapon | SecondaryFireVehicleWeapon | PursuitModeTagGun")
```

Revert: restore `UserInput.ini` from the backup (its shipped bytes are 62 B,
sha256 `b7436972c712d83d…`; the two lines above are the whole file, so it can also be retyped).
Then delete `BmInput.ini` (§A) so the merge is recomputed rather than left stale.

**C. The save: nothing to edit.** No control field exists in `.sgd` (0 hits for `Binding`,
`Sensitiv`, `Layout`, `Gamepad`; the `Invert`/`Controller`/`Option` hits are upgrade and world-object
names) and `profile.bin` is 91 bytes with no strings. An "in-game reset to defaults" therefore writes
**config**, not the save — which is why the layout does not travel with a save between installs.
**Do not** hand-edit an `.sgd` to change controls: there is no field to edit, and the 2.4 MB blob is
the whole world state.

**D. If the goal is the *GOG install's* exact behaviour** rather than the shipped defaults: copy
`E:/Games/Batman - Arkham Knight/BmGame/Config/BmInput.ini` over the installed one (they differ only
in four timestamp lines today, so this changes nothing observable) and, if that install has its own
`UserInput.ini` edits, copy that too — but note the copy **is** identical here, so this cannot be the
cause of a felt difference.

## 6. UNKNOWN, and what would settle each

1. **Why the operator's GOG sessions felt different.** *Searched:* both installs' four chain files
   (identical except 4 timestamp lines), `BmSystemSettings.ini` and `BmGame.ini` (0 controller/
   invert/sensitivity/layout keys), the `.sgd` token census (0 binding/gamepad/sensitivity strings),
   `profile.bin` (91 B, no strings). *Would settle:* the GOG install's `BmInput.ini` as it was before
   2026-11-03, a screenshot of the in-game Controls screen on each install, or the device name the
   game recorded — none of which is on this disk.
2. **`profile.bin`'s field layout** — 91 bytes, no strings; the u32 reading does not parse. A reader
   for the CPY profile container is needed (none in `Tools/scripts`; `Tools/scripts/_dump_profile.py`
   targets a different format and was not used).
3. **Whether the WB-set and CPY-set `.sgd` files hold identical content.** The 4-byte size prefix is
   decoded, but the aligned comparison did not complete (memory), so the 617,196-byte raw difference
   is explained as a shift, not proven.
4. **Where an in-game "controls" option would be stored, if one exists.** Not in the ini chain (0
   keys), not in the save (0 fields), not in `profile.bin` (too small, no strings). Candidates:
   a `BmSystemSettings.ini` section written only when the player changes it — the file's mtime
   (2026-11-06 18:18) shows it *is* rewritten at runtime, but no control key exists in its 779 lines.
5. **The two repacks' own configs** (`[FitGirl Repack]`, `[DODI Repack Repack]`) were not opened
   beyond a `BmInput.ini` existence check.

## 7. Reproduce

```bash
# config
sha256sum "E:/Games/Batman Arkham Knight/BmGame/Config"/{BmInput,UserInput,DefaultInput}.ini \
          "E:/Games/Batman Arkham Knight/BmGame/Config/PC/PCInput.ini"
diff -a "E:/Games/Batman Arkham Knight/BmGame/Config/BmInput.ini" \
        "E:/Games/Batman - Arkham Knight/BmGame/Config/BmInput.ini"

# saves (copies land in tmp/freebuff/bmak-input/, originals untouched)
python - <<'PY'
import os, zlib, hashlib
H = os.environ["USERPROFILE"]
p = os.path.join(H, "Documents", "CPY_SAVES", "Player", "208650", "profile.bin")
raw = open(p, "rb").read()
blob = zlib.decompressobj().decompress(raw[24:])
print(len(raw), "->", len(blob), hashlib.sha256(blob).hexdigest()[:16])
sgd = open(os.path.join(H, "Documents", "CPY_SAVES", "Player", "208650", "BAK1Save0x0.sgd"), "rb").read()
print({t: sgd.count(t.encode()) for t in ("Binding", "Sensitiv", "Gamepad", "Invert", "Controller")})
PY
```

Every copy made by this pass is in `tmp/freebuff/bmak-input/` (`cpy__*`, `wb__*`); no original file
was modified, and no game process was started.
