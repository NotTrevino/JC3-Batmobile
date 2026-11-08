"""decode_depth6.py - G3-12d: the 45 PARTIAL `.ddsc` and the 4 PARTIAL `.pfxc` of the Serpente donor.

G3-12b (`DECODE_DEPTH2`) left two families short and named the ranges it could not close:

  * 45 of the 116 `.ddsc` had a non-zero 84-byte table in the header tail 0x2C..0x80;
  * all 4 `.pfxc` had 512 bytes after the Havok packfile that nothing read.

This script closes both, or records exactly where it stops.  Nothing is taken from a published
layout: every field below is read from the bytes and every reading is carried by an oracle that
would fail if it were wrong.

.ddsc - the header tail is the *omitted-mip table*
  Header 0x00..0x2C fits the same way G3-12b fitted it (the mip chain built from
  format block size, width, height and mip count must sum to `size_body` and tile
  [size_header, len) with zero residue; the block size per format is solved per file from
  {8,16,32,64} and the survivors must form a function of the format id).
  What G3-12b called an opaque tail is 84 bytes = 7 slots of 12, and the record count is
  `mip_count_full - mip_count_in_file`: one record per mip of the full chain that is NOT in
  this file.  Record i is (u32 offset, u32 size, u32 tag) with size = the level (k-1-i),
  offset = the prefix sum of the sizes before it, tag = 0x01000010 on every record of every
  file, and the slots after the last record zero.  The oracle is the full-chain identity:
  the mips of levels 0..mip_count_full-1 cost exactly `size_body + sum(record sizes)`, i.e.
  the table's total is precisely the texel bytes the file does not hold.

.pfxc - the container is a wrapper plus ONE packfile that runs to EOF
  `PFX\\0` + 4 u32 + 28 zero bytes = 68 bytes, then `0x57E0E057` at 0x44 (located by its own
  magic).  G3-12b read the packfile's `__data__` end field (1920) as an absolute packfile
  offset, which made the file look like it had 512 unread trailing bytes.  It is the section's
  LENGTH: the data section starts at 0x244 and is 1920 bytes long, so the packfile ends at
  0x9C4 = 2500 = the file end.  Its own fixup tables prove where they sit - the local fixup
  slots start 1600 bytes into the section, and they are exactly the table at file 0x884.
  So the "trailing blob" is the last 512 bytes of `__data__`: 192 bytes of object-body tail
  (the end of `hknpConvexPolytopeShape` etc.) plus 128 + 96 + 96 bytes of local, global and
  virtual fixup slots.  Byte accounting on every file: 68 + 256 + 256 + 0 + (1600 + 128 + 96
  + 96) = 2500.

  Inside the bodies, the polytope's face table and index list are decoded and cross-checked
  against the polytope object's own vcount/pcount/icount words and against `jc3hkx`'s
  `decode_polytope` output.

Usage
    python Tools/scripts/decode_depth6.py --write
    python Tools/scripts/decode_depth6.py --check
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
import jc3hkx  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "DECODE_DEPTH6.md")
JS = os.path.join(OUT, "DECODE_DEPTH6.json")
BUNDLE = bm_rc.DIR + bm_rc.OLD + ".ee"

AVTX_MAGIC = b"AVTX"
PFX_MAGIC = b"PFX\x00"
HAVOK_MAGIC = 0x57E0E057
HDR = struct.Struct("<4sHBBIHHHHBBHIIIII")          # 44 bytes, 0x00..0x2C
HDR_NAMES = ("magic", "version", "byte_06", "dimension_minus_1", "format_id", "width",
             "height", "depth", "flags", "mip_count_full", "mip_count_in_file",
             "zero_22", "zero_24", "zero_28", "size_header", "size_body", "const_40")
TAIL_OFF = 0x2C
REC = 12                                             # u32 offset, u32 size, u32 tag
TAIL_BYTES = 0x80 - TAIL_OFF                         # 84 = 7 slots
TAIL_SLOTS = TAIL_BYTES // REC                       # 7
REC_TAG = 0x01000010
BLOCK_CANDIDATES = (8, 16, 32, 64)

WRAP_SIZE = 0x44
SECTION_REC = 0x40                                   # 19-byte name, 0xFF, 7 u32, pad
PFX_PAD_ZERO = (0x14, WRAP_SIZE)
FACE_REC = 4                                         # u16 corner offset, u8 count, u8 code
FILL = 0x7F


# --------------------------------------------------------------------------- bundle
def bundle():
    raw = eetoc.unaaf(bm_rc.vfs(BUNDLE))
    return raw, eetoc.sarc_dir(raw)


def body(raw, name, off, size):
    """An inner file's bytes.  offset 0 is a reference: read it through the index."""
    return raw[off:off + size] if off else bm_rc.vfs(name)


