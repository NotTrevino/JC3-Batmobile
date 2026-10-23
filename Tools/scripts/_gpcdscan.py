"""Scan the BmAK GlobalPersistentCookerData.upk for property names and show the
surrounding bytes as text. Decides whether GPCD stores *named* default values
(e.g. 'ChassisMass=1500.0') or just a name table.

Usage: python _gpcdscan.py <gpcd.upk> name1 name2 ...
"""
import re
import sys

path = sys.argv[1]
names = sys.argv[2:]
data = open(path, "rb").read()
print("gpcd size", len(data))

for nm in names:
    pat = re.compile(nm.encode("ascii"))
    hits = [m.start() for m in pat.finditer(data)]
    print("\n=== %s : %d hit(s)" % (nm, len(hits)))
    for off in hits[:4]:
        lo = max(0, off - 80)
        hi = min(len(data), off + 140)
        chunk = data[lo:hi]
        txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print("  @%d (0x%x): %s" % (off, off, txt))
