"""v04_audio_004c.py - apply the two V-04 derived fixes in a NEW private tree (bm-004c).

What this does, in order:

1. takes the two edits `Builds/bm-RC1/verify/audio_diag.md` derived and expresses them on the
   build's *inputs* (never on an existing Builds tree): the `weapons#408` source WAV scaled by
   0.731139 (-2.72 dB) and the `vehicles#279` source WAV with its first 408 frames dropped;
2. rebuilds both payloads through `bm_audio.payload()` with the manifest's own loop-fill gain and
   the build's own re-level loop (copy of `bm_audio.build()` lines 294-299), so the bytes come from
   B-11's code path rather than a re-implementation;
3. splices them into copies of the audited banks in `Builds/bm-004c/banks/` (bm-RC1's bank bytes are
   the input and are not touched) and writes `Working/Audio/bm_bank_manifest_v2.json`;
4. re-runs V-04's two gates - BS.1770 loudness against the vanilla slot (+-1 LU) and the loop wrap
   step (-40 dBFS) - per sample, with `v04_audio.decode/steps/seam/p99` unchanged, and writes
   `Builds/bm-004c/verify/audio_004c.{json,md}`.

Never writes into an existing `Builds/bm-*` tree, never runs `install.ps1`, never launches the game.

Usage
    python Tools/scripts/v04_audio_004c.py --write
    python Tools/scripts/v04_audio_004c.py --check
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_audio                                      # noqa: E402  (payload, mono_48k, fsb_of, VGMPATH)
import bmak_audio_features as g15                    # noqa: E402  (integrated_lufs)
import v04_audio                                     # noqa: E402  (decode, steps, seam, p99, db)

CARD = "V-04c"
RC = os.path.join(ROOT, "Builds", "bm-RC1")          # the audited build: read-only input
SRC_BANKS = os.path.join(RC, "drop", "sound", "fmod_banks")
OUT = os.path.join(ROOT, "Builds", "bm-004c")
OUT_BANKS = os.path.join(OUT, "banks")
VERIFY = os.path.join(OUT, "verify")
MANIFEST = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest.json")
MANIFEST_V2 = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest_v2.json")
RATE = 48000
LU_TOL = v04_audio.LU_TOL                            # +-1.0 LU, the card's band
CLICK_DBFS = v04_audio.CLICK_DBFS                    # -40.0 dBFS, the card's click limit
SCHEMA = 1

# the derived fixes, verbatim from Builds/bm-RC1/verify/audio_diag.md "Fixes - proposed, NOT applied"
FIXES = {
    ("weapons", 408): {"kind": "gain", "factor": 10 ** (-2.72 / 20),   # 0.7311390835
                       "want_stereo_lufs": -5.30, "want_mono_lufs": -8.31,
                       "want_payload_sha256":
                       "12b8cf4eb96b4e2477e2ed55ee311fb5e317568bbcbdbca0648e4415e4fe8424"},
    ("vehicles", 279): {"kind": "pre_roll", "drop_frames": 408,
                        "want_stereo_lufs": -20.45, "want_mono_lufs": -20.45,
                        "want_payload_sha256":
                        "117f8aa25c973a41347a48b38e044b9468aa358e29036c9865d71711dcfe94d3"},
}
WANT_PADDED = {("vehicles", 279): 149911, ("weapons", 408): 80213}


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def source_array(slot: dict) -> tuple[np.ndarray, dict]:
    """The fixed payload source for one slot, derived from its WAV (no repo file is edited)."""
    key = (slot["bank"], int(slot["index"]))
    fx = FIXES[key]
    src = bm_audio.mono_48k(slot["source"], slot.get("span_s"), False)
    if fx["kind"] == "gain":
        src = src * fx["factor"]
    elif fx["kind"] == "pre_roll":
        src = src[int(fx["drop_frames"]):]
    return src, fx


def rebuild(slot: dict) -> dict:
    """`bm_audio.build()`'s payload pipeline for one slot, byte for byte (incl. its re-level loop)."""
    src, fx = source_array(slot)
    gain = float(slot["measured"]["gain_db_loopfill"])
    is_loop = "_loop" in slot["name"]
    want = slot["measured"]["map_delivered_lufs"]
    q, meas = bm_audio.payload(src, gain, int(slot["frames"]), loop=is_loop)
    re_level = 0
    if is_loop and meas["padded_frames"] and want is not None:
        for _ in range(3):
            corr = float(want) - meas["delivered_lufs"]
            if corr >= 0:
                break
            gain += corr
            re_level += 1
            q, meas = bm_audio.payload(src, gain, int(slot["frames"]), loop=True)
        meas["map_delivered_lufs"] = float(want)
        meas["gain_db_loopfill"] = round(gain, 3)
        meas["loop_fill"] = (f"tiled with a {bm_audio.XFADE}-frame equal-power crossfade (V-04)"
                             + (f" after a {fx['drop_frames']}-frame pre-roll trim (V-04 diag)"
                                if fx["kind"] == "pre_roll" else ""))
    body = np.clip(q * 32768.0, -32768, 32767).astype(np.int16)
    if int(slot["channels"]) > 1:
        body = np.repeat(body[:, None], int(slot["channels"]), axis=1).reshape(-1)
    raw = body.tobytes()
    mono_raw = np.clip(q * 32768.0, -32768, 32767).astype(np.int16).tobytes()
    return {"payload": raw, "mono_sha256": sha(mono_raw), "measured": meas, "gain": gain,
            "re_level": re_level,
            "src_frames": int(len(src)), "stereo_lufs": g15.integrated_lufs(
                np.repeat(q[:, None], int(slot["channels"]), axis=1), RATE),
            "mono_lufs": float(meas["delivered_lufs"]), "sha256": sha(raw),
            "fx": fx}


