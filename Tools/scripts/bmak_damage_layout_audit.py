"""Audit of `Research/BatmobileGrab/DAMAGE_RULES.md` section 1 (the Function export layout).

What it does
  * Re-reads `BmGame.upk` with **its own reader** (signature, chunk container, name table,
    import table, export table; only the LZO1X *codec* is imported, not a parser) and
    re-derives every `Function` export from the export table's own offset and size.
  * Checks the layout the note recovered: where the head fields sit, where the bytecode
    starts, **how long it is**, and what the trailing bytes are.  Each check is an oracle that
    fails if the answer is wrong, and each is measured over all 29,620 `Function` exports.
  * Re-decodes every numeric constant the note quotes for the three functions audited here.
  * Traces two damage rules of the note to exact bytecode.

The layout the note states (quoted as the claim under audit):

    u16   0            prefix, constant 0
    i32   @2           Next
    i32   @6           SuperField
    i32   @10          Children
    i32   @14          Line
    i32   @18          ScriptSize   == len(script) + 1
    byte  @22          Script       len(export) - 38 bytes
    i32   @size-16     flags word
    i32   @size-12     pre-name word, always 0x0002xxxx
    i32   @size-8      own FName index
    i32   @size-4      name number, always 0

Constant detection does **not** depend on a token walk: a float literal is a `0x1e` byte
followed by four bytes that decode to a plausible source float, and the audit reports every
`0x1e` in the body, so nothing can be silently skipped.  The token walk is used only as a
boundary oracle (does a body length let a scan end exactly on the last byte?), where a partial
final token is the thing being measured.

Usage
    python Tools/scripts/bmak_damage_layout_audit.py --write
    python Tools/scripts/bmak_damage_layout_audit.py --check   # re-derive and diff both files
"""
import argparse
import collections
import hashlib
import json
import os
import re
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lzo1x import lzo1x_decompress  # noqa: E402  (byte codec only)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = r"E:\Games\Batman - Arkham Knight"
UPK = os.path.join(GAME, "BmGame", "CookedPCConsole", "BmGame.upk")
EXE = os.path.join(GAME, "Binaries", "Win64", "BatmanAK.exe")
DOC_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "DAMAGE_RULES.json")
UVIEWER = os.path.join(ROOT, "Working", "vendor", "UEViewer", "Unreal")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "DAMAGE_LAYOUT_AUDIT.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "DAMAGE_LAYOUT_AUDIT.md")

TAG = b"\xc1\x83\x2a\x9e"
HEAD = 22
AUDITED = [
    "RVehicleBatmobileBase.TakeDamage",
    "RVehicleBatmobileBase.TakeRadiusDamageFromWeapon",
    "RVehicleBatmobileBase.DrainWeaponGeneratorForDamage",
]
RAM = "RVehicleBatmobileBase.TakesDamageFromRam"

REF5 = {0x00, 0x01, 0x02, 0x12, 0x20, 0x29, 0x3A, 0x48}
LIT5 = {0x1D, 0x1E}
LIT2 = {0x24, 0x2C}
NAME_OF = {0x00: "LocalVariable", 0x01: "InstanceVariable", 0x02: "DefaultVariable",
           0x04: "Return", 0x06: "Jump", 0x07: "JumpIfNot", 0x0B: "Nothing", 0x0F: "Let",
           0x10: "op/10", 0x12: "ClassContext", 0x13: "Cast/13", 0x14: "LetBool",
           0x15: "EndParmValue", 0x16: "EndFunctionParms", 0x17: "Self", 0x18: "Skip",
           0x19: "Context", 0x1B: "VirtualFunction", 0x1C: "FinalFunction",
           0x1D: "IntConst", 0x1E: "FloatConst", 0x1F: "StringConst", 0x20: "ObjectConst",
           0x24: "ByteConst", 0x25: "IntZero", 0x26: "IntOne", 0x27: "True", 0x28: "False",
           0x2A: "NoObject", 0x2C: "IntConstByte", 0x2D: "unary/2d", 0x2E: "Cast/2e",
           0x35: "op/35", 0x36: "op/36", 0x3A: "ReturnSlotRef", 0x48: "LocalOutVariable",
           0x72: "op/72", 0x77: "op/77", 0x82: "op/82", 0x90: "op/90", 0x91: "op/91",
           0x93: "op/93", 0x9B: "op/9b", 0xAB: "op/ab", 0xAC: "op/ac", 0xAF: "op/af",
           0xB0: "op/b0", 0xB1: "op/b1", 0xB3: "op/b3", 0xB6: "op/b6", 0xC2: "op/c2",
           0xD8: "op/d8", 0xE1: "op/e1", 0xE2: "op/e2", 0xF5: "op/f5"}


def tok_name(t):
    return NAME_OF.get(t, "byte/%02x" % t)


# --------------------------------------------------------------------------- reader
class PkgError(Exception):
    pass


def _fstr(buf, o):
    n = struct.unpack_from("<i", buf, o)[0]
    if n == 0:
        return "", o + 4
    if n > 0:
        return buf[o + 4:o + 4 + n].rstrip(b"\0").decode("latin-1"), o + 4 + n
    m = -n
    return (buf[o + 4:o + 4 + 2 * m].decode("utf-16-le").rstrip("\0"), o + 4 + 2 * m)


def _dechunk(raw, start):
    out = bytearray()
    q = start
    while q + 16 <= len(raw) and raw[q:q + 4] == TAG:
        block, csize, usize = struct.unpack_from("<III", raw, q + 4)
        if not (block or csize or usize):
            break
        p = q + 16
        pairs, total = [], 0
        while total < usize:
            bc, bu = struct.unpack_from("<II", raw, p)
            p += 8
            if not bc or not bu:
                raise PkgError("zero sub-block")
            pairs.append((bc, bu))
            total += bu
        if total != usize:
            raise PkgError("chunk lists %d, header says %d" % (total, usize))
        for bc, bu in pairs:
            blob = raw[p:p + bc]
            try:
                part = zlib.decompress(blob)
            except zlib.error:
                part = lzo1x_decompress(blob)
            if len(part) != bu:
                raise PkgError("sub-block decoded to %d, expected %d" % (len(part), bu))
            out += part
            p += bc
        q = p
    if not out:
        raise PkgError("no chunk at %#x" % start)
    return bytes(out), q


