STATUS: done — the wheel-check proposals P1/P2/P3/P4/P5 are applied to `Working/Q/PILOT/`. `RECORD.md` is **deliberately unchanged** (OBS is not installed on this machine). The console DLL is **not installed**; it has a receipt with an undo step. No game was launched, no install script run, no `APPROVED_Q.txt` written (it already existed, scoped by the operator).

# Pilot cards: wheel-check findings applied (2026-11-08)

Source report: `tmp/freebuff/reports/pilot-cards-wheel-check.md` §3. Rule followed for every card:
`tmp/freebuff/INSTRUCTIONS.md` §3 (translation/build allowed, test ban stands, never write under a
game install, never guess a value).

## Pre-edit record (required by the brief)
- `MODLOG.md` gained the entry **"Pilot cards: wheel-check proposals applied (2026-11-08, brief 8610)"**
  *before* any card was edited: intended change, files, why, and the revert.
- Old cards copied to `Working/Q/PILOT/_bak-20261108/` first (sha256 of the four originals):
  `LAUNCH.md 6696dcf9…`, `PROVE_CARDS.md afd12fc7…`, `RECORD.md c16cdaa8…`, `SPAWN_BATMOBILE.md 3b6a5c74…`.
- Revert: `cp Working/Q/PILOT/_bak-20261108/*.md Working/Q/PILOT/`, delete `CONSOLE_RECEIPT.md`, delete
  the MODLOG entry.

## Per card

### `LAUNCH.md` — applied P1 + P2, `sleep 120` and the frame-difference proof kept
- **Change.** Step 6's argument string gains `-quickstart`; a `NOTE` says the flag is a *loading*
  shortcut of unstated size and that a refusal means re-running the step once **without** it (recorded,
  not a STOP). Step 12's `sleep 120` is untouched and its NOTE says explicitly that the number is not
  shortened and only a *measured* time may replace it later. Steps 13–16 (frames B and C, different
  sha256) are the menu proof and were not edited. New pre-condition **P4** *checks*
  `D:/Games/Just Cause 3/dropzone/videos/corona_video.bikc` (zero-byte file); absent is **not** a STOP,
  and the card never creates it. Traps gained a paragraph with the three intro sources and the two
  unknowns.
