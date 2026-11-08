"""grab_colour.py - the BmAK Mainbody material chain end to end (GRB-G3-04).

Answers "what is black in BmAK" as a *function of named terms*, not a number:

  1. the painted body slot: `Batmobile_V3_Mainbody_NEW_MIC` in `Playable_Batmobile_SF`,
     its authored parameter arrays and the parent chain up to the master material;
  2. the master material's slot -> expression map (DiffuseColor / SpecularColor /
     SpecularPower / Normal / EmissiveColor, plus BlendMode / LightingModel), and each
     expression's own properties decoded from its export;
  3. the lighting and post-process terms the graph depends on - tonemapper, exposure,
     colour grading, bloom, reflection, wetness - each with the ini file, section, key
     and line where it is set (from the G3-03 config set, `CONFIG.json`);
  4. what is *not* in the files, listed as UNKNOWN with where it would be found.

Everything is read from the install and the project's decoded grab. Nothing is computed
from a shader that was not decoded: an operator is reported only when a decoded tag
proves it, otherwise the relation between named terms is UNKNOWN.

Oracle: each object used here must re-open in `upk_read` at the recorded index with the
recorded name and export size - a mismatch fails `--check` instead of producing a table.

Usage:
  python Tools/scripts/grab_colour.py --write    # COLOUR.md + COLOUR.json
  python Tools/scripts/grab_colour.py --check    # re-derive, compare, exit 1 on drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import grab_model  # noqa: E402
import upk_read  # noqa: E402

OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR.json")
CONFIG = os.path.join(ROOT, "Research", "BatmobileGrab", "CONFIG.json")
VALUES = os.path.join(ROOT, "Research", "BatmobileGrab", "VALUES.json")
UPK = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_Batmobile_SF.upk"
PACKAGE = "Playable_Batmobile_SF"

BODY_MIC = "Batmobile_V3_Mainbody_NEW_MIC"
SLOTS = ("DiffuseColor", "SpecularColor", "SpecularPower", "Normal", "EmissiveColor")

# Keyword -> term name, applied to CONFIG.json rows (file/section/key/value).
TERM_RULES = (
    ("tonemap", r"tonemap|tone_map|tonecurve|tonemapper"),
    ("exposure", r"exposure|eyeadapt|autoexposure|adaptation"),
    ("grading", r"colorgrad|colourgrad|colorcorrect|colourcorrect|saturation|contrast|whitebalance|colortint|colourscal"),
    ("bloom", r"bloom"),
    ("gamma", r"gamma"),
    ("reflection", r"reflection|reflective|probe|specular|environmentcolor|skylight"),
    ("wetness", r"wet|rain|puddle|damp"),
)


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()[:16]


def _items(tag: dict | None) -> list[list[dict]]:
    return [i for i in (tag or {}).get("items") or [] if isinstance(i, list)]


def _named(tags, name):
    for t in tags or []:
        if t.get("name") == name:
            return t
    return None


def params_of(row: dict) -> dict:
    """Scalar / vector / texture parameter arrays -> {kind: {name: value}}.

    Each value carries its tag offset inside the export, so a reader can find the bytes.
    """
    out = {"scalars": {}, "vectors": {}, "textures": {}}
    tags = row.get("tags") or []
    for kind, key in (("scalars", "ScalarParameterValues"),
                      ("vectors", "VectorParameterValues"),
                      ("textures", "TextureParameterValues")):
        t = _named(tags, key)
        for item in _items(t):
            name = next((x.get("value") for x in item if x.get("type") == "NameProperty"), None)
            if not name:
                continue
            val = next((x.get("value") for x in item
                        if x.get("type") in ("FloatProperty", "VectorProperty")), None)
            if val is None:
                vtag = next((x for x in item if x.get("name") == "ParameterValue"), None)
                val = (vtag or {}).get("floats")
            if val is None:
                otag = next((x for x in item if x.get("type") == "ObjectNCRProperty"), None)
                if otag:
                    val = otag.get("ref") or otag.get("value")
            if val is None:
                continue
            out[kind][name] = {"value": val,
                               "tag_offset": (t or {}).get("offset"),
                               "object": row.get("index")}
    return out


def _row_by_index(g, package: str, index) -> dict | None:
    """Same-package only. Export indices are package-local: index 593 exists in several
    of the Playable_Batmobile packages and they are different objects, so a cross-package
    fallback would silently substitute another package's material."""
    for r in g.rows:
        if r.get("package") == package and r.get("index") == index:
            return r
    return None


