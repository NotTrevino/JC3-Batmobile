import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)

def blob(path):
    r = jc3detail.pick(rows, path)
    return jc3grab.read_entry(r, jc3index.DEFAULT_GAME)

def children(d, start, end):
    o, out = start, []
    while o + 8 <= end:
        tag = d[o:o+4]
        size = struct.unpack_from("<I", d, o + 4)[0]
        out.append((tag, o, size, d[o+8:o+12]))
        o = o + 8 + size + (size & 1)
    return out

for path in ("sound/fmod_banks/master.bank", "sound/fmod_banks/vehicles.bank"):
    d = blob(path)
    print("===", path, len(d))
    # RIFF
    riff_size = struct.unpack_from("<I", d, 4)[0]
    kids = children(d, 12, 8 + riff_size)
    for tag, o, size, head in kids:
        print(f"  {tag} @{o} size={size}")
        if tag == b"LIST":
            print("     type", d[o+8:o+12])
            for c in children(d, o+12, o+8+size):
                print(f"       {c[0]} @{c[1]} size={c[2]} head={d[c[1]+8:c[1]+24].hex(' ')}")
