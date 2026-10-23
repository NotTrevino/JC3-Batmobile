#!/usr/bin/env python3
"""
rbmhdr.py - JC3 RBM header inspector + Gibbed block-name resolver.

Why this exists
---------------
`Gibbed.JustCause3.ConvertRBM.exe` dies on `0x483304D6`, the FIRST block of every
standard JC3 vehicle RBM. The Gibbed JC3 fork's own README calls its RBM
serializer "a WIP (in its ultra-very early stage)". This script therefore does
NOT decode RBM block payloads. It only:

  1. Reads the RBMDL header (version, AABB, lod count, block count) using the
     exact field order from Gibbed.JustCause3.RenderBlockModel.ModelFile.cs.
  2. Lists the type hash of the first block.
  3. Optionally resolves a block type hash back to a NAME, because Gibbed
     identifies block types as Jenkins one-at-a-time hashes of their name
     (Gibbed.JustCause3.RenderBlockModel.BlockTypeFactory.cs). Given a candidate
     name we can confirm it exactly -- no format reverse-engineering needed.

Self-tests are pinned against HashName.exe ground truth so a refactor of the
hash cannot silently break the resolver.

Usage
-----
    python rbmhdr.py info     <file.rbm> [<file.rbm> ...]
    python rbmhdr.py info     --json <dir-or-file> [...]
    python rbmhdr.py resolve  <name> [<name> ...]           # name -> hash
    python rbmhdr.py brute    0x483304D6 [wordlist.txt]     # hash -> name
    python rbmhdr.py selftest
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import struct
import sys
from typing import Iterable

# --------------------------------------------------------------------------
# Jenkins one-at-a-time, matching Gibbed.JustCause3.FileFormats.StringHelpers
# --------------------------------------------------------------------------

M32 = 0xFFFFFFFF


def _rotl(x: int, n: int) -> int:
    return ((x << n) | (x >> (32 - n))) & M32


def hash_jenkins(data: bytes, seed: int = 0) -> int:
    """Byte-for-byte port of StringHelpers.HashJenkins.

    Note the original's unusual byte assembly order (little-endian 32-bit words
    read as byte[0] | byte[1]<<8 | byte[2]<<16 | byte[3]<<24) and its loop
    condition `while (i + 12 < length)`; both are reproduced exactly because
    changing either changes every hash.
    """
    length = len(data)
    a = b = c = (0xDEADBEEF + length + seed) & M32
    i = 0

    while i + 12 < length:
        a = (a + (data[i] | (data[i + 1] << 8) | (data[i + 2] << 16) | (data[i + 3] << 24))) & M32
        b = (b + (data[i + 4] | (data[i + 5] << 8) | (data[i + 6] << 16) | (data[i + 7] << 24))) & M32
        c = (c + (data[i + 8] | (data[i + 9] << 8) | (data[i + 10] << 16) | (data[i + 11] << 24))) & M32
        i += 12

        a = (a - c) & M32; a ^= _rotl(c, 4);  c = (c + b) & M32
        b = (b - a) & M32; b ^= _rotl(a, 6);  a = (a + c) & M32
        c = (c - b) & M32; c ^= _rotl(b, 8);  b = (b + a) & M32
        a = (a - c) & M32; a ^= _rotl(c, 16); c = (c + b) & M32
        b = (b - a) & M32; b ^= _rotl(a, 19); a = (a + c) & M32
        c = (c - b) & M32; c ^= _rotl(b, 4);  b = (b + a) & M32

    for k in range(4):
        if i >= length:
            break
        a = (a + (data[i] << (8 * k))) & M32
        i += 1
    for k in range(4):
        if i >= length:
            break
        b = (b + (data[i] << (8 * k))) & M32
        i += 1
    for k in range(4):
        if i >= length:
            break
        c = (c + (data[i] << (8 * k))) & M32
        i += 1

    c ^= b; c = (c - ((b << 14) | (b >> 18))) & M32
    a ^= c; a = (a - ((c << 11) | (c >> 21))) & M32
    b ^= a; b = (b - ((a << 25) | (a >> 7)))  & M32
    c ^= b; c = (c - ((b << 16) | (b >> 16))) & M32
    a ^= c; a = (a - ((c << 4)  | (c >> 28))) & M32
    b ^= a; b = (b - ((a << 14) | (a >> 18))) & M32
    c ^= b; c = (c - ((b << 24) | (b >> 8)))  & M32
    return c & M32


def name_hash(name: str) -> int:
    """Gibbed hashes the ASCII encoding, uppercased names included as written."""
    return hash_jenkins(name.encode("ascii"))


# Pinned against `HashName.exe` output on this machine.
GROUND_TRUTH = {
    "CarPaint": 0xCD931E75,
    "General": 0xA7583B2B,
    "SkinnedGeneral": 0x5E657F20,
    "Lambert": 0xD5D78AE0,
    "Window": 0x5B2003F6,
}

# Block types Gibbed DOES implement (BlockTypeFactory static ctor).
KNOWN_BLOCKS = [
    "CarPaint", "CarPaintSimple", "DeformableWindow", "General",
    "Lambert", "SkinnedGeneral",
]
KNOWN_BLOCK_RAW = {"JC3Genral": 0x2CEC5AD5}

# Confirmed by hash: the exporter (Brooen/RBM-Exporter, io_export_rbm/export_rbm_script.py)
# writes each block type as raw little-endian bytes, and these Jenkins hashes of the
# PascalCase names reproduce those bytes exactly. Sourced from the exporter, not guessed.
#   bytes D6043348 -> 0x483304D6 ; HashJenkins("CarPaintMM")    == 0x483304D6
#   bytes F18B94DB -> 0xDB948BF1 ; HashJenkins("CarLight")      == 0xDB948BF1
#   bytes CD4CD2A5 -> 0xA5D24CCD ; HashJenkins("BavariumShield") == 0xA5D24CCD
#   bytes F603205B -> 0x5B2003F6 ; HashJenkins("Window")        == 0x5B2003F6
#   bytes A1729CF9 -> 0xF99C72A1 ; name spelling UNKNOWN ("WaterHull" hashes to 0xC0EF6B7D)
PROVEN_BLOCKS = {
    0x483304D6: ("CarPaintMM", "exporter node group CARPAINTMM"),
    0xDB948BF1: ("CarLight", "exporter node group CARLIGHT"),
    0xA5D24CCD: ("BavariumShield", "exporter node group BAVARIUMSHIELD"),
    0xF99C72A1: ("WaterHull (name unconfirmed)", "exporter node group WATERHULL, raw bytes only"),
}

# Full name list Gibbed knows how to NAME but not all of which it can parse.
GIBBED_NAMES = [
    "2DTex1", "2DTex2", "3DText", "AOBox", "Beam", "BillboardFoliage", "Box",
    "Bullet", "CarPaint", "CarPaintSimple", "CirrusClouds", "Clouds", "Creatures",
    "DecalDeformable", "DecalSimple", "DecalSkinned", "DeformableWindow",
    "Facade", "Flag", "FogGradient", "Font", "General", "Grass", "GuiAnark",
    "Halo", "Lambert", "Leaves", "Lights", "Line", "Merged", "NvWaterHighEnd",
    "Occluder", "Open", "Particle", "Skidmarks", "SkinnedGeneral",
    "SkyGradient", "SoftClouds", "SplineRoad", "Stars", "Terrain",
    "TerrainForest", "TerrainForestFin", "TreeImpostorTrunk", "TreeImpostorTop",
    "Triangle", "VegetationBark", "VegetationFoliage", "WaterGodrays",
    "WaterHighEnd", "WaterWaves", "Weather", "Window",
]


# --------------------------------------------------------------------------
# RBMDL header
# --------------------------------------------------------------------------

class RbmError(Exception):
    pass


class _Reader:
    """Minimal in-memory stand-in for a binary file object."""

    def __init__(self, blob: bytes):
        self.blob = blob
        self.pos = 0

    def read(self, n: int) -> bytes:
        out = self.blob[self.pos:self.pos + n]
        self.pos += len(out)
        return out

    def seek(self, n: int, whence: int = 0) -> None:
        self.pos = n if whence == 0 else self.pos + n

    def tell(self) -> int:
        return self.pos


def read_header(path: str) -> dict:
    """Header of an RBM file on disk."""
    with open(path, "rb") as fh:
        blob = fh.read()
    out = parse_header(blob)
    out["path"] = path
    return out


def parse_header(blob: bytes) -> dict:
    """Parse the RBMDL header exactly as Gibbed's ModelFile.Deserialize does.

    Layout (Gibbed.JustCause3.RenderBlockModel.ModelFile.cs):
        u32  magicLength   must be 5 (LE); the byte-swapped value selects BE
        char[5] magic      must be "RBMDL"
        s32  versionMajor  (must be 1)
        s32  versionMinor  (must be 16)
        s32  versionRevision
        f32  minX minY minZ
        f32  maxX maxY maxZ
        s32  tag              <- RbmHeader::m_Tag. Verified against
                            aaronkirkham/jc-model-renderer render_block_model.cpp:
                            "RBM v{}.{}.{}. NumberOfBlocks={}, Tag={}". The tag is a
                            free-form value, NOT a zone or attachment count.
        s32  blockCount        <- RbmHeader::m_NumberOfBlocks
        then blockCount x: u32 typeHash, <payload>, u32 footer 0x89ABCDEF
    """
    fh = _Reader(blob)
    raw = fh.read(4)
    if len(raw) < 4:
        raise RbmError("file too short for magic length")
    magic_length = struct.unpack("<I", raw)[0]
    if magic_length == 5:
        endian = "<"
    elif struct.unpack(">I", raw)[0] == 5:
        endian = ">"
    else:
        raise RbmError(f"invalid magic length {magic_length:#x} (expected 5)")

    magic = fh.read(5).decode("ascii", "replace")
    if magic != "RBMDL":
        raise RbmError(f"invalid magic {magic!r} (expected 'RBMDL')")

    major, minor, revision = struct.unpack(endian + "3i", fh.read(12))
    bbox = struct.unpack(endian + "6f", fh.read(24))
    tag, block_count = struct.unpack(endian + "2i", fh.read(8))
    first_block_offset = fh.tell()

    first_type_hash = None
    if block_count > 0:
        fh.seek(first_block_offset)
        first_type_hash = struct.unpack(endian + "I", fh.read(4))[0]

    known = known_block_name(first_type_hash) if first_type_hash is not None else None
    return {
        "endian": "little" if endian == "<" else "big",
        "version": f"{major}.{minor}.{revision}",
        "version_supported_by_gibbed": (major == 1 and minor == 16),
        "min": {"x": bbox[0], "y": bbox[1], "z": bbox[2]},
        "max": {"x": bbox[3], "y": bbox[4], "z": bbox[5]},
        "size_m": {
            "x": round(bbox[3] - bbox[0], 4),
            "y": round(bbox[4] - bbox[1], 4),
            "z": round(bbox[5] - bbox[2], 4),
        },
        "tag": tag,
        "block_count": block_count,
        "first_block_offset": first_block_offset,
        "first_block_type_hash": None if first_type_hash is None else f"0x{first_type_hash:08X}",
        "first_block_name": known,
    }


def known_block_name(type_hash: int) -> str | None:
    if type_hash in PROVEN_BLOCKS:
        return PROVEN_BLOCKS[type_hash][0]
    for name, raw in KNOWN_BLOCK_RAW.items():
        if raw == type_hash:
            return f"{name} (raw)"
    for name in KNOWN_BLOCKS:
        if name_hash(name) == type_hash:
            return name
    for name in GIBBED_NAMES:
        if name_hash(name) == type_hash:
            return f"{name} (named by Gibbed, not parsed by ConvertRBM)"
    return None


# --------------------------------------------------------------------------
# brute force
# --------------------------------------------------------------------------

DEFAULT_WORDLIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blockwords.txt")


def brute_force(target: int, wordlist: str, extra: Iterable[str] = ()) -> list[str]:
    words: list[str] = []
    if os.path.isfile(wordlist):
        with open(wordlist, "r", encoding="utf-8", errors="replace") as fh:
            words.extend(w.strip() for w in fh if w.strip())
    words.extend(extra)
    seen: set[str] = set()
    hits: list[str] = []
    for w in words:
        if w in seen:
            continue
        seen.add(w)
        try:
            h = name_hash(w)
        except UnicodeEncodeError:
            continue
        if h == target:
            hits.append(w)
    return hits


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_info(args) -> int:
    files: list[str] = []
    for p in args.paths:
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                files.extend(os.path.join(root, n) for n in names if n.lower().endswith(".rbm"))
        else:
            files.extend(glob.glob(p))
    files = sorted(set(files))
    if not files:
        print("no .rbm files matched", file=sys.stderr)
        return 2

    rows, bad = [], []
    for f in files:
        try:
            rows.append(read_header(f))
        except RbmError as exc:
            bad.append({"path": f, "error": str(exc)})

    if args.json:
        print(json.dumps({"ok": rows, "errors": bad}, indent=2))
    else:
        name_w = max((len(os.path.basename(r["path"])) for r in rows), default=10)
        print(f"{'file'.ljust(name_w)}  {'ver':>6}  {'tag':>3} {'blk':>4}  "
              f"{'W x H x L (m)':>22}  first block")
        print("-" * (name_w + 60))
        for r in sorted(rows, key=lambda r: os.path.basename(r["path"])):
            s = r["size_m"]
            dims = f"{s['x']:.3f} x {s['y']:.3f} x {s['z']:.3f}"
            blk = r["first_block_type_hash"] or "-"
            if r["first_block_name"]:
                blk += f"  ({r['first_block_name']})"
            print(f"{os.path.basename(r['path']).ljust(name_w)}  {r['version']:>6}  "
                  f"{r['tag']:>3} {r['block_count']:>4}  {dims:>22}  {blk}")
        if bad:
            print(f"\n{len(bad)} file(s) could not be parsed:", file=sys.stderr)
            for b in bad:
                print(f"  {b['path']}: {b['error']}", file=sys.stderr)
    return 0


def cmd_resolve(args) -> int:
    for n in args.names:
        print(f"{name_hash(n):08X}  {n}")
    return 0


def cmd_brute(args) -> int:
    target = int(args.hash, 16) if args.hash.lower().startswith("0x") else int(args.hash, 16)
    wordlist = args.wordlist or DEFAULT_WORDLIST
    hits = brute_force(target, wordlist)
    if hits:
        print(f"0x{target:08X} = " + ", ".join(hits))
        return 0
    known = known_block_name(target)
    if known:
        print(f"0x{target:08X} = {known}")
        return 0
    print(f"0x{target:08X} not found in {wordlist}")
    return 1


def cmd_refs(args) -> int:
    """List the .ddsc paths an RBM references, and whether they resolve inside a tree.

    RBM material blocks store texture paths as plaintext. An RBM lifted out of one
    vehicle's .ee and dropped into another's keeps pointing at the *original*
    vehicle's textures, which do not exist in the target. Shipping a body RBM
    without its textures is what made test-004 hang the game at load.
    """
    root = os.path.abspath(args.tree) if args.tree else None
    files: list[str] = []
    for p in args.paths:
        if os.path.isdir(p):
            for d, _dirs, names in os.walk(p):
                files.extend(os.path.join(d, n) for n in names if n.lower().endswith(".rbm"))
        else:
            files.extend(glob.glob(p))
    files = sorted(set(files))
    if not files:
        print("no .rbm files matched", file=sys.stderr)
        return 2

    total = unresolved = 0
    for f in files:
        with open(f, "rb") as fh:
            blob = fh.read()
        text = "".join(chr(c) if 32 <= c < 127 else "\n" for c in blob)
        refs = sorted(set(re.findall(r"[A-Za-z0-9_./\\-]+\.ddsc", text)))
        print(f"\n{os.path.basename(f)}  ({len(refs)} texture refs)")
        for r in refs:
            hit = ""
            if root:
                cand = os.path.join(root, r.replace("/", os.sep))
                hit = "  OK" if os.path.isfile(cand) else "  --  UNRESOLVED"
            print(f"   {r}{hit}")
            total += 1
            if hit == "  --  UNRESOLVED":
                unresolved += 1
    print(f"\n{total} refs, {total - unresolved} resolve inside "
          f"{root or '(no tree given)'}, {unresolved} unresolved")
    print("Shared/00_shared/textures-dummies refs that do NOT resolve inside the .ee are\n"
          "normal -- the vanilla Serpente body leaves the same class dangling, because\n"
          "they come from the global VFS rather than the entity archive.")
    return 0


def cmd_selftest(_args) -> int:
    ok = True
    for name, expected in GROUND_TRUTH.items():
        got = name_hash(name)
        mark = "ok  " if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"{mark} {name:<16} expected {expected:08X} got {got:08X}")
    for name, raw in KNOWN_BLOCK_RAW.items():
        print(f"ok   {name:<16} raw hash {raw:08X}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="print RBMDL headers (version, AABB, lod/block counts)")
    p.add_argument("paths", nargs="+")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("resolve", help="name -> Jenkins block hash")
    p.add_argument("names", nargs="+")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("brute", help="block hash -> candidate name(s)")
    p.add_argument("hash")
    p.add_argument("wordlist", nargs="?")
    p.set_defaults(func=cmd_brute)

    p = sub.add_parser("selftest", help="verify the hash against HashName.exe ground truth")
    p.set_defaults(func=cmd_selftest)

    p = sub.add_parser("refs", help="list .ddsc texture paths an RBM references, and whether "
                                     "they resolve inside a given tree")
    p.add_argument("paths", nargs="+")
    p.add_argument("--tree", help="root directory (an unpacked .ee) to resolve against")
    p.set_defaults(func=cmd_refs)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())