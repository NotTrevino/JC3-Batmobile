"""bm_audio.py - B-11: the Batmobile sound bank, by swapping sample payloads in a private copy.

`GRAB_BACKLOG.md` §8 (`B-11`): "per the G2-24 route: build a private bank (or a copy of
`vehicles.bank` with swapped samples) from the T-16 map; generate `.ee.fmod_guids`; weapon
sounds per T-11." Out: bank file(s) in the build tree; `Working/Audio/bm_bank_manifest.json`.
Done: "every mapped event resolves; sample count/lengths match the manifest; the installer
handles and rolls back the bank (old AUD-5)."

Why a swap and not a new bank
-----------------------------
G2-24 §10 (`Research/JC3Grab/JC3_AUDIO.md`) settles the route: the banks are FMOD Designer
FEV v56 build 50 with one FSB5 sample bank inside, the events/tunes/parameters live in the FEV
graph and **no `.fev` project ships**, so a new bank cannot be authored (route b = no). What
is proven is a *payload* swap inside a copy of the bank - test-060 did it in place with
`Tools/scripts/_apply_audio.py` (MODLOG §71: identical byte size, FSB5 metadata untouched, the
bank still parses and vgmstream still decodes it). This script does the same on a **private
copy** (R7), driven entirely by T-16's map instead of hard-coded sample numbers.

What the map gives, and what this script therefore writes
---------------------------------------------------------
`Working/Translation/t12_audio_map.json` (T-16, `done`) has 5 rows with `dispo: mapped` and one
`chosen` slot each; a slot carries the bank, the 1-based sample index, the frame count the
sample already has, the BmAK WAV that feeds it (`source`), the span (`source_span_s`), the gain
T-16 measured against the payload (`gain_db`) and the loudness that payload delivered
(`delivered_lufs`). 4 slots are in `vehicles.bank`, 1 in `weapons.bank` (T-11's Vulcan loop).

1. rebuild the payload exactly as T-16 measured it (`mono_48k` -> gain -> trim/pad -> PCM16),
   and refuse to continue if the rebuilt payload's loudness is not the map's `delivered_lufs`
   within `LUFS_TOL`;
2. splice it into the sample's PCM block in the copied bank (`data[:hlen] + pcm`), asserting the
   payload length is unchanged and the sample is located exactly once;
3. re-parse the written bank with `fsb5` and, for every swapped sample, with **vgmstream** -
   frames, rate, channels and the sample name must be what the manifest says;
4. re-emit `.ee.fmod_guids` from the `.ee`'s own inner file (u32 version, u16 bank count + names,
   u16 count + 16 B GUIDs) and assert the re-emitted bytes are the ones the `.ee` carries;
5. resolve every mapped event in the **built** bank: `jc3audio.fev_events` must list the row's
   GUID and `jc3audio.fev_tunes` its tune (rows with no donor GUID, the T-11 weapon rows, resolve
   through their slot instead - recorded as such);
6. write `Working/Audio/bm_bank_manifest.json`, the build receipt and an installer whose Install
   copies the two banks to the dropzone's `sound/fmod_banks/` and whose Rollback091 deletes them
   (the loose-override route of test-060). Nothing is installed or launched here.

Usage
    python Tools/scripts/bm_audio.py --write    # banks + manifest + Builds/bm-004
    python Tools/scripts/bm_audio.py --check    # re-derive, re-read, run the three Done checks
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
import shutil
import subprocess
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import numpy as np                                   # noqa: E402
from fsb5 import FSB5                                # noqa: E402

import bmak_audio_features as g15                    # noqa: E402  (integrated_lufs / _float_mono)
import jc3audio                                      # noqa: E402
import jc3grab                                       # noqa: E402

CARD = "B-11"
BASE_TAG = "bm-001"                                  # the identity build the lineage starts from
TAG = "bm-004"                                       # bm-002 = B-04, bm-003 is B-05's entity step
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
MAP = os.path.join(ROOT, "Working", "Translation", "t12_audio_map.json")
BASE = os.path.join(ROOT, "Builds", BASE_TAG)
OUT = os.path.join(ROOT, "Builds", TAG)
OUT_BANKS = os.path.join(OUT, "banks")
MANIFEST = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest.json")
GAME = r"D:\Games\Just Cause 3"
DROP_BANKS = "dropzone\\sound\\fmod_banks"
VGMPATH = os.path.join(ROOT, "Tools", "vgmstream-win64", "vgmstream-cli.exe")

# vanilla sources: the in-repo copy T-16 measured, and the decoded weapons bank (R10, outside)
BANK_SRC = {
    "vehicles": os.path.join(ROOT, "Working", "Audio", "jc3bank", "sound", "fmod_banks",
                             "vehicles.bank"),
    "weapons": r"E:\Modding\_shared\gamedata\JC3grab\audio\weapons.bank",
}
LUFS_TOL = 0.05          # LU: the rebuilt payload must be the payload T-16 measured
RATE = 48000
SCHEMA = 1

# --- optional per-slot source fixes (B-11-rc4, V-04-derived) -----------------
# Keyed by (bank, 1-based sample index): {"drop_frames": int, "gain_factor": float}.
# Empty by default: Builds/bm-004 and Working/Audio/bm_bank_manifest.json stay the
# same bytes they were before this hook existed.
SOURCE_FIXES: dict = {}


def configure(tag: str | None = None, base: str | None = None,
              manifest: str | None = None) -> None:
    """Point the generator at another output tree / manifest (B-11-rc4).

    Only the module-level paths move - the derivation is the same code path as
    `Builds/bm-004`, so a second tree cannot drift from the first one's rules.
    """
    global TAG, BASE_TAG, OUT, OUT_BANKS, MANIFEST, BASE
    if tag:
        TAG = tag
        OUT = os.path.join(ROOT, "Builds", TAG)
        OUT_BANKS = os.path.join(OUT, "banks")
    if base:
        BASE_TAG = base
        BASE = os.path.join(ROOT, "Builds", BASE_TAG)
    if manifest:
        MANIFEST = manifest


# ------------------------------------------------------------------ helpers
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fsb_of(raw: bytes) -> tuple[int, FSB5]:
    """The bank's own FSB5 (the FEV RIFF wraps it) - offset and parser, never assumed."""
    base = raw.find(b"FSB5")
    if base < 0:
        raise SystemExit("no FSB5 in the bank")
    return base, FSB5(raw[base:])


