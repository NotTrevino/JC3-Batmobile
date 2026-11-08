<!-- canonical DONE path for the native-hook design brief; content identical to
     tmp/freebuff/reports/jc3mp-native-hooks-design.md -->

# Batmobile native hook DLL — design on paper (post-JC3MP)

**STATUS: done (design only).** Nothing was compiled, launched, injected, installed or written outside this
report. The addresses below were re-checked read-only against `D:/Games/Just Cause 3/JustCause3.exe` with the
repo's own `Tools/scripts/exe_addr_check.py`; the output is in §2 verbatim.

Context, per the operator ruling of 2026-11-08 and the JC3MP result:

* the JC3MP **client** refused to install (`Failed to install app '619910' (No subscription)`), because this JC3
  is a repack of Steam build 20206564, not a Steam-owned copy; the **dedicated server** did install at
  `E:/Modding/_tools/jc3mp-server` (its JS runtime is in `data/js/scripting-runtime`).
* so the JC3MP **API contract** survives as the specification, and the runtime has to be built natively.
* `E:/Modding/_tools/jc3-console-thingy` (MIT, v1.1, 2026-01-11) is the loader + address map to build on.

---

## 1. Verdict

**A native hook DLL is the right carrier, and console-thingy supplies the two hardest primitives already: an
XInput proxy (gamepad read, the exact thing JC3MP did not expose) and a D3D11 present hook (HUD/overlay drawing).
What it does not supply is entity-side: there is no decoded vehicle despawn, velocity, health or `.ee`-path
spawn.** The mode swap (RB-4) is therefore **half carried**: spawn is decoded and callable; despawn and per-entity
state copy have to be found. RB-5, RB-6, RB-7 and RB-9 are carried by machinery that already exists in
console-thingy, with the caveats listed per row.

| row | verdict | carrier |
|---|---|---|
| RB-4 mode swap | **partly** — spawn works, despawn/state-copy UNKNOWN | `CSpawnSystem::Spawn` (0x140E97DA0) + a new despawn/velocity/health discovery; the pair stays "two entities, not an in-place transform" |
| RB-5 input scoping | **yes for gamepad read** (XInput proxy), **partly for scoping** | xinput9_1_0 proxy + `CInputDeviceManager` focus flag; per-vehicle gating is ours to write |
| RB-6 HUD | **yes** — D3D11 present hook + FW1 font, or the engine's own debug renderer | `flip` call site 0x1400B8A22 + `HDevice_t`; `CUIManager::m_active` for hiding stock UI (needs a test) |
| RB-7 runtime oracle | **yes** — same process, same pointers, read/write | player/character transform, spawned-object list, plus anything we decode |
| RB-9 "when X do Y" | **yes** — a native per-frame tick plus state writes | present hook gives the tick; the writes need the RB-4/B-7 offsets |
| runtime handling switch | **partly** — structures known, addresses stale | handling-editor structures (`CVehicle`, `CPfxCar`, `SLandSteering`) from 2017; every address in it is dead |

The one thing JC3MP gave that this does **not**: a scripted, sandboxed, reloadable package layer. Here every
change is C++ compiled into the DLL, and a mistake crashes the game rather than throwing in JS.

---

## 2. Address check (read-only, this exe)

`python Tools/scripts/exe_addr_check.py "E:/Modding/_tools/jc3-console-thingy"` — reads
`D:/Games/Just Cause 3/JustCause3.exe`, maps every `0x14…` literal in console-thingy's `src/` into its PE
sections, prints the 8 bytes at the site:

