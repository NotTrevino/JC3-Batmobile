"""Scratch: scan named entries by extension for strings that hash to the unnamed residue."""
from __future__ import annotations

import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3index as J  # noqa: E402

INDEX = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Research", "JC3Grab")
PRINT_RE = re.compile(rb"[\x20-\x7e]{4,256}")
PATH_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\\-]{2,200}\.[A-Za-z0-9]{1,7}\Z")


def main() -> None:
    exts = {e.lower() for e in sys.argv[1].split(",")} if len(sys.argv) > 1 else {".rbm"}
    d = json.load(open(os.path.join(INDEX, "INDEX.json"), encoding="utf-8"))
    game = d["game"]
    arcs = J.scan_archives(game)
    bykey = {a["key"]: a for a in arcs}
    tabs = {a["key"]: J.read_tab(a["tab"]) for a in arcs}
    named = set()
    rows = []
    for line in open(os.path.join(INDEX, "INDEX.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        named.add((r["archive"], int(r["hash"], 16)))
        if os.path.splitext(r["path"])[1].lower() in exts:
            rows.append(r)
    residue = {}
    for k, t in tabs.items():
        miss = set(t) - {h for (a, h) in named if a == k}
        if miss:
            residue[k] = miss
    targets = {h: set() for hs in residue.values() for h in hs}
    print(f"extensions {sorted(exts)}: {len(rows)} entries, {sum(r['size'] for r in rows)/1e6:.0f} MB, "
          f"residue {len(targets)}")
    t0 = time.time()
    seen_bytes = 0
    handles = {}
    for i, r in enumerate(rows, 1):
        a = bykey[r["archive"]]
        f = handles.get(r["archive"])
        if f is None:
            f = handles[r["archive"]] = open(a["arc"], "rb")
        f.seek(r["offset"])
        blob = f.read(r["size"])
        seen_bytes += len(blob)
        for m in PRINT_RE.finditer(blob):
            s = m.group().replace(b"\\", b"/")
            for cand in (s,) + tuple(s[j + 1:] for j, c in enumerate(s) if c in (47, 92) and j + 2 < len(s)):
                text = cand.decode("ascii", "replace")
                if not (PATH_RE.match(text) or re.match(r"[A-Za-z0-9_][A-Za-z0-9_-]{1,120}\.[A-Za-z0-9]{1,7}\Z", text)):
                    continue
                h = J.hash_jenkins(text.encode("ascii", "replace"))
                if h in targets:
                    targets[h].add(text)
        if i % 400 == 0:
            hit = sum(1 for v in targets.values() if v)
            print(f"  [{i}/{len(rows)}] {seen_bytes/1e6:.0f} MB, {time.time()-t0:.0f}s, hits {hit}",
                  flush=True)
    for f in handles.values():
        f.close()
    hits = {h: sorted(v) for h, v in targets.items() if v}
    print(f"resolved {len(hits)} / {len(targets)} in {time.time()-t0:.0f}s")
    for h, v in sorted(hits.items()):
        print(f"  {h:08X} {v[:3]}")


if __name__ == "__main__":
    main()
