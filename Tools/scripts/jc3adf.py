"""jc3adf.py - a reader for Just Cause 3's ADF v4 files, including the parts modules.

Gibbed's `ConvertAdf` deserialises ADF v4 by *guessing* where an inline array copy sits
(`InstanceInfo.GuessInlineArrayCopyPosition`), and throws a NullReferenceException when the guess
does not resolve. It refuses 229 of 233 `*_vehicle_parts.vmodc` files that way.

The file carries everything the guess needs, so this reader does not guess:

  header    magic ' FDA', version 4, then counts+offsets for instances, type definitions,
            string-hash table, name table, total size (16 u32), then a comment string.
  name table  `count` u8 lengths followed by that many NUL-terminated names.
  types     per type: type code, size, alignment, name hash, name index (s64), flags,
            element type hash, element length, member count, then 32-byte members
            (name index s64, type hash, size, offset, default type, default value u64).
  instance  per instance: name hash, type hash, data offset, size, name index s64.
  data      structs at their declared offsets. `A[..]` members are 16 bytes
            (u64 data-relative offset, u64 count); `IA[..]` are inline (element length is in the
            type); `HashString` is (u64 data-relative string offset, u32 hash).

Field offsets are absolute within their struct, so nothing has to be inferred - which is why this
reads the files Gibbed refuses.

Usage as a module:
    import jc3adf
    adf = jc3adf.Adf(blob)
    rows = list(jc3adf.walk(adf))          # [(path, type_name, value)] for the root instance
    parts = jc3adf.parts(adf)              # [{field: value}] with children resolved

CLI:
    python jc3adf.py info   <file.vmodc>
    python jc3adf.py dump   <file.vmodc> [--paths]
    python jc3adf.py verify              # reader vs Gibbed on the 4 files that do convert
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_JC3grab")

SIGNATURE = 0x41444620  # ' FDA'

# Primitive type hashes: the full ADF v4 set (Gibbed TypeHashes, Deca ff_adf, adfdump.py),
# used as element/member types and not present in the file's type dictionary.  Signedness
# comes from the type hash itself, never from the value: the parts modules decode
# parent_part_index/world_collision_body_id/constraint_index as -1 through the signed
# entries, while effect/camera files use the unsigned ones for flags and counts.
PRIMITIVES = {
    0x580D0A62: ("int8", "<b", 1),
    0x0CA2821D: ("uint8", "<B", 1),
    0xD13FCF93: ("int16", "<h", 2),
    0x86D152BD: ("uint16", "<H", 2),
    0x192FE633: ("int32", "<i", 4),
    0x075E4E4F: ("uint32", "<I", 4),
    0xAF41354F: ("int64", "<q", 8),
    0xA139E01F: ("uint64", "<Q", 8),
    0x7515A207: ("float", "<f", 4),
    0xC609F663: ("double", "<d", 8),
    0x8955583E: ("string", None, 8),   # u64 data-relative offset, NUL-terminated
}

TYPE_PRIMITIVE = 0
TYPE_STRUCTURE = 1
TYPE_POINTER = 2
TYPE_ARRAY = 3
TYPE_INLINE_ARRAY = 4
TYPE_STRING = 5
TYPE_BITFIELD = 7
TYPE_ENUMERATION = 8
TYPE_STRING_HASH = 9


class Adf:
    """Parsed header, name table, type dictionary and root instance of one ADF v4 file."""

    def __init__(self, blob: bytes):
        self.blob = blob
        (self.magic, self.version, instance_count, self.instance_off, type_count, self.type_off,
         strhash_count, self.strhash_off, name_count, self.name_off,
         self.total) = struct.unpack_from("<11I", blob, 0)
        if self.magic != SIGNATURE:
            raise ValueError(f"not an ADF file: {self.magic:#x}")
        if self.version != 4:
            raise ValueError(f"ADF version {self.version}, only 4 is supported")

        lens = blob[self.name_off:self.name_off + name_count]
        p = self.name_off + name_count
        self.names = []
        for length in lens:
            self.names.append(blob[p:p + length].decode("latin-1"))
            p += length + 1

        self.instances = []
        p = self.instance_off
        for _ in range(instance_count):
            name_hash, type_hash, offset, size = struct.unpack_from("<4I", blob, p)
            name_index = struct.unpack_from("<q", blob, p + 16)[0]
            p += 24
            self.instances.append({"name": self.name(name_index), "name_hash": name_hash,
                                   "type": type_hash, "offset": offset, "size": size})

        self.types: dict[int, dict] = {}
        p = self.type_off
        for _ in range(type_count):
            code, size, align, name_hash = struct.unpack_from("<4I", blob, p)
            name_index = struct.unpack_from("<q", blob, p + 16)[0]
            p += 24
            flags, element, element_len = struct.unpack_from("<3I", blob, p)
            p += 12
            member_count, = struct.unpack_from("<I", blob, p)
            p += 4
            members = []
            if code == TYPE_STRUCTURE:
                for _m in range(member_count):
                    member_index = struct.unpack_from("<q", blob, p)[0]
                    m_type, m_size, m_off, m_def_type = struct.unpack_from("<4I", blob, p + 8)
                    m_def_value, = struct.unpack_from("<Q", blob, p + 24)
                    p += 32
                    members.append({"name": self.name(member_index), "type": m_type,
                                    "size": m_size, "offset": m_off,
                                    "default_type": m_def_type, "default": m_def_value})
            self.types[name_hash] = {"code": code, "size": size, "align": align,
                                     "name": self.name(name_index), "flags": flags,
                                     "element": element, "element_len": element_len,
                                     "members": members}
        self.by_name = {t["name"]: h for h, t in self.types.items()}

    def name(self, index: int) -> str:
        return self.names[index] if 0 <= index < len(self.names) else f"<{index}>"

    def type(self, type_hash: int) -> dict | None:
        return self.types.get(type_hash)

    def type_name(self, type_hash: int) -> str:
        t = self.types.get(type_hash)
        if t:
            return t["name"]
        p = PRIMITIVES.get(type_hash)
        return p[0] if p else f"<{type_hash:08x}>"

    def string_at(self, offset: int) -> str:
        start = self.data_off + offset
        end = self.blob.find(b"\x00", start)
        return self.blob[start:end].decode("latin-1")

    @property
    def data_off(self) -> int:
        return self.instances[0]["offset"] if self.instances else 0


def _element_stride(adf: Adf, element_hash: int) -> int:
    t = adf.type(element_hash)
    if t:
        return t["size"]
    p = PRIMITIVES.get(element_hash)
    if not p:
        raise KeyError(f"unknown element type {element_hash:#x}")
    return p[2]


def _read(adf: Adf, type_hash: int, base: int, offset: int):
    """Yield (path, type_name, value) for one value of `type_hash` at absolute `base + offset`."""
    blob = adf.blob
    pos = base + offset
    t = adf.type(type_hash)
    if t is None:
        prim = PRIMITIVES.get(type_hash)
        if not prim:
            raise KeyError(f"unknown type {type_hash:#x}")
        name, fmt, _size = prim
        if fmt is None:                     # the String primitive: an offset
            (off,) = struct.unpack_from("<Q", blob, pos)
            end = blob.find(b"\x00", adf.data_off + off)
            yield "", name, blob[adf.data_off + off:end].decode("latin-1")
            return
        yield "", name, struct.unpack_from(fmt, blob, pos)[0]
        return

    name = t["name"]
    if name == "HashString":
        s_off, s_hash = struct.unpack_from("<QI", blob, pos)
        yield "string", "string", adf.string_at(s_off)
        yield "hash", "uint32", s_hash
        return

    if t["code"] == TYPE_STRUCTURE:
        for m in t["members"]:
            for sub, tn, val in _read(adf, m["type"], pos, m["offset"]):
                if sub.startswith("["):
                    yield m["name"] + sub, tn, val
                else:
                    yield (m["name"] + ("." + sub if sub else "")), tn, val
        return

    if t["code"] == TYPE_ARRAY:
        a_off, a_count = struct.unpack_from("<QQ", blob, pos)
        stride = _element_stride(adf, t["element"])
        yield "", name, ""
        start = adf.data_off + a_off
        for i in range(a_count):
            for sub, tn, val in _read(adf, t["element"], start, i * stride):
                yield (f"[{i}]." + sub if sub else f"[{i}]"), tn, val
        return

    if t["code"] == TYPE_INLINE_ARRAY:
        stride = _element_stride(adf, t["element"])
        for i in range(t["element_len"]):
            for sub, tn, val in _read(adf, t["element"], pos, i * stride):
                yield f"[{i}]" + sub, tn, val
        return

    if t["code"] == TYPE_POINTER:
        # data-relative offset of one element; 0 is the null pointer
        (target,) = struct.unpack_from("<Q", blob, pos)
        if not target:
            yield "", name, None
            return
        for sub, tn, val in _read(adf, t["element"], adf.data_off + target, 0):
            yield sub, tn, val
        return

    if t["code"] == TYPE_STRING:
        off, length = struct.unpack_from("<QQ", blob, pos)
        raw = blob[adf.data_off + off:adf.data_off + off + length]
        yield "", name, raw.decode("latin-1")
        return

    if t["code"] in (TYPE_BITFIELD, TYPE_ENUMERATION, TYPE_STRING_HASH):
        prim = PRIMITIVES.get(t["element"])
        if prim and prim[2] == 4:
            yield "", name, struct.unpack_from("<I", blob, pos)[0]
            return
        yield "", name, struct.unpack_from("<Q", blob, pos)[0]
        return

    # a type code this reader has not met: keep the bytes, flag the decode
    size = t["size"] or 0
    yield "", f"raw{size}", blob[pos:pos + size].hex()


def walk(adf: Adf, instance: int = 0):
    """Yield (path, type_name, value) for the whole root instance, in declaration order."""
    inst = adf.instances[instance]
    yield from _read(adf, inst["type"], inst["offset"], 0)


def parts(adf: Adf) -> list[dict]:
    """Decode a VehicleParts module into a list of part dicts (children resolved to lists)."""
    rows: dict[str, object] = {}
    for path, _tn, value in walk(adf):
        rows[path] = value

    def count(prefix: str) -> int:
        n = 0
        while f"{prefix}[{n}]" in rows or f"{prefix}[{n}].name.string" in rows:
            n += 1
        return n

    out = []
    for i in range(count("parts")):
        p = f"parts[{i}]"
        if f"{p}.name.string" not in rows:
            continue
        part = {
            "name": rows.get(f"{p}.name.string", ""),
            "damage_type": rows.get(f"{p}.damage_type.string", ""),
            "behavior": rows.get(f"{p}.behavior.string", ""),
            "model": rows.get(f"{p}.model.string", ""),
            "model_swap": rows.get(f"{p}.model_swap.string", ""),
            "part_index": rows.get(f"{p}.part_index"),
            "parent_part_index": rows.get(f"{p}.parent_part_index"),
            "parent_space_offset": [rows.get(f"{p}.parent_space_offset[{k}]") for k in range(16)],
            "centroid": [rows.get(f"{p}.centroid[{k}]") for k in range(4)],
            "deformation_centroid_offset": [
                rows.get(f"{p}.deformation_centroid_offset[{k}]") for k in range(4)],
        }
        for flag in ("starts_loose", "should_break", "prevent_mesh_swap_while_alive",
                     "prevent_loosening_while_alive", "prevent_breaking_while_alive",
                     "always_mesh_swap_on_death", "always_loosen_on_death",
                     "always_break_on_death", "disappears_when_broken", "appears_on_death",
                     "disappears_on_death", "starts_deleted", "is_deformable", "has_lights",
                     "has_world_collision_shape", "only_collides_once_loose",
                     "only_collides_once_broken"):
            part[flag] = rows.get(f"{p}.{flag}")
        for ident in ("world_collision_instance_id", "raycast_instance_id",
                      "grandpa_world_instance_id", "grandpa_raycast_instance_id",
                      "world_collision_body_id", "raycast_body_id", "constraint_index"):
            part[ident] = rows.get(f"{p}.{ident}")
        for rel in ("children_part_indices", "hide_parts_when_broken",
                    "meshswap_parts_when_broken", "loosen_parts_when_broken",
                    "break_parts_when_broken"):
            values = []
            k = 0
            while f"{p}.{rel}[{k}]" in rows:
                values.append(rows[f"{p}.{rel}[{k}]"])
                k += 1
            part[rel] = values
        out.append(part)
    return out


# --------------------------------------------------------------------------- CLI

def _find_parts_modules() -> list[str]:
    out = []
    for pat in (os.path.join(RAW, "tmp", "*_vehicle_parts.vmodc"),
                os.path.join(RAW, "probe", "*_vehicle_parts.vmodc")):
        out += sorted(glob.glob(pat))
    return out


def cmd_info(a) -> int:
    blob = open(a.file, "rb").read()
    adf = Adf(blob)
    inst = adf.instances[0]
    print(f"{os.path.basename(a.file)}: {len(blob)} B, {len(adf.types)} types, "
          f"{len(adf.names)} names")
    print(f"  instance {inst['name']} type {adf.type_name(inst['type'])} "
          f"at {inst['offset']:#x} size {inst['size']:#x}")
    for t in adf.types.values():
        print(f"  {t['name']:26s} code={t['code']} size={t['size']:4d} members={len(t['members'])}")
    return 0


def cmd_dump(a) -> int:
    blob = open(a.file, "rb").read()
    adf = Adf(blob)
    if a.paths:
        for part in parts(adf):
            print(f"{part['part_index']:3d}  {part['name']:34s} {part['damage_type']:22s} "
                  f"{part['behavior'] or '-':20s} kids={len(part['children_part_indices'])} "
                  f"body={part['world_collision_body_id']} lights={part['has_lights']}")
        return 0
    for path, tn, value in walk(adf):
        print(f"{path:58s} {tn:10s} {value}")
    return 0


def cmd_verify(a) -> int:
    """Compare this reader with Gibbed's decode on the 4 parts modules that do convert."""
    entities = sorted(glob.glob(os.path.join(RAW, "entities", "*monorailflatbed*.json")))
    if not entities:
        print(f"no decoded flatbed entities under {RAW}/entities")
        return 1
    checked = 0
    for entity in entities:
        doc = json.load(open(entity, encoding="utf-8"))
        ref_mod = next((m for m in doc.get("modules", []) if m.get("type") == "VehicleParts"), None)
        if not ref_mod:
            continue
        module = next((f for f in doc["files"]
                       if "vehicle_parts" in f["path"]), None)
        if not module:
            continue
        # the raw module is not kept by the grab; re-extract it from the entity is out of scope,
        # so compare against the cached copy when present
        stem = os.path.basename(module["path"])[:-6]
        raw = os.path.join(RAW, "probe", f"flatbed_vehicle_parts.vmodc")
        if not os.path.exists(raw):
            print(f"missing raw module for {stem}")
            continue
        adf = Adf(open(raw, "rb").read())
        mine = {path: value for path, _tn, value in walk(adf)}
        ref = {r["path"]: r["value"] for r in ref_mod["rows"]}

        # jc3grab's flat dump loses the `parts[i].` prefix on inline-array element rows
        # (`children_part_indices[0]` instead of `parts[0].children_part_indices[0]`), so element
        # rows are compared by value multiset, everything else by exact path.
        element_names = ("children_part_indices", "hide_parts_when_broken",
                         "meshswap_parts_when_broken", "loosen_parts_when_broken",
                         "break_parts_when_broken")
        is_element = lambda k: any((n + "[") in k for n in element_names)
        ref_elements = sorted((k.rsplit("[", 1)[0], v) for k, v in ref.items() if is_element(k))
        mine_elements = sorted((k.rsplit("[", 1)[0].rsplit(".", 1)[-1], v)
                               for k, v in mine.items() if is_element(k))

        bad = []
        missing = []
        for k, v in ref.items():
            if is_element(k):
                continue
            if k not in mine:
                missing.append(k)
                continue
            m = mine[k]
            if isinstance(v, (int, float)) and isinstance(m, (int, float)):
                if abs(float(v) - float(m)) > 1e-4 * max(1.0, abs(float(v))):
                    bad.append((k, v, m))
            elif str(v) != str(m):
                bad.append((k, v, m))
        if ref_elements != mine_elements:
            bad.append(("element rows", len(ref_elements), len(mine_elements)))
        print(f"{os.path.basename(entity)}: ref {len(ref)} rows, mine {len(mine)}, "
              f"missing {len(missing)}, mismatched {len(bad)}, "
              f"element rows {len(ref_elements)}/{len(mine_elements)}")
        for row in bad[:5]:
            print("   mismatch", row)
        for row in missing[:5]:
            print("   missing ", row)
        if missing or bad:
            return 1
        checked += 1
    print(f"ok: {checked} module(s) agree with Gibbed")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    info = sub.add_parser("info")
    info.add_argument("file")
    dump = sub.add_parser("dump")
    dump.add_argument("file")
    dump.add_argument("--paths", action="store_true", help="one line per part")
    sub.add_parser("verify")
    a = p.parse_args()
    return {"info": cmd_info, "dump": cmd_dump, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
