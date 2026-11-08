"""bm_lights.py - B-03: cut the Batmobile's emissive lamp faces into light parts with CarLight blocks.

The card (`GRAB_BACKLOG.md` §8 `B-03`): "for each lamp (head-lamp lenses, tail strip, wheel-arch
lights, boot light, dashboard), cut its faces into a light part (vanilla pattern: `CarLight` +
`Window`, static), write the `CarLight` block with values from T-18."

What is decoded and what is not (nothing here is invented):

  * The lamp faces ARE decoded. `Research/BatmobileGrab/SLOTS.json` slot 5 is
    `Batmobile_V3_Emissive` (4,576 LOD0 faces); the PSKX `MATT0000` list is `material_0..18`, so
    PSKX material index 5 is that slot. The faces are clustered by shared point and each cluster is
    assigned to a lamp by the dominant bone of its faces (`pskx_parts.face_bones`). The lamp table
    itself (names, kinds, parents, sockets) is an authored input, not a decode: the nose bone feeds
    both head lamps, split by the cluster's own X sign, and the rear arches / tail strips are named
    by hand because no bone is unique to them.
  * The `CarLight` block's *material parameters* are NOT decoded (LIGHT_SYSTEM.md §5, MODLOG
    §102d). Every one of the 44 vanilla `CarLight` blocks in our own donor tree has a byte-identical
    1,085 B pre-static header, so a block is authored the only safe way: header, 16 B mid-static and
    the 6-name texture table are copied from a vanilla light part, only the vertex/index buffers are
    ours. The 24 B/vertex second stream is `(u, v, 0, 0, packed, packed)`; `u,v` are the BmAK UVs and
    the packed pair is copied from the template vertex nearest to ours, because no decoded field
    says what it is (§102d).
  * Geometry goes through the ONE transform (R2): `bat_assemble.to_jc3_rot` + the `stations.json`
    scale/offset. `psk2rbm.to_jc3` is the older reflection and mirrors X; under `to_jc3_rot` every
    lamp's side agrees with its bone's pivot in `BONES.json`, which is the cross-check below.

  * Each lamp's vertices are expressed in its PARENT PART's frame: the ONE transform minus the
    parent's pivot (`Working/Appearance/build_parts/parts_manifest.json` `pivot_m`), because B-02
    emits part RBMs pivot-relative and B-04 sets `parent_space_offset = pivot`. The parent index ->
    part name comes from `Research/JC3Grab/PARTS_TABLE.jsonl`; nothing is typed twice.

Outputs (in --out, default `Working/Appearance/build_lights`):
    sportsmuscle_<lamp>_lod1..N.rbm   one light part per lamp, one CarLight block per LOD
    lights_manifest.json              rows B-04 consumes: part, parent part, pivot, frame, faces,
                                     T-18 rows; plus the T-18 hosting diff and the donor census

Usage:
    python Tools/scripts/bm_lights.py --write
    python Tools/scripts/bm_lights.py --check          # re-derive everything, compare bytes
    python Tools/scripts/bm_lights.py --check --fast   # decode the files only (no re-decimation)
"""
import argparse
import glob
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bat_assemble as BA  # noqa: E402
import psk2rbm as P  # noqa: E402
import pskx_parts as PX  # noqa: E402
import rbm_geom as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PSKX = "Working/Appearance/grab/Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx"
STATIONS = "Working/TrueScale/stations.json"
SLOTS = "Research/BatmobileGrab/SLOTS.json"
BONES = "Research/BatmobileGrab/BONES.json"
SOCKETS = "Research/BatmobileGrab/SOCKETS_JC3.json"
T18 = "Working/Translation/t14_lights.json"
PARTS_MANIFEST = "Working/Appearance/build_parts/parts_manifest.json"
PARTS_TABLE = "Research/JC3Grab/PARTS_TABLE.jsonl"
TEMPLATE = ("Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
            "sportsmuscle_headlight_f_l_01_lod1.rbm")
OUT = "Working/Appearance/build_lights"
EMISSIVE_SLOT = 5
BUDGET_KB = 4915.0                     # R9: Vehicle Model HARD
MAX_LODS = 8                           # probe depth for the donor light LOD count
DONOR_GLOB = ("Builds/test-091/aaf/models/jc_vehicles/01_land/"
              "v0300_car_kensington_sportsmuscle/*light*_lod{i}.rbm")

