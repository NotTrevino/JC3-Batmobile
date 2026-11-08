"""grab_bones.py - Batmobile_V2 skeleton, bind pivots and face-to-bone ownership (G1-11).

The cooked mesh has three LODs, but the normal `umodel` export has only LOD0 because UEViewer's
settings file forces `ExportMeshLods=false` even when `-lods` is on the command line.  This tool
expects the two extra exports beside LOD0:

    Batmobile_V2.pskx       LOD0
    Batmobile_V2_Lod1.pskx  LOD1
    Batmobile_V2_Lod2.psk   LOD2

`BONES.md` records the isolated-config command used to make those two files; the user's
`umodel.cfg` is not edited.

What is measured
----------------
* Every `REFSKELT` record: name, parent, local bind position/rotation.  The PSK quaternion
  convention is left-handed: the world rotation is `q_child * q_parent`, and a child's local
  position is rotated by the **inverse** of the parent's rotation.  That combination reproduces
  umodel's glTF inverse-bind pivots for all 180 bones (max error 0.03 cm); the check is recorded
  when the glTF export is present, but the pivots themselves come from the PSK/`bat_assemble`.
* The one assembly transform: `bat_assemble.to_jc3_rot(p) * 0.01 + offset`.  The offset is
  recomputed from the same wheel-hub block as `bat_assemble.main` and must agree with
  `Working/TrueScale/stations.json`; that file is the transform the assembled meshes were built
  with, so its offset is used for the final pivots.
* Every face at every LOD: all three points must have the same unique `>= 0.5` influence for the
  face to be **owned** by that bone.  Otherwise the face is **split** and is never assigned to a
  bone.  This is the cut list B-02 needs.
* Per-bone owned faces per global material slot, per LOD; split faces per slot and the split
  faces touching each bone.  Face indices are written outside the repository:
  `E:\\Modding\\_gamedata\\BmAKgrab\\bones\\<bone>.npy` as int32 rows `(lod, face, slot, kind)`, kind
  0 = owned, 1 = split-touching.  A split face can appear in more than one bone file; the
  `_split.npy` file lists every split face once.

Outputs:
  Research/BatmobileGrab/BONES.json
  Research/BatmobileGrab/BONES.md
  E:\\Modding\\_gamedata\\BmAKgrab\\bones\\*.npy

Usage:
  python Tools/scripts/grab_bones.py --write
  python Tools/scripts/grab_bones.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bat_assemble as BA  # noqa: E402
import grab_meshes as G  # noqa: E402
import pskx_parts as PX  # noqa: E402
import upk_read as U  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GRAB = ROOT / "Research" / "BatmobileGrab"
OUT_JSON = GRAB / "BONES.json"
OUT_MD = GRAB / "BONES.md"
STATIONS = ROOT / "Working" / "TrueScale" / "stations.json"
MESHES_JSON = GRAB / "MESHES.json"
SLOTS_JSON = GRAB / "SLOTS.json"

PACKAGE = "Playable_Batmobile_SF"
MESH = "Batmobile_V2"
GAME = Path(os.environ.get(
    "BMAK_GAME_DIR", r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"))
MESH_ROOT = Path(os.environ.get("BMAK_MESH_DIR", r"E:\Modding\_gamedata\BmAKgrab\meshes"))
BONE_ROOT = Path(os.environ.get("BMAK_BONE_DIR", r"E:\Modding\_gamedata\BmAKgrab\bones"))
MESH_DIR = MESH_ROOT / PACKAGE / PACKAGE / "SkeletalMesh3"
LOD_FILES = (
    ("Batmobile_V2.pskx", 0),
    ("Batmobile_V2_Lod1.pskx", 1),
    ("Batmobile_V2_Lod2.psk", 2),
)

SCALE = 0.01
GROUND = 0.02
CENTER_Z = -0.0555
WHEELS = 4
MOVE_WEIGHT = 0.5
NSLOT = 19


class BoneError(Exception):
    pass


# ---------------------------------------------------------------------------------------------
# ActorX chunks


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def chunks(path: Path):
    """Return (bytes, {chunk_id: (data_offset, stride, count)})."""
    data = path.read_bytes()
    o = 0
    ch: dict[str, tuple[int, int, int]] = {}
    while o + 32 <= len(data):
        cid = data[o:o + 20].split(b"\0")[0].decode("latin-1")
        stride, count = struct.unpack_from("<II", data, o + 24)
        ch[cid] = (o + 32, stride, count)
        nxt = o + 32 + stride * count
        if nxt <= o or nxt > len(data):
            raise BoneError("%s: bad chunk %r at %#x" % (path.name, cid, o))
        o = nxt
    if o != len(data):
        raise BoneError("%s: %d trailing bytes after chunks" % (path.name, len(data) - o))
    return data, ch


def read_mesh(path: Path) -> dict:
    """Read PNTS/VTXW/FACE/MATT from a chunked PSK or PSKX (both LOD0 and LOD2)."""
    data, ch = chunks(path)
    need = ("PNTS0000", "VTXW0000", "MATT0000")
    for key in need:
        if key not in ch:
            raise BoneError("%s: missing %s" % (path.name, key))
    po, ps, pn = ch["PNTS0000"]
    if ps != 12:
        raise BoneError("%s: PNTS stride %d" % (path.name, ps))
    P = np.frombuffer(data, "<f4", pn * 3, po).reshape(pn, 3).astype(np.float64)

    wo, ws, wn = ch["VTXW0000"]
    if ws != 16:
        raise BoneError("%s: VTXW stride %d" % (path.name, ws))
    W = np.frombuffer(data, np.dtype([
        ("p", "<u4"), ("u", "<f4"), ("v", "<f4"), ("m", "u1"), ("r", "u1"),
        ("pad", "<u2")]), wn, wo)

    if "FACE3200" in ch:
        fo, fs, fn = ch["FACE3200"]
        if fs != 18:
            raise BoneError("%s: FACE3200 stride %d" % (path.name, fs))
        F = np.frombuffer(data, np.dtype([
            ("w", "<u4", 3), ("m", "u1"), ("a", "u1"), ("s", "<u4")]), fn, fo)
        face_format = "FACE3200"
    elif "FACE0000" in ch:
        fo, fs, fn = ch["FACE0000"]
        if fs != 12:
            raise BoneError("%s: FACE0000 stride %d" % (path.name, fs))
        F = np.frombuffer(data, np.dtype([
            ("w", "<u2", 3), ("m", "u1"), ("a", "u1"), ("s", "<u4")]), fn, fo)
        face_format = "FACE0000"
    else:
        raise BoneError("%s: no FACE chunk" % path.name)

    mo, ms, mn = ch["MATT0000"]
    if ms != 88:
        raise BoneError("%s: MATT stride %d" % (path.name, ms))
    mats = [data[mo + i * ms:mo + i * ms + 64].split(b"\0")[0].decode("latin-1")
            for i in range(mn)]
    if len(P) == 0 or len(W) == 0 or len(F) == 0:
        raise BoneError("%s: empty mesh" % path.name)
    if int(W["p"].max()) >= len(P) or int(F["w"].max()) >= len(W):
        raise BoneError("%s: index outside PNTS/VTXW" % path.name)
    if int(F["m"].max()) >= len(mats):
        raise BoneError("%s: face section %d outside MATT (%d)" %
                        (path.name, int(F["m"].max()), len(mats)))
    return {"P": P, "W": W, "F": F, "mats": mats, "chunks": ch,
            "data": data, "face_format": face_format, "bytes": len(data)}


def read_skeleton(path: Path) -> dict:
    """Read REFSKELT as names, parents, local bind position and quaternion."""
    data, ch = chunks(path)
    if "REFSKELT" not in ch:
        raise BoneError("%s: no REFSKELT" % path.name)
    o, s, n = ch["REFSKELT"]
    if s != 120:
        raise BoneError("%s: REFSKELT stride %d, expected 120" % (path.name, s))
    bones = []
    for i in range(n):
        r = data[o + i * s:o + (i + 1) * s]
        name = r[:64].split(b"\0")[0].decode("latin-1")
        flags, children, parent = struct.unpack_from("<III", r, 64)
        q = np.array(struct.unpack_from("<4f", r, 76), dtype=np.float64)
        pos = np.array(struct.unpack_from("<3f", r, 92), dtype=np.float64)
        length = struct.unpack_from("<f", r, 104)[0]
        if not name:
            raise BoneError("%s: empty bone name at %d" % (path.name, i))
        if not 0 <= parent < n:
            raise BoneError("%s: bone %d parent %d outside table" % (path.name, i, parent))
        if not np.isfinite(pos).all() or not np.isfinite(q).all():
            raise BoneError("%s: non-finite bind pose at %d" % (path.name, i))
        qn = float(np.linalg.norm(q))
        if qn == 0:
            q = np.array([0.0, 0.0, 0.0, 1.0])
        else:
            q = q / qn
        bones.append({"index": i, "name": name, "flags": flags,
                      "children": children, "parent": parent,
                      "q": q, "pos": pos, "length": length})
    names = [b["name"] for b in bones]
    dups = [n for n, c in Counter(names).items() if c > 1]
    if dups:
        raise BoneError("%s: duplicate bone names: %s" % (path.name, dups[:5]))
    return {"bones": bones, "names": names, "count": n}


def qmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ])


def qrot(q: np.ndarray, v: np.ndarray, inverse: bool = False) -> np.ndarray:
    q = q / np.linalg.norm(q)
    u = q[:3].copy()
    w = q[3]
    if inverse:
        u = -u
    return 2.0 * np.dot(u, v) * u + (w * w - np.dot(u, u)) * v + 2.0 * w * np.cross(u, v)


def world_bones(sk: dict) -> list[dict]:
    """Bind-pose world pivots in PSK centimetres.

    UE3 PSK stores left-handed quaternions: world = q_child * q_parent, and the parent's
    inverse rotation maps the child's local offset into the parent's frame.  This is the
    convention that matches umodel's glTF inverse-bind matrices, not the usual right-handed
    `q_parent * q_child` order.
    """
    bones = sk["bones"]
    state = [0] * len(bones)
    out: list[dict | None] = [None] * len(bones)

    def visit(i: int) -> dict:
        if state[i] == 2:
            return out[i]  # type: ignore[return-value]
        if state[i] == 1:
            raise BoneError("skeleton cycle at bone %d (%s)" % (i, bones[i]["name"]))
        state[i] = 1
        b = bones[i]
        if b["parent"] == i:
            wq, wp = b["q"], b["pos"].copy()
        else:
            p = visit(b["parent"])
            wq = qmul(b["q"], p["world_q"])
            wp = p["world_pos"] + qrot(p["world_q"], b["pos"], inverse=True)
        out[i] = {"world_q": wq / np.linalg.norm(wq), "world_pos": wp}
        state[i] = 2
        return out[i]  # type: ignore[return-value]

    for i in range(len(bones)):
        visit(i)
    for i, b in enumerate(bones):
        if b["parent"] > i:
            raise BoneError("bone %d (%s) has parent %d after it" %
                            (i, b["name"], b["parent"]))
    return [o for o in out if o is not None]  # type: ignore[list-item]


# ---------------------------------------------------------------------------------------------
# the one transform


def compute_frame(path: Path) -> dict:
    """Recompute bat_assemble's wheel hubs and offset from the same LOD0 geometry."""
    mesh = read_mesh(path)
    sk = read_skeleton(path)
    P, W, F = mesh["P"], mesh["W"], mesh["F"]
    bones, Wt = PX.skeleton(str(path))
    if [b["name"] for b in sk["bones"]] != [b[0] for b in bones]:
        raise BoneError("PSKX REFSKELT and pskx_parts bone lists disagree")
    fb = PX.face_bones(P, W, F, Wt, len(bones))
    Vw = BA.to_jc3_rot(P[W["p"]]) * SCALE
    tris = F["w"].astype(np.int64)
    cl = PX.classify(Vw, tris, fb, len(bones))
    round_b = [b for b, (kind, _n, _info) in cl.items() if kind == "spinning"]

    def size(b: int) -> float:
        return max(cl[b][2][3], cl[b][2][4])

    anchors = sorted(round_b, key=size, reverse=True)[:WHEELS]
    if len(anchors) != WHEELS:
        raise BoneError("found %d round wheel anchors, expected %d"
                        % (len(anchors), WHEELS))
    zc0 = np.median([cl[b][2][0][2] for b in anchors])
    corner = {b: ("f" if cl[b][2][0][2] < zc0 else "r") + "_" +
              ("l" if cl[b][2][0][0] < 0 else "r") for b in anchors}
    if sorted(corner.values()) != sorted(BA.CORNERS):
        raise BoneError("wheel anchors do not cover the four corners: %s" % corner)
    wheel_of = dict(corner)
    for b in round_b:
        if b in wheel_of:
            continue
        c = cl[b][2][0]
        for ab in anchors:
            ac, radius = cl[ab][2][0], size(ab) / 2
            if (np.sign(c[0]) == np.sign(ac[0]) and
                    np.linalg.norm(c[1:] - ac[1:]) < radius and
                    size(b) <= 2 * radius):
                wheel_of[b] = corner[ab]

    hubs = {}
    for c in BA.CORNERS:
        bs = [b for b, cc in wheel_of.items()
              if cc == c and size(b) >= 0.8 * max(size(x) for x in anchors)]
        if not bs:
            raise BoneError("no tyre candidate for corner %s" % c)
        tb = min(bs, key=lambda b: cl[b][2][2])
        pts = Vw[np.unique(tris[fb == tb])]
        lo, hi = pts.min(0), pts.max(0)
        hubs[c] = {"centre": (lo + hi) / 2,
                   "radius": float((hi[1] - lo[1]) / 2),
                   "width": float(hi[0] - lo[0]),
                   "bone": bones[tb][0]}
    xc = float(np.mean([hubs[c]["centre"][0] for c in BA.CORNERS]))
    ground = float(min(hubs[c]["centre"][1] - hubs[c]["radius"] for c in BA.CORNERS))
    zc = float((np.mean([hubs[c]["centre"][2] for c in ("f_l", "f_r")]) +
                np.mean([hubs[c]["centre"][2] for c in ("r_l", "r_r")])) / 2)
    offset = np.array([-xc, GROUND - ground, CENTER_Z - zc], dtype=np.float64)
    return {"offset_computed": offset, "hubs": hubs, "cl": cl, "fb": fb,
            "tris": tris, "Vw": Vw, "mesh": mesh, "sk": sk}


