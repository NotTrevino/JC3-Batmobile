"""chase2_08_pkg.py - second pass, route (a): does ANY shipped package carry these four defaults?

The first pass read the class default objects in `BmGame.upk` and `Engine.upk` only, and scanned
`Default__*Vehicle*` objects there. This tool covers the rest of the install:

  sweep  stream every `.upk` under the game folder (CookedPCConsole, DLC, Engine) looking for the
         three class names / `Default__` forms. A package can only serialise a tag whose class name
         it carries, so this names the candidate set exactly.
  scan   parse each named package and report every `Default__*` object whose tag stream holds one of
         the card offsets (F-60 0x4bc, F-62 0x17c, F-63 0x6d4, F-64 0x6d8) or a control neighbour
         (0x4b0/0x4b4/0x4b8/0x4c0 on the sim, 0x180 on the car sim, 0x6dc/0x6e0 on SVehicle).

Read-only: every file is opened `rb`; the JSON report is written outside the repo (R10).
"""
import argparse
import json
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight"
ROOTS = [os.path.join(GAME, "BmGame", "CookedPCConsole"),
         os.path.join(GAME, "DLC"),
         os.path.join(GAME, "Engine", "CookedPCConsole")]

NEEDLES = [b"Default__RVehicleSimBatmobile", b"Default__RVehicleSimCar",
           b"Default__SVehicle", b"RVehicleSimBatmobile", b"RVehicleSimCar",
           b"AirControlTimeInAir", b"AirControlTurnTorque",
           b"StayUprightRollResistAngle", b"StayUprightPitchResistAngle"]

OFFSETS = {0x4B0: "AirControlYawTorqueFactorMin (control)",
           0x4B4: "AirControlPitchTorqueFactorMin (control)",
           0x4B8: "AirControlInterpTime (control)",
           0x4BC: "F-60 AirControlTimeInAir",
           0x4C0: "BattleModeSlopeFactor (control)",
           0x17C: "F-62 AirControlTurnTorque",
           0x180: "RVehicleSimCar neighbour (control)",
           0x6D4: "F-63 StayUprightRollResistAngle",
           0x6D8: "F-64 StayUprightPitchResistAngle",
           0x6DC: "StayUprightStiffness (control)",
           0x6E0: "StayUprightDamping (control)"}

CHUNK = 8 << 20
OVERLAP = 96


def upks(root):
    for dirpath, _d, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".upk"):
                yield os.path.join(dirpath, fn)


def sweep(roots):
    hits, n, nbytes, t0 = {}, 0, 0, time.time()
    for root in roots:
        if not os.path.isdir(root):
            print(f"  (missing root {root})", flush=True)
            continue
        for path in upks(root):
            n += 1
            found, tail = [], b""
            with open(path, "rb") as fh:
                while True:
                    buf = fh.read(CHUNK)
                    if not buf:
                        break
                    nbytes += len(buf)
                    window = tail + buf
                    for nd in NEEDLES:
                        s = nd.decode()
                        if s not in found and nd in window:
                            found.append(s)
                    tail = window[-OVERLAP:]
            if found:
                hits[path] = found
                print(f"  HIT {path} -> {found}", flush=True)
            if n % 500 == 0:
                el = time.time() - t0
                print(f"  ... {n} files, {nbytes / 1e9:.1f} GB, {el:.0f}s "
                      f"({nbytes / 1e6 / max(el, 1e-9):.0f} MB/s)", flush=True)
    el = time.time() - t0
    print(f"\nswept {n} packages, {nbytes / 1e9:.2f} GB in {el:.0f}s; "
          f"{len(hits)} package(s) carry a needle", flush=True)
    return {"files": n, "bytes": nbytes, "seconds": round(el, 1), "hits": hits}


def scan_package(path):
    try:
        pkg = Package(path)
    except Exception as exc:                                     # noqa: BLE001
        return {"package": path, "error": f"{type(exc).__name__}: {exc}"}
    rows, ndefault = [], 0
    for i, e in enumerate(pkg.exports, 1):
        name = e["name"] or ""
        if not name.startswith("Default__"):
            continue
        ndefault += 1
        try:
            tags, _end, why = best_walk(pkg, pkg.data(i))
        except Exception as exc:                                 # noqa: BLE001
            continue
        hit = [(t.get("offset"), t.get("type"), t.get("value")) for t in tags
               if t.get("offset") in OFFSETS]
        if hit:
            rows.append({"export": i, "name": name, "tags": len(tags), "stop": why,
                         "offsets": [{"offset": h[0], "field": OFFSETS[h[0]], "type": h[1],
                                      "value": h[2]} for h in hit]})
    return {"package": path, "default_objects": ndefault, "carriers": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("sweep", "scan"))
    ap.add_argument("--root", action="append", default=None)
    ap.add_argument("--packages", nargs="*", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    if a.mode == "sweep":
        out = sweep(a.root or ROOTS)
    else:
        out = {"packages": [scan_package(p) for p in (a.packages or [])]}
        for row in out["packages"]:
            if "error" in row:
                print(f"{os.path.basename(row['package'])}: {row['error']}")
                continue
            print(f"{os.path.basename(row['package'])}: {row['default_objects']} Default__ exports, "
                  f"{len(row['carriers'])} carry a card offset")
            for c in row["carriers"]:
                print(f"   {c['name']} (export {c['export']}): {c['offsets']}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
