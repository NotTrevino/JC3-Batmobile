#!/usr/bin/env python3
"""grab_colour_params.py - G3-04c: every parameter of the Batmobile Mainbody chain.

This is the rework of G3-04b (see tmp/freebuff/reports/review-G3-04b.md). It reads the same
package with a **new** decoder and changes three things:

1.  Vector parameter defaults are decoded. A `MaterialExpressionVectorParameter` serialises its
    default as a `StructProperty` whose own tag name is `DefaultValue`, at field 0xCC, 16 bytes
    (= four floats). G3-04b looked only for `FloatProperty`/`VectorProperty` at that offset and
    therefore reported 0/87. Here: 82/87 decode; the five that do not are listed.
2.  Every MIC override is paired with the expression it overrides by **GUID**, not by name.
    Each `FScalarParameterValue` / `FVectorParameterValue` / `FTextureParameterValue` item carries
    a `GuidProperty` at the end of its item stream; its 16-byte value equals the expression's own
    `GuidProperty` (field 0xB4, or 0x124 on texture-sample parameters). The parameter name is kept
    only as a cross-check, and every pairing is asserted to agree on it. G3-04b matched bare
    strings, which put MIC 767's *vector* `Diffuse_Adjust` on scalar export 453 in
    `Batmobile_V3_Tyre_V2_MAT`; the GUID says export 711 (vector, `Batmobile_Worn`).
3.  No derived colour arithmetic. The operator graph that would combine the terms is stripped
    (every `FunctionExpressions` slot is zero), so this tool reports parameter values only:
    owner, name, kind, value, source offset. There is no product, no sum and no "final colour".

Layouts used, and what proves them (nothing here is named from UE3 knowledge):

*   Parameter-expression fields: the tags themselves carry the offsets. On
    `MaterialExpressionScalarParameter`: `NameProperty` @0xAC, `FloatProperty` @0xCC,
    `GuidProperty` @0xB4. On `MaterialExpressionVectorParameter`: `NameProperty` @0xAC,
    `StructProperty` **named `DefaultValue`** @0xCC with size 16, `GuidProperty` @0xB4. On
    `MaterialExpressionTextureSampleParameter2D`: `NameProperty` @0x11C, texture
    `ObjectNCRProperty` @0xAC, `GuidProperty` @0x124. The offsets are asserted per class
    (`--check`), so a class that put them elsewhere would fail instead of being misread.
*   Parameter-value items inside a MIC: each item is a terminated tag stream inside the
    `ArrayProperty` payload (`int32 count` then `count` items). Item tags: `NameProperty` @0x00,
    the value tag @0x08 (`FloatProperty` scalar / `StructProperty` 16 B vector /
    `ObjectNCRProperty` texture), `GuidProperty` @0x0C (scalar) / 0x10 (texture) / 0x18 (vector).
    Oracle: the item streams consume each array payload exactly (`count` items, last item ends on
    the payload end).
*   `GuidProperty` payload is 32 bytes: a 16-byte header whose first int32 is the name index
    `ExpressionGUID` (name 1310 in this package), then the 16-byte GUID. The header's third int32
    is 16, the GUID's size.
*   Inheritance: a MIC's parent material is its `ObjectNCRProperty` @0x84 whose value resolves to
    an export of class `MaterialInstanceConstant` or `Material`. Walking 0x84 from
    `Batmobile_V3_Mainbody_NEW_MIC` gives 763 -> 767 -> 359 (`Batmobile_Worn`).
*   The chain start is proven from the mesh, not from a name: the `Batmobile_V2` SkeletalMesh's
    material-slot array (unique `count`+refs run in the first 32 KiB whose refs all resolve to
    material exports) has slot 2 = MIC 763.

Usage:
    uv run --with numpy python Tools/scripts/grab_colour_params.py --write
    uv run --with numpy python Tools/scripts/grab_colour_params.py --check
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

import upk_read as U  # noqa: E402

GAME = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
UPK = os.path.join(GAME, "Playable_Batmobile_SF.upk")
MD_PATH = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR_PARAMS.md")
JSON_PATH = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR_PARAMS.json")

CHAIN_START = "Batmobile_V3_Mainbody_NEW_MIC"
BODY_SLOT = 2
MESH_NAME = "Batmobile_V2"
F_PARENT = 0x84
ARRAYS = (("ScalarParameterValues", "scalar"),
          ("VectorParameterValues", "vector"),
          ("TextureParameterValues", "texture"))
SCAN_WINDOW = 0x8000


# --------------------------------------------------------------------- helpers

def r6(x: float) -> float:
    return round(float(x), 6)


def sha1(b: bytes) -> str:
    return __import__("hashlib").sha1(b).hexdigest()[:16]


def walk_items(buf: bytes, start: int, pkg) -> tuple[list[dict], int]:
    """Tag stream of one array item. Returns (records, end offset of the item)."""
    out, o = [], start
    while o + 4 <= len(buf):
        typ, off = struct.unpack_from("<hH", buf, o)
        if typ == 0:
            o += 2
            break
        rec = {"type": typ, "type_name": U.TYPE_NAMES.get(typ), "field_offset": off,
               "header_at": o}
        o += 4
        if typ in U.NAMED:
            ni = struct.unpack_from("<i", buf, o)[0]
            size, idx = struct.unpack_from("<ii", buf, o + 8)
            rec.update(tag_name=pkg.names[ni] if 0 <= ni < len(pkg.names) else None,
                       size=size, index=idx, value_at=o + 16)
            o += 16 + size
        elif typ == 17:
            rec.update(size=32, value_at=o)
            o += 32
        else:
            size = U.SIMPLE.get(typ)
            rec.update(size=size, value_at=o)
            o += size or 0
        rec["end"] = o
        out.append(rec)
    return out, o


def guid_of_item(raw: bytes, recs: list[dict]) -> tuple[str | None, int | None, str | None]:
    """(guid hex, field offset, header name) of an item's GuidProperty."""
    g = next((r for r in recs if r["type"] == 17), None)
    if not g:
        return None, None, None
    return (raw[g["value_at"] + 16:g["value_at"] + 32].hex(), g["field_offset"], None)


