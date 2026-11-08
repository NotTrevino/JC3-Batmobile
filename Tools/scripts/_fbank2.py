"""GUID scan both encodings + context dump to learn bank metadata layout."""
import os, struct

p = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()
evs = [l.strip() for l in open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\serpente_fmod_events.txt")]

def encodings(g):
    h = g.strip("{}").replace("-", "")
    raw = bytes.fromhex(h)
    a, b, c = struct.unpack(">IHH", raw[:8])
    le = struct.pack("<IHH", a, b, c) + raw[8:]  # mixed-endian GUID struct
    return raw, le

found = {}
for g in evs:
    be, le = encodings(g)
    ib, il = d.find(be), d.find(le)
    if ib >= 0 or il >= 0:
        found[g] = (ib, il)
print("found %d/45" % len(found))
for g, (ib, il) in sorted(found.items(), key=lambda kv: min(x for x in kv[1] if x >= 0)):
    o = ib if ib >= 0 else il
    print("%s @0x%X (%s): %s" % (g, o, "BE" if ib >= 0 else "LE", d[max(0,o-32):o+48].hex(" ")))
missing = [g for g in evs if g not in found]
print("missing:", len(missing))
for g in missing[:10]:
    print("  ", g)