def mono_48k(path: str, span_s: float | None, tail: bool) -> np.ndarray:
    """The payload source, read the way T-16 read it: 48 kHz, mono downmix, optional span.

    scipy is used when it imports; the stdlib `wave` reader is the same read (int16 frames,
    same channel interleave) and exists so a session where scipy's DLLs cannot load - e.g.
    "paging file is too small" under memory pressure - can still build the banks.
    """
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    try:
        from scipy.io import wavfile
        sr, data = wavfile.read(p)
    except Exception:
        import wave
        with wave.open(p, "rb") as f:
            sr, ch, n = f.getframerate(), f.getnchannels(), f.getnframes()
            data = np.frombuffer(f.readframes(n), dtype="<i2")
            if ch > 1:
                data = data.reshape(-1, ch)
    if int(sr) != RATE:
        raise SystemExit(f"{p}: {sr} Hz source - the swap assumes 48 kHz")
    a = g15._float_mono(data)
    a = a.mean(axis=1) if a.ndim > 1 and a.shape[1] > 1 else a.reshape(-1)
    if span_s:
        n = int(round(float(span_s) * RATE))
        a = a[-n:] if tail else a[:n]
    return a


XFADE = 2048   # ~43 ms equal-power crossfade at each tile seam


def payload(src: np.ndarray, gain_db: float, frames: int, loop: bool = False) -> tuple[np.ndarray, dict]:
    """T-16's `build_payload`, to the byte: gain, trim or zero-pad, PCM16 quantise.

    `loop` (V-04, 2026-10-31): a `_loop` slot shorter than its source span is NOT zero-padded - the
    padding put 3.1 s (creaks) and 1.7 s (minigun) of digital silence into every loop cycle, where the
    vanilla loop payloads are continuous to their last frame. It is filled by repeating the source with
    an equal-power crossfade at each seam instead; one-shots keep T-16's zero pad byte for byte."""
    x = src * (10 ** (gain_db / 20.0))
    trimmed = max(0, len(x) - frames)
    padded = max(0, frames - len(x))
    if trimmed:
        x = x[:frames]
    elif padded and loop and len(x) > 4 * XFADE:
        t = np.linspace(0.0, np.pi / 2, XFADE)
        fade_out, fade_in = np.cos(t), np.sin(t)
        out = x.copy()
        while len(out) < frames:
            seam = out[-XFADE:] * fade_out + x[:XFADE] * fade_in
            out = np.concatenate([out[:-XFADE], seam, x[XFADE:]])
        x = out[:frames]
    else:
        x = np.concatenate([x, np.zeros(padded)])
    clip = float((np.abs(x) > 1.0).mean())
    q = np.round(np.clip(x, -1.0, 1.0) * 32767.0) / 32768.0
    return q, {"delivered_lufs": g15.integrated_lufs(q[:, None], RATE),
               "clip_pct": round(100.0 * clip, 2), "padded_frames": padded,
               "trimmed_frames": trimmed, "src_frames": int(len(src))}