# Lamp table. `bones` are the dominant bones its clusters are weighted to (decoded from the PSKX
# skeleton); `parent` is the donor vehicle_parts index the part hangs on, resolved to a B-02 part and
# its pivot by `parent_frames()` (PARTS_TABLE.jsonl index -> name, parts_manifest.json name ->
# pivot_m: body 0, wheel_r_l 11, wheel_r_r 12, wheel_f_l 26, wheel_f_r 27); `sockets` are the BmAK
# light components that name the lamp's socket (SOCKETS_JC3.json / t14_lights.json), [] where the rig
# has none. `lamp_elements` is an AUTHORING parameter (how many lens elements the part is budgeted
# for), not a decoded count: it multiplies the donor LOD ceiling and is then capped by the faces the
# lamp actually has, so it can only make an LOD denser up to the real face count.
LAMPS = (
    {"part": "sportsmuscle_headlight_f_l", "kind": "head-lamp lens", "side": "left", "parent": 0,
     "bones": ("Batmobile_Nose_Mesh",), "lamp_elements": 3,
     "sockets": ("HeadLight1", "HeadLight1a", "HeadLight1b")},
    {"part": "sportsmuscle_headlight_f_r", "kind": "head-lamp lens", "side": "right", "parent": 0,
     "bones": ("Batmobile_Nose_Mesh",), "lamp_elements": 3,
     "sockets": ("HeadLight2", "HeadLight2a", "HeadLight2b")},
    {"part": "sportsmuscle_wheel_f_l_arch", "kind": "wheel-arch light", "side": "left", "parent": 26,
     "bones": ("Wheel_Frnt_Left_Disc", "Damper_Left_Front_02"), "lamp_elements": 3,
     "sockets": ("LWheelLight", "LWheelLight_top", "LWheelLight_bottom")},
    {"part": "sportsmuscle_wheel_f_r_arch", "kind": "wheel-arch light", "side": "right", "parent": 27,
     "bones": ("Wheel_Frnt_Right_Disc",), "lamp_elements": 3,
     "sockets": ("RWheelLight", "RWheelLight_top", "RWheelLight_bottom")},
    {"part": "sportsmuscle_wheel_r_l_arch", "kind": "wheel-arch light", "side": "left", "parent": 11,
     "bones": ("Wheel_Rear_Left_Disc",), "lamp_elements": 3, "sockets": ()},
    {"part": "sportsmuscle_wheel_r_r_arch", "kind": "wheel-arch light", "side": "right", "parent": 12,
     "bones": ("Wheel_Rear_Right_Disc",), "lamp_elements": 3, "sockets": ()},
    {"part": "sportsmuscle_tailstrip_r_l", "kind": "tail strip", "side": "left", "parent": 0,
     "bones": ("SUSP2_Wheel_Rear_Left",), "lamp_elements": 1,
     "sockets": ("BrakeLightL", "BrakeTrailL")},
    {"part": "sportsmuscle_tailstrip_r_r", "kind": "tail strip", "side": "right", "parent": 0,
     "bones": ("SUSP2_Wheel_Rear_Right",), "lamp_elements": 1,
     "sockets": ("BrakeLightR", "BrakeTrailR")},
)

# Light components the rig carries that the Emissive material gives NO faces. Each row is measured
# (distance to the nearest lamp face) rather than assumed; see `no_face_lamps()`.
NO_FACE = (
    {"socket": "Dashboard_Light", "why": "cockpit interior lamp"},
    {"socket": "BootLight", "why": "boot lamp"},
    {"socket": "Headlight_Centre", "why": "centre head-lamp"},
)


def rel(p):
    return os.path.normpath(p).replace("\\", "/")


def load(path):
    return json.load(open(os.path.join(ROOT, path), encoding="utf-8"))


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ inputs

def load_mesh():
    """PSKX -> (Vw, UVw, tris, F, bones, dominant bone per face) in the ONE transform."""
    st = load(STATIONS)
    scale, offset = st["scale"], np.array(st["offset"], dtype=np.float64)
    path = os.path.join(ROOT, PSKX)
    if not os.path.exists(path):
        raise SystemExit(f"BM-03 source mesh missing: {PSKX}")
    Pp, W, F, mats = P.read_pskx(path)
    bones, Wt = PX.skeleton(path)
    fb = PX.face_bones(Pp, W, F, Wt, len(bones))
    Vw = BA.to_jc3_rot(Pp[W["p"]]) * scale + offset          # per wedge, metres
    UVw = np.stack([W["u"], W["v"]], 1).astype(np.float64)
    return dict(path=path, scale=scale, offset=offset, Pp=Pp, W=W, F=F, mats=mats,
                bones=bones, fb=fb, Vw=Vw, UVw=UVw, tris=W["p"][F["w"]].astype(np.int64))


def donor_part_names():
    """Donor sportsmuscle `vehicle_parts` index -> part name, from PARTS_TABLE.jsonl."""
    for line in open(os.path.join(ROOT, PARTS_TABLE), encoding="utf-8"):
        row = json.loads(line)
        if "sportsmuscle_vehicle_parts" in row.get("module", ""):
            return {int(p["i"]): p["n"] for p in row["parts"]}
    raise SystemExit(f"{PARTS_TABLE}: no sportsmuscle_vehicle_parts row")


def parent_frames():
    """Donor parent index -> (donor name, B-02 part name, B-02 entry carrying pivot_m).

    Two files, no typed map: index -> name from PARTS_TABLE.jsonl, name -> pivot from B-02's
    parts_manifest.json. An index the two files cannot join is fatal, never defaulted to 0.
    """
    donor = donor_part_names()
    b02 = {e["name"]: e for e in load(PARTS_MANIFEST)["entries"]}
    out = {}
    for idx, name in donor.items():
        short = name[len("sportsmuscle_"):] if name.startswith("sportsmuscle_") else name
        if short in b02:
            out[idx] = (name, short, b02[short])
    return out


def new_part_indices():
    """Lamp part -> part index, but only where t14_lights.json assigns one to the NEW part.

    t14's `light_parts` rows are donor parts; a donor row names its replacement in `new_part`, and
    the replacement has its own row with the index. So the index belongs to the row whose `part` is
    a `new_part` elsewhere (the front arch lamps: 42/43), never to the donor row that asked for it.
    """
    doc = load(T18).get("light_parts", [])
    new_names = {p["new_part"] for p in doc if p.get("new_part")}
    return {p["part"]: p["part_index"] for p in doc
            if p["part"] in new_names and p.get("part_index") is not None}


