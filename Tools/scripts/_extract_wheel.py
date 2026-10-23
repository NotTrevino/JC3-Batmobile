"""Extract the largest wheel cluster from Batmobile_V2.pskx into a single-wheel
pskx for psk2rbm. Keeps materials 0/9/13 (Wheel/Tyre/Discbreak), clusters faces
by (X, Y) quadrant in the PSK frame (X = length, Y = width), writes PNTS/VTXW/
FACE with remapped indices and the MATT table unchanged (ids stay valid)."""
import struct
import sys

sys.path.insert(0, "Tools/scripts")
from psk2rbm import read_pskx  # noqa: E402

SRC = r"Playable_Batmobile_SF\SkeletalMesh3\Batmobile_V2.pskx"
DST = r"Working\Batmobile\wheel.pskx"
WHEEL_MATS = {0, 9, 13}

P, W, F, mats = read_pskx(SRC)
print("materials:", [mats[i] for i in sorted(WHEEL_MATS)])
sel = [i for i in range(len(F)) if int(F["m"][i]) in WHEEL_MATS]
print("wheel faces:", len(sel), "of", len(F))

pos = P[W["p"].astype(int)]
cen = pos[F["w"][sel]].mean(1)  # face centroids, PSK frame
qx = (cen[:, 0] > 0).astype(int)
qy = (cen[:, 1] > 0).astype(int)
from collections import Counter
groups = Counter(zip(qx.tolist(), qy.tolist()))
print("quadrant (front?, side?) counts:", dict(groups))
best = max(groups, key=groups.get)
take = [sel[i] for i in range(len(sel))
        if (qx[i], qy[i]) == tuple(best)]
print("taking quadrant", tuple(best), len(take), "faces")

tri_w = F["w"][take].astype(int)
# largest connected component by shared POSITION edges (drops stray bits sharing
# the wheel materials: suspension chunks, neighbouring panels)
pt = W["p"][tri_w]  # face corner point ids
parent = list(range(len(take)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb


edge = {}
for i in range(len(take)):
    a, b, c = sorted(pt[i])
    for e in ((a, b), (b, c), (a, c)):
        if e in edge:
            union(i, edge[e])
        else:
            edge[e] = i
from collections import Counter
sizes = Counter(find(i) for i in range(len(take)))
print("components:", len(sizes), "largest:",
      sorted(sizes.values(), reverse=True)[:6])
root = max(sizes, key=sizes.get)
big = {r for r, n in sizes.items() if n >= 300}
# drop far-flung bits sharing the wheel materials: keep only components whose
# centroid is near the main shell (<= 60 PSK units, ~0.35 m fitted)
import numpy as _np
cents = _np.array([pos[F["w"][t]].mean(0) for t in take])
by_root = _np.array([c for i, c in enumerate(cents) if find(i) == root]).mean(0)
near = set()
for r in big:
    c = _np.array([c for i, c in enumerate(cents) if find(i) == r]).mean(0)
    d = float(_np.linalg.norm(c - by_root))
    print("component", r, sizes[r], "faces, dist %.1f" % d)
    if d <= 60.0:
        near.add(r)
take = [take[i] for i in range(len(take)) if find(i) in near]
print("kept", len(take), "faces in", len(near), "components")

tri_w = F["w"][take].astype(int)
used_w = sorted(set(tri_w.ravel()))
wremap = {w: i for i, w in enumerate(used_w)}
used_p = sorted(set(int(W["p"][w]) for w in used_w))
premap = {p: i for i, p in enumerate(used_p)}


def chunk(cid, stride, rows):
    with open(SRC, "rb") as f:
        b = f.read()
    o = 0
    while o + 32 <= len(b):
        tag = b[o:o + 8]
        if tag.startswith(cid):
            return b[o + 8:o + 24], o + 32  # version[16], data offset
        _, _, (st, cn) = tag, None, struct.unpack_from("<II", b, o + 24)
        o += 32 + st * cn
    raise SystemExit("chunk missing: " + str(cid))


out = bytearray()
# PNTS0000 stride 12
ver, _ = chunk(b"PNTS0000", 0, 0)
pts = P[used_p].astype("<f4")
out += b"PNTS0000" + ver + struct.pack("<II", 12, len(pts)) + pts.tobytes()
# VTXW0000 stride 16, remapped point indices
ver, wo = chunk(b"VTXW0000", 0, 0)
vw = bytearray()
for w in used_w:
    vw += struct.pack("<I", premap[int(W["p"][w])]) + W[w].tobytes()[4:16]
assert len(vw) == 16 * len(used_w)
out += b"VTXW0000" + ver + struct.pack("<II", 16, len(used_w)) + bytes(vw)
# FACE3200 stride 18, remapped wedge indices (mat/aux bytes preserved)
ver, fo = chunk(b"FACE3200", 0, 0)
src = open(SRC, "rb").read()
fb = bytearray()
for t in take:
    w0, w1, w2 = (wremap[int(x)] for x in F["w"][t])
    fb += struct.pack("<III", w0, w1, w2) + src[fo + t * 18 + 12: fo + t * 18 + 18]
out += b"FACE3200" + ver + struct.pack("<II", 18, len(take)) + bytes(fb)
# MATT0000 unchanged (ids stay valid)
ver, mo = chunk(b"MATT0000", 0, 0)
mo_end = mo
o = 0
b = src
while o + 32 <= len(b):
    if b[o:o + 8].startswith(b"MATT0000"):
        st, cn = struct.unpack_from("<II", b, o + 24)
        mo_end = o + 32 + st * cn
        break
    st, cn = struct.unpack_from("<II", b, o + 24)
    o += 32 + st * cn
out += b"MATT0000" + ver + struct.pack("<II", st, cn) + b[mo:mo_end]

open(DST, "wb").write(bytes(out))
print("wrote", DST, len(out), "B;", len(used_p), "points,", len(used_w), "wedges,", len(take), "faces")

# validate by re-reading
P2, W2, F2, mats2 = read_pskx(DST)
assert len(F2) == len(take) and len(P2) == len(used_p)
print("re-read OK")
