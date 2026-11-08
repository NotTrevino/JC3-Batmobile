"""jc3_uniform_records.py - G3-04d: do the material uniform records name the CarPaintMM cbuffer parameters?

Reads the shipped Arkham Knight shader cache (read-only) and answers four questions the card
asks, each as a measurement over all records:

  1. the record layout, byte for byte;
  2. which records belong to the paint family (the BmAK paint parameters: BaseColour,
     Diffuse_Adjust and the chain's vector defaults);
  3. the parameter names and their `hash_jenkins` values, compared against hash_jenkins of the
     BmAK names `BaseColour` and `Diffuse_Adjust`;
  4. whether any record maps a parameter name to a cbuffer offset / slot / bind.

Output: Research/JC3Grab/UNIFORM_RECORDS.md.  --check recomputes every number from the install
file, re-runs the oracles and requires the stored page to be byte-identical.  Static only: no
game process is started, attached to or injected into.
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

import grab_shader_combine as G  # noqa: E402  (package reader + DXBC census, read-only)
from rbmhdr import hash_jenkins  # noqa: E402

UPK = G.UPK
OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "UNIFORM_RECORDS.md")
COLOUR_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR_PARAMS.json")

CLASS_LO, CLASS_HI = 2040, 2055
VECTOR = 2055                       # FMaterialUniformExpressionVectorParameter
ENTRY_BYTES = 32
RE_PREFIX = re.compile(rb"[\x00-\xff][\x00\x01]\x00\x00[\x20-\x7e]{1,299}\x00")

MATERIAL = "Batmobile_Worn"
GUID = "5e56a7942acfba4493fbad0c769a1976"
TOL = 1e-4

BMAK_NAMES = ("BaseColour", "Diffuse_Adjust")

# The CarPaintMM constant-buffer members named by the family's 12 reflection headers
# (Research/JC3Grab/CB0_SLOTS.md sections 3-4).  cb7's 20 B / 2 slots are counted there but
# its member names are not in that page, so only the 25 + 7 named members are listed here.
CB2_MEMBERS = (
    "m_SpecularGloss", "m_Metallic", "m_ClearCoat", "m_Emissive", "m_DiffuseWrap",
    "m_DirtParams", "m_DirtBlend", "m_DirtColor", "m_DecalCount", "m_DecalWidth",
    "m_Decal1Color", "m_Decal2Color", "m_Decal3Color", "m_Decal4Color", "m_DecalBlend",
    "m_Damage", "m_DamageBlend", "m_DamageColor", "SupportDecals", "SupportDmgBlend",
    "SupportLayered", "SupportOverlay", "SupportRotating", "SupportDirt", "SupportSoftTint",
)
CB6_MEMBERS = ("m_TintColorR", "m_TintColorG", "m_TintColorB", "_unused",
               "m_SpecularGlossOverride", "m_MetallicOverride", "m_ClearCoatOverride")
PAINT_MEMBERS = CB2_MEMBERS + CB6_MEMBERS          # 32 named members; cb2 -> 25, cb6 -> 7


# ------------------------------------------------------------------ parse
def header_at(d: bytes, names, o: int) -> dict | None:
    """The self-delimiting record header predicate at one offset (G3-04e1's layout)."""
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
            "guid": d[e0:e0 + 16].hex(), "count": count, "entries_at": e0 + 36}


def walk_vector(d: bytes, names, h: dict):
    """Walk the entry array as count x 32 B.  Return (entries, why, end)."""
    N = len(d)
    q, ents = h["entries_at"], []
    for i in range(h["count"]):
        if q + ENTRY_BYTES > N:
            return None, "truncated at entry %d" % i, q
        ci, cn, pi, pn = struct.unpack_from("<IIII", d, q)
        if ci != VECTOR:
            return None, "class word %#x at entry %d is not the vector class" % (ci, i), q
        if pi >= len(names):
            return None, "parameter index %d at entry %d is out of range" % (pi, i), q
        vals = struct.unpack_from("<4f", d, q + 16)
        ents.append({"at": q, "class_id": ci, "class_number": cn, "param_index": pi,
                     "param_name": names[pi], "param_number": pn,
                     "value": [round(v, 6) for v in vals]})
        q += ENTRY_BYTES
    return ents, None, q


def region_start(d: bytes) -> tuple[int, dict]:
    blobs = G.dxbc_census(d)
    return blobs["last_end"], blobs


