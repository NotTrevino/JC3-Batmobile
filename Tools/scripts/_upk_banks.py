"""Find AkBank exports, carve embedded banks, map events->media."""
import json, os, struct

stream = open(r"E:\Modding\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
names = open(r"E:\Modding\JC3-Batmobile\Working\Audio\bm_names.txt").read().splitlines()
NC = len(names)
eoff, ecount, ST = 0x1C9F9 - 0x369, 5490, 72

# import # of class AkBank / AkEvent (class imports have ClassName=="Class")
ioff, icount = 0x182FD - 0x369, 649
imp_names = []
o = ioff
for i in range(icount):
    cnn, _ = struct.unpack_from("<ii", stream, o + 8)
    onn, _ = struct.unpack_from("<ii", stream, o + 20)
    imp_names.append((names[cnn], names[onn]))
    o += 28
akbank_imp = next(i for i, (c, n) in enumerate(imp_names) if c == "Class" and n == "AkBank")
akev_imp = next(i for i, (c, n) in enumerate(imp_names) if c == "Class" and n == "AkEvent")
print("AkBank=import%d AkEvent=import%d" % (akbank_imp, akev_imp))

banks = []
o = eoff
for i in range(ecount):
    ci, = struct.unpack_from("<i", stream, o)
    ni, nn = struct.unpack_from("<ii", stream, o + 12)
    arch, ef, lo, hi, size, off = struct.unpack_from("<IIIIII", stream, o + 20)
    if ci == -(akbank_imp + 1):
        banks.append((names[ni], size, off))
    o += ST
print("AkBank exports:", len(banks))
for nm, size, off in banks:
    print("  %-40s size=%d off=0x%X" % (nm, size, off))
    so = off - 0x369
    print("    serial head:", stream[so:so+32])
    open(os.path.join(r"E:\Modding\JC3-Batmobile\Working\Audio", "bank_%s.bnk" % nm), "wb").write(stream[so:so+size])
