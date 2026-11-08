"""Full 8B-entry parse (a=13 FString-aware); validate coverage + monotonicity."""
import struct

d = open(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\Playable_Batmobile_SF.upk", "rb").read()
s = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
img = d[:0x369] + s
eoff = 0x1C9F9

def serial(idx):
    o = eoff + idx * 72
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
    return img[off:off+size]

for idx, label in [(5280, "RVehicle"), (5281, "Sim"), (5393, "WheelFL")]:
    data = serial(idx)
    p, n, bs = 0, 0, []
    fstr = 0
    ok = True
    while p + 4 <= len(data):
        a, b = struct.unpack_from("<HH", data, p)
        if a == 13:
            (ln,) = struct.unpack_from("<I", data, p + 4)
            if ln > 200:
                ok = False
                break
            try:
                txt = data[p+8:p+8+ln].decode()
            except Exception:
                txt = "?"
            if n < 3 or True:
                pass
            bs.append(b)
            p += 8 + ln
            fstr += 1
            n += 1
            continue
        if a > 16:
            ok = False
            break
        if p + 8 > len(data):
            ok = False
            break
        bs.append(b)
        p += 8
        n += 1
    mono = all(y >= x for x, y in zip(bs, bs[1:]))
    print("%s: entries=%d fstr=%d end=0x%X/%d mono=%s tail=%s" % (
        label, n, fstr, p, len(data), mono, data[p:p+16].hex(" ")))