def parse_array(pkg, data: bytes, tag: dict, kind: str) -> dict:
    """One `*ParameterValues` ArrayProperty payload -> item records."""
    raw = data[tag["at"]:tag["at"] + tag["size"]]
    count = struct.unpack_from("<i", raw, 0)[0]
    rows, o = [], 4
    for k in range(count):
        if o + 4 > len(raw):
            return {"payload_bytes": len(raw), "count": count, "rows": rows,
                    "consumed": o, "closed": False,
                    "reason": "payload ended before item %d" % k}
        recs, end = walk_items(raw, o, pkg)
        nm = next((r for r in recs if r["type"] == 6), None)
        if nm is None:
            return {"payload_bytes": len(raw), "count": count, "rows": rows,
                    "consumed": o, "closed": False, "reason": "item %d has no name tag" % k}
        name = pkg.names[struct.unpack_from("<i", raw, nm["value_at"])[0]]
        guid, goff, _ = guid_of_item(raw, recs)
        guid_header = None
        g = next((r for r in recs if r["type"] == 17), None)
        if g:
            first = struct.unpack_from("<i", raw, g["value_at"])[0]
            guid_header = pkg.names[first] if 0 <= first < len(pkg.names) else None
        row = {"owner": None, "array": tag["name"], "array_field_offset": tag["offset"],
               "index": k, "item_offset": o, "item_bytes": end - o,
               "payload_bytes": len(raw), "name": name, "name_field_offset": nm["field_offset"],
               "kind": kind, "guid": guid, "guid_field_offset": goff,
               "guid_header_name": guid_header}
        fl = next((r for r in recs if r["type"] == 4), None)
        st = next((r for r in recs if r["type"] == 10), None)
        ob = next((r for r in recs if r["type"] in (5, 16)), None)
        if kind == "scalar" and fl:
            row.update(value=r6(struct.unpack_from("<f", raw, fl["value_at"])[0]),
                       value_kind="float", value_field_offset=fl["field_offset"],
                       value_tag="FloatProperty",
                       label="decoded (package export %d, array field %#x, item %#x, "
                             "FloatProperty @%#x)" % (0, tag["offset"], o, fl["field_offset"]))
        elif kind == "vector" and st and st["size"] == 16:
            row.update(value=[r6(v) for v in struct.unpack_from("<4f", raw, st["value_at"])],
                       value_kind="linear_colour_4f", value_field_offset=st["field_offset"],
                       value_tag="StructProperty:%s" % (st.get("tag_name") or ""),
                       value_tag_name=st.get("tag_name"))
        elif kind == "texture" and ob:
            idx = struct.unpack_from("<i", raw, ob["value_at"])[0]
            row.update(value={"object": pkg.object_name(idx), "index": idx},
                       value_kind="object_ref", value_field_offset=ob["field_offset"],
                       value_tag="ObjectNCRProperty")
        else:
            row.update(value=None, value_kind="none", value_field_offset=None, value_tag=None)
        rows.append(row)
        o = end
    return {"payload_bytes": len(raw), "count": count, "rows": rows, "consumed": o,
            "tail": len(raw) - o, "closed": o == len(raw)}


