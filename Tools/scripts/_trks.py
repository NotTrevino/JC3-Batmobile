"""Walk 112 inline TRAN entries; find FSB indices / WAIT refs / names."""
import struct

P = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(P, "rb").read()
o = 0x34A0A68
(cnt,) = struct.unpack_from("<I", d, o)
assert cnt == 112
p = o + 4
n_names = 0
for k in range(cnt):
    assert d[p:p+4] == b"TRAN", (k, hex(p))
    assert d[p+4:p+8] == b"TRNB", (k, hex(p))
    (sz,) = struct.unpack_from("<I", d, p + 8)
    body = d[p+12:p+12+sz]
    # ASCII strings?
    import re
    strs = [m.decode() for m in re.findall(rb"[ -~]{5,}", body)]
    # small ints (FSB idx candidates)
    u32s = struct.unpack("<%dI" % (len(body)//4), body[:len(body)//4*4])
    small = [u for u in u32s if u < 700]
    if strs or (small and k < 8) or k in (0, 1, 111):
        print("trk%-3d sz=%-4d small=%s strs=%s" % (k, sz, small[:8], strs[:3]))
        if k == 0:
            print("   hex:", body[:96].hex(" "))
    p += 12 + sz
print("end @0x%X" % p)
