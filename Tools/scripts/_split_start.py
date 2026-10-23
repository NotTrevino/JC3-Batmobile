"""JC3-ready pair: START (ignition head) + LOOP (flattest window, zero-cross cuts)."""
import os, wave
import numpy as np

A = r"E:\Modding\JC3-Batmobile\Working\Audio\bml"

def load(tag):
    w = wave.open(os.path.join(A, tag + ".wav"), "rb")
    p = (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes())
    a = np.frombuffer(w.readframes(p[3]), dtype=np.int16).astype(np.float64)
    w.close()
    return p, a

def save(tag, p, a):
    o = wave.open(os.path.join(A, tag + ".wav"), "wb")
    o.setnchannels(p[0]); o.setsampwidth(p[1]); o.setframerate(p[2])
    o.writeframes(np.clip(a, -32768, 32767).astype(np.int16).tobytes())
    o.close()
    print("wrote %s.wav (%.2fs)" % (tag, len(a) / p[0] / p[2]))

def zc_up(m, i0, lo, hi):
    seg = m[lo:hi]
    z = np.where((seg[:-1] <= 0) & (seg[1:] > 0))[0]
    return lo + (z[len(z)//2] if len(z) else (hi - lo) // 2)

# START: eng_1808E883 head through settle (0-2.0 s) + 30 ms fade-out
p, a = load("eng_1808E883")
nch, sw, fr, nf = p
m = a.reshape(-1, nch).mean(axis=1)
cut = zc_up(m, 0, int(1.95*fr), int(2.05*fr))
st = a.reshape(-1, nch)[:cut].copy()
f = int(0.03*fr)
st[-f:] *= np.linspace(1, 0, f)[:, None]
save("jc3_batmobile_start", p, st.reshape(-1))

# LOOP: flattest 1.5 s window of eng_1FD7E69F
p2, a2 = load("eng_1FD7E69F")
nch, sw, fr, nf = p2
m2 = a2.reshape(-1, nch).mean(axis=1)
W, H = int(1.5*fr), int(0.1*fr)
best, bv = 0, 1e18
for s in range(0, len(m2)-W, H):
    v = m2[s:s+W].var()
    if v < bv: bv, best = v, s
s0 = zc_up(m2, 0, best, best+H)
s1 = zc_up(m2, 0, best+W-H, best+W+H if best+W+H < len(m2) else len(m2)-1)
# loop-seam check: end vs start continuity
seg = a2.reshape(-1, nch)[s0:s1]
tail = np.abs(seg[-f:].mean(axis=0)).mean()
print("loop window %.2f-%.2fs seam_dc=%.0f" % (s0/fr, s1/fr, tail))
save("jc3_batmobile_loop", p2, seg.reshape(-1))