def source_of(row: dict, slot: dict) -> tuple[str, float | None, bool]:
    """The WAV behind a chosen slot, resolved the way T-16's `target_of` resolved it.

    `source_rule: slot_src` means the row names the WAV itself (the label is its basename);
    `first` / `primary` means the label is a BmAK event name and the payload is that event's
    loudest media, measured as the payload reads it (mono downmix) - the rule T-16 applied.
    """
    label = slot.get("source") or ""
    rule = slot.get("source_rule")
    sources = row.get("sources") or []
    if rule == "slot_src":
        cands = [v["wav"] for s in sources for v in s.get("wems_lufs") or [] if v.get("wav")]
        cands += [(s.get("source") or {}).get("wav") for s in sources]
        hit = [c for c in cands
               if c and os.path.basename(c) == os.path.basename(label)]
        if len(hit) != 1:
            raise SystemExit(f"{row['id']}: slot_src {label!r} matches {len(hit)} WAVs")
        return hit[0], slot.get("source_span_s"), False
    cand = [s for s in sources if s.get("event") == label]
    if len(cand) != 1:
        raise SystemExit(f"{row['id']}: event {label!r} matches {len(cand)} sources")
    cands = [v for v in cand[0].get("wems_lufs") or [] if v.get("wav")]
    if not cands:
        src = (cand[0].get("source") or {}).get("wav")
        if not src:
            raise SystemExit(f"{row['id']}: event {label!r} has no WAV")
        return src, slot.get("source_span_s"), False
    # T-16's `target_of` ranks the variants by their **mono payload** loudness (`source_stats`),
    # not by the shipped multi-channel LUFS, so the row records that number as `src_lufs`.  The
    # variant whose mono loudness equals `src_lufs` is the one T-16 measured - picking it by that
    # number is what makes the rebuilt payload comparable with `delivered_lufs`.
    want = slot.get("src_lufs")
    ranked = []
    for v in cands:
        a = mono_48k(v["wav"], slot.get("source_span_s"), False)
        ranked.append((g15.integrated_lufs(a[:, None], RATE), len(a), v["wav"]))
    best = max(ranked, key=lambda t: t[0]) if want is None else min(
        ranked, key=lambda t: abs(t[0] - float(want)))
    if want is not None and abs(best[0] - float(want)) > LUFS_TOL:
        raise SystemExit(f"{label}: no variant's mono loudness matches src_lufs {want} "
                         f"(closest {best[0]:.2f})")
    if slot.get("source_frames") and best[1] != int(slot["source_frames"]):
        raise SystemExit(f"{label}: variant has {best[1]} frames, map {slot['source_frames']}")
    return best[2], slot.get("source_span_s"), False


def vgm(bank: str, index: int) -> dict:
    """Per-sample facts from vgmstream (the project's proven FSB5 reader)."""
    r = subprocess.run([VGMPATH, "-s", str(index), "-m", bank],
                       capture_output=True, text=True, errors="replace")
    got: dict = {"index": index, "frames": 0, "rate": 0, "channels": 0, "encoding": "",
                 "name": ""}
    for line in (r.stdout + r.stderr).splitlines():
        line = line.strip()
        if line.startswith("sample rate:"):
            got["rate"] = int(line.split(":")[1].split("Hz")[0].strip())
        elif line.startswith("channels:"):
            got["channels"] = int(line.split(":")[1].strip())
        elif line.startswith("stream total samples:"):
            got["frames"] = int(line.split(":")[1].split("(")[0].strip())
        elif line.startswith("encoding:"):
            got["encoding"] = line.split(":", 1)[1].strip()
        elif line.startswith("stream name:"):
            got["name"] = line.split(":", 1)[1].strip()
    if r.returncode != 0 or not got["rate"]:
        raise SystemExit(f"vgmstream failed on {bank} #{index}: {r.stderr[-200:]!r}")
    return got


def fmod_guids_of(ee_path: str) -> tuple[bytes, dict]:
    """The `.ee.fmod_guids`: u32 version, u16 bank count + names, u16 count + 16 B GUIDs."""
    stream, entries = jc3grab.inner_files(open(ee_path, "rb").read())
    hit = next((e for e in entries if e[0].endswith(".fmod_guids")), None)
    if hit is None:
        raise SystemExit(f"{rel(ee_path)} carries no .fmod_guids")
    blob = stream[hit[1]:hit[1] + hit[2]]
    version, nb = struct.unpack_from("<IH", blob, 0)
    o, banks = 6, []
    for _ in range(nb):
        (ln,) = struct.unpack_from("<H", blob, o)
        o += 2
        banks.append(blob[o:o + ln].decode("ascii"))
        o += ln
    (ne,) = struct.unpack_from("<H", blob, o)
    o += 2
    guids = [blob[o + i * 16:o + i * 16 + 16] for i in range(ne)]
    # regenerate the file from its own decoded values - byte-identical or this fails
    out = bytearray(struct.pack("<IH", version, len(banks)))
    for b in banks:
        out += struct.pack("<H", len(b)) + b.encode("ascii")
    out += struct.pack("<H", len(guids))
    for g in guids:
        out += g
    if bytes(out) != blob:
        raise SystemExit(".ee.fmod_guids does not re-emit byte-identically")
    info = {"bytes": len(blob), "version": version, "banks": banks,
            "count": ne, "guids": [g.hex() for g in guids],
            "sha256": sha256(blob)}
    return bytes(out), info


