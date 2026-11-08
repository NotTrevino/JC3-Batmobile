"""Read Batman: Arkham Knight (UE3, version 863 / licensee 800016) cooked packages.

No external tools. Handles the chunked container, the name/import/export tables and the
Batman property-tag format used in cooked objects:

    int16  Type      // 1 Byte, 2 Int, 3 Bool, 4 Float, 5 Object, 6 Name, 7 String, 8 Class,
                     // 9 Array, 10 Struct, 11 Vector, 12 Rotator, 13 Str, 14 Map, 15 Fixed,
                     // 16 ObjectNCR, 17 Guid; 0 = end of the property list
    uint16 Offset    // byte offset of the field in the native class layout
    ...              // simple types: the value follows inline, no name is stored
                     // complex types: FName name, int32 size, int32 array index, then the data

This is the format documented in UEViewer's UnObject.cpp (FPropertyTagBat2) and proven on the
Batmobile package: `RVehicleSimBatmobile SimulationModel` reads named structs and floats.

Usage:
    python Tools/scripts/upk_read.py <package.upk> [--dump NAME] [--json OUT]
"""
import argparse
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lzo1x import lzo1x_decompress  # noqa: E402  (local pure-Python LZO1X)

PKG_TAG = b"\xc1\x83\x2a\x9e"

# EPropType (Unreal/UnObject.cpp), fixed engine enum
TYPE_NAMES = {
    0: "None", 1: "ByteProperty", 2: "IntProperty", 3: "BoolProperty",
    4: "FloatProperty", 5: "ObjectProperty", 6: "NameProperty", 7: "StringProperty",
    8: "ClassProperty", 9: "ArrayProperty", 10: "StructProperty", 11: "VectorProperty",
    12: "RotatorProperty", 13: "StrProperty", 14: "MapProperty",
    15: "FixedArrayProperty", 16: "ObjectNCRProperty", 17: "GuidProperty",
}
# serialized inline, without a name (the object's field offset identifies it)
# Payload bytes behind a tag header, by type id.  `17` (GuidProperty) is **32**, not the 16 an
# FGuid occupies: the cooked stream writes the 16-byte value and a second 16-byte half behind it.
# Measured on `Playable_Batmobile_SF`'s SpotLightComponent (248 bytes): consuming 16 stops the walk
# at byte 146 with `unknown_type_27275`, consuming 32 re-syncs to byte 246 and every later tag
# resolves to a BmSDK offset (LightGuid 0x1cc, LightmapGuid 0x1dc, Brightness 0x1f0, LightColor
# 0x200, CastShadows 0x220).  All 1,778 guid-bearing records in objects.jsonl desynced at the guid
# before this; all 134 light components now walk to `eof` with 0 unresolved tags.
SIMPLE = {2: 4, 3: 4, 4: 4, 6: 8, 11: 12, 12: 12, 13: 0, 16: 4, 17: 32}
# serialized with FName + size + array index
NAMED = {1, 5, 7, 8, 9, 10, 14, 15}


class UpkError(Exception):
    pass


def _fstr(buf, o):
    if o + 4 > len(buf):
        raise UpkError("string length overruns buffer at %#x" % o)
    n = struct.unpack_from("<i", buf, o)[0]
    if n == 0:
        return "", o + 4
    if n > 0:
        if o + 4 + n > len(buf):
            raise UpkError("string overruns buffer at %#x" % o)
        return buf[o + 4:o + 4 + n].rstrip(b"\0").decode("latin-1"), o + 4 + n
    m = -n
    if o + 4 + 2 * m > len(buf):
        raise UpkError("wide string overruns buffer at %#x" % o)
    return buf[o + 4:o + 4 + 2 * m].decode("utf-16-le").rstrip("\0"), o + 4 + 2 * m


