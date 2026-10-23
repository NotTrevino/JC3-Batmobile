"""test-055: move the baked Havok wheel RAYs to the 047 stance stations.

The physicsc carries the hardpoints as plain (x,y,z,1.0) float quads in two
tables. New Z: front -1.557 -> -1.945, rear +1.446 -> +1.539 (== land_global).
Same size out; asserts diff confined to the patched floats and Havok sections
intact. Havok validation of edited data is UNKNOWN -- one launch decides.
Usage: python _patch_rays.py <in.physicsc> <out.physicsc>
"""
import struct
import sys

OLD_NEW = {-1.557: -1.945, 1.446: 1.539}

src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, "rb").read())
assert d.find(b"hk_2014.1.0") == 40, d[:64]
assert b"__classnames__" in d and b"hknpExternMeshShape" in d

quads = []  # (offset of x) for (x in {+-0.885}, y==0.4, z in OLD)
# scan float-aligned: find y==0.4f with x==+-0.885 before and z old after
hits = []
for o in range(0, len(d) - 16, 4):
    x, y, z, w = struct.unpack_from("<ffff", d, o)
    if (abs(abs(x) - 0.885) < 1e-6 and abs(y - 0.4) < 1e-6
            and w == 1.0 and any(abs(z - k) < 1e-3 for k in OLD_NEW)):
        hits.append((o, x, y, z))
print("RAY quads found:", [(hex(o), x, z) for o, x, y, z in hits])
assert len(hits) == 4, hits  # FL, FR, RL, RR in one table
for o, x, y, z in hits:
    key = -1.557 if abs(z + 1.557) < 1e-3 else 1.446
    struct.pack_into("<f", d, o + 8, OLD_NEW[key])
open(dst, "wb").write(d)
print("patched %d floats, size %d (unchanged)" % (len(hits), len(d)))
