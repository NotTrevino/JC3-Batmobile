"""List vehicle-tuning exports (classes + curve/config objects) in base stream."""
import os, struct

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
names = open(os.path.join(A, "bm_names.txt")).read().splitlines()
img = d[:0x369] + s
(ln,) = struct.unpack_from("<i", img, 12)
o = 16 + ln
flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", img, o)
# import class names for resolving export classes
oo = ioff
impnames = []
for _ in range(ic):
    cnn, _ = struct.unpack_from("<ii", img, oo + 8)
    onn, _ = struct.unpack_from("<ii", img, oo + 20)
    impnames.append((names[cnn], names[onn]))
    oo += 28
STR = (doff - eoff) // ec
oo = eoff
import re
pat = re.compile(r"RBatmobile|Vehicle|Booster|Curve|Engine|Wheel|Transmission|Gear|Throttle|Suspension|Brake|Steer", re.I)
for i in range(ec):
    ci, = struct.unpack_from("<i", img, oo)
    ni, nn = struct.unpack_from("<ii", img, oo + 12)
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, oo + 20)
    nm = names[ni]
    cl = impnames[-ci-1][1] if ci < 0 and -ci-1 < len(impnames) else ("export%d" % ci)
    if pat.search(nm) or pat.search(cl):
        print("exp[%d] class=%s name=%s size=%d" % (i, cl, nm, size))
    oo += STR
