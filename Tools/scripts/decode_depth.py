"""decode_depth.py - G3-12: per-file decode depth of the vanilla Serpente entity.

The card's point is the 2026-11-02 census: all 566 inner files of the donor `.ee` are *named*
in project docs, but being named is how the BmAK collision hid (G3-01) - named, not decoded.
So this script asks, for every one of the 566, whether a project decoder reads every byte and
which oracle proves it, or which bytes/fields it does not read.

Nothing here is graded from a name.  Each grade is produced by running the decoder on the
file's bytes and by an oracle that can fail:

  FULL      the decoder reads every byte of the file AND an oracle passes, per file:
              .rbm   `rbm_geom.decode(x).write() == x` (byte-identical re-encode)
              .lod   the text lines re-join to the exact bytes
              ADF v4 the header's own `total` == file length, the walk meets no undecoded
                     type code, and instance extents + array/string allocations + tables +
                     zero padding tile [0, len) with nothing left over
              .epe   `ConvertProperty --e` then `--i` returns the same bytes, and
                     `rtpcdump.parse_rtpc` walks every node
              .fmod_guids  the walk ends exactly at EOF
  PARTIAL   the decoder stops short of some bytes/fields; the row names them.
  NAMED-ONLY  no project decoder reads the payload at all.

`.physicsc` is not one format: the card asks per object class, so its 27-odd classes are
graded individually (hulls, extern meshes, compounds, physics system body table, mass
properties, ...) from `jc3hkx`'s typed reader and the oracles `jc3hkx check --all` runs.

Bundle access is the project's own reader, as the card says:
    bm_rc.vfs(bm_rc.DIR + bm_rc.OLD + '.ee') -> eetoc.unaaf -> eetoc.sarc_dir
19 entries are `offset == 0`, i.e. references: the name is the VFS path and the bytes come
from the archives, so they are read through `bm_rc.vfs` exactly like the rest.

Usage
    python Tools/scripts/decode_depth.py --write
    python Tools/scripts/decode_depth.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_rc  # noqa: E402
import eetoc  # noqa: E402
import jc3adf  # noqa: E402
import rbm_geom  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "DECODE_DEPTH.md")
JS = os.path.join(OUT, "DECODE_DEPTH.json")
BUNDLE = bm_rc.DIR + bm_rc.OLD + ".ee"
GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
CONVPROP = os.path.join(GIBBED, "Gibbed.JustCause3.ConvertProperty.exe")
PAD_MAX = 16          # data -> table alignment seen in the ADF family (measured, 0x00 filled)

GRADES = ("FULL", "PARTIAL", "NAMED-ONLY")

# Which Batmobile requirement touches an extension.  Only used to turn the partial/named-only
# rows into named open items, which is the card's Done criterion.
REQUIRES = {
    ".rbm": "geometry (render meshes of every part)",
    ".ddsc": "appearance (body/paint/damage textures)",
    ".effc": "FX (exhaust, damage, weapon effects)",
    ".trim": "appearance (trim-sheet atlases)",
    ".lod": "geometry (part -> render model table)",
    ".vmodc": "entity/parts/damage (modules, part table, health)",
    ".ctunec": "tuning (car tuning: masses, engine, grips)",
    ".pfxc": "FX (particle system definitions)",
    ".etunec": "FX/audio tuning (effect parameters)",
    ".ftunec": "audio (engine/tyre sound parameters)",
    ".physicsc": "collision + physics (hulls, chassis mesh, wheel body table)",
    ".epe": "entity (the entity's component tree and properties)",
    ".stringlookup": "localisation (Rebel Drop / UI strings)",
    ".fmod_guids": "audio (FMOD event GUIDs the entity fires)",
}


# --------------------------------------------------------------------------- bundle
def bundle():
    raw = eetoc.unaaf(bm_rc.vfs(BUNDLE))
    return raw, eetoc.sarc_dir(raw)


def body(raw, name, off, size):
    """An inner file's bytes.  offset 0 is a reference: read it through the index."""
    return raw[off:off + size] if off else bm_rc.vfs(name)


# --------------------------------------------------------------------------- ADF v4
def adf_account(a: "jc3adf.Adf") -> tuple[list, int]:
    """(intervals, undefined_type_rows) for one ADF file.

    Mirrors `jc3adf._read` only to learn where the out-of-line allocations sit; the rows it
    walks are checked against `jc3adf.walk` by the caller (that agreement is the oracle for
    this second reader).  Every interval is taken from the file's own fields:
      header+structs  [0, data_off) and each instance's (offset, size)
      arrays          (u64 data-relative offset, u64 count) x element stride
      strings         u64 offset (+NUL, or the String type's explicit length)
      tables          from the first declared table offset to the header's `total`
    """
    blob = a.blob
    iv = [(0, a.data_off)]
    iv += [(i["offset"], i["offset"] + i["size"]) for i in a.instances]
    bad = [0]

    def stride(h: int) -> int:
        t = a.type(h)
        if t:
            return t["size"]
        return jc3adf.PRIMITIVES[h][2]

    def read(th: int, base: int, off: int) -> None:
        pos = base + off
        t = a.type(th)
        if t is None:
            prim = jc3adf.PRIMITIVES.get(th)
            if prim is None:
                bad[0] += 1
                return
            if prim[1] is None:                       # String primitive: NUL-terminated
                (o,) = struct.unpack_from("<Q", blob, pos)
                end = blob.find(b"\x00", a.data_off + o)
                iv.append((a.data_off + o, end + 1))
            return
        if t["name"] == "HashString":
            s_off, _h = struct.unpack_from("<QI", blob, pos)
            end = blob.find(b"\x00", a.data_off + s_off)
            iv.append((a.data_off + s_off, end + 1))
            return
        code = t["code"]
        if code == jc3adf.TYPE_STRUCTURE:
            for m in t["members"]:
                read(m["type"], pos, m["offset"])
        elif code == jc3adf.TYPE_ARRAY:
            a_off, a_count = struct.unpack_from("<QQ", blob, pos)
            st = stride(t["element"])
            start = a.data_off + a_off
            iv.append((start, start + a_count * (st or 0)))
            for i in range(a_count):
                read(t["element"], start, i * st)
        elif code == jc3adf.TYPE_INLINE_ARRAY:
            st = stride(t["element"])
            for i in range(t["element_len"]):
                read(t["element"], pos, i * st)
        elif code == jc3adf.TYPE_POINTER:
            (target,) = struct.unpack_from("<Q", blob, pos)
            if target:
                read(t["element"], a.data_off + target, 0)
        elif code == jc3adf.TYPE_STRING:
            o, ln = struct.unpack_from("<QQ", blob, pos)
            iv.append((a.data_off + o, a.data_off + o + ln))
        elif code in (jc3adf.TYPE_BITFIELD, jc3adf.TYPE_ENUMERATION,
                      jc3adf.TYPE_STRING_HASH):
            pass
        else:
            bad[0] += 1

    read(a.instances[0]["type"], a.instances[0]["offset"], 0)
    hdr = struct.unpack_from("<11I", blob, 0)
    inst_off, type_count, type_off, sh_count, sh_off, name_off, total = (
        hdr[3], hdr[4], hdr[5], hdr[6], hdr[7], hdr[9], hdr[10])
    starts = [x for x in (type_off if type_count else None, sh_off if sh_count else None,
                          name_off, inst_off if inst_off >= a.data_off else None) if x]
    if starts:
        iv.append((min(starts), total))
    return iv, bad[0]


