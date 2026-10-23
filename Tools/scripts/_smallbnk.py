"""Parse 57572DAC.bnk fully: sections, HIRC events/sounds, STID, embedded RIFFs."""
import os, struct

d = open(os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\SFX", "57572DAC.bnk"), "rb").read()
print("size:", len(d))
for base, label in ((0x800, "BKHD@0x800"), (0x11B30, "HIRC@0x11B30")):
    tag = d[base:base+4]
    (sz,) = struct.unpack_from("<I", d, base + 4)
    print("%s: tag=%r size=%d" % (label, tag, sz))
o = 0x11B30 + 8
(n,) = struct.unpack_from("<I", d, o); o += 4
print("HIRC objects:", n)
from collections import Counter
tc = Counter()
evs = []
for _ in range(n):
    if o + 5 > len(d): break
    t = d[o]; (ssz,) = struct.unpack_from("<I", d, o + 1)
    tc[t] += 1
    body = d[o+5:o+5+ssz]
    if len(body) >= 4:
        if t == 4:
            eid, = struct.unpack_from("<I", body, 0)
            evs.append(eid)
    o += 5 + ssz
print("types:", dict(sorted(tc.items())))
for e in sorted(evs)[:60]: print("  event %08X" % e)
