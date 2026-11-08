STATUS: done. Desk study only — nothing was launched, installed, captured or killed. Sources read: `skills/game-automation/SKILL.md`, five files in `knowledge/techniques/`, and the three `knowledge/games/just-cause-3/` notes. `um` is present on this machine (`command -v um` -> `/c/Users/User/.local/bin/um`) and `um/ps1/WinDrive.ps1` + `um/ps1/ProcLoopback.ps1` exist in the repo; `um win setup` has **not** been run, so no command below has been exercised here. Everything is quoted from the named file; where a source is silent the cell says **UNKNOWN**.

# Q-PILOT step 1 — what universal-modder teaches an agent about driving a real game

Purpose: the pilot cards (launch, focus, screenshot, key input, record, read values, kill by PID) should be copied from a proven pattern, not invented. This page is the source-to-command map. One page per source follows, then the JC3-specific gaps.

## 0. The seven commands, one place

| capability | copy this, verbatim | from |
|---|---|---|
| launch | `um win launch "C:\Games\Foo\Foo.exe" -- -windowed` (or `um win launch --steam 105600`) | `skills/game-automation/SKILL.md:15` |
| find the window / PID | `um win ps` — "windowed processes: pid, name, title" | `skills/game-automation/SKILL.md:14` |
| focus | `um win drive --proc Terraria "focus"` | `skills/game-automation/SKILL.md:17`, WinDrive `focus` |
| screenshot | `um win shot --exe Terraria.exe shot.png --scale 0.33` | `skills/game-automation/SKILL.md:16` |
| key input | `um win drive --proc Terraria "hold 0x20 150" "sleep 200" "hold 0x20 150"` | `skills/game-automation/SKILL.md:18` |
| recording | `um win record --exe Game.exe --out C:\caps\take1 --seconds 40` then `um video mux C:/caps/take1.mkv C:/caps/take1.audio.raw C:/caps/take1.json take1.mp4 [--offset 0.25]` | `skills/showcase-video/SKILL.md:23,25` |
| reading values | mod-side command file + `until grep -q "<marker>" dev_log.txt; do sleep 1; done` (no JC3 equivalent proven — §8) | `knowledge/techniques/driving-a-game-from-a-mod-side-command-file-lab-profile-wake.md` |
| kill by PID | `um win kill <pid>` — "exact PID only" | `skills/game-automation/SKILL.md:20` |

Prerequisites and safety, both from `SKILL.md`: `um win setup` once (installs the PowerShell tools and a gfxcapture-capable ffmpeg), and input must only reach the game — WinDrive "refuses to send while another app is in the foreground" (`SKILL.md:38-40`).

## 1. `skills/game-automation/SKILL.md` — the operator's manual

| capability | what this file gives | status |
|---|---|---|
| launching | `um win launch --steam 105600` · `um win launch "C:\Games\Foo\Foo.exe" -- -windowed` · `um win setup` | Windows, documented (not run here) |
| focusing | WinDrive command `focus`, "bring the window to the foreground -> ok \| fail"; also `fg`, `title`, `untop` | Windows |
| screenshot | `um win shot --exe Terraria.exe shot.png --scale 0.33` — "full frame + a 1/3 copy that's cheap to look at"; window chosen by `--exe`/`--hwnd`/`--title` | Windows; gfxcapture cannot capture minimized windows |
| key input | `um win drive --proc Terraria "focus" "click 640 360" "key 0x1B" "type hello" "hold 0x44 1500"`; `hold <vk> <ms>`; `sleep <ms>` between steps; `scanmode on` for DirectInput/raw-input games; VK table `Esc 0x1B, Enter 0x0D, Space 0x20, W/A/S/D 0x57/0x41/0x53/0x44, F1 0x70, Shift 0x10, Ctrl 0x11, arrows 0x25-0x28` | Windows |
| recording | only referenced ("`um win shot`/`record` warn when [Auto HDR] is on"); detailed syntax in §5 | Windows |
| reading values | `um win ps`; `um win reg get "HKCU\Software\..."`; otherwise logs/bridge, not this file | Windows |
| kill by PID | `um win kill <pid>` — "exact PID only"; crash reporters (`BsSndRpt64.exe`, `CrashReportClient.exe`, `UnityCrashHandler64.exe`) cleared the same way | Windows |

