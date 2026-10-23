"""psk2rbm.py - turn the Batmobile PSKX into a JC3 vehicle RBM in the DaBaby head's format.

Why this format
---------------
The Meme Vehicle Pack's DaBaby jeep (MODLOG §37) is the only shipped JC3 mod that gives a
vehicle new body geometry. Its `dababy_head.rbm` is ONE CarPaintMM block, flags 0x80 (no
deform bit), vb0 = float3 positions (stride 12), vb1 = u0,v0,u1,v1,normal,tangent
(stride 24), u16 indices. This writer clones that block (material params, texture list,
deform table and all) and replaces only the vertex/index buffers and the bbox, so the
output differs from a known-working file in geometry alone.

Normal packing (verified on vanilla plain blocks, MODLOG §39): with a,b,c the byte-quantised
components of (n+1)/2, the stored float is a/256 + b + 256*c; the reader recovers
x = fract(p), y = fract(p/256), z = fract(p/65536), each *2-1. The tangent is written as 0.0
exactly like the DaBaby head.

Pipeline
--------
  1. read PSKX chunks (PNTS0000, VTXW0000 with u32 point index, FACE3200, MATT0000)
  2. keep the chosen materials, map PSK (X len, Y width, Z up, cm) to JC3 (X width, Y up,
     -Z forward, m) and fit into a target box
  3. decimate in Blender (headless, collapse) to a triangle budget
  4. split vertices on UV seams, smooth normals, check the u16 index limit
  5. write the RBM from the template block; decode it again and verify

Usage:
  python psk2rbm.py <in.pskx> <template.rbm> -o out.rbm [--tris 20000] [--fit-to ref.rbm]
"""
import argparse
import os
import struct
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbm_geom as R  # noqa: E402

BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")

# Batmobile_V2 materials: exterior shell only. Wheels/tyres/discs are separate JC3 parts,
# the cockpit is never seen through a single-block body.
DEFAULT_KEEP = ("Mainbody", "WheelArchs", "Undercarriage", "Glass", "Emissive",
                "Body_Decals", "Upgrades", "Worn")


def read_pskx(path):
    b = open(path, "rb").read()
    o, ch = 0, {}
    while o + 32 <= len(b):
        cid = b[o:o + 20].split(b"\0")[0].decode("ascii", "replace")
        stride, count = struct.unpack_from("<II", b, o + 24)
        ch[cid] = (o + 32, stride, count)
        o += 32 + stride * count
    po, ps, pn = ch["PNTS0000"]
    P = np.frombuffer(b, "<f4", pn * 3, po).reshape(pn, 3).astype(np.float64)
    wo, ws, wn = ch["VTXW0000"]
    if ws != 16:
        raise SystemExit(f"VTXW stride {ws}, expected 16")
    W = np.frombuffer(b, np.dtype([("p", "<u4"), ("u", "<f4"), ("v", "<f4"), ("m", "u1"),
                                   ("r", "u1"), ("pad", "<u2")]), wn, wo)
    fo, fs, fnn = ch["FACE3200"]
    if fs != 18:
        raise SystemExit(f"FACE3200 stride {fs}, expected 18")
    F = np.frombuffer(b, np.dtype([("w", "<u4", 3), ("m", "u1"), ("a", "u1"), ("s", "<u4")]), fnn, fo)
    mo, ms, mn = ch["MATT0000"]
    mats = [b[mo + i * ms: mo + i * ms + 64].split(b"\0")[0].decode() for i in range(mn)]
    if W["p"].max() >= pn or F["w"].max() >= wn:
        raise SystemExit("index out of range: layout assumption wrong")
    return P, W, F, mats


def to_jc3(P):
    """PSK (X length, Y width, Z up) -> JC3 (X width, Y up, Z length, front at -Z).
    Proven by the axis grid render (rbm_geom._tumbler_cloud)."""
    T = P[:, [1, 2, 0]].copy()
    T[:, 2] *= -1.0
    return T


