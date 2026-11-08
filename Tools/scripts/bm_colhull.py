"""bm_colhull.py - B-10c (build): the body's WORLD collision hull from the Batmobile mesh.

Found by Q re-test 5 (2026-11-02, user: "entered, collision still misalign"). The parts module gives
sportsmuscle_body world_collision_body_id 0 and raycast_body_id 42. hknpPhysicsSystemData's body table
(shape pointer every 0x60 bytes from +0x2d20) maps body 0 -> one hknpConvexPolytopeShape and body 42 -> the
extern mesh B-10b rebuilt. So B-10b fixed raycasts/bullets only; walls, ground and Rico's feet use body 0,
which is B-10's per-axis-stretched SERPENTE chassis hull (36 vertices).

Rule: body 0 = the convex hull of the Batmobile body mesh (LOD2, welded - bm_colmesh.load_body), within the
fleet's vertex budget (largest shipped hull 244 vertices of 18,797; indices are u8, hard cap 255). Concave
features (between the fins, the cockpit recess) are filled - every JC3 car's world body is one convex hull.

Polytope layout (decoded; oracle = every donor hull re-encodes byte for byte except the junk padding):
  +0x30 relarray vertices (u16 count, u16 offset from the field) -> vec4, w = 0x3F000000 + index, padded
        to a multiple of 4 by repeating the last vertex (and its index)
  +0x40 relarray planes (outward n, d: n.v + d = 0 on the face), padded to x4 - donor pad rows are
        uninitialised memory (NaN seen), so the engine reads `faces` planes only; we repeat the last plane
  +0x44 relarray faces (u16 first index, u8 index count, u8 minHalfAngle)
  +0x48 relarray u8 vertex indices, 16-aligned, each loop CCW about the outward normal; 0x7F pad to 16
minHalfAngle ~ round(255 * smallest angle to a vertex-sharing face / pi): exact on 69 % of donor faces,
mean error 2.7 of 255 (a contact-welding hint; Havok's builder is not reproduced exactly).
Note: jc3hkx.decode_polytope reads the FACE count as `plane_count` (the plane array is padded to x4).

    bm_colhull.apply(physicsc_path, body_rbm_path) -> dict
"""
from __future__ import annotations

import math
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bm_colmesh  # noqa: E402
import jc3hkx  # noqa: E402

HULL_BUDGET = 244
BODY_TABLE, BODY_STRIDE = 0x2D20, 0x60


def _rel(b, at):
    c, o = struct.unpack_from("<HH", b, at)
    return c, at + o


def parse_hull(blob: bytes) -> dict:
    vc, va = _rel(blob, 0x30)
    pc, pa = _rel(blob, 0x40)
    fc, fa = _rel(blob, 0x44)
    ic, ia = _rel(blob, 0x48)
    nv = vc
    while nv > 1 and struct.unpack_from("<I", blob, va + 16 * (nv - 1) + 12)[0] == \
            struct.unpack_from("<I", blob, va + 16 * (nv - 2) + 12)[0]:
        nv -= 1   # padding repeats the last vertex and its index
    return {"V": [struct.unpack_from("<3f", blob, va + 16 * i) for i in range(nv)], "vc": vc,
            "P": [struct.unpack_from("<4f", blob, pa + 16 * i) for i in range(fc)], "pc": pc,
            "F": [struct.unpack_from("<HBB", blob, fa + 4 * i) for i in range(fc)],
            "I": list(blob[ia:ia + ic]), "fa": fa, "ia": ia, "pa": pa, "va": va}


def encode_hull(head: bytes, V, P, loops, mha) -> bytes:
    nv, nf = len(V), len(loops)
    vc, pc = (nv + 3) // 4 * 4, (nf + 3) // 4 * 4
    va = 0x50
    pa = va + 16 * vc
    fa = pa + 16 * pc
    I = [i for lp in loops for i in lp]
    ia = (fa + 4 * nf + 15) // 16 * 16
    end = (ia + len(I) + 15) // 16 * 16
    out = bytearray(end)
    out[:0x30] = head[:0x30]
    struct.pack_into("<HH", out, 0x30, vc, va - 0x30)
    struct.pack_into("<HH", out, 0x40, pc, pa - 0x40)
    struct.pack_into("<HH", out, 0x44, nf, fa - 0x44)
    struct.pack_into("<HH", out, 0x48, len(I), ia - 0x48)
    for i in range(vc):
        j = min(i, nv - 1)
        struct.pack_into("<3fI", out, va + 16 * i, *V[j], 0x3F000000 + j)
    for i in range(pc):
        struct.pack_into("<4f", out, pa + 16 * i, *P[min(i, nf - 1)])
    k = 0
    for i, lp in enumerate(loops):
        struct.pack_into("<HBB", out, fa + 4 * i, k, len(lp), mha[i])
        k += len(lp)
    out[ia:ia + len(I)] = bytes(I)
    out[ia + len(I):end] = b"\x7f" * (end - ia - len(I))
    return bytes(out)