def window_census():
    """What the donor light meshes actually carry: Window counts per file and per family."""
    files = with_w = 0
    fam = defaultdict(list)
    for i in range(1, MAX_LODS + 1):
        for f in sorted(glob.glob(os.path.join(ROOT, DONOR_GLOB.format(i=i)))):
            try:
                m = R.decode(open(f, "rb").read())
            except R.RbmError:
                continue
            names = [R.BLOCK_NAMES.get(b.type_hash) for b in m.blocks]
            if "CarLight" not in names:
                continue
            files += 1
            has = "Window" in names
            fam[os.path.basename(f).rsplit("_lod", 1)[0]].append(has)
            with_w += has
    return {"files": files, "files_with_window": with_w, "files_without_window": files - with_w,
            "families": len(fam),
            "families_always_with_window": sorted(k for k, v in fam.items() if all(v)),
            "families_never_with_window": sorted(k for k, v in fam.items() if not any(v)),
            "families_mixed": sorted(k for k, v in fam.items() if any(v) and not all(v))}


def t18_hosting(entries):
    """The T-18 hosting diff: what this build hosts vs t14_lights.json's own part map."""
    doc = load(T18)
    rows = {r["id"]: r for r in doc["rows"]}
    hosted = [r["row"] for e in entries for r in e["t18_rows"]]
    mapped = {rid for rid, r in rows.items() if r.get("targets")}
    part_of = {}
    for p in doc.get("light_parts", []):
        for rid in p.get("hosts", []):
            part_of.setdefault(rid, p["part"])
    moves = []
    for e in entries:
        for r in e["t18_rows"]:
            was = part_of.get(r["row"])
            if was and was != e["part"]:
                moves.append({"row": r["row"], "t18_part": was, "now_on": e["part"]})
    return {
        "rows_hosted": sorted(hosted),
        "rows_hosted_count": len(hosted),
        "rows_hosted_mapped": sorted(r for r in hosted if r in mapped),
        "rows_hosted_unmapped": sorted(r for r in hosted if r not in mapped),
        "rows_in_t18_map_not_hosted": sorted(set(part_of) - set(hosted)),
        "rows_hosted_outside_t18_map": sorted(set(hosted) - set(part_of)),
        "rows_mapped_but_unassigned_in_t18": sorted(mapped - set(part_of)),
        "moved": moves,
        "source": "t14_lights.json light_parts[].hosts (T-18's own part->row map)",
    }


def clusters(faces):
    """Union-find over shared POINTS so a UV seam does not split one lens."""
    tri = faces
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for t in tri:
        for a, b in ((t[0], t[1]), (t[1], t[2])):
            ra, rb = find(int(a)), find(int(b))
            if ra != rb:
                parent[ra] = rb
    groups = defaultdict(list)
    for k, t in enumerate(tri):
        groups[find(int(t[0]))].append(k)
    return list(groups.values())


def assign(mesh):
    """Every Emissive face -> one lamp, by dominant bone family + the cluster's own X sign."""
    F, tris, fb, bones, Vw = mesh["F"], mesh["tris"], mesh["fb"], mesh["bones"], mesh["Vw"]
    wedge = F["w"]                                    # per face: 3 WEDGE indices into Vw
    sel = np.nonzero(F["m"] == EMISSIVE_SLOT)[0]
    face_of = {int(k): i for i, k in enumerate(sel)}       # F index -> position inside sel
    lamp_of_bone = defaultdict(list)
    for lamp in LAMPS:
        for b in lamp["bones"]:
            lamp_of_bone[b].append(lamp)
    lamps = {lamp["part"]: {"faces": [], "clusters": 0, "bones": Counter()} for lamp in LAMPS}
    errors = []
    for comp in clusters(tris[sel]):
        faces = [int(sel[k]) for k in comp]
        bone = Counter(bones[b][0] for b in fb[faces]).most_common(1)[0][0]
        cands = lamp_of_bone.get(bone) or []
        if not cands:
            errors.append(f"cluster of {len(faces)} faces on {bone}: no lamp owns that bone")
            continue
        c = Vw[wedge[faces].ravel()].mean(0)
        side = "left" if c[0] < 0 else "right"
        same = [l for l in cands if l["side"] == side]
        if len(cands) > 1 and len(same) != 1:
            errors.append(f"{bone} cluster at x={c[0]:+.3f}: {len(same)} of {len(cands)} "
                          f"lamps want that side")
            continue
        lamp = same[0] if same else cands[0]
        if lamp["side"] != side:
            errors.append(f"{bone} cluster at x={c[0]:+.3f} is {side}, lamp {lamp['part']} is "
                          f"{lamp['side']}")
            continue
        part = lamp["part"]
        lamps[part]["faces"].extend(faces)
        lamps[part]["clusters"] += 1
        lamps[part]["bones"][bone] += len(faces)
    total = sum(len(v["faces"]) for v in lamps.values())
    if total != len(sel):
        errors.append(f"{total} faces assigned of {len(sel)} Emissive faces")
    return sel, face_of, lamps, errors


def no_face_lamps(mesh, sel):
    """For each rig lamp with no Emissive faces: the measured gap to the nearest lamp face."""
    socks = {s["socket"]: s for s in load(SOCKETS)["sockets"]}
    pts = mesh["Vw"][mesh["F"]["w"][sel]].reshape(-1, 3)
    out = []
    for row in NO_FACE:
        s = socks.get(row["socket"])
        if s is None:
            out.append({"socket": row["socket"], "why": row["why"], "error": "socket not in SOCKETS_JC3.json"})
            continue
        p = np.array(s["position_m"], dtype=np.float64)
        d = float(np.min(np.linalg.norm(pts - p, axis=1)))
        out.append({"socket": row["socket"], "why": row["why"], "bone": s["bone"],
                    "position_m": [round(float(x), 6) for x in p],
                    "nearest_lamp_face_m": round(d, 4),
                    "claim": ("no Emissive-material (slot 5) face lies within this distance of the "
                              "socket"),
                    "not_claimed": ("absence of lens geometry (other material slots were not "
                                    "examined); whether Headlight_Centre shares the nose lenses "
                                    "is UNKNOWN"),
                    "evidence": "measured nearest-vertex distance to the material-5 faces"})
    return out


