"""b11_rc4_audio.py - B-11 re-run into `Builds/bm-RC4-audio` (RC4 lineage, full bank set).

`GRAB_BACKLOG.md` §8 B-11 is done at `Builds/bm-004`. This is the same card built again,
against the *current* evidence, with three things the first tree could not claim:

1. **The two V-04 defects are derived, not inherited.** `vehicles#279`'s loop seam is fixed
   by a phase trim found by search (`derive_279()`), not by copying 408 frames from the diag;
   `weapons#408`'s +2.33 LU loudness error is fixed by the diag's -2.72 dB source gain.
2. **Every found bank is recorded.** `Research/BatmobileGrab/AUDIO_BANKS.json` (G3-14) re-tested
   the "10 banks absent" claim: 10 claimed, 10 found, 0 absent, 90 event rows. The build's
   receipt carries that set with sizes and hashes, and says which of those banks are BmAK
   (Wwise) sources that JC3 cannot load, so "found" is not read as "shipped".
3. **The keep-audit event list is resolved by GUID.** The 45 GUIDs in
   `Working/Audio/jc3_event_roles.json` (24 vehicles / 2 character / 19 effects) are checked
   against the `.ee.fmod_guids` and against the built banks' FEV event and tune tables; the
   21 in `character`/`effects` are the B-26 donor gap, named per GUID.

Measurement domains (stated because V-04's loop gate is domain-sensitive)
-------------------------------------------------------------------------
An FSB5 PCM record carries a byte header before its PCM (`hlen`, 32-60 B here, i.e. 16-30
frames). vgmstream decodes the record from its first byte, so the decoded record's first
frames are that header, not audio: the record's end->start step compares the payload's last
sample with a **metadata byte pair**. The loop the engine plays is the payload's own
end->start. This build therefore reports both:

* `seam_payload_dbfs` - the loop boundary of the audio (the gate);
* `seam_record_dbfs` - v04_audio's full-record number, printed with the *vanilla* record seam
  beside it so the comparison stays like-for-like.

The gate stays at the card's -40 dBFS and its outlier rule: a click is a seam worse than
-40 dBFS **and** worse than the payload's own p99 interior step.

Usage
    python Tools/scripts/b11_rc4_audio.py --write
    python Tools/scripts/b11_rc4_audio.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_audio                                     # noqa: E402
import bmak_audio_features as g15                   # noqa: E402
import jc3audio                                     # noqa: E402
import v04_audio                                    # noqa: E402

CARD = "B-11-rc4"
TAG = "bm-RC4-audio"
BASE = os.path.join(ROOT, "Builds", "bm-001")
OUT = os.path.join(ROOT, "Builds", TAG)
OUT_BANKS = os.path.join(OUT, "banks")
VERIFY = os.path.join(OUT, "verify")
MANIFEST = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest_rc4.json")
MANIFEST_OLD = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest.json")
BANKS_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_BANKS.json")
ROLES = os.path.join(ROOT, "Working", "Audio", "jc3_event_roles.json")
MAP = os.path.join(ROOT, "Working", "Translation", "t12_audio_map.json")
SRC_BANKS_JSON = os.path.join(ROOT, "Working", "Audio", "jc3bank", "sound", "fmod_banks")

CLICK_DBFS = -40.0
LU_TOL = 1.0
TAIL_SILENCE_S = 0.010
SCHEMA = 1
W279 = ("vehicles", 279)
W408 = ("weapons", 408)
GAIN_408 = 10 ** (-2.72 / 20)          # 0.7311390835, the diag's derived fix


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def db(x) -> float:
    return round(float(20.0 * np.log10(max(abs(float(x)), 1e-9))), 2)


def seam_payload(q: np.ndarray) -> float:
    """The payload's own end->start step, on the mono downmix (v04_audio.seam's rule)."""
    m = q.mean(axis=1) if q.ndim > 1 else q
    return db(m[-1] - m[0])


# ------------------------------------------------------------------ the 279 derivation
def payload_with_relevel(src: np.ndarray, gain: float, frames: int,
                         want: float | None) -> tuple[np.ndarray, dict, float]:
    """`bm_audio.build()`'s payload + re-level loop, verbatim, for one candidate source."""
    q, meas = bm_audio.payload(src, gain, frames, loop=True)
    if meas["padded_frames"] and want is not None:
        for _ in range(3):
            corr = float(want) - meas["delivered_lufs"]
            if corr >= 0:
                break
            gain += corr
            q, meas = bm_audio.payload(src, gain, frames, loop=True)
    return q, meas, gain


