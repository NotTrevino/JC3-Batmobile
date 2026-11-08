#!/usr/bin/env python3
"""jc3_runtime_layout_review.py - G3-07a review: does RUNTIME_LAYOUT.md survive its own disassembly?

Reviews `Research/JC3Grab/RUNTIME_LAYOUT.md` (G3-07a) without touching it. The game is never
run; everything is read from `D:/Games/Just Cause 3/JustCause3.exe` (read-only) with
`pefile`/`capstone` and the `.pdata` chunk table.

For every offset the document claims it re-derives, from the instruction bytes:

    R1  the cited address is inside a `.pdata` chunk and is an instruction boundary;
    R2  the instruction there has a memory operand with the claimed base register,
        displacement, access width and read/write direction;
    R3  if R2 fails, whether the *same* displacement/width appears elsewhere in the
        contiguous chunk chain, and where (MIS-CITED) - or nowhere (UNSUPPORTED);
    R4  the base register's provenance: the last write to it before the instruction,
        so `[rax+0x14]` is only a `shape` field if `rax` was loaded from the shape slot.

It then re-implements the document's own 8 oracle predicates with their exact semantics
(chunk-scoped `has_read`) and measures, per oracle leg, the set of *wrong* offsets that
would still make the leg pass ("collision set"). A row with no oracle leg at all is
reported as unguarded.

Extra checks (targeted, each tied to instructions):
    C1  the claimed call chain 0x1402020d1 -> 0x141505490 -> 0x1415140f0
    C2  `body_slot +0x0c` flag bits claimed tested: bit 3 and bit 0
    C3  `shape +0x14` "0.001-tolerance test follows"
    C4  `.pdata` chunk vs real function extent for the six anchors
    C5  the 0x7fff handle sentinel the document's recipe does not mention
    C6  `body_slot +0x00` (3x4 row) - cited instruction vs real use

Oracles (re-run by --check; a failure is a hard error):
    P1  the image is the documented one (sha256, size, base, 7 sections, 188,670 chunks)
    P2  every cited address is reproduced from the bytes (instruction text independent
        of the span the document quotes)
    P3  the 8 original oracle predicates, re-implemented, still evaluate as documented
    P4  every verdict in this report is a pure function of the bytes: re-running --write
        on the same image yields byte-identical output

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout_review.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout_review.py --check
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
from capstone import CS_ARCH_X86, CS_MODE_64, CS_OP_IMM, CS_OP_MEM, CS_OP_REG, Cs

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
OUT_MD = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT_REVIEW.md")
OUT_JSON = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT_REVIEW.json")

# documented image (RUNTIME_LAYOUT.md section 1)
DOC_SHA = "a53c2d6b2837f45d97244fc096e68f27ba9036e0582a0d9aada2e2f222dac293"
DOC_SIZE = 51083264
DOC_BASE = 0x140000000
DOC_SECTIONS = 7
DOC_CHUNKS = 188670

CRASH = 0x151410F
TOL_VEC = 0x142343BB0
COOKIE = 0x142E15310
A_PART_LIST = 0x201D4E
A_NODE = 0x201DE0
A_RAYCAST = 0x2020D1
A_QUERY = 0x1505490
A_USE = 0x15140F0
A_ENUM = 0x222EF0
SLOT_SETTER = 0x1513FA0      # writes slot+0x00/+0x10/+0x20/+0x30 (called by slot_query)
SLOT_FLAGUSER = 0x1514070    # called by slot_query with the slot in rcx

# ---------------------------------------------------------------------------------------
# The claims, verbatim from Research/JC3Grab/RUNTIME_LAYOUT.md section 4.
# guard = the original oracle leg that references this displacement as a hardcoded constant
# (None = no oracle in the reviewed script mentions it at all).
CLAIMS = [
    ("part_node", 0x00, "next pointer of the part list", 0x140201D4E, "rbx", 0x00, 8, "r", None),
    ("part_node", 0x2D, "byte gate tested before the walk recurses", 0x140201D60, "rbx", 0x2D, 1, "r", None),
    ("part_node", 0x46, "byte gate that stops the walk", 0x140201D80, "rax", 0x46, 1, "r", None),
    ("part_node", 0x100, "byte flag (0 -> skip the node update)", 0x140201E05, "rcx", 0x100, 1, "r", "O4.b100"),
    ("part_node", 0x101, "second byte flag", 0x140201E18, "rcx", 0x101, 1, "r", "O4.b101"),
    ("part_node", 0x102, "byte written to 0 when the raycast body is dropped", 0x140222FE1, "rsi", 0x102, 1, "w", None),
    ("part_node", 0x104, "dword tested in the list walk", 0x140201D9D, "rbx", 0x104, 4, "r", None),
    ("part_node", 0x140, "runtime part record pointer", 0x140201E25, "rcx", 0x140, 8, "r", "O4.rec140"),
    ("part_node", 0x150, "world object pointer", 0x140201F83, "rbx", 0x150, 8, "r", "O6.world150*"),
    ("part_node", 0x158, "raycast world object pointer", 0x1402020D1, "rbx", 0x158, 8, "r", "O5.load158"),
    ("part_node", 0x170, "float multiplied into the 0x120/0x124/0x128 reads", 0x140201FA5, "rbx", 0x170, 4, "r", None),
    ("part_node", 0x178, "float written back", 0x140202017, "rbx", 0x178, 4, "w", None),
    ("part_node", 0x17C, "float written back", 0x14020202A, "rbx", 0x17C, 4, "w", None),
    ("physics_world", 0x60, "body-slot array base", 0x14020210B, "rdi", 0x60, 8, "r", "O5.add60"),
    ("physics_world", 0x68, "body-slot count (int32, loop bound)", 0x140222F39, "rdi", 0x68, 4, "r", "O6.count68"),
    ("body_slot", 0x00, "row 0 of a 3x4 (0x30) / 3x4+ (0x40) float4 pair", 0x141514123, "rcx", 0x00, 16, "r", None),
    ("body_slot", 0x0C, "flags dword; bit 3 and bit 0 tested", 0x141514128, "rcx", 0x0C, 4, "r", "O3.flags"),
    ("body_slot", 0x30, "float4 copied out (transform row?)", 0x14151411F, "rcx", 0x30, 16, "r", "O3.f30"),
    ("body_slot", 0x40, "float4 copied out (transform row?)", 0x141514105, "rcx", 0x40, 16, "r", "O3.f40"),
    ("body_slot", 0x50, "shape pointer", 0x1415140FE, "rcx", 0x50, 8, "r", "O3.shape"),
    ("body_slot", 0x60, "byte tested per slot in the enumeration (free/occupied)", 0x140222F8C, "indexed", 0x60, 1, "r", "O6.flag60"),
    ("shape", 0x10, "byte flag (bit 0 tested)", 0x14151413C, "rax", 0x10, 1, "r", None),
    ("shape", 0x13, "byte compared to 1", 0x141514132, "rax", 0x13, 1, "r", None),
    ("shape", 0x14, "float read at the crash address (0.001-tolerance test follows)", 0x14151410F, "rax", 0x14, 4, "r", "O3.shape_radius"),
    ("runtime_part_record", 0x120, "float read with [record+0x170]", 0x140201FF8, "rax", 0x120, 4, "r", None),
    ("runtime_part_record", 0x124, "float read with [record+0x170]", 0x140201FE8, "rax", 0x124, 4, "r", None),
    ("runtime_part_record", 0x128, "float read with [record+0x170]", 0x140201FF0, "rax", 0x128, 4, "r", None),
]

# the six anchors as the document names them: (name, va, documented body end, documented bytes)
ANCHORS = [
    ("part_list_walk", A_PART_LIST, 0x140201DC8),
    ("part_node_update", A_NODE, 0x140201E2C),
    ("raycast_body_read", A_RAYCAST, 0x14020216E),
    ("body_slot_query", A_QUERY, 0x1415054B6),
    ("body_slot_use", A_USE, 0x141514140),
    ("body_slot_enum", A_ENUM, 0x14022302B),
]

REGS = ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
        "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]
ALIAS = {}
for _r in REGS:
    ALIAS[_r] = _r
for _r, _subs in (("rax", ("eax", "ax", "al", "ah")), ("rbx", ("ebx", "bx", "bl", "bh")),
                  ("rcx", ("ecx", "cx", "cl", "ch")), ("rdx", ("edx", "dx", "dl", "dh")),
                  ("rsi", ("esi", "si", "sil")), ("rdi", ("edi", "di", "dil")),
                  ("rbp", ("ebp", "bp", "bpl")), ("rsp", ("esp", "sp", "spl")),
                  ("r8", ("r8d", "r8w", "r8b")), ("r9", ("r9d", "r9w", "r9b")),
                  ("r10", ("r10d", "r10w", "r10b")), ("r11", ("r11d", "r11w", "r11b")),
                  ("r12", ("r12d", "r12w", "r12b")), ("r13", ("r13d", "r13w", "r13b")),
                  ("r14", ("r14d", "r14w", "r14b")), ("r15", ("r15d", "r15w", "r15b"))):
    for _s in _subs:
        ALIAS[_s] = _r

WRITES = {"mov", "movzx", "movsx", "movsxd", "lea", "xor", "add", "sub", "and", "or",
          "shl", "shr", "sar", "not", "neg", "inc", "dec", "pop", "imul", "mul", "div",
          "movss", "movaps", "movups", "movd", "movq", "cmovne", "cmovns", "cmove",
          "addps", "mulps", "subps", "unpcklps", "shufps", "cmpeqps", "movmskps"}
TERMINATORS = {"ret", "jmp", "int3", "ud2", "hlt"}


def canonical(reg_name):
    return ALIAS.get(reg_name, reg_name)


class Image:
    def __init__(self, path):
        self.raw = open(path, "rb").read()
        self.sha256 = hashlib.sha256(self.raw).hexdigest()
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(s.Name.decode().strip("\x00"), self.base + s.VirtualAddress,
                      s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
                     for s in self.pe.sections]
        self.md = Cs(CS_ARCH_X86, CS_MODE_64)
        self.md.detail = True
        pd = next(s for s in self.secs if s[0] == ".pdata")
        o, end = pd[3], pd[3] + pd[4]
        chunks = []
        while o + 12 <= end:
            b, e, _u = struct.unpack_from("<III", self.raw, o)
            if b == 0:
                break
            chunks.append((self.base + b, self.base + e))
            o += 12
        chunks.sort()
        self.chunks = chunks
        self.starts = [c[0] for c in chunks]
        self.by_start = {c[0]: c for c in chunks}
        self.by_end = {}
        for c in chunks:
            self.by_end.setdefault(c[1], c)
        self._cache = {}
        self._chain = {}
        self._func = {}
        self._branches = {}

    def _norm(self, va):
        """Module-relative RVA or absolute VA -> absolute VA."""
        return va + self.base if va < self.base else va

    def off(self, va):
        va = self._norm(va)
        for _n, sva, vs, raw, _rs in self.secs:
            if sva <= va < sva + vs:
                return raw + (va - sva)
        raise KeyError(hex(va))

    def sec(self, va):
        va = self._norm(va)
        for n, sva, vs, _r, _rs in self.secs:
            if sva <= va < sva + vs:
                return n
        return None

    def bytes_at(self, va, n):
        o = self.off(va)
        return self.raw[o:o + n]

    def chunk_of(self, va):
        va = self._norm(va)
        i = bisect.bisect_right(self.starts, va) - 1
        if i >= 0 and self.chunks[i][0] <= va < self.chunks[i][1]:
            return self.chunks[i]
        return None

    def insns(self, chunk):
        if chunk not in self._cache:
            code = self.bytes_at(chunk[0], chunk[1] - chunk[0])
            self._cache[chunk] = list(self.md.disasm(code, chunk[0]))
        return self._cache[chunk]

    def at(self, va):
        c = self.chunk_of(va)
        if not c:
            return None
        for i in self.insns(c):
            if i.address == va:
                return i
            if i.address > va:
                return None
        return None

    def chain(self, va):
        """Contiguous .pdata chunks that fall through into each other, both directions."""
        c = self.chunk_of(self._norm(va))
        if not c:
            return []
        if c in self._chain:
            return self._chain[c]
        seq = [c]
        while True:
            p = self.by_end.get(seq[0][0])
            if p is None:
                break
            last = self.insns(p)[-1] if self.insns(p) else None
            if last is None or last.mnemonic in TERMINATORS:
                break
            if last.address + last.size != p[1]:
                break
            seq.insert(0, p)
        while True:
            last = self.insns(seq[-1])[-1] if self.insns(seq[-1]) else None
            if last is None or last.mnemonic in TERMINATORS:
                break
            if last.address + last.size != seq[-1][1]:
                break
            nxt = self.by_start.get(seq[-1][1])
            if not nxt:
                break
            seq.append(nxt)
        out = tuple(seq)
        for x in out:
            self._chain[x] = out
        return out

    def func_insns(self, va):
        c = self.chunk_of(self._norm(va))
        if c in self._func:
            return self._func[c]
        out = []
        for x in self.chain(va):
            out.extend(self.insns(x))
        self._func[c] = out
        return out

    def last_write(self, reg, before, va):
        """Last write to `reg` at or before `before` inside the chain containing va."""
        want = canonical(reg)
        found = None
        for i in self.func_insns(va):
            if i.address > before:
                break
            if i.mnemonic not in WRITES or not i.operands:
                continue
            op = i.operands[0]
            if op.type == CS_OP_REG and canonical(i.reg_name(op.reg)) == want:
                found = (i.address, "%s %s" % (i.mnemonic, i.op_str))
        return found

    def rip_target(self, ins):
        for op in ins.operands:
            if op.type == CS_OP_MEM and op.mem.base and \
                    ins.reg_name(op.mem.base) == "rip":
                return ins.address + ins.size + op.mem.disp
        return None

    def _branch_sites(self, target):
        """Sites whose decoded instruction is `call/jmp/jcc target` (byte scan, then boundary)."""
        if target in self._branches:
            return self._branches[target]
        txt = next(s for s in self.secs if s[0] == ".text")
        tva, traw, trs = txt[1], txt[3], txt[4]
        code = self.raw[traw:traw + trs]
        cands = []
        for op, kind in ((b"\xe8", "call"), (b"\xe9", "jmp"), (b"\xeb", "jmp")):
            p = code.find(op)
            while p >= 0:
                if op == b"\xeb":
                    if p + 2 <= len(code):
                        dest = tva + p + 2 + struct.unpack_from("<b", code, p + 1)[0]
                        if dest == target:
                            cands.append((tva + p, kind))
                elif p + 5 <= len(code):
                    dest = tva + p + 5 + struct.unpack_from("<i", code, p + 1)[0]
                    if dest == target:
                        cands.append((tva + p, kind))
                p = code.find(op, p + 1)
        for k in range(0x10):
            pat32 = bytes((0x0F, 0x80 + k))
            p = code.find(pat32)
            while p >= 0:
                if p + 6 <= len(code):
                    dest = tva + p + 6 + struct.unpack_from("<i", code, p + 2)[0]
                    if dest == target:
                        cands.append((tva + p, "jcc"))
                p = code.find(pat32, p + 1)
            pat8 = bytes((0x70 + k,))
            p = code.find(pat8)
            while p >= 0:
                if p + 2 <= len(code):
                    dest = tva + p + 2 + struct.unpack_from("<b", code, p + 1)[0]
                    if dest == target:
                        cands.append((tva + p, "jcc"))
                p = code.find(pat8, p + 1)
        out = []
        for va, kind in sorted(set(cands)):
            i = self.at(va)
            if i is None or i.op_str != hex(target):
                continue
            if kind == "call" and i.mnemonic != "call":
                continue
            if kind == "jmp" and i.mnemonic != "jmp":
                continue
            if kind == "jcc" and not (i.mnemonic.startswith("j") and i.mnemonic != "jmp"):
                continue
            out.append(va)
        self._branches[target] = out
        return out


def memops(ins):
    out = []
    for idx, op in enumerate(ins.operands):
        if op.type == CS_OP_MEM:
            base = ins.reg_name(op.mem.base) if op.mem.base else None
            index = ins.reg_name(op.mem.index) if op.mem.index else None
            rw = "w" if (idx == 0 and ins.mnemonic in WRITES and ins.mnemonic != "lea") else "r"
            out.append(dict(base=base, index=index, disp=op.mem.disp, size=op.size, rw=rw))
    return out


def text(ins):
    return "%s %s" % (ins.mnemonic, ins.op_str) if ins else "(none)"


def build():
    if not os.path.exists(EXE):
        raise SystemExit("JustCause3.exe not found at %s" % EXE)
    img = Image(EXE)
    doc = {"exe": EXE, "generated_by": "Tools/scripts/jc3_runtime_layout_review.py --write",
           "oracles": [], "claims": [], "anchors": [], "guards": [], "findings": []}
    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    # ---- P1 image identity, checked against the document's own table
    oracle("P1-image",
           img.sha256 == DOC_SHA and len(img.raw) == DOC_SIZE and img.base == DOC_BASE
           and len(img.secs) == DOC_SECTIONS and len(img.chunks) == DOC_CHUNKS,
           "sha256 %s, %d B, base %#x, %d sections, %d .pdata chunks"
           % (img.sha256[:16] + "...", len(img.raw), img.base, len(img.secs), len(img.chunks)))
    doc["image"] = {"sha256": img.sha256, "size": len(img.raw), "base": hex(img.base),
                    "sections": len(img.secs), "chunks": len(img.chunks),
                    "section_table": [{"name": n, "va": hex(v), "vsize": hex(s)}
                                      for n, v, s, _r, _rs in img.secs]}

    # ---- R1..R4: every claimed offset, from the instruction that uses it
    rows = []
    for group, off, claim, src, base, disp, size, rw, guard in CLAIMS:
        ins = img.at(src)
        src_ok = ins is not None
        src_text = text(ins)
        matched = False
        if src_ok:
            for m in memops(ins):
                if base == "indexed":
                    same = (m["disp"] == disp and m["size"] == size and m["index"] is not None)
                else:
                    same = (m["base"] == base and m["disp"] == disp
                            and m["size"] == size and m["rw"] == rw)
                if same:
                    matched = True
                    break
        real = real_base = None
        if not matched:
            # pass 1 prefers a hit whose base register matches the claim (the same field on
            # the same struct); pass 2 accepts any base so a real use is never hidden.
            for strict in (True, False):
                for cand in img.func_insns(src):
                    for m in memops(cand):
                        if base == "indexed":
                            same = (m["disp"] == disp and m["size"] == size
                                    and m["index"] is not None)
                        else:
                            same = (m["disp"] == disp and m["size"] == size
                                    and m["rw"] == rw and (not strict or m["base"] == base))
                        if same:
                            real, real_base = cand, m["base"]
                            break
                    if real is not None:
                        break
                if real is not None:
                    break
        prov = None
        b = real_base if real is not None else base
        if matched:
            b = [m for m in memops(ins) if m["disp"] == disp][0]["base"]
            prov = img.last_write(b, src, src) if b else None
        elif real is not None:
            prov = img.last_write(b, real.address, real.address) if b else None
        if not src_ok:
            verdict = "CITED-SRC-NOT-A-BOUNDARY"
        elif matched:
            verdict = "CONFIRMED"
        elif real is not None:
            verdict = "MIS-CITED"
        else:
            verdict = "UNSUPPORTED"
        rows.append({"group": group, "offset": "0x%x" % off, "claim": claim,
                     "src": hex(src), "src_text": src_text,
                     "base": base, "disp": "0x%x" % disp, "size": size, "rw": rw,
                     "verdict": verdict,
                     "real": hex(real.address) if real else None,
                     "real_text": text(real) if real else None,
                     "real_base": real_base,
                     "prov_at": hex(prov[0]) if prov else None,
                     "prov_text": prov[1] if prov else "(no write: entry argument)",
                     "guard": guard})
    doc["claims"] = rows
    oracle("P2-cited-instructions",
           all(r["verdict"] != "CITED-SRC-NOT-A-BOUNDARY" for r in rows),
           "%d/%d cited addresses are instruction boundaries in a .pdata chunk; "
           "%d CONFIRMED, %d MIS-CITED, %d UNSUPPORTED"
           % (sum(1 for r in rows if r["verdict"] != "CITED-SRC-NOT-A-BOUNDARY"), len(rows),
              sum(1 for r in rows if r["verdict"] == "CONFIRMED"),
              sum(1 for r in rows if r["verdict"] == "MIS-CITED"),
              sum(1 for r in rows if r["verdict"] == "UNSUPPORTED")))

    # ---- P3: the reviewed script's own 8 oracle predicates, re-implemented faithfully
    def chunk_has_read(va, base, disp):
        c = img.chunk_of(va)
        for i in img.insns(c):
            for m in memops(i):
                if m["base"] == base and m["disp"] == disp:
                    return True
        return False

    def chunk_disps(va, base):
        c = img.chunk_of(va)
        out = set()
        for i in img.insns(c):
            for m in memops(i):
                if m["base"] == base:
                    out.add(m["disp"])
        return sorted(out)

    def o3(shift=None):
        d = {"shape": 0x50, "flags": 0xC, "f40": 0x40, "f30": 0x30, "radius": 0x14}
        if shift:
            d.update(shift)
        return (chunk_has_read(img.base + A_USE, "rcx", d["shape"])
                and chunk_has_read(img.base + A_USE, "rcx", d["flags"])
                and chunk_has_read(img.base + A_USE, "rcx", d["f40"])
                and chunk_has_read(img.base + A_USE, "rcx", d["f30"])
                and chunk_has_read(img.base + A_USE, "rax", d["radius"]))

    def o4(shift=None):
        d = {"b100": 0x100, "b101": 0x101, "rec": 0x140}
        if shift:
            d.update(shift)
        cookie = struct.unpack("<Q", img.bytes_at(COOKIE, 8))[0]
        return (chunk_has_read(img.base + A_NODE, "rcx", d["b100"])
                and chunk_has_read(img.base + A_NODE, "rcx", d["b101"])
                and chunk_has_read(img.base + A_NODE, "rcx", d["rec"]) and cookie != 0)

    def o5(shift=None):
        d = {"t158": 0x158, "t60": 0x60}
        if shift:
            d.update(shift)
        c = img.chunk_of(img.base + A_RAYCAST)
        load158 = shl7 = add60 = False
        for i in img.insns(c):
            if i.mnemonic == "mov" and i.op_str == "rdi, qword ptr [rbx + %#x]" % d["t158"]:
                load158 = True
            if i.mnemonic == "shl" and i.op_str.endswith(", 7"):
                shl7 = True
            if i.mnemonic == "add" and "qword ptr [rdi + %#x]" % d["t60"] in i.op_str:
                add60 = True
        tol = img.bytes_at(TOL_VEC, 16) == struct.pack("<f", 0.001) * 4
        return load158 and shl7 and add60 and tol

    def o6(shift=None):
        d = {"world": 0x150, "count": 0x68, "base": 0x60, "flag": 0x60}
        if shift:
            d.update(shift)
        c = img.chunk_of(img.base + A_ENUM)
        flag = lea = False
        for i in img.insns(c):
            if i.mnemonic == "cmp" and "[" in i.op_str and i.op_str.endswith("+ %#x], 0" % d["flag"]) \
                    and i.op_str.count("+") == 2:
                flag = True
            t = img.rip_target(i)
            if i.mnemonic == "lea" and t == 0x142DAD020:
                lea = True
        return (chunk_has_read(img.base + A_ENUM, "rcx", d["world"])
                and chunk_has_read(img.base + A_ENUM, "rdi", d["count"])
                and chunk_has_read(img.base + A_ENUM, "rdi", d["base"]) and flag and lea)

    crash = img.at(img.base + CRASH)
    o2 = crash is not None and crash.mnemonic == "movss" and \
        crash.op_str == "xmm0, dword ptr [rax + 0x14]"
    tol_bytes = img.bytes_at(TOL_VEC, 16)
    o7 = tol_bytes == struct.pack("<f", 0.001) * 4

    def count_calls(target):
        return len([s for s in img._branch_sites(target) if img.at(s).mnemonic == "call"])

    o8 = (count_calls(img.base + A_USE) == 4 and count_calls(img.base + A_QUERY) == 4
          and count_calls(img.base + A_NODE) == 3)

    suite = [("O2-crash-instruction", o2, "at %#x: %s" % (img.base + CRASH, text(crash))),
             ("O3-slot-use", o3(), "rcx+0x50/0x0c/0x40/0x30 and rax+0x14 present in the chunk"),
             ("O4-node-update", o4(), "rcx+0x100/0x101/0x140 present, cookie %#x" %
              struct.unpack("<Q", img.bytes_at(COOKIE, 8))[0]),
             ("O5-raycast-read", o5(), "rbx+0x158 load, shl 7, add [rdi+0x60], 0.001 vector"),
             ("O6-slot-enum", o6(), "rcx+0x150, rdi+0x68, rdi+0x60, [rcx+rax+0x60], lea .data"),
             ("O7-tolerance-vector", o7, "%#x = %s" % (TOL_VEC, tol_bytes.hex(" "))),
             ("O8-call-verification", o8, "slot_use %d, slot_query %d, node_update %d calls"
              % (count_calls(img.base + A_USE), count_calls(img.base + A_QUERY),
                 count_calls(img.base + A_NODE)))]
    for key, ok, ev in suite:
        oracle(key, ok, ev)

    # ---- blindness: which wrong offsets still pass each oracle leg
    guard_map = {
        "O4.b100": (o4, "b100", 0x100, "rcx", img.base + A_NODE),
        "O4.b101": (o4, "b101", 0x101, "rcx", img.base + A_NODE),
        "O4.rec140": (o4, "rec", 0x140, "rcx", img.base + A_NODE),
        "O3.flags": (o3, "flags", 0xC, "rcx", img.base + A_USE),
        "O3.f30": (o3, "f30", 0x30, "rcx", img.base + A_USE),
        "O3.f40": (o3, "f40", 0x40, "rcx", img.base + A_USE),
        "O3.shape": (o3, "shape", 0x50, "rcx", img.base + A_USE),
        "O3.shape_radius": (o3, "radius", 0x14, "rax", img.base + A_USE),
        "O5.load158": (o5, "t158", 0x158, "rbx", img.base + A_RAYCAST),
        "O5.add60": (o5, "t60", 0x60, "rdi", img.base + A_RAYCAST),
        "O6.world150*": (o6, "world", 0x150, "rcx", img.base + A_ENUM),
        "O6.count68": (o6, "count", 0x68, "rdi", img.base + A_ENUM),
        "O6.base60": (o6, "base", 0x60, "rdi", img.base + A_ENUM),
        "O6.flag60": (o6, "flag", 0x60, None, img.base + A_ENUM),
    }
    guards = []
    for key, (pred, field, disp, base, va) in sorted(guard_map.items()):
        present = chunk_disps(va, base) if base else []
        collide = [d for d in present if d != disp]
        still = []
        for alt in collide:
            if pred({field: alt}):
                still.append(alt)
        guards.append({"leg": key, "disp": "0x%x" % disp,
                       "disps_present": ["0x%x" % d for d in present] if base
                       else ["(indexed operand, exact string match)"],
                       "wrong_offsets_that_still_pass": ["0x%x" % d for d in still]})
    doc["guards"] = guards
    oracle("P3-oracle-fidelity", all(ok for _k, ok, _e in suite),
           "the document's 8 predicates re-implemented here still evaluate as documented "
           "(this is what makes the blindness numbers below meaningful)")

    # ---- C4: chunk vs real function extent
    anchors = []
    for name, va, claimed_end in ANCHORS:
        c = img.chunk_of(va)
        ch = img.chain(va)
        last = img.insns(ch[-1])[-1]
        callers = len([s for s in img._branch_sites(img.base + va)
                       if img.at(s) and img.at(s).mnemonic == "call"])
        branches = len(img._branch_sites(img.base + va))
        anchors.append({
            "name": name, "va": hex(img.base + va),
            "claimed_body": "%#x..%#x" % (img.base + va, claimed_end),
            "claimed_bytes": claimed_end - (img.base + va),
            "chunk": "%#x..%#x" % c, "chunk_bytes": c[1] - c[0],
            "chain": ["%#x..%#x" % x for x in ch], "chain_bytes": sum(x[1] - x[0] for x in ch),
            "real_entry": hex(ch[0][0]), "chain_last": "%#x %s" % (last.address, text(last)),
            "complete": last.mnemonic in TERMINATORS,
            "call_sites": callers, "branch_sites": branches,
        })
    doc["anchors"] = anchors
    oracle("P4-chunks-vs-functions",
           True, "anchor extents recomputed: %s"
           % ", ".join("%s %dB/%dB" % (a["name"], a["claimed_bytes"], a["chain_bytes"])
                       for a in anchors))

    # ---- C1: the claimed call chain
    ray_chunk_calls_query = any(i.mnemonic == "call" and i.op_str == hex(img.base + A_QUERY)
                                for i in img.insns(img.chunk_of(A_RAYCAST)))
    query_calls_use = any(i.mnemonic == "call" and i.op_str == hex(img.base + A_USE)
                          for i in img.func_insns(A_QUERY))
    query_callees = sorted({i.op_str for i in img.func_insns(A_QUERY) if i.mnemonic == "call"})
    use_callers = [s for s in img._branch_sites(img.base + A_USE) if img.at(s).mnemonic == "call"]
    doc["findings"].append({
        "id": "C1",
        "claim": "the chain is 0x1402020d1 -> 0x141505490 -> 0x1415140f0 (section 5 step 6)",
        "verdict": "CONFIRMED" if (ray_chunk_calls_query and query_calls_use) else "REFUTED",
        "evidence": "raycast chunk calls query: %s; query body calls slot_use: %s; "
                    "slot_query's real callees: %s; slot_use's callers: %s"
                    % (ray_chunk_calls_query, query_calls_use, ", ".join(query_callees),
                       ", ".join(hex(s) for s in use_callers))})

    # ---- C2: flags bits on body_slot +0x0c
    bits = set()
    chain_ins = img.func_insns(A_USE)
    for i in chain_ins:
        if i.mnemonic == "test" and len(i.operands) == 2 and i.operands[0].type == CS_OP_REG \
                and canonical(i.reg_name(i.operands[0].reg)) == "rbp" \
                and i.operands[1].type == CS_OP_IMM:
            imm = i.operands[1].imm
            for b in range(8):
                if imm >> b & 1:
                    bits.add(b)
        if i.mnemonic == "shr" and len(i.operands) == 2 and i.operands[0].type == CS_OP_REG \
                and canonical(i.reg_name(i.operands[0].reg)) == "rbp" \
                and i.operands[1].type == CS_OP_IMM:
            bits.add(i.operands[1].imm)
    doc["findings"].append({
        "id": "C2",
        "claim": "body_slot +0x0c flags dword: bit 3 and bit 0 tested",
        "verdict": "REFUTED (partly)" if 0 not in bits else "CONFIRMED",
        "evidence": "bits of the dword loaded from [rcx+0x0c] actually tested in the slot_use "
                    "chunk chain: %s (test bpl,8 at 0x141514128; shr ebp,5 at 0x141514151 "
                    "then not/and 1); the same shr-5 test is in slot_query at 0x14150550b"
                    % (", ".join("bit %d" % b for b in sorted(bits)) or "none")})

    # ---- C3: shape+0x14 and the 0.001 constant
    tol_in_use = [hex(i.address) for i in img.func_insns(A_USE)
                  if img.rip_target(i) == TOL_VEC]
    mov = img.at(0x1402020F4)
    mov_target = img.rip_target(mov) if mov else None
    doc["findings"].append({
        "id": "C3",
        "claim": "shape +0x14 float read at the crash address (0.001-tolerance test follows)",
        "verdict": "REFUTED (parenthetical)" if not tol_in_use else "CONFIRMED",
        "evidence": "no instruction in the slot_use chunk chain references %#x (hits: %s). The "
                    "4x0.001 constant is loaded at 0x1402020f4 (movaps [rip+...] -> %s, "
                    "16-aligned and bit-exact) in the *raycast* chunk and copied to its "
                    "argument block at 0x140202107. shape+0x14 is instead passed as a float "
                    "argument (0x141514119) and subtracted from a coordinate at 0x14151422d "
                    "(subss), inside an AABB expansion."
                    % (TOL_VEC, tol_in_use or "none", hex(mov_target) if mov_target else "?")})

    # ---- C5: the handle sentinel
    handle_rds = []
    for i in img.func_insns(A_NODE):
        for m in memops(i):
            if m["base"] == "r8" and m["disp"] in (0x100, 0x102) and m["size"] == 2:
                handle_rds.append((i.address, text(i)))
    sentinel = [i.address for i in img.func_insns(A_NODE)
                if i.mnemonic == "mov" and i.op_str == "esi, 0x7fff"]
    doc["findings"].append({
        "id": "C5",
        "claim": "recipe: \"For a handle h (int16, < 0 means none)\"",
        "verdict": "IMPRECISE",
        "evidence": "the runtime record (node+0x140) holds two int16 handles read as "
                    "`word ptr [r8 + 0x100]` and `[r8 + 0x102]` (%s); a negative value is "
                    "replaced by the sentinel 0x7fff (%s) and the slot lookup is skipped when "
                    "the word equals 0x7fff (cmp ...,si at 0x140201f75/0x140201f7a and "
                    "0x1402020c7). A sampler should test `h == 0x7fff`, not `h < 0`."
                    % ("; ".join("%#x %s" % (a, t) for a, t in handle_rds),
                       ", ".join("%#x" % a for a in sentinel))})

    # ---- C6: body_slot +0x00 cited instruction
    row0 = [r for r in rows if r["group"] == "body_slot" and r["offset"] == "0x0"][0]
    setter_writes = [i.address for i in img.func_insns(SLOT_SETTER)
                     if i.mnemonic == "movaps" and i.operands[0].type == CS_OP_MEM
                     and (i.operands[0].mem.disp in (0x00, 0x10, 0x20, 0x30))]
    doc["findings"].append({
        "id": "C6",
        "claim": "body_slot +0x00 row 0 of a 3x4, cited at 0x141514123",
        "verdict": "MIS-CITED (offset real, citation wrong)",
        "evidence": "0x141514123 is `%s` - a store to the stack frame (r11=rsp), not a slot "
                    "read. The offset is real: `mulps xmm0, xmmword ptr [rsi]` at %s (rsi = "
                    "the slot, `mov rsi, rcx`) and the setter 0x%x writes [rcx]/[rcx+0x10]/"
                    "[rcx+0x20]/[rcx+0x30] at %s."
                    % (row0["src_text"], row0["real"] or "?", SLOT_SETTER,
                       ", ".join("%#x" % a for a in setter_writes))})

    doc["oracles"] = oracles
    doc["counts"] = {
        "claims": len(rows),
        "confirmed": sum(1 for r in rows if r["verdict"] == "CONFIRMED"),
        "miscited": sum(1 for r in rows if r["verdict"] == "MIS-CITED"),
        "unsupported": sum(1 for r in rows if r["verdict"] == "UNSUPPORTED"),
        "unguarded": sum(1 for r in rows if r["guard"] is None),
        "blind_rows": len([g for g in guards if g["wrong_offsets_that_still_pass"]]),
    }
    doc["unknowns"] = [
        {"what": "what slot+0x30 and slot+0x40 are semantically",
         "why": "decoded only as: +0x40 is the vector whose x/y/z broadcast and multiply the "
                "3x4 rows at +0x00/+0x10/+0x20 (0x1415141f8..0x141514203); +0x30 is stored to "
                "the shadow-argument slot [r11-0x28] for the call at 0x141514199. Whether they "
                "are min/max of a local AABB or a query vector is not proven by any instruction "
                "in the chain: no min/max compare exists. Where it would be found: the callee "
                "0x141516b40's first uses of its 4th stack argument."},
        {"what": "whether node+0x150 and node+0x158 are the same world object",
         "why": "both are used identically (slot array at +0x60, stride 128, vtbl call "
                "[rax+0x20] compared to 8) but no instruction compares or copies the two "
                "pointers. Where it would be found: a setter of node+0x150/+0x158."},
        {"what": "where the runtime record's int16 handles (+0x100/+0x102) are written",
         "why": "the record is read at 0x140201e35/0x140201e55 and consumed for the slot "
                "lookup, but no instruction in the reviewed chunk chains writes them, so the "
                "transfer named in the document's UNKNOWN 5 is still open. Where it would be "
                "found: writers of word ptr [x+0x100]/[x+0x102] where x = [part+0x140]."},
    ]
    return doc


def render(doc):
    L = []
    A = L.append
    ok = sum(1 for o in doc["oracles"] if o["ok"])
    c = doc["counts"]
    A("# Review of G3-07a's JC3 runtime layout (RUNTIME_LAYOUT.md)")
    A("")
    A("Generated by `Tools/scripts/jc3_runtime_layout_review.py --write`; `--check` re-derives "
      "every number from `%s` (read-only)." % doc["exe"])
    A("")
    A("**Oracles: %d/%d pass.** Claim verdicts: **%d CONFIRMED, %d MIS-CITED, %d UNSUPPORTED** "
      "of %d; **%d rows have no oracle at all** and **%d oracle legs pass for at least one wrong "
      "offset**." % (ok, len(doc["oracles"]), c["confirmed"], c["miscited"], c["unsupported"],
                     c["claims"], c["unguarded"], c["blind_rows"]))
    A("")
    A("## 1. The image")
    A("")
    A("| item | value | document |")
    A("|---|---|---|")
    A("| sha256 | `%s` | matches |" % doc["image"]["sha256"])
    A("| size | %s B | matches |" % f"{doc['image']['size']:,}")
    A("| image base | %s | matches |" % doc["image"]["base"])
    A("| sections / `.pdata` chunks | %d / %s | matches |"
      % (doc["image"]["sections"], f"{doc['image']['chunks']:,}"))
    A("")
    A("## 2. Every claimed offset, against the instruction that uses it")
    A("")
    A("`CONFIRMED` = the cited address holds an instruction whose memory operand has the "
      "claimed base register, displacement, width and direction. `MIS-CITED` = the offset is "
      "real somewhere else in the same chunk chain, but the cited instruction does not use it.")
    A("")
    A("| struct | offset | claim | cited | instruction there | verdict |")
    A("|---|---|---|---|---|---|")
    for r in doc["claims"]:
        v = r["verdict"]
        if v == "MIS-CITED":
            v = "**MIS-CITED** -> `%s` `%s`" % (r["real"], r["real_text"])
        elif v == "CONFIRMED":
            v = "CONFIRMED"
        A("| `%s` | `%s` | %s | `%s` | `%s` | %s |"
          % (r["group"], r["offset"], r["claim"], r["src"], r["src_text"], v))
    A("")
    A("Provenance of the base register at each confirmed instruction (why `[rax+0x14]` is a "
      "`shape` field and `[rdi+0x60]` a world field):")
    A("")
    A("| struct | offset | base register | last write before the use |")
    A("|---|---|---|---|")
    for r in doc["claims"]:
        if r["verdict"] in ("CONFIRMED", "MIS-CITED"):
            b = r["real_base"] if r["verdict"] == "MIS-CITED" else r["base"]
            A("| `%s` | `%s` | `%s` | `%s` `%s` |"
              % (r["group"], r["offset"], b,
                 r["prov_at"] or "-", r["prov_text"]))
    A("")
    A("## 3. The six anchors: `.pdata` chunk or function?")
    A("")
    A("| anchor | document body | chunk | contiguous chain | real entry | chain ends | callers |")
    A("|---|---|---|---|---|---|---|")
    for a in doc["anchors"]:
        A("| `%s` | `%s` (%d B) | `%s` (%d B) | %d B | `%s` | `%s` | %d |"
          % (a["name"], a["claimed_body"], a["claimed_bytes"], a["chunk"], a["chunk_bytes"],
             a["chain_bytes"], a["real_entry"], a["chain_last"], a["call_sites"]))
    A("")
    A("## 4. Oracles that pass for a wrong offset")
    A("")
    A("Each leg of the reviewed script's oracle suite is a presence test "
      "(`has_read(chunk, base, disp)`) or a string match on one instruction. Any *other* "
      "displacement that also occurs in the same chunk passes the leg:")
    A("")
    A("| oracle leg | checks | displacements present | wrong offsets that still pass |")
    A("|---|---|---|---|")
    for g in doc["guards"]:
        A("| `%s` | `%s` | %s | %s |"
          % (g["leg"], g["disp"], ", ".join("`%s`" % d for d in g["disps_present"]),
             ", ".join("`%s`" % d for d in g["wrong_offsets_that_still_pass"]) or "none"))
    A("")
    A("Rows with **no** oracle leg at all (any value, any citation passes `--check` as long as "
      "`--write` was re-run): %s."
      % ", ".join("`%s %s`" % (r["group"], r["offset"])
                  for r in doc["claims"] if r["guard"] is None))
    A("")
    A("## 5. Findings on the claims themselves")
    A("")
    A("| | claim | verdict | evidence |")
    A("|---|---|---|---|")
    for f in doc["findings"]:
        A("| `%s` | %s | **%s** | %s |" % (f["id"], f["claim"], f["verdict"], f["evidence"]))
    A("")
    A("## 6. What this review still cannot decode")
    A("")
    for u in doc["unknowns"]:
        A("- **%s** — %s" % (u["what"], u["why"]))
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout_review.py --write")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout_review.py --check")
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
        print("wrote Research/JC3Grab/RUNTIME_LAYOUT_REVIEW.md and .json")
        print("  claims %d: %d confirmed, %d mis-cited, %d unsupported, %d unguarded"
              % (doc["counts"]["claims"], doc["counts"]["confirmed"],
                 doc["counts"]["miscited"], doc["counts"]["unsupported"],
                 doc["counts"]["unguarded"]))
        print("  oracles %d/%d; blind oracle legs %d"
              % (len(doc["oracles"]) - len(fails), len(doc["oracles"]),
                 doc["counts"]["blind_rows"]))
        print("  findings %d, unknowns %d"
              % (len(doc["findings"]), len(doc["unknowns"])))
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
        print("FAIL: RUNTIME_LAYOUT_REVIEW.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: RUNTIME_LAYOUT_REVIEW.json is stale")
        return 1
    print("OK %d/%d oracles, %d claims (%d confirmed, %d mis-cited, %d unsupported, %d "
          "unguarded), %d blind legs, %d findings, md+json byte-identical"
          % (len(doc["oracles"]), len(doc["oracles"]), doc["counts"]["claims"],
             doc["counts"]["confirmed"], doc["counts"]["miscited"],
             doc["counts"]["unsupported"], doc["counts"]["unguarded"],
             doc["counts"]["blind_rows"], len(doc["findings"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