Copy also: Python entry point — `from um.win import Drive, shot, Recorder`, `d = Drive("AoE2DE_s")`, `d.focus()`, `d.click(x, y)`, `d.key("0x0D")`; coordinates are in the game window's **client area**; `size <w> <h>` sets the client size and `um win drive --proc X "size 1920 1080"` "also resizes most windowed games".

## 2. `knowledge/techniques/driving-real-games-safely.md` — the hard rules

| capability | command / rule quoted | status |
|---|---|---|
| launching | launch detached or the shell waits for the game: `(cmd //c start "" "<exe>" >/dev/null 2>&1 &)`; prefer flags that skip menus (single player, no anti-cheat) | Windows, documented |
| focusing | tap Alt right before `SetForegroundWindow` when it "silently fails for a freshly launched game"; never type if focus is not yours | Windows |
| screenshot | coordinates: `[System.Windows.Forms.Screen]::PrimaryScreen.Bounds` vs the real resolution, then `click = screenshot_px / scale` (click coords are DPI-logical, captures are physical) | Windows 11 @150% |
| key input | down, sleep ~80 ms, up — one `SendInput` with both is shorter than a frame; extended keys (VK 0x21-0x28, 0x2D, 0x2E, 0xA3, 0xA5) need `KEYEVENTF_EXTENDEDKEY` (0x1); menu moves need ~0.6-0.7 s | Windows |
| recording | — | **UNKNOWN** in this file |
| reading values | `um win drive --proc <Game> idle` (seconds since the last real user input; does not wait) — the human-presence oracle | Windows |
| kill by PID | kill by exact PID; "Never kill by name pattern"; `pkill -f` killed the agent's own shell | Windows |

Safety content to copy into every card: check `idle` first and keep bursts short; "Never focus a game with an online mode while the human is typing" (the GTA V incident); the first click may only highlight — look at a screenshot after each click; unfocused games throttle (`InactiveSleepTime`, `runInBackground`, `t.IdleWhenNotForeground 0`); `PYTHONUTF8=1`/`PYTHONIOENCODING=utf-8` for `um win ps`/`shot`/`drive` on non-UTF-8 locales.

## 3. `knowledge/techniques/driving-a-game-from-a-mod-side-command-file-lab-profile-wake.md` — the input-free route

| capability | command / pattern quoted | status |
|---|---|---|
| launching | no launch command; the pattern starts at the title screen with `waitfor profiles` | **UNKNOWN** (game-specific, Outer Wilds 1.1.16 + OWML) |
| focusing | not needed — the point of the file | n/a |
| screenshot | `ScreenCapture.CaptureScreenshot` (Unity, "includes IMGUI") | Unity only |
| key input | none; commands act through the mod: `profile PortalLab`, `resume`, `wake`, `face`, `walk`, `reload` | Unity/OWML only |
| recording | contact sheets of screenshots at reduced size | Unity only |
| reading values | mod reads `dev_commands.txt` each frame, deletes it, appends results to `dev_log.txt`; agent polls `until grep -q "<marker>" dev_log.txt; do sleep 1; done`; flow control `wait <s>`, `waitfor <condition> <timeout>`, `trace <s>` at 20 Hz; `dump` prints state | Windows, Unity-mod-specific |
| kill by PID | "game killed by exact PID between builds (`um win kill`)" | Windows |

Copy the **protocol** (marker file `dev.enabled`, one file per sequence, poll a log for a marker, wait for the file to disappear before writing the next), not the commands: they call Outer Wilds classes. Gotchas worth a card: "Scene loaded" ≠ "player can act" (wait for input mode); short injected clicks are missed (<60 ms); commands lost/run twice when the file is read-then-deleted.

## 4. `knowledge/techniques/oracles-how-agents-know-a-mod-works.md` — how the pilot knows it worked

| capability | command / pattern quoted | status |
|---|---|---|
| launching | no launch command; rule: "Automate the whole loop, from launch through menus to scene, check and log, so one command answers 'did it work'" | Windows, principle |
| focusing | — | **UNKNOWN** |
| screenshot | `um win shot --scale 0.33`; and the stale-capture check: take two captures a second apart and compare SHA-256 | Windows |
| key input | — | **UNKNOWN** |
| recording | — (screenshots only) | **UNKNOWN** |
| reading values | game logs by engine: tModLoader `client.log`, BepInEx `LogOutput.log`, UE4SS.log, Unity `Player.log`, Minecraft `latest.log`; `um publish check --game <install>` | Windows |
| kill by PID | — | **UNKNOWN** |

