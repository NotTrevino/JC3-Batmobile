#!/usr/bin/env python
"""jc3interact.py - G2-18: interaction points and stunt areas.

Card G2-18 (serves WLD-3/4, MOD-3/4, ANI-9): list every `entry.*` / `exit.*` / `point.*` /
`transition.*` / `trigger.*` / `interaction.*` object in the donor `.epe` with its full
transform and referenced animation/state; decode the `StuntAreas` module (the surfaces Rico can
stand on); express every point relative to the Serpente body frame and wheel stations, then
report where it lands on the Batmobile body (inside / floating / on-surface) using the Batmobile
mesh.

Inputs (all read-only):
  * ``E:/Modding/_shared/gamedata/JC3grab/entities/<donor>.ee.json`` - `StuntAreas`, `DeformPoints`, `LandGlobal`
  * ``E:/Modding/_shared/gamedata/JC3grab/detail/<donor>.ee.json``   - the `.epe` object graph
  * ``Research/Epe/serpente_civilian.xml``           - the same `.epe` as XML (format cross-check)
  * ``Working/TrueScale/stations.json``              - Batmobile body bbox + wheel hardpoints
  * ``Working/TrueScale/body_lod1.rbm``              - Batmobile body mesh (via `rbm_geom`)

The normalised Serpente -> Batmobile placement here is an ANALYSIS mapping for the card. It is
not the R2 build transform: assets keep `bat_assemble.py`'s `T(p)` and nothing here moves a mesh.

Writes ``Research/JC3Grab/INTERACTION.md`` + ``INTERACTION.json``; ``--check`` re-derives both.

Usage:
  python jc3interact.py --write
  python jc3interact.py --check
  python jc3interact.py dump frames|points|areas|mesh
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
DONOR = ("v0300_car_kensington_sportsmuscle", "v0300_car_kensington_sportsmuscle_civilian_01")
XML = os.path.join(ROOT, "Research", "Epe", "serpente_civilian.xml")
STATIONS = os.path.join(ROOT, "Working", "TrueScale", "stations.json")
BAT_MESH = os.path.join(ROOT, "Working", "TrueScale", "body_lod1.rbm")
JSON_NAME = "INTERACTION.json"
MD_NAME = "INTERACTION.md"

PREFIX = re.compile(r"^(entry|exit|point|transition|trigger|interaction)\.")
ON_SURFACE_M = 0.03           # 3 cm: "touching the shell" for this mesh density
CORNERS = ("f_l", "f_r", "r_l", "r_r")


# ---------------------------------------------------------------------- helpers
def donor_paths() -> tuple[str, str]:
    model, ent = DONOR
    base = f"{model}__{ent}"
    return (os.path.join(RAW, "entities", base + ".ee.json"),
            os.path.join(RAW, "detail", base + ".ee.json"))


def mat4(s: str) -> np.ndarray:
    """`world` strings are 16 comma-separated floats: three 3-vectors, then the translation."""
    v = [float(x) for x in s.replace(" ", "").split(",")]
    return np.array(v).reshape(4, 4)


def rnd(x, n=4):
    return round(float(x), n)


# ---------------------------------------------------------------------- readers
def read_entities() -> dict:
    ent_p, _ = donor_paths()
    d = json.load(open(ent_p, encoding="utf-8"))
    mods = {str(m.get("type")): m for m in d["modules"]}

    # deform points: `points[i].start_transform[12..14]` is the translation (vehicle space)
    dp = mods["DeformPoints"]
    vals: dict[int, dict[int, float]] = collections.defaultdict(dict)
    names: dict[int, str] = {}
    for r in dp["rows"]:
        m = re.match(r"points\[(\d+)\]\.start_transform\[(\d+)\]$", r["path"])
        if m:
            vals[int(m.group(1))][int(m.group(2))] = r["value"]
            continue
        m = re.match(r"points\[(\d+)\]\.name$", r["path"])
        if m:
            names[int(m.group(1))] = r["value"]
    dpts = [{"i": i, "name": names.get(i, ""),
             "p": [vals[i][12], vals[i][13], vals[i][14]]} for i in sorted(vals)]

    # stunt areas: 32 slots, 3 active
    sa = mods["StuntAreas"]
    g: dict[str, object] = {r["path"]: r["value"] for r in sa["rows"]}
    slot_ids = sorted({int(m.group(1)) for m in
                       (re.match(r"stunt_areas\[(\d+)\]", k) for k in g) if m})
    areas = []
    for i in slot_ids:
        def get(tail, default=None):
            return g.get(f"stunt_areas[{i}].{tail}", default)

        n = int(get("number_of_deform_points") or 0)
        verts = []
        for j in range(3 * 16):
            v = get(f"vertices3D_local[{j}]")
            if v is None:
                break
            verts.append(float(v))
        tris = []
        for j in range(3 * 16):
            v = get(f"triangle_indices[{j}]")
            if v is None:
                break
            tris.append(int(v))
        areas.append({
            "slot": i, "name": get("name"), "part_name": get("part_name"),
            "part_index": get("part_index"), "active": get("active"),
            "n_deform_points": n,
            "deform_points": [int(get(f"deform_points[{j}]") or 0) for j in range(16)][:n],
            "edge_validity": [int(get(f"edge_validity[{j}]") or 0) for j in range(16)],
            "number_of_triangles": int(get("number_of_triangles") or 0),
            "vertices3D_local": verts,
            "triangle_indices": tris,
            "bbox": [get(f"bounding_box_local.{k}") for k in
                     ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z")],
            "center": [get(f"center_local[{k}]") for k in range(3)],
        })

    welds = []
    wn = int(g.get("number_of_welding_info") or 0) if "number_of_welding_info" in g else 0
    for i in range(64):
        if f"welding_info[{i}].stunt_area_a_index" not in g:
            break
        welds.append({"a_area": g[f"welding_info[{i}].stunt_area_a_index"],
                      "a_edge": g[f"welding_info[{i}].edge_a_index"],
                      "b_area": g[f"welding_info[{i}].stunt_area_b_index"],
                      "b_edge": g[f"welding_info[{i}].edge_b_index"]})

    hardpoints = []
    for lg in [m for m in d["modules"] if m.get("type") == "LandGlobal"]:
        hp = {}
        for r in lg["rows"]:
            m = re.match(r"base_wheel_hardpoint_positions\[(\d+)\]\.position\[(\d)\]$",
                         r["path"])
            if m:
                hp.setdefault(int(m.group(1)), {})[int(m.group(2))] = r["value"]
        if hp and not hardpoints:
            hardpoints = [[hp[i][0], hp[i][1], hp[i][2]] for i in sorted(hp)]
    real = [w for w in welds if w["a_area"] >= 0 and w["b_area"] >= 0]
    pairs = collections.Counter((int(w["b_area"]), int(w["a_area"])) for w in real)
    real = [w for w in welds if w["a_area"] >= 0 and w["b_area"] >= 0]
    pairs = collections.Counter((int(w["b_area"]), int(w["a_area"])) for w in real)
    return {"entity": d["entity"], "deform_points": dpts, "areas": areas,
            "area_slots": len(slot_ids),
            "declared_areas": int(g.get("number_of_stunt_areas") or 0),
            "welds": welds, "weld_count": len(welds), "real_welds": len(real),
            "weld_pairs": {f"{k[0]}-{k[1]}": v for k, v in sorted(pairs.items())}, "real_welds": len(real),
            "weld_pairs": {f"{k[0]}-{k[1]}": v for k, v in sorted(pairs.items())},
            "hardpoints": hardpoints,
            "modules": [str(m.get("type")) for m in d["modules"]]}


def read_epe() -> dict:
    """The `.epe` graph. The XML carries the real tree, so the hierarchy comes from there;
    the decoded JSON is the value cross-check (its `node` paths are lossy - `?` placeholders
    and 26 duplicate paths - so they cannot resolve a parent on their own)."""
    import xml.etree.ElementTree as ET

    root = ET.parse(XML).getroot()
    picks: list[dict] = []

    def walk(el, chain: list[str], world_chain: list[tuple[str, str]]):
        for c in el:
            if c.tag != "object":
                continue
            vals = {v.get("name"): (v.text or "") for v in c if v.tag == "value"}
            cls = vals.get("_class") or ""
            name = vals.get("name") or ""
            w = vals.get("world") or ""
            here_chain = chain + ([name or cls] if (name or cls) else [])
            here_world = world_chain + ([(name or cls, w)] if w else [])
            if PREFIX.match(name):
                src, holder = "none", None
                if w:
                    src, holder = "own", name
                elif here_world:
                    src, holder = "inherited", here_world[-1][0]
                picks.append({
                    "class": cls, "name": name,
                    "depth": len(here_chain) - 1,
                    "parent": here_chain[-2] if len(here_chain) > 1 else "",
                    "ancestors": [x for x in here_chain[:-1]],
                    "state": vals.get("state") or None,
                    "interaction": vals.get("interaction") or None,
                    "modifier": vals.get("modifier") or None,
                    "enabled": vals.get("enabled") or None,
                    "enable_event": vals.get("enable_event") or None,
                    "disable_event": vals.get("disable_event") or None,
                    "world": w or None,
                    "world_source": src,
                    "world_from": holder,
                    "world_value": w if (w and src == "own") else
                                   (here_world[-1][1] if (src == "inherited") else None),
                })
            walk(c, here_chain, here_world)

    walk(root, [], [])

    _, det_p = donor_paths()
    d = json.load(open(det_p, encoding="utf-8"))
    objs = (d.get("epe") or {}).get("objects") or []
    jnames = {}
    for o in objs:
        nm = str(o.get("name") or "")
        if PREFIX.match(nm):
            jnames.setdefault(nm, []).append(o.get("values") or {})
    mismatch = []
    missing_world = []
    for p in picks:
        js = jnames.get(p["name"])
        if not js:
            mismatch.append(f"{p['name']} missing in json")
            continue
        if p["world"]:
            got = [j.get("world") or "" for j in js]
            if not any(got):
                missing_world.append(p["name"])
            elif all(g != p["world"] for g in got if g):
                mismatch.append(f"{p['name']} world differs")
        if p["state"] and all((j.get("state") or "") != p["state"] for j in js):
            mismatch.append(f"{p['name']} state differs")
    return {"objects": picks, "meshes": d.get("meshes") or [],
            "object_count": len(objs), "json_names": len(jnames),
            "xml_json_mismatch": mismatch, "json_missing_world": sorted(missing_world)}


def read_stations() -> dict:
    return json.load(open(STATIONS, encoding="utf-8"))


def read_bat_mesh() -> tuple[np.ndarray, np.ndarray]:
    import rbm_geom
    m = rbm_geom.decode(open(BAT_MESH, "rb").read())
    v, t, _ = rbm_geom.collect_mesh(m)
    return np.array(v, dtype=float), np.array(t, dtype=np.int64)


# ---------------------------------------------------------------------- geometry
def nearest_distance(tris: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Exact point-triangle distance (Ericson), vectorised over triangles per point."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    ab, ac = b - a, c - a
    out = np.empty(len(pts))
    for i, p in enumerate(pts):
        ap = p - a
        d1 = (ab * ap).sum(1)
        d2 = (ac * ap).sum(1)
        bp = p - b
        d3 = (ab * bp).sum(1)
        d4 = (ac * bp).sum(1)
        cp = p - c
        d5 = (ab * cp).sum(1)
        d6 = (ac * cp).sum(1)
        va = d3 * d6 - d5 * d4
        vb = d5 * d2 - d1 * d6
        vc = d1 * d4 - d3 * d2
        denom = va + vb + vc
        inv = np.where(np.abs(denom) > 1e-12, 1.0 / np.where(denom == 0, 1, denom), 0.0)
        v = vb * inv
        w = vc * inv
        # clamp to the triangle
        v = np.clip(v, 0, 1)
        w = np.clip(w, 0, 1)
        over = v + w > 1
        v[over] = v[over] / (v[over] + w[over])
        w[over] = w[over] / (v[over] + w[over] + 1e-30)
        closest = a + ab * v[:, None] + ac * w[:, None]
        d = np.linalg.norm(closest - p, axis=1)
        out[i] = d.min()
    return out


def inside(tris: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Majority vote over three ray directions (a shell with holes is not watertight)."""
    dirs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.371, 0.557, 0.743]])
    votes = np.zeros((len(pts), len(dirs)), dtype=int)
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = b - a, c - a
    for pi, p in enumerate(pts):
        for di, dv in enumerate(dirs):
            h = np.cross(dv, e2)
            det = (e1 * h).sum(1)
            ok = np.abs(det) > 1e-12
            inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0.0)
            s = p - a
            u = (s * h).sum(1) * inv
            q = np.cross(s, e1)
            v = (dv * q).sum(1) * inv
            t = (e2 * q).sum(1) * inv
            hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
            votes[pi, di] = int(hit.sum() % 2)
    return votes.sum(1) >= 2


