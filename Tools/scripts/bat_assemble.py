"""bat_assemble.py - every Batmobile asset through ONE transform, at TRUE scale. MODLOG §70.

The user's rule: grab every asset all at once, fully aligned to the body and scaled. Earlier
builds fitted the body (to 5.0 m) and the wheels (to the Serpente's Ø0.80) SEPARATELY and then
moved the physics stations to suit -- the visual/physics split behind the 047 jitter.

Here there is exactly one transform T for every asset:
    T(p) = to_jc3(p) * scale + offset          scale = 0.01: the PSKX is already in real cm
                                                (tyre Ø ≈ 1.42 m vs the 1.40 m reference)
    offset: track centred on X = 0, tyres' lowest point on the JC3 ground (`--ground`),
            wheelbase midpoint on the Serpente's (`--center-z`), so the car stays centred
            where the vanilla physics expects it.

Outputs (in --out):
    body_lod1..5.rbm        all non-wheel materials (turret, cockpit, glass, arches...) as one
                            PLAIN block cloned from the Serpente paint block (no deform: user rule)
    wheel_<c>_lodN.rbm      each corner's OWN wheel/tyre/disc geometry (front and rear differ),
                            local to its physics hardpoint. JC3 draws a wheel at its hardpoint and
                            spins it about the axle (X), so the true lateral position is kept as a
                            pure X offset in the mesh: an axle shift, which spin cannot wobble.
                            Y and Z must be ZERO offsets: the physics stations move there instead.
    stations.json           per corner: true hub (x,y,z), physics hardpoint (±hardpoint_x, y, z),
                            tyre radius -- the numbers the physics patch consumes.

Side convention (from vanilla wheel meshes, dense rim side = outward): left = -X. The PSK->JC3
axis map is a reflection (Unreal is left-handed), so PSK Y<0 = left = JC3 X<0.
"""
import argparse
import glob
import importlib.util
import json
import os
import re
import shutil
import struct
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psk2rbm as P  # noqa: E402
import pskx_parts as PX  # noqa: E402
import rbm_geom as R  # noqa: E402
import tex2ddsc as TX  # noqa: E402
import eetoc as TOC  # noqa: E402
import factors as FX  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "texmatch", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_texmatch.py"))
TM = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(TM)

CORNERS = ("f_l", "f_r", "r_l", "r_r")


def to_jc3_rot(Pp):
    """PSK (X length prow+, Y width, Z up) -> JC3 (X width, Y up, Z length, front -Z) as a PROPER
    rotation (det +1): (-y, z, -x). The old to_jc3 (y, z, -x) is a reflection; the rig's own
    Left/Right bone labels show it mirrored the car (MODLOG §73)."""
    return np.stack([-Pp[:, 1], Pp[:, 2], -Pp[:, 0]], 1)


def mesh_chain(V0, UV0, tris, budgets, build, label, out_dir, name):
    """Decimate one transformed mesh to each budget, write via `build`, verify. Returns stats."""
    used = np.unique(tris)
    remap = np.full(int(tris.max()) + 1, -1, np.int64)
    remap[used] = np.arange(len(used))
    V, UV, T = V0[used], UV0[used], remap[tris]
    stats = []
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.obj")
        P.write_obj(src, V, np.stack([UV[:, 0], 1.0 - UV[:, 1]], 1), T)
        for i, budget in enumerate(budgets, 1):
            dst = os.path.join(td, f"out{i}.obj")
            P.blender_decimate(src, dst, budget)
            v, uv, I, pos_id = P.read_obj(dst)
            uv[:, 1] = 1.0 - uv[:, 1]
            if len(v) > 65535:
                raise SystemExit(f"{name} lod{i}: {len(v)} verts exceeds u16")
            N = P.smooth_normals(v, I, pos_id)
            raw = build(v, uv, I, N).write()
            err = P.verify(raw, v, I, N)
            if err:
                raise SystemExit(f"{name} lod{i} VERIFY FAILED: {err}")
            path = os.path.join(out_dir, f"{name}_lod{i}.rbm")
            open(path, "wb").write(raw)
            lo, hi = v.min(0), v.max(0)
            stats.append((i, len(v), len(I), tuple(np.round(hi - lo, 3))))
            print(f"  {label} lod{i}: {len(I):6d} tris {len(v):6d} verts  "
                  f"{hi[0]-lo[0]:.3f} x {hi[1]-lo[1]:.3f} x {hi[2]-lo[2]:.3f} m  VERIFY PASS")
    return stats