def fit_box(T, lo, hi, mode):
    """Uniform scale so the LENGTH matches the reference box, then centre X/Z and sit the
    bottom on the reference bottom. Uniform, so the Batmobile keeps its own proportions."""
    tlo, thi = T.min(0), T.max(0)
    s = (hi[2] - lo[2]) / (thi[2] - tlo[2])
    if mode == "fit":   # also never taller/wider than the reference box
        s = min(s, (hi[0] - lo[0]) / (thi[0] - tlo[0]) * 1.25)
    T = (T - [(tlo[0] + thi[0]) / 2, tlo[1], (tlo[2] + thi[2]) / 2]) * s
    return T + [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2], s


def write_obj(path, V, UV, tris):
    with open(path, "w") as fh:
        fh.write("".join("v %.6f %.6f %.6f\n" % tuple(v) for v in V))
        fh.write("".join("vt %.6f %.6f\n" % tuple(t) for t in UV))
        fh.write("".join("f %d/%d %d/%d %d/%d\n" % (a + 1, a + 1, b + 1, b + 1, c + 1, c + 1)
                         for a, b, c in tris))


BLENDER_SCRIPT = r"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
src, dst, target = a[0], a[1], int(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src, forward_axis='NEGATIVE_Z', up_axis='Y')
ob = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = ob
n = len(ob.data.polygons)
if target < n:
    m = ob.modifiers.new("dec", "DECIMATE")
    m.ratio = target / n
    m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)
m = ob.modifiers.new("tri", "TRIANGULATE")
bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.wm.obj_export(filepath=dst, export_selected_objects=True, export_uv=True,
                      export_normals=False, export_materials=False,
                      forward_axis='NEGATIVE_Z', up_axis='Y', apply_modifiers=True)
