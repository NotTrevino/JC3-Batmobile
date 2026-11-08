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

wais = [t for t in children(d, 56372896 + 12, 56372896 + 8 + 834078) if t[0] == b"LIST"]
entries = []
for t in wais:
    seg = d[t[1]:t[1] + 8 + t[2]]
    i = seg.find(b"INST")
    size = struct.unpack_from("<I", seg, i + 4)[0]
    entries.append(seg[i + 8:i + 8 + size])
# also capture the WAIB prefix (before INST)
pref = []
for t in wais:
    seg = d[t[1]:t[1] + 8 + t[2]]
    i = seg.find(b"INST")
    pref.append(seg[:i])
print("entries", len(entries), "min len", min(map(len, entries)), "max", max(map(len, entries)))

for width, fmt in ((2, "<H"), (4, "<I")):
    print("== width", width)
    best = []
    n = min(map(len, entries))
    for off in range(0, n - width + 1):
        vals = []
        ok = True
        for e in entries:
            v = struct.unpack_from(fmt, e, off)[0]
            if v > 700:
                ok = False
                break
            vals.append(v)
        if ok:
            distinct = len(set(vals))
            best.append((off, distinct, max(vals)))
    for off, distinct, mx in best:
        print("  INST off %d distinct=%d max=%d" % (off, distinct, mx))
    # prefix too
    pmin = min(map(len, pref))
    bestp = []
    for off in range(0, pmin - width + 1):
        vals = []
        ok = True
        for e in pref:
            v = struct.unpack_from(fmt, e, off)[0]
            if v > 700:
                ok = False
                break
            vals.append(v)
        if ok:
            bestp.append((off, len(set(vals)), max(vals)))
    for off, distinct, mx in bestp:
        print("  PREF off %d distinct=%d max=%d" % (off, distinct, mx))