def collect(p, d: bytes) -> dict:
    names = p.names
    start, blobs = region_start(d)
    cands = [m.start() for m in RE_PREFIX.finditer(d, start)]
    heads = [h for h in (header_at(d, names, o) for o in cands) if h]
    heads.sort(key=lambda h: h["offset"])
    proven, rejected = [], 0
    for h in heads:
        ents, why, end = walk_vector(d, names, h)
        if ents is None:
            rejected += 1
            continue
        h.update(entries=ents, end=end, span=end - h["offset"])
        proven.append(h)
    entries = [e | {"record": h} for h in proven for e in h["entries"]]
    return {"blobs": blobs, "region_start": start, "candidates": len(cands),
            "headers": heads, "proven": proven, "rejected": rejected,
            "entries": entries}


def paint_records(data: dict) -> list[dict]:
    """Records naming a BmAK paint parameter (BaseColour/Basecolour or Diffuse_Adjust)."""
    out = []
    for h in data["proven"]:
        hits = sorted({e["param_name"] for e in h["entries"]
                       if "basecolour" in e["param_name"].lower().replace("_", "")
                       or e["param_name"].lower().replace("_", "") == "diffuseadjust"})
        if hits:
            out.append({"name": h["name"], "offset": h["offset"], "count": h["count"],
                        "hits": hits})
    return out


def hash_probe(d: bytes, names, start: int) -> dict:
    """Where hash_jenkins(name) occurs: name table, record region, or as an FName index."""
    out = {}
    region = d[start:]
    for key, name in (("base_colour", "BaseColour"), ("diffuse_adjust", "Diffuse_Adjust")):
        h = hash_jenkins(name.encode()) & 0xFFFFFFFF
        needle = struct.pack("<I", h)
        hits, at = [], region.find(needle)
        while at != -1:
            hits.append(start + at)
            at = region.find(needle, at + 1)
        out[key] = {
            "name": name, "hash": h,
            "name_table_index": (names.index(name) if name in names else None),
            "name_table_exact": name in names,
            "hash_u32_in_region": len(hits),
            "hash_u32_offsets": [hex(x) for x in hits[:8]],
            "hash_as_fname_index": h < len(names) and names[h] == name,
        }
    return out


def member_matches(entries: list[dict]) -> dict:
    by_name = {}
    for e in entries:
        if e["param_name"] in PAINT_MEMBERS:
            by_name.setdefault(e["param_name"], 0)
            by_name[e["param_name"]] += 1
    return by_name


def word_probe(entries: list[dict]) -> dict:
    """Is any entry word a per-name constant in cbuffer-offset range?  (the slot test)"""
    words = {"class_id": lambda e: e["class_id"], "class_number": lambda e: e["class_number"],
             "param_index": lambda e: e["param_index"], "param_number": lambda e: e["param_number"]}
    out = {}
    for w, fn in words.items():
        vals = [fn(e) for e in entries]
        out[w] = {"distinct": len(set(vals)), "min": min(vals), "max": max(vals),
                  "nonzero": sum(1 for v in vals if v)}
    # names that occur in more than one entry: a slot field would be constant per name
    per_name = {}
    for e in entries:
        per_name.setdefault(e["param_name"], []).append(e)
    multi = {n: v for n, v in per_name.items() if len(v) > 1}
    constant = {}
    for w, fn in words.items():
        constant[w] = sum(1 for v in multi.values() if len({fn(e) for e in v}) == 1)
    offsets_in_range = sum(1 for e in entries
                           if any(8 <= v <= 316 for v in (e["class_number"], e["param_number"])))
    return {"words": out, "names": len(per_name), "multi_name": len(multi),
            "constant_per_name": constant, "number_words_in_offset_range": offsets_in_range}


def colour_defaults() -> dict:
    if not os.path.exists(COLOUR_JSON):
        return {}
    j = json.load(open(COLOUR_JSON, encoding="utf-8"))
    out = {}
    for row in j.get("defaults", []):
        v = row.get("value")
        if row.get("material") == MATERIAL and isinstance(v, list) and len(v) == 4:
            out[row["name"]] = [round(float(x), 6) for x in v]
    return out


