import os, sys, struct, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3index

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
hits = [r for r in rows if "sound/" in r["path"] and ("fmod" in r["path"] or r["path"].endswith(".bank"))]
print("sound-bank index rows:", len(hits))
for r in hits[:40]:
    print(f"  {r.get('size',0):12d}  {r['path']}")
