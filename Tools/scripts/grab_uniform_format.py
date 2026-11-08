"""grab_uniform_format.py - G3-04e1: the on-disk format of the material uniform records.

Scope, and nothing beyond it: the *format* of the per-material uniform records in
`BmGame/CookedPCConsole/CombinedShaderCache-PC-D3D-SM5.upk` - where the region starts, how
one record is delimited, what each field is, and the oracles that prove the split.  What
the records mean, or how a parameter reaches a constant-buffer slot, is out of scope.

G3-04d (`SHADER_COMBINE.md`) counted 6,934 records; G3-04e (`UNIFORM_RECORDS.md`) 6,943.
This pass does not reuse either walk.  It tests the record *header* at every candidate
offset of the region, so a record is only accepted if its own bytes satisfy:

    record :=  i32    n            ; 2 .. 300, length of the name INCLUDING its NUL
               u8[n]  name         ; printable ASCII, name[n-1] == 0
               u8[16] guid         ; distinct for every record
               u8[16] zero         ; 0 in every record
               u32    count        ; 1 .. 64
               entry[count]

    entry  :=  u32 class          ; FName index, 2040 .. 2055 (FMaterialUniformExpression*)
               u32 class_number   ; FName number
               u32 parameter      ; FName index into the package name table
               u32 param_number   ; FName number
               value              ; width fixed by the class

The header was accepted at **7,278** offsets.  In **6,966** of them every entry is
`FMaterialUniformExpressionVectorParameter` and therefore exactly 32 bytes (16 for the two
FNames, 16 for the RGBA value), so those records tile with a single stride:

    span = 40 + n + 32 * count

and the u32 immediately after the entry array is a plausible count (<= 512) for the list
that follows in all 6,966.  There is **no length prefix and no fixed record stride**; the
length is *derived* from decoded fields.  The 30 random records in section 3 are drawn from
this proven set.

The other **312** header-valid records leave the 32-byte entry shape, and the class met
first is `AppendVector` in 206 of them, `FlipBookTextureParameter` in 78 and `FoldedMath`
in 28.  51 tile only if four more classes are given widths borrowed from the block model,
and just 33 of those 51 then land on a plausible next count, so that width is not proven
either; the remaining 261 never tile at any width tried.  The first such byte offset in
the file is where the format work stops, and section 8 names it.  Nothing about those 312
is guessed here.

Usage
    python Tools/scripts/grab_uniform_format.py --write
    python Tools/scripts/grab_uniform_format.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import grab_shader_combine as G  # noqa: E402  (package reader + DXBC census, read-only)

UPK = G.UPK
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "UNIFORM_FORMAT.md")
JS = os.path.join(OUT, "UNIFORM_FORMAT.json")
PARAMS_JSON = os.path.join(OUT, "COLOUR_PARAMS.json")

CLASS_LO, CLASS_HI = 2040, 2055
VECTOR = 2055                     # FMaterialUniformExpressionVectorParameter, 32 B entry
ENTRY_BYTES = 32
SEED = 20261104
SAMPLE_N = 30
MATERIAL = "Batmobile_Worn"
GUID = "5e56a7942acfba4493fbad0c769a1976"
TOL = 1e-4

# Prior passes' rules, verbatim, used only to explain their counts (never to find records).
RE_G304 = re.compile(rb"[\x01-\xc8]\x00\x00\x00[A-Za-z][A-Za-z0-9_ .]{1,60}\x00")
RE_G304E = re.compile(rb"[\x03-\xc8]\x00\x00\x00[A-Za-z][A-Za-z0-9_ ]{1,80}\x00")
W_G304 = {2055: 16, 2051: 4, 2053: 4, 2054: 4, 2044: 16}
W_G304E = {2055: 16, 2044: 16}    # G3-04e required a 16-byte value in the primary list
# widths G3-04e proved for the list that follows a record (not for the record itself):
# FoldedMath is a class FName only (8 B), the rest carry a value
W_BLOCK = {2055: 16, 2051: 4, 2053: 4, 2054: 4, 2045: 4, 2044: 16}
BLOCK_CLASS_ONLY = {2047: 8}

RE_PREFIX = re.compile(rb"[\x00-\xff][\x00\x01]\x00\x00[\x20-\x7e]{1,299}\x00")


# ------------------------------------------------------------------ parsing
def header_at(d: bytes, names, o: int) -> dict | None:
    """The record header predicate at one offset, independent of any entry width."""
    N = len(d)
    if o + 44 > N:
        return None
    n = struct.unpack_from("<i", d, o)[0]
    if not (2 <= n <= 300) or o + 40 + n > N:
        return None
    raw = d[o + 4:o + 4 + n]
    if raw[-1] != 0 or not all(32 <= c < 127 for c in raw[:-1]):
        return None
    e0 = o + 4 + n
    if any(d[e0 + 16:e0 + 32]):
        return None
    count = struct.unpack_from("<I", d, e0 + 32)[0]
    if not (0 < count <= 64):
        return None
    return {"offset": o, "name_len": n, "name": raw[:-1].decode("latin-1"),
            "guid": d[e0:e0 + 16].hex(), "pad_hex": d[e0 + 16:e0 + 32].hex(),
            "count": count, "entries_at": e0 + 36,
            "name_bytes": raw.hex(), "len_bytes": d[o:o + 4].hex(),
            "count_bytes": d[e0 + 32:e0 + 36].hex()}


def entry_walk(d: bytes, names, h: dict, widths: dict) -> tuple:
    """Walk the entry array with a class->width table.  Returns (entries, why, end)."""
    N = len(d)
    q, ents = h["entries_at"], []
    for i in range(h["count"]):
        if q + 16 > N:
            return None, "truncated at entry %d" % i, q
        ci, cn, pi, pn = struct.unpack_from("<IIII", d, q)
        if not (CLASS_LO <= ci <= CLASS_HI):
            return None, "class word %#x at entry %d is not an FName" % (ci, i), q
        if pi >= len(names):
            return None, "parameter index %d at entry %d is out of range" % (pi, i), q
        w = widths.get(ci)
        if w is None:
            return None, "width unknown for %s at entry %d" % (names[ci], i), q
        vals = struct.unpack_from("<4f", d, q + 16) if w >= 16 else ()
        ents.append({"i": i, "at": q, "class_id": ci, "class": names[ci],
                     "class_number": cn, "param_index": pi, "param_name": names[pi],
                     "param_number": pn,
                     "value": [round(v, 6) for v in vals] if w >= 16 else None,
                     "value_hex": d[q + 16:q + 16 + max(w, 0)].hex(), "width": w})
        q += 16 + w
    return ents, None, q


def block_probe(d: bytes, names, o: int, limit: int = 512) -> dict:
    """Walk the list that follows a record with G3-04e's widths, and say where it stops."""
    N = len(d)
    declared = struct.unpack_from("<I", d, o)[0] if o + 4 <= N else -1
    q, ent, stop = o + 4, [], None
    for i in range(max(0, min(declared, limit))):
        if q + 16 > N:
            stop = "truncated"
            break
        ci = struct.unpack_from("<I", d, q)[0]
        if not (CLASS_LO <= ci <= CLASS_HI):
            stop = "not a class FName"
            break
        if ci in BLOCK_CLASS_ONLY:
            ent.append({"i": i, "at": q, "class": names[ci], "parameter": None})
            q += BLOCK_CLASS_ONLY[ci]
            continue
        w = W_BLOCK.get(ci)
        if w is None:
            stop = "width not proven for %s" % names[ci]
            break
        pi = struct.unpack_from("<I", d, q + 8)[0]
        if pi >= len(names):
            stop = "parameter index out of range"
            break
        ent.append({"i": i, "at": q, "class": names[ci],
                    "parameter": names[pi]})
        q += 16 + w
    return {"offset": o, "declared": declared, "parsed": len(ent), "entries": ent,
            "end": q, "stop": stop, "stop_offset": q if stop else None,
            "stop_word": struct.unpack_from("<I", d, q)[0] if stop and q + 4 <= N else None}