print("DECIMATED", n, "->", len(ob.data.polygons))
"""


def blender_decimate(obj_in, obj_out, target):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(BLENDER_SCRIPT)
        script = fh.name
    try:
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", script, "--",
                            obj_in, obj_out, str(target)], capture_output=True, text=True)
    finally:
        os.unlink(script)
    line = [l for l in r.stdout.splitlines() if l.startswith("DECIMATED")]
    if r.returncode != 0 or not line or not os.path.exists(obj_out):
        raise SystemExit("blender failed:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    print("  blender:", line[0])


def read_obj(path):
    """Flatten OBJ v/vt corners into unique (position, uv) vertices."""
    V, T, corners = [], [], []
    for line in open(path):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("vt "):
            T.append([float(x) for x in line.split()[1:3]])
        elif line.startswith("f "):
            c = [tuple(int(i) - 1 for i in tok.split("/")[:2]) for tok in line.split()[1:]]
            for k in range(1, len(c) - 1):
                corners.append((c[0], c[k], c[k + 1]))
    V, T = np.array(V), np.array(T)
    key, idx = {}, []
    for tri in corners:
        out = []
        for vi, ti in tri:
            out.append(key.setdefault((vi, ti), len(key)))
        idx.append(out)
    pairs = np.array(list(key.keys()))
    return V[pairs[:, 0]], T[pairs[:, 1]], np.array(idx, dtype=np.int64), pairs[:, 0]


def smooth_normals(V, I, pos_id):
    """Area-weighted, shared across UV seams (accumulated per POSITION, not per split vertex)."""
    fn = np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]])
    acc = np.zeros((pos_id.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, pos_id[I[:, k]], fn)
    n = acc[pos_id]
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


def pack_normals(N):
    q = np.clip(np.round((N + 1.0) * 0.5 * 255.0), 0, 255)
    return (q[:, 0] / 256.0 + q[:, 1] + 256.0 * q[:, 2]).astype(np.float32)


def unpack_normals(p):
    p = p.astype(np.float64)
    v = np.stack([p, p / 256.0, p / 65536.0], 1)
    return (v - np.floor(v)) * 2.0 - 1.0


def build_rbm(template_path, V, UV, I, N):
    m = R.decode(open(template_path, "rb").read())
    if len(m.blocks) != 1 or type(m.blocks[0]).__name__ != "CarPaintMM":
        raise SystemExit("template must be a single-CarPaintMM RBM (the DaBaby head)")
    b = m.blocks[0]
    if b.vb0.stride != 12 or b.vb1.stride != 24 or b.ib.stride != 2:
        raise SystemExit("template is not the plain 12/24/u16 layout")
    n = len(V)
    vb1 = np.zeros((n, 6), np.float32)
    vb1[:, 0:2] = UV
    vb1[:, 2:4] = UV           # the DaBaby head carries uv1 = 0; a copy is harmless and lightmap-safe
    vb1[:, 4] = pack_normals(N)
    b.vb0 = R.VertexBuffer(12, n, V.astype("<f4").tobytes())
    b.vb1 = R.VertexBuffer(24, n, vb1.astype("<f4").tobytes())
    b.ib = R.VertexBuffer(2, I.size, I.astype("<u2").tobytes())
    m.bbox_min = tuple(float(x) for x in V.min(0))
    m.bbox_max = tuple(float(x) for x in V.max(0))
    return m


DEFORM_VB0 = np.dtype([("p", "<f4", 3), ("d", "<f4"), ("w", "<i2", 4)])


def build_rbm_deform(template_path, block, V, UV, I, N):
    """Write the mesh as ONE block cloned from a vanilla DEFORM CarPaintMM block (MODLOG §51).

    test-037 proved the Serpente's body slot draws its own deform blocks; the DaBaby-format
    plain block (034-036) is never drawn there. Measured layout of a deform block:
      vb0 stride 24: x, y, z, d (packed small vector), w[4] int16 = (weight lo byte,
                     deform-table index hi byte); weights sum to ~255
      vb1 stride 32: u0, v0, u1, v1, normal (packed), tangent (signed packing),
                     damaged normal (packed), damaged tangent
    d, w, u1/v1 and both tangents are copied from the NEAREST vertex of the template block,
    so a crash dents the mesh like the vanilla body there and every w index stays valid for
    the template's own deform_table, which is kept. Both normals are ours."""
    m = R.decode(open(template_path, "rb").read())
    src = m.blocks[block]
    if type(src).__name__ != "CarPaintMM" or src.vb0.stride != 24 or src.vb1.stride != 32:
        raise SystemExit(f"template block {block} is not a deform CarPaintMM (24/32)")
    if src.flags & (0x20 | 0x40 | 0x2000):
        raise SystemExit("template block carries layered/overlay/skinned buffers: not handled")
    A = np.frombuffer(src.vb0.data, DEFORM_VB0)
    B = np.frombuffer(src.vb1.data, "<f4").reshape(-1, 8)
    P = A["p"].astype(np.float64)
    near = np.empty(len(V), np.int64)
    for i in range(0, len(V), 4096):
        d2 = ((V[i:i + 4096, None, :] - P[None, :, :]) ** 2).sum(-1)
        near[i:i + 4096] = d2.argmin(1)
    n = len(V)
    vb0 = np.zeros(n, DEFORM_VB0)
    vb0["p"] = V
    vb0["d"] = A["d"][near]
    vb0["w"] = A["w"][near]
    vb1 = np.zeros((n, 8), np.float32)
    vb1[:, 0:2] = UV
    vb1[:, 2:4] = B[near, 2:4]
    vb1[:, 4] = pack_normals(N)
    vb1[:, 5] = B[near, 5]
    vb1[:, 6] = pack_normals(N)
    vb1[:, 7] = B[near, 7]
    src.vb0 = R.VertexBuffer(24, n, vb0.tobytes())
    src.vb1 = R.VertexBuffer(32, n, vb1.astype("<f4").tobytes())
    src.ib = R.VertexBuffer(2, I.size, I.astype("<u2").tobytes())
    m.blocks = [src]
    m.number_of_blocks = 1
    m.bbox_min = tuple(float(x) for x in V.min(0))
    m.bbox_max = tuple(float(x) for x in V.max(0))
    return m


