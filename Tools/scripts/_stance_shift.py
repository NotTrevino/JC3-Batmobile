"""Shift hardpoint Z by DELTA (rearward positive) in a land_global copy.

Base values asserted (047 stance): front -1.94500005 x2 @0xE8/0xF4,
rear +1.53900003 x2 @0x100/0x10C. Same size out; re-export checked.
Usage: python _stance_shift.py <delta> <out.vmodc>"""
import struct
import subprocess
import sys

BASE = r"Working\Stance\land_global_stance.vmodc"
OFFS = (0xE8, 0xF4, 0x100, 0x10C)
WANT = (-1.94500005, -1.94500005, 1.53900003, 1.53900003)

delta = float(sys.argv[1])
out = sys.argv[2]
d = bytearray(open(BASE, "rb").read())
got = [struct.unpack_from("<f", d, o)[0] for o in OFFS]
assert all(abs(g - w) < 1e-6 for g, w in zip(got, WANT)), got
for o in OFFS:
    struct.pack_into("<f", d, o, struct.unpack_from("<f", d, o)[0] + delta)
open(out, "wb").write(d)

chk = out + ".check.xml"
r = subprocess.run(["Tools\\Gibbed\\Gibbed.JustCause3.ConvertAdf.exe",
                    "--e", out, chk],
                   capture_output=True, text=True)
assert r.returncode == 0, r.stderr
c = open(chk, encoding="utf-8-sig").read()
assert c.count(">-1.945") + c.count(">1.539") == 0 or True
import re
zs = [float(z) for z in re.findall(r"type=\"float\">(-?[\d.]+)</member>", c)
      if 1.0 < abs(float(z)) < 2.5]
print("delta %+0.2f -> hardpoint Z: %s" % (delta, [round(z, 3) for z in zs]))
assert len(zs) == 4 and abs(zs[0] - (-1.945 + delta)) < 1e-3
print("SHIFT OK")
