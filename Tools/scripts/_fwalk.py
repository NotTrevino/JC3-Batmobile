"""Walk nested LISTs: TRAN->instrument->WAIT->sound->FSB."""
import struct

P = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(P, "rb").read()

def walk(o, depth=0, maxdepth=6):
    if depth > maxdepth or o + 12 > len(d):
        return
    assert d[o:o+4] == b"LIST", hex(o)
    (sz,) = struct.unpack_from("<I", d, o + 4)
    tag = d[o+8:o+12]
    pad = "  " * depth
    print("%sLIST %s @0x%X sz=%d" % (pad, tag, o, sz))
    end = o + 12 + sz
    if tag in (b"TRAN", b"TMLN", b"EVNT"):
        # dump head only, then recurse into nested LISTs
        print("%s  head: %s" % (pad, d[o+12:o+44].hex(" ")))
    p = o + 12
    # find nested LISTs by scanning for b'LIST' + sane size within bounds
    q = p
    while True:
        q = d.find(b"LIST", q, end - 8)
        if q < 0: break
        (sz2,) = struct.unpack_from("<I", d, q + 4)
        if 0 < sz2 < (end - q):
            walk(q, depth + 1, maxdepth)
            q += 12 + sz2
        else:
            q += 4
    # leaf record dump for instrument/sound-ish
    if tag not in (b"TRAN", b"TMLN", b"EVNT", b"TRNS", b"TLNS", b"EVTS"):
        print("%s  body: %s" % (pad, d[o+12:min(end, o+140)].hex(" ")))

walk(0x34A09EC)