def build(write: bool) -> dict:
    mf = json.load(open(MANIFEST, encoding="utf-8"))
    doc = copy.deepcopy(mf)
    slots = {(s["bank"], int(s["index"])): s for s in mf["slots"]}
    targets = sorted(FIXES)

    # 1. the two payloads, rebuilt through B-11's pipeline
    rebuilt = {k: rebuild(slots[k]) for k in targets}

    # 2. the private banks: bm-RC1's bytes in, bm-004c's bytes out
    vanilla_banks = {b: (v.get("file") if os.path.isabs(v.get("file") or "")
                         else os.path.join(ROOT, v.get("file") or mf["inputs"]["banks"][b]))
                     for b, v in mf["bank"].items()}
    written = {}
    out = {}
    for bank in sorted({k[0] for k in targets}):
        src_path = os.path.join(SRC_BANKS, f"{bank}.bank")
        before = open(src_path, "rb").read()
        raw = bytearray(before)
        base, fsb = bm_audio.fsb_of(bytes(raw))
        for (b, idx) in [k for k in targets if k[0] == bank]:
            r = rebuilt[(b, idx)]
            e = fsb.samples[idx - 1]
            data = bytes(e.data)
            hlen = len(data) - e.samples * int(slots[(b, idx)]["channels"]) * 2
            if hlen < 0 or hlen > 4096:
                raise SystemExit(f"{bank} #{idx}: header length {hlen}")
            if bytes(raw).count(data) != 1:
                raise SystemExit(f"{bank} #{idx}: sample data not unique")
            at = bytes(raw).find(data)
            raw[at:at + len(data)] = data[:hlen] + r["payload"]
            r["data_offset"] = at - base
            r["bytes"] = len(r["payload"])
            r["channel_mode"] = ("mono-replicated" if int(slots[(b, idx)]["channels"]) > 1
                                 else "mono")
        out[bank] = bytes(raw)
        written[bank] = {"bytes": len(raw), "sha256": sha(bytes(raw)),
                         "source_sha256": sha(before), "samples": len(fsb.samples),
                         "unchanged_size": len(raw) == len(before)}
        if write:
            os.makedirs(OUT_BANKS, exist_ok=True)
            with open(os.path.join(OUT_BANKS, f"{bank}.bank"), "wb") as f:
                f.write(bytes(raw))

    # 3. manifest v2: the derived changes, every other field carried over byte for byte
    for (b, idx) in targets:
        r = rebuilt[(b, idx)]
        s = doc["slots"][[i for i, x in enumerate(doc["slots"])
                          if (x["bank"], int(x["index"])) == (b, idx)][0]]
        s["measured"] = {k: v for k, v in r["measured"].items()}
        s["measured"].update({"delivered_lufs": round(r["mono_lufs"], 2),
                              "clip_pct": r["measured"]["clip_pct"],
                              "padded_frames": r["measured"]["padded_frames"],
                              "src_frames": r["src_frames"],
                              "map_delivered_lufs": float(s["measured_old"]["map_delivered_lufs"])
                              if "measured_old" in s else float(mf["slots"][
                                  [i for i, x in enumerate(mf["slots"])
                                   if (x["bank"], int(x["index"])) == (b, idx)][0]]
                                  ["measured"]["map_delivered_lufs"]),
                              "gain_db_loopfill": round(r["gain"], 3)})
        s["measured"].setdefault("loop_fill", r["measured"].get("loop_fill"))
        s["payload_sha256"] = r["sha256"]
        s["data_offset"] = r["data_offset"]
        s["bytes"] = r["bytes"]
        s["channel_mode"] = r["channel_mode"]
    for w in doc["written"]:
        if w["bank"] in written:
            w["sha256"] = written[w["bank"]]["sha256"]
            w["bytes"] = written[w["bank"]]["bytes"]
    doc["generator"] = (str(mf.get("generator", "")) +
                        " | v2: V-04c derived fixes applied (weapons#408 -2.72 dB source, "
                        "vehicles#279 408-frame pre-roll) into Builds/bm-004c")
    doc["card_v2"] = CARD
    doc["source_manifest"] = {"path": rel(MANIFEST), "sha256": sha(open(MANIFEST, "rb").read())}
    doc["tree"] = rel(OUT)

    # 4. V-04's gates on the new bytes, per sample
    gates = []
    for (b, idx) in sorted(slots):
        p = os.path.join(OUT_BANKS if write else VERIFY, f"{b}.bank")
        if not write:   # check: still gate the tree on disk
            p = os.path.join(OUT_BANKS, f"{b}.bank")
        built = v04_audio.decode(p, idx)
        van = v04_audio.decode(vanilla_banks[b], idx)
        st_b = g15.integrated_lufs(built["pcm"], built["rate"])
        st_v = g15.integrated_lufs(van["pcm"], van["rate"])
        delta = st_b - st_v
        click = v04_audio.seam(built["pcm"])
        van_click = v04_audio.seam(van["pcm"])
        is_loop = "_loop" in built["name"]
        # the record's leading bytes are its 32-byte codec header, decoded as frames: the diag's
        # payload-domain seam is measured after them, the gate keeps v04_audio's full-record seam
        chan = int(slots[(b, idx)]["channels"])
        rec = bytes(bm_audio.fsb_of(open(p, "rb").read())[1].samples[idx - 1].data)
        hlen = max(0, len(rec) - built["frames"] * chan * 2)
        shift = hlen // (2 * chan)
        wrap_payload = v04_audio.seam(built["pcm"][shift:])
        p99b = v04_audio.p99(v04_audio.steps(built["pcm"]))
        loop_ok, verdict = None, "one-shot"
        if is_loop:
            fail = click > CLICK_DBFS and click > p99b
            loop_ok = not fail
            if fail:
                verdict = "RED: click at the only available loop boundary"
            elif click <= CLICK_DBFS:
                verdict = "pass: below the -40 dBFS threshold"
            else:
                verdict = ("pass: above -40 dBFS but inside the payload's own step "
                           "distribution (not a click)")
        gates.append({
            "bank": b, "index": idx, "name": built["name"],
            "loop": is_loop,
            "built_lufs": round(st_b, 2), "vanilla_lufs": round(st_v, 2),
            "delta_lu": round(delta, 2), "loudness_ok": abs(delta) <= LU_TOL,
            "wrap_dbfs": click, "vanilla_wrap_dbfs": van_click,
            "wrap_payload_dbfs": wrap_payload, "header_shift_frames": shift,
            "interior_p99_dbfs": p99b,
            "loop_ok": loop_ok, "verdict": verdict,
            "fixed": (b, idx) in FIXES,
            "built_sha256": built["sha256"],
        })
    lo = [g for g in gates if g["loop"]]
    doc_out = {"schema": SCHEMA, "card": CARD, "tree": rel(OUT), "source": rel(RC),
               "manifest": rel(MANIFEST_V2), "gates": gates,
               "derived": {f"{b}#{i}": {"payload_sha256": rebuilt[(b, i)]["sha256"],
                                        "mono_sha256": rebuilt[(b, i)]["mono_sha256"],
                                        "want_sha256": FIXES[(b, i)]["want_payload_sha256"],
                                        "sha_domain": (
                                            "2-ch body" if rebuilt[(b, i)]["sha256"] ==
                                            FIXES[(b, i)]["want_payload_sha256"] else
                                            "mono body" if rebuilt[(b, i)]["mono_sha256"] ==
                                            FIXES[(b, i)]["want_payload_sha256"] else
                                            "neither"),
                                        "sha_matches": FIXES[(b, i)]["want_payload_sha256"] in
                                        (rebuilt[(b, i)]["sha256"],
                                         rebuilt[(b, i)]["mono_sha256"]),
                                        "mono_lufs": round(rebuilt[(b, i)]["mono_lufs"], 2),
                                        "want_mono_lufs": FIXES[(b, i)]["want_mono_lufs"],
                                        "stereo_lufs": round(rebuilt[(b, i)]["stereo_lufs"], 2),
                                        "want_stereo_lufs": FIXES[(b, i)]["want_stereo_lufs"],
                                        "gain_db_loopfill": round(rebuilt[(b, i)]["gain"], 3),
                                        "re_level_passes": rebuilt[(b, i)]["re_level"],
                                        "padded_frames": rebuilt[(b, i)]["measured"]["padded_frames"],
                                        "want_padded_frames": WANT_PADDED.get((b, i)),
                                        "src_frames": rebuilt[(b, i)]["src_frames"]}
                              for (b, i) in targets},
               "written": written,
               "summary": {"samples": len(gates),
                           "loudness_ok": sum(g["loudness_ok"] for g in gates),
                           "loop_ok": sum(1 for g in lo if g["loop_ok"]),
                           "loop_samples": len(lo),
                           "red": [f"{g['bank']}#{g['index']}" for g in gates
                                   if not g["loudness_ok"] or g["loop_ok"] is False]}}
    if write:
        os.makedirs(OUT, exist_ok=True)
        os.makedirs(VERIFY, exist_ok=True)
        with open(MANIFEST_V2, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1, sort_keys=True)
            f.write("\n")
        with open(os.path.join(VERIFY, "audio_004c.json"), "w", encoding="utf-8") as f:
            json.dump(doc_out, f, indent=1, sort_keys=True)
            f.write("\n")
        with open(os.path.join(VERIFY, "audio_004c.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(render_md(doc_out))
    return doc_out


def render_md(d: dict) -> str:
    s = d["summary"]
    lines = [
        "# V-04 gates on bm-004c (the two derived fixes, applied)", "",
        f"Generated by `Tools/scripts/v04_audio_004c.py --write`; `--check` rebuilds this file and",
        f"`Builds/bm-004c/verify/audio_004c.json` on disk and compares them byte for byte.", "",
        f"**STATUS: {s['loudness_ok']}/{s['samples']} loudness gates pass, "
        f"{s['loop_ok']}/{s['loop_samples']} loop-wrap gates pass; red: "
        f"{', '.join(s['red']) if s['red'] else 'none'}.**", "",
        f"Banks in `{d['tree']}/banks/` are copies of `{d['source']}`'s bank bytes with only the two",
        f"fixed payloads spliced (`v04_audio.decode` reads them, no game involved).", "",
        "## Loudness (BS.1770-4 gated integrated, as stored) and loop wrap step", "",
        "| sample | loop | built LUFS | vanilla LUFS | delta | gate | wrap dBFS | payload "
        "wrap | p99 | gate |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for g in d["gates"]:
        lines.append(
            f"| `{g['bank']}#{g['index']}` {g['name']} | {'yes' if g['loop'] else 'no'} | "
            f"{g['built_lufs']} | {g['vanilla_lufs']} | {g['delta_lu']:+} | "
            f"{'PASS' if g['loudness_ok'] else 'RED'} | {g['wrap_dbfs']} | "
            f"{g['wrap_payload_dbfs']} | {g['interior_p99_dbfs']} | "
            f"{'-' if g['loop_ok'] is None else ('PASS' if g['loop_ok'] else 'RED')}: "
            f"{g['verdict']} |")
    lines += ["", "## The two fixes, against the diag's predicted values", "",
              "| slot | payload sha256 = predicted | mono LUFS (want) | stereo LUFS (want) | "
              "fill gain | padded frames (want) |", "|---|---|---|---|---|---|"]
    for k, v in sorted(d["derived"].items()):
        lines.append(f"| `{k}` | {'yes' if v['sha_matches'] else 'NO'} | "
                     f"{v['mono_lufs']} ({v['want_mono_lufs']}) | "
                     f"{v['stereo_lufs']} ({v['want_stereo_lufs']}) | "
                     f"{v['gain_db_loopfill']} | {v['padded_frames']} ({v['want_padded_frames']}) |")
    lines += ["", "## Limits", "",
              "* The measure is BS.1770 gated loudness as stored; the diag records that plain RMS",
              "  flips the `vehicles#279` verdict - that dependence is unchanged by this card.",
              "* No install, no game: `install.ps1` was not run and nothing was copied to a",
              "  dropzone. Whether the loops sound right in play is phase Q.",
              "* `weapons#408` has no GUID: the vanilla slot at the same bank+index is the oracle,",
              "  not a proven event.", ""]
    return "\n".join(lines)


def check() -> int:
    if not os.path.isdir(OUT):
        print(f"FAIL: {rel(OUT)} missing (run --write)")
        return 1
    d = build(write=False)
    fails = []
    for name, path in (("manifests", MANIFEST_V2),
                       ("json", os.path.join(VERIFY, "audio_004c.json")),
                       ("md", os.path.join(VERIFY, "audio_004c.md"))):
        if not os.path.exists(path):
            fails.append(f"{rel(path)} missing (run --write)")
    if fails:
        print("FAIL: " + "; ".join(fails))
        return 1
    on_disk = json.load(open(os.path.join(VERIFY, "audio_004c.json"), encoding="utf-8"))
    if on_disk != json.loads(json.dumps(d)):
        diff = v04_audio.diff_paths(on_disk, json.loads(json.dumps(d)))
        print("FAIL: verify/audio_004c.json differs from the re-derived document:")
        for x in diff[:12]:
            print("  " + x)
        return 1
    txt = open(os.path.join(VERIFY, "audio_004c.md"), encoding="utf-8").read()
    if txt != render_md(d):
        print("FAIL: verify/audio_004c.md differs from the regenerated text")
        return 1
    mf = json.load(open(MANIFEST_V2, encoding="utf-8"))
    for (b, idx) in FIXES:
        s = [x for x in mf["slots"] if (x["bank"], int(x["index"])) == (b, idx)][0]
        if s["payload_sha256"] != d["derived"][f"{b}#{idx}"]["payload_sha256"]:
            print(f"FAIL: manifest_v2 {b}#{idx} payload_sha256 drifted")
            return 1
    print(f"CHECK PASS - {d['summary']['loudness_ok']}/{d['summary']['samples']} loudness, "
          f"{d['summary']['loop_ok']}/{d['summary']['loop_samples']} loop-wrap, "
          f"red: {', '.join(d['summary']['red']) if d['summary']['red'] else 'none'}")
    return 0


def main() -> int:
    import argparse
    g = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g.add_argument("--write", action="store_true", help="build bm-004c, manifest_v2, verify/*")
    g.add_argument("--check", action="store_true", help="re-derive and compare (no writes)")
    a = g.parse_args()
    if not (a.write or a.check):
        g.print_help()
        return 2
    if a.write:
        d = build(write=True)
        s = d["summary"]
        print(f"wrote {rel(MANIFEST_V2)}, {rel(OUT)}/banks, {rel(VERIFY)}/audio_004c.*")
        print(f"{s['loudness_ok']}/{s['samples']} loudness, "
              f"{s['loop_ok']}/{s['loop_samples']} loop-wrap, red: "
              f"{', '.join(s['red']) if s['red'] else 'none'}")
        for k, v in sorted(d["derived"].items()):
            print(f"  {k}: sha_matches={v['sha_matches']} mono={v['mono_lufs']} "
                  f"stereo={v['stereo_lufs']} gain={v['gain_db_loopfill']}")
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
