"""Dump (b,value) pairs from tuning serials, tolerant leading pad; full float+int view."""
import struct

d = open(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\Playable_Batmobile_SF.upk", "rb").read()
s = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
img = d[:0x369] + s
eoff = 0x1C9F9

def serial(idx):
    o = eoff + idx * 72
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
    return img[off:off+size]

for idx, label in [(5280, "RVehicle"), (5281, "Sim"), (5393, "WheelFL"), (5110, "Booster")]:
    data = serial(idx)
    # try leading skips 0..4, parse (u16a,u16b,u32v) 8B entries while sane
    best = None
    for skip in range(0, 5):
        p = skip
        rows = []
        while p + 8 <= len(data):
            a, b = struct.unpack_from("<HH", data, p)
            v = struct.unpack_from("<I", data, p + 4)[0]
            if a not in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16):
                break
            rows.append((a, b, v))
            p += 8
        # score: entries parsed + terminator-ish end
        if best is None or len(rows) > len(best[1]):
            best = (skip, rows, p)
    skip, rows, endp = best
    print("== exp[%d] %s size=%d skip=%d entries=%d end=0x%X tail=%s" % (
        idx, label, len(data), skip, len(rows), endp, data[endp:endp+8].hex(" ")))
    for a, b, v in rows:
        f = struct.unpack("<f", struct.pack("<I", v))[0]
        print("   a=%-3d b=%-5d u32=%-10d f=%-12g" % (a, b, v, f))
