"""Cross-bank GUID index: every EVTB record + all 16B GUIDs; locate missing 21."""
import os, struct

A = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks"
evs = [l.strip() for l in open(r"E:\Modding\JC3-Batmobile\Working\Audio\serpente_fmod_events.txt")]
targets = set()
for g in evs:
    h = g.strip("{}").replace("-", "")
    targets.add(bytes.fromhex(h))

for bank in ["vehicles.bank", "effects.bank", "character.bank"]:
    d = open(os.path.join(A, bank), "rb").read()
    o = 0
    nevtb = 0
    hits = []
    while True:
        o = d.find(b"EVTB", o)
        if o < 0: break
        (sz,) = struct.unpack_from("<I", d, o + 4)
        body = d[o+8:o+8+sz]
        nevtb += 1
        if body[:16] in targets:
            # trailing GUID list: find count + entries
            hits.append((o, sz, body))
        o += 8 + sz
    print("%s: EVTB=%d serpentine-hits=%d" % (bank, nevtb, len(hits)))
    for o, sz, body in hits[:6]:
        # dump u16/u32 tail pattern to find ref list
        print("  @0x%X sz=%d tail=%s" % (o, sz, body[80:].hex(" ")[:160]))
