import glob, json, os, collections, re
ENT = "E:/Modding/_JC3grab/entities"
paths = sorted(glob.glob(os.path.join(ENT, "*.ee.json")))
print("entity caches:", len(paths))
mods = collections.Counter()
allpaths = {}          # path -> n entities
drv = []
for p in paths:
    doc = json.load(open(p, encoding="utf-8"))
    seen = set()
    for mod in doc["modules"]:
        t = mod.get("type")
        rows = mod.get("rows") or []
        if t == "DriverLean" or mod.get("instance") == "DriverLean":
            rv = [r for r in rows if r["path"] == "righting_torque"]
            drv.append((doc["entity"], rv[0]["value"] if rv else None))
        for r in rows:
            allpaths.setdefault(r["path"], set()).add(doc["entity"])
        if t: seen.add(t)
    for t in seen: mods[t] += 1
print("module types:", len(mods), "distinct member paths:", len(allpaths))
print("entities with DriverLean:", len(drv))
for e, v in drv: print("   ", v, e)
print()
toks = ["air","upright","stay","self","stabil","flip","torque","lean","jump","gravity",
        "shov","dodge","ram","impact","collid","push","impulse","yaw","roll","pitch","bank"]
for t in toks:
    hit = [k for k in allpaths if t in k.lower()]
    print(f"{t:8s} {len(hit):4d}  " + ", ".join(sorted(hit)[:6]) + (" ..." if len(hit) > 6 else ""))