def load_stations() -> dict | None:
    if not STATIONS.exists():
        return None
    return json.loads(STATIONS.read_text(encoding="utf-8"))


def transform_check(frame: dict, stations: dict | None) -> dict:
    computed = frame["offset_computed"]
    if not stations:
        return {"offset_used": computed, "offset_computed": computed,
                "stations": None, "offset_delta_m": None,
                "hub_delta_m": None, "hubs": {}}
    if abs(float(stations.get("scale", SCALE)) - SCALE) > 1e-9:
        raise BoneError("stations.json scale %.6f, expected %.6f"
                        % (float(stations.get("scale", SCALE)), SCALE))
    if abs(float(stations.get("ground", GROUND)) - GROUND) > 1e-9:
        raise BoneError("stations.json ground %.6f, expected %.6f"
                        % (float(stations.get("ground", GROUND)), GROUND))
    used = np.array(stations["offset"], dtype=np.float64)
    delta = float(np.linalg.norm(computed - used))
    hubs = {}
    for c in BA.CORNERS:
        hub = frame["hubs"][c]["centre"] + used
        station_hub = np.array(stations["corners"][c]["hub_true"], dtype=np.float64)
        hubs[c] = {"computed": hub, "station": station_hub,
                   "delta_m": float(np.linalg.norm(hub - station_hub)),
                   "tyre_bone": frame["hubs"][c]["bone"]}
    hub_delta = max(h["delta_m"] for h in hubs.values())
    if delta > 5e-5:
        raise BoneError("stations.json offset differs from the recomputed bat_assemble offset "
                        "by %.9f m" % delta)
    if hub_delta > 1e-4:
        raise BoneError("stations.json hub differs from the recomputed bat_assemble hub "
                        "by %.9f m" % hub_delta)
    return {"offset_used": used, "offset_computed": computed,
            "stations": str(STATIONS), "stations_sha256": sha256_file(STATIONS),
            "offset_delta_m": delta,
            "hub_delta_m": hub_delta,
            "hubs": hubs}


