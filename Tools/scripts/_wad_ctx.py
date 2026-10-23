"""Context of EV_battle hit (SFX_3/2043EABD) + trio BKHD: bank fragments?"""
import os, struct

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\SFX"
EV1 = struct.pack("<I", 0x388710DB)

def get(wad, want):
    f = open(os.path.join(CK, wad), "rb")
    assert f.read(4) == b"WWAD"
    f.seek(8); n = struct.unpack("<I", f.read(4))[0]; f.seek(0x30)
    for _ in range(n):
        h, sz, nul, off, nul2 = struct.unpack("<IIIII", f.read(20))
        if "%08X" % h == want:
            f.seek(off)
            return f.read(sz)
    raise SystemExit("missing " + want)

# 1. EV_battle context in 2043EABD (2.6MB)
d = get("SFX_3.wad", "2043EABD")
i = d.find(EV1)
print("2043EABD size:", len(d), "EV@0x%X" % i)
print("ctx:", d[max(0,i-64):i+32].hex(" "))
# surrounding: HIRC nearby?
for tag in (b"HIRC", b"BKHD", b"STID", b"RIFF", b"DATA", b"DIDX"):
    j = d.find(tag, max(0, i-100000))
    print("  nearest %r at 0x%X (rel %d)" % (tag, j, j-i))
# full-section walk from entry start (it starts RIFF per census?)
print("entry head:", d[:16])

# 2. BKHD context in trio member 07896F60
t = get("SFX_3.wad", "07896F60")
j = t.find(b"BKHD")
print("trio BKHD @0x%X of %d" % (j, len(t)))
print("ctx:", t[max(0,j-32):j+64].hex(" "))
print("trio head:", t[:16])
