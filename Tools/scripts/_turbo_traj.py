"""Trajectory analysis of Turbo + Batmobile signature WEMs."""
import os, wave
import numpy as np

for tag in ["EC2FD42B", "E7BD5AD0"]:
    w = wave.open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\hashid\%s.wav" % tag, "rb")
    nch, sw, fr, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    a = np.frombuffer(w.readframes(nf), dtype=np.int16).astype(np.float64).reshape(-1, nch).mean(axis=1)
    w.close()
    print("== %s (%dch %.1fs)" % (tag, nch, nf / fr))
    win = fr // 5  # 200 ms
    for i in range(len(a) // win):
        seg = a[i*win:(i+1)*win]
        rms = float(np.sqrt((seg**2).mean()))
        S = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1 / fr)
        cent = float((freqs*S).sum() / (S.sum()+1e-12))
        print("  %4.1fs rms=%6.0f cent=%5.0fHz" % (i/5, rms, cent))
