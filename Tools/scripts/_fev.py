"""Dump full EVENT records for found Serpente GUIDs; find track/sample refs."""
import struct

p = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()
evs = [l.strip() for l in open(r"E:\Modding\JC3-Batmobile\Working\Audio\serpente_fmod_events.txt")]
targets = set()
for g in evs:
    targets.add(bytes.fromhex(g.strip("{}").replace("-", "")))

recs = []
o = 0
while True:
    o = d.find(b"EVTB", o)
    if o < 0: break
    (sz,) = struct.unpack_from("<I", d, o + 4)
    recs.append((o, sz))
    o += 8 + sz
print("EVTB records:", len(recs))
for o, sz in recs:
    body = d[o+8:o+8+sz]
    gid = body[:16]
    if gid in targets:
        print("guid match @0x%X size=%d" % (o, sz))
        print("  hex:", body.hex(" "))
        u32s = struct.unpack("<%dI" % (len(body)//4), body[:len(body)//4*4])
        small = [u for u in u32s if u < 2000]
        print("  small-u32s:", small)
        break