- **Source line.** §3 **P1** ("`LAUNCH.md`, add `-quickstart` to step 6"; "Keep step 12's `sleep 120`
  unchanged: the flag's size of effect is unstated") and **P2** ("new pre-condition P4 (check only):
  intro file present"; "This makes the card's launch reproducible without making the card an
  installer"). Underlying evidence §1.1: jc3-console-thingy README quote, Steam guide 570542665,
  PCGamingWiki file 863.
- **What stays UNKNOWN.** U1 — how much `-quickstart` actually saves (the first run timestamps it and
  records it; nothing is shortened before that measurement). Whether the 2025-12-17 build still honours
  the empty `corona_video.bikc`, and whether creating it would perturb step 5's 9/9 dropzone
  verification — which is why the card only checks.
- **Verified.** `grep` shows `-quickstart` only on line 57 (the launch line) plus its notes; `sleep 120`
  at line 93; `launch_b.png`/`launch_c.png` captures and the `sha256sum` comparison still at 102/112/117.

### `RECORD.md` — NOT applied (P6), card left byte-identical
- **OBS check (read-only).** `ls -d "/c/Program Files/obs-studio" "/c/Program Files (x86)/obs-studio"
  "$LOCALAPPDATA/Programs/obs-studio"` → no output; `ls "/c/Program Files/obs-studio/bin/64bit/obs64.exe"`
  → nothing; `command -v obs64.exe obs-cmd` → nothing. **OBS Studio is not installed**, so
  `--startrecording` / websocket `StopRecord` cannot be used and proposal P6 would have made the card
  unrunnable.
- **Source line.** §3 **P6** ("replace steps 1–6 with OBS + websocket"), whose own risk clause says the
  card "must STOP, not fall back to `--no-audio`" if the scene/ffmpeg are missing — with no OBS at all,
  the honest state is "not applied".
- **Card state.** sha256 `c16cdaa8…` identical to the backup; `um win record`, the float32 peak reader
  and `--offset 0.25` all remain.
- **Side finding (not applied, outside the brief).** `ffmpeg` *is* present on this machine at
  `C:/Users/User/Downloads/ffmpeg-2026-03-09-git-9b7439c31b-full_build/bin/ffmpeg` — so the
  format-agnostic `volumedetect` silence check of §1.8 could replace the float32 reader **without**
  OBS. That edit was not requested; it is the first candidate if the operator wants RECORD improved.

### `SPAWN_BATMOBILE.md` — applied P3 + P4 (console primary, menu fallback)
- **Change.** The card now opens with a two-row **ROUTES** table (A console = primary, B Rebel Drop =
  fallback) and keeps every existing factual block verbatim (the `bm_rebel.py` built-field table and the
  six observed screens with their sources). **Route A** is new: A1 checks the DLL by sha256 against the
  receipt, A2–A4 open `~` (`key 0xC0`, F1 `0x70` as documented alternative) and prove the console by
  frame difference, A5 spawns `<BATMOBILE_HINT>`, A6 closes and captures, A7 checks the dump folder and
  demands crash attribution (remove the DLL, repeat the take) before the build is blamed. **Route B** is
  the old card renumbered B0–B9 with its text and `IF NOT` lines intact. `OPEN_DROP`,
  `DROP_ENTRY_CLICK`, `CONFIRM_CLICK` are now under "CALIBRATION (fallback only)". Pre-condition P3
  became "a route is usable" (DLL hash **or** calibration filled) so the console route is not blocked by
  the menu fields — this is the substance of the operator's ask.
- **Source line.** §3 **P3** ("add a console route ahead of Rebel Drop … Keep the Rebel Drop path as the
  fallback and keep the E-3 trap line") and **P4** ("move the three UNKNOWN fields out of the critical
  path … a calibration field that is only needed on a fallback is not a blocker"). Evidence §1.3
  (repo URL, MIT, `spawn` command, VGM mirror, r/JustCause quote) plus the decoded spawn semantics from
  `src/commands/spawn.h` / `src/game/spawn_system.h` recorded earlier in
  `tmp/freebuff/reports/l0-probe-payloads-offline.md`.
- **What stays UNKNOWN.** U2 — whether the 2018 DLL loads on this build; U3 — whether the name table
  (`0xF71C2A21`) carries our custom leaf, so `BATMOBILE_HINT` is read off the console's hint list on the
  first run, never invented; whether WinDrive can type at all (`type ...` is not in the command list this
  repo cites) — if it cannot, the take records `ACCEPTANCE: not met — console typing needed` and falls
  through to Route B; which key (`~` vs `F1`) the game binds.

### `PROVE_CARDS.md` — applied P5 (§2.1 console hint first)
- **Change.** §2.1 gained `SERPENTE_HINT` as the primary route and demoted `SERPENTE_SPAWN` to
  "ROUTE B (fallback)"; P3 now passes when *either* field is filled; steps 2/2b/2c do console-open →
  frame proof → `type spawn <SERPENTE_HINT>`, with 2F holding the old calibrated route unchanged.
  §1's P3 row and the §2.1 TRAPS line were updated; the approval-gate paragraph now states the file is
  present on 2026-11-08 and that the scope line is read in P1.
- **Source line.** §3 **P5** ("replace the `SERPENTE_SPAWN` calibration with a console hint … keeping
  the `grep …` refusal test so the card still cannot run unfilled").
- **What stays UNKNOWN.** The exact hint string for `v0300_car_kensington_sportsmuscle_civilian_01`
  (not in any repo file or source read — §1.10 says the same); whether `type` exists in WinDrive.

## Console DLL receipt (new file `Working/Q/PILOT/CONSOLE_RECEIPT.md`)
Staged, **not installed**. Release `v1.1` asset `jc3-console-thingy-steam.zip`, zip sha256
`fa1c55f59ea8280c27034b9179b072b258aeaf8b5abd27766b53cde886fca3ea` (matches the GitHub API `digest`),
`xinput9_1_0.dll` 368,128 B, sha256 `379ad6c165c337c0e4fcce66ffac73a5dd86dbc68a39b81d3e7c4390780e1919`,
staged at `Builds/probe-L0/P9-runtime-spawn/payload/xinput9_1_0.dll`. Install is an operator pre-step
(close the game, record any pre-existing `xinput9_1_0.dll` first, copy, re-verify the hash). **Undo:**
`rm "D:/Games/Just Cause 3/xinput9_1_0.dll"` (restore the pre-existing file if step 2 found one). The
receipt also records the blast radius: a second in-process hook, so a crash needs attribution before the
payload is blamed.

## `native-hook-design-jc3mp-contract.md`
**Not present** in `tmp/freebuff/reports/` (the directory listing shows no such file). The spawn
semantics used by the cards therefore rest on the cloned source at `E:/Modding/_shared/tools/jc3-console-thingy`
plus `exe_addr_check.py` (operator relay), as recorded in `tmp/freebuff/reports/l0-probe-payloads-offline.md`.

## Verification run
```
=== RECORD.md unchanged?          c16cdaa8… == c16cdaa8…   (identical)
=== changed lines vs backup       LAUNCH 32, SPAWN_BATMOBILE 136, PROVE_CARDS 51, RECORD 0
=== LAUNCH constraints            -quickstart line 57; sleep 120 line 93; launch_b/c + sha256 lines 102/112/117
=== console route present         SPAWN_BATMOBILE 8,21,57,59,61,77 …; PROVE_CARDS 44,86,87,90,103,125,164
=== fallback fields kept          9 occurrences of OPEN_DROP / DROP_ENTRY_CLICK / CONFIRM_CLICK
=== MODLOG                        1 entry
```
Nothing was launched; no file was written under a game install; `APPROVED_Q.txt` was not created or
edited by this task.

## UNKNOWNs (all four are first-run measurements, none blocks the session)
1. U1 `-quickstart`'s real saving — timestamped on the first launch, `sleep 120` unchanged until then.
2. U2 the DLL loading on the 2025-12-17 build — a clean launch with no console on `~`/`F1` means Route B.
3. U3 a custom `.ee` leaf being in the name table — the console's hint list is the oracle.
4. WinDrive's ability to *type* text (`type ...`) — if absent, the operator types once and the run is
   scored `ACCEPTANCE: not met — console typing needed`.
