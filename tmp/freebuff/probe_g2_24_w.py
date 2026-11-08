import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3index

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
from collections import Counter
ext = Counter()
for r in rows:
    p = r["path"]
    if p.startswith("sound/") or "/sound/" in p:
        ext[os.path.splitext(p)[1].lower()] += 1
print("sound ext census:", ext.most_common(20))
for r in rows:
    p = r["path"]
    if p.lower().endswith((".fev", ".fsb", ".strings.bank", ".dlstrings", ".fevent")) or "banklist" in p:
        print(f"  {r.get('size',0):12d}  {p}")
