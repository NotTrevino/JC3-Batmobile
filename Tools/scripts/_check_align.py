"""Displacement keeps every buffer the same size, so it cannot detect a
size-dependent rule. A count change moves every buffer that follows the one that
grew. If the format requires any alignment on buffer starts, displacement would
never expose a violation while any append would.

So: compare buffer start offsets and their alignment, vanilla vs finned, for every
block in both files. A padding fix is a single-variable change if alignment is the
cause.
"""
import struct
import sys

sys.path.insert(0, r"E:\Modding\JustCause3\JC3-Batmobile\Tools\scripts")
import rbm_geom as R  # noqa: E402

VAN = ("E:/Modding/JustCause3/JC3-Batmobile/Builds/test-003/aaf/models/jc_vehicles/01_land/"
       "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm")
FIN = "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-013/body_lod1_finned.rbm"


def payload_offsets(enc, blk):
    """Locate each buffer payload inside the encoded block, in order."""
    found = []
    prev = -1
    for name, buf in (("vb0", getattr(blk, "vb0", None)),
                      ("vb1", getattr(blk, "vb1", None)),
                      ("ib", getattr(blk, "ib", None))):
        if buf is None or not buf.data:
            continue
        at = enc.find(buf.data, prev + 1)
        if at < 0:
            found.append((name, None, len(buf.data), None))
            continue
        found.append((name, at, len(buf.data), at % 16))
        prev = at
    return found


ev = R.encode_block(R.decode(open(VAN, "rb").read()).blocks[0])
ef = R.encode_block(R.decode(open(FIN, "rb").read()).blocks[0])

bv = R.decode(open(VAN, "rb").read()).blocks[0]
bf = R.decode(open(FIN, "rb").read()).blocks[0]

print("=== block 0 buffer placement ===")
ov = payload_offsets(ev, bv)
of = payload_offsets(ef, bf)
print("  %-5s %-26s %s" % ("buf", "vanilla off/len/mod16", "finned off/len/mod16"))
for (n1, a1, l1, m1), (n2, a2, l2, m2) in zip(ov, of):
    f1 = "0x%04X / %6d / %2s" % (a1, l1, m1) if a1 is not None else "not found"
    f2 = "0x%04X / %6d / %2s" % (a2, l2, m2) if a2 is not None else "not found"
    print("  %-5s %-26s %s" % (n1, f1, f2))
print()

print("=== every block: alignment of each buffer start ===")
mv = R.decode(open(VAN, "rb").read())
mf = R.decode(open(FIN, "rb").read())
bad = []
for i, (b1, b2) in enumerate(zip(mv.blocks, mf.blocks)):
    e1 = R.encode_block(b1)
    e2 = R.encode_block(b2)
    for (n1, a1, l1, m1), (n2, a2, l2, m2) in zip(payload_offsets(e1, b1),
                                                 payload_offsets(e2, b2)):
        if a1 is None or a2 is None:
            continue
        same = (a1 % 16) == (a2 % 16)
        delta = a2 - a1
        if not same or delta != (l2 - l1):
            bad.append((i, n1, a1, a2, a1 % 16, a2 % 16, l1, l2))
        print("  blk %d %-4s  van off 0x%04X (mod16 %2d) len %6d | "
              "fin off 0x%04X (mod16 %2d) len %6d | alignment %s"
              % (i, n1, a1, a2, a1 % 16, a2 % 16, l1, l2,
                 "same" if same else "CHANGED"))
print()
print("blocks whose layout did not shift exactly by the size delta: %d" % len(bad))
for r in bad:
    print("   blk %d %s: off %d -> %d, mod16 %d -> %d, len %d -> %d"
          % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
print()

# Is the 0x89ABCDEF block terminator still landing correctly after the growth?
print("=== block terminator integrity in the finned file ===")
raw = open(FIN, "rb").read()
n = raw.count(struct.pack("<I", 0x89ABCDEF))
print("  0x89ABCDEF occurrences in the finned file: %d (vanilla had %d)"
      % (n, open(VAN, "rb").read().count(struct.pack("<I", 0x89ABCDEF))))