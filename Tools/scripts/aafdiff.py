#!/usr/bin/env python3
"""
aafdiff.py - compare two unpacked JC3 AAF (.ee) trees and report exactly what differs.

The `.ee` is an AAF/SARC archive. `Gibbed.JustCause3.SmallUnpack.exe` expands one
into a directory tree, which is what this script diffs. It answers the question the
Batman mod comparison exists to answer: did the mod author touch geometry, or only
the entity brain, physics and textures?

Usage:
    python aafdiff.py <vanilla_dir> <mod_dir> [--out report.md] [--hash]

Outputs: added / removed / changed files with byte deltas, plus per-extension
rollups and an unchanged-content check via SHA-256 when --hash is passed.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections import Counter


def index(root: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for dirpath, _dirs, names in os.walk(root):
        for n in names:
            full = os.path.join(dirpath, n)
            out[os.path.relpath(full, root).replace("\\", "/")] = os.path.getsize(full)
    return out


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(root: str, rel: str, want_hash: bool, size_cache: dict) -> str:
    key = (root, rel)
    if key in size_cache:
        return size_cache[key]
    if want_hash:
        v = f"{os.path.getsize(os.path.join(root, rel))}:{sha256(os.path.join(root, rel))[:16]}"
    else:
        v = str(os.path.getsize(os.path.join(root, rel)))
    size_cache[key] = v
    return v


def ext(rel: str) -> str:
    return rel.rsplit(".", 1)[-1].lower() if "." in rel else "(none)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vanilla")
    ap.add_argument("mod")
    ap.add_argument("--out", help="write a markdown report here")
    ap.add_argument("--hash", action="store_true",
                    help="compare by SHA-256, not just size (slower but exact)")
    args = ap.parse_args()

    a, b = args.vanilla, args.mod
    ia, ib = index(a), index(b)
    only_a = sorted(set(ia) - set(ib))
    only_b = sorted(set(ib) - set(ia))
    common = sorted(set(ia) & set(ib))

    cache: dict = {}
    same_size, diff_size = [], []
    same_content, changed_content = [], []
    for rel in common:
        if ia[rel] != ib[rel]:
            diff_size.append(rel)
        else:
            same_size.append(rel)
        if digest(a, rel, args.hash, cache) == digest(b, rel, args.hash, cache):
            same_content.append(rel)
        else:
            changed_content.append(rel)

    L: list[str] = []
    def p(s: str = "") -> None:
        L.append(s)

    p("# AAF diff")
    p()
    p(f"- A (vanilla): `{a}` — {len(ia)} files")
    p(f"- B (mod): `{b}` — {len(ib)} files")
    p(f"- comparison: {'SHA-256' if args.hash else 'size only (pass --hash for exact)'}")
    p()
    p("## Summary")
    p()
    p("| Bucket | Count |")
    p("|---|---:|")
    p(f"| Files only in vanilla | {len(only_a)} |")
    p(f"| Files only in mod | {len(only_b)} |")
    p(f"| Common, identical content | {len(same_content)} |")
    p(f"| Common, **different content** | {len(changed_content)} |")
    p(f"| ...of which size differs | {len(diff_size)} |")
    p()

    def rollup(title: str, files: list[str]) -> None:
        if not files:
            p(f"## {title}: none")
            p()
            return
        p(f"## {title} ({len(files)})")
        p()
        c = Counter(ext(f) for f in files)
        p("by extension: " + ", ".join(f"`.{k}` x{v}" for k, v in c.most_common()))
        p()
        p("| Bytes A | Bytes B | Delta | Path |")
        p("|---:|---:|---:|---|")
        for rel in files:
            sa = ia.get(rel)
            sb = ib.get(rel)
            d = (sb - sa) if (sa is not None and sb is not None) else None
            ds = f"{d:+d}" if d is not None else ("—" if sa is None else f"(gone, {sa})")
            p(f"| {sa if sa is not None else '—'} | {sb if sb is not None else '—'} | {ds} | `{rel}` |")
        p()

    rollup("Files only in vanilla", only_a)
    rollup("Files only in mod", only_b)
    rollup("Common files with different content", changed_content)

    text = "\n".join(L)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.out}")
    else:
        print(text)

    print(f"\nidentical={len(same_content)} changed={len(changed_content)} "
          f"onlyA={len(only_a)} onlyB={len(only_b)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())