# BmSDK address hunt — GOG `BatmanAK.exe` (PE 0x6508b1ce)

Target: `E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe`
(read-only; **nothing in the game folder was created, edited or deleted**).
Measured this session: 55,101,440 bytes, PE timestamp `0x6508b1ce`, image base
`0x140000000`, `SizeOfImage` `0x440b000`, entry `0x16c2e74`, **unpacked**
(`.text` on disk == code, no decryption at load).
Tooling: `tmp/freebuff/bmsdk-gog/` (`gog.py` + `probe1..14`), `pefile` 2024.8.26,
`capstone` 5.0.7.

**Verdict in one line:** the BmSDK-AK offset table describes a *different compilation*
of this title — of its 25 code addresses, 2 land exactly on a function start and 23 do
not — so the whole table must be re-derived. This session established the startup half
of the answer to decoded/derived level (`WinMain`, the launch driver and the four
`FEngineLoop` functions, plus the three globals `GNames`, `GObjObjects`, `GEngine`), and
falsified every BmSDK candidate for the UObject/app cluster, which is therefore recorded
**UNKNOWN** rather than guessed.

Every row below is **decoded** (bytes/table read directly, address stated),
**derived** (named rule + inputs), or **UNKNOWN** (no candidate survived a test).

---

## 1. What this exe is (decoded)

```
machine 0x8664   imagebase 0x140000000   entry 0x16c2e74   SizeOfImage 0x440b000
```

| section | VA | vsize | rawsize | chars |
|---|---|---|---|---|
| `.text`  | 0x00001000 | 0x0195891e | 0x01958a00 | 0x60000020 (RX) |
| `.rdata` | 0x0195a000 | 0x017301af | 0x01730200 | 0x40000040 |
| `.data`  | 0x0308b000 | 0x0105c390 | 0x000e2e00 | 0xc0000040 (RW) |
| `.pdata` | 0x040e8000 | 0x0016b2a0 | 0x0016b400 | 0x40000040 |
| `.tls`   | 0x04254000 | 0x49       | 0x200      | 0xc0000040 |
| `.rsrc`  | 0x04255000 | 0x57ae0    | 0x57c00    | 0x40000040 |
| `.reloc` | 0x042ad000 | 0x15d6d6   | 0x15d800   | 0x42000040 |

This is the layout BmSDK's table presupposes (code at 0x1000, `.data` at 0x308b000) —
**not** the repacked Steam install analysed previously (`BMSDK` report
`bmsdk-port-to-repack-exe.md`, whose `.text1` was encrypted). So the earlier "code lives
elsewhere" conclusion does not apply here.

`.pdata` parses as a clean `RUNTIME_FUNCTION[]`: **123,960** entries, first begin
`0x1010`, last end `0x19598ac` — exactly `.text`, monotonic. Median function size 91 B,
p90 385 B. Function starts are therefore available for the whole code section
(`gog.py: func_of / psize`).

Engine source paths are **ASCII** in `.rdata` next to `appErrorf`:
`D:\Bm3_build\TitleUpdatePC\Development\Src\Launch\Src\LaunchEngineLoop.cpp`
(RVAs 0x1F7738F, 0x1F7796F, 0x1F77BEF, 0x1F77EBF), `...\Launch\Src\Launch.cpp`
(0x1F0F0AF), `UnObj.cpp` (0x29A99ED +13 more), `UnName.cpp` (0x29A67BD +3),
`UnObjGC.cpp` (0x29A0E5D +2), `UnLinker.cpp`, `UnVcWin32.cpp`, `UnClass.cpp`,
`UnWorld.cpp`, `UnEngine.cpp`. **All of them have 0 xrefs** (shipping build, asserts
compiled out) — so source-path strings cannot anchor anything here.

---

## 2. Is the hook address a function start with a prologue? **No.**

BmSDK-AK hooks `BaseAddress + 0x5B7220` (`src/BmSDK.Host/Framework/offsets.h`).
In this exe that RVA is **code** (inside `.text`) but it is **not a function entry** and
has **no prologue**:

