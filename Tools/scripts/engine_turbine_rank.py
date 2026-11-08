"""Rank the BmAK engine-group media by 'turbine whine' character, and line them up with
the JC3 vehicle sample slots a same-length swap can fill.

Read-only: reads Research/BatmobileGrab/AUDIO_FEATURES.json (event -> WEM, media measurements,
vgmstream loop lines) and the 48 kHz WAVs under E:\\Modding\\_gamedata\\BmAKgrab\\audio\\wav,
then measures brightness and narrowband tonality with numpy. No bank, no game file, no
install is written.

Usage:
    python Tools/scripts/engine_turbine_rank.py            # measure + print
    python Tools/scripts/engine_turbine_rank.py --write    # also write ENGINE_TURBINE_SCAN.json
    python Tools/scripts/engine_turbine_rank.py --check    # recompute, compare with JSON

Two measured axes, both defined here (not Wwise-authored numbers):
    T = 10*log10(E[2k..10k] / E[20..300])        dB, brightness against the V8 region
    P = 10*log10(max(P[1.2k..8k]) / median(P))   dB, narrowband tonality in the whine band
Class (derived thresholds, stated so they can be argued with):
    TURBINE-LED  T >= 0 and P >= 10 and peak  >= 1200 Hz
    V8-LED       E[20..300] / E[20..16k] >= 0.45 and peak(20..400) < 500 Hz
    MIXED        otherwise
rank_score = T + 0.5*P  (ordering only; both axes are printed so it can be re-ranked)
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEATURES = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_FEATURES.json")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "ENGINE_TURBINE_SCAN.json")
WAV_DIR = r"E:\Modding\_gamedata\BmAKgrab\audio\wav"

GROUPS = ("engine", "battle-mode")
BANDS = ((20, 300), (300, 1200), (1200, 2000), (2000, 10000), (10000, 16000))
WHINE = (1200.0, 8000.0)
WIN, HOP = 4096, 2048

# JC3 engine slots a same-length swap can fill (plan section 6.1), frames from
# JC3_AUDIO_EVENTS.json samples.list. "order" is idle -> high rpm.
JC3_SLOTS = [
    (1, 127, "aston_martin_vantage_engine_rpm_idle_high", 113272, "idle-high"),
    (2, 619, "aston_martin_vantage_engine_rpm_idle2", 119392, "idle"),
    (3, 601, "aston_martin_vantage_engine_rpm_low2", 111710, "low"),
    (4, 390, "aston_martin_vantage_engine_rpm_medium_low", 98882, "medium-low"),
    (5, 636, "aston_martin_vantage_engine_rpm_medium_high2", 98694, "medium-high"),
    (6, 236, "aston_martin_vantage_engine_rpm_high", 94376, "high"),
    (0, 497, "jc3_veh_ferrari_275_engine_whir_loop", 102994, "whir-loop (already turbine)"),
    (0, 484, "jc3_veh_air_jet_fighter_01_jet_turbine_04", 150738, "jet turbine"),
    (0, 631, "jc3_veh_air_cargo_plane_turbine_drone", 204807, "turbine drone"),
    (0, 498, "jc3_veh_ferrari_275_engine_whir_loop", 102994, "dup of 497"),
]
SR = 48000


def band_energy(P, f, lo, hi):
    m = (f >= lo) & (f < hi)
    return float(P[m].sum()) if m.any() else 0.0


def measure(path):
    sr, data = wavfile.read(path)
    if data.dtype != np.int16:
        data = data.astype(np.int16)
    a = data.astype(np.float64) / 32768.0
    if a.ndim > 1:
        ch = int(a.shape[1])
        a = a.mean(axis=1)
    else:
        ch = 1
    n = int(a.shape[0])
    win = np.hanning(WIN)
    acc, cnt = None, 0
    for s in range(0, max(1, n - WIN + 1), HOP):
        seg = a[s:s + WIN]
        if seg.size < WIN:
            seg = np.pad(seg, (0, WIN - seg.size))
        P = np.abs(np.fft.rfft(seg * win)) ** 2
        acc = P if acc is None else acc + P
        cnt += 1
    if acc is None or cnt == 0:
        seg = np.zeros(WIN)
        seg[:min(n, WIN)] = a[:WIN]
        acc, cnt = np.abs(np.fft.rfft(seg * win)) ** 2, 1
    P = acc / cnt + 1e-20
    f = np.fft.rfftfreq(WIN, 1.0 / sr)

    e = {("%d-%d" % b): band_energy(P, f, b[0], b[1]) for b in BANDS}
    tot = band_energy(P, f, 20, 16000) or 1e-20
    high = band_energy(P, f, 2000, 10000)
    low = band_energy(P, f, 20, 300) or 1e-20
    T = 10.0 * math.log10(max(high, 1e-20) / low)

    wm = (f >= WHINE[0]) & (f <= WHINE[1])
    Pw = P[wm]
    peak = float(Pw.max()) if Pw.size else 0.0
    med = float(np.median(Pw)) if Pw.size else 0.0
    P_tone = 10.0 * math.log10(max(peak, 1e-20) / max(med, 1e-20))
    peak_hz = float(f[wm][int(np.argmax(Pw))]) if Pw.size else 0.0

    lm = (f >= 20) & (f <= 400)
    low_peak_hz = float(f[lm][int(np.argmax(P[lm]))]) if lm.any() else 0.0

    low_share = low / tot
    if T >= 0 and P_tone >= 10 and peak_hz >= 1200:
        cls = "TURBINE-LED"
    elif low_share >= 0.45 and low_peak_hz < 500:
        cls = "V8-LED"
    else:
        cls = "MIXED"

    rms = float(np.sqrt(np.mean(a ** 2))) if n else 0.0
    crest = float(np.max(np.abs(a)) / rms) if rms else 0.0
    return {
        "duration_s": round(n / float(sr), 3),
        "frames": n,
        "rate": int(sr),
        "channels": ch,
        "rms_dbfs": round(20 * math.log10(max(rms, 1e-9)), 2),
        "crest": round(crest, 2),
        "T_db": round(T, 2),
        "P_tone_db": round(P_tone, 2),
        "peak_hz": round(peak_hz, 1),
        "low_peak_hz": round(low_peak_hz, 1),
        "low_share": round(low_share, 3),
        "hf_share": round(high / tot, 3),
        "bands": {k: round(v / tot, 4) for k, v in e.items()},
        "class": cls,
        "score": round(T + 0.5 * P_tone, 2),
    }


def collect():
    doc = json.load(open(FEATURES, encoding="utf-8"))
    media = {m["wem_hex"]: m for m in doc["media"]}
    rows = []
    seen = set()
    for ev in doc["events"]:
        if ev.get("group") not in GROUPS:
            continue
        for whex in ev.get("wems") or []:
            m = media.get(whex)
            rec = {"wem": whex, "event": ev["name"], "group": ev["group"], "bank": ev.get("bank")}
            if m is None:
                rec["error"] = "media not in decode table"
                rows.append(rec)
                continue
            rec.update({
                "duration_json_s": m.get("duration_s"),
                "channels_json": m.get("channels"),
                "bytes": m.get("bytes"),
                "source": m.get("source"),
                "loop_lines": m.get("loop_lines") or [],
            })
            key = (whex, ev["name"])
            if key in seen:
                continue
            seen.add(key)
            path = os.path.join(WAV_DIR, "%08X.wav" % int(whex, 16))
            if not os.path.exists(path):
                rec["error"] = "WAV missing"
                rows.append(rec)
                continue
            rec["wav"] = path
            try:
                rec.update(measure(path))
            except Exception as exc:  # measurement only; report, never abort
                rec["error"] = "measure failed: %s" % exc
            rows.append(rec)
    return doc, rows


def loop_window(lines):
    """vgmstream -m text -> (start, end) frames, or None."""
    st = en = None
    for line in lines:
        low = line.lower()
        if low.startswith("loop start:"):
            st = int(low.split(":", 1)[1].split()[0])
        elif low.startswith("loop end:"):
            en = int(low.split(":", 1)[1].split()[0])
    return (st, en) if st is not None and en is not None else None


def fill_plan(ranked):
    """Can a donor be laid into a JC3 slot at exactly the slot's frame count?"""
    out = []
    for r in ranked:
        lw = loop_window(r.get("loop_lines") or [])
        row = {"wem": r["wem"], "event": r["event"], "class": r["class"],
               "frames": r.get("frames"), "loop_window": lw,
               "loop_frames": (lw[1] - lw[0]) if lw else None}
        cells = []
        for o, slot, name, frames, band in JC3_SLOTS:
            if lw:
                lf = lw[1] - lw[0]
                whole, resid = divmod(frames, lf)
                cells.append({"slot": slot, "band": band, "frames": frames,
                              "repeats": whole, "residual_frames": resid,
                              "verdict": "exact" if resid == 0 else "trim tail"})
            else:
                cells.append({"slot": slot, "band": band, "frames": frames,
                              "repeats": 0, "residual_frames": frames,
                              "verdict": "cut first %d frames (no loop)" % frames
                              if r.get("frames", 0) >= frames else "too short"})
        row["slots"] = cells
        out.append(row)
    return out