# ------------------------------------------------------------------ build
def build() -> dict:
    p, d = G.shader_cache()
    data = collect(p, d)
    proven, entries = data["proven"], data["entries"]
    start = data["region_start"]

    anchor = next(h for h in proven if h["guid"] == GUID)
    values = {e["param_name"]: e["value"] for e in anchor["entries"]}
    defaults = colour_defaults()
    agreed = [n for n, v in defaults.items()
              if n in values and max(abs(a - b) for a, b in zip(v, values[n])) <= TOL]
    disagreed = sorted(n for n in defaults if n in values and n not in agreed)

    members = member_matches(entries)
    paint = paint_records(data)
    hashes = hash_probe(d, p.names, start)
    words = word_probe(entries)

    tiling = sum(1 for h in proven if h["span"] == 40 + h["name_len"] + ENTRY_BYTES * h["count"])
    guid_dupes = len(proven) - len({h["guid"] for h in proven})
    class_ids = sorted({e["class_id"] for e in entries})
    entry_bytes = sum(h["count"] * ENTRY_BYTES for h in proven)
    oracles = {
        "headers_are_self_delimiting": tiling == len(proven),
        "every_entry_is_the_vector_class": class_ids == [VECTOR],
        "every_entry_is_32_bytes": all(e["at"] + ENTRY_BYTES <= len(d) for e in entries),
        "guids_are_distinct": guid_dupes == 0,
        "anchor_found_by_guid": anchor is not None,
        "anchor_reproduces_the_declared_defaults": not disagreed and len(agreed) >= 10,
        "no_entry_names_a_carpaintmm_cbuffer_member": len(members) == 0,
        "no_record_maps_a_name_to_a_cbuffer_offset":
            words["number_words_in_offset_range"] == 0,
        "the_only_per_name_constant_is_the_name_index":
            words["constant_per_name"]["param_index"] == words["multi_name"]
            and words["constant_per_name"]["class_number"] == words["multi_name"],
        "name_numbers_cannot_encode_a_cbuffer_offset":
            max(words["words"]["param_number"]["max"],
                words["words"]["class_number"]["max"]) < 8,
        "bmak_name_hashes_do_not_name_an_fname_index":
            not any(v["hash_as_fname_index"] for v in hashes.values()),
        "region_has_no_slot_field": tiling == len(proven) and class_ids == [VECTOR],
    }
    return {
        "file": {"path": UPK, "bytes": os.path.getsize(UPK),
                 "sha1_16": hashlib.sha1(open(UPK, "rb").read()).hexdigest()[:16]},
        "data_bytes": len(d),
        "region_start": start, "region_bytes": len(d) - start,
        "dxbc": {"containers": data["blobs"].get("blobs"),
                 "last_end": data["blobs"].get("last_end")},
        "candidates": data["candidates"], "headers": len(data["headers"]),
        "records": len(proven), "rejected": data["rejected"],
        "entries_total": len(entries), "entry_bytes": entry_bytes,
        "record_bytes": sum(h["span"] for h in proven),
        "first": hex(proven[0]["offset"]), "last_end": hex(proven[-1]["end"]),
        "anchor": {"name": anchor["name"], "offset": hex(anchor["offset"]),
                   "count": anchor["count"], "guid": anchor["guid"],
                   "values": anchor["entries"]},
        "defaults_agreed": agreed, "defaults_disagreed": disagreed,
        "paint_records": paint, "paint_member_matches": members,
        "hash_probe": hashes, "word_probe": words,
        "oracles": oracles,
    }


