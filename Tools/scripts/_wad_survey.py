"""WAD-wide magic survey: every .wad (base+DLC), format + entry content histogram."""
import glob, os, struct, zlib
from collections import Counter

roots = [r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole",
         r"E:\Games\Batman - Arkham Knight\DLC"]
wads = []
for r in roots:
    wads += glob.glob(os.path.join(r, "**", "*.wad"), recursive=True)
print("wads:", len(wads))

def entries_of(p):
    d = open(p, "rb").read()
    magic = d[:4]
    if magic == b"WADZ":
        (sz,) = struct.unpack_from("<I", d, 4)
        raw = zlib.decompress(d[8:])
    elif magic == b"WWAD":
        raw = d
    else:
        return magic, -1, Counter({"??magic": 1})
    n = struct.unpack_from("<I", raw, 8)[0]
    if n > 1000000:
        return magic, -2, Counter({"??n": 1})
    kinds = Counter()
    o = 0x30
    for _ in range(n):
        if o + 20 > len(raw): break
        h, sz, nul, off, nul2 = struct.unpack_from("<IIIII", raw, o); o += 20
        sig = raw[off:off+4] if off + 4 <= len(raw) else b"????"
        kinds[bytes(sig)] += 1
    return magic, n, kinds

for p in sorted(wads):
    rel = p.split("Batman - Arkham Knight\\")[-1]
    try:
        magic, n, kinds = entries_of(p)
        flag = ""
        interesting = {k: v for k, v in kinds.items() if k not in (b"RIFF",)}
        if interesting: flag = "  <== NON-RIFF: %s" % interesting
        print("%-70s %s n=%d riff=%d%s" % (rel[-70:], magic, n, kinds.get(b"RIFF", 0), flag))
    except Exception as e:
        print("%-70s ERR %s" % (rel[-70:], str(e)[:70]))
