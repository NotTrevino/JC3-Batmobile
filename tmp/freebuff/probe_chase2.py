"""Throwaway probe: structure of the R3rdPersonCamera default object tags + absolute addresses."""
import os
import sys

sys.path.insert(0, r"E:/Modding/JustCause3/JC3-Batmobile/Tools/scripts")
from upk_read import Package, best_walk  # noqa

PKG = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk"
pkg = Package(PKG)
print("exports", len(pkg.exports), "names", len(pkg.names))
for i, e in enumerate(pkg.exports, 1):
    if e["name"] in ("Default__R3rdPersonCamera", "Default__RVehicleBatmobileBase"):
        data = pkg.data(i)
        tags, end, why = best_walk(pkg, data)
        print(f"\n{i} {e['name']} class={pkg.object_class(i)} size={e['size']} tags={len(tags)} stop={why}")
        print("  export file offset", hex(e["offset"]))
        for t in tags:
            if t.get("offset") in (0x3E9C, 0x4FD0, 0x4FD4, 0x4FDC, 0x4FF8, 0x5034, 0x11E4):
                print("  ", hex(t["offset"]), t["type"], "keys", sorted(t.keys()),
                      "at", hex(t["at"]), "abs", hex(e["offset"] + t["at"]),
                      "value", str(t.get("value"))[:60])
                if "props" in t:
                    print("     props", len(t["props"]), [(p.get("offset"), p.get("type"), p.get("value")) for p in t["props"][:4]])
        break