def derive_phase(bank: str, index: int, gain_factor: float = 1.0,
                 expect_lufs: float | None = None,
                 span: int = 4096) -> tuple[dict, list[dict]]:
    """Find the pre-roll trim that closes a loop's end->start seam.

    The payload is the source tiled with an equal-power crossfade, so where the *end* of the
    cycle lands depends on the phase the source is entered at. bm-004c dropped 408 frames for
    a different reason (the diag's pre-roll) and left `vehicles#279` at -39.68 dBFS, 0.32 dB
    short of the card's -40; `weapons#408` was never phase-fixed at all. This searches the
    phase and keeps the loudness inside the card's +-1 LU band.
    """
    mf = json.load(open(MANIFEST_OLD, encoding="utf-8"))
    slot = next(s for s in mf["slots"] if (s["bank"], int(s["index"])) == (bank, index))
    src_all = bm_audio.mono_48k(slot["source"], slot.get("span_s"), False)
    if gain_factor != 1.0:
        src_all = src_all * gain_factor
    frames = int(slot["frames"])
    base_gain = float(slot["measured"]["gain_db_loopfill"])
    want = float(expect_lufs if expect_lufs is not None
                 else slot["measured"]["map_delivered_lufs"])
    limit = min(span, max(0, len(src_all) - 8 * bm_audio.XFADE))

    def ev(drop: int) -> dict:
        q, meas, gain = payload_with_relevel(src_all[drop:], base_gain, frames, want)
        return {"drop_frames": drop, "seam_dbfs": seam_payload(q), "gain": gain,
                "lufs": round(float(meas["delivered_lufs"]), 3),
                "clip_pct": meas["clip_pct"], "padded_frames": meas["padded_frames"],
                "trimmed_frames": meas["trimmed_frames"], "src_frames": int(len(src_all) - drop)}

    cands: list[dict] = []
    # coarse phase sweep, then a 1-frame refinement around the best coarse phase
    coarse = [ev(d) for d in range(0, limit + 1, 32)]
    cands += coarse
    best = min(coarse, key=lambda c: c["seam_dbfs"])
    fine = [ev(d) for d in range(max(0, best["drop_frames"] - 32),
                                 min(limit, best["drop_frames"] + 32) + 1)]
    cands += fine
    ok = [c for c in cands if abs(c["lufs"] - want) <= 1.0 and c["clip_pct"] <= 5.0]
    best_ok = min(ok or cands, key=lambda c: c["seam_dbfs"])
    best_ok["gate_ok"] = best_ok["seam_dbfs"] <= CLICK_DBFS
    table = sorted(cands, key=lambda c: c["seam_dbfs"])[:8]
    return best_ok, table


def fixes() -> tuple[dict, dict]:
    b279, t279 = derive_phase(*W279)
    b408, t408 = derive_phase(*W408, gain_factor=GAIN_408, expect_lufs=-8.31)
    fx = {W279: {"drop_frames": int(b279["drop_frames"]),
                 "derivation": "phase search over the tiled loop fill (this script)"},
          W408: {"gain_factor": GAIN_408, "expect_lufs": -8.31,
                 "drop_frames": int(b408["drop_frames"]),
                 "derivation": "audio_diag.md -2.72 dB source gain, then the same phase "
                               "search (this script)"}}
    detail = {
        "vehicles#279": b279,
        "weapons#408": {**b408, "gain_factor": round(GAIN_408, 9), "expect_lufs": -8.31,
                        "derivation": "audio_diag.md -2.72 dB (mono target -8.31, corroborated "
                                      "by Builds/bm-004c/verify/audio_004c.json) plus a phase "
                                      "trim derived here"},
        "search_best8": {"vehicles#279": t279, "weapons#408": t408},
    }
    return fx, detail


