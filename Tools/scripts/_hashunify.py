"""Hashlist unification: verify FNV-1(lower) reproduces WAD hashes; extract Turbo+Batmobile."""
import json, os, struct, subprocess

def fnv1(s):
    h = 0x811C9DC5
    for b in s.encode():
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ b
    return h

pairs = [(l.split("\t")[0].strip().upper(), l.split("\t")[1].strip())
         for l in open(r"E:\Modding\JustCause3\JC3-Batmobile\Research\Arkham Knight SFX\Arkham Knight SFX\batman_bnk\bnk\hashlist.txt",
                       encoding="utf-8", errors="replace").read().splitlines() if "\t" in l]
print("pairs:", len(pairs))
ok = tot = 0
for h, n in pairs:
    tot += 1
    if "%08X" % fnv1(n.lower()) == h:
        ok += 1
print("FNV-1(lower) reproduces hashlist: %d/%d" % (ok, tot))

# which hashlist names are SFX WAD entries vs bank-only?
census = {r["hash"]: r for r in json.load(open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\sfx_census.json"))}
bml = [(h, n) for h, n in pairs if n.startswith("BML_") or n.startswith("VEH_") or "Batmobile" in n]
print("== BML/VEH/Batmobile names: in-SFX-WAD vs bank-only")
for h, n in sorted(bml, key=lambda x: x[1]):
    c = census.get(h)
    print("  %-8s %-28s %s" % ("WEM" if c else "BANK?", h, n))

# extract Turbo + Batmobile WEMs
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\SFX"
outd = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\hashid"
os.makedirs(outd, exist_ok=True)
CLI = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\vgmstream-win64\vgmstream-cli.exe"
for h, wad in [("EC2FD42B", "SFX_1.wad"), ("E7BD5AD0", "SFX_1.wad")]:
    f = open(os.path.join(CK, wad), "rb")
    assert f.read(4) == b"WWAD"
    f.seek(8); n = struct.unpack("<I", f.read(4))[0]; f.seek(0x30)
    for _ in range(n):
        hh, sz, nul, off, nul2 = struct.unpack("<IIIII", f.read(20))
        if "%08X" % hh == h:
            f.seek(off)
            wem = os.path.join(outd, "%s.wem" % h)
            open(wem, "wb").write(f.read(sz))
            print("extracted", h, sz)
            r = subprocess.run([CLI, "-o", os.path.join(outd, h + ".wav"), wem], capture_output=True)
            print("  decode rc:", r.returncode)
            break
    f.close()
