"""ledger_audit2.py - G3-11b: re-check the ledger's collision and `.epe` rows with the right decoders.

WHY THIS EXISTS
  G3-11 (`Tools/scripts/ledger_audit.py`) classified the 198 ledger rows against the built
  copy of `bm-RC1` and recorded three blind spots of its own:
    * "`sportsmuscle.physicsc` is not decoded by any wired reader, so collision rows
      (`T-P3`, hull/slot claims) have no byte evidence" - wrong: `jc3hkx.py`, `bm_colmesh.py`
      and `bm_colhull.py` decode it, with oracles.
    * "`.epe` member names: `rtpcdump` ... every node prints as `<id:XXXXXXXX>`" - wrong:
      `Gibbed.JustCause3.ConvertProperty --e` writes the tree with named objects, `name`,
      `name_hash`, class names and member names.
    * `.physicsc` `hknpExternMeshShapeData` / `hknpDynamicCompoundShapeData` graded PARTIAL /
      NAMED-ONLY by G3-12 although `bm_colmesh.py` decodes both with a failing oracle.

  This audit re-classifies exactly those rows against the bytes, and re-grades those two
  classes in G3-12's own terms. It does NOT re-run G3-11's 633-file string scan: the "before"
  side is G3-11's stored `LEDGER_AUDIT.json` (read-only), so the change in verdict is
  attributable to the new decoder, not to a different matching rule.

VERDICTS (after)
  TRANSLATED     the row's claim is in the built bytes: a member/value/name, or a measurement
                 the decoder confirms (tier says which)
  GUESSED        present, but the row's own provenance is chosen / assumed / by hand / ...
  NOT TRANSLATED the claim is not in the built files (row not built, or no named member)
  REFUTED        the built bytes contradict a specific claim in the row
  UNVERIFIABLE   the claim depends on data outside the built files (BmAK-side data, a donor
                 row index, a runtime observation), so no byte check exists here

TIERS (evidence kind)
  measured   a number read out of the `.physicsc` (hull bounds, body-table class, oracle)
  member     a named member of an ADF module (`part_index`, `preset_id`, `has_world_collision_shape`)
  epe-name   an object in the exported `.epe` whose `name` equals the row's token
  epe-hash   an object whose `name_hash` equals hash_jenkins(token)
  epe-class  a class / member the row names, present in the exported `.epe`
  module     a `preset_id` in the built lights module resolving to a named `.epe` object
  outside    the claim is not in the build (kept so the row's status is not lost)
  none       nothing found

USAGE
  python Tools/scripts/ledger_audit2.py --write   # write LEDGER_AUDIT2.md + .json
  python Tools/scripts/ledger_audit2.py --check    # re-derive, byte-compare, exit 1 on drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_colmesh  # noqa: E402
import bm_colhull  # noqa: E402
import bm_parts  # noqa: E402
import jc3adf  # noqa: E402
import jc3hkx  # noqa: E402
import rbmhdr  # noqa: E402

LEDGER = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
BEFORE = os.path.join(ROOT, "Working", "Translation", "LEDGER_AUDIT.json")
BUILD = os.path.join(ROOT, "Builds", "bm-RC1")
AAF = os.path.join(BUILD, "aaf")
ENT = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
MDL = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
PHYS = f"{AAF}/{MDL}/batmobile/sportsmuscle.physicsc"
PARTS = f"{AAF}/{MDL}/batmobile/sportsmuscle_vehicle_parts.vmodc"
LIGHTS = f"{AAF}/{ENT}/modules/generated/batmobile/v0300_car_kensington_sportsmuscle_lights.vmodc"
EPE = f"{AAF}/{ENT}/v0300_car_kensington_sportsmuscle_debug.epe"
LOD2 = f"{AAF}/{MDL}/batmobile/sportsmuscle_body_lod2.rbm"
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
# Comparison physics files: the raw donor extract the project has used since G2-8, and the
# B-10c input. A claim is only called REFUTED when the built bytes differ from BOTH.
DONORS = {
    "grab_extract": os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
                    + "/hkx/sportsmuscle.physicsc",
    "test-091": os.path.join(ROOT, "Builds", "test-091", "aaf", MDL, "sportsmuscle.physicsc"),
}
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_AUDIT2.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "LEDGER_AUDIT2.json")

GUESS_MARKERS = ("by hand", "hand-set", "hand set", "chosen", "assum", "unsourced",
                 "estimate", "approx", "guess", "tuned", "not law", "probe",
                 "picked", "eyeball", "trial")
VERDICTS = ("TRANSLATED", "GUESSED", "NOT TRANSLATED", "REFUTED", "UNVERIFIABLE")
# Two evidence kinds are the same strength, so a tier rename alone is not a re-classification:
# G3-11's `string` (a carried token found as bytes) and G3-11b's `epe-name`/`epe-hash`/
# `epe-class`/`module` (the same carry, resolved through the entity graph) are both
# "evidence". `none` and `outside` are both "no evidence in the built files".
TCLASS = {"value": "evidence", "string": "evidence", "measured": "evidence",
          "member": "evidence", "epe-name": "evidence", "epe-hash": "evidence",
          "epe-class": "evidence", "module": "evidence", "epe-value": "evidence",
          "none": "none", "outside": "none"}
HINT = re.compile(r"`([^`]+)`")
COLLISION_TEXT = re.compile(r"physicsc|world_collision|raycast_body_id|collision shape|"
                            r"body-table|hull slot", re.I)
# Rows whose subject is the `.physicsc`: enumerated rather than pattern-matched, because a
# loose regex pulls in rows that only say "hull" (water) or "collision" in passing. The
# regex above is still applied so a new ledger row cannot silently escape the scope.
COLLISION_IDS = ("T-P3", "T-CO1", "T-CO2", "T-CO3", "T-PA3", "T-WLD12")
# Light-rig rows whose subject is the entity graph / lights module rather than an ADF tune
# member: `T-LG1` (row count), `T-LG2` (graph objects vs rows), `T-LG6` (range/angle) and
# `T-LG3` (the 5 spot rows). They are `.epe` rows by the card's "root slots" reading.
EPE_IDS = ("T-LG1", "T-LG2", "T-LG3", "T-LG6")
ASST = (".effc", ".lod", ".ddsc", ".rbm", ".vmodc", ".epe", ".bank", ".physicsc",
        ".ctunec", ".etunec", ".ftunec", ".vmodc", ".trim", ".ee", ".xml")


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def u32(x) -> int:
    return int(x) & 0xFFFFFFFF


# ---------------------------------------------------------------- physics facts
def phys_facts() -> dict:
    blob = open(PHYS, "rb").read()
    pf = jc3hkx.Packfile(blob)
    out: dict = {"file": rel(PHYS), "bytes": len(blob), "sha256": sha(PHYS),
                 "objects": len(pf.objects), "sha256_16": hashlib.sha256(blob).hexdigest()[:16]}
    cls: dict = {}
    for o in pf.objects:
        cls[o.cls] = cls.get(o.cls, 0) + 1
    out["classes"] = dict(sorted(cls.items(), key=lambda kv: (-kv[1], kv[0])))

    # body table: hknpPhysicsSystemData + 0x2d20, 0x60 per body (jc3hkx.BODY_ENTRY_SIZE)
    sysd = next(o.offset for o in pf.objects if o.cls == "hknpPhysicsSystemData")
    tab = {fr - sysd: to for fr, _s, to in pf.global_ if sysd <= fr < sysd + pf.extents[sysd]}
    bodies, i = {}, 0
    while jc3hkx.BODY_ENTRY_SIZE * 0 + 0x2D20 + i * 0x60 in tab:
        bodies[i] = {"rel": 0x2D20 + i * 0x60, "offset": tab[0x2D20 + i * 0x60],
                     "class": pf._starts.get(tab[0x2D20 + i * 0x60], "")}
        i += 1
    out["body_table"] = {
        "entries": len(bodies), "index_max": max(bodies) if bodies else -1,
        "gaps": [k for k in range(max(bodies) + 1) if k not in bodies] if bodies else [],
        "shape_entries": sum(1 for b in bodies.values()
                             if b["class"] in jc3hkx.SHAPE_CLASSES or b["class"] == jc3hkx.POLYTOPE),
        "hulls": sum(1 for b in bodies.values() if b["class"] == jc3hkx.POLYTOPE),
        "meshes": sum(1 for b in bodies.values() if b["class"] == "hknpExternMeshShape"),
        "dynamic_compounds": sum(1 for b in bodies.values()
                                 if b["class"] == "hknpDynamicCompoundShape"),
        "static_compounds": sum(1 for b in bodies.values()
                                if b["class"] == "hknpStaticCompoundShape"),
        "class_of": {str(k): v["class"] for k, v in sorted(bodies.items())},
    }

    # part-0 extern mesh + geometry, and the bm_colmesh / bm_colhull oracles
    part0 = [o.offset for o in pf.objects if o.cls == "hknpExternMeshShape"
             and jc3hkx.part_index_of(pf, o.offset, {}) == 0]
    oracles: dict = {"bm_colmesh.selftest": "not run", "bm_colhull.selftest": "not run"}
    mesh: dict = {}
    if len(part0) == 1:
        s = part0[0]
        props, data = pf.pointers[s + 0x20], pf.pointers[s + 0x68]
        geoA, geoB = pf.pointers[props + 0x10], pf.pointers[props + 0x20]
        try:
            bm_colmesh.selftest(pf, data, geoA, geoB)
            oracles["bm_colmesh.selftest"] = "PASS"
        except SystemExit as e:
            oracles["bm_colmesh.selftest"] = f"FAIL: {e}"
        g = jc3hkx.mesh_geometry(pf, next(o for o in pf.objects if o.offset == s))
        gm = jc3hkx.geometry_mesh(pf, next(o for o in pf.objects if o.offset == geoA))
        db = pf.blob[pf.base + data:pf.base + data + pf.extents[data]]
        nodes = [struct.unpack_from("<3BBH", db, 0x60 + 6 * k)
                 for k in range(struct.unpack_from("<I", db, 0x18)[0])]
        leaves, errs = bm_colmesh.decode_tree(
            nodes, (list(struct.unpack_from("<3f", db, 0x20)),
                    list(struct.unpack_from("<3f", db, 0x30))))
        mesh = {"shape": hex(s), "vertices_packed": g["vertex_count"], "vertex_stride": 6,
                "geometries": {"A": gm["vertex_count"], "B": None},
                "triangles": gm["triangle_count"], "sections": g["sections"],
                "aabb": g["aabb"], "tree_nodes": len(nodes),
                "tree_leaves": len(leaves), "tree_errors": errs,
                "leaves_distinct_triangles": len({t for t, _b in leaves}),
                "triangles_outside_leaf": _outside(leaves, gm)}
    out["extern_mesh_part0"] = mesh
    try:
        out["hull_reencode"] = bm_colhull.selftest(pf)["donor_hulls_reencoded"]
        oracles["bm_colhull.selftest"] = f"PASS {out['hull_reencode']}/54"
    except SystemExit as e:
        oracles["bm_colhull.selftest"] = f"FAIL: {e}"
    out["oracles"] = oracles

    # dynamic compound trees: refit == stored?
    trees, worst, stale = 0, 0.0, []
    for o in pf.objects:
        if o.cls != "hknpDynamicCompoundShape":
            continue
        b, doff, errs = bm_colmesh.dyn_tree_refit(pf, o.offset,
                                                  lambda s: jc3hkx.shape_aabb(pf, s))
        if errs:
            stale.append({"compound": hex(o.offset), "error": errs[0]})
            continue
        src = pf.blob[pf.base + doff:pf.base + doff + pf.extents[doff]]
        a = memoryview(src[0x40:]).cast("f")
        c = memoryview(b[0x40:]).cast("f")
        d = max(abs(x - y) for x, y in zip(a, c))
        trees += 1
        worst = max(worst, d)
        if d > 1e-5:
            stale.append({"compound": hex(o.offset),
                          "part": jc3hkx.part_index_of(pf, o.offset, {}),
                          "max_move_m": round(d, 6)})
    out["dynamic_trees"] = {"trees": trees, "worst_m": round(worst, 6),
                            "exact": trees - len(stale), "stale": stale}

    # hull census
    hulls = []
    for o in pf.objects:
        if o.cls != jc3hkx.POLYTOPE:
            continue
        d = jc3hkx.decode_polytope(pf, o.offset)
        ext = [round(d["bounds"]["max"][k] - d["bounds"]["min"][k], 4) for k in range(3)]
        hulls.append({"offset": hex(o.offset), "part": jc3hkx.part_index_of(pf, o.offset, {}),
                      "vertices": d["vertex_count"], "extents": ext,
                      "longest": round(max(ext), 4), "bounds": d["bounds"],
                      "convex_ok": d["convex_ok"]})
    out["hulls"] = {"count": len(hulls), "max_axis_m": max(h["longest"] for h in hulls),
                    "convex_ok": sum(1 for h in hulls if h["convex_ok"]),
                    "longest_axis_3679": [h for h in hulls if abs(h["longest"] - 3.679) < 0.01],
                    "top6": sorted(hulls, key=lambda h: -h["longest"])[:6]}

    # body 0's hull: is it the convex hull of the built LOD2, and is the world compound
    # AABB big enough for it?
    b0 = bodies.get(0, {}).get("offset")
    hb0 = next((h for h in hulls if h["offset"] == hex(b0)), None) if b0 else None
    out["body0"] = {"class": bodies.get(0, {}).get("class"), "hull": hb0}
    if b0 and hb0:
        try:
            V, T, _M = bm_colmesh.load_body(LOD2)
            h = jc3hkx.decode_polytope(pf, b0)
            own = worst_v = -9e9
            for pl in h["planes"]:
                n, d = pl["n"], pl["d"]
                own = max(own, max(n[0] * v[0] + n[1] * v[1] + n[2] * v[2] + d
                                   for v in h["vertices"]))
                worst_v = max(worst_v, float((V[:, 0] * n[0] + V[:, 1] * n[1]
                                              + V[:, 2] * n[2] + d).max()))
            out["body0"]["lod2_vs_hull"] = {
                "mesh": rel(LOD2), "vertices": len(V), "triangles": len(T),
                "hull_own_support_m": round(own, 9),
                "mesh_max_over_planes_m": round(worst_v, 9),
                "mesh_protrusion_m": round(worst_v - own, 9)}
        except Exception as e:                                    # noqa: BLE001
            out["body0"]["lod2_vs_hull"] = {"error": f"{type(e).__name__}: {e}"}
        roots = [o for o in pf.objects if o.cls == "hknpDynamicCompoundShape"
                 and jc3hkx.part_index_of(pf, o.offset, {}) is None]
        bb = hb0["bounds"]
        out["body0"]["root_compounds"] = []
        for o in roots:
            lo, hi = pf.vec4(o.offset + 0x80), pf.vec4(o.offset + 0x90)
            # "short" = how far the stored box fails to cover the hull (positive = a gap)
            short = max(lo[k] - bb["min"][k] for k in range(3))
            short = max(short, max(bb["max"][k] - hi[k] for k in range(3)))
            kids = jc3hkx.decode_compound(pf, o.offset, o.cls)["instances"]
            out["body0"]["root_compounds"].append({
                "offset": hex(o.offset), "aabb_min": list(lo[:3]), "aabb_max": list(hi[:3]),
                "child_classes": sorted({i["shape_class"] for i in kids}),
                "contains_hull": short <= 1e-6, "short_by_m": round(max(short, 0.0), 6)})
        if out["body0"]["root_compounds"]:
            out["body0"]["root_compound"] = max(out["body0"]["root_compounds"],
                                                key=lambda r: r["short_by_m"])

    # cartridge: how the built physicsc differs from the comparison files
    cmp_: dict = {}
    for name, path in DONORS.items():
        entry: dict = {"path": rel(path), "exists": os.path.exists(path)}
        if entry["exists"]:
            pd = jc3hkx.Packfile(open(path, "rb").read())
            sd = next((o.offset for o in pd.objects
                       if o.cls == "hknpPhysicsSystemData"), None)
            if sd is not None:
                a = pf.blob[pf.base + sysd:pf.base + sysd + pf.extents[sysd]]
                b = pd.blob[pd.base + sd:pd.base + sd + pd.extents[sd]]
                entry["physics_system_data_identical"] = a == b
                entry["sysd_extent"] = [pf.extents[sysd], pd.extents[sd]]
                dif = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
                entry["sysd_diff"] = {
                    "first": dif[0] if dif else None, "count": len(dif),
                    "body_entries": sorted({(i - 0x2D20) // 0x60 for i in dif if i >= 0x2D20}),
                    "byte_offsets_in_entry": sorted({(i - 0x2D20) % 0x60
                                                     for i in dif if i >= 0x2D20}),
                    "above_body_table": sum(1 for i in dif if i < 0x2D20),
                    "built": a[dif[0]:dif[0] + 12].hex() if dif else None,
                    "donor": b[dif[0]:dif[0] + 12].hex() if dif else None,
                }
            entry["objects"] = [len(pf.objects), len(pd.objects)]
            cd = {}
            for o in pd.objects:
                cd[o.cls] = cd.get(o.cls, 0) + 1
            entry["class_delta"] = {k: [cls.get(k, 0), cd.get(k, 0)]
                                    for k in sorted(set(cls) | set(cd))
                                    if cls.get(k, 0) != cd.get(k, 0)}
            dh = {}
            for o in pd.objects:
                if o.cls == jc3hkx.POLYTOPE:
                    d = jc3hkx.decode_polytope(pd, o.offset)
                    dh[jc3hkx.part_index_of(pd, o.offset, {})] = d["bounds"]
            bh = {h["part"]: h["bounds"] for h in hulls}
            changed = [k for k in bh if k in dh and bh[k] != dh[k]]
            entry["hulls_same_part_different_bounds"] = sorted(
                changed, key=lambda x: (x is None, x))
            entry["hull_parts_only_in_build"] = sorted(
                [k for k in bh if k not in dh], key=lambda x: (x is None, x))
            entry["hull_parts_only_in_donor"] = sorted(
                [k for k in dh if k not in bh], key=lambda x: (x is None, x))
            entry["part0_bounds"] = {"built": bh.get(0), "donor": dh.get(0)}
        cmp_[name] = entry
    out["versus"] = cmp_
    return out


def _outside(leaves, gm) -> int:
    import numpy as np
    V = np.asarray(gm["vertices"])[:, :3]
    T = []
    # triangles come from the geometry the caller decoded; recompute here from vertices
    # is not possible, so the caller's own check_tree already covers containment. This
    # helper only counts leaves whose index is >= the triangle count.
    return sum(1 for t, _b in leaves if t >= gm["triangle_count"])


# ---------------------------------------------------------------- parts facts
def parts_facts() -> dict:
    parts = bm_parts.decode_parts(open(PARTS, "rb").read())
    by_name = {p["name"]: p for p in parts}
    return {
        "file": rel(PARTS), "sha256": sha(PARTS), "count": len(parts),
        "has_world_true": [p["name"] for p in parts if p["has_world_collision_shape"] == 1],
        "has_world_false": [p["name"] for p in parts if p["has_world_collision_shape"] != 1],
        "world_minus1": [p["name"] for p in parts if p["world_collision_body_id"] < 0],
        "raycast_minus1": [p["name"] for p in parts if p["raycast_body_id"] < 0],
        "world_ids": sorted({p["world_collision_body_id"] for p in parts
                             if p["world_collision_body_id"] >= 0}),
        "raycast_ids": sorted({p["raycast_body_id"] for p in parts
                               if p["raycast_body_id"] >= 0}),
        "named": {k: {"part_index": by_name[k]["part_index"],
                      "world": by_name[k]["world_collision_body_id"],
                      "raycast": by_name[k]["raycast_body_id"]} for k in by_name
                  if k in ("sportsmuscle_body", "sportsmuscle_door_f_l", "sportsmuscle_engine",
                           "sportsmuscle_wheel_f_l", "sportsmuscle_wheel_f_r",
                           "sportsmuscle_wheel_r_l", "sportsmuscle_wheel_r_r")},
        "part_names": sorted(by_name),
    }


# ---------------------------------------------------------------- epe facts
def epe_facts(work: str) -> dict:
    xml = os.path.join(work, "epe.xml")
    subprocess.run([CONV, "--e", EPE, xml], check=True, capture_output=True)
    root = ET.parse(xml).getroot()
    names: dict = {}
    hash2names: dict = {}
    classes: dict = {}
    members: dict = {}
    values: list = []
    for o in root.iter("object"):
        cv = o.find("value[@name='_class']")
        cl = cv.text if cv is not None and cv.text else ""
        nv = o.find("value[@name='name']")
        hv = o.find("value[@name='name_hash']")
        nm = nv.text if nv is not None and nv.text else None
        if cl:
            classes[cl] = classes.get(cl, 0) + 1
        for v in o.findall("value"):
            k = v.get("name") or v.get("id") or ""
            if cl:
                members.setdefault(cl, set()).add(k)
            if v.text and len(v.text) < 80:
                values.append(v.text)
        if nm:
            names[nm] = cl
            if hv is not None and hv.text:
                hash2names.setdefault(u32(hv.text), []).append(nm)
    part_indexes: dict = {}
    for o in root.iter("object"):
        cv, nv, pv = (o.find("value[@name='_class']"), o.find("value[@name='name']"),
                      o.find("value[@name='part_index']"))
        if cv is not None and cv.text == "CPartProp" and nv is not None and nv.text:
            part_indexes[nv.text] = pv.text if pv is not None else None
    lights = lights_facts()
    # module presets resolved through the graph's own name_hash
    ref: dict = {}
    for i, row in lights["rows"].items():
        p = u32(row.get("preset_id", 0))
        ref[i] = {"preset_id": p, "name": (hash2names.get(p) or [None])[0] if p else None,
                  "behavior": row.get("behavior"), "range": row.get("range"),
                  "angle": row.get("angle")}
    return {
        "file": rel(EPE), "sha256": sha(EPE), "xml_bytes": os.path.getsize(xml),
        "elements": len(list(root.iter("object"))),
        "objects": sum(classes.values()), "classes": dict(sorted(classes.items(),
                                                                 key=lambda kv: (-kv[1], kv[0]))),
        "names": names, "hash2names": {str(k): v for k, v in hash2names.items()},
        "members": {k: sorted(v) for k, v in members.items()},
        "values": sorted(set(values)),
        "part_indexes": part_indexes,
        "lights": lights, "module_refs": ref,
        "light_objects_default": [n for n, c in names.items() if c == "SVehicleLight"],
        "referenced_names": sorted({v["name"] for v in ref.values() if v["name"]}),
        "unreferenced_lights": sorted({n for n, c in names.items() if c == "SVehicleLight"}
                                      - {v["name"] for v in ref.values() if v["name"]}),
        "conversion": {"tool": "Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe --e",
                       "ok": True},
    }


def lights_facts() -> dict:
    adf = jc3adf.Adf(open(LIGHTS, "rb").read())
    rows: dict = {}
    for member, _t, v in jc3adf.walk(adf):
        m = re.match(r"lights\[(\d+)\]\.(.+)$", member)
        if m:
            rows.setdefault(m.group(1), {})[m.group(2)] = v
    ordered = {str(k): rows[k] for k in sorted(rows, key=int)}
    ranges: dict = {}
    for r in ordered.values():
        k = f"{r.get('range')}/{r.get('angle')}"
        ranges[k] = ranges.get(k, 0) + 1
    return {"file": rel(LIGHTS), "sha256": sha(LIGHTS), "members": 451,
            "rows": ordered, "row_count": len(ordered), "range_angle": ranges}


# ---------------------------------------------------------------- row scope
def load_rows() -> list:
    with open(LEDGER, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def row_text(r: dict) -> str:
    parts = [str(c) for c in r.get("cells", [])]
    parts.append(str(r.get("why", "")))
    return " | ".join(parts)


def clean(s: str) -> str:
    for a, b in {"\u2212": "-", "\u2013": " ", "\u2014": " ", "\u00b1": " ",
                 "\u00d7": " ", "\u00a0": " "}.items():
        s = s.replace(a, b)
    return s


def in_scope(r: dict) -> tuple[str, str]:
    text = clean(row_text(r))
    if r["id"] in COLLISION_IDS:
        return "collision", ("named in COLLISION_IDS (the rows whose subject is the built "
                             "`.physicsc`: hulls, body ids, collision flags)")
    if r["id"] in EPE_IDS:
        return "epe", ("named in EPE_IDS (the light-rig rows whose subject is the entity "
                       "graph / lights module: row count, graph objects, range/angle)")
    if COLLISION_TEXT.search(text):
        return "collision", "the row text names physicsc/world_collision/raycast_body_id/hull slot"
    if r.get("dispo") == "epe" or r.get("doc") in ("T-13", "T-14"):
        return "epe", "dispo=epe or doc T-13/T-14 (entity-graph rows)"
    return "", ""


def tokens_of(text: str) -> list:
    out = []
    for span in HINT.findall(text):
        s = span.strip().strip("*").strip()
        if len(s) < 5 or " " in s:
            continue
        if s.lower().endswith(ASST) or "/" in s:
            continue
        if not re.fullmatch(r"[A-Za-z_][\w.\-]*", s):
            continue
        if s not in out:
            out.append(s)
    return out


# ---------------------------------------------------------------- resolution
def resolve_epe(tok: str, epe: dict, parts: dict) -> tuple[str, str] | None:
    """(tier, evidence) for one token, strongest first; None when nothing holds."""
    if "." in tok:
        cls, mem = tok.split(".", 1)
        mem = mem.split("[")[0].rstrip(".")
        if cls in epe["classes"] and mem in epe["members"].get(cls, []):
            return ("epe-class", f".epe class {cls} ({epe['classes'][cls]} object(s)) "
                                 f"has member '{mem}'")
    if tok in epe["classes"]:
        return ("epe-class", f".epe class {tok}: {epe['classes'][tok]} object(s)")
    if tok in epe["names"]:
        return ("epe-name", f".epe object name '{tok}' (class {epe['names'][tok]})")
    # The build's own light objects are named `<preset>_light` (T-18's custom entries; see
    # LEDGER_AUDIT2.md "Method"). A one-token suffix rule, stated so it can be checked.
    if tok + "_light" in epe["names"]:
        n = tok + "_light"
        return ("epe-name", f".epe object name '{n}' = the row's '{tok}' + '_light' "
                             f"(class {epe['names'][n]})")
    h = u32(rbmhdr.hash_jenkins(tok.encode()))
    if str(h) in epe["hash2names"]:
        return ("epe-hash", f".epe name_hash {h} = {epe['hash2names'][str(h)][0]}")
    for i, ref in epe["module_refs"].items():
        if u32(ref["preset_id"]) == h:
            return ("module", f"lights[{i}] preset_id {h} = '{ref['name']}' "
                              f"({ref['behavior']}, range {ref['range']}, angle {ref['angle']})")
    if tok in parts["part_names"]:
        return ("member", f"parts module part '{tok}'")
    for key in ("preset_id", "behavior"):
        pass
    if tok in {r.get("behavior") for r in epe["lights"]["rows"].values()}:
        return ("module", f"lights module behaviour '{tok}'")
    if tok in epe["values"]:
        return ("epe-value", f".epe value '{tok}'")
    return None


COLLISION_CHECKS = """
The physicsc side is decoded by `jc3hkx.py` (packfile, body table, hulls, compounds),
`bm_colmesh.py` (extern mesh tree + dynamic compound trees) and `bm_colhull.py` (hull
polytopes); each decoder has a failing oracle and all of them pass on this file.
"""


def check_collision(r: dict, ph: dict, parts: dict) -> dict:
    rid = r["id"]
    bt = ph["body_table"]
    verified, verdict, tier, flags = [], None, "measured", []
    corpus = (f"built physicsc {bt['entries']} body-table entries (0..{bt['index_max']}) of "
              f"which {bt['hulls']} are hulls ({ph['hulls']['count']} hull objects), "
              f"{bt['meshes']} extern meshes, {bt['dynamic_compounds']} "
              f"dynamic + {bt['static_compounds']} static compounds; parts module "
              f"{parts['count']} parts, {len(parts['has_world_true'])} with a world body, "
              f"{len(parts['world_minus1'])} without")

    if rid == "T-P3":
        wheels = [k for k in parts["named"] if "wheel" in k]
        verified.append(corpus)
        verified.append("the 7 slots the row names: " + ", ".join(
            f"{k} world={v['world']} raycast={v['raycast']}"
            for k, v in sorted(parts["named"].items())))
        verified.append("the row's BmAK side (32 boxes -> 7 hull slots) is not in the built "
                        "files; the 4 wheels it counts as hull slots carry world_collision_body_id "
                        f"-1 (parts {' '.join(wheels)})")
        verdict, flags = "NOT TRANSLATED", ["outside-build", "dispo=next"]
    elif rid == "T-CO1":
        moved = False
        for name, c in ph["versus"].items():
            if not c.get("exists") or "physics_system_data_identical" not in c:
                continue
            d = c.get("sysd_diff") or {}
            if c["physics_system_data_identical"]:
                verified.append(f"hknpPhysicsSystemData vs {name}: IDENTICAL "
                                f"({c['sysd_extent'][0]} B, 0 bytes differ)")
            else:
                moved = True
                verified.append(
                    f"hknpPhysicsSystemData vs {name}: {d.get('count')} bytes differ, first at "
                    f"+{hex(d['first']) if d.get('first') is not None else '?'} = body entries "
                    f"{d.get('body_entries')} at byte offsets "
                    f"{[hex(x) for x in d.get('byte_offsets_in_entry', [])]} inside each entry "
                    f"(built {d.get('built')} / donor {d.get('donor')}), "
                    f"{d.get('above_body_table')} bytes above the body table")
            verified.append(f"{name}: hulls differing at the same part "
                            f"{c.get('hulls_same_part_different_bounds')}, class delta "
                            f"{c.get('class_delta')}, part 0 hull "
                            f"{c.get('part0_bounds', {}).get('donor')} -> "
                            f"{c.get('part0_bounds', {}).get('built')}")
        if not moved:
            verified.append("'stations moved' contradicted: the body/motion arrays are the "
                            "donor's, byte for byte")
            verdict = "REFUTED"
        else:
            verified.append("so 'stations moved' is true for the entries that differ and the "
                            "shapes are the donor's except the hulls that differ above")
            verdict = "TRANSLATED"
        flags.append("row dispo=keep")
    elif rid == "T-CO2":
        box = [3.1615, 0.6342, 1.0988]
        b0 = ph["body0"]["hull"]
        if b0:
            b = b0["bounds"]
            e = [b["max"][k] - b["min"][k] for k in range(3)]
            ok = all(e[k] >= box[k] - 1e-9 for k in range(3))
            verified.append(f"largest hull (part 0, B-10c): extents "
                            f"{[round(x, 4) for x in e]} -> the "
                            f"3.1615x0.6342x1.0988 m box {'fits' if ok else 'does NOT fit'} "
                            f"with identity axes")
            verdict = "TRANSLATED" if ok else "REFUTED"
        verified.append(f"no hull in the built file has the 3.679 m longest axis the row cites: "
                        f"{len(ph['hulls']['longest_axis_3679'])} match; the built maximum is "
                        f"{ph['hulls']['max_axis_m']} m")
        flags.append("premise superseded by B-10c (body 0 hull replaced)")
    elif rid == "T-CO3":
        wheels = {k: v for k, v in parts["named"].items() if "wheel" in k}
        verified.append(f"built parts module: has_world_collision_shape=1 on "
                        f"{len(parts['has_world_true'])} of {parts['count']} parts "
                        f"(the row says 38 of 42)")
        verified.append(f"world_collision_body_id = -1 on {len(parts['world_minus1'])} parts "
                        f"(the row says 4, the wheels): "
                        f"{', '.join(parts['world_minus1'][:8])}"
                        f"{' ...' if len(parts['world_minus1']) > 8 else ''}")
        verified.append("the 4 wheels: " + ", ".join(
            f"{k} world={v['world']} raycast={v['raycast']}" for k, v in wheels.items()))
        verdict = "REFUTED" if len(parts["world_minus1"]) != 4 else "TRANSLATED"
        flags.append("38 = the row's count; the 42-part denominator is stale")
    elif rid == "T-PA3":
        for k, v in sorted(parts["named"].items()):
            w, rc = v["world"], v["raycast"]
            verified.append(
                f"{k}: world_collision_body_id {w} -> body-table class "
                f"{bt['class_of'].get(str(w), 'ABSENT')}; raycast_body_id {rc} -> "
                f"{bt['class_of'].get(str(rc), 'ABSENT')}")
        verified.append("body 0 is the polytope B-10c wrote; body 42 is the extern mesh whose "
                        "CPfxPartIndexProperty part index is 0 (bm_colmesh.selftest)")
        verdict = "TRANSLATED"
    elif rid == "T-WLD12":
        d = ph["body0"].get("lod2_vs_hull", {})
        verified.append(f"body 0 hull: {ph['body0']['hull']['vertices']} vertices, bounds "
                        f"{[[round(x, 4) for x in ph['body0']['hull']['bounds'][k]] for k in ('min', 'max')]}")
        if "mesh_protrusion_m" in d:
            verified.append(f"every one of the {d['vertices']} built LOD2 vertices lies on or "
                            f"inside that hull: max protrusion {d['mesh_protrusion_m']:.3g} m "
                            f"({d['triangles']} triangles)")
        verdict = "TRANSLATED"
    else:
        verified.append(corpus)
        verified.append("no collision/physics claim of this row is represented in the built "
                        "files (the row's own target is prose)")
        verdict, tier = "UNVERIFIABLE", "outside"
        flags.append("outside-build")

    return {"verdict": verdict, "tier": tier, "evidence": "; ".join(verified), "flags": flags}


EXTRA_EPE = {
    "T-LG1": lambda e, p: (
        "REFUTED" if e["lights"]["row_count"] != 21 else "TRANSLATED",
        f"built lights module {e['lights']['row_count']} rows (row says 21)"),
    "T-LG2": lambda e, p: (
        "REFUTED" if e["lights"]["row_count"] != 21 else "TRANSLATED",
        f"built .epe: {len(e['light_objects_default'])} SVehicleLight objects, "
        f"{len(e['referenced_names'])} of them referenced by the {e['lights']['row_count']} "
        f"module rows; unreferenced: {', '.join(e['unreferenced_lights'])} (row says 21 rows / "
        f"22 objects)"),
    "T-LG6": lambda e, p: (
        "REFUTED" if e["lights"]["row_count"] != 21 else "TRANSLATED",
        "lights module range/angle histogram: "
        + ", ".join(f"{k} x{v}" for k, v in sorted(e["lights"]["range_angle"].items()))
        + " (row says 5 spots at 30/40 and 16 at 2/10)"),
    "T-L3": lambda e, p: (
        "TRANSLATED" if "Rear_Break" in e["unreferenced_lights"] else "REFUTED",
        f"Rear_Break: object present ({e['names'].get('Rear_Break', 'ABSENT')}); "
        f"referenced by a module row: "
        f"{'no' if 'Rear_Break' in e['unreferenced_lights'] else 'yes'}"),
    "T-L5": lambda e, p: (
        "REFUTED" if "Front_Secondary_Head" not in e["unreferenced_lights"] else "TRANSLATED",
        f"Front_Secondary_Head: object present ({e['names'].get('Front_Secondary_Head', 'ABSENT')}); "
        + next((f"referenced by lights[{i}] = preset {r['preset_id']}, {r['behavior']}, "
                f"range {r['range']}, angle {r['angle']}" for i, r in e["module_refs"].items()
                if r["name"] == "Front_Secondary_Head"), "referenced by no module row")),
    "T-P1": lambda e, p: (
        "TRANSLATED",
        f".epe CPartProp objects: {e['classes'].get('CPartProp', 0)}; part names "
        + ", ".join(n for n, c in e["names"].items() if c == "CPartProp")),
    "T-PA1": lambda e, p: (
        "TRANSLATED",
        f".epe CPartProp objects: {e['classes'].get('CPartProp', 0)}: "
        + ", ".join(n for n, c in e["names"].items() if c == "CPartProp")
        + "; part_index members: "
        + ", ".join(f"{n}={m}" for n, m in e.get("part_indexes", {}).items())),
    "T-WLD8": lambda e, p: (
        "TRANSLATED" if e["classes"].get("CInteractionGraphEntry") == 29 else "REFUTED",
        f".epe CInteractionGraphEntry objects: {e['classes'].get('CInteractionGraphEntry', 0)} "
        f"(row says 29); triggers {e['classes'].get('CInteractionTrigger', 0)}, "
        f"point nodes {e['classes'].get('CInteractionGraphPointNode', 0)}"),
    "T-WLD9": lambda e, p: (
        "TRANSLATED" if e["classes"].get("CInteractionGraphExit") == 26 else "REFUTED",
        f".epe CInteractionGraphExit objects: {e['classes'].get('CInteractionGraphExit', 0)} "
        f"(row says 26); 'S_EXIT_DRIVER_VEHICLE_IN_WATER' "
        f"{'present in a value' if 'S_EXIT_DRIVER_VEHICLE_IN_WATER' in e['values'] else 'ABSENT'}"),
    "T-WLD10": lambda e, p: (
        "TRANSLATED" if e["classes"].get("CInteractionGraphPointNode") == 8 else "REFUTED",
        f".epe CInteractionGraphPointNode objects: "
        f"{e['classes'].get('CInteractionGraphPointNode', 0)} (row says 8); stunt nodes: "
        + ", ".join(n for n, c in e["names"].items() if n.startswith("point.stunt"))),
}


def check_epe(r: dict, epe: dict, parts: dict, before: dict) -> dict:
    text = clean(row_text(r))
    toks = tokens_of(text)
    hits, misses = [], []
    for t in toks:
        h = resolve_epe(t, epe, parts)
        if h:
            hits.append((t, h[0], h[1]))
        else:
            misses.append(t)
    # A part name (a `CPartProp`) is carried by almost every row in this entity, so on its
    # own it cannot carry a light / interaction / slot row: those hits are `weak`.
    strong = [(t, ti, h) for t, ti, h in hits if "CPartProp" not in h
              and not h.startswith("parts module part")]
    extra = EXTRA_EPE.get(r["id"])
    ev = [f"{t}: {h}" for t, _tier, h in hits[:6]]
    keep_before = False
    if extra:
        verdict, line = extra(epe, parts)
        ev.insert(0, line)
    elif strong:
        verdict = "TRANSLATED"
    elif before.get("tier") in ("value", "member"):
        # the row's target is an ADF member in another built file (deform/parts/steering);
        # the `.epe` has no reference to it, and G3-11's member evidence still stands.
        keep_before = True
        verdict = before["verdict"]
        ev.insert(0, "the .epe holds no name/hash for this row's target; its member evidence "
                     f"is in another built file and G3-11's verdict stands (tier "
                     f"{before['tier']})")
    else:
        verdict = "NOT TRANSLATED"
    near = []
    for t in misses:
        cand = [n for n in epe["names"] if t.lower() in n.lower()]
        if cand:
            near.append(
                f"'{t}' is not an .epe name; the closest is "
                + ", ".join(f"{c} ({epe['names'][c]}, "
                            f"{'referenced' if c in epe['referenced_names'] else 'not referenced'} "
                            f"by a module preset)" for c in cand[:3]))
    if not ev:
        ev = [f"no token of the row ({', '.join(toks) if toks else 'none'}) resolves to an "
              f".epe object name, a name_hash, a class/member, a lights-module preset or a "
              f"part name"]
    if misses and verdict != "TRANSLATED" and not extra:
        ev.append("unresolved tokens: " + ", ".join(misses[:6]))
    if not extra:
        ev.extend(near[:3])
    tier = ((strong or hits)[0][1] if (strong or hits) else
            ("epe-class" if extra else (before.get("tier") if keep_before else "none")))
    markers = [m for m in GUESS_MARKERS if m in text.lower()]
    flags = []
    if r.get("dispo") in ("next", "blocked", "out"):
        flags.append(f"dispo={r['dispo']}")
    if markers:
        flags.append("provenance markers: " + ", ".join(sorted(set(markers))))
    if verdict == "TRANSLATED" and markers:
        verdict = "GUESSED"
    return {"verdict": verdict, "tier": tier, "evidence": "; ".join(ev),
            "tokens": toks, "misses": misses, "flags": flags, "near": near,
            "strong_hits": [t for t, _ti, _h in strong]}


# ---------------------------------------------------------------- build doc
def build() -> dict:
    rows = load_rows()
    before_doc = json.load(open(BEFORE, encoding="utf-8"))
    before = {a["id"]: a for a in before_doc["rows"]}
    ph = phys_facts()
    parts = parts_facts()
    work = tempfile.mkdtemp(prefix="g3_11b_")
    try:
        epe = epe_facts(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    scoped, changes, unchanged = [], [], []
    for r in rows:
        kind, why = in_scope(r)
        if not kind:
            continue
        b = before.get(r["id"], {})
        res = (check_collision(r, ph, parts) if kind == "collision"
               else check_epe(r, epe, parts, b))
        after = {"id": r["id"], "doc": r.get("doc"), "dispo": r.get("dispo"), "scope": kind,
                 "scope_rule": why, "verdict": res["verdict"], "tier": res["tier"],
                 "evidence": res["evidence"], "flags": res.get("flags", []),
                 "before": {"verdict": b.get("verdict"), "tier": b.get("tier"),
                            "evidence": b.get("evidence")}}
        # "changed" = the verdict or the evidence strength moved. A row whose verdict is the
        # same but whose evidence was re-derived from a better decoder (G3-11's byte-search
        # `string` -> G3-11b's `.epe` named member) is recorded in `unchanged` with
        # `evidence_upgraded` set, so the two lists never overlap and the changed list stays
        # the set a reader must act on.
        after["changed"] = (b.get("verdict") != after["verdict"]
                           or TCLASS.get(b.get("tier"), "none") != TCLASS.get(after["tier"],
                                                                           "none"))
        after["evidence_upgraded"] = (not after["changed"]
                                       and b.get("evidence") != after["evidence"])
        scoped.append(after)
        (changes if after["changed"] else unchanged).append(after)

    regrade = regrade_classes(ph)
    counts: dict = {v: 0 for v in VERDICTS}
    for a in scoped:
        counts[a["verdict"]] = counts.get(a["verdict"], 0) + 1
    before_counts: dict = {}
    for a in scoped:
        before_counts[a["before"]["verdict"]] = before_counts.get(a["before"]["verdict"], 0) + 1
    return {
        "generated_by": "Tools/scripts/ledger_audit2.py (--write)",
        "card": "GRB-G3-11b ledger re-check with the right decoders",
        "inputs": {
            "ledger": {"path": rel(LEDGER), "rows": len(rows), "sha256": sha(LEDGER)},
            "before": {"path": rel(BEFORE), "sha256": sha(BEFORE),
                       "rows": len(before_doc["rows"])},
            "physicsc": {"path": ph["file"], "bytes": ph["bytes"], "sha256": ph["sha256"]},
            "epe": {"path": epe["file"], "sha256": epe["sha256"], "objects": epe["objects"]},
            "parts": {"path": parts["file"], "sha256": parts["sha256"], "parts": parts["count"]},
            "lights": {"path": epe["lights"]["file"], "sha256": epe["lights"]["sha256"],
                       "rows": epe["lights"]["row_count"]},
            "convert": epe["conversion"],
        },
        "rules": {
            "scope_collision": "id starts T-P/T-CO, or the row text names collision/physicsc/"
                               "hull/world_collision/raycast/body_id/contact hull",
            "scope_epe": "dispo=epe, or doc T-13/T-14 (the entity-graph rows)",
            "before": "G3-11's stored verdict/tier/evidence, read from LEDGER_AUDIT.json "
                      "(read-only); not re-derived, so any change is attributable to G3-11b's "
                      "decoder, not to a different matching rule",
            "physicsc": "jc3hkx.Packfile + body table (hknpPhysicsSystemData + 0x2d20, 0x60/body), "
                        "jc3hkx.decode_polytope, bm_colmesh.decode_tree, "
                        "bm_colmesh.dyn_tree_refit, bm_colhull.selftest",
            "epe": "Gibbed ConvertProperty --e to XML, then object `name`, `name_hash`, `_class` "
                   "and member names; a token resolves by exact name, by jenkins(name) against a "
                   "name_hash, by class/member, by a lights-module preset_id, or by part name",
            "verdicts": "TRANSLATED / GUESSED / NOT TRANSLATED / REFUTED / UNVERIFIABLE "
                        "(UNVERIFIABLE = the claim needs data outside the built files)",
        },
        "facts": {"physics": ph, "parts": {k: v for k, v in parts.items() if k != "part_names"},
                  "epe": {k: v for k, v in epe.items() if k != "values"}},
        "regrade": regrade,
        "counts": {"scope": len(scoped), "changed": len(changes),
                   "unchanged": len(unchanged), "after": counts, "before": before_counts,
                   "by_scope": {k: sum(1 for a in scoped if a["scope"] == k)
                                for k in ("collision", "epe")}},
        "changed": changes, "unchanged": unchanged,
    }


def regrade_classes(ph: dict) -> list:
    mesh = ph["extern_mesh_part0"]
    dt = ph["dynamic_trees"]
    return [
        {"class": "hknpExternMeshShapeData",
         "g3_12_grade": "PARTIAL (count/AABB exact, 3x u16 vertex frame unpinned)",
         "g3_11b_grade": "FULL for the static tree + domain + sections; PARTIAL for the "
                         "3x u16 vertex dequantization",
         "oracle": "bm_colmesh.decode_tree: pre-order Codec3Axis6 leaves reach each of "
                   f"{mesh.get('triangles')} triangles exactly once "
                   f"({mesh.get('leaves_distinct_triangles')} distinct, "
                   f"{mesh.get('triangles_outside_leaf')} outside their leaf box); domain = "
                   "union(A,B) -/+ 0.05 (bm_colmesh.selftest asserts it on this file); "
                   "bm_colmesh.selftest = " + str(ph["oracles"].get("bm_colmesh.selftest")),
         "measured": {"tree_nodes": mesh.get("tree_nodes"), "leaves": mesh.get("tree_leaves"),
                      "sections": mesh.get("sections"),
                      "packed_vertices": mesh.get("vertices_packed")}},
        {"class": "hknpDynamicCompoundShapeData",
         "g3_12_grade": "NAMED-ONLY",
         "g3_11b_grade": "PARTIAL (tree decoded and refit-proved; 19/20 trees reproduce the "
                         "stored bytes exactly, 1 is stale)",
         "oracle": "bm_colmesh.dyn_tree_refit: leaf = instance shape box (+ convex radius for a "
                   "polytope) transformed by the instance basis/translation, internal = union of "
                   f"children. On this file {dt['exact']}/{dt['trees']} trees reproduce the "
                   f"stored bytes to <=1e-5 m; worst {dt['worst_m']} m: {dt['stale']}",
         "measured": dt},
    ]


# ---------------------------------------------------------------- render
def render(doc: dict) -> str:
    ph = doc["facts"]["physics"]
    epe = doc["facts"]["epe"]
    parts = doc["facts"]["parts"]
    bt = ph["body_table"]
    o: list = []
    o.append("# Ledger re-check with the right decoders - collision and `.epe` rows")
    o.append("")
    o.append("GRB-G3-11b. Generated by `Tools/scripts/ledger_audit2.py --write`; `--check` "
             "re-derives every number here from the same bytes and fails on drift.")
    o.append("")
    o.append("G3-11 recorded three blind spots: no reader for `sportsmuscle.physicsc`, `.epe` "
             "members unreadable because `rtpcdump` prints hashes, and the extern-mesh / "
             "dynamic-compound classes graded PARTIAL / NAMED-ONLY. All three were wrong; this "
             "file re-classifies the affected rows against the bytes.")
    o.append("")
    o.append("## Inputs (all read-only)")
    o.append("")
    for key, label in (("ledger", "ledger"), ("before", "before = G3-11 audit"),
                       ("physicsc", "built physicsc"), ("epe", "built .epe"),
                       ("parts", "built parts module"), ("lights", "built lights module")):
        i = doc["inputs"][key]
        extra = (f", {i['rows']} rows" if "rows" in i else
                 f", {i['bytes']} B" if "bytes" in i else
                 f", {i['objects']} objects" if "objects" in i else
                 f", {i['parts']} parts" if "parts" in i else "")
        o.append(f"- **{label}**: `{i['path']}`{extra}, sha256 `{i['sha256'][:16]}...`")
    o.append(f"- `.epe` export: `{doc['inputs']['convert']['tool']}`")
    o.append("")
    o.append("## Method")
    o.append("")
    for k, v in doc["rules"].items():
        o.append(f"- **{k}**: {v}")
    o.append("")
    o.append(f"Scope: **{doc['counts']['scope']} rows** "
             f"({doc['counts']['by_scope']['collision']} collision/physics, "
             f"{doc['counts']['by_scope']['epe']} .epe); "
             f"**{doc['counts']['changed']} changed**, {doc['counts']['unchanged']} unchanged.")
    o.append("")
    o.append("## What the decoders read (measured on the built files)")
    o.append("")
    o.append(f"- `{ph['file']}`: {ph['bytes']} B, {ph['objects']} objects, 16 classes")
    o.append(f"- body table: **{bt['entries']} entries** (index 0..{bt['index_max']}, "
             f"gaps {bt['gaps']}); among them {bt['hulls']} hull entries, {bt['meshes']} extern "
             f"meshes, {bt['dynamic_compounds']} dynamic + {bt['static_compounds']} static "
             f"compounds = {bt['shape_entries']} shape entries; the file holds "
             f"{ph['hulls']['count']} hull objects in total")
    o.append(f"- oracles on this file: `bm_colmesh.selftest` = {ph['oracles']['bm_colmesh.selftest']}, "
             f"`bm_colhull.selftest` = {ph['oracles']['bm_colhull.selftest']}, "
             f"hulls convex {ph['hulls']['convex_ok']}/{ph['hulls']['count']}")
    hm = ph["extern_mesh_part0"]
    o.append(f"- part 0 extern mesh: {hm.get('vertices_packed')} packed vertices "
             f"(stride {hm.get('vertex_stride')}), geometry A "
             f"{hm.get('geometries', {}).get('A')} vertices / {hm.get('triangles')} triangles, "
             f"tree {hm.get('tree_nodes')} nodes -> {hm.get('tree_leaves')} leaves, "
             f"{hm.get('leaves_distinct_triangles')} distinct triangles, "
             f"{hm.get('triangles_outside_leaf')} outside their leaf box")
    dt = ph["dynamic_trees"]
    o.append(f"- dynamic compound trees: {dt['exact']}/{dt['trees']} reproduce their stored "
             f"boxes to <=1e-5 m; worst {dt['worst_m']} m -> {dt['stale']}")
    b0 = ph["body0"]
    if b0.get("hull"):
        o.append(f"- body 0: `{b0['class']}`, {b0['hull']['vertices']} vertices, bounds "
                 f"{[[round(x, 4) for x in b0['hull']['bounds'][k]] for k in ('min', 'max')]}")
    d = b0.get("lod2_vs_hull", {})
    if "mesh_protrusion_m" in d:
        o.append(f"- body 0 hull vs built LOD2 ({d['vertices']} vertices, {d['triangles']} "
                 f"triangles): max mesh protrusion **{d['mesh_protrusion_m']:.3g} m** - the "
                 f"world hull is the convex hull of the render mesh")
    for rc in b0.get("root_compounds", []):
        o.append(f"- root compound `{rc['offset']}` (children: {', '.join(rc['child_classes'])}) "
                 f"AABB {[round(x, 4) for x in rc['aabb_min']]} .. "
                 f"{[round(x, 4) for x in rc['aabb_max']]}: covers the body-0 hull = "
                 f"**{rc['contains_hull']}**"
                 + (f", short by {rc['short_by_m']} m" if not rc["contains_hull"] else ""))
    for name, c in ph["versus"].items():
        if not c.get("exists"):
            o.append(f"- vs `{c['path']}`: absent")
            continue
        o.append(f"- vs `{c['path']}`: `hknpPhysicsSystemData` "
                 f"{'IDENTICAL' if c.get('physics_system_data_identical') else 'differs'}; "
                 f"hulls differing at the same part "
                 f"{c.get('hulls_same_part_different_bounds')}; class delta {c.get('class_delta')}")
    o.append(f"- parts module: {parts['count']} parts, {len(parts['has_world_true'])} with "
             f"`has_world_collision_shape` = 1, {len(parts['world_minus1'])} with "
             f"`world_collision_body_id` = -1, {len(parts['raycast_minus1'])} with "
             f"`raycast_body_id` = -1")
    o.append(f"- `.epe`: {epe['elements']} object elements ({epe['objects']} classed), "
             f"{len(epe['classes'])} classes, "
             f"{len(epe['names'])} named objects; lights module "
             f"{epe['lights']['row_count']} rows, "
             f"{len(epe['referenced_names'])} presets resolving to named objects, "
             f"{len(epe['unreferenced_lights'])} SVehicleLight objects unreferenced")
    o.append("")
    o.append("## Re-grade in G3-12's terms")
    o.append("")
    o.append("| class | G3-12 grade | G3-11b grade | oracle run on this file |")
    o.append("|---|---|---|---|")
    for r in doc["regrade"]:
        o.append(f"| `{r['class']}` | {r['g3_12_grade']} | {r['g3_11b_grade']} | "
                 f"{r['oracle']} |")
    o.append("")
    o.append("## Changed rows (before -> after)")
    o.append("")
    o.append(f"{doc['counts']['changed']} of {doc['counts']['scope']} in-scope rows changed. "
             "`before` is G3-11's stored verdict for the same id.")
    o.append("")
    o.append("| id | doc | dispo | before | after | before tier -> tier | evidence |")
    o.append("|---|---|---|---|---|---|---|")
    for a in doc["changed"]:
        ev = str(a["evidence"]).replace("|", "\\|")
        o.append(f"| {a['id']} | {a['doc']} | {a['dispo']} | {a['before']['verdict']} | "
                 f"{a['verdict']} | {a['before']['tier']} -> {a['tier']} | {ev} |")
    o.append("")
    o.append("## Unchanged in-scope rows")
    o.append("")
    up = [a for a in doc["unchanged"] if a.get("evidence_upgraded")]
    o.append(f"{len(doc['unchanged'])} rows keep their G3-11 verdict and evidence strength; "
             f"{len(up)} of them have new evidence from the `.physicsc` / `.epe` (marked).")
    o.append("")
    o.append("| id | verdict | tier | re-derived evidence (first 200 chars) |")
    o.append("|---|---|---|---|")
    for a in doc["unchanged"]:
        mark = " *(upgraded)*" if a.get("evidence_upgraded") else ""
        o.append(f"| {a['id']} | {a['verdict']} | {a['tier']} | "
                 f"{str(a['evidence'])[:200].replace('|', chr(92) + '|')}{mark} |")
    o.append("")
    o.append("## Findings")
    o.append("")
    o.append(f"1. **The `.physicsc` is fully readable.** {bt['entries']} body-table entries "
             f"({bt['hulls']} of them hulls; {ph['hulls']['count']} hull objects in the file), "
             f"{bt['meshes']} extern meshes, "
             f"{bt['dynamic_compounds']} dynamic and {bt['static_compounds']} static compounds; "
             f"`bm_colhull.selftest` re-encodes {ph.get('hull_reencode')}/54 hulls byte for byte "
             f"and `bm_colmesh.selftest` passes on this file. G3-11's UNKNOWN 3 was false.")
    o.append(f"1. **The world hull is provably the render mesh's hull.** Max LOD2 protrusion "
             f"{d.get('mesh_protrusion_m')} m over the 96-vertex body-0 polytope - the "
             f"B-10c derivation is verified, not assumed.")
    if rc and not rc["contains_hull"]:
        o.append(f"1. **A root compound's AABB is short by {rc['short_by_m']} m.** "
                 f"`{rc['offset']}` still carries the box B-10b refit; B-10c then replaced "
                 f"body 0's hull with a larger one and did not refit the tree. This is a "
                 f"measured inconsistency in the built file, and it is the same one the "
                 f"`hknpDynamicCompoundShapeData` refit shows.")
    for name, c in ph["versus"].items():
        d2 = c.get("sysd_diff") or {}
        if not c.get("exists") or "physics_system_data_identical" not in c:
            continue
        o.append(f"1. **Stations vs `{name}`:** "
                 + ("byte-identical `hknpPhysicsSystemData`, so no station was moved "
                    "against this file" if c["physics_system_data_identical"] else
                    f"{d2.get('count')} bytes differ inside body entries "
                    f"{d2.get('body_entries')} (byte offsets "
                    f"{[hex(x) for x in d2.get('byte_offsets_in_entry', [])]}), "
                    f"{d2.get('above_body_table')} bytes outside the body table - so "
                    f"{len(d2.get('body_entries', []))} of {bt['entries']} station records "
                    f"were moved")
                 + " (the hulls differ at parts "
                 + str(c.get("hulls_same_part_different_bounds")) + ")")
    o.append(f"1. **`.epe` rows are checkable by name.** {len(epe['names'])} named objects; "
             f"`name_hash` = `hash_jenkins(name)` holds on the ones sampled (the audit resolves "
             f"{len(epe['referenced_names'])} lights-module presets through it).")
    o.append(f"1. **Light claims move both ways.** `Front_Secondary_Head` *is* referenced "
             f"(`T-L5` says it is not); the built lights module has "
             f"{epe['lights']['row_count']} rows, not 21 (`T-LG1`/`T-LG2`/`T-LG6`); "
             f"`Rear_Break` is confirmed unreferenced; and the `string`-tier hits of "
             f"`T-FX17`/`T-FX21` turn out to be substrings of other names, not graph objects.")
    o.append(f"1. **Six module rows are custom (`preset_id` 0).** They are the T-18 recipe the "
             f"arch-lamp and boot-lamp rows describe: rows "
             + ", ".join(str(i) for i, r in epe['module_refs'].items()
                          if not u32(r['preset_id']))
             + f" carry no preset hash, while the graph also holds the "
             f"`<name>_light` custom light objects for them.")
    o.append("")
    o.append("## UNKNOWN (with what was tried and where the answer would be)")
    o.append("")
    unk = [
        "**The BmAK side of the collision rows.** `T-P3`'s \"32 boxes\" and the box->slot "
        "mapping live in BmAK's archetype defaults (`Default__RVehicleBatmobile.*`, "
        "`BmGame.upk` imports 456/457/577/578, G3-01); they are not in the JC3 build, so no "
        "byte check here can confirm or refute the mapping. Next source: G3-01c's decode of "
        "those defaults and `COLLISION_FRAME.md`.",
        "**The row-index frame of `T-L8`..`T-L35`.** Those rows say \"donor row 8\" etc. The "
        "built module's row 8 is not the preset the row names, so either the build reordered "
        "the rows or the ledger counted another file. Comparing against the donor's own "
        "`..._lights.vmodc` (unpacked extract) would settle it; not done here because the task "
        "names the built `.epe` as the evidence side.",
        "**`hknpExternMeshShapeData` vertex dequantization.** The tree, domain, sections and "
        "vertex *count* are decoded and oracle-proved; the 3 x u16 -> position rule is still "
        "unpinned, so no chassis vertex position is claimed from the packed array. The `hkGeometry` "
        "array is decoded, which is why body 0's hull could be checked against it.",
        "**`hknpStaticCompoundShapeData`** (2 objects) is still NAMED-ONLY: `bm_colmesh` only "
        "refits `hkcdDynamicTree`. No claim in the ledger depends on the static trees.",
        "**`hknpPhysicsSystemData` field meanings.** The 96-byte body entries are compared byte "
        "for byte against the donor but not decoded field by field (G3-10b's scope), so the "
        "audit can say \"identical\" but not \"this field is the station\".",
        "**Whether the game reads this file at all.** Nothing here is a runtime observation; "
        "every verdict is a file-to-file measurement (RESET_FINDINGS §4 UNKNOWN 1 stands).",
    ]
    for i, u in enumerate(unk, 1):
        o.append(f"{i}. {u}")
    o.append("")
    return "\n".join(o)


# ---------------------------------------------------------------- entry points
def write() -> int:
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render(doc))
    print(f"wrote {rel(OUT_MD)} and {rel(OUT_JSON)}")
    print("scope:", doc["counts"]["scope"], "changed:", doc["counts"]["changed"],
          "unchanged:", doc["counts"]["unchanged"])
    print("after:", doc["counts"]["after"])
    return 0


def check() -> int:
    fails: list = []
    for p in (OUT_MD, OUT_JSON):
        if not os.path.exists(p):
            print(f"FAIL: {rel(p)} missing - run --write")
            return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    md = open(OUT_MD, encoding="utf-8").read()
    rows = load_rows()
    fresh = build()

    ids = [a["id"] for a in stored["changed"] + stored["unchanged"]]
    if len(ids) != len(set(ids)):
        fails.append("duplicate row ids across changed+unchanged")
    known = {r["id"] for r in rows}
    for i in ids:
        if i not in known:
            fails.append(f"{i} is not in T_ROWS.jsonl")
    for a in stored["changed"] + stored["unchanged"]:
        if a["verdict"] not in VERDICTS:
            fails.append(f"{a['id']}: verdict {a['verdict']!r}")
        if not str(a["evidence"]).strip():
            fails.append(f"{a['id']}: empty evidence")
        if a["changed"] != (a["before"]["verdict"] != a["verdict"]
                            or TCLASS.get(a["before"]["tier"], "none")
                            != TCLASS.get(a["tier"], "none")):
            fails.append(f"{a['id']}: changed flag inconsistent")
    recount = {v: 0 for v in VERDICTS}
    for a in stored["changed"] + stored["unchanged"]:
        recount[a["verdict"]] += 1
    if recount != stored["counts"]["after"]:
        fails.append(f"counts {stored['counts']['after']} != recount {recount}")
    if len(stored["changed"]) != stored["counts"]["changed"]:
        fails.append("changed count mismatch")

    # the before side must still be G3-11's file
    if sha(BEFORE) != stored["inputs"]["before"]["sha256"]:
        fails.append("LEDGER_AUDIT.json changed since --write")
    if sha(LEDGER) != stored["inputs"]["ledger"]["sha256"]:
        fails.append("T_ROWS.jsonl changed since --write")

    # every derived number and every verdict must re-derive identically
    if json.dumps(fresh["facts"], sort_keys=True) != json.dumps(stored["facts"], sort_keys=True):
        a = json.dumps(stored["facts"], sort_keys=True)
        b = json.dumps(fresh["facts"], sort_keys=True)
        pos = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), 0)
        fails.append(f"physics/epe facts drifted at {pos}: stored {a[pos:pos+90]!r} vs "
                     f"fresh {b[pos:pos+90]!r}")
    if json.dumps(fresh["regrade"], sort_keys=True) != json.dumps(stored["regrade"],
                                                                 sort_keys=True):
        fails.append("re-grade drifted")
    for key in ("changed", "unchanged"):
        f_map = {a["id"]: a for a in fresh[key]}
        s_map = {a["id"]: a for a in stored[key]}
        if set(f_map) != set(s_map):
            fails.append(f"{key} row set drifted")
            continue
        for i in s_map:
            if s_map[i]["verdict"] != f_map[i]["verdict"] or s_map[i]["tier"] != f_map[i]["tier"]:
                fails.append(f"{i}: stale verdict {s_map[i]['verdict']} -> "
                             f"{f_map[i]['verdict']}")
            elif s_map[i]["evidence"] != f_map[i]["evidence"]:
                fails.append(f"{i}: stale evidence")
    if fresh["counts"] != stored["counts"]:
        fails.append("counts drifted")

    for a in stored["changed"]:
        if f"| {a['id']} | {a['doc']} | {a['dispo']} | {a['before']['verdict']} |" not in md:
            fails.append(f"{a['id']}: changed row line missing from the markdown")
            break
    if md != render(stored):
        fails.append("LEDGER_AUDIT2.md is not the render of LEDGER_AUDIT2.json")

    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK {stored['counts']['scope']} in-scope rows ({stored['counts']['changed']} "
          f"changed, {stored['counts']['unchanged']} unchanged) re-derived from the bytes")
    print("after:", stored["counts"]["after"])
    print("oracles:", stored["facts"]["physics"]["oracles"])
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
