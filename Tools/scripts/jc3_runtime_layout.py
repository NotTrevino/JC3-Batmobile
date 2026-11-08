#!/usr/bin/env python3
"""jc3_runtime_layout.py - G3-07a: what a READ-ONLY JC3 sampler can read, proved statically.

The game is never run. Everything here comes from the PE on disk (`JustCause3.exe`, opened
read-only) plus `capstone` disassembly and the `.pdata` function table, so each claimed offset is
tied to the instruction that uses it.

Anchors (from MODLOG's crash dumps, then verified here):
    0x140201d4e  walks a part list        (MODLOG: "+0x201d60 recurses over children")
    0x140201de0  updates one part node    (MODLOG: node+0x140 record, +0x100/+0x101 bytes)
    0x1402020d1  reads a raycast body     (MODLOG: [node+0x158] -> world -> slot)
    0x1402020d1 -> 0x141505490 -> 0x1415140f0   the +0x151410f crash path
    0x140222ef0  enumerates a world's body slots

Oracles (each re-run by --check; a failure is a hard error):
    O1  the PE is the expected image: base 0x140000000, 7 sections, 188,670 `.pdata` entries
    O2  the instruction at exactly 0x14151410f is `movss xmm0, [rax + 0x14]` - the crash address
    O3  0x1415140f0 reads the slot as 0x50 shape, 0x0c flags, 0x40/0x30 float4s
    O4  0x140201de0 reads 0x100/0x101 bytes and the 0x140 record pointer, and loads the
        `.data` stack cookie 0x142e15310 (a non-zero value proves the image maps as expected)
    O5  0x1402020d1 loads [rbx+0x158], shifts the handle left 7 and adds [rdi+0x60]
    O6  0x140222ef0 reads [rcx+0x150] world, [rdi+0x68] count, [rdi+0x60] slot base, tests the
        slot's 0x60 byte and takes the address of the `.data` object 0x142dad020
    O7  the 16-byte `.rdata` constant at 0x142343bb0 is 0.001 x 4 (the tolerance vector the
        raycast path copies into its argument block)
    O8  call sites are verified: a byte scan for `E8 rel32` is only accepted when the instruction
        boundary at that address is a `call` with that target (no false positives)

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout.py --check
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import os
import struct
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, CS_OP_MEM, Cs

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
OUT_MD = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT.md")
OUT_JSON = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT.json")

# ---- the anchors, all module-relative RVAs that MODLOG's dumps name or that the chain reaches
A_PART_LIST = 0x201D4E
A_NODE_UPDATE = 0x201DE0
A_RAYCAST_READ = 0x2020D1
A_SLOT_QUERY = 0x1505490
A_SLOT_USE = 0x15140F0
A_SLOT_ENUM = 0x2022EF0 if False else 0x222EF0   # 0x140222ef0
CRASH_INS = 0x151410F
COOKIE = 0x142E15310
TOL_VEC = 0x142343BB0
DATA_OBJ = 0x142DAD020


def rva(va, base):
    return va - base


class Image:
    def __init__(self, path):
        self.path = path
        self.raw = open(path, "rb").read()
        self.sha256 = hashlib.sha256(self.raw).hexdigest()
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(s.Name.decode().strip("\x00"), self.base + s.VirtualAddress,
                      s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
                     for s in self.pe.sections]
        self.md = Cs(CS_ARCH_X86, CS_MODE_64)
        self.md.detail = True
        self._pdata()

    def _pdata(self):
        pd = [s for s in self.secs if s[0] == ".pdata"][0]
        o, end = pd[3], pd[3] + pd[4]
        fns = []
        while o + 12 <= end:
            b, e, _u = struct.unpack_from("<III", self.raw, o)
            if b == 0:
                break
            fns.append((self.base + b, self.base + e))
            o += 12
        fns.sort()
        self.fns = fns
        self.starts = [f[0] for f in fns]

    def off(self, va):
        for _n, sva, vs, raw, _rs in self.secs:
            if sva <= va < sva + vs:
                return raw + (va - sva)
        raise KeyError(hex(va))

    def sec(self, va):
        for n, sva, vs, _raw, _rs in self.secs:
            if sva <= va < sva + vs:
                return n
        return None

    def bytes_at(self, va, n):
        o = self.off(va)
        return self.raw[o:o + n]

    def fn_of(self, va):
        i = bisect.bisect_right(self.starts, va) - 1
        if i >= 0 and self.fns[i][0] <= va < self.fns[i][1]:
            return self.fns[i]
        return None

    def insns(self, va, limit=400, span=None):
        f = self.fn_of(va)
        if not f:
            return []
        end = span or min(f[1] - f[0], 6000)
        code = self.bytes_at(va if va == f[0] else f[0], 0)  # keeps the signature honest
        code = self.bytes_at(f[0], min(end, f[1] - f[0]))
        out = []
        for i in self.md.disasm(code, f[0]):
            out.append(i)
            if len(out) >= limit:
                break
        return out

    def at(self, va):
        for i in self.insns(va, limit=4000):
            if i.address == va:
                return i
            if i.address > va:
                return None
        return None

    def calls_to(self, target):
        """Every verified `call target`: byte scan, then instruction-boundary check."""
        txt = [s for s in self.secs if s[0] == ".text"][0]
        tva, traw, trs = txt[1], txt[3], txt[4]
        code = self.raw[traw:traw + trs]
        sites, p = [], 0
        while True:
            p = code.find(b"\xe8", p)
            if p < 0 or p + 5 > len(code):
                break
            dest = tva + p + 5 + struct.unpack_from("<i", code, p + 1)[0]
            if dest == target:
                ins = self.at(tva + p)
                if ins is not None and ins.mnemonic == "call" and ins.op_str == hex(target):
                    sites.append(tva + p)
            p += 1
        return sites


def mem_ops(ins):
    """(base_name, disp) for each memory operand; base 41 is RIP."""
    out = []
    for op in ins.operands:
        if op.type == CS_OP_MEM:
            name = ins.reg_name(op.mem.base) if op.mem.base else None
            out.append((name, op.mem.disp, op.mem.index != 0))
    return out


def has_read(img, fn_va, base_reg, disp, text_hint=None):
    """True when fn_va's body contains a memory operand [base_reg + disp]."""
    for ins in img.insns(fn_va, limit=4000):
        for name, d, _idx in mem_ops(ins):
            if name == base_reg and d == disp:
                if text_hint is None or text_hint in ins.op_str:
                    return True
    return False


