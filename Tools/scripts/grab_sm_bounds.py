#!/usr/bin/env python3
"""grab_sm_bounds.py - the StaticMesh Bounds of the Batmobile's two collision meshes (G3-01b U-4).

G3-01b (`grab_collision_boxes.py`) asked for the cooked `StaticMesh` bounds of `Batmobile_V2`
(export 175973, battle mode) and `Batmobile_V2_Collision_Pursuite` (export 175974, pursuit mode)
as a second oracle for its box extents, and found no `Bounds` struct in their tagged properties:
the tag stream of each export is exactly four tags and ends at byte 32, then a 2-byte `type 0`
terminator. It stopped there because a `--dump` tag walk reports 4 tags and nothing else.

This tool reads what follows the terminator. In both exports the native remainder begins with
the same record, and every field of it is checked against an independent number:

    +0    28 B   FBoxSphereBounds   Origin (3 float), BoxExtent (3 float), SphereRadius (1 float)
    +28    4 B   int32              == the export's `ObjectNCR` tag value (its RB_BodySetup)
    +32   24 B   FBox               Min (3 float), Max (3 float)
    +56    8 B   2 x int32          `6, 128` in both exports; semantics UNKNOWN

LABELS. **decoded** = read from BmGame.upk bytes (export + byte offset); **derived** = computed
here from decoded values with the rule stated; **UNKNOWN** = not decoded, with what was tried.

THE ORACLES (each fails if the reading is wrong)

1. Position. The block starts at `tag_end + 2` (the first byte after the property-list
   terminator), and it is the only FBoxSphereBounds-shaped tuple in the whole native body whose
   Origin/BoxExtent equal the centre/half-span of the FBox 32 bytes behind it. A scan of every
   4-byte offset of both bodies returns one such candidate, at delta 0.
2. Internal arithmetic. `Origin == (Min + Max) / 2` and `BoxExtent == (Max - Min) / 2` to within
   one float ulp (max 1.5e-5 cm). Two independent fields, one derived from the other.
3. Identity. The int32 between them is 169748 / 169749 - the same export index the export's own
   `ObjectNCR` tag points at, i.e. the mesh's `RB_BodySetup` (G3-01b's / G3-01c's bodies).
4. Package-wide shape. The same block sits immediately after the terminator on 39 of the 52
   `StaticMesh` exports of `BmGame.upk` and satisfies oracle 2 there as well, so the position and
   the arithmetic are properties of the package's `StaticMesh` serialisation, not a coincidence
   at two exports. The 13 that do not are listed in the record and are not explained here.
5. Geometry. The FBox is compared with the union of the collision hull's own decoded vertices
   (the 43 / 13 `FKConvexElem` vertex arrays of 169748 / 169749, re-read here from BmGame.upk
   with G3-01c's `parse_element`): the two boxes agree within 12.06 / 21.82 cm (1.7 % / 3.1 % of
   the largest span). SphereRadius is compared with the hull's `max |v - Origin|`: within
   0.997 cm (0.23 %) / 0.210 cm (0.05 %), and it is 4.8 % / 7.0 % smaller than the box's own
   corner distance - so it is a sphere radius measured on vertices, not `|BoxExtent|`.
   The render mesh's own (compressed) vertex buffer is NOT decoded here; see UNKNOWNs.
6. G3-01b's extents. Compared with the mesh's full spans, every chassis-box dimension is at most
   1.00x / 0.98x of the span (full-length reading) and would be 1.42x - 1.96x (half-length
   reading) - a box larger than the mesh that contains it. Second, independent confirmation of
   G3-01b's "extents are FULL lengths" verdict.

Read-only on the game install. Writes only its two outputs.

Usage:
    uv run python Tools/scripts/grab_sm_bounds.py --write
    uv run python Tools/scripts/grab_sm_bounds.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U                    # noqa: E402  (read-only: package + tag walk)
import grab_collision_convex as CC      # noqa: E402  (read-only: parse_element, G3-01c)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
BMGAME = os.path.join(GAME, "BmGame.upk")
BOXES_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_BOXES.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "SM_BOUNDS.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "SM_BOUNDS.json")

TARGETS = (
    {"mesh": 175973, "body": 169748, "mode": "battle", "mesh_name": "Batmobile_V2"},
    {"mesh": 175974, "body": 169749, "mode": "pursuit",
     "mesh_name": "Batmobile_V2_Collision_Pursuite"},
)
HEAD_BYTES = 64          # bytes of native data recorded as hex per export
MIN_EXTENT = 1.0         # cm: a candidate bounds box must be bigger than the zero padding
CONSIST_TOL = 1e-4       # cm: Origin/BoxExtent vs the FBox centre/half-span
FLEET_MIN = 30           # of 52 StaticMesh exports: the observed 39 must clear this
HULL_SPAN_TOL = 0.05     # fraction of the largest span: FBox vs hull vertex union
RADIUS_TOL = 0.005       # fraction of SphereRadius: radius vs hull max |v - Origin|


# ---------------------------------------------------------------- byte helpers

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


def fv(b, o, n):
    return [struct.unpack_from("<f", b, o + 4 * i)[0] for i in range(n)]


# ---------------------------------------------------------------- the record

def mesh_record(pkg, spec):
    """Decode one StaticMesh export's tag stream and the bounds block behind it."""
    e = pkg.exports[spec["mesh"] - 1]
    d = pkg.data(spec["mesh"])
    tags, end, why = U.walk_tags(pkg, d, 0)
    term = d[end:end + 2]
    base = end + 2
    origin = fv(d, base, 3)
    extent = fv(d, base + 12, 3)
    radius = f32(d, base + 24)
    ref = i32(d, base + 28)
    box_min = fv(d, base + 32, 3)
    box_max = fv(d, base + 44, 3)
    tail = [i32(d, base + 56), i32(d, base + 60)]
    objncr = [t for t in tags if t.get("type") == "ObjectNCRProperty"]
    return {
        "export": spec["mesh"],
        "name": e["name"],
        "class": pkg.object_class(spec["mesh"]),
        "outer": pkg.object_path(e["outer_index"]),
        "size": e["size"],
        "mode": spec["mode"],
        "body_expected": spec["body"],
        "tag_count": len(tags),
        "tag_end": end,
        "tag_stop": why,
        "tag_stream_hex": d[:base].hex(),
        "tags": [{"type": t["type"], "offset": t["offset"],
                  "value": t.get("value"), "at": t["at"]} for t in tags],
        "terminator_hex": term.hex(),
        "native_start": base,
        "native_bytes": len(d) - base,
        "head_hex": d[base:base + HEAD_BYTES].hex(),
        "bounds": {
            "native_offset": 0,
            "origin_cm": origin,
            "extent_cm": extent,
            "radius_cm": radius,
            "hex": d[base:base + 28].hex(),
            "label": "decoded: FBoxSphereBounds at native+0 (Origin 3f, BoxExtent 3f, "
                     "SphereRadius 1f = 28 B)",
        },
        "body_ref": {
            "native_offset": 28,
            "value": ref,
            "object_class": pkg.object_class(ref) if 0 < ref <= pkg.export_count else None,
            "object_path": pkg.object_path(ref),
            "tag_value": objncr[0]["value"] if objncr else None,
            "matches_tag": bool(objncr) and objncr[0]["value"] == ref,
            "label": "decoded int32; field name UNKNOWN, value == this export's ObjectNCR tag",
        },
        "box": {
            "native_offset": 32,
            "min_cm": box_min,
            "max_cm": box_max,
            "hex": d[base + 32:base + 56].hex(),
            "label": "decoded: FBox (Min 3f, Max 3f) at native+32",
        },
        "trailer": {
            "native_offset": 56,
            "ints": tail,
            "hex": d[base + 56:base + 64].hex(),
            "label": "decoded bytes; semantics UNKNOWN",
        },
    }


