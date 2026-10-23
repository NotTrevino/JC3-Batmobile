"""Scratch solver: recover a Window/CarLight buffer layout from the files.

Method, and why each step is trustworthy:
  * the texture-name table is self-identifying (ASCII asset paths), so the search
    for it needs no prior knowledge of the block's static field layout;
  * every buffer is `u32 count` followed by `count * stride` bytes, and the engine
    writes a 0x89ABCDEF checksum immediately after the last one, so a candidate
    sequence is only accepted if it lands EXACTLY on that checksum;
  * the decoded float3 positions must reproduce the bounding box the engine itself
    stored in the file header. That is the oracle: a wrong stride gives noise.
"""
import struct
import sys

import numpy as np

import rbm_geom as R

STRIDES = tuple(range(2, 65, 2))
MAX_COUNT = 200_000
# CarPaintMM has 16 bytes of material_params after the texture table; allow a
# little slack so a short trailing gap does not break the chain.
MAX_LEAD = 64


def find_tex_tables(buf, lo, hi):
    """All plausible texture-name tables in [lo, hi), in position order.

    Self-locating: entries are printable asset paths ending in a known extension,
    which no float or index field imitates by accident. That avoids hardcoding a
    per-type offset we would have no way to verify.

    Several can match -- raw floats in a static-parameter block can fake a short
    table, and a table can be mis-parsed by one entry -- so the caller picks the
    first candidate whose buffer chain actually solves, rather than trusting
    position alone.
    """
    hits = []
    for p in range(lo, min(hi, len(buf))):
        if p + 4 > len(buf):
            break
        (cnt,) = struct.unpack_from("<I", buf, p)
        if not 1 <= cnt <= 16:
            continue
        q = p + 4
        names = []
        ok = True
        for _ in range(cnt):
            if q + 4 > len(buf):
                ok = False
                break
            (ln,) = struct.unpack_from("<I", buf, q)
            q += 4
            if ln == 0:
                names.append("")
                continue
            if ln > 4096 or q + ln > len(buf):
                ok = False
                break
            s = buf[q:q + ln]
            if not all(32 <= c < 127 for c in s):
                ok = False
                break
            names.append(s.decode())
            q += ln
        if not ok or not names:
            continue
        if not any(n.endswith((".ddsc", ".dds", ".avtx")) for n in names):
            continue
        hits.append((p, names, q))
    return hits


def chain_to(buf, lo, end, _depth=0):
    """Buffer chain that starts in [lo, end) and finishes exactly at `end`."""
    if _depth > 8:
        return None
    for s in range(lo, end):
        if s + 4 > len(buf):
            break
        (c,) = struct.unpack_from("<I", buf, s)
        if not 3 <= c <= MAX_COUNT:
            continue
        for st in STRIDES:
            if s + 4 + c * st != end:
                continue
            if s - lo <= MAX_LEAD:
                return [(s, st, c)]
            prev = chain_to(buf, lo, s, _depth + 1)
            if prev is None:
                continue
            return prev + [(s, st, c)]
    return None


def find_chain_end(buf, lo, last_block):
    """Where the last buffer of this block ends.

    For the final block of a file that is exactly len(buf)-4, because the
    0x89ABCDEF checksum is the last thing in the file. For any other block the
    buffer run must be followed by that checksum, which is what closes the block.
    Knowing which block is last is what disambiguates: otherwise a spurious run
    landing on a checksum-looking sequence inside vertex data looks just as good.
    """
    for s in range(lo, len(buf)):
        if s + 4 > len(buf):
            break
        (c,) = struct.unpack_from("<I", buf, s)
        if not 3 <= c <= MAX_COUNT:
            continue
        # Every block type here ends with an index buffer, and an index buffer's
        # length is always a multiple of three. Requiring that is what stops a
        # coincidental single "buffer" from being accepted as a whole block.
        if c % 3:
            continue
        for st in STRIDES:
            e = s + 4 + c * st
            if last_block:
                if e == len(buf) - 4:
                    return e
            elif e + 4 <= len(buf) and struct.unpack_from("<I", buf, e)[0] == R.RBM_BLOCK_CHECKSUM:
                return e
    return None


def solve(buf, lo, last_block):
    end = find_chain_end(buf, lo, last_block)
    if end is None:
        return None
    return chain_to(buf, lo, end)


def report(path, verbose=False):
    """Walk the file block by block, exactly as decode() does, and solve each one."""
    import numpy as np

    buf = open(path, "rb").read()
    h = R.Rbm.parse_header(buf)
    pos = h["header_len"]
    blocks = []
    for i in range(h["number_of_blocks"]):
        if pos + 4 > len(buf):
            return None
        (th,) = struct.unpack_from("<I", buf, pos)
        body = pos + 4
        last = i == h["number_of_blocks"] - 1
        seq = None
        _tbl = _names = _tbl_end = None
        for cand in find_tex_tables(buf, body, body + 4096):
            s = solve(buf, cand[2], last)
            if s is not None:
                _tbl, _names, _tbl_end = cand
                seq = s
                break
        if seq is None:
            return None
        end = seq[-1][0] + 4 + seq[-1][1] * seq[-1][2]
        if struct.unpack_from("<I", buf, end)[0] != R.RBM_BLOCK_CHECKSUM:
            return None

        # oracle: positions from the first buffer must reproduce the header bbox
        p0, st0, c0 = seq[0]
        err = None
        if c0 > 0 and st0 % 4 == 0:
            P = np.frombuffer(buf[p0 + 4: p0 + 4 + c0 * st0], dtype="<f4")
            P = P.reshape(-1, st0 // 4)[:, :3]
            P = P[np.isfinite(P).all(axis=1)]
            if len(P) >= 3 and h["number_of_blocks"] == 1:
                lo3, hi3 = P.min(axis=0), P.max(axis=0)
                err = float(max(max(abs(lo3[k] - h["bbox_min"][k]) for k in range(3)),
                                max(abs(hi3[k] - h["bbox_max"][k]) for k in range(3))))
        blocks.append({
            "type": th, "static": _tbl - body, "gap": seq[0][0] - _tbl_end,
            "seq": seq, "verts": c0, "tris": seq[-1][2] // 3, "bbox_err": err,
        })
        pos = end + 4
    if pos != len(buf):
        return None
    return {"path": path, "blocks": blocks, "hdr_bbox": (h["bbox_min"], h["bbox_max"])}


if __name__ == "__main__":
    for path in sys.argv[1:]:
        r = report(path)
        if r is None:
            print(f"{path.rsplit(chr(92), 1)[-1]}: NO SOLUTION")
            continue
        print(f"{path.rsplit(chr(92), 1)[-1]}")
        for i, b in enumerate(r["blocks"]):
            name = R.BLOCK_NAMES.get(b["type"], hex(b["type"]))
            err = "n/a" if b["bbox_err"] is None else f"{b['bbox_err']:.4f} m"
            print(f"   block {i}: {name}  static {b['static']} B  gap {b['gap']} B  "
                  f"verts={b['verts']} tris={b['tris']}  bbox_err={err}")
            for p, st, c in b["seq"]:
                print(f"       buffer 0x{p:05X}  stride {st:>3}  count {c:>7}")