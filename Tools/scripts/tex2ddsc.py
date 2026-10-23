"""tex2ddsc.py - any .tga -> a JC3 .ddsc (single element, FULL mip chain, no .hmddsc). MODLOG §75.

Container: the shape of the Meme Vehicle Pack's `textures/convertible.ddsc` -- a texture that
renders at a NEW path with no .hmddsc: write-to-hmddsc False, mip-count = hdr-mip-count = all mips,
ONE element (offset 128, size = the whole chain). Header flags: 8 on colour textures (DaBaby,
vanilla body_dif 9 = 8|1), 0 here for normal maps (vanilla body_nrm = 1 with an .hmddsc; bit 1
tracks the .hmddsc). [INFERENCE for the normal-map flags; logged.]

Formats (vanilla: body_dif = 71, body_nrm = 83):
    colour  -> 71  BC1/DXT1   (DDS 'DXT1', 128 B header)
    normal  -> 83  BC5        (DDS 'DX10' + 20 B extension, DXGI 83)
Encoders are vectorised numpy: BC1 = per-block bounding-box endpoints in RGB565, 4-colour mode,
nearest-palette indices; BC5 = two BC4 channels (R, G), 8-value mode. Mips: Pillow box filter
down to 1x1. Size capped at --max (default 1024).

Pipeline: tga -> mips -> blocks -> <name>0.dds + <name>.xml -> `ConvertTexture.exe <name>.xml`
(import; proven byte-identical on convertible.ddsc) -> <name>.ddsc. Verify: our own decode of every
mip (PSNR vs the source mip) and a re-EXPORT of the .ddsc that must return our .dds byte-identical.

Usage: python tex2ddsc.py <in.tga> <out_dir> --kind colour|normal [--max 1024]
       (or import as a module: convert(tga, out_dir, kind))
"""
import argparse
import os
import shutil
import struct
import subprocess
import tempfile

import numpy as np
from PIL import Image

GIBBED = r"E:\Modding\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertTexture.exe"
FMT = {"colour": 71, "mask": 71, "normal": 83, "glass": 77}
# mask = linear BC1 (vanilla msk/mpm: flags 1, no sRGB bit 8). glass = BC3/DXT5, the format the
# vanilla Window dif uses (v0300..._glass_alpha_dif: header format 77, DDS 'DXT5', 8-bit alpha).


