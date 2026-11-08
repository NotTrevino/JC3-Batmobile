"""Probe G2-22 (challenge): is a .epe `Usage` int the Jenkins hash of a decoded string?

Reads the already-converted .epe XMLs, collects (object class, every string value in
the object, Usage int), then tests jenkins(s) == Usage for each candidate string.
Never opens an archive; never touches D:/Games.
"""
import json
import os
import re
import sys
import collections

sys.path.insert(0, "Tools/scripts")
from rbmhdr import hash_jenkins  # noqa: E402

EPE = r"E:/Modding/_JC3grab/wiring/epe"


def parse(path):
    """Yield (class_name, [string values in this object], usage_int_or_None)."""
    stack = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s.startswith("<object"):
                m = re.match(r'<object name="([^"]*)">', s)
                stack.append({"name": m.group(1) if m else "", "class": "", "strings": [], "usage": None})
            elif s.startswith("</object>"):
                if stack:
                    o = stack.pop()
                    yield o
            elif s.startswith("<value ") and stack:
                m = re.match(r'<value name="([^"]*)" type="([^"]*)"(?:/>|>(.*)</value>)', s)
                if not m:
                    continue
                name, typ, txt = m.group(1), m.group(2), m.group(3) or ""
                o = stack[-1]
                if name == "_class":
                    o["class"] = txt
                elif name == "Usage":
                    try:
                        o["usage"] = int(txt) & 0xFFFFFFFF
                    except ValueError:
                        pass
                if typ == "string" and txt and len(txt) < 120:
                    o["strings"].append(txt)


def main():
    usage_objs = collections.defaultdict(list)   # usage -> [(class, strings)]
    per_value = collections.Counter()
    nfiles = 0
    for fn in sorted(os.listdir(EPE)):
        if not fn.endswith(".xml"):
            continue
        nfiles += 1
        for o in parse(os.path.join(EPE, fn)):
            if o["usage"] is None:
                continue
            per_value[o["usage"]] += 1
            usage_objs[o["usage"]].append((o["class"], o["name"], o["strings"]))

    print(f"files={nfiles} objects with Usage={sum(per_value.values())} distinct={len(per_value)}")

    # candidate strings -> hash map
    cand = {}  # hash -> [strings]
    for u, rows in usage_objs.items():
        for cls, oname, strs in rows:
            for s in [oname, cls] + strs:
                if not s:
                    continue
                cand.setdefault(hash_jenkins(s.encode()), []).append(s)

    named, unnamed = {}, []
    for u in per_value:
        if u in cand:
            named[u] = collections.Counter(cand[u]).most_common(3)
        else:
            unnamed.append(u)
    print(f"Usage ints that ARE jenkins(some string in the same object): {len(named)}/{len(per_value)}")
    print(f"still unnamed: {len(unnamed)}")
    for u in sorted(named)[:20]:
        print(f"  {u:>10} n={per_value[u]:>4} <- {named[u]}")
    json.dump({"named": {str(k): v for k, v in named.items()},
               "unnamed": unnamed,
               "counts": {str(k): v for k, v in per_value.items()}},
              open("tmp/freebuff/probe_g2_22c.json", "w"), indent=1)


if __name__ == "__main__":
    main()
