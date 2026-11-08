# BmSDK-AK: GOG / Epic port status and offset provenance

Research date: 2026-11-07. Local source: `E:/Modding/_tools/BmSDK-AK` (read-only inspection; nothing written to game folders).

**Rule applied:** every claim below carries a URL or a file path. Where no evidence exists, the row says **UNKNOWN**.

---

## 0. Headline answers

| Question | Answer | Evidence |
|---|---|---|
| Has anyone ported BmSDK-AK to the **GOG** build? | **No.** No public port, fork, PR, release or issue containing GOG offsets was found. Upstream explicitly says GOG is unsupported. | https://github.com/Team-BmSDK/BmSDK-AK (README), https://github.com/Team-BmSDK/BmSDK-AK/issues/14, https://github.com/Team-BmSDK/BmSDK-AK/forks |
| Has anyone ported it to the **Epic (EGS)** build? | **Yes** — unofficial fork `cberdejo/BmSDK-AK-Epic-Games`, release v0.22.0 (2026-10-12), with a complete hand-written Epic offset table. | https://github.com/cberdejo/BmSDK-AK-Epic-Games , https://github.com/cberdejo/BmSDK-AK-Epic-Games/releases , https://github.com/cberdejo/BmSDK-AK-Epic-Games/commit/c51321f |
| Has anyone **documented how the offsets are found**? | **No.** No doc, script, signature database or write-up exists in either repo. The Epic values are bare constants in a commit. How they were derived is **UNKNOWN**. | https://github.com/cberdejo/BmSDK-AK-Epic-Games/commit/c51321f (diff shows only literals), https://bmsdk.dev/docs/contributing/building (no offset methodology) |
| Is there any **signature scanning** in upstream BmSDK-AK? | **No.** Not a single pattern scan exists; all targets are `module base + const offset`. | `E:/Modding/_tools/BmSDK-AK/src/BmSDK.Host/Framework/offsets.h`, `E:/Modding/_tools/BmSDK-AK/src/BmSDK.Host/Framework/detour_manager.cpp`, `E:/Modding/_tools/BmSDK-AK/src/BmSDK/FrameworkInternal/GameDefine.cs` |

### The single most important find

The Epic fork selects its table on **PE `TimeDateStamp == 0x6508B1CE`**:

```cpp
inline constexpr uint32_t TimeDateStampEpic = 0x6508B1CE;
```
— `src/BmSDK.Host/Framework/offsets.h`, in https://github.com/cberdejo/BmSDK-AK-Epic-Games/commit/c51321f

`0x6508B1CE` is **exactly the timestamp you gave for the GOG `Binaries/Win64/BatmanAK.exe`**. That is either (a) the GOG and Epic executables are the same binary / same link, or (b) the fork author labelled a shared build "Epic". This has not been verified in this research — it requires hashing the two exes. **If the GOG exe's timestamp and hash match the Epic one, the Epic offset table is a drop-in candidate for GOG.** Decoded, `0x6508B1CE` = 1 695 068 622 = **2023-09-18 20:23:42 UTC** (computed locally: `date -u -d @1695068622`).

---

## 1. Upstream README (Team-BmSDK/BmSDK-AK)

URL: https://github.com/Team-BmSDK/BmSDK-AK (also https://github.com/Team-BmSDK/BmSDK-AK/blob/main-bm4/README.md)

- Verbatim: *"⚠️ Notice for Epic or GOG users: Only Steam copies of Arkham Knight are supported currently. EGS/GOG support is being considered, but BmSDK unfortunately does not work on these platforms for the time being."*
- Install path documented is the Steam path only: `C:\Program Files (x86)\Steam\steamapps\common\Batman Arkham Knight`.
- Local copy agrees: `E:/Modding/_tools/BmSDK-AK/README.md` lines 100–101 carry the same notice.

A local grep for `gog|epic|egs` over the whole checkout returned **only** those two README lines as meaningful hits — there is no build-conditional code anywhere in `src/`. (Command run: `code_search` for `(?i)gog|epic|egs` in `E:/Modding/_tools/BmSDK-AK`; all other 125 hits were generated UnrealScript names such as `GoggleBlinded`, `HandlePickup`, `Epicenter`.)

