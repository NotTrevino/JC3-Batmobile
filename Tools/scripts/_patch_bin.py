"""In-place binary member patch for modules that do not survive a
ConvertAdf decode->encode round trip (rigid_body.vmodc loses 16 B; see §89).

Writes a value at a fixed file offset, asserting the old value first, and
asserts the file size is unchanged (so no .toc patch is required).

Spec: {"status": "final", "edits": [{"file": "<rel in aaf>", "offset": "0x50",
       "type": "float"|"int32", "old": 975, "new": 4000}]}
Usage: python _patch_bin.py <spec.json> <aaf-dir> [--check-only]
"""
import json
import os
import struct
import sys

FMT = {"float": "<f", "int32": "<i", "uint32": "<I"}


def main():
    spec = json.load(open(sys.argv[1]))
    aaf = sys.argv[2]
    check_only = "--check-only" in sys.argv
    if spec.get("status") != "final":
        raise SystemExit("spec not final — refusing")
    for ed in spec["edits"]:
        vm = os.path.join(aaf, *ed["file"].split("/"))
        fmt = FMT[ed["type"]]
        size = struct.calcsize(fmt)
        data = bytearray(open(vm, "rb").read())
        off = int(ed["offset"], 0) if isinstance(ed["offset"], str) else ed["offset"]
        cur, = struct.unpack(fmt, data[off:off + size])
        if ed["type"] == "float":
            same = abs(cur - float(ed["old"])) < 1e-4
        else:
            same = cur == int(ed["old"])
        assert same, ("old mismatch", ed["file"], hex(off), cur, ed["old"])
        if check_only:
            print("OK %s @%s %s: %s -> %s" % (ed["file"].split("/")[-1], hex(off),
                                              ed["type"], ed["old"], ed["new"]))
            continue
        before = len(data)
        if ed["type"] == "float":
            struct.pack_into(fmt, data, off, float(ed["new"]))
        else:
            struct.pack_into(fmt, data, off, int(ed["new"]))
        assert len(data) == before
        open(vm, "wb").write(data)
        got, = struct.unpack(fmt, data[off:off + size])
        print("PATCHED %s @%s %s = %s (%d B unchanged)" %
              (ed["file"].split("/")[-1], hex(off), ed["type"], got, len(data)))
    print("done")


main()
