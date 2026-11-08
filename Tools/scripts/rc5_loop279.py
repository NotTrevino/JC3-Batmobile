"""rc5_loop279.py - the RC5 seam fix for the three `_loop` slots, in a copy of the RC4 bank build.

`vehicles#279` (`jc3_veh_lave_chassis_spin_creaks_loop_fast`) is the V-04 loop red: the decoded
end->start step is above the card's -40 dBFS and above the payload's own p99. The source-WAV
options in `tmp/freebuff/reports/loop279-edit-options.md` all fade the *source*; this tool shows
why that cannot reach -40 on the built slot and applies the smallest edit that does.

Why the source fade is not enough
---------------------------------
The built record is `header(hlen B) + payload`, and vgmstream decodes `frames` samples, so the
stream it reports ends at `payload[frames-1-shift]` where `shift = hlen/(2*ch)`. That sample is
compared with the record's first decoded frame - the header's first int16 pair, read as audio.
The source fade moves the payload's last sample, not that sample, so its ceiling on the decoded
step is `|0 - header_first|` (measured here per slot), not -inf. A fade to digital zero still
leaves `vehicles#279` at -33.66 dBFS and `vehicles#151` at -12.60 dBFS.

The edit
--------
The smallest linear ramp that drives **both** measured columns below -40 dBFS:

* `A` - over K frames ending at `anchor = frames-1-shift`, ramp the payload to the record's first
  decoded sample (`header0`), so the decoded seam is ~0;
* `B` - only when the payload's own wrap is above -40, ramp `anchor+1 .. frames-1` from `header0`
  to `payload[0]`, so the audio-domain wrap is ~0 too.

K is searched (2, 4, 8, ... frames) and the first value whose every adjacent step inside the
edited span is also at or below -40 dBFS wins, so the click is removed rather than moved. The
changed span is `K` frames (`+ shift` for `B`), i.e. at most ~1 ms.

Route: `Builds/bm-RC4-audio` is copied to a new `Builds/bm-RC5-audio`; the two records are
spliced in the copy with `bm_audio`'s own rule (the vanilla record's header bytes + the edited
payload, unique-match only). `Builds/bm-004c` and `Builds/bm-RC4` are never written.

    python Tools/scripts/rc5_loop279.py --write
    python Tools/scripts/rc5_loop279.py --check

`--write` also writes `Working/Audio/bm_bank_manifest_rc5.json` and the verify page; `--check`
re-derives both banks from `bm-RC4-audio`'s bytes and compares them with the tree, then re-measures
the three slots with `v04_loops.facts()`.
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

import bm_audio                                     # noqa: E402  fsb_of()
import v04_audio                                    # noqa: E402  decode / seam / steps / p99

SRC = os.path.join(ROOT, "Builds", "bm-RC4-audio")
OUT = os.path.join(ROOT, "Builds", "bm-RC5-audio")
SRC_BANKS = os.path.join(SRC, "banks")
OUT_BANKS = os.path.join(OUT, "banks")
VERIFY = os.path.join(OUT, "verify")
MANIFEST_SRC = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest_rc4.json")
MANIFEST = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest_rc5.json")
CARD = "B-11-rc5-loop"
TAG = "bm-RC5-audio"
CLICK_DBFS = -40.0
STEP_MAX = 10.0 ** (CLICK_DBFS / 20.0)      # -40 dBFS as a linear adjacent step
K_CHOICES = [2, 4, 8, 16, 32, 64, 128, 256, 512]
BANKS = ("vehicles", "weapons")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def db(v) -> float:
    return round(float(20.0 * np.log10(max(abs(float(v)), 1e-9))), 2)


def rms_db(a: np.ndarray) -> float:
    return db(float(np.sqrt(np.mean(np.square(a)))) if len(a) else 0.0)


def slurp(p: str) -> bytes:
    with open(p, "rb") as f:
        return f.read()


def record(raw: bytes, index: int) -> dict:
    """The FSB5 sample record at a 1-based index: header length, shift, payload int16."""
    base = raw.find(b"FSB5")
    if base < 0:
        raise SystemExit("no FSB5 in the bank")
    fsb = bm_audio.fsb_of(raw)[1]
    s = fsb.samples[index - 1]
    data = bytes(s.data)
    ch, frames = int(s.channels), int(s.samples)
    hlen = len(data) - frames * ch * 2
    if hlen < 0:
        raise SystemExit(f"#{index}: negative header length")
    shift = hlen // (2 * ch)
    pcm = np.frombuffer(data[hlen:], dtype="<i2").astype(np.int32)
    # vgmstream decodes the record from byte 0, so the first decoded frame is the header's
    # first int16 pair - NOT the payload's first sample
    head = np.frombuffer(data[:2 * ch], dtype="<i2").astype(np.int32)
    return {"name": s.name, "channels": ch, "frames": frames, "hlen": hlen, "shift": shift,
            "data": data, "header": data[:hlen], "pcm": pcm,
            "first": float(head.mean()) / 32768.0}


def anchor_of(rec: dict) -> int:
    return rec["frames"] - 1 - rec["shift"]


def edit(rec: dict, header0: float, K: int, wrap: bool) -> tuple[np.ndarray, list[int]]:
    """The ramp in int16 space: only the span is touched, the rest is byte-identical."""
    if rec["channels"] != 1:
        raise SystemExit(f"{rec['name']}: seam edit is mono-only, record has {rec['channels']} ch")
    a = anchor_of(rec)
    pcm = rec["pcm"].copy()
    touched = np.zeros(len(pcm), dtype=bool)
    start = max(0, a - K + 1)
    base = float(pcm[start - 1] if start > 0 else pcm[start]) / 32768.0
    seg = np.linspace(base, header0, a + 1 - start)
    pcm[start:a + 1] = np.clip(np.round(seg * 32767.0), -32768, 32767).astype(np.int32)
    touched[start:a + 1] = True
    # `wrap`: land on the payload's first sample (kills the audio-domain wrap).
    # otherwise: return to the payload's own last sample, so the tail stays continuous and the
    # existing (already passing) own wrap is left untouched.
    first = float(rec["pcm"][0] if wrap else rec["pcm"][-1]) / 32768.0
    seg_b = np.linspace(header0, first, rec["frames"] - 1 - a)
    pcm[a + 1:] = np.clip(np.round(seg_b * 32767.0), -32768, 32767).astype(np.int32)
    touched[a + 1:] = True
    return pcm, list(np.flatnonzero(touched))


def worst_step(pcm: np.ndarray, touched: list[int]) -> float:
    lo, hi = min(touched) - 1, max(touched) + 1
    seg = pcm[max(0, lo):hi + 1].astype(np.float64) / 32768.0
    return db(float(np.max(np.abs(np.diff(seg))))) if len(seg) > 1 else -999.0


def plan(rec: dict, own_wrap: float) -> dict | None:
    """Smallest K whose seam (both domains) and every adjacent step are at or below -40."""
    if rec["channels"] != 1:
        return None                      # a multi-channel seam edit is not defined here
    wrap = own_wrap > CLICK_DBFS
    header0 = rec["first"]
    for K in K_CHOICES:
        pcm, touched = edit(rec, header0, K, wrap)
        decoded = db(abs(float(pcm[anchor_of(rec)]) / 32768.0 - header0))
        own = db(abs(float(pcm[-1]) / 32768.0 - float(pcm[0]) / 32768.0))
        step = worst_step(pcm, touched)
        if decoded <= CLICK_DBFS and own <= CLICK_DBFS and step <= CLICK_DBFS:
            old = rec["pcm"][touched].astype(np.float64) / 32768.0
            new = pcm[touched].astype(np.float64) / 32768.0
            delta = new - old
            return {"applied": True, "K": K, "wrap_ramp": wrap, "header0": round(header0, 8),
                    "anchor": anchor_of(rec), "changed_frames": len(touched),
                    "changed_ms": round(len(touched) / 48.0, 4),
                    "seam_decoded_dbfs": decoded, "seam_payload_dbfs": own,
                    "worst_step_in_span_dbfs": step,
                    "rms_old_dbfs": rms_db(old), "rms_new_dbfs": rms_db(new),
                    "delta_rms_db": round(rms_db(new) - rms_db(old), 3),
                    "change_rms_dbfs": rms_db(delta),
                    "pcm": pcm}
    return None


def splice(raw: bytearray, rec: dict, pcm: np.ndarray) -> int:
    body = pcm.astype("<i2").tobytes()
    if len(body) != len(rec["data"]) - rec["hlen"]:
        raise SystemExit(f"{rec['name']}: edited payload changed length")
    first = raw.find(rec["data"])
    if first < 0 or raw.find(rec["data"], first + 1) >= 0:
        raise SystemExit(f"{rec['name']}: record data is not unique - refusing to splice")
    raw[first:first + len(rec["data"])] = rec["header"] + body
    return first


def loop_slots(mf: dict) -> list[dict]:
    return [s for s in mf["slots"] if "_loop" in s["name"]]


def measure(banks: dict[str, str], manifest: str) -> dict:
    """`v04_loops.facts()` repointed at this tree, plus the payload seam read from the record."""
    import v04_loops
    v04_loops.BANKS = banks["dir"]
    v04_loops.MANIFEST = manifest
    f = v04_loops.facts()
    for row in f["rows"]:
        raw = slurp(os.path.join(banks["dir"], f"{row['bank']}.bank"))
        rec = record(raw, row["index"])
        row["payload_measured"] = {
            "seam_dbfs": db(abs(float(rec["pcm"][-1]) / 32768.0
                                - float(rec["pcm"][0]) / 32768.0)),
            "first_int16": int(rec["pcm"][0]), "last_int16": int(rec["pcm"][-1]),
            "anchor_int16": int(rec["pcm"][anchor_of(rec)]),
            "header_first_int16": int(round(rec["first"] * 32768)),
            "shift_frames": rec["shift"],
        }
        row["verdict"] = ("PASS" if row["step_dbfs"] <= CLICK_DBFS else "RED")
        row["payload_verdict"] = ("PASS" if row["payload_measured"]["seam_dbfs"] <= CLICK_DBFS
                                  else "RED")
    f["summary"] = {
        "slots": len(f["rows"]),
        "decoded_pass": sum(1 for r in f["rows"] if r["verdict"] == "PASS"),
        "payload_pass": sum(1 for r in f["rows"] if r["payload_verdict"] == "PASS"),
    }
    return f


def derive() -> dict:
    """The expected RC5 banks, built in memory from `bm-RC4-audio`'s bytes."""
    mf = json.load(open(MANIFEST_SRC, encoding="utf-8"))
    out: dict = {"banks": {}, "slots": [], "manifest": mf}
    for bank in BANKS:
        raw = bytearray(slurp(os.path.join(SRC_BANKS, f"{bank}.bank")))
        for s in loop_slots(mf):
            if s["bank"] != bank:
                continue
            rec = record(bytes(raw), s["index"])
            d = v04_audio.decode(os.path.join(SRC_BANKS, f"{bank}.bank"), s["index"])
            own = v04_audio.seam(np.frombuffer(rec["data"][rec["hlen"]:], dtype="<i2")
                                 .astype(np.float64).reshape(-1, rec["channels"]) / 32768.0)
            before = {"decoded_dbfs": v04_audio.seam(d["pcm"]), "payload_dbfs": own,
                      "p99_dbfs": v04_audio.p99(v04_audio.steps(d["pcm"]))}
            already = before["decoded_dbfs"] <= CLICK_DBFS and own <= CLICK_DBFS
            p = None if already else plan(rec, own)
            if p is None:
                row = {"applied": False, "before": before, "after": before,
                       "slot": f"{bank}#{s['index']}", "name": s["name"],
                       "note": ("already at or below -40 dBFS in both domains" if already else
                                f"no mono seam edit defined for {rec['channels']} channels")}
            else:
                pcm = p.pop("pcm")
                off = splice(raw, rec, pcm)
                after = {"decoded_dbfs": p["seam_decoded_dbfs"],
                         "payload_dbfs": p["seam_payload_dbfs"],
                         "worst_step_in_span_dbfs": p["worst_step_in_span_dbfs"]}
                row = {**p, "before": before, "after": after, "data_offset": off,
                       "payload_sha256": sha(pcm.astype("<i2").tobytes()),
                       "slot": f"{bank}#{s['index']}", "name": s["name"]}
            out["slots"].append(row)
        out["banks"][bank] = {"bytes": len(raw), "sha256": sha(bytes(raw)),
                              "path": rel(os.path.join(OUT_BANKS, f"{bank}.bank"))}
    return out