Copy the two rules that make the other six safe: **a circuit breaker** ("after about 3 identical failures, stop, write down what you know, and change approach") and **prove the oracle can fail** (mutated builds/traces; a checker that stays green is not checking). The frozen-oracle gotcha matters for screenshots: `um win shot` (Windows.Graphics.Capture) went byte-identical three times while ReShade post-processing was active — "a frozen oracle inverts conclusions".

## 5. `knowledge/techniques/recording-game-footage.md` + `skills/showcase-video/SKILL.md` — the one source that quotes record syntax

| capability | command quoted | status |
|---|---|---|
| launching | — (record by window, not by launch) | **UNKNOWN** |
| focusing | record while rendering; a minimized window delivers no frame | Windows |
| screenshot | `um video first-frame C:/caps/take1.mkv` ("where gameplay starts") | Windows |
| key input | "for take A drive the picker from a second shell" — recording blocks | Windows |
| recording | `um win record --exe Game.exe --out C:\caps\take1 --seconds 40` -> `take1.mkv`, `take1.audio.raw`, `take1.json`; `um video mux C:/caps/take1.mkv C:/caps/take1.audio.raw C:/caps/take1.json take1.mp4 [--offset 0.25]`; flags from `um/win.py:543-557`: `--exe`, `--hwnd`, `--title`, `--out`, `--seconds`, `--fps` (default 30), `--no-audio`, `--crop left:top:right:bottom`, `--pid` | Windows (source: `.agents/skills/showcase-video/SKILL.md:23,25`) |
| reading values | ffmpeg `gfxcapture` + WASAPI process loopback of the game PID (`um/ps1/ProcLoopback.ps1`), raw f32 stereo 48 kHz placed by QPC timestamps | Windows |
| kill by PID | "Stop from a background thread, with a kill after a timeout"; never stop ffmpeg from the game's main thread | Windows |

Copy: `.mkv` iframe video, process-loopback audio, mux with a measured offset (~0.25-0.3 s encoder start-up, "measure once per machine"), NVENC H.264 limit 4096 px wide (crop or HEVC), and the audio trap — Windows per-app mute makes a process-loopback take exact silence; detect by maximum sample, not by ear.

## 6. `knowledge/techniques/a-force-quit-pc-game-relaunch-wedges-as-an-unkillable-zombie.md` — the launch budget

| capability | command / rule quoted | status |
|---|---|---|
| launching | "Quit the game cleanly to the desktop (in-game Quit / Exit), never Alt+F4 or a task kill"; "Assume one launch per boot"; "Batch your tests: make a single launch answer as many questions as possible" | Windows, Steam/Ubisoft |
| focusing | — (no window exists in the symptom) | **UNKNOWN** |
| screenshot | — | **UNKNOWN** |
| key input | — | **UNKNOWN** |
| recording | — | **UNKNOWN** |
| reading values | "log the discovery data *before* any risky action"; symptom is the mod log freezing mid-init, *before any hook installs* | Windows |
| kill by PID | all three fail on the zombie: `Stop-Process -Id <pid>`, `taskkill /F /PID <pid>`, `um win kill <pid>` -> "There is no running instance of the task." Recovery: reboot | Windows, documented |

This is the pilot's most expensive lesson and it shapes the cards: one launch per boot, a scripted take that answers many questions, and a **zombie check** (process present, one thread, no window, PID unkillable) before spending another launch. Also: clear lingering crash reporters by PID, and ask the human before removing D3D overlay hooks (ReShade `dxgi.dll`, Bandicam, Fraps) since they can wedge at `D3D11CreateDeviceAndSwapChain`.

## 7. `knowledge/games/just-cause-3/` — what the JC3 notes actually say

| capability | what the notes give | status |
|---|---|---|
| launching | **no command**. Compatibility facts only: "Windows, single-player, offline"; "owned on Steam; the install matches Steam build 20206564 (2025-12-17)"; `JustCause3.exe` timestamp `0x5787641c`; DLC under its own folder; "Dropzone files load in any launch" | **UNKNOWN** for a launch command |
| focusing | — | **UNKNOWN** |
| screenshot | — | **UNKNOWN** |
| key input | — | **UNKNOWN** |
| recording | — | **UNKNOWN** |
| reading values | offline file decoding only: `.toc`/`.ee` containers, RTPC/havok, RBMDL 1.16.0, and "Nothing here writes a file or launches the game" | **UNKNOWN** for in-game reading |
| kill by PID | — | **UNKNOWN** |

