#!/usr/bin/env python3
"""grab_collision_boxes.py - decode the BOX elements of BmAK RB_BodySetup (G3-01b open item).

`grab_collision_geom.py` (G3-01b) read each box's centre as "the 12 bytes before the tag stream"
and marked the rotation and the extra tag at 0x4C (type 3) UNKNOWN.  `grab_physics.py` (PHY-1)
described the 64 bytes as "FMatrix, identity rotation, translation in the last row".  This tool
decodes the whole box record - every byte, not a rule of thumb - for

    BmGame.upk  RB_BodySetup 169750  bone Batmobile_Chassis            (2 boxes)
    BmGame.upk  RB_BodySetup 169751  bone Batmobile_Rig_Weapons_Trans  (1 box)

and, as the fleet oracle, the 128 boxes of the four wreck PhysicsAssets
(`Playable_Batmobile*.upk`, 32 per package).  It writes:

    Research/BatmobileGrab/COLLISION_BOXES.json
    Research/BatmobileGrab/COLLISION_BOXES.md

THE BOX RECORD, AS THE BYTES PROVE IT (AggGeom payload, after `u32 sphere_count`,
`u32 box_count`, once per box):

    20 B  property tag: u16 type=10 (StructProperty), u16 offset=0, i32 name_index,
          i32 number=0, i32 size=64, i32 array_index=0
    64 B  TM value: 16 floats.  The three floats at 4*nam i+1..i+3 (i = 0..2) form a 3x3,
          the last three floats (13..15) are the translation
     8 B  u16 type=4 (FloatProperty), u16 offset=0x40, f32   Extent X
     8 B  u16 type=4,               u16 offset=0x44, f32     Extent Y
     8 B  u16 type=4,               u16 offset=0x48, f32     Extent Z
     8 B  u16 type=3 (BoolProperty),u16 offset=0x4C, u32     packed bool word
     2 B  u16 type=0 (end of the element's tag list)

Why that is proven and not guessed (see the `oracles` block of the JSON):

  * the StructProperty tag's own `size` field is 64 and exactly 64 bytes follow it before the
    next tag, and its `name_index` resolves to the string `TM` in both packages
    (BmGame.upk name 78655, Playable_Batmobile_SF.upk name 2846);
  * the 3x3 taken from floats 4i+1..4i+3 is orthonormal with det = +1 for all 131 boxes
    (max deviation reported); the alternative reading (floats 4i..4i+2) is singular on the
    128 identity boxes, so it is rejected by the same test;
  * the translation floats 13..15 are byte-identical to the "12 bytes before the tag stream"
    the earlier tools read as the centre, so the old value is confirmed, not replaced;
  * the two bodies' AggGeom payloads are parsed to the last byte (header, boxes, a zero
    element count, the convex section, a 9-byte zero footer) - nothing is skipped;
  * extents are FULL lengths, tested against the union of the drivable collision hull's decoded
    element boxes (COLLISION_CONVEX.json, where ElemBox == vertex bounds on 56/56 elements):
    full lengths give spans that match the hull, half lengths would make the car 13.8 m long.

Labels: decoded = read from bytes (package + export + byte offset); derived = computed from
decoded values with the rule stated; UNKNOWN = not decoded, with what was tried and where it
would be found.

Read-only on the game install.  Writes only its two outputs.

Usage:
    uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_boxes.py --write
    uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_boxes.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U                          # noqa: E402
from grab_collision_geom import agg_of        # noqa: E402  (same AggGeom walker as G3-01b)
from grab_collision_convex import (           # noqa: E402  (G3-01c's proven convex layout)
    parse_element, box_check, TRAILER_BYTES)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
CONVEX_JSON = os.path.join(OUT, "COLLISION_CONVEX.json")

BODIES = [
    {"export": 169750, "bone": "Batmobile_Chassis", "boxes": 2},
    {"export": 169751, "bone": "Batmobile_Rig_Weapons_Trans", "boxes": 1},
]
WRECK = ["Playable_Batmobile_SF", "Playable_BatmobileMK2_SF",
         "Playable_BatmobileJoker_SF", "Playable_BatmobileFunhouse_SF"]

TM_STRUCT_SIZE = 64
TAG_STRUCT = 10
TAG_FLOAT = 4
TAG_BOOL = 3
TAG_END = 0
ORTHO_TOL = 1e-3
# The extents test: compare the box spans with the union of the drivable collision hull's
# element boxes (COLLISION_CONVEX.json).  A physics box hugs the hull; half lengths would be
# exactly twice it.  "decided" needs the winning reading within 30% on every axis and the losing
# reading at least 1.6x worse; anything else is reported as undecided rather than assumed.
EXTENT_TOL = 0.30
EXTENT_SEPARATION = 1.6
# Containment: how far a decoded box may leave the hull's AABB and still count as "inside".
CONTAIN_CM = 30.0


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


def transpose_read(floats):
    """Reading A: rows from floats 4i+1..4i+3, translation = floats 13..15."""
    rows = [[floats[4 * i + 1 + j] for j in range(3)] for i in range(3)]
    lead = [floats[4 * i] for i in range(4)]
    return {"rows": rows, "translation": list(floats[13:16]), "quad_leads": lead}


def planar_read(floats):
    """Reading B (the rejected one): rows from floats 4i..4i+2, translation = floats 12..14."""
    rows = [[floats[4 * i + j] for j in range(3)] for i in range(3)]
    return {"rows": rows, "translation": list(floats[12:15])}


def ortho(rows, translation):
    norms = [math.sqrt(sum(x * x for x in r)) for r in rows]
    dots = [sum(rows[0][i] * rows[1][i] for i in range(3)),
            sum(rows[0][i] * rows[2][i] for i in range(3)),
            sum(rows[1][i] * rows[2][i] for i in range(3))]
    det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
           - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
           + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
    max_norm_err = max(abs(n - 1.0) for n in norms)
    max_dot = max(abs(d) for d in dots)
    ok = max_norm_err <= ORTHO_TOL and max_dot <= ORTHO_TOL and abs(det - 1.0) <= ORTHO_TOL
    return {"row_norms": [round(n, 6) for n in norms],
            "pairwise_dots": [round(d, 7) for d in dots],
            "det": round(det, 7),
            "max_norm_error": max_norm_err,
            "max_abs_dot": max_dot,
            "is_rotation": ok,
            "translation_cm": [round(v, 4) for v in translation]}


def axis_angle(rows):
    """Derived: angle of the 3x3 (same for R and R^T) and the axis it is nearest to."""
    cos = max(-1.0, min(1.0, (rows[0][0] + rows[1][1] + rows[2][2] - 1.0) / 2.0))
    ang = math.degrees(math.acos(cos))
    # axis of a rotation matrix: (R - R^T) / 2 sin
    if ang < 1e-6:
        return {"angle_deg": 0.0, "axis": None,
                "label": "derived: trace formula on the decoded 3x3; degenerate axis undefined"}
    s = 2.0 * math.sin(math.radians(ang))
    ax = [(rows[2][1] - rows[1][2]) / s, (rows[0][2] - rows[2][0]) / s,
          (rows[1][0] - rows[0][1]) / s]
    names = "XYZ"
    k = max(range(3), key=lambda i: abs(ax[i]))
    return {"angle_deg": round(ang, 4),
            "axis_vector": [round(v, 6) for v in ax],
            "axis_label": names[k] if ax[k] > 0 else "-" + names[k],
            "sign_conditional": True,
            "label": "derived: axis and angle from the decoded 3x3 (geometric axis; R vs R^T "
                     "is not decidable from one matrix, so the sign of the angle is conditional)"}


def parse_box(payload, p, names):
    """Decode one box element at `p`.  Returns (record, next offset, error or None)."""
    start = p
    typ, off = struct.unpack_from("<hH", payload, p)
    name_idx, number, size, arr = struct.unpack_from("<iiii", payload, p + 4)
    tag = {"at": p, "type": typ, "offset": off, "name_index": name_idx,
           "name": names[name_idx] if 0 <= name_idx < len(names) else None,
           "number": number, "size": size, "array_index": arr}
    if typ != TAG_STRUCT or off != 0 or size != TM_STRUCT_SIZE:
        return None, p, "box element does not start with a StructProperty tag of size 64 " \
                        "(type %d, offset %#x, size %d) at byte %d" % (typ, off, size, p)
    tm_at = p + 20
    if tm_at + TM_STRUCT_SIZE > len(payload):
        return None, p, "TM value overruns the payload at byte %d" % tm_at
    floats = [f32(payload, tm_at + 4 * i) for i in range(16)]
    p = tm_at + TM_STRUCT_SIZE

    tags, err = [], None
    while True:
        if p + 4 > len(payload):
            err = "tag list overruns the payload at byte %d" % p
            break
        t, o = struct.unpack_from("<hH", payload, p)
        if t == TAG_END:
            tags.append({"at": p, "type": TAG_END, "offset": o, "kind": "end", "bytes": 2})
            p += 2
            break
        if t == TAG_FLOAT:
            v = f32(payload, p + 4)
            tags.append({"at": p, "type": t, "offset": o, "kind": "float", "value": v,
                         "bytes": 8})
            p += 8
            continue
        if t == TAG_BOOL:
            w = u32(payload, p + 4)
            tags.append({"at": p, "type": t, "offset": o, "kind": "bool", "word": w,
                         "bytes": 8})
            p += 8
            continue
        err = "unexpected tag type %d at offset %#x (byte %d) inside the box element" % (t, o, p)
        break
    if err:
        return None, start, err

    ext = {t["offset"]: t["value"] for t in tags if t["kind"] == "float"}
    bools = [t for t in tags if t["kind"] == "bool"]
    ready = [floats[4 * i] for i in range(4)]
    rec = {
        "index": None,
        "start": start,
        "end": p,
        "bytes": p - start,
        "tm_tag": tag,
        "tm_at": tm_at,
        "tm_float_offsets": [tm_at + 4 * i for i in range(16)],
        "tm_floats": [round(v, 6) for v in floats],
        "tm_quad_leads": [round(v, 6) for v in ready],
        "readings": {
            "A_planes_lead_first": dict(transpose_read(floats),
                                        oracle=ortho(transpose_read(floats)["rows"],
                                                     floats[13:16])),
            "B_planes_xyz_first": dict(planar_read(floats),
                                       oracle=ortho(planar_read(floats)["rows"],
                                                    floats[12:15])),
        },
        "extent_tags": tags,
        "extents_cm": [round(ext.get(0x40, float("nan")), 4),
                       round(ext.get(0x44, float("nan")), 4),
                       round(ext.get(0x48, float("nan")), 4)],
        "extent_offsets_present": sorted(ext),
        "bool_tag": bools[0] if bools else None,
        "bool_word": bools[0]["word"] if bools else None,
        "bool_bits_set": [i for i in range(32) if bools and (bools[0]["word"] >> i) & 1]
                         if bools else None,
        "labels": {
            "tm_tag": "decoded (StructProperty tag at byte %d: name_index %d = `%s`, size %d)"
                      % (tag["at"], name_idx, tag["name"], size),
            "tm_floats": "decoded (16 floats from byte %d, raw 64-byte payload)" % tm_at,
            "extents": "decoded (FloatProperty tags at logical offsets 0x40/0x44/0x48)",
            "bool": "decoded (BoolProperty tag at logical offset 0x4C; payload is the packed "
                    "32-bit bool word, so the value is a bit mask, not a 0/1 flag)",
        },
    }
    a = rec["readings"]["A_planes_lead_first"]
    rec["rotation"] = {
        "rows": [[round(v, 6) for v in r] for r in a["rows"]],
        "translation_cm": a["oracle"]["translation_cm"],
        "oracle": a["oracle"],
        "axis_angle": axis_angle(a["rows"]),
        "label": "decoded (reading A, proven below by the orthonormality oracle); the "
                 "translation is the same 12 bytes the earlier tools read as the centre",
    }
    return rec, p, None


def byte_map(payload, boxes, tail, convex):
    """Every byte of the AggGeom payload as records: (offset, size, kind, label)."""
    rows = [{"offset": 0, "size": 4, "kind": "sphere_count", "value": u32(payload, 0),
             "label": "decoded (u32; 0 spheres in both bodies)"},
            {"offset": 4, "size": 4, "kind": "box_count", "value": u32(payload, 4),
             "label": "decoded (u32; equals the number of box elements decoded)"}]
    for b in boxes:
        rows.append({"offset": b["start"], "size": 20, "kind": "tm_struct_tag",
                     "label": "decoded StructProperty tag, name `TM`, size 64"})
        rows.append({"offset": b["start"] + 20, "size": 64, "kind": "tm",
                     "label": "decoded TM (16 floats: 3x3 + translation)"})
        for t in b["extent_tags"]:
            if t["kind"] == "end":
                rows.append({"offset": t["at"], "size": 2, "kind": "element_end",
                             "label": "decoded end-of-tag-list marker (type 0)"})
            elif t["kind"] == "float":
                rows.append({"offset": t["at"], "size": 8, "kind": "extent_float",
                             "logical_offset": t["offset"], "value": round(t["value"], 4),
                             "label": "decoded FloatProperty at logical offset %#x" % t["offset"]})
            else:
                rows.append({"offset": t["at"], "size": 8, "kind": "bool_word",
                             "logical_offset": t["offset"], "value": t["word"],
                             "label": "decoded BoolProperty at logical offset %#x (packed word)"
                                      % t["offset"]})
    rows.extend(tail)
    rows.extend(convex)
    return rows


def convex_records(payload, start, count):
    """Byte map + decoded numbers for the convex section that follows the boxes."""
    rows = [{"offset": start, "size": 4, "kind": "sphyl_or_third_count",
             "value": u32(payload, start),
             "label": "decoded u32, 0 in both bodies; which element type it counts is UNKNOWN "
                      "(no such element exists in any decoded body to test the order against)"}]
    p = start + 4
    rows.append({"offset": p, "size": 4, "kind": "convex_count", "value": u32(payload, p),
                 "label": "decoded u32; equals the number of elements that follow and that "
                          "consume the payload to its footer (byte accounting oracle)"})
    p += 4
    elements = []
    for k in range(count):
        e = parse_element(payload, p)
        bc = box_check(e["vertices_cm"], e["box"])
        elements.append({"index": k, "start": e["start"], "end": e["end"],
                         "bytes": e["end"] - e["start"], "n_vertices": e["nV"],
                         "n_permuted": e["nP"], "n_indices": e["nI"], "n_edge_vectors": e["nE"],
                         "n_face_vectors": e["nX"], "n_planes": e["nY"],
                         "n_edge_records": e["nZ"],
                         "box_min_cm": bc["box_min_cm"], "box_max_cm": bc["box_max_cm"],
                         "box_vs_vertex_bounds": bc, "trailer_hex": e["trailer"]})
        # sub-offsets for the byte map, recomputed here and cross-checked against parse_element
        q = e["start"]
        seq = [("convex_nV", 4)]
        q += 4
        seq.append(("convex_vertices", 12 * e["nV"]))
        q += 12 * e["nV"]
        seq.append(("convex_nP", 4))
        q += 4
        seq.append(("convex_permuted", 16 * e["nP"]))
        q += 16 * e["nP"]
        seq.append(("convex_nI", 4))
        q += 4
        seq.append(("convex_indices", 4 * e["nI"]))
        q += 4 * e["nI"]
        seq.append(("convex_nE", 4))
        q += 4
        seq.append(("convex_edge_vectors", 12 * e["nE"]))
        q += 12 * e["nE"]
        seq.append(("convex_nX", 4))
        q += 4
        seq.append(("convex_face_vectors", 12 * e["nX"]))
        q += 12 * e["nX"]
        seq.append(("convex_nY", 4))
        q += 4
        seq.append(("convex_planes", 16 * e["nY"]))
        q += 16 * e["nY"]
        seq.append(("convex_nZ", 4))
        q += 4
        seq.append(("convex_edge_records", 4 * e["nZ"]))
        q += 4 * e["nZ"]
        seq.append(("convex_elem_box", 24))
        q += 24
        seq.append(("convex_trailer", TRAILER_BYTES))
        q += TRAILER_BYTES
        assert q == e["end"], "convex sub-offsets do not add up to parse_element's end"
        off = e["start"]
        for kind, size in seq:
            rows.append({"offset": off, "size": size, "kind": kind,
                         "label": "decoded (%s of G3-01c's proven layout)" % kind})
            off += size
        p = e["end"]
    return rows, elements, p


def decode_body(pkg, names, spec, convex_ref):
    payload, size, tags = agg_of(pkg, spec["export"])
    bone = [t.get("value") for t in tags if t.get("type") == "NameProperty"]
    rec = {"export": spec["export"], "object": pkg.object_path(spec["export"]),
           "bone": bone[0] if bone else None, "bone_expected": spec["bone"],
           "export_size": size, "aggeom_bytes": len(payload)}
    p = 8
    nbox = u32(payload, 4)
    boxes, errs = [], []
    for k in range(nbox):
        b, p2, err = parse_box(payload, p, names)
        if err:
            errs.append({"box": k, "at": p, "error": err})
            break
        b["index"] = k
        # translation cross-check: the earlier tools' rule, re-read from the tag position
        tag_at = b["start"] + 20 + TM_STRUCT_SIZE
        before = [f32(payload, tag_at - 12 + 4 * i) for i in range(3)]
        b["translation_vs_previous_rule"] = {
            "rule": "12 bytes before the first element tag (grab_physics / grab_collision_geom)",
            "values_cm": [round(v, 6) for v in before],
            "agrees": all(abs(before[i] - b["tm_floats"][13 + i]) < 1e-4 for i in range(3)),
            "label": "decoded (both reads are the same 12 bytes; the old centre value stands)",
        }
        boxes.append(b)
        p = p2
    rec["boxes"] = boxes
    rec["errors"] = errs
    rec["box_count_header"] = nbox
    rec["sphere_count"] = u32(payload, 0)
    rec["box_count_matches"] = (len(boxes) == nbox and nbox == spec["boxes"])

    # what follows the boxes
    convex_count = None
    convex_elements = []
    tail_rows, convex_rows = [], []
    if not errs:
        sphyl_at = p
        hint = u32(payload, sphyl_at) if sphyl_at + 4 <= len(payload) else None
        if hint == 0:
            cc = u32(payload, sphyl_at + 4)
            convex_count = cc
            convex_rows, convex_elements, p2 = convex_records(payload, sphyl_at, cc)
            tail_rows = [r for r in convex_rows[:2]]
            convex_rows = convex_rows[2:]
            p = p2
        else:
            rec["post_box_note"] = ("UNKNOWN after the boxes: byte %d holds %s, not the 0 the "
                                    "other bodies carry" % (sphyl_at, hint))
    rec["convex_count"] = convex_count
    rec["convex_elements"] = convex_elements
    footer = payload[p:]
    rec["footer"] = {"at": p, "bytes": len(footer), "hex": footer.hex(),
                     "all_zero": not any(footer),
                     "label": "decoded: the bytes left after the last element (G3-01c found the "
                              "same 9-byte zero footer in 169748/169749)"}
    rec["byte_map"] = byte_map(payload, boxes, tail_rows, convex_rows) + \
        [{"offset": p, "size": len(footer), "kind": "footer", "label": "decoded zero footer"}]
    rec["accounting"] = {
        "payload_bytes": len(payload),
        "mapped_bytes": sum(r["size"] for r in rec["byte_map"]),
        "exact": sum(r["size"] for r in rec["byte_map"]) == len(payload),
        "boxes_end": boxes[-1]["end"] if boxes else None,
        "convex_ends": p,
        "footer_bytes": len(footer),
        "label": "derived: the byte map's sizes sum to the declared AggGeom size, with no gap "
                 "and no overlap (offsets are consecutive by construction and checked below)",
    }
    rec["box_offsets_reference"] = convex_ref
    return rec


def wreck_boxes(pkg, names):
    """All box elements of a wreck PhysicsAsset's RB_BodySetups (1 box each)."""
    out = []
    for i in range(1, len(pkg.exports) + 1):
        if (pkg.object_class(i) or "") != "RB_BodySetup":
            continue
        payload, size, tags = agg_of(pkg, i)
        if payload is None or len(payload) < 8 or u32(payload, 4) != 1:
            continue
        bone = [t.get("value") for t in tags if t.get("type") == "NameProperty"]
        b, _p, err = parse_box(payload, 8, names)
        if err:
            out.append({"export": i, "bone": bone[0] if bone else None, "error": err})
            continue
        ora = b["readings"]["A_planes_lead_first"]["oracle"]
        out.append({"export": i, "bone": bone[0] if bone else None,
                    "tm_name": b["tm_tag"]["name"],
                    "extents_cm": b["extents_cm"],
                    "translation_cm": b["readings"]["A_planes_lead_first"]["translation"],
                    "rotation_is_identity": ora["is_rotation"] and
                    abs(b["rotation"]["axis_angle"]["angle_deg"]) < 1e-6,
                    "reading_A": {"is_rotation": ora["is_rotation"],
                                  "max_norm_error": ora["max_norm_error"],
                                  "max_abs_dot": ora["max_abs_dot"]},
                    "reading_B_is_rotation": b["readings"]["B_planes_xyz_first"]["oracle"][
                        "is_rotation"],
                    "det": round(ora["det"], 7),
                    "bool_word": b["bool_word"], "bytes": b["bytes"]})
    return out


