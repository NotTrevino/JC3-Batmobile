"""Generic BKHD->export mapper: flag banks hiding in non-AkBank exports."""
import os, struct, sys

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

def image_of(pkg, streamfile, H):
    d = open(os.path.join(CK, pkg), "rb").read()
    s = open(os.path.join(A, streamfile), "rb").read()
    return d[:H] + s

def exports_of(img):
    (ln,) = struct.unpack_from("<i", img, 12)
    o = 16 + ln
    flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", img, o)
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
        cnn, _cn = struct.unpack_from("<ii", img, oo + 8)
        onn, _on = struct.unpack_from("<ii", img, oo + 20)
        if names[cnn] == "Class" and names[onn] == "AkBank":
            ak.add(ii)
        oo += 28
    STR = (doff - eoff) // ec
    oo = eoff; out = []
    for ii in range(ec):
        ci, = struct.unpack_from("<i", img, oo)
        ni, _nn = struct.unpack_from("<ii", img, oo + 12)
        _, _, _, _, size, off = struct.unpack_from("<IIIIII", img, oo + 20)
        out.append((off, off + size, names[ni], any(ci == -(a + 1) for a in ak)))
        oo += STR
    return sorted(out)

for sf, pkg, H in [("Playable_BatmobileMK2_SF.bin", "Playable_BatmobileMK2_SF.upk", 0x375),
                   ("conv/Playable_BatmobileJoker_SF/stream.bin", "Playable_BatmobileJoker_SF.upk", None),
                   ("conv/Playable_BatmobileFunhouse_SF/stream.bin", "Playable_BatmobileFunhouse_SF.upk", None)]:
    if H is None:
        d = open(os.path.join(CK, pkg), "rb").read()
        (ln,) = struct.unpack_from("<i", d, 12)
        H = 16 + ln + 32  # noff approx; recompute below
        (ln2,) = struct.unpack_from("<i", d, 12)
        o = 16 + ln2
        _, _, H = struct.unpack_from("<iii", d, o)[:3]
    img = image_of(pkg, sf, H)
    exps = exports_of(img)
    s = img[H:]
    idxs = []
    i = s.find(b"BKHD")
    while i >= 0:
        idxs.append(i + H); i = s.find(b"BKHD", i + 1)
    print("== %s: %d BKHD" % (pkg, len(idxs)))
    for b in idxs:
        cont = [(a, e, n, ak) for a, e, n, ak in exps if a <= b < e]
        if cont:
            a, e, n, ak = cont[0]
            if not ak:
                print("  NON-AKBANK HOLDER img+0x%X in %s (size %d)" % (b, n, e - a))
        else:
            print("  img+0x%X in NO export" % b)
print("map done")
