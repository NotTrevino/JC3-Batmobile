"""Tokenize a BmAK CDO blob as [u16 size][u16 offset][payload] and report:
entry count, offset monotonicity, size histogram, and value samples.
Usage: python _simwalk.py [export_index]
"""
import os
import struct
import sys
from collections import Counter

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
img = d[:0x369] + s
eoff = 0x1C9F9

idx = int(sys.argv[1]) if len(sys.argv) > 1 else 5281
o = eoff + idx * 72
arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
data = img[off:off + size]
print("exp[%d] size=%d" % (idx, size))

for start in (0, 2, 4):
    p = start
    entries = []
    ok = True
    while p + 4 <= len(data):
        sz, of = struct.unpack_from("<HH", data, p)
        p += 4
        if sz > len(data):
            ok = False
            break
        entries.append((of, sz, data[p:p + sz]))
        p += sz
    offs = [e[0] for e in entries]
    mono = all(b >= a for a, b in zip(offs, offs[1:]))
    hist = Counter(e[1] for e in entries)
    print(" start=%d entries=%d end=0x%X/%d mono=%s sizes=%s" % (
        start, len(entries), p, len(data), mono, dict(sorted(hist.items()))))

# detail with the best-looking alignment (start=0)
p = 0
entries = []
while p + 4 <= len(data):
    sz, of = struct.unpack_from("<HH", data, p)
    p += 4
    entries.append((of, sz, data[p:p + sz]))
    p += sz
print("\nfirst 60 entries (off, size, value):")
for of, sz, pl in entries[:60]:
    if sz == 4:
        v = "f=%g" % struct.unpack("<f", pl)[0]
    elif sz == 8:
        v = "f2=(%g,%g)" % struct.unpack("<ff", pl)
    else:
        v = pl[:16].hex(" ")
    print("  off=0x%04X size=%-3d %s" % (of, sz, v))
