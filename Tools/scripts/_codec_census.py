"""Codec census over all packs: first-chunk first-block head -> zlib vs LZO."""
import glob, os, struct

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
TAG = b"\xc1\x83\x2a\x9e"
rows = []
for p in glob.glob(os.path.join(CK, "*.upk")):
    try:
        with open(p, "rb") as f:
            head = f.read(4096)
        if head[:4] != TAG:
            rows.append((p, 0, "nonupk")); continue
        (ln,) = struct.unpack_from("<i", head, 12)
        o = 16 + ln
        flags, nc, noff = struct.unpack_from("<iii", head, o)
        with open(p, "rb") as f:
            f.seek(noff)
            region = f.read(1 << 20)
        i = region.find(TAG)
        if i < 0:
            rows.append((p, os.path.getsize(p), "nochunks(ns=%d)" % nc)); continue
        x, tc, tu = struct.unpack_from("<III", region, i + 4)
        q = i + 16
        su = 0
        while su < tu and q + 8 <= len(region):
            bc, bu = struct.unpack_from("<II", region, q); q += 8; su += bu
            if bu == 0 or bc == 0 or len(str([(bc, bu)])) > 0 and (bc > len(region) or bu > (1 << 26)):
                break
        blk = region[q:q+2]
        codec = "zlib" if blk in (b"\x78\x9c", b"\x78\x01", b"\x78\xda") else "LZO?" if blk else "?"
        rows.append((p, os.path.getsize(p), "%s MB=%d" % (codec, os.path.getsize(p) >> 20)))
    except Exception as e:
        rows.append((p, 0, "ERR " + str(e)[:60]))
zl = sorted(((s, p) for p, s, c in rows if c.startswith("zlib")), reverse=True)
lz = sorted(((s, p) for p, s, c in rows if c.startswith("LZO")), reverse=True)
print("zlib packs:", len(zl), " LZO packs:", len(lz))
open(r"E:\Modding\JC3-Batmobile\Working\Audio\zlib_packs.txt", "w").write(
    "\n".join("%d %s" % (s, os.path.basename(p)) for s, p in zl))
open(r"E:\Modding\JC3-Batmobile\Working\Audio\lzo_packs.txt", "w").write(
    "\n".join("%d %s" % (s, os.path.basename(p)) for s, p in lz))
print("== biggest zlib packs:")
for s, p in zl[:25]:
    print("  %10d %s" % (s, os.path.basename(p)))
print("== biggest LZO packs:")
for s, p in lz[:15]:
    print("  %10d %s" % (s, os.path.basename(p)))
others = [(p, s, c) for p, s, c in rows if not (c.startswith("zlib") or c.startswith("LZO"))]
print("other:", len(others), [os.path.basename(p) for p, _, _ in others][:10])