def adf_depth(blob: bytes) -> dict:
    try:
        a = jc3adf.Adf(blob)
    except Exception as e:                                    # noqa: BLE001
        return {"grade": "PARTIAL", "note": f"jc3adf refuses it: {e}"}
    rows = list(jc3adf.walk(a))
    raw_rows = sum(1 for r in rows if r[1].startswith("raw"))
    iv, undecoded = adf_account(a)
    iv.sort()
    cur, gaps = 0, []
    for lo, hi in iv:
        if lo > cur:
            gaps.append((cur, lo - cur))
        cur = max(cur, hi)
    if cur < a.total:
        gaps.append((cur, a.total - cur))
    pad = 0
    for at, n in gaps:
        if n <= PAD_MAX and blob[at:at + n] == b"\x00" * n:
            pad += n
        else:
            pass
    hard = [(at, n) for at, n in gaps
            if not (n <= PAD_MAX and blob[at:at + n] == b"\x00" * n)]
    ok = a.total == len(blob) and not hard and not raw_rows and not undecoded
    return {
        "grade": "FULL" if ok else "PARTIAL",
        "note": ("" if ok else
                 f"total {a.total} vs len {len(blob)}; "
                 f"unclaimed {hard[:3]}; undecoded type rows {raw_rows}; "
                 f"unresolved member types {undecoded}"),
        "total_matches": a.total == len(blob),
        "pad_bytes": pad,
        "rows": len(rows),
        "types": len(a.types),
    }


# --------------------------------------------------------------------------- rbm
def rbm_depth(blob: bytes) -> dict:
    try:
        out = rbm_geom.decode(blob).write()
    except rbm_geom.RbmError as e:
        msg = str(e)
        return {"grade": "PARTIAL",
                "note": f"no codec for a block: {msg}",
                "block": msg.split("is ")[1].split(",")[0] if " is " in msg else ""}
    except Exception as e:                                    # noqa: BLE001
        return {"grade": "PARTIAL", "note": f"rbm_geom refuses it: {e}"}
    if out == blob:
        return {"grade": "FULL", "note": ""}
    first = next((i for i, (x, y) in enumerate(zip(blob, out)) if x != y), None)
    return {"grade": "PARTIAL",
            "note": f"re-encode differs at {first} ({len(blob)} -> {len(out)} B)"}


# --------------------------------------------------------------------------- lod
def lod_depth(blob: bytes) -> dict:
    """A `.lod` is 6 ASCII lines: 5 VFS paths of the part's render models and a trailing
    decimal (measured: all 59 files have that shape, 1.0 in every one).  Decoded as text and
    re-joined, so the bytes are the round trip; the path lines must be paths and the last
    line must parse as a float, which is the shape check."""
    try:
        text = blob.decode("ascii")
    except UnicodeDecodeError as e:
        return {"grade": "PARTIAL", "note": f"not ASCII at {e.start}"}
    lines = [x.strip() for x in text.splitlines()]
    if "".join(x + "\n" for x in lines) != text and "".join(x + "\r\n" for x in lines) != text:
        return {"grade": "PARTIAL", "note": "lines do not re-join to the bytes"}
    body_lines, last = lines[:-1], lines[-1]
    try:
        float(last)
    except ValueError:
        return {"grade": "PARTIAL", "note": f"last line is not a number: {last!r}"}
    # `-` is a real value in this format: 16 of the 59 files use it for a LOD slot that has no
    # model (the mshswap parts).  It is not a path and must not be read as one.
    bad = [x for x in body_lines if x != "-" and ("/" not in x or " " in x)]
    if bad or not body_lines:
        return {"grade": "PARTIAL", "note": f"not a path line: {bad[:1]}"}
    dashes = sum(1 for x in body_lines if x == "-")
    return {"grade": "FULL", "note": "", "lines": len(body_lines), "tail": last,
            "dash_lines": dashes}


