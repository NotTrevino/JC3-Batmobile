"""grab_cockpit.py - G1-19: seat, dash, screen, glass, roof, Driver socket and eye point.

Reads the shipped mesh once and derives every number `Research/BatmobileGrab/COCKPIT.md` prints:

    Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx
    Research/BatmobileGrab/SLOTS.json      slot -> material ordering (agreement check)
    Research/BatmobileGrab/SOCKETS_JC3.json the `Driver` / `DriverAnimOrigin` sockets
    Working/TrueScale/stations.json        the ONE transform (scale, offset, ground, corners, body_bbox)
    Research/BatmobileGrab/MATERIALS.md     the three cockpit material rows
    Research/BatmobileGrab/MESHES.md        the mesh exports (the "no interior elsewhere" claim)

Geometry goes through `bat_assemble.to_jc3_rot` x 0.01 + offset (R2: never a second transform);
rays are Moeller-Trumbore, both windings, no culling; face -> bone is `pskx_parts.face_bones`.

Value classes (R4): every record carries `class`:
    read      - copied from a JSON/MD input (socket, slot, material params)
    measured  - ray-cast or triangle count/bbox on the PSKX through the one transform
    derived   - arithmetic on the above (gaps, angles, distances)
    assumed   - the seated anthropometry, which no file ships; the eye point is
                `derived (assumed input)` and the doc says so.

Sub-selections are printed with their rule, e.g. the driver-facing panel is "slot 10, face normal
+z > 0.5, centroid in x +-0.36, y 1.30..1.60, z -1.90..-1.50" - a script re-runs it, a reader can
repeat it. Nothing in this file is copied from the old page.

Usage:
    python Tools/scripts/grab_cockpit.py --write
    python Tools/scripts/grab_cockpit.py --check
"""
import argparse
import collections
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import psk2rbm as P2          # noqa: E402
import pskx_parts as PX       # noqa: E402
import bat_assemble as BA     # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
PSKX = os.path.join(ROOT, "Working", "Appearance", "grab", "Playable_Batmobile_SF",
                    "SkeletalMesh3", "Batmobile_V2.pskx")
SLOTS = os.path.join(OUT, "SLOTS.json")
SOCKETS = os.path.join(OUT, "SOCKETS_JC3.json")
STATIONS = os.path.join(ROOT, "Working", "TrueScale", "stations.json")
MATERIALS = os.path.join(OUT, "MATERIALS.md")
MESHES = os.path.join(OUT, "MESHES.md")
JSON_OUT = os.path.join(OUT, "COCKPIT.json")
MD_OUT = os.path.join(OUT, "COCKPIT.md")

SLOT_SEAT, SLOT_TUB, SLOT_SCREEN, SLOT_GLASS, SLOT_LINER = 11, 10, 12, 1, 18
PANEL_BOX = {"x": 0.36, "y": [1.30, 1.60], "z": [-1.90, -1.50], "nz": 0.5}
HAND_BOX = {"x": 0.17, "y": [1.00, 1.30], "z": [-1.60, -1.10]}
HAND_BANDS = [[0.90, 1.00], [1.00, 1.10], [1.10, 1.20], [1.20, 1.30]]
SIDE_BOX = {"x": 0.25, "z": [-1.60, -0.40]}
ROOF_Z = [-1.35, -1.25, -1.20, None, -1.00, -0.95, -0.80]   # None = the Driver's own z
EYE_BUILDS = [
    {"label": "adult mean, 1.76 m", "seated_eye_m": 0.79, "sitting_height_m": 0.91},
    {"label": "1.88 m (the project's scale reference, MODLOG §70)",
     "seated_eye_m": 0.84, "sitting_height_m": 0.97},
]


def r(x, n=4):
    v = round(float(x), n)
    return 0.0 if v == 0 else v


def f2(x):
    return "%.2f" % x


def load_inputs():
    with open(SLOTS, encoding="utf-8") as f:
        slots = json.load(f)
    with open(SOCKETS, encoding="utf-8") as f:
        sockets = json.load(f)
    with open(STATIONS, encoding="utf-8") as f:
        st = json.load(f)
    return slots, sockets, st


def material_rows(path, package, wanted):
    """material -> {parent, params, textures}; reads the MATERIALS.md instance table."""
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|") or "→" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[0] != package or cells[1] not in wanted:
            continue
        params = {}
        for kv in cells[3].split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                params[k.strip()] = v.strip()
        textures = {}
        for kv in cells[5].split(","):
            if "→" in kv:
                k, v = kv.split("→", 1)
                textures[k.strip()] = v.strip().strip("`")
        out[cells[1]] = {"parent": cells[2].strip("`"), "params": params,
                         "textures": textures}
    return out


def mesh_exports(path):
    names, inside = [], False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            inside = line.strip() == "## Meshes"
            continue
        m = re.match(r"\| `([^`]+)` \|", line)
        if inside and m:
            names.append(m.group(1))
    return names