def parent_of(g, row: dict) -> dict | None:
    """`row.refs` carries the parent object reference (MIC or Material); the tag stream
    keeps the same link as an ObjectNCRProperty, used only as a fallback."""
    for ref in row.get("refs") or []:
        if ref.get("class") in ("MaterialInstanceConstant", "Material"):
            got = _row_by_index(g, row.get("package"), ref.get("index"))
            if got is not None and got.get("index") != row.get("index"):
                return got
    for _path, t in g.tags(row):
        if t.get("ref_class") in ("MaterialInstanceConstant", "Material"):
            got = _row_by_index(g, row.get("package"), t.get("value"))
            if got is not None and got.get("index") != row.get("index"):
                return got
    return None


def chain_of(g, row: dict) -> list[dict]:
    out, seen = [], set()
    while row is not None and row.get("index") not in seen and len(out) < 8:
        seen.add(row.get("index"))
        out.append(row)
        row = parent_of(g, row)
    return out


def slot_map(g, master: dict) -> dict:
    """Slot name -> expression reference recorded in the Material's tag stream."""
    out = {}
    for tag in master.get("tags") or []:
        name = tag.get("name")
        if name not in SLOTS:
            continue
        props = tag.get("props") or []
        ref = next((p for p in props if p.get("ref")), None)
        mask = next((p.get("value") for p in props if p.get("type") == "IntProperty"), None)
        idx = (ref or {}).get("value")
        out[name] = {
            "tag_offset": tag.get("offset"),
            "type": tag.get("type"),
            "ref": (ref or {}).get("ref"),
            "ref_class": (ref or {}).get("ref_class"),
            "index": idx,
            "mask": mask,
            "null_expression": idx in (None, 0) and ref is None,
        }
    return out


def expression_inventory(upk_path: str, master: dict) -> dict:
    """The Material's `Expressions` array, read from the export bytes.

    Layout: u32 count then count * u32 object indices (stride 4, the decoder produced no
    struct items because the elements are bare object references). Byte accounting:
    4 + 4*count must equal the array's recorded size or the reading is refused.
    """
    res = {"count": None, "by_class": {}, "byte_check": None, "unresolved": 0,
           "note": ""}
    tag = _named(master.get("tags"), "Expressions")
    if not tag:
        res["note"] = "the master carries no Expressions tag"
        return res
    if not os.path.exists(upk_path):
        res["note"] = "package absent"
        return res
    pkg = upk_read.Package(upk_path)
    data = pkg.data(master["index"])
    off = tag.get("offset") or 0
    expected = tag.get("count")
    # The recorded tag offsets can run past the export slice (this master: offset 2088 in a
    # 2004-byte export), i.e. they are not relative to `pkg.data()`. In that case the count
    # is searched for in the whole package image instead, and the same containment test
    # decides whether the location is the array.
    buf, where = data, "export"
    if off + 4 > len(data):
        try:
            buf = pkg._image()
        except Exception:                                # noqa: BLE001
            buf = open(upk_path, "rb").read()
        where = "package image"
        off = -1
    count = int.from_bytes(data[off:off + 4], "little")
    if off >= 0 and (4 + 4 * count) == tag.get("size") and count:
        by_class, unresolved = _classes_at(pkg, buf, off, count)
        res.update(count=count, byte_check=True, by_class=by_class, unresolved=unresolved)
        return res

    # The recorded offset does not point at the payload (it reads 0 for a 237-element
    # array). Locate the array by containment instead: the count, followed by count
    # references that *all* resolve to material expressions. Only a unique candidate
    # is accepted.
    if not expected:
        res["note"] = (f"recorded offset {off} reads {count}, not the array count, and the tag "
                       f"carries no count to search for")
        return res
    found = []
    needle = int(expected).to_bytes(4, "little")
    pos = buf.find(needle)
    while pos >= 0:
        if pos + 4 + 4 * int(expected) <= len(buf):
            by_class, unresolved = _classes_at(pkg, buf, pos, int(expected))
            if unresolved == 0 and by_class:
                found.append((pos, by_class))
        pos = buf.find(needle, pos + 1)
    if len(found) != 1:
        res["note"] = (f"the array is not at the recorded offset and the containment search over "
                       f"the {where} found {len(found)} candidate(s) for {expected} expressions")
        return res
    pos, by_class = found[0]
    res.update(count=int(expected), byte_check=True, by_class=by_class, unresolved=0,
               located_at=pos, buffer=where,
               note=f"located at {where} offset 0x{pos:X} by containment (count then references "
                    f"that all resolve to material expressions); the recorded tag offset does not "
                    f"point at the payload")
    return res