```
.pdata function: 0x5B7200 .. 0x5B722D   (45 bytes)
005b7200  4883ec28            sub   rsp, 0x28
005b7204  488b15edf6bb02      mov   rdx, [rip+0x2bbf6ed]      ; -> 0x31768F8
005b720b  4c8d442430          lea   r8, [rsp+0x30]
005b7210  4881c1b4fcffff      add   rcx, -0x34c
005b7217  c7442430 00000000   mov   dword [rsp+0x30], 0
005b721f  e8cccf9e00          call  0x140FA41F0               ; <- 0x5B7220 is INSIDE this operand
005b7224  8b442430            mov   eax, [rsp+0x30]
005b7228  4883c428            add   rsp, 0x28
005b722c  c3                  ret
```

`0x5B7220` = `0x20` bytes into the function, i.e. the last 4 bytes of the `call`'s
rel32 operand (the task's `cc cf 9e 00` are exactly that displacement, followed by
`8b 44 24 30 48 83 c4 28 c3`). A 5-byte `E9` written there would (a) never be executed
as an entry, and (b) corrupt the displacement of a live internal call — so the detour can
never fire. **This is the same class of failure as the repacked install, for a different
reason: the address is a stale build's function entry, not data.**

The containing function is an accessor-shaped thunk (45 B, returns an int out-param),
one of a dense run of such thunks in 0x5B23xx–0x5B72xx — nothing to do with the engine
loop.

---

## 3. Method used

1. Parse `.pdata` → every real function start/end in `.text`.
2. Walk the **real** startup path from `AddressOfEntryPoint`, not from strings:
   CRT → `invoke_main` → `WinMain` → launch driver → engine loop.
3. Judge identity by (a) position in the call graph, (b) the function's own **string
   vocabulary** (`__FILE__`/config/mode literals), (c) `.pdata` size/prologue, (d)
   xref topology for globals (writes vs reads).
4. For the BmSDK table: read the bytes at every BmSDK RVA, look it up in `.pdata`, and
   require a *structural* match before accepting anything.

---

## 4. Results — every BmSDK address, this exe

