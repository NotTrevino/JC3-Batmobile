import os, sys, struct, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3grab")
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)

def blob(path):
    r = jc3detail.pick(rows, path)
    return jc3grab.read_entry(r, jc3index.DEFAULT_GAME), r

for p in ("sound/fmod_banks/vehicles.bank", "sound/fmod_banks/master.bank",
          "sound/fmod_banks/master_strings.bank", "sound/fmod_banks/master.banklist"):
    d, r = blob(p)
    print("==", p, len(d), "size_field", r.get("size"))
    print("  head:", d[:32].hex(" "))
    # section tags
    tags = []
    for i in range(0, min(len(d), 4096) - 4):
        t = d[i:i+4]
        if t in (b"FSB5", b"BKHD", b"EVNT", b"SNDH", b"SND ", b"STR ", b"LIST", b"GUID", b"PROP", b"VERS", b"INIT", b"INFO", b"NAME", b"BANK"):
            tags.append((i, t))
    print("  tags(first 4KB):", tags[:20])
print()
# master.banklist as text
d, _ = blob("sound/fmod_banks/master.banklist")
print("banklist ascii:", "".join(chr(b) if 32 <= b < 127 else "." for b in d))
