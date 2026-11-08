"""Word-trigram overlap between a brief and every queued brief.

Why: the queue's similarity guard moves a brief out of `queue/` when its wording is too close to
another brief. A rewrite therefore has to be measured, not eyeballed.

Definition used here (stated so the number means one thing):
  token      = a run of [a-z0-9'] after lowercasing
  trigram    = three consecutive tokens
  overlap    = |A & B| / min(|A|, |B|)     (containment: how much of the smaller file is shared)
  jaccard    = |A & B| / |A | B|           (reported as a second, stricter view)

The pass condition is `max(overlap) < --max` and `max(jaccard) < --max`.

Usage:
  python Tools/scripts/trigram_overlap.py --rewrite Working/Queue/rewrites/8863-rewrite.txt \
      --queue tmp/freebuff/queue --max 0.30            # report + verdict, exit 1 on failure
  python Tools/scripts/trigram_overlap.py ... --write   # also write the JSON record
  python Tools/scripts/trigram_overlap.py ... --check   # recompute and compare with the record
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

TOKEN = re.compile(r"[a-z0-9']+")
DEFAULT_RECORD = os.path.join("Working", "Queue", "rewrites", "8863-rewrite-overlap.json")


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def trigrams(text: str) -> set[tuple[str, str, str]]:
    t = tokens(text)
    return {(t[i], t[i + 1], t[i + 2]) for i in range(len(t) - 2)}


def compare(a: set, b: set) -> tuple[float, float, int]:
    inter = len(a & b)
    if not inter:
        return 0.0, 0.0, 0
    contain = inter / min(len(a), len(b))
    jac = inter / len(a | b)
    return contain, jac, inter


def build(rewrite: str, queue_dir: str) -> dict:
    rw_text = open(rewrite, encoding="utf-8").read()
    rw = trigrams(rw_text)
    rows = []
    for name in sorted(os.listdir(queue_dir)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(queue_dir, name)
        other = trigrams(open(path, encoding="utf-8", errors="replace").read())
        contain, jac, inter = compare(rw, other)
        rows.append({"file": name, "containment": round(contain, 4),
                     "jaccard": round(jac, 4), "shared_trigrams": inter,
                     "file_trigrams": len(other)})
    rows.sort(key=lambda r: (-r["containment"], -r["jaccard"]))
    return {
        "rewrite": rewrite.replace(os.sep, "/"),
        "rewrite_trigrams": len(rw),
        "queue_dir": queue_dir.replace(os.sep, "/"),
        "queue_files": len(rows),
        "max_containment": rows[0]["containment"] if rows else 0.0,
        "max_containment_file": rows[0]["file"] if rows else None,
        "max_jaccard": max((r["jaccard"] for r in rows), default=0.0),
        "max_jaccard_file": max(rows, key=lambda r: r["jaccard"])["file"] if rows else None,
        "top": rows[:8],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rewrite", required=True)
    ap.add_argument("--queue", required=True)
    ap.add_argument("--max", type=float, default=0.30)
    ap.add_argument("--record", default=DEFAULT_RECORD)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    rec = build(a.rewrite, a.queue)
    rec["max_allowed"] = a.max
    ok = rec["max_containment"] < a.max and rec["max_jaccard"] < a.max

    print(f"rewrite            {rec['rewrite']}  ({rec['rewrite_trigrams']} trigrams)")
    print(f"compared against   {rec['queue_files']} files in {rec['queue_dir']}")
    for r in rec["top"]:
        print(f"  {r['containment']:.3f} contain / {r['jaccard']:.3f} jaccard / "
              f"{r['shared_trigrams']:4d} shared   {r['file']}")
    print(f"max containment    {rec['max_containment']:.4f}  ({rec['max_containment_file']})")
    print(f"max jaccard        {rec['max_jaccard']:.4f}  ({rec['max_jaccard_file']})")
    print(f"threshold          {a.max:.2f}")
    print(f"verdict            {'PASS' if ok else 'FAIL'}")

    if a.write:
        os.makedirs(os.path.dirname(a.record), exist_ok=True)
        with open(a.record, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
            fh.write("\n")
        print(f"record written     {a.record}")
    if a.check:
        if not os.path.exists(a.record):
            print(f"FAIL: no record at {a.record}; run --write first")
            return 2
        old = json.load(open(a.record, encoding="utf-8"))
        # The queue is live: briefs are added and removed while a session runs, so the file count is
        # recorded but not compared. The invariants that matter are the rewrite itself and the two
        # maxima, which a new high-overlap brief would move.
        same = all(old.get(k) == rec.get(k) for k in
                   ("rewrite_trigrams", "max_containment", "max_jaccard"))
        print(f"record match       {'yes' if same else 'no'}")
        if not same:
            return 1
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
