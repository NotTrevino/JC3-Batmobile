"""Parse Sim serial as (u16 type, u16 offset, value) stream; show type variety."""
import struct

d = open(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\Playable_Batmobile_SF.upk", "rb").read()
s = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
img = d[:0x369] + s
o = 0x1C9F9 + 5281 * 72
arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
sim = img[off:off+size]
print("sim size:", size)
# first entry seems (0,0,?) 4 bytes; then (4,off,float) 8B each? check stride by offset monotonicity
p = 0
entries = []
while p + 8 <= len(sim):
    a, b = struct.unpack_from("<HH", sim, p)
    if a == 4 and p + 8 <= len(sim):
        v = struct.unpack_from("<f", sim, p + 4)[0]
        entries.append((p, a, b, "f=%g" % v))
        p += 8
    elif a == 2 and p + 8 <= len(sim):
        v = struct.unpack_from("<i", sim, p + 4)[0]
        entries.append((p, a, b, "i=%d" % v))
        p += 8
    elif a == 0 and b == 0:
        entries.append((p, a, b, "zero"))
        p += 4
    else:
        entries.append((p, a, b, "?? next=%s" % sim[p+4:p+8].hex(" ")))
        break
print("parsed entries:", len(entries))
for e in entries[:60]:
    print("  @0x%-4X a=%-3d b=%-5d %s" % e)
