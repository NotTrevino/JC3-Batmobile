"""G2-22 probe 2: does any .epe graph name a .effc file? (the md claims 0)"""
import glob
import json
import os
import re

RAW = r"E:/Modding/JustCause3/_grab"
hits = []
files = sorted(glob.glob(os.path.join(RAW, "detail", "*.ee.json")))
strings = 0


def walk(o, path=""):
    global strings
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(o, str):
        strings += 1
        yield path, o


for p in files:
    d = json.load(open(p, encoding="utf-8"))
    for path, s in walk(d.get("epe") or {}):
        if ".effc" in s or ".ctunec" in s or ".trim" in s:
            hits.append((os.path.basename(p), path, s[:120]))
print("detail files", len(files), "string values", strings)
print("ext hits", len(hits))
for h in hits[:20]:
    print(h)

# also: how many FX_TABLE paths contain nitrous / tjump / exhaust, and which containers
rows = [json.loads(l) for l in open("Research/JC3Grab/FX_TABLE.jsonl", encoding="utf-8") if l.strip()]
print("fx rows", len(rows))
nit = [r for r in rows if "nitrous" in r["path"]]
print("nitrous paths", len(nit), "distinct", len({r['path'] for r in nit}),
      "containers", len({r['container'] for r in nit}))
print("sample", [r["path"] for r in nit[:8]])
name_where = [r for r in rows if "dynamic_nitrous" in json.dumps(r)]
print("rows mentioning dynamic_nitrous", len(name_where))