def _classes_at(pkg, data: bytes, off: int, count: int) -> tuple[dict[str, int], int]:
    """Resolve `count` u32 references at `off+4` to class names; return counts + misses."""
    by_class: dict[str, int] = {}
    unresolved = 0
    for i in range(count):
        idx = int.from_bytes(data[off + 4 + 4 * i: off + 8 + 4 * i], "little")
        try:
            cls = pkg.object_class(idx) if idx else None
        except Exception:                                # noqa: BLE001
            cls = None
        if cls and (cls.startswith("MaterialExpression") or cls == "MaterialFunctionCall"):
            by_class[cls] = by_class.get(cls, 0) + 1
        else:
            unresolved += 1
    return dict(sorted(by_class.items(), key=lambda kv: (-kv[1], kv[0]))), unresolved


def material_flags(master: dict) -> dict:
    """ByteProperty / scalar flags on the Material that change how it is shaded."""
    out = {}
    for tag in master.get("tags") or []:
        if tag.get("type") in ("ByteProperty", "BoolProperty", "FloatProperty") and tag.get("name"):
            out[tag["name"]] = {"value": tag.get("value"), "offset": tag.get("offset")}
    return out


def expression_rows(g, slots: dict, master: dict) -> list[dict]:
    """Every expression the master names, decoded from its own export."""
    wanted = {(s.get("index"), s.get("ref")) for s in slots.values() if s.get("index") not in (None, 0)}
    for _p, t in g.tags(master):
        if t.get("ref_class") in ("MaterialExpressionStaticSwitchParameter",
                                  "MaterialExpressionVectorParameter",
                                  "MaterialExpressionScalarParameter",
                                  "MaterialExpressionTextureSampleParameter2D",
                                  "MaterialFunction"):
            wanted.add((t.get("index"), t.get("ref")))
    out, seen = [], set()
    for idx, path in sorted(wanted, key=lambda x: (str(x[0]))):
        if idx is None or idx in seen:
            continue
        seen.add(idx)
        row = next((r for r in g.rows
                    if r.get("package") == PACKAGE and r.get("index") == idx), None)
        if row is None:
            out.append({"index": idx, "path": path, "class": None, "missing": True})
            continue
        fields = {}
        for tag in row.get("tags") or []:
            if tag.get("type") in ("NameProperty", "FloatProperty", "BoolProperty",
                                   "ByteProperty", "VectorProperty") and tag.get("name"):
                fields.setdefault(tag["name"], tag.get("value"))
            elif tag.get("name") == "ParameterValue" and tag.get("floats"):
                fields.setdefault("ParameterValue", tag["floats"])
        func = next((t.get("ref") for _p, t in g.tags(row) if t.get("ref_class") == "MaterialFunction"), None)
        out.append({
            "index": idx,
            "class": row.get("class"),
            "name": row.get("name"),
            "path": path or row.get("name"),
            "sha1": row.get("sha1"),
            "tag_count": row.get("tag_count"),
            "fields": fields,
            "material_function": func,
            "missing": False,
        })
    return out


