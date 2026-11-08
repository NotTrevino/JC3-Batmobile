"""bm_colmesh.py - B-10b (build): the body's world collision built from the Batmobile mesh.

Found by Q re-test 4 (2026-11-02, user: "collision misaligned"; decision "B, build collision from the
Batmobile mesh"). The world collision of part 0 is an `hknpExternMeshShape` whose geometry is BAKED in the
.physicsc (MODLOG sect 56's "follows the render mesh" was wrong): the Serpente's 650-vertex / 1,261-triangle
body inside a 3.5 x 2.3 x 7.0 m Batmobile. B-10 rescaled five polytopes only.

Format (decoded on the donor file, each rule with its oracle - `selftest()`):
  hknpExternMeshShape +0x20 -> hkRefCountedProperties {hkGeometry A, hkGeometry B, CPfxPartIndexProperty}
                      +0x68 -> hknpExternMeshShapeData
  hkGeometry      +0x10 hkArray vertices (vec4, w 0) -> +0x30; +0x20 hkArray triangles (a, b, c, material
                  int32) -> +0x30 + 16 * nv. A carries the surface material (donor: 14 metal, 19 plastic,
                  16 glass), B the same topology with material -1 (the deform target; R1: no deform, so B =
                  A's positions).
  ExternMeshData  +0x10 hkArray nodes (6 B, hkcdStaticTree Codec3Axis6) -> +0x60, 0x7F pad to 16;
                  +0x20/+0x30 domain = union(A, B) -/+ 0.05 (w -0.05/+0.05);
                  +0x48 hkArray sections (2 x 0x70, empty) -> after the nodes, copied.
  node            xyz[3] nibble pairs: child = parent shrunk by (hi nibble)^2/226 and (lo nibble)^2/226 of
                  the parent extent per side; hiData bit 7 = internal; data (23 bit): internal = leaves in
                  the left subtree (left = i + 1, right = i + 2 * data), leaf = triangle index. Pre-order.
                  Oracle: the donor body tree decodes with 0 of 3,783 vertices outside their leaf box and
                  reaches each of the 1,261 triangles exactly once (a linear /15 reading gives 11,159 misses).
  hknpDynamicCompoundShapeData  hkcdDynamicTree: hkArray nodes (32 B: min xyz + 0x3f000000|parent, max
                  xyz + u16 children; leaf = (0, instance)), root at +0x30. Leaf = the instance's shape box
                  in compound space (a polytope's box grown by its convex_radius), internal = exact union
                  of its children. Oracle: refitting every donor tree reproduces it to 1e-5 m. Refit after any shape change
                  (B-10 left the wheel leaves at the old size).

Source mesh: the Batmobile body LOD2 (`sportsmuscle_body_lod2.rbm`), welded by position: 6,269 triangles,
95 % of LOD1's vertices within 0.045 m of it (LOD5: 0.20 m, max 0.57 m - loses the fins). The fleet's
largest single collision geometry is 2,626 triangles (19,096 geometries, 232 entities); quadric decimation
of this non-manifold render mesh to that size doubles the error, so LOD2 is used as is - recorded as above
fleet practice, no format limit (data 23 bit, indices int32). Material: `Window` block -> 16 (donor glass),
every other block -> 14 (donor metal; BmAK armour).

    bm_colmesh.apply(physicsc_path, body_rbm_path) -> dict
"""
from __future__ import annotations

import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3geom  # noqa: E402
import jc3hkx  # noqa: E402

DOMAIN_MARGIN = 0.05        # decoded: donor domain = union(A, B) -/+ 0.05, w carries -/+0.05
Q = 226.0                   # Codec3Axis6 quantization denominator (oracle above)
MAT_GLASS, MAT_METAL, MAT_DEFORM = 16, 14, -1
WELD = 1e-4                 # m
DONOR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Builds", "test-091", "aaf", "models", "jc_vehicles",
                     "01_land", "v0300_car_kensington_sportsmuscle", "sportsmuscle.physicsc")   # B-10's donor


