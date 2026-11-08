STATUS: partial - 9 probe folders built offline under `Builds/probe-L0/` (P1..P9, P9 first in the session). Only **P1** has a real binary payload; **P6/P7/P9** are run-sheets; **P2/P3/P4/P5/P8** are recorded BLOCKED/UNKNOWN with the exact missing writer, because no writer for them exists on this desk or in the community (see `tmp/freebuff/reports/jc3-community-writers-check.md`, written earlier in this task). Nothing was installed, nothing launched, `APPROVED_Q.txt` was not created, no existing `Builds/bm-*` tree was edited.

Generator + checker: `Tools/scripts/l0_probes.py` (`--write`, `--check`). Check: **PASS**, `11 files hashed, P1 shift = +1.0 m on Z`, exit 0.

# L0 probe payloads - offline build

Base for every probe: `Builds/bm-RC4`. Install route: `install_v3.py` only (never Rollback091: it deletes files, tracker V-06-RC2). One change per payload, one question per folder, receipt per folder (`receipt.json`: files, sha256, expected observation, pass/fail, undo).

## Run order
1. **P9 runtime-spawn** first - runtime spawning makes P4/P5/P7 much cheaper.
2. P1 physicsc-read, P7 damage-model, P6 use-vehicle-mod.
3. P2/P3/P4/P5/P8 only after their writer exists (see Gaps).

## P9 runtime-spawn (TEXT + staged DLL) - `Builds/probe-L0/P9-runtime-spawn/`
Source: `E:/Modding/_shared/tools/jc3-console-thingy/src/commands/spawn.h`, `src/game/spawn_system.h` (decoded).

- **Spawn argument: a string model name.** `spawn <arguments>` passes the raw argument string to `jc::CSpawnSystem::Spawn(arguments, transform, cb)`; that forwards `model_name.c_str()` to the native at `0x140E97DA0` with flags `0x2013C`. It is **not** an `.ee` path and **not** a hash.
- **Where:** the local player's transform with the translation replaced by `m_aimPos` and y + 1.0 m - the object appears at the crosshair, one metre up.
- **Names come from the property file**: `Initialize()` hooks `0x140EBFBD7` and adds every model name stored under hash `0xF71C2A21` to the tab-completion hints, so the table holds strings.