# ---------------------------------------------------------------------------------------------
# cooked sections -> material slots


def cooked_sections() -> tuple[list[list[dict]], int, str]:
    """Return the three cooked section lists (LOD order), export index and package hash."""
    pkg_path = GAME / (PACKAGE + ".upk")
    pkg = U.Package(str(pkg_path))
    idx = None
    for i, e in enumerate(pkg.exports, 1):
        if e["name"] == MESH and pkg.class_name(e["class_index"]) == "SkeletalMesh":
            idx = i
            break
    if idx is None:
        raise BoneError("%s: no SkeletalMesh %s" % (pkg_path, MESH))
    data = pkg.data(idx)
    cands = []
    for c in G.section_arrays(data):
        if G._index_count_after(data, c["end"], c["faces"]) is not None:
            cands.append(c)
    cands.sort(key=lambda c: c["at"])
    if len(cands) != 3:
        raise BoneError("found %d valid section arrays in %s, expected 3"
                        % (len(cands), MESH))
    first = next((c for c in cands if c["lod_array_len"] == len(cands)), None)
    if first is None:
        raise BoneError("no LODModels length marker in %s" % MESH)
    chain = sorted([c for c in cands if c["at"] >= first["at"]],
                   key=lambda c: c["at"])[:first["lod_array_len"]]
    if len(chain) != 3:
        raise BoneError("cooked LOD chain has %d entries, expected 3" % len(chain))
    return [c["sections"] for c in chain], idx, sha256_file(pkg_path)


def slot_map_for_lod(lod: int, mesh: dict, sections: list[dict]) -> list[int]:
    """Map PSK section order to the cooked material index, checking the face counts."""
    counts = np.bincount(mesh["F"]["m"].astype(np.int64), minlength=len(mesh["mats"]))
    cooked_counts = [int(s["faces"]) for s in sections]
    if len(counts) != len(cooked_counts):
        raise BoneError("LOD%d: %d PSK sections, %d cooked sections"
                        % (lod, len(counts), len(cooked_counts)))
    if [int(x) for x in counts] != cooked_counts:
        raise BoneError("LOD%d section face counts differ: PSK %s, cooked %s"
                        % (lod, [int(x) for x in counts], cooked_counts))
    out = []
    for s in sections:
        m = int(s["material"])
        if not 0 <= m < NSLOT:
            raise BoneError("LOD%d: cooked material %d outside 0..%d"
                            % (lod, m, NSLOT - 1))
        out.append(m)
    return out


# ---------------------------------------------------------------------------------------------
# face ownership


def face_ownership(mesh: dict, sk: dict, slot_map: list[int], lod: int) -> dict:
    P, W, F = mesh["P"], mesh["W"], mesh["F"]
    data, ch = mesh["data"], mesh["chunks"]
    if "RAWWEIGHTS" not in ch:
        raise BoneError("LOD%d: no RAWWEIGHTS" % lod)
    ro, rs, rn = ch["RAWWEIGHTS"]
    if rs != 12:
        raise BoneError("LOD%d: RAWWEIGHTS stride %d" % (lod, rs))
    rw = np.frombuffer(data, np.dtype([
        ("w", "<f4"), ("p", "<u4"), ("b", "<u4")]), rn, ro)
    nb = sk["count"]
    if int(rw["b"].max()) >= nb:
        raise BoneError("LOD%d: bone index outside REFSKELT" % lod)
    acc = np.zeros((len(P), nb), np.float32)
    np.add.at(acc, (rw["p"].astype(np.int64), rw["b"].astype(np.int64)), rw["w"])
    max_w = acc.max(1)
    owner = acc.argmax(1).astype(np.int32)
    ties = np.count_nonzero(acc == max_w[:, None], axis=1) > 1
    no_weight = max_w < MOVE_WEIGHT
    owner[ties | no_weight] = -1
    points_ge = (acc >= MOVE_WEIGHT).sum(0).astype(np.int64)
    points_dom = np.bincount(owner[owner >= 0], minlength=nb).astype(np.int64)

    face_pts = W["p"][F["w"]].astype(np.int64)           # (faces, 3) point index
    face_owner = owner[face_pts]
    same = ((face_owner[:, 0] == face_owner[:, 1]) &
            (face_owner[:, 1] == face_owner[:, 2]) &
            (face_owner[:, 0] >= 0))
    split = ~same
    slots = np.array(slot_map, dtype=np.int64)[F["m"].astype(np.int64)]
    owned_counts = np.zeros((nb, NSLOT), np.int64)
    if same.any():
        np.add.at(owned_counts, (face_owner[same, 0], slots[same]), 1)
    split_by_slot = np.bincount(slots[split], minlength=NSLOT).astype(np.int64)
    touching = np.zeros((nb, NSLOT), np.int64)
    touch_rows: list[list[tuple[int, int, int, int]]] = [[] for _ in range(nb)]
    unowned_split = 0
    for fi in np.nonzero(split)[0]:
        owners = np.unique(face_owner[fi])
        owners = owners[owners >= 0]
        if len(owners) == 0:
            unowned_split += 1
            continue
        for b in owners:
            touching[int(b), int(slots[fi])] += 1
            touch_rows[int(b)].append((lod, int(fi), int(slots[fi]), 1))
    owned_rows: list[list[tuple[int, int, int, int]]] = [[] for _ in range(nb)]
    for b in range(nb):
        for fi in np.nonzero(same & (face_owner[:, 0] == b))[0]:
            owned_rows[b].append((lod, int(fi), int(slots[fi]), 0))
    return {
        "lod": lod, "owner": owner, "touching": touching,
        "owned_counts": owned_counts, "split_by_slot": split_by_slot,
        "faces": len(F), "owned": int(same.sum()), "split": int(split.sum()),
        "split_mask": split,
        "unowned_split": unowned_split,        "points": len(P),
        "points_unique": int((~no_weight & ~ties).sum()),
        "points_no_ge_0_5": int(no_weight.sum()),
        "points_tie": int(ties.sum()),
        "points_ge": points_ge, "points_dom": points_dom,
        "max_weight": acc.max(0).astype(float),
        "face_owner": face_owner, "same": same,
        "owned_rows": owned_rows, "touch_rows": touch_rows,
        "slot_per_face": slots,
    }


