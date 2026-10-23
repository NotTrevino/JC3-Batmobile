"""test-018 / test-019: separate vertex-count sensitivity from index-count
sensitivity.

Every build that crashed while adding geometry changed BOTH counts in the same
edit. They were never separated, so "changing counts crashes" has never actually
been tested - only "changing counts *while adding a fin* crashes".

    test-018  drop the last triangle of body block 0.
              index count 3168 -> 3165, vertex count and vertex bytes untouched.
              -> isolates index-count / buffer-size sensitivity.

    test-019  duplicate vertex 0 of body block 0.
              vertex count 1024 -> 1025, index buffer untouched.
              -> isolates vertex-count sensitivity.

Neither adds geometry, so neither needs the fin builder. Both are one-line buffer
edits, which is the point: remove every other variable.

Oracles, all offline:
  * whole file re-encodes byte-identically
  * decoded positions reproduce the bbox the header claims (error 0)
  * no index out of range, no degenerate triangle, no non-finite float
  * block count and 0x89ABCDEF terminator count unchanged
"""
import glob
import os
import shutil
import struct
import sys

sys.path.insert(0, r"E:\Modding\JC3-Batmobile\Tools\scripts")
import rbm_geom as R  # noqa: E402

ROOT = "E:/Modding/JC3-Batmobile/Builds"
VAN_BODY = (ROOT + "/test-003/aaf/models/jc_vehicles/01_land/"
            "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm")


def union_bbox(m):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for b in m.blocks:
        vb = getattr(b, "vb0", None)
        if vb is None:
            continue
        for i in range(vb.count):
            p = struct.unpack_from("<fff", vb.data, i * vb.stride)
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
    return tuple(lo), tuple(hi)


def audit(path, expect_label):
    raw = open(path, "rb").read()
    m = R.decode(raw)
    ok_rt = (m.write() == raw)
    lo, hi = union_bbox(m)
    err = max([abs(lo[k] - m.bbox_min[k]) for k in range(3)]
              + [abs(hi[k] - m.bbox_max[k]) for k in range(3)])
    bad_idx = degen = nonfinite = 0
    for b in m.blocks:
        vb, ib = getattr(b, "vb0", None), getattr(b, "ib", None)
        if vb is None:
            continue
        for i in range(vb.count):
            for k in range(3):
                if struct.unpack_from("<f", vb.data, i * vb.stride + k * 4)[0] != struct.unpack_from("<f", vb.data, i * vb.stride + k * 4)[0]:
                    nonfinite += 1
        if ib is None:
            continue
        idx = [struct.unpack_from("<H", ib.data, k * 2)[0] for k in range(ib.count)]
        bad_idx += sum(1 for x in idx if x >= vb.count)
        degen += sum(1 for t in range(0, len(idx) - 2, 3)
                     if idx[t] == idx[t + 1] or idx[t + 1] == idx[t + 2] or idx[t] == idx[t + 2])
    term = raw.count(struct.pack("<I", 0x89ABCDEF))
    print("  [%s] %s" % (expect_label, os.path.basename(path)))
    print("      size            %d B" % len(raw))
    print("      blocks          %d      terminators %d" % (len(m.blocks), term))
    print("      re-encode exact %s" % ok_rt)
    print("      bbox error      %.6f m" % err)
    print("      bad indices     %d      degenerate tris %d      non-finite %d"
          % (bad_idx, degen, nonfinite))
    b0 = m.blocks[0]
    print("      block0 verts    %d      indices %d" % (b0.vb0.count, b0.ib.count))
    assert ok_rt, "re-encode not byte-identical"
    assert err < 1e-6, "header bbox does not match decoded positions"
    assert bad_idx == 0 and degen == 0 and nonfinite == 0
    assert term == 9 and len(m.blocks) == 9
    return raw


def build_018(out):
    m = R.decode(open(VAN_BODY, "rb").read())
    b = m.blocks[0]
    b.ib.count -= 3
    b.ib.data = b.ib.data[: b.ib.count * 2]
    lo, hi = union_bbox(m)
    m.bbox_min, m.bbox_max = lo, hi
    open(out, "wb").write(m.write())
    return out


def build_019(out):
    m = R.decode(open(VAN_BODY, "rb").read())
    b = m.blocks[0]
    for name in ("vb0", "vb1"):
        buf = getattr(b, name)
        if buf is None or not getattr(buf, "data", b""):
            continue
        buf.data = buf.data + buf.data[: buf.stride]
        buf.count += 1
    lo, hi = union_bbox(m)
    m.bbox_min, m.bbox_max = lo, hi
    open(out, "wb").write(m.write())
    return out


print("=== sanity: does the union-of-blocks bbox reproduce the vanilla header? ===")
mv = R.decode(open(VAN_BODY, "rb").read())
lo, hi = union_bbox(mv)
print("  header bbox  min=%s max=%s" % (
    tuple(round(x, 5) for x in mv.bbox_min), tuple(round(x, 5) for x in mv.bbox_max)))
print("  union  bbox  min=%s max=%s" % (
    tuple(round(x, 5) for x in lo), tuple(round(x, 5) for x in hi)))
print("  -> union matches header: %s" % (
    max([abs(lo[k] - mv.bbox_min[k]) for k in range(3)]
        + [abs(hi[k] - mv.bbox_max[k]) for k in range(3)]) < 1e-5))
print()

for tag, fn in (("test-018", build_018), ("test-019", build_019)):
    # write the generated RBM to a stable staging dir; the packaging step wipes
    # Builds/<tag>, so the source must not live there
    stage = "%s/_bisect" % ROOT
    os.makedirs(stage, exist_ok=True)
    p = fn("%s/%s.rbm" % (stage, tag))
    audit(p, tag)
    print()