## 2. Wiki, especially "Building-BmSDK"

- `https://github.com/Team-BmSDK/BmSDK-AK/wiki` and `https://github.com/Team-BmSDK/BmSDK-AK/wiki/Building-BmSDK` **both redirect to the repository root** — the GitHub wiki is not serving pages for this repo. **The "Building-BmSDK" wiki page does not exist.** (Both fetched; final URL in each case was `https://github.com/Team-BmSDK/BmSDK-AK`.)
- Build instructions moved to https://bmsdk.dev/docs/contributing/building . That page describes the architecture (Generator → Host → SDK) and says *"You will need a vanilla build of the game. BmSDK was developed for the Epic Games Store version which has a different executable and some other small differences to the other builds. Prefer getting the game files from the EGS if you can. Otherwise, apply the SteamPatch to the installation you want to use."*
  - Caveat: that text is written for **Arkham City** (it references `BatmanAC.exe`, `BatmanArkhamCity`, Win32). Treat it as AC guidance, not AK. It is still the only statement anywhere that BmSDK's "official" dev build is EGS-sourced.
  - It contains **no** offset-finding methodology, no signature list, no table. Confirms the **UNKNOWN** verdict on documentation.
- The README's own "Contributing" section points at that same page: https://github.com/Team-BmSDK/BmSDK-AK (section "🛠️ Contributing").

## 3. Issues (open and closed)

Search: https://github.com/Team-BmSDK/BmSDK-AK/issues?q=is%3Aissue+gog+OR+epic+OR+EGS+OR+offsets → **1 result**.

- **Issue #14** — "not a bug but sir please waiting for gog mod version we will be very thankfull for you", opened 2026-10-31 by `billogamers-droid`, **still Open**. One comment from `goodpersonff-afk` (2026-11-06) also asking for GOG. **No maintainer reply, no work linked, no branch or PR attached** ("Development: No branches or pull requests").
  URL: https://github.com/Team-BmSDK/BmSDK-AK/issues/14
