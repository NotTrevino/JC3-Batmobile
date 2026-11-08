import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3index

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
paths = sorted({r["path"] for r in rows if "jc_weapons/06_vehicle/" in r["path"]})
print(len(paths))
for p in paths:
    print("  ", p)
print()
for r in rows:
    if "w602" in r["path"] or "w603" in r["path"]:
        print("HIT", r["path"], r.get("size"))