# ------------------------------------------------------------------ CarLight block

def template_block():
    m = R.decode(open(os.path.join(ROOT, TEMPLATE), "rb").read())
    blocks = [b for b in m.blocks if R.BLOCK_NAMES.get(b.type_hash) == "CarLight"]
    if len(blocks) != 1:
        raise SystemExit(f"template {TEMPLATE}: {len(blocks)} CarLight blocks, expected 1")
    src = blocks[0]
    if src.strides != (12, 24, 2):
        raise SystemExit(f"template strides {src.strides}, expected (12, 24, 2)")
    pos = np.frombuffer(src.buffers[0].data, "<f4").reshape(-1, 3)
    six = np.frombuffer(src.buffers[1].data, "<f4").reshape(-1, 6)
    return m, src, pos, six


def build_carlight(tpl, tpl_pos, tpl_six, V, UV, I):
    """A CarLight block: template header/mid/textures byte-exact, our positions/UVs/indices.

    The 24 B stream is (u, v, 0, 0, packed, packed). u,v are ours; the packed pair is copied from
    the template vertex nearest to ours, because its meaning is undecoded (LIGHT_SYSTEM §5).
    """
    _, src, _, _ = tpl
    d = np.linalg.norm(V[:, None, :] - tpl_pos[None, :, :], axis=2)
    near = d.argmin(1)
    A = np.zeros((len(V), 6), np.float32)
    A[:, 0:2] = UV
    A[:, 4:6] = tpl_six[near, 4:6]
    ib = np.asarray(I, dtype="<u2").ravel()
    src.buffers = [R.VertexBuffer(12, len(V), np.asarray(V, "<f4").tobytes()),
                   R.VertexBuffer(24, len(V), A.tobytes()),
                   R.VertexBuffer(2, ib.size, ib.tobytes())]
    return src


def verify_light(raw, tpl, V, UV, I):
    """decode the written block: type, header/texture equality with the clone, counts, geometry."""
    _, src, _, _ = tpl
    m = R.decode(raw)
    if len(m.blocks) != 1:
        return f"{len(m.blocks)} blocks, expected 1"
    blk = m.blocks[0]
    if R.BLOCK_NAMES.get(blk.type_hash) != "CarLight":
        return f"block is {R.BLOCK_NAMES.get(blk.type_hash)}"
    if blk.strides != (12, 24, 2):
        return f"strides {blk.strides}"
    if blk.pre_static != src.pre_static:
        return "pre_static differs from the cloned template"
    if blk.mid_static != src.mid_static:
        return "mid_static differs from the cloned template"
    if blk.textures != src.textures:
        return "texture table differs from the cloned template"
    if blk.buffers[0].count != len(V) or blk.buffers[1].count != len(V):
        return "vertex counts"
    if np.asarray(blk.indices(), np.int64).size != np.asarray(I).size:
        return "index count"
    pos = np.frombuffer(blk.buffers[0].data, "<f4").reshape(-1, 3)
    if not np.allclose(pos, V, atol=1e-5):
        return "positions"
    six = np.frombuffer(blk.buffers[1].data, "<f4").reshape(-1, 6)
    if not np.allclose(six[:, 0:2], UV, atol=1e-5):
        return "uv"
    if not np.array_equal(np.asarray(blk.indices(), np.int64), np.asarray(I, np.int64).ravel()):
        return "indices"
    if not np.allclose(m.bbox_min, np.min(pos, 0), atol=1e-5) or \
            not np.allclose(m.bbox_max, np.max(pos, 0), atol=1e-5):
        return "header bbox"
    if m.write() != raw:
        return "re-encode is not byte-identical"
    return None


# ------------------------------------------------------------------ derivation

def vanilla_ladder():
    """The vanilla light-part shape: how many LODs a donor light mesh has, and its tri count per LOD.

    Measured on the donor light meshes in our own tree: the families ship lod1..lod4 (none goes past
    lod4), and a lamp part carries only the levels EVERY family ships (the head-lamp families stop
    at lod3). The per-LOD ceiling is the largest CarLight triangle count among the donor meshes at
    that level. Every number here is measured, and the census is returned so the manifest can state
    it instead of a sentence that guesses.
    """
    caps, sources, levels = [], [], {}
    for i in range(1, MAX_LODS + 1):
        best, best_f = 0, None
        for f in sorted(glob.glob(os.path.join(ROOT, DONOR_GLOB.format(i=i)))):
            try:
                m = R.decode(open(f, "rb").read())
            except R.RbmError:
                continue
            for b in m.blocks:
                if R.BLOCK_NAMES.get(b.type_hash) == "CarLight" and b.index_count // 3 > best:
                    best, best_f = b.index_count // 3, f
            if any(R.BLOCK_NAMES.get(b.type_hash) == "CarLight" for b in m.blocks):
                family = os.path.basename(f).rsplit("_lod", 1)[0]
                levels.setdefault(family, set()).add(i)
        if not best:
            break                       # no donor light mesh at this LOD -> lamps stop here
        caps.append(best)
        sources.append(rel(best_f))
    fam_levels = {k: len(v) for k, v in levels.items()}
    keep = min(fam_levels.values()) if fam_levels else len(caps)
    stats = {"families": len(fam_levels),
             "family_lods": {str(k): v for k, v in
                             sorted(Counter(fam_levels.values()).items())},
             "min_lods": keep,
             "max_lods": max(fam_levels.values()) if fam_levels else 0,
             "kept": keep, "ceiling_sources": sources[:keep]}
    return caps[:keep], sources[:keep], stats


