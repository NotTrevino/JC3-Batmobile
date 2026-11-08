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

wais = [t for t in children(d, 56372896 + 12, 56372896 + 8 + 834078) if t[0] == b"LIST"]
for t in wais[:3] + wais[100:101]:
    seg = d[t[1]:t[1] + 8 + t[2]]
    i = seg.find(b"INST")
    body = seg[i+8:i+8+struct.unpack_from("<I", seg, i+4)[0]]
    print("idx %d INST len %d: %s" % (wais.index(t), len(body), body.hex(" ")))
    # interpret candidate u16/u32 fields
    us = [struct.unpack_from("<H", body, k)[0] for k in range(0, len(body)-1, 2)]
    print("   u16:", us[:24])
