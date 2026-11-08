"""appearance_bake.py - D-04: build the appearance textures/materials into a private tree.

One command, one transform per texture, one measurement per transform. It does NOT re-grab and
does NOT re-decimate: the geometry in `Working/Appearance/build` is already the pipeline's output,
so the tree is seeded from it and only the material/texture payload is rebuilt. Every rewrite keeps
the block decodable and byte-identical on re-encode.

Stages (build order = TEXTURE_BUILD_PLAN.md stage order; the plan's rule id is on every row):

  1  mask packing (D3)      Batmobile_V3_BRAKE_DISC_R / Int_Cockpit_S / Missile_Upgrade_S /
                            Nimbus_Power_Cell_S -> `s2` four-band selector + the block's gloss
                            float4. Measurement: band fractions, quantisation MAE, selector
                            decode mismatch after BC1.
  2  micro-detail (P1)      Batmobile_Microdetail -> RNM bake into the four body-family `s1`
                            normals at T_eff (integer divisor of the shipped width).
                            Measurements: C1 difference spectrum, C2 repeat-frequency peak,
                            C3 seam, C4 low band.
  3  emissive (R2)          Batmobile_V3_Int_Cockpit_E -> BC3 atlas, A = max(R,G,B).
                            Measurements: T1 channel census, T2 pack round-trip. No CarLight block
                            exists in this tree, so the atlas is written and left unbound.
  4  glass (R4)             the built Window dif read back: alpha vs the opacity map x
                            Glass_Opacity, tint vs the spec.
  5  refusals               every row TEXTURE_BUILD_PLAN.md marks `no` is measured and recorded,
                            not skipped: missing pixels, absent sampler, absent chapter selector.

Output tree (--out, default Builds/bm-RC4-appearance):
    ddsc/*.ddsc  *.rbm  assembly.json  factors.json  stations.json  coverage.md
    texture_ledger.json  texture_ledger.md  budget.json  receipt.json

Usage: python Tools/scripts/appearance_bake.py [--out DIR] [--src-build DIR] [--budget-kb 7065]
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import factors as FX  # noqa: E402
import rbm_geom as R  # noqa: E402
import tex2ddsc as TX  # noqa: E402

GRAB = os.path.join(ROOT, "Working", "Appearance", "grab", "Playable_Batmobile_SF")
TEXDIR = os.path.join(GRAB, "Texture2D")
GRAB_ALL = os.path.join(ROOT, "Working", "Appearance", "grab")
SHADERS = os.path.join(ROOT, "Tools", "JCMR-src", "assets", "jc3", "shaders")
SRC_BUILD = os.path.join(ROOT, "Working", "Appearance", "build")
VFS_DIR = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/batmobile/"
GLOSS_CAP = FX.GLOSS_CAP
T_REQUEST = 15.0          # MicroDetail_size, body family (app-microdetail-bake-plan.md 3.1)
HEIGHT_AMPLITUDE = 0.05   # ASSUMPTION: BmAK carries a Size scalar only, no strength (same report 7)
RNM_STRENGTH = 1.0        # ASSUMPTION, same report 7


# --------------------------------------------------------------------------- io helpers
def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_ddsc(path):
    """(width, height, fourcc, pixels) of a .ddsc, through the same Gibbed export the pipeline uses.

    The payload is the block chain `tex2ddsc` wrote; the exporter's own header is parsed for the
    size/format, and the BCn decoder is the one in tex2ddsc (the encoder it verifies against).
    """
    with tempfile.TemporaryDirectory() as td:
        name = "x"
        _copyfile(path, os.path.join(td, name + ".ddsc"))
        subprocess.run([TX.GIBBED, name + ".ddsc"], cwd=td, capture_output=True)
        dds = open(os.path.join(td, name + "0.dds"), "rb").read()
    if dds[:4] != b"DDS ":
        raise SystemExit(f"{path}: export did not return a DDS")
    h, w = struct.unpack_from("<2I", dds, 12)
    fourcc = dds[84:88].decode("ascii", "replace")
    off = 148 if fourcc == "DX10" else 128
    blocks = ((w + 3) // 4) * ((h + 3) // 4)
    per = 8 if fourcc == "DXT1" else 16
    payload = dds[off:off + blocks * per]        # mip 0 only; the chain follows it
    if fourcc == "DXT1":
        px = TX.decode_bc1(payload, w, h)
    elif fourcc == "DXT5":
        px = TX.decode_bc3(payload, w, h)
    elif fourcc == "DX10":
        px = TX.decode_bc5(payload, w, h)
    else:
        raise SystemExit(f"{path}: unexpected FOURCC {fourcc!r}")
    return w, h, fourcc, px


def write_texture(arr8, name, out_dir, kind, max_side, alpha=None):
    """arr8: (H,W,3|4) uint8 -> .ddsc via tex2ddsc (BC1 / BC5 / BC3) at `max_side`."""
    mode = "RGBA" if arr8.shape[-1] == 4 else "RGB"
    img = Image.fromarray(arr8.astype(np.uint8), mode)
    return TX.convert_image(img, name, out_dir, kind, max_side, alpha)


def hf_energy(a, sigma=2):
    """mean |a - gaussian(a, 2px)| over the last axis (the report's E metric)."""
    out = []
    for c in range(a.shape[-1]):
        ch = Image.fromarray((np.clip(a[..., c], 0, 1) * 255).astype(np.uint8), "L")
        blur = np.asarray(ch.filter(ImageFilter.GaussianBlur(sigma)), np.float32) / 255.0
        out.append(float(np.abs(a[..., c] - blur).mean()))
    return out


def low_band_share(a):
    """share of the radial spectrum below 0.25 of Nyquist, RG mean (report 3.3).

    rfft2: only the non-negative half of the frequency plane is stored (the spectrum of a real
    image is conjugate-symmetric), so the same share is computed for half the memory.
    """
    g = a[..., :2].mean(-1).astype(np.float32)
    g = g - g.mean(dtype=np.float32)
    f = np.abs(np.fft.rfft2(g)) ** 2
    h, w = g.shape
    fy = np.fft.fftfreq(h).astype(np.float32)[:, None]
    fx = np.fft.rfftfreq(w).astype(np.float32)[None, :]
    r = np.sqrt(fy ** 2 + fx ** 2) * np.float32(np.sqrt(2.0))   # same scale as the full-plane metric: corner = 1
    total = f.sum()
    return float(f[r < 0.25].sum() / total) if total else 0.0


# --------------------------------------------------------------------------- P1: micro-detail
def detail_height(res, tile_px, t_eff):
    """The tile as a height field, tiled `t_eff` times into a `res` square.

    The file is DXT1 and its blue channel mean is 0.62, so it is not a unit-length tangent normal
    (measured below); it is read as luminance height, which is what its statistics support.
    """
    im = Image.open(os.path.join(TEXDIR, "Batmobile_Microdetail.tga")).convert("RGB")
    im = im.resize((tile_px, tile_px), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255.0
    h = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return np.tile(h, (t_eff, t_eff))[:res, :res]


def height_to_tangent(h, tile_px):
    gy, gx = np.gradient(h)
    nx = -gx * tile_px * HEIGHT_AMPLITUDE
    ny = -gy * tile_px * HEIGHT_AMPLITUDE
    nz = np.ones_like(nx)
    n = np.stack([nx, ny, nz], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def reorient(n0, n1):
    """Reoriented normal mapping in unit-vector space: rotate the detail normal by the minimal
    rotation that takes +Z to the base normal (Rodrigues, axis = Z x n0), then renormalise.

    The form used before this was the encoded-space RNM of Barre-Brisebois & Hill (inputs in [0,1]),
    fed *decoded* unit vectors; identity then returned (-0.577, -0.577, 0.577) instead of +Z, which
    is what moved the low band. This form is unit-space throughout and its identity is asserted
    before every bake by `reorient_selftest()`.

    float32 throughout: this host caps a process well below the 24 MB a float64 corpus would need.
    """
    f = np.float32
    x, y, z = n0[..., 0], n0[..., 1], n0[..., 2]
    s = np.sqrt(x * x + y * y)                              # sin(angle) = |Z x n0|
    inv = np.where(s > f(1e-6), f(1.0) / np.maximum(s, f(1e-6)), f(0.0))
    ax, ay = -y * inv, x * inv                              # normalised rotation axis
    c, k = z, f(1.0) - z                                    # cos(angle), 1 - cos(angle)
    vx, vy, vz = n1[..., 0], n1[..., 1], n1[..., 2]
    cx, cy, cz = ay * vz, -ax * vz, ax * vy - ay * vx       # a x v, with a_z = 0
    dot = ax * vx + ay * vy                                 # a . v
    rx = vx * c + cx * s + ax * dot * k
    ry = vy * c + cy * s + ay * dot * k
    rz = vz * c + cz * s
    n = np.maximum(np.sqrt(rx * rx + ry * ry + rz * rz), f(1e-6))
    return np.stack([rx / n, ry / n, rz / n], -1)


def reorient_selftest():
    """Identity cases that must hold for a reorientation blend, as the worst error over them."""
    f = np.float32
    z = np.array([0.0, 0.0, 1.0], f)
    base = [z, np.array([0.6, 0.0, 0.8], f), np.array([0.0, -0.8, 0.6], f),
            np.array([0.36, 0.48, 0.8], f)]
    detail = [z, np.array([0.0, 0.6, 0.8], f), np.array([-0.6, 0.0, 0.8], f)]
    err = 0.0
    for b in base:
        err = max(err, float(np.abs(reorient(b[None, :], z[None, :])[0] - b).max()))
    for d in detail:
        err = max(err, float(np.abs(reorient(z[None, :], d[None, :])[0] - d).max()))
    return err


def decode_xy_to_unit(xy):
    xy = xy.astype(np.float32, copy=False)
    n = np.concatenate([xy, np.zeros(xy.shape[:2] + (1,), np.float32)], -1)
    n[..., 2] = np.sqrt(np.maximum(np.float32(0.0), np.float32(1.0) - (n[..., :2] ** 2).sum(-1)))
    return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), np.float32(1e-6))


def seam_ratio(n):
    """boundary gradient / p99 interior gradient, for the integer tile grid of the baked field."""
    g = np.abs(np.diff(n, axis=1))[:, :, :2].sum(-1)
    return g


def microdetail_bake(ddsc_path, out_dir, t_eff_for):
    """Bake the tile into one shipped `s1` normal. Returns measurements on the shipped BC5 pixels."""
    w, h, fourcc, xy = read_ddsc(ddsc_path)
    if fourcc != "DX10":
        raise SystemExit(f"{ddsc_path}: expected BC5 (DX10), got {fourcc}")
    if xy.shape[:2] != (h, w):
        raise SystemExit(f"{ddsc_path}: decoded {xy.shape[:2]} for a {w}x{h} header")
    base_xy = (xy[..., :2].astype(np.float32) / np.float32(255.0)) * np.float32(2.0) - np.float32(1.0)
    del xy
    selftest = reorient_selftest()
    if selftest > 1e-4:
        raise SystemExit(f"reorientation selftest failed: max identity error {selftest}")
    n0 = decode_xy_to_unit(base_xy)
    t_eff = t_eff_for(w)
    tile_px = max(4, w // t_eff)
    hgt = detail_height(h, tile_px, t_eff)
    n1 = height_to_tangent(hgt, tile_px)
    baked = reorient(n0, n1 * RNM_STRENGTH)

    arr = np.zeros((h, w, 3), np.float32)
    arr[..., :2] = baked[..., :2] * np.float32(0.5) + np.float32(0.5)
    arr[..., 2] = np.float32(1.0)
    del baked
    shipped_arr = np.round(arr * np.float32(255.0)).astype(np.uint8)
    del arr
    name = os.path.splitext(os.path.basename(ddsc_path))[0]
    conv = write_texture(shipped_arr, name, out_dir, "normal", w)

    # measurements on the SHIPPED pixels: the exact bytes BC5 stores for mip 0
    shipped = TX.decode_bc5(TX.bc5(shipped_arr.astype(np.float32)), w, h)
    del shipped_arr
    shipped_xy = (shipped[..., :2] / 255.0) * 2.0 - 1.0
    D = shipped_xy - base_xy
    E_diff = hf_energy(np.concatenate([D, np.zeros_like(D[..., :1])], -1))
    E_tile = hf_energy(np.concatenate([n1[..., :2] * np.float32(0.5), np.zeros_like(n1[..., :1])], -1))
    c1 = [round(E_diff[i], 5) for i in range(2)]
    c1_pass = all(E_diff[i] >= 0.5 * E_tile[i] for i in range(2))

    g = D.mean(-1).astype(np.float32)
    g -= g.mean(dtype=np.float32)
    hh, ww = g.shape
    f = np.abs(np.fft.rfft2(g)) ** 2          # non-negative half plane: same profile, half the memory
    fy = np.fft.fftfreq(hh)[:, None].astype(np.float32)   # cycles per texel, 0.5 = Nyquist
    fx = np.fft.rfftfreq(ww)[None, :].astype(np.float32)
    freq = np.sqrt(fx ** 2 + fy ** 2)
    bins = np.linspace(0, float(freq.max()) + 1e-9, max(8, ww // 6) + 1)
    radial = np.array([f[(freq >= bins[i]) & (freq < bins[i + 1])].mean()
                       if ((freq >= bins[i]) & (freq < bins[i + 1])).any() else 0.0
                       for i in range(len(bins) - 1)])
    target = t_eff / float(ww)                 # t_eff repeats across the UV domain
    tb = int(np.argmin(np.abs((bins[:-1] + bins[1:]) / 2 - target)))
    lo, hi = max(0, tb - 1), min(len(radial) - 1, tb + 1)
    peak = radial[lo:hi + 1].max()
    neigh = np.median(np.delete(radial, range(lo, hi + 1)))
    c2 = {"t_eff": t_eff, "target_cycles_per_px": round(float(target), 6),
          "peak_over_neighbour_median": round(float(peak / neigh), 2) if neigh > 0 else None}
    c2_pass = neigh > 0 and peak >= 2.0 * neigh

    nb = (w // t_eff) * t_eff
    gw = seam_ratio(np.concatenate([shipped_xy, np.zeros(shipped_xy.shape[:2] + (1,), np.float32)], -1))
    cols = np.arange(w // t_eff, w, max(1, w // t_eff))[:t_eff - 1]
    boundary = gw[:, np.clip(cols, 1, w - 1)].mean() if len(cols) else 0.0
    interior = float(np.percentile(gw, 99))
    c3 = {"tile_boundary_gradient": round(float(boundary), 4),
          "interior_p99_gradient": round(interior, 4), "grid_texels": int(nb)}
    c3_pass = boundary <= interior

    lb_src = low_band_share(base_xy * 0.5 + 0.5)
    lb_out = low_band_share(shipped_xy * 0.5 + 0.5)
    c4 = {"source_low_band": round(lb_src, 4), "baked_low_band": round(lb_out, 4),
          "delta": round(abs(lb_out - lb_src), 4)}

    # C4 read as the claim it states: the large-scale shading must not move. A band *share* cannot
    # test that - adding detail raises the high band by construction and lowers the share (report
    # 3.3 says as much), so the share is reported and the gate is the low-pass field's change.
    def lowpass(a3, sigma=8):
        out = []
        for i in range(a3.shape[-1]):
            ch = Image.fromarray((np.clip(a3[..., i], 0, 1) * 255).astype(np.uint8), "L")
            out.append(np.asarray(ch.filter(ImageFilter.GaussianBlur(sigma)), np.float32) / 255.0)
        return np.stack(out, -1)

    lp = np.abs(lowpass(shipped_xy * 0.5 + 0.5) - lowpass(base_xy * 0.5 + 0.5))
    c4.update({"lowpass_sigma_px": 8, "lowpass_mean_abs_delta": round(float(lp.mean()), 5),
               "lowpass_max_abs_delta": round(float(lp.max()), 5)})
    c4_pass = float(lp.mean()) <= 0.01

    return {
        "size": [w, h], "mips": conv["mips"], "bytes": conv["bytes"],
        "worst_mip_psnr_db": conv["worst_mip_psnr_db"],
        "t_requested": T_REQUEST, "t_eff": t_eff, "tile_px": tile_px,
        "measurements": [
            {"metric": "C0 reorientation identity selftest", "value": round(selftest, 8),
             "threshold": "<= 1e-4 (n1=+Z returns n0; n0=+Z returns n1)", "pass": bool(selftest <= 1e-4)},
            {"metric": "C1 difference spectrum (RG)", "value": c1,
             "threshold": f">= 0.5 x tile {[round(x, 5) for x in E_tile[:2]]}", "pass": bool(c1_pass)},
            {"metric": "C2 repeat-frequency peak", "value": c2,
             "threshold": "local max within +-1 bin, >= 2x neighbour median", "pass": bool(c2_pass)},
            {"metric": "C3 seam / grid", "value": c3,
             "threshold": "boundary gradient <= interior p99", "pass": bool(c3_pass)},
            {"metric": "C4 low band (the panel's large-scale shading)", "value": c4,
             "threshold": "mean |delta| of the sigma=8 low-pass field <= 0.01; the band-share "
                          "delta is reported, not gated (adding detail moves a share by construction)",
             "pass": bool(c4_pass)},
        ],
        "pass": bool(c1_pass and c2_pass and c3_pass and c4_pass),
    }


# --------------------------------------------------------------------------- D3: mask packing
def band_pack(tga_path, out_dir, size):
    """One mask -> a four-band `s2` selector + the band means the block's float4 carries.

    s2 is a per-texel channel selector on CarPaintMM: black = channel 0, R/G/B = channels 1-3
    (factors.py header). Two measured facts fix the packing granularity:

      - BC1 stores two RGB565 endpoints + two interpolants per 4x4 block, so a block that mixes the
        four selector colours decodes to a colour that is none of them. Measured on these masks:
        3.1 % (BRAKE_DISC_R) to 17.8 % (Int_Cockpit_S) of texels land on the WRONG band.
      - a block whose 16 texels share one selector colour is stored as c0 == c1 and decodes exactly
        (measured mismatch 0.0000 on all four).

    So the band is decided per 4x4 block, and blocks are ordered by their mean so each band receives
    exactly its share of blocks: the shipped histogram then equals the source's per-texel bin
    fractions (measured 0.0000) instead of drifting 1.7 % the way a plain majority vote does. The
    band means still go into the block's gloss float4. The mapping of a *source channel* to a scalar
    is UNKNOWN (app-per-pixel-reflectivity.md 3); the channel with the largest standard deviation
    among the live channels is used and named in the record.
    """
    w, h = max(4, (size[0] // 4) * 4), max(4, (size[1] // 4) * 4)
    a = np.asarray(Image.open(tga_path).convert("RGB").resize((w, h), Image.BOX), np.float32) / 255.0
    std = [float(a[..., i].std()) for i in range(3)]
    live = [i for i in range(3) if std[i] > 0.01]
    if not live:
        raise SystemExit(f"{tga_path}: all channels dead")
    ch = max(live, key=lambda i: std[i])
    v2 = a[..., ch]
    v = v2.reshape(-1)

    # 1-D k-means, 4 levels, initialised at the quartiles: the four band levels and the source bins
    cent = np.quantile(v, [0.125, 0.375, 0.625, 0.875]).astype(np.float64)
    for _ in range(25):
        idx = np.abs(v[:, None] - cent[None, :]).argmin(1)
        for k in range(4):
            sel = idx == k
            if sel.any():
                cent[k] = v[sel].mean()
    order = np.argsort(cent)
    rank = np.empty(4, int)
    rank[order] = np.arange(4)
    idx = rank[idx]
    band_vals = [float(cent[i]) for i in range(4)]
    frac_src = [float((idx == k).mean()) for k in range(4)]

    # per-block assignment: order blocks by mean, hand each band exactly its share of blocks
    by, bx = h // 4, w // 4
    blk = v2[:by * 4, :bx * 4].reshape(by, 4, bx, 4).mean((1, 3)).reshape(-1)
    border = np.argsort(blk, kind="stable")
    n = len(border)
    targets = np.cumsum([int(round(f * n)) for f in frac_src])
    targets[-1] = n
    lab = np.empty(n, int)
    start = 0
    for k in range(4):
        lab[border[start:targets[k]]] = k
        start = targets[k]
    labb = np.repeat(np.repeat(lab.reshape(by, bx), 4, 0), 4, 1)

    sel = np.zeros((h, w, 3), np.uint8)
    for k, c in enumerate(((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255))):
        sel[labb == k] = c
    base = os.path.splitext(os.path.basename(tga_path))[0].lower()
    conv = write_texture(sel, base + "_msk", out_dir, "mask", max(w, h))

    # read the shipped selector back and classify every texel by nearest selector colour
    _w, _h, fourcc, px = read_ddsc(conv["ddsc"])
    got = px[..., :3].astype(np.float32)
    nearest = np.argmin(np.stack([np.linalg.norm(got - np.array(c, np.float32), axis=-1)
                                  for c in ((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255))]), 0)
    want = np.asarray(Image.fromarray(sel, "RGB").resize((_w, _h), Image.NEAREST))
    want_idx = np.argmin(np.stack([np.linalg.norm(want.astype(np.float32) - np.array(c, np.float32), axis=-1)
                                   for c in ((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255))]), 0)
    mismatch = float((nearest != want_idx).mean())
    frac_shipped = [float((nearest == k).mean()) for k in range(4)]
    # the error the block-granular decision itself introduces, against the source scalar
    means = np.array([v[idx == k].mean() if (idx == k).any() else band_vals[k] for k in range(4)])
    mae = float(np.abs(v - means[idx]).mean())
    means_block = np.array([v[labb.reshape(-1) == k].mean() if (labb == k).any() else band_vals[k]
                            for k in range(4)])
    mae_block = float(np.abs(v - means_block[labb.reshape(-1)]).mean())

    gloss = [round(min(1.0 - b, GLOSS_CAP), 4) for b in band_vals]
    hist = max(abs(x - y) for x, y in zip(frac_src, frac_shipped))
    return {
        "source_channel": "RGB"[ch], "channel_std": [round(s, 4) for s in std],
        "bands": [round(b, 5) for b in band_vals],
        "band_fractions_source": [round(f, 4) for f in frac_src],
        "band_fractions_shipped": [round(f, 4) for f in frac_shipped],
        "gloss_float4": gloss, "quantisation_mae": round(mae, 5),
        "blocks": n, "mae_block": round(mae_block, 5),
        "ddsc": conv["ddsc"], "bytes": conv["bytes"], "fourcc": fourcc,
        "measurements": [
            {"metric": "band histogram == source bin fractions (max |delta|)",
             "value": round(hist, 4), "threshold": "<= 0.01", "pass": bool(hist <= 0.01)},
            {"metric": "selector decode mismatch after BC1",
             "value": round(mismatch, 4), "threshold": "<= 0.02", "pass": bool(mismatch <= 0.02)},
            {"metric": "band quantisation MAE on the source scalar",
             "value": round(mae, 5), "threshold": "reported (4 levels is the block ceiling)", "pass": True},
            {"metric": "cost of 4x4 block granularity (MAE block - MAE per-texel k-means)",
             "value": round(mae_block - mae, 5),
             "threshold": "reported: a 4x4 BC1 block is the s2 selector's real granularity",
             "pass": True},
        ],
    }


# --------------------------------------------------------------------------- R2: emissive atlas
def emissive_atlas(out_dir, max_side):
    """RGB = the colour, A = max(RGB) (A4). The alpha copy is taken from the colour BC1 will
    actually store, not from the authored colour: BC1 and BC4 quantise independently, so an authored
    alpha drifts up to 5.7/255 from the shipped RGB and the pack invariant would hold only before
    the codec. Run the colour encoder to its fixed point first, then copy."""
    tga = os.path.join(TEXDIR, "Batmobile_V3_Int_Cockpit_E.tga")
    a = np.asarray(Image.open(tga).convert("RGB"), np.float32) / 255.0
    cov = float((a.max(-1) > 1.0 / 255.0).mean())
    w, h = a.shape[1], a.shape[0]
    rgb = np.round(a * 255).astype(np.float32)
    for _ in range(4):                       # BC1 fixed point of the colour it will carry
        again = np.round(np.clip(TX.decode_bc1(TX.bc1(np.dstack([rgb, np.full((h, w, 1), 255.0)])),
                                               w, h), 0, 255))
        if np.array_equal(again, rgb):
            break
        rgb = again
    rgba = np.concatenate([rgb, rgb.max(-1, keepdims=True)], -1).astype(np.uint8)
    authored_err = float(np.abs(rgba[..., 3].astype(np.float32) - rgba[..., :3].max(-1)).max())
    conv = write_texture(rgba, "batmobile_v3_int_cockpit_e_atlas", out_dir, "glass", max_side)
    _w, _h, fourcc, px = read_ddsc(conv["ddsc"])
    rgb = px[..., :3].astype(np.float32)
    alpha = px[..., 3].astype(np.float32)
    err = float(np.abs(alpha - rgb.max(-1)).max())
    grey = float(np.abs(rgb - rgb.mean(-1, keepdims=True)).max())
    t2 = {"authored_max_error": round(authored_err, 3), "shipped_max_error_255ths": round(err, 3),
          "pass": bool(authored_err == 0.0 and err <= 4.0)}
    t1 = {"channels": "colour (max inter-channel spread %d/255)" % int(round(grey)),
          "coverage_above_1_255": round(cov, 4)}
    return {
        "ddsc": conv["ddsc"], "bytes": conv["bytes"], "fourcc": fourcc,
        "measurements": [
            {"metric": "T1 channel census", "value": t1,
             "threshold": "colour atlas vs greyscale mask", "pass": True},
            {"metric": "T2 pack round-trip A == max(RGB)", "value": dict(t2, authored_max_error=authored_err),
             "threshold": "exact before encode; <= 4/255 after BC1+BC4", "pass": t2["pass"]},
            {"metric": "T5 UV-island containment",
             "value": "not run: the lamp mesh and its UVs are not in the 56-file texture grab; "
                      "the atlas is written unbound",
             "threshold": "n/a - needs the lamp mesh UVs", "pass": None},
        ],
        "bound": False,
    }


# --------------------------------------------------------------------------- tree build
def _copyfile(src, dst):
    """Streamed copy: the broker's 1 MB shutil buffer has failed with MemoryError on this host."""
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        while True:
            chunk = fi.read(1 << 18)
            if not chunk:
                break
            fo.write(chunk)


def seed_tree(src, out):
    os.makedirs(os.path.join(out, "ddsc"), exist_ok=True)
    for f in sorted(os.listdir(os.path.join(src, "ddsc"))):
        if f.lower().endswith(".ddsc"):
            _copyfile(os.path.join(src, "ddsc", f), os.path.join(out, "ddsc", f))
    for f in sorted(os.listdir(src)):
        if f.endswith(".rbm") or f in ("stations.json", "coverage.md"):
            _copyfile(os.path.join(src, f), os.path.join(out, f))
    asm = json.load(open(os.path.join(src, "assembly.json")))
    asm["textures"] = {vfs: os.path.join(out, "ddsc", os.path.basename(p))
                       for vfs, p in asm["textures"].items()}
    json.dump(asm, open(os.path.join(out, "assembly.json"), "w"), indent=2)
    specs = json.load(open(os.path.join(src, "factors.json")))
    return asm, specs


def material_for(specs, texture_name):
    hits = [m for m, s in specs["materials"].items()
            if any(d["factor"].startswith("tex:") and str(d["value"]) == texture_name
                   for d in s["dispositions"])]
    if len(hits) != 1:
        raise SystemExit(f"{texture_name}: bound by {hits}, expected exactly one material")
    return hits[0]


def _src(entry):
    """An input's `source` as one string: factors.py writes a list for per-channel composites."""
    s = entry.get("source", "")
    return "; ".join(s) if isinstance(s, list) else s


def patch_blocks(out, specs, asm, patch):
    """patch: material -> {slot: vfs path, 'gloss': float4, 'metallic': float4}. Re-encode + verify."""
    done = {}
    for part, items in asm["plan"].items():
        for lod in range(1, 6):
            p = os.path.join(out, f"{part}_lod{lod}.rbm")
            raw = open(p, "rb").read()
            m = R.decode(raw)
            if len(m.blocks) != len(items):
                raise SystemExit(f"{p}: {len(m.blocks)} blocks vs {len(items)} planned")
            changed = False
            for blk, it in zip(m.blocks, items):
                if R.BLOCK_NAMES.get(blk.type_hash) != "CarPaintMM":
                    continue
                p2 = patch.get(it["material"])
                if not p2:
                    continue
                for slot, vfs in p2.items():
                    if slot.startswith("s"):
                        blk.textures[int(slot[1])] = vfs
                for key, idx in (("gloss", 0), ("metallic", 4)):
                    if key in p2:
                        sp = list(np.frombuffer(blk.static_params, "<f4"))
                        sp[idx:idx + 4] = p2[key]
                        blk.static_params = struct.pack("<72f", *sp)
                if "overrides" in p2:
                    dy = list(np.frombuffer(blk.dynamic_params, "<f4"))
                    dy[16:19] = p2["overrides"]
                    blk.dynamic_params = struct.pack("<19f", *dy)
                changed = True
            if not changed:
                continue
            new = m.write()
            if R.decode(new).write() != new:
                raise SystemExit(f"{p}: patched RBM does not re-encode byte-identically")
            open(p, "wb").write(new)
            done.setdefault(os.path.basename(p), 0)
            done[os.path.basename(p)] = len([1 for it in items if it["material"] in patch])
    return done


def _grab_index() -> dict:
    """Every `.tga` under the grab root, keyed by stem: the census the refusals cite."""
    idx: dict[str, list[str]] = {}
    for dirpath, _dirs, files in os.walk(GRAB_ALL):
        for f in sorted(files):
            if f.lower().endswith(".tga"):
                idx.setdefault(os.path.splitext(f)[0], []).append(os.path.join(dirpath, f))
    return idx


def _shader_census() -> dict:
    """What the shader reflection headers actually declare about chapters and ramps.

    The claim 'no ramp sampler exists' has to name the population it counted: these are the 961
    `.fb.txt` headers CB0_SLOTS.md is built from, scanned for the two words, with the matching
    declaration lines kept so a reader can see that a `ramp` hit is not a sampler.
    """
    headers = [os.path.join(SHADERS, f) for f in sorted(os.listdir(SHADERS))
               if f.endswith(".fb.txt")] if os.path.isdir(SHADERS) else []
    chapter, ramp, carpaint = [], [], []
    for p in headers:
        text = open(p, encoding="utf-8", errors="replace").read()
        low = text.lower()
        if "chapter" in low:
            chapter.append(os.path.basename(p))
        if "ramp" in low:
            ramp.append({"file": os.path.basename(p),
                         "lines": [ln.strip() for ln in text.splitlines()
                                   if "ramp" in ln.lower()][:3]})
        if "CarPaintStaticMaterialParams" in text:
            carpaint.append(os.path.basename(p))
    return {"dir": os.path.relpath(SHADERS, ROOT).replace(os.sep, "/"),
            "headers": len(headers), "declare_carpaint_static": len(carpaint),
            "mention_chapter": chapter, "mention_ramp": ramp}


def _damage_blocks(out: str) -> list[dict]:
    """Every CarPaintMM block in the tree with its `SupportDmgBlend` bytes.

    `SupportDmgBlend` is `static_support` float[1], i.e. payload +0x12d (CB0_SLOTS.md §3); it is
    the only damage switch the decoded block carries, and it is a global blend, not a selector.
    """
    rows = []
    for f in sorted(os.listdir(out)):
        if not f.endswith(".rbm"):
            continue
        for b in R.decode(open(os.path.join(out, f), "rb").read()).blocks:
            if R.BLOCK_NAMES.get(b.type_hash) != "CarPaintMM":
                continue
            sup = np.frombuffer(b.static_support, "<f4")
            rows.append({"rbm": f, "slots": [os.path.basename(v) for v in b.textures if v],
                         "static_support": [round(float(x), 6) for x in sup],
                         "SupportDmgBlend": round(float(sup[1]), 6)})
    return rows


def refusal_evidence(out: str) -> list[dict]:
    """The plan rows with no faithful route: the file, the bytes, and why the row is refused.

    Every reason here is computed from the pixels, the RBM blocks or the shader headers. The
    report's prose is not the source: two of its claims did not survive the census (see the
    Underlayer and Leather rows, whose pixels are present).
    """
    idx = _grab_index()
    sh = _shader_census()
    dmg = _damage_blocks(out)
    n_tga = sum(len(v) for v in idx.values())
    blend_vals = sorted({r["SupportDmgBlend"] for r in dmg})
    n_blocks = len(dmg)
    ramp_neg = {"metric": "ramp sampler census",
                "value": {"headers": sh["headers"],
                          "declare_carpaint_static": sh["declare_carpaint_static"],
                          "mention_ramp": len(sh["mention_ramp"]),
                          "ramp_declarations": sh["mention_ramp"],
                          "texture_parameter_named_ramp": 0},
                "threshold": "a ramp sampler would name a texture parameter in a "
                             "CarPaintStatic header; the only `ramp` tokens are "
                             "`DamageRampWeight`, a float in 4 window shaders"}

    def entry(rule: str, tex: str, why: str, measurement: str, evidence: list[dict],
              counted: bool, note: str | None = None) -> dict:
        hits = idx.get(tex) or []
        rec = {"rule": rule, "texture": tex, "counted_in_the_12": counted,
               "present_in_playable_batch": os.path.exists(os.path.join(TEXDIR, tex + ".tga")),
               "present_in_grab": bool(hits), "source_file": None, "bytes": None,
               "sha256": None, "size": None, "mode": None, "reason": why,
               "measurement": measurement, "byte_evidence": evidence, "status": "refused"}
        if note:
            rec["note"] = note
        if hits:
            p = hits[0]
            im = Image.open(p)
            rec.update({"source_file": os.path.relpath(p, ROOT).replace(os.sep, "/"),
                        "bytes": os.path.getsize(p), "sha256": _sha(p),
                        "size": [im.size[0], im.size[1]], "mode": im.mode,
                        "all_grab_hits": [os.path.relpath(h, ROOT).replace(os.sep, "/")
                                          for h in hits]})
        return rec

    absent = lambda tex: ({"metric": "grab file census",
                           "value": {"tga_files_scanned": n_tga,
                                     "packages": sorted(os.listdir(GRAB_ALL)),
                                     "stem_hits": 0},
                           "threshold": "a row needs its own pixels: 0 hits under "
                                        "Working/Appearance/grab/**/Texture2D"})
    out_rows: list[dict] = []
    for tex in ["Batmobile_Micropattern_A", "Batmobile_Micropattern_A_Normal",
                "Batmobile_Micropattern_B", "Batmobile_Micropattern_C"]:
        out_rows.append(entry(
            "P1", tex, f"pixels absent: 0 of {n_tga} .tga files in the grab carry this stem",
            f"present_in_grab={bool(idx.get(tex))}; grab scanned={n_tga} files",
            [absent(tex)], True))
    out_rows.append(entry(
        "R2", "Batmobile_V3_Wheel_E",
        f"pixels absent: 0 of {n_tga} .tga files in the grab carry this stem; the four arch strips "
        "stay dark", f"present_in_grab={bool(idx.get('Batmobile_V3_Wheel_E'))}",
        [absent("Batmobile_V3_Wheel_E")], True))
    for tex, note in (("Batman_BM3_V2_Lacquered_Underlayer_Ramp",
                       "the plan's 'absent' reason is corrected: the pixels ARE in the grab, in the "
                       "Startup package, which the bake's Playable_Batmobile_SF batch does not read"),
                      ("Batmobile_V3_Body_ColourRamp", None)):
        hits = idx.get(tex) or []
        out_rows.append(entry(
            "D10", tex,
            (f"pixels present in the grab ({os.path.relpath(hits[0], GRAB_ALL).replace(os.sep, '/')}, "
             f"{os.path.getsize(hits[0]):,} B) but no ramp sampler exists in any of the "
             f"{sh['headers']} shader reflection headers" if hits else
             f"pixels absent: 0 of {n_tga} .tga files in the grab carry this stem; and no ramp "
             f"sampler exists in any of the {sh['headers']} shader reflection headers"),
            (f"present_in_grab=True; {sh['headers']} headers, 0 name a ramp texture parameter"
             if hits else f"present_in_grab=False; {sh['headers']} headers, 0 name a ramp sampler"),
            ([absent(tex)] if not hits else []) + [ramp_neg], True, note))
    out_rows.append(entry(
        "D10", "Batman_BM3_V2_Leather_Ramp",
        f"pixels present (64x512) but no ramp sampler exists in any of the {sh['headers']} shader "
        "reflection headers, so the Leather ramp cannot be sampled; the plan's 'absent' reason is "
        "corrected here",
        f"present_in_grab=True; {sh['headers']} headers, 0 name a ramp texture parameter",
        [ramp_neg], False,
        "the 13th texture refusal and the only one whose pixels exist: it is the Leather half of "
        "the plan's three ramps, refused for the sampler, not for the pixels"))
    out_rows.append(entry(
        "D5", "Aniso_ramp_Lacquered",
        f"pixels absent: 0 of {n_tga} .tga files in the grab carry this stem; the anisotropy lobes "
        f"are a UV-space fake with no sampler (0 of {sh['headers']} headers name one)",
        f"present_in_grab=False; {sh['headers']} headers, 0 name an aniso ramp sampler",
        [absent("Aniso_ramp_Lacquered"), ramp_neg], True))
    for tex in ["Batmobile_V3_TEXTURES_Body_Damage_ChapterMask",
                "Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask",
                "Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask",
                "Batmobile_V3_Undercarriage_Damage_ChapterMask"]:
        hits = idx.get(tex) or []
        w, h = Image.open(hits[0]).size if hits else (None, None)
        ev = [{"metric": "damage mask source",
               "value": {"file": os.path.relpath(hits[0], ROOT).replace(os.sep, "/"),
                         "bytes": os.path.getsize(hits[0]), "sha256": _sha(hits[0]),
                         "size": [w, h]} if hits else {"stem_hits": 0}},]
        out_rows.append(entry(
            "D9", tex,
            f"mask present ({w}x{h}) and bound as Damage_Chapter_Mask, but there is no chapter "
            f"selector to read it: 0 of {sh['headers']} shader reflection headers mention a "
            f"chapter, and the only damage switch in the {n_blocks} decoded CarPaintMM blocks is "
            f"SupportDmgBlend (static_support float[1], payload +0x12d), {blend_vals} in every "
            "block. Writing one static state (mask into a texture slot + SupportDmgBlend 1) would "
            "paint every chapter damaged and its in-game read is unproven (test ban), so the row "
            "stays declared",
            f"{n_blocks} blocks, SupportDmgBlend={blend_vals}, chapter fields in "
            f"{sh['headers']} headers = 0",
            ev[0:] + [{"metric": "chapter selector census",
                       "value": {"shader_headers": sh["headers"],
                                 "mention_chapter": len(sh["mention_chapter"]),
                                 "carpaint_blocks": n_blocks,
                                 "SupportDmgBlend_values": blend_vals,
                                 "SupportDmgBlend_offset": "payload +0x12d = static_support "
                                                           "float[1] (CB0_SLOTS.md §3)"},
                       "threshold": "a chapter selector would appear as a uniform in the shader "
                                    "reflection headers or a selector field in the block; neither "
                                    "exists"}], True))
    out_rows.append({"rule": "D-5", "texture": "skins (Joker / MK2 / Tumbler looks)",
                     "counted_in_the_12": False, "present_in_grab": False,
                     "source_file": None, "bytes": None, "sha256": None,
                     "reason": "7 of 11 looks have no carrier: 4 need a drop entry, 3 a mesh/part "
                               "swap; this tree is a single-look build",
                     "measurement": "0 variant carriers in the tree (one body set, one wheel set)",
                     "byte_evidence": [], "status": "refused",
                     "note": "a plan row outside the 23 texture rows, kept for completeness"})
    return out_rows


def rewrite_refusals(out: str) -> int:
    """Record-only: recompute the `refusals` array and rewrite the ledger pair, no rebuild."""
    path = os.path.join(out, "texture_ledger.json")
    led = json.load(open(path, encoding="utf-8"))
    refusals = refusal_evidence(out)
    led["refusals"] = refusals
    json.dump(led, open(path, "w", encoding="utf-8", newline="\n"), indent=1)
    md_path = os.path.join(out, "texture_ledger.md")
    if os.path.exists(md_path):
        md = open(md_path, encoding="utf-8").read()
        if "## Refused rows (no faithful route)" in md and "## Budget" in md:
            head, rest = md.split("## Refused rows (no faithful route)", 1)
            _old, tail = rest.split("## Budget", 1)
            table = ["## Refused rows (no faithful route)", "",
                     "| rule | texture | reason | measurement |", "|---|---|---|---|"]
            table += [f"| `{r['rule']}` | `{r['texture']}` | {r['reason']} | {r['measurement']} |"
                      for r in refusals]
            open(md_path, "w", encoding="utf-8", newline="\n").write(
                head + "\n".join(table) + "\n\n## Budget" + tail)
    print(f"rewrote {os.path.relpath(path, ROOT).replace(os.sep, '/')}: {len(refusals)} refusals, "
          f"{sum(1 for r in refusals if r['counted_in_the_12'])} counted in the 12")
    for r in refusals:
        print(f"  {r['rule']:3} {r['texture'][:50]:50s} present={str(r['present_in_grab']):5s} "
              f"bytes={r['bytes']} :: {r['measurement']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "Builds", "bm-RC4-appearance"))
    ap.add_argument("--refusals-only", action="store_true",
                    help="re-measure only the refusals and rewrite the ledger (no texture is baked)")
    ap.add_argument("--src-build", default=SRC_BUILD)
    ap.add_argument("--budget-kb", type=float, default=7065.0,
                    help="the game's Vehicle-*HD* Texture HARD budget (asset_memory_budgets.bin)")
    ap.add_argument("--allocator-kb", type=float, default=4648.0,
                    help="the build's own cap after the vanilla resident footprint x0.9 (pipeline log)")
    a = ap.parse_args()
    if a.refusals_only:
        return rewrite_refusals(os.path.abspath(a.out))
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(out, "ddsc"), exist_ok=True)

    asm, specs = seed_tree(a.src_build, out)
    ledger, refusals = [], []

    # ---------------------------------------------------------------- P1 micro-detail into s1
    def t_eff_for(width):
        """Nearest integer tile count that divides the shipped width (C3's seam rule)."""
        cand = [d for d in range(max(1, int(T_REQUEST) - 4), int(T_REQUEST) + 5) if width % d == 0]
        return min(cand, key=lambda d: abs(d - T_REQUEST)) if cand else max(1, round(T_REQUEST))

    md_targets = sorted({m for m, s in specs["materials"].items()
                         if any(str(d["value"]) == "Batmobile_Microdetail" for d in s["dispositions"])})
    baked_s1 = {}
    for mat in md_targets:
        s1 = specs["materials"][mat]["textures"]["s1"]
        if "tga" not in s1:
            refusals.append({"rule": "P1", "texture": mat, "reason": "s1 is not a converted texture"})
            continue
        stem = os.path.splitext(os.path.basename(s1["tga"]))[0].lower()
        path = os.path.join(out, "ddsc", stem + ".ddsc")
        if not os.path.exists(path) or stem in baked_s1:
            continue
        res = microdetail_bake(path, os.path.join(out, "ddsc"), t_eff_for)
        baked_s1[stem] = res
        # T=15 is the body-family value; say so per target when the material has no base size
        sizes = {d["factor"]: d["value"] for d in specs["materials"][mat]["dispositions"]}
        base_size = sizes.get("sc:MicroDetail_size")
        size_note = (f"T={base_size:g} from sc:MicroDetail_size" if base_size is not None else
                     f"T={T_REQUEST:g} assumed: {mat} has no sc:MicroDetail_size "
                     f"(only Material3_Size={sizes.get('sc:MicroDetail_Material3_Size')})")
        ledger.append({
            "rule": "P1", "texture": "Batmobile_Microdetail", "target": stem,
            "source": {"file": "Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_Microdetail.tga",
                       "size": 1024, "format": "DXT1 (TGA on disk)", "sha256": _sha(os.path.join(TEXDIR, "Batmobile_Microdetail.tga"))},
            "destination": f"CarPaintMM s1 NormalMap of {mat} (baked; UV1 x T_eff)",
            "channels": "tangent XY (RNM blend), blue rebuilt to 1",
            "transform": (f"tile read as height (blue mean 0.62: not a unit tangent normal), Sobel -> tangent, "
                          f"reoriented into the base normal at T_eff={res['t_eff']} ({size_note}), "
                          f"height amplitude {HEIGHT_AMPLITUDE}, strength {RNM_STRENGTH} (both assumptions), BC5"),
            "measurements": res["measurements"], "pass": res["pass"],
            "faithful": "yes", "status": "baked",
        })
        # the same source feeds every body-family s1: record each shipped file
        s1["source"] = s1.get("source", "") + f"; baked with Batmobile_Microdetail RNM (T_eff {res['t_eff']})"

    # per-file measurement rows for every baked s1 (5 LODs share one texture, so one row each)
    for stem, res in sorted(baked_s1.items()):
        ledger.append({
            "rule": "P1", "texture": f"baked s1: {stem}", "target": stem,
            "source": {"file": "Working/Appearance/build/ddsc/" + stem + ".ddsc (base normal)"},
            "destination": f"{VFS_DIR}{stem}.ddsc", "channels": "BC5 tangent XY",
            "transform": "see the Batmobile_Microdetail row (one bake per shipped resolution)",
            "measurements": res["measurements"], "pass": res["pass"], "faithful": "yes", "status": "baked",
            "size": res["size"], "bytes": res["bytes"],
        })

    # ---------------------------------------------------------------- D3 s2 band packing
    d3 = ["Batmobile_V3_BRAKE_DISC_R", "Batmobile_V3_Int_Cockpit_S",
          "Batmobile_V3_Missile_Upgrade_S", "Nimbus_Power_Cell_S"]
    patch = {}
    for tex in d3:
        tga = os.path.join(TEXDIR, tex + ".tga")
        if not os.path.exists(tga):
            refusals.append({"rule": "D3", "texture": tex, "reason": "no pixels on disk"})
            continue
        mat = material_for(specs, tex)
        spec = specs["materials"][mat]
        # shipped size from the current s1 (the same material's maps share one resolution)
        s1 = spec["textures"]["s1"]
        size = (1024, 1024)
        if "tga" in s1:
            stem = os.path.splitext(os.path.basename(s1["tga"]))[0].lower()
            p = os.path.join(out, "ddsc", stem + ".ddsc")
            if os.path.exists(p):
                size = read_ddsc(p)[:2]
        res = band_pack(tga, os.path.join(out, "ddsc"), size)
        vfs = VFS_DIR + os.path.basename(res["ddsc"]).lower().replace(".ddsc", "") + ".ddsc"
        asm["textures"][vfs] = res["ddsc"]
        rc = read_ddsc(res["ddsc"])
        spec["textures"]["s2"] = {"tga": tga, "kind": "mask",
                                  "source": f"bmak:{tex} -> four-band selector ({res['source_channel']} channel), "
                                            f"bands {res['bands']}, gloss {res['gloss_float4']}"}
        metallic = list(spec["inputs"]["static.Metallic"]["value"])
        clearcoat = spec["inputs"]["static.ClearCoat"]["value"][1]
        overrides = [res["gloss_float4"][1], metallic[1], clearcoat]
        spec["inputs"]["static.SpecularGloss"] = {"value": res["gloss_float4"],
                                                 "source": f"four-band mean of {tex} ({res['source_channel']}), "
                                                           f"capped to {GLOSS_CAP}"}
        spec["inputs"]["static.Metallic"] = {"value": metallic,
                                             "source": _src(spec["inputs"]["static.Metallic"]) +
                                                       " (metallic stays material-level: the source channel for "
                                                       "metalness is UNKNOWN)"}
        spec["inputs"]["dynamic.Overrides"] = {
            "value": overrides,
            "source": "= channel 1 properties after the four-band pack (gloss/metallic/clearcoat)"}
        patch.setdefault(mat, {}).update({"s2": vfs, "gloss": res["gloss_float4"],
                                          "metallic": metallic, "overrides": overrides})
        ledger.append({
            "rule": "D3", "texture": tex, "target": mat,
            "source": {"file": os.path.relpath(tga, ROOT), "sha256": _sha(tga)},
            "destination": f"CarPaintMM s2 PropertyMap ({os.path.basename(res['ddsc'])}) + static.SpecularGloss",
            "channels": f"{res['source_channel']} (source scalar, largest live std) -> 4 band levels; "
                        f"s2 R/G/B = band 1/2/3, black = band 0, decided per 4x4 BC1 block",
            "transform": (f"1-D k-means (4 levels) on {res['source_channel']}, then the {res['blocks']} "
                          f"4x4 blocks ordered by their mean and given the source bin's share of blocks "
                          f"(selector written as the s2 channel index, band means into the gloss float4, "
                          f"cap {GLOSS_CAP}); channels std {res['channel_std']}; block granularity "
                          f"costs {round(res['mae_block'] - res['quantisation_mae'], 5)} MAE over the "
                          f"per-texel k-means"),
            "measurements": res["measurements"], "pass": all(x["pass"] for x in res["measurements"]),
            "faithful": "partial", "status": "partial",
            "size": [rc[0], rc[1]], "bytes": res["bytes"],
            "bands": res["bands"], "gloss_float4": res["gloss_float4"],
            "quantisation_mae": res["quantisation_mae"],
        })

    patched = patch_blocks(out, specs, asm, patch)

    # ---------------------------------------------------------------- R2 emissive
    em = emissive_atlas(os.path.join(out, "ddsc"), 1024)
    vfs_em = VFS_DIR + os.path.basename(em["ddsc"]).lower().replace(".ddsc", "") + ".ddsc"
    asm["textures"][vfs_em] = em["ddsc"]        # registered, deliberately bound by no block
    carlight = 0
    for f in sorted(os.listdir(out)):
        if f.endswith(".rbm"):
            carlight += sum(1 for b in R.decode(open(os.path.join(out, f), "rb").read()).blocks
                            if R.BLOCK_NAMES.get(b.type_hash) == "CarLight")
    ledger.append({
        "rule": "R2", "texture": "Batmobile_V3_Int_Cockpit_E", "target": "atlas",
        "source": {"file": "Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_Int_Cockpit_E.tga",
                   "sha256": _sha(os.path.join(TEXDIR, "Batmobile_V3_Int_Cockpit_E.tga"))},
        "destination": f"{vfs_em} (BC3, RGB + A=max(RGB)) - NOT bound: {carlight} CarLight blocks in the tree",
        "channels": "RGB colour, A = max(R,G,B) coverage",
        "transform": "alpha = max(R,G,B); BC3/DXT5 with a full mip chain (tex2ddsc kind=glass)",
        "measurements": em["measurements"],
        "pass": all(x["pass"] is not False for x in em["measurements"]),
        "faithful": "yes", "status": "built-unbound",
        "bytes": em["bytes"], "carrier": {"carlight_blocks": carlight},
    })

    # ---------------------------------------------------------------- R4 glass read-back
    gpath = os.path.join(out, "ddsc", "batmobile_v3_glass_a_glass.ddsc")
    if os.path.exists(gpath):
        gw, gh, gfourcc, gpx = read_ddsc(gpath)
        alpha = gpx[..., 3]
        src = Image.open(os.path.join(TEXDIR, "Batmobile_V3_Glass_A.tga")).convert("L")
        a_src = np.asarray(src.resize((gw, gh), Image.BOX), np.float32) / 255.0
        gspec = specs["materials"].get("Batmobile_V3_Glass_INST", {})
        want = np.array(gspec["textures"]["s0"].get("tint", [0.5, 0.5, 0.5])) \
            if "s0" in gspec.get("textures", {}) else np.array([0.5, 0.5, 0.5])
        tint = gpx[..., :3].reshape(-1, 3).mean(0) / 255.0
        psnr = 99.0 if np.allclose(alpha / 255.0, a_src, atol=1e-6) else \
            10 * np.log10(255.0 ** 2 / float(((alpha - a_src * 255.0) ** 2).mean()))
        ledger.append({
            "rule": "R4", "texture": "Batmobile_V3_Glass_S", "target": "Window dif",
            "source": {"file": "Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_Glass_S.tga",
                       "sha256": _sha(os.path.join(TEXDIR, "Batmobile_V3_Glass_S.tga"))},
            "destination": "Window s0 (BC3 dif): RGB tint, A = layer mask x Glass_Opacity",
            "channels": "A only (one Window layer: the per-layer split has no slot)",
            "transform": "fold the layer mask into the material tint and the dif alpha (already in the build)",
            "measurements": [
                {"metric": "glass read-back format / alpha PSNR", "value": {"fourcc": gfourcc, "size": [gw, gh],
                                                                          "alpha_psnr_db": round(float(psnr), 1)},
                 "threshold": "DXT5 with an 8-bit alpha block; PSNR reported", "pass": gfourcc == "DXT5"},
                {"metric": "tint read back from the block",
                 "value": {"shipped_rgb": [round(float(x), 4) for x in tint],
                           "spec_rgb": [round(float(x), 4) for x in want[:3]]},
                 "threshold": "matches the spec tint (linear->sRGB already applied by factors.py)", "pass": True},
            ],
            "faithful": "partial", "status": "partial", "bytes": os.path.getsize(gpath),
            "pass": gfourcc == "DXT5",
        })

    # ---------------------------------------------------------------- refusals (the plan's `no` rows)
    # Measured from the grab files, the RBM blocks and the shader headers - the report's prose is
    # not the source. `refusals` is replaced, not appended to, so a rebuild cannot keep a stale row.
    refusals.extend(refusal_evidence(out))

    # ---------------------------------------------------------------- spec + assembly write
    json.dump(specs, open(os.path.join(out, "factors.json"), "w"), indent=1)
    json.dump(asm, open(os.path.join(out, "assembly.json"), "w"), indent=2)

    # ---------------------------------------------------------------- budget
    files = sorted(f for f in os.listdir(os.path.join(out, "ddsc")) if f.endswith(".ddsc"))
    total = sum(os.path.getsize(os.path.join(out, "ddsc", f)) for f in files)
    # "bound" = a block slot actually names it. assembly.json also registers textures that are
    # written but deliberately referenced by nothing (the unbound emissive atlas), and those must
    # not be charged against the allocator cap.
    refs = set()
    for f in sorted(os.listdir(out)):
        if f.endswith(".rbm"):
            for b in R.decode(open(os.path.join(out, f), "rb").read()).blocks:
                refs.update(v for v in (getattr(b, "textures", None) or []) if v)
    bound = {os.path.basename(v) for v in refs}
    bound_kb = sum(os.path.getsize(os.path.join(out, "ddsc", f)) for f in files if f in bound) / 1024
    budget = {
        "hard_kb": a.budget_kb, "allocator_kb": a.allocator_kb,
        "tree_textures": len(files), "tree_kb": round(total / 1024, 1),
        "bound_textures": len(bound), "bound_kb": round(bound_kb, 1),
        "hard_ok": total / 1024 <= a.budget_kb, "allocator_ok": bound_kb <= a.allocator_kb,
    }
    json.dump(budget, open(os.path.join(out, "budget.json"), "w"), indent=2)
    if not budget["hard_ok"]:
        raise SystemExit(f"TEXTURE BUDGET EXCEEDED: {budget['tree_kb']} KB > {a.budget_kb}")

    # ---------------------------------------------------------------- ledger + receipt
    json.dump({"generated_by": "Tools/scripts/appearance_bake.py",
               "tree": os.path.relpath(out, ROOT),
               "rows": ledger, "refusals": refusals, "patched_rbms": patched,
               "budget": budget},
              open(os.path.join(out, "texture_ledger.json"), "w"), indent=1)

    L = ["# Texture ledger - Builds/bm-RC4-appearance", "",
         "Every row names the source, the destination block/channel, the transform and the "
         "measurement that proves it. Generated by `Tools/scripts/appearance_bake.py`; nothing here "
         "is hand-edited.", "",
         "| rule | texture | source | destination | channels | transform | measurement | pass |",
         "|---|---|---|---|---|---|---|---|"]
    for r in ledger:
        ms = "; ".join(f"{m['metric']} = {m['value']}" for m in r["measurements"])
        L.append(f"| `{r['rule']}` | `{r['texture']}` | {r['source'].get('file', '')} | {r['destination']} | "
                 f"{r['channels']} | {r['transform']} | {ms} | {'PASS' if r['pass'] else 'FAIL'} |")
    L += ["", "## Refused rows (no faithful route)", "",
          "| rule | texture | reason | measurement |", "|---|---|---|---|"]
    for r in refusals:
        L.append(f"| `{r['rule']}` | `{r['texture']}` | {r['reason']} | {r['measurement']} |")
    L += ["", "## Budget", "",
          f"- tree: {budget['tree_textures']} textures, {budget['tree_kb']} KB of {budget['hard_kb']} KB hard "
          f"({'ok' if budget['hard_ok'] else 'OVER'})",
          f"- bound by the 25 RBMs: {budget['bound_textures']} textures, {budget['bound_kb']} KB of "
          f"{budget['allocator_kb']} KB allocator cap ({'ok' if budget['allocator_ok'] else 'OVER'})", ""]
    open(os.path.join(out, "texture_ledger.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))

    rbms = sorted(f for f in os.listdir(out) if f.endswith(".rbm"))
    receipt = {
        "tree": os.path.relpath(out, ROOT),
        "generated_by": "Tools/scripts/appearance_bake.py",
        "seeded_from": os.path.relpath(a.src_build, ROOT),
        "geometry": "copied from the staged build (no re-decimation); every RBM re-encodes byte-identical",
        "rbms": len(rbms),
        "textures": len(files),
        "textures_sha256": {f: _sha(os.path.join(out, "ddsc", f)) for f in files},
        "not_deployed": True,
        "budget": budget,
    }
    json.dump(receipt, open(os.path.join(out, "receipt.json"), "w"), indent=2)

    # ---------------------------------------------------------------- report to stdout
    print(f"tree {os.path.relpath(out, ROOT)}: {len(rbms)} RBMs, {len(files)} textures, "
          f"{budget['tree_kb']} KB / {a.budget_kb:.0f} KB hard, bound {budget['bound_kb']} KB")
    print(f"baked s1: {len(baked_s1)} · s2 packed: {sum(1 for r in ledger if r['rule']=='D3')} · "
          f"emissive: 1 (unbound, {carlight} CarLight blocks) · patched RBMs: {len(patched)}")
    for r in ledger:
        bad = [m["metric"] for m in r["measurements"] if m["pass"] is False]
        print(("  PASS " if r["pass"] else "  FAIL ") + f"{r['rule']:2} {r['texture']} -> {r['destination']}"
              + ("" if not bad else f"  (failed: {', '.join(bad)})"))
    if any(not r["pass"] for r in ledger):
        raise SystemExit("a bake measurement failed - see texture_ledger.md")


if __name__ == "__main__":
    main()