Files: `reading-the-vehicle-fleet-archives-rtpc-havok.md`, `translating-the-batmobile-row-ledger.md` (BmAK: GOG Premium 1.999, buildId 57731640734362250), `vehicle-mesh-editing-added-geometry-loads-with-matching-toc.md`. Their value to the pilot is **the build identity to pin** (Steam 20206564 / `JustCause3.exe` 0x5787641c) and the reminder that all JC3 knowledge in the repo so far comes from archives, not from a running game.

## 8. What stays UNKNOWN for the JC3 pilot

1. **JC3's Steam AppID** — not named in any source read (`--steam 105600` is Terraria). Would be found in Steam's library metadata, not in these notes.
2. **A working JC3 launch line** — no source quotes an exe path or windowed flags for JC3. The install path default in this repo (`jc3index.DEFAULT_GAME = D:/Games/Just Cause 3`) is a repo default, not a proven launch target; the exe name is stated (`JustCause3.exe`) but no launch command is.
3. **Whether `um win launch` / `drive` / `shot` control JC3 at all** — Avalanche engine, Steam+Ubisoft title; none of the notes tried it. Windows-generic mechanisms (gfxcapture, SendInput, exact-PID kill) are documented on other games; JC3-specific behaviour is untested and the test ban stands until `tmp/freebuff/APPROVED_Q.txt` exists.
4. **A JC3 in-game value reader** — the command-file bridge in §3 is a Unity/OWML C# pattern; no JC3 mod-side interpreter is described in either the technique notes or the JC3 notes. Reading values in-game for JC3 has no proven route in these sources.
5. **JC3's log / crash-reporter names** — no source read names them; the §1 rule (find the loader or game log first, then Event Viewer) is engine-generic.
6. **`um win record` on a Ubisoft-launched process** — the recorder takes `--exe`/`--pid`, and JC3 is launched through Ubisoft Connect per the zombie note's class of titles; whether audio loopback follows the right PID is untested here.

## 9. Do not copy (anti-patterns the sources name)

* `pkill -f <pattern>` / wildcard `taskkill /IM` — killed the agent's own shell (`driving-real-games-safely.md`).
* `gdigrab`/GDI screenshots of a GPU game — black frames (`recording-game-footage.md`).
* Treating screenshot pixels as click pixels — DPI shift, ~44 px drift at 150% (`driving-real-games-safely.md`, gotcha 7).
* Alt+F4 / task kill between tests, and fast quit→relaunch — the zombie (`a-force-quit-...zombie.md`).
* Stopping ffmpeg from the game's main thread — tail of the take lost (`recording-game-footage.md`).
* A screenshot oracle nobody compares — prove it is live with two hashes a second apart (`oracles-how-agents-know-a-mod-works.md`, gotcha 4).

## 10. Sources read (all paths under `C:/Users/User/source/repos/universal-modder/`)

`skills/game-automation/SKILL.md`; `skills/showcase-video/SKILL.md` (quoted for record/mux); `knowledge/techniques/driving-real-games-safely.md`; `knowledge/techniques/driving-a-game-from-a-mod-side-command-file-lab-profile-wake.md`; `knowledge/techniques/oracles-how-agents-know-a-mod-works.md`; `knowledge/techniques/recording-game-footage.md`; `knowledge/techniques/a-force-quit-pc-game-relaunch-wedges-as-an-unkillable-zombie.md`; `knowledge/games/just-cause-3/{reading-the-vehicle-fleet-archives-rtpc-havok,translating-the-batmobile-row-ledger,vehicle-mesh-editing-added-geometry-loads-with-matching-toc}.md`; `um/win.py` (argparse, lines 520-575) and `um/ps1/WinDrive.ps1` (command list lines 8-25) for verbatim flag/command names.

Local check, no launch: `command -v um` -> `/c/Users/User/.local/bin/um`; `um/ps1/WinDrive.ps1` and `um/ps1/ProcLoopback.ps1` exist; `um win setup` not run.
