"""grab_shader_combine.py - G3-04d: does the cooked shader cache carry the colour combine rule?

The material graph is stripped (G3-04b: 944 FunctionExpressions slots, all zero) but the
compiled shaders survive in two cooked caches under the install:

    BmGame/CookedPCConsole/CombinedShaderCache-PC-D3D-SM5.upk   21268515 B, one ShaderCache export
    BmGame/CookedPCConsole/GlobalShaderCache-PC-D3D-SM5.bin     12873519 B, BMSG container

This script decodes what those two files actually carry, and separates three questions that
are easy to conflate:

  (a) Is there DXBC bytecode, and does every container frame exactly?      -> decoded here
  (b) Does any blob name its constants (RDEF)?                            -> decoded here: no
  (c) Is `Batmobile_Worn`'s parameter list in the cache, with values?     -> decoded here: yes

What the bytes say (see the generated .md for the tables):

  `.upk`  one export `CacheObject` (class `ShaderCache`), 155333378 B, in two regions:
            [0x19d .. 0x8ab38bb]  38,201 DXBC containers, each preceded by its own u32 size
            [0x8bc1.. ]           per-material records: FString name, 16-byte GUID, 16 zero
                                  bytes, u32 count, then `count` uniform-expression entries
          An entry is `FName class, FName parameter, value`, the value's width set by the
          class (`FMaterialUniformExpressionVectorParameter` = 16 B of RGBA float).  The
          Batmobile body record (`Batmobile_Worn`) carries 14 entries and its values
          reproduce the material's authored vector defaults exactly - `Material1_Basecolour`
          [0.623595, 0.39245, 0.329779, 1], `Material2_BaseColour` / `Material3_BaseColour`
          [0.423977, 0.609159, 0.752809, 1], `Rain_Size_Multiplier` [1, 2, 0, 1] - which is
          the oracle that the record is this material's uniform list and not a lookalike.

  `.bin`  `BMSG` + version 863, a shader-type name table from 0x1C (`FResolveVertexShader`,
          ...), then 2,098 DXBC containers from 0x80, tiled to EOF.

  The gap, stated exactly: every blob in both caches holds only ISGN / OSGN / SHEX.  There is
  **no RDEF chunk anywhere** (0 in 38,201 + 0 in 2,098), so the bytecode carries no constant
  name and no cb-slot binding, and none of the parameter names (`Material0_BaseColour`,
  `Diffuse_Adjust`, ...) occurs in the blob region at all.  The material record carries the
  uniform list but no shader index or offset into the blob region, and `Batmobile_Worn`'s GUID
  occurs only in the record region (5 sites, all in the 0.9 MB record area), never beside a
  blob.  So the material -> pixel-shader binding is not in these files in a form this script
  can read: the cache holds the shader and the uniform list, not the map between them.
  Naming a constant-buffer slot from here would be a guess, so this script does not make one;
  the report names where the binding would have to be found.

Usage
    python Tools/scripts/grab_shader_combine.py --write
    python Tools/scripts/grab_shader_combine.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read  # noqa: E402

INSTALL = "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
UPK = INSTALL + "/CombinedShaderCache-PC-D3D-SM5.upk"
BIN = INSTALL + "/GlobalShaderCache-PC-D3D-SM5.bin"
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "SHADER_COMBINE.md")
JS = os.path.join(OUT, "SHADER_COMBINE.json")
PARAMS_JSON = os.path.join(OUT, "COLOUR_PARAMS.json")

DXBC_MAGIC = b"DXBC"
BMSG_MAGIC = b"BMSG"
KNOWN_CHUNKS = {b"RDEF", b"ISGN", b"OSGN", b"SHEX", b"STAT", b"SPDB", b"IFCE", b"SFI0",
                b"SDBG", b"ILDB", b"PSG1", b"PCSG", b"RDAT", b"RTS0", b"ISG1", b"OSG1",
                b"OSG5", b"HASH", b"DXIL", b"VERS"}
MATERIAL = "Batmobile_Worn"

# Class FName -> value width.  Only the classes that occur in the Batmobile record are listed;
# anything else stops the walk and is reported, rather than guessed.
VALUE_WIDTH = {
    "FMaterialUniformExpressionVectorParameter": 16,
    "FMaterialUniformExpressionScalarParameter": 4,
    "FMaterialUniformExpressionTextureParameter": 4,
    "FMaterialUniformExpressionTexture": 4,
    "FMaterialUniformExpressionStaticSwitchParameter": 4,
    "FMaterialUniformExpressionStaticSwitch": 4,
}
# Values G3-04c decoded for the chain material's own vector defaults (COLOUR_PARAMS.md rows
# 51-68, `StructProperty:DefaultValue @0xcc`).  Used as the cross-check on this record.
EXPECTED = {
    "Material1_Basecolour": [0.623595, 0.39245, 0.329779, 1.0],
    "Material2_BaseColour": [0.423977, 0.609159, 0.752809, 1.0],
    "Material3_BaseColour": [0.423977, 0.609159, 0.752809, 1.0],
    "Rain_Size_Multiplier": [1.0, 2.0, 0.0, 1.0],
    "Material3_Anisotropic_thin_Colour": [0.674157, 0.647211, 0.375439, 1.0],
    "Batman_Rain_Direction": [0.0, 0.0, -1.0, 0.0],
    "Damage_Chapter": [0.0, 0.0, 0.0, 0.0],
}
TOL = 1e-4


# --------------------------------------------------------------------------- upk
def shader_cache():
    p = upk_read.Package(UPK)
    return p, p.data(1)


def dxbc_census(d: bytes) -> dict:
    """Every DXBC container, framed by its own `total` field and chunk offset table."""
    offs = [m.start() for m in re.finditer(re.escape(DXBC_MAGIC), d)]
    blobs, bad = [], []
    for o in offs:
        try:
            unk, total, nch = struct.unpack_from("<III", d, o + 20)
            if not (0 < nch <= 16 and 32 + 4 * nch <= total <= len(d) - o):
                bad.append({"offset": o, "why": "header implausible"})
                continue
            table = struct.unpack_from("<%dI" % nch, d, o + 32)
            tags, sum_chunks, ok = [], 0, True
            for rel in table:
                q = o + rel
                tag, size = struct.unpack_from("<4sI", d, q)
                if tag not in KNOWN_CHUNKS:
                    ok = False
                    tags.append({"tag": tag.decode("latin-1", "replace"), "size": size,
                                 "known": False})
                    continue
                tags.append({"tag": tag.decode("latin-1"), "size": size, "known": True})
                sum_chunks += 8 + size
            if not ok:
                bad.append({"offset": o, "why": "unknown chunk tag"})
                continue
            size_word = struct.unpack_from("<I", d, o - 6)[0] if o >= 6 else None
            blobs.append({"offset": o, "total": total, "chunks": tags,
                          "chunk_bytes": sum_chunks, "size_word_at_minus_6": size_word,
                          "end": o + total})
        except struct.error:
            bad.append({"offset": o, "why": "truncated"})
    # a blob is a pixel shader candidate when it declares a colour output slot
    ps = [b for b in blobs if any(c["tag"] == "OSGN" and c["known"] for c in b["chunks"])]
    gaps = [blobs[i + 1]["offset"] - blobs[i]["end"] for i in range(len(blobs) - 1)]
    return {
        "starts": {b["offset"] for b in blobs},
        "gaps": {"min": min(gaps) if gaps else None, "max": max(gaps) if gaps else None,
                 "distinct": len(set(gaps))},
        "overlaps": sum(1 for g in gaps if g < 0),
        "magic_positions": len(offs),
        "blobs": len(blobs),
        "bad": bad[:20],
        "bad_count": len(bad),
        "first": blobs[0]["offset"] if blobs else None,
        "last_end": max((b["end"] for b in blobs), default=None),
        "chunk_tag_hist": _chunk_hist(blobs),
        "with_rdef": sum(1 for b in blobs if any(c["tag"] == "RDEF" for c in b["chunks"])),
        "with_shex": sum(1 for b in blobs if any(c["tag"] == "SHEX" for c in b["chunks"])),
        "with_osgn": len(ps),
        "size_word_matches": sum(1 for b in blobs
                                 if b["size_word_at_minus_6"] == b["total"]),
        "containers": blobs[:8],
    }


def _chunk_hist(blobs: list) -> dict:
    h: dict = {}
    for b in blobs:
        for c in b["chunks"]:
            h[c["tag"]] = h.get(c["tag"], 0) + 1
    return dict(sorted(h.items(), key=lambda kv: -kv[1]))


def bin_census(b: bytes) -> dict:
    version, a, bb, cc, dd = struct.unpack_from("<5I", b, 4)
    # the type-name table: FString-ish NUL-terminated ASCII runs before the first blob
    first = b.find(DXBC_MAGIC)
    head = b[:first]
    names = re.findall(rb"[A-Za-z][A-Za-z0-9_]{6,63}\x00", head)
    c = dxbc_census(b)
    c.update({"magic": b[:4].decode("latin-1"), "version": version, "hdr_u32": [a, bb, cc, dd],
              "first_blob": first, "header_bytes": first,
              "type_names": [n[:-1].decode("latin-1") for n in names[:40]],
              "type_name_count": len(names)})
    return c


# --------------------------------------------------------------------------- records
def record_candidates(d: bytes, start: int) -> list:
    """Positions that look like `int32 len, name, NUL` - matched in C, not byte by byte."""
    pat = re.compile(rb"[\x01-\xc8]\x00\x00\x00[A-Za-z][A-Za-z0-9_ .]{1,60}\x00")
    return [m.start() for m in pat.finditer(d, start)]


def record_walk(d: bytes, p) -> dict:
    """The per-material record region: FString name, GUID, 16 zero bytes, u32 count, entries."""
    blobs = dxbc_census(d)
    start = blobs["last_end"] if blobs["last_end"] else 0
    recs, errors = [], []
    for o in record_candidates(d, start):
        n = struct.unpack_from("<i", d, o)[0]
        raw = d[o + 4:o + 4 + n]
        if not raw.endswith(b"\x00") or not all(32 <= c < 127 or c == 0 for c in raw):
            continue
        name = raw.split(b"\x00")[0].decode("latin-1")
        # The record stores the material name as a raw FString, NOT as a name-table index:
        # only one name in this package's table contains "batmobile" at all.  Structure, not
        # table membership, is the filter (GUID + 16 zero bytes + a plausible count below).
        if any(r["offset"] == o for r in recs):
            continue
        q = o + 4 + n
        guid = d[q:q + 16]
        q += 16
        pad = d[q:q + 16]
        q += 16
        cnt = struct.unpack_from("<I", d, q)[0]
        q += 4
        entries, ok = [], True
        for i in range(cnt):
            if q + 16 > len(d):
                ok = False
                break
            ci, _cn = struct.unpack_from("<II", d, q)
            pi, _pn = struct.unpack_from("<II", d, q + 8)
            q += 16
            cls = p.names[ci] if ci < len(p.names) else None
            par = p.names[pi] if pi < len(p.names) else None
            w = VALUE_WIDTH.get(cls or "")
            if w is None:
                ok = False
                entries.append({"i": i, "class": cls, "parameter": par, "value": None,
                                "why": "value width UNKNOWN for this class"})
                break
            if q + w > len(d):
                ok = False
                break
            vals = list(struct.unpack_from("<%df" % (w // 4), d, q))
            q += w
            entries.append({"i": i, "class": cls, "parameter": par,
                            "value": [round(v, 6) for v in vals], "raw": d[q - w:q].hex()})
        if not ok or not (0 < cnt <= 64) or q > len(d):
            continue
        blob_starts = blobs["starts"]
        rec = {"offset": o, "name": name, "guid": guid.hex(), "pad_zero": not any(pad),
               "count": cnt, "entries": entries, "walk_ok": ok,
               "end": q, "consumed": q - o,
               "words_equal_blob_offset": sum(
                   1 for k in range(o, q - 3, 4)
                   if struct.unpack_from("<I", d, k)[0] in blob_starts)}
        recs.append(rec)
    return {"region_start": start, "records": recs, "count": len(recs),
            "errors": errors, "region_bytes": len(d) - (start or 0)}


def list_at(d: bytes, p, o: int) -> dict:
    """A uniform-expression list at an offset: u32 count, then count entries."""
    cnt = struct.unpack_from("<I", d, o)[0]
    q, ents, ok, why = o + 4, [], True, None
    for i in range(cnt):
        if q + 16 > len(d):
            ok, why = False, "truncated"
            break
        ci, _ = struct.unpack_from("<II", d, q)
        pi, _ = struct.unpack_from("<II", d, q + 8)
        q += 16
        cls = p.names[ci] if ci < len(p.names) else None
        par = p.names[pi] if pi < len(p.names) else None
        w = VALUE_WIDTH.get(cls or "")
        if w is None or q + w > len(d):
            ok, why = False, "value width UNKNOWN for class %r" % cls
            break
        vals = list(struct.unpack_from("<%df" % (w // 4), d, q))
        q += w
        ents.append({"i": i, "class": cls, "parameter": par,
                     "value": [round(v, 6) for v in vals]})
    return {"offset": o, "count": cnt, "entries": ents, "ok": ok, "stop_reason": why,
            "parsed": len(ents), "end": q}


def compare_vectors(entries: list) -> dict:
    """Cross-check the record's vector values against the defaults G3-04c decoded."""
    got, checked, mismatch = {}, 0, []
    for e in entries:
        if e.get("value") and e.get("parameter") in EXPECTED:
            want = EXPECTED[e["parameter"]]
            got[e["parameter"]] = e["value"]
            checked += 1
            if len(e["value"]) != len(want) or any(abs(a - b) > TOL
                                                   for a, b in zip(e["value"], want)):
                mismatch.append({"parameter": e["parameter"], "record": e["value"],
                                 "decoded": want})
    return {"checked": checked, "parameters": sorted(got), "mismatch": mismatch,
            "values": got}


