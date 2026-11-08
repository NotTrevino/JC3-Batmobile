"""WWAD -> .wem extractor (no QuickBMS needed; format is a flat hash table).
Usage:
  python _wem_extract.py <wad> <hash8> <out.wem>        # single entry
  python _wem_extract.py <wad> --all <outdir>           # whole WAD
  python _wem_extract.py --shortlist                    # Batmobile-engine candidates
WAD path may be a name (SFX_3.wad), a full path, or INT_1.wad (English US).
"""
import json, os, struct, sys

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

def resolve(wad):
    if os.path.isfile(wad):
        return wad
    for c in [os.path.join(CK, "SFX", wad), os.path.join(CK, "English(US)", wad)]:
        if os.path.isfile(c):
            return c
    raise SystemExit("wad not found: " + wad)

def table(p):
    f = open(p, "rb")
    assert f.read(4) == b"WWAD", p
    f.seek(8); n, = struct.unpack("<I", f.read(4)); f.seek(0x30)
    return f, [struct.unpack("<IIIII", f.read(20)) for _ in range(n)]

def extract(wad, want, outdir):
    p = resolve(wad)
    f, tab = table(p)
    os.makedirs(outdir, exist_ok=True)
    got = 0
    for h, sz, nul, off, nul2 in tab:
        tag = "%08X" % h
        if want != "ALL" and tag != want.upper():
            continue
        f.seek(off)
        data = f.read(sz)
        assert data[:4] == b"RIFF" and data[8:12] == b"WAVE", (tag, data[:12])
        name = "%s_%s.wem" % (os.path.splitext(os.path.basename(p))[0], tag)
        open(os.path.join(outdir, name), "wb").write(data)
        print("wrote", name, sz)
        got += 1
    f.close()
    print("done:", got)

def shortlist():
    census = json.load(open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\sfx_census.json"))
    # engine-loop heuristic: multichannel, >=10 s, not a wave compilation
    cands = [r for r in census if isinstance(r["ch"], int) and r["ch"] >= 2
             and (r["dur_s"] or 0) >= 10 and r["extra_waves"] <= 3]
    # sequential-hash families (same asset, variant WADs) first
    fams, seen = {}, {}
    for r in census:
        seen.setdefault(r["hash"][:6], []).append(r["wad"])
    for r in sorted(cands, key=lambda r: -r["size"])[:40]:
        fam = "FAM+" if len(set(seen[r["hash"][:6]])) > 1 else "    "
        print("%s %-14s %08X %10d %dch %7.0fs xW%d %s" %
              (fam, r["wad"], int(r["hash"], 16), r["size"], r["ch"], r["dur_s"],
               r["extra_waves"], r["markers"]))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--shortlist":
        shortlist()
    elif len(a) == 3 and a[1] == "--all":
        extract(a[0], "ALL", a[2])
    elif len(a) == 3:
        extract(a[0], a[1], os.path.dirname(a[2]) or ".")
        # rename single to requested name
        import glob
        p = resolve(a[0])
        base = os.path.splitext(os.path.basename(p))[0] + "_" + a[1].upper() + ".wem"
        src = os.path.join(os.path.dirname(a[2]) or ".", base)
        if src != a[2]:
            os.replace(src, a[2])
    else:
        print(__doc__)
