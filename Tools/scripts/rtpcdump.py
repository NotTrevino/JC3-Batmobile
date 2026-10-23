"""rtpcdump.py - decode a JC3 RTPC property container (.epe) to readable text.

Format (Gibbed.JustCause3.PropertyFormats.PropertyContainerFile):
  'RTPC', u32 version==1, root node (name_hash u32, data_offset u32,
  prop_count u16, child_count u16), nodes walked breadth-first; each property
  is 9 bytes: name_hash u32, 4 data bytes, type u8. Primitive int(1)/float(2)
  values sit inline in the 4 data bytes; every other type stores a data offset.
  Type ids: 1 int, 2 float, 3 stringZ, 4/5/6 vec2/3/4, 8 mat4x4, 9 vec_int,
  10 vec_float, 11 vec_byte, 13 objectid, 14 vec_events.

Name resolution: hashes are Gibbed Jenkins over the property/node name. Pass
--namelist with a plain one-name-per-line list (e.g. the fork's
00_generated.namelist, ~16% coverage); anything unresolved prints as
<id:XXXXXXXX>, same convention as Gibbed's own converter output.

Verified: patched w501_turret_sam_v2.epe -> 333 nodes, incl. node #273
CTurretWeaponComponent and CConstraintLimitedHingeData pairs 80.0/-10.0.

Usage:
  python rtpcdump.py <file.epe> [--namelist names.txt] [--node NAME] [--all]
Read-only; prints to stdout.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rbmhdr import hash_jenkins  # noqa: E402,F401  (re-exported for callers)

TYPES = {0: "unassigned", 1: "int", 2: "float", 3: "string", 4: "vec2",
         5: "vec", 6: "vec4", 8: "mat", 9: "vec_int", 10: "vec_float",
         11: "vec_byte", 13: "objectid", 14: "vec_events"}

# Populated by main() from --namelist; decode() resolves through it.
_H2N: dict[int, str] = {}


def nm(h: int) -> str:
    return _H2N.get(h, f"<id:{h:08X}>")


class Node:
    __slots__ = ("hash", "props", "kids")

    def __init__(self, h: int):
        self.hash = h
        self.props: list = []
        self.kids: list = []


def parse_rtpc(blob: bytes) -> list[Node]:
    if blob[0:4] != b"RTPC":
        raise SystemExit(f"not RTPC, magic={blob[0:4]!r}")
    (ver,) = struct.unpack_from("<I", blob, 4)
    if ver != 1:
        raise SystemExit(f"RTPC version {ver}")
    nodes: list[Node] = []

    def read_node(o: int):
        return struct.unpack_from("<IIHH", blob, o)

    nh, doff, np, nc = read_node(8)
    nodes.append(Node(nh))
    queue = [(0, nh, doff, np, nc)]
    while queue:
        nid, _h, doff, np, nc = queue.pop(0)
        o = doff
        for _ in range(np):
            ph = struct.unpack_from("<I", blob, o)[0]
            pd, pt = blob[o + 4:o + 8], blob[o + 8]
            nodes[nid].props.append((ph, pd, pt))
            o += 9
        o = (doff + 9 * np + 3) & ~3
        for _ in range(nc):
            ch, cdoff, cnp, cnc = read_node(o)
            o += 12
            nodes.append(Node(ch))
            cid = len(nodes) - 1
            nodes[nid].kids.append(cid)
            queue.append((cid, ch, cdoff, cnp, cnc))
    return nodes


def load_names(path: str | None) -> dict[int, str]:
    h2n: dict[int, str] = {}
    if not path:
        return h2n
    with open(path, "rb") as f:
        for line in f.read().split(b"\n"):
            name = line.decode("ascii", "replace").rstrip("\r\n")
            if name:
                h2n.setdefault(hash_jenkins(name.encode("ascii", "replace")), name)
    return h2n


def decode(blob: bytes, pd: bytes, pt: int):
    if pt == 1:
        return ("int", struct.unpack("<i", pd)[0])
    if pt == 2:
        return ("float", struct.unpack("<f", pd)[0])
    (off,) = struct.unpack("<I", pd)
    try:
        if pt == 3:
            end = blob.index(b"\0", off)
            return ("string", blob[off:end].decode("ascii", "replace"))
        if pt in (4, 5, 6):
            n = {4: 2, 5: 3, 6: 4}[pt]
            return (f"vec{n}", struct.unpack(f"<{n}f", blob[off:off + 4 * n]))
        if pt == 8:
            return ("mat", struct.unpack("<16f", blob[off:off + 64]))
        if pt in (9, 10):
            (c,) = struct.unpack_from("<I", blob, off)
            if c > 512:
                return (TYPES[pt] + f"[{c}]", "BIG")
            fm = "<i" if pt == 9 else "<f"
            vals = struct.unpack(f"<{c}{fm[1]}", blob[off + 4:off + 4 + 4 * c])
            return (f"{TYPES[pt]}[{c}]", vals)
        if pt == 11:
            (c,) = struct.unpack_from("<I", blob, off)
            return (f"vec_byte[{c}]", blob[off + 4:off + 4 + min(c, 32)].hex())
        if pt == 14:
            (c,) = struct.unpack_from("<I", blob, off)
            pairs = []
            p = off + 4
            for _ in range(min(c, 32)):
                a, b = struct.unpack_from("<II", blob, p)
                p += 8
                pairs.append((nm(a), nm(b)))
            return (f"vec_events[{c}]", pairs)
        return (TYPES.get(pt, f"?{pt}"), f"off=0x{off:X}")
    except Exception as ex:  # noqa: BLE001 - dump must not die on one bad value
        return (TYPES.get(pt, "?"), f"ERR {ex}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("epe")
    ap.add_argument("--namelist", default=None)
    ap.add_argument("--node", default=None, help="only dump nodes with this name")
    ap.add_argument("--all", action="store_true", help="dump every property (default: summary + floats/ints/strings)")
    a = ap.parse_args()
    with open(a.epe, "rb") as f:
        blob = f.read()
    h2n = load_names(a.namelist)
    _H2N.update(h2n)

    nodes = parse_rtpc(blob)
    print(f"nodes: {len(nodes)}")
    for nid, nd in enumerate(nodes):
        if a.node and nm(nd.hash) != a.node:
            continue
        print(f"--- node#{nid} {nm(nd.hash)} props={len(nd.props)} kids={nd.kids}")
        if not a.all and not a.node and not any(
                k in nm(nd.hash).lower() for k in ("weapon", "turret", "hinge", "missile", "aim")):
            continue
        for ph, pd, pt in nd.props:
            typ, val = decode(blob, pd, pt)
            if not a.all and not a.node and typ not in ("int", "float", "string"):
                continue
            print(f"    {nm(ph)} [{typ}] = {val}")


if __name__ == "__main__":
    main()
