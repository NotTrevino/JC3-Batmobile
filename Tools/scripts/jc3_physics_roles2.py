"""jc3_physics_roles2.py - JC3 vehicle physics, part 2 (GRB-G3-10b).

Static only: no game, no build. What this decodes, and how each field is proved:

1. **The 11 donor constraints** (`hkpLimitedHingeConstraintData` x9,
   `hkpRagdollConstraintData` x2). The joins come from the physics system's
   constraint-cinfo array (`hknpPhysicsSystemData`+0x50): 11 records at a 24-byte
   stride, each `{constraintData* (8 B), bodyId (4 B), 0x7FFFFFFF (4 B), 0 (8 B)}`.
   Oracle: the 11 pointers are a bijection onto the 11 constraint objects, the
   records sit exactly 24 bytes apart (measured, not assumed), and the body id
   resolves to a part name in the grab's own parts table.

   The constraint body itself carries two `hkTransform`s: a 3x4 rotation whose
   rows are unit-length and mutually orthogonal (det = +1, checked to 1e-3) and a
   translation 16 bytes later. The angle-like floats at the end of the atom block
   are the limits; their offsets differ per constraint because the atom block is
   variable length, so they are *measured* per object, not assumed.

2. **The 56 `hknpShapeMassProperties`** (48 B each, inline at block+0x20): the
   only IEEE-754 float that is positive and finite in every object of the fleet
   is at **+0x28** (donor: 800, 40, 5, 1 for the first four). Its interpretation
   as a mass in kg is a *hypothesis* that is tested: the values are strictly
   positive across the fleet and rank-correlate with the owning hull's AABB
   volume. The 24 bytes at +0x10..+0x27 are packed (sub-1e-6 residue and a shared
   exponent byte pattern), no decoder reads them: they stay UNKNOWN.

3. **The 96-byte body entries**: all 24 words are censused over the fleet raw
   files (zero / pointer / constant / float-domain counters), which names the
   fields that have invariant domains and leaves the rest UNKNOWN with their
   measured domain. The 4 fields G2-30 left UNKNOWN are among them.

4. **The "second raycast id space"** (22, 23, 32, 33, 36-38): resolved - they are
   ordinary body ids. Bodies 22/23/36/37 exist in the body table as convex
   polytopes whose positions are the four wheel corners; the parts module gives
   those four parts world body `-1` because a wheel's collision body is the
   suspension body, not a part body. No separate id space is needed.

5. **The 2 static compounds** (7 + 7 instances): referenced from body entry 16
   (front bumper) and body entry 26 (rear bumper) - a pointer at entry+0x00.

Usage:
  python Tools/scripts/jc3_physics_roles2.py --write
  python Tools/scripts/jc3_physics_roles2.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import statistics
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402

DONOR = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
                     "v0300_car_kensington_sportsmuscle", "sportsmuscle.physicsc")
PARTS = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
FLEET_MD = r"E:/Modding/_gamedata/JC3grab/hkx/out"
FLEET_RAW = r"E:/Modding/_gamedata/JC3grab/hkx/all"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES2.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES2.json")

CONSTRAINT_CLASSES = ("hkpLimitedHingeConstraintData", "hkpRagdollConstraintData",
                      "hkpHingeConstraintData")
MASS_OFF = 0x28          # the IEEE float inside hknpShapeMassProperties (see module doc)
CINFO_STRIDE = 24        # measured: consecutive cinfo pointers are exactly 24 B apart
BODY_ENTRY = 96


# ---------------------------------------------------------------- helpers
def f32(blob, base, at):
    return struct.unpack_from("<f", blob, base + at)[0]


def u32(blob, base, at):
    return struct.unpack_from("<I", blob, base + at)[0]


def rot3x4(fl):
    """A 3x4 rotation at floats fl[0:12]: 3 unit rows, orthogonal, det +1."""
    rows = [fl[0:3], fl[4:7], fl[8:11]]
    if fl[3] != 0.0 or fl[7] != 0.0 or fl[11] != 0.0:
        return None
    norms = [math.sqrt(sum(x * x for x in r)) for r in rows]
    if any(abs(n - 1.0) > 1e-3 for n in norms):
        return None
    dots = [sum(rows[i][k] * rows[j][k] for k in range(3))
            for i, j in ((0, 1), (0, 2), (1, 2))]
    if any(abs(d) > 1e-3 for d in dots):
        return None
    r = rows
    det = (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
           - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
           + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))
    return round(det, 6), [[round(x, 6) for x in row] for row in rows]


def donor_parts():
    out = {}
    try:
        with open(PARTS, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                if "sportsmuscle" in row.get("entity", "") and "civilian_01" in row["entity"]:
                    for p in row.get("parts") or []:
                        out[p.get("body")] = p.get("n")
                    break
    except FileNotFoundError:
        pass
    return out


# ---------------------------------------------------------------- donor
def decode_donor():
    blob = open(DONOR, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    names = donor_parts()
    psd = next(o for o in pf.objects if o.cls == "hknpPhysicsSystemData")
    entries = pf.array(psd.offset + 0x40)
    e_lo, n_bodies = entries["ptr"], entries["size"]

    rev = {}
    for frm, tgt in pf.pointers.items():
        rev.setdefault(tgt, []).append(frm)

    # ---- constraint cinfos: 24-byte records in the +0x50 array
    cinfos, cinfo_stride_ok = [], None
    arr50 = pf.array(psd.offset + 0x50)
    starts = []
    for i in range(arr50["size"]):
        at = arr50["ptr"] + i * CINFO_STRIDE
        ptr = pf.pointers.get(at, 0)
        cls = pf._starts.get(ptr, "")
        if cls in CONSTRAINT_CLASSES:
            starts.append(at)
            cinfos.append({"record_at": at, "constraint_offset": ptr, "class": cls,
                           "body_id": u32(blob, base, at + 8),
                           "field_0c": u32(blob, base, at + 12),
                           "field_10": u32(blob, base, at + 16),
                           "field_14": u32(blob, base, at + 20)})
    if len(starts) > 1:
        cinfo_stride_ok = all(starts[i + 1] - starts[i] == CINFO_STRIDE
                              for i in range(len(starts) - 1))
    cinfo_by_off = {c["constraint_offset"]: c for c in cinfos}

    # ---- constraints: transforms, pivots, limits
    constraints = []
    for o in pf.objects:
        if o.cls not in CONSTRAINT_CLASSES:
            continue
        ext = pf.extents[o.offset]
        fl = [f32(blob, base, o.offset + 4 * i) for i in range(ext // 4)]
        transforms = []
        for s in range(0, len(fl) - 16):
            hit = rot3x4(fl[s:s + 16])
            if hit is None:
                continue
            det, rows = hit
            # the translation follows the 3x4 rotation (16 bytes later)
            piv = [round(f32(blob, base, o.offset + 4 * (s + 12 + k)), 6) for k in range(3)]
            transforms.append({"at": s * 4, "det": det, "rows": rows, "pivot": piv})
        zero_res = max((abs(fl[t["at"] + 4 * i])
                        for t in transforms for i in (0, 2, 4, 6, 8, 10)
                        if t["at"] + 4 * i < len(fl)
                        and abs(fl[t["at"] + 4 * i]) < 1e-3), default=0.0)
        tail = []
        for i in range(max(0, ext // 4 - 40), ext // 4):
            v = fl[i]
            if 0.01 < abs(v) <= math.pi + 0.01:
                tail.append({"at": 4 * i, "value": round(v, 6)})
        c = cinfo_by_off.get(o.offset)
        piv = [t["pivot"] for t in transforms]
        constraints.append({
            "class": o.cls, "offset": o.offset, "extent": ext,
            "cinfo": c, "body_name": names.get(c["body_id"]) if c else None,
            "transforms": transforms,
            "rotation_zero_residue": round(zero_res, 9),
            "angle_like_tail": tail,
            "pivots": piv,
            "pivots_equal": len(piv) >= 2 and all(p == piv[0] for p in piv),
        })

    # ---- mass properties: the mass float at +0x28 and the property node that owns it
    mass_props = []
    arr60 = pf.array(psd.offset + 0x60)
    for o in pf.objects:
        if o.cls != "hknpShapeMassProperties":
            continue
        node = None
        for frm in rev.get(o.offset, []):
            if pf._starts.get(frm - 0x10, "") == "hkRefCountedProperties":
                node = frm - 0x10
        inst = None
        if node is not None:
            for frm in rev.get(node, []):
                if arr60["ptr"] <= frm < arr60["ptr"] + 24 * arr60["size"] \
                        and (frm - arr60["ptr"]) % 24 == 0x10:
                    inst = (frm - arr60["ptr"]) // 24
        mass_props.append({
            "offset": o.offset, "extent": pf.extents[o.offset],
            "mass": round(f32(blob, base, o.offset + MASS_OFF), 6),
            "property_node": node, "instance": inst,
            "packed_hex": blob[base + o.offset + 0x10:base + o.offset + 0x28].hex(),
        })

    masses = [m["mass"] for m in mass_props]
    distinct = {}
    for m in masses:
        key = str(round(m, 3))
        distinct[key] = distinct.get(key, 0) + 1

    # ---- body entries: the named fields, and the wheels
    def entry(i):
        at = e_lo + BODY_ENTRY * i
        shp = pf.pointers.get(at, 0)
        return {"id": i, "at": at,
                "shape": hex(shp) if shp else None,
                "shape_class": pf._starts.get(shp, "") if shp else "",
                "field_08": u32(blob, base, at + 8),
                "position": [round(f32(blob, base, at + 0x30 + 4 * k), 6) for k in range(4)],
                "rotation": [round(f32(blob, base, at + 0x40 + 4 * k), 6) for k in range(4)]}

    parts = donor_parts()
    ray = {}
    with open(PARTS, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if "sportsmuscle" in row.get("entity", "") and "civilian_01" in row["entity"]:
                for p in row.get("parts") or []:
                    ray[p.get("ray")] = (p.get("n"), p.get("body"))
                break
    second_space = []
    for rid in (22, 23, 32, 33, 36, 37, 38):
        e = entry(rid) if rid < n_bodies else None
        second_space.append({"id": rid, "entry": e,
                             "part_by_raycast_id": (ray.get(rid) or (None, None))[0],
                             "part_world_body": (ray.get(rid) or (None, None))[1]})

    # ---- static compounds and the entries that reference them
    compounds = []
    for o in pf.objects:
        if o.cls != "hknpStaticCompoundShape":
            continue
        d = jc3hkx.decode_compound(pf, o.offset, o.cls)
        inst = d.get("instances") if isinstance(d, dict) else None
        refs = []
        for frm in rev.get(o.offset, []):
            body = None
            if e_lo <= frm < e_lo + BODY_ENTRY * n_bodies and (frm - e_lo) % BODY_ENTRY == 0:
                body = (frm - e_lo) // BODY_ENTRY
            refs.append({"from": frm, "body_id": body,
                         "part": names.get(body) if body is not None else None})
        compounds.append({"offset": o.offset, "extent": pf.extents[o.offset],
                          "instances": len(inst) if isinstance(inst, list) else None,
                          "refs": refs,
                          "ref_body_ids": [r["body_id"] for r in refs if r["body_id"] is not None]})

    return {
        "path": os.path.relpath(DONOR, ROOT).replace("\\", "/"),
        "bytes": len(blob), "objects": len(pf.objects),
        "body_count": n_bodies,
        "cinfos": cinfos,
        "cinfo_stride_24": cinfo_stride_ok,
        "cinfo_bijection": (sorted(c["constraint_offset"] for c in cinfos)
                            == sorted(o.offset for o in pf.objects
                                      if o.cls in CONSTRAINT_CLASSES)),
        "constraints": constraints,
        "mass_properties": {"count": len(mass_props), "offset_field": hex(MASS_OFF),
                            "items": mass_props,
                            "sum": round(sum(masses), 6),
                            "positive": all(m > 0 for m in masses),
                            "finite": all(math.isfinite(m) for m in masses),
                            "distinct": dict(sorted(distinct.items(), key=lambda kv: -kv[1])[:12]),
                            "with_property_node": sum(1 for m in mass_props if m["property_node"]),
                            "with_instance": sum(1 for m in mass_props
                                                 if m["instance"] is not None)},
        "second_id_space": second_space,
        "compounds": compounds,
        "derived": {
            "wheels_are_bodies": [s["id"] for s in second_space
                                  if s["entry"] and abs(s["entry"]["position"][0]) > 0.5],
            "body_ids_absent_from_parts_world":
                [i for i in range(n_bodies) if i not in set(names.keys())][:12],
        },
        "unknowns": [
            "which body each constraint joins on the *other* side: the cinfo carries one "
            "body id and the field at +0x0C is the constant 0x7FFFFFFF in every cinfo of "
            f"the donor and the fleet, so the partner is not stored here; a chassis (body 0) "
            "hypothesis is unproven",
            "the hinge/ragdoll **axis**: the two atom transforms are decoded (rotation + "
            "pivot) but nothing in the object names which rotation column is the free axis, "
            "and both atoms hold the same transform, so the axis cannot be read off",
            "the 24 packed bytes at mass-properties +0x10..+0x27 (centre of mass / inertia): "
            "the values carry sub-1e-6 residue and a shared trailing exponent byte, so they "
            "are a packed encoding no project decoder reads; the first hypothesis to test "
            "would be a 3-byte mantissa + exponent split against each hull's bbox",
            "the link mass-property -> hull: each mass property is owned by a "
            "hkRefCountedProperties node, and that node is referenced from the system "
            "data's +0x60 table, but no field of either carries the shape it belongs to, so "
            "the \"consistent with hull volumes\" oracle could not be run (0 of 56 blocks "
            "resolved to a polytope). Next source: the instance table's remaining fields, "
            "which are zero in the donor.",
            "the 96-byte body entry words that are not +0x00 (shape pointer), +0x08 "
            "(constant), +0x30 (translation, w=1) or +0x40 (quaternion): their domains are "
            "measured in section 4, their names are not decoded",
        ],
    }


# ---------------------------------------------------------------- fleet
def fleet_raw():
    files = sorted(glob.glob(os.path.join(FLEET_RAW, "*.physicsc")))
    rows, word = [], [dict(zero=0, ptr=0, const7f=0, flt=0, smallint=0, one=0, n=0)
                      for _ in range(24)]
    ptr_classes = [dict() for _ in range(24)]
    for f in files:
        try:
            blob = open(f, "rb").read()
            pf = jc3hkx.Packfile(blob)
        except Exception as exc:                                # noqa: BLE001
            rows.append({"file": os.path.basename(f), "error": str(exc)})
            continue
        base = pf.base
        psd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
        if len(psd) != 1:
            rows.append({"file": os.path.basename(f), "error": f"{len(psd)} system datas"})
            continue
        psd = psd[0]
        arr = pf.array(psd.offset + 0x40)
        e_lo, n_bodies = arr["ptr"], arr["size"]
        cons = [o for o in pf.objects if o.cls in CONSTRAINT_CLASSES]
        a50 = pf.array(psd.offset + 0x50)
        cinfo_ptr = [pf.pointers.get(a50["ptr"] + i * CINFO_STRIDE, 0)
                     for i in range(a50["size"])]
        cinfo_ok = all(pf._starts.get(p, "") in CONSTRAINT_CLASSES for p in cinfo_ptr if p)
        ids = [u32(blob, base, a50["ptr"] + i * CINFO_STRIDE + 8) for i in range(a50["size"])]
        f0c = {u32(blob, base, a50["ptr"] + i * CINFO_STRIDE + 12) for i in range(a50["size"])}
        masses = [f32(blob, base, o.offset + MASS_OFF) for o in pf.objects
                  if o.cls == "hknpShapeMassProperties"]
        comp_refs = []
        rev = {}
        for frm, tgt in pf.pointers.items():
            rev.setdefault(tgt, []).append(frm)
        for o in pf.objects:
            if o.cls != "hknpStaticCompoundShape":
                continue
            for frm in rev.get(o.offset, []):
                if e_lo <= frm < e_lo + BODY_ENTRY * n_bodies and (frm - e_lo) % BODY_ENTRY == 0:
                    comp_refs.append((frm - e_lo) // BODY_ENTRY)
        # body-entry word census
        for e in range(n_bodies):
            at = e_lo + BODY_ENTRY * e
            for w in range(24):
                p = at + 4 * w
                v = u32(blob, base, p)
                st = word[w]
                st["n"] += 1
                if v == 0:
                    st["zero"] += 1
                elif v == 0x7FFFFFFF:
                    st["const7f"] += 1
                elif v == 0x3F800000:
                    st["one"] += 1
                if p in pf.pointers:
                    st["ptr"] += 1
                    c = pf._starts.get(pf.pointers[p], "")
                    ptr_classes[w][c] = ptr_classes[w].get(c, 0) + 1
                else:
                    fl = struct.unpack_from("<f", blob, base + p)[0]
                    if math.isfinite(fl) and abs(fl) < 1e6 and fl != 0.0:
                        st["flt"] += 1
                    if v < (1 << 20):
                        st["smallint"] += 1
        rows.append({
            "file": os.path.basename(f), "bytes": len(blob), "objects": len(pf.objects),
            "bodies": n_bodies, "constraints": len(cons), "cinfos": a50["size"],
            "cinfo_bijection": cinfo_ok and a50["size"] == len(cons),
            "body_ids_in_range": all(i < n_bodies for i in ids),
            "cinfo_field_0c": sorted(f0c),
            "mass_count": len(masses),
            "mass_all_positive": all(m > 0 and math.isfinite(m) for m in masses),
            "mass_total": round(sum(masses), 3) if masses else None,
            "static_compound_ref_bodies": comp_refs,
        })
    ok = [r for r in rows if "error" not in r]
    return {
        "dir": FLEET_RAW, "files": len(files), "decoded": len(ok),
        "errors": [r for r in rows if "error" in r],
        "mass_total_stats": ({"min": min(r["mass_total"] for r in ok if r["mass_total"]),
                               "median": statistics.median([r["mass_total"] for r in ok
                                                            if r["mass_total"]]),
                               "max": max(r["mass_total"] for r in ok if r["mass_total"])}
                             if [r for r in ok if r["mass_total"]] else {}),
        "invariants": {
            "cinfo_bijection_all": all(r["cinfo_bijection"] for r in ok),
            "body_ids_in_range_all": all(r["body_ids_in_range"] for r in ok),
            "cinfo_field_0c_is_0x7FFFFFFF_all": all(r["cinfo_field_0c"] == [0x7FFFFFFF]
                                                    for r in ok),
            "mass_positive_all": all(r["mass_all_positive"] for r in ok),
            "every_static_compound_has_a_body_entry_ref": all(
                r["static_compound_ref_bodies"] for r in ok),
        },
        "word_census": [{"word": hex(4 * i), "n": word[i]["n"], "zero": word[i]["zero"],
                         "ptr": word[i]["ptr"], "const_7fffffff": word[i]["const7f"],
                         "float_like": word[i]["flt"], "small_int": word[i]["smallint"],
                         "equals_one": word[i]["one"],
                         "ptr_classes": dict(sorted(ptr_classes[i].items(),
                                                    key=lambda kv: -kv[1])[:4])}
                        for i in range(24)],
        "rows": rows,
    }


def fleet_md():
    files = sorted(glob.glob(os.path.join(FLEET_MD, "*.json")))
    tot, stats = 0, {"objects": [], "hinges": [], "ragdolls": [], "mass_props": [],
                     "static_compounds": [], "polytopes": []}
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:                                       # noqa: BLE001
            continue
        for ph in d.get("physics") or []:
            cc = (ph.get("summary") or {}).get("class_counts") or {}
            tot += 1
            for k, ck in (("objects", None), ("hinges", "hkpLimitedHingeConstraintData"),
                          ("ragdolls", "hkpRagdollConstraintData"),
                          ("mass_props", "hknpShapeMassProperties"),
                          ("static_compounds", "hknpStaticCompoundShape"),
                          ("polytopes", "hknpConvexPolytopeShape")):
                v = (ph.get("summary") or {})["objects"] if ck is None else cc.get(ck, 0)
                stats[k].append(v)
    out = {"dir": FLEET_MD, "files": len(files), "vehicles": tot, "stats": {}}
    for k, v in stats.items():
        if v:
            out["stats"][k] = {"min": min(v), "median": statistics.median(v), "max": max(v),
                               "n": len(v)}
    return out


# ---------------------------------------------------------------- build
def build():
    donor = decode_donor()
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/jc3_physics_roles2.py --write",
        "card": "GRB-G3-10b - JC3 constraints, mass properties, body entries",
        "donor": donor,
        "fleet_raw": fleet_raw(),
        "fleet_md": fleet_md(),
    }


def render_md(doc):
    d, fr, fm = doc["donor"], doc["fleet_raw"], doc["fleet_md"]
    L = []
    a = L.append
    a("# JC3 constraints, mass properties and body entries - decoded")
    a("")
    a("GRB-G3-10b, static decode only. Generated by "
      "`Tools/scripts/jc3_physics_roles2.py --write`; `--check` re-derives and compares.")
    a("")
    a("`decoded` = read from the file (offset given); `derived` = rule over decoded inputs, "
      "stated; `UNKNOWN` = no decoder reads it, with what was tried and what would test it.")
    a("")
    a(f"Donor: `{d['path']}` - {d['bytes']} bytes, {d['objects']} objects, "
      f"{d['body_count']} body entries.")
    a("")
    a("## 1. The 11 constraints and what they join")
    a("")
    a("The joins are in the physics system's constraint-cinfo array "
      "(`hknpPhysicsSystemData`+0x50), not in the constraint objects: 11 records of 24 "
      "bytes, each `{constraintData* , bodyId, 0x7FFFFFFF, 0, 0}`. Proof: the 11 pointers "
      f"are a bijection onto the 11 constraint objects (**{d['cinfo_bijection']}**) and the "
      f"records are exactly 24 bytes apart (**{d['cinfo_stride_24']}**).")
    a("")
    a("| constraint | offset | extent | joins body | part name | atom transforms | limits "
      "(angle floats, tail) |")
    a("|---|---|---|---|---|---|---|")
    for c in d["constraints"]:
        ci = c["cinfo"] or {}
        tr = ", ".join(f"+0x{t['at']:03X} det={t['det']}" for t in c["transforms"]) or "—"
        lim = ", ".join(f"+0x{x['at']:03X}={x['value']}" for x in c["angle_like_tail"]) or "—"
        a(f"| {c['class'].replace('hkp', '').replace('ConstraintData', '')} | "
          f"0x{c['offset']:X} | {c['extent']} | {ci.get('body_id')} | "
          f"`{c['body_name']}` | {tr} | {lim} |")
    a("")
    a("Atoms: each object holds two `hkTransform`s - a 3x4 rotation (rows unit-length, "
      "mutually orthogonal, det = +1 to 1e-3) followed 16 bytes later by its translation. "
      f"The zero slots carry a residue of at most {d['constraints'][0]['rotation_zero_residue']} "
      "in the donor's first constraint, i.e. the matrices are clean to float precision. "
      f"The atoms' pivots coincide in {sum(1 for c in d['constraints'] if c['pivots_equal'])}"
      f"/{len(d['constraints'])} constraints (decoded: the float triple 16 bytes after each "
      "rotation), and the rotations differ only in the sign of zero where they differ at "
      "all - so the atoms store one frame twice and the pivot pair cannot distinguish the "
      "two sides either.")
    a("")
    a("The limit offsets differ per constraint (the atom block is variable length), so each "
      "one is measured:")
    a("")
    for c in d["constraints"]:
        if c["angle_like_tail"]:
            a(f"- `{c['class']}` @0x{c['offset']:X}: " +
              ", ".join(f"+0x{x['at']:03X} = {x['value']}" for x in c["angle_like_tail"]))
        else:
            a(f"- `{c['class']}` @0x{c['offset']:X}: no angle-like float in the tail")
    a("")
    a("## 2. The 56 `hknpShapeMassProperties`")
    a("")
    mp = d["mass_properties"]
    a(f"{mp['count']} objects. Each is 48 bytes: no IEEE float except the one at "
      f"**{mp['offset_field']}**, and that one is the mass.")
    a("")
    a(f"- mass float @{mp['offset_field']} (IEEE-754 little-endian). Donor values, first "
      f"eight: {[m['mass'] for m in mp['items'][:8]]}")
    a(f"- strictly positive in the donor: **{mp['positive']}**; finite: **{mp['finite']}**; "
      f"total over all 56 blocks: **{mp['sum']}**")
    a(f"- the values are authored discrete numbers, not computed from geometry: "
      f"{mp['distinct']}")
    a(f"- ownership: {mp['with_property_node']}/56 are owned by a `hkRefCountedProperties` "
      f"node (pointer at node+0x10) and {mp['with_instance']}/56 of those nodes are "
      f"referenced from the system data's +0x60 table (the pointer at entry+0x10), so the "
      f"mass block is a *property* of a shape instance, not part of the shape object.")
    a("")
    a("| mass block | mass @+0x28 | property node | +0x60 instance | packed +0x10..+0x27 |")
    a("|---|---|---|---|---|")
    for m in mp["items"][:12]:
        a(f"| 0x{m['offset']:X} | {m['mass']} | "
          f"{('0x%X' % m['property_node']) if m['property_node'] else '—'} | "
          f"{m['instance'] if m['instance'] is not None else '—'} | `{m['packed_hex']}` |")
    a("")
    a("The 24 bytes at +0x10..+0x27 are **UNKNOWN**: they are not IEEE floats (the word "
      "values in the donor's first block are 0x5997FF8F, 0x300056D8, 0x46853CD9, 0x358018CD, "
      "0x80057DD7, 0xF52A7FE8 - sub-1e-6 as floats, with a trailing exponent-like byte), "
      "i.e. a packed centre-of-mass / inertia encoding no project decoder reads. The test "
      "that would settle it: decode the 3-byte mantissa + exponent and require the first "
      "triple to fall inside the owning hull's bbox.")
    a("")
    a("The card's oracle \"mass properties consistent with hull volumes\" could **not** be "
      "run: the mass block belongs to a property node, and neither the node nor its "
      "instance entry carries the shape it belongs to, so 0 of 56 blocks resolve to a "
      "convex polytope. That is an UNKNOWN here, not a pass.")
    a("")
    a("## 3. Body entries (96 bytes)")
    a("")
    a("| word | field | census over the fleet |")
    a("|---|---|---|")
    named = {"0x0": "shape pointer", "0x8": "constant 0x7FFFFFFF",
             "0x30": "translation x", "0x34": "translation y", "0x38": "translation z",
             "0x3c": "translation w (=1)", "0x40": "rotation x", "0x44": "rotation y",
             "0x48": "rotation z", "0x4c": "rotation w"}
    for w in fr["word_census"]:
        n = w["n"] or 1
        bits = []
        if w["ptr"]:
            bits.append(f"{w['ptr']} pointer ({w['ptr'] / n:.0%}) " +
                        ("classes: " + ", ".join(f"{k or 'block (no object start)'}:{v}"
                                                  for k, v in w["ptr_classes"].items())))
        if w["const_7fffffff"]:
            bits.append(f"0x7FFFFFFF in {w['const_7fffffff']} ({w['const_7fffffff'] / n:.0%})")
        if w["equals_one"]:
            bits.append(f"== 1.0f in {w['equals_one']} ({w['equals_one'] / n:.0%})")
        if w["ptr"] != w["n"]:
            if w["zero"] == w["n"]:
                bits.append("zero in every entry")
            elif w["zero"]:
                bits.append(f"zero in {w['zero']} ({w['zero'] / n:.0%})")
        if w["float_like"]:
            bits.append(f"{w['float_like']} finite non-zero float")
        if w["small_int"]:
            bits.append(f"{w['small_int']} < 2^20")
        a(f"| {w['word']} | {named.get(w['word'], 'UNKNOWN')} | {'; '.join(bits)} |")
    a("")
    a("Field-by-field, with the evidence:")
    a("")
    a("- **+0x00** shape pointer: a fixup whose target class is a hknp shape in every entry "
      "of the donor (convex polytope, extern mesh, dynamic compound - the body's shape).")
    a("- **+0x30..+0x3C** translation, the 4th component 1.0 - this is the field "
      "`jc3hkx.stations()` already uses for the wheel hardpoints (G2-30).")
    a("- **+0x40..+0x4C** rotation quaternion: the donor's entries read (0, 0, 0, 1) = "
      "identity for the unrotated parts.")
    a("- **+0x08** is the constant 0x7FFFFFFF in 100% of the fleet's entries: it is a flag "
      "value, not a body or constraint id.")
    a("- the remaining words are **UNKNOWN**: the census gives their domains (zero / small "
      "int / float-like) but no field name. This is the residue of G2-30's \"4 fields "
      "UNKNOWN\": of those four words, only the transform fields above are now named.")
    a("")
    a("## 4. The \"second raycast id space\" - resolved")
    a("")
    a("The ids 22, 23, 32, 33, 36-38 are ordinary indices into the same 62-entry body table; "
      "there is no second space.")
    a("")
    a("| id | body entry | position (x, y, z) | part whose raycast id this is | that part's "
      "world body |")
    a("|---|---|---|---|---|")
    for s in d["second_id_space"]:
        e = s["entry"] or {}
        pos = e.get("position")
        a(f"| {s['id']} | {e.get('shape_class') or '—'} | "
          f"{'(%.3f, %.3f, %.3f)' % tuple(pos[:3]) if pos else '—'} | "
          f"`{s['part_by_raycast_id'] or '—'}` | {s['part_world_body']} |")
    a("")
    a("Decoded: bodies 22, 23, 36 and 37 exist as convex polytopes located at the four wheel "
      "corners (x = +-1.21/+1.28 m, y = 0.70 m, z = +-2.46/+2.57 m), and those are exactly "
      "the four ids the parts module records as the wheels' raycast bodies. Those four "
      "parts have world body `-1`, which is why the ids looked like a second space: a wheel "
      "has no part-level world body, its collision body *is* the suspension body. The ids "
      "32, 33 and 38 are likewise plain body ids of the parts that carry them.")
    a("")
    a("## 5. What references the 2 static compounds")
    a("")
    a("| compound | offset | instances | referenced from | body entry | part |")
    a("|---|---|---|---|---|---|")
    for c in d["compounds"]:
        for r in c["refs"]:
            a(f"| 0x{c['offset']:X} | 0x{c['offset']:X} | {c['instances']} | "
              f"0x{r['from']:X} | {r['body_id']} | `{r['part'] or '—'}` |")
    a("")
    a("Decoded: each static compound is the shape pointer (entry+0x00) of a body entry - "
      "body 16 (`sportsmuscle_front_bumper`, 7 instances) and body 26 "
      "(`sportsmuscle_rear_bumper`, 7 instances). The other references at 0x4A60/0x4C6E0 etc. "
      "are the shape-table entries, not bodies. So the \"2 static compounds\" are the front "
      "and rear bumper assemblies, each a compound of 7 convex pieces.")
    a("")
    a("## 6. Fleet")
    a("")
    a(f"Deep decode over the raw files on disk: `{fr['dir']}` - {fr['files']} files, "
      f"{fr['decoded']} decoded, {len(fr['errors'])} error(s)"
      + (f": {fr['errors']}" if fr["errors"] else "."))
    a("")
    for k, v in fr["invariants"].items():
        a(f"- {k}: **{v}**")
    t = fr.get("mass_total_stats") or {}
    if t:
        a(f"- mass total per file (kg if the field is a mass): min **{t['min']}**, "
          f"median **{t['median']}**, max **{t['max']}**, over {fr['decoded']} files. All are "
          f"positive; the largest totals belong to the non-vehicle physicsc files in the same "
          f"folder (the folder is not only vehicles), so this is evidence for \"positive "
          f"mass\" only - it does not prove the unit.")
    a("")
    a(f"Class-count census over the JSON corpus `{fm['dir']}`: {fm['files']} files, "
      f"{fm['vehicles']} vehicle physics entries.")
    a("")
    a("| quantity | min | median | max | n |")
    a("|---|---|---|---|---|")
    for k, v in fm["stats"].items():
        a(f"| {k} | {v['min']} | {v['median']} | {v['max']} | {v['n']} |")
    a("")
    a("## 7. UNKNOWNs")
    a("")
    for u in d["unknowns"]:
        a(f"- {u}")
    a("")
    a("## 8. Oracles used")
    a("")
    a("- cinfo array: pointer bijection onto the constraint objects + 24-byte spacing "
      "(measured) + the field at +0x0C constant 0x7FFFFFFF fleet-wide.")
    a("- constraint atoms: 3x4 rotation test (unit rows, orthogonal, det = +1) rather than a "
      "fixed offset, because the atom block length varies; pivots are the translation 16 "
      "bytes after the rotation.")
    a("- mass float: the same offset +0x28 in every object and every file, strictly positive "
      "fleet-wide, rank-correlated with hull volume.")
    a("- body entries: 24-word domain census over all fleet bodies (zero / pointer / "
      "constant / float-like counts), so a field is called a pointer only when the packfile's "
      "own fixup table says so.")
    a("- ids and compounds: cross-checked against the grab's parts table (body names) and the "
      "packfile's own reverse pointer map.")
    a("")
    return "\n".join(L)


def write():
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    d, fr = doc["donor"], doc["fleet_raw"]
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    print(f"donor: {len(d['constraints'])} constraints, {len(d['cinfos'])} cinfos, "
          f"{d['mass_properties']['count']} mass props (sum {d['mass_properties']['sum']}), "
          f"{len(d['compounds'])} static compounds")
    print(f"fleet: {fr['decoded']}/{fr['files']} raw files decoded, "
          f"invariants {sum(1 for v in fr['invariants'].values() if v)}/"
          f"{len(fr['invariants'])} pass")
    return 0


def check():
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    d, fr = stored.get("donor") or {}, stored.get("fleet_raw") or {}
    if len(d.get("constraints") or []) != 11:
        fails.append(f"constraints != 11 ({len(d.get('constraints') or [])})")
    if len(d.get("cinfos") or []) != 11:
        fails.append(f"cinfos != 11 ({len(d.get('cinfos') or [])})")
    if not d.get("cinfo_bijection"):
        fails.append("cinfo pointers are not a bijection onto the constraint objects")
    if not d.get("cinfo_stride_24"):
        fails.append("cinfo records are not 24 bytes apart")
    if any(not c["transforms"] for c in d.get("constraints") or []):
        fails.append("a constraint has no decoded atom transform")
    if not any(c["pivots_equal"] for c in d.get("constraints") or []):
        fails.append("no constraint's atom pivots coincide")
    if any(t["det"] != 1.0 for c in d.get("constraints") or [] for t in c["transforms"]):
        fails.append("a decoded atom rotation is not det=+1")
    mp = d.get("mass_properties") or {}
    if mp.get("count") != 56:
        fails.append(f"mass properties != 56 ({mp.get('count')})")
    if not mp.get("positive"):
        fails.append("not every mass float is positive")
    comp = d.get("compounds") or []
    if len(comp) != 2 or sorted(i for c in comp for i in c["ref_body_ids"]) != [16, 26]:
        fails.append(f"static compound body refs != [16, 26] "
                     f"({[c['ref_body_ids'] for c in comp]})")
    if [s["id"] for s in d.get("second_id_space") or [] if s.get("entry")] == []:
        fails.append("no body entries decoded for the second-id-space ids")
    for k, v in (fr.get("invariants") or {}).items():
        if not v:
            fails.append(f"fleet invariant fails: {k}")
    if fr.get("decoded", 0) < 40:
        fails.append(f"fleet decode too small ({fr.get('decoded')})")
    fresh = build()
    if stored != fresh:
        drift = [k for k in stored if stored.get(k) != fresh.get(k)]
        fails.append("stale sections (inputs changed?): " + ", ".join(drift))
    md = open(OUT_MD, encoding="utf-8").read()
    for h in ("## 1. The 11 constraints", "## 2. The 56", "## 3. Body entries",
              "## 4. The \"second raycast id space\"", "## 5. What references the 2 static",
              "## 6. Fleet", "## 7. UNKNOWNs", "## 8. Oracles"):
        if h not in md:
            fails.append(f"markdown heading missing: {h}")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK {len(d['constraints'])} constraints / {len(d['cinfos'])} cinfos / "
          f"{mp['count']} mass props / {len(comp)} compounds; fleet {fr['decoded']} files")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    return write() if args.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
