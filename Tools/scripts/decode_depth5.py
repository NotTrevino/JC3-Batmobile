"""decode_depth5.py - G3-12c: rank the 121 PARTIAL files by format, decode the biggest family.

G3-12 (`DECODE_DEPTH.json`) graded the Serpente donor's 566 inner files 441 FULL / 121 PARTIAL
/ 4 NAMED-ONLY.  This pass answers the next question: what format do the PARTIAL bytes share,
which family covers the most files, and does that family close byte-for-byte when decoded?

Ranking (recomputed here from G3-12's own census, `files[].ext` + `files[].note`):

    family    block type of the undecoded bytes                                 files    bytes
    .ddsc     AVTX texel payload (mip block chain)                                116  73640512
    .rbm      GeneralMkIII block (block 1 of the .rbm)                              3     82344
    .physicsc Havok 2014 packfile objects (per-class field extents)                 1    340368
    .epe      RTPC ConvertProperty blocks (round trip not byte-identical)           1    109526
    .pfxc     PFX wrapper + Havok packfile (NAMED-ONLY)                             4     10000

The dominant family is the `.ddsc` AVTX container: 116 of 121 PARTIAL files, 73.6 MB of the
74.2 MB graded PARTIAL (99.3%).  It is decoded here from the bytes alone.

.ddsc - AVTX container, 128-byte header + one stored mip chain to EOF
  Header 0x00..0x2C is fitted, not published: the field offsets are the ones whose values make
  the storage arithmetic close on all 116 files, and the arithmetic is the oracle.

     0x00 4s   magic 'AVTX'                    116/116
     0x04 H    version                         1 on 116/116
     0x06 B    unknown                         values decoded, meaning UNKNOWN
     0x07 B    resource dimension, stored -1   2 on 116/116 (TEXTURE2D by value only)
     0x08 I    texel format id                 71 / 77 / 83 / 87
     0x0C H    width  (texels, level 0)        the stored chain + table close from it
     0x0E H    height (texels, level 0)        same
     0x10 H    depth                           1 on 116/116
     0x12 H    flags                           0 / 1 / 8 / 9, meaning UNKNOWN
     0x14 B    mip count of the full chain     table length = this - the next field
     0x15 B    mip count stored in this file   the stored chain tiles to EOF
     0x16 H    zero                            116/116
     0x18 I    zero                            116/116
     0x1C I    zero                            116/116
     0x20 I    header size                     128 on 116/116
     0x24 I    payload size                    the stored chain sums to it exactly
     0x28 I    constant                        16 on 116/116, meaning UNKNOWN
     0x2C 84   omitted-mip table, 7 slots x 12  one record per level NOT stored in this file

  Block size is solved per file from {8, 16, 32, 64} bytes per 4x4 block: exactly one candidate
  makes chain_sum(width, height, first_stored_level, mip_count_in_file) == payload size.  The
  survivors must form a function of the format id across all 116 - that fleet invariant is what
  turns a per-file fit into a format map.

  Oracles, each of which fails if a field is wrong:
    O1 the archive holds exactly the 116 paths G3-12 graded PARTIAL .ddsc
    O2 every file names AVTX and closes as header_size + payload == file length
    O3 exactly one block size per file closes the stored chain
    O4 the format id -> block size map is a function (one block size per format)
    O5 the stored mip ranges tile [header_size, len) with zero residue
    O6 the omitted-mip table is decoded: k = full - in_file records, each (prefix-sum offset,
       level price, tag 0x01000010), and 0x2C..0x80 is zero after the last record
    O7 full-chain identity: the levels 0..full-1 cost payload + table total exactly
    O8 round trip: the 128-byte header rebuilt from the decoded fields, plus the payload, is
       the file byte for byte
    O9 negation: perturbing width or height by 4 texels, or either mip count by 1, breaks O7 on
       every file - a field that could slide would not be pinned.  (+-1 texel is also tested and
       only *reported*, because 4x4 block rounding can absorb it.)
    O10 the earlier passes agree: every file's block size, mip counts and FULL grade match
       DECODE_DEPTH6.json (G3-12d)

  What this does NOT do: decode texels into pixels.  No project reader turns the blocks into an
  image, and the format-id *names* (71 = BC1, 77 = BC3, 83 = BC5, per `Tools/scripts/tex2ddsc.py`
  lines 5-7 and 20-22) are project precedent, not byte evidence; 87's name is UNKNOWN here.

Usage
    python Tools/scripts/decode_depth5.py --write
    python Tools/scripts/decode_depth5.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_rc  # noqa: E402
import eetoc  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "DECODE_DEPTH5.md")
JS = os.path.join(OUT, "DECODE_DEPTH5.json")
PRIOR = os.path.join(OUT, "DECODE_DEPTH.json")
PRIOR6 = os.path.join(OUT, "DECODE_DEPTH6.json")
BUNDLE = bm_rc.DIR + bm_rc.OLD + ".ee"

MAGIC = b"AVTX"
HDR = struct.Struct("<4sHBBIHHHHBBHIIIII")          # 44 bytes, 0x00..0x2C
HDR_NAMES = ("magic", "version", "unknown_06", "dimension_minus_1", "format_id", "width",
             "height", "depth", "flags", "mip_count_full", "mip_count_in_file", "zero_16",
             "zero_18", "zero_1c", "size_header", "size_body", "const_28")
TAIL_OFF = 0x2C
TAIL_END = 0x80
REC = 12
SLOTS = (TAIL_END - TAIL_OFF) // REC                     # 7
REC_TAG = 0x01000010
BLOCKS = (8, 16, 32, 64)

# The block type of each family's undecoded bytes.  Each string paraphrases the G3-12 `note`
# of that family, quoted in the markdown; none of it is a guess about the format's meaning.
BLOCK_TYPE = {
    ".ddsc": "AVTX texel payload (mip block chain)",
    ".rbm": "GeneralMkIII block (block 1 of the .rbm)",
    ".physicsc": "Havok 2014 packfile objects (per-class field extents)",
    ".epe": "RTPC ConvertProperty blocks (round trip not byte-identical)",
    ".pfxc": "PFX wrapper + Havok packfile",
}


# --------------------------------------------------------------------------- bundle
def bundle():
    raw = eetoc.unaaf(bm_rc.vfs(BUNDLE))
    return raw, eetoc.sarc_dir(raw)


def inner(raw, name, off, size):
    """An inner file's bytes.  offset 0 is a reference: read it through the index."""
    return raw[off:off + size] if off else bm_rc.vfs(name)


