import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)

def blob(path):
    r = jc3detail.pick(rows, path)
    return jc3grab.read_entry(r, jc3index.DEFAULT_GAME)

d = blob("sound/fmod_banks/vehicles.bank")
print("size", len(d))
i = d.find(b"FSB5")
print("FSB5 at", i, hex(i))
if i >= 0:
    ver, nstreams, shdr, namelen = struct.unpack_from("<IIII", d, i + 4)
    print("ver", ver, "samples", nstreams, "shdr", shdr, "namelen", namelen)
try:
    from fsb5 import FSB5
    fsb = FSB5(d[i:])
    print("fsb5 lib samples:", len(fsb.samples))
    for s in fsb.samples[:6]:
        print("  ", s.name, s.freq, s.channels, s.samples, "loop", s.loop_start, s.loop_end, "mode", s.mode, "len", len(s.data))
except Exception as e:
    print("fsb5 lib error:", type(e).__name__, e)
# top-level chunks after PROJ
def children(d, start, end):
    o, out = start, []
    while o + 8 <= end:
        tag = d[o:o+4]
        size = struct.unpack_from("<I", d, o + 4)[0]
        out.append((tag, o, size))
        o = o + 8 + size + (size & 1)
    return out
kids = children(d, 12, 8 + struct.unpack_from("<I", d, 4)[0])
for k in kids:
    print("top", k[0], hex(k[1]), k[2])
