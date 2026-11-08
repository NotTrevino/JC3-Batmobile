# BmAK UE3 runtime tools check — what already finds UE3 globals / dumps live objects

**STATUS: done** (web survey + on-paper comparison; nothing downloaded, injected, attached or run
against any game). Target of the question: `E:\Games\BmAK-GOG-sdk` (the copy of the GOG install,
`BatmanAK.exe` PE `0x6508b1ce`, 55,101,440 bytes, image base `0x140000000`, `SizeOfImage`
`0x440b000`, text at `0x00001000`).

**One-line answer:** no published tool locates the UObject/app half of BmSDK's table for *any*
Arkham Knight build. Every surviving tool that "finds GObjects/GNames" does it by **scanning live
memory for the data structures** (or by asking you to type in offsets you reversed by hand) — none
of them publishes a code AOB for `StaticFindObject` / `ProcessEvent` / `CollectGarbage` etc., and
none publishes anything for UE3 x64 Arkham Knight at all. The GOG copy already has the two
primitives those scanners exist to find (`GNames` `0x3A8E978`, `GObjObjects` `0x347ACA4`, both
runtime-validated). So the tool class the operator is looking for solves the part that is *already
solved* and cannot solve the part that is missing. The missing part is not needed to read the six
Batmobile values: those are **object properties**, reachable from `GObjObjects` + `GNames` alone
(§4).

Labels: **decoded** = read from a file/bytes with the source stated; **derived** = rule + inputs;
**UNKNOWN** = searched, no evidence found (what was tried is listed in §5).

---

## 0. Method, and what was *not* done

* Sources: the three earlier reports this task names
  (`tmp/freebuff/reports/bmsdk-gog-address-hunt.md`, `…-gog-copy-port.md`,
  `…-port-to-repack-exe.md`) plus web pages fetched 2026-11-08.
* **Not done, deliberately** (task rule "do not run anything"): no tool downloaded or executed, no
  `.CT` opened, no process attached, no scan of `E:\Games\BmAK-GOG-sdk`. The GOG exe was not even
  read with `pefile` in this session; every GOG-exe number below is quoted from the earlier reports
  and re-verified by `Tools/scripts/bmak_tool_claims_check.py --check` (§6).
* Consequence: every "could it find the 22" cell is a **paper** judgement from (a) what the tool's
  own documentation says it does, and (b) the structural facts about this exe that the address hunt
  already measured. It is not a test result, and it is not presented as one.

---

## 1. Tools table

"AK?" = known to work on **any** Arkham Knight build, with the evidence. "Steam?" = whether the
tool/table is tied to the Steam install. "How it finds G" = the mechanism the source actually
documents. "GOG 22?" = on paper, could it produce the 23 named UNKNOWN addresses in
`E:\Games\BmAK-GOG-sdk` (the earlier report calls them "the other 22" — see the count discrepancy
in §5).