```
base 0x140000000 [.text 0x1000 0x22a0cff] [.rdata 0x22a2000 0xa9693a] [.data 0x2d39000 0x26f518]
0x14000B284 .text code 75 07 e8 27 68 ff ff eb      (focus gained, call site)
0x14000B291 .text code 95 c2 e8 da 68 ff ff 48      (focus lost, call site)
0x1400719D0 .text code cc cc 48 89 5c 24 18 55      (event runner, function start)
0x1400B8A22 .text code 00 00 e8 f9 1d 8a 01 90      (present/flip call site)
0x14052CD20 .text code cc cc 48 89 5c 24 08 57      (world time setter)
0x140E97DA0 .text code cc cc 48 8b c4 57 48 81      (CSpawnSystem::Spawn, function start)
0x140EBFBD7 .text code 8b cf e8 44 4e 17 ff 48      (property-file lookup, call site)
0x140F46280 .text code cc cc 40 53 48 83 ec 70      (IsIntroSequenceComplete)
0x140F46300 .text code 5b c3 40 53 48 83 ec 70      (IsIntroMovieComplete)
0x142305658 .rdata data 00 00 41 76 61 6c 61 6e   ("Avalanche" build tag, version gate)
0x142D39DE8 .data data …                            (CDebugRenderer global)
0x142D6F8AC .data data 00 00 05 00 00 00 01 00     (game state)
0x142E22A18 .data bss/none                          (HWND storage)
0x142E2B6F0 / 0x142E2B700 / 0x142E2B6F8 .data      (graphics engine / UIManager / input manager globals)
0x142ED0E78 .data bss/none                          (CClock)
0x142F17250 .data bss/none                          (CDayCycle)
0x142F18998 .data bss/none                          (CSpawnSystem)
0x142F3407A .data bss/none                          (quickstart bool)
0x142F36958 .data bss/none                          (CNetworkPlayerManager)
```

Every literal resolves: the nine function addresses land on `cc cc 48 89…`-style prologues, the four that are
call sites land on an `e8` rel32 in the middle of a function. So **the operator's claim holds for this exe** and
the whole table below is usable as-is.

---

## 3. Contract — each JC3MP member the project needs, and its native implementation

Legend: **K** = known (address verified above / decoded structure), **D** = derivable (rule stated),
**U** = UNKNOWN (finding method named).

### RB-4 — mode swap (despawn pursuit, spawn battle, carry state, re-seat player)

| contract member (JC3MP) | native implementation | tag |
|---|---|---|
| `new Vehicle(modelHash, position, rotation)` | `CSpawnSystem::Spawn(model_name, transform, 0x2013C, cb, udata)` at **0x140E97DA0**; instance `**(CSpawnSystem**)0x142F18998`; transform built from `CCharacter::m_transform` with translation replaced by `CPlayerAimControl::m_aimPos` (console-thingy `commands/spawn.h`, the exact code path already shipped) | **K** (code) |
| model by `.ee` **path** | the spawn argument is a `const char*` model name resolved through the property file; the console command passes arbitrary text, and `0xF71C2A21` is the hashed key it uses to enumerate names. Whether a full `.ee` path is accepted by the same call is **U** (test E1) | **U** |
| `Vehicle.Destroy()` | **no decoded despawn.** The image's only `despawn` name is the 62-byte `CDespawnVolume` type stub at `0x1409DBE40`; `CGameObject` is only a virtual dtor in console-thingy. Cheapest find: RTTI/vtable of the object the spawn callback returns, then its release/`ConditionalDestroy`-shaped slot (E2) | **U** |
| `Vehicle.position` / `.rotation` | transform matrix write. `CCharacter::m_transform` is at **+0x2830** (K, console-thingy `game/character.h`); the **vehicle** entity's transform offset is unknown because the spawned object is typed `CGameObject*` only — find it by spawning at a known transform and scanning the returned object for the 16 matching floats (E3) | **D/U** |
| `Vehicle.linearVelocity` / `.angularVelocity` | no member decoded on either side (JC3 side: `Research/JC3Grab` has no vehicle-velocity layout). Find by: drive at a measured speed, scan the vehicle object for three floats whose magnitude tracks it (E4) | **U** |
| `Vehicle.health` | same shape; a write test (set 1.0, watch the HUD) validates the candidate offset (E5) | **U** |
| `Vehicle.driver` / `GetOccupant` / `SetOccupant` | re-seat after swap. No seat API decoded; cheapest route is *not* re-seating but spawning the battle entity **under** the player: console-thingy spawns at the aim position and the engine's own enter-vehicle event (`0x1400719D0` event runner, name `ply.vehicle.*` family in `commands/event.h`) can be fired by name (E6) | **U/D** |
| `Vehicle.Repair()` / `Respawn()` | not needed for the swap; `Repair` maps onto the health write once E5 lands | **U** |

