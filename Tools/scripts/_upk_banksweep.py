"""Sweep every .upk for bank/event magic + batmobile refs (raw bytes; compressed pkgs hide)."""
import glob, os, re

ck = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
upks = glob.glob(os.path.join(ck, "*.upk"))
print("total upk:", len(upks))
hits_magic = []
hits_bm = []
for p in upks:
    with open(p, "rb") as f:
        head = f.read(1 << 20)
    name = os.path.basename(p)
    magics = [m for m in [b"BKHD", b"BKPK", b"HIRC", b"STID", b"AKEvent", b"AkBank"]
              if m in head]
    if magics:
        hits_magic.append((name, magics, os.path.getsize(p)))
    if b"atmobile" in head or b"ATMOBILE" in head:
        hits_bm.append(name)
print("== upk with bank/event magic in first MB:", len(hits_magic))
for n, m, s in sorted(hits_magic, key=lambda x: -x[2])[:40]:
    print("  %10d %-60s %s" % (s, n, [x.decode() for x in m]))
print("== upk with raw 'atmobile' in first MB:", len(hits_bm))
for n in hits_bm[:40]:
    print("  ", n)

# EDF036D6.bnk: all strings + vehicle/batmobile filter
d = open(os.path.join(ck, "SFX", "EDF036D6.bnk"), "rb").read()
strs = sorted({s.decode() for s in re.findall(rb"[A-Za-z][A-Za-z0-9_]{5,}", d)})
print("== EDF036D6 nameish strings:", len(strs))
veh = [s for s in strs if any(w in s.lower() for w in ["batmobile", "vehicle", "car", "engine", "exhaust", "boost", "afterburn", "turbine", "tire", "skid"])]
print("vehicle-ish:", veh)
print("sample:", strs[:30])