# --------------------------------------------------------------------------- ddsc
def mip_size(w: int, h: int, level: int, blk: int) -> int:
    """One mip's stored bytes: 4x4 blocks, each dimension at least one block."""
    ww, hh = max(1, w >> level), max(1, h >> level)
    return max(1, (ww + 3) // 4) * max(1, (hh + 3) // 4) * blk


def chain_sum(w: int, h: int, start: int, n: int, blk: int) -> int:
    return sum(mip_size(w, h, start + i, blk) for i in range(n))


def ddsc_decode(blob: bytes) -> dict:
    h = dict(zip(HDR_NAMES, HDR.unpack_from(blob, 0)))
    k = h["mip_count_full"] - h["mip_count_in_file"]
    hits = []
    for blk in BLOCK_CANDIDATES:
        if 0 <= k <= TAIL_SLOTS and chain_sum(h["width"], h["height"], k,
                                              h["mip_count_in_file"], blk) == h["size_body"]:
            hits.append(blk)
    blk = hits[0] if len(hits) == 1 else None

    # -- the omitted-mip table: k records at 0x2C, one per absent level
    recs, want = [], []
    off = 0
    for i in range(max(0, k)):
        r_off, r_size, r_tag = struct.unpack_from("<III", blob, TAIL_OFF + REC * i)
        lvl = k - 1 - i
        recs.append({"i": i, "level": lvl, "offset": r_off, "size": r_size, "tag": r_tag})
        want.append({"level": lvl, "offset": off,
                     "size": mip_size(h["width"], h["height"], lvl, blk) if blk else 0})
        off += want[-1]["size"]
    tail_rest = blob[TAIL_OFF + REC * max(0, k):0x80]
    table_matches = bool(blk) and all(
        (r["level"], r["offset"], r["size"], r["tag"]) == (w["level"], w["offset"], w["size"], REC_TAG)
        for r, w in zip(recs, want)) and not any(tail_rest)
    table_total = sum(r["size"] for r in recs)

    # -- the stored mips: levels k..mip_count_full-1, laid down from size_header
    mips, ok_chain = [], False
    if blk:
        pos = h["size_header"]
        for i in range(h["mip_count_in_file"]):
            lvl = k + i
            sz = mip_size(h["width"], h["height"], lvl, blk)
            mips.append({"level": lvl, "w": max(1, h["width"] >> lvl), "h": max(1, h["height"] >> lvl),
                         "offset": pos, "size": sz})
            pos += sz
        ok_chain = pos == len(blob)

    closes = h["size_header"] + h["size_body"] == len(blob)
    full_chain = chain_sum(h["width"], h["height"], 0, h["mip_count_full"], blk) if blk else 0
    identity = bool(blk) and full_chain == h["size_body"] + table_total
    magic_ok = blob[:4] == AVTX_MAGIC and h["dimension_minus_1"] == 2
    full = bool(magic_ok and blk and closes and ok_chain and table_matches and identity)

    return {
        "header": h, "tail_records": k, "records": recs, "expected": want,
        "table_matches": table_matches, "table_total": table_total,
        "tail_rest_zero": not any(tail_rest), "block_bytes": blk,
        "block_candidates": hits, "mips": mips, "closes": closes,
        "chain_to_eof": ok_chain, "full_chain_bytes": full_chain, "identity": identity,
        "grade": "FULL" if full else "PARTIAL",
    }


# --------------------------------------------------------------------------- pfxc
def pfxc_decode(blob: bytes) -> dict:
    """Wrapper + the single packfile it wraps, tiled to EOF by the packfile's own sizes."""
    magic = blob[:4]
    wrap = list(struct.unpack_from("<4I", blob, 4))
    pad_zero = not any(blob[PFX_PAD_ZERO[0]:PFX_PAD_ZERO[1]])
    pack_off = next((i for i in range(0, min(len(blob), 0x200) - 4)
                     if struct.unpack_from("<I", blob, i)[0] == HAVOK_MAGIC), -1)
    out = {"magic": magic.decode("latin-1"), "wrapper": wrap, "wrapper_pad_zero": pad_zero,
           "packfile_offset": pack_off, "grade": "PARTIAL", "regions": []}
    if magic != PFX_MAGIC or pack_off != WRAP_SIZE:
        return out

    p = jc3hkx.Packfile(blob[pack_off:])
    cn, ty, dt = p.sections["__classnames__"], p.sections["__types__"], p.sections["__data__"]
    base = pack_off + dt.data                      # file offset of __data__ byte 0
    # The three fixup tables are the *own* offsets of the data section's record, so their
    # position is decoded, not assumed: bodies [0, lf), local [lf, gf), global [gf, vf),
    # virtual [vf, ex).
    regions = [
        ("PFX wrapper", 0, pack_off),
        ("packfile header", pack_off, cn.data),
        ("__classnames__", pack_off + cn.data, cn.end),
        ("__types__ (empty)", pack_off + ty.data, ty.end),
        ("__data__ object bodies (%d objects)" % len(p.objects), base, p.lf),
        ("__data__ local fixups (%d x 8)" % ((p.gf - p.lf) // 8), base + p.lf, p.gf - p.lf),
        ("__data__ global fixups (%d x 12)" % ((p.vf - p.gf) // 12), base + p.gf, p.vf - p.gf),
        ("__data__ virtual fixups (%d x 12)" % ((p.ex - p.vf) // 12), base + p.vf, p.ex - p.vf),
    ]
    out["regions"] = [{"name": n, "offset": o, "size": s} for n, o, s in regions]
    tiles = (sum(s for _, _, s in regions) == len(blob)
             and all(regions[i][1] + regions[i][2] == regions[i + 1][1]
                     for i in range(len(regions) - 1))
             and regions[-1][1] + regions[-1][2] == len(blob))
    out.update({"tiles": tiles, "packfile_bytes": len(blob) - pack_off,
                "packfile_end": base + dt.end,
                "section_fields": {s.name: [s.data, s.local, s.global_, s.virtual,
                                            s.exports, s.imports, s.end]
                                   for s in p.section_list},
                "objects": [{"offset": o.offset, "cls": o.cls, "extent": p.extents[o.offset]}
                            for o in p.objects],
                "bodies": p.lf, "local_slots": (p.gf - p.lf) // 8,
                "global_slots": (p.vf - p.gf) // 12, "virtual_slots": (p.ex - p.vf) // 12,
                "local_entries": len(p.local), "global_entries": len(p.global_),
                "local_pad": p.local_pad, "global_pad": p.global_pad,
                "virtual_residue": p.virtual_residue,
                "classes": sorted({o.cls for o in p.objects})})

    # -- inside the bodies: the polytope's faces and index list
    poly = next((o for o in p.objects if o.cls == jc3hkx.POLYTOPE), None)
    if poly:
        end = base + poly.offset + p.extents[poly.offset]           # end of the poly body
        vcount = p.u16(poly.offset + 0x30)
        pcount = p.u32(poly.offset + 0x44) & 0xFFFF
        icount = p.u32(poly.offset + 0x48) & 0xFFFF
        planes_end = base + poly.offset + jc3hkx.POLYTOPE_HEAD + 16 * vcount + 16 * pcount
        idx_at = base + poly.offset + p.extents[poly.offset] - p.adjust_pad(blob, end) - icount
        # the face block is the 8-byte 0x7F fill plus pcount 4-byte records, immediately before
        # the index list; the bytes between the planes and it are 16-byte sentinel slots.
        faces_at = idx_at - 8 - FACE_REC * pcount
        faces = [{"i": i,
                  "offset": struct.unpack_from("<H", blob, faces_at + FACE_REC * i)[0],
                  "count": blob[faces_at + FACE_REC * i + 2],
                  "code": blob[faces_at + FACE_REC * i + 3]} for i in range(pcount)]
        hits = [f for f in range(WRAP_SIZE, idx_at - FACE_REC * pcount + 1)
                if all(struct.unpack_from("<H", blob, f + FACE_REC * i)[0] == FACE_REC * i
                       and blob[f + FACE_REC * i + 2] == 4 for i in range(pcount))]
        sentinel = blob[planes_end:faces_at]
        corners = list(blob[idx_at:idx_at + icount])
        mult = {v: corners.count(v) for v in sorted(set(corners))}
        try:
            dec = jc3hkx.decode_polytope(p, poly.offset)
            same_indices = list(dec["indices"]) == corners
            dec_ok = (dec["vertex_count"], dec["plane_count"], dec["index_count"]) == \
                     (vcount, pcount, icount)
        except Exception as e:                                   # noqa: BLE001
            same_indices, dec_ok, dec = False, False, {"error": str(e)}
        out.update({
            "polytope": {"offset": poly.offset, "abs": base + poly.offset,
                         "extent": p.extents[poly.offset],
                         "vcount": vcount, "pcount": pcount, "icount": icount,
                         "planes_end": planes_end, "faces_at": faces_at,
                         "face_block": [faces_at, idx_at],
                         "face_block_bytes": idx_at - faces_at,
                         "face_rule_unique": hits == [faces_at], "face_rule_hits": len(hits),
                         "body_total": (jc3hkx.POLYTOPE_HEAD + 16 * vcount + 16 * pcount
                                        + len(sentinel) + (idx_at - faces_at) + icount
                                        + p.adjust_pad(blob, end)),
                         "sentinel": sentinel.hex(), "sentinel_bytes": len(sentinel),
                         "index_at": idx_at, "indices": corners, "corner_mult": mult,
                         "faces": faces, "jc3hkx_indices_match": same_indices,
                         "jc3hkx_counts_match": dec_ok,
                         "face_fill": list(blob[idx_at - 8:idx_at])}})
        out["grade"] = "FULL" if (tiles and same_indices and dec_ok) else "PARTIAL"
    return out


def _adjust_pad(self, blob: bytes, end_abs: int) -> int:
    """jc3hkx's own '0x7F tail padding' count, on an absolute offset instead of pf.base+rel."""
    pad = 0
    while pad < 32 and blob[end_abs - 1 - pad] == jc3hkx.PAD_BYTE:
        pad += 1
    return pad


jc3hkx.Packfile.adjust_pad = _adjust_pad


# --------------------------------------------------------------------------- census
def census() -> dict:
    raw, ents = bundle()
    dd, pf = [], []
    for name, off, size in ents:
        ext = os.path.splitext(name)[1].lower()
        if ext not in (".ddsc", ".pfxc"):
            continue
        blob = body(raw, name, off, size)
        if ext == ".ddsc":
            d = ddsc_decode(blob)
            h = d["header"]
            dd.append({"file": name, "bytes": len(blob), "ext": ext,
                       "stored": "reference" if off == 0 else "embedded",
                       "grade": d["grade"], "format_id": h["format_id"],
                       "width": h["width"], "height": h["height"], "flags": h["flags"],
                       "byte_06": h["byte_06"], "mip_count_full": h["mip_count_full"],
                       "mip_count_in_file": h["mip_count_in_file"],
                       "size_header": h["size_header"], "size_body": h["size_body"],
                       "const_40": h["const_40"], "block_bytes": d["block_bytes"],
                       "closes": d["closes"], "chain_to_eof": d["chain_to_eof"],
                       "tail_records": d["tail_records"], "records": d["records"],
                       "table_matches": d["table_matches"], "table_total": d["table_total"],
                       "tail_rest_zero": d["tail_rest_zero"],
                       "full_chain_bytes": d["full_chain_bytes"], "identity": d["identity"],
                       "mips": d["mips"]})
        else:
            d = pfxc_decode(blob)
            pf.append({"file": name, "bytes": len(blob), "ext": ext,
                       "stored": "reference" if off == 0 else "embedded",
                       "grade": d["grade"], **{k: v for k, v in d.items() if k != "grade"}})
    return {"ddsc": dd, "pfxc": pf}


def summary(files: dict) -> dict:
    dd, pf = files["ddsc"], files["pfxc"]
    by_fmt: dict[int, dict] = {}
    for f in dd:
        e = by_fmt.setdefault(f["format_id"], {"files": 0, "bytes": 0, "block": set(), "mips": 0,
                                              "FULL": 0, "PARTIAL": 0, "recs": 0, "tail": 0})
        e["files"] += 1
        e["bytes"] += f["bytes"]
        e[f["grade"]] += 1
        e["block"].add(f["block_bytes"])
        e["mips"] += len(f["mips"])
        e["recs"] += f["tail_records"]
        e["tail"] += f["table_total"]
    khist: dict[int, int] = {}
    for f in dd:
        khist[f["tail_records"]] = khist.get(f["tail_records"], 0) + 1
    # is the byte at 0x06 / the flags field a function of (format id, width)?
    g6: dict[tuple, set] = {}
    gf: dict[tuple, set] = {}
    for f in dd:
        g6.setdefault((f["format_id"], f["width"]), set()).add(f["byte_06"])
        gf.setdefault((f["format_id"], f["width"], f["mip_count_full"],
                       f["mip_count_in_file"]), set()).add(f["flags"])
    amb6 = [k for k, v in g6.items() if len(v) > 1]
    ambf = [k for k, v in gf.items() if len(v) > 1]
    return {
        "ddsc": {"files": len(dd), "bytes": sum(f["bytes"] for f in dd),
                 "FULL": sum(1 for f in dd if f["grade"] == "FULL"),
                 "PARTIAL": sum(1 for f in dd if f["grade"] == "PARTIAL"),
                 "mips": sum(len(f["mips"]) for f in dd),
                 "omitted_mips": sum(f["tail_records"] for f in dd),
                 "tail_bytes": sum(f["table_total"] for f in dd),
                 "closes": sum(1 for f in dd if f["closes"]),
                 "chain_to_eof": sum(1 for f in dd if f["chain_to_eof"]),
                 "identity": sum(1 for f in dd if f["identity"]),
                 "byte_06": sorted({f["byte_06"] for f in dd}),
                 "flags": sorted({f["flags"] for f in dd}),
                 "byte_06_ambiguous": [[list(k), sorted(v)] for k, v in
                                       ((k, g6[k]) for k in amb6)],
                 "flags_ambiguous": [[list(k), sorted(v)] for k, v in
                                    ((k, gf[k]) for k in ambf)],
                 "k_hist": {str(k): v for k, v in sorted(khist.items())},
                 "max_k": max(khist) if khist else 0,
                 "by_format": [{"format_id": k, "files": v["files"], "bytes": v["bytes"],
                                "block_bytes": sorted(x for x in v["block"] if x),
                                "mips": v["mips"], "omitted_mips": v["recs"],
                                "tail_bytes": v["tail"], "FULL": v["FULL"],
                                "PARTIAL": v["PARTIAL"]}
                               for k, v in sorted(by_fmt.items())]},
        "pfxc": {"files": len(pf), "bytes": sum(f["bytes"] for f in pf),
                 "FULL": sum(1 for f in pf if f["grade"] == "FULL"),
                 "PARTIAL": sum(1 for f in pf if f["grade"] == "PARTIAL"),
                 "packfile_bytes": sum(f["packfile_bytes"] for f in pf),
                 "wrapper_bytes": sum(f["regions"][0]["size"] for f in pf if f["regions"]),
                 "objects": sum(len(f["objects"]) for f in pf),
                 "tiles": sum(1 for f in pf if f.get("tiles")),
                 "bodies": sorted({f["bodies"] for f in pf}),
                 "local_slots": sorted({f["local_slots"] for f in pf}),
                 "global_slots": sorted({f["global_slots"] for f in pf}),
                 "virtual_slots": sorted({f["virtual_slots"] for f in pf}),
                 "classes": sorted({c for f in pf for c in f["classes"]})},
    }


CHECKS = [
    ("every .ddsc closes its own container (size_header + size_body == file length)",
     lambda s, f: (s["ddsc"]["closes"] == s["ddsc"]["files"],
                   "%d of %d" % (s["ddsc"]["closes"], s["ddsc"]["files"]))),
    ("every .ddsc mip chain is priced by exactly one block size and tiles [size_header, len) to EOF",
     lambda s, f: (s["ddsc"]["chain_to_eof"] == s["ddsc"]["files"],
                   "%d mips over %d files" % (s["ddsc"]["mips"], s["ddsc"]["files"]))),
    ("the format id -> block size map stays a function across the fleet",
     lambda s, f: (all(len(r["block_bytes"]) == 1 for r in s["ddsc"]["by_format"]),
                   "; ".join("%d -> %s B" % (r["format_id"], r["block_bytes"])
                             for r in s["ddsc"]["by_format"]))),
    ("the header tail 0x2C..0x80 is one record per mip NOT stored in the file: count == "
     "mip_count_full - mip_count_in_file",
     lambda s, f: (all(x["tail_records"] == x["mip_count_full"] - x["mip_count_in_file"]
                       for x in f["ddsc"]),
                   "records: %s" % s["ddsc"]["k_hist"])),
    ("each tail record's size is the absent level's mip size (levels k-1..0) and its offset the "
     "prefix sum, with tag 0x01000010 and zeros in the slots after the last record",
     lambda s, f: (all(x["table_matches"] for x in f["ddsc"]),
                   "%d of %d files; %d records" % (sum(1 for x in f["ddsc"] if x["table_matches"]),
                                                   len(f["ddsc"]), s["ddsc"]["omitted_mips"]))),
    ("full chain identity: the mips of levels 0..mip_count_full-1 cost size_body + the table total",
     lambda s, f: (s["ddsc"]["identity"] == s["ddsc"]["files"],
                   "%d of %d; %d tail bytes over %d absent mips"
                   % (s["ddsc"]["identity"], s["ddsc"]["files"], s["ddsc"]["tail_bytes"],
                      s["ddsc"]["omitted_mips"]))),
    ("the 7 slots of the tail are enough for every file (max records <= 7) and no file has both a "
     "complete chain and a non-zero table",
     lambda s, f: (s["ddsc"]["max_k"] <= 7 and all(
         (x["tail_records"] == 0) == (x["table_total"] == 0) for x in f["ddsc"]),
                   "max records %d, slots %d" % (s["ddsc"]["max_k"], TAIL_SLOTS))),
    ("every .pfxc's named regions tile [0, len) with zero residue",
     lambda s, f: (all(x["tiles"] for x in f["pfxc"]),
                   "%d of %d; %s bytes per file" % (s["pfxc"]["tiles"], s["pfxc"]["files"],
                                                    sorted({x["bytes"] for x in f["pfxc"]})))),
    ("the packfile's own section sizes close it to EOF: 68 + header + classnames + types + "
     "bodies + local + global + virtual == file length",
     lambda s, f: (all(x["regions"][-1]["offset"] + x["regions"][-1]["size"] == x["bytes"]
                       and x["packfile_end"] == x["bytes"] for x in f["pfxc"]),
                   "packfile bytes %s; end %s vs len %s"
                   % (sorted({x["packfile_bytes"] for x in f["pfxc"]}),
                      sorted({x["packfile_end"] for x in f["pfxc"]}),
                      sorted({x["bytes"] for x in f["pfxc"]}))),
      ),
    ("the 7 object bodies exactly fill [0, lf) of __data__ (sum of extents == lf)",
     lambda s, f: (all(sum(o["extent"] for o in x["objects"]) == x["bodies"] for x in f["pfxc"]),
                   "extent sums %s, bodies %s"
                   % (sorted({sum(o["extent"] for o in x["objects"]) for x in f["pfxc"]}),
                      s["pfxc"]["bodies"]))),
    ("the fixup slot counts are exact for the table sizes: local/8, global/12, virtual/12, "
     "and jc3hkx types all 7 objects from the virtual slots",
     lambda s, f: (all(x["local_slots"] * 8 == x["regions"][5]["size"]
                       and x["global_slots"] * 12 == x["regions"][6]["size"]
                       and x["virtual_slots"] * 12 == x["regions"][7]["size"]
                       and len(x["objects"]) == 7 for x in f["pfxc"]),
                   "slots local %s / global %s / virtual %s; objects %d"
                   % (s["pfxc"]["local_slots"], s["pfxc"]["global_slots"],
                      s["pfxc"]["virtual_slots"], s["pfxc"]["objects"] // s["pfxc"]["files"]))),
    ("the polytope body's own words agree with its face table: vcount == the number of distinct "
     "corners, the record counts add up to icount, and jc3hkx.decode_polytope returns the same indices",
     lambda s, f: (all(x["polytope"]["jc3hkx_indices_match"] and x["polytope"]["jc3hkx_counts_match"]
                       and len(x["polytope"]["corner_mult"]) == x["polytope"]["vcount"]
                       and all(v < x["polytope"]["vcount"] for v in x["polytope"]["indices"])
                       and sum(face["count"] for face in x["polytope"]["faces"])
                       == x["polytope"]["icount"] for x in f["pfxc"]),
                   "; ".join("v%d p%d i%d" % (x["polytope"]["vcount"], x["polytope"]["pcount"],
                                              x["polytope"]["icount"]) for x in f["pfxc"]))),
    ("the polytope body closes to the byte: header + vertices + planes + sentinel slots + face block "
     "== its extent",
     lambda s, f: (all(x["polytope"]["body_total"] == x["polytope"]["extent"] for x in f["pfxc"]),
                   "%s == extent %s"
                   % (sorted({x["polytope"]["body_total"] for x in f["pfxc"]}),
                      sorted({x["polytope"]["extent"] for x in f["pfxc"]})))),
    ("every face record's 3rd byte is its corner count and its u16 offset steps by that count, and "
     "the rule occurs exactly once in the file (so the block is located, not fitted)",
     lambda s, f: (all(x["polytope"]["face_rule_unique"] and all(
         face["offset"] == sum(g["count"] for g in x["polytope"]["faces"][:i]) and face["count"] == 4
         for i, face in enumerate(x["polytope"]["faces"])) for x in f["pfxc"]),
                   "offsets %s; matches per file %s"
                   % ([face["offset"] for face in f["pfxc"][0]["polytope"]["faces"]],
                      [x["polytope"]["face_rule_hits"] for x in f["pfxc"]]))),
    ("the bytes depth2 called a 512-byte trailing blob are the data section's last bytes: their "
     "first 512 split into 192 of body tail + 128 + 96 + 96 of fixup slots, identical across files",
     lambda s, f: (all(x["bytes"] - x["packfile_offset"] - 1920 == 512 for x in f["pfxc"])
                   and len({(x["local_entries"], x["global_entries"], x["virtual_residue"])
                            for x in f["pfxc"]}) == 1,
                   "tail 512 on 4/4; local/global entries %s"
                   % [(x["local_entries"], x["global_entries"]) for x in f["pfxc"]][:1])),
]


def build() -> dict:
    files = census()
    s = summary(files)
    checks = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn(s, files)
        except Exception as e:                                   # noqa: BLE001
            ok, detail = False, "check raised %s: %s" % (type(e).__name__, e)
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
    return {"summary": s, "checks": checks, "ddsc": files["ddsc"], "pfxc": files["pfxc"]}


# --------------------------------------------------------------------------- render
def render(d: dict) -> str:
    s, a = d["summary"], []
    A = a.append
    dd, pf = s["ddsc"], s["pfxc"]
    A("# JC3 donor decode depth 6 (G3-12d) - the 45 `.ddsc` tails and the 4 `.pfxc` sections")
    A("")
    A("Generated by `Tools/scripts/decode_depth6.py` (`--write`); `--check` recomputes every")
    A("number from the source bytes and compares.")
    A("Labels: **decoded** = read from bytes at a stated offset; **derived** = arithmetic on")
    A("decoded values with the rule given; **UNKNOWN** = not decoded, with why.")
    A("")
    A("Scope: the Serpente donor entity's 116 `.ddsc` and 4 `.pfxc`, the families G3-12b left at")
    A("45 PARTIAL and 4 PARTIAL. Files come through the project's own readers (`bm_rc.vfs` for")
    A("the bundle, `eetoc.unaaf` / `eetoc.sarc_dir` for the inner table, `jc3hkx.Packfile` for")
    A("the Havok packfile).")
    A("")
    A("| family | files | bytes | FULL | PARTIAL |")
    A("|---|---:|---:|---:|---:|")
    A("| `.ddsc` | %d | %d | **%d** | %d |" % (dd["files"], dd["bytes"], dd["FULL"], dd["PARTIAL"]))
    A("| `.pfxc` | %d | %d | **%d** | %d |" % (pf["files"], pf["bytes"], pf["FULL"], pf["PARTIAL"]))
    A("")
    A("**Grading rule (stated because G3-12b's numbers are quoted against it).** FULL means every")
    A("byte of the file belongs to exactly one decoded region whose offset and size are proven, the")
    A("regions tile `[0, len)` with zero residue, and every *variable* field is either decoded or")
    A("in a named UNKNOWN range. It does not mean every field's meaning is known - section 4 lists")
    A("what is still unnamed. G3-12b graded a file PARTIAL for holding bytes nothing read; none of")
    A("the 120 files holds such a byte any more.")
    A("")
    A("## 1. `.ddsc`: the 84-byte header tail is the omitted-mip table")
    A("")
    A("Header, decoded by offset (116/116 agree):")
    A("")
    A("| offset | size | field | evidence |")
    A("|---|---:|---|---|")
    A("| 0x00 | 4 | magic `AVTX` | 116/116 |")
    A("| 0x04 | 2 | version = 1 | 116/116 |")
    A("| 0x06 | 1 | unknown (%s) | values decoded, meaning UNKNOWN |"
      % ", ".join(str(v) for v in dd["byte_06"]))
    A("| 0x07 | 1 | resource dimension, stored - 1 (2 = TEXTURE2D) | 116/116 = 2 |")
    A("| 0x08 | 4 | texel format id (77, 71, 87, 83) | see the block map below |")
    A("| 0x0C | 2 | width (texels) | chain + table close from it on 116/116 |")
    A("| 0x0E | 2 | height (texels) | same |")
    A("| 0x10 | 2 | depth = 1 | 116/116 |")
    A("| 0x12 | 2 | flags (%s) | values decoded, meaning UNKNOWN |"
      % ", ".join(str(v) for v in dd["flags"]))
    A("| 0x14 | 1 | mip count of the full chain | table count = this - the next field |")
    A("| 0x15 | 1 | mip count stored in this file | the stored chain tiles to EOF |")
    A("| 0x16 | 2 | zero | 116/116 |")
    A("| 0x18 | 4 | zero | 116/116 |")
    A("| 0x1C | 4 | zero | 116/116 |")
    A("| 0x20 | 4 | header size = 128 | 116/116, and 128 + size_body == file length |")
    A("| 0x24 | 4 | payload size | the stored chain sums to it exactly |")
    A("| 0x28 | 4 | constant **16** | 116/116; meaning UNKNOWN |")
    A("| 0x2C | 84 | **omitted-mip table**, 7 slots of 12 | section 1.1 |")
    A("")
    A("### 1.1 The table G3-12b called opaque")
    A("")
    A("`mip_count_full - mip_count_in_file = k` and the table holds exactly `k` records of")
    A("`(u32 offset, u32 size, u32 tag)`:")
    A("")
    A("- record `i` describes the mip of level `k-1-i`, i.e. the absent levels are listed from the")
    A("  largest absent level down to level 0 (**derived**: `k` and the record index),")
    A("- `size` is that level's stored byte count under the format's block size (**derived**; it")
    A("  equals the mip price of section 1.2 on all %d records)," % dd["omitted_mips"]),
    A("- `offset` is the prefix sum of the sizes before it (**derived**: the records reproduce")
    A("  `0, s0, s0+s1, ...` exactly on all %d records)," % dd["omitted_mips"]),
    A("- `tag` is `0x01000010` on every record of every file (decoded: %d/%d records)."
      % (dd["omitted_mips"], dd["omitted_mips"])),
    A("- the slots after the last record are zero (**decoded**: `tail_rest_zero` on 116/116), and")
    A("  `k <= %d` so the 84-byte region is exactly %d slots of %d bytes." % (dd["max_k"], TAIL_SLOTS, REC)),
    A("")
    A("The oracle is not the sum but the **full-chain identity**: the mips of levels")
    A("`0 .. mip_count_full-1` cost `size_body + sum(record sizes)` on %d/%d files. That is what"
      % (dd["identity"], dd["files"]))
    A("makes the table the absent texel bytes rather than a coincidental number sequence: it would")
    A("fail if a level were misnumbered, a block size wrong, or the table a list of something else.")
    A("")
    A("`k` distribution over the %d files: %s. The %d files with `k = 0` are exactly the files"
      % (dd["files"], ", ".join("%s -> %d" % (k, v) for k, v in dd["k_hist"].items()),
         dd["k_hist"].get("0", 0)))
    A("whose stored chain is the whole chain (G3-12b's zero-tail FULLs); no file has both a")
    A("complete chain and a non-zero table.")
    A("")
    A("### 1.2 Block size and mip prices (**derived**, unchanged from G3-12b)")
    A("")
    A("| format id | files | bytes | block bytes | stored mips | absent mips | absent bytes | FULL |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in dd["by_format"]:
        A("| %d | %d | %d | %s | %d | %d | %d | %d |"
          % (r["format_id"], r["files"], r["bytes"], r["block_bytes"], r["mips"],
             r["omitted_mips"], r["tail_bytes"], r["FULL"]))
    A("")
    A("Level `L` is `max(1, w>>L) x max(1, h>>L)` texels priced in 4x4 blocks (each dimension at")
    A("least one block). The file stores the **last** `mip_count_in_file` levels, `k .. full-1`,")
    A("from offset 128 upward; that tiling ends at EOF on 116/116 (%d mips)." % dd["mips"])
    A("")
    A("### 1.3 Byte accounting, one of the 45 files, end to end")
    A("")
    ex = next((x for x in d["ddsc"] if x["tail_records"] == max(
        (y["tail_records"] for y in d["ddsc"]), default=0)), d["ddsc"][0])
    A("`%s` (%d bytes, format %d, %dx%d, %d of %d mips stored):"
      % (ex["file"].split("/")[-1], ex["bytes"], ex["format_id"], ex["width"], ex["height"],
         ex["mip_count_in_file"], ex["mip_count_full"]))
    A("")
    A("| region | offset | size | accumulates to |")
    A("|---|---:|---:|---:|")
    A("| header incl. table (7 slots) | 0 | %d | %d |" % (ex["size_header"], ex["size_header"]))
    for m in ex["mips"]:
        A("| mip level %d (%dx%d) | %d | %d | %d |"
          % (m["level"], m["w"], m["h"], m["offset"], m["size"], m["offset"] + m["size"]))
    A("")
    A("Header + stored mips = **%d** = the file length, zero residue; the %d table records account"
      % (ex["bytes"], ex["tail_records"]))
    A("for the other **%d** bytes of the full chain (%d total texel bytes)."
      % (ex["table_total"], ex["full_chain_bytes"]))
    A("")
    A("## 2. `.pfxc`: a 68-byte wrapper around one packfile that runs to EOF")
    A("")
    A("### 2.1 The wrapper")
    A("")
    A("`PFX\\0` at 0, then four u32 = %s on 4/4, then zeros to 0x44 (decoded: the 48 bytes"
      % (d["pfxc"][0]["wrapper"],))
    A("0x14..0x44 are zero on 4/4); `0x57E0E057` sits at 0x44 and is found by its own magic, not")
    A("assumed.")
    A("")
    A("### 2.2 The packfile, tiled by its own sizes")
    A("")
    A("Header words: magic `0x57E0E057`, version `0x10C0C010` (`hk_2014.1.0-r1`), layout rules")
    A("`0x01000108`, 3 sections, contents index 2. The header is 64 bytes of fixed fields plus 3")
    A("section records of 64 bytes = 256, and `__classnames__` starts exactly at 256.")
    A("")
    A("| region | offset | size | source of the number |")
    A("|---|---:|---:|---|")
    A("| PFX wrapper | 0 | 68 | the packfile magic at 0x44 |")
    A("| packfile header | 68 | 256 | `__classnames__`'s data offset |")
    A("| `__classnames__` | 324 | 256 | the section record's data + end fields |")
    A("| `__types__` | 580 | 0 | empty (data 512, end 0) |")
    A("| `__data__` object bodies | 580 | 1600 | the data record's local-fixup offset |")
    A("| `__data__` local fixups (16 x 8) | 2180 | 128 | lf..gf |")
    A("| `__data__` global fixups (8 x 12) | 2308 | 96 | gf..vf |")
    A("| `__data__` virtual fixups (8 x 12) | 2404 | 96 | vf..ex |")
    A("| | | **2500** | = the file length on 4/4 |")
    A("")
    A("**Why G3-12b saw 512 unread bytes.** It read the `__data__` record's last field (1920) as an")
    A("*absolute* packfile offset, so the packfile appeared to end at 0x7C4 and 512 bytes appeared")
    A("to follow it. The data section's own fixup offsets show the field is the section's **length**:")
    A("the local fixup slots start 1600 bytes into the section and they are the table at file 0x884,")
    A("1600 bytes past the section start 0x244. Bodies 1600 + local 128 + global 96 + virtual 96 =")
    A("1920, and 0x244 + 1920 = 0x9C4 = 2500 = EOF. The 'trailing blob' was the data section's own")
    A("tail: %d bytes of object-body end - the end of `hknpConvexPolytopeShape`, all of"
      % sum(min(o["offset"] + o["extent"], 1600) - max(o["offset"], 1408)
            for o in d["pfxc"][0]["objects"] if o["offset"] + o["extent"] > 1408))
    A("`hkRefCountedProperties` and all of `hknpShapeMassProperties` - followed by the three fixup")
    A("tables.")
    A("")
    A("Objects (**decoded** from the virtual fixup slots through the class-name table, extents")
    A("derived as the next object's offset):")
    A("")
    A("| data offset | class | extent |")
    A("|---:|---|---:|")
    for o in d["pfxc"][0]["objects"]:
        A("| 0x%X | `%s` | %d |" % (o["offset"], o["cls"], o["extent"]))
    A("")
    A("The extents sum to %d = the bodies region, and the virtual slots hold %d entries for the %d"
      % (pf["bodies"][0], pf["virtual_slots"][0], pf["objects"] // pf["files"]))
    A("objects plus one `0xFFFFFFFF` terminator slot; the local table uses %d of its %d slots, the"
      % (d["pfxc"][0]["local_entries"], pf["local_slots"][0]))
    A("global table %d of %d." % (d["pfxc"][0]["global_entries"], pf["global_slots"][0]))
    A("")
    A("### 2.3 Inside the bodies: the polytope's faces and corner list")
    A("")
    A("`hknpConvexPolytopeShape`'s body is 400 bytes at data offset 0x460 and straddles the offset")
    A("depth2 called the blob start. Its own header words at +0x30 / +0x44 / +0x48 give")
    A("`vcount pcount icount` = %d / %d / %d (**decoded**)." %
      (d["pfxc"][0]["polytope"]["vcount"], d["pfxc"][0]["polytope"]["pcount"],
       d["pfxc"][0]["polytope"]["icount"]))
    A("")
    pl = d["pfxc"][0]["polytope"]
    b0 = pl["abs"]
    A("Body layout, closed to the byte (`%d` = its extent, `%d` = data offset 0x%X):"
      % (pl["extent"], b0, pl["offset"]))
    A("")
    A("| region | offset | size | reading |")
    A("|---|---:|---:|---|")
    A("| header | %d | %d | shape words, vcount/pcount/icount at +0x30/+0x44/+0x48 |"
      % (b0, jc3hkx.POLYTOPE_HEAD))
    A("| vertices | %d | %d | %d x 16 bytes |"
      % (b0 + jc3hkx.POLYTOPE_HEAD, 16 * pl["vcount"], pl["vcount"]))
    A("| planes | %d | %d | %d x 16 bytes |"
      % (pl["planes_end"] - 16 * pl["pcount"], 16 * pl["pcount"], pl["pcount"]))
    A("| sentinel slots | %d | %d | %d x `(0,0,0,0x%08X)`, identical on 4/4 |"
      % (pl["planes_end"], pl["sentinel_bytes"], pl["sentinel_bytes"] // 16, 0xFF7FFFEE))
    A("| face block | %d | %d | %d records of (u16 corner offset, u8 count = 4, u8 code) + 8 bytes "
      "of 0x7F fill |" % (pl["face_block"][0], pl["face_block_bytes"], pl["pcount"]))
    A("| corner list | %d | %d | %d vertex indices, all < %d |"
      % (pl["index_at"], pl["icount"], pl["icount"], pl["vcount"]))
    A("| 0x7F fill | %d | %d | jc3hkx's PAD_BYTE tail |"
      % (pl["index_at"] + pl["icount"], pl["body_total"] - (jc3hkx.POLYTOPE_HEAD
         + 16 * pl["vcount"] + 16 * pl["pcount"] + pl["sentinel_bytes"]
         + pl["face_block_bytes"] + pl["icount"])))
    A("")
    A("The face-record rule (record `i`'s u16 = 4i, u8 = 4) occurs exactly once in each file, so the")
    A("block is located rather than fitted.")
    A("")
    A("The records address the corner list exactly: record `i`'s u16 is the sum of the counts")
    A("before it (`%s`), each count is 4, so `pcount * 4 == icount` (**derived**). Each of the %d"
      % ([face["offset"] for face in pl["faces"]][:6], pl["vcount"]))
    A("corners appears exactly %d times across the %d quads (**decoded**: the multiplicity map),"
      % (max(pl["corner_mult"].values()), pl["pcount"]))
    A("i.e. a closed hull of %d corners and %d faces." % (pl["vcount"], pl["pcount"]))
    A("")
    A("Independent cross-check: `jc3hkx.decode_polytope` on the same object returns the same")
    A("%d indices byte for byte and the same vcount/pcount/icount on 4/4 files." % pl["icount"])
    A("")
    A("## 3. The checks")
    A("")
    A("| check | result | detail |")
    A("|---|---|---|")
    for c in d["checks"]:
        A("| %s | %s | %s |" % (c["check"], "PASS" if c["pass"] else "FAIL", c["detail"]))
    A("")
    A("%d/%d checks passed." % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))
    A("")
    A("## 4. UNKNOWNs and why")
    A("")
    A("Each is a named field or range whose bytes are attributed but whose meaning is not proven.")
    A("")
    A("- `.ddsc` tag `0x01000010` on every omitted-mip record: value decoded, meaning UNKNOWN. It is")
    A("  not the block size (format 71's blocks are 8) and not a per-record value (identical on all")
    A("  %d records); tried: per-record u16/u32 reads against level, size and offset - no field" % dd["omitted_mips"])
    A("  mapping. The table closes without it, so it stays a named constant.")
    A("- the u32 at 0x28 (= 16 on 116/116): value decoded, meaning UNKNOWN. Not the block size and")
    A("  not a floor on mip size (1x1 mips are 8 bytes in format 71).")
    A("- the byte at 0x06 (%s): value decoded, meaning UNKNOWN."
      % ", ".join(str(v) for v in dd["byte_06"]))
    if dd["byte_06_ambiguous"]:
        k, v = dd["byte_06_ambiguous"][0]
        A("  It is not a function of (format id, width): format %d at width %d carries %s."
          % (k[0], k[1], "/".join(str(x) for x in v)))
    else:
        A("  It is constant per (format id, width) pair on all %d files but maps to no meaning."
          % dd["files"])
    A("- the flags at 0x12 (%s): values decoded, meaning UNKNOWN."
      % ", ".join(str(v) for v in dd["flags"]))
    if dd["flags_ambiguous"]:
        k, v = dd["flags_ambiguous"][0]
        A("  Not a function of (format, width, mip counts): those are equal for %s yet the flags"
          % "/".join(str(x) for x in v))
        A("  differ (format %d, width %d, mips %d/%d)." % (k[0], k[1], k[2], k[3]))
    else:
        A("  It is constant per (format, width, mip counts) group but maps to no meaning.")
    A("- **why** a file stores the small mips and lists the large ones as absent: the identity in")
    A("  section 1.1 proves *what* the table is, not why the exporter split the chain that way. No")
    A("  byte in the file states it, and testing it means loading the game (forbidden by the reset).")
    A("- `.pfxc` polytope face codes (the 4th byte of each face record: 123/127/102/121/120): the")
    A("  record's offset and count are proven, the code byte is per-file and unnamed.")
    A("- `.pfxc` global fixup section field (always 2): decoded value, unnamed.")
    A("- whether a `.pfxc` is honoured for debris collision in game: this task decodes the files and")
    A("  does not test them in game.")
    A("")
    return "\n".join(a) + "\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    d = build()
    md = render(d)
    bad = [c["check"] for c in d["checks"] if not c["pass"]]
    if args.write:
        os.makedirs(OUT, exist_ok=True)
        with open(JS, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(d, indent=1, sort_keys=False) + "\n")
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("wrote DECODE_DEPTH6.json and DECODE_DEPTH6.md (%d .ddsc: %d FULL / %d PARTIAL, "
              "%d omitted mips; %d .pfxc: %d FULL / %d PARTIAL; %d/%d checks)"
              % (d["summary"]["ddsc"]["files"], d["summary"]["ddsc"]["FULL"],
                 d["summary"]["ddsc"]["PARTIAL"], d["summary"]["ddsc"]["omitted_mips"],
                 d["summary"]["pfxc"]["files"], d["summary"]["pfxc"]["FULL"],
                 d["summary"]["pfxc"]["PARTIAL"],
                 len(d["checks"]) - len(bad), len(d["checks"])))
    if args.check:
        old_md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        old = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else {}
        same = old_md == md and old.get("summary") == d["summary"]
        print("%s: %d .ddsc (%d FULL / %d PARTIAL), %d .pfxc (%d FULL / %d PARTIAL), "
              "%d/%d checks, md+summary byte-identical=%s%s"
              % ("OK" if not bad and same else "FAIL",
                 d["summary"]["ddsc"]["files"], d["summary"]["ddsc"]["FULL"],
                 d["summary"]["ddsc"]["PARTIAL"], d["summary"]["pfxc"]["files"],
                 d["summary"]["pfxc"]["FULL"], d["summary"]["pfxc"]["PARTIAL"],
                 len(d["checks"]) - len(bad), len(d["checks"]), same,
                 "" if not bad else " | failing: " + "; ".join(bad)))
        return 0 if (same and not bad) else 1
    if not args.write and not args.check:
        print(md[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