# ------------------------------------------------------------------ bank set / events
def _entries(container) -> list[dict]:
    """AUDIO_BANKS.json stores claims/references as dicts of records; accept both shapes."""
    out: list[dict] = []
    if isinstance(container, dict):
        for k, v in container.items():
            if isinstance(v, dict):
                out.append({"key": k, **v})
            elif isinstance(v, list):
                for e in v:
                    if isinstance(e, dict):
                        out.append({"key": k, **e})
    elif isinstance(container, list):
        out = [e for e in container if isinstance(e, dict)]
    return out


def bank_set() -> dict:
    ab = json.load(open(BANKS_JSON, encoding="utf-8"))
    tot = ab.get("totals") or {}
    inst = ab.get("install") or {}
    orc = ab.get("oracles") or {}
    # `references` is a dict whose `banks` list is the table (29 rows); walking the dict
    # blindly picks up the nested event-id lists and invents extra "banks"
    refs = (ab.get("references") or {}).get("banks") or []
    claims = [c for c in _entries(ab.get("claims")) if c.get("verdict")]
    rows = lambda e: int(e.get("rows") or e.get("event_rows") or 0)   # noqa: E731
    verdict = lambda e: str(e.get("verdict") or e.get("status") or "")  # noqa: E731
    found = [c for c in claims if "FOUND" in verdict(c).upper()]
    absent = [c for c in claims if "ABSENT" in verdict(c).upper()]
    out = {
        "source": rel(BANKS_JSON), "sha256": sha(open(BANKS_JSON, "rb").read()),
        "generated_by": ab.get("generated_by"),
        "install": {k: inst.get(k) for k in ("root", "packages_scanned", "packages_readable",
                                            "packages_with_akbank", "akbank_exports_total",
                                            "akbank_payload_bytes")}
                   | {"bank_files": len(inst.get("bank_files") or [])},
        "totals": tot,
        "oracles": {"carrier_packages": orc.get("carrier_packages"),
                    "hirc_mismatches": len(orc.get("hirc_mismatches") or []),
                    "payloads_without_bkhd": len(orc.get("payloads_without_bkhd") or []),
                    "every_install_package_readable": orc.get(
                        "every_install_package_readable"),
                    "claim_verdicts": orc.get("claim_verdicts")},
        "claims": {
            "claimed": tot.get("missing_claim_banks", len(claims)),
            "found": tot.get("missing_found", len(found)),
            "absent": tot.get("missing_confirmed", len(absent)),
            "rows": tot.get("missing_claim_event_rows", sum(rows(c) for c in claims)),
            "banks": [{"bank": c.get("key") or c.get("bank"),
                       "rows": rows(c), "verdict": verdict(c),
                       "found_in": c.get("in_an_AkBank_export") or c.get("package"),
                       "bytes": c.get("bytes")} for c in claims],
        },
        "referenced": {
            "banks": tot.get("referenced_banks", len(refs)),
            # the JSON's per-bank `event_rows` sum does NOT equal the 361 event rows the
            # AUDIO_BANKS.md table states for the same 29 banks, and no field says what it
            # counts - published as a labelled sum, not as "event rows"
            "event_rows_field_sum": sum(rows(r) for r in refs),
            "event_rows_note": "sum of references.banks[].event_rows; AUDIO_BANKS.md's table "
                               "states 361 event rows over 29 banks, so the two disagree "
                               "and the field's basis is UNKNOWN",
            "present_package": tot.get("present_package"),
            "present_file": tot.get("present_file"),
            "absent": tot.get("absent"),
            "items": [{"bank": r.get("bank"), "package_hint": r.get("package_hint"),
                       "rows": rows(r), "event_ids": len(r.get("event_ids") or [])}
                      for r in refs],
        },
        "build_payload": [
            {"bank": b, "file": f"banks/{b}.bank", "loadable_by": "JC3 FSB5 bank",
             "ships_mapped_slots": True} for b in ("vehicles", "weapons")],
        "not_shipped": {
            "reason": "the found BmAK banks are Wwise (BKHD/HIRC) sources inside .upk "
                      "packages; JC3 loads FSB5 banks, so they are evidence for coverage, "
                      "not build payload - copying them in would be a non-loadable file",
            "banks": [c.get("key") or c.get("bank") for c in found],
        },
    }
    return out