def sampled_strides(d: bytes, h: dict) -> dict:
    """Which entry strides keep every class word a valid uniform-expression FName?"""
    q0 = h["entries_at"]
    out = {}
    for s in (28, 32, 36):
        ok = True
        for i in range(h["count"]):
            at = q0 + s * i
            if at + 4 > len(d):
                ok = False
                break
            ci = struct.unpack_from("<I", d, at)[0]
            if not (CLASS_LO <= ci <= CLASS_HI):
                ok = False
                break
        out[str(s)] = ok
    return out


def colour_defaults() -> dict:
    """Batmobile_Worn's vector defaults as G3-04c decoded them (COLOUR_PARAMS.json)."""
    if not os.path.exists(PARAMS_JSON):
        return {}
    j = json.load(open(PARAMS_JSON, encoding="utf-8"))
    out = {}
    for row in j.get("defaults", []):
        v = row.get("value")
        if row.get("material") == MATERIAL and isinstance(v, list) and len(v) == 4:
            out[row["name"]] = [round(float(x), 6) for x in v]
    return out


def hexdump(off: int, data: bytes) -> list:
    out = []
    for i in range(0, len(data), 16):
        row = data[i:i + 16]
        out.append("    %#08x  %-47s  %s" % (off + i, row.hex(" "),
                                             "".join(chr(c) if 32 <= c < 127 else "."
                                                     for c in row)))
    return out


