"""Throwaway probe 2: full emissive component list with the dominant bone of every face."""
import os
import sys
from collections import Counter

import numpy as np

ROOT = r"E:/Modding/JustCause3/JC3-Batmobile"
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import psk2rbm as P  # noqa
import pskx_parts as PX  # noqa

MESH = r"E:/Modding/ArkhamKnight/_grab/meshes/Playable_Batmobile_SF/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx"
Pp, W, F, mats = P.read_pskx(MESH)
bones, Wt = PX.skeleton(MESH)
fb = PX.face_bones(Pp, W, F, Wt, len(bones))
tri = W["p"][F["w"]]
V = P.to_jc3(Pp) * 0.01          # wedge->point, JC3 metres
m = 5
sel = np.nonzero(F["m"] == m)[0]
print(f"emissive faces {len(sel)} of {len(F)}")

# union-find over shared POINTS (not wedges) so UV seams do not split a lens
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


for k in sel:
    t = tri[k]
    union(int(t[0]), int(t[1]))
    union(int(t[1]), int(t[2]))
groups = {}
for k in sel:
    groups.setdefault(find(int(tri[k][0])), []).append(int(k))
comps = sorted(groups.values(), key=len, reverse=True)
print(f"components {len(comps)}  total faces {sum(len(c) for c in comps)}")
rows = []
for c in comps:
    pts = V[tri[c].ravel()]
    lo, hi = pts.min(0), pts.max(0)
    ctr = (lo + hi) / 2
    bn = Counter(bones[b][0] for b in fb[c]).most_common(3)
    rows.append((len(c), ctr, hi - lo, bn))
rows.sort(key=lambda r: (r[1][2], r[1][0]))
for n, ctr, size, bn in rows:
    print(f"  {n:5d} faces  c=({ctr[0]:+.3f},{ctr[1]:+.3f},{ctr[2]:+.3f}) "
          f"size=({size[0]:.3f},{size[1]:.3f},{size[2]:.3f})  bones={bn}")
