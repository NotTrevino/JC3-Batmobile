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

def find_list(d, typ, start=0):
    i = d.find(b"LIST" + struct.pack("<I", 0)[:0], start)
    return i

d = blob("sound/fmod_banks/vehicles.bank")
# locate EVTS list via the top-level child scan
kids = children(d, 12, 8 + struct.unpack_from("<I", d, 4)[0])
proj = kids[1]
pk = children(d, proj[1] + 12, proj[1] + 8 + proj[2])
evts = next(k for k in pk if d[k[1]+8:k[1]+12] == b"EVTS")
print("EVTS list @%d size=%d" % (evts[1], evts[2]))
evkids = children(d, evts[1] + 12, evts[1] + 8 + evts[2])
print("EVTS children:", len(evkids), set(k[0] for k in evkids))
for k in evkids[:2]:
    print("--- event chunk", k[0], "@", k[1], "size", k[2])
    sub = children(d, k[1] + 8, k[1] + 8 + k[2])
    for s in sub:
        print("   ", s[0], "@", s[1], "size", s[2], d[s[1]+8:s[1]+8+min(s[2],64)].hex(" "))
        if s[0] == b"LIST":
            print("      type", d[s[1]+8:s[1]+12])
            for t in children(d, s[1]+12, s[1]+8+s[2]):
                print("        ", t[0], "@", t[1], "size", t[2], d[t[1]+8:t[1]+8+min(t[2],48)].hex(" "))
print()
# scan GUIDs
guids = [l.strip() for l in open(os.path.join(HERE, "..", "..", "Working", "Audio", "serpente_fmod_events.txt"))]
found = {}
for g in guids:
    h = g.strip("{}").replace("-", "")
    raw = bytes.fromhex(h)
    a, b, c = struct.unpack(">IHH", raw[:8])
    le = struct.pack("<IHH", a, b, c) + raw[8:]
    ib, il = d.find(raw), d.find(le)
    if ib >= 0 or il >= 0:
        found[g] = ("BE", ib) if ib >= 0 else ("LE", il)
print("GUIDs in vehicles.bank: %d/45" % len(found))
for g, (enc, o) in list(found.items())[:10]:
    print("  ", g, enc, "@0x%X" % o)
