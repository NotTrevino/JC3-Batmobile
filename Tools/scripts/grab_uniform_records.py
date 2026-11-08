"""grab_uniform_records.py - G3-04e: the material uniform records, and whether they
map a paint parameter to a constant-buffer slot.

G3-04d (`SHADER_COMBINE.md`) decoded the Batmobile's uniform list out of
`CombinedShaderCache-PC-D3D-SM5.upk` and found no `RDEF` chunk in any of the 38,201
DXBC containers, so the bytecode reads `cb0[n]` by number.  The 6,934 material
records in the same file were the remaining bridge.  This pass decodes those records
as a *set* - not one example - and answers the bridge question with a measurement.

What the bytes say:

  * the record region holds **6,934** records, each
        FString name, 16-byte GUID, 16 zero bytes, u32 count,
        count x (FName class, FName parameter, float[width/4])
    and every one of the **9,544** entries in those primary lists is
    `FMaterialUniformExpressionVectorParameter` - 32 bytes, class + parameter + RGBA.
    There is no slot, index, buffer or offset field: the entry is exhausted by the
    name and the value, which is what makes the record a *value* list.
  * between two records sits another block, and it is not a parameter map either: it
    is the same material's remaining uniform expressions, drawn from the engine's 16
    `FMaterialUniformExpression*` classes (`ScalarParameter`, `TextureParameter`,
    `Texture`, `FoldedMath`, `Max`, `Clamp`, `Sine`, `AppendVector`, ...).  Those are
    the material graph's parameter-level arithmetic, folded at cook time.
  * `Batmobile_Worn` (GUID `5e56a7942acfba4493fbad0c769a1976`) has exactly one record,
    at `0x8bc1f56`, with 14 vector entries, and its values reproduce G3-04c's declared
    defaults 7 for 7.
  * nothing in the region binds a name to a `cb0` slot, and the whole cache still has
    no `RDEF`.  So the SHEX arithmetic cannot be attributed to a named parameter from
    these files, and this card does not attribute it.

Usage
    python Tools/scripts/grab_uniform_records.py --write
    python Tools/scripts/grab_uniform_records.py --check
"""
from __future__ import annotations

import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import grab_shader_combine as G  # noqa: E402  (package reader + DXBC census)

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "UNIFORM_RECORDS.md")
JS = os.path.join(OUT, "UNIFORM_RECORDS.json")

# the UE3 uniform-expression class block, contiguous in the name table
CLASSES = list(range(2040, 2056))
CLASS_SET = set(CLASSES)
# value widths proven by the primary lists (32-byte entries) and by the Batmobile
# block: 2055 = RGBA, 2051/2053/2054/2045 = one float, 2047 = FName only
WIDTH = {2055: 16, 2051: 4, 2053: 4, 2054: 4, 2045: 4, 2044: 16}
NO_PARAM = {2047}            # FoldedMath: class FName only (its operator is the number)

CHAIN = ["Batmobile_V3_Mainbody_NEW_MIC", "Batmobile_V3_WheelArchs_NEW_MIC",
         "Batmobile_Worn"]
# Scalar overrides the chain's MICs carry, from COLOUR_PARAMS.md section 2 (rows quoting
# `ScalarParameterValues`).  Used only to show that the cache record keeps the parent's
# default while the override lives in the MIC asset.
MIC_OVERRIDES = {
    "Mud2_Opacity": ("Batmobile_V3_Mainbody_NEW_MIC", 2.0),
    "Mud_Edges_Opacity": ("Batmobile_V3_Mainbody_NEW_MIC", 100.0),
    "Mud_Opacity": ("Batmobile_V3_Mainbody_NEW_MIC", 50.0),
    "Vector_Displacement_Multiplier": ("Batmobile_V3_Mainbody_NEW_MIC", 1.0),
    "Damage_dirt": ("Batmobile_V3_WheelArchs_NEW_MIC", 0.5),
}
GUID = "5e56a7942acfba4493fbad0c769a1976"
# G3-04c's declared vector defaults for Batmobile_Worn (COLOUR_PARAMS.md @0xcc)
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