def obb_corners(rows, t, ext):
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                pts.append([t[k] + sx * ext[0] * rows[0][k] + sy * ext[1] * rows[1][k]
                            + sz * ext[2] * rows[2][k] for k in range(3)])
    return pts


def union(rows_extents, scale):
    """`scale` turns the stored float into the box's HALF size: 0.5 = full lengths, 1 = half."""
    mn = [float("inf")] * 3
    mx = [float("-inf")] * 3
    for rows, t, ext in rows_extents:
        for pt in obb_corners(rows, t, [e * scale for e in ext]):
            for k in range(3):
                mn[k] = min(mn[k], pt[k])
                mx[k] = max(mx[k], pt[k])
    return mn, mx


def load_hull():
    if not os.path.isfile(CONVEX_JSON):
        return None
    doc = json.load(open(CONVEX_JSON, encoding="utf-8"))
    out = {}
    for b in doc.get("bodies", []):
        u = b.get("union_box")
        if u:
            out[str(b["export"])] = {"min_cm": u["min_cm"], "max_cm": u["max_cm"],
                                     "extent_cm": u["extent_cm"],
                                     "elements": len(b.get("elements", []))}
    return out or None


def extents_oracle(bodies, wreck_packages):
    hull = load_hull()
    res = {"hull_source": CONVEX_JSON if hull else None,
           "rule": "derived: compare sorted spans (frame-agnostic) of the chassis box with the "
                   "union of the drivable collision hull's decoded element boxes. Full lengths "
                   "hug the hull (ratio ~1); half lengths would be twice it.",
           "tolerance": EXTENT_TOL, "separation": EXTENT_SEPARATION}
    if not hull:
        res["verdict"] = "UNKNOWN"
        res["reason"] = "COLLISION_CONVEX.json not present, so the hull union is not available."
        return res
    chassis = [b for b in bodies if b["bone"] == "Batmobile_Chassis"]
    if not chassis or not chassis[0]["boxes"]:
        res["verdict"] = "UNKNOWN"
        res["reason"] = "no chassis box decoded"
        return res
    box = chassis[0]["boxes"][0]
    ext = box["extents_cm"]
    rows = box["rotation"]["rows"]
    t = box["rotation"]["translation_cm"]
    res["chassis_box0"] = {"extents_cm": ext, "translation_cm": t,
                           "span_full_m": [round(e / 100.0, 3) for e in ext],
                           "span_half_m": [round(2 * e / 100.0, 3) for e in ext]}
    res["hull_union"] = hull
    rows_ext = [(rows, t, ext)]

    # wreck union, both conventions, as a second, independent car-sized invariant
    wreck = []
    for name, rows_ in wreck_packages.items():
        for b in rows_:
            if "error" in b:
                continue
            wreck.append(([[1, 0, 0], [0, 1, 0], [0, 0, 1]], b["translation_cm"],
                          b["extents_cm"]))
    wreck_res = {}
    if wreck:
        # the stored float is read as a full side length (half size = e/2) or as a half size
        mn_f, mx_f = union(wreck, 0.5)
        mn_h, mx_h = union(wreck, 1.0)
        wreck_res = {
            "boxes": len(wreck),
            "union_full_cm": {"min": [round(v, 2) for v in mn_f],
                              "max": [round(v, 2) for v in mx_f],
                              "extent": [round(mx_f[i] - mn_f[i], 2) for i in range(3)]},
            "union_half_cm": {"min": [round(v, 2) for v in mn_h],
                              "max": [round(v, 2) for v in mx_h],
                              "extent": [round(mx_h[i] - mn_h[i], 2) for i in range(3)]},
            "label": "derived: corners of every wreck box (identity rotation) at translation "
                     "+/- e/2 (full lengths) and +/- e (half lengths)",
        }
    res["wreck_union"] = wreck_res

    def dev_of(box_span, hull_span):
        ratios = [hull_span[i] / box_span[i] if box_span[i] else float("inf") for i in range(3)]
        return round(max(abs(r - 1.0) for r in ratios), 3), [round(r, 3) for r in ratios]

    tests = []
    for export, h in hull.items():
        hspan = sorted(h["extent_cm"])
        for conv, scale in (("full", 0.5), ("half", 1.0)):
            bspan = sorted(e * scale * 2 for e in ext)
            dev, ratios = dev_of(bspan, hspan)
            over, per_axis = 0.0, []
            for i in range(3):
                lo, hi = t[i] - ext[i] * scale, t[i] + ext[i] * scale
                overhang = max(0.0, h["min_cm"][i] - lo, hi - h["max_cm"][i])
                per_axis.append({"axis": "XYZ"[i],
                                 "box_interval_cm": [round(lo, 2), round(hi, 2)],
                                 "hull_interval_cm": [round(h["min_cm"][i], 2),
                                                      round(h["max_cm"][i], 2)],
                                 "overhang_cm": round(overhang, 2)})
                over = max(over, overhang)
            tests.append({"hull_export": export, "convention": conv,
                          "hull_sorted_span_cm": [round(v, 2) for v in hspan],
                          "box_sorted_span_cm": [round(v, 2) for v in bspan],
                          "ratios": ratios, "max_abs_dev_from_1": dev,
                          "max_overhang_cm": round(over, 2), "intervals": per_axis})
    res["tests"] = tests
    full = [x for x in tests if x["convention"] == "full"]
    half = [x for x in tests if x["convention"] == "half"]
    tight = min(full, key=lambda x: x["max_abs_dev_from_1"])
    tight_half = [x for x in half if x["hull_export"] == tight["hull_export"]][0]
    res["tight_hull"] = tight["hull_export"]
    res["dev_full"] = tight["max_abs_dev_from_1"]
    res["dev_half"] = tight_half["max_abs_dev_from_1"]
    res["overhang_full_cm"] = tight["max_overhang_cm"]
    res["overhang_half_cm"] = tight_half["max_overhang_cm"]

    wk = {}
    if wreck:
        hspan = sorted(hull[tight["hull_export"]]["extent_cm"])
        for conv, key in (("full", "union_full_cm"), ("half", "union_half_cm")):
            bspan = sorted(wreck_res[key]["extent"])
            dev, ratios = dev_of(bspan, hspan)
            wk[conv] = {"box_sorted_span_cm": [round(v, 2) for v in bspan],
                        "ratios": ratios, "max_abs_dev_from_1": dev}
    res["wreck_test"] = wk

    # containment: does each decoded box sit inside the tight hull's own AABB?
    ht = hull[tight["hull_export"]]
    contain = {}
    for conv, scale in (("full", 0.5), ("half", 1.0)):
        worst, rows_c = 0.0, []
        for body in bodies:
            for b in body["boxes"]:
                ext_, t_ = b["extents_cm"], b["rotation"]["translation_cm"]
                per = []
                for i in range(3):
                    lo, hi = t_[i] - ext_[i] * scale, t_[i] + ext_[i] * scale
                    ov = max(0.0, ht["min_cm"][i] - lo, hi - ht["max_cm"][i])
                    per.append({"axis": "XYZ"[i],
                                "box_interval_cm": [round(lo, 2), round(hi, 2)],
                                "hull_interval_cm": [round(ht["min_cm"][i], 2),
                                                     round(ht["max_cm"][i], 2)],
                                "overhang_cm": round(ov, 2)})
                    worst = max(worst, ov)
                rows_c.append({"export": body["export"], "bone": body["bone"],
                               "box": b["index"], "intervals": per,
                               "max_overhang_cm": round(max(x["overhang_cm"]
                                                            for x in per), 2)})
        hmax = max(ht["extent_cm"])
        contain[conv] = {"boxes": rows_c, "max_overhang_cm": round(worst, 2),
                         "hull_max_span_cm": round(hmax, 2),
                         "overhang_fraction_of_hull_max_span": round(worst / hmax, 3)}
    res["containment"] = contain

    cond = {
        "chassis_span_within_%.0f%%_of_the_tight_hull" % (EXTENT_TOL * 100):
            res["dev_full"] <= EXTENT_TOL,
        "half_span_reading_at_least_%.1fx_worse" % EXTENT_SEPARATION:
            res["dev_half"] >= EXTENT_SEPARATION * max(res["dev_full"], 1e-6),
        "every_box_inside_the_hull_at_full_length_(<=%.0f_cm)" % CONTAIN_CM:
            contain["full"]["max_overhang_cm"] <= CONTAIN_CM,
        "the_half_reading_leaves_it_by_at_least_3x_that":
            contain["half"]["max_overhang_cm"]
            >= 3.0 * max(contain["full"]["max_overhang_cm"], 1e-6),
    }
    res["conditions"] = cond
    if all(cond.values()):
        res["verdict"] = "FULL lengths"
        res["reason"] = (
            "against the tight hull (%s) the full-length spans are within %.0f%% on every axis "
            "(worst %.3f) while the half-length reading is %.1fx worse (%.3f), and at full "
            "length every decoded box sits inside that hull's AABB to within %.1f cm (%.1f%% of "
            "the hull's largest span) against %.1f cm for the half-length reading"
            % (tight["hull_export"], EXTENT_TOL * 100, res["dev_full"],
               res["dev_half"] / max(res["dev_full"], 1e-6), res["dev_half"],
               contain["full"]["max_overhang_cm"],
               100 * contain["full"]["overhang_fraction_of_hull_max_span"],
               contain["half"]["max_overhang_cm"]))
    elif res["dev_half"] <= EXTENT_TOL and contain["half"]["max_overhang_cm"] <= CONTAIN_CM:
        res["verdict"] = "HALF lengths"
        res["reason"] = "the half-length reading is the one that matches the hull and the boxes"
    else:
        res["verdict"] = "UNDECIDED"
        res["reason"] = (
            "worst span deviation full %.3f vs half %.3f (rule: winner within %.2f, loser at "
            "least %.1fx worse) and worst overhang full %.1f cm vs half %.1f cm"
            % (res["dev_full"], res["dev_half"], EXTENT_TOL, EXTENT_SEPARATION,
               contain["full"]["max_overhang_cm"], contain["half"]["max_overhang_cm"]))
    wr_flat = [r for rows_ in wreck_packages.values() for r in rows_ if "error" not in r]
    biggest = max((max(r["extents_cm"]) for r in wr_flat), default=None)
    tspan = [round(max(r["translation_cm"][i] for r in wr_flat)
                   - min(r["translation_cm"][i] for r in wr_flat), 1) for i in range(3)]
    res["wreck_conclusion"] = {
        "union_full_cm": wreck_res["union_full_cm"]["extent"] if wreck_res else None,
        "union_half_cm": wreck_res["union_half_cm"]["extent"] if wreck_res else None,
        "largest_box_axis_cm": biggest,
        "translation_span_cm": tspan,
        "verdict": "does not decide",
        "reason": (
            "read as full lengths the union of the 128 wreck boxes is %s cm and read as half "
            "lengths %s cm, against the intact car's hull %s cm: the half reading is the one that "
            "matches the intact car, the opposite of the chassis-box test. The wreck asset's boxes "
            "are per-bone envelopes of an exploded rig - the largest is %s cm on one axis while "
            "the translations span only %s cm - so the assumption this comparison rests on (that "
            "those boxes tile the intact car) is not proven either way. Recorded; not used in the "
            "verdict."
            % (wreck_res["union_full_cm"]["extent"] if wreck_res else None,
               wreck_res["union_half_cm"]["extent"] if wreck_res else None,
               hull[tight["hull_export"]]["extent_cm"], biggest, tspan)),
    }
    # the hull that is not tight is kept as a finding, not folded into the verdict
    others = [x for x in full if x["hull_export"] != tight["hull_export"]]
    if others:
        other = others[0]
        res["other_hull_finding"] = (
            "the other hull (%s, the battle-mode mesh) has larger sorted spans than chassis box 0 "
            "at full length: %s cm against %s cm (worst deviation %.3f), and the box's intervals "
            "leave it by at most %.1f cm - so the box sits inside that hull. The pursuit hull "
            "(%s) is the closer match. Recorded, not explained."
            % (other["hull_export"], other["hull_sorted_span_cm"],
               other["box_sorted_span_cm"], other["max_abs_dev_from_1"],
               other["max_overhang_cm"], tight["hull_export"]))
    return res


