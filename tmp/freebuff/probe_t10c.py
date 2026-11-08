import glob, json, collections, re
files = sorted(glob.glob("E:/Modding/_JC3grab/detail/*.json"))
print("detail files:", len(files))
tok = ["upright","righting","selfright","self_right","stabil","aircontrol","air_control",
       "yaw","torque","shov","dodge","flip","constraint","gravity"]
hits = collections.defaultdict(lambda: collections.defaultdict(set))  # token -> name -> entities
donor = {}
for p in files:
    d = json.load(open(p, encoding="utf-8"))
    ent = d["entity"].split("/")[-1]
    isdonor = "v0300" in ent and "sportsmuscle" in ent
    names = set()
    for o in d["epe"]["objects"]:
        for k in (o.get("values") or {}):
            names.add(str(k))
        if o.get("name"): names.add(str(o["name"]))
    for n in names:
        low = n.lower()
        for t in tok:
            if t in low:
                hits[t][n].add(ent)
                if isdonor: donor[n] = True
for t in tok:
    tot = sum(len(v) for v in hits[t].values())
    print(f"\n== {t}: {len(hits[t])} distinct names, {tot} (name,entity) pairs")
    for n, ents in sorted(hits[t].items(), key=lambda kv: -len(kv[1]))[:6]:
        print(f"   {n:52s} entities={len(ents):3d} donor={'Y' if donor.get(n) else '-'}")
