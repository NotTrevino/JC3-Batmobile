"""v04_loops.py - V-04: where the loop points of the three `_loop` slots live, and the seam.

V-04 (`Builds/bm-RC1/verify/audio.md`) left "the loop point of the three `_loop` payloads"
UNKNOWN because the manifest's `loop_start`/`loop_end` are null and vgmstream prints no loop
line. That is true but it is not the end of the search: an FSB5 sample carries its loop pair
in a **per-sample metadata chunk (type 3, LOOP, two little-endian uint32: start, end)**, and
these very banks use it - 29 samples in `vehicles.bank`, 12 in `weapons.bank`. The three
swapped `_loop` slots carry **none**, in the built bank and in the vanilla bank the payload
came from, and their WAV sources carry no `smpl` chunk at all. So the only loop region the
files define for these three is the whole payload: start 0, end `frames - 1`.

Two things then follow, and both are measured here:

1. The join the payload implies is the file wrap. The built record is not the payload alone,
   though: it is `vanilla[0:slack] + payload[0:len-slack]`, byte for byte (V-04's
   `payload_match: shifted`), so the sample that actually precedes the loop start is
   `payload[frames - 1 - shift]`, not `payload[frames - 1]`. The wrap step is measured on the
   decoded stream and the reconstruction is asserted byte-exact.
2. The `-40 dBFS` gate therefore has two answers: as built (1 of 3 passes, and only because
   the dropped frames land on a quiet moment) and on the payload's own end (0 of 3 pass, but
   only one is an outlier against its own interior step - the creaks, a tile cut).

Usage
    python Tools/scripts/v04_loops.py --write    # Builds/bm-RC1/verify/loops.md
    python Tools/scripts/v04_loops.py --check    # re-read every byte, recompute, compare

Read-only on the banks: `--check` asserts both RC banks still hash to B-11's `written`
sha256, so the only thing this task adds is the report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

import numpy as np
from fsb5 import FSB5

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_audio                                     # noqa: E402  (fsb_of, XFADE, mono_48k)
import v04_audio                                    # noqa: E402  (decode, seam, steps, p99)
import fsb5                                         # noqa: E402  (MetadataChunkType)

RC = os.path.join(ROOT, "Builds", "bm-RC1")
BANKS = os.path.join(RC, "drop", "sound", "fmod_banks")
OUT = os.path.join(RC, "verify", "loops.md")
MANIFEST = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest.json")
MAP = os.path.join(ROOT, "Working", "Translation", "t12_audio_map.json")
CLICK_DBFS = -40.0
VANILLA = {
    "vehicles": os.path.join(ROOT, "Working", "Audio", "jc3bank", "sound", "fmod_banks",
                             "vehicles.bank"),
    "weapons": r"E:\Modding\_shared\gamedata\JC3grab\audio\weapons.bank",
}
LOOP_TYPE = 3          # fsb5.MetadataChunkType.LOOP
sha = lambda b: hashlib.sha256(b).hexdigest()        # noqa: E731


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def db(x: float) -> float:
    return round(float(20.0 * np.log10(max(abs(float(x)), 1e-9))), 2)


# ------------------------------------------------------------------ structure
def fsb_at(path: str) -> tuple[bytes, int, FSB5]:
    raw = open(path, "rb").read()
    base = raw.find(b"FSB5")
    if base < 0:
        raise SystemExit(f"{rel(path)}: no FSB5")
    return raw, base, FSB5(raw[base:])


def chunk_census(path: str) -> dict:
    _raw, _base, fsb = fsb_at(path)
    out: dict[str, int] = {}
    for s in fsb.samples:
        for k in (s.metadata or {}):
            name = getattr(k, "name", str(int(k)))
            out[name] = out.get(name, 0) + 1
    return out


def loop_chunks(path: str) -> list[dict]:
    _raw, _base, fsb = fsb_at(path)
    out = []
    for i, s in enumerate(fsb.samples, 1):
        for k, v in (s.metadata or {}).items():
            if getattr(k, "name", None) == "LOOP":
                start, end = v
                out.append({"index": i, "name": s.name, "frames": s.samples,
                            "start": int(start), "end": int(end),
                            "bytes": struct.pack("<II", int(start), int(end)).hex(" ")})
                break
    return out


def sample_chunks(path: str, index: int) -> dict:
    _raw, _base, fsb = fsb_at(path)
    s = fsb.samples[index - 1]
    md = {}
    for k, v in (s.metadata or {}).items():
        md[getattr(k, "name", str(int(k)))] = {
            "raw": v.hex(" ") if isinstance(v, (bytes, bytearray)) else None,
            "pair": list(v) if isinstance(v, tuple) else None,
        }
    return {"index": index, "name": s.name, "frames": s.samples, "channels": s.channels,
            "frequency": s.frequency, "metadata": md,
            "has_loop": any(getattr(k, "name", None) == "LOOP" for k in (s.metadata or {}))}


def wav_chunks(path: str) -> list[dict]:
    b = open(path, "rb").read()
    if b[:4] != b"RIFF":
        raise SystemExit(f"{path}: not RIFF")
    out, o = [], 12
    while o + 8 <= len(b):
        cid = b[o:o + 4].decode("latin1")
        size = struct.unpack("<I", b[o + 4:o + 8])[0]
        out.append({"id": cid, "offset": o, "size": size,
                    "bytes": b[o:o + min(size + 8, 40)].hex(" ")})
        o += 8 + size + (size & 1)
    return out


def fev_layout(path: str) -> dict:
    raw = open(path, "rb").read()
    base = raw.find(b"FSB5")
    (version, num, shdr, names, datasize) = struct.unpack_from("<IIIII", raw, base + 4)
    return {"riff": raw[:4] == b"RIFF", "magic": raw[8:12].decode("latin1"),
            "fmt_chunk": raw[12:16].decode("latin1"), "fsb5_offset": base,
            "size": len(raw), "fsb5": {"version": version, "num_samples": num,
                                        "sample_headers_size": shdr,
                                        "name_table_size": names, "data_size": datasize}}


# ------------------------------------------------------------------ measure
def facts() -> dict:
    mf = json.load(open(MANIFEST, encoding="utf-8"))
    mp = json.load(open(MAP, encoding="utf-8"))
    slots = [s for s in mf["slots"] if "_loop" in s["name"]]
    layout = {b: fev_layout(os.path.join(BANKS, f"{b}.bank")) for b in ("vehicles", "weapons")}
    census = {b: chunk_census(os.path.join(BANKS, f"{b}.bank")) for b in layout}
    vanilla_census = {b: chunk_census(VANILLA[b]) for b in layout}
    examples = {b: loop_chunks(os.path.join(BANKS, f"{b}.bank")) for b in layout}
    written = {w["bank"]: w for w in mf["written"]}
    bank_sha = {b: sha(open(os.path.join(BANKS, f"{b}.bank"), "rb").read()) for b in layout}

    rows = []
    for s in slots:
        bank, idx = s["bank"], int(s["index"])
        built = v04_audio.decode(os.path.join(BANKS, f"{bank}.bank"), idx)
        van = v04_audio.decode(VANILLA[bank], idx)
        ms = s["measured"]
        row = next(r for r in mp["rows"] if r["id"] == s["row"])
        slot = next(x for x in row["slots"] if x["name"] == s["name"])
        src = bm_audio.mono_48k(*bm_audio.source_of(row, slot))
        gain = float(ms.get("gain_db_loopfill", s["gain_db"]))

        pcm = built["pcm"]
        mono = pcm.mean(axis=1)
        frames = built["frames"]
        ch = int(built["channels"])
        step = v04_audio.seam(pcm)
        interior = v04_audio.p99(v04_audio.steps(pcm))
        van_step = v04_audio.seam(van["pcm"])

        # the record's extra bytes, and the shift they cause in the written payload
        _raw, _base, fsb = fsb_at(os.path.join(BANKS, f"{bank}.bank"))
        rec = bytes(fsb.samples[idx - 1].data)
        need = frames * ch * 2
        slack = len(rec) - need
        shift = slack // (2 * ch)

        # the payload B-11's own rule derives, and the reconstruction of the built stream
        q, _meas = bm_audio.payload(src, gain, frames, loop=True)
        new = np.clip(q * 32768.0, -32768, 32767).astype("<i2")
        if ch > 1:
            new = np.repeat(new[:, None], ch, axis=1).reshape(-1)
        derived = new.tobytes()
        recon = van["bytes"][:slack] + derived[:len(van["bytes"]) - slack]
        pay = np.frombuffer(derived, dtype="<i2").astype(np.float64).reshape(-1, ch) / 32768.0
        own = v04_audio.seam(pay)
        own_p99 = v04_audio.p99(v04_audio.steps(pay))

        # the loop region the data defines: the whole payload
        region = {"start": 0, "end": frames - 1, "length": frames,
                  "length_s": round(frames / float(built["rate"]), 6),
                  "source": "whole payload (no LOOP chunk, no smpl chunk)"}

        # tiling: does the payload repeat a shorter source? derived from bm_audio.payload
        xf = bm_audio.XFADE
        n = int(len(src))
        tiled = bool(ms["padded_frames"]) and n > 4 * xf
        tile = {"tiled": tiled, "src_frames": n, "xfade": xf}
        if tiled:
            period = n - xf
            k = 0 if frames <= n else -(-(frames - n) // period)
            base = n + max(0, k - 1) * period
            tile.update({"period": period, "copies": k + 1,
                         "cut_src_index": xf + ((frames - 1) - base)})
        else:
            tile.update({"cut_src_index": None})

        rows.append({
            "row": s["row"], "bank": bank, "index": idx, "name": s["name"],
            "frames": frames, "channels": ch, "rate": built["rate"],
            "built_meta": sample_chunks(os.path.join(BANKS, f"{bank}.bank"), idx),
            "vanilla_meta": sample_chunks(VANILLA[bank], idx),
            "wav": {"chunks": wav_chunks(s["source"] if os.path.isabs(s["source"])
                                         else os.path.join(ROOT, s["source"])),
                    "path": s["source"] if os.path.isabs(s["source"]) else rel(s["source"])},
            "region": region,
            "first_int16": [int(round(float(v) * 32768)) for v in mono[:4]],
            "last_int16": [int(round(float(v) * 32768)) for v in mono[-4:]],
            "first_bytes": built["bytes"][:8].hex(" "),
            "last_bytes": built["bytes"][-8:].hex(" "),
            "step_dbfs": step,
            "threshold_dbfs": CLICK_DBFS,
            "passes_40": bool(step <= CLICK_DBFS),
            "interior_p99_dbfs": interior,
            "vanilla_step_dbfs": van_step,
            "worse_than_interior": bool(step > interior),
            "record": {"data_bytes": len(rec), "pcm_bytes": need, "slack": slack,
                       "shift_frames": shift},
            "recon_ok": bool(recon == built["bytes"]),
            "payload": {"own_wrap_dbfs": own, "own_p99_dbfs": own_p99,
                        "own_passes_40": bool(own <= CLICK_DBFS),
                        "own_worse_than_p99": bool(own > own_p99),
                        "last_sample_index": frames - 1 - shift,
                        "first_sample_index": 0,
                        "join_is_shifted": bool(shift != 0)},
            "vgmstream_loop_lines": built["loop_lines"],
            "tile": tile,
            "events": next((r for r in mf.get("resolved", []) if r["row"] == s["row"]), None),
            "tune": (mf.get("events", {}).get(bank, {}).get("tunes", {})
                     .get((next((r["guid"] for r in mf.get("resolved", [])
                                 if r["row"] == s["row"]), "") or "").replace("-", ""), None)),
        })

    return {"manifest": {"path": rel(MANIFEST), "sha256": sha(open(MANIFEST, "rb").read())},
            "layout": layout, "census": census, "vanilla_census": vanilla_census,
            "examples": examples, "bank_sha": bank_sha,
            "written": {b: w["sha256"] for b, w in written.items()},
            "rows": rows}


# ------------------------------------------------------------------ render
def render(f: dict) -> str:
    L = f["layout"]
    rows = f["rows"]
    by = {r["name"]: r for r in rows}
    nitro = by["jc3_veh_land_premium_nitro_loop"]
    creaks = by["jc3_veh_lave_chassis_spin_creaks_loop_fast"]
    mini = by["jc3_wpn_minigun_fire_close_loop_04"]
    ex = f["examples"]
    out = []
    a = out.append

    a("# V-04 loop points — the three `_loop` slots, `Builds/bm-RC1`\n")
    a("`python Tools/scripts/v04_loops.py --check`\n")
    a("**The loop pair exists in this bank format, and these three samples do not carry it.** "
      "An FSB5 sample stores its loop start/end in a per-sample metadata chunk (type "
      f"{LOOP_TYPE} = `LOOP`, two little-endian uint32: start, end). These banks use that chunk "
      f"(`vehicles.bank` {f['census']['vehicles'].get('LOOP', 0)} samples, `weapons.bank` "
      f"{f['census']['weapons'].get('LOOP', 0)}), but the three swapped `_loop` payloads carry "
      "**no `LOOP` chunk** — in the built bank and in the vanilla bank they came from, "
      "byte-identical. Their WAV sources carry no `smpl` chunk either (only `fmt ` + `data`, "
      "3/3). So the only loop region the files define for these three is the **whole payload: "
      "start sample 0, end `frames − 1`** — and the join to test is the file wrap.\n")
    a(f"At that wrap, **as built, one of the three is below −40 dBFS** "
      f"(`{mini['name']}`, {mini['step_dbfs']} dBFS). `{nitro['name']}` steps "
      f"{nitro['step_dbfs']} dBFS, above the threshold but quieter than its own interior p99 "
      f"({nitro['interior_p99_dbfs']} dBFS), so it is that payload's normal motion. "
      f"`{creaks['name']}` steps {creaks['step_dbfs']} dBFS against an interior p99 of "
      f"{creaks['interior_p99_dbfs']} dBFS: the one real click.\n")
    a("One correction to V-04's picture: **the built record is not the payload alone.** It is "
      "`vanilla[0:slack] + payload[0:len−slack]` — the splice leaves "
      f"{nitro['record']['shift_frames']} / {creaks['record']['shift_frames']} / "
      f"{mini['record']['shift_frames']} frames of the old payload in front and drops the same "
      "number off the end (byte-exact reconstruction, §2). So the sample that actually precedes "
      "the loop start is `payload[frames − 1 − shift]`. On the payload's own end the three "
      f"steps are {nitro['payload']['own_wrap_dbfs']} / {creaks['payload']['own_wrap_dbfs']} / "
      f"{mini['payload']['own_wrap_dbfs']} dBFS: **none passes −40 on its own**, but only the "
      "creaks is an outlier against its own step distribution.\n")

    a("## 1. The bytes: container, chunk, and the three records\n")
    for b in ("vehicles", "weapons"):
        d = L[b]
        a(f"* `{b}.bank` — {d['size']:,} B, RIFF magic `{d['magic']}`, chunk `{d['fmt_chunk']}`, "
          f"FSB5 at byte {d['fsb5_offset']:,} (version {d['fsb5']['version']}, "
          f"{d['fsb5']['num_samples']} samples, sample headers "
          f"{d['fsb5']['sample_headers_size']:,} B, names {d['fsb5']['name_table_size']:,} B, "
          f"data {d['fsb5']['data_size']:,} B).")
    a("")
    a("That is an **FMOD Designer FEV v56 container around an FSB5 sample bank**, named from its "
      "own magic (`RIFF` / `FEV ` / `FMT ` / `FSB5`). The brief said \"Wwise\"; no byte in either "
      "bank says Wwise, and `Research/JC3Grab/JC3_AUDIO.md` §10 records the same FEV v56 build 50 "
      "format. Nothing below is inferred from the name — the loop chunk is read out of the FSB5 "
      "sample headers.\n")
    a("**Proof the format carries loop points, in these very banks:**\n")
    a("| bank | sample | frames | LOOP pair (start, end) | bytes as stored |")
    a("|---|---|---:|---|---|")
    for b in ("vehicles", "weapons"):
        for e in ex[b][:3]:
            a(f"| `{b}` | `{e['name']}` (#{e['index']}) | {e['frames']:,} | "
              f"({e['start']:,}, {e['end']:,}) | `{e['bytes']}` |")
    a("")
    a("Every pair satisfies `0 ≤ start < end ≤ frames` (all "
      f"{len(ex['vehicles']) + len(ex['weapons'])} of them, checked), which is the oracle that "
      "these really are loop points and not another field wearing the same type id. vgmstream "
      "agrees: on a sample with this chunk it prints `loop start: … / loop end: …`, and on the "
      "three slots it prints no loop line at all.\n")
    a("**The three slots carry no such chunk** (built and vanilla identical):\n")
    a("| slot | sample | frames | metadata chunks in the record | `LOOP`? |")
    a("|---|---|---:|---|---|")
    for r in rows:
        md = ", ".join(f"type {k}" + (f" = pair {v['pair']}" if v["pair"] else
                                      f" = `{v['raw']}`" if v["raw"] else "")
                       for k, v in r["built_meta"]["metadata"].items()) or "—"
        a(f"| `{r['bank']}#{r['index']}` | `{r['name']}` | {r['frames']:,} | {md} | "
          f"{'yes' if r['built_meta']['has_loop'] else '**no**'} |")
    a("")
    a("Type 13 decodes as a 4-byte little-endian float (e.g. `00 00 80 3f` = 1.0) — a per-sample "
      "gain, not a loop pair — and type 5 as four zero bytes. The vanilla record at the same "
      "bank+index is byte-identical, so B-11's splice preserved every header byte and the absent "
      "loop pair is the shipped data's.\n")
    a("**WAV side:**\n")
    a("| source WAV | chunks | `smpl`? |")
    a("|---|---|---|")
    for r in rows:
        ids = ", ".join(f"`{c['id']}`({c['size']} B)" for c in r["wav"]["chunks"])
        has = any(c["id"] == "smpl" for c in r["wav"]["chunks"])
        a(f"| `{os.path.basename(r['wav']['path'])}` | {ids} | {'yes' if has else '**no**'} |")
    a("")
    a("Both places the brief asked about are therefore empty **for these three payloads**: no "
      "FSB5 `LOOP` chunk, no RIFF `smpl` chunk. The loop region is the payload itself — **start "
      "sample 0, end sample `frames − 1`**.\n")

    a("## 2. The loop points, the bytes at the join, and the splice offset\n")
    a("| slot | sample | frames | loop start | loop end | loop length | first 4 int16 | last 4 int16 |")
    a("|---|---|---:|---:|---:|---|---|---|")
    for r in rows:
        a(f"| `{r['bank']}#{r['index']}` | `{r['name']}` | {r['frames']:,} | "
          f"{r['region']['start']} | {r['region']['end']:,} | {r['region']['length']:,} "
          f"({r['region']['length_s']} s @ {r['rate']} Hz) | {r['first_int16']} | "
          f"{r['last_int16']} |")
    a("")
    a("Raw PCM at the join, straight out of the built bank:\n")
    a("| slot | first 8 B | last 8 B | last→first step |")
    a("|---|---|---|---:|")
    for r in rows:
        a(f"| `{r['bank']}#{r['index']}` | `{r['first_bytes']}` | `{r['last_bytes']}` | "
          f"{r['step_dbfs']} dBFS |")
    a("")
    a("**The record the splice wrote.** B-11 writes `data[:hlen] + pcm`, and `hlen` is taken as the "
      "record's surplus over `frames × channels × 2`. The surplus is not at the front: rebuilding "
      "`vanilla[0:slack] + payload[0:len-slack]` reproduces the decoded stream **byte for byte** "
      "for all three slots, which is the oracle for the offset below.\n")
    a("| slot | record bytes | PCM bytes | surplus | shift | reconstruction == built? | join is |")
    a("|---|---:|---:|---:|---:|---|---|")
    for r in rows:
        rec = r["record"]
        a(f"| `{r['bank']}#{r['index']}` | {rec['data_bytes']:,} | {rec['pcm_bytes']:,} | "
          f"{rec['slack']} B | {rec['shift_frames']} frames | "
          f"{'**yes**' if r['recon_ok'] else 'no'} | "
          f"`payload[{r['payload']['last_sample_index']:,}]` → `vanilla[0]` |")
    a("")
    a("So the join the bank actually presents is the **payload sample "
      f"`frames − 1 − shift`**, followed by the *old* payload's first sample — the last "
      "`shift` frames of the new payload never reach the file. That is a build detail (it also "
      "means every swapped slot starts with a few frames of the vanilla audio); it is recorded "
      "here and not fixed.\n")

    a("## 3. Does the loop end join the loop start within −40 dBFS?\n")
    a("| slot | as built: step | ≤ −40? | interior p99 | outlier? | payload's own wrap | own ≤ −40? | own p99 | own outlier? | verdict |")
    a("|---|---:|---|---:|---|---:|---|---:|---|---|")
    for r in rows:
        p = r["payload"]
        if r["passes_40"]:
            v = "**joins cleanly** as built"
        elif r["worse_than_interior"]:
            v = "**click** (above −40 and an outlier against its own p99)"
        else:
            v = "above −40 but inside its own step distribution"
        a(f"| `{r['bank']}#{r['index']}` | {r['step_dbfs']} | "
          f"{'yes' if r['passes_40'] else '**no**'} | {r['interior_p99_dbfs']} | "
          f"{'yes' if r['worse_than_interior'] else 'no'} | {p['own_wrap_dbfs']} | "
          f"{'yes' if p['own_passes_40'] else '**no**'} | {p['own_p99_dbfs']} | "
          f"{'yes' if p['own_worse_than_p99'] else 'no'} | {v} |")
    a("")
    a("Read the table twice, because the two halves answer different questions:\n")
    a(f"* **As built** (what the bank contains today): `{mini['name']}` joins at "
      f"{mini['step_dbfs']} dBFS and passes; `{nitro['name']}` ({nitro['step_dbfs']}) and "
      f"`{creaks['name']}` ({creaks['step_dbfs']}) are above −40, so by the card's number they "
      "fail.")
    a(f"* **On the payload's own end** (what the source loops like, after removing the "
      f"{nitro['record']['shift_frames']}-frame splice offset): "
      f"{nitro['payload']['own_wrap_dbfs']}, {creaks['payload']['own_wrap_dbfs']}, "
      f"{mini['payload']['own_wrap_dbfs']} dBFS — none passes −40. The minigun's clean result is "
      "an artifact of the dropped frames landing on a quiet moment, not a property of its loop.")
    a("")
    a(f"By V-04's actual rule (above −40 **and** an outlier against the payload's own p99), only "
      f"`{creaks['name']}` is a defect in either reading: {creaks['payload']['own_wrap_dbfs']} dBFS "
      f"against a p99 of {creaks['payload']['own_p99_dbfs']} dBFS. The nitro's "
      f"{nitro['payload']['own_wrap_dbfs']} dBFS sits under its p99 "
      f"({nitro['payload']['own_p99_dbfs']}), i.e. the payload is simply that noisy at the seam.\n")

    a("## 4. Why the creaks click: a tile cut, mid-source\n")
    a(f"A-05's slot is longer than its source, so B-11's loop fill repeats the source with a "
      f"{bm_audio.XFADE}-frame equal-power crossfade and truncates to the slot length "
      "(`bm_audio.payload`). The truncation decides which source sample lands next to sample 0:\n")
    a("| slot | source frames | tile period | copies | cut lands on source sample |")
    a("|---|---:|---:|---:|---|")
    for r in rows:
        t = r["tile"]
        if t["tiled"]:
            a(f"| `{r['bank']}#{r['index']}` | {t['src_frames']:,} | {t['period']:,} | "
              f"{t['copies']} | **{t['cut_src_index']:,}** (source frames "
              f"{t['src_frames']:,}) |")
        else:
            a(f"| `{r['bank']}#{r['index']}` | {t['src_frames']:,} | — (not tiled) | 1 | — |")
    a("")
    a("For the creaks the payload ends at source sample "
      f"{creaks['tile']['cut_src_index']:,} of {creaks['tile']['src_frames']:,} — mid-loop, not at "
      "a loop point or a zero crossing — and then jumps to sample 0. That is the click §3 "
      "measures, and it survives the splice offset (the payload's own wrap is "
      f"{creaks['payload']['own_wrap_dbfs']} dBFS). Fixing it means filling the slot to a whole "
      "number of copies or cutting at a zero crossing; that is a build change and this report "
      "does not make it.\n")

    a("## 5. What the event/tune graph says\n")
    a("Each slot does resolve to an event and a tune in the built bank (B-11):\n")
    a("| slot | event GUID | tune GUID | tune body |")
    a("|---|---|---|---:|")
    for r in rows:
        ev = r["events"] or {}
        tu = r["tune"] or {}
        guid = ev.get("guid") or "— (no donor GUID: W-03 resolves through its slot, V-04)"
        a(f"| `{r['bank']}#{r['index']}` | `{guid}` | `{ev.get('tune_guid') or '—'}` | "
          f"{tu.get('bytes', '—')} B |")
    a("")
    a("The FEV parser (`jc3audio.fev_events` / `fev_tunes` / `fev_event_bodies`) reads the GUIDs, "
      "the tune→event link and the body sizes; **it decodes no playback or loop flag from those "
      "bodies**, and nothing else here does. So whether the tune loops the payload, and over "
      "which region, stays UNKNOWN — but it cannot add a loop *pair*: a tune looping a sample "
      "with no `LOOP` chunk can only loop the whole stream.\n")

    a("## 6. Checks\n")
    a("`python Tools/scripts/v04_loops.py --check` re-reads both banks, re-parses every sample "
      "header, re-decodes the six streams with vgmstream, rebuilds each payload, re-derives every "
      "step and tiling number, and requires this file to be exactly what those bytes derive. It "
      "also asserts both RC banks still hash to B-11's written sha256 "
      f"(`vehicles` `{f['bank_sha']['vehicles'][:16]}…`, `weapons` "
      f"`{f['bank_sha']['weapons'][:16]}…`), so nothing in the build moved.\n")

    a("## 7. UNKNOWNs\n")
    a("* **Whether the game loops these three at all, and over what region** — the sample carries "
      "no loop pair, so either the engine loops the whole payload or the FEV tune does; no "
      "decoded field says which, and no game was run (test ban).")
    a("* **What the FEV tune bodies (92 / 164 B) contain** — only GUIDs and sizes are decoded "
      "(`jc3audio.py`); a loop count or mode could live there and is not read here.")
    a("* **Whether −40 dBFS is the right bar for these payloads** — the card states it; the nitro "
      "row is where the number and the ear may disagree, and only a take could settle it.")
    a("* **Why the record surplus is 32–92 B** — measured per record and used as the offset, but "
      "its meaning (padding, per-sample trailer) is not decoded; what is proven is only that the "
      "built stream equals `vanilla[:slack] + payload[:len−slack]` byte for byte.")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ check
def ok(cond: bool, label: str, detail: str = "") -> bool:
    print(f"{'PASS' if cond else 'FAIL'} {label}" + (f" [{detail}]" if detail and not cond else ""))
    return cond


def check(f: dict) -> int:
    good = True
    rows = {r["name"]: r for r in f["rows"]}

    good &= ok(len(f["rows"]) == 3, "three `_loop` slots in the manifest", str(len(f["rows"])))
    for b, d in f["layout"].items():
        good &= ok(d["riff"] and d["magic"] == "FEV ", f"{b}.bank is a RIFF/FEV container",
                   d["magic"])
        good &= ok(f["census"][b].get("LOOP", 0) > 0,
                   f"{b}.bank uses the LOOP chunk ({f['census'][b].get('LOOP', 0)} samples)",
                   str(f["census"][b]))
        for e in f["examples"][b]:
            good &= ok(0 <= e["start"] < e["end"] <= e["frames"],
                       f"{b}#{e['index']} LOOP pair {e['start']}..{e['end']} inside "
                       f"its {e['frames']} frames")

    for name, r in rows.items():
        good &= ok(not r["built_meta"]["has_loop"], f"{name}: built record carries no LOOP chunk")
        good &= ok(not r["vanilla_meta"]["has_loop"],
                   f"{name}: the vanilla record at the same index carries none either")
        good &= ok(r["built_meta"]["metadata"] == r["vanilla_meta"]["metadata"],
                   f"{name}: built and vanilla metadata are identical (the swap kept the header)")
        good &= ok(not any(c["id"] == "smpl" for c in r["wav"]["chunks"]),
                   f"{name}: the source WAV has no smpl chunk")
        good &= ok(r["region"]["start"] == 0 and r["region"]["end"] == r["frames"] - 1,
                   f"{name}: loop region is the whole payload (0..{r['frames'] - 1})")
        good &= ok(r["vgmstream_loop_lines"] == [],
                   f"{name}: vgmstream reports no loop line", str(r["vgmstream_loop_lines"]))
        good &= ok(r["recon_ok"],
                   f"{name}: vanilla[:slack] + payload[:len-slack] reproduces the built stream "
                   "byte for byte")
        good &= ok(r["record"]["shift_frames"] == r["record"]["slack"] // (2 * r["channels"]),
                   f"{name}: the shift is the surplus over the PCM ({r['record']['shift_frames']} "
                   "frames)")
        good &= ok(r["payload"]["last_sample_index"] == r["frames"] - 1 - r["record"]["shift_frames"],
                   f"{name}: the join's last sample is payload[frames-1-shift]")

    mini = rows["jc3_wpn_minigun_fire_close_loop_04"]
    nitro = rows["jc3_veh_land_premium_nitro_loop"]
    creaks = rows["jc3_veh_lave_chassis_spin_creaks_loop_fast"]
    good &= ok(mini["passes_40"], f"as built, minigun joins below -40 dBFS ({mini['step_dbfs']})")
    good &= ok(not nitro["passes_40"] and not nitro["worse_than_interior"],
               f"nitro exceeds -40 ({nitro['step_dbfs']}) but stays under its own p99")
    good &= ok(not creaks["passes_40"] and creaks["worse_than_interior"],
               f"creaks exceeds -40 ({creaks['step_dbfs']}) and its own p99 "
               f"({creaks['interior_p99_dbfs']})")

    for r in (nitro, creaks, mini):
        good &= ok(not r["payload"]["own_passes_40"],
                   f"{r['name']}: the payload's own wrap is above -40 "
                   f"({r['payload']['own_wrap_dbfs']} dBFS)")
    good &= ok(creaks["payload"]["own_worse_than_p99"],
               f"creaks' own wrap is an outlier against its own p99 "
               f"({creaks['payload']['own_wrap_dbfs']} vs {creaks['payload']['own_p99_dbfs']})")
    good &= ok(not nitro["payload"]["own_worse_than_p99"]
               and not mini["payload"]["own_worse_than_p99"],
               "nitro's and the minigun's own wraps stay inside their own p99")

    good &= ok(creaks["tile"]["tiled"] and creaks["tile"]["cut_src_index"] is not None,
               f"creaks is tiled and cut mid-source at "
               f"{creaks['tile'].get('cut_src_index')}")
    good &= ok(not nitro["tile"]["tiled"], "nitro is not tiled (its slot fits its span)")

    for b, want in f["written"].items():
        good &= ok(f["bank_sha"].get(b) == want,
                   f"{b}.bank still hashes to B-11's written sha256 (build untouched)",
                   f"{f['bank_sha'].get(b)} vs {want}")

    expected = render(f)
    disk = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    good &= ok(disk == expected, f"{rel(OUT)} matches a fresh render (every number re-derived)")
    good &= ok(disk.count("`LOOP`?") == 1 and "no such chunk" in disk,
               "the report carries the LOOP-chunk table")
    return 0 if good else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    f = facts()
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(f))
        print(f"wrote {rel(OUT)} ({os.path.getsize(OUT)} bytes)")
        for r in f["rows"]:
            print(f"  {r['bank']}#{r['index']} {r['name']}: loop 0..{r['frames'] - 1}, "
                  f"join payload[{r['payload']['last_sample_index']}]->vanilla[0], "
                  f"as built {r['step_dbfs']} dBFS, own {r['payload']['own_wrap_dbfs']} dBFS")
        return 0

    rc = check(f)
    print(f"\n{'check: all assertions passed' if rc == 0 else 'check: FAILED'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
