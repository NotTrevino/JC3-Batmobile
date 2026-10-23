"""Track GUID -> TRAN record -> WAIT refs -> FSB index."""
import struct

P = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(P, "rb").read()
track = bytes.fromhex("8092227e611a0e4b915ed4b7c2c8f9e0")
o = 0
while True:
    o = d.find(b"LIST", o)
    if o < 0: break
    if d[o+8:o+12] == b"TRAN":
        (sz,) = struct.unpack_from("<I", d, o + 4)
        body = d[o+12:o+12+sz]
        if body[8:24] == track:  # TRNB + size + own guid?
            print("TRAN @0x%X sz=%d" % (o, sz))
            for k in range(0, min(len(body), 256), 16):
                print("  +%03d %s" % (k, body[k:k+16].hex(" ")))
            # all GUIDs in body
            print("  ... searching WAIT refs")
            break
    o += 4
