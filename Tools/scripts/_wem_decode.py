"""Decode shortlist WEMs with vgmstream-cli, rank engine-likeness by stationarity.
Steady multi-channel loops (engine) score high; varied music/dialogue scores low.
Usage: python _wem_decode.py [--limit N]"""
import json, os, struct, subprocess, sys, wave

import numpy as np

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
WEMD = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\wem"
WAVD = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\wav"
CLI = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\vgmstream-win64\vgmstream-cli.exe"

limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 40
census = json.load(open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\sfx_census.json"))
cands = [r for r in census if isinstance(r["ch"], int) and r["ch"] >= 2
         and (r["dur_s"] or 0) >= 10 and r["extra_waves"] <= 3]
cands.sort(key=lambda r: -r["size"])
cands = cands[:limit]
print("shortlist:", len(cands))

os.makedirs(WEMD, exist_ok=True)
os.makedirs(WAVD, exist_ok=True)

def wad_path(wad):
    p = os.path.join(CK, "SFX", wad)
    return p if os.path.exists(p) else os.path.join(CK, "English(US)", wad)

results = []
for r in cands:
    tag = "%s_%s" % (r["wad"].split(".")[0], r["hash"])
    wem = os.path.join(WEMD, tag + ".wem")
    wav = os.path.join(WAVD, tag + ".wav")
    if not os.path.exists(wem) or os.path.getsize(wem) != r["size"]:
        f = open(wad_path(r["wad"]), "rb")
        f.seek(8); n, = struct.unpack("<I", f.read(4)); f.seek(0x30)
        for _ in range(n):
            h, sz, nul, off, nul2 = struct.unpack("<IIIII", f.read(20))
            if "%08X" % h == r["hash"]:
                f.seek(off)
                open(wem, "wb").write(f.read(sz))
                break
        f.close()
    if not os.path.exists(wav):
        pr = subprocess.run([CLI, "-o", wav, wem], capture_output=True, text=True)
        if pr.returncode != 0 or not os.path.exists(wav):
            print("DECODE-FAIL", tag, (pr.stderr or "")[-200:])
            continue
    try:
        w = wave.open(wav, "rb")
        nch, sw, fr, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        dur = nf / fr if fr else 0
        raw = w.readframes(nf)
        w.close()
        a = np.frombuffer(raw, dtype=np.int16 if sw == 2 else np.int32).astype(np.float64)
        a = a.reshape(-1, nch).mean(axis=1)
        sec = max(1, int(fr))
        nsec = len(a) // sec
        rms = np.sqrt((a[:nsec * sec].reshape(nsec, sec) ** 2).mean(axis=1) + 1e-9)
        rms_db = 20 * np.log10(rms / 32768.0 + 1e-9)
        loud = rms_db > -45
        frac_loud = loud.mean()
        cv = rms[mla := loud].std() / (rms[mla].mean() + 1e-9) if loud.sum() > 3 else 9.0
        stat = frac_loud / (1 + cv)
        results.append((stat, tag, r["wad"], r["hash"], r["size"], nch, round(dur, 1),
                        round(float(frac_loud), 2), round(float(cv), 2)))
        print("ok %-22s %dch %7.0fs loud=%.2f cv=%.2f stat=%.3f" %
              (tag, nch, dur, frac_loud, cv, stat))
    except Exception as e:
        print("ANALYZE-FAIL", tag, e)
results.sort(reverse=True)
print("\n== engine-likeness ranking (stationary + loud first) ==")
for s, tag, wad, h, sz, nch, dur, fl, cv in results:
    print("%.3f %-22s %-11s %dch %7.0fs loud=%s cv=%s" % (s, tag, wad, nch, dur, fl, cv))
json.dump([{"tag": t, "stat": s, "wad": w, "hash": h, "size": sz, "ch": nch,
            "dur_s": d, "frac_loud": fl, "cv": cv}
           for s, t, w, h, sz, nch, d, fl, cv in results],
          open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\ranking.json", "w"), indent=1)