Commands (open the console first; key is in the tool's README):
```
spawn v0300_car_kensington_sportsmuscle_civilian_01     # stock Serpente (donor leaf)
spawn v0300_car_kensington_sportsmuscle_debug           # the RC4 Batmobile leaf
spawn v0300_car_kensington_sportsmuscle_debug           # second copy beside it (P5 subject)
```
Pass/fail: PASS = three named entities appear at the crosshair, console prints no error, the last two coexist; FAIL = no entity, an error, or a different model (then the hint table does not carry our leaf).

Staged (never installed to the game folder): `payload/xinput9_1_0.dll`, 368,128 B, sha256 `379ad6c165c337c0e4fcce66ffac73a5dd86dbc68a39b81d3e7c4390780e1919`, from release `v1.1` asset `jc3-console-thingy-steam.zip` (zip sha256 `fa1c55f59ea8280c27034b9179b072b258aeaf8b5abd27766b53cde886fca3ea`, matches the GitHub API `digest`). Addresses in that source were checked against the operator's 2025-12-17 exe with `Tools/scripts/exe_addr_check.py` (function starts and call sites match).

Unknown: whether the `0xF71C2A21` table lists a **replaced** leaf name (we kept the vanilla `_debug` root name, so it should), and whether the native accepts the same name twice in one call or needs two calls.

## P1 physicsc-read (READY) - `Builds/probe-L0/P1-physicsc-read/`
Change: every `hknpConvexPolytopeShape` in `Working/Collision/batmobile.physicsc` moved **+1.0 m on world Z**; all other bytes untouched. 54 hulls, 340,368 B -> 340,368 B (size unchanged).

Oracle in the writer: the new bytes are re-parsed and every shifted hull's vertices are compared to the source, must be `+1.0000` on Z (check prints `first vertex dz=+1.0000`).

Expected observation: on the same approach to a wall, the car stops ~1.0 m further out (or visibly sinks/floats, since the visual body does not move) than in the RC4 control. Pass = contact point differs by ~1.0 m; fail = identical (the `.physicsc` is not read).

Install: `payload/batmobile.physicsc` replaces the member **inside** the built `.ee` (the `.ee` is an AAF archive, magic `AAF\0`, so it is not a loose drop file) - repack with the existing `eetoc.py`/Gibbed SmallPack path used by B-10, then `install_v3.py`. Undo: `install_v3.py -Action rollback`. Details in `INSTALL.md` in the folder.

## P6 use-vehicle-mod (TEXT) - U3
Tap RPADRIGHT / hold 1.5 s / double-tap on the Batmobile, then the same on a stock Serpente as control; record turret, wheels, body, HUD, sound, speed. PASS = a reproducible, vehicle-scoped change the stock car does not show; FAIL = nothing, or the same on the stock car (U3 is vanilla).

## P7 damage-model (TEXT) - H0/H1/H2
Five takes, one weapon each: pistol 10 hits, rifle 10, MG 20, rocket 3, tank shell 3; count hits and read the bar after each. PASS = bar moves per hit with a stable ratio and 0 HP is an instant explosion; FAIL = small arms do not move the bar, a donor burn stage, or a crash.

## P2 keymap-dropzone (BLOCKED)
No writer exists here or in the community check (s1(f)). `settings/keymap_gamepad.bin` is 7,207 B, 145 bindings, 12-byte records then one 18-byte block + `PP`+name each, tiling to EOF; adding one binding means rewriting counts, block table and offsets. 5-minute prover: clone, duplicate one record+block, rewrite offsets, `jc3_input.py --check` must tile to EOF at 146 bindings. Community fallback is the text `Saves/kepmap.txt` (write-only after a 2016 patch), not a dropzone test.

## P3 hud-gfx (UNKNOWN, skipped as the brief allows)
A GFx writer exists (JPEXS FFDec `-replace` / `-header -set gfx`) but FFDec is **not installed** on this desk (`command -v ffdec` empty, no `Tools/ffdec*`), so no payload was shipped rather than a guessed patch of a 260-script movie.

## P4 audio-override (BLOCKED)
B-26 has no proven carrier (`Working/Roadmap/sound.md`: "no payload in RC4; entity-level bank override honoured? UNPROVEN"; blocker 3). RC4 ships **global** swapped banks (B-11); swapping one more GUID there answers "does the sample play", not "is it per entity". The settling experiment needs the game: private bank with an unmistakable tone bound only in the Batmobile's `.ee.fmod_guids`, stock Serpente spawned beside it, listen. Binding payload is card 9150 (not built).

## P5 second-entity (BLOCKED as a drop payload; P9 may replace it)
A second Rebel Drop entry needs a second leaf (renamed `.ee` root name + hash), a `spawn_vehicle_defs.bin` record, an `item.onlinec` record and a `task.onlinec` grant; `bm_rebel.py` builds exactly one entry. If P9's `spawn` resolves the RC4 leaf, P5 becomes "does the second spawn keep speed/health" with no new file.

## P8 effc-growth (BLOCKED)
`effc_writer.py` proves value edits only (95/95 round trip); there is no add/grow path, and `hud_cam_lights_fx.md` NEW-FX-1 (prove `.effc` can GROW) is still todo; no community tool either. 5-minute prover: duplicate an `EmitterTemplates` element by hand in a copy, decode must show 2 templates and re-encode byte-identically, control still round-trips.

# Files written
- `Tools/scripts/l0_probes.py` (generator + `--check`)
- `Builds/probe-L0/P1-physicsc-read/` - `payload/batmobile.physicsc`, `INSTALL.md`, `receipt.json`
- `Builds/probe-L0/P2-keymap-dropzone/` - `PROBE.md`, `receipt.json`
- `Builds/probe-L0/P3-hud-gfx/` - `PROBE.md`, `receipt.json`
- `Builds/probe-L0/P4-audio-override/` - `PROBE.md`, `receipt.json`
- `Builds/probe-L0/P5-second-entity/` - `PROBE.md`, `receipt.json`
- `Builds/probe-L0/P6-use-vehicle-mod/` - `PROBE.md`, `receipt.json`
- `Builds/probe-L0/P7-damage-model/` - `PROBE.md`, `receipt.json`
- `Builds/probe-L0/P8-effc-growth/` - `PROBE.md`, `receipt.json`
- `Builds/probe-L0/P9-runtime-spawn/` - `PROBE.md`, `payload/xinput9_1_0.dll`, `receipt.json`
- `tmp/freebuff/reports/jc3-community-writers-check.md` (earlier half of this task)

# Commands and output (verbatim)
```
=== release assets v1.1
  "name": "v1.1",
      "name": "jc3-console-thingy-steam.zip",
      "digest": "sha256:fa1c55f59ea8280c27034b9179b072b258aeaf8b5abd27766b53cde886fca3ea",
      "browser_download_url": "https://github.com/aaronkirkham/jc3-console-thingy/releases/download/v1.1/jc3-console-thingy-steam.zip"

=== zip sha256
fa1c55f59ea8280c27034b9179b072b258aeaf8b5abd27766b53cde886fca3ea *tmp/freebuff/scratch/jc3-console-thingy-steam.zip
=== zip contents
   368128  2026-01-11 15:23   xinput9_1_0.dll
=== dll
379ad6c165c337c0e4fcce66ffac73a5dd86dbc68a39b81d3e7c4390780e1919 *Builds/probe-L0/P9-runtime-spawn/payload/xinput9_1_0.dll
=== write
wrote 9 probe folders under Builds\probe-L0
P1: 54 hulls, 340368 -> 340368 B
write exit=0
=== check
P1: 54 polytopes, first vertex dz=+1.0000
PASS: 11 files hashed, P1 shift = +1.0 m on Z
check exit=0
```

# UNKNOWNs
- P9: the exact string in the `0xF71C2A21` property table for our leaf (`v0300_car_kensington_sportsmuscle_debug`) - derived from the RC4 build leaf, not read out of the game's table. If `spawn` errors, look it up in `settings/spawn_vehicle_defs.bin`.
- P1: the member path of the `.physicsc` inside the RC4 `.ee` (the AAF repack step is the B-10 build path, not a loose file), so P1 is payload-ready but not one-file drop-ready.
- P3/P4/P5/P8: no writer/binding exists; listed per probe above.
