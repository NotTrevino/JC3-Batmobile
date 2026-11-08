"""G2-30 probe 3: can the data section be re-laid-out with every offset remapped?

Decisive experiment: insert 16 filler bytes at data offset 0, so EVERY object, every
array, every fixup and every table shifts by +16.  Rebuild the tables and the section
record, re-read the result with jc3hkx, and compare the decoded object graph with the
original.  Read-only on the source; writes only to _JC3grab/hkx/write/.
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, r"E:/Modding/JC3-Batmobile/Tools/scripts")
import jc3hkx  # noqa: E402

SRC = (r"E:/Modding/JC3-Batmobile/Builds/test-091/aaf/models/jc_vehicles/01_land/"
       r"v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
OUTDIR = r"E:/Modding/_JC3grab/hkx/write"
os.makedirs(OUTDIR, exist_ok=True)

blob = open(SRC, "rb").read()
pf = jc3hkx.Packfile(blob)
DELTA = 16
objs = sorted(pf._order)


def owner(rel):
    lo, hi = 0, len(objs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if objs[mid] <= rel:
            lo = mid + 1
        else:
            hi = mid - 1
    if hi < 0:
        return None
    o = objs[hi]
    return o if rel < o + pf.extents[o] else None


def remap(rel):
    if rel == 0:
        return DELTA
    o = owner(rel)
    if o is None:
        raise SystemExit(f"target {rel:#x} is not inside an object")
    return o + DELTA + (rel - o)


body = bytearray(pf.blob[pf.base:pf.base + pf.ex])   # objects + all four tables
new = bytearray(b"\x7f" * DELTA) + body              # shift everything by DELTA
lf, gf, vf, ex = pf.lf + DELTA, pf.gf + DELTA, pf.vf + DELTA, pf.ex + DELTA

local = [(remap(f), remap(t)) for f, t in pf.local]
glob = [(remap(f), s, remap(t)) for f, s, t in pf.global_]
cls_off = {nm: rel for rel, _h, nm in pf.classnames}
virt = [(remap(o), 0, cls_off[cls]) for o, cls in pf.virtual]
assert all(f < lf for f, _ in local)
assert all(f < gf for f, _, _ in glob)
assert all(f < vf for f, _, _ in virt)

# rebuild the three fixup tables in their (shifted) slots, then the pointer values
new[lf:gf] = b"\xff" * (gf - lf)
new[gf:vf] = b"\xff" * (vf - gf)
new[vf:ex] = b"\xff" * (ex - vf)
for i, (f, t) in enumerate(local):
    struct.pack_into("<2I", new, lf + 8 * i, f, t)
for i, (f, s, t) in enumerate(glob):
    struct.pack_into("<3I", new, gf + 12 * i, f, s, t)
for i, (f, s, c) in enumerate(virt):
    struct.pack_into("<3I", new, vf + 12 * i, f, s, c)
for f, t in local:
    struct.pack_into("<I", new, f, t)
for f, _s, t in glob:
    struct.pack_into("<I", new, f, t)

out = bytearray(blob[:pf.base])
struct.pack_into("<7I", out, 0x40 + 0x40 * 2 + 20, pf.base, lf, gf, vf, ex, ex, len(new))
out += new

dst = os.path.join(OUTDIR, "probe_shift16.physicsc")
open(dst, "wb").write(out)
print(f"wrote {dst} {len(out):,} B (orig {len(blob):,})")

pf2 = jc3hkx.Packfile(open(dst, "rb").read())
print("objects", len(pf2.objects), "| class list equal:",
      [o.cls for o in pf.objects] == [o.cls for o in pf2.objects])
counts, bad = jc3hkx.shape_checks(pf2)
print("invariants:", counts)
print("violations:", len(bad))
for b in bad[:5]:
    print("  ", b)


def sig(pf):
    rows = []
    for o in pf.objects:
        if o.cls == jc3hkx.POLYTOPE:
            d = jc3hkx.decode_polytope(pf, o.offset)
            rows.append((o.cls, d["vertex_count"], d["plane_count"], d["index_count"],
                         hashlib.sha256(repr([tuple(v) for v in d["vertices"]]).encode()).hexdigest()[:12],
                         hashlib.sha256(repr(d["planes"]).encode()).hexdigest()[:12],
                         tuple(d["indices"][:6])))
        elif o.cls in jc3hkx.COMPOUND_CLASSES:
            d = jc3hkx.decode_compound(pf, o.offset, o.cls)
            rows.append((o.cls, d["instance_count"],
                         tuple((i["shape_class"], i["part_index"],
                                tuple(round(v, 6) for v in i["translation"]))
                               for i in d["instances"])))
        else:
            rows.append((o.cls, pf.extents[o.offset]))
    return rows


a, b = sig(pf), sig(pf2)
print("decoded graph identical:", a == b)
if a != b:
    for x, y in zip(a, b):
        if x != y:
            print("  orig", x, "\n  new ", y)
            break