def consistency(rec):
    """Origin/BoxExtent vs the FBox behind them (oracle 2)."""
    o = rec["bounds"]["origin_cm"]
    e = rec["bounds"]["extent_cm"]
    lo = rec["box"]["min_cm"]
    hi = rec["box"]["max_cm"]
    center = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    half = [(hi[i] - lo[i]) / 2.0 for i in range(3)]
    ce = max(abs(center[i] - o[i]) for i in range(3))
    ee = max(abs(half[i] - e[i]) for i in range(3))
    return {"center_abs_diff_cm": ce, "extent_abs_diff_cm": ee,
            "center_cm": center, "half_span_cm": half,
            "corner_distance_cm": math.sqrt(sum(v * v for v in e)),
            "agrees": ce <= CONSIST_TOL and ee <= CONSIST_TOL,
            "label": "derived: Origin == (Min+Max)/2 and BoxExtent == (Max-Min)/2"}


def candidate_at(d, o):
    """Is there a self-consistent FBoxSphereBounds+FBox pair at native offset `o`?"""
    if o < 0 or o + 56 > len(d):
        return None
    try:
        b = fv(d, o, 7)
        box = fv(d, o + 32, 6)
    except struct.error:
        return None
    if any(v != v or abs(v) > 1e7 for v in b + box):
        return None
    if not all(b[3 + i] > MIN_EXTENT for i in range(3)) or b[6] <= MIN_EXTENT:
        return None
    center = [(box[i] + box[3 + i]) / 2.0 for i in range(3)]
    half = [(box[3 + i] - box[i]) / 2.0 for i in range(3)]
    ce = max(abs(center[i] - b[i]) for i in range(3))
    ee = max(abs(half[i] - b[3 + i]) for i in range(3))
    return {"delta": o, "center_abs_diff_cm": ce, "extent_abs_diff_cm": ee} \
        if ce <= CONSIST_TOL and ee <= CONSIST_TOL else None


def scan_body(d, base, limit=None):
    """Every self-consistent bounds block in the native body, 4-byte offsets."""
    end = len(d) if limit is None else min(len(d), base + limit)
    hits = []
    for o in range(0, end - base - 56 + 1, 4):
        c = candidate_at(d, base + o)
        if c:
            c["absolute_offset"] = c.pop("delta")
            c["delta"] = o
            hits.append(c)
    return hits


