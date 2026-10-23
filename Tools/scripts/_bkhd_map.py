"""Map every BKHD in base stream to its containing export; identify unknown banks."""
import os, struct

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
names = open(os.path.join(A, "bm_names.txt")).read().splitlines()
H = 0x369
img = d[:H] + s

(ln,) = struct.unpack_from("<i", img, 12)
o = 16 + ln
flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", img, o)
STR = (doff - eoff) // ec
exps = []
oo = eoff
for i in range(ec):
    ci, = struct.unpack_from("<i", img, oo)
    ni, nn = struct.unpack_from("<ii", img, oo + 12)
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, oo + 20)
    exps.append((off, off + size, names[ni], ci))
    oo += STR
exps.sort()

bk = []
i = s.find(b"BKHD")
while i >= 0:
    bk.append(i + H)  # image offset
    i = s.find(b"BKHD", i + 1)
print("BKHD in stream:", len(bk))
for b in bk:
    cont = [(a, e, n, c) for a, e, n, c in exps if a <= b < e]
    if cont:
        a, e, n, c = cont[0]
        print("  img+0x%X in export %-44s class=%d size=%d" % (b, n[:44], c, e - a))
    else:
        print("  img+0x%X in NO export (tables region?)" % b)
