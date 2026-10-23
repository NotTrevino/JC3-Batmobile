"""Probe: per-component bboxes of the wheel-material faces in quadrant (1,0)."""
import sys
from collections import Counter

sys.path.insert(0, "Tools/scripts")
from psk2rbm import read_pskx  # noqa: E402

P, W, F, mats = read_pskx(r"Playable_Batmobile_SF\SkeletalMesh3\Batmobile_V2.pskx")
sel = [i for i in range(len(F)) if int(F["m"][i]) in (0, 9, 13)]
pos = P[W["p"].astype(int)]
cen = pos[F["w"][sel]].mean(1)
take = [sel[i] for i in range(len(sel)) if cen[i][0] > 0 and cen[i][1] < 0]
print("quadrant faces:", len(take))

tri_w = F["w"][take].astype(int)
pt = W["p"][tri_w]
parent = list(range(len(take)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


edge = {}
for i in range(len(take)):
    a, b, c = sorted(int(x) for x in pt[i])
    for e in ((a, b), (b, c), (a, c)):
        if e in edge:
            ra, rb = find(i), find(edge[e])
            if ra != rb:
                parent[ra] = rb
        else:
            edge[e] = i
sizes = Counter(find(i) for i in range(len(take)))
for r, n in sorted(sizes.items(), key=lambda kv: -kv[1])[:10]:
    pts = pos[[int(W["p"][w]) for t in [take[i] for i in range(len(take))
                                        if find(i) == r] for w in F["w"][t]]]
    print("n=%5d  X %7.1f..%7.1f  Y %8.1f..%7.1f  Z %6.1f..%6.1f" % (
        n, pts[:, 0].min(), pts[:, 0].max(),
        pts[:, 1].min(), pts[:, 1].max(), pts[:, 2].min(), pts[:, 2].max()))