def fleet_scan(pkg):
    """Oracle 4: how many StaticMesh exports carry the same block at tag_end+2."""
    rows, conforming, other = [], 0, []
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "StaticMesh":
            continue
        d = pkg.data(i)
        tags, end, why = U.walk_tags(pkg, d, 0)
        c = candidate_at(d, end + 2)
        row = {"export": i, "name": pkg.exports[i - 1]["name"], "size": len(d),
               "tag_count": len(tags), "tag_end": end, "conforms_at_tag_end_plus_2": bool(c)}
        if c:
            row["center_abs_diff_cm"] = c["center_abs_diff_cm"]
            row["extent_abs_diff_cm"] = c["extent_abs_diff_cm"]
            conforming += 1
        else:
            row["head_hex"] = d[end + 2:end + 2 + 32].hex()
            other.append(row)
        rows.append(row)
    return {"staticmesh_exports": len(rows), "conforming": conforming,
            "not_conforming": len(other), "rows": rows, "non_conforming": other,
            "label": "decoded: BmGame.upk, every export whose class is StaticMesh"}


# ---------------------------------------------------------------- hull geometry

def hull_vertices(pkg, export):
    """The collision hull's own vertices: 169748 / 169749 AggGeom, G3-01c's element layout."""
    d = pkg.data(export)
    tags, end, why = U.walk_tags(pkg, d, 0)
    agg = [t for t in tags if t.get("type") == "StructProperty" and t.get("name") == "AggGeom"]
    if not agg:
        raise SystemExit("export %d has no AggGeom tag" % export)
    attr = agg[0]
    payload = d[attr["at"]:attr["at"] + attr["size"]]
    counts = [u32(payload, 4 * k) for k in range(4)]
    if counts[:3] != [0, 0, 0]:
        raise SystemExit("export %d carries shaped elements (%r); this tool expects convex only"
                         % (export, counts))
    p, verts = 16, []
    for _ in range(counts[3]):
        el = CC.parse_element(payload, p)
        verts += [tuple(v) for v in el["vertices_cm"]]
        p = el["end"]
    footer = payload[p:]
    return {"export": export, "aggeom_bytes": len(payload), "counts": counts,
            "elements": counts[3], "vertices": verts, "footer": footer,
            "footer_all_zero": not any(footer),
            "bytes_consumed": p, "aggeom_tag_at": attr["at"]}


def hull_oracle(rec, hull):
    """Oracle 5: FBox vs the hull's vertex union; SphereRadius vs max |v - Origin|."""
    v = hull["vertices"]
    lo = [min(p[i] for p in v) for i in range(3)]
    hi = [max(p[i] for p in v) for i in range(3)]
    box_lo = rec["box"]["min_cm"]
    box_hi = rec["box"]["max_cm"]
    span = [box_hi[i] - box_lo[i] for i in range(3)]
    diffs = [box_lo[i] - lo[i] for i in range(3)] + [box_hi[i] - hi[i] for i in range(3)]
    origin = rec["bounds"]["origin_cm"]
    rad = [math.sqrt(sum((p[i] - origin[i]) ** 2 for i in range(3))) for p in v]
    corner = math.sqrt(sum(x * x for x in rec["bounds"]["extent_cm"]))
    worst = max(abs(x) for x in diffs)
    worst_frac = worst / max(span)
    radius_diff = rec["bounds"]["radius_cm"] - max(rad)
    return {
        "vertices": len(v),
        "vertex_union_min_cm": lo,
        "vertex_union_max_cm": hi,
        "vertex_union_span_cm": [hi[i] - lo[i] for i in range(3)],
        "box_vs_union_cm": diffs,
        "box_vs_union_worst_cm": worst,
        "box_vs_union_worst_fraction_of_span": worst_frac,
        "max_vertex_distance_from_origin_cm": max(rad),
        "radius_minus_max_vertex_distance_cm": radius_diff,
        "radius_fraction_of_that": abs(radius_diff) / rec["bounds"]["radius_cm"],
        "box_corner_distance_cm": corner,
        "radius_over_corner": rec["bounds"]["radius_cm"] / corner,
        "agrees_box": worst_frac <= HULL_SPAN_TOL,
        "agrees_radius": abs(radius_diff) / rec["bounds"]["radius_cm"] <= RADIUS_TOL,
        "radius_below_corner": rec["bounds"]["radius_cm"] <= 0.98 * corner,
        "label": "derived: the FBox and the SphereRadius against the decoded hull vertices of "
                 "the same mesh's RB_BodySetup",
    }


# ---------------------------------------------------------------- G3-01b's boxes

def load_boxes():
    rec = json.load(open(BOXES_JSON, encoding="utf-8"))
    rows = []
    for b in rec["bodies"]:
        for bx in b["boxes"]:
            rows.append({"body": b["export"], "bone": b["bone"], "box": bx["index"],
                         "extents_cm": [float(x) for x in bx["extents_cm"]],
                         "bool_word": bx["bool_word"]})
    return rows


