"""chase2_04_pkgscan.py - chase2-04 route (a), complete half: does ANY shipped package name the field?

chase-04 read the class default object only inside `BmGame.upk` (235 `Default__*` objects) and the
15 `Playable_Batmobile*` archetypes. A patch or DLC package could still define a subclass whose
default object writes one of the `ImpactRoadAssist*` fields, so this walks EVERY `.upk` under the
install (base + DLC) and streams each one through a chunked byte search for

    ImpactRoadAssist, RVehicleBatmobileBase, Default__RVehicleBatmobile

A package can only serialise a property whose *name* is in its name table, so a package that does
not contain the string cannot carry a tag for that field. The output lists every file that does,
with the byte offsets of each hit, so a follow-up `chase02_cdo.py --package <file> --scan` can be
aimed at exactly those files.

Read-only: opens each package `rb`, writes nothing under the game folder. The report goes next to
the other chase decodes, outside the repo (R10).

Usage:
  python Tools/scripts/chase/chase2_04_pkgscan.py [--root DIR ...] [--out FILE]
"""
import argparse
import os
import time

NAMES = [b"ImpactRoadAssist", b"RVehicleBatmobileBase", b"Default__RVehicleBatmobile"]
ROOT = r"E:\Games\Batman - Arkham Knight"
OUT = r"E:\Modding\_gamedata\BmAKgrab\chase\chase2_04_pkgscan.txt"
CHUNK = 8 << 20
OVERLAP = 64  # a name cannot straddle a chunk boundary further than its own length


def scan_file(path: str) -> list[tuple[bytes, list[int]]]:
    hits: dict[bytes, list[int]] = {n: [] for n in NAMES}
    tail = b""
    base = 0
    with open(path, "rb") as f:
        while True:
            buf = f.read(CHUNK)
            if not buf:
                break
            blob = tail + buf
            for n in NAMES:
                at = blob.find(n)
                while at >= 0:
                    hits[n].append(base - len(tail) + at)
                    at = blob.find(n, at + 1)
            base += len(buf)
            tail = blob[-OVERLAP:]
    return [(n, hits[n]) for n in NAMES if hits[n]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", default=None)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    roots = a.root or [ROOT]
    files = []
    for root in roots:
        for dirpath, _dirs, names in os.walk(root):
            for n in names:
                if n.lower().endswith(".upk"):
                    files.append(os.path.join(dirpath, n))
    files.sort()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    t0 = time.time()
    total = 0
    found = 0
    with open(a.out, "w", encoding="utf8", newline="\n") as out:
        out.write(f"# chase2-04 package scan: {len(files)} .upk files under {', '.join(roots)}\n")
        out.write(f"# names: {', '.join(n.decode() for n in NAMES)}\n\n")
        for i, path in enumerate(files, 1):
            try:
                size = os.path.getsize(path)
                hits = scan_file(path)
            except OSError as e:  # unreadable file is reported, not skipped silently
                out.write(f"UNREADABLE {path}: {e}\n")
                continue
            total += size
            if hits:
                found += 1
                rel = os.path.relpath(path, ROOT)
                out.write(f"{rel}  ({size:,} B)\n")
                for name, offs in hits:
                    out.write(f"    {name.decode()} x{len(offs)} at {', '.join(f'0x{o:x}' for o in offs[:12])}"
                              f"{' …' if len(offs) > 12 else ''}\n")
            if i % 500 == 0:
                out.write(f"# progress {i}/{len(files)}, {total/1e9:.2f} GB, {time.time()-t0:.0f}s\n")
                out.flush()
                print(f"progress {i}/{len(files)} {total/1e9:.2f} GB {time.time()-t0:.0f}s", flush=True)
        out.write(f"\n# done: {len(files)} files, {total:,} B, {found} with any name, "
                  f"{time.time()-t0:.0f}s\n")
    print(f"done: {len(files)} files, {total:,} B, {found} with any name, {time.time()-t0:.0f}s")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