def summarise(doc, rows):
    ok = [r for r in rows if "score" in r]
    by_wem = {}
    for r in ok:
        by_wem.setdefault(r["wem"], r)
    ranked = sorted(by_wem.values(), key=lambda r: (-r["score"], r["wem"]))
    per_event = {}
    for r in ok:
        per_event.setdefault(r["event"], []).append(r)
    ev_rows = []
    for name, recs in sorted(per_event.items()):
        best = max(recs, key=lambda r: r["score"])
        ev_rows.append({
            "event": name, "group": recs[0]["group"], "media": len({r["wem"] for r in recs}),
            "best_wem": best["wem"], "best_score": best["score"], "best_class": best["class"],
            "best_T_db": best["T_db"], "best_P_tone_db": best["P_tone_db"],
            "turbine_led": sum(1 for r in recs if r["class"] == "TURBINE-LED"),
            "v8_led": sum(1 for r in recs if r["class"] == "V8-LED"),
            "looped": sorted({r["wem"] for r in recs if r["loop_lines"]}),
        })
    ev_rows.sort(key=lambda r: -r["best_score"])
    out = {
        "schema": 1,
        "generated_by": "Tools/scripts/engine_turbine_rank.py",
        "inputs": {"features": os.path.relpath(FEATURES, ROOT).replace("\\", "/"),
                   "wav_dir": WAV_DIR},
        "method": {
            "window": "%d-sample Hann, %d hop, averaged power spectrum" % (WIN, HOP),
            "T_db": "10*log10(E[2k..10k] / E[20..300])",
            "P_tone_db": "10*log10(max(P[1.2k..8k]) / median(P[1.2k..8k]))",
            "class_rule": "TURBINE-LED if T>=0 and P>=10 and peak>=1200 Hz; "
                          "V8-LED if E[20..300]/E[20..16k]>=0.45 and peak(20..400)<500 Hz",
            "score": "T + 0.5*P (ordering only)",
            "loop_points": "vgmstream -m lines captured by bmak_audio_features.py; "
                           "absence means the stream carries no loop flag, not that the "
                           "Wwise event is one-shot",
        },
        "counts": {
            "rows": len(rows), "measured": len(ok),
            "distinct_media": len(by_wem),
            "turbine_led": sum(1 for r in ranked if r["class"] == "TURBINE-LED"),
            "v8_led": sum(1 for r in ranked if r["class"] == "V8-LED"),
            "mixed": sum(1 for r in ranked if r["class"] == "MIXED"),
            "with_loop_points": sum(1 for r in ranked if r["loop_lines"]),
        },
        "ranked": ranked,
        "events": ev_rows,
        "jc3_slots": [{"order": o, "slot": s, "name": n, "frames": fr, "band": b,
                       "seconds": round(fr / float(SR), 3)}
                      for o, s, n, fr, b in JC3_SLOTS],
    }
    sustained = [r for r in ranked if (r.get("loop_window") or 0) or (r["duration_s"] >= 2.0)]
    out["sustained"] = [r["wem"] for r in sustained]
    out["fill"] = fill_plan(sustained)
    return out