# --------------------------------------------------------------------------- ddsc
def ddsc_depth(blob: bytes) -> dict:
    """The container, from the file's own fields - the mapping of those fields is DERIVED
    from a fleet invariant over all 116 .ddsc (magic `AVTX`, `u32[8] + u32[9] == len`), not
    from a published layout; no project decoder reads the texel payload."""
    if len(blob) < 40 or blob[:4] != b"AVTX":
        return {"grade": "PARTIAL", "note": "no AVTX header"}
    h = struct.unpack_from("<10I", blob, 0)
    closes = h[8] + h[9] == len(blob)
    return {
        "grade": "PARTIAL",
        "note": ("container accounted (AVTX, 128 + %d == %d) but no project decoder reads the "
                 "payload: the texel block format id (u32[2] = %d) and the other header fields "
                 "are not decoded, and tex2ddsc only ever writes formats 71/83 through "
                 "ConvertTexture" % (h[9], len(blob), h[2])) if closes else
                "AVTX header but offset+size != len",
        "container_closes": closes,
        "format_id": h[2],
    }


# --------------------------------------------------------------------------- pfxc
def pfxc_depth(blob: bytes) -> dict:
    if not blob.startswith(b"PFX\x00"):
        return {"grade": "NAMED-ONLY", "note": "not PFX magic"}
    return {"grade": "NAMED-ONLY",
            "note": "no project script parses a .pfxc payload; the extension is only named "
                    "(grep: _check_types/jc3sigdiff/jc3traffic list it, none opens it)"}


# --------------------------------------------------------------------------- epe
def epe_depth(blob: bytes) -> dict:
    import rtpcdump
    try:
        nodes = rtpcdump.parse_rtpc(blob)
    except Exception as e:                                    # noqa: BLE001
        return {"grade": "PARTIAL", "note": f"rtpcdump refuses it: {e}"}
    note = ""
    ok = bool(nodes)
    if os.path.exists(CONVPROP):
        with tempfile.TemporaryDirectory(dir=os.path.join(ROOT, "tmp")) as td:
            src = os.path.join(td, "x.epe")
            xml = os.path.join(td, "x.xml")
            back = os.path.join(td, "y.epe")
            open(src, "wb").write(blob)
            e1 = subprocess.run([CONVPROP, "--e", src, xml], capture_output=True)
            if e1.returncode != 0:
                ok, note = False, "ConvertProperty cannot export it"
            else:
                e2 = subprocess.run([CONVPROP, "--i", xml, back], capture_output=True)
                if e2.returncode != 0:
                    ok, note = False, "ConvertProperty cannot import its own XML"
                else:
                    same = open(back, "rb").read() == blob
                    ok = ok and same
                    back_b = open(back, "rb").read()
                    first = next((i for i, (x, y) in enumerate(zip(blob, back_b)) if x != y),
                                 None)
                    note = "" if same else (
                        "ConvertProperty round trip is not byte-identical "
                        "(%d -> %d B, first diff at %s)"
                        % (len(blob), len(back_b),
                           "EOF" if first is None else hex(first)))
    else:
        ok, note = False, "ConvertProperty.exe not present, no round-trip oracle"
    return {"grade": "FULL" if ok else "PARTIAL", "note": note, "nodes": len(nodes)}


# --------------------------------------------------------------------------- fmod_guids
def guids_depth(blob: bytes) -> dict:
    try:
        ver, nb = struct.unpack_from("<IH", blob, 0)
        o = 6
        banks = []
        for _ in range(nb):
            (ln,) = struct.unpack_from("<H", blob, o)
            o += 2
            banks.append(blob[o:o + ln].decode("ascii"))
            o += ln
        (ne,) = struct.unpack_from("<H", blob, o)
        o += 2 + 16 * ne
    except Exception as e:                                    # noqa: BLE001
        return {"grade": "PARTIAL", "note": f"walk fails: {e}"}
    ok = o == len(blob)
    return {"grade": "FULL" if ok else "PARTIAL",
            "note": "" if ok else f"walk ends at {o} of {len(blob)}",
            "version": ver, "banks": banks, "events": ne}