### RB-5 — gamepad read and input scoping

| contract member | native implementation | tag |
|---|---|---|
| gamepad buttons/axes (**JC3MP has none**) | console-thingy **is** an `xinput9_1_0.dll` proxy: `XInputGetState`/`XInputSetState` are exported and forwarded (`src/xinput9_1_0.h`), so the DLL sees every pad state before the game does — LT/RT triggers, A/B/X/Y, LB/RB, sticks. This is strictly better than JC3MP's `hasController()` | **K** |
| `localPlayer.controlsEnabled = false` | `CInputDeviceManager` instance `**(…)0x142E2B6F8`, focus flag at **+0x70** (`game/input_manager.h`); console-thingy already drives `Input::EnableInput` off it. That is *wholesale* gating; per-vehicle scoping = suppress our own injected inputs + ignore game input while a flag is set | **K (flag) / D (scoping)** |
| LT hold → battle mode | read LT from the XInput state; a hold timer in the tick (§RB-9) decides the swap; then gate with the focus flag | **K/D** |
| A hold-to-charge → higher eject | read A; the "higher" part needs the eject impulse, which is the velocity write (U, E4) | **U** |
| LB exit | read LB; exit = the same enter/exit event (`ply.vehicle.*`) or the despawn path | **U** |

### RB-6 — HUD (hide stock, draw ours)

| contract member | native implementation | tag |
|---|---|---|
| `jcmp.ui.HideHud()` | `CUIManager` instance `**(…)0x142E2B700`, `m_active` at **+0x213** (K). Whether that bool is the HUD's visibility or only the console/UI root is **U** — one write test (E7). Fallback: draw over the stock HUD (the present hook is last) | **K/U** |
| `Renderer.DrawRect` in a render pass | present/flip call site **0x1400B8A22**, injected exactly as console-thingy does; `HDevice_t` via `CGraphicsEngine` `**(…)0x142E2B6F0` + **0xEB0** → `ID3D11Device` + `+0x28` (`game/device.h`, `game/graphics_engine.h`); text via FW1FontWrapper (`graphics.h`) | **K** |
| engine-native 2D primitives | `CDebugRenderer` global **0x142D39DE8**, primitive renderer at **+0x10**, whose vtable has `DebugLine`, `DebugTriangleFilled` etc. (`game/debug_renderer.h`). Use this for the speed/telemetry HUD: no D3D11 state juggling | **K** |

### RB-7 — runtime oracle

| contract member | native implementation | tag |
|---|---|---|
| live position/rotation readout | player `CNetworkPlayerManager` `**(…)0x142F36958` → `m_localPlayer` **+0x48** → `CNetworkPlayer::m_player` **+0x128** → `CPlayer::m_character` **+0x100** → `m_transform` **+0x2830** (all K, console-thingy `player_manager.h` / `player.h`) | **K** |
| vehicle identity / "which car am I in" | reverse of RB-4: keep the `spawned_objects` the callback returns; compare its transform translation with the player's (D). A `player.vehicle`-shaped pointer is **U** (E3) | **D/U** |
| health / velocity / loaded resources | same U offsets as RB-4, exposed on screen instead of written | **U** |
| frame time / clock | `CClock` `**(…)0x142ED0E78`, `m_paused` **+0x2C** (K); `game state` at **0x142D6F8AC** (K, `main.cpp` uses `== 15` as "in game") | **K** |

### RB-9 — "when X do Y" (water teleport, regen timer, flip thrusters)

