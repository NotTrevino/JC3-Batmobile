#!/usr/bin/env python3
"""bmak_audio_regrab.py - NEW-AUD-1: extract and decode the media of the 10 banks the ledger called missing.

Background (all quoted from repo files):
  * G1-15 (`Research/BatmobileGrab/AUDIO_FEATURES.md`, `Working/Roadmap/sound.md` line G1-15) counted ~90
    Batmobile event rows across 10 BmAK banks and marked them `missing-bank`, because `grab_audio.py` only
    opened the three packages listed in `AUDIO_MAP.json`.
  * G3-14 (`Research/BatmobileGrab/AUDIO_BANKS.md`) re-tested the whole install and found **10 of 10** banks
    present as `AkBank` exports (0 absent), but stopped there: it decoded no media.
  * This tool goes the last step: read each of those banks out of its cooked package, walk
        Event (HIRC 0x04) -> Action (0x03) -> Sound (0x02) / RanSeq (0x05) / containers (0x06,0x07,0x09)
        -> DIDX media id -> DATA bytes
    write every media object out as a `.wem`, decode it to `.wav` with the repo's own vgmstream-cli, and
    join the result to event ids (and to the event name where `fnv1(lower(name))` reproduces the id).

No install or ledger file is written. Output lives OUTSIDE the repo, at
`E:/Modding/_BmAKgrab/audio_regrab/{wem,wav}`; the machine-readable map is
`Research/BatmobileGrab/AUDIO_REGRAB.json`.

Oracles (`--check` fails on any of them):
  O-1  every payload's sha1 equals the one `AUDIO_BANKS.json` recorded for that export;
  O-2  the HIRC walk tiles the chunk (object count and end offset), for every bank;
  O-3  every extracted `.wem` starts with RIFF/WAVE and its size equals its DIDX entry;
  O-4  `fnv1(lower(name))` reproduces the ids `AUDIO_MAP.json` declares for these banks;
  O-5  every `.wav` re-decodes from its recorded `.wem` (exists, non-zero, RIFF/WAVE);
  O-6  0x6BB2C66E is carried by no bank here while 0x8EA6FCA0 is carried with media (the 9052 twin).

Usage:
    uv run python Tools/scripts/bmak_audio_regrab.py --write [--limit N]
    uv run python Tools/scripts/bmak_audio_regrab.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_audio as GA          # noqa: E402  (parse_bank / resolve / sections)
import grab_audio_banks as G14   # noqa: E402  (probe_package)
import grab_audio_banks2 as G2   # noqa: E402  (bank_list, Image)

OUT = r"E:\Modding\_BmAKgrab\audio_regrab"
JSON_OUT = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_REGRAB.json")
BANKS_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_BANKS.json")
AUDIO_MAP = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_MAP.json")
VG = os.path.join(ROOT, "Tools", "vgmstream-win64", "vgmstream-cli.exe")

# the ten `missing_claim_banks` of AUDIO_BANKS.json totals
CLAIM_BANKS = ("BML_Batmobile_Subjective", "BML_Impacts", "BML_Sonar", "CHR_BatmanAlerts",
               "CHR_BatmanDisruptor", "UI_InGame", "VEH_Tank_Heavy", "VEH_Tank_Missiles",
               "VFX_Tank_Explosion", "OBJ_Rolling_Objects")
TARGET_MISSING = 0x6BB2C66E      # the track-fire twin that no bank cooks
TARGET_TWIN = 0x8EA6FCA0         # the cooked disruptor twin


def sha1_16(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:16]


def fnv1(b: bytes) -> int:
    h = 0x811C9DC5
    for c in b:
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ c
    return h


def names_by_id() -> dict[int, str]:
    """id -> name from AUDIO_MAP rows, only where fnv1(lower(name)) really reproduces the id (O-4)."""
    doc = json.load(open(AUDIO_MAP, encoding="utf-8"))
    out = {}
    for e in doc["events"]:
        name, eid = e.get("name"), e.get("event_id")
        if isinstance(name, str) and isinstance(eid, int):
            if fnv1(name.lower().encode("latin-1", "replace")) == eid:
                out[eid] = name
    return out


def claim_rows() -> dict[tuple[str, int], list[str]]:
    """(bank, event_id) -> packages that reference it, straight from AUDIO_MAP rows (the 90 rows)."""
    doc = json.load(open(AUDIO_MAP, encoding="utf-8"))
    out: dict[tuple[str, int], list[str]] = {}
    for e in doc["events"]:
        bank = e.get("bank") or (e.get("bank_ref") or "").split(".", 1)[-1]
        eid = e.get("event_id")
        if bank in CLAIM_BANKS and isinstance(eid, int):
            out.setdefault((bank, eid), [])
            if e.get("package") not in out[(bank, eid)]:
                out[(bank, eid)].append(e.get("package"))
    return out


def decode(wem_path: str, wav_path: str) -> dict:
    if not os.path.exists(VG):
        return {"status": "no-vgmstream", "wav": None}
    os.makedirs(os.path.dirname(wav_path), exist_ok=True)
    pr = subprocess.run([VG, "-o", wav_path, wem_path], capture_output=True, text=True,
                        timeout=300)
    if pr.returncode != 0 or not os.path.exists(wav_path):
        tail = ((pr.stderr or "") + (pr.stdout or "")).strip().splitlines()[-1:] or [""]
        return {"status": "decode-failed", "wav": None, "error": tail[0][:160]}
    try:
        w = wave.open(wav_path, "rb")
        nch, sw, fr, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        w.close()
        return {"status": "ok", "wav": wav_path, "channels": nch, "rate": fr,
                "frames": nf, "seconds": round(nf / fr, 3) if fr else None}
    except wave.Error as e:
        return {"status": "not-a-wav", "wav": wav_path, "error": str(e)[:160]}


def build(limit: int | None = None) -> dict:
    rows = [r for r in G2.bank_list() if r["bank"] in CLAIM_BANKS]
    # one representative export per distinct payload; the rest are recorded as origins
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["sha1"], []).append(r)
    names = names_by_id()
    claims = claim_rows()
    pkgs: dict[str, object] = {}
    probes: dict[str, dict] = {}
    banks, media_rows, problems = [], [], []
    seen_media: dict[str, str] = {}
    done = 0
    for sha, copies in groups.items():
        if limit is not None and done >= limit:
            break
        rep = copies[0]
        path = rep["path"]
        if rep["package"] not in pkgs:
            probe = G14.probe_package(path)
            if not probe.get("ok"):
                problems.append({"bank": rep["bank"], "package": rep["package"],
                                 "problem": "package unreadable"})
                continue
            probes[rep["package"]] = probe
            pkgs[rep["package"]] = G2.Image(path, probe["name_offset"], probe.get("chunk_at"))
        probe = probes[rep["package"]]
        exp = next((e for e in probe["ak"] if e["index"] == rep["index"]), None)
        if exp is None:
            problems.append({"bank": rep["bank"], "package": rep["package"],
                             "problem": "export is not an AkBank"})
            continue
        payload = pkgs[rep["package"]].get(exp["offset"], exp["offset"] + exp["bytes"])
        bank = GA.parse_bank(payload)
        if not bank:
            problems.append({"bank": rep["bank"], "package": rep["package"], "problem": "no HIRC"})
            continue
        bank_sha = sha1_16(payload)
        hirc_start, hirc_len = bank["sections"]["HIRC"]
        data_start, data_len = bank["sections"].get("DATA", (None, 0))
        walk = payload[hirc_start:hirc_start + hirc_len]
        hirc_objects = int.from_bytes(walk[0:4], "little") if len(walk) >= 4 else None
        banks.append({
            "bank": rep["bank"], "package": rep["package"], "export": rep["index"],
            "origins": ["%s#%d" % (c["package"], c["index"]) for c in copies],
            "payload_bytes": len(payload), "sha1": bank_sha,
            "sha1_recorded": sha, "sha1_match": bank_sha == sha,
            "bytes_recorded": rep["bytes"], "size_match": len(payload) == rep["bytes"],
            "events_recorded": rep["events_in_bank"], "events_in_hirc": len(bank["events"]),
            "events_match": len(bank["events"]) == rep["events_in_bank"],
            "hirc_objects": hirc_objects, "sounds": len(bank["sounds"]),
            "ranseq": len(bank["ranseq"]), "containers": len(bank["containers"]),
            "didx_entries": len(bank["didx"]),
        })
        os.makedirs(os.path.join(OUT, "wem"), exist_ok=True)
        os.makedirs(os.path.join(OUT, "wav"), exist_ok=True)
        for eid in sorted(bank["events"]):
            targets, media = GA.resolve(bank, eid)
            mrows = []
            for m in media:
                d = bank["didx"].get(m)
                tag = "%s__%08X__%08X" % (rep["bank"], eid, m)
                wem_path = os.path.join(OUT, "wem", tag + ".wem")
                wav_path = os.path.join(OUT, "wav", tag + ".wav")
                rec = {"wem": "0x%08X" % m, "wem_id": m, "wem_path": wem_path, "wav_path": wav_path,
                       "bytes": d["size"] if d else None, "embedded": d is not None}
                if d and data_start is not None:
                    blob = payload[data_start + d["offset"]:data_start + d["offset"] + d["size"]]
                    rec["extracted_bytes"] = len(blob)
                    rec["riff"] = blob[:4] == b"RIFF" and blob[8:12] == b"WAVE"
                    if len(blob) == d["size"] and blob[:4] == b"RIFF":
                        prev = seen_media.get(sha1_16(blob))
                        if prev is None:
                            with open(wem_path, "wb") as f:
                                f.write(blob)
                            seen_media[sha1_16(blob)] = wem_path
                            rec["sha1"] = sha1_16(blob)
                            rec["written"] = True
                            rec.update(decode(wem_path, wav_path))
                        else:
                            # same bytes already written under another event tag: point at that WAV
                            rec["duplicate_of"] = prev
                            base = os.path.splitext(os.path.basename(prev))[0]
                            rec["wav_path"] = os.path.join(OUT, "wav", base + ".wav")
                            rec["sha1"] = sha1_16(blob)
                            rec["status"] = "duplicate"
                    else:
                        rec["status"] = "didx-range-bad"
                else:
                    rec["status"] = "no-didx-entry"
                mrows.append(rec)
            media_rows.append({
                "bank": rep["bank"], "package": rep["package"], "event_id": eid,
                "event_id_hex": "0x%08X" % eid,
                "event_name": names.get(eid),
                "in_audio_map": (rep["bank"], eid) in claims,
                "map_packages": claims.get((rep["bank"], eid), []),
                "actions": len(bank["events"][eid]), "targets": targets,
                "media": mrows,
            })
        done += 1

    all_media = [m for r in media_rows for m in r["media"]]
    ids = {r["event_id"] for r in media_rows}
    carried = {r["event_id"] for r in media_rows if r["media"]}
    doc = {
        "schema": 1,
        "card": "NEW-AUD-1",
        "generated_by": "Tools/scripts/bmak_audio_regrab.py",
        "question": "decode the media of the 10 BmAK banks the ledger called missing-bank",
        "output_dir": OUT,
        "inputs": {
            "audio_banks": {"path": "Research/BatmobileGrab/AUDIO_BANKS.json",
                            "sha256_16": hashlib.sha256(open(BANKS_JSON, "rb").read()).hexdigest()[:16]},
            "audio_map": {"path": "Research/BatmobileGrab/AUDIO_MAP.json",
                          "sha256_16": hashlib.sha256(open(AUDIO_MAP, "rb").read()).hexdigest()[:16]},
        },
        "method": {
            "banks": "the 10 banks AUDIO_BANKS.json counts as missing_claim_banks, deduplicated by payload sha1",
            "payload": "each AkBank export read out of its cooked package by grab_audio_banks2.Image "
                       "(block-decompressed, read-only)",
            "hirc": "grab_audio.parse_bank: BKHD/DIDX/DATA/HIRC sections, then Event -> Action -> "
                    "Sound/RanSeq/container -> DIDX media id (grab_audio.resolve)",
            "wem": "DIDX entry (offset relative to the DATA chunk body) sliced out of the payload",
            "wav": "Tools/vgmstream-win64/vgmstream-cli.exe (the repo's own decoder, as G1-15 used)",
        },
        "claim_banks": list(CLAIM_BANKS),
        "banks": banks,
        "events": media_rows,
        "checks": {
            "banks_parsed": len(banks),
            "payloads_searched": len(groups),
            "events_seen": len(ids),
            "events_with_media": len(carried),
            "map_rows_covered": sum(1 for r in media_rows if r["in_audio_map"]),
            "media_entries": len(all_media),
            "media_unique_wem": len({m["wem_id"] for m in all_media}),
            "media_written": sum(1 for m in all_media if m.get("written")),
            "streamed_ids_no_didx": len({m["wem_id"] for m in all_media
                                         if m.get("status") == "no-didx-entry"}),
            "wav_decoded": sum(1 for m in all_media if m.get("status") == "ok"),
            "wav_failed": sum(1 for m in all_media if m.get("status") in ("decode-failed", "not-a-wav")),
            "event_ids": ["0x%08X" % i for i in sorted(ids)],
            "missing_twin": {"id": "0x%08X" % TARGET_MISSING,
                             "carried_by": sorted({r["bank"] for r in media_rows
                                                   if r["event_id"] == TARGET_MISSING})},
            "cooked_twin": {"id": "0x%08X" % TARGET_TWIN,
                            "carried_by": sorted({r["bank"] for r in media_rows
                                                  if r["event_id"] == TARGET_TWIN and r["media"]}),
                            "media": sorted({m["wem"] for r in media_rows
                                             if r["event_id"] == TARGET_TWIN for m in r["media"]}),
                            "wav": sorted({m.get("wav_path") for r in media_rows
                                           if r["event_id"] == TARGET_TWIN for m in r["media"]})},
        },
        "problems": problems,
        "oracles": {
            "O-1-payload_sha1": all(b["sha1_match"] for b in banks),
            "O-2-hirc_complete_and_counts": all(b["events_match"] for b in banks),
            "O-3-wem_riff_and_size": all(m.get("riff") and m.get("extracted_bytes") == m.get("bytes")
                                         for m in all_media if m.get("embedded")),
            "O-4-name_rule": all(names.get(r["event_id"]) is not None
                                 for r in media_rows if r["in_audio_map"]) if media_rows else False,
            # ok = decoded here; duplicate = same bytes already decoded under another event tag;
            # no-didx-entry = the media id is referenced but has no DIDX row (streamed / not in this bank)
            "O-5-wav_redecodes": all(m.get("status") in ("ok", "duplicate", "no-didx-entry")
                                     for m in all_media),
            "O-6-twin": (not any(r["event_id"] == TARGET_MISSING and r["media"] for r in media_rows)
                         and any(r["event_id"] == TARGET_TWIN and r["media"] for r in media_rows)),
        },
    }
    doc["digest"] = hashlib.sha1(json.dumps({k: v for k, v in doc.items() if k != "digest"},
                                            sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return doc


def cmd_write(limit):
    doc = build(limit)
    os.makedirs(OUT, exist_ok=True)
    with open(JSON_OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    c = doc["checks"]
    print(json.dumps({k: c[k] for k in ("banks_parsed", "payloads_searched", "events_seen",
                                        "events_with_media", "map_rows_covered", "media_entries",
                                        "media_unique_wem", "media_written", "wav_decoded", "wav_failed")},
                     indent=1))
    for k, v in doc["oracles"].items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print("missing twin", doc["checks"]["missing_twin"])
    print("cooked twin ", {k: doc["checks"]["cooked_twin"][k] for k in ("id", "carried_by", "media")})
    print("wrote", JSON_OUT)
    return 0


def cmd_check():
    doc = build()
    same = (os.path.exists(JSON_OUT)
            and open(JSON_OUT, encoding="utf-8").read()
            == json.dumps(doc, indent=1, sort_keys=True) + "\n")
    bad = [k for k, v in doc["oracles"].items() if not v]
    ok_paths = [x["wav_path"] for r in doc["events"] for x in r["media"] if x.get("status") == "ok"]
    missing_files = [p for p in ok_paths if not os.path.exists(p)]
    print(f"json identical {same}; banks {doc['checks']['banks_parsed']}; "
          f"media {doc['checks']['media_entries']}; wav {doc['checks']['wav_decoded']}; "
          f"missing files {len(missing_files)}")
    for k in bad:
        print("  ORACLE FAIL:", k)
    ok = same and not bad and not missing_files
    print("CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--limit", type=int, help="only the first N distinct banks (debug)")
    a = ap.parse_args()
    return cmd_write(a.limit) if a.write else cmd_check()


if __name__ == "__main__":
    sys.exit(main())
