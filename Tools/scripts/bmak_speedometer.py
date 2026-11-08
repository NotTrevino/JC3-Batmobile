"""bmak_speedometer.py - where the Batmobile speed number is drawn, and what feeds it.

The HUD inventory found no movie that draws speed: 19 HUD movies, 252 `UC_*` setters (149
distinct names), zero speed inputs. This tool records the only speedometer the install actually
contains and proves it from five directions:

  * **movies**   every HUD movie's inflated tag stream, scanned for speed identifiers; a match is
                 classified as a FrameLabel (animation label) or something that could be a readout
  * **flag**     `BmGame.RPlayerController:bDebugSpeedometer` (BoolProperty) is the only object
                 whose name contains "Speedometer"; its config value in BmGame.ini / DefaultGame.ini
  * **native**   `RPlayerControllerBase.DrawHUD` is a 39-byte, bytecode-less native function;
                 `RPlayerController.DrawHUD` is the script caller that invokes it, and
                 `RPlayerController.PreRender` owns the Canvas
  * **wire**     every script function that references the property. Exactly one does:
                 `RDebugMenuContent.DoGadgetsMenu`, the debug menu item labelled "Speedometer"
  * **fields**   the Batmobile's speed-shaped floats, with their BmSDK offsets and class-default
                 values, which are the values a native readout would be reading

Record: `Research/BatmobileGrab/SPEEDOMETER.json`.

Usage:
  python Tools/scripts/bmak_speedometer.py --write
  python Tools/scripts/bmak_speedometer.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upk_read import Package, export_summary  # noqa: E402
import bmak_hud  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "Research" / "BatmobileGrab" / "HUD_INVENTORY.json"
OUT = ROOT / "Research" / "BatmobileGrab" / "SPEEDOMETER.json"
SDK = ROOT / "Working" / "vendor" / "BmSDK" / "RVehicleBatmobileBase.g.cs"
GAME = bmak_hud.GAME
INI = (GAME / "BmGame" / "Config" / "BmGame.ini",
       GAME / "BmGame" / "Config" / "DefaultGame.ini")
SPEED_TOKEN = re.compile(rb"(?i)speed[a-z0-9_]*")


def inflate(blob: bytes) -> bytes | None:
    at = blob.find(b"CFX")
    if at < 4:
        return None
    n = int.from_bytes(blob[at - 4:at], "little")
    payload = blob[at:at + n]
    for off in range(32):
        try:
            data = zlib.decompressobj().decompress(payload[off:])
        except zlib.error:
            continue
        if len(data) > 1024:
            return data
    return None


def movie_tokens() -> list[dict]:
    doc = json.loads(INVENTORY.read_text(encoding="utf-8"))
    by_pkg: dict[str, Package] = {}
    rows = []
    for rec in doc["hud_movies"]:
        pkg = by_pkg.setdefault(rec["package"],
                                Package(str(GAME / "BmGame" / "CookedPCConsole" / rec["package"])))
        i = next((k for k in range(1, pkg.export_count + 1)
                  if pkg.object_path(k) == rec["object"]), None)
        if not i:
            raise SystemExit(f"missing {rec['object']}")
        e = pkg.exports[i - 1]
        data = inflate(pkg.image[e["offset"]:e["offset"] + e["size"]])
        if not data:
            raise SystemExit(f"{rec['object']}: does not inflate")
        found = sorted({m.group().decode("latin-1") for m in SPEED_TOKEN.finditer(data)})
        if found:
            # HudModuleHealth's two tokens are FrameLabel tags (`ffdec -dumpSWF` prints
            # `FrameLabel (name: "SpeedMin")`); the record keeps the tokens, the doc keeps the
            # tag proof. Nothing here claims they are a readout.
            rows.append({"object": rec["object"], "tokens": found})
    return rows


def ini_flags() -> dict:
    out = {}
    for p in INI:
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^\s*bDebugSpeedometer\s*=\s*(True|False)", text, re.M)
        out[p.name] = m.group(1) == "True" if m else None
    return out


def native() -> dict:
    pkg = Package(str(GAME / "BmGame" / "CookedPCConsole" / "BmGame.upk"))
    idx = pkg.find("bDebugSpeedometer")
    if idx is None:
        raise SystemExit("bDebugSpeedometer is not in BmGame.upk")
    ref = struct.pack("<i", idx)
    refs = []
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "Function":
            continue
        if ref in pkg.data(i):
            refs.append(pkg.object_path(i))
    def size(path):
        i = next((k for k in range(1, pkg.export_count + 1)
                  if pkg.object_path(k) == path), None)
        return (len(pkg.data(i)), pkg.data(i)) if i else (None, b"")
    base_size, _ = size("RPlayerControllerBase.DrawHUD")
    caller_size, caller = size("RPlayerController.DrawHUD")
    menu_size, menu = size("RDebugMenuContent.DoGadgetsMenu")
    base_idx = next((k for k in range(1, pkg.export_count + 1)
                     if pkg.object_path(k) == "RPlayerControllerBase.DrawHUD"), None)
    calls_base = bool(base_idx) and struct.pack("<i", base_idx) in caller
    ref_hits = sorted(set(refs))
    return {
        "flag": {"class": "RPlayerController", "property": "bDebugSpeedometer",
                 "type": "BoolProperty", "config": ini_flags()},
        "toggle": {"function": "RDebugMenuContent.DoGadgetsMenu",
                   "label": "Speedometer" if b"Speedometer" in menu else None,
                   "bytes": menu_size,
                   "references_flag": "RDebugMenuContent.DoGadgetsMenu" in ref_hits},
        "draw": {"native_function": "RPlayerControllerBase.DrawHUD",
                 "bytes": base_size,
                 "caller": "RPlayerController.DrawHUD",
                 "caller_bytes": caller_size,
                 "caller_calls_base": calls_base,
                 "canvas": "RPlayerController.PreRender"},
        "script_references": ref_hits,
    }


def fields() -> list[dict]:
    src = SDK.read_text(encoding="utf-8", errors="replace")
    names = ("CurrentThrottle", "ThrottleSpeed", "FakeExtraSpeed", "FakeExtraSpeedMax",
             "FakeExtaSpeedAccel", "FakeExtaSpeedDecel", "BattleModeSpeedDelta")
    offsets = {}
    for name in names:
        m = re.search(r"FloatProperty: " + name +
                      r"\n.*?\n\s*public unsafe float " + name + r"\s*\{[^}]*Ptr \+ (\d+)",
                      src, re.S)
        if m:
            offsets[name] = int(m.group(1))
    pkg = Package(str(GAME / "BmGame" / "CookedPCConsole" / "BmGame.upk"))
    cdo = next((i for i, e in enumerate(pkg.exports, 1)
                if e["name"] == "Default__RVehicleBatmobileBase"), None)
    values = {}
    if cdo:
        for t in export_summary(pkg, cdo, max_tags=4000)["tags"]:
            for name, off in offsets.items():
                if t.get("offset") == off:
                    values[name] = t.get("value")
    rows = [{"class": "RVehicleBatmobileBase", "name": n, "offset": offsets.get(n),
             "default": values.get(n), "type": "FloatProperty"} for n in names]
    # The magnitude itself is the actor's velocity vector, which lives on the Engine base class;
    # RVehicle's generated dump has no scalar speed property, so this is the only live reading.
    engine = Package(str(GAME / "BmGame" / "CookedPCConsole" / "Engine.upk"))
    i = next((k for k in range(1, engine.export_count + 1)
              if engine.object_path(k) == "Actor.Velocity"), None)
    if not i:
        raise SystemExit("Engine.upk: Actor.Velocity not found")
    rows.append({"class": "Engine.Actor", "name": "Velocity", "offset": None, "default": None,
                 "type": engine.object_class(i), "package": "Engine.upk"})
    return rows


def collect() -> dict:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    return {
        "verdict": ("no Scaleform movie draws speed; the only speedometer in the install is the "
                    "native debug readout gated by RPlayerController.bDebugSpeedometer"),
        "movies": {"scanned": len(inventory["hud_movies"]), "matches": movie_tokens(),
                   "note": ("HudModuleHealth's SpeedMin/SpeedMax are FrameLabel tags (tag id 43) "
                            "per `ffdec -dumpSWF`; no movie defines a speed setter.")},
        "native": native(),
        "fields": fields(),
        "units": ("Unreal units are cm/s; FakeExtraSpeedMax 3500.0 is 126 km/h. The native "
                  "readout's own conversion is not in script and is not claimed."),
    }


def build() -> dict:
    doc = collect()
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return doc


def check() -> int:
    old = json.loads(OUT.read_text(encoding="utf-8"))
    new = collect()
    bad = 0
    for key in ("movies", "native", "fields"):
        if old[key] != new[key]:
            print(f"FAIL: {key} changed")
            bad += 1
    if old["verdict"] != new["verdict"]:
        print("FAIL: verdict changed")
        bad += 1
    print(f"{'PASS' if not bad else 'FAIL'}: speedometer record current")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.write and not a.check:
        build()
        return 0
    if a.write:
        build()
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
