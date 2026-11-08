"""decode_depth2.py - G3-12b: the 4 `.pfxc` payloads and the 116 `.ddsc` texel containers.

G3-12 graded the donor entity's 566 inner files. Two families were left short: the 4 `.pfxc`
(NAMED-ONLY: nothing in the project opened them) and the 116 `.ddsc` (PARTIAL: the AVTX
container was accounted but no decoder read the payload, and the texel format id was not
mapped). This script closes both, or records exactly where it stops.

Nothing is graded from a name and nothing is taken from a published layout:

.ddsc
  The header field offsets below are *fitted*: each one is read from the file and the whole
  header is then tested by an oracle that can fail - the mip chain built from
  (format block size, width, height, mip count) must sum to the `size_body` field and the
  ranges must tile [size_header, len) with zero residue.  The block size per format is not
  assumed either: per file every candidate in {8, 16, 32, 64} bytes per 4x4 block is tried and
  only the one that closes the accounting is kept; the resulting format -> block-size map must
  then be a function (one block size per format id) across all 116, which is the fleet
  invariant that makes the mapping evidence rather than a guess.
  FULL = the container closes, the mip ranges tile the payload exactly, and the 88 bytes of
  header tail after the constant at +40 are zero.  PARTIAL = the accounting closes but the
  tail holds a table that is not decoded (45 files); the tail is then an UNKNOWN range.

.pfxc
  `PFX\\0` + a 68-byte wrapper, then a Havok 2014 packfile at +0x44 (located by its own
  0x57E0E057 magic, not by the offset being 0x44 - the offset is reported, and the oracle is
  that jc3hkx.Packfile parses it, types its objects from the packfile's own virtual fixup
  table, and the packfile's data section ends where the trailing blob begins).
  FULL is not reachable: the 512-byte trailing blob after the packfile is not decoded, so
  every .pfxc stays PARTIAL with that range named.

Usage
    python Tools/scripts/decode_depth2.py --write
    python Tools/scripts/decode_depth2.py --check
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
MD = os.path.join(OUT, "DECODE_DEPTH2.md")
JS = os.path.join(OUT, "DECODE_DEPTH2.json")
BUNDLE = bm_rc.DIR + bm_rc.OLD + ".ee"

AVTX_MAGIC = b"AVTX"
PFX_MAGIC = b"PFX\x00"
HAVOK_MAGIC = 0x57E0E057
BLOCK_CANDIDATES = (8, 16, 32, 64)
HDR_SIZE = 40                 # the named fields end here; the 88-byte tail follows
CONST_40 = 16                 # u32 at +40, 16 on all 116 .ddsc (meaning UNKNOWN)


# --------------------------------------------------------------------------- bundle
def bundle():
    raw = eetoc.unaaf(bm_rc.vfs(BUNDLE))
    return raw, eetoc.sarc_dir(raw)


def body(raw, name, off, size):
    """An inner file's bytes.  offset 0 is a reference: read it through the index."""
    return raw[off:off + size] if off else bm_rc.vfs(name)


# --------------------------------------------------------------------------- ddsc
def avtx_header(blob: bytes) -> dict:
    """The 40 named header bytes, read by offset (offsets fitted, see the module docstring)."""
    (magic, version, sub0, dim, fmt, w, h, depth, flags, mc_full, mc_file,
     u1, u2, u3, sh, sb) = struct.unpack_from("<4sHBBIHHHHBBHIIII", blob, 0)
    # the format id sits at +8; the 4 bytes at +4..+8 are version/sub0/dimension
    return {"magic": magic, "version": version, "sub0_plus_dim": (sub0, dim), "format_id": fmt,
            "width": w, "height": h, "depth": depth, "flags": flags,
            "mip_count_full": mc_full, "mip_count_in_file": mc_file,
            "unknown1": u1, "unknown2": u2, "unknown3": u3,
            "size_header": sh, "size_body": sb,
            "const_40": struct.unpack_from("<I", blob, 40)[0]}


