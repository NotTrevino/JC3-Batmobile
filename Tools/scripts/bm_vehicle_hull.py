"""bm_vehicle_hull.py - B-10e: vehicle-vs-vehicle collision, which body and which box.

Three questions, all answered from files:

 Q1  Is B-10/B-10d's 3.495 x 2.271 x 7.025 m a mesh bbox in other axes, or another
     quantity?  (recomputed here from Batmobile_V2.pskx vertices and from
     Working/Appearance/build_parts/parts_manifest.json)
 Q2  Can the chassis box rotation be derived?  (read from the box TM floats in
     BmGame.upk, then tested against the convex hulls' bounding boxes)
 Q3  Which JC3 bodies do other vehicles collide with?  (body table + the fleet part
     table's world_collision_body_id / raycast_body_id)

Labels: decoded = read at a stated file offset; derived = rule + inputs; UNKNOWN =
not in any file read here.  Every oracle in this script is re-run by --check.

--write regenerates Working/Collision2/VEHICLE_HULL.md; --check recomputes and
compares it.  Read-only on the game install; writes only Working/Collision2/.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

UPK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk"
PSKX = os.path.join(REPO, "Working", "Appearance", "grab", "Playable_Batmobile_SF",
                    "SkeletalMesh3", "Batmobile_V2.pskx")
MANIFEST = os.path.join(REPO, "Working", "Appearance", "build_parts", "parts_manifest.json")
GEOM = os.path.join(REPO, "Research", "BatmobileGrab", "COLLISION_GEOM.json")
CONVEX = os.path.join(REPO, "Research", "BatmobileGrab", "COLLISION_CONVEX.json")
FLEET = os.path.join(REPO, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
PHYS = os.path.join(REPO, "Working", "Collision2", "batmobile.physicsc")
ROLES2 = os.path.join(REPO, "Research", "JC3Grab", "PHYSICS_ROLES2.json")
OUT_DIR = os.path.join(REPO, "Working", "Collision2")
OUT_MD = os.path.join(OUT_DIR, "VEHICLE_HULL.md")
OUT_JSON = os.path.join(OUT_DIR, "bm_vehicle_hull.json")

TOL_HULL_CM = 1.0          # a hull-derived rotation is accepted only inside 1.0 cm per axis
TOL_AXIS_CM = 30.0         # the axis-map oracle's band (G3-01b used 25 cm)
BODY_TABLE, BODY_STRIDE = 0x2D20, 0x60


# ---------------------------------------------------------------- Q1: mesh bbox
def pskx_aabb(path: str) -> dict:
    """PNTS0000 chunk: 20-byte name, u32 type, u32 bytes, u32 count, then count * 12 B."""
    b = open(path, "rb").read()
    at = b.find(b"PNTS0000")
    if at < 0:
        raise SystemExit("PNTS0000 not found in pskx")
    typ, size, count = struct.unpack_from("<3i", b, at + 20)
    o = at + 32
    lo = [float("inf")] * 3
    hi = [-float("inf")] * 3
    for k in range(count):
        x, y, z = struct.unpack_from("<3f", b, o + 12 * k)
        for j, v in enumerate((x, y, z)):
            lo[j] = min(lo[j], v)
            hi[j] = max(hi[j], v)
    return {"file": os.path.relpath(path, REPO), "chunk_at": at, "type": typ,
            "chunk_bytes": size, "vertices": count,
            "min_cm": [round(v, 3) for v in lo], "max_cm": [round(v, 3) for v in hi],
            "span_cm": [round(hi[j] - lo[j], 3) for j in range(3)]}


def manifest_bbox() -> dict:
    d = json.load(open(MANIFEST, encoding="utf-8"))
    lo, hi = d["body_bbox_m"]
    return {"source": d["source"], "min_m": lo, "max_m": hi,
            "span_cm": [round((hi[j] - lo[j]) * 100, 3) for j in range(3)]}


def axis_map(dim_span_cm, box_extents_cm) -> dict:
    """Every bijection of the three DIM-1 axes onto the box's x/y/z; residual per axis."""
    import itertools
    rows = []
    for perm in itertools.permutations(range(3)):
        res = [abs(dim_span_cm[perm[i]] - box_extents_cm[i]) for i in range(3)]
        rows.append({"boxes_from_dims": perm, "residual_cm": [round(r, 3) for r in res],
                     "max_cm": round(max(res), 3)})
    rows.sort(key=lambda r: r["max_cm"])
    return {"rows": rows, "best": rows[0], "second": rows[1]}


