"""Spectral character of top-ranked loops (slice reads only): centroid + f0/harmonicity."""
import json, os, wave
import numpy as np

rank = json.load(open(r"E:\Modding\JC3-Batmobile\Working\Audio\ranking.json"))
WAVD = r"E:\Modding\JC3-Batmobile\Working\Audio\wav"

def autocorr_peak(a, fr):
    a = a - a.mean()
    seg = a[:fr * 4]
    ac = np.correlate(seg, seg, mode="full")[len(seg) - 1:]
    ac /= ac[0] + 1e-12
    lo, hi = int(fr / 500), int(fr / 25)
    k = int(np.argmax(ac[lo:hi])) + lo
    return fr / k, float(ac[k])

rows = []
for r in rank[:14]:
    w = wave.open(os.path.join(WAVD, r["tag"] + ".wav"), "rb")
    nch, sw, fr, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    mid = nf // 2
    w.setpos(max(0, mid - fr * 3))
    raw = w.readframes(fr * 6)
    w.close()
    dt = np.int16 if sw == 2 else np.int32
    a = np.frombuffer(raw, dtype=dt).astype(np.float64)
    a = a.reshape(-1, nch)[:, :min(nch, 2)].mean(axis=1)
    n = len(a)
    S = np.abs(np.fft.rfft(a * np.hanning(n)))[:n // 4]
    freqs = np.fft.rfftfreq(n, 1 / fr)[:n // 4]
    cent = float((freqs * S).sum() / (S.sum() + 1e-12))
    f0, harm = autocorr_peak(a, fr)
    rows.append((harm, cent, f0, r["tag"], nch, r["dur_s"]))
    print("%-22s %dch %6.0fs cent=%5.0fHz f0~%4.0fHz harm=%.2f" % (r["tag"], nch, r["dur_s"], cent, f0, harm))
rows.sort(reverse=True)
print("\n== harmonicity ranking ==")
for harm, cent, f0, tag, nch, dur in rows:
    print("harm=%.2f cent=%5.0fHz f0~%4.0fHz %-22s %dch %.0fs" % (harm, cent, f0, tag, nch, dur))