def build_rbm_plain(template_path, block, V, UV, I, N):
    """ONE NON-deform block cloned from template block N with IS_DEFORM (0x1000) cleared.

    User rule (MODLOG §52): the Arkham Knight Batmobile does not deform, so neither does ours.
    Cloning the Serpente's paint block (0x101F) keeps its material, textures and palette
    behaviour; clearing the deform bit gives 0x001F, a flag set vanilla already uses on plain
    blocks. Plain layout = the DaBaby head's: vb0 float3 (12), vb1 u0,v0,u1,v1,normal,tangent
    (24). u1/v1 and the tangent are copied from the nearest template vertex."""
    m = R.decode(open(template_path, "rb").read())
    src = m.blocks[block]
    if type(src).__name__ != "CarPaintMM" or src.vb0.stride != 24 or src.vb1.stride != 32:
        raise SystemExit(f"template block {block} is not a deform CarPaintMM (24/32)")
    if src.flags & (0x20 | 0x40 | 0x2000):
        raise SystemExit("template block carries layered/overlay/skinned buffers: not handled")
    P = np.frombuffer(src.vb0.data, DEFORM_VB0)["p"].astype(np.float64)
    B = np.frombuffer(src.vb1.data, "<f4").reshape(-1, 8)
    near = np.empty(len(V), np.int64)
    for i in range(0, len(V), 4096):
        near[i:i + 4096] = ((V[i:i + 4096, None, :] - P[None, :, :]) ** 2).sum(-1).argmin(1)
    n = len(V)
    vb1 = np.zeros((n, 6), np.float32)
    vb1[:, 0:2] = UV
    vb1[:, 2:4] = B[near, 2:4]
    vb1[:, 4] = pack_normals(N)
    vb1[:, 5] = B[near, 5]
    src.flags &= ~0x1000
    src.vb0 = R.VertexBuffer(12, n, V.astype("<f4").tobytes())
    src.vb1 = R.VertexBuffer(24, n, vb1.astype("<f4").tobytes())
    src.ib = R.VertexBuffer(2, I.size, I.astype("<u2").tobytes())
    m.blocks = [src]
    m.number_of_blocks = 1
    m.bbox_min = tuple(float(x) for x in V.min(0))
    m.bbox_max = tuple(float(x) for x in V.max(0))
    return m


