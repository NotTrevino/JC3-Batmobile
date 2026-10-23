"""WAIS table parse + WAIT ordering; validate index hypothesis by distribution."""
import struct
from collections import Counter

p = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()

def find_all(tag):
    out = []
    o = 0
    while True:
        o = d.find(b"LIST", o)
        if o < 0: break
        if d[o+8:o+12] == tag:
            (sz,) = struct.unpack_from("<I", d, o + 4)
            out.append((o, sz))
        o += 4
    return out

waits = find_all(b"WAIT")
print("WAIT-LISTs:", len(waits))
wais = find_all(b"WAIS")
print("WAIS:", [(hex(o), sz) for o, sz in wais])
o, sz = wais[0]
body = d[o+12:o+12+sz]
print("WAIS body len:", len(body), "head:", body[:32].hex(" "))
# try u16 array
u16s = struct.unpack("<%dH" % (len(body)//2), body[:len(body)//2*2])
print("as u16: count=%d min=%d max=%d unique=%d" % (len(u16s), min(u16s), max(u16s), len(set(u16s))))
c = Counter(u16s)
print("top values:", c.most_common(8))
# FSB has 649 subsongs: values should be < 649 if indices
over = [v for v in set(u16s) if v >= 649]
print("values >= 649:", len(over), sorted(over)[:10])
