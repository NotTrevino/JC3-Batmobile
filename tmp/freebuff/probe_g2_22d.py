"""Probe G2-22 (challenge): how many of the 'UNKNOWN' Usage names are recoverable by
Jenkins-hashing every string value that the same 232 graphs already decode?

If Usage == jenkins(name) holds (see probe_g2_22b), then the 'no name in any decoded
file' claim is a claim about *adjacent* strings only. This probe hashes every
type="string" value in the 232 vehicle graphs plus a few other decoded string tables.
No archive is opened; D:/Games is untouched.
"""
import json
import os
import re
import sys
import collections

sys.path.insert(0, "Tools/scripts")
from rbmhdr import hash_jenkins  # noqa: E402

EPE = r"E:/Modding/_JC3grab/wiring/epe"


def strings_in(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            if "<value " in line and 'type="string"' in line:
                m = re.search(r'type="string"\s*(?:/>|>([^<]*)</value>)', line)
                if m and m.group(1):
                    yield m.group(1)


def main():
    d = json.load(open("Research/JC3Grab/USAGES.json", encoding="utf-8"))
    vals = d["epe"]["values"]
    slugs = set()
    for v in vals:
        for e in v["vehicles"]:
            slugs.add(e.rsplit("/", 1)[-1])
    files = [f for f in os.listdir(EPE) if f.endswith(".xml") and f[:-4].rsplit(".ee", 1)[0] in slugs]
    print(f"graphs matched for {len(slugs)} vehicles: {len(files)}")

    seen = collections.Counter()          # string -> count
    for fn in files:
        for s in strings_in(os.path.join(EPE, fn)):
            seen[s] += 1
    print(f"distinct string values in those graphs: {len(seen)} (doc says 849,942 values)")

    h2s = collections.defaultdict(list)
    for s in seen:
        if len(s) < 160:
            h2s[hash_jenkins(s.encode())].append(s)

    named = sum(1 for v in vals if v["name_source"] != "UNKNOWN")
    resolved = []
    for v in vals:
        u = v["usage"] & 0xFFFFFFFF
        if v["name_source"] != "UNKNOWN":
            continue
        if u in h2s:
            resolved.append((u, collections.Counter(h2s[u]).most_common(3)))
    print(f"doc-named: {named}/{len(vals)}; of the {len(vals)-named} UNKNOWN, "
          f"hash resolves {len(resolved)} from graph strings alone")
    for u, s in resolved:
        print(f"  {u:>10} <- {s}")
    json.dump({"resolved": resolved}, open("tmp/freebuff/probe_g2_22d.json", "w"), indent=1)


if __name__ == "__main__":
    main()