# ---------------------------------------------------------------- mesh
def load_body(rbm: str):
    m = jc3geom.decode_mesh(open(rbm, "rb").read(), rbm)
    P, T, M = [], [], []
    base = 0
    for b in m["blocks"]:
        p = np.asarray(b["positions"], np.float64)[:, :3]
        idx = np.asarray(b["indices"], np.int64).reshape(-1, 3) + base
        P.append(p); T.append(idx)
        M.append(np.full(len(idx), MAT_GLASS if b.get("type") == "Window" else MAT_METAL, np.int32))
        base += len(p)
    P, T, M = np.vstack(P), np.vstack(T), np.concatenate(M)
    key = np.round(P / WELD).astype(np.int64)
    _u, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    V = P[first]
    T = inv.reshape(-1)[T]
    keep = (T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])
    return V.astype(np.float32), T[keep].astype(np.int32), M[keep]


# ---------------------------------------------------------------- static tree (Codec3Axis6)
def decode_tree(nodes, domain):
    """[(leaf triangle, (lo, hi))] in pre-order + structural errors."""
    out, errs = [], []

    def rec(i, lo, hi, depth):
        if depth > 64 or i >= len(nodes):
            errs.append(f"node {i} out of range / too deep"); return
        x = nodes[i]
        ext = [hi[k] - lo[k] for k in range(3)]
        nlo = [lo[k] + ext[k] * (x[k] >> 4) ** 2 / Q for k in range(3)]
        nhi = [hi[k] - ext[k] * (x[k] & 15) ** 2 / Q for k in range(3)]
        data = (x[3] & 0x7F) << 16 | x[4]
        if x[3] & 0x80:
            rec(i + 1, nlo, nhi, depth + 1)
            rec(i + 2 * data, nlo, nhi, depth + 1)
        else:
            out.append((data, (nlo, nhi)))
    rec(0, domain[0], domain[1], 0)
    return out, errs


def build_tree(V, T, domain):
    """Top-down median split on the widest centroid axis; conservative nibble quantization."""
    tri_lo = V[T].min(1).astype(np.float64)
    tri_hi = V[T].max(1).astype(np.float64)
    cen = (tri_lo + tri_hi) / 2
    nodes: list = []

    def quant(plo, phi, clo, chi):
        xyz = []
        for k in range(3):
            ext = phi[k] - plo[k]
            a = c = 0
            if ext > 0:
                for n in range(15, -1, -1):
                    if plo[k] + ext * n * n / Q <= clo[k]:
                        a = n; break
                for n in range(15, -1, -1):
                    if phi[k] - ext * n * n / Q >= chi[k]:
                        c = n; break
            xyz.append(a << 4 | c)
        dlo = [plo[k] + (phi[k] - plo[k]) * (xyz[k] >> 4) ** 2 / Q for k in range(3)]
        dhi = [phi[k] - (phi[k] - plo[k]) * (xyz[k] & 15) ** 2 / Q for k in range(3)]
        return xyz, dlo, dhi

    def rec(ids, plo, phi, root=False):
        lo, hi = tri_lo[ids].min(0), tri_hi[ids].max(0)
        if root:
            xyz, dlo, dhi = [0, 0, 0], list(plo), list(phi)
        else:
            xyz, dlo, dhi = quant(plo, phi, lo, hi)
        me = len(nodes)
        nodes.append(None)
        if len(ids) == 1:
            t = int(ids[0])
            nodes[me] = (xyz[0], xyz[1], xyz[2], (t >> 16) & 0x7F, t & 0xFFFF)
            return 1
        c = cen[ids]
        ax = int(np.argmax(c.max(0) - c.min(0)))
        order = ids[np.argsort(c[:, ax], kind="stable")]
        half = len(order) // 2
        nl = rec(order[:half], dlo, dhi)
        nodes[me] = (xyz[0], xyz[1], xyz[2], 0x80 | ((nl >> 16) & 0x7F), nl & 0xFFFF)
        nr = rec(order[half:], dlo, dhi)
        return nl + nr
    rec(np.arange(len(T)), domain[0], domain[1], root=True)
    return nodes


def check_tree(nodes, domain, V, T) -> list[str]:
    leaves, errs = decode_tree(nodes, domain)
    seen = [t for t, _ in leaves]
    if sorted(seen) != list(range(len(T))):
        errs.append(f"leaves reach {len(set(seen))} distinct of {len(T)} triangles ({len(seen)} leaves)")
    if len(nodes) != 2 * len(T) - 1:
        errs.append(f"{len(nodes)} nodes for {len(T)} triangles")
    miss = 0
    for t, (lo, hi) in leaves:
        p = V[T[t]]
        if (p < np.array(lo) - 1e-5).any() or (p > np.array(hi) + 1e-5).any():
            miss += 1
    if miss:
        errs.append(f"{miss} triangles outside their leaf box")
    return errs