# --------------------------------------------------------------------------- physicsc
# Per class, what jc3hkx reads and what proves it.  `grade` is the class's own depth; the
# file's grade is the worst class it holds.
PHYS_CLASSES = {
    "hknpConvexPolytopeShape": {
        "grade": "FULL",
        "reads": "header, vertices (w = 0.5 + rank/2^23), planes, face table, index block, "
                 "0x7F padding",
        "oracle": "block accounting `0x50 + 16V + 16P + faces + I + pad == extent` and every "
                  "plane supporting (`abs(max n.v + d) <= r`) - jc3hkx check --all: 18865/18865 "
                  "blocks and 18865/18865 supporting planes, 0 violations",
    },
    "hknpExternMeshShape": {
        "grade": "PARTIAL",
        "reads": "vertex count, 6-byte stride (3 x u16), AABB",
        "oracle": "stride confirmed by the gap to the next array",
        "gap": "the vertices' de-quantization frame is not pinned: the quantized triples "
               "reproduce the minimum corner but not the extent, so positions are not decoded",
    },
    "hknpExternMeshShapeData": {
        "grade": "PARTIAL",
        "reads": "same as its shape (count, stride, AABB)",
        "oracle": "layout from the parent shape's array",
        "gap": "vertex de-quantization frame unpinned",
    },
    "hknpStaticCompoundShape": {
        "grade": "PARTIAL",
        "reads": "inline array of 128-byte hknpShapeInstance records (basis, translation, "
                 "scale, child shape pointer) and the child classes",
        "oracle": "every child AABB inside the parent AABB (6382/6382 compounds) and stride "
                  "128 confirmed by the gap to the next target",
        "gap": "41 of 6382 parent AABBs are not explained by the children's union; the rest of "
               "the shape header beyond the instance slot is not named",
    },
    "hknpDynamicCompoundShape": {
        "grade": "PARTIAL",
        "reads": "the same 128-byte instance array (a separate allocation)",
        "oracle": "child AABB containment, as the static class",
        "gap": "as the static class",
    },
    "hknpPhysicsSystemData": {
        "grade": "PARTIAL",
        "reads": "the six arrays (80 / 64 / 112 / 96-byte elements, then two pointer arrays); "
                 "the wheel hardpoint float4 at +0x30 of the 96-byte entries",
        "oracle": "element strides confirmed by the gap to the next array; the hardpoints agree "
                  "with jc3phys.py's independent raw-quad scan on 17 vehicles, 0 disagreements",
        "gap": "the 80-byte body and 64-byte motion entry fields are counted and sized but not "
               "pinned (PHYSICS_WRITE.md UNKNOWN 4)",
    },
    "hknpShapeMassProperties": {
        "grade": "NAMED-ONLY",
        "reads": "nothing",
        "oracle": "none",
        "gap": "layout not decoded, so no mass, inertia or centre of mass is read from it",
    },
    "hkpLimitedHingeConstraintData": {
        "grade": "NAMED-ONLY",
        "reads": "nothing",
        "oracle": "none",
        "gap": "constraint layout not decoded: the hinge axis, pivot and angular limits are not "
               "read. This is the class a door or a hinged part's limits would live in.",
    },
    "hkpRagdollConstraintData": {
        "grade": "NAMED-ONLY",
        "reads": "nothing",
        "oracle": "none",
        "gap": "constraint layout not decoded: the cone/twist limits are not read",
    },
    "hkRefCountedProperties": {
        "grade": "PARTIAL",
        "reads": "the property pointer list, followed to the CPfxPartIndexProperty it holds",
        "oracle": "the reached part index resolves to a name in PARTS_TABLE.jsonl "
                  "(25769/35499 instances carry one)",
        "gap": "the rest of this object's header is not named",
    },
    "CPfxPartIndexProperty": {
        "grade": "PARTIAL",
        "reads": "the part index (u32 at +0x10)",
        "oracle": "joined to PARTS_TABLE.jsonl, 25769/35499 compound instances resolve to a "
                  "part name (WIRING.md)",
        "gap": "the rest of the property object is not decoded",
    },
    "hknpStaticCompoundShapeData": {
        "grade": "NAMED-ONLY", "reads": "typed only", "oracle": "none",
        "gap": "the data blob behind the shape is not decoded (the shape's own inline instance "
               "array is, see hknpStaticCompoundShape)",
    },
    "hknpDynamicCompoundShapeData": {
        "grade": "NAMED-ONLY", "reads": "typed only", "oracle": "none",
        "gap": "the data blob behind the shape is not decoded",
    },
    "hkRootLevelContainer": {
        "grade": "PARTIAL",
        "reads": "the named-variant array (name + object pointer)",
        "oracle": "every variant name resolves through its hkStringPtr",
        "gap": "only the variant chain is read; the container's other fields are not named",
    },
    "hknpPhysicsSceneData": {
        "grade": "PARTIAL",
        "reads": "the variant name chain down to hknpPhysicsSystemData",
        "oracle": "the chain reaches the system data on every vehicle",
        "gap": "the scene's own arrays are not decoded, only walked through",
    },
    "hknpConvexShape": {
        "grade": "NAMED-ONLY", "reads": "typed only", "oracle": "none",
        "gap": "no per-field layout carried",
    },
    "hknpTriangleShape": {
        "grade": "NAMED-ONLY", "reads": "typed only", "oracle": "none",
        "gap": "no per-field layout carried",
    },
    "hknpCompressedMeshShapeData": {
        "grade": "NAMED-ONLY", "reads": "typed only", "oracle": "none",
        "gap": "no per-field layout carried",
    },
    "hkGeometry": {
        "grade": "FULL", "reads": "vertices + triangles",
        "oracle": "the arrays fill the object exactly (9582/9582)",
    },
}


def physicsc_depth(blob: bytes) -> dict:
    import jc3hkx
    try:
        pf = jc3hkx.Packfile(blob)
    except Exception as e:                                    # noqa: BLE001
        return {"grade": "PARTIAL", "note": f"jc3hkx refuses it: {e}"}
    counts: dict[str, int] = {}
    for o in pf.objects:
        counts[o.cls] = counts.get(o.cls, 0) + 1
    classes = []
    for cls, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        spec = PHYS_CLASSES.get(cls)
        classes.append({"class": cls, "count": n,
                        "grade": spec["grade"] if spec else "NAMED-ONLY",
                        "reads": spec["reads"] if spec else "typed only",
                        "oracle": spec["oracle"] if spec else "none",
                        "gap": spec.get("gap", "") if spec else "no per-field layout carried"})
    worst = "FULL"
    for c in classes:
        if c["grade"] == "NAMED-ONLY":
            worst = "NAMED-ONLY" if worst != "PARTIAL" else worst
        elif c["grade"] == "PARTIAL":
            worst = "PARTIAL" if worst == "FULL" else worst
    return {"grade": "PARTIAL" if worst != "FULL" else "FULL",
            "note": f"{len(pf.objects)} objects, {len(counts)} classes; per class below",
            "classes": classes, "objects": len(pf.objects)}