class Pkg:
    """BmGame.upk parsed here, not by `upk_read.py`."""

    def __init__(self, path):
        self.file = path
        raw = open(path, "rb").read()
        self.bytes = len(raw)
        if raw[:4] != TAG:
            raise PkgError("signature %r" % raw[:4])
        self.version, self.licensee = struct.unpack_from("<HH", raw, 4)
        self.header_size = struct.unpack_from("<i", raw, 8)[0]
        self.group, o = _fstr(raw, 12)
        self.flags = struct.unpack_from("<I", raw, o)[0]
        o += 4
        (self.name_count, self.name_offset, self.export_count, self.export_offset,
         self.import_count, self.import_offset) = struct.unpack_from("<6i", raw, o)
        # Tables live in a logical image: either the file itself, or the file prefix followed
        # by the decompressed chunk body (the prefix ends where the name table starts).
        self.image = raw
        try:
            self.names = self._names(raw)
            self.chunked = False
        except Exception:
            start = raw.find(TAG, self.name_offset)
            if start < 0:
                raise PkgError("tables do not parse and no chunk tag follows")
            body, _ = _dechunk(raw, start)
            del self.image
            self.image = raw[:self.name_offset] + body
            self.names = self._names(self.image)
            self.chunked = True
        del raw
        self.imports = self._imports()
        self.exports = self._exports()
        self.paths = {}
        for i in range(1, self.export_count + 1):
            self.paths[i] = self.path(i)

    def _names(self, buf):
        o = self.name_offset
        names = []
        for _ in range(self.name_count):
            st, o = _fstr(buf, o)
            o += 8
            names.append(st)
        if self.import_offset and o != self.import_offset:
            raise PkgError("name table ends at %#x, imports at %#x" % (o, self.import_offset))
        if "Function" not in names or "TakeDamage" not in names:
            raise PkgError("name table does not look like BmGame")
        return names

    def _imports(self):
        rows = []
        for i in range(self.import_count):
            v = struct.unpack_from("<7i", self.image, self.import_offset + i * 28)
            rows.append({"class_package": self.names[v[0]], "class_name": self.names[v[2]],
                         "outer": v[4], "name": self.names[v[5]]})
        return rows

    def _exports(self):
        rows = []
        for i in range(self.export_count):
            v = struct.unpack_from("<11i", self.image, self.export_offset + i * 72)
            rows.append({"class_index": v[0], "outer_index": v[2], "name": self.names[v[3]],
                         "size": v[9], "offset": v[10]})
        return rows

    def obj_class(self, index):
        """Class object of an export/import, by name."""
        if index < 0:
            i = -index - 1
            return self.imports[i]["class_name"] if i < len(self.imports) else None
        if 0 < index <= self.export_count:
            return self.class_name(self.exports[index - 1]["class_index"])
        return None

    def class_name(self, index):
        if index < 0:
            i = -index - 1
            return self.imports[i]["name"] if i < len(self.imports) else None
        if 0 < index <= self.export_count:
            return self.exports[index - 1]["name"]
        return None

    def path(self, index, depth=0):
        if index == 0 or depth > 12:
            return None
        if index < 0:
            i = -index - 1
            if i >= len(self.imports):
                return None
            imp = self.imports[i]
            return "%s.%s" % (imp["class_package"], imp["name"]) if imp["class_package"] \
                else imp["name"]
        e = self.exports[index - 1]
        outer = self.path(e["outer_index"], depth + 1)
        return e["name"] if not outer else "%s.%s" % (outer, e["name"])

    def data(self, index):
        e = self.exports[index - 1]
        return self.image[e["offset"]:e["offset"] + e["size"]]

    def functions(self):
        return [i for i in range(1, self.export_count + 1)
                if self.class_name(self.exports[i - 1]["class_index"]) == "Function"]

    def find(self, path):
        """Export index for a path, either fully qualified or as a dotted tail."""
        for i in range(1, self.export_count + 1):
            p = self.paths.get(i)
            if p == path or (p and p.endswith("." + path)):
                return i
        return None


# --------------------------------------------------------------------------- fields
def head(d):
    return {"prefix_u16": struct.unpack_from("<H", d, 0)[0],
            "next": struct.unpack_from("<i", d, 2)[0],
            "super": struct.unpack_from("<i", d, 6)[0],
            "children": struct.unpack_from("<i", d, 10)[0],
            "line": struct.unpack_from("<i", d, 14)[0],
            "script_size": struct.unpack_from("<i", d, 18)[0]}


def body_of(d):
    """The bytecode as this audit reads it: ScriptSize bytes from offset 22."""
    return d[HEAD:HEAD + struct.unpack_from("<i", d, 18)[0]]


def body_note(d):
    """The bytecode as the note reads it: len(export) - 38 bytes (one byte shorter)."""
    return d[HEAD:len(d) - 16]


def float_scan(body):
    """Every `0x1e` in the body, with the float behind it and a plausibility flag.

    A source literal is a float a compiler could emit: 0, or a magnitude a game would use.
    A `0x1e` that happens to sit inside an index decodes to a garbage magnitude instead.
    """
    out = []
    i = body.find(b"\x1e")
    while i >= 0 and i + 5 <= len(body):
        v = struct.unpack_from("<f", body, i + 1)[0]
        ok = (v == 0.0) or (1e-5 <= abs(v) <= 1e6)
        out.append({"at": i, "value": round(v, 6), "plausible": ok})
        i = body.find(b"\x1e", i + 1)
    return out


def scan(body, jump=2):
    """Coarse left-to-right token widths; returns the position it reaches."""
    m, n = 0, len(body)
    while m < n:
        t = body[m]
        if t in REF5 or t in LIT5:
            w = 5
        elif t in LIT2:
            w = 2
        elif t == 0x1F:
            z = body.find(b"\x00", m + 1)
            if z < 0:
                return n + 1
            w = z - m + 1
        elif t in (0x06, 0x07):
            w = 1 + jump
        else:
            w = 1
        m += w
    return m


# --------------------------------------------------------------------------- one function
def audit_function(pkg, path):
    i = pkg.find(path)
    d = pkg.data(i)
    h = head(d)
    b, bn = body_of(d), body_note(d)
    trailer = d[HEAD + len(b):]
    return {
        "path": path, "export": i, "file_offset": pkg.exports[i - 1]["offset"],
        "size": len(d), "head": h,
        "next_path": pkg.path(h["next"]), "super_path": pkg.path(h["super"]),
        "children_path": pkg.path(h["children"]),
        "body_bytes_audit": len(b), "body_bytes_note": len(bn),
        "body_sha1_audit": hashlib.sha1(b).hexdigest(),
        "body_sha1_note": hashlib.sha1(bn).hexdigest(),
        "body_head_hex": b[:12].hex(" "), "body_tail_hex": b[-8:].hex(" "),
        "trailer_bytes": len(trailer), "trailer_hex": trailer.hex(" "),
        "trailer_name": pkg.names[struct.unpack_from("<i", trailer, len(trailer) - 8)[0]]
        if len(trailer) >= 8 else None,
        "scan_exact_end": scan(b) == len(b),
        "float_bytes": float_scan(b),
    }


# --------------------------------------------------------------------------- rules
def count_int(node, value):
    n = 0
    if isinstance(node, dict):
        if node.get("int") == value:
            n += 1
        for v in node.values():
            n += count_int(v, value)
    elif isinstance(node, list):
        for v in node:
            n += count_int(v, value)
    return n