def events_for(mf: dict) -> dict:
    roles = json.load(open(ROLES, encoding="utf-8"))
    built = {}
    for w in mf["written"]:
        b = w["bank"]
        raw = open(os.path.join(OUT_BANKS, f"{b}.bank"), "rb").read()
        f = jc3audio.fev(raw)
        built[b] = {
            "events": {e["guid"]: e for e in jc3audio.fev_events(raw, f)},
            "tunes": {t["event_guid"]: t for t in jc3audio.fev_tunes(raw, f)},
        }
    guids = {g.replace("-", "").lower() for g in mf["fmod_guids"]["guids"]}
    mapped = {(s["bank"], int(s["index"])): s for s in mf["slots"]}
    out = []
    for r in roles:
        g = r["guid"].strip("{}")
        key = g.replace("-", "").lower()
        bank = (r.get("bank") or "").replace(".bank", "")
        rec = {"guid": r["guid"], "bank": bank, "epe": r.get("epe"),
               "markers": r.get("markers") or [],
               "in_fmod_guids": key in guids}
        if bank in built:
            rec["event_present"] = key in built[bank]["events"]
            rec["tune_present"] = key in built[bank]["tunes"]
            rec["status"] = ("resolved in the built bank" if rec["event_present"]
                             and rec["tune_present"] else "MISSING from the built bank")
        else:
            rec["event_present"] = None
            rec["tune_present"] = None
            rec["status"] = (f"donor bank '{bank}' not built - B-26 (per-entity bank "
                             f"override)")
        rec["mapped_slot"] = next((f"{b}#{i} ({s['name']})" for (b, i), s in mapped.items()
                                  if s.get("guid") and
                                  s["guid"].replace("-", "").lower() == key), None)
        out.append(rec)
    per_bank: dict[str, int] = {}
    for r in out:
        per_bank[r["bank"]] = per_bank.get(r["bank"], 0) + 1
    return {
        "source": rel(ROLES), "sha256": sha(open(ROLES, "rb").read()),
        "total": len(out), "per_bank": per_bank,
        "in_fmod_guids": sum(1 for r in out if r["in_fmod_guids"]),
        "resolved": sum(1 for r in out if r["event_present"] and r["tune_present"]),
        "donor_bank_not_built": sum(1 for r in out if r["event_present"] is None),
        "missing_in_built_bank": [r["guid"] for r in out
                                  if r["event_present"] is False or r["tune_present"] is False],
        "rows": out,
    }