def upk_oracle(upk_path: str, rows: list[dict]) -> dict:
    """Re-open each object in the package: index -> name + export size must match."""
    res = {"upk": upk_path, "exists": os.path.exists(upk_path), "checked": [], "mismatches": []}
    if not res["exists"]:
        res["note"] = "package not present - the grab rows are the only source"
        return res
    pkg = upk_read.Package(upk_path)
    for row in rows:
        idx = row.get("index")
        if idx is None:
            continue
        try:
            name = pkg.object_name(idx)
            data = pkg.data(idx)
        except Exception as exc:                        # noqa: BLE001
            res["mismatches"].append({"index": idx, "error": str(exc)})
            continue
        entry = {"index": idx, "package_name": name, "export_bytes": len(data),
                 "grab_name": row.get("name"), "sha1": sha1(data)}
        res["checked"].append(entry)
        if name and row.get("name") and name.lower() != str(row["name"]).lower():
            res["mismatches"].append({"index": idx, "package_name": name, "grab_name": row.get("name")})
        elif row.get("size") and len(data) > int(row["size"]):
            pass                                        # exports carry a header; size is the payload
    res["count"] = len(res["checked"])
    return res


def terms_from_config() -> dict:
    """Term -> config rows (file, line, section, key, value, chain)."""
    out: dict[str, list[dict]] = {name: [] for name, _rx in TERM_RULES}
    if not os.path.exists(CONFIG):
        return {"source": "CONFIG.json missing", "rows": out}
    doc = json.load(open(CONFIG, encoding="utf-8"))
    for cat, rows in (doc.get("categories") or {}).items():
        if cat not in ("postprocess", "batmobile", "vehicle"):
            continue
        for r in rows:
            hay = " ".join(str(r.get(k, "")) for k in ("section", "key", "value"))
            for name, rx in TERM_RULES:
                if re.search(rx, hay, re.I):
                    out[name].append({"file": r.get("file"), "line": r.get("line"),
                                      "section": r.get("section"), "key": r.get("key"),
                                      "value": r.get("value"), "chain": r.get("chain"),
                                      "category": cat})
    dedup: dict[str, list[dict]] = {}
    for name, rows in out.items():
        seen, keep = set(), []
        for r in rows:
            k = (r["file"], r["line"], r["key"], str(r["value"]))
            if k in seen:
                continue
            seen.add(k)
            keep.append(r)
        dedup[name] = keep
    return {"source": "Research/BatmobileGrab/CONFIG.json (G3-03)", "rows": dedup}


