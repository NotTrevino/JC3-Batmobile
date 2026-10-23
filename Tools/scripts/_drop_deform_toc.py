"""Drop the deform record from test-032's .toc (first removal-with-.toc test).
patch_toc keeps offset-0 records unconditionally, so this is a deliberate extra
step beyond patch. Verifies everything else is untouched."""
import struct

P = r"Builds\test-032\v0300_car_kensington_sportsmuscle_civilian_01.ee.toc"
d = open(P, "rb").read()
recs = []
o = 0
while o + 4 <= len(d):
    (nl,) = struct.unpack_from("<I", d, o)
    o += 4
    name = d[o:o + nl].decode()
    o += nl
    (off, sz) = struct.unpack_from("<II", d, o)
    o += 8
    recs.append((name, off, sz))
assert o == len(d)
drop = [r for r in recs if "vehicle_deform" in r[0]]
assert len(drop) == 1, drop
print("dropping:", drop[0])
out = bytearray()
for name, off, sz in recs:
    if "vehicle_deform" not in name:
        nb = name.encode()
        out += struct.pack("<I", len(nb)) + nb + struct.pack("<II", off, sz)
open(P, "wb").write(bytes(out))
print("records: %d -> %d" % (len(recs), len(recs) - 1))