def build():
    pkg = U.Package(os.path.join(GAME, "BmGame.upk"))
    names = pkg.names
    doc = {"card": "G3-01b (open item: box rotations, the 0x4C tag, every byte of the box record)",
           "generator": "grab_collision_boxes.py",
           "inputs": {"bmgame": os.path.join(GAME, "BmGame.upk"),
                      "bodies": [b["export"] for b in BODIES],
                      "wreck_packages": [os.path.join(GAME, w + ".upk") for w in WRECK],
                      "convex_record": CONVEX_JSON}}

    convex_ref = None
    if os.path.isfile(CONVEX_JSON):
        cv = json.load(open(CONVEX_JSON, encoding="utf-8"))
        convex_ref = {"bodies": {str(b["export"]): b["aggeom_bytes"] for b in cv["bodies"]},
                      "summary": {k: cv["summary"][k] for k in
                                  ("elements", "elements_by_body", "plane_clean", "box_exact")},
                      "label": "decoded by G3-01c; used here as the hull oracle and for the "
                               "convex section's layout"}

    bodies = [decode_body(pkg, names, spec, convex_ref) for spec in BODIES]
    doc["bodies"] = bodies
    doc["convex_record"] = convex_ref

    # wreck fleet
    wreck_packages, wreck_meta = {}, []
    for w in WRECK:
        path = os.path.join(GAME, w + ".upk")
        if not os.path.exists(path):
            wreck_meta.append({"package": w, "error": "missing"})
            continue
        p = U.Package(path)
        rows = wreck_boxes(p, p.names)
        wreck_packages[w] = rows
        wreck_meta.append({"package": w, "path": path, "boxes": len(rows),
                           "errors": sum(1 for r in rows if "error" in r),
                           "boxes_identity_rotation": sum(1 for r in rows
                                                          if r.get("rotation_is_identity")),
                           "bool_words": sorted({r.get("bool_word") for r in rows
                                                 if "bool_word" in r}),
                           "tm_names": sorted({r.get("tm_name") for r in rows
                                               if "tm_name" in r})})
    doc["wreck"] = {"packages": wreck_meta,
                    "signature": {w: [(r.get("bone"), r.get("extents_cm"),
                                       r.get("translation_cm")) for r in rows if "error" not in r]
                                  for w, rows in wreck_packages.items()},
                    "boxes": {w: rows for w, rows in wreck_packages.items()}}
    sigs = {json.dumps(v) for v in doc["wreck"]["signature"].values()}
    doc["wreck"]["layouts_identical"] = len(sigs) <= 1

    doc["oracles"] = {
        "struct_tag_name": {
            "bmgame": {"name_index": 78655, "name": names[78655] if 78655 < len(names) else None},
            "wreck": {w: {"name_index": 2846,
                          "name": (U.Package(os.path.join(GAME, w + ".upk")).names[2846]
                                   if os.path.exists(os.path.join(GAME, w + ".upk")) else None)}
                      for w in WRECK},
            "label": "decoded: the StructProperty tag's name_index resolves to `TM` in both "
                     "packages, so the 64-byte payload is the box's TM member",
        },
        "orthonormality": None,          # filled below
        "byte_accounting": None,         # filled below
        "extents": extents_oracle(bodies, wreck_packages),
    }

    # orthonormality oracle across every box
    all_boxes = [b for body in bodies for b in body["boxes"]]
    wr_boxes = [r for rows in wreck_packages.values() for r in rows if "error" not in r]
    a_ok = sum(1 for b in all_boxes if b["readings"]["A_planes_lead_first"]["oracle"][
        "is_rotation"]) + sum(1 for r in wr_boxes if r.get("reading_A", {}).get("is_rotation"))
    b_ok = sum(1 for b in all_boxes if b["readings"]["B_planes_xyz_first"]["oracle"][
        "is_rotation"]) + sum(1 for r in wr_boxes if r.get("reading_B_is_rotation"))
    doc["oracles"]["orthonormality"] = {
        "boxes_bmgame": len(all_boxes),
        "boxes_wreck": len(wr_boxes),
        "reading_A_pass": a_ok,
        "reading_B_pass": b_ok,
        "reading_A_worst_norm_error": max(
            [b["readings"]["A_planes_lead_first"]["oracle"]["max_norm_error"] for b in all_boxes]
            + [r.get("reading_A", {}).get("max_norm_error", 0) for r in wr_boxes] or [0]),
        "reading_A_worst_dot": max(
            [b["readings"]["A_planes_lead_first"]["oracle"]["max_abs_dot"] for b in all_boxes]
            + [r.get("reading_A", {}).get("max_abs_dot", 0) for r in wr_boxes] or [0]),
        "reading_A_dets": sorted({round(b["readings"]["A_planes_lead_first"]["oracle"]["det"], 7)
                                  for b in all_boxes}
                                 | {r.get("det") for r in wr_boxes if "det" in r}),
        "quad_lead_values": sorted({round(v, 6) for b in all_boxes
                                    for v in b["tm_quad_leads"]}),
        "label": "derived: rows = floats[4i+1..4i+3] (reading A) give an orthonormal 3x3 with "
                 "det +1 on every box; rows = floats[4i..4i+2] (reading B) do not. The four "
                 "quad-leading floats are 0,0,0,1 in every box, which is the invariant that "
                 "fixes which three floats of each quad are the row.",
    }
    acct = []
    for body in bodies:
        a = body["accounting"]
        offs = [r["offset"] for r in body["byte_map"]]
        ok_offsets = offs == sorted(offs) and offs[0] == 0 and len(set(offs)) == len(offs)
        acct.append({"export": body["export"], "payload_bytes": a["payload_bytes"],
                     "mapped_bytes": a["mapped_bytes"], "exact": a["exact"],
                     "footer_bytes": a["footer_bytes"], "footer_hex": body["footer"]["hex"],
                     "offsets_consecutive": ok_offsets,
                     "boxes": len(body["boxes"]), "convex_elements": len(body["convex_elements"])})
    doc["oracles"]["byte_accounting"] = {
        "rows": acct,
        "label": "derived: header + box elements + zero count + convex section + footer cover "
                 "the declared AggGeom payload exactly, with byte-map records that start at 0 and "
                 "are strictly increasing",
    }

    # 0x4C tag evidence
    bools = []
    for body in bodies:
        for b in body["boxes"]:
            bools.append({"export": body["export"], "bone": body["bone"], "box": b["index"],
                          "tag_at": b["bool_tag"]["at"] if b["bool_tag"] else None,
                          "logical_offset": b["bool_tag"]["offset"] if b["bool_tag"] else None,
                          "word": b["bool_word"], "bits": b["bool_bits_set"]})
    wreck_words = sorted({r.get("bool_word") for r in wr_boxes})
    doc["tag_0x4c"] = {
        "rows": bools,
        "wreck_words": wreck_words,
        "offset_proof": "decoded: the tag's u16 offset field is 0x4C and its 4-byte payload is "
                        "the packed bool word, so the element struct has a bool bitfield word at "
                        "0x4C and its size is 0x50 (80 B: TM 0x00-0x3F, extents 0x40-0x4B, "
                        "word 0x4C-0x4F)",
        "name": "UNKNOWN",
        "name_reason": "the member's name is not stored (simple types carry no FName in this "
                       "format) and no local layout lists it: BMSDK_OFFSETS.json has 41 classes "
                       "(Actor, RVehicle*, SVehicle* ...) and no FKBoxElem/AggGeom struct, so "
                       "which bool bit 6 is cannot be named from local evidence",
        "where_it_would_be_found": "BmSDK-AK's struct dump for the box element (card G3-06, "
                                   "native layouts), or a body where another bit of the same "
                                   "word differs and its effect can be observed",
    }

    # checks
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    check("both bodies decoded (bone matches the card)",
          all(b["bone"] == b["bone_expected"] for b in bodies),
          ", ".join("%d: %s" % (b["export"], b["bone"]) for b in bodies))
    check("the box count in the payload equals the number of box elements decoded",
          all(b["box_count_matches"] for b in bodies),
          ", ".join("%d: header %d, decoded %d" % (b["export"], b["box_count_header"],
                                                   len(b["boxes"])) for b in bodies))
    check("every box starts with a StructProperty tag of size 64 named TM",
          all(b["tm_tag"]["type"] == TAG_STRUCT and b["tm_tag"]["size"] == 64
              and b["tm_tag"]["name"] == "TM" and b["tm_tag"]["offset"] == 0
              for b in all_boxes),
          "%d boxes" % len(all_boxes))
    check("every box's tag list is exactly 0x40/0x44/0x48 floats + 0x4C bool + end",
          all([t["offset"] for t in b["extent_tags"] if t["kind"] == "float"] == [0x40, 0x44, 0x48]
              and [t["offset"] for t in b["extent_tags"] if t["kind"] == "bool"] == [0x4C]
              and b["extent_tags"][-1]["kind"] == "end" for b in all_boxes),
          "%d boxes, extents 0x40/0x44/0x48, bool 0x4C" % len(all_boxes))
    n_all = len(all_boxes) + len(wr_boxes)
    check("reading A gives a proper rotation on every box; reading B does not",
          doc["oracles"]["orthonormality"]["reading_A_pass"] == n_all
          and doc["oracles"]["orthonormality"]["reading_B_pass"] < n_all,
          "A %d/%d, B %d/%d" % (doc["oracles"]["orthonormality"]["reading_A_pass"], n_all,
                                doc["oracles"]["orthonormality"]["reading_B_pass"], n_all))
    check("the wreck's 128 boxes are identity rotations under reading A",
          all(r.get("rotation_is_identity") for r in wr_boxes) and len(wr_boxes) == 128,
          "%d/%d identity, dets %s" % (sum(1 for r in wr_boxes if r.get("rotation_is_identity")),
                                       len(wr_boxes),
                                       sorted({r.get("det") for r in wr_boxes})))
    check("the translation equals the '12 bytes before the tags' the earlier tools read",
          all(b["translation_vs_previous_rule"]["agrees"] for b in all_boxes),
          "%d boxes" % len(all_boxes))
    check("the four quad-leading floats are 0,0,0,1 in every box",
          doc["oracles"]["orthonormality"]["quad_lead_values"] == [0, 1],
          str(doc["oracles"]["orthonormality"]["quad_lead_values"]))
    check("the AggGeom payload is covered byte for byte, with a zero footer",
          all(a["exact"] and a["offsets_consecutive"] and a["footer_bytes"] < 16
              and a["footer_hex"].strip("0") == "" for a in acct),
          "; ".join("%d: %d/%d B, footer %d B" % (a["export"], a["mapped_bytes"],
                                                 a["payload_bytes"], a["footer_bytes"])
                    for a in acct))
    check("the convex element after the boxes satisfies ElemBox == vertex bounds",
          all(e["box_vs_vertex_bounds"]["matches"] for b in bodies
              for e in b["convex_elements"]),
          "; ".join("%d: %d element(s)" % (b["export"], len(b["convex_elements"]))
                    for b in bodies))
    check("the extents convention is decided by the hull oracle",
          doc["oracles"]["extents"]["verdict"] in ("FULL lengths", "HALF lengths"),
          "%s (worst dev full %s, half %s)"
          % (doc["oracles"]["extents"]["verdict"],
             doc["oracles"]["extents"].get("dev_full"),
             doc["oracles"]["extents"].get("dev_half")))
    check("the four wreck packages carry identical box layouts",
          doc["wreck"]["layouts_identical"],
          "%d packages, %d boxes" % (len(wreck_meta), len(wr_boxes)))
    check("every box, in every package, has its TM struct tag named `TM`",
          all(r.get("tm_name") == "TM" for r in wr_boxes)
          and all(b["tm_tag"]["name"] == "TM" for b in all_boxes),
          "wreck TM names %s" % sorted({r.get("tm_name") for r in wr_boxes}))
    check("the 0x4C bool is recorded as a bitmask and its name stays UNKNOWN",
          doc["tag_0x4c"]["name"] == "UNKNOWN" and all(r["bits"] is not None for r in bools),
          "; ".join("%s box %d word %s bits %s" % (r["bone"], r["box"], r["word"], r["bits"])
                    for r in bools))
    doc["checks"] = checks

    doc["summary"] = {
        "bodies": len(bodies),
        "boxes_bmgame": len(all_boxes),
        "boxes_wreck": len(wr_boxes),
        "boxes_total": len(all_boxes) + len(wr_boxes),
        "rotations_decoded": len(all_boxes),
        "rotations_non_identity": sum(1 for b in all_boxes
                                      if b["rotation"]["axis_angle"]["angle_deg"] > 1e-6),
        "extents_convention": doc["oracles"]["extents"]["verdict"],
        "tag_0x4c_words": sorted({r["word"] for r in bools} | set(wreck_words)),
        "unaccounted_bytes": {str(a["export"]): a["payload_bytes"] - a["mapped_bytes"]
                              for a in acct},
        "unknowns": ["the 0x4C bool's member name and meaning",
                     "which element type the zero count before the convex count belongs to",
                     "whether the decoded 3x3 is the transform's rows or its columns "
                     "(the 4.00 deg Y tilt's sign)",
                     "the StaticMesh Bounds as a second extents oracle (not a tag; no layout)"],
    }
    return doc


