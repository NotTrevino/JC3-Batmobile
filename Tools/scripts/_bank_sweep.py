"""Sweep small packs (<8MB): dechunk, list AkBank exports. Finds small bank definers."""
import glob, os, struct, sys, zlib

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
TAG = b"\xc1\x83\x2a\x9e"

def dechunk(d, start):
    out = []
    i = d.find(TAG, start)
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
            try: raw = zlib.decompress(d[q:q+bc])
            except Exception: bad = True; break
            if len(raw) != bu: bad = True; break
            cat += raw; q += bc
        if not bad: out.append(bytes(cat))
        i = d.find(TAG, q)
    return out

packs = sorted((os.path.getsize(p), p) for p in glob.glob(os.path.join(CK, "*.upk")) if os.path.getsize(p) < 8 << 20)
print("small packs:", len(packs))
for sz, p in packs:
    fn = os.path.basename(p)
    try:
        d = open(p, "rb").read()
        (ln,) = struct.unpack_from("<i", d, 12)
        o = 16 + ln
        flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", d, o)
        stream = b"".join(dechunk(d, noff))
        if not stream:
            # maybe uncompressed: tables must parse straight from file
            try:
                (t,) = struct.unpack_from("<i", d, noff)
                if 0 < t < 512 or -512 < t < 0:
                    img = d
                else:
                    print("%-55s LZO/unparsed" % fn); continue
            except Exception:
                print("%-55s LZO/unparsed" % fn); continue
        else:
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
        STR = (doff - eoff) // ec if ec else 72
        oo = eoff; found = []
        for _ in range(ec):
            ci, = struct.unpack_from("<i", img, oo)
            ni, _ = struct.unpack_from("<ii", img, oo + 12)
            if any(ci == -(a + 1) for a in ak) and ("BML_" in names[ni] or "VEH_" in names[ni] or "Bank" in names[ni]):
                found.append(names[ni])
            oo += STR
        if found:
            print("%-55s BANKS: %s" % (fn, found))
    except Exception as e:
        print("%-55s ERR %s" % (fn, str(e)[:80]))
print("sweep done")