def _dechunk(raw, start):
    """Decompress the UE3 chunk list beginning at `start`; returns (bytes, next_offset)."""
    out = bytearray()
    q = start
    while q + 16 <= len(raw) and raw[q:q + 4] == PKG_TAG:
        block, csize, usize = struct.unpack_from("<III", raw, q + 4)
        if block == 0 and csize == 0 and usize == 0:
            break
        p = q + 16
        pairs = []
        total = 0
        while total < usize:
            if p + 8 > len(raw):
                raise UpkError("chunk at %#x is truncated" % q)
            bc, bu = struct.unpack_from("<II", raw, p)
            p += 8
            if bc == 0 or bu == 0:
                raise UpkError("zero sub-block in chunk at %#x" % q)
            pairs.append((bc, bu))
            total += bu
        if total != usize:
            raise UpkError("chunk at %#x lists %d bytes, header says %d" % (q, total, usize))
        for bc, bu in pairs:
            blob = raw[p:p + bc]
            try:
                part = zlib.decompress(blob)
            except zlib.error:
                part = lzo1x_decompress(blob)
            if len(part) != bu:
                raise UpkError("sub-block at %#x decoded to %d, expected %d" % (p, len(part), bu))
            out += part
            p += bc
        q = p
    if not out:
        raise UpkError("no chunks at %#x" % start)
    return bytes(out), q


class Package:
    def __init__(self, path):
        self.path = path
        self.raw = open(path, "rb").read()
        self.version = struct.unpack_from("<H", self.raw, 4)[0]
        self.licensee = struct.unpack_from("<H", self.raw, 6)[0]
        self.header_size = struct.unpack_from("<i", self.raw, 8)[0]
        self.group, o = _fstr(self.raw, 12)
        self.flags = struct.unpack_from("<I", self.raw, o)[0]
        o += 4
        (self.name_count, self.name_offset,
         self.export_count, self.export_offset,
         self.import_count, self.import_offset) = struct.unpack_from("<6i", self.raw, o)
        self.image = self._image()
        self.names = self._read_names()
        self.imports = self._read_imports()
        self.exports = self._read_exports()

    # ---------------- container ----------------

    def _image(self):
        """Logical package image: the on-disk header prefix + decompressed body."""
        raw = self.raw
        if self.raw[self.name_offset:self.name_offset + 4] and self._looks_like_names(self.raw):
            return raw
        start = raw.find(PKG_TAG, self.name_offset)
        if start < 0:
            raise UpkError("not chunked and the name table is not where the header says")
        body, _ = _dechunk(raw, start)
        return raw[:self.name_offset] + body

    def _looks_like_names(self, buf):
        try:
            names = self._read_names(buf)
            return names and names[0] == "None" or bool(names)
        except Exception:
            return False

    def _read_names(self, buf=None):
        buf = self.image if buf is None else buf
        o = self.name_offset
        names = []
        for _ in range(self.name_count):
            s, o = _fstr(buf, o)
            o += 8                      # uint64 name flags
            names.append(s)
        if buf is self.image and o != self.import_offset:
            raise UpkError("name table ends at %#x, imports start at %#x" % (o, self.import_offset))
        return names

    def _read_imports(self):
        rows = []
        o = self.import_offset
        for i in range(self.import_count):
            ints = struct.unpack_from("<7i", self.image, o + i * 28)
            rows.append({
                "class_package": self.names[ints[0]],
                "class_name": self.names[ints[2]],
                "outer": ints[4],
                "name": self.names[ints[5]],
            })
        return rows

    def _read_exports(self):
        rows = []
        o = self.export_offset
        for i in range(self.export_count):
            ints = struct.unpack_from("<11i", self.image, o + i * 72)
            rows.append({
                "class_index": ints[0],
                "super_index": ints[1],
                "outer_index": ints[2],
                "name": self.names[ints[3]],
                "size": ints[9],
                "offset": ints[10],
            })
        return rows

    # ---------------- objects ----------------

    def class_name(self, index):
        """Resolve a class reference: negative = imported class object, positive = class export."""
        if index < 0:
            i = -index - 1
            return self.imports[i]["name"] if i < len(self.imports) else None
        if index > 0 and index <= len(self.exports):
            return self.exports[index - 1]["name"]
        return None

    def object_name(self, index):
        if index == 0:
            return None
        if index > 0:
            return self.exports[index - 1]["name"] if index <= len(self.exports) else None
        i = -index - 1
        return self.imports[i]["name"] if i < len(self.imports) else None

    def object_path(self, index):
        """Human path for an object reference (export/import), following the outer chain."""
        if index == 0:
            return None
        if index > 0:
            if index > len(self.exports):
                return None
            e = self.exports[index - 1]
            outer = self.object_name(e["outer_index"])
            return e["name"] if not outer else "%s.%s" % (outer, e["name"])
        i = -index - 1
        if i >= len(self.imports):
            return None
        imp = self.imports[i]
        return "%s.%s" % (imp["class_package"], imp["name"]) if imp["class_package"] else imp["name"]

    def object_class(self, object_index):
        if object_index > 0:
            if object_index > len(self.exports):
                return None
            return self.class_name(self.exports[object_index - 1]["class_index"])
        if object_index < 0:
            i = -object_index - 1
            return self.imports[i]["class_name"] if i < len(self.imports) else None
        return None

    def data(self, index):
        e = self.exports[index - 1]
        return self.image[e["offset"]:e["offset"] + e["size"]]

    def find(self, name):
        for i, e in enumerate(self.exports, 1):
            if e["name"] == name:
                return i
        for i, e in enumerate(self.imports, 1):
            if e["name"] == name:
                return -i
        return None


