"""Hexdump a BmAK export's serial blob (name/type tags visible in ASCII?)."""
import os
import struct

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
img = d[:0x369] + s
eoff = 0x1C9F9

def serial(idx):
    o = eoff + idx * 72
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
    return img[off:off + size], off, size

for idx, label in [(5280, "RVehicleBatmobile"), (5281, "Sim")]:
    data, off, size = serial(idx)
    print("\n===== exp[%d] %s off=0x%X size=%d" % (idx, label, off, size))
    for base in range(0, min(len(data), 512), 32):
        chunk = data[base:base + 32]
        hexs = " ".join("%02x" % b for b in chunk)
        txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print("  %04X  %-95s  %s" % (base, hexs, txt))
