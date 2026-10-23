"""Summarise the two decompiled HUD movies into one comparable spec.

The movie bytes are carved by `bmak_hud.py` (BmAK) and `jc3index.py extract` (JC3).  This tool reads
the **decompiled output** of JPEXS Free Flash Decompiler (ffdec) for both and writes the parts the
translation needs:

  * stage size, frame count and the public `UC_*` interface (BmAK);
  * frame labels, the mode machine and the numeric constants (BmAK);
  * the vehicle cluster: speedometer, nitrous, health and weapon HUD entry points (JC3).

It never writes game content.  Point it at the decompile directories:

    python Tools/scripts/hud_spec.py \
        --bmak E:/Modding/_BmAK_grab/hud/dec \
        --jc3  E:/Modding/_JC3grab/hud/dec \
        --write

Reproduce the decompile first:
    java -jar ffdec.jar -export script <out> <movie.gfx>
    java -jar ffdec.jar -swf2xml <movie.gfx> <out>/movie.xml
    java -jar ffdec.jar -dumpSWF <movie.gfx> > <out>/tags.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Research" / "BatmobileGrab" / "HUD_SPEC.json"


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def external_images(dec: Path) -> list[str]:
    xml = dec / "movie.xml"
    if not xml.exists():
        return []
    text = read_text(xml)
    return sorted(set(re.findall(r'fileName="([^"]+)"', text)))


def bmak(dec: Path) -> dict:
    scripts = sorted((dec / "scripts").rglob("*.as"))
    as_text = {p.name: read_text(p) for p in scripts}
    main = as_text.get("ModuleStruct_Batmobile.as", "")
    master = as_text.get("ModularHudBm3.as", "")
    labels = []
    tags = dec / "tags.txt"
    if tags.exists():
        for m in re.finditer(r'FrameLabel \(name: "([^"]+)"\)', read_text(tags)):
            if m.group(1) not in labels:
                labels.append(m.group(1))
    setters = re.findall(r"public function (UC_[A-Za-z0-9_]+)\(([^)]*)\)", main)
    constants = {}
    for name in ("TickDeltaTime", "StageWidth", "StageHeight"):
        m = re.search(rf"{name}:Number\s*=\s*([0-9.]+)", master)
        if m:
            constants[name] = float(m.group(1))
    for name in ("MaxHealthChangePerFrame",):
        m = re.search(rf"{name}:Number\s*=\s*([0-9.]+)", main)
        if m:
            constants[name] = float(m.group(1))
    m = re.search(r"perspectiveProjection\.fieldOfView\s*=\s*([0-9.]+)", main)
    if m:
        constants["PerspectiveFOV"] = float(m.group(1))
    all_text = "\n".join(as_text.values())
    m = re.search(r'SWF\(width="([0-9]+)", height="([0-9]+)"', all_text)
    if m:
        constants["MovieWidth"], constants["MovieHeight"] = int(m.group(1)), int(m.group(2))
    return {
        "scripts": len(scripts),
        "external_images": external_images(dec),
        "frame_labels": labels,
        "uc_setters": [{"name": n, "args": a.strip()} for n, a in setters],
        "constants": constants,
        "mode_strings": sorted(set(re.findall(r'"(DRIVE|BATTLE|ZOOMED)"', main))),
        "has_battle_mode": "BattleAndZoomInterface" in main,
        "has_boost_gauge": "BoostMovie" in main and "UC_SetBoostLevel" in main,
        "has_energy_system": "BatmobileEnergySystem" in main,
        "has_winch": "WinchMeter" in main,
    }


def jc3(dec: Path) -> dict:
    scripts = sorted((dec / "scripts").rglob("*.as"))
    as_text = {p.name: read_text(p) for p in scripts}
    hud = as_text.get("hud.as", "")
    consts = {}
    for name in ("SPEEDO_SMOOTHING_TIME", "SPEEDO_DEGREES", "VEHICLE_FADE_IN_TIME",
                 "VEHICLE_FADE_OUT_TIME"):
        m = re.search(rf"{name}:[A-Za-z]*\s*=\s*([0-9.]+)", hud)
        if m:
            consts[name] = float(m.group(1))
    m = re.search(r'SWF\(width="([0-9]+)", height="([0-9]+)"', hud)
    if m:
        consts["MovieWidth"], consts["MovieHeight"] = int(m.group(1)), int(m.group(2))
    api = []
    for name in ("SetVehicleInfo", "SetVehicleType", "InitPrimaryMeter", "SetPrimaryMeterValue",
                 "InitVehicleNitrous", "UpdateVehicleNitrous", "HideVehicleNitrous",
                 "InitVehicleWeapons", "UpdateVehicleWeapons", "ShowVehicleUi", "HideVehicleUi",
                 "UpdateMechSpeedometer"):
        m = re.search(rf"public function {name}\(([^)]*)\)", hud)
        if m:
            api.append({"name": name, "args": m.group(1).strip()})
    return {
        "scripts": len(scripts),
        "external_images": external_images(dec),
        "constants": consts,
        "vehicle_api": api,
        "has_speedometer": "MCI_speedometer" in hud or "MCI_speedo" in hud,
        "has_nitrous": "MCI_nitro_meter" in hud,
        "has_vehicle_weapons": "InitVehicleWeapons" in hud,
        "has_vehicle_health": any("vehicle" in p.name.lower() for p in scripts)
                              or "hud_health" in " ".join(p.name for p in scripts),
        "vehicle_types": sorted(set(re.findall(r"VEHICLE_TYPE_[A-Z]+", hud))),
    }


def build(bmak_dir: Path | None, jc3_dir: Path | None) -> dict:
    out = {"jp_exs": "JPEXS Free Flash Decompiler (ffdec), CFX 0x0f"}
    if bmak_dir:
        out["bmak"] = bmak(bmak_dir)
    if jc3_dir:
        out["jc3"] = jc3(jc3_dir)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bmak", type=Path, help="ffdec output for HudModuleBatmobile.gfx")
    ap.add_argument("--jc3", type=Path, help="ffdec output for ui/hud.gfx")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.bmak and not a.jc3:
        raise SystemExit("give --bmak and/or --jc3")
    spec = build(a.bmak, a.jc3)
    if a.check:
        old = json.loads(OUT.read_text(encoding="utf-8"))
        bad = 0
        for side in ("bmak", "jc3"):
            if side in old and side in spec:
                for k, v in old[side].items():
                    if k in ("scripts", "constants"):
                        ok = v == spec[side][k]
                        print(f"{'PASS' if ok else 'FAIL'} {side}.{k}")
                        bad += not ok
        print(f"{'PASS' if not bad else 'FAIL'}: HUD spec")
        raise SystemExit(1 if bad else 0)
    if a.write:
        OUT.write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {OUT}")
    print(json.dumps(spec, indent=1)[:4000])


if __name__ == "__main__":
    main()
