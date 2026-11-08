"""Depth-1 engine media: event -> action -> target -> direct sounds only. Decode + rank."""
import json, os, struct, subprocess, wave
import numpy as np

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

di = d.find(b"DIDX"); (dsz,) = struct.unpack_from("<I", d, di + 4)
didx = {}
for k in range(dsz // 12):
    mid, off, sz = struct.unpack_from("<III", d, di + 8 + 12 * k)
    didx[mid] = (off, sz)
data = d.find(b"DATA"); dbase = data + 8
snd_f = {sid: allhits(body, set(didx)) for sid, body in objs.get(2, {}).items()}

FOCUS = ["Play_Batmobile_Idle", "Play_Batmobile_Engine_Transition_In",
         "Play_Batmobile_Engine_Transition_Out", "Play_Batmobile_Clutch",
         "Play_Batmobile_Reverse", "Play_Batmobile_Tyres", "Play_Batmobile_Positional",
         "Play_Batmobile_DistantRev", "Play_Batmobile_MShot"]
want_ids = {fnv1(n.lower()): n for n in FOCUS}
# plus every other event in the bank (unmatched keep raw id)
_extra = True

os.makedirs(os.path.join(A, "bml"), exist_ok=True)
rows = []
seen_media = {}
for eid, body in objs.get(4, {}).items():
    if eid not in want_ids:
        if _extra:
            want_ids[eid] = "(unmatched-%08X)" % eid
        else:
            continue
    (cnt,) = struct.unpack_from("<I", body, 4)
    acts = {struct.unpack_from("<I", body, 8 + 4 * k)[0] for k in range(cnt)} & A3
    for aid in acts:
        ab = objs[3][aid]
        tgt = struct.unpack_from("<I", ab, 6)[0] if len(ab) >= 10 else None
        tgts = {tgt} & SC if tgt else allhits(ab, SC) - {aid}
        for tgt in tgts:
            direct = ({tgt} & S) | ({tgt} and (allhits(objs[[k for k in objs if tgt in objs[k]][0]][tgt], S) if tgt in C else set()) or set())
            for sid in direct:
                for f in snd_f.get(sid, ()):
                    if f in seen_media:
                        seen_media[f][1].append(want_ids[eid])
                        continue
                    off, sz = didx[f]
                    wem = d[dbase+off:dbase+off+sz]
                    tag = "eng_%08X" % f
                    open(os.path.join(A, "bml", tag + ".wem"), "wb").write(wem)
                    wav = os.path.join(A, "bml", tag + ".wav")
                    r = subprocess.run([CLI, "-o", wav, os.path.join(A, "bml", tag + ".wem")],
                                       capture_output=True, text=True)
                    if r.returncode != 0:
                        continue
                    w = wave.open(wav, "rb")
                    nch, sw, fr, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
                    a = np.frombuffer(w.readframes(nf), dtype=np.int16).astype(np.float64)
                    w.close()
                    a = a.reshape(-1, nch).mean(axis=1)
                    sec = fr
                    nsec = len(a) // sec
                    rms = np.sqrt((a[:nsec*sec].reshape(nsec, sec) ** 2).mean(axis=1) + 1e-9)
                    cv = float(rms.std() / (rms.mean() + 1e-9))
                    seg = a[len(a)//3:len(a)//3 + fr * 4]
                    Sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
                    freqs = np.fft.rfftfreq(len(seg), 1 / fr)
                    cent = float((freqs * Sp).sum() / (Sp.sum() + 1e-12))
                    seen_media[f] = [{"tag": tag, "ch": nch, "dur": round(nf / fr, 1),
                                       "cv": round(cv, 3), "cent": round(cent),
                                       "size": sz}, [want_ids[eid]]]
print("%-14s %4s %7s %6s %8s %6s %s" % ("tag", "ch", "dur_s", "cv", "cent", "size", "events"))
rank = []
for f, (info, evs) in seen_media.items():
    print("%-14s %4d %7.1f %6.3f %8.0f %6d %s" % (info["tag"], info["ch"], info["dur"], info["cv"],
          info["cent"], info["size"], ",".join(evs)))
    rank.append((info["cv"], info["cent"], info["tag"], evs, info))
rank.sort(key=lambda r: (r[0], r[1]))
print("\n== steadiest + deepest first (engine-loop-like) ==")
for cv, cent, tag, evs, info in rank[:20]:
    print("cv=%.3f cent=%5.0fHz %-14s %dch %.1fs %s" % (cv, cent, tag, info["ch"], info["dur"], ",".join(evs)))
json.dump([{"info": info, "events": evs} for _, _, _, evs, info in rank],
          open(os.path.join(A, "bml", "engine_depth1.json"), "w"), indent=1)
