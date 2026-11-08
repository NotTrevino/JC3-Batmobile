"""G2-30 probe 4: the donor's 54 hulls - part binding, extent, counts, box, centroid."""
import sys

sys.path.insert(0, r"E:/Modding/JustCause3/JC3-Batmobile/Tools/scripts")
import jc3hkx  # noqa: E402

SRC = (r"E:/Modding/JustCause3/JC3-Batmobile/Builds/test-091/aaf/models/jc_vehicles/01_land/"
       r"v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
EE = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
      "v0300_car_kensington_sportsmuscle_civilian_01.ee")
blob = open(SRC, "rb").read()
pf = jc3hkx.Packfile(blob)
parts = jc3hkx.load_part_names()

# shape offset -> (part name, which compound holds it)
owner = {}
for o in pf.objects:
    if o.cls in jc3hkx.COMPOUND_CLASSES:
        d = jc3hkx.decode_compound(pf, o.offset, o.cls)
        for inst in d["instances"]:
            if inst["shape"]:
                owner.setdefault(inst["shape"], []).append(
                    (hex(o.offset), inst["part_index"],
                     parts.get((EE, inst["part_index"])) if inst["part_index"] is not None else None))

print(f"{'offset':>10} {'ext':>5} {'v':>3} {'p':>3} {'i':>3} {'face':>4} {'pad':>3} {'r':>6} "
      f"{'box':>24} {'centroid':>22}  part / compound")
tot = 0
for o in pf.objects:
    if o.cls != jc3hkx.POLYTOPE:
        continue
    d = jc3hkx.decode_polytope(pf, o.offset)
    tot += d["extent"]
    b = d["bounds"]
    size = [b["max"][k] - b["min"][k] for k in range(3)]
    c = [(b["max"][k] + b["min"][k]) / 2 for k in range(3)]
    own = owner.get(o.offset, [("", None, None)])[0]
    print(f"{o.offset:#10x} {d['extent']:5d} {d['vertex_count']:3d} {d['plane_count']:3d} "
          f"{d['index_count']:3d} {d['face_bytes']:4d} {d['pad_bytes']:3d} {d['convex_radius']:6.4f} "
          f"{str([round(x, 3) for x in size]):>24} {str([round(x, 3) for x in c]):>22}  "
          f"{own[2]} / {own[0]}")
print("hull bytes total", tot)