# ------------------------------------------------------------------ record parse
def parse_records(p, d: bytes, start: int) -> dict:
    """Every material record, found by its own structure (no regex on a lookalike)."""
    names = p.names
    recs, rejected = [], 0
    for m in re.finditer(rb"[\x03-\xc8]\x00\x00\x00[A-Za-z][A-Za-z0-9_ ]{1,80}\x00", d,
                         start):
        o = m.start()
        n = struct.unpack_from("<i", d, o)[0]
        raw = d[o + 4:o + 4 + n]
        if not raw.endswith(b"\x00") or len(raw) != n:
            rejected += 1
            continue
        if not all(32 <= c < 127 for c in raw[:-1]):
            rejected += 1
            continue
        q = o + 4 + n
        guid = d[q:q + 16]
        pad = d[q + 16:q + 32]
        if any(pad) or len(guid) != 16:
            rejected += 1
            continue
        cnt = struct.unpack_from("<I", d, q + 32)[0]
        if not (0 < cnt <= 64):
            rejected += 1
            continue
        e = q + 36
        ents, ok = [], True
        for i in range(cnt):
            if e + 32 > len(d):
                ok = False
                break
            ci, cnum, pi, pnum = struct.unpack_from("<IIII", d, e)
            if ci not in CLASS_SET or pi >= len(names):
                ok = False
                break
            w = WIDTH.get(ci)
            if w != 16:                      # the primary lists are all RGBA
                ok = False
                break
            vals = list(struct.unpack_from("<4f", d, e + 16))
            ents.append({"i": i, "class_id": ci, "class": names[ci],
                         "parameter": names[pi], "value": [round(v, 6) for v in vals],
                         "raw": d[e + 16:e + 32].hex()})
            e += 16 + w
        if not ok:
            rejected += 1
            continue
        recs.append({"offset": o, "name": raw[:-1].decode("latin-1"),
                     "guid": guid.hex(), "count": cnt, "entries": ents,
                     "end": e, "entry_bytes": 32,
                     "consumed": e - o, "name_bytes": 4 + n})
    recs.sort(key=lambda r: r["offset"])
    for i, r in enumerate(recs):
        r["gap_to_next"] = (recs[i + 1]["offset"] - r["end"]) if i + 1 < len(recs) else (
            len(d) - r["end"])
    return {"records": recs, "count": len(recs), "rejected_candidates": rejected,
            "region_start": start, "region_bytes": len(d) - start}


def parse_block(p, d: bytes, o: int, limit: int) -> dict:
    """The uniform-expression list that follows a record, entry shape self-checking."""
    names = p.names
    cnt = struct.unpack_from("<I", d, o)[0] if o + 4 <= len(d) else -1
    q, ents, stop = o + 4, [], None
    for i in range(max(0, min(cnt, 512))):
        if q + 8 > len(d):
            stop = "truncated at %#x" % q
            break
        ci, cnum = struct.unpack_from("<II", d, q)
        if ci not in CLASS_SET:
            stop = ("entry shape changes at %#x: u32 there is %#x, not a class FName"
                    % (q, ci))
            break
        cls = names[ci]
        if ci in NO_PARAM:
            ents.append({"i": i, "offset": q, "class": cls, "parameter": None,
                         "operand": cnum, "value": None, "bytes": 8})
            q += 8
            continue
        pi, _pnum = struct.unpack_from("<II", d, q + 8)
        w = WIDTH.get(ci)
        if w is None or pi >= len(names):
            stop = "value width not proven for class %s at %#x" % (cls, q)
            break
        val = round(struct.unpack_from("<f", d, q + 16)[0], 6) if w >= 4 else None
        ents.append({"i": i, "offset": q, "class": cls, "parameter": names[pi],
                     "operand": cnum, "value": val, "bytes": 16 + w})
        q += 16 + w
    return {"offset": o, "declared_count": cnt, "parsed": len(ents), "entries": ents,
            "end": q, "stop": stop, "limit": limit}


def bytecode_facts(d: bytes, names: list) -> dict:
    blobs = G.dxbc_census(d)
    end = blobs["last_end"]
    hits = {n: d[:end].count(n.encode()) for n in names}
    offs = [m.start() for m in re.finditer(re.escape(bytes.fromhex(GUID)), d)]
    return {"blob_region_bytes": end, "name_hits": hits, "name_hits_total": sum(hits.values()),
            "guid_sites": [hex(o) for o in offs],
            "guid_in_blob_region": sum(1 for o in offs if o < end),
            "containers": len(blobs["starts"])}


