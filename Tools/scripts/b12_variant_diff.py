#!/usr/bin/env python3
"""b12_variant_diff.py - B-12's gate: the two variant trees may differ in exactly the declared files.

The card's Do-line says `aafdiff` between the variants lists **only** the files the variant table
names. This script holds the build to that: it diffs the `pursuit` and `battle` unpacked trees by
SHA-256 (so a same-size value change cannot hide), reads the declaration the battle build wrote to
`<build>/variant.json`, and fails on any changed / added / removed file that is not in
`planned_files`.

It also runs `aafdiff.py --hash` itself and writes that report, so the evidence and the assertion
come from one invocation.

Usage:
    python Tools/scripts/b12_variant_diff.py \
        --pursuit Builds/bm-RC4-modes/pursuit/aaf \
        --battle  Builds/bm-RC4-modes/battle/aaf \
        --out tmp/freebuff/reports/aafdiff-pursuit-battle.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from aafdiff import index, sha256  # noqa: E402


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def digests(root: str) -> dict[str, str]:
    out = {}
    for n in index(root):
        out[n] = sha256(os.path.join(root, n))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pursuit", required=True, help="pursuit variant's unpacked aaf tree")
    ap.add_argument("--battle", required=True, help="battle variant's unpacked aaf tree")
    ap.add_argument("--declared", help="variant.json to read planned_files from "
                                       "(default: <battle>/../variant.json)")
    ap.add_argument("--out", help="write aafdiff's markdown report here")
    a = ap.parse_args()

    declared_path = a.declared or os.path.join(os.path.dirname(os.path.abspath(a.battle)),
                                               "variant.json")
    doc = json.load(open(declared_path, encoding="utf-8"))
    planned = list(doc.get("planned_files") or [])

    pa, pb = digests(a.pursuit), digests(a.battle)
    only_p = sorted(set(pa) - set(pb))
    only_b = sorted(set(pb) - set(pa))
    changed = sorted(n for n in set(pa) & set(pb) if pa[n] != pb[n])
    observed = sorted(set(changed) | set(only_p) | set(only_b))
    extra = [n for n in observed if n not in planned]
    missing = [n for n in planned if n not in observed]

    print(f"pursuit {rel(a.pursuit)}: {len(pa)} files")
    print(f"battle  {rel(a.battle)}: {len(pb)} files")
    print(f"declared {rel(declared_path)}: {len(planned)} planned file(s), "
          f"variant {doc.get('name')!r}")
    print(f"observed: {len(changed)} changed, {len(only_p)} only pursuit, {len(only_b)} only battle")
    for n in planned:
        state = ("changed" if n in changed else
                 "only in battle" if n in only_b else
                 "only in pursuit" if n in only_p else "IDENTICAL - declared but unchanged")
        print(f"  {state:<34} {n}")
    for n in extra:
        print(f"  UNDECLARED {n}")

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, "aafdiff.py"),
                            a.pursuit, a.battle, "--hash", "--out", a.out],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-800:] + r.stderr[-800:], file=sys.stderr)
            print("FAIL: aafdiff.py did not run", file=sys.stderr)
            return 2
        print(f"wrote {rel(os.path.abspath(a.out))}")

    ok = not extra and not missing
    print(("PASS: the diff is exactly the declared file set"
           if ok else
           f"FAIL: {len(extra)} undeclared, {len(missing)} declared-but-unchanged"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
