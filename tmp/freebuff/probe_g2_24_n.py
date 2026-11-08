import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)

def blob(path):
    r = jc3detail.pick(rows, path)
    return jc3grab.read_entry(r, jc3index.DEFAULT_GAME)

d = blob("sound/fmod_banks/vehicles.bank")

# WAVS: 649 entries index byte + 16B GUID
snas = 57241896
# parse WAVS list children
def children(d, start, end):
    o, out = start, []
    while o + 8 <= end:
        tag = d[o:o+4]
        size = struct.unpack_from("<I", d, o + 4)[0]
        out.append((tag, o, size))
        o = o + 8 + size + (size & 1)
    return out

wk = children(d, snas + 12, snas + 8 + 22082)
wavs = []
for t in wk:
    if t[0] == b"WAV ":
        body = d[t[1]+8:t[1]+8+t[2]]
        idx = body[0]
        wavs.append((idx, body[1:17]))
print("WAVS entries:", len(wavs), "index range", wavs[0][0], wavs[-1][0])
wavguid = {g: i for i, g in wavs}

# EVTS: find event index and GUIDs
evts = 55115010
ek = children(d, evts + 12, evts + 8 + 66560)
events = [t for t in ek if t[0] == b"LIST"]
def event_info(k):
    body = d[k[1]+8+8+4:k[1]+8+k[2]]  # after LIST/EVNT/EVTB hdr messy
    return body
print("events", len(events))
# print EVTB body first bytes of event 0 and 20
for k in (events[0], events[20]):
    o = k[1]
    sub = children(d, o + 12, o + 8 + k[2])
    evtb = sub[0]
    body = d[evtb[1]+8:evtb[1]+8+evtb[2]]
    print("event @%d idx=%d body[0:20]=%s" % (o, body[0], body[1:21].hex(" ")))
    print("   GUIDs in body:", [body[i:i+16].hex() for i in (1, 33, 49, 65)])

# donor GUID -> offset
g = "{249a34b0-7997-424c-9f26-7b7eb0725e9c}"
raw = bytes.fromhex(g.strip("{}").replace("-", ""))
o = d.find(raw)
print("donor guid offset", o)
# find enclosing EVTB by scanning back for 'EVTB'
back = d.rfind(b"EVTB", o - 400, o)
print("EVTB at", back, "-> event idx?", d[back+8])
# find enclosing LIST EVNT
lv = d.rfind(b"LIST", back - 400, back)
print("LIST at", lv, d[lv+8:lv+12], "size", struct.unpack_from("<I", d, lv+4)[0])

# TLNS entry 0: find WAV GUID matches
tlns = 55181578
tk = children(d, tlns + 12, tlns + 8 + 95536)
tunes = [t for t in tk if t[0] == b"LIST"]
print("tunes", len(tunes))
tb = d[tunes[0][1]:tunes[0][1]+8+tunes[0][2]]
hits = []
for i in range(len(tb) - 15):
    gg = tb[i:i+16]
    if gg in wavguid:
        hits.append((i, wavguid[gg]))
print("tune0 WAV guid hits:", hits)
