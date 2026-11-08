# Pilot cards — wheel-reuse check (JC3 + Batman: Arkham Knight)

Date: 2026-11-08. Read-only research. Nothing was installed, downloaded, launched, or edited —
`Working/Q/PILOT/*.md` are unchanged; §3 lists proposals only.

Rules followed: `tmp/freebuff/INSTRUCTIONS.md`; claims about both games are cited to a URL, and
anything the sources do not state is marked **UNKNOWN** rather than filled from memory.

## 0. Verdict in six lines

1. **The 20-second mux problem is already solved by OBS.** `--startrecording` is a documented
   launch parameter and `StopRecord` is a websocket request; the `--offset 0.25` pilot threshold and
   the float32 peak guess in `RECORD.md` exist only because the card builds its own recorder.
2. **The two hardest calibration fields can be deleted, not calibrated.** `SPAWN_BATMOBILE`'s
   `OPEN_DROP` / `DROP_ENTRY_CLICK` / `CONFIRM_CLICK` and `PROVE_CARDS`' `SERPENTE_SPAWN` exist to
   drive a menu. A published MIT-licensed JC3 console (`jc3-console-thingy`) spawns entities by
   name, so the menu path is optional.
3. **JC3 has a documented fast-load flag** (`-quickstart`) and a documented intro-removal file
   (`dropzone/videos/corona_video.bikc`). `LAUNCH.md` currently has neither and burns ~120 s on
   `sleep` waiting for init.
4. **Arkham Knight's launch story is not JC3's.** `-nologo` and `-windowed` are documented for
   Knight; `BmLauncher.exe` / `-nolauncher` belong to **Asylum and City**, not Knight — adding them
   to a Knight card would be an invented flag.
5. **Telemetry has no JC3 speedometer mod to reuse** (searched; every hit is another game). JC3's
   own driving HUD is the only speed source in evidence, so `qa1_hud.py` stays — a Cheat Engine
   position read is a *cross-check*, not a replacement.
6. **No published agent drives JC3 or Arkham Knight.** The closest prior art (GTA V, MIT) is
   screen-capture + virtual gamepad at a fixed window position — which is exactly the pattern the
   cards already use, so it validates the loop rather than replacing it.

---

## 1. Per-card findings

Format: **reusable tool** (URL, licence, Steam?) → **what it replaces in the card** → **risk**.

### 1.1 `LAUNCH.md` — cold start to the main menu

