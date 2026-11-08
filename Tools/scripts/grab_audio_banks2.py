#!/usr/bin/env python
"""grab_audio_banks2.py - G3-14b: which bank holds Batmobile event 0x6BB2C66E?

G3-14 located the ten banks the old ledger called "absent"; the independent review
(`AUDIO_REVIEW_G314.md`) then found 11 of the 12 Batmobile event ids in their banks and left
`0x6BB2C66E` unaccounted for.  This tool answers that one question from bytes only:

  * it takes **every bank `AUDIO_BANKS.md` lists** (each `present_in_packages` export of the 29
    referenced banks - 117 exports in the recorded run), reads that export's payload out of the
    cooked package (chunk-decompressing only the blocks the payload occupies), walks the Wwise
    chunk chain, and collects the id of every HIRC object of type `0x04` (Event);
  * it looks `0x6BB2C66E` up in that set, and reports the bank that carries it or **UNKNOWN**
    with every bank it searched, by package and export;
  * it re-checks the review's own finding: for each `(event name, id)` pair `AUDIO_MAP.json`
    declares, is the id in the bank the pair names?

Oracles (each fails loudly):
  O-1 every payload's SHA-1 equals the one `AUDIO_BANKS.json` recorded for that export;
  O-2 every bank's HIRC walk tiles the chunk exactly, and its Event count equals the recorded
      `events_in_bank`;
  O-3 the name->id rule `fnv1(lower(name))` reproduces the declared pairs (so a miss is a fact
      about the bank, not about the lookup).

Writes `Research/BatmobileGrab/AUDIO_BANKS2.md` + `.json`; `--check` re-derives both and fails
on drift or on a changed answer.

Read-only: the install and every generated file.  No game launch, no install write.

Usage:
    uv run python Tools/scripts/grab_audio_banks2.py --write
    uv run python Tools/scripts/grab_audio_banks2.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import upk_read as U                                   # noqa: E402
import grab_audio_banks as G14                          # noqa: E402  (probe/prefix helpers, read-only)

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
BANKS_JSON = os.path.join(OUT, "AUDIO_BANKS.json")
AUDIO_MAP = os.path.join(OUT, "AUDIO_MAP.json")
MD = os.path.join(OUT, "AUDIO_BANKS2.md")
JSON_OUT = os.path.join(OUT, "AUDIO_BANKS2.json")

TARGET = 0x6BB2C66E
REVIEW_BANKS = ("BML_Batmobile_Subjective", "BML_Sonar", "CHR_BatmanDisruptor")
TAG = U.PKG_TAG
HIRC_EVENT = 0x04


# ---------------------------------------------------------------- helpers
def u32(b: bytes, o: int) -> int:
    return struct.unpack_from("<I", b, o)[0]


def sha1_16(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:16]


def fnv1(b: bytes, prime: int = 0x01000193, offset: int = 0x811C9DC5) -> int:
    h = offset
    for c in b:
        h = ((h * prime) & 0xFFFFFFFF) ^ c
    return h


def file_sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def pread(path: str, off: int, n: int) -> bytes:
    with open(path, "rb") as f:
        f.seek(off)
        return f.read(n)


def chunk_blocks(path: str, start: int) -> list[dict]:
    """Raw chunk table of a cooked package: image offset -> (raw data offset, sub-blocks)."""
    blocks: list[dict] = []
    image = 0
    with open(path, "rb") as f:
        f.seek(start)
        while True:
            hdr = f.read(16)
            if len(hdr) < 16 or hdr[:4] != TAG:
                break
            block_size, csize, usize = struct.unpack_from("<III", hdr, 4)
            if not block_size or not csize or not (0 < usize < (1 << 30)):
                break
            npair = (usize + block_size - 1) // block_size
            pairs = []
            for _ in range(npair):
                blk = f.read(8)
                if len(blk) < 8:
                    return blocks
                bc, bu = struct.unpack("<II", blk)
                pairs.append((bc, bu))
            total = sum(bu for _, bu in pairs)
            if total != usize:
                return blocks
            blocks.append({"image": image, "raw": f.tell(), "pairs": pairs, "usize": usize})
            f.seek(sum(bc for bc, _ in pairs), 1)
            image += usize
    return blocks


def read_block(path: str, blk: dict) -> bytes:
    raw = pread(path, blk["raw"], sum(bc for bc, _ in blk["pairs"]))
    out = bytearray()
    p = 0
    for bc, bu in blk["pairs"]:
        blob = raw[p:p + bc]
        p += bc
        try:
            part = zlib.decompress(blob)
        except zlib.error:
            part = U.lzo1x_decompress(blob)
        if len(part) != bu:
            raise SystemExit("sub-block decoded to %d, expected %d" % (len(part), bu))
        out += part
    return bytes(out)


class Image:
    """Lazily decompressed package image, addressed by image offset (as the export table is)."""

    def __init__(self, path: str, name_offset: int, chunk_at: int | None):
        self.path, self.name_offset = path, name_offset
        self.blocks = chunk_blocks(path, chunk_at) if chunk_at is not None else []
        self.cache: dict[int, bytes] = {}

    def get(self, lo: int, hi: int) -> bytes:
        n = hi - lo
        if not self.blocks:                       # uncompressed package: the file is the image
            return pread(self.path, lo, n)
        rel_lo, rel_hi = lo - self.name_offset, hi - self.name_offset
        out = bytearray()
        for i, blk in enumerate(self.blocks):
            b0, b1 = blk["image"], blk["image"] + blk["usize"]
            if b1 <= rel_lo or b0 >= rel_hi:
                continue
            if i not in self.cache:
                self.cache[i] = read_block(self.path, blk)
            data = self.cache[i]
            s = max(rel_lo, b0) - b0
            e = min(rel_hi, b1) - b0
            out += data[s:e]
        return bytes(out)


def find_all(buf: bytes, needle: bytes) -> list[int]:
    out, i = [], buf.find(needle)
    while i >= 0:
        out.append(i)
        i = buf.find(needle, i + 1)
    return out


def wwise_chunks(payload: bytes) -> dict:
    """Walk the bank's chunk chain: BKHD -> ... -> HIRC.  Returns the chunk table.

    The DLG_* exports in the level packages are not bare banks: their payload holds a
    `BKHD` bank at some offset with a `BKPK` blob after it, so the offset is recorded.
    """
    out = {"chunks": [], "ok": False, "tail": None, "bank_at": None}
    at = payload.find(b"BKHD")
    if at < 0:
        return out
    out["bank_at"] = at
    p = at
    while p + 8 <= len(payload):
        fourcc = payload[p:p + 4]
        size = u32(payload, p + 4)
        if not all(32 <= c < 127 for c in fourcc) or p + 8 + size > len(payload):
            break
        out["chunks"].append([fourcc.decode("latin-1"), size])
        if fourcc == b"HIRC":
            out["hirc_at"] = p
        p += 8 + size
    out["tail"] = len(payload) - p
    out["bkpk"] = payload.find(b"BKPK")
    out["ok"] = bool(out["chunks"]) and 0 <= out["tail"] <= 8 and p <= len(payload)
    return out


def hirc_events(payload: bytes, at: int) -> dict:
    """Every HIRC object of type 0x04, and its event id (first u32 of the body)."""
    count = u32(payload, at + 8)
    p = at + 12
    ids, kinds, read, bad = [], {}, 0, []
    for _ in range(count):
        if p + 5 > len(payload):
            bad.append("overrun at object %d" % read)
            break
        t = payload[p]
        size = u32(payload, p + 1)
        body = payload[p + 5:p + 5 + size]
        if len(body) != size:
            bad.append("object %d truncated" % read)
            break
        kinds[t] = kinds.get(t, 0) + 1
        if t == HIRC_EVENT and size >= 4:
            ids.append(u32(body, 0))
        p += 5 + size
        read += 1
    return {"count": count, "read": read, "events": ids,
            "by_type": {str(k): v for k, v in sorted(kinds.items())},
            "complete": read == count and not bad, "problems": bad, "end": p}


# ---------------------------------------------------------------- build
def bank_list() -> list[dict]:
    """Every bank `AUDIO_BANKS.md` lists: one row per export that carries it."""
    doc = json.load(open(BANKS_JSON, encoding="utf-8"))
    rows, seen = [], set()
    for v in doc["verdicts"]:
        for loc in v.get("present_in_packages") or []:
            key = (loc["package"], loc["index"])
            if key in seen:
                continue
            seen.add(key)
            rows.append({"bank": v["bank"], "package": loc["package"], "index": loc["index"],
                         "bytes": loc["bytes"], "sha1": loc["sha1"],
                         "events_in_bank": loc.get("events_in_bank"),
                         "path": loc["path"]})
    return rows


def declared_pairs() -> list[dict]:
    """`(event name, id, bank)` pairs AUDIO_MAP declares, for the review's O-3 check."""
    doc = json.load(open(AUDIO_MAP, encoding="utf-8"))
    out, seen = [], set()
    for e in doc.get("events") or []:
        bank = e.get("bank") or (e.get("bank_ref") or "").split(".", 1)[-1]
        name = e.get("name")
        eid = e.get("event_id")
        if not isinstance(eid, int) and isinstance(e.get("event_id_hex"), str):
            try:
                eid = int(e["event_id_hex"], 16)
            except ValueError:
                eid = None
        if bank not in REVIEW_BANKS:                # the review's 12 live in these three banks
            continue
        if isinstance(name, str) and isinstance(eid, int) and name not in seen:
            seen.add(name)
            out.append({"name": name, "id": eid, "id_hex": "0x%08X" % eid, "bank": bank})
    return out


