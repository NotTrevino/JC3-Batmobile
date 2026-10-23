"""FSB5 census: all sample entries (name, rate, ch, codec, offset, size)."""
import os, struct

p = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()
f5 = d.find(b"FSB5")
print("FSB5 @0x%X" % f5)
ver, nstreams, shdr, namelen = struct.unpack_from("<IIII", d, f5 + 4)
print("ver=%d streams=%d samplehdr=%d namelen=%d" % (ver, nstreams, shdr, namelen))
# FSB5 layout: base header(60B) then sample headers (shdr each), then extra/names, then data
o = f5 + 60 + shdr
rows = []
nt = d[o:o+namelen]
names = [x.decode() for x in nt.split(b"\x00") if x]
print("nametable names:", len(names))
for n in names:
    if any(w in n.lower() for w in ["kensington", "sportsmuscle", "serpente", "posh", "mu10", "batmobile"]):
        print("  VEH:", n)
print("sample vehicle prefixes:")
from collections import Counter
c = Counter(n.split("_")[2] + "_" + n.split("_")[3] if len(n.split("_")) > 3 else n for n in names)
for k, v in c.most_common(40):
    print("  %4d %s" % (v, k))
