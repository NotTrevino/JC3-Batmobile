"""G2-34 probe: what the index and the decoded entities say about tether / airlift / winch."""
import collections
import glob
import json
import os

RAW = r"E:/Modding/_JC3grab"
OUT = r"Research/JC3Grab"
PAT = ("tether", "grapple", "grapp", "rope", "winch", "airlift", "cargo_rope", "hook")

hits = collections.defaultdict(list)
tot = 0
for line in open(os.path.join(OUT, "INDEX.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    p = r["path"]
    tot += 1
    low = p.lower()
    if any(k in low for k in PAT):
        hits[p.rsplit("/", 1)[0]].append(p)
print("index rows", tot, "dirs with a hit", len(hits), "files", sum(len(v) for v in hits.values()))
for d, v in sorted(hits.items(), key=lambda kv: -len(kv[1]))[:25]:
    print(f"  {len(v):4}  {d}")
print()
for d, v in sorted(hits.items(), key=lambda kv: -len(kv[1]))[:8]:
    print(d)
    for p in v[:8]:
        print("    ", p.rsplit("/", 1)[-1])