def mip_chain(img, max_side):
    w, h = img.size
    s = min(1.0, max_side / max(w, h))
    w, h = max(4, int(w * s)), max(4, int(h * s))
    img = img.resize((w, h), Image.LANCZOS) if (w, h) != img.size else img
    out = [np.asarray(img, np.float32)]
    while w > 1 or h > 1:
        w, h = max(1, w // 2), max(1, h // 2)
        img = img.resize((w, h), Image.BOX)
        out.append(np.asarray(img, np.float32))
    return out


def blocks_of(a):
    """(H, W, C) -> (nby, nbx, 16, C), padding to a multiple of 4 by edge replication."""
    h, w, c = a.shape
    H, W = (h + 3) // 4 * 4, (w + 3) // 4 * 4
    a = np.pad(a, ((0, H - h), (0, W - w), (0, 0)), mode="edge")
    return a.reshape(H // 4, 4, W // 4, 4, c).transpose(0, 2, 1, 3, 4).reshape(H // 4, W // 4, 16, c)


def to565(c):
    c = np.clip(np.round(c), 0, 255).astype(np.uint32)
    return ((c[..., 0] >> 3) << 11) | ((c[..., 1] >> 2) << 5) | (c[..., 2] >> 3)


def from565(v):
    r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
    return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.float32)


def bc1(a):
    """BC1. With a 4th (alpha) channel, blocks holding any pixel with alpha < 128 use BC1's
    punch-through 3-colour mode (c0 <= c1; index 3 = transparent); other blocks 4-colour mode."""
    B = blocks_of(a[..., :3])
    cut = blocks_of(a[..., 3:4])[..., 0] < 128 if a.shape[-1] == 4 else np.zeros(B.shape[:3], bool)
    big = 1e9
    hi = np.where(cut[..., None], -big, B).max(2)                     # endpoints from OPAQUE pixels
    lo = np.where(cut[..., None], big, B).min(2)
    allcut = cut.all(2)
    hi = np.where(allcut[..., None], 0, hi)
    lo = np.where(allcut[..., None], 0, lo)
    c0, c1 = to565(hi), to565(lo)
    punch = cut.any(2)
    # 4-colour mode needs c0 > c1, punch-through needs c0 <= c1
    swap = np.where(punch, c0 > c1, c0 < c1)
    c0, c1 = np.where(swap, c1, c0), np.where(swap, c0, c1)
    p0, p1 = from565(c0), from565(c1)
    pal4 = np.stack([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3], 2)
    pal3 = np.stack([p0, p1, (p0 + p1) / 2, np.full_like(p0, big)], 2)    # index 3 never chosen by colour
    pal = np.where(punch[..., None, None], pal3, pal4)                     # (by, bx, 4, 3)
    d = ((B[:, :, :, None, :] - pal[:, :, None, :, :]) ** 2).sum(-1)      # (by, bx, 16, 4)
    idx = d.argmin(-1).astype(np.uint32)
    idx = np.where((c0 == c1)[..., None] & ~punch[..., None], 0, idx)
    idx = np.where(cut, 3, idx)
    bits = (idx << (2 * np.arange(16, dtype=np.uint32))).sum(-1).astype(np.uint32)
    out = np.zeros(c0.shape + (2,), np.uint32)
    out[..., 0] = c0 | (c1 << 16)
    out[..., 1] = bits
    return out.astype("<u4").tobytes()


def bc4(ch):
    """ch: (by, bx, 16) float 0..255 -> (by, bx, 8) bytes, 8-value mode (r0 > r1)."""
    r0 = np.clip(np.round(ch.max(2)), 0, 255)
    r1 = np.clip(np.round(ch.min(2)), 0, 255)
    r0 = np.where(r0 == r1, np.minimum(r0 + 1, 255), r0)
    r1 = np.where(r0 == r1, r1 - 1, r1)
    t = np.arange(8, dtype=np.float32)
    w = np.array([0, 7, 6, 5, 4, 3, 2, 1], np.float32) / 7.0      # palette 0: r0, 1: r1, 2..7: blends
    pal = r0[..., None] * np.r_[1.0, 0.0, w[2:]] + r1[..., None] * (1 - np.r_[1.0, 0.0, w[2:]])
    idx = np.abs(ch[..., :, None] - pal[..., None, :]).argmin(-1).astype(np.uint64)  # (by,bx,16)
    bits = (idx << (3 * np.arange(16, dtype=np.uint64))).sum(-1).astype(np.uint64)
    out = np.zeros(ch.shape[:2] + (8,), np.uint8)
    out[..., 0], out[..., 1] = r0.astype(np.uint8), r1.astype(np.uint8)
    for k in range(6):
        out[..., 2 + k] = ((bits >> np.uint64(8 * k)) & np.uint64(255)).astype(np.uint8)
    return out, pal, idx


def bc5(a):
    B = blocks_of(a[..., :2])
    r, _, _ = bc4(B[..., 0])
    g, _, _ = bc4(B[..., 1])
    return np.concatenate([r, g], -1).tobytes()


def bc3(a):
    """BC3/DXT5 = BC4 alpha block (8 B) + BC1 colour block (8 B), per 4x4 block."""
    by, bx = (a.shape[0] + 3) // 4, (a.shape[1] + 3) // 4
    col = np.frombuffer(bc1(a[..., :3]), np.uint8).reshape(by, bx, 8)
    alp = bc4(blocks_of(a[..., 3:4])[..., 0])[0].astype(np.uint8)
    return np.concatenate([alp, col], -1).tobytes()


def decode_bc1(data, w, h):
    by, bx = (h + 3) // 4, (w + 3) // 4
    v = np.frombuffer(data, "<u4").reshape(by, bx, 2)
    c0, c1 = v[..., 0] & 0xFFFF, v[..., 0] >> 16
    p0, p1 = from565(c0), from565(c1)
    four = (c0 > c1)[..., None, None]
    pal = np.where(four, np.stack([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3], 2),
                   np.stack([p0, p1, (p0 + p1) / 2, np.zeros_like(p0)], 2))     # 3-colour: index 3 = transparent black
    idx = (v[..., 1][..., None] >> (2 * np.arange(16, dtype=np.uint32))) & 3
    px = np.take_along_axis(pal, idx[..., None].astype(np.int64).repeat(3, -1), 2)
    return px.reshape(by, bx, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(by * 4, bx * 4, 3)[:h, :w]


def decode_bc4(blk):
    r0, r1 = blk[..., 0].astype(np.float32), blk[..., 1].astype(np.float32)
    w = np.r_[1.0, 0.0, np.array([6, 5, 4, 3, 2, 1], np.float32) / 7.0]
    pal = r0[..., None] * w + r1[..., None] * (1 - w)
    bits = np.zeros(blk.shape[:2], np.uint64)
    for k in range(6):
        bits |= blk[..., 2 + k].astype(np.uint64) << np.uint64(8 * k)
    idx = ((bits[..., None] >> (3 * np.arange(16, dtype=np.uint64))) & np.uint64(7)).astype(np.int64)
    return np.take_along_axis(pal, idx, 2)


def decode_bc5(data, w, h):
    by, bx = (h + 3) // 4, (w + 3) // 4
    v = np.frombuffer(data, np.uint8).reshape(by, bx, 16)
    ch = [decode_bc4(v[..., :8]), decode_bc4(v[..., 8:])]
    px = np.stack(ch, -1)
    return px.reshape(by, bx, 4, 4, 2).transpose(0, 2, 1, 3, 4).reshape(by * 4, bx * 4, 2)[:h, :w]


def decode_bc3(data, w, h):
    by, bx = (h + 3) // 4, (w + 3) // 4
    v = np.frombuffer(data, np.uint8).reshape(by, bx, 16)
    col = decode_bc1(v[..., 8:].tobytes(), w, h)
    a = decode_bc4(v[..., :8]).reshape(by, bx, 4, 4).transpose(0, 2, 1, 3).reshape(by * 4, bx * 4)[:h, :w]
    return np.concatenate([col, a[..., None]], -1)


def dds_header(w, h, kind, nbytes0):
    hd = bytearray(128)
    hd[0:4] = b"DDS "
    struct.pack_into("<7I", hd, 4, 124, 0x21007, h, w, nbytes0, 1, 1)        # size, flags, h, w, pitch, depth, mips
    struct.pack_into("<2I", hd, 76, 32, 4)                                  # pixel format: size, FOURCC
    hd[84:88] = {"normal": b"DX10", "glass": b"DXT5"}.get(kind, b"DXT1")
    struct.pack_into("<I", hd, 108, 0x1000)                                 # caps: TEXTURE
    if kind == "normal":
        hd += struct.pack("<5I", 83, 3, 0, 1, 0)                            # DXGI_BC5_UNORM, 2D, 1 array
    return bytes(hd)


def xml_for(w, h, kind, mips, chain_size):
    fl = 8 if kind in ("colour", "glass") else 0   # bit 8 = sRGB (vanilla dif 9, glass_alpha_dif 9)
    el = [f'\t\t<element offset="128" size="{chain_size}" external="False" unknown8="00000010" unknownA="00000000" />']
    el += ['\t\t<element offset="0" size="0" external="False" unknown8="00000000" unknownA="00000000" />'] * 7
    return ('\ufeff<?xml version="1.0" encoding="utf-8"?>\n<texture write-to-hmddsc="False">\n'
            f'\t<header unknown-06="00000008" unknown-1C="00000000" dimension="2" depth="1" '
            f'mip-count="{mips}" hdr-mip-count="{mips}" flags="{fl:08X}" />\n'
            f'\t<check width="{w}" height="{h}" format="{FMT[kind]}" />\n\t<elements>\n'
            + "\n".join(el) + "\n\t</elements>\n</texture>")


def psnr(a, b):
    m = ((a - b) ** 2).mean()
    return 99.0 if m == 0 else 10 * np.log10(255.0 ** 2 / m)


def convert(tga, out_dir, kind, max_side=1024, alpha_tga=None):
    alpha = Image.open(alpha_tga).convert("L") if alpha_tga else None
    return convert_image(Image.open(tga), os.path.splitext(os.path.basename(tga))[0], out_dir, kind,
                         max_side, alpha)


def convert_image(img, name, out_dir, kind, max_side=1024, alpha=None):
    """img: PIL image (file or generated).
    colour/mask -> BC1 (punch-through when `alpha`, an L image, is given or img has its own alpha);
    normal -> BC5; glass -> BC3/DXT5 (8-bit alpha, no punch-through), the vanilla Window dif format."""
    if kind == "normal":
        img = img.convert("RGB")
    else:
        alpha = alpha or (img.getchannel("A") if img.mode in ("RGBA", "LA") else None)
        img = img.convert("RGB")
        if alpha is not None:
            img = img.copy()
            img.putalpha(alpha.resize(img.size, Image.NEAREST))
    if kind == "glass" and img.mode != "RGBA":
        img = img.convert("RGBA")                              # DXT5 needs the alpha block
    mips = mip_chain(img, max_side)
    enc, dec = {"normal": (bc5, decode_bc5), "glass": (bc3, decode_bc3)}.get(kind, (bc1, decode_bc1))
    chain, worst, worst_a = b"", 99.0, 99.0
    for m in mips:
        data = enc(m)
        h, w = m.shape[:2]
        got = dec(data, w, h)
        ref = m[..., :2] if kind == "normal" else m[..., :3]
        if m.shape[-1] == 4 and kind != "glass":              # cut-out pixels have no colour to compare
            keep = m[..., 3] >= 128
            got, ref = (got[keep], ref[keep]) if keep.any() else (got[:0], ref[:0])
        elif m.shape[-1] == 4:
            keep = m[..., 3] >= 8                              # fully transparent texels show nothing
            worst_a = min(worst_a, psnr(got[..., 3][keep], m[..., 3][keep])) if keep.any() else worst_a
            got, ref = got[..., :3][keep], ref[keep]
        if len(ref):
            worst = min(worst, psnr(got, ref))
        chain += data
    h, w = mips[0].shape[:2]
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        hd = dds_header(w, h, kind, len(enc(mips[0])))
        open(os.path.join(td, name + "0.dds"), "wb").write(hd + chain)
        open(os.path.join(td, name + ".xml"), "w", encoding="utf-8", newline="\r\n").write(xml_for(w, h, kind, len(mips), len(chain)))
        r = subprocess.run([GIBBED, name + ".xml"], cwd=td, capture_output=True, text=True)
        ddsc = os.path.join(td, name + ".ddsc")
        if r.returncode != 0 or not os.path.exists(ddsc):
            raise SystemExit(f"{name}: ConvertTexture import failed\n{r.stdout[-800:]}{r.stderr[-800:]}")
        chk = os.path.join(td, "chk")
        os.makedirs(chk)
        shutil.copy(ddsc, chk)
        subprocess.run([GIBBED, name + ".ddsc"], cwd=chk, capture_output=True, text=True)
        back = open(os.path.join(chk, name + "0.dds"), "rb").read()
        if back[-len(chain):] != chain:
            raise SystemExit(f"{name}: re-export does not return our blocks")
        dst = os.path.join(out_dir, name + ".ddsc")
        shutil.copy(ddsc, dst)
    out = {"name": name, "kind": kind, "size": [w, h], "mips": len(mips), "bytes": os.path.getsize(dst),
           "alpha": alpha is not None, "worst_mip_psnr_db": round(float(worst), 1), "ddsc": dst}
    if kind == "glass":
        out["worst_alpha_psnr_db"] = round(float(worst_a), 1)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tga")
    ap.add_argument("out_dir")
    ap.add_argument("--kind", choices=list(FMT), required=True)
    ap.add_argument("--max", type=int, default=1024)
    a = ap.parse_args()
    print(convert(a.tga, a.out_dir, a.kind, a.max))


if __name__ == "__main__":
    main()