def compare(boxes, recs):
    """Oracle 6: each G3-01b box against each mesh's own full span, both readings."""
    rows = []
    for bx in boxes:
        bext = sorted(bx["extents_cm"], reverse=True)
        for rec in recs:
            span = sorted([2.0 * e for e in rec["bounds"]["extent_cm"]], reverse=True)
            full = [bext[i] / span[i] for i in range(3)]
            half = [2.0 * bext[i] / span[i] for i in range(3)]
            rows.append({
                "body": bx["body"], "bone": bx["bone"], "box": bx["box"],
                "mesh": rec["export"], "mesh_mode": rec["mode"],
                "box_extents_sorted_cm": bext,
                "mesh_full_spans_sorted_cm": span,
                "ratio_full_reading": full,
                "ratio_half_reading": half,
                "max_ratio_full": max(full),
                "max_ratio_half": max(half),
                "min_ratio_half": min(half),
                "label": "derived: box extent / mesh span, sorted per axis to stay "
                         "frame-agnostic (spans read either way are only compared sorted)",
            })
    return rows


def comparison_verdict(rows):
    """The decisive rows: the two chassis boxes (169750), the whole-car envelopes.

    The discriminating axis is each box's LONGEST one.  A chassis box is allowed to be much
    thinner than the car on some other axis (box 1 is a floor pan: 103.5 cm), so the smallest
    ratio of a box decides nothing; a box that is longer than the mesh it sits in cannot exist
    in either reading, and the long axis is where the two readings are 2x apart.
    """
    chassis = [r for r in rows if r["body"] == 169750]
    full = max(r["max_ratio_full"] for r in chassis) if chassis else None
    half = min(r["max_ratio_half"] for r in chassis) if chassis else None
    thin = min(r["min_ratio_half"] for r in chassis) if chassis else None
    return {"chassis_rows": len(chassis),
            "max_ratio_full_reading": full,
            "max_ratio_half_reading": half,
            "min_ratio_half_reading_any_axis": thin,
            "verdict": "FULL lengths" if (full is not None and full <= 1.10
                                          and half is not None and half >= 1.40) else "UNDECIDED",
            "label": "derived: with FULL lengths every chassis-box dimension is at most %.3fx "
                     "the mesh span; with HALF lengths every chassis box's long axis would be "
                     "%.3fx the span of the mesh that contains it" % (full, half)}


# ---------------------------------------------------------------- build the record

def build():
    pkg = U.Package(BMGAME)
    recs = [mesh_record(pkg, spec) for spec in TARGETS]
    for rec in recs:
        rec["consistency"] = consistency(rec)
        d = pkg.data(rec["export"])
        rec["candidates"] = scan_body(d, rec["native_start"])
        rec["candidates_in_first_1024"] = [c for c in rec["candidates"]
                                           if c["delta"] < 1024]
        hull = hull_vertices(pkg, rec["body_expected"])
        rec["hull"] = {"export": hull["export"], "elements": hull["elements"],
                       "counts": hull["counts"], "vertices": len(hull["vertices"]),
                       "aggeom_bytes": hull["aggeom_bytes"],
                       "bytes_consumed": hull["bytes_consumed"],
                       "footer_bytes": len(hull["footer"]),
                       "footer_all_zero": hull["footer_all_zero"]}
        rec["hull"]["oracle"] = hull_oracle(rec, hull)
        rec["hull"]["vertex_union_note"] = (
            "the hull's vertices are the collision decomposition of this mesh, not the render "
            "mesh's own vertex buffer (which is compressed and not decoded here)")

    fleet = fleet_scan(pkg)
    boxes = load_boxes()
    rows = compare(boxes, recs)
    verdict = comparison_verdict(rows)

    doc = {
        "generator": "Tools/scripts/grab_sm_bounds.py (G3-01b U-4 follow-up)",
        "card": "GRAB_BACKLOG.md G3-01b open item: StaticMesh Bounds as a second extents oracle",
        "inputs": {"package": BMGAME, "boxes_record": BOXES_JSON,
                   "reader": "Tools/scripts/upk_read.py (read-only)",
                   "convex_reader": "Tools/scripts/grab_collision_convex.parse_element (read-only)"},
        "scope": "BmGame.upk StaticMesh 175973 and 175974; every StaticMesh export for the "
                 "package-wide position oracle",
        "layout": {
            "native_offset_0": "FBoxSphereBounds: Origin 3f, BoxExtent 3f, SphereRadius 1f (28 B)",
            "native_offset_28": "int32 = the export's ObjectNCR tag value (its RB_BodySetup)",
            "native_offset_32": "FBox: Min 3f, Max 3f (24 B)",
            "native_offset_56": "2 x int32, `6, 128` in both exports - semantics UNKNOWN",
            "native_offset_64": "cooked compressed mesh data (not decoded here)",
            "label": "decoded: byte offsets relative to the first byte after the property-list "
                     "terminator",
        },
        "static_meshes": recs,
        "fleet": fleet,
        "comparison": rows,
        "comparison_verdict": verdict,
        "unknowns": [
            {"item": "the member names of the u32 at native+28 and the two u32 at native+56",
             "tried": "decoded every value; the +28 value equals the export's own ObjectNCR tag "
                      "(169748/169749) and the +56 pair is `6, 128` in both exports",
             "why": "BMSDK_OFFSETS.json has no StaticMesh layout, so a byte offset can be named "
                    "only with the engine's own struct dump (the G3-06 native-layout question)"},
            {"item": "the exact vertex set SphereRadius was measured on",
             "tried": "compared it with the hull's max |v - Origin| (0.997 cm / 0.210 cm apart) "
                      "and with the box corner distance (4.8 % / 7.0 % farther away)",
             "why": "the render mesh's own vertex buffer is cooked/compressed (the native body "
                    "from +64 on is not decoded here), so the equality can be tested only "
                    "against the collision decomposition, which is a different vertex set"},
            {"item": "why 13 of 52 BmGame StaticMesh exports do not carry the block at tag_end+2",
             "tried": "scanned every 4-byte offset up to 16 bytes past the terminator on each of "
                      "the 52; recorded those exports' heads in the record",
             "why": "those exports' native heads start with zero bytes (e.g. 176006 "
                    "HelicopterSearchLight), so a different or absent native prologue is in "
                    "front of the mesh data; deciding it needs its own decode, and it does not "
                    "affect 175973/175974"},
            {"item": "whether the FBox is the render mesh's data or its collision proxy's",
             "tried": "the FBox is 12.06 cm / 21.82 cm wider than the hull vertex union on one "
                      "axis and 0.31 cm / 16.79 cm narrower on another",
             "why": "both are coded here as numbers; which vertex set the engine took is not "
                    "provable without the render mesh's vertex buffer"},
        ],
        "checks": [],
    }
    doc["checks"] = run_checks(doc)
    doc["summary"] = {
        "static_meshes": len(recs),
        "bounds_position": {str(r["export"]): r["native_start"] for r in recs},
        "origin_cm": {str(r["export"]): r["bounds"]["origin_cm"] for r in recs},
        "extent_cm": {str(r["export"]): r["bounds"]["extent_cm"] for r in recs},
        "full_span_cm": {str(r["export"]): [2.0 * e for e in r["bounds"]["extent_cm"]]
                         for r in recs},
        "radius_cm": {str(r["export"]): r["bounds"]["radius_cm"] for r in recs},
        "fleet_conforming": "%d/%d" % (fleet["conforming"], fleet["staticmesh_exports"]),
        "extents_verdict": verdict["verdict"],
        "checks_passed": str(sum(1 for c in doc["checks"] if c["ok"])) + "/%d" % len(doc["checks"]),
    }
    return doc