def name_leak(d: bytes, blob_end: int) -> dict:
    """Do the parameter names appear anywhere in the bytecode region?  (They must not.)"""
    region = d[:blob_end]
    probes = ["Material0_BaseColour", "Diffuse_Adjust", "Material1_Basecolour",
              "Material2_BaseColour", "Batmobile_Worn"]
    hits = {p: region.count(p.encode()) for p in probes}
    return {"probes": hits, "total": sum(hits.values()), "blob_region_bytes": blob_end}


def guid_sites(d: bytes, guid: bytes, blob_end: int) -> dict:
    offs = [m.start() for m in re.finditer(re.escape(guid), d)]
    return {"count": len(offs),
            "in_blob_region": sum(1 for o in offs if o < blob_end),
            "offsets": [hex(o) for o in offs[:10]]}


# --------------------------------------------------------------------------- build
def build() -> dict:
    p, d = shader_cache()
    upk = dxbc_census(d)
    recs = record_walk(d, p)
    body = next((r for r in recs["records"] if r["name"] == MATERIAL and r["walk_ok"]), None)
    body2 = next((r for r in recs["records"] if r["name"] == MATERIAL
                  and r is not body), None)
    cross = compare_vectors(body["entries"]) if body else {"checked": 0, "mismatch": [],
                                                           "parameters": [], "values": {}}
    leak = name_leak(d, upk["last_end"] or 0)
    guid = guid_sites(d, bytes.fromhex(body["guid"]), upk["last_end"] or 0) if body else {}
    region = d[recs["region_start"]:]
    mat_sites = [recs["region_start"] + m.start()
                 for m in re.finditer(re.escape(MATERIAL.encode()), region)]
    mat_recs = [r for r in recs["records"] if r["name"] == MATERIAL]
    trailing = list_at(d, p, body["end"]) if body else None
    if trailing:
        blob_starts = set(dxbc_census(d)["starts"])
        trailing["blob_words"] = sum(
            1 for k in range(trailing["offset"], trailing["end"] - 3, 4)
            if struct.unpack_from("<I", d, k)[0] in blob_starts)
    nxt = min((r["offset"] for r in recs["records"] if body and r["offset"] > body["end"]),
              default=None)
    binb = open(BIN, "rb").read()
    b = bin_census(binb)

    checks = [
        ("the .upk holds one ShaderCache export",
         len(p.exports) == 1 and p.object_class(1) == "ShaderCache",
         "%d exports, class %r, %d B" % (len(p.exports), p.object_class(1), len(d))),
        ("every DXBC container in the .upk frames from its own header",
         upk["bad_count"] == 0 and upk["blobs"] == upk["magic_positions"],
         "%d magic, %d parsed, %d rejected" % (upk["magic_positions"], upk["blobs"],
                                               upk["bad_count"])),
        ("no two containers overlap and the run is strictly increasing",
         upk["overlaps"] == 0,
         "%d containers, gaps between them min %d / max %d, %d distinct gap lengths "
         "(so the framing between blobs is not decoded - reported, not assumed)"
         % (upk["blobs"], upk["gaps"]["min"], upk["gaps"]["max"], upk["gaps"]["distinct"])),
        ("the containers are bytecode only: ISGN/OSGN/SHEX, and no RDEF anywhere",
         upk["with_rdef"] == 0 and b["with_rdef"] == 0 and upk["with_shex"] > 1000,
         ".upk RDEF %d of %d, .bin RDEF %d of %d; chunk tags %s"
         % (upk["with_rdef"], upk["blobs"], b["with_rdef"], b["blobs"],
            ",".join(upk["chunk_tag_hist"]))),
        ("no parameter name and no material name occurs in the bytecode region",
         leak["total"] == 0,
         "%d B region, hits %s" % (leak["blob_region_bytes"], leak["probes"])),
        ("the .bin parses as BMSG with a type-name table before its first blob",
         b["magic"] == "BMSG" and b["type_name_count"] >= 1 and b["first_blob"] == 0x80,
         "version %d, %d type names, %d blobs, first at %#x"
         % (b["version"], b["type_name_count"], b["blobs"], b["first_blob"])),
        ("the material record region parses to its own end without error",
         recs["count"] > 0 and all(r["walk_ok"] for r in recs["records"]),
         "%d records, %d B, %d unparsed"
         % (recs["count"], recs["region_bytes"],
            sum(1 for r in recs["records"] if not r["walk_ok"]))),
        ("the Batmobile body material is present with its uniform list",
         body is not None and body["count"] == 14,
         "%s at %#x, %d entries, guid %s"
         % (MATERIAL, body["offset"], body["count"], body["guid"]) if body else "absent"),
        ("that record's vector values reproduce the defaults G3-04c decoded",
         bool(body) and cross["checked"] >= 5 and not cross["mismatch"],
         "%d parameters cross-checked, %d mismatches: %s"
         % (cross["checked"], len(cross["mismatch"]), cross["parameters"])),
        ("what follows the record is a second uniform list, not a shader index",
         bool(trailing) and trailing["count"] > 0 and trailing["parsed"] > 0
         and trailing["blob_words"] == 0,
         "second list at %#x: %d entries, %d parsed (%s), %d words equal to a blob start"
         % (trailing["offset"], trailing["count"], trailing["parsed"],
            trailing["stop_reason"] or "complete", trailing["blob_words"])
         if trailing else "none"),
        ("the material is named at %d sites in the record region but only one carries a "
         "uniform list" % len(mat_sites),
         len(mat_sites) >= 2 and len(mat_recs) == 1,
         "name sites %s; parsed uniform records for it: %d"
         % ([hex(o) for o in mat_sites], len(mat_recs))),
        ("the material's GUID never occurs in the bytecode region",
         bool(body) and guid["in_blob_region"] == 0,
         "guid at %s; %d of them before the record region"
         % (guid.get("offsets"), guid.get("in_blob_region"))),
    ]

    return {
        "task": "G3-04d - shader cache: is the colour combine rule in the cooked DXBC?",
        "inputs": {"upk": UPK, "upk_bytes": os.path.getsize(UPK),
                   "upk_sha1": hashlib.sha1(open(UPK, "rb").read()).hexdigest()[:16],
                   "bin": BIN, "bin_bytes": len(binb),
                   "bin_sha1": hashlib.sha1(binb).hexdigest()[:16],
                   "material": MATERIAL},
        "upk": {"export_bytes": len(d), "blobs": upk["blobs"],
                "blob_region": [upk["first"], upk["last_end"]],
                "chunk_tags": upk["chunk_tag_hist"], "with_rdef": upk["with_rdef"],
                "with_osgn": upk["with_osgn"], "with_shex": upk["with_shex"],
                "size_word_matches": upk["size_word_matches"],
                "containers": upk["containers"], "bad": upk["bad"]},
        "bin": {"version": b["version"], "blobs": b["blobs"], "with_rdef": b["with_rdef"],
                "chunk_tags": b["chunk_tag_hist"], "type_names": b["type_names"],
                "type_name_count": b["type_name_count"], "first_blob": b["first_blob"],
                "header_bytes": b["header_bytes"]},
        "records": {"region_start": recs["region_start"], "count": recs["count"],
                    "region_bytes": recs["region_bytes"],
                    "material": body, "material_second": body2,
                    "trailing_list": trailing,
                    "walk_errors": [r["name"] for r in recs["records"] if not r["walk_ok"]]},
        "cross_check": cross,
        "name_leak": leak,
        "guid_sites": guid,
        "verdict": {
            "bytecode_present": True,
            "reflection_present": False,
            "uniform_list_present": bool(body),
            "material_to_blob_binding": "UNKNOWN: no RDEF, no name in the blob region, "
                                        "no blob offset in the record, GUID absent from the "
                                        "blob region",
            "combine_rule": "UNKNOWN: the PS bytecode is present but unnamed; the uniform "
                            "list is present but unbound",
        },
        "checks": [{"check": n, "pass": bool(ok), "detail": d2} for n, ok, d2 in checks],
    }