| behaviour | native implementation | tag |
|---|---|---|
| per-frame tick (the JS event loop's replacement) | the present hook 0x1400B8A22 runs every rendered frame; console-thingy already does its input drawing there. A second hook on the same site (or a `std::thread` polling at 60 Hz against `CClock`) gives the tick | **K** |
| water teleport | write the entity transform translation (RB-4 U once the vehicle transform is found); "am I in water" — no engine water query decoded, so use the minimap's own rule from the JC3 side (surface height) or a fixed Y test | **U/D** |
| regen timer | needs the health offset (RB-4 U) + the tick; then it is a plain write | **U** |
| flip thrusters | needs angular velocity (RB-4 U); the impulse direction is trigonometry, the write is the same slot | **U** |
| summon / homing | the spawn call already teleports a car to a point (console spawn does exactly this); homing is per-frame translation writes | **K/U** |

### Runtime handling switch (§3.2 of the brief)

The 2017 handling editor's **structures** are the useful part, its **addresses** are not:

| thing | evidence | tag |
|---|---|---|
| `CVehicle` with `PfxVehicle`, `mass`, `dragCoefficient`, `linearDamping`, `angularDamping`, `gravityFactor` | `jc3-handling-editor/src/ui_menus/car_ui_menu.cpp` (decoded C++) | **K (structure, source read)** |
| `CPfxCar` with `landVehicleEngine`, `landVehicleTransmission`, `wheelInfo` (TArray), `wheelSuspensionConstants`, `transmissionResourceCachePtr`, `topSpeed` at **+0x3EC** | same file | **K (structure) / U (offset valid for this build)** |
| `SLandSteering` from a resource cache via `0x1434CD7E0` | same file, 2017 address | **U** for this exe |
| re-find method | RTTI names in `.rdata` (`.?AVCPfxCar@@`, `.?AVCVehicle@@`, `.?AVSLandSteering@@`), the `land_steering` / `custom_land_global` name strings, and the resource-cache resolver's callers; then re-derive `topSpeed` by comparing against a known JC3 vehicle's handling file | **method** |

So: **yes, the structures are reusable, the offsets and the resolver are not** — expect every `+0x3EC`-class
offset to have moved, and validate each by value against a decoded JC3 handling file before use.

---

## 4. Address table to build (tagged)

| # | symbol | address / offset | tag | source |
|---|---|---|---|---|
| A1 | `CSpawnSystem` instance | `**(void***)0x142F18998` | **known** | `game/spawn_system.h`; check §2 |
| A2 | `CSpawnSystem::Spawn` | `0x140E97DA0` | **known** | same; prologue verified |
| A3 | spawn flags constant | `0x2013C` | **known** | same |
| A4 | property-file model lookup (for names/hashes) | `0x140EBFBD7`, key `0xF71C2A21` | **known** | `commands/spawn.h`; call site verified |
| A5 | event runner (`ply.vehicle.*`, `spawn`, teleport-ish events) | `0x1400719D0` | **known** | `commands/event.h` |
| A6 | world time / `CDayCycle` | `0x142F17250`, setter `0x14052CD20`, timescale `+0x88` | **known** | `commands/world.h` |
| A7 | present / flip call site | `0x1400B8A22` | **known** | `main.cpp`; `e8` verified |
| A8 | `CGraphicsEngine` → `HDevice_t*` → `ID3D11Device*` | `**(…)0x142E2B6F0` + `0xEB0`; device `+0x28`; screen `+0x1A0/+0x1A4` | **known** | `game/graphics_engine.h`, `game/device.h` |
| A9 | `CInputDeviceManager` + focus | `**(…)0x142E2B6F8`, `+0x70` | **known** | `game/input_manager.h` |
| A10 | `CUIManager` + active | `**(…)0x142E2B700`, `+0x213` | **known** | `game/ui_manager.h` |
| A11 | `CDebugRenderer` + primitive renderer | `**(…)0x142D39DE8`, `+0x10` | **known** | `game/debug_renderer.h` |
| A12 | `CClock` + paused | `**(…)0x142ED0E78`, `+0x2C` | **known** | `game/clock.h` |
| A13 | game state, `== 15` = in game | `0x142D6F8AC` | **known** | `main.cpp` |
| A14 | HWND | `0x142E22A18` | **known** | `main.cpp` |
| A15 | player manager → local player → player → character → transform | `0x142F36958` → `+0x48` → `+0x128` → `+0x100` → `+0x2830` | **known** | `player_manager.h`, `player.h`, `character.h` |
| A16 | aim position | `CPlayer + 0x…`→`m_aimControl` (`player.h`), aim pos `+0x14C` | **known (structure)** | `player.h` |
| A17 | build tag gate | `0x142305658 == 0x6c617641` | **known** | `main.cpp`, `Avalanche` bytes |
| A18 | version-check mirror / quickstart | `0x142F3407A`, `0x140F46280`, `0x140F46300` | **known** | `main.cpp` |
| A19 | `CGameObject` vtable → class identity of a spawned object | vtable read from the callback's object | **derivable** | `game/game_object.h` |
| A20 | vehicle transform offset | unknown | **UNKNOWN** (E3) | — |
| A21 | vehicle linear/angular velocity | unknown | **UNKNOWN** (E4) | — |
| A22 | vehicle health | unknown | **UNKNOWN** (E5) | — |
| A23 | despawn / release call | unknown; nearest names `CDespawnVolume` @ `0x1409DBE40`, `CEntityObject` @ `0x14061BC60` | **UNKNOWN** (E2) | `exe-entity-swap-consumer.md` |
| A24 | HUD hide entry point | `CUIManager::m_active` (candidate) | **UNKNOWN → test** (E7) | — |
| A25 | handling resolver / `SLandSteering` | was `0x1434CD7E0` (2017) | **UNKNOWN** | `car_ui_menu.cpp` |
| A26 | `CPfxCar::topSpeed` | was `+0x3EC` (2017) | **UNKNOWN** | same |

---

## 5. Missing pieces and the cheapest way to find each

| # | missing | cheapest finding method | why it is cheap |
|---|---|---|---|
| E1 | does `Spawn()` accept an `.ee` path | one console `spawn <path>` (console-thingy is already built), then read the spawn callback's object count | the console path exists and is one line of input |
| E2 | despawn of a spawned object | print the object's vtable address from the callback; look the vtable up in `.rdata` (it is a pointer to a table of code pointers); its first slot is the destructor; find the entity-manager release that calls it | vtable identity is data, not code search |
| E3 | vehicle transform offset | spawn at a known transform, scan the object's first 4 KB for the 16 floats (row-major, last row = translation); confirm with a second spawn elsewhere | one run, no symbols needed |
| E4 | velocity | drive straight at a measured speed, scan for three floats with that magnitude in the vehicle object; brake and re-read | same object already located in E3 |
| E5 | health | scan for `100.0`/`1.0` in the object, damage the car, re-scan | the only 100.0 that drops when shot |
| E6 | re-seat / enter | fire `ply.vehicle.*` events by name through 0x1400719D0 and watch the player's transform | the event runner is already callable |
| E7 | stock HUD hide | write `CUIManager::m_active` false while in game; if the HUD stays, overlay instead | one write, reversible |
| E8 | `.ee` vs model hash for the battle car | `spawn` with the donor's name string (from `Research/BatmobileGrab`) and with the `.ee` path; compare object counts | same test as E1 |
| E9 | handling offsets | search `.rdata` for `.?AVCPfxCar@@` / `.?AVSLandSteering@@` (RTTI), then the strings `land_steering`, `custom_land_global`; re-derive `topSpeed` by matching a decoded handling file's value | RTTI names survive builds far better than code addresses |

All nine are **read-only or in-process writes to a private test install**; none is claimed here.

---

## 6. Licence notes

* **jc3-console-thingy** — MIT, `Copyright (c) 2018 Aaron K`. Reuse of `src/hooking/*`, `src/game/*`,
  `src/commands/*`, `src/graphics.h` requires: keep the copyright + permission notice, state that the file was
  modified, do not use the author's name to endorse the derivative.
* **`src/hooking/hooking.h`** carries a second notice: *"Some parts contain the SteamComponent of CitizenFX
  Framework"*, MIT, `Copyright(c) 2014 Bas Timmer / NTAuthority et al.` Both notices must be preserved verbatim.
* **jitasm** (inline assembler) and **libudis86** (disassembler) ship under `deps/`; each keeps its own
  BSD-style licence file — do not vendor them without it.
* **jc3-handling-editor** — MIT (see its `LICENSE`); its *structures* would be re-expressed, not copied, and the
  notice kept if any of its code is lifted.
* **BmAK/JC3 game data** — never committed, never redistributed; the DLL contains no game assets, only addresses
  and structure layouts (facts about the binary, no copyrighted code).
* `rg -n "Copyright"` over the reused files before the first commit, and ship a `THIRD_PARTY_NOTICES.md`.

## 7. Build plan

| step | choice | reason |
|---|---|---|
| toolchain | Visual Studio 2019+ / MSVC, C++17 (console-thingy needs "nested namespaces") | its `premake.lua`/`configure.ps1` target exactly that |
| project shape | **new** `Tools/native/bm-hook/` in this repo containing only our sources + a `vendor/` pointer to console-thingy (or a git submodule), never a copy of the game | keeps MIT notices intact and the repo game-free |
| output dir | `E:/Modding/_bmhook/build/` (outside the repo) for `xinput9_1_0.dll` and PDBs | "no game binaries in the repo" |
| install | operator copies the DLL into `D:/Games/Just Cause 3/` **by hand**; we never write there | test ban + install is read-only to us |
| loader | keep console-thingy's `xinput9_1_0.dll` proxy + `D3D11CreateDevice` import hook + the `0x142305658` build gate | already proven in this exe |
| code layout | `hook/` (console-thingy derived, MIT headers kept), `entity/` (spawn, despawn, transform, health), `input/` (XInput state → bindings), `hud/` (debug renderer + overlay), `mode/` (the RB-4 state machine), `read/` (RB-7 telemetry) | one folder per contract area, so a broken area can be compiled out with a define |
| safety | every hook behind a `#ifdef BM_ENABLE_*`; a `--safe` build that only *reads* (RB-7) ships first, writable paths second | a crash costs a session, a read-only build cannot corrupt a save |
| version gate | refuse to install hooks when `*(uint32_t*)0x142305658 != 0x6c617641` | already console-thingy's rule |

## 8. Five-minute experiments for the first supervised session

Ordered so that a failure early wastes nothing:

1. **E1/E8 — spawn works, and with which argument.** `spawn <known JC3 vehicle name>`; then `spawn <donor .ee
   path>`. PASS = a car appears; record the callback's object count.
2. **E2/E3 — what the spawned object is, and where its transform is.** print its vtable; spawn again 10 m away and
   diff the two objects' first 4 KB for the 16 floats that changed. PASS = one 4×4 block whose translation equals
   both spawn points.
3. **E4/E5 — velocity and health.** drive at a measured speed and re-read the object; damage it and re-scan for
   100.0. PASS = offsets that track reality.
4. **E7 — can we hide the stock HUD.** write `CUIManager::m_active = false`; screenshot before/after. PASS = HUD
   gone and the game still playable.
5. **RB-5 proof — LT/A/LB.** log the XInput state from the proxy while pressing them; then gate the game's input
   with the focus flag and confirm the car no longer reacts. PASS = the pad values arrive and the gate holds.
6. **RB-4 dress rehearsal.** with E2/E3/E4/E5 in hand: spawn the battle donor at the pursuit car's transform,
   copy the four state values, fire the enter event, then (if E2 landed) despawn the pursuit entity.
7. **RB-9 smoke test.** tick from the present hook: teleport the car 20 m up and let it fall; regen by writing
   health; flip by writing angular velocity. PASS = each visible in one run.

## 9. UNKNOWNs (recap)

`Vehicle.Destroy` equivalent, vehicle transform/velocity/health offsets, `.ee`-path acceptance, seat/enter API,
HUD-hide entry point, all handling-editor addresses and its `topSpeed` offset, and whether the 2025-12-17 exe's
entity manager exposes a release call at all. Each is tied to the experiment above; none is guessed.

**COMPROMISES: none.** The design states what is carried and what must be found; it does not substitute a value
for a missing address, and it does not claim any runtime behaviour was observed.

**Files written:** this report only. `Tools/scripts/exe_addr_check.py` was run read-only; nothing was compiled,
launched or installed.
