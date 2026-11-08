"""G2-33 probe: light module vocabulary, preset ids, part binding, CarLight census."""
import collections
import glob
import json
import os

RAW = r"E:/Modding/JustCause3/_grab"
OUT = r"Research/JC3Grab"

ent_files = sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json")))
members = collections.Counter()
types = {}
behaviors = collections.Counter()
presets = collections.Counter()
preset0 = []
entries_total = 0
per_entity = {}
entities_with_lights = 0
values = collections.defaultdict(collections.Counter)
for p in ent_files:
    d = json.load(open(p, encoding="utf-8"))
    ent = d["entity"]
    mods = [m for m in d["modules"] if m.get("type") == "VehicleDynamicLights"]
    if not mods:
        continue
    entities_with_lights += 1
    import re
    rows = []
    for m in mods:
        rows += m["rows"]
    cur = {}
    entries = []
    for r in rows:
        mm = re.fullmatch(r"lights\[(\d+)\]\.(.+)", r["path"])
        if not mm:
            continue
        i, name = int(mm.group(1)), mm.group(2)
        types[name] = r["type"]
        members[name] += 1
        cur.setdefault(i, {})[name] = r["value"]
    entries = [cur[i] for i in sorted(cur)]
    entries_total += len(entries)
    per_entity[ent] = len(entries)
    for e in entries:
        behaviors[str(e.get("behavior"))] += 1
        pid = e.get("preset_id")
        presets[pid] += 1
        if pid in (0, None):
            preset0.append((ent, e.get("behavior"), e.get("part")))
        for k in ("range", "angle", "multiplier", "light_type", "blinking",
                  "volumetric_mode", "cast_shadows", "near_cap"):
            if k in e:
                values[k][str(e[k])] += 1

print("entities with VehicleDynamicLights", entities_with_lights, "of", len(ent_files))
print("light entries", entries_total, "per entity min/med/max",
      min(per_entity.values()), sorted(per_entity.values())[len(per_entity)//2],
      max(per_entity.values()))
print("members", len(members))
for k, v in sorted(members.items(), key=lambda kv: -kv[1]):
    print(f"  {k:28} {types[k]:8} x{v}")
print("behaviors", dict(behaviors))
print("preset ids", len(presets), "zero/none:", len(preset0), preset0[:5])
for k, v in sorted(presets.items(), key=lambda kv: -kv[1])[:30]:
    print("  preset", k, "x", v)
for k, c in values.items():
    print("values", k, dict(c.most_common(8)))

# part binding
parts = {}
for line in open(os.path.join(OUT, "PARTS_TABLE.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    parts[r["entity"]] = {p["i"]: p for p in r["parts"]}
miss_name = miss_flag = 0
ex = []
ref = collections.Counter()
for p in ent_files:
    d = json.load(open(p, encoding="utf-8"))
    ent = d["entity"]
    mods = [m for m in d["modules"] if m.get("type") == "VehicleDynamicLights"]
    if not mods or ent not in parts:
        continue
    cur = {}
    import re
    for m in mods:
        for r in m["rows"]:
            mm = re.fullmatch(r"lights\[(\d+)\]\.(.+)", r["path"])
            if mm:
                cur.setdefault(int(mm.group(1)), {})[mm.group(2)] = r["value"]
    for e in cur.values():
        idx = e.get("part_index")
        part = parts[ent].get(idx)
        ref[idx] += 1
        if part is None:
            miss_name += 1
            ex.append((ent, idx))
        elif part["n"] != e.get("part"):
            miss_name += 1
            ex.append((ent, idx, part["n"], e.get("part")))
        elif part.get("lights") != 1:
            miss_flag += 1
            ex.append((ent, idx, part["n"], "lights=0"))
print("light entries whose part_index does not resolve to the named part:", miss_name)
print("light entries on a part with has_lights=0:", miss_flag)
print("examples", ex[:6])
lit = sum(1 for e in parts.values() for p in e.values() if p.get("lights") == 1)
li = sum(1 for e in parts.values() for p in e.values() if p.get("lights") == 1
         and p.get("dt") == "Land_Light")
print("parts with lights=1 fleet-wide", lit, "of which Land_Light", li,
      "total parts", sum(len(e) for e in parts.values()))

# CarLight census
blocks = 0
stride = collections.Counter()
iw = collections.Counter()
slots = []
meshes = set()
ents = set()
for line in open(os.path.join(OUT, "GEOMETRY.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    for b in r.get("blocks") or []:
        if b.get("type") != "CarLight":
            continue
        blocks += 1
        stride[b.get("vertex_stride")] += 1
        iw[b.get("payload", {}).get("index_width")] += 1
        slots.append(b.get("material_slots") or 0)
        meshes.add((r["entity"], r["path"]))
        ents.add(r["entity"])
print("CarLight blocks", blocks, "meshes", len(meshes), "entities", len(ents))
print("stride", dict(stride), "index width", dict(iw),
      "material slots min/max", (min(slots), max(slots)))

# index paths with 'light' outside jc_vehicles
hits = collections.Counter()
for line in open(os.path.join(OUT, "INDEX.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    p = r.get("path", "")
    if "light" in p.lower() and "/jc_vehicles/" not in p:
        hits[p.rsplit("/", 1)[0]] += 1
print("index light paths outside jc_vehicles:", len(hits))
for k, v in hits.most_common(12):
    print("  ", k, v)
