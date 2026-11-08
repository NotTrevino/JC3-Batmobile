"""BFS from Serpente engine GUIDs through bank refs to FSB subsongs."""
import struct

P = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(P, "rb").read()

# index every 16B high-entropy GUID-like value -> list of offsets (metadata region only, pre-FSB)
f5 = d.find(b"FSB5")
meta = d[:f5]
print("metadata bytes:", len(meta))
# collect all LIST-chunk records with their 4CC path; index GUIDs
idx = {}
o = 0
while True:
    o = meta.find(b"LIST", o)
    if o < 0: break
    (sz,) = struct.unpack_from("<I", meta, o + 4)
    tag = meta[o+8:o+12]
    body = meta[o+12:o+12+sz]
    # every 16B window with high entropy = candidate GUID ref
    for k in range(0, len(body) - 15):
        g = body[k:k+16]
        if len(set(g)) >= 10 and g != b"\x00" * 16:
            idx.setdefault(g, []).append((tag, o, k))
    o += 4

print("distinct GUID-like values:", len(idx))
evs = [l.strip() for l in open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\serpente_fmod_events.txt")]
targets = {bytes.fromhex(g.strip("{}").replace("-", "")) for g in evs}
# BFS
seen = {}
front = [(g, 0, "event") for g in targets if g in idx]
print("seed hits:", len(front))
depth = 0
found_subs = {}
while front and depth < 6:
    nxt = []
    for g, dep, via in front:
        if g in seen: continue
        seen[g] = (dep, via)
        for tag, o, k in idx.get(g, [])[:12]:
            nxt.append((g, dep, tag))
    # group by chunk type for visibility
    from collections import Counter
    c = Counter(t for _, _, t in nxt)
    print("depth", depth, "refs:", dict(c.most_common(10)))
    front = []
    depth += 1
    if depth > 4: break
print("seen GUIDs:", len(seen))