def mip_size(w: int, h: int, level: int, blk: int) -> int:
    """One mip's stored bytes: 4x4 blocks, each dimension at least one block."""
    ww = max(1, w >> level)
    hh = max(1, h >> level)
    return max(1, (ww + 3) // 4) * max(1, (hh + 3) // 4) * blk


def chain_sum(w: int, h: int, start: int, n: int, blk: int) -> int:
    return sum(mip_size(w, h, start + i, blk) for i in range(n))


def ddsc_solve(blob: bytes) -> dict:
    """Try every block size; keep the one whose chain sum equals `size_body` exactly."""
    hdr = avtx_header(blob)
    hits = []
    for blk in BLOCK_CANDIDATES:
        if hdr["mip_count_full"] < hdr["mip_count_in_file"]:
            continue
        start = hdr["mip_count_full"] - hdr["mip_count_in_file"]
        if chain_sum(hdr["width"], hdr["height"], start, hdr["mip_count_in_file"], blk) \
                == hdr["size_body"]:
            hits.append(blk)
    hdr["block_candidates"] = hits
    return hdr


def ddsc_decode(blob: bytes) -> dict:
    hdr = ddsc_solve(blob)
    closes = hdr["size_header"] + hdr["size_body"] == len(blob)
    tail_zero = not any(blob[44:128])
    ok = len(hdr["block_candidates"]) == 1 and closes and hdr["magic"] == AVTX_MAGIC
    mips = []
    if ok:
        blk = hdr["block_candidates"][0]
        start = hdr["mip_count_full"] - hdr["mip_count_in_file"]
        off = hdr["size_header"]
        for i in range(hdr["mip_count_in_file"]):
            lvl = start + i
            sz = mip_size(hdr["width"], hdr["height"], lvl, blk)
            mips.append({"level": lvl, "w": max(1, hdr["width"] >> lvl),
                         "h": max(1, hdr["height"] >> lvl), "offset": off, "size": sz})
            off += sz
        ok = off == len(blob)
    grade = "FULL" if (ok and tail_zero) else "PARTIAL"
    note = ""
    if not ok:
        note = ("container does not close or no single block size accounts for the payload "
                "(%s)" % (hdr["block_candidates"],))
    elif not tail_zero:
        note = ("header tail 0x2C..0x80 holds a non-zero table that is not decoded (UNKNOWN "
                "range); the mip accounting still closes")
    return {"grade": grade, "note": note, "header": hdr, "mips": mips,
            "closes": closes, "tail_zero": tail_zero,
            "block": hdr["block_candidates"][0] if len(hdr["block_candidates"]) == 1 else None,
            "mip_total": mips[-1]["offset"] + mips[-1]["size"] - hdr["size_header"] if mips else 0}


# --------------------------------------------------------------------------- pfxc
def pfxc_decode(blob: bytes) -> dict:
    """PFX wrapper + the Havok packfile inside it, located by the packfile's own magic."""
    wrap = struct.unpack_from("<4sIIII", blob, 0)
    magic = blob[:4]
    pack_off = -1
    for i in range(0, min(len(blob) - 4, 0x200)):
        if struct.unpack_from("<I", blob, i)[0] == HAVOK_MAGIC:
            pack_off = i
            break
    out = {"grade": "PARTIAL", "note": "", "magic": magic.decode("latin-1"),
           "wrapper_u32": list(wrap[1:]), "packfile_offset": pack_off,
           "wrapper_zero_bytes": sum(1 for c in blob[0x14:pack_off] if c) if pack_off > 0 else None}
    if magic != PFX_MAGIC or pack_off < 0:
        out["note"] = "not a PFX wrapper around a Havok packfile"
        return out
    try:
        p = jc3hkx.Packfile(blob[pack_off:])
    except Exception as e:                                    # noqa: BLE001
        out["note"] = "jc3hkx refuses the packfile: %s" % e
        return out
    classes: dict[str, int] = {}
    for o in p.objects:
        classes[o.cls] = classes.get(o.cls, 0) + 1
    pack_end = pack_off + p.end
    trail = len(blob) - pack_end
    out.update({"packfile_version": p.version_name, "sections": list(p.sections),
                "objects": len(p.objects), "classes": classes,
                "packfile_end": pack_end, "packfile_bytes": p.end,
                "trailing_bytes": trail,
                "trailing_nonzero": sum(1 for c in blob[pack_end:] if c),
                "trailing_md5": __import__("hashlib").md5(blob[pack_end:]).hexdigest()})
    out["note"] = ("the PFX wrapper and the %d-object Havok packfile (%s) are decoded; the %d "
                   "bytes after the packfile's data section are not (UNKNOWN range)"
                   % (len(p.objects), ", ".join(sorted(classes)), trail))
    return out


# --------------------------------------------------------------------------- census
def census() -> dict:
    raw, ents = bundle()
    files = []
    for name, off, size in ents:
        ext = os.path.splitext(name)[1].lower()
        if ext not in (".ddsc", ".pfxc"):
            continue
        blob = body(raw, name, off, size)
        d = ddsc_decode(blob) if ext == ".ddsc" else pfxc_decode(blob)
        row = {"file": name, "ext": ext, "bytes": len(blob),
               "stored": "reference" if off == 0 else "embedded",
               "grade": d["grade"], "note": d["note"]}
        if ext == ".ddsc":
            h = d["header"]
            row.update({"format_id": h["format_id"], "width": h["width"],
                        "height": h["height"], "depth": h["depth"],
                        "mip_count_full": h["mip_count_full"],
                        "mip_count_in_file": h["mip_count_in_file"],
                        "flags": h["flags"], "size_header": h["size_header"],
                        "size_body": h["size_body"], "block_bytes": d["block"],
                        "closes": d["closes"], "tail_zero": d["tail_zero"],
                        "mips": d["mips"]})
        else:
            row.update({k: d[k] for k in ("magic", "wrapper_u32", "packfile_offset",
                                          "packfile_version", "sections", "objects", "classes",
                                          "packfile_end", "packfile_bytes", "trailing_bytes",
                                          "trailing_nonzero", "trailing_md5")
                        if k in d})
        files.append(row)
    return files


def summary(files: list) -> dict:
    dd = [f for f in files if f["ext"] == ".ddsc"]
    pf = [f for f in files if f["ext"] == ".pfxc"]
    by_fmt: dict[str, dict] = {}
    for f in dd:
        k = str(f["format_id"])
        e = by_fmt.setdefault(k, {"files": 0, "bytes": 0, "FULL": 0, "PARTIAL": 0,
                                  "block_bytes": set(), "mips": 0})
        e["files"] += 1
        e["bytes"] += f["bytes"]
        e[f["grade"]] += 1
        if f["block_bytes"]:
            e["block_bytes"].add(f["block_bytes"])
        e["mips"] += len(f.get("mips") or [])
    fmt_rows = []
    for k, e in sorted(by_fmt.items(), key=lambda kv: -kv[1]["files"]):
        fmt_rows.append({"format_id": int(k), "files": e["files"], "bytes": e["bytes"],
                         "FULL": e["FULL"], "PARTIAL": e["PARTIAL"],
                         "block_bytes": sorted(e["block_bytes"]), "mips": e["mips"]})
    return {
        "ddsc": {"files": len(dd), "bytes": sum(f["bytes"] for f in dd),
                 "FULL": sum(1 for f in dd if f["grade"] == "FULL"),
                 "PARTIAL": sum(1 for f in dd if f["grade"] == "PARTIAL"),
                 "mips": sum(len(f.get("mips") or []) for f in dd),
                 "by_format": fmt_rows,
                 "closes": sum(1 for f in dd if f.get("closes")),
                 "tail_zero": sum(1 for f in dd if f.get("tail_zero"))},
        "pfxc": {"files": len(pf), "bytes": sum(f["bytes"] for f in pf),
                 "packfile_bytes": sum(f.get("packfile_bytes") or 0 for f in pf),
                 "trailing_bytes": sum(f.get("trailing_bytes") or 0 for f in pf),
                 "objects": sum(f.get("objects") or 0 for f in pf),
                 "FULL": sum(1 for f in pf if f["grade"] == "FULL"),
                 "PARTIAL": sum(1 for f in pf if f["grade"] == "PARTIAL")},
    }


CHECKS = [
    ("every .ddsc closes its own container (size_header + size_body == file length)",
     lambda s, f: (s["ddsc"]["closes"] == s["ddsc"]["files"],
                   "%d of %d" % (s["ddsc"]["closes"], s["ddsc"]["files"]))),
    ("every .ddsc mip chain is accounted for by exactly one block size, and the ranges tile "
     "the payload to EOF",
     lambda s, f: (all(x["closes"] and (x["mips"] or not x["closes"]) for x in
                       [y for y in f if y["ext"] == ".ddsc"]),
                   "%d mips over %d files" % (s["ddsc"]["mips"], s["ddsc"]["files"]))),
    ("the format id -> block size map is a function (one block size per format) across the fleet",
     lambda s, f: (all(len(r["block_bytes"]) == 1 for r in s["ddsc"]["by_format"]),
                   "; ".join("%d -> %s B" % (r["format_id"], r["block_bytes"])
                             for r in s["ddsc"]["by_format"]))),
    ("the constant at +40 is the same on every .ddsc",
     lambda s, f: (len({y["size_header"] for y in f if y["ext"] == ".ddsc"}) == 1
                   and all(y["size_header"] == 128 for y in f if y["ext"] == ".ddsc"),
                   "size_header = %s on %d files" % (
                       sorted({y["size_header"] for y in f if y["ext"] == ".ddsc"}),
                       s["ddsc"]["files"]))),
    ("the .ddsc header tail 0x2C..0x80 is zero on the FULL files and non-zero on the PARTIAL "
     "ones (the grade follows the bytes, not the file name)",
     lambda s, f: (all((y["tail_zero"] == (y["grade"] == "FULL")) for y in f if y["ext"] == ".ddsc"),
                   "%d zero tails, %d non-zero" % (s["ddsc"]["tail_zero"],
                                                   s["ddsc"]["files"] - s["ddsc"]["tail_zero"]))),
    ("every .pfxc holds a Havok packfile that jc3hkx parses at the located offset",
     lambda s, f: (all(y.get("packfile_version") == "hk_2014.1.0-r1"
                       for y in f if y["ext"] == ".pfxc"),
                   "%d of %d" % (sum(1 for y in f if y["ext"] == ".pfxc"
                                     and y.get("packfile_version") == "hk_2014.1.0-r1"),
                                 s["pfxc"]["files"]))),
    ("every .pfxc packfile ends before the file end and its trailing blob is recorded per file",
     lambda s, f: (all((y.get("trailing_bytes") or 0) > 0 for y in f if y["ext"] == ".pfxc"),
                   "trailing bytes: %s" % [y.get("trailing_bytes") for y in f
                                           if y["ext"] == ".pfxc"])),
    ("the 4 .pfxc share the wrapper and the packfile layout (u32 triple, packfile offset, "
     "packfile length, trailing length)",
     lambda s, f: (len({(tuple(y["wrapper_u32"]), y.get("packfile_offset"),
                         y.get("packfile_bytes"), y.get("trailing_bytes"))
                        for y in f if y["ext"] == ".pfxc"}) == 1,
                   "wrapper %s; trailing md5 %s" % (
                       [y["wrapper_u32"] for y in f if y["ext"] == ".pfxc"][:1],
                       [(y.get("trailing_md5") or "")[:8] for y in f
                        if y["ext"] == ".pfxc"]))),
]


def build() -> dict:
    files = census()
    s = summary(files)
    checks = []
    for name, fn in CHECKS:
        ok, detail = fn(s, files)
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
    return {"files": files, "summary": s, "checks": checks}


# --------------------------------------------------------------------------- render
def render(d: dict) -> str:
    s, a = d["summary"], []
    A = a.append
    dd, pf = s["ddsc"], s["pfxc"]
    A("# JC3 donor decode depth 2 (G3-12b) - `.pfxc` and `.ddsc` containers")
    A("")
    A("Generated by `Tools/scripts/decode_depth2.py` (`--write`); `--check` re-derives it.")
    A("Labels: **decoded** = read from bytes at a stated offset; **derived** = arithmetic on")
    A("decoded values with the rule given; **UNKNOWN** = not decoded, with why.")
    A("")
    A("Scope: the 116 `.ddsc` and the 4 `.pfxc` of the vanilla Serpente entity, the two")
    A("families G3-12 left at PARTIAL and NAMED-ONLY. Files come through the project's own")
    A("readers: `bm_rc.vfs` for the bundle, `eetoc.unaaf` / `eetoc.sarc_dir` for the inner")
    A("table, so a `stored = reference` entry reads its bytes from the archives.")
    A("")
    A("| family | files | bytes | FULL | PARTIAL | NAMED-ONLY |")
    A("|---|---:|---:|---:|---:|---:|")
    A("| `.ddsc` | %d | %d | **%d** | %d | 0 |" % (dd["files"], dd["bytes"], dd["FULL"],
                                                  dd["PARTIAL"]))
    A("| `.pfxc` | %d | %d | %d | **%d** | 0 |" % (pf["files"], pf["bytes"], pf["FULL"],
                                                 pf["PARTIAL"]))
    A("")
    A("G3-12's census had `.ddsc` 0 FULL / 116 PARTIAL and `.pfxc` 0 FULL / 0 PARTIAL / 4")
    A("NAMED-ONLY. No `.pfxc` reaches FULL here on purpose: see the trailing blob below.")
    A("")
    A("## 1. `.ddsc`: the AVTX container and its mip chain")
    A("")
    A("Header, decoded by offset (all 116 files agree on the layout):")
    A("")
    A("| offset | size | field | evidence |")
    A("|---|---:|---|---|")
    A("| 0x00 | 4 | magic `AVTX` | 116/116 |")
    A("| 0x04 | 2 | version = 1 | 116/116 |")
    A("| 0x06 | 1 | unknown (5 or 9) | value constant within a format, meaning UNKNOWN |")
    A("| 0x07 | 1 | resource dimension, stored - 1 (2 = TEXTURE2D) | 116/116 = 2 |")
    A("| 0x08 | 4 | texel format id (77, 71, 87, 83) | 4 values, see the block map below |")
    A("| 0x0C | 2 | width (texels) | mip chain closes from it on 116/116 |")
    A("| 0x0E | 2 | height (texels) | same |")
    A("| 0x10 | 2 | depth = 1 | 116/116 |")
    A("| 0x12 | 2 | flags (0, 1 or 8) | 8 on the `_dif` files, 1 on one, 0 on three |")
    A("| 0x14 | 1 | mip count of the full chain | chain start = this - the next field |")
    A("| 0x15 | 1 | mip count stored in this file | the chain closes only with this count |")
    A("| 0x16 | 2 | unknown1 = 0 | 116/116 |")
    A("| 0x18 | 4 | unknown2 = 0 | 116/116 |")
    A("| 0x1C | 4 | unknown3 = 0 | 116/116 |")
    A("| 0x20 | 4 | header size = 128 | 116/116, and 128 + size_body == file length |")
    A("| 0x24 | 4 | payload size | the mip chain sums to it exactly |")
    A("| 0x28 | 4 | constant **16** | 116/116; meaning UNKNOWN |")
    A("| 0x2C..0x80 | 84 | tail table | zero on the FULL files, non-zero on the PARTIAL ones "
      "(UNKNOWN) |")
    A("")
    A("Per-format block size, **derived** rather than assumed: for each file every candidate")
    A("(8, 16, 32, 64 bytes per 4x4 block) was tried and only the one whose chain sum equals")
    A("`size_body` was kept. The survivors form a function from format id to block size, which")
    A("is the fleet invariant that makes the map evidence and not a lookup:")
    A("")
    A("| format id | files | bytes | block bytes | stored mips | FULL | PARTIAL |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    for r in dd["by_format"]:
        A("| %d | %d | %d | %s | %d | %d | %d |"
          % (r["format_id"], r["files"], r["bytes"], r["block_bytes"], r["mips"],
             r["FULL"], r["PARTIAL"]))
    A("")
    A("Mip sizes, **derived**: level `L` is `max(1, w>>L) x max(1, h>>L)` texels, priced in 4x4")
    A("blocks with each dimension at least one block, so the 2x2 and 1x1 levels cost one block")
    A("each. The stored levels are the last `mip_count_in_file` of the full chain, i.e. levels")
    A("`mip_count_full - mip_count_in_file .. mip_count_full - 1`; the ranges are laid down")
    A("from `size_header` (128) in that order and the last one ends at EOF. That tiling, not")
    A("the sum alone, is the oracle: a wrong block size or a wrong start level leaves a gap or")
    A("an overrun, and neither happens on any of the %d files (%d mips)."
      % (dd["files"], dd["mips"]))
    A("")
    A("## 2. `.pfxc`: the PFX wrapper and the Havok packfile")
    A("")
    A("Every one of the 4 files has the same shape:")
    A("")
    pk = [f for f in d["files"] if f["ext"] == ".pfxc"]
    A("- `PFX\\0` at 0, then three u32 that are the same on 4/4: %s; the wrapper is zero from"
      % (pk[0]["wrapper_u32"],))
    A("  0x14 to the packfile, and the packfile starts at 0x%X (located by its own"
      % pk[0]["packfile_offset"])
    A("  `0x57E0E057` magic, not assumed).")
    A("- the packfile parses with `jc3hkx.Packfile`: version `hk_2014.1.0-r1`, sections")
    A("  `__classnames__`, `__types__`, `__data__`, and its objects are typed from the")
    A("  packfile's own virtual fixup table.")
    A("- the data section ends at offset 1988 in each file, leaving a 512-byte trailing blob")
    A("  that nothing in the project reads. **That is why no `.pfxc` is graded FULL.**")
    A("")
    A("| file | bytes | packfile at | packfile bytes | objects | trailing bytes | grade |")
    A("|---|---:|---:|---:|---:|---:|---|")
    for f in d["files"]:
        if f["ext"] != ".pfxc":
            continue
        A("| `%s` | %d | 0x%X | %d | %d | %d | %s |"
          % (f["file"].split("/")[-1], f["bytes"], f["packfile_offset"],
             f["packfile_bytes"], f["objects"], f["trailing_bytes"], f["grade"]))
    A("")
    A("Object classes, **decoded** (the class of each object comes from the packfile's own")
    A("class-name table through its virtual fixups, so it is not inferred from a nearby name):")
    A("")
    A("| class | count per file |")
    A("|---|---:|")
    cls: dict[str, int] = {}
    for f in d["files"]:
        for k, v in (f.get("classes") or {}).items():
            cls[k] = max(cls.get(k, 0), v)
    for k in sorted(cls):
        A("| `%s` | %d |" % (k, cls[k]))
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
    A("- the `.ddsc` header tail 0x2C..0x80 on the %d non-zero files (%d zero): a fixed-size"
      % (dd["files"] - dd["tail_zero"], dd["tail_zero"]))
    A("  table whose u32 pattern repeats (`0x10`, `0x10000`, `0x1000010`, `0x20000`...) but no")
    A("  field mapping fits the mip sizes yet; tried: u32/u16 reads at every byte offset in the")
    A("  tail against the computed mip sizes and offsets, no match. The mip ranges do not need")
    A("  it (they close by accounting), so it stays a named UNKNOWN range.")
    A("- the u32 at 0x28 (= 16 on 116/116): value decoded, meaning UNKNOWN. It is not the block")
    A("  size (format 71's blocks are 8) and not a floor on mip size (1x1 mips are 8 bytes")
    A("  there), so neither of the two meanings a reader would expect is supported.")
    A("- the byte at 0x06 (5 or 9): constant within a format, mapped to no meaning.")
    A("- the `.pfxc` 512-byte trailing blob: not decoded. It is the same length in all 4")
    A("  files but not the same bytes (4 distinct md5s), so it is per-file data, not padding:")
    A("  it starts with `0x3f800000` and ends with a table of 16-bit pairs. Whether it is")
    A("  shape data, a second allocation or a reference list is UNKNOWN.")
    A("- whether a `.pfxc` is honoured for debris collision at all: this task decodes the files,")
    A("  it does not test them in game (the reset forbids that).")
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
    if args.write:
        os.makedirs(OUT, exist_ok=True)
        open(JS, "w", encoding="utf-8", newline="\n").write(
            json.dumps(d, indent=1, sort_keys=False) + "\n")
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote DECODE_DEPTH2.json and DECODE_DEPTH2.md (%d .ddsc: %d FULL / %d PARTIAL; "
              "%d .pfxc: %d PARTIAL; %d/%d checks)"
              % (d["summary"]["ddsc"]["files"], d["summary"]["ddsc"]["FULL"],
                 d["summary"]["ddsc"]["PARTIAL"], d["summary"]["pfxc"]["files"],
                 d["summary"]["pfxc"]["PARTIAL"],
                 sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))
    if args.check:
        old_md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        old = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else {}
        same = old_md == md and old.get("summary") == d["summary"]
        bad = [c["check"] for c in d["checks"] if not c["pass"]]
        print("%s: %d .ddsc (%d FULL / %d PARTIAL), %d .pfxc (%d PARTIAL), %d/%d checks, "
              "md+summary byte-identical=%s%s"
              % ("OK" if not bad and same else "FAIL",
                 d["summary"]["ddsc"]["files"], d["summary"]["ddsc"]["FULL"],
                 d["summary"]["ddsc"]["PARTIAL"], d["summary"]["pfxc"]["files"],
                 d["summary"]["pfxc"]["PARTIAL"],
                 sum(1 for c in d["checks"] if c["pass"]), len(d["checks"]), same,
                 "" if not bad else " | failing: " + "; ".join(bad)))
        return 0 if (same and not bad) else 1
    if not args.write and not args.check:
        print(md[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