def decimated_lods(V0, UV0, tris, budgets):
    """[(v, uv, I, N)] per budget for one sub-mesh (Blender collapse, UV-seam split, smooth normals)."""
    used = np.unique(tris)
    remap = np.full(int(tris.max()) + 1, -1, np.int64)
    remap[used] = np.arange(len(used))
    V, UV, T = V0[used], UV0[used], remap[tris]
    out = []
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.obj")
        P.write_obj(src, V, np.stack([UV[:, 0], 1.0 - UV[:, 1]], 1), T)
        for i, budget in enumerate(budgets, 1):
            dst = os.path.join(td, f"out{i}.obj")
            target, corrected = budget, 0
            for _ in range(6):          # BUD-1: hit the budget, do not overshoot it
                P.blender_decimate(src, dst, target)
                v, uv, I, pos_id = P.read_obj(dst)
                if len(I) <= budget:
                    break
                # Blender's collapse leaves n-gons at aggressive ratios, and the triangulate step
                # then emits MORE triangles than the ratio asked for: the shipped lod5 carried
                # 1,592 tris against an 800 budget (+99%), lod4 1,827 vs 1,500 (+22%). Feed the
                # overshoot back in until the triangulated result fits (MODLOG #111).
                corrected = len(I)
                target = max(1, int(target * budget / len(I) * 0.95))
            else:
                # some pieces are boundary-limited: the outline alone needs more triangles than
                # the budget allows, and no collapse can go below it (this is why the shipped
                # lod4/lod5 overshot). Keep the smallest achievable and let the model-budget
                # guard at the end account for the bytes.
                print(f"    lod{i}: boundary-limited, kept {len(I)} tris (budget {budget})")
            if corrected:
                print(f"    overshoot corrected: {corrected} -> {len(I)} tris (budget {budget})")
            uv[:, 1] = 1.0 - uv[:, 1]
            if len(v) > 65535:
                raise SystemExit(f"lod{i}: {len(v)} verts exceeds u16")
            N = P.smooth_normals(v, I, pos_id)
            # a vertex used only by zero-area (decimated-flat) triangles gets a ZERO normal, which
            # cannot round-trip through the packing; those triangles are invisible, so any unit
            # normal is correct -- use up
            z = np.linalg.norm(N, axis=1) < 0.5
            N[z] = (0.0, 1.0, 0.0)
            out.append((v, uv, I, N))
    return out


def build_window_block(template_rbm, V, UV, I, N):
    """A JC3 Window block (glass) cloned from a vanilla window RBM; only geometry replaced.

    Measured layout (MODLOG §74), 40 B per vertex: x, y, z | u, v | 0, 0 | packed normal (col 7: dot
    +1.000 vs geometry) | tangent | a constant packed ~(1,1,1) tint. Indices u16. Tangent and tint are
    copied from the template's first vertex (its normal map is a dummy, so the tangent is unused)."""
    m = R.decode(open(template_rbm, "rb").read())
    src = [b for b in m.blocks if R.BLOCK_NAMES.get(b.type_hash) == "Window"][0]
    if src.strides != (40, 2):
        raise SystemExit(f"window template strides {src.strides}, expected (40, 2)")
    T = np.frombuffer(src.buffers[0].data, "<f4").reshape(-1, 10)
    A = np.zeros((len(V), 10), np.float32)
    A[:, 0:3] = V
    A[:, 3:5] = UV
    A[:, 7] = P.pack_normals(N)
    A[:, 8] = T[0, 8]
    A[:, 9] = T[0, 9]
    src.buffers = [R.VertexBuffer(40, len(V), A.tobytes()),
                   R.VertexBuffer(2, I.size, I.astype("<u2").tobytes())]
    return src