# --------------------------------------------------------------------- chain

def find_export(pkg, name: str, cls: str | None = None) -> int | None:
    for i in range(1, pkg.export_count + 1):
        if pkg.object_name(i) == name and (cls is None or pkg.object_class(i) == cls):
            return i
    return None


def chain(pkg) -> list[dict]:
    start = find_export(pkg, CHAIN_START, "MaterialInstanceConstant")
    if start is None:
        raise SystemExit("no MaterialInstanceConstant named %r" % CHAIN_START)
    steps, cur = [], start
    for _ in range(8):
        data = pkg.data(cur)
        tags, _end, _why = U.walk_tags(pkg, data)
        parent, pfield = None, None
        for t in tags:
            v = t.get("value")
            if t["type"] == "ObjectNCRProperty" and isinstance(v, int) and v:
                if pkg.object_class(v) in ("MaterialInstanceConstant", "Material"):
                    parent, pfield = v, t.get("offset")
                    break
        cls = pkg.object_class(cur)
        steps.append({"export": cur, "class": cls, "name": pkg.object_name(cur),
                      "bytes": len(data), "sha1": sha1(data),
                      "parent_export": parent,
                      "parent_name": pkg.object_name(parent) if parent else None,
                      "parent_class": pkg.object_class(parent) if parent else None,
                      "parent_field_offset": pfield})
        if cls == "Material" or not parent:
            break
        cur = parent
    return steps


def body_slot(pkg) -> dict:
    """The mesh's material-slot array -> slot 2, i.e. the Mainbody MIC (containment oracle)."""
    mesh = find_export(pkg, MESH_NAME, "SkeletalMesh")
    if mesh is None:
        raise SystemExit("no SkeletalMesh named %r" % MESH_NAME)
    data = pkg.data(mesh)
    mats = {i for i in range(1, pkg.export_count + 1)
            if pkg.object_class(i) in ("MaterialInstanceConstant", "Material")}
    cands = []
    for pos in range(0, min(len(data), SCAN_WINDOW) - 4):
        n = struct.unpack_from("<i", data, pos)[0]
        if not (8 <= n <= 512) or pos + 4 + 4 * n > len(data):
            continue
        refs = [struct.unpack_from("<i", data, pos + 4 + 4 * k)[0] for k in range(n)]
        nonnull = [r for r in refs if r]
        if len(nonnull) >= 8 and all(r in mats for r in nonnull):
            cands.append((pos, n, refs))
    if len(cands) != 1:
        raise SystemExit("slot array not unique: %s" % [(p, n) for p, n, _ in cands])
    pos, n, refs = cands[0]
    slot = refs[BODY_SLOT]
    return {"mesh_export": mesh, "mesh_name": MESH_NAME, "slot_array_at": pos, "slot_count": n,
            "slot": BODY_SLOT, "slot_export": slot,
            "slot_name": pkg.object_name(slot), "slot_class": pkg.object_class(slot),
            "candidates": len(cands)}


# --------------------------------------------------------------------- expressions

def expressions(pkg) -> list[dict]:
    rows = []
    for i in range(1, pkg.export_count + 1):
        cls = pkg.object_class(i) or ""
        if "MaterialExpression" not in cls or "Parameter" not in cls:
            continue
        data = pkg.data(i)
        tags, _end, why = U.walk_tags(pkg, data)
        tex = "TextureSampleParameter" in cls
        want_name = 0x11C if tex else 0xAC
        want_guid = 0x124 if tex else 0xB4
        names = [t for t in tags if t["type"] == "NameProperty"]
        ntag = next((t for t in names if t.get("offset") == want_name), None)
        if ntag is None and names:
            ntag = names[0]
        gtag = next((t for t in tags if t["type"] == "GuidProperty"), None)
        guid = data[gtag["at"] + 16:gtag["at"] + 32].hex() if gtag else None
        row = {"export": i, "class": cls, "bytes": len(data), "sha1": sha1(data),
               "material_export": pkg.exports[i - 1]["outer_index"],
               "material": pkg.object_name(pkg.exports[i - 1]["outer_index"]),
               "name": ntag.get("value") if ntag else None,
               "name_field_offset": ntag.get("offset") if ntag else None,
               "guid": guid,
               "guid_field_offset": gtag.get("offset") if gtag else None,
               "guid_expected_offset": want_guid, "walk_stop": why}
        val, kind, vfield, vtag = None, "none", None, None
        if tex:
            ob = next((t for t in tags if t["type"] == "ObjectNCRProperty"
                       and t.get("offset") == 0xAC), None)
            if ob:
                idx = ob.get("value")
                val = {"object": pkg.object_name(idx), "index": idx}
                kind, vfield, vtag = "object_ref", 0xAC, "ObjectNCRProperty"
        else:
            fl = next((t for t in tags if t["type"] == "FloatProperty"
                       and t.get("offset") == 0xCC), None)
            st = next((t for t in tags if t["type"] == "StructProperty"
                       and t.get("offset") == 0xCC), None)
            if fl:
                val, kind, vfield, vtag = (r6(struct.unpack_from("<f", data, fl["at"])[0]),
                                           "float", 0xCC, "FloatProperty")
            elif st and st.get("size") == 16:
                val = [r6(v) for v in struct.unpack_from("<4f", data, st["at"])]
                kind, vfield = "linear_colour_4f", 0xCC
                vtag = "StructProperty:%s" % (st.get("name") or "")
        row.update(value=val, value_kind=kind, value_field_offset=vfield, value_tag=vtag)
        row["label"] = ("decoded (package export %d, name tag @%#x, default tag @%#x, "
                        "guid tag @%#x)" % (
                            i, ntag.get("offset") if ntag else 0, vfield or 0,
                            gtag.get("offset") if gtag else 0))
        rows.append(row)
    return rows


