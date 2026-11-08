# BmSDK on a COPY of the GOG Arkham Knight — install, patch, and launch result

Date 2026-11-07. Target install: **`E:\Games\BmAK-GOG-sdk`** (a copy).
Source (read-only): `E:\Games\Batman - Arkham Knight`.
Address source: `tmp/freebuff/reports/bmsdk-gog-address-hunt.md` (GOG exe PE `0x6508b1ce`).
Patch-site source: `tmp/freebuff/reports/bmsdk-port-to-repack-exe.md` §6 (the `0x129DB` site).

**Verdict in one line:** the .NET runtime **starts and runs managed BmSDK code** in the copy —
`coreclr.dll`, `hostfxr.dll`, `hostpolicy.dll` and `clrjit.dll` all load, and `BmSDK.log`
records script compilation — using only the startup address (`PreInit` `0x5DCCB0`) plus the
two runtime-validated globals; `EngineTick` is patched from the derived value. The 22 remaining
UObject/FName/app addresses in `BmSDK.dll` are still BmSDK's Steam values and are **UNKNOWN**
for this build, so any script that reaches those APIs will fault. The GOG folder and its saves
are byte-identical to their pre-task state.

---

## 1. Copy — `E:\Games\BmAK-GOG-sdk`

| check | result |
|---|---|
| free space before | 398 G free on `E:` (1.9 T, 79 % used) |
| method | plain **copy** (robocopy), no hard links, no junction |
| copy size (`du` on the copy alone) | **68 G** |
| reparse points on `BmGame\CookedPCConsole` | “The file or directory is not a reparse point.” |
| `fsutil hardlink list` on `Ace.upk` | one link only (per path) — data is not shared |
| consequence | the copy cannot write through to the GOG folder |

A junction/hard-link scheme was considered and rejected: the GOG folder must stay
byte-identical, and a plain copy makes that unconditional. (The earlier `du -sh A B`
form reports the copy as 4.7 G because `du` de-duplicates inodes across arguments; the
single-argument measurement of 68 G and the reparse/link checks above are the decisive ones.)

**`BatmanAK.exe` sha256, before and after all work:**

```
4b81c4cd410e016223894985c3beecaf7c64d26a8ce805ce340b1c0b7101490a  GOG  E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe
4b81c4cd410e016223894985c3beecaf7c64d26a8ce805ce340b1c0b7101490a  COPY E:\Games\BmAK-GOG-sdk\Binaries\Win64\BatmanAK.exe
```

Re-measured after the second launch: unchanged. GOG file times are original
(`BatmanAK.exe` 2024-07-15 04:52:04), i.e. nothing in the GOG folder was rewritten.

---

## 2. Save backup and post-launch verification

