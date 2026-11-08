"""Parse .ee.fmod_guids: ver u32, bankcount u16, bank names, then u16 count + 16B GUIDs."""
import os, struct
p = (r"E:\Modding\JustCause3\JC3-Batmobile\Builds\test-003\aaf\editor\entities\jc_vehicles\01_land"
     r"\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee.fmod_guids")
d = open(p, "rb").read()
ver, nb = struct.unpack_from("<IH", d, 0)
o = 6
banks = []
for _ in range(nb):
    (ln,) = struct.unpack_from("<H", d, o); o += 2
    banks.append(d[o:o+ln].decode()); o += ln
print("ver", ver, "banks", banks)
(ne,) = struct.unpack_from("<H", d, o); o += 2
print("events:", ne)
os.makedirs(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio", exist_ok=True)
out = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\serpente_fmod_events.txt", "w")
for i in range(ne):
    g = d[o:o+16]; o += 16
    s = "{%s-%s-%s-%s-%s}" % (g[:4].hex(), g[4:6].hex(), g[6:8].hex(), g[8:10].hex(), g[10:].hex())
    print("  ", s)
    out.write(s + "\n")
print("end 0x%X / 0x%X" % (o, len(d)))
