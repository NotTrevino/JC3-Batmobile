"""Carve embedded banks by BKHD scan within AkBank export ranges."""
import os, struct

stream = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
exports = {"BML_Engine": (7278764, 0x107DF6), "BML_Burnout": (477026, 0x93694),
           "AUX_InBatmobile": (67651, 0x82E51)}
for nm, (size, off) in exports.items():
    so = off - 0x369
    seg = stream[so:so+size]
    i = seg.find(b"BKHD")
    print("== %s: BKHD @+%d (serial %d B)" % (nm, i, size))
    print("   pre-head:", seg[max(0,i-16):i].hex(" "))
    o = i
    if o < 0:
        continue
    # walk sections from BKHD
    total = None
    while o + 8 <= len(seg):
        tag = seg[o:o+4]
        (sz,) = struct.unpack_from("<I", seg, o + 4)
        print("   sect %r size %d @+%d" % (tag, sz, o))
        o += 8 + sz
        if o > i + 2000000 and tag not in (b"BKHD", b"HIRC", b"STID", b"ENVS", b"STMG", b"PLAT", b"INIT"):
            print("   (stop, likely bank end)")
            break
        if tag == b"HIRC":
            total = o
    if total:
        open(os.path.join(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio", "bank_%s.bank" % nm), "wb").write(seg[i:total])
        print("   SAVED (%d B)" % (total - i))