def derive(remesh=True):
    """Every output byte + the manifest, from the files alone. No disk writes."""
    mesh = load_mesh()
    ladder, ladder_sources, ladder_stats = vanilla_ladder()
    lods = len(ladder)
    sel, _, lamps, errors = assign(mesh)
    if errors:
        raise SystemExit("BM-03 lamp assignment failed: " + "; ".join(errors))
    tpl = template_block()
    tpl_m, tpl_src, tpl_pos, tpl_six = tpl
    Vw, UVw = mesh["Vw"], mesh["UVw"]
    frames = parent_frames()
    new_idx = new_part_indices()
    files, entries, checks = {}, [], {}
    all_faces = []
    pivot_ok, pivot_checked = [], 0
    for lamp in LAMPS:
        faces = sorted(lamps[lamp["part"]]["faces"])
        if not faces:
            raise SystemExit(f"{lamp['part']}: owns no Emissive faces")
        frame = frames.get(lamp["parent"])
        if frame is None:
            raise SystemExit(f"{lamp['part']}: parent index {lamp['parent']} does not join "
                             f"{PARTS_TABLE} to {PARTS_MANIFEST}")
        donor_name, part_name, pentry = frame
        pivot = np.array(pentry["pivot_m"], dtype=np.float64)
        all_faces.extend(faces)
        tris = mesh["F"]["w"][faces]                       # wedge indices of those faces
        # LOD budgets: the vanilla light-part ladder (the max triangles each LOD of the donor light
        # meshes carries, measured) times the AUTHORING lamp_elements of this part, capped by the
        # faces the lamp actually has, so the multiplier can never invent geometry.
        budgets = [max(4, min(len(faces), cap * lamp["lamp_elements"])) for cap in ladder[:lods]]
        # B-02 emits part RBMs relative to their pivot, and B-04 sets parent_space_offset = pivot:
        # express this lamp in its parent part's frame here, not in body space.
        V = Vw - pivot
        decimated = BA.decimated_lods(V, UVw, tris, budgets) if remesh else None
        lod_names, faces_per, verts_per, bytes_per = [], [], [], []
        bbox_of, bbox_abs = [], []
        for i, budget in enumerate(budgets, 1):
            name = f"{lamp['part']}_lod{i}.rbm"
            if remesh:
                v, uv, I, _N = decimated[i - 1]
            else:
                raw = open(os.path.join(ROOT, OUT, name), "rb").read()
                m = R.decode(raw)
                v = np.frombuffer(m.blocks[0].buffers[0].data, "<f4").reshape(-1, 3)
                uv = np.frombuffer(m.blocks[0].buffers[1].data, "<f4").reshape(-1, 6)[:, 0:2]
                I = np.asarray(m.blocks[0].indices(), np.int64).reshape(-1, 3)
            blk = build_carlight(tpl, tpl_pos, tpl_six, v, uv, I)
            out = R.Rbm(tpl_m.magic_length, tpl_m.magic, tpl_m.version,
                        tuple(float(x) for x in v.min(0)), tuple(float(x) for x in v.max(0)),
                        1, tpl_m.tag, [blk]).write()
            err = verify_light(out, tpl, v, uv, I)
            if err:
                raise SystemExit(f"{name}: VERIFY FAILED: {err}")
            files[name] = out
            lod_names.append(name)
            faces_per.append(int(len(I)))
            verts_per.append(int(len(v)))
            bytes_per.append(len(out))
            bbox_of.append([np.round(v.min(0), 4).tolist(), np.round(v.max(0), 4).tolist()])
            bbox_abs.append([[round(float(x), 4) for x in v.min(0) + pivot],
                             [round(float(x), 4) for x in v.max(0) + pivot]])
        src_lo = np.round(Vw[mesh["F"]["w"][faces]].reshape(-1, 3).min(0), 4)
        src_hi = np.round(Vw[mesh["F"]["w"][faces]].reshape(-1, 3).max(0), 4)
        if budgets[0] >= len(faces):            # LOD1 kept every source face: the pivot must not move it
            pivot_checked += 1
            pivot_ok.append(np.allclose(np.array(bbox_abs[0][0]), src_lo, atol=1e-4) and
                            np.allclose(np.array(bbox_abs[0][1]), src_hi, atol=1e-4))
        socks = socket_rows(lamp["sockets"])
        pts = Vw[mesh["F"]["w"][faces]].reshape(-1, 3)
        for s in socks:
            if s.get("position_m"):
                s["nearest_lamp_face_m"] = round(float(np.min(np.linalg.norm(
                    pts - np.array(s["position_m"], dtype=np.float64), axis=1))), 4)
        entries.append({
            "part": lamp["part"],
            "kind": lamp["kind"],
            "side": lamp["side"],
            "parent": lamp["parent"],
            "parent_part": part_name,
            "parent_part_source": (f"{PARTS_TABLE} parts[].i -> n, then "
                                   f"{PARTS_MANIFEST} entries[].pivot_m"),
            "pivot_m": [round(float(x), 6) for x in pivot],
            "frame": "parent part frame: vertices are relative to pivot_m (B-02 convention)",
            "part_index": new_idx.get(lamp["part"]),
            "part_index_source": ("t14_lights.json light_parts[].part_index (new_part match)"
                                  if lamp["part"] in new_idx else
                                  "none assigned in t14_lights.json; B-04 assigns the next free"),
            "lamp_elements": lamp["lamp_elements"],
            "lamp_elements_source": ("AUTHORING parameter (no decoded lens count); the budget it "
                                     "multiplies is capped by faces_lod0"),
            "bones": sorted(lamps[lamp["part"]]["bones"].items(),
                            key=lambda kv: -kv[1]),
            "clusters": lamps[lamp["part"]]["clusters"],
            "faces_lod0": len(faces),
            "face_indices": faces,
            "lod_files": lod_names,
            "lod_budgets": budgets,
            "faces_per_lod": faces_per,
            "vertices_per_lod": verts_per,
            "bytes_per_lod": bytes_per,
            "bbox_m": bbox_of,
            "bbox_body_m": bbox_abs,
            "block": "CarLight",
            "window_block": None,
            "window_reason": ("no Window block is authored for this lamp: the BmAK material gives "
                              "one emissive surface and B-03 adds no second shell. Whether the "
                              "game needs the pair is UNKNOWN (phase Q); the donor census is in "
                              "manifest.window"),
            "sockets": socks,
            "t18_rows": t18_rows(lamp["sockets"]),
        })
    slots_faces = next(s for s in load(SLOTS)["slots"] if s["index"] == EMISSIVE_SLOT)["lod0_faces"]
    checks[f"faces_total_{slots_faces}"] = len(sel) == slots_faces
    checks["lod_budget_within_vanilla_ladder"] = all(
        e["faces_per_lod"][i] <= ladder[i]
        * next(l["lamp_elements"] for l in LAMPS if l["part"] == e["part"])
        for e in entries for i in range(lods))
    checks["every_face_once"] = sorted(all_faces) == sorted(int(x) for x in sel)
    checks["lamp_faces_sum_equals_cut"] = (sum(e["faces_lod0"] for e in entries)
                                           == len(all_faces) == len(sel))
    checks[f"lods_each_{lods}"] = all(len(e["lod_files"]) == lods for e in entries)
    checks["lod_files_unique"] = len(files) == lods * len(LAMPS)
    checks["carllight_header_from_template"] = all(
        R.decode(b).blocks[0].pre_static == tpl_src.pre_static
        and R.decode(b).blocks[0].mid_static == tpl_src.mid_static
        and R.decode(b).blocks[0].textures == tpl_src.textures for b in files.values())
    checks["roundtrip_byte_identical"] = all(
        R.decode(b).write() == b for b in files.values())
    checks["pivot_applied_exactly"] = bool(pivot_ok) and all(pivot_ok)
    side = []
    for e in entries:
        want = -1 if e["side"] == "left" else 1
        for s in e["sockets"]:
            p = s.get("position_m")
            if p:
                side.append(bool(np.sign(p[0]) == want and abs(p[0]) > 1e-6))
    checks["socket_side_matches_lamp"] = bool(side) and all(side)
    t18_doc = load(T18)["rows"]
    t18_ids = {r["id"] for r in t18_doc}
    checks["t18_rows_exist"] = all(r["row"] in t18_ids
                                  for e in entries for r in e["t18_rows"])
    checks["t18_sockets_exist_in_jc3"] = all(
        "error" not in s for e in entries for s in e["sockets"])
    manifest = build_manifest(mesh, lamps, entries, checks, files, ladder, ladder_sources, lods,
                              ladder_stats, pivot_checked)
    return manifest, files


