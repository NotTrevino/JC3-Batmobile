# G3-HUD-RADAR recheck - the radar numbers the report states, against the files

STATUS: done. All 8 numbers re-derive from the bytes or the AS3; **5 are SAME, 0 DIFFER, 3 have no
source in any file** (the report itself labels those UNKNOWN). The single disagreement found is
inside the old lane's own trail, not against the source: `Working/HUD/RADAR.json` records
`standalone_divisor: null` and `Working/HUD/RADAR.md` prints "divides the raw pixel radius by None",
while the AS3 divides by **400** at line 596 - so the report's 400 is right and its record is wrong.
Two of the numbers the brief asks about were never claimed: the report states **no icon size** and
the only rate it states is the movie's **30 fps**, not a radar refresh rate. No metre radius and no
pulse period exist in the files.

## What the report actually states (picked out of `tmp/freebuff/reports/G3-HUD-RADAR.md`)

| report text | kind |
|---|---|
| "stage **1024x720 px @ 30 fps**" | stage + only rate |
| "**80 px per distance unit** (decoded constant); world radius in metres **UNKNOWN**" | map scale + range |
| "Standalone debug build divides the pixel radius by **400**" | debug divisor |
| "**15** `UC_*` setters", "**113** sprites, **58** scripts" | counts |
| "tanks have bigger arrows - **CONFIRMED carrier, size UNKNOWN**" | icon size: no number |
| "`MapPulseTimer` period ... **UNKNOWN**" | pulse period: no number |

## The answer (full table, sources and JC3 column)

`Working/Translation/HUD_RADAR_RECHECK.md` carries the table with a source line per row and a
rewritten JC3-carry column. Summary:

| # | report value | found in the BmAK data | verdict | JC3 can carry |
|---|---|---|---|---|
| 1 | 80 px/unit | AS3 288/289/336/337 | SAME | no, only re-applied by the transplant (POIs are stage-pixel placed) |
| 2 | world radius m: UNKNOWN | no metre constant | no source (correct UNKNOWN) | nothing to carry |
| 3 | debug divisor 400 | AS3 596 `/ 400` | SAME (corrects RADAR.json) | no, debug only |
| 4 | icon size: none given | no icon width/height | no source (no claim made) | scale ratio only (`m_IconScale`) |
| 5 | 30 fps | GFx header `0x1e00`; 40 frames | SAME, but playback rate not radar refresh | yes, JC3 stage is also 30 fps |
| 6 | pulse period: UNKNOWN | `totalFrames - 55 - param1*30` (AS3 514); totalFrames is symbol content | no source (correct UNKNOWN) | no |
| 7 | stage 1024x720 | GFx header RECT, nbits 16 | SAME | height only; JC3 stage is 1280x720 |
| 8 | 15 UC_ setters | 15 in the module AS3 | SAME for the module script; 21 in `HUD_INTERFACES.json` | no, must be re-expressed as `UpdatePoi` data |

The BmAK data route matters: **`Research/BatmobileGrab/HUD.json` has no radar row at all** (its two
movies are `HudModuleBatmobile` and `StoryModeHUD`), and **`Tools/scripts/bmak_hud.py`'s `TARGETS`
are those same two objects**. The radar numbers live only in the carved
`BmGame.upk:HudModuleBespokeLocalRadar.Image` (66,317 B / 139,264 B, sha256 `f9f622d5a068919e`,
re-carved here through `bmak_hud.carve()`), its ffdec AS3 export, and `Working/HUD/RADAR.json`.
`HUD_SPEC.json` corroborates the stage (StageWidth 1024.0, StageHeight 720.0, TickDeltaTime 0.033)
for the *Batmobile* module, not the radar one.

JC3 evidence for the right-hand column is the decompiled HUD movie itself
(`E:/Modding/_shared/gamedata/JC3grab/hud/dec/scripts`): `hud.as` line 15
`[SWF(width="1280", height="720", backgroundColor="#666666", frameRate="30")]`, `hud.as`
3768/3812 `CreatePoi`/`UpdatePoi`, the demo POI placements `poi.x = 600 / 200 / ...`, and
`hud_code/poi.as` `UpdateIconScale` (764) + `UpdateArrow` (818) with 8 `ARROW_*` states drawn at
`{-135,-90,-45,0,45,90,135,180}` and `ARROW_POINT_AT = 1` declared with no case. `grep -ri minimap`
over all 260 JC3 HUD scripts: **0 matches** - so the old report's route (b) "JC3's minimap is AS3 in
`hud.gfx`" is not supported by the decompiled scripts; what exists is the POI marker system, not a
radar.

## Files written

- `Tools/scripts/hud_radar_recheck.py` - `--write` / `--check`; the check re-carves the movie,
  re-decodes the GFx header, re-reads the AS3, `HUD.json`/`HUD_SPEC.json` and the JC3 scripts, and
  rebuilds both outputs byte for byte.