# ------------------------------------------------------------------ build
def build(write: bool = True) -> dict:
    """Derive the banks from the map.

    `write=False` (what `--check` uses) sends the derived bytes to a temporary directory instead of
    `Builds/bm-004`, so the check compares against what is on disk instead of repairing it.
    """
    m = json.load(open(MAP, encoding="utf-8"))
    rows = [r for r in m["rows"] if r.get("dispo") == "mapped"]
    if not rows:
        raise SystemExit("the T-16 map has no mapped rows")

    # 1. the payloads, rebuilt from the map
    plan: dict[str, list[dict]] = {}
    for r in rows:
        for s in r["slots"]:
            if not s.get("chosen"):
                continue
            wav, span, tail = source_of(r, s)
            src = mono_48k(wav, span, tail)
            is_loop = "_loop" in s["name"]
            gain = float(s["gain_db"])
            fix = SOURCE_FIXES.get((s["bank"], int(s["index_1based"])))
            if fix:
                drop = int(fix.get("drop_frames") or 0)
                factor = float(fix.get("gain_factor") or 1.0)
                if drop:
                    if len(src) - drop < 8 * XFADE:
                        raise SystemExit(f"{s['name']}: a {drop}-frame drop leaves "
                                         f"{len(src) - drop} frames of source")
                    src = src[drop:]
                if factor != 1.0:
                    gain += 20.0 * math.log10(factor)
            q, meas = payload(src, gain, int(s["frames"]), loop=is_loop)
            want = s.get("delivered_lufs")
            if fix and fix.get("expect_lufs") is not None:
                # a source fix retargets the payload's loudness (B-11-rc4: the -2.72 dB
                # minigun gain is derived against the vanilla slot, not against T-16's
                # unfixed payload), so the map's number is not this slot's oracle
                want = float(fix["expect_lufs"])
                meas["fix_expect_lufs"] = want
            if is_loop and meas["padded_frames"] and want is not None:
                # the loop fill replaced silence with signal: re-level onto T-16's delivered loudness
                # only ever DOWN: raising gain on a hot source clipped the minigun 3.5 -> 7.7 %
                for _ in range(3):
                    corr = float(want) - meas["delivered_lufs"]
                    if corr >= 0:
                        break
                    gain += corr
                    q, meas = payload(src, gain, int(s["frames"]), loop=True)
                if abs(meas["delivered_lufs"] - float(want)) > 1.0:
                    raise SystemExit(f"{s['name']}: loop fill is {meas['delivered_lufs']:.2f} LUFS, outside +-1 LU of {want}")
                meas["map_delivered_lufs"] = float(want)
                want = meas["delivered_lufs"]   # inside the card's +-1 LU band (V-04); both recorded
                meas["gain_db_loopfill"] = round(gain, 3)
                meas["loop_fill"] = f"tiled with a {XFADE}-frame equal-power crossfade (V-04)"
            if want is None or abs(meas["delivered_lufs"] - float(want)) > LUFS_TOL:
                raise SystemExit(f"{r['id']} {s['name']}: rebuilt payload is "
                                 f"{meas['delivered_lufs']:.2f} LUFS, map says {want}")
            plan.setdefault(s["bank"], []).append({
                "row": r["id"], "feature": r["feature"], "guid": r.get("guid"),
                "bank": s["bank"], "index": int(s["index_1based"]), "name": s["name"],
                "frames": int(s["frames"]), "rate": int(s["rate"]),
                "channels": int(s["channels"]), "encoding": s["encoding"],
                "gain_db": float(s["gain_db"]), "source": wav, "span_s": span,
                "map_lufs": float(want), "payload": q, "measured": meas,
                "loop_start": s.get("loop_start"), "loop_end": s.get("loop_end")})

    # 2. the private banks (R7: the vanilla file is never edited in place)
    banks = {}
    for bank, edits in sorted(plan.items()):
        src_path = BANK_SRC[bank]
        raw = bytearray(open(src_path, "rb").read())
        # no `bytes(raw)` copies here: a 210 MB bank plus its FSB5 sample data plus two
        # whole-file copies is ~1 GB of commit, which a low-paging-file session cannot get
        orig_sha, orig_len = sha256(raw), len(raw)
        base, fsb = fsb_of(raw)
        for e in edits:
            s = fsb.samples[e["index"] - 1]
            if s.name != e["name"]:
                raise SystemExit(f"{bank} #{e['index']} is {s.name!r}, map says {e['name']!r}")
            if s.samples != e["frames"]:
                raise SystemExit(f"{bank} #{e['index']}: {s.samples} frames, map {e['frames']}")
            data = bytes(s.data)
            hlen = len(data) - s.samples * int(e["channels"]) * 2
            if hlen < 0 or hlen > 4096:
                raise SystemExit(f"{bank} #{e['index']}: header length {hlen} looks wrong")
            pcm = np.clip(e["payload"] * 32768.0, -32768, 32767).astype(np.int16)
            if int(e["channels"]) > 1:
                # the slot is multi-channel and the payload source is mono: the same signal per
                # channel (recorded as `channel_mode: mono-replicated` in the manifest)
                pcm = np.repeat(pcm[:, None], int(e["channels"]), axis=1).reshape(-1)
            body = pcm.tobytes()
            if len(body) != s.samples * int(e["channels"]) * 2:
                raise SystemExit(f"{bank} #{e['index']}: payload {len(body)} B for "
                                 f"{s.samples} x {e['channels']} frames")
            first = raw.find(data)
            if first < 0 or raw.find(data, first + 1) >= 0:
                raise SystemExit(f"{bank} #{e['index']}: sample data is not unique in the "
                                 f"bank - cannot splice safely")
            at = first
            raw[at:at + len(data)] = data[:hlen] + body
            e["payload_sha256"] = sha256(body)
            e["data_offset"] = at - base
            e["bytes"] = len(body)
            e["channel_mode"] = "mono-replicated" if int(e["channels"]) > 1 else "mono"
        nsamples = len(fsb.samples)
        del fsb                     # its sample data is only needed for the splice above
        banks[bank] = {"source": src_path, "source_sha256": orig_sha,
                       "source_bytes": orig_len, "fsb_offset": base,
                       "samples": nsamples, "_bytes": raw}

    # 3. write them to the build and prove the result with fsb5 + vgmstream
    tmproot = None if write else tempfile.mkdtemp(prefix="bm_audio_check_")
    written = []
    names_by_bank: dict[str, list[str]] = {}
    for bank, d in sorted(banks.items()):
        path = os.path.join(OUT_BANKS if write else tmproot, f"{bank}.bank")
        if write:
            os.makedirs(OUT_BANKS, exist_ok=True)
        blob = d.pop("_bytes")
        size = len(blob)
        with open(path, "wb") as f:
            f.write(blob)
        del blob                    # the file on disk is the copy from here on
        raw = open(path, "rb").read()
        base, fsb = fsb_of(raw)
        names_by_bank[bank] = [s.name for s in fsb.samples]
        if len(fsb.samples) != d["samples"]:
            raise SystemExit(f"{bank}: sample count moved {d['samples']} -> {len(fsb.samples)}")
        for e in plan[bank]:
            s = fsb.samples[e["index"] - 1]
            got = vgm(path, e["index"])
            if (s.samples, got["frames"]) != (e["frames"], e["frames"]):
                raise SystemExit(f"{bank} #{e['index']}: frames {s.samples}/{got['frames']} "
                                 f"vs manifest {e['frames']}")
            if got["name"] != e["name"] or s.name != e["name"]:
                raise SystemExit(f"{bank} #{e['index']}: name changed")
            if got["rate"] != e["rate"] or got["channels"] != e["channels"]:
                raise SystemExit(f"{bank} #{e['index']}: {got['rate']} Hz / {got['channels']} ch")
            e["written"] = {"frames": got["frames"], "rate": got["rate"],
                            "channels": got["channels"], "encoding": got["encoding"],
                            "stream_name": got["name"],
                            "duration_s": round(got["frames"] / float(got["rate"]), 6)}
        written.append({"bank": bank,
                        "file": rel(os.path.join(OUT_BANKS, f"{bank}.bank")),
                        "bytes": size,
                        "sha256": sha256(raw), "samples": d["samples"],
                        "source": rel(d["source"]) if d["source"].startswith(ROOT)
                        else d["source"],
                        "source_sha256": d["source_sha256"],
                        "sample_count_unchanged": True,
                        "size_unchanged": size == d["source_bytes"]})
        del fsb, raw

    # 4. every mapped event resolves in the built bank
    events = {}
    for bank in banks:
        raw = open(os.path.join(OUT_BANKS if write else tmproot,
                               f"{bank}.bank"), "rb").read()
        f = jc3audio.fev(raw)
        evs = {e["guid"]: e for e in jc3audio.fev_events(raw, f)}
        tunes = {t["event_guid"]: t for t in jc3audio.fev_tunes(raw, f)}
        events[bank] = {"events": len(evs), "tunes": len(tunes), "evs": evs, "tunes": tunes}
        del raw
    resolved = []
    for bank, edits in plan.items():
        for e in edits:
            rec = {"row": e["row"], "bank": bank, "sample": e["name"],
                   "index": e["index"], "guid": e["guid"]}
            if e["guid"]:
                g = e["guid"].replace("-", "")
                rec["event_present"] = g in events[bank]["evs"]
                rec["tune_present"] = g in events[bank]["tunes"]
                rec["tune_guid"] = events[bank]["tunes"].get(g, {}).get("tune_guid")
                rec["resolved"] = rec["event_present"] and rec["tune_present"]
            else:
                rec["event_present"] = None      # weapon row: no donor GUID (T-11 names a slot)
                rec["tune_present"] = None
                rec["resolved"] = e["name"] in names_by_bank[bank]
                rec["note"] = "weapon row: resolves through its slot, not a donor GUID"
            if not rec["resolved"]:
                raise SystemExit(f"{e['row']}: event does not resolve in {bank}.bank")
            resolved.append(rec)

    # 5. the `.ee.fmod_guids`, re-emitted from the .ee's own inner file
    #    (the .ee itself is the build's root file - the aaf tree carries only loose overrides)
    ee_path = os.path.join(OUT, "aaf", "editor", "entities", "jc_vehicles", "01_land",
                           "v0300_car_kensington_sportsmuscle", f"{EE}.fmod_guids")
    ee_src = os.path.join(BASE, EE)
    if not os.path.exists(ee_src):
        raise SystemExit(f"{rel(ee_src)} missing: the .fmod_guids has to come from the .ee")
    guid_blob, guid_info = fmod_guids_of(ee_src)
    guid_info["ee"] = rel(ee_src)
    if write:
        os.makedirs(os.path.dirname(ee_path), exist_ok=True)
        with open(ee_path, "wb") as f:
            f.write(guid_blob)
    if tmproot:
        shutil.rmtree(tmproot, ignore_errors=True)

    return {
        "schema": SCHEMA, "card": CARD, "generator": "Tools/scripts/bm_audio.py",
        "inputs": {"map": rel(MAP) + " (T-16)",
                   "banks": {k: (rel(v) if v.startswith(ROOT) else v)
                             for k, v in BANK_SRC.items()},
                   "route": "Research/JC3Grab/JC3_AUDIO.md §10 route a + c "
                            "(sample swap in a copy of the bank; no new bank)",
                   "precedent": "Tools/scripts/_apply_audio.py / MODLOG §71 (test-060)"},
        "bank": {k: {kk: vv for kk, vv in v.items() if kk not in ("bytes", "source")}
                 for k, v in banks.items()},
        "written": written,
        "slots": [e for bank in sorted(plan) for e in sorted(plan[bank],
                                                            key=lambda x: x["index"])],
        "resolved": resolved,
        "fmod_guids": {**guid_info, "file": rel(ee_path),
                       "note": "re-emitted from the .ee's own inner file; identical bytes, "
                               "so no .ee/.toc change is needed for the event pins"},
        "events": {k: {"events": v["events"], "tunes": v["tunes"]} for k, v in events.items()},
        "installer": {"game_dir": GAME, "drop": DROP_BANKS,
                      "files": [f"{k}.bank" for k in sorted(banks)],
                      "actions": ["Install", "Verify", "Rollback091", "Status"],
                      "rollback": f"a bank the dropzone already had is copied to "
                                  f"<name>.{TAG}-backup before Install and restored by "
                                  f"Rollback091; a bank this build added is removed",
                      "dropzone_at_build": dropzone_probe([f"{k}.bank" for k in sorted(banks)])},
        "summary": {
            "mapped_rows": len(rows), "slots_written": sum(len(v) for v in plan.values()),
            "banks": len(banks),
            "sample_count": sum(v["samples"] for v in banks.values()),
            "resolved": sum(1 for r in resolved if r["resolved"]),
            "lu_tolerance": LUFS_TOL,
            "max_lu_delta": round(max(abs(e["measured"]["delivered_lufs"] - e["map_lufs"])
                                      for v in plan.values() for e in v), 4),
            "bytes": {w["bank"]: w["bytes"] for w in written},
            "size_unchanged": all(w["size_unchanged"] for w in written),
        },
    }


