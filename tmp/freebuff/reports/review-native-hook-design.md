# Adversarial review — `reports/native-hook-design-jc3mp-contract.md`

**STATUS: done.** Every address the design cites was re-checked against
`D:/Games/Just Cause 3/JustCause3.exe` (read-only), every claim about `jc3-console-thingy` was checked against its
source with file:line, and the design was compared with `ROADMAP.md` RB-4…RB-9. **The design was not edited.**
Five findings are real (two wrong, three mis-tagged), six claims are guesses presented as knowledge, and the
design forgets four of the ROADMAP's named blockers. §6 is the short correction briefs **7981-7987** must read.

Tools run (nothing else executed; no game launch, no compile):

```
$ python Tools/scripts/exe_addr_check.py "E:/Modding/_tools/jc3-console-thingy"      # 23 literals
$ python Tools/scripts/jc3_rtti_map.py --check
PASS: 690 vehicle rows and 6 literal hits recompute identically from 51083264 bytes
$ python - <<'PY'  # PE import table + .pdata + RTTI strings of D:/Games/Just Cause 3/JustCause3.exe
```

---

## 1. Claims that hold (with the evidence line)

### 1.1 The console-thingy addresses (all of them)

`exe_addr_check.py` resolves **every** `0x14…` literal in console-thingy's `src/`; the design's table is a subset.
Section, kind and bytes, verbatim:

```
0x14000B284 .text code 75 07 e8 27 68 ff ff eb      (focus gained — call site, e8 at +2)
0x14000B291 .text code 95 c2 e8 da 68 ff ff 48      (focus lost  — call site, e8 at +2)
0x1400719D0 .text code cc cc 48 89 5c 24 18 55      (event runner — prologue)
0x1400B8A22 .text code 00 00 e8 f9 1d 8a 01 90      (flip/present — call site, e8 at +2)
0x14052CD20 .text code cc cc 48 89 5c 24 08 57      (world time setter — prologue)
0x140E97DA0 .text code cc cc 48 8b c4 57 48 81      (Spawn — prologue)
0x140EBFBD7 .text code 8b cf e8 44 4e 17 ff 48      (property lookup — call site, e8 at +2)
0x140F46280 .text code cc cc 40 53 48 83 ec 70      (IsIntroSequenceComplete)
0x140F46300 .text code 5b c3 40 53 48 83 ec 70      (IsIntroMovieComplete)
0x142305658 .rdata data 00 00 41 76 61 6c 61 6e   (u32 = 0x6c617641 = "Aval")
0x142D39DE8 .data 0x142D6F8AC .data 0x142E2B6F0/6F8/700 .data 0x142ED0E78 .data 0x142F17250 .data
0x142F18998 .data 0x142F3407A .data 0x142F36958 .data 0x142E22A18 .data (bss)
```

| design claim | evidence | verdict |
|---|---|---|
| `CSpawnSystem` instance `**(void***)0x142F18998` | `src/game/spawn_system.h:17` | holds |
| `Spawn` at `0x140E97DA0`, flags `0x2013C` | `src/game/spawn_system.h:32` | holds |
| transform from `CCharacter::m_transform`, translation from `m_aimPos` | `src/commands/spawn.h:46-55` | holds |
| model-name lookup hook at `0x140EBFBD7`, key `0xF71C2A21` | `src/commands/spawn.h:35`, `:38` | holds |
| event runner `0x1400719D0(argument, nullptr)` | `src/commands/event.h:41` | holds |
| world clock `0x142F17250`, setter `0x14052CD20`, timescale `+0x88` | `src/commands/world.h:20`, `:27`, `:31` | holds |
| flip site `0x1400B8A22` | `src/main.cpp:92` | holds |
| `CGraphicsEngine` `**(…)0x142E2B6F0`, `+0xEB0` → `HDevice_t*`; device `+0x28`; screen `+0x1A0/+0x1A4` | `graphics_engine.h:17-18`; `device.h:11-15` (`0x28+8+0x170=0x1A0`) | holds |
| input manager `**(…)0x142E2B6F8`, `+0x70` | `input_manager.h:15-16` | holds |
| UI manager `**(…)0x142E2B700`, `+0x213` | `ui_manager.h:15-16` | holds |
| debug renderer `**(…)0x142D39DE8`, `+0x10` | `debug_renderer.h:47-48` | holds |
| clock `**(…)0x142ED0E78`, `+0x2C` | `clock.h:15-16` | holds |
| game state `0x142D6F8AC == 15` | `main.cpp:23` | holds |
| HWND `0x142E22A18` | `main.cpp:75`, `:144` | holds |
| build gate `0x142305658 == 0x6c617641` | `main.cpp:132` | holds |
| quickstart `0x142F3407A`, intro patches `0x140F46280/0x140F46300` | `main.cpp:66-72` | holds |
| player chain `0x142F36958 → +0x48 → +0x128 → +0x100 → +0x2830` | `player_manager.h:35-36`, `:11-13`; `player.h:20-23`; `character.h:11-12` | holds |
| `CDebugRenderer` primitives `DebugLine`/`DebugTriangleFilled` | `debug_renderer.h:33-52` | holds |
| console-thingy is an `xinput9_1_0` proxy | `src/xinput9_1_0.h` exports; `main.cpp:118-127` loads the system DLL | holds — and **stronger than the design says** (see §1.2) |
| `CGameObject` is only a virtual dtor there | `game/game_object.h:6` | holds |
| MIT © 2018 Aaron K; CitizenFX notice in `hooking.h` | `LICENSE:1-3`; `hooking/hooking.h:5-24` | holds |

