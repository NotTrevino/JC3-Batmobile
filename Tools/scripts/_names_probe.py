"""Partial probe: dechunk first chunks only, parse names, grep bank names."""
import os, struct, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lzo1x import lzo1x_decompress  # noqa: E402

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
TAG = b"\xc1\x83\x2a\x9e"

def dec_blk(blk, bu):
    if blk[:2] in (b"\x78\x9c", b"\x78\x01", b"\x78\xda"):
        raw = zlib.decompress(blk)
    else:
        raw = lzo1x_decompress(blk)
    if len(raw) != bu:
        raise ValueError("size %d/%d" % (len(raw), bu))
    return raw

def first_chunks(d, H, maxch=10):
    out = []
    i = d.find(TAG, H)
    while i >= 0 and len(out) < maxch and i + 24 <= len(d):
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
            try: raw = dec_blk(d[q:q+bc], bu)
            except Exception: bad = True; break
            cat += raw; q += bc
        if not bad: out.append(bytes(cat))
        i = d.find(TAG, q)
    return out

for pkg in sys.argv[1:]:
    d = open(os.path.join(CK, pkg), "rb").read()
    (ln,) = struct.unpack_from("<i", d, 12)
    o = 16 + ln
    flags, nc, noff = struct.unpack_from("<iii", d, o)
    stream = b"".join(first_chunks(d, noff))
    img = d[:noff] + stream
    names = []
    oo = noff
    try:
        for _ in range(nc):
            (ln,) = struct.unpack_from("<i", img, oo); oo += 4
            if not (0 < ln < 512 or -512 < ln < 0): raise ValueError((_, ln))
            if ln > 0:
                raw = img[oo:oo+ln]; oo += ln
                names.append(raw[:-1].decode("ascii", "replace"))
            else:
                names.append(img[oo:oo+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); oo += (-ln)*2
            oo += 8
    except Exception as e:
        print("%s: names FAIL %s (got %d)" % (pkg, e, len(names)))
        continue
    print("%s: names=%d" % (pkg, len(names)))
    for n in names:
        if "BML_Battlemode" in n or n in ("Play_Batmobile_Turbo", "Play_BattlemodeEngine",
                                          "VEH_Batmobile_MK2_Engine", "BML_Engine"):
            print("   HIT:", n)