# ---------------- property tags ----------------

def _decode_simple(t, payload):
    if t == 2:
        return struct.unpack("<i", payload)[0]
    if t == 3:
        return bool(struct.unpack("<i", payload)[0])
    if t == 4:
        return struct.unpack("<f", payload)[0]
    if t == 6:
        idx, num = struct.unpack("<ii", payload)
        return {"name_index": idx, "number": num}
    if t == 11:
        return [round(v, 6) for v in struct.unpack("<3f", payload)]
    if t == 12:
        return list(struct.unpack("<3i", payload))
    if t == 16:
        return struct.unpack("<i", payload)[0]
    if t == 17:
        return payload.hex()
    return payload.hex()


def walk_tags(pkg, data, start=0, depth=0, max_tags=4096, strict=False):
    """Walk a Batman property-tag stream. Returns (tags, end_offset, stop_reason)."""
    tags = []
    p = start
    while p + 4 <= len(data):
        t, off = struct.unpack_from("<hH", data, p)
        if t == 0:
            return tags, p, "end"
        if t in SIMPLE:
            if t == 13:                      # StrProperty: FString, variable length
                try:
                    text, nxt = _fstr(data, p + 4)
                except UpkError:
                    return tags, p, "bad_string"
                tags.append({"type": TYPE_NAMES[t], "type_id": t, "offset": off, "value": text,
                             "at": p + 8})
                p = nxt
                continue
            n = SIMPLE[t]
            if p + 4 + n > len(data):
                return tags, p, "overrun"
            if t == 6:                      # NameProperty: resolve the FName now, so the JSON is readable
                idx, num = struct.unpack_from("<ii", data, p + 4)
                value = pkg.names[idx] if 0 <= idx < len(pkg.names) else None
                tag = {"type": TYPE_NAMES[t], "type_id": t, "offset": off, "value": value,
                       "at": p + 4}
                if num:
                    tag["number"] = num
                tags.append(tag)
                p += 4 + n
                continue
            if t == 16:                     # object reference: resolve path/class inline as well
                idx = struct.unpack_from("<i", data, p + 4)[0]
                tag = {"type": TYPE_NAMES[t], "type_id": t, "offset": off, "value": idx,
                       "at": p + 4}
                if idx:
                    tag["ref"] = pkg.object_path(idx)
                    tag["ref_class"] = pkg.object_class(idx)
                tags.append(tag)
                p += 4 + n
                continue
            tag = {"type": TYPE_NAMES[t], "type_id": t, "offset": off,
                   "value": _decode_simple(t, data[p + 4:p + 4 + n]), "at": p + 4}
            if t == 3:
                # A BoolProperty payload is not a 0/1 bool: it is the whole 32-bit bitfield word
                # the class's consecutive bools are packed into.  Keep it, or every bool at one
                # offset looks identical and a shared word cannot be resolved to its members.
                tag["bits"] = struct.unpack_from("<I", data, p + 4)[0]
            tags.append(tag)
            p += 4 + n
        elif t in NAMED:
            if p + 20 > len(data):
                return tags, p, "overrun"
            ni, nn, size, arr = struct.unpack_from("<iiii", data, p + 4)
            if not (0 <= ni < len(pkg.names)) or size < 0 or p + 20 + size > len(data):
                return tags, p, "bad_tag"
            payload = data[p + 20:p + 20 + size]
            tag = {"type": TYPE_NAMES[t], "type_id": t, "offset": off,
                   "name": pkg.names[ni], "size": size, "array_index": arr,
                   "at": p + 20}
            tag.update(_decode_named(pkg, t, payload, depth))
            tags.append(tag)
            p += 20 + size
        else:
            return tags, p, "unknown_type_%d" % t
        if len(tags) >= max_tags:
            return tags, p, "max_tags"
    return tags, p, "eof"


