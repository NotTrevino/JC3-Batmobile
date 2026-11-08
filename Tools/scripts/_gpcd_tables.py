"""GPCD (uncompressed): parse tables, list AkBank exports incl. BML_Battlemode."""
import os, struct

d = open(os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole", "GlobalPersistentCookerData.upk"), "rb").read()
assert d[:4] == b"\xc1\x83\x2a\x9e"
(ln,) = struct.unpack_from("<i", d, 12)
o = 16 + ln
flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", d, o)
print("flags=0x%X nc=%d noff=0x%X ec=%d eoff=0x%X ic=%d" % (flags & 0xFFFFFFFF, nc, noff, ec, eoff, ic))
names = []
oo = noff
for i in range(nc):
    (ln,) = struct.unpack_from("<i", d, oo); oo += 4
    if not (0 < ln < 512 or -512 < ln < 0):
        print("BAD name entry", i, ln); break
    if ln > 0:
        raw = d[oo:oo+ln]; oo += ln
        names.append(raw[:-1].decode("ascii", "replace"))
    else:
        names.append(d[oo:oo+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); oo += (-ln)*2
    oo += 8
print("names:", len(names))
open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\gpcd_names.txt", "w").write("\n".join(names))
oo = ioff; impcls = []
for i in range(ic):
    cnn, _ = struct.unpack_from("<ii", d, oo + 8)
    onn, _ = struct.unpack_from("<ii", d, oo + 20)
    impcls.append((names[cnn], names[onn])); oo += 28
ak = [i for i, (c, n) in enumerate(impcls) if c == "Class" and n == "AkBank"]
print("AkBank class imports:", ak)
STR = (doff - eoff) // ec
print("stride:", STR, "rem:", (doff - eoff) % ec)
oo = eoff; nbank = 0
for i in range(ec):
    ci, = struct.unpack_from("<i", d, oo)
    ni, nn = struct.unpack_from("<ii", d, oo + 12)
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", d, oo + 20)
    if any(ci == -(a + 1) for a in ak):
        nbank += 1
        if "BML_" in names[ni] or "VEH_" in names[ni] or "Batmobile" in names[ni]:
            print("  BANK-EXPORT[%d] %s size=%d" % (i, names[ni], size))
    oo += STR
print("akbank exports total:", nbank)