Extra addresses the design inherited from the earlier exe study, verified here for the first time:

| address | check | verdict |
|---|---|---|
| `0x1409DBE40` (`CDespawnVolume`) | `.pdata` function start, size **62** | holds exactly |
| `0x14061BC60` (`CEntityObject`) | `.pdata` function start, size **115** | holds exactly |

### 1.2 One claim the design under-states (and should have used)

The design asserts the XInput proxy works because console-thingy ships as `xinput9_1_0.dll`. The **import table of
this exe** proves it: the DLL list contains `XINPUT9_1_0.dll` (and `DINPUT8.dll`, `d3d11.dll`, `d3d9.dll`).
So the game calls `XInputGetState` through exactly the module console-thingy proxies — the premise is not just
plausible, it is decoded from the import directory (`import rva 0x2d31d18`, 27 DLLs). The design's RB-5 "yes" is
therefore correct on the strongest possible evidence, but cites the weakest.

### 1.3 RTTI exists, so the method in E9 is half sound

`3575` distinct `.?AV…@@` names are in the file, including `.?AVCPfxCar@@` (1), `.?AVCVehicle@@` (1),
`.?AVCPfxVehicle@@` (1), `.?AVCCharacter@@` (1). `jc3_rtti_map.py --check` recomputes 690 vehicle rows and 6
literal hits from the same bytes and passes.

---

## 2. Claims that are wrong (with proof)

### W1 — "the nine function addresses land on prologues, the four that are call sites land on an e8"

There are **nine `.text` literals**, of which **five are function starts** and **four are call sites**
(`0x14000B284`, `0x14000B291`, `0x1400B8A22`, `0x140EBFBD7` — each has `e8` as its third byte; the other five start
with a prologue: `48 89 5c 24…`, `48 8b c4…`, `40 53…`). The sentence counts the same nine twice. As written it
implies nine function starts plus four call sites = thirteen sites, which do not exist.

### W2 — "console-thingy already drives `Input::EnableInput` off it"

Direction is reversed. `Input::EnableInput` **writes** both flags:
`jc::CUIManager::instance().m_active = !toggle;` with the comment `// toggle hud`, and
`CInputDeviceManager::instance().m_hasFocus = !toggle;` (`src/input.cpp:31-40`). `FocusChanged` also writes
`m_hasFocus = false` on focus regain (`src/input.cpp:14-26`), and `main.cpp:23-40` calls `EnableInput(false)` when
the clock is paused. Nothing in console-thingy *reads* the flag to decide anything — the game reads it, which is the
whole mechanism.

Two consequences the review should carry forward: the design's RB-5 row is right about the mechanism but wrong about
who drives it, and its RB-6 row marks `CUIManager::m_active` as "UNKNOWN — one write test (E7)" when
console-thingy's own comment and shipped behaviour already demonstrate it hides the HUD. E7 is a **confirmation**,
not a discovery.

### W3 — E9's RTTI lookup name for `SLandSteering` does not exist

`E9` proposes searching `.rdata` for `.?AVCPfxCar@@` / `.?AVSLandSteering@@`. In this exe:

```
.?AVCPfxCar@@        1        land_steering        1
.?AVCVehicle@@       1        custom_land_global   0
.?AVCPfxVehicle@@    1        SLandSteering        0
.?AVSLandSteering@@  0        .?AVRVehicle@@       0
```