def socket_rows(names):
    """Each socket plus EVERY T-18 row that names it, with that row's own colour.

    The old version kept the first LightColor found per socket, which silently dropped the second
    and third colours T-18 puts on the same socket (HeadLight1 carries T-L8's blue, T-L11's
    [223,91,75] and T-L18's battle red). B-05/B-07 need all of them, so none is collapsed here.
    """
    socks = {s["socket"]: s for s in load(SOCKETS)["sockets"]}
    rows = load(T18)["rows"]
    out = []
    for n in names:
        s = socks.get(n)
        if s is None:
            out.append({"socket": n, "error": "missing from SOCKETS_JC3.json"})
            continue
        colours = [{"row": r["id"],
                    "colour_rgba": (r.get("bmak") or {}).get("colour"),
                    "mapped": bool(r.get("targets")),
                    "components": (r.get("bmak") or {}).get("components"),
                    "bmak_type": r.get("bmak_type")}
                   for r in rows if r.get("socket") == n]
        out.append({"socket": n, "bone": s["bone"], "position_m": s["position_m"],
                    "forward_jc3": s["forward_jc3"], "role": s["role"],
                    "t18_rows_on_socket": [c["row"] for c in colours],
                    "t18_colours": colours,
                    "primary_light_colour_rgba": next(
                        (c["colour_rgba"] for c in colours if c["colour_rgba"]), None),
                    "colour_source": "t14_lights.json rows[].bmak.colour (LIGHTS.json LightColor)"})
    return out


def t18_rows(names):
    doc = load(T18)
    out = []
    for row in doc["rows"]:
        if row.get("socket") in names:
            out.append({"row": row["id"], "socket": row["socket"], "group": row.get("group"),
                        "mapped": bool(row.get("targets")),
                        "bmak_type": row.get("bmak_type")})
    return out