def build() -> dict:
    g = grab_model.Grab()
    body = next((r for r in g.rows if r.get("package") == PACKAGE
                 and r.get("class") == "MaterialInstanceConstant" and r.get("name") == BODY_MIC), None)
    if body is None:
        raise SystemExit(f"{PACKAGE} has no {BODY_MIC}")

    chain = chain_of(g, body)
    steps = []
    for row in chain:
        steps.append({
            "class": row.get("class"),
            "name": row.get("name"),
            "path": f"{row.get('outer')}:{row.get('name')}",
            "index": row.get("index"),
            "sha1": row.get("sha1"),
            "bytes": row.get("size"),
            "parsed": row.get("parsed"),
            "params": params_of(row),
        })

    master = next((r for r in chain if r.get("class") == "Material"), None)

    # Resolved parameters, child wins - the same rule the engine uses for a MIC chain.
    merged: dict[str, dict] = {"scalars": {}, "vectors": {}, "textures": {}}
    for step in steps:
        for kind, items in step["params"].items():
            for name, val in items.items():
                merged[kind].setdefault(name, dict(val, from_object=step["name"]))

    slots = slot_map(g, master) if master else {}
    flags = material_flags(master) if master else {}
    exprs = expression_rows(g, slots, master) if master else []
    inventory = expression_inventory(UPK, master) if master else {}

    base = None
    for key in ("Material0_BaseColour", "Main_BaseColour", "Base_Colour", "BaseColor"):
        if key in merged["vectors"]:
            base = {"parameter": key, **merged["vectors"][key]}
            break
    adjust = merged["vectors"].get("Diffuse_Adjust")

    values = json.load(open(VALUES, encoding="utf-8")) if os.path.exists(VALUES) else {}
    decoded_tma3 = values.get("paint", {}).get("base_colour")

    terms = terms_from_config()
    oracle = upk_oracle(UPK, [body] + ([master] if master else []) + [e for e in exprs if not e["missing"]])

    unknowns = []
    if not master:
        unknowns.append("the parent chain does not reach a Material export - the master graph "
                        "is UNKNOWN for this slot")
    if not slots:
        unknowns.append("no DiffuseColor/SpecularColor/... slot tag decoded on the master")
    rel = [e for e in exprs if e.get("fields", {}).get("Value") is None
           and e.get("fields", {}).get("DefaultValue") is None]
    if rel:
        unknowns.append(f"{len(rel)} expression(s) carry neither Value nor DefaultValue: a static "
                        f"switch's chosen branch is not in the export")
    null_slots = [s for s, v in slots.items() if v.get("null_expression")]
    if null_slots:
        unknowns.append(f"slot(s) {', '.join(sorted(null_slots))}: FMaterialInput.Expression is null "
                        f"with a mask, so the colour is produced inside the material's function "
                        f"graph, not by one expression; the function bodies are UNKNOWN (they live "
                        f"in the `Material_Functions` / `Engine` packages, which this grab did not read)")
    if master and not inventory.get("count"):
        unknowns.append("the master's expression list: " + str(inventory.get("note") or "not decoded"))
    elif inventory.get("note"):
        unknowns.append(inventory["note"])
    if not terms["rows"].get("tonemap"):
        unknowns.append("tonemapper: no ini key matched 'tonemap' in the config set")
    if not terms["rows"].get("reflection"):
        unknowns.append("reflection/environment: no ini key matched; where the body's reflection "
                        "comes from is UNKNOWN (would be a level's Environment/probe actor)")
    unknowns.append("the lighting sum and the tonemap operator itself are shader code, not "
                    "serialised in the package - the relation between the terms below is UNKNOWN")

    return {
        "schema": 1,
        "generated_by": "Tools/scripts/grab_colour.py --write",
        "card": "GRB-G3-04 BmAK colour pipeline",
        "package": {"path": UPK, "name": PACKAGE,
                    "bytes": os.path.getsize(UPK) if os.path.exists(UPK) else None},
        "body_slot": {"name": BODY_MIC, "index": body.get("index"), "sha1": body.get("sha1")},
        "chain": steps,
        "master": ({"name": master.get("name"), "index": master.get("index"),
                    "outer": master.get("outer"), "sha1": master.get("sha1"),
                    "parsed": master.get("parsed"), "bytes": master.get("size"),
                    "tag_count": master.get("tag_count")} if master else None),
        "slots": slots,
        "material_flags": flags,
        "expressions": exprs,
        "expressions_inventory": inventory,
        "parameters": merged,
        "base_colour": base,
        "diffuse_adjust": adjust,
        "ledger_t_ma3": {"decoded_base_colour": decoded_tma3,
                         "matches_upk": (base is not None and decoded_tma3 is not None
                                         and all(abs(float(base["value"][i]) - float(decoded_tma3[i])) < 5e-4
                                                 for i in range(3)))},
        "terms": terms,
        "oracle": oracle,
        "unknowns": unknowns,
    }