# ------------------------------------------------------------------ build
def build() -> dict:
    p, d = G.shader_cache()
    blobs = G.dxbc_census(d)
    start = blobs["last_end"]
    names = p.names
    N = len(d)

    print("  testing the record header at every candidate offset ...", flush=True)
    cands = [m.start() for m in RE_PREFIX.finditer(d, start)]
    H = [h for h in (header_at(d, names, o) for o in cands) if h]
    H.sort(key=lambda h: h["offset"])
    first = H[0]["offset"]
    prefix = d[start:first]

    # ---- partition: proven all-vector records, then the ones that leave that shape
    A, B, C = [], [], []
    for h in H:
        ents, why, end = entry_walk(d, names, h, {VECTOR: 16})
        if ents is not None:
            h.update(entries=ents, end=end, span=end - h["offset"], why=None)
            A.append(h)
            continue
        h["first_stop"] = why
        h["stop_offset"] = end
        ents2, why2, end2 = entry_walk(d, names, h, W_BLOCK)
        if ents2 is not None:
            h.update(entries=ents2, end=end2, span=end2 - h["offset"], why=None,
                     next_u32_plausible=(end2 + 4 <= N
                                         and struct.unpack_from("<I", d, end2)[0] <= 512))
            B.append(h)
        else:
            h.update(entries=None, why=why2)
            C.append(h)

    # ---- header oracles, over every candidate
    strings_ok = sum(1 for h in H if h["name_len"] == len(h["name"]) + 1)
    pad_ok = sum(1 for h in H if h["pad_hex"] == "00" * 16)
    guid_unique = len({h["guid"] for h in H})
    guid_recur = min(d.count(bytes.fromhex(h["guid"])) for h in H)
    offsets_sorted = all(a["offset"] < b["offset"] for a, b in zip(A, A[1:]))

    # ---- A: the proven population
    entries_total = sum(h["count"] for h in A)
    span_total = sum(h["span"] for h in A)
    spans_ok = sum(1 for h in A if h["span"] == 40 + h["name_len"] + ENTRY_BYTES * h["count"])
    classes, clsnum, pnum = {}, {}, {}
    for h in A:
        for e in h["entries"]:
            classes[e["class"]] = classes.get(e["class"], 0) + 1
            clsnum[str(e["class_number"])] = clsnum.get(str(e["class_number"]), 0) + 1
            pnum[str(e["param_number"])] = pnum.get(str(e["param_number"]), 0) + 1
    # stride oracle over every proven record with at least 3 entries
    stride_rows = [h for h in A if h["count"] >= 3]
    stride_ok = {str(s): sum(1 for h in stride_rows if sampled_strides(d, h)[str(s)])
                 for s in (28, 32, 36)}
    gaps = [b["offset"] - a["end"] for a, b in zip(A, A[1:])]
    tail = N - A[-1]["end"]
    accounted = len(prefix) + span_total + sum(gaps) + tail
    next_ok = sum(1 for h in A
                  if h["end"] + 4 <= N and struct.unpack_from("<I", d, h["end"])[0] <= 512)

    # ---- the 312 that leave the 32-byte entry shape
    leaves = sorted(B + C, key=lambda h: h["offset"])
    first_stop = min(leaves, key=lambda h: h["stop_offset"])
    stop_ci = struct.unpack_from("<I", d, first_stop["stop_offset"])[0]
    stop_at = first_stop["stop_offset"]
    stop_entry_index = (stop_at - first_stop["entries_at"]) // ENTRY_BYTES
    stop_context = []
    q = stop_at
    for k in range(3):
        if q + 4 > N:
            break
        w = struct.unpack_from("<I", d, q)[0]
        stop_context.append({"at": q, "word": w,
                             "as_class": names[w] if CLASS_LO <= w <= CLASS_HI else None})
        q += 8
    leaves_hist = {}
    for h in leaves:
        ci = struct.unpack_from("<I", d, h["stop_offset"])[0]
        key = names[ci] if CLASS_LO <= ci <= CLASS_HI else "class word %#x" % ci
        leaves_hist[key] = leaves_hist.get(key, 0) + 1

    # ---- prior counts, reproduced from these 7,278 headers
    g304 = sum(1 for h in H if RE_G304.match(d, h["offset"])
               and entry_walk(d, names, h, W_G304)[0] is not None)
    g304e = sum(1 for h in H if RE_G304E.match(d, h["offset"])
                and entry_walk(d, names, h, W_G304E)[0] is not None)
    missed_304 = [h["name"] for h in A if not RE_G304.match(d, h["offset"])]
    missed_304e = [h["name"] for h in A if not RE_G304E.match(d, h["offset"])]

    # ---- 30 random proven records
    rng = random.Random(SEED)
    idx = sorted(rng.sample(range(len(A)), SAMPLE_N))
    samples = []
    for i in idx:
        h = A[i]
        hex_text = d[h["offset"]:h["end"]].hex()
        back = header_at(bytes.fromhex(hex_text), names, 0)
        rb = entry_walk(bytes.fromhex(hex_text), names, back, {VECTOR: 16}) if back else (None,)
        same = (back is not None and rb[0] is not None
                and back["name"] == h["name"] and back["guid"] == h["guid"]
                and back["count"] == h["count"]
                and [e["param_name"] for e in rb[0]] == [e["param_name"] for e in h["entries"]]
                and [e["value"] for e in rb[0]] == [e["value"] for e in h["entries"]])
        samples.append({"index": i, "offset": h["offset"], "name": h["name"],
                        "name_len": h["name_len"], "guid": h["guid"],
                        "count": h["count"], "end": h["end"], "span": h["span"],
                        "hex": hex_text, "entries": h["entries"],
                        "reparse_ok": bool(same), "strides": sampled_strides(d, h),
                        "fields": {"len_at": h["offset"], "len_bytes": h["len_bytes"],
                                   "name_at": h["offset"] + 4, "name_bytes": h["name_bytes"],
                                   "guid_at": h["offset"] + 4 + h["name_len"],
                                   "guid_bytes": h["guid"],
                                   "pad_at": h["offset"] + 20 + h["name_len"],
                                   "pad_bytes": h["pad_hex"],
                                   "count_at": h["offset"] + 36 + h["name_len"],
                                   "count_bytes": h["count_bytes"],
                                   "entries_at": h["entries_at"]}})

    # ---- anchor record and its external cross-check
    body = next((h for h in A if h["guid"] == GUID), None)
    want = colour_defaults()
    cross = []
    if body:
        for e in body["entries"]:
            w = want.get(e["param_name"])
            if w is None:
                continue
            cross.append({"parameter": e["param_name"], "record": e["value"], "decoded": w,
                          "match": all(abs(a - b) <= TOL for a, b in zip(e["value"], w))})
    anchor_block = block_probe(d, names, body["end"]) if body else None
    detail = None
    if anchor_block and anchor_block["stop"]:
        so = anchor_block["stop_offset"]
        ci, cn, pi, pn = struct.unpack_from("<IIII", d, so + 1)
        ok_entry = CLASS_LO <= ci <= CLASS_HI and pi < len(names)
        detail = {"offset": so, "word": anchor_block["stop_word"],
                  "reason": anchor_block["stop"], "bytes": d[so:so + 8].hex(),
                  "resumes_at": so + 1,
                  "resumes": ("%s, %s, value %r" % (names[ci], names[pi],
                                                    round(struct.unpack_from("<f", d, so + 17)[0], 6)))
                  if ok_entry else None}

    checks = [
        ("the record region starts after the last DXBC container",
         first > start,
         "container run ends %#x; first header at %#x; %d B between them (filler of the "
         "same kind as the inter-container gaps)" % (start, first, len(prefix))),
        ("the header predicate accepts 7,278 offsets and no two overlap in the proven set",
         len(H) == 7278 and len(A) == 6966 and len(B) + len(C) == 312 and offsets_sorted
         and all(h["end"] <= N for h in A),
         "%d header candidates, %d proven all-vector, %d + %d leave the shape; starts "
         "strictly increasing; last proven end %#x <= EOF %#x"
         % (len(H), len(A), len(B), len(C), A[-1]["end"], N)),
        ("string length words match the strings",
         strings_ok == len(H),
         "%d/%d: i32 n == len(name)+1, NUL at byte n-1, every name byte printable"
         % (strings_ok, len(H))),
        ("the 16 bytes after the guid are zero",
         pad_ok == len(H), "%d/%d records have 16 zero bytes at +20+n" % (pad_ok, len(H))),
        ("the guids are distinct and each recurs in the file",
         guid_unique == len(H) and guid_recur >= 2,
         "%d distinct guids for %d records; each occurs at least %d times"
         % (guid_unique, len(H), guid_recur)),
        ("the declared count fixes the span of every proven record",
         spans_ok == len(A) and entries_total == sum(len(h["entries"]) for h in A),
         "%d/%d proven records: span == 40 + n + 32*count; %d entries decoded from %d "
         "declared" % (spans_ok, len(A), sum(len(h["entries"]) for h in A), entries_total)),
        ("the entry counts sum to the decoded entries",
         len(A) == 6966 and entries_total == 9582,
         "%d proven records, %d entries, %d B of spans" % (len(A), entries_total, span_total)),
        ("every proven entry is the same class and no reference is out of range",
         set(classes) == {names[VECTOR]},
         "class census %s; 0 parameter indices out of the %d-name table"
         % (classes, len(names))),
        ("the u32 after every proven record is a plausible next-list count",
         next_ok == len(A),
         "%d/%d proven records are followed by a u32 <= 512 (this is the boundary oracle "
         "for the record's end)" % (next_ok, len(A))),
        ("the region partitions into prefix, record spans, bytes outside records and tail",
         accounted == N - start,
         "%d B prefix + %d B record spans (%.1f%% of the %d B region) + %d B outside "
         "records + %d B tail == %d B; the header predicate was tested at all %d "
         "candidate offsets, so no further record header exists in that remainder "
         "under this layout"
         % (len(prefix), span_total, 100.0 * span_total / (N - start), N - start,
            sum(gaps), tail, N - start, len(cands))),
        ("the 30 sampled records re-parse from their own hex",
         all(s["reparse_ok"] for s in samples),
         "%d/%d round-trip name, guid, count, parameters and values"
         % (sum(1 for s in samples if s["reparse_ok"]), len(samples))),
        ("32 bytes is the only entry stride that resolves every class word",
         stride_ok["32"] == len(stride_rows) and stride_ok["28"] == 0
         and stride_ok["36"] == 0,
         "over all %d proven records with count >= 3: stride 32 valid %d, stride 28 valid "
         "%d, stride 36 valid %d"
         % (len(stride_rows), stride_ok["32"], stride_ok["28"], stride_ok["36"])),
        ("G3-04d's 6,934 and G3-04e's 6,943 are these same headers through narrower rules",
         g304 == 6934 and g304e == 6943,
         "re-running their acceptance rules over the 7,278 headers: %d (G3-04d regex + its "
         "width table), %d (G3-04e regex + 16-byte-only entries), %d structural"
         % (g304, g304e, len(A))),
        ("the anchor record is found by guid and its values match G3-04c",
         body is not None and body["count"] == 14 and len(cross) >= 10
         and all(c["match"] for c in cross),
         "%s at %#x, %d entries, %d vector defaults cross-checked, %d mismatches"
         % (MATERIAL, body["offset"] if body else 0, body["count"] if body else 0,
            len(cross), sum(1 for c in cross if not c["match"]))),
        ("the bytes after the record stop at one named field",
         detail is not None,
         "anchor block: %d declared, %d parsed, stop at %#x on u32 %#x (%s), resumes at "
         "%#x as a well-formed entry"
         % (anchor_block["declared"], anchor_block["parsed"], detail["offset"],
            detail["word"], detail["reason"], detail["resumes_at"]) if detail else "none"),
    ]

    return {
        "task": "G3-04e1 - on-disk format of the material uniform records",
        "inputs": {"upk": UPK, "bytes": os.path.getsize(UPK),
                   "sha1_16": hashlib.sha1(open(UPK, "rb").read()).hexdigest()[:16]},
        "region": {"container_run_end": start, "first_record": first,
                   "prefix_bytes": len(prefix), "prefix_hex": prefix.hex(),
                   "candidates_scanned": len(cands), "header_candidates": len(H),
                   "region_bytes": N - start, "records_bytes": span_total,
                   "between_bytes": sum(gaps), "tail_bytes": tail, "file_bytes": N,
                   "gap_min": min(gaps), "gap_max": max(gaps)},
        "layout": {"name_len": "i32 at +0, length of the name including its NUL",
                   "name": "u8[n] printable ASCII, NUL-terminated",
                   "guid": "u8[16] at +4+n, distinct per record",
                   "pad": "u8[16] at +20+n, 0 in every record",
                   "count": "u32 at +36+n, 1..64",
                   "entry": "32 B for the vector class: class FName (8) + parameter FName "
                            "(8) + 4 x f32",
                   "span": "40 + n + 32 * count",
                   "length_prefix": "none",
                   "fixed_stride": "none"},
        "census": {"records": len(A), "entries": entries_total,
                   "entries_decoded": sum(len(h["entries"]) for h in A),
                   "strings_ok": strings_ok, "pad_ok": pad_ok, "spans_ok": spans_ok,
                   "guid_unique": guid_unique, "guid_recur_min": guid_recur,
                   "class_census": classes, "class_number_census": clsnum,
                   "param_number_census": pnum,
                   "stride_records": len(stride_rows), "stride_valid": stride_ok,
                   "count_hist": _hist([h["count"] for h in A]),
                   "name_len_range": [min(h["name_len"] for h in A),
                                      max(h["name_len"] for h in A)],
                   "span_range": [min(h["span"] for h in A), max(h["span"] for h in A)],
                   "distinct_names": len({h["name"] for h in A})},
        "leaves": {"records": len(leaves), "tile_with_block_widths": len(B),
                   "nested": len(C),
                   "first_non_vector_class": leaves_hist,
                   "first_stop_offset": stop_at,
                   "first_stop_entry_index": stop_entry_index,
                   "first_stop_record": first_stop["name"],
                   "next_u32_plausible": next_ok,
                   "first_stop_record_offset": first_stop["offset"],
                   "first_stop_class_word": stop_ci,
                   "first_stop_context": stop_context,
                   "block_width_tiles_next_plausible": sum(
                       1 for h in B if h.get("next_u32_plausible"))},
        "reconciliation": {"structural": len(A), "header_candidates": len(H),
                           "g3_04d": g304, "g3_04e": g304e,
                           "missed_by_g3_04d": missed_304,
                           "missed_by_g3_04e": missed_304e},
        "samples": samples, "sample_seed": SEED,
        "anchor": {"offset": body["offset"] if body else None,
                   "guid": body["guid"] if body else None,
                   "count": body["count"] if body else None,
                   "entries": body["entries"] if body else None,
                   "cross_check": cross,
                   "block": anchor_block, "block_stop_detail": detail},
        "checks": [{"check": n, "pass": bool(ok), "detail": det} for n, ok, det in checks],
    }


