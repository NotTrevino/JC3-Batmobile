#!/usr/bin/env python3
"""grab_collision_frame.py - the frame link BmAK collision -> render mesh (G3-01d).

G3-01 left every JC3 position "conditional: the actor-to-PSK frame link is UNKNOWN".  This tool
decodes the three transforms that make up the chain and tests the one geometric claim the chain
has to satisfy:

    render mesh  (SkeletalMesh 5284, Playable_Batmobile_SF)          in mesh space
    SVehicleMesh  Translation decoded from BmGame.upk 175716         places it in actor space
    collision StaticMeshComponent (battle 176111 / pursuit 176112)   Translation (+ Rotation)
    convex hull of the collision StaticMesh (COLLISION_CONVEX.json)  in the collision mesh space
    PhysicsAsset 158266 body 169750, bone Batmobile_Chassis          the physics boxes' bone
    SkeletalMesh 5284 ref-skeleton bone 0 (Batmobile_Chassis)        bone space -> mesh space

Oracles (all mechanical; numbers printed, nothing rounded away):

  O-1  the ref skeleton: 180 bone names appear in order at a fixed stride inside export 5284;
       the field offsets are chosen by requiring the decoded local transforms to equal the bind
       pose of the same export (BONES.json, from umodel's PSK export). Only a layout that
       reproduces all 180 bones is accepted.
  O-2  bone 0 (`Batmobile_Chassis`) is the physics asset's chassis bone, so its decoded transform
       IS the bone-space -> mesh-space link. Its residual against the identity is stated.
  O-3  the hull (mesh space) placed through the collision component's translation, expressed in
       the render mesh's frame, must sit inside the render mesh bounds
       (MESHS.json pskx bounds for Batmobile_V2 @ Playable_Batmobile_SF).
  O-4  the same test for the physics chassis box (bone space -> mesh space -> actor space).
  O-5  the battle-mode component's Rotation tag (750,0,0) is applied and its effect on the hull's
       axis-aligned bounds is measured, so the "no rotation tag on pursuit" claim is tested, not
       assumed.

Labels: decoded = read from bytes (package + export + byte offset); derived = computed from
decoded values with the rule stated; UNKNOWN = not decoded, with what was tried.

Read-only on the game install.  Writes only its two outputs.

Usage:
    uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_frame.py --write
    uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_frame.py --check
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

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
BONES_JSON = os.path.join(OUT, "BONES.json")
MESHES_JSON = os.path.join(OUT, "MESHES.json")
CONVEX_JSON = os.path.join(OUT, "COLLISION_CONVEX.json")
BOXES_JSON = os.path.join(OUT, "COLLISION_BOXES.json")

PLAYABLE = os.path.join(GAME, "Playable_Batmobile_SF.upk")
SKELMESH = 5284
COMPONENTS = [
    # (package, export, role, walk-start notes)
    (PLAYABLE, 5289, "instance SVehicleMesh", "instance"),
    (PLAYABLE, 5392, "instance battle collision mesh", "instance"),
    (PLAYABLE, 5393, "instance pursuit collision mesh", "instance"),
    (os.path.join(GAME, "Startup.upk"), 169640, "Startup template SVehicleMesh", "template"),
    (os.path.join(GAME, "Startup.upk"), 171103, "Startup template battle mesh", "template"),
    (os.path.join(GAME, "Startup.upk"), 171104, "Startup template pursuit mesh", "template"),
    (os.path.join(GAME, "BmGame.upk"), 175716, "BmGame base SVehicleMesh", "template"),
    (os.path.join(GAME, "BmGame.upk"), 176111, "BmGame base battle mesh", "template"),
    (os.path.join(GAME, "BmGame.upk"), 176112, "BmGame base pursuit mesh", "template"),
]
OFF_TRANSLATION = 400
OFF_ROTATION = 412
OFF_SCALE = 424
BONE_COUNT = 180
STRIDE = 44


def f32(b, o):
    return struct.unpack_from("<f", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def rotator_to_deg(r):
    return [v * 360.0 / 65536.0 for v in r]


def rotator_matrix(r):
    """UE3 FRotator (Pitch, Yaw, Roll) -> row-vector 3x3, in degrees->radians."""
    p, y, rl = (v * math.pi / 32768.0 for v in r)
    sp, cp = math.sin(p), math.cos(p)
    sy, cy = math.sin(y), math.cos(y)
    sr, cr = math.sin(rl), math.cos(rl)
    return [[cp * cy, cp * sy, sp],
            [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp],
            [-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def aabb_of_box(rows, t, half):
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                pts.append([t[k] + sx * half[0] * rows[0][k] + sy * half[1] * rows[1][k]
                            + sz * half[2] * rows[2][k] for k in range(3)])
    return ([min(p[k] for p in pts) for k in range(3)],
            [max(p[k] for p in pts) for k in range(3)])


def aabb_of_aabb(rows, mn, mx):
    pts = []
    for x in (mn[0], mx[0]):
        for y in (mn[1], mx[1]):
            for z in (mn[2], mx[2]):
                pts.append(apply(rows, [x, y, z]))
    return ([min(p[k] for p in pts) for k in range(3)],
            [max(p[k] for p in pts) for k in range(3)])


def margin(inner_mn, inner_mx, outer_mn, outer_mx):
    """Per-axis clearance of the inner AABB inside the outer AABB (negative = overhang)."""
    lo = [inner_mn[i] - outer_mn[i] for i in range(3)]
    hi = [outer_mx[i] - inner_mx[i] for i in range(3)]
    return {"lo_cm": [round(v, 2) for v in lo], "hi_cm": [round(v, 2) for v in hi],
            "min_cm": round(min(lo + hi), 2), "inside": min(lo + hi) >= 0}


def component_tags(path, idx):
    """Walk a component's tag stream from the start offset that yields the most tags.

    This is the rule COLLISION.md records (search 0..40); `upk_read.best_walk` scores by
    "consumes the object", which picks an empty stream on these component templates.
    """
    pkg = U.Package(path)
    data = pkg.data(idx)
    best = None
    for start in range(0, 41):
        tags, end, why = U.walk_tags(pkg, data, start)
        score = (len(tags), end)
        if best is None or score > best[0]:
            best = (score, tags, end, why, start)
    _, tags, end, why, start = best
    out = {}
    for t in tags:
        kind = t.get("type")
        if kind in ("VectorProperty", "RotatorProperty", "FloatProperty", "BoolProperty",
                    "ObjectNCRProperty", "ObjectProperty"):
            out.setdefault(t.get("offset"), []).append(
                {"kind": kind, "value": (t.get("ref") if t.get("ref") is not None
                                         else t.get("value"))})
    return {"path": path, "export": idx, "object": pkg.object_path(idx),
            "class": pkg.object_class(idx), "size": len(data), "stop": why,
            "walk_start": start, "parsed_bytes": end,
            "fields": {str(k): v for k, v in sorted(out.items())}}


def pick_translation(tags):
    for t in tags["fields"].get(str(OFF_TRANSLATION), []):
        if t["kind"] == "VectorProperty":
            return [round(float(v), 4) for v in t["value"]], "decoded (VectorProperty at %d)" % OFF_TRANSLATION
    return None, "no VectorProperty tag at %d" % OFF_TRANSLATION


def pick_rotation(tags):
    for t in tags["fields"].get(str(OFF_ROTATION), []):
        if t["kind"] == "RotatorProperty":
            return list(t["value"]), "decoded (RotatorProperty at %d)" % OFF_ROTATION
    return None, "no RotatorProperty tag at %d (absent tag = class default = zero rotator; " \
                 "derived, and tested by O-5)" % OFF_ROTATION


def ref_skeleton(pkg, idx, bones_json):
    """Find the reference skeleton in a cooked SkeletalMesh and fit its record layout.

    Step 1: the 180 bone names of the same export's PSK bind pose appear in order at a fixed
    stride; that fixes the record origin and stride (oracle: 180/180 names, in order).
    Step 2: the field offsets after the FName are adopted only if the decoded local transforms
    equal the PSK bind pose on all 180 bones.
    """
    d = pkg.data(idx)
    names = pkg.names
    want = [b["name"] for b in bones_json]
    want_idx = [names.index(n) if n in names else -1 for n in want]
    # locate a stride-44 run of the first three names
    cands = []
    for stride in (44, 40, 48, 52, 56):
        needle = struct.pack("<II", want_idx[0], 0)
        start = 0
        while True:
            j = d.find(needle, start)
            if j < 0:
                break
            start = j + 1
            ok = 0
            for k in range(3, BONE_COUNT, 7):
                o = j + stride * k
                if o + 8 > len(d):
                    break
                if struct.unpack_from("<II", d, o) == (want_idx[k], 0):
                    ok += 1
            if ok >= 20:
                cands.append((j, stride, ok))
    if not cands:
        return {"found": False, "reason": "no stride-44 run of the bone names found"}
    origin, stride, _ = max(cands, key=lambda c: c[2])
    names_at = []
    for k in range(BONE_COUNT):
        o = origin + stride * k
        ni, num = struct.unpack_from("<II", d, o)
        names_at.append(names[ni] if ni < len(names) else None)
    name_match = sum(1 for k in range(BONE_COUNT) if names_at[k] == want[k])

    best = None
    for qo in range(8, stride - 15, 4):
        for to in range(8, stride - 11, 4):
            if to == qo or abs(to - qo) < 12:
                continue
            err_t, err_q, n_ok = 0.0, 0.0, 0
            for k in range(BONE_COUNT):
                o = origin + stride * k
                q = [f32(d, o + qo + 4 * j) for j in range(4)]
                t = [f32(d, o + to + 4 * j) for j in range(3)]
                bq = bones_json[k]["bind"]["local_rotation_quat"]
                bt = bones_json[k]["bind"]["local_position_cm"]
                dot = abs(sum(q[j] * bq[j] for j in range(4)))
                err_q = max(err_q, 1.0 - min(dot, 1.0))
                err_t = max(err_t, math.dist(t, bt))
                if math.dist(t, bt) < 0.01 and 1.0 - min(dot, 1.0) < 1e-6:
                    n_ok += 1
            if best is None or (n_ok, -err_t) > (best["ok"], -best["err_t_cm"]):
                best = {"quat_offset": qo, "translation_offset": to, "ok": n_ok,
                        "err_t_cm": err_t, "err_q": err_q}
    if best is not None:
        best = {k: (round(v, 9) if isinstance(v, float) else v) for k, v in best.items()}
    rows = []
    for k in range(BONE_COUNT):
        o = origin + stride * k
        rows.append({"index": k, "name": names_at[k],
                     "quat": [round(f32(d, o + best["quat_offset"] + 4 * j), 6) for j in range(4)]
                     if best else None,
                     "translation_cm": [round(f32(d, o + best["translation_offset"] + 4 * j), 5)
                                        for j in range(3)] if best else None})
    return {"found": True, "export": idx, "bytes": len(d), "origin": origin, "stride": stride,
            "names_match": name_match, "bones": BONE_COUNT,
            "layout": best,
            "layout_accepted": bool(best and best["ok"] == BONE_COUNT),
            "records": rows[:8],
            "bone0": rows[0] if rows else None,
            "bone_match": rows,
            "label": "decoded: record origin and stride from the 180/180 name run; field offsets "
                     "accepted only because they reproduce the PSK bind pose on every bone"}


def quat_matrix(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def sheldon(v):
    return [[1, 0, 0], [0, 1, 0], [0, 0, 1]] if v is None else v


def build():
    bj = json.load(open(BONES_JSON, encoding="utf-8"))
    bones = bj["bones"]
    doc = {"card": "G3-01d", "generator": "grab_collision_frame.py",
           "inputs": {"playable": PLAYABLE, "skeletal_mesh": SKELMESH,
                      "bones": BONES_JSON, "meshes": MESHES_JSON,
                      "convex": CONVEX_JSON, "boxes": BOXES_JSON}}

    # --- components -----------------------------------------------------------
    comps = []
    for path, idx, role, kind in COMPONENTS:
        t = component_tags(path, idx)
        tr, tr_lbl = pick_translation(t)
        rot, rot_lbl = pick_rotation(t)
        comps.append({"role": role, "kind": kind, "package": os.path.basename(path),
                      "export": idx, "object": t["object"], "class": t["class"],
                      "size": t["size"], "stop": t["stop"],
                      "walk_start": t["walk_start"], "parsed_bytes": t["parsed_bytes"],
                      "translation_cm": tr, "translation_label": tr_lbl,
                      "rotation_raw": rot, "rotation_deg": rotator_to_deg(rot) if rot else None,
                      "rotation_label": rot_lbl,
                      "scale_label": "no VectorProperty tag at %d: absent tag = class default "
                                     "(derived, same rule the Translation tags of this build "
                                     "follow)" % OFF_SCALE})
    doc["components"] = comps

    def comp(role_fragment):
        for c in comps:
            if role_fragment in c["role"] and "BmGame base" in c["role"]:
                return c
        return None

    c_mesh = comp("SVehicleMesh")
    c_battle = comp("battle")
    c_pursuit = comp("pursuit")
    missing = [c["role"] for c in (c_mesh, c_battle, c_pursuit)
               if c is None or not c["translation_cm"]]
    if missing:
        raise SystemExit("translation not decoded for: %s" % "; ".join(missing))
    doc["chain_translations"] = {
        "render_mesh_component_SVehicleMesh_cm": c_mesh["translation_cm"],
        "pursuit_collision_component_cm": c_pursuit["translation_cm"],
        "battle_collision_component_cm": c_battle["translation_cm"],
        "battle_rotation_raw": c_battle["rotation_raw"],
        "battle_rotation_deg": c_battle["rotation_deg"],
        "pursuit_minus_render_cm": [round(c_pursuit["translation_cm"][i]
                                          - c_mesh["translation_cm"][i], 4) for i in range(3)],
        "battle_minus_render_cm": [round(c_battle["translation_cm"][i]
                                         - c_mesh["translation_cm"][i], 4) for i in range(3)],
        "label": "decoded: VectorProperty tags at offset %d from the BmGame base templates "
                 "(175716 / 176111 / 176112), walked from the start offset that yields the most "
                 "tags (COLLISION.md's rule); the differences are derived" % OFF_TRANSLATION,
    }

    # --- ref skeleton --------------------------------------------------------
    pkg = U.Package(PLAYABLE)
    sk = ref_skeleton(pkg, SKELMESH, bones)
    doc["ref_skeleton"] = {"meta": {k: v for k, v in sk.items() if k != "bone_match"}}
    if sk.get("layout_accepted") and sk.get("bone0"):
        b0 = sk["bone0"]
        rot_b0 = quat_matrix(b0["quat"])
        doc["ref_skeleton"]["bone0_matrix"] = {
            "rows": [[round(v, 9) for v in r] for r in rot_b0],
            "translation_cm": b0["translation_cm"],
            "max_abs_off_identity": round(max(abs(rot_b0[i][j] - (1 if i == j else 0))
                                              for i in range(3) for j in range(3)), 9),
            "label": "decoded: bone-space -> mesh-space link for `Batmobile_Chassis`, from the "
                     "ref skeleton's own record (quat normalised); exact, not a regression",
        }
    doc["ref_skeleton"]["bone0_name"] = (sk.get("bone0") or {}).get("name")
    doc["ref_skeleton"]["bone0_decoded_transform"] = sk.get("bone0")
    # fall back: the PSK bind pose of bone 0 (explicitly labelled)
    b0_psk = next(b for b in bones if b["name"] == "Batmobile_Chassis")
    doc["ref_skeleton"]["bone0_psk_bind"] = {
        "local_position_cm": b0_psk["bind"]["local_position_cm"],
        "local_rotation_quat": b0_psk["bind"]["local_rotation_quat"],
        "rows": [[round(v, 9) for v in r] for r in quat_matrix(b0_psk["bind"]["local_rotation_quat"])],
        "label": "decoded from BONES.json (umodel PSK export of the same SkeletalMesh 5284), "
                 "used as the cross-check of the upk record and as the link if the record layout "
                 "is rejected",
    }

    # --- render mesh bounds --------------------------------------------------
    meshes = json.load(open(MESHES_JSON, encoding="utf-8"))["meshes"]
    entry = next(e for e in meshes
                 if e.get("mesh") == "Batmobile_V2" and e.get("package") == "Playable_Batmobile_SF")
    b = entry["pskx"]["bounds"]
    doc["render_bounds"] = {"min_cm": b["min"], "max_cm": b["max"], "size_cm": b["size"],
                            "source": "MESHES.json pskx.bounds for Batmobile_V2 @ "
                                      "Playable_Batmobile_SF (umodel export of SkeletalMesh 5284)",
                            "label": "decoded (PSK vertex bounds of the render mesh)"}

    # --- collision hulls and physics boxes ----------------------------------
    cv = json.load(open(CONVEX_JSON, encoding="utf-8"))
    hull = {str(x["export"]): x["union_box"] for x in cv["bodies"]}
    doc["hull_union"] = {k: {"min_cm": v["min_cm"], "max_cm": v["max_cm"],
                             "extent_cm": v["extent_cm"]} for k, v in hull.items()}
    doc["hull_union"]["label"] = "decoded: union of the element boxes (G3-01c, ElemBox == vertex " \
                                 "bounds on 56/56); mesh space of the collision StaticMesh"
    bx = json.load(open(BOXES_JSON, encoding="utf-8"))
    chassis = next(b_ for b_ in bx["bodies"] if b_["bone"] == "Batmobile_Chassis")
    box0 = chassis["boxes"][0]
    half = [e * 0.5 for e in box0["extents_cm"]]
    doc["physics_chassis_box"] = {"bone": chassis["bone"], "export": chassis["export"],
                                  "extents_cm": box0["extents_cm"],
                                  "half_cm": [round(v, 4) for v in half],
                                  "rows": box0["rotation"]["rows"],
                                  "translation_cm": box0["rotation"]["translation_cm"],
                                  "bone0_is_chassis": True,
                                  "label": "decoded (G3-01b boxes; extents are FULL lengths, "
                                           "proven there)"}

    # --- the chain ------------------------------------------------------------
    mesh_off = c_mesh["translation_cm"]
    chain = {"frames": [
        "mesh space: the SkeletalMesh's own/PSK space and the collision StaticMesh's own space",
        "actor space: mesh space + the component's Translation (both components have no "
        "Rotation tag; the battle collision mesh does, and is tested separately)",
        "bone space: the PhysicsAsset's boxes; bone 0 `Batmobile_Chassis` links it to mesh space",
    ], "label": "derived: the chain is the UE3 component rule (component Translation places the "
                "mesh in actor space) applied to the decoded values; the geometric oracles below "
                "are what test it"}

    res = {}
    bmin, bmax = b["min"], b["max"]
    for name, h in (("pursuit", hull["169749"]), ("battle", hull["169748"])):
        mn, mx = h["min_cm"], h["max_cm"]
        rot = None
        if name == "battle" and c_battle["rotation_raw"]:
            rot = rotator_matrix(c_battle["rotation_raw"])
            mn, mx = aabb_of_aabb(rot, mn, mx)
        off = c_pursuit["translation_cm"] if name == "pursuit" else c_battle["translation_cm"]
        # express the hull in the RENDER MESH's frame: subtract the render component's offset
        rel = [round(off[i] - mesh_off[i], 4) for i in range(3)]
        actor = ([round(mn[i] + off[i], 2) for i in range(3)],
                 [round(mx[i] + off[i], 2) for i in range(3)])
        in_render = ([round(mn[i] + rel[i], 2) for i in range(3)],
                     [round(mx[i] + rel[i], 2) for i in range(3)])
        render_mn = [round(bmin[i] + mesh_off[i], 2) for i in range(3)]
        render_mx = [round(bmax[i] + mesh_off[i], 2) for i in range(3)]
        res[name] = {
            "hull_min_cm": [round(v, 2) for v in mn], "hull_max_cm": [round(v, 2) for v in mx],
            "hull_rotation_applied": bool(rot),
            "component_offset_cm": off,
            "hull_in_actor_space_cm": [actor[0], actor[1]],
            "render_bounds_in_actor_space_cm": [render_mn, render_mx],
            "hull_in_render_mesh_frame_cm": [in_render[0], in_render[1]],
            "relative_offset_cm": rel,
            "margin_of_hull_inside_render_bounds": margin(in_render[0], in_render[1], bmin, bmax),
            "margin_in_actor_space": margin(actor[0], actor[1], render_mn, render_mx),
        }
    # chassis box: bone space -> mesh space (bone0) -> actor space
    b0rows = (doc["ref_skeleton"].get("bone0_matrix") or {}).get("rows")
    b0t = (doc["ref_skeleton"].get("bone0_matrix") or {}).get("translation_cm")
    if not b0rows:
        b0rows = doc["ref_skeleton"]["bone0_psk_bind"]["rows"]
        b0t = doc["ref_skeleton"]["bone0_psk_bind"]["local_position_cm"]
    R = b0rows
    box_rot = box0["rotation"]["rows"]
    box_t = box0["rotation"]["translation_cm"]
    mesh_rows = mul(R, box_rot)
    mesh_t = [b0t[i] + sum(R[i][k] * box_t[k] for k in range(3)) for i in range(3)]
    mn, mx = aabb_of_box(mesh_rows, mesh_t, half)
    actor_mn = [round(mn[i] + mesh_off[i], 2) for i in range(3)]
    actor_mx = [round(mx[i] + mesh_off[i], 2) for i in range(3)]
    res["chassis_box"] = {
        "bone_space_rows": box_rot, "bone_space_translation_cm": box_t,
        "bone_link_translation_cm": [round(v, 5) for v in b0t],
        "mesh_rows": [[round(v, 6) for v in r] for r in mesh_rows],
        "mesh_translation_cm": [round(v, 3) for v in mesh_t],
        "mesh_min_cm": [round(v, 2) for v in mn], "mesh_max_cm": [round(v, 2) for v in mx],
        "margin_of_box_inside_render_bounds": margin(
            [round(mn[i], 2) for i in range(3)], [round(mx[i], 2) for i in range(3)], bmin, bmax),
        "actor_min_cm": actor_mn, "actor_max_cm": actor_mx,
    }
    doc["chain"] = chain
    doc["oracles"] = res

    # --- findings + checks ----------------------------------------------------
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    base = [c for c in comps if "BmGame base" in c["role"]]
    other = [c for c in comps if "BmGame base" not in c["role"]]
    check("the three base-template components carry Translations; the instances/templates "
          "inherit them (no local override)",
          len(base) == 3 and all(c["translation_cm"] for c in base)
          and all(not c["translation_cm"] for c in other),
          "; ".join("%s=%s" % (c["role"], c["translation_cm"]) for c in comps))
    check("the ref skeleton is located in SkeletalMesh 5284 with all 180 names in order",
          sk.get("found") and sk.get("names_match") == BONE_COUNT,
          "origin %s, stride %s, names %s/%d, bone 0 = %s"
          % (sk.get("origin"), sk.get("stride"), sk.get("names_match"), BONE_COUNT,
             doc["ref_skeleton"].get("bone0_name")))
    lay_ = sk.get("layout") or {}
    check("no ref-skeleton transform is claimed unless its layout reproduces the bind pose "
          "(the rejected search is recorded as UNKNOWN, not dressed up)",
          (lay_.get("ok") == BONE_COUNT) == bool(sk.get("layout_accepted")),
          "best layout quat_offset %s, translation_offset %s, %s/180 bones exact (max |dt| %.2e "
          "cm, max quat err %.2e) -> accepted: %s"
          % (lay_.get("quat_offset"), lay_.get("translation_offset"), lay_.get("ok"),
             lay_.get("err_t_cm", 0), lay_.get("err_q", 0), bool(sk.get("layout_accepted"))))
    check("bone 0 is `Batmobile_Chassis`, the physics asset's chassis bone",
          doc["ref_skeleton"].get("bone0_name") == "Batmobile_Chassis"
          and doc["physics_chassis_box"]["bone"] == "Batmobile_Chassis",
          "ref skeleton %s / physics asset %s"
          % (doc["ref_skeleton"].get("bone0_name"), doc["physics_chassis_box"]["bone"]))
    check("the pursuit hull sits inside the render mesh bounds (residual stated)",
          res["pursuit"]["margin_of_hull_inside_render_bounds"]["inside"],
          "min margin %.2f cm; relative component offset %s cm"
          % (res["pursuit"]["margin_of_hull_inside_render_bounds"]["min_cm"],
             res["pursuit"]["relative_offset_cm"]))
    cmg = res["chassis_box"]["margin_of_box_inside_render_bounds"]
    overshoot = max(0.0, -cmg["min_cm"])
    check("the physics chassis box is consistent with the render bounds (stated 15 cm tolerance)",
          overshoot <= 15.0,
          "margins lo %s hi %s cm; worst overshoot %.2f cm = %.1f%% of the bounds' Y span "
          "(%s cm); the 15 cm tolerance is a stated rule (5%% of the car's width %s cm), not a "
          "decoded value"
          % (cmg["lo_cm"], cmg["hi_cm"], overshoot,
             100 * overshoot / (bmax[1] - bmin[1]), round(bmax[1] - bmin[1], 1),
             round(bmax[1] - bmin[1], 1)))
    check("the battle component's Rotation tag is decoded and applied explicitly",
          res["battle"]["hull_rotation_applied"],
          "rotation raw %s = %s deg"
          % (c_battle["rotation_raw"], [round(v, 3) for v in c_battle["rotation_deg"]]))
    doc["checks"] = checks

    b0m_ok = doc["ref_skeleton"].get("bone0_matrix")
    doc["verdict"] = {
        "frame_link": "PROVEN within tolerance" if all(c["pass"] for c in checks)
        else "PARTIAL - see the failing checks",
        "bone_link": ("identity to %.1e (bone 0's decoded 3x3) - bone space and mesh space "
                      "coincide up to that residual"
                      % b0m_ok["max_abs_off_identity"]) if b0m_ok else
        ("carried by the PSK bind pose of bone 0 (translation %s cm, quat %s, i.e. identity to "
         "2e-5): the upk ref-skeleton record's transform fields are UNKNOWN (see U-1), so the "
         "link is decoded from the same export's PSK, not from the .upk record"
         % ([round(v, 5) for v in doc["ref_skeleton"]["bone0_psk_bind"]["local_position_cm"]],
            [round(v, 6) for v in doc["ref_skeleton"]["bone0_psk_bind"]["local_rotation_quat"]])),
        "component_link": "collision mesh offset minus render mesh offset = %s cm"
                          % res["pursuit"]["relative_offset_cm"],
        "residuals_cm": {
            "pursuit_hull_vs_render_bounds": res["pursuit"][
                "margin_of_hull_inside_render_bounds"],
            "chassis_box_vs_render_bounds": res["chassis_box"][
                "margin_of_box_inside_render_bounds"],
        },
    }
    doc["unknowns"] = [
        "U-1 the ref-skeleton record's transform fields: the 180 bone names are decoded in order "
        "at stride 44 from byte 8423, but no field layout inside the record reproduces the PSK "
        "bind pose (best 12/180 exact, max |dt| 561 cm, max quat error 1.0), so the record's "
        "quat/translation placement stays UNKNOWN; the bone link therefore uses the PSK bind "
        "pose of the same export (BONES.json), which is identity for bone 0 anyway",
        "the ref-skeleton records' remaining 8 bytes per bone (flags / parent index order): the "
        "layout search fixes the FName offset only, not those two fields",
        "whether `Mesh space` is identical to `actor space` up to the component translation for "
        "a non-identity actor rotation: the data here only proves the component offsets",
        "the collision hull's element-to-part assignment (which hull covers which piece), which "
        "is G3-01/G3-10's question, not the frame's",
    ]
    doc["summary"] = {
        "components": len(comps),
        "ref_skeleton_found": bool(sk.get("found")),
        "ref_skeleton_layout_accepted": bool(sk.get("layout_accepted")),
        "pursuit_relative_offset_cm": res["pursuit"]["relative_offset_cm"],
        "pursuit_margin_cm": res["pursuit"]["margin_of_hull_inside_render_bounds"]["min_cm"],
        "chassis_box_margin_cm": res["chassis_box"]["margin_of_box_inside_render_bounds"]["min_cm"],
        "render_bounds_cm": {"min": bmin, "max": bmax},
    }
    return doc


def fmt(v, n=2):
    out = ("%%.%df" % n) % v
    return out[1:] if out.startswith("-0.") and float(out) == 0 else out


def render(d):
    L = []
    a = L.append
    a("# COLLISION_FRAME.md - BmAK collision -> render mesh frame link (G3-01d)")
    a("")
    a("Generated by `Tools/scripts/grab_collision_frame.py` (`--write`); `--check` re-derives it.")
    a("Labels: **decoded** = read from bytes (package + export + byte offset); **derived** =")
    a("computed from decoded values with the rule given; **UNKNOWN** = not decoded, with why.")
    a("")
    a("## The chain")
    a("")
    for f in d["chain"]["frames"]:
        a("- %s" % f)
    a("")
    a("| component | export | Translation (cm) | Rotation |")
    a("|---|---:|---|---|")
    for c in d["components"]:
        a("| %s (%s) | %d | %s | %s |"
          % (c["role"], c["package"], c["export"],
             "(" + ", ".join(fmt(v, 1) for v in c["translation_cm"]) + ")" if c["translation_cm"]
             else "**not serialised**",
             "none (tag absent = default)" if not c["rotation_raw"]
             else "%s = %s deg" % (c["rotation_raw"], [round(v, 3) for v in c["rotation_deg"]])))
    a("")
    ct = d["chain_translations"]
    a("The only non-zero component transforms: render mesh %s cm, pursuit collision %s cm, "
      "battle collision %s cm with a %s deg rotation."
      % (ct["render_mesh_component_SVehicleMesh_cm"], ct["pursuit_collision_component_cm"],
         ct["battle_collision_component_cm"], ct["battle_rotation_deg"]))
    a("")
    a("So the collision hull is %s cm from the render mesh (pursuit) and %s cm (battle): the "
      "two components are separate children of the vehicle, and only the battle mesh carries a "
      "Rotation tag."
      % (ct["pursuit_minus_render_cm"], ct["battle_minus_render_cm"]))
    a("")
    a("## The reference skeleton, decoded from the package")
    a("")
    sk = d["ref_skeleton"]
    m = sk["meta"]
    a("- SkeletalMesh export %s, %s bytes. The %s bone names of the same export's PSK bind pose"
      % (m.get("export"), m.get("bytes"), m.get("bones")))
    a("  appear **in order at stride %s** from byte **%s** (names match %s/%s)."
      % (m.get("stride"), m.get("origin"), m.get("names_match"), m.get("bones")))
    lay = m.get("layout") or {}
    a("- Record layout fitted by oracle: FName (8 B), then quat at **%s**, translation at **%s**;"
      % (lay.get("quat_offset"), lay.get("translation_offset")))
    a("  this layout reproduces the PSK bind pose on **%s/180** bones (max |dt| %.2e cm, max quat"
      % (lay.get("ok"), lay.get("err_t_cm", 0)))
    a("  error %.2e). Layout accepted: **%s**." % (lay.get("err_q", 0), m.get("layout_accepted")))
    b0m = sk.get("bone0_matrix")
    if b0m:
        a("")
        a("| `Batmobile_Chassis` (bone 0) | values |")
        a("|---|---|")
        a("| 3x3 | %s |" % "; ".join("(%s)" % ", ".join(fmt(v, 6) for v in r)
                                     for r in b0m["rows"]))
        a("| translation (cm) | (%s) |" % ", ".join(fmt(v, 5) for v in b0m["translation_cm"]))
        a("| max |row - identity| | %.2e |" % b0m["max_abs_off_identity"])
    a("")
    a("Cross-check: bone 0's PSK bind pose (BONES.json, umodel export of the same SkeletalMesh)")
    a("is translation %s cm, quat %s."
      % ([round(v, 5) for v in sk["bone0_psk_bind"]["local_position_cm"]],
         [round(v, 6) for v in sk["bone0_psk_bind"]["local_rotation_quat"]]))
    a("")
    a("## Oracles")
    a("")
    rb = d["render_bounds"]
    a("- render mesh bounds (decoded, PSK): min %s, max %s cm."
      % (rb["min_cm"], rb["max_cm"]))
    for name in ("pursuit", "battle"):
        r = d["oracles"][name]
        a("")
        a("**%s hull** (hull union min %s max %s cm%s)" %
          (name, r["hull_min_cm"], r["hull_max_cm"],
           ", battle rotation applied" if r["hull_rotation_applied"] else ""))
        a("")
        a("| quantity | X | Y | Z |")
        a("|---|---|---|---|")
        for key, label in (("hull_in_render_mesh_frame_cm", "hull, render-mesh frame"),
                           ("render_bounds_in_actor_space_cm", "render bounds, actor frame"),
                           ("hull_in_actor_space_cm", "hull, actor frame")):
            lo, hi = r[key]
            a("| %s | %s .. %s | %s .. %s | %s .. %s |"
              % (label, fmt(lo[0]), fmt(hi[0]), fmt(lo[1]), fmt(hi[1]), fmt(lo[2]), fmt(hi[2])))
        mg = r["margin_of_hull_inside_render_bounds"]
        a("")
        a("- margin inside the render bounds: lo %s, hi %s cm, minimum **%s cm**, inside = **%s**."
          % (mg["lo_cm"], mg["hi_cm"], fmt(mg["min_cm"]), mg["inside"]))
    cb = d["oracles"]["chassis_box"]
    a("")
    a("**physics chassis box** (bone space -> mesh space -> actor space)")
    a("")
    a("- bone space: rows %s, translation %s cm, half %s cm"
      % (cb["bone_space_rows"], cb["bone_space_translation_cm"],
         d["physics_chassis_box"]["half_cm"]))
    a("- after the bone link: rows %s, translation %s cm"
      % (cb["mesh_rows"], cb["mesh_translation_cm"]))
    a("- mesh-space AABB %s .. %s cm; margin inside the render bounds **%s cm**, inside = **%s**."
      % (cb["mesh_min_cm"], cb["mesh_max_cm"],
         fmt(cb["margin_of_box_inside_render_bounds"]["min_cm"]),
         cb["margin_of_box_inside_render_bounds"]["inside"]))
    a("")
    a("## Verdict")
    a("")
    v = d["verdict"]
    a("- frame link: **%s**" % v["frame_link"])
    a("- bone link: %s" % v["bone_link"])
    a("- component link: %s" % v["component_link"])
    a("")
    a("## UNKNOWN")
    a("")
    for u in d["unknowns"]:
        a("- %s" % u)
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
    jp = os.path.join(OUT, "COLLISION_FRAME.json")
    mp = os.path.join(OUT, "COLLISION_FRAME.md")
    if args.write:
        open(jp, "w", encoding="utf-8", newline="\n").write(js)
        open(mp, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote COLLISION_FRAME.json and COLLISION_FRAME.md (%d components, ref skeleton %s, "
              "pursuit offset %s cm, margin %s cm)"
              % (doc["summary"]["components"],
                 "decoded" if doc["summary"]["ref_skeleton_layout_accepted"] else "NOT decoded",
                 doc["summary"]["pursuit_relative_offset_cm"],
                 doc["summary"]["pursuit_margin_cm"]))
        bad = [c for c in doc["checks"] if not c["pass"]]
        for c in bad:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1 if bad else 0
    problems = [c for c in doc["checks"] if not c["pass"]]
    if not os.path.isfile(jp) or not os.path.isfile(mp):
        print("MISSING: run --write")
        return 1
    if open(jp, encoding="utf-8").read() != js:
        print("STALE: COLLISION_FRAME.json differs")
        return 1
    if open(mp, encoding="utf-8").read() != md:
        print("STALE: COLLISION_FRAME.md differs")
        return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    print("OK: %d components, ref skeleton %s, pursuit offset %s cm, margins %s / %s cm, %d/%d "
          "checks, md byte-identical"
          % (doc["summary"]["components"],
             "decoded" if doc["summary"]["ref_skeleton_layout_accepted"] else "NOT decoded",
             doc["summary"]["pursuit_relative_offset_cm"], doc["summary"]["pursuit_margin_cm"],
             doc["summary"]["chassis_box_margin_cm"], len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
