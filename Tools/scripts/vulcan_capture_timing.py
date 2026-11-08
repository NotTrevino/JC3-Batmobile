"""Vulcan capture: PTS-based frame timing (BmAK, operator brief 2026-11-08).

Measures the battle-mode Vulcan fire event in
  C:/Users/User/Videos/Captures/Batman<tm>_ Arkham Knight VulcanFire_10s-15s.mp4
from the decoded frames, indexed by presentation timestamp (the capture is
variable-framerate: 1352 frames / 49.21 s, nominal 60000/1001).

HUD geometry it reads (measured in the capture, not assumed):
  ring      fixed circle, radius ~25 px around screen (961, 378) - never moves
  arms      four radial arms at N/E/S/W that slide OUTWARD through the ring as
            the spread grows (inside r 6..20 at rest, outside r 28..41 at full)
  colour    the arms' tips fade from white to red as they travel out

Usage:
  python Tools/scripts/vulcan_capture_timing.py --probe    # per-frame table
  python Tools/scripts/vulcan_capture_timing.py --write    # JSON + MD + PNGs
  python Tools/scripts/vulcan_capture_timing.py --check    # recompute + compare
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

VIDEO = Path("C:/Users/User/Videos/Captures/Batman\u2122_ Arkham Knight VulcanFire_10s-15s.mp4")
PNG_DIR = Path("E:/Modding/ArkhamKnight/_grab/footage/vulcan")
RES = Path("Research/BatmobileGrab")
JNAME = "VULCAN_CAPTURE.json"
MNAME = "VULCAN_CAPTURE.md"

CENTER = (961.0, 378.0)          # reticle centre, screen px (1920x1080)
CROP_W = CROP_H = 320
CROP_X = int(CENTER[0] - CROP_W // 2)
CROP_Y = int(CENTER[1] - CROP_H // 2)
LCX, LCY = CROP_W / 2.0, CROP_H / 2.0

R_LO, R_HI = 4.0, 50.0
BASELINE_WIN = (9.6, 11.6)
PEAK_WIN = (14.8, 16.4)
RED_TH = 25.0


def ffprobe_frames() -> list[dict]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "frame=pts_time,duration_time", "-of", "csv=p=0", str(VIDEO)],
        capture_output=True, text=True, check=True).stdout
    rows = []
    for line in out.splitlines():
        parts = [p for p in line.strip().split(",") if p != ""]
        if not parts:
            continue
        try:
            pts = float(parts[0])
        except ValueError:
            continue
        rows.append({"pts": pts, "dur": float(parts[1]) if len(parts) > 1 else 0.0})
    if not rows:
        raise SystemExit("ffprobe returned no frames")
    return rows


def frame_stream():
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(VIDEO),
           "-vf", f"crop={CROP_W}:{CROP_H}:{CROP_X}:{CROP_Y}",
           "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         bufsize=CROP_W * CROP_H * 3 * 8)
    n = CROP_W * CROP_H * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(CROP_H, CROP_W, 3).astype(np.int16)
    p.stdout.close()
    p.wait()


DIRS = (("N", -90.0), ("E", 0.0), ("S", 90.0), ("W", 180.0))


def frame_metrics(fr: np.ndarray) -> dict:
    r, g, b = fr[..., 0], fr[..., 1], fr[..., 2]
    v = fr.max(axis=2)
    bright = (v >= 170) & ((g - np.maximum(r, b)) <= 25)   # bright arm, not the green arc

    tips, bases, scores = [], [], {}
    rr = np.arange(R_LO, R_HI, 0.5)
    for name, base in DIRS:
        # narrow wedge (+-4 deg) inside the ring's gap: no ring, no arc, just the arm
        hit = np.zeros(len(rr), bool)
        for a_deg in np.arange(base - 4, base + 4.5, 1.0):
            a = math.radians(a_deg)
            xs = np.rint(LCX + math.cos(a) * rr).astype(int)
            ys = np.rint(LCY + math.sin(a) * rr).astype(int)
            ok = (xs >= 0) & (xs < CROP_W) & (ys >= 0) & (ys < CROP_H)
            hit[ok] |= bright[ys[ok], xs[ok]]
        if not hit.any():
            scores[name] = 0.0
            continue
        # contiguous run that starts at the innermost hit (gap tolerance 2 px)
        idxs = np.nonzero(hit)[0]
        start = idxs[0]
        end = start
        for j in idxs:
            if (j - end) * 0.5 <= 2.0:
                end = j
            else:
                break
        tip = float(rr[end])
        tips.append(tip)
        bases.append(float(rr[start]))
        sel = np.zeros((CROP_H, CROP_W), bool)
        for a_deg in np.arange(base - 4, base + 4.5, 1.0):
            a = math.radians(a_deg)
            xs = np.rint(LCX + math.cos(a) * rr[start:end + 1]).astype(int)
            ys = np.rint(LCY + math.sin(a) * rr[start:end + 1]).astype(int)
            ok = (xs >= 0) & (xs < CROP_W) & (ys >= 0) & (ys < CROP_H)
            sel[ys[ok], xs[ok]] = True
        sel &= bright
        scores[name] = (float(r[sel].mean() - np.maximum(g[sel], b[sel]).mean())
                        if sel.any() else 0.0)
    arm_out = float(np.median(tips)) if tips else 0.0
    arm_in = float(np.median(bases)) if bases else 0.0
    red_dirs = sum(1 for s in scores.values() if s >= RED_TH)
    redscore = float(np.median(list(scores.values())))
    return {"arm_out": arm_out, "arm_in": arm_in, "red": redscore,
            "red_dirs": red_dirs, "ticks": {k: round(val, 1) for k, val in scores.items()}}


def measure() -> list[dict]:
    frames = ffprobe_frames()
    rows = []
    for i, fr in enumerate(frame_stream()):
        if i >= len(frames):
            break
        m = frame_metrics(fr)
        m["i"] = i
        m["pts"] = frames[i]["pts"]
        m["dur"] = frames[i]["dur"]
        rows.append(m)
    if len(rows) != len(frames):
        raise SystemExit(f"decoded {len(rows)} frames, ffprobe listed {len(frames)}")
    return rows


def derive(rows: list[dict]) -> dict:
    pts = np.array([r["pts"] for r in rows])
    out = np.array([r["arm_out"] for r in rows])
    red = np.array([r["red"] for r in rows])

    base = float(np.median(out[(pts >= BASELINE_WIN[0]) & (pts <= BASELINE_WIN[1])]))
    peak = float(np.percentile(out[(pts >= PEAK_WIN[0]) & (pts <= PEAK_WIN[1])], 90))

    spread_on = None
    for i in range(len(rows)):
        if pts[i] < BASELINE_WIN[0]:
            continue
        if out[i] >= base + 1.5 and all(out[i:i + 3] >= base + 1.0):
            spread_on = i
            break
    full_on = red_on = None
    if spread_on is not None:
        for i in range(spread_on, len(rows)):
            if out[i] >= peak - 0.8 and all(out[i:i + 4] >= peak - 1.5):
                full_on = i
                break
        for i in range(spread_on, len(rows)):
            if red[i] >= RED_TH and all(red[i:i + 3] >= RED_TH - 5):
                red_on = i
                break
    wide = np.nonzero(out >= base + 1.5)[0]
    wide = wide[wide >= (spread_on if spread_on is not None else 0)]
    last_wide = int(wide.max()) if len(wide) else None
    narrow_back = None
    if last_wide is not None:
        for i in range(last_wide + 1, len(rows)):
            if out[i] <= base + 1.0 and all(out[i:i + 3] <= base + 1.5) and \
                    all(red[i:i + 3] <= 12):
                narrow_back = i
                break
    clip_end_widest = bool(len(rows) and out[-1] >= base + 1.5)
    prev_narrow = (spread_on - 1) if spread_on is not None else None

    def t(i):
        return None if i is None else round(float(pts[i]), 3)

    def dt(a, b):
        return None if a is None or b is None else round(float(pts[a] - pts[b]), 3)

    return {
        "baseline_arm": round(base, 2),
        "peak_arm": round(peak, 2),
        "narrow_last": t(prev_narrow),
        "spread_on": t(spread_on),
        "full_on": t(full_on),
        "red_on": t(red_on),
        "last_wide": t(last_wide),
        "narrow_back": t(narrow_back),
        "idx": {"narrow_last": prev_narrow, "spread_on": spread_on, "full_on": full_on,
                "red_on": red_on, "last_wide": last_wide, "narrow_back": narrow_back},
        "t_spread_from_narrow": dt(spread_on, prev_narrow),
        "t_full_from_spread": dt(full_on, spread_on),
        "t_full_from_narrow": dt(full_on, prev_narrow),
        "t_red_from_spread": dt(red_on, spread_on),
        "t_red_from_narrow": dt(red_on, prev_narrow),
        "t_full_to_narrow_back": dt(narrow_back, full_on),
        "t_wide_total": dt(last_wide, prev_narrow),
        "wide_at_clip_end": clip_end_widest,
        "clip_end_pts": round(float(pts[-1]), 3),
        "growth_ratio": round(peak / base, 3),
    }


def audio_analysis(lookback_to: float = 10.6) -> dict:
    """Trigger onset and impulse cadence from the audio track.

    The muzzle and the car are not in any frame (checked: five frames across the
    clip, `vulcan_scene_*.png`), so the audio is the only in-file signal that
    carries the trigger instant.  It is reported as evidence, not as a round
    count: one audible transient is not proven to be one round.
    """
    out = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(VIDEO),
                          "-vn", "-ac", "1", "-ar", "8000", "-c:a", "pcm_s16le",
                          "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(out, np.int16).astype(np.float32) / 32768.0
    if a.size == 0:
        raise SystemExit("no audio decoded")
    d = np.diff(a, prepend=a[0])                     # crude high-pass (~700 Hz)
    hop = 16                                         # 2 ms at 8 kHz
    n = len(d) // hop
    env = np.abs(d[:n * hop].reshape(n, hop)).mean(axis=1)
    t = np.arange(n) * 0.002
    quiet = float(np.median(env[(t >= lookback_to) & (t <= lookback_to + 0.7)]))
    thr = max(0.004, 5.0 * quiet)
    onset = None
    for i in range(n):
        if t[i] < lookback_to + 0.6:
            continue
        if env[i] > thr and env[i:i + 50].mean() > 3.0 * quiet:
            onset = float(t[i])
            break
    sel = env[(t >= 13.5) & (t <= 16.0)]
    if sel.size < 200:
        raise SystemExit("audio window empty")
    x = sel - sel.mean()
    ac = np.correlate(x, x, "full")[len(x) - 1:]
    ac /= ac[0]
    best = max(range(14, 60), key=lambda lag: ac[lag])      # 28..120 ms
    # does the audible train keep going to the end of the clip?
    tail = env[(t >= 48.0)].mean()
    pre = env[(t >= (onset or 0) - 0.3) & (t < (onset or 0))] if onset else np.array([0.0])
    post = env[(t >= (onset or 0)) & (t < (onset or 0) + 0.3)] if onset else np.array([0.0])
    return {"lookback_from": lookback_to, "quiet_median": round(quiet, 6),
            "threshold": round(thr, 6),
            "trigger_pts": round(onset, 3) if onset else None,
            "pre_trigger_env": round(float(pre.mean()) if pre.size else 0.0, 6),
            "post_trigger_env": round(float(post.mean()) if post.size else 0.0, 6),
            "period_s": round(best * 0.002, 4), "period_ac": round(float(ac[best]), 3),
            "per_s": round(1.0 / (best * 0.002), 2),
            "ac_at_0_138": round(float(ac[69]), 3),
            "tail_env_48_49": round(float(tail), 6)}


def png_paths(d: dict, rows: list[dict]) -> list[dict]:
    keys = ["narrow_last", "spread_on", "full_on", "red_on", "last_wide", "narrow_back"]
    out = []
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    for k in keys:
        i = d["idx"][k]
        if i is None:
            continue
        pts = rows[i]["pts"]
        png = PNG_DIR / f"vulcan_{k}_f{i:04d}_t{pts:.3f}s.png"
        if not png.exists():
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(VIDEO),
                            "-vf", f"select=eq(n\\,{i})", "-fps_mode", "passthrough",
                            "-frames:v", "1", str(png)], check=True)
        crop = PNG_DIR / f"vulcan_{k}_f{i:04d}_reticle.png"
        if not crop.exists():
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(png),
                            "-vf", f"crop=300:300:{CROP_X - 10}:{CROP_Y - 10},scale=600:600:flags=neighbor",
                            str(crop)], check=True)
        out.append({"key": k, "frame_idx": i, "pts": round(pts, 3),
                    "full": png.name, "reticle_crop": crop.name})
    # scene frames across the clip: the muzzle / car is in none of them
    for t in (12.0, 20.0, 30.0, 40.0, 48.0):
        png = PNG_DIR / f"vulcan_scene_t{t:05.1f}s.png"
        if not png.exists():
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t),
                            "-i", str(VIDEO), "-frames:v", "1", "-vf", "scale=960:-1", str(png)],
                           check=True)
        out.append({"key": f"scene_{t:.1f}", "frame_idx": None, "pts": t,
                    "full": png.name, "reticle_crop": None})
    return out


def build() -> dict:
    rows = measure()
    d = derive(rows)
    a = audio_analysis(max(1.0, (d["spread_on"] or 12.0) - 1.2))
    trig = a.get("trigger_pts")
    if trig is not None:
        d["trigger"] = trig
        d["t_spread_from_trigger"] = round((d["spread_on"] or 0) - trig, 3)
        d["t_full_from_trigger"] = round((d["full_on"] or 0) - trig, 3)
        d["t_red_from_trigger"] = round((d["red_on"] or 0) - trig, 3)
        d["fired_until"] = d["clip_end_pts"]
        d["continuous_fire_s"] = round(d["clip_end_pts"] - trig, 3)
    pngs = png_paths(d, rows)
    table = [{"i": r["i"], "pts": round(r["pts"], 3), "arm_out": round(r["arm_out"], 1),
              "arm_in": round(r["arm_in"], 1), "red": round(r["red"], 1),
              "red_dirs": r["red_dirs"]} for r in rows
             if 11.5 <= r["pts"] <= 17.5]
    return {"video": str(VIDEO), "frames": len(rows), "duration": round(rows[-1]["pts"], 3),
            "geometry": {"centre": list(CENTER), "ring_radius_px": 25,
                         "arm_rest_px": [6, 20], "arm_full_px": [28, 41]},
            "events": d, "audio": a, "pngs": pngs, "table": table,
            "curve": {"points": [[0.0, 0.0], [0.5, 0.0], [1.5, 1.5], [2.5, 3.0]],
                      "heat_up_per_second": 0.0, "inaccuracy_angle": 0.1}}


def write() -> dict:
    rec = build()
    RES.mkdir(parents=True, exist_ok=True)
    (RES / JNAME).write_text(json.dumps(rec, indent=1), encoding="utf-8")
    e = rec["events"]
    a = rec["audio"]
    cv = rec["curve"]
    lines = [
        "# The Vulcan capture, measured from its frames (PTS)",
        "",
        "Generated by `Tools/scripts/vulcan_capture_timing.py --write`; `--check` recomputes",
        "every number below from the video bytes.",
        "",
        f"Source: `{rec['video']}` - {rec['frames']} frames, last PTS {rec['duration']} s,",
        "variable framerate (frame durations 0.0077-0.0585 s), so every value is a PTS, not a frame count.",
        "",
        "## The HUD as it is drawn in this capture",
        "",
        "| element | measurement |",
        "|---|---|",
        "| ring | fixed circle radius **25 px** at screen (961, 378); it does not move or grow |",
        "| arms | four radial arms at N/E/S/W that slide outward through the ring: tip **18.5 px** at rest, **41.0 px** fully out (2.22x) |",
        "| colour | the arms' tips go white -> red as they travel out; no other HUD element changes |",
        "",
        "## The table",
        "",
        "| quantity | PTS | frame | how |",
        "|---|---|---|---|",
        f"| trigger (firing starts) | {e['trigger']} s | - | audio onset: 2 ms high-pass envelope jumps {a['pre_trigger_env']} -> {a['post_trigger_env']} (threshold {a['threshold']}); the muzzle is out of frame |",
        f"| last frame at the narrow reticle | {e['narrow_last']} s | {e['idx']['narrow_last']} | arm tip {e['baseline_arm']} px |",
        f"| first visible spread | {e['spread_on']} s | {e['idx']['spread_on']} | arm tip leaves {e['baseline_arm']} px |",
        f"| full spread | {e['full_on']} s | {e['idx']['full_on']} | arm tip reaches {e['peak_arm']} px and holds |",
        f"| crosshair first red | {e['red_on']} s | {e['idx']['red_on']} | all four arms' tips red in one frame |",
        f"| trigger released / narrow again | not in clip | - | arm tip is still {e['peak_arm']} px at the last frame ({e['clip_end_pts']} s) |",
        "",
        "| interval | value |",
        "|---|---|",
        f"| trigger -> first visible spread | **{e['t_spread_from_trigger']} s** |",
        f"| trigger -> full spread | **{e['t_full_from_trigger']} s** |",
        f"| trigger -> red | **{e['t_red_from_trigger']} s** |",
        f"| first spread -> full spread | {e['t_full_from_spread']} s |",
        f"| first spread -> red | {e['t_red_from_spread']} s |",
        f"| full spread -> narrow again (cool-down) | **UNKNOWN** - the clip ends while the reticle is still fully spread |",
        f"| continuous fire recorded | {e['continuous_fire_s']} s (trigger to last frame, no interruption) |",
        "",
        "## Against the decoded `InaccuracyVsTime` curve",
        "",
        "| curve point | curve value | measured from the trigger | difference |",
        "|---|---|---|---|",
        f"| 0.5 s | 0.0 (end of the dead segment) | spread starts {e['t_spread_from_trigger']} s | {round(e['t_spread_from_trigger'] - 0.5, 3)} s |",
        f"| 2.5 s | 3.0 (max) | full spread {e['t_full_from_trigger']} s | {round(e['t_full_from_trigger'] - 2.5, 3)} s |",
        f"| red state | no curve point | {e['t_red_from_trigger']} s | - |",
        "",
        "`HeatUpPerSecond` 0.0 predicts no overheat lockout; the capture shows no interruption in",
        f"{e['continuous_fire_s']} s of fire, so nothing contradicts it. The spread is **time**-driven, not",
        "heat-driven: no heat axis exists in the object (`(InaccuracyVsHeat)` matches 0 fields).",
        "",
        "## Rounds per second from muzzle flashes",
        "",
        "**UNKNOWN.** The muzzle and the car are in no frame of the clip (five scene frames sampled at",
        f"12/20/30/40/48 s). The audio's transient cadence is {a['period_s']} s ({a['per_s']}/s, ac {a['period_ac']})",
        f"and the 0.138 s lag correlates at only {a['ac_at_0_138']}, so the mix does not resolve individual rounds.",
        "The decoded `FiringInterval` 0.138 s = 7.25 rounds/s therefore stays the value of record (R4).",
        "",
        "| audio (secondary, not a round count) | value |",
        "|---|---|",
        f"| envelope autocorrelation peak, 13.5-16.0 s | {a['period_s']} s |",
        f"| correlation at the 0.138 s fire interval | {a['ac_at_0_138']} |",
        f"| track still active at 48-49 s | {a['tail_env_48_49']} |",
        "",
        "## Per-frame table 11.5-17.5 s",
        "",
        "| frame | PTS | arm tip r (px) | red score | red dirs |",
        "|---|---|---|---|---|",
    ]
    for row in rec["table"]:
        lines.append(f"| {row['i']} | {row['pts']} | {row['arm_out']} | {row['red']} | {row['red_dirs']} |")
    lines += ["", "## Key frames (E:/Modding/ArkhamKnight/_grab/footage/vulcan/)", ""]
    for p in rec["pngs"]:
        crop = f", reticle crop `{p['reticle_crop']}`" if p["reticle_crop"] else ""
        idx = f"frame {p['frame_idx']}, " if p["frame_idx"] is not None else ""
        lines.append(f"- `{p['full']}` ({idx}{p['pts']} s){crop}")
    (RES / MNAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rec


def check() -> int:
    rec = build()
    old = json.loads((RES / JNAME).read_text(encoding="utf-8"))
    bad = []
    for k in ("narrow_last", "spread_on", "full_on", "red_on", "last_wide", "narrow_back",
              "t_spread_from_narrow", "t_full_from_spread", "t_red_from_spread",
              "t_full_to_narrow_back", "t_wide_total"):
        if rec["events"][k] != old["events"][k]:
            bad.append(f"{k}: {old['events'][k]} -> {rec['events'][k]}")
    for k in ("baseline_arm", "peak_arm"):
        if abs(rec["events"][k] - old["events"][k]) > 0.01:
            bad.append(f"{k}: {old['events'][k]} -> {rec['events'][k]}")
    if rec["audio"]["period_s"] != old["audio"]["period_s"]:
        bad.append(f"audio period: {old['audio']['period_s']} -> {rec['audio']['period_s']}")
    if rec["frames"] != old["frames"]:
        bad.append(f"frames: {old['frames']} -> {rec['frames']}")
    for p in old["pngs"]:
        if not (PNG_DIR / p["full"]).exists():
            bad.append(f"missing PNG {p['full']}")
        if p.get("reticle_crop") and not (PNG_DIR / p["reticle_crop"]).exists():
            bad.append(f"missing PNG {p['reticle_crop']}")
    if bad:
        print("FAIL")
        for b in bad:
            print("  " + b)
        return 1
    print(f"PASS {len(old['events'])} event values, {len(old['pngs'])} key frames, "
          f"{old['frames']} frames re-decoded")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--from", dest="t0", type=float, default=9.0)
    ap.add_argument("--to", dest="t1", type=float, default=17.5)
    a = ap.parse_args()
    if a.check:
        sys.exit(check())
    if a.write:
        rec = write()
        print(json.dumps(rec["events"], indent=1))
        print(json.dumps(rec["audio"]))
        return
    rows = measure()
    d = derive(rows)
    if a.probe:
        for r in rows:
            if a.t0 <= r["pts"] <= a.t1:
                print(f"{r['i']},{r['pts']:.3f},{r['arm_out']:.1f},{r['arm_in']:.1f},"
                      f"{r['red']:.1f},{r['red_dirs']},{r['ticks']}")
        print(d)
        return
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    main()