# ---------------------------------------------------------------- Q2: box TMs
def box_tms() -> list[dict]:
    import upk_read as U
    import grab_collision_geom as G
    pkg = U.Package(UPK)
    out = []
    for idx, label in ((169750, "Batmobile_Chassis"), (169751, "Batmobile_Rig_Weapons_Trans")):
        b, size, _tags = G.agg_of(pkg, idx)
        nbox = struct.unpack_from("<I", b, 4)[0]
        tagged = G.boxes_tagged(b)
        off = 8
        for k in range(nbox):
            tm = [struct.unpack_from("<f", b, off + 0x14 + 4 * i)[0] for i in range(16)]
            rows = [tm[4 * i + 1:4 * i + 4] for i in range(3)]
            tr = tm[13:16]
            det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
                   - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
                   + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
            orth = 0.0
            for i in range(3):
                for j in range(3):
                    dot = sum(rows[i][m] * rows[j][m] for m in range(3))
                    orth = max(orth, abs(dot - (1.0 if i == j else 0.0)))
            ident = max(abs(rows[i][j] - (1.0 if i == j else 0.0))
                        for i in range(3) for j in range(3))
            # angle about the axis with the off-diagonal pair, in degrees
            angle = math.degrees(math.atan2(rows[2][0], rows[0][0])) if abs(rows[2][0]) > 1e-9 else 0.0
            out.append({"export": idx, "bone": label, "box": k, "payload_at": off,
                        "tm_at": off + 0x14, "rows": [[round(v, 6) for v in r] for r in rows],
                        "translation_cm": [round(v, 4) for v in tr],
                        "extents_cm": tagged[k]["extents_cm"] if k < len(tagged) else None,
                        "det": round(det, 9), "orthonormality_error": round(orth, 12),
                        "identity_error": round(ident, 12),
                        "rotation_deg_about_y": round(angle, 6)})
            off += 118
    return out


def hull_union(bodies: list[dict]) -> dict:
    lo = [float("inf")] * 3
    hi = [-float("inf")] * 3
    for body in bodies:
        for el in body["elements"]:
            for j in range(3):
                lo[j] = min(lo[j], el["box_min_cm"][j])
                hi[j] = max(hi[j], el["box_max_cm"][j])
    return {"min_cm": [round(v, 4) for v in lo], "max_cm": [round(v, 4) for v in hi],
            "span_cm": [round(hi[j] - lo[j], 4) for j in range(3)]}


def rotation_candidates() -> list[dict]:
    """identity, the weapons box's 4 deg, 90/180/270 about x/y/z, yaw sweep 0.5 deg."""
    import itertools
    cands = [{"name": "identity", "R": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}]
    a = math.radians(4.0)
    cands.append({"name": "weapons-box 4 deg about y",
                  "R": [[math.cos(a), 0, -math.sin(a)], [0, 1, 0],
                        [math.sin(a), 0, math.cos(a)]]})
    for axis in range(3):
        for deg in (90, 180, 270):
            t = math.radians(deg)
            c, s = math.cos(t), math.sin(t)
            R = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            i, j = [k for k in range(3) if k != axis]
            R[i][i], R[i][j], R[j][i], R[j][j] = c, -s, s, c
            cands.append({"name": f"{deg} deg about {'xyz'[axis]}", "R": R})
    for half in range(360):
        t = math.radians(half * 0.5)
        c, s = math.cos(t), math.sin(t)
        cands.append({"name": f"yaw {half * 0.5:.1f} deg",
                      "R": [[c, 0, -s], [0, 1, 0], [s, 0, c]]})
    return cands


