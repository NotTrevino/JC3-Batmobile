import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
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

def entries(sec, typ):
    off, size = secs[sec]
    return [(k[1], k[2]) for k in children(d, off+12, off+8+size)
            if k[0] == b"LIST" and d[k[1]+8:k[1]+12] == typ]

evs = entries(b"EVTS", b"EVNT")
tns = entries(b"TLNS", b"TMLN")
print("events", len(evs), "tunes", len(tns))

def evbody(off, size):
    evtb = children(d, off+12, off+8+size)[0]
    return d[evtb[1]+8:evtb[1]+8+evtb[2]]

def tune_windows(off, size):
    seg = d[off:off+8+size]
    return {seg[i:i+16] for i in range(len(seg)-15)}

tn_win = [tune_windows(o, s) for o, s in tns]
# for each event, which tune windows does its body contain?
hits = []
for i, (o, s) in enumerate(evs):
    b = evbody(o, s)
    bw = {b[k:k+16] for k in range(len(b)-15)}
    m = [j for j, tw in enumerate(tn_win) if bw & tw]
    hits.append(m)
print("events with any tune-window match:", sum(1 for m in hits if m))
print("positional matches:", sum(1 for i, m in enumerate(hits) if i in m))
print("first 12:", hits[:12])
print("horn event (idx 255) matches:", hits[255] if len(hits) > 255 else None)
