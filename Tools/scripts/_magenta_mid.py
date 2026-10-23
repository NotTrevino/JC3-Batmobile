"""Make a solid-magenta single-mip DXT1 DDS at any square size, using the
ConvertTexture wrapper layout (124 B header + u32 zero + raw blocks).
Usage: python _magenta_mid.py <size> <out.dds>
"""
import struct
import sys

size, out = int(sys.argv[1]), sys.argv[2]
hdr = bytearray(open(r"Working\TexProbe\body_dif3.dds", "rb").read()[:128])
struct.pack_into("<II", hdr, 12, size, size)
struct.pack_into("<I", hdr, 20, max(1, (size + 3) // 4) * 8)  # DXT1 pitch
n = (size * size) // 2  # DXT1: 8 B per 16 px
open(out, "wb").write(bytes(hdr) + struct.pack("<HHI", 0xF81F, 0, 0) * (n // 8))
print(out, size, len(open(out, "rb").read()))