def min_half_angle(P, loops) -> list[int]:
    out = []
    for i, lp in enumerate(loops):
        s, best = set(lp), math.pi
        for j, l2 in enumerate(loops):
            if j != i and s & set(l2):
                c = max(-1.0, min(1.0, sum(P[i][k] * P[j][k] for k in range(3))))
                best = min(best, math.acos(c))
        out.append(max(0, min(255, round(255 * best / math.pi))))
    return out


def selftest(pf) -> dict:
    """Every donor hull re-encodes from its decoded content (the stored minHalfAngle kept), byte for byte
    outside the junk regions (padding plane rows, bytes between the face table and the indices)."""
    n, fails = 0, []
    for o in pf.objects:
        if o.cls != jc3hkx.POLYTOPE:
            continue
        b = pf.blob[pf.base + o.offset:pf.base + o.offset + pf.extents[o.offset]]
        h = parse_hull(b)
        loops = [h["I"][f:f + c] for f, c, _ in h["F"]]
        e = encode_hull(b[:0x30], h["V"], h["P"], loops, [m for _, _, m in h["F"]])
        junk = set()
        for i in range(len(h["P"]), h["pc"]):
            junk.update(range(h["pa"] + 16 * i, h["pa"] + 16 * i + 16))
        junk.update(range(h["fa"] + 4 * len(h["F"]), h["ia"]))
        junk.update(range(0x30, 0x50))   # header tail: compare the relarrays separately below
        bad = [i for i in range(len(b)) if i not in junk and (i >= len(e) or b[i] != e[i])]
        hdr = [struct.unpack_from("<HH", b, x) == struct.unpack_from("<HH", e, x) for x in (0x30, 0x40, 0x44, 0x48)]
        n += 1
        if bad or len(e) != len(b) or not all(hdr):
            fails.append((hex(o.offset), len(b), len(e), [hex(x) for x in bad[:4]], hdr))
    if fails:
        raise SystemExit(f"B-10c selftest: {len(fails)}/{n} donor hulls do not re-encode: {fails[:3]}")
    return {"donor_hulls_reencoded": n}


def batmobile_hull(V):
    from scipy.spatial import ConvexHull
    P = np.asarray(V, np.float64)
    full = ConvexHull(P)
    pts = P[full.vertices]
    if len(pts) > HULL_BUDGET:   # support points along k Fibonacci directions: largest k within budget
        best, lo, hi = None, 16, 8192
        while lo <= hi:
            k = (lo + hi) // 2
            i = np.arange(k) + 0.5
            phi, th = np.arccos(1 - 2 * i / k), math.pi * (1 + 5 ** 0.5) * i
            D = np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)
            sel = np.unique(np.argmax(pts @ D.T, axis=0))
            h = ConvexHull(pts[sel])
            if len(h.vertices) <= HULL_BUDGET:
                best, lo = pts[sel][h.vertices], k + 1
            else:
                hi = k - 1
        pts = best
    h = ConvexHull(pts)
    Vh = pts[h.vertices]
    remap = {int(v): i for i, v in enumerate(h.vertices)}
    groups: list = []
    for s, eq in zip(h.simplices, h.equations):   # merge coplanar triangles into faces
        for g in groups:
            if np.abs(g["eq"] - eq).max() < 1e-6:
                g["tris"].append(s)
                break
        else:
            groups.append({"eq": eq, "tris": [s]})
    planes, loops = [], []
    for g in groups:
        n = g["eq"][:3]
        vs = sorted({remap[int(x)] for t in g["tris"] for x in t})
        c = Vh[vs].mean(0)
        u = Vh[vs[0]] - c
        u /= np.linalg.norm(u)
        w = np.cross(n, u)
        ang = [math.atan2(float(np.dot(Vh[v] - c, w)), float(np.dot(Vh[v] - c, u))) for v in vs]
        loop = [v for _, v in sorted(zip(ang, vs))]   # CCW about the outward normal
        planes.append((float(n[0]), float(n[1]), float(n[2]), -float(np.dot(n, Vh[loop[0]]))))
        loops.append(loop)
    cut = max(max(p[0] * q[0] + p[1] * q[1] + p[2] * q[2] + p[3] for p in planes) for q in P[full.vertices])
    return ([tuple(map(float, v)) for v in Vh], planes, loops,
            {"full_hull_vertices": len(full.vertices), "max_cut_m": round(max(cut, 0.0), 4)})


