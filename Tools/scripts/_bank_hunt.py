"""Bank-definer hunt: partial dechunk (tables only) over candidate packs."""
import os, struct, sys, zlib

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
A = r"E:\Modding\JC3-Batmobile\Working\Audio"
TAG = b"\xc1\x83\x2a\x9e"

def partial(d, H, need, maxch=60):
    out = []
    i = d.find(TAG, H)
    while i >= 0 and sum(map(len, out)) < need and len(out) < maxch and i + 24 <= len(d):
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
            if d[q:q+2] not in (b"\x78\x9c", b"\x78\x01", b"\x78\xda"):
                bad = True; break
            try: raw = zlib.decompress(d[q:q+bc])
            except Exception: bad = True; break
            if len(raw) != bu: bad = True; break
            cat += raw; q += bc
        if not bad: out.append(bytes(cat))
        i = d.find(TAG, q)
    return b"".join(out)

cands = [l.split(None, 1)[1] for l in open(os.path.join(A, "zlib_packs.txt")).read().splitlines()]
keys = ["batmobile", "tank", "vehicle", "gad_", "showcase_vehicles", "batpod", "excavator",
        "ace_", "cityx.upk", "cityy.upk", "cityz.upk", "waynetower", "batcave", "panessa"]
cands = [c for c in cands if any(k in c.lower() for k in keys)]
print("candidates:", len(cands))
for pkg in cands:
    try:
        d = open(os.path.join(CK, pkg), "rb").read()
        (ln,) = struct.unpack_from("<i", d, 12)
        o = 16 + ln
        flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", d, o)
        stream = partial(d, noff, doff - noff + 16)
        if len(stream) < doff - noff:
            print("%-50s tables-incomplete" % pkg); continue
        img = d[:noff] + stream
        names = []
        oo = noff
        for _ in range(nc):
            (ln,) = struct.unpack_from("<i", img, oo); oo += 4
            if ln > 0:
                raw = img[oo:oo+ln]; oo += ln
                names.append(raw[:-1].decode("ascii", "replace"))
            else:
                names.append(img[oo:oo+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); oo += (-ln)*2
            oo += 8
        oo = ioff; ak = set()
        for ii in range(ic):
            cnn, _ = struct.unpack_from("<ii", img, oo + 8)
            onn, _ = struct.unpack_from("<ii", img, oo + 20)
            if names[cnn] == "Class" and names[onn] == "AkBank":
                ak.add(ii)
            oo += 28
        STR = (doff - eoff) // ec
        oo = eoff; found = []
        for _ in range(ec):
            ci, = struct.unpack_from("<i", img, oo)
            ni, _ = struct.unpack_from("<ii", img, oo + 12)
            if any(ci == -(a + 1) for a in ak) and ("BML_" in names[ni] or "VEH_" in names[ni] or "Turbo" in names[ni] or "Battle" in names[ni]):
                found.append(names[ni])
            oo += STR
        if found:
            print("%-50s DEFINER?: %s" % (pkg, found))
    except Exception as e:
        print("%-50s ERR %s" % (pkg, str(e)[:70]))
print("hunt done")
