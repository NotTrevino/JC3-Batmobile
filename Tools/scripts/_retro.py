"""Retrospective: hashlist names for all shortlist suspects + WAD-vs-bank media overlap."""
import json, os, struct

pairs = {l.split("\t")[0].strip().upper(): l.split("\t")[1].strip()
         for l in open(r"E:\Modding\JC3-Batmobile\Research\Arkham Knight SFX\Arkham Knight SFX\batman_bnk\bnk\hashlist.txt",
                       encoding="utf-8", errors="replace").read().splitlines() if "\t" in l}
census = {r["hash"]: r for r in json.load(open(r"E:\Modding\JC3-Batmobile\Working\Audio\sfx_census.json"))}
rank = json.load(open(r"E:\Modding\JC3-Batmobile\Working\Audio\ranking.json"))

print("== shortlist retrospective (spectral rank + hashlist name)")
for r in rank[:16]:
    h = r["tag"].split("_")[-1]
    print("  stat=%.3f %-22s = %s" % (r["stat"], r["tag"], pairs.get(h, "(unnamed)")))

for h in ["EDF036D6", "07896F60", "07896F61", "07896F63", "E01EC5A5", "2043EABE",
          "CE2F6B57", "CE2F6B54", "CD2F69E2", "CD2F69E1", "75FA4BAC", "5946F94F",
          "5646F4F5", "10AF2680", "CC2F6871", "CB591E44", "A284435E", "466D1B0B",
          "EC2FD42B", "E7BD5AD0", "AA84F8A2", "A1109037", "2043EABD", "26173CE6"]:
    print("  %s = %s" % (h, pairs.get(h, "(unnamed)")))

# WAD hashes vs BML_Engine DIDX/HIRC media IDs
d = open(r"E:\Modding\JC3-Batmobile\Working\Audio\bank_BML_Engine.bank", "rb").read()
di = d.find(b"DIDX")
(dsz,) = struct.unpack_from("<I", d, di + 4)
didx = set()
for k in range(dsz // 12):
    mid, _, _ = struct.unpack_from("<III", d, di + 8 + 12 * k)
    didx.add("%08X" % mid)
wadhashes = set(census)
print("DIDX-in-WAD-hashes:", len(didx & wadhashes), sorted(didx & wadhashes)[:10])
hi = d.find(b"HIRC")
o = hi + 8
(n,) = struct.unpack_from("<I", d, o); o += 4
hirc_ids = set()
for _ in range(n):
    t = d[o]; (sz,) = struct.unpack_from("<I", d, o + 1); body = d[o+5:o+5+sz]
    for k in range(len(body) - 3):
        hirc_ids.add("%08X" % struct.unpack_from("<I", body, k)[0])
    o += 5 + sz
print("HIRC-u32-in-WAD-hashes:", len(hirc_ids & wadhashes), sorted(hirc_ids & wadhashes)[:15])
print("HIRC-u32-in-hashlist-names:", sum(1 for h in hirc_ids if h in pairs))