**JC3 fast load: `-quickstart`**
`aaronkirkham/jc3-console-thingy` README, https://github.com/aaronkirkham/jc3-console-thingy
(MIT). Exact line: *"***OPTIONAL*** - Enable faster game loading with the `-quickstart` launch
argument via Steam"*. The same sentence appears in the JC4 sibling repo
(https://github.com/aaronkirkham/jc4-console-thingy).
* Replaces: nothing structurally, but it shortens the init wait that step 12 currently pays for
  blindly (`sleep 120`). Steam is not required by the flag itself; the flag is passed on the command
  line the card already builds in step 6.
* Risk: the source says "faster game loading", **not** "skip intro". It is a loading shortcut of
  unstated size; the card must keep its frame-difference proof (steps 13–16) and must not replace
  the 120 s wait with a shorter invented number.

**JC3 intro removal: an empty `corona_video.bikc` inside the dropzone**
* Steam guide "How to skip the intro screen [DLC Support]",
  https://steamcommunity.com/sharedfiles/filedetails?id=570542665 — create `dropzone\videos\`,
  create an empty file named `corona_video.bikc`, then add the vfs launch arguments.
* Same method, packaged: PCGamingWiki community file
  https://community.pcgamingwiki.com/files/file/863-just-cause-3-no-intro-mod/ — *"Extract
  `dropzone` directory to the installation directory. Add command line arguments:
  `--vfs-fs dropzone --vfs-archive patch_win64 --vfs-archive archives_win64 --vfs-fs`"*. Licence:
  community file, no explicit licence. Steam: the game copy is, the mod is not.
* The original: https://videogamemods.com/vgm/justcause3/mods/no-intro — *"Removes the intro video.
  Does not remove login screen!"*
* Replaces: the post-launch `sleep 120` + "did the menu arrive?" uncertainty, and gives step 6 a
  second reason to exist beyond mod loading.
* Risk: `LAUNCH.md` step 6 **already** passes `--vfs-fs dropzone …`; this only helps if the file
  exists **in the real game directory**, and a glob of this repo finds no `corona_video*`
  (`glob **/corona_video*` → 0 files). Creating it in `D:\Games\Just Cause 3` is an **install**, which
  card rule 9 forbids — so it is an operator pre-step, and the card may only *check* for it.
* Note the dropzone in step 6 also carries the mod payload; the empty video file is a payload
  change to the same folder the build is verified against (step 5 reads 9/9). It must not be added
  by a card.

**Arkham Knight intro + windowed**
* `-nologo` skips the intro videos: Steam guide "Batman™: Arkham Knight Optimisation Guide",
  https://steamcommunity.com/sharedfiles/filedetails?id=866035266 — *"input this parameter … This
  will disable the introduction videos and skip straight to the game start menu."*
* `-windowed` is the documented workaround for "won't start / can't run fullscreen":
  https://steamcommunity.com/app/208650/discussions/0/523890046867965665 and the MSI FAQ
  https://www.msi.com/faq/faq-10708 (both say: add `-windowed` to launch options).
* Replaces: the `size 1600 900` guess in step 8 (a windowed start is the documented fix), and the
  intro wait.
* Risk: `-windowed` gives a default size, not 1600×900; the card still needs a size command or a
  config edit. `-nologo` is a Steam-launch-option example; whether the Knight executable accepts it
  when invoked directly is **UNKNOWN** (no source shows a direct `BatmanAK.exe -nologo` run).

**The flag that must NOT be added:** `BmLauncher`/`-nolauncher` are **Asylum and City** tools —
https://neatodev.github.io/BmLauncherAsylumNET6 and https://neatodev.github.io/CityLauncher both say
*"replacement application for the original BmLauncher of the game"* for those two titles, and the
City page adds *"Not necessary for Steam, which already has built-in launcher skipping for this
game."* No source describes a Knight `BmLauncher`. Knight ships `BatmanAK.exe` under
`Binaries\Win64` (https://dcgamessupport.wbgames.com/hc/en-us/articles/360036775914 and
https://www.intel.com/content/www/us/en/support/articles/000094465/graphics.html both use that
path). Treat "Knight has a launcher" as **UNKNOWN** and do not card it.

**Window size, JC3.** No launch flag for resolution found for JC3 in any source here; the repo's
`um win drive "size 1600 900"` remains the only documented method. **UNKNOWN** whether JC3 accepts
a resolution switch.

### 1.2 `LOAD_SAVE.md` — main menu into free roam

**JC3.** No reusable loader was found. The only JC3 "fast start" artefact in evidence is
`-quickstart` (§1.1) and the no-intro file, which the mod itself says *"Does not remove login
screen!"* (https://videogamemods.com/vgm/justcause3/mods/no-intro). So the card's `ENTER_KEY` /
`SAVE_SLOT_CLICK` calibration fields survive unchanged: **nothing published navigates JC3's main
menu**. UNKNOWN.

**Arkham Knight — save-slot swap (documented, and it removes the menu walk).**
* Location and naming: WB support https://dcgamessupport.wbgames.com/hc/en-us/articles/360001040067
  (*"C:\Program Files (x86)\Steam\userdata\…\208650 … BAK1Save 0x0.sgd & BAK1Save 0x1.sgd would be
  the first slot"*), corroborated by the Nexus readme
  https://www.nexusmods.com/batmanarkhamknight/mods/1295?tab=docs (*"BAK1Save0x0.sgd … correspond to
  the first save slot … three total files for each save slot"*).
* A ready-made free-roam save set: same Nexus page, "Optimized Free Roam (Save Game Files)";
  and a 100% save at https://www.yoursavegames.com/2017/04/batman-arkham-knight-100-pc-save-game.html.
* Steam needed: yes for the `userdata\208650` path; the non-Steam path is
  `<game>\BMGame\SaveData` (Nexus readme; PCGamingWiki
  https://www.pcgamingwiki.com/wiki/Batman:_Arkham_Knight lists both `\BMGame\SaveData\` and
  `\userdata\<id>\208650\`).
* Replaces: every click in a Knight variant of the card **if and only if** a chosen slot loads
  straight into free roam. That is not stated by any source read here — the Nexus pack says the files
  are "listed in slot 3", i.e. you still pick a slot. So it replaces *save hunting*, not the menu
  navigation. Partial.
* Risk: cloud sync overwrite (*"Cloud synchronization can overwrite your local saves"*,
  https://www.games-manuals.com/save-game-location-backup-installation/batman-arkham-knight-208650);
  slot numbering off-by-one between filename and in-game list; a save from another platform is
  rejected (`00 10 25 00` prefix conversion per PCGamingWiki); achievements.

### 1.3 `SPAWN_BATMOBILE.md` — Rebel Drop entry selected, car delivered

**The big find: `jc3-console-thingy`** — https://github.com/aaronkirkham/jc3-console-thingy (MIT,
6 commits, last touched 2018-12-31). Install: drop `xinput9_1_0.dll` in the JC3 folder, open with
`~` or `F1`. Commands: `spawn` (*"Spawn everything! Vehicles, characters, animals & props"*),
`event`, `world`. Mirrored on VGM as "JC3 Entity Spawner"
(https://videogamemods.com/vgm/justcause3/mods/jc3-entity-spawner, 1,394 downloads) and recommended
in r/JustCause (https://www.reddit.com/r/JustCause/comments/1e7fqsf/is_there_a_mod_that_allows_me_to_spawn_a_small/:
*"The easiest way to do this is with this tool … It lets you spawn in anything you want."*).
* Replaces: `OPEN_DROP`, `DROP_ENTRY_CLICK`, `CONFIRM_CLICK` — three UNKNOWN calibration fields and
  the entire beacon/restock economy (Rebel Drop needs beacons and a restock timer, per
  https://justcause.fandom.com/wiki/Rebel_drop). A name-typed spawn has no list to scroll and no
  cooldown.
* Risk (real, and it decides the card): it spawns **entities the game's own name table knows**.
  Whether a custom Batmobile `.ee` is in that table is **UNKNOWN** — no source shows the console
  spawning a mod entity. Second risk: it is a DLL injected as `xinput9_1_0.dll`, i.e. a second
  in-process hook beside the dropzone payload; a crash would make `LAUNCH`'s dump check (step 18)
  ambiguous. Third: the tool is 2018 and untested against 1.0.8-class builds (**UNKNOWN**).

**Rebel Drop alternatives that do not need a DLL** (fallbacks, not replacements for the menu):
* `Full Rebel Drop mod v4.1`, https://videogamemods.com/vgm/justcause3/mods/rebel-drop-v4-1 —
  *"it removes rebel drop timers of everything"* and adds vehicles; still a menu, but a shorter one.
* `Infinite Rebel Drop Beacons` (.wtunec), https://videogamemods.com/vgm/justcause3/mods/infinite-rebel-drop-beacons-wtunec-file-for-patch-1-05
  — removes the beacon constraint, not the navigation.
* Both are payload drops into `dropzone`, i.e. build/install work, and neither is licence-stated
  (**UNKNOWN**).

**Arkham Knight.** No spawn tool for the Batmobile was found. The Knight trainers/CE tables in §2
list vehicle *health*, *missiles*, *afterburner* — never "spawn vehicle". **UNKNOWN.**

### 1.4 `ENTER_EXIT.md` — `Y`, fallback `E`, camera/HUD frame

No tool is needed and none was found that would improve it: the keys are `decoded` rows in
`CONTROLS.md`, and the card already proves entry by frame difference. Two cross-game notes:
* Entry is a *volume*, not a point (catalogue E-1/E-2). Nothing published for JC3 automates
  "walk to the door", so the card's approach instruction stands.
* If the binding ever turns out gamepad-only, the virtual-pad route in §1.5 is the substitution;
  it changes the *source* of the press, not the card's `SEE` lines.
* Arkham Knight's Batmobile enter/exit binding is **UNKNOWN** in this repo — not searched as a
  binding table because the question was tools, and the Arkham Wiki command list
  (https://arkhamcity.fandom.com/wiki/Command_list) is a per-title table, not a PC key map. Do not
  add a Knight enter/exit card on the strength of it.

### 1.5 `CONTROLS.md` / any card that presses a key — scripted input

The card set presses keys through `um win drive … "key 0xNN"` and defends itself with
`scanmode on` (LAUNCH step 19). Three published facts refine that, and one tool adds a whole input
class the cards cannot reach today.

**AutoHotkey's own documentation on why key injection fails in games** —
https://www.autohotkey.com/docs/v1/commands/Send.htm and https://www.autohotkey.com/docs/v2/howto/SendKeys.htm:
* `SendInput` *"automatically reverts to SendEvent"* if another low-level keyboard hook is installed;
* `SendPlay` *"can work in cases where the other modes fail, particularly in some games"*, but the v2
  guide warns *"SendPlay doesn't tend to work on modern systems unless you run with UI access. On
  Windows 11 and later, SendPlay may have no effect at all."*
* `ControlSend` *"sends messages directly to the window that you specify"* — a fourth mode.
* Replaces: nothing in the cards; it **validates** the existing ladder and supplies the exact
  fallback order the cards lack (Input → Event → Play/ControlSend) instead of "re-run the step once".

**Virtual gamepad: ViGEmBus + vgamepad.** https://github.com/nefarius/ViGEmBus (**BSD-3-Clause**,
4.2k stars) and https://github.com/yannbouteiller/vgamepad (**MIT**; *"The ViGEmBus driver
(v1.17.333) is bundled with the library and installs automatically"*).
* Adds: analog axes and triggers, which no `key 0xNN` can express — this is the only route to
  steering/brake *magnitude* and to a card that can hold a partial throttle. It also sidesteps the
  DirectInput/XInput question entirely, because the game sees a real device.
* Replaces: the `scanmode` workaround as the *primary* input path on any card that needs a
  continuous input (DRIVE, BRAKE, AIRFIELD run-up).
* Risk: **ViGEmBus is retired** — its README carries *"🧟 THIS PROJECT HAS BEEN RETIRED 🧟 … read the
  end-of-life statement"*. Installing a kernel driver is an admin action, i.e. an operator pre-step
  (card rule 9), and a kernel driver is the largest blast radius of anything in this report. Steam:
  not needed by the driver, needed by JC3.
* Precedent that this combination is the standard answer for driving games: a GTA V autonomous
  driver, https://github.com/jey7800/GTA-V-Autonomous-Driving-AI (MIT), lists
  *"Driver: ViGEmBus (virtual gamepad driver)"* and requires *"GTA V running in windowed mode at
  1280×720, positioned at (0, 0)"* — the same fixed-window contract `LAUNCH.md` step 8 establishes.

**Not needed:** JC3MP. `benank/jc3mp-warp` (https://github.com/benank/jc3mp-warp) is three lines:
`if (!player.vehicle) { player.position = player.aimPosition; }` with a client `KeyUp` binding, and
`XONOSNET/jc3mp-xonosutils` (MIT) is a `B`-key teleport menu — both are **server-side multiplayer**
teleports that require a JC3MP server and a Steam-owned JC3 (see
`tmp/freebuff/reports/jc3mp-runtime-platform-check.md`). For single-player piloting they are the
wrong wheel.

### 1.6 `AIRFIELD.md` — prove the straight test strip

No published tool proves "this strip is straight and clear" for JC3. The reusable pieces are
*observational*, not navigational:
* `jc3-console-thingy`'s `world` command (*"Change world parameters"*) is the only candidate for
  stabilising the shot (time of day / weather). Which parameters it exposes is **UNKNOWN** — the
  README lists the command, not its arguments.
* For Arkham Knight, the UE3 pseudo-console gives a free camera: the FearLess thread
  https://fearlessrevolution.com/viewtopic.php?t=946 (SunBeam's RCheatManager emulation) lists
  `ToggleDebugCamera`, `EnableDebugCamera`, `Fly`, `Ghost`, `Teleport`. That would let an operator
  take one overhead reference frame of a strip instead of inferring straightness from a chase cam.
  Risk: it needs a `console.txt` + `BmInput.ini` edit **and** a Cheat Engine table that emulates a
  UObject the game does not ship; the thread itself says *"some will crash, as they require some
  additional UObjects - e.g.: DebugCamera"*. Too fragile to put in a pilot card; operator-only.
* Replaces: nothing in the card's `SEE` lines. **AIRFIELD remains a geometry/vision task**; its
  `STRIP_START`, reference-shot and `STRIP_LENGTH_M` calibration fields are still the honest answer.

### 1.7 `SCREENSHOT.md` — one frame plus a live-oracle check

Nothing to reuse: the card already does the minimum (`um win shot`, then a hash comparison to prove
the oracle is not frozen). Two cross-game cautions from the sources above:
* Arkham Knight's documented launch failure mode is fullscreen (*"people having trouble running the
  game fullscreen … forcing windowed mode … worked"*, https://steamcommunity.com/app/208650/discussions/0/523890046867965665)
  — a frozen or black capture on Knight should send the pilot to `-windowed`, not to a new capture
  tool.
* OBS can also take stills, but has **no screenshot launch parameter** in the official list
  (https://obsproject.com/kb/launch-parameters) — do not card one.

### 1.8 `RECORD.md` — 20 s take with audio, proven non-silent

**This is the card that reinvents the most, and OBS is the wheel.**

* Official launch parameters, https://obsproject.com/kb/launch-parameters: `--startrecording`
  (*"Automatically start recording"*), `--minimize-to-tray`, `--collection "name"`,
  `--profile "name"`, `--scene "name"`, `--multi` (*"Don't warn when launching multiple instances"*),
  `--startreplaybuffer`, `--always-on-top`.
* There is **no** stop parameter — OBS staff answer that directly
  (https://obsproject.com/forum/threads/timed-recordings-on-obs.99727: *"There's no command like
  that. Invoking OBS from the command line tells OBS to launch, and then tells it that it should do
  something right when it starts"*; and
  https://obsproject.com/forum/threads/command-line-to-stop-stream-record.60324/ recommends
  websockets *"since it has support for both starting and stopping"*).
* Stop path: obs-websocket v5 ships with OBS 28+ and exposes `StopRecord`. Two clients:
  `obs-cmd` (https://github.com/grigio/obs-cmd, *"OBS Studio 30.0+ with obs-websocket v5.5.0+"*,
  `obs-cmd record start|stop`) and the Python client `obs-ws-client`
  (https://pypi.org/project/obs-ws-client → `Request('StartRecord')` … `Request('StopRecord')`,
  `res.res_data["outputPath"]`). The `obs-cmd` licence is not stated in its README
  (**UNKNOWN**); `obs-ws-client` publishes no licence field in its PyPI description (**UNKNOWN**).
* Replaces, item by item:
  * `um win record` → `obs64.exe --startrecording` (or one `StartRecord` request);
  * the separate `take1.audio.raw` and `um video mux` steps → OBS writes one file with audio;
  * `--offset 0.25` → **gone**; no mux, so no offset threshold to calibrate;
  * the float32 assumption in step 4 → replace with a format-agnostic silence check
    (`ffmpeg -i take.mkv -af volumedetect -f null -` and read `max_volume`; ffmpeg is not currently
    cited in this repo — **UNKNOWN** whether it is installed, so this is a proposal, not a fact).
* Risk: OBS needs a configured scene + audio source before it can record anything, which is a
  one-time operator setup and a new failure mode ("recording started, scene was empty"). Per-app
  mute still yields exact silence (`RECORD.md` P3) — OBS does not fix that. And the take must still
  be proven non-silent; `--startrecording` only proves a file was started.
* Cross-check on why the current card is fragile: OBS's own forum thread on the same topic shows an
  operator discovering `--startrecording` *does* work while `--stoprecording` does not
  (https://obsproject.com/forum/threads/cli-stop-and-start-for-timed-recording.152689) — i.e. the
  half-and-half approach fails, so a card that adopts OBS must adopt the websocket too.

### 1.9 `KILL.md` — end the session by exact PID

`um win kill <pid>` stays; no published tool improves a PID kill, and every "close the game" helper
found (trainers, CE, OBS) has its own lifetime problem. One addition worth a note, not a step: if a
trainer or CE is attached, the *game* PID is still the only one the card may kill, and the attached
tool may itself hold a handle that delays exit. The card's existing rule (exact PID, never a name
pattern, `pkill -f` killed the agent's own shell upstream) is already the correct defence.

### 1.10 `PROVE_CARDS.md` — prove the cards on a stock Serpente

* `SPAWN_SERPENTE`'s `SERPENTE_SPAWN` field can be **filled by the console**: `jc3-console-thingy`'s
  `spawn` takes names/hints, so "Serpente" is typed, not navigated (§1.3). That deletes the
  calibration run this file was built around — but only if the console works on the installed build
  (**UNKNOWN**) and only if the exact hint string for the Serpente is discovered at the console
  (the tool shows a hints list; the string itself is not in any source here).
* `DRIVE_SERPENTE` / `BRAKE_SERPENTE` read speed from the HUD via `qa1_hud.py`. No JC3 speedometer
  mod was found to replace it (searched: `"just cause 3" mod speedometer` returned Cyberpunk, My
  Summer Car, Minecraft, GTA IV/V, SnowRunner — no JC3 hit). A Cheat Engine table for JC3 exists
  (`Just Cause 3 - table v: 1.0.2 CT`, https://fearlessrevolution.com/viewtopic.php?p=116086, target
  *"Game Version: 1.05"*, and a user asking for *"the waypoint teleporter"* implies a teleport
  script), and a trainer with a store/teleport hotkey set exists (LinGon +24/+23,
  https://gtrainers.com/load/j/just_cause_3/just_cause_3_trainer_24_update_jan_2017_lingon/281-1-0-2669:
  *"Number 8 - Store Location Number 9 - Teleport Number 0 - Undo Teleportation"*). Neither displays
  speed or position as a number, so neither is a telemetry source. The HUD OCR stays.
* The trainer's own warning is the reason to keep it out of a card: *"May or may not work correct
  with all versions of this game title, this version is made for the bonus version"*
  (https://steamcommunity.com/app/225540/discussions/0/1620599015898610075). Licence: freeware,
  no licence stated (**UNKNOWN**); distribution is third-party.

---

## 2. Cross-game tools (one table)

| tool | URL | licence | Steam needed? | what it is for | evidence class |
|---|---|---|---|---|---|
| `jc3-console-thingy` | https://github.com/aaronkirkham/jc3-console-thingy | MIT | game does; tool no | JC3 in-game console: `spawn`, `event`, `world`, `-quickstart` | README + VGM mirror |
| JC3 no-intro file | https://steamcommunity.com/sharedfiles/filedetails?id=570542665 ; https://videogamemods.com/vgm/justcause3/mods/no-intro | none stated | no | remove JC3 intro video | two independent guides |
| OBS Studio + obs-websocket | https://obsproject.com/kb/launch-parameters | OBS is GPL-2.0 (not stated on that page) | no | one-file recording with audio, start via flag, stop via `StopRecord` | official docs |
| `obs-cmd` | https://github.com/grigio/obs-cmd | not stated (UNKNOWN) | no | CLI start/stop against obs-websocket v5 | README |
| `obs-ws-client` (Python) | https://pypi.org/project/obs-ws-client | not stated (UNKNOWN) | no | `StartRecord`/`StopRecord` in Python | PyPI page |
| ViGEmBus | https://github.com/nefarius/ViGEmBus | BSD-3-Clause | no | kernel driver exposing a virtual X360/DS4 pad | repo + LICENSE |
| `vgamepad` | https://github.com/yannbouteiller/vgamepad | MIT | no | Python API onto ViGEmBus; bundles 1.17.333 installer | README + PyPI |
| AutoHotkey | https://www.autohotkey.com/docs/v2/lib/Send.htm | GPL-2.0 (not re-checked here) | no | input modes: Input / Event / Play / ControlSend | official docs |
| JC3 CE table 1.0.2 | https://fearlessrevolution.com/viewtopic.php?p=116086 | none stated (UNKNOWN) | table targets Steam 1.05 | memory read/write incl. teleport scripts | forum post |
| JC3 trainers (LinGon) | https://gtrainers.com/load/j/just_cause_3/just_cause_3_trainer_24_update_jan_2017_lingon/281-1-0-2669 | freeware, none stated | version-dependent | store/teleport hotkeys, timers | trainer listing |
| Arkham Knight CE tables | https://fearlessrevolution.com/viewtopic.php?t=20454 ; https://cheatevolution.com/batman-arkham-knight-trainer | none stated | supports Steam/Epic/MS Store | save location, teleport, X/Y/Z edit, Batmobile health | trainer listings |
| Arkham Knight UE3 pseudo-console | https://fearlessrevolution.com/viewtopic.php?t=946 | CE table, none stated | targets `BatmanAK.exe` | `Fly`, `Ghost`, `Teleport`, `ToggleDebugCamera` | author write-up |
| GTA V autonomous driver (prior art) | https://github.com/jey7800/GTA-V-Autonomous-Driving-AI | MIT | game yes | screen capture + ViGEmBus loop at fixed window | README |
| JC3MP warp / xonosutils | https://github.com/benank/jc3mp-warp ; https://github.com/XONOSNET/jc3mp-xonosutils | MIT (xonosutils), none stated (warp) | **yes, Steam JC3 + server** | multiplayer teleport only | source |

**Seen and rejected as "an agent that drives JC3 or Arkham Knight":** none exists. Searches for
game-driving agents return GTA V / GTA San Andreas / Hill Climb / Forza bots only
(https://github.com/CT83/Driver MIT, https://github.com/1Stalk/FH6-Wheelspin-Farm-Bot MIT,
https://github.com/glitchivy/Hill-Climb-RL). **UNKNOWN** whether any private JC3 or Knight agent
exists.

---

## 3. Recommended card changes (proposals — no card edited)

Each is written so it can be accepted or refused on its own; each names its revert.

**P1 — `LAUNCH.md`, add `-quickstart` to step 6.**
Step 6's argument string becomes `--vfs-fs dropzone --vfs-archive patch_win64 --vfs-archive
archives_win64 --vfs-archive dlc_win64 --vfs-fs . -quickstart` (source: jc3-console-thingy README).
Keep step 12's `sleep 120` unchanged: the flag's size of effect is unstated, and the card has no
timing oracle. *Revert:* delete the flag from the line. *Value:* fewer launches where init stalls;
none of the `SEE` lines change, so nothing else is affected.

**P2 — `LAUNCH.md`, new pre-condition P4 (check only): intro file present.**
`| P4 | the intro is already removed | ls "D:/Games/Just Cause 3/dropzone/videos/corona_video.bikc" | a zero-byte file |`
with `IF NOT` → run the card without it (no STOP). This makes the card's launch reproducible
without making the card an installer. *Revert:* delete row P4. *Risk:* if the real install's
dropzone is the build's payload, adding this file is a build change and must go through the build,
not the operator.

**P3 — `SPAWN_BATMOBILE.md`, add a console route ahead of Rebel Drop.**
New step between 1 and 2: press `~`/`F1`, type `spawn ` and select the hint for the vehicle, with
`SEE` = the frame changes and `ENTER_EXIT` can now enter it. Keep the Rebel Drop path as the
fallback and keep the E-3 trap line ("listed ≠ spawnable") — the console does not remove that trap,
it only removes the list. *Revert:* delete the step and its `CONTROLS.md` row. *Risk:* DLL route and
custom-`.ee` invisibility (§1.3); both must be checked in the same take, and a crash must be
attributed to the console, not to the payload.

**P4 — `SPAWN_BATMOBILE.md`, move the three UNKNOWN fields out of the critical path.**
`OPEN_DROP`, `DROP_ENTRY_CLICK`, `CONFIRM_CLICK` become *fallback-route* fields, used only if P3's
route is refused. *Revert:* restore them as unconditional pre-conditions. This is the change the
operator asked for in substance: a calibration field that is only needed on a fallback is not a
blocker.

**P5 — `PROVE_CARDS.md` §2.1, replace the `SERPENTE_SPAWN` calibration with a console hint.**
`SERPENTE_SPAWN=<spawn <hint>>` filled once from the console's own hint list, keeping the
`grep -E "^    SERPENTE_SPAWN=<"` refusal test so the card still cannot run unfilled. *Revert:*
delete the field and return to the operator-calibration wording.

**P6 — `RECORD.md`, replace steps 1–6 with OBS + websocket.**
Start: `obs64.exe --profile "<p>" --collection "<c>" --scene "<s>" --startrecording
--minimize-to-tray`; stop: one `StopRecord` request; `SEE` = `outputPath` printed by the response and
one file that exists and is non-zero. Silence check becomes `ffmpeg … volumedetect` /
`max_volume` instead of a float32 unpack. Delete `--offset 0.25` and its calibration note.
*Revert:* the current six steps are unchanged in git; restore them. *Risk:* requires a configured
scene (operator pre-step) and an installed ffmpeg (**UNKNOWN** in this repo); until both exist the
card must STOP, not fall back to `--no-audio`.

**P7 — `CONTROLS.md`, add an input-mode column for the fallback ladder.**
Rows that need a *hold* (throttle, brake, steer) get `input=virtual-pad`, the rest stay `key 0xNN`.
The ladder in the header becomes the documented one: `SendInput` → `SendEvent` → `SendPlay`/
`ControlSend`, with the AHK v2 warning about Windows 11 quoted. *Revert:* drop the column. This is
the only proposal that needs a driver install, so it should be the last one accepted.

**P8 — a new Arkham Knight launch note, not a card.**
Record `-nologo -windowed` as the Knight launch string and record that `BmLauncher`/`-nolauncher`
are Asylum/City-only. *Revert:* delete the note. No Knight card exists yet, so this is knowledge
capture, not a card edit.

**Not proposed:** changes to `ENTER_EXIT`, `SCREENSHOT`, `KILL`. Nothing found improves them, and
`KILL`'s exact-PID rule is already the safest option in evidence.

---

## 4. UNKNOWNs, each with the test that would settle it

| # | unknown | why it matters | 5-minute test |
|---|---|---|---|
| U1 | Does `-quickstart` actually shorten JC3's init, and by how much? | P1 is otherwise a cosmetic flag | launch twice (with/without), timestamp the first non-black frame — one `um win shot` per 5 s |
| U2 | Does `jc3-console-thingy` load on this JC3 build (1.0.8-class) without a crash? | P3/P5 depend on it | drop `xinput9_1_0.dll`, open with `~`, type `spawn` + one letter; a hint list or a dump decides it |
| U3 | Can the console spawn a **custom** `.ee` vehicle (the Batmobile), not just vanilla? | the whole SPAWN card's value | with the payload installed, type the Batmobile's hint; if it is absent from the list, U3 = no |
| U4 | Does `-nologo` work when `BatmanAK.exe` is invoked directly (not through Steam)? | P8 records it as a Knight launch flag | run `BatmanAK.exe -nologo -windowed` once, time to main menu |
| U5 | Does a Knight save slot load straight into free roam? | would delete LOAD_SAVE's menu walk | copy `BAK1Save0x0.sgd` into `userdata\<id>\208650\remote`, launch, count clicks |
| U6 | Is ffmpeg present, and does `volumedetect` read an OBS `.mkv`? | P6's silence check | `ffmpeg -i <take>.mkv -af volumedetect -f null -` and read `max_volume` |
| U7 | Does a virtual pad reach JC3 at all (does the game see XInput)? | the only route to analog input | `vgamepad` + `hardwaretester.com/gamepad`, then one in-game menu press |
| U8 | Does `world` in the JC3 console stabilise weather/time for a repeatable strip shot? | AIRFIELD repeatability | open the console, type `world `, read the hint list |
| U9 | Which JC3 CE table AOBs survive the installed build? | a position cross-check for DRIVE/BRAKE | attach CE to `JustCause3.exe`, tick the teleport script; a red X is the answer |
| U10 | Is there any JC3 speed readout that is not HUD pixels? | would remove OCR from every drive card | search for a speedometer mod returned none; the test is one CE scan for a float that matches the HUD at two speeds |

## 5. What this report does not claim

* It does not claim any of these tools work on this machine — no install, no launch, no attach.
* It does not claim `-quickstart` skips the intro (the source says "faster game loading").
* It does not claim a Knight `BmLauncher` exists (the sources that name it name Asylum and City).
* It does not claim the console can spawn a mod entity (no source shows it).
* Licences marked "not stated (UNKNOWN)" were not inferred from the vendor's other projects.