def _decode_named(pkg, t, payload, depth):
    """Best-effort decode of a named property's payload; never raises."""
    if t == 16:
        return {"value": struct.unpack("<i", payload)[0] if len(payload) >= 4 else None}
    if t == 5:
        ref = struct.unpack("<i", payload)[0] if len(payload) >= 4 else None
        return {"value": ref, "ref": pkg.object_path(ref) if ref else None}
    if t == 8:
        ref = struct.unpack("<i", payload)[0] if len(payload) >= 4 else None
        return {"value": ref, "ref": pkg.object_path(ref) if ref else None}
    if t == 13:
        try:
            return {"value": _fstr(payload, 0)[0]}
        except UpkError:
            return {"raw": payload[:64].hex()}
    if t == 10:
        if depth < 6 and len(payload) >= 4:
            nested, end, why = walk_tags(pkg, payload, 0, depth + 1, strict=True)
            if nested and (why == "end" or end >= len(payload) - 8):
                return {"props": nested, "nested": len(nested)}
        return {"raw": payload[:128].hex(), "floats": _floats(payload)}
    if t == 9:
        return _decode_array(pkg, payload, depth)
    if t == 1:
        # A ByteProperty with an enum serialises its value as an FName (8 bytes); without one it is a
        # single byte. The FName is the enum entry, so resolve it like a name or the value is just the
        # low byte of a name index (e.g. Type 134 instead of VEHLT_HeadLight).
        if len(payload) >= 8:
            idx, num = struct.unpack_from("<ii", payload)
            if 0 <= idx < len(pkg.names):
                return {"value": pkg.names[idx], "enum_index": idx}
        return {"value": payload[0] if payload else None}
    if t == 7:
        try:
            return {"value": _fstr(payload, 0)[0]}
        except UpkError:
            return {"raw": payload[:64].hex()}
    return {"raw": payload[:64].hex()}


def _floats(payload, limit=8):
    out = []
    for i in range(0, min(len(payload) - 3, limit * 4), 4):
        v = struct.unpack_from("<f", payload, i)[0]
        if v != v or abs(v) > 1e12:
            return out
        out.append(round(v, 5))
    return out


def _decode_array(pkg, payload, depth):
    if len(payload) < 4:
        return {"count": 0, "items": []}
    count = struct.unpack_from("<i", payload, 0)[0]
    body = payload[4:]
    if count < 0 or count > 100000:
        return {"count": count, "raw": payload[:64].hex()}
    if count == 0:
        return {"count": 0, "items": []}
    if count <= 4096 and len(body) >= 4 and 0 < struct.unpack_from("<i", body, 0)[0] <= 512:
        # arrays of FString: variable-length elements, count already consumed
        try:
            o, strings = 0, []
            for _ in range(count):
                s, o = _fstr(body, o)
                strings.append(s)
            if o == len(body):
                return {"count": count, "strings": strings}
        except UpkError:
            pass
    if len(body) % count == 0:
        stride = len(body) // count
        if stride == 4:
            ints = list(struct.unpack("<%di" % count, body)) if count <= 4096 else []
            if ints and any(ints) and all(v == 0 or pkg.object_class(v) for v in ints):
                return {"count": count, "stride": 4,
                        "refs": [{"index": v, "path": pkg.object_path(v),
                                  "class": pkg.object_class(v)} for v in ints]}
            fvals = list(struct.unpack("<%df" % count, body)) if count <= 4096 else []
            return {"count": count, "stride": 4, "floats": [round(v, 5) for v in fvals]}
        if stride == 8:
            vals = struct.unpack("<%di" % (count * 2), body) if count <= 4096 else ()
            return {"count": count, "stride": 8, "ints": list(vals)}
        if stride == 12:
            vals = struct.unpack("<%df" % (count * 3), body) if count <= 4096 else ()
            return {"count": count, "stride": 12, "vec3": [round(v, 5) for v in vals]}
        if depth < 5 and count <= 512:
            # arrays of tagged structs: material parameter values, curve points, bounds
            items, ok = [], True
            for i in range(count):
                chunk = body[i * stride:(i + 1) * stride]
                tags, end, why = walk_tags(pkg, chunk, 0, depth + 1, max_tags=64)
                if tags and end <= len(chunk):
                    items.append(tags)
                else:
                    items.append({"raw": chunk[:32].hex()})
                    ok = False
            if ok:
                return {"count": count, "stride": stride, "items": items}
            return {"count": count, "stride": stride, "raw": body[:96].hex()}
    return {"count": count, "raw": payload[:96].hex()}


