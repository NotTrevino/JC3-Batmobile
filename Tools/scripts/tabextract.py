"""tabextract.py - slice one file out of a JC3 archives/patch .arc via its .tab.

The .tab is a flat index: magic 'TAB\\0', u16 2, u16 1, u32 alignment 0x800,
then (name_hash u32, offset u32, size u32) records. name_hash is Gibbed's
Jenkins lookup3 over the ASCII VFS path with FORWARD slashes
(Gibbed.JustCause3.FileFormats.StringHelpers + ProjectHelpers).
.arc entries are stored raw: seek to offset, copy size bytes, no per-entry
decompression (Gibbed.JustCause3.Unpack reads them verbatim).

Verified: game12.tab hash 435781BB -> w501_turret_sam_v2.ee @161933312+3542656;
patch game1.tab 6BCDDDF3 -> w501_turret_sam_v2.epe @441401344+115460.

Usage:
  python tabextract.py <file.tab> <vfs/path/like.this> -o <out>
  python tabextract.py <file.tab> --hash 435781BB -o <out>
Read-only w.r.t. inputs; writes only the requested -o file.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rbmhdr import hash_jenkins  # noqa: E402


def read_tab(path: str) -> dict[int, tuple[int, int]]:
    with open(path, "rb") as f:
        blob = f.read()
    if blob[0:4] != b"TAB\0":
        raise SystemExit("not a TAB file")
    v1, v2 = struct.unpack_from("<HH", blob, 4)
    (align,) = struct.unpack_from("<I", blob, 8)
    if (v1, v2, align) != (2, 1, 0x800):
        raise SystemExit(f"unexpected TAB header {(v1, v2, align)}")
    entries = {}
    o = 12
    while o + 12 <= len(blob):
        nh, off, size = struct.unpack_from("<III", blob, o)
        entries[nh] = (off, size)
        o += 12
    return entries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tab", help="input .tab index file")
    ap.add_argument("path", nargs="?", help="VFS path (back- or forward slashes)")
    ap.add_argument("--hash", help="archive name hash hex, e.g. 435781BB")
    ap.add_argument("-o", required=True, help="output file")
    a = ap.parse_args()
    entries = read_tab(a.tab)
    if a.hash:
        h = int(a.hash, 16)
    elif a.path:
        h = hash_jenkins(a.path.replace("\\", "/").encode("ascii"))
    else:
        raise SystemExit("need VFS path or --hash")
    if h not in entries:
        raise SystemExit(f"hash {h:08X} not in {a.tab} ({len(entries)} entries)")
    off, size = entries[h]
    arc = os.path.splitext(a.tab)[0] + ".arc"
    with open(arc, "rb") as f:
        f.seek(off)
        data = f.read(size)
    if len(data) != size:
        raise SystemExit(f"short read {len(data)} != {size}")
    with open(a.o, "wb") as f:
        f.write(data)
    print(f"hash {h:08X} off={off} size={size} -> {a.o} magic={data[:4]!r}")


if __name__ == "__main__":
    main()
