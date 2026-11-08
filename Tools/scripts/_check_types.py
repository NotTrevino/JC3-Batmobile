"""Inventory every non-mesh, non-texture file type in the donor entity.

The .lod files turned out to be nothing but LOD mesh path tables. But the same
walk turned up types I have never opened: .ctunec (x17), .pfxc, .etunec,
.ftunec, .trim (x60), .stringlookup, and an .xml. One of these may be the
declaration site that rejects changed mesh counts, so look at all of them.
"""
import collections
import glob
import os
import re
import struct

ROOT = "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-003/aaf"
SKIP = {".rbm", ".ddsc", ".png", ".tga", ".dds", ".lod", ".epe"}


def summarize(path):
    d = open(path, "rb").read()
    name = os.path.basename(path)
    head = " ".join("%02X" % c for c in d[:32])
    strs = [s.decode("latin1") for s in re.findall(rb"[ -~]{5,}", d)]
    uniq = []
    for s in strs:
        if s not in uniq:
            uniq.append(s)
    print("--- %-42s %7d B" % (name, len(d)))
    print("    head: %s" % head)
    if uniq:
        shown = uniq[:8]
        print("    strings: %s" % " | ".join(repr(s)[:46] for s in shown))
        if len(uniq) > 8:
            print("             ... %d more unique" % (len(uniq) - 8))
    return d


for ext in (".ctunec", ".pfxc", ".etunec", ".ftunec", ".stringlookup", ".xml", ".trim"):
    files = sorted(glob.glob(ROOT + "/**/*" + ext, recursive=True))
    if not files:
        print("=== %s : none ===" % ext)
        continue
    total = sum(os.path.getsize(f) for f in files)
    print("=== %s : %d files, %d B total ===" % (ext, len(files), total))
    for f in files[:2]:
        summarize(f)
    print()

# .trim has 60 files; show one and check whether any of them mentions a render part
print("=== do any .trim / .ctunec / .pfxc files reference render mesh parts? ===")
for ext in (".trim", ".ctunec", ".pfxc", ".etunec", ".ftunec"):
    files = sorted(glob.glob(ROOT + "/**/*" + ext, recursive=True))
    tally = collections.Counter()
    for f in files:
        d = open(f, "rb").read()
        for key in (b"body_lod1", b"plate_r", b"sportsmuscle_body", b".rbm", b"vmodc"):
            if key in d:
                tally[key.decode()] += 1
    print("   %-10s %s" % (ext, dict(tally) if tally else "no mesh/part references"))