def verify_blocks(raw, parts):
    """every block: byte-identical re-encode, counts, indices, positions, normal round trip."""
    m = R.decode(raw)
    if m.write() != raw:
        return "re-encode is not byte-identical"
    if len(m.blocks) != len(parts):
        return f"{len(m.blocks)} blocks, expected {len(parts)}"
    for k, (blk, (v, I, N, ncol, stride)) in enumerate(zip(m.blocks, parts)):
        got = np.array(blk.indices()) if hasattr(blk, "indices") else \
            np.frombuffer(blk.ib.data, "<u2").astype(np.int64)
        if not np.array_equal(got, I.ravel()):
            return f"block {k}: index buffer mismatch"
        A = np.frombuffer(blk.vb0.data if stride == 40 else blk.vb1.data, "<f4").reshape(-1, stride // 4)
        pos = np.frombuffer(blk.vb0.data, "<f4").reshape(-1, blk.vb0.stride // 4)[:, :3]
        if len(pos) != len(v) or not np.allclose(pos, v, atol=1e-5):
            return f"block {k}: positions"
        d = (P.unpack_normals(A[:, ncol]) * N).sum(1)
        if d.mean() < 0.98:
            return f"block {k}: normal round trip {d.mean():.3f}"
    return None


def body_chain(Vw, UVw, groups, budgets, a, out_dir):
    """Body LODs with one block per KIND: 'paint' -> plain CarPaintMM, 'glass' -> Window.
    Each kind is decimated separately; a LOD's budget is split by face share (floors: 100, 5%)."""
    total = sum(len(t) for t in groups.values())
    # face share, floored at 5% of the LOD budget (capped at the source faces) so a small but very
    # visible kind -- the curved canopy glass -- is not reduced to a few hundred facets
    share = lambda t, b: max(100, int(b * len(t) / total), min(len(t), int(0.05 * b)))
    lods = {k: decimated_lods(Vw, UVw, t, [share(t, b) for b in budgets]) for k, t in groups.items()}
    for i in range(len(budgets)):
        v, uv, I, N = lods["paint"][i]
        m = P.build_rbm_plain(a.body_template, a.body_block, v, uv, I, N)
        parts = [(v, I, N, 4, 24)]
        allv = [v]
        if "glass" in lods:
            gv, guv, gI, gN = lods["glass"][i]
            m.blocks.append(build_window_block(a.window_template, gv, guv, gI, gN))
            parts.append((gv, gI, gN, 7, 40))
            allv.append(gv)
        m.number_of_blocks = len(m.blocks)
        allv = np.concatenate(allv)
        m.bbox_min = tuple(float(x) for x in allv.min(0))
        m.bbox_max = tuple(float(x) for x in allv.max(0))
        raw = m.write()
        err = verify_blocks(raw, parts)
        if err:
            raise SystemExit(f"body lod{i + 1} VERIFY FAILED: {err}")
        open(os.path.join(out_dir, f"body_lod{i + 1}.rbm"), "wb").write(raw)
        lo, hi = allv.min(0), allv.max(0)
        print(f"  body lod{i + 1}: " + " + ".join(f"{k} {len(lods[k][i][2])} tris" for k in lods)
              + f"  {hi[0]-lo[0]:.3f} x {hi[1]-lo[1]:.3f} x {hi[2]-lo[2]:.3f} m  VERIFY PASS ({len(m.blocks)} blocks)")


def tex_bytes(dims, cap, kind):
    """exact .ddsc payload for a texture scaled to `cap` (as tex2ddsc.mip_chain does) + header"""
    w, h = dims
    s = min(1.0, cap / max(w, h))
    w, h = max(4, int(w * s)), max(4, int(h * s))
    per = 8 if kind == "colour" else 16
    total = 0
    while True:
        total += ((w + 3) // 4) * ((h + 3) // 4) * per
        if w == 1 and h == 1:
            break
        w, h = max(1, w // 2), max(1, h // 2)
    return total + 148


def texture_budget_kb(budget_xml, vehicle_class, vanilla_toc, safety=0.9):
    """the game's own cap: vanilla asset_memory_budgets <class> Texture HARD value (the one Luke JC
    raised to stop "disappearing parts"), minus the vanilla entity's resident .ddsc footprint
    (conservative: assume all of it still loads), times a safety factor."""
    import xml.etree.ElementTree as ET
    hard = None
    for o in ET.parse(budget_xml).getroot().iter("object"):
        if [v.text for v in o.findall("value") if v.get("id") == "BACF1B49"] == [vehicle_class]:
            for c in o.findall("object"):
                if c.get("name") == "Texture":
                    hard = max(int(v.text) for v in c.findall("value"))
    if hard is None:
        raise SystemExit(f"no Texture budget for {vehicle_class} in {budget_xml}")
    resident = sum(s for n, o, s in TOC.read_toc(open(vanilla_toc, "rb").read()) if o and n.endswith(".ddsc")) / 1024
    kb = (hard - resident) * safety
    print(f"texture budget: {vehicle_class} hard {hard} KB - vanilla resident {resident:.0f} KB, x{safety} = {kb:.0f} KB")
    return kb


def allocate_caps(needs, budget_kb, tex_max):
    """needs: {tex: [path, kind, area_m2]}. Halve, one step at a time, the texture with the most bytes
    per m² of surface it covers until the set fits: big visible surfaces keep resolution."""
    from PIL import Image
    dims = {t: Image.open(p).size for t, (p, k, a) in needs.items()}
    cap = {t: min(tex_max, max(dims[t])) for t in needs}
    size = lambda t: tex_bytes(dims[t], cap[t], needs[t][1])
    while sum(size(t) for t in needs) / 1024 > budget_kb:
        cand = [t for t in needs if cap[t] > 64]
        if not cand:
            raise SystemExit("textures cannot fit the budget even at 64 px")
        t = max(cand, key=lambda t: size(t) / max(needs[t][2], 1e-6))
        cap[t] //= 2
    total = sum(size(t) for t in needs) / 1024
    print(f"texture caps fit {total:.0f} KB <= {budget_kb:.0f} KB:")
    for t in sorted(needs, key=lambda t: -needs[t][2]):
        print(f"    {cap[t]:5d} px  {size(t) / 1024:7.0f} KB  {needs[t][2]:7.2f} m²  {needs[t][1]:6s} {t}")
    return cap


def budget_value(budget_xml, vehicle_class, kind):
    """HARD (second) value in KB of <kind> (Model/Texture/...) for a class in the vanilla budgets"""
    import xml.etree.ElementTree as ET
    for o in ET.parse(budget_xml).getroot().iter("object"):
        if [v.text for v in o.findall("value") if v.get("id") == "BACF1B49"] == [vehicle_class]:
            for c in o.findall("object"):
                if c.get("name") == kind:
                    return max(int(v.text) for v in c.findall("value"))
    raise SystemExit(f"no {kind} budget for {vehicle_class}")


def repaint(vmodc, xml_path, out, fin):
    """every palette Tint -> fin (rgb, gloss, metallic, coat); in place at ConvertAdf offset-in-file,
    old values asserted, same size (palette_black.py's method, §55)"""
    import xml.etree.ElementTree as ET
    b = bytearray(open(vmodc, "rb").read())
    n = 0
    for t in ET.parse(xml_path).getroot().iter("member"):
        if t.get("type") != "Tint":
            continue
        n += 1
        for m in t.iter("member"):
            off = m.get("offset-in-file")
            if off is None or m.get("type") != "float":
                continue
            key = {"R": "rgb", "G": "rgb", "B": "rgb", "specular_gloss": "gloss",
                   "metallic": "metallic", "clear_coat": "coat"}.get(m.get("name"))
            if key is None:
                continue
            off = int(off, 16)
            if abs(struct.unpack_from("<f", b, off)[0] - float(m.text)) > 1e-5:
                raise SystemExit(f"palette @{off:#x} does not match {xml_path}")
            struct.pack_into("<f", b, off, fin[key])
    if n == 0:
        raise SystemExit("no Tint records in the palette")
    open(out, "wb").write(bytes(b))
    print(f"palette: {n} tints repainted -> {out}")


def part_chain(V0, UV0, groups, budgets, container_template, out_dir, name):
    """One RBM per LOD holding ONE BLOCK PER MATERIAL. groups: [(label, tris, make, is_glass)];
    make(v, uv, I, N) -> (block, normal_col, stride). Each material is decimated separately; a LOD's
    budget is split by face share (min 20 faces, glass floored at 5% so the canopy stays smooth)."""
    total = sum(len(t) for _, t, _, _ in groups)
    def share(t, b, glass):
        s = max(min(len(t), 20), int(b * len(t) / total))
        return max(s, min(len(t), int(0.05 * b))) if glass else s
    lods = [decimated_lods(V0, UV0, t, [share(t, b, g) for b in budgets]) for _, t, _, g in groups]
    for i in range(len(budgets)):
        m = R.decode(open(container_template, "rb").read())
        m.blocks, parts, allv = [], [], []
        for (label, _, make, _), L in zip(groups, lods):
            v, uv, I, N = L[i]
            blk, ncol, stride = make(v, uv, I, N)
            m.blocks.append(blk)
            parts.append((v, I, N, ncol, stride))
            allv.append(v)
        m.number_of_blocks = len(m.blocks)
        allv = np.concatenate(allv)
        m.bbox_min = tuple(float(x) for x in allv.min(0))
        m.bbox_max = tuple(float(x) for x in allv.max(0))
        raw = m.write()
        err = verify_blocks(raw, parts)
        if err:
            raise SystemExit(f"{name} lod{i + 1} VERIFY FAILED: {err}")
        open(os.path.join(out_dir, f"{name}_lod{i + 1}.rbm"), "wb").write(raw)
        lo, hi = allv.min(0), allv.max(0)
        print(f"  {name} lod{i + 1}: {len(m.blocks)} blocks, {sum(len(p[1]) for p in parts)} tris  "
              f"{hi[0]-lo[0]:.3f} x {hi[1]-lo[1]:.3f} x {hi[2]-lo[2]:.3f} m  VERIFY PASS")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pskx")
    ap.add_argument("--body-template", required=True, help="sportsmuscle_body_lod1.rbm")
    ap.add_argument("--body-block", type=int, default=6, help="paint block to clone (written plain)")
    ap.add_argument("--wheel-template", required=True, help="sportsmuscle_wheel_f_l_lod1.rbm (1 plain block)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=float, default=0.01, help="PSK units -> m (cm: 0.01 = true scale)")
    ap.add_argument("--ground", type=float, default=0.02,
                    help="JC3 Y of the tyre contact (vanilla: hub 0.40 - radius 0.38)")
    ap.add_argument("--center-z", type=float, default=-0.0555,
                    help="JC3 Z of the wheelbase midpoint (vanilla: (-1.557 + 1.446) / 2)")
    ap.add_argument("--hardpoint-x", default="true",
                    help="physics |X| per wheel: 'true' = each hub's own X (axle shift 0, physics moves "
                         "with the asset); a number = keep that track and shift the meshes along the axle")
    ap.add_argument("--body-tris", default="43000,6000,3000,1500,800")
    ap.add_argument("--wheel-tris", default="2500,1000,400,200,100")
    ap.add_argument("--land-xml", required=True,
                    help="ConvertAdf export of the live land_global: number_of_wheels comes from the game")
    ap.add_argument("--colour-block", type=int, default=3,
                    help="block of --body-template cloned for materials WITH a colour map (interior-style: no paint mask)")
    ap.add_argument("--tex-max", type=int, default=1024, help="texture size cap")
    ap.add_argument("--budget-xml", required=True,
                    help="ConvertProperty export of the VANILLA settings/asset_memory_budgets.bin")
    ap.add_argument("--vehicle-class", default="Vehicle-*HD*")
    ap.add_argument("--vanilla-toc", required=True, help="the vanilla .ee.toc (resident texture footprint)")
    ap.add_argument("--budget-safety", type=float, default=1.0,
                    help="model cap as a fraction of the game's Model HARD budget: 1.0 = the hard "
                         "cap itself (BUD-1, standing), 0.9 = the old guard")
    ap.add_argument("--palette", help="the vehicle palette .vmodc to repaint from the paint material's scalars")
    ap.add_argument("--palette-xml", help="its ConvertAdf export (offsets)")
    ap.add_argument("--window-template", required=True,
                    help="a vanilla RBM with a Window block (sportsmuscle_door_f_l_window_lod1.rbm)")
    ap.add_argument("--src-dir", required=True, help="asset folder with .props.txt dumps and .tga textures")
    ap.add_argument("--dry-run", action="store_true", help="stations + transform only, no meshes")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    # ---- read once: geometry, skeleton, material->texture bindings
    Pp, W, F, mats = P.read_pskx(a.pskx)
    bones, Wt = PX.skeleton(a.pskx)
    fb = PX.face_bones(Pp, W, F, Wt, len(bones))
    nwheels = int(re.search(r'name="number_of_wheels"[^>]*offset-in-file[^>]*>(\d+)<',
                            open(a.land_xml, encoding="utf-8-sig").read()).group(1))

    # ---- the ONE transform: proper rotation (MODLOG §73: the rig's L/R labels prove the old
    #      reflection mirrored the car) + scale, then a single offset
    Vw = to_jc3_rot(Pp[W["p"]]) * a.scale
    UVw = np.stack([W["u"], W["v"]], 1).astype(np.float64)
    tris = F["w"].astype(np.int64)
    sv = np.einsum("ij,ij->i", Vw[tris[:, 0]], np.cross(Vw[tris[:, 1]], Vw[tris[:, 2]])).sum() / 6
    if sv < 0:                      # vanilla JC3 meshes have POSITIVE signed volume (measured)
        tris = tris[:, [0, 2, 1]]
    print(f"rotation: signed volume {sv:+.1f} -> winding {'reversed' if sv < 0 else 'kept'}")

    # ---- parts, dynamically: bones classified by shape; the N largest round parts anchor wheels
    cl = PX.classify(Vw, tris, fb, len(bones))
    round_b = [b for b, (k, n, info) in cl.items() if k == "spinning"]
    size = lambda b: max(cl[b][2][3], cl[b][2][4])
    anchors = sorted(round_b, key=size, reverse=True)[:nwheels]
    if len(anchors) != nwheels:
        raise SystemExit(f"found {len(anchors)} round parts for {nwheels} wheels")
    cz = np.median([cl[b][2][0][2] for b in anchors])
    corner = {b: ("f" if cl[b][2][0][2] < cz else "r") + "_" + ("l" if cl[b][2][0][0] < 0 else "r")
              for b in anchors}
    if sorted(corner.values()) != sorted(CORNERS):
        raise SystemExit(f"wheel anchors do not cover the four corners: {corner}")
    wheel_of = dict(corner)
    for b in round_b:                                    # attach other round parts INSIDE a wheel
        if b in wheel_of:
            continue
        c = cl[b][2][0]
        for ab in anchors:
            ac, r = cl[ab][2][0], size(ab) / 2
            if np.sign(c[0]) == np.sign(ac[0]) and np.linalg.norm(c[1:] - ac[1:]) < r and size(b) <= 2 * r:
                wheel_of[b] = corner[ab]
    print("wheels:", {c: [bones[b][0] for b in wheel_of if wheel_of[b] == c] for c in CORNERS})
    face_part = np.array(["body"] * len(F), dtype=object)
    for b, c in wheel_of.items():
        face_part[fb == b] = "wheel_" + c

    # ---- left/right audit against the rig's own labels (report only, never used for logic)
    agree = disagree = 0
    for b, (name, _) in enumerate(bones):
        if cl[b][2] is None:
            continue
        x = cl[b][2][0][0]
        lab = re.search(r"(?:^|_)(L|Left|R|Right)(?:_|$)", name)
        if lab and abs(x) > 0.2:
            is_left = lab.group(1) in ("L", "Left")
            agree += is_left == (x < 0)
            disagree += is_left != (x < 0)
    print(f"L/R audit vs bone labels (left = -X): {agree} agree, {disagree} disagree")

    # ---- hubs: per corner, the ROUNDEST attached part (the tyre) gives centre, radius, width
    hubs = {}
    for c in CORNERS:
        bs = [b for b, cc in wheel_of.items() if cc == c and size(b) >= 0.8 * max(size(x) for x in anchors)]
        tb = min(bs, key=lambda b: cl[b][2][2])
        pts = Vw[np.unique(tris[fb == tb])]
        lo, hi = pts.min(0), pts.max(0)
        hubs[c] = ((lo + hi) / 2, (hi[1] - lo[1]) / 2, hi[0] - lo[0], bones[tb][0])
    # nothing outside the tyre's own circle can spin with it: faces weighted to a wheel bone whose
    # centroid lies beyond the tyre radius (+3%) go to the static body (an ~80-vert piece above each
    # tyre is weighted to the Disc bone; it would orbit the axle)
    cen = Vw[tris].mean(1)
    moved = 0
    for c in CORNERS:
        sel = face_part == "wheel_" + c
        rad = np.linalg.norm(cen[:, 1:] - hubs[c][0][1:], axis=1)
        out = sel & (rad > 1.03 * hubs[c][1])
        face_part[out] = "body"
        moved += int(out.sum())
    print(f"wheel faces outside their tyre circle -> body: {moved}")
    xc = np.mean([h[0][0] for h in hubs.values()])
    ground = min(h[0][1] - h[1] for h in hubs.values())
    zc = (np.mean([hubs[c][0][2] for c in ("f_l", "f_r")]) + np.mean([hubs[c][0][2] for c in ("r_l", "r_r")])) / 2
    offset = np.array([-xc, a.ground - ground, a.center_z - zc])
    Vw = Vw + offset
    print(f"transform: scale {a.scale}  offset {np.round(offset, 4).tolist()}")

    stations = {"scale": a.scale, "offset": offset.tolist(), "ground": a.ground, "mapping": "rotation",
                "hardpoint_x": a.hardpoint_x, "corners": {}}
    for c in CORNERS:
        hub = hubs[c][0] + offset
        sx = -1 if c.endswith("l") else 1
        hx = float(hub[0]) if a.hardpoint_x == "true" else sx * float(a.hardpoint_x)
        stations["corners"][c] = {"hub_true": [round(float(x), 4) for x in hub],
                                  "hardpoint": [round(hx, 4), round(float(hub[1]), 4), round(float(hub[2]), 4)],
                                  "axle_shift_x": round(float(hub[0]) - hx, 4),
                                  "radius": round(float(hubs[c][1]), 4),
                                  "tyre_width": round(float(hubs[c][2]), 4),
                                  "tyre_bone": hubs[c][3]}
    body_faces = face_part == "body"
    allv = Vw[np.unique(tris[body_faces])]
    blo, bhi = allv.min(0), allv.max(0)
    stations["body_bbox"] = [np.round(blo, 3).tolist(), np.round(bhi, 3).tolist()]
    fz = [stations["corners"][c]["hub_true"][2] for c in ("f_l", "r_l")]
    print(f"body  {bhi[0]-blo[0]:.3f} x {bhi[1]-blo[1]:.3f} x {bhi[2]-blo[2]:.3f} m   wheelbase {fz[1]-fz[0]:.3f} m")
    for c, s in stations["corners"].items():
        print(f"  {c}: hub {s['hub_true']}  radius {s['radius']:.3f}  width {s['tyre_width']:.3f}  ({s['tyre_bone']})")
    json.dump(stations, open(os.path.join(a.out, "stations.json"), "w"), indent=2)

    # ---- materials: the FULL BmAK interface of each material -> a JC3 block spec (factors.py).
    #      Every JC3 input is set by a rule and tagged; an unhandled BmAK factor fails the run (§79).
    props, files = FX.load_bmak(a.src_dir)
    used = sorted({mats[i] for i in np.unique(F["m"])})
    fallbacks = TM.texture_bindings(used, a.src_dir)
    specs = {m: FX.jc3_spec(m, FX.resolve(m, props), files, fallbacks) for m in used}
    unhandled = [f"{m}: {d['factor']}" for m, s in specs.items() for d in s["dispositions"]
                 if d["disposition"] == "UNHANDLED"]
    json.dump({"materials": specs, "unhandled": unhandled}, open(os.path.join(a.out, "factors.json"), "w"), indent=1)
    FX.write_report(specs, os.path.join(a.out, "coverage.md"))
    print(f"factors: {len(specs)} materials, {sum(len(s['dispositions']) for s in specs.values())} BmAK factors, "
          f"{len(unhandled)} unhandled -> coverage.md")
    if unhandled:
        raise SystemExit("UNHANDLED BmAK factors: " + "; ".join(unhandled))

    # ---- texture jobs: every slot texture the specs ask for (tga, separation mask, generated solid)
    area_f = 0.5 * np.linalg.norm(np.cross(Vw[tris[:, 1]] - Vw[tris[:, 0]], Vw[tris[:, 2]] - Vw[tris[:, 0]]), axis=1)
    jobs = {}           # key -> {path|solid, kind, alpha, tint, mult, area}
    for mi, m in enumerate(mats):
        if m not in specs:
            continue
        A = float(area_f[F["m"] == mi].sum())
        for slot, t in specs[m]["textures"].items():
            if "tga" in t:
                if t.get("kind") == "glass":
                    # Window dif: BC3 whose alpha is the BmAK opacity map x Glass_Opacity (factors.py)
                    key = os.path.splitext(os.path.basename(t["tga"]))[0] + "_glass"
                    j = jobs.setdefault(key, {"tga": t["tga"], "kind": "glass", "tint": t["tint"],
                                              "mult": t.get("alpha_multiplier", 1.0), "area": 0.0})
                    j["area"] += A
                    continue
                kind = t.get("kind") or {"s0": "colour", "s1": "normal"}.get(slot, "mask")
                key = os.path.splitext(os.path.basename(t["tga"]))[0] + ("_a" if t.get("alpha_tga") else "")
                if kind == "mask":
                    key += "_msk"
                j = jobs.setdefault(key, {"tga": t["tga"], "kind": kind, "alpha": t.get("alpha_tga"), "area": 0.0})
                j["area"] += A
            elif "solid" in t:
                rgb = tuple(int(round(c * 255)) for c in t["solid"][:3])
                jobs.setdefault("solid_%02x%02x%02x" % rgb, {"solid": rgb, "kind": "colour", "area": 0.0})
    big = {k: [j["tga"], j["kind"], j["area"]] for k, j in jobs.items() if "tga" in j}
    caps = allocate_caps(big, texture_budget_kb(a.budget_xml, a.vehicle_class, a.vanilla_toc), a.tex_max)
    vfs_dir = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/batmobile/"
    tex_files, vfs_of = {}, {}
    if not a.dry_run:
        from PIL import Image
        for key, j in jobs.items():
            if "solid" in j:
                r = TX.convert_image(Image.new("RGB", (8, 8), j["solid"]), key.lower(), os.path.join(a.out, "ddsc"), "colour")
            elif j["kind"] == "glass":
                src = Image.open(j["tga"]).convert("L")
                alpha = src.point(lambda v: min(255, int(round(v * j["mult"]))))
                tint = Image.new("RGB", src.size, tuple(int(round(c * 255)) for c in j["tint"]))
                r = TX.convert_image(tint, key.lower(), os.path.join(a.out, "ddsc"), "glass", caps[key], alpha)
            else:
                alpha = Image.open(j["alpha"]).convert("L") if j.get("alpha") else None
                r = TX.convert_image(Image.open(j["tga"]), key.lower(), os.path.join(a.out, "ddsc"), j["kind"],
                                     caps[key], alpha)
            vfs_of[key] = vfs_dir + key.lower() + ".ddsc"
            tex_files[vfs_of[key]] = r["ddsc"]
            print(f"  texture {key}: {j['kind']}{' +alpha' if r['alpha'] else ''} {r['size'][0]}x{r['size'][1]} "
                  f"{r['bytes']} B  worst PSNR {r['worst_mip_psnr_db']} dB"
                  + (f" (alpha {r['worst_alpha_psnr_db']} dB)" if "worst_alpha_psnr_db" in r else ""))

    def slot_path(m, slot):
        t = specs[m]["textures"][slot]
        if "vanilla" in t:
            return t["vanilla"]
        if "solid" in t:
            return vfs_of["solid_%02x%02x%02x" % tuple(int(round(c * 255)) for c in t["solid"][:3])]
        base = os.path.splitext(os.path.basename(t["tga"]))[0]
        if t.get("kind") == "glass":
            return vfs_of[base + "_glass"]
        key = base + ("_a" if t.get("alpha_tga") else "")
        return vfs_of[key + ("_msk" if slot in ("s2", "s3") else "")]

    plan = {part: [{"material": mats[mi], "mat_index": int(mi), "block": specs[mats[mi]]["block"]}
                   for mi in np.unique(F["m"][face_part == part])]
            for part in ["body"] + ["wheel_" + c for c in CORNERS]}
    json.dump({"plan": plan, "textures": tex_files}, open(os.path.join(a.out, "assembly.json"), "w"), indent=2)
    if a.dry_run:
        return

    # ---- meshes: one block per material, EVERY CarPaintMM input written from the spec
    def maker(m):
        spec = specs[m]

        def make(v, uv, I, N):
            if spec["block"] == "Window":
                blk = build_window_block(a.window_template, v, uv, I, N)
                for i, s in enumerate(("s0", "s1")):           # dif (BC3) + normal; crack slots keep vanilla
                    if s in spec["textures"]:
                        blk.textures[i] = slot_path(m, s)
                return blk, 7, 40
            blk = P.build_rbm_plain(a.body_template, a.colour_block, v, uv, I, N).blocks[0]
            inp = spec["inputs"]
            blk.static_params = struct.pack("<72f", *[x for n in FX.STATIC for x in inp["static." + n]["value"]])
            blk.static_support = struct.pack("<7f", *[inp["support." + n]["value"] for n in FX.SUPPORT])
            blk.dynamic_params = struct.pack("<16f3f", *(inp["dynamic.TintColorR"]["value"] + inp["dynamic.TintColorG"]["value"]
                                                         + inp["dynamic.TintColorB"]["value"] + [0.0] * 4),
                                             *inp["dynamic.Overrides"]["value"])
            blk.flags = spec["flags"]["value"]
            for s in ("s0", "s1", "s2", "s3"):
                blk.textures[int(s[1])] = slot_path(m, s)
            return blk, 4, 24
        return make

    for part in plan:
        if part == "body":
            V0, budgets, container = Vw, [int(x) for x in a.body_tris.split(",")], a.body_template
        else:
            V0 = Vw - np.array(stations["corners"][part[6:]]["hardpoint"])
            budgets, container = [int(x) for x in a.wheel_tris.split(",")], a.wheel_template
        groups = [(it["material"], tris[(face_part == part) & (F["m"] == it["mat_index"])], maker(it["material"]),
                   it["block"] == "Window") for it in plan[part]]
        part_chain(V0, UVw, groups, budgets, container, a.out, part)

    # ---- model budget guard: every LOD of the bound parts counts (consistent with 063/065
    #      rendering); over the game's Vehicle model hard cap the whole vehicle would vanish (§76)
    model_kb = sum(os.path.getsize(os.path.join(a.out, f"{p}_lod{i}.rbm"))
                   for p in plan for i in range(1, 6)) / 1024
    hard_kb = budget_value(a.budget_xml, a.vehicle_class, "Model")
    cap_kb = hard_kb * a.budget_safety
    print(f"model footprint {model_kb:.0f} KB of {cap_kb:.0f} KB "
          f"(Model HARD {hard_kb:.0f} KB x{a.budget_safety:g}; old x0.9 guard = {hard_kb * 0.9:.0f} KB)")
    if model_kb > cap_kb:
        raise SystemExit("MODEL BUDGET EXCEEDED: lower --body-tris / --wheel-tris")
    # palette: no block carries SUPPORT_PALETTE_FILE any more -- every block's tint colours are its
    # own BmAK colours (spec dynamic.TintColor*), so the vehicle palette no longer recolours the car
    stale = os.path.join(a.out, "palette_true.vmodc")
    if os.path.exists(stale):
        os.remove(stale)
    print("assembly ->", os.path.join(a.out, "assembly.json"))


if __name__ == "__main__":
    main()