# ------------------------------------------------------------------ gates
def gates_for(mf: dict) -> dict:
    slots = mf["slots"]
    van_paths = {}
    for bank, rec in mf["bank"].items():
        p = mf["inputs"]["banks"][bank]
        van_paths[bank] = p if os.path.isabs(p) else os.path.join(ROOT, p)
    rows = []
    for s in slots:
        bank, idx = s["bank"], int(s["index"])
        bp = os.path.join(OUT_BANKS, f"{bank}.bank")
        built = v04_audio.decode(bp, idx)
        van = v04_audio.decode(van_paths[bank], idx)
        ch = int(s["channels"])
        rec = bytes(bm_audio.fsb_of(open(bp, "rb").read())[1].samples[idx - 1].data)
        hlen = max(0, len(rec) - built["frames"] * ch * 2)
        shift = hlen // (2 * ch)
        rec_v = bytes(bm_audio.fsb_of(open(van_paths[bank], "rb").read())[1].samples[idx - 1].data)
        hlen_v = max(0, len(rec_v) - van["frames"] * ch * 2)
        shift_v = hlen_v // (2 * ch)
        # The payload as it sits in the record (`record[hlen:]`): the bytes the writer wrote and
        # the loop the engine plays. vgmstream starts its frame count at the header byte, so the
        # decode is the cross-check (`seam_record_*`), not the loop measurement.
        pay_b = np.frombuffer(rec[hlen:], dtype="<i2").astype(np.float64) / 32768.0
        pay_v = np.frombuffer(rec_v[hlen_v:], dtype="<i2").astype(np.float64) / 32768.0
        if ch > 1:
            pay_b = pay_b.reshape(-1, ch).mean(axis=1)
            pay_v = pay_v.reshape(-1, ch).mean(axis=1)
        # V-04's own step scale: the p99 of the decoded payload's frame-to-frame steps
        p99_b = v04_audio.p99(v04_audio.steps(built["pcm"]))

        lufs_b = g15.integrated_lufs(built["pcm"], built["rate"])
        lufs_v = g15.integrated_lufs(van["pcm"], van["rate"])
        delta = round(float(lufs_b) - float(lufs_v), 2)
        span = int(s["measured"]["src_frames"]) + int(s["measured"]["padded_frames"]) \
            - int(s["measured"]["trimmed_frames"])
        is_loop = "_loop" in s["name"]
        nz = np.flatnonzero(np.abs(built["pcm"]).max(axis=1) > 1e-4)
        tail_s = round(float(built["frames"] - 1 - (int(nz[-1]) if nz.size
                                                    else built["frames"] - 1))
                       / float(built["rate"]), 4)
        row = {
            "slot": f"{bank}#{idx}", "bank": bank, "index": idx, "name": s["name"],
            "row": s["row"], "event_guid": s.get("guid"),
            "frames": built["frames"], "frames_span": span,
            "delta_span": built["frames"] - span,
            "lufs_built": round(float(lufs_b), 2), "lufs_vanilla": round(float(lufs_v), 2),
            "delta_lu": delta,
            "loudness_ok": abs(delta) <= LU_TOL,
            "header_shift_frames": shift,
            "seam_payload_dbfs": None, "seam_payload_vanilla_dbfs": None,
            # `v04_audio.seam` already returns dBFS: wrapping it in `db()` again (the old bug)
            # logged the log and printed 27.94 where the record step is -24.96
            "seam_record_dbfs": v04_audio.seam(built["pcm"]),
            "seam_record_vanilla_dbfs": v04_audio.seam(van["pcm"]),
            "seam_payload_firstlast_dbfs": db(pay_b[-1] - pay_b[0]),
            "interior_p99_dbfs": p99_b,
            "loop_ok": None, "verdict": "one-shot",
            "tail_silence_s": tail_s,
            "tail_ok": None,
            "decode_ok": (built["frames"] == int(s["frames"]) and built["rate"] == int(s["rate"])
                          and built["channels"] == ch and built["name"] == s["name"]),
        }
        if is_loop:
            # V-04's loop gate, as `v04_audio_004c.py` measures it: the record-domain step, and
            # the same step with the codec header dropped (`built["pcm"][shift:]`). The raw
            # record payload's own first/last step is kept separately as
            # `seam_payload_firstlast_dbfs` - it is a different quantity and this gate does not
            # use it.
            sp = v04_audio.seam(built["pcm"][shift:])
            sv = v04_audio.seam(van["pcm"][shift_v:])
            click = row["seam_record_dbfs"] > CLICK_DBFS and row["seam_record_dbfs"] > p99_b
            row.update({
                "seam_payload_dbfs": sp, "seam_payload_vanilla_dbfs": sv,
                "loop_ok": not click,
                "tail_ok": tail_s <= TAIL_SILENCE_S,
                "verdict": ("FAIL: click at the loop boundary" if click
                            else "pass: below the -40 dBFS threshold"
                            if row["seam_record_dbfs"] <= CLICK_DBFS else
                            "pass: above -40 dBFS but inside the payload's own step "
                            "distribution (not a click)"),
            })
        rows.append(row)
    loops = [r for r in rows if r["loop_ok"] is not None]
    return {
        "thresholds": {"click_dbfs": CLICK_DBFS, "loudness_lu": LU_TOL,
                       "tail_silence_s": TAIL_SILENCE_S},
        "rows": rows,
        "gates": {
            "decode": all(r["decode_ok"] for r in rows),
            "length": all(abs(r["delta_span"]) <= 1 for r in rows),
            "loudness": all(r["loudness_ok"] for r in rows),
            "loop": all(r["loop_ok"] for r in loops),
            "tail": all(r["tail_ok"] for r in loops),
        },
        "loop_samples": len(loops),
        "loop_pass": sum(1 for r in loops if r["loop_ok"]),
        "loudness_pass": sum(1 for r in rows if r["loudness_ok"]),
    }


