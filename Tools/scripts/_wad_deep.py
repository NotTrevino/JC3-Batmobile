"""Deep WAD scan: full-byte scan of every SFX entry for BKHD/HIRC/STID/RIFF/event-IDs."""
import glob, os, struct

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\SFX"
EV1 = struct.pack("<I", 0x388710DB)  # Play_BattlemodeEngine
EV2 = struct.pack("<I", 0xB1B5DD98)  # Play_Batmobile_Turbo

wads = sorted(glob.glob(os.path.join(CK, "SFX_*.wad")))
print("wads:", len(wads))
for p in wads:
    f = open(p, "rb")
    assert f.read(4) == b"WWAD"
    f.seek(8); n = struct.unpack("<I", f.read(4))[0]; f.seek(0x30)
    tab = [struct.unpack("<IIIII", f.read(20)) for _ in range(n)]
    print("== %s (%d entries)" % (os.path.basename(p), n))
    for h, sz, nul, off, nul2 in tab:
        f.seek(off)
        # stream the entry in 64MB chunks (entries up to 1.2GB)
        rem = sz
        nriff = nbkhd = nhirc = nstid = nev1 = nev2 = 0
        carry = b""
        while rem > 0:
            blk = f.read(min(rem, 1 << 26))
            if not blk: break
            rem -= len(blk)
            buf = carry + blk
            nriff += buf.count(b"RIFF")
            nbkhd += buf.count(b"BKHD")
            nhirc += buf.count(b"HIRC")
            nstid += buf.count(b"STID")
            nev1 += buf.count(EV1)
            nev2 += buf.count(EV2)
            carry = buf[-8:]
        # first entry's own magic already RIFF (census); report extras
        print("  %08X %10dB riff=%d bkhd=%d hirc=%d stid=%d EV_battle=%d EV_turbo=%d" %
              (h, sz, nriff, nbkhd, nhirc, nstid, nev1, nev2))
    f.close()
print("scan done")
