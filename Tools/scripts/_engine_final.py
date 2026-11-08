"""FINAL engine-event -> media resolve + extract + decode."""
import json, os, struct, subprocess

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
CLI = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\vgmstream-win64\vgmstream-cli.exe"

def fnv1(s):
    h = 0x811C9DC5
    for b in s.encode():
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ b
    return h

names = open(os.path.join(A, "bm_names.txt")).read().splitlines()
name_by_id = {}
for nm in names:
    if nm.startswith("Play_") or nm.startswith("Stop_"):
        name_by_id.setdefault(fnv1(nm.lower()), []).append(nm)

d = open(os.path.join(A, "bank_BML_Engine.bank"), "rb").read()
hi = d.find(b"HIRC"); o = hi + 8
(n,) = struct.unpack_from("<I", d, o); o += 4
objs = {}
for _ in range(n):
    t = d[o]; (sz,) = struct.unpack_from("<I", d, o + 1); body = d[o+5:o+5+sz]
    oid, = struct.unpack_from("<I", body, 0)
    objs.setdefault(t, {})[oid] = body; o += 5 + sz
S = set(objs.get(2, {})); C = set()
for t in (5, 6, 7, 9): C.update(objs.get(t, {}))
SC = S | C
A3 = set(objs.get(3, {}))

def allhits(body, ids):
    return {struct.unpack_from("<I", body, k)[0] for k in range(len(body) - 3)} & ids

ev_acts = {}
for eid, body in objs.get(4, {}).items():
    (cnt,) = struct.unpack_from("<I", body, 4)
    assert 8 + 4 * cnt <= len(body) + 8 or cnt == 0, (eid, cnt, len(body))
    ev_acts[eid] = {struct.unpack_from("<I", body, 8 + 4 * k)[0] for k in range(cnt)} & A3

act_tgt = {}
for aid, body in objs.get(3, {}).items():
    tgt6 = struct.unpack_from("<I", body, 6)[0] if len(body) >= 10 else None
    if tgt6 in SC:
        act_tgt[aid] = {tgt6}
    else:
        act_tgt[aid] = allhits(body, SC) - {aid}

cont_ch = {oid: allhits(body, SC) - {oid} for t in (5, 6, 7, 9) for oid, body in objs.get(t, {}).items()}

di = d.find(b"DIDX"); (dsz,) = struct.unpack_from("<I", d, di + 4)
didx = {}
for k in range(dsz // 12):
    mid, off, sz = struct.unpack_from("<III", d, di + 8 + 12 * k)
    didx[mid] = (off, sz)
DSET = set(didx)
snd_f = {sid: allhits(body, DSET) for sid, body in objs.get(2, {}).items()}

def media_of(node, depth=0):
    out = set()
    if node in snd_f: out.update(snd_f[node])
    if node in cont_ch and depth < 8:
        for ch in cont_ch[node]: out.update(media_of(ch, depth + 1))
    return out

data = d.find(b"DATA"); (datasz,) = struct.unpack_from("<I", d, data + 4); dbase = data + 8
os.makedirs(os.path.join(A, "bml"), exist_ok=True)
meta = []
for eid, acts in sorted(ev_acts.items()):
    nms = name_by_id.get(eid, ["(unmatched-%08X)" % eid])
    files = set()
    for aid in acts:
        for tgt in act_tgt.get(aid, ()): files.update(media_of(tgt))
    for f in sorted(files):
        off, sz = didx[f]
        wem = d[dbase+off:dbase+off+sz]
        assert wem[:4] == b"RIFF", (f, wem[:12])
        tag = "bml_%08X" % f
        open(os.path.join(A, "bml", tag + ".wem"), "wb").write(wem)
        wav = os.path.join(A, "bml", tag + ".wav")
        r = subprocess.run([CLI, "-o", wav, os.path.join(A, "bml", tag + ".wem")], capture_output=True, text=True)
        ok = r.returncode == 0 and os.path.exists(wav)
        meta.append({"event": nms[0], "eid": "%08X" % eid, "media": "%08X" % f, "size": sz, "wav": ok})
        print("%-38s ev=%08X media=%08X %8dB %s" % (nms[0][:38], eid, f, sz, "WAV-OK" if ok else "FAIL"))
json.dump(meta, open(os.path.join(A, "bml", "engine_media.json"), "w"), indent=1)
have = {m["eid"] for m in meta}
print("events with media: %d/%d  missing: %s" % (len(have), len(ev_acts), ["%08X" % e for e in sorted(ev_acts) if "%08X" % e not in have]))
