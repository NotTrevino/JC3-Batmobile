"""adfdump.py - decode a JC3 ADF stat file (.wtunec/.vmodc) to readable text.

Format (Gibbed.JustCause3.FileFormats.AdfFile, all little-endian here):
  'ADF ', u32 version==4, then counts+offsets for instances, type
  definitions, string-hashes and the name table, total size, five zero u32s,
  comment stringZ. The name table gives every type/member/instance name, so
  ADF needs no external dictionary: member types arrive as type hashes
  (primitives 0x7515A207 float / 0x192FE633 int32 / ... / 0x8955583E string,
  see AdfTypeHashes), structs/arrays/inline-arrays/pointers/enums resolve
  through the embedded definitions. String members are s64 offsets.

  Offset convention (verified against game files): array/string data offsets
  are ABSOLUTE to the ADF file start. Decode instance bytes sliced at the
  instance offset while keeping ioff at the instance's file offset, i.e.
  dec(file[oo:oo+sz], ..., ioff=oo, base=0). Passing instance bytes with
  ioff=0 (or whole-file bytes with base=0) silently misdecodes every array
  into plausible-looking garbage while fixed-offset members stay correct.

Verified: w501_sam_missile.wtunec -> WeaponTuning{velocity=360.0,
max_range=500.0, ...}; identical parser decodes pistol/rifle/sniper/RPG/
FireLeech/grenade tunecs. detonation_time members are float32 (type hash
0x7515A207), NOT bools -- the neighbouring flags (detonate_on_impact,
missile_per_shot) are uint8.

Usage:
  python adfdump.py <file.wtunec> [--instance NAME] [--keys k1,k2,...]
Read-only; prints to stdout. --keys filters printed member paths to the
given substrings (e.g. velocity,detonation,angle).
"""
from __future__ import annotations

import argparse
import struct

PRIM = {0x580D0A62: ("int8", 1, "<b"), 0x0CA2821D: ("uint8", 1, "<B"),
        0xD13FCF93: ("int16", 2, "<h"), 0x86D152BD: ("uint16", 2, "<H"),
        0x192FE633: ("int32", 4, "<i"), 0x075E4E4F: ("uint32", 4, "<I"),
        0xAF41354F: ("int64", 8, "<q"), 0xA139E01F: ("uint64", 8, "<Q"),
        0x7515A207: ("float", 4, "<f"), 0xC609F663: ("double", 8, "<d")}
ADF_STR = 0x8955583E


class AR:
    def __init__(self, b: bytes, p: int = 0):
        self.b = b
        self.p = p

    def u32(self) -> int:
        v = struct.unpack_from("<I", self.b, self.p)[0]
        self.p += 4
        return v

    def s64(self) -> int:
        v = struct.unpack_from("<q", self.b, self.p)[0]
        self.p += 8
        return v

    def u64(self) -> int:
        v = struct.unpack_from("<Q", self.b, self.p)[0]
        self.p += 8
        return v

    def strz(self) -> str:
        e = self.b.index(b"\0", self.p)
        s = self.b[self.p:e].decode("ascii", "replace")
        self.p = e + 1
        return s


def parse_adf(blob: bytes):
    if struct.unpack_from("<I", blob, 0)[0] != 0x41444620:
        raise SystemExit(f"not ADF, magic={blob[0:4]!r}")
    if struct.unpack_from("<I", blob, 4)[0] != 4:
        raise SystemExit("ADF version != 4")
    r = AR(blob, 8)
    icount, ioff = r.u32(), r.u32()
    tcount, toff = r.u32(), r.u32()
    hcount, hoff = r.u32(), r.u32()
    ncount, noff = r.u32(), r.u32()
    r.u32()
    if any(r.u32() for _ in range(5)):
        raise SystemExit("ADF reserved fields nonzero")
    r.strz()
    r.p = noff
    lens = list(blob[noff:noff + ncount])
    r.p = noff + ncount
    names = []
    for ln in lens:
        names.append(r.b[r.p:r.p + ln].decode("ascii", "replace"))
        r.p += ln + 1
    r.p = toff
    tds = {}
    for _ in range(tcount):
        kind, size, _alg, nh = r.u32(), r.u32(), r.u32(), r.u32()
        tname, _fl, eth, eln = names[r.s64()], r.u32(), r.u32(), r.u32()
        mems = []
        if kind == 1:
            for _ in range(r.u32()):
                mems.append((names[r.s64()], r.u32(), r.u32(), r.u32(), r.u32(), r.u64()))
        elif r.u32() != 0:
            raise SystemExit(f"typedef {tname} tail nonzero")
        tds[nh] = {"name": tname, "kind": kind, "size": size,
                   "eth": eth, "eln": eln, "mems": mems}
    sh = {}
    r.p = hoff
    for _ in range(hcount):
        v = r.strz()
        sh[r.u32()] = v
        r.u32()
    r.p = ioff
    insts = []
    for _ in range(icount):
        nh2, th2, oo2, sz2, ni2 = r.u32(), r.u32(), r.u32(), r.u32(), r.s64()
        insts.append((names[ni2], th2, oo2, sz2))
    return tds, sh, insts


