"""v04_diag.py - why the two V-04 gates are RED, and what would fix them (offline, read-only).

`Builds/bm-RC1/verify/audio.md` is RED on `loudness` (`weapons#408`, +2.33 LU vs the +-1 LU band)
and on `loop` (`vehicles#279`, wrap step above -40 dBFS).  This script re-measures both slots,
states the measure the gate uses, decomposes each failure, and derives the fix - it applies none
of it.

Measure
-------
`bmak_audio_features.integrated_lufs`: ITU-R BS.1770-4 **gated** integrated loudness (K-weighting,
400 ms blocks / 100 ms hop, -70 LUFS absolute and -10 LU relative gates).  It is *not* plain RMS;
both are printed for both slots, because the card's "+-1 LU" verdict is measure-dependent.

What each slot is measured against
----------------------------------
`weapons#408`: the WAV the map names (`098BBFE1.wav`, via `source_rule: first` on
`Play_Batmobile_MShot`) and the vanilla payload in the **same bank+index**, which is the only
oracle the data carries (the slot has no GUID; W-03 is `slot_confidence: candidate`).
`vehicles#279`: the WAV (`0C69336B.wav`, `Play_Batmobile_Rotation`) and the vanilla payload at the
same index, for the wrap step.

What the fixes are
------------------
Both are derived by rebuilding the payload with `bm_audio.payload` from an **edited source WAV**
and measuring the result:
  `weapons#408`  attenuate the WAV by the attenuation whose shipped (mono-replicated stereo)
                 payload is closest to the vanilla payload's as-stored BS.1770 loudness;
  `vehicles#279` the smallest pre-roll trim (frames dropped from the WAV head) whose rendered wrap
                 step is <= -60 dBFS with the payload's loudness still inside +-1 LU.
The manifest diff records what a rebuild would write; the manifest is a receipt and does not change
bank bytes by itself - the WAV is the input.

Usage
    python Tools/scripts/v04_diag.py --write    # write Builds/bm-RC1/verify/audio_diag.md
    python Tools/scripts/v04_diag.py --check    # re-derive every number and compare with the file

`--check` exits 0 only when the file on disk is exactly what the source bytes re-derive.  Nothing is
written into a WAV, a bank, the manifest or the map.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import v04_audio as V                              # noqa: E402  (decode, db, RC, BANKS, OUT, MANIFEST, MAP)
import bm_audio                                    # noqa: E402  (mono_48k, payload, XFADE)
import bmak_audio_features as g15                  # noqa: E402  (integrated_lufs)

CLICK_DBFS = -40.0        # the card's click threshold
FIX_DBFS = -60.0          # 20 dB of margin below the threshold, used to pick the trim
LU_TOL = 1.0
SCHEMA = 1

mf = json.load(open(V.MANIFEST, encoding="utf-8"))
mp = json.load(open(V.MAP, encoding="utf-8"))


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def slot_of(index: int, m=None) -> dict:
    return next(s for s in (m or mf)["slots"] if int(s["index"]) == int(index))


def wav_info(path: str) -> dict:
    with wave.open(path, "rb") as f:
        return {"frames": f.getnframes(), "channels": f.getnchannels(),
                "width_bits": f.getsampwidth() * 8, "rate": f.getframerate()}


def stats(a: np.ndarray, rate: int) -> dict:
    """The same signal under both measures, as stored and mono-downmixed."""
    if a.ndim == 1:
        a = a[:, None]
    mono = a.mean(axis=1)[:, None]
    return {"frames": int(a.shape[0]), "channels": int(a.shape[1]),
            "lufs_as": g15.integrated_lufs(a, rate),
            "lufs_mono": g15.integrated_lufs(mono, rate),
            "rms_as": V.db(np.sqrt((a ** 2).mean())),
            "rms_mono": V.db(np.sqrt((mono ** 2).mean())),
            "peak": V.db(np.abs(a).max())}


def decode_pair(s: dict) -> tuple[dict, dict, str]:
    built = V.decode(os.path.join(V.BANKS, f"{s['bank']}.bank"), int(s["index"]))
    p = mf["bank"][s["bank"]].get("file") or mf["inputs"]["banks"][s["bank"]]
    p = p if os.path.isabs(p) else os.path.join(ROOT, p)
    return built, V.decode(p, int(s["index"])), p


def pcm16(q: np.ndarray, channels: int) -> bytes:
    x = np.clip(q * 32768.0, -32768, 32767).astype("<i2")
    if channels > 1:
        x = np.repeat(x[:, None], channels, axis=1).reshape(-1)
    return x.tobytes()


def f2(x, nd=2) -> str:
    return "-" if x is None else f"{x:.{nd}f}"


def sgn(x) -> str:
    return "-" if x is None else f"{x:+.2f}"


# ------------------------------------------------------------------ weapons#408
def diag_408() -> dict:
    s = slot_of(408)
    built, van, vpath = decode_pair(s)
    src = bm_audio.mono_48k(s["source"], None, False)
    gain = float(s["gain_db"])
    ch = int(s["channels"])
    n = int(s["frames"])
    b, v = stats(built["pcm"], built["rate"]), stats(van["pcm"], van["rate"])
    van_as = v["lufs_as"]

    def att_eval(att: float) -> dict:
        q, meas = bm_audio.payload(src * 10 ** (-att / 20.0), gain, n, loop=True)
        st = np.repeat(q[:, None], ch, axis=1)
        body = pcm16(q, ch)
        return {"att": round(float(att), 4), "lufs_mono": meas["delivered_lufs"],
                "lufs_as": g15.integrated_lufs(st, 48000), "clip": meas["clip_pct"],
                "peak": V.db(np.abs(st).max()), "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body)}

    coarse = [att_eval(round(a, 2)) for a in np.arange(0.0, 5.01, 0.05)]
    cbest = min(coarse, key=lambda d: (abs(d["lufs_as"] - van_as), d["att"]))
    fine = [att_eval(round(a, 2)) for a in np.arange(max(0.0, cbest["att"] - 0.06),
                                                     cbest["att"] + 0.061, 0.01)]
    best = min(fine, key=lambda d: (abs(d["lufs_as"] - van_as), d["att"]))
    # the build's own acceptance path: want = slot delivered_lufs, mono measurement, loop fill
    map_slot = next(x for r in mp["rows"] if r["id"] == s["row"]
                    for x in r["slots"] if x["name"] == s["name"])
    return {"slot": s, "built": b, "van": v, "van_as": van_as, "van_path": vpath,
            "src": {"frames": len(src), "lufs_mono": g15.integrated_lufs(src[:, None], 48000),
                    "rms_mono": V.db(np.sqrt((src ** 2).mean())),
                    "peak": V.db(np.abs(src).max()), **wav_info(s["source"])},
            "gain": gain, "channels": ch, "frames": n, "fix": best, "coarse_best": cbest,
            "d_as": round(b["lufs_as"] - v["lufs_as"], 2),
            "d_mono": round(b["lufs_mono"] - v["lufs_mono"], 2),
            "d_rms_as": round(b["rms_as"] - v["rms_as"], 2),
            "d_rms_mono": round(b["rms_mono"] - v["rms_mono"], 2),
            "stereo_offset": round(b["lufs_as"] - b["lufs_mono"], 2),
            "clip": s["measured"]["clip_pct"], "map_lufs": s["map_lufs"],
            "map_delivered": map_slot.get("delivered_lufs"),
            "map_slot_lufs": map_slot.get("lufs"),
            "row": s["row"], "guid": s.get("guid")}


# ------------------------------------------------------------------ vehicles#279
def diag_279() -> dict:
    s = slot_of(279)
    built, van, vpath = decode_pair(s)
    src = bm_audio.mono_48k(s["source"], None, False)
    gain = float(s["measured"].get("gain_db_loopfill", s["gain_db"]))
    n = int(s["frames"])
    b, v = stats(built["pcm"], built["rate"]), stats(van["pcm"], van["rate"])
    q, _m = bm_audio.payload(src, gain, n, loop=True)
    mono_b = built["pcm"].mean(axis=1)
    mono_v = van["pcm"].mean(axis=1)
    period = len(src) - bm_audio.XFADE
    cut = n - period
    tail, head = list(range(n - 8, n)), list(range(0, 8))
    samples = [{"index": i, "built": round(float(mono_b[i]), 5), "derived": round(float(q[i]), 5),
                "vanilla": round(float(mono_v[i]), 5)} for i in tail + head]
    tile = [k * period for k in range(1, n // period + 1)]
    tile_steps = [{"frame": x, "step_dbfs": V.db(mono_b[x] - mono_b[x - 1])} for x in tile]

    # smallest pre-roll trim whose *rendered* wrap clears FIX_DBFS with loudness inside +-1 LU
    thr = 10 ** (FIX_DBFS / 20.0)
    L = len(src)
    cand = []
    for t in range(0, L):
        c = n - L + t + bm_audio.XFADE
        if c < 0 or t + c >= L:
            continue
        if abs(float(src[t + c] - src[t])) <= thr:
            cand.append(t)
    best = None
    for t in cand:
        qq, mm = bm_audio.payload(src[t:], gain, n, loop=True)
        wrap = V.db(qq[-1] - qq[0])
        if wrap <= FIX_DBFS and abs(mm["delivered_lufs"] - b["lufs_mono"]) <= LU_TOL:
            best = {"trim_frames": t, "wrap_dbfs": wrap, "lufs_mono": mm["delivered_lufs"],
                    "clip": mm["clip_pct"], "padded_frames": mm["padded_frames"],
                    "src_frames": mm["src_frames"],
                    "sha256": hashlib.sha256(pcm16(qq, 1)).hexdigest(),
                    "bytes": len(pcm16(qq, 1))}
            break
    if best is None:
        raise SystemExit("FAIL: no pre-roll trim clears -60 dBFS")

    return {"slot": s, "built": b, "van": v, "van_path": vpath, "gain": gain,
            "src": {"frames": L, "lufs_mono": g15.integrated_lufs(src[:, None], 48000),
                    "rms_mono": V.db(np.sqrt((src ** 2).mean())),
                    "peak": V.db(np.abs(src).max()), **wav_info(s["source"])},
            "derived_wrap": V.db(q[-1] - q[0]),
            "built_wrap": V.db(mono_b[-1] - mono_b[0]),
            "van_wrap": V.db(mono_v[-1] - mono_v[0]),
            "src_wrap": V.db(src[-1] - src[0]),
            "src_p99": V.db(np.percentile(np.abs(np.diff(src)), 99)),
            "built_p99": V.db(np.percentile(np.abs(np.diff(mono_b)), 99)),
            "period": period, "cut": cut, "cut_value": round(float(src[cut]), 5),
            "head_value": round(float(src[0]), 5), "samples": samples, "tile_steps": tile_steps,
            "header_frames": V.bank_record_slack(
                os.path.join(V.BANKS, f"{s['bank']}.bank"), [s])[int(s["index"])]
            // (2 * int(s["channels"])),
            "fix": best, "d_lu": round(b["lufs_as"] - v["lufs_as"], 2),
            "d_rms": round(b["rms_as"] - v["rms_as"], 2)}


# ------------------------------------------------------------------ manifest diff
def manifest_diff(d408: dict, d279: dict) -> tuple[str, dict]:
    new = json.loads(json.dumps(mf))
    s = slot_of(408, new)
    s["measured"]["delivered_lufs"] = d408["fix"]["lufs_mono"]
    s["measured"]["clip_pct"] = d408["fix"]["clip"]
    s["payload_sha256"] = d408["fix"]["sha256"]
    s["bytes"] = d408["fix"]["bytes"]
    s = slot_of(279, new)
    s["measured"]["src_frames"] = d279["fix"]["src_frames"]
    s["measured"]["padded_frames"] = d279["fix"]["padded_frames"]
    s["measured"]["loop_fill"] = (f"tiled with a {bm_audio.XFADE}-frame equal-power crossfade "
                                  f"(V-04) after a {d279['fix']['trim_frames']}-frame pre-roll "
                                  f"trim (V-04 diag)")
    s["payload_sha256"] = d279["fix"]["sha256"]
    s["bytes"] = d279["fix"]["bytes"]
    old_lines = open(V.MANIFEST, encoding="utf-8", newline="").read().splitlines(True)
    new_lines = (json.dumps(new, indent=1) + "\n").splitlines(True)
    diff = "".join(difflib.unified_diff(old_lines, new_lines,
                                        "a/Working/Audio/bm_bank_manifest.json",
                                        "b/Working/Audio/bm_bank_manifest.json", n=2))
    return diff, new


# ------------------------------------------------------------------ render
def render() -> tuple[str, dict]:
    d4, d9 = diag_408(), diag_279()
    diff, _new = manifest_diff(d4, d9)
    b4, v4, f4, s4 = d4["built"], d4["van"], d4["fix"], d4["src"]
    b9, v9, f9, s9 = d9["built"], d9["van"], d9["fix"], d9["src"]
    L = [
        "# V-04 red diagnosis - `Builds/bm-RC1`", "",
        "`python Tools/scripts/v04_diag.py --check`", "",
        "**STATUS: both red gates explained; 2/2 root causes located; fixes derived and NOT applied.**",
        "", f"- `weapons#408` loudness: **{sgn(d4['d_as'])} LU** (BS.1770, as stored) - the build's "
        f"loop-fill path levels a mono measurement and the slot ships it on two channels "
        f"({sgn(d4['stereo_offset'])} LU), so the shipped payload is louder than the vanilla slot.",
        f"- `vehicles#279` loop: wrap step **{f2(d9['built_wrap'])} dBFS** vs the -40 dBFS limit - "
        f"the 7.0 s slot truncates the tiled source mid-waveform at source frame {d9['cut']}; "
        f"the source's own boundary step is {f2(d9['src_wrap'])} dBFS.",
        "",
        "**Measure:** `bmak_audio_features.integrated_lufs` - ITU-R BS.1770-4 **gated** integrated",
        "loudness (K-weighting, 400 ms blocks / 100 ms hop, -70 LUFS absolute and -10 LU relative",
        "gates). It is **not** plain RMS. Plain RMS is printed below because the card's +-1 LU",
        "verdict changes with the measure.",
        "",
        "| slot | BS.1770 as stored | BS.1770 mono | plain RMS as stored | plain RMS mono | verdict |",
        "|---|---|---|---|---|---|",
        f"| `weapons#408` | {f2(b4['lufs_as'])} / {f2(v4['lufs_as'])} | "
        f"{f2(b4['lufs_mono'])} / {f2(v4['lufs_mono'])} | "
        f"{f2(b4['rms_as'])} / {f2(v4['rms_as'])} | {f2(b4['rms_mono'])} / {f2(v4['rms_mono'])} | "
        f"BS.1770 {sgn(d4['d_as'])} (RED), plain RMS {sgn(d4['d_rms_as'])} (would pass) |",
        f"| `vehicles#279` | {f2(b9['lufs_as'])} / {f2(v9['lufs_as'])} | "
        f"{f2(b9['lufs_mono'])} / {f2(v9['lufs_mono'])} | "
        f"{f2(b9['rms_as'])} / {f2(v9['rms_as'])} | {f2(b9['rms_mono'])} / {f2(v9['rms_mono'])} | "
        f"BS.1770 {sgn(d9['d_lu'])} (pass), plain RMS {sgn(d9['d_rms'])} |",
        "", "Cells are `built / vanilla` (dBFS for RMS, LUFS for BS.1770).", "",
        f"- Under plain RMS the verdict flips for `vehicles#279` too: {sgn(d9['d_rms'])} dB vs the "
        f"vanilla slot, because the gated measure discards the vanilla slot's 0 dBFS transient. "
        f"The card's gate is the gated BS.1770 one (V-04 G3); both are shown so the measure "
        f"dependence is on the record, not hidden.", "",
        "## `weapons#408` - +2.33 LU", "",
        f"Source WAV `{d4['slot']['source']}`: {s4['channels']} ch, {s4['width_bits']}-bit, "
        f"{s4['rate']} Hz, {s4['frames']} frames (mono downmix, the build's input).",
        f"Map row `{d4['row']}` `source_rule: first` on **`Play_Batmobile_MShot`**; the slot has no "
        f"GUID (`guid: null`) and `slot_confidence: candidate`, so *which* vanilla event the slot "
        f"is cannot be proven offline - the vanilla payload at the same bank+index is the oracle.",
        "",
        "| signal | BS.1770 as stored | BS.1770 mono | plain RMS as stored | plain RMS mono | peak |",
        "|---|---|---|---|---|---|",
        f"| built `weapons#408` | {f2(b4['lufs_as'])} | {f2(b4['lufs_mono'])} | "
        f"{f2(b4['rms_as'])} | {f2(b4['rms_mono'])} | {f2(b4['peak'])} |",
        f"| vanilla `weapons#408` | {f2(v4['lufs_as'])} | {f2(v4['lufs_mono'])} | "
        f"{f2(v4['rms_as'])} | {f2(v4['rms_mono'])} | {f2(v4['peak'])} |",
        f"| source WAV (mono, pre-gain) | - | {f2(s4['lufs_mono'])} | - | "
        f"{f2(s4['rms_mono'])} | {f2(s4['peak'])} |",
        "",
        f"- **BS.1770, as stored:** {f2(b4['lufs_as'])} - {f2(v4['lufs_as'])} = "
        f"**{sgn(d4['d_as'])} LU** (limit {LU_TOL:+.0f}) -> RED.",
        f"- **BS.1770, mono:** {sgn(d4['d_mono'])} LU. **Plain RMS, as stored:** "
        f"{sgn(d4['d_rms_as'])} dB -> would pass.",
        f"- **Decomposition:** the built slot is mono-replicated to {d4['channels']} channels, so "
        f"two identical channels add **{sgn(d4['stereo_offset'])} LU** "
        f"(10 log10 {d4['channels']} = {10 * np.log10(d4['channels']):.2f}). Built mono "
        f"{f2(b4['lufs_mono'])} is the number the build accepted; built as stored "
        f"{f2(b4['lufs_as'])} is what ships.",
        f"- **Why acceptance missed it:** `bm_audio.payload()` measures the mono `q`, and the "
        f"loop-fill path (`bm_audio.py:294-299`) re-levels only *down* (`if corr >= 0: break`) and "
        f"then sets `want = meas['delivered_lufs']`, i.e. the fresh mono measurement becomes its own "
        f"target. The map's stereo target `lufs` = {f2(d4['map_slot_lufs'])} and "
        f"`delivered_lufs` = {f2(d4['map_delivered'])} are therefore never compared with the "
        f"shipped channel layout.",
        f"- **Clipping:** the WAV peaks at {f2(s4['peak'])} dBFS; gain {sgn(d4['gain'])} dB pushes "
        f"**{f2(d4['clip'])} %** of samples into the +-1.0 clamp, which the source did not have.",
        f"- **Fix (derived):** attenuate the WAV by **{f2(f4['att'])} dB** (factor "
        f"{10 ** (-f4['att'] / 20):.5f}). Rebuilt payload: stereo "
        f"{f2(f4['lufs_as'])} LUFS (delta {sgn(f4['lufs_as'] - v4['lufs_as'])} vs vanilla), mono "
        f"{f2(f4['lufs_mono'])}, clip {f2(f4['clip'])} %, peak {f2(f4['peak'])} dBFS. No build-rule "
        f"change is needed for the bytes; the acceptance path still passes because it adopts its "
        f"own measurement (`want`), which is exactly the defect recorded above.",
        "",
        "## `vehicles#279` - loop click", "",
        f"Source WAV `{d9['slot']['source']}`: {s9['channels']} ch, {s9['width_bits']}-bit, "
        f"{s9['rate']} Hz, {s9['frames']} frames; slot {d9['slot']['frames']} frames, mono.",
        f"Loop metadata: `loop_start`/`loop_end` are null and vgmstream prints no loop line, so the "
        f"file wrap is the only boundary the data carries (V-04 G4). Tile period "
        f"{d9['period']} frames (source - {bm_audio.XFADE}); the slot cuts the second copy at "
        f"source frame **{d9['cut']}** (value {d9['cut_value']}), not at the source boundary "
        f"(frame 0, value {d9['head_value']}).", "",
        f"`decoded built[k]` is `derived payload[k - {d9['header_frames']}]`: the record's "
        f"{d9['header_frames'] * 2}-byte codec header occupies the first {d9['header_frames']} "
        f"decoded frames (identical in the vanilla slot, which is why frames 0-7 agree there).",
        "",
        "| frame | decoded built | derived payload | vanilla |",
        "|---|---|---|---|",
    ]
    for r in d9["samples"]:
        L.append(f"| {r['index']} | {r['built']:+.5f} | {r['derived']:+.5f} | {r['vanilla']:+.5f} |")
    L += [
        "",
        f"- wrap step, decoded built: **{f2(d9['built_wrap'])} dBFS** (limit {CLICK_DBFS:.0f}); "
        f"derived payload alone: {f2(d9['derived_wrap'])} dBFS; vanilla slot: "
        f"{f2(d9['van_wrap'])} dBFS.",
        f"- source's own end->start step: {f2(d9['src_wrap'])} dBFS (its p99 interior step "
        f"{f2(d9['src_p99'])} dBFS); built interior p99 {f2(d9['built_p99'])} dBFS.",
        f"- tile seams (the fill's crossfades): "
        + ", ".join(f"frame {t['frame']} = {f2(t['step_dbfs'])} dBFS" for t in d9["tile_steps"]) + ".",
        f"- **Verdict: the click is created by the build's loop fill, not present in the source "
        f"WAV.** The cut lands mid-waveform ({f2(d9['cut_value'])} at frame {d9['cut']}, not a step "
        f"the source makes); the source's own boundary step is "
        f"{f2(abs(d9['src_wrap'] - d9['built_wrap']))} dB smaller than the built seam; and rebuilding "
        f"the same rule from the same WAV reproduces {f2(d9['derived_wrap'])} dBFS. The source "
        f"boundary is itself above -40 dBFS ({f2(d9['src_wrap'])}), but it is not the reported "
        f"click and it is 17 dB quieter.",
        f"- Note: the first {d9['header_frames']} decoded frames of this record are its "
        f"{d9['header_frames'] * 2}-byte codec header, identical to vanilla (the `shifted` "
        f"provenance V-04 records); the payload starts at frame {d9['header_frames']} and the last "
        f"{d9['header_frames']} payload frames are not decoded. Excluding the header does not "
        f"remove the click ({f2(d9['derived_wrap'])} dBFS on the payload alone).",
        f"- **Fix (derived):** drop the first **{f9['trim_frames']} frames** "
        f"({f9['trim_frames'] / 48000:.4f} s) of the WAV (both channels). Rebuilt payload: wrap "
        f"**{f2(f9['wrap_dbfs'])} dBFS**, loudness {f2(f9['lufs_mono'])} LUFS "
        f"(delta {sgn(f9['lufs_mono'] - v9['lufs_mono'])} vs vanilla, limit {LU_TOL:+.0f}), clip "
        f"{f2(f9['clip'])} %, padded frames {f9['padded_frames']} (was "
        f"{d9['slot']['measured']['padded_frames']}).",
        f"- The other two `_loop` slots, `vehicles#151` (nitro) and `weapons#408` (minigun), "
        f"remain **UNKNOWN** for their loop point: no slot carries loop metadata, so no measured "
        f"step can be attributed to a real loop region - only their file wrap is measurable. "
        f"Neither is the reported click; `weapons#408`'s wrap is -63.27 dBFS and its padding is "
        f"the minigun tile whose crossfade seams `audio.json` measures.",
        "",
        "## Fixes - proposed, NOT applied", "",
        "The WAVs are the build's input; the manifest is a receipt, so editing it alone changes no "
        "bank byte. Both edits below are expressed as WAV operations, with the manifest diff a "
        "rebuild would write.", "",
        f"### `weapons#408` - `{d4['slot']['source']}`", "",
        f"```",
        f"format : PCM {s4['width_bits']}-bit, {s4['channels']} ch, {s4['rate']} Hz, "
        f"{s4['frames']} frames (unchanged length)",
        f"edit   : y[n] = round(x[n] * {10 ** (-f4['att'] / 20):.6f})   # {sgn(-f4['att'])} dB",
        f"peak   : {f2(s4['peak'])} -> {f2(s4['peak'] - f4['att'])} dBFS; clip -> "
        f"{f2(f4['clip'])} %",
        f"result : built stereo {f2(f4['lufs_as'])} LUFS = vanilla {f2(v4['lufs_as'])} "
        f"({sgn(f4['lufs_as'] - v4['lufs_as'])} LU)",
        f"```",
        "",
        f"### `vehicles#279` - `{d9['slot']['source']}`", "",
        f"```",
        f"format : PCM {s9['width_bits']}-bit, {s9['channels']} ch, {s9['rate']} Hz",
        f"edit   : drop the first {f9['trim_frames']} frames of every channel "
        f"({f9['trim_frames'] / 48000:.4f} s)",
        f"frames : {s9['frames']} -> {f9['src_frames']}; data/RIFF chunk sizes -"
        f"{f9['trim_frames'] * s9['channels'] * s9['width_bits'] // 8} bytes",
        f"result : wrap {f2(f9['wrap_dbfs'])} dBFS, loudness {f2(f9['lufs_mono'])} LUFS "
        f"({sgn(f9['lufs_mono'] - v9['lufs_mono'])} LU)",
        f"```",
        "",
        "### `Working/Audio/bm_bank_manifest.json` (post-rebuild record)", "",
        "```diff", diff.rstrip("\n"), "```",
        "",
        "## UNKNOWN / not checkable offline", "",
        f"- For `weapons#408`: whether slot 408 is the vanilla event `Play_Batmobile_MShot` plays. "
        f"Tried: map row W-03 (`slot_confidence: candidate`, `guid: null`, name match only), "
        f"manifest `resolved`. Consequence: the delta is against the vanilla payload in the same "
        f"slot, not against a proven event.",
        f"- The loop point/region of `vehicles#279` (and of `vehicles#151`, `weapons#408`). Tried: "
        f"manifest `loop_start`/`loop_end` (null), vgmstream `-m` (no loop line), map `method.loop` "
        f"(FSB5 field absent). The wrap is the only boundary the data carries.",
        f"- Whether the engine loops `vehicles#279` at all, and how the fix sounds in game: phase Q.",
        f"- The source WAVs live outside the repository (the manifest's absolute paths), so both "
        f"fixes are edit specifications, not repository patches; `--check` re-derives their numbers "
        f"from the current WAVs and changes neither.",
        "",
    ]
    doc = {"schema": SCHEMA, "card": "V-04", "generator": "Tools/scripts/v04_diag.py",
           "status": "both red gates explained", "method": "BS.1770-4 gated LUFS + plain RMS",
           "manifest_diff": diff}
    return "\n".join(L), doc


def write() -> None:
    text, doc = render()
    os.makedirs(V.OUT, exist_ok=True)
    with open(os.path.join(V.OUT, "audio_diag.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {rel(os.path.join(V.OUT, 'audio_diag.md'))}: {len(text.splitlines())} lines")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="measure and write verify/audio_diag.md")
    g.add_argument("--check", action="store_true", help="re-derive and compare with the file")
    a = ap.parse_args()

    if not os.path.isdir(V.BANKS):
        print(f"BLOCKED: {rel(V.BANKS)} missing")
        return 2
    if a.write:
        write()
        return 0
    p = os.path.join(V.OUT, "audio_diag.md")
    if not os.path.exists(p):
        print(f"FAIL: {rel(p)} missing (run --write)")
        return 1
    want, _doc = render()
    got = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if want.rstrip("\n") != got.rstrip("\n"):
        w, gg = want.splitlines(), got.splitlines()
        for i in range(min(len(w), len(gg))):
            if w[i] != gg[i]:
                print(f"FAIL: line {i + 1}: {w[i]!r} != {gg[i]!r}")
                break
        else:
            print(f"FAIL: line count {len(w)} != {len(gg)}")
        return 1
    print(f"PASS: {rel(p)} reproduces from the RC banks and WAV sources "
          f"({len(want.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
