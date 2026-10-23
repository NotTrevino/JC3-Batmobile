"""UE3 summary parse + name-table walk with sanity checks (uncompressed pkgs only)."""
import struct, sys

def parse_summary(d):
    assert d[:4] == b"\xc1\x83\x2a\x9e", d[:4].hex()
    vlo, vhi = struct.unpack_from("<HH", d, 4)
    (hdr,) = struct.unpack_from("<I", d, 8)
    o = 12
    (ln,) = struct.unpack_from("<i", d, o); o += 4
    folder = d[o:o+ln]; o += ln
    flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", d, o)
    return dict(vlo=vlo, vhi=vhi, hdr=hdr, folder=folder, flags=flags & 0xFFFFFFFF,
                nc=nc, noff=noff, ec=ec, eoff=eoff, ic=ic, ioff=ioff, doff=doff)

def walk_names(d, nc, noff):
    names, o = [], noff
    for i in range(nc):
        if o + 4 > len(d):
            return names, "EOF@%d" % i
        (ln,) = struct.unpack_from("<i", d, o)
        if not (0 < ln < 512 or -512 < ln < 0):
            return names, "badlen %d @entry %d off 0x%X" % (ln, i, o)
        o += 4
        if ln > 0:
            s = d[o:o+ln]; o += ln
            names.append(s[:-1].decode("ascii", "replace") if s.endswith(b"\x00") else s.decode("ascii", "replace"))
        else:
            names.append(d[o:o+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); o += (-ln)*2
        # trailer: try skips, accept first that yields sane next len (or EOF on last)
        if i == nc - 1:
            break
        advanced = False
        for skip in (4, 8, 12, 0):
            if o + skip + 4 > len(d):
                continue
            (nxt,) = struct.unpack_from("<i", d, o + skip)
            if 0 < nxt < 512 or -512 < nxt < 0:
                o += skip; advanced = True; break
        if not advanced:
            return names, "nostride @entry %d off 0x%X tail=%s" % (i, o, d[o:o+16].hex(" "))
    return names, "ok"

import os
ck = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
for t in sys.argv[1:] or ["Film_B1.upk"]:
    d = open(os.path.join(ck, t), "rb").read()
    try:
        s = parse_summary(d)
    except Exception as e:
        print(t, "HDR-FAIL", e); continue
    print(t, "flags=0x%X compressed=%s names=%d@0x%X exports=%d@0x%X imports=%d@0x%X" % (
        s["flags"], bool(s["flags"] & 0x02000000), s["nc"], s["noff"], s["ec"], s["eoff"], s["ic"], s["ioff"]))
    if s["nc"] > 0 and s["noff"] < len(d):
        names, st = walk_names(d, min(s["nc"], 200000), s["noff"])
        print("   walked:", len(names), st)
        if names:
            print("   first:", names[:8])
