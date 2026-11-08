import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
d = jc3grab.read_entry(jc3detail.pick(rows, "sound/fmod_banks/vehicles.bank"), jc3index.DEFAULT_GAME)

def children(d, start, end):
    o, out = start, []
    while o + 8 <= end:
        tag = d[o:o+4]
        size = struct.unpack_from("<I", d, o + 4)[0]
        out.append((tag, o, size))
        o = o + 8 + size + (size & 1)
    return out

kids = children(d, 12, 8 + struct.unpack_from("<I", d, 4)[0])
proj = kids[1]
pk = children(d, proj[1] + 12, proj[1] + 8 + proj[2])
for want in (b"EVIS", b"WAIS", b"EFIS", b"MODS"):
    k = next(x for x in pk if d[x[1]+8:x[1]+12] == want)
    sub = children(d, k[1] + 12, k[1] + 8 + k[2])
    print("=== %s @%d size=%d chunks=%d" % (want, k[1], k[2], len(sub)))
    print("  tags:", sorted(set(t[0] for t in sub)))
    for t in sub[1:3]:
        print("  %s @%d size=%d : %s" % (t[0].decode(errors="replace"), t[1], t[2], d[t[1]+8:t[1]+8+min(t[2], 96)].hex(" ")))