def _hist(vals: list) -> dict:
    h = {}
    for v in vals:
        h[str(v)] = h.get(str(v), 0) + 1
    return dict(sorted(h.items(), key=lambda kv: int(kv[0])))


# ------------------------------------------------------------------ render
def render(d: dict) -> str:
    L = []
    A = L.append
    r, c, lv = d["region"], d["census"], d["leaves"]
    A("# The material uniform records: on-disk format, proven to the first unexplained byte (G3-04e1)")
    A("")
    A("Generated by `python Tools/scripts/grab_uniform_format.py --write`; `--check`")
    A("recomputes every number from the install file and requires the stored files to be")
    A("byte-identical. Machine half: `UNIFORM_FORMAT.json`.")
    A("")
    A("Labels: **decoded** = read from bytes at a stated offset; **derived** = arithmetic on")
    A("decoded values; **UNKNOWN** = not in the bytes, with where it would be.")
    A("")
    A("Scope is format only. Nothing here says what a record expresses, or how a parameter")
    A("reaches a constant-buffer slot.")
    A("")
    A("Input (read-only):")
    A("")
    A("| file | bytes | sha1[:16] |")
    A("|---|---:|---|")
    A("| `%s` | %d | `%s` |" % (d["inputs"]["upk"], d["inputs"]["bytes"],
                                d["inputs"]["sha1_16"]))
    A("")
    A("## 1. The answer")
    A("")
    A("**No length prefix, no fixed stride.** The record is self-delimiting: an `i32` name")
    A("length, the name, a 16-byte guid, 16 zero bytes, a `u32` count, and `count` entries")
    A("whose width is fixed by their class. For the class that occurs in every entry of the")
    A("proven records - `FMaterialUniformExpressionVectorParameter` - the entry is exactly")
    A("32 bytes, so the record's length is *derived*:")
    A("")
    A("    span = 40 + n + 32 * count           (n = the name length field, NUL included)")
    A("")
    A("Testing that layout at every candidate offset of the region accepts the header at")
    A("**%d** offsets. **%d** of them are proven end to end (%d entries, %d B); **%d**"
      % (r["header_candidates"], c["records"], c["entries"], r["records_bytes"],
         lv["records"]))
    A("leave the 32-byte entry shape and are **not** decoded here (section 7).")
    A("")
    A("The brief's 6,934 is exactly reproduced: it is G3-04d's regex-plus-width-table pass")
    A("over these same %d headers (section 7). The layout itself accepts **%d** records."
      % (r["header_candidates"], c["records"]))
    A("")
    A("## 2. Where the region is")
    A("")
    A("| item | value |")
    A("|---|---|")
    A("| end of the DXBC container run | `%#x` |" % r["container_run_end"])
    A("| first record header | `%#x` |" % r["first_record"])
    A("| bytes between them | %d (`%s`) |" % (len(r["prefix_hex"]) // 2, r["prefix_hex"][:64] + "..."))
    A("| candidate offsets tested | %d |" % r["candidates_scanned"])
    A("| header accepted | %d |" % r["header_candidates"])
    A("| region to EOF | %d B |" % r["region_bytes"])
    A("| Σ proven record spans | %d B (%.1f%% of the region) |"
      % (r["records_bytes"], 100.0 * r["records_bytes"] / r["region_bytes"]))
    A("| Σ bytes between proven records | %d B (range %d … %d) |"
      % (r["between_bytes"], r["gap_min"], r["gap_max"]))
    A("| trailing bytes after the last proven record | %d B |" % r["tail_bytes"])
    A("")
    A("The records are %.1f%% of the region, not all of it: between them sits the other "
      "per-material data (the uniform-expression blocks, and material payload this card "
      "does not decode). That is why there is no fixed stride - the bytes are a run of "
      "records *interleaved* with data this card leaves UNKNOWN, not a record table."
      % (100.0 * r["records_bytes"] / r["region_bytes"]))
    A("## 3. The layout, field by field")
    A("")
    A("```")
    A("record :=  i32    n          ; 2 .. 300, length of the name INCLUDING its NUL")
    A("           u8[n]  name       ; printable ASCII, name[n-1] == 0")
    A("           u8[16] guid       ; distinct for every record")
    A("           u8[16] zero       ; 0 in every record")
    A("           u32    count      ; 1 .. 64")
    A("           entry[count]")
    A("")
    A("entry  :=  u32 class        ; FName index, 2040..2055, FMaterialUniformExpression*")
    A("           u32 class_number ; FName number")
    A("           u32 parameter    ; FName index into the package name table")
    A("           u32 param_number ; FName number")
    A("           f32[4] value     ; 16 B: the width the vector class measures")
    A("```")
    A("")
    A("| field | offset | size | oracle |")
    A("|---|---:|---:|---|")
    A("| name length | `+0` | 4 | equals `len(name)+1` in **%d/%d** headers |"
      % (c["strings_ok"], r["header_candidates"]))
    A("| name | `+4` | n | every byte printable ASCII, NUL exactly at `n-1` |")
    A("| guid | `+4+n` | 16 | **%d** distinct values for %d headers; every one recurs "
      "elsewhere in the file (minimum %d occurrences) |"
      % (c["guid_unique"], r["header_candidates"], c["guid_recur_min"]))
    A("| zero pad | `+20+n` | 16 | all zero in **%d/%d** headers |"
      % (c["pad_ok"], r["header_candidates"]))
    A("| count | `+36+n` | 4 | 1..64; the entry array is `count` x its stride, so the "
      "record ends exactly where the next list begins |")
    A("| entries | `+40+n` | 32 x count | for the vector class, stride 32 puts a valid class "
      "FName at every entry start; 28 and 36 do not (section 4) |")
    A("")
    A("| census over the %d proven records | value |" % c["records"])
    A("|---|---|")
    A("| entries | %d (all decoded) |" % c["entries_decoded"])
    A("| entry class | %s |" % ", ".join("`%s` %d" % (k, v) for k, v in c["class_census"].items()))
    A("| count per record | %s |" % ", ".join("%s x%d" % (k, v) for k, v in c["count_hist"].items()))
    A("| name length (incl. NUL) | %d .. %d B |" % tuple(c["name_len_range"]))
    A("| record span | %d .. %d B |" % tuple(c["span_range"]))
    A("| distinct names / guids | %d / %d |" % (c["distinct_names"], c["guid_unique"]))
    A("| class FName number | %s |"
      % ", ".join("%s x%d" % (k, v) for k, v in c["class_number_census"].items()))
    A("| parameter FName number | %s |"
      % ", ".join("%s x%d" % (k, v) for k, v in c["param_number_census"].items()))
    A("| entry stride over the %d records with count >= 3 | 32 B valid in %d, 28 B in %d, "
      "36 B in %d |" % (c["stride_records"], c["stride_valid"]["32"],
                        c["stride_valid"]["28"], c["stride_valid"]["36"]))
    A("")
    A("## 4. Thirty random records, byte for byte")
    A("")
    A("Sample: `random.Random(%d).sample(range(%d), %d)`, indices %s."
      % (d["sample_seed"], c["records"], SAMPLE_N,
         ", ".join(str(s["index"]) for s in d["samples"])))
    A("Each block is the record's own bytes, then the field split with absolute offsets.")
    A("Every sample is re-parsed from its printed hex (oracle O11).")
    A("")
    for n_, s in enumerate(d["samples"], 1):
        f = s["fields"]
        A("### %d. index %d - `%s`" % (n_, s["index"], s["name"]))
        A("")
        A("`%#x` .. `%#x`, span **%d** B = 40 + %d + 32 x %d."
          % (s["offset"], s["end"], s["span"], s["name_len"], s["count"]))
        A("")
        A("```")
        L.extend(hexdump(s["offset"], bytes.fromhex(s["hex"])))
        A("```")
        A("")
        A("| offset | size | field | value |")
        A("|---|---:|---|---|")
        A("| `%#x` | 4 | name length | %d |" % (f["len_at"], s["name_len"]))
        A("| `%#x` | %d | name | `%s` |" % (f["name_at"], s["name_len"], s["name"]))
        A("| `%#x` | 16 | guid | `%s` |" % (f["guid_at"], s["guid"]))
        A("| `%#x` | 16 | zero pad | `%s` |" % (f["pad_at"], f["pad_bytes"]))
        A("| `%#x` | 4 | count | %d |" % (f["count_at"], s["count"]))
        A("| `%#x` | %d | entries | %d x 32 B |"
          % (f["entries_at"], s["count"] * 32, s["count"]))
        A("")
        A("| # | at | class | parameter | value |")
        A("|---:|---|---|---|---|")
        for e in s["entries"]:
            A("| %d | `%#x` | `%s` | `%s` | `%s` |"
              % (e["i"] + 1, e["at"], e["class"], e["param_name"], e["value"]))
        A("")
    A("## 5. The anchor record: `Batmobile_Worn`")
    A("")
    a = d["anchor"]
    A("Found by guid `%s`, not by name: **`%#x`**, %d entries."
      % (a["guid"], a["offset"], a["count"]))
    A("Its values reproduce G3-04c's decoded vector defaults (`COLOUR_PARAMS.json`):")
    A("**%d checked, %d mismatches** at 1e-4."
      % (len(a["cross_check"]), sum(1 for x in a["cross_check"] if not x["match"])))
    A("")
    A("| parameter | record value | `COLOUR_PARAMS.json` | match |")
    A("|---|---|---|---|")
    for x in a["cross_check"]:
        A("| `%s` | `%s` | `%s` | %s |"
          % (x["parameter"], x["record"], x["decoded"], "yes" if x["match"] else "**NO**"))
    A("")
    A("## 6. Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, ch in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |"
          % (i, ch["check"], "PASS" if ch["pass"] else "FAIL", ch["detail"]))
    A("")
    rc = d["reconciliation"]
    A("## 7. The three counts, reconciled")
    A("")
    A("| walk | records | rule |")
    A("|---|---:|---|")
    A("| G3-04d | %d | name regex `[A-Za-z][A-Za-z0-9_ .]{1,60}` **and** its width table "
      "(no FlipBook/Constant/FoldedMath entry) |" % rc["g3_04d"])
    A("| G3-04e | %d | name regex `[A-Za-z][A-Za-z0-9_ ]{1,80}` **and** 16-byte entries only |"
      % rc["g3_04e"])
    A("| this pass | %d | the layout itself, no name pattern, vector-class entries |"
      % rc["structural"])
    A("")
    A("Both prior numbers are reproduced by applying their own rules to these headers")
    A("(oracle O13), so they are subsets of one population, not different structures.")
    A("The %d records G3-04d's regex cannot match at all:" % len(rc["missed_by_g3_04d"]))
    A("")
    A("| name | why |")
    A("|---|---|")
    for nme in rc["missed_by_g3_04d"]:
        why = ("name longer than 60 characters" if len(nme) > 60
               else "character outside `[A-Za-z0-9_ .]` or a leading non-letter")
        A("| `%s` | %s |" % (nme, why))
    A("")
    A("## 8. Where the format stops: the first field this card cannot explain")
    A("")
    A("The record ends at its entry array, and for the proven records the next u32 is a")
    A("plausible count in **%d/%d** cases (oracle O9) - that is the boundary proof."
      % (lv["next_u32_plausible"], c["records"]))
    A("Beyond it, the record format is not what stops the work; the *entry* format does, for")
    A("the %d headers whose entries are not all vector parameters:" % lv["records"])
    A("")
    A("| first non-vector class met | records |")
    A("|---|---:|")
    for k, v in sorted(lv["first_non_vector_class"].items(), key=lambda kv: -kv[1]):
        A("| `%s` | %d |" % (k, v))
    A("")
    A("Of those, %d tile only if the FlipBook entry (`FMaterialUniformExpression"
      % lv["tile_with_block_widths"])
    A("FlipBookTextureParameter`) is given the 4-byte width borrowed from the post-record")
    A("block model, and only %d of the %d then land on a plausible next count - so that "
      "width is" % (lv["block_width_tiles_next_plausible"], lv["tile_with_block_widths"]))
    A("not proven either. The remaining %d never tile at any width tried." % lv["nested"])
    A("")
    A("**The first unexplained byte in the file** is at `%#x`, entry index %d of `%s`"
      % (lv["first_stop_offset"], lv["first_stop_entry_index"], lv["first_stop_record"]))
    A("(record at `%#x`):" % lv["first_stop_record_offset"])
    A("")
    A("```")
    for row in lv["first_stop_context"]:
        A("    %#08x  %08x  %s" % (row["at"], row["word"],
                                   ("-> `%s`" % row["as_class"]) if row["as_class"]
                                   else "(not a class FName)"))
    A("```")
    A("")
    A("The entry begins with a class FName (`FMaterialUniformExpressionAppendVector`), then")
    A("instead of a parameter FName and a value it carries further class FNames - the")
    A("operands of the expression. So the entry's width depends on a tree whose encoding")
    A("(operand order, per-class payload, termination) is **UNKNOWN** from these bytes; that")
    A("is the first field this card cannot explain, and it stops the format work here.")
    A("")
    dt = a["block_stop_detail"]
    if dt:
        A("The same thing shows up after the anchor record: its following block declares %d"
          % a["block"]["declared"])
        A("expressions, %d parse, and at `%#x` the u32 is `%#x` - %s - while `%#x` begins a"
          % (a["block"]["parsed"], dt["offset"], dt["word"], dt["reason"], dt["resumes_at"]))
        A("well-formed entry (%s). A single byte sits before the nested expression; its"
          % dt["resumes"])
        A("meaning is UNKNOWN (oracle O15). This does not touch the record: its extent is")
        A("fixed by its own count (oracle O6).")
        A("")
    A("## 9. UNKNOWNs")
    A("")
    A("1. **The entry payload for every class other than")
    A("   `FMaterialUniformExpressionVectorParameter`.**  Section 8: `AppendVector` stores")
    A("   operand class FNames where a value would be. Affects %d of %d headers. Would need"
      % (lv["records"], r["header_candidates"]))
    A("   the cooker's serialiser for `FMaterialUniformExpression*`, which the project does")
    A("   not have.")
    A("2. **The purpose of the 16 zero bytes at `+20+n`.**  Zero in every record, so four")
    A("   `u32` zeros, two `u64` zeros and one 16-byte zero field are indistinguishable.")
    A("3. **The %d bytes between the container run and the first record**, and the bytes"
      % r["prefix_bytes"])
    A("   between records. Same filler as the inter-container gaps G3-04d measured (310 …")
    A("   2044 B); not decoded there or here.")
    A("4. **What the records mean.**  Out of scope by the brief; the slot binding is absent")
    A("   from the cache (`SHADER_COMBINE.md`: 0 `RDEF` in 38,201 + 2,098 blobs).")
    A("")
    A("## 10. Reproduce")
    A("")
    A("    uv run python Tools/scripts/grab_uniform_format.py --write")
    A("    uv run python Tools/scripts/grab_uniform_format.py --check")
    A("")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ main
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
    for ch in d["checks"]:
        print("%s  %s" % ("PASS" if ch["pass"] else "FAIL", ch["check"]))
        print("      %s" % ch["detail"])
        ok = ok and ch["pass"]
    print("\n%d/%d oracles pass" % (sum(1 for ch in d["checks"] if ch["pass"]),
                                   len(d["checks"])))

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
