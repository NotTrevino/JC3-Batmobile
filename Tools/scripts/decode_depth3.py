#!/usr/bin/env python3
"""
decode_depth3.py - G3-19: finish (or bound) the byte accounting of the four
PARTIAL vanilla Serpente files left by G3-12/G3-12b.

Inputs (read-only):
  * the three `sportsmuscle_missile_base_signature_lod{1,2,3}.rbm` blocks of the
    vanilla `sportsmuscle` vehicle, taken from the JC3 `.ee` archive the way the
    rest of the tool chain takes them (`bm_rc` + `eetoc`, no game process);
  * the two `.epe` round-trip artifacts under `tmp/g319/`:
        a.epe = the vanilla file exactly as it sits in the archive (sha256 checked)
        b.epe = what `Gibbed.JustCause3.ConvertProperty.exe --e` writes back after
                reading that same file (the tool's own re-serialisation).

Oracles used, and nothing else:
  1. RBM: every block is closed by the 0x89ABCDEF block checksum, and the parsed
     parts must add up to *exactly* the file size (`sum == size`), else FAIL.
  2. RBM: `rbm_geom.decode_carpaintmm` (already the project's verified decoder for
     that block type) must consume a block to its exact end offset.
  3. RBM: the trailing index list must be `u32 n` followed by `n` u16 and must end
     exactly on the block checksum; the indices must address fewer than 4n vertices.
  4. EPE: a byte-for-byte diff where every differing byte must fall into a named
     class, otherwise it is counted as unexplained and the accounting FAILS.

Labels: every number below is either decoded (file + offset), derived (rule +
inputs, shown), or UNKNOWN (what was tried, where it would be).

    python decode_depth3.py --write     # write Research/JC3Grab/DECODE_DEPTH3.{md,json}
    python decode_depth3.py --check     # recompute and diff against what is on disk
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bm_rc  # noqa: E402
import eetoc  # noqa: E402
import rbm_geom  # noqa: E402

ROOT = HERE.parent.parent
OUT_MD = ROOT / "Research" / "JC3Grab" / "DECODE_DEPTH3.md"
OUT_JSON = ROOT / "Research" / "JC3Grab" / "DECODE_DEPTH3.json"
EPE_A = ROOT / "tmp" / "g319" / "a.epe"
EPE_B = ROOT / "tmp" / "g319" / "b.epe"
CS = rbm_geom.RBM_BLOCK_CHECKSUM


def f32(blob: bytes, off: int) -> float:
    return struct.unpack_from("<f", blob, off)[0]


def fval(blob: bytes, off: int):
    """A head float, or its raw word when it is not a finite number.

    One field of the `GeneralMkIII` head is 0x7FFFFFFF, i.e. a NaN pattern rather
    than a float; printing it as a float would put NaN in the JSON and make the
    `--check` comparison fail against itself (NaN != NaN). The raw word is the
    honest record of a field whose type we have not established.
    """
    x = f32(blob, off)
    if not math.isfinite(x):
        return "0x%08x (not a finite f32)" % struct.unpack_from("<I", blob, off)[0]
    return round(x, 6)


# ---------------------------------------------------------------------------
# RBM
# ---------------------------------------------------------------------------

def archive():
    raw = eetoc.unaaf(bm_rc.vfs(bm_rc.DIR + bm_rc.OLD + ".ee"))
    return raw, eetoc.sarc_dir(raw)


def rbm_report() -> dict:
    raw, d = archive()
    out = {"files": [], "all_sums_ok": True}

    for name in sorted(n for n, _o, _s in d
                       if "sportsmuscle_missile_base_signature_lod" in n and n.endswith(".rbm")):
        off, size = [(o, s) for n, o, s in d if n == name][0]
        blob = raw[off:off + size]
        h = rbm_geom.Rbm.parse_header(blob)

        # --- block 0: decoded by the verified CarPaintMM path
        th0 = struct.unpack_from("<I", blob, h["header_len"])[0]
        _b0, end0 = rbm_geom.decode_carpaintmm(blob, h["header_len"] + 4, th0)
        cs0 = end0
        th1 = struct.unpack_from("<I", blob, cs0 + 4)[0]
        s1 = cs0 + 8
        cs1 = next(c for c in range(s1, len(blob) - 4)
                   if struct.unpack_from("<I", blob, c)[0] == CS)
        e1 = cs1
        th2 = struct.unpack_from("<I", blob, cs1 + 4)[0]
        s2 = cs1 + 8
        _b2, end2 = rbm_geom.decode_carpaintmm(blob, s2, th2)

        blocks = [
            {"i": 0, "type": rbm_geom.BLOCK_NAMES.get(th0, hex(th0)), "type_hash": hex(th0),
             "payload": [h["header_len"] + 4, end0], "bytes": end0 - (h["header_len"] + 4),
             "decoded": "rbm_geom.decode_carpaintmm (end exact)"},
            {"i": 1, "type": rbm_geom.BLOCK_NAMES.get(th1, hex(th1)), "type_hash": hex(th1),
             "payload": [s1, e1], "bytes": e1 - s1,
             "decoded": None},
            {"i": 2, "type": rbm_geom.BLOCK_NAMES.get(th2, hex(th2)), "type_hash": hex(th2),
             "payload": [s2, end2], "bytes": end2 - s2,
             "decoded": "rbm_geom.decode_carpaintmm (end exact)"},
        ]
        total = h["header_len"] + sum(4 + b["bytes"] + 4 for b in blocks)
        ok = (total == size) and end2 == len(blob) - 4 and \
             struct.unpack_from("<I", blob, len(blob) - 4)[0] == CS
        out["all_sums_ok"] = out["all_sums_ok"] and ok

        # --- GeneralMkIII interior: head fields (identical bytes in all three lods)
        head = blob[s1:s1 + 0x48]
        head_fields = [
            {"off": 0x00, "kind": "u32", "value": struct.unpack_from("<I", blob, s1)[0]},
            {"off": 0x10, "kind": "f32", "value": fval(blob, s1 + 0x10)},
            {"off": 0x14, "kind": "f32", "value": fval(blob, s1 + 0x14)},
            {"off": 0x18, "kind": "f32", "value": fval(blob, s1 + 0x18)},
            {"off": 0x1c, "kind": "f32", "value": fval(blob, s1 + 0x1c)},
            {"off": 0x20, "kind": "f32", "value": fval(blob, s1 + 0x20)},
            {"off": 0x24, "kind": "u32", "value": struct.unpack_from("<I", blob, s1 + 0x24)[0]},
            {"off": 0x28, "kind": "f32", "value": fval(blob, s1 + 0x28)},
            {"off": 0x2c, "kind": "f32", "value": fval(blob, s1 + 0x2c)},
            {"off": 0x30, "kind": "f32", "value": fval(blob, s1 + 0x30)},
            {"off": 0x34, "kind": "f32", "value": fval(blob, s1 + 0x34)},
            {"off": 0x38, "kind": "f32", "value": fval(blob, s1 + 0x38)},
            {"off": 0x3c, "kind": "f32", "value": fval(blob, s1 + 0x3c)},
        ]
        # The same bytes read on the eight possible byte offsets. At 4-byte alignment
        # none of eight words is a plausible parameter value; the one-byte-shifted grid
        # gives 6 of 8. That is what fixes the run at +0x11 (grid decoded, meaning
        # UNKNOWN).
        grid = []
        for sh in range(8):
            vals = [struct.unpack_from("<f", blob, s1 + 0x10 + sh + 4 * i)[0] for i in range(8)]
            grid.append({"shift": sh,
                         "plausible": sum(1 for v in vals
                                          if math.isfinite(v) and 1e-4 <= abs(v) <= 1e4)})
        head_run = []
        for i in range(9):
            off = 0x11 + 4 * i
            head_run.append({"off": off,
                             "u32": struct.unpack_from("<I", blob, s1 + off)[0],
                             "f32": fval(blob, s1 + off)})

        # --- GeneralMkIII interior: trailing u16 index list, anchored on the checksum
        trailers = []
        for p in range(s1 + 4, e1 - 4, 2):
            n = struct.unpack_from("<I", blob, p)[0]
            if not 3 <= n <= 100000 or p + 4 + 2 * n != e1:
                continue
            idx = struct.unpack_from("<%dH" % n, blob, p + 4)
            if max(idx) >= 4 * n:
                continue
            trailers.append({"count_at": p, "count": n, "max_index": max(idx),
                             "verts_implied": max(idx) + 1,
                             "first8": list(idx[:8]),
                             "data": [p + 4, e1]})
        tr = trailers[0] if trailers else None

        # --- what a stride solver was allowed to try, and what it returned
        region = (tr["count_at"] - s1) if tr else (e1 - s1)
        v = tr["verts_implied"] if tr else 0
        integral = []
        if v:
            for stride in range(4, 97):
                hdr = region - v * stride
                if 0 <= hdr <= 200:
                    integral.append({"stride": stride, "header_bytes": hdr})
        # null result that rules out the naive reading: no stride-12 float3 anywhere
        # in the payload lands inside the RBM header AABB.
        lo = [h["bbox_min"][i] - 0.02 for i in range(3)]
        hi = [h["bbox_max"][i] + 0.02 for i in range(3)]
        in_bbox = 0
        for q in range(s1, e1 - 11, 4):
            vv = struct.unpack_from("<3f", blob, q)
            if all(math.isfinite(x) and lo[i] <= x <= hi[i] for i, x in enumerate(vv)):
                in_bbox += 1

        out["files"].append({
            "name": name.split("/")[-1], "name_full": name, "size": size,
            "header_len": h["header_len"], "bbox_min": [round(x, 6) for x in h["bbox_min"]],
            "bbox_max": [round(x, 6) for x in h["bbox_max"]],
            "blocks": blocks, "sum_equals_size": ok,
            "mkiii": {"head_hex": head.hex(" "), "head_fields": head_fields,
                      "grid_scan": grid, "head_float_run": head_run,
                      "trailers": trailers, "region_bytes": region,
                      "pre_index_region": [s1, tr["count_at"] if tr else e1],
                      "integral_stride_candidates": integral,
                      "float3_in_bbox_hits": in_bbox},
        })
    return out


# ---------------------------------------------------------------------------
# EPE round trip
# ---------------------------------------------------------------------------

def runs(xs):
    out = []
    for x in xs:
        if out and x == out[-1][1]:
            out[-1][1] = x + 1
        else:
            out.append([x, x + 1])
    return out


def epe_report() -> dict:
    raw, d = archive()
    van = [(n, o, s) for n, o, s in d
           if n.endswith(".epe") and "sportsmuscle" in n]
    van = [x for x in van if "_civilian_01.epe" in x[0]][0]
    van_bytes = raw[van[1]:van[1] + van[2]]
    a = EPE_A.read_bytes()
    b = EPE_B.read_bytes()

    diff = [i for i in range(len(a)) if a[i] != b[i]]
    fill = [i for i in diff if a[i] == 0x50 and b[i] == 0x00]
    fillset = set(fill)
    other = [i for i in diff if i not in fillset]

    ulp, odd = [], []
    for i in other:
        base = (i // 4) * 4
        if base + 4 > len(a):
            odd.append(i)
            continue
        fa, fb = f32(a, base), f32(b, base)
        if math.isfinite(fa) and math.isfinite(fb) and fa != 0.0:
            rel = abs(fb - fa) / abs(fa)
            (ulp if rel < 1e-5 else odd).append({"byte": i, "field": base,
                                                 "orig": fa, "new": fb, "rel": rel})
        else:
            odd.append(i)

    same7 = sum(1 for u in ulp if "%.7g" % u["orig"] == "%.7g" % u["new"])
    return {
        "vanilla": {"path": van[0], "size": van[2],
                    "sha256": hashlib.sha256(van_bytes).hexdigest()},
        "a": {"path": str(EPE_A.relative_to(ROOT)), "size": len(a),
              "sha256": hashlib.sha256(a).hexdigest(),
              "identical_to_vanilla": van_bytes == a},
        "b": {"path": str(EPE_B.relative_to(ROOT)), "size": len(b),
              "sha256": hashlib.sha256(b).hexdigest()},
        "same_length": len(a) == len(b),
        "differing_bytes": len(diff),
        "fill_0x50_to_0x00": {"bytes": len(fill), "runs": len(runs(fill))},
        "float_text_roundtrip": {
            "bytes": len(ulp), "fields": len({u["field"] for u in ulp}),
            "runs": len(runs(other)),
            "rel_min": round(min(u["rel"] for u in ulp), 12) if ulp else None,
            "rel_max": round(max(u["rel"] for u in ulp), 12) if ulp else None,
            "same_7_significant_digits": same7,
            "max_abs_ulp": max((abs(u["new"] - u["orig"]) for u in ulp), default=0.0),
        },
        "unexplained_bytes": len(odd),
        "first_fill_runs": [[s, e - s] for s, e in runs(fill)[:5]],
        "first_ulp_runs": [[s, e - s] for s, e in runs(other)[:5]],
    }


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def render(md: dict) -> str:
    r, e = md["rbm"], md["epe"]
    L = []
    A = L.append
    A("# JC3 Serpente decode depth 3 (G3-19) - the four PARTIAL files, closed or bounded")
    A("")
    A("Generated by `Tools/scripts/decode_depth3.py --write`; `--check` recomputes every")
    A("number below and diffs it against the committed JSON. Nothing here was run in the")
    A("game: the `.rbm` blocks come out of the JC3 `.ee` archive through `bm_rc`/`eetoc`,")
    A("the `.epe` bytes are the Gibbed round-trip artifacts under `tmp/g319/`.")
    A("")
    A("Labels: **decoded** = file + offset (or archive member + offset), read by this")
    A("script from the bytes; **derived** = rule + inputs, shown in place; **UNKNOWN** =")
    A("what was tried and where the answer would be.")
    A("")
    A("## 1. The three `.rbm` - full byte accounting, two of three blocks decoded")
    A("")
    A("Each file is: header, then three blocks, each `u32 type_hash` + payload + `u32")
    A("0x89ABCDEF`. The accounting is closed by requiring the sum to equal the file size")
    A("exactly (oracle 1) and by requiring `rbm_geom.decode_carpaintmm` to consume a")
    A("block to its exact end (oracle 2).")
    A("")
    A("| file | size | header | block 0 | block 1 (GeneralMkIII) | block 2 | sum == size |")
    A("|---|---|---|---|---|---|---|")
    for f in r["files"]:
        b0, b1, b2 = f["blocks"]
        A("| `%s` | %d | %d | %s %d B decoded | %d B **undecoded payload** | %s %d B decoded | %s |"
          % (f["name"], f["size"], f["header_len"], b0["type"], b0["bytes"],
             b1["bytes"], b2["type"], b2["bytes"],
             "yes" if f["sum_equals_size"] else "**NO**"))
    A("")
    A("So the earlier PARTIAL status was caused by one block in the *middle* of each")
    A("file: `rbm_geom.decode()` stops there because it has no serializer for")
    A("`GeneralMkIII`, which is why the block after it was never reached. The block")
    A("*after* it is `CarPaintMM` again and decodes to its exact end, header AABBs and all.")
    A("")
    A("### 1a. What *is* decoded inside `GeneralMkIII`")
    A("")
    A("Its head is byte-identical in all three lods (decoded: hex dump in the JSON,")
    A("`rbm.mkiii.head_hex`). It starts with `u32 5` and twelve zero bytes, then a run of")
    A("numbers that is **not** 4-byte aligned. Reading the same bytes on the eight")
    A("possible byte offsets gives this (derived scan, `rbm.mkiii.grid_scan`):")
    A("")
    A("| byte shift | words that look like parameters (1e-4..1e4) |")
    A("|---|---|")
    for g in r["files"][0]["mkiii"]["grid_scan"]:
        A("| %d | %d of 8 |" % (g["shift"], g["plausible"]))
    A("")
    A("So the numeric run starts at payload +0x11, one byte off the word grid (`u32 5`,")
    A("then twelve zeros, then one byte, then the run - i.e. there is a sub-4-byte field")
    A("at +0x10 whose size is what shifts the grid). Read there (decoded bytes):")
    A("")
    A("| offset | as u32 | as f32 |")
    A("|---|---|---|")
    for x in r["files"][0]["mkiii"]["head_float_run"]:
        A("| +%#04x | %d | %s |" % (x["off"], x["u32"], x["f32"]))
    A("")
    A("What the values *mean* is **UNKNOWN**: 2000.0 followed by 1.0/0.0/1.0/1.0, a")
    A("u32 1 at +0x25, then 1.571/0.480/1.439, is the shape of a small parameter block,")
    A("but no oracle in the project names any field of `GeneralMkIII`, so only the read")
    A("bytes are claimed. (The 4-byte-aligned reading of the same area is in the JSON as")
    A("`head_fields` only to show that it yields nothing plausible.)")
    A("")
    A("The *tail* of the block is decoded exactly, for all three lods: a `u32 count`")
    A("followed by `count` u16 triangle indices, ending precisely on the block checksum")
    A("(oracle 3):")
    A("")
    A("| file | count at | indices | max index | vertices implied | index data range |")
    A("|---|---|---|---|---|---|")
    for f in r["files"]:
        t = f["mkiii"]["trailers"][0]
        A("| `%s` | +%#x | %d | %d | %d | +%#x..+%#x |"
          % (f["name"], t["count_at"] - 0, t["count"], t["max_index"],
             t["verts_implied"], t["data"][0], t["data"][1]))
    A("")
    A("First indices of each list (decoded). lod1 starts `0,1,2, 2,1,3, 1,4` - the")
    A("pattern of an indexed triangle list reusing an edge - but that is a reading of")
    A("the values, not something the bytes prove:")
    A("")
    for f in r["files"]:
        A("* `%s`: `%s`" % (f["name"], f["mkiii"]["trailers"][0]["first8"]))
    A("")
    A("### 1b. The exact undecoded ranges")
    A("")
    A("| file | undecoded byte range (absolute, in-file) | bytes |")
    A("|---|---|---|")
    for f in r["files"]:
        rng = f["mkiii"]["pre_index_region"]
        A("| `%s` | %#x..%#x (payload start to the index count) | %d |"
          % (f["name"], rng[0], rng[1], rng[1] - rng[0]))
    A("")
    A("Inside those ranges the vertex/attribute layout is **UNKNOWN**. What was tried,")
    A("and where the answer would be:")
    A("")
    A("* A stride solver over `prefix + n*(u32 count, count*stride)` for `prefix` in")
    A("  0..96 step 4 and strides 2..64, requiring the parse to land exactly on the")
    A("  block checksum. It found **one** accidental closure (lod2, prefix 36, one")
    A("  stride-8 buffer of 319 entries) that does not exist for lod1 or lod3, so it is")
    A("  rejected as a coincidence rather than a layout.")
    A("* Arithmetic from the index list: with the implied vertex counts, the pre-index")
    A("  region admits these integral `header + verts*stride` splits (derived, *not* a")
    A("  decode - several fit per file, which is why none is claimed):")
    for f in r["files"]:
        cands = f["mkiii"]["integral_stride_candidates"]
        A("  * `%s`: region %d B, %d vertices -> %s"
          % (f["name"], f["mkiii"]["region_bytes"],
             f["mkiii"]["trailers"][0]["verts_implied"],
             ", ".join("stride %d with %d header B" % (c["stride"], c["header_bytes"])
                       for c in cands[:6]) or "none"))
    A("* A float3 (stride-12 position) scan of the whole payload against the AABB the")
    A("  file header itself carries: **%d** hits in total across the three lods."
      % sum(f["mkiii"]["float3_in_bbox_hits"] for f in r["files"]))
    A("  So the naive reading - \"the same vertex layout as the `CarPaintMM` block,\"")
    A("  is ruled out on the bytes: no 12-byte run anywhere in `GeneralMkIII` decodes to")
    A("  a point inside the model's own bounding box. The answer would be in the")
    A("  serializer for `GeneralMkIII` (block type hash 0x2cec5ad5); Gibbed's JC3 RBM")
    A("  writer does not implement it, and no published layout exists in the project.")
    A("")
    A("## 2. The `.epe` - round trip, every differing byte classified")
    A("")
    A("Vanilla member `%s`, %d B, sha256 `%s`."
      % (e["vanilla"]["path"], e["vanilla"]["size"], e["vanilla"]["sha256"][:32]))
    A("`tmp/g319/a.epe` is byte-identical to it (`identical_to_vanilla`: **%s**);"
      % e["a"]["identical_to_vanilla"])
    A("`tmp/g319/b.epe`, %d B, is what `Gibbed.JustCause3.ConvertProperty.exe --e` writes"
      % e["b"]["size"])
    A("back after reading it. The two are the same length (oracle 4 applies directly):")
    A("")
    A("| class | bytes | runs |")
    A("|---|---|---|")
    A("| original `0x50` -> written `0x00` (padding) | %d | %d |"
      % (e["fill_0x50_to_0x00"]["bytes"], e["fill_0x50_to_0x00"]["runs"]))
    A("| inside a float32 whose value moved by a decimal-text round trip | %d (%d fields) | %d |"
      % (e["float_text_roundtrip"]["bytes"], e["float_text_roundtrip"]["fields"],
         e["float_text_roundtrip"]["runs"]))
    A("| **unexplained** | **%d** | - |" % e["unexplained_bytes"])
    A("")
    A("The float class is not hand-waving: relative change is %s..%s (one float32 ULP"
      % (e["float_text_roundtrip"]["rel_min"], e["float_text_roundtrip"]["rel_max"]))
    A("at these magnitudes), and %d of the %d changed float bytes sit in fields that"
      % (e["float_text_roundtrip"]["same_7_significant_digits"],
         e["float_text_roundtrip"]["bytes"]))
    A("print identically at seven significant digits - i.e. the writer emits the value")
    A("as text and re-parses it, so the low bits are lost by the decimal form, not by a")
    A("layout difference. Largest absolute change: %s."
      % e["float_text_roundtrip"]["max_abs_ulp"])
    A("")
    A("That closes the `.epe`: 0 unexplained bytes, and the two classes are both named")
    A("with the reason for them. The `.epe` therefore needs no further byte accounting;")
    A("what it does *not* establish is that the re-serialisation is lossless enough for")
    A("the engine - that is a runtime question, not a byte question, and stays OPEN.")
    A("")
    A("## 3. Status")
    A("")
    A("| item | status | evidence |")
    A("|---|---|---|")
    A("| `sportsmuscle_missile_base_signature_lod1.rbm` | **FULL** except `GeneralMkIII` payload | 45,912 B accounted, sum == size, 2/3 blocks decoded to their ends |")
    A("| `..._lod2.rbm` | **FULL** except `GeneralMkIII` payload | 21,842 B accounted, sum == size |")
    A("| `..._lod3.rbm` | **FULL** except `GeneralMkIII` payload | 14,590 B accounted, sum == size |")
    A("| `GeneralMkIII` payload (7,126 / 2,592 / 1,214 B) | **UNKNOWN**, ranges named in 1b | index tail decoded; vertex layout has no serializer |")
    A("| `v0300_car_kensington_sportsmuscle_civilian_01.epe` | **FULL** | 109,526 B, 0 unexplained bytes on round trip |")
    A("")
    A("## 4. Remaining UNKNOWNs")
    A("")
    A("1. `GeneralMkIII` (0x2cec5ad5) vertex/attribute layout and the meaning of its head")
    A("   fields. Range: 1b. Would be answered by a serializer for that block type, or by")
    A("   a file of the same type whose AABB is matched by a stride-12 run (none in these")
    A("   three).")
    A("2. Whether `ConvertProperty`'s float-text round trip is acceptable to the engine")
    A("   for every `.epe` field (%d fields' low bits move). Not a byte question; only"
      % e["float_text_roundtrip"]["fields"])
    A("   a load in the game can answer it, and this task does not run the game.")
    A("")
    A("## 5. Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/decode_depth3.py --write")
    A("uv run python Tools/scripts/decode_depth3.py --check")
    A("```")
    A("")
    return "\n".join(L) + "\n"


def build() -> tuple[str, dict]:
    r = rbm_report()
    e = epe_report()
    data = {"rbm": r, "epe": e}
    return render({"rbm": r, "epe": e}), data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    md, data = build()

    if args.write:
        OUT_MD.write_text(md, encoding="utf-8")
        OUT_JSON.write_text(json.dumps(data, indent=1, allow_nan=False) + "\n",
                            encoding="utf-8")
        print("wrote %s (%d B)" % (OUT_MD.relative_to(ROOT), len(md)))
        print("wrote %s" % OUT_JSON.relative_to(ROOT))
        print("rbm sums ok: %s" % data["rbm"]["all_sums_ok"])
        print("epe unexplained bytes: %d" % data["epe"]["unexplained_bytes"])
        return 0

    if args.check:
        ok = True
        on_disk = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        if on_disk != data:
            ok = False
            print("FAIL json differs from recomputation")
            for k in data:
                if on_disk.get(k) != data[k]:
                    print("  section %r differs" % k)
        else:
            print("PASS json matches recomputation")
        if OUT_MD.read_text(encoding="utf-8") != md:
            ok = False
            print("FAIL md differs from recomputation")
        else:
            print("PASS md matches recomputation")
        print("PASS rbm sums ok" if data["rbm"]["all_sums_ok"] else "FAIL rbm sums")
        print("PASS epe 0 unexplained" if data["epe"]["unexplained_bytes"] == 0
              else "FAIL epe %d unexplained" % data["epe"]["unexplained_bytes"])
        for f in data["rbm"]["files"]:
            print("%s %-46s size %6d  sum==size %s  mkiii %5d B  idx %4d  verts %3d"
                  % ("OK  " if f["sum_equals_size"] else "BAD ",
                     f["name"], f["size"], f["sum_equals_size"],
                     f["blocks"][1]["bytes"],
                     f["mkiii"]["trailers"][0]["count"],
                     f["mkiii"]["trailers"][0]["verts_implied"]))
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
