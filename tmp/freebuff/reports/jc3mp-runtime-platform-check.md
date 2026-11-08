# JC3MP as a runtime platform for RB-4…RB-9 — wheel-reinvention check

STATUS: done (read-only desk research; no download, no install, no game launch)

Scope: ROADMAP §4 RB-4 (runtime mode swap), RB-5 (input scoping), RB-6 (HUD writing),
RB-7 (runtime oracle), RB-9 ("when X do Y" logic). Question asked: does Just Cause 3
Multiplayer (JC3MP, Steam 619910) already ship the runtime that these five rows are
trying to build, and can it run on this operator's install?

Evidence labels follow the project rule: **decoded** = read directly from the named
source; **derived** = rule + inputs; **UNKNOWN** = tried, not found, or not provable
offline.

Note on method: the JC3MP docs are a client-rendered site, so a plain fetch returns
only the page title. The class pages below were read through the `r.jina.ai` text
renderer of the **same canonical URLs** (`https://just-cause.mp/docs/...`); the
canonical URL is what is cited. One route correction found on the way:
`/docs/server/vehicle` is a 404 — the live path is `/docs/server/classes/vehicle`.

---

## 1. Verdict

**JC3MP is a real scripting runtime and it already carries most of what RB-5, RB-6,
RB-7 and RB-9 exist to build. It does not carry the part of RB-4 that lore needs
(the 2-second in-place transform), and it cannot be adopted on this operator's
current install as things stand.**

Per row, in one line each:

| row | carried by JC3MP? | why |
|---|---|---|
| RB-4 runtime mode swap | **partly** | server `new Vehicle(modelHash, pos, rot)` + `Destroy()` + `SetOccupant()` + read/write `linearVelocity`/`angularVelocity`/`health` gives a *two-entity swap with state carried*. No member exists to swap a model in place or play a turret-rise/wheel-reconfigure animation. |
| RB-5 input scoping | **partly** | `jcmp.localPlayer.controlsEnabled` (get/set) disables local control wholesale; `SetAbilityEnabled(hash, bool)` gates individual abilities; keyboard can be captured in a CEF page (`document.onkeydown`). **Gamepad buttons/axes: no member found** — only `jcmp.input.hasController()` (presence). |
| RB-6 HUD writing | **yes, by a different route** | a full-viewport `WebUIWindow` (CEF) + `jcmp.ui.HideHud()` + `Renderer.DrawRect` in `Render`/`GameUpdateRender`/`GameRender`. No Scaleform recompile, no `hud.gfx` copy. |
| RB-7 runtime oracle | **partly** | live readout of position/rotation/velocities/health/`aabb`/camera is carried to the server console and to a WebUI panel. Arbitrary engine reads (mass, material, colour truth) are not exposed: no member. |
| RB-9 "when X do Y" | **yes** | full JS runtime on both sides, timers (`setInterval` in a shipped package), mutable positions/velocities, `jcmp.localPlayer.healthEffects` (a regen-settings object), event bus + `jcmp.network`. |

The decisive caveats, in order of severity:

1. **It is a replacement runtime, not an augment.** Everything above only exists while
   the game is running *as JC3MP* (multiplayer client), not in the single-player
   install the BATMOBILE currently targets. Adopting it re-scopes the product from
   "mod for JC3" to "content pack for a JC3MP server" — an operator decision, and one
   that must be listed under COMPROMISES if taken, per the 2026-11-06 rule.
2. **Ownership.** Steam states the mod requires Just Cause 3 *on Steam*; SteamDB
   records `MustOwnAppToPurchase: Just Cause 3 (225540)`; the mod's own FAQ says
   *"Steam must be running for the server to properly start"*.
3. **The local install is not a Steam-authenticated JC3.** `D:/Games/Just Cause 3`
   holds `steam_api64.dll` (981,144 B, 2025-12-17) **plus** `steam_api64.rne`
   (208,296 B nominal, 2025-12-17) **plus** `steam_emu.ini` (3,300 B). A `steam_emu.ini`
   next to a `.rne` shadow copy is the signature of a Steam-emulator/repack layout,
   not a Steam client install (derived from the listing; the file contents were not
   read and must not be). Whether the JC3MP client boots against that layout is
   **UNKNOWN** and is the single question that decides the whole lead.

So: not a wheel reinvention to be avoided on capability grounds — on capability it
wins on four of five rows. It is blocked on platform/scope, not on API.

---

## 2. API table

Side: **S** = server package, **C** = client package, **W** = WebUI (CEF page).
Access: R = read, W = write.