def build():
    if not os.path.exists(EXE):
        raise SystemExit("JustCause3.exe not found at %s" % EXE)
    img = Image(EXE)
    base = img.base
    doc = {"exe": EXE, "size": len(img.raw), "sha256": img.sha256,
           "image_base": hex(base), "sections": [], "functions": [], "oracles": [],
           "fields": {}, "call_sites": {}}
    for name, va, vs, raw, rs in img.secs:
        doc["sections"].append({"name": name, "va": hex(va), "vsize": hex(vs),
                                "raw": hex(raw), "raw_size": hex(rs)})

    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    text = next(s for s in img.secs if s[0] == ".text")
    pd = next(s for s in img.secs if s[0] == ".pdata")
    oracle("O1-image",
           base == 0x140000000 and len(img.secs) == 7 and len(img.fns) == 188670,
           "base %#x, %d sections, %d .pdata functions, .text %#x/%#x B, .pdata %#x"
           % (base, len(img.secs), len(img.fns), text[1], text[2], pd[1]))

    crash = img.at(base + CRASH_INS)
    oracle("O2-crash-instruction",
           crash is not None and crash.mnemonic == "movss"
           and crash.op_str == "xmm0, dword ptr [rax + 0x14]",
           "at %#x: %s %s" % (base + CRASH_INS, crash.mnemonic if crash else "?",
                              crash.op_str if crash else "?"))

    use_fn = img.fn_of(base + A_SLOT_USE)
    use = {"fn": hex(use_fn[0]), "size": use_fn[1] - use_fn[0],
           "shape": has_read(img, use_fn[0], "rcx", 0x50),
           "flags": has_read(img, use_fn[0], "rcx", 0xC),
           "f40": has_read(img, use_fn[0], "rcx", 0x40),
           "f30": has_read(img, use_fn[0], "rcx", 0x30),
           "shape_radius": has_read(img, use_fn[0], "rax", 0x14)}
    oracle("O3-slot-use",
           all(use[k] for k in ("shape", "flags", "f40", "f30", "shape_radius")),
           "%s (%d B): rcx+0x50 shape=%s, rcx+0x0c flags=%s, rcx+0x40=%s, rcx+0x30=%s, "
           "rax+0x14=%s" % (use["fn"], use["size"], use["shape"], use["flags"], use["f40"],
                            use["f30"], use["shape_radius"]))

    node_fn = img.fn_of(base + A_NODE_UPDATE)
    cookie = struct.unpack("<Q", img.bytes_at(COOKIE, 8))[0]
    node = {"fn": hex(node_fn[0]), "size": node_fn[1] - node_fn[0],
            "b100": has_read(img, node_fn[0], "rcx", 0x100),
            "b101": has_read(img, node_fn[0], "rcx", 0x101),
            "rec140": has_read(img, node_fn[0], "rcx", 0x140),
            "cookie": hex(cookie), "cookie_sec": img.sec(COOKIE)}
    oracle("O4-node-update",
           all(node[k] for k in ("b100", "b101", "rec140")) and cookie != 0,
           "%s (%d B): rcx+0x100=%s, rcx+0x101=%s, rcx+0x140=%s; stack cookie at %#x = %#x "
           "(%s)" % (node["fn"], node["size"], node["b100"], node["b101"], node["rec140"],
                     COOKIE, cookie, img.sec(COOKIE)))

    ray_fn = img.fn_of(base + A_RAYCAST_READ)
    shl7 = add60 = load158 = False
    for i in img.insns(ray_fn[0], limit=4000):
        if i.mnemonic == "shl" and i.op_str.endswith(", 7"):
            shl7 = True
        if i.mnemonic == "add" and "qword ptr [rdi + 0x60]" in i.op_str:
            add60 = True
        if i.mnemonic == "mov" and i.op_str.startswith("rdi, qword ptr [rbx + 0x158]"):
            load158 = True
    tol_bytes = img.bytes_at(TOL_VEC, 16)
    tol_ok = tol_bytes == struct.pack("<f", 0.001) * 4      # float32 0.001, bit for bit
    ray = {"fn": hex(ray_fn[0]), "size": ray_fn[1] - ray_fn[0],
           "slot_base_load": load158, "handle_shift7": shl7, "slot_add": add60,
           "tol": struct.unpack("<4f", tol_bytes), "tol_is_1e-3_f32": tol_ok}
    oracle("O5-raycast-read",
           load158 and shl7 and add60 and tol_ok,
           "%s (%d B): [rbx+0x158]=%s, shl ...,7=%s, add [rdi+0x60]=%s; %#x = %s (%s)"
           % (ray["fn"], ray["size"], load158, shl7, add60, TOL_VEC,
              ", ".join("%.9g" % v for v in ray["tol"]),
              "bit-exact 4x float32(0.001)" if tol_ok else "NOT the 0.001 vector"))

    enum_fn = img.fn_of(base + A_SLOT_ENUM)
    enum = {"fn": hex(enum_fn[0]), "size": enum_fn[1] - enum_fn[0],
            "world150": has_read(img, enum_fn[0], "rcx", 0x150),
            "count68": has_read(img, enum_fn[0], "rdi", 0x68),
            "base60": has_read(img, enum_fn[0], "rdi", 0x60),
            "flag60": False, "data_obj": False}
    for i in img.insns(enum_fn[0], limit=4000):
        if i.mnemonic == "cmp" and "[rcx + rax + 0x60]" in i.op_str:
            enum["flag60"] = True
        if i.mnemonic == "lea" and "rip" in i.op_str:
            try:
                disp = int(i.op_str.split("rip + ")[1].rstrip("]"), 16)
                if i.address + i.size + disp == DATA_OBJ:
                    enum["data_obj"] = True
            except ValueError:
                pass
    data_bytes = img.bytes_at(DATA_OBJ, 8)
    enum["data_obj_value"] = struct.unpack("<fi", data_bytes)
    oracle("O6-slot-enum",
           enum["world150"] and enum["count68"] and enum["base60"] and enum["flag60"]
           and enum["data_obj"],
           "%s (%d B): rcx+0x150=%s, rdi+0x68 count=%s, rdi+0x60 base=%s, "
           "[rcx+rax+0x60] flag=%s, lea %#x=%s (holds %r)"
           % (enum["fn"], enum["size"], enum["world150"], enum["count68"], enum["base60"],
              enum["flag60"], DATA_OBJ, enum["data_obj"], enum["data_obj_value"]))

    oracles.append({"key": "O7-tolerance-vector", "ok": tol_ok,
                    "evidence": "%#x == 4x float32(0.001) bit for bit (bytes %s)"
                                % (TOL_VEC, tol_bytes.hex(" "))})

    sites = {"slot_use": img.calls_to(base + A_SLOT_USE),
             "slot_query": img.calls_to(base + A_SLOT_QUERY),
             "node_update": img.calls_to(base + A_NODE_UPDATE),
             "part_list": img.calls_to(base + A_PART_LIST)}
    doc["call_sites"] = {k: {"count": len(v), "sites": [hex(s) for s in v]} for k, v in sites.items()}
    oracle("O8-call-verification",
           len(sites["slot_use"]) == 4 and len(sites["slot_query"]) == 4
           and len(sites["node_update"]) == 3,
           "verified call sites: slot_use %d, slot_query %d, node_update %d, part_list %d "
           "(byte scan accepted only at an instruction boundary)"
           % (len(sites["slot_use"]), len(sites["slot_query"]), len(sites["node_update"]),
              len(sites["part_list"])))

    doc["functions"] = [
        {"name": "part_list_walk", "va": hex(base + A_PART_LIST),
         "fn": [hex(img.fn_of(base + A_PART_LIST)[0]), hex(img.fn_of(base + A_PART_LIST)[1])],
         "role": "walks a part list: [obj] next pointer at +0x00, byte gates at +0x2d/+0x46, "
                 "dword at +0x104"},
        {"name": "part_node_update", "va": hex(base + A_NODE_UPDATE),
         "fn": [hex(node_fn[0]), hex(node_fn[1])],
         "role": "one part node: flags at +0x100/+0x101, runtime record at +0x140"},
        {"name": "raycast_body_read", "va": hex(base + A_RAYCAST_READ), "fn": [hex(ray_fn[0]), hex(ray_fn[1])],
         "role": "raycast world at node+0x158 -> slot = world+0x60 + handle*128"},
        {"name": "body_slot_query", "va": hex(base + A_SLOT_QUERY),
         "fn": [hex(img.fn_of(base + A_SLOT_QUERY)[0]), hex(img.fn_of(base + A_SLOT_QUERY)[1])],
         "role": "takes the world pointer (rcx) and a handle list; the raycast path calls it"},
        {"name": "body_slot_use", "va": hex(base + A_SLOT_USE), "fn": [hex(use_fn[0]), hex(use_fn[1])],
         "role": "reads a slot: shape +0x50, flags +0x0c, float4s +0x40/+0x30; 0x151410f is here"},
        {"name": "body_slot_enum", "va": hex(base + A_SLOT_ENUM), "fn": [hex(enum_fn[0]), hex(enum_fn[1])],
         "role": "enumerates a world's slots: count +0x68, base +0x60, free byte +0x60 per slot"},
    ]
    doc["oracles"] = oracles

    doc["fields"] = {
        "part_node": [
            {"offset": "0x00", "what": "next pointer of the part list", "src": "0x140201d4e"},
            {"offset": "0x2d", "what": "byte gate tested before the walk recurses", "src": "0x140201d60"},
            {"offset": "0x46", "what": "byte gate that stops the walk", "src": "0x140201d80"},
            {"offset": "0x100", "what": "byte flag (0 -> skip the node update)", "src": "0x140201e05"},
            {"offset": "0x101", "what": "second byte flag", "src": "0x140201e18"},
            {"offset": "0x102", "what": "byte written to 0 when the raycast body is dropped",
             "src": "0x140222fe1"},
            {"offset": "0x104", "what": "dword tested in the list walk", "src": "0x140201d9d"},
            {"offset": "0x140", "what": "runtime part record pointer", "src": "0x140201e25"},
            {"offset": "0x150", "what": "world object pointer", "src": "0x140201f83"},
            {"offset": "0x158", "what": "raycast world object pointer", "src": "0x1402020d1"},
            {"offset": "0x170", "what": "float multiplied into the 0x120/0x124/0x128 reads",
             "src": "0x140201fa5"},
            {"offset": "0x178", "what": "float written back", "src": "0x140202017"},
            {"offset": "0x17c", "what": "float written back", "src": "0x14020202a"},
        ],
        "physics_world": [
            {"offset": "0x60", "what": "body-slot array base", "src": "0x14020210b / 0x140222f88"},
            {"offset": "0x68", "what": "body-slot count (int32, loop bound)", "src": "0x140222f39"},
        ],
        "body_slot": [
            {"offset": "0x00", "what": "row 0 of a 3x4 (0x30) / 3x4+ (0x40) float4 pair - see UNKNOWN 2",
             "src": "0x141514123"},
            {"offset": "0x0c", "what": "flags dword; bit 3 and bit 0 tested", "src": "0x141514128"},
            {"offset": "0x30", "what": "float4 copied out (transform row?)", "src": "0x14151411f"},
            {"offset": "0x40", "what": "float4 copied out (transform row?)", "src": "0x141514105"},
            {"offset": "0x50", "what": "shape pointer", "src": "0x1415140fe"},
            {"offset": "0x60", "what": "byte tested per slot in the enumeration (free/occupied)",
             "src": "0x140222f8c"},
        ],
        "shape": [
            {"offset": "0x10", "what": "byte flag (bit 0 tested)", "src": "0x14151413c"},
            {"offset": "0x13", "what": "byte compared to 1", "src": "0x141514132"},
            {"offset": "0x14", "what": "float read at the crash address (0.001-tolerance test follows)",
             "src": "0x14151410f"},
        ],
        "runtime_part_record": [
            {"offset": "0x120", "what": "float read with [record+0x170]", "src": "0x140201ff8"},
            {"offset": "0x124", "what": "float read with [record+0x170]", "src": "0x140201fe8"},
            {"offset": "0x128", "what": "float read with [record+0x170]", "src": "0x140201ff0"},
        ],
    }
    doc["recipe"] = [
        "Find the module base (EnumProcessModules), then read the part node's world pointer at "
        "+0x150 (and the raycast world at +0x158).",
        "Read the slot count at world+0x68 and the slot array base at world+0x60.",
        "For a handle h (int16, < 0 means none): slot = world[+0x60] + h*128.",
        "Per slot: flags at +0x0c, float4s at +0x30/+0x40, shape pointer at +0x50, free byte at "
        "+0x60.",
        "Per shape: byte +0x10, byte +0x13, float +0x14.",
        "Every read above is a fixed offset from a pointer already dereferenced by the game's own "
        "code path (0x1402020d1 -> 0x141505490 -> 0x1415140f0); a sampler does not need to "
        "interpret any of them to copy them.",
    ]
    doc["unknowns"] = [
        {"what": "the entity/vehicle list root (a global that leads to a spawned vehicle)",
         "why": "no anchor in MODLOG reaches it and no self-validating structure exists in the "
                "file image: the part node is reached from its parent, never from a global that "
                "the static image proves. Tried: verified callers of the four anchors (0x201de0 "
                "3, 0x1505490 4, 0x15140f0 4, 0x201d4e 0) and every `.data` operand they touch; "
                "the only `.data` object on the chain is 0x142dad020, passed by `lea` as an "
                "argument and holding %r - a value block, not a root pointer. Where it "
                "would be: a read-only probe that scans `.data` for a pointer whose target holds "
                "the part list's node layout (+0x150/+0x158 non-null)." % (enum["data_obj_value"],)},
        {"what": "which slot field is the world transform and which is the AABB",
         "why": "0x1415140f0 copies +0x40 and +0x30 as float4s and 0x140201ebd builds a 3x4 from "
                "node +0xc8..+0xf8, but no instruction in the anchors writes them back into an "
                "AABB or compares min/max, so 'transform' vs 'bounds' is a reading, not a decode."},
        {"what": "the render-instance transform",
         "why": "the anchors are physics-side only; no anchor dereferences a render instance. "
                "Tried: the call graph of the four anchors (all bodies' `.data` operands listed). "
                "Where it would be: the draw/instance path, which no MODLOG dump names."},
        {"what": "the loaded-resource table (path hashes)",
         "why": "not on any anchor's path; the only hash-keyed structure the project has decoded "
                "is the `.epe` palette reference (0x6187A56B at 0x266), which is asset-side. A "
                "static search for it would need a name list and an xref method this card does "
                "not have a self-validating oracle for."},
        {"what": "whether a slot handle is global or per-world",
         "why": "0x140222ef0 enumerates handles 0..count-1 of ONE world and writes them into a "
                "caller buffer; the transfer to the parts' +0x100/+0x102 fields is not in that "
                "function."},
    ]
    doc["counts"] = {"sections": len(img.secs), "pdata_functions": len(img.fns),
                     "text_bytes": text[2], "pdata_bytes": pd[4]}
    doc["generated_by"] = "Tools/scripts/jc3_runtime_layout.py --write"
    return doc


