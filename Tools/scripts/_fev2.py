"""Locate the FSB-ref field: compare trailing layouts across found event records."""
import struct

p = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()
evs = [l.strip() for l in open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\serpente_fmod_events.txt")]
targets = {bytes.fromhex(g.strip("{}").replace("-", "")) for g in evs}
recs = []
o = 0
while True:
    o = d.find(b"EVTB", o)
    if o < 0: break
    (sz,) = struct.unpack_from("<I", d, o + 4)
    recs.append((o, sz))
    o += 8 + sz
shown = 0
for o, sz in recs:
    body = d[o+8:o+8+sz]
    if body[:16] in targets and shown < 4:
        print("record size=%d" % sz)
        for k in range(0, len(body), 16):
            print("  +%03d %s" % (k, body[k:k+16].hex(" ")))
        shown += 1
    if shown >= 4: break