def fmt(v, n=3):
    out = ("%%.%df" % n) % v
    return out[1:] if out.startswith("-0.") and float(out) == 0 else out


def render(d):
    L = []
    a = L.append
    s = d["summary"]
    a("# COLLISION_BOXES.md - the box records of BmAK `RB_BodySetup` (G3-01b open item)")
    a("")
    a("Generated by `Tools/scripts/grab_collision_boxes.py` (`--write`); `--check` re-derives it")
    a("from the packages and fails on a one-byte difference.")
    a("")
    a("Decoded here: **%d boxes** in `BmGame.upk` (the drivable car's PhysicsAsset) and **%d boxes**"
      % (s["boxes_bmgame"], s["boxes_wreck"]))
    a("in the four wreck PhysicsAssets, used as the fleet oracle. Every byte of the two")
    a("`BmGame.upk` box bodies' AggGeom payloads is mapped, including the rotation and the extra")
    a("tag at 0x4C that G3-01b left UNKNOWN.")
    a("")
    a("Labels: **decoded** = read from bytes (package + export + byte offset); **derived** =")
    a("computed from decoded values with the rule given; **UNKNOWN** = not decoded, with what was")
    a("tried and where it would be found.")
    a("")
    a("## The box record")
    a("")
    a("Inside the AggGeom payload, after `u32 sphere_count` and `u32 box_count`, once per box:")
    a("")
    a("| bytes | content | evidence |")
    a("|---:|---|---|")
    a("| 20 | property tag: `u16 type=10` (StructProperty), `u16 offset=0`, `i32 name_index`, "
      "`i32 number=0`, `i32 size=64`, `i32 array_index=0` | decoded; the name index resolves to "
      "`TM` (BmGame.upk name 78655, Playable_Batmobile_SF.upk name 2846) and `size` is exactly the "
      "64 bytes that follow |")
    a("| 64 | `TM`: 16 floats - a 3x3 (floats `4i+1..4i+3`) and a translation (floats 13..15) | "
      "decoded; the 3x3 is orthonormal with det +1 on all %d boxes (oracle below), and the floats "
      "`4i` are 0,0,0,1 on every box |" % (s["boxes_bmgame"] + s["boxes_wreck"]))
    a("| 8 | `u16 type=4`, `u16 offset=0x40`, `f32` Extent X | decoded FloatProperty tag |")
    a("| 8 | `u16 type=4`, `u16 offset=0x44`, `f32` Extent Y | decoded FloatProperty tag |")
    a("| 8 | `u16 type=4`, `u16 offset=0x48`, `f32` Extent Z | decoded FloatProperty tag |")
    a("| 8 | `u16 type=3` (BoolProperty), `u16 offset=0x4C`, `u32` packed bool word | decoded |")
    a("| 2 | `u16 type=0` - end of the element's tag list | decoded |")
    a("")
    a("So the element struct is 0x50 = 80 bytes (TM 0x00-0x3F, extents 0x40-0x4B, bool word")
    a("0x4C-0x4F), and the tags after the TM are the element's own members, not `RB_BodySetup`")
    a("fields: they sit inside the AggGeom `StructProperty` payload (declared size 1759 /")
    a("143 bytes), which is why their offsets are 0x40/0x44/0x48/0x4C and not the BodySetup's")
    a("0xCD/0xD0/0xEC.")
    a("")
    a("## The rotation, decoded")
    a("")
    o = d["oracles"]["orthonormality"]
    a("Two readings of the 16 floats were tested against the same oracle (a transform's 3x3 must")
    a("be orthonormal with det +1):")
    a("")
    a("| reading | rows taken from | proper rotation on | verdict |")
    a("|---|---|---|---|")
    a("| **A** | floats `4i+1, 4i+2, 4i+3` (i = 0..2), translation = floats 13..15 | "
      "**%d / %d** boxes | **DECODED** |" % (o["reading_A_pass"], s["boxes_total"]))
    a("| B | floats `4i, 4i+1, 4i+2`, translation = floats 12..14 | %d / %d boxes | REJECTED "
      "(singular on the identity boxes) |" % (o["reading_B_pass"], s["boxes_total"]))
    a("")
    a("Reading A's worst row-norm error is %.1e and its worst |row.row| is %.1e over all %d boxes;"
      % (o["reading_A_worst_norm_error"], o["reading_A_worst_dot"], s["boxes_total"]))
    a("its determinants are %s." % o["reading_A_dets"])
    a("")
    a("| export | bone | box | TM rows (decoded) | translation (cm) | axis / angle (derived) |")
    a("|---|---|---:|---|---|---|")
    for body in d["bodies"]:
        for b in body["boxes"]:
            aa = b["rotation"]["axis_angle"]
            rows = "; ".join("(%s)" % ", ".join(fmt(v) for v in r) for r in b["rotation"]["rows"])
            a("| %d | `%s` | %d | %s | (%s) | %s |"
              % (body["export"], body["bone"], b["index"], rows,
                 ", ".join(fmt(v) for v in b["rotation"]["translation_cm"]),
                 ("identity" if aa["angle_deg"] == 0 else
                  "axis (%s), angle ±%s deg (sign conditional: R vs R^T is not decidable from "
                  "one matrix)"
                  % (", ".join(fmt(v) for v in aa["axis_vector"]), fmt(aa["angle_deg"], 2)))))
    a("")
    a("The translation is byte-identical to the 12 bytes before the tag stream that")
    a("`grab_physics.py` read as the centre, so that earlier value is confirmed rather than")
    a("replaced. The 3x3's *geometric* axis and angle are decoded; whether the stored quads are")
    a("the transform's rows or its columns is not decidable from one matrix, so the 4.00 deg Y")
    a("tilt is reported with a conditional sign.")
    a("")
    for body in d["bodies"]:
        a("## Export %d - `%s`, bone `%s`" % (body["export"], body["object"], body["bone"]))
        a("")
        a("AggGeom payload **%d B**, header `sphere_count=%d`, `box_count=%d`; boxes decoded: "
          "**%d**." % (body["aggeom_bytes"], body["sphere_count"],
                       body["box_count_header"], len(body["boxes"])))
        a("")
        a("| box | element bytes | TM tag | extents X/Y/Z (cm) | 0x4C word | bits set |")
        a("|---:|---|---|---|---:|---|")
        for b in body["boxes"]:
            a("| %d | %d..%d (%d B) | type %d, offset 0, name `%s` (index %d), size %d | %s | "
              "`0x%02x` | %s |"
              % (b["index"], b["start"], b["end"] - 1, b["bytes"], b["tm_tag"]["type"],
                 b["tm_tag"]["name"], b["tm_tag"]["name_index"], b["tm_tag"]["size"],
                 " / ".join(fmt(v) for v in b["extents_cm"]), b["bool_word"],
                 b["bool_bits_set"]))
        a("")
        a("Byte map (every byte, in order):")
        a("")
        a("| offset | bytes | kind | detail |")
        a("|---:|---:|---|---|")
        for r in body["byte_map"]:
            extra = ""
            if "logical_offset" in r:
                extra = "offset %#04x, value %s" % (r["logical_offset"], r.get("value"))
            elif "value" in r:
                extra = "value %s" % r["value"]
            a("| %d | %d | %s | %s |" % (r["offset"], r["size"], r["kind"],
                                         (r["label"] + ((" - " + extra) if extra else ""))
                                         .replace("|", "/")))
        a("")
        ac = body["accounting"]
        a("- accounting: %d of %d bytes mapped, exact = %s, footer %d B (`%s`)."
          % (ac["mapped_bytes"], ac["payload_bytes"], ac["exact"], ac["footer_bytes"],
             body["footer"]["hex"]))
        if body["convex_elements"]:
            a("- convex section: %d element(s), %d B; `ElemBox == vertex bounds` %s."
              % (len(body["convex_elements"]),
                 sum(e["bytes"] for e in body["convex_elements"]),
                 "holds on all of them" if all(e["box_vs_vertex_bounds"]["matches"]
                                               for e in body["convex_elements"]) else "FAILS"))
        a("- translation vs the earlier '12 bytes before the tags' rule: %s."
          % ("agrees on every box" if all(b["translation_vs_previous_rule"]["agrees"]
                                          for b in body["boxes"]) else "DISAGREES"))
        a("")

    a("## The extra tag at 0x4C (type 3)")
    a("")
    a("| export | bone | box | tag byte | logical offset | packed word | bits set |")
    a("|---|---|---:|---:|---|---:|---|")
    for r in d["tag_0x4c"]["rows"]:
        a("| %d | `%s` | %d | %s | %#x | `0x%02x` | %s |"
          % (r["export"], r["bone"], r["box"], r["tag_at"], r["logical_offset"], r["word"],
             r["bits"]))
    a("")
    a("Wreck boxes' 0x4C words: %s." % (", ".join("`0x%02x`" % w for w in
                                                  d["tag_0x4c"]["wreck_words"]) or "-"))
    a("")
    a("- %s." % d["tag_0x4c"]["offset_proof"])
    a("- name: **UNKNOWN**. %s." % d["tag_0x4c"]["name_reason"])
    a("- where it would be found: %s." % d["tag_0x4c"]["where_it_would_be_found"])
    a("")
    a("It is decoded as a packed 32-bit bool word at logical offset 0x4C: chassis box 0 has bit 6")
    a("set (word `0x40`), chassis box 1, the weapons box and all 128 wreck boxes have word 0.")
    a("")

    a("## Oracle: are the extents full or half lengths?")
    a("")
    e = d["oracles"]["extents"]
    a("- rule: %s" % e["rule"])
    cr = d.get("convex_record") or {}
    cs = cr.get("summary", {})
    a("- hull source: `COLLISION_CONVEX.json` (G3-01c: %s elements decoded, plane-clean %s, "
      "ElemBox == vertex bounds %s, per body: %s), whose union boxes are a tight hull of the same "
      "car in centimetres."
      % (cs.get("elements"), cs.get("plane_clean"), cs.get("box_exact"),
         cs.get("elements_by_body")))
    a("")
    if "tests" in e:
        a("| hull body | convention | hull sorted span (cm) | box sorted span (cm) | ratios | "
          "max |dev| | max overhang (cm) |")
        a("|---|---|---|---|---|---:|---:|")
        for t_ in e["tests"]:
            a("| %s | %s | %s | %s | %s | %s | %s |"
              % (t_["hull_export"], t_["convention"],
                 ", ".join(fmt(v, 1) for v in t_["hull_sorted_span_cm"]),
                 ", ".join(fmt(v, 1) for v in t_["box_sorted_span_cm"]),
                 ", ".join(fmt(v, 3) for v in t_["ratios"]),
                 fmt(t_["max_abs_dev_from_1"], 3), fmt(t_["max_overhang_cm"], 1)))
        a("")
        a("The tight hull is **%s**; overhang is derived as the largest distance by which a box's "
          "interval leaves the hull's interval on any axis." % e["tight_hull"])
        for conv in ("full", "half"):
            c = e["containment"][conv]
            a("")
            a("Containment, **%s** lengths (half size = e x %s):"
              % (conv, "0.5" if conv == "full" else "1"))
            a("")
            a("| box | axis | box interval (cm) | hull interval (cm) | overhang (cm) |")
            a("|---|---|---|---|---:|")
            for r in c["boxes"]:
                for iv in r["intervals"]:
                    a("| %d `%s` box %d | %s | %s | %s | %s |"
                      % (r["export"], r["bone"], r["box"], iv["axis"],
                         " .. ".join(fmt(v, 1) for v in iv["box_interval_cm"]),
                         " .. ".join(fmt(v, 1) for v in iv["hull_interval_cm"]),
                         fmt(iv["overhang_cm"], 1)))
            a("")
            a("- worst overhang **%s cm** (%.1f%% of the hull's largest span, %s cm)."
              % (fmt(c["max_overhang_cm"], 2),
                 100 * c["overhang_fraction_of_hull_max_span"], fmt(c["hull_max_span_cm"], 1)))
        a("")
        a("| condition | holds |")
        a("|---|---|")
        for k, v in e["conditions"].items():
            a("| %s | %s |" % (k, "yes" if v else "**no**"))
        a("")
        a("- chassis box 0 extents (decoded): %s cm -> spans as full lengths %s m, as half lengths "
          "%s m."
          % (", ".join(fmt(v) for v in e["chassis_box0"]["extents_cm"]),
             ", ".join(fmt(v) for v in e["chassis_box0"]["span_full_m"]),
             ", ".join(fmt(v) for v in e["chassis_box0"]["span_half_m"])))
    a("- **verdict: %s.** %s" % (e["verdict"], e.get("reason", "")))
    if e.get("other_hull_finding"):
        a("- finding: %s" % e["other_hull_finding"])
    wc = e.get("wreck_conclusion")
    if wc:
        w = e["wreck_union"]
        a("")
        a("### The wreck boxes do not decide it")
        a("")
        a("The 128 wreck boxes use the same element struct (identity rotation), so their union was")
        a("tested as a second, independent size check against the intact car's hull:")
        a("")
        a("- %d boxes; union of their corners read as **full** lengths: %s cm."
          % (w["boxes"], ", ".join(fmt(v, 1) for v in w["union_full_cm"]["extent"])))
        a("- the same union read as **half** lengths: %s cm."
          % ", ".join(fmt(v, 1) for v in w["union_half_cm"]["extent"]))
        a("- deviation from the tight hull's sorted spans: full %s (ratios %s), half %s "
          "(ratios %s)."
          % (fmt(e["wreck_test"]["full"]["max_abs_dev_from_1"], 3),
             ", ".join(fmt(v, 3) for v in e["wreck_test"]["full"]["ratios"]),
             fmt(e["wreck_test"]["half"]["max_abs_dev_from_1"], 3),
             ", ".join(fmt(v, 3) for v in e["wreck_test"]["half"]["ratios"])))
        a("- **this comparison does not decide it.** %s" % wc["reason"])
    a("")

    a("## Fleet: the wreck boxes (oracle for the same struct)")
    a("")
    a("| package | boxes | identity rotation | 0x4C words | TM name |")
    a("|---|---:|---:|---|---|")
    for m in d["wreck"]["packages"]:
        if "error" in m:
            a("| `%s` | - | - | - | - |" % m["package"])
            continue
        a("| `%s` | %d | %d | %s | `%s` |"
          % (m["package"], m["boxes"], m["boxes_identity_rotation"],
             ", ".join("0x%02x" % w for w in m["bool_words"]),
             ", ".join(m.get("tm_names") or [])))
    a("")
    a("All %d wreck boxes are single-box bodies with an identity 3x3, so they pin the layout"
      % d["summary"]["boxes_wreck"])
    a("(any mis-assigned float would break orthonormality or the det) and the four packages carry")
    a("%s layouts." % ("identical" if d["wreck"]["layouts_identical"] else "DIFFERING"))
    a("")

    a("## UNKNOWN")
    a("")
    a("| # | unknown | what was tried | where it would be found |")
    a("|---|---|---|---|")
    for i, u in enumerate(d["summary"]["unknowns"], 1):
        tried = {
            "the 0x4C bool's member name and meaning":
                "decoded the tag (type 3, offset 0x4C, 4-byte packed word) and every box's word; "
                "searched BMSDK_OFFSETS.json's 41 classes for a box/aggregate struct and found "
                "none, so no local layout names the bit",
            "which element type the zero count before the convex count belongs to":
                "decoded the word (0 in both bodies) and the convex count after it (0 and 1, and "
                "the 1's single element consumes the payload to the footer); no sphere or sphyl "
                "element exists in any body decoded here to test the type order",
            "whether the decoded 3x3 is the transform's rows or its columns "
            "(the 4.00 deg Y tilt's sign)":
                "tested both readings of the 16 floats (one fails orthonormality); R and R^T are "
                "both proper rotations of the same angle about Y, and no second transform in the "
                "file fixes the convention",
            "the StaticMesh Bounds as a second extents oracle (not a tag; no layout)":
                "G3-01c walked 175973/175974: 4 unnamed tags and no Bounds struct; "
                "BMSDK_OFFSETS.json has no StaticMesh class",
        }[u]
        where = {
            "the 0x4C bool's member name and meaning":
                "BmSDK-AK's struct dump for the box element (G3-06 native layouts), or a body "
                "whose other 0x4C bit differs and whose effect is observable",
            "which element type the zero count before the convex count belongs to":
                "a body that contains a sphere or sphyl element (none of the 131 boxes' bodies "
                "do), or the engine's aggregate serialiser definition",
            "whether the decoded 3x3 is the transform's rows or its columns "
            "(the 4.00 deg Y tilt's sign)":
                "a second, known transform for the same bone (bone local matrix in the skeletal "
                "mesh) or the engine's FMatrix convention for this build",
            "the StaticMesh Bounds as a second extents oracle (not a tag; no layout)":
                "G3-06, then re-run this tool with the mesh bounds as a second hull",
        }[u]
        a("| U-%d | %s | %s | %s |" % (i, u, tried, where))
    a("")

    a("## Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for c in d["checks"]:
        a("| %s | %s | %s |" % (c["name"].replace("|", "/"),
                                "PASS" if c["pass"] else "FAIL",
                                str(c["detail"]).replace("|", "/")))
    a("")
    a("%d/%d checks passed." % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not args.write and not args.check:
        args.check = True
    doc = build()
    js = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    md = render(doc)
    js_path = os.path.join(OUT, "COLLISION_BOXES.json")
    md_path = os.path.join(OUT, "COLLISION_BOXES.md")
    if args.write:
        with open(js_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote COLLISION_BOXES.json and COLLISION_BOXES.md (%d boxes: %d BmGame + %d wreck); "
              "extents: %s"
              % (doc["summary"]["boxes_total"], doc["summary"]["boxes_bmgame"],
                 doc["summary"]["boxes_wreck"], doc["summary"]["extents_convention"]))
        bad = [c for c in doc["checks"] if not c["pass"]]
        for c in bad:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1 if bad else 0
    problems = [c for c in doc["checks"] if not c["pass"]]
    if not os.path.isfile(js_path) or not os.path.isfile(md_path):
        print("MISSING: run --write")
        return 1
    if open(js_path, encoding="utf-8").read() != js:
        print("STALE: COLLISION_BOXES.json does not match a fresh build")
        return 1
    if open(md_path, encoding="utf-8").read() != md:
        print("STALE: COLLISION_BOXES.md does not match a fresh render")
        return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    print("OK: %d boxes (%d BmGame + %d wreck), %d byte-mapped payloads, rotations %d/%d, "
          "extents %s, %d/%d checks, md byte-identical"
          % (doc["summary"]["boxes_total"], doc["summary"]["boxes_bmgame"],
             doc["summary"]["boxes_wreck"], len(doc["bodies"]),
             doc["summary"]["rotations_decoded"], doc["summary"]["boxes_total"],
             doc["summary"]["extents_convention"], len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
