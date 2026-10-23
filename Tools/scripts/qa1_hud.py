#!/usr/bin/env python3
"""QA-1: read the JC3 HUD speedometer out of a recorded take.

JC3 exposes no telemetry, so the HUD is the only oracle for the T-5 behaviour
rows. The speedometer is a fixed-position gauge with the speed in km/h in a
fixed font. This script cuts that gauge out of the video, splits the digits,
learns the ten digit shapes from a handful of frames whose value the operator
read by eye, and then turns the whole take into a speed trace at the sampling
rate.

    python qa1_hud.py crops --video take1.mkv --out work --fps 5
    python qa1_hud.py build --crops work/hud --known known.json
    python qa1_hud.py trace --crops work/hud --csv trace.csv --fps 5
    python qa1_hud.py runs  --csv trace.csv --fps 5

`known.json` is {"<seconds>": <km/h>} for frames you have looked at, e.g.
{"170": 0, "195": 135}. `build` writes `digits.json` (the templates) and a
`unknown.png` sheet of any glyph it could not label, so a take with a digit the
known frames did not cover fails loudly instead of guessing.

Everything downstream is re-runnable: same video, same known frames, same
numbers.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:  # pragma: no cover
    sys.exit("needs pillow and numpy:  uv run --with pillow --with numpy python qa1_hud.py")

# Gauge crop in source-video pixels: JC3 renders 1280x720 into the top-left of
# a 1920x1080 capture; the gauge sits at x 100..290, y 540..660.
CROP = "190:120:100:540"
SCALE = (380, 240)
# The numerals inside the scaled crop; "KM/H" and the tick ring stay outside.
BAND = (70, 104, 220, 192)
GLYPH = (26, 34)
PITCH = 42.0  # px advance of one digit in the scaled crop
SAME = 0.16  # XOR fraction under which a glyph is the same digit


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("ffmpeg not on PATH (um win record needs it too)")
    return exe


def crop_frames(video: str, out: str, fps: float) -> None:
    hud = os.path.join(out, "hud")
    os.makedirs(hud, exist_ok=True)
    for p in glob.glob(os.path.join(hud, "*.png")):
        os.remove(p)
    vf = f"fps={fps},crop={CROP},scale={SCALE[0]}:{SCALE[1]}:flags=neighbor"
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", video, "-vf", vf,
                        "-start_number", "0", os.path.join(hud, "h_%05d.png"), "-y"])
    if r.returncode != 0:
        sys.exit("ffmpeg failed")
    print(hud)


def smooth(a: np.ndarray) -> np.ndarray:
    """Blur then re-threshold, so antialiasing jitter does not split a digit."""
    im = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    return np.asarray(im) > 110


def glyphs_of(path: str) -> list[np.ndarray]:
    """The digits of the km/h readout, left to right.

    The HUD font is tabular and its digits often touch, so column runs are not
    glyphs: the runs tall enough to be a numeral give the string's extent, and
    the extent is divided by the known digit pitch.
    """
    a = np.asarray(Image.open(path).convert("L").crop(BAND))
    mask = a > 185

    # Vertical: the numerals are the tallest ink block; "KM/H" sits below them
    # with a blank row in between, so taking the band's full height would feed
    # K/M/H strokes into the digit bitmaps.
    rows = mask.any(axis=1)
    blocks = _runs(rows)
    if not blocks:
        return []
    top, bottom = max(blocks, key=lambda b: b[1] - b[0])
    if bottom - top < 35:
        return []  # too short to be a numeral at this scale

    # Horizontal: group the ink columns into words and keep the widest one, so
    # the gauge ring and the shift icon on either side cannot stretch the block.
    cols = mask[top:bottom].any(axis=0)
    words = _runs(cols)
    if not words:
        return []
    merged: list[tuple[int, int]] = []
    for x0, x1 in words:
        if merged and x0 - merged[-1][1] <= 12:
            merged[-1] = (merged[-1][0], x1)
        else:
            merged.append((x0, x1))
    left, right = max(merged, key=lambda b: b[1] - b[0])
    if right - left < 20:
        return []

    k = max(1, min(3, int(round((right - left) / PITCH))))
    out = []
    for i in range(k):
        xa = left + (right - left) * i // k
        xb = left + (right - left) * (i + 1) // k
        cell = mask[top:bottom, xa:xb]
        ys = np.flatnonzero(cell.any(axis=1))
        xs = np.flatnonzero(cell.any(axis=0))
        if ys.size == 0 or xs.size == 0:
            return []
        cell = cell[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
        g = Image.fromarray((cell * 255).astype(np.uint8)).resize(GLYPH, Image.BILINEAR)
        out.append(smooth(np.asarray(g) > 110))
    return out


def _runs(flags: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous True runs of a 1-D boolean array."""
    out: list[tuple[int, int]] = []
    start = None
    for i, on in enumerate(flags):
        if on and start is None:
            start = i
        elif not on and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(flags)))
    return out