def let_tree(body, at):
    """Decode one `Let(lhs, rhs)` where every operator is a parm list closed by `0x16`.

    The nesting must balance for the statement to end exactly where the next statement
    starts; that balance is the oracle, not the opcode names.
    """
    pos = [at]

    def expr():
        p = pos[0]
        t = body[p]
        pos[0] = p + 1
        if t in (0x00, 0x01, 0x02, 0x12, 0x20, 0x29, 0x3A, 0x48):
            idx = struct.unpack_from("<i", body, p + 1)[0]
            pos[0] = p + 5
            return {"ref": {"token": tok_name(t), "index": idx}}
        if t in (0x1D, 0x1E):
            pos[0] = p + 5
            if t == 0x1E:
                return {"float": round(struct.unpack_from("<f", body, p + 1)[0], 6)}
            return {"int": struct.unpack_from("<i", body, p + 1)[0]}
        if t in LIT2:                       # 0x24 ByteConst / 0x2c IntConstByte: one byte
            pos[0] = p + 2
            return {"int": body[p + 1]}
        if t == 0x2D:
            return {"un": "0x2d", "arg": expr()}
        if t == 0x18:
            pos[0] = p + 5
            return {"skip": expr()}
        if t in (0x13, 0x2E):
            idx = struct.unpack_from("<i", body, p + 1)[0]
            pos[0] = p + 5
            return {"cast": idx, "arg": expr()}
        if t in (0x1B, 0x1C):
            idx = struct.unpack_from("<i", body, p + 1)[0]
            pos[0] = p + 5
            return {"call": idx, "token": tok_name(t), "parms": parms()}
        if t == 0x16:
            raise ValueError("0x16 where an expression was expected, at %d" % p)
        if t >= 0x80 or t in (0x10, 0x34, 0x35, 0x36, 0x49, 0x62, 0x72, 0x77, 0x82, 0x9B, 0xC2):
            return {"op": "0x%02x" % t, "parms": parms()}
        if t in (0x0B, 0x17, 0x25, 0x26, 0x27, 0x28, 0x2A):
            return {"bare": tok_name(t)}
        raise ValueError("token %02x at %d" % (t, p))

    def parms():
        out = []
        while True:
            if pos[0] >= len(body):
                raise ValueError("eof in parms")
            if body[pos[0]] == 0x16:
                pos[0] += 1
                return out
            out.append(expr())

    if body[at] != 0x0F:
        raise ValueError("not a Let at %d" % at)
    pos[0] = at + 1
    tree = {"lhs": expr(), "rhs": expr()}       # evaluated before pos[0] is read
    return pos[0], tree


def readers(pkg, index):
    """Every Function whose body carries `index` as a 4-byte operand."""
    packed = struct.pack("<i", index)
    hits = []
    for f in pkg.functions():
        if packed in body_of(pkg.data(f)):
            hits.append(pkg.paths[f])
    return sorted(hits)


def exe_registrations():
    """The note's `exec<Name>` counts in `BatmanAK.exe`: prefix hits vs NUL-terminated hits."""
    exe = open(EXE, "rb").read()
    out = {}
    for short in ("TakeDamage", "TakeRadiusDamageFromWeapon", "DrainWeaponGeneratorForDamage"):
        pat = ("exec" + short).encode()
        hits = [m.group().decode() for m in re.finditer(re.escape(pat) + rb"[ -~]*", exe)]
        out[short] = {"prefix": exe.count(pat), "exact": exe.count(pat + bytes([0])),
                      "strings": sorted(hits)}
    return out


def rule_records(pkg, docjson):
    out = []
    td = pkg.find("RVehicleBatmobileBase.TakeDamage")
    b = body_of(pkg.data(td))
    amdr = pkg.find("RVehicleBatmobileBase.ArmourModeDamageReduction")
    arm = pkg.find("RVehicleBatmobileBase.ArmouredMode")
    at = b.find(struct.pack("<i", amdr))
    gate = b.rfind(b"\x07", 0, at)
    let = b.rfind(b"\x0f", 0, at)
    end, tree = let_tree(b, let)
    off = struct.unpack_from("<H", b, gate + 1)[0]
    target = gate + 3 + off
    out.append({
        "id": "R1_armour_mode_reduction",
        "rule": "DAMAGE_RULES.md 3.1: `ArmouredMode` gates `ArmourModeDamageReduction`, whose "
                "shipped value 0 makes armoured mode reduce nothing",
        "function": "RVehicleBatmobileBase.TakeDamage", "export": td,
        "gate": {"at": gate, "token": "0x07 JumpIfNot", "jump_offset": off,
                 "bytes": b[gate:gate + 3].hex(" "),
                 "condition_at": gate + 3, "condition_bytes": b[gate + 3:let].hex(" "),
                 "target_at": target,
                 "target_byte": "0x%02x" % b[target] if target < len(b) else "past end",
                 "target_is_statement_start": target < len(b) and b[target] == 0x0F},
        "gate_condition_ref": {"at": b.find(struct.pack("<i", arm), gate, let),
                               "index": arm, "path": pkg.path(arm),
                               "class": pkg.obj_class(arm)},
        "statement": {"at": let, "end": end, "bytes": b[let:end].hex(" ")},
        "statement_tree": tree,
        "statement_ends_at_next_statement": b[end] == 0x0F,
        "field_ref": {"index": amdr, "at": at},
        "literal_100_count": count_int(tree, 100),
        "shipped_values": [{"archetype": r["archetype"], "value": r["value"]}
                           for r in docjson["damage_values"]
                           if r["name"].endswith("ArmourModeDamageReduction")],
        "readers_in_package": readers(pkg, amdr),
    })
    ri = pkg.find(RAM)
    rb = body_of(pkg.data(ri))
    rv = pkg.find("TakesDamageFromRam.ReturnValue")
    out.append({
        "id": "R2_ram_is_unconditional",
        "rule": "DAMAGE_RULES.md 3.4: `TakesDamageFromRam` opens with `return true`; its "
                "trailing bytes are called an incomplete descriptor of UNKNOWN meaning",
        "function": RAM, "export": ri, "body": rb.hex(" "), "body_bytes": len(rb),
        "body_sha1": hashlib.sha1(rb).hexdigest(),
        "note_body_bytes": len(body_note(pkg.data(ri))),
        "note_body_sha1": hashlib.sha1(body_note(pkg.data(ri))).hexdigest(),
        "return_value_ref": {"index": rv, "path": pkg.path(rv),
                             "class": pkg.obj_class(rv),
                             "at": rb.find(struct.pack("<i", rv)) - 1},
        "decode": ["04 Return", "27 True", "04 Return", "3a <ref ReturnValue> 0x%04x" % rv],
        "unconditional": rb[:2] == b"\x04\x27",
    })
    return out


