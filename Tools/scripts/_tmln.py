"""Full TMLN record for engine_running_sound + track GUID extraction."""
import struct

P = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(P, "rb").read()
want = bytes.fromhex("905be2e525448045a10b6034fd27ff11")
# find TMLN LIST containing it
o = 0
while True:
    o = d.find(b"LIST", o)
    if o < 0: break
    if d[o+8:o+12] == b"TMLN":
        (sz,) = struct.unpack_from("<I", d, o + 4)
        body = d[o+12:o+12+sz]
        if want in body:
            print("TMLN @0x%X sz=%d" % (o, sz))
            print("head:", body[:16].hex(" "))
            # TLNB + size? then guids
            print("full:")
            for k in range(0, len(body), 16):
                print("  +%03d %s" % (k, body[k:k+16].hex(" ")))
            break
    o += 4
