"""Full-chain solid-magenta DXT1 payload for one .dds element file.

Writes <size>x<size> DXT1 with ALL mips down to 1x1 (solid magenta blocks),
in the ConvertTexture wrapper layout (124 B DDS header + u32 zero + blocks).
Usage: python _magenta_chain.py <size> <out.dds>
"""
import struct
import sys

size, out = int(sys.argv[1]), sys.argv[2]
hdr = bytearray(open(r"Working\TexProbe\body_dif3.dds", "rb").read()[:128])
struct.pack_into("<II", hdr, 12, size, size)
body = bytearray()
s = size
while True:
    n = max(s * s // 2, 8)  # DXT1: 8 B per 16 px, min one block
    body += struct.pack("<HHI", 0xF81F, 0, 0) * (n // 8)
    if s == 1:
        break
    s //= 2
open(out, "wb").write(bytes(hdr) + bytes(body))
print(out, size, len(open(out, "rb").read()))
