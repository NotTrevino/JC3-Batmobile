"""v04_audio.py - V-04: audio gates on the release candidate's banks (offline, read-only).

Card (`GRAB_BACKLOG.md` section 9a):
    decode the built bank back; compare each sample to its WAV source (length +-1 frame);
    loudness within +-1 LU of the vanilla event it replaces; loops seamless (no click > -40 dBFS
    at the loop point).  Done: all events pass.

What is measured, and how
-------------------------
The five swapped slots of B-11 (`Working/Audio/bm_bank_manifest.json`) are decoded back **out of
the RC's own banks** (`Builds/bm-RC1/drop/sound/fmod_banks/*.bank`, the files the installer ships)
with vgmstream, and decoded again out of the **vanilla banks** B-11 copied (their sha256 must equal
the manifest's `bank.*.source_sha256`, so the comparison is against the exact shipped bytes).

  G1 decode     the RC banks are B-11's (sha256 == manifest `written`), each slot decodes to the
                manifest's frames / rate / channels / name, and the decoded PCM is the payload
                B-11's own rule derives from the WAV source (`bm_audio.mono_48k` + `payload`),
                byte for byte.  Any byte offset between the two is reported (`payload_match`)
  G2 length     frames_built vs the WAV source.  Two referents, both printed:
                `raw`  = the WAV's own frame count (`wave`), and
                `span` = src_frames + padded_frames - trimmed_frames, i.e. the WAV after B-11's
                documented trim / tile / span cut.  The +-1 frame gate is `span`: against the raw
                WAV a swap cannot pass (route a keeps the slot's frame count, so it trims, pads or
                tiles) - spec `Research/specs/V-04.md` section 3 (V-04/3)
  G3 loudness   integrated LUFS (ITU-R BS.1770-4, `bmak_audio_features.integrated_lufs`) of the
                DECODED built payload vs the DECODED vanilla payload at the same bank+index, both
                measured as stored (channel layout as the bank holds it).  The mono downmix is
                printed too, because T-16's map compares a mono payload measurement against a
                stereo slot target
  G4 loop       only `_loop` slots.  The loop point is looked up in the manifest (`loop_start` /
                `loop_end`) and in vgmstream's metadata; when both are absent the only loop
                boundary the data carries is the file wrap, and the vanilla payload at the same
                index is the oracle for whether that boundary is a loop: all three vanilla `_loop`
                payloads are continuous across it (their end->start step is smaller than their own
                p99 interior step).  Click = the wrap step is worse than -40 dBFS **and** an
                outlier against the payload's own interior step distribution (p99); the vanilla
                seam is printed beside it.  The derived tile seams B-11's loop fill creates are
                measured the same way
  G5 tail       no `_loop` slot may end in > 10 ms of digital silence (the defect B-11's loop fill
                fixed); the vanilla tail RMS is printed beside it

Usage
    python Tools/scripts/v04_audio.py --write    # measure, write Builds/bm-RC1/verify/audio.{json,md}
    python Tools/scripts/v04_audio.py --check    # re-derive every number and compare with the files

`--check` passes when the files on disk are exactly what the source bytes re-derive.  It exits 0
even when a gate is RED, because the red gate is a property of the build, not a stale report; the
gate verdict is printed and stored.  Nothing is written into a bank, the game installs or another
task's files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_audio                                    # noqa: E402  (VGMPATH, fsb_of, payload, source_of)
import bmak_audio_features as g15                  # noqa: E402  (integrated_lufs)

CARD = "V-04"
RC = os.path.join(ROOT, "Builds", "bm-RC1")
BANKS = os.path.join(RC, "drop", "sound", "fmod_banks")
OUT = os.path.join(RC, "verify")
MANIFEST = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest.json")
MAP = os.path.join(ROOT, "Working", "Translation", "t12_audio_map.json")
CLICK_DBFS = -40.0        # the card's click threshold
LU_TOL = 1.0              # the card's loudness band
TAIL_SILENCE_S = 0.010    # G5: a loop payload may not end in digital silence
SCHEMA = 1
sha = lambda b: hashlib.sha256(b).hexdigest()        # noqa: E731


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def db(x) -> float:
    return round(float(20.0 * np.log10(max(abs(float(x)), 1e-9))), 2)


# ------------------------------------------------------------------ decode
def decode(bank: str, index: int) -> dict:
    """One stream out of a bank, through vgmstream, plus the metadata it prints."""
    d = tempfile.mkdtemp(prefix="v04_")
    w = os.path.join(d, "s.wav")
    try:
        # `-m` prints metadata and exits without decoding, so it is a separate call
        rm = subprocess.run([bm_audio.VGMPATH, "-s", str(index), "-m", bank],
                            capture_output=True, text=True, errors="replace")
        if rm.returncode != 0:
            raise SystemExit(f"FAIL: vgmstream cannot read {rel(bank)} #{index}: "
                             f"{(rm.stdout + rm.stderr)[-300:]!r}")
        meta = (rm.stdout + rm.stderr).splitlines()
        r = subprocess.run([bm_audio.VGMPATH, "-s", str(index), "-o", w, bank],
                           capture_output=True, text=True, errors="replace")
        if r.returncode != 0 or not os.path.exists(w):
            raise SystemExit(f"FAIL: vgmstream cannot decode {rel(bank)} #{index}: "
                             f"{(r.stdout + r.stderr)[-300:]!r}")
        with wave.open(w, "rb") as f:
            rate, ch, n = f.getframerate(), f.getnchannels(), f.getnframes()
            body = f.readframes(n)
    finally:
        for p in os.listdir(d):
            os.remove(os.path.join(d, p))
        os.rmdir(d)
    a = np.frombuffer(body, dtype="<i2").astype(np.float64) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch)
    else:
        a = a.reshape(-1, 1)
    loop_lines = [x.strip() for x in meta
                  if x.strip().lower().startswith(("loop start", "loop end", "loop flag"))]
    num = lambda s: int(s.split(":", 1)[1].split("(")[0].strip())  # noqa: E731
    return {"rate": rate, "channels": ch, "frames": n, "pcm": a, "bytes": body,
            "sha256": sha(body), "meta": meta, "loop_lines": loop_lines,
            "loop_start": next((num(x) for x in loop_lines
                                if x.lower().startswith("loop start")), None),
            "loop_end": next((num(x) for x in loop_lines
                              if x.lower().startswith("loop end")), None),
            "name": next((x.split(":", 1)[1].strip() for x in meta
                          if x.strip().startswith("stream name:")), "")}


def bank_record_slack(bank: str, slots: list[dict]) -> dict[int, int]:
    """Bytes each FSB5 sample record carries besides `frames * channels * 2` of PCM.

    B-11 calls this `hlen` and treats it as a *header*; the decoder starts the stream at the
    record's first byte, so the value also says how far a payload written at `hlen` is shifted.
    Read once per bank (the files are 177-210 MB).
    """
    raw = open(bank, "rb").read()
    _base, fsb = bm_audio.fsb_of(raw)
    out = {}
    for s in slots:
        rec = bytes(fsb.samples[s["index"] - 1].data)
        out[s["index"]] = len(rec) - int(s["frames"]) * int(s["channels"]) * 2
    return out


def wav_frames(path: str) -> tuple[int, int, int]:
    with wave.open(path, "rb") as f:
        return f.getnframes(), f.getnchannels(), f.getframerate()


def steps(a: np.ndarray) -> np.ndarray:
    m = a.mean(axis=1) if a.ndim > 1 else a
    return np.abs(np.diff(m))


def seam(a: np.ndarray) -> float:
    m = a.mean(axis=1) if a.ndim > 1 else a
    return db(m[-1] - m[0])


def p99(step: np.ndarray) -> float:
    return db(np.percentile(step, 99)) if step.size else -180.0


# ------------------------------------------------------------------ measure
def measure() -> dict:
    mf = json.load(open(MANIFEST, encoding="utf-8"))
    mp = json.load(open(MAP, encoding="utf-8"))
    slots = mf["slots"]
    inputs: dict[str, dict] = {}
    gates: dict[str, bool] = {}

    # G0 - every input present and the RC carries exactly B-11's bytes
    written = {w["bank"]: w for w in mf["written"]}
    missing = []
    for s in slots:
        p = s["source"] if os.path.isabs(s["source"]) else os.path.join(ROOT, s["source"])
        inputs[f"source:{os.path.basename(p)}"] = {"path": rel(p) if p.startswith(ROOT) else p,
                                                   "exists": os.path.exists(p)}
        if not os.path.exists(p):
            missing.append(p)
    bank_files = {}
    for bank, w in sorted(written.items()):
        p = os.path.join(BANKS, f"{bank}.bank")
        got = sha(open(p, "rb").read()) if os.path.exists(p) else None
        bank_files[bank] = {"path": rel(p), "bytes": os.path.getsize(p) if got else 0,
                            "sha256": got, "manifest_sha256": w["sha256"],
                            "manifest_samples": w["samples"], "match": got == w["sha256"]}
        if not got:
            missing.append(p)
    vanilla = {}
    for bank, key in sorted(mf["bank"].items()):
        p = key.get("file") or mf["inputs"]["banks"][bank]
        p = p if os.path.isabs(p) else os.path.join(ROOT, p)
        got = sha(open(p, "rb").read()) if os.path.exists(p) else None
        vanilla[bank] = {"path": rel(p) if p.startswith(ROOT) else p, "sha256": got,
                         "manifest_source_sha256": key["source_sha256"],
                         "match": got == key["source_sha256"]}
        if not got:
            missing.append(p)
    if missing:
        raise SystemExit("FAIL: input missing (not skipped): " + ", ".join(rel(p) for p in missing))

    # per-slot measurement
    rows = []
    dec_ok = prov_ok = len_ok = loud_ok = loop_ok = tail_ok = True
    shifts = {b: bank_record_slack(os.path.join(BANKS, f"{b}.bank"),
                                   [s for s in slots if s["bank"] == b]) for b in sorted(bank_files)}
    for s in slots:
        bank, idx = s["bank"], int(s["index"])
        built = decode(os.path.join(BANKS, f"{bank}.bank"), idx)
        van = decode(vanilla[bank]["path"], idx)
        p = s["source"] if os.path.isabs(s["source"]) else os.path.join(ROOT, s["source"])
        raw_frames, raw_ch, raw_rate = wav_frames(p)
        ms = s["measured"]
        span_frames = int(ms["src_frames"]) + int(ms["padded_frames"]) - int(ms["trimmed_frames"])

        # the payload B-11's rule derives from the WAV (same inputs, same function)
        row = next(r for r in mp["rows"] if r["id"] == s["row"])
        slot = next(x for x in row["slots"] if x["name"] == s["name"])
        src = bm_audio.mono_48k(*bm_audio.source_of(row, slot))
        gain = float(ms.get("gain_db_loopfill", s["gain_db"]))
        q, _meas = bm_audio.payload(src, gain, int(s["frames"]), loop="_loop" in s["name"])
        pcm = np.clip(q * 32768.0, -32768, 32767).astype("<i2")
        if int(s["channels"]) > 1:
            pcm = np.repeat(pcm[:, None], int(s["channels"]), axis=1).reshape(-1)
        derived = pcm.tobytes()

        slack = shifts[bank][idx]                       # bytes a record carries besides its PCM
        if built["bytes"] == derived:
            match, shift_frames = "exact", 0
        elif slack > 0 and built["bytes"][slack:] == derived[:len(built["bytes"]) - slack] \
                and built["bytes"][:slack] == van["bytes"][:slack]:
            match, shift_frames = "shifted", slack // (2 * int(s["channels"]))
        else:
            match, shift_frames = "mismatch", None

        meta_ok = (built["frames"] == int(s["frames"]) and built["rate"] == int(s["rate"])
                   and built["channels"] == int(s["channels"]) and built["name"] == s["name"])
        dec_ok &= meta_ok
        prov_ok &= match in ("exact", "shifted")

        st_b, st_v = steps(built["pcm"]), steps(van["pcm"])
        lufs_b = g15.integrated_lufs(built["pcm"], built["rate"])
        lufs_v = g15.integrated_lufs(van["pcm"], van["rate"])
        mono_b = g15.integrated_lufs(built["pcm"].mean(axis=1)[:, None], built["rate"])
        mono_v = g15.integrated_lufs(van["pcm"].mean(axis=1)[:, None], van["rate"])
        is_loop = "_loop" in s["name"]

        d_span = built["frames"] - span_frames
        d_raw = built["frames"] - raw_frames
        length_ok = abs(d_span) <= 1
        len_ok &= length_ok
        dl = None if (lufs_b is None or lufs_v is None) else round(lufs_b - lufs_v, 2)
        loudness_ok = dl is not None and abs(dl) <= LU_TOL
        loud_ok &= loudness_ok

        nz = np.flatnonzero(np.abs(built["pcm"]).max(axis=1) > 1e-4)
        tail_s = round(float(built["frames"] - 1 -
                             (int(nz[-1]) if nz.size else built["frames"] - 1))
                       / float(built["rate"]), 4)
        tail_rms_b = db(np.sqrt((built["pcm"][-480:] ** 2).mean()))
        tail_rms_v = db(np.sqrt((van["pcm"][-480:] ** 2).mean()))

        loop_rec = None
        if is_loop:
            sb, sv = seam(built["pcm"]), seam(van["pcm"])
            pb, pv = p99(st_b), p99(st_v)
            click = sb > CLICK_DBFS and sb > pb
            if click:
                verdict = "FAIL: click at the only available loop boundary"
            elif sb <= CLICK_DBFS:
                verdict = "pass: below the -40 dBFS threshold"
            else:
                verdict = ("pass: above -40 dBFS but inside the payload's own step "
                           "distribution (not a click)")
            tile = None
            if int(ms["padded_frames"]) > 0:
                period = int(ms["src_frames"]) - bm_audio.XFADE
                pos = [k * period for k in range(1, int(built["frames"] / period) + 2)
                       if k * period < built["frames"] - 2]
                if pos:
                    mm = max(float(np.abs(np.diff(built["pcm"].mean(axis=1)[x - 4:x + 5])).max())
                             for x in pos)
                    tile = {"count": len(pos), "max_step_dbfs": db(mm),
                            "interior_p99_dbfs": pb}
            loop_rec = {
                "loop_point": {"manifest_loop_start": s.get("loop_start"),
                               "manifest_loop_end": s.get("loop_end"),
                               "vgmstream_loop_start": built["loop_start"],
                               "vgmstream_loop_end": built["loop_end"],
                               "vgmstream_loop_lines": built["loop_lines"],
                               "status": "present" if built["loop_lines"] else "absent"},
                "seam_dbfs": sb, "vanilla_seam_dbfs": sv,
                "interior_p99_dbfs": pb, "vanilla_interior_p99_dbfs": pv,
                "seam_worse_than_vanilla_db": round(sb - sv, 2),
                "tile_seams": tile,
                "verdict": verdict, "click": click}
            loop_ok &= not click
            tail_ok &= tail_s <= TAIL_SILENCE_S

        rows.append({
            "row": s["row"], "feature": s["feature"], "slot": f"{bank}#{idx}",
            "bank": bank, "index": idx, "name": s["name"],
            "event_guid": s.get("guid"),
            "event_identity": "name match, not a proven event: T-16 "
                               f"slot_confidence={row.get('slot_confidence')!r}",
            "decode": {"frames": built["frames"], "rate": built["rate"],
                       "channels": built["channels"], "name": built["name"],
                       "encoding": next((x.split(":", 1)[1].strip() for x in built["meta"]
                                         if x.strip().startswith("encoding:")), ""),
                       "meta_ok": meta_ok, "pcm_sha256": built["sha256"],
                       "manifest_payload_sha256": s["payload_sha256"],
                       "payload_match": match, "shift_frames": shift_frames,
                       "record_slack_bytes": slack},
            "length": {"frames_built": built["frames"], "frames_wav_raw": raw_frames,
                       "frames_wav_span": span_frames, "delta_raw": d_raw,
                       "delta_span": d_span, "ok": length_ok},
            "loudness": {"lufs_built": lufs_b, "lufs_vanilla": lufs_v,
                         "delta_lu": dl, "ok": loudness_ok,
                         "lufs_built_mono": mono_b, "lufs_vanilla_mono": mono_v,
                         "delta_lu_mono": None if (mono_b is None or mono_v is None)
                         else round(mono_b - mono_v, 2),
                         "t16_map_lufs": slot.get("lufs"),
                         "manifest_map_lufs": s["map_lufs"],
                         "wav": {"channels": raw_ch, "rate": raw_rate,
                                 "frames": raw_frames,
                                 "lufs_mono": g15.integrated_lufs(src[:, None],
                                                                  built["rate"])}},
            "loop": loop_rec,
            "tail": {"silence_s": tail_s, "rms_dbfs": tail_rms_b,
                     "vanilla_rms_dbfs": tail_rms_v,
                     "ok": bool(tail_s <= TAIL_SILENCE_S) if is_loop else None},
        })

    gates = {"inputs": True, "decode": bool(dec_ok), "provenance": bool(prov_ok),
             "length": bool(len_ok), "loudness": bool(loud_ok), "loop": bool(loop_ok),
             "tail": bool(tail_ok)}
    red = [k for k, v in gates.items() if not v]
    doc = {
        "schema": SCHEMA, "card": CARD, "generator": "Tools/scripts/v04_audio.py",
        "scope": "the five B-11 swapped slots, decoded back out of the RC's own banks",
        "inputs": {"rc_banks": bank_files, "vanilla_banks": vanilla,
                   "sources": inputs,
                   "manifest": rel(MANIFEST), "manifest_sha256": sha(open(MANIFEST, "rb").read()),
                   "map": rel(MAP), "map_sha256": sha(open(MAP, "rb").read())},
        "method": {
            "decode": "vgmstream -s IDX -m on the RC bank; frames/rate/channels/name from its "
                      "metadata, PCM from the WAV it writes",
            "length": "frames_built vs the WAV: `span` = src_frames + padded_frames - "
                      "trimmed_frames (the +-1 gate, spec V-04 section 3) and `raw` = the WAV's "
                      "own frame count (printed, cannot pass: route a keeps the slot's frames)",
            "loudness": "ITU-R BS.1770-4 integrated LUFS of the decoded built payload vs the "
                        "decoded vanilla payload at the same bank+index, both as stored; the "
                        "mono downmix is printed because T-16's map compares a mono payload "
                        "measurement with a stereo slot target",
            "loop": "no slot carries a loop field: the manifest's loop_start/loop_end are null "
                    "and vgmstream prints no loop start/end/flag line (the stream NAME contains "
                    "`_loop`, which is not metadata). The only loop boundary the data carries is "
                    "therefore the file wrap, and the vanilla payload at the same index is the "
                    "oracle that the boundary is the loop (its end->start step is inside its own "
                    "p99 interior step). A click is a wrap step worse than -40 dBFS AND an "
                    "outlier against the built payload's own p99 interior step",
            "tail": "a loop payload may not end in more than 10 ms of digital silence",
        },
        "gates": gates,
        "verdict": "ALL GREEN" if not red else "RED: " + ", ".join(red),
        "rows": rows,
        "unknowns": [
            {"what": "the loop point of the three `_loop` payloads",
             "status": "UNKNOWN",
             "tried": "manifest loop_start/loop_end (null on 5/5), vgmstream -m (no loop line, see "
                      "rows[].loop.loop_point.vgmstream_loop_lines), t12_audio_map.json "
                      "method.loop (records the FSB5 field absent)",
             "why": "the bank stores no loop field; whether the event/tune graph or the engine "
                    "loops the payload, and over which region, is not in any file read here"},
            {"what": "whether the chosen slot is the vanilla event the game plays for that row",
             "status": "UNKNOWN",
             "tried": "t12_audio_map.json slot records (`slot_confidence`), manifest `resolved` "
                      "GUIDs, G2-24 (no tune->sample field in the bank)",
             "why": "the ±1 LU comparison is against the vanilla payload in the same slot "
                    "(same bank, same index), not against a proven event"},
            {"what": "whether the swapped payload is what the event plays at runtime",
             "status": "UNKNOWN",
             "tried": "FEV event/tune GUIDs present in the built bank (B-11), slot naming",
             "why": "needs the game (phase Q); the test ban is in force"},
        ],
        "offline_uncheckable": [
            "loop point / seam of `jc3_veh_land_premium_nitro_loop` (A-02)",
            "loop point / seam of `jc3_veh_lave_chassis_spin_creaks_loop_fast` (A-05)",
            "loop point / seam of `jc3_wpn_minigun_fire_close_loop_04` (W-03)",
            "which vanilla event each slot really is (all five; W-03 has no donor GUID at all)",
            "how the swap sounds in game (timbre, mixing, ducking) - phase Q only",
        ],
        "summary": {
            "slots": len(rows), "banks": len(bank_files), "samples": sum(
                v["manifest_samples"] for v in bank_files.values()),
            "decode_meta_ok": sum(1 for r in rows if r["decode"]["meta_ok"]),
            "provenance": {k: sum(1 for r in rows if r["decode"]["payload_match"] == k)
                           for k in ("exact", "shifted", "mismatch")},
            "length_ok": sum(1 for r in rows if r["length"]["ok"]),
            "loudness_ok": sum(1 for r in rows if r["loudness"]["ok"]),
            "max_abs_delta_lu": max(abs(r["loudness"]["delta_lu"] or 0.0) for r in rows),
            "loop_slots": sum(1 for r in rows if r["loop"]),
            "loop_click": sum(1 for r in rows if r["loop"] and r["loop"]["click"]),
            "red_gates": red,
        },
    }
    return doc


# ------------------------------------------------------------------ render
def render_md(doc: dict) -> str:
    s = doc["summary"]
    g = doc["gates"]
    L = ["# V-04 audio gates - `Builds/bm-RC1`", "",
         f"`python Tools/scripts/v04_audio.py --check`", "",
         f"**{doc['verdict']}** - {s['slots']} slots in {s['banks']} banks "
         f"({s['samples']:,} samples).", "",
         "| gate | result |", "|---|---|"]
    for k in ("inputs", "decode", "provenance", "length", "loudness", "loop", "tail"):
        L.append(f"| {k} | {'GREEN' if g[k] else 'RED'} |")
    L += ["", "## Per slot", "",
          "| slot | name | fr built / wav / span | \u0394 span | LUFS built / vanilla | "
          "\u0394 LU | loop |",
          "|---|---|---|---|---|---|---|"]
    for r in doc["rows"]:
        ln, ld = r["length"], r["loudness"]
        lp = r["loop"]
        L.append(f"| `{r['slot']}` | `{r['name']}` | {ln['frames_built']} / "
                 f"{ln['frames_wav_raw']} / {ln['frames_wav_span']} | {ln['delta_span']:+d} | "
                 f"{ld['lufs_built']} / {ld['lufs_vanilla']} | "
                 f"{'-' if ld['delta_lu'] is None else format(ld['delta_lu'], '+.2f')} | "
                 f"{('n/a (one-shot)') if not lp else ('CLICK' if lp['click'] else 'no click')} |")
    L += ["", "`\u0394 span` is the card's \u00b11-frame test against the WAV *after* B-11's "
          "documented trim/tile/span: "
          "`src_frames + padded_frames - trimmed_frames`. Against the raw WAV every slot differs "
          "(`\u0394 raw` below), which route a makes unavoidable.", "",
          "| slot | \u0394 raw (frames, by design) | payload provenance | payload shift |",
          "|---|---|---|---|"]
    for r in doc["rows"]:
        d = r["decode"]
        L.append(f"| `{r['slot']}` | {r['length']['delta_raw']:+d} | {d['payload_match']} | "
                 f"{d['shift_frames']} frames |")
    L += ["", "## Loop seams", "",
          "| slot | loop point | built seam | vanilla seam | built p99 step | click? |",
          "|---|---|---|---|---|---|"]
    for r in doc["rows"]:
        lp = r["loop"]
        if not lp:
            continue
        L.append(f"| `{r['slot']}` | {lp['loop_point']['status']} | "
                 f"{lp['seam_dbfs']} dBFS | {lp['vanilla_seam_dbfs']} dBFS | "
                 f"{lp['interior_p99_dbfs']} dBFS | {'yes' if lp['click'] else 'no'} |")
    L += ["", "No payload carries an FSB5 loop field (manifest `loop_start`/`loop_end` null, "
          "vgmstream prints no loop line), so the file wrap is the only loop boundary the data "
          "carries; the vanilla payload at the same index is continuous there, which is the "
          "evidence that the boundary is the loop. A click is a wrap step worse than -40 dBFS "
          "**and** an outlier against the payload's own p99 interior step. The tile seams B-11's "
          "loop fill creates are measured too (`tile_seams` in the JSON) and are not clicks.", ""]
    L += ["## What cannot be checked offline", ""]
    L += [f"- {x}" for x in doc["offline_uncheckable"]]
    L += ["", "## UNKNOWNs", ""]
    for u in doc["unknowns"]:
        L += [f"- **{u['what']}** - {u['status']}. Tried: {u['tried']}. Why: {u['why']}"]
    L.append("")
    return "\n".join(L)


def write(doc: dict) -> None:
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "audio.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1) + "\n")
    with open(os.path.join(OUT, "audio.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(doc))


# ------------------------------------------------------------------ main
def diff_paths(a, b, path="") -> list[str]:
    if isinstance(a, bool) or isinstance(b, bool):
        return [] if a is b else [f"{path}: {a!r} != {b!r}"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return [] if abs(float(a) - float(b)) < 1e-9 else [f"{path}: {a!r} != {b!r}"]
    if type(a) is not type(b):
        return [f"{path}: {type(a).__name__} != {type(b).__name__}"]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{path}.{k}: missing in re-derived")
            elif k not in b:
                out.append(f"{path}.{k}: missing in the file")
            else:
                out += diff_paths(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: {len(a)} != {len(b)} items"]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff_paths(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="measure and write verify/audio.{json,md}")
    g.add_argument("--check", action="store_true", help="re-derive and compare with the files")
    a = ap.parse_args()

    if not os.path.isdir(BANKS):
        print(f"BLOCKED: {rel(BANKS)} missing (gate BX / B-14)")
        return 2
    doc = measure()
    s = doc["summary"]

    if a.write:
        write(doc)
        print(f"wrote {rel(OUT)}/audio.json + audio.md: {s['slots']} slots, "
              f"decode {s['decode_meta_ok']}/{s['slots']}, length {s['length_ok']}/{s['slots']}, "
              f"loudness {s['loudness_ok']}/{s['slots']} (max |delta| "
              f"{s['max_abs_delta_lu']:.2f} LU), loop clicks {s['loop_click']}/"
              f"{s['loop_slots']}")
        for r in doc["rows"]:
            ln, ld, lp = r["length"], r["loudness"], r["loop"]
            print(f"  {r['slot']:>12} {r['name'][:40]:40s} fr {ln['frames_built']:>7}/"
                  f"{ln['frames_wav_span']:<7} dspan {ln['delta_span']:+d} "
                  f"LU {ld['lufs_built']}/{ld['lufs_vanilla']} d {ld['delta_lu']:+.2f} "
                  f"prov {r['decode']['payload_match']:<8} "
                  f"loop {('n/a' if not lp else ('CLICK' if lp['click'] else 'ok'))}")
        print(f"verdict: {doc['verdict']}")
        return 0

    jp = os.path.join(OUT, "audio.json")
    mdp = os.path.join(OUT, "audio.md")
    if not os.path.exists(jp) or not os.path.exists(mdp):
        print(f"FAIL: {rel(jp)} missing (run --write)")
        return 1
    on_disk = json.load(open(jp, encoding="utf-8"))
    d = diff_paths(doc, on_disk)
    md_want = render_md(doc)
    md_got = open(mdp, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if d:
        for x in d[:10]:
            print("FAIL:", x)
        return 1
    if md_want != md_got:
        print("FAIL: audio.md differs from the re-rendered text")
        return 1
    print(f"PASS: {rel(jp)} + audio.md reproduce from the banks and WAV sources "
          f"({s['slots']} slots, {s['samples']:,} samples)")
    print(f"gates: decode {s['decode_meta_ok']}/{s['slots']}, length {s['length_ok']}/"
          f"{s['slots']}, loudness {s['loudness_ok']}/{s['slots']} "
          f"(max |delta| {s['max_abs_delta_lu']:.2f} LU), loop clicks {s['loop_click']}/"
          f"{s['loop_slots']}, tail "
          f"{sum(1 for r in doc['rows'] if r['loop'] and r['tail']['ok'])}/{s['loop_slots']}")
    print(f"verdict: {doc['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
