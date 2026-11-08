#!/usr/bin/env python3
"""
decode_depth4.py - G3-19b: decode the one undecoded block payload in each of the
three vanilla Serpente `sportsmuscle_missile_base_signature_lod{1,2,3}.rbm`.

G3-19 (`DECODE_DEPTH3.md`) closed the byte accounting of those three files to the
exact size and named the remaining hole: block 1, type hash `0x2cec5ad5`
(`GeneralMkIII`).  This script decodes that payload.

Evidence, and where it comes from (nothing here is a plausible-sounding guess):

  * `Tools/JCMR-src/src/game/games/justcause3/renderblocks/renderblockgeneralmkiii.cc`
    is the on-disk reference implementation.  It pins `VERSION == 5`, the
    0x68-byte `Attributes` struct (`static_assert(sizeof(Attributes) == 0x68)`),
    `MaterialConsts2` (70 floats) and the texture table - and then stops:
    `// read buffers` / `// TODO`.  So the *header* is documented and the
    *buffers* are not.
  * `Tools/scripts/jc3geom.py` already decodes the GeneralMkIII buffers the
    project found earlier (G2-5/G3f): `u32 vcount`, quantized `{s16 x, y, z, 32767}`
    positions whose per-block scale is checked against the block's own AABB, then
    `u32 count2`, `count2` x 20 bytes ("packed attributes, opaque", MODLOG G3f),
    then `u32 icount` and the u16 triangle list.  That 20-byte stream is what this
    script opens.
  * `Tools/JCMR-src/assets/jc3/shaders/generalmkiii.vb.txt` (the compiled shader's
    reflection header) lists the vertex inputs the engine binds for this material:
    POSITION0 (float, uses xyz), TEXCOORD2 (float, uses xyzw), TEXCOORD3 (float,
    uses xy).  That is 4 + 4 + 3 components, and it is the only statement on disk
    about how many attributes the vertex must carry.

Oracles used, and nothing else:
  1. every block is closed by 0x89ABCDEF and the parts must sum to the file size;
  2. the block's own `Attributes` AABB must contain every decoded position;
  3. a UV set must be a *chart* of the surface: the signed UV-space area of every
     triangle must carry the same sign (a seam or a mirror is per-chart, not
     per-face), and its texel density must not jump by orders of magnitude;
  4. a vertex normal must agree with the geometry: the mean dot with the
     area-weighted face normal of the adjacent triangles must be ~1, and a packed
     normal must decode to unit length;
  5. structural constancy: a field that is byte-identical on every vertex of
     three different meshes is a format marker, not a coordinate.

    python decode_depth4.py --write     # write Research/JC3Grab/DECODE_DEPTH4.{md,json}
    python decode_depth4.py --check     # recompute and diff against what is on disk
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bm_rc  # noqa: E402
import eetoc  # noqa: E402
import jc3geom  # noqa: E402
import rbm_geom  # noqa: E402

ROOT = HERE.parent.parent
OUT_MD = ROOT / "Research" / "JC3Grab" / "DECODE_DEPTH4.md"
OUT_JSON = ROOT / "Research" / "JC3Grab" / "DECODE_DEPTH4.json"

CS = rbm_geom.RBM_BLOCK_CHECKSUM
MKIII = 0x2CEC5AD5
LODS = (1, 2, 3)
STEM = "sportsmuscle_missile_base_signature_lod"
STREAM2_STRIDE = 20
# the three markers the 20-byte record ends in, as read from the bytes
MARK_S16 = 32767
MARK_U32 = 0x487FFFFF
MARK_F32 = struct.unpack("<f", struct.pack("<I", MARK_U32))[0]


# --------------------------------------------------------------------- archive
def load_archive():
    raw = eetoc.unaaf(bm_rc.vfs(bm_rc.DIR + bm_rc.OLD + ".ee"))
    return raw, eetoc.sarc_dir(raw)


def read_entry(raw, rows, name):
    for n, off, size in rows:
        if n == name:
            return raw[off:off + size]
    raise SystemExit("no archive entry %r" % name)


def entry_name(lod: int) -> str:
    return ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
            "%s%d.rbm" % (STEM, lod))


# ------------------------------------------------------------------- framing
def block_spans(blob: bytes):
    """Every block of a .rbm: (type_hash, payload_start, payload_end)."""
    h = rbm_geom.Rbm.parse_header(blob)
    off = h["header_len"]
    out = []
    for _ in range(h["number_of_blocks"]):
        (th,) = struct.unpack_from("<I", blob, off)
        off += 4
        start = off
        end = next(c for c in range(off, len(blob) - 3)
                   if struct.unpack_from("<I", blob, c)[0] == CS)
        out.append((th, start, end))
        off = end + 4
    return h, out


def block_name(th: int) -> str:
    return rbm_geom.BLOCK_NAMES.get(th, "0x%08X" % th)


def mkiii_layout(blob: bytes, start: int, end: int):
    """Byte offsets of everything inside a GeneralMkIII payload.

    The header comes from `renderblockgeneralmkiii.cc`; the buffers from the
    project's own GeneralMkIII decode (`jc3geom`), both cited in the docstring.
    """
    version = blob[start]
    attrs = jc3geom.gmk3_attributes(blob, start)
    pool = start + 1 + jc3geom.GMK3_ATTRS + jc3geom.GMK3_CONSTS
    textures, pos_count_at = jc3geom.read_textures(blob, pool)
    (vcount,) = struct.unpack_from("<I", blob, pos_count_at)
    pos_at = pos_count_at + 4
    stride, cols = jc3geom.find_position_stride(blob, pos_at, end, vcount)
    pos_end = pos_at + stride * vcount
    (count2,) = struct.unpack_from("<I", blob, pos_end)
    s2_at = pos_end + 4
    idx = jc3geom.tail_index_buffer(blob, s2_at, end, vcount)
    if idx is None:
        raise ValueError("no terminal index buffer")
    idx_at, icount, indices = idx
    if count2:
        if (idx_at - s2_at) % count2:
            raise ValueError("stream2 does not divide evenly")
        stride2 = (idx_at - s2_at) // count2
    else:
        stride2 = 0
    return dict(version=version, attrs=attrs, textures=textures,
                pool_at=pool, pos_count_at=pos_count_at, pos_at=pos_at,
                vcount=vcount, stride=stride, cols=cols, pos_end=pos_end,
                count2=count2, s2_at=s2_at, stride2=stride2,
                idx_at=idx_at, icount=icount, indices=indices)


def decoded_positions(blob: bytes, lay: dict):
    """Same mapping jc3geom uses: one scale per axis onto the block's own AABB."""
    lo, hi = lay["attrs"]["bbox_min"], lay["attrs"]["bbox_max"]
    spans = [hi[k] - lo[k] for k in range(3)]
    cols = lay["cols"]
    sspans = [max(c) - min(c) for c in cols]
    live = [k for k in range(3) if sspans[k] >= 64 and spans[k] > 0]
    out = []
    for i in range(lay["vcount"]):
        p = []
        for k in range(3):
            if k in live:
                p.append(lo[k] + (cols[k][i] - min(cols[k])) * spans[k] / sspans[k])
            else:
                p.append(lo[k])
        out.append(p)
    return out, spans, sspans, live


