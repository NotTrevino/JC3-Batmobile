import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)

def blob(path):
    r = jc3detail.pick(rows, path)
    return jc3grab.read_entry(r, jc3index.DEFAULT_GAME)

def dump(d, start, end, depth=0, limit=None, base=0):
    o = start
    n = 0
    while o + 8 <= end:
        tag = d[o:o+4]
        if not all(32 <= b < 127 for b in tag):
            print("  " * depth + f"?? non-ascii at {o}: {d[o:o+16].hex(' ')}")
            return
        size = struct.unpack_from("<I", d, o + 4)[0]
        body = o + 8
        print("  " * depth + f"{tag.decode()} @{o} size={size}" + (f" head={d[body:body+16].hex(' ')}" if tag not in (b'RIFF', b'LIST') else f" type={d[body:body+4]}"))
        if tag in (b"RIFF", b"LIST"):
            dump(d, body + 4, body + size, depth + 1)
        o = body + size + (size & 1)
        n += 1
        if limit and n >= limit:
            return

d = blob("sound/fmod_banks/master.bank")
print("=== master.bank", len(d))
dump(d, 0, min(len(d), 700), limit=40)