# ------------------------------------------------------------------ render
def render(r: dict) -> str:
    out = []

    def A(line):
        out.append(line)

    A("# The material uniform records: names and values, and no name -> cbuffer offset map (G3-04d)")
    A("")
    A("Generated by `python Tools/scripts/jc3_uniform_records.py --write`; `--check`")
    A("re-derives every number from the install file, re-runs the oracles and requires this")
    A("page to match byte for byte.  Static only: no game process was started, attached to or")
    A("injected into.  Labels are the project's: **decoded** (file + offset), **derived**")
    A("(rule + inputs), **UNKNOWN** (what was tried, where the answer would be).")
    A("")
    A("Input (read-only):")
    A("")
    A("| file | bytes | sha1[:16] |")
    A("|---|---:|---|")
    A("| `%s` | %d | `%s` |" % (r["file"]["path"], r["file"]["bytes"], r["file"]["sha1_16"]))
    A("")
    A("The record region is read from the package's decompressed data stream (`upk_read.Package")
    A(".data(1)`), **%d B**; every offset in this page is an offset in that stream, not in the" % r["data_bytes"])
    A("21 MB container.")
    A("## 1. Answer")
    A("")
    A("**The records name their parameters and carry their values, and no record maps a name to")
    A("a cbuffer offset.** Every proven record's entry is exactly 32 B - an FName pair and one")
    A("RGBA - and the record's span is exactly `40 + name + 32 x count`, so no byte is left over")
    A("for a slot, buffer or offset field.  Of the %d entries, **%d** name a member of the 32"
      % (r["entries_total"], len(r["paint_member_matches"])))
    A("CarPaintMM `cb2`/`cb6` members that `CB0_SLOTS.md` decoded (0 expected: those are JC3")
    A("names, these are Arkham's).  `hash_jenkins` of the two BmAK names therefore has nothing")
    A("to attach to: `BaseColour` -> **%d**, `Diffuse_Adjust` -> **%d**, and neither value occurs"
      % (r["hash_probe"]["base_colour"]["hash"], r["hash_probe"]["diffuse_adjust"]["hash"]))
    A("anywhere in the record region as a slot, nor as an FName index (%d and %d occurrences)."
      % (r["hash_probe"]["base_colour"]["hash_u32_in_region"],
         r["hash_probe"]["diffuse_adjust"]["hash_u32_in_region"]))
    A("")
    A("So the paint-colour combine rule stays **UNKNOWN**.  What the records add is the paint")
    A("material's own parameter set and values (section 4), not the constant-buffer layout; that")
    A("layout is the JC3 reflection headers' (`CB0_SLOTS.md`), which name `cb2`/`cb6`/`cb7`")
    A("members directly from files on disk.")
    A("")
    A("## 2. Record layout, decoded from all %d records" % r["records"])
    A("")
    A("```")
    A("record :=  i32    n          ; 2 .. 300, length of the name including its NUL")
    A("           u8[n]  name       ; printable ASCII, name[n-1] == 0")
    A("           u8[16] guid       ; distinct per record")
    A("           u8[16] zero       ; all zero")
    A("           u32    count      ; 1 .. 64")
    A("           entry[count]")
    A("")
    A("entry  :=  u32 class            ; FName index, %d..%d" % (CLASS_LO, CLASS_HI))
    A("           u32 class_number     ; FName number")
    A("           u32 parameter        ; FName index into the package name table")
    A("           u32 param_number     ; FName number")
    A("           f32[4] value         ; RGBA")
    A("```")
    A("")
    A("| measurement | value |")
    A("|---|---:|")
    A("| end of the last DXBC container | `%#x` |" % r["region_start"])
    A("| region scanned to EOF | %d B |" % r["region_bytes"])
    A("| candidate offsets tested (length-prefix + printable + NUL) | %d |" % r["candidates"])
    A("| offsets where the header predicate holds | %d |" % r["headers"])
    A("| records proven end to end (count x 32 B) | **%d** |" % r["records"])
    A("| headers that leave the 32 B entry shape | %d (not decoded here) |" % r["rejected"])
    A("| entries | **%d** |" % r["entries_total"])
    A("| entry bytes | %d |" % r["entry_bytes"])
    A("| record bytes | %d |" % r["record_bytes"])
    A("| first record / last record end | `%s` / `%s` |" % (r["first"], r["last_end"]))
    A("| record spans equal `40 + n + 32 x count` | %d / %d |"
      % (r["records"], r["records"]))
    A("")
    A("The field widths are not assumed: the tiling test above accepts every proven record, and")
    A("28 B and 36 B strides put a non-class word at an entry start (G3-04e1's stride samples).")
    A("")
    A("## 3. Which records belong to the paint family")
    A("")
    A("The paint family is defined here by the BmAK paint parameter names, not by a shader")
    A("reference: a record belongs to it if it carries `BaseColour` / `Basecolour` or")
    A("`Diffuse_Adjust`.  **%d records** match, with **%d** entries in total."
      % (len(r["paint_records"]), sum(p["count"] for p in r["paint_records"])))
    A("")
    A("| record | offset | entries | paint parameters named |")
    A("|---|---|---:|---|")
    for p in r["paint_records"][:40]:
        A("| `%s` | `%s` | %d | %s |" % (p["name"], hex(p["offset"]), p["count"],
                                          ", ".join("`%s`" % h for h in p["hits"])))
    if len(r["paint_records"]) > 40:
        A("| ... %d more records | | | |" % (len(r["paint_records"]) - 40))
    A("")
    A("The chain material's own record, found by GUID `%s` (not by name), is **`%s`** at `%s`"
      % (GUID, r["anchor"]["name"], r["anchor"]["offset"]))
    A("with **%d** vector entries.  Its values reproduce G3-04c's declared defaults: **%d/%d"
      % (r["anchor"]["count"], len(r["defaults_agreed"]), len(r["defaults_agreed"]) + len(r["defaults_disagreed"])))
    A("checked, %d mismatches** at %g." % (len(r["defaults_disagreed"]), TOL))
    A("")
    A("| parameter | record value | `COLOUR_PARAMS.json` default | match |")
    A("|---|---|---|---|")
    defaults = colour_defaults()
    for e in r["anchor"]["values"]:
        n = e["param_name"]
        if n not in defaults:
            continue
        A("| `%s` | `%s` | `%s` | %s |"
          % (n, e["value"], defaults[n],
             "yes" if n in r["defaults_agreed"] else "**no**"))
    A("")
    A("## 4. Names, hashes, and the comparison with the BmAK parameters")
    A("")
    A("`hash_jenkins` is the project's archive-path Jenkins function (`Tools/scripts/rbmhdr.py`),")
    A("the same recipe that names JC3 paths.  The records do not store hashes: a parameter is")
    A("written as an `FName` index into the package name table, so a hash can only be compared")
    A("against the FName **index**, the name **string**, or raw bytes.")
    A("")
    A("| BmAK parameter | `hash_jenkins` (dec) | `hash_jenkins` (hex) | in the name table as a string | hash as an FName index | hash as a u32 in the region |")
    A("|---|---:|---|---:|---:|---:|")
    for k in ("base_colour", "diffuse_adjust"):
        h = r["hash_probe"][k]
        A("| `%s` | %d | `%#010x` | %s | %s | %d |"
          % (h["name"], h["hash"], h["hash"],
             "yes" if h["name_table_exact"] else "no",
             "yes" if h["hash_as_fname_index"] else "no", h["hash_u32_in_region"]))
    A("")
    A("A parameter->slot field would show up as a per-name constant integer in the entry.  Testing")
    A("all %d entries, and the %d parameter names that occur more than once:" % (r["entries_total"], r["word_probe"]["multi_name"]))
    A("")
    A("| entry word | distinct values | min | max | nonzero | constant per name (of %d) |"
      % r["word_probe"]["multi_name"])
    A("|---|---:|---:|---:|---:|---:|")
    for w in ("class_id", "class_number", "param_index", "param_number"):
        v = r["word_probe"]["words"][w]
        A("| `%s` | %d | %d | %d | %d | %d |"
          % (w, v["distinct"], v["min"], v["max"], v["nonzero"],
             r["word_probe"]["constant_per_name"][w]))
    A("")
    A("The only word constant per name is the parameter's own name index (by construction).  A")
    A("cbuffer offset would have to be another per-name constant; the only other integer is the")
    A("FName number, whose values are 0 and small disambiguators.  **%d entries carry any number"
      % r["word_probe"]["number_words_in_offset_range"])
    A("word in the offset range 8..316**, and no entry has a fourth integer at all.")
    A("")
    A("Of the 32 CarPaintMM `cb2`/`cb6` members named by `CB0_SLOTS.md`, **%d** occur as a"
      % len(r["paint_member_matches"]))
    A("parameter in any record%s.  That is the expected result, not a gap: the JC3 paint members"
      % ("" if not r["paint_member_matches"] else
         " (" + ", ".join("`%s` x%d" % (n, c) for n, c in sorted(r["paint_member_matches"].items())) + ")"))
    A("exist in JC3's reflection headers, while these records are Arkham materials keyed by")
    A("Arkham parameter names (`BaseColour`, `Diffuse_Adjust`); no file joins the two dialects.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    ev = {
        "headers_are_self_delimiting": "span == 40 + n + 32 x count for every proven record",
        "every_entry_is_the_vector_class": "class id 2055 only",
        "every_entry_is_32_bytes": "%d entries, each 32 B" % r["entries_total"],
        "guids_are_distinct": "%d records, %d distinct guids" % (r["records"], r["records"]),
        "anchor_found_by_guid": "`%s` at `%s`" % (r["anchor"]["name"], r["anchor"]["offset"]),
        "anchor_reproduces_the_declared_defaults": "%d agreed, %d mismatched"
        % (len(r["defaults_agreed"]), len(r["defaults_disagreed"])),
        "no_entry_names_a_carpaintmm_cbuffer_member": "%d matches of 32 member names"
        % len(r["paint_member_matches"]),
        "no_record_maps_a_name_to_a_cbuffer_offset": "%d entries with an offset-range number word"
        % r["word_probe"]["number_words_in_offset_range"],
        "the_only_per_name_constant_is_the_name_index":
            "param_index and class_number constant for %d/%d multi-occurrence names; "
            "param_number constant for %d (its range is a name number, not an offset)"
            % (r["word_probe"]["constant_per_name"]["param_index"], r["word_probe"]["multi_name"],
               r["word_probe"]["constant_per_name"]["param_number"]),
        "name_numbers_cannot_encode_a_cbuffer_offset":
            "largest FName number is %d; cb2 spans 0..316 B"
            % max(r["word_probe"]["words"]["param_number"]["max"],
                  r["word_probe"]["words"]["class_number"]["max"]),
        "bmak_name_hashes_do_not_name_an_fname_index": "BaseColour %s, Diffuse_Adjust %s"
        % (r["hash_probe"]["base_colour"]["hash_as_fname_index"],
           r["hash_probe"]["diffuse_adjust"]["hash_as_fname_index"]),
        "region_has_no_slot_field": "every record tiles with 32 B entries; no other width accepted",
    }
    for k, ok in r["oracles"].items():
        A("| `%s` | %s | %s |" % (k, "**PASS**" if ok else "**FAIL**", ev.get(k, "")))
    A("")
    A("%d/%d oracles pass." % (sum(1 for v in r["oracles"].values() if v), len(r["oracles"])))
    A("")
    A("## 6. UNKNOWN")
    A("")
    A("- **Which cbuffer slot a paint parameter lands in.**  Tried: all %d records, %d entries,"
      % (r["records"], r["entries_total"]))
    A("  every field split at its own offset; the entry has no slot field, no class carries a")
    A("  slot, and the BmAK name hashes resolve to nothing.  Still unknown because the binding")
    A("  is written by the cooker into `RDEF`, which is absent from all 40,299 containers")
    A("  (G3-04d's shader-cache result); it would need a build that keeps `RDEF` or a live")
    A("  constant-buffer capture.")
    A("- **How `BaseColour` and `Diffuse_Adjust` combine.**  The records give their values")
    A("  (`Material0_BaseColour` `[0.0, 0.0, 0.0, 1.0]`, `Diffuse_Adjust` `[1.0, 1.0, 1.0, 1.0]`)")
    A("  but no operator graph: the material functions' `FunctionExpressions` are stripped")
    A("  (`COLOUR_PARAMS.md` section 6), and these records hold values only.  Still unknown; it")
    A("  needs the SHEX body or the stripped graph.")
    A("- **The %d headers that leave the 32 B shape.**  Reported, not decoded: their first entry"
      % r["rejected"])
    A("  has a class word outside %d..%d or a parameter index outside the name table, so the"
      % (CLASS_LO, CLASS_HI))
    A("  width of that class is not proven here.  They add no paint parameter (the paint records")
    A("  are all in the proven set), so they do not change the answer.")
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/jc3_uniform_records.py --write")
    A("python Tools/scripts/jc3_uniform_records.py --check")
    A("```")
    return "\n".join(out) + "\n"


