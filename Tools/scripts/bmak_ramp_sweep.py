"""bmak_ramp_sweep.py - where every colour-ramp name lives, across every cooked package.

Rule D10 ("the ramp files are missing on disk") is a claim about the whole install.
This tool tests it by opening the name table of *every* .upk in CookedPCConsole and
recording which packages mention a ramp-ish name, and which of those names are local
Texture2D exports rather than imports.

Speed: a package's name table sits at the front of the container, so the scan
decompresses chunk by chunk only until the name table parses - not the whole package.
`validate()` checks that shortcut against `upk_read.Package` on a sample, and the scan
refuses to report if they disagree.

Usage:
    python Tools/scripts/bmak_ramp_sweep.py            # scan, print, write JSON
    python Tools/scripts/bmak_ramp_sweep.py --check    # re-scan, compare to the JSON
"""
from __future__ import annotations

import argparse
import glob
import json
import multiprocessing as mp
import os
import random
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read  # noqa: E402
from _lzo1x import lzo1x_decompress  # noqa: E402

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT = os.path.join(ROOT, "Working", "Ramp", "ramp_scan.json")
PAT = re.compile(r"(ramp|lacquered|colourlut|colorlut)", re.I)
EXACT = ("Batman_BM3_V2_Lacquered_Underlayer_Ramp",
         "Batman_BM3_V2_Leather_Ramp",
         "Batmobile_V3_Body_ColourRamp",
         "Batmobile_V3_Tyre_ColourRamp",
         "Engine.Aniso_ramp_Lacquered")
READ_STEPS = (256 << 10, 1 << 20, 4 << 20)


def _fstr(buf, o):
    n = struct.unpack_from("<i", buf, o)[0]
    o += 4
    if n == 0:
        return "", o
    if n > 0:
        return buf[o:o + n].rstrip(b"\0").decode("latin-1"), o + n
    m = -n
    return buf[o:o + 2 * m].decode("utf-16-le").rstrip("\0"), o + 2 * m


def _names(buf, nc, no):
    o, out = no, []
    for _ in range(nc):
        s, o = _fstr(buf, o)
        out.append(s)
        o += 8                                  # uint64 name flags
    return out


class _Short(Exception):
    """The bytes read so far do not reach the end of the name table."""


def _parse(raw):
    if raw[:4] != upk_read.PKG_TAG:
        raise upk_read.UpkError("no package tag")
    _grp, o = _fstr(raw, 12)
    o += 4
    nc, no, ec, eo, ic, io = struct.unpack_from("<6i", raw, o)
    if no + 4 <= len(raw):
        try:
            got = _names(raw, nc, no)
            if got and got[0] in ("None", "") and no + _span(raw, no, nc) == io:
                return got
        except Exception:  # noqa: BLE001 - compressed body, fall through
            pass
    start = raw.find(upk_read.PKG_TAG, no)
    if start < 0:
        raise _Short("name table not in these bytes")
    out = bytearray()
    q = start
    while q + 16 <= len(raw):
        block, csize, usize = struct.unpack_from("<III", raw, q + 4)
        if block == 0 and csize == 0 and usize == 0:
            break
        p, pairs, total = q + 16, [], 0
        while total < usize:
            if p + 8 > len(raw):
                raise _Short("chunk header past the read window")
            bc, bu = struct.unpack_from("<II", raw, p)
            p += 8
            pairs.append((bc, bu))
            total += bu
        for bc, bu in pairs:
            blob = raw[p:p + bc]
            if len(blob) < bc:
                raise _Short("sub-block past the read window")
            try:
                part = zlib.decompress(blob)
            except zlib.error:
                part = lzo1x_decompress(blob)
            if len(part) != bu:
                raise upk_read.UpkError("sub-block decodes to %d, header says %d" % (len(part), bu))
            out += part
            p += bc
        q = p
        image = raw[:no] + bytes(out)
        try:
            got = _names(image, nc, no)
        except Exception:  # noqa: BLE001 - name table not complete yet
            continue
        # the oracle: the name rows must end exactly where the import table starts
        if no + _span(image, no, nc) == io and got and got[0] in ("None", ""):
            return got
    raise _Short("name table did not parse inside %d bytes" % len(raw))