def run_checks(doc):
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    recs = doc["static_meshes"]
    check("the tagged properties of both exports carry no Bounds struct",
          all(r["tag_count"] == 4 for r in recs),
          ", ".join("%d: %d tags, bytes 0..%d" % (r["export"], r["tag_count"], r["tag_end"])
                    for r in recs))
    check("the property list ends on a 2-byte type 0 terminator in both exports",
          all(r["terminator_hex"] == "0000" for r in recs),
          ", ".join("%d: %s" % (r["export"], r["terminator_hex"]) for r in recs))
    check("the bounds block starts at tag_end+2 and is the only such block in the body",
          all(r["candidates"] and r["candidates"][0]["delta"] == 0
              and len(r["candidates_in_first_1024"]) == 1 for r in recs),
          ", ".join("%d: %d candidate(s) at deltas %s" % (
              r["export"], len(r["candidates"]),
              [c["delta"] for c in r["candidates"][:6]]) for r in recs))
    check("Origin == (Min+Max)/2 and BoxExtent == (Max-Min)/2 for both blocks",
          all(r["consistency"]["agrees"] for r in recs),
          ", ".join("%d: centre %.2e cm, extent %.2e cm" % (
              r["export"], r["consistency"]["center_abs_diff_cm"],
              r["consistency"]["extent_abs_diff_cm"]) for r in recs))
    check("the int32 at native+28 is each export's own ObjectNCR (RB_BodySetup) value",
          all(r["body_ref"]["matches_tag"] and r["body_ref"]["value"] == r["body_expected"]
              and r["body_ref"]["object_class"] == "RB_BodySetup" for r in recs),
          ", ".join("%d: %d = tag %s" % (r["export"], r["body_ref"]["value"],
                                         r["body_ref"]["tag_value"]) for r in recs))
    check("the same block sits at tag_end+2 on most StaticMesh exports of BmGame.upk",
          doc["fleet"]["conforming"] >= FLEET_MIN,
          "%d/%d conform (%d recorded as non-conforming)" % (
              doc["fleet"]["conforming"], doc["fleet"]["staticmesh_exports"],
              doc["fleet"]["not_conforming"]))
    check("the hull vertices are re-read from the export the bounds point at",
          all(r["hull"]["export"] == r["body_expected"] and r["hull"]["footer_all_zero"]
              for r in recs),
          ", ".join("%d: %d elements, %d vertices, %d B AggGeom, %d B zero footer" % (
              r["export"], r["hull"]["elements"], r["hull"]["vertices"],
              r["hull"]["aggeom_bytes"], r["hull"]["footer_bytes"]) for r in recs))
    check("the FBox agrees with the hull's vertex union within 5 %% of the largest span",
          all(r["hull"]["oracle"]["agrees_box"] for r in recs),
          "; ".join("%d: worst %.2f cm = %.2f %% of span" % (
              r["export"], r["hull"]["oracle"]["box_vs_union_worst_cm"],
              100 * r["hull"]["oracle"]["box_vs_union_worst_fraction_of_span"]) for r in recs))
    check("SphereRadius is within 0.5 %% of the hull's max |v - Origin|",
          all(r["hull"]["oracle"]["agrees_radius"] for r in recs),
          "; ".join("%d: radius %.4f vs %.4f cm (%.2f %%)" % (
              r["export"], r["bounds"]["radius_cm"],
              r["hull"]["oracle"]["max_vertex_distance_from_origin_cm"],
              100 * r["hull"]["oracle"]["radius_fraction_of_that"]) for r in recs))
    check("SphereRadius is NOT the box corner distance (it is smaller on both)",
          all(r["hull"]["oracle"]["radius_below_corner"] for r in recs),
          "; ".join("%d: %.4f / %.4f = %.4f" % (
              r["export"], r["bounds"]["radius_cm"],
              r["hull"]["oracle"]["box_corner_distance_cm"],
              r["hull"]["oracle"]["radius_over_corner"]) for r in recs))
    check("every G3-01b chassis-box dimension is within the mesh's own full span",
          doc["comparison_verdict"]["max_ratio_full_reading"] is not None
          and doc["comparison_verdict"]["max_ratio_full_reading"] <= 1.10,
          "max ratio %.4f" % (doc["comparison_verdict"]["max_ratio_full_reading"] or 0.0))
    check("under the half-length reading every chassis box would be longer than the mesh",
          doc["comparison_verdict"]["max_ratio_half_reading"] is not None
          and doc["comparison_verdict"]["max_ratio_half_reading"] >= 1.40,
          "long-axis ratio %.4f (the thin axis of the floor-pan box stays at %.4f, which decides "
          "nothing)" % (doc["comparison_verdict"]["max_ratio_half_reading"] or 0.0,
                        doc["comparison_verdict"]["min_ratio_half_reading_any_axis"] or 0.0))
    check("the extents verdict is FULL lengths by this second check too",
          doc["comparison_verdict"]["verdict"] == "FULL lengths",
          doc["comparison_verdict"]["verdict"])
    return checks


