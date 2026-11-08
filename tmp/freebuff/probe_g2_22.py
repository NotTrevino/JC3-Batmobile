"""G2-22 probe: independent of jc3usage.build() - raw counts over the caches."""
import collections
import glob
import json
import os
import re

RAW = r"E:/Modding/JustCause3/_grab"
files = sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json")))
print("cache files", len(files))
mods = 0
ea_per_entity = collections.Counter()
eeu_per_entity = collections.Counter()
ea_files = collections.Counter()
eeu_files = collections.Counter()
rows = 0
nested = 0
usage_names = collections.Counter()
usage_hashes = collections.Counter()
ent_with_ea = 0
for p in files:
    d = json.load(open(p, encoding="utf-8"))
    mods += len(d["modules"])
    n_ea = sum(1 for m in d["modules"] if m.get("type") == "EffectAttachments")
    n_eeu = sum(1 for m in d["modules"] if m.get("type") == "ExtendedEffectUsages")
    ea_per_entity[n_ea] += 1
    eeu_per_entity[n_eeu] += 1
    if n_ea:
        ent_with_ea += 1
    for m in d["modules"]:
        if m.get("type") == "EffectAttachments":
            ea_files[m.get("file")] += 1
            rs = m.get("rows") or []
            names = {}
            hashes = {}
            for r in rs:
                mm = re.fullmatch(r"usage_effects\[(\d+)\]\.usage\.(string|hash)", r["path"])
                if mm:
                    (names if mm.group(2) == "string" else hashes)[int(mm.group(1))] = r["value"]
                if re.fullmatch(r"effect_indices\[\d+\]", r["path"]):
                    nested += 1
            for i in sorted(set(names) | set(hashes)):
                rows += 1
                usage_names[str(names.get(i))] += 1
                usage_hashes[str(hashes.get(i))] += 1
        if m.get("type") == "ExtendedEffectUsages":
            eeu_files[m.get("file")] += 1
print("modules", mods)
print("EA per entity", dict(ea_per_entity), "entities with >=1 EA", ent_with_ea)
print("EEU per entity", dict(eeu_per_entity))
print("EA module files", dict(list(ea_files.items())))
print("EEU module files", dict(eeu_files))
print("usage rows", rows, "nested indices", nested)
print("distinct usage names", len(usage_names))
print("distinct usage hashes", len(usage_hashes))
for k, v in sorted(usage_names.items(), key=lambda kv: (-kv[1], kv[0])):
    print(f"  {k!r:34} x{v}")
