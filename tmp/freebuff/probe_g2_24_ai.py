import os, sys, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME

def blob(p):
    return jc3grab.read_entry(jc3detail.pick(rows, p), GAME)

def children(d, start, end):
    o, out = start, []
    while o + 8 <= end:
        tag = d[o:o+4]
        size = struct.unpack_from("<I", d, o + 4)[0]
        out.append((tag, o, size))
        o = o + 8 + size + (size & 1)
    return out

def sections(d):
    kids = children(d, 12, 8 + struct.unpack_from("<I", d, 4)[0])
    proj = next(k for k in kids if k[0] == b"LIST" and d[k[1]+8:k[1]+12] == b"PROJ")
    return proj, children(d, proj[1] + 12, proj[1] + 8 + proj[2])

d = blob("sound/fmod_banks/vehicles.bank")
proj, secs = sections(d)
evts = next(k for k in secs if k[0] == b"LIST" and d[k[1]+8:k[1]+12] == b"EVTS")
ev = [k for k in children(d, evts[1] + 12, evts[1] + 8 + evts[2]) if k[0] == b"LIST"]
print("events", len(ev))
for k in ev[:3] + ev[-2:]:
    sub = children(d, k[1] + 12, k[1] + 8 + k[2])
    evtb = sub[0]
    body = d[evtb[1]+8:evtb[1]+8+evtb[2]]
    print("  ord=%d guid=%s size=%d" % (body[0], body[1:17].hex(), evtb[2]))

# GUID match test
guids = [l.strip() for l in open(os.path.join(HERE, "..", "..", "Working", "Audio", "serpente_fmod_events.txt"))]
raws = {bytes.fromhex(g.strip("{}").replace("-", "")) for g in guids}
matched, unmatched = {}, []
for k in ev:
    body = d[children(d, k[1]+12, k[1]+8+k[2])[0][1]+8:]
    g = body[1:17]
    if g in raws:
        matched[g.hex()] = body[0]
print("donor guids matched to event ordinals:", len(matched))

# PRMS names
prms = next(k for k in secs if k[0] == b"LIST" and d[k[1]+8:k[1]+12] == b"PRMS")
sub = children(d, prms[1] + 12, prms[1] + 8 + prms[2])
names = []
for t in sub:
    if t[0] != b"LIST":
        continue
    seg = d[t[1]:t[1]+8+t[2]]
    # PRMB header: u32 size, u8 0, GUID, u32 0, u16 namelen, name
    i = 12  # after LIST/PRMB/u32size+u8
    # find name length: scan for printable run
    import re
    m = re.search(rb"[ -~]{2,}", seg[12:])
    if m:
        names.append(seg[12+m.start():12+m.end()].decode(errors="replace"))
print("PRMS entries", len(sub)-1, "names", len(names))
print("distinct names", len(set(names)))
print("first 15:", names[:15])
print("rpm-ish:", [n for n in set(names) if "rpm" in n.lower() or "engine" in n.lower() or "speed" in n.lower()][:20])

# weapon GUID bank membership
for p in ("sound/fmod_banks/weapons.bank", "sound/fmod_banks/weapons_preorder.bank",
          "sound/fmod_banks/effects.bank", "sound/fmod_banks/character.bank"):
    raw = blob(p)
    print(p, "size", len(raw), "FSB5", raw.find(b"FSB5") >= 0)
