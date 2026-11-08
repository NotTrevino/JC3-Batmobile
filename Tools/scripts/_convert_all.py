"""CONVERT everything grabbed: batch vgmstream decode + manifest provenance.
Usage: python _convert_all.py
"""
import json, os, subprocess, wave

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
CLI = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\vgmstream-win64\vgmstream-cli.exe"

mf = os.path.join(A, "grab_manifest.json")
manifest = json.load(open(mf))
nab = 0
for row in manifest:
    if "dedup_of" in row or "wav" in row:
        continue
    tag = row.get("tag")
    if not tag:
        continue  # BANK-ONLY (no bytes)
    wem = os.path.join(A, "grab", tag + ".wem")
    wav = os.path.join(A, "grab", tag + ".wav")
    if os.path.exists(wav):
        pass
    else:
        r = subprocess.run([CLI, "-o", wav, wem], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(wav):
            row["decode"] = "FAIL " + (r.stderr or "")[-120:]
            print("FAIL", tag)
            continue
    try:
        w = wave.open(wav, "rb")
        row["wav"] = wav
        row["ch"] = w.getnchannels()
        row["dur_s"] = round(w.getnframes() / w.getframerate(), 2)
        w.close()
        nab += 1
    except Exception as e:
        row["decode"] = "WAV-READ-FAIL %s" % e
print("decoded+measured: %d" % nab)
json.dump(manifest, open(mf, "w"), indent=1)
print("manifest rows:", len(manifest))
