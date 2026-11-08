import os, sys, struct, collections
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

kids = children(d, 12, 8 + struct.unpack_from("<I", d, 4)[0])
proj = next(k for k in kids if k[0] == b"LIST" and d[k[1]+8:k[1]+12] == b"PROJ")
secs = {}
for k in children(d, proj[1]+12, proj[1]+8+proj[2]):
    if k[0] == b"LIST":
        secs[d[k[1]+8:k[1]+12]] = (k[1], k[2])

off, size = secs[b"EVTS"]
evs = []
for k in children(d, off+12, off+8+size):
    if k[0] == b"LIST" and d[k[1]+8:k[1]+12] == b"EVNT":
        evtb = children(d, k[1]+12, k[1]+8+k[2])[0]
        evs.append(d[evtb[1]+8:evtb[1]+8+evtb[2]])

off, size = secs[b"TLNS"]
tunes = []
for k in children(d, off+12, off+8+size):
    if k[0] == b"LIST" and d[k[1]+8:k[1]+12] == b"TMLN":
        sub = children(d, k[1]+12, k[1]+8+k[2])
        tl = sub[0]
        body = d[tl[1]+8:tl[1]+8+tl[2]]
        # u32 size, byte 0, GUID
        tl_guid = body[5:21]
        tunes.append(tl_guid)
print("tunes", len(tunes), "distinct", len(set(tunes)))
hits = []
for e in evs:
    m = [i for i, g in enumerate(tunes) if g in e]
    hits.append(m)
c = collections.Counter(len(m) for m in hits)
print("hit-count distribution:", c.most_common())
print("positional:", sum(1 for i, m in enumerate(hits) if m == [i]))
print("first 10:", hits[:10])