def manifest_rc5(d: dict) -> dict:
    mf = json.loads(json.dumps(d["manifest"]))
    by_slot = {(r["slot"].split("#")[0], int(r["slot"].split("#")[1])): r for r in d["slots"]}
    for s in mf["slots"]:
        r = by_slot.get((s["bank"], int(s["index"])))
        if not r:
            continue
        s["measured"] = dict(s["measured"])
        s["measured"]["rc5_seam"] = {k: r["after"][k] for k in r["after"]}
        if r.get("applied"):
            s["payload_sha256"] = r["payload_sha256"]
            s["bytes"] = s["frames"] * int(s["channels"]) * 2
            s["data_offset"] = r["data_offset"]
            s["measured"]["rc5_seam_edit"] = {k: r[k] for k in
                                              ("K", "wrap_ramp", "header0", "anchor",
                                               "changed_frames", "changed_ms", "delta_rms_db",
                                               "change_rms_dbfs")}
    for w in mf["written"]:
        b = d["banks"][w["bank"]]
        w["file"] = b["path"]
        w["bytes"] = b["bytes"]
        w["sha256"] = b["sha256"]
    mf["card"] = CARD
    mf["generator"] = "Tools/scripts/rc5_loop279.py over Builds/bm-RC4-audio"
    mf["seam_edits"] = [{k: r.get(k) for k in ("slot", "name", "applied", "K", "wrap_ramp",
                                               "anchor", "changed_frames", "changed_ms",
                                               "delta_rms_db", "change_rms_dbfs")}
                        | {"before": r["before"], "after": r["after"]} for r in d["slots"]]
    return mf