- `Working/Translation/HUD_RADAR_RECHECK.md` - the short table.
- `Working/Translation/HUD_RADAR_RECHECK.json` - the same facts as data.
- this report.

No other file was edited; `Research/BatmobileGrab/HUD*`, `Working/HUD/*` and
`tmp/freebuff/reports/G3-HUD-RADAR.md` are untouched. Revert = delete the four files above.

## Commands and output (verbatim, final run)

```
$ uv run python Tools/scripts/hud_radar_recheck.py --write; echo "WRITE_EXIT=$?"
wrote Working\Translation\HUD_RADAR_RECHECK.md and HUD_RADAR_RECHECK.json
8 rows: 5 same, 0 differ, 3 no source
WRITE_EXIT=0

$ uv run python Tools/scripts/hud_radar_recheck.py --check; echo "CHECK_EXIT=$?"
PASS radar movie carves to 66317 / 139264 B
PASS radar gfx sha256 f9f622d5a068 matches the RADAR.json pin
PASS GFx header decodes 1024x720 @ 30.0 fps
PASS AS3 px/unit values = [80] at lines [288, 289, 336, 337]
PASS AS3 standalone divisor = [400] at line [596]
PASS AS3 rad->deg factor 57.3 present
PASS AS3 pulse frame base = [30]
PASS AS3 defines 15 UC_ setters
PASS no metre/world-radius constant in the AS3
PASS HUD.json and bmak_hud.TARGETS carry no radar row
PASS RADAR.json's standalone_divisor is null while the AS3 says 400 (record disagrees with the report)
PASS JC3 hud.gfx stage is 1280x720 @ 30 fps
PASS JC3 POI carries m_IconScale through Update()
PASS JC3 POIs are positioned in stage pixels by the caller
PASS Working\Translation\HUD_RADAR_RECHECK.md re-derives byte for byte
PASS HUD_RADAR_RECHECK.json re-derives byte for byte
PASS: G3-HUD-RADAR recheck 0 failure(s)
CHECK_EXIT=0
```

A first `--check` run failed one assertion (`no metre/world-radius constant in the AS3`) because the
probe matched the clip name `LockonAndHealthMeter`; the probe was narrowed to whole words and the
run above is the repaired one. No test, game or install script was run.

Blind decode used to fix the header layout (page note, not a project file):
`uv run python -c "...RECT bits..."` -> `nbits 16 [0, 20480, 0, 14400] w 1024.0 h 720.0`,
`fps raw 0x1e00 30.0`, `frames 40`, first tag bytes `11 fa 01 04 00 00` (a `FileAttributes`-style
tag header), which is why the header is trusted: it lands on 1024x720/30 with no tuning.

## UNKNOWNs

1. **World radius / range in metres.** No metre, km or radius constant in the module AS3
   (whole-word probes 0) and none in `HUD.json`/`RADAR.json`. It is whatever the native
   `RHudModuleLocalRadar` divides by before calling `UC_UpdateTargetPosition`; route:
   `upk_read.py` on `BmGame.upk`'s `RHudModuleLocalRadar` function bodies and `CLASS_DEFAULTS.json`.
   Not attempted here - it needs the native side, not the HUD data.
2. **Icon pixel sizes.** 113 `DefineSprite` carriers exist; none is measured in the AS3, and the
   frame→art table that would say *which* sprite is an icon is symbol content. Route: the
   `DefineSprite` bounds in `radar.gfx` (or ffdec `shapes/*.svg` viewBox values). The report is
   right to claim no size, so nothing here contradicts it.
3. **A radar update rate as such.** Both sides are event/call driven with no timer; the 30 fps in
   `[SWF]` and the GFx header is playback rate. Whether the native radar sends every tick is
   UNKNOWN (same native route as 1).
4. **`MapPulseTimer` period.** `UC_DoPulse` computes `totalFrames - 55 - param1*30`; `totalFrames`
   is a symbol property, so the seconds value cannot be read from the script. Route: the
   `MapPulseTimer_21` sprite's frame count in `radar.gfx`.
5. **Whether JC3's native POI placement uses world coordinates** (which would give the 80 px/unit
   something to attach to). The movie only receives/sets stage pixels (`poi.x = ...`); the world→
   screen transform is native. Route: JC3's `ui`/HUD caller in `hud.gfx`'s native side.
6. **The old report's route (b) premise.** It says JC3's minimap is AS3 in `hud.gfx`; 0 matches for
   "minimap" in all 260 scripts. Either the map is native or it lives in another movie. Route:
   search the other JC3 UI movies, not `hud.gfx`. Recorded as a correction to that report, not as a
   value here.