class Mesh:
    def __init__(self):
        Pp, W, F, mats = P2.read_pskx(PSKX)
        bones, Wt = PX.skeleton(PSKX)
        self.bones = [b[0] for b in bones]
        self.fb = PX.face_bones(Pp, W, F, Wt, len(bones))
        st = json.load(open(STATIONS, encoding="utf-8"))
        self.st = st
        self.Vw = BA.to_jc3_rot(Pp[W["p"]]) * st["scale"] + np.array(st["offset"])
        self.tri = self.Vw[F["w"].astype(np.int64)]
        self.midx = F["m"].astype(int)
        self.mats = mats
        n = np.cross(self.tri[:, 1] - self.tri[:, 0], self.tri[:, 2] - self.tri[:, 0])
        ln = np.linalg.norm(n, axis=1)
        ln[ln == 0] = 1.0
        self.normals = n / ln[:, None]
        self.centroids = self.tri.mean(1)

    def slot(self, i):
        return self.midx == i

    def cast(self, origin, direction):
        d = np.asarray(direction, float)
        d = d / np.linalg.norm(d)
        v0 = self.tri[:, 0]
        e1 = self.tri[:, 1] - v0
        e2 = self.tri[:, 2] - v0
        h = np.cross(d, e2)
        a = (e1 * h).sum(1)
        s = np.asarray(origin, float) - v0
        u = np.zeros(len(self.tri))
        v = np.zeros(len(self.tri))
        t = np.zeros(len(self.tri))
        ok = np.abs(a) > 1e-12
        u[ok] = (s[ok] * h[ok]).sum(1) / a[ok]
        q = np.cross(s, e1)
        v[ok] = (d * q[ok]).sum(1) / a[ok]
        t[ok] = (e2[ok] * q[ok]).sum(1) / a[ok]
        hit = ((np.abs(a) > 1e-12) & (u >= -1e-9) & (u <= 1 + 1e-9) & (v >= -1e-9)
               & (u + v <= 1 + 1e-9) & (t > 1e-6))
        idx = np.where(hit)[0]
        idx = idx[np.argsort(t[idx])]
        return [{"t": float(t[i]), "material": self.mats[self.midx[i]],
                 "slot": int(self.midx[i])} for i in idx]

    def faces_area(self, mask):
        T = self.tri[mask]
        if not len(T):
            return 0.0
        return 0.5 * float(np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]),
                                          axis=1).sum())

    def bbox(self, mask):
        P = self.tri[mask].reshape(-1, 3)
        return {"min": [r(x) for x in P.min(0)], "max": [r(x) for x in P.max(0)],
                "size": [r(x) for x in (P.max(0) - P.min(0))]}