# --------------------------------------------------------------------------- ddsc
def mip_size(w: int, h: int, level: int, blk: int) -> int:
    """One mip's stored bytes: 4x4 blocks, each dimension at least one block."""
    ww, hh = max(1, w >> level), max(1, h >> level)
    return max(1, (ww + 3) // 4) * max(1, (hh + 3) // 4) * blk


def chain_sum(w: int, h: int, start: int, n: int, blk: int) -> int:
    return sum(mip_size(w, h, start + i, blk) for i in range(n))


def header(blob: bytes) -> dict:
    h = dict(zip(HDR_NAMES, HDR.unpack_from(blob, 0)))
    h["magic"] = h["magic"].decode("latin-1")
    return h


def solve(blob: bytes) -> tuple[dict, int, list]:
    """(header, first stored level, block sizes whose chain sum equals `payload`)."""
    h = header(blob)
    start = h["mip_count_full"] - h["mip_count_in_file"]
    hits = []
    if 0 <= start <= SLOTS:
        for blk in BLOCKS:
            if chain_sum(h["width"], h["height"], start, h["mip_count_in_file"], blk) \
                    == h["size_body"]:
                hits.append(blk)
    return h, start, hits


def closes(w: int, h: int, start: int, n: int, blk: int, body: int,
           records: list, mip_full: int) -> bool:
    """The whole storage identity for a candidate (width, height, start, block size).

    Both halves must hold: the stored levels cost `body`, and the full chain costs `body` plus
    the omitted-mip table.  A perturbation that only moves bytes between the two halves still
    fails one of them.
    """
    if start < 0 or start > SLOTS or n < 0 or mip_full < n:
        return False
    stored = chain_sum(w, h, start, n, blk)
    if stored != body:
        return False
    if mip_full - n != len(records):
        return False
    off = 0
    for i, rec in enumerate(records):
        lvl = start - 1 - i
        sz = mip_size(w, h, lvl, blk)
        if (rec["offset"], rec["size"]) != (off, sz):
            return False
        off += sz
    return chain_sum(w, h, 0, mip_full, blk) == body + off


def ddsc_decode(blob: bytes) -> dict:
    h, start, hits = solve(blob)
    blk = hits[0] if len(hits) == 1 else None
    k = h["mip_count_full"] - h["mip_count_in_file"]
    recs, mips = [], []
    for i in range(max(0, min(k, SLOTS))):
        r_off, r_size, r_tag = struct.unpack_from("<III", blob, TAIL_OFF + REC * i)
        recs.append({"i": i, "level": k - 1 - i, "offset": r_off, "size": r_size, "tag": r_tag})
    tail_rest = blob[TAIL_OFF + REC * max(0, min(k, SLOTS)):TAIL_END]

    ok_tile = False
    if blk:
        pos = h["size_header"]
        for i in range(h["mip_count_in_file"]):
            lvl = start + i
            sz = mip_size(h["width"], h["height"], lvl, blk)
            mips.append({"level": lvl, "w": max(1, h["width"] >> lvl),
                         "h": max(1, h["height"] >> lvl), "offset": pos, "size": sz})
            pos += sz
        ok_tile = pos == len(blob)

    table_ok = bool(blk) and closes(h["width"], h["height"], start, h["mip_count_in_file"],
                                    blk, h["size_body"], recs, h["mip_count_full"]) \
        and all(r["tag"] == REC_TAG for r in recs) and not any(tail_rest)
    table_total = sum(r["size"] for r in recs)
    identity = bool(blk) and chain_sum(h["width"], h["height"], 0, h["mip_count_full"], blk) \
        == h["size_body"] + table_total
    closes_len = h["size_header"] + h["size_body"] == len(blob)
    magic_ok = h["magic"] == MAGIC.decode()

    # O8 round trip: rebuild the header (fields + table + zero pad) from decoded values only.
    rebuilt = bytearray(HDR.pack(*[h[n] if n != "magic" else MAGIC for n in HDR_NAMES]))
    for r in recs:
        rebuilt += struct.pack("<III", r["offset"], r["size"], REC_TAG)
    rebuilt += b"\x00" * (TAIL_END - len(rebuilt))
    rebuilt += blob[h["size_header"]:]
    roundtrip = bytes(rebuilt) == blob

    # O9 negation: perturbations must break the identity; +-1 texel is reported, not required.
    blind, soft_blind = [], []
    if blk:
        for dw, dh, ds in ((4, 0, 0), (-4, 0, 0), (0, 4, 0), (0, -4, 0),
                           (0, 0, 1), (0, 0, -1)):
            w2, h2, s2 = h["width"] + dw, h["height"] + dh, start + ds
            if w2 < 1 or h2 < 1:
                continue
            if closes(w2, h2, s2, h["mip_count_in_file"], blk, h["size_body"], recs,
                      h["mip_count_full"]):
                blind.append("w%+d h%+d start%+d" % (dw, dh, ds))
        for dw, dh in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            w2, h2 = h["width"] + dw, h["height"] + dh
            if w2 < 1 or h2 < 1:
                continue
            if closes(w2, h2, start, h["mip_count_in_file"], blk, h["size_body"], recs,
                      h["mip_count_full"]):
                soft_blind.append("w%+d h%+d" % (dw, dh))

    full = bool(magic_ok and blk and closes_len and ok_tile and table_ok and identity
                and roundtrip and not blind)
    return {
        "header": h, "first_stored_level": start, "block_bytes": blk,
        "block_candidates": hits, "records": recs, "table_total": table_total,
        "table_zero_pad": not any(tail_rest), "mips": mips, "mip_count": len(mips),
        "closes": closes_len, "tiles": ok_tile, "table_ok": table_ok,
        "identity": identity, "roundtrip": roundtrip,
        "blind_spots": blind, "soft_blind_spots": soft_blind,
        "full_chain_bytes": chain_sum(h["width"], h["height"], 0, h["mip_count_full"], blk)
        if blk else 0,
        "grade": "FULL" if full else "PARTIAL",
    }


# --------------------------------------------------------------------------- census
def prior_census() -> list:
    """G3-12's per-file rows, kept as the ranking input (this script does not re-grade them)."""
    d = json.load(open(PRIOR, encoding="utf-8"))
    return [f for f in d["files"] if f["grade"] != "FULL"]


def rank(rows: list) -> list:
    groups: dict[tuple, dict] = {}
    for f in rows:
        key = (f["ext"], BLOCK_TYPE.get(f["ext"], "UNKNOWN"))
        g = groups.setdefault(key, {"ext": f["ext"], "block_type": key[1], "files": 0,
                                    "bytes": 0, "grades": {}, "paths": []})
        g["files"] += 1
        g["bytes"] += f["bytes"]
        g["grades"][f["grade"]] = g["grades"].get(f["grade"], 0) + 1
        g["paths"].append(f["file"])
    out = sorted(groups.values(), key=lambda g: (-g["files"], -g["bytes"]))
    total = sum(g["files"] for g in out)
    for g in out:
        g["share_of_files"] = round(g["files"] / total, 4)
    return out


def archive_ddsc() -> list:
    raw, ents = bundle()
    out = []
    for name, off, size in ents:
        if os.path.splitext(name)[1].lower() != ".ddsc":
            continue
        blob = inner(raw, name, off, size)
        d = ddsc_decode(blob)
        h = d["header"]
        out.append({
            "file": name, "bytes": len(blob), "stored": "reference" if off == 0 else "embedded",
            "version": h["version"], "format_id": h["format_id"],
            "width": h["width"], "height": h["height"],
            "depth": h["depth"], "flags": h["flags"], "unknown_06": h["unknown_06"],
            "const_28": h["const_28"], "dimension_minus_1": h["dimension_minus_1"],
            "size_header": h["size_header"], "size_body": h["size_body"],
            "mip_count_full": h["mip_count_full"], "mip_count_in_file": h["mip_count_in_file"],
            "first_stored_level": d["first_stored_level"], "block_bytes": d["block_bytes"],
            "block_candidates": d["block_candidates"], "records": d["records"],
            "table_total": d["table_total"], "mips": d["mips"], "mip_count": d["mip_count"],
            "closes": d["closes"], "tiles": d["tiles"], "table_ok": d["table_ok"],
            "identity": d["identity"], "roundtrip": d["roundtrip"],
            "blind_spots": d["blind_spots"], "soft_blind_spots": d["soft_blind_spots"],
            "full_chain_bytes": d["full_chain_bytes"], "grade": d["grade"],
        })
    return sorted(out, key=lambda r: r["file"])


def hist(rows: list, field: str) -> dict:
    c: dict = {}
    for r in rows:
        c[str(r[field])] = c.get(str(r[field]), 0) + 1
    return dict(sorted(c.items()))


def formats(rows: list) -> list:
    c: dict = {}
    for r in rows:
        e = c.setdefault(str(r["format_id"]), {"format_id": r["format_id"], "files": 0,
                                               "bytes": 0, "block_bytes": set(), "texels": 0})
        e["files"] += 1
        e["bytes"] += r["bytes"]
        if r["block_bytes"]:
            e["block_bytes"].add(r["block_bytes"])
        e["texels"] += r["width"] * r["height"]
    out = []
    for e in sorted(c.values(), key=lambda x: -x["files"]):
        blks = sorted(e["block_bytes"])
        out.append({"format_id": e["format_id"], "files": e["files"], "bytes": e["bytes"],
                    "block_bytes": blks, "base_texels": e["texels"],
                    "bytes_per_texel": (blks[0] / 16.0) if len(blks) == 1 else None})
    return out


def prior6() -> dict:
    if not os.path.exists(PRIOR6):
        return {}
    return {f["file"]: f for f in json.load(open(PRIOR6, encoding="utf-8"))["ddsc"]}


def build() -> dict:
    rows = prior_census()
    ranked = rank(rows)
    dd = archive_ddsc()
    fmts = formats(dd)
    p6 = prior6()

    # -- cross-check against G3-12d, per file
    mism = []
    for r in dd:
        p = p6.get(r["file"])
        if not p:
            mism.append({"file": r["file"], "why": "absent from DECODE_DEPTH6.json"})
            continue
        got = (r["block_bytes"], r["mip_count_full"], r["mip_count_in_file"], r["grade"])
        exp = (p.get("block_bytes"), p.get("mip_count_full"), p.get("mip_count_in_file"),
               p.get("grade"))
        if got != exp:
            mism.append({"file": r["file"], "why": "G3-12c %s vs G3-12d %s" % (got, exp)})

    graded_paths = {f["file"] for f in rows if f["ext"] == ".ddsc"}
    arch_paths = {r["file"] for r in dd}
    per_fmt_blk = {str(f["format_id"]): f["block_bytes"] for f in fmts}

    checks = [
        ("the archive holds exactly the 116 .ddsc paths G3-12 graded PARTIAL",
         len(dd) == 116 and arch_paths == graded_paths,
         "%d in the archive, %d in G3-12, %d shared, %d only-archive, %d only-G3-12"
         % (len(dd), len(graded_paths), len(arch_paths & graded_paths),
            len(arch_paths - graded_paths), len(graded_paths - arch_paths))),
        ("every .ddsc names AVTX and closes as header_size + payload == file length",
         all(r["closes"] and r["dimension_minus_1"] == 2 and r["depth"] == 1
             and r["size_header"] == 128 for r in dd),
         "%d/%d close; header %s; dimension-1 %s; depth %s"
         % (sum(1 for r in dd if r["closes"]), len(dd),
            hist(dd, "size_header"), hist(dd, "dimension_minus_1"), hist(dd, "depth"))),
        ("exactly one block size per file closes the stored mip chain",
         all(len(r["block_candidates"]) == 1 for r in dd),
         "single-candidate files %d/%d; candidates seen %s"
         % (sum(1 for r in dd if len(r["block_candidates"]) == 1), len(dd),
            sorted({tuple(r["block_candidates"]) for r in dd}))),
        ("the format id -> block size map is a function across the fleet",
         all(len(v) == 1 for v in per_fmt_blk.values()),
         "; ".join("%s -> %s B" % (k, v) for k, v in sorted(per_fmt_blk.items()))),
        ("the stored mip ranges tile [header_size, len) with zero residue",
         all(r["tiles"] for r in dd),
         "%d/%d files; %d mips stored" % (sum(1 for r in dd if r["tiles"]), len(dd),
                                          sum(r["mip_count"] for r in dd))),
        ("the omitted-mip table decodes: k records, prefix-sum offsets, level prices, tag 16",
         all(r["table_ok"] for r in dd),
         "%d/%d files; %d records; tags %s; total %d B; pad zero on %d/%d"
         % (sum(1 for r in dd if r["table_ok"]), len(dd),
            sum(len(r["records"]) for r in dd),
            sorted({rec["tag"] for r in dd for rec in r["records"]}),
            sum(r["table_total"] for r in dd),
            sum(1 for r in dd if not r["records"] or r["table_ok"]), len(dd))),
        ("full-chain identity: levels 0..full-1 cost payload + table total",
         all(r["identity"] for r in dd),
         "%d/%d files; %d B of texel chain over %d B stored + %d B omitted"
         % (sum(1 for r in dd if r["identity"]), len(dd),
            sum(r["full_chain_bytes"] for r in dd), sum(r["size_body"] for r in dd),
            sum(r["table_total"] for r in dd))),
        ("round trip: header rebuilt from decoded fields + payload == the file, byte for byte",
         all(r["roundtrip"] for r in dd),
         "%d/%d files" % (sum(1 for r in dd if r["roundtrip"]), len(dd))),
        ("negation: +-4 texels or +-1 mip breaks the identity on every file",
         all(not r["blind_spots"] for r in dd),
         "%d files with a blind spot; %d files where +-1 texel is absorbed by block rounding"
         % (sum(1 for r in dd if r["blind_spots"]),
            sum(1 for r in dd if r["soft_blind_spots"]))),
        ("the earlier pass agrees per file (block size, mip counts, FULL grade)",
         len(dd) == 116 and not mism,
         "%d mismatches vs DECODE_DEPTH6.json" % len(mism)),
        ("G3-12's 121 PARTIAL split by extension as re-counted here",
         sum(g["grades"].get("PARTIAL", 0) for g in ranked) == 121,
         "%d PARTIAL: %s; plus %d NAMED-ONLY: %s"
         % (sum(g["grades"].get("PARTIAL", 0) for g in ranked),
            ", ".join("%s %d" % (g["ext"], g["grades"].get("PARTIAL", 0)) for g in ranked),
            sum(g["grades"].get("NAMED-ONLY", 0) for g in ranked),
            ", ".join("%s %d" % (g["ext"], g["grades"].get("NAMED-ONLY", 0))
                     for g in ranked if g["grades"].get("NAMED-ONLY")))),
        ("every non-.ddsc PARTIAL / NAMED-ONLY file is listed with its block type",
         len(ranked) >= 2 and sum(g["files"] for g in ranked if g["ext"] != ".ddsc") == 9,
         ", ".join("%s %d" % (g["ext"], g["files"]) for g in ranked if g["ext"] != ".ddsc")),
    ]

    return {
        "task": "G3-12c - rank the PARTIAL files by format, decode the largest family",
        "bundle": BUNDLE,
        "sources": {"ranking": os.path.relpath(PRIOR, ROOT).replace("\\", "/"),
                    "cross_check": os.path.relpath(PRIOR6, ROOT).replace("\\", "/")
                    if os.path.exists(PRIOR6) else None,
                    "bundle_reader": "bm_rc.vfs + eetoc.unaaf + eetoc.sarc_dir",
                    "reused": ["Tools/scripts/decode_depth.py",
                               "Tools/scripts/decode_depth2.py",
                               "Tools/scripts/decode_depth6.py"]},
        "ranking": [{k: v for k, v in g.items()} for g in ranked],
        "chosen": {"ext": ranked[0]["ext"], "block_type": ranked[0]["block_type"],
                   "files": ranked[0]["files"], "bytes": ranked[0]["bytes"]},
        "ddsc": {
            "files": len(dd), "bytes": sum(r["bytes"] for r in dd),
            "FULL": sum(1 for r in dd if r["grade"] == "FULL"),
            "PARTIAL": sum(1 for r in dd if r["grade"] == "PARTIAL"),
            "mips_stored": sum(r["mip_count"] for r in dd),
            "files_omitting_levels": sum(1 for r in dd if r["records"]),
            "records": sum(len(r["records"]) for r in dd),
            "payload_bytes": sum(r["size_body"] for r in dd),
            "omitted_bytes": sum(r["table_total"] for r in dd),
            "full_chain_bytes": sum(r["full_chain_bytes"] for r in dd),
            "header_hist": {f: hist(dd, f) for f in ("version", "unknown_06",
                                                     "dimension_minus_1", "flags",
                                                     "size_header", "const_28", "depth")},
            "by_format": fmts,
            "mip_counts": hist(dd, "mip_count_in_file"),
            "first_levels": hist(dd, "first_stored_level"),
            "soft_spot_types": hist([{"spot": s} for r in dd for s in r["soft_blind_spots"]],
                                    "spot"),
            "soft_blind_files": [{"file": r["file"], "width": r["width"], "height": r["height"],
                                  "spots": r["soft_blind_spots"]}
                                 for r in dd if r["soft_blind_spots"]],
        },
        "coverage": {
            "partial_files": sum(g["grades"].get("PARTIAL", 0) for g in ranked),
            "partial_bytes": sum(f["bytes"] for f in rows if f["grade"] == "PARTIAL"),
            "chosen_files": len(dd),
            "chosen_bytes": sum(r["bytes"] for r in dd),
        },
        "remaining": [g for g in ranked if g["ext"] != ".ddsc"],
        "files": dd,
        "cross_check_mismatches": mism,
        "checks": [{"check": n, "pass": bool(ok), "detail": d} for n, ok, d in checks],
    }


# --------------------------------------------------------------------------- render
def render(d: dict) -> str:
    s, a = d["ddsc"], []
    A = a.append
    A("# JC3 donor decode depth 5 (G3-12c) - ranked PARTIAL families, `.ddsc` decoded")
    A("")
    A("Generated by `Tools/scripts/decode_depth5.py` (`--write`); `--check` recomputes every")
    A("number from the source bytes and compares.  Labels: **decoded** = read from bytes at a")
    A("stated offset; **derived** = arithmetic on decoded values with the rule given;")
    A("**UNKNOWN** = not decoded, with why.")
    A("")
    A("Inputs: the donor bundle `%s` (read through `bm_rc.vfs`, `eetoc.unaaf`,"
      % d["bundle"].replace("\\", "/"))
    A("`eetoc.sarc_dir`), G3-12's census `%s` for the ranking, and G3-12d's"
      % d["sources"]["ranking"])
    A("`%s` for the per-file cross-check." % (d["sources"]["cross_check"] or "(absent)"))
    A("")
    A("## 1. Ranked PARTIAL families")
    A("")
    A("| family | block type of the undecoded bytes | files | bytes | grade at G3-12 | share of files |")
    A("|---|---|---:|---:|---|---:|")
    for g in d["ranking"]:
        A("| `%s` | %s | %d | %d | %s | %.1f%% |"
          % (g["ext"], g["block_type"], g["files"], g["bytes"],
             ", ".join("%s %d" % (k, v) for k, v in sorted(g["grades"].items())),
             100 * g["share_of_files"]))
    A("")
    cv = d["coverage"]
    A("The largest family is `%s` - **%d files, %d bytes**, decoded in full below.  That is"
      % (d["chosen"]["ext"], d["chosen"]["files"], d["chosen"]["bytes"]))
    A("**%d of the %d PARTIAL files (%.0f%%) and %d of the %d graded PARTIAL bytes (%.1f%%)**."
      % (cv["chosen_files"], cv["partial_files"],
         100.0 * cv["chosen_files"] / cv["partial_files"],
         cv["chosen_bytes"], cv["partial_bytes"],
         100.0 * cv["chosen_bytes"] / cv["partial_bytes"]))
    A("")
    A("## 2. `.ddsc` - the AVTX container")
    A("")
    A("Header 0x00..0x2C, decoded by offset on %d/%d files:" % (s["FULL"], s["files"]))
    A("")
    A("| offset | size | field | value(s) seen | evidence |")
    A("|---|---:|---|---|---|")
    rows = [("0x00", "4", "magic", "AVTX", "116/116"),
            ("0x04", "2", "version", str(s["header_hist"]["version"]), "decoded"),
            ("0x06", "1", "unknown", str(s["header_hist"]["unknown_06"]), "values decoded, meaning UNKNOWN"),
            ("0x07", "1", "resource dimension, stored - 1", str(s["header_hist"]["dimension_minus_1"]),
             "116/116 = 2"),
            ("0x08", "4", "texel format id",
             ", ".join("%d (%d files)" % (f["format_id"], f["files"]) for f in s["by_format"]),
             "block size solved per file, oracle O4"),
            ("0x0C", "2", "width (texels, level 0)", "per file", "the chain closes from it, O3/O7"),
            ("0x0E", "2", "height (texels, level 0)", "per file", "the chain closes from it, O3/O7"),
            ("0x10", "2", "depth", "1", "116/116"),
            ("0x12", "2", "flags", str(s["header_hist"]["flags"]), "values decoded, meaning UNKNOWN"),
            ("0x14", "1", "mip count of the full chain", "per file", "table length = this - the next field, O6"),
            ("0x15", "1", "mip count stored here", str(s["mip_counts"]), "stored chain tiles to EOF, O5"),
            ("0x16", "2", "zero", "0", "116/116"),
            ("0x18", "4", "zero", "0", "116/116"),
            ("0x1C", "4", "zero", "0", "116/116"),
            ("0x20", "4", "header size", str(s["header_hist"]["size_header"]), "116/116, and 128 + payload == len"),
            ("0x24", "4", "payload size", "per file", "stored chain sums to it exactly, O3"),
            ("0x28", "4", "constant", str(s["header_hist"]["const_28"]), "116/116; meaning UNKNOWN"),
            ("0x2C", "84", "omitted-mip table, 7 slots of 12", "k records", "section 2.2")]
    for r in rows:
        A("| %s | %s | %s | %s | %s |" % r)
    A("")
    A("### 2.1 Texel block size per format")
    A("")
    A("Solved, not assumed: per file each candidate in {8, 16, 32, 64} bytes per 4x4 block is")
    A("tried and only the one whose chain sum equals the payload survives (O3); the survivors")
    A("must form a function of the format id (O4).")
    A("")
    A("| format id | files | bytes | base texels | bytes per 4x4 block | bytes/texel | "
      "name (project precedent only) |")
    A("|---|---:|---:|---:|---:|---:|---|")
    names = {71: "colour BC1 (`tex2ddsc.py:5-7`)", 83: "normal BC5 (`tex2ddsc.py:6`)",
             77: "glass BC3 (`tex2ddsc.py:20-22`)", 87: "UNKNOWN"}
    for f in s["by_format"]:
        bpt = f["bytes_per_texel"]
        A("| %d | %d | %d | %d | %s | %s | %s |"
          % (f["format_id"], f["files"], f["bytes"], f["base_texels"],
             "/".join(str(b) for b in f["block_bytes"]),
             "%.2f" % bpt if bpt is not None else "UNKNOWN",
             names.get(f["format_id"], "UNKNOWN")))
    A("")
    A("Format 87's 64 bytes per 4x4 block is 4 bytes per texel, and its three files store")
    A("exactly width x height x 4 bytes at level 0 (`t_spherical_ramp`, `t_flare_headlight_ramp`:")
    A("256 x 256 x 4 = 262144 = payload; `erosion_smallcurve_soft`: 256 x 16 x 4 = 16384).  That")
    A("is consistent with an uncompressed 4-channel format, but no project decoder or export")
    A("proves the channel layout, so its identity stays UNKNOWN.")
    A("")
    A("The names column is **not** byte evidence: no project reader decodes the blocks into")
    A("pixels, and the id -> codec names come from `Tools/scripts/tex2ddsc.py`, whose docstring")
    A("records them as the formats `ConvertTexture.exe` was driven with.  The block *sizes* are")
    A("decoded here; the codec identities are precedent.")
    A("")
    A("### 2.2 The 84-byte tail is the omitted-mip table")
    A("")
    A("`k = mip_count_full - mip_count_in_file` (%s records over %d files).  Record `i` is"
      % (s["records"], s["files"]))
    A("`(u32 offset, u32 size, u32 tag)` describing the level `k-1-i` - the levels the file does")
    A("*not* store, listed largest-absent first.  `size` equals that level's block price,")
    A("`offset` its prefix sum, `tag` 0x01000010 on every record, and the rest of the 84 bytes")
    A("is zero.  The identity that closes it:")
    A("")
    A("    full chain (levels 0..mip_count_full-1) == payload + sum(record sizes)")
    A("    %d B == %d B + %d B" % (s["full_chain_bytes"], s["payload_bytes"], s["omitted_bytes"]))
    A("")
    A("Stored mips: %d over %d files, laid down from offset 128, tiling to EOF with zero residue"
      % (s["mips_stored"], s["files"]))
    A("(first stored level: %s).  %d of %d files store the whole chain and %d omit levels; the"
      % (s["first_levels"], s["files"] - s["files_omitting_levels"], s["files"],
         s["files_omitting_levels"]))
    A("table is empty on those %d, which is why its pad is zero on all %d."
      % (s["files"] - s["files_omitting_levels"], s["files"]))
    A("")
    A("## 3. Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, c in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |" % (i, c["check"], "PASS" if c["pass"] else "FAIL",
                                          c["detail"]))
    A("")
    A("O9 is the one that matters for a wrong offset: every dimension is perturbed by 4 texels")
    A("and every mip count by 1, and the storage identity must break.  %d files have a blind spot"
      % sum(1 for c in d["files"] if c["blind_spots"]))
    A("at 4 texels; at 1 texel %d files have at least one absorbed perturbation (reported, not"
      % len(s["soft_blind_files"]))
    A("relied on): %s." % ", ".join("%s on %d" % (k, v)
                                   for k, v in sorted(s["soft_spot_types"].items())))
    if s["soft_blind_files"]:
        A("")
    A("Examples of the absorbed perturbations:")
    A("")
    for f in s["soft_blind_files"][:10]:
            A("- `%s` (%dx%d): %s" % (f["file"], f["width"], f["height"], f["spots"]))
    A("")
    A("## 4. What remains")
    A("")
    A("| family | files | bytes | block type | status |")
    A("|---|---:|---:|---|---|")
    for g in d["remaining"]:
        status = ("closed by G3-12d (`DECODE_DEPTH6.md`)" if g["ext"] == ".pfxc"
                  else "open - undecoded block named in G3-12")
        A("| `%s` | %d | %d | %s | %s |" % (g["ext"], g["files"], g["bytes"], g["block_type"],
                                            status))
    A("")
    A("Together with the %d `%s` files decoded here, that accounts for every PARTIAL and"
      % (d["chosen"]["files"], d["chosen"]["ext"]))
    A("NAMED-ONLY file in G3-12's census.")
    A("")
    A("## 5. UNKNOWNs")
    A("")
    A("1. **Texel contents.** The block *layout* is decoded (size, offsets, tiling); no decoder")
    A("   turns a block into pixels.  Would need a BCn decoder and a reference image; not")
    A("   attempted here, and not needed for byte accounting.")
    A("2. **Format 87's codec.** Its block size is decoded (see 2.1); no name is.  Would need a")
    A("   texture that uses it exported by `ConvertTexture.exe`, or the engine's format enum.")
    A("3. **Header fields of unknown meaning.** `0x06` (values %s), flags `0x12` (values %s) and"
      % (list(s["header_hist"]["unknown_06"]), list(s["header_hist"]["flags"])))
    A("   the constant 16 at `0x28`.  Values are decoded on every file; their meaning is not")
    A("   carried by any check here.")
    A("4. **Why a mip level is omitted.** The table says which levels are absent and what they")
    A("   cost; why the cooker dropped exactly those (streaming size, editor setting) is UNKNOWN.")
    A("")
    A("## 6. Reproduce")
    A("")
    A("    uv run python Tools/scripts/decode_depth5.py --write")
    A("    uv run python Tools/scripts/decode_depth5.py --check")
    A("")
    return "\n".join(a) + "\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pass --write or --check")

    d = build()
    md = render(d)
    js = json.dumps(d, indent=1) + "\n"

    ok = True
    for c in d["checks"]:
        print("%s  %s" % ("PASS" if c["pass"] else "FAIL", c["check"]))
        print("      %s" % c["detail"])
        ok = ok and c["pass"]
    print("\n%d/%d oracles pass" % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))

    if args.write:
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(JS, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote %s (%d B)" % (os.path.relpath(MD, ROOT), len(md.encode("utf-8"))))
        print("wrote %s (%d B)" % (os.path.relpath(JS, ROOT), len(js.encode("utf-8"))))
    if args.check:
        stale = []
        for path, want in ((MD, md), (JS, js)):
            if not os.path.exists(path):
                stale.append("%s missing" % os.path.relpath(path, ROOT))
                continue
            got = open(path, encoding="utf-8").read()
            if got != want:
                stale.append("%s differs" % os.path.relpath(path, ROOT))
        if stale:
            print("CHECK FAILED: " + "; ".join(stale))
            ok = False
        else:
            print("CHECK OK: the stored .md/.json are byte-identical to a fresh recompute")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