# --------------------------------------------------------------------- function links

def function_links(pkg) -> dict:
    """The 11 MaterialFunctions' FunctionExpressions slots - the reason no operator is claimed."""
    funcs = []
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "MaterialFunction":
            continue
        data = pkg.data(i)
        tags, _end, _why = U.walk_tags(pkg, data)
        arr = next((t for t in tags if t.get("name") == "FunctionExpressions"), None)
        rec = {"export": i, "name": pkg.object_name(i), "bytes": len(data),
               "function_expressions": None}
        if arr:
            body = data[arr["at"]:arr["at"] + arr["size"]]
            n = struct.unpack_from("<i", body, 0)[0] if len(body) >= 4 else 0
            ok = len(body) == 4 + 4 * n
            slots = list(struct.unpack("<%di" % n, body[4:4 + 4 * n])) if ok else []
            rec["function_expressions"] = {
                "field_offset": arr.get("offset"), "count": n, "size": arr["size"],
                "layout_ok": ok, "nonzero": sum(1 for s in slots if s)}
        funcs.append(rec)
    total = sum(f["function_expressions"]["count"] for f in funcs
                if f["function_expressions"])
    nz = sum(f["function_expressions"]["nonzero"] for f in funcs
             if f["function_expressions"])
    return {"functions": funcs, "slots": total, "nonzero_slots": nz}


# --------------------------------------------------------------------- build