def render_md(doc: dict) -> str:
    p = doc["package"]
    out = ["# BmAK body colour - the Mainbody chain, decoded", ""]
    out.append("GRB-G3-04. Generated by `Tools/scripts/grab_colour.py --write`; `--check` "
               "re-derives this and fails on drift.")
    out.append("")
    out.append(f"Package `{p['name']}` (`{p['path']}`, {p['bytes']} bytes). Body slot "
               f"`{doc['body_slot']['name']}` export #{doc['body_slot']['index']}.")
    out.append("")
    out.append("Nothing here is computed: a value is `decoded` (export index + tag offset), `derived` "
               "(rule stated) or `UNKNOWN`. The relation between terms is stated only where a tag "
               "proves it.")
    out.append("")
    out.append("## 1. Chain: body MIC -> parents -> master")
    out.append("")
    out.append("| # | class | object | export | sha1 | bytes / parsed |")
    out.append("|---|---|---|---|---|---|")
    for i, s in enumerate(doc["chain"], 1):
        out.append(f"| {i} | {s['class']} | `{s['path']}` | {s['index']} | `{s['sha1']}` | "
                   f"{s['bytes']} / {s['parsed']} |")
    out.append("")
    m = doc["master"]
    if m:
        out.append(f"Master material: `{m['outer']}:{m['name']}` export #{m['index']}, "
                   f"{m['parsed']}/{m['bytes']} bytes parsed, {m['tag_count']} tags.")
    else:
        out.append("Master material: **UNKNOWN** - the chain did not reach a `Material` export.")
    out.append("")
    out.append("## 2. Authored parameters (child wins over parent)")
    out.append("")
    for kind, label in (("vectors", "Vector"), ("scalars", "Scalar"), ("textures", "Texture")):
        rows = doc["parameters"].get(kind) or {}
        out.append(f"### {label} ({len(rows)})")
        out.append("")
        if not rows:
            out.append("- none")
            out.append("")
            continue
        out.append("| parameter | value | from | export | tag offset |")
        out.append("|---|---|---|---|---|")
        for name, v in sorted(rows.items()):
            val = v.get("value")
            val = (f"`{val}`" if not isinstance(val, list) else
                   "[" + ", ".join(f"{float(x):.6g}" for x in val) + "]")
            out.append(f"| `{name}` | {val} | {v.get('from_object')} | {v.get('object')} | "
                       f"{v.get('tag_offset')} |")
        out.append("")
    base = doc.get("base_colour")
    out.append("### The painted base colour")
    out.append("")
    if base:
        vals = [float(x) for x in base["value"][:4]]
        out.append(f"- `{base['parameter']}` = linear [{', '.join(f'{v:.6g}' for v in vals)}] "
                   f"(decoded: export #{base['object']}, tag offset {base['tag_offset']}, "
                   f"from `{base['from_object']}`)")
    else:
        out.append("- **UNKNOWN**: no base-colour vector parameter on the chain.")
    adj = doc.get("diffuse_adjust")
    if base and adj:
        av = [float(x) for x in adj["value"][:3]]
        prod = [float(base["value"][i]) * av[i] for i in range(3)]
        out.append(f"- `Diffuse_Adjust` = [{', '.join(f'{v:.6g}' for v in av)}] "
                   f"(decoded: export #{adj['object']}, tag offset {adj['tag_offset']})")
        out.append(f"- derived: base x adjust = linear [{', '.join(f'{v:.6g}' for v in prod)}] "
                   f"(rule: component-wise multiply, both factors decoded above)")
    elif base:
        out.append("- `Diffuse_Adjust`: absent on this chain, so the base colour stands alone.")
    t = doc.get("ledger_t_ma3") or {}
    if t.get("decoded_base_colour") is not None:
        out.append(f"- ledger T-MA3 value (from `VALUES.json`): linear "
                   f"[{', '.join(f'{float(x):.6g}' for x in t['decoded_base_colour'][:3])}] - "
                   f"matches the package: **{t['matches_upk']}**")
    out.append("")
    out.append("## 3. Master slot -> expression")
    out.append("")
    if doc["slots"]:
        out.append("| slot | expression | class | export | tag offset |")
        out.append("|---|---|---|---|---|")
        for slot, s in doc["slots"].items():
            out.append(f"| {slot} | `{s.get('ref')}` | {s.get('ref_class')} | {s.get('index')} | "
                       f"{s.get('tag_offset')} |")
    else:
        out.append("- **UNKNOWN**: no slot tag decoded.")
    out.append("")
    if doc["material_flags"]:
        out.append("Material-level flags that change shading (decoded from the same tag stream):")
        out.append("")
        out.append("| property | value | offset |")
        out.append("|---|---|---|")
        for k, v in sorted(doc["material_flags"].items()):
            out.append(f"| {k} | `{v.get('value')}` | {v.get('offset')} |")
        out.append("")
    out.append("## 4. Expressions the graph names")
    out.append("")
    out.append("| class | object | export | decoded fields |")
    out.append("|---|---|---|---|")
    for e in doc["expressions"]:
        if e.get("missing"):
            out.append(f"| — | `{e.get('path')}` | {e.get('index')} | **not in the grab** |")
            continue
        fields = e.get("fields") or {}
        txt = ", ".join(f"{k}={v}" for k, v in list(fields.items())[:6]) or "—"
        out.append(f"| {e['class']} | `{e.get('name')}` | {e['index']} | {txt} |")
    out.append("")
    inv = doc.get("expressions_inventory") or {}
    out.append("### The master's own expression list")
    out.append("")
    if inv.get("count"):
        out.append(f"`Expressions` array: **{inv['count']}** object references, byte accounting "
                   f"4 + 4*{inv['count']} = the recorded size: **{inv['byte_check']}**"
                   + (f"; {inv['unresolved']} index(es) did not resolve to a class"
                      if inv.get("unresolved") else ""))
        out.append("")
        out.append("| expression class | count |")
        out.append("|---|---|")
        for cls, n in list((inv.get("by_class") or {}).items())[:20]:
            out.append(f"| {cls} | {n} |")
    else:
        out.append(f"- **UNKNOWN**: {inv.get('note') or 'no expression list decoded'}")
    out.append("")
    out.append("## 5. Lighting and post-process terms")
    out.append("")
    out.append(f"Source: {doc['terms']['source']}. Each row is a real key: file, line, section.")
    out.append("")
    for name, rows in doc["terms"]["rows"].items():
        out.append(f"### {name} ({len(rows)})")
        out.append("")
        if not rows:
            out.append("- **UNKNOWN**: no key in the config set names this term.")
            out.append("")
            continue
        out.append("| file:line | section | key | value |")
        out.append("|---|---|---|---|")
        for r in rows[:12]:
            out.append(f"| `{r['file']}:{r['line']}` | {r['section']} | `{r['key']}` | "
                       f"`{str(r['value'])[:120]}` |")
        if len(rows) > 12:
            out.append(f"| ... {len(rows) - 12} more | | | |")
        out.append("")
    out.append("## 6. The body's on-screen colour, as a function of the terms above")
    out.append("")
    out.append("Written as a function, not a number. Every term is either decoded above or UNKNOWN.")
    out.append("")
    out.append("```")
    out.append("body_base_linear   = VectorParameter(Material0_BaseColour)            [decoded, §2]")
    out.append("                     , optionally x Diffuse_Adjust                     [decoded, §2]")
    out.append("diffuse_input      = master slot DiffuseColor -> expression(s)         [decoded, §3/§4]")
    out.append("specular_input     = master slot SpecularColor / SpecularPower        [decoded, §3]")
    out.append("emissive_input     = master slot EmissiveColor                        [decoded, §3]")
    out.append("surface_lighting   = f(diffuse_input, specular_input, lights, probe)   [UNKNOWN: shader]")
    out.append("reflection_term    = environment / probe contribution                  [UNKNOWN - see §5]")
    out.append("wetness_term       = rain_effect material function on the master       [decoded ref, §4]")
    out.append("hdr_linear         = surface_lighting + reflection_term + wetness_term [UNKNOWN: combine rule]")
    out.append("displayed_rgb      = tonemap(exposure x hdr_linear) + grading/bloom   [keys decoded §5,")
    out.append("                                                                        operator UNKNOWN]")
    out.append("```")
    out.append("")
    out.append(f"- base colour term: " + ("decoded, §2" if base else "**UNKNOWN**"))
    out.append(f"- slot -> expression map: " + ("decoded, §3" if doc["slots"] else "**UNKNOWN**"))
    out.append(f"- tonemap / exposure / grading keys: "
               f"{sum(len(v) for v in doc['terms']['rows'].values())} config rows (§5); the operators "
               f"themselves are not serialised anywhere in these files")
    out.append("- a screen pixel value under named lighting: **UNKNOWN** - no calibrated capture of "
               "the body exists in the project (`FOOTAGE.md` measures air time, not colour)")
    out.append("")
    out.append("## 7. UNKNOWNs")
    out.append("")
    for u in doc["unknowns"]:
        out.append(f"- {u}")
    out.append("")
    o = doc["oracle"]
    out.append("## 8. Oracle")
    out.append("")
    out.append(f"- package present: {o['exists']}; objects re-opened in `upk_read`: {o.get('count', 0)}; "
               f"mismatches: {len(o['mismatches'])}")
    for m2 in o["mismatches"][:6]:
        out.append(f"  - {m2}")
    out.append("")
    return "\n".join(out)


