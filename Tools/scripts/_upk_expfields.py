"""Dump AKEvent export serials: FObjectExport field map + property stream."""
import struct

stream = open(r"E:\Modding\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
names = open(r"E:\Modding\JC3-Batmobile\Working\Audio\bm_names.txt").read().splitlines()
eoff = 0x1C9F9 - 0x369
ST = 72

for idx in (69, 88):
    o = eoff + idx * ST
    print("export[%d]:" % idx, stream[o:o+ST].hex(" "))
    ci, si, oi = struct.unpack_from("<iii", stream, o)
    ni, nn = struct.unpack_from("<ii", stream, o + 12)
    print("  class=%d super=%d outer=%d name=%s num=%d" % (ci, si, oi, names[ni], nn))
    print("  +20:", struct.unpack_from("<IIIIII", stream, o + 20))
    print("  +44:", struct.unpack_from("<IIIIII", stream, o + 44))
    print("  +68:", struct.unpack_from("<H", stream, o + 68))