| member | type | R/W | side | source URL | evidence |
|---|---|---|---|---|---|
| `new Vehicle(modelHash, position, rotation?)` | ctor | W (create) | S | https://just-cause.mp/docs/server/classes/vehicle | decoded — "modelHash is a number, not a model name"; example `new Vehicle(28454791, new Vector3f(-12652, 1115, -4925), new Vector3f())` |
| `Vehicle.position` | Vector3f | R/W | S | same | decoded |
| `Vehicle.rotation` | Vector3f | R/W | S | same | decoded |
| `Vehicle.linearVelocity` | Vector3f | R/W | S | same | decoded |
| `Vehicle.angularVelocity` | Vector3f | R/W | S | same | decoded |
| `Vehicle.health` | number | R/W | S | same | decoded |
| `Vehicle.modelHash` | number | R | S | same | decoded |
| `Vehicle.networkId` | number | R | S | same | decoded |
| `Vehicle.destroyed` | boolean | R | S | same | decoded |
| `Vehicle.driver` | Player | R/W | S | same | decoded |
| `Vehicle.nitroEnabled`, `Vehicle.turboJumpEnabled` | boolean | R/W | S | same | decoded |
| `Vehicle.primaryColor` | number | R/W | S | same | decoded (index, not RGB — see §6) |
| `Vehicle.handling` | VehicleHandling | R | S | same | decoded (member exists; contents not read) |
| `Vehicle.Destroy()` | method | — | S | same | decoded |
| `Vehicle.GetOccupant(seat)` | method | — | S | same | decoded — "Seat 0 is the driver" |
| `Vehicle.SetOccupant(seat, player)` | method | — | S | same | decoded |
| `Vehicle.Repair()`, `Vehicle.Respawn()` | method | — | S | same | decoded |
| `Player.vehicle` | Vehicle | R | S | https://just-cause.mp/docs/server/classes/player | decoded — how a server reads "the vehicle a player is in" |
| `Player.position` / `.rotation` / `.health` | Vector3f / Vector3f / number | R/W | S | same | decoded |
| `Player.invulnerable`, `Player.respawnPosition`, `Player.skin` | bool / Vector3f / string | R/W | S | same | decoded |
| `Player.GiveWeapon(hash, ammo, equip)`, `Player.RemoveWeapon(hash)` | method | — | S | same | decoded |
| `jcmp.localPlayer.position` / `.rotation` | Vector3f | R/W | C | https://just-cause.mp/docs/client/classes/local-player | decoded |
| `jcmp.localPlayer.controlsEnabled` | boolean | R/W | C | same | decoded |
| `jcmp.localPlayer.frozen` | boolean | R/W | C | same | decoded |
| `jcmp.localPlayer.healthEffects` | HealthEffect | R | C | same | decoded — class summary: "Local player health regeneration settings" (https://just-cause.mp/docs/client) |
| `jcmp.localPlayer.SetAbilityEnabled(ability, enabled)` / `IsAbilityEnabled(ability)` | method | — | C | local-player | decoded; ability ids are hashes, e.g. `0xE060F641` = wingsuit |
| `jcmp.localPlayer.camera`, `.wingsuit`, `.baseState`, `.lookAt` | objects / number | R (some W) | C | local-player | decoded |
| local player's current vehicle | — | — | C | https://just-cause.mp/docs/client | **NOT PRESENT** — the client class has no `vehicle` member (see §6) |
| `NetworkVehicle.position` / `.rotation` / `.linearVelocity` / `.angularVelocity` / `.health` / `.maxHealth` / `.aabb` / `.speedKph` / `.engineRPM` / `.gear` / `.type` / `.modelHash` / `.networkId` | mixed | **R only** | C | https://just-cause.mp/docs/client/classes/network-vehicle | decoded |
| `jcmp.vehicles` | Array<NetworkVehicle> | R | C | https://just-cause.mp/docs/client | decoded |
| `jcmp.players` | Array<NetworkPlayer> | R | C | same | decoded |
| `new WebUIWindow(name, url, size)` | ctor | W | C | https://just-cause.mp/docs/client/classes/web-ui-window | decoded; url form `package://<pkg>/...`; example sizes it to `jcmp.viewportSize` |
| `WebUIWindow.autoResize`, `.autoRenderTexture`, `.autoRenderTexture`, `.captureMouseInput`, `.hidden`, `.location`, `.position`, `.size`, `.texture` | mixed | R/W (texture R) | C | same | decoded |
| `WebUIWindow.AddEvent`, `.CallEvent`, `.BringToFront`, `.Destroy`, `.Reload(ignoreCache?)` | method | — | C | same | decoded |
| `jcmp.ui.HideHud()` / `ShowHud()` / `IsHudVisible()` | method | — | C | https://just-cause.mp/docs/client/classes/jcmp-ui-namespace | decoded |
| `jcmp.ui.AddEvent` / `CallEvent` | method | — | C | same | decoded (WebUI bridge) |
| `jcmp.events` (Add/Call/Remove, AddRemoteCallable/CallRemote shims) | EventSystem | — | S/C | https://just-cause.mp/docs/concepts/compatibility | decoded |
| `jcmp.network.AddHandler/Invoke/Broadcast/RemoveHandler/RemoveAll` | NetworkEventSystem | — | S/C/W | same + https://just-cause.mp/docs/changes-since-v1.0.7 | decoded (per-domain matrix on the changes page) |
| `jcmp.world`, `jcmp.settings`, `jcmp.packages`, `jcmp.version`, `jcmp.build`, `jcmp.viewportSize`, `jcmp.print`, `jcmp.printLog` | mixed | R | C | https://just-cause.mp/docs/client | decoded |
| `Renderer.DrawRect` in `Render` / `GameUpdateRender` / `GameRender` | method | — | C | https://just-cause.mp/docs/client | decoded — "Render: 2D overlay pass, positions are screen pixels" |
| `jcmp.input.hasController()` | method | — | W | https://just-cause.mp/docs/webui/globals/jcmp | decoded — "Whether a controller is present" |
| `input-controller-changed` | event | — | W | https://just-cause.mp/docs/changes-since-v1.0.7 | decoded — client sends a boolean on the shared WebUI bridge |
| `jcmp.playerSkins`, `jcmp.ResolvePlayerSkin(skin)`, `jcmp.IsPlayerSkin(skin)` | namespace | — | S | changes-since-v1.0.7 | decoded — a skin may be a short name **or a full `.ee` path** |
| `jcmp.ShowCursor()` / `HideCursor()` | method | — | W | webui/globals/jcmp | decoded |
| gamepad buttons / axes / triggers | — | — | any | — | **UNKNOWN** — no member in the client, server, shared or WebUI reference (§6.1) |

Construction/ownership rules decoded from https://just-cause.mp/docs/developing/server-packages:
server code owns spawning ("Do not spawn the vehicle on the client"); a stock
dedicated server ships `data/example-server-packages` with `chat`, `spawn-menu`,
`freeroam`; a non-empty `packages/` replaces the bundled set; `restart_package <name>`
reloads a package and refreshes `client_package` for new joins only.

Answers to the six questions in the brief, condensed:

- **create a vehicle by modelHash** — yes, server side only, number hash (`Vehicle` ctor).
- **read and set position / rotation / linearVelocity / angularVelocity / health** — yes
  on the server (`Vehicle`), all five, both directions.
- **read the vehicle the local player is in** — server: yes (`Player.vehicle`). Client:
  no such member; you would match `jcmp.vehicles` against `localPlayer.position`
  (derived workaround, not a documented API).
- **read gamepad input** — no. Presence only (`jcmp.input.hasController()`).
  Keyboard: yes, inside a WebUI page (`document.onkeydown`), which is what
  `jc3mp-keypress` does (https://raw.githubusercontent.com/benank/jc3mp-keypress/master/client_package/main.js —
  decoded: a 1×1 `WebUIWindow` is the entire package).

---

## 3. Mod-loading evidence

Question: does JC3MP load dropzone mods, and can a server spawn a custom `.ee`
vehicle by hash?

**Found (weak, community-grade):** a r/JustCause thread titled "How do i mod my own
server in JC3MP?" whose indexed text is *"I've downloaded the mod files that were
made for multiplayer, I pasted the dropzone file into the JC3 folder and set the launch
options"* (https://www.reddit.com/r/JustCause/comments/uud98t/how_do_i_mod_my_own_server_in_jc3mp).
The page itself returns HTTP 403 to a text fetch, so only the search-result snippet is
available. That is a player describing a dropzone inside the JC3 folder for a JC3MP
session — **not** a statement that the server distributes mods.

**Found (decoded, but only for player skins):** `player.skin` "Accepts a short name
from `jcmp.playerSkins` or a full `.ee` path", and `jcmp.ResolvePlayerSkin` "returns the
canonical `.ee` path for a known name. `.ee` paths come back as-is, even if they are not
in `playerSkins`" (https://just-cause.mp/docs/changes-since-v1.0.7). So the runtime
*does* resolve `.ee` paths — for **player models**, not for vehicles.

**Not found (all UNKNOWN):**
- any docs statement that the JC3MP client launches with
  `--vfs-fs dropzone --vfs-archive patch_win64 --vfs-archive archives_win64 --vfs-fs .`
  (that argument string is documented only for *vanilla* JC3 modding, e.g.
  https://just-cause.mp is silent; vanilla sources: https://eonzenx.github.io/apex-resource-index/tutorials/jc3/mod_setup
  and https://justcause.fandom.com/wiki/Modifying_(JC3));
- any member that spawns a vehicle from a `.ee` **path** — `Vehicle` takes
  `modelHash: number` and nothing else;
- any server→client mod sync for JC3MP (JC4MP has exactly that, `mods` folder + auto
  sync, https://docs.jc4mp.com/mods/overview — **not** evidence for JC3MP);
- any forum/Discord/ModDB comment confirming a custom `.ee` vehicle visible to other
  players under JC3MP. ModDB's JC3MP tutorial
  (https://www.moddb.com/mods/just-cause-3-multiplayer/tutorials/how-to-create-a-jc3mp-server)
  covers server install and packages only.

**Derived reading:** a stock JC3MP vehicle is an engine entity selected by its existing
hash, so a *new* `.ee` would only exist for clients that have it in their own dropzone.
Whether the JC3MP client loads that dropzone at all is the gate, and it is unproven.

---

## 4. Availability

| fact | value | source |
|---|---|---|
| client app | **619910**, free, "Play Game", released 20 Jul 2017 | https://store.steampowered.com/app/619910/Just_Cause_3_Multiplayer_Mod |
| ownership requirement | store note: *"This mod requires Just Cause 3 on Steam"*; SteamDB `MustOwnAppToPurchase: Just Cause 3 (225540)` | store page; https://steamdb.info/app/619910 |
| dedicated server | Steam **tool** app **619960**, `steamcmd +login anonymous +app_update 619960` | https://just-cause.mp/docs ; https://steamcommunity.com/sharedfiles/filedetails?id=1094953641 |
| distribution | "There is no website zip anymore" — Steam only | https://just-cause.mp/docs |
| still alive? | **yes, actively developed**: Update **1.0.8** live 19 Aug 2026 ("1.0.7 was the first step in bringing JC3:MP back"); a public *compat* branch was published for the JC3 Denuvo-removal update | https://just-cause.mp/ ; https://steamcommunity.com/app/619910 |
| Steam must run | "Steam must be running for the server to properly start" | https://just-cause.mp/docs/general/information/faq |
| family sharing | does **not** work; you must own the game | https://steamcommunity.com/app/619910/discussions/0/1699416432426286066 |
| known live defects | "Unable to see other players on latest version … fixed by reverting to the old version of the game and mod" (Apr 2026, marked Completed) | https://feedback.just-cause.mp/ |
| this install | `steam_api64.dll` 981,144 B + `steam_api64.rne` 208,296 B + `steam_emu.ini` 3,300 B, all 2025-12-17; `JustCause3.exe` 51,083,264 B 2025-12-17; `dropzone/` present | read-only `ls -la "D:/Games/Just Cause 3"` (verbatim in §7) |

**Verdict on Q3:** downloadable and runnable today — for a **Steam-owned** JC3 with the
Steam client running. It does not "accept other installs": the only documented path is
Steam (store requirement + `MustOwnAppToPurchase` + Steam-must-be-running). The local
`D:` install is an emulated/repack layout (`steam_emu.ini` + `.rne` shadow), so on the
evidence it is **expected to fail** — but that is a **derived prediction, not a
measurement**. Nothing in the sources addresses emulated installs at all, so the
proposition "JC3MP runs on a non-Steam JC3" is **UNKNOWN**.

---

## 5. Mapping to RB-4 … RB-9

### RB-4 — mode swap at runtime (pursuit ⇄ battle)

- **Carried:** a scripted **two-entity swap**: `Vehicle.Destroy()` the pursuit car,
  `new Vehicle(battleHash, pos, rot)`, `SetOccupant(0, player)`, and copy
  `health` / `linearVelocity` / `angularVelocity` across before destroying. All five
  members are decoded above. `Player.vehicle` lets the script read which car the player
  was in; `Vehicle.driver` (get **set**) lets it read and write the seat without a
  `SetOccupant` call.
- **Lore fit is now good, not bad:** ROADMAP §7 records the operator fact that the swap
  causes a *near-instant slowdown* and carries health/ammo rather than speed, so the old
  "second entity arrives at rest" objection (RB-4 / P5) stops mattering.
- **NOT carried:** the transform itself — turret rising, wheels/body reconfiguring over
  ~2 s. There is no member to change a vehicle's model in place, no animation/anim-graph
  member, no joint/hierarchy member in the server, client, shared or WebUI reference.
  A swap therefore produces a **cut**, not the 2-second transform.
- **Still UNKNOWN:** whether `linearVelocity` write takes effect on an occupied,
  server-owned vehicle in the current build (the property is `get set`, but no release
  note or package proves the write sticks); whether `Vehicle.handling` is writable
  (it is `get` only in the table); whether `turboJumpEnabled` / `nitroEnabled` map to
  anything like the flip-thruster/boost behaviour.

### RB-5 — input scoping (LT-hold, A-hold-charge, keymap writer)

- **Carried:** `jcmp.localPlayer.controlsEnabled = false` gives **script-level control
  gating that no keymap writer can give** — it is per-client, at runtime, reversible, and
  it does not touch `settings/keymap_gamepad.bin` (so no global on-foot side effect, which
  is open decision #7 in ROADMAP §6). `SetAbilityEnabled(hash, bool)` gates single
  abilities by hash. Keyboard: a CEF page's `document.onkeydown`/`keyup` is the pattern
  the public `jc3mp-keypress` package is built on (decoded from its `client_package/main.js`,
  a single `new WebUIWindow('keypress', …, new Vector2(1,1))`).
- **NOT carried:** gamepad. The only controller member found anywhere in the reference is
  `jcmp.input.hasController()` (presence) plus an `input-controller-changed` boolean.
  There is **no** button, axis, trigger or held-state member on the server, client,
  shared or WebUI side. Since the operator ruling is "bind the gamepad first" (ROADMAP §7),
  this is the row's real blocker inside JC3MP.
- **UNKNOWN:** whether the embedded CEF exposes the HTML5 **Gamepad API**, which would
  give buttons/axes to a WebUI page even without a JC3MP member. Nothing in the docs says
  either way. Also unknown: whether LT (a trigger) is even reported as a key to the CEF
  page once JC3's own input is disabled.

### RB-6 — HUD writing

- **Carried, and this is the biggest single win.** `new WebUIWindow(name, url, size)` with
  `size = new Vector2(jcmp.viewportSize.x, jcmp.viewportSize.y)` is a **full-viewport CEF
  overlay**; `autoResize`, `hidden`, `location`, `Reload(true)`, `BringToFront()`,
  `Destroy()` are all decoded. `jcmp.ui.HideHud()` / `ShowHud()` / `IsHudVisible()` remove
  the vanilla HUD. For world-anchored markers (lock diamond/circle, radar icons) there is
  `Renderer.DrawRect` in `Render` (screen pixels), `GameUpdateRender` (2D overlay) and
  `GameRender` (3D pass, first argument is a world position). Data reaches the page via
  `WebUIWindow.CallEvent` or directly through `jcmp.network` (v1.0.8 lets WebUI talk to
  the server without a client proxy).
- **What it removes from the critical path:** NEW-HUD-4 (Scaleform recompile), the
  `hud.gfx` private-copy question (probe P3), the ADF append writer for HUD, and the
  "entity→HUD caller is native" blocker. HTML/CSS also makes the afterburner/cooldown
  gauges, reload circle and tracker signal trivial compared with Scaleform.
- **Not carried:** replacing *parts* of the vanilla HUD while keeping the rest —
  `HideHud()` is a single switch. Keeping e.g. JC3's minimap while drawing your own health
  bar is **UNKNOWN** (no per-widget HUD member found).

### RB-7 — runtime oracle

- **Carried (readout class):** the client can read, live, every frame if wanted:
  `localPlayer.position/rotation/lookAt/baseState`, `NetworkVehicle.position/rotation/
  linearVelocity/angularVelocity/health/maxHealth/speedKph/engineRPM/gear/aabb/type`,
  `camera`, and draw into `Render`. Values can be pushed to the server console with
  `jcmp.network.Invoke` + `print`, or rendered on screen. `jcmp.server.performance` gives
  a tick/frame summary string.
- **`aabb` is worth flagging for collision work:** a client-side AABB for each network
  vehicle is exactly the kind of number the collision chain wants and cannot get from
  files.
- **Not carried:** arbitrary engine reads. There is no member for mass, material,
  colour, light, effect or physics properties. `Vehicle.handling` (server, get) is the only
  handling-shaped object, and its contents were not read. So the oracle JC3MP gives is a
  **telemetry** oracle, not a memory-inspection oracle; it cannot answer RB-12 (colour
  bridge) or the "live mass" question.
- **Also not carried:** anything about the **single-player** game. JC3MP instruments
  itself, not the stock install — so it cannot serve as the oracle for RC4-on-vanilla.

### RB-9 — "when X do Y" logic

- **Carried, fully, on both sides.** This is a general JS runtime with timers (a shipped
  package uses `setInterval(..., 100)` —
  https://raw.githubusercontent.com/derbl4ck/jc3mp-minimap/master/xRef_mod.js, decoded),
  an event bus, `jcmp.network`, and mutable entity state.
  - **water teleport:** `player.position = new Vector3f(...)` is decoded in the server-packages
    example; `Vehicle.position` is get **set**. A "if in water, move to land" rule is a
    few lines.
  - **regen timer:** `jcmp.localPlayer.healthEffects` is a decoded **HealthEffect** object
    documented as "Local player health regeneration settings" — i.e. the runtime already
    models out-of-combat regen, which is precisely the RB-9 example. Its fields were not
    read, so the numbers remain UNKNOWN.
  - **flip thrusters:** `Vehicle.angularVelocity` (get **set**) + `linearVelocity` +
    `turboJumpEnabled` + `nitroEnabled` give a righting impulse; `wingsuit.boostPower` etc.
    are the player-side analogue. Whether the setters produce a *visible* physics change is
    UNKNOWN (see §6.4).
- **Not carried:** **water detection.** The minimap package fakes "underwater" with
  `player.position.y < 1023.5` (decoded, same file) — a hard-coded altitude, not a query.
  No `IsInWater`-style member exists, so the teleport rule needs a height/raycast
  substitute. Same class of gap for "is the car flipped" — no ground-contact or up-vector
  member; it would be derived from `rotation`.

### Cross-cutting: what JC3MP does **not** touch at all

RB-8 (audio authoring/FSB5), RB-10 (`.effc` growth, `.physicsc` append), RB-11 (budgets),
RB-12 (colour bridge) and every data-side row are **untouched** by this platform. JC3MP
adds a runtime; it does not add format writers. Those spikes stay spikes.

---

## 6. UNKNOWNs, and the 5-minute experiment that settles each

All experiments are to be run by the operator under supervision, in a **new private
server tree**, never against `D:/Games/Just Cause 3` and never touching an existing
`Builds/bm-*`. Each is one script file plus one server restart.

**6.1 Does a WebUI page get gamepad buttons/axes?** (decides RB-5)
*Why unknown:* only `hasController()` + `input-controller-changed` exist; nothing says
whether CEF's Gamepad API is enabled in this build.
*5-minute test:* client package whose `client_package/ui/index.html` runs
`setInterval(()=>{const g=navigator.getGamepads()[0]; if(g) hud.CallEvent('pad', g.buttons.map(b=>b.value).join(','))},100)`
plus `console.log(jcmp.input.hasController())`. Press LT/RT. If the array moves, RB-5 has
a gamepad route and the keymap writer stops being on the critical path.

**6.2 What is the *real* member list?** (settles §2 completeness)
*Why unknown:* the docs are generated from engine bindings and the published class pages
may lag the 1.0.8 build; the old `github.com/Paradigm-MP/scripting-api-data` repo is
**404**, so there is no machine-readable source to diff against.
*5-minute test:* in a client package, `print(Object.getOwnPropertyNames(jcmp).join(' '))`,
then the same on `jcmp.localPlayer`, `jcmp.vehicles[0]`, and (server)
`new Vehicle(28454791, new Vector3f(), new Vector3f())`. Diff the output against §2. Any
extra member (an input namespace in particular) changes the verdict on RB-5.

**6.3 Does the client load a dropzone / a custom `.ee`?** (settles §3, and RB-4's art route)
*Why unknown:* no docs statement; one Reddit snippet only; `Vehicle` takes a numeric hash.
*5-minute test:* drop one visually obvious override into a **copy** of the install's
`dropzone`, launch 619910 through Steam, join the private server. Then on the server:
`new Vehicle(<our entity hash>, player.position, player.rotation)`. If the car appears,
custom entities are viable; if the spawn throws or the model is invisible, they are not.

**6.4 Do the velocity/health setters actually move an occupied car?** (decides RB-4/RB-9 quality)
*Why unknown:* the table says `get set`; no release note or package demonstrates a write
taking effect on a driven, server-owned vehicle.
*5-minute test:* server handler on a chat command that sets
`v.linearVelocity = new Vector3f(0,0,40)` and `v.angularVelocity = new Vector3f(0,3,0)`
on `player.vehicle`, then logs both back one tick later. Two numbers and one visual tell
you whether the setters are real or cosmetic.

**6.5 Does the JC3MP client even start on the `D:` layout?** (decides the whole lead)
*Why unknown:* the platform documents only the Steam path; `steam_emu.ini` + `.rne`
suggests an emulated install, and nothing anywhere addresses that case.
*5-minute test:* install **619910 only** (free, no purchase) on a machine with the `D:`
install, launch it, and read the first error. Expected on the evidence: a Steam
ownership/"Steam must be running" failure. If it boots and reaches a server browser, the
lead is real. **This is the one experiment that must come first — the other four are
wasted if it fails.**

**6.6 Is there a per-widget HUD switch, or water/flip query?** (RB-6/RB-9 polish)
*Why unknown:* `HideHud()` is one boolean; no water or contact member found.
*5-minute test:* covered by 6.2's property dump on `jcmp.ui` and `jcmp.world`; for water,
spawn a boat, drive into the sea, and log `player.vehicle.position.y` against the
minimap package's 1023.5 heuristic to see whether a height rule is usable.

**6.7 Scope decision (not an experiment).** Adopting JC3MP re-targets the deliverable
from "JC3 single-player mod" to "JC3MP server content". If the operator wants that, it
belongs in COMPROMISES with the reason; if not, JC3MP is still useful **as an oracle and
a logic sandbox** for RB-7/RB-9 numbers, while RB-4's in-place transform and RB-6's
in-game HUD stay on the native/data route.

---

## 7. Commands run (verbatim output)

Read-only listing of the game install (the only local command; nothing launched):

```
$ ls -la "D:/Games/Just Cause 3" 2>&1 | head -40
total 181713
drwxr-xr-x 1 User 197121        0 Oct  7 20:14 .
drwxr-xr-x 1 User 197121        0 Oct 14 18:35 ..
-rwxr-xr-x 1 User 197121    14848 Feb  4  2017 AvAnimFragments_F.dll
-rwxr-xr-x 1 User 197121   172544 Feb  4  2017 CrashRpt1402.dll
-rwxr-xr-x 1 User 197121   1480192 Feb  4  2017 CrashSender1402.exe
-rwxr-xr-x 1 User 197121   285184 Feb  4  2017 EffectFragments_F.dll
-rwxr-xr-x 1 User 197121   1733120 Feb  4  2017 FragmentBundle_F.dll
-rwxr-xr-x 1 User 197121    35840 Feb  4  2017 IOFragments_F.dll
-rwxr-xr-x 1 User 197121 51083264 Dec 17  2025 JustCause3.exe
-rwxr-xr-x 1 User 197121    36864 Mar  2  2015 Language Selector.exe
-rw-r--r-- 1 User 197121      249 Dec 18  2025 Origins.ini
-rwxr-xr-x 1 User 197121     7168 Feb  4  2017 ProfileContext_F.dll
-rw-r--r-- 1 User 197121 11412258 Aug  6  2016 ShadersConstMathLowShadows_F.shader_bundle
-rw-r--r-- 1 User 197121 11539522 Aug  6  2016 ShadersConstMath_F.shader_bundle
-rw-r--r-- 1 User 197121 11449330 Aug  6  2016 ShadersLowShadows_F.shader_bundle
-rw-r--r-- 1 User 197121 11576594 Aug  6  2016 Shaders_F.shader_bundle
drwxr-xr-x 1 User 197121        0 Oct  6 08:22 _Redist
drwxr-xr-x 1 User 197121        0 Oct  6 08:22 archives_win64
-rwxr-xr-x 1 User 197121   435712 Feb  4  2017 bink2w64.dll
-rw-r--r-- 1 User 197121   8010 Aug  6  2016 crashrpt_lang.ini
-rwxr-xr-x 1 User 197121   298272 Feb  4  2017 cudart64_55.dll
-rwxr-xr-x 1 User 197121 74730784 Feb  4  2017 cufft64_55.dll
-rwxr-xr-x 1 User 197121   276832 Feb  4  2017 d3dx11_43.dll
drwxr-xr-x 1 User 197121        0 Dec 18  2025 dlc_win64
drwxr-xr-x 1 User 197121        0 Nov  2 01:10 dropzone
-rwxr-xr-x 1 User 197121  5230592 Feb  4  2017 fmod_studio_F.dll
-rwxr-xr-x 1 User 197121   421376 Feb  4  2017 gfsdk_waveworks.win64.dll
-rwxr-xr-x 1 User 197121   41984 Feb  4  2017 jc3AudioDSP_MultibandCompressor_SSE_F.dll
drwxr-xr-x 1 User 197121        0 Oct  6 08:22 patch_win64
-rwxr-xr-x 1 User 197121  694184 Feb  4  2017 sdkencryptedappticket64.dll
-rwxr-xr-x 1 User 197121   981144 Dec 17  2025 steam_api64.dll
-rwxr-xr-x 1 User 197121   208296 Dec 17  2025 steam_api64.rne
-rw-r--r-- 1 User 197121   3300 Oct  6 08:34 steam_emu.ini
-rw-r--r-- 1 User 197121 303855 Oct  6 05:34 unins000.dat
-rwxr-xr-x 1 User 197121 1515889 Oct  6 05:32 unins000.exe
```

```
$ mkdir -p tmp/freebuff/reports && ls tmp/freebuff/reports | head -5 && echo "---QUEUE 7970---" && ls tmp/freebuff/queue/ | grep -i "7970" ; ls tmp/freebuff/queue/held 2>/dev/null | grep -i 7970 ; echo "(end)"
7202-v04-audio-gates.md
7203-v05-predictions-part1.md
7205-g3-04d-uniform-records.md
7206-g3-10c-inertia.md
7207-g3-02f-sampler-unknowns.md
---QUEUE 7970---
(end)
```

(No `7970` brief exists in `queue/` or `queue/held/`; this report is the deliverable.)

Web reads (no page was modified, nothing downloaded or executed):
`https://just-cause.mp/`, `/docs`, `/docs/client`, `/docs/server/classes/{vehicle,player}`,
`/docs/client/classes/{local-player,network-vehicle,web-ui-window,jcmp-ui-namespace}`,
`/docs/webui`, `/docs/webui/globals/jcmp`, `/docs/developing/server-packages`,
`/docs/concepts/{compatibility,serialization}`, `/docs/changes-since-v1.0.7`,
`/docs/general/information/{faq,server-configuration}`,
`https://store.steampowered.com/app/619910/Just_Cause_3_Multiplayer_Mod`,
`https://steamdb.info/app/619910`, `https://feedback.just-cause.mp/`,
`https://steamcommunity.com/sharedfiles/filedetails?id=1094953641`,
`https://steamcommunity.com/app/619910/discussions/0/1699416432426286066`,
`https://www.moddb.com/mods/just-cause-3-multiplayer/tutorials/how-to-create-a-jc3mp-server`,
`https://api.github.com/repos/Paradigm-MP/SI-Script-Pack/git/trees/master`,
`https://raw.githubusercontent.com/{derbl4ck/jc3mp-minimap/master/{main.js,xRef_mod.js},benank/jc3mp-keypress/master/client_package/main.js}`,
`https://docs.jc4mp.com/mods/overview` (JC4MP — cited only to show it is *not* JC3MP evidence).

Route notes for the next reader: `/docs/server/vehicle` → 404, use
`/docs/server/classes/vehicle`; `github.com/Paradigm-MP/scripting-api-data` → 404 (gone);
`api.github.com/search/code` → 401 (needs auth); `reddit.com` → 403 to text fetches.

---

## 8. UNKNOWNs (formal list)

1. **Full member list at 1.0.8** — docs are generated but only published as a rendered
   site; the old API-data repo is 404. §2 is complete for the five classes in the brief,
   possibly not complete for the build. Settle with §6.2.
2. **Gamepad buttons/axes** — no member in any domain; CEF Gamepad API availability
   unstated. Settle with §6.1.
3. **Dropzone / custom `.ee` under JC3MP** — one 403-blocked Reddit snippet; `Vehicle`
   takes a numeric hash only; `.ee` paths are proven for **player skins** only. §6.3.
4. **Non-Steam install support** — no source addresses it; local layout is emulated.
   §6.5 (needs a launch, so operator-only).
5. **Whether velocity/health setters change driven physics** (vs. cosmetic sync) — §6.4.
6. **`HealthEffect` fields** (regen delay/rate/threshold), `Vehicle.handling` fields,
   `VehicleHandling` shape — objects confirmed, contents not read. §6.2 dump.
7. **Per-widget HUD hiding** — only a global `HideHud()`. §6.6.
8. **Water/flip/ground-contact queries** — none found; the shipped minimap fakes water
   with `y < 1023.5`. §6.6.
9. **Whether the 2-second transform can be authored at all in JC3MP** — no animation or
   joint member exists in the reference, but a model swap via `Destroy`+`new Vehicle`
   cannot produce it either way. This is the one RB-4 requirement JC3MP does **not**
   carry on the evidence.

---

COMPROMISES: none taken. Nothing in this report amends a lore requirement; where JC3MP
cannot carry a lore behaviour (in-place 2-second transform, gamepad hold detection,
colour/mass truth) it is recorded as a gap with the member that is missing, per the
2026-11-06 rule, not accepted as a limit.
