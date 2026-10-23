"""Solid-magenta DXT1 payloads for the texture-path discriminator (test-056).

No DXT encoder needed for a flat color: every 8-byte DXT1 block with color0 =
RGB565 magenta, color1 = black, all indices 0 renders uniform magenta. Payload
layouts are preserved byte-for-byte (only block contents change), so container,
mips and sizes are untouched by construction.
Usage: python _magenta.py <in.dds> <out.dds>
"""
import struct
import sys

MAGENTA = struct.pack("<HHI", 0xF81F, 0x0000, 0x00000000)

src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, "rb").read())
assert d[:4] == b"DDS ", src
w, h = struct.unpack_from("<II", d, 12)
pad = 128  # 124 B DDS header + u32 zero (ConvertTexture wrapper alignment)
body = len(d) - pad
assert body % 8 == 0, (src, len(d))
n = body // 8
d[pad:] = MAGENTA * n
open(dst, "wb").write(d)
print("%s: %dx%d, %d blocks magenta, %d B unchanged" % (dst, w, h, n, len(d)))
