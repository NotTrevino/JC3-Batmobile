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
        body = d[t[1]+8:t[1]+8+t[2]]
        wavs.append((body[0], body[1:17]))
wavguid = {g: i for i, g in wavs}
print("wavs", len(wavs), wavs[0][0], wavs[-1][0])

kids = children(d, 12, 8 + struct.unpack_from("<I", d, 4)[0])
proj = kids[1]
pk = children(d, proj[1] + 12, proj[1] + 8 + proj[2])
for k in pk:
    if k[0] != b"LIST":
        continue
    typ = d[k[1]+8:k[1]+12]
    body_start, body_end = k[1]+12, k[1]+8+k[2]
    hits, offs = 0, []
    for i in range(body_start, body_end - 15):
        if d[i:i+16] in wavguid:
            hits += 1
            offs.append(i - body_start)
    print("%s size=%d wavguid-hits=%d %s" % (typ.decode(errors="replace"), k[2], hits, offs[:6]))
