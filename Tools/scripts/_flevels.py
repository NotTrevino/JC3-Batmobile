"""Bank level walk: EVNT/TMLN/TRAN/WAIT structures; link Serpente events to FSB."""
import struct

p = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()

def chunks(tag, n=3):
    out = []
    o = 0
    while len(out) < n:
        o = d.find(b"LIST", o)
        if o < 0: break
        if d[o+8:o+12] == tag:
            (sz,) = struct.unpack_from("<I", d, o + 4)
            out.append((o, sz))
        o += 4
    return out

for tag in [b"EVNT", b"TMLN", b"TRAN", b"WAIT"]:
    lst = chunks(tag, 1)
    print("== %r" % tag, ["0x%X sz=%d" % (o, s) for o, s in lst])
    if lst:
        o, sz = lst[0]
        print("   head:", d[o:o+64].hex(" "))
# WAIT entries: find FSB-index-sized ints
o, sz = chunks(b"WAIT", 1)[0]
body = d[o+12:o+12+sz]
print("WAIT body len:", len(body))
# entries separated how? look for repeating u16/u32 size prefixes: scan small ints
import re
print("WAIT head:", body[:96].hex(" "))
