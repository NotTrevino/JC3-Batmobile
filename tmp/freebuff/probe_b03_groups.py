"""Throwaway probe 4: emissive clusters in the ONE transform, grouped by dominant bone."""
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

ROOT = r"E:/Modding/JustCause3/JC3-Batmobile"
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import bat_assemble as BA  # noqa
import psk2rbm as P  # noqa
import pskx_parts as PX  # noqa

MESH = r"E:/Modding/ArkhamKnight/_grab/meshes/Playable_Batmobile_SF/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx"
st = json.load(open(os.path.join(ROOT, "Working/TrueScale/stations.json"), encoding="utf-8"))
scale, offset = st["scale"], np.array(st["offset"], float)
Pp, W, F, mats = P.read_pskx(MESH)
bones, Wt = PX.skeleton(MESH)
fb = PX.face_bones(Pp, W, F, Wt, len(bones))
tri = W["p"]
V = BA.to_jc3_rot(Pp) * scale + offset          # the one transform
  
sel = np.nonzero(F["m"] == 5)[0]
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
    t = tri[F["w"][k]]
    union(int(t[0]), int(t[1]))
    union(int(t[1]), int(t[2]))
groups = defaultdict(list)
for k in sel:
    groups[find(int(tri[F["w"][k]][0]))].append(int(k))

by_bone = defaultdict(list)
for comp, faces in groups.items():
    c = Counter(bones[b][0] for b in fb[faces]).most_common(1)[0][0]
    by_bone[c].append(faces)
print(f"{len(groups)} clusters -> {len(by_bone)} bones")
tot = 0
for bone, comps in sorted(by_bone.items(), key=lambda kv: -sum(len(c) for c in kv[1])):
    faces = [f for c in comps for f in c]
    pts = V[tri[F["w"][faces]].ravel()]
    lo, hi = pts.min(0), pts.max(0)
    xs = sorted({round(float(c[0]), 3) for c in [(V[tri[F["w"][f]].ravel()].mean(0)) for f in faces]})
    tot += len(faces)
    print(f"{bone:<28} comps {len(comps):3d} faces {len(faces):5d} "
          f"x {lo[0]:+.3f}..{hi[0]:+.3f} y {lo[1]:+.3f}..{hi[1]:+.3f} z {lo[2]:+.3f}..{hi[2]:+.3f}")
print("total", tot, "of", len(sel))
