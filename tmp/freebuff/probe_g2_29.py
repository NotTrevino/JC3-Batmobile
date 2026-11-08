"""Independent re-derivation for G2-29 (does not import jc3traffic). Raw byte checks."""
import json
import os
import re
import sys

sys.path.insert(0, "Tools/scripts")
import jc3grab  # noqa: E402

D = "v0300_car_kensington_sportsmuscle_civilian_01"
rows = [json.loads(l) for l in open("Research/JC3Grab/INDEX.jsonl", encoding="utf-8")]


def get(p):
    return jc3grab.read_entry(jc3grab.resolve(p, rows), jc3grab.DEFAULT_GAME)


out = {}
spawn = get("settings/spawn_vehicle_defs.bin")
out["spawn_bytes"] = len(spawn)
out["ee_path_count"] = len(re.findall(rb"\.ee\x00", spawn))
out["donor_name_count"] = spawn.count(D.encode())
out["donor_path_count"] = spawn.count(D.encode() + b".ee")
# the donor's own record: take 200 bytes after the path and look for the tag list + name
i = spawn.index(D.encode() + b".ee")
tail = spawn[i:i + 260]
out["record_tail"] = re.sub(rb"[^\x20-\x7e]", b"|", tail).decode()
out["tags_contain"] = {
    t: t.encode() in tail.decode("latin-1").encode() for t in
    ("ambient", "liberated", "highend", "car", "ground")
}

blo = get("global/global.blo")
out["traffic_rule_strings"] = sorted({m.decode() for m in re.findall(rb"[A-Za-z0-9_]*(?:TrafficRule)\d*", blo)})
out["numbered_rule_strings"] = sorted({m.decode() for m in re.findall(rb"\d\d[b]?_[A-Z][A-Za-z0-9]+", blo)})
out["selector_present"] = b"ambient,ground,car,liberated,-highend" in blo
out["driver_seats"] = blo.count(b"Driver")
out["bts_paths"] = sorted({m.decode() for m in re.findall(rb"ai/bts/[\w/]+\.bts", blo)})

item = get("profile/item.onlinec")
task = get("profile/task.onlinec")
out["item_keys"] = sorted({m.group().decode() for m in re.finditer(
    rb"v0300_car_kensington_sportsmuscle_civilian_01[\w]*", item)})
out["task_keys"] = sorted({m.group().decode() for m in re.finditer(
    rb"[\w]*v0300_car_kensington_sportsmuscle_civilian_01[\w]*", task)})

# independent census of the 17 files: hard-coded extension list from the tool, re-scanned here
EXT = {".bin", ".onlinec", ".gsc", ".gdc", ".btc", ".entityregc", ".stringlookup", ".epe", ".toc",
       ".vmodc", ".physicsc", ".gadfc", ".mdic", ".wtunec", ".ctunec", ".effc", ".pfxc", ".trim",
       ".lua", ".defc", ".pfs", ".revolutionc", ".destc", ".bl", ".blo", ".ee"}
hits = []
for r in rows:
    if os.path.splitext(r["path"])[1].lower() not in EXT:
        continue
    data = jc3grab.read_entry(r, jc3grab.DEFAULT_GAME)
    if D.encode() in data:
        hits.append(r["path"] + "@" + r["mount"])
out["name_hit_files"] = len(hits)
out["name_hits"] = hits
out["bl_hits"] = [h for h in hits if h.endswith(".bl@patch") or h.endswith(".bl@base")]
print(json.dumps(out, indent=1, sort_keys=True))
