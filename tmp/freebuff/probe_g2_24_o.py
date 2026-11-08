import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)

def blob(path):
    r = jc3detail.pick(rows, path)
    return jc3grab.read_entry(r, jc3index.DEFAULT_GAME)

d = blob("sound/fmod_banks/vehicles.bank")
meta = d[:57295680]
strs = [(m.start(), m.group().decode()) for m in re.finditer(rb"[ -~]{5,}", meta)]
print("strings:", len(strs))
kw = ("engine", "horn", "radio", "nitro", "exhaust", "weapon", "turbo", "skid", "impact", "suspens", "gear", "door", "start", "idle", "rpm", "speed")
for off, s in strs:
    lo = s.lower()
    if any(k in lo for k in kw):
        print("%8d  %s" % (off, s[:120]))
