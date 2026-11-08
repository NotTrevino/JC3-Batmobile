import glob, json, collections, re
ENT = "E:/Modding/JustCause3/_grab/entities"
paths = sorted(glob.glob(ENT + "/*.ee.json"))
norm = collections.defaultdict(set)     # normalised path -> entities
where = {}                              # norm path -> (module type, example)
vals = collections.defaultdict(list)    # norm path -> [values]
donor = {}
for p in paths:
    doc = json.load(open(p, encoding="utf-8"))
    isdonor = "v0300" in doc["entity"] and "sportsmuscle" in doc["entity"]
    for mod in doc["modules"]:
        t = mod.get("type")
        for r in (mod.get("rows") or []):
            k = re.sub(r"\[\d+\]", "[]", r["path"])
            norm[k].add(doc["entity"])
            where.setdefault(k, (t, doc["entity"], r["path"]))
            vals[k].append((doc["entity"].split("/")[-1], r["value"]))
            if isdonor:
                donor[k] = r["value"]
print("normalised paths:", len(norm), "types:", len({v[0] for v in where.values() if v[0]}))
def show(tok):
    print("\n==", tok)
    for k in sorted(norm):
        if tok in k.lower():
            t, e, raw = where[k]
            vs = sorted({v for _, v in vals[k]}, key=str)
            print(f"  {k:44s} {str(t):20s} n={len(norm[k]):3d} donor={donor.get(k)!r} vals={vs[:6]}")
for tok in ["crashing_impulse", "impact_deform_threshold", "impact_damage_factor", "impact_armor",
            "takeoff_pitch_damping", "gravity_multiplier", "righting_torque", "air_steering",
            "deform_scale", "collision_damage", "ram_"]:
    show(tok)
