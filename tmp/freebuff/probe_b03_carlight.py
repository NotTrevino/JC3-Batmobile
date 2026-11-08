"""Throwaway probe 3: CarLight static header - is any byte a vertex/index count?"""
import glob
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, r"E:/Modding/JC3-Batmobile/Tools/scripts")
import rbm_geom as R  # noqa

D = r"E:/Modding/JC3-Batmobile/Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
files = sorted(glob.glob(D + "/*light*_lod*.rbm"))
print(f"{len(files)} light meshes")
rows = []
for f in files:
    raw = open(f, "rb").read()
    m = R.decode(raw)
    for b in m.blocks:
        if R.BLOCK_NAMES.get(b.type_hash) != "CarLight":
            continue
        rows.append((os.path.basename(f), len(b.pre_static), len(b.mid_static),
                     [vb.stride for vb in b.buffers], [vb.count for vb in b.buffers],
                     b.pre_static, b.mid_static, b.textures, b))
print("CarLight blocks:", len(rows))
print("pre_static sizes", Counter(r[1] for r in rows), "mid", Counter(r[2] for r in rows))
print("strides", Counter(tuple(r[3]) for r in rows))
pre = rows[0][5]
n = len(pre)
var = []
for i in range(n):
    vals = {r[5][i] for r in rows}
    if len(vals) > 1:
        var.append(i)
print(f"pre_static bytes differing across meshes: {len(var)} of {n}")
print("differing offsets:", var[:80])
# correlate: for each differing offset, group value by vertex count
by_count = defaultdict(set)
for r in rows:
    by_count[r[4][0]].add(bytes(r[5][i] for i in var))
for cnt, vals in sorted(by_count.items()):
    print(f"  vcount {cnt}: {len(vals)} distinct differing-byte patterns")
# print the first 160 bytes as hex/int of one block
print("pre_static[0:64]", pre[:64].hex())
u32 = np.frombuffer(pre, "<u4")
print("first 20 u32:", u32[:20].tolist())
f32 = np.frombuffer(pre, "<f4")
print("first 20 f32:", np.round(f32[:20], 4).tolist())
