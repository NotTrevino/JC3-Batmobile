"""Test TRAN pair as FSB data offset/length: decode + analyze."""
import struct
import numpy as np

P = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(P, "rb").read()
f5 = d.find(b"FSB5")
ver, n, shdr, ntl = struct.unpack_from("<IIII", d, f5 + 4)
blob = f5 + 60 + shdr + 4 * n
o = blob
for _ in range(n):
    e = d.find(b"\x00", o)
    o = e + 1
D0 = o
print("FSB data @0x%X" % D0)
import os
print("file len 0x%X, data remainder 0x%X" % (len(d), len(d) - D0))

for off, ln, tag in [(160991, 160991, "trans-pair")]:
    a = np.frombuffer(d[D0+off:D0+off+ln], dtype=np.int16).astype(np.float64)
    print("%s: %d samples %.2fs" % (tag, len(a), len(a) / 48000))
    win = 4800
    for i in range(0, min(len(a) // win, 12)):
        seg = a[i*win:(i+1)*win]
        rms = float(np.sqrt((seg**2).mean()))
        S = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1 / 48000)
        cent = float((freqs*S).sum() / (S.sum()+1e-12))
        print("  %.1fs rms=%6.0f cent=%5.0fHz" % (i/10, rms, cent))
