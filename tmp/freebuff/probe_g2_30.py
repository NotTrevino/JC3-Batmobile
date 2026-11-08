"""G2-30 probe: what is inside the donor .physicsc, and can every polytope block be re-emitted?

Read-only. Uses jc3hkx.Packfile for the envelope, but re-derives the hull block
accounting here so the writer is not built on a single decoder's say-so.
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, r"E:/Modding/JC3-Batmobile/Tools/scripts")
import jc3hkx  # noqa: E402

FILES = {
    "donor": r"E:/Modding/JC3-Batmobile/Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc",
    "assembled": r"E:/Modding/JC3-Batmobile/Working/Assembled/sportsmuscle_true.physicsc",
}

for tag, path in FILES.items():
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    print(f"== {tag}: {os.path.basename(path)} {len(blob):,} B sha256={hashlib.sha256(blob).hexdigest()[:16]}")
    print("  sections:", [(s.name, s.data, s.end) for s in pf.section_list])
    print("  objects:", len(pf.objects), "classes:", sorted({o.cls for o in pf.objects}))
    print("  lf/gf/vf/ex:", pf.lf, pf.gf, pf.vf, pf.ex, "local", len(pf.local), "global", len(pf.global_))
    counts = {}
    for o in pf.objects:
        counts[o.cls] = counts.get(o.cls, 0) + 1
    print("  class counts:", counts)
    # where does the data section end (tail bytes after last object)?
    last = max(pf._order)
    print("  last object", hex(last), "extent", pf.extents[last], "data end", pf.lf,
          "tail bytes", pf.lf - (last + pf.extents[last]))
    tail = blob[pf.base + last + pf.extents[last]:pf.base + pf.lf]
    print("  tail distinct:", sorted(set(tail))[:5], len(tail))
    for o in pf.objects:
        if o.cls == jc3hkx.POLYTOPE:
            d = jc3hkx.decode_polytope(pf, o.offset)
            print(f"  hull @{o.offset:#08x} ext={d['extent']:5d} v={d['vertex_count']:3d} "
                  f"p={d['plane_count']:3d} unused={d['unused_planes']} i={d['index_count']:3d} "
                  f"face={d['face_bytes']:4d} pad={d['pad_bytes']:2d} r={d['convex_radius']:.4f} "
                  f"flags={d['shape_flags']:#010x} tag={d['shape_tag']:#x} "
                  f"box={[round(d['bounds']['max'][k]-d['bounds']['min'][k],4) for k in range(3)]}")
        elif o.cls in jc3hkx.COMPOUND_CLASSES:
            d = jc3hkx.decode_compound(pf, o.offset, o.cls)
            print(f"  {o.cls} @{o.offset:#08x} ext={d['extent']} inst={d['instance_count']} "
                  f"inline={d['instances_inline']} aabb={[round(d['aabb']['max'][k]-d['aabb']['min'][k],3) for k in range(3)]}")
        elif o.cls == "hknpExternMeshShape":
            g = jc3hkx.mesh_geometry(pf, o)
            print(f"  extern @{o.offset:#08x} verts={g['vertex_count']} "
                  f"aabb={[round(g['aabb'][1][k]-g['aabb'][0][k],3) for k in range(3)]} sections={g['sections']}")
        else:
            print(f"  {o.cls} @{o.offset:#08x} ext={pf.extents[o.offset]}")