| # | Tool | URL | AK? | Steam? | How it finds GObjects/GNames | GOG 22? |
|---|---|---|---|---|---|---|
| 1 | **CE "Fetch UE3 Pointers/Addresses" script** (One3rd / SunBeam table) | `https://framedsc.com/GameGuides/batman_arkham_asylum.htm`, `https://fearlessrevolution.com/viewtopic.php?t=562` | **No evidence.** Documented for Arkham **Asylum** (`ShippingPC-BmGame.exe`), City (`t=1217`, `BatmanAC.exe`), Origins (`t=1304`, `BatmanOrigins.exe`). No AK page lists this script. | Table is "for the latest Steam build" per its own post; AA/AC/AO tables are **32-bit** processes. | Runtime pointer fetch from the live process: "Activate Fetch UE3 Pointers/Addresses script to fetch the required GNames and GObjects pointers", then a separate **GNames & GObjects Dumper** writes `NamesDump.txt` / `ObjectsDump.txt`; the dump must be re-taken after a loading screen because the objects get reallocated. Script body is inside a login-gated `.CT` → **AOB vs pointer-scan is UNKNOWN** (see §5.1). | **No.** Data-structure discovery only; it never yields function entry points, and it is version-locked by its own author ("if script doesn't get enabled, let me know"). |
| 2 | **SunBeam AK console table** (2017) | `https://fearlessrevolution.com/viewtopic.php?t=946` | **Yes, Steam AK.** Game process `BatmanAK.exe`, table `BatmanAK.CT` 45.26 KiB, posted 2017-04-03; method is a `console.txt` + `BmInput.ini` `exec` + "Set Hook & Emulate RCheatManager UObject" because "the `Console` UObject is missing completely". | Yes — thread is Steam-specific; replies that fail are told "**Steam** version, no torrent crap". | The thread text does **not** describe a pointer-fetch step for AK (unlike the AA/AC/AO posts). It emulates `RCheatManager` and injects its address into `RPlayerController` "at a certain offset I've dug up through debugging" → it clearly has working GNames/GObjects internally, but the mechanism is in the `.CT`/binary and **UNKNOWN** from the text. | **No.** Closed binary table, no published table of engine addresses. |
| 3 | **SunBeam AK "[Engine:Unreal 3.5] « revisited »"** (2019) | `https://fearlessrevolution.com/viewtopic.php?p=96952` | **Yes, Steam AK 1.0 / file 1.6.2.0.** `d3d9.dll` proxy + full source zip (password `SunBeamFRF`), console via `[Engine.Console] ConsoleKey=Tilde`. | Yes ("Game Vendor: Steam"). | Native C++ proxy DLL; source is *published* but was not downloaded here → internals **UNKNOWN**. It demonstrably reaches UE3 console/`ProcessEvent` on AK. | **No** for the 22 (it does not expose a reusable address set), but it is the best *proof* that AK is reachable from a non-CE DLL. |
| 4 | **Unreal Finder Tool** (CorrM; base generator by KN4CK3R) | `https://github.com/CorrM/Unreal-Finder-Tool` | **No evidence for any UE3 title.** README: "Useful tool to help you fetch and dump **Unreal Engine 4** Games information"; repo now marked **Deprecated** ("use version 4 … CheatGear is not associated in anyway with the old UFT tool(v3)"). | No — external reader, store-agnostic. | Scans the target process for the name table and the object array, validates them (GNames must start `None`, `ByteProperty`; GObjects accepts a chunk/first-UObject address, auto-detected), then generates a C++ SDK. UE4 object-array shape (`FUObjectItem` stride, chunks). | **No.** Its whole model is the UE4 object array; AK is UE3 x64 with a `TArray<UObject*>` plus a loose `Index` field, and the README documents no UE3 path. |
| 5 | **UE3 SDK generators — TheFeckless (original)** | original thread is on UnknownCheats; **URL UNKNOWN** (it is not linked as a repo from any of the forks below — they only credit "TheFeckless") | No repo documents AK. | N/A — injected into whatever process you choose. | **They do not discover anything.** The generated `GameDefines.hpp` is hand-reversed per game; only GObjects/GNames may be supplied as an offset **or** a pattern. | **No** — by construction it needs the numbers you are missing. |
| 6 | **UE3SDKGenerator (ItsBrank v2.3.0, deprecated)** | `https://github.com/ItsBrank/UE3SDKGenerator` — **now HTTP 404** (fetched 2026-11-08); README text survives in search index and GitHubHelp mirror `https://githubhelp.com/ItsBrank/UE3SDKGenerator` | No. | N/A (internal DLL). | Same as #5. Verbatim README: "Generate an sdk using either offsets or patterns for GObjects and GNames" and "The `GameDefines.hpp` file will need to be reversed by hand because every game is different, **there is no way to automate this process**." | **No.** |
| 7 | **CodeRed-Generator** (maintained successor to #6) | `https://github.com/CodeRedModding/CodeRed-Generator` (v1.2.1) | No. | N/A (internal DLL). | Same as #5 ("Global Initialization: … either offsets or patterns for GObjects and GNames"), plus GObjects **chunks** and x32/x64 alignment. | **No.** |
| 8 | **ue3-sdkgen** (nyrpqsqq35) | `https://github.com/nyrpqsqq35/ue3-sdkgen` | No ("only tested on RL", i.e. Rocket League — UE3 x64). | N/A. | Runs internally or externally; still needs GObjects/GNames supplied (offsets/patterns). | **No** — but it is the closest thing to a *current* UE3 x64 generator, and it confirms the x64 UE3 shape exists as a solved problem elsewhere. |
| 9 | **BmSDK-AK** (Team-BmSDK) | `https://github.com/Team-BmSDK/BmSDK-AK`, `https://bmsdk.dev/docs/contributing/building` | **Yes — but Steam/EGS only, explicitly not GOG.** README: "Only Steam copies of Arkham Knight are supported currently. EGS/GOG support is being considered, but BmSDK unfortunately does not work on these platforms for the time being." | Yes. Docs: "BmSDK was developed for the Epic Games Store version … Otherwise, apply the **SteamPatch**". | **Hardcoded per-build RVA table** (`GameDefine.Steam.cs`, `offsets.h`, `GameOffsets.h`) — the very 25 values this project had to patch. No AOB, no discovery. | **No as shipped** — it is the *consumer* of these numbers, not a finder. Its open **issue #14** (opened 2026-10-31, "waiting for gog mod version") is the only GOG-related issue; it contains no addresses. |
| 10 | **cberdejo "Epic fork"** | **UNKNOWN — could not be located.** Searches for `cberdejo` + BmSDK/Arkham return nothing; the org/repo that exists is `Team-BmSDK` and the maintainer's clone path in the docs is `https://github.com/etkramer/BmSDK`. | — | — | — | — (see §5.2) |
| 11 | **CE `UnrealEngineTools` (UEInfoScanner.LUA, Dark Byte / Eric Heijnen, MIT)** | `https://github.com/cheat-engine/UnrealEngineTools` | No evidence for AK; the script is written around UE4 `FProperty`/`FField` but explicitly notes "in older UE games a property is an UObject" (the UE3 case). | No. | **Pure runtime memory scanning** (`createMemScan`, grouped scans) — finds `GEngine`/`GameEngine` class and its properties, walks `UClass.PropertyLink`, derives `UObject.Name`/`Class`/`FProperty` offsets by validating candidates against real memory. No module-relative AOB at all. | **No.** It finds *data* (names, classes, property offsets) — useful for reading Batmobile members (§4), useless for function addresses. |
| 12 | **GSpots** | `https://github.com/GLX-ILLUSION/GSpots-` | No evidence for AK; author warns "This will not work on EVERY Unreal Engine game… if the games exe is encrypted, this could bypass it via the memory scan". | No. | Signature table + memory scan, auto-detects the UE version, handles XOR name encryption (UE4.23–5.0 era). | **No** — same class as #11, and its signature set is UE4/UE5. |
| 13 | **AK CE tables on FearLess Revolution / Cheat Happens / WeMod / MrAntiFun** | `t=37352` (health), `t=31886` (health/vehicles/skill points), `t=34317` (`BatmanAK.CT`), `http://www.cheathappens.com/20195-PC-Batman_Arkham_Knight_cheats`, `https://www.wemod.com/cheats/batman-arkham-knight-trainers`, `https://mrantifun.net/threads/batman-arkham-knight-trainer.4737` | **Yes for values, on multiple vendors.** WeMod: "Trainers and Cheats for **Steam, Xbox, Epic Games, and GOG**"; MrAntiFun lists "Batman: Arkham Knight (**GOG**) 9-18-23". Cheat Happens AK list is health/ammo/XP/teleport only. | Not tied to Steam on the WeMod/MrAntiFun side; FRL tables are Steam-versioned. | **Value/pointer scanning only** (health, ammo, XP, cooldown). None of them publishes UE3 object access, GNames/GObjects, or `ProcessEvent`. The SunBeam AK table (#2) is the exception and is still a closed binary. | **No.** |
| 14 | **PCGamingWiki** (AK page + UE3 list) | `https://www.pcgamingwiki.com/wiki/Batman:_Arkham_Knight`, `…/List_of_games_that_use_Unreal_Engine_3` | n/a (reference). Confirms engine "Unreal Engine 3, build 10246 changelist 1340247", Windows exe `BatmanAK.exe`; the **Asylum** page shows a GOG release exists and that its `Engine.u` differs between "Steam and GOG" packages. | n/a | n/a | **No** — but it is the citation for "AK is UE3" and for "GOG builds differ in their executable/packages", which is the whole premise of the port. |

Rows 1–14 cover every tool the brief named except the **BmSDK Discord** ("Arkham Workshop",
`https://discord.gg/FN84a5MRsz` from `bmsdk.dev/docs`): invitation-only chat, not fetchable, so it is
UNKNOWN by construction (§5.3).

---

## 2. Arkham Knight-specific evidence

What actually exists for **this title**, in order of strength:

1. **AK is UE3, and the ported build is not the one BmSDK targets.** PCGamingWiki gives engine build
   `10246 changelist 1340247` for the retail game. BmSDK's README says only Steam is supported and
   the docs say the project was built against the **Epic** executable, with a `SteamPatch` for other
   installs. → AK exists in at least three different `BatmanAK.exe` binaries (Steam, EGS,
   ours = GOG PE `0x6508b1ce`, and the repack `58352898e8aedabe48cd14843865dcf0e697a066ce52c9913df726aa955656ac`,
   104,360,448 bytes). **Only the Steam and EGS tables are published anywhere**, and only as
   constants.
2. **The AK console has been reached twice, both times by hooking/emulating a UObject, not by
   finding a table.** 2017: SunBeam emulates `RCheatManager` and patches `RPlayerController` (#2).
   2019: a `d3d9.dll` proxy (#3) with source, on file version `1.6.2.0`. Both are Steam-only and
   both are closed/compiled against that executable.
3. **The most AK-specific clue in any of these threads is the console command list.** It names the
   classes and functions the operator wants to read (e.g. `FunctionBmGame.RCheatManager` entries
   such as `BatmobileInfinitePower`, `BatmobileSetTireFrictionMod`, `SpawnBatmobileMob`), and
   SunBeam's own 2019 reply prints a live object dump in the form
   `UObject[151071] TriggerFearTakedown 0xC76BFA8 ( Function BmGame.RPlayerController.TriggerFearTakedown )`
   — i.e. **object index, name, address, kind+class**. That is the same walk we can do with
   `GObjObjects` + `GNames` (§4); it is *evidence that the walk is sufficient to enumerate functions
   and properties*, not evidence that anyone published addresses for our build.
4. **AK on GOG is trainable by value scanning, and that is all.** WeMod/MrAntiFun ship a GOG AK
   trainer (health/ammo/XP/cooldowns). No GOG-aware table publishes `GObjObjects`, `ProcessEvent` or
   any of the 23 symbols.
5. **BmSDK-AK has exactly one GOG-related issue (#14) and it contains no technical content** — a
   request, opened 2026-10-31, still the only GOG hit in the tracker. "EGS/GOG support is being
   considered" is the project's own status line; GOG is therefore **not** a solved upstream case we
   can copy.
6. **Our own build's status is unchanged and is the binding constraint:** `GNames`
   `0x3A8E978` and `GObjObjects` `0x347ACA4` are decoded and runtime-validated; `EngineTick`
   `0x5D9850` is derived; everything else in the table (`ProcessEvent`, `ProcessInternal`,
   `StaticFindObject`, `StaticConstructObject`, `LoadPackage`, `CollectGarbage`, `CallFunction`,
   `AddObject`, `ConditionalDestroy`, `FindFunction`, `ConditionalPostLoad`, `AddToRoot`,
   `RemoveFromRoot`, `GetDefaultObject`, `SpawnActor`, `ProcessDeferredMessage`, `NameInit`,
   `StringCtor`, `BeginLoad`, `EndLoad`, `AppRealloc`, `AppFree`, `GError`) is UNKNOWN for the GOG
   exe. That is 23 named symbols where the earlier report says "the other 22" — see §5.4.

---

## 3. Signatures we could reuse

### 3.1 What does *not* exist (searched, negative)

* **No AOB signature for any of `StaticFindObject`, `ProcessEvent`, `ProcessInternal`,
  `CollectGarbage`, `LoadPackage`, `NameInit`, `StaticConstructObject` for any UE3 x64 Arkham
  build.** Every UE3 generator named in §1 either takes offsets/patterns from you or ships a
  per-game `GameDefines.hpp`; none publishes Arkham patterns. The AOB libraries that do exist
  (`UE4SS` "Fixing missing AOBs", `patrickBakin/UE4-Function-Address-Finder`,
  `MercyProductions/Unreal-Engine-Universal`) are **UE4/UE5** and describe a different object model
  (`FUObjectItem`, `FNamePool`, `FField`) plus a change in how `ProcessEvent` is reached
  (vtable index, not a call). Not transferable to UE3 by inspection.
* **No published `BatmanAK.exe` GOG-side table at all**, from any store, in any of the sources above.

### 3.2 What *is* reusable, in order of value

| # | Reusable thing | Why it survives a build change | Evidence |
|---|---|---|---|
| S1 | **`GNames` data-shape oracle:** `GNames[0] == "None"`, `GNames[1] == "ByteProperty"`, walk `FNameEntry` by stride. | It is a property of the name table, not of any code; a different compiler still puts the same two strings first. Already used to validate `0x3A8E978` in this project. | `bmsdk-gog-address-hunt.md` §4.2 (runtime self-validated, MODLOG 2026-11-03 G3-02d). |
| S2 | **`GObjObjects` data-shape oracle:** 16 consecutive objects satisfy `Index == position`, then walk 700,416 slots. | Structural invariant of `TUObjectArray`, independent of code layout. Already used to validate `0x347ACA4`. | same section; and this is exactly the validation `UEInfoScanner.LUA` performs ("the instantiated object has a number for its name", class must be `Class`, vtable must be executable). |
| S3 | **The five startup prologue patterns, derived from *this* GOG build** (already established, so no re-hunt needed): | They were derived here, so they are re-acquirable on the same build; they are the *only* patterns in this repo that are known-good for this exe. | `bmsdk-gog-address-hunt.md` §6 |

```
PreInit : 48 8b c4 48 89 48 08 55 56 57 41 54 41 55 41 56 41 57 48 8d a8 d8 fd ff ff
Init    : 48 8b c4 55 56 57 41 54 41 55 48 8d 68 a1 48 81 ec b0 00 00 00
Tick    : 48 8b c4 56 57 41 54 41 55 41 56 48 81 ec 90 00 00 00
Exit    : 48 8b c4 55 41 54 41 55 48 8d 68 a1 48 81 ec f0 00 00 00
WinMain : 48 89 5c 24 08 48 89 74 24 10 48 89 7c 24 18 41 54 48 83 ec 30 41 8b f1
```

| # | Reusable thing | Note |
|---|---|---|
| S4 | **The data-segment drift rule `+0x6E0C0`** (both runtime-validated globals are exactly BmSDK's value plus this). | Applies to `.data` **only**. It is the reason a "just shift the table" plan looks tempting and it must not be extended to code — the launch region drifted `~+0x28C90` while `NameInit` (`0xF37BF0`) and `ProcessDeferredMessage` (`0x105D400`) sit at *identical* RVAs. |

### 3.3 Why no Steam-derived AOB can be transplanted (paper comparison)

1. **The build is structurally different, not shifted.** Of BmSDK's 25 code/global constants, **2
   land exactly on a function start**; 23 do not. Specifically `ProcessEvent` and `ProcessInternal`
   (`0xF90CD0`, `0xF90B30`, `0x1A0` apart) both fall inside **one 2,156-byte function at `0xF90620`**,
   at two byte-identical blocks `0x1A1` apart differing only in one rip displacement. A signature
   written around two separate functions cannot match a build where they are one function with
   duplicated prologues.
2. **`StaticFindObject`'s slot is not a function.** BmSDK's `0xF3B7F0` lands mid-region; the nearest
   `.pdata` starts are `0xF3B890` and `0xF3B8BA`, and the surrounding functions are 20–190 B. There
   is no "start" at that address to anchor a prologue pattern to, in *this* build, at all.
3. **The GOG exe *is* AOB-scan-able** (unlike the repack): `.text` at `0x00001000`,
   `SizeOfImage` `0x440b000`, 55,101,440 bytes, unpacked, `123,960` `.pdata` functions. So the
   blocker is not the packer any more — it is that no correct pattern exists to scan *for*.
4. **String anchors are dead** (both builds): the `D:\Bm3_build\…\UnObj.cpp` / `UnName.cpp` /
   `UnObjGC.cpp` paths survive in `.rdata` with **0 xrefs** (shipping build, asserts compiled out).
   This is why "find the file name, find the function" fails and why every generator ends up asking
   for hand-reversed offsets.
5. **The only generic primitive that does transfer is the vtable, not a signature**: `ProcessEvent`
   can be identified from a live object's vtable (a slot that lands on a function of the right
   shape), which is what `MercyProductions` does for UE4 and what `UEInfoScanner` does for
   properties. That needs **no** AOB, and it needs `GObjObjects` — which we have. Applicability to
   UE3/AK: **UNKNOWN**, must be tested (§4 step 4).

---

## 4. Recommended route to the 22 addresses

The brief's real goal is six **live values**: LT hold time, eject charge window, steering curve,
`HealthRecoverRate`, summon numbers, and the physics asset the running game uses. None of those is
a function address. They are **properties on UObjects** (`FloatProperty`, `ObjectProperty`,
`StructProperty`) — which means the fastest correct route does not go through the 22 at all.

**Step 1 — stop hunting code addresses for the data goal.** Use the two verified primitives as a
resolver: `GNames 0x3A8E978` to turn a name into a string, `GObjObjects 0x347ACA4` to walk objects,
`UObject.Class`/`Name` to match `BMRVehicle*`/`UKFVehicle*`-shaped classes by name. This is a pure
data walk: ~50 lines over `ReadProcessMemory`, no engine call, no signature, no `ProcessEvent`. It is
the same walk SunBeam's 2019 dump (`UObject[151071] … Function BmGame.RPlayerController.…`) shows is
sufficient to enumerate classes, functions and their addresses *by name*.
*Oracle for the values themselves:* the project already decoded these members from the shipped
packages (the `G3-*` / `BMAK-PHYSICS` / `steering-*` reports). Package data is store-independent, so
the decoded value is a real oracle: a live read that disagrees is a wrong offset, not a different
game.

**Step 2 — validate property offsets, do not assume them.** `Research/BatmobileGrab/BMSDK_OFFSETS.json`
gives absolute `Ptr + N` offsets, but it was generated from the **Steam/EGS** build's layout. Object
layout may well match (it is class layout, not `.data` layout), but that is a **derived** assumption
until checked. Check per class the way `UEInfoScanner` does: walk `PropertyLink`, compare the name at
each property against `GNames`, and confirm type + offset agree with the SDK dump. A mismatch is
information; a silent mismatch is a wrong Batmobile value.

**Step 3 — only then, and only if a *call* is unavoidable**, get `ProcessEvent` from the object
graph rather than from a pattern: take `GObjObjects[0]`'s vtable, find the slot whose target has the
UE3 `ProcessEvent` shape (the `ProcessInternal`-calling wrapper), and verify by invoking a harmless
no-arg `UFunction` found by name. This is S5-style discovery, needs no AOB, and is exactly what the
AK console emulation in #2/#3 must have done. **UNKNOWN until tested.**

**Step 4 — for BmSDK in-process use, reduce the table instead of completing it.** Of the 23 named
symbols, only four are load-bearing for a scripting hook, and three have cheap substitutes:
* `StaticFindObject` → re-implement over `GObjObjects` + `GNames` (name compare is data-only).
* `NameInit` / `StringCtor` → construct `FName` by hashing against `GNames` in our own code; no
  engine call needed to *read* or *compare* names.
* `ProcessEvent` → §4 step 3 (vtable), with `ProcessInternal` as its callee.
* `LoadPackage` / `SpawnActor` / `CollectGarbage` / `AppRealloc` / `AppFree` / `GError` /
  `BeginLoad` / `EndLoad` / `CallFunction` / `AddObject` / `ConditionalDestroy` / `FindFunction` /
  `ConditionalPostLoad` / `AddToRoot` / `RemoveFromRoot` / `GetDefaultObject` /
  `ProcessDeferredMessage` → only needed for spawn/GC/alloc paths; defer, and if needed use the
  anchors the address hunt already found rather than an external tool: `GNames` has exactly **two
  writers** (`0xF58D26` in `0xF58C50`, `0xF59110` in `0xF59070`), the `Core`/`Engine` package
  creation calls sit at `0x5DD48F` → `0xF58AD0` and `0x5DD8CC` → `0xBE72D0`, and `GObjObjects` has
  128 xrefs with six large readers (`0x915040`, `0x9AA8C0`, `0xB14540`, `0xF6C140`, `0xAD8C80`,
  `0xF6F530`). Those are *this build's* addresses — no external signature can beat them.

**Step 5 — if a tool is still wanted, the only one in §1 worth a trial is `UEInfoScanner.LUA` (#11)**,
because it derives structure offsets by validation instead of trusting constants, and would
independently confirm or refute step 2's `BMSDK_OFFSETS.json` assumption. It is UE4-shaped and would
need work for UE3 (`UProperty` is a `UObject`, `PropertyLink` iteration differs) — so this is a
fallback, not the plan, and it cannot produce the 22 either.

**Explicitly not recommended:** the AA/AC/AO "Fetch UE3 Pointers" scripts (32-bit, different engine
build, version-locked), the AK Steam tables (closed, Steam-versioned, no address list), UFT / TheFeckless
forks (they need the numbers we lack, by their authors' own statement), and a Steam-derived AOB
(§3.3 — nothing to write it from).

---

## 5. UNKNOWNs

1. **Mechanism of the "Fetch UE3 Pointers/Addresses" script (AOB vs pointer scan).** The `.CT` body
   is login-gated on FearLess Revolution; the posts describe only *behaviour* ("fetch the required
   GNames and GObjects pointers", dump to `NamesDump.txt`/`ObjectsDump.txt`, re-press after loading
   screens). Not downloaded by rule. Would be settled by opening `BatmanAK.CT` / the AA table and
   reading the script.
2. **The "cberdejo Epic fork".** Could not be located: no repository, gist, or forum post under that
   name for BmSDK/Arkham. Observed instead: the docs point at `https://github.com/etkramer/BmSDK` and
   the org is `Team-BmSDK`; the documented non-EGS path is applying the **SteamPatch**. Whether a
   second fork exists under another account is UNKNOWN.
3. **The BmSDK Discord ("Arkham Workshop").** Invitation-only; not fetchable; no archive. Any address
   discussion there is outside what this task can cite.
4. **Count discrepancy in the earlier report — found by this task's check.** `bmsdk-gog-copy-port.md`
   §3.2 says "the other **22** addresses" and then names **23** (`ProcessEvent` … `GError`); 3 patched
   + 23 = 26, so the "25" total does not reconcile with that list either. This report therefore
   quotes the *list* and reports both figures rather than silently picking one. Which symbol is the
   odd one out needs the upstream `GameDefine.Steam.cs` (or the local patched `BmSDK.dll` immediate
   table) counted — not done here, because it is outside a web survey and no file was read.
5. **Whether any Steam/EGS AK build's bytes match the GOG exe closely enough for an AOB.** Not
   tested (no scan, by rule), and no candidate pattern exists to test.
6. **What the 23 symbols look like in the GOG exe at function-start granularity.** For `NameInit`
   (`0xF37BF0`) and `ProcessDeferredMessage` (`0x105D400`) the RVAs *are* function starts here, but
   neither body was verified against its signature in the earlier session; the rest have no start at
   all. So there is nothing in this build to anchor a published pattern to.
7. **Whether `BMSDK_OFFSETS.json`'s property offsets equal the GOG build's.** Derived-but-unverified;
   needs the step-2 check. If they differ, every Batmobile read needs re-verification by name+type.
8. **Whether `UEInfoScanner.LUA` works on UE3 x64 AK.** The script is UE4-shaped; it acknowledges the
   older `UProperty`-is-an-`UObject` layout but the class/field walk assumes `FField`. Untested.
9. **Whether UFT / CodeRed / ue3-sdkgen work on AK at all.** No repository claims it; `ue3-sdkgen`
   is only tested on Rocket League. Would need a trial build + injection, which the test ban forbids.
10. **The AK engine build of *our* GOG exe.** PCGamingWiki's `10246 / 1340247` is for the retail title
    generally; whether the GOG `BatmanAK.exe` (`0x6508b1ce`) is that build is UNKNOWN (would need its
    version string / a package header match — not done).
11. **MrAntiFun's "Batman: Arkham Knight (GOG) 6-27-40" version string** is not a plausible build
    identifier (year 40); recorded as listed, not interpreted.

---

## 6. Files written, commands, and the check

**New files (nothing else edited):**
* `Tools/scripts/bmak_tool_claims_check.py` — re-extracts every *local* number this report quotes
  from the three earlier reports; `--write` regenerates the JSON, `--check` fails if the JSON is stale
  or if the report stops quoting a value or drops a required section.
* `Research/BatmobileGrab/BMAK_TOOL_CLAIMS.json` — generated by `--write`.
* `tmp/freebuff/reports/bmak-ue3-runtime-tools-check.md` — this report.

**Revert:** delete those three files. No game folder, no process, no earlier report was touched.

**Commands run (verbatim, with output):**

```
$ python Tools/scripts/bmak_tool_claims_check.py --write
wrote Research\BatmobileGrab\BMAK_TOOL_CLAIMS.json
EXIT=0

$ python -c "import json;d=json.load(open('Research/BatmobileGrab/BMAK_TOOL_CLAIMS.json')); ..."
{
 "data_delta": "0x6E0C0",
 "gog_exe_size_bytes": 55101440,
 "gog_image_base": "0x140000000",
 "gog_pe_timestamp": "0x6508b1ce",
 "gog_size_of_image": "0x440b000",
 "gog_text_rva": "0x00001000",
 "patched": {
  "EngineTick": {"file_offset": "0x000FB6B0", "gog": "0x5D9850", "steam": "0x5B1DA0"},
  "GNames": {"file_offset": "0x000FB688", "gog": "0x3A8E978", "steam": "0x3A208B8"},
  "GObjObjects": {"file_offset": "0x000FB690", "gog": "0x347ACA4", "steam": "0x340CBE4"}
 },
 "pdata_function_count": 123960,
 "repack_sha256": "58352898e8aedabe48cd14843865dcf0e697a066ce52c9913df726aa955656ac",
 "repack_size_bytes": 104360448,
 "unknown_symbol_count_listed": 23,
 "unknown_symbol_count_prose": 22
}
23 ['ProcessEvent', 'ProcessInternal', 'StaticFindObject', 'StaticConstructObject', 'LoadPackage',
'CollectGarbage', 'CallFunction', 'AddObject', 'ConditionalDestroy', 'FindFunction',
'ConditionalPostLoad', 'AddToRoot', 'RemoveFromRoot', 'GetDefaultObject', 'SpawnActor',
'ProcessDeferredMessage', 'NameInit', 'StringCtor', 'BeginLoad', 'EndLoad', 'AppRealloc',
'AppFree', 'GError']
```

The first `--write` attempt failed with `FACT NOT FOUND (pe)` and then
`MISMATCH: report says 22 unpatched but lists 23 names`; both were fixed by correcting the parser
and by making the report disclose the count discrepancy (§5.4) instead of hiding it.

Final check:

```
$ python Tools/scripts/bmak_tool_claims_check.py --check
PASS: 14 facts, 42 quoted values, 5 sections
EXIT=0
```

## COMPROMISES

1. **Nothing was tested.** Per the brief ("do not run anything; compare patterns on paper only") and
   the project TEST BAN, no tool was downloaded, no `.CT` opened, no process attached, no scan run.
   Every "could it find the 22" cell is a documentation-based judgement, not a result. The one
   exception to "no reading" is that this task read web pages — that is the task.
2. **The 22-vs-23 count is reported, not resolved.** The earlier report's own list names 23 symbols
   under a "22" sentence with a "25" total. Resolving it needs `GameDefine.Steam.cs` or the patched
   `BmSDK.dll` immediate count; that is an address-table audit, not a tool survey, so it is left as
   UNKNOWN §5.4 rather than guessed. The operator sees both numbers and the reason.
3. **The six live values were not read.** The test ban forbids attaching, so §4 is a route with an
   oracle, not a result. It is written so the next session can execute step 1 without any of the 22.
4. **One URL is dead** (`ItsBrank/UE3SDKGenerator`, HTTP 404 at 2026-11-08); its README quotes are
   taken from the search index and the GitHubHelp mirror, which are labelled as such.
5. **The Discord and the `cberdejo` fork are UNKNOWN, not skipped for convenience** — there is no
   fetchable artifact for either.