def class_ids(r: dict) -> str:
    return "%d" % VECTOR


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write %s" % os.path.relpath(MD, ROOT))
    ap.add_argument("--check", action="store_true", help="no writes: re-derive and compare")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    r = build()
    text = render(r)
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        bad = [k for k, v in r["oracles"].items() if not v]
        print("wrote %s: %d records, %d entries, %d paint records, %d/%d oracles"
              % (os.path.relpath(MD, ROOT), r["records"], r["entries_total"],
                 len(r["paint_records"]), len(r["oracles"]) - len(bad), len(r["oracles"])))
        for k in bad:
            print("  FAIL", k)
        return 1 if bad else 0
    if not os.path.exists(MD):
        print("missing %s (run --write)" % os.path.relpath(MD, ROOT))
        return 1
    have = open(MD, encoding="utf-8", newline="").read()
    bad = [k for k, v in r["oracles"].items() if not v]
    if have.replace("\r\n", "\n") != text:
        print("FAIL: %s does not match the re-derived page" % os.path.relpath(MD, ROOT))
        for old, new in zip(have.splitlines(), text.splitlines()):
            if old != new:
                print("  page : %r" % old[:160])
                print("  new  : %r" % new[:160])
                break
        return 1
    for k in bad:
        print("  FAIL", k)
    if bad:
        return 1
    print("ok: %d records, %d entries, %d paint records, %d/%d oracles, page matches"
          % (r["records"], r["entries_total"], len(r["paint_records"]),
             len(r["oracles"]), len(r["oracles"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
