"""GRAB everything Batmobile: hashlist-name rule x WAD tables + all bank DIDX media.
Rules in CHECKLIST.md. Output: Working/Audio/grab/<tag>.wem + grab_manifest.json.
Usage: python _grab_all.py
"""
import glob, hashlib, json, os, struct

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

def inc_name(n):
    lo = n.lower()
    if lo.startswith("dlg_"):
        return False
    return ("batmobile" in lo or lo.startswith("bml_") or "veh_" in lo and "batmobile" in lo
            or (lo.startswith("seq_") and "batmobile" in lo)
            or (lo.startswith("ch") and "batmobile" in lo)
            or (lo.startswith("obj_") and "batmobile" in lo)
            or (lo.startswith("pso_") and "batmobile" in lo))

pairs = [(l.split("\t")[0].strip().upper(), l.split("\t")[1].strip())
         for l in open(r"E:\Modding\JC3-Batmobile\Research\Arkham Knight SFX\Arkham Knight SFX\batman_bnk\bnk\hashlist.txt",
                       encoding="utf-8", errors="replace").read().splitlines() if "\t" in l]
want = {h: n for h, n in pairs if inc_name(n)}
print("wanted hashes:", len(want))

# WAD tables: SFX (census) + INT_1..8 (scan headers)
loc = {}  # hash -> (wadpath, off, sz)
census = json.load(open(os.path.join(A, "sfx_census.json")))
for r in census:
    h = "%08X" % int(r["hash"], 16)
    if h in want:
        loc[h] = (os.path.join(CK, "SFX", r["wad"]), None, None)
print("wanted in SFX:", len([h for h in want if h in loc]))
intdir = os.path.join(CK, "English(US)")
for iw in sorted(glob.glob(os.path.join(intdir, "INT_[12345678].wad"))):
    f = open(iw, "rb")
    assert f.read(4) == b"WWAD", iw
    f.seek(8); n = struct.unpack("<I", f.read(4))[0]; f.seek(0x30)
    for _ in range(n):
        h, sz, nul, off, nul2 = struct.unpack("<IIIII", f.read(20))
        tag = "%08X" % h
        if tag in want and tag not in loc:
            loc[tag] = (iw, off, sz)
    f.close()
print("wanted located total:", len(loc), "/", len(want))
missing = sorted(h for h in want if h not in loc)
print("missing (bank-only names, expected):", len(missing))

outd = os.path.join(A, "grab")
os.makedirs(outd, exist_ok=True)
manifest = []
seen_sha = {}
# load existing manifest to resume
mf = os.path.join(A, "grab_manifest.json")
if os.path.exists(mf):
    for row in json.load(open(mf)):
        manifest.append(row)
        seen_sha[row["sha256"]] = row["tag"]

def add_blob(tag, name, src, data):
    sha = hashlib.sha256(data).hexdigest()
    if sha in seen_sha:
        manifest.append({"tag": tag, "name": name, "source": src, "size": len(data),
                         "sha256": sha, "dedup_of": seen_sha[sha]})
        print("dup  %-24s %s" % (tag, seen_sha[sha]))
        return
    open(os.path.join(outd, tag + ".wem"), "wb").write(data)
    seen_sha[sha] = tag
    manifest.append({"tag": tag, "name": name, "source": src, "size": len(data), "sha256": sha})
    print("grab %-24s %8dB %s" % (tag, len(data), src.split("CookedPCConsole")[-1][:60]))

for h, n in sorted(want.items(), key=lambda kv: kv[1]):
    if h not in loc:
        manifest.append({"tag": None, "name": n, "source": "BANK-ONLY", "size": 0, "sha256": "", "want_hash": h})
        continue
    wad, off, sz = loc[h]
    f = open(wad, "rb")
    if off is None:  # SFX: rescan table for offset
        assert f.read(4) == b"WWAD"
        f.seek(8); n2 = struct.unpack("<I", f.read(4))[0]; f.seek(0x30)
        for _ in range(n2):
            hh, ss, n0, oo, n1 = struct.unpack("<IIIII", f.read(20))
            if "%08X" % hh == h:
                off, sz = oo, ss
                break
    f.seek(off)
    data = f.read(sz)
    f.close()
    if data[:4] != b"RIFF":
        print("SKIP non-RIFF", h, n)
        continue
    add_blob("wad_%s" % h, n, "%s@0x%X" % (os.path.basename(wad), off), data)

# bank DIDX media: BML_Engine, BML_Burnout, AUX_InBatmobile, MK2_Engine
banks = [(os.path.join(A, "bank_BML_Engine.bank"), "eng"),
         (os.path.join(A, "bank_BML_Burnout.bank"), "bout"),
         (os.path.join(A, "bank_AUX_InBatmobile.bank"), "aux"),
         (os.path.join(A, "bank_MK2_Engine.bank"), "mk2")]
for bp, pre in banks:
    if not os.path.exists(bp):
        print("missing bank file", bp); continue
    d = open(bp, "rb").read()
    di = d.find(b"DIDX")
    if di < 0:
        print("no DIDX in", bp); continue
    (dsz,) = struct.unpack_from("<I", d, di + 4)
    data = d.find(b"DATA")
    (datasz,) = struct.unpack_from("<I", d, data + 4)
    dbase = data + 8
    for k in range(dsz // 12):
        mid, off, sz = struct.unpack_from("<III", d, di + 8 + 12 * k)
        wem = d[dbase+off:dbase+off+sz]
        if wem[:4] != b"RIFF":
            continue
        add_blob("%s_%08X" % (pre, mid), "bank-media", "%s:DIDX:%08X" % (os.path.basename(bp), mid), wem)

json.dump(manifest, open(mf, "w"), indent=1)
print("manifest rows:", len(manifest), "unique blobs:", len(seen_sha))