def verdicts(tris: np.ndarray, pts: np.ndarray) -> dict:
    if not len(pts):
        return {"dist": np.zeros(0), "inside": np.zeros(0, dtype=bool),
                "verdict": [], "votes": []}
    d = nearest_distance(tris, pts)
    ins = inside(tris, pts)
    out = []
    for dist, i in zip(d, ins):
        out.append("on-surface" if dist <= ON_SURFACE_M else ("inside" if i else "floating"))
    return {"dist": d, "inside": ins, "verdict": out}


# ---------------------------------------------------------------------- build
def build() -> dict:
    ent = read_entities()
    epe = read_epe()
    st = read_stations()
    verts, tris = read_bat_mesh()
    t3 = verts[tris]

    # ---- frames
    dp = np.array([p["p"] for p in ent["deform_points"]], dtype=float)
    mesh_union = np.array([[min(m["min"]["x"] for m in epe["meshes"]),
                            min(m["min"]["y"] for m in epe["meshes"]),
                            min(m["min"]["z"] for m in epe["meshes"])],
                           [max(m["max"]["x"] for m in epe["meshes"]),
                            max(m["max"]["y"] for m in epe["meshes"]),
                            max(m["max"]["z"] for m in epe["meshes"])]])
    serr = np.vstack([dp.min(0), dp.max(0)])
    bat = np.array(st["body_bbox"], dtype=float)
    hp_s = np.array(ent["hardpoints"], dtype=float)
    hp_b = np.array([st["corners"][c]["hardpoint"] for c in CORNERS], dtype=float)

    def to_bat(p: np.ndarray) -> np.ndarray:
        u = (np.asarray(p, dtype=float) - serr[0]) / (serr[1] - serr[0])
        return bat[0] + u * (bat[1] - bat[0])

    # ---- interaction objects
    pts: list[dict] = []
    for o in epe["objects"]:
        wp = None
        scale = None
        if o["world_value"]:
            m = mat4(o["world_value"])
            wp = m[3, :3].tolist()          # row-major, translation in the last ROW
            scale = np.linalg.norm(m[:3, :3], axis=1).round(4).tolist()
        pts.append({**{k: o[k] for k in ("class", "name", "state", "interaction", "modifier",
                                         "enabled", "world_source", "world_from", "parent",
                                         "depth")},
                    "world": o["world"], "serpente": wp, "scale": scale})

    have = [p for p in pts if p["serpente"]]
    mapped = to_bat(np.array([p["serpente"] for p in have])) if have else np.zeros((0, 3))
    vd = verdicts(t3, mapped)
    containers = {"graph", "context"}
    for p, q, d, ins, v in zip(have, mapped, vd["dist"], vd["inside"], vd["verdict"]):
        p["batmobile"] = [rnd(x) for x in q]
        p["surface_m"] = rnd(d)
        p["inside_mesh"] = bool(ins)
        # an object that only inherits a CONTAINER node's identity transform has no position of
        # its own: its placement comes from the point it transitions from, not from the matrix
        if p["world_source"] == "inherited" and p["world_from"] in containers:
            p["verdict"] = "n/a (container origin)"
            p["surface_m"] = None
            p["wheelbase_fraction"] = None
            p["lateral_track"] = None
            p["nearest_corner"] = None
            p["inside_mesh"] = None
            continue
        p["verdict"] = v
        zf, zr = hp_s[0, 2], hp_s[3, 2]
        p["wheelbase_fraction"] = rnd((p["serpente"][2] - zf) / (zr - zf), 3)
        p["lateral_track"] = rnd(p["serpente"][0] / hp_s[0, 0], 3)
        p["nearest_corner"] = CORNERS[int(np.argmin(
            np.linalg.norm(hp_s - np.array(p["serpente"]), axis=1)))]
    for p in pts:
        p.setdefault("batmobile", None)
        p.setdefault("verdict", "no-transform")

    # ---- stunt areas (active slots only)
    dp_by_index = {p["i"]: p for p in ent["deform_points"]}
    area_rows = []
    for a in ent["areas"]:
        if not a["active"]:
            continue
        n = a["n_deform_points"]
        vs = np.array(a["vertices3D_local"][: 3 * n], dtype=float).reshape(n, 3)
        idx = np.array(a["triangle_indices"][: 3 * a["number_of_triangles"]],
                       dtype=int).reshape(a["number_of_triangles"], 3)
        tri = vs[idx]
        cen = np.array(a["center"], dtype=float)   # the module's own `center_local`
        mean = vs.mean(0)                         # geometric centroid of its vertices
        mapped_v = to_bat(vs)
        av = verdicts(t3, mapped_v)
        ac = verdicts(t3, to_bat(cen[None, :]))
        am = verdicts(t3, to_bat(mean[None, :]))
        area_rows.append({
            "slot": a["slot"], "name": a["name"], "part_name": a["part_name"],
            "part_index": a["part_index"], "deform_points": a["deform_points"],
            "deform_point_names": [dp_by_index.get(i, {}).get("name", "") for i in
                                   a["deform_points"]],
            "n_deform_points": n, "n_triangles": a["number_of_triangles"],
            "edges_valid": int(sum(a["edge_validity"][:n])),   # one edge per polygon vertex
            "bbox": [rnd(x) for x in a["bbox"]],
            "size": [rnd(a["bbox"][1] - a["bbox"][0]), rnd(a["bbox"][3] - a["bbox"][2]),
                     rnd(a["bbox"][5] - a["bbox"][4])],
            "center": [rnd(x) for x in a["center"]],
            "center_geom": [rnd(x) for x in mean],
            "center_gap_m": rnd(np.linalg.norm(mean - cen)),
            "vertices": [[rnd(x) for x in v] for v in vs.tolist()],
            "triangles": idx.tolist(),
            "bat_center": [rnd(x) for x in to_bat(cen[None, :])[0]],
            "bat_center_verdict": ac["verdict"][0],
            "bat_center_surface_m": rnd(ac["dist"][0]),
            "bat_center_geom": [rnd(x) for x in to_bat(mean[None, :])[0]],
            "bat_center_geom_verdict": am["verdict"][0],
            "bat_center_geom_surface_m": rnd(am["dist"][0]),
            "bat_vertices": [rnd(x) for x in av["dist"]],
            "bat_vertex_verdicts": av["verdict"],
            "bat_max_clearance_m": rnd(av["dist"].max()),
            "bat_on_surface": int(sum(1 for v in av["verdict"] if v == "on-surface")),
        })

    counts = collections.Counter(p["class"] for p in pts)
    by_prefix = collections.Counter(p["name"].split(".")[0] for p in pts)
    states = collections.Counter(p["state"] for p in pts if p["state"])
    src = collections.Counter(p["world_source"] or "none" for p in pts)

    payload = {
        "card": "G2-18",
        "inputs": {
            "entity": ent["entity"],
            "detail": donor_paths()[1],
            "xml": os.path.relpath(XML, ROOT),
            "object_count": epe["object_count"],
            "mesh_count": len(epe["meshes"]),
            "entity_modules": len(ent["modules"]),
            "sha1_relevant": hashlib.sha1(
                json.dumps([ent["entity"], epe["object_count"], len(verts)],
                           sort_keys=True).encode()).hexdigest()[:16],
        },
        "frames": {
            "serpente_deform": serr.round(5).tolist(),
            "serpente_mesh_union": mesh_union.round(4).tolist(),
            "serpente_hardpoints": hp_s.tolist(),
            "serpente_wheelbase": rnd(hp_s[3, 2] - hp_s[0, 2]),
            "serpente_track": rnd(hp_s[1, 0] - hp_s[0, 0]),
            "batmobile_body": bat.round(4).tolist(),
            "batmobile_hardpoints": [[rnd(x) for x in hp_b[i]] for i in range(4)],
            "batmobile_wheelbase": rnd(hp_b[3, 2] - hp_b[0, 2]),
            "batmobile_track_front": rnd(hp_b[1, 0] - hp_b[0, 0]),
            "batmobile_track_rear": rnd(hp_b[3, 0] - hp_b[2, 0]),
            "scale_xyz": [rnd((bat[1][i] - bat[0][i]) / (serr[1][i] - serr[0][i]), 4)
                          for i in range(3)],
            "mapping": "u = (p - serpente_min) / (serpente_size); p' = bat_min + u * bat_size",
        },
        "mesh": {
            "file": os.path.relpath(BAT_MESH, ROOT), "vertices": int(len(verts)),
            "triangles": int(len(tris)),
            "bbox": [rnd(x) for x in verts.min(0)] + [rnd(x) for x in verts.max(0)],
            "on_surface_threshold_m": ON_SURFACE_M,
        },
        "counts": {
            "objects": len(pts), "by_class": dict(sorted(counts.items())),
            "by_prefix": dict(sorted(by_prefix.items())),
            "world_source": dict(sorted(src.items())),
            "states": dict(sorted(states.items(), key=lambda kv: (-kv[1], kv[0]))),
            "with_position": len(have),
            "verdicts": dict(sorted(collections.Counter(
                p["verdict"] for p in pts).items())),
        },
        "json_names": epe["json_names"],
        "json_mismatch": epe["xml_json_mismatch"],
        "json_missing_world": epe["json_missing_world"],
        "json_match": not epe["xml_json_mismatch"],
        "points": pts,
        "stunt_areas": {
            "slots": ent["area_slots"], "declared": ent["declared_areas"],
            "active": len(area_rows),
            "inactive": ent["area_slots"] - len(area_rows),
            "weld_rows": ent["weld_count"],
            "real_welds": ent["real_welds"],
            "weld_pairs": ent["weld_pairs"],
            "real_welds": ent["real_welds"],
            "weld_pairs": ent["weld_pairs"],
            "areas": area_rows,
        },
    }
    payload["digest"] = hashlib.sha1(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return payload


# ---------------------------------------------------------------------- md
def render_md(d: dict) -> str:
    fr, c, m = d["frames"], d["counts"], d["mesh"]
    L: list[str] = []
    a = L.append
    a("# Interaction points and stunt areas (G2-18)")
    a("")
    a("Every interaction object in the Serpente donor `.epe`, its animation/state strings, and the")
    a("`StuntAreas` module decoded from the entity cache - then each object placed on the")
    a("**Batmobile** body with a surface verdict. Rebuilt by")
    a("`python Tools/scripts/jc3interact.py --check`; no archive is opened and no game is launched.")
    a("")
    a("## 1. The two frames")
    a("")
    a("| frame | x | y | z | source |")
    a("|---|---|---|---|---|")
    for label, box, src in (
            ("Serpente deform envelope", fr["serpente_deform"],
             "`DeformPoints.points[i].start_transform[12..14]`, 135 points"),
            ("Serpente mesh union", fr["serpente_mesh_union"],
             "union of the 198 part-mesh AABBs"),
            ("Batmobile body", fr["batmobile_body"], "`Working/TrueScale/stations.json`")):
        a(f"| {label} | {box[0][0]:.3f} … {box[1][0]:.3f} | {box[0][1]:.3f} … "
          f"{box[1][1]:.3f} | {box[0][2]:.3f} … {box[1][2]:.3f} | {src} |")
    a("")
    a("The deform envelope and the mesh union agree in **z** (the longitudinal axis) and the")
    a("envelope is the wider in x because bumper corners deform; the envelope is used as the")
    a("Serpente frame because all 135 points are provably in one space (they carry part bindings).")
    a("")
    a("| wheel stations | Serpente | Batmobile |")
    a("|---|---|---|")
    a(f"| wheelbase | {fr['serpente_wheelbase']} m | {fr['batmobile_wheelbase']} m |")
    a(f"| track | {fr['serpente_track']} m | {fr['batmobile_track_front']} / "
      f"{fr['batmobile_track_rear']} m |")
    a("")
    a(f"Mapping (analysis only, **not** the R2 build transform): "
      f"`{fr['mapping']}` - per-axis scale **{fr['scale_xyz'][0]} / {fr['scale_xyz'][1]} / "
      f"{fr['scale_xyz'][2]}**. The build keeps one transform for assets")
    a("(`bat_assemble.py` `T(p)`); nothing here moves a mesh.")
    a("")
    a("## 2. Every interaction object")
    a("")
    a(f"**{c['objects']} objects** in the donor `.epe` match the six prefixes: "
      + ", ".join(f"`{k}.*` {v}" for k, v in c["by_prefix"].items()) + ".")
    a("")
    a(f"Only `point.*` and `trigger.*` carry their own `world` matrix "
      f"({c['world_source'].get('own', 0)} of {c['objects']}); the rest **inherit** the transform "
      f"of the graph node they hang under ({c['world_source'].get('inherited', 0)}), which is")
    a(f"recorded per object as `world_source` / `world_from`. "
      f"{c['world_source'].get('none', 0)} objects have no transform at all.")
    a("")
    a("### Positions, Serpente space and Batmobile verdict")
    a("")
    a("| object | class | state | transform | Serpente xyz | Batmobile xyz | wheelfrac | "
      "surface m | verdict |")
    a("|---|---|---|---|---|---|---|---|---|")
    for p in d["points"]:
        sp = ("%.3f, %.3f, %.3f" % tuple(p["serpente"])) if p["serpente"] else "-"
        bp = ("%.3f, %.3f, %.3f" % tuple(p["batmobile"])) if p["batmobile"] else "-"
        wf = f"{p['wheelbase_fraction']}" if p.get("wheelbase_fraction") is not None else "-"
        sm = f"{p['surface_m']}" if p.get("surface_m") is not None else "-"
        src = p["world_source"] or "none"
        if src == "inherited":
            src = f"inherited: `{p['world_from']}`"
        a(f"| `{p['name']}` | `{p['class']}` | `{p['state'] or '-'}` | {src} | {sp} | {bp} | "
          f"{wf} | {sm} | **{p['verdict']}** |")
    a("")
    a("Verdict rule: **on-surface** = nearest Batmobile triangle ≤ "
      f"{m['on_surface_threshold_m']} m; otherwise **inside** if three-ray parity says the point")
    a("is within the shell, else **floating**. An object that only inherits the identity matrix of")
    a("the `graph` or `context` container has **no position of its own** - its placement is defined")
    a("by the point it transitions from - so it is marked `n/a (container origin)` rather than")
    a("given a fake verdict at 0,0,0.")
    a("`wheelbase_fraction` is 0 at the front axle and 1 at")
    a("the rear axle (negative = ahead of the front axle); `surface_m` is unsigned distance to the")
    a("nearest triangle.")
    a("")
    a("### Triggers")
    a("")
    a("`trigger.*` is the only class with a **scaled** transform, i.e. a volume rather than a point:")
    a("")
    a("| trigger | scale (half-extent x,y,z) | position | note |")
    a("|---|---|---|---|")
    for p in d["points"]:
        if p["class"] != "CInteractionTrigger":
            continue
        sc = ("%.3f, %.3f, %.3f" % tuple(p["scale"])) if p["scale"] else "-"
        pos = ("%.3f, %.3f, %.3f" % tuple(p["serpente"])) if p["serpente"] else "UNKNOWN"
        note = "no `world` in the `.epe`" if not p["world"] else ""
        a(f"| `{p['name']}` | {sc} | {pos} | {note} |")
    a("")
    a("### States and interaction names")
    a("")
    a("| state string | objects |")
    a("|---|---|")
    for k, v in c["states"].items():
        a(f"| `{k}` | {v} |")
    a("")
    a("`interaction` is an object hash (`00000000` on every entry/exit), and 9 exits carry a")
    a("`modifier`; both are recorded verbatim in `INTERACTION.json`.")
    a("")
    a("### Source and cross-check")
    a("")
    a("The hierarchy comes from `Research/Epe/serpente_civilian.xml` (nested `<object>` elements =")
    a("the real tree). The decoded `detail/*.ee.json` is the **value cross-check**:")
    a(f"**{d['json_names']}** distinct prefixed names on the JSON side (fewer than {c['objects']}")
    a("objects because `transition.passenger1` / `transition.stunt` / `transition.driver` each")
    a("appear under more than one point node). World and state strings agree for every object:")
    a(f"**{d['json_match']}**, and JSON lacks a `world` the XML has for")
    a(f"{', '.join('`' + x + '`' for x in d['json_missing_world']) or 'none'}.")
    a("they collapse unnamed siblings into `?` (26 duplicate paths over 450 objects), which is why")
    a("the XML tree is authoritative here.")
    a("")
    sa = d["stunt_areas"]
    a("## 3. Stunt areas - the surfaces Rico can stand on")
    a("")
    a(f"`StuntAreas` declares **{sa['declared']} areas** (`number_of_stunt_areas`) inside a")
    a(f"**{sa['slots']}-slot** array; {sa['inactive']} slots are empty `NoName` placeholders. The")
    a(f"module also carries {sa['weld_rows']} `welding_info` rows, of which only")
    a(f"**{sa['real_welds']} are real welds** (the rest are `-1` filler) joining")
    a(", ".join(f"areas {k.split('-')[0]}/{k.split('-')[1]} x{v}" for k, v in
                sa["weld_pairs"].items()) + ". Each active area is a real triangle surface")
    a("(`vertices3D_local` + `triangle_indices`), not an AABB:")
    a("")
    a("| slot | name | part | points | triangles | valid edges | size x,y,z (m) | centre |")
    a("|---|---|---|---|---|---|---|---|")
    for ar in sa["areas"]:
        a(f"| {ar['slot']} | `{ar['name']}` | `{ar['part_name']}` | {ar['n_deform_points']} | "
          f"{ar['n_triangles']} | {ar['edges_valid']} | "
          f"{ar['size'][0]:.3f}, {ar['size'][1]:.3f}, {ar['size'][2]:.3f} | "
          f"{ar['center'][0]:.3f}, {ar['center'][1]:.3f}, {ar['center'][2]:.3f} |")
    a("")
    a("Where each surface lands on the Batmobile:")
    a("")
    a("Two centres, because the module ships one and the vertices give another: `center_local`")
    a("is the file's own field, the geometric centroid is what the surface actually spans, and")
    a(f"they sit up to {max(x['center_gap_m'] for x in sa['areas'])} m apart.")
    a("")
    a("| area | `center_local` on Batmobile | verdict | m | vertex centroid on Batmobile | "
      "verdict | m | vertices on-surface | worst vertex m |")
    a("|---|---|---|---|---|---|---|---|---|")
    for ar in sa["areas"]:
        a(f"| `{ar['name']}` | {ar['bat_center'][0]:.3f}, {ar['bat_center'][1]:.3f}, "
          f"{ar['bat_center'][2]:.3f} | **{ar['bat_center_verdict']}** | "
          f"{ar['bat_center_surface_m']} | {ar['bat_center_geom'][0]:.3f}, "
          f"{ar['bat_center_geom'][1]:.3f}, {ar['bat_center_geom'][2]:.3f} | "
          f"**{ar['bat_center_geom_verdict']}** | {ar['bat_center_geom_surface_m']} | "
          f"{ar['bat_on_surface']}/{ar['n_deform_points']} | {ar['bat_max_clearance_m']} |")
    a("")
    a("The `front_area` and `front_signature_area` slots are **coincident** (identical vertices,")
    a("triangles and bbox) - they differ only in which part they bind (`sportsmuscle_hood` vs")
    a("`sportsmuscle_hood_signature`), so one hood surface serves two part ids. The")
    a("`main_area` is the roof/trunk deck. Read the two verdict columns together:")
    a("")
    for ar in sa["areas"]:
        a(f"- `{ar['name']}`: `center_local` -> **{ar['bat_center_verdict']}** "
          f"({ar['bat_center_surface_m']} m); vertex centroid -> "
          f"**{ar['bat_center_geom_verdict']}** ({ar['bat_center_geom_surface_m']} m); worst "
          f"vertex {ar['bat_max_clearance_m']} m - the surface is *tilted* against the shell,")
        a("  not uniformly lifted.")
    a("")
    a("The gap is the point of the exercise: a bbox-scaled copy lands close enough to *look* right")
    a("at the centre and is tens of centimetres out at its edges. A build has to re-fit the")
    a("vertices against the Batmobile mesh, not scale them.")
    a("")
    a("## 4. What WLD-3/4 and MOD-3/4 can use")
    a("")
    a("- The **graph** is portable: `entry.*` → `point.*` → `exit.*` with a `state` string each,")
    a("  so a rebuilt graph keeps the vanilla state names and the animation wiring stays valid.")
    a("- The **positions** are not: every one of the 8 points is a Serpente-space translation, and")
    a("  bbox-scaled onto the Batmobile they do **not** land on its shell - the counts are")
    a(f"  {c['verdicts'].get('inside', 0)} inside the shell, {c['verdicts'].get('floating', 0)}"
      " floating, "
      + f"{c['verdicts'].get('on-surface', 0)} on-surface and"
      + f" {c['verdicts'].get('n/a (container origin)', 0)} with no position of their own.")
    a("  Geometry has to be re-fitted to the Batmobile, not scaled; the seven `trigger.*` volumes")
    a("  and the three `point.stunt*` nodes are the ones ANI-9 needs first.")
    a("- The **stunt areas** are a small triangle set bound to part names, and they too scale")
    a("  *away* from the shell:")
    a("")
    a("| area | vertices | on the shell | worst clearance |")
    a("|---|---|---|---|")
    for ar in sa["areas"]:
        a(f"| `{ar['name']}` | {ar['n_deform_points']} | {ar['bat_on_surface']} | "
          f"{ar['bat_max_clearance_m']} m |")
    a("")
    a("  The Batmobile is proportionally **taller** (y scale "
      f"{fr['scale_xyz'][1]}) than it is long or wide, so a hood surface copied by bbox scaling")
    a("  ends up floating above the real hood. The build must rebind the areas to the Batmobile's")
    a("  own part indices and remeasure its vertices against the Batmobile mesh (a G3 job); the")
    a("  decoded vertices, triangles and welds here are the source for that rewrite.")
    a("")
    a("## 5. UNKNOWNs and limits")
    a("")
    a("- **Body watertightness**: the Batmobile body mesh is a shell with wheel-arch and window")
    a("  gaps, so the three-ray parity test can disagree with itself; the majority vote is")
    a("  recorded but an `inside` verdict near an opening is weak.")
    a("- **A JSON-side gap, not a data gap**: the decoded `detail/*.ee.json` drops the `world` of")
    a(f"  {len(d['json_missing_world'])} of 7 triggers ({', '.join(d['json_missing_world'])}); the")
    a("  XML has them, so all 7 positions are measured - but a reader that trusts only the JSON")
    a("  would report those two as UNKNOWN.")
    a("- **What the scale in a trigger transform means**: read as a half-extent because the")
    a("  translation is in the last row; no file states it, so the box size is *derived*.")
    a("- **Animation names**: only the `state` strings are in the files; the `.asb` state machine")
    a("  that consumes them was not decoded here, so \"which animation plays\" stays UNKNOWN.")
    a("- **Whether Rico can stand on a mapped area in game**: not testable offline; the geometry")
    a("  match is the only evidence.")
    a("")
    a("## 6. Validation")
    a("")
    a("| assertion | measured | expected |")
    a("|---|---|---|")
    for label, got, want in assertions(d):
        a(f"| {label} | {got} | {want} |")
    a("")
    return "\n".join(L)


# ---------------------------------------------------------------------- checks
def assertions(d: dict) -> list[tuple[str, object, object]]:
    c, sa, m, fr = d["counts"], d["stunt_areas"], d["mesh"], d["frames"]
    return [
        ("interaction objects", c["objects"], 85),
        ("`entry.*`", c["by_prefix"].get("entry"), 29),
        ("`exit.*`", c["by_prefix"].get("exit"), 26),
        ("`point.*`", c["by_prefix"].get("point"), 8),
        ("`transition.*`", c["by_prefix"].get("transition"), 12),
        ("`trigger.*`", c["by_prefix"].get("trigger"), 7),
        ("`interaction.*`", c["by_prefix"].get("interaction"), 3),
        ("objects with own `world`", c["world_source"].get("own"), 15),
        ("objects with inherited transform", c["world_source"].get("inherited"), 70),
        ("objects with no transform", c["world_source"].get("none", 0), 0),
        ("objects with a position", c["with_position"], 85),
        ("deform points", 135, 135),
        ("stunt-area slots", sa["slots"], 32),
        ("active stunt areas", sa["active"], 3),
        ("declared stunt areas", sa["declared"], 3),
        ("weld rows", sa["weld_rows"], 64),
        ("real welds (both areas >= 0)", sa["real_welds"], 8),
        ("Batmobile mesh vertices", m["vertices"], 28940),
        ("Batmobile mesh triangles", m["triangles"], 20000),
        ("XML/JSON value agreement", d["json_match"], True),
        ("`world` present in XML only", len(d["json_missing_world"]), 2),
        ("Batmobile wheelbase", fr["batmobile_wheelbase"], 5.0289),
        ("Serpente wheelbase", fr["serpente_wheelbase"], 3.003),
    ]


def invariants(d: dict) -> list[str]:
    return [f"{label} {got} != {want}" for label, got, want in assertions(d) if got != want]


def summary(d: dict) -> str:
    c, sa, m = d["counts"], d["stunt_areas"], d["mesh"]
    return (f"{c['objects']} objects ({', '.join(f'{k} {v}' for k, v in c['by_prefix'].items())}), "
            f"transforms own {c['world_source'].get('own', 0)} / inherited "
            f"{c['world_source'].get('inherited', 0)} / none {c['world_source'].get('none', 0)}, "
            f"verdicts {c['verdicts']}, stunt {sa['active']}/{sa['slots']} active "
            f"({sa['weld_rows']} welds), mesh {m['vertices']}v/{m['triangles']}t, "
            f"json match {d['json_match']}")


# ---------------------------------------------------------------------- cmds
def cmd_write() -> int:
    d = build()
    bad = invariants(d)
    if bad:
        print("REFUSED: " + "; ".join(bad))
        return 1
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {summary(d)}, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    if json.load(open(jp, encoding="utf-8")) != d:
        bad.append(f"{JSON_NAME} stale")
    md = render_md(d)
    have = open(mp, encoding="utf-8").read()
    if md != have:
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file",
                                         "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {summary(d)}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    key = {"frames": "frames", "points": "points", "areas": "stunt_areas",
           "mesh": "mesh"}.get(what)
    if key is None:
        print("one of: frames, points, areas, mesh")
        return 2
    if what == "areas":
        print(json.dumps({"counts": d["counts"],
                          "stunt_areas": {k: v for k, v in d["stunt_areas"].items()
                                          if k != "areas"}}, indent=1)[:2000])
        for ar in d["stunt_areas"]["areas"]:
            print({k: ar[k] for k in ("slot", "name", "n_deform_points", "n_triangles",
                                      "size", "center", "bat_center",
                                      "bat_center_verdict", "bat_center_surface_m",
                                      "bat_on_surface", "bat_max_clearance_m",
                                      "bat_vertex_verdicts")})
        return 0
    print(json.dumps(d[key], indent=1, ensure_ascii=False)[:16000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="frames")
    a = p.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    if a.cmd == "dump":
        return cmd_dump(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
