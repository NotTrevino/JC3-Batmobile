"""GPCD numbers x8 vs serial b-set per class: universal rule test."""
import os, re, struct
from collections import Counter

g = open(os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole",
                      "GlobalPersistentCookerData.upk"), "rb").read()
schema = {}
for m in re.finditer(rb"((?:BmGame\.RVehicleSimBatmobile|BmGame\.RVehicleBatmobile|Engine\.SVehicleSimBase|Engine\.SVehicleWheel|Engine\.SVehicle|Engine\.AkVehicleSoundInfo)(?:::[A-Za-z0-9_.]+|:([A-Za-z0-9_.]+)))\x00(.{4})([A-Za-z]+Property)\x00(.{4})", g):
    full = m.group(1).decode()
    nm = m.group(2).decode() if m.group(2) else full
    b = struct.unpack("<I", m.group(3))[0]
    t = m.group(4).decode()
    c = struct.unpack("<I", m.group(5))[0]
    cls = full.split(":")[0].split(".")[-1]
    schema.setdefault(cls, []).append((nm, b, t, c))

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

def bset(data):
    out = Counter()
    for mt in re.finditer(b"\x04\x00", data):
        i = mt.start()
        if i + 8 <= len(data):
            bb = struct.unpack_from("<H", data, i + 2)[0]
            out[bb] += 1
    return out

for idx, cls in [(5281, "RVehicleSimBatmobile"), (5280, "RVehicleBatmobile"), (5393, "SVehicleWheel")]:
    data = serial(idx)
    bs = bset(data)
    print("== exp[%d] float-headers=%d distinct-b=%d" % (idx, sum(bs.values()), len(bs)))
    hit = miss = 0
    for nm, b0, t, c in schema.get(cls, []):
        if t != "FloatProperty":
            continue
        if c * 8 in bs:
            hit += 1
        else:
            miss += 1
            if miss <= 8:
                print("   MISS %s c=%d (x8=%d)" % (nm, c, c*8))
    print("   floatprops: %d hit, %d miss" % (hit, miss))
json_out = {k: [[n, b, t, c] for n, b, t, c in v] for k, v in schema.items()}
import json
json.dump(json_out, open(os.path.join(A, "gpcd_schema.json"), "w"), indent=1)
