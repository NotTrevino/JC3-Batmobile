# BmSDK-AK port to the installed (repacked) Arkham Knight exe

Target: `E:\Games\Batman Arkham Knight\Binaries\Win64\BatmanAK.exe`
sha256 `58352898e8aedabe48cd14843865dcf0e697a066ce52c9913df726aa955656ac`, PE timestamp
`0x568ee584` (1452205444), 104,360,448 bytes. Measured, not quoted: file size and sha256
recomputed on 2026-11-06 (`tmp/freebuff/bmsdk-port/pe_probe.py`).

Installed SDK: BmSDK v0.21.0 (`Binaries\Win64\dinput8.dll`, `plugins\BmSDK.Host.asi`, `sdk\`,
`BmGame\Scripts`), source at `E:\Modding\_shared\tools\BmSDK-AK`.

**Verdict in one line:** the detour fails because `BaseAddress + 0x5B7220` is string data in *this*
exe, not code — the installed image is a repacked build whose code lives in `.text1` and is
decrypted at load, so none of BmSDK's 22 hard-coded addresses (code *or* globals) are valid here.
The equivalent `FEngineLoop::PreInit` could not be established to the standard this project
requires, so it is recorded as **UNKNOWN** with the exact falsification of every candidate
(`§5`). No game file was modified (`§7`).

Every number below is **decoded** (file/section/offset given), **derived** (rule + inputs) or
**UNKNOWN**.

---

## 1. What the installed exe actually is (decoded)

Read from the file with `pefile` and from the live process with `ReadProcessMemory`
(read-only; `tmp/freebuff/bmsdk-port/dump_mem.ps1`, `proc_probe2.py`).

```
machine 0x8664  imagebase 0x140000000  SizeOfImage 0x8C61000  entry 0x4260151
header entry point is inside .srdata, whose raw data is 0x200 bytes and whose runtime
page at that RVA is zero-filled => the header entry point is a decoy
```

| # | section | VA | vsize | rawsize | chars (disk) | content (measured) |
|---|---------|----|-------|---------|--------------|--------------------|
| 0 | `.link` | 0x00001000 | 0x0195C000 | 0x0195C000 | 0xE0000080 (RWX) | UTF-16 string/data blob |
| 1 | `.text` | 0x0195D000 | 0x01738000 | 0x01737800 | 0xC0000000 (RW) | live string/rodata blob |
| 2 | `.sdata` | 0x03095000 | 0x0105D000 | 0x000E3000 | 0x40000040 | globals + 16 MB BSS |
| 3 | `.pdata` | 0x040F2000 | 0x0016C000 | 0x0016B600 | 0x40000040 | valid unwind table |
| 4 | `.xdata` | 0x0425E000 | 0x00001000 | 0x00000200 | 0x40000040 | unwind payloads |
| 5 | `.bss` | 0x0425F000 | 0x00001000 | 0x00000400 | 0xE0000020 | |
| 6 | `.srdata` | 0x04260000 | 0x00001000 | 0x00000200 | 0x20000020 | |
| 7 | `.data1` | 0x04261000 | 0x00001000 | 0x00001000 | 0x40000040 | |
| 8 | `.text1` | 0x04262000 | 0x049A7000 | 0x049A7000 | 0x60000060 (RX) | code, **encrypted on disk** |
| 9 | `.xtext` | 0x08C09000 | 0x00057AC9 | 0x00057E00 | 0x40000040 | |

Section names 1, 3, 5 are literally `.text\0ta`, `.pdata\0a`, `.bss\0b` in the header
(8-byte name fields padded with junk) — the header was rebuilt by a packer.

Decisive measurements:

* `.pdata` parses as a clean `RUNTIME_FUNCTION[]`: **124,020** plausible triples
  (`begin < end < SizeOfImage`), monotonic, first `begin` **0x4262010**, last `end`
  **0x6078E00** (`pe_probe5.py`). The image's real code is therefore
  **0x4262000 … ~0x60E0000** — exactly `.text1`.
* `.text1` on disk: entropy **7.97**, head `e34a883e290e66b7…` (ciphertext).
* `.text1` in memory after load: head `ff252207e501 cccc… 90 4883ec28…` (an ILT thunk then a
  real prologue), **128,312** prologue-like byte sequences, entropy **7.66**
  (`compare_mem.py`). The packer decrypts `.text1` in place at load.
* `.text1` beyond **0x6162000** stays at entropy **8.00** with ~15 noise hits/MB and no `CC`
  padding even at runtime (`probe9_text1.py`): ~46.5 MB of the section is a second,
  still-encrypted payload that is never touched during startup.
* `.pdata` and `.link` are byte-identical in memory and on disk (100.00 % / 96.31 %), `.sdata`
  is 80 % different (runtime-initialised), `.text1` 62 % different (decrypted).
* The string blobs are real UTF-16 text: `.link` at RVA 0x5B6FBA is `EMPBlast`, the same string
  the operator saw through the `E9`.

So this is **not** the layout BmSDK was built for: BmSDK's whole address table assumes code
at 0x1000-and-up with `.text` ~17 MB; here 0x1000…0x3095000 (50.6 MB) is string/rodata and the
code is at 0x4262000.

---

## 2. Why `0x5B7220` fails (all three hypotheses tested)

| hypothesis | test | result |
|---|---|---|
| **H1 wrong build** | compare layout the offsets presuppose with this exe | Offsets 0x5B7220, 0x5B1DA0, 0xF90CD0, 0xFA2A60, 0xF3B7F0 … all land in `.link` on UTF-16 text (`kerLv4`, `EMPBlast`, `dlerDLC_NightWin`, …). A build where those RVAs are code cannot have a 26.6 MB string section at 0x1000. **No byte of this exe supports H1 as the whole story**; the engine provenance strings (`D:\Bm3_build\TitleUpdatePC\Development\Src\...`) are consistent with the same title update family. Whether it is byte-identical to BmSDK's target build is **UNKNOWN** — that would need the original `.exe`, which does not exist on this machine (searched the game folder, `temp-dodi`, `Uninstall`, and `E:\Modding`, depth 4: only this one copy). |
| **H2 relocated sections** | test constant-delta fits against the unwind table | Falsified for a *uniform* shift. Best of all candidate deltas explains only **10/22** offsets, and the explanations are semantically impossible (e.g. delta 0x5095A00 maps `ProcessEvent` onto a **44-byte** function, `CollectGarbage` onto 3,257 bytes, `ProcessDeadMessage` onto a 512 KB gap). Also `0x5B7220 + 0x195C000 = 0x20B2E20` still decodes as UTF-16 text (`pe_probe3.py`). |
| **H3 packing that decrypts later** | read the live process, compare sections with disk | **Confirmed.** `.text1` is decrypted in place at load (`compare_mem.py`); the decrypted range starts at exactly the first `.pdata` function (0x4262010). BmSDK's offsets are below that, inside `.link`, which is *never* rewritten (96.31 % identical to disk; the 3.7 % delta is runtime-mutated data plus the host's own `E9`). |

### Why the .NET runtime never starts (mechanism, decoded)

`BmSDK.Host.asi`'s `DllMain` → `init_runtime()` → `DetourManager::RegisterEngineLoopPreInitDetour()`
→ `DetourAttach(BaseAddress + 0x5B7220, …)`. In this image that address is inside `.link`
(string data), so:

1. the `E9 …` trampoline is written over string bytes (observed live at
   `0x1405B7220`: `e9538ffebf` + `cc4c00760034000000000045004d0050004200` — the `E9` followed by
   the mangled `EMPBlast` text), and
2. the detour body (`runtime::load_dll()`) is only reached when a thread executes that address,
   which never happens because nothing jumps there.

Confirmed in the live process: module list contains `DINPUT8.dll` (twice) and
`BmSDK.Host.asi` at `0x7ff8e6810000`, and **no** `coreclr.dll`, `hostfxr.dll`,
`hostpolicy.dll` or `clrjit.dll` (`proc_probe2.py`, 136 modules). So the host loaded, the
detour committed, and .NET was never initialised — exactly the reported symptom, with the
cause now measured rather than inferred.

Side effect worth flagging: the installed host is silently corrupting `.link` string data in
every session. That is data, not code, so the game survives, but it is a live defect.

---

## 3. Address audit — every native address BmSDK uses, checked against this exe

Method: take each constant from `src/BmSDK/FrameworkInternal/GameDefine.Steam.cs`,
`src/BmSDK.Host/Framework/offsets.h` and `src/BmSDK.Generator/Engine/GameOffsets.h`, read the
bytes at `BaseAddress + offset` in the *decrypted* runtime image, and look the address up in
the `.pdata` function list (`pe_probe2.py`, `delta_cluster.py`).

All code offsets resolve into `.link` (string data). Sample bytes are the first 16 at each RVA.

| symbol | BmSDK offset | section here | bytes here (first 16) | verdict |
|---|---|---|---|---|
| `EngineLoopPreInit` | 0x5B7220 | `.link` | `6b00650072004c007600340000000000` = `kerLv4` | **invalid** (data) |
| `EngineTick` | 0x5B1DA0 | `.link` | `00000000000000004d00490045005f00` = `MIE_` | **invalid** |
| `AppRealloc` | 0xFA2A60 | `.link` | `4e0044004500520043004100540045` = `NDERCATE` | **invalid** |
| `AppFree` | 0xFA2A80 | `.link` | `4c00650066007400…` = `Left` | **invalid** |
| `StaticFindObject` | 0xF3B7F0 | `.link` | `7400630068004e006f00740046…` = `tchNotF` | **invalid** |
| `StaticConstructObject` | 0xF470B0 | `.link` | `610074006d006f00620069006c00` | **invalid** |
| `LoadPackage` | 0xF46DA0 | `.link` | `75006d0070000000470041005f` | **invalid** |
| `CollectGarbage` | 0xF2C280 | `.link` | `69006e006500440079006e006100` | **invalid** |
| `ProcessEvent` | 0xF90CD0 | `.link` | `64006c006500720044004c0043005f` = `dlerDLC_` | **invalid** |
| `ProcessInternal` | 0xF90B30 | `.link` | `4500500065007200630065006e0074` | **invalid** |
| `CallFunction` | 0xF95AA0 | `.link` | `47000000000000004100750064006900` | **invalid** |
| `AddObject` | 0xF388F0 | `.link` | `6f006f006c00650061006e00…` | **invalid** |
| `ConditionalDestroy` | 0xF38D80 | `.link` | `6b00650064005400650078007400` | **invalid** |
| `FindFunction` | 0xF3DB80 | `.link` | `4200670053006300610072006500` | **invalid** |
| `ConditionalPostLoad` | 0xF430F0 | `.link` | `6800610072006100630074006500` | **invalid** |
| `AddToRoot` | 0xF2D440 | `.link` | `000000000400000078c3fd0230000000` | **invalid** (non-code) |
| `RemoveFromRoot` | 0xF2D460 | `.link` | `22059319010000005ce4e50200000000` | **invalid** (non-code) |
| `GetDefaultObject` | 0xF92870 | `.link` | `750073005f00440069007300610062` | **invalid** |
| `SpawnActor` | 0xACBC70 | `.link` | `30692f4501000000d09bbb4401000000` | **invalid** (non-code) |
| `ProcessDeferredMessage` | 0x105D400 | `.link` | `5f00500072006f006a006500630074` = `_Project` | **invalid** |
| `NameInit` | 0xF37BF0 | `.link` | `4600520041004e0047004500…` = `FRANGE` | **invalid** |
| `StringCtor` | 0x41D0 | `.link` | (string data) | **invalid** |
| `BeginLoad` / `EndLoad` (Generator) | 0xF2D410 / 0xF43BF0 | `.link` | string data | **invalid** |
| `GNames` | 0x3A208B8 | `.sdata` | `00…00` (24 bytes of zero) | **invalid** (expects a pointer; GNames is a live pointer variable) |
| `GObjObjects` | 0x340CBE4 | `.sdata` | `00000000 4c53d24d 00000000 9785b014` | **invalid** (32-bit pairs, not a pointer array) |
| `GError` | 0x3A20AA8 | `.sdata` | inside the same zeroed span | **invalid** |

Structural proof that these offsets do not belong to this image: a rip-relative reference scan
over the decrypted code (9,731,722 instructions, `sweep2.py`) finds **0** references to
0x340CBE4, 0x3A208B8 or 0x3A20AA8 — a build in which `StaticFindObject` exists must reference
`GObjObjects` and `GNames`. For comparison the same scan finds 38,144 references into `.text`
(the live string table) and only 19 into `.link`.

Member offsets in `GameDefine.MemberOffsets` (`Object__Outer`=52, `Object__Name`=60,
`Object__Class`=68, …) are **not verified**: they can only be checked against a live `UObject`
graph, and that needs `GObjObjects`, which is UNKNOWN here. Recorded as UNKNOWN, not assumed.

Replacement values for every row above: **UNKNOWN**. No row has a candidate that survived a
test, and this project's rule is that a plausible-looking address is not evidence.

---

## 4. What the repack did to the string tables (useful for the next attempt)

Two large string/rodata blobs exist, and they are not interchangeable:

* `.link` (26.6 MB, 0x1000–0x195D000): UTF-16 data, contains `EMPBlast`, `D:\Bm3_build\…`
  assert paths, `LoadPackage`, `GEngine`. Referenced from code only **19** times.
* `.text` (24.3 MB, 0x195D000–0x3095000): UTF-16 data, contains the literals the code actually
  uses — `Core`, `Engine`, `<uninitialized>`, `BmGame`, `WinDrv`, `AkAudio`,
  `..\..\BmGame\Config\BmEngine.ini`, `Engine.GameEngine`, `Fatal error!`, `Pure virtual not
  implemented`. Referenced **38,144** times.

Consequence for anchoring: any scheme that searches `.link` for a literal will find the string
and no xref, and any scheme that assumes `.link` is the live `.rdata` will produce wrong
cross-references. This is the trap that makes naive signature work on this exe fail.

---

## 5. Locating the equivalent `FEngineLoop::PreInit` — attempts, results, verdict

Everything below was executed against the decrypted runtime image (dump of
`PID 8756`/`PID 9820`, base 0x140000000, `.text1` 77,230,080 bytes).

| attempt | method | result |
|---|---|---|
| A. assert-path xrefs | `D:\Bm3_build\…\Launch\Src\LaunchEngineLoop.cpp` occurs 4× (RVAs 0x6232F0, 0x6238E0, 0x623B00, 0x623DB0), `Launch.cpp` 1× (0x5BB030), `UnObj.cpp` 16×, `UnName.cpp` 4×, `UnObjGC.cpp` 3×, `UnLinker.cpp` 7×, `UnVcWin32.cpp` 3× | **0 xrefs** to any of them. Shipping build: the assert paths survive in the string table but the checks are compiled out. Dead end. |
| B. package literals | xref UTF-16 `Core` (219 occurrences), `Engine` (748), `BmGame` (22) | The only referencing functions are small (55–669 bytes, e.g. 0x4263CC0 78 B, 0x4263D0E 669 B) and sit at the head of `.text1`; too small to be `PreInit`, and they do not call `LoadPackage`-shaped code. Not adopted. |
| C. constant-delta RANSAC | fit all 22 offsets to the 124,020 `.pdata` starts | Best delta 0x5095A00 explains 10/22, all other peaks 9/22, and the mappings are impossible on size grounds (`ProcessEvent`→44 B). Falsified (`§2`). |
| D. `WinMain` via imports | find `call [IAT:GetCommandLineW]` (slot 0x1460B21F8) → 3 call sites → functions 0x428E360 (784 B), 0x48B4630 (394 B), 0x4A195F0 (51 B) | 0x428E360 is reached from 0x500BC40 (896 B, the CRT `__scrt_common_main_seh` shape) and does `GetCommandLineW` → `malloc`-style call 0x5366BA0 → tokenizer call 0x42782F0 → `free`. It is command-line **tokenisation**, not the engine entry, and it contains no engine-loop call. Not adopted. |
| E. `Sleep`/`PeekMessageW` sites | 21 and 5 call sites | Split across window/viewport helpers (largest 0x53832E0, 600 B); no loop that matches `while(!GIsRequestingExit) Tick();`. Inconclusive. |

**Verdict: the equivalent `FEngineLoop::PreInit` in this exe is UNKNOWN.** The stable pattern
that was asked for cannot be honestly derived from a function that has not been identified —
publishing a byte pattern derived from an unverified candidate would be exactly the guess this
project forbids, and a wrong `E9` in code (not data) would crash the game instead of just
mangling a string.

What a next session should do, in order, with the tooling that already exists here
(`tmp/freebuff/bmsdk-port/`):

1. Sample the main thread's stack of a running session (`TEB.TibStackBase/TibStackLimit` via
   `NtQueryInformationThread` + `ReadProcessMemory`) and take the return address that recurs at
   the same depth across samples: that is the engine-loop caller, i.e. `WinMain`. This is
   behaviour-based and needs no string anchors.
2. From `WinMain`, the call immediately preceding the repeating loop entry is `PreInit`; the
   loop body call is `FEngineLoop::Tick` (BmSDK's 0x5B1DA0 is the same function *in the original
   layout*, so its identity can be cross-checked by the loop shape).
3. Derive the pattern from the identified function prologue plus one wildcarded immediate
   (the `LoadPackage("Core")` call site) rather than a raw byte prefix, because the packer
   rewrites rip-relative displacements.
4. Only then repeat for the globals: `StaticFindObject` = the only function that walks
   `GObjObjects` comparing `FName`s, and both global addresses fall out of *its own* decoded
   instructions once it is identified.

---

## 6. The patch that would be required (exact edits)

The SDK hard-codes addresses in **three** places. Changing only the host is not sufficient:
after `.NET` starts, `BmSDK.dll` would immediately use `ProcessEvent`/`StaticFindObject`/
`GNames` from `GameDefineSteam` and crash.

1. `src/BmSDK.Host/Framework/offsets.h`
   ```cpp
   inline constexpr uintptr_t EngineLoopPreInit = 0x5B7220;   // -> <verified RVA>
   ```
2. `src/BmSDK/FrameworkInternal/GameDefine.Steam.cs` — all 21 `IntPtr` properties
   (`GNames`, `GObjObjects`, `GError`, `AppRealloc`, `AppFree`, `EngineTick`,
   `StaticFindObject`, `StaticConstructObject`, `LoadPackage`, `CollectGarbage`,
   `ProcessEvent`, `ProcessInternal`, `CallFunction`, `AddObject`, `ConditionalDestroy`,
   `FindFunction`, `ConditionalPostLoad`, `AddToRoot`, `RemoveFromRoot`, `GetDefaultObject`,
   `SpawnActor`, `ProcessDeferredMessage`, `NameInit`, `StringCtor`).
3. `src/BmSDK.Generator/Engine/GameOffsets.h` — `GObjects`, `GNames`, `StaticFindObject`,
   `LoadPackage`, `BeginLoad`, `EndLoad`, `CollectGarbage`, `ProcessEvent`.

Rebuild: `Build.ps1 Build Release` (needs MSBuild + v145 C++ tools + vcpkg manifest for
Detours). **Blocked on this machine** — see §7.

If the toolchain stays unavailable, the equivalent binary edits are:

* **`plugins\BmSDK.Host.asi`** — the only `imm32` occurrence of `0x5B7220` is at file offset
  **0x129DB** (RVA 0x133DB), inside the `mov rax,[rip+…]; add rax, imm32` that forms
  `BaseAddress + offset`:
  `48 8b 05 97 c6 29 00 | 48 05 20 72 5b 00 | 4c 8d 05 …`
  Patch the four bytes at 0x129DB to the verified RVA, little-endian.
* **`sdk\BmSDK.dll`** — each offset is compiled as `ldc.i4 <imm32>; conv.i; ret`, i.e. the byte
  pattern `20 <imm32 LE> D3 2A`. Locate by the current value (each of
  `0x3A208B8`, `0x340CBE4`, `0x3A20AA8`, `0xFA2A60`, `0xFA2A80`, `0x5B1DA0`, `0xF3B7F0`,
  `0xF470B0`, `0xF46DA0`, `0xF2C280`, `0xF90CD0`, `0xF90B30`, `0xF95AA0`, `0xF388F0`,
  `0xF38D80`, `0xF3DB80`, `0xF430F0`, `0xF2D440`, `0xF2D460`, `0xF92870`, `0xACBC70`,
  `0x105D400`, `0xF37BF0`, `0x41D0` is unique in a 25 MB assembly) and replace the 4-byte
  immediate.
* Backup rule: copy the original beside it first —
  `plugins\BmSDK.Host.asi` → `plugins\BmSDK.Host.asi.orig-20261106`,
  `sdk\BmSDK.dll` → `sdk\BmSDK.dll.orig-20261106` — before writing anything.

**Nothing was built or installed.** Two independent blockers: (a) no verified
`EngineLoopPreInit` RVA (§5), and (b) no C++ toolchain: `vswhere -all -products *` reports only
*Visual Studio Build Tools 2026* 18.4.11605.240, whose install directory has **no `VC\Tools\MSVC`
and no `cl.exe`**, `vswhere -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64`
returns nothing, and there is no vcpkg anywhere (`C:\vcpkg`, repo-local `vcpkg_installed`).
MSBuild 18.4 itself is present. Writing an unverified `E9` target into a **code** section is
not recoverable by the user the way the current data corruption is, so it was not done.

---

## 7. Game-folder state

Nothing under `E:\Games\Batman Arkham Knight` was created, edited, moved or deleted by this
task. The folder was only read (and the process only read via `ReadProcessMemory`).

One session was started for scraping, as authorised (`Start-Process BatmanAK.exe`,
2026-11-06). Consequences, measured:

* `PID 8756` (first session) exited during the dump; `PID 9820` is the live session
  (4.5 GB working set) and still holds BmSDK's 5-byte `E9` at `0x1405B7220`, i.e. the string
  data there is corrupted **in RAM only**.
* `coreclr` never loaded in either session (`§2`).

Recommended operator action: close the running session and, until a verified port exists,
remove or rename `Binaries\Win64\plugins\BmSDK.Host.asi` (and keep the backup) so that the
shipped-but-wrong `E9` stops being written into `.link` on every launch.

---

## 8. How to confirm a future port actually worked

1. Launch `Binaries\Win64\BatmanAK.exe`, then list the process modules (read-only):
   `coreclr.dll`, `hostfxr.dll`, `hostpolicy.dll` must appear. Today the list is
   `DINPUT8.dll` ×2 + `BmSDK.Host.asi` only.
2. `Binaries\Win64\BmSDK.log` must exist (the log is
   `FileUtils.GetBinariesPath() + "BmSDK.log"` →
   `E:\Games\Batman Arkham Knight\Binaries\Win64\BmSDK.log`) and start with
   `[Loader] Detected Steam build`, then contain `[MinimalScript] Hello from MinimalScript!`
   from `bin\BmGame\Scripts\MinimalScript.cs` (`Debug.Log` in `Main()`).
3. Only then verify a native call path: invoke one cheat/`ProcessEvent` and confirm no crash —
   that is the step that proves the managed offset table, not just the host detour.

---

## COMPROMISES

1. **`FEngineLoop::PreInit` not identified.** Recorded UNKNOWN. Four independent methods
   (assert-path xrefs, package-literal xrefs, unwind-table delta fitting, import-call tracing
   from `GetCommandLineW`) were executed and falsified; the next step (main-thread stack
   sampling) is specified but not executed.
2. **`BmSDK.Host.asi` not rebuilt.** No C++ toolchain on the machine (no `VC\Tools\MSVC`,
   no `cl.exe`, no vcpkg). Exact source edits and the byte-level equivalents (including the
   `0x129DB` patch site) are given instead.
3. **No patched asi installed.** Deliberate: installing a `E9` over an unverified *code*
   address would turn a recoverable data corruption into a crash, and the task's own condition
   ("only if the original is backed up beside it", after the report says what to change) is not
   met because the value is unknown.
4. **Only the first two sessions were dumped.** One exited mid-dump (`.xtext` unread, error
   299), the other is the live one. All conclusions about `.text1` decryption and `.pdata` come
   from data present in both.
5. **Member offsets not verified** (`Object__Outer`=52 etc.); they need a live `UObject` graph,
   which needs the UNKNOWN `GObjObjects`.
6. Read-only rule preserved: no writes to game files, no writes to game memory, no
   `SuspendThread`. The one live session was launched, as the operator authorised.

---

## Evidence artifacts (all under `E:\Modding\JustCause3\JC3-Batmobile\tmp\freebuff\bmsdk-port\`)

| file | what it produced |
|---|---|
| `pe_probe.py`, `pe_probe2.py`, `pe_probe3.py`, `pe_probe4.py`, `pe_probe5.py` | headers, sections, entropy, bytes at every BmSDK RVA, `.pdata`/`.xtext` parsing, 124,020 function starts |
| `dump_mem.ps1`, `compare_mem.py` | read-only section dump of the live process; memory-vs-disk diff proving `.text1` decryption |
| `proc_probe.py`, `proc_probe2.py`, `probe_proc.ps1` | live module list (no coreclr), main-module section table, live bytes at 0x5B7220 with the `E9` |
| `delta_solve.py`, `delta_cluster.py` | constant-delta falsification |
| `xref_scan.py`, `probe7_structure.py`, `probe9_text1.py`, `sweep2.py` | reference topology: `.link` 19 refs vs `.text` 38,144; `.text1` 46 MB still encrypted |
| `probe6_paths.py`, `probe8_literals.py`, `probe10_xrefcheck.py`, `probe11_sweep.py` | string/path census and scanner self-tests |
| `probe12_winmain.py`, `probe13_main.py` | import-call tracing of `GetCommandLineW`/`Sleep`/`PeekMessageW`; full disassembly of 0x428E360 |
| `bmlib.py` | shared image view, unwind lookup, chunked xref scanner, IAT-resolving disassembler |
| `dump\*.bin` | the section dumps (147 MB) used for every runtime claim |