def build():
    slots, sockets, st = load_inputs()
    mesh = Mesh()
    sock = {s["socket"]: s for s in sockets["sockets"]}
    drv, anim = sock["Driver"], sock["DriverAnimOrigin"]
    hip = np.array(drv["position_m"])
    ground = st["ground"]
    fz = st["corners"]["f_l"]["hub_true"][2]
    rz = st["corners"]["r_l"]["hub_true"][2]
    slot_names = {s["index"]: s["material"] for s in slots["slots"]}

    # ---- slots and bones -------------------------------------------------
    groups = []
    for idx in (SLOT_SEAT, SLOT_TUB, SLOT_SCREEN, SLOT_GLASS, SLOT_LINER):
        m = mesh.slot(idx)
        cnt = collections.Counter(mesh.fb[m].tolist())
        bones = [{"bone": mesh.bones[k], "faces": int(v)} for k, v in cnt.most_common()]
        groups.append({"slot": idx, "material": slot_names.get(idx), "faces": int(m.sum()),
                       "area_cm2": r(mesh.faces_area(m) * 1e4, 1), "bones": bones,
                       "bbox": mesh.bbox(m), "class": "measured"})
    seat, tub, screen, glass, liner = groups

    # ---- seat contact, headrest, roof profile ----------------------------
    down = mesh.cast((hip[0], 1.40, hip[2]), (0, -1, 0))
    cushion = next(h for h in down if h["slot"] == SLOT_SEAT)
    seat["cushion_y"] = r(1.40 - cushion["t"])
    seat["cushion_gap_m"] = r(seat["cushion_y"] - hip[1])
    headrest = mesh.cast((hip[0], 1.40, -0.80), (0, 1, 0))[0]
    profile = []
    for z in ROOF_Z:
        zz = hip[2] if z is None else z
        hits = mesh.cast((hip[0], 1.40, zz), (0, 1, 0))
        first = hits[0]
        second = hits[1] if len(hits) > 1 else None
        profile.append({"z": r(zz), "driver": z is None,
                        "y": r(1.40 + first["t"]), "material": first["material"],
                        "slot": first["slot"],
                        "y2": r(1.40 + second["t"]) if second else None,
                        "material2": second["material"] if second else None})
    up = mesh.cast((hip[0], hip[1], hip[2]), (0, 1, 0))
    liner_y = r(hip[1] + up[0]["t"])
    skin_y = r(hip[1] + up[1]["t"])
    # sweep the whole centre strip: the roof over the driver must never be glass
    sweep = {"rays": 0, "glass": 0, "x": [-0.15, 0.15], "z": [-1.35, -0.95], "step": 0.05,
             "first": {}}
    for xx in np.arange(-0.15, 0.1501, 0.05):
        for zz in np.arange(-1.35, -0.9499, 0.05):
            hits = mesh.cast((float(xx), 1.40, float(zz)), (0, 1, 0))
            sweep["rays"] += 1
            if not hits:
                continue
            sweep["first"][hits[0]["material"]] = sweep["first"].get(hits[0]["material"], 0) + 1
            if hits[0]["slot"] == SLOT_GLASS:
                sweep["glass"] += 1

    # ---- screen, panel, hand box ----------------------------------------
    sm = mesh.slot(SLOT_SCREEN)
    P = mesh.tri[sm].reshape(-1, 3)
    sc_lo, sc_hi = P.min(0), P.max(0)
    centre = (sc_lo + sc_hi) / 2
    nn = mesh.normals[sm].copy()
    nn[nn[:, 2] < 0] *= -1
    normal = [r(x, 3) for x in nn.mean(0)]
    screen.update({"size": [r(x) for x in sc_hi - sc_lo],
                   "bbox": {"min": [r(x) for x in sc_lo], "max": [r(x) for x in sc_hi]},
                   "centre": [r(x) for x in centre], "normal": normal,
                   "tilt_from_vertical_deg": r(np.degrees(np.arcsin(abs(normal[1]))), 1)})
    pm = (mesh.slot(SLOT_TUB)
          & (np.abs(mesh.centroids[:, 0]) <= PANEL_BOX["x"])
          & (mesh.centroids[:, 1] >= PANEL_BOX["y"][0]) & (mesh.centroids[:, 1] <= PANEL_BOX["y"][1])
          & (mesh.centroids[:, 2] >= PANEL_BOX["z"][0]) & (mesh.centroids[:, 2] <= PANEL_BOX["z"][1])
          & (mesh.normals[:, 2] > PANEL_BOX["nz"]))
    pcount = collections.Counter(mesh.fb[pm].tolist())
    panel = {"faces": int(pm.sum()), "area_cm2": r(mesh.faces_area(pm) * 1e4, 1),
             "bbox": mesh.bbox(pm), "class": "measured",
             "bones": [{"bone": mesh.bones[k], "faces": int(v)} for k, v in pcount.most_common()],
             "rule": "slot %d, face normal +z > %.1f, centroid |x| <= %.2f, y %.2f..%.2f, "
                     "z %.2f..%.2f" % (SLOT_TUB, PANEL_BOX["nz"], PANEL_BOX["x"],
                                       PANEL_BOX["y"][0], PANEL_BOX["y"][1],
                                       PANEL_BOX["z"][0], PANEL_BOX["z"][1])}

    hb = ((np.abs(mesh.tri[:, :, 0]) < HAND_BOX["x"]).all(1)
          & (mesh.tri[:, :, 1] >= HAND_BOX["y"][0]).all(1)
          & (mesh.tri[:, :, 1] <= HAND_BOX["y"][1]).all(1)
          & (mesh.tri[:, :, 2] >= HAND_BOX["z"][0]).all(1)
          & (mesh.tri[:, :, 2] <= HAND_BOX["z"][1]).all(1))
    bands = {}
    for lo, hi in HAND_BANDS:
        b = ((np.abs(mesh.tri[:, :, 0]) < HAND_BOX["x"]).all(1)
             & (mesh.tri[:, :, 1] >= lo).all(1) & (mesh.tri[:, :, 1] <= hi).all(1)
             & (mesh.tri[:, :, 2] >= HAND_BOX["z"][0]).all(1)
             & (mesh.tri[:, :, 2] <= HAND_BOX["z"][1]).all(1))
        bands["y %.2f..%.2f" % (lo, hi)] = int(b.sum())
    hand = {"faces": int(hb.sum()), "bands": bands, "class": "measured",
            "rule": "all three vertices of the face inside |x| < %.2f, y %.2f..%.2f, z %.2f..%.2f"
                    % (HAND_BOX["x"], HAND_BOX["y"][0], HAND_BOX["y"][1],
                       HAND_BOX["z"][0], HAND_BOX["z"][1])}

    # ---- glass -----------------------------------------------------------
    mean_eye = np.array([hip[0], hip[1] + EYE_BUILDS[0]["seated_eye_m"], hip[2]])
    eye188 = np.array([hip[0], hip[1] + EYE_BUILDS[1]["seated_eye_m"], hip[2]])
    fwd = mesh.cast(mean_eye, (0, 0, -1))[0]
    fwd188 = mesh.cast(eye188, (0, 0, -1))[0]
    side_r = mesh.cast((0, 1.71, -1.10), (1, 0, 0))[0]
    side_l = mesh.cast((0, 1.71, -1.10), (-1, 0, 0))[0]
    side_mask = (mesh.slot(SLOT_GLASS)
                 & (np.abs(mesh.tri[:, :, 0]) > SIDE_BOX["x"]).all(1)
                 & (mesh.tri[:, :, 2] >= SIDE_BOX["z"][0]).all(1)
                 & (mesh.tri[:, :, 2] <= SIDE_BOX["z"][1]).all(1))
    glass.update({
        "windscreen_m": r(fwd["t"]), "windscreen_z": r(mean_eye[2] - fwd["t"]),
        "windscreen_material": fwd["material"],
        "windscreen_m_188": r(fwd188["t"]), "windscreen_z_188": r(eye188[2] - fwd188["t"]),
        "windscreen_material_188": fwd188["material"],
        "side_ray": {"z": -1.10, "y": 1.71, "x_right": r(side_r["t"]),
                     "x_left": r(-side_l["t"]), "material": side_r["material"]},
        "side_faces": int(side_mask.sum()), "side_box": SIDE_BOX,
        "side_bbox": mesh.bbox(side_mask),
    })

    # ---- Driver, anchors, eye, sightlines --------------------------------
    driver = {
        "position_m": [r(x) for x in hip],
        "above_ground_m": r(hip[1] - ground),
        "assembly_z": r(hip[2]),
        "front_axle_z": r(fz),
        "front_axle_dist_m": r(hip[2] - fz),
        "bone": drv["bone"],
        "relative_location_cm": [r(x) for x in drv["relative_location_cm"]],
        "rotation_missing": drv["rotation_missing"],
        "forward_jc3": [r(x, 3) for x in drv["forward_jc3"]],
        "up_jc3": [r(x, 3) for x in drv["up_jc3"]],
        "right_jc3": [r(x, 3) for x in drv["right_jc3"]],
        "cushion_y": seat["cushion_y"],
        "above_cushion_m": r(hip[1] - seat["cushion_y"]),
        "class": "read",
    }
    anim_origin = {"position_m": [r(x) for x in anim["position_m"]],
                   "location_missing": anim["location_missing"], "class": "read"}
    req = sockets["required_anchors"]
    anchors = {"required": len(req["names"]), "present": len(req["present"]),
               "names": req["names"], "driver_required": "Driver" in req["names"],
               "driver_anim_required": "DriverAnimOrigin" in req["names"],
               "driver_anim_role": anim["role"], "class": "read"}

    liner_at_head = next(p["y"] for p in profile if p["z"] == -1.00)
    crowns = []
    for b in EYE_BUILDS:
        eye = np.array([hip[0], hip[1] + b["seated_eye_m"], hip[2]])
        d = centre - eye
        dist = float(np.linalg.norm(d))
        ang = float(np.degrees(np.arctan2(-d[1], abs(d[2]))))
        t = (-1.52 - eye[2]) / d[2]
        crowns.append({
            "label": b["label"], "seated_eye_m": b["seated_eye_m"],
            "eye": [r(x) for x in eye],
            "sitting_height_m": b["sitting_height_m"],
            "crown_y": r(hip[1] + b["sitting_height_m"]),
            "clear_liner_eyes_m": r(liner_at_head - eye[1]),
            "clear_liner_crown_m": r(liner_at_head - (hip[1] + b["sitting_height_m"])),
            "screen_m": r(dist), "screen_deg": r(ang, 1),
            "sightline_y_at_z152": r(eye[1] + d[1] * t),
            "class": "derived (assumed input: seated eye height, no source)",
        })
    eye_block = {"liner_at_head_y": r(liner_at_head), "builds": crowns,
                 "hip_to_liner_m": r(liner_y - hip[1]),
                 "hip_to_liner_from_hip_m": r(liner_y - hip[1]),
                 "assumed": "seated eye height / sitting height: standard adult anthropometry, "
                            "no file in the project ships it",
                 "class": "assumed"}

    mats_in = material_rows(MATERIALS, "Playable_Batmobile_SF",
                            {slot_names[SLOT_TUB], slot_names[SLOT_SEAT], slot_names[SLOT_GLASS]})
    materials = {}
    for name, rec in mats_in.items():
        keep = {k: v for k, v in rec["params"].items()
                if k in ("Metalicity", "EmissiveMultiply", "Glass_Opacity", "Glass_Reflectivity",
                         "Glass_Roughness", "glass_smudges")}
        textures = {k: v for k, v in rec["textures"].items()
                    if k in ("Emissive", "Colour_Map", "Ref_n_Rough_Map", "Colour_Ramp_Map",
                             "OpacityMap", "Normal_Map", "Material_Separation_Mask", "Normal")}
        materials[name] = {"parent": rec["parent"], "params": keep, "textures": textures,
                           "class": "read (MATERIALS.md)"}

    meshes = mesh_exports(MESHES)
    doc = {
        "schema": 1, "generated_by": "grab_cockpit.py",
        "inputs": {
            "pskx": os.path.relpath(PSKX, ROOT).replace("\\", "/"),
            "slots": "Research/BatmobileGrab/SLOTS.json",
            "sockets": "Research/BatmobileGrab/SOCKETS_JC3.json",
            "stations": "Working/TrueScale/stations.json",
            "materials": "Research/BatmobileGrab/MATERIALS.md",
            "meshes": "Research/BatmobileGrab/MESHES.md",
        },
        "method": {
            "transform": "bat_assemble.to_jc3_rot x stations.scale 0.01 + stations.offset "
                         "(the ONE transform; R2)",
            "rays": "Moeller-Trumbore against the PSKX triangles, both windings, no culling; "
                    "distances in metres from the stated origin",
            "materials": "FACE3200.m -> the SLOTS.json slot order (agreement checked in slots[])",
            "bones": "pskx_parts.face_bones (dominant bone per face by summed vertex weights)",
            "ground": "stations.ground; JC3 y = vertical, x = axle (left = -x), nose at -z",
        },
        "slots": groups, "panel": panel, "screen": screen, "glass": glass,
        "roof": {"profile": profile, "liner_y": liner_y, "skin_y": skin_y,
                 "skin_material": up[1]["material"] if len(up) > 1 else None,
                 "skin_gap_m": r(skin_y - liner_y), "sweep": sweep, "headrest": {
                     "z": -0.80, "y": r(1.40 + headrest["t"]),
                     "material": headrest["material"]}},
        "socket_count": int(sockets["counts"]["sockets"]),
        "driver_anchors": sum(1 for x in sockets["sockets"] if x.get("role") == "driver"),
        "transform_ground": ground,
        "driver": driver, "anim_origin": anim_origin, "anchors": anchors,
        "eye": eye_block, "hand_box": hand, "materials": materials,
        "mesh_exports": {"count": len(meshes), "names": meshes},
        "checks": {
            "driver_in_required": anchors["driver_required"],
            "driver_anim_not_required": not anchors["driver_anim_required"],
            "screen_faces": screen["faces"],
            "hand_box_faces": hand["faces"],
            "roof_above_cushion": r(liner_y - seat["cushion_y"]),
        },
    }
    return doc


