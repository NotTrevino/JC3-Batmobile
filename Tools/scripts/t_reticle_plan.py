"""t_reticle_plan.py - verify the anchors of the reticle opt-in build plan.

Re-reads HUD_SPEC.json, the shipped radar AS3 (the only JC3 HUD source in the
repo), the two AutoAim presets and the built .epe bytes, then checks the report's
numbers and arithmetic. Read-only.

Usage:
  python Tools/scripts/t_reticle_plan.py --check
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "reticle-opt-in-build-plan.md")
SPEC = os.path.join(ROOT, "Research", "BatmobileGrab", "HUD_SPEC.json")
RADAR = os.path.join(ROOT, "Working", "HUD", "radar", "_ffdec2", "scripts",
                     "ModuleStruct_Bespoke_LocalRadar.as")


def main() -> int:
    ok: list[str] = []
    fails: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        (ok if cond else fails).append(f"{name}{(': ' + detail) if detail else ''}")

    if not os.path.isfile(REPORT):
        print("FAIL missing report")
        return 1
    md = open(REPORT, encoding="utf-8").read()
    for head in ("## 2. Weapon data", "## 3. The HUD elements", "## 4. BmAK versus JC3",
                 "## 5. The private", "## 7. UNKNOWNs"):
        check(f"section {head!r}", head in md)

    # ------------------------------------------------------------- HUD spec
    s = json.load(open(SPEC, encoding="utf-8"))
    b, j = s["bmak"], s["jc3"]
    check("bmak 99 scripts", b["scripts"] == 99)
    check("bmak 31 setters", len(b["uc_setters"]) == 31)
    check("bmak 112 frame labels", len(b["frame_labels"]) == 112)
    check("bmak 4 external images", len(b["external_images"]) == 4)
    check("bmak 1024x768", b["constants"]["MovieWidth"] == 1024 and b["constants"]["MovieHeight"] == 768)
    check("jc3 260 scripts", j["scripts"] == 260)
    check("jc3 9 atlases", len(j["external_images"]) == 9)
    check("jc3 1280x720", j["constants"]["MovieWidth"] == 1280 and j["constants"]["MovieHeight"] == 720)
    api = {x["name"]: x["args"] for x in j["vehicle_api"]}
    check("InitVehicleWeapons 9 args", api.get("InitVehicleWeapons", "").count(",") == 8)
    check("UpdateVehicleWeapons 6 args", api.get("UpdateVehicleWeapons", "").count(",") == 5)

    # ---------------------------------------------------------------- radar
    radar = open(RADAR, encoding="utf-8", errors="replace").read()
    check("SetLockonValue signature",
          "UC_SetLockonValue(param1:Number, param2:Number)" in radar)
    check("SetLockonValue writes scaleX", "LockonMeter.Bar.Element.scaleX = param1" in radar)
    check("SetLockonValue threshold use", "param1 > param2" in radar)
    check("UpdateTargetPosition 4 args",
          "UC_UpdateTargetPosition(param1:Number, param2:Number, param3:Number, param4:int)" in radar)
    check("tracking-dot count is param4", "Private_VehicleTracker(param4)" in radar)
    check("SetHealthValue exists", "UC_SetHealthValue" in radar)
    check("status text 3 states", all(x in radar for x in
          ("$Tracking.VehicleLockon", "VehicleNoLockon")))

    # --------------------------------------------------------------- report
    for token in ("0.12", "0.15", "750", "150", "6D4C8277", "00568A74", "2.0 s",
                  "60 frames", "45 frames", "5 … 30", "0.4", "32 KB", "0.2"):
        check(f"quote {token}", token in md)
    check("no stale kind claim", "value + **kind**" not in md)

    # ------------------------------------------------------------ arithmetic
    check("2.0 s = 60 frames", 2.0 * 30 == 60)
    check("1.5 s = 45 frames", 1.5 * 30 == 45)
    check("0.25 s = 7.5 frames", 0.25 * 30 == 7.5)
    check("256^2 BC1 = 32 KB", 256 * 256 // 2 == 32 * 1024)

    # ----------------------------------------------------------- build bytes
    ees = [p for p in glob.glob(os.path.join(ROOT, "Builds", "bm-006", "**", "*.epe"),
                                 recursive=True) if os.path.getsize(p) < 200_000]
    cur = None
    for p in ees:
        data = open(p, "rb").read()
        if b"autoaim_vehicle_no_lockon_missile" in data:
            cur = (p, data)
    check("built epe found", cur is not None, f"{len(ees)} scanned")
    if cur:
        p, data = cur
        check("current build has no lock-on preset", b"autoaim_vehicle_lockon_missile" not in data,
              os.path.relpath(p, ROOT))
        check("current build counts 0 CMissileWeaponBase", data.count(b"CMissileWeaponBase") == 0,
              str(data.count(b"CMissileWeaponBase")))
        check("current build has no-lockon preset", data.count(b"autoaim_vehicle_no_lockon_missile") >= 1)

    for line in ok:
        print("PASS", line)
    for line in fails:
        print("FAIL", line)
    print(f"\n{len(ok)} passed, {len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
