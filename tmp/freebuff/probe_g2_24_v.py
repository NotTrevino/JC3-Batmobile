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
t = wais[0]
o, size = t[1], t[2]
print("WAIT @%d size=%d" % (o, size))
for r in range(o, o + 8 + size, 32):
    chunk = d[r:r+32]
    print("%7d  %-95s  %s" % (r - o, chunk.hex(" "), "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)))
