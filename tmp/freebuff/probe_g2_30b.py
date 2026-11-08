"""G2-30 probe 2: is the data section fully partitioned by typed objects?  Which hull is which part?"""
import sys

sys.path.insert(0, r"E:/Modding/JustCause3/JC3-Batmobile/Tools/scripts")
import jc3hkx  # noqa: E402

PATH = (r"E:/Modding/JustCause3/JC3-Batmobile/Builds/test-091/aaf/models/jc_vehicles/01_land/"
        r"v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
blob = open(PATH, "rb").read()
pf = jc3hkx.Packfile(blob)

order = sorted(pf._order)
gaps = []
for i, off in enumerate(order):
    end = off + pf.extents[off]
    nxt = order[i + 1] if i + 1 < len(order) else pf.lf
    if end != nxt:
        gaps.append((hex(off), pf._starts[off], pf.extents[off], hex(nxt), nxt - end))
print("objects:", len(order), "contiguous:", not gaps, "gaps:", len(gaps))
for g in gaps[:12]:
    print("  gap", g)
print("first object", hex(order[0]), "last", hex(order[-1]), "end", pf.lf)

parts = jc3hkx.load_part_names()
ee = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee"
for o in pf.objects:
    if o.cls not in jc3hkx.COMPOUND_CLASSES:
        continue
    d = jc3hkx.decode_compound(pf, o.offset, o.cls)
    print(f"\n{o.cls} @{o.offset:#08x} instances={d['instance_count']} inline={d['instances_inline']}")
    for inst in d["instances"]:
        pname = parts.get((ee, inst["part_index"])) if inst["part_index"] is not None else None
        box = inst["aabb"]
        size = ([round(box["max"][k] - box["min"][k], 4) for k in range(3)] if box else None)
        print(f"   inst {inst['index']:2d} shape @{inst['shape']:#08x} {inst['shape_class']:26s} "
              f"part {inst['part_index']} {pname} size {size} t={[round(v,3) for v in inst['translation'][:3]]}")