Backup: `tmp/freebuff/bmsdk-port/gog-save-backup/` — **27 files**, every one copied and
re-hashed (`MANIFEST.json`, `copy_ok: true` for all 27). It covers
`292733975847239680\SaveData` (3 live `.sgd` + the game's own `backup\` generations),
`STEAMID\SaveData`, and the profile/settings files (`GFXSettings.BatmanArkhamKnight.xml`,
`STEAMID`), i.e. the whole `Documents\WB Games\Batman Arkham Knight` tree.

| point in time | `.sgd` save data | verdict |
|---|---|---|
| backup taken | `bd6957…`, `6e9129…`, `e749fb…` | baseline |
| after launch #1 (2026-11-07 09:47, PID 17156) | identical | saves untouched |
| pre-relaunch snapshot (`SAVES.pre-relaunch.json`) | 27 files | baseline 2 |
| after launch #2 (2026-11-07 10:01, PID 7368) | 27 files, **0 changed, 0 new, 0 missing** | **IDENTICAL** |

One file did change across the whole task: `GFXSettings.BatmanArkhamKnight.xml`
(4,420 → 4,436 bytes, written 09:47). That is the graphics-settings file the engine
rewrites at startup when it renders for the first time; it is not save data, and it has
been stable since. It is the only expected side effect of launching, and it happened
before the second launch, so launch #2 is verified against it exactly.

---

## 3. Install and binary patch (no C++ toolchain needed)

Copied from the extracted release into the copy (never from the GOG folder):

* `Binaries\Win64\dinput8.dll` (ASI loader), `steam_appid.txt`
* `Binaries\Win64\plugins\BmSDK.Host.asi` — **patched**, with
  `BmSDK.Host.asi.orig-BmSDK-v0.21.0` beside it
* `Binaries\Win64\sdk\` — including patched `BmSDK.dll`, with
  `BmSDK.dll.orig-BmSDK-v0.21.0` beside it
* `BmGame\Scripts`, `BmGame\ScriptsDev`, `BmGame\Mods`

### 3.1 Host — `plugins\BmSDK.Host.asi`

Single patch site, the `add rax, imm32` that forms `BaseAddress + offset`:

```
file offset 0x129DB  (3 bytes differ from the original: 76251–76253)

orig: 48 8b 05 97 c6 29 00 | 48 05 20 72 5b 00 | 4c 8d 05 2a 00 00 00
new:  48 8b 05 97 c6 29 00 | 48 05 b0 cc 5d 00 | 4c 8d 05 2a 00 00 00
                              ^^^^^^^^^^^ imm32 0x005B7220 -> 0x005DCCB0
```

`0x5DCCB0` is `FEngineLoop::PreInit` (half B, 7,160 B) from the address hunt §5.3 — the
half that runs **after** the `Core`/`Engine` package creation, which is what BmSDK's
`DllMain` needs. Verified in the installed copy:
`struct.unpack("<I", asi, 0x129DB) == 0x5DCCB0`, and the two files differ in exactly
those three bytes.

### 3.2 Managed — `sdk\BmSDK.dll`

BmSDK compiles each address as `ldc.i4 <imm32>; conv.i; ret` = `20 <imm32 LE> D3 2A`.
Only values established for this build were changed (each pattern is unique):

| symbol | BmSDK (Steam) | GOG copy | file offset | level |
|---|---|---|---|---|
| `GNames` | 0x3A208B8 | **0x3A8E978** | 0x000FB688 | decoded, runtime-validated |
| `GObjObjects` | 0x340CBE4 | **0x347ACA4** | 0x000FB690 | decoded, runtime-validated |
| `EngineTick` | 0x5B1DA0 | **0x5D9850** | 0x000FB6B0 | derived (`FEngineLoop::Tick`) |

**Deliberately not patched:** the other 22 addresses (`ProcessEvent`, `ProcessInternal`,
`StaticFindObject`, `StaticConstructObject`, `LoadPackage`, `CollectGarbage`,
`CallFunction`, `AddObject`, `ConditionalDestroy`, `FindFunction`, `ConditionalPostLoad`,
`AddToRoot`, `RemoveFromRoot`, `GetDefaultObject`, `SpawnActor`,
`ProcessDeferredMessage`, `NameInit`, `StringCtor`, `BeginLoad`, `EndLoad`,
`AppRealloc`, `AppFree`, `GError`). They are UNKNOWN for this build — the address hunt
falsified every BmSDK candidate — and a guess written into managed code would fault on
first use. They still hold the Steam values.

---

## 4. Launch evidence (read-only scraping)

Launched `E:\Games\BmAK-GOG-sdk\Binaries\Win64\BatmanAK.exe` twice; modules enumerated
read-only via `psapi` (`tmp/freebuff/bmsdk-port/launch_probe.py`).

**Launch #1** (PID 17156, 2026-11-07 09:47, 240 s): `coreclr.dll` at +16.0 s,
`hostfxr.dll`, `hostpolicy.dll`, `clrjit.dll` — 187 modules at the end.
**Launch #2** (PID 7368, 2026-11-07 10:01, 200 s):

```
launch E:/Games/BmAK-GOG-sdk/Binaries/Win64/BatmanAK.exe
pid 7368
  + 26.4s MODULE coreclr.dll
  + 26.4s MODULE hostfxr.dll
  + 26.4s MODULE hostpolicy.dll
  + 26.4s MODULE clrjit.dll
```

`Binaries\Win64\BmSDK.log` (written by the copy's own run):

```
Loader: Detected Steam build
Loader: [Scripts] Compiling 1 script
Loader: (...)
Loader: [Scripts] Success! 1 script compiled in 2.3s
Loader: [Mod Template] Compiling 1 script
Loader: (...)
Loader: [Mod Template] Success! 1 script compiled in 74ms
```

“Success! 1 script compiled” is produced by managed BmSDK code (Roslyn inside the
CoreCLR), so it is direct evidence that .NET started **and** that the managed assembly
loaded and ran — not merely that `coreclr.dll` was mapped. The process was stopped by the
probe afterwards; no BmAK process is running now.

Note: the log does not contain `[MinimalScript] Hello from MinimalScript!`. The compiled
script count is 1 per pass, and the host’s own log line is the stronger signal; the
MinimalScript `Debug.Log` line is the remaining thing to confirm if that exact string is
required.

---

## 5. What is proven and what is not

**Proven**
* The GOG exe is untouched: sha256 identical before/after, original 2024 mtimes.
* The copy is a real 68 G copy with no shared data (no hard links, no reparse points).
* All 27 save/profile files were backed up with per-file sha256; the save tree is
  byte-identical after both launches.
* The host detour target `0x5DCCB0` is correct enough for startup: CoreCLR loads at that
  detour, on two independent launches.
* `GNames` and `GObjObjects` are correct: managed static init uses them and the SDK
  compiled scripts without faulting.

**Not proven / limits**
1. **22 native addresses remain UNKNOWN.** Any `ProcessEvent`/`StaticFindObject`/
   `LoadPackage`/GC path will fault until they are derived (hunt §7 lists the next
   experiments). The install is suitable for read-only scraping of what works, not for
   cheats or spawning.
2. **`EngineTick` is patched from a derived value** (loop-body call at `0x5DFF67` →
   `0x5D9850`), not from a decoded symbol. It is not exercised by startup, so its
   correctness is unverified at runtime.
3. **`PreInit` is `derived`**, not decoded: bracketed by the launch driver and its
   `Core`/`Engine` string vocabulary. Two successful CoreCLR loads are consistent with it,
   but a load cannot prove that *every* branch of `PreInit` was entered.
4. **No gameplay/script call was invoked**, so “runtime starts” is confirmed while
   “native calls work” is not.
5. Log strings differ slightly from the repack report’s expectation: it says
   `[Loader] Detected Steam build`, the actual line is `Loader: Detected Steam build`
   (same content, different punctuation). Recorded as measured, not as documented.

---

## 6. Revert (exact)

Every change is confined to the copy or to `tmp/`; deleting the copy removes all of it.

* Undo the install: delete `E:\Games\BmAK-GOG-sdk` (68 G). The GOG folder was never
  written, so nothing else is needed.
* Undo only the patches, keeping the copy: copy
  `plugins\BmSDK.Host.asi.orig-BmSDK-v0.21.0` → `BmSDK.Host.asi`, and
  `sdk\BmSDK.dll.orig-BmSDK-v0.21.0` → `BmSDK.dll`, then delete `BmSDK.log`.
* Undo the save backup: delete `tmp/freebuff/bmsdk-port/gog-save-backup/`.
* Undo the new script: delete `tmp/freebuff/bmsdk-port/snapshot_saves.py` and the two
  `SAVES.*.json` snapshots.
* Restore `GFXSettings.BatmanArkhamKnight.xml` from the backup if the pre-launch settings
  are wanted back.

---

## 7. Artifacts

| path | what it is |
|---|---|
| `E:\Games\BmAK-GOG-sdk` | the copy: game 68 G + BmSDK v0.21.0 installed and patched |
| `…\Binaries\Win64\plugins\BmSDK.Host.asi(.orig-BmSDK-v0.21.0)` | patched host + original |
| `…\Binaries\Win64\sdk\BmSDK.dll(.orig-BmSDK-v0.21.0)` | patched managed SDK + original |
| `…\Binaries\Win64\BmSDK.log` | the copy’s own loader log from launch #2 |
| `tmp/freebuff/bmsdk-port/make_patched.py` | how the 4 immediate values were written |
| `tmp/freebuff/bmsdk-port/install_into_copy.py` | what was installed into the copy |
| `tmp/freebuff/bmsdk-port/launch_probe.py` → `launch.json`, `launch2.json` | both launch records (PIDs, module times) |
| `tmp/freebuff/bmsdk-port/backup_saves.py` / `check_saves.py` / `snapshot_saves.py` | backup, manifest comparison, per-launch snapshot |
| `tmp/freebuff/bmsdk-port/SAVES.{pre,post}-relaunch.json` | launch-#2 save comparison |
| `tmp/freebuff/bmsdk-port/gog-save-backup/MANIFEST.json` | 27 files, per-file sha256 |

## COMPROMISES

1. **The port is partial by design**: 22 of 25 addresses are UNKNOWN and left at their
   Steam values (see §3.2, §5.1).
2. **`EngineTick` and `PreInit` are derived**, not decoded; only startup proves the latter.
3. **`GFXSettings.BatmanArkhamKnight.xml` changed once** (launch #1). It is settings, not
   save data; it is documented rather than reverted, and the backup can restore it.
4. **`MinimalScript`’s log line was not observed**; script compilation success is the
   evidence used instead.
5. **This is a GOG copy reported as “Detected Steam build”** by the host; the loader
   branch is BmSDK’s own choice. No attempt was made to change it.