def verify(raw, V, I, N):
    m = R.decode(raw)
    if m.write() != raw:
        return "re-encode is not byte-identical"
    b = m.blocks[0]
    if b.vb0.count != len(V) or b.vb1.count != len(V) or b.ib.count != I.size:
        return "counts do not match"
    got = np.array(b.indices())
    if got.max() >= len(V) or not np.array_equal(got, I.ravel()):
        return "index buffer mismatch"
    back = unpack_normals(np.frombuffer(b.vb1.data, "<f4").reshape(-1, b.vb1.stride // 4)[:, 4])
    d = (back * N).sum(1)
    if d.mean() < 0.98:
        return f"normal round trip poor (mean dot {d.mean():.3f})"
    pos = (np.frombuffer(b.vb0.data, DEFORM_VB0)["p"] if b.vb0.stride == 24
           else np.frombuffer(b.vb0.data, "<f4").reshape(-1, 3))
    if not np.isfinite(pos).all() or not np.allclose(pos, V, atol=1e-5):
        return "positions not written as given"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pskx")
    ap.add_argument("template", help="dababy_head.rbm (format template)")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--tris", type=int, default=20000, help="triangle budget after decimation")
    ap.add_argument("--fit-to", help="RBM whose bbox the result is fitted into (default: template)")
    ap.add_argument("--keep", default=",".join(DEFAULT_KEEP),
                    help="comma list of material-name substrings to keep")
    ap.add_argument("--obj", help="also save the decimated OBJ here")
    ap.add_argument("--deform-block", type=int,
                    help="write a DEFORM block cloned from this block of the template "
                         "(e.g. sportsmuscle_body_lod1.rbm block 6) instead of the plain format")
    ap.add_argument("--plain", action="store_true",
                    help="with --deform-block: clone that block but write it NON-deform (bit 0x1000 cleared)")
    ap.add_argument("--max-verts", type=int, default=0,
                    help="keep only the largest triangles within this vertex budget (size tests)")
    ap.add_argument("--weld", action="store_true",
                    help="merge vertices across UV seams (vertex-count tests; tears the texture)")
    ap.add_argument("--wheels", action="store_true",
                    help="allow the wheel/tyre/disc materials normally excluded from --keep "
                         "(test-046: Batmobile wheels; use with a single-wheel pskx from "
                         "_extract_wheel.py, since --keep otherwise merges all four corners)")
    a = ap.parse_args()

    P, W, F, mats = read_pskx(a.pskx)
    keep = [s for s in a.keep.split(",") if s]
    km = [i for i, nm in enumerate(mats) if any(k in nm for k in keep)
          and (a.wheels or not any(x in nm for x in ("Wheel_V2", "Tyre", "Discbreak", "Cockpit")))]
    print("materials kept:", ", ".join(mats[i] for i in km))
    sel = np.isin(F["m"], km)
    tris_w = F["w"][sel].astype(np.int64)
    print(f"  faces {sel.sum()} of {len(F)}")

    used = np.unique(tris_w)
    remap = np.full(len(W), -1, np.int64)
    remap[used] = np.arange(len(used))
    Vw = to_jc3(P[W["p"][used]])
    UVw = np.stack([W["u"][used], 1.0 - W["v"][used]], 1)   # OBJ convention; flipped back below

    ref = R.decode(open(a.fit_to or a.template, "rb").read())
    Vw, s = fit_box(Vw, np.array(ref.bbox_min), np.array(ref.bbox_max), "length")
    print(f"  scale {s:.5f} (PSK cm -> m and fitted to the reference length)")

    with tempfile.TemporaryDirectory() as td:
        src, dst = os.path.join(td, "in.obj"), os.path.join(td, "out.obj")
        write_obj(src, Vw, UVw, remap[tris_w])
        blender_decimate(src, dst, a.tris)
        if a.obj:
            import shutil
            shutil.copy(dst, a.obj)
        V, UV, I, pos_id = read_obj(dst)
    UV[:, 1] = 1.0 - UV[:, 1]
    if a.weld:
        # one vertex per POSITION (first UV wins): no seam splits, far fewer vertices.
        # For size/visibility tests only -- the texture mapping tears along seams.
        uniq, first, inv = np.unique(pos_id, return_index=True, return_inverse=True)
        V, UV, I, pos_id = V[first], UV[first], inv[I], np.arange(len(uniq))
    if len(V) > 65535:
        raise SystemExit(f"{len(V)} vertices exceeds the u16 index limit: lower --tris")
    N = smooth_normals(V, I, pos_id)
    if a.max_verts and len(V) > a.max_verts:
        # keep the LARGEST triangles until the vertex budget is spent (the big body panels);
        # a vertex-count test, not a shippable mesh
        area = np.linalg.norm(np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]), axis=1)
        used, keep = set(), []
        for t in np.argsort(-area):
            new = set(I[t]) - used
            if len(used) + len(new) > a.max_verts:
                continue
            used |= new
            keep.append(t)
        idx = np.array(sorted(used))
        remap = np.full(len(V), -1, np.int64)
        remap[idx] = np.arange(len(idx))
        V, UV, N, I = V[idx], UV[idx], N[idx], remap[I[np.array(keep)]]
        print(f"  --max-verts: kept {len(I)} largest tris on {len(V)} verts")

    if a.deform_block is not None and a.plain:
        m = build_rbm_plain(a.template, a.deform_block, V, UV, I, N)
    elif a.deform_block is not None:
        m = build_rbm_deform(a.template, a.deform_block, V, UV, I, N)
    else:
        m = build_rbm(a.template, V, UV, I, N)
    raw = m.write()
    err = verify(raw, V, I, N)
    if err:
        raise SystemExit("VERIFY FAILED: " + err)
    open(a.output, "wb").write(raw)
    lo, hi = V.min(0), V.max(0)
    print(f"wrote {a.output}: {len(raw)} B, {len(V)} verts, {len(I)} tris, "
          f"bbox {hi[0]-lo[0]:.3f} x {hi[1]-lo[1]:.3f} x {hi[2]-lo[2]:.3f} m  VERIFY PASS")


if __name__ == "__main__":
    main()
