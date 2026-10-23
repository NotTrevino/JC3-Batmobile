"""Dechunk any package -> stream file; report bank/event-name presence."""
import os, struct, sys, zlib

TAG = b"\xc1\x83\x2a\x9e"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

def dechunk(d):
    payloads = []
    i = d.find(TAG, 0x200)
    while i >= 0 and i + 24 <= len(d):
        x, tc, tu = struct.unpack_from("<III", d, i + 4)
        if x != 0x20000:
            i = d.find(TAG, i + 4); continue
        q = i + 16
        pairs, su = [], 0
        while su < tu:
            if q + 8 > len(d) or len(pairs) > 512: break
            bc, bu = struct.unpack_from("<II", d, q); q += 8
            pairs.append((bc, bu)); su += bu
        if su != tu:
            i = d.find(TAG, i + 4); continue
        cat = bytearray(); bad = False
        for bc, bu in pairs:
            try:
                raw = zlib.decompress(d[q:q+bc])
            except Exception: bad = True; break
            if len(raw) != bu: bad = True; break
            cat += raw; q += bc
        if not bad:
            payloads.append(bytes(cat))
        i = d.find(TAG, q)
    return payloads

pkg = sys.argv[1]
d = open(os.path.join(CK, pkg), "rb").read()
payloads = dechunk(d)
stream = b"".join(payloads)
out = os.path.join(r"E:\Modding\JC3-Batmobile\Working\Audio", os.path.splitext(pkg)[0] + ".bin")
open(out, "wb").write(stream)
print(pkg, "file=%d stream=%d chunks=%d" % (len(d), len(stream), len(payloads)))
for t in [b"BML_Battlemode", b"BML_Batmobile", b"Play_Batmobile_Turbo", b"BKHD", b"STID", b"AkBank"]:
    print("  %r: %d" % (t, stream.count(t)))