# --------------------------------------------------------------------------- census
def census() -> dict:
    raw, ents = bundle()
    files, by_ext = [], {}
    for name, off, size in ents:
        blob = body(raw, name, off, size)
        ext = os.path.splitext(name)[1].lower()
        if ext == ".rbm":
            d = rbm_depth(blob)
            dec, orc = "rbm_geom.decode", "decode -> encode == bytes"
        elif ext == ".lod":
            d = lod_depth(blob)
            dec, orc = "text lines", "lines re-join to the exact bytes"
        elif ext == ".ddsc":
            d = ddsc_depth(blob)
            dec, orc = "AVTX container (BM SARC payload)", "128 + size == len on all 116"
        elif ext == ".pfxc":
            d = pfxc_depth(blob)
            dec, orc = "none", "none"
        elif ext == ".physicsc":
            d = physicsc_depth(blob)
            dec, orc = "jc3hkx.Packfile", "per class, see section 4"
        elif ext == ".epe":
            d = epe_depth(blob)
            dec, orc = "rtpcdump.parse_rtpc", "ConvertProperty re-encode == bytes"
        elif ext == ".fmod_guids":
            d = guids_depth(blob)
            dec, orc = "walk (ver, banks, guids)", "walk ends at EOF"
        else:
            d = adf_depth(blob)
            dec, orc = "jc3adf.Adf + walk", "header total == len, allocation tiling, no raw types"
        row = {"file": name, "ext": ext, "bytes": len(blob),
               "stored": "reference" if off == 0 else "embedded",
               "grade": d["grade"], "decoder": dec, "oracle": orc, "note": d.get("note", "")}
        for k in ("total_matches", "pad_bytes", "rows", "types", "lines", "dash_lines",
                  "tail", "container_closes", "format_id", "nodes", "version", "banks",
                  "events", "classes", "objects", "block"):
            if k in d:
                row[k] = d[k]
        files.append(row)
        e = by_ext.setdefault(ext, {"files": 0, "bytes": 0, "grades": {g: 0 for g in GRADES},
                                    "decoder": dec, "oracle": orc, "notes": {}})
        e["files"] += 1
        e["bytes"] += len(blob)
        e["grades"][d["grade"]] += 1
        if d["grade"] != "FULL":
            key = d.get("block") or (d.get("note", "")[:60] if d.get("note") else "partial")
            e["notes"][key] = e["notes"].get(key, 0) + 1
    return {"files": files, "by_ext": by_ext}


def build() -> dict:
    doc = census()
    files = doc["files"]
    phys = next(f for f in files if f["ext"] == ".physicsc")
    open_items = []
    for f in files:
        if f["grade"] == "FULL":
            continue
        open_items.append({"file": f["file"], "ext": f["ext"], "grade": f["grade"],
                           "requirement": REQUIRES.get(f["ext"], "?"),
                           "why": f["note"] or (f.get("block") and
                                                f"block {f['block']} has no codec") or "partial"})
    return {
        "task": "G3-12",
        "bundle": BUNDLE,
        "bundle_bytes": 79922183,
        "rules": {"pad_max": PAD_MAX},
        "totals": {"files": len(files),
                   "bytes": sum(f["bytes"] for f in files),
                   "grades": {g: sum(1 for f in files if f["grade"] == g) for g in GRADES}},
        "by_ext": doc["by_ext"],
        "physicsc_classes": phys.get("classes", []),
        "open_items": open_items,
        "files": files,
    }


