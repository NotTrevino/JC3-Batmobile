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

wavs = []
for t in children(d, 57241896 + 12, 57241896 + 8 + 22082):
    if t[0] == b"WAV ":
        wavs.append(d[t[1]+8:t[1]+8+t[2]])
wavguid = {w[1:17]: w[0] for w in wavs}
print("wavs", len(wavs))

# WAIS entries: collect 16B GUIDs (first two after WAIB header)
wais = [t for t in children(d, 56372896 + 12, 56372896 + 8 + 834078) if t[0] == b"LIST"]
print("wais entries", len(wais))
hit = 0
for t in wais[:5]:
    body = d[t[1]+8+8:t[1]+8+t[2]]  # after LIST/WAIT/WAIB?
    print(" wais body head", body[:48].hex(" "))

# try: GUID at body offset 8 and 24 (WAIB has u32 size then 0 then GUID1 then zeros then GUID2)
def wais_guids(t):
    seg = d[t[1]:t[1]+8+t[2]]
    out = []
    for i in range(len(seg) - 15):
        g = seg[i:i+16]
        if g in wavguid:
            out.append((i, wavguid[g]))
    return out

cnt = sum(1 for t in wais if wais_guids(t))
print("wais entries containing a WAV GUID:", cnt)
# TLNS -> WAIS guid matches
waisg = set()
for t in wais:
    seg = d[t[1]:t[1]+8+t[2]]
    for i in (0x2c, 0x30, 0x34, 0x38, 0x3c, 0x40):
        if i + 16 <= len(seg):
            waisg.add(seg[i:i+16])
print("distinct wais guid slots", len(waisg))
tlns = [t for t in children(d, 55181578 + 12, 55181578 + 8 + 95536) if t[0] == b"LIST"]
print("tunes", len(tlns))
m = 0
for t in tlns:
    seg = d[t[1]:t[1]+8+t[2]]
    for i in range(len(seg) - 15):
        if seg[i:i+16] in waisg:
            m += 1
            break
print("tunes with a WAIS guid:", m)