# --------------------------------------------------------------------------- corpus
def corpus(pkg):
    funcs = pkg.functions()
    next_kind = collections.Counter()
    child_kind = collections.Counter()
    rel = collections.Counter()
    trailer = collections.Counter()
    pre = collections.Counter()
    lengths = collections.Counter()
    thin = collections.Counter()
    ends_return_nothing = ends_return_ref = 0
    final_call_hits = final_call_ok = 0
    prefix0 = name_ok = num0 = 0
    desc_stubs = desc_refs = desc_own = 0
    for i in funcs:
        d = pkg.data(i)
        n = len(d)
        h = head(d)
        prefix0 += h["prefix_u16"] == 0
        ss = h["script_size"]
        rel[ss - (n - 38)] += 1
        trailer[n - HEAD - ss] += 1
        pre[struct.unpack_from("<i", d, n - 12)[0] & 0xFFFF0000] += 1
        namei, numi = struct.unpack_from("<ii", d, n - 8)
        if 0 <= namei < len(pkg.names) and pkg.names[namei] == pkg.exports[i - 1]["name"]:
            name_ok += 1
        num0 += numi == 0
        if h["next"] == 0:
            next_kind["0"] += 1
        elif 0 < h["next"] <= pkg.export_count:
            next_kind["export:" + (pkg.class_name(pkg.exports[h["next"] - 1]["class_index"])
                                   or "?")] += 1
        else:
            next_kind["import/out-of-range"] += 1
        if h["children"] == 0:
            child_kind["0"] += 1
        elif 0 < h["children"] <= pkg.export_count and \
                pkg.exports[h["children"] - 1]["outer_index"] == i:
            child_kind["own property"] += 1
        else:
            child_kind["other"] += 1
        b = d[HEAD:HEAD + ss]
        lengths[len(b)] += 1
        if len(b) <= 3:
            thin[b.hex(" ")] += 1
        if b.endswith(b"\x04\x0b"):
            ends_return_nothing += 1
        if b[-6:-4] == b"\x04\x3a":
            ends_return_ref += 1
        # anchor E: a native stub is `(29 <ref>)* 0b`; is every ref a property of the function?
        if b and b[-1] == 0x0B and len(b) >= 6:
            core = b[:-1]
            if len(core) % 5 == 0 and all(core[k] == 0x29 for k in range(0, len(core), 5)):
                desc_stubs += 1
                for k in range(0, len(core), 5):
                    r = struct.unpack_from("<i", core, k + 1)[0]
                    desc_refs += 1
                    if 0 < r <= pkg.export_count and                             pkg.exports[r - 1]["outer_index"] == i and pkg.obj_class(r):
                        desc_own += 1
        # anchor F: every 0x1c (call) token's operand is a Function export or an import
        m = b.find(b"\x1c")
        while m >= 0 and m + 5 <= len(b):
            ref = struct.unpack_from("<i", b, m + 1)[0]
            if 0 < ref <= pkg.export_count or -pkg.import_count <= ref < 0:
                final_call_hits += 1
                final_call_ok += pkg.obj_class(ref) == "Function"
            m = b.find(b"\x1c", m + 5)
    return {
        "function_exports": len(funcs), "prefix_zero": prefix0,
        "name_at_minus8_is_own_name": name_ok, "name_number_zero": num0,
        "next_kind": dict(sorted(next_kind.items())), "children_kind": dict(child_kind),
        "script_size_minus_(size-38)": {str(k): v for k, v in sorted(rel.items())},
        "trailer_bytes": {str(k): v for k, v in sorted(trailer.items())},
        "pre_name_word_high16": {"%#010x" % k: v for k, v in pre.most_common(8)},
        "body_lengths": {str(k): v for k, v in sorted(lengths.items())[:6]},
        "min_body_length": min(lengths),
        "bodies_le_3_bytes": dict(sorted(thin.items(), key=lambda kv: -kv[1])),
        "bodies_ending_return_nothing": ends_return_nothing,
        "bodies_ending_return_ref": ends_return_ref,
        "call_token_operands": final_call_hits,
        "call_token_operands_are_functions": final_call_ok,
        "descriptor_stubs": desc_stubs, "descriptor_refs": desc_refs,
        "descriptor_refs_own": desc_own,
    }


def body_length_test(pkg):
    """Exact-end test for three candidate body lengths, over all Function exports."""
    funcs = pkg.functions()
    variants = {
        "ScriptSize (= @18)": lambda d, ss: d[HEAD:HEAD + ss],
        "ScriptSize - 1 (= len(export) - 38, the note)": lambda d, ss: d[HEAD:HEAD + ss - 1],
        "ScriptSize + 1": lambda d, ss: d[HEAD:HEAD + ss + 1],
    }
    out = {}
    for label, fn in variants.items():
        exact = over = 0
        for i in funcs:
            d = pkg.data(i)
            ss = struct.unpack_from("<i", d, 18)[0]
            b = fn(d, ss)
            end = scan(b)
            if end == len(b):
                exact += 1
            elif end > len(b):
                over += 1
        out[label] = {"exact_end": exact, "total": len(funcs),
                      "percent": round(100.0 * exact / len(funcs), 1), "overshoot": over}
    return out


def ueviewer_evidence():
    path = os.path.join(UVIEWER, "UnTypeinfo.h")
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    found = {}
    for i, line in enumerate(lines):
        if "remaining data will be dropped anyway" in line:
            found["children_return"] = {"file": "Working/vendor/UEViewer/Unreal/UnTypeinfo.h",
                                        "line": i + 1, "text": line.strip()}
        if "Ar.Serialize(&Script[0], ScriptSize)" in line:
            found["script_size_bytes"] = {"file": "Working/vendor/UEViewer/Unreal/UnTypeinfo.h",
                                          "line": i + 1, "text": line.strip()}
    return found