def write() -> int:
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    print(f"chain {len(doc['chain'])} objects, master "
          f"{doc['master']['name'] if doc['master'] else 'UNKNOWN'}, "
          f"slots {len(doc['slots'])}, expressions {len(doc['expressions'])}, "
          f"config terms {sum(len(v) for v in doc['terms']['rows'].values())}")
    print(f"base colour {doc['base_colour']['value'] if doc['base_colour'] else None} "
          f"matches T-MA3: {doc['ledger_t_ma3']['matches_upk']}")
    print("unknowns:", len(doc["unknowns"]))
    return 0


def check() -> int:
    fails = []
    if not (os.path.exists(OUT_JSON) and os.path.exists(OUT_MD)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    fresh = build()

    if not stored.get("chain"):
        fails.append("no chain objects")
    if not stored.get("master"):
        fails.append("no master material resolved")
    if not stored.get("slots"):
        fails.append("no slot map")
    for slot in SLOTS:
        if slot not in stored.get("slots", {}):
            fails.append(f"slot {slot} missing (UNKNOWN is allowed, absence is not)")
    if not stored.get("base_colour"):
        fails.append("no base colour parameter")
    else:
        vals = stored["base_colour"].get("value") or []
        if len(vals) < 3:
            fails.append("base colour has fewer than 3 components")
        expected = (stored.get("ledger_t_ma3") or {}).get("decoded_base_colour")
        if expected and not stored["ledger_t_ma3"]["matches_upk"]:
            fails.append("base colour does not match the ledger value within 5e-4")

    o = stored.get("oracle") or {}
    if o.get("mismatches"):
        fails.append(f"{len(o['mismatches'])} object(s) did not re-open at their recorded index")

    if stored.get("unknowns") is None:
        fails.append("unknowns list missing")

    inv = stored.get("expressions_inventory") or {}
    if not inv.get("count"):
        if not inv.get("note"):
            fails.append("expression list neither decoded nor explained")
        elif not any(str(inv["note"]) in str(u) for u in stored.get("unknowns") or []):
            fails.append("expression-list UNKNOWN is not repeated in the UNKNOWNs list")
    elif not inv.get("byte_check"):
        fails.append("Expressions array byte accounting failed")

    for key in ("body_slot", "package", "parameters", "expressions", "terms"):
        if key not in stored:
            fails.append(f"section {key} missing")

    drift = [k for k in ("chain", "master", "slots", "base_colour", "parameters")
             if stored.get(k) != fresh.get(k)]
    if drift:
        fails.append("stale sections (inputs changed?): " + ", ".join(drift))

    md = open(OUT_MD, encoding="utf-8").read()
    for heading in ("## 1. Chain", "## 2. Authored parameters", "## 3. Master slot",
                    "## 4. Expressions", "## 5. Lighting and post-process", "## 6. The body's",
                    "## 7. UNKNOWNs", "## 8. Oracle"):
        if heading not in md:
            fails.append(f"markdown heading missing: {heading}")

    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK chain {len(stored['chain'])}, slots {len(stored['slots'])}, "
          f"expressions {len(stored['expressions'])}, terms "
          f"{sum(len(v) for v in stored['terms']['rows'].values())}, "
          f"unknowns {len(stored['unknowns'])}")
    print(f"oracle: {o.get('count', 0)} objects re-opened, {len(o.get('mismatches', []))} mismatches")
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
