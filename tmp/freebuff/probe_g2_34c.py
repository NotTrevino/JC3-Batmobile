"""G2-34 probe 3: fleet-wide census of the tether / rope / winch / cargo classes."""
import collections
import glob
import json
import os
import re

RAW = r"E:/Modding/JustCause3/_grab"
PAT = re.compile(r"grappl|tether|rope|winch|hook|cargobay|cargo_bay|tow", re.I)

classes = collections.Counter()
cls_entities: dict[str, set] = collections.defaultdict(set)
cls_values: dict[str, dict] = collections.defaultdict(dict)
paths = collections.Counter()
path_values: dict[str, set] = collections.defaultdict(set)
entities_with: dict[str, set] = collections.defaultdict(set)

files = sorted(glob.glob(os.path.join(RAW, "detail", "*.json")))
for p in files:
    d = json.load(open(p, encoding="utf-8"))
    ent = os.path.basename(p)[:-8]
    for o in ((d.get("epe") or {}).get("objects") or []):
        c = str(o.get("class") or "")
        n = str(o.get("name") or "")
        hit = bool(PAT.search(c) or PAT.search(n))
        if not hit:
            continue
        classes[c or "?"] += 1
        cls_entities[c or "?"].add(ent)
        entities_with[n].add(ent)
        for k, v in (o.get("values") or {}).items():
            if k.startswith("_") or k in ("name", "name_hash"):
                continue
            paths[f"{c}.{k}"] += 1
            cls_values[c][k] = v
            path_values[f"{c}.{k}"].add(str(v))

print("classes:", len(classes))
for c, v in classes.most_common():
    print(f"  {v:5}  {c:35} entities {len(cls_entities[c])}")
print("\nmembers per class:")
for c in classes:
    print(" ", c, "->", {k: cls_values[c][k] for k in cls_values[c]})
print("\nmember paths with >1 distinct value:")
for k, v in sorted(path_values.items()):
    if len(v) > 1:
        print(" ", k, len(v), sorted(v)[:6])
print("\ncargo bay entities:", len(cls_entities.get("CVehicleCargoBay", [])))
for e in sorted(cls_entities.get("CVehicleCargoBay", []))[:30]:
    print("   ", e)
print("\ntether hook entities:", len(cls_entities.get("CGrapplingHookPropData", [])))
for e in sorted(cls_entities.get("CGrapplingHookPropData", []))[:10]:
    print("   ", e)
print("\ninteraction names with reel/grapple:", sum(1 for n in entities_with if re.search("reel|grapple", n, re.I)))
for n in sorted(n for n in entities_with if re.search("reel|grapple", n, re.I))[:20]:
    print("   ", n, len(entities_with[n]))