def xor(a: np.ndarray, b: np.ndarray) -> float:
    return float((a ^ b).sum()) / float(a.size)


def dist(g: np.ndarray, tmpl: dict[str, list[np.ndarray]]) -> tuple[str | None, float]:
    best, bd = None, 9e9
    for ch, reps in tmpl.items():
        for r in reps:
            d = xor(g, r)
            if d < bd:
                best, bd = ch, d
    return best, bd


def build(crops: str, known: str, fps: float) -> dict:
    with open(known) as fh:
        vals = {float(k): str(v) for k, v in json.load(fh).items()}
    files = sorted(glob.glob(os.path.join(crops, "h_*.png")))
    if not files:
        sys.exit(f"no frames in {crops}; run `crops` first")
    tmpl: dict[str, list[np.ndarray]] = {}
    for t, val in sorted(vals.items()):
        i = int(round(t * fps))
        if i >= len(files):
            sys.exit(f"known frame t={t}s is past the end of the take")
        gs = glyphs_of(files[i])
        if len(gs) != len(val):
            print(f"  skip t={t}s: read {val} but found {len(gs)} glyphs")
            continue
        for g, ch in zip(gs, val):
            reps = tmpl.setdefault(ch, [])
            if not any(xor(g, r) < SAME for r in reps):
                reps.append(g)
        print(f"  t={t:6.1f}s  {val:>4}  {len(gs)} glyphs")

    # Every glyph in the take must now match some template.
    unknown: list[np.ndarray] = []
    for f in files:
        for g in glyphs_of(f):
            ch, d = dist(g, tmpl)
            if ch is None or d > SAME:
                if not any(xor(g, u) < SAME for u in unknown):
                    unknown.append(g)
    out = os.path.join(os.path.dirname(os.path.abspath(crops)), "digits.json")
    payload = {ch: [{"shape": list(r.shape),
                     "bits": np.packbits(r.reshape(-1)).tolist()} for r in reps]
               for ch, reps in tmpl.items()}
    with open(out, "w") as fh:
        json.dump(payload, fh)
    print(f"templates for {''.join(sorted(tmpl))} -> {out}")
    if unknown:
        sheet = Image.new("L", (8 * 60, ((len(unknown) + 7) // 8) * 70), 0)
        d = ImageDraw.Draw(sheet)
        for n, g in enumerate(unknown):
            im = Image.fromarray((g * 255).astype(np.uint8)).resize((36, 48), Image.NEAREST)
            x, y = (n % 8) * 60, (n // 8) * 70
            sheet.paste(im, (x + 4, y + 4))
            d.text((x + 4, y + 56), str(n), fill=255)
        p = os.path.join(os.path.dirname(os.path.abspath(crops)), "unknown.png")
        sheet.save(p)
        print(f"WARNING {len(unknown)} glyph(s) match nothing -> {p}; add known frames")
    else:
        print("every glyph in the take is covered by the templates")
    return tmpl


def load(crops: str) -> dict[str, list[np.ndarray]]:
    p = os.path.join(os.path.dirname(os.path.abspath(crops)), "digits.json")
    if not os.path.exists(p):
        sys.exit(f"{p} missing; run `build` first")
    with open(p) as fh:
        raw = json.load(fh)
    tmpl: dict[str, list[np.ndarray]] = {}
    for ch, reps in raw.items():
        for r in reps:
            shape = tuple(r["shape"])
            tmpl.setdefault(ch, []).append(
                np.unpackbits(np.array(r["bits"], dtype=np.uint8))[:int(np.prod(shape))]
                .reshape(shape).astype(bool))
    return tmpl


def trace(crops: str, csv: str, fps: float, t0: float = 0.0,
          t1: float = 1e9) -> list[tuple[float, int | None]]:
    tmpl = load(crops)
    files = sorted(glob.glob(os.path.join(crops, "h_*.png")))
    rows: list[tuple[float, int | None]] = []
    for n, f in enumerate(files):
        if not (t0 <= n / fps <= t1):
            continue
        gs = glyphs_of(f)
        val: int | None = None
        if 1 <= len(gs) <= 3:
            chars = []
            for g in gs:
                ch, d = dist(g, tmpl)
                if ch is None or d > SAME:
                    chars = []
                    break
                chars.append(ch)
            if chars:
                v = int("".join(chars))
                if v <= 400:
                    val = v
        rows.append((n / fps, val))
    with open(csv, "w") as fh:
        fh.write("t,speed\n")
        for t, v in rows:
            fh.write(f"{t:.2f},{'' if v is None else v}\n")
    got = sum(1 for _, v in rows if v is not None)
    print(f"{got}/{len(rows)} frames read -> {csv}")
    return rows


def measure(csv: str, out: str) -> dict:
    """The numbers T-5's behaviour rows need, as a JSON receipt."""
    rows: list[tuple[float, float]] = []
    with open(csv) as fh:
        next(fh)
        for line in fh:
            t, v = line.strip().split(",")
            if v:
                rows.append((float(t), float(v)))
    if len(rows) < 10:
        sys.exit("trace too short to measure")

    def crossing(target: float) -> float | None:
        for (t0, v0), (t1, v1) in zip(rows, rows[1:]):
            if v0 < target <= v1:
                return t0 + (target - v0) / (v1 - v0) * (t1 - t0)
        return None

    def dist(t_a: float, t_b: float) -> float:
        d = 0.0
        for (t0, v0), (t1, v1) in zip(rows, rows[1:]):
            if t0 < t_a:
                continue
            if t1 > t_b:
                break
            d += (v0 + v1) / 2 / 3.6 * (t1 - t0)
        return d

    peak_t, peak = max(rows, key=lambda r: r[1])
    out_d: dict = {"csv": os.path.abspath(csv), "samples": len(rows),
                   "from": rows[0][0], "to": rows[-1][0],
                   "peak_kmh": peak, "peak_t": round(peak_t, 2)}

    start = crossing(2)
    t100 = crossing(100)
    if start is not None and t100 is not None:
        out_d["launch"] = {
            "moving_t": round(start, 2), "t100": round(t100, 2),
            "s": round(t100 - start, 2), "distance_m": round(dist(start, t100), 1),
            "t60": round(crossing(60) - start, 2) if crossing(60) else None,
            "peak_reached": peak,
        }

    # Deceleration segments. A segment is a strictly falling run that loses at
    # least 15 km/h; whether it reached a standstill is recorded, not required,
    # because a take that leaves the road cannot produce a clean stop.
    brakes = []
    i = 0
    while i < len(rows):
        j = i
        while j + 1 < len(rows) and rows[j + 1][1] < rows[j][1]:
            j += 1
        drop = rows[i][1] - rows[j][1]
        if j > i and drop >= 15:
            dur = rows[j][0] - rows[i][0]
            brakes.append({
                "from_kmh": rows[i][1], "to_kmh": rows[j][1],
                "t0": round(rows[i][0], 2), "t1": round(rows[j][0], 2),
                "s": round(dur, 2), "distance_m": round(dist(rows[i][0], rows[j][0]), 1),
                "decel_ms2": round(drop / 3.6 / max(dur, .2), 2),
                "to_standstill": rows[j][1] <= 5,
            })
            i = j
        i += 1
    out_d["brake_segments"] = brakes
    with open(out, "w") as fh:
        json.dump(out_d, fh, indent=1)
    print(json.dumps(out_d, indent=1))
    return out_d


def runs(csv: str) -> None:
    rows: list[tuple[float, float]] = []
    with open(csv) as fh:
        next(fh)
        for line in fh:
            t, v = line.strip().split(",")
            if v:
                rows.append((float(t), float(v)))
    if not rows:
        sys.exit("empty trace")
    print(f"{len(rows)} samples  {rows[0][0]:.1f}-{rows[-1][0]:.1f}s  "
          f"max {max(v for _, v in rows):.0f} km/h")

    def at(target: float) -> float | None:
        return next((t for t, v in rows if v >= target), None)

    # Acceleration runs: a climb that starts at a standstill.
    i = 0
    while i < len(rows):
        t0, v0 = rows[i]
        if v0 <= 5:
            j, peak = i, v0
            while j + 1 < len(rows) and rows[j + 1][1] >= peak - 8:
                j += 1
                peak = max(peak, rows[j][1])
            if peak >= 100:
                seg = rows[i:j + 1]
                tp = at(0)  # global, replaced below
                t100 = next((t for t, v in seg if v >= 100), None)
                if t100 is not None:
                    line = (f"  accel @ {t0:6.1f}s  start {v0:3.0f} -> 100 in "
                            f"{t100 - t0:5.2f}s")
                    for th in (150, 160, 180):
                        th_t = next((t for t, v in seg if v >= th), None)
                        if th_t is not None:
                            line += f" | {th} @ {th_t - t0:5.2f}s"
                    line += f" | peak {peak:.0f} @ {seg[-1][0]:.1f}s"
                    # distance covered from the start to 100 km/h
                    d = 0.0
                    prev = seg[0]
                    for cur in seg:
                        if cur[0] > t100:
                            break
                        d += (prev[1] + cur[1]) / 2 / 3.6 * (cur[0] - prev[0])
                        prev = cur
                    print(line + f" | {d:.0f} m to 100")
                i = j
        i += 1

    # Braking runs: monotonically falling from >= 80 to a standstill.
    i = 0
    while i < len(rows):
        t0, v0 = rows[i]
        if v0 >= 80:
            j = i
            while j + 1 < len(rows) and rows[j + 1][1] <= rows[j][1] + 1:
                j += 1
            if rows[j][1] <= 5 and j > i:
                seg = rows[i:j + 1]
                d = sum((seg[k][1] + seg[k + 1][1]) / 2 / 3.6 * (seg[k + 1][0] - seg[k][0])
                        for k in range(len(seg) - 1))
                dur = rows[j][0] - t0
                t100 = next((t for t, v in seg if v <= 100), t0)
                print(f"  brake @ {t0:6.1f}s  {v0:.0f} -> 0 in {dur:5.2f}s  "
                      f"{d:.0f} m  ({v0 / 3.6 / max(dur, .2):.1f} m/s2 avg)  "
                      f"100 km/h at {t100:6.2f}s")
                i = j
        i += 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crops", help="1) cut HUD crops out of a take")
    c.add_argument("--video", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--fps", type=float, default=5.0)
    b = sub.add_parser("build", help="2) learn the digits from frames you read")
    b.add_argument("--crops", required=True)
    b.add_argument("--known", required=True)
    b.add_argument("--fps", type=float, default=5.0)
    t = sub.add_parser("trace", help="3) whole take -> speed trace")
    t.add_argument("--crops", required=True)
    t.add_argument("--csv", default="trace.csv")
    t.add_argument("--fps", type=float, default=5.0)
    t.add_argument("--from", dest="t0", type=float, default=0.0)
    t.add_argument("--to", dest="t1", type=float, default=1e9)
    m = sub.add_parser("measure", help="4) the T-5 behaviour numbers as JSON")
    m.add_argument("--csv", required=True)
    m.add_argument("--json", default="qa1_measure.json")
    r = sub.add_parser("runs", help="5) acceleration and braking runs")
    r.add_argument("--csv", required=True)
    a = ap.parse_args()
    if a.cmd == "crops":
        crop_frames(a.video, a.out, a.fps)
    elif a.cmd == "build":
        build(a.crops, a.known, a.fps)
    elif a.cmd == "trace":
        trace(a.crops, a.csv, a.fps, a.t0, a.t1)
    elif a.cmd == "measure":
        measure(a.csv, a.json)
    else:
        runs(a.csv)


if __name__ == "__main__":
    main()