# ---------------------------------------------------------------------------------------------
# glTF cross-check (optional, produced by umodel's -gltf)


def gltf_check(gltf_path: Path, sk: dict, world: list[dict]) -> dict | None:
    if not gltf_path.exists():
        return None
    bin_path = gltf_path.with_suffix(".bin")
    if not bin_path.exists():
        return None
    j = json.loads(gltf_path.read_text(encoding="utf-8"))
    if not j.get("skins"):
        return None
    skin = j["skins"][0]
    acc = j["accessors"][skin["inverseBindMatrices"]]
    bv = j["bufferViews"][acc["bufferView"]]
    raw = bin_path.read_bytes()
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    mats = np.frombuffer(raw, "<f4", acc["count"] * 16, off).reshape(
        acc["count"], 4, 4).transpose(0, 2, 1)
    worlds = np.linalg.inv(mats)[:, :3, 3]
    # glTF: (x, y, z), Y up, metres.  PSK: (x, z, -y), Z up, centimetres.
    psk = np.stack([worlds[:, 0], -worlds[:, 2], worlds[:, 1]], 1) * 100.0
    nodes = [j["nodes"][i].get("name") for i in skin["joints"]]
    by_name = {n: i for i, n in enumerate(nodes)}
    errors = []
    for i, b in enumerate(sk["bones"]):
        k = by_name.get(b["name"])
        if k is None:
            raise BoneError("glTF has no joint named %s" % b["name"])
        errors.append(float(np.linalg.norm(world[i]["world_pos"] - psk[k])))
    return {"path": str(gltf_path), "sha256": sha256_file(gltf_path),
            "bin_sha256": sha256_file(bin_path),
            "joints": len(errors), "max_delta_cm": max(errors),
            "mean_delta_cm": float(sum(errors) / len(errors))}


# ---------------------------------------------------------------------------------------------
# collection


def expected_meshes() -> dict:
    doc = json.loads(MESHES_JSON.read_text(encoding="utf-8"))
    for m in doc["meshes"]:
        if m["package"] == PACKAGE and m["mesh"] == MESH:
            return m
    raise BoneError("MESHES.json has no %s/%s" % (PACKAGE, MESH))


def slot_rows() -> list[dict]:
    doc = json.loads(SLOTS_JSON.read_text(encoding="utf-8"))
    if doc.get("mesh") != MESH:
        raise BoneError("SLOTS.json is for %s, not %s" % (doc.get("mesh"), MESH))
    return doc["slots"]