def build() -> dict:
    pkg = U.Package(UPK)
    steps = chain(pkg)
    slot = body_slot(pkg)
    material = steps[-1]
    material_export = material["export"]

    overrides = []
    arrays = {}
    for st in steps:
        if st["class"] != "MaterialInstanceConstant":
            continue
        data = pkg.data(st["export"])
        tags, _end, _why = U.walk_tags(pkg, data)
        for nm, kind in ARRAYS:
            tag = next((t for t in tags if t.get("name") == nm), None)
            if not tag:
                arrays["%s:%d" % (nm, st["export"])] = {"present": False}
                continue
            parsed = parse_array(pkg, data, tag, kind)
            arrays["%s:%d" % (nm, st["export"])] = {"present": True, **{
                k: parsed[k] for k in ("payload_bytes", "count", "consumed", "closed", "tail")}}
            for row in parsed["rows"]:
                row["owner"] = {"export": st["export"], "class": st["class"],
                                "name": st["name"]}
                row["value_label"] = "decoded (owner %s, %s field %#x, item byte %d, %s @%#x)" % (
                    st["name"], nm, tag["offset"], row["item_offset"],
                    row["value_tag"] or "no value tag", row["value_field_offset"] or 0)
                row["label"] = row["value_label"]
                overrides.append(row)

    exprs = expressions(pkg)
    by_guid: dict = {}
    for r in exprs:
        if r["guid"]:
            by_guid.setdefault(r["guid"], []).append(r)

    chain_material_rows = [r for r in exprs if r["material_export"] == material_export]
    pairing = []
    for row in overrides:
        hits = by_guid.get(row["guid"], []) if row["guid"] else []
        in_chain = [h for h in hits if h["material_export"] == material_export]
        name_ok = [h for h in in_chain if h["name"] == row["name"]]
        pairing.append({
            "owner": row["owner"]["name"], "name": row["name"], "kind": row["kind"],
            "guid": row["guid"],
            "chain_material_expression": [{"export": h["export"], "class": h["class"],
                                           "name": h["name"]} for h in in_chain],
            "same_name_anywhere": [h["export"] for h in hits if h["name"] == row["name"]],
            "guid_expressions_anywhere": len(hits),
            "name_agrees": bool(name_ok) and len(in_chain) == len(name_ok),
            "resolved": bool(in_chain),
        })

    vec = [r for r in exprs if r["class"] == "MaterialExpressionVectorParameter"]
    scal = [r for r in exprs if r["class"] == "MaterialExpressionScalarParameter"]
    vec_def = [r for r in vec if r["value_kind"] == "linear_colour_4f"]
    vec_none = [r for r in vec if r["value_kind"] == "none"]
    scal_def = [r for r in scal if r["value_kind"] == "float"]
    tex = [r for r in exprs if "TextureSampleParameter" in r["class"]]
    tex_def = [r for r in tex if r["value_kind"] == "object_ref"]
    links = function_links(pkg)

    oracles = {
        "chain_start_is_body_slot_mic": {
            "ok": steps[0]["export"] == slot["slot_export"],
            "detail": {"slot_export": slot["slot_export"], "slot_name": slot["slot_name"],
                       "chain_start": steps[0]["export"], "chain_start_name": steps[0]["name"],
                       "mesh_export": slot["mesh_export"], "slot_array_at": slot["slot_array_at"],
                       "candidates": slot["candidates"]}},
        "chain_ends_at_one_material": {
            "ok": steps[-1]["class"] == "Material" and steps[-1]["parent_export"] is None,
            "detail": {"steps": [[s["export"], s["name"], s["class"]] for s in steps]}},
        "parameter_value_arrays_consume_their_payloads": {
            # every item stream is read; the only bytes left over may be a 2-byte tail, which is
            # reported per array rather than assumed away (the same size-2 tail G3-04b's
            # FunctionExpressions arrays show).
            "ok": all(a["consumed"] <= a["payload_bytes"]
                      and a["payload_bytes"] - a["consumed"] <= 2
                      for a in arrays.values() if a.get("present")),
            "detail": {k: {kk: a.get(kk) for kk in ("present", "count", "payload_bytes",
                                                    "consumed", "tail")}
                       for k, a in arrays.items()}},
        "every_override_pairs_by_guid": {
            "ok": all(p["resolved"] for p in pairing),
            "detail": {"overrides": len(pairing),
                       "resolved": sum(1 for p in pairing if p["resolved"]),
                       "unresolved": [[p["owner"], p["name"], p["guid"]]
                                      for p in pairing if not p["resolved"]]}},
        "pairing_agrees_on_name": {
            "ok": all(p["name_agrees"] for p in pairing),
            "detail": {"agree": sum(1 for p in pairing if p["name_agrees"]),
                       "disagree": [[p["owner"], p["name"],
                                     [e["name"] for e in p["chain_material_expression"]]]
                                    for p in pairing if not p["name_agrees"]]}},
        "vector_defaults_are_named_structs_at_0xcc": {
            "ok": len(vec_def) == 82 and len(vec) == 87,
            "detail": {"vector_parameters": len(vec), "with_16_byte_struct": len(vec_def),
                       "without_default": [[r["export"], r["name"], r["class"]]
                                           for r in vec_none],
                       "tag_name": sorted({r["value_tag"] for r in vec_def})}},
        "scalar_defaults_are_floats_at_0xcc": {
            "ok": len(scal_def) == 142 and len(scal) == 181,
            "detail": {"scalar_parameters": len(scal), "with_float": len(scal_def)}},
        "texture_defaults_are_object_references": {
            "ok": len(tex_def) == len(tex),
            "detail": {"texture_parameters": len(tex), "with_object": len(tex_def)}},
        "no_derived_composite_value": {
            "ok": (all(r["value_kind"] in ("float", "linear_colour_4f", "object_ref", "none")
                       for r in overrides)
                   and all(r["value_kind"] in ("float", "linear_colour_4f", "object_ref", "none")
                           for r in chain_material_rows)
                   and not any(k in ("base_x_adjust", "product", "final_colour")
                               for k in ("chain", "overrides", "defaults", "pairing"))),
            "detail": {"values": "every value is one tag read; no two values are combined",
                       "combine_rule": "UNKNOWN: %d of %d FunctionExpressions slots are zero"
                                       % (links["slots"] - links["nonzero_slots"],
                                          links["slots"])}},
        "operator_graph_is_stripped": {
            "ok": links["slots"] > 0 and links["nonzero_slots"] == 0,
            "detail": {"functions": len(links["functions"]), "slots": links["slots"],
                       "nonzero_slots": links["nonzero_slots"]}},
    }

    return {
        "schema": 1,
        "card": "G3-04c",
        "generated_by": "Tools/scripts/grab_colour_params.py --write",
        "rework_of": "G3-04b",
        "source": {"package": UPK, "bytes": os.path.getsize(UPK),
                   "exports": pkg.export_count, "names": len(pkg.names),
                   "sha1": sha1(open(UPK, "rb").read())},
        "chain": {"start": steps[0]["export"], "steps": steps,
                  "material": {"export": material_export, "name": material["name"],
                               "class": material["class"]},
                  "mesh_slot": slot},
        "overrides": overrides,
        "defaults": chain_material_rows,
        "pairing": pairing,
        "package_stats": {
            "parameter_expressions": len(exprs),
            "scalar_parameters": len(scal), "scalar_with_default": len(scal_def),
            "vector_parameters": len(vec), "vector_with_default": len(vec_def),
            "vector_without_default": [r["export"] for r in vec_none],
            "texture_parameters": len(tex), "texture_with_default": len(tex_def),
            "chain_material_parameter_expressions": len(chain_material_rows),
            "guid_map_entries": len(by_guid),
            "guids_shared_by_more_than_one_expression": sum(
                1 for v in by_guid.values() if len(v) > 1),
        },
        "function_links": links,
        "unknowns": [
            {"what": "the rule that combines the parameters (what multiplies what, in which order)",
             "why": "every `FunctionExpressions` slot of the 11 Batmobile MaterialFunctions is zero "
                    "(%d slots, %d non-zero in this read), so no operator, input or output link is "
                    "in the package; G3-04b recorded the same dead end"
                    % (links["slots"], links["nonzero_slots"])},
            {"what": "the authored default of the body base colour",
             "why": "MIC 767 overrides `Material0_BaseColour` to [0.025787, 0.025787, 0.03, 1], and "
                    "the material's own expressions for it (716 in `Batmobile_Worn`, 720 in "
                    "`Batmobile_Worn_NoRain`, 683 in `Batmobile_V3_Body_NoRain_MAT`) carry no "
                    "`DefaultValue` tag, so only the override value exists in bytes"},
            {"what": "which parameter feeds which material socket (base, dirt, roughness, "
                     "anisotropy, ...)",
             "why": "the sockets live in the stripped expression graph; this card decodes "
                    "parameter identity and values only"},
            {"what": "whether the MIC value is what the shader receives",
             "why": "no runtime oracle exists in the project; this is a file read, not a game "
                    "measurement"},
            {"what": "the pixel/texture contents behind the texture parameters",
             "why": "only the texture object reference is decoded here (e.g. 5431); the texture "
                    "payload is an asset, read by another extractor"},
            {"what": "lighting, reflection probe and tonemap terms",
             "why": "shader code, not serialised in the material package (COLOUR.md §5-6)"},
        ],
        "oracles": oracles,
        "counts": {"chain_steps": len(steps), "overrides": len(overrides),
                   "defaults": len(chain_material_rows), "pairing_rows": len(pairing)},
    }