def _span(buf, o, nc):
    for _ in range(nc):
        _s, o = _fstr(buf, o)
        o += 8
    return o


def names_fast(path):
    """Name table of a cooked package, reading only as much as it needs."""
    for size in (256 << 10, 1 << 20, 4 << 20, None):
        with open(path, "rb") as f:
            raw = f.read() if size is None else f.read(size)
        try:
            return _parse(raw)
        except _Short:
            continue
    return upk_read.Package(path).names


def _one(path):
    base = os.path.basename(path)
    try:
        names = names_fast(path)
    except Exception as e:  # noqa: BLE001 - reported, never swallowed
        return base, None, "%s: %s" % (type(e).__name__, e)
    hits = sorted({n for n in names if PAT.search(n)})
    return base, (names, hits), None


def validate(sample=60):
    """names_fast must return exactly what upk_read.Package returns."""
    files = sorted(glob.glob(os.path.join(CK, "*.upk")))
    random.seed(7)
    picks = random.sample(files, min(sample, len(files))) + [
        os.path.join(CK, "Playable_Batmobile_SF.upk")]
    bad = []
    for p in picks:
        try:
            ref = upk_read.Package(p).names
        except Exception:  # noqa: BLE001 - a package upk_read cannot open is not a test
            continue
        try:
            got = names_fast(p)
        except Exception as e:  # noqa: BLE001
            bad.append((os.path.basename(p), "raised %s" % e))
            continue
        if got != ref:
            bad.append((os.path.basename(p), "differs (%d vs %d names)" % (len(got), len(ref))))
    return len(picks), bad


def scan():
    files = sorted(glob.glob(os.path.join(CK, "*.upk")))
    with mp.Pool(max(2, (os.cpu_count() or 4) - 1)) as pool:
        res = pool.map(_one, files, chunksize=8)
    rows, bad, n = {}, [], 0
    for base, got, err in res:
        if err:
            bad.append([base, err])
            continue
        n += 1
        names, hits = got
        if not hits:
            continue
        rows[base] = {"names": hits, "exact_referenced": [x for x in EXACT if x in names]}
    # exports need the export table: only for the few packages that named a ramp
    for base in list(rows):
        try:
            pkg = upk_read.Package(os.path.join(CK, base))
        except Exception as e:  # noqa: BLE001
            rows[base]["error"] = "%s: %s" % (type(e).__name__, e)
            continue
        rows[base]["exports"] = [
            {"index": i, "name": e["name"], "class": pkg.object_class(i),
             "size": e["size"]} for i, e in enumerate(pkg.exports, 1)
            if PAT.search(e["name"]) and pkg.object_class(i) in ("Texture2D",)]
    return {"package_count": len(files), "scanned": n, "unreadable": bad, "packages": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    npkgs, bad = validate()
    print("validate: names_fast == upk_read on %d sampled packages, %d mismatches"
          % (npkgs, len(bad)))
    for b in bad[:6]:
        print("   MISMATCH", b)
    if bad:
        print("refusing to report a scan the shortcut contradicts")
        return 2
    got = scan()
    print("upks on disk: %d, name tables read: %d, unreadable: %d, packages naming a ramp: %d"
          % (got["package_count"], got["scanned"], len(got["unreadable"]), len(got["packages"])))
    carriers = {b: r["exports"] for b, r in got["packages"].items() if r.get("exports")}
    print("packages with a Texture2D ramp EXPORT: %d" % len(carriers))
    for b, ex in sorted(carriers.items()):
        print("   %-40s %s" % (b, ", ".join("%s[%d]" % (e["name"], e["index"]) for e in ex)))
    for x in EXACT:
        where = sorted(b for b, r in got["packages"].items() if x in r["exact_referenced"])
        print("%-42s referenced by %2d packages" % (x, len(where)))
    if got["unreadable"]:
        print("unreadable (first 8 of %d): %s" % (len(got["unreadable"]),
                                                  got["unreadable"][:8]))
    if a.check:
        old = json.load(open(OUT))
        same = old.get("packages") == got["packages"] and old.get("scanned") == got["scanned"]
        print("CHECK:", "match" if same else "DRIFT")
        return 0 if same else 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(got, open(OUT, "w"), indent=1)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
