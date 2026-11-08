"""chase_namescan.py - does ANY shipped package name the eight chased properties?

Route 1 of chase-03: the G1 readers only looked at the 15 `Playable_Batmobile*` packages.
A field value can only be serialised by a package whose name table holds the property name
(a `FPropertyTag` carries the name as an FName, and FName strings are plain ASCII in the
package), so one pass over every `.upk` in `BmGame/CookedPCConsole` answers the question for
the whole install: which packages mention `StrafeForce`, `StrafeDuration`, … at all.

Read-only: opens each package, never writes to the install. Results go to
`E:\\Modding\\_gamedata\\BmAKgrab\\chase\\namescan.json`.

Usage:
  python chase_namescan.py            # full pass over every .upk
  python chase_namescan.py --limit 50 # first N files (smoke test)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time

NAMES = [b"StrafeForce", b"StrafeTorque", b"StrafeDuration", b"StrafeTime",
         b"StrafeRight", b"StrafeFwdCorrectionForce", b"StrafeTarget",
         b"TransformationAnimNode", b"StrafeCooldown"]
RX = re.compile(b"|".join(NAMES))
COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT = os.path.join(r"E:\Modding\_gamedata\BmAKgrab", "chase", "namescan.json")
CHUNK = 16 * 1024 * 1024
OVERLAP = 64


def scan(path: str) -> dict:
    hits: dict[str, int] = {}
    with open(path, "rb") as f:
        tail = b""
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            blob = tail + chunk
            for m in RX.finditer(blob):
                name = m.group(0).decode("ascii")
                hits[name] = hits.get(name, 0) + 1
            tail = blob[-OVERLAP:]
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(COOKED, "*.upk")))
    if a.limit:
        files = files[:a.limit]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    t0 = time.time()
    found: dict[str, dict] = {}
    total = 0
    for i, path in enumerate(files, 1):
        total += os.path.getsize(path)
        try:
            hits = scan(path)
        except OSError as exc:
            print("skip", path, exc)
            continue
        if hits:
            found[os.path.basename(path)] = hits
            print(f"HIT {os.path.basename(path)} {hits}", flush=True)
        if i % 200 == 0:
            print(f"{i}/{len(files)} files, {total / 1e9:.1f} GB, "
                  f"{time.time() - t0:.0f}s, {len(found)} with a hit", flush=True)
    rec = {"files": len(files), "bytes": total, "seconds": round(time.time() - t0, 1),
           "names": [n.decode() for n in NAMES], "packages_with_a_hit": found,
           "hit_count": len(found)}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    print(json.dumps({k: rec[k] for k in ("files", "bytes", "seconds", "hit_count")}))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
