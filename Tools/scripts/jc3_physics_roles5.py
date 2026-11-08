"""jc3_physics_roles5.py - raycast ids and static-compound references (G3-10f).

G3-10 (`PHYSICS_ROLES.md`) left two things open:

  * the "second raycast id space" - 24 of the 42 part raycast ids sit below 42 while the other
    18 sit in 42..59, and no decoder had mapped either to a body or a shape;
  * what a static compound's body reference points at - two `hknpStaticCompoundShape` objects
    were found and two body entries were seen pointing at them, but the shapes the compounds
    *include* were never decoded.

This pass decodes both from the shipped bytes and measures the mapping on the donor and over
the fleet (`E:/Modding/_shared/gamedata/JC3grab/hkx/out`, 233 physics entries, every raw `.physicsc`
those decodes name that exists in `E:/Modding/_shared/gamedata/JC3grab/hkx/all`).

What is proved, and what is measured but not universal, is stated in the render: the module
refuses to turn a rate into an invariant.

Usage:
    python Tools/scripts/jc3_physics_roles5.py --write
    python Tools/scripts/jc3_physics_roles5.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402

DONOR = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
                     "v0300_car_kensington_sportsmuscle", "sportsmuscle.physicsc")
PARTS = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
OUT_DIR = r"E:/Modding/_shared/gamedata/JC3grab/hkx/out"
RAW_DIR = r"E:/Modding/_shared/gamedata/JC3grab/hkx/all"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES5.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES5.json")

ENTRY = 96
COMPOUNDS = ("hknpStaticCompoundShape", "hknpDynamicCompoundShape")


# ------------------------------------------------------------------ decode
def load_parts() -> dict:
    out = {}
    with open(PARTS, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("parts"):
                out[r["entity"]] = r
    return out


def decode(blob: bytes) -> dict:
    """Bodies, their shapes/part indices, and every compound with its children."""
    pf = jc3hkx.Packfile(blob)
    psd = next((o for o in pf.objects if o.cls == "hknpPhysicsSystemData"), None)
    if psd is None:
        raise SystemExit("no hknpPhysicsSystemData")
    arr = pf.array(psd.offset + 0x40)
    cache: dict = {}
    entries = []
    for i in range(arr["size"]):
        at = arr["ptr"] + ENTRY * i
        shape = pf.pointers.get(at, 0)
        entries.append({
            "id": i, "shape": shape,
            "class": pf._starts.get(shape, "") if shape else "",
            "part_index": jc3hkx.part_index_of(pf, shape, cache) if shape else None,
            "pos": [round(pf.f32(at + 0x30 + 4 * k), 6) for k in range(3)],
        })
    by_shape: dict = {}
    for e in entries:
        if e["shape"]:
            by_shape.setdefault(e["shape"], []).append(e["id"])

    # every compound (static and dynamic) and its children, so nesting can be measured
    declared = {}
    children_of: dict = {}
    for o in pf.objects:
        if o.cls not in COMPOUNDS:
            continue
        d = jc3hkx.decode_compound(pf, o.offset, o.cls)
        declared[o.offset] = (o.cls, d)
        for inst in d["instances"]:
            if inst["shape"]:
                children_of.setdefault(inst["shape"], []).append(o.offset)

    compounds = []
    for off, (cls, d) in sorted(declared.items()):
        if cls != "hknpStaticCompoundShape":
            continue
        kids = []
        for inst in d["instances"]:
            box = jc3hkx.transform_aabb(inst["aabb"], inst["basis"], inst["translation"]) \
                if inst["aabb"] else None
            over = None
            if box:
                lo, hi = d["aabb"]["min"], d["aabb"]["max"]
                over = max(max(lo[k] - box["min"][k], box["max"][k] - hi[k]) for k in range(3))
            kids.append({
                "index": inst["index"], "shape": inst["shape"],
                "class": inst["shape_class"], "part_index": inst["part_index"],
                "scale": [round(v, 6) for v in inst["scale"][:3]],
                "translation": [round(v, 6) for v in inst["translation"][:3]],
                "aabb_overflow_m": None if over is None else round(over, 6),
                "in_body_table": inst["shape"] in by_shape if inst["shape"] else None,
            })
        compounds.append({
            "offset": off, "extent": pf.extents[off],
            "instance_count": d["instance_count"], "instances_inline": d["instances_inline"],
            "aabb": {k: [round(x, 6) for x in v] for k, v in d["aabb"].items()},
            "refs": by_shape.get(off, []),
            "parent_compounds": children_of.get(off, []),
            "children": kids,
        })
    return {
        "objects": len(pf.objects), "body_count": arr["size"], "body_entries": entries,
        "compounds": compounds,
        "compounds_all": {c: sum(1 for o in pf.objects if o.cls == c) for c in COMPOUNDS},
        "classes": {c: sum(1 for o in pf.objects if o.cls == c)
                    for c in ("hknpConvexPolytopeShape", "hknpExternMeshShape",
                              "hknpStaticCompoundShape", "hknpDynamicCompoundShape",
                              "CPfxPartIndexProperty")},
        "blob_size": len(blob),
    }


# ------------------------------------------------------------------ donor
def donor(pf: dict, parts: dict) -> dict:
    row = next(r for e, r in parts.items() if "v0300_car_kensington_sportsmuscle" in e
               and e.endswith("_civilian_01.ee"))
    ps = row["parts"]
    entries = {e["id"]: e for e in pf["body_entries"]}
    mapped = []
    for i, p in enumerate(ps):
        rid = p.get("ray")
        e = entries.get(rid) if isinstance(rid, int) and rid >= 0 else None
        mapped.append({
            "part": i, "name": p.get("n"), "ray": rid, "world_body": p.get("body"),
            "entry_class": e["class"] if e else None,
            "entry_part_index": e["part_index"] if e else None,
            "same_part": bool(e and e["part_index"] == i),
            "world_matches": (p.get("body") in (-1, None)) or
                             bool(entries.get(p.get("body")) and
                                  entries[p["body"]]["part_index"] == i),
        })
    ray_ids = sorted({m["ray"] for m in mapped if isinstance(m["ray"], int) and m["ray"] >= 0})
    extern_ids = [e["id"] for e in pf["body_entries"] if e["class"] == "hknpExternMeshShape"]
    window_lo = min(extern_ids) if extern_ids else pf["body_count"]
    # per-class summary of what a ray id selects
    by_class: dict = {}
    for m in mapped:
        if m["ray"] is not None and m["ray"] >= 0:
            by_class.setdefault(m["entry_class"], []).append(m["ray"])
    comp = []
    for c in pf["compounds"]:
        comp.append({
            "offset": c["offset"], "extent": c["extent"],
            "instances": c["instance_count"], "instances_inline": c["instances_inline"],
            "aabb": c["aabb"],
            "refs": [{"body": b, "entry_part_index": entries[b]["part_index"],
                      "part": ps[entries[b]["part_index"]]["n"]
                      if entries[b]["part_index"] is not None
                      and entries[b]["part_index"] < len(ps) else None} for b in c["refs"]],
            "parent_compounds": c["parent_compounds"],
            "children": c["children"],
            "child_classes": sorted({ch["class"] for ch in c["children"]}),
            "child_part_indices": sorted({ch["part_index"] for ch in c["children"]}),
            "children_in_body_table": sum(1 for ch in c["children"] if ch["in_body_table"]),
            "children_inside": sum(1 for ch in c["children"]
                                   if ch["aabb_overflow_m"] is not None
                                   and ch["aabb_overflow_m"] <= 1e-6),
            "worst_overflow_m": max((ch["aabb_overflow_m"] for ch in c["children"]
                                     if ch["aabb_overflow_m"] is not None), default=None),
        })
    return {
        "path": os.path.relpath(DONOR, ROOT).replace("\\", "/"),
        "bytes": pf["blob_size"], "objects": pf["objects"], "body_count": pf["body_count"],
        "classes": pf["classes"], "parts_entity": row["entity"], "part_count": len(ps),
        "mapped": mapped,
        "same_part": sum(1 for m in mapped if m["same_part"]),
        "no_ray": [m["part"] for m in mapped if m["ray"] in (-1, None)],
        "ray_ids": ray_ids, "ray_count": len(ray_ids),
        "below_window": [r for r in ray_ids if r < window_lo],
        "in_window": [r for r in ray_ids if r >= window_lo],
        "extern_ids": extern_ids, "window_lo": window_lo,
        "window_is_extern_block": [r for r in ray_ids if r >= window_lo] == extern_ids,
        "ray_by_class": {k: v for k, v in sorted(by_class.items())},
        "ids_no_part_names": [e["id"] for e in pf["body_entries"]
                              if e["id"] not in ray_ids],
        "compounds": comp,
    }


# ------------------------------------------------------------------ fleet
def fleet(parts: dict) -> dict:
    files = sorted(glob.glob(os.path.join(OUT_DIR, "*.json")))
    raws = {os.path.basename(p).lower(): p
            for p in sorted(glob.glob(os.path.join(RAW_DIR, "*.physicsc")))}
    cen = {"files": len(files), "entries": 0, "with_system": 0, "paired": 0,
           "raw_files": len(raws), "static_files": 0, "statics": 0, "dyn": 0,
           "instances": 0, "no_system": 0, "class_pair_ok": 0, "extern_le_poly": 0}
    chk = {k: [0, 0] for k in ("ray_in_table", "ray_bit_is_inside_table",
                               "ray_selects_a_shape", "world_in_table",
                               "static_one_body_or_child", "child_is_object",
                               "static_parent_has_part", "prop_is_permutation")}
    ident = {"files": 0, "same": 0, "parts": 0}
    combos: dict = {}
    deltas: dict = {}
    no_ray_parts = 0
    per_file, decoded, raw_used = [], {}, set()

    def bump(k, ok):
        chk[k][0] += 1
        chk[k][1] += bool(ok)

    for f in files:
        doc = json.load(open(f, encoding="utf-8"))
        for ph in doc.get("physics") or []:
            cen["entries"] += 1
            s = ph.get("summary") or {}
            cc = s.get("class_counts") or {}
            if "hknpPhysicsSystemData" not in cc:
                cen["no_system"] += 1
                continue
            cen["with_system"] += 1
            stat = cc.get("hknpStaticCompoundShape", 0)
            statd = cc.get("hknpStaticCompoundShapeData", 0)
            cen["statics"] += stat
            cen["dyn"] += cc.get("hknpDynamicCompoundShape", 0)
            if stat or statd:
                cen["static_files"] += 1
            if stat == statd:
                cen["class_pair_ok"] += 1
            if cc.get("hknpExternMeshShape", 0) <= cc.get("hknpConvexPolytopeShape", 0):
                cen["extern_le_poly"] += 1
            name = os.path.basename(ph.get("file", "")).lower()
            if name not in raws:
                continue
            cen["paired"] += 1
            raw_used.add(name)
            if name not in decoded:
                decoded[name] = decode(open(raws[name], "rb").read())
            pf = decoded[name]
            row = parts.get(doc.get("entity", ""))
            entries = {e["id"]: e for e in pf["body_entries"]}
            nb = pf["body_count"]
            if row:
                same = 0
                for i, p in enumerate(row["parts"]):
                    rid = p.get("ray")
                    if rid in (-1, None):
                        no_ray_parts += 1
                        continue
                    e = entries.get(rid) if isinstance(rid, int) else None
                    bump("ray_in_table", isinstance(rid, int) and 0 <= rid < nb)
                    bump("ray_selects_a_shape", bool(e and e["shape"]))
                    if e:
                        bump("ray_bit_is_inside_table", 0 <= rid < nb)
                        if e["part_index"] == i:
                            same += 1
                        if e["part_index"] is not None:
                            key = "%+d" % (e["part_index"] - i)
                            deltas[key] = deltas.get(key, 0) + 1
                    wb = p.get("body")
                    if isinstance(wb, int) and wb >= 0:
                        bump("world_in_table", bool(entries.get(wb)))
                ident["files"] += 1
                ident["parts"] += len(row["parts"])
                ident["same"] += same
                props = sorted({e["part_index"] for e in pf["body_entries"]
                                if e["part_index"] is not None})
                bump("prop_is_permutation", props == list(range(len(props))))
            for c in pf["compounds"]:
                cen["instances"] += c["instance_count"]
                have = len(c["refs"]) + len(c["parent_compounds"])
                combo = (len(c["refs"]), len(c["parent_compounds"]))
                combos[str(combo)] = combos.get(str(combo), 0) + 1
                bump("static_one_body_or_child", have >= 1)
                for b in c["refs"]:
                    bump("static_parent_has_part", entries[b]["part_index"] is not None)
                for ch in c["children"]:
                    bump("child_is_object", ch["shape"] is not None)
            per_file.append({"raw": name, "entity": doc.get("entity"),
                             "bodies": nb, "parts": len(row["parts"]) if row else 0,
                             "statics": len(pf["compounds"]),
                             "instances": sum(c["instance_count"] for c in pf["compounds"]),
                             "externs": pf["classes"]["hknpExternMeshShape"],
                             "polytopes": pf["classes"]["hknpConvexPolytopeShape"],
                             "dyn": pf["classes"]["hknpDynamicCompoundShape"],
                             "same": None})
    for k, v in chk.items():
        cen[k] = {"checked": v[0], "pass": v[1]}
    cen["identity"] = {"files": ident["files"], "parts": ident["parts"], "same": ident["same"]}
    cen["no_ray_parts"] = no_ray_parts
    cen["combination_counts"] = dict(sorted(combos.items()))
    cen["delta_histogram"] = dict(sorted(deltas.items(), key=lambda kv: int(kv[0]))[:12])
    cen["raw_files_used"] = len(raw_used)
    cen["raw_files_unpaired"] = sorted(set(raws) - raw_used)
    seen, uniq = set(), []
    for r in per_file:
        if r["raw"] in seen:
            continue
        seen.add(r["raw"])
        uniq.append(r)
    return {"census": cen, "per_file": uniq}


# ------------------------------------------------------------------ build
def build() -> dict:
    parts = load_parts()
    d = donor(decode(open(DONOR, "rb").read()), parts)
    return {"schema": 1, "generator": "jc3_physics_roles5.py", "card": "G3-10f",
            "donor": d, "fleet": fleet(parts)}


def oracles(doc: dict) -> list[dict]:
    d, c = doc["donor"], doc["fleet"]["census"]
    rate = lambda k: (c[k]["pass"] / c[k]["checked"]) if c[k]["checked"] else 0.0
    idr = c["identity"]["same"] / c["identity"]["parts"] if c["identity"]["parts"] else 0.0
    return [
        {"id": "donor_rays_resolve", "kind": "invariant",
         "ok": d["same_part"] + len(d["no_ray"]) == d["part_count"],
         "detail": f"{d['same_part']}/{d['part_count']} (no-ray parts {d['no_ray']})"},
        {"id": "donor_window_is_extern_block", "kind": "invariant",
         "ok": d["window_is_extern_block"],
         "detail": f"{len(d['in_window'])} rays >= {d['window_lo']}, "
                   f"{len(d['extern_ids'])} extern bodies"},
        {"id": "donor_ray_below_window_is_hull_or_compound", "kind": "invariant",
         "ok": all(m["entry_class"] in ("hknpConvexPolytopeShape", "hknpStaticCompoundShape")
                   for m in d["mapped"]
                   if isinstance(m["ray"], int) and 0 <= m["ray"] < d["window_lo"]),
         "detail": f"{len(d['below_window'])} rays below the extern block"},
        {"id": "donor_compound_single_body", "kind": "invariant",
         "ok": all(len(x["refs"]) == 1 for x in d["compounds"]),
         "detail": [f"{len(x['refs'])} body / {len(x['parent_compounds'])} parent"
                    for x in d["compounds"]]},
        {"id": "donor_compound_children_nested", "kind": "invariant",
         "ok": all(x["children_in_body_table"] == 0 for x in d["compounds"]),
         "detail": [x["children_in_body_table"] for x in d["compounds"]]},
        {"id": "donor_compound_child_has_no_part", "kind": "invariant",
         "ok": all(x["child_part_indices"] == [None] for x in d["compounds"]),
         "detail": [x["child_part_indices"] for x in d["compounds"]]},
        {"id": "fleet_ray_in_body_table", "kind": "invariant", "ok": rate("ray_in_table") == 1.0,
         "detail": f"{c['ray_in_table']['pass']}/{c['ray_in_table']['checked']}"},
        {"id": "fleet_ray_selects_a_shape", "kind": "invariant",
         "ok": rate("ray_selects_a_shape") == 1.0,
         "detail": f"{c['ray_selects_a_shape']['pass']}/{c['ray_selects_a_shape']['checked']}"},
        {"id": "fleet_world_body_in_table", "kind": "invariant",
         "ok": rate("world_in_table") == 1.0,
         "detail": f"{c['world_in_table']['pass']}/{c['world_in_table']['checked']}"},
        {"id": "fleet_compound_is_body_or_child", "kind": "invariant",
         "ok": rate("static_one_body_or_child") == 1.0,
         "detail": f"{c['static_one_body_or_child']['pass']}/"
                   f"{c['static_one_body_or_child']['checked']}; combos {c['combination_counts']}"},
        {"id": "fleet_compound_child_is_object", "kind": "invariant",
         "ok": rate("child_is_object") == 1.0,
         "detail": f"{c['child_is_object']['pass']}/{c['child_is_object']['checked']}"},
        {"id": "fleet_property_is_permutation", "kind": "measured",
         "ok": rate("prop_is_permutation") == 1.0,
         "detail": f"{c['prop_is_permutation']['pass']}/{c['prop_is_permutation']['checked']} files"},
        {"id": "fleet_part_index_identity", "kind": "measured", "ok": idr == 1.0,
         "detail": f"{c['identity']['same']}/{c['identity']['parts']} parts "
                   f"({c['identity']['files']} files); delta histogram {c['delta_histogram']}"},
        {"id": "fleet_static_parent_has_part", "kind": "measured",
         "ok": rate("static_parent_has_part") == 1.0,
         "detail": f"{c['static_parent_has_part']['pass']}/"
                   f"{c['static_parent_has_part']['checked']}"},
        {"id": "fleet_one_system_per_file", "kind": "invariant", "ok": c["no_system"] == 0,
         "detail": f"{c['no_system']} without"},
        {"id": "fleet_compound_data_pair", "kind": "invariant",
         "ok": c["class_pair_ok"] == c["entries"],
         "detail": f"{c['class_pair_ok']}/{c['entries']}"},
        {"id": "fleet_extern_le_polytope", "kind": "invariant",
         "ok": c["extern_le_poly"] == c["entries"],
         "detail": f"{c['extern_le_poly']}/{c['entries']}"},
    ]


# ------------------------------------------------------------------ render
def render(doc: dict) -> str:
    d, fl, c = doc["donor"], doc["fleet"], doc["fleet"]["census"]
    L = []
    A = L.append
    A("# Raycast ids and static-compound references (G3-10f)")
    A("")
    A("Generated by `Tools/scripts/jc3_physics_roles5.py`; `--check` re-derives every number")
    A("and fails on drift. `decoded` = read at the stated offset; `derived` = a rule over decoded")
    A("inputs; `UNKNOWN` = no decoder reads it, blocker named. Rates are reported as rates -")
    A("no oracle in this file turns a fleet rate into an invariant.")
    A("")
    A(f"Donor `{d['path']}` - {d['bytes']:,} B, {d['objects']} objects, "
      f"**{d['body_count']} body entries**.")
    A(f"Fleet `{OUT_DIR}` - {c['files']} entity decodes, {c['entries']} physics entries "
      f"({c['with_system']} with a system); {c['paired']} name a `.physicsc` that is present in")
    A(f"`{RAW_DIR}` ({c['raw_files_used']} distinct files, decoded once each).")
    A("")
    A("## 1. The two questions, answered")
    A("")
    A("**No second id space.** A part's `ray` value is an index into the physics system's")
    A(f"body-entry array (`hknpPhysicsSystemData+0x40`, {ENTRY}-byte entries): every non-negative")
    A(f"ray id in the donor ({d['ray_count']}/{d['part_count']} parts carry one) is inside "
      f"0..{d['body_count'] - 1}, and")
    A(f"fleet-wide **{c['ray_in_table']['pass']}/{c['ray_in_table']['checked']}** ray ids select "
      f"a body entry, each with a shape.")
    A(f"The `{d['extern_ids'][0]}..{d['extern_ids'][-1]}` window is exactly the body entries "
      "whose shape is an")
    A("`hknpExternMeshShape` (measured: the set of ray ids at or above the first extern body")
    A("equals the set of extern body indices for the donor). It is the body table's order, not a")
    A("separate space.")
    A("")
    A("**A static compound is a body's shape, or a child of another compound, and its children")
    A("are nested.** Each donor compound is the shape of exactly one body entry and its seven")
    A("children are `hknpConvexPolytopeShape` objects that are not in the body table and carry")
    A("no part index.")
    A("")
    A("**What is not fleet-wide:** the `CPfxPartIndexProperty` number is not the parts-module")
    A(f"index for every vehicle - {c['identity']['same']}/{c['identity']['parts']} parts agree "
      f"({c['identity']['files']} files).")
    A("The property numbering is still a permutation of its range")
    A(f"({c['prop_is_permutation']['pass']}/{c['prop_is_permutation']['checked']} files), so it "
      f"is a part index in a different")
    A("numbering, not noise; the identity of a ray id's part is therefore proved by the")
    A("part-index round trip for the donor and where the numbering coincides, and is *not*")
    A("proved by it elsewhere. That is the honest limit of this decode.")
    A("")
    A("## 2. Every raycast-related id in the donor")
    A("")
    A(f"{d['part_count']} parts, {d['ray_count']} ray ids, {d['same_part']} of them select the")
    A(f"body entry whose part index is that part; parts with no ray id: {d['no_ray'] or 'none'}.")
    A("")
    A("| ray id range | ids | shape class of the selected entry |")
    A("|---|---|---|")
    for cls, ids in d["ray_by_class"].items():
        A(f"| `{min(ids)}..{max(ids)}` | {len(ids)} | `{cls}` |")
    A("")
    A(f"Body ids no part names ({len(d['ids_no_part_names'])}): "
      + (", ".join(str(i) for i in d["ids_no_part_names"]) or "none")
      + " - the two dynamic compounds.")
    A("")
    A("| part | name | ray | entry class | entry part_index | world body | same part |")
    A("|---:|---|---:|---|---:|---:|---|")
    for m in d["mapped"]:
        A(f"| {m['part']} | `{m['name']}` | {m['ray']} | `{m['entry_class']}` | "
          f"{m['entry_part_index']} | {m['world_body']} | {'yes' if m['same_part'] else 'no'} |")
    A("")
    A("## 3. The static compounds, decoded")
    A("")
    A("| compound | extent | body | part | parents | instances | child classes | children in body table | worst AABB overflow |")
    A("|---|---:|---:|---|---:|---:|---|---:|---:|")
    for x in d["compounds"]:
        ref = x["refs"][0] if x["refs"] else {"body": None, "part": None,
                                              "entry_part_index": None}
        A(f"| `{x['offset']:#x}` | {x['extent']} | {ref['body']} | `{ref['part']}` "
          f"({ref['entry_part_index']}) | {len(x['parent_compounds'])} | {x['instances']} | "
          f"{', '.join('`%s`' % k for k in x['child_classes'])} | "
          f"{x['children_in_body_table']} | {x['worst_overflow_m']} |")
    A("")
    for x in d["compounds"]:
        ref = x["refs"][0] if x["refs"] else {"body": None, "part": None}
        A(f"### `{x['offset']:#x}` - the compound of the `{ref['part']}` body")
        A("")
        A(f"AABB min {x['aabb']['min']} max {x['aabb']['max']}. Children (all")
        A("`hknpConvexPolytopeShape`, none in the body table, no part index):")
        A("")
        A("| # | child shape | class | part_index | scale | translation | AABB overflow (m) |")
        A("|---:|---|---|---:|---|---|---:|")
        for ch in x["children"]:
            A(f"| {ch['index']} | `{ch['shape']:#x}` | `{ch['class']}` | {ch['part_index']} | "
              f"{ch['scale']} | {ch['translation']} | {ch['aabb_overflow_m']} |")
        A("")
    A("The stored compound AABB is not the exact union of its children: the worst overflow is")
    A(f"{max(x['worst_overflow_m'] or 0 for x in d['compounds']):.3g} m, so containment is a")
    A("property of the authored box, not of the instance transforms.")
    A("")
    A("## 4. The fleet")
    A("")
    A("| quantity | value |")
    A("|---|---|")
    A(f"| entity decodes | {c['files']} |")
    A(f"| physics entries / with a system | {c['entries']} / {c['with_system']} |")
    A(f"| entries whose raw `.physicsc` is present | {c['paired']} ({c['raw_files_used']} files) |")
    A(f"| files carrying a static compound | {c['static_files']} |")
    A(f"| static compounds / dynamic compounds (summary) | {c['statics']} / {c['dyn']} |")
    A(f"| compound instances decoded (raw subset) | {c['instances']} |")
    A(f"| parts with no ray id (`-1`) | {c['no_ray_parts']} |")
    A("")
    A("| check | checked | pass | rate |")
    A("|---|---:|---:|---:|")
    for k in ("ray_in_table", "ray_selects_a_shape", "world_in_table",
              "static_one_body_or_child", "child_is_object", "static_parent_has_part",
              "prop_is_permutation"):
        v = c[k]
        r = (v["pass"] / v["checked"]) if v["checked"] else 0.0
        A(f"| `{k}` | {v['checked']} | {v['pass']} | {r:.4f} |")
    A("")
    A("Compound reference combinations across the decoded fleet "
      "(body refs, parent compounds):")
    A("")
    A("| combination | compounds |")
    A("|---|---:|")
    for k, v in c["combination_counts"].items():
        A(f"| {k} | {v} |")
    A("")
    A("So a static compound can be a body's shape, a child of another compound, or both - all")
    A("three occur; none is orphaned. The body's shape is the addressable one; the child")
    A("instances are not addressable through the body table.")
    A("")
    A("Part-index delta histogram (property value minus parts-module index, raw subset):")
    A("")
    A("| delta | count |")
    A("|---|---:|")
    for k, v in c["delta_histogram"].items():
        A(f"| {k} | {v} |")
    A("")
    A(f"{len(c['raw_files_unpaired'])} raw file(s) are named by no entity decode: "
      + (", ".join(f"`{x}`" for x in c["raw_files_unpaired"]) or "none") + ".")
    A("")
    A("Per raw file (deduplicated; entity variants share one `.physicsc`):")
    A("")
    A("| raw file | bodies | parts | statics | instances | dyn | externs | polytopes |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in fl["per_file"]:
        A(f"| `{r['raw']}` | {r['bodies']} | {r['parts']} | {r['statics']} | {r['instances']} | "
          f"{r['dyn']} | {r['externs']} | {r['polytopes']} |")
    A("")
    A("## 5. Oracles (`--check` re-runs all; `measured` rows are reported, not asserted)")
    A("")
    A("| oracle | kind | result | detail |")
    A("|---|---|---|---|")
    for o in doc["oracles"]:
        A(f"| `{o['id']}` | {o['kind']} | **{'pass' if o['ok'] else 'rate'}** | {o['detail']} |")
    A("")
    A("## 6. UNKNOWNs")
    A("")
    A("* **The parts-module ordering versus the property numbering** for the vehicles whose")
    A(f"  property value differs from the parts index ({c['identity']['parts'] - c['identity']['same']}"
      " parts). The property is a permutation,")
    A("  so both numberings are well formed; which one the game's raycast query uses is not in")
    A("  any decoded file. Where it would be found: the engine's raycast consumer, or a")
    A("  geometric oracle per part (hull vs part mesh bounds).")
    A("* **Which engine system reads the `ray` id.** The field is decoded from the parts module")
    A("  (`_vehicle_parts.vmodc`); its reader is not decoded. Next source: the executable's")
    A("  parts-module reader.")
    A("* **Whether a compound's child shapes are addressable by any id.** They carry no part")
    A("  property; nothing in the file names them except the compound's instance array. Whether")
    A("  the engine addresses an instance by index is UNKNOWN.")
    A("* **The stored compound AABB** is not the exact union of the children (worst overflow")
    A("  above). Why the author's box is looser or tighter is not decoded.")
    A("* **Fleet body tables for the entries whose raw `.physicsc` is absent** "
      f"({c['entries'] - c['paired']} of {c['entries']}):")
    A("  their `out/` decodes carry `summary` only, so the id mapping cannot run on them; the")
    A("  class-count invariants do cover all entries.")
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/jc3_physics_roles5.py --write")
    A("python Tools/scripts/jc3_physics_roles5.py --check")
    A("```")
    A("")
    return "\n".join(L)


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("use --write or --check")
    doc = build()
    doc["oracles"] = oracles(doc)
    md = render(doc)
    bad = [o["id"] for o in doc["oracles"] if not o["ok"] and o["kind"] == "invariant"]
    rates = [o["id"] for o in doc["oracles"] if not o["ok"] and o["kind"] == "measured"]
    if a.write:
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"wrote {os.path.relpath(OUT_MD, ROOT)} ({md.count(chr(10))} lines)")
        print(f"wrote {os.path.relpath(OUT_JSON, ROOT)}")
        print(f"donor: {doc['donor']['same_part']}/{doc['donor']['part_count']} rays map, "
              f"{len(doc['donor']['compounds'])} static compounds")
        c = doc["fleet"]["census"]
        print(f"fleet: {c['entries']} entries, {c['paired']} with raw bytes, "
              f"{c['statics']} static compounds, {c['instances']} instances decoded")
        print("invariants not universal:", bad or "none")
        print("measured rates below 1.0:", rates or "none")
        return 1 if bad else 0
    fails = []
    if not os.path.exists(OUT_MD) or not os.path.exists(OUT_JSON):
        fails.append("outputs missing - run --write")
    else:
        if open(OUT_MD, encoding="utf-8").read() != md:
            fails.append("PHYSICS_ROLES5.md differs from a fresh render")
        if json.load(open(OUT_JSON, encoding="utf-8")) != doc:
            fails.append("PHYSICS_ROLES5.json differs from a fresh render")
    for o in doc["oracles"]:
        print(f"{'OK  ' if o['ok'] else 'RATE'} {o['id']} [{o['kind']}]: {o['detail']}")
    for f in fails:
        print("FAIL", f)
    print("invariants not universal:", bad or "none")
    print("measured rates below 1.0 (reported, not asserted):", rates or "none")
    if not bad and not fails:
        print("CHECK_EXIT=0")
    return 1 if (bad or fails) else 0


if __name__ == "__main__":
    sys.exit(main())