`SLandSteering` has **zero** occurrences in any form, and `custom_land_global` zero. So the RTTI half is valid for
`CPfxCar`/`CVehicle` and **invalid for `SLandSteering`**; the string half is valid only for `land_steering` (one
hit). A brief that follows E9 literally will search for a name the exe does not contain and conclude the class is
absent.

### W4 — §2 reads as if the whole address table was verified; one cited address is not in the exe at all

`0x1434CD7E0` (the 2017 `SLandSteering` resolver from `jc3-handling-editor`) maps to **no section** of this exe:
the RVA is outside `.text/.rdata/.data/.pdata/.tls/.rsrc/.reloc`. The design tags it UNKNOWN in §3/§4, which is
correct, but §2's sentence "every literal resolves … so the operator's claim holds for this exe" is scoped to
console-thingy's literals while the document reads as a whole-table guarantee. The distinction matters to a brief
that copies A25.

---

## 3. Claims stated as known that are really guesses

| # | claim in the design | why it is a guess | what would make it evidence |
|---|---|---|---|
| G1 | A5 "event runner (`ply.vehicle.*`, `spawn`, teleport-ish events)" | the only decoded hints are the 19 strings at `commands/event.h:8-26`, and the only vehicle one is `ply.vehicle.burn`. `0x1400719D0` takes an arbitrary string; nothing shows `spawn`, `enter`, `exit` or a teleport event exists | call it with each name and watch, or find the event-name table in the exe |
| G2 | §3 RB-4 "`ply.vehicle.*` family" used for re-seat/enter/exit | one member of that family is decoded; a family is extrapolated | same experiment as G1 |
| G3 | "expect every `+0x3EC`-class offset to have moved" | the design itself shows the structures came from a 2017 build, but no measurement shows a shift; UE-style layouts often keep member offsets across builds | re-derive one offset (e.g. `topSpeed`) by value and compare |
| G4 | A16 "`CPlayer + 0x…`→`m_aimControl` … aim pos `+0x14C`" tagged **known (structure)** while the middle offset is left as `0x…` | the number is not missing, it is derivable: `player.h:20-23` gives `_pad[0x100]` + `m_character` (8) + `_pad2[0x40]` = **`m_aimControl` at +0x148**, so `m_aimPos` is at `+0x148 → +0x14C` | arithmetic from the header; tag it known, or state the derivation |
| G5 | §7 "a `--safe` build that only *reads* … cannot corrupt a save" | it still injects a DLL, hooks D3D11 and reads/writes the game's heap-adjacent memory; a crash during a save write can corrupt a save regardless of intent | drop the guarantee; say "does not write game state" |
| G6 | §3 RB-4 "re-seat … fire the enter event … or the despawn path" presented as two routes | both rest on G1/G2 and on the UNKNOWN despawn | experiment E6 |

---

## 4. What the design forgot from ROADMAP RB-4…RB-9

Quoting `ROADMAP.md` §4 (lines 85-90) and its probe table (lines 103-108):

| row | ROADMAP says | what the design misses |
|---|---|---|
| **RB-4** | "**0 selectors in 52 module types**; a second entity via Rebel Drop **works but arrives at rest**"; blocks "battle mode, battle weapons, battle HUD, battle audio/**camera**/lamps, D-2" | never mentions the Rebel Drop baseline (P5: "does a Rebel Drop spawn carry speed/health?") that the hook must beat, never mentions the **camera/lamp handoff** after the swap, never mentions **P6** (`USE_VEHICLE_MOD`, the mode trigger), and does not say what happens to the old entity's *seat* if despawn (E2) fails — i.e. the fallback is the arrival-at-rest swap the design calls half-carried without naming |
| **RB-5** | "Input is a **global keymap** (`settings/keymap_gamepad.bin`); **no keymap writer**; LT-hold / A-hold-charge are not expressible as decoded; whether a **dropzone keymap is honoured** is UNKNOWN"; blocks D-11, every weapon bind, eject | the design replaces the keymap with XInput reading but never says so: it does not mention the keymap file, P2, or that a native hook makes the keymap writer unnecessary for *our* inputs while leaving **vanilla bindings and D-11** untouched; "every weapon bind" is absent |
| **RB-6** | "**No Scaleform writer**: no tool recompiles `hud.gfx`; whether a **private copy loads** is UNKNOWN; the **entity→HUD caller is native**"; blocks all of L7 | the design proposes an overlay and `m_active` but never mentions `hud.gfx`, P3, or the entity→HUD caller — and that caller is exactly what makes battle-HUD *elements* (weapon icons, lock reticle) need either a Scaleform route or a full reimplementation. L7 is not mentioned at all |
| **RB-7** | "No runtime oracle (G3-07 open; `jc3oracle.py` absent)"; blocks "**collision truth, colour truth, live mass**" | the design's RB-7 covers position/rotation/health/velocity and calls that the oracle. It never connects **live mass** (which its own handling table lists as `CVehicle.mass`), never mentions **collision truth** (P1: does the game read our `batmobile.physicsc`?), and never mentions **colour truth** (RB-12). Those are the three questions RB-7 exists to answer |
| **RB-9** | "No script-logic carrier found for 'when X do Y' (water teleport, flip thrusters, regen timer, summon/homing); **`.btc` bodies undecoded**" | the four behaviours are covered, but the design never says that the RB-9 question was *carrier-shaped* (a script graph, `.btc`, the 11 teleport graphs from `reports/mode-toggle-runtime-swap.md`) and that a native tick replaces it. It also repeats the minimap Y-heuristic as "the JC3 side's rule", which is a JC3 file's display convention, not a water query |

