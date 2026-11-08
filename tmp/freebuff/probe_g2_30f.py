"""G2-30 probe 6: where does the face table actually start?

For every hull, try every byte shift in the gap between the plane block and the index
block; report the shift (if any) under which 4-byte records `u16 first, u8 count, u8 min`
partition the index list exactly (firsts contiguous from 0, sum(count) == index_count).
"""
import sys

sys.path.insert(0, r"E:/Modding/JC3-Batmobile/Tools/scripts")
import jc3hkx  # noqa: E402

SRC = (r"E:/Modding/JC3-Batmobile/Builds/test-091/aaf/models/jc_vehicles/01_land/"
       r"v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
blob = open(SRC, "rb").read()
pf = jc3hkx.Packfile(blob)

shifts = {}
for o in pf.objects:
    if o.cls != jc3hkx.POLYTOPE:
        continue
    d = jc3hkx.decode_polytope(pf, o.offset)
    plane_at = o.offset + jc3hkx.POLYTOPE_HEAD + 16 * d["vertex_count"]
    pad = d["pad_bytes"]
    idx_at = o.offset + d["extent"] - pad - d["index_count"]
    gap_lo = plane_at + 16 * (d["plane_count"] + d["unused_planes"])
    hits = []
    for s in range(0, 49):
        start = gap_lo + s
        nbytes = idx_at - start
        if nbytes <= 0 or nbytes % 4:
            continue
        recs = [pf.u32(start + 4 * i) for i in range(nbytes // 4)]
        firsts = [r & 0xFFFF for r in recs]
        counts = [(r >> 16) & 0xFF for r in recs]
        if not firsts or firsts[0] != 0:
            continue
        if any(firsts[i] + counts[i] != firsts[i + 1] for i in range(len(firsts) - 1)):
            continue
        if firsts[-1] + counts[-1] != d["index_count"]:
            continue
        hits.append((s, len(recs)))
    shifts[o.offset] = hits
    print(f"@{o.offset:#08x} v={d['vertex_count']:3d} p={d['plane_count']:3d} "
          f"i={d['index_count']:3d} gap={idx_at - gap_lo:4d} -> {hits}")

print()
print("hulls:", len(shifts),
      "| exactly one hit:", sum(1 for h in shifts.values() if len(h) == 1),
      "| none:", sum(1 for h in shifts.values() if not h))
from collections import Counter  # noqa: E402
print("shift histogram:", Counter(h[0][0] for h in shifts.values() if h))
print("records vs planes:", Counter(
    (d["plane_count"], n)
    for o in pf.objects if o.cls == jc3hkx.POLYTOPE
    for h in [shifts[o.offset]] if h
    for n in [h[0][1]]
    for d in [jc3hkx.decode_polytope(pf, o.offset)]
).most_common(8))
