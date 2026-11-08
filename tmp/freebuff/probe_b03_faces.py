"""Throwaway probe: where are the Batmobile_V3_Emissive faces on LOD0/1/2?"""
import os
import sys
from collections import Counter

import numpy as np

ROOT = r"E:/Modding/JC3-Batmobile"
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import psk2rbm as P  # noqa

MESH = r"E:/Modding/_BmAKgrab/meshes/Playable_Batmobile_SF/Playable_Batmobile_SF/SkeletalMesh3"

for name in ("Batmobile_V2.pskx", "Batmobile_V2_Lod1.pskx"):
    path = os.path.join(MESH, name)
    Pp, W, F, mats = P.read_pskx(path)
    print(f"\n=== {name}: {len(Pp)} points, {len(W)} wedges, {len(F)} faces")
    print("materials:", list(enumerate(mats)))
    tri = W["p"][F["w"]]        # wedge -> point index
    cent = Pp[tri].mean(1)          # PSK cm
    jc = P.to_jc3(cent) * 0.01      # metres, JC3 axes
    cnt = Counter(F["m"].tolist())
    for m, c in sorted(cnt.items()):
        sub = jc[F["m"] == m]
        lo, hi = sub.min(0), sub.max(0)
        print(f"  mat {m} {mats[m]:38s} faces {c:7d}  x {lo[0]:+.2f}..{hi[0]:+.2f} "
              f"y {lo[1]:+.2f}..{hi[1]:+.2f} z {lo[2]:+.2f}..{hi[2]:+.2f}")
    m = 5 if len(mats) > 5 else 0   # SLOTS.json: slot 5 = Batmobile_V3_Emissive
    sel = F["m"] == m
    sub = jc[sel]
    print(f"  EMISSIVE mat {m}: {sel.sum()} faces, bbox "
          f"{np.round(sub.min(0),3).tolist()} .. {np.round(sub.max(0),3).tolist()}")
    # cluster by grid cells on z (length) and y (height): print a coarse histogram
    z = sub[:, 2]
    y = sub[:, 1]
    x = sub[:, 0]
    for axis, nm in ((0, "x"), (1, "y"), (2, "z")):
        h, e = np.histogram(sub[:, axis], bins=24)
        print(f"  hist {nm}: " + " ".join(f"{h[i]}" for i in range(len(h))))
        print(f"        edges {e[0]:+.2f} .. {e[-1]:+.2f}")
    # simple connected components over shared vertices of emissive faces
    tri_em = tri[sel]
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for t in tri_em:
        union(t[0], t[1])
        union(t[1], t[2])
    groups = {}
    for k, t in enumerate(tri_em):
        groups.setdefault(find(t[0]), []).append(k)
    comps = sorted(groups.values(), key=len, reverse=True)
    print(f"  components: {len(comps)}  sizes {[len(c) for c in comps[:20]]}")
    for c in comps[:24]:
        pts = jc[sel][c]
        lo, hi = pts.min(0), pts.max(0)
        ctr = (lo + hi) / 2
        print(f"    comp {len(c):5d} faces  centre ({ctr[0]:+.2f},{ctr[1]:+.2f},{ctr[2]:+.2f}) "
              f"size ({hi[0]-lo[0]:.3f},{hi[1]-lo[1]:.3f},{hi[2]-lo[2]:.3f})")
