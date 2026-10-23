"""Scratch: hash every path-like string already captured in Research/JC3Grab against the residue."""
from __future__ import annotations

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3index as J  # noqa: E402

INDEX = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Research", "JC3Grab")
PATH_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\\-]{3,200}\.[A-Za-z0-9]{1,7}")


def main() -> None:
    d = json.load(open(os.path.join(INDEX, "INDEX.json"), encoding="utf-8"))
    game = d["game"]
    arcs = J.scan_archives(game)
    tabs = {a["key"]: J.read_tab(a["tab"]) for a in arcs}
    named = set()
    for line in open(os.path.join(INDEX, "INDEX.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        named.add((r["archive"], int(r["hash"], 16)))
    residue = {h for k, t in tabs.items() for h in set(t) - {h for (a, h) in named if a == k}}
    print("residue", len(residue))

    cands = set()
    for p in glob.glob(os.path.join(INDEX, "*.json")) + glob.glob(os.path.join(INDEX, "*.jsonl")):
        txt = open(p, encoding="utf-8", errors="replace").read()
        for m in PATH_RE.finditer(txt):
            cands.add(m.group().replace("\\", "/"))
    print("candidate strings", len(cands))

    by_hash = {}
    for c in cands:
        by_hash.setdefault(J.hash_jenkins(c.encode("ascii", "replace")), set()).add(c)
    found = {h: sorted(by_hash[h]) for h in residue if h in by_hash}
    print("resolved", len(found))
    for h, v in sorted(found.items()):
        print(f"  {h:08X} {v[:3]}")


if __name__ == "__main__":
    main()
