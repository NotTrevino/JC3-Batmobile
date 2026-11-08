"""Swap nitro_start/loop/stop PCM payloads with Batmobile audio (same sizes).
Verifies by re-parse + vgmstream decode. Writes patched bank for dropzone.
Usage: python _apply_audio.py <src-bank> <dst-bank>
"""
import os, struct, subprocess, wave

import numpy as np
from fsb5 import FSB5

CLI = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\vgmstream-win64\vgmstream-cli.exe"
A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"

JOBS = [
    # (fsb index, source wav, use seconds or full, fade-out ms at end)
    (56, os.path.join(A, "bml", "jc3_batmobile_start.wav"), 0.7445, 30),
    (150, os.path.join(A, "hashid", "EC2FD42B.wav"), 3.2254, 0),
    (355, os.path.join(A, "hashid", "EC2FD42B.wav"), -0.756, 100),
]

def load_mono(path, nsamples):
    w = wave.open(path, "rb")
    nch, fr, nf = w.getnchannels(), w.getframerate(), w.getnframes()
    assert fr == 48000, fr
    a = np.frombuffer(w.readframes(nf), dtype=np.int16).astype(np.float64)
    w.close()
    return a.reshape(-1, nch).mean(axis=1), nsamples

def main():
    import sys
    src, dst = sys.argv[1], sys.argv[2]
    raw = bytearray(open(src, "rb").read())
    base = raw.find(b"FSB5")
    fsb = FSB5(bytes(raw[base:]))
    # data region base in FILE coords: find via first sample? use lib offsets relative to FSB start
    for idx, wav, span, fade_ms in JOBS:
        s = fsb.samples[idx]
        ns = s.samples
        payload_len = len(s.data)
        # header = payload_len - ns*2 (mono16)
        hlen = payload_len - ns * 2
        assert 0 <= hlen < 4096, (idx, payload_len, ns)
        mono, _ = load_mono(wav, ns)
        if span > 0:
            need = int(span * 48000)
            seg = mono[:need]
        else:
            need = int(-span * 48000)
            seg = mono[-need:]
        # exact length adjust (resample-free: trim/pad with edge fade)
        if len(seg) > ns:
            seg = seg[:ns]
        elif len(seg) < ns:
            pad = np.zeros(ns - len(seg))
            seg = np.concatenate([seg, pad])
        # loudness match to ORIGINAL payload pcm
        orig = np.frombuffer(s.data[hlen:hlen+ns*2], dtype=np.int16).astype(np.float64)
        g = np.sqrt((orig**2).mean() + 1) / (np.sqrt((seg**2).mean() + 1))
        seg = np.clip(seg * g, -32768, 32767)
        if fade_ms:
            f = int(fade_ms * 48)
            seg[-f:] *= np.linspace(1, 0, f)
        # zero-cross start
        zc = np.where(np.diff(np.sign(seg)))[0]
        if len(zc):
            seg[:zc[0]] = 0
        newdata = s.data[:hlen] + seg.astype(np.int16).tobytes()
        assert len(newdata) == payload_len, (len(newdata), payload_len)
        # locate sample data in FILE by content match
        doff = bytes(raw).find(bytes(s.data))
        assert doff >= 0 and raw[doff:doff+len(s.data)] == bytes(s.data), (idx, "offset mismatch")
        raw[doff:doff+len(s.data)] = newdata
        print("swapped #%d %-42s ns=%d gain=%.2f" % (idx, s.name, ns, g))
    open(dst, "wb").write(bytes(raw))
    print("wrote", dst, len(raw))
    # verify: reparse + decode swapped subsongs
    fsb2 = FSB5(bytes(open(dst, "rb").read())[base:])
    assert len(fsb2.samples) == 649
    for idx, _, _, _ in JOBS:
        r = subprocess.run([CLI, "-s", str(idx + 1), "-o", os.path.join(A, "verify_%d.wav" % idx), dst],
                           capture_output=True, text=True)
        ok = r.returncode == 0 and os.path.exists(os.path.join(A, "verify_%d.wav" % idx))
        print("verify #%d: %s" % (idx, "WAV-OK" if ok else r.stderr[-200:]))

main()