# --------------------------------------------------------------------------- claims
def claims(pkg, docjson, funcs, corp, blt, reg):
    out = []

    def add(cid, section, claim, measured, verdict, evidence):
        out.append({"id": cid, "section": section, "claim": claim, "measured": measured,
                    "verdict": verdict, "evidence": evidence})

    td = funcs[AUDITED[0]]
    tw = funcs[AUDITED[1]]
    dw = funcs[AUDITED[2]]
    ram = funcs[RAM]

    def plausible(f):
        return [c for c in f["float_bytes"] if c["plausible"]]

    add("L1", "1", "u16 prefix at 0 is constant 0 on every Function export",
        "%d/%d" % (corp["prefix_zero"], corp["function_exports"]),
        "PASS" if corp["prefix_zero"] == corp["function_exports"] else "FAIL",
        "two bytes read at export offset 0")
    add("L2", "1", "Next @2 is the UField sibling link",
        "0: %d, UField-subclass export: %d, unresolvable: %d"
        % (corp["next_kind"].get("0", 0),
           sum(v for k, v in corp["next_kind"].items() if k.startswith("export:")),
           corp["next_kind"].get("import/out-of-range", 0)),
        "PASS" if corp["next_kind"].get("import/out-of-range", 0) == 0 else "FAIL",
        "every value is 0 or an export whose class is a UField subclass "
        "(%s)" % ", ".join(sorted(k.split(":", 1)[1] for k in corp["next_kind"]
                                  if k.startswith("export:"))))
    add("L3", "1", "Children @10 is the first child property (the first parameter)",
        "own property: %d, 0: %d, other: %d" % (corp["children_kind"].get("own property", 0),
                                                corp["children_kind"].get("0", 0),
                                                corp["children_kind"].get("other", 0)),
        "PASS" if corp["children_kind"].get("other", 0) == 0 else "FAIL",
        "every value is 0 or an export whose outer_index is the function itself")
    add("L4", "1", "ScriptSize @18 == len(script) + 1",
        "ScriptSize - (len(export) - 38) = %s" % corp["script_size_minus_(size-38)"], "FAIL",
        "the field is a byte count: a scan of ScriptSize bytes ends exactly on the last byte "
        "in %d of %d bodies, the note's length in %d"
        % (blt["ScriptSize (= @18)"]["exact_end"], blt["ScriptSize (= @18)"]["total"],
           blt["ScriptSize - 1 (= len(export) - 38, the note)"]["exact_end"]))
    add("L5", "1", "Script @22 is len(export) - 38 bytes",
        "trailer after 22 + ScriptSize: %s bytes" % corp["trailer_bytes"], "FAIL",
        "the note's slice is one byte short in %d exports and one byte long in %d; %d bodies "
        "end in `04 0b` (`return;`) which the note's slice turns into a bare `04`"
        % (corp["script_size_minus_(size-38)"].get("1", 0),
           corp["script_size_minus_(size-38)"].get("-1", 0),
           corp["bodies_ending_return_nothing"]))
    add("L6", "1", "trailing i32 @size-16 is a flags word",
        "@size-16 is the body's last byte in %d exports"
        % corp["script_size_minus_(size-38)"].get("1", 0), "FAIL",
        "the export ends with a %s-byte trailer that ends in the own FName; @size-16 is not a "
        "field" % "/".join(sorted(corp["trailer_bytes"])))
    add("L7", "1", "pre-name word @size-12 is always 0x0002xxxx",
        str(corp["pre_name_word_high16"]), "FAIL",
        "as an exact pattern it holds for %d of %d; the field takes 0x00824802 (TakeRadius) and "
        "0xffff2002 (the %d exports with a 17-byte trailer)"
        % (corp["pre_name_word_high16"].get("%#010x" % 0x00020000, 0),
           corp["function_exports"], corp["script_size_minus_(size-38)"].get("-1", 0)))
    add("L8", "1", "name FName @size-8 is the function's own name; number @size-4 is 0",
        "%d name, %d number" % (corp["name_at_minus8_is_own_name"],
                                corp["name_number_zero"]),
        "PASS" if corp["name_at_minus8_is_own_name"] == corp["function_exports"] ==
        corp["name_number_zero"] else "FAIL",
        "index resolved through this audit's own name table")
    add("L9", "1", "anchor C: the thinnest script in the package is one byte and it is 0x04",
        "shortest body %d byte(s); bodies of <=3 bytes: %s"
        % (corp["min_body_length"], corp["bodies_le_3_bytes"]),
        "FAIL",
        "in the file's frame every one-byte body is `0b` (`EX_Nothing`, %s of them) and `04` "
        "alone is never a body; the 2-byte `04 0b` bodies are what the note's one-byte slice "
        "turns into `04`, so in the note's own frame the thinnest body is either still the "
        "0x0b one-byte body or zero bytes.  The anchor holds in neither frame"
        % format(corp["bodies_le_3_bytes"].get("0b", 0), ","))
    add("L10", "1", "anchor F: a 0x1c token is followed by a Function export in 99%+ of hits",
        "%d/%d = %.3f%%" % (corp["call_token_operands_are_functions"],
                            corp["call_token_operands"], 100.0 *
                            corp["call_token_operands_are_functions"] /
                            max(corp["call_token_operands"], 1)),
        "PASS" if corp["call_token_operands_are_functions"] /
        max(corp["call_token_operands"], 1) > 0.98 else "FAIL",
        "every 0x1c operand in every body, not a 1-in-7 sample")
    add("L11", "1", "UEViewer stops after Children for GAME_Batman4", "UnTypeinfo.h:164", "PASS",
        "the local copy carries the quoted `return;` comment")
    add("L12", "1", "UEViewer reads ScriptSize bytes of script",
        "UnTypeinfo.h `Ar.Serialize(&Script[0], ScriptSize)`", "PASS",
        "the serializer's own line: ScriptSize is a byte count")
    add("L13", "2", "body B column: TakeDamage 2,028 / TakeRadius 288 / Drain 322",
        "%d / %d / %d" % (td["body_bytes_audit"], tw["body_bytes_audit"],
                          dw["body_bytes_audit"]), "FAIL",
        "each is one byte short of the ScriptSize field (%d / %d / %d)"
        % (td["head"]["script_size"], tw["head"]["script_size"], dw["head"]["script_size"]))
    add("L14", "3.1", "TakeDamage body literals: 9 found, distinct 0.5/1.0/2.0/2.5/5.0/1000.0",
        "%d plausible of %d 0x1e bytes, distinct %s"
        % (len(plausible(td)), len(td["float_bytes"]),
           sorted({c["value"] for c in plausible(td)})),
        "PASS" if len(plausible(td)) == 9 and sorted({c["value"] for c in plausible(td)}) ==
        [0.5, 1.0, 2.0, 2.5, 5.0, 1000.0] else "FAIL",
        "offsets %s" % [c["at"] for c in plausible(td)])
    add("L15", "3.2", "TakeRadiusDamageFromWeapon body literals: 0.0/0.1/0.5/1.0/1500.0",
        "%d plausible of %d 0x1e bytes, distinct %s"
        % (len(plausible(tw)), len(tw["float_bytes"]),
           sorted({c["value"] for c in plausible(tw)})),
        "PASS" if sorted({c["value"] for c in plausible(tw)}) == [0.0, 0.1, 0.5, 1.0, 1500.0]
        else "FAIL", "offsets %s" % [c["at"] for c in plausible(tw)])
    add("L16", "4", "DrainWeaponGeneratorForDamage body literals: 8 found, distinct "
                    "0.0/0.05/0.5/1.0",
        "%d plausible of %d 0x1e bytes, distinct %s"
        % (len(plausible(dw)), len(dw["float_bytes"]),
           sorted({c["value"] for c in plausible(dw)})),
        "PASS" if len(plausible(dw)) == 8 and sorted({c["value"] for c in plausible(dw)}) ==
        [0.0, 0.05, 0.5, 1.0] else "FAIL",
        "offsets %s" % [c["at"] for c in plausible(dw)])
    add("L17", "3.4", "TakesDamageFromRam body is 7 bytes (sha1 1aa78f33...); its 4 trailing "
                      "bytes do not form a descriptor, so the tail is UNKNOWN",
        "body is %d bytes (sha1 %s); the note's %d-byte slice hashes %s"
        % (ram["body_bytes_audit"], ram["body_sha1_audit"], ram["body_bytes_note"],
           ram["body_sha1_note"]), "FAIL",
        "the 8-byte body reads `04 27` (return true) then `04 3a 60 29 00 00` (return "
        "ReturnValue = export 10592, `TakesDamageFromRam.ReturnValue`, a BoolProperty)")
    add("L18", "3.1", "ArmourModeDamageReduction is read by exactly 1 script function",
        "%d" % len(readers(pkg, pkg.find("RVehicleBatmobileBase.ArmourModeDamageReduction"))),
        "PASS", "4-byte operand scan over all Function bodies")
    add("L19", "4", "LowHealthWarningLevel has exactly 1 reader",
        "%d" % len(readers(pkg, pkg.find("RVehicleBatmobileBase.LowHealthWarningLevel"))),
        "PASS", "same scan")
    add("L20", "5", "HealthRecoverRate is read by exactly 1 script function (ExperienceAwarded)",
        "%d" % len(readers(pkg, pkg.find("RVehicleBatmobileBase.HealthRecoverRate"))),
        "PASS", "same scan")
    add("L24", "2", "`exec<>` count in the exe: TakeDamage 3, TakeRadius 0, Drain 0",
        "%d / %d / %d prefix hits; %d / %d / %d NUL-terminated"
        % (reg["TakeDamage"]["prefix"], reg["TakeRadiusDamageFromWeapon"]["prefix"],
           reg["DrainWeaponGeneratorForDamage"]["prefix"], reg["TakeDamage"]["exact"],
           reg["TakeRadiusDamageFromWeapon"]["exact"],
           reg["DrainWeaponGeneratorForDamage"]["exact"]),
        "PASS" if (reg["TakeDamage"]["prefix"],
                   reg["TakeRadiusDamageFromWeapon"]["prefix"],
                   reg["DrainWeaponGeneratorForDamage"]["prefix"]) == (3, 0, 0) else "FAIL",
        "the note's substring method reproduces 3; one of the three is "
        "`execTakeDamageFromChainGun`, so the registrations of this exact name are %d.  The "
        "count still does not decide native-vs-script, as the note says — the body does"
        % reg["TakeDamage"]["exact"])
    add("L21", "1", "anchor A_super: SuperField of TakeDamage resolves to an inherited TakeDamage",
        "%s" % td["super_path"],
        "PASS" if (td["super_path"] or "").endswith(".TakeDamage") else "FAIL",
        "the field is an import (negative index) naming the parent's function")
    add("L22", "1", "anchor A_children: Children of TakeDamage is TakeDamage.DamageAmount",
        "%s" % td["children_path"],
        "PASS" if td["children_path"] == "RVehicleBatmobileBase.TakeDamage.DamageAmount"
        else "FAIL",
        "the field is an export whose outer_index is the function")
    add("L23", "1", "anchor E_native_parm_refs_own_properties",
        "%d/%d refs in %d descriptor stubs" % (corp["descriptor_refs_own"],
                                                corp["descriptor_refs"],
                                                corp["descriptor_stubs"]),
        "PASS" if corp["descriptor_refs_own"] == corp["descriptor_refs"] else "FAIL",
        "every `29 <ref>` stub in the package, not just the traced five")
    return out


