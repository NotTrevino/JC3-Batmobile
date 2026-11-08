"""G2-30 independent verification: read the written blobs from disk and re-derive the claims
with raw struct parsing (does not call hull_bytes / packfile_bytes / scale_hull)."""
import hashlib
import os
import struct
import sys

sys.path.insert(0, r"E:/Modding/JC3-Batmobile/Tools/scripts")
import jc3hkx as R  # reader + shape_checks only

W = r"E:/Modding/_JC3grab/hkx/write"
DON = R.DONOR
donor = open(DON, "rb").read()


def sections(blob):
    n = struct.unpack_from("<I", blob, 0x14)[0]
    out = []
    for i in range(n):
        b = 0x40 + i * 0x40
        name = blob[b:b + 19].split(b"\0")[0].decode()
        out.append((name, *struct.unpack_from("<7I", blob, b + 20)))
    return out


print("== section records and sizes (raw) ==")
for f in sorted(os.listdir(W)):
    if not f.endswith(".physicsc"):
        continue
    blob = open(os.path.join(W, f), "rb").read()
    secs = sections(blob)
    data = [s for s in secs if s[0] == "__data__"][0]
    ok = data[1] + data[7] == len(blob)
    print(f"  {f:28s} {len(blob):>8,} B  dataStart {data[1]:#x} + end {data[7]:,} == size: {ok}  "
          f"lf/gf/vf/ex {data[2]:,}/{data[3]:,}/{data[4]:,}/{data[7]:,}")

print("\n== invariant pass (reader, shape_checks) ==")
for f in sorted(os.listdir(W)):
    if not f.endswith(".physicsc"):
        continue
    pf = R.Packfile(open(os.path.join(W, f), "rb").read())
    counts, bad = R.shape_checks(pf)
    print(f"  {f:28s} hulls {counts['polytopes']:3d} convex {counts['convex']:3d} "
          f"blocks {counts['blocks']:3d} compounds {counts['compounds']:3d} "
          f"union_ok {counts['union_ok']:3d} violations {len(bad)}")

print("\n== the scaled wheel: is it exactly k x the donor, about its centre? ==")
leaf = 0xB5D0
base = R.Packfile(donor)
v0 = R.decode_polytope(base, leaf)["vertices"]
pf = R.Packfile(open(os.path.join(W, "scale_wheel.physicsc"), "rb").read())
v1 = R.decode_polytope(pf, leaf)["vertices"]
c = [0.0, 0.0, 0.0]
b = R.decode_polytope(base, leaf)["bounds"]
c = [(b["min"][k] + b["max"][k]) / 2 for k in range(3)]
ratios = {(round((v1[i][k] - c[k]) / (v0[i][k] - c[k]), 4) if abs(v0[i][k] - c[k]) > 1e-6 else None)
          for i in range(len(v0)) for k in range(3)}
ratios.discard(None)
print(f"  distinct per-vertex ratios: {sorted(ratios)}")
print(f"  expected 1.365/0.8225 = {1.365 / (b['max'][1] - b['min'][1]):.4f}")
d1 = R.decode_polytope(pf, leaf)
print(f"  box after {[round(d1['bounds']['max'][k] - d1['bounds']['min'][k], 4) for k in range(3)]} m, "
      f"radius {d1['convex_radius']:.6f}, indices identical: "
      f"{d1['indices'] == R.decode_polytope(base, leaf)['indices']}")

print("\n== does every compound that holds the wheel now cover it? (raw AABB test) ==")
for off in sorted({o.offset for o in pf.objects if o.cls in R.COMPOUND_CLASSES}):
    d = R.decode_compound(pf, off, pf._starts[off])
    hit = [i for i in d["instances"] if i["shape"] == leaf]
    if not hit:
        continue
    box = R.transform_aabb(d1["bounds"], hit[0]["basis"], hit[0]["translation"])
    lo = pf.vec4(off + 0x80)[:3]
    hi = pf.vec4(off + 0x90)[:3]
    inside = all(box["min"][k] >= lo[k] - 1e-3 and box["max"][k] <= hi[k] + 1e-3 for k in range(3))
    print(f"  compound {off:#x}: wheel box inside stored AABB: {inside}")

print("\n== the replaced hull: slot size changed, count of objects unchanged ==")
pfr = R.Packfile(open(os.path.join(W, "replace_hull.physicsc"), "rb").read())
print(f"  objects {len(pfr.objects)} (donor {len(base.objects)}), "
      f"hull@0x{leaf:x} extent {pfr.extents[leaf]} (donor {base.extents[leaf]}), "
      f"vertices {R.decode_polytope(pfr, leaf)['vertex_count']}, "
      f"fixups local {len(pfr.local)} global {len(pfr.global_)}")
print("  sha256:", hashlib.sha256(open(os.path.join(W, "scale_wheel.physicsc"), "rb").read()).hexdigest()[:16])