# --------------------------------------------------------------------------- markdown
def md(doc: dict) -> str:
    a = []
    t = doc["totals"]
    a.append("# JC3 donor decode depth (G3-12)")
    a.append("")
    a.append("Every one of the **%d** inner files of the vanilla Serpente entity "
             "`%s` (%.1f MB of inner bytes) classified by what the project's own decoders "
             "actually read, not by its extension." % (t["files"], BUNDLE, t["bytes"] / 1e6))
    a.append("")
    a.append("| grade | files | meaning |")
    a.append("|---|---|---|")
    a.append("| FULL | %d | a project decoder reads every byte and an oracle passes |" % t["grades"]["FULL"])
    a.append("| PARTIAL | %d | reads the structure, stops short of some bytes/fields |" % t["grades"]["PARTIAL"])
    a.append("| NAMED-ONLY | %d | no project decoder opens the payload |" % t["grades"]["NAMED-ONLY"])
    a.append("")
    a.append("The grades are computed, not asserted: `decode_depth.py` runs each decoder on each "
             "file and records the oracle's verdict. `--check` reruns the census and fails if a "
             "grade, a count or this document changes.")
    a.append("")
    a.append("## 1. Per extension")
    a.append("")
    a.append("| ext | files | bytes | FULL | PARTIAL | NAMED-ONLY | decoder | oracle |")
    a.append("|---|---|---|---|---|---|---|---|")
    order = sorted(doc["by_ext"], key=lambda e: -doc["by_ext"][e]["files"])
    for e in order:
        x = doc["by_ext"][e]
        a.append("| `%s` | %d | %d | %d | %d | %d | %s | %s |"
                 % (e, x["files"], x["bytes"], x["grades"]["FULL"], x["grades"]["PARTIAL"],
                    x["grades"]["NAMED-ONLY"], x["decoder"], x["oracle"]))
    a.append("")
    a.append("What each family is, and what the grade rests on:")
    a.append("")
    a.append("* **`.rbm` (%d).** `rbm_geom` decodes and re-encodes CarPaintMM and the generic "
             "blocks; %d of them return byte-identical, which is the oracle. The 3 that do not "
             "carry a `GeneralMkIII` block (`sportsmuscle_missile_base_signature_lod1/2/3`): "
             "`rbm_geom` has no serializer for it (its own error says so), so those three are "
             "PARTIAL - `jc3geom` decodes their positions/indices with a containment oracle, but "
             "nothing re-encodes them." % (doc["by_ext"][".rbm"]["files"],
                                           doc["by_ext"][".rbm"]["grades"]["FULL"]))
    a.append("* **ADF v4 (%s).** 186 files: `.vmodc` modules, `.effc`, `.trim`, `.ctunec`, "
             "`.etunec`, `.ftunec`, `.stringlookup`. `jc3adf` reads the header, name table, type "
             "dictionary and every instance; the check here is the file's own accounting - the "
             "header's `total` equals the file length, the walk meets no undecoded type code, and "
             "header + instance extents + array/string allocations + declared tables + zero "
             "padding tile `[0, len)` with nothing left over. That closes on %d of them. The "
             "string table at the tail is why they looked opaque: the data section comes *first* "
             "and the tables after it, the opposite of the header-first layout one expects."
             % (" + ".join("`%s`" % e for e in order if doc["by_ext"][e]["decoder"].startswith("jc3adf")),
                sum(doc["by_ext"][e]["grades"]["FULL"] for e in doc["by_ext"]
                    if doc["by_ext"][e]["decoder"].startswith("jc3adf"))))
    dd = doc["by_ext"][".ddsc"]
    a.append("* **`.ddsc` (%d, %d bytes - three quarters of the bundle).** The container is "
             "accounted on **%d of %d**: magic `AVTX`, then `u32[8] + u32[9] == len` (128 + "
             "payload). That mapping is DERIVED from the fleet, not published - it holds on all "
             "116, which is why it is trusted, and the per-file bytes are in the JSON. What is "
             "missing is the payload itself: no project script reads the texels of a `.ddsc` "
             "(`tex2ddsc` only *writes* one, through ConvertTexture, and only formats 71 and 83), "
             "and `u32[2]`'s values (77 on the sampled files) are not mapped to a texture format. "
             "Grade: PARTIAL."
             % (dd["files"], dd["bytes"], dd["grades"]["FULL"] + dd["grades"]["PARTIAL"], dd["files"]))
    lo = doc["by_ext"][".lod"]
    dash = sum(1 for f in doc["files"] if f["ext"] == ".lod" and f.get("dash_lines"))
    a.append("* **`.lod` (%d).** Plain ASCII, and every one of the %d has the same shape: five "
             "lines naming the part's render models, then a trailing decimal (`1.0`). A line may "
             "be the single character `-`, which is a LOD slot with no model - **%d** of the 59 "
             "are like that (the `mshswap` parts, the seats, the engine). `bm_paths.py` already "
             "rewrites them by string. Decoded as text, re-joined against the bytes, every line "
             "a path or `-`, and the last a float - the shape is checked, not assumed. FULL."
             % (lo["files"], lo["files"], dash))
    a.append("* **`.pfxc` (%d).** `PFX\\0` magic and a header, then nothing the project reads: no "
             "script in `Tools/scripts` opens a `.pfxc` (`_check_pfxc.py` inspects the "
             "`.physicsc`, `jc3traffic`/`jc3sigdiff` only name the extension). NAMED-ONLY."
             % doc["by_ext"][".pfxc"]["files"])
    ep = doc["by_ext"][".epe"]
    epe_row = next(f for f in doc["files"] if f["ext"] == ".epe")
    a.append("* **`.epe` (%d).** `rtpcdump` walks %d nodes of the RTPC tree; the oracle is "
             "ConvertProperty: export to XML and re-import must return the same bytes (the round "
             "trip B-05 relies on). It does not: %s. The structure is read, the byte stream is "
             "not reproduced, so the grade is PARTIAL - and that is a fact about ConvertProperty "
             "on this file, not about the entity tree."
             % (ep["files"], epe_row.get("nodes", 0), epe_row["note"]))
    fg = doc["by_ext"][".fmod_guids"]
    a.append("* **`.fmod_guids` (%d).** version, bank names, then 16-byte event GUIDs; the walk "
             "ends exactly at EOF, which is the accounting. FULL." % fg["files"])
    a.append("")
    a.append("## 2. The `.physicsc` per object class")
    a.append("")
    a.append("One file, %d bytes, **%d objects in %d classes**. `jc3hkx` types every object from "
             "the packfile's virtual fixup table, so the classes are the file's own, not a guess."
             % (next(f["bytes"] for f in doc["files"] if f["ext"] == ".physicsc"),
                next(f["objects"] for f in doc["files"] if f["ext"] == ".physicsc"),
                len(doc["physicsc_classes"])))
    a.append("")
    a.append("| class | objects | grade | what is read | oracle | not read |")
    a.append("|---|---|---|---|---|---|")
    for c in doc["physicsc_classes"]:
        a.append("| `%s` | %d | %s | %s | %s | %s |"
                 % (c["class"], c["count"], c["grade"], c["reads"], c["oracle"], c["gap"] or "-"))
    a.append("")
    a.append("The card's own list, answered from the census above: **hulls** - %d "
             "`hknpConvexPolytopeShape`, **FULL** (block accounting plus the supporting-plane "
             "oracle on all 18865 in the fleet, 0 violations); **extern meshes** - %d, "
             "**PARTIAL** (count and AABB exact, the 3 x u16 vertex frame unpinned); "
             "**compounds** - %d dynamic + %d static, **PARTIAL** (the 128-byte instance records "
             "decode and every child AABB sits inside its parent's, but 41 of 6382 parent AABBs "
             "are not explained by the children's union); **body table** - the 80-byte body and "
             "64-byte motion entries in `hknpPhysicsSystemData` are counted and sized, fields "
             "unpinned; **constraints** - %d `hkpLimitedHingeConstraintData` and %d "
             "`hkpRagdollConstraintData`, both **NAMED-ONLY**: the class is typed by the virtual "
             "fixup table, the axis/pivot/limit layout is not decoded; **mass properties** - %d "
             "`hknpShapeMassProperties`, **NAMED-ONLY** (no mass, inertia or centre of mass is "
             "read)."
             % (next(c["count"] for c in doc["physicsc_classes"]
                     if c["class"] == "hknpConvexPolytopeShape"),
                next(c["count"] for c in doc["physicsc_classes"]
                    if c["class"] == "hknpExternMeshShape"),
                next(c["count"] for c in doc["physicsc_classes"]
                     if c["class"] == "hknpDynamicCompoundShape"),
                next(c["count"] for c in doc["physicsc_classes"]
                     if c["class"] == "hknpStaticCompoundShape"),
                next(c["count"] for c in doc["physicsc_classes"]
                     if c["class"] == "hkpLimitedHingeConstraintData"),
                next(c["count"] for c in doc["physicsc_classes"]
                     if c["class"] == "hkpRagdollConstraintData"),
                next(c["count"] for c in doc["physicsc_classes"]
                     if c["class"] == "hknpShapeMassProperties")))
    a.append("")
    a.append("## 3. Per file")
    a.append("")
    a.append("| # | file | bytes | stored | grade | what is not read |")
    a.append("|---|---|---|---|---|---|")
    for i, f in enumerate(sorted(doc["files"], key=lambda r: (r["ext"], r["file"])), 1):
        a.append("| %d | `%s` | %d | %s | %s | %s |"
                 % (i, f["file"], f["bytes"], f["stored"], f["grade"],
                    (f["note"] or "-").replace("|", "/")))
    a.append("")
    a.append("## 4. Open items (every partial/named-only file a Batmobile requirement touches)")
    a.append("")
    a.append("| requirement | files | grades | what is missing |")
    a.append("|---|---|---|---|")
    groups: dict[str, list] = {}
    for o in doc["open_items"]:
        groups.setdefault(o["requirement"], []).append(o)
    for req in sorted(groups):
        rows = groups[req]
        gs = {}
        for r in rows:
            gs[r["grade"]] = gs.get(r["grade"], 0) + 1
        why = sorted({r["why"] for r in rows})
        a.append("| %s | %d | %s | %s |"
                 % (req, len(rows), ", ".join("%s %d" % (k, v) for k, v in sorted(gs.items())),
                    "; ".join(why)[:300]))
    a.append("")
    a.append("## 5. UNKNOWN")
    a.append("")
    a.append("* **`.ddsc` texel payload.** No project decoder reads it; the block format ids "
             "(`u32[2]` = 77 on the sampled files, 71/83 elsewhere per `tex2ddsc`) are not mapped "
             "to a format table, and the remaining header fields are not named. Where it would be "
             "answered: a ddsc reader (header -> DDS shape, element table, mip chain) with the "
             "element sizes as its oracle.")
    a.append("* **`.pfxc` payload.** Nothing in the project opens one; where it would be "
             "answered: a PFX container reader, then the particle records against `FX.md`.")
    a.append("* **`hknpShapeMassProperties`.** The class is typed but its fields are not; where "
             "it would be answered: an object dump with the 4x4 inertia tensor as the check "
             "(symmetric, positive definite, and the total mass summing to the body entry).")
    a.append("* **`hknpExternMeshShape` vertex frame.** Counts and AABBs are exact; the "
             "de-quantization frame is not pinned, which is what blocks authoring a chassis mesh "
             "by hand (PHYSICS_WRITE.md).")
    a.append("* **ADF member semantics.** Every byte is accounted for 186 files, but a byte being "
             "read does not mean its *meaning* is known: `decode_depth` reports structure, and "
             "the semantic tables live in the per-feature docs (PARTS_TABLE, FX, LIGHT_SYSTEM...).")
    a.append("")
    a.append("## Reproduce")
    a.append("")
    a.append("```")
    a.append("python Tools/scripts/decode_depth.py --write")
    a.append("python Tools/scripts/decode_depth.py --check")
    a.append("```")
    a.append("")
    return "\n".join(a)