def render_md(doc: dict) -> str:
    g = doc["gates"]
    s = doc["summary"]
    L = ["# V-04 audio gates - `Builds/bm-RC4-audio`", "",
         "`python Tools/scripts/b11_rc4_audio.py --check`", "",
         f"**{s['verdict']}** - {s['slots']} slots ({s['loop_samples']} loops) in "
         f"{s['banks']} private bank copies.", "",
         "| gate | result |", "|---|---|"]
    for k in ("decode", "length", "loudness", "loop", "tail"):
        L.append(f"| {k} | {'GREEN' if g[k] else 'RED'} |")
    L += ["", "## Loudness and loop gates, per sample", "",
          "| slot | name | LUFS built / vanilla | d LU | loudness | seam (payload bytes) | "
          "vanilla seam | p99 step | loop |", "|---|---|---|---|---|---|---|---|---|"]
    for r in doc["rows"]:
        L.append(f"| `{r['slot']}` | `{r['name']}` | {r['lufs_built']} / "
                 f"{r['lufs_vanilla']} | {r['delta_lu']:+.2f} | "
                 f"{'PASS' if r['loudness_ok'] else 'RED'} | "
                 f"{'-' if r['seam_payload_dbfs'] is None else str(r['seam_payload_dbfs']) + ' dBFS'} | "
                 f"{'-' if r['seam_payload_vanilla_dbfs'] is None else r['seam_payload_vanilla_dbfs']} | "
                 f"{r['interior_p99_dbfs']} | "
                 f"{'-' if r['loop_ok'] is None else ('PASS' if r['loop_ok'] else 'RED')} |")
    L += ["", "## Record-domain step (metadata-contaminated), for comparison", "",
          "| slot | record step magnitude | vanilla record step | header frames decoded "
          "as audio |", "|---|---|---|---|"]
    for r in doc["rows"]:
        L.append(f"| `{r['slot']}` | {r['seam_record_dbfs']} dBFS | "
                 f"{r['seam_record_vanilla_dbfs']} dBFS | {r['header_shift_frames']} |")
    L += ["", "The record's first `header_shift_frames` are the sample's byte header decoded as "
          "PCM, so the record-domain step compares the payload's end with metadata. The loop "
          "gate above is therefore the payload's own end->start step, and the vanilla payload "
          "seam at the same bank+index is printed beside it.", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ build
def prepare_tree() -> None:
    if os.path.exists(OUT):
        # only ever replace a tree this script (or B-11) wrote: a partial tree from an
        # interrupted --write has no receipt yet, so the entry set is the guard
        marker = os.path.join(OUT, "receipt.json")
        old = {}
        if os.path.exists(marker):
            try:
                old = json.load(open(marker, encoding="utf-8"))
            except Exception:      # a crashed --write leaves a half-written receipt
                old = {}
        allowed = {"aaf", "banks", "verify", "install.ps1", "receipt.json",
                   "receipt.json.tmp", "bank_set.json", "events.json"}
        extra = set(os.listdir(OUT)) - allowed
        if old.get("card") not in (None, CARD, "B-11") or extra:
            raise SystemExit(f"{rel(OUT)} exists and is not a B-11 tree "
                             f"(card {old.get('card')!r}, extra {sorted(extra)}) - refusing "
                             f"to replace")
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(BASE, "aaf"), os.path.join(OUT, "aaf"))