- Search `is:issue signature OR scan` → **1 unrelated result** (#13, update modes), i.e. no issue discusses offset derivation.
  URL: https://github.com/Team-BmSDK/BmSDK-AK/issues?q=is%3Aissue+signature+OR+scan

## 4. Pull requests (open and closed)

URL: https://github.com/Team-BmSDK/BmSDK-AK/pulls?q=is%3Apr — **16 total (7 open, 9 closed)**.

Open: #15–#21, all by `XeTrinityz`, all performance/feature work (string work in `ProcessInternal` detour, `OnDraw(Canvas)`, key-swallowing, wrapper cache fix, exception containment, param fixing). Closed: #1–#10, release-please bumps, a README docs PR (#7), and "feat: support DLC when launched from .exe" (#5).

**No PR mentions GOG, Epic, EGS, a different exe, or offsets.** Nothing to cherry-pick.

## 5. Releases

URL: https://github.com/Team-BmSDK/BmSDK-AK/releases — latest **v0.21.0 (2026-09-12)**; earlier v0.19.0, v0.18.0, v0.17.2. Release notes cover `TArray.AsSpan()`, an installer `.exe`, `BmSDK.log`, DLC support, super-class fallback. **No GOG/Epic asset, no platform-specific download.**

Fork release: https://github.com/cberdejo/BmSDK-AK-Epic-Games/releases — **v0.22.0 (2026-10-12)**, single feature line: *"Support Epic Games copies of Arkham Knight (c51321f)"*.

## 6. Forks list

URL: https://github.com/Team-BmSDK/BmSDK-AK/forks — 3 forks:

| Fork | Created / updated | Relevance |
|---|---|---|
| `cberdejo/BmSDK-AK-Epic-Games` | 2026-10-10 / 2026-10-12 | **The Epic port.** Full offset table + timestamp switch. |
| `Samuil1337/BmSDK-AK` | 2026-07-13 / 2026-07-14 | Looks like a docs/CI fork; README identical, no offset work visible. |
| `XeTrinityz/BmSDK-AK` | 2026-11-06 / 2026-11-07 | Same README as upstream (still says "Only Steam copies…"); the author's work arrives as PRs #15–#21, none platform-related. |

`XeTrinityz` fork README checked: https://github.com/XeTrinityz/BmSDK-AK — carries the unmodified Steam-only notice. `Samuil1337` fork infers from PR #7 authorship (README styling), URL https://github.com/Team-BmSDK/BmSDK-AK/pull/7.

No fork contains a GOG offset table.

## 7. The Epic port, in full (what you can literally reuse)

Fork: https://github.com/cberdejo/BmSDK-AK-Epic-Games — README states:

> "BmSDK relies on memory offsets that are specific to each build of the game, and the Epic Games build of Arkham Knight differs from the Steam one. This fork:
> Detects which build is running from the executable's PE header timestamp and uses the matching set of offsets (Epic build 0x6508B1CE), falling back to the original Steam offsets otherwise.
> Applies this in BmSDK, BmSDK.Host and BmSDK.Generator.
> Makes the installer detect Epic Games installations automatically…"
> "⚠️ Notice for GOG users: Only Steam and Epic copies of Arkham Knight are supported by this fork. GOG copies are not supported for the time being."

Single commit of substance: `c51321f` "feat: support Epic Games copies of Arkham Knight" — https://github.com/cberdejo/BmSDK-AK-Epic-Games/commit/c51321f . It touches exactly 6 files:

1. `src/BmSDK.Host/Framework/offsets.h` — adds `TimeDateStampEpic`, turns `EngineLoopPreInit` into a runtime variable, adds `offsets::init()` that reads `PIMAGE_NT_HEADERS64->FileHeader.TimeDateStamp` and switches.
2. `src/BmSDK.Host/dllmain.cpp` — `offsets::BaseAddress = GetModuleHandle(NULL)` → `offsets::init()`.
3. `src/BmSDK.Generator/Engine/GameOffsets.h` — same switch for the 8 generator offsets.
4. `src/BmSDK.Generator/Runtime.cpp` — one line: `GameOffsets::Init(Runtime::BaseAddress);`
5. `src/BmSDK/FrameworkInternal/GameDefine.Epic.cs` — **new file, 50 lines, the Epic table (24 addresses).**
6. `src/BmSDK/FrameworkInternal/GameDefine.cs` — `Current` becomes lazy, adds `Detect()` reading the PE header from `MemUtil.GetBaseAddress()`.
7. `src/BmSDK.Installer/GameDetector.cs` — adds `DetectEpic()`, `EpicAppName = "Cowbird"`, reads `%PROGRAMDATA%\Epic\EpicGamesLauncher\Data\Manifests\*.item`.

### Epic address table (verbatim from the commit diff)

```
GNames                 0x3A8E978
GObjObjects            0x347ACA4
GError                 0x3A8EB68
AppRealloc             0xFCD870
AppFree                0xFCD890
EngineTick             0x5D9850
StaticFindObject       0xF66230
StaticConstructObject  0xF71A70
LoadPackage            0xF71760
CollectGarbage         0xF56E80
ProcessEvent           0xFBBCC0
ProcessInternal        0xFBBB20
CallFunction           0xFC0A90
AddObject              0xF63450
ConditionalDestroy     0xF638D0
FindFunction           0xF685C0
ConditionalPostLoad    0xF6DAB0
AddToRoot              0xF58050
RemoveFromRoot         0xF58070
GetDefaultObject       0xFBD860
SpawnActor             0xAF45A0
ProcessDeferredMessage 0x1087F80
NameInit               0xF62750
StringCtor             0x41A0
```
Host: `EngineLoopPreInit 0x5DEA60`. Generator: `GObjects 0x347ACA4`, `GNames 0x3A8E978`, `StaticFindObject 0xF66230`, `LoadPackage 0xF71760`, `BeginLoad 0xF58020`, `EndLoad 0xF6E5B0`, `CollectGarbage 0xF56E80`, `ProcessEvent 0xFBBCC0`.

Source for every number above: https://github.com/cberdejo/BmSDK-AK-Epic-Games/commit/c51321f

**How those Epic numbers were obtained: UNKNOWN.** The commit message is one line, the README says nothing, there is no script, no `.sig` file, no notes. Do not assume a method.

## 8. Precedent inside the same organisation: BmSDK-AC (Arkham City)

Arkham City already has an **official** two-build design, and it is a better template than the AK fork:

- https://github.com/Team-BmSDK/BmSDK-AC — README: *"Only Steam and Epic copies of Arkham City are supported currently. GOG support is being considered, but BmSDK unfortunately does not work on this platform for the time being."*
- Files: `src/BmSDK/FrameworkInternal/GameDefine.cs`, `GameDefine.Steam.cs`, `GameDefine.Epic.cs` — https://github.com/Team-BmSDK/BmSDK-AC/tree/main/src/BmSDK/FrameworkInternal
- `GameDefine.Detect()` (raw: https://raw.githubusercontent.com/Team-BmSDK/BmSDK-AC/main/src/BmSDK/FrameworkInternal/GameDefine.cs) switches on PE `TimeDateStamp` and **throws** on anything unknown:

```csharp
_ => throw new NotSupportedException(
    $"Unrecognized BatmanAC.exe build (TimeDateStamp 0x{timeDateStamp:X8})"),
```

That fail-fast behaviour is the opposite of the AK Epic fork, which silently falls back to Steam. For a GOG hunt, AC's version is the safer copy: it will tell you loudly that a table is missing instead of detonating at a wrong address. AC also demonstrates `VTableOffsets` (build-invariant) living outside the per-build table.

## 9. neatodev/BmLauncher

- https://github.com/neatodev/BmLauncher — **Batman: Arkham Asylum**, not Knight. README: *"THIS PROJECT IS ARCHIVED"*, superseded by the .NET 6 rewrite (`neatodev/BmLauncherAsylumNET6`, https://github.com/neatodev/BmLauncherAsylumNET6), with `neatodev/CityLauncher` (https://github.com/neatodev/CityLauncher) covering City.
- It **does** support all three stores: *"It supports the Steam, GOG and Epic Games Store version and nothing else."* and gives GOG install-location instructions ("click the icon next to the PLAY button and select Manage installation→Show folder"). URL: https://github.com/neatodev/BmLauncher/blob/master/README.md
- But it is a **config/INI front-end**: `Program.cs` (https://raw.githubusercontent.com/neatodev/BmLauncher/master/Program.cs) is WinForms + NLog + `MyFactory.readFiles()` + an NvAPI worker. **It contains no process-memory code, no offsets, no signature scanning** — nothing that helps with a GOG `BatmanAK.exe` address hunt. Its only transferable idea is that "support GOG" there means *find the install folder and edit INIs it already knows*, which sidesteps the problem entirely.

## 10. Web search for any other GOG work

Searched for GOG + BmSDK + offsets + timestamp combinations. Nothing exists outside the sources above:

- bmsdk.dev (https://bmsdk.dev/) and docs (https://bmsdk.dev/docs) — no GOG AK material.
- Nexus "Fightable Characters (BmSDk)" (https://www.nexusmods.com/batmanarkhamknight/mods/3426) and "Fightable Allies" (https://www.nexusmods.com/batmanarkhamknight/mods/3489) — mods requiring BmSDK-AK, no GOG notes.
- "Arkham Knight Community Patch" (https://www.nexusmods.com/batmanarkhamknight/mods/5) claims Steam/GOG/EGS testing, but it is a file/pak patch, unrelated to BmSDK.
- A third-party article (https://macmyths.com/how-to-install-and-manage-mods-for-batman-arkham-knight-on-pc, 2026-10-04) restates only "the current repository notice says it supports Steam copies only".
- GOG build data for reference (build 1.999, 2024-07-10): https://www.gogdb.org/product/1881970704

**GOG Arkham Knight offset table, for BmSDK or for anything else: UNKNOWN. No public source.**

---

## 11. How the addresses are declared in the local source (E:/Modding/_tools/BmSDK-AK)

There is no C/C++ SDK header table for gameplay functions and no C struct dump — the design is **three separate hard-coded tables**, one per binary that needs to touch the process.

### (a) `src/BmSDK/FrameworkInternal/GameDefine.cs` — the abstract contract
Declares one abstract `IntPtr` property per target and pins the build-invariant member offsets. `Current` is a **static singleton hard-wired to Steam**:

```csharp
public static GameDefine Current { get; } = new GameDefineSteam();
```
`E:/Modding/_tools/BmSDK-AK/src/BmSDK/FrameworkInternal/GameDefine.cs`

### (b) `src/BmSDK/FrameworkInternal/GameDefine.Steam.cs` — the actual table
24 concrete addresses, grouped `Globals` / `app` / `UObject (static)` / `UObject (local)` / `UClass` / `UWorld` / `FWindowsViewport` / `FName` / `FString`:

```
GNames 0x3A208B8   GObjObjects 0x340CBE4   GError 0x3A20AA8
AppRealloc 0xFA2A60   AppFree 0xFA2A80   EngineTick 0x5B1DA0
StaticFindObject 0xF3B7F0   StaticConstructObject 0xF470B0
LoadPackage 0xF46DA0   CollectGarbage 0xF2C280
ProcessEvent 0xF90CD0   ProcessInternal 0xF90B30   CallFunction 0xF95AA0
AddObject 0xF388F0   ConditionalDestroy 0xF38D80   FindFunction 0xF3DB80
ConditionalPostLoad 0xF430F0   AddToRoot 0xF2D440   RemoveFromRoot 0xF2D460
GetDefaultObject 0xF92870   SpawnActor 0xACBC70
ProcessDeferredMessage 0x105D400   NameInit 0xF37BF0   StringCtor 0x41D0
```
`E:/Modding/_tools/BmSDK-AK/src/BmSDK/FrameworkInternal/GameDefine.Steam.cs`

Also build-invariant and *not* per-define (`GameDefine.MemberOffsets`): `Object__ObjectInternalInteger 48`, `Object__Outer 52`, `Object__Name 60`, `Object__Class 68`, `Struct__SuperStruct 92`, `Class__ClassFlags 244`.

### (c) `src/BmSDK.Host/Framework/offsets.h` — one address for the C++ host
```cpp
namespace offsets {
    inline uintptr_t BaseAddress = 0;
    inline constexpr uintptr_t EngineLoopPreInit = 0x5B7220;
}
```
`E:/Modding/_tools/BmSDK-AK/src/BmSDK.Host/Framework/offsets.h` — consumed in `detour_manager.cpp` as `offsets::BaseAddress + offsets::EngineLoopPreInit`:
`E:/Modding/_tools/BmSDK-AK/src/BmSDK.Host/Framework/detour_manager.cpp`
`BaseAddress` is set once in `E:/Modding/_tools/BmSDK-AK/src/BmSDK.Host/dllmain.cpp` from `GetModuleHandle(NULL)`.

### (d) `src/BmSDK.Generator/Engine/GameOffsets.h` — 8 addresses for the SDK generator
`GObjects 0x340CBE4`, `GNames 0x3A208B8`, `StaticFindObject 0xF3B7F0`, `LoadPackage 0xF46DA0`, `BeginLoad 0xF2D410`, `EndLoad 0xF43BF0`, `CollectGarbage 0xF2C280`, `ProcessEvent 0xF90CD0`.
`E:/Modding/_tools/BmSDK-AK/src/BmSDK.Generator/Engine/GameOffsets.h`, used by `Runtime::OnAttach()` in `E:/Modding/_tools/BmSDK-AK/src/BmSDK.Generator/Runtime.cpp`.

### Count check vs. the brief's "22 hard-coded addresses"
The real numbers are **24** in `GameDefine.Steam.cs`, **+1** in `BmSDK.Host/Framework/offsets.h`, and **+8** in `BmSDK.Generator/Engine/GameOffsets.h` (of which `BeginLoad`/`EndLoad` are generator-only and absent from the runtime table). The closest thing to "22" is the set of **21** detour delegate types in `E:/Modding/_tools/BmSDK-AK/src/BmSDK/FrameworkInternal/GameFunctions.cs` plus `EngineTick`/`ConditionalPostLoad` bookkeeping — that is not a clean 22 either. **Exact figure: 24 per-build runtime addresses (+1 host +8 generator). Plan the GOG hunt around 24, not 22.** The abstract declarations live in `GameDefine.cs`; the values live only in the per-build subclass — so adding a build means **one new `GameDefine.<Build>.cs` plus a switch arm**, which is precisely what the Epic fork did.

### Signature scanning: definitively absent
- No `PatternScan` / `SigScan` / `FindPattern` / `memmem` / module-scan helper exists in `src/BmSDK.Host` (search returned 0 matches for `(?i)scan|memmem|VirtualProtect.*Search|ModuleBase \+`).
- A search for `(?i)signature|sigscan|find_pattern|patternscan|scan_pattern` under `src/BmSDK` returned only two **doc comments** about C# method signatures (`Framework/Attributes/RedirectAttribute.cs`, `Framework/Attributes/ComponentRedirectAttribute.cs`) — unrelated to byte patterns.
- Everything resolves through `DetourUtil.NewDetour(GameDefine.Current.<X>, …)` in `E:/Modding/_tools/BmSDK-AK/src/BmSDK/Loader.cs` and `Marshal.GetDelegateForFunctionPointer(MemUtil.GetIntPointer(GameDefine.Current.<X>))` in `GameFunctions.cs`. **Address = image base + constant, nothing else.**

---

## 12. What `7993-bmsdk-gog-address-hunt` can reuse

**Usable directly (with a hash check first):**
1. **The Epic offset table as a GOG starting hypothesis.** It is keyed on `TimeDateStamp 0x6508B1CE`, identical to the GOG exe's timestamp. First action: hash and `cmp` the GOG `Binaries/Win64/BatmanAK.exe` against the Epic/Steam exes and compare `.text` size. Identical → adopt the 24 Epic values unchanged; different → they are landmarks, not values. Source: https://github.com/cberdejo/BmSDK-AK-Epic-Games/commit/c51321f
2. **The two-build plumbing**, already debugged: lazy `GameDefine.Current`, `Detect()` reading `*(uint*)(base + *(int*)(base + 0x3C) + 8)`, `offsets::init()` in the host, `GameOffsets::Init()` in the generator. Copy shape, add a `GameDefine.Gog.cs`. Sources: same commit; `E:/Modding/_tools/BmSDK-AK/src/BmSDK/FrameworkInternal/GameDefine.cs`.
3. **AC's fail-fast `Detect()`** instead of the fork's silent Steam fallback — refuse to run on an unknown `TimeDateStamp` with the value printed. https://raw.githubusercontent.com/Team-BmSDK/BmSDK-AC/main/src/BmSDK/FrameworkInternal/GameDefine.cs
4. **The 24-name hit list** (Source: `E:/Modding/_tools/BmSDK-AK/src/BmSDK/FrameworkInternal/GameDefine.Steam.cs`) — this is the work queue for a GOG dump: 3 globals, 3 `app`, 4 `UObject` statics, 9 `UObject` locals, `GetDefaultObject`, `SpawnActor`, `ProcessDeferredMessage`, `NameInit`, `StringCtor`, plus `EngineLoopPreInit` for the host.
5. **The build-invariant `MemberOffsets`** (48/52/60/68, 92, 244) — likely reusable unchanged on GOG, so don't spend dump time there; verify with one pointer chase.
6. **`GameDetector.cs`'s installer pattern** — `EpicAppName = "Cowbird"` + `%PROGRAMDATA%\Epic\...\Manifests\*.item`. A GOG arm would read the Galaxy registry/`goggame-*.info` equivalent instead. Source: https://github.com/cberdejo/BmSDK-AK-Epic-Games/commit/c51321f

**Not available, don't budget for it:**
- No signature database, no AOB strings, no IDA/Ghidra script, no "how we found these" write-up — from upstream, the Epic fork, AC, or the web. **UNKNOWN**, and absent from every surface checked.
- No GOG `BatmanAK.exe` offset table of any kind.
- Nothing in neatodev/BmLauncher (Asylum-only config launcher, archived, no memory code).

**Suggested minimal experiment (per AGENTS.md, prefer 5 minutes over 500 lines):** dump the GOG exe's PE `TimeDateStamp` and SHA-256, compare with the Steam and Epic exes. Only then decide whether 7993 is "wire up a new table" or "re-derive 24 addresses". The timestamp collision makes the cheap answer plausible enough that it should be tested before any dumping begins.
