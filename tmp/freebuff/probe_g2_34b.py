"""G2-34 probe 2: modules, objects and index entries that are actually about rope/tether/winch."""
import collections
import glob
import json
import os
import re

RAW = r"E:/Modding/JustCause3/_grab"
OUT = r"Research/JC3Grab"
TOK = re.compile(r"tether|rope|winch|grapp?nel|airlift|tow", re.I)
BAD = re.compile(r"propeller|dialogue|bark_", re.I)

# 1. index, token-targeted
hits = collections.Counter()
examples = collections.defaultdict(list)
for line in open(os.path.join(OUT, "INDEX.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    p = r["path"]
    if BAD.search(p):
        continue
    for m in set(x.lower() for x in TOK.findall(p)):
        hits[m] += 1
        if len(examples[m]) < 12:
            examples[m].append(p)
print("index token hits:", dict(hits))
for k, v in examples.items():
    print(k)
    for p in v[:12]:
        print("   ", p)

# 2. entity caches: module types and files with the tokens
print("\n--- entity cache modules")
mods = collections.Counter()
ents = collections.defaultdict(set)
for p in sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json"))):
    d = json.load(open(p, encoding="utf-8"))
    for m in d["modules"]:
        t = str(m.get("type"))
        f = str(m.get("file") or "")
        if TOK.search(t) or TOK.search(f):
            mods[(t, f.rsplit("/", 1)[-1])] += 1
            ents[(t, f.rsplit("/", 1)[-1])].add(d["entity"])
for k, v in mods.most_common():
    print(f"  {v:4}  {k[0]}  {k[1]}")

# 3. epe: object classes / names with the tokens
print("\n--- epe objects")
cls = collections.Counter()
names = collections.Counter()
vals = collections.Counter()
for p in sorted(glob.glob(os.path.join(RAW, "detail", "*.ee.json"))):
    d = json.load(open(p, encoding="utf-8"))
    for o in ((d.get("epe") or {}).get("objects") or []):
        c = str(o.get("class") or "")
        n = str(o.get("name") or "")
        if TOK.search(c):
            cls[c] += 1
        if TOK.search(n):
            names[n] += 1
        for k, v in (o.get("values") or {}).items():
            if isinstance(v, str) and TOK.search(v) and len(v) < 120:
                vals[v] += 1
print("classes", dict(cls))
print("names", dict(names.most_common(30)))
print("string values", dict(vals.most_common(20)))

# 4. v1602 and v4603 cargo tank module lists
for want in ("v1602_boat_urga_transport", "v4603_plane_urga_cargotransport_military_cargo_tank"):
    for p in sorted(glob.glob(os.path.join(RAW, "entities", f"*{want}*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if "military_cargo_tank" in want and "cargo_tank" not in d["entity"]:
            continue
        print("\n---", os.path.basename(p))
        for m in d["modules"]:
            print(f"   {str(m.get('type')):22} {str(m.get('file')).rsplit('/', 1)[-1]}")
