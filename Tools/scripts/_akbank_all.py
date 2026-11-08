"""All AkBank-class imports + matching exports in base & MK2 images (multi-import blind spot check)."""
import os, struct

def load(pkg, streamfile, H):
    CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
    A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
    d = open(os.path.join(CK, pkg), "rb").read()
    s = open(os.path.join(A, streamfile), "rb").read()
    return d[:H] + s

for pkg, streamfile, H in [("Playable_Batmobile_SF.upk", "bm_stream.bin", 0x369),
                           ("Playable_BatmobileMK2_SF.upk", "Playable_BatmobileMK2_SF.bin", 0x375)]:
    img = load(pkg, streamfile, H)
    (ln,) = struct.unpack_from("<i", img, 12)
    o = 16 + ln
    flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", img, o)
    names = []
    oo = noff
    for i in range(nc):
        (ln,) = struct.unpack_from("<i", img, oo); oo += 4
        if ln > 0:
            raw = img[oo:oo+ln]; oo += ln
            names.append(raw[:-1].decode("ascii", "replace"))
        else:
            names.append(img[oo:oo+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); oo += (-ln)*2
        oo += 8
    oo = ioff
    impcls = []
    for i in range(ic):
        cnn, _ = struct.unpack_from("<ii", img, oo + 8)
        onn, _ = struct.unpack_from("<ii", img, oo + 20)
        impcls.append((names[cnn], names[onn])); oo += 28
    akimps = [i for i, (c, n) in enumerate(impcls) if c == "Class" and n == "AkBank"]
    print("== %s: AkBank class imports=%s" % (pkg, akimps))
    STR = (doff - eoff) // ec
    oo = eoff
    for i in range(ec):
        ci, = struct.unpack_from("<i", img, oo)
        ni, nn = struct.unpack_from("<ii", img, oo + 12)
        arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, oo + 20)
        for ai in akimps:
            if ci == -(ai + 1):
                print("  export[%d] class=import%d(AkBank) name=%s size=%d" % (i, ai, names[ni], size))
        oo += STR
