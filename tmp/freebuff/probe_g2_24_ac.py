import os, sys, struct, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3wiring

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME

for wid in ("w602", "w603", "w618", "w619"):
    cands = [r for r in rows if f"/{wid}_" in r["path"] and r["path"].endswith(".ee")]
    print("==", wid, len(cands))
    for r in cands[:6]:
        print("   ", r["path"], r.get("size"))