---

## 5. Small corrections that do not change the verdict

* §2's "23 literals" is right, but the count sentence inside it (W1) must be `5 function starts + 4 call sites`.
* §3 RB-6's claim that the debug-renderer vtable "has `DebugLine`, `DebugTriangleFilled`" holds
  (`debug_renderer.h:33-40`), but the class is `PrimitiveRendererImpl`, not the renderer's own vtable — call it by
  name to avoid a wrong vtable assumption.
* §6 says jitasm and libudis86 "ship under `deps/`; each keeps its own BSD-style licence file". `deps/libudis86`
  exists with sources and **no licence file in that directory**; `deps/jitasm` is **not a directory** — `jitasm.h`
  lives in `src/hooking/`. Re-check before vendoring; the claim as written is not supported by the tree.
* §1's "console-thingy supplies … an XInput proxy (gamepad read, the exact thing JC3MP did not expose)" is right and
  now proven by the import table (§1.2) — cite it.

---

## 6. Correction brief — for briefs 7981-7987 (read this instead of the four lines above)

1. **`0x1434CD7E0` does not exist in this exe.** It maps to no section. Do not use it, and do not treat the design's
   §2 as a whole-table verification: §2 covers console-thingy's 23 literals only, and those all pass.
2. **`.?AVSLandSteering@@` is not in the exe (0 occurrences); `custom_land_global` is not either.** For the handling
   re-find use `.?AVCPfxCar@@` (1 hit), `.?AVCVehicle@@` (1), `.?AVCPfxVehicle@@` (1), and the plain string
   `land_steering` (1 hit). Anything that searches for `SLandSteering` will find nothing and must not conclude the
   class is absent.
3. **`Input::EnableInput` writes the flags, it is not driven by them** (`input.cpp:31-40`). The game reads
   `CInputDeviceManager::m_hasFocus`; console-thingy sets it. And `CUIManager::m_active` is *already demonstrated*
   to toggle the HUD by console-thingy (`input.cpp:37`, comment `// toggle hud`) — E7 is a confirmation, not a
   discovery.
4. **The XInput premise is proven, not assumed**: the exe imports `XINPUT9_1_0.dll` (27-DLL import table). RB-5's
   gamepad read may be built on it.
5. **Do not assume any event name beyond `ply.vehicle.burn`.** `0x1400719D0` accepts arbitrary strings; no enter,
   exit, spawn or teleport event names are decoded. Treat RB-4's re-seat as UNKNOWN until tested.
6. **`0x2013C`, `0xF71C2A21`, `0x6c617641` are constants, not addresses** — they will not appear in an address map
   and `exe_addr_check.py` is right to ignore them.

---

## 7. Limits of this review

* Address checks are static (PE sections, `.pdata` starts, import table, string census). No process was attached, so
  nothing here proves a function *behaves* as the design assumes — only that the address is a real site.
* The RTTI census is exact-string only; a class whose RTTI was stripped is reported absent even if its vtable
  exists. That is why W3 is stated as "the lookup name is wrong", not "the class does not exist".
* Console-thingy was read at v1.1 as installed; no git history was inspected, so "v1.1 changed this" claims are not
  made.
* Me neither: the design's own UNKNOWNs (despawn, vehicle transform/velocity/health, `.ee` acceptance) were not
  resolved here — they remain the experiments the design lists.
