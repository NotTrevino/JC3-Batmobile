"""WEM census: for every SFX WWAD entry, parse RIFF header in place:
fmt codec/channels/rate, data size -> duration, LIST adtl marker names.
No full extraction. Also counts embedded RIFFs in the first 2 MB of each entry
(concatenated-bank detection)."""
import os, struct

wad_dir = os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole", "SFX")

def chunks(f, total):
    """yield (name, size, off) walking RIFF chunks from current pos; cap at total."""
    start = f.tell()
    out = []
    while f.tell() - start < total:
        h = f.read(8)
        if len(h) < 8:
            break
        cid, sz = h[:4], struct.unpack("<I", h[4:])[0]
        out.append((cid, sz, f.tell()))
        f.seek((sz + 1) & ~1, 1)
    return out

rows = []
for fn in sorted(os.listdir(wad_dir)):
    if not fn.lower().endswith(".wad"):
        continue
    p = os.path.join(wad_dir, fn)
    f = open(p, "rb")
    f.seek(8)
    n, = struct.unpack("<I", f.read(4))
    f.seek(0x30)
    tab = [struct.unpack("<IIIII", f.read(20)) for _ in range(n)]
    for h, sz, _nul, off, _nul2 in tab:
        f.seek(off)
        riff = f.read(12)
        if riff[:4] != b"RIFF" or riff[8:12] != b"WAVE":
            rows.append((fn, h, sz, "NOT-RIFF", "", "", "", "", ""))
            continue
        info = {}
        markers = []
        for cid, csz, coff in chunks(f, sz):
            if cid == b"fmt ":
                f.seek(coff)
                raw = f.read(min(csz, 24))
                if len(raw) >= 16:
                    codec, ch, rate = struct.unpack("<HHI", raw[:8])
                    br = struct.unpack("<I", raw[8:12])[0] if len(raw) >= 12 else 0
                    info.update(codec=codec, ch=ch, rate=rate, br=br)
            elif cid == b"data":
                info["data"] = csz
            elif cid == b"LIST":
                f.seek(coff)
                ltype = f.read(4)
                if ltype == b"adtl":
                    end = coff + 4 + csz
                    names = []
                    while f.tell() + 8 <= end:
                        lab = f.read(8)
                        if len(lab) < 8:
                            break
                        lid, lsz = struct.unpack("<II", lab)
                        txt = f.read((lsz + 1) & ~1)
                        try:
                            names.append(txt.split(b"\x00")[0].decode())
                        except Exception:
                            pass
                    markers = names
        # embedded RIFF count in first 2MB
        f.seek(off)
        head = f.read(min(sz, 2 << 20))
        extra = head.count(b"WAVE") - 1
        codec = info.get("codec", "?")
        ch = info.get("ch", "?")
        rate = info.get("rate", "?")
        dur = (info["data"] / (info["br"] / 8) if info.get("br") else 0) if isinstance(info.get("br"), int) else 0
        rows.append((fn, h, sz, codec, ch, rate,
                     round(dur, 1) if dur and dur < 1e6 else 0,
                     extra, "|".join(markers[:4])))
    f.close()

print("total entries:", len(rows))
print("%-14s %8s %10s %-6s %3s %7s %9s %6s markers" % ("wad", "hash", "size", "codec", "ch", "rate", "dur_s", "xWAVE"))
for r in sorted(rows, key=lambda r: -r[2])[:60]:
    print("%-14s %08X %10d %-6s %-3s %-7s %-9s %-6s %s" % r)
import json
json.dump([{"wad": r[0], "hash": "%08X" % r[1], "size": r[2], "codec": r[3], "ch": r[4],
            "rate": r[5], "dur_s": r[6], "extra_waves": r[7], "markers": r[8]} for r in rows],
          open(r"E:\Modding\JC3-Batmobile\Working\Audio\sfx_census.json", "w"), indent=1)
print("wrote Working/Audio/sfx_census.json")
