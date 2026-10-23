"""Sounds' fileID fields vs WAD hashes: streamed-media references in BML_Engine?"""
import json, os, struct

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
d = open(os.path.join(A, "bank_BML_Engine.bank"), "rb").read()
hi = d.find(b"HIRC"); o = hi + 8
(n,) = struct.unpack_from("<I", d, o); o += 4
sounds = {}
for _ in range(n):
    t = d[o]; (sz,) = struct.unpack_from("<I", d, o + 1); body = d[o+5:o+5+sz]
    if t == 2:
        sid, = struct.unpack_from("<I", body, 0)
        sounds[sid] = body
    o += 5 + sz
census = json.load(open(os.path.join(A, "sfx_census.json")))
wadhashes = {"%08X" % int(r["hash"], 16) for r in census}
pairs = {}
for l in open(r"E:\Modding\JC3-Batmobile\Research\Arkham Knight SFX\Arkham Knight SFX\batman_bnk\bnk\hashlist.txt",
              encoding="utf-8", errors="replace").read().splitlines():
    if "\t" in l:
        h, nm = l.split("\t", 1)
        pairs[h.strip().upper()] = nm.strip()
print("sounds:", len(sounds), "wadhashes:", len(wadhashes))
for sid, body in sorted(sounds.items()):
    u32s = struct.unpack("<%dI" % (len(body)//4), body[:len(body)//4*4])
    # Wwise SFX voice: source/file id typically at a fixed spot; test ALL u32s
    hits = [("0x%X=%s" % (u, pairs.get("%08X" % u, "?WAD?" if "%08X" % u in wadhashes else ""))) for u in u32s
            if "%08X" % u in wadhashes or "%08X" % u in pairs and pairs["%08X" % u].startswith(("BML_", "VEH_", "AMB_", "SEQ_"))]
    if hits:
        print("snd %08X -> %s" % (sid, hits))
print("done")