`Δ` = BmSDK RVA minus the `.pdata` start of the function that contains it here (0 means
BmSDK's address *is* a function start in this build).

### 4.1 Startup / engine loop (established)

| BmSDK symbol | BmSDK RVA | **this exe (RVA)** | Δ | evidence | level |
|---|---|---|---|---|---|
| `EngineLoopPreInit` (the hook) | 0x5B7220 | **0x5DCCB0** | — | see §5.3 | derived |
| `EngineTick` (`FEngineLoop::Tick`) | 0x5B1DA0 | **0x5D9850** | — | §5.2 | derived |
| *(not in table)* `WinMain` | — | **0x5DFFF0** | — | §5.1 | decoded |
| *(not in table)* launch driver | — | **0x5DFEF0** | — | §5.2 | decoded |
| *(not in table)* `GuardedMain` wrapper | — | **0x5DFD70** | — | §5.3 | derived |
| *(not in table)* `FEngineLoop::Init` | — | **0x5DB710** | — | §5.2 | derived |
| *(not in table)* `FEngineLoop::Exit` | — | **0x5D7B90** | — | §5.2 | derived |
| *(not in table)* `PreInit` first half | — | **0x5DEA60** | — | §5.3 | derived |

### 4.2 Globals

| BmSDK symbol | BmSDK RVA | **this exe (RVA)** | evidence | level |
|---|---|---|---|---|
| `GNames` | 0x3A208B8 | **0x3A8E978** | runtime self-validated (MODLOG 2026-11-03 G3-02d: `[0]='None'`, `[1]='ByteProperty'`, FNameEntry walk), + 27 code xrefs incl. 2 write sites (0xF58D26 in 0xF58C50, 0xF59110 in 0xF59070) | decoded |
| `GObjObjects` | 0x340CBE4 | **0x347ACA4** | runtime self-validated (16 consecutive objects with `Index == position`; 700,416 slots walked) + 128 code xrefs | decoded |
| `GError` | 0x3A20AA8 | **UNKNOWN** | no candidate tested; see §7 | UNKNOWN |
| `GEngine` (candidate) | *(not in table)* | **0x3A8EB68** | 600 refs, exactly **1** write (0xF8558E in 0xF85550, 10,005 B); WinMain reads it after the loop and virtual-calls `[rax+0x20]` (0x5E00F1) — `GEngine->…` shape | derived |

Both runtime-verified values are exactly **BmSDK value + 0x6E0C0**
(`0x3A208B8+0x6E0C0 = 0x3A8E978`, `0x340CBE4+0x6E0C0 = 0x347ACA4`): the `.data` segment
moved by one constant, while the code segment did **not** (see §7). Cross-check: a
rip-relative scan for BmSDK's own `0x3A208B8` / `0x340CBE4` in this image finds **0**
references — those values are dead here, as expected for a moved data segment.

### 4.3 UObject / app / FName / FString cluster — all UNKNOWN

| BmSDK symbol | BmSDK RVA | this exe | Δ | why it is not adopted | level |
|---|---|---|---|---|---|
| `StringCtor` | 0x41D0 | 0x41A0* (145 B) | +0x30 | lands inside a plausible FString-shaped function, but nothing in it was verified as `FString::FString(const TCHAR*)`; BmSDK needs the exact ctor | UNKNOWN |
| `CollectGarbage` | 0xF2C280 | 0xF2C25C* (334 B) | +0x24 | BmSDK's address is mid-function; the 334 B function is not GC-shaped (no `GObjObjects` ref); the 7,201 B neighbour 0xF2D0A0 holds `verify`-style line-number traps, not identified | UNKNOWN |
| `BeginLoad` | 0xF2D410 | 0xF2D0A0* | +0x370 | inside a 7,201 B function with three unrelated BmSDK anchors | UNKNOWN |
| `AddToRoot` | 0xF2D440 | 0xF2D0A0* | +0x3A0 | idem | UNKNOWN |
| `RemoveFromRoot` | 0xF2D460 | 0xF2D0A0* | +0x3C0 | idem | UNKNOWN |
| `NameInit` | 0xF37BF0 | **0xF37BF0** | 0 | *is* a function start here (40 B: `sub rsp,0x28; test byte [rcx+0x6c],2; mov edx,[rcx+0x78]; …`) — but that body does not match `FName::Init(this, name, number, findType, split)` (no FName layout), so alignment alone is not evidence | UNKNOWN |
| `AddObject` | 0xF388F0 | 0xF38880* (136 B) | +0x70 | mid-function of a dense run of small getters/setters; no `GObjObjects` write | UNKNOWN |
| `ConditionalDestroy` | 0xF38D80 | 0xF38D60* | +0x20 | mid-function | UNKNOWN |
| `StaticFindObject` | 0xF3B7F0 | 0xF3B7xx region: starts 0xF3B890, 0xF3B8BA, … | — | BmSDK's RVA is not a start; the nearby functions are 20–190 B and none was shown to walk `GObjObjects` comparing FNames | UNKNOWN |
| `FindFunction` | 0xF3DB80 | 0xF3DB60* (78 B) | +0x20 | mid-function, and a `UFunction* FindFunction(FName, int)` body was not verified | UNKNOWN |
| `ConditionalPostLoad` | 0xF430F0 | 0xF43070* (1,934 B) | +0x80 | mid-function | UNKNOWN |
| `EndLoad` | 0xF43BF0 | 0xF43B40* | +0xB0 | mid-function | UNKNOWN |
| `LoadPackage` | 0xF46DA0 | 0xF46D90* (97 B) | +0x10 | 97 B cannot be `UObject::LoadPackage`; no package-loader shape verified | UNKNOWN |
| `StaticConstructObject` | 0xF470B0 | 0xF46F9D* (319 B) | +0x113 | mid-function | UNKNOWN |
| `ProcessInternal` | 0xF90B30 | inside **0xF90620** (2,156 B) | +0x510 | see §7 — merged/duplicated code, not a function boundary | UNKNOWN |
| `ProcessEvent` | 0xF90CD0 | inside **0xF90620** (2,156 B) | +0x6B0 | idem | UNKNOWN |
| `CallFunction` | 0xF95AA0 | 0xF95A70* | +0x30 | mid-function | UNKNOWN |
| `GetDefaultObject` | 0xF92870 | 0xF926AA* (535 B) | +0x1C6 | mid-function | UNKNOWN |
| `SpawnActor` | 0xACBC70 | 0xACBA20* (614 B) | +0x250 | mid-function | UNKNOWN |
| `ProcessDeferredMessage` | 0x105D400 | **0x105D400** | 0 | *is* a start (188 B: `push rbx; sub rsp,0x30; mov [rsp+0x20],-2; mov rbx,rcx; …`) and the message-pump region matches (neighbouring 0x105D340/0x105D4C0 are pump helpers), but the body was not verified against `FWindowsViewport::ProcessDeferredMessage` | UNKNOWN |
| `AppRealloc` | 0xFA2A60 | 0xFA2980* (288 B) | +0xE0 | mid-function; allocator wrapper not verified | UNKNOWN |
| `AppFree` | 0xFA2A80 | 0xFA2980* | +0x100 | idem | UNKNOWN |

\* containing `.pdata` start, shown only to document *why* BmSDK's value is rejected.
`UNKNOWN` here means "no candidate survived a test", not "not looked at": each row was
opened, disassembled and checked against the signature BmSDK's own delegate implies
(`GameFunctions.cs`).

---

## 5. The startup chain, with evidence

### 5.1 `WinMain` = 0x5DFFF0 (decoded)

`AddressOfEntryPoint` 0x16C2E74 → `call 0x16C2FFC` (`__security_init_cookie`) → `jmp 0x16C2BA4`
(`__scrt_common_main_seh` shape: `GetStartupInfoW`, gs:[0x30], `Sleep`, `_acmdln`). At
0x16C2CF7:

```
016c2cf7  488d0d02d393fe   lea  rcx, [rip-0x16c2cfe]     ; = 0x140000000 = &__ImageBase
016c2cf5  33d2             xor  edx, edx                 ; hPrevInstance = NULL
016c2cf2  4c8bc3           mov  r8, rbx                  ; _acmdln (char*)
016c2cee  440f45c8         cmovne r9d, eax               ; nCmdShow (10 or STARTUPINFO.wShowWindow)
016c2cfe  e8edd2f1fe       call 0x1405DFFF0              ; WinMain(hInstance, NULL, cmdline, show)
```

Four-argument `(HINSTANCE, HINSTANCE, char*, int)` call out of the CRT = `WinMain`.
Its body (372 B, prologue `48 89 5c 24 08 48 89 74 24 10 48 89 7c 24 18 41 54 48 83 ec 30`)
does `CreateMutexW`, `GetLastError`+`ERROR_ALREADY_EXISTS`, `_set_invalid_parameter_handler`,
`wcscpy_s(GameName, "N"…)`, sets `[0x3A96C48]=1`, `GetCommandLineW`, then calls
0x5DFFB0 (→ 0x5DFEF0). This is `Launch.cpp` (its `__FILE__` string is 0x1F0F0AF, no xref).

### 5.2 The launch driver and the loop (decoded)

`0x5DFEF0` (187 B) — exact call/loop structure:

```
005dfeff  e86cfeffff   call 0x5DFD70            ; PreInit + Init (wrapper, below)
005dff0a  cmp [0x3A96C78], eax  / jne          ; GIsRequestingExit?
005dff32  call 0xC9A790                        ; app-level init, 2 string args
005dff3e  call 0x5DB710(rcx=&0x317A630)        ; FEngineLoop::Init
005dff60  lea rcx,[0x317A630]
005dff67  call 0x5D9850                        ; <- loop body  == FEngineLoop::Tick
005dff6c  cmp [0x3A96C78], 0 / je 0x5DFF60     ; while (!GIsRequestingExit)
005dff77  mov [0x3A96C78], 1
005dff88  call 0x5D7B90(rcx=&0x317A630)        ; FEngineLoop::Exit
```

* `0x317A630` is dereferenced only by these functions plus 0x5D86F0 (53 B) and one
  `lea` at 0x17B7DE0 → it is the **`GEngineLoop` object** (7 refs total, no writes:
  it is an object, not a pointer).
* `0x3A96C78` (21 refs, 15 write sites) is the loop-termination flag (`GIsRequestingExit`).
* `0x5D9850` (1,702 B) is entered only from that loop; its prologue
  `48 8b c4 56 57 41 54 41 55 41 56 48 81 ec 90 00 00 00` begins with
  `QueryPerformanceCounter` (delta-time bookkeeping) — a tick function.
* `0x5D7B90` (1,772 B) runs after the loop and references `benchmark.log` and
  `"min= %6.2f   avg= %6.2f   max= %6.2f%s"` — an engine shutdown/benchmark flush.
* `0x5DB710` (2,339 B) is called once between PreInit and the loop; references
  `"engine-ini:Engine.Engine.GameEngine"` (0x5DB822), `-EXEC=`/`exec ` (0x5DBCF8/0x5DBD3C),
  `STATUNIT`, `nosound`, `PERFMEMDUMP`, `USEALLAVAILABLECORES` — engine creation + startup
  exec (`FEngineLoop::Init`).

### 5.3 `FEngineLoop::PreInit` = 0x5DCCB0 (derived) and its wrapper

`0x5DFD70` (374 B, `Launch.cpp`'s guarded-main step) does the launch-side set-up, then:

```
005dfd88  mov edx,8 / mov ecx,0x150 / call 0xFCD850     ; new(0x150, 8)
005dfda3  r8=0x1F0EE88 ("Main Thread") / edx=0 / call 0xFDF470   ; construct
005dfdb9  store -> 0x3179D30 and 0x3A8EAF8
005dfdc7  lea rdx,[0x1F0EEA0] / call 0xF73A00            ; cmdline test
005dfdf4  call 0xFD3640 -> FString of the command line
005dfe3f  wcscpy_s(0x3179DE0, 0x400, cmdline)            ; global cmdline buffer
005dfeae  call 0x5DEA60(&GEngineLoop=0x317A630, FString) ; half A (4,880 B)
005dfeb7  call 0x5D64D0(eax)
005dfecc  call 0x5DCCB0(&GEngineLoop, FString)           ; half B (7,160 B)
005dfed5  mov [0x3179D3C], 0
```

`0x5DCCB0` carries the strings that only `FEngineLoop::PreInit` has, in UE3 source order:

```
0x5DCD3E U:"EDITOR"                     0x5DCDC0 U:"CookPackages"
0x5DD0CF U:"Make is not supported in this mode."
0x5DCFDD U:"Engine.ServerCommandlet"    0x5DD1CC U:"UnrealEd.MakeCommandlet"
0x5DD48F lea rcx,[0x1BC14F8]  ("Core")  -> call 0xF58AD0 -> cached at 0x347AC90
0x5DD636 U:"CommandletsToForceMinimalShaderCompilation"
0x5DD8CC lea rcx,[0x1BC1508]  ("Engine")-> call 0xBE72D0 -> cached at 0x318D6B8
0x5DD8F3 walks [obj+0x5c] (Outer chain)  0x5DD901 mov [0x3A96C78],0
0x5DD95B U:"engine-ini:Engine.Engine.GameEngine"
0x5DD834 U:"AUTODEBUG"  0x5DD880 U:"VADEBUG"  0x5DDFF3 U:"NOINI"  0x5DE5C3 U:"ONETHREAD"
0x5DE137 U:"DUMPMOVIE"  0x5DE156 U:"-MATINEESSCAPTURE="  0x5DE1E4 U:"BENCHMARK"
```

Prologue (proper, 8-byte aligned frame):
`48 8b c4 48 89 48 08 55 56 57 41 54 41 55 41 56 41 57 48 8d a8 d8 fd ff ff`
(`mov rax,rsp; mov [rax+8],rcx; push rbp,rsi,rdi,r12,r13,r14,r15; lea rbp,[rax-0x228]`).

The first half it calls, `0x5DEA60` (4,880 B, 54 string refs), is the engine/thread
bootstrap: thread priorities `GameAboveNormal`/`PhysUpdateNormal`/`GC Scheduler`/
`Low Priority`/`Idle Priority`, `VERIFYGC`/`NOVERIFYGC`, `SEEKFREEPACKAGEMAP`,
`ENABLE_TFC_RANDOM`, `firstinstall`, `-SS:`, `Engine.Engine`, `bUseTextureStreaming`.
Whether AK split `PreInit` into these two functions or `0x5DEA60` is a sub-step is
**not established**; both are listed, and the recommendation in §8 assumes the pair.

---

## 6. Answer for the port brief (paste-ready)

Only verified rows carry a value; `UNKNOWN` must stay `UNKNOWN` until tested.

```cpp
// BatmanAK.exe — GOG build, PE timestamp 0x6508b1ce, image base 0x140000000
// derived/decoded 2026-11-07, see tmp/freebuff/reports/bmsdk-gog-address-hunt.md
namespace offsets {
    inline constexpr uintptr_t EngineLoopPreInit   = 0x5DCCB0;  // derived  (PreInit half B, 7160 B)
    inline constexpr uintptr_t EngineLoopPreInitB  = 0x5DEA60;  // derived  (PreInit half A, 4880 B)
    inline constexpr uintptr_t EngineLoopInit      = 0x5DB710;  // derived  (FEngineLoop::Init)
    inline constexpr uintptr_t EngineTick          = 0x5D9850;  // derived  (FEngineLoop::Tick)
    inline constexpr uintptr_t EngineLoopExit      = 0x5D7B90;  // derived  (FEngineLoop::Exit)
    inline constexpr uintptr_t WinMain             = 0x5DFFF0;  // decoded
    inline constexpr uintptr_t GuardedMain         = 0x5DFEF0;  // decoded
    inline constexpr uintptr_t LaunchWrapper       = 0x5DFD70;  // derived

    inline constexpr uintptr_t GNames              = 0x3A8E978; // decoded (runtime validated)
    inline constexpr uintptr_t GObjObjects         = 0x347ACA4; // decoded (runtime validated)
    inline constexpr uintptr_t GEngine             = 0x3A8EB68; // derived
    inline constexpr uintptr_t GEngineLoop         = 0x317A630; // decoded (object, not pointer)
    inline constexpr uintptr_t GIsRequestingExit   = 0x3A96C78; // decoded (loop flag)

    // all still UNKNOWN for this build — do not paste BmSDK's Steam values:
    // GError, AppRealloc, AppFree, StaticFindObject, StaticConstructObject, LoadPackage,
    // CollectGarbage, ProcessEvent, ProcessInternal, CallFunction, AddObject,
    // ConditionalDestroy, FindFunction, ConditionalPostLoad, AddToRoot, RemoveFromRoot,
    // GetDefaultObject, SpawnActor, ProcessDeferredMessage, NameInit, StringCtor,
    // BeginLoad, EndLoad
}
```

Scan patterns (prologue + 24 bytes, wildcarding any rel32/rip displacement):

```
PreInit  : 48 8b c4 48 89 48 08 55 56 57 41 54 41 55 41 56 41 57 48 8d a8 d8 fd ff ff
Init     : 48 8b c4 55 56 57 41 54 41 55 48 8d 68 a1 48 81 ec b0 00 00 00
Tick     : 48 8b c4 56 57 41 54 41 55 41 56 48 81 ec 90 00 00 00
Exit     : 48 8b c4 55 41 54 41 55 48 8d 68 a1 48 81 ec f0 00 00 00
WinMain  : 48 89 5c 24 08 48 89 74 24 10 48 89 7c 24 18 41 54 48 83 ec 30 41 8b f1
```

A better detour than a byte pattern: hook whichever of the PreInit pair is entered
**after** `Core`/`Engine` package creation (0x5DD48F / 0x5DD8CC inside 0x5DCCB0), because
BmSDK's `Loader.DllMain` immediately runs `StaticInit`/`ScriptManager`, which need
`GNames`/`GObjObjects` populated.

---

## 7. Why the 22 UObject addresses are not merely "shifted"

1. **They are entries in another compilation.** Landing 0x6B0 into a function for
   `ProcessEvent` and 0x510 for `ProcessInternal` cannot be a relocation: the two BmSDK
   RVAs are 0x1A0 apart and *both* fall inside one 2,156-byte function here (0xF90620),
   at two byte-identical code blocks 0x1A1 apart (differing only in one rip displacement:
   `48 8b 05 56 1c af 02` vs `48 8b 05 ad 1a af 02`). Two `FFrame`-shaped constructions
   with different globals — not the `ProcessEvent`/`ProcessInternal` pair.
2. **Uniform-delta fitting is dead on arrival** because the `.data` segment *is* uniform
   (+0x6E0C0, proven by two runtime-validated globals) while the code is not: e.g. the
   whole launch region is ~+0x28C90 relative to BmSDK's (their `PreInit` 0x5B7220 vs this
   build's 0x5DCCB0), whereas `NameInit` (0xF37BF0) and `ProcessDeferredMessage`
   (0x105D400) sit at *identical* RVAs. One build cannot be a constant shift of the other.
3. **`.pdata` has no boundary where BmSDK expects one** in several regions: 0xF2D0A0 is a
   single 7,201-byte range covering three BmSDK anchors (0xF2D410/0xF2D440/0xF2D460), and
   those 45-byte thunk-shaped neighbours in 0x5B7xxx (like the hook target's function)
   show this build groups/inlines small functions differently.
4. Therefore the remaining 22 must each be established semantically, from a verified
   primitive. Two primitives now exist and are the right starting point:
   * `GObjObjects = 0x347ACA4` — 128 xrefs; biggest readers 0x915040 (6,043 B),
     0x9AA8C0 (1,245 B), 0xB14540 (1,452 B), 0xF6C140 (4,013 B), 0xAD8C80 (4,976 B),
     0xF6F530 (6,703 B). `StaticFindObject`, `CollectGarbage`, `AddToRoot`,
     `RemoveFromRoot`, `AddObject` all read it.
   * `GNames = 0x3A8E978` — 27 xrefs, **two writers** (0xF58D26 in 0xF58C50, 0xF59110 in
     0xF59070 which is 34,332 B) — the writer set bounds `FName` name-table growth, i.e.
     `NameInit`.

The next experiment, in order (all tooling already in `tmp/freebuff/bmsdk-gog/`):
1. In 0x915040 / 0xF6F530 / 0xAD8C80, classify the `GObjObjects` loops (`GObjObjects[i]`
   walk + `FName` compare ⇒ `StaticFindObject`; walk + flag test + `ConditionalDestroy`
   ⇒ `CollectGarbage`). Confirm with callers: `StaticFindObject` is called from hundreds
   of sites, `CollectGarbage` from a handful.
2. Take the confirmed `StaticFindObject`'s callee that converts `const TCHAR*` → `FName`
   (walk of `GNames` + hash) — that is `NameInit`/`FName::Init`; then `StringCtor` is the
   `FString` ctor it uses.
3. `ProcessInternal` = the callee of the bytecode dispatch: search the `GNatives` table
   consumers. Note: this build has **exactly one** `call qword ptr [idx*8 + table]`
   site (0xC76D7D → table 0x3B2FD84) and 5,305 `call [reg + reg*8]` sites, so `GNatives`
   is reached through a *pointer*, not a static array — start from 0xC76D00 and from the
   `-1` bytecode `Code` dispatch shape.
4. `LoadPackage`: hook the `("Core")`/`("Engine")` creation helpers reached at 0x5DD48F
   (callee 0xF58AD0) and 0x5DD8CC (callee 0xBE72D0); one of them is the package creator,
   the other its cache, and `LoadPackage` is their common caller.
5. Only then `ProcessEvent` (caller of `ProcessInternal` with the 4-argument shape from
   `GameFunctions.cs`), then the app allocators (0xFA25xx–0xFA2Dxx) and the rest.

---

## 8. Game-folder state and reproduction

* No file under `E:\Games\Batman Arkham Knight` was written, moved or deleted; no process
  was started; no memory was written. Only `pefile` reads of the exe.
* New files created by this session (revert = delete them):
  `tmp/freebuff/bmsdk-gog/gog.py`, `probe1.py`, `probe2.py`, `probe3.py`,
  `probe4_ptrtables.py`, `probe5.py`, `probe6_winmain.py`, `probe7_strxrefs.py`,
  `probe8_engineloop.py`, `probe9_loopfuncs.py`, `probe10.py`, `probe11_strings_of.py`,
  `probe12_gnatives.py`, `probe12b.py`, `probe13.py`, `probe14_windows.py`, `selftest.py`,
  and this report `tmp/freebuff/reports/bmsdk-gog-address-hunt.md` (new file, no existing
  file edited).
* Re-derive every number in this report: `python tmp/freebuff/bmsdk-gog/selftest.py`.

## COMPROMISES

1. **22 of 25 BmSDK code addresses are UNKNOWN** for this build. This is a measured
   negative: each was opened, disassembled and rejected for a stated reason (§4.3), and
   the structural falsification is in §7. No plausible-looking RVA was published.
2. **`FEngineLoop::PreInit` is `derived`, not `decoded`**: there is no symbol table, and
   the two halves (0x5DCCB0, 0x5DEA60) are bracketed by the launch driver, not by a name.
   The evidence is the launch-order position, the `Core`/`Engine`/commandlet string
   vocabulary and the `.pdata` prologues.
3. **`NameInit` and `ProcessDeferredMessage` land exactly on function starts** here, but
   neither body was verified against its signature; they are kept UNKNOWN deliberately.
4. **No runtime test was run.** The two globals rest on the earlier read-only runtime
   probe recorded in `MODLOG.md` (2026-11-03, G3-02d); they were not re-sampled this
   session.
5. `GError` has no candidate; the `+0x6E0C0` rule would put it at 0x3A8F768, but a
   derived-by-drift address is not evidence, so it is not published as a value.
