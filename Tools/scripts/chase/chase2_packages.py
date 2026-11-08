"""chase2_packages.py - second pass, route (a): does ANY shipped package carry a default for these
classes, or a tag at the card offsets?

The first pass scanned `BmGame.upk` only, and only its `Default__*Camera*/*Batmobile*/*Vehicle*`
exports. This tool has two modes:

  sweep   stream every `.upk` under the game folder (BmGame + DLC) and report which ones contain the
          bytes `Default__R3rdPersonCamera` / `Default__RVehicleBatmobileBase` (a longer name such as
          `Default__R3rdPersonCamera_SomeSubclass` also matches, which is the point: subclass
          defaults are what could override F-9..F-16). Streaming, 8 MB chunks with overlap, so a
          62 GB install is read once and nothing is decompressed.
  scan    for each package the sweep named (or the ones given), parse it and report every export
          whose tag stream carries one of the card offsets, so an override is a decoded fact and
          not a string match.

Read-only: every file is opened `rb`, nothing is written under the game folder.

Usage:
    python Tools/scripts/chase/chase2_packages.py sweep --json OUT.json
    python Tools/scripts/chase/chase2_packages.py scan --packages a.upk b.upk
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
ROOTS = [os.path.join(GAME, "BmGame", "CookedPCConsole"), os.path.join(GAME, "DLC")]
NEEDLES = [b"Default__R3rdPersonCamera", b"Default__RVehicleBatmobileBase"]

# F-8 .. F-16, plus the three FFreeCameraConfig pitch/distance members this pass asks about.
OFFSETS = {0x3DF4: "BattleModeCamConfig", 0x3E9C: "BattleModeWinchCamConfig",
           0x3F44: "BattleModeAbseilingCamConfig", 0x4FD0: "BattleModeCamFOV",
           0x4FD4: "BattleModeWinchCamFOV", 0x4FDC: "BattleModeHeadOffset",
           0x4FF8: "BattleModeWinchHeadOffset", 0x5034: "BattleModeAbseilingExtraCameraRot",
           0x11E4: "StrafeCooldown",
           0x3E40: "CamConfig.maxPitch", 0x3E44: "CamConfig.MinPitch"}

CHUNK = 8 << 20
OVERLAP = 64


def upks(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".upk"):
                yield os.path.join(dirpath, fn)


def sweep(roots):
    hits, n, nbytes, t0 = {}, 0, 0, time.time()
    for root in roots:
        if not os.path.isdir(root):
            print(f"  (missing root {root})")
            continue
        for path in upks(root):
            n += 1
            found = []
            tail = b""
            with open(path, "rb") as fh:
                while True:
                    buf = fh.read(CHUNK)
                    if not buf:
                        break
                    nbytes += len(buf)
                    window = tail + buf
                    for nd in NEEDLES:
                        if nd in window and nd.decode() not in found:
                            found.append(nd.decode())
                    tail = window[-OVERLAP:]
            if found:
                hits[path] = found
                print(f"  HIT {path} -> {found}", flush=True)
            if n % 400 == 0:
                el = time.time() - t0
                print(f"  ... {n} files, {nbytes / 1e9:.1f} GB, {el:.0f}s "
                      f"({nbytes / 1e6 / max(el, 1e-9):.0f} MB/s)", flush=True)
    el = time.time() - t0
    print(f"\nswept {n} packages, {nbytes / 1e9:.2f} GB in {el:.0f}s "
          f"({nbytes / 1e6 / max(el, 1e-9):.0f} MB/s); {len(hits)} package(s) carry a needle")
    return {"files": n, "bytes": nbytes, "seconds": round(el, 1), "hits": hits}


def scan_package(path):
    try:
        pkg = Package(path)
    except Exception as exc:                                    # noqa: BLE001 - report, never crash
        return {"package": path, "error": f"{type(exc).__name__}: {exc}"}
    rows = []
    for i, e in enumerate(pkg.exports, 1):
        name = e["name"] or ""
        if not name.startswith("Default__"):
            continue
        try:
            tags, _end, why = best_walk(pkg, pkg.data(i))
        except Exception as exc:                                # noqa: BLE001
            rows.append({"export": i, "name": name, "error": str(exc)})
            continue
        hit = [(t.get("offset"), t.get("type"), t.get("value")) for t in tags
               if t.get("offset") in OFFSETS]
        if hit:
            rows.append({"export": i, "name": name, "tags": len(tags), "stop": why,
                         "offsets": [{"offset": h[0], "field": OFFSETS[h[0]], "type": h[1],
                                      "value": h[2]} for h in hit]})
    return {"package": path, "default_objects": sum(1 for e in pkg.exports
                                                   if (e["name"] or "").startswith("Default__")),
            "carriers": rows}


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
        pkgs = a.packages or []
        out = {"packages": [scan_package(p) for p in pkgs]}
        for row in out["packages"]:
            if "error" in row:
                print(f"{row['package']}: {row['error']}")
                continue
            print(f"{os.path.basename(row['package'])}: {row['default_objects']} Default__ exports, "
                  f"{len(row['carriers'])} carry a card offset")
            for c in row["carriers"]:
                print(f"   {c['name']} (export {c['export']}): {c['offsets']}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
