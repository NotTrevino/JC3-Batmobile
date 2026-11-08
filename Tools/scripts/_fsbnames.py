"""FSB5 nametable: offset table + blob -> all 649 names; find Serpente streams."""
import struct

p = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()
f5 = d.find(b"FSB5")
ver, n, shdr, ntl = struct.unpack_from("<IIII", d, f5 + 4)
t0 = f5 + 60 + shdr
blob = t0 + 4 * n
names = []
o = blob
while len(names) < n and o < len(d):
    e = d.find(b"\x00", o)
    frag = d[o:e]
    try:
        names.append(frag.decode())
    except Exception:
        break
    o = e + 1
print("names:", len(names))
open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3bank\fsb_names.txt", "w").write("\n".join(names))
for i, nm in enumerate(names):
    lo = nm.lower()
    if any(w in lo for w in ["kensington", "sportsmuscle", "serpente", "posh", "mu10", "batmobile", "nitro", "turbo"]):
        print("HIT %d: %s" % (i, nm))
# engine-ish across all cars (start/loop/rpm)
eng = [nm for nm in names if any(w in nm.lower() for w in ["_start", "rpm", "_loop", "idle", "engine"])]
print("engine-ish total:", len(eng))