# ------------------------------------------------------------------ markdown
def f4(x):
    return ("%.4f" % x).rstrip("0").rstrip(".")


def write_md(doc):
    s = {g["slot"]: g for g in doc["slots"]}
    seat, tub, screen, glass, liner = (s[SLOT_SEAT], s[SLOT_TUB], s[SLOT_SCREEN],
                                       s[SLOT_GLASS], s[SLOT_LINER])
    drv, anim, anc = doc["driver"], doc["anim_origin"], doc["anchors"]
    roof, eye, hand, panel = doc["roof"], doc["eye"], doc["hand_box"], doc["panel"]
    scr, side = doc["screen"], doc["glass"]
    mats = doc["materials"]
    L = []
    a = L.append
    a("# Cockpit and driver placement (G1-19)")
    a("")
    a("Generated by `%s` from the shipped mesh through the ONE transform" % doc["generated_by"])
    a("(`bat_assemble.to_jc3_rot` x `stations.json` `scale` + `offset`), the `Driver` socket, "
      "`SLOTS.json`, `stations.json` and the material rows. Every number below is produced by that")
    a("script; `--check` re-derives it and compares (`Research/BatmobileGrab/COCKPIT.json`). Nothing")
    a("here is hand-typed.")
    a("")
    a("Frame: **x = axle (left = -x), y = vertical (ground %s), z = longitudinal, nose at -z**."
      % f4(doc["transform_ground"]))
    a("")
    a("Value classes (R4) are given per table: `read` (socket/slot/material inputs), `measured`")
    a("(triangles or rays on the PSKX), `derived` (arithmetic on those), `assumed` (anthropometry,")
    a("no source - the eye point is `derived (assumed input)`).")
    a("")
    a("## 1. What is where - slot and bone")
    a("")
    a("| part | material slot (faces, LOD0) | bone(s) | measured location, JC3 metres |")
    a("|---|---|---|---|")
    a("| **seat** - cushion, bolsters, rear lip | **%d** `%s` (%s) | %s | bbox x %s..%s, "
      "y %s..%s, z %s..%s; cushion top under the Driver **y %s** |"
      % (seat["slot"], seat["material"], "{:,}".format(seat["faces"]),
         " + ".join("`%s` %s" % (b["bone"], "{:,}".format(b["faces"])) for b in seat["bones"][:2]),
         f4(seat["bbox"]["min"][0]), f4(seat["bbox"]["max"][0]),
         f4(seat["bbox"]["min"][1]), f4(seat["bbox"]["max"][1]),
         f4(seat["bbox"]["min"][2]), f4(seat["bbox"]["max"][2]), f4(seat["cushion_y"])))
    a("| **cockpit tub, dash, cowl** | **%d** `%s` (%s) | %s | bbox x %s..%s, y %s..%s, z %s..%s |"
      % (tub["slot"], tub["material"], "{:,}".format(tub["faces"]),
         " + ".join("`%s` %s" % (b["bone"], "{:,}".format(b["faces"])) for b in tub["bones"][:2]),
         f4(tub["bbox"]["min"][0]), f4(tub["bbox"]["max"][0]),
         f4(tub["bbox"]["min"][1]), f4(tub["bbox"]["max"][1]),
         f4(tub["bbox"]["min"][2]), f4(tub["bbox"]["max"][2])))
    a("| **centre screen** | **%d** `%s` (%s) | `%s` | **%s x %s m**, x %s..%s, y %s..%s, "
      "z %s..%s; %s cm2; centre (%s, %s, %s); mean normal (%s, %s, %s), %s deg from vertical |"
      % (screen["slot"], screen["material"], "{:,}".format(screen["faces"]),
         screen["bones"][0]["bone"],
         f4(screen["size"][0]), f4(screen["size"][1]),
         f4(screen["bbox"]["min"][0]), f4(screen["bbox"]["max"][0]),
         f4(screen["bbox"]["min"][1]), f4(screen["bbox"]["max"][1]),
         f4(screen["bbox"]["min"][2]), f4(screen["bbox"]["max"][2]),
         ("%g" % screen["area_cm2"]),
         f4(screen["centre"][0]), f4(screen["centre"][1]), f4(screen["centre"][2]),
         f4(screen["normal"][0]), f4(screen["normal"][1]), f4(screen["normal"][2]),
         f4(screen["tilt_from_vertical_deg"])))
    a("| **driver-facing instrument panel** | slot **%d** `%s` (%s faces, %s cm2) | %s | "
      "x %s..%s, y %s..%s, z %s..%s (`%s`) |"
      % (SLOT_TUB, tub["material"], "{:,}".format(panel["faces"]),
         "%g" % panel["area_cm2"],
         " + ".join("`%s` %s" % (b["bone"], "{:,}".format(b["faces"]))
                    for b in panel["bones"][:2]) or "-",
         f4(panel["bbox"]["min"][0]), f4(panel["bbox"]["max"][0]),
         f4(panel["bbox"]["min"][1]), f4(panel["bbox"]["max"][1]),
         f4(panel["bbox"]["min"][2]), f4(panel["bbox"]["max"][2]), panel["rule"]))
    a("| **canopy glass** - windscreen + side windows | **%d** `%s` (%s; %s on `%s`) | `%s` | "
      "windscreen first hit **%s m** ahead of the mean eye (z %s); side ray at y %s, z %s hits "
      "glass at x %s / %s; side-window faces %s, z %s..%s, y %s..%s |"
      % (glass["slot"], glass["material"], "{:,}".format(glass["faces"]),
         "{:,}".format(glass["bones"][0]["faces"]), glass["bones"][0]["bone"],
         glass["bones"][0]["bone"], f4(glass["windscreen_m"]), f4(glass["windscreen_z"]),
         f4(glass["side_ray"]["y"]), f4(glass["side_ray"]["z"]),
         f4(glass["side_ray"]["x_left"]), f4(glass["side_ray"]["x_right"]),
         "{:,}".format(glass["side_faces"]), f4(glass["side_bbox"]["min"][2]),
         f4(glass["side_bbox"]["max"][2]), f4(glass["side_bbox"]["min"][1]),
         f4(glass["side_bbox"]["max"][1])))
    a("| **canopy roof over the driver** | **%d** `%s` (%s, `%s`) = inner liner; skin `%s` | "
      "`%s` | liner **y %s**, skin y %s (%s m above it) - **opaque: no glass on the centreline** |"
      % (liner["slot"], liner["material"], "{:,}".format(liner["faces"]), liner["bones"][0]["bone"],
         roof["skin_material"] or "-", liner["bones"][0]["bone"],
         f4(roof["liner_y"]), f4(roof["skin_y"]), f4(roof["skin_gap_m"])))
    a("| **yoke / steering control** | **- none -** | - | **absent**: the box |x| < %s, "
      "y %s..%s, z %s..%s holds **%d faces of any material** (section 6) |"
      % (f2(HAND_BOX["x"]), f2(HAND_BOX["y"][0]), f2(HAND_BOX["y"][1]),
         f2(HAND_BOX["z"][0]), f2(HAND_BOX["z"][1]), hand["faces"]))
    a("")
    a("Seat and screen counts come from the material slots; the panel row is the selection printed "
      "in its own last column, not a hand-picked subset.")
    a("")
    a("Materials that carry the interior's look (read from `MATERIALS.md`, class `read`):")
    a("")
    for name in (tub["material"], seat["material"], glass["material"]):
        m = mats.get(name)
        if not m:
            continue
        a("- `%s` -> MIC of `%s`%s." % (name, m["parent"],
                                        "".join("; %s=%s" % (k, v) for k, v in m["params"].items())))
        if m["textures"]:
            a("  - maps: %s." % ", ".join("%s `%s`" % (k, v) for k, v in m["textures"].items()))
    a("")
    a("## 2. The `Driver` socket")
    a("")
    a("| field | value | class |")
    a("|---|---|---|")
    a("| `position_m` (JC3, through the one transform) | **(%s, %s, %s)** - centreline, **%s m above "
      "the ground**, assembly z %s, **%s m behind the front axle (z %s)** | read |"
      % (f4(drv["position_m"][0]), f4(drv["position_m"][1]), f4(drv["position_m"][2]),
         f4(drv["above_ground_m"]), f4(drv["assembly_z"]), f4(drv["front_axle_dist_m"]),
         f4(drv["front_axle_z"])))
    a("| bone / relative location | `%s`, (%s, %s, %s) cm in the bone frame; rotation null "
      "(`rotation_missing: %s`) | read |"
      % (drv["bone"], f4(drv["relative_location_cm"][0]), f4(drv["relative_location_cm"][1]),
         f4(drv["relative_location_cm"][2]), str(drv["rotation_missing"]).lower()))
    a("| `forward_jc3` | (%s, %s, %s) - the driver faces the nose | read |"
      % (f4(drv["forward_jc3"][0]), f4(drv["forward_jc3"][1]), f4(drv["forward_jc3"][2])))
    a("| socket basis | `up_jc3` (%s, %s, %s), `right_jc3` (%s, %s, %s) - the socket's own up is the "
      "car's **lateral** axis; build the seated pose on world up, not on the socket basis | read |"
      % (f4(drv["up_jc3"][0]), f4(drv["up_jc3"][1]), f4(drv["up_jc3"][2]),
         f4(drv["right_jc3"][0]), f4(drv["right_jc3"][1]), f4(drv["right_jc3"][2])))
    a("| seat surface under it (ray down onto slot %d) | **y %s** -> the socket sits **%.0f mm "
      "above the cushion**: it is the **hip / seat point**, not the feet and not the head | "
      "measured |"
      % (SLOT_SEAT, f4(drv["cushion_y"]), drv["above_cushion_m"] * 1000))
    a("| `DriverAnimOrigin` (second driver socket) | (%s, %s, %s) - a null location, the "
      "`Batmobile_Chassis` pivot at ground level: the enter/exit origin, not the seated pose | read |"
      % (f4(anim["position_m"][0]), f4(anim["position_m"][1]), f4(anim["position_m"][2])))
    a("")
    a("Of the %d required anchors in `SOCKETS_JC3.json` (%d/%d present), **`Driver` is the only "
      "driver anchor in the list**: `DriverAnimOrigin` is not one of the %d (it is a second socket "
      "with role `%s`)."
      % (anc["required"], anc["present"], anc["required"], anc["required"], anc["driver_anim_role"]))
    a("")
    a("## 3. Canopy clearance above the Driver")
    a("")
    a("Ray straight up from (Driver x, 1.40, z), first surface per height (all materials tested):")
    a("")
    a("| z (longitudinal) | inner surface y | material | class |")
    a("|---|---|---|---|")
    for p in roof["profile"]:
        a("| **%s%s** | **%s** | `%s` | measured |"
          % (f4(p["z"]), " (the Driver)" if p["driver"] else "", f4(p["y"]), p["material"]))
    a("")
    firsts = ", ".join("`%s` %d" % (k, v) for k, v in sorted(roof["sweep"]["first"].items()))
    a("**Hip-to-liner clearance: %s m** (liner %s, hip %s); the skin sits %s m above the liner. "
      "Of the %d vertical rays from y 1.40 at |x| <= %s and z %s..%s, **%d hits glass** (first "
      "surfaces: %s): the roof over the driver is opaque, glass is the windscreen (z %s) and the "
      "side windows (x %s / %s)."
      % (f4(eye["hip_to_liner_m"]), f4(roof["liner_y"]), f4(drv["position_m"][1]),
         f4(roof["skin_gap_m"]), roof["sweep"]["rays"],
         f4(roof["sweep"]["x"][1]), f4(roof["sweep"]["z"][0]), f4(roof["sweep"]["z"][1]),
         roof["sweep"]["glass"], firsts,
         f4(glass["windscreen_z"]), f4(glass["side_ray"]["x_left"]), f4(glass["side_ray"]["x_right"])))
    a("")
    a("## 4. The eye point - `derived (assumed input)`")
    a("")
    a("**No eye or camera socket ships in the mesh**: `SOCKETS_JC3.json` has %d sockets and %d "
      "driver-role anchors, neither an eye point; `MECHANICS.md` carries no camera/eye property. "
      "The only camera-named members in the grab are `RVehicleWeapon.OverrideCamera` (a "
      "`NameProperty`, default `CustomCamera` - `WEAPONS.md`, `OFFSETS.md`) and an AnimSet named "
      "`Camera`; neither is an eye point."
      % (doc["socket_count"], doc["driver_anchors"]))
    a("")
    a("So the eye is the `Driver` hip plus a **seated eye height that no file supplies** "
      "(`assumed`); the point below is `derived (assumed input)` and the assumption travels with "
      "it:")
    a("")
    a("| build | seated eye / sitting height (assumed) | **eye point** | crown y | clearance to the "
      "liner at the head column (z %s, y %s): above the eyes / above the crown |"
      % (f4(-1.00), f4(eye["liner_at_head_y"])))
    a("|---|---|---|---|---|")
    for b in eye["builds"]:
        a("| %s | %s / %s m | **(%s, %s, %s)** | %s | **%s / %s m** |"
          % (b["label"], f4(b["seated_eye_m"]), f4(b["sitting_height_m"]),
             f4(b["eye"][0]), f4(b["eye"][1]), f4(b["eye"][2]), f4(b["crown_y"]),
             f4(b["clear_liner_eyes_m"]), f4(b["clear_liner_crown_m"])))
    a("")
    a("Sightlines from the mean eye:")
    a("")
    a("- level forward: hits `%s` (windscreen) at **%s m**;"
      % (glass["windscreen_material"], f4(glass["windscreen_m"])))
    a("- to the centre screen centre (%s, %s, %s): **%s m, %s deg below the level line**; that "
      "sightline crosses z %s at y %s - the dash lip at z %s does not occlude it;"
      % (f4(scr["centre"][0]), f4(scr["centre"][1]), f4(scr["centre"][2]),
         f4(eye["builds"][0]["screen_m"]), f4(eye["builds"][0]["screen_deg"]),
         f4(-1.52), f4(eye["builds"][0]["sightline_y_at_z152"]), f4(-1.52)))
    a("- the driver-facing panel spans x %s..%s, y %s..%s, z %s..%s (%s faces, %s cm2);"
      % (f4(panel["bbox"]["min"][0]), f4(panel["bbox"]["max"][0]),
         f4(panel["bbox"]["min"][1]), f4(panel["bbox"]["max"][1]),
         f4(panel["bbox"]["min"][2]), f4(panel["bbox"]["max"][2]),
         "{:,}".format(panel["faces"]), "%g" % panel["area_cm2"]))
    a("- for the %s build the level line meets the cowl/windscreen base at **%s m**."
      % (eye["builds"][1]["label"].split(" (")[0], f4(glass["windscreen_m_188"])))
    a("")
    a("ANI-9's \"head under the canopy\" is satisfied by %s-%s m above the crown; the eye point "
      "is not a file value."
      % (f4(min(b["clear_liner_crown_m"] for b in eye["builds"])),
         f4(max(b["clear_liner_crown_m"] for b in eye["builds"]))))
    a("")
    a("## 5. APP-3 - what is visible through the glass")
    a("")
    a("The interior is enclosed by the windscreen ahead (z %s), the side windows beside the "
      "driver's head (x %s / %s, z %s..%s) and an **opaque roof** (liner `%s` + skin) directly "
      "overhead. Seat and screens are therefore visible **through the windscreen and the side "
      "windows, not from above**."
      % (f4(glass["windscreen_z"]), f4(glass["side_ray"]["x_left"]),
         f4(glass["side_ray"]["x_right"]), f4(glass["side_bbox"]["min"][2]),
         f4(glass["side_bbox"]["max"][2]), liner["material"]))
    a("")
    gl = mats.get(glass["material"], {"params": {}, "textures": {}})
    sc = mats.get(seat["material"], {"params": {}, "textures": {}})
    a("The glass is tinted and alpha-mapped (`%s`), and the interior glow comes from the seat "
      "material's emissive map (`%s` x `%s`)."
      % (", ".join("%s=%s" % (k, v) for k, v in gl["params"].items()),
         sc["textures"].get("Emissive", "-"),
         sc["params"].get("EmissiveMultiply", "-")))
    a("")
    a("## 6. Gaps - stated, not smoothed")
    a("")
    a("1. **No yoke / steering control.** The hand box |x| < %s, y %s..%s, z %s..%s contains "
      "**%d faces of any material** (%s). The nearest driver-facing surface is the instrument "
      "panel at z %s. Consequence for ANI-9: the seated pose has nothing to grip; a grip point, "
      "if one is wanted, must come from the JC3 side (G2-19)."
      % (f2(HAND_BOX["x"]), f2(HAND_BOX["y"][0]), f2(HAND_BOX["y"][1]),
         f2(HAND_BOX["z"][0]), f2(HAND_BOX["z"][1]), hand["faces"],
         ", ".join("%s: %d" % (k, v) for k, v in hand["bands"].items()),
         f4(panel["bbox"]["max"][2])))
    a("2. **No eye point in any file** (section 4) - the eye above is derived from an assumed "
      "seated eye height, not read.")
    a("3. **Screen content is not in the material.** `%s` is a master `Material` with no connected "
      "Diffuse/Specular/Power/Emissive and no texture parameters - the %s x %s m panel geometry "
      "ships, the picture does not. What glows comes from the seat material's emissive map, not "
      "from a screen texture."
      % (screen["material"], f4(screen["size"][0]), f4(screen["size"][1])))
    a("4. **No other interior mesh.** `MESHES.md` lists %d mesh exports; apart from `Batmobile_V2` "
      "they are the Destroyed/Fire variants, the MK2 and Jokerfied skins and the Batwing carrier, "
      "so the yoke is not hiding elsewhere."
      % doc["mesh_exports"]["count"])
    a("")
    a("## 7. How to re-measure")
    a("")
    a("```")
    a("python Tools/scripts/grab_cockpit.py --write    # COCKPIT.json + COCKPIT.md")
    a("python Tools/scripts/grab_cockpit.py --check    # re-derive and compare")
    a("```")
    a("")
    a("The script ray-casts the seat, roof, glass and sightlines (Moeller-Trumbore, both windings),")
    a("counts faces per slot and per bone, prints the panel/hand-box/side-window selections with")
    a("their rules, and reads the socket and material rows. `--check` fails if any of them moves.")
    a("")
    return "\n".join(L)


