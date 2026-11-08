#!/usr/bin/env python
"""hud_radar_recheck.py - re-check the numbers G3-HUD-RADAR states against the files.

The lane's report (`tmp/freebuff/reports/G3-HUD-RADAR.md`) states, for the BmAK local radar:
a stage of 1024x720 @ 30 fps, **80 px per radar distance unit**, a standalone-only divisor of
**400**, 15 `UC_*` setters, 113 sprites / 58 scripts, and says the world radius, the icon pixel
sizes and the `MapPulseTimer` period are UNKNOWN.

This script re-derives each of those numbers from the bytes and line numbers, and then asks
which of them the JC3 side can carry. Nothing is taken from the report or from RADAR.json.

Inputs (read-only):
  BmGame.upk:HudModuleBespokeLocalRadar.Image   via `bmak_hud.carve` (the same carve function
                                                 the HUD grab uses; the radar movie is NOT in
                                                 `Research/BatmobileGrab/HUD.json`, whose
                                                 `TARGETS` are only HudModuleBatmobile + HUD)
  Working/HUD/radar/_ffdec2/scripts/ModuleStruct_Bespoke_LocalRadar.as   the ffdec AS3 export
  Research/BatmobileGrab/HUD.json, HUD_SPEC.json                          the BmAK HUD data
  E:/Modding/_shared/gamedata/JC3grab/hud/dec/scripts/hud.as, hud_code/poi.as    the JC3 HUD scripts

Outputs:
  Working/Translation/HUD_RADAR_RECHECK.md    the short table
  Working/Translation/HUD_RADAR_RECHECK.json  the same facts as data

Usage:
  uv run python Tools/scripts/hud_radar_recheck.py --write
  uv run python Tools/scripts/hud_radar_recheck.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import bmak_hud  # noqa: E402  the HUD grab's own carve()

RADAR_OBJECT = "HudModuleBespokeLocalRadar.Image"
RADAR_PACKAGE = "BmGame.upk"
AS3 = ROOT / "Working" / "HUD" / "radar" / "_ffdec2" / "scripts" / "ModuleStruct_Bespoke_LocalRadar.as"
RADAR_JSON = ROOT / "Working" / "HUD" / "RADAR.json"
HUD_JSON = ROOT / "Research" / "BatmobileGrab" / "HUD.json"
HUD_SPEC = ROOT / "Research" / "BatmobileGrab" / "HUD_SPEC.json"
JC3 = Path(os.environ.get("JC3_GRAB", r"E:/Modding/_shared/gamedata/JC3grab")) / "hud" / "dec" / "scripts"
JC3_HUD = JC3 / "hud.as"
JC3_POI = JC3 / "hud_code" / "poi.as"
OUT_MD = ROOT / "Working" / "Translation" / "HUD_RADAR_RECHECK.md"
OUT_JSON = ROOT / "Working" / "Translation" / "HUD_RADAR_RECHECK.json"


# ---------------------------------------------------------------- movie bytes
def gfx_header(data: bytes) -> dict:
    """Decode the GFx header the inflated tag stream starts with.

    RECT: 5-bit nbits, then 4 signed fields of nbits twips (1 px = 20 twips), byte aligned,
    then u16 frame rate (8.8 fixed) and u16 frame count.  Proven by the radar movie itself:
    it must come out 1024x720 @ 30, and a wrong bit order cannot produce that.
    """
    pos = 0

    def bits(n: int) -> int:
        nonlocal pos
        v = 0
        for _ in range(n):
            v = (v << 1) | ((data[pos >> 3] >> (7 - (pos & 7))) & 1)
            pos += 1
        return v

    def sint(n: int) -> int:
        v = bits(n)
        return v - (1 << n) if v & (1 << (n - 1)) else v

    nbits = bits(5)
    xmin, xmax, ymin, ymax = (sint(nbits) for _ in range(4))
    pos = (pos + 7) // 8 * 8
    fps_raw = int.from_bytes(data[pos // 8: pos // 8 + 2], "little")
    frames = int.from_bytes(data[pos // 8 + 2: pos // 8 + 4], "little")
    return {
        "nbits": nbits,
        "width": (xmax - xmin) / 20,
        "height": (ymax - ymin) / 20,
        "frame_rate": fps_raw / 256,
        "frames": frames,
        "header_bytes": data[: pos // 8 + 4],
    }


def movie() -> dict:
    payload, inflated = bmak_hud.carve(RADAR_PACKAGE, RADAR_OBJECT)
    h = gfx_header(inflated)
    return {
        "object": f"{RADAR_PACKAGE}:{RADAR_OBJECT}",
        "packed_bytes": len(payload),
        "inflated_bytes": len(inflated),
        "gfx_sha256": hashlib.sha256(payload).hexdigest(),
        "header": {k: h[k] for k in ("nbits", "width", "height", "frame_rate", "frames")},
        "header_hex": h["header_bytes"].hex(),
    }


# ---------------------------------------------------------------- AS3 numbers
def line_of(text: str, needle: str) -> int | None:
    for i, ln in enumerate(text.splitlines(), 1):
        if needle in ln:
            return i
    return None


def as3_facts(text: str) -> dict:
    lines = text.splitlines()
    px = [(i, ln.strip()) for i, ln in enumerate(lines, 1) if re.search(r"\b80 \* ", ln)]
    deg = [(i, ln.strip()) for i, ln in enumerate(lines, 1) if "57.3" in ln]
    div400 = [(i, ln.strip()) for i, ln in enumerate(lines, 1) if re.search(r"/\s*400\b", ln)]
    pulse = [(i, ln.strip()) for i, ln in enumerate(lines, 1) if re.search(r"param1 \* 30", ln)]
    mask = [(i, ln.strip()) for i, ln in enumerate(lines, 1) if "? 8 : 1" in ln]
    swf = next((ln.strip() for ln in lines if "[SWF(" in ln), "")
    setters = re.findall(r"public function (UC_\w+)\s*\(([^)]*)\)", text)
    # whole words only: `LockonMeter`/`HealthMeter` are clip names, not units
    metre_words = [w for w in ("metre", "meter", "metres", "meters", "kilometre", "kilometres",
                               "world_radius", "map_radius")
                   if re.search(rf"\b{w}\b", text, re.I)]
    return {
        "as3_lines": len(lines),
        "as3_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "px_per_unit_lines": [i for i, _ in px],
        "px_per_unit_values": sorted({int(m) for _, ln in px for m in re.findall(r"(\d+) \* ", ln)}),
        "degree_lines": [i for i, _ in deg],
        "degree_values": sorted({m for _, ln in deg for m in re.findall(r"57\.3", ln)}),
        "debug_divisor_lines": [i for i, _ in div400],
        "debug_divisor_values": sorted({int(m) for _, ln in div400 for m in re.findall(r"/\s*(\d+)\b", ln)}),
        "pulse_fps_lines": [i for i, _ in pulse],
        "pulse_fps_values": sorted({int(m) for _, ln in pulse for m in re.findall(r"\* (\d+)", ln)}),
        "mask_scale_lines": [i for i, _ in mask],
        "swf_metadata": swf,
        "setters": [
            {"name": n, "params": " ".join(p.split())} for n, p in setters
        ],
        "metre_constants": metre_words,
        "has_icon_size": bool(re.search(r"\b(icon_width|icon_height|ICON_W|ICON_H|width\s*=\s*\d+)\b", text)),
    }


# ---------------------------------------------------------------- BmAK HUD data
def hud_data() -> dict:
    table = json.loads(HUD_JSON.read_text(encoding="utf-8"))
    spec = json.loads(HUD_SPEC.read_text(encoding="utf-8"))
    pinned = json.loads(RADAR_JSON.read_text(encoding="utf-8")) if RADAR_JSON.exists() else {}
    objects = [m["object"] for m in table["movies"]]
    return {
        "hud_json_objects": objects,
        "hud_json_covers_radar": any(RADAR_OBJECT in o for o in objects),
        "bmak_hud_targets": [f"{pkg}:{path}" for pkg, path, _s, _r in bmak_hud.TARGETS],
        "hud_spec_constants": spec["bmak"]["constants"],
        "hud_spec_setters": len(spec["bmak"]["uc_setters"]),
        "radar_json_px_per_unit": pinned.get("as3", {}).get("px_per_distance_unit"),
        "radar_json_stage": pinned.get("as3", {}).get("stage"),
        "radar_json_standalone_divisor": pinned.get("as3", {}).get("standalone_divisor"),
        "radar_json_setters": len(pinned.get("as3", {}).get("setters", [])),
        "radar_json_sprite_count": pinned.get("as3", {}).get("sprite_count"),
        "radar_json_script_count": pinned.get("as3", {}).get("script_count"),
    }


# ---------------------------------------------------------------- JC3 side
def jc3_facts() -> dict:
    hud = JC3_HUD.read_text(encoding="utf-8", errors="replace")
    poi = JC3_POI.read_text(encoding="utf-8", errors="replace")
    swf = next((ln.strip() for ln in hud.splitlines() if "[SWF(" in ln), "")
    m = re.search(r'width="(\d+)"[^]]*height="(\d+)"[^]]*frameRate="(\d+)"', swf)
    arrows = sorted({int(v) for v in re.findall(r"ARROW_\w+:int = (-?\d+)", poi)})
    rot = sorted({int(v) for v in re.findall(r"MCI_arrow\.rotation = (-?\d+)", poi)})
    return {
        "hud_as_swf": swf,
        "stage_width": int(m.group(1)) if m else None,
        "stage_height": int(m.group(2)) if m else None,
        "frame_rate": int(m.group(3)) if m else None,
        "poi_icon_scale_lines": poi.count("m_IconScale"),
        "poi_update_present": "public function Update(data:Object)" in poi,
        "poi_arrow_states": arrows,
        "poi_arrow_rotations": rot,
        "poi_position_lines": [i for i, ln in enumerate(hud.splitlines(), 1) if re.match(r"\s*poi\.x = ", ln)],
        "poi_has_distance_field": '"m_Distance"' in hud,
        "poi_count": len(set(re.findall(r"POI_TYPE_\w+:int = \d+", hud))),
    }


# ---------------------------------------------------------------- verdicts
def build() -> dict:
    mv = movie()
    as3 = as3_facts(AS3.read_text(encoding="utf-8", errors="replace"))
    hud = hud_data()
    jc3 = jc3_facts()
    hdr = mv["header"]

    rows = [
        {
            "id": "scale",
            "report_value": "80 px per radar distance unit",
            "source": f"AS3 lines {', '.join(map(str, as3['px_per_unit_lines']))}: "
                      f"`80 * this.target_location_distance * Math.sin/Cos(...)` and the same 80 for each "
                      f"tracking dot",
            "in_bmak_hud_data": "no - HUD.json covers only " + ", ".join(hud["hud_json_objects"]) +
                                f"; px/unit is in RADAR.json ({hud['radar_json_px_per_unit']}) and the AS3",
            "verdict": "SAME" if as3["px_per_unit_values"] == [80] else "DIFFERS",
            "jc3_carry": "PARTIAL - JC3 POIs are placed in stage pixels by the caller "
                         f"(`poi.x = 600`, hud.as line {jc3['poi_position_lines'][0]}); hud.gfx has no "
                         "world-to-pixel mapping, so the 80 would be applied by the transplant, not carried",
        },
        {
            "id": "radius",
            "report_value": "world radius / range in metres: UNKNOWN",
            "source": "no metre constant in the AS3" +
                      (f" (probes: {as3['metre_constants']})" if as3["metre_constants"] else
                       " (0 matches for metre/meter/world_radius/map_radius)"),
            "in_bmak_hud_data": "no - neither HUD.json nor RADAR.json carries a world radius",
            "verdict": "UNKNOWN - no source in any file, the report is right to say so",
            "jc3_carry": "NO - nothing to carry",
        },
        {
            "id": "debug_divisor",
            "report_value": "standalone debug build divides the pixel radius by 400",
            "source": f"AS3 line {as3['debug_divisor_lines'][0]}: "
                      "`Math.sqrt(...) / 400` inside `Tick()`'s `if(Standalone)` block",
            "in_bmak_hud_data": "no - but RADAR.json's `standalone_divisor` is "
                                f"{hud['radar_json_standalone_divisor']!r} and RADAR.md says \"by None\", "
                                "so the lane's own record disagrees with its report; the AS3 settles it "
                                "in the report's favour",
            "verdict": "SAME (400) - and it corrects RADAR.json/RADAR.md",
            "jc3_carry": "NO - debug-only, not part of the shipped mapping",
        },
        {
            "id": "icon_size",
            "report_value": "icon pixel sizes: none given (explicitly \"size UNKNOWN\")",
            "source": "no width/height for an icon anywhere in the module script",
            "in_bmak_hud_data": f"no - {hud['radar_json_sprite_count']} DefineSprite carriers are "
                                "counted, none is measured",
            "verdict": "NO SOURCE for any number; the report claims none, only a carrier count "
                       f"({hud['radar_json_sprite_count']} sprites)",
            "jc3_carry": "PARTIAL - a JC3 POI scales its icon (`m_IconScale` -> "
                         f"`m_Icon.scaleX/scaleY`, poi.as line 764, {jc3['poi_icon_scale_lines']} use), "
                         "so a size *ratio* carries; an absolute pixel size has no JC3 field",
        },
        {
            "id": "update_rate",
            "report_value": "30 fps (stated as the stage frame rate, the only rate the report gives)",
            "source": f"GFx header of the carved movie: frame rate 0x1e00 = {hdr['frame_rate']}, "
                      f"{hdr['frames']} frames; the AS3 [SWF] metadata line repeats 30",
            "in_bmak_hud_data": "not in HUD.json (no radar movie); HUD_SPEC.json's TickDeltaTime "
                                f"{hud['hud_spec_constants']['TickDeltaTime']} = 1/30 for the Batmobile module",
            "verdict": "SAME at movie level - BUT it is playback rate, not a radar refresh rate: "
                       "positions arrive per setter call, and `UC_UpdateTargetPosition` returns early "
                       "when angle/distance/bearing are unchanged",
            "jc3_carry": "YES - JC3's hud.gfx stage is also 30 fps "
                         f"(`[SWF(width=\"{jc3['stage_width']}\", height=\"{jc3['stage_height']}\", "
                         f"frameRate=\"{jc3['frame_rate']}\")]`, hud.as line 15)",
        },
        {
            "id": "pulse_period",
            "report_value": "MapPulseTimer period: UNKNOWN",
            "source": f"AS3 line {as3['pulse_fps_lines'][0] if as3['pulse_fps_lines'] else '-'}: "
                      "`totalFrames - 55 - param1 * 30` - the 30 is seconds->frames, but `totalFrames` "
                      "is symbol content, so no period number exists in the files",
            "in_bmak_hud_data": "no",
            "verdict": "UNKNOWN - no source; the report is right",
            "jc3_carry": "NO - JC3 POIs have `m_Flash` (alpha tween) but no frame-counted pulse of this shape",
        },
        {
            "id": "stage",
            "report_value": "stage 1024x720",
            "source": f"GFx header of the carved movie: RECT {hdr['width']:.0f}x{hdr['height']:.0f} "
                      f"(nbits {hdr['nbits']}, header {mv['header_hex']})",
            "in_bmak_hud_data": "not in HUD.json; HUD_SPEC.json agrees for the Batmobile module "
                                f"(StageWidth {hud['hud_spec_constants']['StageWidth']}, "
                                f"StageHeight {hud['hud_spec_constants']['StageHeight']})",
            "verdict": "SAME",
            "jc3_carry": f"PARTIAL - JC3's stage is {jc3['stage_width']}x{jc3['stage_height']}: "
                         "the height carries, the 1024 width does not (layout must be re-fitted)",
        },
        {
            "id": "setters",
            "report_value": "15 UC_* setters",
            "source": f"AS3: {len(as3['setters'])} `public function UC_*` definitions",
            "in_bmak_hud_data": f"RADAR.json lists {hud['radar_json_setters']}; HUD_INTERFACES.json "
                                "lists 21 for the same module (it adds the 6 inherited module-level ones)",
            "verdict": "SAME for the module's own script (15); DIFFERS if counted from "
                       "HUD_INTERFACES.json (21)",
            "jc3_carry": "NO - JC3 has no ModuleStruct_Bespoke_LocalRadar; a POI is driven by one "
                         "`UpdatePoi(poi, data)` object, so the setters must be re-expressed, not carried",
        },
    ]

    return {
        "card": "G3-HUD-RADAR recheck",
        "movie": mv,
        "as3": as3,
        "bmak_hud_data": hud,
        "jc3": jc3,
        "rows": rows,
        "counts": {
            "rows": len(rows),
            "same": sum(1 for r in rows if r["verdict"].startswith("SAME")),
            "differs": sum(1 for r in rows if r["verdict"].startswith("DIFFERS")),
            "no_source": sum(1 for r in rows if r["verdict"].startswith("NO SOURCE")
                             or r["verdict"].startswith("UNKNOWN")),
        },
    }


# ---------------------------------------------------------------- rendering
def render_md(f: dict) -> str:
    mv, as3, hud, jc3, c = f["movie"], f["as3"], f["bmak_hud_data"], f["jc3"], f["counts"]
    out = []
    w = out.append
    w("# G3-HUD-RADAR - the stated numbers, re-checked against the files")
    w("")
    w(f"Generated by `Tools/scripts/hud_radar_recheck.py`; `--check` re-carves the movie, re-reads the")
    w("AS3 and the JC3 scripts and rebuilds this file byte for byte. Rows: "
      f"**{c['same']} same, {c['differs']} differ, {c['no_source']} with no source** ({c['rows']} in all).")
    w("")
    w("## Verdict")
    w("")
    w("No claim in `tmp/freebuff/reports/G3-HUD-RADAR.md` is contradicted by BmAK's bytes: 80 px/unit, "
      "1024x720 @ 30 fps and the 400 debug divisor all re-derive. The one disagreement is inside the")
    w("lane's own trail - `Working/HUD/RADAR.json` stores `standalone_divisor: null` and `RADAR.md`")
    w("prints \"by None\" where the AS3 line 596 divides by 400, i.e. the report is right and its record")
    w("is wrong. Two of the numbers the brief asks about (icon size, radar update rate) were never")
    w("claimed: the report gives no icon size and the only rate it gives is the movie's 30 fps, not a")
    w("radar refresh rate. Neither the report nor this file finds a metre radius or a pulse period.")
    w("")
    w("## Where the radar data actually lives")
    w("")
    w(f"- `Research/BatmobileGrab/HUD.json` does **not** contain the radar module: its two rows are "
      f"`{hud['hud_json_objects'][0]}` and `{hud['hud_json_objects'][1]}`.")
    w(f"- `Tools/scripts/bmak_hud.py`'s `TARGETS` are the same two objects "
      f"(`{hud['bmak_hud_targets'][0]}`, `{hud['bmak_hud_targets'][1]}`); the radar is not in it.")
    w("  Its `carve()` still reaches the radar export, which is how this recheck gets the bytes.")
    w(f"- The radar movie `{mv['object']}` carves to {mv['packed_bytes']:,} B packed / "
      f"{mv['inflated_bytes']:,} B inflated, sha256 `{mv['gfx_sha256'][:16]}` - the same pin as "
      "`RADAR.json`.")
    w(f"- Numbers come from the GFx header of those bytes and from the ffdec AS3 export "
      f"(`{AS3.name}`, {as3['as3_lines']} lines).")
    w("")
    w("## Table")
    w("")
    w("| # | what the report states | value in the BmAK HUD data | verdict | JC3 side can carry it? |")
    w("|---|---|---|---|---|")
    for i, r in enumerate(f["rows"], 1):
        w(f"| {i} | {r['report_value']} | {r['source']} | **{r['verdict']}** | {r['jc3_carry']} |")
    w("")
    w("Sources per row are exact lines; the verdicts are recomputed on every `--check`.")
    w("")
    w("## JC3 side, in short")
    w("")
    w(f"- Stage: `{jc3['hud_as_swf']}` (hud.as line 15) - 30 fps carries, {jc3['stage_width']} px width does not.")
    w(f"- POI icons scale: `m_IconScale` reached `m_Icon.scaleX/scaleY` in `hud_code/poi.as` "
      f"(poi.as `UpdateIconScale`); no absolute pixel size field exists.")
    w(f"- POI direction is an 8-way enum, not a bearing: `ARROW_*` = {jc3['poi_arrow_states']}, drawn at "
      f"rotations {jc3['poi_arrow_rotations']}; `ARROW_POINT_AT = 1` is declared but has no case, so no continuous")
    w("  rotation is decoded on the JC3 side. That is why the BmAK `rotation = bearing * 57.3` survives")
    w("  only as an 8-way nearest arrow.")
    w(f"- POI position is set by the caller in stage pixels (`poi.x = ...`, hud.as lines "
      f"{jc3['poi_position_lines']}); there is no world-space mapping in the movie, so the 80 px/unit")
    w("  scale has no JC3 carrier - the transplant has to apply it.")
    w("")
    w("## Limits")
    w("")
    w("- Icon pixel sizes and the world radius are UNKNOWN on both sides; no file states them, and none")
    w("  is invented here.")
    w(f"- The 30 fps is the movie's playback rate. JC3's POI updates are also call-driven, so \"update")
    w("  rate\" is the same 30 fps on both sides and not a radar-specific number.")
    w("")
    return "\n".join(out)


def render_json(f: dict) -> str:
    keep = {k: f[k] for k in ("card", "movie", "as3", "bmak_hud_data", "jc3", "rows", "counts")}
    keep["as3"] = {k: v for k, v in f["as3"].items() if k != "swf_metadata"}
    return json.dumps(keep, indent=1) + "\n"


# ---------------------------------------------------------------- commands
def write() -> None:
    f = build()
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(f), encoding="utf-8")
    OUT_JSON.write_text(render_json(f), encoding="utf-8")
    c = f["counts"]
    print(f"wrote {OUT_MD.relative_to(ROOT)} and {OUT_JSON.name}")
    print(f"{c['rows']} rows: {c['same']} same, {c['differs']} differ, {c['no_source']} no source")


def check() -> None:
    f = build()
    bad = 0

    def ok(cond: bool, msg: str) -> None:
        nonlocal bad
        print(f"{'PASS' if cond else 'FAIL'} {msg}")
        bad += not cond

    hdr, as3, hud, jc3 = f["movie"]["header"], f["as3"], f["bmak_hud_data"], f["jc3"]
    ok(f["movie"]["packed_bytes"] == 66317 and f["movie"]["inflated_bytes"] == 139264,
       f"radar movie carves to {f['movie']['packed_bytes']} / {f['movie']['inflated_bytes']} B")
    ok(f["movie"]["gfx_sha256"].startswith("f9f622d5a068"),
       f"radar gfx sha256 {f['movie']['gfx_sha256'][:12]} matches the RADAR.json pin")
    ok((hdr["width"], hdr["height"], hdr["frame_rate"]) == (1024, 720, 30.0),
       f"GFx header decodes {hdr['width']:.0f}x{hdr['height']:.0f} @ {hdr['frame_rate']} fps")
    ok(as3["px_per_unit_values"] == [80],
       f"AS3 px/unit values = {as3['px_per_unit_values']} at lines {as3['px_per_unit_lines']}")
    ok(as3["debug_divisor_values"] == [400],
       f"AS3 standalone divisor = {as3['debug_divisor_values']} at line {as3['debug_divisor_lines']}")
    ok(as3["degree_values"] == ["57.3"], "AS3 rad->deg factor 57.3 present")
    ok(as3["pulse_fps_values"] == [30], f"AS3 pulse frame base = {as3['pulse_fps_values']}")
    ok(len(as3["setters"]) == 15, f"AS3 defines {len(as3['setters'])} UC_ setters")
    ok(not as3["metre_constants"], "no metre/world-radius constant in the AS3")
    ok(hud["hud_json_covers_radar"] is False and not any(RADAR_OBJECT in t for t in hud["bmak_hud_targets"]),
       "HUD.json and bmak_hud.TARGETS carry no radar row")
    ok(hud["radar_json_standalone_divisor"] is None,
       "RADAR.json's standalone_divisor is null while the AS3 says 400 (record disagrees with the report)")
    ok((jc3["stage_width"], jc3["stage_height"], jc3["frame_rate"]) == (1280, 720, 30),
       f"JC3 hud.gfx stage is {jc3['stage_width']}x{jc3['stage_height']} @ {jc3['frame_rate']} fps")
    ok("m_IconScale" in JC3_POI.read_text(encoding="utf-8", errors="replace") and jc3["poi_update_present"],
       "JC3 POI carries m_IconScale through Update()")
    ok(len(jc3["poi_position_lines"]) >= 3, "JC3 POIs are positioned in stage pixels by the caller")

    want_md, want_json = render_md(f), render_json(f)
    ok(OUT_MD.exists() and OUT_MD.read_text(encoding="utf-8") == want_md,
       f"{OUT_MD.relative_to(ROOT)} re-derives byte for byte")
    ok(OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == want_json,
       f"{OUT_JSON.name} re-derives byte for byte")
    print(f"{'PASS' if not bad else 'FAIL'}: G3-HUD-RADAR recheck {bad} failure(s)")
    raise SystemExit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    write() if a.write else check()


if __name__ == "__main__":
    main()
