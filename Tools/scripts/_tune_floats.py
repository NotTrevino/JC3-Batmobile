"""Dump all float32 + int32 values from vehicle tuning serials; eyeball ranges."""
import os, struct

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
names = open(os.path.join(A, "bm_names.txt")).read().splitlines()
img = d[:0x369] + s
eoff = 0x1C9F9

def serial(idx):
    o = eoff + idx * 72
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
    return img[off:off+size]

for idx, label in [(5280, "RVehicle"), (5281, "Sim"), (5393, "WheelFL"), (5110, "Booster")]:
    data = serial(idx)
    print("== exp[%d] %s (%d B)" % (idx, label, len(data)))
    floats = []
    for k in range(0, len(data) - 3):
        v = struct.unpack_from("<f", data, k)[0]
        if v != v:  # nan skip
            continue
        floats.append((k, v))
    # interesting ranges: speeds, ratios, rpm, mass-like
    for k, v in floats:
        av = abs(v)
        if (0.1 < av < 20) or (1000 < av < 30000) or (50 < av < 500):
            print("   @0x%-4X %-14g as-int=%d" % (k, v, struct.unpack_from("<i", data, k)[0]))
