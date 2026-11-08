#!/usr/bin/env python3
"""grab_collision_geom.py - collision GEOMETRY of the drivable Batmobile (G3-01b).

G3-01 (grab_collision.py) found the RB_BodySetup / AggGeom references and stopped at
"native binary". This script decodes what can be proven from the bytes and writes:

    Research/BatmobileGrab/COLLISION_GEOM.json   (machine readable)
    Research/BatmobileGrab/COLLISION_GEOM.md     (human readable)

Sources (cooked packages only, nothing from engine defaults):
    BmGame.upk  RB_BodySetup 169748 (Batmobile_V2 battle-mode mesh) and 169749 (pursuit mesh)
    BmGame.upk  PhysicsAsset 158266 Physics.Batmobile_V3_Physics and its children:
                RB_BodySetup 169750 (Batmobile_Chassis), 169751 (Batmobile_Rig_Weapons_Trans),
                RB_ConstraintSetup 171462
    Research/BatmobileGrab/SOCKETS_JC3.json  body_box (oracle for the chassis box size)

Labels on every value:
    decoded   read from bytes (export, byte offset, tag or record kind)
    derived   computed from decoded values; the rule is stated next to it
    UNKNOWN   not decoded; the reason says what was tried

AggGeom layout that is proven here
    u32 sphere_count, u32 box_count, u32 sphyl_count?, u32 convex_count|word3   (16-byte header)
    Convex element 0 (proven: every triangle's plane matches a stored plane):
        u32 n, n x FVector (12 B)            VertexData
        u32 n, n x 16 B                      block A (values are vertex components; semantic UNKNOWN)
        u32 n, n x u32                       triangle indices (3 per triangle)
        then the layout is NOT proven beyond the planes (see the chain notes)
    Planes (proven): 16 B records stored as (W, nx, ny, nz) with n . x = W on the face.
    Box elements (wreck and chassis): extents are the tagged floats at logical offsets
    0x40/0x44/0x48 (FloatProperty tags "04 00 40 00" ...), centre = 12 bytes before the first tag
    (grab_physics.py rule, proven on the 128 wreck records only).

Usage:
    uv run --with numpy --with pillow python Tools/scripts/grab_collision_geom.py --write
    uv run --with numpy --with pillow python Tools/scripts/grab_collision_geom.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
SOCKETS = os.path.join(OUT, "SOCKETS_JC3.json")

EXT_RE = re.compile(rb"\x04\x00\x40\x00(.{4})\x04\x00\x44\x00(.{4})\x04\x00\x48\x00(.{4})", re.S)


def agg_of(pkg, idx):
    """-> (bytes of AggGeom payload, export size) for an RB_BodySetup export index."""
    data = pkg.data(idx)
    tags, _end, _why = U.walk_tags(pkg, data)
    agg = [t for t in tags if t.get("name") == "AggGeom"]
    if not agg:
        return None, len(data), tags
    a = agg[0]
    return data[a["at"]:a["at"] + a["size"]], len(data), tags


def header(b):
    return [struct.unpack_from("<I", b, o)[0] for o in range(0, 16, 4)]


def boxes_tagged(b):
    """Box extents from the tagged-float tail, centre 12 B before the first tag (grab_physics rule)."""
    out = []
    for m in EXT_RE.finditer(b):
        # the regex matched 3 tagged floats at 0x40/0x44/0x48 (4-byte tag header, then the value)
        ext = [struct.unpack("<f", m.group(i))[0] for i in (1, 2, 3)]
        centre = list(struct.unpack_from("<3f", b, m.start() - 12)) if m.start() >= 12 else None
        out.append({"at": m.start(), "extents_cm": [round(v, 3) for v in ext],
                    "centre_cm": [round(v, 3) for v in centre] if centre else None,
                    "label": "decoded (extents: tagged floats 0x40/0x44/0x48 at byte %d; "
                             "centre: 12 bytes before the tag stream, grab_physics rule, "
                             "rotation not decoded)" % m.start()})
    return out


def read_u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def read_f(b, o):
    return struct.unpack_from("<f", b, o)[0]


def convex0(b):
    """Decode convex element 0 (16 header bytes, then VertexData, block A, indices).
    Returns verts, A, indices, and the offsets, plus the plane-oracle result."""
    p = 16
    n = read_u32(b, p); p += 4
    verts = [tuple(read_f(b, p + 12 * i + 4 * j) for j in range(3)) for i in range(n)]
    p += 12 * n
    na = read_u32(b, p); p += 4
    blockA = [tuple(read_f(b, p + 16 * i + 4 * j) for j in range(4)) for i in range(na)]
    p += 16 * na
    ni = read_u32(b, p); p += 4
    idx = [read_u32(b, p + 4 * i) for i in range(ni)]
    p += 4 * ni
    return {"nV": n, "verts_offset": 20, "verts": verts, "nA": na, "blockA": blockA,
            "nI": ni, "indices": idx, "indices_end": p}


def plane_oracle(verts, idx, planes):
    """Each triangle's face plane must match a stored (W, n) plane: n_stored = -n_tri, W = n_stored . a."""
    res = []
    for t in range(0, len(idx), 3):
        a, bb, c = (verts[k] for k in idx[t:t + 3])
        e1 = [bb[i] - a[i] for i in range(3)]
        e2 = [c[i] - a[i] for i in range(3)]
        nrm = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
        L = math.sqrt(sum(x * x for x in nrm)) or 1.0
        nrm = [x / L for x in nrm]
        stored = [-x for x in nrm]
        W = sum(stored[i] * a[i] for i in range(3))
        hit = None
        for k, (pw, px, py, pz) in enumerate(planes):
            if abs(px - stored[0]) < 2e-3 and abs(py - stored[1]) < 2e-3 and abs(pz - stored[2]) < 2e-3 \
                    and abs(pw - W) < 0.05:
                hit = k
                break
        res.append({"tri": t // 3, "indices": idx[t:t + 3], "plane_index": hit})
    unmatched = [r for r in res if r["plane_index"] is None]
    used = sorted({r["plane_index"] for r in res if r["plane_index"] is not None})
    return {"triangles": len(res), "unmatched": len(unmatched), "planes_used": used,
            "planes_stored": len(planes), "all_triangles_match_a_plane": not unmatched}


def planes_after(b, o):
    """Read a count + 16-byte plane block at byte o (count-prefixed)."""
    n = read_u32(b, o)
    return [tuple(read_f(b, o + 4 + 16 * i + 4 * j) for j in range(4)) for i in range(n)], o + 4 + 16 * n


def chain_counts(b):
    """Byte chain of element 0 as seen by the decoder. Used only to LOCATE the plane block (Y)."""
    p = 16
    marks = []
    for name, esz in (("V", 12), ("A", 16), ("I", 4), ("E", 12), ("X", 12), ("Y", 16), ("Z", 4)):
        n = read_u32(b, p)
        marks.append({"block": name, "count": n, "at": p})
        p += 4 + esz * n
    marks.append({"next_at": p, "next_u32": read_u32(b, p)})
    return marks


def decode_static(pkg, idx, label):
    b, size, _tags = agg_of(pkg, idx)
    rec = {"export": idx, "label": label, "export_size": size}
    if b is None:
        rec["error"] = "no AggGeom tag"
        return rec
    hdr = header(b)
    rec["aggeom_bytes"] = len(b)
    rec["header_u32"] = {"words": hdr,
                         "label": "decoded (words 0..3 of the AggGeom payload); "
                                  "word 0 = 0 sphere count, word 3 = convex count when it is small"}
    if hdr[3] and hdr[3] < 256:
        c0 = convex0(b)
        marks = chain_counts(b)
        Y = [m for m in marks if m.get("block") == "Y"][0]
        planes, _ = planes_after(b, Y["at"])
        rec["convex_element_0"] = {
            "nV": c0["nV"], "vertices_cm": [[round(v, 4) for v in vv] for vv in c0["verts"]],
            "vertex_label": "decoded (u32 count at byte 16, FVector records from byte 20)",
            "triangle_indices": c0["indices"], "nI": c0["nI"],
            "triangles": c0["nI"] // 3,
            "triangle_label": "decoded (u32 count then u32 indices, as the chain at byte %d)" % (c0["indices_end"] - 4 * c0["nI"] - 4),
            "planes_stored_W_nxnynz": [[round(v, 4) for v in pl] for pl in planes],
            "planes_label": "decoded block Y (count at byte %d); layout (W,nx,ny,nz) proven by the oracle below"
                            % Y["at"],
            "oracle_planes": plane_oracle(c0["verts"], c0["indices"], planes),
            "blockA_count": c0["nA"],
            "blockA_label": "decoded count; values are vertex components, semantic UNKNOWN",
            "chain_marks": marks,
            "chain_status": "UNKNOWN beyond element 0: the seven-array chain (V,A,I,E,X,Y,Z) leaves the "
                            "element boundary without a valid next count (checked for 169749 at byte 644; "
                            "for 169748 the Z count does not equal the triangle count), so elements 1..N "
                            "are not decoded.",
        }
        if hdr[3] != 1:
            rec["convex_count_label"] = "decoded (header word 3); element count taken from it"
    else:
        rec["header_note"] = ("header word 3 = %d is not a convex count (word 1 = %d boxes, word 2 = %d)"
                              % (hdr[3], hdr[1], hdr[2]))
        rec["boxes"] = boxes_tagged(b)
        rec["box_count_word"] = hdr[1]
        rec["sphyl_word"] = hdr[2]
        rec["sphyl_label"] = "UNKNOWN: word 2 = 10 on all box bodies (meaning not decoded)"
    return rec


def physics_asset(pkg):
    pa_idx = 158266
    tags, _e, _w = U.walk_tags(pkg, pkg.data(pa_idx))
    arrays = {}
    for t in tags:
        if t.get("type") == "ArrayProperty":
            arrays[t["name"]] = t
    data = pkg.data(pa_idx)
    out = {"export": pa_idx, "name": pkg.object_path(pa_idx), "size": len(data)}

    # the array payloads sit behind their tag; read count then u32 object indices
    def array_items(name):
        for t in tags:
            if t.get("name") == name and t.get("type") == "ArrayProperty":
                payload_at = t["at"]
                size = t["size"]
                n = read_u32(data, payload_at)
                items = [read_u32(data, payload_at + 4 + 4 * i) for i in range(n)]
                return items, size
        return None, None

    body_items, body_sz = array_items("BodySetup")
    cons_items, cons_sz = array_items("ConstraintSetup")
    bb_items, bb_sz = array_items("BoundsBodies")
    out["BodySetup"] = {"refs": body_items, "payload_bytes": body_sz,
                        "label": "decoded (ArrayProperty BodySetup: count + u32 object indices)"}
    out["ConstraintSetup"] = {"refs": cons_items, "payload_bytes": cons_sz,
                              "label": "decoded (ArrayProperty ConstraintSetup)"}
    out["BoundsBodies"] = {"refs": bb_items, "payload_bytes": bb_sz,
                           "label": "decoded (ArrayProperty BoundsBodies: body indices)"}
    bodies = []
    for i in body_items or []:
        bodies.append(pa_body(pkg, i))
    out["bodies"] = bodies
    out["constraints"] = [pa_constraint(pkg, i) for i in cons_items or []]
    return out


def pa_body(pkg, idx):
    b, size, tags = agg_of(pkg, idx)
    bone = [t.get("value") for t in tags if t.get("type") == "NameProperty"]
    outer = [t for t in tags if t.get("type") == "ObjectNCRProperty"]
    rec = {"export": idx, "object": pkg.object_path(idx), "size": size,
           "bone": bone[0] if bone else None,
           "bone_label": "decoded (NameProperty in the BodySetup's tags)",
           "aggeom_bytes": len(b) if b else None}
    if b:
        g = decode_static(pkg, idx, "PA body")
        for k in ("export", "export_size", "label"):
            g.pop(k, None)
        rec["geometry"] = g
    if outer:
        rec["object_ref"] = {"value": outer[0].get("value"), "path": outer[0].get("ref")}
    return rec


def pa_constraint(pkg, idx):
    tags, _e, _w = U.walk_tags(pkg, pkg.data(idx))
    rec = {"export": idx, "object": pkg.object_path(idx), "size": len(pkg.data(idx)), "fields": []}
    for t in tags:
        if t.get("type") == "NameProperty":
            rec["fields"].append({"offset": t.get("offset"), "value": t.get("value"),
                                  "label": "decoded (NameProperty at byte %d)" % t.get("offset")})
        elif t.get("type") == "VectorProperty":
            rec["fields"].append({"offset": t.get("offset"), "value": t.get("value"),
                                  "label": "decoded (VectorProperty at byte %d); field name UNKNOWN "
                                           "(no RB_ConstraintSetup layout in BMSDK_OFFSETS)" % t.get("offset")})
    return rec


def bounds_check(pa):
    """Oracle: chassis box extents (cm, read as FULL lengths) against the body box derived from SOCKETS_JC3."""
    try:
        sk = json.load(open(SOCKETS, encoding="utf-8"))
    except Exception as ex:  # pragma: no cover
        return {"error": str(ex)}
    bb = sk["body_box"]
    span_m = [round(bb["max_m"][k] - bb["min_m"][k], 3) for k in range(3)]
    chassis = [b for b in pa["bodies"] if b.get("bone") == "Batmobile_Chassis"]
    if not chassis or "geometry" not in chassis[0] or not chassis[0]["geometry"].get("boxes"):
        return {"error": "no chassis boxes"}
    ext = chassis[0]["geometry"]["boxes"][0]["extents_cm"]
    full_m = sorted(round(v / 100.0, 3) for v in ext)
    return {"body_box_span_m_xyz_jc3": span_m,
            "chassis_box0_extents_cm": ext,
            "chassis_box0_full_m_sorted": full_m,
            "body_box_span_m_sorted": sorted(span_m),
            "label": "derived: compares sorted spans. If extents are FULL lengths the sorted spans agree "
                     "within about 0.25 m (6.9/3.75/2.07 vs 7.0/3.5/2.27); if they were HALF lengths the box "
                     "would be about 13.8 m long, which the body box does not show. Frame axes are not proven."}


def build():
    import upk_read
    base = upk_read.Package(os.path.join(GAME, "BmGame.upk"))
    out = {"card": "G3-01b", "generator": "grab_collision_geom.py",
           "inputs": {"bmgame": os.path.join(GAME, "BmGame.upk"), "sockets_jc3": SOCKETS}}
    out["battle_mesh_body_169748"] = decode_static(base, 169748, "Batmobile_V2 battle")
    out["pursuit_mesh_body_169749"] = decode_static(base, 169749, "Batmobile_V2_Collision_Pursuite")
    pa = physics_asset(base)
    out["physics_asset_158266"] = pa
    out["oracle_chassis_box_vs_body_box"] = bounds_check(pa)
    out["cylinder_names"] = {
        "verdict": "UNKNOWN",
        "reason": "BMSDK_OFFSETS.json has no CylinderComponent class; the 78.0 / 175.0 floats are not "
                  "named by any decoded layout, so radius vs height is not proven."}
    out["active_mesh_per_mode"] = {
        "verdict": "UNKNOWN",
        "reason": "BatmanVsBatmobileCollisionMode (BMSDK layout offset 5895) is not serialised in the "
                  "archetype, the Startup CDO or the BmGame base template walked by grab_collision.py; "
                  "no state function was decoded."}
    return out


def render(d):
    L = []
    L.append("# COLLISION_GEOM.md - drivable Batmobile collision geometry (G3-01b)\n")
    L.append("Generated by `Tools/scripts/grab_collision_geom.py` (`--write`). Do not edit by hand; "
             "`--check` re-derives it.\n")
    L.append("Labels: **decoded** = read from bytes; **derived** = computed from decoded values (rule given); "
             "**UNKNOWN** = not decoded (reason given).\n")

    def body_block(title, rec):
        L.append("## " + title + "\n")
        L.append("- export %d, `%s`, AggGeom %s bytes, header words %s (%s)" % (
            rec["export"], rec.get("label", ""), rec.get("aggeom_bytes"),
            rec["header_u32"]["words"], rec["header_u32"]["label"]))
        if "convex_element_0" in rec:
            c = rec["convex_element_0"]
            L.append("- convex element 0 (decoded): %d vertices (%s); %d triangles (%s); plane block count %d (%s)"
                     % (c["nV"], c["vertex_label"], c["triangles"], c["triangle_label"],
                        len(c["planes_stored_W_nxnynz"]), c["planes_label"]))
            o = c["oracle_planes"]
            L.append("- oracle (plane check): %d triangles, %d unmatched, planes used %s of %d stored -> %s"
                     % (o["triangles"], o["unmatched"], o["planes_used"], o["planes_stored"],
                        "all triangles lie on a stored plane" if o["all_triangles_match_a_plane"] else "FAILED"))
            L.append("- block A count %d: %s" % (c["blockA_count"], c["blockA_label"]))
            L.append("- status: " + c["chain_status"])
        if "boxes" in rec:
            for k, bx in enumerate(rec["boxes"]):
                L.append("- box %d (decoded extents %s cm; centre %s cm; %s)" % (
                    k, bx["extents_cm"], bx["centre_cm"], bx["label"]))
        if "header_note" in rec:
            L.append("- note: " + rec["header_note"] + "; " + rec.get("sphyl_label", ""))
        L.append("")

    body_block("Battle-mode mesh: RB_BodySetup 169748 (Batmobile_V2)", d["battle_mesh_body_169748"])
    body_block("Pursuit-mode mesh: RB_BodySetup 169749 (Batmobile_V2_Collision_Pursuite)",
               d["pursuit_mesh_body_169749"])

    pa = d["physics_asset_158266"]
    L.append("## PhysicsAsset Physics.Batmobile_V3_Physics (158266)\n")
    L.append("- decoded: BodySetup refs %s, ConstraintSetup refs %s, BoundsBodies %s (ArrayProperty payloads)"
             % (pa["BodySetup"]["refs"], pa["ConstraintSetup"]["refs"], pa["BoundsBodies"]["refs"]))
    L.append("- bounds: the Bounds array (72 B) is NOT decoded (UNKNOWN field layout).\n")
    for b in pa["bodies"]:
        L.append("- body export %s bone `%s`, AggGeom %s bytes (decoded)" % (b["export"], b["bone"], b.get("aggeom_bytes")))
        g = b.get("geometry", {})
        if "boxes" in g:
            for k, bx in enumerate(g["boxes"]):
                L.append("  - box %d: extents %s cm, centre %s cm (%s)" % (k, bx["extents_cm"], bx["centre_cm"], bx["label"]))
        if "convex_element_0" in g:
            L.append("  - convex element 0: %d vertices, oracle %s" % (g["convex_element_0"]["nV"],
                                                                     g["convex_element_0"]["oracle_planes"]["all_triangles_match_a_plane"]))
    for c in pa["constraints"]:
        L.append("- constraint export %s (RB_ConstraintSetup): " % c["export"] + "; ".join(
            "%s=%s" % (f["offset"], f["value"]) for f in c["fields"]) + " (offset names UNKNOWN)")
    L.append("")
    o = d["oracle_chassis_box_vs_body_box"]
    L.append("## Oracle: chassis box vs body box\n")
    L.append("- " + str(o.get("label", o)) + "\n")
    L.append("- chassis box 0 extents (cm): %s; body box spans (m): %s" % (
        o.get("chassis_box0_extents_cm"), o.get("body_box_span_m_xyz_jc3")))
    L.append("")
    L.append("## Verdicts\n")
    L.append("- cylinder names (78.0 / 175.0): **%s** - %s" % (d["cylinder_names"]["verdict"], d["cylinder_names"]["reason"]))
    L.append("- active mesh per mode: **%s** - %s" % (d["active_mesh_per_mode"]["verdict"], d["active_mesh_per_mode"]["reason"]))
    L.append("")
    L.append("## UNKNOWN\n")
    L.append("- AggGeom elements 1..N of the battle and pursuit bodies: the element chain does not close.")
    L.append("- Block A (16 B records, count per element) and the extra arrays E, X, Z: semantic UNKNOWN.")
    L.append("- Box rotations (the chassis TM is not decoded; the centre rule is proven only on the wreck).")
    L.append("- Actor frame to PSK frame link: UNKNOWN; JC3 positions stay conditional (see SOCKETS_JC3.json).")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    d = build()
    js = json.dumps(d, indent=1, sort_keys=True, default=str) + "\n"
    md = render(d)
    js_path = os.path.join(OUT, "COLLISION_GEOM.json")
    md_path = os.path.join(OUT, "COLLISION_GEOM.md")
    if args.check:
        ok = True
        for path, want in ((js_path, js), (md_path, md)):
            have = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if have != want:
                print("!! %s is stale" % os.path.basename(path), file=sys.stderr)
                ok = False
        print("COLLISION_GEOM.md/json current" if ok else "regenerate with --write")
        return 0 if ok else 1
    if args.write:
        open(js_path, "w", encoding="utf-8", newline="\n").write(js)
        open(md_path, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote COLLISION_GEOM.md and .json")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
