#!/usr/bin/env python3
"""
vmodcdiff.py - locate and decode value changes between two JC3 .vmodc files.

`.vmodc` stat modules are ADF/RTPC-style property containers. Gibbed's
ConvertProperty does not handle them (it throws NotSupportedException), but the
files carry plaintext property paths plus fixed-width little-endian values, which
is enough to read *where* and *what* a mod author changed.

Why byte-level: in the shipped Batman mod every edited `.vmodc` has an IDENTICAL
byte size to its vanilla counterpart, so edits are in-place value writes. That
means a straight offset diff pinpoints each change exactly.

Two passes are used to name each edit:
  1. Find contiguous changed byte ranges.
  2. For each range, try to decode the containing aligned value as
     float / int32 / uint32 / uint16 / uint8 and report whichever parses cleanly,
     so a tuned float reads as a tunable number rather than raw bytes.

Usage:
    python vmodcdiff.py <vanilla.vmodc> <mod.vmodc> [--strings]
"""

from __future__ import annotations

import argparse
import re
import struct
import sys

PRINTABLE = re.compile(rb"[\x20-\x7e]{3,}")


def changed_ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    """Contiguous [start, end) byte ranges where a and b differ."""
    if len(a) != len(b):
        raise SystemExit(f"size mismatch: {len(a)} vs {len(b)} -- not an in-place edit")
    ranges: list[tuple[int, int]] = []
    start = None
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            if start is None:
                start = i
        elif start is not None:
            ranges.append((start, i))
            start = None
    if start is not None:
        ranges.append((start, len(a)))
    return ranges


def decode_at(buf: bytes, off: int, width: int):
    """Decode the value starting at off, preferring the most plausible reading."""
    if off + width > len(buf):
        return None, None
    chunk = buf[off:off + width]
    if width == 4:
        f = struct.unpack("<f", chunk)[0]
        if f == f and abs(f) < 1e30:
            i = struct.unpack("<i", chunk)[0]
            u = struct.unpack("<I", chunk)[0]
            return f"float32 {f!r}", i
    if width == 2:
        u = struct.unpack("<H", chunk)[0]
        return None, u
    if width == 1:
        return None, chunk[0]
    return None, None


def decode_pair(a: bytes, b: bytes, off: int, width: int) -> str:
    ca, cb = a[off:off + width], b[off:off + width]
    for w in (4, 2, 1):
        if off + w > len(a):
            continue
        fa, _ = decode_at(a, off, w)
        fb, _ = decode_at(b, off, w)
        if fa is not None and fb is not None:
            fa_v = float(fa.split(" ", 1)[1])
            fb_v = float(fb.split(" ", 1)[1])
            if fa_v == fb_v:
                continue
            ratio = ""
            if fb_v != 0 and abs(fa_v) > 1e-9:
                r = fb_v / fa_v
                ratio = f"   (x{r:.4g})" if 0.001 < abs(r) < 1000 else ""
            return f"{w * 8}-bit float {fa_v!r} -> {fb_v!r}{ratio}"
    if width == 4:
        ia, ib = struct.unpack("<i", ca)[0], struct.unpack("<i", cb)[0]
        return f"int32  {ia} -> {ib}"
    if width == 2:
        ua, ub = struct.unpack("<H", ca)[0], struct.unpack("<H", cb)[0]
        return f"uint16 {ua} -> {ub}"
    return f"bytes  {ca.hex()} -> {cb.hex()}"


def strings(buf: bytes) -> list[tuple[int, str]]:
    return [(m.start(), m.group().decode("ascii")) for m in PRINTABLE.finditer(buf)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vanilla")
    ap.add_argument("mod")
    ap.add_argument("--strings", action="store_true", help="dump plaintext property paths")
    args = ap.parse_args()

    a = open(args.vanilla, "rb").read()
    b = open(args.mod, "rb").read()

    print(f"A (vanilla): {args.vanilla}  ({len(a)} bytes)")
    print(f"B (mod):     {args.mod}  ({len(b)} bytes)")
    print()

    if a == b:
        print("IDENTICAL -- no differences")
        return 0

    if args.strings:
        sa, sb = strings(a), strings(b)
        only_b = [s for s in sb if s not in sa]
        only_a = [s for s in sa if s not in sb]
        print(f"## plaintext strings only in vanilla ({len(only_a)})")
        for off, s in only_a:
            print(f"  0x{off:06X} {s}")
        print(f"## plaintext strings only in mod ({len(only_b)})")
        for off, s in only_b:
            print(f"  0x{off:06X} {s}")
        print()

    ranges = changed_ranges(a, b)
    print(f"## {len(ranges)} changed byte range(s)")
    print()
    for start, end in ranges:
        width = end - start
        desc = decode_pair(a, b, start, width)
        print(f"  0x{start:06X}-0x{end:06X} ({width:>4} B)  {desc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())