def render(d: dict, f: dict) -> str:
    L = [f"# {TAG} - loop seams after the RC5 edit", "",
         f"Source tree `{rel(SRC)}` (never modified), copy `{rel(OUT)}`, "
         f"card `{CARD}`.", "",
         "Measured with `v04_loops.facts()`; `payload` is read from the record itself, because "
         "`v04_loops`' payload column re-derives `bm_audio.payload()` from the unfixed source and "
         "therefore describes the pre-edit payload.", "",
         "| slot | decoded seam | payload seam | p99 | edit | changed span | RMS delta |",
         "|---|---:|---:|---:|---|---:|---:|"]
    for r in f["rows"]:
        e = next(x for x in d["slots"] if x["slot"] == f"{r['bank']}#{r['index']}")
        L.append(f"| `{r['name']}` | **{r['step_dbfs']}** | "
                 f"{r['payload_measured']['seam_dbfs']} | {r['interior_p99_dbfs']} | "
                 f"{'K=' + str(e['K']) + (' + wrap' if e.get('wrap_ramp') else '') if e.get('applied') else 'none'} | "
                 f"{e.get('changed_frames', 0)} frames / {e.get('changed_ms', 0)} ms | "
                 f"{e.get('delta_rms_db', 0)} dB |")
    L += ["", f"**{f['summary']['decoded_pass']}/{f['summary']['slots']} decoded seams and "
          f"{f['summary']['payload_pass']}/{f['summary']['slots']} payload seams at or below "
          f"-40 dBFS.**", ""]
    return "\n".join(L) + "\n"


