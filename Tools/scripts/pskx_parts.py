"""pskx_parts.py - discover a skeletal PSKX's parts dynamically: no material or bone NAME lists. §73.

Every face gets its DOMINANT bone (RAWWEIGHTS summed over its three points). Each bone's faces are
then classified by SHAPE, in the shared JC3 frame:
    spinning  the geometry covers the full circle around a lateral (X) axis through its own centre
              (>= `--min-sectors` of 16 angular sectors) and is round (Y extent ~ Z extent) --
              tyres, rims, brake discs, wheel fans
    static    everything else (body shell, armour, suspension, weapons, flaps, doors, cockpit)
Spinning bones are grouped into wheels by corner (sign of X, side of the wheel's Z median).

`parts(pskx)` returns (P, W, F, mats, face_bone, bones, classes) for bat_assemble.py; run directly it
prints the per-bone table so the classification is auditable.

RAWWEIGHTS record (stride 12): float weight, u32 point index, u32 bone index.
REFSKELT record (stride 120): char name[64], u32 flags, u32 num_children, u32 parent, quat, pos ...
"""
import argparse
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psk2rbm as P  # noqa: E402


def chunks(b):
    o, ch = 0, {}
    while o + 32 <= len(b):
        cid = b[o:o + 20].split(b"\0")[0].decode("ascii", "replace")
        stride, count = struct.unpack_from("<II", b, o + 24)
        ch[cid] = (o + 32, stride, count)
        o += 32 + stride * count
    return ch


def skeleton(path):
    b = open(path, "rb").read()
    ch = chunks(b)
    o, s, n = ch["REFSKELT"]
    bones = []
    for i in range(n):
        r = b[o + i * s:o + (i + 1) * s]
        name = r[:64].split(b"\0")[0].decode()
        _, _, parent = struct.unpack_from("<III", r, 64)
        bones.append((name, parent))
    o, s, n = ch["RAWWEIGHTS"]
    if s != 12:
        raise SystemExit(f"RAWWEIGHTS stride {s}, expected 12")
    Wt = np.frombuffer(b, np.dtype([("w", "<f4"), ("p", "<u4"), ("b", "<u4")]), n, o)
    return bones, Wt


def face_bones(P_pts, W, F, Wt, nbones):
    """dominant bone per face: sum of the bone weights of its three points"""
    npts = len(P_pts)
    acc = np.zeros((npts, nbones), np.float32)
    np.add.at(acc, (Wt["p"].astype(np.int64), Wt["b"].astype(np.int64)), Wt["w"])
    pts = W["p"][F["w"]].astype(np.int64)                 # (faces, 3) point indices
    return acc[pts].sum(1).argmax(1)


def classify(V, tris, fb, nbones, min_faces=20, min_sectors=15, roundness=0.15):
    """V: wedge positions in JC3 metres; tris: wedge index triples; fb: dominant bone per face."""
    out = {}
    for b in range(nbones):
        sel = np.nonzero(fb == b)[0]
        if len(sel) < min_faces:
            out[b] = ("static", len(sel), None)
            continue
        pts = V[np.unique(tris[sel])]
        lo, hi = pts.min(0), pts.max(0)
        c = (lo + hi) / 2
        ey, ez = hi[1] - lo[1], hi[2] - lo[2]
        ang = np.arctan2(pts[:, 2] - c[2], pts[:, 1] - c[1])
        sectors = len(np.unique(np.floor((ang + np.pi) / (2 * np.pi) * 16).astype(int) % 16))
        rnd = abs(ey - ez) / max(ey, ez, 1e-9)
        spin = sectors >= min_sectors and rnd <= roundness
        out[b] = ("spinning" if spin else "static", len(sel), (c, sectors, rnd, ey, ez))
    return out


def corners_of(classes, V, tris, fb):
    """spinning bones -> corner key by sign of X and side of the Z median of all spinning geometry"""
    spin = [b for b, (k, _, _) in classes.items() if k == "spinning"]
    cz = np.median([classes[b][2][0][2] for b in spin])
    res = {}
    for b in spin:
        c = classes[b][2][0]
        res[b] = ("f" if c[2] < cz else "r") + "_" + ("l" if c[0] < 0 else "r")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pskx")
    ap.add_argument("--scale", type=float, default=0.01)
    a = ap.parse_args()
    Pp, W, F, mats = P.read_pskx(a.pskx)
    bones, Wt = skeleton(a.pskx)
    fb = face_bones(Pp, W, F, Wt, len(bones))
    V = P.to_jc3(Pp[W["p"]]) * a.scale
    tris = F["w"].astype(np.int64)
    cl = classify(V, tris, fb, len(bones))
    cor = corners_of(cl, V, tris, fb)
    print(f"{len(bones)} bones, {len(F)} faces; faces per class:",
          {k: sum(n for kk, n, _ in cl.values() if kk == k) for k in ("spinning", "static")})
    for b, (k, n, info) in sorted(cl.items(), key=lambda kv: -kv[1][1]):
        if n == 0:
            continue
        extra = ""
        if info is not None:
            c, sec, rnd, ey, ez = info
            extra = f"sectors {sec:2d} round {rnd:.2f}  YxZ {ey:.2f}x{ez:.2f}  c ({c[0]:+.2f},{c[1]:.2f},{c[2]:+.2f})"
        print(f"  {k:8s} {cor.get(b, ''):4s} {n:6d}  {bones[b][0][:44]:44s} {extra}")


if __name__ == "__main__":
    main()