def dropzone_probe(names: list[str]) -> dict:
    """What the target directory holds *before* Install - read-only, so Rollback has a baseline."""
    out: dict[str, dict] = {}
    base = os.path.join(GAME, DROP_BANKS)
    for n in names:
        p = os.path.join(base, n)
        if os.path.exists(p):
            st = os.stat(p)
            out[n] = {"present": True, "bytes": st.st_size,
                      "mtime": datetime.datetime.fromtimestamp(st.st_mtime).strftime(
                          "%Y-%m-%d %H:%M:%S")}
        else:
            out[n] = {"present": False}
    return out


def installer_text(doc: dict) -> str:
    files = doc["installer"]["files"]
    blocks = []
    for name in files:
        w = next(w for w in doc["written"] if w["file"].endswith(f"/{name}"))
        path = os.path.join(OUT_BANKS, name)
        blocks.append({"name": name, "sha": w["sha256"], "path": path})
    lines = [
        "<#",
        f"    {TAG} installer (B-11 audio: private copies of the swapped banks).",
        "    Generated by Tools/scripts/bm_audio.py, never run by it.",
        "    Close the game before -Action Install. Rollback091 restores every bank the dropzone",
        "    already had (from the .bm004-backup copy) and removes the ones this build added.",
        "    -GameDir defaults to the real install; point it at a copy to rehearse offline",
        "    (the test-091 re-install only runs against the real path).",
        "#>",
        "[CmdletBinding()]",
        "param([ValidateSet('Install','Verify','Rollback091','Status')]"
        "[string]$Action = 'Status', "
        f"[string]$GameDir = '{doc['installer']['game_dir']}')",
        "$ErrorActionPreference = 'Stop'",
        f"$BankDir = Join-Path $GameDir '{doc['installer']['drop']}'",
        "$B = '{}'".format(OUT),
        f"$BakSuffix = '.{TAG}-backup'",
        "function DepBank($name, $sha) {",
        "    if (-not (Test-Path -LiteralPath $BankDir)) "
        "{ New-Item -ItemType Directory -Force -Path $BankDir | Out-Null }",
        "    $src = Join-Path $B ('banks\\' + $name)",
        "    $dst = Join-Path $BankDir $name",
        "    $bakPath = $dst + $BakSuffix",
        "    if (Test-Path -LiteralPath $dst) {",
        "        $cur = (Get-FileHash -LiteralPath $dst).Hash",
        "        if ($cur -ne $sha) {",
        "            if (Test-Path -LiteralPath $bakPath) "
        "{ throw ('an un-rolled-back ' + $BakSuffix + ' already guards ' + $name) }",
        "            Copy-Item -LiteralPath $dst -Destination $bakPath -Force",
        "            Write-Host ('backed up ' + $name + ' -> ' + $name + $BakSuffix)",
        "        }",
        "    }",
        "    Copy-Item -LiteralPath $src -Destination $dst -Force",
        "    $got = (Get-FileHash -LiteralPath $dst).Hash",
        "    if ($got -ne $sha) { throw ('bank hash mismatch: ' + $name) }",
        "    Write-Host ('deployed ' + $name)",
        "}",
        "function UnBank($name) {",
        "    $dst = Join-Path $BankDir $name",
        "    $bakPath = $dst + $BakSuffix",
        "    if (Test-Path -LiteralPath $bakPath) {",
        "        Copy-Item -LiteralPath $bakPath -Destination $dst -Force",
        "        Remove-Item -LiteralPath $bakPath -Force",
        "        Write-Host ('restored ' + $name + ' from ' + $name + $BakSuffix)",
        "    } elseif (Test-Path -LiteralPath $dst) {",
        "        Remove-Item -LiteralPath $dst -Force",
        "        Write-Host ('removed ' + $name + ' (added by this build, no backup)')",
        "    }",
        "}",
        "switch ($Action) {",
        "    'Install' {",
    ]
    for b in blocks:
        lines.append(f"        DepBank '{b['name']}' '{b['sha']}'")
    lines += [f"        Write-Host 'deployed {TAG} audio banks'", "    }", "    'Verify' {"]
    for b in blocks:
        lines += [
            f"        $p = Join-Path $BankDir '{b['name']}'",
            "        if (-not (Test-Path -LiteralPath $p)) "
            "{ throw ('missing ' + $p) }",
            f"        $got = (Get-FileHash -LiteralPath $p).Hash",
            f"        if ($got -ne '{b['sha']}') {{ throw ('bank differs: ' + $p) }}",
            f"        Write-Host ('verified {b['name']} ' + $got)",
        ]
    lines += ["    }", "    'Rollback091' {"]
    for b in blocks:
        lines.append(f"        UnBank '{b['name']}'")
    lines += [
        f"        if ($GameDir -eq '{doc['installer']['game_dir']}') {{",
        "            & (Join-Path 'E:\\Modding\\JustCause3\\JC3-Batmobile\\Builds\\test-091' 'install.ps1') "
        "-Action Install",
        "        } else {",
        "            Write-Host ('rehearsal on ' + $GameDir + ': test-091 re-install skipped')",
        "        }",
        "        Write-Host 'rolled back to test-091, banks restored'",
        "    }",
        "    'Status' {",
        "        Write-Host ('bank dir: ' + $BankDir)",
    ]
    for b in blocks:
        lines += [
            f"        $p = Join-Path $BankDir '{b['name']}'",
            "        $h = if (Test-Path -LiteralPath $p) "
            "{(Get-FileHash -LiteralPath $p).Hash} else {'none'}",
            "        $bk = if (Test-Path -LiteralPath ($p + $BakSuffix)) {'yes'} else {'no'}",
            f"        Write-Host ('{b['name']}: ' + $h + ' (backup ' + $bk + ')')",
            f"        if ($h -eq '{b['sha']}') "
            f"{{ Write-Host '  == {TAG} {b['name']} (match)' }}",
        ]
    lines += ["    }", "}"]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ check