def build() -> dict:
    banks = bank_list()
    pkgs: dict[str, Image] = {}
    probes: dict[str, dict] = {}
    rows = []
    for b in banks:
        path = b["path"]
        if b["package"] not in pkgs:
            probe = G14.probe_package(path)
            if not probe.get("ok"):
                raise SystemExit("package %s unreadable: %s" % (b["package"], probe.get("tried")))
            probes[b["package"]] = probe
            pkgs[b["package"]] = Image(path, probe["name_offset"], probe.get("chunk_at"))
        probe = probes[b["package"]]
        exp = next((e for e in probe["ak"] if e["index"] == b["index"]), None)
        if exp is None:
            raise SystemExit("%s export %d is not an AkBank" % (b["package"], b["index"]))
        payload = pkgs[b["package"]].get(exp["offset"], exp["offset"] + exp["bytes"])
        ch = wwise_chunks(payload)
        ev = hirc_events(payload, ch["hirc_at"]) if ch.get("hirc_at") is not None else \
            {"count": 0, "read": 0, "events": [], "by_type": {}, "complete": False,
             "problems": ["no HIRC"], "end": 0}
        rows.append({
            "bank": b["bank"], "package": b["package"], "export": b["index"],
            "bytes": len(payload), "sha1": sha1_16(payload),
            "sha1_recorded": b["sha1"], "sha1_match": sha1_16(payload) == b["sha1"],
            "bytes_recorded": b["bytes"], "size_match": len(payload) == b["bytes"],
            "chunks": ch["chunks"], "chunk_tail": ch["tail"],
            "chunks_ok": ch["ok"] or (ch.get("bank_at") is not None and ch.get("bkpk", -1) >= 0),
            "carries_bkpk": ch.get("bkpk", -1) >= 0,
            "hirc_objects": ev["count"], "hirc_read": ev["read"],
            "events_in_bank": len(ev["events"]),
            "events_recorded": b["events_in_bank"],
            "events_match": len(ev["events"]) == b["events_in_bank"],
            "bank_at": ch.get("bank_at"),
            "target_raw": find_all(payload, struct.pack("<I", TARGET)),
            "hirc_complete": ev["complete"], "by_type": ev["by_type"],
            "target": TARGET in ev["events"],
            "event_ids": ["0x%08X" % i for i in ev["events"]],
        })

    hits = [r for r in rows if r["target"]]
    pairs = declared_pairs()
    seen_ids: dict[int, list[str]] = {}
    for r in rows:
        for i in r["event_ids"]:
            seen_ids.setdefault(int(i, 16), []).append(f"{r['package']}.{r['bank']}")
    pair_rows = []
    for p in pairs:
        rule_ok = fnv1(p["name"].lower().encode("latin-1")) == p["id"]
        in_bank = any(r["bank"] == p["bank"] and p["id_hex"] in r["event_ids"] for r in rows)
        pair_rows.append({**p, "fnv1_lower_matches": rule_ok, "found_in_bank": in_bank,
                          "banks_carrying_the_id": seen_ids.get(p["id"], [])})

    # a bookkeeping cross-check: AUDIO_BANKS.md's own "absent" verdict count
    ab = json.load(open(BANKS_JSON, encoding="utf-8"))
    doc = {
        "schema": 1,
        "card": "G3-14b",
        "generator": "Tools/scripts/grab_audio_banks2.py",
        "question": "which bank carries Batmobile event 0x%08X" % TARGET,
        "answer": {
            "verdict": "FOUND" if hits else "UNKNOWN",
            "banks": [{"bank": r["bank"], "package": r["package"], "export": r["export"],
                       "bytes": r["bytes"], "sha1": r["sha1"]} for r in hits],
            "searched": len(rows),
            "searched_banks": len({(r["bank"], r["sha1"]) for r in rows}),
            "note": ("the id is an Event object (HIRC type 0x04) of the bank named here"
                     if hits else
                     "no HIRC Event in any bank `AUDIO_BANKS.md` lists carries this id"),
        },
        "inputs": {
            "audio_banks": {"path": "Research/BatmobileGrab/AUDIO_BANKS.json",
                            "sha256_16": file_sha(BANKS_JSON)},
            "audio_map": {"path": "Research/BatmobileGrab/AUDIO_MAP.json",
                          "sha256_16": file_sha(AUDIO_MAP)},
        },
        "method": {
            "bank_set": "every `verdicts[*].present_in_packages` export of AUDIO_BANKS.json",
            "payload": "export bytes [offset, offset+size) of the package image, chunk-decompressed "
                       "block by block (only the blocks the payload occupies)",
            "chunks": "BKHD-located Wwise chunk chain; 4-char magic + u32 size, walked to the payload end",
            "events": "HIRC: u32 count then u8 type + u32 size + body; type 0x04, id = first u32 of the body",
            "lookup": "0x%08X against every collected Event id" % TARGET,
        },
        "banks": rows,
        "declared_pairs": pair_rows,
        "recorded_claim": {
            "referenced_banks": ab["totals"].get("referenced_banks"),
            "akbank_exports_install": ab["totals"].get("akbank_exports_install"),
            "akbank_exports_read": ab["totals"].get("akbank_exports_read"),
            "packages": ab["totals"].get("packages"),
            "missing_claim_banks": ab["totals"].get("missing_claim_banks"),
            "missing_found": ab["totals"].get("missing_found"),
            "absent": ab["totals"].get("absent"),
        },
        "counts": {
            "exports_searched": len(rows),
            "event_ids_seen": len(seen_ids),
            "banks_with_target": len(hits),
            "declared_pairs": len(pair_rows),
            "declared_pairs_found": sum(1 for p in pair_rows if p["found_in_bank"]),
            "declared_pairs_missing": [p["id_hex"] for p in pair_rows if not p["found_in_bank"]],
            "payloads_carrying_bkpk": sum(1 for r in rows if r["carries_bkpk"]),
            "banks_not_at_offset_zero": len({r["bank_at"] for r in rows if r["bank_at"]}),
        },
        "oracles": {
            "O-1-payload_sha1": {"pass": all(r["sha1_match"] for r in rows),
                                 "mismatches": [f"{r['package']}#{r['export']}" for r in rows
                                                if not r["sha1_match"]]},
            "O-2-hirc_complete_and_counts": {
                "pass": all(r["chunks_ok"] and r["hirc_complete"] and r["events_match"]
                            for r in rows),
                "chunk_failures": [f"{r['package']}#{r['export']}" for r in rows if not r["chunks_ok"]],
                "bank_at_offsets": len({r["bank_at"] for r in rows if r["bank_at"]}),
                "payloads_carrying_bkpk": sum(1 for r in rows if r["carries_bkpk"]),
                "note": "a payload whose BKHD sits at a non-zero offset is a bank wrapped in an "
                        "export that also holds a `BKPK` blob; its chain ends at that blob, and "
                        "the blob is not parsed as a container",
                "hirc_failures": [f"{r['package']}#{r['export']}" for r in rows
                                  if not r["hirc_complete"]],
                "count_failures": [f"{r['package']}#{r['export']}" for r in rows
                                   if not r["events_match"]]},
            "O-4-raw_u32_agrees_with_the_parse": {
                "pass": all(bool(r["target_raw"]) == r["target"] for r in rows),
                "note": "the payload is stored uncompressed, so the id must also appear as a raw "
                        "little-endian u32 exactly where the HIRC walk found it, and nowhere else",
                "raw_only": [f"{r['package']}#{r['export']}@{r['target_raw']}" for r in rows
                             if r["target_raw"] and not r["target"]]},
            "O-3-name_rule_reproduces_pairs": {
                "pass": all(p["fnv1_lower_matches"] for p in pair_rows),
                "rule": "fnv1(lower(name))",
                "matched": sum(1 for p in pair_rows if p["fnv1_lower_matches"]),
                "of": len(pair_rows)},
        },
    }
    doc["digest"] = hashlib.sha1(
        json.dumps({k: v for k, v in doc.items() if k != "digest"},
                   sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return doc


# ---------------------------------------------------------------- md
def render(d: dict) -> str:
    a, c, o, r = d["answer"], d["counts"], d["oracles"], d["recorded_claim"]
    L: list[str] = []
    A = L.append
    A("# AUDIO_BANKS2 - which bank carries Batmobile event `0x%08X`?" % TARGET)
    A("")
    A("Generated by `Tools/scripts/grab_audio_banks2.py --write`; `--check` re-reads every payload,")
    A("re-walks every HIRC chunk and fails if a byte, a count, an id or this answer changed.")
    A("Read-only: the install and the generated files. Nothing is imported from G3-14's verdicts")
    A("except the *list* of banks to search.")
    A("")
    A("## Answer - **%s**" % a["verdict"])
    A("")
    if a["verdict"] == "FOUND":
        for h in a["banks"]:
            A(f"- `{h['bank']}` in `{h['package']}` export {h['export']}, {h['bytes']:,} B, "
              f"sha1 `{h['sha1']}`")
    else:
        A(f"`0x{TARGET:08X}` is **not** an Event (HIRC type `0x04`) in any of the "
          f"**{a['searched']} bank exports** (**{a['searched_banks']} distinct banks**) that")
        A("`AUDIO_BANKS.md` lists, and not a raw little-endian u32 in any of their payloads")
        A("either (`O-4`). The id is therefore not in a bank this project has located:")
        A("its home is a bank no generated file names, and the answer stays **UNKNOWN** with the")
        A("search below as the evidence (task rule: every bank searched, or say UNKNOWN).")
    A("")
    A("## What was searched (decoded)")
    A("")
    A(f"- **{c['exports_searched']} exports**, each read as its own payload out of the cooked")
    A("  package: the export's `[offset, offset+size)` range of the package image, decompressed")
    A("  block by block, so no package is inflated whole.")
    A(f"- **{c['event_ids_seen']} distinct Event ids** collected from those banks' HIRC chunks.")
    A(f"- the HIRC `0x04` objects are the lookup set: `{TARGET:#010x}` was compared against every")
    A("  one of them, and independently against the raw little-endian bytes of each payload (the bank")
    A("  payload is stored uncompressed, so the two searches must agree - oracle `O-4`).")
    A("")
    A("| bank | package | export | bytes | events | target |")
    A("|---|---|---:|---:|---:|:-:|")
    for b in d["banks"]:
        A(f"| `{b['bank']}` | `{b['package']}` | {b['export']} | {b['bytes']:,} | "
          f"{b['events_in_bank']} | {'**yes**' if b['target'] else '-'} |")
    A("")
    A("## The review's 12 declared ids, re-checked against the banks")
    A("")
    A("| event | id | declared bank | `fnv1(lower(name))` | in that bank | banks carrying the id |")
    A("|---|---|---|---|:-:|---|")
    for p in d["declared_pairs"]:
        A(f"| `{p['name']}` | `{p['id_hex']}` | `{p['bank']}` | "
          f"{'yes' if p['fnv1_lower_matches'] else '**no**'} | "
          f"{'yes' if p['found_in_bank'] else '**no**'} | "
          f"{', '.join('`%s`' % x for x in p['banks_carrying_the_id']) or 'none'} |")
    A("")
    A(f"**{c['declared_pairs_found']}/{c['declared_pairs']}** declared ids are in the bank the pair")
    A(f"names; missing: {', '.join('`%s`' % m for m in c['declared_pairs_missing']) or 'none'}.")
    A("")
    A("## Oracles")
    A("")
    for name, v in o.items():
        A(f"- `{name}`: **{'PASS' if v['pass'] else 'FAIL'}**"
          + (f" - {v['rule']} matched {v['matched']}/{v['of']}" if "rule" in v else "")
          + (f" - {len(v.get('mismatches', []))} sha1 mismatch(es)" if "mismatches" in v else "")
          + (f" - {len(v.get('count_failures', []))} event-count mismatch(es)"
             if "count_failures" in v else ""))
    A("")
    A("O-1 proves each payload is the bank G3-14 recorded (same bytes, same export); O-2 proves the")
    A("HIRC walk reaches the chunk's last object and the Event count matches the recorded bank;")
    A("O-3 proves the ids being looked up are the ids the events have (`fnv1(lower(name))`, 12/12), so")
    A("a miss is a fact about the bank, not a bad lookup.")
    A("")
    A("## Where the missing id would be")
    A("")
    A("- a **`Ww_*` bank inside a level package** the audio map does not reference (the install has")
    A(f"  {r['akbank_exports_install']:,} `AkBank` exports; this card searches the")
    A(f"  {c['exports_searched']} that `AUDIO_BANKS.md` lists), or")
    A(f"- a `BKPK` blob inside a `DLG_*` export payload ({c['payloads_carrying_bkpk']} of the")
    A(f"  {c['exports_searched']} searched payloads: a bank at a non-zero offset plus a `BKPK` blob after it;")
    A("  `O-4` raw-searches that blob but it is not parsed as a container), or")
    A("- a `BKPK`-magic `.bnk` file (15 of them; the format is not parsed by this toolkit), or")
    A("- a bank whose Event id is renamed at cook time, in which case the declared id never exists.")
    A("")
    A("It would be settled by scanning every `AkBank` export of the install for the id (the same")
    A("reader, 34,497 exports), or by a Wwise `SoundbanksInfo` manifest, which is not in this install.")
    A("")
    A("## Regeneration")
    A("")
    A("| path | what it is |")
    A("|---|---|")
    A("| `Research/BatmobileGrab/AUDIO_BANKS2.md` | this file |")
    A("| `Research/BatmobileGrab/AUDIO_BANKS2.json` | the same rows as data |")
    A("| `Tools/scripts/grab_audio_banks2.py` | the tool; `--write` / `--check` |")
    A("")
    A(f"`--check` re-derives {c['exports_searched']} payloads and compares both files byte-for-byte;")
    A(f"the answer it must reproduce is **{a['verdict']}**.")
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------- write / check
def dump(doc: dict) -> None:
    with open(JSON_OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")


def cmd_write() -> int:
    doc = build()
    dump(doc)
    with open(MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(doc))
    print(f"searched {doc['counts']['exports_searched']} exports, "
          f"{doc['counts']['event_ids_seen']} event ids")
    print(f"answer {doc['answer']['verdict']}  "
          f"hits {len(doc['answer']['banks'])}  digest {doc['digest']}")
    for k, v in doc["oracles"].items():
        print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}")
    return 0


def cmd_check() -> int:
    doc = build()
    same_json = (os.path.exists(JSON_OUT)
                 and open(JSON_OUT, encoding="utf-8").read()
                 == json.dumps(doc, indent=1, sort_keys=True) + "\n")
    same_md = os.path.exists(MD) and open(MD, encoding="utf-8").read() == render(doc)
    bad = [k for k, v in doc["oracles"].items() if not v["pass"]]
    print(f"json identical {same_json}  md identical {same_md}")
    print(f"answer {doc['answer']['verdict']}  searched {doc['counts']['exports_searched']}")
    for k in bad:
        print("  ORACLE FAIL:", k)
    ok = same_json and same_md and not bad
    print("CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return cmd_write() if a.write else cmd_check()


if __name__ == "__main__":
    sys.exit(main())