def collect() -> dict:
    missing = [name for name, _ in LOD_FILES if not (MESH_DIR / name).exists()]
    if missing:
        raise BoneError("missing mesh exports: %s; run the LOD export command in BONES.md"
                        % ", ".join(missing))
    frame = compute_frame(MESH_DIR / LOD_FILES[0][0])
    sk = frame["sk"]
    world = world_bones(sk)
    sections, export_index, pkg_sha = cooked_sections()
    expected = expected_meshes()
    slots = slot_rows()
    if len(slots) != NSLOT:
        raise BoneError("SLOTS.json has %d slots, expected %d" % (len(slots), NSLOT))
    tf = transform_check(frame, load_stations())

    lods = []
    all_owned = np.zeros((sk["count"], len(LOD_FILES), NSLOT), np.int64)
    all_touch = np.zeros((sk["count"], len(LOD_FILES), NSLOT), np.int64)
    all_points_ge = np.zeros((sk["count"], len(LOD_FILES)), np.int64)
    all_points_dom = np.zeros((sk["count"], len(LOD_FILES)), np.int64)
    all_max_weight = np.zeros((sk["count"], len(LOD_FILES)), float)
    owned_rows: list[list[tuple[int, int, int, int]]] = [[] for _ in range(sk["count"])]
    touch_rows: list[list[tuple[int, int, int, int]]] = [[] for _ in range(sk["count"])]
    split_rows_all = []
    for file_name, lod in LOD_FILES:
        path = MESH_DIR / file_name
        mesh = read_mesh(path)
        mesh["path"] = str(path)
        if len(mesh["mats"]) != len(sections[lod]):
            raise BoneError("LOD%d: %d PSK materials, %d cooked sections"
                            % (lod, len(mesh["mats"]), len(sections[lod])))
        slot_map = slot_map_for_lod(lod, mesh, sections[lod])
        own = face_ownership(mesh, sk, slot_map, lod)
        exp = expected["lods"][lod]["faces"] if lod < len(expected["lods"]) else None
        if exp is not None and exp != own["faces"]:
            raise BoneError("LOD%d: %d faces, MESHES.json says %d"
                            % (lod, own["faces"], exp))
        if own["owned"] + own["split"] != own["faces"]:
            raise BoneError("LOD%d: owned + split != total" % lod)
        slot_totals = own["owned_counts"].sum(0) + own["split_by_slot"]
        expected_by_slot = expected["lods"][lod].get("faces_by_material", {})
        for s in range(NSLOT):
            if int(slot_totals[s]) != int(expected_by_slot.get(str(s), 0)):
                raise BoneError("LOD%d slot %d: %d faces, MESHES.json says %s"
                                % (lod, s, slot_totals[s],
                                   expected_by_slot.get(str(s), 0)))
        all_owned[:, lod, :] = own["owned_counts"]
        all_touch[:, lod, :] = own["touching"]
        all_points_ge[:, lod] = own["points_ge"]
        all_points_dom[:, lod] = own["points_dom"]
        all_max_weight[:, lod] = own["max_weight"]
        for b in range(sk["count"]):
            owned_rows[b].extend(own["owned_rows"][b])
            touch_rows[b].extend(own["touch_rows"][b])
        split_rows_all.extend((lod, int(fi), int(own["slot_per_face"][fi]))
                              for fi in np.nonzero(own["split_mask"])[0])
        lods.append({
            "lod": lod,
            "file": str(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "face_format": mesh["face_format"],
            "points": own["points"],
            "wedges": len(mesh["W"]),
            "faces": own["faces"],
            "sections": len(mesh["mats"]),
            "materials": len(mesh["mats"]),
            "owned": own["owned"],
            "split": own["split"],
            "unowned_split": own["unowned_split"],
            "points_with_ge_0_5": own["points_unique"],
            "points_no_ge_0_5": own["points_no_ge_0_5"],
            "points_tie": own["points_tie"],
            "expected_faces": exp,
            "faces_by_slot": [int(x) for x in slot_totals],
            "owned_by_slot": [int(x) for x in own["owned_counts"].sum(0)],
            "split_by_slot": [int(x) for x in own["split_by_slot"]],
            "slot_map": [int(x) for x in slot_map],
        })

    # per-bone files: owned and split-touching rows, sorted and unique
    BONE_ROOT.mkdir(parents=True, exist_ok=True)
    face_files = {}
    for b in range(sk["count"]):
        rows = owned_rows[b] + touch_rows[b]
        arr = np.array(rows, dtype=np.int32).reshape(-1, 4) if rows else np.zeros((0, 4), np.int32)
        if len(arr):
            arr = np.unique(arr, axis=0)
        name = sk["bones"][b]["name"]
        path = BONE_ROOT / (name + ".npy")
        np.save(path, arr, allow_pickle=False)
        face_files[name] = str(path)
    split_arr = (np.array(split_rows_all, dtype=np.int32).reshape(-1, 3)
                 if split_rows_all else np.zeros((0, 3), np.int32))
    if len(split_arr):
        split_arr = np.unique(split_arr, axis=0)
    split_file = BONE_ROOT / "_split.npy"
    np.save(split_file, split_arr, allow_pickle=False)

    bones = []
    for i, b in enumerate(sk["bones"]):
        wq = world[i]["world_q"]
        wp = world[i]["world_pos"]
        pivot = BA.to_jc3_rot(np.array([wp]))[0] * SCALE + tf["offset_used"]
        bones.append({
            "index": i,
            "name": b["name"],
            "parent_index": b["parent"],
            "parent": sk["bones"][b["parent"]]["name"],
            "children": b["children"],
            "flags": b["flags"],
            "bind": {
                "local_position_cm": [round(float(x), 6) for x in b["pos"]],
                "local_rotation_quat": [round(float(x), 9) for x in b["q"]],
                "world_position_cm": [round(float(x), 6) for x in wp],
                "world_rotation_quat": [round(float(x), 9) for x in wq],
            },
            "pivot_jc3_m": [round(float(x), 6) for x in pivot],
            "points_ge_0_5": {str(l): int(all_points_ge[i, l]) for l in range(3)},
            "points_dominant": {str(l): int(all_points_dom[i, l]) for l in range(3)},
            "max_weight": {str(l): round(float(all_max_weight[i, l]), 6) for l in range(3)},
            "owned_faces": {str(l): int(all_owned[i, l].sum()) for l in range(3)},
            "owned_faces_by_slot": {str(l): [int(x) for x in all_owned[i, l]]
                                    for l in range(3)},
            "split_touching": {str(l): int(all_touch[i, l].sum()) for l in range(3)},
            "split_touching_by_slot": {str(l): [int(x) for x in all_touch[i, l]]
                                       for l in range(3)},
            "face_file": face_files[b["name"]],
            "face_rows": int(len(np.load(face_files[b["name"]]))),
        })

    owned_by_lod = [int(sum(l["owned"] for l in lods if l["lod"] == x)) for x in range(3)]
    split_by_lod = [int(sum(l["split"] for l in lods if l["lod"] == x)) for x in range(3)]
    total_by_lod = [int(l["faces"]) for l in lods]
    split_touching_rows = int(sum(all_touch[i, l].sum()
                                 for i in range(sk["count"]) for l in range(3)))
    checks = {
        "bone_count": sk["count"],
        "unique_names": len(set(sk["names"])) == sk["count"],
        "parent_before_child": all(b["parent"] <= i for i, b in enumerate(sk["bones"])),
        "root_bones": [b["name"] for i, b in enumerate(sk["bones"]) if b["parent"] == i],
        "faces_total": total_by_lod,
        "owned_total": owned_by_lod,
        "split_total": split_by_lod,
        "owned_plus_split_equals_total": all(
            owned_by_lod[l] + split_by_lod[l] == total_by_lod[l] for l in range(3)),
        "owned_by_bone_equals_total": all(
            sum(b["owned_faces"][str(l)] for b in bones) == owned_by_lod[l]
            for l in range(3)),
        "faces_match_meshes": all(l["faces"] == l["expected_faces"] for l in lods),
        "slot_totals_match_cooked": True,
        "points_total": [l["points"] for l in lods],
        "points_with_ge_0_5": [l["points_with_ge_0_5"] for l in lods],
        "points_no_ge_0_5": [l["points_no_ge_0_5"] for l in lods],
        "points_tie": [l["points_tie"] for l in lods],
        "unowned_split": [l["unowned_split"] for l in lods],
        "face_files": len(face_files),
        "split_file": str(split_file),
        "split_file_rows": int(len(split_arr)),
        "wheel_pivot_max_delta_m": None,
        "gltf": None,
    }
    # wheel pivots against the stations transform
    wheel_bones = {
        "f_l": "Wheel_Front_Left_Vis",
        "f_r": "Wheel_Front_Right_Vis",
        "r_l": "Wheel_Rear_Left_Vis",
        "r_r": "Wheel_Rear_Right_Vis",
    }
    name_to_bone = {b["name"]: b for b in bones}
    wd = []
    for c, name in wheel_bones.items():
        b = name_to_bone.get(name)
        if b is None or tf["hubs"].get(c) is None:
            continue
        wd.append(float(np.linalg.norm(np.array(b["pivot_jc3_m"]) -
                                       tf["hubs"][c]["station"])))
    if len(wd) != WHEELS:
        raise BoneError("expected %d wheel pivots to check, found %d" % (WHEELS, len(wd)))
    checks["wheel_pivot_max_delta_m"] = max(wd)
    gt = gltf_check(MESH_DIR / "gltf" / "Batmobile_V2.gltf", sk, world)
    checks["gltf"] = gt
    if gt and gt["max_delta_cm"] > 0.05:
        raise BoneError("glTF joint cross-check failed: %.6f cm" % gt["max_delta_cm"])

    verdict = (
        "%d bones, %d root, 3 LODs: %s faces; %s owned, %s split; %d point records with a "
        "unique >= 0.5 influence; %d per-bone face files; wheel-bone/hub offset %s m; glTF "
        "joint max error %s cm"
        % (checks["bone_count"], len(checks["root_bones"]),
           " / ".join("{:,}".format(x) for x in total_by_lod),
           " / ".join("{:,}".format(x) for x in owned_by_lod),
           " / ".join("{:,}".format(x) for x in split_by_lod),
           sum(checks["points_with_ge_0_5"]), len(face_files),
           ("%.6f" % checks["wheel_pivot_max_delta_m"]
            if checks["wheel_pivot_max_delta_m"] is not None else "n/a"),
           ("%.4f" % gt["max_delta_cm"]) if gt else "n/a"))
    return {
        "schema": 1,
        "generator": "grab_bones.py",
        "verdict": verdict,
        "mesh": MESH,
        "package": PACKAGE,
        "package_sha256": pkg_sha,
        "export_index": export_index,
        "inputs": {
            "mesh_root": str(MESH_DIR),
            "bone_root": str(BONE_ROOT),
            "game": str(GAME),
            "meshes_json": "Research/BatmobileGrab/MESHES.json",
            "slots_json": "Research/BatmobileGrab/SLOTS.json",
            "stations": str(STATIONS) if STATIONS.exists() else None,
            "transform": {
                "scale": SCALE,
                "rotation": "bat_assemble.to_jc3_rot: (x,y,z) -> (-y,z,-x)",
                "ground": GROUND,
                "center_z": CENTER_Z,
            },
        },
        "lods": lods,
        "slots": [{"index": s["index"], "material": s["material"],
                   "kind": s.get("kind"), "parent": s.get("parent"),
                   "lod0_faces": s.get("lod0_faces")} for s in slots],
        "transform": {
            "offset_used": [round(float(x), 9) for x in tf["offset_used"]],
            "offset_computed": [round(float(x), 9) for x in tf["offset_computed"]],
            "offset_delta_m": (round(tf["offset_delta_m"], 9)
                               if tf["offset_delta_m"] is not None else None),
            "hub_delta_m": (round(tf["hub_delta_m"], 9)
                            if tf["hub_delta_m"] is not None else None),
            "stations": tf["stations"],
            "stations_sha256": tf.get("stations_sha256"),
            "hubs": {c: {"computed_jc3_m": [round(float(x), 6) for x in h["computed"]],
                         "station_jc3_m": [round(float(x), 6) for x in h["station"]],
                         "delta_m": round(float(h["delta_m"]), 9),
                         "tyre_bone": h["tyre_bone"]}
                     for c, h in tf["hubs"].items()},
        },
        "counts": {
            "bones": sk["count"],
            "lods": 3,
            "slots": NSLOT,
            "faces_by_lod": total_by_lod,
            "owned_by_lod": owned_by_lod,
            "split_by_lod": split_by_lod,
            "points_by_lod": [l["points"] for l in lods],
            "face_files": len(face_files),
            "split_file": str(split_file),
            "split_file_rows": int(len(split_arr)),
            "split_touching_rows": split_touching_rows,
            "face_rows_total": int(sum(b["face_rows"] for b in bones)),
            "owned_total": int(sum(owned_by_lod)),
            "split_total": int(sum(split_by_lod)),
        },
        "checks": checks,
        "bones": bones,
    }


# ---------------------------------------------------------------------------------------------
# markdown


def fnum(v, places=3):
    if v is None:
        return "-"
    return ("%%.%df" % places) % float(v)


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |")
    return out


def render_md(doc: dict) -> str:
    c = doc["counts"]
    L = []
    add = L.append
    add("# Batmobile_V2 skeleton and face ownership (G1-11)")
    add("")
    add("Generated by `Tools/scripts/grab_bones.py` from the `Batmobile_V2` PSKX/PSK exports, the "
        "cooked `%s.upk` section tables and `bat_assemble`'s one transform. Nothing in this page "
        "is hand-copied from a render: the pivots are accumulated from `REFSKELT`, and the face "
        "counts are read from `RAWWEIGHTS`." % doc["package"])
    add("")
    add("**Verdict:** " + doc["verdict"] + ".")
    add("")
    add("## 1. Inputs and LODs")
    add("")
    rows = []
    for l in doc["lods"]:
        rows.append(["LOD%d" % l["lod"], "`%s`" % Path(l["file"]).name,
                     "{:,}".format(l["points"]), "{:,}".format(l["faces"]),
                     str(l["sections"]), "{:,}".format(l["expected_faces"]),
                     "`%s`" % l["sha256"][:16]])
    add("\n".join(md_table(["LOD", "file", "points", "faces", "sections", "MESHES.md",
                            "sha256"], rows)))
    add("")
    add("LOD0 was already exported. LOD1/LOD2 were made with an isolated `umodel.cfg` because "
        "UEViewer's settings file overrides the `-lods` command-line flag (`ExportMeshLods=false`). "
        "The user's config was not touched; see §9.")
    add("")
    add("## 2. The one transform")
    add("")
    t = doc["transform"]
    add("`T(p) = bat_assemble.to_jc3_rot(p) * 0.01 + offset`; rotation `(x, y, z) -> (-y, z, -x)`, "
        "so the result is metres in the JC3 frame (X width, Y up, Z length, front -Z).")
    add("")
    add("| quantity | value |")
    add("|---|---|")
    add("| offset used (m) | %s |" % ", ".join("%.9f" % x for x in t["offset_used"]))
    add("| offset recomputed (m) | %s |" % ", ".join("%.9f" % x for x in t["offset_computed"]))
    add("| offset difference | %s m |" % fnum(t["offset_delta_m"], 9))
    add("| max hub difference vs stations.json | %s m |" % fnum(t["hub_delta_m"], 9))
    add("| stations.json | `%s` |" % (t["stations"] or "-"))
    add("")
    if t["hubs"]:
        rows = []
        for corner, h in t["hubs"].items():
            rows.append([corner, "`%s`" % h["tyre_bone"],
                         ", ".join("%.4f" % x for x in h["computed_jc3_m"]),
                         ", ".join("%.4f" % x for x in h["station_jc3_m"]),
                         fnum(h["delta_m"], 9)])
        add("\n".join(md_table(["corner", "tyre bone", "hub from geometry + T",
                                "stations.json hub", "delta m"], rows)))
    add("")
    add("`Working/TrueScale/stations.json` is the transform the assembled meshes were built with. "
        "The offset is recomputed from the current LOD0 wheel hubs and must agree with that file; "
        "the file's offset is then used for the bone pivots, so the skeleton and the mesh cannot "
        "drift apart. The wheel-bone/hub offset in §8 is the skeleton's own lateral pivot offset "
        "from the tyre geometry, not transform drift; the transform check is the hub column above.")
    add("")
    add("## 3. Skeleton")
    add("")
    add("| index | bone | parent | pivot x | pivot y | pivot z | owned L0 | owned L1 | owned L2 | split L0 | split L1 | split L2 |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for b in doc["bones"]:
        p = b["pivot_jc3_m"]
        add("| %d | `%s` | `%s` | %.3f | %.3f | %.3f | %d | %d | %d | %d | %d | %d |"
            % (b["index"], b["name"], b["parent"], p[0], p[1], p[2],
               b["owned_faces"]["0"], b["owned_faces"]["1"], b["owned_faces"]["2"],
               b["split_touching"]["0"], b["split_touching"]["1"],
               b["split_touching"]["2"]))
    add("")
    add("`owned` columns are ownership. `split` columns are split faces **touching** the bone "
        "(one face can touch two or three bones), not a second ownership count.")
    add("")
    add("Pivots are the bind-pose world origin of each bone after `T`, metres. The root is "
        "`%s` at `%s`. The PSK parent chain uses the left-handed order "
        "`q_world = q_child * q_parent` and rotates the child's local offset by the inverse of "
        "the parent's rotation; that is what reproduces umodel's own glTF inverse-bind matrices."
        % (doc["checks"]["root_bones"][0] if doc["checks"]["root_bones"] else "-",
           ", ".join("%.3f" % x for x in doc["bones"][0]["pivot_jc3_m"])
           if doc["bones"] else "-"))
    add("")
    add("## 4. Faces by LOD and slot")
    add("")
    rows = []
    for l in doc["lods"]:
        rows.append(["LOD%d" % l["lod"], "{:,}".format(l["faces"]),
                     "{:,}".format(l["owned"]), "{:,}".format(l["split"]),
                     str(l["unowned_split"]), "{:,}".format(l["expected_faces"])])
    add("\n".join(md_table(["LOD", "faces", "owned", "split", "split with no >=0.5 owner",
                            "MESHES.md"], rows)))
    add("")
    add("A face is owned only when all three points have the same unique `>= 0.5` influence. "
        "Otherwise it is split and is not assigned to a bone; the per-slot split counts below "
        "include every split face once.")
    add("")
    for l in doc["lods"]:
        add("### LOD%d" % l["lod"])
        add("")
        add("| slot | material | faces | owned | split |")
        add("|---|---|---|---|---|")
        for s in doc["slots"]:
            i = s["index"]
            add("| %d | `%s` | %d | %d | %d |"
                % (i, s["material"], l["faces_by_slot"][i],
                   l["owned_by_slot"][i], l["split_by_slot"][i]))
        add("")
    add("## 5. Per-bone owned faces by material slot")
    add("")
    add("Cells are owned faces only; a split face is not owned and is counted in §6. The JSON "
        "has the same three tables as `owned_faces_by_slot`.")
    add("")
    for l in doc["lods"]:
        lod = str(l["lod"])
        add("### LOD%d" % l["lod"])
        add("")
        headers = ["bone"] + [str(s["index"]) for s in doc["slots"]] + ["total"]
        add("| " + " | ".join(headers) + " |")
        add("|" + "|".join("---" for _ in headers) + "|")
        for b in doc["bones"]:
            vals = b["owned_faces_by_slot"][lod]
            add("| `%s` | %s | %d |" % (b["name"], " | ".join(str(x) for x in vals),
                                        sum(vals)))
        add("")
    add("## 6. Split faces")
    add("")
    rows = []
    for l in doc["lods"]:
        rows.append(["LOD%d" % l["lod"], "{:,}".format(l["split"]),
                     "{:,}".format(l["unowned_split"]),
                     ", ".join("%d:%d" % (s["index"], l["split_by_slot"][s["index"]])
                               for s in doc["slots"] if l["split_by_slot"][s["index"]])
                     or "-"])
    add("\n".join(md_table(["LOD", "split faces", "no owner >=0.5", "by slot"], rows)))
    add("")
    add("`_split.npy` lists every split face once as `(lod, face, slot)`. A split face can appear "
        "in more than one per-bone file as `kind=1`; that is a **touching** list, not ownership.")
    add("")
    add("### Bones touching split faces")
    add("")
    top = sorted(doc["bones"], key=lambda b: -sum(b["split_touching"].values()))
    rows = [[ "`%s`" % b["name"], str(b["split_touching"]["0"]),
             str(b["split_touching"]["1"]), str(b["split_touching"]["2"])]
            for b in top if sum(b["split_touching"].values())]
    add("\n".join(md_table(["bone", "LOD0", "LOD1", "LOD2"], rows)))
    add("")
    add("## 7. Face index files (outside the repository)")
    add("")
    add("`E:\\Modding\\_gamedata\\BmAKgrab\\bones\\<bone>.npy`; 180 files, int32, one row per face:")
    add("")
    add("```text")
    add("(lod, face_index, slot, kind)   kind 0 = owned, 1 = split-touching")
    add("```")
    add("")
    add("`_split.npy` is `(lod, face_index, slot)`. All files are written by `--write` and "
        "checked by `--check`; no face list is committed to the repository.")
    add("")
    add("| check | result |")
    add("|---|---|")
    add("| face files | %d |" % c["face_files"])
    add("| `_split.npy` rows | %d |" % c["split_file_rows"])
    add("| per-bone owned rows | %d |" % c["owned_total"])
    add("| per-bone split-touching rows | %d |" % c["split_touching_rows"])
    add("| total per-bone rows | %d |" % c["face_rows_total"])
    add("")
    add("## 8. Checks")
    add("")
    ch = doc["checks"]
    add("| check | result |")
    add("|---|---|")
    add("| bones | %d, unique names %s |" % (ch["bone_count"], ch["unique_names"]))
    add("| parent before child | %s |" % ch["parent_before_child"])
    add("| roots | %s |" % ", ".join("`%s`" % x for x in ch["root_bones"]))
    add("| faces per LOD | %s |" % " / ".join("{:,}".format(x) for x in ch["faces_total"]))
    add("| owned + split = total | %s |" % ch["owned_plus_split_equals_total"])
    add("| owned by bone = total | %s |" % ch["owned_by_bone_equals_total"])
    add("| faces match MESHES.md | %s |" % ch["faces_match_meshes"])
    add("| slot totals match cooked sections | %s |" % ch["slot_totals_match_cooked"])
    add("| points with no >=0.5 owner | %s |" % ch["points_no_ge_0_5"])
    add("| points with a tie | %s |" % ch["points_tie"])
    add("| split with no >=0.5 owner | %s |" % ch["unowned_split"])
    add("| wheel bone pivot vs tyre geometry hub | %s m |" % fnum(ch["wheel_pivot_max_delta_m"], 9))
    if ch["gltf"]:
        add("| PSK pivots vs glTF inverse bind (180 joints) | %s cm max, %s cm mean |"
            % (fnum(ch["gltf"]["max_delta_cm"], 6), fnum(ch["gltf"]["mean_delta_cm"], 6)))
    else:
        add("| PSK pivots vs glTF inverse bind | glTF export not present |")
    add("")
    add("## 9. Limits and reproduce")
    add("")
    add("* Ownership uses the `>= 0.5` threshold exactly. A point with two equal maxima would be "
        "ambiguous; this mesh has %s such points, so none are guessed."
        % " / ".join(str(x) for x in ch["points_tie"]))
    add("* Split faces are not assigned to a bone. Per-bone `kind=1` rows are touching evidence "
        "and can overlap; they are not ownership.")
    add("* LOD1/LOD2 section order is mapped to the cooked section material index and verified "
        "against the face count of every section, not assumed from a material name (PSK `MATT` "
        "names are generic `material_N`).")
    add("* The external LOD1/LOD2 exports are not in the repository. Reproduce with an isolated "
        "`umodel.cfg` (the user's config is not edited):")
    add("")
    add("```bash")
    add("python Tools/scripts/grab_bones.py --write")
    add("python Tools/scripts/grab_bones.py --check")
    add("```")
    add("")
    add("To recreate the missing LODs, run `umodel.exe -export -psk -lods -notex` from a "
        "temporary directory containing an `umodel.cfg` with `ExportMeshLods = true`, then copy "
        "`Batmobile_V2_Lod1.pskx` and `Batmobile_V2_Lod2.psk` beside `Batmobile_V2.pskx` in "
        "`E:\\Modding\\_gamedata\\BmAKgrab\\meshes\\Playable_Batmobile_SF\\Playable_Batmobile_SF\\SkeletalMesh3\\`.")
    add("")
    add("* The optional glTF cross-check reads `...SkeletalMesh3/gltf/Batmobile_V2.gltf` and "
        "`.bin`; it is evidence only, not a pivot source. If those files are removed, re-run "
        "`--write` so the record no longer expects them.")
    add("")
    add("Environment: `BMAK_GAME_DIR`, `BMAK_MESH_DIR`, `BMAK_BONE_DIR` override the lab paths. "
        "No game file, install, save or dropzone is modified.")
    add("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------
# check / write


def json_text(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def check_files(doc: dict) -> list[str]:
    bad = []
    total_rows = 0
    for b in doc["bones"]:
        path = Path(b["face_file"])
        if not path.exists():
            bad.append("missing %s" % path)
            continue
        arr = np.load(path, allow_pickle=False)
        if arr.dtype != np.int32 or arr.ndim != 2 or arr.shape[1] != 4:
            bad.append("%s: expected int32 (N,4), got %s %s"
                       % (path.name, arr.dtype, arr.shape))
            continue
        if len(arr) != b["face_rows"]:
            bad.append("%s: %d rows, JSON says %d" % (path.name, len(arr), b["face_rows"]))
        if len(arr):
            if arr[:, 0].min() < 0 or arr[:, 0].max() > 2:
                bad.append("%s: lod outside 0..2" % path.name)
            if arr[:, 1].min() < 0:
                bad.append("%s: negative face" % path.name)
            if arr[:, 2].min() < 0 or arr[:, 2].max() >= NSLOT:
                bad.append("%s: slot outside 0..%d" % (path.name, NSLOT - 1))
            if not set(np.unique(arr[:, 3]).tolist()) <= {0, 1}:
                bad.append("%s: kind is not 0/1" % path.name)
            if len(np.unique(arr, axis=0)) != len(arr):
                bad.append("%s: duplicate rows" % path.name)
        if len(arr):
            faces_by_lod = {l["lod"]: l["faces"] for l in doc["lods"]}
            for lod, faces in faces_by_lod.items():
                sel = arr[:, 0] == lod
                if sel.any() and arr[sel, 1].max() >= faces:
                    bad.append("%s: face index outside LOD%d (%d faces)"
                               % (path.name, lod, faces))
        k0 = int((arr[:, 3] == 0).sum()) if len(arr) else 0
        k1 = int((arr[:, 3] == 1).sum()) if len(arr) else 0
        if k0 != sum(b["owned_faces"].values()):
            bad.append("%s: %d owned rows, JSON says %d"
                       % (path.name, k0, sum(b["owned_faces"].values())))
        if k1 != sum(b["split_touching"].values()):
            bad.append("%s: %d split-touching rows, JSON says %d"
                       % (path.name, k1, sum(b["split_touching"].values())))
        total_rows += len(arr)
    sf = Path(doc["counts"]["split_file"])
    if not sf.exists():
        bad.append("missing %s" % sf)
    else:
        arr = np.load(sf, allow_pickle=False)
        if arr.dtype != np.int32 or arr.ndim != 2 or arr.shape[1] != 3:
            bad.append("%s: expected int32 (N,3), got %s %s"
                       % (sf.name, arr.dtype, arr.shape))
        elif len(arr) != doc["counts"]["split_file_rows"]:
            bad.append("%s: %d rows, JSON says %d"
                       % (sf.name, len(arr), doc["counts"]["split_file_rows"]))
    expected_rows = sum(l["owned"] for l in doc["lods"]) + \
        sum(b["split_touching"][str(l)] for b in doc["bones"] for l in range(3))
    if total_rows != expected_rows:
        bad.append("per-bone row total %d does not match owned + split-touching %d"
                   % (total_rows, expected_rows))
    return bad


def write(doc: dict) -> None:
    OUT_JSON.write_text(json_text(doc), encoding="utf-8")
    OUT_MD.write_text(render_md(doc), encoding="utf-8")
    print("wrote %s (%d bytes)" % (OUT_JSON, OUT_JSON.stat().st_size))
    print("wrote %s (%d bytes)" % (OUT_MD, OUT_MD.stat().st_size))
    print("wrote %d bone face files and %s" % (len(doc["bones"]),
                                                doc["counts"]["split_file"]))
    print(doc["verdict"])


def check(doc: dict) -> int:
    bad = []
    for path, text in ((OUT_JSON, json_text(doc)), (OUT_MD, render_md(doc))):
        if not path.exists():
            bad.append("missing %s" % path)
            continue
        old = path.read_text(encoding="utf-8")
        if old != text:
            old_lines, new_lines = old.splitlines(), text.splitlines()
            at = next((i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b),
                      min(len(old_lines), len(new_lines)))
            bad.append("%s differs at line %d: on disk %r, derived %r"
                       % (path.name, at + 1,
                          old_lines[at][:120] if at < len(old_lines) else "",
                          new_lines[at][:120] if at < len(new_lines) else ""))
    bad += check_files(doc)
    for key, value in doc["checks"].items():
        if isinstance(value, bool) and not value:
            bad.append("check %s is false" % key)
    if bad:
        for b in bad[:20]:
            print("FAIL: " + b)
        if len(bad) > 20:
            print("FAIL: ... %d more" % (len(bad) - 20))
        return 1
    print("PASS: " + doc["verdict"])
    print("%d bone face files, %d split rows, all record and .npy checks pass"
          % (doc["counts"]["face_files"], doc["counts"]["split_file_rows"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="regenerate BONES.json, BONES.md and the external .npy files")
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare the record and the external .npy files")
    a = ap.parse_args()
    if not a.write and not a.check:
        ap.error("choose --write or --check")
    doc = collect()
    if a.check:
        return check(doc)
    write(doc)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BoneError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        sys.exit(2)
