"""Stride-variant scoring: configs that fully consume all 4 serials win."""
import struct

d = open(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\Playable_Batmobile_SF.upk", "rb").read()
s = open(r"E:\Modding\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
img = d[:0x369] + s
eoff = 0x1C9F9

def serial(idx):
    o = eoff + idx * 72
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
    return img[off:off+size]

blobs = {"RVehicle": serial(5280), "Sim": serial(5281), "Wheel": serial(5393), "Booster": serial(5110)}

def parse(data, sizes, skip):
    p = skip
    n = 0
    while p < len(data):
        if p + 4 > len(data):
            return None
        a, b = struct.unpack_from("<HH", data, p)
        if a not in sizes:
            return None
        if a in (3, 13):
            if p + 8 > len(data):
                return None
            (ln,) = struct.unpack_from("<I", data, p + 4)
            if ln > 500:
                return None
            p += 8 + ln
            n += 1
            continue
        sz = sizes[a]
        if p + 4 + sz > len(data):
            # trailing (0,0) terminator 2B?
            if p + 2 <= len(data):
                return (n, len(data) - p)
            return None
        p += 4 + sz
        n += 1
    return (n, 0)

results = []
for s1 in (1, 4):
    for s10 in (4, 8):
        for s0 in (0, 4):
            for s6 in (4, 8):
                for sk in (0, 1, 4):
                    sizes = {0: s0, 1: s1, 2: 4, 3: -1, 4: 4, 6: s6, 10: s10, 13: -1, 16: 4}
                    ok = True
                    tot = 0
                    for label, data in blobs.items():
                        r = parse(data, sizes, sk)
                        if r is None:
                            ok = False
                            break
                        tot += r[0]
                    results.append((ok, tot, s1, s10, s0, s6, sk))
for ok, tot, s1, s10, s0, s6, sk in sorted(results, reverse=True)[:12]:
    print("ok=%s entries=%d s1=%d s10=%d s0=%d s6=%d skip=%d" % (ok, tot, s1, s10, s0, s6, sk))
