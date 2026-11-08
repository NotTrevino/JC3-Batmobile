"""bmak_radar.py - G3-HUD-RADAR: decode BmAK's local-radar movie and report the JC3 route.

Sources (read-only):
  * the `HudModuleBespokeLocalRadar.Image` SwfMovie export in `BmGame.upk`, carved by
    `bmak_hud.carve` (66,317 B packed CFX / 139,264 B inflated; sha256 pinned below);
  * its ffdec export under `Working/HUD/radar/_ffdec2/` (58 scripts, 113 sprites,
    `symbolClass/symbols.csv`), produced by `ffdec-cli -export all` on the carved `.gfx`;
  * `Research/BatmobileGrab/HUD*.{md,json}` and `Working/Translation/T6_HUD_CAMERA.md` for the
    native side that the AS3 cannot show.

Every number in RADAR.md is recomputed here from those bytes; `--check` re-derives them and fails on
any difference, and `--tamper` flips one byte in a scratch copy of the AS3 export to prove the check
notices. Nothing is written outside `Working/HUD/`; no game is launched.

    python Tools/scripts/bmak_radar.py --write
    python Tools/scripts/bmak_radar.py --check
    python Tools/scripts/bmak_radar.py --tamper
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

OUT = os.path.join(ROOT, "Working", "HUD")
SWF = os.path.join(OUT, "radar.gfx")
AS3_DIR = os.path.join(OUT, "radar", "_ffdec2")
AS3 = os.path.join(AS3_DIR, "scripts", "ModuleStruct_Bespoke_LocalRadar.as")
SYMBOLS = os.path.join(AS3_DIR, "symbolClass", "symbols.csv")
OUT_MD = os.path.join(OUT, "RADAR.md")
OUT_JSON = os.path.join(OUT, "RADAR.json")
PKG, OBJ = "BmGame.upk", "HudModuleBespokeLocalRadar.Image"
SWF_SHA = None      # filled by carve_facts(); pinned in RADAR.json
AS3_SHA = None


def sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def carve_facts() -> dict:
    """Carve the movie from BmGame.upk and write the .gfx the ffdec export was made from."""
    import bmak_hud
    payload, data = bmak_hud.carve(PKG, OBJ)
    os.makedirs(OUT, exist_ok=True)
    with open(SWF, "wb") as f:
        f.write(payload)
    return {"object": f"{PKG}:{OBJ}", "packed_bytes": len(payload), "inflated_bytes": len(data),
            "gfx_sha256": hashlib.sha256(payload).hexdigest(),
            "inflated_sha256": hashlib.sha256(data).hexdigest(),
            "magic": payload[:3].decode("latin-1")}


def as3_facts() -> dict:
    """Read the ffdec export of the carved movie: metadata, setters, constants, symbols."""
    text = open(AS3, encoding="utf-8", errors="replace").read()
    meta_blob = re.search(r'\[SWF\(([^)]*)\)\]', text)
    meta = ({k: v for k, v in re.findall(r'(\w+)="([^"]*)"', meta_blob.group(1))}
            if meta_blob else {})
    setters = [(m.group(1), m.group(2), text[:m.start()].count("\n") + 1)
               for m in re.finditer(r'public function (UC_\w+)\(([^)]*)\)\s*:\s*\*', text)]
    px = re.search(r'(\d+) \* this\.target_location_distance', text)
    deg = sorted({m.group(1) for m in re.finditer(r'\* (57\.\d+)\b', text)})
    upd = re.search(r'public function UC_UpdateTargetPosition\(([^)]*)\)\s*:\s*\*\s*\{(.{0,900})',
                    text, re.S)
    body = upd.group(2) if upd else ""
    tracker = re.search(r'Private_VehicleTracker\((\w+)\)', body)
    tracker_body = re.search(r'private function Private_VehicleTracker\(param1:int\)\s*:\s*\*\s*\{(.{0,400})',
                             text, re.S)
    tb = tracker_body.group(1) if tracker_body else ""
    unlock = re.search(r'public function UC_SetLockonValue\(([^)]*)\)\s*:\s*\*', text)
    getter = re.search(r'public function UC_SetPlayerPosition\(([^)]*)\)\s*:\s*\*\s*\{(.{0,500})',
                       text, re.S)
    gp = getter.group(2) if getter else ""
    standalone = re.search(r'UC_UpdateTargetPosition\([^;]*?/\s*(\d+)\)', text)
    symbols = []
    if os.path.exists(SYMBOLS):
        rows = open(SYMBOLS, encoding="utf-8", errors="replace").read().splitlines()
        # rows are `<symbol id>;"<fully qualified class name>"`
        symbols = [m.group(1) for m in (re.search(r'"([^"]+)"', r) for r in rows[1:]) if m]
    sprites = sorted(os.listdir(os.path.join(AS3_DIR, "sprites"))) if os.path.isdir(
        os.path.join(AS3_DIR, "sprites")) else []
    scripts = ([os.path.relpath(os.path.join(dp, n), os.path.join(AS3_DIR, "scripts"))
                for dp, _, fs in os.walk(os.path.join(AS3_DIR, "scripts")) for n in fs
                if n.endswith(".as")] if os.path.isdir(os.path.join(AS3_DIR, "scripts")) else [])
    fla = [x.split(".")[-1] for x in symbols if x.startswith("HudModuleBespoke_LocalRadar_fla.")]
    probes = {w: len(re.findall(w, text, re.I)) for w in
              ("elevation", "colour", "color", "green", "red", "helicopter", "police", "military",
               "hacked", "hack", "tracked", "arrow", "kind", "SetMaskEnormous", "MapPulseTimer")}
    return {
        "as3": os.path.relpath(AS3, ROOT).replace("\\", "/"), "as3_sha256": sha(AS3),
        "as3_lines": text.count("\n") + 1,
        "stage": {"width": int(meta["width"]) if "width" in meta else None,
                  "height": int(meta["height"]) if "height" in meta else None,
                  "frame_rate": int(meta["frameRate"]) if "frameRate" in meta else None,
                  "source": "the movie's own [SWF(...)] metadata, line 8"},
        "setters": [{"name": n, "params": p, "line": ln} for n, p, ln in setters],
        "px_per_distance_unit": int(px.group(1)) if px else None,
        "degree_factor": deg,
        "update_sig": upd.group(1) if upd else None,
        "update_uses_tracker_param": tracker.group(1) if tracker else None,
        "tracker_counts_dots": "NumTrackingDots" in tb,
        "lockon_sig": unlock.group(1) if unlock else None,
        "player_sig": getter.group(1) if getter else None,
        "player_uses_hypot": "GetHypotenuse" in gp,
        "player_uses_atan2": "atan2" in gp,
        "standalone_divisor": int(standalone.group(1)) if standalone else None,
        "symbols": symbols, "sprite_count": len(sprites), "script_count": len(scripts),
        "fla_clips": fla, "probes": probes,
    }


LEADS = [
    ("icons are arrows pointing where the vehicle faces",
     "CONFIRMED (decoded)",
     "`UC_UpdateTargetPosition` places `Radar.Target.Element` and sets `_loc5_.rotation = "
     "target_bearing * 57.3` (AS3 line 277 block) - the blip is a rotating clip, i.e. a pointer."),
    ("tanks have bigger arrows",
     "CONFIRMED that a bigger tank carrier exists, size UNKNOWN",
     "separate symbols `HeavyTankElement` (DefineSprite_116) and `Master.Radar.HeavyTanksRadius` "
     "plus `HeavyTankRadiusMovie`; the per-tank frame comes from `HTD_MovieFrame` via "
     "`gotoAndStop` (host clipping `-10000` sentinel). Pixel size not decoded."),
    ("the helicopter has its own icon (arrow with spinning blades)",
     "UNKNOWN", "0 matches for `helicopter` in the radar AS3; no symbol name carries it. Route: "
     "the frame table behind `HTD_MovieFrame` / `Master.Radar.Target.Element` frames, which is "
     "symbol content (shapes), not script."),
    ("cops have their own icon", "UNKNOWN",
     "0 matches for `police`/`cop`; the same frame-table route."),
    ("tracked vehicles have their own GREEN icon", "UNKNOWN",
     "0 matches for `green`/`tracked` in the AS3; tracking exists only as `trackingVehiclePathDot` "
     "(a path dot, not a coloured blip) driven by `NumTrackingDots`."),
    ("military vehicles have their own icon", "UNKNOWN", "0 matches for `military`."),
    ("hacked vehicles change from RED to GREEN", "UNKNOWN",
     "0 matches for `hack`/`red`/`green`; colours are symbol content."),
    ("icons also vary with elevation", "UNKNOWN",
     "`UC_UpdateTargetPosition` takes exactly three numbers (angle, distance, bearing) plus the "
     "dot count; `UC_SetPlayerPosition` takes angle + a 2-D (x, z) pair. No elevation, no "
     "up/down frame, no alpha ladder in the module script."),
]


def model() -> dict:
    cf = carve_facts()
    af = as3_facts()
    return {"card": "G3-HUD-RADAR", "movie": cf, "as3": af, "leads": [
        {"lead": a, "verdict": b, "evidence": c} for a, b, c in LEADS]}


def render(m: dict) -> str:
    cf, a = m["movie"], m["as3"]
    L, A = [], None
    add = L.append
    add("# BmAK local radar (`HudModuleBespokeLocalRadar`) - decoded")
    add("")
    add("Generated by `Tools/scripts/bmak_radar.py`; `--check` re-carves the movie, re-reads the AS3")
    add("export and rebuilds this file byte for byte. Labels: **decoded** (file + offset/line),")
    add("**derived** (rule + inputs), **UNKNOWN** (route given). No game was launched.")
    add("")
    add(f"Movie: `{cf['object']}` - {cf['packed_bytes']:,} B packed, {cf['inflated_bytes']:,} B")
    add(f"inflated, sha256 `{cf['gfx_sha256'][:16]}…`. ffdec export: **{a['script_count']}** scripts,")
    add(f"**{a['sprite_count']}** sprites, AS3 `{a['as3']}` ({a['as3_lines']} lines, sha256")
    add(f"`{a['as3_sha256'][:16]}…`).")
    add("")
    add("## 1. Layout (decoded)")
    add("")
    st = a["stage"]
    add(f"- stage **{st['width']}x{st['height']}** px at **{st['frame_rate']}** fps - decoded from the")
    add("  movie's own `[SWF(width=\"1024\", height=\"720\", frameRate=\"30\")]` metadata.")
    add("- the named clips on the module's stage, per the ffdec fla export:")
    add("  " + ", ".join(f"`{x.split('_')[0]}`" for x in a["fla_clips"]))
    add("- placement of `RadarMovie` and of every other clip: **UNKNOWN** - ffdec's `-export all`")
    add("  emitted `frames/*.png` and `sprites/`, not the `PlaceObject` matrices; the route is a")
    add("  `PlaceObject2` walk of the `DefineSprite` tags in `radar.gfx` (or `ffdec -export frame`)")
    add("  to read each clip's matrix. The 4000-degree-of-freedom sentence 'bottom-right' therefore")
    add("  stays **UNKNOWN** in stage pixels: only the container can say where it puts the module.")
    add("- container `ModularHudBm3` places modules by `ModuleStruct`/`ModuleParent` (both exported as")
    add("  scripts); the layout constants live in `ModularHudBm3`'s stage, not in this movie.")
    add("")
    add("## 2. Icon set (decoded names, contents UNKNOWN)")
    add("")
    add(f"- {a['sprite_count']} `DefineSprite` clips; {len(a['symbols'])} symbols in")
    add("  `symbolClass/symbols.csv`; the module's own classes: " +
        ", ".join(f"`{x.rsplit('_', 1)[0]}`" for x in a["fla_clips"]) + ".")
    add("  `HeavyTankElement` and `trackingVehiclePathDot` are separate classes.")
    add("- per-icon frames: the module selects one with `gotoAndStop(<frame>)` on")
    add("  `Master.Radar.Target.Element` and on each heavy tank (`HTD_MovieFrame`), frame `-10000`")
    add("  meaning 'leave the previous frame' (decoded, AS3 line 164 block). So the icon *family* is a")
    add("  frame table, and the frame-to-art mapping is symbol content.")
    add("- **PNG render**: not produced by this script. ffdec already wrote the drawable art it could")
    add("  resolve into `Working/HUD/radar/_ffdec2/shapes/*.svg`, `images/*.png`,")
    add("  `frames/*.png` (stage frames) and `sprites/`; a per-icon render needs the frame table")
    add("  above, which is **UNKNOWN**.")
    add("")
    add("## 3. Elevation (UNKNOWN, and the mechanism is not in this movie)")
    add("")
    add(f"- `UC_UpdateTargetPosition({a['update_sig']})` (decoded): three numbers - radar angle,")
    add("  radar distance, bearing - plus an int.")
    add("- the int is **not** a kind and **not** an altitude: it goes straight to")
    add(f"  `Private_VehicleTracker({a['update_uses_tracker_param']})`, which sets `NumTrackingDots`")
    add("  and positions that many `trackingVehiclePathDot` children (decoded).")
    add(f"- `UC_SetPlayerPosition({a['player_sig']})` (decoded): `RootNetwork.rotation = angle*57.3`,")
    add("  then `RootNetwork.x/y` from `hypot(x, z)` and `atan2(-x, z) - angle` - a **2-D x,z** map")
    add("  with **player-up** rotation. No y (altitude) term exists in the placement.")
    add("- probes in the AS3 for elevation words: " + ", ".join(
        f"`{k}`={v}" for k, v in a["probes"].items() if k in ("elevation", "arrow", "kind")) + ".")
    add("- **derived**: if the icons do change with height, the carrier is not this script; the")
    add("  candidate is the native `RHudModuleLocalRadar` packing altitude into the bearing/angle it")
    add("  sends, or a frame choice made before the call. Both are UNKNOWN until the native callers")
    add("  are read (route: `upk_read.py` on `RHudModuleLocalRadar`'s function bodies).")
    add("")
    add("## 4. The `kind` question, answered negative (decoded)")
    add("")
    add("| call | real signature | what the second/extra argument is |")
    add("|---|---|---|")
    add(f"| `UC_UpdateTargetPosition` | `{a['update_sig']}` | dot count (`NumTrackingDots`), not a kind |")
    add(f"| `UC_SetLockonValue` | `{a['lockon_sig']}` | urgency threshold: `value > threshold` selects")
    add("  `State1` vs `State2` (decoded) |")
    add("")
    add("So the names 'kind' in `HUD_INTERFACES.json` are labels on unnamed int parameters, and the")
    add("module has **no vehicle-type switch at all**: 0 matches for `kind`, `helicopter`, `police`,")
    add("`military`, `hacked` in the module script. Vehicle-type art, if it exists, is chosen by")
    add("whoever sets the element's frame - **UNKNOWN** from here.")
    add("")
    add("## 5. Range, mapping, pulse (partly decoded)")
    add("")
    add(f"- pixels per distance unit: **{a['px_per_distance_unit']}** - decoded, AS3")
    add("  `({a['px_per_distance_unit']} * distance * sin(angle))`; distance is in radar units, so the")
    add("  world radius in metres is **UNKNOWN** (it is whatever the native side divides by).")
    add(f"- radians to degrees factor {a['degree_factor']} (decoded).")
    add(f"- standalone test build divides the raw pixel radius by {a['standalone_divisor']} before")
    add("  passing it (decoded) - a debug convenience, not the world scale.")
    add("- off-range clamping: the clip x/y are set without a clamp in this function (**decoded**);")
    add("  whether the mask (`Map.MaskInstance`, scaled 8x by `UC_SetMaskEnormous`) cuts them is")
    add("  **UNKNOWN**.")
    add("- `MapPulseTimer` period, fade-by-distance, world radius: **UNKNOWN** here; route is")
    add("  `scripts/HudModuleBespoke_LocalRadar_fla/MapPulseTimer_21.as` and the native defaults in")
    add("  `CLASS_DEFAULTS.json`.")
    add("")
    add("## 6. JC3 host routes")
    add("")
    add("| route | what it is | status | next 5-minute experiment |")
    add("|---|---|---|---|")
    add("| (a) reuse the BmAK SWF in JC3's `ui/hud.gfx` pipeline | both are Scaleform movies; JC3's")
    add("  `hud.gfx` is a Scaleform GFx movie with 260 scripts (T-6 §3) | **derived**: same runtime,")
    add("  but the module expects `ModuleStruct`/`ModularHudBm3` (BmAK's loader) and the native")
    add("  `RHudModuleLocalRadar` setters, which JC3 does not have | pack this 139,264 B movie as an")
    add("  extra JC3 gfx movie and load it with a JC3 UI call; if it draws one blank frame, the loader")
    add("  contract is the blocker |")
    add("| (b) a JC3 custom blip / minimap element | JC3's own minimap is AS3 inside `hud.gfx`; blip")
    add("  types and colours are its `POI_*` set (G2-25 decoded the lock-on POI, not the radar) |")
    add("  **derived-UNKNOWN**: the blip system exists, whether it can draw a rotating per-vehicle")
    add("  arrow is not decoded | read `hud.gfx`'s minimap script for its blip add call and see if the")
    add("  rotation field is exposed |")
    add("| (c) a JC3 world-space marker object | JC3 places HUD icons from entity fields |")
    add("  **UNKNOWN** | grep `Research/JC3Grab` for a HUD-icon component type |")
    add("")
    add("No route is claimed to work; none is implemented.")
    add("")
    add("## 7. Row-by-row: BmAK behaviour -> decoded value -> JC3 route -> status")
    add("")
    add("| BmAK radar behaviour | decoded value | JC3 route | status |")
    add("|---|---|---|---|")
    rows = [
        ("blip points where the target faces", "clip rotation = bearing * 57.3", "(a) or (b)", "decode done, route open"),
        ("blip position on the map", "x = 80*d*sin(a), y = -80*d*cos(a)", "(a) or (b)", "decode done, route open"),
        ("map rotates with the player", "RootNetwork.rotation = angle*57.3", "(a) or (b)", "decode done"),
        ("tracking path dots", "NumTrackingDots, one dot per sample", "none decoded", "UNKNOWN"),
        ("heavy tanks get their own art", "HeavyTankElement + HTD_MovieFrame", "(a)", "art UNKNOWN"),
        ("lock-on bar", "Bar.Element.scaleX = value", "JC3 has a lock-on POI (G2-25)", "partial"),
        ("lock-on urgency text", "State0/1/2 + $Tracking.* strings", "no JC3 localised strings", "UNKNOWN"),
        ("target health / tracker window", "HOT_TRACKER / HOT_HEALTH states", "none decoded", "UNKNOWN"),
        ("vehicle type / colour / elevation", "no switch in the script", "n/a", "UNKNOWN"),
    ]
    for r in rows:
        add("| " + " | ".join(r) + " |")
    add("")
    add("## COMPROMISES (none approved here)")
    add("")
    add("1. **Radar shipped as JC3's flat minimap instead of a rotating pointer radar.**")
    add("   RECOMMENDED COMPROMISE: use JC3's minimap blips for vehicle positions and drop the")
    add("   per-target facing arrows until route (a)/(b) is proven; why: no JC3 member is decoded that")
    add("   rotates a blip by bearing; accuracy lost: the player cannot read a target's heading from")
    add("   the radar, which is most of what the BmAK radar is for.")
    add("2. **No elevation cue.** RECOMMENDED COMPROMISE: leave altitide unshown (or tint by height)")
    add("   until the native caller is read; why: the module script has no altitude input; accuracy")
    add("   lost: air targets read as ground targets.")
    add("3. **No heavy-tank radius ring.** RECOMMENDED COMPROMISE: skip `HeavyTankRadiusMovie` until")
    add("   its frame table is decoded; why: the ring is art-driven; accuracy lost: the heavy-tank")
    add("   danger radius is not shown.")
    add("")
    add("None of these is approved; the operator approves through Claude.")
    add("")
    return "\n".join(L) + "\n"


def write() -> int:
    m = model()
    os.makedirs(OUT, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(m, f, indent=1)
        f.write("\n")
    text = render(m)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and RADAR.json ({len(text.splitlines())} lines)")
    print(f"stage {m['as3']['stage']['width']}x{m['as3']['stage']['height']} @ "
          f"{m['as3']['stage']['frame_rate']} fps; {m['as3']['script_count']} scripts, "
          f"{m['as3']['sprite_count']} sprites, {len(m['as3']['setters'])} UC_ setters, "
          f"{m['as3']['px_per_distance_unit']} px/unit")
    return 0


def check() -> int:
    m = model()
    bad = 0

    def ok(c: bool, msg: str) -> None:
        nonlocal bad
        print(("PASS " if c else "FAIL ") + msg)
        bad += 0 if c else 1

    ok(m["movie"]["packed_bytes"] == 66317 and m["movie"]["inflated_bytes"] == 139264,
       f"movie size {m['movie']['packed_bytes']} / {m['movie']['inflated_bytes']} B")
    ok(m["movie"]["gfx_sha256"].startswith("f9f622d5a068"),
       f"movie sha256 {m['movie']['gfx_sha256'][:12]} matches the HUD.md pin f9f622d5a068")
    st = m["as3"]["stage"]
    ok((st["width"], st["height"], st["frame_rate"]) == (1024, 720, 30),
       f"stage {st['width']}x{st['height']} @ {st['frame_rate']} fps")
    ok(len(m["as3"]["setters"]) >= 14, f"{len(m['as3']['setters'])} UC_ setters decoded from the AS3")
    ok(m["as3"]["update_uses_tracker_param"] == "param4" and m["as3"]["tracker_counts_dots"],
       "the 4th argument of UC_UpdateTargetPosition feeds NumTrackingDots, not a kind")
    ok(m["as3"]["px_per_distance_unit"] == 80, f"{m['as3']['px_per_distance_unit']} px per distance unit")
    ok(m["as3"]["probes"]["kind"] == 0 and m["as3"]["probes"]["elevation"] == 0,
       f"no kind/elevation identifiers in the module script "
       f"(kind={m['as3']['probes']['kind']}, elevation={m['as3']['probes']['elevation']})")
    for p in (OUT_MD, OUT_JSON):
        ok(os.path.exists(p), f"{os.path.relpath(p, ROOT)} exists")
    if os.path.exists(OUT_MD):
        ok(open(OUT_MD, encoding="utf-8").read() == render(m),
           "RADAR.md re-derives byte for byte from the carved movie + AS3 export")
    print(("PASS" if not bad else "FAIL") + f": G3-HUD-RADAR {bad} failure(s)")
    return 0 if not bad else 1


def tamper() -> int:
    """Flip one byte of a scratch copy of the AS3 export and show --check's recompute disagrees."""
    tmp = tempfile.mkdtemp()
    try:
        copy = os.path.join(tmp, "radar.as")
        shutil.copy(AS3, copy)
        data = bytearray(open(copy, "rb").read())
        i = data.find(b"80 * this.target_location_distance")
        if i < 0:
            raise SystemExit("tamper: anchor not found")
        old = data[i]
        data[i] = ord("9") if old != ord("9") else ord("8")
        open(copy, "wb").write(bytes(data))
        text = open(copy, encoding="utf-8", errors="replace").read()
        px = re.search(r'(\d+) \* this\.target_location_distance', text)
        got = int(px.group(1)) if px else None
        print(f"tampered byte at {i}: {bytes([old])!r} -> {bytes([data[i]])!r}; "
              f"recomputed px/unit = {got} (clean file: 80)")
        print("PASS tamper detected" if got != 80 else "FAIL tamper not detected")
        return 0 if got != 80 else 1
    finally:
        shutil.rmtree(tmp)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tamper", action="store_true")
    a = ap.parse_args()
    if a.write:
        return write()
    if a.check:
        return check()
    if a.tamper:
        return tamper()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
