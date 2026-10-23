"""eetoc.py - compare an .ee's real SARC directory with an .ee.toc, or write a matching .toc.

Hypothesis under test (MODLOG §40): the game reads a dropzone .ee through the .ee.toc that
sits next to it -- for a vanilla-path override that is the VANILLA .toc from the archives,
whose (name, offset, size) records describe the vanilla layout. Change any inner file's size
or add/remove a file and the game reads the wrong bytes.

.ee  = AAF container ("AAF\\0", chunks of raw-deflate data tagged "EWAM") around a SARC v2.
.toc = the SARC directory as a flat list: u32 name_len, name, u32 offset, u32 size.

Usage:
  python eetoc.py compare <file.ee> <file.ee.toc>
  python eetoc.py write   <file.ee> -o <file.ee.toc>
"""
import argparse
import struct
import sys
import zlib


def unaaf(b):
    if b[:4] != b"AAF\0":
        raise SystemExit("not an AAF file")
    total, _, nchunks = struct.unpack_from("<III", b, 0x24)
    o, out = 0x30, bytearray()
    for _ in range(nchunks):
        csize, usize, step, magic = struct.unpack_from("<III4s", b, o)
        if magic != b"EWAM":
            raise SystemExit(f"bad chunk magic {magic!r} at {o}")
        out += zlib.decompress(b[o + 16:o + 16 + csize], -15)
        o += step
    if len(out) != total:
        raise SystemExit(f"AAF size mismatch {len(out)} != {total}")
    return bytes(out)


def sarc_dir(s):
    if s[4:8] != b"SARC":
        raise SystemExit("not a SARC stream")
    ver, dsize = struct.unpack_from("<II", s, 8)
    o, end, ents = 16, 16 + dsize, []
    while o < end:
        n = struct.unpack_from("<I", s, o)[0]
        if n == 0:
            break
        name = s[o + 4:o + 4 + n].split(b"\0")[0].decode()
        off, size = struct.unpack_from("<II", s, o + 4 + n)
        ents.append((name, off, size))
        o += 4 + n + 8
    return ents


def read_toc(b):
    o, ents = 0, []
    while o + 4 <= len(b):
        n = struct.unpack_from("<I", b, o)[0]
        name = b[o + 4:o + 4 + n].split(b"\0")[0].decode()
        off, size = struct.unpack_from("<II", b, o + 4 + n)
        ents.append((name, off, size))
        o += 4 + n + 8
    return ents


def write_toc(ents):
    # Names are stored at their exact length, no padding (vanilla's first record has
    # name_len 129).
    out = bytearray()
    for name, off, size in ents:
        nb = name.encode()
        out += struct.pack("<I", len(nb)) + nb + struct.pack("<II", off, size)
    return bytes(out)


def patch_toc(ee_raw, base_toc, internal=(), include_lod=False):
    """Rewrite a vanilla .toc for a modified .ee: same record order, offset-0 (external)
    records untouched, every other record's offset/size taken from the .ee, records for files
    the .ee no longer has dropped, and files the .ee adds appended (except .lod, which
    the shipped DaBaby .toc omits too).

    `internal`: name substrings whose offset-0 records are pointed INTO the .ee. Offset 0 means
    "not in this .ee, load from the archives" -- a modified file left at 0 is silently
    ignored (test-023: the repointed vehicle_parts.vmodc never took effect). The shipped
    DaBaby .toc gives every file it changed a real offset."""
    real = sarc_dir(unaaf(ee_raw))
    R = {n: (o, s) for n, o, s in real}
    out, seen = [], set()
    for n, o, s in base_toc:
        seen.add(n)
        if o == 0 and not any(k in n for k in internal):
            out.append((n, o, s))
        elif o == 0 and n not in R:
            raise SystemExit(f"--internal {n}: not present in the .ee")
        elif n in R:
            out.append((n,) + R[n])
    base_names = {n for n, _, _ in base_toc}
    new = [(n, o, s) for n, o, s in real
           if n not in base_names and (include_lod or not n.endswith(".lod")) and _is_new(n)]
    # New records go BEFORE the root .epe record, never after it. Vanilla and the shipped
    # DaBaby .toc both END with the entity's .epe; records after it are not preloaded before
    # the entity is built (test-035/036/038: appended meshes never drawn; test-037: an
    # appended .lod naming an already-listed mesh drew fine). MODLOG §52.
    at = len(out)
    if out and out[-1][0].endswith(".epe"):
        at -= 1
    return out[:at] + new + out[at:]


