"""G2-29 probe: which files mention the donor, and what the spawn-def table looks like."""
import json
import os
import re
import sys
import time

sys.path.insert(0, "Tools/scripts")
import jc3grab  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

DONOR = "v0300_car_kensington_sportsmuscle_civilian_01"
CHASSIS = "v0300_car_kensington_sportsmuscle"
EXT = {".bin", ".onlinec", ".gsc", ".gdc", ".btc", ".entityregc", ".stringlookup",
       ".epe", ".vmodc", ".toc", ".pfs", ".physicsc"}

rows = [json.loads(l) for l in open("Research/JC3Grab/INDEX.jsonl", encoding="utf-8")]
variants = [r for r in rows if CHASSIS in r["path"]]
print("index rows mentioning the chassis dir:", len(variants))

spellings = [DONOR, DONOR + ".ee",
             r"editor\entities\jc_vehicles\01_land\%s\%s.ee" % (CHASSIS, DONOR),
             "editor/entities/jc_vehicles/01_land/%s/%s.ee" % (CHASSIS, DONOR)]
hashes = {}
for s in spellings:
    hashes[s] = hash_jenkins(s.encode()) & 0xFFFFFFFF

targets = [r for r in rows if os.path.splitext(r["path"])[1].lower() in EXT]
print("scan set:", len(targets), "files,", round(sum(r["size"] for r in targets) / 1e6, 1), "MB")

t0 = time.time()
hits = []
for i, r in enumerate(targets):
    try:
        data = jc3grab.read_entry(r, jc3grab.DEFAULT_GAME)
    except Exception as exc:  # noqa: BLE001
        print("  read failed", r["path"], exc)
        continue
    n = data.count(DONOR.encode())
    h = sum(1 for s, v in hashes.items()
            for pat in (v.to_bytes(4, "little"), v.to_bytes(4, "big"))
            if pat in data)
    if n or h:
        hits.append((r["path"], r["mount"], r["size"], n, h))
print(f"scanned in {time.time() - t0:.1f}s; hits: {len(hits)}")
for path, mount, size, n, h in hits:
    print(f"  {n:4} str {h:3} hash  {size:9}  {mount:6} {path}")