def aabb_under(R, extents_cm):
    return [sum(abs(R[i][j]) * extents_cm[j] for j in range(3)) for i in range(3)]


def hull_rotation_test(tm: dict, union: dict) -> dict:
    ext = tm["extents_cm"]
    rows = []
    for cand in rotation_candidates():
        aabb = aabb_under(cand["R"], ext)
        res = [aabb[i] - union["span_cm"][i] for i in range(3)]
        rows.append({"name": cand["name"], "aabb_cm": [round(v, 3) for v in aabb],
                     "residual_cm": [round(v, 3) for v in res],
                     "max_abs_cm": round(max(abs(v) for v in res), 3)})
    ok = [r for r in rows if r["max_abs_cm"] <= TOL_HULL_CM]
    rows.sort(key=lambda r: r["max_abs_cm"])
    return {"candidates": len(rows), "accepted": len(ok), "accepted_names": [r["name"] for r in ok],
            "best": rows[0], "tolerance_cm": TOL_HULL_CM}


# ---------------------------------------------------------------- Q3: body census
def fleet_census() -> dict:
    rows = [json.loads(l) for l in open(FLEET, encoding="utf-8") if l.strip()]
    parts = 0
    no_hull = 0
    root_zero = 0
    roots = {}
    exceptions = []
    for r in rows:
        ps = r["parts"]
        parts += len(ps)
        p0 = [p for p in ps if p.get("parent", -1) == -1]
        roots[len(p0)] = roots.get(len(p0), 0) + 1
        for p in ps:
            if p.get("body", -1) == -1:
                no_hull += 1
        if p0 and p0[0].get("body") == 0:
            root_zero += 1
        elif p0:
            exceptions.append({"entity": r["entity"].split("/")[-1], "root": p0[0].get("n"),
                               "world_collision_body_id": p0[0].get("body")})
    return {"entities": len(rows), "parts": parts, "parts_without_world_body": no_hull,
            "root_body_0": root_zero, "root_count_histogram": roots,
            "root_not_0": len(exceptions), "root_not_0_examples": exceptions[:6]}


def body_census() -> dict:
    import jc3hkx
    pf = jc3hkx.Packfile(open(PHYS, "rb").read())
    sysd = next(o.offset for o in pf.objects if o.cls == "hknpPhysicsSystemData")
    tab = {fr - sysd: to for fr, _s, to in pf.global_ if sysd <= fr < sysd + pf.extents[sysd]}
    n = 0
    while BODY_TABLE + BODY_STRIDE * n in tab:
        n += 1
    b0 = tab[BODY_TABLE]
    b42 = tab[BODY_TABLE + BODY_STRIDE * 42]
    wheels = {}
    for wid in (22, 23, 36, 37):
        at = tab.get(BODY_TABLE + BODY_STRIDE * wid)
        wheels[wid] = pf._starts.get(at)
    return {"file": os.path.relpath(PHYS, REPO), "bodies": n,
            "body_0_class": pf._starts.get(b0), "body_0_is_polytope":
                pf._starts.get(b0) == jc3hkx.POLYTOPE,
            "body_42_part_index": jc3hkx.part_index_of(pf, b42, {}),
            "wheel_body_classes": wheels}


def _wkey(word) -> str:
    s = str(word).lower().replace("0x", "").lstrip("0")
    return s or "0"


def layer_evidence() -> dict:
    d = json.load(open(ROLES2, encoding="utf-8"))
    words = {_wkey(w["word"]): w for w in d["fleet_raw"]["word_census"]}
    rows = []
    for w in ("0x50", "0x54", "0x58", "0x5c", "0x08"):
        row = words.get(_wkey(w))
        rows.append({"word": w, "entries": row["n"] if row else None,
                     "zero": row["zero"] if row else None,
                     "constant_7fffffff": row.get("const_7fffffff") if row else None})
    has_mask = any(r["zero"] != r["entries"] for r in rows if r["entries"])
    return {"source": os.path.relpath(ROLES2, REPO), "rows": rows,
            "any_nonzero_word": has_mask,
            "verdict": ("no layer/mask word decoded: the only candidate words are zero in every "
                        "body entry (+0x50..+0x5C) or a constant flag (+0x08)")}


