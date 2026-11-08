import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
d = jc3grab.read_entry(jc3detail.pick(rows, "sound/fmod_banks/vehicles.bank"), jc3index.DEFAULT_GAME)
seg = d[537022:55089666]
strs = [(m.start(), m.group().decode()) for m in re.finditer(rb"[ -~]{5,}", seg)]
print("PEFX strings:", len(strs))
for off, s in strs[:30]:
    print("  +%d %r" % (off, s[:110]))
print(" ... tail:")
for off, s in strs[-15:]:
    print("  +%d %r" % (off, s[:110]))