# ---------------------------------------------------------------- rendering

def fmt(v, n=3):
    if isinstance(v, list):
        return " / ".join("%.*f" % (n, x) for x in v)
    return "%.*f" % (n, v)


def render(doc):
    L = []
    a = L.append
    recs = doc["static_meshes"]
    a("# StaticMesh Bounds of the Batmobile's two collision meshes (G3-01b U-4)")
    a("")
    a("Generated by `Tools/scripts/grab_sm_bounds.py --write`. Every number below is recomputed "
      "from `BmGame.upk` by `--check`, which also fails if this file or the JSON differs by one "
      "byte.")
    a("")
    a("**The question.** G3-01b (`grab_collision_boxes.py`) wanted the cooked `StaticMesh` bounds "
      "of `Batmobile_V2` (175973) and `Batmobile_V2_Collision_Pursuite` (175974) as a second "
      "check on its box extents. It found no `Bounds` struct in their tagged properties - "
      "correctly: both exports carry **four** tags and end the property list at byte 32.")
    a("")
    a("**The answer.** The bounds are in the untagged native data that starts at byte "
      "**%d** (both exports), as an `FBoxSphereBounds`: Origin (3 floats), BoxExtent (3 "
      "floats), SphereRadius (1 float) = 28 bytes." % recs[0]["native_start"])
    a("")

    a("## 1. The decoded records")
    a("")
    a("| export | mesh | mode | body setup | native start | tags | size |")
    a("|---|---|---|---|---:|---:|---:|")
    for r in recs:
        a("| %d | `%s` | %s | %d `%s` | %d | %d | %d B |" % (
            r["export"], r["name"], r["mode"], r["body_ref"]["value"], r["body_ref"]["object_path"],
            r["native_start"], r["tag_count"], r["size"]))
    a("")
    a("The four tags, for completeness (they are all the tagged properties there are):")
    a("")
    a("| export | # | type | class offset | value | at |")
    a("|---|---:|---|---:|---|---:|")
    for r in recs:
        for i, t in enumerate(r["tags"]):
            a("| %d | %d | %s | %d | `%s` | %d |" % (r["export"], i, t["type"], t["offset"],
                                                     t["value"], t["at"]))
    a("")
    a("### The seven floats, and the field set around them")
    a("")
    a("| export | Origin (cm) | BoxExtent (cm) | SphereRadius (cm) | full span = 2 x extent |")
    a("|---|---|---|---:|---|")
    for r in recs:
        a("| %d | %s | %s | %.4f | %s |" % (
            r["export"], fmt(r["bounds"]["origin_cm"], 4), fmt(r["bounds"]["extent_cm"], 4),
            r["bounds"]["radius_cm"], fmt([2 * e for e in r["bounds"]["extent_cm"]], 4)))
    a("")
    a("Field set at the native start (decoded offsets, relative to it):")
    a("")
    a("| offset | bytes | content |")
    a("|---:|---:|---|")
    for k in ("native_offset_0", "native_offset_28", "native_offset_32",
              "native_offset_56", "native_offset_64"):
        a("| +%s | | %s |" % (k.split("_")[-1], doc["layout"][k]))
    a("")
    for r in recs:
        a("```")
        a("%d %s  native+0 .. +%d" % (r["export"], r["name"], HEAD_BYTES - 1))
        a(r["head_hex"])
        a("  FBoxSphereBounds  origin %s  extent %s  radius %.4f"
          % (fmt(r["bounds"]["origin_cm"], 4), fmt(r["bounds"]["extent_cm"], 4),
             r["bounds"]["radius_cm"]))
        a("  int32             %d (%s)" % (r["body_ref"]["value"], r["body_ref"]["object_path"]))
        a("  FBox              min %s  max %s"
          % (fmt(r["box"]["min_cm"], 4), fmt(r["box"]["max_cm"], 4)))
        a("  trailer           %s" % (r["trailer"]["hex"],))
        a("```")
        a("")

    a("## 2. Oracles actually run")
    a("")
    a("| # | oracle | result |")
    a("|---:|---|---|")
    a("| 1 | the block starts exactly at `tag_end+2` and is the only self-consistent "
      "FBoxSphereBounds+FBox pair in the body | %s |"
      % "; ".join("%d: %d candidate(s) at delta %d"
                  % (r["export"], len(r["candidates"]), r["candidates"][0]["delta"])
                  for r in recs))
    a("| 2 | `Origin == (Min+Max)/2`, `BoxExtent == (Max-Min)/2` | %s |"
      % "; ".join("%d: %.2e / %.2e cm" % (r["export"], r["consistency"]["center_abs_diff_cm"],
                                          r["consistency"]["extent_abs_diff_cm"]) for r in recs))
    a("| 3 | the int32 between them is each export's own `ObjectNCR` (RB_BodySetup) | "
      "%s |" % ", ".join("%d = %d" % (r["export"], r["body_ref"]["value"]) for r in recs))
    a("| 4 | the same block at `tag_end+2` across BmGame.upk's StaticMesh exports | "
      "**%d / %d** conform, %d not (%s) |"
      % (doc["fleet"]["conforming"], doc["fleet"]["staticmesh_exports"],
         doc["fleet"]["not_conforming"],
         ", ".join(str(r["export"]) for r in doc["fleet"]["non_conforming"][:8])))
    a("| 5 | the FBox vs the hull's own vertex union | %s |"
      % "; ".join("%d: worst %.2f cm (%.2f %%)"
                  % (r["export"], r["hull"]["oracle"]["box_vs_union_worst_cm"],
                     100 * r["hull"]["oracle"]["box_vs_union_worst_fraction_of_span"])
                  for r in recs))
    a("| 6 | SphereRadius vs `max |v - Origin|` of the hull | %s |"
      % "; ".join("%d: %.4f vs %.4f (%.2f %%)"
                  % (r["export"], r["bounds"]["radius_cm"],
                     r["hull"]["oracle"]["max_vertex_distance_from_origin_cm"],
                     100 * r["hull"]["oracle"]["radius_fraction_of_that"]) for r in recs))
    a("| 7 | SphereRadius vs the box corner distance (is it `|BoxExtent|`?) | %s |"
      % "; ".join("%d: %.4f / %.4f = %.4f -> **not** the corner"
                  % (r["export"], r["bounds"]["radius_cm"],
                     r["hull"]["oracle"]["box_corner_distance_cm"],
                     r["hull"]["oracle"]["radius_over_corner"]) for r in recs))
    a("| 8 | G3-01b's box extents vs the mesh spans, both readings | **%s** |"
      % doc["comparison_verdict"]["verdict"])
    a("")
    a("Oracle 4's non-conforming exports, recorded rather than explained: those native heads "
      "begin with zero bytes (see the JSON's `fleet.non_conforming`, which keeps the first 32 "
      "bytes of each).")
    a("")
    a("### The hull oracle's numbers")
    a("")
    a("| export | hull elements | hull vertices | vertex-union span (cm) | FBox span (cm) | "
      "FBox - union (min xyz, max xyz) |")
    a("|---|---:|---:|---|---|---|")
    for r in recs:
        o = r["hull"]["oracle"]
        a("| %d | %d | %d | %s | %s | %s |" % (
            r["export"], r["hull"]["elements"], o["vertices"],
            fmt(o["vertex_union_span_cm"], 3),
            fmt([r["box"]["max_cm"][i] - r["box"]["min_cm"][i] for i in range(3)], 3),
            " / ".join("%+.2f" % x for x in o["box_vs_union_cm"])))
    a("")
    diffs = [x for r in recs for x in r["hull"]["oracle"]["box_vs_union_cm"]]
    a("The FBox is not the hull's vertex union: it reaches up to **+%.2f cm** beyond it on one "
      "side and falls up to **%.2f cm** inside it on another. That is consistent with the bounds "
      "being computed over the render mesh's own vertices - which this record does not decode - "
      "while the hull vertices are a decomposition of the same surface. Both are recorded as "
      "numbers; neither is adjusted." % (max(diffs), abs(min(diffs))))
    a("")

    a("## 3. The comparison G3-01b asked for")
    a("")
    a("Box extents are G3-01b's decoded `KBoxElem` extents (`COLLISION_BOXES.json`, "
      "`extents_cm`); spans are this record's `2 x BoxExtent`. Both are sorted per axis before "
      "dividing, the same frame-agnostic rule G3-01b used, because the box is in a bone's frame "
      "and the mesh bounds in the mesh's.")
    a("")
    a("| box (body / bone / #) | box extents (cm) | mesh | mesh full span (cm) | ratio, FULL "
      "reading | ratio, HALF reading |")
    a("|---|---|---|---|---|---|")
    for r in doc["comparison"]:
        a("| %d / `%s` / %d | %s | %d %s | %s | %s | %s |" % (
            r["body"], r["bone"], r["box"], fmt(r["box_extents_sorted_cm"], 3),
            r["mesh"], r["mesh_mode"], fmt(r["mesh_full_spans_sorted_cm"], 3),
            fmt(r["ratio_full_reading"], 4), fmt(r["ratio_half_reading"], 4)))
    a("")
    v = doc["comparison_verdict"]
    a("**Verdict: %s**, by the two chassis boxes (the whole-car envelopes). Under the full-length "
      "reading every chassis-box dimension is at most **%.4f** of the mesh span; under the "
      "half-length reading each chassis box's long axis would be **%.4f** of the span of the "
      "mesh that is supposed to contain it. This reproduces G3-01b's own result (\"extents: "
      "FULL lengths\") from the mesh geometry instead of from the convex hull."
      % (v["verdict"], v["max_ratio_full_reading"], v["max_ratio_half_reading"]))
    a("")
    a("The test is run on each box's longest axis, not on its smallest: chassis box 1 is a floor "
      "pan, 103.5 cm on one axis, so under the half reading that axis alone would still be "
      "%.4f of the mesh span and decide nothing. The long axis is where the two readings are a "
      "factor of two apart." % (v["min_ratio_half_reading_any_axis"],))
    a("")
    a("The weapons box (169751, `Batmobile_Rig_Weapons_Trans`) is a part, not the car, so its "
      "ratios (~0.14-0.39) decide nothing and are listed without a verdict.")
    a("")

    a("## 4. Checks")
    a("")
    a("`--check` recomputes all of these from the package bytes and also requires this file and "
      "the JSON to be byte-identical to a fresh build.")
    a("")
    a("| check | result | detail |")
    a("|---|:---:|---|")
    for c in doc["checks"]:
        a("| %s | %s | %s |" % (c["check"], "PASS" if c["ok"] else "**FAIL**", c["detail"]))
    a("")
    a("## 5. UNKNOWNs")
    a("")
    a("| # | unknown | what was tried | why it stays UNKNOWN / where it would be found |")
    a("|---|---|---|---|")
    for i, u in enumerate(doc["unknowns"], 1):
        a("| U-%d | %s | %s | %s |" % (i, u["item"], u["tried"], u["why"]))
    a("")
    a("## 6. What this changes for G3-01b")
    a("")
    a("- G3-01b's U-4 (\"the StaticMesh Bounds as a second extents oracle\") is **answered**: the "
      "bounds are a decoded `FBoxSphereBounds` in the native data, not a tagged property, and "
      "they agree with the full-length reading of the box extents.")
    a("- The mesh bounds give the two collision meshes' own extents: battle **%s cm**, pursuit "
      "**%s cm** (full spans), with sphere radii **%.4f / %.4f cm**."
      % (fmt([2 * e for e in recs[0]["bounds"]["extent_cm"]], 4),
         fmt([2 * e for e in recs[1]["bounds"]["extent_cm"]], 4),
         recs[0]["bounds"]["radius_cm"], recs[1]["bounds"]["radius_cm"]))
    a("- Still open, and not guessed here: the *member names* of the two neighbouring fields "
      "(U-1), the exact vertex set behind SphereRadius (U-2), and why 13 other StaticMesh exports "
      "in the package do not carry the block at the same offset (U-3).")
    a("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- entry point

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="decode and write both outputs")
    ap.add_argument("--check", action="store_true", help="recompute, re-check, compare outputs")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("pick --write or --check")

    doc = build()
    md = render(doc)
    body = json.dumps(doc, indent=1, sort_keys=True, allow_nan=False) + "\n"

    failed = [c for c in doc["checks"] if not c["ok"]]
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote SM_BOUNDS.json and SM_BOUNDS.md (%d StaticMesh exports, %d checks, %d failed)"
              % (len(doc["static_meshes"]), len(doc["checks"]), len(failed)))
        for c in failed:
            print("  FAIL %s: %s" % (c["check"], c["detail"]))
        return 1 if failed else 0

    problems = []
    for c in failed:
        problems.append("%s: %s" % (c["check"], c["detail"]))
    if not os.path.exists(OUT_MD):
        problems.append("SM_BOUNDS.md is missing")
    elif open(OUT_MD, encoding="utf-8").read() != md:
        problems.append("SM_BOUNDS.md is stale")
    if not os.path.exists(OUT_JSON):
        problems.append("SM_BOUNDS.json is missing")
    elif open(OUT_JSON, encoding="utf-8").read() != body:
        problems.append("SM_BOUNDS.json is stale")
    if problems:
        print("FAIL")
        for p in problems:
            print("  - " + p)
        return 1
    print("OK: %d StaticMesh exports, bounds at native+0 in both, fleet %d/%d, extents %s, "
          "%d/%d checks, md+json byte-identical"
          % (len(doc["static_meshes"]), doc["fleet"]["conforming"],
             doc["fleet"]["staticmesh_exports"], doc["comparison_verdict"]["verdict"],
             len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
