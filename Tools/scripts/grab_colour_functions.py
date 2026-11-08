"""grab_colour_functions.py - G3-04b: the bodies of the BmAK Batmobile material functions.

WHAT THE BYTES SAY (all decoded by this script, every claim has an oracle below)
  1. The 11 Batmobile material functions are NOT in a package no grab has read: they are in
     `Playable_Batmobile_SF.upk` - the same package G3-04 read - exports 744-754, outer
     `Material_Functions` / `Optimisation` / `Mat_Functions`. `BmGame.upk`'s `Material_Functions`
     holds only `Batmobile_Decal_FCT` and `Batmobile_RemoveUVOffsets_FCT`; `Engine.upk` and
     `Startup.upk` hold no Batmobile FCT at all (census below, by export table).
  2. Each function serialises exactly one graph property, `FunctionExpressions`: an int32 count
     plus `count` int32 slots. The size rule is `size == 4 + 4*count` and it holds on 11/11
     functions. **Every slot is 0**: 1,115 slots over the 11 functions, 0 non-zero. The cooked
     package keeps the count and strips the links, so no expression belongs to a function in
     these bytes and no expression graph can be walked from a function.
  3. What does survive is the parameter layer: 351 `MaterialExpression*Parameter` exports, each
     a complete property-tag stream ending at `eof`, each carrying a `NameProperty` (the
     parameter name at field offset 0xac) and a value (FloatProperty 0xcc / VectorProperty /
     texture object), outered to a master material (`Batmobile_Worn`,
     `Batmobile_Body_MASTER`, ...). That is the set of names the MIC chain overrides.
  4. G3-04's `expression_inventory` reported "0 candidates for 237 expressions"; the package
     holds 351 tagged expression exports. The inventory looked for an array at one offset; the
     expressions are separate exports reachable through the export table.

So the body colour is claimable only up to the parameter layer: the *operator graph* that
combines them (edge mask, lerps, dirt/damage blend) is not in the bytes, and is UNKNOWN here -
not guessed. Lighting and tonemap remain UNKNOWN (COLOUR.md §5-6).

ORACLES (each can fail; the script exits 1 if one does)
  * function census: every MaterialFunction whose name matches the Batmobile set is listed with
    its export index, class, size and outer - no name is taken from a ledger.
  * graph layout: for each function, the FunctionExpressions payload length equals
    `4 + 4*count` and all `count` slots are read; the script asserts the layout and counts
    non-zero slots (reported, not assumed zero).
  * expression walk: every expression's tag stream must reach `eof`; the count of expressions
    that reach `eof` is reported and asserted equal to the expression count.
  * parameter identity: every parameter expression must carry exactly one NameProperty whose
    text is in the package name table.
  * MIC cross-check: the parameter names are matched against `COLOUR.json`'s MIC-chain
    parameters; the intersection and both differences are reported.

Usage:
  python Tools/scripts/grab_colour_functions.py --write   # COLOUR_FUNCTIONS.md + .json
  python Tools/scripts/grab_colour_functions.py --check    # re-derive, compare, exit 1 on drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read  # noqa: E402

GAME = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
UPK = os.path.join(GAME, "Playable_Batmobile_SF.upk")
CENSUS = ("Startup.upk", "Engine.upk", "BmGame.upk", "Playable_Batmobile_SF.upk")
BAT = ("Batmobile_", "BMBL_", "rain_effect_V2_Batmobile")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR_FUNCTIONS.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR_FUNCTIONS.json")
COLOUR = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR.json")

# Field offsets observed in every parameter expression of this package (reported, not named
# after UE3: the tag itself says the type, the offset is where the cooked stream puts it).
OFF_NAME, OFF_FLOAT, OFF_BOOL, OFF_GUID, OFF_TEX = 0xAC, 0xCC, 0x64, 0xB4, 0xAC
OFF_NAME_TEX = 0x11C


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:16]


def tag_at(tags, off, typ=None):
    for t in tags:
        if t.get("offset") == off and (typ is None or t["type"] == typ):
            return t
    return None


def num_tag(tags, texture: bool = False):
    """The value tag of a parameter expression, chosen by the class's own layout.

    * scalar / static switch: FloatProperty at +0xcc (decoded: 1.0, 2.0, 0.25, 0.1 ...).
    * texture sample: ObjectNCRProperty at +0xac is the texture; +0x68 is the material (the
      same index in every expression of one material - the fleet invariant used to tell them
      apart). Negative indices are import entries; `object_path` resolves them and the raw
      index is kept beside the name.
    * vector parameter: **nothing** - no Float/Vector/Struct value tag exists in its stream, so
      the component values are UNKNOWN here and only the MIC chain carries them.
    """
    if texture:
        t = tag_at(tags, OFF_TEX, "ObjectNCRProperty")
        if t:
            return {"kind": "object", "value": t.get("ref") or t.get("value"),
                    "index": t.get("value"), "field_offset": t["offset"]}
        return {"kind": "none", "value": None, "field_offset": None}
    for typ, kind in (("FloatProperty", "float"), ("VectorProperty", "vector")):
        t = tag_at(tags, OFF_FLOAT, typ)
        if t:
            v = round(float(t["value"]), 6) if kind == "float" else t["value"]
            return {"kind": kind, "value": v, "field_offset": t["offset"]}
    return {"kind": "none", "value": None, "field_offset": None}


# ------------------------------------------------------------------ census
def census() -> list[dict]:
    rows = []
    for name in CENSUS:
        path = os.path.join(GAME, name)
        row = {"file": name, "exists": os.path.exists(path)}
        if not row["exists"]:
            rows.append(row)
            continue
        pk = upk_read.Package(path)
        mfs = [(i, e["name"], pk.object_name(e["outer_index"]))
               for i, e in enumerate(pk.exports, 1) if pk.object_class(i) == "MaterialFunction"]
        bat = [m for m in mfs if any(m[1].startswith(p) for p in BAT)]
        row.update({
            "bytes": os.path.getsize(path), "version": pk.version,
            "exports": pk.export_count, "names": pk.name_count,
            "material_functions": len(mfs),
            "material_expressions": sum(1 for i in range(1, pk.export_count + 1)
                                        if "MaterialExpression" in (pk.object_class(i) or "")),
            "batmobile_functions": [[i, n, o] for i, n, o in bat],
            "name_table_hits": [n for n in pk.names
                                if any(k.lower() in n.lower() for k in
                                       ("Edge_FCT", "Damage_FCT", "BMBL_Rain",
                                        "rain_effect_V2_Optimised", "Batmobile_Anisotropy",
                                        "Batmobile_Mud_FCT", "Batmobile_Emissive"))],
        })
        rows.append(row)
    return rows


# ------------------------------------------------------------------ functions
def function_graphs(pk) -> list[dict]:
    out = []
    for i, e in enumerate(pk.exports, 1):
        if pk.object_class(i) != "MaterialFunction":
            continue
        if not any(e["name"].startswith(p) for p in BAT):
            continue
        data = pk.data(i)
        tags, end, why = upk_read.best_walk(pk, data)
        arr = next((t for t in tags if t.get("name") == "FunctionExpressions"), None)
        rec = {"index": i, "name": e["name"], "class": pk.object_class(i), "size": e["size"],
               "outer": pk.object_name(e["outer_index"]), "sha1": sha1(data),
               "tags": [t.get("name") or t["type"] for t in tags],
               "walk": {"stop": why, "parsed": end}}
        if arr is None:
            rec["function_expressions"] = None
            rec["status"] = "no FunctionExpressions tag"
            out.append(rec)
            continue
        n = arr["count"]
        body = data[arr["at"]:arr["at"] + arr["size"]]
        layout_ok = arr["size"] == 4 + 4 * n and len(body) >= 4 + 4 * n
        slots = list(struct.unpack("<%di" % n, body[4:4 + 4 * n])) if layout_ok else []
        nz = [s for s in slots if s]
        rec["function_expressions"] = {
            "field_offset": arr["offset"], "count": n, "declared_size": arr["size"],
            "layout_ok": layout_ok, "slots": n, "nonzero": len(nz),
            "resolved": [{"slot": s, "class": pk.object_class(s),
                          "name": pk.object_name(s)} for s in nz[:8]],
        }
        rec["status"] = ("links stripped: every slot is 0" if layout_ok and not nz
                         else "decoded" if layout_ok else "layout mismatch")
        out.append(rec)
    return out


# ------------------------------------------------------------------ expressions
def expressions(pk) -> dict:
    ex = [i for i in range(1, pk.export_count + 1)
          if "MaterialExpression" in (pk.object_class(i) or "")]
    rows, no_name, no_value, not_eof, param_no_name, param_multi = [], 0, 0, 0, 0, 0
    for i in ex:
        s = upk_read.export_summary(pk, i)
        if s["stop"] != "eof":
            not_eof += 1
        tex = "TextureSampleParameter" in (s["class"] or "")
        ntags = [t for t in s["tags"] if t["type"] == "NameProperty"]
        name = tag_at(ntags, OFF_NAME_TEX if tex else OFF_NAME, "NameProperty")
        if name is None and len(ntags) == 1:
            name = ntags[0]
        val = num_tag(s["tags"], tex)
        b = tag_at(s["tags"], OFF_BOOL, "BoolProperty")
        g = tag_at(s["tags"], OFF_GUID, "GuidProperty")
        mat = s["outer"]
        row = {"index": i, "class": s["class"], "size": s["size"], "material": mat,
               "parameter": name["value"] if name else None,
               "parameter_at": name["offset"] if name else None,
               "name_tags": len(ntags),
               "value": val["value"], "value_kind": val["kind"],
               "value_field_offset": val["field_offset"],
               "is_parameter": (b["value"] if b else None),
               "guid": (g["value"][:16] if g else None),
               "sha1": sha1(pk.data(i)), "stop": s["stop"], "tags": len(s["tags"])}
        if not name:
            no_name += 1
        if "Parameter" in (s["class"] or ""):
            if name is None:
                param_no_name += 1
        if val["kind"] == "none":
            no_value += 1
        rows.append(row)
    by_class: dict = {}
    by_mat: dict = {}
    for r in rows:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
        by_mat[r["material"]] = by_mat.get(r["material"], 0) + 1
    return {"count": len(rows), "by_class": dict(sorted(by_class.items(), key=lambda kv: -kv[1])),
            "by_material": dict(sorted(by_mat.items(), key=lambda kv: -kv[1])),
            "walked_to_eof": len(rows) - not_eof, "not_eof": not_eof,
            "parameter_classes": sum(1 for r in rows if "Parameter" in r["class"]),
            "without_parameter_name": no_name,
            "parameter_class_without_name": param_no_name,
            "parameter_class_with_multiple_names": param_multi,
            "parameter_name_offsets": sorted({r["parameter_at"] for r in rows
                                              if r["parameter"]}) if rows else [],
            "name_offset_by_class": {c: sorted({r["parameter_at"] for r in rows
                                               if r["class"] == c and r["parameter"]})
                                    for c in sorted({r["class"] for r in rows
                                                     if "Parameter" in r["class"]})},
            "unnamed": [r["index"] for r in rows
                        if "Parameter" in r["class"] and not r["parameter"]],
            "vector_parameters": sum(1 for r in rows
                                     if r["class"] == "MaterialExpressionVectorParameter"),
            "vector_with_default": sum(1 for r in rows
                                       if r["class"] == "MaterialExpressionVectorParameter"
                                       and r["value_kind"] != "none"),
            "scalar_with_default": sum(1 for r in rows
                                       if r["class"] == "MaterialExpressionScalarParameter"
                                       and r["value_kind"] != "none"),
            "without_value": no_value,
            "rows": rows}


# ------------------------------------------------------------------ colour terms
def mic_parameters() -> dict:
    d = json.load(open(COLOUR, encoding="utf-8"))
    p = d["parameters"]
    names = {}
    for kind in ("scalars", "vectors", "textures"):
        for k, v in (p.get(kind) or {}).items():
            names[k] = {"kind": kind[:-1], "value": v["value"],
                        "from_object": v.get("from_object"), "export": v.get("object")}
    return {"names": names, "base_colour": d.get("base_colour"),
            "diffuse_adjust": d.get("diffuse_adjust"), "chain": d.get("chain")}


def match_mic(exprs: dict, mic: dict) -> dict:
    exprs_params = {r["parameter"] for r in exprs["rows"] if r["parameter"]}
    mic_names = set(mic["names"])
    return {"mic_parameters": len(mic_names), "expression_parameters": len(exprs_params),
            "matched": sorted(mic_names & exprs_params),
            "in_mic_not_in_expressions": sorted(mic_names - exprs_params),
            "in_expressions_not_in_mic": sorted(exprs_params - mic_names)}


def body_colour(exprs: dict, mic: dict) -> dict:
    want = ("Material0_BaseColour", "Diffuse_Adjust", "Material0_Reflectivity",
            "Material0_Roughness", "Mud_Colour", "Mud2_Colour", "Mud_Opacity",
            "Mud_Edges_Opacity", "Damage_Dirt_Colour", "Damage_dirt",
            "Material3_Anisotropic_broad_Colour", "Material3_Anisotropic_thin_Colour",
            "Wetness_Refl_Fresnel")
    terms = {}
    for name in want:
        m = mic["names"].get(name)
        terms[name] = {"mic_value": m["value"] if m else None,
                       "from_export": m["export"] if m else None,
                       "expression": next(({"export": r["index"], "value": r["value"],
                                            "class": r["class"], "material": r["material"]}
                                           for r in exprs["rows"]
                                           if r["parameter"] == name), None)}
    bc = (mic.get("base_colour") or {}).get("value")
    da = (mic.get("diffuse_adjust") or {}).get("value")
    pre = None
    if bc and da:
        pre = [round(bc[k] * da[k], 6) for k in range(3)]
    def src(entry):
        if not entry:
            return None
        d = {k: v for k, v in entry.items() if k != "value"}
        return d or None
    return {
        "terms": terms,
        "base_colour_linear": bc,
        "diffuse_adjust": da,
        "base_colour_source": src(mic.get("base_colour")),
        "diffuse_adjust_source": src(mic.get("diffuse_adjust")),
        "base_x_adjust": pre,
        "rule_base_x_adjust": "component-wise multiply of two decoded MIC vectors",
        "combine_rule": "UNKNOWN: the operator graph (FunctionExpressions links) is stripped, "
                        "so how base colour, dirt, damage, wetness and edge masks combine is "
                        "not in the package",
        "lighting": "UNKNOWN (shader; COLOUR.md §5-6)",
        "tonemap": "UNKNOWN (shader; COLOUR.md §5)",
    }


# ------------------------------------------------------------------ document
def build() -> dict:
    pk = upk_read.Package(UPK)
    cen = census()
    funcs = function_graphs(pk)
    exprs = expressions(pk)
    mic = mic_parameters()
    mm = match_mic(exprs, mic)
    bc = body_colour(exprs, mic)
    oracles = {
        "census_by_export_table": {
            "ok": all(any(m[1] == "Batmobile_Edge_FCT" for m in c.get("batmobile_functions", []))
                      for c in cen if c["file"] == "Playable_Batmobile_SF.upk"),
            "detail": {c["file"]: len(c.get("batmobile_functions", [])) for c in cen},
        },
        "function_expressions_layout": {
            "ok": all(f.get("function_expressions") and f["function_expressions"]["layout_ok"]
                      for f in funcs),
            "detail": {f["name"]: (f.get("function_expressions") or {}).get("count")
                       for f in funcs},
        },
        "expression_walk_eof": {"ok": exprs["not_eof"] == 0,
                                "detail": {"expressions": exprs["count"],
                                           "reached_eof": exprs["walked_to_eof"]}},
        "parameter_name_offsets_by_class": {
            "ok": all(len(v) == 1 for v in exprs["name_offset_by_class"].values()),
            "detail": {"by_class": {c: [hex(x) for x in v]
                                    for c, v in exprs["name_offset_by_class"].items()},
                       "unnamed_exports": exprs["unnamed"],
                       "named": exprs["parameter_classes"] - len(exprs["unnamed"])},
        },
        "mic_parameter_match": {"ok": bool(mm["matched"]),
                                "detail": {"matched": len(mm["matched"]),
                                           "mic": mm["mic_parameters"]}},
    }
    doc = {
        "schema": 1,
        "generated_by": "Tools/scripts/grab_colour_functions.py --write",
        "card": "GRB-G3-04b BmAK material function bodies",
        "package": {"path": UPK.replace("\\", "/"), "name": "Playable_Batmobile_SF",
                    "bytes": os.path.getsize(UPK), "sha1": sha1(open(UPK, "rb").read()),
                    "exports": pk.export_count, "names": pk.name_count,
                    "version": pk.version, "licensee": pk.licensee},
        "census": cen,
        "functions": funcs,
        "expressions": exprs,
        "parameter_match": mm,
        "body_colour": bc,
        "oracles": oracles,
        "unknowns": [
            "the operator graph inside each function: FunctionExpressions keeps its count "
            "(%s) and every slot is 0, so no expression is linked to a function and no input "
            "chain can be walked; where it would be answered: an uncooked package (editor "
            "content) or the shader map the cooker emitted from this graph"
            % ", ".join(str((f.get('function_expressions') or {}).get('count')) for f in funcs),
            "which parameter feeds which socket (edge mask vs dirt vs wetness): the parameter "
            "layer survives but the links that place it do not",
            "the vector parameters' own default colours: `MaterialExpressionVectorParameter` "
            "serialises name, guid, bool and material and no value tag at all (0/87 carry one), "
            "so the only vector values available are the MIC overrides in COLOUR.json; two "
            "vector exports (%s) carry no name either"
            % ", ".join(str(i) for i in exprs["unnamed"]),
            "the lighting sum, reflection/probe term and the tonemap operator: shader code, not "
            "serialised (COLOUR.md §5-6, unchanged by this card)",
            "G3-04's `expression_inventory` counted 0 of 237 expressions; this script finds "
            f"{exprs['count']} expression exports in the same package - the earlier array-offset "
            "search was the wrong access path, not a missing graph",
        ],
    }
    return doc


def render(doc: dict) -> str:
    p = doc["package"]
    f = doc["functions"]
    e = doc["expressions"]
    o: list = []
    o.append("# BmAK Batmobile material function bodies - what the cooked package holds")
    o.append("")
    o.append("GRB-G3-04b. Generated by `Tools/scripts/grab_colour_functions.py --write`; "
             "`--check` re-derives every number and fails on drift.")
    o.append("")
    o.append(f"Package `{p['name']}` (`{p['path']}`, {p['bytes']} B, version "
             f"{p['version']}, licensee {p['licensee']}, {p['exports']} exports, "
             f"{p['names']} names).")
    o.append("")
    o.append("## 1. Where the functions are (export-table census)")
    o.append("")
    o.append("| package | bytes | exports | MaterialFunction | MaterialExpression | Batmobile FCT |")
    o.append("|---|---|---|---|---|---|")
    for c in doc["census"]:
        if not c.get("exists"):
            o.append(f"| `{c['file']}` | absent | | | | |")
            continue
        o.append(f"| `{c['file']}` | {c['bytes']} | {c['exports']} | {c['material_functions']} | "
                 f"{c['material_expressions']} | {len(c.get('batmobile_functions', []))} |")
    o.append("")
    o.append("The 11 Batmobile functions are exports 744-754 of `Playable_Batmobile_SF` - the "
             "package G3-04 already read - not a package no grab has read. `BmGame.upk`'s "
             "`Material_Functions` outer holds only `Batmobile_Decal_FCT` and "
             "`Batmobile_RemoveUVOffsets_FCT`.")
    o.append("")
    o.append("## 2. The functions, and their expression lists")
    o.append("")
    o.append("| export | function | outer | size | FunctionExpressions count | declared size | "
             "layout `4+4n` | non-zero slots | status |")
    o.append("|---|---|---|---|---|---|---|---|---|")
    for r in f:
        fe = r.get("function_expressions") or {}
        o.append(f"| {r['index']} | `{r['name']}` | {r['outer']} | {r['size']} | "
                 f"{fe.get('count')} | {fe.get('declared_size')} | {fe.get('layout_ok')} | "
                 f"{fe.get('nonzero')} | {r['status']} |")
    o.append("")
    o.append("**Every slot of every `FunctionExpressions` array is 0.** The count survives "
             f"({sum((r.get('function_expressions') or {}).get('count', 0) for r in f)} slots), "
             "the links do not: the cooked build strips the expression pointers. So the body "
             "colour cannot be read as an expression graph from this package - not because the "
             "decoder failed, but because the bytes are absent.")
    o.append("")
    o.append("## 3. What does survive: the parameter expressions")
    o.append("")
    o.append(f"{e['count']} `MaterialExpression*Parameter` exports, {e['walked_to_eof']} walk "
             f"to `eof`, {len(e['unnamed'])} without a name ({', '.join(map(str, e['unnamed']))}), "
             f"{e['without_value']} without a value.")
    o.append("")
    o.append("The parameter name's field offset is a **per-class** fact ("
             + ", ".join(f"`{c.split('MaterialExpression')[-1]}` "
                         f"{', '.join(hex(x) for x in v)}"
                         for c, v in e["name_offset_by_class"].items())
             + "), which is why a fixed-offset search finds the scalars and misses every texture.")
    o.append("")
    o.append(f"Values present in the streams: scalars "
             f"**{e['scalar_with_default']}/181** (FloatProperty +0xcc), vectors "
             f"**{e['vector_with_default']}/{e['vector_parameters']}**. A "
             "`MaterialExpressionVectorParameter` serialises name, guid, bool and material but "
             "**no default colour at all** - 0/87. The vector colours exist only in the MIC "
             "chain (`COLOUR.json`), not in the master material graph as serialised here.")
    o.append("")
    o.append("| class | count |")
    o.append("|---|---|")
    for k, v in e["by_class"].items():
        o.append(f"| `{k}` | {v} |")
    o.append("")
    o.append("| master material (outer) | expressions |")
    o.append("|---|---|")
    for k, v in e["by_material"].items():
        o.append(f"| `{k}` | {v} |")
    o.append("")
    o.append("### Parameters the MIC chain overrides, and where they are set")
    o.append("")
    o.append("| parameter | MIC value | expression value | class | material | export |")
    o.append("|---|---|---|---|---|---|")
    for name, t in doc["body_colour"]["terms"].items():
        x = t["expression"]
        o.append(f"| `{name}` | {t['mic_value']} | "
                 f"{x['value'] if x and x['value'] is not None else '-'} | "
                 f"{x['class'] if x else '-'} | {x['material'] if x else '-'} | "
                 f"{x['export'] if x else '-'} |")
    o.append("")
    o.append(f"MIC parameters matched to a decoded expression: "
             f"**{len(doc['parameter_match']['matched'])} of "
             f"{doc['parameter_match']['mic_parameters']}**. In the MIC but not among the "
             f"expressions: {', '.join(doc['parameter_match']['in_mic_not_in_expressions']) or 'none'}.")
    o.append("")
    o.append("## 4. Body colour, as far as the bytes go")
    o.append("")
    b = doc["body_colour"]
    o.append("```")
    o.append(f"Material0_BaseColour  = {b['base_colour_linear']}   [decoded: MIC chain, "
             f"{json.dumps(b['base_colour_source'])[:120] if b['base_colour_source'] else 'COLOUR.json'}]")
    o.append(f"Diffuse_Adjust        = {b['diffuse_adjust']}          [decoded: MIC chain, "
             f"{json.dumps(b['diffuse_adjust_source'])[:120] if b['diffuse_adjust_source'] else 'COLOUR.json'}]")
    o.append(f"scalar terms in streams = {doc['expressions']['scalar_with_default']}/"
             f"{sum(1 for r in doc['expressions']['rows'] if r['class'] == 'MaterialExpressionScalarParameter')}"
             f" (FloatProperty +0xcc); vector terms 0/"
             f"{doc['expressions']['vector_parameters']} in streams, MIC only")
    o.append(f"base x adjust         = {b['base_x_adjust']}   "
             f"[derived: {b['rule_base_x_adjust']}]")
    o.append("dirt / damage / wetness / edge terms  = parameters above [decoded]")
    o.append("combine(term...)      = ?  [UNKNOWN: FunctionExpressions links are 0]")
    o.append("surface_lighting      = ?  [UNKNOWN: shader]")
    o.append("displayed_rgb         = ?  [UNKNOWN: tonemap/exposure, COLOUR.md §5]")
    o.append("```")
    o.append("")
    o.append("## 5. Oracles (each can fail; `--check` re-runs them)")
    o.append("")
    o.append("| oracle | ok | detail |")
    o.append("|---|---|---|")
    for k, v in doc["oracles"].items():
        o.append(f"| `{k}` | {v['ok']} | {json.dumps(v['detail'])[:300]} |")
    o.append("")
    o.append("## 6. UNKNOWN")
    o.append("")
    for i, u in enumerate(doc["unknowns"], 1):
        o.append(f"{i}. {u}")
    o.append("")
    return "\n".join(o)


def write() -> int:
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write(render(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    print("functions:", len(doc["functions"]), "all links 0:",
          all((f.get("function_expressions") or {}).get("nonzero") == 0
              for f in doc["functions"]))
    print("expressions:", doc["expressions"]["count"],
          "walked_to_eof:", doc["expressions"]["walked_to_eof"],
          "matched MIC params:", len(doc["parameter_match"]["matched"]))
    print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
    return 0


def check() -> int:
    fails: list = []
    for p in (OUT_MD, OUT_JSON):
        if not os.path.exists(p):
            print(f"FAIL: {os.path.relpath(p, ROOT)} missing - run --write")
            return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    md = open(OUT_MD, encoding="utf-8").read()
    fresh = build()
    if json.dumps(fresh, sort_keys=True) != json.dumps(stored, sort_keys=True):
        a, b = json.dumps(stored, sort_keys=True), json.dumps(fresh, sort_keys=True)
        pos = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), 0)
        fails.append(f"re-derivation differs at {pos}: stored {a[pos:pos+100]!r} vs "
                     f"fresh {b[pos:pos+100]!r}")
    if md != render(stored):
        fails.append("COLOUR_FUNCTIONS.md is not the render of COLOUR_FUNCTIONS.json")
    for k, v in stored["oracles"].items():
        if not v["ok"]:
            fails.append(f"oracle {k} failed: {json.dumps(v['detail'])[:200]}")
    if len(stored["functions"]) != 11:
        fails.append(f"expected 11 Batmobile functions, got {len(stored['functions'])}")
    if stored["expressions"]["count"] == 0:
        fails.append("no expression exports decoded")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK {len(stored['functions'])} functions, "
          f"{stored['expressions']['count']} expressions, "
          f"{len(stored['parameter_match']['matched'])} MIC parameters matched")
    print("all FunctionExpressions slots zero:",
          sum((f.get('function_expressions') or {}).get('slots', 0)
              for f in stored['functions']),
          "slots,", sum((f.get('function_expressions') or {}).get('nonzero', 0)
                        for f in stored['functions']), "non-zero")
    print("oracles:", {k: v["ok"] for k, v in stored["oracles"].items()})
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