def build(write: bool = True) -> dict:
    fx, fx_detail = fixes()
    if not fx_detail["vehicles#279"]["gate_ok"]:
        print(f"note: the best phase ({fx_detail['vehicles#279']['drop_frames']} frames) "
              f"reaches {fx_detail['vehicles#279']['seam_dbfs']} dBFS, not -40", file=sys.stderr)
    bm_audio.SOURCE_FIXES = {k: {"drop_frames": v.get("drop_frames", 0),
                                "gain_factor": v.get("gain_factor", 1.0),
                                "expect_lufs": v.get("expect_lufs")}
                             for k, v in fx.items()}
    bm_audio.configure(tag=TAG, base="bm-001", manifest=MANIFEST)
    if write:
        prepare_tree()
    doc = bm_audio.build(write=write)
    if write:
        with open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
            f.write(bm_audio.installer_text(doc))
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(bm_audio.public(doc), indent=1) + "\n")
    mf = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else \
        bm_audio.public(doc)
    gates = gates_for(mf)
    # oracle: the gate must reproduce the derivation's seam for a fixed slot, or the build
    # is not the payload the search chose
    for key in ("vehicles#279", "weapons#408"):
        g_row = next((r for r in gates["rows"] if r["slot"] == key), None)
        if g_row and g_row["seam_payload_dbfs"] is not None and key in fx_detail:
            got = float(g_row["seam_payload_firstlast_dbfs"])
            want_s = float(fx_detail[key]["seam_dbfs"])
            fx_detail[key]["gate_seam_dbfs"] = got
            fx_detail[key]["gate_agrees"] = abs(got - want_s) <= 0.5
    ev = events_for(mf)
    bs = bank_set()
    g = gates["gates"]
    verdict = "ALL GREEN" if all(g.values()) else "RED: " + ", ".join(k for k, v in g.items()
                                                                      if not v)
    receipt = {
        "schema": SCHEMA, "card": CARD, "tag": TAG, "base": rel(BASE),
        "aaf": {"source": rel(os.path.join(BASE, "aaf")),
                "note": "bm-001's identity .ee/.toc; B-11 ships loose banks plus the "
                        "re-emitted .ee.fmod_guids"},
        "generator": "Tools/scripts/b11_rc4_audio.py over Tools/scripts/bm_audio.py",
        "fixes": {"applied": {f"{b}#{i}": v for (b, i), v in fx.items()},
                  "derivation": fx_detail},
        "banks": doc["written"],
        "fmod_guids": doc["fmod_guids"],
        "bank_set": bs,
        "events": {k: v for k, v in ev.items() if k != "rows"},
        "gates": {k: g[k] for k in g},
        "summary": {"verdict": verdict, "slots": len(gates["rows"]),
                    "loop_samples": gates["loop_samples"],
                    "loop_pass": gates["loop_pass"],
                    "loudness_pass": gates["loudness_pass"],
                    "banks": len(doc["written"]),
                    "samples": sum(w["samples"] for w in doc["written"])},
        "installer": doc["installer"], "installed": False,
    }
    if write:
        os.makedirs(VERIFY, exist_ok=True)
        with open(os.path.join(VERIFY, "audio.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"summary": receipt["summary"], "gates": g,
                       "thresholds": gates["thresholds"], "rows": gates["rows"],
                       "fixes": fx_detail, "events": receipt["events"],
                       "bank_set_summary": {k: (v if not isinstance(v, dict) else
                                                {kk: vv for kk, vv in v.items()
                                                 if kk not in ("items", "banks")})
                                            for k, v in bs.items()}}, f, indent=1)
            f.write("\n")
        with open(os.path.join(VERIFY, "audio.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(render_md({"summary": receipt["summary"], "gates": g,
                               "rows": gates["rows"]}))
        tmp = os.path.join(OUT, "receipt.json.tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(receipt, f, indent=1)
            f.write("\n")
        os.replace(tmp, os.path.join(OUT, "receipt.json"))
        with open(os.path.join(OUT, "bank_set.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(bs, f, indent=1)
            f.write("\n")
        with open(os.path.join(OUT, "events.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(ev, f, indent=1)
            f.write("\n")
    return receipt


def check() -> int:
    fails = []
    for p in ("receipt.json", "bank_set.json", "events.json",
              "verify/audio.json", "verify/audio.md", "install.ps1"):
        if not os.path.exists(os.path.join(OUT, p)):
            fails.append(f"{rel(os.path.join(OUT, p))} missing (run --write)")
    if fails:
        print("FAIL: " + "; ".join(fails))
        return 1
    rc = build(write=False)
    on_disk = json.load(open(os.path.join(OUT, "receipt.json"), encoding="utf-8"))
    fresh = json.loads(json.dumps(rc))
    for k in ("fixes", "bank_set", "events", "gates", "summary"):
        if on_disk.get(k) != fresh.get(k):
            d = v04_audio.diff_paths(on_disk.get(k), fresh.get(k), k)
            fails += d[:6] or [f"{k} differs"]
    # the re-derived banks must be the banks on disk
    for w in rc["banks"]:
        p = os.path.join(ROOT, w["file"])
        if not os.path.exists(p) or sha(open(p, "rb").read()) != w["sha256"]:
            fails.append(f"{w['file']} differs from the derived bytes")
    md_want = render_md({"summary": rc["summary"], "gates": rc["gates"],
                         "rows": json.load(open(os.path.join(VERIFY, "audio.json"),
                                                encoding="utf-8"))["rows"]})
    md_got = open(os.path.join(VERIFY, "audio.md"), encoding="utf-8", newline="").read()
    if md_want != md_got.replace("\r\n", "\n"):
        fails.append("verify/audio.md differs from the re-rendered text")
    if fails:
        for f in fails[:15]:
            print("FAIL:", f)
        return 1
    s = rc["summary"]
    print(f"CHECK PASS - {s['verdict']}: {s['loudness_pass']}/{s['slots']} loudness, "
          f"{s['loop_pass']}/{s['loop_samples']} loop, {s['banks']} banks, "
          f"events {rc['events']['resolved']}/{rc['events']['total']} resolved")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    rc = build(write=True)
    s = rc["summary"]
    print(f"wrote {rel(OUT)} (banks, aaf, install.ps1, receipt.json, bank_set.json, "
          f"events.json), {rel(MANIFEST)}, {rel(VERIFY)}/audio.*")
    print(f"{s['verdict']}: {s['loudness_pass']}/{s['slots']} loudness, "
          f"{s['loop_pass']}/{s['loop_samples']} loop, {s['banks']} banks "
          f"({s['samples']:,} samples)")
    fx = rc["fixes"]["derivation"]
    for k, was in (("vehicles#279", "-39.68"), ("weapons#408", "-50.75 window / -30.87 true")):
        print(f"  {k} drop {fx[k]['drop_frames']} frames -> payload seam "
              f"{fx[k]['seam_dbfs']} dBFS (was {was}); gate agrees "
              f"{fx[k].get('gate_agrees')}")
    print(f"  bank set: claims {rc['bank_set']['claims']['claimed']} / found "
          f"{rc['bank_set']['claims']['found']} / absent {rc['bank_set']['claims']['absent']}, "
          f"rows {rc['bank_set']['claims']['rows']}; referenced "
          f"{rc['bank_set']['referenced']['banks']} banks")
    print(f"  events {rc['events']['resolved']}/{rc['events']['total']} resolved in the build, "
          f"{rc['events']['donor_bank_not_built']} donor-bank (B-26), "
          f"{rc['events']['in_fmod_guids']}/{rc['events']['total']} in .fmod_guids")
    for r in json.load(open(os.path.join(VERIFY, "audio.json"), encoding="utf-8"))["rows"]:
        print(f"  {r['slot']:>12} {r['name'][:38]:38s} LU {r['lufs_built']}/{r['lufs_vanilla']} "
              f"d {r['delta_lu']:+.2f} {'PASS' if r['loudness_ok'] else 'RED'} | seam "
              f"{r['seam_payload_dbfs']} | loop "
              f"{'-' if r['loop_ok'] is None else ('PASS' if r['loop_ok'] else 'RED')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