def check() -> int:
    doc = build(write=False)
    fails: list[str] = []
    for w in doc["written"]:
        path = os.path.join(ROOT, w["file"])
        if not os.path.exists(path):
            fails.append(f"{w['file']} missing (run --write)")
            continue
        blob = open(path, "rb").read()
        if sha256(blob) != w["sha256"]:
            fails.append(f"{w['file']} differs from the derived bytes")
        if len(blob) != w["bytes"]:
            fails.append(f"{w['file']}: {len(blob)} B vs {w['bytes']}")
    # the Done checks, re-run on the files on disk (not on the in-memory copies)
    for w in doc["written"]:
        path = os.path.join(ROOT, w["file"])
        if not os.path.exists(path):
            continue
        raw = open(path, "rb").read()
        base, fsb = fsb_of(raw)
        if len(fsb.samples) != w["samples"]:
            fails.append(f"{w['bank']}: {len(fsb.samples)} samples, manifest {w['samples']}")
        for e in [s for s in doc["slots"] if s["bank"] == w["bank"]]:
            got = vgm(path, e["index"])
            # the payload bytes themselves: a same-length edit inside a sample has to fail too
            s = fsb.samples[e["index"] - 1]
            data = bytes(s.data)
            hlen = len(data) - s.samples * int(e["channels"]) * 2
            if hlen < 0 or sha256(data[hlen:]) != e["payload_sha256"]:
                fails.append(f"{w['bank']} #{e['index']}: payload bytes differ from the "
                             f"manifest (sha256)")
            if got["frames"] != e["frames"]:
                fails.append(f"{w['bank']} #{e['index']}: {got['frames']} frames, "
                             f"manifest {e['frames']}")
            if got["name"] != e["name"]:
                fails.append(f"{w['bank']} #{e['index']}: name {got['name']!r}")
            if abs(got["frames"] / float(got["rate"]) -
                   e["written"]["duration_s"]) > 1e-6:
                fails.append(f"{w['bank']} #{e['index']}: duration moved")
        f = jc3audio.fev(raw)
        evs = {x["guid"] for x in jc3audio.fev_events(raw, f)}
        tunes = {x["event_guid"] for x in jc3audio.fev_tunes(raw, f)}
        for e in [s for s in doc["slots"] if s["bank"] == w["bank"] and s["guid"]]:
            g = e["guid"].replace("-", "")
            if g not in evs:
                fails.append(f"{w['bank']}: event {e['guid']} missing")
            if g not in tunes:
                fails.append(f"{w['bank']}: tune for {e['guid']} missing")
    # fmod_guids + installer + manifest
    gp = os.path.join(ROOT, doc["fmod_guids"]["file"])
    if not os.path.exists(gp):
        fails.append(f"{doc['fmod_guids']['file']} missing")
    elif sha256(open(gp, "rb").read()) != doc["fmod_guids"]["sha256"]:
        fails.append(f"{doc['fmod_guids']['file']} differs from the re-emitted bytes")
    ip = os.path.join(OUT, "install.ps1")
    if not os.path.exists(ip):
        fails.append(f"Builds/{TAG}/install.ps1 missing")
    else:
        ps = open(ip, encoding="utf-8").read()
        if ps != installer_text(doc):
            fails.append("install.ps1 is stale against the re-derived text")
        for a in doc["installer"]["actions"]:
            if f"'{a}'" not in ps:
                fails.append(f"install.ps1 has no {a!r} action")
        for w in doc["written"]:
            if w["sha256"] not in ps:
                fails.append(f"install.ps1 does not pin {w['bank']}.bank")
    if os.path.exists(MANIFEST):
        old = open(MANIFEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if old != json.dumps(public(doc), indent=1) + "\n":
            fails.append(f"{rel(MANIFEST)} differs from the re-derived record")
    else:
        fails.append(f"{rel(MANIFEST)} missing (run --write)")
    if fails:
        for f in fails[:20]:
            print("FAIL:", f)
        return 1
    s = doc["summary"]
    print(f"PASS: {s['mapped_rows']} mapped rows, {s['slots_written']} slots in "
          f"{s['banks']} banks ({s['sample_count']} samples), {s['resolved']} events resolved, "
          f"max LU delta {s['max_lu_delta']:.2f} <= {s['lu_tolerance']:.2f} | "
          f"banks {', '.join(f'{k} {v:,} B' for k, v in s['bytes'].items())} "
          f"(size unchanged {s['size_unchanged']}) | .ee.fmod_guids "
          f"{doc['fmod_guids']['bytes']} B, {doc['fmod_guids']['count']} GUIDs | "
          f"installer {len(doc['written'])} bank(s) + rollback")
    return 0


def public(doc: dict) -> dict:
    """The JSON-safe view: the sample arrays never leave the process (only their sha256)."""
    out = {k: v for k, v in doc.items() if k != "slots"}
    out["slots"] = [{k: v for k, v in s.items() if k != "payload"} for s in doc["slots"]]
    return json.loads(json.dumps(out, default=list))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write the banks, manifest, build")
    g.add_argument("--check", action="store_true", help="re-derive and compare (no writes)")
    a = ap.parse_args()
    if a.check:
        sys.exit(check())

    # the build tree first (bm-001's aaf, identity): build() writes the banks and the
    # `.ee.fmod_guids` into it, so the tree has to exist before it runs
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(BASE, "aaf"), os.path.join(OUT, "aaf"))
    doc = build()
    with open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
        f.write(installer_text(doc))
    receipt = {
        "schema": SCHEMA, "card": CARD, "tag": TAG, "base": rel(BASE),
        "aaf_identity": {"source": rel(os.path.join(BASE, "aaf")),
                         "note": "the .ee/.toc are bm-001's, unchanged: B-11 ships loose banks"},
        "banks": doc["written"], "slots": public(doc)["slots"],
        "fmod_guids": doc["fmod_guids"], "summary": doc["summary"],
        "installer": doc["installer"], "installed": False,
    }
    with open(os.path.join(OUT, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(public(doc), indent=1) + "\n")
    s = doc["summary"]
    print(f"wrote {rel(OUT_BANKS)}/*.bank, {rel(MANIFEST)}, {rel(OUT)}/install.ps1 + "
          f"receipt.json: {s['slots_written']} slots, {s['banks']} banks, "
          f"{s['resolved']} events resolved, max LU delta {s['max_lu_delta']:.2f}")
    for w in doc["written"]:
        print(f"  {w['bank']}.bank {w['bytes']:,} B sha256 {w['sha256'][:16]}… "
              f"({w['samples']} samples, size unchanged {w['size_unchanged']})")


if __name__ == "__main__":
    main()