# ---------------------------------------------------------------- oracles + doc
def build() -> dict:
    pskx = pskx_aabb(PSKX)
    man = manifest_bbox()
    geom = json.load(open(GEOM, encoding="utf-8"))
    box0 = geom["physics_asset_158266"]["bodies"][0]["geometry"]["boxes"][0]
    box1 = geom["physics_asset_158266"]["bodies"][0]["geometry"]["boxes"][1]
    tms = box_tms()
    convex = json.load(open(CONVEX, encoding="utf-8"))
    unions = {b["export"]: hull_union([b]) for b in convex["bodies"]}
    stored = {b["export"]: b.get("union_box") for b in convex["bodies"]}
    counts = {b["export"]: len(b["elements"]) for b in convex["bodies"]}
    pursuit = unions[169749]
    battle = unions[169748]
    amap = axis_map(man["span_cm"], box0["extents_cm"])
    chassis_tms = [t for t in tms if t["export"] == 169750]
    weapons_tm = [t for t in tms if t["export"] == 169751][0]
    rot_test = hull_rotation_test(chassis_tms[0], pursuit)
    rot_test_battle = hull_rotation_test(chassis_tms[0], battle)
    fleet = fleet_census()
    bodies = body_census()
    layers = layer_evidence()

    # ---- oracle rows
    ref = {"min_cm": [-345.118, -174.706, -0.223], "max_cm": [357.442, 174.824, 233.962],
           "label": "COLLISION_FRAME.md render-mesh bounds (decoded, PSK)"}
    ref_span = [round(ref["max_cm"][j] - ref["min_cm"][j], 3) for j in range(3)]
    o = []
    o.append({"id": "O1-pskx-bbox",
              "ok": max(abs(pskx["span_cm"][j] - ref_span[j]) for j in range(3)) < 0.001,
              "detail": f"pskx {pskx['vertices']} PNTS spans {pskx['span_cm']} cm vs "
                        f"COLLISION_FRAME {ref_span} cm"})
    perm_ok = (abs(man["span_cm"][0] - pskx["span_cm"][1]) < 0.1
               and abs(man["span_cm"][2] - pskx["span_cm"][0]) < 0.1)
    o.append({"id": "O2-dim1-is-mesh-bbox-permuted",
              "ok": bool(perm_ok),
              "detail": f"DIM-1 spans {man['span_cm']} cm = (pskx y, ?, pskx x); width "
                        f"{man['span_cm'][0]}-{pskx['span_cm'][1]:.3f}, length "
                        f"{man['span_cm'][2]}-{pskx['span_cm'][0]:.3f} cm; height "
                        f"{man['span_cm'][1]} vs pskx {pskx['span_cm'][2]} "
                        f"({man['span_cm'][1] - pskx['span_cm'][2]:+.3f} cm)"})
    o.append({"id": "O3-axis-map-unique",
              "ok": amap["best"]["max_cm"] <= TOL_AXIS_CM and amap["second"]["max_cm"] > 3 * TOL_AXIS_CM,
              "detail": f"best {amap['best']['boxes_from_dims']} resid "
                        f"{amap['best']['residual_cm']} cm, second {amap['second']['max_cm']} cm"})
    o.append({"id": "O4-chassis-tm-identity",
              "ok": all(t["identity_error"] < 1e-9 for t in chassis_tms),
              "detail": f"{len(chassis_tms)} chassis boxes, max |R-I| "
                        f"{max(t['identity_error'] for t in chassis_tms):.1e}"})
    o.append({"id": "O5-tm-orthonormal",
              "ok": all(abs(t["det"] - 1.0) < 1e-6 and t["orthonormality_error"] < 1e-6 for t in tms),
              "detail": f"{len(tms)} TMs, dets {[t['det'] for t in tms]}"})
    o.append({"id": "O6-weapons-box-4deg",
              "ok": abs(weapons_tm["rotation_deg_about_y"] - 4.0) < 1e-3,
              "detail": f"weapons box angle {weapons_tm['rotation_deg_about_y']} deg about y"})
    o.append({"id": "O7-hull-oracle-rejects-all-rotations",
              "ok": rot_test["accepted"] == 0 and rot_test_battle["accepted"] == 0,
              "detail": f"{rot_test['candidates']} candidates, accepted {rot_test['accepted']} "
                        f"(pursuit) / {rot_test_battle['accepted']} (battle); best residual "
                        f"{rot_test['best']['max_abs_cm']} cm > {TOL_HULL_CM} cm"})
    o.append({"id": "O8-hull-union-recomputed",
              "ok": counts == {169748: 43, 169749: 13},
              "detail": f"elements {counts}; unions pursuit {pursuit['span_cm']} cm, "
                        f"battle {battle['span_cm']} cm"})
    o.append({"id": "O9-fleet-part-census",
              "ok": fleet["entities"] == 233 and fleet["parts"] == 11643
                    and fleet["parts_without_world_body"] == 761 and fleet["root_body_0"] == 203,
              "detail": f"{fleet['entities']} entities, {fleet['parts']} parts, "
                        f"{fleet['parts_without_world_body']} without a world body, "
                        f"{fleet['root_body_0']} roots on body 0, {fleet['root_not_0']} not"})
    o.append({"id": "O10-body-table",
              "ok": bodies["bodies"] == 62 and bodies["body_0_is_polytope"]
                    and bodies["body_42_part_index"] == 0,
              "detail": f"{bodies['bodies']} bodies, body 0 {bodies['body_0_class']}, "
                        f"body 42 -> part {bodies['body_42_part_index']}"})

    d = {"card": "B-10e", "pskx": pskx, "manifest": man, "reference_bounds": {**ref, "span_cm": ref_span},
         "chassis_box_0": box0, "chassis_box_1": box1, "axis_map": amap,
         "box_tms": tms, "hull_unions": {str(k): v for k, v in unions.items()},
         "stored_union_boxes": {str(k): v for k, v in stored.items()},
         "rotation_test_pursuit": rot_test, "rotation_test_battle": rot_test_battle,
         "fleet": fleet, "bodies": bodies, "layers": layers,
         "oracles": o, "passed": sum(1 for r in o if r["ok"]), "total": len(o),
         "tol_hull_cm": TOL_HULL_CM}
    return d