def build_manifest(mesh, lamps, entries, checks, files, ladder, ladder_sources, lods,
                   ladder_stats, pivot_checked):
    tpl_m, tpl_src, _, _ = template_block()
    slots = load(SLOTS)
    emissive = next(s for s in slots["slots"] if s["index"] == EMISSIVE_SLOT)
    b02 = load(PARTS_MANIFEST)["budget"]
    lights_kb = sum(len(b) for b in files.values()) / 1024.0
    # marginal CarPaintMM bytes of the same faces at the same budgets: 24 B/vertex + 2 B/index
    # (a removed block's own header is not counted -- the body is re-emitted as a whole in B-04/B-05)
    paint_bytes = sum(e["vertices_per_lod"][i] * 24 + e["faces_per_lod"][i] * 3 * 2
                      for e in entries for i in range(lods))
    net_kb = b02["model_kb"] + (sum(len(b) for b in files.values()) - paint_bytes) / 1024.0
    checks["net_model_budget_green"] = net_kb <= BUDGET_KB
    checks["sum_equals_parts"] = (sum(len(b) for b in files.values())
                                  == sum(e["bytes_per_lod"][i]
                                         for e in entries for i in range(lods)))
    no_face = no_face_lamps(mesh, [f for e in entries for f in e["face_indices"]])
    checks["no_face_lamps_measured"] = (len(no_face) == len(NO_FACE)
                                        and all(r.get("nearest_lamp_face_m", 0) > 0
                                                for r in no_face))
    hosted_sockets = {s["socket"] for e in entries for s in e["sockets"]}
    checks["no_face_lamps_not_hosted"] = all(r["socket"] not in hosted_sockets for r in no_face)
    faces = [f for e in entries for f in e["face_indices"]]
    return {
        "schema": 1,
        "card": "B-03",
        "generator": "bm_lights.py --write",
        "source": rel(PSKX),
        "source_sha256": sha(open(os.path.join(ROOT, mesh["path"]), "rb").read()),
        "transform": {"scale": mesh["scale"],
                      "offset": [round(float(x), 9) for x in mesh["offset"]],
                      "mapping": "rotation", "fn": "bat_assemble.to_jc3_rot * scale + offset",
                      "frame": ("parent part frame: the transform above minus the lamp's pivot_m "
                                "(B-02 emits part RBMs pivot-relative; B-04 sets "
                                "parent_space_offset = pivot_m)")},
        "block_values": {"t18_values_in_block": 0, "status": "UNKNOWN",
                         "why": ("the CarLight material parameters are undecoded (MODLOG §102d), so "
                                 "the header/mid-static/texture table are cloned byte-exact from "
                                 "the template and no T-18 number is written into the block; the "
                                 "card's Do step 'write the CarLight block with values from T-18' "
                                 "is therefore NOT met and stays UNKNOWN rather than guessed")},
        "window": {"written": False, "census": window_census(),
                   "status": "UNKNOWN whether the game needs the pair (runtime, phase Q)",
                   "why": ("no Window block is authored: the BmAK material gives one emissive "
                           "surface and B-03 adds no second shell; the donor census above shows "
                           "which vanilla light families do ship the pair (the head lamps all do, "
                           "the centre tail lamp never does)")},
        "material": {"index": EMISSIVE_SLOT, "name": emissive["material"],
                     "faces_lod0": emissive["lod0_faces"],
                     "source": SLOTS},
        "template": {"file": rel(TEMPLATE), "block": "CarLight",
                     "pre_static_bytes": len(tpl_src.pre_static),
                     "pre_static_sha256": sha(tpl_src.pre_static),
                     "mid_static_sha256": sha(tpl_src.mid_static),
                     "textures": tpl_src.textures, "strides": list(tpl_src.strides),
                     "sha256": sha(open(os.path.join(ROOT, TEMPLATE), "rb").read()),
                     "why": ("header/mid/texture table copied byte-exact; the material "
                             "parameters are undecoded (LIGHT_SYSTEM §5, MODLOG §102d)")},
        "lod_ladder": {"lods": lods, "triangles_per_lens": ladder, "sources": ladder_sources,
                       "census": ladder_stats,
                       "what": ("the fewest LODs any donor light family ships (the donor families "
                                "ship lod1..lod{max}; only the levels every family shares are kept, "
                                "so LOD1..LOD{lods}), ceiling = the largest CarLight triangle count "
                                "at that level over the {families} donor light families; a part's "
                                "budget is that ceiling x its AUTHORING lamp_elements, capped by "
                                "the faces the lamp has").replace("{lods}", str(lods))
                               .replace("{max}", str(ladder_stats["max_lods"]))
                               .replace("{families}", str(ladder_stats["families"]))},
        "lamps": entries,
        "lamps_without_faces": no_face,
        "t18_hosting": t18_hosting(entries),
        "pivot_check": {"lamps_checked": pivot_checked,
                        "why": ("pivot_applied_exactly compares LOD1's absolute bbox (vertices + "
                                "pivot) with the source faces' bbox for the lamps whose LOD1 kept "
                                "every face; a lamp whose LOD1 is decimated is not counted")},
        "cut": {"faces": len(faces),
                "face_indices_sha256": sha((",".join(str(x) for x in faces)).encode()),
                "what": ("the LOD0 PSKX face indices that move out of the body/wheel parts; "
                         "B-04/B-05 re-emit those parts without them")},
        "budget": {"lights_kb": round(lights_kb, 1),
                   "b02_model_kb": b02["model_kb"], "cap_kb": BUDGET_KB,
                   "sum_kb": round(b02["model_kb"] + lights_kb, 1),
                   "paint_equivalent_bytes": int(paint_bytes),
                   "net_kb": round(net_kb, 1),
                   "note": ("net = B-02 + lights - the marginal CarPaintMM bytes (24 B/vertex, "
                            "2 B/index) of the same faces at the same LOD budgets; the sum is "
                            "reported as well (R9)")},
        "checks": checks,
    }


