"""UE3 property-stream walk for vehicle tuning exports (generic tag decode)."""
import os, struct, sys

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
d = open(os.path.join(CK, "Playable_Batmobile_SF.upk"), "rb").read()
s = open(os.path.join(A, "bm_stream.bin"), "rb").read()
names = open(os.path.join(A, "bm_names.txt")).read().splitlines()
img = d[:0x369] + s
(ln,) = struct.unpack_from("<i", img, 12)
o = 16 + ln
flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", img, o)
STR = (doff - eoff) // ec

def serial(idx):
    oo = eoff + idx * STR
    arch, ef, lo, hi2, size, off = struct.unpack_from("<IIIIII", img, oo + 20)
    return img[off:off+size]

def walk_props(buf, depth=0):
    o = 0
    out = []
    while o + 24 <= len(buf):
        ni, nn = struct.unpack_from("<ii", buf, o); o += 8
        if not (0 <= ni < len(names)):
            break
        if names[ni] == "None":
            break
        ti, tn = struct.unpack_from("<ii", buf, o); o += 8
        (sz,) = struct.unpack_from("<i", buf, o); o += 4
        (ai,) = struct.unpack_from("<i", buf, o); o += 4
        t = names[ti] if 0 <= ti < len(names) else "?%d" % ti
        val = buf[o:o+sz]
        tag = ""
        if t in ("IntProperty", "FloatProperty") and sz == 4:
            tag = ("int=%d" % struct.unpack("<i", val)[0]) if t[0] == "I" else ("float=%g" % struct.unpack("<f", val)[0])
        elif t == "BoolProperty" and sz == 0:
            tag = "bool=%s" % bool(ai)
        elif t == "StrProperty":
            tag = "str=" + val[:-1].decode(errors="replace")
        elif t == "NameProperty" and sz == 8:
            vi, _ = struct.unpack("<ii", val)
            tag = "name=" + (names[vi] if 0 <= vi < len(names) else str(vi))
        elif t == "ObjectProperty" and sz == 4:
            tag = "objref=%d" % struct.unpack("<i", val)[0]
        out.append((names[ni], t, tag, sz))
        o += sz
    return out

want = {"RVehicle": 5280, "Sim": 5281, "Booster": 5110, "WheelFL": 5393,
        "VehSoundInfo": 146, "JumpBurstRPM": 25}
for label, idx in want.items():
    data = serial(idx)
    print("== exp[%d] %s (%d B): %d props" % (idx, label, len(data), 0))
    for nm, t, tag, sz in walk_props(data):
        if t in ("IntProperty", "FloatProperty", "BoolProperty", "StrProperty", "NameProperty") or \
           any(w in nm.lower() for w in ["speed", "rpm", "torque", "gear", "mass", "accel", "boost",
               "throttle", "drag", "grip", "steer", "suspens", "brake", "power", "curve",
               "velocity", "radius", "width", "ratio", "force", "damp", "/max", "min", "max"]):
            print("   %-42s %-16s %s" % (nm, t, tag))