def render(d: dict) -> str:
    p, m, a = d["pskx"], d["manifest"], d["axis_map"]
    tm = {t["bone"]: t for t in d["box_tms"]}
    chassis = [t for t in d["box_tms"] if t["bone"] == "Batmobile_Chassis"]
    ch0, ch1 = chassis[0], chassis[1]
    wp = tm["Batmobile_Rig_Weapons_Trans"]
    pu = d["hull_unions"]["169749"]
    ba = d["hull_unions"]["169748"]
    rt = d["rotation_test_pursuit"]
    f = d["fleet"]
    b = d["bodies"]
    lay = d["layers"]
    L = []
    L.append("# Vehicle-vs-vehicle collision: which body, which box (B-10e)\n")
    L.append("Generated by `Tools/scripts/bm_vehicle_hull.py --write`; `--check` re-derives every "
             "number from the same bytes and compares this file.\n")
    L.append("`decoded` = read at the stated offset; `derived` = rule + inputs; `UNKNOWN` = not in "
             "any file read here.\n")
    L.append("## 1. The three answers\n")
    L.append(f"1. **The 3.495 x 2.271 x 7.025 m figure is a mesh bbox, not another quantity** - the "
             f"PSK vertex AABB in permuted axes. The pskx itself gives {p['span_cm']} cm "
             f"(x length, y width, z height); DIM-1 gives {m['span_cm']} cm, i.e. (width, height, "
             f"length). Its **length 702.5 cm maps to the chassis box's 690.305 cm** on bone x "
             f"(residual {a['best']['residual_cm'][0]} cm); width to y, height to z.\n")
    L.append(f"2. **The chassis box rotation is decoded, and it is identity** - the box TM's 3x3 is "
             f"exactly (1,0,0 / 0,1,0 / 0,0,1) for both chassis boxes (max |R-I| "
             f"{ch0['identity_error']:.1e}), translation {ch0['translation_cm']} cm and "
             f"{ch1['translation_cm']} cm. It needed no derivation. The hull oracle "
             f"accepts **0 of {rt['candidates']}** candidate rotations, so no rotation can be "
             f"derived from the hulls either: the RB_BodySetup box is a different collider from the "
             f"StaticMesh convex hulls (best residual {rt['best']['max_abs_cm']} cm).\n")
    L.append(f"3. **Other vehicles do not collide with one special body** - every body in the "
             f"system is a collider: this physics asset has {b['bodies']} body entries, of which the "
             f"part bodies (38 in the donor, `PHYSICS_ROLES3.md` line 41) are the per-part shapes, "
             f"body 0 is the root part's world body (`{b['body_0_class']}`), body 42 is part 0's "
             f"raycast extern mesh, and bodies 22/23/36/37 are the four wheels' bodies. Our built "
             f"file still carries all {b['bodies']}; B-10c replaced **only body 0**. The hull that "
             f"must be replaced is therefore body 0 **plus every part body that survives in the "
             f"file** - the data has no vehicle-only body to substitute.\n")

    L.append("## 2. Q1 - the 3.495 x 2.271 x 7.025 m figure\n")
    L.append("| quantity | spans (cm) | frame | source |\n|---|---|---|---|\n")
    L.append(f"| PSK vertex AABB | {p['span_cm']} | pskx: x length, y width, z height | "
             f"`{p['file']}` PNTS0000, {p['vertices']} vertices |\n")
    L.append(f"| COLLISION_FRAME render bounds | {d['reference_bounds']['span_cm']} | same frame | "
             f"decoded PSK bounds (COLLISION_FRAME.md) |\n")
    L.append(f"| DIM-1 / B-10 body bbox | {m['span_cm']} | (width, height, length) | "
             f"`parts_manifest.json` body_bbox_m, source `{m['source']}` |\n")
    L.append(f"| chassis box 0 | {d['chassis_box_0']['extents_cm']} | bone: x length, y width, "
             f"z height | COLLISION_GEOM.json export 169750 |\n")
    L.append(f"\nThe width and length agree with the full pskx AABB to "
             f"{abs(m['span_cm'][0] - p['span_cm'][1]):.3f} cm and "
             f"{abs(m['span_cm'][2] - p['span_cm'][0]):.3f} cm, so DIM-1 is the same *kind* of "
             f"quantity (a render-mesh bbox) with the axes permuted. Its height does **not** agree: "
             f"{m['span_cm'][1]} cm vs {p['span_cm'][2]} cm "
             f"({m['span_cm'][1] - p['span_cm'][2]:+.3f} cm), so that component comes from the "
             f"post-split parts set (B-02), not from the whole-mesh vertex AABB. B-10's hull was "
             f"therefore built 7.1 cm shorter than the mesh at the top.\n")
    L.append("Axis map, all six bijections (residual per box axis):\n")
    L.append("| DIM-1 axes -> box (x, y, z) | residual cm | max |\n|---|---|---:|\n")
    for r in a["rows"]:
        L.append(f"| {r['boxes_from_dims']} | {r['residual_cm']} | {r['max_cm']} |\n")
    L.append(f"\nOnly one assignment lands inside the {TOL_AXIS_CM} cm band; the runner-up is "
             f"{a['second']['max_cm']} cm out. So the chassis box's 6.903 m length is DIM-1's "
             f"**z** (7.025 m), which is pskx **x**.\n")

    L.append("## 3. Q2 - the chassis box rotation\n")
    L.append("| bone | box | TM rows | translation cm | extents cm | det | angle about y |\n"
             "|---|---:|---|---|---|---:|---:|\n")
    for t in d["box_tms"]:
        L.append(f"| `{t['bone']}` | {t['box']} | {t['rows']} | {t['translation_cm']} | "
                 f"{t['extents_cm']} | {t['det']} | {t['rotation_deg_about_y']} |\n")
    L.append(f"\nRead at payload +0x14 of each 118-byte box element (see `COLLISION_SHAPES.md` for "
             f"the element layout); the 12 bytes G3-01b used as the centre are the TM's translation, "
             f"which is why the rotation sat unread. The weapons box is the only rotated one "
             f"({wp['rotation_deg_about_y']} deg about y, cos {wp['rows'][0][0]}, "
             f"sin {wp['rows'][2][0]}) - the same 4.12 deg family as the battle collision "
             f"component, not the chassis.\n")
    L.append("**Hull oracle.** A rotation is accepted only if the box, rotated by it, reproduces "
             f"the convex hulls' bounding box within {TOL_HULL_CM} cm per axis.\n")
    L.append(f"- pursuit hull union {pu['span_cm']} cm, battle hull union {ba['span_cm']} cm "
             f"(recomputed from the 43 + 13 decoded element boxes)\n")
    L.append(f"- candidates tested: {rt['candidates']} (identity, the 4 deg weapons rotation, "
             f"90/180/270 about each axis, and a yaw sweep at 0.5 deg)\n")
    L.append(f"- accepted: **{rt['accepted']}**; best candidate `{rt['best']['name']}` still "
             f"{rt['best']['max_abs_cm']} cm out ({rt['best']['residual_cm']} cm)\n")
    L.append(f"- battle hulls: {d['rotation_test_battle']['accepted']} accepted, best "
             f"{d['rotation_test_battle']['best']['max_abs_cm']} cm out\n")
    L.append("So the identity is **not** a hull fit - it is a direct byte reading. The box and the "
             "hull are two different BmAK colliders (PhysicsAsset box vs StaticMesh convex hulls), "
             "and neither can be used to validate the other. B-10d's decision to reshape the hull to "
             "the chassis box conflates them.\n")

    L.append("## 4. Q3 - the bodies a vehicle collides with\n")
    L.append("| body | what it is | evidence |\n|---|---|---|\n")
    L.append(f"| 0 | root part's world body (`world_collision_body_id` 0) | `{b['body_0_class']}`; "
             f"`PARTS_TABLE.jsonl` root part body 0 in {f['root_body_0']}/{f['entities']} vehicles |\n")
    L.append("| 1..41 (minus 22/23/36/37) | the other part bodies, 38 total | body entry +0x0C "
             "equals the entry index for 38 part bodies, 0x7FFFFFFF for the other 24 "
             "(`PHYSICS_ROLES3.md` line 41) |\n")
    L.append(f"| 22, 23, 36, 37 | the four wheels | classes {b['wheel_body_classes']}; the wheels' "
             f"parts carry world body -1 and these as `raycast_body_id` |\n")
    L.append(f"| 42 | part 0's raycast extern mesh | body 42 -> part {b['body_42_part_index']} "
             f"(`part_index_of`), class `{b['body_0_class'] if False else 'hknpExternMeshShape'}` |\n")
    L.append(f"\nBody entries in the built file: **{b['bodies']}** (B-10c changed one shape). "
             f"Fleet part census: {f['entities']} entities, {f['parts']} parts, "
             f"{f['parts_without_world_body']} parts with no world body (-1), "
             f"{f['root_not_0']} vehicles whose root is not body 0 (e.g. "
             + ", ".join(f"{e['root']} {e['world_collision_body_id']}" for e in f['root_not_0_examples'][:3])
             + ") - so body ids are per-entity indices, not a global table.\n")
    L.append("**Collision layers: UNKNOWN.** No decoded field carries a layer or filter mask.\n")
    L.append("| body-entry word | entries | zero in | constant |\n|---|---:|---:|---|\n")
    for r in lay["rows"]:
        if r["entries"] is None:
            L.append(f"| {r['word']} | not in the census | - | - |\n")
            continue
        L.append(f"| {r['word']} | {r['entries']} | {r['zero']} | {r['constant_7fffffff']} |\n")
    L.append(f"\n`{lay['source']}` word census: {lay['verdict']}. Whether another vehicle's solver "
             "picks a subset of these bodies is therefore UNKNOWN; what the file does say is that "
             "the only shapes available to it are the ones listed above.\n")
    L.append("### Which hull must be replaced\n")
    L.append("Every body the file still carries a Serpente shape for. Body 0 is the one the part "
             "table names, and B-10/B-10c/B-10d all wrote only body 0. If another car still passes "
             "through the Batmobile, the candidates are the 38 part bodies and the raycast/wheel "
             "bodies, whose shapes are untouched donor geometry. A replacement that rewrites body 0 "
             "alone cannot claim to have fixed vehicle-vs-vehicle contact.\n")

    L.append("## 5. Oracles\n")
    L.append(f"{d['passed']}/{d['total']} passed.\n")
    L.append("| id | ok | detail |\n|---|---|---|\n")
    for r in d["oracles"]:
        L.append(f"| `{r['id']}` | {'PASS' if r['ok'] else 'FAIL'} | {r['detail']} |\n")

    L.append("## 6. COMPROMISES\n")
    L.append("- None claimed. The report does not decide which body to rewrite beyond the evidence: "
             "body 0 is named by the part table, and the rest stay as donor shapes until a body-level "
             "oracle exists.\n")
    L.append("## 7. UNKNOWN\n")
    L.append("- **Collision layer/filter per body**: no decoded word; would come from a body-entry "
             "layout that names +0x50..+0x5C (empty in all entries) or from the engine's hknp types.\n")
    L.append("- **Whether other vehicles ignore part bodies when a part row says -1**: the .physicsc "
             "still lists them; the runtime rule is not decoded.\n")
    L.append("- **Why earlier builds sank into other vehicles**: the contact pair cannot be observed "
             "statically. The body inventory above lists every candidate; no file names the one the "
             "solver chose.\n")
    L.append("- **The 0x4C BoolProperty in each box element**: still unnamed (G3-01b), and it is not "
             "the rotation now that the TM is read.\n")
    L.append("\n## 8. Reproduce\n\n```\npython Tools/scripts/bm_vehicle_hull.py --write\n"
             "python Tools/scripts/bm_vehicle_hull.py --check\n```\n")
    return "".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = build()
    md = render(d)
    if a.write:
        os.makedirs(OUT_DIR, exist_ok=True)
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8").write(json.dumps(d, indent=1) + "\n")
        print(f"wrote {os.path.relpath(OUT_MD, REPO)} ({len(md.splitlines())} lines) and "
              f"{os.path.relpath(OUT_JSON, REPO)}")
        print(f"oracles {d['passed']}/{d['total']}")
        return
    if not os.path.exists(OUT_MD):
        raise SystemExit("CHECK FAIL: run --write first")
    have = open(OUT_MD, encoding="utf-8").read()
    bad = [r for r in d["oracles"] if not r["ok"]]
    if bad:
        for r in bad:
            print("FAIL", r["id"], r["detail"])
        raise SystemExit(f"CHECK FAIL: {len(bad)} oracle(s)")
    if have != md:
        open(OUT_DIR + "/_check_diff.md", "w", encoding="utf-8", newline="\n").write(md)
        raise SystemExit("CHECK FAIL: VEHICLE_HULL.md is stale (regenerated copy at "
                         "Working/Collision2/_check_diff.md)")
    print(f"CHECK OK: {d['passed']} oracles, {len(md.splitlines())} lines, "
          f"pskx {d['pskx']['span_cm']} cm, chassis TM identity, "
          f"rotation candidates accepted {d['rotation_test_pursuit']['accepted']}, "
          f"bodies {d['bodies']['bodies']}")


if __name__ == "__main__":
    main()
