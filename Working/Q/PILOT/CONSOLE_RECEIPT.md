# Receipt — `xinput9_1_0.dll` (jc3-console-thingy v1.1) for Route A of SPAWN_BATMOBILE

Status: **STAGED, NOT INSTALLED.** This desk never writes into a game folder (INSTRUCTIONS §3 test
ban); installing it is an **operator pre-step**, done once, through this receipt.

## What it is

| field | value | evidence |
|---|---|---|
| tool | `jc3-console-thingy` (JC3 in-game console: `spawn`, `event`, `world`) | https://github.com/aaronkirkham/jc3-console-thingy (MIT) |
| release | `v1.1`, asset `jc3-console-thingy-steam.zip` | GitHub release API for tag `v1.1` |
| zip sha256 | `fa1c55f59ea8280c27034b9179b072b258aeaf8b5abd27766b53cde886fca3ea` | matches the API's own `digest` field |
| shipped file | `xinput9_1_0.dll`, 368,128 B | zip listing (one file) |
| dll sha256 | `379ad6c165c337c0e4fcce66ffac73a5dd86dbc68a39b81d3e7c4390780e1919` | `sha256sum` on the extracted file |
| staged copy | `Builds/probe-L0/P9-runtime-spawn/payload/xinput9_1_0.dll` | this repo, L0 probe P9 |
| target | `D:\Games\Just Cause 3\xinput9_1_0.dll` | the operator's install |

Address check: every address in the cloned source (`C:\Users\...` source at
`E:/Modding/_shared/tools/jc3-console-thingy`) was checked against the operator's 2025-12-17 `JustCause3.exe`
with `Tools/scripts/exe_addr_check.py` — function starts and call sites match (operator relay,
2026-11-08).

## Install (operator only)

1. Close JC3. Confirm no `JustCause3.exe` in `um win ps`.
2. Check whether the game already ships an `xinput9_1_0.dll` (JC3 does not normally; if one exists,
   **record it first** and copy it aside — that file may be another mod's hook).
3. `cp Builds/probe-L0/P9-runtime-spawn/payload/xinput9_1_0.dll "D:/Games/Just Cause 3/xinput9_1_0.dll"`
4. `sha256sum "D:/Games/Just Cause 3/xinput9_1_0.dll"` must print `379ad6c1…e1919`.

## Undo

    rm "D:/Games/Just Cause 3/xinput9_1_0.dll"

then `ls "D:/Games/Just Cause 3/xinput9_1_0.dll"` must say *No such file*. If step 2 found a
pre-existing file, restore that copy instead of deleting. Nothing else in the install is touched;
the DLL writes no config and the console has no persistence.

## What it costs if it goes wrong

* It is an injected in-process hook beside the dropzone payload, so a crash during a take is
  **ambiguous** and must be attributed by removing the DLL and repeating the take (SPAWN A7).
* The tool is from 2018/2025-release-build lineage, untested against this build: **UNKNOWN** whether
  it loads. A clean launch with no console on `~`/`F1` means Route B, not a STOP.
* The names it can spawn come from the game's own property table (`0xF71C2A21`); whether a
  **custom** `.ee` leaf is in it is **UNKNOWN** — the hint list is the only oracle.