# --------------------------------------------------------------------------- render
def render(d: dict) -> str:
    a = []
    A = a.append
    A("# Batmobile colour: what the cooked shader caches carry (G3-04d)")
    A("")
    A("Generated by `Tools/scripts/grab_shader_combine.py` (`--write`); `--check` recomputes")
    A("every number from the install files and compares.  Labels: **decoded** = read from")
    A("bytes at a stated offset; **derived** = arithmetic on decoded values; **UNKNOWN** =")
    A("not in the files, with where it would be.")
    A("")
    A("Inputs (read-only):")
    A("")
    A("| file | bytes | sha1[:16] |")
    A("|---|---:|---|")
    A("| `%s` | %d | `%s` |" % (d["inputs"]["upk"], d["inputs"]["upk_bytes"],
                                 d["inputs"]["upk_sha1"]))
    A("| `%s` | %d | `%s` |" % (d["inputs"]["bin"], d["inputs"]["bin_bytes"],
                                 d["inputs"]["bin_sha1"]))
    A("")
    A("## 1. The `.upk` shader cache")
    A("")
    u = d["upk"]
    A("One export, class `ShaderCache`, %d B of payload in two regions:" % u["export_bytes"])
    A("")
    A("| region | offsets | contents |")
    A("|---|---|---|")
    A("| shader bytecode | %#x .. %#x | **%d DXBC containers** |"
      % (u["blob_region"][0], u["blob_region"][1], u["blobs"]))
    A("| material records | %#x .. end | %d per-material uniform lists |"
      % (d["records"]["region_start"], d["records"]["count"]))
    A("")
    A("Every container frames from its own header: magic, 16-byte checksum, u32 1, u32 total,")
    A("u32 chunk count, a chunk-offset table of that count, then the chunks.  The u32 six")
    A("bytes before each magic equals that container's own `total` (%d/%d), so the region is"
      % (u["size_word_matches"], u["blobs"]))
    A("a run of size-prefixed blobs rather than a coincidental byte pattern.")
    A("")
    A("Chunk tags across all %d containers:" % u["blobs"])
    A("")
    A("| tag | count |")
    A("|---|---:|")
    for k, v in u["chunk_tags"].items():
        A("| `%s` | %d |" % (k, v))
    A("")
    A("**There is no `RDEF` chunk: %d of %d.**  `RDEF` is the chunk that names constants and"
      % (u["with_rdef"], u["blobs"]))
    A("their constant-buffer slots; without it the bytecode reads `cb0[..]` by number only.")
    A("")
    A("## 2. The `.bin` global cache")
    A("")
    b = d["bin"]
    A("`%s` version %d, header %d B, then **%d DXBC containers** from %#x, tiled to EOF."
      % ("BMSG", b["version"], b["header_bytes"], b["blobs"], b["first_blob"]))
    A("The header carries a shader-type name table; its first %d entries:" % len(b["type_names"]))
    A("")
    A("    " + ", ".join(b["type_names"]))
    A("")
    A("Its chunk tags are the same set, and again `RDEF` count is **%d**." % b["with_rdef"])
    A("")
    A("## 3. The material record (decoded)")
    A("")
    m = d["records"]["material"]
    if m:
        A("`%s` at **%#x**, GUID `%s`, %d zero pad bytes, **%d uniform-expression entries**."
          % (m["name"], m["offset"], m["guid"], 16 if m["pad_zero"] else 0, m["count"]))
        A("Each entry is `FName class, FName parameter, value`; the class fixes the value")
        A("width (`FMaterialUniformExpressionVectorParameter` = 16 B RGBA float).")
        A("")
        A("| # | class | parameter | value |")
        A("|---:|---|---|---|")
        for e in m["entries"]:
            A("| %d | `%s` | `%s` | %s |"
              % (e["i"] + 1, e["class"], e["parameter"],
                 e["value"] if e.get("value") is not None else "UNKNOWN (%s)" % e.get("why")))
        A("")
        A("### Why this record is `Batmobile_Worn`'s uniform list")
        A("")
        c = d["cross_check"]
        A("The values reproduce G3-04c's decoded defaults for this material's own vector")
        A("parameters (`COLOUR_PARAMS.md`, `StructProperty:DefaultValue @0xcc`): **%d "
          "cross-checked, %d mismatches** (`%s`).  A lookalike record would not carry"
          % (c["checked"], len(c["mismatch"]), ", ".join(c["parameters"])))
        A("these numbers to 1e-4.")
        A("")
    A("## 4. Where the chain breaks")
    A("")
    A("| question | answer | evidence |")
    A("|---|---|---|")
    A("| is the pixel shader bytecode present? | **yes** | %d SHEX chunks, %d with an OSGN "
      "output signature |" % (u["with_shex"], u["with_osgn"]))
    A("| does the bytecode name its constants? | **no** | 0 RDEF in %d + %d blobs |"
      % (u["blobs"], b["blobs"]))
    A("| do the parameter names occur near the bytecode? | **no** | %d hits in the %d B blob "
      "region (%s) |" % (d["name_leak"]["total"], d["name_leak"]["blob_region_bytes"],
                         d["name_leak"]["probes"]))
    A("| does the material record point at a blob? | **no** | the %d vector entries are "
      "followed by a second list (%d entries), and neither lists a blob start |"
      % (m["count"] if m else 0,
         (d["records"]["trailing_list"] or {}).get("count", 0)))
    A("| does the material GUID occur beside a blob? | **no** | %d sites, %d in the blob region, "
      "at %s |" % (d["guid_sites"].get("count", 0), d["guid_sites"].get("in_blob_region", 0),
                   d["guid_sites"].get("offsets")))
    A("")
    A("So the cache holds both halves - the compiled PS and this material's uniform list - but")
    A("not the map between them.  `Material0_BaseColour` and `Diffuse_Adjust` therefore cannot")
    A("be assigned a `cb0` slot from these files: any such assignment would be a guess, and")
    A("this card does not make one.")
    A("")
    A("What would close it: a build whose DXBC keeps `RDEF` (then the constant names and")
    A("offsets are in the chunk and the PS can be disassembled by name), or the shader-map")
    A("hash function the cooker used to key blobs by material, or a runtime capture of the")
    A("constant buffer the PS receives.  None of the three is in the project today.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, c2 in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |" % (i, c2["check"], "PASS" if c2["pass"] else "FAIL",
                                          c2["detail"]))
    A("")
    A("## 6. UNKNOWNs")
    A("")
    A("1. **Which blob is this material's PS.**  No name, no GUID and no offset links the")
    A("   record to the blob region (section 4).  Would be found in an uncooked build's")
    A("   shader map, or by keying blobs with the cooker's hash.")
    A("2. **The constant-buffer slot of each parameter.**  Needs `RDEF`, which is absent from")
    A("   all %d + %d shipped blobs." % (u["blobs"], b["blobs"]))
    A("3. **The combine operator.**  It is in the PS arithmetic, which is present but unnamed;")
    A("   reading it without `RDEF` would mean matching 38,201 blobs to materials by eye.")
    A("4. **Lighting, reflection and tonemap.**  Same bytecode, same gap.")
    A("")
    A("## 7. Reproduce")
    A("")
    A("    uv run python Tools/scripts/grab_shader_combine.py --write")
    A("    uv run python Tools/scripts/grab_shader_combine.py --check")
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
    md, js = render(d), json.dumps(d, indent=1) + "\n"
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
            elif open(path, encoding="utf-8").read() != want:
                stale.append("%s differs" % os.path.relpath(path, ROOT))
        if stale:
            print("CHECK FAILED: " + "; ".join(stale))
            ok = False
        else:
            print("CHECK OK: the stored .md/.json are byte-identical to a fresh recompute")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