def _s_at(d: bytes, o: int):
    try:
        e = d.index(b"\0", o)
        if e - o > 200:
            return None
        s = d[o:e].decode("ascii", "replace")
        return s if all(32 <= ord(c) < 127 for c in s) else None
    except Exception:  # noqa: BLE001
        return None


def _match(keys, path: str) -> bool:
    return keys is None or any(k in path.lower() for k in keys or [])


def dec(d: bytes, tds: dict, sh: dict, ioff: int, tho: int, base: int, keys=None, path=""):
    sub_all = keys is not None and _match(keys, path)  # this node matches: whole subtree
    sub = None if sub_all else keys
    if tho in PRIM:
        if not _match(keys, path):
            return None
        tn, sz, fm = PRIM[tho]
        return f"{tn}={struct.unpack(fm, d[base:base + sz])[0]}"
    if tho == ADF_STR:
        if not _match(keys, path):
            return None
        (o,) = struct.unpack_from("<q", d, base)
        for c in (o, o - ioff):
            if 0 <= c < len(d):
                s = _s_at(d, c)
                if s is not None:
                    return f"str={s!r}"
        return "str=?"
    td = tds.get(tho)
    if td is None:
        return f"<type:{tho:08X}>"
    k, tn = td["kind"], td["name"]
    if k == 1:
        parts = []
        for m, th, _ms, mo, _a, _b in td["mems"]:
            subpath = f"{path}.{m}" if path else m
            v = dec(d, tds, sh, ioff, th, base + mo, sub, subpath)
            if v is not None:
                parts.append(f"{m}={v}")
        if sub is not None and not parts:
            return None
        return f"{tn}{{{';'.join(parts)}}}"
    if k == 4:
        eth, n = td["eth"], td["eln"]
        esz = PRIM[eth][1] if eth in PRIM else tds[eth]["size"]
        items = [dec(d, tds, sh, ioff, eth, base + i * esz, sub, f"{path}[{i}]")
                 for i in range(n)]
        items = [x for x in items if x is not None]
        if sub is not None and not items:
            return None
        return f"{tn}[{n}]=" + ",".join(items)
    if k == 3:
        o = struct.unpack_from("<q", d, base)[0]
        c = struct.unpack_from("<q", d, base + 8)[0]
        if o == 0 and c == 0:
            return tn + "[]=empty"
        eth = td["eth"]
        esz = PRIM[eth][1] if eth in PRIM else tds[eth]["size"]
        o2 = o - ioff if 0 <= o - ioff < len(d) else o
        if not (0 <= o2 < len(d)) or c > 4096:
            return tn + "[]@?"
        items = [dec(d, tds, sh, ioff, eth, o2 + i * esz, sub, f"{path}[{i}]")
                 for i in range(min(c, 64))]
        items = [x for x in items if x is not None]
        if sub is not None and not items:
            return None
        return f"{tn}[{c}]=" + ",".join(items)
    if k == 2:
        if not _match(keys, path):
            return None
        return f"{tn}->0x{struct.unpack_from('<Q', d, base)[0]:X}"
    if k == 9:
        if not _match(keys, path):
            return None
        (v,) = struct.unpack_from("<I", d, base)
        return f"{tn}={sh.get(v, '?')!r}"
    if not _match(keys, path):
        return None
    return f"{tn}(k{k})={d[base:base + td['size']].hex()}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tunec")
    ap.add_argument("--instance", default=None)
    ap.add_argument("--keys", default=None, help="comma-separated member-name filters")
    a = ap.parse_args()
    keys = [k.strip().lower() for k in a.keys.split(",")] if a.keys else None
    with open(a.tunec, "rb") as f:
        blob = f.read()
    tds, sh, insts = parse_adf(blob)
    for iname, th, oo, sz in insts:
        if a.instance and iname != a.instance:
            continue
        d = blob[oo:oo + sz]
        print(f"== instance {iname!r} type={tds[th]['name']} ==")
        out = dec(d, tds, sh, oo, th, 0, keys, iname)
        print(out if out is not None else "(no matches)")


if __name__ == "__main__":
    main()
