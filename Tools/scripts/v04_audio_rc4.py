#!/usr/bin/env python3
"""v04_audio_rc4.py - V-04 audio gates, measured on `Builds/bm-RC4` itself.

Templates, used verbatim:

  * `v04_audio_004c.py` (the per-sample gate harness): `v04_audio.decode` for the built bank and for
    the vanilla bank at the same slot, `v04_audio.seam(built["pcm"])` for the wrap step the gate
    uses, `v04_audio.seam(built["pcm"][shift:])` for the same step with the record's codec header
    decoded as audio, and `v04_audio.p99(v04_audio.steps(pcm))` for the payload's own step scale.
    =-1 frame against `src_frames + padded_frames - trimmed_frames`, +-1 LU against the vanilla
    event, -40 dBFS loop wrap, 10 ms tail-silence rule.
  * `v04_loops.py` (the loop domain): the record's leading bytes are its codec header decoded as
    frames, so the payload-domain number is measured after `shift = hlen // (2 * channels)`.

Why the rows are computed here and not through `b11_rc4_audio.gates_for`: that helper returns
`db(v04_audio.seam(...))` for the record step (seam already returns dBFS, so the number is a log of
a log) and takes the payload step from the raw record bytes rather than from the decode. Both give
numbers that are not comparable to the card's, so V-04's own template is used instead. `b11` is
kept for `events_for` only.

The card's expected result is 5/5 loudness and **2/3** loop, with `vehicles#279` RED. That is what
this produces - a run that reports 3/3 fails here. The exact dBFS magnitudes quoted in the review
(-28.27 record / -39.68 payload for #279, -61.21 for #408) are *bm-004c's* bytes: this script
re-decodes bm-004c and asserts those numbers against its own `verify/audio_004c.json`, then prints
bm-RC4's own, which differ because the RC banks were rebuilt from the manifest.

Environment: the temp tree is ~610 MB and C: is full, so TMPDIR/TEMP/TMP and `tempfile.tempdir`
point at `tmp/tmpdir` on E: before anything decodes.

Usage
    python Tools/scripts/v04_audio_rc4.py --write   # measure + write the report pair
    python Tools/scripts/v04_audio_rc4.py --check   # re-derive, compare, assert the 2/3 result
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

TMP = os.path.join(ROOT, "tmp", "tmpdir")
os.makedirs(TMP, exist_ok=True)
for _k in ("TMPDIR", "TEMP", "TMP"):
    os.environ[_k] = TMP
tempfile.tempdir = TMP                     # C: is full; the decode WAVs must land on E:

import bm_audio                            # noqa: E402  (fsb_of / VGMPATH)
import bmak_audio_features as g15          # noqa: E402  (BS.1770-4, the card's loudness)
import v04_audio                           # noqa: E402  (the template: decode / seam / steps / p99)
import b11_rc4_audio as B11                # noqa: E402  (events_for only)

RC = os.path.join(ROOT, "Builds", "bm-RC4")
BANKS = os.path.join(RC, "drop", "sound", "fmod_banks")
RECEIPT = os.path.join(RC, "receipt.json")
MANIFEST = B11.MANIFEST                    # Working/Audio/bm_bank_manifest_rc4.json
HIST = os.path.join(ROOT, "Builds", "bm-004c")   # the tree the quoted dBFS were measured on
HIST_BANKS = os.path.join(HIST, "banks")
HIST_JSON = os.path.join(HIST, "verify", "audio_004c.json")
REPORTS = os.path.join(ROOT, "tmp", "freebuff", "reports")
OUT_MD = os.path.join(REPORTS, "verify-v04-audio-rc4.md")
OUT_JSON = os.path.join(REPORTS, "verify-v04-audio-rc4.json")
CLICK_DBFS = v04_audio.CLICK_DBFS
LU_TOL = v04_audio.LU_TOL
TAIL_SILENCE_S = v04_audio.TAIL_SILENCE_S
SCHEMA = 1
QUOTED = {"vehicles#279": {"record": -28.27, "payload": -39.68, "p99": -46.01},
          "weapons#408": {"record": -61.21, "payload": -50.75, "p99": -11.54}}


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def sha_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wrap(path: str, idx: int, channels: int, frames: int) -> dict:
    """The loop numbers exactly as `v04_audio_004c.py` computes them, plus the decode's sha.

    `built` is the vgmstream decode of the record; its leading bytes are the codec header decoded
    as audio, so the payload-domain step is the same array with `shift` frames dropped.
    """
    built = v04_audio.decode(path, idx)
    rec = bytes(bm_audio.fsb_of(open(path, "rb").read())[1].samples[idx - 1].data)
    hlen = max(0, len(rec) - int(frames) * int(channels) * 2)
    shift = hlen // (2 * int(channels))
    return {"record_dbfs": v04_audio.seam(built["pcm"]),
            "payload_dbfs": v04_audio.seam(built["pcm"][shift:]),
            "shift": shift, "p99_dbfs": v04_audio.p99(v04_audio.steps(built["pcm"])),
            "decoded_sha256": built["sha256"]}


def measure() -> dict:
    """Every number this report states, from the RC's bytes and the manifest's own slots."""
    receipt = json.load(open(RECEIPT, encoding="utf-8"))
    mf = json.load(open(MANIFEST, encoding="utf-8"))
    shipped = {f["path"]: f for f in receipt["files"]}
    want_banks = sorted(p for p in shipped if p.startswith("sound/fmod_banks/")
                        and p.endswith(".bank"))
    on_disk = sorted("sound/fmod_banks/" + n for n in os.listdir(BANKS) if n.endswith(".bank"))
    if on_disk != want_banks:
        raise SystemExit(f"bank set differs from the receipt: disk {on_disk} vs receipt "
                         f"{want_banks}")

    banks = []
    for p in on_disk:
        f = os.path.join(BANKS, os.path.basename(p))
        got = sha_file(f)
        banks.append({"path": p, "bytes": os.path.getsize(f), "sha256": got,
                      "receipt_bytes": shipped[p]["bytes"],
                      "receipt_sha256": shipped[p]["sha256"], "match": got == shipped[p]["sha256"]})

    van_paths = {}
    for bank, key in sorted(mf["bank"].items()):
        p = mf["inputs"]["banks"][bank]
        van_paths[bank] = p if os.path.isabs(p) else os.path.join(ROOT, p)

    rows = []
    for s in mf["slots"]:
        bank, idx = s["bank"], int(s["index"])
        ch = int(s["channels"])
        bp = os.path.join(BANKS, f"{bank}.bank")
        built = v04_audio.decode(bp, idx)
        van = v04_audio.decode(van_paths[bank], idx)
        lufs_b = float(g15.integrated_lufs(built["pcm"], built["rate"]))
        lufs_v = float(g15.integrated_lufs(van["pcm"], van["rate"]))
        delta = round(lufs_b - lufs_v, 2)
        span = (int(s["measured"]["src_frames"]) + int(s["measured"]["padded_frames"])
                - int(s["measured"]["trimmed_frames"]))
        nz = abs(built["pcm"]).max(axis=1) if built["pcm"].ndim > 1 else abs(built["pcm"])
        idx_nz = [i for i, v in enumerate(nz) if v > 1e-4]
        tail_s = round(float(built["frames"] - 1 - (idx_nz[-1] if idx_nz
                                                    else built["frames"] - 1))
                       / float(built["rate"]), 4)
        is_loop = "_loop" in built["name"]
        row = {
            "slot": f"{bank}#{idx}", "bank": bank, "index": idx, "name": built["name"],
            "row": s["row"], "event_guid": s.get("guid"),
            "frames": built["frames"], "frames_span": span,
            "delta_span": built["frames"] - span,
            "lufs_built": round(lufs_b, 2), "lufs_vanilla": round(lufs_v, 2),
            "delta_lu": delta, "loudness_ok": abs(delta) <= LU_TOL,
            "decode_ok": (built["frames"] == int(s["frames"]) and built["rate"] == int(s["rate"])
                          and built["channels"] == ch and built["name"] == s["name"]),
            "built_sha256": built["sha256"], "vanilla_sha256": van["sha256"],
            "tail_silence_s": tail_s, "tail_ok": None,
            "interior_p99_dbfs": v04_audio.p99(v04_audio.steps(built["pcm"])),
            "seam_record_dbfs": None, "seam_payload_dbfs": None,
            "vanilla_seam_dbfs": v04_audio.seam(van["pcm"]),
            "header_shift_frames": None, "loop_ok": None, "verdict": "one-shot",
        }
        if is_loop:
            w = wrap(bp, idx, ch, built["frames"])
            a, p99 = w["record_dbfs"], w["p99_dbfs"]
            row.update({
                "seam_record_dbfs": a, "seam_payload_dbfs": w["payload_dbfs"],
                "header_shift_frames": w["shift"], "interior_p99_dbfs": p99,
                "tail_ok": tail_s <= TAIL_SILENCE_S,
                "loop_ok": not (a > CLICK_DBFS and a > p99),
            })
            row["verdict"] = ("FAIL: click at the only available loop boundary"
                              if not row["loop_ok"] else
                              "pass: below the -40 dBFS threshold" if a <= CLICK_DBFS else
                              "pass: above -40 dBFS but inside the payload's own step distribution")
        rows.append(row)

    B11.OUT_BANKS = BANKS
    ev = B11.events_for(mf)
    loops = [r for r in rows if r["loop_ok"] is not None]
    return {
        "schema": SCHEMA, "card": "V-04", "build": "Builds/bm-RC4",
        "inputs": {
            "banks": rel(BANKS), "receipt": rel(RECEIPT), "receipt_sha256": sha_file(RECEIPT),
            "manifest": rel(MANIFEST), "manifest_sha256": sha_file(MANIFEST),
        },
        "banks": banks,
        "thresholds": {"click_dbfs": CLICK_DBFS, "loudness_lu": LU_TOL,
                       "tail_silence_s": TAIL_SILENCE_S},
        "gates": {
            "decode": all(r["decode_ok"] for r in rows),
            "length": all(abs(r["delta_span"]) <= 1 for r in rows),
            "loudness": all(r["loudness_ok"] for r in rows),
            "loop": all(r["loop_ok"] for r in loops),
            "tail": all(r["tail_ok"] for r in loops),
        },
        "counts": {"slots": len(rows), "loop_samples": len(loops),
                   "loop_pass": sum(1 for r in loops if r["loop_ok"]),
                   "loudness_pass": sum(1 for r in rows if r["loudness_ok"])},
        "rows": rows,
        "events": {k: v for k, v in ev.items() if k != "rows"},
        "event_rows": ev["rows"],
    }


def provenance() -> dict:
    """Re-measure the numbers the review quotes on the tree they were measured on.

    `Builds/bm-004c/verify/audio_004c.json` states -28.27 record / -39.68 payload for
    `vehicles#279` and -61.21 for `weapons#408`. This recomputes both from bm-004c's own bank bytes
    and checks the result against that JSON, so the quoted numbers have an owner.
    """
    hist = json.load(open(HIST_JSON, encoding="utf-8"))
    gates = {(g["bank"], int(g["index"])): g for g in hist["gates"]}
    mf = json.load(open(MANIFEST, encoding="utf-8"))
    slots = {(s["bank"], int(s["index"])): s for s in mf["slots"]}
    out = {}
    for key in (("vehicles", 279), ("weapons", 408)):
        s = slots[key]
        bp = os.path.join(HIST_BANKS, f"{key[0]}.bank")
        w = wrap(bp, key[1], int(s["channels"]), int(s["frames"]))
        g = gates[key]
        out[f"{key[0]}#{key[1]}"] = {
            "tree": rel(HIST_BANKS), "record_dbfs": w["record_dbfs"],
            "payload_dbfs": w["payload_dbfs"], "header_shift_frames": w["shift"],
            "interior_p99_dbfs": w["p99_dbfs"],
            "json_record_dbfs": g["wrap_dbfs"], "json_payload_dbfs": g["wrap_payload_dbfs"],
            "json_p99_dbfs": g["interior_p99_dbfs"],
            "reproduces_json": (w["record_dbfs"] == g["wrap_dbfs"]
                                and w["payload_dbfs"] == g["wrap_payload_dbfs"]
                                and w["p99_dbfs"] == g["interior_p99_dbfs"]),
            "decoded_sha256": w["decoded_sha256"], "json_built_sha256": g["built_sha256"],
            "sha_matches_json": w["decoded_sha256"] == g["built_sha256"],
        }
    return out


def verdict(doc: dict) -> tuple[str, list[str]]:
    g, c = doc["gates"], doc["counts"]
    bad = []
    for k in ("decode", "length", "loudness"):
        if not g[k]:
            bad.append(k)
    if c["loop_pass"] != 2 or c["loop_samples"] != 3:
        bad.append(f"loop {c['loop_pass']}/{c['loop_samples']}")
    if doc["events"]["resolved"] != 24 or doc["events"]["in_fmod_guids"] != 45:
        bad.append(f"events {doc['events']['resolved']}/45 resolved, "
                   f"{doc['events']['in_fmod_guids']}/45 in fmod_guids")
    if any(not b["match"] for b in doc["banks"]):
        bad.append("bank bytes differ from the receipt")
    if not all(p["reproduces_json"] for p in doc["provenance"].values()):
        bad.append("the quoted dBFS do not re-derive from bm-004c")
    return (("PASS: 5/5 loudness, 2/3 loop (vehicles#279 RED), 24/45 events resolved"
             if not bad else "RED: " + ", ".join(bad)), bad)


def render_md(doc: dict) -> str:
    g, c = doc["gates"], doc["counts"]
    loops = [r for r in doc["rows"] if r["loop_ok"] is not None]
    by = {r["slot"]: r for r in loops}
    v279, w408 = by.get("vehicles#279"), by.get("weapons#408")
    v, _bad = verdict(doc)
    L = ["# V-04 audio gates on `Builds/bm-RC4`", "",
         "`python Tools/scripts/v04_audio_rc4.py --write` measures; `--check` re-derives every",
         "number and asserts the result. Offline and read-only: no bank is written, nothing is",
         "installed and no game is launched.", "",
         f"**{v}** - {c['slots']} swapped samples in {len(doc['banks'])} built banks, "
         f"{c['loop_samples']} of them `_loop`.", ""]

    L += ["## The two banks in the tree", "",
          "| bank | bytes | sha256 | receipt match |", "|---|---|---|---|"]
    for b in doc["banks"]:
        L.append(f"| `{b['path']}` | {b['bytes']:,} | `{b['sha256'][:16]}...` | "
                 f"{'PASS' if b['match'] else 'RED'} |")
    L += ["", "`character.bank` and `effects.bank` are **not** in this tree, so the 21 donor GUIDs",
          "below have no carrier here (B-26).", ""]

    L += ["## Gate summary", "", "| gate | result |", "|---|---|"]
    for k in ("decode", "length", "loudness", "loop", "tail"):
        L.append(f"| {k} | {'GREEN' if g[k] else 'RED'} |")
    L += [f"| length | {c['slots']}/{c['slots']} within 1 frame of the source span |",
          f"| loudness | {c['loudness_pass']}/{c['slots']} within 1 LU of the vanilla event |",
          f"| loop wrap | **{c['loop_pass']}/{c['loop_samples']}** below the -40 dBFS rule |", ""]

    L += ["## Per sample, decoded from the built bank", "",
          "| slot | name | frames / span | d frames | LUFS built / vanilla | d LU | loudness |",
          "|---|---|---|---|---|---|---|"]
    for r in doc["rows"]:
        L.append(f"| `{r['slot']}` | `{r['name']}` | {r['frames']} / {r['frames_span']} | "
                 f"{r['delta_span']:+d} | {r['lufs_built']} / {r['lufs_vanilla']} | "
                 f"{r['delta_lu']:+.2f} | {'PASS' if r['loudness_ok'] else 'RED'} |")
    L += ["", "Length is measured against `span = src_frames + padded_frames - trimmed_frames`",
          "(the WAV after B-11's documented trim/tile, V-04/3); against the raw WAV a swap cannot",
          "pass because the slot keeps its frame count.", ""]

    L += ["## Loop wrap, per `_loop` sample", "",
          "| slot | seam, decoded record | seam, payload after the codec header | vanilla seam | "
          "interior p99 | header frames | verdict |", "|---|---|---|---|---|---|---|"]
    for r in loops:
        L.append(f"| `{r['slot']}` | **{r['seam_record_dbfs']} dBFS** | "
                 f"{r['seam_payload_dbfs']} dBFS | {r['vanilla_seam_dbfs']} dBFS | "
                 f"{r['interior_p99_dbfs']} dBFS | {r['header_shift_frames']} | "
                 f"{'PASS' if r['loop_ok'] else 'RED'} |")
    L += ["", "The gate is V-04's: a click is a decoded end->start step above -40 dBFS **and**",
          "above the payload's own p99 interior step. The payload-domain column is the same step",
          "with the record's codec header (decoded as audio by the decoder) dropped.", ""]
    L.append(f"* `weapons#408` - **PASS**: record step {w408['seam_record_dbfs']} dBFS and payload "
             f"step {w408['seam_payload_dbfs']} dBFS, loudness {w408['delta_lu']:+.2f} LU against "
             f"vanilla; its p99 is {w408['interior_p99_dbfs']} dBFS, so the payload-domain step is "
             "inside its own interior distribution." if w408 else "* `weapons#408` absent.")
    L.append(f"* `vehicles#279` - **RED**: record step {v279['seam_record_dbfs']} dBFS is above "
             f"the -40 dBFS rule and above this payload's own p99 ({v279['interior_p99_dbfs']} "
             f"dBFS), so it is an outlier click, not the noise floor; the payload-domain step is "
             f"{v279['seam_payload_dbfs']} dBFS, still above -40." if v279 else
             "* `vehicles#279` absent.")
    L += ["", f"**So the loop gate is {c['loop_pass']}/{c['loop_samples']}, not "
              f"{c['loop_samples']}/{c['loop_samples']}.** A run that reports 3/3 has measured a",
          "different domain, dropped the p99 rule, or gated the wrong tree.", ""]

    L += ["## Where the quoted dBFS come from", "",
          "The review quotes `-28.27` record / `-39.68` payload for `vehicles#279` and `-61.21` for",
          "`weapons#408`. Those are **`Builds/bm-004c`'s bytes**, and this script re-derives them",
          "there:", "",
          "| slot | tree | record | payload | p99 | matches `audio_004c.json` | decoded sha == json |",
          "|---|---|---|---|---|---|---|"]
    for slot, p in doc["provenance"].items():
        L.append(f"| `{slot}` | `{p['tree']}` | {p['record_dbfs']} | {p['payload_dbfs']} | "
                 f"{p['interior_p99_dbfs']} | {'YES' if p['reproduces_json'] else 'NO'} | "
                 f"{'YES' if p['sha_matches_json'] else 'NO'} |")
    L += ["", "`bm-RC4`'s banks were rebuilt from the manifest, so the same measurement on this",
          "tree gives the numbers in the table above (`vehicles#279` record "
          f"{v279['seam_record_dbfs']}, payload {v279['seam_payload_dbfs']}; `weapons#408` record "
          f"{w408['seam_record_dbfs']}, payload {w408['seam_payload_dbfs']}). The verdict is the",
          "same - #279 above the rule and above its p99, #408 fixed - but the magnitudes belong to",
          "the tree they were measured on. The `sha_matches_json` column shows bm-004c is still the",
          "tree those numbers describe.", ""]

    e = doc["events"]
    L += ["## The 45 pinned GUIDs", "",
          f"* `.ee.fmod_guids`: **{e['in_fmod_guids']}/{e['total']}** present (re-emitted).",
          f"* resolved in the built banks: **{e['resolved']}/{e['total']}** "
          f"({', '.join(f'{b} {n}' for b, n in sorted(e['per_bank'].items()))}).",
          f"* donor banks not built: **{e['donor_bank_not_built']}** (effects + character) - "
          "**B-26**, named per GUID in the JSON.", "",
          "| bank | GUIDs | resolved | status |", "|---|---|---|---|"]
    per: dict[str, list[dict]] = {}
    for r in doc["event_rows"]:
        per.setdefault(r["bank"], []).append(r)
    for bank in sorted(per):
        rows = per[bank]
        res = sum(1 for r in rows if r["event_present"] and r["tune_present"])
        status = ("resolved in the built bank" if bank in ("vehicles", "weapons")
                  else "donor bank not built - B-26 (per-entity override)")
        L.append(f"| `{bank}` | {len(rows)} | {res} | {status} |")
    L += ["", "Every resolved GUID has both its FEV event and its tune table row in the built",
          "bank; the 21 donor GUIDs have no event row to resolve because their bank is not in",
          "this tree.", ""]

    L += ["## Not a failure of this build", "",
          "`python Tools/scripts/bm_audio.py --check` targets `Builds/bm-004` and probes the live",
          "install, whose two banks were overwritten by later test installs (2026-11-02 21:48:39);",
          "its derivation diff is 0. It measures a different tree, so it is not evidence against",
          "`Builds/bm-RC4`.", ""]

    L += ["## Limits", "",
          "* **No game run.** These are decoded bytes: whether the engine honours the loop is",
          "  UNKNOWN (test ban).",
          f"* **`vehicles#279` stays RED** on the card's rule: record step "
          f"{v279['seam_record_dbfs']} dBFS against -40 and p99 {v279['interior_p99_dbfs']} dBFS.",
          "  It is recorded, not bent.",
          "* **The exact magnitudes in the review are bm-004c's**, reproduced above; the RC4 tree's",
          "  own numbers differ by 1-5 dB because its banks are rebuilt bytes. Neither number is",
          "  adjusted to match the other.",
          "* **The 21 donor GUIDs' audio** needs B-26's per-entity bank override, whose mechanism",
          "  is not decoded; no substitute is counted as resolved here.",
          "* Loop points of the three `_loop` slots are still not carried in FSB5 LOOP metadata",
          "  (`v04_loops.py`): the whole payload is the loop, as measured.", ""]
    return "\n".join(L)


def oracles(doc: dict) -> list[tuple[str, bool, str]]:
    g, c = doc["gates"], doc["counts"]
    loops = [r for r in doc["rows"] if r["loop_ok"] is not None]
    by = {r["slot"]: r for r in loops}
    v279, w408 = by.get("vehicles#279"), by.get("weapons#408")
    prov = doc["provenance"]
    return [
        ("two banks, byte-identical to the RC receipt",
         len(doc["banks"]) == 2 and all(b["match"] for b in doc["banks"]),
         ", ".join(f"{b['path'].split('/')[-1]} {b['bytes']:,}" for b in doc["banks"])),
        ("no character/effects bank in the tree",
         not any(b["path"].endswith(("character.bank", "effects.bank")) for b in doc["banks"]), ""),
        (f"length: {c['slots']}/{c['slots']} within 1 frame",
         g["length"] and all(abs(r["delta_span"]) <= 1 for r in doc["rows"]), ""),
        (f"loudness: {c['loudness_pass']}/{c['slots']} within 1 LU",
         g["loudness"] and c["loudness_pass"] == c["slots"], ""),
        ("loop: 2/3, not 3/3",
         len(loops) == 3 and c["loop_pass"] == 2
         and [r["slot"] for r in loops if not r["loop_ok"]] == ["vehicles#279"], ""),
        ("vehicles#279 RED: above -40 dBFS and above its own p99",
         v279 is not None and v279["seam_record_dbfs"] > CLICK_DBFS
         and v279["seam_record_dbfs"] > v279["interior_p99_dbfs"],
         f"{v279['seam_record_dbfs']} record / {v279['seam_payload_dbfs']} payload vs -40, "
         f"p99 {v279['interior_p99_dbfs']}" if v279 else ""),
        ("weapons#408 PASS: loudness +0.00 LU and a quiet wrap",
         w408 is not None and abs(w408["delta_lu"]) <= 0.01 and w408["loop_ok"],
         f"{w408['delta_lu']:+.2f} LU, record {w408['seam_record_dbfs']}" if w408 else ""),
        ("the quoted dBFS re-derive from bm-004c bytes",
         all(p["reproduces_json"] and p["sha_matches_json"] for p in prov.values()),
         "; ".join(f"{s}: {p['record_dbfs']}/{p['payload_dbfs']} vs json "
                   f"{p['json_record_dbfs']}/{p['json_payload_dbfs']}" for s, p in prov.items())),
        ("events: 45 pinned, 45/45 in fmod_guids",
         doc["events"]["total"] == 45 and doc["events"]["in_fmod_guids"] == 45, ""),
        ("events: 24/45 resolved, 21 donor (B-26)",
         doc["events"]["resolved"] == 24 and doc["events"]["donor_bank_not_built"] == 21,
         f"{doc['events']['resolved']}/{doc['events']['total']}"),
    ]


def print_samples(doc: dict) -> None:
    for r in doc["rows"]:
        loop = ("-" if r["loop_ok"] is None else ("PASS" if r["loop_ok"] else "RED"))
        print(f"  {r['slot']:>12} {r['name'][:34]:34s} frames {r['frames']}/{r['frames_span']} "
              f"({r['delta_span']:+d}) | LUFS {r['lufs_built']}/{r['lufs_vanilla']} "
              f"({r['delta_lu']:+.2f}) | seam record {r['seam_record_dbfs']} / payload "
              f"{r['seam_payload_dbfs']} / p99 {r['interior_p99_dbfs']} | loop {loop}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = measure()
    doc["provenance"] = provenance()
    text = render_md(doc)
    checks = oracles(doc)
    failed = [c for c in checks if not c[1]]
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f" [{detail}]" if detail else ""))
    if a.write:
        os.makedirs(REPORTS, exist_ok=True)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
            f.write("\n")
        print(f"wrote {rel(OUT_MD)} and {rel(OUT_JSON)}")
    else:
        if not os.path.exists(OUT_MD) or not os.path.exists(OUT_JSON):
            print("FAIL: the report pair is missing (run --write)")
            return 1
        if open(OUT_MD, encoding="utf-8", newline="").read().replace("\r\n", "\n") != text:
            print("FAIL: the report differs from the re-derived text")
            return 1
        if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(json.dumps(doc)):
            print("FAIL: the JSON differs from the re-derived numbers")
            return 1
        print("PASS: report pair matches the re-derived numbers")
    print_samples(doc)
    c, d = doc["counts"], doc["events"]
    print(f"{'RED' if failed else 'PASS'}: {c['slots']} samples, {c['loudness_pass']}/"
          f"{c['slots']} loudness, {c['loop_pass']}/{c['loop_samples']} loop, "
          f"events {d['resolved']}/{d['total']} resolved, {d['in_fmod_guids']}/{d['total']} "
          f"in fmod_guids")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
