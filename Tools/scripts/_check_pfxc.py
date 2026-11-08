"""Does the Havok collision container hold a baked copy of the render mesh?

Method note: the first attempt counted int16 triples matching the rounded
position and got 140/140 -- a false positive, because the debris mesh is only
0.389 m across so every component rounds to 0 and (0,0,0) matches everywhere.
This version requires the geometry to actually line up.

If a baked copy exists in a simple form (contiguous float32, or int16 with a
single scale/offset), then it is regenerable in Python and added geometry stops
being blocked. If it does not, the reference is genuine and Havok derives
collision at load from the render mesh it is handed.
"""
import glob
import os
import struct
import sys

sys.path.insert(0, r"E:\Modding\JustCause3\JC3-Batmobile\Tools\scripts")
import rbm_geom as R  # noqa: E402

ROOT = "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-003/aaf"


def mesh_points(path):
    m = R.decode(open(path, "rb").read())
    out = []
    for b in m.blocks:
        vb = getattr(b, "vb0", None)
        if vb is not None:
            for i in range(vb.count):
                out.append(struct.unpack_from("<fff", vb.data, i * vb.stride))
    return out


def bbox_of(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def close(a, b, tol):
    return abs(a - b) <= tol


pairs = []
for pfxc in sorted(glob.glob(ROOT + "/**/*_col.pfxc", recursive=True)):
    stem = os.path.basename(pfxc)[: -len("_col.pfxc")]
    rbm = glob.glob(ROOT + "/**/" + stem + "_lod1.rbm", recursive=True)
    if rbm:
        pairs.append((stem, rbm[0], pfxc))

print("=== debris part / pfxc pairs: %d ===" % len(pairs))

for stem, rbm, pfxc in pairs:
    pts = mesh_points(rbm)
    n = len(pts)
    lo_x, hi_x, lo_y, hi_y, lo_z, hi_z = bbox_of(pts)
    mb = (hi_x - lo_x, hi_y - lo_y, hi_z - lo_z)
    d = open(pfxc, "rb").read()
    print()
    print("--- %s" % stem)
    print("    mesh: %d verts, bbox %.3f x %.3f x %.3f m  |  pfxc %d B"
          % (n, mb[0], mb[1], mb[2], len(d)))

    # ---- 1. contiguous float32 run of exactly n verts, at any byte offset
    need = n * 3 * 4
    best = None
    if need <= len(d):
        for off in range(0, len(d) - need + 1, 4):
            cand = struct.unpack_from("<%df" % (n * 3), d, off)
            cand = [v for v in cand if -50 < v < 50]
            if len(cand) != n * 3:
                continue
            cl = bbox_of([(cand[i * 3], cand[i * 3 + 1], cand[i * 3 + 2])
                          for i in range(n)])
            tol = 1e-3
            if (close(cl[0], lo_x, tol) and close(cl[1], hi_x, tol)
                    and close(cl[2], lo_y, tol) and close(cl[3], hi_y, tol)
                    and close(cl[4], lo_z, tol) and close(cl[5], hi_z, tol)):
                best = off
                break
    print("    contiguous float32 copy of all %d verts: %s"
          % (n, ("FOUND at 0x%04X" % best) if best is not None else "not present"))

    # ---- 2. int16 buffer of n verts: scan for any contiguous run of 3n int16s
    #         whose per-axis span ratio matches the mesh bbox ratio
    need16 = n * 3 * 2
    ratios = [mb[i] / mb[0] for i in range(3)]
    cand_offsets = []
    if need16 <= len(d):
        for off in range(0, len(d) - need16 + 1, 2):
            v = struct.unpack_from("<%dh" % (n * 3), d, off)
            ax = [v[i::3] for i in range(3)]
            if any(len(set(a)) < 2 for a in ax):
                continue
            sp = [max(a) - min(a) for a in ax]
            if min(sp) <= 0:
                continue
            r = [sp[i] / sp[0] for i in range(3)]
            if all(close(r[i], ratios[i], 0.05) for i in range(3)):
                cand_offsets.append(off)
                if len(cand_offsets) >= 3:
                    break
    print("    contiguous int16 buffer whose span ratios match the mesh: %d candidate(s) %s"
          % (len(cand_offsets), ["0x%04X" % o for o in cand_offsets[:3]]))
    for off in cand_offsets[:2]:
        v = struct.unpack_from("<%dh" % (n * 3), d, off)
        ax = [v[i::3] for i in range(3)]
        print("        @0x%04X raw spans %s  (values look like %s)"
              % (off, [max(a) - min(a) for a in ax],
                 "small ints" if max(max(a) for a in ax) < 1000 else "large"))

    # ---- 3. verbatim float32 anywhere (per-vertex, not contiguous)
    hits = 0
    nonzero = 0
    for p in pts:
        if abs(p[0]) > 1e-6 or abs(p[1]) > 1e-6 or abs(p[2]) > 1e-6:
            nonzero += 1
            if d.count(struct.pack("<fff", *p)):
                hits += 1
    print("    non-degenerate verts appearing verbatim as float32: %d of %d"
          % (hits, nonzero))

    # ---- 4. what IS in the file: float32s that look like a car-sized point cloud
    f = [struct.unpack_from("<f", d, o)[0] for o in range(0, len(d) - 4, 4)]
    car = [v for v in f if -20 < v < 20 and abs(v) > 1e-4]
    print("    float32s in -20..20 and non-tiny: %d of %d slots" % (len(car), len(f)))