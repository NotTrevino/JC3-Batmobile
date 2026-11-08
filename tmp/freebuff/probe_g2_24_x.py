import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
d = jc3grab.read_entry(jc3detail.pick(rows, "sound/fmod_banks/vehicles.bank"), jc3index.DEFAULT_GAME)

def children(d, start, end):
    o, out = start, []
    while o + 8 <= end:
        tag = d[o:o+4]
        size = struct.unpack_from("<I", d, o + 4)[0]
        out.append((tag, o, size))
        o = o + 8 + size + (size & 1)
    return out

wavs = []
for t in children(d, 57241896 + 12, 57241896 + 8 + 22082):
    if t[0] == b"WAV ":
        wavs.append(d[t[1]+8:t[1]+8+t[2]])

def variants(g):
    a, b, c = struct.unpack(">IHH", g[:8])
    return {
        "raw": g,
        "le8": struct.pack("<IHH", a, b, c) + g[8:],
        "rev": g[::-1],
        "le4": struct.pack("<I", a) + g[4:],
    }

tag = {}
for w in wavs:
    for name, v in variants(w[1:17]).items():
        tag.setdefault(name, set()).add(v)
print({k: len(v) for k, v in tag.items()})

for sec_name, sec_off, sec_size in (("WAIS", 56372896, 834078), ("TLNS", 55181578, 95536), ("EVTS", 55115010, 66560)):
    hits = {k: 0 for k in tag}
    seg = d[sec_off:sec_off + 8 + sec_size]
    for i in range(len(seg) - 15):
        for k, vs in tag.items():
            if seg[i:i+16] in vs:
                hits[k] += 1
    print(sec_name, hits)
