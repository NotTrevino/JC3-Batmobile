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
i = d.find(b"FSB5")
fsb = d[i:]
n, shdr, namelen = struct.unpack_from("<III", fsb, 8)
print("n=%d shdr=%d namelen=%d" % (n, shdr, namelen))
for off in (60 + shdr, 60 + shdr + 4, 60 + shdr - 4):
    seg = fsb[off:off + 120]
    print("at", off, "->", seg[:120])