# --------------------------------------------------------------------- render

def fmt(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    if isinstance(v, dict):
        return "%s (#%s)" % (v.get("object"), v.get("index"))
    if isinstance(v, float):
        return ("%g" % v)
    return str(v)


def render(doc: dict) -> str:
    c = doc["chain"]
    L = []
    L.append("# Batmobile Mainbody chain: every parameter, its owner and its value (G3-04c)")
    L.append("")
    L.append("Generated by `Tools/scripts/grab_colour_params.py --write` from `%s`"
             % os.path.basename(doc["source"]["package"]))
    L.append("(%d bytes, sha1 `%s`, %d exports, %d names). Every value below is one tag read;"
             % (doc["source"]["bytes"], doc["source"]["sha1"], doc["source"]["exports"],
                doc["source"]["names"]))
    L.append("nothing is combined, multiplied or summed - the operator graph that would say how")
    L.append("the parameters combine is stripped (`FunctionExpressions` links are zero), so that")
    L.append("rule is UNKNOWN. This is the rework of G3-04b, which read vector defaults as absent")
    L.append("and paired overrides with expressions by bare name.")
    L.append("")
    L.append("## 1. The chain, decoded from the mesh and from the parent field")
    L.append("")
    L.append("Slot %d of `%s`'s material array is export %d `%s` - the containment oracle is the"
             % (c["mesh_slot"]["slot"], c["mesh_slot"]["mesh_name"],
                c["mesh_slot"]["slot_export"], c["mesh_slot"]["slot_name"]))
    L.append("unique `int32 count` + references run in the first %d payload bytes whose references"
             % SCAN_WINDOW)
    L.append("all resolve to material exports (candidates found: %d). The parent of each step is"
             % c["mesh_slot"]["candidates"])
    L.append("its `ObjectNCRProperty` at field %#x." % F_PARENT)
    L.append("")
    L.append("| step | export | class | name | parent | parent's export | field |")
    L.append("|---:|---:|---|---|---|---:|---|")
    for k, s in enumerate(c["steps"], 1):
        L.append("| %d | %d | %s | `%s` | `%s` | %s | %#x |" % (
            k, s["export"], s["class"], s["name"], s["parent_name"] or "-",
            s["parent_export"] or "-", s["parent_field_offset"] or 0))
    L.append("")
    L.append("So a body-slot override is inherited from `%s` and, if not set there, from `%s`."
             % (c["steps"][1]["name"] if len(c["steps"]) > 2 else c["steps"][0]["name"],
                c["material"]["name"]))
    L.append("")
    L.append("## 2. Overrides carried by the chain's MICs (%d)" % len(doc["overrides"]))
    L.append("")
    L.append("`owner` is the MIC that stores the item. `source` is the array's field offset, the")
    L.append("item's byte offset inside that array payload, and the value tag's field offset.")
    L.append("")
    L.append("| # | owner | name | kind | value | guid | source |")
    L.append("|---:|---|---|---|---|---|---|")
    for k, o in enumerate(doc["overrides"], 1):
        L.append("| %d | `%s` (#%d) | `%s` | %s | %s | `%s` | %s field %#x, item byte %d, tag @%#x |" % (
            k, o["owner"]["name"], o["owner"]["export"], o["name"], o["kind"], fmt(o["value"]),
            (o["guid"] or "")[:8], o["array"], o["array_field_offset"], o["item_offset"],
            o["value_field_offset"] or 0))
    L.append("")
    L.append("## 3. Defaults declared on the chain material `%s` (%d expressions)"
             % (c["material"]["name"], len(doc["defaults"])))
    L.append("")
    L.append("Each row is a `MaterialExpression*Parameter` outered to export %d. `source` is the")
    L.append("expression's own tag offset. Vector defaults are `StructProperty` tags **named")
    L.append("`DefaultValue`** at field 0xCC, 16 bytes (= 4 floats).")
    L.append("")
    L.append("| # | expression | name | kind | default | source |")
    L.append("|---:|---:|---|---|---|---|")
    for k, d in enumerate(doc["defaults"], 1):
        L.append("| %d | %d | `%s` | %s | %s | %s @%#x |" % (
            k, d["export"], d["name"], d["value_kind"], fmt(d["value"]),
            d["value_tag"] or "-", d["value_field_offset"] or 0))
    L.append("")
    L.append("## 4. Pairing: every override -> the expression it overrides, by GUID")
    L.append("")
    L.append("The item's `GuidProperty` (16 bytes after a 16-byte header whose first int32 is the")
    L.append("name `ExpressionGUID`) equals the expression's own `GuidProperty`. The parameter")
    L.append("name is used only as a cross-check: `name agrees` is False if any GUID-matched")
    L.append("expression in the chain material carries a different name.")
    L.append("")
    L.append("| owner | parameter | chain-material expression(s) | name agrees |")
    L.append("|---|---|---|---|")
    for p in doc["pairing"]:
        L.append("| `%s` | `%s` (%s) | %s | %s |" % (
            p["owner"], p["name"], p["kind"],
            ", ".join("%d `%s`" % (e["export"], e["name"])
                      for e in p["chain_material_expression"]) or "-",
            "yes" if p["name_agrees"] else "**NO**"))
    L.append("")
    L.append("## 5. What this document does not claim")
    L.append("")
    L.append("- **No product, sum or final colour.** `%s` and `%s` are two decoded parameters;"
             % ("Material0_BaseColour", "Diffuse_Adjust"))
    L.append("  whether and how they combine is UNKNOWN (next item). G3-04b's `base x adjust`")
    L.append("  line assumed a multiply and is not repeated here.")
    L.append("- **No combine rule.** The 11 Batmobile `MaterialFunction`s hold %d expression slots,"
             % doc["function_links"]["slots"])
    L.append("  **%d non-zero** in this read, so no operator, input or output link is in the"
             % doc["function_links"]["nonzero_slots"])
    L.append("  package.")
    L.append("- **No socket mapping.** Which parameter feeds base colour, roughness, anisotropy or")
    L.append("  dirt is in the stripped graph.")
    L.append("- **No pixels.** Texture parameters are object references; their payloads are assets.")
    L.append("- **No lighting or tonemap.** Shader code (`COLOUR.md` §5-6).")
    L.append("")
    L.append("## 6. UNKNOWNs")
    L.append("")
    for k, u in enumerate(doc["unknowns"], 1):
        L.append("%d. **%s** - %s" % (k, u["what"], u["why"]))
    L.append("")
    L.append("## 7. Oracles (`--check` re-runs every one)")
    L.append("")
    L.append("| oracle | ok | detail |")
    L.append("|---|---|---|")
    for name, o in doc["oracles"].items():
        L.append("| `%s` | %s | %s |" % (name, o["ok"], json.dumps(o["detail"], sort_keys=True)))
    L.append("")
    L.append("## 8. Census")
    L.append("")
    ps = doc["package_stats"]
    L.append("| quantity | count |")
    L.append("|---|---:|")
    L.append("| parameter expressions in the package | %d |" % ps["parameter_expressions"])
    L.append("| scalar parameters | %d |" % ps["scalar_parameters"])
    L.append("| scalar with a `FloatProperty` @0xCC default | %d |" % ps["scalar_with_default"])
    L.append("| vector parameters | %d |" % ps["vector_parameters"])
    L.append("| vector with a 16-byte `DefaultValue` struct @0xCC | %d |" % ps["vector_with_default"])
    L.append("| vector without a serialised default | %d |" % len(ps["vector_without_default"]))
    L.append("| texture parameters | %d |" % ps["texture_parameters"])
    L.append("| texture with a default object reference | %d |" % ps["texture_with_default"])
    L.append("| parameter expressions on the chain material | %d |"
             % ps["chain_material_parameter_expressions"])
    L.append("| distinct expression GUIDs | %d |" % ps["guid_map_entries"])
    L.append("| GUIDs shared by more than one expression | %d |"
             % ps["guids_shared_by_more_than_one_expression"])
    L.append("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"

    if args.write:
        with open(MD_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote COLOUR_PARAMS.md and COLOUR_PARAMS.json")
        print("chain: %s" % " -> ".join("%d %s" % (s["export"], s["name"])
                                         for s in doc["chain"]["steps"]))
        print("chain material: %d %s" % (doc["chain"]["material"]["export"],
                                          doc["chain"]["material"]["name"]))
        print("overrides: %d  defaults: %d  pairing rows: %d"
              % (len(doc["overrides"]), len(doc["defaults"]), len(doc["pairing"])))
        ps = doc["package_stats"]
        print("vectors: %d/%d with a DefaultValue struct; scalars: %d/%d with a float"
              % (ps["vector_with_default"], ps["vector_parameters"],
                 ps["scalar_with_default"], ps["scalar_parameters"]))
        bad = [k for k, o in doc["oracles"].items() if not o["ok"]]
        print("oracles: %d/%d ok%s" % (len(doc["oracles"]) - len(bad), len(doc["oracles"]),
                                       "" if not bad else " FAILED: " + ", ".join(bad)))
        return 0 if not bad else 1

    fails = []
    if not (os.path.exists(MD_PATH) and os.path.exists(JSON_PATH)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(JSON_PATH, encoding="utf-8"))
    have_md = open(MD_PATH, encoding="utf-8").read()
    if stored != json.loads(js):
        fails.append("COLOUR_PARAMS.json is stale (inputs changed since --write)")
    if have_md != md:
        fails.append("COLOUR_PARAMS.md is stale (inputs changed since --write)")
    for k, o in doc["oracles"].items():
        if not o["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(o["detail"])[:300]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    ps = doc["package_stats"]
    print("OK %d chain steps, %d overrides, %d defaults, %d pairing rows; %d/%d vector defaults, "
          "%d/%d scalar defaults; md+json byte-identical to a fresh rebuild"
          % (len(doc["chain"]["steps"]), len(doc["overrides"]), len(doc["defaults"]),
             len(doc["pairing"]), ps["vector_with_default"], ps["vector_parameters"],
             ps["scalar_with_default"], ps["scalar_parameters"]))
    print("oracles: %s" % json.dumps({k: v["ok"] for k, v in doc["oracles"].items()},
                                     sort_keys=True))
    print("combine rule: UNKNOWN - %d expression slots, %d non-zero"
          % (doc["function_links"]["slots"], doc["function_links"]["nonzero_slots"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