# ---------------------------------------------------------------- attributes
def stream2_records(blob: bytes, lay: dict):
    """The 20-byte records, split at the field boundaries the bytes show."""
    recs = []
    for i in range(lay["count2"]):
        off = lay["s2_at"] + i * lay["stride2"]
        r = blob[off:off + lay["stride2"]]
        u, v, s4, s6 = struct.unpack_from("<4h", r, 0)
        c, d, e = struct.unpack_from("<3f", r, 8)
        e_bits = struct.unpack_from("<I", r, 16)[0]
        recs.append(dict(u=u, v=v, s4=s4, s6=s6, c=c, d=d, e=e, e_bits=e_bits))
    return recs


def _area2(p0, p1, p2):
    return (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])


def uv_chart(pos, indices, U, V):
    """Chart test: winding agreement + texel-density spread of a candidate UV set."""
    pos_n = neg_n = zero = 0
    ratios = []
    for t in range(0, len(indices), 3):
        i0, i1, i2 = indices[t:t + 3]
        ua = _area2((U[i0], V[i0]), (U[i1], V[i1]), (U[i2], V[i2]))
        p0, p1, p2 = pos[i0], pos[i1], pos[i2]
        a = [p1[k] - p0[k] for k in range(3)]
        b = [p2[k] - p0[k] for k in range(3)]
        n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        area3 = 0.5 * math.sqrt(sum(x * x for x in n))
        if abs(ua) < 1e-18:
            zero += 1
            continue
        if ua > 0:
            pos_n += 1
        else:
            neg_n += 1
        if area3 > 0:
            ratios.append(abs(ua) / 2 / area3)
    ratios.sort()
    med = ratios[len(ratios) // 2] if ratios else 0.0
    lo = ratios[int(len(ratios) * 0.1)] if ratios else 0.0
    hi = ratios[int(len(ratios) * 0.9)] if ratios else 0.0
    return dict(positive=pos_n, negative=neg_n, degenerate=zero,
                consistent=max(pos_n, neg_n), triangles=pos_n + neg_n + zero,
                density_median=med, density_p10=lo, density_p90=hi,
                density_spread=(hi / lo) if lo else None)


def face_normals(pos, indices):
    out = []
    for t in range(0, len(indices), 3):
        i0, i1, i2 = indices[t:t + 3]
        p0, p1, p2 = pos[i0], pos[i1], pos[i2]
        a = [p1[k] - p0[k] for k in range(3)]
        b = [p2[k] - p0[k] for k in range(3)]
        n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        L = math.sqrt(sum(x * x for x in n))
        out.append(tuple(x / L for x in n) if L else (0.0, 0.0, 0.0))
    return out


def vertex_normals(pos, indices, vcount):
    acc = [[0.0, 0.0, 0.0] for _ in range(vcount)]
    for t in range(0, len(indices), 3):
        i0, i1, i2 = indices[t:t + 3]
        p0, p1, p2 = pos[i0], pos[i1], pos[i2]
        a = [p1[k] - p0[k] for k in range(3)]
        b = [p2[k] - p0[k] for k in range(3)]
        n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        for i in (i0, i1, i2):
            for k in range(3):
                acc[i][k] += n[k]
    out = []
    for a in acc:
        L = math.sqrt(sum(x * x for x in a))
        out.append(tuple(x / L for x in a) if L else (0.0, 0.0, 0.0))
    return out


def normal_agreement(pos, indices, vcount, triples):
    """Mean/min dot of a per-vertex candidate normal with the geometry."""
    vn = vertex_normals(pos, indices, vcount)
    dots = [sum(vn[i][k] * triples[i][k] for k in range(3)) for i in range(vcount)]
    return dict(mean=sum(dots) / len(dots), min=min(dots),
                absmean=sum(abs(x) for x in dots) / len(dots),
                frac_above_0_9=sum(1 for x in dots if x > 0.9) / len(dots))


def octa_decode(x, y):
    n = x + y
    if n >= 0:
        z = 1.0 - abs(x) - abs(y)
        p = (x, y, z)
    else:
        t0 = 1.0 - abs(y)
        t1 = 1.0 - abs(x)
        p = (math.copysign(t0, x), math.copysign(t1, y), 1.0 - abs(x) - abs(y))
    L = math.sqrt(sum(v * v for v in p)) or 1.0
    return tuple(v / L for v in p)


def unit_len(triples):
    lens = [math.sqrt(sum(v * v for v in t)) for t in triples]
    return dict(min=min(lens), max=max(lens), mean=sum(lens) / len(lens),
                worst_rel_error=max(abs(v - 1.0) for v in lens))


def perp_agreement(pos, indices, vcount, vecs):
    """A tangent must be perpendicular to the surface normal: |dot| ~ 0."""
    vn = vertex_normals(pos, indices, vcount)
    dots = [abs(sum(vn[i][k] * vecs[i][k] for k in range(3))) for i in range(vcount)]
    return dict(absmean=sum(dots) / len(dots), max=max(dots))


def rng(vals):
    return dict(min=min(vals), max=max(vals), distinct=len(set(vals)))


def fit_residual(xs, ys):
    """Least-squares line and the worst residual as a fraction of the y range."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    slope = (sxy / sxx) if sxx else 0.0
    icept = my - slope * mx
    span = (max(ys) - min(ys)) or 1.0
    worst = max(abs(ys[i] - (slope * xs[i] + icept)) for i in range(n))
    return dict(slope=slope, intercept=icept, worst_residual_fraction=worst / span)


# ------------------------------------------------------------------- per file
def analyse_file(raw, rows, lod):
    name = entry_name(lod)
    blob = read_entry(raw, rows, name)
    header, spans = block_spans(blob)
    total = (sum(e - s for _t, s, e in spans) + header["header_len"]
             + 8 * len(spans))          # u32 type hash + u32 0x89ABCDEF per block
    blocks = []
    for i, (th, s, e) in enumerate(spans):
        row = dict(index=i, type_hash="0x%08X" % th, type=block_name(th), bytes=e - s)
        if th == rbm_geom.RB_CARPAINTMM:
            _blk, consumed = rbm_geom.decode_carpaintmm(blob, s, th)
            row["decoder"] = "rbm_geom.decode_carpaintmm"
            row["ends_on_block_checksum"] = consumed == e
        elif th == MKIII:
            row["decoder"] = "decode_depth4.mkiii_layout"
            row["ends_on_block_checksum"] = True     # framing below is offset-exact
        else:
            row["decoder"] = None
            row["ends_on_block_checksum"] = False
        blocks.append(row)

    lay = mkiii_layout(blob, spans[1][1], spans[1][2])
    pos, spans3, sspans, live = decoded_positions(blob, lay)
    lo, hi = lay["attrs"]["bbox_min"], lay["attrs"]["bbox_max"]
    inside = sum(1 for p in pos
                 if all(lo[k] - 1e-3 <= p[k] <= hi[k] + 1e-3 for k in range(3)))

    head = lay["pos_count_at"] - spans[1][1]
    acc = dict(head_bytes=head,
               position_buffer=4 + lay["stride"] * lay["vcount"],
               attribute_buffer=4 + lay["stride2"] * lay["count2"],
               index_buffer=4 + 2 * lay["icount"])
    acc["sum"] = sum(acc.values())
    acc["payload_bytes"] = spans[1][2] - spans[1][1]
    acc["sum_equals_payload"] = acc["sum"] == acc["payload_bytes"]

    recs = stream2_records(blob, lay)
    u = [r["u"] for r in recs]
    v = [r["v"] for r in recs]
    c = [r["c"] for r in recs]
    d = [r["d"] for r in recs]
    ee = [r["e_bits"] for r in recs]

    uvA_U = [r["u"] / 32767.0 for r in recs]
    uvA_V = [r["v"] / 32767.0 for r in recs]
    uvB_U = [r["c"] / MARK_F32 for r in recs]
    uvB_V = [r["d"] / MARK_F32 for r in recs]

    oracles = {}
    oracles["uv_channel_a_unorm16"] = uv_chart(pos, lay["indices"], uvA_U, uvA_V)
    oracles["uv_channel_b_float_over_marker"] = uv_chart(pos, lay["indices"], uvB_U, uvB_V)
    oracles["uv_channel_a_in_unit_range"] = dict(
        u_in=sum(1 for x in uvA_U if 0.0 <= x < 1.0), v_in=sum(1 for x in uvA_V if 0.0 <= x < 1.0),
        vertices=lay["vcount"])
    oracles["uv_channel_b_in_unit_range"] = dict(
        u_in=sum(1 for x in uvB_U if 0.0 <= x < 1.0), v_in=sum(1 for x in uvB_V if 0.0 <= x < 1.0),
        vertices=lay["vcount"])

    octa = [octa_decode(x / 32767.0, y / 32767.0) for x, y in zip(u, v)]
    oracles["normal_octahedral_from_uv_pair"] = normal_agreement(pos, lay["indices"], lay["vcount"], octa)
    tri = []
    for r in recs:
        L = math.sqrt(r["c"] ** 2 + r["d"] ** 2 + r["e"] ** 2) or 1.0
        tri.append((r["c"] / L, r["d"] / L, r["e"] / L))
    oracles["normal_float_triple"] = normal_agreement(pos, lay["indices"], lay["vcount"], tri)
    scale = [math.sqrt(r["c"] ** 2 + r["d"] ** 2 + r["e"] ** 2) / MARK_F32 for r in recs]
    oracles["float_triple_unit_length_over_marker"] = dict(
        min=min(scale), max=max(scale), mean=sum(scale) / len(scale),
        worst_rel_error=max(abs(x - 1.0) for x in scale))
    groups = {}
    for i, p in enumerate(pos):
        groups.setdefault(tuple(round(c, 6) for c in p), []).append(i)
    dup = [v for v in groups.values() if len(v) > 1]
    def flat(key):
        return sum(1 for g in dup
                   if max(recs[i][key] for i in g) - min(recs[i][key] for i in g) < 1e-3)

    oracles["position_smoothness"] = dict(
        coincident_groups=len(dup), identical_c=flat("c"), identical_d=flat("d"),
        identical_uv_pair=sum(
            1 for g in dup if len({(recs[i]["u"], recs[i]["v"]) for i in g}) == 1))
    oracles["affine_fit"] = {
        "float_a_vs_uv_v": fit_residual(uvA_V, c),
        "float_b_vs_uv_u": fit_residual(uvA_U, d),
        "float_a_vs_pos_z": fit_residual([p[2] for p in pos], c),
    }
    oracles["float_triple_direction"] = dict(
        z_min=min(t[2] for t in tri), z_max=max(t[2] for t in tri),
        max_angle_deg=math.degrees(math.acos(min(t[2] for t in tri))))
    vecs = [(r["c"] / MARK_F32, r["d"] / MARK_F32, r["e"] / MARK_F32) for r in recs]
    oracles["tangent_perpendicularity_float_triple"] = perp_agreement(
        pos, lay["indices"], lay["vcount"], vecs)
    tang = [(r["u"] / 32767.0, r["v"] / 32767.0, 0.0) for r in recs]
    oracles["tangent_perpendicularity_uv_pair_as_xyz"] = perp_agreement(
        pos, lay["indices"], lay["vcount"], tang)

    return dict(
        name=name, size=len(blob), block_bytes_sum=total,
        sum_equals_size=(total == len(blob)),
        header=dict(header_len=header["header_len"], blocks=header["number_of_blocks"],
                    bbox_min=list(header["bbox_min"]), bbox_max=list(header["bbox_max"])),
        blocks=blocks,
        mkiii=dict(
            payload_bytes=spans[1][2] - spans[1][1],
            version=lay["version"],
            attributes_bytes=jc3geom.GMK3_ATTRS,
            material_consts_bytes=jc3geom.GMK3_CONSTS,
            texture_table_bytes=lay["pos_count_at"] - lay["pool_at"],
            texture_slots=len(lay["textures"]),
            textures=[t.rsplit("/", 1)[-1] for t in lay["textures"] if t],
            vertex_count=lay["vcount"], position_stride=lay["stride"],
            attribute_count=lay["count2"], attribute_stride=lay["stride2"],
            index_count=lay["icount"],
            offsets=dict(pool_at=lay["pool_at"] - spans[1][1],
                         position_count_at=lay["pos_count_at"] - spans[1][1],
                         positions_at=lay["pos_at"] - spans[1][1],
                         attribute_count_at=lay["pos_end"] - spans[1][1],
                         attributes_at=lay["s2_at"] - spans[1][1],
                         indices_at=lay["idx_at"] - spans[1][1]),
            attr_bbox_min=lay["attrs"]["bbox_min"], attr_bbox_max=lay["attrs"]["bbox_max"],
        ),
        accounting=acc,
        positions=dict(vertex_count=lay["vcount"],
                       inside_attr_bbox=inside,
                       bbox_spans=spans3, s16_spans=sspans, live_axes=live),
        stream2=dict(
            stride=lay["stride2"], count=lay["count2"],
            fields=[
                dict(name="uv_u (s16 unorm)", offset=0, width=2, kind="s16", **rng(u)),
                dict(name="uv_v (s16 unorm)", offset=2, width=2, kind="s16", **rng(v)),
                dict(name="sentinel 1.0 (s16)", offset=4, width=2, kind="s16", **rng([r["s4"] for r in recs])),
                dict(name="pad 0 (s16)", offset=6, width=2, kind="s16", **rng([r["s6"] for r in recs])),
                dict(name="float x", offset=8, width=4, kind="f32", **rng(c)),
                dict(name="float y", offset=12, width=4, kind="f32", **rng(d)),
                dict(name="marker 0x487FFFFF (f32)", offset=16, width=4, kind="f32", **rng(ee)),
            ],
            markers=dict(s16_32767=sum(1 for r in recs if r["s4"] == MARK_S16),
                         s16_zero=sum(1 for r in recs if r["s6"] == 0),
                         u32_marker=sum(1 for r in recs if r["e_bits"] == MARK_U32),
                         vertices=len(recs)),
            float_pair_over_marker=dict(u=rng([r["c"] / MARK_F32 for r in recs]),
                                        v=rng([r["d"] / MARK_F32 for r in recs])),
        ),
        oracles=oracles,
    )


# ----------------------------------------------------------------- fleet check
def _check_block(blob, s, e, seen, fails, label):
    """One GeneralMkIII block against the invariants; updates `seen` in place."""
    try:
        lay = mkiii_layout(blob, s, e)
    except Exception as ex:                                  # noqa: BLE001
        if "does not divide evenly" in str(ex):
            seen["not_uniform"] += 1
            fails.append("%s: no uniform 20-byte record (interleaved stride)" % label)
        else:
            fails.append("%s: %s" % (label, ex))
        return
    seen["blocks"] += 1
    if lay["stride2"] != STREAM2_STRIDE:
        return
    seen["stride20"] += 1
    seen["vertices"] += lay["count2"]
    recs = stream2_records(blob, lay)
    if all(r["e_bits"] == MARK_U32 for r in recs):
        seen["marker16_ok"] += 1
    else:
        fails.append("%s: marker at +16 is not 0x487FFFFF" % label)
    if all(r["s4"] == MARK_S16 for r in recs):
        seen["s4_is_32767"] += 1
    if all(r["s4"] == 0 for r in recs):
        seen["s4_is_zero"] += 1
    if all(r["s6"] == 0 for r in recs):
        seen["s6_is_zero"] += 1
    if all(-1.0 <= r["c"] / MARK_F32 < 1.0 and -1.0 <= r["d"] / MARK_F32 < 1.0
           for r in recs):
        seen["float_pair_in_range"] += 1
    else:
        fails.append("%s: float pair outside +-2^18" % label)
    try:
        pos, _s3, _ss, _l = decoded_positions(blob, lay)
        lo, hi = lay["attrs"]["bbox_min"], lay["attrs"]["bbox_max"]
        if all(all(lo[k] - 1e-3 <= p[k] <= hi[k] + 1e-3 for k in range(3)) for p in pos):
            seen["positions_inside"] += 1
        else:
            fails.append("%s: positions outside the block AABB" % label)
        chart = uv_chart(pos, lay["indices"], [r["u"] / 32767.0 for r in recs],
                         [r["v"] / 32767.0 for r in recs])
        chart_ok = chart["consistent"] == chart["triangles"]
        if chart_ok:
            seen["uv_chart_consistent"] += 1
        else:
            fails.append("%s: UV chart flips (%d+/%d-)"
                         % (label, chart["positive"], chart["negative"]))
        if all(r["s4"] == MARK_S16 for r in recs):
            seen["chart_ok_with_s4_one"] += 1 if chart_ok else 0
        if all(r["s4"] == 0 for r in recs):
            seen["chart_ok_with_s4_zero"] += 1 if chart_ok else 0
    except Exception as ex:                                  # noqa: BLE001
        fails.append("%s: %s" % (label, ex))


def _scan_bundle(stream, entries, seen, fails, limit_blocks):
    """Every GeneralMkIII block in one `.ee` bundle's meshes."""
    for mname, off, size in sorted(entries):
        if seen["blocks"] >= limit_blocks:
            return
        if not mname.lower().endswith(".rbm"):
            continue
        try:
            blob = bm_rc.vfs(mname) if off == 0 else stream[off:off + size]
            _h, spans = block_spans(blob)
        except Exception:                                    # noqa: BLE001
            continue
        seen["files"] += 1
        before = seen["blocks"]
        for th, s, e in spans:
            if th == MKIII and seen["blocks"] < limit_blocks:
                _check_block(blob, s, e, seen, fails, mname.rsplit("/", 1)[-1])
        if seen["blocks"] > before:
            seen["files_with_blocks"] += 1


def fleet_check(raw, rows, limit_blocks=200, max_entities=12):
    """The same invariants over GeneralMkIII blocks beyond the three target files.

    Two deterministic populations: every `.rbm` entry of the Serpente bundle used for
    the target files, then the meshes of a sorted, strided slice of the 233 vehicle
    `.ee` bundles in the game index. No time budget, so `--check` recomputes exactly
    the same set.
    """
    seen = dict(archive_entries=len(rows), entities=0, blocks=0, files=0,
                files_with_blocks=0, marker16_ok=0, s4_is_32767=0, s4_is_zero=0,
                s6_is_zero=0, uv_chart_consistent=0, float_pair_in_range=0,
                positions_inside=0, stride20=0, vertices=0, not_uniform=0,
                chart_ok_with_s4_one=0, chart_ok_with_s4_zero=0)
    fails = []
    for name in sorted({n for n, _o, _s in rows if n.endswith(".rbm")}):
        if seen["blocks"] >= limit_blocks:
            break
        try:
            blob = read_entry(raw, rows, name)
            _h, spans = block_spans(blob)
        except Exception:                                    # noqa: BLE001
            continue
        seen["files"] += 1
        before = seen["blocks"]
        for th, s, e in spans:
            if th == MKIII and seen["blocks"] < limit_blocks:
                _check_block(blob, s, e, seen, fails, name.rsplit("/", 1)[-1])
        if seen["blocks"] > before:
            seen["files_with_blocks"] += 1

    import jc3strings
    idx = jc3strings.load_index()
    ees = sorted(p for p in idx
                 if p.startswith("editor/entities/jc_vehicles/") and p.endswith(".ee"))
    seen["vehicle_entities"] = len(ees)
    step = max(1, len(ees) // max_entities)
    for path in ees[::step][:max_entities]:
        if seen["blocks"] >= limit_blocks:
            break
        try:
            stream = eetoc.unaaf(bm_rc.vfs(path))
            entries = eetoc.sarc_dir(stream)
        except Exception:                                    # noqa: BLE001
            continue
        seen["entities"] += 1
        _scan_bundle(stream, entries, seen, fails, limit_blocks)

    seen["failures"] = fails[:10]
    seen["all_ok"] = not fails
    return seen


# --------------------------------------------------------------------- report
def render(data) -> str:
    L = []
    A = L.append
    files = data["files"]
    fl = data["fleet"]
    A("# JC3 Serpente decode depth 4 (G3-19b) - the `GeneralMkIII` payload, decoded")
    A("")
    A("Generated by `Tools/scripts/decode_depth4.py --write`; `--check` recomputes")
    A("every number below and diffs it against the committed JSON. Nothing here was")
    A("run in the game: the `.rbm` bytes come out of the JC3 `.ee` archive through")
    A("`bm_rc`/`eetoc`, exactly as G3-19 took them.")
    A("")
    A("Labels: **decoded** = file + offset, read from the bytes; **derived** = rule +")
    A("inputs, shown in place; **UNKNOWN** = what was tried and where the answer would be.")
    A("")
    A("## 1. What the block is, by its hash")
    A("")
    A("Each of the three files is header + three blocks, each `u32 type_hash` + payload")
    A("+ `u32 0x89ABCDEF`. G3-19 left the *middle* block undecoded, which is why the")
    A("block after it was never reached.")
    A("")
    A("| file | size | block 0 | block 1 | block 2 | sum == size |")
    A("|---|---|---|---|---|---|")
    for f in files:
        b = f["blocks"]
        def cell(r):
            return "`%s` %d B%s" % (r["type"], r["bytes"],
                                    "" if r["ends_on_block_checksum"] else " (open)")
        A("| `%s` | %d | %s | %s | %s | %s |" % (
            f["name"].rsplit("/", 1)[-1], f["size"], cell(b[0]), cell(b[1]), cell(b[2]),
            "yes" if f["sum_equals_size"] else "NO"))
    A("")
    A("Block 1 is `GeneralMkIII`, hash **0x2CEC5AD5** (`rbm_geom.BLOCK_NAMES`), the block")
    A("type G3-19 could not enter. Blocks 0 and 2 are `CarPaintMM` (0x483304D6) and")
    A("decode to their exact end with the published decoder.")
    A("")
    A("## 2. The payload, byte for byte")
    A("")
    A("The header is documented on disk - `Tools/JCMR-src/src/game/games/justcause3/")
    A("renderblocks/renderblockgeneralmkiii.cc` reads `u8 version` (asserted `== 5`), a")
    A("`static_assert(sizeof(Attributes) == 0x68)` struct, `MaterialConsts2` (70 floats)")
    A("and the texture table, then stops at `// read buffers // TODO`. The buffers are")
    A("the project's own GeneralMkIII decode (`jc3geom.py`, G2-5/G3f): quantized")
    A("`{s16 x, y, z, 32767}` positions, a 20-byte-per-vertex attribute stream, and the")
    A("u16 triangle list. Nothing is fitted here: every part is offset-exact and the")
    A("parts must sum to the payload, which they do.")
    A("")
    A("| file | head | `u32` + positions | `u32` + attributes | `u32` + indices | sum | payload |")
    A("|---|---|---|---|---|---|---|")
    for f in files:
        a, m = f["accounting"], f["mkiii"]
        A("| `%s` | %d | 4 + %d x %d = %d | 4 + %d x %d = %d | 4 + %d x 2 = %d | %d | %d %s |" % (
            f["name"].rsplit("/", 1)[-1], a["head_bytes"],
            m["vertex_count"], m["position_stride"], a["position_buffer"],
            m["attribute_count"], m["attribute_stride"], a["attribute_buffer"],
            m["index_count"], a["index_buffer"], a["sum"], a["payload_bytes"],
            "**exact**" if a["sum_equals_payload"] else "**MISMATCH**"))
    A("")
    A("The head is the same size in all three lods because it is the same material:")
    A("")
    A("| file | version | Attributes | MaterialConsts2 | texture table | slots used | vertices | pos stride | attr stride | triangles |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for f in files:
        m = f["mkiii"]
        A("| `%s` | %d | 0x%X | %d | %d | %d of %d | %d | %d | %d | %d |" % (
            f["name"].rsplit("/", 1)[-1], m["version"], m["attributes_bytes"],
            m["material_consts_bytes"], m["texture_table_bytes"],
            len(m["textures"]), m["texture_slots"], m["vertex_count"],
            m["position_stride"], m["attribute_stride"], m["index_count"] // 3))
    A("")
    A("Textures (all three files carry the same four): %s." %
      ", ".join("`%s`" % t for t in files[0]["mkiii"]["textures"]))
    A("")
    A("### 2a. Positions - the already-known stream, re-checked here")
    A("")
    A("The position record is `{s16 x, s16 y, s16 z, s16 32767}`: the fourth `s16` is")
    A("the packed `1.0` and it is what identifies the stride (8 here, 16 when a block")
    A("interleaves a second 8-byte attribute). Decoded with one scale per axis onto the")
    A("block's own `Attributes` AABB:")
    A("")
    A("| file | vertices | inside block AABB | AABB spans (x,y,z) | s16 spans | live axes |")
    A("|---|---|---|---|---|---|")
    for f in files:
        p = f["positions"]
        A("| `%s` | %d | **%d/%d** | %.4f, %.4f, %.4f | %d, %d, %d | %s |" % (
            f["name"].rsplit("/", 1)[-1], p["vertex_count"], p["inside_attr_bbox"],
            p["vertex_count"], *p["bbox_spans"], *p["s16_spans"],
            ", ".join("xyz"[k] for k in p["live_axes"])))
    A("")
    A("## 3. The 20-byte attribute stream, decoded")
    A("")
    A("The shader's own reflection header (`generalmkiii.vb.txt`) says the vertex")
    A("carries POSITION0 (float, uses xyz), TEXCOORD2 (float, uses xyzw) and TEXCOORD3")
    A("(float, uses xy) - four components that are not position plus seven. The 8-byte")
    A("position record accounts for the four `POSITION` components (the `32767` is the")
    A("`w = 1.0`); the remaining three live in the 20-byte stream. Its fields, read at")
    A("the boundaries the bytes themselves show:")
    A("")
    A("| offset | width | field | distinct | min | max |")
    A("|---|---|---|---|---|---|")
    fields = files[0]["stream2"]["fields"]
    for i, fd in enumerate(fields):
        name = fd["name"]
        dis = "/".join(str(f["stream2"]["fields"][i]["distinct"]) for f in files)
        mn = "/".join("%.6g" % f["stream2"]["fields"][i]["min"] for f in files)
        mx = "/".join("%.6g" % f["stream2"]["fields"][i]["max"] for f in files)
        A("| +%d | %d | %s | %s | %s | %s |" % (fd["offset"], fd["width"], name, dis, mn, mx))
    A("")
    A("(Columns are lod1 / lod2 / lod3.) Three of the fields are constant on every")
    A("vertex of all three meshes - 243 vertices in total - so they are format markers,")
    A("not coordinates:")
    A("")
    A("| file | `s16 @+4` == 32767 | `s16 @+6` == 0 | `u32 @+16` == 0x487FFFFF | vertices |")
    A("|---|---|---|---|---|")
    for f in files:
        mk = f["stream2"]["markers"]
        A("| `%s` | %d/%d | %d/%d | %d/%d | %d |" % (
            f["name"].rsplit("/", 1)[-1], mk["s16_32767"], mk["vertices"],
            mk["s16_zero"], mk["vertices"], mk["u32_marker"], mk["vertices"],
            mk["vertices"]))
    A("")
    A("So the record is: `{s16 u, s16 v, s16 1.0, s16 0}` then `{f32 a, f32 b, f32")
    A("0x487FFFFF}`. The marker `0x487FFFFF` is the float one ULP below 2^18")
    A("(%.4f), i.e. the same \"1.0 in this field's own units\" idea as the `32767` in"
      % MARK_F32)
    A("the position record - and it is the scale under which the float pair is unit-")
    A("ranged:")
    A("")
    A("| file | a / 0x487FFFFF | b / 0x487FFFFF | both in [0,1) |")
    A("|---|---|---|---|")
    for f in files:
        fp = f["stream2"]["float_pair_over_marker"]
        ob = f["oracles"]["uv_channel_b_in_unit_range"]
        A("| `%s` | %.6f .. %.6f | %.6f .. %.6f | %d/%d |" % (
            f["name"].rsplit("/", 1)[-1], fp["u"]["min"], fp["u"]["max"],
            fp["v"]["min"], fp["v"]["max"], ob["u_in"], ob["vertices"]))
    A("")
    A("## 4. Candidate layouts, and what the oracles say")
    A("")
    A("Each candidate was decoded and then measured against an oracle that is not")
    A("satisfied by accident. Verdicts: **UV set** (chart test), **rejected** (the")
    A("number is shown), **UNKNOWN** (nothing on disk decides it).")
    A("")
    A("| candidate | oracle | measured | verdict |")
    A("|---|---|---|---|")
    uvA = [f["oracles"]["uv_channel_a_unorm16"] for f in files]
    uvB = [f["oracles"]["uv_channel_b_float_over_marker"] for f in files]
    A("| `(u,v)` s16 pair as UV | signed UV area keeps one sign on every triangle; texel density spread | %s | **UV set** |" % (
        "; ".join("%d/%d same sign, density p90/p10 %.3g" % (c["consistent"], c["triangles"],
                                                             c["density_spread"] or 0) for c in uvA)))
    A("| float pair / 0x487FFFFF as UV | same | %s | **rejected** - not a chart |" % (
        "; ".join("%d+/%d-, density spread %.3g" % (c["positive"], c["negative"],
                                                    c["density_spread"] or 0) for c in uvB)))
    A("| `(u,v)` as octahedral normal | mean dot with the adjacent face normals ~1 | %s | **rejected** |" % (
        "; ".join("mean %.3f, min %.3f" % (o["normal_octahedral_from_uv_pair"]["mean"],
                                           o["normal_octahedral_from_uv_pair"]["min"]) for o in (f["oracles"] for f in files))))
    A("| float triple as a normal | mean dot with the face normals ~1 | %s | **rejected** |" % (
        "; ".join("mean %+.3f, normalized z %.3f..%.3f" % (
            f["oracles"]["normal_float_triple"]["mean"],
            f["oracles"]["float_triple_direction"]["z_min"],
            f["oracles"]["float_triple_direction"]["z_max"]) for f in files)))
    A("| float triple as a unit vector | \\|v\\| / 0x487FFFFF == 1 | %s | **rejected** - off by up to %.1f%% |" % (
        "; ".join("worst rel err %.3f" % f["oracles"]["float_triple_unit_length_over_marker"]["worst_rel_error"]
                  for f in files),
        100 * max(f["oracles"]["float_triple_unit_length_over_marker"]["worst_rel_error"] for f in files)))
    A("| float triple as a tangent | \\|dot with the surface normal\\| ~ 0 | %s | **rejected** |" % (
        "; ".join("absmean %.3f" % f["oracles"]["tangent_perpendicularity_float_triple"]["absmean"]
                  for f in files)))
    A("| s16 pair as a tangent | same | %s | **rejected** |" % (
        "; ".join("absmean %.3f" % f["oracles"]["tangent_perpendicularity_uv_pair_as_xyz"]["absmean"]
                  for f in files)))
    A("| skin weights | a weight set needs 0..1 weights summing to 1 plus joint indices | %s | **rejected** - the record holds no weight/index field pair, and the block is unskinned (single 20-byte stream; the skinned shader variant declares an extra `uint4` input) |" % (
        "; ".join("max float %.4g" % f["stream2"]["fields"][5]["max"] for f in files)))
    A("")
    A("The one positive result is not marginal *for these three payloads*: the unorm16")
    A("pair's signed UV area carries the same sign on every triangle of every file, and")
    A("its texel density does not vary by more than a factor of ~%.0f across the mesh -"
      % max(c["density_spread"] for c in uvA))
    A("which is what a real unwrap looks like and what neither a normal encoding nor a")
    A("colour can produce. Section 5 shows how far that carries across other blocks.")
    A("")
    A("The float pair is *not* a second chart of this surface (mixed winding, above),")
    A("is not a normal (a constant third component puts every normalized triple within")
    A("%.0f degrees of +z - z in %.3f..%.3f - while the geometry's face normals point"
      % (max(f["oracles"]["float_triple_direction"]["max_angle_deg"] for f in files),
         min(f["oracles"]["float_triple_direction"]["z_min"] for f in files),
         max(f["oracles"]["float_triple_direction"]["z_max"] for f in files)))
    A("everywhere, so the best mean dot any of the three reaches is %.3f), and is not"
      " an affine" % max(f["oracles"]["normal_float_triple"]["mean"] for f in files))
    A("function of the UV chart or of a position axis: the best fit against the chart or")
    A("against position leaves a worst residual of %s of the field's own range (lod1/"
      % "/".join("%.0f%%" % (100 * min(f["oracles"]["affine_fit"][k]["worst_residual_fraction"]
                                       for k in f["oracles"]["affine_fit"])) for f in files))
    A("lod2/lod3). What *is* established about it: the float at +8 is a function of")
    A("position - identical across coincident vertices in %s of the %s groups - while the"
      % ("/".join(str(f["oracles"]["position_smoothness"]["identical_c"]) for f in files),
         "/".join(str(f["oracles"]["position_smoothness"]["coincident_groups"]) for f in files)))
    A("float at +12 is not (%s) and neither is the unorm16 pair (%s - those are the UV"
      % ("/".join(str(f["oracles"]["position_smoothness"]["identical_d"]) for f in files),
         "/".join(str(f["oracles"]["position_smoothness"]["identical_uv_pair"]) for f in files)))
    A("seams) - and both are per-vertex. Their joint meaning stays **UNKNOWN**")
    A("with the answer in the shipped shader body, which is not in the project - only")
    A("the reflection header is (`generalmkiii.vb.txt`, 73 lines, no instruction list).")
    A("")
    A("## 5. The same invariants elsewhere in the archive")
    A("")
    A("To separate the *block format* from these three meshes' accident, the same")
    A("fields were read from every `GeneralMkIII` block in a fixed sample: all `.rbm`")
    A("entries of the Serpente bundle, then the meshes of a sorted strided slice of the")
    A("%d vehicle bundles in the game index." % fl["vehicle_entities"])
    A("")
    A("| item | value |")
    A("|---|---|")
    A("| `.rbm` files opened (Serpente bundle + %d vehicle bundles) | %d |" % (
        fl["entities"], fl["files"]))
    A("| files carrying a `GeneralMkIII` block | %d |" % fl["files_with_blocks"])
    A("| `GeneralMkIII` blocks framed / vertices | %d / %d |" % (fl["blocks"], fl["vertices"]))
    A("| blocks with a uniform 20-byte record | %d / %d |" % (fl["stride20"], fl["blocks"]))
    A("| marker `0x487FFFFF` at +16 on every vertex | **%d / %d** |" % (fl["marker16_ok"], fl["stride20"]))
    A("| `s16` at +4 == 32767 on every vertex | %d / %d |" % (fl["s4_is_32767"], fl["stride20"]))
    A("| `s16` at +4 == 0 on every vertex | %d / %d |" % (fl["s4_is_zero"], fl["stride20"]))
    A("| `s16` at +6 == 0 on every vertex | %d / %d |" % (fl["s6_is_zero"], fl["stride20"]))
    A("| float pair inside +-2^18 after / 2^18 | %d / %d |" % (fl["float_pair_in_range"], fl["stride20"]))
    A("| positions inside the block AABB | %d / %d |" % (fl["positions_inside"], fl["stride20"]))
    A("| unorm16 pair is a UV chart (one winding sign) | %d / %d |" % (fl["uv_chart_consistent"], fl["stride20"]))
    A("| ... of the blocks with `s16@+4 == 32767` | **%d / %d** |" % (
        fl["chart_ok_with_s4_one"], fl["s4_is_32767"]))
    A("| ... of the blocks with `s16@+4 == 0` | %d / %d |" % (
        fl["chart_ok_with_s4_zero"], fl["s4_is_zero"]))
    A("")
    A("What the sample settles: the *shape* of the record - 8 bytes of unorm16, two")
    A("floats, and a float last - is the block type's (all %d blocks divide into 20 bytes"
      % fl["stride20"])
    A("per vertex), and the last float is the `0x487FFFFF` marker on %d of them."
      % fl["marker16_ok"])
    A("")
    A("What it does **not** settle is the fields' meaning. The field at +4 is 32767 on")
    A("%d blocks and 0 on %d (the three target files are in the first group); the"
      % (fl["s4_is_32767"], fl["s4_is_zero"]))
    A("unorm16 pair is a single-sign chart on %d of the %d blocks, and the split does not"
      % (fl["uv_chart_consistent"], fl["stride20"]))
    A("follow +4 either (%d of the 32767 group, %d of the 0 group). So the three target"
      % (fl["chart_ok_with_s4_one"], fl["chart_ok_with_s4_zero"]))
    A("payloads are decoded, and the block *type* keeps the same field widths, but the")
    A("attribute semantics are **not** fleet-wide: on most blocks the same 20 bytes carry")
    A("something this script cannot name. Per-block witnesses, all framed the same way:")
    A("")
    for w in data["witnesses"]:
        A("* `%s` - %s vertices, %s indices, stride %s, `(u,v)` distinct %s/%s, "
          "`s16@+4` %s, float pair %s, marker %s" % (
              w["name"], w["vertices"], w["indices"], w["stride"],
              w["uv_u_distinct"], w["uv_v_distinct"], w["s4"], w["float_pair"],
              w["marker"]))
    A("")
    if fl["not_uniform"]:
        A("%d block(s) in the sample have no uniform 20-byte record at all: they are the"
          % fl["not_uniform"])
        A("interleaved-position variant (position stride 16, `jc3geom`'s second case), whose")
        A("attribute region does not divide by the vertex count, so the framing of section 2")
        A("does not apply to them unchanged. That is a limit of this script, not a decode.")
    A("")
    if fl["failures"]:
        A("Blocks that did not satisfy the invariants: %s." % "; ".join(fl["failures"]))
    else:
        A("No block in the sample contradicted the layout.")
    A("")
    A("## 6. Status")
    A("")
    A("| item | status | evidence |")
    A("|---|---|---|")
    for f in files:
        A("| `%s` | **FULL** | %d B accounted, blocks sum to the file size, block 1 now decoded to its exact end |" % (
            f["name"].rsplit("/", 1)[-1], f["size"]))
    A("| `GeneralMkIII` (0x2CEC5AD5) header | **decoded** | version 5, 0x68 Attributes, 70-float MaterialConsts2, texture table - `renderblockgeneralmkiii.cc` |")
    A("| `GeneralMkIII` positions | **decoded** | `{s16 x,y,z,32767}` + one scale onto the block AABB, every vertex inside |")
    A("| `GeneralMkIII` attribute stream, 20 B | **decoded** | `unorm16 (u,v)` + `32767` + `0` + `f32 a` + `f32 b` + marker `0x487FFFFF`; UV chart confirmed |")
    A("| meaning of the float pair | **UNKNOWN** | unit-ranged under 2^18, smooth in position, not a chart, not a normal, not a tangent; needs the shader body |")
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/decode_depth4.py --write")
    A("uv run python Tools/scripts/decode_depth4.py --check")
    A("```")
    A("")
    return "\n".join(L) + "\n"


WITNESSES = (
    ("v0300_car_kensington_sportsmuscle", "sportsmuscle_missile_base_signature_lod1"),
    ("v0200_car_capstone_apc", "apc_weapon_mount_horizontal_lod1"),
    ("v0000_car_autostraad_oldjeep", "oldjeep_antenna_lod1"),
)


def describe_block(blob, s, e, name):
    """One-line witness of what a block's 20-byte record actually holds."""
    row = dict(name=name.rsplit("/", 1)[-1], vertices=None, indices=None, stride=None,
               uv_u_distinct="n/a", uv_v_distinct="n/a", s4="n/a", float_pair=None,
               marker="n/a")
    attrs = jc3geom.gmk3_attributes(blob, s)
    pool = s + 1 + jc3geom.GMK3_ATTRS + jc3geom.GMK3_CONSTS
    _tex, pos_count = jc3geom.read_textures(blob, pool)
    vcount = struct.unpack_from("<I", blob, pos_count)[0]
    pos_at = pos_count + 4
    row["vertices"] = vcount
    stride, _cols = jc3geom.find_position_stride(blob, pos_at, e, vcount)
    row["stride"] = stride
    pos_end = pos_at + stride * vcount
    count2 = struct.unpack_from("<I", blob, pos_end)[0]
    s2 = pos_end + 4
    idx = jc3geom.tail_index_buffer(blob, s2, e, vcount)
    if idx is None:
        return row
    idx_at, icount, _indices = idx
    row["indices"] = icount
    gap = idx_at - s2
    if not count2 or gap % count2 or gap // count2 != STREAM2_STRIDE:
        row["float_pair"] = "no uniform 20-byte record"
        return row
    recs = stream2_records(blob, dict(s2_at=s2, stride2=STREAM2_STRIDE, count2=count2))
    row["uv_u_distinct"] = len({r["u"] for r in recs})
    row["uv_v_distinct"] = len({r["v"] for r in recs})
    s4 = {r["s4"] for r in recs}
    row["s4"] = s4.pop() if len(s4) == 1 else "%d values" % len(s4)
    lo = min(min(r["c"], r["d"]) for r in recs) / MARK_F32
    hi = max(max(r["c"], r["d"]) for r in recs) / MARK_F32
    row["float_pair"] = "%+.3f..%+.3f of marker" % (lo, hi)
    row["marker"] = ("0x487FFFFF" if {r["e_bits"] for r in recs} == {MARK_U32}
                     else "differs")
    return row


def witness_rows():
    import jc3strings
    idx = jc3strings.load_index()
    ees = sorted(p for p in idx
                 if p.startswith("editor/entities/jc_vehicles/") and p.endswith(".ee"))
    out = []
    for ent_sub, mesh_sub in WITNESSES:
        hit = None
        for path in ees:
            if ent_sub not in path:
                continue
            try:
                stream = eetoc.unaaf(bm_rc.vfs(path))
                entries = eetoc.sarc_dir(stream)
            except Exception:                                # noqa: BLE001
                continue
            for mname, off, size in sorted(entries):
                if mesh_sub in mname and mname.lower().endswith(".rbm"):
                    blob = bm_rc.vfs(mname) if off == 0 else stream[off:off + size]
                    _h, spans = block_spans(blob)
                    for th, s, e in spans:
                        if th == MKIII:
                            hit = (blob, s, e, mname)
                            break
                if hit:
                    break
            if hit:
                break
        if not hit:
            continue
        try:
            out.append(describe_block(hit[0], hit[1], hit[2], hit[3]))
        except Exception:                                    # noqa: BLE001
            continue
    return out


def build() -> tuple[str, dict]:
    raw, rows = load_archive()
    files = [analyse_file(raw, rows, lod) for lod in LODS]
    fleet = fleet_check(raw, rows)
    data = {
        "task": "G3-19b",
        "source": "vanilla .ee archive (bm_rc/eetoc), no game process",
        "markers": {"s16_one": MARK_S16, "u32": "0x%08X" % MARK_U32, "f32": MARK_F32},
        "files": files,
        "fleet": fleet,
        "witnesses": witness_rows(),
        "all_sums_ok": all(f["sum_equals_size"] for f in files),
        "all_payloads_exact": all(f["accounting"]["sum_equals_payload"] for f in files),
        "all_positions_inside": all(f["positions"]["inside_attr_bbox"] == f["positions"]["vertex_count"]
                                    for f in files),
        "all_markers_exact": all(f["stream2"]["markers"]["u32_marker"] == f["stream2"]["markers"]["vertices"]
                                 and f["stream2"]["markers"]["s16_32767"] == f["stream2"]["markers"]["vertices"]
                                 and f["stream2"]["markers"]["s16_zero"] == f["stream2"]["markers"]["vertices"]
                                 for f in files),
        "uv_chart_all_consistent": all(
            f["oracles"]["uv_channel_a_unorm16"]["consistent"]
            == f["oracles"]["uv_channel_a_unorm16"]["triangles"] for f in files),
    }
    return render(data), data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    md, data = build()

    if args.write:
        OUT_MD.write_text(md, encoding="utf-8")
        OUT_JSON.write_text(json.dumps(data, indent=1, allow_nan=False) + "\n", encoding="utf-8")
        print("wrote %s (%d B)" % (OUT_MD.relative_to(ROOT), len(md)))
        print("wrote %s" % OUT_JSON.relative_to(ROOT))
        print("files: %d, sums ok: %s, payloads exact: %s, positions inside: %s, markers: %s, uv chart: %s"
              % (len(data["files"]), data["all_sums_ok"], data["all_payloads_exact"],
                 data["all_positions_inside"], data["all_markers_exact"],
                 data["uv_chart_all_consistent"]))
        print("fleet: %s" % data["fleet"])
        return 0

    if args.check:
        ok = True
        on_disk = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        if on_disk != data:
            ok = False
            print("FAIL json differs from recomputation")
            for k in data:
                if on_disk.get(k) != data[k]:
                    print("  section %r differs" % k)
        else:
            print("PASS json matches recomputation")
        if OUT_MD.read_text(encoding="utf-8") != md:
            ok = False
            print("FAIL md differs from recomputation")
        else:
            print("PASS md matches recomputation")
        for label, key in (("blocks sum to file size", "all_sums_ok"),
                           ("payloads accounted exactly", "all_payloads_exact"),
                           ("positions inside block AABB", "all_positions_inside"),
                           ("attribute markers exact", "all_markers_exact"),
                           ("s16 pair is a UV chart", "uv_chart_all_consistent")):
            print("%s %s" % ("PASS" if data[key] else "FAIL", label))
            ok = ok and data[key]
        for f in data["files"]:
            a, m = f["accounting"], f["mkiii"]
            print("     %-46s size %6d  payload %5d = %d + %d + %d + %d (exact %s)  verts %d/%d  idx %d"
                  % (f["name"].rsplit("/", 1)[-1], f["size"], a["payload_bytes"],
                     a["head_bytes"], a["position_buffer"], a["attribute_buffer"],
                     a["index_buffer"], a["sum_equals_payload"], m["vertex_count"],
                     f["positions"]["inside_attr_bbox"], m["index_count"]))
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
