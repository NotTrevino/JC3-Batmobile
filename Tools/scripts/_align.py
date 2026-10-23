"""GPCD full schema for vehicle classes + serial (4,b) scan; test b==N*8."""
import os, re, struct

g = open(os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole",
                      "GlobalPersistentCookerData.upk"), "rb").read()
props = {}
for m in re.finditer(rb"((?:BmGame\.RVehicleSimBatmobile|BmGame\.RVehicleBatmobile|Engine\.SVehicleSimBase|Engine\.SVehicleWheel|Engine\.SVehicle):([A-Za-z0-9_.]+))\x00(.{4})([A-Za-z]+Property)\x00(.{4})", g):
    cls = m.group(0).split(b":")[0].split(b".")[-1].decode()
    nm = m.group(2).decode()
    b = struct.unpack("<I", m.group(3))[0]
    t = m.group(4).decode()
    c = struct.unpack("<I", m.group(5))[0]
    props.setdefault(cls, []).append((nm, b, t, c))
for cls, lst in props.items():
    print("== %s (%d props)" % (cls, len(lst)))

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
img = d[:0x369] + s
eoff = 0x1C9F9

def serial(idx):
    o = eoff + idx * 72
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
    return img[off:off+size]

def scan45(data):
    out = []
    for m in re.finditer(b"\x04\x00", data):
        i = m.start()
        if i + 8 > len(data):
            continue
        b = struct.unpack_from("<H", data, i + 2)[0]
        v = struct.unpack_from("<f", data, i + 4)[0]
        out.append((b, v))
    return out

for idx, cls in [(5281, "RVehicleSimBatmobile"), (5280, "RVehicleBatmobile")]:
    data = serial(idx)
    hits = scan45(data)
    print("== exp[%d] (4,b) raw hits: %d" % (idx, len(hits)))
    byb = {}
    for b, v in hits:
        byb.setdefault(b, []).append(v)
    # test: GPCD c*8 present?
    for nm, b0, t, c in props.get(cls, []) + props.get("SVehicleSimBase", []):
        if t == "FloatProperty" and c * 8 in byb:
            print("  ALIGN %s c=%d -> b=%d vals=%s" % (nm, c, c*8, ["%g" % v for v in byb[c*8]][:3]))
json.dump({k: v for k, v in props.items()},
          open(os.path.join(A, "gpcd_vehicle_schema.json"), "w"), indent=1, default=str)
