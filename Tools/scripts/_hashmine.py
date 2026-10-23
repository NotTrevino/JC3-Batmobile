"""Hashlist mining: vehicle/battle/turbo/engine names -> hashes -> census cross-ref."""
import json, os, re

lines = open(r"E:\Modding\JC3-Batmobile\Research\Arkham Knight SFX\Arkham Knight SFX\batman_bnk\bnk\hashlist.txt",
             encoding="utf-8", errors="replace").read().splitlines()
print("lines:", len(lines))
pairs = []
for l in lines:
    parts = l.split("\t")
    if len(parts) >= 2:
        pairs.append((parts[0].strip().upper(), parts[1].strip()))
    elif parts:
        pairs.append(("", parts[0].strip()))
print("parsed:", len(pairs))
by_hash = {h: n for h, n in pairs if h}
census = {r["hash"]: r for r in json.load(open(r"E:\Modding\JC3-Batmobile\Working\Audio\sfx_census.json"))}

keys = ["batmobile", "bml_", "turbo", "battle", "engine", "exhaust", "afterburn", "boost",
        "turbine", "throttle", "veh_", "vehicle", "tank", "tyre", "tire", "skid", "drift",
        "rev", "idle", "rpm", "chase", "pursuit", " templ", "loop"]
hits = [(h, n) for h, n in pairs if any(k.strip("_") in n.lower() for k in keys)]
print("vehicle-ish hits:", len(hits))
for h, n in sorted(hits, key=lambda x: x[1]):
    c = census.get(h)
    loc = ("%s %dch %.0fs %dB" % (c["wad"], c["ch"], c["dur_s"], c["size"])) if c else "not-in-SFX-census"
    print("  %s %-42s %s" % (h, n, loc))
json.dump({"hashlist": pairs}, open(r"E:\Modding\JC3-Batmobile\Working\Audio\hashlist.json", "w"))
