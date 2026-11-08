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
end = 60 + shdr
# printable runs inside the sample header region
runs = []
o = 60
while o < end:
    if 32 <= fsb[o] < 127:
        s = o
        while o < end and 32 <= fsb[o] < 127:
            o += 1
        if o - s >= 4:
            runs.append((s, o - s, fsb[s:o]))
    else:
        o += 1
print("printable runs in shdr region:", len(runs))
for r in runs[:20]:
    print("  @%d len=%d %r" % r)
print("last 64 bytes before name table:", fsb[end-64:end].hex(" "))
print("first 128 of shdr region:", fsb[60:188].hex(" "))