# ---------------------------------------------------------------- blobs
def geometry_blob(template: bytes, V, T, mats) -> tuple[bytes, dict]:
    nv, nt = len(V), len(T)
    out = bytearray(template[:0x30])
    struct.pack_into("<II", out, 0x18, nv, nv | 0x80000000)
    struct.pack_into("<II", out, 0x28, nt, nt | 0x80000000)
    vb = np.zeros((nv, 4), np.float32); vb[:, :3] = V
    tb = np.zeros((nt, 4), np.int32); tb[:, :3] = T; tb[:, 3] = mats
    out += vb.tobytes() + tb.tobytes()
    old_nv = struct.unpack_from("<I", template, 0x18)[0]
    return bytes(out), {0x10: 0x10, 0x20: 0x20, 0x30: 0x30, 0x30 + 16 * old_nv: 0x30 + 16 * nv}   # header slots + arrays


def data_blob(template: bytes, nodes, domain) -> tuple[bytes, dict]:
    n_old = struct.unpack_from("<I", template, 0x18)[0]
    sec_old = ((0x60 + 6 * n_old + 15) // 16) * 16
    out = bytearray(template[:0x60])
    n = len(nodes)
    struct.pack_into("<II", out, 0x18, n, n | 0x80000000)
    struct.pack_into("<4f", out, 0x20, *domain[0], -DOMAIN_MARGIN)
    struct.pack_into("<4f", out, 0x30, *domain[1], DOMAIN_MARGIN)
    for x in nodes:
        out += struct.pack("<3BBH", *x)
    out += b"\x7f" * ((-len(out)) % 16)
    sec_new = len(out)
    out += template[sec_old:]
    return bytes(out), {0x10: 0x10, 0x48: 0x48, 0x60: 0x60, sec_old: sec_new}   # header slots + arrays


# ---------------------------------------------------------------- dynamic compound trees
def dyn_tree_refit(pf, comp_off: int, box_of) -> tuple[bytes | None, int, list[str]]:
    """Refit one hknpDynamicCompoundShape's hkcdDynamicTree. Returns (new data blob or None, data off, errs)."""
    data = pf.pointers.get(comp_off + 0xC0, 0)
    if not data or pf._starts.get(data) != "hknpDynamicCompoundShapeData":
        return None, 0, [f"compound @{comp_off:#x}: no dynamic tree"]
    d = jc3hkx.decode_compound(pf, comp_off, pf._starts[comp_off])
    blob = bytearray(pf.blob[pf.base + data:pf.base + data + pf.extents[data]])
    n = struct.unpack_from("<I", blob, 0x18)[0]
    root = struct.unpack_from("<I", blob, 0x30)[0]
    node = lambda i: 0x40 + 32 * i
    errs = []

    def fit(i) -> tuple[list, list]:
        c0, c1 = struct.unpack_from("<HH", blob, node(i) + 28)
        if c0 == 0:                       # leaf: c1 = instance index
            ins = d["instances"][c1]
            box = box_of(ins["shape"])
            if pf._starts.get(ins["shape"]) == jc3hkx.POLYTOPE:   # decoded: leaf = hull bounds +- convex_radius
                r = pf.f32(ins["shape"] + 0x14)
                box = {"min": [x - r for x in box["min"]], "max": [x + r for x in box["max"]]}
            w = jc3hkx.transform_aabb(box, ins["basis"], ins["translation"])
            lo, hi = list(w["min"]), list(w["max"])
        else:
            l0, h0 = fit(c0); l1, h1 = fit(c1)
            lo = [min(l0[k], l1[k]) for k in range(3)]; hi = [max(h0[k], h1[k]) for k in range(3)]
        struct.pack_into("<3f", blob, node(i), *lo)
        struct.pack_into("<3f", blob, node(i) + 16, *hi)
        return lo, hi
    if not (0 < root < n):
        return None, data, [f"compound @{comp_off:#x}: root {root}"]
    fit(root)
    return bytes(blob), data, errs


# ---------------------------------------------------------------- apply
def apply(phys: str, body_rbm: str) -> dict:
    pf = jc3hkx.Packfile(open(phys, "rb").read())
    parts: dict = {}
    body = [o.offset for o in pf.objects if o.cls == "hknpExternMeshShape"
            and jc3hkx.part_index_of(pf, o.offset, parts) == 0]
    if len(body) != 1:
        raise SystemExit(f"B-10b: {len(body)} extern mesh shapes on part 0, expected 1")
    shape = body[0]
    props, data = pf.pointers.get(shape + 0x20), pf.pointers.get(shape + 0x68)
    geoA, geoB = pf.pointers.get(props + 0x10), pf.pointers.get(props + 0x20)
    if {pf._starts.get(geoA), pf._starts.get(geoB)} != {"hkGeometry"} or pf._starts.get(data) != "hknpExternMeshShapeData":
        raise SystemExit("B-10b: body shape graph is not {props: 2 x hkGeometry, data}")
    selftest(pf, data, geoA, geoB)

    V, T, M = load_body(body_rbm)
    lo, hi = V.min(0).astype(np.float64), V.max(0).astype(np.float64)
    domain = ([float(lo[k] - DOMAIN_MARGIN) for k in range(3)], [float(hi[k] + DOMAIN_MARGIN) for k in range(3)])
    nodes = build_tree(V, T, domain)
    errs = check_tree(nodes, domain, V, T)
    if errs:
        raise SystemExit("B-10b tree: " + " | ".join(errs))

    blobA, mapA = geometry_blob(pf.blob[pf.base + geoA:pf.base + geoA + pf.extents[geoA]], V, T, M)
    blobB, mapB = geometry_blob(pf.blob[pf.base + geoB:pf.base + geoB + pf.extents[geoB]], V, T,
                                np.full(len(T), MAT_DEFORM, np.int32))
    blobD, mapD = data_blob(pf.blob[pf.base + data:pf.base + data + pf.extents[data]], nodes, domain)
    edits = {geoA: blobA, geoB: blobB, data: blobD}
    inner = {geoA: mapA, geoB: mapB, data: mapD}

    # compound boxes (+0x80) with the authored margin kept, then every dynamic tree refit
    new_box = {"min": domain[0], "max": domain[1]}
    cedits = jc3hkx.compound_aabb_edits(pf, {shape: (None, new_box)})
    edits.update(cedits)
    boxes: dict = {shape: new_box}
    for off, b in cedits.items():
        boxes[off] = {"min": list(struct.unpack_from("<3f", b, 0x80)), "max": list(struct.unpack_from("<3f", b, 0x90))}

    def box_of(s):
        return boxes.get(s) or jc3hkx.shape_aabb(pf, s)
    refit = []
    for o in pf.objects:
        if o.cls != "hknpDynamicCompoundShape":
            continue
        blob, doff, e = dyn_tree_refit(pf, o.offset, box_of)
        if e:
            raise SystemExit("B-10b refit: " + " | ".join(e))
        src = pf.blob[pf.base + doff:pf.base + doff + pf.extents[doff]]
        moved = float(np.abs(np.frombuffer(src[0x40:], np.float32) - np.frombuffer(blob[0x40:], np.float32)).max())
        if moved > 1e-5:   # below that it is float rounding of an unchanged tree: keep the authored bytes
            edits[doff] = blob
            refit.append({"compound": hex(o.offset), "max_move_m": round(moved, 4)})

    out, info = jc3hkx.packfile_bytes(pf, edits, inner)
    open(phys, "wb").write(out)

    # read back
    pf2 = jc3hkx.Packfile(out)
    s2 = next(o.offset for o in pf2.objects if o.cls == "hknpExternMeshShape"
              and jc3hkx.part_index_of(pf2, o.offset, {}) == 0)
    d2, g2 = pf2.pointers[s2 + 0x68], pf2.pointers[pf2.pointers[s2 + 0x20] + 0x10]
    gm = jc3hkx.geometry_mesh(pf2, next(o for o in pf2.objects if o.offset == g2))
    db = pf2.blob[pf2.base + d2:pf2.base + d2 + pf2.extents[d2]]
    n2 = struct.unpack_from("<I", db, 0x18)[0]
    nodes2 = [struct.unpack_from("<3BBH", db, 0x60 + 6 * i) for i in range(n2)]
    dom2 = (list(struct.unpack_from("<3f", db, 0x20)), list(struct.unpack_from("<3f", db, 0x30)))
    V2 = np.asarray(gm["vertices"], np.float32)[:, :3]
    e2 = check_tree(nodes2, dom2, V2, T)
    if gm["vertex_count"] != len(V) or gm["triangle_count"] != len(T) or not np.array_equal(V2, V) or e2:
        raise SystemExit(f"B-10b read-back: {e2}")
    _info, bad = jc3hkx.check_file(phys)
    if bad:
        raise SystemExit("B-10b check_file: " + " | ".join(bad[:6]))
    return {"card": "B-10b", "source": os.path.basename(body_rbm), "vertices": len(V), "triangles": len(T),
            "glass_triangles": int((M == MAT_GLASS).sum()), "tree_nodes": len(nodes),
            "domain": [[round(x, 4) for x in domain[0]], [round(x, 4) for x in domain[1]]],
            "compounds_reboxed": len(cedits), "dynamic_trees_refit": refit, "bytes": info["size"]}


def selftest(pf, data, geoA, geoB) -> None:
    """The decoded rules, re-proved on the input file before anything is written."""
    gA = jc3hkx.geometry_mesh(pf, next(o for o in pf.objects if o.offset == geoA))
    gB = jc3hkx.geometry_mesh(pf, next(o for o in pf.objects if o.offset == geoB))
    db = pf.blob[pf.base + data:pf.base + data + pf.extents[data]]
    n = struct.unpack_from("<I", db, 0x18)[0]
    nodes = [struct.unpack_from("<3BBH", db, 0x60 + 6 * i) for i in range(n)]
    dom = (list(struct.unpack_from("<3f", db, 0x20)), list(struct.unpack_from("<3f", db, 0x30)))
    want = ([min(gA["bounds"]["min"][k], gB["bounds"]["min"][k]) - DOMAIN_MARGIN for k in range(3)],
            [max(gA["bounds"]["max"][k], gB["bounds"]["max"][k]) + DOMAIN_MARGIN for k in range(3)])
    if any(abs(dom[j][k] - want[j][k]) > 1e-4 for j in range(2) for k in range(3)):
        raise SystemExit(f"B-10b selftest: domain rule fails on the input ({dom} vs {want})")
    gb = pf.blob[pf.base + geoA:pf.base + geoA + pf.extents[geoA]]
    T = np.array([struct.unpack_from("<4i", gb, 0x30 + 16 * gA["vertex_count"] + 16 * i)[:3]
                  for i in range(gA["triangle_count"])])
    V = np.asarray(gA["vertices"], np.float64)[:, :3]
    errs = check_tree(nodes, dom, V, T)
    if errs:
        raise SystemExit("B-10b selftest: the decoder does not reproduce the input tree: " + " | ".join(errs))
    # dynamic tree rule, proved on the untouched donor (nothing stale there): refit == stored, every node
    dpf = jc3hkx.Packfile(open(DONOR, "rb").read())
    worst = 0.0
    for o in dpf.objects:
        if o.cls != "hknpDynamicCompoundShape":
            continue
        blob, doff, e = dyn_tree_refit(dpf, o.offset, lambda s: jc3hkx.shape_aabb(dpf, s))
        if e:
            raise SystemExit("B-10b selftest refit: " + " | ".join(e))
        src = dpf.blob[dpf.base + doff:dpf.base + doff + dpf.extents[doff]]
        a = np.frombuffer(src[0x40:], np.float32)
        b = np.frombuffer(blob[0x40:], np.float32)
        worst = max(worst, float(np.abs(a - b).max()))
    if worst > 1e-5:
        raise SystemExit(f"B-10b selftest: dynamic tree refit differs from the donor by {worst} m")

if __name__ == "__main__":
    import json
    import shutil
    import tempfile
    src = sys.argv[1]
    rbm = sys.argv[2]
    tmp = os.path.join(tempfile.mkdtemp(), "out.physicsc")
    shutil.copy(src, tmp)
    print(json.dumps(apply(tmp, rbm), indent=1))
    print("written", tmp)
