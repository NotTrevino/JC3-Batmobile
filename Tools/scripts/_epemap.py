"""EPE name->Sound-GUID map + bank chunk-type census."""
import re
from collections import Counter

x = open(r"E:\Modding\JC3-Batmobile\Working\Audio\serpente_epe.xml", encoding="utf-8").read()
# component blocks: <value name="name" ...>X</value> ... <value name="Sound" ...>BYTES</value>
pairs = []
for m in re.finditer(r'<value name="name" type="string">([^<]+)</value>(.*?)<value name="Sound" type="vec_byte">([0-9A-F,]+)</value>', x, re.S):
    nm, mid, sb = m.group(1), m.group(2), m.group(3)
    if len(mid) < 3000:
        pairs.append((nm, bytes(int(b, 16) for b in sb.split(",")).hex()))
print("named sounds:", len(pairs))
for nm, g in pairs:
    print("  %-32s %s" % (nm, g[:16] + "..."))
open(r"E:\Modding\JC3-Batmobile\Working\Audio\epe_soundmap.txt", "w").write("\n".join("%s %s" % p for p in pairs))

d = open(r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank", "rb").read()
c = Counter()
o = 0
while True:
    i = d.find(b"LIST", o)
    if i < 0: break
    tag = d[i+8:i+12]
    c[tag] += 1
    o = i + 4
print("LIST subtypes:", dict(c))