# Files the vanilla .ee carries but its .toc deliberately does not list (shared assets also
# in the global archives). Filled in by main() from the base .ee when one is given.
_VANILLA_UNLISTED = set()


def _is_new(n):
    return n not in _VANILLA_UNLISTED


def compare(ee_path, toc_path, quiet=False):
    real = sarc_dir(unaaf(open(ee_path, "rb").read()))
    toc = read_toc(open(toc_path, "rb").read())
    R = {n: (o, s) for n, o, s in real}
    T = {n: (o, s) for n, o, s in toc}
    only_ee = sorted(set(R) - set(T))
    only_toc = sorted(set(T) - set(R))
    moved = [n for n in set(R) & set(T) if R[n] != T[n]]
    ok = not (only_ee or only_toc or moved)
    print(f"{'MATCH' if ok else 'DIFFERS'}  ee={len(R)} toc={len(T)}  only_in_ee={len(only_ee)} "
          f"only_in_toc={len(only_toc)}  offset/size_mismatch={len(moved)}")
    if not quiet:
        for n in sorted(moved)[:8]:
            print(f"   {n}: ee {R[n]} toc {T[n]}")
        for n in only_ee[:5]:
            print("   only in ee :", n)
        for n in only_toc[:5]:
            print("   only in toc:", n)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("compare"); p.add_argument("ee"); p.add_argument("toc"); p.add_argument("-q", action="store_true")
    p = sub.add_parser("write"); p.add_argument("ee"); p.add_argument("-o", required=True)
    p = sub.add_parser("patch", help="vanilla .toc -> .toc matching a modified .ee")
    p.add_argument("ee"); p.add_argument("base_toc")
    p.add_argument("--base-ee", help="the known-good .ee the base .toc belongs to: its files "
                   "that the .toc does not list stay unlisted")
    p.add_argument("--internal", action="append", default=[],
                   help="name substring: read this file from the .ee, not the archives (repeatable)")
    p.add_argument("--include-lod", action="store_true",
                   help="also list appended .lod files (vanilla .tocs list their .lod files; test-034 "
                        "showed an unlisted new .lod leaves the body slot empty)")
    p.add_argument("-o", required=True)
    a = ap.parse_args()
    if a.cmd == "compare":
        sys.exit(0 if compare(a.ee, a.toc, a.q) else 1)
    if a.cmd == "patch":
        base = read_toc(open(a.base_toc, "rb").read())
        if a.base_ee:
            listed = {n for n, _, _ in base}
            _VANILLA_UNLISTED.update(n for n, _, _ in sarc_dir(unaaf(open(a.base_ee, "rb").read()))
                                     if n not in listed)
        ents = patch_toc(open(a.ee, "rb").read(), base, a.internal, a.include_lod)
        open(a.o, "wb").write(write_toc(ents))
        added = len(ents) - sum(1 for n, _, _ in ents if n in {b[0] for b in base})
        print(f"wrote {a.o}: {len(ents)} records ({added} appended)")
        return
    raw = open(a.ee, "rb").read()
    ents = sarc_dir(unaaf(raw))
    open(a.o, "wb").write(write_toc(ents))
    print(f"wrote {a.o}: {len(ents)} entries")


if __name__ == "__main__":
    main()
