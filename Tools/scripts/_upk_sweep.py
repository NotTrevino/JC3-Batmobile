"""Sweep all .upk summaries (64B reads): compression flags + candidate ranking."""
import glob, os, struct

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
upks = glob.glob(os.path.join(CK, "*.upk"))
print("total:", len(upks))
uncomp, comp = [], []
veh_cands = []
for p in upks:
    with open(p, "rb") as f:
        head = f.read(64)
    if head[:4] != b"\xc1\x83\x2a\x9e":
        print("NON-UE3:", os.path.basename(p)); continue
    (ln,) = struct.unpack_from("<i", head, 12)
    o = 16 + ln
    flags = struct.unpack_from("<i", head, o)[0] & 0xFFFFFFFF
    sz = os.path.getsize(p)
    if flags & 0x02000000:
        comp.append((sz, os.path.basename(p)))
    else:
        uncomp.append((sz, os.path.basename(p)))
    n = os.path.basename(p).lower()
    if any(w in n for w in ["batmobile", "vehicle", "tank", "showcase", "mk2", "joker", "funhouse", "car", "bike", "bat_"]):
        veh_cands.append((sz, os.path.basename(p), bool(flags & 0x02000000)))
print("uncompressed:", len(uncomp), "compressed:", len(comp))
print("== uncompressed packs (greppable directly):")
for sz, n in sorted(uncomp, reverse=True)[:40]:
    print("  %10d %s" % (sz, n))
print("== vehicle-ish candidates:")
for sz, n, c in sorted(veh_cands, reverse=True):
    print("  %10d %-50s %s" % (sz, n, "COMPRESSED" if c else "plain"))