def digest(doc):
    keys = ["wem", "event", "duration_s", "channels", "T_db", "P_tone_db", "peak_hz",
            "low_share", "class", "score"]
    blob = "|".join(",".join(str(r.get(k)) for k in keys) for r in doc["ranked"])
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def print_table(doc):
    c = doc["counts"]
    print("measured %d rows over %d distinct media: %d turbine-led, %d v8-led, %d mixed, "
          "%d with loop points" % (c["measured"], c["distinct_media"], c["turbine_led"],
                                   c["v8_led"], c["mixed"], c["with_loop_points"]))
    print()
    print("%-10s %-42s %7s %6s %7s %7s %8s %8s %6s %s"
          % ("wem", "event", "sec", "ch", "T dB", "P dB", "peak Hz", "low Hz", "score", "class"))
    for r in doc["ranked"][:40]:
        print("%-10s %-42s %7.3f %6d %7.2f %7.2f %8.0f %8.0f %6.2f %s"
              % (r["wem"], r["event"][:42], r["duration_s"], r["channels"], r["T_db"],
                 r["P_tone_db"], r["peak_hz"], r["low_peak_hz"], r["score"], r["class"]))
    print()
    looped = [r for r in doc["ranked"] if r["loop_lines"]]
    print("loop points found on %d media:" % len(looped))
    for r in looped:
        print("  %s %-40s %s" % (r["wem"], r["event"][:40], "; ".join(r["loop_lines"])))
    print()
    print("slot fill for the sustained (>=2 s or looped) turbine layers:")
    for row in doc["fill"]:
        if row["class"] != "TURBINE-LED":
            continue
        tail = ", ".join("%d:%s(%d rep,%d resid)" % (c["slot"], c["verdict"][:9], c["repeats"],
                                                    c["residual_frames"]) for c in row["slots"][:6])
        print("  %s %-38s loop=%s  %s" % (row["wem"], row["event"][:38],
                                          row["loop_frames"], tail))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc, rows = collect()
    out = summarise(doc, rows)
    if a.check:
        if not os.path.exists(OUT_JSON):
            print("FAIL: %s missing (run --write first)" % OUT_JSON)
            return 1
        old = json.load(open(OUT_JSON, encoding="utf-8"))
        bad = []
        if old.get("counts") != out["counts"]:
            bad.append("counts differ: %s vs %s" % (old.get("counts"), out["counts"]))
        om = {r["wem"] + "/" + r["event"]: r for r in old.get("ranked", [])}
        for r in out["ranked"]:
            o = om.get(r["wem"] + "/" + r["event"])
            if o is None:
                bad.append("missing row %s/%s" % (r["wem"], r["event"]))
                continue
            for k in ("T_db", "P_tone_db", "peak_hz", "low_share", "class", "duration_s"):
                if o.get(k) != r.get(k):
                    bad.append("%s/%s %s: %r != %r" % (r["wem"], r["event"], k,
                                                       o.get(k), r.get(k)))
        d_new, d_old = digest(out), old.get("digest")
        if d_new != d_old:
            bad.append("digest %s != %s" % (d_new, d_old))
        if bad:
            print("FAIL: %d difference(s)" % len(bad))
            for b in bad[:25]:
                print("  " + b)
            return 1
        print("PASS: %d rows, digest %s recompute identically from %s"
              % (len(out["ranked"]), d_new, WAV_DIR))
        return 0
    out["digest"] = digest(out)
    if a.write:
        json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), indent=1)
        print("wrote %s (digest %s)" % (OUT_JSON, out["digest"]))
    print_table(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
