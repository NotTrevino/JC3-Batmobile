"""GPCD property-offset hypothesis test: read floats at scraped offsets from Sim serial."""
import os, re, struct

g = open(os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole",
                      "GlobalPersistentCookerData.upk"), "rb").read()
# entries for RVehicleSimBatmobile: name + b + type + c
props = {}
for m in re.finditer(rb"BmGame\.RVehicleSimBatmobile:([A-Za-z0-9_.]+)\x00(.{4})([A-Za-z]+Property)\x00(.{4})", g):
    nm = m.group(1).decode()
    b = struct.unpack("<I", m.group(2))[0]
    t = m.group(3).decode()
    c = struct.unpack("<I", m.group(4))[0]
    props[nm] = (b, t, c)
for k in ["BattleModeThrottleSpeed", "VehicleTransmission.DifferentialRatio",
          "VehicleTransmission.GearRatios", "ScaleTopSpeed", "TimeAtTopSpeed",
          "BoostTorqueVSpeedCurve", "StandardTorqueVSpeedCurve", "BattleModeVSpeedCurve"]:
    print("%-42s %s" % (k, props.get(k, "ABSENT")))

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
img = d[:0x369] + s
o = 0x1C9F9 + 5281 * 72
arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, o + 20)
sim = img[off:off+size]
for k in ["BattleModeThrottleSpeed", "VehicleTransmission.DifferentialRatio", "ScaleTopSpeed", "TimeAtTopSpeed"]:
    b, t, c = props[k]
    print("%-42s off=0x%X f=%g u32=%d" % (k, c, struct.unpack_from("<f", sim, c)[0], struct.unpack_from("<I", sim, c)[0]))
