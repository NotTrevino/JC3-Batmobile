"""jc3names.py - try to name the tab records no filelist or dictionary names.

The index (`jc3index.py`) names 81,862 of 81,953 entries.  The residue is
addressed only by Jenkins hash.  A name can still be recovered when the string
appears *somewhere* in the install - typically a dependency path stored inside
another asset.  This tool mines printable ASCII runs from a source, normalizes
them to forward slashes, and hashes them against the residue.

Sources:
  filelists   every Gibbed `*.filelist` path (sanity: resolves 0 by construction)
  game-text   every text-ish file under the install (*.ini, *.txt, *.fs, ...)
  archives    every `.arc`, streamed in chunks (the expensive one)
  entries     only the unnamed entries' own bytes (cheap, already negative)

Usage:
  python jc3names.py scan --source archives [--limit N] [--verbose]
  python jc3names.py residue
Read-only over the game; writes nothing except stdout.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3index as J  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
INDEX = os.path.join(ROOT, "Research", "JC3Grab")
# A path has no spaces (the game never ships one), starts with a word character
# and ends in a short extension.  Two variants: with directory separators and a
# bare file name.
PATH_RE = re.compile(rb"[A-Za-z0-9_][A-Za-z0-9_./\\-]{2,200}\.[A-Za-z0-9]{1,7}\Z")
NAME_RE = re.compile(rb"[A-Za-z0-9_][A-Za-z0-9_-]{1,120}\.[A-Za-z0-9]{1,7}\Z")
PRINT_RE = re.compile(rb"[\x20-\x7e]{4,256}")
CHUNK = 8 << 20


def load_residue() -> tuple[dict[str, set[int]], dict[str, dict[int, tuple[int, int]]], str]:
    d = json.load(open(os.path.join(INDEX, "INDEX.json"), encoding="utf-8"))
    game = d["game"]
    arcs = J.scan_archives(game)
    tabs = {a["key"]: J.read_tab(a["tab"]) for a in arcs}
    named: set[tuple[str, int]] = set()
    for line in open(os.path.join(INDEX, "INDEX.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        named.add((r["archive"], int(r["hash"], 16)))
    residue = {}
    for k, t in tabs.items():
        miss = set(t) - {h for (a, h) in named if a == k}
        if miss:
            residue[k] = miss
    return residue, tabs, game


def candidates(text: bytes):
    """Path-ish candidates inside one printable run."""
    for part in (text,):
        s = part.replace(b"\\", b"/")
        if PATH_RE.match(s) or NAME_RE.match(s):
            yield s
        # A run can carry a leading binary remnant; try each '/' and '\\' boundary.
        for i, ch in enumerate(s):
            if ch in (47, 92) and i + 2 < len(s):
                tail = s[i + 1:]
                if PATH_RE.match(tail) or NAME_RE.match(tail):
                    yield tail


def scan_blob(blob: bytes, targets: dict[int, set[str]], stats: dict, verbose: bool):
    for m in PRINT_RE.finditer(blob):
        stats["runs"] += 1
        for s in candidates(m.group()):
            stats["cand"] += 1
            h = J.hash_jenkins(s)
            if h in targets:
                targets[h].add(s.decode("ascii", "replace"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("residue")
    r.set_defaults(func=cmd_residue)
    s = sub.add_parser("scan")
    s.add_argument("--source", default="archives",
                   choices=("archives", "game-text", "filelists", "entries", "all"))
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--verbose", action="store_true")
    s.add_argument("--chunk", type=int, default=CHUNK)
    s.set_defaults(func=cmd_scan)
    a = ap.parse_args()
    sys.exit(a.func(a))


def cmd_residue(a) -> int:
    residue, tabs, game = load_residue()
    print(f"game {game}")
    total = 0
    for k, hs in residue.items():
        print(f"{k}: {len(hs)} unnamed")
        for h in sorted(hs):
            off, size = tabs[k][h]
            with open(os.path.join(game, k + ".arc"), "rb") as f:
                f.seek(off)
                head = f.read(16)
            print(f"  {h:08X} size={size:>9} magic={head[:4].hex()} first={head.hex()}")
            total += 1
    print("total", total)
    return 0


def cmd_scan(a) -> int:
    residue, tabs, game = load_residue()
    targets: dict[int, set[str]] = {h: set() for hs in residue.values() for h in hs}
    stats = {"runs": 0, "cand": 0, "bytes": 0}
    t0 = time.time()
    if a.source in ("filelists", "all"):
        for fl in J.find_filelists(os.path.join(ROOT, "Tools", "Gibbed")):
            blob = open(fl["path"], "rb").read()
            scan_blob(blob, targets, stats, a.verbose)
            print(f"filelist {os.path.basename(fl['path'])} bytes={len(blob)} "
                  f"resolved={sum(1 for v in targets.values() if v)}")
    if a.source in ("game-text", "all"):
        exts = (".ini", ".txt", ".cfg", ".xml", ".json", ".fs", ".lua", ".def", ".pdx")
        for dirpath, _dirs, files in os.walk(game):
            for fn in files:
                if not fn.lower().endswith(exts):
                    continue
                try:
                    blob = open(os.path.join(dirpath, fn), "rb").read()
                except OSError:
                    continue
                stats["bytes"] += len(blob)
                scan_blob(blob, targets, stats, a.verbose)
        print(f"game-text done bytes={stats['bytes']}")
    if a.source in ("entries", "all"):
        for k, hs in residue.items():
            p = os.path.join(game, k + ".arc")
            with open(p, "rb") as f:
                for h in sorted(hs):
                    off, size = tabs[k][h]
                    if size > 64 << 20:
                        continue
                    f.seek(off)
                    blob = f.read(size)
                    stats["bytes"] += len(blob)
                    scan_blob(blob, targets, stats, a.verbose)
        print(f"entries done bytes={stats['bytes']}")
    if a.source in ("archives", "all"):
        arcs = J.scan_archives(game)
        for i, arc in enumerate(arcs, 1):
            p = arc["arc"] if isinstance(arc, dict) and "arc" in arc else None
            if p is None:
                # scan_archives keys: inspect once
                print("arc keys", list(arc)[:10])
                return 1
            if a.limit and i > a.limit:
                break
            size = os.path.getsize(p)
            with open(p, "rb") as f:
                tail = b""
                while True:
                    chunk = f.read(a.chunk)
                    if not chunk:
                        break
                    stats["bytes"] += len(chunk)
                    scan_blob(tail + chunk, targets, stats, a.verbose)
                    tail = chunk[-300:]
            done = sum(1 for v in targets.values() if v)
            print(f"[{i}/{len(arcs)}] {arc['key']} {size/1e6:.0f} MB  resolved {done}/91  "
                  f"({time.time()-t0:.0f}s)", flush=True)
    names = {}
    for h, ss in targets.items():
        if ss:
            names[h] = sorted(ss)
    print(f"runs={stats['runs']:,} candidates={stats['cand']:,} bytes={stats['bytes']/1e9:.1f} GB "
          f"seconds={time.time()-t0:.0f}")
    print(f"resolved {len(names)} / {len(targets)}")
    for h in sorted(names)[:100]:
        print(f"  {h:08X} {names[h][:2]}")
    return 0


if __name__ == "__main__":
    main()
