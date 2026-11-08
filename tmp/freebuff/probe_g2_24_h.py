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
        out.append((tag, o, size))
        o = o + 8 + size + (size & 1)
    return out

d = blob("sound/fmod_banks/vehicles.bank")
evts_start = 55115010
evts = children(d, 55115022, 55115010 + 8 + 66560)
print("event list count", struct.unpack_from("<I", d, evts[0][1] + 8)[0])
ev = [k for k in evts if k[0] == b"LIST"]
print("events:", len(ev))
for k in ev[:3]:
    print("=== LIST EVNT @%d size=%d" % (k[1], k[2]))
    print(d[k[1]:k[1]+8+k[2]].hex(" "))
    print("--- children:")
    for t in children(d, k[1] + 12, k[1] + 8 + k[2]):
        print("   %s @%d size=%d : %s" % (t[0].decode(errors="replace"), t[1], t[2], d[t[1]+8:t[1]+8+t[2]].hex(" ")))
