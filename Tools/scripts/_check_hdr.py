"""If the collision is derived from the render mesh at load, and displacing floats
works while changing counts crashes, then a stale count or offset must live inside
the RBM file. Our codec round-trips byte-exactly, which means any such field is
preserved verbatim -- it is never updated when we grow a buffer.

Compare the raw headers of a vanilla block against our appended-geometry version
and look for a size/offset field that did not move when the payload moved.
"""
import struct
import sys

sys.path.insert(0, r"E:\Modding\JC3-Batmobile\Tools\scripts")
import rbm_geom as R  # noqa: E402

VAN = ("E:/Modding/JC3-Batmobile/Builds/test-003/aaf/models/jc_vehicles/01_land/"
       "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm")
FIN = "E:/Modding/JC3-Batmobile/Builds/test-013/body_lod1_finned.rbm"

av = open(VAN, "rb").read()
af = open(FIN, "rb").read()
mv = R.decode(av)
mf = R.decode(af)

print("=== file header, vanilla vs finned ===")
for label, raw in (("vanilla", av), ("finned ", af)):
    print("  %s first 96 B:" % label)
    for o in range(0, 96, 16):
        print("     0x%04X  %s" % (o, " ".join("%02X" % c for c in raw[o:o + 16])))
    ints = struct.unpack_from("<24I", raw, 0)
    print("     as u32: %s" % [v for v in ints])
print()

print("=== block 0: what changed? ===")
bv, bf = mv.blocks[0], mf.blocks[0]
print("  verts  %d -> %d   (+%d)" % (bv.vb0.count, bf.vb0.count,
                                      bf.vb0.count - bv.vb0.count))
print("  idx    %d -> %d" % (bv.ib.count, bf.ib.count))
sv = len(bv.vb0.data)
sf = len(bf.vb0.data)
print("  vb0 payload  %d B -> %d B   (+%d)" % (sv, sf, sf - sv))
print("  ib  payload  %d B -> %d B" % (len(bv.ib.data), len(bf.ib.data)))
print("  total file   %d B -> %d B   (+%d)" % (len(av), len(af), len(af) - len(av)))
print()

# Re-encode the vanilla block and locate each payload inside it, so we can tell
# which header words act as an offset/size table.
enc = R.encode_block(bv)
print("=== hunting for a stale offset/size table in the block header ===")
print("  vanilla block0 encodes to %d B" % len(enc))
iv = enc.find(bv.vb0.data)
ii = enc.find(bv.ib.data)
print("  vb0 payload found in the encoded block at 0x%04X (len %d)" % (iv, sv))
print("  ib  payload found in the encoded block at 0x%04X (len %d)" % (ii, len(bv.ib.data)))
print()
print("  searching the first 0x40 B of the block for those offsets or sizes...")
head = enc[:0x40]
targets = {
    "vb0 offset 0x%04X" % iv: iv,
    "vb0 size %d" % sv: sv,
    "ib offset 0x%04X" % ii: ii,
    "ib size %d" % len(bv.ib.data): len(bv.ib.data),
    "vert count %d" % bv.vb0.count: bv.vb0.count,
    "index count %d" % bv.ib.count: bv.ib.count,
}
for label, val in targets.items():
    hits = [o for o in range(0, len(head) - 4) if struct.unpack_from("<I", head, o)[0] == val]
    print("     %-18s -> u32 hits in block header at %s"
          % (label, ["0x%02X" % h for h in hits] or "none"))
print()
print("  for contrast, do those same values appear ANYWHERE in the vanilla block?")
for label, val in targets.items():
    n = sum(1 for o in range(0, len(enc) - 4) if struct.unpack_from("<I", enc, o)[0] == val)
    print("     %-18s -> %d occurrence(s) in the whole block" % (label, n))