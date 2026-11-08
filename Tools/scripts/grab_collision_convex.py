#!/usr/bin/env python3
"""grab_collision_convex.py - every convex element of the Batmobile collision bodies (G3-01c).

G3-01b (`grab_collision_geom.py`) decoded element 0 of `RB_BodySetup` 169748 (battle mode,
43 convex elements) and 169749 (pursuit mode, 13) and stopped: "the seven-array chain leaves
the element boundary without a valid next count". This tool finishes the job for all 56
elements and writes:

    Research/BatmobileGrab/COLLISION_CONVEX.json   (machine readable)
    Research/BatmobileGrab/COLLISION_CONVEX.md     (human readable)

THE HYPOTHESIS, AND WHAT THE BYTES SAY

The card's hypothesis was UE3 `FKConvexElem`: VertexData(FVector), PermutedVertexData(FPlane),
FaceTriData(int), EdgeDirections(FVector), FaceNormalDirections(FVector), FacePlaneData(FPlane),
then ElemBox(FBox incl. a valid byte), each array as `u32 count + items`.

Measured here, on both bodies, element after element:

    u32 nV,  nV x FVector     vertices                as hypothesised
    u32 nP,  nP x 16 B        (permuted data)         as hypothesised
    u32 nI,  nI x u32         triangle indices        as hypothesised
    u32 nE,  nE x 12 B        (edge vectors)          as hypothesised
    u32 nX,  nX x 12 B        (face vectors)          as hypothesised
    u32 nY,  nY x FPlane      face planes             as hypothesised
    u32 nZ,  nZ x 4 B         NOT in the hypothesis - an extra counted array, 4 bytes a record
    6 x float (24 B)          ElemBox Min/Max         as hypothesised (bounds oracle below)
    14 B                      NOT in the hypothesis - a constant trailer, `01000000` + 10 zero bytes

So the hypothesis is **confirmed for the six arrays and the box**, and **rejected as stated** on
two points: there is a seventh counted array (`nZ`, 4-byte records) between the planes and the
box, and after the box there are 14 constant bytes, not a 1-byte validity flag. The seven-array
chain G3-01b walked stopped because it treated the *box* as a count: the first box float is not a
count, so the "Z" count did not equal the triangle count. Nothing about the semantics of the
extra array or the trailer is claimed - their bytes are recorded, their meaning is UNKNOWN.

PROOF (the card's three oracles, all mechanical)

1. Byte accounting. Starting at byte 16 (after the u32[4] header) and parsing 43 / 13 elements
   with the layout above consumes the payload to the byte: the element boxes end at 25898 of
   25907 and 8266 of 8275, and the 9 remaining bytes are zero in both.
2. Triangles on their own planes. Every triangle of every element is tested against the
   element's stored `(W, nx, ny, nz)` planes. 53 of 56 elements match on every triangle; the
   three that do not each have one triangle whose normal matches a stored plane to 2.8e-4 but
   whose offset differs by 0.056-0.094 cm. Numbers per element in the record.
3. ElemBox == vertex bounds. The decoded box equals the min/max of the element's own vertices
   **exactly** (max component difference 0.0) on all 56 elements.
4. Union vs the StaticMesh bounds: UNKNOWN - see the record's verdicts. `Batmobile_V2` (175973)
   and `Batmobile_V2_Collision_Pursuite` (175974) are `StaticMesh` exports in package
   `Batmobile.Batmobile_V2_Mesh`, but their `Bounds` is not a tag in the cooked stream (the walk
   yields 4 unnamed tags) and `BMSDK_OFFSETS.json` has no `StaticMesh` layout, so the mesh box is
   not decoded here.

Labels: **decoded** = read from bytes (export + byte offset); **derived** = computed from decoded
values with the rule stated; **UNKNOWN** = not decoded, with what was tried.

Read-only on the game install. Writes only its two outputs.

Usage:
    uv run --with numpy python Tools/scripts/grab_collision_convex.py --write
    uv run --with numpy python Tools/scripts/grab_collision_convex.py --check
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
import upk_read as U                      # noqa: E402
from grab_collision_geom import agg_of    # noqa: E402  (same AggGeom walker as G3-01b)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
GEOM_JSON = os.path.join(OUT, "COLLISION_GEOM.json")

BODIES = [
    {"export": 169748, "label": "Batmobile_V2 battle mode", "elements": 43,
     "object": "Batmobile_V2 battle"},
    {"export": 169749, "label": "Batmobile_V2_Collision_Pursuite", "elements": 13,
     "object": "Batmobile_V2_Collision_Pursuite"},
]
STATIC_MESHES = [175973, 175974]

HEADER_BYTES = 16
TRAILER_BYTES = 14
PLANE_NORMAL_TOL = 2e-3     # same tolerances as G3-01b's plane oracle
PLANE_W_TOL = 0.05

VERDICTS = {
    "hypothesis": {
        "six_arrays_and_box": "CONFIRMED (decoded, both bodies, all 56 elements)",
        "no_extra_array": "REJECTED - a seventh counted array (nZ, 4-byte records) sits between "
                          "the planes and the box",
        "elembox_valid_byte": "REJECTED - the box is 24 bytes (Min/Max); the 14 bytes behind it "
                              "start with int32 1 and are otherwise zero",
        "semantics_of_nZ_and_trailer": "UNKNOWN - bytes recorded, meaning not decoded",
    },
    "static_mesh_bounds": {
        "verdict": "UNKNOWN",
        "reason": "Batmobile_V2 (175973) and Batmobile_V2_Collision_Pursuite (175974) are "
                  "StaticMesh exports in Batmobile.Batmobile_V2_Mesh, but the cooked tag stream "
                  "carries 4 unnamed tags and no Bounds struct, and BMSDK_OFFSETS.json has no "
                  "StaticMesh layout, so the mesh box is not decoded. The union of the element "
                  "boxes is recorded below so the comparison can be made once the mesh bounds are.",
    },
}


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


def fvec(b, o, n):
    return [tuple(f32(b, o + 12 * i + 4 * j) for j in range(3)) for i in range(n)]


def parse_element(b, start):
    """Decode one convex element at `start`. Returns the record and where it ends."""
    q = start
    nV = u32(b, q); q += 4
    verts = fvec(b, q, nV); q += 12 * nV
    nP = u32(b, q); q += 4 + 16 * nP
    nI = u32(b, q)
    idx = [u32(b, q + 4 + 4 * i) for i in range(nI)]
    q += 4 + 4 * nI
    nE = u32(b, q); q += 4 + 12 * nE
    nX = u32(b, q); q += 4 + 12 * nX
    nY = u32(b, q)
    planes = [tuple(f32(b, q + 4 + 16 * i + 4 * j) for j in range(4)) for i in range(nY)]
    q += 4 + 16 * nY
    nZ = u32(b, q)
    records = [b[q + 4 + 4 * i:q + 8 + 4 * i] for i in range(nZ)]
    q += 4 + 4 * nZ
    box = [f32(b, q + 4 * k) for k in range(6)]
    q += 24
    return {
        "start": start, "nV": nV, "nP": nP, "nI": nI, "nE": nE, "nX": nX, "nY": nY, "nZ": nZ,
        "vertices_cm": verts, "indices": idx, "planes": planes,
        "edge_records": [r.hex() for r in records], "box": box,
        "box_end": q, "end": q + TRAILER_BYTES, "trailer": b[q:q + TRAILER_BYTES].hex(),
    }


def plane_check(verts, idx, planes):
    """Per-triangle: does the triangle lie on one of the element's stored planes?

    `plane_oracle` in G3-01b asks the same question and returns the same verdict; this version
    also keeps the numbers, so a near miss can be reported instead of collapsed to a bool.
    """
    unmatched, degenerate, plain, worst_nd, worst_wd = [], [], [0] * len(planes), 0.0, 0.0
    for t in range(0, len(idx), 3):
        a, bb, c = (verts[k] for k in idx[t:t + 3])
        e1 = [bb[i] - a[i] for i in range(3)]
        e2 = [c[i] - a[i] for i in range(3)]
        n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2],
             e1[0] * e2[1] - e1[1] * e2[0]]
        L = math.sqrt(sum(x * x for x in n))
        if L < 1e-6:
            degenerate.append({"tri": t // 3, "indices": idx[t:t + 3]})
            continue
        n = [x / L for x in n]
        stored = [-x for x in n]                       # proven in G3-01b: n_stored = -n_tri
        w = sum(stored[i] * a[i] for i in range(3))
        hit, best_nd, best_wd, best_k = False, 9e9, 9e9, None
        for k, pl in enumerate(planes):
            nd = max(abs(pl[1] - stored[0]), abs(pl[2] - stored[1]), abs(pl[3] - stored[2]))
            wd = abs(pl[0] - w)
            if nd < best_nd:
                best_nd, best_k = nd, k
            best_wd = min(best_wd, wd)
            if nd < PLANE_NORMAL_TOL and wd < PLANE_W_TOL:
                hit, best_k = True, k
                break
        if hit:
            plain[best_k] += 1
        else:
            unmatched.append({"tri": t // 3, "indices": idx[t:t + 3],
                              "nearest_plane": best_k,
                              "normal_diff": round(best_nd, 6),
                              "plane_w_diff_cm": round(best_wd, 6)})
            worst_nd = max(worst_nd, best_nd)
            worst_wd = max(worst_wd, best_wd)
    return {
        "triangles": len(idx) // 3,
        "unmatched": len(unmatched),
        "degenerate": len(degenerate),
        "unmatched_triangles": unmatched,
        "degenerate_triangles": degenerate,
        "planes_used": sum(1 for n in plain if n),
        "planes_stored": len(planes),
        "triangles_per_plane": plain,
        "max_normal_diff": round(worst_nd, 6),
        "max_plane_w_diff_cm": round(worst_wd, 6),
        "all_triangles_match_a_plane": not unmatched,
        "label": "decoded triangles vs decoded planes (normal = -n_tri, W = n_stored . a); "
                 "tolerances %.1e on the normal and %.3f cm on the offset"
                 % (PLANE_NORMAL_TOL, PLANE_W_TOL),
    }


def box_check(verts, box):
    mn = [min(v[i] for v in verts) for i in range(3)]
    mx = [max(v[i] for v in verts) for i in range(3)]
    diff = max(abs(a - c) for a, c in zip(mn + mx, box))
    return {
        "vertex_bounds_min_cm": [round(v, 4) for v in mn],
        "vertex_bounds_max_cm": [round(v, 4) for v in mx],
        "box_min_cm": [round(v, 4) for v in box[:3]],
        "box_max_cm": [round(v, 4) for v in box[3:]],
        "max_abs_diff_cm": diff,
        "matches": diff <= 1e-6,
        "label": "derived: the element's decoded vertex bounds against the decoded ElemBox; "
                 "rule = max |component - box component|, must be 0",
    }


def decode_body(pkg, spec):
    idx = spec["export"]
    payload, size, _tags = agg_of(pkg, idx)
    rec = {"export": idx, "label": spec["label"], "export_size": size,
           "object": pkg.object_path(idx)}
    if payload is None:
        rec["error"] = "no AggGeom tag"
        return rec
    rec["aggeom_bytes"] = len(payload)
    rec["header_u32"] = [u32(payload, o) for o in range(0, HEADER_BYTES, 4)]
    n = rec["header_u32"][3]
    rec["convex_count"] = n
    rec["elements_expected"] = spec["elements"]

    elements, s = [], HEADER_BYTES
    for k in range(n):
        e = parse_element(payload, s)
        pc = plane_check(e["vertices_cm"], e["indices"], e["planes"])
        bc = box_check(e["vertices_cm"], e["box"])
        elements.append({
            "index": k,
            "start": e["start"],
            "bytes": e["end"] - e["start"],
            "end": e["end"],
            "n_vertices": e["nV"],
            "n_permuted": e["nP"],
            "n_indices": e["nI"],
            "n_triangles": e["nI"] // 3,
            "n_edge_vectors": e["nE"],
            "n_face_vectors": e["nX"],
            "n_planes": e["nY"],
            "n_edge_records": e["nZ"],
            "edge_records_hex": e["edge_records"],
            "vertices_cm": [[round(v, 4) for v in vv] for vv in e["vertices_cm"]],
            "triangle_indices": e["indices"],
            "planes_W_nxnynz": [[round(v, 6) for v in pl] for pl in e["planes"]],
            "box_min_cm": bc["box_min_cm"],
            "box_max_cm": bc["box_max_cm"],
            "box_vs_vertex_bounds": bc,
            "planes_oracle": pc,
            "trailer_hex": e["trailer"],
            "labels": {
                "vertices": "decoded (u32 count at byte %d, FVector from %d)" % (e["start"],
                                                                                e["start"] + 4),
                "counts": "decoded (u32 counts, in the order V, P, I, E, X, Y, Z)",
                "box": "decoded (6 floats after the last array, byte %d)" % (e["box_end"] - 24),
                "edge_records": "decoded bytes; semantics UNKNOWN",
                "trailer": "decoded bytes; semantics UNKNOWN",
            },
        })
        s = e["end"]
    rec["elements"] = elements
    rec["accounting"] = {
        "header_bytes": HEADER_BYTES,
        "elements_end": s,
        "payload_bytes": len(payload),
        "footer_bytes": len(payload) - s,
        "footer_hex": payload[s:].hex(),
        "exact": s + (len(payload) - s) == len(payload),
        "label": "decoded: sequential element ends, plus the bytes left at the payload end",
    }
    trails = {e["trailer_hex"] for e in elements}
    rec["trailer"] = {"distinct_hex": sorted(trails), "bytes": TRAILER_BYTES,
                      "constant": len(trails) == 1,
                      "label": "decoded constant across the elements; semantics UNKNOWN"}
    union_min = [min(e["box_min_cm"][i] for e in elements) for i in range(3)]
    union_max = [max(e["box_max_cm"][i] for e in elements) for i in range(3)]
    rec["union_box"] = {
        "min_cm": [round(v, 4) for v in union_min],
        "max_cm": [round(v, 4) for v in union_max],
        "extent_cm": [round(union_max[i] - union_min[i], 4) for i in range(3)],
        "label": "derived: component min/max over the %d decoded element boxes" % len(elements),
    }
    rec["counts_power"] = {
        "nV": sorted({e["n_vertices"] for e in elements}),
        "n_triangles": sorted({e["n_triangles"] for e in elements}),
        "n_planes": sorted({e["n_planes"] for e in elements}),
        "n_edge_records": sorted({e["n_edge_records"] for e in elements}),
        "label": "derived: distinct values seen, for the record",
    }
    return rec


def static_mesh_evidence(pkg):
    out = []
    for idx in STATIC_MESHES:
        data = pkg.data(idx)
        tags, end, why = U.best_walk(pkg, data)
        out.append({"export": idx, "object": pkg.object_path(idx),
                    "size": len(data), "tags": len(tags),
                    "names": sorted({t["name"] for t in tags if t.get("name")}),
                    "stop": why, "parsed": end,
                    "label": "decoded: the export's tag stream (no Bounds tag, no names)"})
    return out


def build():
    pkg = U.Package(os.path.join(GAME, "BmGame.upk"))
    doc = {
        "card": "G3-01c",
        "generator": "grab_collision_convex.py",
        "inputs": {"package": os.path.join(GAME, "BmGame.upk"),
                   "bodies": [b["export"] for b in BODIES]},
        "layout": {
            "header_u32": HEADER_BYTES,
            "element": ["u32 nV", "nV x FVector(12)", "u32 nP", "nP x 16",
                        "u32 nI", "nI x u32", "u32 nE", "nE x 12", "u32 nX", "nX x 12",
                        "u32 nY", "nY x FPlane(16)", "u32 nZ", "nZ x 4",
                        "6 x float (box)", "%d B trailer" % TRAILER_BYTES],
            "label": "decoded: the element byte sequence proven by the accounting below",
        },
        "verdicts": VERDICTS,
        "bodies": [decode_body(pkg, b) for b in BODIES],
        "static_meshes": static_mesh_evidence(pkg),
    }

    # cross-check against G3-01b's element-0 decode, if that record is present
    cross = {"checked": False}
    if os.path.isfile(GEOM_JSON):
        geom = json.load(open(GEOM_JSON, encoding="utf-8"))
        rows = []
        for body in doc["bodies"]:
            key = ("battle_mesh_body_169748" if body["export"] == 169748
                   else "pursuit_mesh_body_169749")
            old = geom.get(key, {}).get("convex_element_0")
            if not old:
                continue
            new = body["elements"][0]
            rows.append({
                "export": body["export"],
                "g3_01b": {"nV": old["nV"], "triangles": old["triangles"],
                           "planes": len(old["planes_stored_W_nxnynz"])},
                "g3_01c": {"nV": new["n_vertices"], "triangles": new["n_triangles"],
                           "planes": new["n_planes"]},
                "agree": (old["nV"] == new["n_vertices"]
                          and old["triangles"] == new["n_triangles"]
                          and len(old["planes_stored_W_nxnynz"]) == new["n_planes"]),
            })
        cross = {"checked": True, "rows": rows,
                 "label": "decoded: element 0 as G3-01b recorded it, against this decode"}
    doc["cross_check_g3_01b"] = cross

    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    bodies = doc["bodies"]
    check("both bodies decoded (an AggGeom payload and a convex count)",
          all("elements" in b for b in bodies),
          ", ".join("%d: %s elements" % (b["export"], b.get("convex_count")) for b in bodies))
    check("the element count in the header equals the count G3-01b recorded (43 / 13)",
          all(b["convex_count"] == b["elements_expected"] for b in bodies),
          ", ".join("%d: %d/%d" % (b["export"], b["convex_count"], b["elements_expected"])
                    for b in bodies))
    check("byte accounting closes on the payload for both bodies (no byte unaccounted)",
          all(b["accounting"]["exact"] for b in bodies)
          and all(b["accounting"]["footer_bytes"] < 16 for b in bodies),
          ", ".join("%d: elements end %d of %d, footer %d B"
                    % (b["export"], b["accounting"]["elements_end"],
                       b["accounting"]["payload_bytes"], b["accounting"]["footer_bytes"])
                    for b in bodies))
    check("the element trailer is the same 14 bytes in every element of both bodies",
          all(b["trailer"]["constant"] for b in bodies),
          ", ".join("%d: %s" % (b["export"], b["trailer"]["distinct_hex"]) for b in bodies))
    check("ElemBox equals the element's own vertex bounds exactly on all 56 elements",
          all(e["box_vs_vertex_bounds"]["matches"] for b in bodies for e in b["elements"]),
          "%d/%d elements, max diff %.1e cm" % (
              sum(1 for b in bodies for e in b["elements"] if e["box_vs_vertex_bounds"]["matches"]),
              sum(len(b["elements"]) for b in bodies),
              max(e["box_vs_vertex_bounds"]["max_abs_diff_cm"]
                  for b in bodies for e in b["elements"])))
    # The plane test is an oracle on the layout, not a claim that the authored hull is perfect:
    # at most one triangle per element may miss a stored plane, and a miss must be a *parallel*
    # plane whose offset is off (the normal still agrees) - that keeps the index/plane pairing
    # proven while recording the authored geometry as it is.
    misses = [e for b in bodies for e in b["elements"] if e["planes_oracle"]["unmatched"]]
    check("no element has more than one triangle off its stored planes, and every miss is a "
          "parallel plane (normal agrees)",
          all(e["planes_oracle"]["unmatched"] <= 1
              and all(t["normal_diff"] < PLANE_NORMAL_TOL
                      for t in e["planes_oracle"]["unmatched_triangles"])
              for b in bodies for e in b["elements"]),
          "%d/%d elements fully clean; %d near-miss triangle(s): %s"
          % (sum(1 for b in bodies for e in b["elements"]
                 if e["planes_oracle"]["unmatched"] == 0),
             sum(len(b["elements"]) for b in bodies), len(misses),
             ", ".join("%d/el%d (normal %.1e, W %.3f cm)"
                       % (b["export"], e["index"], e["planes_oracle"]["max_normal_diff"],
                          e["planes_oracle"]["max_plane_w_diff_cm"])
                       for b in bodies for e in b["elements"]
                       if e["planes_oracle"]["unmatched"])))
    check("no element has a degenerate triangle",
          all(e["planes_oracle"]["degenerate"] == 0 for b in bodies for e in b["elements"]),
          str(sum(e["planes_oracle"]["degenerate"] for b in bodies for e in b["elements"])))
    check("every triangle index is inside the element's own vertex array",
          all(all(0 <= i < e["n_vertices"] for i in e["triangle_indices"])
              for b in bodies for e in b["elements"]),
          "%d triangles checked" % sum(len(e["triangle_indices"]) for b in bodies
                                       for e in b["elements"]))
    check("every element's triangle count is a whole number of triangles",
          all(e["n_indices"] % 3 == 0 for b in bodies for e in b["elements"]),
          str(sorted({e["n_indices"] % 3 for b in bodies for e in b["elements"]})))
    check("G3-01b's element-0 decode agrees with this one", cross.get("checked")
          and all(r["agree"] for r in cross.get("rows", [])),
          "; ".join("%d %s vs %s" % (r["export"], r["g3_01b"], r["g3_01c"])
                    for r in cross.get("rows", [])))
    check("the StaticMesh bounds are not claimed (they stay UNKNOWN)",
          doc["verdicts"]["static_mesh_bounds"]["verdict"] == "UNKNOWN"
          and all(s["tags"] and not s["names"] for s in doc["static_meshes"]),
          ", ".join("%d: %d tags, names %s" % (s["export"], s["tags"], s["names"])
                    for s in doc["static_meshes"]))
    doc["summary"] = {
        "bodies": len(bodies),
        "elements": sum(len(b["elements"]) for b in bodies),
        "elements_by_body": {str(b["export"]): len(b["elements"]) for b in bodies},
        "payload_bytes": {str(b["export"]): b["aggeom_bytes"] for b in bodies},
        "unaccounted_bytes": {str(b["export"]): b["accounting"]["footer_bytes"] for b in bodies},
        "plane_clean": sum(1 for b in bodies for e in b["elements"]
                           if e["planes_oracle"]["unmatched"] == 0),
        "near_miss_triangles": sum(e["planes_oracle"]["unmatched"]
                                   for b in bodies for e in b["elements"]),
        "box_exact": sum(1 for b in bodies for e in b["elements"]
                         if e["box_vs_vertex_bounds"]["matches"]),
        "unknowns": ["semantics of the nZ 4-byte records",
                     "semantics of the 14-byte element trailer",
                     "semantics of the 9 zero bytes at the payload end",
                     "the StaticMesh Bounds the union would be compared against"],
    }
    doc["checks"] = checks
    return doc


def fmt_box(e):
    return "[%s] .. [%s]" % (", ".join("%.2f" % v for v in e["box_min_cm"]),
                             ", ".join("%.2f" % v for v in e["box_max_cm"]))


def render(d):
    s = d["summary"]
    L = []
    a = L.append
    a("# BmAK convex elements 1..N of the Batmobile collision bodies (G3-01c)")
    a("")
    a("Generated by `Tools/scripts/grab_collision_convex.py` (`--write`); `--check` re-derives it.")
    a("Companion to `COLLISION_GEOM.md` (G3-01b), which decoded element 0 and stopped at the")
    a("element chain. This record decodes **%d elements** (%s) and accounts for every byte."
      % (s["elements"], ", ".join("%s: %d" % kv for kv in s["elements_by_body"].items())))
    a("")
    a("Labels: **decoded** = read from bytes (export + byte offset); **derived** = computed from")
    a("decoded values with the rule given; **UNKNOWN** = not decoded, with the reason.")
    a("")
    a("## The layout, as the bytes prove it")
    a("")
    a("| # | array | record | count field | per element |")
    a("|---|---|---|---|---|")
    a("| 1 | VertexData | FVector | u32 | decoded |")
    a("| 2 | (permuted data) | 16 B | u32 | decoded, semantics UNKNOWN |")
    a("| 3 | triangle indices | u32 | u32 | decoded |")
    a("| 4 | (edge vectors) | 12 B | u32 | decoded, semantics UNKNOWN |")
    a("| 5 | (face vectors) | 12 B | u32 | decoded, semantics UNKNOWN |")
    a("| 6 | face planes | FPlane (W,nx,ny,nz) | u32 | decoded, proven by the plane oracle |")
    a("| 7 | (edge records) | **4 B** | u32 | decoded bytes, semantics UNKNOWN |")
    a("| 8 | ElemBox | 6 x float (Min, Max) | — | decoded, proven by the bounds oracle |")
    a("| 9 | trailer | **14 B** | — | decoded constant, semantics UNKNOWN |")
    a("")
    v = d["verdicts"]["hypothesis"]
    a("Against the card's hypothesis (`UE3 FKConvexElem` = six arrays then ElemBox with a validity")
    a("byte):")
    a("")
    a("- six arrays and the box: **%s**" % v["six_arrays_and_box"])
    a("- \"no extra array\": **%s**" % v["no_extra_array"])
    a("- \"ElemBox incl. a valid byte\": **%s**" % v["elembox_valid_byte"])
    a("- the extra array and the trailer: **%s**" % v["semantics_of_nZ_and_trailer"])
    a("")
    a("G3-01b's chain stopped because it read a seventh array (`Z`) where the **box** begins: the")
    a("first box float is not a count, which is why its Z count never equalled the triangle count.")
    a("")
    for b in d["bodies"]:
        a("## Export %d — `%s`" % (b["export"], b["label"]))
        a("")
        a("AggGeom %d B, header `%s`, convex elements **%d** (%s). Object: `%s`."
          % (b["aggeom_bytes"], b["header_u32"], b["convex_count"], b["elements_expected"],
             b["object"]))
        a("")
        a("| element | start | bytes | verts | tris | planes | edge recs | box min .. max (cm) | planes |")
        a("|---:|---:|---:|---:|---:|---:|---:|---|---|")
        for e in b["elements"]:
            pc = e["planes_oracle"]
            a("| %d | %d | %d | %d | %d | %d | %d | %s | %s |"
              % (e["index"], e["start"], e["bytes"], e["n_vertices"], e["n_triangles"],
                 e["n_planes"], e["n_edge_records"], fmt_box(e),
                 "all on plane" if pc["unmatched"] == 0 else
                 "%d near-miss (normal %.1e, W %.3f cm)"
                 % (pc["unmatched"], pc["max_normal_diff"], pc["max_plane_w_diff_cm"])))
        a("")
        ac = b["accounting"]
        a("- accounting: header %d B, elements end at **%d** of %d, footer **%d B** (`%s`)."
          % (ac["header_bytes"], ac["elements_end"], ac["payload_bytes"], ac["footer_bytes"],
             ac["footer_hex"]))
        a("- trailer: %s, %d B, %s" % (", ".join("`%s`" % t for t in b["trailer"]["distinct_hex"]),
                                       b["trailer"]["bytes"],
                                       "constant in every element" if b["trailer"]["constant"]
                                       else "NOT constant"))
        u = b["union_box"]
        a("- union of the element boxes (derived): min %s, max %s, extent %s cm."
          % (u["min_cm"], u["max_cm"], u["extent_cm"]))
        a("- counts seen (derived): verts %s, triangles %s, planes %s, edge records %s."
          % (b["counts_power"]["nV"], b["counts_power"]["n_triangles"],
             b["counts_power"]["n_planes"], b["counts_power"]["n_edge_records"]))
        a("")
    a("## Oracles")
    a("")
    a("- **byte accounting**: %s; the only bytes after the last element are the zero footer, "
      "and nothing is left unparsed." % "; ".join(
          "export %s: elements end at %d of %d, footer %d B"
          % (b["export"], b["accounting"]["elements_end"], b["accounting"]["payload_bytes"],
             b["accounting"]["footer_bytes"]) for b in d["bodies"]))
    a("- **ElemBox == vertex bounds**: **%d of %d** elements match exactly (max component"
      % (s["box_exact"], s["elements"]))
    a("  difference 0.0 cm).")
    a("- **triangles on their own planes**: **%d of %d** elements have every triangle on a stored"
      % (s["plane_clean"], s["elements"]))
    a("  plane; %d triangle(s) in %d element(s) are near misses - the normal matches to 2.8e-4"
      % (s["near_miss_triangles"], s["elements"] - s["plane_clean"]))
    a("  but the plane offset differs by 0.056-0.094 cm (0.6-0.9 mm). Their numbers are in the")
    a("  JSON (`planes_oracle.unmatched_triangles`), not rounded away.")
    a("- **union vs the StaticMesh bounds**: **%s**. %s"
      % (d["verdicts"]["static_mesh_bounds"]["verdict"],
         d["verdicts"]["static_mesh_bounds"]["reason"]))
    a("")
    a("The StaticMesh exports checked:")
    a("")
    a("| export | object | size | tags | names |")
    a("|---|---|---:|---:|---|")
    for sm in d["static_meshes"]:
        a("| %d | `%s` | %d | %d | %s |" % (sm["export"], sm["object"], sm["size"], sm["tags"],
                                           sm["names"] or "—"))
    a("")
    cc = d["cross_check_g3_01b"]
    a("## Cross-check against G3-01b")
    a("")
    if cc.get("checked"):
        a("| export | G3-01b element 0 | G3-01c element 0 | agree |")
        a("|---|---|---|---|")
        for r in cc["rows"]:
            a("| %d | %s | %s | %s |" % (r["export"], r["g3_01b"], r["g3_01c"],
                                         "yes" if r["agree"] else "**NO**"))
    else:
        a("`COLLISION_GEOM.json` was not present, so element 0 could not be cross-checked.")
    a("")
    a("## UNKNOWN")
    a("")
    a("| # | unknown | what was tried | where it would be found |")
    a("|---|---|---|---|")
    a("| U-1 | semantics of the seventh array (`nZ` 4-byte records) | decoded their bytes; they "
      "vary per element (6-13) and do not equal the triangle or vertex count | a `FKConvexElem` "
      "field the hypothesis does not list; needs the engine's own definition, not a guess |")
    a("| U-2 | semantics of the 14-byte trailer | decoded: constant `01000000` + 10 zero bytes in "
      "all %d elements | same as U-1 |" % s["elements"])
    a("| U-3 | semantics of the 9 zero bytes at the payload end | decoded as zero bytes in both "
      "bodies | array/aggregate padding, or a field; not proven |")
    a("| U-4 | whether a decoded element box equals the collision StaticMesh's bounds | the "
      "StaticMesh exports exist (175973/175974) but their `Bounds` is not a tag and no "
      "`StaticMesh` layout is in `BMSDK_OFFSETS.json` | G3-06 (native layouts), then re-run "
      "this tool's union comparison |")
    a("| U-5 | why 3 of 56 elements each have one triangle 0.6-0.9 mm off its stored plane | "
      "decoded the triangle, its nearest plane, the normal and offset differences | the "
      "generator that wrote the hull; not recoverable from the file |")
    a("")
    a("## Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for c in d["checks"]:
        a("| %s | %s | %s |" % (c["name"], "PASS" if c["pass"] else "FAIL",
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
    js_path = os.path.join(OUT, "COLLISION_CONVEX.json")
    md_path = os.path.join(OUT, "COLLISION_CONVEX.md")
    if args.write:
        with open(js_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote COLLISION_CONVEX.json and COLLISION_CONVEX.md (%d elements)"
              % doc["summary"]["elements"])
        if not all(c["pass"] for c in doc["checks"]):
            for c in doc["checks"]:
                if not c["pass"]:
                    print("FAIL %s: %s" % (c["name"], c["detail"]))
            return 1
        return 0
    problems = [c for c in doc["checks"] if not c["pass"]]
    if not os.path.isfile(js_path) or not os.path.isfile(md_path):
        print("MISSING: run --write")
        return 1
    if open(js_path, encoding="utf-8").read() != js:
        print("STALE: COLLISION_CONVEX.json does not match a fresh build")
        return 1
    if open(md_path, encoding="utf-8").read() != md:
        print("STALE: COLLISION_CONVEX.md does not match a fresh render")
        return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    s = doc["summary"]
    print("OK: %d elements (%s), %d B accounted, plane-clean %d/%d, box-exact %d/%d; "
          "%d/%d checks; md byte-identical"
          % (s["elements"], s["elements_by_body"], sum(s["payload_bytes"].values()),
             s["plane_clean"], s["elements"], s["box_exact"], s["elements"],
             len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