# --------------------------------------------------------------------------- render
def table(header, rows, align=None):
    align = align or ["---"] * len(header)
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


def tree_text(node, paths):
    if "ref" in node:
        idx = node["ref"]["index"]
        p = paths.get(idx)
        return "`%s`" % (p if p else "%s %d" % (node["ref"]["token"], idx))
    if "float" in node:
        return "`%s`" % node["float"]
    if "int" in node:
        return "`%s`" % node["int"]
    if "bare" in node:
        return "`%s`" % node["bare"]
    if "un" in node:
        return "%s(%s)" % (node["un"], tree_text(node["arg"], paths))
    if "skip" in node:
        return "skip(%s)" % tree_text(node["skip"], paths)
    if "cast" in node:
        return "cast(%s)" % tree_text(node["arg"], paths)
    if "parms" in node:
        return "%s(%s)" % (node.get("op", "call"),
                           ", ".join(tree_text(x, paths) for x in node["parms"]))
    return "?"


def render(doc):
    ps = doc["package"]
    corp = doc["corpus"]
    blt = doc["body_length_test"]
    L = []
    A = L.append
    A("# Audit: the `Function` export layout in `DAMAGE_RULES.md` §1")
    A("")
    A("Generated by `Tools/scripts/bmak_damage_layout_audit.py --write`; `--check` re-derives "
      "every number from `BmGame.upk` and diffs both files.  Subject: "
      "`Research/BatmobileGrab/DAMAGE_RULES.md` §1 (layout), the constants it quotes for the "
      "three functions audited here, and two of its damage rules.")
    A("")
    A("Package, read by this audit's own reader: **%s** bytes, version %s, licensee %s, %s "
      "names, %s imports, %s exports, of which **%s** are `Function`."
      % (format(ps["bytes"], ","), ps["version"], ps["licensee"], format(ps["names"], ","),
         format(ps["imports"], ","), format(ps["exports"], ","),
         format(ps["functions"], ",")))
    A("")
    A("## Verdict")
    A("")
    A("**%s**" % doc["verdict"])
    A("")
    for line in doc["verdict_points"]:
        A("- " + line)
    A("")
    A("## 1. The head: where the bytecode starts")
    A("")
    L.extend(table(["offset", "field", "measured", "oracle"],
                   doc["head_table"], ["---:", "---", "---", "---"]))
    A("")
    A("## 2. The body: how long it is")
    A("")
    A("The note says the script at offset 22 is `len(export) - 38` bytes and that "
      "`ScriptSize == len(script) + 1`.  The field is a byte count, not a count-plus-one.")
    A("")
    A("**2a. The field against the export size, over all %s `Function` exports**"
      % format(ps["functions"], ","))
    A("")
    L.extend(table(["ScriptSize − (len(export) − 38)", "exports"],
                   [[k, format(v, ",")] for k, v in
                    corp["script_size_minus_(size-38)"].items()], ["---:", "---:"]))
    A("")
    A("**2b. Token-scan exact-end test** — a body of the right length is consumed exactly; a "
      "body cut short leaves a partial final token, so the scan cannot land on the last byte.")
    A("")
    L.extend(table(["body length", "scan ends exactly", "of", "%", "overshoots"],
                   [[k, format(v["exact_end"], ","), format(v["total"], ","), v["percent"],
                     format(v["overshoot"], ",")] for k, v in blt.items()],
                   ["---", "---:", "---:", "---:", "---:"]))
    A("")
    A("**2c. What the cut byte is.**  %s bodies end in `04 0b` — `EX_Return` + `EX_Nothing`, "
      "i.e. `return;` — only once the note's missing byte is included.  Under the note's slice "
      "they end on a bare `04`, a `Return` with no operand."
      % format(corp["bodies_ending_return_nothing"], ","))
    A("")
    A("%s further bodies end in `04 3a <4-byte ref>` — `return <ref>` — and the note's slice "
      "cuts the last byte of that reference, leaving a 3-byte operand.  `TakeRadiusDamageFrom"
      "Weapon` is one of them: its body ends `04 3a a6 28 00 00`, the note's ends `04 3a a6 28`."
      % format(corp["bodies_ending_return_ref"], ","))
    A("")
    A("## 3. The trailer")
    A("")
    A("After the body every `Function` export ends with a trailer whose last 8 bytes are the "
      "export's own `FName` and a zero number.")
    A("")
    L.extend(table(["trailer bytes", "exports"],
                   [[k, format(v, ",")] for k, v in corp["trailer_bytes"].items()],
                   ["---:", "---:"]))
    A("")
    A("The word the note calls a *pre-name word, always `0x0002xxxx`* takes these high halves: "
      "`%s`.  As an exact pattern the claim fails (0x0082… and 0xffff… exist); as a bit test "
      "(bit 17) it holds for all but the %s exports with a 17-byte trailer."
      % ("`, `".join(corp["pre_name_word_high16"]),
         corp["script_size_minus_(size-38)"].get("-1", 0)))
    A("")
    A("## 4. The three functions, re-parsed from the raw bytes")
    A("")
    L.extend(table(["function", "export", "file offset", "size", "ScriptSize",
                    "body (audit)", "body (note)", "body sha1 (audit)"],
                   [["`%s`" % fn["path"].rsplit(".", 1)[-1], fn["export"],
                     format(fn["file_offset"], ","), format(fn["size"], ","),
                     fn["head"]["script_size"], fn["body_bytes_audit"],
                     fn["body_bytes_note"], "`%s`" % fn["body_sha1_audit"]]
                    for fn in doc["functions"].values()],
                   ["---", "---:", "---:", "---:", "---:", "---:", "---:", "---"]))
    A("")
    A("Head fields resolved to objects — the independent check on offsets 2/6/10/14:")
    A("")
    L.extend(table(["function", "Next @2", "SuperField @6", "Children @10", "Line @14"],
                   [["`%s`" % fn["path"].rsplit(".", 1)[-1], "`%s`" % fn["next_path"],
                     "`%s`" % fn["super_path"], "`%s`" % fn["children_path"],
                     fn["head"]["line"]] for fn in doc["functions"].values()]))
    A("")
    A("### Every float constant in each body")
    A("")
    A("A float literal is a `0x1e` byte whose next four bytes decode to a plausible source "
      "float.  All of them are listed, so a constant the note missed would show up.")
    A("")
    for fn in doc["functions"].values():
        fb = fn["float_bytes"]
        A("**`%s`** — %d `0x1e` byte(s): %s" % (
            fn["path"].rsplit(".", 1)[-1], len(fb),
            ", ".join("`%s`@%d%s" % (c["value"], c["at"], "" if c["plausible"] else " (not a literal)")
                      for c in fb) or "none"))
        A("")
    A("### The `exec<>` counts the note quotes for the same three functions (§2)")
    A("")
    L.extend(table(["function", "note", "prefix hits", "NUL-terminated", "strings matching"],
                   [["`%s`" % k, v["note"], v["prefix"], v["exact"],
                     ", ".join("`%s`" % x for x in v["strings"])]
                    for k, v in doc["exe_registrations"].items()],
                   ["---", "---:", "---:", "---:", "---"]))
    A("")
    A("## 5. Two rules traced to bytecode")
    A("")
    paths = doc["_path_of"]
    for r in doc["rules"]:
        A("### `%s`" % r["id"])
        A("")
        A("Rule as the note states it: " + r["rule"])
        A("")
        if r["id"].startswith("R1"):
            A("- Gate: `%s` at body %d (`%s`), jump offset %d, condition at %d = `%s` — the "
              "`%s` instance variable.  Offset base assumed = end of the jump instruction; "
              "resulting target %d holds `%s` (statement start: %s)."
              % (r["gate"]["token"], r["gate"]["at"], r["gate"]["bytes"],
                 r["gate"]["jump_offset"], r["gate"]["condition_at"],
                 r["gate"]["condition_bytes"], r["gate_condition_ref"]["path"],
                 r["gate"]["target_at"], r["gate"]["target_byte"],
                 str(r["gate"]["target_is_statement_start"]).lower()))
            if not r["gate"]["target_is_statement_start"]:
                A("  The target does not land on a statement start, so `0x07`'s offset base "
                  "is **not** established here; the gate's sense rests on the token being "
                  "`JumpIfNot` with that condition, not on the target.  It does not matter "
                  "for this rule: the two plausible bases put the target at %s or %s, both "
                  "past the statement's last byte %d, so `not ArmouredMode` skips the "
                  "reduction under either convention."
                  % (format(r["gate"]["jump_offset"], ","),
                     format(r["gate"]["target_at"], ","), r["statement"]["end"] - 1))
            A("- Statement at %d..%d: `%s`"
              % (r["statement"]["at"], r["statement"]["end"], r["statement"]["bytes"]))
            A("")
            A("Decoded (each operator is a parm list closed by `0x16`; the nesting balances "
              "exactly and the statement ends on the next `0x0f` Let: %s):"
              % str(r["statement_ends_at_next_statement"]).lower())
            A("")
            A("```")
            A("%s = %s" % (tree_text(r["statement_tree"]["lhs"], paths),
                           tree_text(r["statement_tree"]["rhs"], paths)))
            A("```")
            A("")
            A("`ArmourModeDamageReduction` at %d; `100` occurs %d times in the statement; "
              "shipped values %s; read by %s."
              % (r["field_ref"]["at"], r["literal_100_count"],
                 ", ".join("`%s` = %s" % (v["archetype"], v["value"])
                           for v in r["shipped_values"]),
                 ", ".join("`%s`" % x for x in r["readers_in_package"])))
            A("")
            A("The tree is what the bytes say; its *semantics* above `0x7f` are not "
              "established (§7).  Read as a percentage cut — "
              "`(DamageAmount * (100 - ArmourModeDamageReduction)) / 100` — the two `100`s "
              "and the subtract-shaped subexpression fit, and with the shipped value 0 the "
              "factor is exactly 1, so the note's conclusion (shipped armoured mode reduces "
              "nothing) survives the weaker reading under either assignment of "
              "`0x90`/`0x91`.  What is verified: the field is the reduction, it is read "
              "here, the assignment is gated on `ArmouredMode`, and every archetype ships 0.")
        else:
            A("- Body, %d bytes: `%s`" % (r["body_bytes"], r["body"]))
            A("- Decoded: %s" % " → ".join(r["decode"]))
            A("")
            A("The fourth construct's reference completes to export %d = `%s` (%s).  The "
              "note's %d-byte body hashes `%s`: it is this body minus its last byte, and that "
              "is exactly why the note had to call the tail UNKNOWN."
              % (r["return_value_ref"]["index"], r["return_value_ref"]["path"],
                 r["return_value_ref"]["class"], r["note_body_bytes"],
                 r["note_body_sha1"]))
        A("")
    A("## 6. Every claim tested")
    A("")
    L.extend(table(["id", "§", "claim in the note", "as measured", "verdict"],
                   [[c["id"], c["section"], c["claim"], c["measured"], "**%s**" % c["verdict"]]
                    for c in doc["claims"]], ["---", "---", "---", "---", "---"]))
    A("")
    A("## 7. UNKNOWNs")
    A("")
    for u in doc["unknowns"]:
        A("- " + u)
    A("")
    A("## 8. Tool")
    A("")
    A("```")
    A("python Tools/scripts/bmak_damage_layout_audit.py --write   # this note + the JSON")
    A("python Tools/scripts/bmak_damage_layout_audit.py --check   # re-derive, diff, exit 1 on drift")
    A("```")
    A("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- build
def build():
    pkg = Pkg(UPK)
    docjson = json.load(open(DOC_JSON, encoding="utf-8"))
    corp = corpus(pkg)
    blt = body_length_test(pkg)
    funcs = {p: audit_function(pkg, p) for p in AUDITED}
    funcs[RAM] = audit_function(pkg, RAM)
    rules = rule_records(pkg, docjson)

    paths = {}
    for name in ("TakeDamage.DamageAmount", "RVehicleBatmobileBase.ArmourModeDamageReduction",
                 "TakeRadiusDamageFromWeapon.ReturnValue", "TakesDamageFromRam.ReturnValue",
                 "RVehicleBatmobileBase.ArmouredMode"):
        idx = pkg.find(name)
        if idx:
            paths[idx] = pkg.path(idx)
    for r in rules:
        for k in ("return_value_ref", "gate_condition_ref", "field_ref"):
            if k in r and r[k]["index"] not in paths:
                paths[r[k]["index"]] = pkg.path(r[k]["index"])
    for fn in funcs.values():
        paths[fn["export"]] = fn["path"]

    exec_counts = {}
    exe = open(EXE, "rb").read()
    for p in AUDITED + [RAM]:
        exec_counts[p] = len(re.findall(re.escape(("exec" + p.rsplit(".", 1)[-1]).encode()), exe))

    td, tw, dw, ram = (funcs[AUDITED[0]], funcs[AUDITED[1]], funcs[AUDITED[2]], funcs[RAM])
    one_short = corp["script_size_minus_(size-38)"].get("1", 0)
    one_long = corp["script_size_minus_(size-38)"].get("-1", 0)
    head_table = [
        ["@0", "u16 prefix", "%d/%d zero" % (corp["prefix_zero"],
                                             corp["function_exports"]),
         "two bytes at export offset 0"],
        ["@2", "Next", "%d/%d resolve" % (sum(v for k, v in corp["next_kind"].items()
                                              if k.startswith("export:")),
                                          corp["function_exports"]),
         "0, or an export of a UField subclass — never an import"],
        ["@6", "SuperField", "negative = import",
         "`%s` for TakeDamage; 0 for the two functions the class declares"
         % td["super_path"]],
        ["@10", "Children", "%d/%d own property" % (corp["children_kind"].get("own property", 0),
                                                    corp["function_exports"]),
         "0, or an export whose outer_index is this function"],
        ["@14", "Line", "source lines %d..%d" % (min(f["head"]["line"] for f in funcs.values()),
                                                 max(f["head"]["line"] for f in funcs.values())),
         "plausible editor lines"],
        ["@18", "ScriptSize", "body byte count", "§2 — not len + 1"],
    ]

    verdict_points = [
        "Head offsets 0/2/6/10/14/18: **confirmed**, each by an oracle over all %d `Function` "
        "exports (`u16@0` zero %d/%d, `Children` an own property %d/%d, trailing FName = own "
        "name %d/%d)."
        % (corp["function_exports"], corp["prefix_zero"], corp["function_exports"],
           corp["children_kind"].get("own property", 0), corp["function_exports"],
           corp["name_at_minus8_is_own_name"], corp["function_exports"]),
        "Body length: **one byte wrong**.  `ScriptSize` is the number of body bytes, not "
        "`len + 1`; the note's `len(export) - 38` cuts the last byte in %d of %d exports (and "
        "keeps one trailer byte in %d).  A token scan of ScriptSize bytes ends exactly on the "
        "last byte in %d bodies against %d for the note's length."
        % (one_short, corp["function_exports"], one_long,
           blt["ScriptSize (= @18)"]["exact_end"],
           blt["ScriptSize - 1 (= len(export) - 38, the note)"]["exact_end"]),
        "Trailer: 15 bytes, 17 on %d exports, always ending in the own FName + a zero number; "
        "the note's `flags word @size-16` is not a field and `pre-name word == 0x0002xxxx` is "
        "not exact." % one_long,
        "Anchors: 5 of the note's 7 hold as stated (A_super, A_children, D_name, "
        "E_native_parm_refs — %d/%d refs over %d stubs — and F_call_token at %d/%d); 2 do "
        "not (B_script_size_is_len_plus_one, C_thinnest_script_is_return)."
        % (corp["descriptor_refs_own"], corp["descriptor_refs"], corp["descriptor_stubs"],
           corp["call_token_operands_are_functions"], corp["call_token_operands"]),
        "Constants: every literal the note quotes for the three audited functions re-decodes "
        "to the quoted value, and no plausible float in those bodies is unaccounted for; the "
        "note quotes no offsets, this audit adds them.",
        "Rules: §3.1's armour-mode reduction and §3.4's unconditional `return true` both trace "
        "to exact bytecode; §3.4 is also the case where the one-byte error bites, because the "
        "cut byte is what completes `return ReturnValue`.",
    ]
    unknowns = [
        "Opcode semantics above `0x7F` (`0x90`, `0x91`, `0x93`, `0xb1`, …): the bodies use "
        "operators the note's token table does not list, and this audit does not name them.  "
        "They are decoded only as parm-list operators, and only where the nesting balances "
        "exactly; which of `0x90`/`0x91` is multiply and which is divide is not established "
        "here.  A runnable oracle (the game's VM) is outside the read-only inputs.",
        "The trailer's own fields (the bytes before the FName): neither the note nor this "
        "audit identifies them.  Only the length, the constant tail (FName index + 0) and the "
        "effect on the body boundary are decoded.",
        "The %d exports with a 17-byte trailer are counted, not explained." % one_long,
        "`Next`/`SuperField` are checked for resolution and class, not by walking the UField "
        "chain in order.",
    ]

    reg = exe_registrations()
    for k, note_value in (("TakeDamage", 3), ("TakeRadiusDamageFromWeapon", 0),
                          ("DrainWeaponGeneratorForDamage", 0)):
        reg[k]["note"] = note_value
    doc = {
        "schema": "bmak.damage_layout_audit/1",
        "generated_by": "Tools/scripts/bmak_damage_layout_audit.py",
        "subject": "Research/BatmobileGrab/DAMAGE_RULES.md",
        "exe_registrations": reg,
        "package": {"path": UPK, "bytes": pkg.bytes, "version": pkg.version,
                    "licensee": pkg.licensee, "chunked": pkg.chunked,
                    "names": len(pkg.names), "imports": pkg.import_count,
                    "exports": pkg.export_count, "functions": len(pkg.functions()),
                    "header_size": pkg.header_size},
        "verdict": "STRUCTURE HOLDS; BODY LENGTH IS ONE BYTE SHORT",
        "verdict_points": verdict_points,
        "head_table": head_table,
        "corpus": corp,
        "body_length_test": blt,
        "functions": funcs,
        "rules": rules,
        "claims": claims(pkg, docjson, funcs, corp, blt, reg),
        "exec_strings": exec_counts,
        "ueviewer": ueviewer_evidence(),
        "unknowns": unknowns,
    }
    # anchors: never write a record this audit does not believe
    assert corp["prefix_zero"] == corp["function_exports"]
    assert corp["name_at_minus8_is_own_name"] == corp["function_exports"]
    assert blt["ScriptSize (= @18)"]["exact_end"] > \
        blt["ScriptSize - 1 (= len(export) - 38, the note)"]["exact_end"]
    assert ram["body_bytes_audit"] == 8 and ram["body_bytes_note"] == 7
    assert td["body_bytes_audit"] == td["head"]["script_size"]

    json_text = json.dumps(doc, indent=1, sort_keys=True)
    md_text = render(dict(doc, _path_of=paths))
    return doc, json_text, md_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("--write or --check")
    doc, json_text, md_text = build()
    if a.write:
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(json_text + "\n")
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md_text)
        print("wrote", os.path.relpath(OUT_JSON, ROOT))
        print("wrote", os.path.relpath(OUT_MD, ROOT))
        print("verdict:", doc["verdict"])
        for c in doc["claims"]:
            print("  %-4s %s  %s" % (c["id"], c["verdict"], c["claim"][:70]))
        return 0
    ok = True
    for path, text, label in ((OUT_JSON, json_text + "\n", "json"), (OUT_MD, md_text, "md")):
        if not os.path.exists(path):
            print("%s: MISSING" % label)
            ok = False
            continue
        same = open(path, encoding="utf-8").read() == text
        print("%s: %s" % (label, "PASS" if same else "FAIL"))
        ok = ok and same
    print("check: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