def best_walk(pkg, data, max_tags=20000):
    """Batman objects do not all start their tag list at byte 0. The vehicle and weapon archetypes
    carry a 1-byte prefix (their streams parse to the last byte from offset 1, and only from there),
    while sims/wheels start at 0. Try the observed starts and keep the walk that consumes the most
    of the object with the most tags; ties go to the earlier start."""
    best = None
    limit = min(len(data), 65536)
    for start in (0, 1, 2, 4):
        tags, end, why = walk_tags(pkg, data, start, max_tags=max_tags)
        score = (end >= limit - 4, len(tags))
        if best is None or score > best[0]:
            best = (score, tags, end, why)
    return best[1], best[2], best[3]


def export_summary(pkg, index, max_tags=20000):
    e = pkg.exports[index - 1]
    data = pkg.data(index)
    tags, end, why = best_walk(pkg, data, max_tags=max_tags)
    return {
        "index": index,
        "name": e["name"],
        "class": pkg.object_class(index),
        "outer": pkg.object_path(e["outer_index"]),
        "size": e["size"],
        "tags": tags,
        "tag_count": len(tags),
        "parsed_bytes": end,
        "stop": why,
    }


def census(pkg):
    from collections import Counter
    counts = Counter(pkg.object_class(i) for i in range(1, pkg.export_count + 1))
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("--dump", help="object name to dump")
    ap.add_argument("--json", help="write the census + dumped object to this file")
    a = ap.parse_args()
    pkg = Package(a.package)
    print("package   ", os.path.basename(a.package))
    print("version   ", pkg.version, "licensee", pkg.licensee)
    print("counts    ", pkg.name_count, "names /", pkg.import_count,
          "imports /", pkg.export_count, "exports")
    print("image     ", len(pkg.image), "bytes")
    print("classes   ", json.dumps(census(pkg))[:400])
    out = {"package": a.package, "version": pkg.version, "licensee": pkg.licensee,
           "names": pkg.name_count, "imports": pkg.import_count, "exports": pkg.export_count,
           "classes": census(pkg)}
    if a.dump:
        idx = pkg.find(a.dump)
        if not idx:
            raise SystemExit("no object named %r" % a.dump)
        if idx < 0:
            raise SystemExit("%r is an import: %s" % (a.dump, pkg.object_path(idx)))
        s = export_summary(pkg, idx)
        out["dump"] = s
        print("\n--- %s (%s) %d bytes ---" % (s["name"], s["class"], s["size"]))
        for t in s["tags"][:60]:
            if "name" in t:
                print("  %-28s %-16s @%#06x size=%-5d %s" % (
                    t["name"], t["type"], t["offset"], t["size"],
                    _short(t)))
            else:
                print("  %-28s %-16s @%#06x %s" % ("(offset-only)", t["type"], t["offset"],
                                                   _short(t)))
        print("  tags: %d, bytes: %d/%d, stop: %s" % (s["tag_count"], s["parsed_bytes"],
                                                      s["size"], s["stop"]))
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), indent=1)


def _short(tag):
    if "props" in tag:
        return "{%d props}" % tag["nested"]
    if "ref" in tag:
        return "-> %s" % tag["ref"]
    if "items" in tag:
        return "%d items" % tag["count"]
    if "floats" in tag and tag.get("count", 0):
        return "floats %s" % tag["floats"][:6]
    if "value" in tag:
        return repr(tag["value"])
    if "raw" in tag:
        return "raw " + tag["raw"][:32]
    return ""


if __name__ == "__main__":
    sys.exit(main())