def write_all(manifest, files, out):
    os.makedirs(os.path.join(ROOT, out), exist_ok=True)
    for name, raw in files.items():
        open(os.path.join(ROOT, out, name), "wb").write(raw)
    path = os.path.join(ROOT, out, "lights_manifest.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")
    return path


def compare(manifest, files, out):
    bad = []
    for name, raw in files.items():
        p = os.path.join(ROOT, out, name)
        if not os.path.exists(p):
            bad.append(f"{name}: missing")
        elif open(p, "rb").read() != raw:
            bad.append(f"{name}: differs from the re-derived bytes")
    p = os.path.join(ROOT, out, "lights_manifest.json")
    if not os.path.exists(p):
        bad.append("lights_manifest.json: missing")
    else:
        on_disk = json.load(open(p, encoding="utf-8"))
        if on_disk != json.loads(json.dumps(manifest)):
            diff = [k for k in manifest if on_disk.get(k) != json.loads(json.dumps(manifest))[k]]
            bad.append(f"lights_manifest.json: differs in {diff}")
    return bad


def summary(manifest):
    m = manifest
    t18 = [r for e in m["lamps"] for r in e["t18_rows"]]
    sockets = [s for e in m["lamps"] for s in e["sockets"]]
    coloured = sum(1 for s in sockets if s.get("primary_light_colour_rgba"))
    mapped = sum(1 for r in t18 if r["mapped"])
    return (f"{len(m['lamps'])} lamp parts / {sum(len(e['lod_files']) for e in m['lamps'])} RBMs, "
            f"{m['cut']['faces']} Emissive faces cut, "
            f"{len(sockets)} lamp sockets ({coloured} with a T-18 LightColor), "
            f"{len(t18)} T-18 rows ({mapped} mapped, {len(t18) - mapped} unmapped), "
            f"{len(m['lamps_without_faces'])} rig lamps with no faces; pivot-relative per parent "
            f"part ({m['pivot_check']['lamps_checked']} lamps bbox-checked); "
            f"model {m['budget']['lights_kb']:.1f} KB lights, sum {m['budget']['sum_kb']:.1f} KB, "
            f"net {m['budget']['net_kb']:.1f} KB of {m['budget']['cap_kb']:.0f} KB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--fast", action="store_true",
                    help="--check only: decode the files on disk instead of re-decimating")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    remesh = not a.fast
    manifest, files = derive(remesh=remesh)
    fails = [k for k, v in manifest["checks"].items() if not v]
    if a.write:
        path = write_all(manifest, files, a.out)
        print(f"BM-03 written: {summary(manifest)}")
        print(f"  -> {rel(path)}")
        for k, v in manifest["checks"].items():
            print(f"  {k:<34} {'PASS' if v else 'FAIL'}")
        if fails:
            raise SystemExit("BM-03 manifest checks failed: " + ", ".join(fails))
        return 0
    bad = compare(manifest, files, a.out) if remesh else decode_only(a.out, manifest)
    for line in bad[:20]:
        print("  FAIL", line)
    print(f"{'PASS' if not bad and not fails else 'FAIL'}: {summary(manifest)}"
          + ("" if remesh else " (fast: files decoded, not re-decimated)"))
    return 1 if bad or fails else 0


def decode_only(out, manifest):
    """--fast: the manifest is trusted for derivation, the RBMs are decoded and compared."""
    bad = []
    tpl = [b for b in R.decode(open(os.path.join(ROOT, TEMPLATE), "rb").read()).blocks
           if R.BLOCK_NAMES.get(b.type_hash) == "CarLight"][0]
    for e in manifest["lamps"]:
        for i, name in enumerate(e["lod_files"]):
            p = os.path.join(ROOT, out, name)
            if not os.path.exists(p):
                bad.append(f"{name}: missing")
                continue
            raw = open(p, "rb").read()
            m = R.decode(raw)
            blk = m.blocks[0]
            if R.BLOCK_NAMES.get(blk.type_hash) != "CarLight":
                bad.append(f"{name}: block {R.BLOCK_NAMES.get(blk.type_hash)}")
                continue
            if blk.strides != (12, 24, 2):
                bad.append(f"{name}: strides {blk.strides}")
            if blk.pre_static != tpl.pre_static or blk.mid_static != tpl.mid_static:
                bad.append(f"{name}: cloned header differs from {rel(TEMPLATE)}")
            if blk.textures != tpl.textures:
                bad.append(f"{name}: texture table differs from the template")
            if blk.vb0.count != e["vertices_per_lod"][i] or blk.index_count != e["faces_per_lod"][i] * 3:
                bad.append(f"{name}: counts differ from the manifest")
            if len(raw) != e["bytes_per_lod"][i]:
                bad.append(f"{name}: {len(raw)} B vs manifest {e['bytes_per_lod'][i]} B")
            pos = np.frombuffer(blk.buffers[0].data, "<f4").reshape(-1, 3)
            if not np.allclose(m.bbox_min, pos.min(0), atol=1e-5) or \
                    not np.allclose(m.bbox_max, pos.max(0), atol=1e-5):
                bad.append(f"{name}: file header bbox != geometry")
            if m.write() != raw:
                bad.append(f"{name}: re-encode is not byte-identical")
    return bad


if __name__ == "__main__":
    sys.exit(main())