def prepare() -> None:
    if os.path.exists(OUT):
        marker = os.path.join(OUT, "receipt.json")
        old = {}
        if os.path.exists(marker):
            try:
                old = json.load(open(marker, encoding="utf-8"))
            except Exception:
                old = {}
        if old.get("card") != CARD:
            raise SystemExit(f"{rel(OUT)} exists and is not a {CARD} tree "
                             f"(card {old.get('card')!r}) - refusing to replace")
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for name in ("aaf", "banks"):
        shutil.copytree(os.path.join(SRC, name), os.path.join(OUT, name))
    for name in ("install.ps1", "bank_set.json", "events.json"):
        p = os.path.join(SRC, name)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(OUT, name))
    os.makedirs(VERIFY, exist_ok=True)


def build(write: bool = True) -> int:
    d = derive()
    if write:
        prepare()
        for bank in BANKS:
            # apply the same two splices to the copy, from the copy's own bytes
            path = os.path.join(OUT_BANKS, f"{bank}.bank")
            raw = bytearray(slurp(path))
            for r in d["slots"]:
                if r["slot"].split("#")[0] != bank or not r.get("applied"):
                    continue
                rec = record(bytes(raw), int(r["slot"].split("#")[1]))
                pcm, _t = edit(rec, r["header0"], r["K"], r["wrap_ramp"])
                splice(raw, rec, pcm)
            with open(path, "wb") as fh:
                fh.write(bytes(raw))
        mf = manifest_rc5(d)
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mf, fh, indent=1)
            fh.write("\n")
        receipt = {"schema": 1, "card": CARD, "tag": TAG, "base": rel(SRC),
                   "generator": "Tools/scripts/rc5_loop279.py",
                   "route": "copy of Builds/bm-RC4-audio; bm_audio splice rule (header kept, "
                            "payload body replaced, unique match)",
                   "banks": d["banks"], "seam_edits": mf["seam_edits"],
                   "manifest": rel(MANIFEST), "installed": False}
        with open(os.path.join(OUT, "receipt.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(receipt, fh, indent=1)
            fh.write("\n")

    f = measure({"dir": OUT_BANKS}, MANIFEST if write else MANIFEST)

    # the tree's banks must equal the in-memory derivation, byte for byte
    drift = []
    for bank in BANKS:
        p = os.path.join(OUT_BANKS, f"{bank}.bank")
        got = sha(slurp(p)) if os.path.exists(p) else None
        if got != d["banks"][bank]["sha256"]:
            drift.append(f"{bank}.bank on disk {got} != derived {d['banks'][bank]['sha256']}")

    if write:
        with open(os.path.join(VERIFY, "loops_rc5.json"), "w", encoding="utf-8",
                  newline="\n") as fh:
            json.dump({"summary": f["summary"], "rows": f["rows"], "edits": d["slots"],
                       "banks": d["banks"]}, fh, indent=1)
            fh.write("\n")
        with open(os.path.join(VERIFY, "loops_rc5.md"), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(render(d, f))

    for r in f["rows"]:
        print(f"{r['verdict']:4s} {r['name']:42s} decoded {r['step_dbfs']:>7} dBFS  "
              f"payload {r['payload_measured']['seam_dbfs']:>7} dBFS  "
              f"p99 {r['interior_p99_dbfs']:>7}")
    for e in d["slots"]:
        if e.get("applied"):
            print(f"  edit {e['slot']}: K={e['K']} wrap={e['wrap_ramp']} "
                  f"{e['changed_frames']} frames ({e['changed_ms']} ms), "
                  f"delta RMS {e['delta_rms_db']} dB, change {e['change_rms_dbfs']} dBFS")
        else:
            print(f"  edit {e['slot']}: none (already at or below -40 in both domains)")
    print(f"summary: {f['summary']}")
    if drift:
        for x in drift:
            print("FAIL:", x)
        return 1
    print(f"{'PASS' if not drift else 'FAIL'}: {rel(OUT)} banks equal the re-derived edit")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(SRC_BANKS):
        print(f"MISSING: {rel(SRC_BANKS)}", file=sys.stderr)
        return 2
    if a.check and not os.path.exists(MANIFEST):
        print(f"FAIL: {rel(MANIFEST)} missing (run --write)", file=sys.stderr)
        return 1
    return build(write=a.write)


if __name__ == "__main__":
    raise SystemExit(main())