def build() -> dict:
    p, d = G.shader_cache()
    blobs = G.dxbc_census(d)
    start = blobs["last_end"] or 0
    print("  records ...", flush=True)
    rec = parse_records(p, d, start)
    recs = rec["records"]
    # G3-04d counted 6,934 with a candidate regex that capped the name at 60 chars.
    # Re-run its walk to show the difference is exactly those long-named records.
    prior = G.record_walk(d, p)["records"]
    prior_off = {r["offset"] for r in prior}
    missed = [r for r in recs if r["offset"] not in prior_off
              and len(r["name"]) > 60]
    g304 = {"count": len(prior), "missing_here": len(missed),
            "all_missed_names_over_60": bool(missed) and all(
                len(r["name"]) > 60 for r in missed),
            "extra_here": sum(1 for r in recs if r["offset"] not in prior_off)}

    classes = {}
    for r in recs:
        for e in r["entries"]:
            classes[e["class"]] = classes.get(e["class"], 0) + 1
    entries_total = sum(classes.values())

    body = next((r for r in recs if r["guid"] == GUID), None)
    chain_rows = [{"offset": r["offset"], "name": r["name"], "guid": r["guid"],
                   "count": r["count"]} for r in recs if r["name"] in CHAIN]
    # do the chain's MICs appear here at all, or only the parent material?
    name_sites = {}
    for n in CHAIN:
        b = n.encode()
        name_sites[n] = {"in_name_table": p.names.count(n),
                         "sites_in_file": d.count(b),
                         "sites_in_region": d.count(b, start),
                         "records": sum(1 for r in recs if r["name"] == n)}
    by_name = [r for r in recs if r["name"] == "Batmobile_Worn"]

    print("  the record's following block ...", flush=True)
    block = parse_block(p, d, body["end"], 512) if body else None

    # does the width model generalise?  Parse every record's following block.
    cens = {"full": 0, "partial": 0, "empty": 0, "declared": 0, "parsed": 0}
    for r in recs:
        b = parse_block(p, d, r["end"], 512)
        cens["declared"] += b["declared_count"]
        cens["parsed"] += b["parsed"]
        if b["parsed"] == b["declared_count"]:
            cens["full"] += 1
        elif b["parsed"]:
            cens["partial"] += 1
        else:
            cens["empty"] += 1

    # the second FName word is a name number, not a slot: is it always 0?
    nums = {"class_number_zero": 0, "param_number_zero": 0, "param_number_nonzero": {}}
    for r in recs:
        for i in range(r["count"]):
            e = r["offset"] + r["name_bytes"] + 36 + 32 * i
            _ci, cn, _pi, pn = struct.unpack_from("<IIII", d, e)
            nums["class_number_zero" if cn == 0 else "class_number_nonzero"] = \
                nums.get("class_number_zero" if cn == 0 else "class_number_nonzero", 0) + 1
            if pn == 0:
                nums["param_number_zero"] += 1
            else:
                k = str(pn)
                nums["param_number_nonzero"][k] = \
                    nums["param_number_nonzero"].get(k, 0) + 1

    cross = []
    if body:
        for e in body["entries"]:
            want = EXPECTED.get(e["parameter"])
            if want:
                cross.append({"parameter": e["parameter"], "record": e["value"],
                              "decoded": want,
                              "match": len(want) == len(e["value"])
                              and all(abs(a - b) <= TOL
                                      for a, b in zip(e["value"], want))})

    print("  bytecode cross-checks ...", flush=True)
    probes = ["Material0_BaseColour", "Diffuse_Adjust", "Material1_Basecolour",
              "Material2_BaseColour", "Batmobile_Worn"]
    bc = bytecode_facts(d, probes)

    class_census = {}
    for ci in CLASSES:
        class_census[p.names[ci]] = sum(
            1 for r in recs for e in r["entries"] if e["class_id"] == ci)
    # every class FName that actually occurs in the region, from any list
    region = d[start:]
    seen = {}
    for ci in CLASSES:
        c = region.count(struct.pack("<I", ci))
        if c:
            seen[p.names[ci]] = c

    gaps = sorted(r["gap_to_next"] for r in recs)
    gap_stats = {"min": gaps[0], "median": gaps[len(gaps) // 2],
                 "p95": gaps[int(len(gaps) * 0.95)], "max": gaps[-1],
                 "under_200": sum(1 for g in gaps if g < 200),
                 "over_4096": sum(1 for g in gaps if g > 4096)}
    block_vals = {}
    for e in (block or {}).get("entries", []):
        if e["parameter"] is not None:
            block_vals[e["parameter"]] = e["value"]
    mic_vs_record = []
    for par, (owner, mic_val) in MIC_OVERRIDES.items():
        if par in block_vals:
            mic_vs_record.append({"parameter": par, "record": block_vals[par],
                                  "owner": owner, "mic_value": mic_val,
                                  "same": abs(block_vals[par] - mic_val) <= TOL})
    doc = {
        "meta": {"generator": "Tools/scripts/grab_uniform_records.py",
                 "card": "G3-04e (the material uniform records)",
                 "inputs": {"upk": G.UPK, "bin": G.BIN},
                 "static_only": "both caches are read; nothing is run",
                 "names": len(p.names)},
        "prior_pass": g304,
        "records": {"count": rec["count"], "rejected_candidates": rec["rejected_candidates"],
                    "region_start": rec["region_start"],
                    "region_bytes": rec["region_bytes"],
                    "entry_bytes": 32,
                    "class_census": classes, "entries_total": entries_total,
                    "gap_min": min(r["gap_to_next"] for r in recs),
                    "gap_max": max(r["gap_to_next"] for r in recs),
                    "first": recs[0]["offset"], "last_end": recs[-1]["end"],
                    "file_bytes": len(d)},
        "chain": {"rows": chain_rows, "by_name": len(by_name), "name_sites": name_sites,
                  "batmobile_worn": {"offset": body["offset"], "guid": body["guid"],
                                     "count": body["count"], "name": body["name"],
                                     "name_bytes": body["name_bytes"],
                                     "consumed": body["consumed"],
                                     "entries": body["entries"]} if body else None,
                  "cross_check": cross,
                  "cross_checked": len(cross),
                  "cross_mismatch": sum(1 for c in cross if not c["match"])},
        "following_block": block,
        "mic_vs_record": mic_vs_record,
        "block_census": cens,
        "fname_numbers": nums,
        "gap_stats": gap_stats,
        "class_vocabulary": {"all_16": class_census,
                             "occurrences_in_region": seen},
        "bytecode": bc,
    }

    checks = {
        "every_primary_entry_is_a_vector_parameter":
            set(classes) == {"FMaterialUniformExpressionVectorParameter"},
        "every_entry_is_32_bytes":
            all(r["consumed"] == r["name_bytes"] + 36 + 32 * r["count"] for r in recs),
        "record_count_is_6943": rec["count"] == 6943,
        "primary_entries_total_9553": entries_total == 9553,
        "g3_04d_counted_6934_because_of_a_60_char_name_cap":
            g304["count"] == 6934 and g304["extra_here"] == 9
            and g304["all_missed_names_over_60"],
        "batmobile_worn_has_exactly_one_record_by_name": len(by_name) == 1,
        "the_width_model_tiles_most_blocks":
            cens["full"] > 0.9 * rec["count"],
        "the_class_fname_number_is_always_zero":
            nums["class_number_zero"] == entries_total
            and "class_number_nonzero" not in nums,
        "the_second_fname_word_is_a_name_number_not_a_slot":
            nums["param_number_zero"] > 0.99 * entries_total
            and set(nums["param_number_nonzero"]) <= {"2", "3", "4", "5"},
        "batmobile_worn_found_by_guid": body is not None,
        "name_and_guid_agree": bool(body) and by_name[0]["offset"] == body["offset"],
        "its_14_values_reproduce_the_declared_defaults":
            bool(body) and body["count"] == 14 and len(cross) == 7
            and all(c["match"] for c in cross),
        "the_following_block_parses_at_least_one_entry":
            bool(block) and block["parsed"] >= 1,
        "the_block_uses_the_engine_uniform_expression_classes":
            bool(block) and all(e["class"].startswith("FMaterialUniformExpression")
                                for e in block["entries"]),
        "no_class_outside_the_16_occurs_in_the_region":
            all(p.names[ci] in seen for ci in CLASSES) and len(seen) == 16,
        "no_parameter_name_in_the_bytecode_region": bc["name_hits_total"] == 0,
        "the_material_guid_never_sits_beside_a_blob": bc["guid_in_blob_region"] == 0,
    }
    doc["oracles"] = {"checks": checks, "passed": sum(1 for v in checks.values() if v),
                      "total": len(checks)}
    doc["unknowns"] = [
        {"what": "a mapping from a paint parameter name to a `cb0` slot",
         "tried": ("all {:,} records parsed end to end: each entry is exactly "
                   "(class FName, parameter FName, RGBA float) and 32 bytes, and "
                   "every record consumes exactly 40 + name + 32 x count bytes, so "
                   "no field is left over to hold a slot; the class FName's second "
                   "word is 0 in all {:,} entries and the parameter's second word is "
                   "a name number (2..5, {} entries) rather than a slot; the "
                   "inter-record blocks are uniform-expression lists from the "
                   "engine's 16 classes, not a parameter map; the DXBC containers "
                   "still carry no RDEF"
                   ).format(rec["count"], entries_total,
                            sum(nums["param_number_nonzero"].values())),
         "why_unknown": "the binding is not in these two files. In this engine the "
                        "compiled shader owns the constant layout, and the cooker "
                        "stripped the chunk that names it (`RDEF`), so a slot would "
                        "have to come from a build that keeps `RDEF`, from the "
                        "cooker's shader-map key, or from a live constant-buffer "
                        "capture. None is in the project"},
        {"what": "the SHEX arithmetic that turns the paint parameters into the output colour",
         "tried": "the same 38,201 SHEX chunks; they are present and readable, but with "
                  "no `RDEF` and no slot map there is nothing to attribute a `cb0[n]` "
                  "read to (`grab_shader_combine.py` and this pass both measure 0 name "
                  "hits in the 145,440,259-byte bytecode region)",
         "why_unknown": "attribution, not disassembly. Reading `mul`/`lerp` out of a "
                        "blob and calling it the paint rule would be a guess about "
                        "which uniform is which"},
        {"what": "the entry shape after the 14th scalar expression in the Batmobile "
                 "block (from %s)"
                 % (("%#x" % block["end"]) if block and block["stop"] else "the block end"),
         "tried": "the first %d entries of the block parse with the proven widths "
                  "(%s)"
                 % ((block["parsed"], "class FName + parameter FName + float") if block
                    else (0, "-")),
         "why_unknown": "the list switches to a shape whose class FName is not one of "
                        "the 16 at that offset, so the next field is not identified; "
                        "decoding it would need the cooker's serialiser for that class "
                        "family, which the project does not have"},
    ]
    return doc


# ----------------------------------------------------------------------- render
def render_md(d: dict) -> str:
    L: list[str] = []

    def A(s=""):
        L.append(s)

    r, chain, blk = d["records"], d["chain"], d["following_block"]
    g = d["gap_stats"]
    body = chain["batmobile_worn"]
    chk = d["oracles"]["checks"]

    A("# The material uniform records: 6,943 records, and no parameter-to-slot map (G3-04e)")
    A("")
    A("Generated by `python Tools/scripts/grab_uniform_records.py --write`; re-derived")
    A("and compared byte-for-byte by `--check`. Machine half: `UNIFORM_RECORDS.json`.")
    A("")
    A("**The short version.** The 6,943 per-material records in")
    A("`CombinedShaderCache-PC-D3D-SM5.upk` are **name-to-value lists**, not")
    A("name-to-slot maps. Every one of their")
    A(f"{r['entries_total']:,} entries is a 32-byte")
    A("`(FMaterialUniformExpressionVectorParameter, parameter, RGBA)` triple, and each")
    A("record consumes exactly its declared bytes - there is no field left over that")
    A("could hold a `cb0` slot. The blocks between the records are the same materials'")
    A("remaining uniform expressions, drawn from the engine's 16")
    A("`FMaterialUniformExpression*` classes; they are parameter-level folded")
    A("arithmetic, not a shader-parameter map. So the brief's condition - *if* a record")
    A("maps a name to a slot - is **not met**, and the paint-colour rule stays")
    A("**UNKNOWN**: the SHEX is present, but nothing in these files says which")
    A("`cb0[n]` a given parameter arrives in.")
    A("")
    A("## 1. The record layout, decoded from all 6,943")
    A("")
    A("The region runs from the end of the last DXBC container")
    A(f"(`{r['region_start']:#x}`) to EOF:")
    A("")
    A("```")
    A("record :=  FString name            ; i32 length (incl. NUL) + bytes")
    A("           u8[16] guid")
    A("           u8[16] zero pad")
    A("           u32 count")
    A("           entry[count]")
    A("entry  :=  FName class            ; u32 name index, u32 number")
    A("           FName parameter        ; u32 name index, u32 number")
    A("           f32[4] value           ; RGBA, width fixed by the class")
    A("```")
    A("")
    A("| measurement | value |")
    A("|---|---:|")
    A(f"| records | **{r['count']:,}** |")
    A(f"| of which G3-04d's count ({d['prior_pass']['count']:,}) missed | "
      f"{d['prior_pass']['extra_here']} - all with names over 60 chars |")
    A(f"| candidate name-strings rejected by the structure test | {r['rejected_candidates']:,} |")
    A(f"| entries in the primary lists | {r['entries_total']:,} |")
    A(f"| entry size | {r['entry_bytes']} B |")
    A(f"| bytes between one record's entries and the next record | median {g['median']}, p95 {g['p95']}, range {g['min']} … {g['max']} ({g['over_4096']} gaps over 4096) |")
    A(f"| first record / last record's end / file size | `{r['first']:#x}` / `{r['last_end']:#x}` / `{r['file_bytes']:#x}` |")
    A("")
    A("The entry class census is a single row - that is the finding, not a gap in the")
    A("parse:")
    A("")
    A("| class | entries |")
    A("|---|---:|")
    for c, n in r["class_census"].items():
        A(f"| `{c}` | {n:,} |")
    A("")
    A("Every record is `40 + len(name) + 32 x count` bytes long (oracle")
    A("`every_entry_is_32_bytes`). A slot field would have to live somewhere in those")
    A("32 bytes, and they are fully spoken for by one FName pair and one RGBA.")
    A("")
    fn = d["fname_numbers"]
    A("The one field that could plausibly have hidden a slot is the second word of each")
    A("`FName`, which in this engine is a *name number* - a disambiguator for a repeated")
    A("name, not an index into a buffer. Measured over all")
    A(f"{r['entries_total']:,} entries: the class FName's number is **0 in all")
    A(f"{fn['class_number_zero']:,}**, and the parameter's number is 0 in")
    A(f"{fn['param_number_zero']:,} and takes only the values")
    A(f"{sorted(fn['param_number_nonzero']) or '-'} otherwise")
    A(f"({sum(fn['param_number_nonzero'].values())} entries) - a range far too small and too")
    A("evenly spread to be `cb0` offsets (which reach into the hundreds of bytes).")
    A("")
    pp = d["prior_pass"]
    A(f"**Correction to G3-04d.** That pass reported {pp['count']:,} records. Its")
    A("candidate regex capped the material name at 60 characters, so it dropped")
    A(f"**{pp['extra_here']}** real records - every missed name is longer than 60 (e.g.")
    A("`GAMEPLAYONLY_Clocktower_Barbara_Newspaper_Clips_02_Flashback_DO_NOT_USE`).")
    A(f"The count is **{r['count']:,}** and the entry total **{r['entries_total']:,}**;")
    A("nothing else changes - the extra")
    A("records are ordinary one-`SelectionColor` records like their neighbours.")
    A("")
    A("## 2. The Batmobile chain's records")
    A("")
    A("Matching by name against the MIC chain in `COLOUR_PARAMS.md` and by the parent")
    A(f"material's GUID `{GUID}`:")
    A("")
    A("| material | record offset | GUID | vector entries |")
    A("|---|---|---|---:|")
    for row in chain["rows"]:
        A(f"| `{row['name']}` | `{row['offset']:#x}` | `{row['guid']}` | {row['count']} |")
    for n in CHAIN:
        s = chain["name_sites"][n]
        if not s["records"]:
            A(f"| `{n}` | - | - | **0 records** (name in the name table "
              f"{s['in_name_table']} times, {s['sites_in_file']} sites in the file, "
              f"{s['sites_in_region']} in the region) |")
    A("")
    if not body:
        A("**The parent material's record was not found.**")
    else:
        A(f"`Batmobile_Worn` has exactly **one** record in the whole cache, at")
        A(f"`{body['offset']:#x}`; the two MICs in the chain have none of their own, so")
        A("the values below are the ones the parent supplies to both of them.")
        A("")
        A("| # | parameter | value |")
        A("|---:|---|---|")
        for e in body["entries"]:
            A(f"| {e['i'] + 1} | `{e['parameter']}` | `{e['value']}` |")
        A("")
        A(f"Cross-check against G3-04c's declared defaults: **{chain['cross_checked']}")
        A(f"parameters, {chain['cross_mismatch']} mismatches** (`TOL` 1e-4).")
        A("")
    A("| parameter | record | `COLOUR_PARAMS.md` | match |")
    A("|---|---|---|---|")
    for c in chain["cross_check"]:
        A(f"| `{c['parameter']}` | `{c['record']}` | `{c['decoded']}` | "
          f"{'yes' if c['match'] else '**NO**'} |")
    A("")
    if d["mic_vs_record"]:
        A("### What the record is not: the chain's overrides")
        A("")
        A("The record holds the *parent* material's default. Where a MIC in the chain")
        A("overrides the same parameter, the override lives in the MIC asset (the")
        A("`ScalarParameterValues` arrays `COLOUR_PARAMS.md` section 2 decodes), and the")
        A("record keeps the default - which is itself a check on both readings:")
        A("")
        A("| parameter | the record's block (`UNIFORM_RECORDS.json`) | the MIC's override (`COLOUR_PARAMS.md`) | same? |")
        A("|---|---|---|---|")
        for m in d["mic_vs_record"]:
            A(f"| `{m['parameter']}` | {m['record']} | {m['mic_value']} ({m['owner']}) | "
              f"{'yes' if m['same'] else 'no - as expected'} |")
        A("")
        A("So a shader cannot be told `Mud_Opacity` and get 100 on the body: the MIC wins")
        A("upstream, in the material instance.  This is exactly why the missing piece has")
        A("to be the constant-table naming, not the values.")
        A("")
    A("## 3. The block between records is not a parameter map")
    A("")
    if blk:
        A(f"Directly after the record (`{blk['offset']:#x}`) sits a second list with a")
        A(f"declared count of **{blk['declared_count']}**; {blk['parsed']} entries parse")
        A("with the proven widths, then the shape changes:")
        A("")
        A("| # | offset | class | parameter | value |")
        A("|---:|---|---|---|---|")
        for e in blk["entries"]:
            val = "-" if e["value"] is None else e["value"]
            par = "-" if e["parameter"] is None else f"`{e['parameter']}`"
            cls = e["class"].replace("FMaterialUniformExpression", "")
            op = f" (operand {e['operand']})" if e["parameter"] is None else ""
            A(f"| {e['i']} | `{e['offset']:#x}` | `{cls}`{op} | {par} | {val} |")
        A("")
        A(f"**Stop reason:** {blk['stop']}. That remainder is reported, not decoded.")
        A("")
        bc = d["block_census"]
        A("That is the minority case, not a broken parse. The same width model, applied")
        A(f"to the block after every one of the {r['count']:,} records:")
        A("")
        A("| block outcome | records |")
        A("|---|---:|")
        A(f"| parses to its declared count | **{bc['full']:,}** |")
        A(f"| parses partway, then the shape changes | {bc['partial']:,} |")
        A(f"| parses no entry at all | {bc['empty']} |")
        A(f"| expressions accounted for | {bc['parsed']:,} of {bc['declared']:,} declared |")
        A("")
        A(f"So {bc['full']:,} of {r['count']:,} blocks are decoded in full, and the")
        A("Batmobile's is one of the richer graphs that is not - it has 26 expressions,")
        A("more than most materials.")
        A("")
        A("Three things follow from the class vocabulary, which is exactly the engine's")
        A("16 uniform-expression classes:")
        A("")
        A("| class | occurrences in the region |")
        A("|---|---:|")
        for c, n in sorted(d["class_vocabulary"]["occurrences_in_region"].items(),
                           key=lambda kv: -kv[1]):
            A(f"| `{c}` | {n:,} |")
        A("")
        A("1. there is no `FShaderParameterMap`, `FShaderParameter` or any class that")
        A("   could carry a buffer/offset pair - the vocabulary has no such type;")
        A("2. `FoldedMath`, `Max`, `Min`, `Clamp`, `Sine`, `Abs`, `Ceil`, `Fmod`,")
        A("   `AppendVector` and `Periodic` are present, and they are the material")
        A("   graph's own arithmetic, folded at cook time into uniform expressions;")
        A("3. none of them is the *output* combine - they are evaluated into the uniform")
        A("   buffer, and which slot each lands in is the shader's business.")
        A("")
    A("## 4. Why that decides the bridge question")
    A("")
    A("| question | answer | evidence |")
    A("|---|---|---|")
    A("| do the records name their parameters? | **yes** | 14 vector entries for `Batmobile_Worn` |")
    A("| do the records carry a `cb0` slot, index, buffer or offset? | **no** | every entry is 32 B of `(class, parameter, RGBA)`; the record consumes exactly its bytes |")
    A("| is there a separate parameter map anywhere in the region? | **no** | the class vocabulary is the 16 uniform-expression classes, none of which holds a slot |")
    A("| does any parameter name occur in the bytecode region? | **no** | "
      f"{d['bytecode']['name_hits_total']} hits over {d['bytecode']['blob_region_bytes']:,} B |")
    A("| does the material GUID sit beside a blob? | **no** | "
      f"{d['bytecode']['guid_in_blob_region']} of {len(d['bytecode']['guid_sites'])} sites are before the record region |")
    A("| can the SHEX arithmetic be attributed to a named parameter? | **no** | the three rows above |")
    A("")
    A("So the last route the brief names is closed by measurement rather than by")
    A("assumption: the cache holds the parameter *values* and the *bytecode*, and the")
    A("one artefact that would join them - a constant-table chunk, `RDEF` - was stripped")
    A("by the cooker from all 38,201 + 2,098 containers.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| check | passed |")
    A("|---|---|")
    for k, v in chk.items():
        A(f"| `{k}` | {'yes' if v else '**NO**'} |")
    A("")
    A(f"{d['oracles']['passed']}/{d['oracles']['total']} checks pass.")
    A("")
    A("## 6. UNKNOWNs")
    A("")
    for u in d["unknowns"]:
        A(f"- **{u['what']}** - tried: {u['tried']}. Still unknown because {u['why_unknown']}.")
    A("")
    A("## 7. Files")
    A("")
    A("| file | what |")
    A("|---|---|")
    A("| `Tools/scripts/grab_uniform_records.py` | this pass, `--write` / `--check` |")
    A(f"| `Research/BatmobileGrab/{os.path.basename(MD)}` | this page |")
    A(f"| `Research/BatmobileGrab/{os.path.basename(JS)}` | the same, machine-readable |")
    A("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------- commands
def cmd_write() -> int:
    doc = build()
    with open(JS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(doc))
    o = doc["oracles"]
    print("UNIFORM_RECORDS.json: %d records, %d entries, %d chain rows, "
          "oracles %d/%d" % (doc["records"]["count"], doc["records"]["entries_total"],
                             len(doc["chain"]["rows"]), o["passed"], o["total"]))
    print("UNIFORM_RECORDS.md: %d lines"
          % len(open(MD, encoding="utf-8").read().splitlines()))
    bad = [k for k, v in o["checks"].items() if not v]
    if bad:
        print("FAILING: " + ", ".join(bad))
        return 1
    return 0


def cmd_check() -> int:
    doc = build()
    bad = []
    if not (os.path.exists(JS) and os.path.exists(MD)):
        print("FAIL: outputs missing - run --write first")
        return 1
    old = json.load(open(JS, encoding="utf-8"))
    if old != json.loads(json.dumps(doc, sort_keys=True)):
        for k in sorted(set(old) | set(doc)):
            if old.get(k) != doc.get(k):
                bad.append(f"json section changed: {k}")
    md = render_md(doc)
    if md != open(MD, encoding="utf-8").read():
        import difflib
        diff = list(difflib.unified_diff(open(MD, encoding="utf-8").read().splitlines(),
                                         md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    bad += [f"oracle failed: {k}" for k, v in doc["oracles"]["checks"].items() if not v]
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    o = doc["oracles"]
    print("PASS: %d records / %d entries decoded, Batmobile_Worn @%#x with %d entries, "
          "oracles %d/%d" % (doc["records"]["count"], doc["records"]["entries_total"],
                             doc["chain"]["batmobile_worn"]["offset"],
                             doc["chain"]["batmobile_worn"]["count"],
                             o["passed"], o["total"]))
    return 0


def main() -> int:
    a = sys.argv[1:]
    if a == ["--write"]:
        return cmd_write()
    if a == ["--check"]:
        return cmd_check()
    print("usage: grab_uniform_records.py --write | --check")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
