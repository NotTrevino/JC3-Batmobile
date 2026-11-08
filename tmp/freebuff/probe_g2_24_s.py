import os, sys, re, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
d = jc3grab.read_entry(jc3detail.pick(rows, "sound/fmod_banks/vehicles.bank"), jc3index.DEFAULT_GAME)

start = 55205400
end = 55206200
for o in range(start, end, 32):
    chunk = d[o:o+32]
    print("%8d  %-95s  %s" % (o, chunk.hex(" "), "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)))