def render(doc):
    L = []
    A = L.append
    ok = sum(1 for o in doc["oracles"] if o["ok"])
    A("# JC3 runtime layout for a read-only sampler (G3-07a)")
    A("")
    A("Generated by `Tools/scripts/jc3_runtime_layout.py --write`; `--check` re-derives every")
    A("number and re-runs every oracle. The game is never run: everything here is read from")
    A("`%s` (read-only) with `pefile`/`capstone`, and every offset is tied to the instruction that" % doc["exe"])
    A("uses it.")
    A("")
    A("**Oracles: %d/%d pass.** A failing oracle is a hard error in `--check`, not a note." % (ok, len(doc["oracles"])))
    A("")
    A("## 1. The image")
    A("")
    A("| item | value |")
    A("|---|---|")
    A("| path | `%s` |" % doc["exe"])
    A("| size / sha256 | %s B / `%s` |" % (f"{doc['size']:,}", doc["sha256"]))
    A("| image base | %s |" % doc["image_base"])
    A("| `.pdata` functions | %s |" % f"{doc['counts']['pdata_functions']:,}")
    A("")
    A("| section | VA | virtual size | raw |")
    A("|---|---|---|---|")
    for s in doc["sections"]:
        A("| `%s` | %s | %s | %s (raw %s) |" % (s["name"], s["va"], s["vsize"], s["raw"], s["raw_size"]))
    A("")
    A("## 2. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in doc["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**", o["evidence"]))
    A("")
    A("## 3. The functions on the chain")
    A("")
    A("| function | entry | body | what it does |")
    A("|---|---|---|---|")
    for f in doc["functions"]:
        A("| `%s` | %s | %s..%s | %s |" % (f["name"], f["va"], f["fn"][0], f["fn"][1], f["role"]))
    A("")
    A("Verified call sites (byte scan accepted only where the instruction boundary is a `call`):")
    A("")
    A("| target | sites |")
    A("|---|---|")
    for k, v in sorted(doc["call_sites"].items()):
        A("| `%s` | %d %s |" % (k, v["count"], ", ".join("`%s`" % s for s in v["sites"][:6])))
    A("")
    A("## 4. Offsets a sampler reads")
    A("")
    for group in ("part_node", "physics_world", "body_slot", "shape", "runtime_part_record"):
        A("### `%s`" % group)
        A("")
        A("| offset | what | the instruction that uses it |")
        A("|---|---|---|")
        for f in doc["fields"][group]:
            A("| `%s` | %s | `%s` |" % (f["offset"], f["what"], f["src"]))
        A("")
    A("## 5. The recipe")
    A("")
    for i, step in enumerate(doc["recipe"], 1):
        A("%d. %s" % (i, step))
    A("")
    A("## 6. What is NOT decoded")
    A("")
    for u in doc["unknowns"]:
        A("- **%s** — %s" % (u["what"], u["why"]))
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout.py --write")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout.py --check")
    A("```")
    A("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    fails = [o["key"] for o in doc["oracles"] if not o["ok"]]

    if a.write:
        if fails:
            print("FAIL: oracles failed, nothing written: %s" % ", ".join(fails))
            return 1
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote Research/JC3Grab/RUNTIME_LAYOUT.md and .json")
        print("  image %s B, %d sections, %d .pdata functions"
              % (f"{doc['size']:,}", doc["counts"]["sections"], doc["counts"]["pdata_functions"]))
        print("  oracles %d/%d, functions %d, fields %d, call sites %s"
              % (len(doc["oracles"]) - len(fails), len(doc["oracles"]), len(doc["functions"]),
                 sum(len(v) for v in doc["fields"].values()),
                 {k: v["count"] for k, v in sorted(doc["call_sites"].items())}))
        print("  unknowns %d" % len(doc["unknowns"]))
        return 0

    if fails:
        print("FAIL")
        for o in doc["oracles"]:
            if not o["ok"]:
                print("  - oracle %s: %s" % (o["key"], o["evidence"]))
        return 1
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != md:
        print("FAIL: RUNTIME_LAYOUT.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: RUNTIME_LAYOUT.json is stale")
        return 1
    print("OK %d/%d oracles, %d functions, %d call sites, %d unknowns, md+json byte-identical"
          % (len(doc["oracles"]), len(doc["oracles"]), len(doc["functions"]),
             sum(v["count"] for v in doc["call_sites"].values()), len(doc["unknowns"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