def check_hull(V, P, loops) -> list[str]:
    errs = []
    for i, (lp, p) in enumerate(zip(loops, P)):
        if len(lp) < 3 or len(lp) > 255:
            errs.append(f"face {i}: {len(lp)} indices")
        on = max(abs(p[0] * V[v][0] + p[1] * V[v][1] + p[2] * V[v][2] + p[3]) for v in lp)
        top = max(p[0] * v[0] + p[1] * v[1] + p[2] * v[2] + p[3] for v in V)
        a, b, c = (np.array(V[lp[k]]) for k in range(3))
        if on > 1e-4 or top > 1e-4 or float(np.dot(np.cross(b - a, c - a), p[:3])) <= 0:
            errs.append(f"face {i}: on {on:.2e} top {top:.2e} or winding")
    return errs


def apply(phys: str, body_rbm: str) -> dict:
    pf = jc3hkx.Packfile(open(phys, "rb").read())
    st = selftest(pf)
    sysd = next(o.offset for o in pf.objects if o.cls == "hknpPhysicsSystemData")
    tab = {fr - sysd: to for fr, _s, to in pf.global_ if sysd <= fr < sysd + pf.extents[sysd]}
    b0, b42 = tab.get(BODY_TABLE), tab.get(BODY_TABLE + BODY_STRIDE * 42)
    if pf._starts.get(b0) != jc3hkx.POLYTOPE or jc3hkx.part_index_of(pf, b42, {}) != 0:
        raise SystemExit("B-10c: body table is not body 0 = polytope / body 42 = part 0's raycast shape")
    V, _T, _M = bm_colmesh.load_body(body_rbm)
    Vh, P, loops, loss = batmobile_hull(V)
    errs = check_hull(Vh, P, loops)
    if errs or len(Vh) > HULL_BUDGET:
        raise SystemExit("B-10c hull: " + " | ".join(errs[:5]))
    mha = min_half_angle(P, loops)
    src = pf.blob[pf.base + b0:pf.base + b0 + pf.extents[b0]]
    out, info = jc3hkx.packfile_bytes(pf, {b0: encode_hull(src, Vh, P, loops, mha)},
                                     {b0: {k: k for k in range(0x50)}})   # header pointer slots stay
    open(phys, "wb").write(out)
    # read back through the table
    pf2 = jc3hkx.Packfile(out)
    s2 = next(o.offset for o in pf2.objects if o.cls == "hknpPhysicsSystemData")
    nb0 = next(to for fr, _s, to in pf2.global_ if fr == s2 + BODY_TABLE)
    h = parse_hull(pf2.blob[pf2.base + nb0:pf2.base + nb0 + pf2.extents[nb0]])
    loops2 = [h["I"][f:f + c] for f, c, _ in h["F"]]
    e2 = check_hull(h["V"], h["P"], loops2)
    if e2 or len(h["V"]) != len(Vh) or len(loops2) != len(loops):
        raise SystemExit("B-10c read-back: " + " | ".join(e2[:5]))
    _i, bad = jc3hkx.check_file(phys)
    if bad:
        raise SystemExit("B-10c check_file: " + " | ".join(bad[:6]))
    Va = np.array(Vh)
    return {"card": "B-10c", **st, "vertices": len(Vh), "faces": len(loops), **loss,
            "bounds": [Va.min(0).round(3).tolist(), Va.max(0).round(3).tolist()],
            "convex_radius": round(pf.f32(b0 + 0x14), 6), "bytes": info["size"]}


if __name__ == "__main__":
    import json
    import shutil
    import tempfile
    tmp = os.path.join(tempfile.mkdtemp(), "out.physicsc")
    shutil.copy(sys.argv[1], tmp)
    print(json.dumps(apply(tmp, sys.argv[2]), indent=1))
    print("written", tmp)
