"""Two things about the appended fin that were never checked.

Position, index range, degeneracy and float sanity were all verified. But the
collision is derived from the mesh, and Havok's mesh-to-convex conversion is
sensitive to two things a render mesh tolerates:

  1. NORMALS. Normals live in vb1 (stride 0x10), not vb0. A zero-length or
     non-normalised normal is invisible to rendering and fatal to a collider.
  2. WINDING. Inconsistent or inverted triangle winding produces garbage plane
     normals during convex decomposition. "No degenerate triangles" says nothing
     about this.

Both are checkable offline.
"""
import struct
import sys

sys.path.insert(0, r"E:\Modding\JustCause3\JC3-Batmobile\Tools\scripts")
import rbm_geom as R  # noqa: E402

CASES = [
    ("test-013 body+fin",
     "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-013/body_lod1_finned.rbm",
     "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-003/aaf/models/jc_vehicles/01_land/"
     "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm"),
    ("test-014 plate_r+fin",
     "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-014/plate_r_finned.rbm",
     "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-003/aaf/models/jc_vehicles/01_land/"
     "v0300_car_kensington_sportsmuscle/sportsmuscle_plate_r_lod1.rbm"),
]


def vb1_floats(buf):
    per = buf.stride // 4
    fmt = "<%df" % per
    return [struct.unpack_from(fmt, buf.data, i * buf.stride) for i in range(buf.count)]


def analyse(label, raw, tag):
    m = R.decode(raw)
    print("--- %s : %s" % (label, tag))
    for bi, b in enumerate(m.blocks):
        vb0, vb1, ib = getattr(b, "vb0", None), getattr(b, "vb1", None), getattr(b, "ib", None)
        if vb1 is None or not getattr(vb1, "data", b""):
            print("    blk %d: no vb1" % bi)
            continue
        nf = vb1_floats(vb1)
        per = vb1.stride // 4
        print("    blk %d: vb1 stride=%d -> %d floats/vertex, count=%d"
              % (bi, vb1.stride, per, vb1.count))
        # normals are the first 3 of each record in the vanilla layout
        bad_zero = bad_len = 0
        bad_uv = 0
        for v in nf:
            nx, ny, nz = v[0], v[1], v[2]
            ln = (nx * nx + ny * ny + nz * nz) ** 0.5
            if ln < 1e-6:
                bad_zero += 1
            elif abs(ln - 1.0) > 0.02:
                bad_len += 1
            if per >= 4:
                u, w = v[2], v[3]
                if not (-0.05 <= u <= 1.05 and -0.05 <= w <= 1.05) and per >= 4:
                    bad_uv += 1
        print("        zero-length normals : %d" % bad_zero)
        print("        non-unit normals    : %d  (|n|-1 > 0.02)" % bad_len)
        if per >= 4:
            print("        out-of-range UVs     : %d" % bad_uv)

        # winding consistency, via signed volume of each triangle
        if vb0 is not None and ib is not None:
            pts = [struct.unpack_from("<fff", vb0.data, i * vb0.stride)
                   for i in range(vb0.count)]
            idx = [struct.unpack_from("<H", ib.data, k * 2)[0] for k in range(ib.count)]
            pos = neg = zero = 0
            for t in range(0, len(idx) - 2, 3):
                a, bb, c = pts[idx[t]], pts[idx[t + 1]], pts[idx[t + 2]]
                u = [bb[i] - a[i] for i in range(3)]
                w = [c[i] - a[i] for i in range(3)]
                n = (u[1] * w[2] - u[2] * w[1],
                     u[2] * w[0] - u[0] * w[2],
                     u[0] * w[1] - u[1] * w[0])
                vol = n[0] * a[0] + n[1] * a[1] + n[2] * a[2]
                if vol > 1e-12:
                    pos += 1
                elif vol < -1e-12:
                    neg += 1
                else:
                    zero += 1
            tot = pos + neg + zero
            minority = min(pos, neg)
            print("        triangle winding     : %d outward, %d inverted, %d coplanar"
                  % (pos, neg, zero))
            print("        minority orientation : %d of %d  (%.1f%%)"
                  % (minority, tot, 100.0 * minority / max(tot, 1)))
    print()


for label, path, orig in CASES:
    analyse(label, open(path, "rb").read(), "APPENDED GEOMETRY (crashed)")
    if orig:
        analyse(label, open(orig, "rb").read(), "pristine vanilla (worked)")