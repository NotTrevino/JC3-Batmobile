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
seg = d[i:i+60]
print("header 60B:", seg.hex(" "))
fsb = d[i:]
print("u32s:", [struct.unpack_from("<I", seg, k)[0] for k in range(0, 60, 4)])
n = struct.unpack_from("<I", seg, 8)[0]
shdr = struct.unpack_from("<I", seg, 12)[0]
print("n", n, "shdr", shdr, "per", shdr / n, "mod34", shdr % 34, "mod32", shdr % 32)
base = 60
for k in range(3):
    o = base + k * 34
    print("samplehdr", k, d[i+o:i+o+34].hex(" "))
    print("   u64s", [struct.unpack_from("<Q", d, i+o+8*j)[0] for j in range(4)])
    print("   u32s", [struct.unpack_from("<I", d, i+o+4*j)[0] for j in range(8)])
print("after headers:", d[i+60+shdr:i+60+shdr+80])
nt = d[i+60+shdr:i+60+shdr+struct.unpack_from("<I", seg, 16)[0]]
print("names len", len(nt))
print("names:", nt[:300])