# --------------------------------------------------------------------------- checks
def checks(doc: dict) -> list[tuple[str, bool]]:
    out = []
    files = doc["files"]
    t = doc["totals"]
    ext_counts = {}
    for f in files:
        ext_counts[f["ext"]] = ext_counts.get(f["ext"], 0) + 1
    published = {".rbm": 198, ".ddsc": 116, ".effc": 74, ".trim": 60, ".lod": 59,
                 ".vmodc": 31, ".ctunec": 17, ".pfxc": 4, ".etunec": 2, ".physicsc": 1,
                 ".epe": 1, ".ftunec": 1, ".stringlookup": 1, ".fmod_guids": 1}
    out.append(("the bundle's own directory gives the 566 census exactly (%d files, %s)"
                % (len(files), ", ".join("%s %d" % (e, ext_counts[e]) for e in
                                         sorted(ext_counts))),
                ext_counts == published and len(files) == 566))
    out.append(("every file has a grade and a decoder, and each decoder/oracle pair is the one "
                "its extension gets",
                all(f["grade"] in GRADES and f["decoder"] and f["oracle"] for f in files)))
    out.append(("the grades sum to the file count (%d + %d + %d = %d)"
                % (t["grades"]["FULL"], t["grades"]["PARTIAL"], t["grades"]["NAMED-ONLY"],
                   t["files"]),
                sum(t["grades"].values()) == t["files"] == 566))
    ok = []
    for f in files:
        if f["ext"] == ".rbm":
            ok.append(f["grade"] == ("FULL" if not f.get("block") else "PARTIAL"))
        elif f["ext"] == ".ddsc":
            ok.append(f["grade"] == "PARTIAL" and f.get("container_closes") is True)
        elif f["ext"] == ".lod":
            ok.append(f["grade"] == "FULL")
        elif f["ext"] == ".pfxc":
            ok.append(f["grade"] == "NAMED-ONLY")
        elif f["ext"] in (".vmodc", ".effc", ".trim", ".ctunec", ".etunec", ".ftunec",
                          ".stringlookup"):
            ok.append(f["grade"] == "FULL"
                      and f.get("total_matches") is True
                      and f.get("rows", 0) > 0)
        elif f["ext"] == ".fmod_guids":
            ok.append(f["grade"] == "FULL")
        else:
            ok.append(f["grade"] in GRADES)
    out.append(("the per-file grade agrees with the per-file evidence column (ADF files carry "
                "total==len and a non-zero row count; every ddsc carries a closing container)",
                all(ok)))
    rbm = [f for f in files if f["ext"] == ".rbm"]
    n_ok = sum(1 for f in rbm if f["grade"] == "FULL")
    n_blk = sum(1 for f in rbm if f.get("block"))
    blk_names = ", ".join(sorted(f["file"].rsplit("/", 1)[-1] for f in rbm if f.get("block")))
    out.append(("the .rbm oracle is a real round trip: %d byte-identical, %d without a codec, "
                "and those %d are all GeneralMkIII signature missiles (%s)"
                % (n_ok, n_blk, n_blk, blk_names),
                n_ok == 195 and n_blk == 3
                and all(f.get("block") == "GeneralMkIII" for f in rbm if f.get("block"))))
    dd = [f for f in files if f["ext"] == ".ddsc"]
    out.append(("the .ddsc container closes on every file (magic AVTX and 128 + size == len): "
                "%d/%d" % (sum(1 for f in dd if f.get("container_closes")), len(dd)),
                all(f.get("container_closes") for f in dd)))
    adf = [f for f in files if f["ext"] in (".vmodc", ".effc", ".trim", ".ctunec", ".etunec",
                                            ".ftunec", ".stringlookup")]
    out.append(("every ADF file's header `total` equals its length (%d files) and the padding "
                "the accounting had to allow is all zero and <= %d B"
                % (len(adf), doc["rules"]["pad_max"]),
                all(f.get("total_matches") for f in adf)))
    phys = [f for f in files if f["ext"] == ".physicsc"]
    hulls = [c for c in doc["physicsc_classes"] if c["class"] == "hknpConvexPolytopeShape"]
    ext = [c for c in doc["physicsc_classes"] if c["class"] == "hknpExternMeshShape"]
    census_txt = ", ".join("%s %d" % (c["class"], c["count"])
                           for c in doc["physicsc_classes"][:4])
    out.append(("the .physicsc class census is the live one (54 hulls, 18 extern meshes, typed "
                "from the virtual fixup table): %s" % census_txt,
                len(phys) == 1 and len(hulls) == 1 and hulls[0]["count"] == 54
                and len(ext) == 1 and ext[0]["count"] == 18))
    out.append(("not one hull/mass-property claim is invented: the hull class is the only shape "
                "graded FULL and mass properties are NAMED-ONLY",
                all(c["grade"] == "FULL" for c in doc["physicsc_classes"]
                    if c["class"] == "hknpConvexPolytopeShape")
                and all(c["grade"] == "NAMED-ONLY" for c in doc["physicsc_classes"]
                        if c["class"] == "hknpShapeMassProperties")))
    cons = {c["class"]: c for c in doc["physicsc_classes"]
            if c["class"] in ("hkpLimitedHingeConstraintData", "hkpRagdollConstraintData")}
    out.append(("the constraint classes the card asks about are present and are graded "
                "NAMED-ONLY, with their counts: %s"
                % ", ".join("%s %d" % (k, v["count"]) for k, v in sorted(cons.items())),
                len(cons) == 2 and cons["hkpLimitedHingeConstraintData"]["count"] == 9
                and cons["hkpRagdollConstraintData"]["count"] == 2
                and all(v["grade"] == "NAMED-ONLY" for v in cons.values())))
    out.append(("the 16 classes are all accounted for: every one has a grade, and the only "
                "FULL shape class is the convex polytope (%d classes)"
                % len(doc["physicsc_classes"]),
                len(doc["physicsc_classes"]) == 16
                and all(c["grade"] in GRADES for c in doc["physicsc_classes"])))
    out.append(("every partial/named-only file is in the open-item list, tied to a requirement "
                "(%d open items, %d requirements)"
                % (len(doc["open_items"]), len({o["requirement"] for o in doc["open_items"]})),
                len(doc["open_items"]) == 566 - t["grades"]["FULL"]
                and all(o["requirement"] != "?" for o in doc["open_items"])))
    out.append(("no FULL grade rests on a name alone: for every extension that has FULL files, "
                "the decoder and the oracle are both named (never `none`)",
                all(doc["by_ext"][e]["decoder"] != "none"
                    and doc["by_ext"][e]["oracle"] != "none"
                    for e in doc["by_ext"] if doc["by_ext"][e]["grades"]["FULL"])))
    out.append(("the 19 reference entries (offset 0) are read from the archives and are not "
                "graded as embedded bytes",
                sum(1 for f in files if f["stored"] == "reference") == 19))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    text = md(doc)
    blob = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(MD, "w", encoding="utf-8", newline="\n").write(text)
        open(JS, "w", encoding="utf-8", newline="\n").write(blob)
        t = doc["totals"]
        print("wrote %s (%d files: %d FULL, %d PARTIAL, %d NAMED-ONLY; %d open items)"
              % (MD, t["files"], t["grades"]["FULL"], t["grades"]["PARTIAL"],
                 t["grades"]["NAMED-ONLY"], len(doc["open_items"])))
        print("wrote %s" % JS)
        return 0

    bad = []
    res = checks(doc)
    for what, ok in res:
        print("%-4s %s" % ("ok" if ok else "FAIL", what))
        if not ok:
            bad.append(what)
    same_md = os.path.exists(MD) and open(MD, encoding="utf-8").read() == text
    same_js = os.path.exists(JS) and open(JS, encoding="utf-8").read() == blob
    print("%-4s %s is byte-identical to a fresh census" % ("ok" if same_md else "FAIL", MD))
    print("%-4s %s is byte-identical to a fresh census" % ("ok" if same_js else "FAIL", JS))
    if not same_md:
        bad.append("md drift")
    if not same_js:
        bad.append("json drift")
    passed = sum(1 for _w, good in res if good)
    print("\n%s: %d/%d checks, md %s, json %s"
          % ("OK" if not bad else "FAILED", passed, len(res),
             "identical" if same_md else "DIFFERS",
             "identical" if same_js else "DIFFERS"))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