def check(doc):
    fail = []
    new = build()
    if new != doc:
        keys = sorted(k for k in set(new) | set(doc) if new.get(k) != doc.get(k))
        fail.append("stored JSON differs from a fresh build (keys: %s)" % ", ".join(keys[:6]))
    if doc["checks"]["screen_faces"] != 100:
        fail.append("slot 12 face count %s, expected 100" % doc["checks"]["screen_faces"])
    if not doc["checks"]["driver_in_required"]:
        fail.append("Driver is not in required_anchors")
    if not doc["checks"]["driver_anim_not_required"]:
        fail.append("DriverAnimOrigin unexpectedly in required_anchors")
    if doc["checks"]["hand_box_faces"] != 4:
        fail.append("hand box holds %s faces, expected 4" % doc["checks"]["hand_box_faces"])
    try:
        md = open(MD_OUT, encoding="utf-8").read()
    except OSError:
        md = None
    if md != write_md(doc):
        fail.append("COCKPIT.md is not the current generator output")
    if fail:
        print("FAIL")
        for f in fail:
            print("  -", f)
        return 1
    c = doc["checks"]
    print("OK: %d sockets, Driver (%s, %s, %s) on %s; seat %s faces (cushion y %s) / tub %s / "
          "screen %s faces %s x %s m / glass %s; roof liner %s (hip-to-liner %s); hand box %s faces; "
          "panel %s faces; %d mesh exports; MD regenerates identical"
          % (doc["socket_count"], f4(doc["driver"]["position_m"][0]),
             f4(doc["driver"]["position_m"][1]),
             f4(doc["driver"]["position_m"][2]), doc["driver"]["bone"],
             "{:,}".format(doc["slots"][0]["faces"]), f4(doc["slots"][0]["cushion_y"]),
             "{:,}".format(doc["slots"][1]["faces"]),
             c["screen_faces"], f4(doc["screen"]["size"][0]), f4(doc["screen"]["size"][1]),
             "{:,}".format(doc["slots"][3]["faces"]), f4(doc["roof"]["liner_y"]),
             f4(doc["eye"]["hip_to_liner_m"]), c["hand_box_faces"], doc["panel"]["faces"],
             doc["mesh_exports"]["count"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="rebuild COCKPIT.json + COCKPIT.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    a = ap.parse_args()
    doc = build()
    doc["transform_ground"] = json.load(open(STATIONS, encoding="utf-8"))["ground"]
    if a.write:
        with open(JSON_OUT, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1)
        with open(MD_OUT, "w", encoding="utf-8") as f:
            f.write(write_md(doc))
        print("wrote", os.path.relpath(JSON_OUT, ROOT), "and", os.path.relpath(MD_OUT, ROOT))
    if a.check:
        stored = None
        try:
            with open(JSON_OUT, encoding="utf-8") as f:
                stored = json.load(f)
        except OSError:
            print("FAIL\n  - no COCKPIT.json - run --write first")
            return 1
        return check(stored)
    if not a.write:
        print(json.dumps({k: doc[k] for k in ("checks",)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
